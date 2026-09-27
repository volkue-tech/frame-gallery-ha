"""Acceptance items B1, B2, B5, B6, B7, and B8 at the configuration layer.

Each test names its acceptance item in its docstring. B3 and B4 (helper
overrides and fallbacks) are covered in ``test_overrides.py``; the helper
client that reads the states arrives in Phase 3.
"""

from __future__ import annotations

from collections.abc import Mapping
from ipaddress import IPv4Address, IPv4Network

import pytest

from frame_gallery.config.capabilities import resolve_effective_filters
from frame_gallery.config.filters import (
    FilterChoice,
    FilterDimension,
    FilterField,
    IgnoreReason,
    Provenance,
)
from frame_gallery.config.options import ConfigError, Options, parse_options
from frame_gallery.config.overrides import apply_helper_values
from frame_gallery.domain import BLACK, FitMode, SourceKey
from tests.unit.config.synthetic import (
    AIC_DEPARTMENT,
    CMA_DEPARTMENT,
    COLOR,
    PERIOD,
    STYLE,
    VOCABULARY,
)

TV = "10.0.0.5"
CONTAINER = (IPv4Network("172.30.32.0/23"),)


def _parse(raw: Mapping[str, object]) -> Options:
    return parse_options(raw, vocabulary=VOCABULARY, excluded_networks=CONTAINER)


def _rejected(raw: Mapping[str, object]) -> ConfigError:
    with pytest.raises(ConfigError) as caught:
        _parse(raw)
    return caught.value


def test_b1_missing_tv_address_prevents_start() -> None:
    """B1: a missing television IP prevents start with a clear validation message."""
    error = _rejected({"source": "art_institute_chicago"})
    assert [issue.option for issue in error.issues] == ["tv_host"]
    assert error.issues[0].message.startswith("The television IP address is required.")
    assert "tv_host: The television IP address is required." in str(error)


def test_b2_static_filters_work_without_helpers() -> None:
    """B2: static source, department, style/period, and colour filters work
    without helper entities, as four distinct dimensions, wherever the
    selected source supports them (§9.2 as amended by D-146); the others are
    reported, never silently dropped (B8)."""
    options = _parse(
        {
            "tv_host": TV,
            "source": "art_institute_chicago",
            "department": AIC_DEPARTMENT,
            "style": STYLE,
            "color": COLOR,
        }
    )
    assert options.helpers == ()
    merge = apply_helper_values(options.filters, {}, VOCABULARY)
    assert merge.filters == options.filters
    assert merge.warnings == ()
    effective = resolve_effective_filters(merge.filters, VOCABULARY)
    assert effective.active() == {}
    assert [ignored.dimension for ignored in effective.ignored] == [
        FilterDimension.DEPARTMENT,
        FilterDimension.STYLE,
        FilterDimension.COLOR,
    ]
    period = _parse({"tv_host": TV, "source": "art_institute_chicago", "style": PERIOD})
    effective = resolve_effective_filters(period.filters, VOCABULARY)
    assert effective.active() == {FilterDimension.PERIOD: PERIOD}

    cma = _parse(
        {
            "tv_host": TV,
            "source": "cleveland_museum_of_art",
            "department": CMA_DEPARTMENT,
            "style": PERIOD,
        }
    )
    effective = resolve_effective_filters(cma.filters, VOCABULARY)
    assert effective.active() == {
        FilterDimension.DEPARTMENT: CMA_DEPARTMENT,
        FilterDimension.PERIOD: PERIOD,
    }


def test_b5_invalid_static_values_are_rejected() -> None:
    """B5: invalid static filter values are rejected with a message per option."""
    error = _rejected(
        {"tv_host": TV, "department": "aic_missing", "style": "no such style", "color": 3}
    )
    assert [issue.option for issue in error.issues] == ["department", "style", "color"]


def test_b5_values_are_normalized_predictably() -> None:
    """B5: case, spacing, separators, and diacritics normalize to the same key,
    for static options and helper values alike."""
    for spelling in ("Test Paintings", "  TEST-PAINTINGS ", "test_paintings", "Tëst Pâintings"):
        options = _parse({"tv_host": TV, "department": spelling})
        assert options.filters.department == FilterChoice(AIC_DEPARTMENT, Provenance.STATIC)
        merge = apply_helper_values(options.filters, {FilterField.DEPARTMENT: spelling}, VOCABULARY)
        assert merge.filters.department == FilterChoice(AIC_DEPARTMENT, Provenance.HELPER)


