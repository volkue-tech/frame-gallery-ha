"""Candidate-only guides preserve native cards, freshness checks and old script IDs.

These are structural checks, not a claim that HA has rendered the candidate.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
LANGUAGES = {"en": "English", "de": "Deutsch", "fr": "Français", "es": "Español", "it": "Italiano"}


def name(language: str) -> str:
    suffix = "" if language == "en" else "." + language
    return "CURRENT_ARTWORK" + suffix + ".md"


@pytest.mark.parametrize("language", LANGUAGES)
def test_guides_have_complete_native_cards_and_matching_language_links(language: str) -> None:
    guide = (ROOT / name(language)).read_text()
    assert "!" + name(language) in (ROOT / ".dockerignore").read_text().splitlines()
    for other, label in LANGUAGES.items():
        if other != language:
            assert f"[{label}]({name(other)})" in guide
    assert "(examples/background-send-script.yaml)" in guide
    assert "`script.frame_gallery_new_artwork`" in guide
    assert "`hassio.app_start`" in guide
    assert "b7" in guide
    assert "b8" in guide
    assert "30" in guide
    assert "Wake-on-LAN" in guide or "wake-on-LAN" in guide
    blocks = re.findall(r"```yaml\n(.*?)\n```", guide, re.DOTALL)
    assert len(blocks) == 1
    card = blocks[0]
    assert card.startswith("type: markdown\ntitle: Frame Gallery — ")
    assert "custom:" not in card
    for fragment in (
        "states.sensor.frame_gallery_current_artwork",
        "item is not defined or item is none",
        "item.state == 'artwork' and",
        "as_timestamp(now()) - as_timestamp(item.last_reported, 0) < 90",
        "item.attributes.get('display_title', '')",
        "item.attributes.get('display_artist', '')",
        "item.attributes.get('display_source', '')",
        "item.state == 'validation_required'",
        "item.state == 'checking'",
        "item.state == 'unidentified'",
    ):
        assert fragment in card
    assert "{% else %}" in card
    assert "{% endif %}" in card
    assert "artwork_info" not in card  # Last-delivery captions cannot be current evidence.


def test_service_script_uses_explicit_commands_without_restarting_or_changing_ids() -> None:
    script = (ROOT / "examples/background-send-script.yaml").read_text()
    for fragment in (
        "mode: single",
        "entity_id: timer.frame_gallery_run",
        "action: hassio.app_start",
        "action: hassio.app_stdin",
        "command: new_artwork",
        'request_id: "{{ frame_gallery_request_id }}"',
        'issued_at: "{{ frame_gallery_issued_at }}"',
        "now().strftime('%Y%m%d%H%M%S%f')",
        'timeout: "00:00:05"',
        'timeout: "00:02:30"',
    ):
        assert fragment in script
    assert "hassio.app_restart" not in script
    assert "refresh_current" not in script
    assert "sensor.frame_gallery_current_artwork" in script
    assert "camera." not in script
