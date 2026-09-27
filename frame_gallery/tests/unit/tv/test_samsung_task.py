"""The television worker task, in-process, over a stand-in of the installed
samsungtvws 3.0.6 (tv/samsung_task.py; §12.1, §12.4, D-161, D-162)."""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
import json
import logging
import math
import os
import socket
import time
import warnings
from collections.abc import Callable, Iterator
from importlib.metadata import version
from ipaddress import IPv4Address
from pathlib import Path
from types import SimpleNamespace

import pytest
import samsungtvws

from frame_gallery.imaging.contract import MAX_OUTPUT_BYTES
from frame_gallery.isolation.executor import JsonObject
from frame_gallery.logs.redact import Redactor, set_active_redactor
from frame_gallery.tv import samsung_task
from frame_gallery.tv.contract import Pairing, TvRequest
from frame_gallery.tv.samsung_task import (
    ART_PORT,
    CLIENT_NAME,
    CONNECT_S,
    PAIRING_WAIT_S,
    RESULT_MARGIN_S,
    UPLOAD_ALLOWANCE_S,
    ConnectGuard,
    GuardViolation,
    install_connect_guard,
    load_library,
    quiet_library,
    read_delivery,
    run_delivery,
)
from tests.conftest import NetworkBlockedError
from tests.support.fake_samsungtvws import (
    FakeConnection,
    Recorder,
    Script,
    make_art_class,
    make_library,
    make_websocket,
)

HOST = IPv4Address("192.0.2.20")
"""TEST-NET-1: never a real device on a LAN."""

JPEG = b"\xff\xd8" + b"x" * 1000 + b"\xff\xd9"
SEED = "87654321"
NEW = "NEWTOKEN42"


class Rig:
    """One delivery over the fake library, with a fake monotonic clock.

    ``delays`` advance the clock whenever a library call is recorded whose
    event starts with the key, for example ``{"open:ok": 30}``.
    """

    def __init__(self, tmp_path: Path, **script: object) -> None:
        self.script = Script(**script)  # type: ignore[arg-type]
        self.now = 100.0
        self.delays: dict[str, float] = {}
        self.events: list[str] = []
        self.recorder = Recorder()
        self.library = make_library(self.script, self._record)
        self.jpeg = tmp_path / "delivery-0.jpg"
        self.jpeg.write_bytes(JPEG)
        self.sha256 = hashlib.sha256(JPEG).hexdigest()
        self.emit_hook: Callable[[JsonObject], None] | None = None
        self.tripped = False

    def _record(self, event: str) -> None:
        self.events.append(event)
        for prefix, seconds in self.delays.items():
            if event.startswith(prefix):
                self.now += seconds

    def emit(self, event: JsonObject) -> None:
        if self.emit_hook is not None:
            self.emit_hook(event)
        self.events.append("event:" + json.dumps(event, sort_keys=True))

    def request(self, left: float, token: str | None) -> TvRequest:
        return TvRequest(HOST, token, self.jpeg, self.sha256, self.now + left)

    def run(self, left: float = 40.0, token: str | None = None) -> JsonObject:
        return run_delivery(
            self.library,
            self.request(left, token),
            self.emit,
            guard_tripped=lambda: self.tripped,
            monotonic=lambda: self.now,
        )

    def markers(self) -> list[str]:
        found = []
        for event in self.events:
            if event.startswith("event:"):
                data = json.loads(event.removeprefix("event:"))
                if "marker" in data:
                    found.append(data["marker"])
        return found

    def calls(self, prefix: str) -> list[str]:
        return [event for event in self.events if event.startswith(prefix)]


def marker(name: str, content_id: str | None = None) -> str:
    return "event:" + json.dumps({"content_id": content_id, "marker": name}, sort_keys=True)


def token(value: str) -> str:
    return "event:" + json.dumps({"token": value})


# --------------------------------------------------------------- the sequence


