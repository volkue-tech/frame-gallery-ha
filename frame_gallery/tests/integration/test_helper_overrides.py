"""Helper overrides end to end: the real Supervisor helper reader, behind a
scripted transport, feeding the runner (§15.3, D-112; B3, B4, B5, B8)."""

from __future__ import annotations

import json
import logging
from ipaddress import IPv4Network, ip_address
from pathlib import Path

import pytest

from frame_gallery.app.outcomes import Outcome
from frame_gallery.config.filters import FilterField
from frame_gallery.domain import SourceKey
from frame_gallery.ha.client import SupervisorHelperReader
from tests.support.fakes import make_candidate
from tests.support.net import FakeResolver, FakeResponse, FakeTransport
from tests.unit.app.harness import SYNTHETIC_VOCABULARY, Harness

TOKEN = "fake-supervisor-token-abcdef"  # noqa: S105 - a synthetic test value


def _state(value: str) -> FakeResponse:
    body = json.dumps({"entity_id": "input_select.x", "state": value}).encode()
    return FakeResponse(headers={"Content-Type": "application/json"}, body=body)


def _harness(tmp_path: Path, raw: dict[str, object], *states: FakeResponse) -> Harness:
    transport = FakeTransport(states)
    reader = SupervisorHelperReader(
        token=TOKEN,
        resolver=FakeResolver(default=(ip_address("172.30.32.2"),)),
        transport=transport,
        networks=(IPv4Network("172.30.32.0/23"),),
    )
    harness = Harness(
        tmp_path,
        raw={"tv_host": "10.0.0.5", **raw},
        vocabulary=SYNTHETIC_VOCABULARY,
        helper_reader=reader,
    )
    harness.cma_provider.candidates = [make_candidate("2001", provider_key="cma")]
    return harness


def test_b3_a_valid_helper_value_overrides_the_static_value(tmp_path: Path) -> None:
    h = _harness(
        tmp_path,
        {
            "source": "cleveland_museum_of_art",
            "department": "aic_test_paintings",
            "department_helper": "input_select.fg_department",
        },
        _state("Test Prints"),
    )
    result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert h.cma_provider.filters[0].department == "cma_test_prints"
    assert h.last_run["filters"]["provenance"]["department"] == "helper"  # type: ignore[index]


@pytest.mark.parametrize("state", ["unavailable", "unknown"])
def test_b4_an_unavailable_helper_falls_back(
    tmp_path: Path, state: str, caplog: pytest.LogCaptureFixture
) -> None:
    h = _harness(
        tmp_path,
        {
            "source": "cleveland_museum_of_art",
            "department": "cma_test_prints",
            "department_helper": "input_select.fg_department",
        },
        _state(state),
    )
    with caplog.at_level(logging.WARNING):
        result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert h.cma_provider.filters[0].department == "cma_test_prints"
    assert "department_helper is unavailable" in caplog.text


def test_b4_an_unreachable_supervisor_falls_back(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    h = _harness(
        tmp_path,
        {
            "source": "cleveland_museum_of_art",
            "department": "cma_test_prints",
            "department_helper": "input_select.fg_department",
        },
        FakeResponse(status=502),
    )
    with caplog.at_level(logging.WARNING):
        h.run()
    assert h.cma_provider.filters[0].department == "cma_test_prints"
    assert "department_helper could not be read" in caplog.text
    assert TOKEN not in caplog.text


def test_b5_an_invalid_helper_value_falls_back(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    h = _harness(
        tmp_path,
        {"style_helper": "input_text.fg_style"},
        _state("no such style"),
    )
    with caplog.at_level(logging.WARNING):
        h.run()
    assert h.provider.filters[0].style is None
    assert "style_helper matches no key" in caplog.text


def test_the_source_helper_switches_the_source(tmp_path: Path) -> None:
    h = _harness(
        tmp_path,
        {"source_helper": "input_select.fg_source"},
        _state("cleveland_museum_of_art"),
    )
    h.run()
    assert h.cma_provider.filters[0].source is SourceKey.CLEVELAND_MUSEUM_OF_ART
    assert h.provider.filters == []


def test_all_four_helpers_take_four_reads(tmp_path: Path) -> None:
    h = _harness(
        tmp_path,
        {
            "source_helper": "input_select.a",
            "department_helper": "input_select.b",
            "style_helper": "input_text.c",
            "color_helper": "select.d",
        },
        _state("art_institute_chicago"),
        _state("any"),
        _state("any"),
        _state("any"),
    )
    reader = h.helper_reader
    assert isinstance(reader, SupervisorHelperReader)
    h.run()
    transport = reader._transport
    assert isinstance(transport, FakeTransport)
    assert len(transport.calls) == 4
    assert [call.request.target.rsplit("/", 1)[1] for call in transport.calls] == [
        "input_select.a",
        "input_select.b",
        "input_text.c",
        "select.d",
    ]
    assert set(FilterField) == {
        FilterField.SOURCE,
        FilterField.DEPARTMENT,
        FilterField.STYLE,
        FilterField.COLOR,
    }
