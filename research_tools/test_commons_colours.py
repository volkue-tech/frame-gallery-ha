"""Offline pilot tests, separate from the shipped runtime's unchanged gates."""

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from research_tools.commons_colours import aggregate, group, run_worker, selection


class ColourTests(unittest.TestCase):
    def test_basic_families(self):
        for rgb, expected in [
            ((255, 0, 0), "red"),
            ((0, 0, 255), "blue"),
            ((255, 255, 0), "yellow"),
            ((0, 180, 0), "green"),
            ((255, 128, 0), "orange"),
            ((180, 0, 255), "purple"),
            ((255, 160, 210), "pink"),
            ((100, 60, 20), "brown"),
            ((220, 195, 160), "beige"),
            ((110, 110, 110), "gray"),
            ((0, 0, 0), "black"),
            ((255, 255, 255), "white"),
        ]:
            with self.subTest(rgb=rgb):
                self.assertEqual(group(rgb), expected)

    def test_area_and_future_combinations(self):
        result = aggregate(
            [(60, (0, 0, 255)), (30, (255, 255, 0)), (9, (0, 0, 0)), (1, (255, 0, 0))]
        )
        self.assertEqual(result["search_colours"], ["blue", "yellow", "black"])
        self.assertEqual(len(result["distribution"]), 12)
        self.assertAlmostEqual(sum(x["share"] for x in result["distribution"]), 1)
        self.assertEqual(result["distribution"][0]["pixels"], 1)
        self.assertEqual(
            [c["group"] for c in result["top_chromatic_colours"]], ["blue", "yellow"]
        )

    def test_pilot_dark_blue_and_ochre_remain_recognisable(self):
        self.assertEqual(group((13, 27, 109)), "blue")
        self.assertEqual(group((205, 146, 37)), "yellow")
        self.assertEqual(group((172, 111, 28)), "yellow")

    def test_no_three_shades_of_blue_or_invented_colours(self):
        result = aggregate([(50, (0, 0, 255)), (50, (10, 60, 220))])
        self.assertEqual(len(result["top_colours"]), 1)
        self.assertEqual(result["top_colours"][0]["share"], 1)

    def test_order_deterministic_and_bounded(self):
        palette = [(80, (255, 255, 255)), (10, (0, 0, 255)), (10, (255, 255, 0))]
        self.assertEqual(aggregate(palette), aggregate(list(reversed(palette))))
        with self.assertRaises(ValueError):
            aggregate([])
        works = [dict(id=index) for index in range(400)]
        self.assertEqual(len(selection(works, 48)), 48)
        self.assertEqual(len({w["id"] for w in selection(works, 48)}), 48)

    def test_real_child_deterministic_unframed_jpeg(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.jpg"
            image = Image.new("RGB", (512, 288), (0, 0, 255))
            image.paste((255, 255, 0), (0, 0, 256, 288))
            image.save(path, quality=95)
            one = run_worker(path)
            self.assertEqual(one, run_worker(path))
            self.assertEqual(one["dimensions"], [512, 288])
            self.assertEqual(set(one["search_colours"]), {"blue", "yellow"})
            self.assertEqual(json.loads(json.dumps(one)), one)

    def test_child_rejects_png_and_oversize(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.jpg"
            Image.new("RGB", (10, 10)).save(path, format="PNG")
            with self.assertRaises(ValueError):
                run_worker(path)
            Image.new("RGB", (1100, 10)).save(path)
            with self.assertRaises(ValueError):
                run_worker(path)

    def test_palette_neutrals_are_not_discarded(self):
        result = aggregate([(70, (0, 0, 0)), (20, (255, 255, 255)), (10, (0, 0, 255))])
        self.assertEqual(
            [c["group"] for c in result["top_colours"]], ["black", "white", "blue"]
        )
        self.assertEqual(
            [c["group"] for c in result["top_chromatic_colours"]], ["blue"]
        )

    def test_discovery_keeps_width_ratio_and_jpeg_rules(self):
        from research_tools.commons_expand import eligible

        self.assertTrue(eligible(dict(width=3200, height=1800, mime="image/jpeg")))
        self.assertFalse(eligible(dict(width=1600, height=900, mime="image/jpeg")))
        self.assertFalse(eligible(dict(width=3200, height=2000, mime="image/jpeg")))
        self.assertFalse(eligible(dict(width=3200, height=1800, mime="image/png")))
        self.assertFalse(eligible(dict(width=3200, height=0, mime="image/jpeg")))

    def test_real_child_refuses_header_flood_before_pillow(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.jpg"
            Image.new("RGB", (20, 20)).save(path)
            ordinary = path.read_bytes()
            path.write_bytes(ordinary[:2] + b"\xff\xfe\x00\x02" * 1100 + ordinary[2:])
            with self.assertRaises(ValueError):
                run_worker(path)

    def test_research_markup_is_plain_and_non_executable(self):
        from research_tools.commons_review import plain

        self.assertEqual(plain("<b>Paul Klee</b><script>evil()</script>"), "Paul Klee")
        self.assertEqual(
            plain(
                'Painting<span style="display: none"><b>labelQS:Q123</b></span>'
                "<br>Paul Klee"
            ),
            "Painting Paul Klee",
        )
        self.assertEqual(
            plain('Work<span class="labelQS">hidden</span> end'), "Work end"
        )
        self.assertEqual(plain(None), "")
        self.assertEqual(plain("x" * 100001), "")

    def test_pd_art_is_not_us_clearance_without_declared_basis(self):
        from research_tools.commons_review import template_names, us_basis

        self.assertEqual(us_basis(template_names("{{PD-Art}}")), [])
        self.assertEqual(us_basis(template_names("{{PD-old-100}}")), [])
        self.assertEqual(
            us_basis(template_names("{{PD-old-auto-expired}}")), ["pd-old-auto-expired"]
        )
        text = "{{PD-Art|PD-old-auto-expired|deathyear=1935}}"
        self.assertEqual(us_basis(template_names(text), text), ["pd-old-auto-expired"])
        commented = "<!-- {{PD-US-expired}} --><nowiki>{{PD-old-auto-expired}}</nowiki>"
        self.assertEqual(us_basis(template_names(commented), commented), [])

    def test_candidate_evidence_never_accepts_a_work(self):
        from research_tools.commons_review import prepare

        expected = dict(
            id=12,
            file_title="File:Example.jpg",
            sha1="a" * 40,
            width=3200,
            height=1800,
            status="unreviewed",
        )
        page = dict(
            pageid=12,
            ns=6,
            title=expected["file_title"],
            imagerepository="local",
            imageinfo=[
                dict(
                    sha1=expected["sha1"],
                    width=3200,
                    height=1800,
                    mime="image/jpeg",
                    extmetadata={
                        key: {"value": value}
                        for key, value in dict(
                            AttributionRequired="false",
                            Copyrighted="false",
                            LicenseShortName="Public domain",
                            Artist="<b>Artist</b>",
                            ObjectName="Artwork",
                        ).items()
                    },
                )
            ],
            revisions=[
                dict(
                    revid=45,
                    timestamp="2026-10-09",
                    slots={"main": {"content": "{{Artwork}} {{PD-old-auto-expired}}"}},
                )
            ],
        )
        record = prepare(page, expected)
        self.assertEqual(record["reasons"], [])
        self.assertIn("NOT visually accepted", record["status"])
        self.assertEqual(record["artist"], "Artist")
        page["imageinfo"][0]["sha1"] = "b" * 40
        self.assertTrue(prepare(page, expected)["reasons"])
        page["imageinfo"][0]["sha1"] = expected["sha1"]
        page["revisions"][0]["slots"]["main"]["content"] = "{{PD-Art}}"
        self.assertTrue(prepare(page, expected)["reasons"])


if __name__ == "__main__":
    unittest.main()
