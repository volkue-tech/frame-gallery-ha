"""Vocabularies and normalization (§15.2, D-124)."""

from __future__ import annotations

import dataclasses

import pytest

from frame_gallery.config.filters import FilterDimension, FilterField
from frame_gallery.config.vocabulary import (
    BUILTIN_VOCABULARY,
    FIELD_DIMENSIONS,
    LOOKUP_MAX_LENGTH,
    NO_FILTER_TERMS,
    UNAVAILABLE_TERMS,
    Lookup,
    LookupStatus,
    Vocabulary,
    VocabularyEntry,
    field_for,
    normalize_term,
)
from frame_gallery.domain import SourceKey
from tests.unit.config.synthetic import (
    AIC_DEPARTMENT,
    AIC_OTHER_DEPARTMENT,
    CMA_DEPARTMENT,
    COLOR,
    ENTRIES,
    OTHER_STYLE,
    PERIOD,
    STYLE,
    VOCABULARY,
)

AIC = SourceKey.ART_INSTITUTE_CHICAGO
CMA = SourceKey.CLEVELAND_MUSEUM_OF_ART


# -- normalize_term ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Impressionism", "impressionism"),
        ("Arts of Africa", "arts_of_africa"),
        ("Musée d'Orsay", "musee_d_orsay"),
        ("  ANY ", "any"),
        ("", ""),
        ("---", ""),
        ("__a__b__", "a_b"),
        ("Test  Period 1800-1899", "test_period_1800_1899"),
        ("aic_test_paintings", "aic_test_paintings"),
        ("ÉCOLE", "ecole"),
        ("Straße", "strasse"),
        (
            "\uff29\uff2d\uff30\uff32\uff25\uff33\uff33\uff29\uff2f\uff2e",
            "impression",
        ),  # full-width letters
        ("\ufb01ne", "fine"),  # ligature
        ("\u210c", "h"),  # black-letter capital H: cased only after decomposition
        ("x\u0301\u0302y", "xy"),  # stacked combining marks
        ("日本", ""),  # letters outside a-z become separators
        ("tab\tand\nnewline", "tab_and_newline"),
    ],
)
def test_normalize_term(text: str, expected: str) -> None:
    assert normalize_term(text) == expected


def test_normalize_term_is_idempotent() -> None:
    for text in (
        "Musée d'Orsay",
        "  ANY ",
        "Tést Style Two",
        "\uff29\uff2d\uff30\uff32\uff25\uff33\uff33\uff29\uff2f\uff2e",
    ):
        once = normalize_term(text)
        assert normalize_term(once) == once


def test_reserved_terms() -> None:
    assert frozenset({"any", "all", "random", "none", ""}) == NO_FILTER_TERMS
    assert frozenset({"unavailable", "unknown"}) == UNAVAILABLE_TERMS


def test_field_dimensions_and_field_for() -> None:
    assert dict(FIELD_DIMENSIONS) == {
        FilterField.DEPARTMENT: {FilterDimension.DEPARTMENT},
        FilterField.STYLE: {FilterDimension.STYLE, FilterDimension.PERIOD},
        FilterField.COLOR: {FilterDimension.COLOR},
    }
    assert field_for(FilterDimension.DEPARTMENT) is FilterField.DEPARTMENT
    assert field_for(FilterDimension.STYLE) is FilterField.STYLE
    assert field_for(FilterDimension.PERIOD) is FilterField.STYLE
    assert field_for(FilterDimension.COLOR) is FilterField.COLOR


# -- VocabularyEntry --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "dimension", "source"),
    [
        ("aic_test_paintings", FilterDimension.DEPARTMENT, AIC),
        ("cma_test_prints", FilterDimension.DEPARTMENT, CMA),
        ("style_test_one", FilterDimension.STYLE, None),
        ("period_test_1800_1899", FilterDimension.PERIOD, None),
        ("color_test_blue", FilterDimension.COLOR, None),
        ("color_" + "x" * 58, FilterDimension.COLOR, None),  # exactly 64 characters
    ],
)
def test_entry_accepts_namespaced_keys(
    key: str, dimension: FilterDimension, source: SourceKey | None
) -> None:
    entry = VocabularyEntry(key, "A Test Label", dimension, source)
    assert entry.key == key
    assert entry.field is field_for(dimension)


