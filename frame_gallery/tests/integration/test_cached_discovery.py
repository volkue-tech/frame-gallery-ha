"""The persistent metadata cache across runs (§9.5, §13.4, F6, R-13).

The real Art Institute adapter and gateway run over the synthesized API; the
state store and the metadata cache are the real files of one data directory.
Each run builds everything afresh, as a new process would.
"""

from __future__ import annotations

import json
from pathlib import Path

from frame_gallery.app.fetching import SourceFetcher
from frame_gallery.app.outcomes import Hint, Outcome
from frame_gallery.app.ports import ProviderBinding
from frame_gallery.app.runner import RunResult
from frame_gallery.budget.allowance import Allowance
from frame_gallery.domain import SourceKey
from frame_gallery.net.gateway import Gateway
from frame_gallery.net.wire import WireRequest
from frame_gallery.providers.aic import AicProvider, aic_policy
from frame_gallery.randomness import SeededRandomSource
from tests.support.fakes import canvas_jpeg_bytes
from tests.support.museums import AicMuseum, ParsedRequest
from tests.support.net import (
    TEST_IDENTITY,
    FakeResolver,
    FakeResponse,
    FakeTransport,
    image_response,
)
from tests.support.persistent import PersistentRig


class CachedRuns:
    def __init__(self, root: Path) -> None:
        self.rig = PersistentRig(root)
        self.museum = AicMuseum()
        self.museum.add(2)

    def run(self, day: float) -> tuple[RunResult, list[ParsedRequest]]:
        h = self.rig.harness(days=day)

        def route(request: WireRequest) -> FakeResponse:
            if request.host == "www.artic.edu":
                return image_response(canvas_jpeg_bytes())
            return self.museum(request)

        gateway = Gateway(
            resolver=FakeResolver(),
            transport=FakeTransport(clock=h.clock, handler=route),
            clock=h.clock,
            random=SeededRandomSource(int(day * 10)),
            identity=TEST_IDENTITY,
        )
        channel = gateway.channel(aic_policy(TEST_IDENTITY), metadata_allowance=Allowance("m", 15))
        cache = self.rig.layout.metadata_cache("aic", h.clock)
        h.bindings = {
            SourceKey.ART_INSTITUTE_CHICAGO: ProviderBinding(
                AicProvider(channel, cache), cache=cache
            )
        }
        h.image_fetcher = SourceFetcher(channels=[channel])
        self.museum.seen.clear()
        result = h.run()
        return result, [r for r in self.museum.seen if r.path == "/api/v1/artworks/search"]

    def cache_keys(self) -> list[str]:
        loaded = json.loads((self.rig.layout.data / "cache" / "aic.json").read_text())
        return [entry["key"] for entry in loaded["entries"]]

    def pages_skipped(self) -> object:
        selection = json.loads((self.rig.state / "last_run.json").read_text())["stats"]
        return selection["selection"]["pages_skipped"]


def test_counts_and_exhausted_pages_carry_over_between_runs(tmp_path: Path) -> None:
    runs = CachedRuns(tmp_path / "rig")

    first, searches = runs.run(0)
    assert first.delivered_id == "aic:1"
    assert [s.params["limit"] for s in searches] == [0, 50]  # the count, then the page

    second, searches = runs.run(0.5)
    assert second.delivered_id == "aic:2"
    assert [s.params["limit"] for s in searches] == [50]  # the count came from the cache

    third, searches = runs.run(1.5)
    assert third.outcome is Outcome.NO_MATCH
    assert third.hint == Hint.NOTHING_NEW
    assert len(searches) == 2  # the count expired after a day; the page offered nothing new
    assert "aic:exhausted:any" in runs.cache_keys()

    fourth, searches = runs.run(1.6)
    assert fourth.outcome is Outcome.NO_MATCH
    assert fourth.hint == Hint.NOTHING_NEW
    assert searches == []  # the page is known to be exhausted: nothing is fetched
    assert runs.pages_skipped() == 1
