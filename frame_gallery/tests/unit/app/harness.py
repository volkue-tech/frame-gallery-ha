"""A configurable runner with fake ports, for the runner tests."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from frame_gallery.app.ports import ProviderBinding
from frame_gallery.app.runner import Runner, RunnerPorts, RunResult
from frame_gallery.app.signals import CancellationController
from frame_gallery.config.filters import FilterDimension
from frame_gallery.config.options import LogLevel
from frame_gallery.config.vocabulary import BUILTIN_VOCABULARY, Vocabulary, VocabularyEntry
from frame_gallery.domain import SourceKey
from frame_gallery.providers.contract import Candidate
from frame_gallery.randomness import SeededRandomSource
from tests.support.clock import FakeClock
from tests.support.fakes import (
    TEST_TV_HOST,
    Events,
    FakeExecutor,
    FakeFetcher,
    FakeHelperReader,
    FakeNetworkInfo,
    FakeOptionsSource,
    FakePreview,
    FakeProvider,
    FakeRecords,
    FakeStateStore,
    FakeTelevision,
    FakeWatchdog,
    FakeWorkspace,
    make_candidate,
)

SYNTHETIC_VOCABULARY = Vocabulary(
    version="test-1",
    entries=(
        VocabularyEntry(
            key="aic_test_paintings",
            label="Test Paintings",
            dimension=FilterDimension.DEPARTMENT,
            source=SourceKey.ART_INSTITUTE_CHICAGO,
        ),
        VocabularyEntry(
            key="cma_test_prints",
            label="Test Prints",
            dimension=FilterDimension.DEPARTMENT,
            source=SourceKey.CLEVELAND_MUSEUM_OF_ART,
        ),
        VocabularyEntry(
            key="style_test_one", label="Test Style One", dimension=FilterDimension.STYLE
        ),
        VocabularyEntry(
            key="period_test_1800_1899",
            label="Test Nineteenth Century",
            dimension=FilterDimension.PERIOD,
        ),
        VocabularyEntry(key="color_test_blue", label="Test Blue", dimension=FilterDimension.COLOR),
    ),
)


def default_candidates() -> list[Candidate]:
    return [make_candidate("1001"), make_candidate("1002"), make_candidate("1003")]


@dataclass
class Harness:
    tmp_path: Path
    raw: dict[str, object] = field(default_factory=lambda: {"tv_host": TEST_TV_HOST})
    candidates: Sequence[Candidate] | None = None
    vocabulary: Vocabulary = BUILTIN_VOCABULARY
    clock: FakeClock = field(default_factory=FakeClock)
    events: Events = field(default_factory=Events)
    cancellation: CancellationController = field(default_factory=CancellationController)
    log_levels: list[LogLevel] = field(default_factory=list)

    def __post_init__(self) -> None:
        clock, events = self.clock, self.events
        self.options = FakeOptionsSource(self.raw, events, clock)
        self.network = FakeNetworkInfo()
        self.state = FakeStateStore(events, clock)
        self.helpers = FakeHelperReader(events)
        candidates = default_candidates() if self.candidates is None else self.candidates
        self.provider = FakeProvider(events, clock, candidates)
        self.cma_provider = FakeProvider(
            events, clock, [], key="cma", source=SourceKey.CLEVELAND_MUSEUM_OF_ART
        )
        self.local_provider = FakeProvider(
            events, clock, [], key="local", source=SourceKey.LOCAL_MEDIA
        )
        self.fetcher = FakeFetcher(events, clock)
        self.executor = FakeExecutor(events, clock)
        self.tv = FakeTelevision(events, clock)
        self.workspace = FakeWorkspace(self.tmp_path, events)
        self.preview = FakePreview(events)
        self.records = FakeRecords(events, clock)
        self.watchdog = FakeWatchdog(events)
        self.logger = logging.getLogger("frame_gallery.test_runner")

    def providers(self) -> Mapping[SourceKey, ProviderBinding]:
        return {
            SourceKey.ART_INSTITUTE_CHICAGO: ProviderBinding(self.provider),
            SourceKey.CLEVELAND_MUSEUM_OF_ART: ProviderBinding(self.cma_provider),
            SourceKey.LOCAL_MEDIA: ProviderBinding(self.local_provider),
        }

    def runner(self) -> Runner:
        ports = RunnerPorts(
            options_source=self.options,
            network_info=self.network,
            state=self.state,
            helper_reader=self.helpers,
            providers=self.providers(),
            fetcher=self.fetcher,
            executor=self.executor,
            television=self.tv,
            workspace=self.workspace,
            preview=self.preview,
            records=self.records,
            watchdog=self.watchdog,
        )
        return Runner(
            ports,
            clock=self.clock,
            random=SeededRandomSource(7),
            cancellation=self.cancellation,
            vocabulary=self.vocabulary,
            logger=self.logger,
            set_log_level=self.log_levels.append,
        )

    def run(self) -> RunResult:
        return self.runner().run()

    def next_run(self) -> RunResult:
        """Another run with the same fakes, as a new process would start it:
        a controller serves exactly one run."""
        self.cancellation = CancellationController()
        return self.run()

    @property
    def last_run(self) -> Mapping[str, object]:
        assert len(self.records.last_run) == 1
        return self.records.last_run[0]
