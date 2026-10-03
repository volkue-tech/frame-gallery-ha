"""The run orchestrator (§4.1, §6, §7, §12.4).

One run moves through CONFIGURE, RESOLVE_FILTERS, SELECT, ATTEMPT,
PRE-STAGE, DELIVER, RECORD, PUBLISH, and FINISH. Every path, including a stop
request and an internal error, ends in FINISH and then CLEANUP. The runner
depends only on ports (§5); Phase 2 exercises it against fakes.

Stop requests (§7.6, D-141): before DELIVER, a stop request raises
``Cancelled`` wherever the run is, and every stage boundary re-checks it.
From the start of the television call to the end of the run, stop requests
are deferred: the adapter learns of one through ``stop_requested``, stops its
worker, and returns the markers seen, so no marker or ledger write is lost;
RECORD and FINISH are never interrupted, and a stop request after
``selected`` only skips PUBLISH.
"""

from __future__ import annotations

import enum
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Final

from frame_gallery.app.outcomes import (
    Hint,
    LedgerAction,
    NoDeliveryEvidence,
    Outcome,
    classify_delivery,
    classify_no_delivery,
)
from frame_gallery.app.ports import (
    FetchedImage,
    HelperReader,
    ImageFetcher,
    NetworkInfo,
    OptionsSource,
    PreviewPublisher,
    ProviderBinding,
    RunRecords,
    StateStore,
    WatchdogControl,
    Workspace,
)
from frame_gallery.app.records import (
    AttemptNote,
    RunStats,
    build_current_record,
    build_last_run_record,
)
from frame_gallery.app.signals import CancellationController
from frame_gallery.budget.allowance import Allowance
from frame_gallery.budget.clock import Clock
from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.budget.limits import (
    CANDIDATE_ALLOWANCE,
    LOCAL_INSPECTION_ALLOWANCE,
    REMOTE_PROBE_ALLOWANCE,
)
from frame_gallery.budget.phases import (
    LAST_RUN_RESERVE_S,
    PREPARE_S,
    PRESTAGE_RESERVE_S,
    ContentWindow,
    Phase,
    RunBudget,
)
from frame_gallery.config.capabilities import resolve_effective_filters
from frame_gallery.config.filters import EffectiveFilters, FilterDimension, FilterField, FilterSet
from frame_gallery.config.options import ConfigError, LogLevel, Options, parse_options
from frame_gallery.config.overrides import apply_helper_values
from frame_gallery.config.vocabulary import BUILTIN_VOCABULARY, Vocabulary
from frame_gallery.domain import SourceKey, WorkspacePaths
from frame_gallery.errors import AlreadyRunning, Cancelled, PublishError, StateError
from frame_gallery.imaging.contract import (
    PREPARE_TASK,
    DeliveryArtifact,
    PrepareRequest,
    PrepareResult,
    PrepareStatus,
)
from frame_gallery.imaging.delivery import DeliveryValidationError, validate_delivery
from frame_gallery.imaging.sniff import sniff_file
from frame_gallery.isolation.executor import Executor, WorkerError, WorkerErrorKind
from frame_gallery.logs.summary import format_summary, sanitize_for_log
from frame_gallery.providers.contract import (
    Candidate,
    DiscoveryContext,
    DiscoveryNotes,
    SourceError,
    SourceErrorKind,
)
from frame_gallery.providers.rights import ALLOWED_RIGHTS
from frame_gallery.randomness import RandomSource
from frame_gallery.selection.exclusion import ExclusionSet
from frame_gallery.selection.geometry import check_rendition
from frame_gallery.selection.shortlist import (
    DiscoveryEnd,
    SelectionPolicy,
    SelectionResult,
    SelectionStats,
    ShortlistEntry,
    build_shortlist,
)
from frame_gallery.tv.port import (
    DeliveryRequest,
    DeliveryResult,
    DeliveryStatus,
    Marker,
    MarkerEvent,
    Television,
)

LOGGER_NAME: Final = "frame_gallery.run"


class Stage(enum.StrEnum):
    CONFIGURE = "configure"
    RESOLVE_FILTERS = "resolve_filters"
    SELECT = "select"
    ATTEMPT = "attempt"
    PRE_STAGE = "pre_stage"
    DELIVER = "deliver"
    RECORD = "record"
    PUBLISH = "publish"
    FINISH = "finish"


@dataclass(frozen=True, slots=True)
class RunnerPorts:
    """Everything the runner talks to (§20.2)."""

    options_source: OptionsSource
    network_info: NetworkInfo
    state: StateStore
    helper_reader: HelperReader
    providers: Mapping[SourceKey, ProviderBinding]
    fetcher: ImageFetcher
    executor: Executor
    television: Television
    workspace: Workspace
    preview: PreviewPublisher
    records: RunRecords
    watchdog: WatchdogControl
    storage_report: Callable[[], None] = lambda: None
    finish_loading: Callable[[Deadline], None] = lambda _deadline: None


@dataclass(frozen=True, slots=True)
class RunResult:
    outcome: Outcome
    exit_code: int
    hint: str | None
    elapsed_s: float
    summary_line: str
    stages: tuple[Stage, ...]
    """The stages entered, in order (for diagnostics and tests)."""

    delivered_id: str | None = None
    ignored_filters: tuple[str, ...] = ()
    summary_emitted: bool = True
    """False when the watchdog fired first and emitted the only summary line."""


