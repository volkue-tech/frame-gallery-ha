"""The guarded gateway: every provider request goes through here (§10, D-108).

One :class:`Gateway` serves a run; each provider talks through its own
:class:`ProviderChannel`, which holds the provider's host policy, its pacing
clock, its metadata allowance, and its 403/429 stop (D-115). A request:

1. is refused at once after a stop;
2. takes one metadata request from the allowance (metadata only);
3. waits for the provider's pacing interval (start to start);
4. resolves the host once, and requires every address to be public;
5. connects to the addresses in order (the transport checks the peer);
6. follows at most 3 redirects, each validated and paced like a new request;
7. checks the status, the media type, the encoding, and the declared length;
8. reads the body in re-clamped steps, capping the bytes received and, after
   at most one gzip layer (metadata only), the decoded bytes.

Only a metadata request is retried, once, and only after a connect failure, a
502/503/504, or a 429 whose ``Retry-After`` is at most 5 s (D-115). The
request's own time limit gives ``SourceError(TIMEOUT)``; the caller's deadline
gives ``DeadlineExceeded``. Logs carry the host, the path without its query,
the status, the byte count, and the duration, never bodies or header values.
"""

from __future__ import annotations

import json
import logging
import os
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Final, NoReturn, Protocol

from frame_gallery.budget.allowance import Allowance, AllowanceExhausted
from frame_gallery.budget.clock import Clock
from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.budget.limits import CONNECT_S, DNS_S, READ_S
from frame_gallery.net.identity import ClientIdentity
from frame_gallery.net.policy import (
    HTTPS_PORT,
    MAX_ADDRESSES,
    MAX_REDIRECTS,
    MISSING_STATUSES,
    REDIRECT_STATUSES,
    RETRY_AFTER_MAX_S,
    RETRY_JITTER_S,
    RETRY_STATUSES,
    RETRY_WAIT_MIN_S,
    RULES,
    STOP_STATUSES,
    TOO_MANY_REQUESTS,
    HostPolicy,
    KindRules,
    PolicyViolation,
    RequestKind,
    ValidatedUrl,
    content_length,
    is_public_address,
    media_type,
    resolve_redirect,
    retry_after_seconds,
    validate_url,
)
from frame_gallery.net.wire import (
    FailureStage,
    IPAddress,
    Resolver,
    Transport,
    TransportFailure,
    WireRequest,
    WireResponse,
)
from frame_gallery.providers.contract import SourceError, SourceErrorKind
from frame_gallery.randomness import RandomSource

READ_CHUNK: Final = 64 * 1024
_GZIP_WBITS: Final = 16 + zlib.MAX_WBITS
_SUCCESS: Final = 200

_log = logging.getLogger("frame_gallery.net")


@dataclass(frozen=True, slots=True)
class Download:
    """An image written to its destination."""

    path: Path
    size_bytes: int
    media_type: str


class _Sink(Protocol):
    def write(self, data: bytes) -> None: ...


class _Retry(Exception):
    """A failure that permits the single metadata retry after ``wait_s``."""

    def __init__(self, error: SourceError, wait_s: float) -> None:
        super().__init__(error.kind.value)
        self.error = error
        self.wait_s = wait_s


class _MemorySink:
    __slots__ = ("data",)

    def __init__(self) -> None:
        self.data = bytearray()

    def write(self, data: bytes) -> None:
        self.data += data


class _FileSink:
    """Writes to a new file (never an existing one or through a symlink)."""

    __slots__ = ("_fd",)

    def __init__(self, path: Path) -> None:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
        self._fd = os.open(path, flags, 0o600)

    def write(self, data: bytes) -> None:
        view = memoryview(data)
        while view:
            written = os.write(self._fd, view)
            view = view[written:]

    def close(self) -> None:
        os.close(self._fd)