@pytest.mark.parametrize(
    "key",
    [
        "",
        "Aic_test",
        "aic-test",
        "aic test",
        "aic_",
        "_aic_test",
        "aic__test",
        "aic_test_",
        "aïc_test",
        "aic_test\n",
        "aic_" + "x" * 61,  # 65 characters
    ],
)
def test_entry_rejects_malformed_keys(key: str) -> None:
    with pytest.raises(ValueError, match="vocabulary key"):
        VocabularyEntry(key, "A Test Label", FilterDimension.DEPARTMENT, AIC)


@pytest.mark.parametrize(
    ("key", "dimension", "source", "match"),
    [
        ("aic_test", FilterDimension.DEPARTMENT, None, "names its museum"),
        ("local_test", FilterDimension.DEPARTMENT, SourceKey.LOCAL_MEDIA, "names its museum"),
        ("cma_test", FilterDimension.DEPARTMENT, AIC, "must start with 'aic_'"),
        ("aic_test", FilterDimension.DEPARTMENT, CMA, "must start with 'cma_'"),
        ("style_test", FilterDimension.DEPARTMENT, AIC, "must start with 'aic_'"),
        ("style_test", FilterDimension.STYLE, AIC, "only department entries"),
        ("period_test", FilterDimension.STYLE, None, "must start with 'style_'"),
        ("style_test", FilterDimension.PERIOD, None, "must start with 'period_'"),
        ("colour_test", FilterDimension.COLOR, None, "must start with 'color_'"),
        ("color_test", FilterDimension.COLOR, CMA, "only department entries"),
        ("aic_test", FilterDimension.PERIOD, None, "must start with 'period_'"),
    ],
)
def test_entry_rejects_wrong_namespace(
    key: str, dimension: FilterDimension, source: SourceKey | None, match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        VocabularyEntry(key, "A Test Label", dimension, source)


@pytest.mark.parametrize(
    ("label", "match"),
    [
        ("", "non-blank"),
        ("   ", "non-blank"),
        ("x" * 101, "at most 100"),
        ("Any", "reserved"),
        ("  ALL ", "reserved"),
        ("Random", "reserved"),
        ("None", "reserved"),
        ("—", "reserved"),
        ("日本画", "reserved"),
        ("Unknown", "reserved"),
        ("unavailable", "reserved"),
    ],
)
def test_entry_rejects_bad_labels_and_aliases(label: str, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        VocabularyEntry("style_test", label, FilterDimension.STYLE)
    with pytest.raises(ValueError, match=match):
        VocabularyEntry("style_test", "A Test Label", FilterDimension.STYLE, aliases=(label,))


def test_entry_accepts_limit_length_label() -> None:
    entry = VocabularyEntry("style_test", "y" * 100, FilterDimension.STYLE, aliases=("z" * 100,))
    assert len(entry.label) == 100


def test_entry_terms_are_normalized_and_deduplicated() -> None:
    entry = VocabularyEntry(
        "style_test_one",
        "Style Test One",
        FilterDimension.STYLE,
        aliases=("STYLE-TEST-ONE", "Tést Alias", "test alias"),
    )
    assert entry.terms() == ("style_test_one", "test_alias")


def test_entry_is_frozen() -> None:
    entry = ENTRIES[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        entry.key = "aic_other"  # type: ignore[misc]


# -- Lookup -----------------------------------------------------------------------------------


def test_lookup_result_consistency() -> None:
    assert Lookup(LookupStatus.KEY, "style_test_one").key == "style_test_one"
    assert Lookup(LookupStatus.ANY).key is None
    assert Lookup(LookupStatus.INVALID, None).key is None
    with pytest.raises(ValueError, match="exactly when"):
        Lookup(LookupStatus.KEY)
    with pytest.raises(ValueError, match="exactly when"):
        Lookup(LookupStatus.ANY, "style_test_one")
    with pytest.raises(ValueError, match="exactly when"):
        Lookup(LookupStatus.INVALID, "style_test_one")


# -- Vocabulary construction ------------------------------------------------------------------


def test_vocabulary_basics() -> None:
    assert VOCABULARY.version == "test-1"
    assert VOCABULARY.entry(AIC_DEPARTMENT) is ENTRIES[0]
    assert VOCABULARY.entry("aic_missing") is None
    assert VOCABULARY.entry("Test Paintings") is None  # exact keys only
    assert repr(VOCABULARY) == "Vocabulary('test-1', entries=7)"


def test_vocabulary_accepts_any_iterable() -> None:
    vocabulary = Vocabulary("gen", (entry for entry in ENTRIES))
    assert vocabulary.entries_for(FilterField.COLOR) == (ENTRIES[-1],)


@pytest.mark.parametrize("version", ["", "   "])
def test_vocabulary_needs_a_version(version: str) -> None:
    with pytest.raises(ValueError, match="version"):
        Vocabulary(version, ())


def test_vocabulary_rejects_duplicate_keys() -> None:
    first = VocabularyEntry("style_test", "First", FilterDimension.STYLE)
    second = VocabularyEntry("style_test", "Second", FilterDimension.STYLE)
    with pytest.raises(ValueError, match="duplicate vocabulary key 'style_test'"):
        Vocabulary("v", (first, second))


@pytest.mark.parametrize(
    ("first", "second"),
    [
        # Two labels that normalize alike.
        (
            VocabularyEntry("style_a", "Test Label", FilterDimension.STYLE),
            VocabularyEntry("style_b", "TEST-label", FilterDimension.STYLE),
        ),
        # An alias equal to another entry's key.
        (
            VocabularyEntry("style_a", "Label A", FilterDimension.STYLE),
            VocabularyEntry("style_b", "Label B", FilterDimension.STYLE, aliases=("style_a",)),
        ),
        # A style and a period share the style field.
        (
            VocabularyEntry("style_a", "Shared", FilterDimension.STYLE),
            VocabularyEntry("period_a", "Shared", FilterDimension.PERIOD),
        ),
        # Departments of both museums share the department field.
        (
            VocabularyEntry("aic_a", "Photography", FilterDimension.DEPARTMENT, AIC),
            VocabularyEntry("cma_a", "Photography", FilterDimension.DEPARTMENT, CMA),
        ),
        # Two aliases of different entries.
        (
            VocabularyEntry("color_a", "Label A", FilterDimension.COLOR, aliases=("Même",)),
            VocabularyEntry("color_b", "Label B", FilterDimension.COLOR, aliases=("meme",)),
        ),
    ],
)
def test_vocabulary_rejects_ambiguous_terms(
    first: VocabularyEntry, second: VocabularyEntry
) -> None:
    with pytest.raises(ValueError, match="ambiguous"):
        Vocabulary("v", (first, second))


def test_same_term_in_different_fields_is_allowed() -> None:
    department = VocabularyEntry("aic_blue", "Blue", FilterDimension.DEPARTMENT, AIC)
    color = VocabularyEntry("color_blue", "Blue", FilterDimension.COLOR)
    vocabulary = Vocabulary("v", (department, color))
    assert vocabulary.lookup(FilterField.DEPARTMENT, "blue") == Lookup(LookupStatus.KEY, "aic_blue")
    assert vocabulary.lookup(FilterField.COLOR, "blue") == Lookup(LookupStatus.KEY, "color_blue")


def test_an_entry_may_repeat_its_own_terms() -> None:
    entry = VocabularyEntry(
        "style_same", "Style Same", FilterDimension.STYLE, aliases=("style same",)
    )
    assert Vocabulary("v", (entry,)).lookup(FilterField.STYLE, "STYLE SAME").key == "style_same"


# -- entries_for ------------------------------------------------------------------------------


def test_entries_for_each_field_in_vocabulary_order() -> None:
    assert [e.key for e in VOCABULARY.entries_for(FilterField.DEPARTMENT)] == [
        AIC_DEPARTMENT,
        AIC_OTHER_DEPARTMENT,
        CMA_DEPARTMENT,
    ]
    assert [e.key for e in VOCABULARY.entries_for(FilterField.STYLE)] == [
        STYLE,
        OTHER_STYLE,
        PERIOD,
    ]
    assert [e.key for e in VOCABULARY.entries_for(FilterField.COLOR)] == [COLOR]


def test_entries_for_source_is_rejected() -> None:
    with pytest.raises(ValueError, match="lookup_source"):
        VOCABULARY.entries_for(FilterField.SOURCE)


# -- lookup -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "value", "key"),
    [
        (FilterField.DEPARTMENT, AIC_DEPARTMENT, AIC_DEPARTMENT),
        (FilterField.DEPARTMENT, "AIC-TEST-PAINTINGS", AIC_DEPARTMENT),
        (FilterField.DEPARTMENT, "Test Paintings", AIC_DEPARTMENT),
        (FilterField.DEPARTMENT, "  test   paintings  ", AIC_DEPARTMENT),
        (FilterField.DEPARTMENT, "Test Canvas Works", AIC_DEPARTMENT),
        (FilterField.DEPARTMENT, "arts of elsewhere test", AIC_OTHER_DEPARTMENT),
        (FilterField.DEPARTMENT, "Arts of Elsewhere (Test)", AIC_OTHER_DEPARTMENT),
        (FilterField.DEPARTMENT, CMA_DEPARTMENT, CMA_DEPARTMENT),
        (FilterField.DEPARTMENT, "test engravings", CMA_DEPARTMENT),
        (FilterField.DEPARTMENT, "TËST ENGRAVINGS", CMA_DEPARTMENT),
        (FilterField.STYLE, STYLE, STYLE),
        (FilterField.STYLE, "test style two", OTHER_STYLE),
        (FilterField.STYLE, "Tést Style Two", OTHER_STYLE),
        (FilterField.STYLE, "second_test_style", OTHER_STYLE),
        (FilterField.STYLE, PERIOD, PERIOD),
        (FilterField.STYLE, "Test Period 1800\u20131899", PERIOD),
        (FilterField.STYLE, "test nineteenth century", PERIOD),
        (FilterField.COLOR, COLOR, COLOR),
        (FilterField.COLOR, "Test Azure", COLOR),
        (FilterField.COLOR, "\uff34\uff25\uff33\uff34 \uff22\uff2c\uff35\uff25", COLOR),
    ],
)
def test_lookup_finds_keys_labels_and_aliases(field: FilterField, value: str, key: str) -> None:
    assert VOCABULARY.lookup(field, value) == Lookup(LookupStatus.KEY, key)


@pytest.mark.parametrize(
    "value", ["any", "ANY", "  Any ", "all", "Random", "none", "NONE", "", "   ", "-", "—", "_"]
)
@pytest.mark.parametrize("field", [FilterField.DEPARTMENT, FilterField.STYLE, FilterField.COLOR])
def test_lookup_no_filter_terms_mean_any(field: FilterField, value: str) -> None:
    assert VOCABULARY.lookup(field, value) == Lookup(LookupStatus.ANY)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        (FilterField.DEPARTMENT, "aic_test_missing"),
        (FilterField.DEPARTMENT, "Test"),
        (FilterField.DEPARTMENT, STYLE),  # a key of another field
        (FilterField.DEPARTMENT, "Test Blue"),  # a label of another field
        (FilterField.STYLE, AIC_DEPARTMENT),
        (FilterField.STYLE, COLOR),
        (FilterField.COLOR, PERIOD),
        (FilterField.COLOR, "unknown"),
        (FilterField.COLOR, "日本"),  # only letters outside a-z: not "no filter"
        (FilterField.COLOR, "any colour"),
        (FilterField.COLOR, "x" * (LOOKUP_MAX_LENGTH + 1)),
        (FilterField.COLOR, " " * (LOOKUP_MAX_LENGTH + 1)),
    ],
)
def test_lookup_invalid_values(field: FilterField, value: str) -> None:
    assert VOCABULARY.lookup(field, value) == Lookup(LookupStatus.INVALID)


