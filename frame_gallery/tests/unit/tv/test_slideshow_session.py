"""Pinned library over socketpair: real parser, no TCP/HA/Frame access."""

from __future__ import annotations

import contextlib
import os
from collections.abc import Generator
from typing import Any

import pytest
import samsungtvws
import websocket
from samsungtvws.rest import SamsungTVRest

from frame_gallery.isolation.executor import JsonObject
from frame_gallery.observer.event_backend import EventBackend
from frame_gallery.observer.model import Evidence, Observation, Status
from frame_gallery.observer.stream import SLIDESHOW_POLICY, Change
from frame_gallery.tv import samsung_task as task
from tests.unit.observer.test_events import Session
from tests.unit.observer.test_slideshow import rotation, selected
from tests.unit.tv.test_event_session import D2D, IDENTITY, EventTV, payload


@pytest.fixture
def pipe() -> Generator[tuple[int, int], None, None]:
    read_fd, write_fd = os.pipe()
    os.set_blocking(read_fd, False)
    try:
        yield read_fd, write_fd
    finally:
        os.close(read_fd)
        with contextlib.suppress(OSError):
            os.close(write_fd)


def capture(
    events: list[JsonObject], monkeypatch: pytest.MonkeyPatch, fd: int
) -> tuple[list[JsonObject], list[str]]:
    tv = EventTV(events)
    monkeypatch.setattr(websocket, "create_connection", tv.create_connection)
    rest_calls, d2d_calls = [], []

    def device(_s: Any) -> JsonObject:
        rest_calls.append(True)
        return {"device": {"id": IDENTITY}}

    monkeypatch.setattr(SamsungTVRest, "rest_device_info", device)
    thumbnail = D2D()

    def d2d(*_a: Any) -> D2D:
        d2d_calls.append(True)
        return thumbnail

    monkeypatch.setattr(samsungtvws.SamsungTVArt, "_open_d2d_socket", d2d)
    monkeypatch.setattr(task, "current_id_once", lambda *_a: pytest.fail("No extra ID query"))
    request = payload(fd)
    request["policy"] = SLIDESHOW_POLICY.to_json()
    emitted: list[JsonObject] = []
    try:
        assert task.observe_session_task(request, emitted.append) == {"status": "paused"}
    finally:
        tv.close()
    assert len(tv.urls) == 1
    assert rest_calls == [True]
    assert d2d_calls == [True]
    assert thumbnail.closed
    assert tv.requests == [
        "get_artmode_status",
        "get_current_artwork",
        "get_thumbnail",
        "get_current_artwork",
        "get_artmode_status",
    ]
    assert websocket.create_connection == tv.create_connection
    return emitted, tv.requests


def test_two_slideshow_cycles_and_nav_keep_same_socket_without_requests(
    monkeypatch: pytest.MonkeyPatch, pipe: tuple[int, int]
) -> None:
    events: list[JsonObject] = [
        {"event": "art_mode_changed", "status": "nav"},
        selected("MY_NEXT"),
        rotation("MY_NEXT"),
        {"event": "art_mode_changed", "status": "on"},
        selected("MY_THIRD"),
        rotation("MY_THIRD"),
        {"event": "art_mode_changed", "status": "on"},
        {"event": "art_mode_changed", "status": "on"},
        {"event": "art_mode_changed", "status": "off"},
    ]
    emitted, _requests = capture(events, monkeypatch, pipe[0])
    assert emitted[0]["kind"] == "baseline"
    assert [e["kind"] for e in emitted] == ["baseline"] + ["change"] * 9
    changes = [Change.from_json(e["change"]) for e in emitted[1:]]  # type: ignore[arg-type]
    assert changes == [
        Change("invalidate"),
        Change("selected", "MY_NEXT"),
        Change("rotation", "MY_NEXT"),
        Change("mode", "on"),
        Change("selected", "MY_THIRD"),
        Change("rotation", "MY_THIRD"),
        Change("mode", "on"),
        Change("mode", "on"),
        Change("mode", "off"),
    ]


def test_captured_standby_ends_normally_without_follow_up_query_or_reconnect(
    monkeypatch: pytest.MonkeyPatch, pipe: tuple[int, int]
) -> None:
    emitted, _requests = capture(
        [{"event": "go_to_standby"}, {"event": "art_mode_changed", "status": "on"}],
        monkeypatch,
        pipe[0],
    )
    assert [e["kind"] for e in emitted] == ["baseline", "change"]
    assert emitted[-1] == {"kind": "change", "change": Change("standby").to_json()}


def test_restart_notifications_then_complete_cycles_use_one_real_parser_socket(
    monkeypatch: pytest.MonkeyPatch, pipe: tuple[int, int]
) -> None:
    events: list[JsonObject] = [
        {"event": "art_mode_changed", "status": "nav"},
        rotation("MY_OFFLINE"),  # valid but cannot itself confirm a work
        selected("MY_OFFLINE"),
        {"event": "art_mode_changed", "status": "on"},  # rotation missing
        selected("MY_NEXT"),
        rotation("MY_NEXT"),
        {"event": "art_mode_changed", "status": "on"},
        selected("MY_THIRD"),
        rotation("MY_THIRD"),
        {"event": "art_mode_changed", "status": "on"},
        {"event": "art_mode_changed", "status": "off"},
    ]
    emitted, _requests = capture(events, monkeypatch, pipe[0])
    raw = emitted[0]["observation"]
    assert isinstance(raw, dict)
    baseline = Observation.from_json(
        {k: raw[k] for k in ("status", "device_id", "content_id", "thumbnail_sha256")}
    )

    class Observer:
        device_id = baseline.device_id

        def session_request(self) -> JsonObject:
            return {}

        def accept_snapshot(self, value: JsonObject) -> Observation:
            assert value == raw  # real parser transport test, not an image-verifier substitute
            return baseline

        def accept_slideshow(self, content_id: str) -> Observation:
            return Observation(
                Status.UNIDENTIFIED, self.device_id, content_id, None, Evidence.SLIDESHOW
            )

    session = Session()
    backend = EventBackend(Observer(), session, lambda: 10, lambda _d: SLIDESHOW_POLICY)
    assert backend.start() == Observation(Status.CHECKING)
    observed: list[Observation] = []
    for event in emitted:
        session.queue.append((event, 10))
        result = backend.update()
        if result is not None:
            observed.append(result)
    assert [v.content_id for v in observed if v.evidence is Evidence.SLIDESHOW] == [
        "MY_NEXT",
        "MY_THIRD",
    ]
    assert all(v.status is not Status.UNAVAILABLE for v in observed)
    assert observed[-1].status is Status.TV_IN_USE
    assert len(session.starts) == 1


@pytest.mark.parametrize(
    "bad",
    [
        {**selected(), "is_shown": "No"},
        {**rotation(), "type": "unknown"},
        {"event": "art_mode_changed", "status": "unknown"},
        {"event": "unknown"},
    ],
)
def test_bad_firmware_event_ends_without_fallback(
    bad: JsonObject, monkeypatch: pytest.MonkeyPatch, pipe: tuple[int, int]
) -> None:
    emitted, _requests = capture([bad], monkeypatch, pipe[0])
    assert emitted[-1] == {"kind": "end", "status": "unavailable", "reason": "event_rejected"}
