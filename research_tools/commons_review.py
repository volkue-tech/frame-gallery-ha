"""Private candidate evidence and contact sheets; never automatic acceptance.

Metadata, rights, source revision and bounded preview evidence are separate from
an actual curator decision. Files below build/ are public-source research only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research_tools.commons_colours import (  # noqa: E402
    BASELINE,
    MAX_AXIS,
    MAX_BYTES,
    run_worker,
    save,
)
from research_tools.commons_expand import OUTPUT, eligible  # noqa: E402


class PlainText(HTMLParser):
    """Untrusted provider markup becomes plain research text, never executable UI."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.tags: list[tuple[str, bool]] = []

    def handle_starttag(self, tag, attrs) -> None:
        attributes = dict(attrs)
        style = re.sub(r"\s+", "", attributes.get("style") or "").lower()
        classes = (attributes.get("class") or "").lower().split()
        hidden = (
            bool(self.tags and self.tags[-1][1])
            or tag in ("script", "style")
            or "display:none" in style
            or "visibility:hidden" in style
            or "labelqs" in classes
        )
        if tag not in {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }:
            self.tags.append((tag, hidden))
        if not hidden and tag in ("br", "div", "p", "li"):
            self.parts.append(" ")

    def handle_endtag(self, tag) -> None:
        for index in range(len(self.tags) - 1, -1, -1):
            if self.tags[index][0] == tag:
                del self.tags[index:]
                break
        if tag in ("div", "p", "li"):
            self.parts.append(" ")

    def handle_data(self, data) -> None:
        if not self.tags or not self.tags[-1][1]:
            self.parts.append(data)


def plain(raw: object) -> str:
    if not isinstance(raw, str) or len(raw) > 100000:
        return ""
    parser = PlainText()
    parser.feed(raw)
    return " ".join("".join(parser.parts).split())[:2000]


def source_markup(wikitext: str) -> str:
    without_comments = re.sub(r"<!--.*?-->", "", wikitext, flags=re.DOTALL)
    return re.sub(
        r"<(nowiki|pre|syntaxhighlight)\b[^>]*>.*?</\1\s*>",
        "",
        without_comments,
        flags=re.DOTALL | re.IGNORECASE,
    )


def template_names(wikitext: str) -> set[str]:
    # Only inventory direct declarations. This is NOT a MediaWiki expansion or
    # legal evaluator: ambiguous/transcluded bases still require manual review.
    return {
        name.strip().lower().replace("_", " ")
        for name in re.findall(r"\{\{\s*([^{}|\n]+)", source_markup(wikitext))
    }


def artwork_artist(observed: object, description: object) -> str:
    """An institution upload credit is not the maker of the original artwork.

    Only this explicit Rijksmuseum source format is resolved; no category/name
    guessing. Unknown/attributed maker statements remain qualified as recorded.
    """
    artist = plain(observed)
    if artist != "Rijksmuseum" or not isinstance(description, str):
        return artist
    text = plain(description)
    match = re.search(
        r"Vervaardiger:\s*(?:tekenaar|schilder|ontwerper):\s*(.*?)\s+Datering:", text
    )
    return (
        match[1].strip()
        if match and match[1].strip()
        else "Artist not identified (Rijksmuseum source)"
    )


def us_basis(names: set[str], wikitext: str = "") -> list[str]:
    # PD-Art's documented first parameter names the underlying public-domain
    # basis. Record it distinctly; never treat PD-Art alone as US clearance.
    wrappers = re.findall(
        r"\{\{\s*PD-Art(?:-two)?\s*\|\s*(?:1\s*=\s*)?"
        r"(PD-old-auto-expired|PD-old-100-expired|PD-old-100-1923|PD-old-70-expired|PD-US-expired)\s*[|}]",
        source_markup(wikitext),
        flags=re.IGNORECASE,
    )
    # Verified official alias: PD-old-100-1923 redirects to PD-old-100-expired.
    # PD-Art-two-auto documents a US-expired basis plus an explicit deathyear.
    # Never infer this from a bare PD-Art or a photographic CC0 declaration.
    auto = re.findall(
        r"\{\{\s*PD-Art-two-auto\s*\|\s*(?:deathyear\s*=\s*|1\s*=\s*)?"
        r"([0-9]{4})\s*[|}]",
        source_markup(wikitext),
        flags=re.IGNORECASE,
    )
    aliases = (
        {"pd-art-two-auto"}
        if any(1000 <= int(year) <= datetime.now(UTC).year - 71 for year in auto)
        else set()
    )
    return sorted(
        name
        for name in names | {w.lower() for w in wrappers} | aliases
        if name
        in {
            "pd-old-auto-expired",
            "pd-old-100-expired",
            "pd-old-100-1923",
            "pd-old-70-expired",
            "pd-art-two-auto",
            "pd-us-expired",
            "pd-us",
            "pd-us-no notice",
            "pd-us-not renewed",
            "cc-zero",
            "cc0",
        }
        and (name != "pd-art-two-auto" or name in aliases)
    )


