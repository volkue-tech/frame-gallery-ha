"""The Art Institute of Chicago adapter (§9.5, D-132, D-146) against a
synthesized API behind the real gateway and a scripted transport."""

from __future__ import annotations

from collections.abc import MutableSequence
from datetime import timedelta
from typing import Any, cast

import pytest

from frame_gallery.budget.allowance import Allowance, AllowanceExhausted
from frame_gallery.budget.deadline import Deadline
from frame_gallery.config.filters import EffectiveFilters, FilterSet
from frame_gallery.domain import FitMode, Size, SourceKey
from frame_gallery.net.gateway import Gateway
from frame_gallery.net.policy import HostPolicy
from frame_gallery.providers.aic import (
    API_HOST,
    ARTWORK_FIELDS,
    IIIF_HOST,
    PAGE_SIZE,
    AicProvider,
    aic_policy,
    rendition_size,
)
from frame_gallery.providers.cache import MemoryMetadataCache
from frame_gallery.providers.contract import (
    Attribution,
    Candidate,
    DiscoveryContext,
    ImageRef,
    ImageRefKind,
    SourceError,
    SourceErrorKind,
)
from frame_gallery.providers.rights import RightsBasis
from frame_gallery.randomness import SeededRandomSource
from frame_gallery.selection.exclusion import ExclusionSet
from frame_gallery.selection.shortlist import DiscoveryEnd, SelectionPolicy, build_shortlist
from frame_gallery.store.cache import ExhaustedPages
from tests.support.clock import FakeClock
from tests.support.museums import (
    AicMuseum,
    ParsedRequest,
    aic_image_id,
    aic_record,
    aic_search,
)
from tests.support.net import (
    PLACEHOLDER_CONTACT,
    TEST_IDENTITY,
    FakeResolver,
    FakeResponse,
    FakeTransport,
    json_response,
    status_response,
)


def filters(period: str | None = None) -> EffectiveFilters:
    return EffectiveFilters(
        source=SourceKey.ART_INSTITUTE_CHICAGO,
        department=None,
        style=None,
        period=period,
        color=None,
        ignored=(),
        requested=FilterSet(source=SourceKey.ART_INSTITUTE_CHICAGO),
    )


class Rig:
    def __init__(self, museum: AicMuseum | None = None, *, allowance: int = 15) -> None:
        self.clock = FakeClock()
        self.museum = museum or AicMuseum()
        self.transport = FakeTransport(clock=self.clock, handler=self.museum)
        self.gateway = Gateway(
            resolver=FakeResolver(),
            transport=self.transport,
            clock=self.clock,
            random=SeededRandomSource(5),
            identity=TEST_IDENTITY,
        )
        self.allowance = Allowance("metadata_requests", allowance)
        self.channel = self.gateway.channel(
            aic_policy(TEST_IDENTITY), metadata_allowance=self.allowance
        )
        self.cache = MemoryMetadataCache(self.clock)
        self.provider = AicProvider(self.channel, self.cache)

    def context(self, seed: int = 11, seconds: float = 300.0) -> DiscoveryContext:
        return DiscoveryContext(
            deadline=Deadline.after(self.clock, seconds, "discovery"),
            random=SeededRandomSource(seed),
        )

    def take(self, count: int, period: str | None = None, seed: int = 11) -> list[Candidate]:
        iterator = self.provider.iter_candidates(filters(period), self.context(seed))
        found: list[Candidate] = []
        for candidate in iterator:
            found.append(candidate)
            if len(found) == count:
                break
        return found

    def searches(self) -> list[ParsedRequest]:
        return [r for r in self.museum.seen if r.path == "/api/v1/artworks/search"]


def test_policy_hosts_pacing_and_courtesy_header() -> None:
    policy = aic_policy(TEST_IDENTITY)
    assert policy.provider_key == "aic"
    assert policy.hosts == {"api.artic.edu", "www.artic.edu"}
    assert policy.min_interval_s == 1.0
    assert dict(policy.courtesy_headers) == {
        "AIC-User-Agent": f"FrameGallery/0.0.0-test ({PLACEHOLDER_CONTACT})"
    }


