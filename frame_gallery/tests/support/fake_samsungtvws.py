"""A stand-in for the art surface of the installed ``samsungtvws`` 3.0.6.

It models only what the installed distribution shows (D-161), and the
behaviour of it that the television task depends on (D-162):

* the ``SamsungTVArt`` constructor and the methods ``supported``, ``open``,
  ``get_api_version``, ``upload``, ``select_image`` and ``close``, with the
  installed signatures (a conformance test compares them);
* ``open()`` opens the websocket through ``websocket.create_connection``,
  looked up at call time on the module it was given, sends the token it holds,
  and keeps a token the television issues in ``token``; after a failure that
  follows the handshake, a second ``open()`` on the same object returns the
  stale connection, as the library does;
* ``upload()`` asks ``self.get_api_version()`` first and, on 0.97, falls back
  to a second upload after an error reply to the first;
* the library's own exception classes, and those of ``websocket-client`` and
  ``requests``, with the library's messages.

A test scripts it through a :class:`Script`; every call is appended to a call
log, so a test can check the order of events, for example that the
``upload_started`` marker was written before ``upload`` was called. Nothing
here opens a socket.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import requests
import websocket
from samsungtvws import exceptions

from frame_gallery.tv.samsung_task import TvLibrary

LIBRARY_SENTINEL = "fake-samsungtvws-3.0.6"
TV_ERROR_SEND = "`send_image` request failed with error number -1"
TV_ERROR_SELECT = "`select_image` request failed with error number -11"
PARSE_FAILURE = "Failed to parse response from TV. Maybe feature not supported on this model"


@dataclass
class Script:
    """What the fake television does. Every step defaults to success."""

    supported: str = "yes"
    """``yes``, ``no``, ``unreachable`` (``HttpApiError``), ``timeout``
    (``requests.ReadTimeout``), ``garbage`` (``ResponseError``), ``weird``
    (``AttributeError``, a JSON reply that is not an object)."""

    open: list[str] = field(default_factory=lambda: ["ok"])
    """One outcome per ``open()`` call; the last one repeats. ``ok``,
    ``unauthorized``, ``prompt_timeout`` (a time-out after the handshake),
    ``handshake_timeout`` (a time-out during it), ``ready_timeout`` (the
    connect event arrived, the ready event did not), ``close_frame``
    (``ResponseError``), ``refused`` (``ConnectionRefusedError``), ``failure``
    (``ConnectionFailure``)."""

    issue_token: str | None = "12345678"  # noqa: S105 - a fake pairing token
    """The token the television sends on connect; ``None`` sends none."""

    api_version: str = "4.3.4.0"
    """The version, or ``error`` (``ResponseError``), ``lost``, ``timeout``."""

    upload: str = "ok"
    """``ok``, ``error`` (the TV's error reply), ``garbage`` (an unparsable
    reply), ``lost`` (``WebSocketConnectionClosedException``), ``timeout``
    (``ConnectionFailure`` for a websocket time-out), ``socket`` (``OSError``),
    ``hang`` (sleeps ``hang_s``), ``bad_id`` (returns an invalid id),
    ``keyerror`` (a malformed reply)."""

    upload_097: str = "ok"
    """On API 0.97: ``ok``, or ``error`` (the library then uploads again)."""

    content_id: str = "MY_F0042"
    select: str = "ok"
    """``ok``, ``refused`` (the TV's error reply), ``garbage``, ``lost``,
    ``socket``, ``hang``, ``keyerror``."""

    hang_s: float = 30.0

    @classmethod
    def load(cls, path: Path) -> Script:
        data = json.loads(path.read_text()) if path.exists() else {}
        return cls(**data)


class Recorder:
    """Appends each event to a list and, when given a path, to a file."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.events: list[str] = []

    def __call__(self, event: str) -> None:
        self.events.append(event)
        if self.path is not None:
            self.path.write_text(json.dumps(self.events))


class FakeConnection:
    def __init__(self, record: Callable[[str], None]) -> None:
        self._record = record
        self.timeout: float | None = None

    def settimeout(self, timeout: float | None) -> None:
        self.timeout = timeout

    def shutdown(self) -> None:
        self._record("shutdown")


def make_websocket(record: Callable[[str], None]) -> SimpleNamespace:
    """A stand-in for the ``websocket`` module's ``create_connection``; the
    fake ``open()`` sets ``next_outcome`` before it calls it."""
    module = SimpleNamespace(next_outcome="ok")

    def create_connection(url: str, timeout: float | None = None, **_options: Any) -> Any:
        outcome = module.next_outcome
        if outcome == "handshake_timeout":
            record("handshake:timeout")
            raise websocket.WebSocketTimeoutException("Connection timed out")
        if outcome == "refused":
            record("handshake:refused")
            raise ConnectionRefusedError(61, "Connection refused")
        record(f"handshake:{url}")
        connection = FakeConnection(record)
        connection.settimeout(timeout)
        return connection

    module.create_connection = create_connection
    return module


def make_art_class(script: Script, record: Callable[[str], None], ws: Any) -> type[Any]:
    """A ``SamsungTVArt`` stand-in bound to ``script`` and the ``ws`` module."""

    class FakeArt:
        def __init__(
            self,
            host: str,
            token: str | None = None,
            token_file: str | None = None,
            port: int = 8001,
            timeout: float | None = None,
            key_press_delay: float = 1,
            name: str = "SamsungTvRemote",
        ) -> None:
            self.host = host
            self.token = token
            self.token_file = token_file
            self.port = port
            self.timeout = None if timeout == 0 else timeout
            self.key_press_delay = key_press_delay
            self.name = name
            self.connection: FakeConnection | None = None
            record(f"init:{host}:{port}:{timeout}:{key_press_delay}:{name}")

        def supported(self) -> bool:
            record(f"supported:{self.timeout}")
            outcome = script.supported
            if outcome == "unreachable":
                raise exceptions.HttpApiError(
                    "TV unreachable or feature not supported on this model."
                )
            if outcome == "timeout":
                raise requests.ReadTimeout("read timed out")
            if outcome == "garbage":
                raise exceptions.ResponseError(PARSE_FAILURE)
            if outcome == "weird":
                raise AttributeError("'list' object has no attribute 'get'")
            return outcome == "yes"

        def open(self) -> FakeConnection:
            if self.connection:
                # someone else already created a new connection (the library's
                # base class), and the art channel waits for "ready" again.
                record("open:stale")
                raise exceptions.ConnectionFailure("Websocket Time out: timed out")
            outcome = script.open.pop(0) if len(script.open) > 1 else script.open[0]
            record(f"open:{outcome}:token={self.token}:timeout={self.timeout}")
            ws.next_outcome = outcome
            connection: FakeConnection = ws.create_connection(
                f"wss://{self.host}:{self.port}/api/v2/channels/com.samsung.art-app",
                self.timeout,
                sslopt={},
                connection="Connection: Upgrade",
            )
            if outcome == "unauthorized":
                raise exceptions.UnauthorizedError({"event": "ms.channel.unauthorized"})
            if outcome == "prompt_timeout":
                raise websocket.WebSocketTimeoutException("Connection timed out")
            if outcome == "close_frame":
                raise exceptions.ResponseError(PARSE_FAILURE)
            if outcome == "failure":
                raise exceptions.ConnectionFailure({"event": "unexpected"})
            if script.issue_token is not None:
                self.token = script.issue_token
            self.connection = connection
            if outcome == "ready_timeout":
                raise exceptions.ConnectionFailure("Websocket Time out: timed out")
            return connection

        def get_api_version(self) -> str:
            record(f"api_version:{self.timeout}")
            outcome = script.api_version
            if outcome == "error":
                raise exceptions.ResponseError("Missing 'version' in response")
            if outcome == "lost":
                raise websocket.WebSocketConnectionClosedException("socket is already closed.")
            if outcome == "timeout":
                raise exceptions.ConnectionFailure("Websocket Time out: timed out")
            return outcome

        def upload(
            self,
            file: bytes,
            matte: str = "shadowbox_polar",
            portrait_matte: str = "shadowbox_polar",
            file_type: str = "png",
            date: str | None = None,
        ) -> str:
            record(f"upload:{len(file)}:{matte}:{portrait_matte}:{file_type}:{self.timeout}")
            try:
                if self.get_api_version() == "0.97":
                    record("upload:binary")
                    if script.upload_097 == "error":
                        raise exceptions.ResponseError(TV_ERROR_SEND)
                    return script.content_id
            except exceptions.ResponseError:
                pass
            record("upload:d2d")
            return self._step(script.upload, script.content_id, TV_ERROR_SEND)

        def select_image(
            self,
            content_id: str,
            category: str | None = None,
            show: bool = True,
        ) -> dict[str, str]:
            record(f"select:{content_id}:{show}:{self.timeout}")
            self._step(script.select, content_id, TV_ERROR_SELECT)
            return {"event": "image_selected"}

        def close(self) -> None:
            record("close")
            self.connection = None

        def _step(self, outcome: str, content_id: str, tv_error: str) -> str:
            if outcome in ("error", "refused"):
                raise exceptions.ResponseError(tv_error)
            if outcome == "garbage":
                raise exceptions.ResponseError(PARSE_FAILURE)
            if outcome == "lost":
                raise websocket.WebSocketConnectionClosedException("socket is already closed.")
            if outcome == "timeout":
                raise exceptions.ConnectionFailure("Websocket Time out: timed out")
            if outcome == "socket":
                raise OSError(104, "Connection reset by peer")
            if outcome == "hang":
                time.sleep(script.hang_s)
            if outcome == "bad_id":
                return "not a content id!"
            if outcome == "keyerror":
                raise KeyError("content_id")
            return content_id

    return FakeArt


def make_library(script: Script, record: Callable[[str], None]) -> TvLibrary:
    """The task's view of the library, over the fake."""
    ws = make_websocket(record)
    return TvLibrary(
        art_class=make_art_class(script, record, ws),
        websocket=ws,
        unauthorized=exceptions.UnauthorizedError,
        response_error=exceptions.ResponseError,
        websocket_timeout=websocket.WebSocketTimeoutException,
        transport_errors=(
            OSError,
            websocket.WebSocketException,
            requests.RequestException,
            exceptions.HttpApiError,
            exceptions.ConnectionFailure,
        ),
    )
