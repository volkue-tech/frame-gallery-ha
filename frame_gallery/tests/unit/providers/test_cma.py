"""The Cleveland Museum of Art adapter (§9.6, D-136, D-146) against a
synthesized Open Access API behind the real gateway."""

from __future__ import annotations

import logging
from collections.abc import MutableSequence
from datetime import timedelta
from typing import Any

import pytest

from frame_gallery.budget.allowance import Allowance, AllowanceExhausted
from frame_gallery.budget.deadline import Deadline
from frame_gallery.config.filters import EffectiveFilters, FilterSet
from frame_gallery.domain import FitMode, Size, SourceKey
from frame_gallery.net.gateway import Gateway
from frame_gallery.net.policy import HostPolicy
from frame_gallery.providers import cma as cma_module
from frame_gallery.providers.cache import MemoryMetadataCache
from frame_gallery.providers.cma import (
    API_HOST,
    DEPARTMENTS,
    DOCUMENTED_DEPARTMENTS,
    FIELDS,
    IMAGE_HOST,
    PAGE_SIZE,
    CmaProvider,
    cma_policy,
)
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
from tests.support.museums import CMA_CDN, CmaMuseum, ParsedRequest, cma_record
from tests.support.net import (
    PLACEHOLDER_CONTACT,
    TEST_IDENTITY,
    FakeResolver,
    FakeTransport,
    json_response,
    status_response,
)


def filters(department: str | None = None, period: str | None = None) -> EffectiveFilters:
    return EffectiveFilters(
        source=SourceKey.CLEVELAND_MUSEUM_OF_ART,
        department=department,
        style=None,
        period=period,
        color=None,
        ignored=(),
        requested=FilterSet(source=SourceKey.CLEVELAND_MUSEUM_OF_ART),
    )


class Rig:
    def __init__(self, museum: CmaMuseum | None = None, *, allowance: int = 15) -> None:
        self.clock = FakeClock()
        self.museum = museum or CmaMuseum()
        self.transport = FakeTransport(clock=self.clock, handler=self.museum)
        self.gateway = Gateway(
            resolver=FakeResolver(),
            transport=self.transport,
            clock=self.clock,
            random=SeededRandomSource(5),
            identity=TEST_IDENTITY,
        )
        self.channel = self.gateway.channel(
            cma_policy(), metadata_allowance=Allowance("metadata_requests", allowance)
        )
        self.cache = MemoryMetadataCache(self.clock)
        self.provider = CmaProvider(self.channel, self.cache)

    def context(self, seed: int = 11) -> DiscoveryContext:
        return DiscoveryContext(
            deadline=Deadline.after(self.clock, 300, "discovery"), random=SeededRandomSource(seed)
        )

    def take(self, count: int, **kwargs: str | None) -> list[Candidate]:
        found: list[Candidate] = []
        for candidate in self.provider.iter_candidates(filters(**kwargs), self.context()):
            found.append(candidate)
            if len(found) == count:
                break
        return found


def test_policy() -> None:
    policy = cma_policy()
    assert policy.provider_key == "cma"
    assert policy.hosts == {"openaccess-api.clevelandart.org", "openaccess-cdn.clevelandart.org"}
    assert dict(policy.courtesy_headers) == {}
    assert policy.min_interval_s == 1.0


def test_capabilities() -> None:
    provider = Rig().provider
    capabilities = provider.capabilities()
    assert capabilities.source is SourceKey.CLEVELAND_MUSEUM_OF_ART
    assert capabilities.provider_key == "cma" == provider.key
    assert capabilities.dims_in_metadata


def test_the_curated_departments_are_documented_values() -> None:
    assert len(DOCUMENTED_DEPARTMENTS) == 21
    assert set(DEPARTMENTS.values()) <= set(DOCUMENTED_DEPARTMENTS)
    assert "Performing Arts, Music, & Film" not in DEPARTMENTS.values()
    assert all(key.startswith("cma_") for key in DEPARTMENTS)
    assert len(set(DEPARTMENTS.values())) == len(DEPARTMENTS) == 12


