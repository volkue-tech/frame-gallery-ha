"""Pinned offline families, no extra downloads, and bounded colour preselection."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import MappingProxyType

import pytest

from frame_gallery.config.filters import FilterField
from frame_gallery.config.vocabulary import BUILTIN_VOCABULARY
from frame_gallery.providers import commons_colours
from frame_gallery.providers.commons_catalog import CATALOG
from frame_gallery.providers.commons_colours import COLOUR_PROFILES, matches_colour
from tests.support.commons import TEST_CATALOG
from tests.unit.providers.test_commons import Rig, filters


def test_compact_profiles_match_full_1000_research_and_active_pins() -> None:
    root = Path(__file__).resolve().parents[3]
    document = json.loads((root / "research/commons-1000-colours-2026-10-10.json").read_text())
    research = {p["id"]: p for p in document["profiles"]}
    assert len(research) == len(COLOUR_PROFILES) == len(CATALOG) == 1000
    offered = {e.key for e in BUILTIN_VOCABULARY.entries_for(FilterField.COLOR)}
    for work in CATALOG:
        pin, colours = COLOUR_PROFILES[work.page_id]
        full = research[work.page_id]
        assert pin == work.sha1 == full["original_sha1"]
        assert colours == {"color_" + name for name in full["search_colours"]}
        assert colours <= offered
        assert sum(p["pixels"] for p in full["distribution"]) == full["sample_pixels"]
        assert len(full["top_colours"]) <= 3
    assert all(any(key in value[1] for value in COLOUR_PROFILES.values()) for key in offered)
    with pytest.raises(TypeError):
        COLOUR_PROFILES[1] = ("bad", frozenset())  # type: ignore[index]


def test_missing_unknown_and_changed_pin_never_match() -> None:
    work = CATALOG[0]
    key = next(iter(COLOUR_PROFILES[work.page_id][1]))
    assert matches_colour(work, key)
    assert not matches_colour(work, "color_unknown")
    assert not matches_colour(replace(work, sha1="f" * 40), key)
    assert not matches_colour(replace(work, page_id=1), key)


def _profiles(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        commons_colours,
        "COLOUR_PROFILES",
        MappingProxyType(
            {
                work.page_id: (
                    work.sha1,
                    frozenset({"color_blue" if work.page_id <= 3 else "color_yellow"}),
                )
                for work in TEST_CATALOG
            }
        ),
    )


def test_colour_prefilter_never_requests_other_colour_or_extra_renditions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _profiles(monkeypatch)
    rig = Rig()
    chosen = list(
        rig.provider.iter_candidates(replace(filters(), color="color_blue"), rig.context())
    )
    assert {c.native_id for c in chosen} == {"1", "2", "3"}
    assert len(rig.site.queries) == 1
    assert set(rig.site.queries[0]["pageids"].split("|")) == {"1", "2", "3"}
    assert all(
        call.request.host == "commons.wikimedia.org"
        and call.request.target.startswith("/w/api.php?")
        for call in rig.transport.calls
    )


def test_empty_or_entirely_sent_colour_does_not_touch_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _profiles(monkeypatch)
    rig = Rig()
    assert (
        list(rig.provider.iter_candidates(replace(filters(), color="color_red"), rig.context()))
        == []
    )
    assert not rig.transport.calls
    context = replace(rig.context(), is_excluded_for_good=lambda _: True)
    assert list(rig.provider.iter_candidates(replace(filters(), color="color_blue"), context)) == []
    assert not rig.transport.calls


def test_partial_history_exclusion_stays_inside_colour(monkeypatch: pytest.MonkeyPatch) -> None:
    _profiles(monkeypatch)
    rig = Rig()
    context = replace(rig.context(), is_excluded_for_good=lambda qid: qid == "commons:2")
    chosen = list(rig.provider.iter_candidates(replace(filters(), color="color_blue"), context))
    assert {c.native_id for c in chosen} == {"1", "3"}
    assert set(rig.site.queries[0]["pageids"].split("|")) == {"1", "3"}
