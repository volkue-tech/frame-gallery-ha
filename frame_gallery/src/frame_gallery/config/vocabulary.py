"""Filter vocabularies and helper-value normalization (§15.2, D-124).

A vocabulary gives every filter key a label and optional aliases. Static
option values and helper states are normalized with :func:`normalize_term`
and matched against the keys, labels, and aliases of one option field only.
The source is not part of any vocabulary: it accepts only the defined source
keys (§15.3).
"""

from __future__ import annotations

import enum
import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from frame_gallery.config.filters import FilterDimension, FilterField
from frame_gallery.domain import SourceKey

KEY_MAX_LENGTH: Final = 64
LABEL_MAX_LENGTH: Final = 100
"""The limit for labels and aliases."""

LOOKUP_MAX_LENGTH: Final = 255
"""Longer values are invalid without being normalized; a helper state is at
most 255 characters (§15.3), and no key, label, or alias comes close."""

NO_FILTER_TERMS: Final = frozenset({"any", "all", "random", "none", ""})
"""Normalized values that mean "no filter" (§15.2)."""

UNAVAILABLE_TERMS: Final = frozenset({"unavailable", "unknown"})
"""Home Assistant's states for an entity without a usable value. A helper in
one of them falls back like a helper that could not be read (B4)."""

_KEY: Final = re.compile(r"[a-z0-9]+(?:_[a-z0-9]+)*", re.ASCII)
"""Keys are already normalized: no leading, trailing, or doubled ``_``."""

_SEPARATORS: Final = re.compile(r"[^a-z0-9]+", re.ASCII)

_FIELD_OF: Final[Mapping[FilterDimension, FilterField]] = MappingProxyType(
    {
        FilterDimension.DEPARTMENT: FilterField.DEPARTMENT,
        FilterDimension.STYLE: FilterField.STYLE,
        FilterDimension.PERIOD: FilterField.STYLE,
        FilterDimension.COLOR: FilterField.COLOR,
    }
)

FIELD_DIMENSIONS: Final[Mapping[FilterField, frozenset[FilterDimension]]] = MappingProxyType(
    {
        FilterField.DEPARTMENT: frozenset({FilterDimension.DEPARTMENT}),
        FilterField.STYLE: frozenset({FilterDimension.STYLE, FilterDimension.PERIOD}),
        FilterField.COLOR: frozenset({FilterDimension.COLOR}),
    }
)
"""The dimensions each option field carries; ``style`` also carries periods (§9.2)."""

_DEPARTMENT_PREFIXES: Final[Mapping[SourceKey, str]] = MappingProxyType(
    {
        SourceKey.ART_INSTITUTE_CHICAGO: "aic_",
        SourceKey.CLEVELAND_MUSEUM_OF_ART: "cma_",
    }
)

_PREFIXES: Final[Mapping[FilterDimension, str]] = MappingProxyType(
    {
        FilterDimension.STYLE: "style_",
        FilterDimension.PERIOD: "period_",
        FilterDimension.COLOR: "color_",
    }
)

_SOURCES: Final[Mapping[str, SourceKey]] = MappingProxyType({key.value: key for key in SourceKey})


def normalize_term(text: str) -> str:
    """Case-fold, strip diacritics, and join alphanumeric runs with ``_``.

    ``"Musée d'Orsay"`` becomes ``"musee_d_orsay"``. Compatibility forms
    (full-width letters, ligatures) decompose to their plain letters; the
    second case fold catches letters that only become cased by decomposition.
    """
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    decomposed = unicodedata.normalize("NFKD", decomposed.casefold())
    stripped = "".join(char for char in decomposed if not unicodedata.combining(char))
    return _SEPARATORS.sub("_", stripped).strip("_")


def field_for(dimension: FilterDimension) -> FilterField:
    """The option field that carries ``dimension`` (period keys go in ``style``)."""
    return _FIELD_OF[dimension]


def _means_no_filter(value: str, term: str) -> bool:
    """Whether ``value`` (normalized to ``term``) asks for no filter.

    A value made only of letters outside ``[a-z0-9]`` also normalizes to the
    empty term; it is invalid rather than silently "no filter". Blank values
    and values made only of separators (such as ``-``) mean no filter.
    """
    if term not in NO_FILTER_TERMS:
        return False
    return bool(term) or not any(char.isalnum() for char in value)