class _Terminal(Exception):
    """Internal control flow: ends the stage sequence with a classified outcome.

    It never escapes the runner.
    """

    def __init__(self, outcome: Outcome, hint: Hint | str | None = None) -> None:
        super().__init__(outcome.value)
        self.outcome = outcome
        self.hint = None if hint is None else str(hint)


@dataclass(slots=True)
class _RunState:
    started_wall: datetime
    outcome: Outcome | None = None
    hint: str | None = None
    options: Options | None = None
    configure_deadline: Deadline | None = None
    filters: EffectiveFilters | None = None
    binding: ProviderBinding | None = None
    window: ContentWindow | None = None
    evidence: NoDeliveryEvidence = field(default_factory=NoDeliveryEvidence)
    stats: RunStats = field(default_factory=RunStats)
    entry: ShortlistEntry | None = None
    artifact: DeliveryArtifact | None = None
    provider_stopped: bool = False
    prestage_attempted: bool = False
    prestaged: bool = False
    intent_attempted: bool = False
    television_contacted: bool = False
    markers: list[Marker] = field(default_factory=list)
    promoted: bool = False
    selected: bool = False
    record_attempted: bool = False
    recorded: bool = False
    unrecorded: bool = False
    warnings: list[str] = field(default_factory=list)
    finish_deadline: Deadline | None = None


@dataclass(slots=True)
class _TelevisionReply:
    status: DeliveryStatus | None = None
    """``None`` when no result arrived (killed, cancelled, or failed)."""

    reported: tuple[Marker, ...] = ()
    detail: str = ""
    cancelled: bool = False
    failure: Exception | None = None


