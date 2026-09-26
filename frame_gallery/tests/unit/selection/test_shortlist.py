"""The single-pass discovery and shortlist (§8.2, §8.3, D-117, D-134, D-137).

Candidates are synthetic Art Institute works (``aic:<n>``, CC0); time moves
only when a fake source advances the :class:`FakeClock`.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterable, Iterator, Mapping, MutableSequence, Sequence
from dataclasses import dataclass

import pytest

from frame_gallery.budget.allowance import Allowance
from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.budget.limits import (
    CANDIDATE_ALLOWANCE,
    LOCAL_INSPECTION_ALLOWANCE,
    PROBE_REQUEST_S,
    REMOTE_PROBE_ALLOWANCE,
    SHORTLIST_SIZE,
)
from frame_gallery.budget.phases import DISCOVERY_S
from frame_gallery.domain import FitMode, Size
from frame_gallery.errors import Cancelled
from frame_gallery.providers.contract import (
    Attribution,
    Candidate,
    DimensionProbe,
    DimensionSource,
    SourceError,
    SourceErrorKind,
)
from frame_gallery.providers.rights import RightsBasis
from frame_gallery.randomness import RandomSource, SeededRandomSource
from frame_gallery.selection.exclusion import ExclusionSet
from frame_gallery.selection.geometry import Rejection
from frame_gallery.selection.shortlist import (
    ChoiceBasis,
    DecisionSink,
    DiscoveryEnd,
    SelectionPolicy,
    SelectionResult,
    SelectionStats,
    ShortlistEntry,
    build_shortlist,
)
from tests.support.clock import FakeClock

STRICT = Size(3840, 2160)
"""Exactly 16:9."""

STRICT_EDGE = Size(1616, 900)
"""The widest near-16:9 ratio, ``(16/9) * 1.01``."""

NEARLY = Size(2400, 1500)
"""1.6:1 landscape, the closest fallback below (``|ln 0.9|``)."""

WIDE = Size(3000, 1500)
"""2:1 landscape (``ln 1.125``)."""

WIDER = Size(3000, 1200)
"""2.5:1 landscape, the farthest fallback (``ln 1.40625``)."""

PORTRAIT = Size(2000, 3000)
SQUARE = Size(2400, 2400)
TINY = Size(640, 360)
"""16:9, but a 6x upscale onto the canvas."""

STRICT_CONTAIN = SelectionPolicy(
    landscape_only=True, strict_tv_format=True, fit_mode=FitMode.CONTAIN
)
RELAXED = SelectionPolicy(landscape_only=True, strict_tv_format=False, fit_mode=FitMode.CONTAIN)
STRICT_COVER = SelectionPolicy(landscape_only=True, strict_tv_format=True, fit_mode=FitMode.COVER)
STRICT_ANY_SHAPE = SelectionPolicy(
    landscape_only=False, strict_tv_format=True, fit_mode=FitMode.CONTAIN
)
CC0_ONLY = frozenset({RightsBasis.CC0})
NO_EXCLUSIONS = ExclusionSet()

TRANSPORT_KINDS = [
    SourceErrorKind.TRANSPORT,
    SourceErrorKind.TIMEOUT,
    SourceErrorKind.HTTP_ERROR,
    SourceErrorKind.OVER_CAP,
    SourceErrorKind.UNEXPECTED_FORMAT,
]


def work(
    native_id: int, dims: Size | None = STRICT, *, rights: RightsBasis = RightsBasis.CC0
) -> Candidate:
    return Candidate(
        provider_key="aic",
        native_id=str(native_id),
        rights_basis=rights,
        rights_field="is_public_domain",
        attribution=Attribution(title=f"Work {native_id}"),
        dims=dims,
    )


def works(first: int, count: int, dims: Size | None) -> list[Candidate]:
    return [work(first + offset, dims) for offset in range(count)]


class ScriptedSource:
    """A lazy provider stream that counts pulls.

    Each pull first advances the clock by ``step_s``, like a slow request,
    then yields the next candidate or raises the next scripted exception.
    """

    def __init__(
        self,
        script: Iterable[Candidate | BaseException],
        *,
        clock: FakeClock | None = None,
        step_s: float = 0.0,
    ) -> None:
        self._script = iter(script)
        self._clock = clock
        self._step_s = step_s
        self.pulls = 0

    def __iter__(self) -> Iterator[Candidate]:
        return self

    def __next__(self) -> Candidate:
        self.pulls += 1
        if self._clock is not None:
            self._clock.advance(self._step_s)
        item = next(self._script)
        if isinstance(item, BaseException):
            raise item
        return item


class FakeProbe:
    """A counting dimension probe with scripted outcomes per qualified id."""

    def __init__(
        self,
        source: DimensionSource,
        default: Size | None = PORTRAIT,
        outcomes: Mapping[str, Size | BaseException | None] | None = None,
    ) -> None:
        self._source = source
        self._default = default
        self._outcomes = dict(outcomes or {})
        self.calls: list[str] = []
        self.deadlines: list[Deadline] = []

    @property
    def source(self) -> DimensionSource:
        return self._source

    def measure(self, candidate: Candidate, deadline: Deadline) -> Size | None:
        self.calls.append(candidate.qualified_id)
        self.deadlines.append(deadline)
        outcome = self._outcomes.get(candidate.qualified_id, self._default)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class CountingRandom:
    """A seeded source that counts draws and allows only ``random()``."""

    def __init__(self, seed: int = 0, values: Sequence[float] | None = None) -> None:
        self._seeded = SeededRandomSource(seed)
        self._values = list(values) if values is not None else None
        self.draws = 0

    def random(self) -> float:
        self.draws += 1
        if self._values is not None:
            return self._values[self.draws - 1]
        return self._seeded.random()

    def randrange(self, stop: int) -> int:
        pytest.fail("selection must not call randrange")

    def shuffle[T](self, items: MutableSequence[T]) -> None:
        pytest.fail("selection must not shuffle")


@dataclass
class Budget:
    clock: FakeClock
    deadline: Deadline
    candidates: Allowance
    probes: Allowance
    inspections: Allowance


def make_budget(*, candidate_limit: int = CANDIDATE_ALLOWANCE) -> Budget:
    clock = FakeClock()
    return Budget(
        clock=clock,
        deadline=Deadline.after(clock, DISCOVERY_S, "discovery"),
        candidates=Allowance("candidates", candidate_limit),
        probes=Allowance("probes", REMOTE_PROBE_ALLOWANCE),
        inspections=Allowance("inspections", LOCAL_INSPECTION_ALLOWANCE),
    )


def select(
    candidates: Iterable[Candidate],
    *,
    budget: Budget | None = None,
    policy: SelectionPolicy = STRICT_CONTAIN,
    exclusions: ExclusionSet = NO_EXCLUSIONS,
    allowed_rights: frozenset[RightsBasis] = CC0_ONLY,
    random: RandomSource | None = None,
    probe: DimensionProbe | None = None,
    shortlist_size: int = SHORTLIST_SIZE,
    on_decision: DecisionSink | None = None,
) -> SelectionResult:
    run_budget = budget if budget is not None else make_budget()
    return build_shortlist(
        candidates,
        exclusions=exclusions,
        policy=policy,
        allowed_rights=allowed_rights,
        deadline=run_budget.deadline,
        random=random if random is not None else CountingRandom(),
        candidate_allowance=run_budget.candidates,
        probe_allowance=run_budget.probes,
        inspection_allowance=run_budget.inspections,
        probe=probe,
        shortlist_size=shortlist_size,
        on_decision=on_decision,
    )


def ids(result: SelectionResult) -> list[str]:
    return [entry.candidate.qualified_id for entry in result.entries]


def bases(result: SelectionResult) -> list[ChoiceBasis]:
    return [entry.basis for entry in result.entries]


# --- Arguments --------------------------------------------------------------


@pytest.mark.parametrize("size", [0, -2, True])
def test_rejects_a_shortlist_size_below_one(size: int) -> None:
    source = ScriptedSource(works(1001, 3, STRICT))
    with pytest.raises(ValueError, match="shortlist_size must be a positive integer"):
        select(source, shortlist_size=size)
    assert source.pulls == 0


def test_defaults_to_the_shortlist_of_two_and_no_probe() -> None:
    budget = make_budget()
    result = build_shortlist(
        [*works(1001, 5, STRICT), work(2001, None)],
        exclusions=NO_EXCLUSIONS,
        policy=STRICT_CONTAIN,
        allowed_rights=CC0_ONLY,
        deadline=budget.deadline,
        random=CountingRandom(),
        candidate_allowance=budget.candidates,
        probe_allowance=budget.probes,
        inspection_allowance=budget.inspections,
    )
    assert ids(result) == ["aic:1001", "aic:1002"]


# --- Strict and first-eligible entries --------------------------------------


def test_strict_matches_fill_the_shortlist_and_stop_pulling() -> None:
    source = ScriptedSource(works(1001, 12, STRICT))
    random = CountingRandom()
    result = select(source, random=random)
    assert ids(result) == ["aic:1001", "aic:1002"]
    assert bases(result) == [ChoiceBasis.STRICT, ChoiceBasis.STRICT]
    assert all(entry.size == STRICT for entry in result.entries)
    assert result.end is DiscoveryEnd.SHORTLIST_FULL
    assert source.pulls == 2
    assert result.stats == SelectionStats(candidates_seen=2, evaluated=2)
    assert result.provider_error is None
    assert not result.limits_reached
    assert not result.transport_failure
    assert not result.provider_stopped
    assert random.draws == 0


def test_a_shortlist_of_one_stops_after_the_first_match() -> None:
    source = ScriptedSource([work(1001, PORTRAIT), *works(1002, 5, STRICT_EDGE)])
    result = select(source, shortlist_size=1)
    assert ids(result) == ["aic:1002"]
    assert result.end is DiscoveryEnd.SHORTLIST_FULL
    assert source.pulls == 2


def test_first_eligible_entries_keep_pull_order_when_strict_is_off() -> None:
    source = ScriptedSource(
        [work(1001, WIDE), work(1002, PORTRAIT), work(1003, STRICT), work(1004, WIDER)]
    )
    random = CountingRandom()
    result = select(source, policy=RELAXED, random=random)
    assert ids(result) == ["aic:1001", "aic:1003"]
    assert bases(result) == [ChoiceBasis.FIRST_ELIGIBLE, ChoiceBasis.FIRST_ELIGIBLE]
    assert [entry.size for entry in result.entries] == [WIDE, STRICT]
    assert result.end is DiscoveryEnd.SHORTLIST_FULL
    assert source.pulls == 3
    assert result.stats.rejected == {Rejection.NOT_LANDSCAPE.value: 1}
    assert result.stats.fallback_offered == 0
    assert random.draws == 0


def test_first_eligible_accepts_any_shape_when_landscape_only_is_off() -> None:
    policy = SelectionPolicy(landscape_only=False, strict_tv_format=False, fit_mode=FitMode.CONTAIN)
    result = select([work(1001, PORTRAIT), work(1002, SQUARE)], policy=policy)
    assert ids(result) == ["aic:1001", "aic:1002"]
    assert bases(result) == [ChoiceBasis.FIRST_ELIGIBLE, ChoiceBasis.FIRST_ELIGIBLE]


def test_portrait_and_square_are_rejected_when_landscape_only() -> None:  # C2
    for policy in (STRICT_CONTAIN, RELAXED, STRICT_COVER):
        result = select([work(1001, PORTRAIT), work(1002, SQUARE)], policy=policy)
        assert result.entries == ()
        assert result.end is DiscoveryEnd.EXHAUSTED
        assert result.stats.rejected == {Rejection.NOT_LANDSCAPE.value: 2}


def test_too_small_works_are_rejected_before_their_shape() -> None:
    result = select([work(1001, TINY), work(1002, Size(300, 600)), work(1003, PORTRAIT)])
    assert result.entries == ()
    assert result.stats.rejected == {
        Rejection.TOO_SMALL.value: 2,
        Rejection.NOT_LANDSCAPE.value: 1,
    }
    assert type(result.stats.rejected) is dict


def test_too_small_depends_on_the_fit_mode() -> None:
    wide = Size(1600, 500)
    contain = select([work(1001, wide)], policy=RELAXED)
    assert ids(contain) == ["aic:1001"]
    cover = SelectionPolicy(landscape_only=True, strict_tv_format=False, fit_mode=FitMode.COVER)
    result = select([work(1001, wide)], policy=cover)
    assert result.entries == ()
    assert result.stats.rejected == {Rejection.TOO_SMALL.value: 1}


def test_the_policy_canvas_is_used() -> None:
    small_canvas = SelectionPolicy(
        landscape_only=True,
        strict_tv_format=True,
        fit_mode=FitMode.CONTAIN,
        canvas=Size(1280, 720),
    )
    assert ids(select([work(1001, TINY)], policy=small_canvas)) == ["aic:1001"]
    assert select([work(1001, TINY)]).stats.rejected == {Rejection.TOO_SMALL.value: 1}


# --- Exclusions and the candidate allowance ---------------------------------


def test_excluded_candidates_are_skipped_without_charge() -> None:
    exclusions = ExclusionSet(
        history=frozenset({"aic:1001"}),
        uploaded=frozenset({"aic:1002"}),
        uncertain=frozenset({"aic:1003"}),
    )
    budget = make_budget(candidate_limit=1)
    probe = FakeProbe(DimensionSource.REMOTE_PROBE)
    source = ScriptedSource(
        [work(1001, None), work(1002, None), work(1003, None), work(1004, STRICT)]
    )
    result = select(source, budget=budget, exclusions=exclusions, probe=probe, shortlist_size=1)
    assert ids(result) == ["aic:1004"]
    assert result.end is DiscoveryEnd.SHORTLIST_FULL
    assert result.stats == SelectionStats(candidates_seen=4, excluded=3, evaluated=1)
    assert budget.candidates.used == 1
    assert probe.calls == []


def test_only_excluded_candidates_end_exhausted() -> None:
    candidates = works(1001, 5, STRICT)
    exclusions = ExclusionSet(history=frozenset(c.qualified_id for c in candidates))
    result = select(candidates, exclusions=exclusions)
    assert result.entries == ()
    assert result.end is DiscoveryEnd.EXHAUSTED
    assert result.stats == SelectionStats(candidates_seen=5, excluded=5)
    assert not result.limits_reached


def test_candidate_allowance_ends_discovery_after_150_evaluations() -> None:
    budget = make_budget()
    source = ScriptedSource(works(1001, 200, PORTRAIT))
    result = select(source, budget=budget)
    assert result.end is DiscoveryEnd.CANDIDATE_ALLOWANCE
    assert result.stats.evaluated == CANDIDATE_ALLOWANCE == 150
    assert result.stats.candidates_seen == 151
    assert source.pulls == 151
    assert result.stats.rejected == {Rejection.NOT_LANDSCAPE.value: 150}
    assert budget.candidates.exhausted
    assert result.limits_reached


def test_excluded_candidates_do_not_count_towards_the_allowance() -> None:
    portraits = works(1001, 300, PORTRAIT)
    excluded = frozenset(c.qualified_id for c in portraits[::2])
    source = ScriptedSource([*portraits[:299], work(2001, STRICT)])
    result = select(source, exclusions=ExclusionSet(history=excluded))
    # 150 excluded and 149 rejected portraits; the 150th evaluation still qualifies.
    assert ids(result) == ["aic:2001"]
    assert result.end is DiscoveryEnd.EXHAUSTED
    assert result.stats.excluded == 150
    assert result.stats.evaluated == 150


def test_an_empty_allowance_ends_at_the_first_evaluation() -> None:
    budget = make_budget(candidate_limit=0)
    exclusions = ExclusionSet(uploaded=frozenset({"aic:1001"}))
    source = ScriptedSource(works(1001, 5, STRICT))
    result = select(source, budget=budget, exclusions=exclusions)
    assert result.entries == ()
    assert result.end is DiscoveryEnd.CANDIDATE_ALLOWANCE
    assert result.stats == SelectionStats(candidates_seen=2, excluded=1)
    assert source.pulls == 2


def test_the_allowance_end_still_fills_fallbacks() -> None:
    budget = make_budget(candidate_limit=2)
    source = ScriptedSource([work(1001, WIDER), work(1002, WIDE), work(1003, STRICT)])
    result = select(source, budget=budget)
    assert ids(result) == ["aic:1002", "aic:1001"]
    assert bases(result) == [ChoiceBasis.FALLBACK, ChoiceBasis.FALLBACK]
    assert result.end is DiscoveryEnd.CANDIDATE_ALLOWANCE
    assert result.stats.candidates_seen == 3


def test_an_empty_source_is_exhausted() -> None:
    result = select(ScriptedSource([]))
    assert result.entries == ()
    assert result.end is DiscoveryEnd.EXHAUSTED
    assert result.stats == SelectionStats()
    assert result.provider_error is None
    assert not result.limits_reached
    assert not result.transport_failure
    assert not result.provider_stopped


def test_a_plain_list_is_accepted() -> None:
    result = select([work(1001, WIDE), work(1002, STRICT)])
    assert ids(result) == ["aic:1002", "aic:1001"]
    assert result.end is DiscoveryEnd.EXHAUSTED


# --- Rights (D-134) ---------------------------------------------------------


def test_a_rights_basis_outside_the_allowlist_is_rejected_and_charged() -> None:
    probe = FakeProbe(DimensionSource.REMOTE_PROBE, default=STRICT)
    budget = make_budget()
    source = [
        work(1001, None, rights=RightsBasis.USER_SUPPLIED),
        work(1002, STRICT, rights=RightsBasis.USER_SUPPLIED),
        work(1003, STRICT),
    ]
    result = select(source, budget=budget, probe=probe)
    assert ids(result) == ["aic:1003"]
    assert result.stats.rights_rejected == 2
    assert result.stats.evaluated == 3
    assert budget.candidates.used == 3
    assert probe.calls == []


def test_the_allowlist_is_whatever_the_caller_passes() -> None:
    local = frozenset({RightsBasis.USER_SUPPLIED})
    source = [work(1001, STRICT), work(1002, STRICT, rights=RightsBasis.USER_SUPPLIED)]
    result = select(source, allowed_rights=local)
    assert ids(result) == ["aic:1002"]
    assert result.stats.rights_rejected == 1


# --- Dimensions, probes, and inspections (§8.3) -----------------------------


def test_missing_dimensions_without_a_probe_are_unavailable() -> None:
    result = select([work(1001, None), work(1002, STRICT)])
    assert ids(result) == ["aic:1002"]
    assert result.stats.dims_unavailable == 1
    assert result.stats.probes_used == 0


def test_probed_dimensions_are_used_for_the_entry() -> None:
    probe = FakeProbe(DimensionSource.REMOTE_PROBE, default=STRICT_EDGE)
    result = select([work(1001, None)], probe=probe)
    assert result.entries == (ShortlistEntry(work(1001, None), STRICT_EDGE, ChoiceBasis.STRICT),)
    assert result.stats.probes_used == 1


def test_metadata_dimensions_are_never_probed() -> None:
    probe = FakeProbe(DimensionSource.REMOTE_PROBE)
    result = select(works(1001, 2, STRICT), probe=probe)
    assert probe.calls == []
    assert result.stats.probes_used == 0


def test_remote_probes_never_exceed_30_requests() -> None:  # C4
    budget = make_budget()
    probe = FakeProbe(DimensionSource.REMOTE_PROBE, default=PORTRAIT)
    candidates = works(1001, 100, None)
    result = select(candidates, budget=budget, probe=probe)
    assert len(probe.calls) == REMOTE_PROBE_ALLOWANCE == 30
    assert probe.calls == [c.qualified_id for c in candidates[:30]]
    assert result.end is DiscoveryEnd.EXHAUSTED
    assert result.stats.probes_used == 30
    assert result.stats.inspections_used == 0
    assert result.stats.probe_allowance_hit
    assert not result.stats.inspection_allowance_hit
    assert result.stats.dims_unavailable == 70
    assert result.stats.rejected == {Rejection.NOT_LANDSCAPE.value: 30}
    assert result.limits_reached
    assert budget.probes.used == 30
    assert budget.inspections.used == 0


def test_metadata_dimensions_still_qualify_after_the_probes_are_spent() -> None:
    probe = FakeProbe(DimensionSource.REMOTE_PROBE, default=PORTRAIT)
    source = ScriptedSource([*works(1001, 40, None), work(2001, WIDE), *works(3001, 5, STRICT)])
    result = select(source, probe=probe)
    assert ids(result) == ["aic:3001", "aic:3002"]
    assert result.end is DiscoveryEnd.SHORTLIST_FULL
    assert len(probe.calls) == 30
    assert result.stats.dims_unavailable == 10
    assert result.stats.fallback_offered == 1
    assert result.limits_reached


def test_local_inspections_use_their_own_allowance_of_300() -> None:
    budget = make_budget(candidate_limit=1000)
    probe = FakeProbe(DimensionSource.LOCAL_INSPECTION, default=PORTRAIT)
    result = select(works(1001, 400, None), budget=budget, probe=probe)
    assert len(probe.calls) == LOCAL_INSPECTION_ALLOWANCE == 300
    assert result.stats.inspections_used == 300
    assert result.stats.probes_used == 0
    assert result.stats.inspection_allowance_hit
    assert not result.stats.probe_allowance_hit
    assert result.stats.dims_unavailable == 100
    assert result.limits_reached
    assert budget.inspections.used == 300
    assert budget.probes.used == 0


def test_a_spent_probe_allowance_does_not_affect_inspections() -> None:
    budget = make_budget()
    budget.probes.take(REMOTE_PROBE_ALLOWANCE)
    probe = FakeProbe(DimensionSource.LOCAL_INSPECTION, default=STRICT)
    result = select(works(1001, 3, None), budget=budget, probe=probe)
    assert ids(result) == ["aic:1001", "aic:1002"]
    assert result.stats.inspections_used == 2
    assert not result.limits_reached


def test_a_remote_probe_gets_its_own_request_deadline() -> None:
    budget = make_budget()
    probe = FakeProbe(DimensionSource.REMOTE_PROBE, default=STRICT)
    select([work(1001, None)], budget=budget, probe=probe)
    (deadline,) = probe.deadlines
    assert deadline.name == "probe"
    assert deadline.expires_at == budget.clock.monotonic() + PROBE_REQUEST_S


def test_a_remote_probe_deadline_is_clamped_to_discovery() -> None:
    budget = make_budget()
    budget.clock.advance(DISCOVERY_S - 2.0)
    probe = FakeProbe(DimensionSource.REMOTE_PROBE, default=STRICT)
    select([work(1001, None)], budget=budget, probe=probe)
    (deadline,) = probe.deadlines
    assert deadline.expires_at == budget.deadline.expires_at


def test_a_local_inspection_uses_the_discovery_deadline() -> None:
    budget = make_budget()
    probe = FakeProbe(DimensionSource.LOCAL_INSPECTION, default=STRICT)
    select([work(1001, None)], budget=budget, probe=probe)
    assert probe.deadlines == [budget.deadline]
    assert probe.deadlines[0] is budget.deadline


def test_a_probe_that_cannot_measure_counts_as_unavailable() -> None:
    probe = FakeProbe(DimensionSource.REMOTE_PROBE, default=None)
    result = select([work(1001, None), work(1002, STRICT)], probe=probe)
    assert ids(result) == ["aic:1002"]
    assert result.stats.dims_unavailable == 1
    assert result.stats.probes_used == 1
    assert not result.transport_failure


def test_a_probe_404_or_410_moves_on() -> None:
    error = SourceError(SourceErrorKind.NOT_FOUND, "404")
    probe = FakeProbe(DimensionSource.REMOTE_PROBE, default=STRICT, outcomes={"aic:1001": error})
    result = select(works(1001, 3, None), probe=probe)
    assert ids(result) == ["aic:1002", "aic:1003"]
    assert result.end is DiscoveryEnd.SHORTLIST_FULL
    assert result.stats.probe_not_found == 1
    assert result.stats.probe_transport_failures == 0
    assert result.stats.dims_unavailable == 0
    assert result.provider_error is None
    assert not result.transport_failure


@pytest.mark.parametrize("kind", TRANSPORT_KINDS)
def test_a_probe_transport_failure_moves_on(kind: SourceErrorKind) -> None:
    error = SourceError(kind)
    probe = FakeProbe(DimensionSource.REMOTE_PROBE, default=STRICT, outcomes={"aic:1001": error})
    result = select(works(1001, 3, None), probe=probe)
    assert ids(result) == ["aic:1002", "aic:1003"]
    assert result.end is DiscoveryEnd.SHORTLIST_FULL
    assert result.stats.probe_transport_failures == 1
    assert result.stats.probe_not_found == 0
    assert result.provider_error is None
    assert result.transport_failure


def test_a_403_429_stop_during_a_probe_ends_discovery_without_fallbacks() -> None:
    error = SourceError(SourceErrorKind.STOPPED, "429")
    probe = FakeProbe(DimensionSource.REMOTE_PROBE, default=STRICT, outcomes={"aic:1003": error})
    source = ScriptedSource(
        [work(1001, STRICT), work(1002, WIDE), work(1003, None), work(1004, STRICT)]
    )
    result = select(source, probe=probe)
    assert ids(result) == ["aic:1001"]
    assert bases(result) == [ChoiceBasis.STRICT]
    assert result.end is DiscoveryEnd.PROVIDER_STOPPED
    assert result.provider_error is error
    assert result.provider_stopped
    assert result.transport_failure
    assert result.stats.fallback_offered == 1
    assert source.pulls == 3


class ExpiringProbe(FakeProbe):
    """A probe whose request is cut off because discovery itself expires."""

    def __init__(self, clock: FakeClock) -> None:
        super().__init__(DimensionSource.REMOTE_PROBE, default=STRICT)
        self._clock = clock

    def measure(self, candidate: Candidate, deadline: Deadline) -> Size | None:
        self.calls.append(candidate.qualified_id)
        self._clock.advance(DISCOVERY_S)
        raise DeadlineExceeded("probe")


def test_a_probe_cut_off_by_the_discovery_deadline_ends_discovery() -> None:
    budget = make_budget()
    probe = ExpiringProbe(budget.clock)
    source = ScriptedSource([work(1001, WIDE), work(1002, None), work(1003, STRICT)])
    result = select(source, budget=budget, probe=probe)
    assert ids(result) == ["aic:1001"]
    assert bases(result) == [ChoiceBasis.FALLBACK]
    assert result.end is DiscoveryEnd.DEADLINE
    assert result.provider_error is None
    assert result.limits_reached
    assert not result.transport_failure
    assert source.pulls == 2


def test_a_probe_exceeding_its_own_limit_is_a_transport_failure() -> None:
    """§4.2, §7.4: the probe's own 5 s limit fails that probe only."""
    error = DeadlineExceeded("probe")
    probe = FakeProbe(DimensionSource.REMOTE_PROBE, default=STRICT, outcomes={"aic:1002": error})
    source = ScriptedSource([work(1001, WIDE), work(1002, None), work(1003, STRICT)])
    result = select(source, probe=probe)
    assert ids(result) == ["aic:1003", "aic:1001"]
    assert bases(result) == [ChoiceBasis.STRICT, ChoiceBasis.FALLBACK]
    assert result.stats.probe_transport_failures == 1
    assert result.transport_failure
    assert not result.limits_reached


