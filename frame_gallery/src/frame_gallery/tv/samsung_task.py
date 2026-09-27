"""The television worker task: connect, upload, and select (§12.1, §12.2, D-161, D-162).

This module runs only inside the isolated television worker. It is the only
module that imports ``samsungtvws`` (D-107), and it does so only in
:func:`load_library`, so the delivery logic below can be tested in-process
with a stand-in of the library.

One delivery, in order:

1. The JPEG is read once and must have the parent's SHA-256; only these
   bytes are uploaded. If less time is left than a connection and the
   upload allowance need, the result is ``insufficient_time``.
2. ``supported()`` asks the television's REST service whether it is a Frame
   TV. No answer is ``unreachable``; a clear "no" is ``unsupported``.
3. ``open()`` connects to the art channel on port 8002, with the stored
   token if there is one. A rejection is ``not_authorized`` (``rejected``).
   A time-out after the websocket handshake completed is a prompt that was
   not accepted: ``not_authorized`` (``prompt``), never retried (D-115). Any
   other failure is retried once, on a new connection, if time allows. A
   token the television issued is sent to the parent before ``connected``.
4. ``connected``. The art API version is read; version 0.97, whose upload
   path the library may repeat internally, is ``unsupported`` (D-162). The
   version is pinned on the connection, so ``upload()`` does not ask again.
   If less than the upload allowance is left: ``insufficient_time``.
5. ``upload_started`` is emitted, and its write has completed, **before**
   ``upload()`` is called: a missing marker proves that nothing was uploaded.
6. ``upload()`` returns the content ID; ``uploaded`` is emitted with it, or
   without it if it does not have the strict form (the result is then
   ``protocol``: the upload is recorded, but cannot be selected).
7. ``select_image()`` shows it; ``selected`` is emitted.

After ``upload_started``, every failure keeps the upload quarantine: the
installed library does not tell a refusal before the transfer from one after
it, so a television error reply is ``protocol``, never ``refused``. After
``uploaded``, only the television's own error reply to the selection is
``refused``. A failure to emit an event is never caught: the task ends at
once, so nothing is uploaded or selected that the parent could not record.
"""

from __future__ import annotations

import contextlib
import errno
import hashlib
import logging
import os
import re
import stat
import time
import warnings
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from ipaddress import IPv4Address
from pathlib import Path
from typing import Any, Final

from frame_gallery.imaging.contract import MAX_OUTPUT_BYTES
from frame_gallery.isolation.executor import EventSink, JsonObject
from frame_gallery.logs.redact import active_redactor
from frame_gallery.tv.contract import (
    TOKEN_PATTERN,
    Pairing,
    TvRequest,
    marker_event,
    result,
    token_event,
)
from frame_gallery.tv.port import CONTENT_ID_PATTERN, DeliveryStatus, Marker

ART_PORT: Final = 8002
"""The TLS art channel, which carries the pairing token."""

CLIENT_NAME: Final = "frame_gallery"
"""The name the television shows for the paired client (D-138)."""

CONNECT_S: Final = 5.0
"""Every TCP connect, and the REST check's connect and read (§7.2)."""

PAIRING_WAIT_S: Final = 20.0
UPLOAD_ALLOWANCE_S: Final = 15.0
"""Time kept for the upload and the selection (§12.1). Proposed; measured in Phase 8."""

RESULT_MARGIN_S: Final = 1.0
"""Kept before the deadline to send the result ahead of the parent's kill timer."""

MIN_WAIT_S: Final = 0.5
"""The library treats a time-out of 0 as none at all; no wait is shorter than this."""

UNSUPPORTED_API_VERSIONS: Final = frozenset({"0.97"})
"""On 0.97 the library's ``upload()`` falls back to a second, socket-based
upload of the same image after an error reply to the first (D-162)."""

_TV_ERROR: Final = re.compile(r"`([A-Za-z_]{1,40})` request failed with error number (-?\w{1,12})")
"""The library's text for the television's own error reply (3.0.6)."""

_API_VERSION: Final = re.compile(r"[0-9][0-9.]{0,15}")
_READ_FLAGS: Final = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
_LIBRARY_LOGGERS: Final = ("samsungtvws", "websocket", "urllib3", "requests")

_log = logging.getLogger("frame_gallery.tv.worker")


