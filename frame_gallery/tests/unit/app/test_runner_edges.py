"""Runner edge cases found in the Phase 2 review: stop requests at every
awkward moment, port failures after ``selected``, FINISH robustness, and
classification details (§4.2, §7.6, §12.3, §12.4, §13.6)."""

from __future__ import annotations

import contextlib
import logging
import os
import signal
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import pytest

from frame_gallery.app import runner as runner_module
from frame_gallery.app.outcomes import Hint, Outcome
from frame_gallery.app.ports import FetchedImage, ProviderBinding
from frame_gallery.app.runner import Stage
from frame_gallery.app.signals import CancellationController, install_sigterm_handler
from frame_gallery.budget.allowance import AllowanceExhausted
from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.domain import Size, SourceKey
from frame_gallery.errors import Cancelled, StateError
from frame_gallery.imaging.contract import DeliveryArtifact
from frame_gallery.isolation.executor import WorkerError, WorkerErrorKind
from frame_gallery.providers.contract import (
    Candidate,
    DimensionSource,
    ImageRef,
    SourceError,
    SourceErrorKind,
)
from frame_gallery.providers.rights import RightsBasis
from frame_gallery.tv.port import (
    DeliveryRequest,
    DeliveryResult,
    DeliveryStatus,
    Marker,
    MarkerSink,
)
from tests.support.clock import FakeClock
from tests.support.fakes import make_candidate
from tests.unit.app.harness import Harness

ALL = [Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED, Marker.SELECTED]


@pytest.fixture
def h(tmp_path: Path) -> Harness:
    return Harness(tmp_path)


# ------------------------------------------------ stop requests (§7.6)


def test_a_stop_swallowed_by_a_port_is_honoured_at_the_next_stage(h: Harness) -> None:
    """A port that swallows even BaseException cannot lose the stop request:
    the next stage boundary re-checks it, before any TV contact."""
    original = h.provider._generate

    def swallowing() -> Iterator[Candidate]:
        with contextlib.suppress(BaseException):  # the defect under test
            h.cancellation.request_stop()
        yield from original()

    h.provider._generate = swallowing  # type: ignore[method-assign]
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert "tv.deliver" not in h.events
    assert h.state.ledger == {}


def test_a_stop_cannot_be_swallowed_by_except_exception(h: Harness) -> None:
    """``Cancelled`` is a BaseException: ``except Exception`` never absorbs it."""
    original = h.provider._generate

    def generic_handler() -> Iterator[Candidate]:
        with contextlib.suppress(Exception):  # a typical adapter or logging handler
            h.cancellation.request_stop()
        yield from original()

    h.provider._generate = generic_handler  # type: ignore[method-assign]
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert "tv.deliver" not in h.events


def test_a_stop_during_the_promotion_completes_it_then_cancels(h: Harness) -> None:
    """§7.6: after ``uploaded`` the ledger holds ``uploaded``, even when the stop
    arrives while the promotion is being written."""
    original = h.state.promote_upload

    def stop_during_write(qualified_id: str, now: datetime) -> None:
        h.cancellation.request_stop()  # deferred: must not interrupt the write
        original(qualified_id, now)

    h.state.promote_upload = stop_during_write  # type: ignore[method-assign]
    h.tv.markers = [Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED]
    h.tv.status = DeliveryStatus.REFUSED
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert h.state.ledger == {"aic:1001": "uploaded"}
    assert h.state.history == []


def test_a_stop_during_the_intent_removal_does_not_leave_a_quarantine(h: Harness) -> None:
    """D-137: without ``upload_started`` the intent is removed, stop or not."""
    original = h.state.remove_upload_intent

    def stop_during_removal(qualified_id: str) -> None:
        h.cancellation.request_stop()  # deferred: the outcome is already decided
        original(qualified_id)

    h.state.remove_upload_intent = stop_during_removal  # type: ignore[method-assign]
    h.tv.markers = [Marker.CONNECTED]
    h.tv.status = DeliveryStatus.UNREACHABLE
    result = h.run()
    assert result.outcome is Outcome.TV_UNREACHABLE
    assert h.state.ledger == {}


