"""Real installed Art/websocket code over a socket pair; no TCP/TLS/TV access.

Notification names are explicitly synthetic. This is not device event evidence.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import socket
import time
from collections.abc import Callable, Generator
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest
import samsungtvws
import websocket
from samsungtvws.rest import SamsungTVRest

from frame_gallery.isolation.executor import JsonObject
from frame_gallery.observer.model import FRESH_S
from frame_gallery.observer.stream import SLIDESHOW_POLICY, EventPolicy
from frame_gallery.tv import samsung_task as module
from frame_gallery.tv import state_query
from frame_gallery.tv.event_frames import SessionClosed
from tests.support.socket_tv import SocketTV, TvScript, _send
from tests.unit.tv.test_event_frames import Connection
from tests.unit.tv.test_observation import Art, Unauthorized, library

HOST = "192.168.1.20"
IDENTITY = "uuid:offline-event-tv"
DEVICE = hashlib.sha256(IDENTITY.encode()).hexdigest()
POLICY = EventPolicy("offline.mode", "offline.content", "offline.invalidate")


@pytest.fixture
def pipe() -> Generator[tuple[int, int], None, None]:
    r, w = os.pipe()
    os.set_blocking(r, False)
    try:
        yield r, w
    finally:
        os.close(r)
        with contextlib.suppress(OSError):
            os.close(w)


def payload(fd: int) -> JsonObject:
    return {
        "host": HOST,
        "token": None,
        "device_id": DEVICE,
        "tokenless_grant": True,
        "enroll_device": False,
        "policy": POLICY.to_json(),
        "cancel_fd": fd,
    }


class D2D:
    def __init__(self) -> None:
        image = b"synthetic-thumbnail"
        header = json.dumps(
            {
                "fileLength": len(image),
                "fileID": "MY_OFFLINE",
                "fileType": "jpg",
                "num": 0,
                "total": 1,
            }
        ).encode()
        self.data = len(header).to_bytes(4, "big") + header + image
        self.closed = False

    def recv(self, n: int) -> bytes:
        out, self.data = self.data[:n], self.data[n:]
        return out

    def close(self) -> None:
        self.closed = True


class EventTV(SocketTV):
    def __init__(self, events: list[JsonObject], delay: float = 0) -> None:
        super().__init__(TvScript(issue_token=None))
        self.notifications = events
        self.delay = delay

    def _answer(self, sock: Any, message: dict[str, Any]) -> None:
        request = json.loads(message["params"]["data"])
        name, request_id = request["request"], request["request_id"]
        self.requests.append(name)
        body: dict[str, Any] = {"request_id": request_id, "event": name}
        if name == "get_artmode_status":
            body["value"] = "on"
        elif name == "get_current_artwork":
            body["content_id"] = "MY_OFFLINE"
        elif name == "get_thumbnail":
            body["conn_info"] = {}
        else:
            raise AssertionError(name)
        _send(sock, {"event": "d2d_service_message", "data": json.dumps(body)})
        if len(self.requests) == 5:
            time.sleep(self.delay)
            sock.sendall(b"\x89\x00")
            for event in self.notifications:
                _send(sock, {"event": "d2d_service_message", "data": json.dumps(event)})


def test_real_library_one_connection_initial_proof_then_only_events(
    monkeypatch: pytest.MonkeyPatch, pipe: tuple[int, int]
) -> None:
    tv = EventTV(
        [
            {"event": POLICY.mode_event, "value": "on"},
            {"event": POLICY.content_event, "content_id": "MY_OFFLINE"},
            {"event": POLICY.mode_event, "value": "off"},
        ],
        delay=0.3,
    )
    monkeypatch.setattr(websocket, "create_connection", tv.create_connection)
    pongs: list[int] = []
    original_pong = websocket.WebSocket.pong

    def pong(connection: websocket.WebSocket, value: Any) -> None:
        pongs.append(len(value))
        original_pong(connection, value)

    def forbid_ping(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("client keepalive forbidden")

    monkeypatch.setattr(websocket.WebSocket, "pong", pong)
    monkeypatch.setattr(websocket.WebSocket, "ping", forbid_ping)
    monkeypatch.setattr(SamsungTVRest, "rest_device_info", lambda _s: {"device": {"id": IDENTITY}})
    d2d = D2D()
    d2d_calls: list[bool] = []

    def d2d_socket(_self: Any, _info: Any) -> D2D:
        d2d_calls.append(True)
        return d2d

    monkeypatch.setattr(samsungtvws.SamsungTVArt, "_open_d2d_socket", d2d_socket)
    events: list[JsonObject] = []
    try:
        assert module.observe_session_task(payload(pipe[0]), events.append) == {"status": "paused"}
    finally:
        tv.close()
    assert len(tv.urls) == 1
    assert tv.requests == [
        "get_artmode_status",
        "get_current_artwork",
        "get_thumbnail",
        "get_current_artwork",
        "get_artmode_status",
    ]
    assert d2d_calls == [True]
    assert pongs == [0]
    assert d2d.closed
    assert events[0]["kind"] == "baseline"
    assert [x["kind"] for x in events] == ["baseline", "change", "change", "change"]


@pytest.mark.parametrize("ending", ["cancel", "standby"])
def test_real_library_opted_in_state_cycle_uses_same_socket_no_open_getter_or_setter(
    monkeypatch: pytest.MonkeyPatch, pipe: tuple[int, int], ending: str
) -> None:
    tv = EventTV([{"event": "go_to_standby"}] if ending == "standby" else [])
    monkeypatch.setattr(websocket, "create_connection", tv.create_connection)
    monkeypatch.setattr(SamsungTVRest, "rest_device_info", lambda _s: {"device": {"id": IDENTITY}})
    thumbnail = D2D()
    thumbnail_calls: list[bool] = []

    def d2d(_self: Any, _info: Any) -> D2D:
        thumbnail_calls.append(True)
        return thumbnail

    monkeypatch.setattr(samsungtvws.SamsungTVArt, "_open_d2d_socket", d2d)
    clock_calls = 0

    def now() -> float:
        nonlocal clock_calls
        clock_calls += 1
        return 0 if clock_calls == 1 else 60

    def events(connection: Any, bounds: Any, policy: Any, timeout: Any) -> Any:
        return state_query.current_state_events(connection, bounds, policy, timeout, now=now)

    monkeypatch.setattr(module, "current_state_events", events)
    observed: list[JsonObject] = []

    def emit(value: JsonObject) -> None:
        observed.append(value)
        if value.get("kind") == "current_state":
            os.write(pipe[1], b"stop")

    request = {
        **payload(pipe[0]),
        "policy": replace(SLIDESHOW_POLICY, state_refresh=True).to_json(),
    }
    try:
        assert module.observe_session_task(request, emit) == {"status": "paused"}
    finally:
        tv.close()
    assert len(tv.urls) == 1
    initial = [
        "get_artmode_status",
        "get_current_artwork",
        "get_thumbnail",
        "get_current_artwork",
        "get_artmode_status",
    ]
    extra = [
        "get_artmode_status",
        "get_current_artwork",
        "get_current_artwork",
        "get_artmode_status",
    ]
    assert tv.requests == initial + (extra if ending == "cancel" else [])
    assert thumbnail_calls == [True]
    if ending == "cancel":
        assert observed[1:3] == [
            {"kind": "state_checking"},
            {"kind": "current_state", "content_id": "MY_OFFLINE"},
        ]
        assert observed[-1] == {"kind": "end", "status": "paused"}
    else:
        assert observed[-1] == {"kind": "change", "change": {"kind": "standby", "value": ""}}


@pytest.mark.parametrize("value", [None, True, 1, "unknown"])
def test_bad_mode_is_not_a_confirmed_tv_in_use(
    value: Any, monkeypatch: pytest.MonkeyPatch, pipe: tuple[int, int]
) -> None:
    art = Art()
    art.info = {"device": {"id": IDENTITY}}
    art.mode = [value]
    lib = library(art)
    lib.websocket.create_connection = lambda: None
    monkeypatch.setattr(module, "load_library", lambda: lib)
    monkeypatch.setattr(
        module, "install_connect_guard", lambda _h: SimpleNamespace(undo=lambda: None)
    )
    events: list[JsonObject] = []
    module.observe_session_task(payload(pipe[0]), events.append)
    assert events == [{"kind": "end", "status": "unavailable", "reason": "startup_failed"}]


@pytest.mark.parametrize("error", [Unauthorized("secret"), RuntimeError("secret"), SessionClosed()])
def test_start_errors_status_only(
    error: Exception, monkeypatch: pytest.MonkeyPatch, pipe: tuple[int, int]
) -> None:
    art = Art()
    art.info = {"device": {"id": IDENTITY}}
    art.failure = error
    lib = library(art)
    lib.websocket.create_connection = lambda: None
    monkeypatch.setattr(module, "load_library", lambda: lib)
    monkeypatch.setattr(
        module, "install_connect_guard", lambda _h: SimpleNamespace(undo=lambda: None)
    )
    events: list[JsonObject] = []
    module.observe_session_task(payload(pipe[0]), events.append)
    expected = (
        "not_authorized"
        if isinstance(error, Unauthorized)
        else "paused"
        if isinstance(error, SessionClosed)
        else "unavailable"
    )
    expected_end = {"kind": "end", "status": expected}
    if expected == "unavailable":
        expected_end["reason"] = "startup_failed"
    assert events == [expected_end]
    assert "secret" not in str(events)


def test_no_bounded_transport_fails_closed(
    monkeypatch: pytest.MonkeyPatch, pipe: tuple[int, int]
) -> None:
    art = Art()
    art.info = {"device": {"id": IDENTITY}}
    lib = library(art)
    lib.websocket.create_connection = lambda: None
    monkeypatch.setattr(module, "load_library", lambda: lib)
    monkeypatch.setattr(
        module, "install_connect_guard", lambda _h: SimpleNamespace(undo=lambda: None)
    )
    out: list[JsonObject] = []
    module.observe_session_task(payload(pipe[0]), out.append)
    assert out == [{"kind": "end", "status": "unavailable", "reason": "startup_failed"}]


def test_worker_contract_and_sink_cleanup(
    monkeypatch: pytest.MonkeyPatch, pipe: tuple[int, int]
) -> None:
    closed: list[bool] = []

    def events(*_a: Any, **_kw: Any) -> Generator[JsonObject, None, None]:
        try:
            yield {"kind": "end", "status": "paused"}
        finally:
            closed.append(True)

    monkeypatch.setattr(module, "_session_events", events)
    monkeypatch.setattr(module, "load_library", lambda: library(Art()))
    monkeypatch.setattr(
        module,
        "install_connect_guard",
        lambda _h: SimpleNamespace(undo=lambda: closed.append(True)),
    )

    def sink(_event: JsonObject) -> None:
        raise ValueError("synthetic sink")

    with pytest.raises(ValueError, match="synthetic sink"):
        module.observe_session_task(payload(pipe[0]), sink)
    assert closed == [True, True]


@pytest.mark.parametrize(
    "change",
    [
        {"policy": None},
        {"cancel_fd": True},
        {"cancel_fd": "bad"},
        {"cancel_fd": 2},
        {"device_id": None, "enroll_device": True},
        {"unexpected": True},
    ],
)
def test_bad_contract_before_library(
    change: JsonObject, monkeypatch: pytest.MonkeyPatch, pipe: tuple[int, int]
) -> None:
    def forbid() -> None:
        raise AssertionError("must validate first")

    monkeypatch.setattr(module, "load_library", forbid)
    with pytest.raises(ValueError, match=r"invalid|pinned"):
        module.observe_session_task({**payload(pipe[0]), **change}, lambda _e: None)


def test_cancellation_pipe_and_validation(pipe: tuple[int, int], tmp_path: Path) -> None:
    assert not module._cancelled(pipe[0])
    os.write(pipe[1], b"x")
    assert module._cancelled(pipe[0])
    os.set_blocking(pipe[0], True)
    with pytest.raises(ValueError, match="cancellation"):
        module.observe_session_task(payload(pipe[0]), lambda _e: None)
    with (tmp_path / "file").open("wb") as f, pytest.raises(ValueError, match="cancellation"):
        module.observe_session_task(payload(f.fileno()), lambda _e: None)


@pytest.mark.parametrize("raw", ["", b"unexpected binary"])
def test_idle_timeout_and_bad_receive_contract(
    raw: Any, monkeypatch: pytest.MonkeyPatch, pipe: tuple[int, int]
) -> None:
    c: Any = Connection()
    replies = iter([TimeoutError("idle"), raw])

    def receive() -> Any:
        item = next(replies)
        if isinstance(item, Exception):
            raise item
        return item

    c.recv = receive
    art = Art()
    lib = library(art)
    lib.websocket.create_connection = lambda *_a, **_kw: c

    def baseline(a: Any, _device: Any) -> JsonObject:
        a.connection = lib.websocket.create_connection()
        return {"status": "unidentified", "content_id": "MY_OFFLINE"}

    monkeypatch.setattr(module, "_observe_art", baseline)
    monkeypatch.setattr(module, "load_library", lambda: lib)
    out: list[JsonObject] = []
    module.observe_session_task(payload(pipe[0]), out.append)
    assert out[-1] == {"kind": "end", "status": "unavailable", "reason": "receive_failed"}


@pytest.mark.parametrize(
    "change",
    [
        {"event": POLICY.content_event, "content_id": "MY_OTHER"},
        {"event": POLICY.invalidation_event},
        {"event": "unknown"},
    ],
)
def test_changed_or_unrecognized_event_ends_without_queries(
    change: JsonObject, monkeypatch: pytest.MonkeyPatch, pipe: tuple[int, int]
) -> None:
    c: Any = Connection()
    c.recv = lambda: json.dumps({"event": "d2d_service_message", "data": json.dumps(change)})
    art = Art()
    lib = library(art)
    lib.websocket.create_connection = lambda *_a, **_kw: c

    def baseline(a: Any, _device: Any) -> JsonObject:
        a.connection = lib.websocket.create_connection()
        return {"status": "unidentified", "content_id": "MY_OFFLINE"}

    monkeypatch.setattr(module, "_observe_art", baseline)
    monkeypatch.setattr(module, "load_library", lambda: lib)
    out: list[JsonObject] = []
    module.observe_session_task(payload(pipe[0]), out.append)
    assert len(out) == 2
    assert out[-1]["kind"] == ("end" if change["event"] == "unknown" else "change")


class QueryTV(EventTV):
    def __init__(self, mode: str, result: str) -> None:
        self.probe_policy = EventPolicy(
            "offline.mode", "offline.content", "offline.invalidate", "status", True
        )
        super().__init__([{"event": "offline.mode", "status": mode}])
        self.result = result
        self.cancel_query: Callable[[], None] = lambda: None

    def _answer(self, sock: Any, message: dict[str, Any]) -> None:
        if len(self.requests) < 5:
            super()._answer(sock, message)
            return
        request = json.loads(message["params"]["data"])
        self.requests.append(request["request"])
        assert request["request"] == "get_current_artwork"
        assert request["id"] == request["request_id"]
        if self.result == "cancel":
            self.cancel_query()
            return
        if self.result == "disconnect":
            sock.shutdown(socket.SHUT_RDWR)
            return
        for _ in range(2):
            _send(
                sock,
                {
                    "event": "d2d_service_message",
                    "data": json.dumps({"event": "offline.mode", "status": "on"}),
                },
            )
        body: JsonObject = {
            "event": "get_current_artwork",
            "request_id": request["request_id"],
            "id": request["id"],
            "content_id": "MY_NEW",
        }
        if self.result == "wrong_id":
            body["request_id"] = "wrong"
        elif self.result == "off":
            body = {"event": "offline.mode", "status": "off"}
        elif self.result == "error":
            body = {"event": "error", "request_id": request["request_id"], "secret": "not-logged"}
        _send(sock, {"event": "d2d_service_message", "data": json.dumps(body)})


@pytest.mark.parametrize(
    ("mode", "result"),
    [
        ("on", "ok"),
        ("off", "ok"),
        ("on", "wrong_id"),
        ("on", "off"),
        ("on", "error"),
        ("on", "cancel"),
        ("on", "disconnect"),
    ],
)
def test_real_library_one_extra_id_request_same_socket_no_library_getter_or_retry(
    mode: str, result: str, monkeypatch: pytest.MonkeyPatch, pipe: tuple[int, int]
) -> None:
    tv = QueryTV(mode, result)
    tv.cancel_query = lambda: os.close(pipe[1])
    monkeypatch.setattr(websocket, "create_connection", tv.create_connection)
    monkeypatch.setattr(SamsungTVRest, "rest_device_info", lambda _s: {"device": {"id": IDENTITY}})
    d2d = D2D()
    thumbnail_calls: list[bool] = []

    def thumbnail(_self: Any, _info: Any) -> D2D:
        thumbnail_calls.append(True)
        return d2d

    monkeypatch.setattr(samsungtvws.SamsungTVArt, "_open_d2d_socket", thumbnail)
    original_get = cast(Callable[[Any], Any], samsungtvws.SamsungTVArt.get_current)
    getters: list[bool] = []

    def get_current(art: Any) -> Any:
        getters.append(True)
        assert len(getters) <= 2, "No post-baseline library getter/discard loop"
        return original_get(art)

    def ping(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("No client keepalive")

    monkeypatch.setattr(samsungtvws.SamsungTVArt, "get_current", get_current)
    monkeypatch.setattr(websocket.WebSocket, "ping", ping)
    events: list[JsonObject] = []
    try:
        module.observe_session_task(
            {**payload(pipe[0]), "policy": tv.probe_policy.to_json()}, events.append
        )
    finally:
        tv.close()
    assert len(tv.urls) == 1
    assert len(thumbnail_calls) == 1
    assert len(getters) == 2
    assert tv.requests == [
        "get_artmode_status",
        "get_current_artwork",
        "get_thumbnail",
        "get_current_artwork",
        "get_artmode_status",
    ] + (["get_current_artwork"] if mode == "on" else [])
    if mode == "off":
        assert [e["kind"] for e in events] == ["baseline", "change"]
    elif result == "ok":
        assert [e["kind"] for e in events] == ["baseline", "querying", "current_id"]
        assert events[-1] == {"kind": "current_id", "content_id": "MY_NEW"}
    else:
        assert [e["kind"] for e in events] == ["baseline", "querying", "end"]
        assert events[-1]["status"] == ("paused" if result in {"off", "cancel"} else "unavailable")
    assert "not-logged" not in str(events)
    assert d2d.closed


def test_expired_baseline_never_triggers_a_follow_up_query(
    monkeypatch: pytest.MonkeyPatch, pipe: tuple[int, int]
) -> None:
    now = [0.0]
    monkeypatch.setattr(time, "monotonic", lambda: now[0])
    connection: Any = Connection()
    sent: list[str] = []
    connection.send = sent.append

    def receive() -> str:
        now[0] = FRESH_S
        return json.dumps(
            {
                "event": "d2d_service_message",
                "data": json.dumps({"event": "offline.mode", "status": "on"}),
            }
        )

    connection.recv = receive
    art = Art()
    lib = library(art)
    lib.websocket.create_connection = lambda *_a, **_kw: connection

    def baseline(a: Any, _device: Any) -> JsonObject:
        a.connection = lib.websocket.create_connection()
        return {"status": "unidentified", "content_id": "MY_OFFLINE"}

    monkeypatch.setattr(module, "_observe_art", baseline)
    monkeypatch.setattr(module, "load_library", lambda: lib)
    out: list[JsonObject] = []
    policy = EventPolicy("offline.mode", "offline.content", "offline.invalidate", "status", True)
    module.observe_session_task({**payload(pipe[0]), "policy": policy.to_json()}, out.append)
    assert out[-1] == {"kind": "end", "status": "paused"}
    assert len(out) == 2
    assert sent == []