def test_a_repeated_work_never_takes_a_second_slot() -> None:
    budget = make_budget()
    source = ScriptedSource([work(1001, STRICT), work(1001, STRICT), work(1002, STRICT)])
    result = select(source, budget=budget)
    assert ids(result) == ["aic:1001", "aic:1002"]
    assert result.stats.duplicates == 1
    assert result.stats.evaluated == 2
    assert budget.candidates.used == 2


def test_a_repeated_excluded_work_counts_as_a_duplicate() -> None:
    exclusions = ExclusionSet(history=frozenset({"aic:1001"}))
    result = select([work(1001, STRICT), work(1001, STRICT)], exclusions=exclusions)
    assert result.stats.excluded == 1
    assert result.stats.duplicates == 1
    assert result.stats.evaluated == 0


@pytest.mark.parametrize("error", [Cancelled(), ValueError("probe bug")])
def test_other_probe_exceptions_propagate(error: Exception) -> None:
    probe = FakeProbe(DimensionSource.REMOTE_PROBE, outcomes={"aic:1001": error})
    with pytest.raises(type(error)) as raised:
        select([work(1001, None)], probe=probe)
    assert raised.value is error


# --- Fallbacks (D-117) ------------------------------------------------------


def test_restrictive_filters_fall_back_to_the_closest_landscape_works() -> None:  # C6
    random = CountingRandom()
    source = [work(1001, WIDER), work(1002, WIDE), work(1003, PORTRAIT), work(1004, NEARLY)]
    result = select(source, random=random)
    assert ids(result) == ["aic:1004", "aic:1002"]
    assert bases(result) == [ChoiceBasis.FALLBACK, ChoiceBasis.FALLBACK]
    assert [entry.size for entry in result.entries] == [NEARLY, WIDE]
    assert not any(entry.require_near_16_9 for entry in result.entries)
    assert result.end is DiscoveryEnd.EXHAUSTED
    assert result.stats.fallback_offered == 3
    assert result.stats.rejected == {Rejection.NOT_LANDSCAPE.value: 1}
    assert random.draws == 3


