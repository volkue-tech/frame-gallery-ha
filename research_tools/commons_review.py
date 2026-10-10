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
from research_tools.commons_expand import (  # noqa: E402
    OUTPUT,
    SINGLE_SUBJECTS,
    eligible,
)

RESEARCH_POOLS = ("targeted", *SINGLE_SUBJECTS)


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
        r"Vervaardiger:\s*(?:tekenaar|schilder|ontwerper):\s*(.*?)"
        r"(?=\s*(?:Datering|Plaats vervaardiging|opdrachtgever):)",
        text,
    )
    return (
        match[1].strip()
        if match and match[1].strip()
        else "Artist not identified (Rijksmuseum source)"
    )


def us_basis(names: set[str], wikitext: str = "") -> list[str]:
    # Commons' documented Self wrapper takes explicit licence tags as positional
    # parameters. Recognize CC0 there, not merely in rendered metadata, an author
    # name, comments, examples, or a vaguely named template. This still says
    # nothing about rights to a separately depicted contemporary artwork.
    self_cc0 = set()
    for fields in re.findall(
        r"\{\{\s*self\s*\|([^{}]+)\}\}", source_markup(wikitext), re.I
    ):
        for field in fields.split("|"):
            if "=" in field:
                key, field = field.split("=", 1)
                if not key.strip().isdigit() or not 1 <= int(key.strip()) <= 6:
                    continue
            tag = field.strip().lower().replace("_", " ")
            if tag in {"cc-zero", "cc0"}:
                self_cc0.add(tag)
    # PD-Art's documented first parameter names the underlying public-domain
    # basis. Record it distinctly; never treat PD-Art alone as US clearance.
    wrappers = re.findall(
        r"\{\{\s*PD-Art(?:-two)?\s*\|\s*(?:1\s*=\s*)?"
        r"(PD-old-auto-expired|PD-old-auto-1923|PD-old-100-expired|"
        r"PD-old-100-1923|PD-old-70-expired|PD-old-70-1923|PD-US-expired)\s*[|}]",
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
        for name in names | {w.lower() for w in wrappers} | aliases | self_cc0
        if name
        in {
            "pd-old-auto-expired",
            "pd-old-auto-1923",
            "pd-old-100-expired",
            "pd-old-100-1923",
            "pd-old-70-expired",
            "pd-old-70-1923",
            "pd-art-old-100-expired",
            "pd-art-two-auto",
            "pd-us-expired",
            "pd-us",
            "pd-us-no notice",
            "pd-us-not renewed",
            "pd-self",
            "cc-zero",
            "cc0",
        }
        and (name != "pd-art-two-auto" or name in aliases)
    )


def declared_creators(wikitext: str) -> str:
    """Use only an explicit artwork artist field, never categories/uploaders."""
    field = re.search(
        r"^\s*\|\s*artist\s*=([^\n]*)", source_markup(wikitext), re.I | re.M
    )
    if not field:
        return ""
    return "; ".join(re.findall(r"\{\{\s*Creator:([^{}|]+)\}\}", field[1], re.I))


