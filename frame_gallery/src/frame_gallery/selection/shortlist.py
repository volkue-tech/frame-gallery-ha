"""The single-pass discovery and shortlist (§8.2, D-117).

One pass pulls candidates lazily and stops as soon as the shortlist is full,
the discovery deadline expires, the candidate allowance runs out, or the
provider ends discovery. Excluded works are skipped before the candidate
allowance is charged (D-137); rights (D-134), dimensions (§8.3), and shape
and quality (§8.1, D-116) are then checked in that order. With strict TV
format on, landscape works outside the near-16:9 band are ranked in a bounded
fallback structure that fills any empty slots after the pass (D-117).

The module performs no I/O: its only time source is the deadline, and its
only randomness the injected :class:`RandomSource`. The types below are the
stable contract used by the runner.
"""

from __future__ import annotations

import enum
import heapq
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field

from frame_gallery.budget.allowance import Allowance, AllowanceExhausted
from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.budget.limits import PROBE_REQUEST_S, SHORTLIST_SIZE
from frame_gallery.domain import CANVAS, FitMode, Size
from frame_gallery.providers.contract import (
    Candidate,
    DimensionProbe,
    DimensionSource,
    SourceError,
    SourceErrorKind,
)
from frame_gallery.providers.rights import RightsBasis
from frame_gallery.randomness import RandomSource
from frame_gallery.selection.exclusion import ExclusionSet
from frame_gallery.selection.geometry import (
    Rejection,
    check_rendition,
    is_near_16_9,
    log_distance_to_16_9,
)


class ChoiceBasis(enum.StrEnum):
    """Why a candidate was shortlisted; verified again on the real image."""

    STRICT = "strict"
    """Near-16:9 while strict TV format is on."""

    FIRST_ELIGIBLE = "first_eligible"
    """Eligible while strict TV format is off."""

    FALLBACK = "fallback"
    """A landscape work closest to 16:9, when no strict match was found."""


@dataclass(frozen=True, slots=True)
class SelectionPolicy:
    """The selection options of one run."""

    landscape_only: bool
    strict_tv_format: bool
    fit_mode: FitMode
    canvas: Size = CANVAS

    @property
    def fallback_permitted(self) -> bool:
        """Fallback only with strict format, landscape-only, and ``contain`` (D-117)."""
        return self.strict_tv_format and self.landscape_only and self.fit_mode is FitMode.CONTAIN


@dataclass(frozen=True, slots=True)
class ShortlistEntry:
    candidate: Candidate
    size: Size
    """The dimensions selection evaluated (metadata or probe)."""

    basis: ChoiceBasis

    @property
    def require_near_16_9(self) -> bool:
        return self.basis is ChoiceBasis.STRICT


class DiscoveryEnd(enum.StrEnum):
    """Why the discovery pass ended."""

    SHORTLIST_FULL = "shortlist_full"
    EXHAUSTED = "exhausted"
    """The provider had no more candidates."""

    DEADLINE = "deadline"
    """The discovery deadline expired (including a request cut off by it)."""

    CANDIDATE_ALLOWANCE = "candidate_allowance"
    METADATA_ALLOWANCE = "metadata_allowance"
    """The provider used up its metadata requests (§7.2, D-114)."""

    PROVIDER_ERROR = "provider_error"
    """A provider or transport error ended discovery (not a 403/429 stop)."""

    PROVIDER_STOPPED = "provider_stopped"
    """A 403/429 stop: no further requests to this provider in this run."""


@dataclass(frozen=True, slots=True)
class SelectionStats:
    candidates_seen: int = 0
    """Candidates the provider yielded."""

    excluded: int = 0
    """Skipped because they were in the exclusion set (not charged)."""

    evaluated: int = 0
    """Charged to the candidate allowance."""

    rights_rejected: int = 0
    dims_unavailable: int = 0
    rejected: dict[str, int] = field(default_factory=dict)
    """Counts per ``Rejection`` value."""

    fallback_offered: int = 0
    probes_used: int = 0
    inspections_used: int = 0
    probe_allowance_hit: bool = False
    inspection_allowance_hit: bool = False
    probe_not_found: int = 0
    probe_transport_failures: int = 0
    duplicates: int = 0
    """A qualified identifier seen again in the same pass (not charged)."""

    inspection_failures: int = 0
    """Local header inspections that failed; not transport failures (§9.3)."""