class TestRequests:
    def test_every_request_is_cc0_with_an_image_and_an_explicit_limit(self) -> None:
        rig = Rig()
        rig.museum.add(40)
        rig.take(30)
        assert rig.museum.targets
        for target in rig.museum.targets:
            assert target.startswith("/api/artworks/?cc0&has_image=1&")
        for request in rig.museum.seen:
            assert request.host == API_HOST
            assert request.query["cc0"] == ""
            assert request.query["has_image"] == "1"
            assert request.query["limit"] in {"1", "25"}

    def test_count_then_random_pages(self) -> None:
        rig = Rig()
        rig.museum.add(90)
        found = rig.take(90)
        count, *pages = rig.museum.seen
        assert count.query["limit"] == "1"
        assert count.query["fields"] == "id"
        skips = [int(page.query["skip"]) for page in pages]
        assert sorted(skips) == [0, 25, 50, 75]
        assert all(page.query["limit"] == str(PAGE_SIZE) == "25" for page in pages)
        assert all(page.query["fields"] == ",".join(FIELDS) for page in pages)
        assert "images" in FIELDS
        assert len({candidate.native_id for candidate in found}) == 90

    def test_no_request_ever_names_the_tiff(self) -> None:
        rig = Rig()
        rig.museum.add(5)
        found = rig.take(5)
        refs = [rig.provider.full_ref(candidate).location for candidate in found]
        assert all(ref.endswith("_print.jpg") for ref in refs)
        assert all(".tif" not in target for target in rig.museum.targets)

    def test_requests_carry_the_honest_user_agent_only(self) -> None:
        rig = Rig()
        rig.museum.add(2)
        rig.take(2)
        headers = rig.transport.calls[0].request.headers
        assert headers["User-Agent"] == f"FrameGallery/0.0.0-test (contact: {PLACEHOLDER_CONTACT})"
        assert "AIC-User-Agent" not in headers

    def test_an_empty_result_ends_after_the_count(self) -> None:
        rig = Rig()
        assert rig.take(3) == []
        assert len(rig.museum.seen) == 1


class TestFilters:
    def test_departments_are_sent_as_documented_values(self) -> None:
        museum = CmaMuseum()
        museum.add(3, department="European Painting and Sculpture")
        museum.add(3, first=10, department="Prints")
        rig = Rig(museum)
        found = rig.take(10, department="cma_european_painting_sculpture")
        assert sorted(c.native_id for c in found) == ["1", "2", "3"]
        assert all(
            "&department=European%20Painting%20and%20Sculpture&" in target
            for target in rig.museum.targets
        )

    def test_a_record_of_another_department_is_skipped(self) -> None:
        museum = CmaMuseum()
        museum.records = [cma_record(1, department="Prints"), cma_record(2, department="Drawings")]
        museum.total = 2
        museum._matches = lambda record, query: True  # type: ignore[method-assign]
        found = Rig(museum).take(5, department="cma_prints")
        assert [c.native_id for c in found] == ["1"]

    def test_unknown_department_keys_are_a_programming_error(self) -> None:
        with pytest.raises(ValueError, match="unknown Cleveland department"):
            Rig().take(1, department="cma_performing_arts")

    @pytest.mark.parametrize(
        ("key", "sent"),
        [
            ("period_before_1400", {"created_before": "1400"}),
            ("period_1400_1599", {"created_after": "1399", "created_before": "1600"}),
            ("period_1900_and_later", {"created_after": "1899"}),
        ],
    )
    def test_periods_are_widened_by_one_year(self, key: str, sent: dict[str, str]) -> None:
        rig = Rig()
        rig.museum.add(1, earliest=1450)
        rig.take(1, period=key)
        query = rig.museum.seen[0].query
        assert {k: v for k, v in query.items() if k.startswith("created_")} == sent

    def test_the_exact_range_is_enforced_on_creation_date_earliest(self) -> None:
        museum = CmaMuseum()
        museum.records = [
            cma_record(1, earliest=1800),
            cma_record(2, earliest=1899),
            cma_record(3, earliest=1799),
            cma_record(4, earliest=1900),
            cma_record(5, earliest=None),
            cma_record(6, earliest="1850"),
            cma_record(7, earliest=1850),
        ]
        museum.total = 7
        museum._matches = lambda record, query: True  # type: ignore[method-assign]
        found = Rig(museum).take(10, period="period_1800_1899")
        assert sorted(c.native_id for c in found) == ["1", "2", "7"]

    def test_counts_are_cached_per_filter_signature(self) -> None:
        rig = Rig()
        rig.museum.add(3, department="Drawings")
        rig.take(1, department="cma_drawings")
        rig.take(1, department="cma_drawings")
        rig.take(1, department="cma_drawings", period="period_1800_1899")
        counts = [r for r in rig.museum.seen if r.query["limit"] == "1"]
        assert len(counts) == 2


