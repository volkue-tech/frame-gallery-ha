"""Explicit human-inspected first-batch choices, never threshold auto-selection.

The IDs were selected after viewing curator sheets 000--015 on 2026-10-09.
Any subsequent source, identity, preview or dossier flag blocks that choice.
Research acceptance is not release approval or worldwide legal clearance.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from research_tools.commons_colours import BASELINE, ROOT, save
from research_tools.commons_expand import OUTPUT

CHOICES = frozenset(
    map(
        int,
        """
25893538 38150775 74888952 90858339 23040475 30479115 74726012 103694347
141525210 142200844 178217854 4691628 25027786 107060939 41466351 149931955
29010353 114877885 36652938 70846784 91957917 123067744 123898742 37709189
59040202 142204289 200090400 18774412 55955732 95306820 9934723 76000401
76000748 156850328 156830081 76001995 146030403 76613575 128612500 12664633
156882066 186729481 45453768 54950059 23599371 13319862 62025574 76614673
20005027 74648716 50573805 142071813 150940461 13405478 24986087 49057437
50308787 81326189 81333248 138667986 20518159 41235033 81306373 94091272
18430183 64497875 18936216 26598752 165878149 18935587 34547170 101181437
137142542 182084252 13105985 13126969 63564407 129802206 132763643 156348
74572653 22133858 31244975 76095011 176607326 141402648 87955357 156815878
76621395 29941270 56771126 156839088 77838547 56397303 13405265 29850754
62034144 189362292 16052872 74648512 22134074 66383635 95306977 101145460
182610819 13460862 138016733 156862749 164289029 126454720 71001518 21963257
32079692 22026123 146096944
27683876 99178355 91718208 147696850 22132098 55808460 21865440 16728284
21998429 29696188 56890167 21865553 55820104 21976346
""".split(),
    )
)


def curate() -> None:
    baseline = json.loads(BASELINE.read_text())["included"]
    checked = set()
    for path in OUTPUT.glob("baseline-identity-*.json"):
        for page in json.loads(path.read_text()).get("query", {}).get("pages", []):
            checked.add(page["pageid"])
    if checked != {w["id"] for w in baseline}:
        raise ValueError("complete baseline artwork-identity receipts required")
    rows = json.loads((OUTPUT / "curator-dossiers.json").read_text())["records"]
    by_id = {row["id"]: row for row in rows}
    metadata = {
        w["id"]: w for w in json.loads((OUTPUT / "review.json").read_text())["records"]
    }
    accepted, deferred = [], []
    for work_id in sorted(CHOICES):
        row = by_id[work_id]
        if row["flags"]:
            deferred.append(dict(id=work_id, reasons=row["flags"]))
            continue
        path = OUTPUT / f"{work_id}.jpg"
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["thumbnail_sha256"]:
            raise ValueError("curated thumbnail changed")
        evidence = OUTPUT / row["evidence_file"]
        if hashlib.sha256(evidence.read_bytes()).hexdigest() != row["evidence_sha256"]:
            raise ValueError("curated source receipt changed")
        # Match the second-view receipt by ID, not the order after new flags.
        receipt = next(
            (p, r)
            for p in sorted(OUTPUT.glob("curator-sheet-*.json"))
            for r in json.loads(p.read_text())["records"]
            if r["id"] == work_id
        )
        sheet_path = receipt[0].with_suffix(".jpg")
        sheet_hash = json.loads(receipt[0].read_text())["sha256"]
        if hashlib.sha256(sheet_path.read_bytes()).hexdigest() != sheet_hash:
            raise ValueError("actually inspected second-view sheet changed")
        work = metadata[work_id]
        accepted.append(
            dict(
                id=work_id,
                file_title=work["file_title"],
                sha1=work["sha1"],
                title=work["title"],
                artist=work["artist"],
                width=work["width"],
                height=work["height"],
                source=work["source"],
                source_revision=row["source_revision"],
                source_page_sha256=row["source_page_sha256"],
                rights_label_observed=row["rights_label"],
                rights_basis=row["rights_basis"],
                artwork_qids=row["artwork_qids"],
                physical_measures=row["physical_measures"],
                thumbnail_sha256=row["thumbnail_sha256"],
                evidence_sha256=row["evidence_sha256"],
                second_visual_sheet_sha256=sheet_hash,
                decision="accepted local research; not release-approved",
                reason="Complete unframed reproduction visually inspected twice; "
                "source/pin/rights declarations and proportions checked; "
                "no unresolved artwork-identity flag; selected for gallery variety.",
                physical_evidence="source dimensions agree within 2.5%"
                if row["physical_measures"]
                else "source has no explicit dimensions; full reproduction "
                "visually checked, no quantitative physical-ratio claim",
            )
        )
    target = ROOT / "frame_gallery/research/commons-expansion-curation-2026-10-09.json"
    save(
        target,
        dict(
            schema=1,
            updated_at=datetime.now(UTC).isoformat(),
            status="partial local research milestone, NOT a 1000-work catalogue",
            baseline_sha256=hashlib.sha256(BASELINE.read_bytes()).hexdigest(),
            baseline_count=400,
            target_total=1000,
            added_count=len(accepted),
            local_reviewed_total=400 + len(accepted),
            criteria=dict(minimum_source_width_px=3000, relative_16_9_tolerance=0.025),
            rights_scope="Recorded Commons PD/CC0 declarations are not worldwide "
            "legal clearance or the qualified release license review.",
            included=accepted,
            selected_but_deferred=deferred,
        ),
    )
    print(json.dumps(dict(accepted=len(accepted), deferred=len(deferred))))


if __name__ == "__main__":
    curate()
