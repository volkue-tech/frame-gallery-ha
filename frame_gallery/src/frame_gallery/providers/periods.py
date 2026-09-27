"""The period filter's project-defined year ranges (§15.2, D-146).

Both museums document their works' creation years as numbers: the Art
Institute's ``date_start`` and Cleveland's ``creation_date_earliest``. A work
matches a period when that earliest year lies inside the range, both bounds
included. The ranges are labelled with years, not style names; the vocabulary
(``config.vocabulary``) carries the same keys.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final


@dataclass(frozen=True, slots=True)
class YearRange:
    """Inclusive bounds; ``None`` is open."""

    first: int | None
    last: int | None

    def __post_init__(self) -> None:
        if self.first is None and self.last is None:
            msg = "a period needs at least one bound"
            raise ValueError(msg)
        if self.first is not None and self.last is not None and self.first > self.last:
            msg = "a period's first year must not follow its last"
            raise ValueError(msg)

    def contains(self, value: int) -> bool:
        return (self.first is None or value >= self.first) and (
            self.last is None or value <= self.last
        )


PERIOD_RANGES: Final[Mapping[str, YearRange]] = MappingProxyType(
    {
        "period_before_1400": YearRange(None, 1399),
        "period_1400_1599": YearRange(1400, 1599),
        "period_1600_1799": YearRange(1600, 1799),
        "period_1800_1899": YearRange(1800, 1899),
        "period_1900_and_later": YearRange(1900, None),
    }
)
"""Contiguous and non-overlapping: every year belongs to exactly one period."""


def period_range(key: str) -> YearRange:
    """The range of a period key. Raises ``ValueError`` for an unknown key
    (the capability matrix passes only vocabulary keys)."""
    found = PERIOD_RANGES.get(key)
    if found is None:
        msg = f"unknown period key {key!r}"
        raise ValueError(msg)
    return found