def prepare(page: dict, expected: dict) -> dict:
    sys.path.insert(0, str(ROOT / "frame_gallery/src"))
    from frame_gallery.providers.commons import _rights

    expected = {key: value for key, value in expected.items() if key != "status"}

    infos = page.get("imageinfo", [])
    info = infos[0] if len(infos) == 1 and isinstance(infos[0], dict) else {}
    reasons = []
    if (
        page.get("pageid") != expected["id"]
        or page.get("ns") != 6
        or page.get("title") != expected["file_title"]
        or page.get("imagerepository") != "local"
        or info.get("sha1") != expected["sha1"]
        or not eligible(info)
    ):
        reasons.append("source identity, hash, type or dimensions changed")
    rights = _rights(info.get("extmetadata"))
    if rights is None:
        reasons.append("current PD/CC0 rights gate refused")
    revisions = page.get("revisions", [])
    revision = revisions[0] if len(revisions) == 1 else {}
    text = revision.get("slots", {}).get("main", {}).get("content", "")
    if not isinstance(text, str) or not 0 < len(text) <= 500000:
        reasons.append("missing/bounded source revision")
        text = ""
    names = template_names(text)
    basis = us_basis(names, text)
    if not basis:
        reasons.append("no direct recorded US/CC0 basis; manual rights review needed")
    metadata = info.get("extmetadata", {})
    values = {
        key: field.get("value")
        for key, field in metadata.items()
        if isinstance(field, dict)
    }
    return dict(
        **expected,
        title=plain(values.get("ObjectName")) or expected["file_title"][5:],
        artist=artwork_artist(values.get("Artist"), values.get("ImageDescription")),
        date=plain(values.get("DateTimeOriginal")),
        description=plain(values.get("ImageDescription")),
        rights_label=values.get("LicenseShortName"),
        rights_gate_passed=rights is not None,
        direct_templates=sorted(names),
        us_basis_declarations=basis,
        source_revision=revision.get("revid"),
        source_timestamp=revision.get("timestamp"),
        source_page_sha256=hashlib.sha256(text.encode()).hexdigest(),
        thumbnail_url=info.get("thumburl"),
        thumbnail_mime=info.get("thumbmime"),
        reported_thumbnail_dimensions=[info.get("thumbwidth"), info.get("thumbheight")],
        reasons=reasons,
        status="deferred metadata"
        if reasons
        else "metadata eligible; NOT visually accepted",
        checked_at=datetime.now(UTC).isoformat(),
    )


def research_channel(requests: int):
    sys.path.insert(0, str(ROOT / "frame_gallery/src"))
    from frame_gallery.budget.allowance import Allowance
    from frame_gallery.budget.clock import SystemClock
    from frame_gallery.budget.deadline import Deadline
    from frame_gallery.net.gateway import Gateway
    from frame_gallery.net.identity import commons_identity
    from frame_gallery.net.transport import SystemResolver, Urllib3Transport
    from frame_gallery.providers.commons import commons_policy
    from frame_gallery.randomness import SeededRandomSource

    clock = SystemClock()
    gateway = Gateway(
        resolver=SystemResolver(),
        transport=Urllib3Transport(),
        clock=clock,
        random=SeededRandomSource(20261009),
        identity=commons_identity(),
    )
    return gateway.channel(
        commons_policy(), metadata_allowance=Allowance("private review", requests)
    ), Deadline.after(clock, 900, "finite Commons evidence pass")