@dataclass(frozen=True, slots=True)
class TvLibrary:
    """What the task needs of the installed library (injectable for tests)."""

    art_class: Callable[..., Any]
    websocket: Any
    """The module whose ``create_connection`` opens the art channel; the task
    wraps it to learn whether the websocket handshake completed."""

    unauthorized: type[BaseException]
    response_error: type[BaseException]
    websocket_timeout: type[BaseException]
    transport_errors: tuple[type[BaseException], ...]
    """Failures of the connection itself: sockets, the websocket, HTTP, and
    the library's own connection failures."""


def load_library() -> TvLibrary:
    """Import the installed library (the only import of it, D-107)."""
    import requests  # noqa: PLC0415 - imported only inside the worker
    import samsungtvws  # noqa: PLC0415
    import websocket  # noqa: PLC0415
    from samsungtvws import exceptions  # noqa: PLC0415

    return TvLibrary(
        art_class=samsungtvws.SamsungTVArt,
        websocket=websocket,
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


def read_delivery(path: Path, sha256: str) -> bytes:
    """The parent-validated JPEG, read once without following a link.

    Raises ``OSError`` if it cannot be read, and ``ValueError`` if its bytes
    are not the ones the parent validated.
    """
    fd = os.open(path, _READ_FLAGS)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_OUTPUT_BYTES:
            raise OSError(errno.EINVAL, "the delivery file is not a JPEG of the expected size")
        with os.fdopen(fd, "rb", closefd=False) as file:
            data = file.read(MAX_OUTPUT_BYTES + 1)
    finally:
        os.close(fd)
    if len(data) > MAX_OUTPUT_BYTES or hashlib.sha256(data).hexdigest() != sha256:
        msg = "the delivery file is not the validated image"
        raise ValueError(msg)
    return data


def _never() -> bool:
    return False


def _register_secret(token: str) -> None:
    redactor = active_redactor()
    if redactor is not None:
        redactor.add_secret(token)


class _Clock:
    def __init__(self, deadline: float, monotonic: Callable[[], float]) -> None:
        self._monotonic = monotonic
        self._deadline = deadline - RESULT_MARGIN_S

    def left(self) -> float:
        return self._deadline - self._monotonic()


class _Handshakes:
    """Counts completed websocket handshakes of the art channel (D-162).

    ``websocket-client`` raises the same time-out when the television never
    answers the upgrade and when it answers but then waits for the user; only
    the second is a pairing prompt. ``samsungtvws`` looks up
    ``websocket.create_connection`` at call time, so a wrapper sees it return.
    """

    def __init__(self, module: Any) -> None:
        self._module = module
        self._real = module.create_connection
        self.count = 0
        module.create_connection = self._create_connection

    def _create_connection(self, *args: Any, **kwargs: Any) -> Any:
        connection = self._real(*args, **kwargs)
        self.count += 1
        return connection

    def undo(self) -> None:
        self._module.create_connection = self._real


class _Finished(Exception):
    """Ends the delivery early with a result."""

    def __init__(self, outcome: JsonObject) -> None:
        super().__init__(outcome.get("status"))
        self.outcome = outcome


def _finished(status: DeliveryStatus, detail: str, pairing: Pairing | None = None) -> _Finished:
    return _Finished(result(status, detail, pairing))


def run_delivery(
    library: TvLibrary,
    request: TvRequest,
    emit: EventSink,
    *,
    guard_tripped: Callable[[], bool] = _never,
    monotonic: Callable[[], float] = time.monotonic,
) -> JsonObject:
    """One delivery; see the module docstring. Returns a result object.

    ``guard_tripped`` tells whether the connect guard refused an address;
    such a failure is ``protocol``, not a television that is off.
    """
    if request.token is not None:
        _register_secret(request.token)
    handshakes = _Handshakes(library.websocket)
    delivery = _Delivery(
        library, request, emit, handshakes, guard_tripped, _Clock(request.deadline, monotonic)
    )
    try:
        return delivery.run()
    finally:
        delivery.abandon()
        handshakes.undo()


@dataclass
class _Delivery:
    library: TvLibrary
    request: TvRequest
    emit: EventSink
    handshakes: _Handshakes
    guard_tripped: Callable[[], bool]
    clock: _Clock
    art: Any = field(default=None)

    def run(self) -> JsonObject:
        # A failure to emit an event is not a _Finished: it ends the task at once.
        try:
            data = self._verified_delivery()
            self._check_support()
            self._connect()
            self.emit(marker_event(Marker.CONNECTED))
            self._pin_api_version()
            if self.clock.left() < UPLOAD_ALLOWANCE_S:
                raise _finished(
                    DeliveryStatus.INSUFFICIENT_TIME,
                    "paired, but too little time is left to upload",
                )
            self.emit(marker_event(Marker.UPLOAD_STARTED))
            content_id = self._upload(data)
            self.emit(marker_event(Marker.UPLOADED, content_id))
            if content_id is None:
                raise _finished(
                    DeliveryStatus.PROTOCOL,
                    "the TV confirmed the upload without a usable content id",
                )
            self._select(content_id)
        except _Finished as finished:
            return finished.outcome
        self.emit(marker_event(Marker.SELECTED))
        return result(DeliveryStatus.OK, "selected")

    # ------------------------------------------------------------ connection

    def _new_art(self, timeout: float) -> Any:
        self.abandon()
        self.art = self.library.art_class(
            str(self.request.host),
            token=self.request.token,
            port=ART_PORT,
            timeout=max(MIN_WAIT_S, timeout),
            key_press_delay=0,
            name=CLIENT_NAME,
        )
        return self.art

    def abandon(self) -> None:
        """Drop the connection without the websocket close handshake, which
        waits up to 3 s for the television; the worker exits anyway."""
        art, self.art = self.art, None
        shutdown = getattr(getattr(art, "connection", None), "shutdown", None)
        if callable(shutdown):
            with contextlib.suppress(Exception):
                shutdown()

    def _set_timeout(self, seconds: float) -> None:
        """Apply ``seconds`` to each later wait of the open connection."""
        seconds = max(MIN_WAIT_S, seconds)
        self.art.timeout = seconds  # for the upload socket, which is opened later
        self.art.connection.settimeout(seconds)  # the websocket keeps its own

    def _unless_blocked(self) -> None:
        if self.guard_tripped():
            raise _finished(
                DeliveryStatus.PROTOCOL,
                "the worker's connect guard refused an address other than the TV's",
            )

    # ----------------------------------------------------------------- steps

    def _verified_delivery(self) -> bytes:
        try:
            data = read_delivery(self.request.jpeg_path, self.request.jpeg_sha256)
        except OSError:
            raise _finished(
                DeliveryStatus.PROTOCOL, "the delivery file could not be read"
            ) from None
        except ValueError:
            raise _finished(
                DeliveryStatus.PROTOCOL, "the delivery file is not the validated image"
            ) from None
        if self.clock.left() < CONNECT_S + UPLOAD_ALLOWANCE_S:
            raise _finished(
                DeliveryStatus.INSUFFICIENT_TIME, "too little time is left to connect and upload"
            )
        return data

    def _check_support(self) -> None:
        art = self._new_art(CONNECT_S)
        try:
            supported = art.supported()
        except Exception as exc:  # noqa: BLE001 - every failure has an outcome
            self._unless_blocked()
            if isinstance(exc, self.library.transport_errors):
                raise _finished(
                    DeliveryStatus.UNREACHABLE, f"the TV did not answer ({type(exc).__name__})"
                ) from None
            raise _finished(
                DeliveryStatus.PROTOCOL,
                f"the TV's device information was not readable ({type(exc).__name__})",
            ) from None
        if supported is not True:
            raise _finished(DeliveryStatus.UNSUPPORTED, "the TV does not report Frame art support")

    def _connect(self) -> None:
        """Open the art channel, with at most one reconnect before ``upload_started``."""
        failure: _Finished | None = None
        for _attempt in range(2):
            wait = min(PAIRING_WAIT_S, self.clock.left() - UPLOAD_ALLOWANCE_S)
            if wait < CONNECT_S:
                break
            failure = self._open(wait)
            if failure is None:
                return
            _log.info("connecting to the TV failed: %s", failure.outcome["detail"])
        raise failure or _finished(
            DeliveryStatus.INSUFFICIENT_TIME, "too little time is left to connect and upload"
        )

    def _open(self, wait: float) -> _Finished | None:
        """One attempt, on a new connection object: ``SamsungTVArt.open()``
        returns the old, stale connection if an earlier ``open()`` on the same
        object failed after the handshake. Returns ``None`` on success, or the
        failure if a retry may help."""
        art = self._new_art(wait)
        before = self.handshakes.count
        try:
            art.open()
        except self.library.unauthorized:
            raise _finished(
                DeliveryStatus.NOT_AUTHORIZED, "the TV refused the pairing", Pairing.REJECTED
            ) from None
        except Exception as exc:  # noqa: BLE001 - every failure has an outcome
            self._unless_blocked()
            if isinstance(exc, self.library.websocket_timeout) and self.handshakes.count > before:
                # The TV answered the handshake but did not confirm the
                # connection: the prompt was not accepted in time (D-115: no retry).
                raise _finished(
                    DeliveryStatus.NOT_AUTHORIZED,
                    "the connection prompt was not accepted in time",
                    Pairing.PROMPT,
                ) from None
            return _finished(
                DeliveryStatus.UNREACHABLE,
                f"the TV's art service did not connect ({type(exc).__name__})",
            )
        self._relay_token(art)
        return None

    def _relay_token(self, art: Any) -> None:
        issued = getattr(art, "token", None)
        if not isinstance(issued, str) or issued == self.request.token:
            return
        if TOKEN_PATTERN.fullmatch(issued) is None:
            _log.warning("the TV issued a pairing token of an unexpected form; it is not kept")
            return
        _register_secret(issued)
        self.emit(token_event(issued))

    def _pin_api_version(self) -> None:
        self._set_timeout(min(CONNECT_S, self.clock.left()))
        try:
            version = self.art.get_api_version()
        except Exception as exc:  # noqa: BLE001 - every failure has an outcome
            self._unless_blocked()
            if isinstance(exc, self.library.transport_errors):
                raise _finished(
                    DeliveryStatus.UNREACHABLE,
                    f"the art API version was not received ({type(exc).__name__})",
                ) from None
            raise _finished(
                DeliveryStatus.PROTOCOL,
                f"the art API version was not readable ({type(exc).__name__})",
            ) from None
        if not isinstance(version, str) or _API_VERSION.fullmatch(version) is None:
            raise _finished(DeliveryStatus.PROTOCOL, "the art API version is not valid")
        if version in UNSUPPORTED_API_VERSIONS:
            raise _finished(
                DeliveryStatus.UNSUPPORTED, f"the TV's art API {version} is not supported yet"
            )
        # upload() asks for the version again; it is answered from here.
        self.art.get_api_version = lambda: version

    def _upload(self, data: bytes) -> str | None:
        """After ``upload_started``: every failure keeps the quarantine.

        Each wait of the upload may use all the time left: a kill during the
        selection still leaves ``uploaded``, which is better than a slow upload
        cut off into a quarantine."""
        self._set_timeout(self.clock.left())
        try:
            content_id = self.art.upload(data, matte="none", portrait_matte="none", file_type="jpg")
        except Exception as exc:  # noqa: BLE001 - every failure has an outcome
            self._unless_blocked()
            if isinstance(exc, self.library.response_error):
                raise _finished(
                    DeliveryStatus.PROTOCOL,
                    f"the TV reported an error during the upload{_tv_error(exc)};"
                    " it may hold the image",
                ) from None
            if isinstance(exc, self.library.transport_errors):
                raise _finished(
                    DeliveryStatus.UNREACHABLE,
                    f"the upload was cut off ({type(exc).__name__}); the TV may hold the image",
                ) from None
            raise _finished(
                DeliveryStatus.PROTOCOL,
                f"unexpected upload reply ({type(exc).__name__}); the TV may hold the image",
            ) from None
        if isinstance(content_id, str) and CONTENT_ID_PATTERN.fullmatch(content_id):
            return content_id
        _log.warning("the TV confirmed the upload with a content id of an unexpected form")
        return None

    def _select(self, content_id: str) -> None:
        """After ``uploaded``: the ledger holds the upload whatever happens here."""
        self._set_timeout(self.clock.left())
        try:
            self.art.select_image(content_id, show=True)
        except Exception as exc:  # noqa: BLE001 - every failure has an outcome
            self._unless_blocked()
            if isinstance(exc, self.library.response_error) and _tv_error(exc):
                raise _finished(
                    DeliveryStatus.REFUSED,
                    f"the TV refused to show the uploaded artwork{_tv_error(exc)}",
                ) from None
            if isinstance(exc, self.library.transport_errors):
                raise _finished(
                    DeliveryStatus.UNREACHABLE,
                    f"the selection was cut off ({type(exc).__name__})",
                ) from None
            raise _finished(
                DeliveryStatus.PROTOCOL, f"unexpected selection reply ({type(exc).__name__})"
            ) from None


def _tv_error(exc: BaseException) -> str:
    """`` (TV error send_image -1)`` for the television's own error reply, else ``""``."""
    match = _TV_ERROR.search(str(exc))
    return "" if match is None else f" (TV error {match.group(1)} {match.group(2)})"


# ------------------------------------------------------------------ the guard


class GuardViolation(Exception):
    """The worker tried to reach an address other than the television's.

    Not an ``OSError``, so the libraries do not turn it into "unreachable"."""


@dataclass(frozen=True, slots=True)
class ConnectGuard:
    blocked: list[str]
    undo: Callable[[], None]

    def tripped(self) -> bool:
        return bool(self.blocked)


_BLOCKED_RESOLVERS: Final = ("gethostbyname", "gethostbyname_ex", "gethostbyaddr", "getnameinfo")


def install_connect_guard(host: IPv4Address) -> ConnectGuard:
    """Let the worker reach only ``host`` (any port), resolve no names, and
    spend at most ``CONNECT_S`` on any TCP connect.

    The television chooses the address of its upload socket (the D2D
    ``conn_info``); the guard makes sure it is the television's own. The
    libraries resolve even an address literal through ``getaddrinfo``, so
    the literal itself is passed on; every other name is refused. It wraps
    the standard library's ``socket`` functions, not the library (D-160).
    ``undo`` restores them (for tests).
    """
    import socket  # noqa: PLC0415 - only the television worker needs sockets

    allowed = str(host)
    blocked: list[str] = []
    saved: list[tuple[object, str, object]] = []

    def replace(owner: object, name: str, value: object) -> None:
        saved.append((owner, name, getattr(owner, name)))
        setattr(owner, name, value)

    def refuse(what: str) -> GuardViolation:
        blocked.append(what)
        _log.warning("the connect guard refused %s", what)
        return GuardViolation("the television worker may reach only the TV")

    def check(address: object) -> None:
        if isinstance(address, tuple) and len(address) >= 2 and address[0] == allowed:
            return
        what = f"{address[0]}:{address[1]}" if isinstance(address, tuple) else "an address"
        raise refuse(what[:80])

    @contextlib.contextmanager
    def bounded(sock: socket.socket) -> Iterator[None]:
        previous = sock.gettimeout()
        if previous is not None and previous <= CONNECT_S:
            yield
            return
        sock.settimeout(CONNECT_S)
        try:
            yield
        finally:
            sock.settimeout(previous)

    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex
    real_getaddrinfo = socket.getaddrinfo

    def connect(self: socket.socket, address: object) -> None:
        check(address)
        with bounded(self):
            real_connect(self, address)  # type: ignore[arg-type]

    def connect_ex(self: socket.socket, address: object) -> int:
        check(address)
        with bounded(self):
            return real_connect_ex(self, address)  # type: ignore[arg-type]

    def getaddrinfo(name: object, *args: object, **kwargs: object) -> object:
        # The same signature as socket.getaddrinfo, passed on unchanged,
        # except that the name must be the television's address literal.
        if name != allowed:
            raise refuse("a name lookup")
        return real_getaddrinfo(name, *args, **kwargs)  # type: ignore[arg-type]

    def resolver(*_args: object, **_kwargs: object) -> object:
        raise refuse("a name lookup")

    replace(socket.socket, "connect", connect)
    replace(socket.socket, "connect_ex", connect_ex)
    replace(socket, "getaddrinfo", getaddrinfo)
    for name in _BLOCKED_RESOLVERS:
        replace(socket, name, resolver)

    def undo() -> None:
        for owner, name, value in reversed(saved):
            setattr(owner, name, value)

    return ConnectGuard(blocked, undo)


# ------------------------------------------------------------------ the entry


def quiet_library() -> None:
    """The library talks TLS to the TV without verification on port 8002
    (its documented behaviour, D-161); the resulting urllib3 warning is not
    actionable. Its loggers are capped at WARNING (§18.1): at INFO it logs
    the pairing token."""
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    for name in _LIBRARY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)


def deliver_task(payload: JsonObject, emit: EventSink) -> JsonObject:
    """The worker's entry for the ``deliver`` task (process executor only):
    the guard, then the real library, then :func:`run_delivery`."""
    request = TvRequest.from_json(payload)
    quiet_library()
    guard = install_connect_guard(request.host)
    return run_delivery(load_library(), request, emit, guard_tripped=guard.tripped)
