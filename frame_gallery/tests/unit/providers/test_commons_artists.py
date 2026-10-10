"""Artist/colour intersection is bounded and never relaxed by shape fallback."""

from __future__ import annotations

from dataclasses import replace

import pytest

from frame_gallery.providers.commons import CommonsProvider
from tests.support.commons import TEST_CATALOG
from tests.unit.providers.test_commons import Rig, filters
from tests.unit.providers.test_commons_colours import _profiles


def rig_with_artists() -> Rig:
    rig = Rig()
    catalogue = tuple(
        replace(work, artist="First Test Artist" if work.page_id % 2 else "Second Test Artist")
        for work in TEST_CATALOG
    )
    rig.provider = CommonsProvider(rig.channel, catalogue)
    return rig


def test_artist_prefilter_limits_metadata_to_selected_artist() -> None:
    rig = rig_with_artists()
    result = list(
        rig.provider.iter_candidates(
            replace(filters(), artist="artist_first_test_artist"), rig.context()
        )
    )
    assert {c.native_id for c in result} == {"1", "3", "5", "7", "9", "11"}
    assert len(rig.site.queries) == 2
    assert all(int(i) % 2 for query in rig.site.queries for i in query["pageids"].split("|"))


def test_colour_and_artist_are_an_intersection_not_a_union(monkeypatch: pytest.MonkeyPatch) -> None:
    _profiles(monkeypatch)
    rig = rig_with_artists()
    result = list(
        rig.provider.iter_candidates(
            replace(filters(), artist="artist_first_test_artist", color="color_blue"), rig.context()
        )
    )
    assert {c.native_id for c in result} == {"1", "3"}
    assert len(rig.site.queries) == 1
    assert set(rig.site.queries[0]["pageids"].split("|")) == {"1", "3"}


@pytest.mark.parametrize("artist", ["artist_no_match", "artist_first_test_artist"])
def test_empty_or_fully_sent_selection_never_calls_network(artist: str) -> None:
    rig = rig_with_artists()
    context = replace(rig.context(), is_excluded_for_good=lambda _: True)
    assert list(rig.provider.iter_candidates(replace(filters(), artist=artist), context)) == []
    assert not rig.transport.calls


def test_sent_work_does_not_relax_artist_or_recycle_an_upload() -> None:
    rig = rig_with_artists()
    context = replace(
        rig.context(), is_excluded_for_good=lambda qid: qid in {"commons:1", "commons:3"}
    )
    result = list(
        rig.provider.iter_candidates(replace(filters(), artist="artist_first_test_artist"), context)
    )
    assert {c.native_id for c in result} == {"5", "7", "9", "11"}
    assert all(
        int(i) % 2 and i not in {"1", "3"}
        for query in rig.site.queries
        for i in query["pageids"].split("|")
    )