def test_a_strict_match_comes_before_fallbacks() -> None:
    result = select([work(1001, WIDE), work(1002, STRICT)])
    assert ids(result) == ["aic:1002", "aic:1001"]
    assert bases(result) == [ChoiceBasis.STRICT, ChoiceBasis.FALLBACK]
    assert [entry.require_near_16_9 for entry in result.entries] == [True, False]


def test_fallbacks_are_unused_when_strict_matches_fill_the_shortlist() -> None:
    source = ScriptedSource(
        [work(1001, NEARLY), work(1002, STRICT), work(1003, STRICT_EDGE), work(1004, STRICT)]
    )
    result = select(source)
    assert ids(result) == ["aic:1002", "aic:1003"]
    assert bases(result) == [ChoiceBasis.STRICT, ChoiceBasis.STRICT]
    assert result.end is DiscoveryEnd.SHORTLIST_FULL
    assert result.stats.fallback_offered == 1
    assert source.pulls == 3


def test_the_shortlist_never_exceeds_its_size() -> None:
    random = CountingRandom(values=[0.5, 0.5, 0.5, 0.1])
    source = [
        work(1001, STRICT),
        work(1002, WIDE),
        work(1003, WIDER),
        work(1004, NEARLY),
        work(1005, WIDE),
    ]
    result = select(source, random=random, shortlist_size=3)
    assert ids(result) == ["aic:1001", "aic:1004", "aic:1005"]
    assert bases(result) == [ChoiceBasis.STRICT, ChoiceBasis.FALLBACK, ChoiceBasis.FALLBACK]
    assert result.stats.fallback_offered == 4


