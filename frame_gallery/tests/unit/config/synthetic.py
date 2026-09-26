"""A synthetic vocabulary for the configuration tests.

Every key, label, and alias is invented; the real vocabularies are fixed in
Phase 3 (Q-14).
"""

from __future__ import annotations

from frame_gallery.config.filters import FilterDimension
from frame_gallery.config.vocabulary import Vocabulary, VocabularyEntry
from frame_gallery.domain import SourceKey

AIC_DEPARTMENT = "aic_test_paintings"
AIC_OTHER_DEPARTMENT = "aic_test_arts_of_elsewhere"
CMA_DEPARTMENT = "cma_test_prints"
STYLE = "style_test_one"
OTHER_STYLE = "style_test_two"
PERIOD = "period_test_1800_1899"
COLOR = "color_test_blue"

ENTRIES = (
    VocabularyEntry(
        AIC_DEPARTMENT,
        "Test Paintings",
        FilterDimension.DEPARTMENT,
        SourceKey.ART_INSTITUTE_CHICAGO,
        aliases=("Test Canvas Works",),
    ),
    VocabularyEntry(
        AIC_OTHER_DEPARTMENT,
        "Arts of Elsewhere (Test)",
        FilterDimension.DEPARTMENT,
        SourceKey.ART_INSTITUTE_CHICAGO,
    ),
    VocabularyEntry(
        CMA_DEPARTMENT,
        "Test Prints",
        FilterDimension.DEPARTMENT,
        SourceKey.CLEVELAND_MUSEUM_OF_ART,
        aliases=("Tëst Engravings",),
    ),
    VocabularyEntry(STYLE, "Test Style One", FilterDimension.STYLE),
    VocabularyEntry(
        OTHER_STYLE, "Tést Style Two", FilterDimension.STYLE, aliases=("Second Test Style",)
    ),
    VocabularyEntry(
        PERIOD,
        "Test Period 1800-1899",
        FilterDimension.PERIOD,
        aliases=("Test Nineteenth Century",),
    ),
    VocabularyEntry(COLOR, "Test Blue", FilterDimension.COLOR, aliases=("Test Azure",)),
)

VOCABULARY = Vocabulary("test-1", ENTRIES)
