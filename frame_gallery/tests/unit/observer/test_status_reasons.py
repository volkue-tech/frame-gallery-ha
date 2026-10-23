"""Bounded protocol/status payloads and complete offline native-card contracts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import cast

import pytest
from tests.unit.ha.test_current_artwork import Rig, response

from frame_gallery.isolation.executor import JsonValue
from frame_gallery.observer.model import Observation, Status, StatusReason


@pytest.mark.parametrize("reason", list(StatusReason))
def test_reason_roundtrip_and_ha_publisher_uses_only_validated_codes(reason: StatusReason) -> None:
    seen = Observation(Status.PAUSED, reason=reason)
    assert Observation.from_json(seen.to_json()) == seen
    rig = Rig()
    rig.transport.add(response({}, 404), response({}))
    assert rig.publish(seen)
    payload = json.loads(rig.transport.calls[-1].request.body or b"")
    assert payload["state"] == "paused"
    assert payload["attributes"]["status_reason"] == reason.value
    assert "title" not in payload["attributes"]
    assert not payload["attributes"]["preview_available"]


@pytest.mark.parametrize("bad", [[], {}, 1, True, "secret raw remote error", "other"])
def test_reason_rejects_untrusted_types_and_arbitrary_text(bad: JsonValue) -> None:
    value = Observation(Status.PAUSED).to_json()
    value["reason"] = bad
    with pytest.raises(ValueError, match=r"reason|StatusReason"):
        Observation.from_json(value)


def test_nonenum_reason_and_artwork_reason_cannot_borrow_metadata() -> None:
    with pytest.raises(ValueError, match="reason"):
        Observation(Status.PAUSED, reason=cast(StatusReason, "untrusted"))
    with pytest.raises(ValueError, match="reason"):
        Observation(
            Status.ARTWORK, "a" * 64, "MY_KNOWN", "b" * 64, reason=StatusReason.SERVICE_STOPPED
        )


@pytest.mark.parametrize("language", ["", ".de", ".fr", ".es", ".it"])
def test_new_status_card_is_complete_safe_and_has_every_known_reason(language: str) -> None:
    root = Path(__file__).resolve().parents[3]
    name = "CURRENT_STATUS" + language + ".md"
    text = (root / name).read_text()
    blocks = re.findall(r"```yaml\n(.*?)\n```", text, re.S)
    assert len(blocks) == 1
    card = blocks[0]
    assert card.startswith("type: markdown\ntitle: Frame Gallery — ")
    assert card.endswith("{% endif %}")
    assert "!" + name in (root / ".dockerignore").read_text().splitlines()
    for code in ("", ".de", ".fr", ".es", ".it"):
        if code != language:
            assert "(CURRENT_STATUS" + code + ".md)" in text
    for reason in StatusReason:
        assert "'" + reason.value + "': " in card
    for guard in (
        "item.state == 'artwork' and age >= 0",
        "age <",
        "item.last_reported",
        ("(900 if item.attributes.get('confirmation_method') == 'slideshow_events' else 90)"),
        "item.attributes.get('status_reason', '')",
        "{% elif reason in messages %}",
        "preview_available",
        "states(camera_entity) not in ['unknown', 'unavailable']",
        ("state_attr(camera_entity, 'file_path') == '/media/frame_gallery/preview/current.jpg'"),
        "picture is string and picture",
        "preview_sha256",
        "| e",
    ):
        assert guard in card
    assert card.index("age >= 0") < card.index("<img") < card.index("display_artist")
    assert "custom:" not in card
    assert "input_text." not in card
    assert "token=" not in card
    # JSON quoting preserves apostrophes, Unicode and escapes inside Jinja literals.
    reason_lines = re.findall(r"^      '[^']+': (.+?)(?:,)?$", card, re.M)
    assert len(reason_lines) == len(StatusReason)
    for value in reason_lines:
        assert isinstance(json.loads(value.rstrip(",")), str)
