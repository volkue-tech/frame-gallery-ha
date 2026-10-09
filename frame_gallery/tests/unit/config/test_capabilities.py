"""The capability matrix and effective filters (§9.2, D-124, B8)."""

from __future__ import annotations

import itertools

import pytest

from frame_gallery.config.capabilities import (
    CAPABILITY_MATRIX,
    capability_rows,
    resolve_effective_filters,
    supports,
)
from frame_gallery.config.filters import (
    ANY,
    EffectiveFilters,
    FilterChoice,
    FilterDimension,
    FilterField,
    FilterSet,
    IgnoredFilter,
    IgnoreReason,
    Provenance,
)
from frame_gallery.domain import SourceKey
from tests.unit.config.synthetic import (
    AIC_DEPARTMENT,
    CMA_DEPARTMENT,
    COLOR,
    PERIOD,
    STYLE,
    VOCABULARY,
)

LOCAL = SourceKey.LOCAL_MEDIA
AIC = SourceKey.ART_INSTITUTE_CHICAGO
CMA = SourceKey.CLEVELAND_MUSEUM_OF_ART
COMMONS = SourceKey.WIKIMEDIA_COMMONS

DEPARTMENT = FilterDimension.DEPARTMENT
STYLE_DIM = FilterDimension.STYLE
PERIOD_DIM = FilterDimension.PERIOD
COLOR_DIM = FilterDimension.COLOR

# The expected matrix, written out by hand from §9.2 as amended by D-146
# (not derived from the code).
EXPECTED_SUPPORT = {
    (COMMONS, DEPARTMENT): False,
    (COMMONS, STYLE_DIM): False,
    (COMMONS, PERIOD_DIM): False,
    (COMMONS, COLOR_DIM): True,
    (LOCAL, DEPARTMENT): False,
    (LOCAL, STYLE_DIM): False,
    (LOCAL, PERIOD_DIM): False,
    (LOCAL, COLOR_DIM): False,
    (AIC, DEPARTMENT): False,
    (AIC, STYLE_DIM): False,
    (AIC, PERIOD_DIM): True,
    (AIC, COLOR_DIM): False,
    (CMA, DEPARTMENT): True,
    (CMA, STYLE_DIM): False,
    (CMA, PERIOD_DIM): True,
    (CMA, COLOR_DIM): False,
}

# (field, key, dimension) for every kind of filter value.
VALUES = (
    (FilterField.DEPARTMENT, AIC_DEPARTMENT, DEPARTMENT),
    (FilterField.DEPARTMENT, CMA_DEPARTMENT, DEPARTMENT),
    (FilterField.STYLE, STYLE, STYLE_DIM),
    (FilterField.STYLE, PERIOD, PERIOD_DIM),
    (FilterField.COLOR, COLOR, COLOR_DIM),
)

APPLIED = None
UNSUPPORTED = IgnoreReason.UNSUPPORTED_BY_SOURCE
OTHER = IgnoreReason.OTHER_SOURCE

# The expected outcome of each value for each source (None = applied).
EXPECTED_OUTCOME = {
    (COMMONS, AIC_DEPARTMENT): UNSUPPORTED,
    (COMMONS, CMA_DEPARTMENT): UNSUPPORTED,
    (COMMONS, STYLE): UNSUPPORTED,
    (COMMONS, PERIOD): UNSUPPORTED,
    (COMMONS, COLOR): APPLIED,
    (LOCAL, AIC_DEPARTMENT): UNSUPPORTED,
    (LOCAL, CMA_DEPARTMENT): UNSUPPORTED,
    (LOCAL, STYLE): UNSUPPORTED,
    (LOCAL, PERIOD): UNSUPPORTED,
    (LOCAL, COLOR): UNSUPPORTED,
    (AIC, AIC_DEPARTMENT): UNSUPPORTED,
    (AIC, CMA_DEPARTMENT): UNSUPPORTED,
    (AIC, STYLE): UNSUPPORTED,
    (AIC, PERIOD): APPLIED,
    (AIC, COLOR): UNSUPPORTED,
    (CMA, AIC_DEPARTMENT): OTHER,
    (CMA, CMA_DEPARTMENT): APPLIED,
    (CMA, STYLE): UNSUPPORTED,
    (CMA, PERIOD): APPLIED,
    (CMA, COLOR): UNSUPPORTED,
}


