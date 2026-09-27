"""The shared provider contract suite (§9.1, §20.1, D-134, D-141).

Every adapter runs against its own synthesized fixture and must:

- report its source and key consistently;
- agree with ``CAPABILITY_MATRIX``: a supported filter changes what it asks
  for, and an unsupported one changes nothing;
- offer only rights bases that ``ALLOWED_RIGHTS`` allows for its source;
- be lazy: no request and no scan before the first ``next()``;
- send every request through the gateway, to its policy hosts only, and
  hand out renditions only on those hosts;
- report a 404 or 410 from a discovery endpoint as ``HTTP_ERROR``, and from a
  rendition as ``NOT_FOUND``;
- (local media) return ``None`` from an inspection of an unreadable file.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from frame_gallery.app.fetching import SourceFetcher
from frame_gallery.budget.allowance import Allowance
from frame_gallery.budget.deadline import Deadline
from frame_gallery.config.capabilities import CAPABILITY_MATRIX
from frame_gallery.config.filters import EffectiveFilters, FilterDimension, FilterSet
from frame_gallery.domain import SourceKey
from frame_gallery.isolation.in_process import InProcessExecutor, default_tasks
from frame_gallery.net.gateway import Gateway
from frame_gallery.net.policy import HostPolicy, validate_url
from frame_gallery.providers.aic import AicProvider, aic_policy
from frame_gallery.providers.cache import MemoryMetadataCache
from frame_gallery.providers.cma import CmaProvider, cma_policy
from frame_gallery.providers.contract import (
    Candidate,
    DiscoveryContext,
    ImageRefKind,
    Provider,
    SourceError,
    SourceErrorKind,
)
from frame_gallery.providers.local_media import LocalInspectionProbe, LocalMediaProvider
from frame_gallery.providers.rights import ALLOWED_RIGHTS
from frame_gallery.randomness import SeededRandomSource
from tests.support.clock import FakeClock
from tests.support.images import marked, save_jpeg
from tests.support.museums import AicMuseum, CmaMuseum, ParsedRequest, aic_record, cma_record
from tests.support.net import (
    TEST_IDENTITY,
    FakeResolver,
    FakeTransport,
    image_response,
    status_response,
)

# A valid key for every dimension; the capability matrix decides which apply.
FILTER_KEYS = {
    FilterDimension.DEPARTMENT: "cma_prints",
    FilterDimension.STYLE: "style_any_documented_one",
    FilterDimension.PERIOD: "period_1800_1899",
    FilterDimension.COLOR: "color_any_documented_one",
}


def _filters(source: SourceKey, dimension: FilterDimension | None = None) -> EffectiveFilters:
    values = {dimension: FILTER_KEYS[dimension]} if dimension is not None else {}
    return EffectiveFilters(
        source=source,
        department=values.get(FilterDimension.DEPARTMENT),
        style=values.get(FilterDimension.STYLE),
        period=values.get(FilterDimension.PERIOD),
        color=values.get(FilterDimension.COLOR),
        ignored=(),
        requested=FilterSet(source=source),
    )


@dataclass
class Subject:
    """One adapter over its fixture, and a view of what it asked for."""

    source: SourceKey
    provider: Provider
    clock: FakeClock
    asked: Callable[[], list[str]]
    """Requests sent (remote), or files visited (local), so far."""

    policy: HostPolicy | None = None
    transport: FakeTransport | None = None
    fetcher: SourceFetcher | None = None
    extras: dict[str, object] = field(default_factory=dict)

    def context(self) -> DiscoveryContext:
        return DiscoveryContext(Deadline.after(self.clock, 300, "discovery"), SeededRandomSource(4))

    def run(self, dimension: FilterDimension | None = None, limit: int = 50) -> list[Candidate]:
        found: list[Candidate] = []
        for candidate in self.provider.iter_candidates(
            _filters(self.source, dimension), self.context()
        ):
            found.append(candidate)
            if len(found) >= limit:
                break
        return found


def _remote(source: SourceKey, museum: AicMuseum | CmaMuseum) -> Subject:
    clock = FakeClock()
    transport = FakeTransport(clock=clock, handler=museum)
    gateway = Gateway(
        resolver=FakeResolver(),
        transport=transport,
        clock=clock,
        random=SeededRandomSource(1),
        identity=TEST_IDENTITY,
    )
    policy = (
        aic_policy(TEST_IDENTITY) if source is SourceKey.ART_INSTITUTE_CHICAGO else cma_policy()
    )
    channel = gateway.channel(policy, metadata_allowance=Allowance("metadata_requests", 15))
    cache = MemoryMetadataCache(clock)
    provider: Provider
    if source is SourceKey.ART_INSTITUTE_CHICAGO:
        provider = AicProvider(channel, cache)
    else:
        provider = CmaProvider(channel, cache)
    return Subject(
        source=source,
        provider=provider,
        clock=clock,
        asked=lambda: [f"{call.request.host}{call.request.target}" for call in transport.calls],
        policy=policy,
        transport=transport,
        fetcher=SourceFetcher(channels=[channel]),
        extras={"museum": museum},
    )


def _aic() -> Subject:
    museum = AicMuseum()
    museum.records = [aic_record(n, date_start=1700 + 5 * n) for n in range(1, 41)]
    museum.sizes = {str(r["image_id"]): (3840, 2160) for r in museum.records if isinstance(r, dict)}
    return _remote(SourceKey.ART_INSTITUTE_CHICAGO, museum)


def _cma() -> Subject:
    museum = CmaMuseum()
    museum.records = [
        cma_record(n, earliest=1700 + 5 * n, department="Prints" if n % 2 else "Drawings")
        for n in range(1, 41)
    ]
    return _remote(SourceKey.CLEVELAND_MUSEUM_OF_ART, museum)


def _local(tmp_path: Path) -> Subject:
    root = tmp_path / "library"
    root.mkdir(parents=True)
    for n in range(6):
        save_jpeg(marked((64 + n, 36)), root / f"work{n}.jpg")
    provider = LocalMediaProvider(root=root, preview_dir=tmp_path / "preview")
    clock = FakeClock()
    return Subject(
        source=SourceKey.LOCAL_MEDIA,
        provider=provider,
        clock=clock,
        asked=lambda: sorted(provider._files),
        fetcher=SourceFetcher(local=provider),
        extras={"root": root},
    )


FACTORIES: dict[str, Callable[[Path], Subject]] = {
    "aic": lambda tmp_path: _aic(),
    "cma": lambda tmp_path: _cma(),
    "local": _local,
}


@pytest.fixture(params=list(FACTORIES))
def subject(request: pytest.FixtureRequest, tmp_path: Path) -> Subject:
    return FACTORIES[request.param](tmp_path)


def test_identity(subject: Subject) -> None:
    capabilities = subject.provider.capabilities()
    assert capabilities.source is subject.source
    assert capabilities.provider_key == subject.provider.key == subject.source.provider_key
    found = subject.run()
    assert found
    assert {candidate.provider_key for candidate in found} == {subject.source.provider_key}
    assert all(c.qualified_id.startswith(f"{subject.source.provider_key}:") for c in found)


def test_rights_bases_are_allowed(subject: Subject) -> None:
    allowed = ALLOWED_RIGHTS[subject.source]
    found = subject.run()
    assert found
    assert {candidate.rights_basis for candidate in found} <= allowed
    assert len({candidate.rights_field for candidate in found}) == 1


def test_candidates_are_lazy(subject: Subject) -> None:
    iterator: Iterator[Candidate] = subject.provider.iter_candidates(
        _filters(subject.source), subject.context()
    )
    assert subject.asked() == []
    next(iterator)
    assert subject.asked() != []


@pytest.mark.parametrize("name", list(FACTORIES))
@pytest.mark.parametrize("dimension", list(FilterDimension))
def test_the_adapter_agrees_with_the_capability_matrix(
    name: str, dimension: FilterDimension, tmp_path: Path
) -> None:
    base = FACTORIES[name](tmp_path / "base")
    other = FACTORIES[name](tmp_path / "filtered")
    unfiltered = base.run(limit=100)
    filtered = other.run(dimension, limit=100)
    if dimension in CAPABILITY_MATRIX[base.source]:
        # The filter reaches the source, and narrows what is offered.
        assert other.asked() != base.asked()
        assert 0 < len(filtered) < len(unfiltered)
    else:
        # An unsupported filter changes nothing at all.
        assert other.asked() == base.asked()
        assert [c.qualified_id for c in filtered] == [c.qualified_id for c in unfiltered]


def test_renditions_are_on_policy_hosts(subject: Subject) -> None:
    found = subject.run()
    for candidate in found:
        ref = subject.provider.full_ref(candidate)
        if subject.policy is None:
            assert ref.kind is ImageRefKind.LOCAL
            assert Path(ref.location).parent == subject.extras["root"]
        else:
            assert ref.kind is ImageRefKind.REMOTE
            validate_url(ref.location, subject.policy)
    if subject.transport is not None and subject.policy is not None:
        assert {call.request.host for call in subject.transport.calls} <= subject.policy.hosts


@pytest.mark.parametrize("name", ["aic", "cma"])
@pytest.mark.parametrize("status", [404, 410])
def test_discovery_404_and_410_are_http_errors(name: str, status: int, tmp_path: Path) -> None:
    # Local media has no discovery endpoint.
    subject = FACTORIES[name](tmp_path)
    museum = subject.extras["museum"]
    assert isinstance(museum, AicMuseum | CmaMuseum)
    path = "/api/v1/artworks/search" if subject.provider.key == "aic" else "/api/artworks/"

    def missing(request: ParsedRequest) -> object:
        return status_response(status)

    museum.overrides[path] = missing  # type: ignore[assignment]
    with pytest.raises(SourceError) as excinfo:
        subject.run()
    assert excinfo.value.kind is SourceErrorKind.HTTP_ERROR


def test_the_aic_size_lookup_404_is_an_http_error() -> None:
    subject = _aic()
    museum = subject.extras["museum"]
    assert isinstance(museum, AicMuseum)
    museum.overrides["/api/v1/images"] = lambda request: status_response(404)
    with pytest.raises(SourceError) as excinfo:
        subject.run()
    assert excinfo.value.kind is SourceErrorKind.HTTP_ERROR


@pytest.mark.parametrize("status", [404, 410])
def test_rendition_404_and_410_are_not_found(subject: Subject, status: int, tmp_path: Path) -> None:
    (candidate, *_rest) = subject.run()
    ref = subject.provider.full_ref(candidate)
    assert subject.fetcher is not None
    if subject.transport is not None:
        subject.transport.handler = lambda request: status_response(status)
    else:
        Path(ref.location).unlink()  # the local equivalent: the file is gone
    with pytest.raises(SourceError) as excinfo:
        subject.fetcher.fetch(ref, tmp_path / "rendition", subject.context().deadline)
    assert excinfo.value.kind is SourceErrorKind.NOT_FOUND


def test_renditions_are_fetched_through_the_fetcher(subject: Subject, tmp_path: Path) -> None:
    (candidate, *_rest) = subject.run()
    ref = subject.provider.full_ref(candidate)
    assert subject.fetcher is not None
    if subject.transport is not None:
        subject.transport.handler = lambda request: image_response(b"\xff\xd8synthetic")
    fetched = subject.fetcher.fetch(ref, tmp_path / "rendition", subject.context().deadline)
    assert fetched.path == tmp_path / "rendition"
    assert fetched.size_bytes > 0


def test_local_inspection_returns_none_for_unreadable_files(tmp_path: Path) -> None:
    subject = _local(tmp_path)
    root = subject.extras["root"]
    assert isinstance(root, Path)
    (root / "broken.jpg").write_bytes(b"\xff\xd8\xff\xe0 not a real JPEG")
    provider = subject.provider
    assert isinstance(provider, LocalMediaProvider)
    probe = LocalInspectionProbe(provider, InProcessExecutor(default_tasks(), subject.clock))
    found = subject.run()
    broken = [c for c in found if c.attribution.title == "broken"]
    assert len(broken) == 1
    assert probe.measure(broken[0], subject.context().deadline) is None
    others = [c for c in found if c.attribution.title != "broken"]
    assert all(probe.measure(c, subject.context().deadline) is not None for c in others)