def test_many_fallbacks_keep_only_the_best() -> None:
    sizes = [Size(3000, height) for height in range(1000, 1500, 25)]  # 3:1 up to about 2:1
    source = [work(1001 + index, size) for index, size in enumerate(sizes)]
    result = select(source)
    assert [entry.size for entry in result.entries] == [Size(3000, 1475), Size(3000, 1450)]
    assert result.stats.fallback_offered == len(sizes)


def test_exact_ties_are_broken_by_the_random_tiebreak() -> None:
    random = CountingRandom(values=[0.9, 0.1, 0.5])
    result = select(works(1001, 3, WIDE), random=random)
    assert ids(result) == ["aic:1002", "aic:1003"]


def test_a_complete_tie_goes_to_the_earlier_offer() -> None:
    random = CountingRandom(values=[0.5, 0.5, 0.5])
    result = select(works(1001, 3, WIDE), random=random)
    assert ids(result) == ["aic:1001", "aic:1002"]


def test_the_tiebreak_is_drawn_once_per_offered_candidate() -> None:
    random = CountingRandom(seed=7)
    source = [*works(1001, 5, WIDE), work(1006, PORTRAIT), work(1007, STRICT)]
    result = select(source, random=random)
    assert result.stats.fallback_offered == 5
    assert random.draws == 5