def _check_text(text: str, what: str) -> None:
    if not text.strip() or len(text) > LABEL_MAX_LENGTH:
        msg = f"a vocabulary {what} must be non-blank and at most {LABEL_MAX_LENGTH} characters"
        raise ValueError(msg)
    term = normalize_term(text)
    if term in NO_FILTER_TERMS or term in UNAVAILABLE_TERMS:
        msg = f"the vocabulary {what} {text!r} normalizes to a reserved term"
        raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class VocabularyEntry:
    """One filter value: a namespaced key, its label, and its aliases (§15.2)."""

    key: str
    label: str
    dimension: FilterDimension
    source: SourceKey | None = None
    """The museum of a department entry; ``None`` for every other dimension."""

    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len(self.key) > KEY_MAX_LENGTH or _KEY.fullmatch(self.key) is None:
            msg = "a vocabulary key must be 1-64 of a-z, 0-9, and single inner underscores"
            raise ValueError(msg)
        if self.dimension is FilterDimension.DEPARTMENT:
            prefix = None if self.source is None else _DEPARTMENT_PREFIXES.get(self.source)
            if prefix is None:
                msg = "a department entry names its museum source"
                raise ValueError(msg)
        elif self.source is not None:
            msg = "only department entries name a source"
            raise ValueError(msg)
        else:
            prefix = _PREFIXES[self.dimension]
        if not self.key.startswith(prefix):
            msg = f"the {self.dimension.value} key {self.key!r} must start with {prefix!r}"
            raise ValueError(msg)
        _check_text(self.label, "label")
        for alias in self.aliases:
            _check_text(alias, "alias")

    @property
    def field(self) -> FilterField:
        """The option field this entry belongs to."""
        return field_for(self.dimension)

    def terms(self) -> tuple[str, ...]:
        """The normalized key, label, and aliases, without duplicates, in order."""
        texts = (self.key, self.label, *self.aliases)
        return tuple(dict.fromkeys(normalize_term(text) for text in texts))


class LookupStatus(enum.StrEnum):
    ANY = "any"
    """The value asks for no filter."""

    KEY = "key"
    """The value names a key of the field."""

    INVALID = "invalid"
    """The value normalizes to no key of the field."""


@dataclass(frozen=True, slots=True)
class Lookup:
    """The result of matching one value against one option field."""

    status: LookupStatus
    key: str | None = None
    """The matched key; set exactly when ``status`` is ``KEY``."""

    def __post_init__(self) -> None:
        if (self.status is LookupStatus.KEY) != (self.key is not None):
            msg = "a lookup carries a key exactly when its status is KEY"
            raise ValueError(msg)


_ANY: Final = Lookup(LookupStatus.ANY)
_INVALID: Final = Lookup(LookupStatus.INVALID)