class Runner:
    """Runs one bounded run and returns its classified result.

    One runner and one :class:`CancellationController` serve exactly one run.
    """

    def __init__(
        self,
        ports: RunnerPorts,
        *,
        clock: Clock,
        random: RandomSource,
        cancellation: CancellationController,
        vocabulary: Vocabulary = BUILTIN_VOCABULARY,
        logger: logging.Logger | None = None,
        set_log_level: Callable[[LogLevel], None] | None = None,
    ) -> None:
        self._ports = ports
        self._clock = clock
        self._random = random
        self._cancel = cancellation
        self._vocabulary = vocabulary
        self._log = logger if logger is not None else logging.getLogger(LOGGER_NAME)
        self._set_log_level = set_log_level
        self._stages: list[Stage] = []
        self._budget: RunBudget | None = None

    # ------------------------------------------------------------------ run

    def run(self) -> RunResult:
        """Run once. The summary line is logged last, after CLEANUP, and only if
        the watchdog did not claim the run first (one summary line, §19)."""
        self._cancel.claim()
        budget = RunBudget(self._clock)
        self._budget = budget
        self._stages = []
        run = _RunState(started_wall=self._clock.utc_now())
        result: RunResult | None = None
        watchdog_stopped = True
        try:
            self._run_stages(run)
            try:
                result = self._finish(run)
            except Exception:  # noqa: BLE001 - the run must still end with a summary line
                self._log.exception("internal error while finishing")
                result = self._fallback_result(run)
        finally:
            self._cleanup()
            if run.outcome is not Outcome.ALREADY_RUNNING:
                try:
                    deadline = self._finish_deadline(run)
                    if run.outcome in (
                        Outcome.NO_MATCH,
                        Outcome.SOURCE_FAILED,
                        Outcome.IMAGE_FAILED,
                    ):
                        deadline = deadline.cap_at(
                            self._run_budget().no_delivery_end, "no delivery"
                        )
                    self._ports.finish_loading(deadline)
                except Exception:  # noqa: BLE001 - feedback must never change delivery
                    self._log.warning("loading timer notification failed", exc_info=True)
            watchdog_stopped = self._disarm_watchdog()
        if not watchdog_stopped:
            # The watchdog fired first: it emits the only summary line and ends
            # the process with exit code 71 (§4.3).
            return replace(result, summary_emitted=False)
        self._log.log(result.outcome.log_level, "%s", result.summary_line)
        return result

    def _run_stages(self, run: _RunState) -> None:
        try:
            try:
                # A stop request that arrived before the run was ready was only
                # recorded (the controller started deferred); honour it here.
                self._cancel.end_start_deferral()
                self._cancel.check()
                self._ports.watchdog.arm(self._run_budget())
                self._configure(run)
                self._resolve_filters(run)
                self._select(run)
                self._attempt(run)
                self._prestage(run)
                self._deliver(run)
                self._record(run)
                self._publish(run)
            finally:
                # From here on the outcome is being decided: defer stop requests
                # so that settling state and FINISH are never interrupted.
                self._cancel.begin_deferral()
        except _Terminal as terminal:
            run.outcome, run.hint = terminal.outcome, terminal.hint
        except Cancelled:
            self._cancel.begin_deferral()
            run.outcome = Outcome.CANCELLED
        except DeadlineExceeded as exc:
            run.outcome, run.hint = self._classify_escaped_deadline(run, exc)
        except Exception:  # noqa: BLE001 - every unexpected error is classified, never lost
            self._log.exception("internal error")
            run.outcome = Outcome.INTERNAL_ERROR
        try:
            self._settle(run)
        except Exception:  # noqa: BLE001 - a port breaking its contract is still classified
            self._log.exception("internal error while settling state")
            run.outcome = Outcome.INTERNAL_ERROR

    def _classify_escaped_deadline(
        self, run: _RunState, exc: DeadlineExceeded
    ) -> tuple[Outcome, str | None]:
        """A ``DeadlineExceeded`` that no stage handled.

        In the content window it means the search limits were reached and
        follows the no-delivery rules (§4.2). Anywhere else it ends the run
        as ``deadline_exceeded`` (a CONFIGURE overrun, recorded in DECISIONS).
        """
        self._log.error("the run's time budget ran out (%s)", exc.deadline_name)
        if run.window is not None and not run.prestaged:
            run.evidence.limits_reached = True
            outcome, hint = classify_no_delivery(run.evidence)
            return outcome, None if hint is None else str(hint)
        return Outcome.DEADLINE_EXCEEDED, None

    # ------------------------------------------------------------ CONFIGURE

    def _enter(self, stage: Stage) -> None:
        # A stop request that was swallowed somewhere is honoured here at the
        # latest (a no-op while stop requests are deferred).
        self._cancel.check()
        self._stages.append(stage)
        self._log.debug("stage %s", stage.value)

    def _configure(self, run: _RunState) -> None:
        self._enter(Stage.CONFIGURE)
        deadline = self._run_budget().phase(Phase.CONFIGURE)
        run.configure_deadline = deadline
        try:
            self._ports.state.open(deadline)
        except AlreadyRunning:
            self._log.warning("another run is in progress")
            raise _Terminal(Outcome.ALREADY_RUNNING) from None
        except StateError as exc:
            self._log.error("state is unavailable: %s", sanitize_for_log(str(exc)))
            raise _Terminal(Outcome.STATE_ERROR) from None
        try:
            raw = self._ports.options_source.load(deadline)
            options = parse_options(
                raw,
                vocabulary=self._vocabulary,
                excluded_networks=self._ports.network_info.container_networks(),
            )
        except ConfigError as exc:
            for issue in exc.issues:
                self._log.error(
                    "option %s: %s", issue.option, sanitize_for_log(issue.message, max_length=300)
                )
            raise _Terminal(Outcome.CONFIG_INVALID) from None
        run.options = options
        if self._set_log_level is not None:
            self._set_log_level(options.log_level)

    def _resolve_filters(self, run: _RunState) -> None:
        self._enter(Stage.RESOLVE_FILTERS)
        options = self._options(run)
        filters = options.filters
        helpers = dict(options.helpers)
        if helpers:
            filters = self._apply_helpers(options.filters, helpers, run)
        effective = resolve_effective_filters(filters, self._vocabulary)
        run.filters = effective
        for ignored in effective.ignored:
            self._log.warning(
                "filter %s=%s ignored for %s: %s",
                ignored.field.value,
                ignored.key,
                effective.source.value,
                ignored.reason.value,
            )
        applied = ", ".join(self._describe_applied(effective)) or "none"
        ignored_text = ", ".join(i.describe() for i in effective.ignored) or "none"
        self._log.info(
            "start: source=%s (%s) filters=%s ignored=%s",
            effective.source.value,
            filters.source_provenance.value,
            applied,
            ignored_text,
        )

    @staticmethod
    def _describe_applied(effective: EffectiveFilters) -> list[str]:
        fields = {
            FilterDimension.DEPARTMENT: FilterField.DEPARTMENT,
            FilterDimension.STYLE: FilterField.STYLE,
            FilterDimension.PERIOD: FilterField.STYLE,
            FilterDimension.COLOR: FilterField.COLOR,
        }
        return [
            f"{dimension.value}={key}({effective.requested.choice(fields[dimension]).provenance})"
            for dimension, key in effective.active().items()
        ]

    def _apply_helpers(
        self, static: FilterSet, helpers: dict[FilterField, str], run: _RunState
    ) -> FilterSet:
        """Helper overrides with static fallback; this stage never fails (§15.3)."""
        deadline = run.configure_deadline
        if deadline is None:  # pragma: no cover - set by CONFIGURE
            return static
        try:
            values = self._ports.helper_reader.read(helpers, deadline)
            merged = apply_helper_values(static, values, self._vocabulary)
        except Cancelled:
            raise
        except Exception:  # noqa: BLE001 - helpers must never fail the run (B4)
            self._log.warning("helper values could not be applied; using the static options")
            return static
        for warning in merged.warnings:
            self._log.warning("%s", warning)
        return merged.filters

    # --------------------------------------------------------------- SELECT

    def _select(self, run: _RunState) -> None:
        self._enter(Stage.SELECT)
        options = self._options(run)
        filters = run.filters
        if filters is None:  # pragma: no cover - set by RESOLVE_FILTERS
            raise RuntimeError("filters missing")
        binding = self._ports.providers[filters.source]
        run.binding = binding
        try:
            exclusions = self._ports.state.load_exclusions(self._clock.utc_now())
        except StateError as exc:
            self._log.error("history is unusable: %s", sanitize_for_log(str(exc)))
            raise _Terminal(Outcome.STATE_ERROR) from None

        window = self._run_budget().content_window()
        run.window = window
        policy = SelectionPolicy(
            landscape_only=options.landscape_only,
            strict_tv_format=options.strict_tv_format,
            fit_mode=options.fit_mode,
        )
        notes = DiscoveryNotes()
        try:
            selection = self._discover(binding, filters, exclusions, policy, window, notes)
        finally:
            if binding.after_discovery is not None:
                binding.after_discovery()
        run.stats.selection = selection
        run.stats.pages_skipped = run.evidence.pages_skipped = notes.pages_skipped
        self._record_selection_evidence(run.evidence, selection)
        run.evidence.library_empty = (
            filters.source is SourceKey.LOCAL_MEDIA
            and selection.end is DiscoveryEnd.EXHAUSTED
            and selection.stats.candidates_seen == 0
        )
        self._log_selection(selection)

    def _discover(  # noqa: PLR0917 - one discovery's inputs
        self,
        binding: ProviderBinding,
        filters: EffectiveFilters,
        exclusions: ExclusionSet,
        policy: SelectionPolicy,
        window: ContentWindow,
        notes: DiscoveryNotes,
    ) -> SelectionResult:
        """Run the provider's candidates through selection (§8)."""
        try:
            candidates = binding.provider.iter_candidates(
                filters,
                DiscoveryContext(
                    deadline=window.discovery,
                    random=self._random,
                    is_excluded_for_good=exclusions.excludes_for_good,
                    notes=notes,
                ),
            )
            return build_shortlist(
                candidates,
                exclusions=exclusions,
                policy=policy,
                allowed_rights=ALLOWED_RIGHTS[filters.source],
                deadline=window.discovery,
                random=self._random,
                candidate_allowance=Allowance("candidates", CANDIDATE_ALLOWANCE),
                probe_allowance=Allowance("remote_probes", REMOTE_PROBE_ALLOWANCE),
                inspection_allowance=Allowance("local_inspections", LOCAL_INSPECTION_ALLOWANCE),
                probe=binding.probe,
                on_decision=self._log_decision if self._log.isEnabledFor(logging.DEBUG) else None,
            )
        except DeadlineExceeded:
            # The provider's first request was cut off before it yielded anything.
            return SelectionResult(entries=(), end=DiscoveryEnd.DEADLINE, stats=SelectionStats())
        except SourceError as exc:
            # The provider failed before yielding anything iterable.
            end = (
                DiscoveryEnd.PROVIDER_STOPPED
                if exc.kind is SourceErrorKind.STOPPED
                else DiscoveryEnd.PROVIDER_ERROR
            )
            return SelectionResult(entries=(), end=end, stats=SelectionStats(), provider_error=exc)

    @staticmethod
    def _record_selection_evidence(
        evidence: NoDeliveryEvidence, selection: SelectionResult
    ) -> None:
        stats = selection.stats
        error = selection.provider_error
        evidence.discovery_transport_failure = (
            error is not None and error.kind is not SourceErrorKind.NOT_FOUND
        )
        evidence.attempt_transport_failure = stats.probe_transport_failures > 0
        evidence.discovery_expired_without_candidates = (
            selection.end is DiscoveryEnd.DEADLINE and stats.candidates_seen == 0
        )
        evidence.limits_reached = selection.limits_reached
        evidence.candidates_seen = stats.candidates_seen
        # A repeated work counts like an excluded one: it offers nothing new.
        evidence.candidates_excluded = stats.excluded + stats.duplicates

    def _log_decision(self, candidate: Candidate, decision: str) -> None:
        self._log.debug("candidate %s: %s", candidate.qualified_id, decision)

    def _log_selection(self, selection: SelectionResult) -> None:
        stats = selection.stats
        self._log.info(
            "selection: %d shortlisted (%s); seen=%d excluded=%d evaluated=%d "
            "probes=%d inspections=%d",
            len(selection.entries),
            selection.end.value,
            stats.candidates_seen,
            stats.excluded,
            stats.evaluated,
            stats.probes_used,
            stats.inspections_used,
        )
        if selection.provider_error is not None:
            self._log.error(
                "the source failed: %s", sanitize_for_log(str(selection.provider_error))
            )
        for entry in selection.entries:
            self._log.debug(
                "shortlisted %s (%s, %dx%d)",
                entry.candidate.qualified_id,
                entry.basis.value,
                entry.size.width,
                entry.size.height,
            )

    # -------------------------------------------------------------- ATTEMPT

    def _attempt(self, run: _RunState) -> None:
        self._enter(Stage.ATTEMPT)
        selection = run.stats.selection
        window = run.window
        if selection is None or window is None:  # pragma: no cover - set by SELECT
            raise RuntimeError("selection missing")
        if selection.provider_stopped:
            # A 403/429 stop: no further request to this provider in this run.
            raise _Terminal(*classify_no_delivery(run.evidence))
        if not selection.entries:
            raise _Terminal(*classify_no_delivery(run.evidence))
        try:
            paths = self._ports.workspace.create()
        except StateError as exc:
            self._log.error("scratch space is unavailable: %s", sanitize_for_log(str(exc)))
            raise _Terminal(Outcome.STATE_ERROR) from None
        for index, entry in enumerate(selection.entries):
            # A stop request swallowed by a port is honoured before new work.
            self._cancel.check()
            if window.attempts.expired():
                run.evidence.limits_reached = True
                break
            artifact = self._attempt_one(run, index, entry, paths, window)
            if artifact is not None:
                run.entry = entry
                run.artifact = artifact
                self._log_chosen(entry, artifact)
                return
            if run.provider_stopped:
                break  # a 403/429 stop: no further request to this provider
        raise _Terminal(*classify_no_delivery(run.evidence))

    def _attempt_one(
        self,
        run: _RunState,
        index: int,
        entry: ShortlistEntry,
        paths: WorkspacePaths,
        window: ContentWindow,
    ) -> DeliveryArtifact | None:
        """FETCH, then PREPARE in the worker, then parent validation (§6, §11)."""
        note = AttemptNote(
            qualified_id=entry.candidate.qualified_id, basis=entry.basis.value, result=""
        )
        run.stats.attempts.append(note)
        fetched = self._fetch(run, entry, index=index, paths=paths, window=window, note=note)
        if fetched is None:
            return None
        output_path = paths.outbox / f"delivery-{index}.jpg"
        result = self._prepare(
            run, entry, fetched=fetched, output_path=output_path, window=window, note=note
        )
        if result is None:
            return None
        return self._verify_output(run, entry, result=result, output_path=output_path, note=note)

    def _fetch(
        self,
        run: _RunState,
        entry: ShortlistEntry,
        *,
        index: int,
        paths: WorkspacePaths,
        window: ContentWindow,
        note: AttemptNote,
    ) -> FetchedImage | None:
        binding = run.binding
        if binding is None:  # pragma: no cover - set by SELECT
            raise RuntimeError("provider missing")
        qualified_id = entry.candidate.qualified_id
        try:
            ref = binding.provider.full_ref(entry.candidate)
            fetched = self._ports.fetcher.fetch(
                ref, paths.inbox / f"source-{index}.bin", window.download()
            )
        except SourceError as exc:
            if exc.kind is SourceErrorKind.NOT_FOUND:
                note.result = "not_found"
            else:
                note.result = "transport"
                run.evidence.attempt_transport_failure = True
                run.provider_stopped = exc.kind is SourceErrorKind.STOPPED
            self._log.warning("download of %s failed: %s", qualified_id, exc.kind.value)
            return None
        except DeadlineExceeded:
            if window.attempts.expired():
                # Cut off by the content window: the search limits were reached.
                note.result = "deadline"
                run.evidence.limits_reached = True
            else:
                # The download's own time limit: a transport failure (§4.2).
                note.result = "transport"
                run.evidence.attempt_transport_failure = True
            self._log.warning("download of %s ran out of time", qualified_id)
            return None
        sniffed = sniff_file(fetched.path)
        if sniffed is None or sniffed is not fetched.declared_format:
            note.result = "failed:format_mismatch"
            run.evidence.processing_failure = True
            self._log.warning("%s is not the declared image format", qualified_id)
            return None
        return fetched

    def _prepare(
        self,
        run: _RunState,
        entry: ShortlistEntry,
        *,
        fetched: FetchedImage,
        output_path: Path,
        window: ContentWindow,
        note: AttemptNote,
    ) -> PrepareResult | None:
        options = self._options(run)
        qualified_id = entry.candidate.qualified_id
        request = PrepareRequest(
            source_path=str(fetched.path),
            output_path=str(output_path),
            declared_format=fetched.declared_format,
            fit_mode=options.fit_mode,
            background=options.background,
            landscape_only=options.landscape_only,
            require_near_16_9=entry.require_near_16_9,
        )
        prepare_deadline = window.prepare()
        try:
            timeout = prepare_deadline.clamp(PREPARE_S)
        except DeadlineExceeded:
            note.result = "deadline"
            run.evidence.limits_reached = True
            return None
        self._cancel.check()
        try:
            raw = self._ports.executor.run(PREPARE_TASK, request.to_json(), timeout=timeout)
            result = PrepareResult.from_json(raw)
        except WorkerError as exc:
            cut_by_window = (
                window.attempts.expired()
                or prepare_deadline.expires_at >= window.attempts.expires_at
            )
            if exc.kind is WorkerErrorKind.TIMEOUT and cut_by_window:
                # Cut off by the content window, not by the task's own limit.
                note.result = "deadline"
                run.evidence.limits_reached = True
            else:
                note.result = f"failed:worker_{exc.kind.value}"
                run.evidence.processing_failure = True
            self._log.warning("preparing %s failed: %s", qualified_id, exc.kind.value)
            return None
        except ValueError:
            note.result = "failed:worker_protocol"
            run.evidence.processing_failure = True
            self._log.warning("preparing %s returned an invalid result", qualified_id)
            return None
        if result.status is PrepareStatus.FAILED:
            reason = result.failure.value if result.failure is not None else "unknown"
            note.result = f"failed:{reason}"
            run.evidence.processing_failure = True
            self._log.warning("preparing %s failed: %s", qualified_id, reason)
            return None
        return result

    def _verify_output(
        self,
        run: _RunState,
        entry: ShortlistEntry,
        *,
        result: PrepareResult,
        output_path: Path,
        note: AttemptNote,
    ) -> DeliveryArtifact | None:
        options = self._options(run)
        qualified_id = entry.candidate.qualified_id
        rejection = result.rejection
        oriented = result.oriented_size
        if result.status is PrepareStatus.OK and oriented is not None:
            # Defence in depth: verify the chosen reason again on the real size.
            rejection = check_rendition(
                oriented,
                fit_mode=options.fit_mode,
                landscape_only=options.landscape_only,
                require_near_16_9=entry.require_near_16_9,
            )
        if result.status is PrepareStatus.REJECTED or rejection is not None:
            rule = "unknown" if rejection is None else rejection.value
            note.result = f"rejected:{rule}"
            self._log.info("%s does not qualify after all: %s", qualified_id, rule)
            return None
        try:
            artifact = validate_delivery(output_path)
        except DeliveryValidationError as exc:
            note.result = "failed:invalid_output"
            run.evidence.processing_failure = True
            self._log.error(
                "the prepared image for %s is invalid: %s",
                qualified_id,
                sanitize_for_log(str(exc)),
            )
            return None
        note.result = "prepared"
        return artifact

    def _log_chosen(self, entry: ShortlistEntry, artifact: DeliveryArtifact) -> None:
        attribution = entry.candidate.attribution
        parts = [
            part for part in (attribution.creator, attribution.title, attribution.date_text) if part
        ]
        self._log.info(
            "chosen: %s (%s) sha256=%s %s",
            entry.candidate.qualified_id,
            entry.basis.value,
            artifact.sha256,
            sanitize_for_log(". ".join(parts)) if parts else "(no attribution)",
        )

    # ------------------------------------------------------------ PRE-STAGE

    def _prestage(self, run: _RunState) -> None:
        self._enter(Stage.PRE_STAGE)
        entry = run.entry
        if entry is None:  # pragma: no cover - set by ATTEMPT
            raise RuntimeError("no candidate")
        qualified_id = entry.candidate.qualified_id
        now = self._clock.utc_now()
        run.prestage_attempted = True
        try:
            self._ports.state.prestage_history(qualified_id, now)
        except StateError as exc:
            self._log.error("history could not be pre-staged: %s", sanitize_for_log(str(exc)))
            raise _Terminal(Outcome.STATE_ERROR) from None
        run.prestaged = True
        if not self._run_budget().television_reserve_available():
            self._log.error("not enough time left for the television; the TV was not contacted")
            raise _Terminal(Outcome.DEADLINE_EXCEEDED)
        self._cancel.check()
        run.intent_attempted = True
        try:
            self._ports.state.commit_upload_intent(qualified_id, now)
        except StateError as exc:
            self._log.error(
                "the upload intent could not be recorded: %s", sanitize_for_log(str(exc))
            )
            raise _Terminal(Outcome.STATE_ERROR) from None

    # -------------------------------------------------------------- DELIVER

    def _deliver(self, run: _RunState) -> None:
        self._enter(Stage.DELIVER)
        options = self._options(run)
        entry, artifact = run.entry, run.artifact
        if entry is None or artifact is None:  # pragma: no cover - set by ATTEMPT
            raise RuntimeError("nothing to deliver")
        qualified_id = entry.candidate.qualified_id
        request = DeliveryRequest(
            jpeg_path=artifact.path,
            jpeg_sha256=artifact.sha256,
            tv_host=options.tv_host,
            deadline=self._run_budget().phase(Phase.DELIVER),
            stop_requested=self._stop_requested,
        )
        reply = self._call_television(run, request, qualified_id)
        if reply.status is None:
            # §7.6: the worker group is killed before the markers are read.
            self._terminate_workers()
        if reply.failure is not None:
            failure = reply.failure
            self._log.error(
                "the television step failed unexpectedly",
                exc_info=(type(failure), failure, failure.__traceback__),
            )
        for marker in reply.reported:
            self._take_marker(run, marker, qualified_id)
        if reply.detail:
            self._log.info("television: %s", sanitize_for_log(reply.detail))
        self._conclude_delivery(run, reply, qualified_id)

    def _call_television(
        self, run: _RunState, request: DeliveryRequest, qualified_id: str
    ) -> _TelevisionReply:
        """Call the port with stop requests deferred from here to the end of the
        run (§7.6, D-141).

        No SIGTERM can split a marker from its ledger write, or drop a marker or
        the port's reply: the adapter learns of a stop request through
        ``request.stop_requested``, kills its worker, and returns the markers
        seen; the run is then classified as cancelled.
        """

        def on_marker(event: MarkerEvent) -> None:
            self._take_marker(run, event.marker, qualified_id)

        reply = _TelevisionReply()
        self._cancel.check()
        self._cancel.begin_deferral()
        run.television_contacted = True
        try:
            result: DeliveryResult = self._ports.television.deliver(request, on_marker)
            reply.status, reply.reported, reply.detail = (
                result.status,
                result.markers_seen,
                result.detail,
            )
        except Cancelled:
            reply.cancelled = True
        except DeadlineExceeded:
            self._log.error("the television step ran out of time")
        except Exception as exc:  # noqa: BLE001 - classified from the markers
            reply.failure = exc
        reply.cancelled = reply.cancelled or self._cancel.stop_requested
        return reply

    def _stop_requested(self) -> bool:
        return self._cancel.stop_requested

    def _conclude_delivery(
        self, run: _RunState, reply: _TelevisionReply, qualified_id: str
    ) -> None:
        verdict = classify_delivery(run.markers, reply.status, cancelled=reply.cancelled)
        self._log.info(
            "television result: status=%s markers=%s",
            "none" if reply.status is None else reply.status.value,
            ",".join(m.value for m in run.markers) or "none",
        )
        if verdict.selected:
            run.selected = True
            if reply.failure is not None:
                run.warnings.append("television_result_invalid")
            return
        if reply.failure is not None:
            # Not selected: an adapter failure is a bug. A committed intent
            # stays as quarantine (§4.2, internal_error).
            raise reply.failure
        if verdict.ledger is LedgerAction.REMOVE_INTENT:
            self._remove_intent(qualified_id)
        elif verdict.ledger is LedgerAction.KEEP_UNCERTAIN:
            self._log.warning("%s stays in the upload quarantine", qualified_id)
        if verdict.outcome is None:  # pragma: no cover - classify_delivery always sets it
            raise RuntimeError("unclassified television result")
        raise _Terminal(verdict.outcome, verdict.hint)

    def _take_marker(self, run: _RunState, marker: Marker, qualified_id: str) -> None:
        """Record one marker; ``uploaded`` (or ``selected``) promotes the entry."""
        if marker not in run.markers:
            run.markers.append(marker)
        if marker is Marker.SELECTED and Marker.UPLOADED not in run.markers:
            self._log.warning("the television reported selected without uploaded")
        if marker in (Marker.UPLOADED, Marker.SELECTED) and not run.promoted:
            self._promote(run, qualified_id)
        if marker is Marker.SELECTED:
            # Stop requests are deferred already: RECORD always follows (§12.3).
            run.selected = True

    def _terminate_workers(self) -> None:
        try:
            self._ports.executor.terminate_all()
        except Exception:  # noqa: BLE001 - best-effort; cleanup repeats it
            self._log.exception("terminating the workers failed")

    def _promote(self, run: _RunState, qualified_id: str) -> None:
        try:
            self._ports.state.promote_upload(qualified_id, self._clock.utc_now())
        except Exception as exc:  # noqa: BLE001 - the ledger stays conservative
            # The intent stays ``uncertain``: the work is still excluded for the
            # quarantine period. The outcome does not change (§13.6 step 4).
            self._log.error(
                "the confirmed upload of %s could not be recorded: %s",
                qualified_id,
                sanitize_for_log(str(exc)),
                exc_info=not isinstance(exc, StateError),
            )
            return
        run.promoted = True

    def _remove_intent(self, qualified_id: str) -> None:
        try:
            self._ports.state.remove_upload_intent(qualified_id)
        except Exception as exc:  # noqa: BLE001 - the ledger stays conservative
            self._log.error(
                "the upload intent for %s could not be removed; it stays in quarantine: %s",
                qualified_id,
                sanitize_for_log(str(exc)),
                exc_info=not isinstance(exc, StateError),
            )

    # --------------------------------------------------------- RECORD, PUBLISH

    def _record(self, run: _RunState) -> None:
        self._enter(Stage.RECORD)
        run.record_attempted = True
        run.finish_deadline = self._run_budget().phase(Phase.FINISH)
        try:
            self._ports.state.record_history()
        except StateError as exc:
            run.unrecorded = True
            self._log.error("the delivery could not be recorded: %s", sanitize_for_log(str(exc)))
            return
        run.recorded = True

    def _publish(self, run: _RunState) -> None:
        self._enter(Stage.PUBLISH)
        entry, artifact, finish = run.entry, run.artifact, run.finish_deadline
        if entry is None or artifact is None or finish is None:  # pragma: no cover
            raise RuntimeError("nothing to publish")
        # PUBLISH may not use FINISH's last seconds: the last-run record needs them.
        deadline = finish.cap_at(finish.expires_at - LAST_RUN_RESERVE_S, "publish")
        if self._cancel.stop_requested:
            run.warnings.append("preview_skipped")
            self._log.warning("stop requested: the preview was not updated")
            return
        try:
            self._ports.preview.publish(artifact, deadline)
        except (PublishError, StateError, DeadlineExceeded) as exc:
            run.warnings.append("preview_failed")
            self._log.warning("the preview could not be updated: %s", sanitize_for_log(str(exc)))
        record = build_current_record(
            qualified_id=entry.candidate.qualified_id,
            attribution=entry.candidate.attribution,
            sha256=artifact.sha256,
            delivered_at=self._clock.utc_now(),
            preview_fingerprint=artifact.fingerprint,
        )
        try:
            self._ports.records.write_current(record, deadline)
        except (StateError, DeadlineExceeded) as exc:
            run.warnings.append("current_failed")
            self._log.warning(
                "the current-artwork record could not be written: %s", sanitize_for_log(str(exc))
            )

    # ------------------------------------------------------- settle, FINISH

    def _settle(self, run: _RunState) -> None:
        """Reconcile state once the outcome is known; stop requests are deferred.

        - After ``selected``, RECORD always runs (§12.3), even when an internal
          error ended the stage sequence first.
        - Otherwise the pre-staged history generation is discarded, and the
          upload intent follows the rules of §7.6 and §13.6.
        """
        if run.selected:
            if not run.record_attempted:
                self._record(run)
            return
        if run.prestage_attempted:
            # Also after an interrupted pre-staging: the port may have written it.
            self._ports.state.discard_prestaged_history()
        entry = run.entry
        if not run.intent_attempted or entry is None or run.outcome is Outcome.INTERNAL_ERROR:
            # After an internal error a committed intent stays as quarantine.
            return
        if not run.television_contacted:
            # The television was never contacted: the intent can go (§7.6).
            # Once it was contacted, DELIVER applied the marker-based action
            # itself, with stop requests deferred.
            self._remove_intent(entry.candidate.qualified_id)

    def _finish(self, run: _RunState) -> RunResult:
        self._enter(Stage.FINISH)
        budget = self._run_budget()
        outcome = self._final_outcome(run)
        deadline = self._finish_deadline(run)
        self._flush_cache(run, deadline)
        artwork_id = run.entry.candidate.qualified_id if run.selected and run.entry else None
        record = build_last_run_record(
            outcome=outcome,
            hint=run.hint,
            started_at=run.started_wall,
            finished_at=self._clock.utc_now(),
            elapsed_s=budget.elapsed(),
            filters=run.filters,
            stats=run.stats,
            artwork_id=artwork_id,
        )
        try:
            self._ports.records.write_last_run(record, deadline)
        except Exception as exc:  # noqa: BLE001 - a lost record never loses the summary line
            self._log.warning(
                "the last-run record could not be written: %s",
                sanitize_for_log(str(exc)),
                exc_info=not isinstance(exc, (StateError, DeadlineExceeded)),
            )
            if outcome is Outcome.DELIVERED:
                outcome = Outcome.DELIVERED_WITH_WARNINGS
        ignored = tuple(i.describe() for i in run.filters.ignored) if run.filters else ()
        summary = format_summary(
            outcome=outcome.value,
            exit_code=outcome.exit_code,
            elapsed_s=budget.elapsed(),
            ignored=ignored,
            hint=run.hint,
        )
        return RunResult(
            outcome=outcome,
            exit_code=outcome.exit_code,
            hint=run.hint,
            elapsed_s=budget.elapsed(),
            summary_line=summary,
            stages=tuple(self._stages),
            delivered_id=artwork_id,
            ignored_filters=ignored,
        )

    def _flush_cache(self, run: _RunState, deadline: Deadline) -> None:
        """Write the provider's metadata cache once; it may not use the
        last-run record's reserve, and it never changes the outcome (§13.4)."""
        cache = run.binding.cache if run.binding is not None else None
        if cache is None:
            return
        try:
            cache.flush(deadline.cap_at(deadline.expires_at - LAST_RUN_RESERVE_S, "cache"))
        except Exception:  # noqa: BLE001 - a cache is never worth an outcome
            self._log.warning("the metadata cache could not be written", exc_info=True)

    @staticmethod
    def _final_outcome(run: _RunState) -> Outcome:
        if run.selected and run.outcome in (None, Outcome.CANCELLED):
            # After ``selected`` a stop request never turns the run into
            # ``cancelled`` (§7.6); an internal error still reports itself.
            if run.unrecorded:
                return Outcome.DELIVERED_UNRECORDED
            if run.warnings:
                return Outcome.DELIVERED_WITH_WARNINGS
            return Outcome.DELIVERED
        if run.outcome is None:  # pragma: no cover - every other path sets an outcome
            return Outcome.INTERNAL_ERROR
        return run.outcome

    def _finish_deadline(self, run: _RunState) -> Deadline:
        if run.finish_deadline is not None:
            return run.finish_deadline
        window = run.window
        if (
            window is not None
            and not run.prestaged
            and window.window.remaining() >= PRESTAGE_RESERVE_S
        ):
            # A run decided in SELECT or ATTEMPT ends by the end of its content
            # window (70 s, C11); honest ports leave it the 2 s reserve.
            return window.window
        # Otherwise FINISH has its own reserve (§7.3).
        return self._run_budget().phase(Phase.FINISH)

    def _fallback_result(self, run: _RunState) -> RunResult:
        """The result when FINISH itself failed: still one classified line."""
        budget = self._run_budget()
        outcome = Outcome.INTERNAL_ERROR
        summary = format_summary(
            outcome=outcome.value, exit_code=outcome.exit_code, elapsed_s=budget.elapsed()
        )
        return RunResult(
            outcome=outcome,
            exit_code=outcome.exit_code,
            hint=None,
            elapsed_s=budget.elapsed(),
            summary_line=summary,
            stages=tuple(self._stages),
            delivered_id=run.entry.candidate.qualified_id if run.selected and run.entry else None,
        )

    def _cleanup(self) -> None:
        """Kill workers and remove the workspace on every path; never raises."""
        for action in (
            self._ports.executor.terminate_all,
            self._ports.workspace.remove,
            self._ports.state.close,
            self._ports.storage_report,
        ):
            try:
                action()
            except Exception:  # noqa: BLE001 - cleanup is best-effort by design
                self._log.exception("cleanup step failed")

    def _disarm_watchdog(self) -> bool:
        """Stop the watchdog last; ``False`` if it had already claimed the run."""
        try:
            return self._ports.watchdog.disarm()
        except Exception:  # noqa: BLE001 - cleanup is best-effort by design
            self._log.exception("cleanup step failed")
            return True

    # -------------------------------------------------------------- helpers

    def _run_budget(self) -> RunBudget:
        if self._budget is None:  # pragma: no cover - set by run()
            raise RuntimeError("no active run")
        return self._budget

    @staticmethod
    def _options(run: _RunState) -> Options:
        if run.options is None:  # pragma: no cover - set by CONFIGURE
            raise RuntimeError("options missing")
        return run.options
