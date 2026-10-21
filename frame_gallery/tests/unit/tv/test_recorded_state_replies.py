"""Offline regression replay of already-recorded, sanitized device replies."""

from __future__ import annotations

from typing import Any

import pytest

from frame_gallery.tv.state_query import StateInterrupted, _reply
from tests.support.recorded_state_replies import RECORDED_STATE_REPLIES
from tests.unit.observer.test_events import envelope
from tests.unit.tv.test_state_query import POLICY, Rig


@pytest.mark.parametrize(("request_name", "nonce", "body"), RECORDED_STATE_REPLIES)
def test_recorded_response_names_and_id_only_correlation_are_accepted(
    request_name: str, nonce: str, body: dict[str, Any]
) -> None:
    assert _reply(envelope(body), request_name, nonce, POLICY) == body


@pytest.mark.parametrize(("request_name", "nonce", "body"), RECORDED_STATE_REPLIES)
@pytest.mark.parametrize(
    "mutation",
    ["request_name", "other_reply", "unknown_reply", "stale", "conflict", "missing", "bad_id"],
)
def test_recorded_replies_still_require_the_right_event_and_fresh_correlation(
    request_name: str, nonce: str, body: dict[str, Any], mutation: str
) -> None:
    changed = dict(body)
    if mutation == "request_name":
        changed["event"] = request_name  # the old synthetic fake is not a protocol response
    elif mutation == "other_reply":
        changed["event"] = (
            "current_artwork" if request_name == "get_artmode_status" else "artmode_status"
        )
    elif mutation == "unknown_reply":
        changed["event"] = "unknown_reply"
    elif mutation == "stale":
        changed["id"] = "0" * 32
    elif mutation == "conflict":
        changed["request_id"] = "0" * 32
    elif mutation == "missing":
        del changed["id"]
    else:
        changed["id"] = None
    with pytest.raises(StateInterrupted) as caught:
        _reply(envelope(changed), request_name, nonce, POLICY)
    assert caught.value.change is None


@pytest.mark.parametrize(("request_name", "nonce", "body"), RECORDED_STATE_REPLIES)
@pytest.mark.parametrize("correlation", ["id", "request_id", "both"])
def test_recorded_reply_accepts_only_matching_present_correlation_fields(
    request_name: str, nonce: str, body: dict[str, Any], correlation: str
) -> None:
    changed = dict(body)
    if correlation != "id":
        changed["request_id"] = nonce
    if correlation == "request_id":
        del changed["id"]
    assert _reply(envelope(changed), request_name, nonce, POLICY) == changed


@pytest.mark.parametrize("event", ["artmode_status", "current_artwork", None])
def test_unknown_request_never_accepts_a_correlated_response(event: str | None) -> None:
    with pytest.raises(StateInterrupted):
        _reply(envelope({"event": event, "id": "a" * 32}), "unknown", "a" * 32, POLICY)


def test_complete_recorded_mode_current_current_mode_cycle_on_one_transport() -> None:
    rig = Rig()
    for name, _nonce, body in RECORDED_STATE_REPLIES:

        def receive(name: str = name, body: dict[str, Any] = body) -> str:
            assert rig.sent[-1]["request"] == name
            return envelope({**body, "id": rig.sent[-1]["id"]})

        rig.responses.append(receive)
    assert rig.query() == "MY_F0015"
    assert [item["request"] for item in rig.sent] == [
        "get_artmode_status",
        "get_current_artwork",
        "get_current_artwork",
        "get_artmode_status",
    ]
    assert len({item["id"] for item in rig.sent}) == 4
    assert rig.connection is rig.bounds.connection
    assert rig.bounds._refresh_until is None
