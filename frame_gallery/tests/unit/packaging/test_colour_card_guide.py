"""The complete native colour card and documented helper key stay usable."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from scripts.app_config import schema

from frame_gallery.config.filters import FilterField
from frame_gallery.config.vocabulary import BUILTIN_VOCABULARY


@pytest.mark.parametrize("language", ["en", "de"])
def test_colour_guide_matches_complete_native_example(language: str) -> None:
    root = Path(__file__).resolve().parents[3]
    suffix = ".de" if language == "de" else ""
    guide_name = f"COMMONS_COLOUR{suffix}.md"
    guide = (root / guide_name).read_text()
    assert f"!{guide_name}" in (root / ".dockerignore").read_text().splitlines()
    blocks = re.findall(r"```yaml\n(.*?)\n```", guide, re.DOTALL)
    assert len(blocks) == 1
    example = (root / f"examples/commons-colour-card{suffix}.yaml").read_text()
    assert blocks[0] + "\n" == example
    assert example.startswith("type: vertical-stack\ncards:\n")
    assert "\t" not in example
    assert "type: entities" in example
    assert "entity: input_select.frame_gallery_colour" in example
    label = "Farbwunsch (nur Commons)" if language == "de" else "Colour wish (Commons only)"
    assert f"name: {label}" in example
    basic_guide = (root / "DOCS.md").read_text()
    basic = re.findall(r"```yaml\n(.*?)\n```", basic_guide, re.DOTALL)[1]
    native_image_and_loading = basic[basic.index("  - type: picture-entity") :]
    translated = native_image_and_loading
    if language == "de":
        translated = translated.replace("Load new artwork", "Neues Kunstwerk laden")
        translated = translated.replace("Updating artwork…", "Kunstwerk wird geladen …")
    assert example.endswith(translated + "\n")
    assert "`color_helper`" in guide
    assert "color_helper" in schema()
    assert "color_entity" not in guide


@pytest.mark.parametrize("language", ["en", "de"])
def test_documented_dropdown_offers_every_runtime_colour_and_no_multicolour_value(
    language: str,
) -> None:
    root = Path(__file__).resolve().parents[3]
    suffix = ".de" if language == "de" else ""
    guide = (root / f"COMMONS_COLOUR{suffix}.md").read_text()
    options = ["any"] + [e.label for e in BUILTIN_VOCABULARY.entries_for(FilterField.COLOR)]
    assert len(options) == 13
    for option in options:
        assert f"`{option}`" in guide
    if language == "de":
        assert "nicht** von selbst einen Lauf" in guide
        assert "Mehrere Farben gleichzeitig" in guide
    else:
        assert "not** automatically start a run" in guide
        assert "Selecting multiple colours at once is not offered" in guide


def test_colour_guides_have_reciprocal_language_links_and_identical_card_wiring() -> None:
    root = Path(__file__).resolve().parents[3]
    english = (root / "COMMONS_COLOUR.md").read_text()
    german = (root / "COMMONS_COLOUR.de.md").read_text()
    assert "**English** | [Deutsch](COMMONS_COLOUR.de.md)" in english
    assert "[English](COMMONS_COLOUR.md) | **Deutsch**" in german
    assert "does not automatically switch" in english
    assert "nicht automatisch" in german
    de_example = (root / "examples/commons-colour-card.de.yaml").read_text()
    en_example = (root / "examples/commons-colour-card.yaml").read_text()
    translated = de_example.replace("Farbwunsch (nur Commons)", "Colour wish (Commons only)")
    translated = translated.replace("Neues Kunstwerk laden", "Load new artwork")
    translated = translated.replace("Kunstwerk wird geladen …", "Updating artwork…")
    assert translated == en_example
