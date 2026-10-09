"""Explicit human-inspected first-batch choices, never threshold auto-selection.

The IDs were selected after viewing curator sheets 000--054 on 2026-10-09.
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
21995421 34888005 4848754 148676 41234621 55820097 21983403 22147995
22148178 21897870 22008005 21855719 23611297 22728217 68866805 49345095
79077030 36187271 81434665 141891714 23600099 165009791 38794836
29859009 6932372 141501630 11583593 185085338
26210769 101180635 91185050 68712674 29934901
141503301 148659 69367477 69367478 149994747 166265763 83775989
20836951 84917041 21116675 76297104 132599475 11376427 67636094
117494345 9694102 22248528 56283143 83593797 176662289 132704252
186311052 21932258 189613984
29453631 173720589 23227439 44806961 44024109 111622914 74546579
129942739 111139063 165339992 109122728 26568074 29673142 69311040
65375635 75381504 93097969 31650532 41875599 53280155 49893685
124646299 129480759 21853937 83529716 40205542 23821678 40711058
50627665 92833209 48303061 164574133 68196720 92574811 132538902
45254415 106289300 21170222 113174036 12793786 198656654 49345017
121412517 74389708 164274040 5544940 194918345 54586369 164671265
22600904 137145458 54586370 140216454 140217862 69774630
123170828 140070044 142202947 141534000 13318212 15288395
41474968 9926665 34313785 34258055 34249146 118243083 168384466
21963767 15676619 84757026 84115175 22232441
98814213 29511761 73882502 98809146 128723452 156929787 99878772
73882636 73882433 86019471 4592534 133949802 3225070 119221337
126722150 15957034 18936207 116206004 128989871 124915272 163318479
181134110 48450222 166459292 47139064 18936330 72990653 136178267
98034987 74019822 7745117 22205024 47726567 143435922 145194329
66372744 171251262 163968044 139276550 66676306 7478744 119119721
48986314 10345644 83746514 164564105 124521020 84250403 86152402
130697950 16084852 38363034 18652908 117288307 14945368 26043772
86008698 13301088 158919042 15208000 79066095 22162546 93597976
36322343 61316880 67621780 113436658 113760526 31548457 127759558
17132228 31888585 21170851 169640367 86490366 18426650 48775571
42838057 73329015 185920882 125972883
689813 48330814 77050821 29859368 50442208 187965047 128432667
140224565 67537617 52873819 67541234 127069165 163968085 95831369
131734965 160495779 21931368 194996256 74877410
257770 48450338 21938680 128007967 167374053 164564883
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