def _filters(
    source: SourceKey, field: FilterField, key: str | None, provenance: Provenance
) -> FilterSet:
    choice = FilterChoice(key, provenance)
    if field is FilterField.DEPARTMENT:
        return FilterSet(source, department=choice)
    if field is FilterField.STYLE:
        return FilterSet(source, style=choice)
    return FilterSet(source, color=choice)


def test_matrix_is_exactly_the_published_one() -> None:
    assert dict(CAPABILITY_MATRIX) == {
        COMMONS: frozenset({COLOR_DIM}),
        LOCAL: frozenset(),
        AIC: frozenset({PERIOD_DIM}),
        CMA: frozenset({DEPARTMENT, PERIOD_DIM}),
    }


def test_matrix_is_read_only() -> None:
    with pytest.raises(TypeError):
        CAPABILITY_MATRIX[LOCAL] = frozenset({DEPARTMENT})  # type: ignore[index]


@pytest.mark.parametrize(("source", "dimension"), list(EXPECTED_SUPPORT))
def test_supports(source: SourceKey, dimension: FilterDimension) -> None:
    assert supports(source, dimension) is EXPECTED_SUPPORT[(source, dimension)]


def test_capability_rows() -> None:
    rows = capability_rows()
    assert [dimension for dimension, _ in rows] == [DEPARTMENT, STYLE_DIM, PERIOD_DIM, COLOR_DIM]
    for dimension, cells in rows:
        assert [source for source, _ in cells] == [LOCAL, AIC, CMA, COMMONS]
        for source, supported in cells:
            assert supported is EXPECTED_SUPPORT[(source, dimension)]


@pytest.mark.parametrize("provenance", list(Provenance))
@pytest.mark.parametrize(("source", "value"), list(itertools.product(list(SourceKey), VALUES)))
def test_every_source_value_and_provenance(
    source: SourceKey,
    value: tuple[FilterField, str, FilterDimension],
    provenance: Provenance,
) -> None:
    field, key, dimension = value
    filters = _filters(source, field, key, provenance)
    effective = resolve_effective_filters(filters, VOCABULARY)
    assert effective.source is source
    assert effective.requested is filters
    reason = EXPECTED_OUTCOME[(source, key)]
    if reason is None:
        assert effective.active() == {dimension: key}
        assert effective.ignored == ()
    else:
        assert effective.active() == {}
        assert effective.ignored == (
            IgnoredFilter(
                field=field, dimension=dimension, key=key, reason=reason, provenance=provenance
            ),
        )


@pytest.mark.parametrize("source", list(SourceKey))
def test_no_filters_means_nothing_applied_or_ignored(source: SourceKey) -> None:
    filters = FilterSet(source)
    assert resolve_effective_filters(filters, VOCABULARY) == EffectiveFilters(
        source=source,
        department=None,
        style=None,
        period=None,
        color=None,
        ignored=(),
        requested=filters,
    )


def test_explicit_any_choices_are_neither_applied_nor_ignored() -> None:
    helper_any = FilterChoice(None, Provenance.HELPER)
    filters = FilterSet(CMA, department=helper_any, style=helper_any, color=helper_any)
    effective = resolve_effective_filters(filters, VOCABULARY)
    assert effective.active() == {}
    assert effective.ignored == ()


def test_only_the_period_applies_on_aic() -> None:
    # D-146: the Art Institute's department, style, and colour values are
    # undocumented, so the beta reports them as unsupported.
    filters = FilterSet(
        AIC,
        department=FilterChoice(AIC_DEPARTMENT),
        style=FilterChoice(STYLE, Provenance.HELPER),
        color=FilterChoice(COLOR),
    )
    effective = resolve_effective_filters(filters, VOCABULARY)
    assert effective.active() == {}
    assert [ignored.describe() for ignored in effective.ignored] == [
        "department=aic_test_paintings(unsupported_by_source)",
        "style=style_test_one(unsupported_by_source)",
        "color=color_test_blue(unsupported_by_source)",
    ]
    period = resolve_effective_filters(FilterSet(AIC, style=FilterChoice(PERIOD)), VOCABULARY)
    assert period.active() == {PERIOD_DIM: PERIOD}
    assert period.ignored == ()