def source_artist(observed: object, description: object, wikitext: str) -> str:
    """Prefer an explicit Art Photo artwork maker over its photographic credit.

    This does not change rights handling or guess artists from filenames. The
    raw source receipt retains the photographer and both licensing scopes.
    """
    stated = declared_creators(wikitext)
    artist = artwork_artist(observed, description)
    if stated and (
        "art photo" in template_names(wikitext) or artist.startswith("Creator:")
    ):
        return stated
    markup = source_markup(wikitext)
    if not artist and re.search(
        r"^\s*\|\s*institution\s*=\s*Rijksmuseum\s*$", markup, re.I | re.M
    ):
        maker = artwork_artist("Rijksmuseum", description)
        if not maker.startswith("Artist not identified"):
            return maker
    if "art photo" in template_names(wikitext) and re.search(
        r"^\s*\|\s*artist\s*=\s*\n", markup, re.I | re.M
    ):
        # One explicit caption shape names the original maker independently
        # of the separately labelled photographer. Never guess from a file
        # title/category or overwrite a nonempty artwork artist field.
        photographer = re.search(
            r"^\s*\|\s*photographer\s*=\s*\[\[User:([^]|]+)"
            r"(?:\|([^]]+))?\]\]",
            markup,
            re.I | re.M,
        )
        caption = re.match(
            r"^.+?, by ([^,;]{2,120}), [0-9]{4}(?:[-–][0-9]{4})?, "
            r"(?:oil on (?:canvas|panel)|watercolou?r|pastel|tempera)\b",
            plain(description),
            re.I,
        )
        if (
            photographer
            and caption
            and artist in {photographer[1].strip(), (photographer[2] or "").strip()}
        ):
            return caption[1].strip()
    # An unresolved Creator link is rendered literally by Commons. Remove
    # that namespace only when the non-Art-Photo source explicitly supplies
    # the exact same Creator in its Author field. Never infer from a filename.
    if artist.startswith("Creator:") and "art photo" not in template_names(wikitext):
        author = re.search(
            r"^\s*\|\s*author\s*=\s*\{\{\s*Creator:([^{}|]+)\}\}\s*$",
            source_markup(wikitext),
            re.I | re.M,
        )
        if author and artist == "Creator:" + author[1]:
            return author[1]
    return artist or stated


def source_title(observed: object, description: object, fallback: str) -> str:
    """A short explicit caption may replace only a technical source identifier."""
    title = plain(observed) or fallback
    caption = plain(description)
    if (
        re.fullmatch(
            r"(?:(?:[0-9]{6,12}\s*)?(?:DSCN?|IMG|PXL)[-_ ]?[0-9]{3,12}[a-z]?"
            r"|MET DP[0-9]{3,12})(?:\.jpe?g)?",
            title,
            re.I,
        )
        and 3 <= len(caption) <= 100
        and not re.search(r"https?://|\{\{|\[\[", caption)
    ):
        return caption
    return title


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
        title=source_title(
            values.get("ObjectName"),
            values.get("ImageDescription"),
            expected["file_title"][5:],
        ),
        artist=source_artist(
            values.get("Artist"), values.get("ImageDescription"), text
        ),
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


def research_pool(pool: str | None) -> str | None:
    """A narrow retained-source pass, not a source-path or licence override."""
    if pool is None:
        return None
    if pool == "targeted":
        return "discovery-targeted.json"
    if pool in SINGLE_SUBJECTS:
        return f"discovery-subject-{pool}.json"
    raise ValueError("unknown retained research pool")


def metadata(limit: int, pool: str | None = None) -> None:
    from frame_gallery.net.policy import https_url
    from frame_gallery.providers.commons import RIGHTS_FIELDS

    if not 1 <= limit <= 1000:
        raise ValueError("bounded evidence pass")
    pool_file = research_pool(pool)
    baseline = json.loads(BASELINE.read_text())
    excluded = {w["id"] for w in baseline["included"] + baseline["previously_deferred"]}
    candidates = {}
    # Direct PD-Art discovery first, then Artwork/CC0 and broad retained
    # fallback evidence. Order never approves a work or excludes another pool.
    for name in tuple(
        p.name for p in sorted(OUTPUT.glob("discovery-subject-*.json"))
    ) + (
        "discovery-pdart-highres.json",
        "discovery-media-precise.json",
        "discovery-genre-precise.json",
        "discovery-pdart-precise.json",
        "discovery-paintings-precise.json",
        "discovery-artwork-precise.json",
        "discovery-cc0-art-precise.json",
        "discovery-targeted.json",
        "discovery-pdart.json",
        "discovery-pdart-single.json",
        "discovery-artists.json",
        "discovery-paintings.json",
        "discovery-artwork.json",
        "discovery.json",
    ):
        if pool_file is not None and name != pool_file:
            continue
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
    works = sorted(
        [w for w in candidates.values() if w["id"] not in done], key=preview_priority
    )[:limit]
    channel, deadline = research_channel(210)
    for offset in range(0, len(works), 5):
        if deadline.remaining() < 45:
            print(
                json.dumps(dict(status="finite time cap; metadata progress retained"))
            )
            return
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


