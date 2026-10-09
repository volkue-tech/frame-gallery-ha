"""Offline physical-format prompts for the unchanged 400-work baseline.

These are measurement-scope prompts, not automatic crop determinations or
catalogue removals. Read only retained, source-pinned Commons receipts.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from research_tools.commons_colours import BASELINE, ROOT, save
from research_tools.commons_dossiers import physical
from research_tools.commons_expand import OUTPUT


def verify_decision(record: dict, decision: dict, thumbnail_sha256: str) -> dict:
    """Apply only a source/preview-bound manual review, never a ratio heuristic."""
    if (
        any(
            record[key] != decision.get(key)
            for key in (
                "id",
                "original_sha1",
                "source_revision",
                "source_markup_sha256",
            )
        )
        or decision.get("thumbnail_sha256") != thumbnail_sha256
    ):
        raise ValueError("manual baseline scope review no longer matches evidence")
    if (
        decision.get("decision")
        != "measurement scope resolved after actual preview and source review"
        or not isinstance(decision.get("reason"), str)
        or not decision["reason"].strip()
        or not isinstance(decision.get("limits"), str)
        or not decision["limits"].strip()
    ):
        raise ValueError("explicit bounded manual scope decision required")
    return decision


def audit() -> None:
    baseline = {row["id"]: row for row in json.loads(BASELINE.read_text())["included"]}
    pages = {}
    files = list((ROOT / "build/commons-colours").glob("metadata-*.json"))
    files.extend(OUTPUT.glob("baseline-identity-*.json"))
    for file in files:
        receipt = file.read_bytes()
        for page in json.loads(receipt).get("query", {}).get("pages", []):
            if page.get("pageid") in baseline and page.get("revisions"):
                pages[page["pageid"]] = (
                    page,
                    file,
                    hashlib.sha256(receipt).hexdigest(),
                )
    if set(pages) != set(baseline):
        raise ValueError("all 400 baseline source revisions are required")
    decisions_path = ROOT / "research/commons-baseline-format-decisions-2026-10-10.json"
    decisions = (
        json.loads(decisions_path.read_text())["records"]
        if decisions_path.exists()
        else []
    )
    by_id = {d["id"]: d for d in decisions}
    if len(by_id) != len(decisions) or not set(by_id).issubset(baseline):
        raise ValueError("manual baseline reviews must have unique baseline IDs")
    records = []
    for work_id, work in baseline.items():
        page, file, receipt_hash = pages[work_id]
        info = page["imageinfo"][0]
        if info["sha1"] != work["sha1"] or page["title"] != work["file_title"]:
            raise ValueError("baseline source pin changed")
        revision = page["revisions"][0]
        text = revision["slots"]["main"]["content"]
        measures = physical(text)
        prompts = (
            ["measurement scope outside original near-16:9 band; review required"]
            if any(abs(m["ratio"] / (16 / 9) - 1) > 0.025 for m in measures)
            else []
        )
        records.append(
            dict(
                id=work_id,
                title=work["title"],
                artist=work["artist"],
                original_sha1=work["sha1"],
                source_revision=revision["revid"],
                source_receipt=str(file.relative_to(ROOT)),
                source_receipt_sha256=receipt_hash,
                source_markup_sha256=hashlib.sha256(text.encode()).hexdigest(),
                physical_measurements=measures,
                review_prompts=prompts,
                status="unresolved source-measurement prompt"
                if prompts
                else "no automatic measurement prompt; not a fresh visual approval",
            )
        )
        if work_id in by_id:
            if not prompts:
                raise ValueError("saved baseline scope prompt unexpectedly changed")
            preview = ROOT / "build/commons-colours" / f"{work_id}.jpg"
            records[-1]["manual_resolution"] = verify_decision(
                records[-1],
                by_id[work_id],
                hashlib.sha256(preview.read_bytes()).hexdigest(),
            )
            records[-1]["status"] = "manual measurement-scope review resolved"
    report = dict(
        schema=1,
        recorded_at=datetime.now(UTC).isoformat(),
        status="offline source audit only; baseline/catalogue/history unchanged",
        baseline_sha256=hashlib.sha256(BASELINE.read_bytes()).hexdigest(),
        source_revisions_checked=len(records),
        with_physical_measurements=sum(
            bool(r["physical_measurements"]) for r in records
        ),
        automatic_measurement_prompts=sum(bool(r["review_prompts"]) for r in records),
        resolved_measurement_prompts=sum(
            bool(r.get("manual_resolution")) for r in records
        ),
        unresolved_measurement_prompts=sum(
            bool(r["review_prompts"]) and not r.get("manual_resolution")
            for r in records
        ),
        records=records,
    )
    save(ROOT / "research/commons-baseline-format-audit-2026-10-09.json", report)
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "source_revisions_checked",
                    "with_physical_measurements",
                    "unresolved_measurement_prompts",
                )
            }
        )
    )


if __name__ == "__main__":
    audit()
