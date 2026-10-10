"""Separate CC research receipts; never change PD/CC0 admission or runtime pins.

An own-source statement is a research lead, NOT clearance of depicted artwork.
Keep full raw rights metadata and explicit attribution/change obligations before
manual original-work, visual, duplicate and release-design review.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from collections import Counter
from datetime import UTC, datetime

from research_tools.commons_colours import LABELS, MAX_AXIS, MAX_BYTES, run_worker, save
from research_tools.commons_expand import OUTPUT, eligible
from research_tools.commons_review import (
    PlainText,
    plain,
    research_channel,
    source_markup,
)

REPORT = OUTPUT / "cc-research.json"
PROFILES = OUTPUT / "cc-profiles.json"
FULL_RIGHTS = OUTPUT / "cc-full-rights.json"
LICENCE = re.compile(r"https://creativecommons\.org/licenses/(by|by-sa)/(3\.0|4\.0)/?")


def notice_text(raw: object) -> str:
    """Retain complete supplied notices, not the short display-caption limit."""
    if not isinstance(raw, str) or len(raw) > 100000:
        return ""
    parser = PlainText()
    parser.feed(raw)
    return " ".join("".join(parser.parts).split())


def self_licences(text: str) -> set[str]:
    """Literal positional Self fields only, not comments/named author/examples."""
    result = set()
    markup = source_markup(text)
    for outer in re.finditer(r"\{\{\s*self\b", markup, re.I):
        depth, start = 1, outer.end()
        for token in re.finditer(r"\{\{|}}|\|", markup[outer.end() :]):
            end = outer.end() + token.start()
            if depth == 1 and token[0] in ("|", "}}"):
                field = markup[start:end].strip().lower()
                if "=" in field:
                    key, field = field.split("=", 1)
                    field = field.strip()
                    if not key.strip().isdigit() or not 1 <= int(key.strip()) <= 6:
                        field = ""
                if re.fullmatch(r"cc-by(?:-sa)?-(?:3\.0|4\.0)", field):
                    result.add(field)
                start = end + len(token[0])
            if token[0] == "{{":
                depth += 1
            elif token[0] == "}}":
                depth -= 1
                if not depth:
                    break
    return result


def assess(page: dict, expected: dict) -> dict:
    """Conservative preview eligibility, not a rights/curation approval."""
    infos = page.get("imageinfo", [])
    info = (
        infos[0]
        if isinstance(infos, list) and len(infos) == 1 and isinstance(infos[0], dict)
        else {}
    )
    revisions = page.get("revisions", [])
    revision = (
        revisions[0]
        if isinstance(revisions, list)
        and len(revisions) == 1
        and isinstance(revisions[0], dict)
        else {}
    )
    slots = revision.get("slots", {})
    slot = slots.get("main", {}) if isinstance(slots, dict) else {}
    text = slot.get("content", "") if isinstance(slot, dict) else ""
    blockers = []
    if not isinstance(text, str) or not 0 < len(text) <= 500000:
        text = ""
        blockers.append("missing/bounded source revision")
    if type(revision.get("revid")) is not int or revision["revid"] <= 0:
        blockers.append("missing source revision identity")
    if (
        page.get("pageid") != expected["id"]
        or page.get("title") != expected["file_title"]
        or page.get("ns") != 6
        or page.get("imagerepository") != "local"
        or info.get("sha1") != expected["sha1"]
        or not eligible(info)
    ):
        blockers.append("source identity/upload/format changed")
    metadata = info.get("extmetadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    values = {
        key: value.get("value")
        for key, value in metadata.items()
        if isinstance(value, dict)
    }
    licence_url = values.get("LicenseUrl", "")
    match = LICENCE.fullmatch(licence_url) if isinstance(licence_url, str) else None
    family, version = match.groups() if match else (None, None)
    tag = f"cc-{family}-{version}" if match else None
    expected_label = f"CC {family.upper()} {version}" if match else None
    if (
        tag not in self_licences(text)
        or values.get("LicenseShortName") != expected_label
        or str(values.get("AttributionRequired", "")).lower() != "true"
        or str(values.get("Copyrighted", "")).lower() != "true"
        or plain(values.get("Restrictions"))
    ):
        blockers.append("active Self licence and rendered rights do not agree")
    if version == "3.0":
        blockers.append("version 3.0 obligations require separate source review")
    markup = source_markup(text)
    if not re.search(r"^\s*\|\s*source\s*=\s*\{\{\s*own\s*}}\s*$", markup, re.I | re.M):
        blockers.append("no explicit own-source declaration; separate rights review")
    if re.search(r"\{\{\s*(?:Art Photo|FoP|PD-Art)(?=[\s|}-])", markup, re.I):
        blockers.append("separate depicted-work/reproduction scope")
    description = plain(values.get("ImageDescription"))
    # One literal own-photography description refers to natural garden flowers,
    # not a pre-existing copyrighted artwork. Keep other derivative statements
    # in the same caption visible; this is preview research, never admission.
    scope_description = re.sub(
        r"^Photographic art based on garden flowers \(Agapanthus\)",
        "Own floral photograph",
        description,
    )
    if re.search(
        r"\b(?:based? on|base on|FRACT files|derivative|adapted from|"
        r"photograph of|photo of|Kusama|Anadol)\b",
        scope_description,
        re.I,
    ):
        blockers.append("declared/possible third-party underlying work")
    creator = plain(values.get("Artist"))
    if not creator:
        blockers.append("missing creator credit")
    return dict(
        id=expected["id"],
        file_title=expected["file_title"],
        source=expected["source"],
        original_sha1=expected["sha1"],
        width=info.get("width"),
        height=info.get("height"),
        source_revision=revision.get("revid"),
        source_page_sha256=hashlib.sha256(text.encode()).hexdigest(),
        title=plain(values.get("ObjectName")) or expected["file_title"][5:],
        creator=creator,
        description=description,
        licence=expected_label,
        licence_url=licence_url if match else None,
        licence_version=version,
        share_alike=family == "by-sa" if match else None,
        attribution={
            key: notice_text(values.get(key))
            for key in (
                "Artist",
                "ObjectName",
                "Credit",
                "Attribution",
                "UsageTerms",
                "Copyright",
                "CopyrightNotice",
                "Disclaimer",
                "LicenseShortName",
                "Permission",
            )
        },
        supplied_rights_metadata=metadata,
        notices_complete=False,
        notices_note="Older receipts requested selected fields only; retrieve full "
        "rights metadata before any CC admission/attribution approval",
        modification_notice_required=True,
        preview_changes="Downscaled/re-encoded research preview; no crop intended",
        future_tv_changes="Proportional resize, JPEG conversion and optional padding; "
        "describe actual changes, retain prior notices; no artwork relicensing",
        thumbnail_url=info.get("thumburl"),
        thumbnail_mime=info.get("thumbmime"),
        reported_thumbnail_dimensions=[info.get("thumbwidth"), info.get("thumbheight")],
        preview_blockers=blockers,
        review_prompts=[
            "Verify that the stated creator licences the artwork itself, "
            "not just a photo",
            "Inspect complete composition, artistic merit, variety "
            "and duplicate identity",
            "Design mandatory accessible credit/licence/notices "
            "before runtime admission",
        ],
        status="research lead only; NOT accepted; runtime PD/CC0 gate unchanged",
    )


def audit() -> None:
    records = json.loads((OUTPUT / "review.json").read_text())["records"]
    rows = []
    for old in records:
        if not str(old.get("rights_label", "")).startswith("CC BY"):
            continue
        path = OUTPUT / old["evidence_file"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != old["evidence_sha256"]:
            raise ValueError("retained raw source receipt changed")
        page = next(
            p
            for p in json.loads(path.read_text())["query"]["pages"]
            if p["pageid"] == old["id"]
        )
        row = assess(page, old)
        row.update(evidence_file=old["evidence_file"], evidence_sha256=digest)
        rows.append(row)
    report = dict(
        schema=1,
        approval_date="2026-10-10",
        scope="CC BY/SA research only",
        created_at=datetime.now(UTC).isoformat(),
        records=rows,
        status="NOT accepted works; no runtime/release policy change",
        sources=[
            "https://creativecommons.org/licenses/by/4.0/",
            "https://creativecommons.org/licenses/by-sa/4.0/",
            "https://commons.wikimedia.org/wiki/Commons:Licensing",
        ],
    )
    save(REPORT, report)
    print(
        json.dumps(
            dict(
                records=len(rows),
                preview_leads=sum(not r["preview_blockers"] for r in rows),
                leading_creators=Counter(r["creator"] for r in rows).most_common(8),
            )
        )
    )


def full_metadata(limit: int) -> None:
    """Fetch all extmetadata for decoded pilot leads; preserve old receipts."""
    from frame_gallery.net.policy import https_url
    from frame_gallery.providers.contract import SourceError

    if not 1 <= limit <= 100:
        raise ValueError("bounded CC metadata pilot")
    profiles = json.loads(PROFILES.read_text())["profiles"]
    old = {r["id"]: r for r in json.loads(REPORT.read_text())["records"]}
    report = (
        json.loads(FULL_RIGHTS.read_text())
        if FULL_RIGHTS.exists()
        else dict(
            schema=1,
            records=[],
            network_deferred=[],
            status="Full CC research metadata; manual notice/work-scope review pending",
        )
    )
    done = {r["id"] for k in ("records", "network_deferred") for r in report[k]}
    works = [old[p["id"]] for p in profiles if p["id"] not in done][:limit]
    channel, deadline = research_channel(25)
    for offset in range(0, len(works), 5):
        if deadline.remaining() < 45:
            break
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
            ("maxlag", "5"),
        )
        try:
            document = channel.get_json(
                https_url("commons.wikimedia.org", "/w/api.php", query), deadline
            )
        except SourceError as error:
            report["network_deferred"].extend(
                dict(
                    id=w["id"],
                    kind=error.kind.value,
                    retry="no automatic retry",
                )
                for w in batch
            )
            save(FULL_RIGHTS, report)
            raise
        path = OUTPUT / f"cc-full-metadata-{batch[0]['id']}.json"
        save(path, document)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        pages = document.get("query", {}).get("pages", [])
        for work in batch:
            page = next((p for p in pages if p.get("pageid") == work["id"]), {})
            expected = dict(work, sha1=work["original_sha1"])
            row = assess(page, expected)
            row.update(
                all_extmetadata_requested=True,
                notices_complete=False,
                notices_note="All returned rights metadata and raw source retained; "
                "manual supplied-notice/source review still required",
                evidence_file=path.name,
                evidence_sha256=digest,
                prior_evidence_file=work["evidence_file"],
                prior_evidence_sha256=work["evidence_sha256"],
                source_revision_changed=(
                    row["source_page_sha256"] != work["source_page_sha256"]
                ),
                checked_at=datetime.now(UTC).isoformat(),
            )
            report["records"].append(row)
        save(FULL_RIGHTS, report)
        print(json.dumps(dict(cc_full_metadata=len(report["records"]))))


def refresh_notices() -> None:
    """Reparse complete retained rights receipts offline; no new source claim."""
    report = json.loads(FULL_RIGHTS.read_text())
    for old in report["records"]:
        path = OUTPUT / old["evidence_file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != old["evidence_sha256"]:
            raise ValueError("retained full rights receipt changed")
        page = next(
            p
            for p in json.loads(path.read_text())["query"]["pages"]
            if p["pageid"] == old["id"]
        )
        parsed = assess(page, dict(old, sha1=old["original_sha1"]))
        if parsed["source_page_sha256"] != old["source_page_sha256"]:
            raise ValueError("retained full rights source changed")
        old["attribution"] = parsed["attribution"]
    report["offline_notice_reparse_at"] = datetime.now(UTC).isoformat()
    save(FULL_RIGHTS, report)
    print(json.dumps(dict(offline_notice_records=len(report["records"]))))


def preview_pilot(records, done, previous_counts, pool_ids, limit, author_cap):
    """A finite, varied preview selection; blockers/deferrals remain excluded."""
    if not 1 <= limit <= 100 or not 1 <= author_cap <= 25:
        raise ValueError("bounded varied research pilot")
    counts = Counter(previous_counts)
    selected = []
    for work in sorted(records, key=lambda w: w["id"]):
        if (
            work["preview_blockers"]
            or work["id"] in done
            or work["id"] not in pool_ids
            or counts[work["creator"]] >= author_cap
        ):
            continue
        counts[work["creator"]] += 1
        selected.append(work)
        if len(selected) == limit:
            break
    return selected


def previews(limit: int, author_cap: int, pool: str) -> None:
    from frame_gallery.net.policy import RequestKind
    from frame_gallery.providers.commons import _image_url
    from frame_gallery.providers.contract import SourceError

    if not 1 <= limit <= 100 or not 1 <= author_cap <= 25:
        raise ValueError("bounded varied research pilot")
    if pool not in {
        "fractal-art",
        "digital-art",
        "abstract-photography",
        "fine-art-photography",
        "artistic-composition",
    }:
        raise ValueError("unknown fixed CC research pool")
    report = json.loads(REPORT.read_text())
    if pool == "artistic-composition":
        # Discovery prioritization only. A caption saying "painting" does not
        # establish original-work rights; all existing preview blockers apply.
        pool_ids = {
            row["id"]
            for row in report["records"]
            if re.search(
                r"\b(?:painting|illustration|composition|photographic art)\b",
                row["title"] + " " + row["description"],
                re.I,
            )
            and not re.search(
                r"\b(?:museum|mural|airport|church|palace|hotel|festival|"
                r"in action|retouching|participants|room|visitor centre)\b",
                row["title"] + " " + row["description"],
                re.I,
            )
        }
    else:
        pool_ids = {
            row["id"]
            for row in json.loads(
                (OUTPUT / f"discovery-subject-{pool}.json").read_text()
            )["candidates"]
        }
    profiles = (
        json.loads(PROFILES.read_text())
        if PROFILES.exists()
        else dict(
            schema=1,
            profiles=[],
            refused=[],
            network_deferred=[],
            status="CC preview research only; NOT accepted works",
        )
    )
    done = {
        p["id"]
        for key in ("profiles", "refused", "network_deferred")
        for p in profiles[key]
    }
    selected = preview_pilot(
        report["records"],
        done,
        Counter(p["creator"] for p in profiles["profiles"]),
        pool_ids,
        limit,
        author_cap,
    )
    channel, deadline = research_channel(1)
    for work in selected:
        if deadline.remaining() < 45:
            break
        url = _image_url(work["thumbnail_url"], channel.policy)
        dimensions = work["reported_thumbnail_dimensions"]
        if (
            url is None
            or work["thumbnail_mime"] != "image/jpeg"
            or any(type(v) is not int or not 0 < v <= MAX_AXIS for v in dimensions)
        ):
            profiles["refused"].append(
                dict(id=work["id"], reason="thumbnail metadata bound")
            )
            save(PROFILES, profiles)
            continue

        class Sink:
            def __init__(self):
                self.data = bytearray()

            def write(self, chunk):
                if len(self.data) + len(chunk) > MAX_BYTES:
                    raise ValueError("thumbnail byte cap")
                self.data.extend(chunk)

        sink = Sink()
        try:
            channel._request(url, RequestKind.IMAGE, deadline, sink)
        except SourceError as error:
            profiles["network_deferred"].append(
                dict(
                    id=work["id"],
                    kind=error.kind.value,
                    retry="no automatic retry; separately reviewed future retry only",
                )
            )
            save(PROFILES, profiles)
            raise
        path = OUTPUT / f"cc-{work['id']}.jpg"
        path.write_bytes(sink.data)
        try:
            profile = run_worker(path)
            actual = profile["dimensions"]
            if abs(actual[0] / actual[1] / (dimensions[0] / dimensions[1]) - 1) > 0.015:
                raise ValueError("thumbnail ratio disagreement")
        except ValueError:
            profiles["refused"].append(dict(id=work["id"], reason="decode/shape bound"))
            save(PROFILES, profiles)
            continue
        profile.update(
            **{
                k: work[k]
                for k in (
                    "id",
                    "title",
                    "creator",
                    "licence",
                    "licence_url",
                    "source",
                    "source_revision",
                    "source_page_sha256",
                    "original_sha1",
                    "evidence_file",
                    "evidence_sha256",
                )
            },
            status="decoded CC research lead; NOT curator approval",
        )
        profiles["profiles"].append(profile)
        save(PROFILES, profiles)
        print(json.dumps(dict(cc_previews=len(profiles["profiles"]), id=work["id"])))


def sheets() -> None:
    from PIL import Image, ImageDraw, ImageOps

    profiles = json.loads(PROFILES.read_text())["profiles"]
    for start in range(0, len(profiles), 16):
        sheet = Image.new("RGB", (1600, 1120), "#eceae5")
        draw = ImageDraw.Draw(sheet)
        for index, work in enumerate(profiles[start : start + 16]):
            path = OUTPUT / f"cc-{work['id']}.jpg"
            if (
                hashlib.sha256(path.read_bytes()).hexdigest()
                != work["thumbnail_sha256"]
            ):
                raise ValueError("CC preview changed")
            with Image.open(path) as opened:
                image = ImageOps.exif_transpose(opened).convert("RGB")
            image.thumbnail((390, 219))
            x, y = index % 4 * 400, index // 4 * 280
            sheet.paste(image, (x + (400 - image.width) // 2, y))
            draw.text(
                (x + 6, y + 221), f"#{start + index} · {work['id']}", fill="black"
            )
            draw.text((x + 6, y + 239), work["creator"][:55], fill="black")
            draw.text((x + 6, y + 257), work["title"][:55], fill="black")
        # Hash-addressed sheets keep actual viewed evidence through later appends.
        path = OUTPUT / f"cc-sheet-{start // 16:03}.jpg"
        if path.exists():
            old = path.read_bytes()
            archive = path.with_name(
                f"{path.stem}-{hashlib.sha256(old).hexdigest()[:16]}.jpg"
            )
            if not archive.exists():
                archive.write_bytes(old)
        sheet.save(path, quality=94)
    print(
        json.dumps(dict(cc_previews=len(profiles), sheets=(len(profiles) + 15) // 16))
    )


def pilot_review() -> None:
    """Transcribe CC sheets 000--005 actually viewed on 2026-10-10; no admission."""
    initial = [
        79084437,
        79084439,
        79084440,
        79084443,
        79084444,
        79084448,
        79084449,
        79084450,
        79084453,
        79084455,
        79084458,
        79084459,
        109614002,
        138312367,
        66650186,
        70282948,
        79505810,
        110526834,
        114214780,
        114257101,
        123118292,
        123579698,
        124227780,
        124229187,
        141184909,
        171449241,
        178576923,
        182684373,
        183879370,
        170850628,
        171229726,
        200070018,
        63062883,
        88681104,
        97149779,
        97149780,
        97342056,
        121747071,
        130006397,
        130653987,
        130655630,
        131664405,
        145862641,
        145862642,
        145862647,
        145862648,
        145862649,
        145862653,
        173602593,
        186689650,
        34169247,
        34530099,
        41901548,
        43103287,
        45688028,
        45688030,
        45688031,
        45688032,
        45741636,
        47011320,
        48935323,
        48935324,
        49591524,
        50215328,
        53423185,
        54620895,
        54976122,
        59616774,
        59755095,
        60742078,
        60742080,
        61228560,
        62693392,
        63160782,
        63568228,
        63710695,
        64623996,
        65090101,
        67765911,
        69735907,
        72530722,
        72530826,
        74606313,
        77028514,
        78234263,
        78234415,
        78890797,
        79465159,
        80695274,
        80831967,
    ]
    promising = {
        79084443,
        79084444,
        79084449,
        79084455,
        109614002,
        66650186,
        79505810,
        110526834,
        124227780,
        141184909,
        171449241,
        170850628,
        171229726,
        63062883,
        88681104,
        121747071,
        145862649,
        173602593,
        78234263,
        78234415,
        78890797,
    }
    extra_prompts = {
        63062883: "VRT ticket recorded; separately check embedded "
        "depicted artwork/assets",
        121747071: "Retain both named collaborators and independently "
        "check rendered-model scope",
        145862649: "Check Tom Taylor Entertainment/film character "
        "and scene asset rights",
        173602593: "Own declaration by KristaKim account is not "
        "independent authentication of the artist",
        78234263: "Verified-account and permission-ticket declarations recorded; "
        "check complete painting/model-rights scope, not just photo ownership",
        78234415: "Verified-account and permission-ticket declarations recorded; "
        "check complete painting/model-rights scope, not just photo ownership",
        78890797: "Tutorial/marketing caption is not independent proof "
        "of original illustration and asset rights",
    }
    profiles = json.loads(PROFILES.read_text())["profiles"][:90]
    if [p["id"] for p in profiles] != initial:
        raise ValueError("actually viewed CC pilot order changed")
    rights = {r["id"]: r for r in json.loads(FULL_RIGHTS.read_text())["records"]}
    rows = []
    for index, profile in enumerate(profiles):
        work_id = profile["id"]
        source = rights[work_id]
        sheet = OUTPUT / f"cc-sheet-{index // 16:03}.jpg"
        sheet_hash = hashlib.sha256(sheet.read_bytes()).hexdigest()
        archived = sheet.with_name(f"{sheet.stem}-{sheet_hash[:16]}.jpg")
        if not archived.exists():
            archived.write_bytes(sheet.read_bytes())
        if (
            hashlib.sha256((OUTPUT / f"cc-{work_id}.jpg").read_bytes()).hexdigest()
            != profile["thumbnail_sha256"]
            or hashlib.sha256(
                (OUTPUT / source["evidence_file"]).read_bytes()
            ).hexdigest()
            != source["evidence_sha256"]
            or source["source_revision_changed"]
            or source["preview_blockers"]
        ):
            raise ValueError("actually reviewed CC pilot evidence changed")
        row = {
            k: source[k]
            for k in (
                "id",
                "title",
                "creator",
                "source",
                "licence",
                "licence_url",
                "source_revision",
                "source_page_sha256",
                "original_sha1",
                "evidence_file",
                "evidence_sha256",
                "attribution",
            )
        }
        row.update(
            thumbnail_sha256=profile["thumbnail_sha256"],
            sheet_position=index,
            sheet_sha256=sheet_hash,
            visual_decision="promising reserve"
            if work_id in promising
            else "deferred variety/quality",
            reason="Actually viewed original digital/photographic composition; "
            "distinctive palette/geometry; no obvious photographed "
            "third-party artwork observed; "
            "reserve only"
            if work_id in promising
            else "Actually viewed repetitive/weak composition, "
            "technical record or unresolved architecture/material scope; "
            "not variety priority",
            artwork_rights_observation="Explicit Own work and matching "
            f"Self {source['licence']}; "
            "not independent proof of every underlying asset or worldwide clearance",
            required_before_admission=[
                "Second individual full-composition and duplicate review",
                "Resolve any named external formula/preset/assets scope",
                "Mandatory accessible attribution and runtime rights validation",
                *([extra_prompts[work_id]] if work_id in extra_prompts else []),
            ],
            preview_changes="Downscaled/re-encoded research preview; no crop intended",
            counts_as_accepted_work=False,
        )
        rows.append(row)
    from research_tools.commons_review import ROOT

    target = ROOT / "research/commons-cc-pilot-review-2026-10-10.json"
    if target.exists():
        old = target.read_bytes()
        archive = OUTPUT / f"cc-screen-{hashlib.sha256(old).hexdigest()}.json"
        if not archive.exists():
            archive.write_bytes(old)
    save(
        target,
        dict(
            schema=1,
            reviewed_at=datetime.now(UTC).isoformat(),
            records=rows,
            status="90 actually viewed CC leads; 21 reserves, NOT catalogue additions",
            accepted_cc_works=0,
        ),
    )
    print(json.dumps(dict(inspected=90, promising_reserves=21, accepted_new_cc=0)))


def cc_card(profile: dict, source: dict) -> str:
    """Escaped research card; source notices are text, never executable markup."""
    work_id = profile["id"]
    licence = LICENCE.fullmatch(source["licence_url"])
    if (
        type(work_id) is not int
        or work_id <= 0
        or source["id"] != work_id
        or licence is None
        or licence[2] != "4.0"
    ):
        raise ValueError("research card source/licence mismatch")
    title, creator = html.escape(source["title"]), html.escape(source["creator"])
    notices = "".join(
        f"<p><b>{html.escape(key)}</b>: {html.escape(value)}</p>"
        for key, value in source["attribution"].items()
        if value
    )
    colours = " · ".join(
        f"{html.escape(LABELS[c['group']])} {c['share']:.0%}"
        for c in profile["top_colours"]
    )
    return (
        f'<article><img src="cc-{work_id}.jpg" loading="lazy" alt="{title}">'
        f"<h2>{title}</h2><p>{creator}</p><p>{colours}</p>"
        "<p><strong>Vorgemerkt, noch nicht aufgenommen</strong></p>"
        f'<p><a href="https://commons.wikimedia.org/w/index.php?curid={work_id}">'
        "Commons-Quelle</a> · "
        f'<a href="{html.escape(source["licence_url"])}">'
        f"{html.escape(source['licence'])}</a></p>"
        "<p>Vorschau proportional verkleinert und als JPEG gespeichert; "
        "kein absichtlicher Beschnitt.</p>"
        "<details><summary>Namensnennung und mitgelieferte Lizenzhinweise</summary>"
        f"{notices}</details></article>"
    )


def gallery() -> None:
    """A separate private CC reserve preview; never inflate the accepted count."""
    from research_tools.commons_colours import OUTPUT as gallery_output
    from research_tools.commons_review import ROOT

    reviewed = json.loads(
        (ROOT / "research/commons-cc-pilot-review-2026-10-10.json").read_text()
    )["records"]
    # A varied entrance to this separate research page, not admission priority.
    entrance = [171229726, 63062883, 173602593, 78234415, 121747071, 170850628]
    rank = {work_id: index for index, work_id in enumerate(entrance)}
    reviewed.sort(key=lambda row: rank.get(row["id"], len(rank)))
    profiles = {p["id"]: p for p in json.loads(PROFILES.read_text())["profiles"]}
    rights = {r["id"]: r for r in json.loads(FULL_RIGHTS.read_text())["records"]}
    cards = []
    for row in reviewed:
        if row["visual_decision"] != "promising reserve":
            continue
        work_id = row["id"]
        profile, source = profiles[work_id], rights[work_id]
        raw = (OUTPUT / f"cc-{work_id}.jpg").read_bytes()
        if (
            hashlib.sha256(raw).hexdigest() != row["thumbnail_sha256"]
            or profile["thumbnail_sha256"] != row["thumbnail_sha256"]
            or hashlib.sha256(
                (OUTPUT / source["evidence_file"]).read_bytes()
            ).hexdigest()
            != row["evidence_sha256"]
            or source["source_page_sha256"] != row["source_page_sha256"]
        ):
            raise ValueError("CC reserve preview evidence changed")
        cards.append(cc_card(profile, source))
        (gallery_output / f"cc-{work_id}.jpg").write_bytes(raw)
    markup = (
        '<!doctype html><html lang="de"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        "<title>Frame Gallery · CC-Recherche</title><style>"
        "body{font:16px system-ui;background:#f6f5f1;color:#18232d;"
        "max-width:1200px;margin:24px auto;padding:0 16px}"
        ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));"
        "gap:24px}article{background:white;padding:14px;border-radius:12px}"
        "img{width:100%;aspect-ratio:16/9;object-fit:contain;background:#181818}"
        "h2{font-size:19px}a{color:#005c92}details p{overflow-wrap:anywhere}"
        "p{line-height:1.5}</style><h1>Moderne Motive · CC-Recherche</h1>"
        f"<p>{len(cards)} vielversprechende Motive, separat vorgemerkt. "
        "Sie zählen noch nicht zum Katalog. Bildrechte, vollständige Komposition, "
        "Duplikate und die spätere verlässlich erreichbare Namensnennung "
        "müssen abschließend geklärt werden.</p>"
        '<p><a href="gallery.html">Zur kuratierten Sammlung und Farbauswahl</a></p>'
        '<div class="grid">' + "".join(cards) + "</div></html>"
    )
    (gallery_output / "cc-gallery.html").write_text(markup)
    print(json.dumps(dict(cc_reserve_preview=len(cards), accepted_new_cc=0)))


if __name__ == "__main__":
    import sys

    from research_tools.commons_review import ROOT

    sys.path.insert(0, str(ROOT / "frame_gallery/src"))
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=(
            "audit",
            "metadata",
            "refresh-notices",
            "previews",
            "sheets",
            "pilot-review",
            "gallery",
        ),
    )
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--author-cap", type=int, default=12)
    parser.add_argument(
        "--pool",
        default="fractal-art",
        choices=(
            "fractal-art",
            "digital-art",
            "abstract-photography",
            "fine-art-photography",
            "artistic-composition",
        ),
    )
    args = parser.parse_args()
    if args.mode == "audit":
        audit()
    elif args.mode == "metadata":
        full_metadata(args.limit)
    elif args.mode == "refresh-notices":
        refresh_notices()
    elif args.mode == "pilot-review":
        pilot_review()
    elif args.mode == "gallery":
        gallery()
    elif args.mode == "previews":
        previews(args.limit, args.author_cap, args.pool)
    else:
        sheets()