def test_b5_invalid_helper_value_falls_back_with_one_warning() -> None:
    """B5: an invalid helper value falls back to the static value, with one warning."""
    options = _parse({"tv_host": TV, "department": AIC_DEPARTMENT})
    merge = apply_helper_values(
        options.filters, {FilterField.DEPARTMENT: "not a department"}, VOCABULARY
    )
    assert merge.filters == options.filters
    assert len(merge.warnings) == 1
    assert "not a department" not in merge.warnings[0]


def test_b6_defaults_preserve_the_full_artwork() -> None:
    """B6: landscape-only and fit-mode defaults preserve the full artwork
    (contain, no crop), with strict near-16:9 on and a black background."""
    options = _parse({"tv_host": TV})
    assert options.landscape_only is True
    assert options.strict_tv_format is True
    assert options.fit_mode is FitMode.CONTAIN
    assert options.background == BLACK
    assert options.filters.source is SourceKey.ART_INSTITUTE_CHICAGO


@pytest.mark.parametrize(
    ("value", "phrase"),
    [
        ("169.254.10.20", "link-local"),
        ("127.0.0.1", "loopback"),
        ("0.0.0.0", "unspecified"),  # noqa: S104
        ("239.1.2.3", "multicast"),
        ("255.255.255.255", "broadcast"),
        ("100.64.0.1", "private (RFC 1918)"),
        ("172.30.32.10", "container network"),
        ("frame.local", "IPv4 address"),
        ("fd00::5", "IPv4 address"),
    ],
)
def test_b7_non_private_tv_address_is_rejected(value: str, phrase: str) -> None:
    """B7: an address that is not an RFC 1918 private IPv4 literal, or that lies
    in the container or Supervisor network, is rejected with a clear message."""
    error = _rejected({"tv_host": value})
    assert [issue.option for issue in error.issues] == ["tv_host"]
    assert phrase in error.issues[0].message


def test_b7_private_tv_address_is_accepted() -> None:
    """B7: an RFC 1918 literal outside the container networks is accepted."""
    for value in ("10.0.0.5", "172.16.4.2", "192.168.1.20"):
        assert _parse({"tv_host": value}).tv_host == IPv4Address(value)


def test_b8_unsupported_static_filters_are_reported() -> None:
    """B8: a static filter the source does not support is ignored visibly,
    with its reason, and never claimed to apply."""
    options = _parse(
        {
            "tv_host": TV,
            "source": "cleveland_museum_of_art",
            "department": AIC_DEPARTMENT,
            "style": STYLE,
            "color": COLOR,
        }
    )
    effective = resolve_effective_filters(options.filters, VOCABULARY)
    assert effective.active() == {}
    assert [ignored.describe() for ignored in effective.ignored] == [
        "department=aic_test_paintings(other_source)",
        "style=style_test_one(unsupported_by_source)",
        "color=color_test_blue(unsupported_by_source)",
    ]
    assert {ignored.provenance for ignored in effective.ignored} == {Provenance.STATIC}


def test_b8_unsupported_helper_filters_are_reported_like_static_ones() -> None:
    """B8: a known helper key that does not apply to the (helper-selected)
    source overrides the static value and is then reported as ignored."""
    options = _parse({"tv_host": TV, "department": AIC_DEPARTMENT})
    merge = apply_helper_values(
        options.filters,
        {FilterField.SOURCE: "local_media", FilterField.COLOR: "Test Blue"},
        VOCABULARY,
    )
    assert merge.warnings == ()
    effective = resolve_effective_filters(merge.filters, VOCABULARY)
    assert effective.source is SourceKey.LOCAL_MEDIA
    assert [(i.field, i.reason, i.provenance) for i in effective.ignored] == [
        (FilterField.DEPARTMENT, IgnoreReason.UNSUPPORTED_BY_SOURCE, Provenance.STATIC),
        (FilterField.COLOR, IgnoreReason.UNSUPPORTED_BY_SOURCE, Provenance.HELPER),
    ]
