"""Synthetic offline state checks; no television or network connection."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, cast

import pytest

from frame_gallery.observer.stream import (
    MAX_EVENTS,
    MAX_FRAME,
    MAX_REFRESHES,
    SLIDESHOW_POLICY,
    Change,
)
from frame_gallery.tv.event_frames import FrameBounds, RefreshExpired, SessionClosed
from frame_gallery.tv.state_query import (
    StateInterrupted,
    current_state_events,
    notification,
    read_current_state,
)
from tests.unit.observer.test_events import envelope
from tests.unit.tv.test_event_frames import Connection

POLICY = replace(SLIDESHOW_POLICY, state_refresh=True)


class Rig:
    def __init__(self) -> None:
        self.now = 0.0
        self.cancel = False
        self.connection: Any = cast(Any, Connection())
        self.connection.send = self.send
        self.connection.recv = self.recv
        self.request: dict[str, Any] | None = None
        self.sent: list[dict[str, Any]] = []
        self.responses: list[Any] = []
        self.ids = ["MY_KNOWN", "MY_KNOWN"]
        self.bounds = FrameBounds(self.connection, lambda: self.now, lambda: self.cancel, 0)
        self.bounds.passive = True

    def send(self, raw: str) -> None:
        message = json.loads(raw)
        assert message["method"] == "ms.channel.emit"
        assert message["params"]["event"] == "art_app_request"
        assert message["params"]["to"] == "host"
        self.request = json.loads(message["params"]["data"])
        self.sent.append(self.request)

    def recv(self) -> Any:
        if self.responses:
            value = self.responses.pop(0)
            return value() if callable(value) else value
        if self.request is None:
            self.now += 1
            raise TimeoutError
        request, self.request = self.request, None
        body = {"request_id": request["id"]}
        if request["request"] == "get_artmode_status":
            body.update(event="artmode_status", value="on")
        else:
            assert request["request"] == "get_current_artwork"
            body.update(event="current_artwork", content_id=self.ids.pop(0))
        return envelope(body)

    def query(self) -> str:
        return read_current_state(self.connection, self.bounds, POLICY, TimeoutError)

    def listening(self) -> Any:
        return current_state_events(
            self.connection, self.bounds, POLICY, TimeoutError, now=lambda: self.now
        )

    def at(self, value: float) -> Any:
        def timeout() -> None:
            self.now = value
            raise TimeoutError

        return timeout


def test_four_coherent_getters_same_id_and_repeated_minute_budget() -> None:
    r = Rig()
    for at in (0, 60, 120):
        r.now, r.ids = at, ["MY_KNOWN", "MY_KNOWN"]
        assert r.query() == "MY_KNOWN"
        assert r.bounds._refresh_until is None
        with pytest.raises(ValueError, match="budget"):
            r.query()
    assert [item["request"] for item in r.sent] == [
        "get_artmode_status",
        "get_current_artwork",
        "get_current_artwork",
        "get_artmode_status",
    ] * 3
    assert len({item["id"] for item in r.sent}) == 12
    assert all(item["id"] == item["request_id"] for item in r.sent)


@pytest.mark.parametrize(
    "change", ["policy", "connection", "passive", "cancel", "cap", "legacy", "pending"]
)
def test_no_send_without_explicit_policy_and_bounds(change: str) -> None:
    r = Rig()
    policy = POLICY
    if change == "policy":
        policy = SLIDESHOW_POLICY
    elif change == "connection":
        r.bounds.connection = Connection()
    elif change == "passive":
        r.bounds.passive = False
    elif change == "cancel":
        r.cancel = True
    elif change == "cap":
        r.bounds._refreshes = MAX_REFRESHES
    elif change == "legacy":
        r.bounds._query_until = 5
    else:
        r.bounds._refresh_until = 5
    with pytest.raises((ValueError, SessionClosed)):
        read_current_state(r.connection, r.bounds, policy, TimeoutError)
    assert not r.sent


@pytest.mark.parametrize("value", ["off", "nav", "unknown", None, True])
def test_mode_must_be_on_before_any_id_request(value: Any) -> None:
    r = Rig()
    r.responses = [
        lambda: envelope({"event": "artmode_status", "id": r.sent[-1]["id"], "value": value})
    ]
    with pytest.raises(StateInterrupted) as caught:
        r.query()
    assert caught.value.change == (
        Change("mode", "off") if value == "off" else Change("invalidate")
    )
    assert len(r.sent) == 1


@pytest.mark.parametrize("bad", ["../bad", None, 3, ""])
def test_invalid_current_id_never_confirms(bad: Any) -> None:
    r = Rig()
    r.ids = [bad, "MY_KNOWN"]
    with pytest.raises(ValueError, match="ID"):
        r.query()
    assert len(r.sent) == 2


def test_changed_id_during_cycle_cannot_confirm() -> None:
    r = Rig()
    r.ids = ["MY_FIRST", "MY_SECOND"]
    with pytest.raises(StateInterrupted) as caught:
        r.query()
    assert caught.value.change is None
    assert len(r.sent) == 4


@pytest.mark.parametrize(
    "event",
    [
        {"event": "art_mode_changed", "status": "nav"},
        {"event": "art_mode_changed", "status": "off"},
        {"event": "go_to_standby", "extra": True},
        {"event": "unfamiliar_bounded_notification"},
    ],
)
def test_interleaved_mutation_stops_current_cycle_without_resend(event: dict[str, Any]) -> None:
    r = Rig()
    r.responses = [envelope(event)]
    with pytest.raises(StateInterrupted):
        r.query()
    assert len(r.sent) == 1


@pytest.mark.parametrize("field", ["id", "event", "request_id"])
def test_wrong_or_replayed_correlation_does_not_confirm(field: str) -> None:
    r = Rig()
    r.responses = [
        lambda: envelope(
            {
                "event": "artmode_status",
                "request_id": r.sent[-1]["id"],
                field: "wrong",
                "value": "on",
            }
        )
    ]
    with pytest.raises(StateInterrupted):
        r.query()
    assert len(r.sent) == 1


def test_interleaved_on_does_not_resend_or_extend_deadline() -> None:
    r = Rig()
    r.responses = [envelope({"event": "art_mode_changed", "status": "on"})] * 3
    assert r.query() == "MY_KNOWN"
    assert len(r.sent) == 4


@pytest.mark.parametrize("raw", [None, "", b"binary", "{bad", "{}"])
def test_bad_transport_or_envelope_fails_closed(raw: Any) -> None:
    r = Rig()
    r.responses = [raw]
    with pytest.raises(ValueError, match=r"transport|event|JSON|property|notification"):
        r.query()
    assert len(r.sent) == 1


def test_timeout_and_frozen_clock_flood_are_bounded() -> None:
    r = Rig()
    r.responses = [r.at(1), r.at(2), r.at(3), r.at(5)]
    with pytest.raises(RefreshExpired):
        r.query()
    assert len(r.sent) == 1
    assert r.bounds._refresh_until is None
    with pytest.raises(ValueError, match="budget"):
        r.query()
    r = Rig()
    r.responses = [envelope({"event": "art_mode_changed", "status": "on"})] * (MAX_EVENTS + 1)
    with pytest.raises(ValueError, match="frame budget"):
        r.query()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (envelope({"event": "unknown", "anything": "not metadata"}), None),
        (json.dumps({"event": "ms.channel.ready"}), None),
        (
            envelope({"event": "art_mode_changed", "status": "nav", "extra": True}),
            Change("invalidate"),
        ),
        (
            envelope({"event": "art_mode_changed", "status": "off", "extra": True}),
            Change("mode", "off"),
        ),
        (envelope({"event": "go_to_standby", "extra": True}), Change("standby")),
        (envelope({"event": "art_mode_changed", "status": "on"}), Change("mode", "on")),
        (envelope({"event": "art_mode_changed", "status": "on", "id": "old"}), None),
        (envelope({"event": "art_mode_changed", "status": "on", "extra": True}), None),
        (envelope({"event": "art_mode_changed", "status": "unknown"}), None),
    ],
)
def test_unknown_notifications_never_prove_and_negative_mode_is_honoured(
    raw: str, expected: Any
) -> None:
    assert notification(raw, POLICY) == expected


@pytest.mark.parametrize(
    "raw", ["[]", "{}", "x" * (MAX_FRAME + 1), json.dumps({"event": "ms.error"}), envelope([])]
)
def test_malformed_or_refused_notification_still_stops(raw: str) -> None:
    with pytest.raises(ValueError, match=r"notification|byte bound|refused|event"):
        notification(raw, POLICY)


def test_quiet_same_image_is_reconfirmed_each_minute_without_new_transport() -> None:
    r = Rig()
    stream = r.listening()
    r.responses = [r.at(60)]
    assert next(stream) == {"kind": "state_checking"}
    assert next(stream) == {"kind": "current_state", "content_id": "MY_KNOWN"}
    r.ids, r.responses = ["MY_KNOWN", "MY_KNOWN"], [r.at(120)]
    assert next(stream) == {"kind": "state_checking"}
    assert next(stream) == {"kind": "current_state", "content_id": "MY_KNOWN"}
    assert len(r.sent) == 8
    stream.close()


def test_menu_exit_recovers_without_any_on_notification_after_expired_baseline() -> None:
    r = Rig()
    stream = r.listening()
    r.responses = [envelope({"event": "art_mode_changed", "status": "nav"})]
    assert next(stream)["change"] == Change("invalidate").to_json()
    r.responses = [r.at(180)]  # the mode-on event was lost, TV is actually on
    assert not r.sent
    assert next(stream) == {"kind": "state_checking"}
    assert next(stream) == {"kind": "current_state", "content_id": "MY_KNOWN"}
    stream.close()


def test_still_in_menu_reads_only_mode_then_recovers_without_a_new_on_event() -> None:
    r = Rig()
    stream = r.listening()
    r.responses = [envelope({"event": "art_mode_changed", "status": "nav"})]
    assert next(stream)["change"] == Change("invalidate").to_json()
    r.responses = [r.at(60)]
    assert next(stream) == {"kind": "state_checking"}
    r.responses = [
        lambda: envelope(
            {
                "event": "artmode_status",
                "request_id": r.sent[-1]["id"],
                "value": "nav",
            }
        )
    ]
    assert next(stream)["change"] == Change("invalidate").to_json()
    assert [value["request"] for value in r.sent] == ["get_artmode_status"]
    r.request, r.responses = None, [r.at(120)]
    assert next(stream) == {"kind": "state_checking"}
    assert next(stream) == {"kind": "current_state", "content_id": "MY_KNOWN"}
    assert len(r.sent) == 5
    stream.close()


def test_standby_ends_without_getter() -> None:
    r = Rig()
    stream = r.listening()
    r.responses = [envelope({"event": "go_to_standby"})]
    assert next(stream)["kind"] == "change"
    with pytest.raises(StopIteration):
        next(stream)
    assert not r.sent


@pytest.mark.parametrize("value", ["off", "nav"])
def test_mode_off_or_menu_does_not_end_same_socket_recovery(value: str) -> None:
    r = Rig()
    stream = r.listening()
    r.responses = [envelope({"event": "art_mode_changed", "status": value})]
    assert next(stream)["kind"] == "change"
    r.responses = [r.at(60)]
    assert next(stream) == {"kind": "state_checking"}
    r.responses = [
        lambda: envelope({"event": "artmode_status", "id": r.sent[-1]["id"], "value": "off"})
    ]
    assert next(stream)["change"] == Change("mode", "off").to_json()
    assert len(r.sent) == 1
    r.request, r.responses = None, [r.at(120)]
    assert next(stream) == {"kind": "state_checking"}
    assert next(stream)["content_id"] == "MY_KNOWN"
    assert len(r.sent) == 5
    stream.close()


@pytest.mark.parametrize("bad", [False, True])
def test_deferred_initial_thumbnail_is_once_and_only_after_mode_on(bad: bool) -> None:
    r = Rig()
    snapshots: list[float] = []

    def snapshot() -> dict[str, Any]:
        snapshots.append(r.now)
        return {"content_id": None if bad else "MY_KNOWN", "thumbnail": "proof"}

    stream = current_state_events(
        r.connection, r.bounds, POLICY, TimeoutError, now=lambda: r.now, initial_snapshot=snapshot
    )
    r.responses = [r.at(60)]
    assert next(stream) == {"kind": "state_checking"}
    if bad:
        with pytest.raises(ValueError, match="deferred"):
            next(stream)
        return
    assert next(stream) == {
        "kind": "baseline",
        "observation": {"content_id": "MY_KNOWN", "thumbnail": "proof"},
    }
    assert len(r.sent) == 1
    r.responses = [r.at(120)]
    assert next(stream) == {"kind": "state_checking"}
    assert next(stream)["kind"] == "current_state"
    assert snapshots == [60]
    assert len(r.sent) == 5
    stream.close()


def test_parent_backpressure_does_not_schedule_the_next_read_too_soon() -> None:
    r = Rig()
    stream = r.listening()
    r.responses = [r.at(60)]
    assert next(stream) == {"kind": "state_checking"}
    r.now = 65
    assert next(stream)["kind"] == "current_state"
    r.ids, r.responses = ["MY_KNOWN", "MY_KNOWN"], [r.at(120), r.at(125)]
    assert next(stream) == {"kind": "state_checking"}
    assert next(stream)["kind"] == "current_state"
    assert r.bounds._last_refresh == 125
    stream.close()


def test_expired_initial_snapshot_ends_instead_of_downloading_thumbnail_again() -> None:
    r = Rig()
    attempts: list[float] = []

    def snapshot() -> dict[str, Any]:
        attempts.append(r.now)
        r.now += 5
        return {"content_id": "MY_KNOWN"}

    stream = current_state_events(
        r.connection, r.bounds, POLICY, TimeoutError, now=lambda: r.now, initial_snapshot=snapshot
    )
    r.responses = [r.at(60)]
    assert next(stream) == {"kind": "state_checking"}
    with pytest.raises(ValueError, match="no repeated thumbnail"):
        next(stream)
    assert attempts == [60]
    assert len(r.sent) == 1


def test_unknown_frame_clears_then_current_state_recovers_on_same_socket() -> None:
    r = Rig()
    stream = r.listening()
    r.responses = [envelope({"event": "unknown"})]
    assert next(stream) == {"kind": "state_checking"}
    r.responses = [r.at(60)]
    assert next(stream) == {"kind": "state_checking"}
    assert next(stream)["content_id"] == "MY_KNOWN"
    stream.close()


def test_interrupted_and_expired_cycles_wait_a_whole_minute() -> None:
    for interruption in (envelope({"event": "unknown"}), None):
        r = Rig()
        stream = r.listening()
        r.responses = [r.at(60)]
        assert next(stream) == {"kind": "state_checking"}
        r.responses = [r.at(65)] if interruption is None else [interruption]
        r.responses += [r.at(120)]
        assert next(stream) == {"kind": "state_checking"}
        if interruption is not None:
            assert next(stream) == {"kind": "state_checking"}
        r.request = None
        assert next(stream)["content_id"] == "MY_KNOWN"
        assert len(r.sent) == 5
        stream.close()


@pytest.mark.parametrize("raw", [None, "", b"binary"])
def test_closed_event_transport_is_terminal(raw: Any) -> None:
    r = Rig()
    r.responses = [raw]
    with pytest.raises(ValueError, match="transport"):
        next(r.listening())


def test_refresh_read_timeout_is_clamped_without_changing_legacy_once_latch() -> None:
    r = Rig()
    r.bounds.begin_refresh()
    assert r.bounds.read(1) == b"x"
    r.bounds._partial = None
    r.bounds.finish_refresh()
    r.bounds.begin_query()
    with pytest.raises(ValueError, match="once"):
        r.bounds.begin_query()