class Gateway:
    """The run's gateway: shared resolver, transport, clock, and identity."""

    def __init__(
        self,
        *,
        resolver: Resolver,
        transport: Transport,
        clock: Clock,
        random: RandomSource,
        identity: ClientIdentity,
    ) -> None:
        self._resolver = resolver
        self._transport = transport
        self._clock = clock
        self._random = random
        self._identity = identity

    def channel(self, policy: HostPolicy, *, metadata_allowance: Allowance) -> ProviderChannel:
        """A channel for one provider; create one per provider per run."""
        return ProviderChannel(self, policy, metadata_allowance)


class ProviderChannel:
    """One provider's view of the gateway (§10, D-115)."""

    def __init__(self, gateway: Gateway, policy: HostPolicy, allowance: Allowance) -> None:
        self._gateway = gateway
        self._policy = policy
        self._allowance = allowance
        self._stopped = False
        self._next_start: float | None = None
        self._headers = {
            "User-Agent": gateway._identity.user_agent,
            "Connection": "close",
            **policy.courtesy_headers,
        }

    @property
    def policy(self) -> HostPolicy:
        return self._policy

    @property
    def stopped(self) -> bool:
        """Whether a 401/403/429 stopped this provider for the run."""
        return self._stopped

    @property
    def metadata_requests(self) -> int:
        """Metadata requests sent so far (retries and redirects included)."""
        return self._allowance.used

    # --------------------------------------------------------------- requests

    def get_json(self, url: str, deadline: Deadline) -> object:
        """GET a JSON document. Raises ``SourceError``, ``DeadlineExceeded``,
        ``AllowanceExhausted`` (the metadata allowance), or ``Cancelled``.

        A 404 or 410 is ``HTTP_ERROR``: metadata requests are discovery
        requests (D-141 item 3).
        """
        rules = RULES[RequestKind.METADATA]
        retried = False
        while True:
            sink = _MemorySink()
            try:
                self._request(url, RequestKind.METADATA, deadline, sink)
            except _Retry as retry:
                if retried or not self._may_retry(retry.wait_s, deadline, rules):
                    self._give_up(retry)
                retried = True
                self._gateway._clock.sleep(retry.wait_s)
                continue
            return _parse_json(bytes(sink.data))

    def download(self, url: str, destination: Path, deadline: Deadline) -> Download:
        """GET an image into ``destination``, a new file. Never retried.

        A 404 or 410 is ``NOT_FOUND`` (one resource). The partial file is
        removed on any failure.
        """
        sink = _FileSink(destination)
        completed = False
        try:
            found, size = self._request(url, RequestKind.IMAGE, deadline, sink)
            completed = True
        except _Retry as retry:
            self._give_up(retry)
        finally:
            sink.close()
            if not completed:
                destination.unlink(missing_ok=True)
        return Download(path=destination, size_bytes=size, media_type=found)

    def _give_up(self, retry: _Retry) -> NoReturn:
        """Raise the failure a retry would have answered; an unanswered 429 is
        a stop (D-115)."""
        if retry.error.kind is SourceErrorKind.STOPPED and not self._stopped:
            self._stopped = True
            _log.warning(
                "%s: HTTP 429 without a permitted retry: no further requests in this run",
                self._policy.provider_key,
            )
        raise retry.error from None

    def _may_retry(self, wait_s: float, deadline: Deadline, rules: KindRules) -> bool:
        if self._stopped or self._allowance.exhausted:
            return False
        # The wait and one whole connect must still fit the caller's deadline.
        return deadline.remaining() > wait_s + min(CONNECT_S, rules.total_s)

    def _request(
        self, url: str, kind: RequestKind, deadline: Deadline, sink: _Sink
    ) -> tuple[str, int]:
        """One attempt, redirects included. Returns the media type and size."""
        rules = RULES[kind]
        attempt = deadline.child(rules.total_s, f"{kind.value} request")
        current = self._validated(url, "the URL")
        for hop in range(MAX_REDIRECTS + 1):
            started = self._gateway._clock.monotonic()
            response = self._send(current, kind, deadline, attempt)
            try:
                status = response.status
                if status in REDIRECT_STATUSES:
                    if hop == MAX_REDIRECTS:
                        self._fail(
                            SourceErrorKind.HTTP_ERROR, "too many redirects", current, status
                        )
                    location = response.header("location")
                    if location is None:
                        self._fail(
                            SourceErrorKind.HTTP_ERROR,
                            "redirect without a location",
                            current,
                            status,
                        )
                    _log.debug(
                        "%s %s%s -> %d redirect", kind.value, current.host, current.path, status
                    )
                    current = self._validated(location, "the redirect", base=current)
                    continue
                self._check_status(status, response, kind, current)
                found, declared, gzipped = self._check_headers(response, rules, current)
                size = self._read_body(
                    response,
                    deadline,
                    attempt,
                    sink,
                    current,
                    max_bytes=rules.max_bytes,
                    declared=declared,
                    gzipped=gzipped,
                )
            finally:
                response.close()
            _log.debug(
                "%s %s%s -> %d, %d B, %.2f s",
                kind.value,
                current.host,
                current.path,
                status,
                size,
                self._gateway._clock.monotonic() - started,
            )
            return found, size
        raise AssertionError("unreachable")  # pragma: no cover - the loop returns or raises

    def _validated(self, url: str, what: str, *, base: ValidatedUrl | None = None) -> ValidatedUrl:
        try:
            if base is None:
                return validate_url(url, self._policy)
            return resolve_redirect(base, url, self._policy)
        except PolicyViolation as exc:
            kind = SourceErrorKind.UNEXPECTED_FORMAT if base is None else SourceErrorKind.HTTP_ERROR
            raise SourceError(kind, f"{what} is outside the host policy ({exc})") from None

    # ------------------------------------------------------------------ steps

    def _send(
        self, current: ValidatedUrl, kind: RequestKind, deadline: Deadline, attempt: Deadline
    ) -> WireResponse:
        if self._stopped:
            raise SourceError(SourceErrorKind.STOPPED, "stopped earlier in this run")
        if kind is RequestKind.METADATA and not self._allowance.try_take():
            raise AllowanceExhausted(self._allowance.name)
        self._pace(deadline, attempt)
        addresses = self._resolve(current.host, deadline, attempt)
        rules = RULES[kind]
        headers = {
            "Host": current.host,
            "Accept": rules.accept,
            "Accept-Encoding": rules.accept_encoding,
            **self._headers,
        }
        failure = TransportFailure(FailureStage.CONNECT, "no address")
        for address in addresses[:MAX_ADDRESSES]:
            request = WireRequest(
                address=address,
                host=current.host,
                port=HTTPS_PORT,
                tls=True,
                target=current.target,
                headers=headers,
            )
            try:
                return self._gateway._transport.open(
                    request,
                    connect_timeout=self._clamp(CONNECT_S, deadline, attempt),
                    exchange_timeout=self._clamp(rules.total_s, deadline, attempt),
                )
            except TransportFailure as exc:
                if exc.stage is not FailureStage.CONNECT:
                    self._transport_failed(exc, deadline, attempt, current)
                failure = exc
        if failure.timed_out and attempt.expired():
            self._timed_out(deadline, current)
        raise _Retry(
            SourceError(SourceErrorKind.TRANSPORT, f"connect to {current.host} failed"),
            self._retry_wait(RETRY_WAIT_MIN_S),
        )

    def _pace(self, deadline: Deadline, attempt: Deadline) -> None:
        clock = self._gateway._clock
        if self._next_start is not None:
            wait = self._next_start - clock.monotonic()
            if wait > 0:
                if wait >= deadline.remaining():
                    raise DeadlineExceeded(deadline.name)
                if wait >= attempt.remaining():
                    self._timed_out(deadline, None)
                clock.sleep(wait)
        self._next_start = clock.monotonic() + self._policy.min_interval_s

    def _resolve(self, host: str, deadline: Deadline, attempt: Deadline) -> list[IPAddress]:
        try:
            addresses = list(
                self._gateway._resolver.resolve(
                    host, HTTPS_PORT, self._clamp(DNS_S, deadline, attempt)
                )
            )
        except TransportFailure as exc:
            if exc.timed_out and attempt.expired():
                self._timed_out(deadline, None)
            raise _Retry(
                SourceError(SourceErrorKind.TRANSPORT, f"name resolution for {host} failed"),
                self._retry_wait(RETRY_WAIT_MIN_S),
            ) from None
        if not addresses or not all(is_public_address(address) for address in addresses):
            # A resolver that answers with a private or special address is
            # refused outright (§10); this is never retried.
            raise SourceError(SourceErrorKind.TRANSPORT, f"{host} resolved to a non-public address")
        return addresses

    def _check_status(
        self, status: int, response: WireResponse, kind: RequestKind, current: ValidatedUrl
    ) -> None:
        if status == _SUCCESS:
            return
        if status in STOP_STATUSES:
            self._stop(status, current)
        if status == TOO_MANY_REQUESTS:
            wait = retry_after_seconds(
                response.header("retry-after"), self._gateway._clock.utc_now()
            )
            if RULES[kind].retry and wait is not None and wait <= RETRY_AFTER_MAX_S:
                raise _Retry(
                    SourceError(SourceErrorKind.STOPPED, f"HTTP 429 from {current.host}"),
                    self._retry_wait(max(wait, RETRY_WAIT_MIN_S)),
                )
            self._stop(status, current)
        if status in RETRY_STATUSES and RULES[kind].retry:
            raise _Retry(
                SourceError(SourceErrorKind.HTTP_ERROR, f"HTTP {status} from {current.host}"),
                self._retry_wait(RETRY_WAIT_MIN_S),
            )
        if status in MISSING_STATUSES and kind is RequestKind.IMAGE:
            self._fail(SourceErrorKind.NOT_FOUND, "not found", current, status)
        self._fail(SourceErrorKind.HTTP_ERROR, "unexpected status", current, status)

    def _check_headers(
        self, response: WireResponse, rules: KindRules, current: ValidatedUrl
    ) -> tuple[str, int | None, bool]:
        """The media type, the declared length, and whether the body is gzipped."""
        found = media_type(response.header("content-type"))
        if found is None or found not in rules.media_types:
            self._fail(SourceErrorKind.UNEXPECTED_FORMAT, "unexpected media type", current)
        encoding = (response.header("content-encoding") or "identity").strip().lower()
        if encoding not in ("identity", "gzip") or (encoding == "gzip" and not rules.gzip_allowed):
            self._fail(SourceErrorKind.UNEXPECTED_FORMAT, "unexpected content encoding", current)
        try:
            declared = content_length(response.header("content-length"))
        except ValueError:
            self._fail(SourceErrorKind.UNEXPECTED_FORMAT, "invalid Content-Length", current)
        if declared is not None and declared > rules.max_bytes:
            self._fail(SourceErrorKind.OVER_CAP, "declared length over the cap", current)
        return found, declared, encoding == "gzip"

    def _read_body(
        self,
        response: WireResponse,
        deadline: Deadline,
        attempt: Deadline,
        sink: _Sink,
        current: ValidatedUrl,
        *,
        max_bytes: int,
        declared: int | None,
        gzipped: bool,
    ) -> int:
        decoder = zlib.decompressobj(wbits=_GZIP_WBITS) if gzipped else None
        received = 0
        written = 0
        while True:
            timeout = self._clamp(READ_S, deadline, attempt)
            try:
                chunk = response.read(READ_CHUNK, timeout)
            except TransportFailure as exc:
                self._transport_failed(exc, deadline, attempt, current)
            if not chunk:
                break
            received += len(chunk)
            if received > max_bytes:
                self._fail(SourceErrorKind.OVER_CAP, "body over the cap", current)
            if decoder is None:
                data = chunk  # within the cap: received == written
            else:
                data = _inflate(decoder, chunk, max_bytes - written, self, current)
            written += len(data)
            sink.write(data)
        if declared is not None and received != declared:
            self._fail(SourceErrorKind.TRANSPORT, "body shorter than declared", current)
        if decoder is not None and not decoder.eof:
            self._fail(SourceErrorKind.UNEXPECTED_FORMAT, "truncated gzip body", current)
        return written

    # ---------------------------------------------------------------- helpers

    def _clamp(self, timeout: float, deadline: Deadline, attempt: Deadline) -> float:
        try:
            return attempt.clamp(timeout)
        except DeadlineExceeded:
            self._timed_out(deadline, None)

    def _timed_out(self, deadline: Deadline, current: ValidatedUrl | None) -> NoReturn:
        """The caller's deadline wins over the request's own time limit."""
        if deadline.expired():
            raise DeadlineExceeded(deadline.name)
        where = f" ({current.host}{current.path})" if current is not None else ""
        raise SourceError(SourceErrorKind.TIMEOUT, f"request time limit reached{where}")

    def _transport_failed(
        self, exc: TransportFailure, deadline: Deadline, attempt: Deadline, current: ValidatedUrl
    ) -> NoReturn:
        if exc.timed_out:
            if attempt.expired():
                self._timed_out(deadline, current)
            raise SourceError(
                SourceErrorKind.TIMEOUT, f"{current.host} stopped responding"
            ) from None
        raise SourceError(
            SourceErrorKind.TRANSPORT, f"{exc.stage.value} failed for {current.host}"
        ) from None

    def _stop(self, status: int, current: ValidatedUrl) -> NoReturn:
        self._stopped = True
        _log.warning(
            "%s answered HTTP %d: no further requests to %s in this run",
            current.host,
            status,
            self._policy.provider_key,
        )
        raise SourceError(SourceErrorKind.STOPPED, f"HTTP {status} from {current.host}")

    def _fail(
        self,
        kind: SourceErrorKind,
        detail: str,
        current: ValidatedUrl,
        status: int | None = None,
    ) -> NoReturn:
        suffix = f" (HTTP {status})" if status is not None else ""
        raise SourceError(kind, f"{detail}{suffix}: {current.host}{current.path}")

    def _retry_wait(self, base: float) -> float:
        return base + self._gateway._random.random() * RETRY_JITTER_S