def test_capabilities() -> None:
    rig = Rig()
    capabilities = rig.provider.capabilities()
    assert capabilities.source is SourceKey.ART_INSTITUTE_CHICAGO
    assert capabilities.provider_key == "aic" == rig.provider.key
    assert capabilities.dims_in_metadata


class TestRequests:
    def test_count_then_a_page_then_its_image_sizes(self) -> None:
        rig = Rig()
        rig.museum.add(30)
        (first,) = rig.take(1)
        assert rig.museum.paths() == [
            "/api/v1/artworks/search",
            "/api/v1/artworks/search",
            "/api/v1/images",
        ]
        count, page, images = rig.museum.seen
        assert count.params == {
            "limit": 0,
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"is_public_domain": True}},
                        {"exists": {"field": "image_id"}},
                    ]
                }
            },
        }
        assert page.params["fields"] == list(ARTWORK_FIELDS)
        assert page.params["limit"] == PAGE_SIZE == 50
        assert page.params["page"] == 1
        assert page.params["query"] == count.params["query"]
        assert set(images.query) == {"ids", "fields", "limit"}
        assert images.query["fields"] == "id,width,height"
        assert len(images.query["ids"].split(",")) == 30 == int(images.query["limit"])
        assert first.dims == Size(1686, 948)
        assert rig.channel.metadata_requests == 3

    def test_every_request_carries_the_courtesy_header(self) -> None:
        rig = Rig()
        rig.museum.add(3)
        rig.take(3)
        for call in rig.transport.calls:
            assert call.request.host == API_HOST
            assert call.request.headers["AIC-User-Agent"].endswith(f"({PLACEHOLDER_CONTACT})")

    def test_requests_are_paced(self) -> None:
        rig = Rig()
        rig.museum.add(3)
        rig.take(1)
        assert rig.clock.sleeps == [pytest.approx(1.0), pytest.approx(1.0)]

    def test_pages_are_sampled_without_replacement(self) -> None:
        rig = Rig()
        rig.museum.add(160, first=1000)
        found = rig.take(160)
        pages = [cast("int", request.params["page"]) for request in rig.searches()[1:]]
        assert sorted(pages) == [1, 2, 3, 4]
        assert len({candidate.native_id for candidate in found}) == 160

    def test_the_result_window_caps_the_pages(self, monkeypatch: pytest.MonkeyPatch) -> None:
        rig = Rig(AicMuseum(total=250_000))
        shuffled: list[list[int]] = []

        class Spy(SeededRandomSource):
            def shuffle(self, items: MutableSequence[Any]) -> None:
                shuffled.append(list(items))
                super().shuffle(items)

        context = DiscoveryContext(Deadline.after(rig.clock, 60, "d"), Spy(1))
        with pytest.raises(AllowanceExhausted):  # 200 empty pages, 15 requests
            list(rig.provider.iter_candidates(filters(), context))
        assert shuffled == [list(range(1, 201))]  # 10 000 / 50

    def test_an_empty_catalogue_ends_after_the_count(self) -> None:
        rig = Rig()
        assert rig.take(5) == []
        assert rig.museum.paths() == ["/api/v1/artworks/search"]

    def test_a_page_without_usable_records_needs_no_size_lookup(self) -> None:
        museum = AicMuseum()
        museum.records = [aic_record(1, public=False), aic_record(2, public=False)]
        rig = Rig(museum)
        assert rig.take(5) == []
        assert rig.museum.paths() == ["/api/v1/artworks/search", "/api/v1/artworks/search"]


