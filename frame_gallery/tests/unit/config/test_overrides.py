"""Helper overrides (§9.2, §15.3, D-112; B3-B5, B8)."""

from __future__ import annotations

import pytest

from frame_gallery.config.capabilities import resolve_effective_filters
from frame_gallery.config.filters import (
    ANY,
    FilterChoice,
    FilterDimension,
    FilterField,
    FilterSet,
    IgnoredFilter,
    IgnoreReason,
    Provenance,
)
from frame_gallery.config.overrides import HelperMerge, apply_helper_values
from frame_gallery.config.vocabulary import BUILTIN_VOCABULARY
from frame_gallery.domain import SourceKey
from tests.unit.config.synthetic import (
    AIC_DEPARTMENT,
    AIC_OTHER_DEPARTMENT,
    CMA_DEPARTMENT,
    COLOR,
    OTHER_STYLE,
    PERIOD,
    STYLE,
    VOCABULARY,
)

AIC = SourceKey.ART_INSTITUTE_CHICAGO
CMA = SourceKey.CLEVELAND_MUSEUM_OF_ART
LOCAL = SourceKey.LOCAL_MEDIA

STATIC = FilterSet(
    AIC,
    department=FilterChoice(AIC_DEPARTMENT),
    style=FilterChoice(STYLE),
    color=FilterChoice(COLOR),
)

FILTER_FIELDS = (FilterField.DEPARTMENT, FilterField.STYLE, FilterField.COLOR)


def _merge(values: dict[FilterField, str | None], static: FilterSet = STATIC) -> HelperMerge:
    return apply_helper_values(static, values, VOCABULARY)


def test_no_helpers_keep_the_static_filters() -> None:
    merge = _merge({})
    assert merge.filters == STATIC
    assert merge.warnings == ()


# -- unreadable and unavailable helpers (B4) --------------------------------------------------


@pytest.mark.parametrize("field", list(FilterField))
def test_unreadable_helper_keeps_static_with_one_warning(field: FilterField) -> None:
    merge = _merge({field: None})
    assert merge.filters == STATIC
    assert merge.warnings == (f"{field.value}_helper could not be read; using the static value",)


@pytest.mark.parametrize("state", ["unavailable", "unknown", "Unavailable", " UNKNOWN "])
@pytest.mark.parametrize("field", list(FilterField))
def test_unavailable_helper_keeps_static_with_one_warning(field: FilterField, state: str) -> None:
    merge = _merge({field: state})
    assert merge.filters == STATIC
    assert merge.warnings == (
        f"{field.value}_helper is unavailable in Home Assistant; using the static value",
    )


# -- source_helper (B3, B5) -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "source"),
    [
        ("cleveland_museum_of_art", CMA),
        ("Cleveland Museum of Art", CMA),
        ("LOCAL-MEDIA", LOCAL),
        ("art_institute_chicago", AIC),
    ],
)
def test_source_helper_overrides_the_source(value: str, source: SourceKey) -> None:
    merge = _merge({FilterField.SOURCE: value})
    assert merge.filters.source is source
    assert merge.filters.source_provenance is Provenance.HELPER
    assert (merge.filters.department, merge.filters.style, merge.filters.color) == (
        STATIC.department,
        STATIC.style,
        STATIC.color,
    )
    assert merge.warnings == ()


@pytest.mark.parametrize(
    "value", ["aic", "Art Institute of Chicago", "any", "", "museum", "x" * 300]
)
def test_invalid_source_helper_keeps_static_with_one_warning(value: str) -> None:
    merge = _merge({FilterField.SOURCE: value})
    assert merge.filters == STATIC
    assert merge.filters.source_provenance is Provenance.STATIC
    assert merge.warnings == (
        (
            "source_helper does not name a source (art_institute_chicago, "
            "cleveland_museum_of_art, local_media, or wikimedia_commons); using the static value"
        ),
    )


# -- department, style, and color helpers (B3, B5) --------------------------------------------


@pytest.mark.parametrize(
    ("field", "value", "key"),
    [
        (FilterField.DEPARTMENT, AIC_OTHER_DEPARTMENT, AIC_OTHER_DEPARTMENT),
        (FilterField.DEPARTMENT, "Arts of Elsewhere (Test)", AIC_OTHER_DEPARTMENT),
        (FilterField.STYLE, "Tést Style Two", OTHER_STYLE),
        (FilterField.STYLE, "test nineteenth century", PERIOD),
        (FilterField.COLOR, "test azure", COLOR),
    ],
)
def test_valid_helper_value_overrides_static(field: FilterField, value: str, key: str) -> None:
    merge = _merge({field: value})
    assert merge.filters.choice(field) == FilterChoice(key, Provenance.HELPER)
    assert merge.filters.source is AIC
    assert merge.filters.source_provenance is Provenance.STATIC
    for other in FILTER_FIELDS:
        if other is not field:
            assert merge.filters.choice(other) == STATIC.choice(other)
    assert merge.warnings == ()


@pytest.mark.parametrize("value", ["any", "ALL", "random", "none", "", "  ", "-"])
@pytest.mark.parametrize("field", FILTER_FIELDS)
def test_no_filter_helper_value_clears_the_filter(field: FilterField, value: str) -> None:
    merge = _merge({field: value})
    assert merge.filters.choice(field) == FilterChoice(None, Provenance.HELPER)
    assert merge.warnings == ()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (FilterField.DEPARTMENT, "aic_test_missing"),
        (FilterField.DEPARTMENT, STYLE),
        (FilterField.STYLE, COLOR),
        (FilterField.STYLE, "private note: back door code 1234"),
        (FilterField.COLOR, "日本"),
        (FilterField.COLOR, "x" * 300),
    ],
)
def test_invalid_helper_value_keeps_static_with_one_log_safe_warning(
    field: FilterField, value: str
) -> None:
    merge = _merge({field: value})
    assert merge.filters == STATIC
    reason = "matches no key, label, or alias of this option"
    assert merge.warnings == (f"{field.value}_helper {reason}; using the static value",)
    assert value not in merge.warnings[0]


