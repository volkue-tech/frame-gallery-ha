"""The run orchestrator against fakes (§4.1, §4.2, §7, §12.4; C7, C11, E4, E7-E10, F1, F2)."""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterator, Mapping
from datetime import datetime
from pathlib import Path

import pytest

from frame_gallery.app.outcomes import Hint, Outcome
from frame_gallery.app.ports import ProviderBinding
from frame_gallery.app.runner import Stage
from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.budget.phases import LAST_RUN_RESERVE_S, PREPARE_S
from frame_gallery.config.filters import FilterField
from frame_gallery.config.options import LogLevel
from frame_gallery.domain import Size, SourceKey
from frame_gallery.errors import AlreadyRunning, Cancelled, PublishError, StateError
from frame_gallery.imaging.contract import (
    ImageFormat,
    PrepareFailure,
    PrepareRequest,
    PrepareResult,
    PrepareStatus,
)
from frame_gallery.isolation.executor import JsonObject, WorkerError, WorkerErrorKind
from frame_gallery.providers.contract import Candidate, SourceError, SourceErrorKind
from frame_gallery.selection.exclusion import ExclusionSet
from frame_gallery.selection.geometry import Rejection
from frame_gallery.tv.port import (
    DeliveryRequest,
    DeliveryResult,
    DeliveryStatus,
    Marker,
    MarkerSink,
)
from tests.support.fakes import FakeCacheWriter, canvas_jpeg_bytes, make_candidate
from tests.unit.app.harness import SYNTHETIC_VOCABULARY, Harness

ALL_STAGES = (
    Stage.CONFIGURE,
    Stage.RESOLVE_FILTERS,
    Stage.SELECT,
    Stage.ATTEMPT,
    Stage.PRE_STAGE,
    Stage.DELIVER,
    Stage.RECORD,
    Stage.PUBLISH,
    Stage.FINISH,
)


@pytest.fixture
def h(tmp_path: Path) -> Harness:
    return Harness(tmp_path)


def assert_cleaned_up(h: Harness) -> None:
    """Every path ends in CLEANUP (§4.1, §14, F1, F2)."""
    assert "executor.terminate_all" in h.events
    assert h.workspace.removed == 1
    assert not h.workspace.root.exists()
    assert h.state.closed
    assert h.watchdog.armed
    assert h.watchdog.disarmed


def assert_tv_untouched(h: Harness) -> None:
    assert "tv.deliver" not in h.events
    assert h.state.history == []
    assert h.state.ledger == {}
    assert h.preview.published == []
    assert h.records.current == []


# ---------------------------------------------------------------- success


def test_delivered_runs_every_stage_in_order(h: Harness) -> None:
    result = h.run()

    assert result.outcome is Outcome.DELIVERED
    assert result.exit_code == 0
    assert result.stages == ALL_STAGES
    assert result.delivered_id == "aic:1001"
    assert h.state.history == ["aic:1001"]
    assert h.state.ledger == {"aic:1001": "uploaded"}
    assert_cleaned_up(h)


def test_delivered_event_order_follows_the_lifecycle(h: Harness) -> None:
    h.run()
    order = [
        "watchdog.arm",
        "state.open",
        "options.load",
        "state.load_exclusions",
        "provider.iter",
        "workspace.create",
        "fetch:1001",
        "executor.run:prepare",
        "state.prestage:aic:1001",
        "state.commit_intent:aic:1001",
        "tv.deliver",
        "state.promote:aic:1001",
        "state.record_history",
        "preview.publish",
        "records.current",
        "records.last_run",
        "executor.terminate_all",
        "workspace.remove",
        "state.close",
        "watchdog.disarm",
    ]
    positions = [h.events.index(event) for event in order]
    assert positions == sorted(positions)
    # History is recorded before the preview is published (D-113, accepted).
    assert h.events.before("state.record_history", "preview.publish")
    # The intent is committed only after the pre-staged history (§4.1).
    assert h.events.before("state.prestage:aic:1001", "state.commit_intent:aic:1001")


def test_preview_bytes_equal_the_television_payload(h: Harness) -> None:
    """One file and one SHA-256 serve the TV, the preview, and the record (D8)."""
    h.run()
    assert h.tv.payloads == [canvas_jpeg_bytes()]
    assert h.preview.published == h.tv.payloads
    digest = hashlib.sha256(canvas_jpeg_bytes()).hexdigest()
    assert h.preview.artifacts[0].sha256 == digest
    assert h.records.current[0]["sha256"] == digest
    assert h.records.current[0]["id"] == "aic:1001"


def test_summary_line_and_last_run_record(h: Harness, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger=h.logger.name):
        result = h.run()
    assert result.summary_line.startswith("outcome=delivered exit=0 elapsed=")
    assert result.summary_line in caplog.text
    record = h.last_run
    assert record["outcome"] == "delivered"
    assert record["exit_code"] == 0
    assert record["artwork"] == "aic:1001"
    assert record["ignored_filters"] == []


def test_the_log_level_option_is_applied(tmp_path: Path) -> None:
    h = Harness(tmp_path, raw={"tv_host": "10.0.0.5", "log_level": "debug"})
    h.run()
    assert h.log_levels == [LogLevel.DEBUG]


# -------------------------------------------------------- deadline propagation