class TestCounts:
    def test_counts_are_cached_per_filter_for_a_day(self) -> None:
        rig = Rig()
        rig.museum.add(10)
        rig.take(1)
        rig.take(1)
        counts = [r for r in rig.searches() if r.params["limit"] == 0]
        assert len(counts) == 1
        rig.take(1, period="period_1800_1899")
        counts = [r for r in rig.searches() if r.params["limit"] == 0]
        assert len(counts) == 2
        rig.clock.advance(timedelta(days=1).total_seconds())
        rig.take(1)
        counts = [r for r in rig.searches() if r.params["limit"] == 0]
        assert len(counts) == 3

    @pytest.mark.parametrize(
        "document",
        [
            [],
            {},
            {"pagination": []},
            {"pagination": {"total": -1}},
            {"pagination": {"total": True}},
            {"pagination": {"total": "12"}},
            {"pagination": {"total": 1.5}},
        ],
    )
    def test_malformed_counts(self, document: object) -> None:
        museum = AicMuseum()
        museum.overrides["/api/v1/artworks/search"] = lambda request: json_response(document)
        rig = Rig(museum)
        with pytest.raises(SourceError) as excinfo:
            rig.take(1)
        assert excinfo.value.kind is SourceErrorKind.UNEXPECTED_FORMAT

    @pytest.mark.parametrize("data", [None, {}, "records"])
    def test_malformed_pages(self, data: object) -> None:
        museum = AicMuseum(total=10)

        def search(request: ParsedRequest) -> FakeResponse:
            if request.params["limit"] == 0:
                return json_response(aic_search([], 10))
            return json_response({"pagination": {"total": 10}, "data": data})

        museum.overrides["/api/v1/artworks/search"] = search
        with pytest.raises(SourceError) as excinfo:
            Rig(museum).take(1)
        assert excinfo.value.kind is SourceErrorKind.UNEXPECTED_FORMAT


class TestRecords:
    def test_every_record_is_checked_again(self) -> None:
        museum = AicMuseum()
        good = aic_record(1)
        bad = [
            aic_record(2, public=False),
            aic_record(3, public="true"),
            aic_record(4, public=None),
            {**aic_record(5), "id": True},
            {**aic_record(6), "id": -6},
            {**aic_record(7), "id": "7"},
            {**aic_record(8), "id": 10**11},
            {**aic_record(9), "image_id": aic_image_id(0xABC).upper()},
            {**aic_record(10), "image_id": None},
            {**aic_record(11), "image_id": "../../etc"},
            "not an object",
            None,
        ]
        museum.records = [good, *bad]
        museum.sizes = {aic_image_id(n): (3000, 2000) for n in range(1, 12)}
        found = Rig(museum).take(20)
        assert [candidate.native_id for candidate in found] == ["1"]
        (candidate,) = found
        assert candidate.rights_basis is RightsBasis.CC0
        assert candidate.rights_field == "is_public_domain"
        assert candidate.qualified_id == "aic:1"

    def test_attribution_is_cleaned_text(self) -> None:
        museum = AicMuseum()
        record = aic_record(1, title="  A\u0000 Title\nwith\u202e controls  ")
        record["artist_display"] = 42
        record["date_display"] = "x" * 1000
        record["credit_line"] = ""
        museum.records = [record]
        museum.sizes = {aic_image_id(1): (4000, 2250)}
        (candidate,) = Rig(museum).take(1)
        assert candidate.attribution == Attribution(
            title="A Title with controls",
            creator=None,
            date_text="x" * 300,
            credit_line=None,
        )

    def test_sizes_come_from_the_images_resource(self) -> None:
        museum = AicMuseum()
        museum.records = [aic_record(n) for n in range(1, 6)]
        museum.sizes = {
            aic_image_id(1): (3840, 2160),
            aic_image_id(2): (1686, 1000),
            aic_image_id(3): (1685, 1000),  # narrower than the rendition: skipped
            aic_image_id(4): ("3000", "2000"),  # digit strings are accepted
            # 5: no image record: offered without dimensions
        }
        found = {c.native_id: c.dims for c in Rig(museum).take(10)}
        assert found == {
            "1": Size(1686, 948),
            "2": Size(1686, 1000),
            "4": Size(1686, 1124),
            "5": None,
        }

    @pytest.mark.parametrize(
        "entry",
        [
            "not an object",
            {"id": 5, "width": 3000, "height": 2000},
            {"id": aic_image_id(1), "width": 0, "height": 10},
            {"id": aic_image_id(1), "width": True, "height": 10},
            {"id": aic_image_id(1), "width": 3000},
            {"id": aic_image_id(1), "width": 10**6, "height": 10},
        ],
    )
    def test_malformed_image_entries_give_no_size(self, entry: object) -> None:
        museum = AicMuseum()
        museum.records = [aic_record(1)]
        museum.overrides["/api/v1/images"] = lambda request: json_response({"data": [entry]})
        (candidate,) = Rig(museum).take(1)
        assert candidate.dims is None

    def test_a_malformed_image_response_is_an_error(self) -> None:
        museum = AicMuseum()
        museum.records = [aic_record(1)]
        museum.overrides["/api/v1/images"] = lambda request: json_response({"data": "x"})
        with pytest.raises(SourceError) as excinfo:
            Rig(museum).take(1)
        assert excinfo.value.kind is SourceErrorKind.UNEXPECTED_FORMAT

    def test_repeated_image_ids_are_looked_up_once(self) -> None:
        museum = AicMuseum()
        museum.records = [aic_record(1, image=7), aic_record(2, image=7)]
        museum.sizes = {aic_image_id(7): (3840, 2160)}
        rig = Rig(museum)
        assert len(rig.take(5)) == 2
        (images,) = [r for r in rig.museum.seen if r.path == "/api/v1/images"]
        assert images.query["ids"] == aic_image_id(7)


