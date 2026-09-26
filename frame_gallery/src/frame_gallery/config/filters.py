"""Filter value types (§9.2, D-124).

There are four distinct filter dimensions besides the source: department or
collection, style, period, and colour. The ``style`` option carries either a
``style_...`` key (style dimension) or a ``period_...`` key (period dimension).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from frame_gallery.domain import SourceKey


class FilterField(enum.StrEnum):
    """An option that selects or filters artwork (and may have a helper)."""

    SOURCE = "source"
    DEPARTMENT = "department"
    STYLE = "style"
    COLOR = "color"


class FilterDimension(enum.StrEnum):
    """A filter dimension of the capability matrix (§9.2)."""

    DEPARTMENT = "department"
    STYLE = "style"
    PERIOD = "period"
    COLOR = "color"


class Provenance(enum.StrEnum):
    """Where an effective filter value came from."""

    STATIC = "static"
    HELPER = "helper"


@dataclass(frozen=True, slots=True)
class FilterChoice:
    """One filter value. ``key`` is a vocabulary key, or ``None`` for "any"."""

    key: str | None = None
    provenance: Provenance = Provenance.STATIC


ANY = FilterChoice()


@dataclass(frozen=True, slots=True)
class FilterSet:
    """The source and filter values, before the capability matrix is applied."""

    source: SourceKey
    department: FilterChoice = ANY
    style: FilterChoice = ANY
    color: FilterChoice = ANY
    source_provenance: Provenance = Provenance.STATIC

    def choice(self, field: FilterField) -> FilterChoice:
        """The choice for a filter field (not for ``SOURCE``)."""
        if field is FilterField.DEPARTMENT:
            return self.department
        if field is FilterField.STYLE:
            return self.style
        if field is FilterField.COLOR:
            return self.color
        msg = "the source is not a FilterChoice"
        raise ValueError(msg)


class IgnoreReason(enum.StrEnum):
    """Why a configured filter does not apply to the selected source."""

    UNSUPPORTED_BY_SOURCE = "unsupported_by_source"
    """The source does not support this filter dimension."""

    OTHER_SOURCE = "other_source"
    """The value belongs to another source, for example a ``cma_...`` department
    while the source is the Art Institute."""


@dataclass(frozen=True, slots=True)
class IgnoredFilter:
    """A filter that was configured but ignored for this run, visibly (B8)."""

    field: FilterField
    dimension: FilterDimension
    key: str
    reason: IgnoreReason
    provenance: Provenance

    def describe(self) -> str:
        """A compact, log-safe description, e.g. ``department=cma_x(other_source)``."""
        return f"{self.field.value}={self.key}({self.reason.value})"


@dataclass(frozen=True, slots=True)
class EffectiveFilters:
    """The filters that apply to this run, and those that were ignored."""

    source: SourceKey
    department: str | None
    style: str | None
    period: str | None
    color: str | None
    ignored: tuple[IgnoredFilter, ...]
    requested: FilterSet
    """The values before the capability matrix was applied (for provenance)."""

    def active(self) -> dict[FilterDimension, str]:
        """The applied filter keys by dimension (unset dimensions omitted)."""
        values = {
            FilterDimension.DEPARTMENT: self.department,
            FilterDimension.STYLE: self.style,
            FilterDimension.PERIOD: self.period,
            FilterDimension.COLOR: self.color,
        }
        return {dimension: key for dimension, key in values.items() if key is not None}