def test_deadlines_propagate_to_every_port(h: Harness) -> None:
    h.options.delay_s = 4.0  # CONFIGURE takes 4 s
    start = h.clock.monotonic()
    h.run()

    configure = h.state.deadlines["open"]
    assert configure.expires_at == pytest.approx(start + 10)
    discovery = h.provider.contexts[0].deadline
    assert discovery.name == "discovery"
    # The content window opens at +4 s; discovery ends at most 30 s into it.
    assert discovery.expires_at == pytest.approx(start + 4 + 30)
    download = h.fetcher.deadlines[0]
    assert download.expires_at == pytest.approx(start + 4 + 20)
    assert h.executor.timeouts == [PREPARE_S]
    deliver = h.tv.requests[0].deadline
    assert deliver.name == "deliver"
    assert deliver.expires_at == pytest.approx(start + 4 + 40)
    # The options are read under the CONFIGURE deadline.
    assert h.options.deadline is configure
    # RECORD starts at +4 s: FINISH gets its own 10 s, shared by every FINISH port.
    finish = h.records.deadlines["last_run"]
    assert finish.name == "finish"
    assert finish.expires_at == pytest.approx(start + 4 + 10)
    # PUBLISH (preview and current record) keeps FINISH's last 2 s for last_run.
    publish = h.preview.deadline
    assert publish is not None
    assert publish.name == "publish"
    assert publish.expires_at == pytest.approx(finish.expires_at - 2)
    assert h.records.deadlines["current"] is publish


def test_helpers_are_read_under_the_configure_deadline(tmp_path: Path) -> None:
    h = Harness(
        tmp_path,
        raw={"tv_host": "10.0.0.5", "color_helper": "input_select.fg_colour"},
        vocabulary=SYNTHETIC_VOCABULARY,
    )
    start = h.clock.monotonic()
    h.run()
    assert h.helpers.deadline is h.state.deadlines["open"]
    assert h.helpers.deadline is not None
    assert h.helpers.deadline.expires_at == pytest.approx(start + 10)


def test_deliver_is_clamped_by_the_total_when_it_starts_late(h: Harness) -> None:
    """A stalled intent write ends PRE-STAGE at 75 s: 45 s remain. DELIVER gets
    45 - 10 = 35 s, not 40 s, so FINISH's 10 s reserve survives (§7.1, §7.3)."""
    h.state.delays["commit_intent"] = 75.0
    start = h.clock.monotonic()
    h.run()
    deliver = h.tv.requests[0].deadline
    assert deliver.expires_at == pytest.approx(start + 110)
    # The TV answers at once, so RECORD starts at 75 s with its own 10 s.
    finish = h.records.deadlines["last_run"]
    assert finish.expires_at == pytest.approx(start + 85)


def test_prepare_timeout_is_clamped_to_the_content_window(h: Harness) -> None:
    # Discovery uses 50 s of the window (starting at +0): 8 s remain before the
    # PRE-STAGE reserve, so the 15 s prepare budget is clamped.
    h.provider.per_candidate_s = 50.0
    h.provider.candidates = [make_candidate("1001")]
    h.run()
    assert h.executor.timeouts[0] == pytest.approx(8.0)
    assert h.executor.timeouts[0] < PREPARE_S


def test_the_television_address_reaches_the_port(tmp_path: Path) -> None:
    h = Harness(tmp_path, raw={"tv_host": "172.16.4.2"})
    h.run()
    assert str(h.tv.requests[0].tv_host) == "172.16.4.2"


# ------------------------------------------------------ CONFIGURE outcomes


def test_missing_tv_host_is_config_invalid(tmp_path: Path) -> None:
    h = Harness(tmp_path, raw={})
    result = h.run()
    assert result.outcome is Outcome.CONFIG_INVALID
    assert result.exit_code == 0
    assert result.stages == (Stage.CONFIGURE, Stage.FINISH)
    assert "provider.iter" not in h.events
    assert_tv_untouched(h)
    assert h.last_run["outcome"] == "config_invalid"
    assert h.state.closed
    assert h.watchdog.disarmed


def test_tv_host_in_the_container_network_is_config_invalid(tmp_path: Path) -> None:
    h = Harness(tmp_path, raw={"tv_host": "172.30.32.5"})
    assert h.run().outcome is Outcome.CONFIG_INVALID


def test_lock_contention_is_already_running(h: Harness) -> None:
    h.state.fail["open"] = AlreadyRunning()
    result = h.run()
    assert result.outcome is Outcome.ALREADY_RUNNING
    assert "options.load" not in h.events
    assert_tv_untouched(h)


def test_unusable_state_at_open_is_state_error(h: Harness) -> None:
    h.state.fail["open"] = StateError("read-only")
    assert h.run().outcome is Outcome.STATE_ERROR
    assert "options.load" not in h.events


def test_newer_history_version_is_state_error_before_selection(h: Harness) -> None:
    h.state.fail["load_exclusions"] = StateError("written by a newer version")
    result = h.run()
    assert result.outcome is Outcome.STATE_ERROR
    assert "provider.iter" not in h.events
    assert_tv_untouched(h)


def test_a_deadline_escaping_a_stage_is_deadline_exceeded(h: Harness) -> None:
    h.options.error = DeadlineExceeded("configure")
    result = h.run()
    assert result.outcome is Outcome.DEADLINE_EXCEEDED
    assert_tv_untouched(h)


# ------------------------------------------------------------- filters, B8


