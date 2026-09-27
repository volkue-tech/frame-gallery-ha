"""Outcome taxonomy and classification tables (§4.2, §12.4, D-133)."""

from __future__ import annotations

import logging
from itertools import product

import pytest

from frame_gallery.app.outcomes import (
    INTERNAL_ERROR_EXIT_CODE,
    WATCHDOG_EXIT_CODE,
    Hint,
    LedgerAction,
    NoDeliveryEvidence,
    Outcome,
    classify_delivery,
    classify_no_delivery,
)
from frame_gallery.providers.local_media import LIBRARY_ROOT
from frame_gallery.tv.port import DeliveryStatus, Marker


def test_every_classified_outcome_exits_zero_except_internal_error() -> None:
    for outcome in Outcome:
        expected = 70 if outcome is Outcome.INTERNAL_ERROR else 0
        assert outcome.exit_code == expected
    assert INTERNAL_ERROR_EXIT_CODE == 70
    assert WATCHDOG_EXIT_CODE == 71


@pytest.mark.parametrize(
    ("outcome", "level"),
    [
        (Outcome.DELIVERED, logging.INFO),
        (Outcome.NO_MATCH, logging.INFO),
        (Outcome.DELIVERED_WITH_WARNINGS, logging.WARNING),
        (Outcome.ALREADY_RUNNING, logging.WARNING),
        (Outcome.CANCELLED, logging.WARNING),
        (Outcome.DELIVERED_UNRECORDED, logging.ERROR),
        (Outcome.CONFIG_INVALID, logging.ERROR),
        (Outcome.STATE_ERROR, logging.ERROR),
        (Outcome.SOURCE_FAILED, logging.ERROR),
        (Outcome.IMAGE_FAILED, logging.ERROR),
        (Outcome.TV_UNREACHABLE, logging.ERROR),
        (Outcome.TV_NOT_AUTHORIZED, logging.ERROR),
        (Outcome.TV_REJECTED, logging.ERROR),
        (Outcome.DEADLINE_EXCEEDED, logging.ERROR),
        (Outcome.INTERNAL_ERROR, logging.ERROR),
    ],
)
def test_log_levels_follow_the_taxonomy(outcome: Outcome, level: int) -> None:
    assert outcome.log_level == level


def test_delivered_outcomes() -> None:
    assert {o for o in Outcome if o.delivered} == {
        Outcome.DELIVERED,
        Outcome.DELIVERED_WITH_WARNINGS,
        Outcome.DELIVERED_UNRECORDED,
    }


# ------------------------------------------------------- no delivery (§4.2)


@pytest.mark.parametrize(
    "evidence",
    [
        NoDeliveryEvidence(discovery_transport_failure=True),
        NoDeliveryEvidence(attempt_transport_failure=True),
        NoDeliveryEvidence(discovery_expired_without_candidates=True),
        NoDeliveryEvidence(attempt_transport_failure=True, processing_failure=True),
        NoDeliveryEvidence(discovery_transport_failure=True, limits_reached=True),
    ],
)
def test_transport_failures_win_as_source_failed(evidence: NoDeliveryEvidence) -> None:
    assert classify_no_delivery(evidence) == (Outcome.SOURCE_FAILED, None)


def test_processing_failure_is_image_failed() -> None:
    evidence = NoDeliveryEvidence(processing_failure=True, limits_reached=True)
    assert classify_no_delivery(evidence) == (Outcome.IMAGE_FAILED, None)


def test_no_match_hints() -> None:
    assert classify_no_delivery(NoDeliveryEvidence(limits_reached=True)) == (
        Outcome.NO_MATCH,
        Hint.LIMITS_REACHED,
    )
    all_excluded = NoDeliveryEvidence(candidates_seen=3, candidates_excluded=3)
    assert classify_no_delivery(all_excluded) == (Outcome.NO_MATCH, Hint.NOTHING_NEW)
    some_excluded = NoDeliveryEvidence(candidates_seen=3, candidates_excluded=2)
    assert classify_no_delivery(some_excluded) == (Outcome.NO_MATCH, Hint.FILTERS_TOO_RESTRICTIVE)
    assert classify_no_delivery(NoDeliveryEvidence()) == (
        Outcome.NO_MATCH,
        Hint.FILTERS_TOO_RESTRICTIVE,
    )


