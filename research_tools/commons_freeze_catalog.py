"""Freeze the human-approved local 1000-work selection; no live mutations.

The historical 400-work manifest and all research stay intact. Seven actually
viewed, accepted additions remain a curatorial reserve, not a rights rejection.
Only the compact catalogue and search labels enter the runtime package.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from research_tools.commons_colours import BASELINE, ROOT, save
from research_tools.commons_expansion_audit import verify_profile

APPROVAL = ROOT / "research/commons-baseline-hold-approval-2026-10-10.json"
PROPOSAL = ROOT / "research/commons-baseline-held-proposal-2026-10-10.json"
CURATION = ROOT / "frame_gallery/research/commons-expansion-curation-2026-10-09.json"
BASELINE_COLOURS = ROOT / "frame_gallery/research/commons-colour-profiles-2026-10-09.json"
NEW_COLOURS = ROOT / "frame_gallery/research/commons-expansion-colours-2026-10-09.json"
SELECTION = ROOT / "frame_gallery/research/commons-1000-selection-2026-10-10.json"
COLOURS = ROOT / "frame_gallery/research/commons-1000-colours-2026-10-10.json"
DESTINATION = ROOT / "frame_gallery/src/frame_gallery/providers/commons_catalog.py"
RESERVE_IDS = frozenset({90790746, 91211830, 79631807, 88955007, 71912666, 91219459, 65254132})


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select(
    baseline: dict,
    curation: dict,
    proposal: dict,
    approval: dict,
    old_colours: dict,
    new_colours: dict,
    hashes: dict[str, str],
) -> tuple[dict, dict]:
    """Pure fail-closed selection, also exercised with synthetic test records."""
    if (
        approval["answer"] != "Ja, vorläufig zurückstellen und ersetzen"
        or approval["proposal_sha256"] != hashes["proposal"]
        or approval["baseline_sha256"] != hashes["baseline"]
        or proposal["baseline_sha256"] != hashes["baseline"]
        or curation["baseline_sha256"] != hashes["baseline"]
        or new_colours["curation_sha256"] != hashes["curation"]
    ):
        raise ValueError("approval or source manifest pin changed")
    old = baseline["included"]
    added = curation["included"]
    held = {r["id"]: r["sha1"] for r in approval["held_pins"]}
    proposed = {r["id"]: r["retained_catalogue_entry"]["sha1"] for r in proposal["records"]}
    if (
        len(old) != 400
        or len(added) != 663
        or len(held) != 56
        or len(approval["held_pins"]) != 56
        or len(proposal["records"]) != 56
        or held != proposed
    ):
        raise ValueError("approved 400/663/56 scope changed")
    old_by_id = {w["id"]: w for w in old}
    new_by_id = {w["id"]: w for w in added}
    if any(i not in old_by_id or old_by_id[i]["sha1"] != pin for i, pin in held.items()):
        raise ValueError("held identity or upload pin changed")
    if not RESERVE_IDS <= new_by_id.keys():
        raise ValueError("actually reviewed reserve missing")
    all_works = old + added
    if (
        len({w["id"] for w in all_works}) != 1063
        or len({w["sha1"] for w in all_works}) != 1063
        or len({(w["title"].casefold(), w["artist"].casefold()) for w in all_works}) != 1063
    ):
        raise ValueError("duplicate identity, upload or title/artist")
    profiles = {}
    for works, document, is_new in (
        (old, old_colours, False),
        (added, new_colours, True),
    ):
        by_id = {p["id"]: p for p in document["profiles"]}
        if (
            len(by_id) != len(works)
            or len(document["profiles"]) != len(works)
            or set(by_id) != {w["id"] for w in works}
        ):
            raise ValueError("missing, extra or duplicate colour profile")
        for work in works:
            if (
                work["width"] < 3000
                or abs(work["width"] * 9 - work["height"] * 16) * 40 > work["height"] * 16
                or work["rights_label_observed"] not in {"Public domain", "CC0"}
            ):
                raise ValueError("source width, ratio or rights gate failed")
            verify_profile(by_id[work["id"]], work, is_new)
        profiles.update(by_id)
    included = [w for w in old if w["id"] not in held] + [
        w for w in added if w["id"] not in RESERVE_IDS
    ]
    if len(included) != 1000:
        raise ValueError("active selection must contain exactly 1000")
    selection = dict(
        schema=1,
        research_date="2026-10-10",
        status="local update candidate; not published or installed",
        decision="D-215",
        input_sha256=hashes,
        criteria=baseline["criteria"],
        included_count=1000,
        retained_active_baseline_count=344,
        added_count=656,
        held_count=56,
        reserve_count=7,
        history_policy="Permanent commons:{page_id} identities and upload pins "
        "unchanged; no ledger migration, reset or deletion.",
        held_ids=list(held),
        reserve_reason="Accepted and actually viewed additions, lower curatorial "
        "priority/repetitive coastal detail; retained for later selection. "
        "Not a rights or technical rejection.",
        reserve=[w for w in added if w["id"] in RESERVE_IDS],
        included=included,
    )
    colours = dict(
        schema=1,
        status="full local profiles for the 1000-work update candidate",
        count=1000,
        profiles=[profiles[w["id"]] for w in included],
    )
    return selection, colours


def render_catalog(selection: dict) -> str:
    header = '''"""Generated 1000-work Commons catalogue (D-215), no image bytes.