def test_tiebreaks_are_reproducible_under_a_seed() -> None:
    orderings: set[tuple[str, ...]] = set()
    for seed in range(20):
        first = select(works(1001, 4, WIDE), random=SeededRandomSource(seed))
        second = select(works(1001, 4, WIDE), random=SeededRandomSource(seed))
        assert ids(first) == ids(second)
        orderings.add(tuple(ids(first)))
    assert len(orderings) > 1


def test_no_fallback_in_cover_mode() -> None:
    random = CountingRandom()
    source = [work(1001, WIDE), work(1002, WIDER), work(1003, NEARLY)]
    result = select(source, policy=STRICT_COVER, random=random)
    assert result.entries == ()
    assert result.end is DiscoveryEnd.EXHAUSTED
    assert result.stats.rejected == {Rejection.NOT_NEAR_16_9.value: 3}
    assert result.stats.fallback_offered == 0
    assert random.draws == 0


def test_cover_mode_still_takes_strict_matches() -> None:
    result = select([work(1001, WIDE), work(1002, STRICT)], policy=STRICT_COVER)
    assert ids(result) == ["aic:1002"]
    assert bases(result) == [ChoiceBasis.STRICT]


def test_no_fallback_when_landscape_only_is_off() -> None:
    source = [work(1001, WIDE), work(1002, PORTRAIT), work(1003, SQUARE), work(1004, STRICT)]
    result = select(source, policy=STRICT_ANY_SHAPE)
    assert ids(result) == ["aic:1004"]
    assert bases(result) == [ChoiceBasis.STRICT]
    assert result.stats.rejected == {Rejection.NOT_NEAR_16_9.value: 3}
    assert result.stats.fallback_offered == 0


