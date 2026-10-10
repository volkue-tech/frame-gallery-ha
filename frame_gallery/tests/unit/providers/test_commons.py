"""Commons safety, finite discovery, no-repeat and source capabilities (D-206)."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from frame_gallery.app.artwork_info import artwork_info
from frame_gallery.budget.allowance import Allowance, AllowanceExhausted
from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.config.capabilities import CAPABILITY_MATRIX
from frame_gallery.config.filters import EffectiveFilters, FilterDimension, FilterSet
from frame_gallery.domain import Size, SourceKey
from frame_gallery.net.gateway import Gateway
from frame_gallery.net.identity import commons_identity
from frame_gallery.net.policy import HostPolicy
from frame_gallery.providers.commons import CommonsProvider, commons_policy
from frame_gallery.providers.commons_catalog import CATALOG, CuratedWork
from frame_gallery.providers.contract import (
    Candidate,
    DiscoveryContext,
    ImageRefKind,
    SourceError,
    SourceErrorKind,
)
from frame_gallery.providers.rights import RightsBasis
from frame_gallery.randomness import SeededRandomSource
from tests.support.clock import FakeClock
from tests.support.commons import TEST_CATALOG, CommonsSite, record
from tests.support.net import (
    TEST_IDENTITY,
    FakeResolver,
    FakeTransport,
    json_response,
    status_response,
)


def filters() -> EffectiveFilters:
    return EffectiveFilters(
        SourceKey.WIKIMEDIA_COMMONS,
        None,
        None,
        None,
        None,
        (),
        FilterSet(SourceKey.WIKIMEDIA_COMMONS),
    )


class Rig:
    def __init__(self, *, allowance: int = 15) -> None:
        self.clock = FakeClock()
        self.site = CommonsSite()
        self.transport = FakeTransport(clock=self.clock, handler=self.site)
        self.gateway = Gateway(
            resolver=FakeResolver(),
            transport=self.transport,
            clock=self.clock,
            random=SeededRandomSource(5),
            identity=TEST_IDENTITY,
        )
        self.channel = self.gateway.channel(
            commons_policy(), metadata_allowance=Allowance("metadata", allowance)
        )
        self.provider = CommonsProvider(self.channel, TEST_CATALOG)

    def context(self, seed: int = 5) -> DiscoveryContext:
        return DiscoveryContext(
            Deadline.after(self.clock, 30, "discovery"), SeededRandomSource(seed)
        )

    def run(self) -> list[Candidate]:
        return list(self.provider.iter_candidates(filters(), self.context()))


def test_historical_400_manifest_remains_pinned_and_retained() -> None:
    root = Path(__file__).resolve().parents[3]
    baseline_path = root / "research/commons-wide-selection-2026-10-06.json"
    baseline = json.loads(baseline_path.read_text())
    manifest = json.loads((root / "research/commons-400-selection-2026-10-06.json").read_text())
    old_catalog = tuple(
        CuratedWork(row["id"], row["file_title"], row["sha1"], row["title"], row["artist"])
        for row in manifest["included"]
    )
    assert len(old_catalog) == len({work.page_id for work in old_catalog}) == 400
    assert len({work.sha1 for work in old_catalog}) == 400
    assert len({(work.title.casefold(), work.artist.casefold()) for work in old_catalog}) == 400
    assert len({work.artist for work in old_catalog}) == 299
    assert (
        manifest["baseline_manifest_sha256"]
        == hashlib.sha256(baseline_path.read_bytes()).hexdigest()
    )
    assert baseline["proposal_count"] == 200
    assert len(baseline["deferred"]) == 34
    assert manifest["baseline_count"] == 166
    assert manifest["added_count"] == 234
    assert manifest["included_count"] == 400
    assert manifest["artist_label_count"] == 299
    assert manifest["criteria"] == {
        "minimum_source_width_px": 3000,
        "relative_16_9_tolerance": 0.025,
    }
    rows = manifest["included"]
    assert rows[:166] == baseline["included"]
    assert manifest["previously_deferred"] == baseline["deferred"]
    known_qids = [row["qid"] for row in rows[166:] if row["qid"]]
    assert len(known_qids) == len(set(known_qids))
    for row in rows[166:]:
        assert row["visual_review_date"] == "2026-10-06"
        assert row["source_revision"] > 0
        assert re.fullmatch("[0-9a-f]{64}", row["source_page_sha256"])
        assert row["rights_label_observed"] in {"Public domain", "CC0"}
        assert not row["physical_check"]["dimension_review"]
    assert [work.page_id for work in old_catalog] == [row["id"] for row in rows]
    assert {row["id"] for row in baseline["deferred"]}.isdisjoint(
        work.page_id for work in old_catalog
    )
    assert set(manifest["visually_reviewed_reserve_ids"]).isdisjoint(
        work.page_id for work in old_catalog
    )
    assert 98722784 not in {work.page_id for work in old_catalog}
    assert 3817033 in {work.page_id for work in old_catalog}
    for work, row in zip(old_catalog, rows, strict=True):
        assert (work.file_title, work.sha1, work.title, work.artist) == (
            row["file_title"],
            row["sha1"],
            row["title"],
            row["artist"],
        )
        assert row["width"] >= 3000
        assert abs(row["width"] * 9 - row["height"] * 16) * 40 <= row["height"] * 16
    assert (
        sum(
            abs(math.log((row["width"] / row["height"]) / (16 / 9))) <= math.log(1.01)
            for row in rows
        )
        == manifest["within_app_strict_ratio"]
        == 152
    )
    for work in old_catalog:
        assert work.page_id > 0
        assert work.file_title.startswith("File:")
        assert re.fullmatch("[0-9a-f]{40}", work.sha1)
        assert work.title
        assert work.artist


def test_1000_runtime_matches_approved_partition_without_rekeying_history() -> None:
    root = Path(__file__).resolve().parents[3]
    path = root / "research/commons-1000-selection-2026-10-10.json"
    manifest = json.loads(path.read_text())
    rows = manifest["included"]
    baseline_path = root / "research/commons-400-selection-2026-10-06.json"
    baseline = json.loads(baseline_path.read_text())["included"]
    assert (
        manifest["input_sha256"]["baseline"]
        == hashlib.sha256(baseline_path.read_bytes()).hexdigest()
    )
    assert len(CATALOG) == len(rows) == len({w.page_id for w in CATALOG}) == 1000
    assert len({w.sha1 for w in CATALOG}) == 1000
    assert len({(w.title.casefold(), w.artist.casefold()) for w in CATALOG}) == 1000
    held = set(manifest["held_ids"])
    reserves = {w["id"] for w in manifest["reserve"]}
    active = {w.page_id for w in CATALOG}
    assert len(held) == 56
    assert len(reserves) == 7
    assert active.isdisjoint(held | reserves)
    assert rows[:344] == [w for w in baseline if w["id"] not in held]
    assert {w["id"] for w in baseline} == {w["id"] for w in rows[:344]} | held
    assert manifest["added_count"] == 656
    for work, row in zip(CATALOG, rows, strict=True):
        assert (work.page_id, work.file_title, work.sha1, work.title, work.artist) == (
            row["id"],
            row["file_title"],
            row["sha1"],
            row["title"],
            row["artist"],
        )
        assert row["width"] >= 3000
        assert abs(row["width"] * 9 - row["height"] * 16) * 40 <= row["height"] * 16
        assert row["rights_label_observed"] in {"Public domain", "CC0"}


def test_identity_policy_caption_and_lazy_paced_batched_discovery() -> None:
    rig = Rig()
    assert rig.provider.key == "commons"
    cap = rig.provider.capabilities()
    assert cap.source is SourceKey.WIKIMEDIA_COMMONS
    assert cap.dims_in_metadata
    assert CAPABILITY_MATRIX[cap.source] == {FilterDimension.COLOR}
    assert commons_policy().hosts == {
        "commons.wikimedia.org",
        "upload.wikimedia.org",
        "thumb.wikimedia.org",
    }
    it = rig.provider.iter_candidates(filters(), rig.context())
    assert not rig.transport.calls
    first = next(it)
    assert len(rig.transport.calls) == 1
    assert first.dims == Size(3840, 2160)
    assert first.rights_basis is RightsBasis.PUBLIC_DOMAIN
    assert rig.provider.full_ref(first).kind is ImageRefKind.REMOTE
    assert "thumb.wikimedia.org" in rig.provider.full_ref(first).location
    assert json.loads(artwork_info(first))["museum"] == "Wikimedia Commons"
    found = [first, *it]
    assert len(found) == 12
    assert len({c.qualified_id for c in found}) == 12
    assert len(rig.site.queries) == 3
    assert rig.clock.monotonic() >= 2
    assert sorted(int(v) for q in rig.site.queries for v in q["pageids"].split("|")) == list(
        range(1, 13)
    )
    for q in rig.site.queries:
        assert 1 <= len(q["pageids"].split("|")) <= 5
        assert q["iiurlwidth"] == "3840"
        assert q["maxlag"] == "5"
        assert q["iilimit"] == "1"
        assert q["formatversion"] == "2"
        assert "extmetadata" in q["iiprop"]
        assert "sha1" in q["iiprop"]
    assert all("Authorization" not in call.request.headers for call in rig.transport.calls)
    assert all(
        call.request.headers["User-Agent"] == commons_identity().user_agent
        for call in rig.transport.calls
    )


def test_empty_catalog_and_foreign_filters_or_channel_and_unoffered_refs() -> None:
    rig = Rig()
    assert list(CommonsProvider(rig.channel, ()).iter_candidates(filters(), rig.context())) == []
    with pytest.raises(ValueError, match="another provider"):
        CommonsProvider(
            rig.gateway.channel(
                HostPolicy("aic", frozenset({"example.org"})),
                metadata_allowance=Allowance("other", 15),
            )
        )
    with pytest.raises(ValueError, match="another source"):
        list(
            rig.provider.iter_candidates(
                replace(filters(), source=SourceKey.LOCAL_MEDIA), rig.context()
            )
        )
    candidate = rig.run()[0]
    for stranger in (replace(candidate, provider_key="aic"), replace(candidate, native_id="999")):
        with pytest.raises(ValueError, match="not offered"):
            rig.provider.full_ref(stranger)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("LicenseShortName", "CC BY-SA"),
        ("LicenseShortName", []),
        ("LicenseShortName", None),
        ("Copyrighted", "True"),
        ("Copyrighted", None),
        ("AttributionRequired", "true"),
        ("AttributionRequired", None),
        ("Restrictions", "personality rights"),
    ],
)
def test_rights_fail_closed(field: str, value: object) -> None:
    rig = Rig()
    for row in rig.site.records.values():
        assert isinstance(row, dict)
        cast("dict[str, Any]", row)["imageinfo"][0]["extmetadata"][field] = {"value": value}
    assert rig.run() == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("extmetadata", None),
        ("extmetadata", {"bad": []}),
        ("sha1", "changed"),
        ("mime", "image/png"),
        ("width", None),
        ("height", None),
        ("thumbwidth", None),
        ("thumbheight", None),
        ("thumbwidth", 3841),
        ("thumbheight", 3841),
        ("thumbmime", "image/png"),
        ("thumburl", None),
        ("thumburl", "http://thumb.wikimedia.org/wikipedia/commons/test.jpg"),
        ("thumburl", "https://example.org/wikipedia/commons/test.jpg"),
        ("thumburl", "https://commons.wikimedia.org/wikipedia/commons/test.jpg"),
        ("thumburl", "https://thumb.wikimedia.org/other/test.jpg"),
    ],
)
def test_changed_upload_and_invalid_or_unsafe_renditions_are_skipped(
    field: str, value: object
) -> None:
    rig = Rig()
    for row in rig.site.records.values():
        assert isinstance(row, dict)
        cast("dict[str, Any]", row)["imageinfo"][0][field] = value
    assert rig.run() == []


@pytest.mark.parametrize(
    "patch",
    [
        {"ns": 0},
        {"title": "File:Different.jpg"},
        {"imagerepository": "shared"},
        {"imageinfo": []},
        {"imageinfo": None},
        {"imageinfo": [None]},
    ],
)
def test_missing_renamed_or_malformed_files_are_skipped(patch: dict[str, object]) -> None:
    rig = Rig()
    for row in rig.site.records.values():
        assert isinstance(row, dict)
        row.update(patch)
    assert rig.run() == []


def test_original_when_small_cc0_and_plain_false_labels() -> None:
    rig = Rig()
    for row in rig.site.records.values():
        assert isinstance(row, dict)
        info = cast("dict[str, Any]", row)["imageinfo"][0]
        info.update(width=3000, height=2000)
        info["extmetadata"]["LicenseShortName"]["value"] = "CC0"
        info["extmetadata"]["Copyrighted"]["value"] = "True"
        info["extmetadata"]["LicenseUrl"] = {
            "value": "http://creativecommons.org/publicdomain/zero/1.0/deed.en"
        }
    found = rig.run()
    assert len(found) == 12
    assert all(c.rights_basis is RightsBasis.CC0 and c.dims == Size(3000, 2000) for c in found)
    assert all("upload.wikimedia.org" in rig.provider.full_ref(c).location for c in found)
    row = rig.site.records[1]
    assert isinstance(row, dict)
    cast("dict[str, Any]", row)["imageinfo"][0]["height"] = 3841
    assert len(rig.run()) == 11


@pytest.mark.parametrize(
    "url",
    [
        None,
        [],
        "https://example.org/publicdomain/zero/1.0/",
        "https://creativecommons.org/licenses/by/4.0/",
    ],
)
def test_cc0_without_canonical_dedication_url_is_skipped(url: object) -> None:
    rig = Rig()
    for row in rig.site.records.values():
        info = cast("dict[str, Any]", row)["imageinfo"][0]
        info["extmetadata"]["LicenseShortName"]["value"] = "CC0"
        info["extmetadata"]["LicenseUrl"] = {"value": url}
    assert rig.run() == []


@pytest.mark.parametrize(
    "document",
    [
        None,
        {},
        {"error": {"info": "secret/untrusted"}},
        {"warnings": {}},
        {"query": {}},
        {"query": {"pages": {}}},
    ],
)
def test_invalid_envelopes_stop_with_safe_source_error(document: object) -> None:
    rig = Rig()
    rig.transport.add(json_response(document))
    with pytest.raises(SourceError) as exc:
        rig.run()
    assert exc.value.kind is SourceErrorKind.UNEXPECTED_FORMAT
    assert "secret/untrusted" not in str(exc.value)
    assert len(rig.transport.calls) == 1


def test_unrequested_duplicate_and_non_records_cannot_offer_extra_works() -> None:
    rig = Rig()
    first = record(TEST_CATALOG[0])
    rig.transport.add(
        json_response({"query": {"pages": [None, {}, {"pageid": 999}, first, first]}})
    )
    ctx = rig.context()
    # With the same deterministic order, make the first batch only work 1.
    rig.provider = CommonsProvider(rig.channel, TEST_CATALOG[:1])
    found = list(rig.provider.iter_candidates(filters(), ctx))
    assert [c.native_id for c in found] == ["1"]


def test_allowance_expiry_and_http_stop_are_not_retried_forever() -> None:
    rig = Rig(allowance=1)
    with pytest.raises(AllowanceExhausted):
        rig.run()
    assert len(rig.transport.calls) == 1
    rig = Rig()
    ctx = rig.context()
    rig.clock.advance(31)
    with pytest.raises(DeadlineExceeded):
        list(rig.provider.iter_candidates(filters(), ctx))
    assert not rig.transport.calls
    rig = Rig()
    rig.transport.add(status_response(403))
    for _ in range(2):
        with pytest.raises(SourceError) as exc:
            rig.run()
        assert exc.value.kind is SourceErrorKind.STOPPED
    assert len(rig.transport.calls) == 1


def test_all_sent_ends_without_requests_but_uncertainty_still_reaches_selection() -> None:
    rig = Rig()
    ctx = replace(rig.context(), is_excluded_for_good=lambda _key: True)
    assert list(rig.provider.iter_candidates(filters(), ctx)) == []
    assert ctx.notes.pages_skipped == 3
    assert not rig.transport.calls
    assert len(rig.run()) == 12


def test_catalog_is_shuffled_reproducibly_without_repeats() -> None:
    left, right = Rig(), Rig()
    assert [c.native_id for c in left.run()] == [c.native_id for c in right.run()]
    other = list(right.provider.iter_candidates(filters(), right.context(12)))
    assert [c.native_id for c in other] != [c.native_id for c in left.run()]


def large_catalog(rig: Rig, count: int) -> None:
    catalog = tuple(
        replace(TEST_CATALOG[0], page_id=n, file_title=f"File:Synthetic {n}.jpg", sha1=f"{n:040x}")
        for n in range(1, count + 1)
    )
    rig.provider = CommonsProvider(rig.channel, catalog)
    rig.site.records = {work.page_id: record(work) for work in catalog}


@pytest.mark.parametrize("count", [200, 400, 1000])
def test_large_catalog_has_ten_request_cap_not_an_unbounded_full_scan(count: int) -> None:
    rig = Rig()
    large_catalog(rig, count)
    started = rig.clock.monotonic()
    found = rig.run()
    assert len(found) == len({candidate.native_id for candidate in found}) == 50
    assert len(rig.site.queries) == 10
    assert rig.clock.monotonic() - started < 30


@pytest.mark.parametrize("count", [200, 400, 1000])
def test_large_catalog_last_unsent_work_is_found_without_requerying_sent_works(count: int) -> None:
    rig = Rig()
    large_catalog(rig, count)
    ctx = replace(rig.context(), is_excluded_for_good=lambda key: key != f"commons:{count}")
    found = list(rig.provider.iter_candidates(filters(), ctx))
    assert [candidate.qualified_id for candidate in found] == [f"commons:{count}"]
    assert [query["pageids"] for query in rig.site.queries] == [str(count)]
    assert ctx.notes.pages_skipped == count // 5 - 1


@pytest.mark.parametrize("count", [200, 400, 1000])
def test_large_catalog_exhaustion_is_request_free_and_does_not_recycle(count: int) -> None:
    rig = Rig()
    large_catalog(rig, count)
    ctx = replace(rig.context(), is_excluded_for_good=lambda _key: True)
    assert list(rig.provider.iter_candidates(filters(), ctx)) == []
    assert ctx.notes.pages_skipped == count // 5
    assert not rig.transport.calls


@pytest.mark.parametrize("count", [200, 400, 1000])
def test_large_catalog_rejected_rights_stops_at_the_same_request_limit(count: int) -> None:
    rig = Rig()
    large_catalog(rig, count)
    for row in rig.site.records.values():
        cast("dict[str, Any]", row)["imageinfo"][0]["extmetadata"]["Copyrighted"]["value"] = "True"
    assert rig.run() == []
    assert len(rig.site.queries) == 10
