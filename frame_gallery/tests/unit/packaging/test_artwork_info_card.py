"""Keep the optional native card complete, escaped, and separate from basics."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[3]


def test_optional_guide_and_complete_yaml_are_identical() -> None:
    guide = (PROJECT / "ARTWORK_INFO.md").read_text()
    blocks = re.findall(r"```yaml\n(.*?)```", guide, re.DOTALL)
    assert len(blocks) == 1
    assert blocks[0] == (PROJECT / "examples/artwork-info-card.yaml").read_text()
    assert "not available in" in guide
    assert "0.1.0b1" in guide
    assert "Initial value" in guide
    assert "`255`" in guide
    assert "`0`" in guide


def test_optional_card_extends_the_standard_without_a_custom_extension() -> None:
    basic = re.findall(r"```yaml\n(.*?)```", (PROJECT / "DOCS.md").read_text(), re.DOTALL)[1]
    card = (PROJECT / "examples/artwork-info-card.yaml").read_text()
    assert card.startswith(basic)
    assert "custom:" not in card
    assert "camera.frame_gallery_preview" in card
    assert "script.frame_gallery_new_artwork" in card
    assert "timer.frame_gallery_run" in card
    assert "state_not: active" in card
    assert 'state_not: ""' in card
    assert "state_not: unknown" in card
    assert "state_not: unavailable" in card
    assert "from_json(default={})" in card
    assert "if info is mapping" in card
    for field in ("title", "artist", "museum"):
        assert f"info.{field} is string and info.{field}" in card
        assert f"{{{{ info.{field} | e }}}}" in card
    assert "| safe" not in card
    assert "input_text.frame_gallery_artwork" not in basic