# --- Provider errors and deadlines ------------------------------------------


@pytest.mark.parametrize("kind", [*TRANSPORT_KINDS, SourceErrorKind.NOT_FOUND])
def test_a_provider_error_keeps_the_shortlist_and_fills_fallbacks(kind: SourceErrorKind) -> None:
    error = SourceError(kind, "mid-discovery")
    source = ScriptedSource([work(1001, STRICT), work(1002, WIDE), error, work(1003, STRICT)])
    result = select(source)
    assert ids(result) == ["aic:1001", "aic:1002"]
    assert bases(result) == [ChoiceBasis.STRICT, ChoiceBasis.FALLBACK]
    assert result.end is DiscoveryEnd.PROVIDER_ERROR
    assert result.provider_error is error
    assert result.transport_failure is (kind is not SourceErrorKind.NOT_FOUND)
    assert not result.provider_stopped
    assert not result.limits_reached
    assert result.stats.candidates_seen == 2
    assert source.pulls == 3


def test_a_provider_stop_keeps_strict_entries_but_no_fallbacks() -> None:
    error = SourceError(SourceErrorKind.STOPPED, "403")
    source = ScriptedSource([work(1001, STRICT), work(1002, WIDE), error])
    result = select(source)
    assert ids(result) == ["aic:1001"]
    assert result.end is DiscoveryEnd.PROVIDER_STOPPED
    assert result.provider_error is error
    assert result.provider_stopped
    assert result.transport_failure
    assert not result.limits_reached