344 active baseline pins plus 656 additions; 56 held pins and seven reserves
remain in research. Permanent commons:{page_id} history IDs are unchanged.
Provenance: research/commons-1000-selection-2026-10-10.json.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class CuratedWork:
    page_id: int
    file_title: str
    sha1: str
    title: str
    artist: str


CATALOG: Final = (
'''
    rows = []
    for w in selection["included"]:
        values = (w["id"], w["file_title"], w["sha1"], w["title"], w["artist"])
        rendered = []
        for value in values:
            if not isinstance(value, str) or len(ascii(value)) <= 76:
                rendered.append("        " + ascii(value) + ",")
                continue
            chunks, current = [], ""
            for char in value:
                if len(ascii(current + char)) > 76:
                    chunks.append(current)
                    current = ""
                current += char
            chunks.append(current)
            rendered.append(
                "        (\n"
                + "\n".join("            " + ascii(chunk) for chunk in chunks)
                + "\n        ),"
            )
        rows.append("    CuratedWork(\n" + "\n".join(rendered) + "\n    ),")
    return header + "\n".join(rows) + "\n)\n"


def inputs() -> tuple[dict, dict]:
    paths = dict(
        baseline=BASELINE,
        curation=CURATION,
        proposal=PROPOSAL,
        approval=APPROVAL,
        old_colours=BASELINE_COLOURS,
        new_colours=NEW_COLOURS,
    )
    documents = {k: json.loads(p.read_text()) for k, p in paths.items()}
    return select(**documents, hashes={k: sha256(p) for k, p in paths.items()})


def freeze() -> None:
    selection, colours = inputs()
    save(SELECTION, selection)
    colours["selection_sha256"] = sha256(SELECTION)
    save(COLOURS, colours)
    DESTINATION.write_text(render_catalog(selection))
    print(json.dumps(dict(active=1000, held=56, reserve=7, retained=1063)))


def audit() -> dict:
    """Compare retained inputs, full profiles and actual compact runtime data."""
    from collections import Counter

    from frame_gallery.providers.commons_catalog import CATALOG
    from frame_gallery.providers.commons_colours import COLOUR_PROFILES

    expected, colours = inputs()
    actual = json.loads(SELECTION.read_text())
    colours["selection_sha256"] = sha256(SELECTION)
    if actual != expected or json.loads(COLOURS.read_text()) != colours:
        raise ValueError("frozen manifest/full profiles no longer match evidence")
    if [(w.page_id, w.file_title, w.sha1, w.title, w.artist) for w in CATALOG] != [
        (w["id"], w["file_title"], w["sha1"], w["title"], w["artist"]) for w in actual["included"]
    ]:
        raise ValueError("actual runtime catalogue differs from frozen selection")
    if dict(COLOUR_PROFILES) != {
        p["id"]: (p["original_sha1"], frozenset("color_" + c for c in p["search_colours"]))
        for p in colours["profiles"]
    }:
        raise ValueError("actual compact colour labels differ from full profiles")
    report = dict(
        schema=1,
        recorded_on="2026-10-10",
        scope="Offline local freeze/runtime consistency; no native or live test",
        active=1000,
        held=56,
        reserve=7,
        retained_research=1063,
        input_sha256=actual["input_sha256"],
        selection_sha256=sha256(SELECTION),
        full_colours_sha256=sha256(COLOURS),
        runtime_catalogue_sha256=sha256(DESTINATION),
        runtime_colour_data_sha256=sha256(
            ROOT / "frame_gallery/src/frame_gallery/providers/commons_colour_data.py"
        ),
        unchanged_ids_pins_and_full_profile_evidence=True,
        actual_runtime_matches=True,
        artist_label_count=len({w.artist for w in CATALOG}),
        colour_matches=dict(Counter(c for p in colours["profiles"] for c in p["search_colours"])),
        rights_labels=dict(Counter(w["rights_label_observed"] for w in actual["included"])),
    )
    save(ROOT / "research/commons-1000-freeze-audit-2026-10-10.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true")
    if parser.parse_args().audit:
        print(json.dumps(audit()))
    else:
        freeze()