def preview_priority(work: dict) -> int:
    """Order research only; never exclude or approve a work by its label."""
    title = (work.get("title") or work.get("file_title", "")).casefold()
    if re.search(
        r"\b(?:frieze|sidewall|album|drawing|sketch|map|atlas|loc|verhandeling|"
        r"receipt|manuscript|lettre|papiers|missa|banknote|fragment|"
        r"stereoscopic|stereograph|correspondance|correspondence|"
        r"dancing master|permit number|korte verhandeling|ku-?[0-9]+)\b",
        title,
    ) or re.search(
        r"\b(?:department|office|archives|records administration|"
        r"gouvernement|compositeur|auteur du texte|éditeur scientifique|"
        r"editeur scientifique|photographe|photographer)\b",
        work.get("artist", ""),
        re.I,
    ):
        return 4
    query = work.get("query", "").lower()
    names = work.get("direct_templates", [])
    if any(
        query.endswith(f'"{subject}"')
        for subject in (
            "digital art",
            "fractal art",
            "generative art",
            "fine art photography",
            "abstract photography",
        )
    ) or any(
        query.endswith(f'hastemplate:artwork insource:"{medium}"')
        for medium in (
            "huile",
            "olieverf",
            "gouache",
            "tempera",
            "watercolour",
            "watercolor",
        )
    ):
        return -1
    if 'insource:"oil"' in query or any(name.startswith("pd-art") for name in names):
        return 0
    if "hastemplate:cc-zero" in query:
        # This broad discovery pool contains many archival/object photographs.
        # Give retained direct artwork evidence priority without approving it.
        return 3
    if not work.get("artist") or work["artist"].casefold().startswith(
        ("unknown", "made by", "anonymous")
    ):
        return 1
    return 0


def preview_candidates(
    records: list[dict],
    done: set[int],
    limit: int,
    pool_ids: set[int] | None = None,
) -> list[dict]:
    """Order a bounded retained pool; never approve or discard another pool."""
    if not 1 <= limit <= 600:
        raise ValueError("bounded thumbnail pass")
    return sorted(
        [
            work
            for work in records
            if not work["reasons"]
            and work["id"] not in done
            and (pool_ids is None or work["id"] in pool_ids)
        ],
        key=preview_priority,
    )[:limit]


def thumbnails(limit: int, pool: str | None = None) -> None:
    from frame_gallery.net.policy import RequestKind
    from frame_gallery.providers.commons import _image_url
    from frame_gallery.providers.contract import SourceError

    if not 1 <= limit <= 600:
        raise ValueError("bounded thumbnail pass")
    pool_file = research_pool(pool)
    pool_ids = (
        {w["id"] for w in json.loads((OUTPUT / pool_file).read_text())["candidates"]}
        if pool_file is not None
        else None
    )
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
    works = preview_candidates(report["records"], done, limit, pool_ids)
    channel, deadline = research_channel(1)
    for work in works:
        if deadline.remaining() < 45:
            print(json.dumps(dict(status="finite time cap; preview progress retained")))
            return
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
    parser.add_argument("--pool", choices=RESEARCH_POOLS)
    args = parser.parse_args()
    if args.pool is not None and args.mode not in ("metadata", "thumbnails"):
        parser.error("--pool only selects retained metadata or preview candidates")
    if args.mode == "metadata":
        metadata(args.limit, args.pool)
    elif args.mode == "thumbnails":
        thumbnails(args.limit, args.pool)
    elif args.mode == "sheets":
        sheets()
    else:
        report = json.loads((OUTPUT / "review.json").read_text())
        print(json.dumps(Counter(w["status"] for w in report["records"])))