def test_a_request_cut_off_by_the_deadline_ends_discovery() -> None:
    source = ScriptedSource([work(1001, WIDE), DeadlineExceeded("discovery"), work(1002, STRICT)])
    result = select(source)
    assert ids(result) == ["aic:1001"]
    assert bases(result) == [ChoiceBasis.FALLBACK]
    assert result.end is DiscoveryEnd.DEADLINE
    assert result.provider_error is None
    assert result.limits_reached
    assert not result.transport_failure


def test_the_deadline_is_checked_before_every_pull() -> None:
    budget = make_budget()
    source = ScriptedSource(works(1001, 10, PORTRAIT), clock=budget.clock, step_s=10.0)
    result = select(source, budget=budget)
    assert result.end is DiscoveryEnd.DEADLINE
    assert source.pulls == 3
    assert result.stats.candidates_seen == 3
    assert budget.clock.elapsed == DISCOVERY_S


def test_an_expired_deadline_pulls_nothing() -> None:
    budget = make_budget()
    budget.clock.advance(DISCOVERY_S)
    source = ScriptedSource(works(1001, 3, STRICT))
    result = select(source, budget=budget)
    assert result.entries == ()
    assert result.end is DiscoveryEnd.DEADLINE
    assert result.stats == SelectionStats()
    assert source.pulls == 0


def test_an_endless_stream_of_excluded_works_ends_at_the_deadline() -> None:  # C11
    budget = make_budget()

    def endless() -> Iterator[Candidate]:
        for native_id in itertools.count(1001):
            budget.clock.advance(0.25)
            yield work(native_id, STRICT)

    exclusions = ExclusionSet(history=frozenset(f"aic:{n}" for n in range(1001, 1200)))
    result = select(endless(), budget=budget, exclusions=exclusions)
    assert result.end is DiscoveryEnd.DEADLINE
    assert result.entries == ()
    assert result.stats.excluded == 120
    assert result.stats.evaluated == 0
    assert budget.clock.elapsed == DISCOVERY_S


def test_the_full_shortlist_wins_over_an_expired_deadline() -> None:
    budget = make_budget()
    source = ScriptedSource(works(1001, 3, STRICT), clock=budget.clock, step_s=DISCOVERY_S)
    result = select(source, budget=budget, shortlist_size=1)
    assert result.end is DiscoveryEnd.SHORTLIST_FULL
    assert not result.limits_reached


@pytest.mark.parametrize("error", [Cancelled(), RuntimeError("provider bug")])
def test_other_provider_exceptions_propagate(error: Exception) -> None:
    source = ScriptedSource([work(1001, STRICT), error])
    with pytest.raises(type(error)) as raised:
        select(source)
    assert raised.value is error


# --- A mixed pass -----------------------------------------------------------


def test_every_statistic_of_a_mixed_pass() -> None:
    budget = make_budget(candidate_limit=12)
    not_found = SourceError(SourceErrorKind.NOT_FOUND)
    timeout = SourceError(SourceErrorKind.TIMEOUT)
    probe = FakeProbe(
        DimensionSource.REMOTE_PROBE,
        default=None,
        outcomes={"aic:1006": not_found, "aic:1007": timeout, "aic:1008": WIDER},
    )
    source = ScriptedSource(
        [
            work(1001, STRICT),  # excluded
            work(1002, STRICT, rights=RightsBasis.USER_SUPPLIED),
            work(1003, TINY),
            work(1004, PORTRAIT),
            work(1005, None),  # the probe cannot measure it
            work(1006, None),  # 404
            work(1007, None),  # timeout
            work(1008, None),  # probed: a fallback
            work(1009, WIDE),
            work(1010, SQUARE),
            work(1011, STRICT_EDGE),
            work(1012, NEARLY),
            work(1013, WIDE),
            work(1014, STRICT),  # the allowance of 12 ends discovery here
        ]
    )
    exclusions = ExclusionSet(history=frozenset({"aic:1001"}))
    result = select(source, budget=budget, exclusions=exclusions, probe=probe)
    assert probe.calls == ["aic:1005", "aic:1006", "aic:1007", "aic:1008"]
    assert result.end is DiscoveryEnd.CANDIDATE_ALLOWANCE
    assert ids(result) == ["aic:1011", "aic:1012"]
    assert bases(result) == [ChoiceBasis.STRICT, ChoiceBasis.FALLBACK]
    assert result.stats == SelectionStats(
        candidates_seen=14,
        excluded=1,
        evaluated=12,
        rights_rejected=1,
        dims_unavailable=1,
        rejected={Rejection.TOO_SMALL.value: 1, Rejection.NOT_LANDSCAPE.value: 2},
        fallback_offered=4,
        probes_used=4,
        probe_not_found=1,
        probe_transport_failures=1,
    )
    assert result.limits_reached
    assert result.transport_failure


# --- The result and policy types --------------------------------------------


@pytest.mark.parametrize(
    ("end", "limits"),
    [
        (DiscoveryEnd.SHORTLIST_FULL, False),
        (DiscoveryEnd.EXHAUSTED, False),
        (DiscoveryEnd.DEADLINE, True),
        (DiscoveryEnd.CANDIDATE_ALLOWANCE, True),
        (DiscoveryEnd.PROVIDER_ERROR, False),
        (DiscoveryEnd.PROVIDER_STOPPED, False),
    ],
)
def test_limits_reached_by_end(end: DiscoveryEnd, limits: bool) -> None:
    result = SelectionResult(entries=(), end=end, stats=SelectionStats())
    assert result.limits_reached is limits
    assert result.provider_stopped is (end is DiscoveryEnd.PROVIDER_STOPPED)