def test_style_ignored_and_period_applied_on_cma() -> None:
    style = resolve_effective_filters(FilterSet(CMA, style=FilterChoice(STYLE)), VOCABULARY)
    assert style.style is None
    assert style.period is None
    assert [ignored.describe() for ignored in style.ignored] == [
        "style=style_test_one(unsupported_by_source)"
    ]
    period = resolve_effective_filters(FilterSet(CMA, style=FilterChoice(PERIOD)), VOCABULARY)
    assert period.period == PERIOD
    assert period.style is None
    assert period.ignored == ()


def test_ignored_filters_are_listed_in_field_order() -> None:
    filters = FilterSet(
        CMA,
        department=FilterChoice(AIC_DEPARTMENT, Provenance.STATIC),
        style=FilterChoice(STYLE, Provenance.HELPER),
        color=FilterChoice(COLOR, Provenance.STATIC),
    )
    effective = resolve_effective_filters(filters, VOCABULARY)
    assert effective.active() == {}
    assert effective.ignored == (
        IgnoredFilter(FilterField.DEPARTMENT, DEPARTMENT, AIC_DEPARTMENT, OTHER, Provenance.STATIC),
        IgnoredFilter(FilterField.STYLE, STYLE_DIM, STYLE, UNSUPPORTED, Provenance.HELPER),
        IgnoredFilter(FilterField.COLOR, COLOR_DIM, COLOR, UNSUPPORTED, Provenance.STATIC),
    )
    assert [ignored.describe() for ignored in effective.ignored] == [
        "department=aic_test_paintings(other_source)",
        "style=style_test_one(unsupported_by_source)",
        "color=color_test_blue(unsupported_by_source)",
    ]


def test_local_media_ignores_everything() -> None:
    filters = FilterSet(
        LOCAL,
        department=FilterChoice(CMA_DEPARTMENT),
        style=FilterChoice(PERIOD),
        color=FilterChoice(COLOR, Provenance.HELPER),
    )
    effective = resolve_effective_filters(filters, VOCABULARY)
    assert effective.active() == {}
    assert [(i.field, i.reason) for i in effective.ignored] == [
        (FilterField.DEPARTMENT, UNSUPPORTED),
        (FilterField.STYLE, UNSUPPORTED),
        (FilterField.COLOR, UNSUPPORTED),
    ]


def test_mixed_applied_and_ignored() -> None:
    filters = FilterSet(
        CMA,
        department=FilterChoice(CMA_DEPARTMENT),
        style=FilterChoice(PERIOD, Provenance.HELPER),
        color=FilterChoice(COLOR),
    )
    effective = resolve_effective_filters(filters, VOCABULARY)
    assert effective.active() == {DEPARTMENT: CMA_DEPARTMENT, PERIOD_DIM: PERIOD}
    assert [i.describe() for i in effective.ignored] == [
        "color=color_test_blue(unsupported_by_source)"
    ]


@pytest.mark.parametrize(
    "filters",
    [
        FilterSet(AIC, department=FilterChoice("aic_unknown")),
        FilterSet(AIC, color=FilterChoice("Test Blue")),  # a label, not a key
        FilterSet(AIC, department=FilterChoice(STYLE)),  # a key of another field
        FilterSet(AIC, style=FilterChoice(COLOR)),
        FilterSet(AIC, color=FilterChoice(PERIOD)),
    ],
)
def test_unvalidated_keys_are_programming_errors(filters: FilterSet) -> None:
    with pytest.raises(ValueError, match="not a validated vocabulary key"):
        resolve_effective_filters(filters, VOCABULARY)


def test_any_constant_is_the_default_choice() -> None:
    assert FilterSet(AIC).department is ANY
