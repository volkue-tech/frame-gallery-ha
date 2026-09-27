"""The Samsung adapter: the ``Television`` port over the isolated worker (§12, D-141, D-162).

The parent side of a delivery:

1. The stored pairing token, if any, goes to the worker inside its request
   message; no token file is shared with the worker (D-162).
2. The ``deliver`` task runs in the television worker through the executor.
   Its kill timer is the DELIVER deadline, and a stop request (SIGTERM) is
   polled while it runs: the executor then kills the worker, after every
   event the worker had already written was relayed.
3. Each event is checked as it arrives. A marker is relayed to the runner at
   once, so the runner promotes the ledger entry as soon as ``uploaded``
   arrives; a marker out of order is still relayed (the runner handles it
   conservatively) before the worker is stopped for the protocol violation.
   A new pairing token, sent before ``connected`` (at most one per
   connection attempt, so at most two), is registered with the redactor and
   installed at once (``new_token``; the last one wins), even if the worker
   dies later. After a rejection, a stored token is removed
   (``token_rejected``).
4. The worker's status must fit the markers the parent relayed; otherwise it
   is ``protocol``. The worker runs the third-party library, so the parent
   does not let its status alone remove an upload intent.

``deliver`` returns only after its worker was killed and its channel closed
(the executor returns or raises only then), so no marker can arrive after
the runner has classified the result. A marker the worker writes is never
lost to a SIGTERM, because the runner defers stop requests for the whole
call.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Final

from frame_gallery.errors import StateError
from frame_gallery.isolation.executor import Executor, JsonObject, WorkerError, WorkerErrorKind
from frame_gallery.logs.redact import active_redactor
from frame_gallery.logs.summary import sanitize_for_log
from frame_gallery.tv.contract import TOKEN_PATTERN, Pairing, TvRequest
from frame_gallery.tv.port import (
    MARKER_ORDER,
    AuthChange,
    DeliveryRequest,
    DeliveryResult,
    DeliveryStatus,
    Marker,
    MarkerEvent,
    MarkerSink,
)
from frame_gallery.tv.token_store import TokenStore

DELIVER_TASK: Final = "deliver"
DELIVER_TIMEOUT_S: Final = 40.0
"""The DELIVER phase (§7.2); the deadline clamps it further."""

MAX_DETAIL: Final = 160
MAX_TOKEN_EVENTS: Final = 2
"""One per connection attempt (D-162 point 4: at most one reconnect)."""

_log = logging.getLogger("frame_gallery.tv")

_FAILED_WORKER: Final = {
    WorkerErrorKind.TIMEOUT: DeliveryStatus.UNREACHABLE,
    WorkerErrorKind.STOPPED: DeliveryStatus.UNREACHABLE,
}
"""A killed worker is a lost connection (§12.3); anything else a protocol failure."""

_BEFORE_UPLOAD_ONLY: Final = frozenset(
    {DeliveryStatus.NOT_AUTHORIZED, DeliveryStatus.UNSUPPORTED, DeliveryStatus.INSUFFICIENT_TIME}
)


class _EventRelay:
    """Checks each worker event, relays markers to the runner, and hands a
    new pairing token to ``on_token``."""

    def __init__(self, on_marker: MarkerSink, on_token: Callable[[str], None]) -> None:
        self._on_marker = on_marker
        self._on_token = on_token
        self.seen: list[Marker] = []
        self.tokens = 0

    def __call__(self, event: JsonObject) -> None:
        """Raises ``ValueError`` for an event that breaks the protocol."""
        if set(event) == {"token"}:
            self._token(event["token"])
        else:
            self._marker(event)

    def _token(self, token: object) -> None:
        if self.tokens >= MAX_TOKEN_EVENTS or self.seen:
            msg = "a token event after a marker or a third token event"
            raise ValueError(msg)
        if not isinstance(token, str) or TOKEN_PATTERN.fullmatch(token) is None:
            msg = "a token of an unexpected form"
            raise ValueError(msg)
        self.tokens += 1
        self._on_token(token)

    def _marker(self, event: JsonObject) -> None:
        name, content_id = event.get("marker"), event.get("content_id")
        if set(event) != {"marker", "content_id"} or not isinstance(name, str):
            msg = "not a marker event"
            raise ValueError(msg)
        if content_id is not None and not isinstance(content_id, str):
            msg = "invalid content id"
            raise ValueError(msg)
        checked = MarkerEvent(Marker(name), content_id)  # ValueError if unknown or invalid
        if checked.marker in self.seen:
            msg = f"marker {name} repeated"
            raise ValueError(msg)
        in_order = MARKER_ORDER[len(self.seen)] is checked.marker
        self.seen.append(checked.marker)
        self._on_marker(checked)
        if not in_order:
            msg = f"marker {name} out of order"
            raise ValueError(msg)


class SamsungTelevision:
    """The ``Television`` port. One instance serves one run."""

    def __init__(
        self,
        executor: Executor,
        tokens: TokenStore,
        *,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self._executor = executor
        self._tokens = tokens
        self._monotonic = monotonic
        self._new_token = False

    def deliver(self, request: DeliveryRequest, on_marker: MarkerSink) -> DeliveryResult:
        """Connect, upload, and select in the worker; see the module docstring.

        Raises ``DeadlineExceeded`` when no time is left to start.
        """
        timeout = request.deadline.clamp(DELIVER_TIMEOUT_S)
        seed = self._tokens.load()
        payload = TvRequest(
            host=request.tv_host,
            token=seed,
            jpeg_path=request.jpeg_path,
            jpeg_sha256=request.jpeg_sha256,
            deadline=self._monotonic() + timeout,
        ).to_json()
        self._new_token = False
        relay = _EventRelay(on_marker, self._install)
        pairing: str | None = None
        try:
            outcome = self._executor.run(
                DELIVER_TASK,
                payload,
                timeout=timeout,
                on_event=relay,
                should_stop=request.stop_requested,
            )
            status, detail, pairing = _parse_result(outcome, relay.seen)
        except WorkerError as exc:
            status = _FAILED_WORKER.get(exc.kind, DeliveryStatus.PROTOCOL)
            detail = f"the television worker ended: {exc.kind.value}"
        return DeliveryResult(
            status=status,
            auth=self._auth(seed, rejected=pairing == Pairing.REJECTED.value),
            markers_seen=tuple(relay.seen),
            detail=sanitize_for_log(detail, max_length=MAX_DETAIL),
        )

    def _install(self, token: str) -> None:
        """Keep a new token at once; a failure to store it does not stop the delivery."""
        redactor = active_redactor()
        if redactor is not None:
            redactor.add_secret(token)
        try:
            self._tokens.install(token)
        except StateError as exc:
            _log.warning("the new pairing token could not be stored: %s", exc)
            return
        self._new_token = True
        _log.info("the TV accepted the pairing; the token is stored")

    def _auth(self, seed: str | None, *, rejected: bool) -> AuthChange:
        if self._new_token:
            return AuthChange.NEW_TOKEN
        if rejected and seed is not None:
            self._tokens.remove()
            _log.warning("the TV rejected the stored pairing token; it was removed")
            return AuthChange.TOKEN_REJECTED
        return AuthChange.UNCHANGED


_STATUSES: Final = frozenset(status.value for status in DeliveryStatus)
_PAIRINGS: Final = frozenset(pairing.value for pairing in Pairing)


def _parse_result(
    outcome: JsonObject, seen: list[Marker]
) -> tuple[DeliveryStatus, str, str | None]:
    status, detail, pairing = outcome.get("status"), outcome.get("detail"), outcome.get("pairing")
    if (
        set(outcome) != {"status", "detail", "pairing"}
        or not isinstance(status, str)
        or status not in _STATUSES
        or not isinstance(detail, str)
        or not (pairing is None or (isinstance(pairing, str) and pairing in _PAIRINGS))
    ):
        return DeliveryStatus.PROTOCOL, "the television worker's result was not understood", None
    parsed = DeliveryStatus(status)
    if not _fits(parsed, pairing, seen):
        return (
            DeliveryStatus.PROTOCOL,
            f"the television worker's result ({status}) does not fit its markers",
            None,
        )
    return parsed, detail, pairing


def _fits(status: DeliveryStatus, pairing: str | None, seen: list[Marker]) -> bool:
    """Whether ``status`` can follow the markers relayed (§12.4)."""
    if pairing is not None and status is not DeliveryStatus.NOT_AUTHORIZED:
        return False
    if status is DeliveryStatus.OK:
        return Marker.SELECTED in seen
    if status is DeliveryStatus.REFUSED:
        return Marker.UPLOADED in seen and Marker.SELECTED not in seen
    if status in _BEFORE_UPLOAD_ONLY:
        return Marker.UPLOAD_STARTED not in seen
    return Marker.SELECTED not in seen