class TestPeriods:
    @pytest.mark.parametrize(
        ("key", "bounds"),
        [
            ("period_before_1400", {"lte": 1399}),
            ("period_1400_1599", {"gte": 1400, "lte": 1599}),
            ("period_1800_1899", {"gte": 1800, "lte": 1899}),
            ("period_1900_and_later", {"gte": 1900}),
        ],
    )
    def test_the_range_is_sent(self, key: str, bounds: dict[str, int]) -> None:
        rig = Rig()
        rig.museum.add(2)
        rig.take(1, period=key)
        clauses = rig.searches()[0].params["query"]["bool"]["filter"]  # type: ignore[index]
        assert clauses[-1] == {"range": {"date_start": bounds}}

    def test_the_range_is_checked_on_every_record(self) -> None:
        museum = AicMuseum()
        museum.records = [
            aic_record(1, date_start=1850),
            aic_record(2, date_start=1799),
            aic_record(3, date_start=1900),
            aic_record(4, date_start=None),
            aic_record(5, date_start="1850"),
            aic_record(6, date_start=1800),
            aic_record(7, date_start=1899),
        ]
        museum.sizes = {aic_image_id(n): (3840, 2160) for n in range(1, 8)}
        found = Rig(museum).take(10, period="period_1800_1899")
        assert sorted(c.native_id for c in found) == ["1", "6", "7"]

    def test_without_a_period_the_date_is_ignored(self) -> None:
        museum = AicMuseum()
        museum.records = [aic_record(1, date_start=None), aic_record(2, date_start="?")]
        museum.sizes = {aic_image_id(n): (3840, 2160) for n in (1, 2)}
        assert len(Rig(museum).take(5)) == 2

    def test_unknown_period_keys_are_a_programming_error(self) -> None:
        with pytest.raises(ValueError, match="unknown period"):
            Rig().take(1, period="period_jurassic")


class TestFailures:
    @pytest.mark.parametrize(
        ("status", "kind"),
        [
            (404, SourceErrorKind.HTTP_ERROR),
            (403, SourceErrorKind.STOPPED),
            (500, SourceErrorKind.HTTP_ERROR),
        ],
    )
    def test_search_failures(self, status: int, kind: SourceErrorKind) -> None:
        museum = AicMuseum()
        museum.overrides["/api/v1/artworks/search"] = lambda request: status_response(status)
        with pytest.raises(SourceError) as excinfo:
            Rig(museum).take(1)
        assert excinfo.value.kind is kind

    def test_the_metadata_allowance_ends_discovery(self) -> None:
        rig = Rig()
        rig.museum.add(500)
        rig.museum.sizes = {}  # no sizes: nothing is ever shortlisted
        iterator = rig.provider.iter_candidates(filters(), rig.context())
        with pytest.raises(AllowanceExhausted):
            for _candidate in iterator:
                pass
        # 1 count + 7 pages x (search + images) = 15 requests.
        assert rig.channel.metadata_requests == 15
        assert len(rig.transport.calls) == 15


