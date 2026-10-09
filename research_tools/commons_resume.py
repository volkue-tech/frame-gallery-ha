"""Offline evidence maintenance and transcription of inspected sheets.

No automatic acceptance. Reparse saved public evidence; preserve source hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime

from research_tools.commons_colours import run_worker, save
from research_tools.commons_expand import OUTPUT
from research_tools.commons_review import prepare

# Actually viewed sheets 018--038 on 2026-10-09. These only pass the visual
# first screen; physical proportions, source rights and duplicate review follow.
SECOND_PLAUSIBLE = {
    299,
    300,
    301,
    302,
    303,
    304,
    307,
    308,
    309,
    310,
    311,
    312,
    313,
    314,
    315,
    316,
    317,
    318,
    319,
    320,
    323,
    324,
    326,
    327,
    328,
    329,
    330,
    334,
    335,
    336,
    337,
    338,
    341,
    342,
    379,
    381,
    383,
    410,
    412,
    415,
    416,
    424,
    425,
    430,
    457,
}
SECOND_REASONS = {
    305: "alternative scan of position 298; not another artwork",
    306: "detail of triptych, not whole artwork",
    321: "three-dimensional object photograph",
    322: "surrounding gold frame",
    325: "detail of a larger painting",
    331: "framed triptych photograph",
    332: "framed alternative scan of position 331",
    333: "visible black surrounding border",
    339: "dark detail, not whole Return of the Prodigal Son",
    340: "cropped textile/clothing detail, not whole portrait",
    343: "monochrome alternative; duplicate and quality review deferred",
    359: "visible surrounding frame",
    406: "explicitly labelled detail",
    411: "visible surrounding frame",
    413: "alternative Cleopatra scan of position 412",
    414: "monochrome alternative of position 415",
    421: "framed triptych; surrounding seams/borders",
    422: "four panels of larger multi-panel work, not standalone reproduction",
    423: "alternative Garden of Earthly Delights scan of position 421",
    447: "back of artwork, not artwork",
    448: "war casualty drawing; reserve, not colourful gallery priority",
    508: "detail of larger calligraphic painting",
    509: "detail of larger calligraphic painting",
    510: "detail of larger calligraphic painting",
}


def screen() -> None:
    works = json.loads((OUTPUT / "profiles.json").read_text())["profiles"]
    destination = OUTPUT / "visual-screen-002.json"
    if destination.exists():
        previous = json.loads(destination.read_text())
        for row, work in zip(previous["records"], works[299:609], strict=True):
            if (
                row["id"] != work["id"]
                or row["thumbnail_sha256"] != work["thumbnail_sha256"]
            ):
                raise ValueError("inspected source order or preview changed")
        print(json.dumps(dict(screened=310, status="retained second screen")))
        return
    rows = []
    for position in range(299, 609):
        work = works[position]
        sheet = OUTPUT / f"sheet-{position // 16:03}.jpg"
        rows.append(
            dict(
                id=work["id"],
                original_sha1=work["original_sha1"],
                thumbnail_sha256=work["thumbnail_sha256"],
                contact_sheet_position=position,
                contact_sheet_sha256=hashlib.sha256(sheet.read_bytes()).hexdigest(),
                screen="visual first-pass"
                if position in SECOND_PLAUSIBLE
                else "deferred",
                reason=(
                    "complete reproduction visually plausible; provenance, physical "
                    "proportions and duplicate review required"
                )
                if position in SECOND_PLAUSIBLE
                else SECOND_REASONS.get(
                    position,
                    "archival/monochrome paper page, object photograph or "
                    "surrounding scan margins; not colourful-gallery priority",
                ),
            )
        )
    save(
        destination,
        dict(
            schema=1,
            inspected_at=datetime.now(UTC).isoformat(),
            status="visual screening only; no catalogue approvals",
            records=rows,
        ),
    )
    print(json.dumps(dict(screened=len(rows), plausible=len(SECOND_PLAUSIBLE))))


def reparse() -> None:
    path = OUTPUT / "review.json"
    report = json.loads(path.read_text())
    for index, old in enumerate(report["records"]):
        evidence = OUTPUT / old["evidence_file"]
        if hashlib.sha256(evidence.read_bytes()).hexdigest() != old["evidence_sha256"]:
            raise ValueError("raw source receipt changed")
        pages = json.loads(evidence.read_text())["query"]["pages"]
        page = next(p for p in pages if p["pageid"] == old["id"])
        expected = {
            k: old[k]
            for k in ("id", "file_title", "sha1", "width", "height", "source", "query")
        }
        new = prepare(page, expected)
        if new["source_page_sha256"] != old["source_page_sha256"]:
            raise ValueError("source revision changed offline")
        new.update(
            evidence_file=old["evidence_file"],
            evidence_sha256=old["evidence_sha256"],
            checked_at=old["checked_at"],
            reparsed_at=datetime.now(UTC).isoformat(),
        )
        report["records"][index] = new
    save(path, report)
    by_id = {w["id"]: w for w in report["records"]}
    profiles_path = OUTPUT / "profiles.json"
    profiles = json.loads(profiles_path.read_text())
    for work in profiles["profiles"]:
        old = run_worker(OUTPUT / f"{work['id']}.jpg")
        if old["thumbnail_sha256"] != work["thumbnail_sha256"]:
            raise ValueError("thumbnail changed offline")
        for key in ("distribution", "palette", "search_colours", "dimensions"):
            if old[key] != work[key]:
                raise ValueError("analysis changed offline")
        for key in ("oriented_dimensions", "exif_orientation"):
            work[key] = old[key]
        for key in ("title", "artist"):
            work[key] = by_id[work["id"]][key]
    save(profiles_path, profiles)
    print(
        json.dumps(
            dict(
                records=len(report["records"]),
                eligible=sum(not w["reasons"] for w in report["records"]),
                orientation_verified=len(profiles["profiles"]),
            )
        )
    )


def failures() -> None:
    """Retain the two actually observed failures from the pre-receipt tools."""
    path = OUTPUT / "profiles.json"
    previews = json.loads(path.read_text())
    rows = previews.setdefault("network_deferred", [])
    if not any(row["id"] == 64086561 for row in rows):
        rows.append(
            dict(
                id=64086561,
                reason="Observed exchange timeout fetching CH 18193649 thumbnail; "
                "not a permanent artwork rejection",
                kind="timeout",
                recorded_at=datetime.now(UTC).isoformat(),
                retry="no automatic retry; future separately reviewed retry only",
            )
        )
        save(path, previews)
    path = OUTPUT / "discovery-targeted.json"
    report = json.loads(path.read_text())
    query = (
        'filemime:"image/jpeg" filew:20001,100000 fileh:10976,57693 "Camille Pissarro"'
    )
    # The exact next query follows the last saved completed width window.
    # Its old tool did not save refused responses: preserve that limitation.
    rows = report.setdefault("deferred_queries", [])
    if not any(row["query"] == query for row in rows):
        if len(report["completed_queries"]) != 194:
            raise ValueError("old search refusal context changed")
        rows.append(
            dict(
                query=query,
                reason="Observed targeted API response refusal after 194 queries; "
                "old implementation did not retain response detail",
                recorded_at=datetime.now(UTC).isoformat(),
                retry="no automatic retry; individual future review required",
            )
        )
        save(path, report)
    print(json.dumps(dict(retained_network_deferrals=2)))


def third_screen() -> None:
    """Transcribe the actually viewed candidate sheets 038--041, not a classifier."""
    plausible = {
        612,
        613,
        615,
        616,
        618,
        620,
        621,
        623,
        624,
        626,
        627,
        628,
        630,
        635,
        639,
        641,
        643,
        645,
        646,
        651,
        652,
        653,
        655,
        656,
        657,
        659,
        660,
        661,
        662,
        663,
        664,
        665,
        666,
    }
    framed = {625, 632, 638, 640, 642}
    details = {629, 631, 633, 654}
    bordered = {644, 647, 648, 649, 650}
    works = json.loads((OUTPUT / "profiles.json").read_text())["profiles"]
    path = OUTPUT / "visual-screen-003.json"
    if path.exists():
        saved = json.loads(path.read_text())["records"]
        for row, work in zip(saved, works[609:667], strict=True):
            if (
                row["id"] != work["id"]
                or row["thumbnail_sha256"] != work["thumbnail_sha256"]
            ):
                raise ValueError("third inspected preview changed")
        return
    rows = []
    for position in range(609, 667):
        work = works[position]
        reason = (
            "complete reproduction visually plausible; source/identity review pending"
            if position in plausible
            else "surrounding frame or museum photograph"
            if position in framed
            else "detail/crop of larger work, not complete reproduction"
            if position in details
            else "surrounding paper border/sketch sheet; deferred quality"
            if position in bordered
            else "dark/war/monochrome or damaged reproduction; not gallery priority"
        )
        rows.append(
            dict(
                id=work["id"],
                original_sha1=work["original_sha1"],
                thumbnail_sha256=work["thumbnail_sha256"],
                contact_sheet_position=position,
                contact_sheet_sha256=hashlib.sha256(
                    (OUTPUT / f"sheet-{position // 16:03}.jpg").read_bytes()
                ).hexdigest(),
                screen="visual first-pass" if position in plausible else "deferred",
                reason=reason,
            )
        )
    save(path, dict(schema=1, inspected_at=datetime.now(UTC).isoformat(), records=rows))
    print(json.dumps(dict(third_screened=58, plausible=len(plausible))))


def fourth_screen() -> None:
    """Transcribe sheets 041--065 actually viewed, without catalogue approval."""
    plausible = {
        668,
        671,
        674,
        675,
        677,
        678,
        680,
        682,
        686,
        687,
        689,
        690,
        692,
        693,
        694,
        696,
        697,
        699,
        700,
        702,
        704,
        706,
        709,
        710,
        712,
        713,
        714,
        734,
        752,
        791,
        794,
        795,
        800,
        821,
        823,
        827,
        831,
        835,
        849,
        850,
        860,
        861,
        862,
        863,
        864,
        865,
        904,
        907,
        917,
        928,
        932,
        962,
        993,
        1001,
        1007,
        1011,
        1015,
        1021,
        1022,
        1024,
        1025,
        1029,
        1037,
        1044,
        1047,
        1050,
        1051,
        1052,
        1055,
    }
    works = json.loads((OUTPUT / "profiles.json").read_text())["profiles"]
    path = OUTPUT / "visual-screen-004.json"
    if path.exists():
        saved = json.loads(path.read_text())["records"]
        for row, work in zip(saved, works[667:1056], strict=True):
            if (
                row["id"] != work["id"]
                or row["thumbnail_sha256"] != work["thumbnail_sha256"]
            ):
                raise ValueError("fourth inspected preview changed")
        return
    rows = []
    for position in range(667, 1056):
        work = works[position]
        rows.append(
            dict(
                id=work["id"],
                original_sha1=work["original_sha1"],
                thumbnail_sha256=work["thumbnail_sha256"],
                contact_sheet_position=position,
                contact_sheet_sha256=hashlib.sha256(
                    (OUTPUT / f"sheet-{position // 16:03}.jpg").read_bytes()
                ).hexdigest(),
                screen="visual first-pass" if position in plausible else "deferred",
                reason=(
                    "Complete reproduction visually plausible; physical "
                    "proportions, source and artwork identity need second review"
                )
                if position in plausible
                else (
                    "Observed frame/margin, archival page, object photo, artwork "
                    "detail/alternative scan or muted/repetitive motif; "
                    "not gallery priority"
                ),
            )
        )
    save(
        path,
        dict(
            schema=1,
            inspected_at=datetime.now(UTC).isoformat(),
            status="Actual first visual screen only; no automatic acceptance",
            records=rows,
        ),
    )
    print(json.dumps(dict(fourth_screened=len(rows), plausible=len(plausible))))


def fifth_screen() -> None:
    """Transcribe sheets 066--079 actually viewed; no automatic acceptance."""
    plausible = {
        1069,
        1070,
        1071,
        1075,
        1079,
        1080,
        1082,
        1083,
        1089,
        1102,
        1103,
        1109,
        1133,
        1151,
        1153,
        1160,
        1163,
        1165,
        1166,
        1167,
        1172,
        1173,
        1176,
        1189,
        1193,
        1220,
        1221,
        1224,
        1225,
        1235,
        1239,
        1240,
        1242,
        1243,
        1244,
        1245,
        1249,
        1251,
        1256,
        1258,
        1260,
        1267,
    }
    works = json.loads((OUTPUT / "profiles.json").read_text())["profiles"]
    path = OUTPUT / "visual-screen-005.json"
    if path.exists():
        saved = json.loads(path.read_text())["records"]
        for row, work in zip(saved, works[1056:1268], strict=True):
            if (
                row["id"] != work["id"]
                or row["thumbnail_sha256"] != work["thumbnail_sha256"]
            ):
                raise ValueError("fifth inspected preview changed")
        return
    rows = []
    for position in range(1056, 1268):
        work = works[position]
        rows.append(
            dict(
                id=work["id"],
                original_sha1=work["original_sha1"],
                thumbnail_sha256=work["thumbnail_sha256"],
                contact_sheet_position=position,
                contact_sheet_sha256=hashlib.sha256(
                    (OUTPUT / f"sheet-{position // 16:03}.jpg").read_bytes()
                ).hexdigest(),
                screen="visual first-pass" if position in plausible else "deferred",
                reason=(
                    "Complete reproduction visually plausible; source, physical "
                    "proportions and artwork identity require second review"
                )
                if position in plausible
                else (
                    "Observed object/frame/chart/book page, detail or alternative "
                    "scan; "
                    "or muted/repetitive archival motif, not colourful-gallery priority"
                ),
            )
        )
    save(
        path,
        dict(
            schema=1,
            inspected_at=datetime.now(UTC).isoformat(),
            status="Actual first visual screen only; no automatic acceptance",
            records=rows,
        ),
    )
    print(json.dumps(dict(fifth_screened=len(rows), plausible=len(plausible))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=("screen", "reparse", "failures", "third", "fourth", "fifth")
    )
    args = parser.parse_args()
    if args.mode == "screen":
        screen()
    elif args.mode == "reparse":
        reparse()
    elif args.mode == "failures":
        failures()
    elif args.mode == "third":
        third_screen()
    elif args.mode == "fourth":
        fourth_screen()
    else:
        fifth_screen()
