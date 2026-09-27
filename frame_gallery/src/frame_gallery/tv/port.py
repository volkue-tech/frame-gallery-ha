"""The television port and its progress markers (§12.1).

The whole delivery is one coarse operation. The implementation (Phase 5)
runs the Samsung library in an isolated worker and relays the worker's
progress markers to the parent as they arrive, through ``on_marker``.
"""

from __future__ import annotations

import enum
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from ipaddress import IPv4Address
from pathlib import Path
from typing import Final, Protocol

from frame_gallery.budget.deadline import Deadline

CONTENT_ID_PATTERN: Final = re.compile(r"[A-Za-z0-9_.:-]{1,64}")
"""A strict pattern for the television's content identifier (≤ 64 chars)."""


class Marker(enum.StrEnum):
    """Progress markers, in the order the worker emits them."""

    CONNECTED = "connected"
    UPLOAD_STARTED = "upload_started"
    """Sent, and its send completed, before the library's upload is called:
    a missing ``upload_started`` proves that nothing was uploaded."""

    UPLOADED = "uploaded"
    """The television confirmed the upload. Carries its ``content_id``, or
    ``None`` when the confirmation came without a usable one (D-162): the
    upload is recorded all the same, but it cannot be selected."""

    SELECTED = "selected"


MARKER_ORDER: Final = (Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED, Marker.SELECTED)


class DeliveryStatus(enum.StrEnum):
    OK = "ok"
    UNREACHABLE = "unreachable"
    NOT_AUTHORIZED = "not_authorized"
    UNSUPPORTED = "unsupported"
    REFUSED = "refused"
    PROTOCOL = "protocol"
    INSUFFICIENT_TIME = "insufficient_time"
    """The upload allowance guard: not enough DELIVER time left to upload."""


class AuthChange(enum.StrEnum):
    UNCHANGED = "unchanged"
    NEW_TOKEN = "new_token"  # noqa: S105 - a status name, not a secret
    TOKEN_REJECTED = "token_rejected"  # noqa: S105 - a status name, not a secret


@dataclass(frozen=True, slots=True)
class MarkerEvent:
    marker: Marker
    content_id: str | None = None

    def __post_init__(self) -> None:
        if self.marker is Marker.UPLOADED:
            if (
                self.content_id is not None
                and CONTENT_ID_PATTERN.fullmatch(self.content_id) is None
            ):
                msg = "the uploaded marker needs a valid content_id or none"
                raise ValueError(msg)
        elif self.content_id is not None:
            msg = f"the {self.marker.value} marker carries no content_id"
            raise ValueError(msg)


def _never() -> bool:
    return False


@dataclass(frozen=True, slots=True)
class DeliveryRequest:
    jpeg_path: Path
    """The parent-validated ``delivery.jpg``."""

    jpeg_sha256: str
    """The parent's SHA-256 of ``delivery.jpg`` (§11.3). The worker uploads only
    bytes with this hash (D-162)."""

    tv_host: IPv4Address
    """The validated RFC 1918 literal (§15.4)."""

    deadline: Deadline
    """The DELIVER deadline; the worker's kill timer is clamped to it."""

    stop_requested: Callable[[], bool] = field(default=_never)
    """Whether a stop request (SIGTERM) arrived. Stop requests are deferred for
    the whole call, so the adapter polls this while it waits for its worker."""


@dataclass(frozen=True, slots=True)
class DeliveryResult:
    status: DeliveryStatus
    auth: AuthChange = AuthChange.UNCHANGED
    markers_seen: tuple[Marker, ...] = ()
    detail: str = ""
    """A short, log-safe explanation."""


MarkerSink = Callable[[MarkerEvent], None]


class Television(Protocol):
    def deliver(self, request: DeliveryRequest, on_marker: MarkerSink) -> DeliveryResult:
        """Connect, upload, and select, calling ``on_marker`` for each marker.

        The caller defers stop requests for the whole call, so neither a
        marker nor its ledger write can be lost to a SIGTERM (§7.6, D-141).
        The adapter polls ``request.stop_requested`` while it waits; once it
        returns true, the adapter kills its worker, relays every marker the
        worker had already sent, and returns ``UNREACHABLE`` with the markers
        seen. The caller then classifies the run as cancelled.

        If the worker is killed by its timer or the deadline, the adapter also
        returns ``UNREACHABLE`` with the markers seen so far. The method
        returns or raises only after its worker was killed and its channel
        closed, so no marker can arrive after the caller has classified the
        result (D-137); the caller also kills every worker before classifying
        an interrupted delivery.
        """
        ...