class TestRefs:
    def test_full_ref_is_the_documented_iiif_rendition(self) -> None:
        museum = AicMuseum()
        museum.records = [aic_record(42, image=9)]
        museum.sizes = {aic_image_id(9): (3840, 2160)}
        rig = Rig(museum)
        (candidate,) = rig.take(1)
        assert rig.provider.full_ref(candidate) == ImageRef(
            ImageRefKind.REMOTE,
            f"https://{IIIF_HOST}/iiif/2/{aic_image_id(9)}/full/1686,/0/default.jpg",
        )

    def test_foreign_or_unknown_candidates_are_refused(self) -> None:
        rig = Rig()
        stranger = Candidate("cma", "1", RightsBasis.CC0, "x", Attribution(), None)
        unknown = Candidate("aic", "99", RightsBasis.CC0, "x", Attribution(), None)
        for candidate in (stranger, unknown):
            with pytest.raises(ValueError, match="not offered"):
                rig.provider.full_ref(candidate)

    def test_the_channel_must_be_the_aic_channel(self) -> None:
        rig = Rig()
        other = rig.gateway.channel(
            HostPolicy("cma", frozenset({"openaccess-api.clevelandart.org"})),
            metadata_allowance=Allowance("m", 1),
        )
        with pytest.raises(ValueError, match="another provider"):
            AicProvider(other, rig.cache)


class TestExhaustedPages:
    """Pages that offer nothing new are remembered for 7 days (§9.5, D-156)."""

    def museum(self) -> AicMuseum:
        museum = AicMuseum()
        museum.add(3 * PAGE_SIZE)
        return museum

    def discover(self, rig: Rig, excluded: set[str], seed: int = 11) -> DiscoveryContext:
        context = DiscoveryContext(
            deadline=Deadline.after(rig.clock, 300, "discovery"),
            random=SeededRandomSource(seed),
            is_excluded_for_good=excluded.__contains__,
        )
        list(rig.provider.iter_candidates(filters(), context))
        return context

    def pages_searched(self, rig: Rig) -> list[int]:
        pages = [r.params.get("page") for r in rig.searches() if r.params["limit"] != 0]
        return sorted(page for page in pages if isinstance(page, int))

    def test_a_fully_excluded_page_is_remembered_and_then_skipped(self) -> None:
        rig = Rig(self.museum())
        first_page = {f"aic:{n}" for n in range(1, PAGE_SIZE + 1)}
        context = self.discover(rig, first_page)
        assert context.notes.pages_skipped == 0
        hints = rig.cache.get_exhausted("aic:exhausted:any")
        assert hints == ExhaustedPages(3 * PAGE_SIZE, frozenset({1}))
        rig.museum.seen.clear()
        context = self.discover(rig, first_page, seed=12)
        assert context.notes.pages_skipped == 1
        assert self.pages_searched(rig) == [2, 3]

    def test_a_page_with_one_new_work_is_not_remembered(self) -> None:
        rig = Rig(self.museum())
        almost = {f"aic:{n}" for n in range(1, PAGE_SIZE)}  # aic:50 stays new
        self.discover(rig, almost)
        assert rig.cache.get_exhausted("aic:exhausted:any") is None

    def test_pages_without_new_works_to_offer_are_not_remembered(self) -> None:
        """Review finding: an empty or unusable page may be passing, and a
        skipped page would later read as "nothing new left"."""
        museum = AicMuseum()
        museum.add(PAGE_SIZE, width=1000, height=800)  # too narrow for the rendition
        museum.add(PAGE_SIZE, first=PAGE_SIZE + 1)
        for number in range(PAGE_SIZE + 1, 2 * PAGE_SIZE + 1):
            del museum.sizes[aic_image_id(number)]  # no image record: no dimensions
        rig = Rig(museum)
        self.discover(rig, set())
        assert rig.cache.get_exhausted("aic:exhausted:any") is None

    def test_an_empty_page_is_not_remembered(self) -> None:
        museum = self.museum()
        museum.overrides["/api/v1/artworks/search"] = lambda request: json_response(
            aic_search([], 3 * PAGE_SIZE)
        )
        rig = Rig(museum)
        self.discover(rig, set())
        assert rig.cache.get_exhausted("aic:exhausted:any") is None

    def test_a_page_of_sent_and_unusable_works_is_remembered(self) -> None:
        museum = AicMuseum()
        museum.add(PAGE_SIZE - 1, width=1000, height=800)
        museum.add(1, first=PAGE_SIZE)
        rig = Rig(museum)
        self.discover(rig, {f"aic:{PAGE_SIZE}"})
        hints = rig.cache.get_exhausted("aic:exhausted:any")
        assert hints == ExhaustedPages(PAGE_SIZE, frozenset({1}))

    def test_hints_for_another_total_are_ignored(self) -> None:
        rig = Rig(self.museum())
        rig.cache.add_exhausted("aic:exhausted:any", 999, [1, 2], timedelta(days=7))
        context = self.discover(rig, set())
        assert context.notes.pages_skipped == 0
        assert self.pages_searched(rig) == [1, 2, 3]

    def test_hints_are_kept_per_filter_signature(self) -> None:
        rig = Rig(self.museum())
        rig.cache.add_exhausted("aic:exhausted:any", 3 * PAGE_SIZE, [1, 2, 3], timedelta(days=7))
        context = DiscoveryContext(
            deadline=Deadline.after(rig.clock, 300, "discovery"), random=SeededRandomSource(1)
        )
        found = list(rig.provider.iter_candidates(filters("period_1800_1899"), context))
        assert context.notes.pages_skipped == 0
        assert len(found) == 3 * PAGE_SIZE