class TestRecords:
    def test_only_cc0_records_with_a_print_are_offered(self) -> None:
        museum = CmaMuseum()
        museum.records = [
            cma_record(1),
            cma_record(2, status="Copyrighted"),
            cma_record(3, status="Other"),
            cma_record(4, status="cc0"),
            {**cma_record(5), "share_license_status": None},
            {**cma_record(6), "id": True},
            {**cma_record(7), "id": "7"},
            {**cma_record(8), "id": 0},
            {**cma_record(9), "images": None},
            {**cma_record(10), "images": {"web": {}, "full": {}}},
            {**cma_record(11), "images": {"print": "x"}},
            "not an object",
        ]
        rig = Rig(museum)
        found = rig.take(20)
        assert [c.native_id for c in found] == ["1"]
        (candidate,) = found
        assert candidate.rights_basis is RightsBasis.CC0
        assert candidate.rights_field == "share_license_status"
        assert candidate.qualified_id == "cma:1"
        assert candidate.dims == Size(3400, 1913)

    @pytest.mark.parametrize(
        "url",
        [
            f"https://{API_HOST}/1999.1/1999.1_print.jpg",
            "https://images.example.org/1999.1_print.jpg",
            f"http://{CMA_CDN}/1999.1/1999.1_print.jpg",
            f"https://{CMA_CDN}/1999.1/1999.1_full.tif",
            f"https://{CMA_CDN}/1999.1/1999.1_print.jpg?x=1",
            f"https://{CMA_CDN}/1999.1/../print.jpg",
            f"https://{CMA_CDN}:8443/1999.1/1999.1_print.jpg",
            f"https://{CMA_CDN}/1999.1//1999.1_print.jpg",
            f"https://{CMA_CDN}/./1999.1_print.jpg",
            "",
            42,
        ],
    )
    def test_prints_elsewhere_are_skipped_and_counted(
        self, url: object, caplog: pytest.LogCaptureFixture
    ) -> None:
        museum = CmaMuseum()
        museum.records = [cma_record(1, print_url=url), cma_record(2)]
        with caplog.at_level(logging.WARNING):
            found = Rig(museum).take(5)
        assert [c.native_id for c in found] == ["2"]
        assert f"cma: 1 print renditions were skipped: not a JPEG on {IMAGE_HOST}" in caplog.text

    def test_upper_case_extensions_are_accepted(self) -> None:
        museum = CmaMuseum()
        museum.records = [cma_record(1, print_url=f"https://{CMA_CDN}/a/B_PRINT.JPG")]
        rig = Rig(museum)
        (candidate,) = rig.take(1)
        assert rig.provider.full_ref(candidate).location == f"https://{CMA_CDN}/a/B_PRINT.JPG"

    @pytest.mark.parametrize(
        ("width", "height", "dims"),
        [
            ("3400", "1913", Size(3400, 1913)),
            (3400, 2267, Size(3400, 2267)),
            ("0", "10", None),
            ("3400", None, None),
            ("3400.0", "10", None),
            (True, 10, None),
        ],
    )
    def test_print_sizes_are_parsed_defensively(
        self, width: object, height: object, dims: Size | None
    ) -> None:
        museum = CmaMuseum()
        museum.records = [cma_record(1, width=width, height=height)]
        (candidate,) = Rig(museum).take(1)
        assert candidate.dims == dims

    def test_attribution(self) -> None:
        museum = CmaMuseum()
        record = cma_record(1, title="  Synthetic\tTitle ")
        museum.records = [
            record,
            {**cma_record(2), "creators": [], "url": "https://evil.example/art/x"},
            {**cma_record(3), "creators": ["not an object"], "url": None},
            {**cma_record(4), "creators": None},
        ]
        found = {c.native_id: c.attribution for c in Rig(museum).take(4)}
        assert found["1"] == Attribution(
            title="Synthetic Title",
            creator="Synthetic Artist 1 (invented, 1800-1880)",
            date_text="c. 1880",
            detail_url="https://clevelandart.org/art/1999.1",
        )
        assert found["2"].creator is None
        assert found["2"].detail_url is None
        assert found["3"].creator is None
        assert found["4"].creator is None