def metadata(limit: int) -> None:
    from frame_gallery.net.policy import https_url
    from frame_gallery.providers.commons import RIGHTS_FIELDS

    if not 1 <= limit <= 1000:
        raise ValueError("bounded evidence pass")
    baseline = json.loads(BASELINE.read_text())
    excluded = {w["id"] for w in baseline["included"] + baseline["previously_deferred"]}
    candidates = {}
    # Specific Artwork declarations first, broad search as separately retained
    # fallback evidence. No automatic promotion based on these search labels.
    for name in (
        "discovery-targeted.json",
        "discovery-pdart.json",
        "discovery-pdart-single.json",
        "discovery-artists.json",
        "discovery-paintings.json",
        "discovery-artwork.json",
        "discovery.json",
    ):
        path = OUTPUT / name
        if path.exists():
            for work in json.loads(path.read_text())["candidates"]:
                if work["id"] not in excluded:
                    candidates.setdefault(work["id"], work)
    path = OUTPUT / "review.json"
    report = (
        json.loads(path.read_text())
        if path.exists()
        else dict(
            schema=1,
            status="candidate evidence only; no new accepted works",
            records=[],
        )
    )
    done = {w["id"] for w in report["records"]}
    works = [w for w in candidates.values() if w["id"] not in done][:limit]
    channel, deadline = research_channel(210)
    for offset in range(0, len(works), 5):
        batch = works[offset : offset + 5]
        query = (
            ("action", "query"),
            ("format", "json"),
            ("formatversion", "2"),
            ("pageids", "|".join(str(w["id"]) for w in batch)),
            ("prop", "imageinfo|revisions"),
            ("rvprop", "ids|timestamp|content"),
            ("rvslots", "main"),
            ("iiprop", "size|mime|sha1|url|extmetadata|thumbmime"),
            ("iilimit", "1"),
            ("iiurlwidth", "512"),
            ("iiextmetadatalanguage", "en"),
            (
                "iiextmetadatafilter",
                RIGHTS_FIELDS + "|Artist|ObjectName|DateTimeOriginal|ImageDescription",
            ),
            ("maxlag", "5"),
        )
        document = channel.get_json(
            https_url("commons.wikimedia.org", "/w/api.php", query), deadline
        )
        if (
            not isinstance(document, dict)
            or "error" in document
            or "warnings" in document
        ):
            save(OUTPUT / "metadata-query-refusal.json", document)
            raise ValueError("review metadata refused; no blind retry")
        evidence = OUTPUT / f"review-metadata-{batch[0]['id']}.json"
        save(evidence, document)
        pages = {p["pageid"]: p for p in document.get("query", {}).get("pages", [])}
        for work in batch:
            record = prepare(pages.get(work["id"], {}), work)
            record["evidence_file"] = evidence.name
            record["evidence_sha256"] = hashlib.sha256(
                evidence.read_bytes()
            ).hexdigest()
            report["records"].append(record)
        report["updated_at"] = datetime.now(UTC).isoformat()
        save(path, report)
        print(
            json.dumps(
                dict(
                    checked=len(report["records"]),
                    eligible=sum(not w["reasons"] for w in report["records"]),
                )
            )
        )