def test_a_first_pairing_in_the_documented_order(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    assert rig.run() == {"status": "ok", "detail": "selected", "pairing": None}
    left = 40.0 - RESULT_MARGIN_S
    url = f"wss://{HOST}:{ART_PORT}/api/v2/channels/com.samsung.art-app"
    assert rig.events == [
        f"init:{HOST}:{ART_PORT}:{CONNECT_S}:0:{CLIENT_NAME}",
        f"supported:{CONNECT_S}",
        f"init:{HOST}:{ART_PORT}:{PAIRING_WAIT_S}:0:{CLIENT_NAME}",
        f"open:ok:token=None:timeout={PAIRING_WAIT_S}",
        f"handshake:{url}",
        token("12345678"),
        marker("connected"),
        f"api_version:{CONNECT_S}",
        marker("upload_started"),
        f"upload:{rig.sha256}:none:none:jpg:{left}",
        "upload:d2d",
        marker("uploaded", "MY_F0042"),
        f"select:MY_F0042:True:{left}",
        marker("selected"),
        "shutdown",
    ]


def test_the_stored_token_is_sent_and_an_unchanged_token_is_not_relayed(
    tmp_path: Path,
) -> None:
    rig = Rig(tmp_path, issue_token=SEED)
    assert rig.run(token=SEED)["status"] == "ok"
    assert f"open:ok:token={SEED}:timeout={PAIRING_WAIT_S}" in rig.events
    assert not [event for event in rig.events if '"token"' in event]


def test_a_changed_token_is_relayed_before_connected(tmp_path: Path) -> None:
    rig = Rig(tmp_path, issue_token=NEW)
    assert rig.run(token=SEED)["status"] == "ok"
    position = rig.events.index(token(NEW))
    assert rig.events[position + 1] == marker("connected")


def test_no_token_event_when_the_tv_sends_none(tmp_path: Path) -> None:
    rig = Rig(tmp_path, issue_token=None)
    assert rig.run()["status"] == "ok"
    assert not [event for event in rig.events if '"token"' in event]


@pytest.mark.parametrize("issued", ["abc", "to-ken-1234", "x" * 65])
def test_a_token_of_an_unexpected_form_is_not_relayed(
    tmp_path: Path, issued: str, caplog: pytest.LogCaptureFixture
) -> None:
    rig = Rig(tmp_path, issue_token=issued)
    with caplog.at_level(logging.WARNING, logger="frame_gallery.tv.worker"):
        assert rig.run()["status"] == "ok"
    assert not [event for event in rig.events if '"token"' in event]
    assert "unexpected form" in caplog.text


def test_both_tokens_are_registered_with_the_redactor(tmp_path: Path) -> None:
    redactor = Redactor()
    set_active_redactor(redactor)
    Rig(tmp_path, issue_token=NEW).run(token=SEED)
    assert redactor.redact(f"{SEED} {NEW}") == "[REDACTED] [REDACTED]"


def test_without_a_redactor_the_tokens_are_still_used(tmp_path: Path) -> None:
    set_active_redactor(None)
    rig = Rig(tmp_path, issue_token=NEW)
    assert rig.run(token=SEED)["status"] == "ok"
    assert token(NEW) in rig.events


def test_only_the_bytes_read_and_checked_first_are_uploaded(tmp_path: Path) -> None:
    """The file is replaced after its check, before the upload: the upload
    still carries the validated bytes, because the file is read only once
    (D-162 point 2)."""
    rig = Rig(tmp_path)
    real_class = rig.library.art_class

    def replacing(*args: object, **kwargs: object) -> object:
        art = real_class(*args, **kwargs)
        real_supported = art.supported

        def supported() -> bool:
            rig.jpeg.write_bytes(b"\xff\xd8" + b"z" * 1000 + b"\xff\xd9")  # same length
            return bool(real_supported())

        art.supported = supported
        return art

    rig.library = dataclasses.replace(rig.library, art_class=replacing)
    assert rig.run()["status"] == "ok"
    assert rig.calls("upload:")[0].startswith(f"upload:{rig.sha256}:")


def test_upload_started_is_written_before_the_upload_is_called(tmp_path: Path) -> None:
    """A failed marker write ends the task: nothing is uploaded (§12.1)."""
    rig = Rig(tmp_path)

    def broken_pipe(event: JsonObject) -> None:
        if event.get("marker") == "upload_started":
            raise BrokenPipeError(32, "parent gone")

    rig.emit_hook = broken_pipe
    with pytest.raises(BrokenPipeError):
        rig.run()
    assert rig.calls("upload") == []
    assert rig.events[-1] == "shutdown"


def test_a_failed_token_write_ends_the_task(tmp_path: Path) -> None:
    rig = Rig(tmp_path)

    def broken_pipe(event: JsonObject) -> None:
        if "token" in event:
            raise BrokenPipeError(32, "parent gone")

    rig.emit_hook = broken_pipe
    with pytest.raises(BrokenPipeError):
        rig.run()
    assert rig.markers() == []


# ------------------------------------------------------------- before the TV


def test_an_unreadable_delivery_file_contacts_no_tv(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.jpeg.unlink()
    assert rig.run() == {
        "status": "protocol",
        "detail": "the delivery file could not be read",
        "pairing": None,
    }
    assert rig.events == []


def test_a_delivery_file_with_other_bytes_contacts_no_tv(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.jpeg.write_bytes(JPEG + b"tampered")
    assert rig.run()["detail"] == "the delivery file is not the validated image"
    assert rig.events == []


def test_too_little_time_to_connect_and_upload_contacts_no_tv(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    outcome = rig.run(left=RESULT_MARGIN_S + CONNECT_S + UPLOAD_ALLOWANCE_S - 0.1)
    assert outcome["status"] == "insufficient_time"
    assert rig.events == []


# ------------------------------------------------------------ support, connect


@pytest.mark.parametrize(
    ("supported", "status"),
    [
        ("no", "unsupported"),
        ("unreachable", "unreachable"),
        ("timeout", "unreachable"),
        ("garbage", "protocol"),
        ("weird", "protocol"),
    ],
)
def test_the_capability_check(tmp_path: Path, supported: str, status: str) -> None:
    rig = Rig(tmp_path, supported=supported)
    assert rig.run()["status"] == status
    assert rig.markers() == []
    assert rig.calls("open") == []


@pytest.mark.parametrize(
    ("outcomes", "status", "pairing", "attempts"),
    [
        (["unauthorized"], "not_authorized", Pairing.REJECTED.value, 1),
        (["prompt_timeout"], "not_authorized", Pairing.PROMPT.value, 1),
        (["handshake_timeout"], "unreachable", None, 2),
        (["ready_timeout"], "unreachable", None, 2),
        (["close_frame"], "protocol", None, 2),
        (["malformed"], "protocol", None, 2),
        (["failure"], "unreachable", None, 2),
        (["refused"], "unreachable", None, 2),
    ],
)
def test_connection_failures_come_before_any_marker(
    tmp_path: Path, outcomes: list[str], status: str, pairing: str | None, attempts: int
) -> None:
    rig = Rig(tmp_path, open=outcomes)
    outcome = rig.run()
    assert (outcome["status"], outcome["pairing"]) == (status, pairing)
    assert rig.markers() == []
    assert len(rig.calls("open:")) == attempts


@pytest.mark.parametrize(
    "first", ["handshake_timeout", "ready_timeout", "close_frame", "failure", "refused"]
)
def test_a_failed_connection_is_tried_once_more_on_a_new_connection(
    tmp_path: Path, first: str
) -> None:
    """A second open() on the same object would wait again on the stale
    connection instead of connecting, so the retry makes a new object; the
    first connection is dropped before it (D-162)."""
    rig = Rig(tmp_path, open=[first, "ok"])
    assert rig.run()["status"] == "ok"
    inits = [i for i, e in enumerate(rig.events) if e.startswith(f"init:{HOST}:{ART_PORT}:20.0")]
    assert len(inits) == 2
    assert "open:stale" not in rig.events
    handshakes = [i for i, e in enumerate(rig.events) if e.startswith("handshake:wss")]
    if handshakes[0] < inits[1]:  # the first attempt got a connection: dropped first
        assert "shutdown" in rig.events[handshakes[0] : inits[1]]


def test_a_token_issued_before_a_failed_ready_wait_is_kept_and_used(tmp_path: Path) -> None:
    """The TV sends ms.channel.connect with a new token, then no ready: the
    token goes to the parent at once, and the retry sends it (R11)."""
    rig = Rig(tmp_path, open=["ready_timeout", "ok"], issue_token=NEW)
    assert rig.run()["status"] == "ok"
    opens = rig.calls("open:")
    assert opens[0].startswith("open:ready_timeout:token=None:")
    assert opens[1].startswith(f"open:ok:token={NEW}:")
    assert rig.events.count(token(NEW)) == 1
    assert rig.events.index(token(NEW)) < rig.events.index(opens[1])


def test_a_token_issued_before_a_failure_without_a_retry_is_still_sent(tmp_path: Path) -> None:
    rig = Rig(tmp_path, open=["ready_timeout", "prompt_timeout"], issue_token=NEW)
    outcome = rig.run()
    assert (outcome["status"], outcome["pairing"]) == ("not_authorized", "prompt")
    assert token(NEW) in rig.events


def test_a_pairing_timeout_is_never_retried(tmp_path: Path) -> None:
    rig = Rig(tmp_path, open=["prompt_timeout", "ok"])
    assert rig.run()["status"] == "not_authorized"
    assert len(rig.calls("open:")) == 1


def test_no_second_attempt_without_time_for_it(tmp_path: Path) -> None:
    rig = Rig(tmp_path, open=["refused", "ok"])
    rig.delays = {"handshake:refused": 5.0}
    outcome = rig.run(left=RESULT_MARGIN_S + UPLOAD_ALLOWANCE_S + CONNECT_S + 4.0)
    assert outcome["status"] == "unreachable"
    assert len(rig.calls("open:")) == 1


def test_a_slow_capability_check_can_leave_too_little_time_to_connect(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.delays = {"supported": 10.0}
    outcome = rig.run(left=RESULT_MARGIN_S + UPLOAD_ALLOWANCE_S + CONNECT_S + 5.0)
    assert outcome == {
        "status": "insufficient_time",
        "detail": "too little time is left to connect and upload",
        "pairing": None,
    }
    assert rig.calls("open:") == []


def test_the_pairing_wait_leaves_the_upload_allowance(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    left = RESULT_MARGIN_S + UPLOAD_ALLOWANCE_S + 12.0
    assert rig.run(left=left)["status"] == "ok"
    assert rig.calls("open:") == ["open:ok:token=None:timeout=12.0"]


# ------------------------------------------------------------ after connected


def test_too_little_time_after_pairing_uploads_nothing(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.delays = {"open:ok": 30.0}  # a long first-run pairing
    outcome = rig.run(left=40.0)
    assert outcome == {
        "status": "insufficient_time",
        "detail": "paired, but too little time is left to upload",
        "pairing": None,
    }
    assert rig.markers() == ["connected"]


@pytest.mark.parametrize(
    ("api_version", "status", "detail"),
    [
        ("0.97", "unsupported", "the TV's art API 0.97 is not supported yet"),
        ("error", "protocol", "the art API version was not readable (ResponseError)"),
        (
            "lost",
            "unreachable",
            "the art API version was not received (WebSocketConnectionClosedException)",
        ),
        ("timeout", "unreachable", "the art API version was not received (ConnectionFailure)"),
        ("4.x", "protocol", "the art API version is not valid"),
    ],
)
def test_the_api_version_is_checked_before_upload_started(
    tmp_path: Path, api_version: str, status: str, detail: str
) -> None:
    rig = Rig(tmp_path, api_version=api_version)
    assert rig.run() == {"status": status, "detail": detail, "pairing": None}
    assert rig.markers() == ["connected"]
    assert rig.calls("upload") == []


def test_the_api_version_is_asked_only_once(tmp_path: Path) -> None:
    """upload() asks for the version itself; the task answers from its own
    check, so the library never takes the 0.97 path or asks again."""
    rig = Rig(tmp_path)
    assert rig.run()["status"] == "ok"
    assert len(rig.calls("api_version")) == 1
    assert "upload:binary" not in rig.events


def test_the_fake_models_the_libraries_second_upload_on_0_97() -> None:
    """Why 0.97 is refused: after an error reply to the websocket upload, the
    library's upload() uploads the same bytes again (D-162)."""
    recorder = Recorder()
    script = Script(api_version="0.97", upload_097="error")
    art = make_art_class(script, recorder, make_websocket(recorder))(str(HOST))
    assert art.upload(JPEG) == "MY_F0042"
    assert recorder.events[-2:] == ["upload:binary", "upload:d2d"]


@pytest.mark.parametrize(
    ("upload", "status", "detail"),
    [
        (
            "error",
            "protocol",
            (
                "the TV reported an error during the upload (TV error send_image -1);"
                " it may hold the image"
            ),
        ),
        (
            "garbage",
            "protocol",
            "the TV reported an error during the upload; it may hold the image",
        ),
        (
            "lost",
            "unreachable",
            (
                "the upload was cut off (WebSocketConnectionClosedException);"
                " the TV may hold the image"
            ),
        ),
        (
            "timeout",
            "unreachable",
            "the upload was cut off (ConnectionFailure); the TV may hold the image",
        ),
        ("socket", "unreachable", "the upload was cut off (OSError); the TV may hold the image"),
        ("keyerror", "protocol", "unexpected upload reply (KeyError); the TV may hold the image"),
    ],
)
def test_upload_failures_keep_the_quarantine(
    tmp_path: Path, upload: str, status: str, detail: str
) -> None:
    """Every failure after upload_started ends there: the parent keeps the
    intent as uncertain (§12.4); a TV error reply is never an explicit refusal."""
    rig = Rig(tmp_path, upload=upload)
    assert rig.run() == {"status": status, "detail": detail, "pairing": None}
    assert rig.markers() == ["connected", "upload_started"]


def test_a_confirmed_upload_without_a_usable_id_is_still_recorded(tmp_path: Path) -> None:
    rig = Rig(tmp_path, upload="bad_id")
    assert rig.run() == {
        "status": "protocol",
        "detail": "the TV confirmed the upload without a usable content id",
        "pairing": None,
    }
    assert rig.events[-2:] == [marker("uploaded"), "shutdown"]
    assert rig.calls("select") == []


@pytest.mark.parametrize(
    ("select", "status", "detail"),
    [
        (
            "refused",
            "refused",
            "the TV refused to show the uploaded artwork (TV error select_image -11)",
        ),
        ("garbage", "protocol", "unexpected selection reply (ResponseError)"),
        ("lost", "unreachable", "the selection was cut off (WebSocketConnectionClosedException)"),
        ("socket", "unreachable", "the selection was cut off (OSError)"),
        ("keyerror", "protocol", "unexpected selection reply (KeyError)"),
    ],
)
def test_selection_failures_follow_the_upload(
    tmp_path: Path, select: str, status: str, detail: str
) -> None:
    rig = Rig(tmp_path, select=select)
    assert rig.run() == {"status": status, "detail": detail, "pairing": None}
    assert rig.markers() == ["connected", "upload_started", "uploaded"]


def test_each_wait_follows_the_remaining_time(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.delays = {"api_version": 2.0, "upload:d2d": 6.0}
    assert rig.run(left=40.0)["status"] == "ok"
    left = 40.0 - RESULT_MARGIN_S
    assert rig.calls("upload:")[0].endswith(f":{left - 2.0}")
    assert rig.calls("select")[0].endswith(f":{left - 8.0}")


def test_no_wait_is_shorter_than_the_minimum(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.delays = {"upload:d2d": 60.0}
    assert rig.run()["status"] == "ok"
    assert rig.calls("select")[0].endswith(":0.5")


def test_the_connection_timeout_is_set_too(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[float | None] = []
    real = FakeConnection.settimeout

    def spy(self: FakeConnection, timeout: float | None) -> None:
        seen.append(timeout)
        real(self, timeout)

    monkeypatch.setattr(FakeConnection, "settimeout", spy)
    rig = Rig(tmp_path)
    rig.run()
    left = 40.0 - RESULT_MARGIN_S
    assert seen == [PAIRING_WAIT_S, CONNECT_S, left, left]


def test_a_failing_shutdown_is_ignored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(_self: FakeConnection) -> None:
        raise OSError(9, "Bad file descriptor")

    monkeypatch.setattr(FakeConnection, "shutdown", broken)
    assert Rig(tmp_path).run()["status"] == "ok"


def test_the_defaults_are_the_real_clock_and_no_guard(tmp_path: Path) -> None:
    rig = Rig(tmp_path, supported="unreachable")
    request = TvRequest(HOST, None, rig.jpeg, rig.sha256, time.monotonic() + 40.0)
    assert run_delivery(rig.library, request, rig.emit)["status"] == "unreachable"


def test_the_handshake_wrapper_is_removed_afterwards(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    original = rig.library.websocket.create_connection
    rig.run()
    assert rig.library.websocket.create_connection is original


# --------------------------------------------------------------- the guard


@pytest.mark.parametrize(
    "script",
    [
        {"supported": "unreachable"},
        {"open": ["refused"]},
        {"api_version": "lost"},
        {"upload": "socket"},
        {"select": "socket"},
    ],
)
def test_a_refusal_of_the_connect_guard_is_a_protocol_failure(
    tmp_path: Path, script: dict[str, object]
) -> None:
    """The libraries turn the guard's refusal into "unreachable"; the task
    reports it as what it is."""
    rig = Rig(tmp_path, **script)
    rig.tripped = True
    assert rig.run() == {
        "status": "protocol",
        "detail": "the worker's connect guard refused an address other than the TV's",
        "pairing": None,
    }


class TestConnectGuard:
    """In the test session the H2 guard already blocks the network, so a
    permitted call reaches the H2 blocker instead of a real socket."""

    @pytest.fixture
    def guard(self) -> Iterator[ConnectGuard]:
        installed = install_connect_guard(HOST)
        try:
            yield installed
        finally:
            installed.undo()

    def test_only_the_television_can_be_reached(self, guard: ConnectGuard) -> None:
        with socket.socket() as sock:
            with pytest.raises(GuardViolation, match="only the TV"):
                sock.connect(("192.0.2.99", 8002))
            assert guard.blocked == ["192.0.2.99:8002"]
            assert guard.tripped()
            with pytest.raises(GuardViolation):
                sock.connect_ex(("192.0.2.99", 8002))
            with pytest.raises(GuardViolation):
                sock.connect("/tmp/some.sock")  # noqa: S108 - not a real path
            with pytest.raises(NetworkBlockedError):
                sock.connect((str(HOST), 8002))  # passed on
            with pytest.raises(NetworkBlockedError):
                sock.connect_ex((str(HOST), 8002))
        assert guard.blocked[-1] == "an address"

    def test_a_violation_is_no_os_error(self) -> None:
        assert not issubclass(GuardViolation, OSError)

    def test_names_are_not_resolved(self, guard: ConnectGuard) -> None:
        with pytest.raises(GuardViolation):
            socket.getaddrinfo("example.org", 443)
        with pytest.raises(NetworkBlockedError):
            socket.getaddrinfo(str(HOST), 8002)  # the literal is passed on
        for name in ("gethostbyname", "gethostbyname_ex", "gethostbyaddr", "getnameinfo"):
            with pytest.raises(GuardViolation):
                getattr(socket, name)("example.org")
        assert guard.blocked == ["a name lookup"] * 5

    def test_it_can_be_undone(self) -> None:
        guard = install_connect_guard(HOST)
        guard.undo()
        with socket.socket() as sock, pytest.raises(NetworkBlockedError):
            sock.connect(("192.0.2.99", 8002))  # the H2 blocker is back

    @pytest.mark.parametrize(
        ("before", "during"),
        [(None, CONNECT_S), (30.0, CONNECT_S), (2.0, 2.0), (0.0, 0.0), (CONNECT_S, CONNECT_S)],
    )
    def test_every_connect_is_bounded(
        self, monkeypatch: pytest.MonkeyPatch, before: float | None, during: float
    ) -> None:
        seen: list[float | None] = []

        def spy(self: socket.socket, _address: object) -> None:
            seen.append(self.gettimeout())

        def spy_ex(self: socket.socket, _address: object) -> int:
            seen.append(self.gettimeout())
            return 0

        monkeypatch.setattr(socket.socket, "connect", spy)
        monkeypatch.setattr(socket.socket, "connect_ex", spy_ex)
        guard = install_connect_guard(HOST)
        try:
            with socket.socket() as sock:
                sock.settimeout(before)
                sock.connect((str(HOST), 8002))
                assert sock.connect_ex((str(HOST), 8002)) == 0
                assert sock.gettimeout() == before
        finally:
            guard.undo()
        assert seen == [during, during]


# --------------------------------------------------------------- the pieces


class TestRequest:
    def payload(self, **changes: object) -> dict[str, object]:
        base: dict[str, object] = {
            "host": str(HOST),
            "token": SEED,
            "jpeg_path": "/tmp/out/delivery-0.jpg",  # noqa: S108 - a test value only
            "jpeg_sha256": "a" * 64,
            "deadline": 1234.5,
        }
        base.update(changes)
        return base

    @pytest.mark.parametrize("token_value", [SEED, None])
    def test_round_trip(self, token_value: str | None) -> None:
        payload = self.payload(token=token_value)
        request = TvRequest.from_json(payload)  # type: ignore[arg-type]
        assert request.to_json() == payload

    def test_an_integer_deadline_is_accepted(self) -> None:
        assert TvRequest.from_json(self.payload(deadline=100)).deadline == 100.0  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "changes",
        [
            {"host": "8.8.8.8"},
            {"host": "tv.local"},
            {"host": 1},
            {"token": "abc"},
            {"token": 12345678},
            {"token": "to-ken-1234"},
            {"jpeg_path": 5},
            {"jpeg_sha256": "A" * 64},
            {"jpeg_sha256": "a" * 63},
            {"deadline": True},
            {"deadline": "10"},
            {"deadline": math.nan},
            {"deadline": math.inf},
            {"extra": 1},
        ],
    )
    def test_invalid_requests(self, changes: dict[str, object]) -> None:
        with pytest.raises(ValueError, match=r"."):
            TvRequest.from_json(self.payload(**changes))  # type: ignore[arg-type]

    def test_a_missing_field_is_invalid(self) -> None:
        payload = self.payload()
        del payload["token"]
        with pytest.raises(ValueError, match="invalid television request"):
            TvRequest.from_json(payload)  # type: ignore[arg-type]


class TestDeliveryFile:
    SHA = hashlib.sha256(JPEG).hexdigest()

    def test_a_regular_file_with_the_hash_is_read(self, tmp_path: Path) -> None:
        (tmp_path / "d.jpg").write_bytes(JPEG)
        assert read_delivery(tmp_path / "d.jpg", self.SHA) == JPEG

    def test_other_bytes_are_refused(self, tmp_path: Path) -> None:
        (tmp_path / "d.jpg").write_bytes(JPEG[:-1])
        with pytest.raises(ValueError, match="not the validated image"):
            read_delivery(tmp_path / "d.jpg", self.SHA)

    def test_a_link_is_refused(self, tmp_path: Path) -> None:
        (tmp_path / "real.jpg").write_bytes(JPEG)
        (tmp_path / "d.jpg").symlink_to(tmp_path / "real.jpg")
        with pytest.raises(OSError, match=r"."):
            read_delivery(tmp_path / "d.jpg", self.SHA)

    def test_a_directory_is_refused(self, tmp_path: Path) -> None:
        (tmp_path / "d.jpg").mkdir()
        with pytest.raises(OSError, match="expected size"):
            read_delivery(tmp_path / "d.jpg", self.SHA)

    @pytest.mark.parametrize("size", [0, MAX_OUTPUT_BYTES + 1])
    def test_sizes_out_of_range_are_refused(self, tmp_path: Path, size: int) -> None:
        with (tmp_path / "d.jpg").open("wb") as file:
            file.truncate(size)
        with pytest.raises(OSError, match="expected size"):
            read_delivery(tmp_path / "d.jpg", self.SHA)

    def test_a_file_that_grows_while_read_is_refused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with (tmp_path / "d.jpg").open("wb") as file:
            file.truncate(MAX_OUTPUT_BYTES + 1)
        real_fstat = os.fstat

        class Small:
            def __init__(self, info: os.stat_result) -> None:
                self.st_mode = info.st_mode
                self.st_size = 10

        monkeypatch.setattr(os, "fstat", lambda fd: Small(real_fstat(fd)))
        with pytest.raises(ValueError, match="not the validated image"):
            read_delivery(tmp_path / "d.jpg", self.SHA)


class TestInstalledLibrary:
    def test_the_real_library_surface_is_what_the_task_expects(self) -> None:
        library = load_library()
        assert library.art_class is samsungtvws.SamsungTVArt
        assert callable(library.websocket.create_connection)
        assert issubclass(library.unauthorized, library.transport_errors)
        assert not issubclass(library.websocket_timeout, OSError)
        assert issubclass(library.websocket_timeout, library.transport_errors)
        assert not issubclass(library.response_error, library.transport_errors)

    def test_the_version_is_the_pinned_one(self) -> None:
        assert version("samsungtvws") == "3.0.6"

    @pytest.mark.parametrize(
        "method",
        ["__init__", "supported", "open", "get_api_version", "upload", "select_image", "close"],
    )
    def test_the_fake_has_the_installed_signatures(self, method: str) -> None:
        """Names, kinds, and defaults; a call the real library would reject
        fails against the fake too."""
        fake = make_art_class(Script(), Recorder(), make_websocket(Recorder()))

        def shape(function: object) -> list[tuple[str, object, object]]:
            parameters = inspect.signature(function).parameters.values()  # type: ignore[arg-type]
            return [(p.name, p.kind, p.default) for p in parameters]

        assert shape(getattr(fake, method)) == shape(getattr(samsungtvws.SamsungTVArt, method))

    def test_the_select_refusal_text_is_the_librarys(self) -> None:
        """The TV's own error reply is recognised by the library's wording."""
        source = inspect.getsource(samsungtvws.art.art.SamsungTVArt._wait_for_d2d)
        assert "request failed with error number" in source


def test_the_library_is_kept_quiet() -> None:
    with warnings.catch_warnings():
        quiet_library()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("default")
            quiet_library()
            warnings.warn("Unverified HTTPS request is being made to host", stacklevel=1)
        assert caught == []
    for name in ("samsungtvws", "websocket", "urllib3", "requests"):
        assert logging.getLogger(name).level == logging.WARNING


def test_the_module_logger() -> None:
    assert samsung_task._log.name == "frame_gallery.tv.worker"


def test_the_worker_entry_installs_the_guard_before_the_library(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rig = Rig(tmp_path)
    order: list[str] = []
    guard = ConnectGuard([], lambda: None)

    def fake_guard(host: IPv4Address) -> ConnectGuard:
        order.append(f"guard:{host}")
        return guard

    def fake_load() -> object:
        order.append("library")
        return rig.library

    monkeypatch.setattr(samsung_task, "install_connect_guard", fake_guard)
    monkeypatch.setattr(samsung_task, "load_library", fake_load)
    payload = TvRequest(HOST, None, rig.jpeg, rig.sha256, time.monotonic() + 40.0).to_json()
    assert samsung_task.deliver_task(payload, rig.emit)["status"] == "ok"
    assert order == [f"guard:{HOST}", "library"]
    guard.blocked.append("x")
    rig2 = Rig(tmp_path, supported="unreachable")
    monkeypatch.setattr(samsung_task, "load_library", lambda: rig2.library)
    assert samsung_task.deliver_task(payload, rig2.emit)["status"] == "protocol"


class TestHandshakes:
    """The create_connection wrapper, driven directly (D-162 points 4 and 5)."""

    class Connection:
        def __init__(self) -> None:
            self.timeouts: list[float | None] = []
            self.reads = 0

        def settimeout(self, timeout: float | None) -> None:
            self.timeouts.append(timeout)

        def recv(self) -> str:
            self.reads += 1
            return "frame"

        def shutdown(self) -> None:
            raise OSError(9, "already closed")

    def wrapper(self, now: list[float]) -> tuple[samsung_task._Handshakes, SimpleNamespace]:
        made: list[tuple[object, object]] = []

        def create_connection(url: object, timeout: object = None, **_: object) -> object:
            made.append((url, timeout))
            return TestHandshakes.Connection()

        module = SimpleNamespace(create_connection=create_connection, made=made)
        handshakes = samsung_task._Handshakes(module, TimeoutError, lambda: now[0])
        return handshakes, module

    def test_without_a_deadline_nothing_is_bounded(self) -> None:
        handshakes, module = self.wrapper([100.0])
        connection = module.create_connection("wss://tv", 20.0)
        assert module.made == [("wss://tv", 20.0)]
        assert connection.recv() == "frame"
        assert connection.timeouts == []
        assert handshakes.count == 1

    def test_with_a_deadline_the_connect_and_every_read_are_bounded(self) -> None:
        now = [100.0]
        handshakes, module = self.wrapper(now)
        handshakes.deadline = 103.0
        connection = module.create_connection("wss://tv", 20.0)
        assert module.made == [("wss://tv", 3.0)]  # clamped to the time left
        now[0] = 102.0
        assert connection.recv() == "frame"
        assert connection.timeouts == [1.0]
        now[0] = 103.5
        with pytest.raises(TimeoutError, match="the pairing wait ended"):
            connection.recv()
        handshakes.settle()
        assert connection.recv() == "frame"  # its own time-out again
        assert handshakes.deadline is None

    def test_a_missing_time_out_becomes_the_time_left(self) -> None:
        handshakes, module = self.wrapper([100.0])
        handshakes.deadline = 100.1
        module.create_connection("wss://tv")
        assert module.made == [("wss://tv", samsung_task.MIN_WAIT_S)]

    def test_every_connection_is_dropped_once(self) -> None:
        handshakes, module = self.wrapper([100.0])
        module.create_connection("wss://tv", 1.0)
        module.create_connection("wss://tv", 1.0)
        handshakes.drop_all()  # a failing shutdown is ignored
        handshakes.drop_all()
        handshakes.undo()
        assert module.create_connection is not handshakes._create_connection
