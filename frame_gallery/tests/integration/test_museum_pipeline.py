"""The whole run with the real museum adapters, the real gateway, and the
real fetcher over synthesized APIs; the worker and the television are fakes
(C1, C9, C10, B8). Nothing here touches the network (H2)."""

from __future__ import annotations

from pathlib import Path

from frame_gallery.app.fetching import SourceFetcher
from frame_gallery.app.outcomes import Outcome
from frame_gallery.app.ports import ProviderBinding
from frame_gallery.budget.allowance import Allowance
from frame_gallery.domain import SourceKey
from frame_gallery.net.gateway import Gateway
from frame_gallery.net.wire import WireRequest
from frame_gallery.providers.aic import AicProvider, aic_policy
from frame_gallery.providers.cache import MemoryMetadataCache
from frame_gallery.providers.cma import CmaProvider, cma_policy
from frame_gallery.randomness import SeededRandomSource
from tests.support.fakes import canvas_jpeg_bytes
from tests.support.museums import AicMuseum, CmaMuseum, aic_image_id, aic_record, cma_record
from tests.support.net import (
    PLACEHOLDER_CONTACT,
    TEST_IDENTITY,
    FakeResolver,
    FakeResponse,
    FakeTransport,
    image_response,
)
from tests.unit.app.harness import Harness

IMAGE = canvas_jpeg_bytes()


def _harness(
    tmp_path: Path, raw: dict[str, object], museum: AicMuseum | CmaMuseum
) -> tuple[Harness, FakeTransport]:
    def route(request: WireRequest) -> FakeResponse:
        if request.host in ("www.artic.edu", "openaccess-cdn.clevelandart.org"):
            return image_response(IMAGE)
        return museum(request)

    h = Harness(tmp_path, raw={"tv_host": "10.0.0.5", **raw})
    transport = FakeTransport(clock=h.clock, handler=route)
    gateway = Gateway(
        resolver=FakeResolver(),
        transport=transport,
        clock=h.clock,
        random=SeededRandomSource(3),
        identity=TEST_IDENTITY,
    )
    aic = gateway.channel(aic_policy(TEST_IDENTITY), metadata_allowance=Allowance("m", 15))
    cma = gateway.channel(cma_policy(), metadata_allowance=Allowance("m", 15))
    cache = MemoryMetadataCache(h.clock)
    h.bindings = {
        SourceKey.ART_INSTITUTE_CHICAGO: ProviderBinding(AicProvider(aic, cache)),
        SourceKey.CLEVELAND_MUSEUM_OF_ART: ProviderBinding(CmaProvider(cma, cache)),
    }
    h.image_fetcher = SourceFetcher(channels=[aic, cma])
    return h, transport


def test_cleveland_combined_filters_deliver_a_cc0_print(tmp_path: Path) -> None:
    museum = CmaMuseum()
    museum.records = [
        cma_record(1, department="Prints", earliest=1850, width="3400", height="3400"),
        cma_record(2, department="Drawings", earliest=1850, width="3400", height="1913"),
        cma_record(3, department="Prints", earliest=1750, width="3400", height="1913"),
        cma_record(
            4, department="Prints", earliest=1860, width="3400", height="1913", status="Other"
        ),
        cma_record(5, department="Prints", earliest=1870, width="3400", height="1913"),
    ]
    h, transport = _harness(
        tmp_path,
        {"source": "cleveland_museum_of_art", "department": "Prints", "style": "19th century"},
        museum,
    )
    result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert result.delivered_id == "cma:5"
    image_requests = [
        c.request for c in transport.calls if c.request.host == "openaccess-cdn.clevelandart.org"
    ]
    assert [r.target for r in image_requests] == ["/1999.5/1999.5_print.jpg"]
    api = [
        c.request.target
        for c in transport.calls
        if c.request.host == "openaccess-api.clevelandart.org"
    ]
    assert all(
        t.startswith(
            "/api/artworks/?cc0&has_image=1&department=Prints&created_after=1799&created_before=1900&"
        )
        for t in api
    )
    assert not [c for c in transport.calls if ".tif" in c.request.target]


def test_art_institute_period_filter_and_reported_unsupported_filters(tmp_path: Path) -> None:
    museum = AicMuseum()
    museum.records = [aic_record(n, date_start=1500 + n) for n in range(1, 30)]
    museum.sizes = {aic_image_id(n): (3000, 3000) for n in range(1, 30)}
    museum.sizes[aic_image_id(12)] = (3840, 2160)  # 1512: in the period, 16:9
    h, transport = _harness(
        tmp_path,
        {"source": "art_institute_chicago", "style": "1400 to 1599", "department": "Prints"},
        museum,
    )
    result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert result.delivered_id == "aic:12"
    assert "ignored_filters=department=cma_prints(unsupported_by_source)" in result.summary_line
    iiif = [c.request for c in transport.calls if c.request.host == "www.artic.edu"]
    assert [r.target for r in iiif] == [f"/iiif/2/{aic_image_id(12)}/full/1686,/0/default.jpg"]
    assert all(
        c.request.headers["AIC-User-Agent"].endswith(f"({PLACEHOLDER_CONTACT})")
        for c in transport.calls
    )
