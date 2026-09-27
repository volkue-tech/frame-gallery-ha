"""The television task over the **installed** samsungtvws 3.0.6 (D-161, D-162).

``samsungtvws`` and ``websocket-client`` run unchanged; only the steps that
would open a network connection are replaced:

* ``websocket.create_connection`` (TCP, TLS, and the HTTP upgrade) returns a
  real ``websocket.WebSocket`` over a socket pair, served by
  :class:`tests.support.socket_tv.SocketTV`;
* the REST capability check returns a Frame TV's answer.

The D2D upload socket is a real ``socket.connect``: the task's connect guard
sees it first, then the session's H2 guard blocks it, so nothing leaves the
host. The timing constants are shortened so a pairing time-out takes a
fraction of a second.
"""

from __future__ import annotations

import gc
import hashlib
import json
import time
import warnings
from collections.abc import Iterator
from ipaddress import IPv4Address
from pathlib import Path

import pytest
import samsungtvws
import websocket
from samsungtvws.rest import SamsungTVRest

from frame_gallery.isolation.executor import JsonObject
from frame_gallery.tv import samsung_task
from frame_gallery.tv.contract import TvRequest
from frame_gallery.tv.samsung_task import ConnectGuard, install_connect_guard, run_delivery
from tests.support.socket_tv import D2D_PORT, SocketTV, TvScript

HOST = IPv4Address("192.0.2.20")
JPEG = b"\xff\xd8" + b"x" * 300 + b"\xff\xd9"
SEED = "87654321"


@pytest.fixture(autouse=True)
def _short_waits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(samsung_task, "CONNECT_S", 0.3)
    monkeypatch.setattr(samsung_task, "PAIRING_WAIT_S", 0.4)
    monkeypatch.setattr(samsung_task, "UPLOAD_ALLOWANCE_S", 0.5)
    monkeypatch.setattr(samsung_task, "RESULT_MARGIN_S", 0.1)
    monkeypatch.setattr(samsung_task, "MIN_WAIT_S", 0.05)


@pytest.fixture(autouse=True)
def _frame_tv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        SamsungTVRest,
        "rest_device_info",
        lambda _self: {"device": {"FrameTVSupport": "true"}},
    )


@pytest.fixture
def guard() -> Iterator[ConnectGuard]:
    installed = install_connect_guard(HOST)
    try:
        yield installed
    finally:
        installed.undo()


class Run:
    def __init__(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, **script: object) -> None:
        self.tv = SocketTV(TvScript(**script))  # type: ignore[arg-type]
        monkeypatch.setattr(websocket, "create_connection", self.tv.create_connection)
        self.jpeg = tmp_path / "delivery-0.jpg"
        self.jpeg.write_bytes(JPEG)
        self.events: list[JsonObject] = []

    def deliver(self, guard: ConnectGuard, token: str | None = None) -> JsonObject:
        request = TvRequest(
            HOST, token, self.jpeg, hashlib.sha256(JPEG).hexdigest(), time.monotonic() + 5.0
        )
        # The library does not close its D2D socket when the connect fails;
        # the worker exits after its task, so only an in-process run sees it.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            try:
                return run_delivery(
                    samsung_task.load_library(),
                    request,
                    self.events.append,
                    guard_tripped=guard.tripped,
                )
            finally:
                self.tv.close()
                gc.collect()

    def markers(self) -> list[object]:
        return [event["marker"] for event in self.events if "marker" in event]


def test_a_first_pairing_sends_no_token_and_relays_the_issued_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, guard: ConnectGuard
) -> None:
    run = Run(tmp_path, monkeypatch)
    outcome = run.deliver(guard)
    assert "token=" not in run.tv.urls[0]
    assert "name=" in run.tv.urls[0]
    assert run.events[0] == {"token": "12345678"}
    assert run.markers() == ["connected", "upload_started"]
    # upload() asked no second time for the version, and its D2D socket went
    # to the TV's address: past the connect guard, into the H2 blocker.
    assert run.tv.requests == ["api_version", "send_image"]
    assert guard.blocked == []
    assert outcome["status"] == "protocol"
    assert outcome["detail"] == (
        "unexpected upload reply (NetworkBlockedError); the TV may hold the image"
    )


