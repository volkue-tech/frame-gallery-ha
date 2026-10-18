"""Offline restart sequences, not a reconstruction of the unrecorded b9 frames."""

from __future__ import annotations

import pytest
from tests.unit.observer.test_events import SEEN, Rig

from frame_gallery.isolation.executor import JsonObject
from frame_gallery.observer.event_backend import EventBackend
from frame_gallery.observer.event_controller import EventController
from frame_gallery.observer.model import Action, Command, Observation, SessionFailure, Status
from frame_gallery.observer.stream import SLIDESHOW_POLICY, Change


def running() -> tuple[Rig, EventController, list[Observation]]:
    r = Rig()
    r.backend = EventBackend(r.host, r.session, lambda: r.now, lambda _d: SLIDESHOW_POLICY)
    published: list[Observation] = []
    controller = EventController(
        send=lambda: 0,
        source=r.backend,
        publish=published.append,
        claim=lambda _c: True,
        stopped=lambda: False,
    )
    controller.start()
    assert controller.command(Command(Action.NEW_ARTWORK, "offline_restart_01", r.now))
    r.baseline()
    controller.tick()
    assert published[-1] == SEEN
    return r, controller, published


def push(r: Rig, controller: EventController, change: Change) -> None:
    r.add({"kind": "change", "change": change.to_json()}, r.now)
    controller.tick()


@pytest.mark.parametrize(
    "incomplete",
    [
        [Change("rotation", "MY_OFFLINE")],
        [Change("selected", "MY_OFFLINE"), Change("mode", "on")],
        [Change("selected", "MY_NEXT"), Change("rotation", "MY_OTHER")],
        [Change("selected", "MY_NEXT"), Change("selected", "MY_NEXT")],
        [
            Change("selected", "MY_NEXT"),
            Change("rotation", "MY_NEXT"),
            Change("rotation", "MY_NEXT"),
        ],
    ],
)
def test_incomplete_restart_clears_caption_then_accepts_a_whole_new_cycle(
    incomplete: list[Change],
) -> None:
    r, controller, published = running()
    stops = r.session.stops
    r.now = 12
    push(r, controller, Change("invalidate"))  # observed nav; never Art Mode on
    for change in incomplete:
        push(r, controller, change)
    assert published[-1] == Observation(Status.CHECKING)
    assert r.backend._confirmed_at is None
    assert r.session.stops == stops
    assert len(r.session.starts) == 1
    r.now = 612
    for change in (
        Change("selected", "MY_NEXT"),
        Change("rotation", "MY_NEXT"),
        Change("mode", "on"),
    ):
        push(r, controller, change)
    assert published[-1].status is Status.UNIDENTIFIED
    assert published[-1].content_id == "MY_NEXT"
    assert len(r.session.starts) == 1
    assert r.session.stops == stops


def test_incomplete_timeout_stays_receive_only_and_never_uses_late_halves() -> None:
    r, controller, published = running()
    stops = r.session.stops
    r.now = 12
    push(r, controller, Change("selected", "MY_NEXT"))
    r.now = 17
    controller.tick()
    assert published[-1] == Observation(Status.CHECKING)
    assert r.backend._slideshow is not None
    assert r.backend._slideshow.pending_at is None
    push(r, controller, Change("rotation", "MY_NEXT"))
    push(r, controller, Change("mode", "on"))
    assert published[-1] == Observation(Status.CHECKING)
    assert r.backend._confirmed_at is None
    assert r.session.stops == stops
    r.now = 612
    for change in (
        Change("selected", "MY_NEXT"),
        Change("rotation", "MY_NEXT"),
        Change("mode", "on"),
    ):
        push(r, controller, change)
    assert published[-1].content_id == "MY_NEXT"
    assert len(r.session.starts) == 1


@pytest.mark.parametrize("last", [Change("mode", "off"), Change("standby")])
def test_recovery_never_survives_mode_off_or_standby(last: Change) -> None:
    r, controller, published = running()
    r.now = 12
    push(r, controller, Change("rotation", "MY_OFFLINE"))
    push(r, controller, last)
    assert published[-1].status in {Status.PAUSED, Status.TV_IN_USE}
    stops = r.session.stops
    for change in (
        Change("selected", "MY_NEXT"),
        Change("rotation", "MY_NEXT"),
        Change("mode", "on"),
    ):
        push(r, controller, change)
    assert published[-1].status in {Status.PAUSED, Status.TV_IN_USE}
    assert r.session.stops == stops
    assert len(r.session.starts) == 1


def test_recovery_logs_once_and_never_freshens_same_id(caplog: pytest.LogCaptureFixture) -> None:
    r, controller, published = running()
    r.now = 12
    for _ in range(20):
        push(r, controller, Change("rotation", "MY_OFFLINE"))
    assert len(caplog.records) == 1
    assert "same connection" in caplog.text
    assert r.backend._confirmed_at is None
    for change in (
        Change("selected", "MY_OFFLINE"),
        Change("rotation", "MY_OFFLINE"),
        Change("mode", "on"),
    ):
        push(r, controller, change)
    assert published[-1] == Observation(Status.CHECKING)
    assert r.backend._confirmed_at is None
    r.backend.stop()
    r.backend.start()
    r.baseline()
    r.backend.update()
    push(r, controller, Change("rotation", "MY_OFFLINE"))
    assert len(caplog.records) == 2  # one warning per new explicit session


@pytest.mark.parametrize("reason", list(SessionFailure))
def test_fixed_failure_codes_reach_parent_log_and_disarm(
    reason: SessionFailure,
    caplog: pytest.LogCaptureFixture,
) -> None:
    r, controller, published = running()
    r.add({"kind": "end", "status": "unavailable", "reason": reason.value})
    controller.tick()
    assert published[-1] == Observation(Status.UNAVAILABLE)
    assert f"reason={reason.value}" in caplog.text
    assert "no reconnect" in caplog.text
    assert len(r.session.starts) == 1


@pytest.mark.parametrize(
    "end",
    [
        {"kind": "end", "status": "unavailable", "reason": "Bearer secret-token"},
        {"kind": "end", "status": "unavailable", "reason": []},
        {"kind": "end", "status": "paused", "reason": "startup_failed"},
    ],
)
def test_arbitrary_failure_text_is_never_logged(
    end: JsonObject,
    caplog: pytest.LogCaptureFixture,
) -> None:
    r, controller, published = running()
    r.add(end)
    controller.tick()
    assert published[-1] == Observation(Status.UNAVAILABLE)
    assert "event_contract_rejected" in caplog.text
    assert "secret-token" not in caplog.text


def test_stale_or_malformed_event_still_ends_not_resynchronizes() -> None:
    r, controller, published = running()
    r.now = 16
    r.add({"kind": "change", "change": Change("rotation", "MY_OFFLINE").to_json()}, 10)
    controller.tick()
    assert published[-1] == Observation(Status.UNAVAILABLE)
    assert len(r.session.starts) == 1
