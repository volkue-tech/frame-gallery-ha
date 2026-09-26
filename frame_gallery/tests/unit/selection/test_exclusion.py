"""The exclusion set (§8.2, §13.6, D-137)."""

from __future__ import annotations

import pytest

from frame_gallery.selection.exclusion import ExclusionSet


def test_an_empty_set_excludes_nothing() -> None:
    exclusions = ExclusionSet()
    assert len(exclusions) == 0
    assert "aic:1001" not in exclusions


@pytest.mark.parametrize("kind", ["history", "uploaded", "uncertain"])
def test_each_set_excludes_its_identifiers(kind: str) -> None:
    exclusions = ExclusionSet(**{kind: frozenset({"aic:1001"})})
    assert "aic:1001" in exclusions
    assert "aic:1002" not in exclusions
    assert "cma:1001" not in exclusions
    assert len(exclusions) == 1


def test_membership_spans_all_three_sets() -> None:
    exclusions = ExclusionSet(
        history=frozenset({"aic:1001"}),
        uploaded=frozenset({"aic:1002"}),
        uncertain=frozenset({"cma:1003"}),
    )
    assert all(qid in exclusions for qid in ("aic:1001", "aic:1002", "cma:1003"))
    assert "aic:1003" not in exclusions


def test_len_counts_the_union_once() -> None:
    exclusions = ExclusionSet(
        history=frozenset({"aic:1001", "aic:1002"}),
        uploaded=frozenset({"aic:1002", "aic:1003"}),
        uncertain=frozenset({"aic:1003", "aic:1001", "local:fp:abc"}),
    )
    assert len(exclusions) == 4


def test_non_string_values_are_not_members() -> None:
    exclusions = ExclusionSet(history=frozenset({"aic:1001"}))
    assert 1001 not in exclusions
    assert None not in exclusions
