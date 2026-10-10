"""Five-language artist guides preserve complete native card wiring and names."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Final

import pytest
from scripts.app_config import translations

from frame_gallery.config.filters import FilterField
from frame_gallery.config.vocabulary import BUILTIN_VOCABULARY, LookupStatus, artist_key
from frame_gallery.providers.commons_catalog import CATALOG
from tests.unit.packaging.test_colour_card_guide import LABELS, _english_labels, _suffix

ARTIST_LABELS: Final = {
    "en": "Artist (Commons only)",
    "de": "Künstler (nur Commons)",
    "fr": "Artiste (Commons uniquement)",
    "es": "Artista (solo Commons)",
    "it": "Artista (solo Commons)",
}
NAMES: Final = {
    "en": "English",
    "de": "Deutsch",
    "fr": "Français",
    "es": "Español",
    "it": "Italiano",
}
ROOT: Final = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("language", list(LABELS))
def test_artist_guides_keep_both_complete_native_cards_and_all_language_links(
    language: str,
) -> None:
    suffix = _suffix(language)
    name = f"COMMONS_ARTIST{suffix}.md"
    guide = (ROOT / name).read_text()
    assert f"!{name}" in (ROOT / ".dockerignore").read_text().splitlines()
    blocks = re.findall(r"```yaml\n(.*?)\n```", guide, re.DOTALL)
    assert len(blocks) == 2
    for block, mode in zip(blocks, ("only-card", "card"), strict=True):
        example = (ROOT / f"examples/commons-artist-{mode}{suffix}.yaml").read_text()
        assert block + "\n" == example
        canonical = (ROOT / f"examples/commons-artist-{mode}.yaml").read_text()
        english = _english_labels(example, language).replace(
            ARTIST_LABELS[language], ARTIST_LABELS["en"]
        )
        assert english == canonical
        assert "custom:" not in example
        assert "entity: input_select.frame_gallery_artist" in example
        assert "entity: camera.frame_gallery_preview" in example
        assert "entity: timer.frame_gallery_run" in example
        assert "entity_id: script.frame_gallery_new_artwork" in example
        assert (
            "input_select.frame_gallery_colour" in example
            if mode == "card"
            else ("input_select.frame_gallery_colour" not in example)
        )
    for other, label in NAMES.items():
        if other == language:
            assert f"**{label}**" in guide
        else:
            assert f"[{label}](COMMONS_ARTIST{_suffix(other)}.md)" in guide
    fields = translations(language)["configuration"]
    assert isinstance(fields, dict)
    for field in ("artist", "artist_helper"):
        value = fields[field]
        assert isinstance(value, dict)
        field_name = value["name"]
        assert isinstance(field_name, str)
        assert field_name in guide
        assert f"`{field}`" in guide
    assert "0.1.0b6" in guide  # Explicit public-version warning, not availability.
    assert "(ARTIST_CHOICES.md)" in guide
    assert f"(COMMONS_COLOUR{suffix}.md)" in guide
    offered = re.findall(r"```text\n(.*?)\n```", guide, re.DOTALL)
    assert len(offered) == 1
    for option in offered[0].splitlines():
        assert BUILTIN_VOCABULARY.lookup(FilterField.ARTIST, option).status in {
            LookupStatus.ANY,
            LookupStatus.KEY,
        }


def test_artist_choice_table_has_exactly_current_catalogue_labels_and_counts() -> None:
    guide = (ROOT / "ARTIST_CHOICES.md").read_text()
    rows = re.findall(r"^\| ([^|]+) \| (\d+) \|$", guide, re.MULTILINE)
    expected = Counter(artist_key(work.artist) for work in CATALOG)
    entries = BUILTIN_VOCABULARY.entries_for(FilterField.ARTIST)
    assert len(rows) == len(entries) == 557
    assert sum(int(count) for _, count in rows) == len(CATALOG) == 1000
    assert dict(rows) == {entry.label: str(expected[entry.key]) for entry in entries}
    assert "unsent works" in guide


def test_artist_only_card_is_combined_card_without_colour_row() -> None:
    for language in LABELS:
        suffix = _suffix(language)
        combined = (ROOT / f"examples/commons-artist-card{suffix}.yaml").read_text()
        row = (
            "      - entity: input_select.frame_gallery_colour\n"
            f"        name: {LABELS[language][0]}\n"
        )
        assert combined.count(row) == 1
        assert (
            combined.replace(row, "")
            == (ROOT / f"examples/commons-artist-only-card{suffix}.yaml").read_text()
        )