@pytest.mark.parametrize(
    "stats",
    [SelectionStats(probe_allowance_hit=True), SelectionStats(inspection_allowance_hit=True)],
)
def test_limits_reached_by_a_spent_dimension_allowance(stats: SelectionStats) -> None:
    result = SelectionResult(entries=(), end=DiscoveryEnd.EXHAUSTED, stats=stats)
    assert result.limits_reached


@pytest.mark.parametrize(
    ("error", "probe_failures", "expected"),
    [
        (None, 0, False),
        (None, 1, True),
        (SourceError(SourceErrorKind.NOT_FOUND), 0, False),
        (SourceError(SourceErrorKind.NOT_FOUND), 2, True),
        (SourceError(SourceErrorKind.HTTP_ERROR), 0, True),
        (SourceError(SourceErrorKind.STOPPED), 0, True),
    ],
)
def test_transport_failure(error: SourceError | None, probe_failures: int, expected: bool) -> None:
    result = SelectionResult(
        entries=(),
        end=DiscoveryEnd.PROVIDER_ERROR,
        stats=SelectionStats(probe_transport_failures=probe_failures),
        provider_error=error,
    )
    assert result.transport_failure is expected


@pytest.mark.parametrize("landscape_only", [True, False])
@pytest.mark.parametrize("strict", [True, False])
@pytest.mark.parametrize("fit_mode", list(FitMode))
def test_fallback_is_permitted_only_for_strict_landscape_contain(
    landscape_only: bool, strict: bool, fit_mode: FitMode
) -> None:
    policy = SelectionPolicy(
        landscape_only=landscape_only, strict_tv_format=strict, fit_mode=fit_mode
    )
    expected = landscape_only and strict and fit_mode is FitMode.CONTAIN
    assert policy.fallback_permitted is expected


@pytest.mark.parametrize(
    ("basis", "required"),
    [
        (ChoiceBasis.STRICT, True),
        (ChoiceBasis.FIRST_ELIGIBLE, False),
        (ChoiceBasis.FALLBACK, False),
    ],
)
def test_only_strict_entries_require_near_16_9(basis: ChoiceBasis, required: bool) -> None:
    assert ShortlistEntry(work(1001), STRICT, basis).require_near_16_9 is required


# --- Per-candidate decisions (§19) and local inspections (§9.3) --------------


def test_every_considered_candidate_gets_one_decision() -> None:
    decisions: list[tuple[str, str]] = []
    exclusions = ExclusionSet(history=frozenset({"aic:1002"}))
    probe = FakeProbe(
        DimensionSource.REMOTE_PROBE,
        outcomes={
            "aic:1006": None,
            "aic:1007": SourceError(SourceErrorKind.NOT_FOUND),
            "aic:1008": SourceError(SourceErrorKind.TRANSPORT),
        },
    )
    candidates = [
        work(1001, PORTRAIT),
        work(1002),
        work(1001, STRICT),
        work(1003, rights=RightsBasis.USER_SUPPLIED),
        work(1004, WIDE),
        work(1006, None),
        work(1007, None),
        work(1008, None),
        work(1005, STRICT),
    ]
    select(
        candidates,
        exclusions=exclusions,
        probe=probe,
        shortlist_size=1,
        on_decision=lambda c, d: decisions.append((c.qualified_id, d)),
    )
    assert decisions == [
        ("aic:1001", "rejected:not_landscape"),
        ("aic:1002", "excluded"),
        ("aic:1001", "duplicate"),
        ("aic:1003", "rights_rejected"),
        ("aic:1004", "fallback_offered"),
        ("aic:1006", "dims_unavailable"),
        ("aic:1007", "probe_not_found"),
        ("aic:1008", "probe_failed"),
        ("aic:1005", "shortlisted:strict"),
    ]


def test_decisions_for_relaxed_policy_and_allowance_hits() -> None:
    decisions: list[str] = []
    budget = make_budget()
    budget.probes = Allowance("probes", 0)
    probe = FakeProbe(DimensionSource.REMOTE_PROBE)
    select(
        [work(1, None), work(2, NEARLY)],
        budget=budget,
        policy=RELAXED,
        probe=probe,
        on_decision=lambda _c, d: decisions.append(d),
    )
    assert decisions == ["dims_unavailable:allowance", "shortlisted:first_eligible"]


def test_cover_rejects_a_non_16_9_work_without_fallback() -> None:
    decisions: list[str] = []
    select([work(1, WIDE)], policy=STRICT_COVER, on_decision=lambda _c, d: decisions.append(d))
    assert decisions == ["rejected:not_near_16_9"]


@pytest.mark.parametrize(
    "error",
    [SourceError(SourceErrorKind.UNEXPECTED_FORMAT), SourceError(SourceErrorKind.TRANSPORT)],
)
def test_a_failed_local_inspection_is_not_a_transport_failure(error: SourceError) -> None:
    probe = FakeProbe(DimensionSource.LOCAL_INSPECTION, outcomes={"aic:1": error})
    decisions: list[str] = []
    result = select([work(1, None)], probe=probe, on_decision=lambda _c, d: decisions.append(d))
    assert result.stats.inspection_failures == 1
    assert result.stats.probe_transport_failures == 0
    assert not result.transport_failure
    assert decisions == ["inspection_failed"]


def test_a_local_inspection_exceeding_its_own_time_is_an_inspection_failure() -> None:
    probe = FakeProbe(DimensionSource.LOCAL_INSPECTION, outcomes={"aic:1": DeadlineExceeded("x")})
    result = select([work(1, None)], probe=probe)
    assert result.stats.inspection_failures == 1
    assert not result.transport_failure
