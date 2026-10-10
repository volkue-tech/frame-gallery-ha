"""The unreleased guide's complete native card and helper values stay usable."""

from __future__ import annotations

import re
from pathlib import Path

from frame_gallery.config.filters import FilterField
from frame_gallery.config.vocabulary import BUILTIN_VOCABULARY


def test_draft_colour_card_matches_complete_native_example() -> None:
    root = Path(__file__).resolve().parents[4]
    guide = (root / "docs/plans/commons-colour-user-guide-draft.md").read_text()
    blocks = re.findall(r"```yaml\n(.*?)\n```", guide, re.DOTALL)
    assert len(blocks) == 1
    example = (root / "frame_gallery/examples/commons-colour-card.yaml").read_text()
    assert blocks[0] + "\n" == example
    assert example.startswith("type: vertical-stack\ncards:\n")
    assert "\t" not in example
    assert "type: entities" in example
    assert "entity: input_select.frame_gallery_colour" in example
    assert "name: Farbwunsch (nur Commons)" in example
    basic_guide = (root / "frame_gallery/DOCS.md").read_text()
    basic = re.findall(r"```yaml\n(.*?)\n```", basic_guide, re.DOTALL)[1]
    native_image_and_loading = basic[basic.index("  - type: picture-entity") :]
    translated = native_image_and_loading.replace("Load new artwork", "Neues Kunstwerk laden")
    translated = translated.replace("Updating artwork…", "Kunstwerk wird geladen …")
    assert example.endswith(translated + "\n")
    assert "color_entity" in guide
    assert "Noch nicht veröffentlicht" in guide


def test_documented_dropdown_offers_every_runtime_colour_and_no_multicolour_value() -> None:
    root = Path(__file__).resolve().parents[4]
    guide = (root / "docs/plans/commons-colour-user-guide-draft.md").read_text()
    options = ["any"] + [e.label for e in BUILTIN_VOCABULARY.entries_for(FilterField.COLOR)]
    assert len(options) == 13
    for option in options:
        assert f"`{option}`" in guide
    assert "nicht** von selbst einen Lauf" in guide
    assert "Mehrere Farben gleichzeitig" in guide
