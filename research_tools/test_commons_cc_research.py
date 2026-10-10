"""Synthetic CC research tests; production admission is deliberately unchanged."""

import copy
import unittest

from research_tools.commons_cc_research import (
    assess,
    cc_card,
    notice_text,
    preview_pilot,
    self_licences,
)


class CCResearchTests(unittest.TestCase):
    def setUp(self):
        self.expected = dict(
            id=1,
            file_title="File:Independent digital art.jpg",
            sha1="a" * 40,
            source="https://commons.wikimedia.org/wiki/File:Independent_digital_art.jpg",
        )
        metadata = {
            key: {"value": value}
            for key, value in dict(
                LicenseShortName="CC BY-SA 4.0",
                AttributionRequired="true",
                Copyrighted="True",
                Restrictions="",
                Artist="Example creator",
                ObjectName="Independent composition",
                ImageDescription="Original digital art.",
                LicenseUrl="https://creativecommons.org/licenses/by-sa/4.0/",
                Credit="Specific supplied credit",
                UsageTerms="Specific supplied terms",
                Disclaimer="Specific supplied disclaimer",
            ).items()
        }
        self.page = dict(
            pageid=1,
            ns=6,
            title=self.expected["file_title"],
            imagerepository="local",
            imageinfo=[
                dict(
                    sha1="a" * 40,
                    width=3840,
                    height=2160,
                    mime="image/jpeg",
                    extmetadata=metadata,
                )
            ],
            revisions=[
                dict(
                    revid=42,
                    slots={
                        "main": {
                            "content": "{{Information\n|source={{own}}\n"
                            "|author=Example creator\n}}\n"
                            "{{self|cc-by-sa-4.0}}"
                        }
                    },
                )
            ],
        )

    def test_original_declaration_is_only_preview_lead(self):
        row = assess(self.page, self.expected)
        self.assertEqual(row["preview_blockers"], [])
        self.assertIn("NOT accepted", row["status"])
        self.assertTrue(row["share_alike"])
        self.assertTrue(row["modification_notice_required"])
        self.assertEqual(row["attribution"]["Credit"], "Specific supplied credit")
        self.assertEqual(
            row["supplied_rights_metadata"], self.page["imageinfo"][0]["extmetadata"]
        )
        self.assertEqual(row["source_revision"], 42)
        self.assertEqual(len(row["source_page_sha256"]), 64)
        self.assertTrue(any("artwork itself" in x for x in row["review_prompts"]))

    def test_by_is_not_share_alike(self):
        page = copy.deepcopy(self.page)
        page["revisions"][0]["slots"]["main"]["content"] = (
            "{{Information\n|source={{own}}\n}}\n{{self|cc-by-4.0}}"
        )
        for key, value in (
            ("LicenseShortName", "CC BY 4.0"),
            ("LicenseUrl", "https://creativecommons.org/licenses/by/4.0"),
        ):
            page["imageinfo"][0]["extmetadata"][key]["value"] = value
        row = assess(page, self.expected)
        self.assertEqual(row["preview_blockers"], [])
        self.assertFalse(row["share_alike"])

    def test_supplied_notice_after_display_limit_is_not_lost(self):
        text = "prefix " * 400 + "Specific retained disclaimer"
        page = copy.deepcopy(self.page)
        page["imageinfo"][0]["extmetadata"]["Permission"] = {
            "value": "<div>" + text + "</div>"
        }
        row = assess(page, self.expected)
        self.assertEqual(row["attribution"]["Permission"], text)
        self.assertTrue(notice_text(text).endswith("Specific retained disclaimer"))
        self.assertEqual(notice_text(None), "")
        self.assertEqual(notice_text("x" * 100001), "")

    def test_matching_older_licence_still_needs_version_review(self):
        page = copy.deepcopy(self.page)
        page["revisions"][0]["slots"]["main"]["content"] = (
            "{{Information\n|source={{own}}\n}}\n{{self|cc-by-sa-3.0}}"
        )
        for key, value in (
            ("LicenseShortName", "CC BY-SA 3.0"),
            ("LicenseUrl", "https://creativecommons.org/licenses/by-sa/3.0/"),
        ):
            page["imageinfo"][0]["extmetadata"][key]["value"] = value
        row = assess(page, self.expected)
        self.assertEqual(row["licence_version"], "3.0")
        self.assertIn(
            "version 3.0 obligations require separate source review",
            row["preview_blockers"],
        )

    def test_preview_card_escapes_notices_and_labels_reserve(self):
        source = assess(self.page, self.expected)
        source["title"] = '<img src=x onerror="alert(1)">'
        source["creator"] = "A & B"
        source["attribution"]["Permission"] = "<script>untrusted</script>"
        card = cc_card(dict(id=1, top_colours=[]), source)
        self.assertIn("Vorgemerkt, noch nicht aufgenommen", card)
        self.assertIn("A &amp; B", card)
        self.assertIn("&lt;script&gt;untrusted&lt;/script&gt;", card)
        self.assertNotIn("<script>", card)
        self.assertIn("https://commons.wikimedia.org/w/index.php?curid=1", card)
        self.assertIn("https://creativecommons.org/licenses/by-sa/4.0/", card)
        self.assertIn("kein absichtlicher Beschnitt", card)

    def test_preview_card_invalid_links_and_identity_fail(self):
        source = assess(self.page, self.expected)
        for key, value in (
            ("id", 2),
            ("licence_url", "javascript:alert(1)"),
            ("licence_url", "https://creativecommons.org/licenses/by-sa/3.0/"),
        ):
            with self.subTest(key=key, value=value):
                changed = dict(source, **{key: value})
                with self.assertRaises(ValueError):
                    cc_card(dict(id=1, top_colours=[]), changed)

    def test_comments_literals_named_nested_fields_not_licences(self):
        for text in (
            "<!--{{self|cc-by-sa-4.0}}-->",
            "<nowiki>{{self|cc-by-sa-4.0}}</nowiki>",
            "{{self|author=cc-by-sa-4.0}}",
            "{{self|author={{cc-by-sa-4.0}}}}",
            "{{self|7=cc-by-sa-4.0}}",
            "{{self|cc-by-nc-4.0|cc-by-nd-4.0}}",
        ):
            with self.subTest(text=text):
                self.assertEqual(self_licences(text), set())
        self.assertEqual(
            self_licences("{{self|cc-by-4.0|2=cc-by-sa-4.0}}"),
            {"cc-by-4.0", "cc-by-sa-4.0"},
        )

    def test_mismatch_restrictions_redirect_licences_refused(self):
        for key, value in (
            ("LicenseShortName", "CC BY 4.0"),
            ("LicenseUrl", "https://creativecommons.org.evil/licenses/by-sa/4.0/"),
            ("LicenseUrl", "https://creativecommons.org/licenses/by-sa/4.0/?x=1"),
            ("Restrictions", "personality rights"),
            ("AttributionRequired", None),
            ("Copyrighted", "False"),
            ("Artist", ""),
        ):
            with self.subTest(key=key, value=value):
                page = copy.deepcopy(self.page)
                page["imageinfo"][0]["extmetadata"][key]["value"] = value
                self.assertTrue(assess(page, self.expected)["preview_blockers"])

    def test_third_party_creation_and_art_photo_not_cleared(self):
        for description in (
            "Part of the images can base on already existed FRACT files.",
            "Based on someone else's artwork",
            "Photo of an installation by Kusama",
            "Machine Hallucinations by Refik Anadol",
        ):
            with self.subTest(description=description):
                page = copy.deepcopy(self.page)
                page["imageinfo"][0]["extmetadata"]["ImageDescription"]["value"] = (
                    description
                )
                self.assertIn(
                    "declared/possible third-party underlying work",
                    assess(page, self.expected)["preview_blockers"],
                )
        page = copy.deepcopy(self.page)
        page["revisions"][0]["slots"]["main"]["content"] += "\n{{Art Photo}}"
        self.assertIn(
            "separate depicted-work/reproduction scope",
            assess(page, self.expected)["preview_blockers"],
        )

    def test_literal_flower_photography_not_a_derivative_artwork(self):
        page = copy.deepcopy(self.page)
        field = page["imageinfo"][0]["extmetadata"]["ImageDescription"]
        field["value"] = (
            "Photographic art based on garden flowers (Agapanthus) in a garden."
        )
        self.assertEqual(assess(page, self.expected)["preview_blockers"], [])
        field["value"] += " Adapted from someone else's artwork."
        self.assertIn(
            "declared/possible third-party underlying work",
            assess(page, self.expected)["preview_blockers"],
        )

    def test_missing_own_source_and_changed_pins_fail(self):
        for mutation in ("source", "sha1", "format", "revision"):
            with self.subTest(mutation=mutation):
                page = copy.deepcopy(self.page)
                if mutation == "source":
                    page["revisions"][0]["slots"]["main"]["content"] = (
                        "{{self|cc-by-sa-4.0}}"
                    )
                elif mutation == "sha1":
                    page["imageinfo"][0]["sha1"] = "b" * 40
                elif mutation == "format":
                    page["imageinfo"][0]["height"] = 3840
                else:
                    page["revisions"] = []
                self.assertTrue(assess(page, self.expected)["preview_blockers"])

    def test_malformed_source_fields_do_not_clear_or_crash(self):
        for key, value in (
            ("revisions", [42]),
            ("revisions", None),
            ("imageinfo", None),
            ("revisions", [{"revid": 42, "slots": {"main": 7}}]),
        ):
            with self.subTest(key=key, value=value):
                page = copy.deepcopy(self.page)
                page[key] = value
                self.assertTrue(assess(page, self.expected)["preview_blockers"])
        page = copy.deepcopy(self.page)
        page["imageinfo"][0]["extmetadata"] = []
        self.assertTrue(assess(page, self.expected)["preview_blockers"])

    def test_fop_and_pd_art_are_separate_underlying_scope(self):
        for template in ("{{FoP}}", "{{FoP-India}}", "{{PD-Art|PD-old}}"):
            with self.subTest(template=template):
                page = copy.deepcopy(self.page)
                page["revisions"][0]["slots"]["main"]["content"] += template
                self.assertIn(
                    "separate depicted-work/reproduction scope",
                    assess(page, self.expected)["preview_blockers"],
                )

    def test_preview_pilot_limits_scope_authors_and_does_not_mutate(self):
        records = [
            dict(
                id=i,
                creator="same" if i < 6 else "other",
                preview_blockers=["needs review"] if i == 7 else [],
            )
            for i in range(10)
        ]
        original = copy.deepcopy(records)
        rows = preview_pilot(records, {1}, {"same": 1}, set(range(9)), 5, 3)
        self.assertEqual([r["id"] for r in rows], [0, 2, 6, 8])
        self.assertEqual(records, original)
        self.assertEqual(
            len(preview_pilot(records, set(), {}, set(range(10)), 1, 25)), 1
        )
        self.assertEqual(preview_pilot(records, set(), {}, set(), 10, 25), [])

    def test_preview_pilot_rejects_unbounded_pass(self):
        for limit, cap in ((0, 12), (101, 12), (30, 0), (30, 26)):
            with self.subTest(limit=limit, cap=cap):
                with self.assertRaises(ValueError):
                    preview_pilot([], set(), {}, set(), limit, cap)


if __name__ == "__main__":
    unittest.main()