@dataclass(frozen=True, slots=True)
class SelectionResult:
    entries: tuple[ShortlistEntry, ...]
    end: DiscoveryEnd
    stats: SelectionStats
    provider_error: SourceError | None = None
    """The error that ended discovery, if any."""

    @property
    def provider_stopped(self) -> bool:
        return self.end is DiscoveryEnd.PROVIDER_STOPPED

    @property
    def limits_reached(self) -> bool:
        return (
            self.end
            in (
                DiscoveryEnd.DEADLINE,
                DiscoveryEnd.CANDIDATE_ALLOWANCE,
                DiscoveryEnd.METADATA_ALLOWANCE,
            )
            or self.stats.probe_allowance_hit
            or self.stats.inspection_allowance_hit
        )

    @property
    def transport_failure(self) -> bool:
        """Discovery or a probe failed at the transport level (§4.2 rule 1)."""
        error = self.provider_error
        return (
            error is not None and error.kind is not SourceErrorKind.NOT_FOUND
        ) or self.stats.probe_transport_failures > 0


DecisionSink = Callable[[Candidate, str], None]
"""Receives ``(candidate, decision)``, e.g. ``excluded`` or ``rejected:too_small``."""


def build_shortlist(
    candidates: Iterable[Candidate],
    *,
    exclusions: ExclusionSet,
    policy: SelectionPolicy,
    allowed_rights: frozenset[RightsBasis],
    deadline: Deadline,
    random: RandomSource,
    candidate_allowance: Allowance,
    probe_allowance: Allowance,
    inspection_allowance: Allowance,
    probe: DimensionProbe | None = None,
    shortlist_size: int = SHORTLIST_SIZE,
    on_decision: DecisionSink | None = None,
) -> SelectionResult:
    """Run one discovery pass and return at most ``shortlist_size`` entries.

    ``candidates`` is pulled one candidate at a time, and never again once
    the pass has ended. A provider error ends the pass but keeps the entries
    found so far; fallbacks then fill the empty slots, except after a 403/429
    stop (§8.2, D-115). Raises ``ValueError`` if ``shortlist_size`` is below 1.
    ``Cancelled`` and any unexpected error from the provider or the probe
    propagate unchanged. ``on_decision`` receives one decision per candidate
    considered (for DEBUG logging, §19); the module itself does no I/O.
    """
    if (
        isinstance(shortlist_size, bool)
        or not isinstance(shortlist_size, int)
        or shortlist_size < 1
    ):
        msg = f"shortlist_size must be a positive integer, got {shortlist_size!r}"
        raise ValueError(msg)
    discovery = _Discovery(
        exclusions=exclusions,
        policy=policy,
        allowed_rights=allowed_rights,
        deadline=deadline,
        random=random,
        candidate_allowance=candidate_allowance,
        probe_allowance=probe_allowance,
        inspection_allowance=inspection_allowance,
        probe=probe,
        shortlist_size=shortlist_size,
        on_decision=on_decision,
    )
    return discovery.run(candidates)


class _DiscoveryEnded(Exception):
    """Ends the pass from inside a step. Private control flow; never escapes."""

    def __init__(self, end: DiscoveryEnd, error: SourceError | None = None) -> None:
        super().__init__(end.value)
        self.end = end
        self.error = error


@dataclass(slots=True)
class _Tally:
    """The mutable counterpart of :class:`SelectionStats` during one pass."""

    candidates_seen: int = 0
    excluded: int = 0
    evaluated: int = 0
    rights_rejected: int = 0
    dims_unavailable: int = 0
    rejected: dict[str, int] = field(default_factory=dict)
    fallback_offered: int = 0
    probes_used: int = 0
    inspections_used: int = 0
    probe_allowance_hit: bool = False
    inspection_allowance_hit: bool = False
    probe_not_found: int = 0
    probe_transport_failures: int = 0
    duplicates: int = 0
    inspection_failures: int = 0

    def reject(self, rejection: Rejection) -> None:
        self.rejected[rejection.value] = self.rejected.get(rejection.value, 0) + 1

    def freeze(self) -> SelectionStats:
        return SelectionStats(
            candidates_seen=self.candidates_seen,
            excluded=self.excluded,
            evaluated=self.evaluated,
            rights_rejected=self.rights_rejected,
            dims_unavailable=self.dims_unavailable,
            rejected=dict(self.rejected),
            fallback_offered=self.fallback_offered,
            probes_used=self.probes_used,
            inspections_used=self.inspections_used,
            probe_allowance_hit=self.probe_allowance_hit,
            inspection_allowance_hit=self.inspection_allowance_hit,
            probe_not_found=self.probe_not_found,
            probe_transport_failures=self.probe_transport_failures,
            duplicates=self.duplicates,
            inspection_failures=self.inspection_failures,
        )


