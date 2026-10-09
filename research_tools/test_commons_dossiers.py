"""Offline tests of review aids; flags are never automatic acceptance."""

import unittest

from research_tools.commons_dossiers import physical, qids
from research_tools.commons_review import template_names, us_basis


class DossierTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