class Vocabulary:
    """A versioned set of filter keys, labels, and aliases (§15.2, D-124).

    Within each option field every normalized key, label, and alias maps to
    exactly one key, so normalization is deterministic. The department field
    holds the departments of both museums; the ``style`` field holds style
    and period keys; the ``color`` field holds colour keys.
    """

    __slots__ = ("_by_key", "_entries", "_terms", "_version")

    def __init__(self, version: str, entries: Iterable[VocabularyEntry]) -> None:
        if not version.strip():
            msg = "a vocabulary needs a version"
            raise ValueError(msg)
        ordered = tuple(entries)
        by_key: dict[str, VocabularyEntry] = {}
        terms: dict[FilterField, dict[str, str]] = {field: {} for field in FIELD_DIMENSIONS}
        for entry in ordered:
            if entry.key in by_key:
                msg = f"duplicate vocabulary key {entry.key!r}"
                raise ValueError(msg)
            by_key[entry.key] = entry
            field_terms = terms[entry.field]
            for term in entry.terms():
                owner = field_terms.setdefault(term, entry.key)
                if owner != entry.key:
                    msg = (
                        f"{term!r} is ambiguous in the {entry.field.value} field: "
                        f"{owner!r} and {entry.key!r}"
                    )
                    raise ValueError(msg)
        self._version = version
        self._entries = ordered
        self._by_key = by_key
        self._terms = terms

    @property
    def version(self) -> str:
        return self._version

    def entry(self, key: str) -> VocabularyEntry | None:
        """The entry for an exact key, or ``None``."""
        return self._by_key.get(key)

    def entries_for(self, field: FilterField) -> tuple[VocabularyEntry, ...]:
        """The entries of one option field, in vocabulary order."""
        self._field_terms(field)
        return tuple(entry for entry in self._entries if entry.field is field)

    def lookup(self, field: FilterField, value: str) -> Lookup:
        """Normalize ``value`` and match it against the field's entries.

        Raises ``ValueError`` for the ``SOURCE`` field (use :meth:`lookup_source`).
        """
        field_terms = self._field_terms(field)
        if len(value) > LOOKUP_MAX_LENGTH:
            return _INVALID
        term = normalize_term(value)
        if _means_no_filter(value, term):
            return _ANY
        key = field_terms.get(term)
        return _INVALID if key is None else Lookup(LookupStatus.KEY, key)

    def lookup_source(self, value: str) -> SourceKey | None:
        """The source whose key equals the normalized ``value``, or ``None``.

        Only the defined source keys are accepted (§15.3): there are no labels
        or aliases, and "any" is not a source.
        """
        if len(value) > LOOKUP_MAX_LENGTH:
            return None
        return _SOURCES.get(normalize_term(value))

    def _field_terms(self, field: FilterField) -> Mapping[str, str]:
        field_terms = self._terms.get(field)
        if field_terms is None:
            msg = "the source has no vocabulary; use lookup_source"
            raise ValueError(msg)
        return field_terms

    def __repr__(self) -> str:
        return f"Vocabulary({self._version!r}, entries={len(self._entries)})"


def _cleveland(key: str, documented: str) -> VocabularyEntry:
    """A Cleveland department: the label names the museum (labels stay
    distinct across museums, D-143); the documented value is an alias."""
    return VocabularyEntry(
        key=key,
        label=f"{documented} (Cleveland)",
        dimension=FilterDimension.DEPARTMENT,
        source=SourceKey.CLEVELAND_MUSEUM_OF_ART,
        aliases=(documented,),
    )


def _period(key: str, label: str, *aliases: str) -> VocabularyEntry:
    return VocabularyEntry(key=key, label=label, dimension=FilterDimension.PERIOD, aliases=aliases)


BUILTIN_VOCABULARY: Final = Vocabulary(
    version="1",
    entries=(
        _cleveland("cma_american_painting_sculpture", "American Painting and Sculpture"),
        _cleveland("cma_european_painting_sculpture", "European Painting and Sculpture"),
        _cleveland(
            "cma_modern_european_painting_sculpture", "Modern European Painting and Sculpture"
        ),
        _cleveland("cma_drawings", "Drawings"),
        _cleveland("cma_prints", "Prints"),
        _cleveland("cma_photography", "Photography"),
        _cleveland("cma_chinese_art", "Chinese Art"),
        _cleveland("cma_japanese_art", "Japanese Art"),
        _cleveland("cma_korean_art", "Korean Art"),
        _cleveland("cma_indian_southeast_asian_art", "Indian and South East Asian Art"),
        _cleveland("cma_islamic_art", "Islamic Art"),
        _cleveland("cma_textiles", "Textiles"),
        _period("period_before_1400", "Before 1400", "up to 1399"),
        _period("period_1400_1599", "1400 to 1599", "1400-1599", "15th and 16th centuries"),
        _period("period_1600_1799", "1600 to 1799", "1600-1799", "17th and 18th centuries"),
        _period("period_1800_1899", "1800 to 1899", "1800-1899", "19th century"),
        _period("period_1900_and_later", "1900 and later", "since 1900", "20th century and later"),
    ),
)
"""The shipped vocabulary, version 1 (Q-14, D-152), built only from values the
official documentation names (D-146):

- the curated Cleveland departments, whose documented values the Cleveland
  adapter sends (``providers.cma.DEPARTMENTS``);
- five project-defined periods of the earliest creation year, valid for both
  museums (``providers.periods.PERIOD_RANGES``).

There are no Art Institute departments, no styles, and no colours: their
values are undocumented (Q-25). The mapping is documented in
``VOCABULARY.md``; tests keep the two identical."""