class _Fallbacks:
    """The ``capacity`` best fallback works: the §8.2 "top-2 heap" (D-117).

    The key is ``(log distance to 16:9, random tiebreak)``; smaller is better,
    and an exact tie on both goes to the earlier offer. The heap holds negated
    keys, so its root is the worst retained entry, the one a better offer
    displaces.
    """

    __slots__ = ("_capacity", "_heap", "_offers")

    def __init__(self, capacity: int) -> None:
        self._capacity = capacity
        self._heap: list[tuple[float, float, int, ShortlistEntry]] = []
        self._offers = 0

    def offer(self, entry: ShortlistEntry, tiebreak: float) -> None:
        item = (-log_distance_to_16_9(entry.size), -tiebreak, -self._offers, entry)
        self._offers += 1
        if len(self._heap) < self._capacity:
            heapq.heappush(self._heap, item)
        else:
            heapq.heappushpop(self._heap, item)

    def best(self, count: int) -> list[ShortlistEntry]:
        """Up to ``count`` retained entries, best first."""
        ranked = sorted(self._heap, reverse=True)
        return [item[-1] for item in ranked[:count]]


class _Discovery:
    """The state of one discovery pass (§8.2)."""

    def __init__(
        self,
        *,
        exclusions: ExclusionSet,
        policy: SelectionPolicy,
        allowed_rights: frozenset[RightsBasis],
        deadline: Deadline,
        random: RandomSource,
        candidate_allowance: Allowance,
        probe_allowance: Allowance,
        inspection_allowance: Allowance,
        probe: DimensionProbe | None,
        shortlist_size: int,
        on_decision: DecisionSink | None,
    ) -> None:
        self._on_decision = on_decision
        self._exclusions = exclusions
        self._policy = policy
        self._allowed_rights = allowed_rights
        self._deadline = deadline
        self._random = random
        self._candidate_allowance = candidate_allowance
        self._probe_allowance = probe_allowance
        self._inspection_allowance = inspection_allowance
        self._probe = probe
        self._shortlist_size = shortlist_size
        self._entries: list[ShortlistEntry] = []
        self._fallbacks = _Fallbacks(shortlist_size)
        self._tally = _Tally()
        self._seen: set[str] = set()

    def run(self, candidates: Iterable[Candidate]) -> SelectionResult:
        end, error = self._scan(iter(candidates))
        if self._policy.fallback_permitted and end is not DiscoveryEnd.PROVIDER_STOPPED:
            free = self._shortlist_size - len(self._entries)
            self._entries.extend(self._fallbacks.best(free))
        return SelectionResult(tuple(self._entries), end, self._tally.freeze(), error)

    def _scan(self, candidates: Iterator[Candidate]) -> tuple[DiscoveryEnd, SourceError | None]:
        try:
            while len(self._entries) < self._shortlist_size:
                if self._deadline.expired():
                    return DiscoveryEnd.DEADLINE, None
                self._consider(self._pull(candidates))
        except _DiscoveryEnded as ended:
            return ended.end, ended.error
        return DiscoveryEnd.SHORTLIST_FULL, None

    def _pull(self, candidates: Iterator[Candidate]) -> Candidate:
        try:
            candidate = next(candidates)
        except StopIteration:
            raise _DiscoveryEnded(DiscoveryEnd.EXHAUSTED) from None
        except SourceError as error:
            end = (
                DiscoveryEnd.PROVIDER_STOPPED
                if error.kind is SourceErrorKind.STOPPED
                else DiscoveryEnd.PROVIDER_ERROR
            )
            raise _DiscoveryEnded(end, error) from None
        except DeadlineExceeded:
            raise _DiscoveryEnded(DiscoveryEnd.DEADLINE) from None
        except AllowanceExhausted:
            # The provider's metadata allowance, not a failure: a search limit.
            raise _DiscoveryEnded(DiscoveryEnd.METADATA_ALLOWANCE) from None
        self._tally.candidates_seen += 1
        return candidate

    def _consider(self, candidate: Candidate) -> None:
        tally = self._tally
        qualified_id = candidate.qualified_id
        if qualified_id in self._seen:
            # A provider may repeat a work (overlapping pages); it never takes a
            # second slot and is never charged twice.
            tally.duplicates += 1
            self._decide(candidate, "duplicate")
            return
        self._seen.add(qualified_id)
        if qualified_id in self._exclusions:
            tally.excluded += 1
            self._decide(candidate, "excluded")
            return
        if not self._candidate_allowance.try_take():
            raise _DiscoveryEnded(DiscoveryEnd.CANDIDATE_ALLOWANCE)
        tally.evaluated += 1
        if candidate.rights_basis not in self._allowed_rights:
            tally.rights_rejected += 1
            self._decide(candidate, "rights_rejected")
            return
        size = candidate.dims if candidate.dims is not None else self._measure(candidate)
        if size is not None:
            self._rank(candidate, size)

    def _decide(self, candidate: Candidate, decision: str) -> None:
        """Report one per-candidate decision (DEBUG detail, §19)."""
        if self._on_decision is not None:
            self._on_decision(candidate, decision)

    def _measure(self, candidate: Candidate) -> Size | None:
        """The probed dimensions, charged to the probe's own allowance (§8.3).

        ``None`` skips the candidate; the reason has already been counted.
        """
        tally = self._tally
        probe = self._probe
        if probe is None:
            tally.dims_unavailable += 1
            self._decide(candidate, "dims_unavailable")
            return None
        remote = probe.source is DimensionSource.REMOTE_PROBE
        allowance = self._probe_allowance if remote else self._inspection_allowance
        if not allowance.try_take():
            if remote:
                tally.probe_allowance_hit = True
            else:
                tally.inspection_allowance_hit = True
            tally.dims_unavailable += 1
            self._decide(candidate, "dims_unavailable:allowance")
            return None
        if remote:
            tally.probes_used += 1
            deadline = self._deadline.child(PROBE_REQUEST_S, "probe")
        else:
            tally.inspections_used += 1
            deadline = self._deadline
        return self._call_probe(probe, candidate, deadline)

    def _call_probe(
        self, probe: DimensionProbe, candidate: Candidate, deadline: Deadline
    ) -> Size | None:
        tally = self._tally
        try:
            size = probe.measure(candidate, deadline)
        except SourceError as error:
            if error.kind is SourceErrorKind.STOPPED:
                raise _DiscoveryEnded(DiscoveryEnd.PROVIDER_STOPPED, error) from None
            if error.kind is SourceErrorKind.NOT_FOUND:
                tally.probe_not_found += 1
                self._decide(candidate, "probe_not_found")
            else:
                self._probe_failed(probe, candidate)
            return None
        except DeadlineExceeded:
            if self._deadline.expired():
                raise _DiscoveryEnded(DiscoveryEnd.DEADLINE) from None
            # The probe's own time limit, not discovery's: a failed probe, and
            # selection moves on to the next candidate (§4.2, §7.4).
            self._probe_failed(probe, candidate)
            return None
        if size is None:
            tally.dims_unavailable += 1
            self._decide(candidate, "dims_unavailable")
        return size

    def _probe_failed(self, probe: DimensionProbe, candidate: Candidate) -> None:
        """A remote probe failure is a transport failure (§4.2 rule 1); a local
        inspection failure is not, and only feeds the aggregated warning (§9.3)."""
        if probe.source is DimensionSource.REMOTE_PROBE:
            self._tally.probe_transport_failures += 1
            self._decide(candidate, "probe_failed")
        else:
            self._tally.inspection_failures += 1
            self._decide(candidate, "inspection_failed")

    def _rank(self, candidate: Candidate, size: Size) -> None:
        policy = self._policy
        rejection = check_rendition(
            size,
            fit_mode=policy.fit_mode,
            landscape_only=policy.landscape_only,
            require_near_16_9=False,
            canvas=policy.canvas,
        )
        if rejection is None and policy.strict_tv_format and not is_near_16_9(size):
            if policy.fallback_permitted:
                entry = ShortlistEntry(candidate, size, ChoiceBasis.FALLBACK)
                self._fallbacks.offer(entry, self._random.random())
                self._tally.fallback_offered += 1
                self._decide(candidate, "fallback_offered")
                return
            rejection = Rejection.NOT_NEAR_16_9
        if rejection is not None:
            self._tally.reject(rejection)
            self._decide(candidate, f"rejected:{rejection.value}")
            return
        basis = ChoiceBasis.STRICT if policy.strict_tv_format else ChoiceBasis.FIRST_ELIGIBLE
        self._entries.append(ShortlistEntry(candidate, size, basis))
        self._decide(candidate, f"shortlisted:{basis.value}")