def test_pages_known_to_offer_nothing_new_give_nothing_new() -> None:
    """Exhausted-page hints: the adapter skipped every page it knew to be
    exhausted, so nothing new was even seen (§9.5, §9.6, R-13)."""
    skipped = NoDeliveryEvidence(pages_skipped=4)
    assert classify_no_delivery(skipped) == (Outcome.NO_MATCH, Hint.NOTHING_NEW)
    skipped_and_excluded = NoDeliveryEvidence(
        pages_skipped=4, candidates_seen=2, candidates_excluded=2
    )
    assert classify_no_delivery(skipped_and_excluded) == (Outcome.NO_MATCH, Hint.NOTHING_NEW)
    skipped_but_rejected = NoDeliveryEvidence(
        pages_skipped=4, candidates_seen=2, candidates_excluded=1
    )
    assert classify_no_delivery(skipped_but_rejected) == (
        Outcome.NO_MATCH,
        Hint.FILTERS_TOO_RESTRICTIVE,
    )
    assert classify_no_delivery(NoDeliveryEvidence(pages_skipped=4, limits_reached=True)) == (
        Outcome.NO_MATCH,
        Hint.LIMITS_REACHED,
    )


def test_an_empty_local_library_names_its_location() -> None:
    assert classify_no_delivery(NoDeliveryEvidence(library_empty=True)) == (
        Outcome.NO_MATCH,
        Hint.LIBRARY_EMPTY,
    )
    assert str(LIBRARY_ROOT) in Hint.LIBRARY_EMPTY.value
    # Limits and failures still take precedence.
    limited = NoDeliveryEvidence(library_empty=True, limits_reached=True)
    assert classify_no_delivery(limited) == (Outcome.NO_MATCH, Hint.LIMITS_REACHED)


# ------------------------------------------------------- television (§12.4)

NONE: tuple[Marker, ...] = ()
CONNECTED = (Marker.CONNECTED,)
STARTED = (Marker.CONNECTED, Marker.UPLOAD_STARTED)
UPLOADED = (*STARTED, Marker.UPLOADED)
SELECTED = (*UPLOADED, Marker.SELECTED)
STATUSES: tuple[DeliveryStatus | None, ...] = (None, *DeliveryStatus)


@pytest.mark.parametrize(("status", "cancelled"), list(product(STATUSES, [False, True])))
def test_selected_always_wins(status: DeliveryStatus | None, cancelled: bool) -> None:
    verdict = classify_delivery(SELECTED, status, cancelled=cancelled)
    assert verdict.selected
    assert verdict.outcome is None
    assert verdict.ledger is LedgerAction.KEEP_UPLOADED


@pytest.mark.parametrize(("status", "cancelled"), list(product(STATUSES, [False, True])))
def test_uploaded_is_never_resent(status: DeliveryStatus | None, cancelled: bool) -> None:
    verdict = classify_delivery(UPLOADED, status, cancelled=cancelled)
    assert not verdict.selected
    assert verdict.ledger is LedgerAction.KEEP_UPLOADED
    if cancelled:
        assert verdict.outcome is Outcome.CANCELLED
    elif status in (DeliveryStatus.REFUSED, DeliveryStatus.UNSUPPORTED):
        assert verdict.outcome is Outcome.TV_REJECTED
        assert verdict.hint is None
    else:
        assert verdict.outcome is Outcome.TV_UNREACHABLE
        assert verdict.hint is Hint.STORED_ON_TV


_Q = LedgerAction.KEEP_UNCERTAIN
_MAY = Hint.UPLOAD_MAY_HAVE_REACHED_TV