class TestFailures:
    @pytest.mark.parametrize(
        "document",
        [
            [],
            {},
            {"info": []},
            {"info": {"total": -1}},
            {"info": {"total": "10"}},
        ],
    )
    def test_malformed_counts(self, document: object) -> None:
        museum = CmaMuseum()
        museum.overrides["/api/artworks/"] = lambda request: json_response(document)
        with pytest.raises(SourceError) as excinfo:
            Rig(museum).take(1)
        assert excinfo.value.kind is SourceErrorKind.UNEXPECTED_FORMAT

    def test_malformed_pages(self) -> None:
        museum = CmaMuseum()

        def respond(request: ParsedRequest) -> Any:
            if request.query["limit"] == "1":
                return json_response({"info": {"total": 5}, "data": []})
            return json_response({"info": {"total": 5}, "data": {"not": "a list"}})

        museum.overrides["/api/artworks/"] = respond
        with pytest.raises(SourceError) as excinfo:
            Rig(museum).take(1)
        assert excinfo.value.kind is SourceErrorKind.UNEXPECTED_FORMAT

    @pytest.mark.parametrize(
        ("status", "kind"),
        [
            (401, SourceErrorKind.STOPPED),
            (403, SourceErrorKind.STOPPED),
            (404, SourceErrorKind.HTTP_ERROR),
        ],
    )
    def test_http_failures(self, status: int, kind: SourceErrorKind) -> None:
        museum = CmaMuseum()
        museum.overrides["/api/artworks/"] = lambda request: status_response(status)
        rig = Rig(museum)
        with pytest.raises(SourceError) as excinfo:
            rig.take(1)
        assert excinfo.value.kind is kind
        assert rig.channel.stopped is (kind is SourceErrorKind.STOPPED)

    def test_the_metadata_allowance_ends_discovery(self) -> None:
        museum = CmaMuseum()
        museum.add(600, status="Copyrighted")  # nothing is ever offered
        museum.total = 600
        museum._matches = lambda record, query: True  # type: ignore[method-assign]
        rig = Rig(museum)
        with pytest.raises(AllowanceExhausted):
            rig.take(1)
        assert rig.channel.metadata_requests == 15  # 1 count + 14 pages


class TestPageOrder:
    def test_small_totals_are_shuffled_lists(self) -> None:
        order = list(cma_module._page_order(10, SeededRandomSource(3)))
        assert sorted(order) == list(range(10))

    def test_large_totals_are_drawn_lazily_without_repeats(self) -> None:
        order = cma_module._page_order(10**9, SeededRandomSource(3))
        pages = [next(order) for _ in range(50)]
        assert len(set(pages)) == 50
        assert all(0 <= page < 10**9 for page in pages)

    def test_repeated_draws_end_the_order(self) -> None:
        class Stuck(SeededRandomSource):
            def randrange(self, stop: int) -> int:
                return 7

            def shuffle(self, items: MutableSequence[Any]) -> None:  # pragma: no cover
                raise AssertionError

        assert list(cma_module._page_order(10**6, Stuck(0))) == [7]


