"""Offline tests of review aids; flags are never automatic acceptance."""

import unittest

from research_tools.commons_dossiers import physical, qids
from research_tools.commons_expand import PRECISE_WINDOWS, eligible
from research_tools.commons_resume import validate_screen_range
from research_tools.commons_review import (
    artwork_artist,
    declared_creators,
    preview_priority,
    template_names,
    us_basis,
)
from research_tools.commons_targeted import artist_term


class DossierTests(unittest.TestCase):
    def test_missing_artist_uses_explicit_creators_not_categories(self):
        text = (
            "|artist = {{Creator:Joost de Momper d. J.}} "
            "{{Creator:Jan Brueghel (I)}}\n|title=Summer"
        )
        self.assertEqual(
            declared_creators(text), "Joost de Momper d. J.; Jan Brueghel (I)"
        )
        self.assertEqual(
            declared_creators(
                "|author={{Creator:Uploader}}\n[[Category:Paintings by someone]]"
            ),
            "",
        )
        self.assertEqual(declared_creators("<!-- |artist={{Creator:Hidden}} -->"), "")

    def test_preview_order_is_only_a_research_priority(self):
        self.assertEqual(preview_priority(dict(title="Blue coast", artist="Artist")), 0)
        self.assertEqual(
            preview_priority(dict(title="Blue coast", artist="Unknown artist")), 1
        )
        self.assertEqual(
            preview_priority(dict(title="Drawing, a frieze", artist="Artist")), 2
        )

    def test_inspected_range_never_silently_counts_unseen_choices(self):
        validate_screen_range(16, 32, {16, 31}, 40)
        for start, stop, choices, count in (
            (16, 32, {32}, 40),
            (16, 16, set(), 40),
            (-1, 32, {16}, 40),
            (16, 41, {16}, 40),
        ):
            with self.assertRaises(ValueError):
                validate_screen_range(start, stop, choices, count)

    def test_precise_discovery_windows_do_not_weaken_acceptance(self):
        self.assertEqual(PRECISE_WINDOWS[0][0], 3000)
        self.assertEqual(PRECISE_WINDOWS[-1][1], 20000)
        for previous, current in zip(PRECISE_WINDOWS, PRECISE_WINDOWS[1:]):
            self.assertEqual(previous[1] + 1, current[0])
        self.assertTrue(eligible(dict(width=3840, height=2160, mime="image/jpeg")))
        self.assertFalse(eligible(dict(width=2999, height=1687, mime="image/jpeg")))
        self.assertFalse(eligible(dict(width=3840, height=2500, mime="image/jpeg")))
        self.assertFalse(eligible(dict(width=3840, height=2160, mime="image/png")))

    def test_search_names_drop_biographies_and_keep_person(self):
        self.assertEqual(
            artist_term(
                "Lord Frederic Leighton (1830 - 1896) – creator "
                "Details on Google Art Project"
            ),
            "Lord Frederic Leighton",
        )
        self.assertEqual(artist_term("Creator:Frédéric Houbron"), "Frédéric Houbron")
        self.assertEqual(artist_term("Attributed to Roelof Koets"), "Roelof Koets")

    def test_named_physical_axes_keep_their_meaning(self):
        measures = physical("{{Size|cm|height=90|width=160}}")
        self.assertEqual(measures[0]["ratio"], 160 / 90)
        self.assertEqual(measures[0]["interpretation"], "named height/width")
        self.assertEqual(
            physical("{{Size|cm|height=160|width=90}}")[0]["ratio"], 90 / 160
        )

    def test_unlabelled_axes_are_explicitly_interpreted_not_named(self):
        item = physical("{{Size|cm|57.5|100}}")[0]
        self.assertEqual(item["ratio"], 100 / 57.5)
        self.assertTrue(item["interpretation"].startswith("unlabelled"))
        self.assertEqual(physical("{{Size|cm|57.5|100|200}}"), [])
        self.assertEqual(physical("{{Size|cm|width=0|height=10}}"), [])

    def test_artwork_qids_not_property_fragments_or_query_prefixes(self):
        self.assertEqual(
            qids('href="https://www.wikidata.org/wiki/Q123#P1476"'), {"Q123"}
        )
        self.assertEqual(qids('href="https://www.wikidata.org/wiki/Q456"'), {"Q456"})
        self.assertEqual(qids('href="https://www.wikidata.org/wiki/Q1234?x=1"'), set())

    def test_plain_museum_dimensions_preserve_conflicting_scopes(self):
        values = physical("|dimensions = Sheet: 39.5 x 57 cm; Image: 30.6 x 53.3 cm\n")
        self.assertEqual(len(values), 2)
        self.assertAlmostEqual(values[0]["ratio"], 57 / 39.5)
        self.assertAlmostEqual(values[1]["ratio"], 53.3 / 30.6)
        values = physical("|pretty_dimensions = w970 x h550 mm\n")
        self.assertEqual(values[0]["interpretation"], "explicit w/h plain dimensions")
        self.assertEqual(values[0]["ratio"], 970 / 550)
        self.assertEqual(
            physical("|Description={{de|28 × 46,5 cm.}}\n|Source=example")[0]["ratio"],
            46.5 / 28,
        )
        self.assertAlmostEqual(
            physical("|core:format={{en|w26 x h14.5 cm (Without frame)}}\n")[0][
                "ratio"
            ],
            26 / 14.5,
        )
        self.assertEqual(
            physical("|core:format={{en|w97,0 x h55,0 mm}}\n")[0]["ratio"],
            97 / 55,
        )

    def test_verified_aliases_and_explicit_deathyear_only(self):
        for markup in (
            "{{PD-Art|PD-old-100-1923}}",
            "{{PD-Art-two|PD-old-70-expired}}",
            "{{PD-Art|PD-old-70-1923}}",
            "{{PD-Art|PD-old-auto-1923|deathyear=1925}}",
            "{{PD-art-old-100-expired}}",
            "{{PD-Art-two-auto|deathyear=1930}}",
        ):
            self.assertTrue(us_basis(template_names(markup), markup))
        for markup in (
            "{{PD-Art}}",
            "{{PD-Art-two-auto}}",
            "{{PD-Art-two-auto|deathyear=9999}}",
            "<!-- {{PD-Art|PD-old-100-1923}} -->",
        ):
            self.assertEqual(us_basis(template_names(markup), markup), [])

    def test_dutch_museum_axes_are_not_ignored_or_reversed(self):
        values = physical("|Description=Afmetingen: h 138 mm × b 254 mm\n|Date=1880")
        self.assertEqual(values[0]["ratio"], 254 / 138)
        values = physical(
            "|Description=drager: h 54,7 cm. × b 976 mm × d 1,9 cm\n|Date=1626"
        )
        self.assertAlmostEqual(values[0]["ratio"], 976 / 547)
        self.assertEqual(physical("|Description=h 0 mm × b 100 mm\n|Date=1626"), [])

    def test_museum_upload_credit_is_not_artwork_artist(self):
        description = (
            "<b>Vervaardiger:</b> tekenaar: Henri Joseph Harpignies<br>"
            "<b>Datering:</b> 1861"
        )
        self.assertEqual(
            artwork_artist("Rijksmuseum", description), "Henri Joseph Harpignies"
        )
        self.assertEqual(
            artwork_artist("Rijksmuseum", "no explicit maker"),
            "Artist not identified (Rijksmuseum source)",
        )
        self.assertEqual(artwork_artist("Other museum", description), "Other museum")


if __name__ == "__main__":
    unittest.main()