@pytest.mark.parametrize(
    ("status", "outcome", "ledger", "hint"),
    [
        (None, Outcome.TV_UNREACHABLE, _Q, _MAY),
        (DeliveryStatus.UNREACHABLE, Outcome.TV_UNREACHABLE, _Q, _MAY),
        (DeliveryStatus.PROTOCOL, Outcome.TV_UNREACHABLE, _Q, _MAY),
        (DeliveryStatus.OK, Outcome.TV_UNREACHABLE, _Q, _MAY),
        (DeliveryStatus.REFUSED, Outcome.TV_REJECTED, LedgerAction.REMOVE_INTENT, None),
        # The worker reports these only before ``upload_started`` (§12.1); if one
        # arrives after it, the upload may have happened, so the quarantine holds
        # and the status still names the outcome (D-141).
        (DeliveryStatus.NOT_AUTHORIZED, Outcome.TV_NOT_AUTHORIZED, _Q, None),
        (DeliveryStatus.UNSUPPORTED, Outcome.TV_REJECTED, _Q, None),
        (DeliveryStatus.INSUFFICIENT_TIME, Outcome.DEADLINE_EXCEEDED, _Q, None),
    ],
)
def test_upload_started_quarantines_unless_refused(
    status: DeliveryStatus | None, outcome: Outcome, ledger: LedgerAction, hint: Hint | None
) -> None:
    verdict = classify_delivery(STARTED, status, cancelled=False)
    assert verdict == verdict.__class__(selected=False, outcome=outcome, ledger=ledger, hint=hint)


@pytest.mark.parametrize("status", STATUSES)
def test_cancelled_after_upload_started_keeps_the_quarantine_unless_refused(
    status: DeliveryStatus | None,
) -> None:
    verdict = classify_delivery(STARTED, status, cancelled=True)
    assert verdict.outcome is Outcome.CANCELLED
    expected = (
        LedgerAction.REMOVE_INTENT
        if status is DeliveryStatus.REFUSED
        else LedgerAction.KEEP_UNCERTAIN
    )
    assert verdict.ledger is expected
    assert verdict.hint is None


@pytest.mark.parametrize("markers", [NONE, CONNECTED])
@pytest.mark.parametrize(
    ("status", "outcome", "hint"),
    [
        (None, Outcome.TV_UNREACHABLE, None),
        (DeliveryStatus.UNREACHABLE, Outcome.TV_UNREACHABLE, None),
        (DeliveryStatus.PROTOCOL, Outcome.TV_UNREACHABLE, None),
        (DeliveryStatus.OK, Outcome.TV_UNREACHABLE, None),
        (DeliveryStatus.NOT_AUTHORIZED, Outcome.TV_NOT_AUTHORIZED, Hint.ACCEPT_PROMPT),
        (DeliveryStatus.UNSUPPORTED, Outcome.TV_REJECTED, None),
        (DeliveryStatus.REFUSED, Outcome.TV_REJECTED, None),
        (DeliveryStatus.INSUFFICIENT_TIME, Outcome.DEADLINE_EXCEEDED, Hint.PAIRED_START_AGAIN),
    ],
)
def test_before_upload_the_intent_is_removed(
    markers: tuple[Marker, ...],
    status: DeliveryStatus | None,
    outcome: Outcome,
    hint: Hint | None,
) -> None:
    if status is DeliveryStatus.INSUFFICIENT_TIME and Marker.CONNECTED not in markers:
        hint = None  # nothing was paired before the art channel was reached
    verdict = classify_delivery(markers, status, cancelled=False)
    assert verdict == verdict.__class__(
        selected=False, outcome=outcome, ledger=LedgerAction.REMOVE_INTENT, hint=hint
    )


@pytest.mark.parametrize("markers", [NONE, CONNECTED])
def test_cancelled_before_upload_removes_the_intent(markers: tuple[Marker, ...]) -> None:
    verdict = classify_delivery(markers, None, cancelled=True)
    assert verdict.outcome is Outcome.CANCELLED
    assert verdict.ledger is LedgerAction.REMOVE_INTENT
