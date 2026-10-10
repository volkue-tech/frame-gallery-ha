"""Offline profile audit regression tests using a small synthetic palette."""

from __future__ import annotations

import copy
import unittest

from research_tools.commons_colours import METHOD, aggregate
from research_tools.commons_expansion_audit import verify_profile


class ExpansionAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.work = dict(
            id=1,
            sha1="source-pin",
            source_revision=123,
            source_page_sha256="source-markup",
            thumbnail_sha256="preview-pin",
        )
        self.profile = dict(
            **aggregate([(8, (0, 0, 255)), (2, (255, 255, 0))]),
            id=1,
            original_sha1="source-pin",
            method=METHOD,
            source_revision=123,
            source_page_sha256="source-markup",
            thumbnail_sha256="preview-pin",
        )

    def test_complete_profile_matches_original_pin_and_source_evidence(self) -> None:
        verify_profile(self.profile, self.work, True)
        verify_profile(self.profile, self.work, False)

    def test_rejects_changed_identity_pin_method_or_source(self) -> None:
        for key in (
            "id",
            "original_sha1",
            "method",
            "source_revision",
            "source_page_sha256",
            "thumbnail_sha256",
        ):
            profile = copy.deepcopy(self.profile)
            profile[key] = "changed"
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_profile(profile, self.work, True)

    def test_rejects_changed_area_top_groups_and_search_colours(self) -> None:
        for key in ("sample_pixels", "distribution", "top_colours", "search_colours"):
            profile = copy.deepcopy(self.profile)
            profile[key] = None
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_profile(profile, self.work, True)

    def test_rejects_oversized_palette(self) -> None:
        profile = copy.deepcopy(self.profile)
        profile["palette"] *= 65
        with self.assertRaises(ValueError):
            verify_profile(profile, self.work, True)


if __name__ == "__main__":
    unittest.main()
