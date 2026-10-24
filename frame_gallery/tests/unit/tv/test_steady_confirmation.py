"""D-252: real correlated reader, finite fake time, no network/TV or new socket."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from frame_gallery.observer.stream import SLIDESHOW_POLICY, Change
from frame_gallery.tv import steady_state
from frame_gallery.tv.event_frames import SessionClosed
from frame_gallery.tv.steady_state import confirmed_art_events
from tests.unit.observer.test_events import envelope
from tests.unit.observer.test_slideshow import rotation, selected
from tests.unit.tv.test_state_query import Rig

POLICY = replace(SLIDESHOW_POLICY, state_refresh=True, art_only_refresh=True)


def listen(r: Rig, confirmed: float = 0) -> Any:
    return confirmed_art_events(
        r.connection,
        r.bounds,
        POLICY,
        TimeoutError,
        confirmed_at=confirmed,
        now=lambda: r.now,
    )


def test_quiet_image_reconfirmed_for_seven_hours_without_checking_or_connection() -> None:
    r = Rig()
    stream = listen(r)
    for minute in range(1, 421):
        r.ids = ["MY_KNOWN", "MY_KNOWN"]
        assert next(stream) == {"kind": "current_state", "content_id": "MY_KNOWN"}
        assert r.now == minute * 60
        assert r.bounds.connection is r.connection
    assert len(r.sent) == 420 * 4
    assert {request["request"] for request in r.sent} == {
        "get_artmode_status",
        "get_current_artwork",
    }
    assert len({request["id"] for request in r.sent}) == len(r.sent)


@pytest.mark.parametrize("kind", ["standby", "nav", "off"])
@pytest.mark.parametrize("at_due_time", [False, True])
def test_queued_negative_mode_precedes_any_due_read(kind: str, at_due_time: bool) -> None:
    r = Rig()
    if at_due_time:
        r.now = 60
    body = (
        {"event": "go_to_standby"}
        if kind == "standby"
        else {"event": "art_mode_changed", "status": kind}
    )
    r.responses = [envelope(body)]
    stream = listen(r)
    assert next(stream)["kind"] == "change"
    with pytest.raises(StopIteration):
        next(stream)
    assert r.sent == []


@pytest.mark.parametrize("kind", ["off", "nav", "standby"])
def test_negative_during_read_stops_after_one_get_without_retry(kind: str) -> None:
    r = Rig()
    body = (
        {"event": "go_to_standby"}
        if kind == "standby"
        else {"event": "art_mode_changed", "status": kind}
    )
    r.responses = [r.at(60), envelope(body)]
    stream = listen(r)
    result = next(stream)
    assert result["kind"] == "change"
    with pytest.raises(StopIteration):
        next(stream)
    assert len(r.sent) == 1


@pytest.mark.parametrize("problem", ["timeout", "id_change", "stale_nonce", "unknown", "empty"])
def test_failed_cycle_is_terminal_never_waits_to_retry(problem: str) -> None:
    r = Rig()
    r.responses = [r.at(60)]
    if problem == "timeout":
        r.responses += [r.at(65)]
    elif problem == "id_change":
        r.ids = ["MY_A", "MY_B"]
    elif problem == "stale_nonce":
        r.responses += [envelope({"event": "artmode_status", "id": "0" * 32, "value": "on"})]
    elif problem == "unknown":
        r.responses += [envelope({"event": "unfamiliar"})]
    else:
        r.responses += [""]
    stream = listen(r)
    with pytest.raises(ValueError, match=r"Art|state"):
        next(stream)
    sent = len(r.sent)
    with pytest.raises(StopIteration):
        next(stream)
    assert len(r.sent) == sent


@pytest.mark.parametrize("at", [-1, 90, 900, float("nan"), float("inf")])
def test_initial_backpressure_or_bad_clock_cannot_freshen_baseline(at: float) -> None:
    r = Rig()
    r.now = at
    with pytest.raises(ValueError, match="Art confirmation"):
        next(listen(r))
    assert r.sent == []


def test_timeout_jump_past_freshness_does_not_send() -> None:
    r = Rig()
    r.responses = [r.at(91)]
    with pytest.raises(ValueError, match="fresh proof"):
        next(listen(r))
    assert r.sent == []


@pytest.mark.parametrize("broken", [False, True])
def test_selected_image_needs_art_on_before_query(broken: bool) -> None:
    r = Rig()
    r.responses = [envelope(selected("MY_NEXT"))]
    stream = listen(r)
    assert next(stream) == {"kind": "change", "change": Change("selected", "MY_NEXT").to_json()}
    if broken:
        with pytest.raises(ValueError, match="Art mode"):
            next(stream)
        assert r.sent == []
    else:
        r.responses = [
            envelope(rotation("MY_NEXT")),
            envelope({"event": "art_mode_changed", "status": "on"}),
        ]
        assert next(stream)["kind"] == next(stream)["kind"] == "change"
        r.ids = ["MY_NEXT", "MY_NEXT"]
        assert next(stream) == {"kind": "current_state", "content_id": "MY_NEXT"}


def test_duplicate_on_is_only_hint_and_does_not_renew_clock() -> None:
    r = Rig()
    r.responses = [envelope({"event": "art_mode_changed", "status": "on"})]
    stream = listen(r)
    assert next(stream)["kind"] == "change"
    r.now = 91
    with pytest.raises(ValueError, match="proof gap"):
        next(stream)
    assert r.sent == []


@pytest.mark.parametrize("raw", ["", 3, envelope({"event": "unfamiliar"})])
def test_idle_bad_or_unknown_frame_is_terminal(raw: Any) -> None:
    r = Rig()
    r.responses = [raw]
    with pytest.raises(ValueError, match="Art"):
        next(listen(r))
    assert r.sent == []


def test_cancellation_never_sends_or_reconnects() -> None:
    r = Rig()
    r.cancel = True
    with pytest.raises(SessionClosed):
        next(listen(r))
    assert r.sent == []


@pytest.mark.parametrize("broken", ["policy", "connection"])
def test_no_read_without_new_internal_policy_and_same_socket(broken: str) -> None:
    r = Rig()
    connection = object() if broken == "connection" else r.connection
    policy = SLIDESHOW_POLICY if broken == "policy" else POLICY
    stream = confirmed_art_events(connection, r.bounds, policy, TimeoutError, confirmed_at=0)
    with pytest.raises(ValueError, match="unapproved"):
        next(stream)
    assert r.sent == []


@pytest.mark.parametrize("finish", [59.0, 65.0, float("nan"), float("inf")])
def test_reply_clock_failure_never_becomes_a_confirmation(
    finish: float, monkeypatch: pytest.MonkeyPatch
) -> None:
    r = Rig()
    r.responses = [r.at(60)]

    def read(*_args: Any) -> str:
        r.now = finish
        return "MY_KNOWN"

    monkeypatch.setattr(steady_state, "read_current_state", read)
    with pytest.raises(ValueError, match="reply clock"):
        next(listen(r))
    assert r.sent == []


def test_frozen_monotonic_time_is_bounded_even_with_only_receive_timeouts() -> None:
    r = Rig()

    def timeout() -> None:
        raise TimeoutError

    r.connection.recv = timeout
    with pytest.raises(ValueError, match="clock did not progress"):
        next(listen(r))
    assert r.sent == []


def test_eight_hour_lifetime_still_ends_without_a_new_connection() -> None:
    r = Rig()
    stream = listen(r)
    for _ in range(479):
        r.ids = ["MY_KNOWN", "MY_KNOWN"]
        assert next(stream)["kind"] == "current_state"
    with pytest.raises(SessionClosed):
        next(stream)
    assert len(r.sent) == 479 * 4
