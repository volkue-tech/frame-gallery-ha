"""Offline, resumable human-viewed screening; never catalogue acceptance.

Screening positions refer to the saved contact sheets, and are bound back to
the page ID, original hash and thumbnail hash. Duplicate fingerprints are only
review prompts: they must never automatically reject or approve an artwork.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime

from research_tools.commons_colours import BASELINE, ROOT, run_worker, save
from research_tools.commons_expand import OUTPUT

# Visually inspected contact sheets 000--018. Reasons are conservative
# deferrals, not assertions that a reproduction or artwork is unlawful.
FIRST_SCREEN = {
    1: "museum-photo border/shadow; verify full reproduction",
    24: "visible surrounding frame",
    28: "inscription-heavy ex-voto; reserve rather than colourful-gallery priority",
    48: "visible surrounding frame",
    49: "explicitly labelled fragment, not a complete work",
    50: "two framed paintings in one photograph",
    51: "auction footer/watermark",
    53: "framed triptych photograph",
    58: "paired oval portraits with surrounding whitespace",
    61: "white border/rounded corners; verify complete reproduction",
    79: "ornamented engraving border; not gallery priority",
    81: "sketchbook page, not standalone complete painting",
    83: "visible surrounding frame",
    88: "detail of a larger work",
    89: "monochrome alternative reproduction; duplicate review pending",
    93: "photographic glare/blue cast; reproduction quality deferred",
    99: "sketchbook page",
    101: "monochrome alternative scan of position 16",
    102: "monochrome Counter-composition XVI; existing artwork duplicate",
    104: "framed triptych photograph",
    107: "alternate Bellotto scan of position 103",
    108: "museum-room photograph, not artwork reproduction",
    109: "surrounding band/glare; reproduction quality deferred",
    110: "detail of a larger work",
    111: "outline-only illustration; not gallery priority",
    113: "sketchbook page",
    115: "visible surrounding frame",
    116: "visible surrounding frame",
    117: "framed artwork photograph",
    118: "detail of a larger work",
    120: "sketchbook page",
    127: "monochrome alternative scan; artwork duplicate review pending",
    129: "very dark/damaged reproduction; quality deferred",
    130: "visible surrounding frame",
    135: "detail of a larger work",
    138: "monochrome decorative sketch; reserve, not colourful-gallery priority",
    139: "sketchbook page",
    143: "back of a canvas, not artwork",
    144: "back of a canvas, not artwork",
    145: "visible surrounding frame",
    149: "visible surrounding frame",
    150: "nonrectangular shaped painting with surrounding black area",
    151: "monochrome decorative sketch; reserve",
    153: "detail of a larger portrait",
    154: "detail of a larger portrait",
    155: "detail of a larger portrait",
    157: "framed artwork photographed obliquely",
    159: "alternate Fortress of Koenigstein scan; duplicate review pending",
    164: "visible surrounding frame",
    165: "surrounding paper border/sketch",
    169: "detail of a larger work",
    170: "detail of a larger work",
    171: "detail of a larger work",
    172: "monochrome decorative sketch; reserve",
    175: "visible surrounding frame",
    176: "framed alternate reproduction of position 175",
    177: "detail of a larger portrait",
    178: "detail of a larger portrait",
    188: "visible dark border; reproduction review pending",
    189: "detail of a larger work",
    190: "detail of a larger work",
    191: "visible surrounding frame",
    193: "alternate scan of position 186",
    199: "visible dark border; duplicate review pending",
    203: "visible surrounding frame",
    205: "detail of frame/canvas, not complete painting",
    211: "detail of a larger work",
    213: "back of a canvas, not artwork",
    214: "detail of a larger portrait",
    223: "white band and colour calibration chart",
    235: "visible dark border",
    243: "visible dark border",
    250: "detail of inscription/print, not complete painting",
    260: "visible surrounding frame",
    261: "nonrectangular decoration in large frame",
    262: "detail of frame/canvas, not complete painting",
    267: "visible surrounding frame",
    269: "visible surrounding frame and reflected exit sign",
    272: "framed triptych in museum room",
    284: "illustration in book/page, not standalone reproduction",
    296: "alternate reproduction of position 288",
}


def screen() -> None:
    profiles = json.loads((OUTPUT / "profiles.json").read_text())["profiles"]
    receipt = OUTPUT / "visual-screen-001.json"
    if receipt.exists():
        prior = json.loads(receipt.read_text())["records"]
        if len(prior) == 299:
            for row, work in zip(prior, profiles[:299], strict=True):
                if (
                    row["id"] != work["id"]
                    or row["original_sha1"] != work["original_sha1"]
                ):
                    raise ValueError("inspected profile order/source changed")
                if (
                    row["thumbnail_sha256"]
                    != hashlib.sha256(
                        (OUTPUT / f"{work['id']}.jpg").read_bytes()
                    ).hexdigest()
                ):
                    raise ValueError("inspected thumbnail changed")
            print(
                json.dumps(
                    dict(screened=299, status="retained original inspection receipt")
                )
            )
            return
    records = []
    for position, work in enumerate(profiles[:299]):
        sheet = OUTPUT / f"sheet-{position // 16:03}.jpg"
        records.append(
            dict(
                id=work["id"],
                original_sha1=work["original_sha1"],
                thumbnail_sha256=hashlib.sha256(
                    (OUTPUT / f"{work['id']}.jpg").read_bytes()
                ).hexdigest(),
                contact_sheet_position=position,
                contact_sheet_sha256=hashlib.sha256(sheet.read_bytes()).hexdigest(),
                screen="deferred" if position in FIRST_SCREEN else "visual first-pass",
                reason=FIRST_SCREEN.get(
                    position,
                    "complete reproduction visually plausible; "
                    "provenance and duplicate review still required",
                ),
            )
        )
    save(
        receipt,
        dict(
            schema=1,
            inspected_at=datetime.now(UTC).isoformat(),
            status="screening evidence only; zero catalogue approvals",
            records=records,
        ),
    )
    print(
        json.dumps(dict(screened=len(records), deferred=len(FIRST_SCREEN), accepted=0))
    )


def fingerprints() -> None:
    path = OUTPUT / "profiles.json"
    document = json.loads(path.read_text())
    for work in document["profiles"]:
        if "review_dhash256" not in work:
            new = run_worker(OUTPUT / f"{work['id']}.jpg")
            if new["thumbnail_sha256"] != work["thumbnail_sha256"]:
                raise ValueError("cached thumbnail changed")
            for key in ("distribution", "palette", "search_colours", "dimensions"):
                if new[key] != work[key]:
                    raise ValueError("offline analysis changed")
            work["review_dhash256"] = new["review_dhash256"]
    save(path, document)
    baseline = json.loads(BASELINE.read_text())
    baseline_colours = json.loads(
        (
            ROOT / "frame_gallery/research/commons-colour-profiles-2026-10-09.json"
        ).read_text()
    )["profiles"]
    baseline_by_id = {w["id"]: w for w in baseline["included"]}
    all_seen = [(w, "baseline") for w in baseline_colours]
    prompts = []
    for work in document["profiles"]:
        a = int(work["review_dhash256"], 16)
        for other, origin in all_seen:
            distance = (a ^ int(other["review_dhash256"], 16)).bit_count()
            if distance <= 32:
                prompts.append(
                    dict(
                        candidate=work["id"],
                        other=other["id"],
                        other_origin=origin,
                        distance=distance,
                        other_title=baseline_by_id.get(other["id"], other).get("title"),
                        status=(
                            "manual artwork-identity check required; "
                            "not automatic rejection"
                        ),
                    )
                )
        all_seen.append((work, "candidate"))
    save(OUTPUT / "duplicate-prompts.json", dict(schema=1, prompts=prompts))
    print(
        json.dumps(
            dict(
                profile_fingerprints=len(document["profiles"]),
                review_prompts=len(prompts),
            )
        )
    )


def checkpoint() -> None:
    """Retain a compact tracked receipt; raw pages/JPEGs stay private in build/."""
    review_path = OUTPUT / "review.json"
    review_bytes = review_path.read_bytes()
    review = json.loads(review_bytes)
    previews_path = OUTPUT / "profiles.json"
    preview_bytes = previews_path.read_bytes()
    previews = json.loads(preview_bytes)
    # Discovery/preview files grow between finite passes. Retain the exact
    # hashed metadata snapshot too, not a hash of subsequently replaced bytes.
    for label, payload in (("review", review_bytes), ("profiles", preview_bytes)):
        digest = hashlib.sha256(payload).hexdigest()
        archive = OUTPUT / f"checkpoint-{label}-{digest}.json"
        if archive.exists() and archive.read_bytes() != payload:
            raise ValueError("retained checkpoint bytes changed")
        if not archive.exists():
            archive.write_bytes(payload)
    screened = {
        "records": [
            row
            for path in sorted(OUTPUT.glob("visual-screen-*.json"))
            for row in json.loads(path.read_text())["records"]
        ]
    }
    prompt_path = OUTPUT / "duplicate-prompts.json"
    prompts = json.loads(prompt_path.read_text())
    curated_path = (
        ROOT / "frame_gallery/research/commons-expansion-curation-2026-10-09.json"
    )
    curated = json.loads(curated_path.read_text()) if curated_path.exists() else {}
    accepted_count = len(curated.get("included", []))
    snapshot = dict(
        schema=1,
        recorded_at=datetime.now(UTC).isoformat(),
        status="partial local curation; runtime remains 400; NOT release-approved",
        baseline_count=400,
        target_total=1000,
        accepted_additions=accepted_count,
        local_reviewed_total=400 + accepted_count,
        remaining_additions=600 - accepted_count,
        accepted_receipt_sha256=hashlib.sha256(curated_path.read_bytes()).hexdigest()
        if curated_path.exists()
        else None,
        metadata_checked=len(review["records"]),
        metadata_eligible=sum(not work["reasons"] for work in review["records"]),
        metadata_receipt_sha256=hashlib.sha256(review_bytes).hexdigest(),
        preview_count=len(previews["profiles"]),
        preview_receipt_sha256=hashlib.sha256(preview_bytes).hexdigest(),
        locally_refused=previews["refused"],
        network_deferred=previews.get("network_deferred", []),
        visually_screened_count=len(screened["records"]),
        visual_deferrals=sum(
            row["screen"] == "deferred" for row in screened["records"]
        ),
        visual_screen=screened,
        duplicate_prompts=prompts["prompts"],
        required_next_checks=[
            "remaining visual review and distinct physical artwork identities",
            "source/proportion/provenance and rights-basis decisions",
            f"{600 - accepted_count} additional actual approvals plus complete "
            "source-bound colour profiles",
            "full catalogue/preview/documentation and native release gates",
        ],
        private_cache=(
            "build/commons-1000-research "
            "(retain locally; never distribute artwork bytes)"
        ),
    )
    amendments_path = ROOT / "research/commons-visual-screen-amendments-2026-10-10.json"
    if amendments_path.exists():
        snapshot["visual_screen_chronology_amendments"] = dict(
            file=str(amendments_path.relative_to(ROOT)),
            sha256=hashlib.sha256(amendments_path.read_bytes()).hexdigest(),
            note="Original receipts retained; subsequent actual review and "
            "transcription-order corrections are explicitly recorded separately.",
        )
    for label, filename in (
        (
            "photo_measurement_scopes",
            "commons-photo-measurement-scopes-2026-10-10.json",
        ),
        ("quality_pass_notes", "commons-quality-pass-notes-2026-10-10.json"),
    ):
        path = ROOT / "research" / filename
        if path.exists():
            snapshot[label] = dict(
                file=str(path.relative_to(ROOT)),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                note="Explicit local evidence only; no generic scope exemption "
                "or runtime/release approval.",
            )
    save(ROOT / "research/commons-expansion-checkpoint-2026-10-09.json", snapshot)
    print(
        json.dumps(
            {
                key: snapshot[key]
                for key in (
                    "metadata_checked",
                    "metadata_eligible",
                    "preview_count",
                    "visually_screened_count",
                    "visual_deferrals",
                    "accepted_additions",
                )
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("screen", "fingerprints", "checkpoint"))
    args = parser.parse_args()
    if args.mode == "screen":
        screen()
    elif args.mode == "fingerprints":
        fingerprints()
    else:
        checkpoint()