def thumbnails(limit: int) -> None:
    from frame_gallery.net.policy import RequestKind
    from frame_gallery.providers.commons import _image_url
    from frame_gallery.providers.contract import SourceError

    if not 1 <= limit <= 600:
        raise ValueError("bounded thumbnail pass")
    report = json.loads((OUTPUT / "review.json").read_text())
    path = OUTPUT / "profiles.json"
    profiles = (
        json.loads(path.read_text())
        if path.exists()
        else dict(
            schema=1,
            status="unreviewed candidate previews; not accepted",
            profiles=[],
            refused=[],
        )
    )
    done = {
        p["id"]
        for p in profiles["profiles"]
        + profiles["refused"]
        + profiles.get("network_deferred", [])
    }
    works = [w for w in report["records"] if not w["reasons"] and w["id"] not in done][
        :limit
    ]
    channel, deadline = research_channel(1)
    for work in works:
        url = _image_url(work["thumbnail_url"], channel.policy)
        dimensions = work["reported_thumbnail_dimensions"]
        if (
            url is None
            or work["thumbnail_mime"] != "image/jpeg"
            or any(not isinstance(v, int) or not 0 < v <= MAX_AXIS for v in dimensions)
        ):
            profiles["refused"].append(
                dict(id=work["id"], reason="thumbnail metadata bound")
            )
            save(path, profiles)
            continue

        class Sink:
            def __init__(self) -> None:
                self.data = bytearray()

            def write(self, chunk: bytes) -> None:
                if len(self.data) + len(chunk) > MAX_BYTES:
                    raise ValueError("thumbnail byte bound")
                self.data.extend(chunk)

        sink = Sink()
        # Network refusals terminate the pass. Only a local decoder refusal is
        # recorded as a candidate deferral; it never triggers another request.
        try:
            channel._request(url, RequestKind.IMAGE, deadline, sink)
        except SourceError as error:
            profiles.setdefault("network_deferred", []).append(
                dict(
                    id=work["id"],
                    original_sha1=work["sha1"],
                    reason="research network refusal; not permanent artwork rejection",
                    kind=error.kind.value,
                    observed_at=datetime.now(UTC).isoformat(),
                    retry="no automatic retry; future separately reviewed retry only",
                )
            )
            save(path, profiles)
            raise
        image_path = OUTPUT / f"{work['id']}.jpg"
        image_path.write_bytes(sink.data)
        try:
            profile = run_worker(image_path)
            actual = profile["dimensions"]
            if abs(actual[0] / actual[1] / (dimensions[0] / dimensions[1]) - 1) > 0.015:
                raise ValueError("thumbnail shape disagreement")
        except ValueError:
            profiles["refused"].append(
                dict(id=work["id"], reason="local decoder/shape bound")
            )
            save(path, profiles)
            continue
        profile.update(
            id=work["id"],
            title=work["title"],
            artist=work["artist"],
            file_title=work["file_title"],
            original_sha1=work["sha1"],
            source=work["source"],
            source_page_sha256=work["source_page_sha256"],
            source_revision=work["source_revision"],
            thumbnail_url=url,
            reported_thumbnail_dimensions=dimensions,
            analysed_at=datetime.now(UTC).isoformat(),
            status="needs full-image, rights-provenance and artwork-duplicate review",
        )
        profiles["profiles"].append(profile)
        save(path, profiles)
        print(json.dumps(dict(previews=len(profiles["profiles"]), id=work["id"])))


def sheets() -> None:
    from PIL import Image, ImageDraw, ImageOps

    profiles = json.loads((OUTPUT / "profiles.json").read_text())["profiles"]
    for start in range(0, len(profiles), 16):
        sheet = Image.new("RGB", (1600, 1120), "#eceae5")
        draw = ImageDraw.Draw(sheet)
        for position, work in enumerate(profiles[start : start + 16]):
            with Image.open(OUTPUT / f"{work['id']}.jpg") as opened:
                image = ImageOps.exif_transpose(opened).convert("RGB")
            image.thumbnail((390, 219))
            x, y = position % 4 * 400, position // 4 * 280
            sheet.paste(image, (x + (400 - image.width) // 2, y))
            draw.text(
                (x + 6, y + 221), f"#{start + position} · {work['id']}", fill="black"
            )
            draw.text((x + 6, y + 239), work["artist"][:55], fill="black")
            draw.text((x + 6, y + 257), work["title"][:60], fill="black")
        destination = OUTPUT / f"sheet-{start // 16:03}.jpg"
        if destination.exists():
            old = destination.read_bytes()
            old_hash = hashlib.sha256(old).hexdigest()[:12]
            # Appending candidates changes the last partial sheet. Retain the
            # actually inspected prior sheet referenced by the screen receipt.
            archive = destination.with_name(f"{destination.stem}-{old_hash}.jpg")
            if not archive.exists():
                archive.write_bytes(old)
        sheet.save(destination, quality=94)
    print(json.dumps(dict(previews=len(profiles), sheets=(len(profiles) + 15) // 16)))


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "frame_gallery/src"))
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("metadata", "thumbnails", "sheets", "counts"))
    parser.add_argument("--limit", type=int, default=1000)
    args = parser.parse_args()
    if args.mode == "metadata":
        metadata(args.limit)
    elif args.mode == "thumbnails":
        thumbnails(args.limit)
    elif args.mode == "sheets":
        sheets()
    else:
        report = json.loads((OUTPUT / "review.json").read_text())
        print(json.dumps(Counter(w["status"] for w in report["records"])))