def test_other_source_key_still_overrides() -> None:
    """A known key that does not apply to the source overrides the static value (§9.2)."""
    static = FilterSet(CMA, department=FilterChoice(CMA_DEPARTMENT))
    merge = _merge({FilterField.DEPARTMENT: AIC_DEPARTMENT}, static)
    assert merge.filters.department == FilterChoice(AIC_DEPARTMENT, Provenance.HELPER)
    assert merge.warnings == ()
    effective = resolve_effective_filters(merge.filters, VOCABULARY)
    assert effective.department is None
    assert effective.ignored[0] == IgnoredFilter(
        FilterField.DEPARTMENT,
        FilterDimension.DEPARTMENT,
        AIC_DEPARTMENT,
        IgnoreReason.OTHER_SOURCE,
        Provenance.HELPER,
    )


def test_warnings_follow_field_order_one_per_helper() -> None:
    values: dict[FilterField, str | None] = {
        FilterField.COLOR: "nope",
        FilterField.STYLE: None,
        FilterField.DEPARTMENT: "unavailable",
        FilterField.SOURCE: "nowhere",
    }
    merge = _merge(values)
    assert merge.filters == STATIC
    assert [warning.split(" ", 1)[0] for warning in merge.warnings] == [
        "source_helper",
        "department_helper",
        "style_helper",
        "color_helper",
    ]


def test_mixed_helpers_apply_independently() -> None:
    values: dict[FilterField, str | None] = {
        FilterField.SOURCE: "cleveland_museum_of_art",
        FilterField.DEPARTMENT: "Test Prints",
        FilterField.STYLE: None,
        FilterField.COLOR: "any",
    }
    merge = _merge(values)
    assert merge.filters == FilterSet(
        CMA,
        department=FilterChoice(CMA_DEPARTMENT, Provenance.HELPER),
        style=STATIC.style,
        color=FilterChoice(None, Provenance.HELPER),
        source_provenance=Provenance.HELPER,
    )
    assert merge.warnings == ("style_helper could not be read; using the static value",)


def test_builtin_vocabulary_v1_accepts_only_supported_helper_values() -> None:
    static = FilterSet(AIC)
    values: dict[FilterField, str | None] = {
        FilterField.SOURCE: "local_media",
        FilterField.DEPARTMENT: AIC_DEPARTMENT,
        FilterField.COLOR: "any",
    }
    merge = apply_helper_values(static, values, BUILTIN_VOCABULARY)
    assert merge.filters.source is LOCAL
    assert merge.filters.department == ANY
    assert merge.filters.color == FilterChoice(None, Provenance.HELPER)
    assert len(merge.warnings) == 1
    assert merge.warnings[0].startswith("department_helper matches no key")


# -- overrides and the capability matrix together (B8) ----------------------------------------


def test_helper_source_change_makes_static_department_other_source() -> None:
    merge = _merge({FilterField.SOURCE: "cleveland_museum_of_art"})
    effective = resolve_effective_filters(merge.filters, VOCABULARY)
    assert effective.source is CMA
    assert effective.active() == {}
    assert effective.ignored == (
        IgnoredFilter(
            FilterField.DEPARTMENT,
            FilterDimension.DEPARTMENT,
            AIC_DEPARTMENT,
            IgnoreReason.OTHER_SOURCE,
            Provenance.STATIC,
        ),
        IgnoredFilter(
            FilterField.STYLE,
            FilterDimension.STYLE,
            STYLE,
            IgnoreReason.UNSUPPORTED_BY_SOURCE,
            Provenance.STATIC,
        ),
        IgnoredFilter(
            FilterField.COLOR,
            FilterDimension.COLOR,
            COLOR,
            IgnoreReason.UNSUPPORTED_BY_SOURCE,
            Provenance.STATIC,
        ),
    )
    assert effective.requested.source_provenance is Provenance.HELPER


def test_helper_source_and_department_combine() -> None:
    static = FilterSet(AIC, department=FilterChoice(AIC_DEPARTMENT), style=FilterChoice(PERIOD))
    values: dict[FilterField, str | None] = {
        FilterField.SOURCE: "cleveland_museum_of_art",
        FilterField.DEPARTMENT: "tëst engravings",
    }
    merge = apply_helper_values(static, values, VOCABULARY)
    effective = resolve_effective_filters(merge.filters, VOCABULARY)
    assert effective.active() == {
        FilterDimension.DEPARTMENT: CMA_DEPARTMENT,
        FilterDimension.PERIOD: PERIOD,
    }
    assert effective.ignored == ()


def test_helper_source_local_media_ignores_every_filter() -> None:
    merge = _merge({FilterField.SOURCE: "local_media", FilterField.STYLE: PERIOD})
    effective = resolve_effective_filters(merge.filters, VOCABULARY)
    assert effective.active() == {}
    assert [(i.key, i.reason, i.provenance) for i in effective.ignored] == [
        (AIC_DEPARTMENT, IgnoreReason.UNSUPPORTED_BY_SOURCE, Provenance.STATIC),
        (PERIOD, IgnoreReason.UNSUPPORTED_BY_SOURCE, Provenance.HELPER),
        (COLOR, IgnoreReason.UNSUPPORTED_BY_SOURCE, Provenance.STATIC),
    ]
