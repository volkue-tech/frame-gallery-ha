"""Offline tests of review aids; flags are never automatic acceptance."""

import unittest

from research_tools.commons_dossiers import physical, qids
from research_tools.commons_review import artwork_artist, template_names, us_basis
from research_tools.commons_targeted import artist_term


class DossierTests(unittest.TestCase):
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

    def test_verified_aliases_and_explicit_deathyear_only(self):
        for markup in (
            "{{PD-Art|PD-old-100-1923}}",
            "{{PD-Art-two|PD-old-70-expired}}",
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
