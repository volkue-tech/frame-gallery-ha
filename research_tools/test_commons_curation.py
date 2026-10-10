"""Offline count planning must not approve a change to baseline selection."""

from __future__ import annotations

import unittest

from research_tools.commons_curation import catalogue_counts


class CatalogueCountsTests(unittest.TestCase):
    def test_below_target_keeps_nominal_and_unresolved_counts_separate(self) -> None:
        counts = catalogue_counts(400, 592, 56)
        self.assertEqual(counts["local_reviewed_total"], 992)
        self.assertEqual(counts["remaining_additions"], 8)
        self.assertEqual(counts["count_without_unresolved_baseline"], 936)
        self.assertEqual(counts["remaining_without_unresolved_baseline"], 64)
        self.assertEqual(counts["nominal_reserve_count"], 0)

    def test_over_target_has_nonnegative_remaining_and_explicit_reserves(self) -> None:
        counts = catalogue_counts(400, 663, 56)
        self.assertEqual(counts["local_reviewed_total"], 1063)
        self.assertEqual(counts["remaining_additions"], 0)
        self.assertEqual(counts["nominal_reserve_count"], 63)
        self.assertEqual(counts["count_without_unresolved_baseline"], 1007)
        self.assertEqual(counts["remaining_without_unresolved_baseline"], 0)
        self.assertEqual(counts["reserve_without_unresolved_baseline"], 7)
        self.assertEqual(counts["unresolved_baseline_count"], 56)

    def test_exact_target_without_unresolved_cases(self) -> None:
        counts = catalogue_counts(400, 656, 56)
        self.assertEqual(counts["count_without_unresolved_baseline"], 1000)
        self.assertEqual(counts["remaining_without_unresolved_baseline"], 0)
        self.assertEqual(counts["reserve_without_unresolved_baseline"], 0)

    def test_invalid_counts_are_rejected(self) -> None:
        for values in ((-1, 0, 0), (400, -1, 0), (400, 0, -1), (400, 0, 401)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                catalogue_counts(*values)


if __name__ == "__main__":
    unittest.main()
