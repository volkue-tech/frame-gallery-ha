"""Structural five-language/native-card checks, not a claim of live HA rendering."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
LANGUAGES = {"en": "English", "de": "Deutsch", "fr": "Français", "es": "Español", "it": "Italiano"}


def name(code: str) -> str:
    return "CURRENT_PREVIEW" + ("" if code == "en" else "." + code) + ".md"


@pytest.mark.parametrize("language", LANGUAGES)
def test_complete_current_preview_card_gates_image_and_caption_together(language: str) -> None:
    guide = (ROOT / name(language)).read_text()
    assert "!" + name(language) in (ROOT / ".dockerignore").read_text().splitlines()
    for other, label in LANGUAGES.items():
        if other != language:
            assert f"[{label}]({name(other)})" in guide
    assert "/media/frame_gallery/preview/current.jpg" in guide
    assert "latest.jpg" in guide
    assert "128 MiB" in guide
    assert "32 KiB" in guide
    blocks = re.findall(r"```yaml\n(.*?)\n```", guide, re.DOTALL)
    assert len(blocks) == 1
    card = blocks[0]
    assert card.startswith("type: markdown\ntitle: Frame Gallery — ")
    assert "custom:" not in card
    for fragment in (
        "states.sensor.frame_gallery_current_artwork",
        "item.state == 'artwork'",
        "age >= 0",
        "age <",
        "item.last_reported",
        "(900 if item.attributes.get('confirmation_method') == 'slideshow_events' else 90)",
        "item.attributes.get('preview_available', false)",
        "picture is string and picture",
        "states(camera_entity) not in ['unknown', 'unavailable']",
        "state_attr(camera_entity, 'entity_picture')",
        "state_attr(camera_entity, 'file_path') == '/media/frame_gallery/preview/current.jpg'",
        "item.attributes.get('preview_sha256', '')",
        "| e",
        "item.attributes.get('display_title', '')",
        "item.attributes.get('display_artist', '')",
        "item.attributes.get('display_source', '')",
    ):
        assert fragment in card
    assert "input_text." not in card  # Last-sent text cannot establish current evidence.
    assert "http://" not in card
    assert "https://" not in card
    assert "token=" not in card  # No saved camera credential in the YAML.
    assert card.index("age >= 0") < card.index("<img") < card.index("display_title")
    assert "{% else %}" in card
    assert card.endswith("{% endif %}")