def test_rendition_size() -> None:
    assert rendition_size(Size(1685, 1000)) is None
    assert rendition_size(Size(1686, 1)) == Size(1686, 1)
    assert rendition_size(Size(3372, 1)) == Size(1686, 1)  # never 0
    assert rendition_size(Size(3840, 2160)) == Size(1686, 948)
    assert rendition_size(Size(2000, 3000)) == Size(1686, 2529)


def test_selection_over_the_synthetic_api() -> None:
    """Adapter, gateway, and selection together: landscape works near 16:9
    are shortlisted, and only documented hosts are contacted."""
    museum = AicMuseum()
    museum.records = [aic_record(n) for n in range(1, 41)]
    museum.sizes = {aic_image_id(n): (3000, 3000) for n in range(1, 41)}  # squares
    museum.sizes[aic_image_id(17)] = (3840, 2160)
    museum.sizes[aic_image_id(33)] = (1920, 1080)
    rig = Rig(museum)
    context = rig.context()
    result = build_shortlist(
        rig.provider.iter_candidates(filters(), context),
        exclusions=ExclusionSet(frozenset({"aic:33"})),
        policy=SelectionPolicy(
            landscape_only=True, strict_tv_format=True, fit_mode=FitMode.CONTAIN
        ),
        allowed_rights=frozenset({RightsBasis.CC0}),
        deadline=context.deadline,
        random=SeededRandomSource(2),
        candidate_allowance=Allowance("candidates", 150),
        probe_allowance=Allowance("remote_probes", 30),
        inspection_allowance=Allowance("local_inspections", 300),
    )
    assert [entry.candidate.qualified_id for entry in result.entries] == ["aic:17"]
    assert result.end is DiscoveryEnd.EXHAUSTED
    assert result.stats.probes_used == 0
    assert {call.request.host for call in rig.transport.calls} == {API_HOST}