def test_the_stored_token_is_sent_exactly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, guard: ConnectGuard
) -> None:
    """No newline or other byte is added to the token in the URL (D-162)."""
    run = Run(tmp_path, monkeypatch, issue_token=SEED)
    run.deliver(guard, token=SEED)
    assert run.tv.urls[0].endswith(f"&token={SEED}")
    assert not [event for event in run.events if "token" in event]


def test_a_rejection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, guard: ConnectGuard) -> None:
    run = Run(tmp_path, monkeypatch, connections=["unauthorized"])
    outcome = run.deliver(guard, token=SEED)
    assert (outcome["status"], outcome["pairing"]) == ("not_authorized", "rejected")
    assert len(run.tv.urls) == 1


def test_silence_after_the_handshake_is_an_unaccepted_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, guard: ConnectGuard
) -> None:
    run = Run(tmp_path, monkeypatch, connections=["silent", "ok"])
    outcome = run.deliver(guard)
    assert (outcome["status"], outcome["pairing"]) == ("not_authorized", "prompt")
    assert len(run.tv.urls) == 1  # never retried (D-115)


def test_a_hung_handshake_is_unreachable_and_retried(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, guard: ConnectGuard
) -> None:
    run = Run(tmp_path, monkeypatch, connections=["hang"])
    outcome = run.deliver(guard)
    assert (outcome["status"], outcome["pairing"]) == ("unreachable", None)
    assert len(run.tv.urls) == 2


def test_a_missing_ready_event_is_retried_on_a_new_connection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, guard: ConnectGuard
) -> None:
    """The library's second open() on the same object would reuse the stale
    connection; the task makes a new one."""
    run = Run(tmp_path, monkeypatch, connections=["no_ready", "ok"])
    run.deliver(guard)
    assert len(run.tv.urls) == 2
    assert run.markers()[0] == "connected"
    assert run.tv.requests[0] == "api_version"


def test_art_api_0_97_uploads_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, guard: ConnectGuard
) -> None:
    run = Run(tmp_path, monkeypatch, api_version="0.97")
    outcome = run.deliver(guard)
    assert outcome["status"] == "unsupported"
    assert run.tv.requests == ["api_version"]
    assert run.markers() == ["connected"]


def test_an_upload_socket_to_another_address_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, guard: ConnectGuard
) -> None:
    run = Run(tmp_path, monkeypatch, d2d_ip="192.0.2.99")
    outcome = run.deliver(guard)
    assert guard.blocked == [f"192.0.2.99:{D2D_PORT}"]
    assert outcome == {
        "status": "protocol",
        "detail": "the worker's connect guard refused an address other than the TV's",
        "pairing": None,
    }
    assert run.markers() == ["connected", "upload_started"]


def test_the_libraries_select_refusal_is_recognised(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, guard: ConnectGuard
) -> None:
    """The TV's own error reply to select_image, as the installed library
    reports it, is what the task maps to ``refused``."""
    run = Run(tmp_path, monkeypatch)
    art = samsung_task.load_library().art_class(str(HOST), port=8002, timeout=1, key_press_delay=0)
    try:
        connection = art.open()
        with pytest.raises(samsungtvws.exceptions.ResponseError) as caught:
            art.select_image("MY_F0042", show=True)
    finally:
        connection.shutdown()
        run.tv.close()
    assert samsung_task._tv_error(caught.value) == " (TV error select_image -11)"
    assert run.tv.requests == ["select_image"]
    del guard


def test_the_socket_tv_replies_parse_as_the_library_expects() -> None:
    """A guard against drift in the test double itself."""
    reply = {"event": "d2d_service_message", "data": json.dumps({"event": "api_version"})}
    frame = samsungtvws.helper.process_api_response(json.dumps(reply))
    assert frame["event"] == "d2d_service_message"
