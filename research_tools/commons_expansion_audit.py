"""Offline research consistency audit, not runtime admission or rights clearance."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from research_tools.commons_colours import BASELINE, METHOD, ROOT, aggregate, save
from research_tools.commons_curation import catalogue_counts


def verify_profile(profile: dict, work: dict, new: bool) -> None:
    if profile["id"] != work["id"] or profile["original_sha1"] != work["sha1"]:
        raise ValueError("profile identity or original upload pin changed")
    if profile["method"] != METHOD:
        raise ValueError("colour method changed")
    if len(profile["palette"]) > 128:
        raise ValueError("palette exceeds retained bound")
    expected = aggregate([(p["pixels"], tuple(p["rgb"])) for p in profile["palette"]])
    for key, value in expected.items():
        if profile[key] != value:
            raise ValueError(f"colour evidence mismatch: {key}")
    if new:
        for key in ("source_revision", "source_page_sha256", "thumbnail_sha256"):
            if profile[key] != work[key]:
                raise ValueError(f"source evidence mismatch: {key}")


def audit() -> dict:
    paths = {
        "baseline": BASELINE,
        "baseline_colours": ROOT
        / "frame_gallery/research/commons-colour-profiles-2026-10-09.json",
        "curation": ROOT
        / "frame_gallery/research/commons-expansion-curation-2026-10-09.json",
        "new_colours": ROOT
        / "frame_gallery/research/commons-expansion-colours-2026-10-09.json",
        "baseline_audit": ROOT
        / "research/commons-baseline-format-audit-2026-10-09.json",
    }
    hashes = {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()}
    documents = {k: json.loads(p.read_text()) for k, p in paths.items()}
    old = documents["baseline"]["included"]
    added = documents["curation"]["included"]
    if (
        documents["curation"]["baseline_sha256"] != hashes["baseline"]
        or documents["baseline_audit"]["baseline_sha256"] != hashes["baseline"]
        or documents["new_colours"]["curation_sha256"] != hashes["curation"]
    ):
        raise ValueError("manifest evidence changed")
    all_works = old + added
    if len({w["id"] for w in all_works}) != len(all_works):
        raise ValueError("duplicate catalogue ID")
    pins = [w.get("sha1", w.get("original_sha1")) for w in all_works]
    if any(not p for p in pins) or len(set(pins)) != len(pins):
        raise ValueError("duplicate or missing original upload pin")
    blue_additions = 0
    for works, colours, new in (
        (old, documents["baseline_colours"]["profiles"], False),
        (added, documents["new_colours"]["profiles"], True),
    ):
        by_id = {p["id"]: p for p in colours}
        if len(by_id) != len(colours) or set(by_id) != {w["id"] for w in works}:
            raise ValueError("missing or extra colour profile")
        for work in works:
            if new and (
                work["width"] < 3000
                or abs(work["width"] / work["height"] / (16 / 9) - 1) > 0.025
            ):
                raise ValueError("new-work original dimension gate failed")
            verify_profile(by_id[work["id"]], work, new)
            if new and "blue" in by_id[work["id"]]["search_colours"]:
                blue_additions += 1
    result = dict(
        schema=1,
        recorded_at=datetime.now(UTC).isoformat(),
        status="offline research consistency only; "
        "no runtime freeze or release approval",
        input_sha256=hashes,
        baseline_count=len(old),
        accepted_additions=len(added),
        profiles_verified=len(all_works),
        blue_additions=blue_additions,
        unique_ids_and_upload_pins=True,
        complete_palette_and_distribution_recomputed=True,
        source_evidence_matches=True,
        **catalogue_counts(
            len(old),
            len(added),
            documents["baseline_audit"]["unresolved_measurement_prompts"],
        ),
    )
    save(ROOT / "research/commons-expansion-colour-audit-2026-10-10.json", result)
    return result


if __name__ == "__main__":
    print(json.dumps(audit()))