def test_selected_only_in_the_result_survives_a_stop_during_its_promotion(h: Harness) -> None:
    """§12.3: an adapter that reports every marker only in its result still gets
    RECORD, even when a stop arrives while the promotion is written."""
    h.tv.markers = []
    original_deliver = h.tv.deliver

    def report_only(request: DeliveryRequest, on_marker: MarkerSink) -> DeliveryResult:
        original_deliver(request, on_marker)
        return DeliveryResult(status=DeliveryStatus.OK, markers_seen=tuple(ALL))

    original_promote = h.state.promote_upload

    def stop_during_write(qualified_id: str, now: datetime) -> None:
        h.cancellation.request_stop()
        original_promote(qualified_id, now)

    h.tv.deliver = report_only  # type: ignore[method-assign]
    h.state.promote_upload = stop_during_write  # type: ignore[method-assign]
    result = h.run()
    assert result.outcome is Outcome.DELIVERED_WITH_WARNINGS  # PUBLISH skipped
    assert h.state.history == ["aic:1001"]
    assert h.state.ledger == {"aic:1001": "uploaded"}


def test_workers_are_killed_before_an_interrupted_delivery_is_classified(h: Harness) -> None:
    """§7.6: the worker group is killed before the markers are read."""
    h.tv.markers = [Marker.CONNECTED]
    h.tv.error = Cancelled()
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert h.events.before("executor.terminate_all", "state.remove_intent:aic:1001")


def test_a_stop_while_arming_the_watchdog_is_still_a_classified_run(h: Harness) -> None:
    def stop_on_arm() -> None:
        h.events.append("watchdog.arm")
        h.cancellation.request_stop()

    h.watchdog.arm = stop_on_arm  # type: ignore[method-assign]
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert h.records.last_run[0]["outcome"] == "cancelled"
    assert result.summary_line.startswith("outcome=cancelled")


def test_a_controller_serves_exactly_one_run(h: Harness) -> None:
    h.run()
    with pytest.raises(RuntimeError, match="exactly one run"):
        h.run()
    h.cancellation = CancellationController()
    assert h.run().delivered_id == "aic:1002"


# ------------------------------------------- failures after ``selected``


def test_an_adapter_failure_after_selected_still_records(h: Harness) -> None:
    """§12.3: after ``selected``, RECORD always runs."""
    h.tv.error = RuntimeError("the channel broke after selected")
    result = h.run()
    assert result.outcome is Outcome.DELIVERED_WITH_WARNINGS
    assert h.state.history == ["aic:1001"]
    assert h.state.ledger == {"aic:1001": "uploaded"}
    assert Stage.RECORD in result.stages


def test_an_adapter_failure_after_uploaded_is_internal_error(h: Harness) -> None:
    h.tv.markers = [Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED]
    h.tv.error = WorkerError(WorkerErrorKind.PROTOCOL, "bad result")
    result = h.run()
    assert result.outcome is Outcome.INTERNAL_ERROR
    assert h.state.ledger == {"aic:1001": "uploaded"}
    assert h.state.history == []
    assert h.events.before("executor.terminate_all", "records.last_run")


def test_an_internal_error_after_selected_still_records_history(h: Harness) -> None:
    """An error between DELIVER and RECORD: RECORD runs from the settle step,
    and the run reports the error with history +1 (§4.2)."""
    original = h.tv.deliver

    def deliver_then_break(request: DeliveryRequest, on_marker: MarkerSink) -> DeliveryResult:
        result = original(request, on_marker)
        h.state.fail["record_history"] = RuntimeError("store bug")
        return result

    h.tv.deliver = deliver_then_break  # type: ignore[method-assign]
    result = h.run()
    assert result.outcome is Outcome.INTERNAL_ERROR
    assert h.events.count("state.record_history") == 1


def test_selected_without_uploaded_is_promoted(h: Harness) -> None:
    h.tv.markers = [Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.SELECTED]
    h.state.fail["record_history"] = StateError("rename failed")
    result = h.run()
    assert result.outcome is Outcome.DELIVERED_UNRECORDED
    assert h.state.ledger == {"aic:1001": "uploaded"}


