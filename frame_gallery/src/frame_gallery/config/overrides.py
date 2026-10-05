"""Merging helper values into the static filters (§9.2, §15.3, D-112).

Each helper that was read either overrides its static value or falls back to
it with exactly one warning (B3-B5). A known key that does not apply to the
selected source still overrides the static value; the capability matrix then
ignores and reports it exactly like a static value (§9.2). Warnings name the
helper option and the reason only, never the helper's value.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from frame_gallery.config.filters import FilterChoice, FilterField, FilterSet, Provenance
from frame_gallery.config.vocabulary import (
    UNAVAILABLE_TERMS,
    LookupStatus,
    Vocabulary,
    normalize_term,
)


@dataclass(frozen=True, slots=True)
class HelperMerge:
    filters: FilterSet
    warnings: tuple[str, ...]
    """One log-safe WARNING per helper that fell back to its static value."""


_UNREADABLE: Final = "could not be read"
_UNAVAILABLE: Final = "is unavailable in Home Assistant"
_NOT_A_SOURCE: Final = (
    "does not name a source (art_institute_chicago, cleveland_museum_of_art, "
    "local_media, or wikimedia_commons)"
)
_NOT_A_KEY: Final = "matches no key, label, or alias of this option"


def _warning(field: FilterField, reason: str) -> str:
    return f"{field.value}_helper {reason}; using the static value"


def apply_helper_values(
    static: FilterSet, values: Mapping[FilterField, str | None], vocabulary: Vocabulary
) -> HelperMerge:
    """Override static values with valid helper values; fall back otherwise.

    ``values`` holds the helpers that were configured: ``None`` for a helper
    that could not be read. Fields are processed in ``FilterField`` order, so
    the warnings are too.
    """
    source, source_provenance = static.source, static.source_provenance
    choices = {
        FilterField.DEPARTMENT: static.department,
        FilterField.STYLE: static.style,
        FilterField.COLOR: static.color,
    }
    warnings: list[str] = []
    for field in FilterField:
        if field not in values:
            continue
        value = values[field]
        if value is None:
            warnings.append(_warning(field, _UNREADABLE))
        elif normalize_term(value) in UNAVAILABLE_TERMS:
            warnings.append(_warning(field, _UNAVAILABLE))
        elif field is FilterField.SOURCE:
            helper_source = vocabulary.lookup_source(value)
            if helper_source is None:
                warnings.append(_warning(field, _NOT_A_SOURCE))
            else:
                source, source_provenance = helper_source, Provenance.HELPER
        else:
            result = vocabulary.lookup(field, value)
            if result.status is LookupStatus.INVALID:
                warnings.append(_warning(field, _NOT_A_KEY))
            else:
                choices[field] = FilterChoice(result.key, Provenance.HELPER)
    merged = FilterSet(
        source=source,
        department=choices[FilterField.DEPARTMENT],
        style=choices[FilterField.STYLE],
        color=choices[FilterField.COLOR],
        source_provenance=source_provenance,
    )
    return HelperMerge(filters=merged, warnings=tuple(warnings))
