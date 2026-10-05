"""The shipped vocabulary, version 1 (Q-14, D-146, D-152), its agreement with
the adapters' mappings, and with VOCABULARY.md."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from frame_gallery.config.capabilities import CAPABILITY_MATRIX
from frame_gallery.config.filters import FilterDimension, FilterField
from frame_gallery.config.vocabulary import (
    BUILTIN_VOCABULARY,
    NO_FILTER_TERMS,
    UNAVAILABLE_TERMS,
    Lookup,
    LookupStatus,
    Vocabulary,
    normalize_term,
)
from frame_gallery.domain import SourceKey
from frame_gallery.providers.cma import DEPARTMENTS, DOCUMENTED_DEPARTMENTS
from frame_gallery.providers.periods import PERIOD_RANGES

DOCUMENT = Path(__file__).resolve().parents[3] / "VOCABULARY.md"
VOCAB = BUILTIN_VOCABULARY


def test_version_and_shape() -> None:
    assert VOCAB.version == "1"
    departments = VOCAB.entries_for(FilterField.DEPARTMENT)
    styles = VOCAB.entries_for(FilterField.STYLE)
    assert len(departments) == 12
    assert {entry.source for entry in departments} == {SourceKey.CLEVELAND_MUSEUM_OF_ART}
    assert [entry.dimension for entry in styles] == [FilterDimension.PERIOD] * 5
    assert VOCAB.entries_for(FilterField.COLOR) == ()


def test_only_documented_values_are_used() -> None:
    # D-146: no Art Institute departments, no styles, no colours.
    keys = [
        entry.key
        for field in (FilterField.DEPARTMENT, FilterField.STYLE, FilterField.COLOR)
        for entry in VOCAB.entries_for(field)
    ]
    assert not [key for key in keys if key.startswith(("aic_", "style_", "color_"))]


def test_cleveland_entries_match_the_adapter_mapping() -> None:
    departments = VOCAB.entries_for(FilterField.DEPARTMENT)
    assert [entry.key for entry in departments] == list(DEPARTMENTS)
    for entry in departments:
        documented = DEPARTMENTS[entry.key]
        assert documented in DOCUMENTED_DEPARTMENTS
        assert entry.label == f"{documented} (Cleveland)"
        assert entry.aliases == (documented,)


def test_period_entries_match_the_adapter_ranges() -> None:
    assert [entry.key for entry in VOCAB.entries_for(FilterField.STYLE)] == list(PERIOD_RANGES)


def test_labels_are_distinct_and_name_their_museum() -> None:
    labels = [
        normalize_term(e.label)
        for f in FilterField
        if f is not FilterField.SOURCE
        for e in VOCAB.entries_for(f)
    ]
    assert len(labels) == len(set(labels))
    for entry in VOCAB.entries_for(FilterField.DEPARTMENT):
        assert entry.label.endswith("(Cleveland)")


def test_terms_are_unique_and_never_reserved() -> None:
    for field in (FilterField.DEPARTMENT, FilterField.STYLE, FilterField.COLOR):
        terms = [term for entry in VOCAB.entries_for(field) for term in entry.terms()]
        assert len(terms) == len(set(terms))
        assert not set(terms) & (NO_FILTER_TERMS | UNAVAILABLE_TERMS)
    # Rebuilding checks the same rules the constructor enforces.
    rebuilt = Vocabulary(
        VOCAB.version,
        [e for f in FilterField if f is not FilterField.SOURCE for e in VOCAB.entries_for(f)],
    )
    assert repr(rebuilt) == repr(VOCAB)


@pytest.mark.parametrize(
    ("field", "value", "key"),
    [
        (FilterField.DEPARTMENT, "Prints", "cma_prints"),
        (FilterField.DEPARTMENT, "  PRINTS ", "cma_prints"),
        (FilterField.DEPARTMENT, "prints (cleveland)", "cma_prints"),
        (FilterField.DEPARTMENT, "cma_prints", "cma_prints"),
        (
            FilterField.DEPARTMENT,
            "Indian and South East Asian Art",
            "cma_indian_southeast_asian_art",
        ),
        (FilterField.DEPARTMENT, "modern european painting & sculpture (Cleveland)", None),
        (FilterField.DEPARTMENT, "Photography (Cleveland)", "cma_photography"),
        (FilterField.DEPARTMENT, "Performing Arts, Music, & Film", None),
        (FilterField.DEPARTMENT, "Arts of Asia", None),
        (FilterField.STYLE, "19th Century", "period_1800_1899"),
        (FilterField.STYLE, "1800-1899", "period_1800_1899"),
        (FilterField.STYLE, "1800 to 1899", "period_1800_1899"),
        (FilterField.STYLE, "Before 1400", "period_before_1400"),
        (FilterField.STYLE, "up to 1399", "period_before_1400"),
        (FilterField.STYLE, "Since 1900", "period_1900_and_later"),
        (FilterField.STYLE, "20th century and later", "period_1900_and_later"),
        (FilterField.STYLE, "15th and 16th centuries", "period_1400_1599"),
        (FilterField.STYLE, "Impressionism", None),
        (FilterField.COLOR, "Blue", None),
    ],
)
def test_normalization_and_aliases(field: FilterField, value: str, key: str | None) -> None:
    expected = Lookup(LookupStatus.INVALID) if key is None else Lookup(LookupStatus.KEY, key)
    assert VOCAB.lookup(field, value) == expected


@pytest.mark.parametrize("field", [FilterField.DEPARTMENT, FilterField.STYLE, FilterField.COLOR])
@pytest.mark.parametrize("value", ["any", "Any", " none ", "", "random", "all"])
def test_no_filter_terms(field: FilterField, value: str) -> None:
    assert VOCAB.lookup(field, value) == Lookup(LookupStatus.ANY)


# --- VOCABULARY.md -------------------------------------------------------------------------

_ROW = re.compile(
    r"\| `(?P<key>[a-z0-9_]+)` \| (?P<label>[^|]+) \| (?P<aliases>[^|]+) \| (?P<value>[^|]+) \|"
)


def _rows(section: str) -> list[dict[str, str]]:
    text = DOCUMENT.read_text(encoding="utf-8")
    start = text.index(section)
    end = text.find("\n## ", start + len(section))
    body = text[start : len(text) if end == -1 else end]
    return [match.groupdict() for match in _ROW.finditer(body)]


def test_the_document_lists_every_department_exactly() -> None:
    rows = _rows("## Departments")
    assert [row["key"] for row in rows] == list(DEPARTMENTS)
    for row in rows:
        entry = VOCAB.entry(row["key"])
        assert entry is not None
        assert row["label"].strip() == entry.label
        assert row["aliases"].strip() == "; ".join(entry.aliases)
        assert row["value"].strip() == f"`department={DEPARTMENTS[entry.key]}`"


def test_the_document_lists_every_period_exactly() -> None:
    rows = _rows("## Periods")
    assert [row["key"] for row in rows] == list(PERIOD_RANGES)
    for row in rows:
        entry = VOCAB.entry(row["key"])
        assert entry is not None
        assert row["label"].strip() == entry.label
        assert row["aliases"].strip() == "; ".join(entry.aliases)
        period = PERIOD_RANGES[entry.key]
        if period.first is None:
            expected = f"≤ {period.last}"
        elif period.last is None:
            expected = f"≥ {period.first}"
        else:
            expected = f"{period.first}\u2013{period.last}"
        assert row["value"].strip() == expected


def test_the_document_states_the_capability_matrix() -> None:
    text = DOCUMENT.read_text(encoding="utf-8")
    table = text[text.index("## Capability matrix") :]
    names = {
        "Department": FilterDimension.DEPARTMENT,
        "Style": FilterDimension.STYLE,
        "Period": FilterDimension.PERIOD,
        "Colour": FilterDimension.COLOR,
    }
    sources = (
        SourceKey.LOCAL_MEDIA,
        SourceKey.ART_INSTITUTE_CHICAGO,
        SourceKey.CLEVELAND_MUSEUM_OF_ART,
        SourceKey.WIKIMEDIA_COMMONS,
    )
    for name, dimension in names.items():
        match = re.search(rf"^\| {name} \| (.+) \|$", table, re.MULTILINE)
        assert match is not None
        cells = [cell.strip() for cell in match.group(1).split("|")]
        for source, cell in zip(sources, cells, strict=True):
            assert cell.startswith("supported") is (dimension in CAPABILITY_MATRIX[source])