class TestExhaustedPages:
    """Offsets that offer nothing new are remembered for 7 days (§9.6, D-156)."""

    def discover(self, rig: Rig, excluded: set[str], seed: int = 11) -> DiscoveryContext:
        context = DiscoveryContext(
            deadline=Deadline.after(rig.clock, 300, "discovery"),
            random=SeededRandomSource(seed),
            is_excluded_for_good=excluded.__contains__,
        )
        list(rig.provider.iter_candidates(filters(), context))
        return context

    def skips(self, rig: Rig) -> list[int]:
        return sorted(int(r.query["skip"]) for r in rig.museum.seen if "skip" in r.query)

    def test_a_fully_excluded_offset_is_remembered_and_then_skipped(self) -> None:
        museum = CmaMuseum()
        museum.add(75)
        rig = Rig(museum)
        first = {f"cma:{n}" for n in range(1, 26)}
        self.discover(rig, first)
        assert rig.cache.get_exhausted("cma:exhausted:any:any") == ExhaustedPages(
            75, frozenset({0})
        )
        rig.museum.seen.clear()
        context = self.discover(rig, first, seed=5)
        assert context.notes.pages_skipped == 1
        assert self.skips(rig) == [25, 50]

    def test_prints_without_dimensions_are_not_remembered(self) -> None:
        """A work not sent yet keeps its page, even without dimensions."""
        museum = CmaMuseum()
        museum.add(25, width="unknown")
        rig = Rig(museum)
        self.discover(rig, set())
        assert rig.cache.get_exhausted("cma:exhausted:any:any") is None

    def test_an_empty_page_is_not_remembered(self) -> None:
        museum = CmaMuseum()
        museum.total = 25  # the count says 25, but the page comes back empty
        rig = Rig(museum)
        self.discover(rig, set())
        assert rig.cache.get_exhausted("cma:exhausted:any:any") is None

    def test_hints_beyond_the_current_pages_are_not_counted(self) -> None:
        museum = CmaMuseum()
        museum.add(25)
        rig = Rig(museum)
        rig.cache.add_exhausted("cma:exhausted:any:any", 25, [0, 7], timedelta(days=7))
        context = self.discover(rig, set())
        assert context.notes.pages_skipped == 1
        assert self.skips(rig) == []

    def test_large_totals_skip_hinted_pages_while_drawing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(cma_module, "SHUFFLE_LIMIT", 1)
        order = list(cma_module._page_order(4, SeededRandomSource(3), skip=frozenset({0, 2})))
        assert sorted(order) == [1, 3]

    def test_small_totals_skip_hinted_pages(self) -> None:
        order = list(cma_module._page_order(10, SeededRandomSource(3), skip=frozenset({1, 2})))
        assert sorted(order) == [0, 3, 4, 5, 6, 7, 8, 9]


class TestRefs:
    def test_foreign_or_unknown_candidates_are_refused(self) -> None:
        rig = Rig()
        for candidate in (
            Candidate("aic", "1", RightsBasis.CC0, "x", Attribution(), None),
            Candidate("cma", "404", RightsBasis.CC0, "x", Attribution(), None),
        ):
            with pytest.raises(ValueError, match="not offered"):
                rig.provider.full_ref(candidate)

    def test_the_channel_must_be_the_cma_channel(self) -> None:
        rig = Rig()
        other = rig.gateway.channel(
            HostPolicy("aic", frozenset({"api.artic.edu"})), metadata_allowance=Allowance("m", 1)
        )
        with pytest.raises(ValueError, match="another provider"):
            CmaProvider(other, rig.cache)

    def test_the_print_is_the_ref(self) -> None:
        rig = Rig()
        rig.museum.add(1)
        (candidate,) = rig.take(1)
        assert rig.provider.full_ref(candidate) == ImageRef(
            ImageRefKind.REMOTE, f"https://{CMA_CDN}/1999.1/1999.1_print.jpg"
        )


def test_selection_over_the_synthetic_api() -> None:
    museum = CmaMuseum()
    museum.add(30, width="3400", height="3400")  # squares
    museum.records[11] = cma_record(12, width="3400", height="1913")
    museum.records[20] = cma_record(21, status="Copyrighted", width="3400", height="1913")
    rig = Rig(museum)
    context = rig.context()
    result = build_shortlist(
        rig.provider.iter_candidates(filters(), context),
        exclusions=ExclusionSet(),
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
    assert [entry.candidate.qualified_id for entry in result.entries] == ["cma:12"]
    assert result.end is DiscoveryEnd.EXHAUSTED
    assert result.stats.probes_used == 0
