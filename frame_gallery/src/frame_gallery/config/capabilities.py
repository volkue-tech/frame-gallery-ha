"""The filter capability matrix (§9.2, D-124).

A filter applies only when the selected source supports its dimension and,
for a department, when the department belongs to that source. Everything
else is ignored for the run and listed with its reason, so it can be
reported in the log, the summary line, and ``last_run.json`` (B8). Nothing
is ever silently dropped.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from frame_gallery.config.filters import (
    EffectiveFilters,
    FilterDimension,
    FilterField,
    FilterSet,
    IgnoredFilter,
    IgnoreReason,
)
from frame_gallery.config.vocabulary import FIELD_DIMENSIONS, Vocabulary, VocabularyEntry
from frame_gallery.domain import SourceKey

CAPABILITY_MATRIX: Final[Mapping[SourceKey, frozenset[FilterDimension]]] = MappingProxyType(
    {
        SourceKey.LOCAL_MEDIA: frozenset(),
        SourceKey.ART_INSTITUTE_CHICAGO: frozenset(
            {
                FilterDimension.DEPARTMENT,
                FilterDimension.STYLE,
                FilterDimension.PERIOD,
                FilterDimension.COLOR,
            }
        ),
        SourceKey.CLEVELAND_MUSEUM_OF_ART: frozenset(
            {FilterDimension.DEPARTMENT, FilterDimension.PERIOD}
        ),
    }
)
"""The dimensions each source supports (§9.2). Landscape-only, strict
near-16:9, and the fit mode apply to every source and are not listed."""

_FILTER_FIELDS: Final = (FilterField.DEPARTMENT, FilterField.STYLE, FilterField.COLOR)
"""The fields resolved, in the order ignored filters are reported."""

type CapabilityRow = tuple[FilterDimension, tuple[tuple[SourceKey, bool], ...]]


def supports(source: SourceKey, dimension: FilterDimension) -> bool:
    """Whether ``source`` supports filtering by ``dimension``."""
    return dimension in CAPABILITY_MATRIX[source]


def capability_rows() -> tuple[CapabilityRow, ...]:
    """The matrix as documentation rows: each dimension, then each source in
    ``SourceKey`` order with whether it supports the dimension."""
    return tuple(
        (dimension, tuple((source, supports(source, dimension)) for source in SourceKey))
        for dimension in FilterDimension
    )


def _ignore_reason(source: SourceKey, entry: VocabularyEntry) -> IgnoreReason | None:
    if not supports(source, entry.dimension):
        return IgnoreReason.UNSUPPORTED_BY_SOURCE
    if entry.source is not None and entry.source is not source:
        return IgnoreReason.OTHER_SOURCE
    return None


def resolve_effective_filters(filters: FilterSet, vocabulary: Vocabulary) -> EffectiveFilters:
    """Apply the capability matrix: keep what the source supports, and list
    everything else as ignored with a reason (never silently dropped).

    Every key must come from ``vocabulary`` through option or helper
    validation; an unknown key, or a key in the wrong field, is a programming
    error and raises ``ValueError``.
    """
    applied: dict[FilterDimension, str] = {}
    ignored: list[IgnoredFilter] = []
    for field in _FILTER_FIELDS:
        choice = filters.choice(field)
        if choice.key is None:
            continue
        entry = vocabulary.entry(choice.key)
        if entry is None or entry.dimension not in FIELD_DIMENSIONS[field]:
            msg = f"the {field.value} value is not a validated vocabulary key of that field"
            raise ValueError(msg)
        reason = _ignore_reason(filters.source, entry)
        if reason is None:
            applied[entry.dimension] = entry.key
        else:
            ignored.append(
                IgnoredFilter(
                    field=field,
                    dimension=entry.dimension,
                    key=entry.key,
                    reason=reason,
                    provenance=choice.provenance,
                )
            )
    return EffectiveFilters(
        source=filters.source,
        department=applied.get(FilterDimension.DEPARTMENT),
        style=applied.get(FilterDimension.STYLE),
        period=applied.get(FilterDimension.PERIOD),
        color=applied.get(FilterDimension.COLOR),
        ignored=tuple(ignored),
        requested=filters,
    )
