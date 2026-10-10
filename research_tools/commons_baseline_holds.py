"""Retain unresolved legacy pins separately from the usable-count proposal.

Offline only. The explicit 2026-10-10 review read the source headers/rights for
all 56 unresolved prompts and actually viewed their baseline review sheets.
This receipt does not establish cropping, remove a runtime entry, or resolve
the prompts. It prevents a nominal count from being called a vetted count.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from research_tools.commons_baseline_audit import verify_render_evidence
from research_tools.commons_colours import BASELINE, ROOT, save

INSPECTED_AUDIT_SHA256 = (
    "4fb27f67bd07691c8be6823b69334b203a8b749300520cce41ea36fb4a5f67f2"
)


def holds() -> None:
    path = ROOT / "research/commons-baseline-format-audit-2026-10-09.json"
    audit_bytes = path.read_bytes()
    if hashlib.sha256(audit_bytes).hexdigest() != INSPECTED_AUDIT_SHA256:
        raise ValueError("explicitly read/viewed baseline audit bytes changed")
    audit = json.loads(audit_bytes)
    baseline_bytes = BASELINE.read_bytes()
    if hashlib.sha256(baseline_bytes).hexdigest() != audit["baseline_sha256"]:
        raise ValueError("baseline audit pin changed")
    baseline = {r["id"]: r for r in json.loads(baseline_bytes)["included"]}
    profiles = {
        r["id"]: r
        for r in json.loads(
            (
                ROOT / "frame_gallery/research/commons-colour-profiles-2026-10-09.json"
            ).read_text()
        )["profiles"]
    }
    rows = []
    for row in audit["records"]:
        if not row["review_prompts"] or row.get("manual_resolution"):
            continue
        receipt = (ROOT / row["source_receipt"]).read_bytes()
        if hashlib.sha256(receipt).hexdigest() != row["source_receipt_sha256"]:
            raise ValueError("actually read baseline source receipt changed")
        page = next(
            p for p in json.loads(receipt)["query"]["pages"] if p["pageid"] == row["id"]
        )
        markup = page["revisions"][0]["slots"]["main"]["content"]
        if hashlib.sha256(markup.encode()).hexdigest() != row["source_markup_sha256"]:
            raise ValueError("actually read baseline source markup changed")
        preview = ROOT / "build/commons-colours" / f"{row['id']}.jpg"
        thumbnail_hash = hashlib.sha256(preview.read_bytes()).hexdigest()
        verify_render_evidence(row, profiles[row["id"]], thumbnail_hash)
        rows.append(
            dict(
                **row,
                retained_catalogue_entry=baseline[row["id"]],
                thumbnail_sha256=thumbnail_hash,
                curator_review="Source headers and rights read; preview actually "
                "viewed. No further explicit frame-only or numerical-boundary "
                "resolution was established in this pass.",
                selection_proposal="Retain identity, upload pin and history; do "
                "not count this unresolved case towards 1000 vetted usable "
                "works. Collect an additional reserve instead.",
                limits="Measurement-scope disagreement is not proof of cropping. "
                "No runtime catalogue removal, repinning, release or HA mutation.",
            )
        )
    if len(rows) != 56 or len(baseline) != 400:
        raise ValueError("explicitly reviewed 400/56 baseline scope changed")
    save(
        ROOT / "research/commons-baseline-held-proposal-2026-10-10.json",
        dict(
            schema=1,
            recorded_at=datetime.now(UTC).isoformat(),
            status="Local selection proposal only; runtime unchanged",
            baseline_sha256=hashlib.sha256(baseline_bytes).hexdigest(),
            audit_sha256=hashlib.sha256(audit_bytes).hexdigest(),
            retained_baseline_count=400,
            unresolved_held_count=len(rows),
            baseline_without_unresolved_measurement_prompt=400 - len(rows),
            additional_acceptances_needed_for_1000=600 + len(rows),
            records=rows,
        ),
    )
    print(json.dumps(dict(retained=400, held=56, additions_needed=656)))


if __name__ == "__main__":
    holds()
