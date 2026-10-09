"""Generate small runtime search labels, never thumbnails or full palettes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frame_gallery/research/commons-colour-profiles-2026-10-09.json"
DESTINATION = ROOT / "frame_gallery/src/frame_gallery/providers/commons_colour_data.py"


def render() -> str:
    document = json.loads(SOURCE.read_text())
    rows = []
    for profile in sorted(document["profiles"], key=lambda p: p["id"]):
        keys = tuple("color_" + value for value in profile["search_colours"])
        rows.append(f"    ({profile['id']}, {profile['original_sha1']!r}, {keys!r}),")
    return (
        '"""Generated offline colour search metadata (D-213), not artwork bytes.\n'
        f"Research SHA256: {hashlib.sha256(SOURCE.read_bytes()).hexdigest()}\n"
        'Full palettes/provenance are retained separately under research/."""\n\n'
        "from typing import Final\n\n"
        "COLOUR_DATA: Final[tuple[tuple[int, str, tuple[str, ...]], ...]] = (\n"
        + "\n".join(rows)
        + "\n)\n"
    )


if __name__ == "__main__":
    DESTINATION.write_text(render())