def _inflate(
    decoder: zlib._Decompress,
    chunk: bytes,
    room: int,
    channel: ProviderChannel,
    current: ValidatedUrl,
) -> bytes:
    """Decode one chunk of a single gzip member into at most ``room`` bytes.

    The decoder may produce one byte more than ``room``, so an overflow is
    detected without decoding the rest."""
    if decoder.eof:
        channel._fail(SourceErrorKind.UNEXPECTED_FORMAT, "data after the gzip body", current)
    try:
        data = decoder.decompress(chunk, room + 1)
    except zlib.error:
        channel._fail(SourceErrorKind.UNEXPECTED_FORMAT, "invalid gzip body", current)
    if len(data) > room or decoder.unconsumed_tail:
        channel._fail(SourceErrorKind.OVER_CAP, "decoded body over the cap", current)
    if decoder.unused_data:
        channel._fail(SourceErrorKind.UNEXPECTED_FORMAT, "data after the gzip body", current)
    return data


def _reject_constant(name: str) -> NoReturn:
    msg = f"non-standard JSON constant {name}"
    raise ValueError(msg)


def _parse_json(data: bytes) -> object:
    """Standard-library JSON only (D-127); NaN and Infinity are refused."""
    try:
        document: object = json.loads(data.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise SourceError(
            SourceErrorKind.UNEXPECTED_FORMAT, "the response is not valid JSON"
        ) from None
    return document