# ------------------------------------------------ settle and FINISH


def test_an_unexpected_ledger_error_keeps_the_intent_and_the_outcome(
    h: Harness, caplog: pytest.LogCaptureFixture
) -> None:
    """A store that breaks its contract while removing an intent: the work stays
    in quarantine (the conservative side) and the error is logged in full."""
    h.state.fail["commit_intent"] = StateError("read-only")
    h.state.fail["remove_intent"] = OSError("EIO")
    with caplog.at_level(logging.ERROR, logger=h.logger.name):
        result = h.run()
    assert result.outcome is Outcome.STATE_ERROR
    assert "stays in quarantine" in caplog.text
    assert "Traceback" in caplog.text


def test_a_port_breaking_its_contract_while_settling_is_classified(
    h: Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_discard() -> None:
        raise OSError("EIO")

    monkeypatch.setattr(h.state, "discard_prestaged_history", broken_discard)
    h.state.fail["commit_intent"] = StateError("read-only")
    result = h.run()
    assert result.outcome is Outcome.INTERNAL_ERROR
    assert h.records.last_run[0]["outcome"] == "internal_error"


def test_an_internal_error_between_selected_and_record_still_records(
    h: Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """§12.3: the settle step runs RECORD when the stage sequence broke after
    ``selected`` but before RECORD; the run still reports the error."""

    def broken_classifier(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("classifier bug")

    monkeypatch.setattr(runner_module, "classify_delivery", broken_classifier)
    result = h.run()
    assert result.outcome is Outcome.INTERNAL_ERROR
    assert h.state.history == ["aic:1001"]
    assert Stage.RECORD in result.stages


def test_a_failure_to_kill_the_workers_is_logged_and_the_run_goes_on(
    h: Harness, caplog: pytest.LogCaptureFixture
) -> None:
    def broken_terminate() -> None:
        raise OSError("ESRCH")

    h.executor.terminate_all = broken_terminate  # type: ignore[method-assign]
    h.tv.markers = [Marker.CONNECTED]
    h.tv.error = Cancelled()
    with caplog.at_level(logging.ERROR, logger=h.logger.name):
        result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert "terminating the workers failed" in caplog.text
    assert h.state.ledger == {}


def test_an_unexpected_record_failure_never_loses_the_summary(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    h = Harness(tmp_path, candidates=[])
    h.records.last_run_error = OSError("EIO")
    with caplog.at_level(logging.INFO, logger=h.logger.name):
        result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert "outcome=no_match" in caplog.text


def test_a_failing_finish_still_ends_with_a_classified_line(
    h: Harness, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_record(**_fields: object) -> dict[str, object]:
        raise RuntimeError("bug in FINISH")

    monkeypatch.setattr(runner_module, "build_last_run_record", broken_record)
    with caplog.at_level(logging.ERROR, logger=h.logger.name):
        result = h.run()
    assert result.outcome is Outcome.INTERNAL_ERROR
    assert result.exit_code == 70
    assert result.summary_line.startswith("outcome=internal_error exit=70")
    assert h.watchdog.disarmed


def test_finish_after_a_prestage_outcome_keeps_its_own_reserve(h: Harness) -> None:
    """§7.3: a PRE-STAGE outcome after 70 s still gets FINISH's time, so the
    last-run record is written (the content window has long expired)."""
    h.state.delays["prestage"] = 71.0
    result = h.run()
    assert result.outcome is Outcome.DEADLINE_EXCEEDED
    assert h.records.remaining["last_run"] > 0
    assert h.records.last_run[0]["outcome"] == "deadline_exceeded"


# ------------------------------------------------ classification


def test_a_provider_timing_out_on_its_first_call_is_source_failed(h: Harness) -> None:
    h.provider.call_error = DeadlineExceeded("discovery")
    assert h.run().outcome is Outcome.SOURCE_FAILED


def test_a_deadline_escaping_the_content_window_is_limits_reached(h: Harness) -> None:
    h.workspace.error = DeadlineExceeded("attempts")
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert result.hint == Hint.LIMITS_REACHED


class TickingClock(FakeClock):
    """Real time passes between two readings, as with any real clock."""

    def monotonic(self) -> float:
        self.advance(1e-6)
        return super().monotonic()


def test_a_worker_timeout_at_its_own_limit_is_image_failed_with_a_real_clock(
    tmp_path: Path,
) -> None:
    """§4.2 rule 2: a worker timeout is a processing failure, even when the
    clamped timeout is a hair below 15 s because the clock moved."""
    h = Harness(tmp_path, clock=TickingClock())
    h.executor.behaviours = [WorkerError(WorkerErrorKind.TIMEOUT)] * 2
    result = h.run()
    assert result.outcome is Outcome.IMAGE_FAILED
    assert all(timeout < 15.0 for timeout in h.executor.timeouts)


class FailingProbe:
    def __init__(self, source: DimensionSource, error: SourceError) -> None:
        self._source = source
        self.error = error

    @property
    def source(self) -> DimensionSource:
        return self._source

    def measure(self, candidate: Candidate, deadline: Deadline) -> Size | None:
        raise self.error


def _probe_harness(tmp_path: Path, probe: FailingProbe) -> Harness:
    h = Harness(tmp_path, candidates=[make_candidate("1", size=None)])
    providers = h.providers()

    def with_probe() -> dict[SourceKey, ProviderBinding]:
        bound = dict(providers)
        bound[SourceKey.ART_INSTITUTE_CHICAGO] = ProviderBinding(h.provider, probe=probe)
        return bound

    h.providers = with_probe  # type: ignore[method-assign]
    return h


def test_a_probe_transport_failure_is_source_failed(tmp_path: Path) -> None:
    """§4.2 rule 1: a probe that fails at the transport level."""
    probe = FailingProbe(DimensionSource.REMOTE_PROBE, SourceError(SourceErrorKind.TRANSPORT))
    assert _probe_harness(tmp_path, probe).run().outcome is Outcome.SOURCE_FAILED


def test_a_probe_not_found_is_no_match(tmp_path: Path) -> None:
    probe = FailingProbe(DimensionSource.REMOTE_PROBE, SourceError(SourceErrorKind.NOT_FOUND))
    assert _probe_harness(tmp_path, probe).run().outcome is Outcome.NO_MATCH


def test_a_local_inspection_failure_is_not_a_source_failure(tmp_path: Path) -> None:
    probe = FailingProbe(
        DimensionSource.LOCAL_INSPECTION, SourceError(SourceErrorKind.UNEXPECTED_FORMAT)
    )
    assert _probe_harness(tmp_path, probe).run().outcome is Outcome.NO_MATCH


def test_the_rights_allowlist_of_the_source_is_applied(h: Harness) -> None:
    """D-134: a user-supplied work is never delivered from a museum source."""
    h.provider.candidates = [
        make_candidate("1001", rights=RightsBasis.USER_SUPPLIED),
        make_candidate("1002"),
    ]
    result = h.run()
    assert result.delivered_id == "aic:1002"
    assert h.last_run["stats"]["selection"]["rights_rejected"] == 1  # type: ignore[index]


def test_debug_logs_one_decision_per_candidate(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """§19: DEBUG adds per-candidate decisions."""
    h = Harness(
        tmp_path,
        candidates=[make_candidate("1", size=Size(800, 1200)), make_candidate("2")],
    )
    h.logger.setLevel(logging.DEBUG)
    try:
        with caplog.at_level(logging.DEBUG, logger=h.logger.name):
            h.run()
    finally:
        h.logger.setLevel(logging.NOTSET)
    assert "candidate aic:1: rejected:not_landscape" in caplog.text
    assert "candidate aic:2: shortlisted:strict" in caplog.text


def test_no_decision_logging_without_debug(h: Harness, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger=h.logger.name):
        h.run()
    assert "candidate aic:" not in caplog.text


# ------------------------------------------- re-verification regressions


def test_a_stop_at_upload_started_keeps_the_marker_and_the_quarantine(h: Harness) -> None:
    """A stop while the TV works is only recorded: the adapter stops, relays the
    markers seen, and the run is cancelled with the quarantine intact (F1)."""

    def stop_at(marker: Marker) -> None:
        if marker is Marker.UPLOAD_STARTED:
            h.cancellation.request_stop()  # deferred during the TV call

    h.tv.during = stop_at
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert "tv.stopped" in h.events
    assert h.state.ledger == {"aic:1001": "uncertain"}
    assert h.state.history == []


def test_a_stop_after_selected_in_the_call_still_records(h: Harness) -> None:
    def stop_at(marker: Marker) -> None:
        if marker is Marker.SELECTED:
            h.cancellation.request_stop()

    h.tv.during = stop_at
    result = h.run()
    assert result.outcome is Outcome.DELIVERED_WITH_WARNINGS
    assert h.state.history == ["aic:1001"]


def test_a_real_sigterm_in_the_marker_callback_loses_nothing(h: Harness) -> None:
    """F1/F2: a real SIGTERM during the TV call is deferred for the whole call."""
    original = h.state.promote_upload

    def signal_during_promotion(qualified_id: str, now: datetime) -> None:
        os.kill(os.getpid(), signal.SIGTERM)
        original(qualified_id, now)

    h.state.promote_upload = signal_during_promotion  # type: ignore[method-assign]
    restore = install_sigterm_handler(h.cancellation)
    try:
        result = h.run()
    finally:
        restore()
    # The stop arrived while ``uploaded`` was being promoted; the fake TV then
    # stops after that marker: nothing is lost, and the work is never resent.
    assert result.outcome is Outcome.CANCELLED
    assert h.state.ledger == {"aic:1001": "uploaded"}


def test_a_stop_the_adapter_absorbs_is_still_classified_as_cancelled(h: Harness) -> None:
    """F5: the adapter kills its worker and returns; the run is cancelled."""
    original = h.tv.deliver

    def absorb(request: DeliveryRequest, on_marker: MarkerSink) -> DeliveryResult:
        h.cancellation.request_stop()  # deferred: recorded only
        original(request, on_marker)
        return DeliveryResult(status=DeliveryStatus.UNREACHABLE, markers_seen=(Marker.CONNECTED,))

    h.tv.markers = [Marker.CONNECTED]
    h.tv.deliver = absorb  # type: ignore[method-assign]
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert h.state.ledger == {}


def test_a_refused_upload_removes_the_intent_even_when_a_stop_is_pending(h: Harness) -> None:
    def stop_at(marker: Marker) -> None:
        if marker is Marker.UPLOAD_STARTED:
            h.cancellation.request_stop()

    original = h.tv.deliver

    def refuse(request: DeliveryRequest, on_marker: MarkerSink) -> DeliveryResult:
        original(request, on_marker)
        return DeliveryResult(
            status=DeliveryStatus.REFUSED,
            markers_seen=(Marker.CONNECTED, Marker.UPLOAD_STARTED),
        )

    h.tv.markers = [Marker.CONNECTED, Marker.UPLOAD_STARTED]
    h.tv.during = stop_at
    h.tv.deliver = refuse  # type: ignore[method-assign]
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert h.state.ledger == {}


def test_a_stop_before_the_run_starts_is_honoured_inside_it(h: Harness) -> None:
    """F4: the entry point creates the controller deferred, so a stop that
    arrives before the run is ready is classified, not escaped."""
    h.cancellation = CancellationController(start_deferred=True)
    h.cancellation.request_stop()  # recorded only
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert result.stages == (Stage.FINISH,)
    assert h.records.last_run[0]["outcome"] == "cancelled"
    assert "watchdog.arm" not in h.events
    assert h.watchdog.disarmed


def test_an_interrupted_prestage_is_discarded(h: Harness) -> None:
    """F6: the port may have written the generation before the stop arrived."""
    original = h.state.prestage_history

    def write_then_stop(qualified_id: str, now: datetime) -> None:
        original(qualified_id, now)
        h.cancellation.request_stop()

    h.state.prestage_history = write_then_stop  # type: ignore[method-assign]
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert h.state.prestaged is None
    assert "state.discard_prestaged" in h.events


def test_a_slow_preview_leaves_time_for_the_last_run_record(h: Harness) -> None:
    """F7: PUBLISH cannot use FINISH's last seconds."""
    original = h.preview.publish

    def slow_publish(artifact: DeliveryArtifact, deadline: Deadline) -> None:
        h.clock.advance_to(deadline.expires_at)
        original(artifact, deadline)

    h.preview.publish = slow_publish  # type: ignore[method-assign]
    result = h.run()
    assert result.outcome is Outcome.DELIVERED_WITH_WARNINGS
    assert h.records.remaining["last_run"] == pytest.approx(2.0)
    assert h.records.last_run


def test_a_swallowed_stop_is_honoured_before_the_next_attempt(h: Harness) -> None:
    """F8: the attempt loop re-checks before starting new work."""
    original = h.fetcher.fetch

    def swallowing_fetch(ref: ImageRef, destination: Path, deadline: Deadline) -> FetchedImage:
        with contextlib.suppress(BaseException):
            h.cancellation.request_stop()
        raise SourceError(SourceErrorKind.NOT_FOUND)

    h.fetcher.fetch = swallowing_fetch  # type: ignore[method-assign]
    del original
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert [e for e in h.events if e.startswith("executor.run")] == []


def test_a_watchdog_that_fired_first_keeps_the_only_summary_line(
    h: Harness, caplog: pytest.LogCaptureFixture
) -> None:
    """§19: exactly one summary line; the watchdog's, when it claimed the run."""
    h.watchdog.fired = True
    with caplog.at_level(logging.INFO, logger=h.logger.name):
        result = h.run()
    assert not result.summary_emitted
    assert "outcome=" not in caplog.text


def test_a_no_delivery_finish_never_gets_a_sliver_of_the_window(tmp_path: Path) -> None:
    """P3: an overrun leaving less than the 2 s reserve gives FINISH its own time."""
    h = Harness(tmp_path, candidates=[make_candidate("1")])
    h.options.delay_s = 10.0
    h.fetcher.failures = {"1": SourceError(SourceErrorKind.NOT_FOUND)}
    h.fetcher.delay_s = 59.95  # overruns its download deadline (no pre-emption)
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert h.records.deadlines["last_run"].name == "finish"
    assert h.records.remaining["last_run"] == pytest.approx(10.0)


def test_the_chosen_line_puts_the_digest_before_untrusted_text(
    h: Harness, caplog: pytest.LogCaptureFixture
) -> None:
    h.provider.candidates = [make_candidate("1001", title="Fortune Cookie: Still Life")]
    with caplog.at_level(logging.INFO, logger=h.logger.name):
        h.run()
    chosen = next(r.getMessage() for r in caplog.records if r.getMessage().startswith("chosen:"))
    assert chosen.startswith("chosen: aic:1001 (strict) sha256=")


def test_a_failing_watchdog_disarm_is_logged_and_the_summary_still_appears(
    h: Harness, caplog: pytest.LogCaptureFixture
) -> None:
    def broken_disarm() -> bool:
        raise RuntimeError("thread state")

    h.watchdog.disarm = broken_disarm  # type: ignore[method-assign]
    with caplog.at_level(logging.INFO, logger=h.logger.name):
        result = h.run()
    assert result.summary_emitted
    assert "cleanup step failed" in caplog.text
    assert result.summary_line in caplog.text


def test_a_library_cut_short_by_its_entry_limit_is_a_search_limit(tmp_path: Path) -> None:
    """The local scan stopped at its 20 000-entry limit before finding a usable
    image: "search limits reached", never "no usable images" (review finding)."""
    h = Harness(tmp_path, raw={"tv_host": "10.0.0.5", "source": "local_media"})
    h.local_provider.error = AllowanceExhausted("local_directory_entries")
    h.local_provider.raise_at = 0
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert result.hint == Hint.LIMITS_REACHED
