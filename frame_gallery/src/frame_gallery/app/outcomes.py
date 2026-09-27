"""The outcome taxonomy, exit codes, and outcome classification (§4.2, §12.4, D-133).

Every run ends with exactly one outcome. Two pure classifiers decide it when
nothing was delivered and when the television phase did not end in
``selected``; both are table-tested.
"""

from __future__ import annotations

import enum
import logging
from collections.abc import Collection
from dataclasses import dataclass
from typing import Final

from frame_gallery.tv.port import DeliveryStatus, Marker

INTERNAL_ERROR_EXIT_CODE: Final = 70
WATCHDOG_EXIT_CODE: Final = 71


class Outcome(enum.StrEnum):
    DELIVERED = "delivered"
    DELIVERED_WITH_WARNINGS = "delivered_with_warnings"
    DELIVERED_UNRECORDED = "delivered_unrecorded"
    NO_MATCH = "no_match"
    CONFIG_INVALID = "config_invalid"
    ALREADY_RUNNING = "already_running"
    STATE_ERROR = "state_error"
    SOURCE_FAILED = "source_failed"
    IMAGE_FAILED = "image_failed"
    TV_UNREACHABLE = "tv_unreachable"
    TV_NOT_AUTHORIZED = "tv_not_authorized"
    TV_REJECTED = "tv_rejected"
    DEADLINE_EXCEEDED = "deadline_exceeded"
    CANCELLED = "cancelled"
    INTERNAL_ERROR = "internal_error"

    @property
    def exit_code(self) -> int:
        """Every classified outcome exits 0; only a bug exits non-zero (D-133)."""
        return INTERNAL_ERROR_EXIT_CODE if self is Outcome.INTERNAL_ERROR else 0

    @property
    def log_level(self) -> int:
        return _LOG_LEVELS.get(self, logging.ERROR)

    @property
    def delivered(self) -> bool:
        """The television displays the new artwork."""
        return self in _DELIVERED


_DELIVERED: Final = frozenset(
    {Outcome.DELIVERED, Outcome.DELIVERED_WITH_WARNINGS, Outcome.DELIVERED_UNRECORDED}
)
_LOG_LEVELS: Final = {
    Outcome.DELIVERED: logging.INFO,
    Outcome.NO_MATCH: logging.INFO,
    Outcome.DELIVERED_WITH_WARNINGS: logging.WARNING,
    Outcome.ALREADY_RUNNING: logging.WARNING,
    Outcome.CANCELLED: logging.WARNING,
}


class Hint(enum.StrEnum):
    """User-facing hints shown in the summary line (§4.2, §12)."""

    FILTERS_TOO_RESTRICTIVE = "filters too restrictive"
    NOTHING_NEW = "nothing new left for these filters"
    LIBRARY_EMPTY = "no usable JPEG or PNG images in /media/frame_gallery/library"
    """The local library offered nothing (§9.3): the hint names its location."""
    LIMITS_REACHED = "search limits reached"
    ACCEPT_PROMPT = "accept the connection prompt on your TV, then start the app again"
    PAIRED_START_AGAIN = "paired; start the app again"
    UPLOAD_MAY_HAVE_REACHED_TV = "the upload may have reached the TV"
    STORED_ON_TV = "stored on the TV and may be displayed"


@dataclass(slots=True)
class NoDeliveryEvidence:
    """What SELECT and ATTEMPT observed, for the §4.2 classification."""

    discovery_transport_failure: bool = False
    """Discovery ended because of a provider or transport error, or a 403/429 stop."""

    attempt_transport_failure: bool = False
    """A probe or a download failed at the transport level (not 404 or 410)."""

    discovery_expired_without_candidates: bool = False
    """The discovery deadline passed before the provider returned any candidate."""

    processing_failure: bool = False
    """An attempt failed in processing: decode, render, encode, or the worker."""

    limits_reached: bool = False
    candidates_seen: int = 0
    candidates_excluded: int = 0
    library_empty: bool = False
    """The local library was scanned completely and offered no candidate."""

    pages_skipped: int = 0
    """Result pages the adapter skipped as known to offer nothing new."""


def classify_no_delivery(evidence: NoDeliveryEvidence) -> tuple[Outcome, Hint | None]:
    """The first matching rule wins: ``source_failed``, ``image_failed``, ``no_match``."""
    if (
        evidence.discovery_transport_failure
        or evidence.attempt_transport_failure
        or evidence.discovery_expired_without_candidates
    ):
        return Outcome.SOURCE_FAILED, None
    if evidence.processing_failure:
        return Outcome.IMAGE_FAILED, None
    if evidence.limits_reached:
        return Outcome.NO_MATCH, Hint.LIMITS_REACHED
    if evidence.candidates_excluded == evidence.candidates_seen and (
        evidence.candidates_seen > 0 or evidence.pages_skipped > 0
    ):
        # Everything seen was excluded, or the cache already knew that the
        # skipped pages offer nothing new (exhausted-page hints).
        return Outcome.NO_MATCH, Hint.NOTHING_NEW
    if evidence.library_empty:
        return Outcome.NO_MATCH, Hint.LIBRARY_EMPTY
    return Outcome.NO_MATCH, Hint.FILTERS_TOO_RESTRICTIVE