def test_ignored_filters_are_reported_in_log_summary_and_record(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    h = Harness(
        tmp_path,
        raw={
            "tv_host": "10.0.0.5",
            "source": "cleveland_museum_of_art",
            "department": "aic_test_paintings",
            "style": "style_test_one",
            "color": "color_test_blue",
        },
        vocabulary=SYNTHETIC_VOCABULARY,
    )
    h.cma_provider.candidates = [make_candidate("77", provider_key="cma")]
    with caplog.at_level(logging.WARNING, logger=h.logger.name):
        result = h.run()

    assert result.outcome is Outcome.DELIVERED
    assert set(result.ignored_filters) == {
        "department=aic_test_paintings(other_source)",
        "style=style_test_one(unsupported_by_source)",
        "color=color_test_blue(unsupported_by_source)",
    }
    assert "ignored_filters=" in result.summary_line
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len([r for r in warnings if "ignored" in r.getMessage()]) == 3
    ignored = h.last_run["ignored_filters"]
    assert isinstance(ignored, list)
    reasons = {(i["filter"], i["reason"]) for i in ignored}
    assert reasons == {
        ("department", "other_source"),
        ("style", "unsupported_by_source"),
        ("color", "unsupported_by_source"),
    }
    # The provider only sees what applies.
    assert h.cma_provider.filters[0].active() == {}


def test_helper_values_override_static_values(tmp_path: Path) -> None:
    h = Harness(
        tmp_path,
        raw={
            "tv_host": "10.0.0.5",
            "source": "cleveland_museum_of_art",
            "department_helper": "input_select.fg_department",
        },
        vocabulary=SYNTHETIC_VOCABULARY,
    )
    h.cma_provider.candidates = [make_candidate("2001", provider_key="cma")]
    h.helpers.values = {FilterField.DEPARTMENT: "Test Prints"}
    h.run()
    assert h.helpers.requested == {FilterField.DEPARTMENT: "input_select.fg_department"}
    applied = h.cma_provider.filters[0]
    assert applied.department == "cma_test_prints"
    assert h.last_run["filters"]["provenance"]["department"] == "helper"  # type: ignore[index]


def test_a_failing_helper_reader_falls_back_to_static_values(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    h = Harness(
        tmp_path,
        raw={
            "tv_host": "10.0.0.5",
            "source": "cleveland_museum_of_art",
            "department": "cma_test_prints",
            "department_helper": "input_select.fg_department",
        },
        vocabulary=SYNTHETIC_VOCABULARY,
    )
    h.cma_provider.candidates = [make_candidate("2001", provider_key="cma")]
    h.helpers.error = RuntimeError("proxy down")
    with caplog.at_level(logging.WARNING, logger=h.logger.name):
        result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert h.cma_provider.filters[0].department == "cma_test_prints"
    assert "static options" in caplog.text


def test_no_helper_read_without_configured_helpers(h: Harness) -> None:
    h.run()
    assert "helpers.read" not in h.events


# ------------------------------------------------------------ no delivery


def test_an_empty_local_library_gets_its_own_hint(tmp_path: Path) -> None:
    h = Harness(tmp_path, raw={"tv_host": "10.0.0.5", "source": "local_media"})
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert result.hint == Hint.LIBRARY_EMPTY
    assert "/media/frame_gallery/library" in result.summary_line


def test_a_local_library_cut_off_by_the_deadline_is_not_called_empty(tmp_path: Path) -> None:
    h = Harness(tmp_path, raw={"tv_host": "10.0.0.5", "source": "local_media"})
    h.local_provider.error = DeadlineExceeded("discovery")
    h.local_provider.raise_at = 0
    result = h.run()
    assert result.hint != Hint.LIBRARY_EMPTY


def test_empty_source_is_no_match_and_leaves_the_tv_unchanged(tmp_path: Path) -> None:
    h = Harness(tmp_path, candidates=[])
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert result.hint == Hint.FILTERS_TOO_RESTRICTIVE
    assert result.stages == (
        Stage.CONFIGURE,
        Stage.RESOLVE_FILTERS,
        Stage.SELECT,
        Stage.ATTEMPT,
        Stage.FINISH,
    )
    assert "workspace.create" not in h.events
    assert_tv_untouched(h)
    assert_cleaned_up_without_workspace(h)


def assert_cleaned_up_without_workspace(h: Harness) -> None:
    assert h.workspace.removed == 1
    assert h.state.closed
    assert h.watchdog.disarmed


def test_everything_excluded_is_nothing_new(h: Harness) -> None:
    h.state.exclusions = ExclusionSet(
        history=frozenset({"aic:1001"}),
        uploaded=frozenset({"aic:1002"}),
        uncertain=frozenset({"aic:1003"}),
    )
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert result.hint == Hint.NOTHING_NEW
    assert_tv_untouched(h)


def test_the_provider_learns_the_permanent_exclusions_for_its_hints(h: Harness) -> None:
    h.state.exclusions = ExclusionSet(
        history=frozenset({"aic:1001"}),
        uploaded=frozenset({"aic:1002"}),
        uncertain=frozenset({"aic:1003"}),
    )
    h.run()
    [context] = h.provider.contexts
    assert context.is_excluded_for_good("aic:1001")
    assert context.is_excluded_for_good("aic:1002")
    # A quarantine ends, so a hint may not rest on it.
    assert not context.is_excluded_for_good("aic:1003")


def test_skipped_exhausted_pages_are_nothing_new_and_recorded(h: Harness) -> None:
    h.provider.candidates = []
    h.provider.on_context = lambda context: setattr(context.notes, "pages_skipped", 3)
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert result.hint == Hint.NOTHING_NEW
    stats = h.last_run["stats"]
    assert isinstance(stats, dict)
    selection = stats["selection"]
    assert isinstance(selection, dict)
    assert selection["pages_skipped"] == 3


def test_the_metadata_cache_is_written_once_before_the_last_run_record(h: Harness) -> None:
    writer = FakeCacheWriter(h.events)
    h.bindings = {SourceKey.ART_INSTITUTE_CHICAGO: ProviderBinding(h.provider, cache=writer)}
    result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert h.events.count("cache.flush") == 1
    assert h.events.before("cache.flush", "records.last_run")
    [deadline] = writer.deadlines
    assert deadline.expires_at == h.records.deadlines["last_run"].expires_at - LAST_RUN_RESERVE_S


def test_a_failing_cache_never_changes_the_outcome(
    h: Harness, caplog: pytest.LogCaptureFixture
) -> None:
    writer = FakeCacheWriter(h.events, error=RuntimeError("cache bug"))
    h.bindings = {SourceKey.ART_INSTITUTE_CHICAGO: ProviderBinding(h.provider, cache=writer)}
    with caplog.at_level(logging.WARNING, h.logger.name):
        result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert "the metadata cache could not be written" in caplog.text


def test_a_run_that_lost_the_lock_writes_no_cache(h: Harness) -> None:
    writer = FakeCacheWriter(h.events)
    h.bindings = {SourceKey.ART_INSTITUTE_CHICAGO: ProviderBinding(h.provider, cache=writer)}
    h.state.fail["open"] = AlreadyRunning()
    assert h.run().outcome is Outcome.ALREADY_RUNNING
    assert "cache.flush" not in h.events


def test_excluded_works_are_skipped(h: Harness) -> None:
    h.state.exclusions = ExclusionSet(history=frozenset({"aic:1001"}))
    result = h.run()
    assert result.delivered_id == "aic:1002"


def test_rejected_candidates_give_filters_too_restrictive(tmp_path: Path) -> None:
    h = Harness(tmp_path, candidates=[make_candidate("1", size=Size(800, 1200))])
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert result.hint == Hint.FILTERS_TOO_RESTRICTIVE


def _slow_everywhere(h: Harness) -> float:
    """Every step uses its whole budget: CONFIGURE 10 s, discovery until 39 s,
    and the attempts until the end of the attempts window at 68 s."""
    start = h.clock.monotonic()
    h.options.delay_s = 10.0
    h.provider.candidates = [make_candidate("1"), make_candidate("2")]
    h.provider.per_candidate_s = 14.5
    h.records.consume_deadline = True
    return start


def test_no_match_run_ends_by_70_seconds_when_every_step_is_slow(tmp_path: Path) -> None:
    """C11: the attempts run until 68 s; FINISH then ends by 70 s, not 78 s."""
    h = Harness(tmp_path)
    start = _slow_everywhere(h)
    h.fetcher.consume_deadline = True
    h.fetcher.failures = {
        "1": SourceError(SourceErrorKind.NOT_FOUND),
        "2": SourceError(SourceErrorKind.NOT_FOUND),
    }
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert h.fetcher.deadlines[-1].expires_at == pytest.approx(start + 68)
    assert h.clock.monotonic() - start == pytest.approx(70.0)
    assert result.elapsed_s <= 70.0 + 1e-9


def test_source_failed_run_ends_by_70_seconds_when_every_step_is_slow(tmp_path: Path) -> None:
    h = Harness(tmp_path)
    start = _slow_everywhere(h)
    h.fetcher.consume_deadline = True
    h.fetcher.failures = {
        "1": SourceError(SourceErrorKind.TRANSPORT),
        "2": SourceError(SourceErrorKind.TRANSPORT),
    }
    result = h.run()
    assert result.outcome is Outcome.SOURCE_FAILED
    assert h.clock.monotonic() - start == pytest.approx(70.0)


def test_image_failed_run_ends_by_70_seconds_when_every_step_is_slow(tmp_path: Path) -> None:
    h = Harness(tmp_path)
    start = _slow_everywhere(h)
    h.executor.consume_timeout = True
    h.executor.behaviours = [WorkerError(WorkerErrorKind.CRASH), WorkerError(WorkerErrorKind.CRASH)]
    result = h.run()
    assert result.outcome is Outcome.IMAGE_FAILED
    assert h.clock.monotonic() - start == pytest.approx(70.0)


def test_slow_provider_without_candidates_is_source_failed_by_70_seconds(tmp_path: Path) -> None:
    h = Harness(tmp_path, candidates=[])
    start = h.clock.monotonic()
    h.options.delay_s = 10.0

    def endless() -> Iterator[Candidate]:
        # A real provider clamps every request to the discovery deadline, so a
        # provider that never finds anything ends with DeadlineExceeded.
        deadline = h.provider.contexts[-1].deadline
        while True:
            h.clock.advance(5.0)
            deadline.check()
            yield from ()

    h.provider.candidates = []
    h.provider._generate = endless  # type: ignore[method-assign]
    h.records.consume_deadline = True
    result = h.run()
    assert result.outcome is Outcome.SOURCE_FAILED
    assert h.clock.monotonic() - start <= 70.0 + 1e-9


def test_limits_reached_hint(h: Harness) -> None:
    h.provider.candidates = [make_candidate(str(i), size=Size(800, 1200)) for i in range(200)]
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert result.hint == Hint.LIMITS_REACHED
    # 150 are evaluated (the candidate allowance); the 151st ends the pass.
    assert h.last_run["stats"]["selection"]["evaluated"] == 150  # type: ignore[index]
    assert h.provider.pulled == 151


def test_provider_transport_error_is_source_failed(h: Harness) -> None:
    h.provider.raise_at = 0
    h.provider.error = SourceError(SourceErrorKind.TRANSPORT, "connect failed")
    result = h.run()
    assert result.outcome is Outcome.SOURCE_FAILED
    assert_tv_untouched(h)


def test_provider_failing_on_the_first_call_is_source_failed(h: Harness) -> None:
    h.provider.call_error = SourceError(SourceErrorKind.HTTP_ERROR, "503")
    assert h.run().outcome is Outcome.SOURCE_FAILED


def test_stop_after_403_does_not_attempt_downloads(h: Harness) -> None:
    h.provider.raise_at = 1
    h.provider.error = SourceError(SourceErrorKind.STOPPED, "403")
    result = h.run()
    assert result.outcome is Outcome.SOURCE_FAILED
    assert not any(e.startswith("fetch:") for e in h.events)


def test_stop_on_a_download_ends_the_attempts(h: Harness) -> None:
    h.fetcher.failures = {"1001": SourceError(SourceErrorKind.STOPPED, "429")}
    result = h.run()
    assert result.outcome is Outcome.SOURCE_FAILED
    assert [e for e in h.events if e.startswith("fetch:")] == ["fetch:1001"]


def test_provider_error_mid_discovery_still_attempts_the_shortlist(h: Harness) -> None:
    h.provider.raise_at = 1
    h.provider.error = SourceError(SourceErrorKind.TIMEOUT)
    result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert result.delivered_id == "aic:1001"


def test_download_transport_failure_then_success_delivers(h: Harness) -> None:
    h.fetcher.failures = {"1001": SourceError(SourceErrorKind.TRANSPORT)}
    result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert result.delivered_id == "aic:1002"


def test_download_transport_failure_everywhere_is_source_failed(h: Harness) -> None:
    h.fetcher.failures = {
        "1001": SourceError(SourceErrorKind.OVER_CAP),
        "1002": SourceError(SourceErrorKind.TRANSPORT),
    }
    assert h.run().outcome is Outcome.SOURCE_FAILED


def test_not_found_everywhere_is_no_match(h: Harness) -> None:
    h.fetcher.failures = {
        "1001": SourceError(SourceErrorKind.NOT_FOUND),
        "1002": SourceError(SourceErrorKind.NOT_FOUND),
    }
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    notes = h.last_run["stats"]["attempts"]  # type: ignore[index]
    assert [n["result"] for n in notes] == ["not_found", "not_found"]


def test_download_cut_by_the_window_counts_as_limits(h: Harness) -> None:
    # Discovery leaves 10 s of the attempts; the download is cut by the window.
    h.provider.per_candidate_s = 24.0
    h.provider.candidates = [make_candidate("1001"), make_candidate("1002")]
    h.fetcher.consume_deadline = True
    h.fetcher.failures = {"1001": DeadlineExceeded("download")}
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert result.hint == Hint.LIMITS_REACHED
    # The window is used up: the second candidate is never fetched.
    assert [e for e in h.events if e.startswith("fetch:")] == ["fetch:1001"]


def test_download_exceeding_its_own_limit_is_a_transport_failure(h: Harness) -> None:
    """§4.2: a request's own timeout counts towards source_failed."""
    h.fetcher.failures = {
        "1001": DeadlineExceeded("download"),
        "1002": DeadlineExceeded("download"),
    }
    result = h.run()
    assert result.outcome is Outcome.SOURCE_FAILED
    notes = h.last_run["stats"]["attempts"]  # type: ignore[index]
    assert [n["result"] for n in notes] == ["transport", "transport"]


def test_a_provider_repeating_itself_is_nothing_new(h: Harness) -> None:
    h.provider.candidates = [make_candidate("1001")] * 3
    h.state.exclusions = ExclusionSet(history=frozenset({"aic:1001"}))
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert result.hint == Hint.NOTHING_NEW


def test_only_two_candidates_are_attempted(h: Harness) -> None:
    h.fetcher.failures = {
        "1001": SourceError(SourceErrorKind.NOT_FOUND),
        "1002": SourceError(SourceErrorKind.NOT_FOUND),
    }
    h.run()
    assert [e for e in h.events if e.startswith("fetch:")] == ["fetch:1001", "fetch:1002"]


def test_no_second_attempt_once_the_window_is_used_up(h: Harness) -> None:
    h.fetcher.consume_deadline = True
    h.fetcher.delay_s = 0
    h.provider.per_candidate_s = 0
    h.fetcher.failures = {"1001": SourceError(SourceErrorKind.NOT_FOUND)}
    # The first download uses 20 s; make the window short by a slow CONFIGURE.
    h.options.delay_s = 10.0
    h.provider.candidates = [make_candidate("1001"), make_candidate("1002")]
    h.provider.per_candidate_s = 19.0
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert result.hint == Hint.LIMITS_REACHED


# ------------------------------------------------------------ image failures


def _failed(failure: PrepareFailure) -> JsonObject:
    return PrepareResult(status=PrepareStatus.FAILED, failure=failure).to_json()


def test_processing_failure_everywhere_is_image_failed(h: Harness) -> None:
    h.executor.behaviours = [
        lambda _r: _failed(PrepareFailure.DECODE),
        WorkerError(WorkerErrorKind.CRASH),
    ]
    result = h.run()
    assert result.outcome is Outcome.IMAGE_FAILED
    assert_tv_untouched(h)


def test_processing_failure_then_success_delivers(h: Harness) -> None:
    h.executor.behaviours = [WorkerError(WorkerErrorKind.MEMORY)]
    result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert result.delivered_id == "aic:1002"


def test_worker_timeout_by_its_own_limit_is_image_failed(h: Harness) -> None:
    h.executor.behaviours = [WorkerError(WorkerErrorKind.TIMEOUT)] * 2
    assert h.run().outcome is Outcome.IMAGE_FAILED


def test_worker_timeout_cut_by_the_window_is_limits(h: Harness) -> None:
    h.provider.per_candidate_s = 24.0  # two candidates: 48 s of the 58 s
    h.provider.candidates = [make_candidate("1001"), make_candidate("1002")]
    h.executor.behaviours = [WorkerError(WorkerErrorKind.TIMEOUT)] * 2
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert result.hint == Hint.LIMITS_REACHED


def test_invalid_worker_result_is_image_failed(h: Harness) -> None:
    h.executor.behaviours = [lambda _r: {"status": "ok"}, lambda _r: {"nonsense": True}]
    assert h.run().outcome is Outcome.IMAGE_FAILED


def test_declared_format_mismatch_is_image_failed(h: Harness) -> None:
    h.fetcher.declared = {"1001": ImageFormat.PNG, "1002": ImageFormat.PNG}
    result = h.run()
    assert result.outcome is Outcome.IMAGE_FAILED
    assert "executor.run:prepare" not in h.events


def test_not_an_image_is_image_failed(h: Harness) -> None:
    h.fetcher.payloads = {"1001": b"<html>", "1002": b"GIF89a"}
    assert h.run().outcome is Outcome.IMAGE_FAILED


def test_invalid_prepared_output_is_image_failed(h: Harness) -> None:
    def write_garbage(request: PrepareRequest) -> JsonObject:
        Path(request.output_path).write_bytes(b"\xff\xd8\xff\xe0 not really a jpeg")
        return h.executor.ok_result().to_json()

    h.executor.behaviours = [write_garbage, write_garbage]
    assert h.run().outcome is Outcome.IMAGE_FAILED


def test_rejection_by_real_dimensions_tries_the_next_candidate(h: Harness) -> None:
    rejected = PrepareResult(
        status=PrepareStatus.REJECTED,
        source_size=Size(1000, 1000),
        oriented_size=Size(1000, 1000),
        orientation=1,
        rejection=Rejection.NOT_LANDSCAPE,
    ).to_json()
    h.executor.behaviours = [lambda _r: rejected]
    result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert result.delivered_id == "aic:1002"
    notes = h.last_run["stats"]["attempts"]  # type: ignore[index]
    assert notes[0]["result"] == "rejected:not_landscape"


def test_parent_rechecks_the_reported_size(h: Harness) -> None:
    """A worker that reports a square image as OK is still rejected (defence in depth)."""
    h.executor.oriented_size = Size(1000, 1000)
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert_tv_untouched(h)


def test_prepare_request_carries_the_selection_constraints(tmp_path: Path) -> None:
    h = Harness(
        tmp_path,
        raw={"tv_host": "10.0.0.5", "fit_mode": "cover", "background_color": "#102030"},
    )
    seen: list[PrepareRequest] = []

    def capture(request: PrepareRequest) -> JsonObject:
        seen.append(request)
        Path(request.output_path).write_bytes(canvas_jpeg_bytes())
        return h.executor.ok_result().to_json()

    h.executor.behaviours = [capture]
    h.run()
    request = seen[0]
    assert request.fit_mode.value == "cover"
    assert request.background.to_hex() == "#102030"
    assert request.landscape_only is True
    assert request.require_near_16_9 is True
    assert request.declared_format is ImageFormat.JPEG
    assert Path(request.output_path).parent == h.workspace.root / "out"
    assert Path(request.source_path).parent == h.workspace.root / "in"


# ---------------------------------------------------------------- PRE-STAGE


def test_prestage_failure_is_state_error_and_the_tv_is_untouched(h: Harness) -> None:
    h.state.fail["prestage"] = StateError("disk full")
    result = h.run()
    assert result.outcome is Outcome.STATE_ERROR
    assert "state.commit_intent:aic:1001" not in h.events
    assert_tv_untouched(h)


def test_intent_failure_is_state_error_and_the_intent_is_cleaned(h: Harness) -> None:
    h.state.fail["commit_intent"] = StateError("read-only")
    result = h.run()
    assert result.outcome is Outcome.STATE_ERROR
    assert "state.discard_prestaged" in h.events
    assert "state.remove_intent:aic:1001" in h.events
    assert_tv_untouched(h)


def test_television_reserve_is_rechecked_before_the_intent(h: Harness) -> None:
    """§7.3: not enough time for DELIVER + FINISH means no intent and no TV contact."""
    h.state.delays["prestage"] = 71.0  # a stalled fsync leaves < 50 s
    result = h.run()
    assert result.outcome is Outcome.DEADLINE_EXCEEDED
    assert "state.commit_intent:aic:1001" not in h.events
    assert "state.discard_prestaged" in h.events
    assert_tv_untouched(h)


# ------------------------------------------------------------------ DELIVER


@pytest.mark.parametrize(
    ("markers", "status", "outcome", "ledger", "hint"),
    [
        ((), DeliveryStatus.UNREACHABLE, Outcome.TV_UNREACHABLE, {}, None),
        ((Marker.CONNECTED,), DeliveryStatus.PROTOCOL, Outcome.TV_UNREACHABLE, {}, None),
        (
            (Marker.CONNECTED,),
            DeliveryStatus.NOT_AUTHORIZED,
            Outcome.TV_NOT_AUTHORIZED,
            {},
            Hint.ACCEPT_PROMPT,
        ),
        ((Marker.CONNECTED,), DeliveryStatus.UNSUPPORTED, Outcome.TV_REJECTED, {}, None),
        (
            (Marker.CONNECTED,),
            DeliveryStatus.INSUFFICIENT_TIME,
            Outcome.DEADLINE_EXCEEDED,
            {},
            Hint.PAIRED_START_AGAIN,
        ),
        (
            (Marker.CONNECTED, Marker.UPLOAD_STARTED),
            DeliveryStatus.UNREACHABLE,
            Outcome.TV_UNREACHABLE,
            {"aic:1001": "uncertain"},
            Hint.UPLOAD_MAY_HAVE_REACHED_TV,
        ),
        (
            (Marker.CONNECTED, Marker.UPLOAD_STARTED),
            DeliveryStatus.REFUSED,
            Outcome.TV_REJECTED,
            {},
            None,
        ),
        (
            (Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED),
            DeliveryStatus.REFUSED,
            Outcome.TV_REJECTED,
            {"aic:1001": "uploaded"},
            None,
        ),
        (
            (Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED),
            DeliveryStatus.UNREACHABLE,
            Outcome.TV_UNREACHABLE,
            {"aic:1001": "uploaded"},
            Hint.STORED_ON_TV,
        ),
        ((Marker.CONNECTED,), DeliveryStatus.OK, Outcome.TV_UNREACHABLE, {}, None),
    ],
)
def test_television_results_follow_the_last_marker(
    h: Harness,
    markers: tuple[Marker, ...],
    status: DeliveryStatus,
    outcome: Outcome,
    ledger: dict[str, str],
    hint: Hint | None,
) -> None:
    """§12.4 and E4, E7, E8, E10: history, current, and preview change only after selected."""
    h.tv.markers = list(markers)
    h.tv.status = status
    result = h.run()

    assert result.outcome is outcome
    assert result.hint == (None if hint is None else str(hint))
    assert h.state.ledger == ledger
    assert h.state.history == []
    assert h.state.prestaged is None
    assert h.preview.published == []
    assert h.records.current == []
    assert result.stages[-2:] == (Stage.DELIVER, Stage.FINISH)
    assert_cleaned_up(h)


def test_uploaded_is_promoted_immediately(h: Harness) -> None:
    """D-137: the promotion happens while the delivery is still running."""
    seen: list[str | None] = []

    def ledger_right_after(marker: Marker) -> None:
        if marker is Marker.UPLOADED:
            seen.append(h.state.ledger.get("aic:1001"))

    h.tv.markers = [Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED]
    h.tv.status = DeliveryStatus.REFUSED
    h.tv.during = ledger_right_after
    h.run()
    assert seen == ["uploaded"]


def test_uploaded_reported_only_in_the_result_is_still_promoted(h: Harness) -> None:
    h.tv.markers = []
    h.tv.report_markers = True
    h.tv.status = DeliveryStatus.REFUSED

    original = h.tv.deliver

    def deliver_reporting_only(request: DeliveryRequest, on_marker: MarkerSink) -> DeliveryResult:
        result = original(request, on_marker)
        return type(result)(
            status=result.status,
            markers_seen=(Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED),
        )

    h.tv.deliver = deliver_reporting_only  # type: ignore[method-assign]
    result = h.run()
    assert result.outcome is Outcome.TV_REJECTED
    assert h.state.ledger == {"aic:1001": "uploaded"}


def test_failed_promotion_keeps_the_intent_and_the_outcome(h: Harness) -> None:
    h.state.fail["promote"] = StateError("disk full")
    h.tv.markers = [Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED]
    h.tv.status = DeliveryStatus.REFUSED
    result = h.run()
    assert result.outcome is Outcome.TV_REJECTED
    assert h.state.ledger == {"aic:1001": "uncertain"}


def test_failed_intent_removal_leaves_it_in_quarantine(h: Harness) -> None:
    h.state.fail["remove_intent"] = StateError("read-only")
    h.tv.markers = [Marker.CONNECTED]
    h.tv.status = DeliveryStatus.UNREACHABLE
    result = h.run()
    assert result.outcome is Outcome.TV_UNREACHABLE
    assert h.state.ledger == {"aic:1001": "uncertain"}


def test_television_deadline_is_classified_from_the_markers(h: Harness) -> None:
    h.tv.markers = [Marker.CONNECTED, Marker.UPLOAD_STARTED]
    h.tv.error = DeadlineExceeded("deliver")
    result = h.run()
    assert result.outcome is Outcome.TV_UNREACHABLE
    assert h.state.ledger == {"aic:1001": "uncertain"}


def test_selected_with_a_later_protocol_error_is_delivered(h: Harness) -> None:
    h.tv.status = DeliveryStatus.PROTOCOL
    result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert h.state.history == ["aic:1001"]


# ------------------------------------------------------- RECORD and PUBLISH


def test_history_rename_failure_is_delivered_unrecorded(h: Harness) -> None:
    h.state.fail["record_history"] = StateError("rename failed")
    result = h.run()
    assert result.outcome is Outcome.DELIVERED_UNRECORDED
    assert "preview.publish" in h.events  # PUBLISH is still attempted
    assert h.state.ledger == {"aic:1001": "uploaded"}


def test_preview_failure_is_delivered_with_warnings(tmp_path: Path) -> None:
    h = Harness(tmp_path)
    h.preview.error = PublishError("/media unavailable")
    result = h.run()
    assert result.outcome is Outcome.DELIVERED_WITH_WARNINGS
    assert h.state.history == ["aic:1001"]
    assert h.records.current  # the current record is still written


def test_current_record_failure_is_delivered_with_warnings(tmp_path: Path) -> None:
    h = Harness(tmp_path)
    h.records.current_error = StateError("disk full")
    assert h.run().outcome is Outcome.DELIVERED_WITH_WARNINGS


def test_last_run_failure_after_delivery_is_delivered_with_warnings(tmp_path: Path) -> None:
    h = Harness(tmp_path)
    h.records.last_run_error = StateError("disk full")
    assert h.run().outcome is Outcome.DELIVERED_WITH_WARNINGS


def test_last_run_failure_does_not_change_other_outcomes(tmp_path: Path) -> None:
    h = Harness(tmp_path, candidates=[])
    h.records.last_run_error = StateError("disk full")
    assert h.run().outcome is Outcome.NO_MATCH


# ----------------------------------------------------------- cancellation


def test_stop_during_selection_is_cancelled(h: Harness) -> None:
    h.provider.raise_at = 1
    h.provider.error = Cancelled()
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert result.exit_code == 0
    assert result.stages[-1] is Stage.FINISH
    assert_tv_untouched(h)
    assert_cleaned_up_without_workspace(h)
    assert h.last_run["outcome"] == "cancelled"


def test_stop_during_preparation_is_cancelled(h: Harness) -> None:
    h.executor.behaviours = [Cancelled()]
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert_tv_untouched(h)
    assert_cleaned_up(h)


def test_stop_after_the_intent_removes_it(h: Harness) -> None:
    def cancel_on_deliver(request: DeliveryRequest, on_marker: MarkerSink) -> DeliveryResult:
        raise Cancelled

    h.tv.deliver = cancel_on_deliver  # type: ignore[method-assign]
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert "state.remove_intent:aic:1001" in h.events
    assert h.state.ledger == {}
    assert h.state.history == []


def test_stop_after_upload_started_keeps_the_quarantine(h: Harness) -> None:
    h.tv.markers = [Marker.CONNECTED, Marker.UPLOAD_STARTED]
    h.tv.error = Cancelled()
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert h.state.ledger == {"aic:1001": "uncertain"}
    assert "state.remove_intent:aic:1001" not in h.events


def test_stop_after_uploaded_keeps_the_ledger_entry(h: Harness) -> None:
    h.tv.markers = [Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED]
    h.tv.error = Cancelled()
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert h.state.ledger == {"aic:1001": "uploaded"}


def test_stop_after_selected_is_deferred_and_skips_publish(h: Harness) -> None:
    """§7.6: RECORD still runs; PUBLISH is skipped; the outcome is not cancelled."""

    def stop_after_selected(marker: Marker) -> None:
        if marker is Marker.SELECTED:
            h.cancellation.request_stop()  # deferred: must not raise

    h.tv.during = stop_after_selected
    result = h.run()
    assert result.outcome is Outcome.DELIVERED_WITH_WARNINGS
    assert h.state.history == ["aic:1001"]
    assert "preview.publish" not in h.events
    assert h.records.last_run


def test_stop_raised_after_selected_is_still_delivered(h: Harness) -> None:
    h.tv.error = Cancelled()  # raised after all four markers
    result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert h.state.history == ["aic:1001"]


def test_stop_during_finish_does_not_interrupt(tmp_path: Path) -> None:
    h = Harness(tmp_path, candidates=[])
    original = h.records.write_last_run

    def stop_then_write(record: Mapping[str, object], deadline: Deadline) -> None:
        h.cancellation.request_stop()  # deferred during FINISH
        original(record, deadline)

    h.records.write_last_run = stop_then_write  # type: ignore[method-assign]
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert h.records.last_run


# ------------------------------------------------------------ internal error


def test_unexpected_error_is_internal_error_with_exit_70(
    h: Harness, caplog: pytest.LogCaptureFixture
) -> None:
    h.provider.raise_at = 0
    h.provider.error = RuntimeError("bug")
    with caplog.at_level(logging.ERROR, logger=h.logger.name):
        result = h.run()
    assert result.outcome is Outcome.INTERNAL_ERROR
    assert result.exit_code == 70
    assert "Traceback" in caplog.text
    assert_cleaned_up_without_workspace(h)


def test_internal_error_after_the_intent_keeps_the_quarantine(h: Harness) -> None:
    h.tv.markers = []
    h.tv.error = RuntimeError("bug in the adapter")
    result = h.run()
    assert result.outcome is Outcome.INTERNAL_ERROR
    assert h.state.ledger == {"aic:1001": "uncertain"}
    assert "state.remove_intent:aic:1001" not in h.events


def test_an_unusable_television_port_is_internal_error_and_keeps_the_intent(h: Harness) -> None:
    h.tv.deliver = None  # type: ignore[assignment,method-assign]  # calling it fails
    result = h.run()
    assert result.outcome is Outcome.INTERNAL_ERROR
    assert h.state.ledger == {"aic:1001": "uncertain"}


def test_internal_error_before_the_television_keeps_a_committed_intent(h: Harness) -> None:
    """§4.2: after an internal error a committed intent stays as quarantine,
    even though the television was never contacted."""
    original = h.state.commit_upload_intent

    def commit_then_fail(qualified_id: str, now: datetime) -> None:
        original(qualified_id, now)
        raise RuntimeError("bug after the intent was committed")

    h.state.commit_upload_intent = commit_then_fail  # type: ignore[method-assign]
    result = h.run()
    assert result.outcome is Outcome.INTERNAL_ERROR
    assert "tv.deliver" not in h.events
    assert h.state.ledger == {"aic:1001": "uncertain"}
    assert "state.remove_intent:aic:1001" not in h.events


def test_cleanup_failures_never_escape(h: Harness, caplog: pytest.LogCaptureFixture) -> None:
    h.workspace.remove_error = OSError("busy")
    with caplog.at_level(logging.ERROR, logger=h.logger.name):
        result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert "cleanup step failed" in caplog.text
    assert h.state.closed
    assert h.watchdog.disarmed


def test_a_missing_workspace_is_state_error(h: Harness) -> None:
    h.workspace.error = StateError("no /tmp")
    result = h.run()
    assert result.outcome is Outcome.STATE_ERROR
    assert_tv_untouched(h)


def test_the_television_address_is_not_recorded(h: Harness) -> None:
    result = h.run()
    text = repr(h.last_run) + result.summary_line + repr(h.records.current)
    assert "192.168.1.20" not in text


# ------------------------------------------------------------ further paths


def test_runner_without_a_log_level_hook(h: Harness) -> None:
    runner = h.runner()
    runner._set_log_level = None
    assert runner.run().outcome is Outcome.DELIVERED


def test_a_stop_while_reading_helpers_cancels(tmp_path: Path) -> None:
    h = Harness(
        tmp_path,
        raw={"tv_host": "10.0.0.5", "color_helper": "input_select.fg_colour"},
        vocabulary=SYNTHETIC_VOCABULARY,
    )
    h.helpers.error = Cancelled()
    result = h.run()
    assert result.outcome is Outcome.CANCELLED
    assert "provider.iter" not in h.events


def test_an_unreadable_helper_falls_back_with_a_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """B4: a helper that cannot be read falls back to its static value."""
    h = Harness(
        tmp_path,
        raw={
            "tv_host": "10.0.0.5",
            "source": "cleveland_museum_of_art",
            "department": "cma_test_prints",
            "department_helper": "input_select.fg_department",
        },
        vocabulary=SYNTHETIC_VOCABULARY,
    )
    h.cma_provider.candidates = [make_candidate("2001", provider_key="cma")]
    h.helpers.values = {FilterField.DEPARTMENT: None}
    with caplog.at_level(logging.WARNING, logger=h.logger.name):
        result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert h.cma_provider.filters[0].department == "cma_test_prints"
    assert "department_helper" in caplog.text


def test_no_time_left_to_prepare_counts_as_limits(h: Harness) -> None:
    """The download succeeds exactly at the end of the attempts: nothing is prepared."""
    h.provider.per_candidate_s = 24.0
    h.provider.candidates = [make_candidate("1001"), make_candidate("1002")]
    h.fetcher.consume_deadline = True
    result = h.run()
    assert result.outcome is Outcome.NO_MATCH
    assert result.hint == Hint.LIMITS_REACHED
    assert "executor.run:prepare" not in h.events


def test_repeated_markers_are_recorded_once(h: Harness) -> None:
    h.tv.markers = [Marker.CONNECTED, Marker.CONNECTED]
    h.tv.status = DeliveryStatus.UNREACHABLE
    result = h.run()
    assert result.outcome is Outcome.TV_UNREACHABLE
    assert h.last_run["outcome"] == "tv_unreachable"


def test_television_detail_is_logged_safely(h: Harness, caplog: pytest.LogCaptureFixture) -> None:
    h.tv.detail = "art mode\nis off"
    with caplog.at_level(logging.INFO, logger=h.logger.name):
        h.run()
    assert "television: art mode is off" in caplog.text