def test_lookup_at_the_length_limit_is_normalized() -> None:
    padded = "Test Blue".center(LOOKUP_MAX_LENGTH)
    assert len(padded) == LOOKUP_MAX_LENGTH
    assert VOCABULARY.lookup(FilterField.COLOR, padded).key == COLOR


def test_lookup_source_field_is_rejected() -> None:
    with pytest.raises(ValueError, match="lookup_source"):
        VOCABULARY.lookup(FilterField.SOURCE, "local_media")


# -- lookup_source ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("local_media", SourceKey.LOCAL_MEDIA),
        ("art_institute_chicago", AIC),
        ("cleveland_museum_of_art", CMA),
        ("Art Institute Chicago", AIC),
        ("  CLEVELAND-MUSEUM-OF-ART ", CMA),
        ("Local Media", SourceKey.LOCAL_MEDIA),
        ("aic", None),
        ("cma", None),
        ("Art Institute of Chicago", None),  # not a source key
        ("any", None),
        ("", None),
        ("unknown", None),
        ("local_media" + " " * LOOKUP_MAX_LENGTH, None),
    ],
)
def test_lookup_source(value: str, expected: SourceKey | None) -> None:
    assert VOCABULARY.lookup_source(value) is expected
    assert BUILTIN_VOCABULARY.lookup_source(value) is expected