class LedgerAction(enum.StrEnum):
    """What happens to the write-ahead upload intent (§12.4, §13.6)."""

    REMOVE_INTENT = "remove_intent"
    """No ``upload_started`` was seen, or the upload was explicitly refused."""

    KEEP_UNCERTAIN = "keep_uncertain"
    """``upload_started`` without ``uploaded``: the quarantine applies."""

    KEEP_UPLOADED = "keep_uploaded"
    """``uploaded`` was seen: the entry was promoted and is never resent."""


@dataclass(frozen=True, slots=True)
class TelevisionVerdict:
    selected: bool
    """``selected`` was seen: the run continues to RECORD and PUBLISH."""

    outcome: Outcome | None
    """The outcome when not selected."""

    ledger: LedgerAction
    hint: Hint | None = None


_STATUS_OUTCOMES: Final = {
    DeliveryStatus.UNREACHABLE: Outcome.TV_UNREACHABLE,
    DeliveryStatus.PROTOCOL: Outcome.TV_UNREACHABLE,
    DeliveryStatus.NOT_AUTHORIZED: Outcome.TV_NOT_AUTHORIZED,
    DeliveryStatus.UNSUPPORTED: Outcome.TV_REJECTED,
    DeliveryStatus.REFUSED: Outcome.TV_REJECTED,
    DeliveryStatus.INSUFFICIENT_TIME: Outcome.DEADLINE_EXCEEDED,
    # ``ok`` without a ``selected`` marker contradicts the protocol, so it is
    # handled like a lost connection.
    DeliveryStatus.OK: Outcome.TV_UNREACHABLE,
}
_STATUS_HINTS: Final = {
    DeliveryStatus.NOT_AUTHORIZED: Hint.ACCEPT_PROMPT,
    DeliveryStatus.INSUFFICIENT_TIME: Hint.PAIRED_START_AGAIN,
}


def classify_delivery(
    markers: Collection[Marker], status: DeliveryStatus | None, *, cancelled: bool
) -> TelevisionVerdict:
    """Classify the television phase from the last marker seen (§12.4).

    ``status`` is ``None`` when no result arrived: the worker was killed by its
    timer, crashed, or the run was cancelled. The television state and the
    ledger always follow the markers; the status only names the outcome.
    """
    if Marker.SELECTED in markers:
        return TelevisionVerdict(selected=True, outcome=None, ledger=LedgerAction.KEEP_UPLOADED)
    if Marker.UPLOADED in markers:
        return _after_uploaded(status, cancelled=cancelled)
    if Marker.UPLOAD_STARTED in markers:
        return _after_upload_started(status, cancelled=cancelled)
    return _before_upload(status, cancelled=cancelled, connected=Marker.CONNECTED in markers)


def _after_uploaded(status: DeliveryStatus | None, *, cancelled: bool) -> TelevisionVerdict:
    """The TV holds the upload: the work is never uploaded again."""
    if cancelled:
        outcome = Outcome.CANCELLED
    elif status in (DeliveryStatus.REFUSED, DeliveryStatus.UNSUPPORTED):
        outcome = Outcome.TV_REJECTED
    else:
        outcome = Outcome.TV_UNREACHABLE
    hint = Hint.STORED_ON_TV if outcome is Outcome.TV_UNREACHABLE else None
    return TelevisionVerdict(
        selected=False, outcome=outcome, ledger=LedgerAction.KEEP_UPLOADED, hint=hint
    )


def _after_upload_started(status: DeliveryStatus | None, *, cancelled: bool) -> TelevisionVerdict:
    """The upload may have arrived, unless the TV explicitly refused it."""
    if status is DeliveryStatus.REFUSED:
        # An explicit refusal proves nothing was stored, even if a stop request
        # arrived meanwhile: the intent goes (§13.6 step 3).
        return TelevisionVerdict(
            selected=False,
            outcome=Outcome.CANCELLED if cancelled else Outcome.TV_REJECTED,
            ledger=LedgerAction.REMOVE_INTENT,
        )
    if cancelled:
        outcome = Outcome.CANCELLED
    elif status is None:
        outcome = Outcome.TV_UNREACHABLE
    else:
        outcome = _STATUS_OUTCOMES[status]
    hint = Hint.UPLOAD_MAY_HAVE_REACHED_TV if outcome is Outcome.TV_UNREACHABLE else None
    return TelevisionVerdict(
        selected=False, outcome=outcome, ledger=LedgerAction.KEEP_UNCERTAIN, hint=hint
    )


def _before_upload(
    status: DeliveryStatus | None, *, cancelled: bool, connected: bool
) -> TelevisionVerdict:
    """Nothing was uploaded (no ``upload_started``): the intent is removed.

    ``insufficient_time`` gets the hint "paired; start the app again" only
    after ``connected``; before it, the worker stopped without contacting the
    art channel (D-162 point 5), and nothing was paired."""
    if cancelled:
        outcome, hint = Outcome.CANCELLED, None
    elif status is None:
        outcome, hint = Outcome.TV_UNREACHABLE, None
    else:
        outcome, hint = _STATUS_OUTCOMES[status], _STATUS_HINTS.get(status)
        if status is DeliveryStatus.INSUFFICIENT_TIME and not connected:
            hint = None
    return TelevisionVerdict(
        selected=False, outcome=outcome, ledger=LedgerAction.REMOVE_INTENT, hint=hint
    )
