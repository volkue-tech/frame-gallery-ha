"""Offline tests of review aids; flags are never automatic acceptance."""

import hashlib
import json
import unittest

from research_tools.commons_baseline_audit import (
    verify_decision,
    verify_render_evidence,
)
from research_tools.commons_dossiers import (
    declared_artwork_qids,
    physical,
    qids,
    scoped_measures,
    separate_attribution_declaration,
)
from research_tools.commons_expand import (
    GENRE_SUBJECT,
    HIGH_RES_WINDOWS,
    MEDIA_SUBJECT,
    PRECISE_WINDOWS,
    SINGLE_SUBJECTS,
    busy_refusal,
    eligible,
)
from research_tools.commons_resume import validate_screen_range
from research_tools.commons_review import (
    artwork_artist,
    declared_creators,
    preview_candidates,
    preview_priority,
    research_pool,
    sheet_offsets,
    source_artist,
    source_title,
    template_names,
    us_basis,
)
from research_tools.commons_targeted import artist_term


class DossierTests(unittest.TestCase):
    def test_subject_measurement_scope_is_exactly_bound_and_preserves_other_axes(self):
        work = dict(
            id=1, sha1="original", source_revision=2, source_page_sha256="source"
        )
        profile = dict(thumbnail_sha256="preview")
        measures = [
            dict(raw="crystals 10 x 10 mm", ratio=1),
            dict(raw="canvas", ratio=1.8),
        ]
        decision = dict(
            id=1,
            original_sha1="original",
            source_revision=2,
            source_page_sha256="source",
            thumbnail_sha256="preview",
            measurements_sha256=hashlib.sha256(
                json.dumps(measures, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest(),
            excluded_measurement_indices=[0],
            scope="photographed subject, not photographic composition",
            reason="Actual source gives crystal size, not camera-image size",
            limits="This explicit decision is not approval",
        )
        self.assertEqual(
            scoped_measures(work, profile, measures, decision), measures[1:]
        )
        self.assertEqual(len(measures), 2)
        for key in (
            "id",
            "original_sha1",
            "source_revision",
            "source_page_sha256",
            "thumbnail_sha256",
            "measurements_sha256",
            "scope",
            "reason",
            "limits",
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                scoped_measures(work, profile, measures, dict(decision, **{key: ""}))
        for indices in (None, [], [True], [0, 0], [-1], [2], [0.0], "0"):
            with self.subTest(indices=indices), self.assertRaises(ValueError):
                scoped_measures(
                    work,
                    profile,
                    measures,
                    dict(decision, excluded_measurement_indices=indices),
                )
        with self.assertRaises(ValueError):
            scoped_measures(
                work, profile, measures + [dict(raw="new", ratio=2)], decision
            )

    def test_incremental_contact_sheets_keep_absolute_positions(self):
        self.assertEqual(list(sheet_offsets(33, 1)), [16, 32])
        self.assertEqual(list(sheet_offsets(32, 2)), [])
        self.assertEqual(list(sheet_offsets(0, 0)), [])
        for value in (-1, True, 1.5, "1", 3):
            with self.subTest(value=value), self.assertRaises(ValueError):
                sheet_offsets(33, value)
        for count in (-1, True, 1.5):
            with self.subTest(count=count), self.assertRaises(ValueError):
                sheet_offsets(count, 0)

    def test_baseline_board_preview_is_bound_to_source_and_original_hash(self):
        record = dict(id=42, original_sha1="source")
        profile = dict(record, thumbnail_sha256="preview")
        verify_render_evidence(record, profile, "preview")
        for key in profile:
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_render_evidence(
                    record, dict(profile, **{key: "other"}), "preview"
                )
        with self.assertRaises(ValueError):
            verify_render_evidence(record, profile, "other-preview")

    def test_dutch_labelled_support_axes_do_not_use_object_depth(self):
        text = (
            "|Description={{nl|Afmetingen: drager: hoogte ca. 39,6 cm. × "
            "breedte ca. 71,8 cm. × dikte 1,0 cm. buitenmaat: diepte 5,2 cm.}}"
        )
        values = physical(text)
        self.assertEqual(len(values), 1)
        self.assertAlmostEqual(values[0]["ratio"], 71.8 / 39.6)
        self.assertIn("drager:", values[0]["raw"])
        self.assertAlmostEqual(
            physical("|description=hoogte 30 cm × breedte 535 mm")[0]["ratio"],
            535 / 300,
        )
        self.assertEqual(physical("|description=hoogte 0 cm × breedte 71 cm"), [])
        self.assertEqual(physical("|description=hoogte 30 cm × diepte 53 cm"), [])

    def test_rijks_maker_stops_before_separate_creation_place(self):
        text = (
            "Vervaardiger: schilder: Hercules Segers Plaats vervaardiging: "
            "Amsterdam (mogelijk) Datering: ca. 1626 - ca. 1630"
        )
        self.assertEqual(artwork_artist("Rijksmuseum", text), "Hercules Segers")

    def test_rijks_commissioner_is_not_part_of_qualified_maker(self):
        text = (
            "Vervaardiger: schilder: Reinier Nooms (eigenhandig gesigneerd)"
            "opdrachtgever: Admiraliteit van Amsterdam Plaats vervaardiging: "
            "Amsterdam Datering: 1662 - 1668"
        )
        self.assertEqual(
            artwork_artist("Rijksmuseum", text),
            "Reinier Nooms (eigenhandig gesigneerd)",
        )

    def test_technical_met_identifier_uses_only_bounded_explicit_caption(self):
        caption = 'Camellia Flower and <a href="https://example.org">Yōkan</a>'
        self.assertEqual(
            source_title("MET DP139008", caption, "fallback"),
            "Camellia Flower and Yōkan",
        )
        self.assertEqual(
            source_title("A real title", caption, "fallback"), "A real title"
        )
        for value in ("x" * 101, "https://example.org/caption", "{{caption}}"):
            self.assertEqual(
                source_title("MET DP139008", value, "fallback"), "MET DP139008"
            )

    def test_targeted_preview_pool_keeps_bounds_flags_and_completed_work(self):
        def work(work_id, reasons):
            return dict(id=work_id, reasons=reasons, title="Painting", artist="Maker")

        records = [
            work(1, []),
            work(2, ["rights unresolved"]),
            work(3, []),
            work(4, []),
        ]
        self.assertEqual(
            [w["id"] for w in preview_candidates(records, {3}, 10, {2, 3, 4})], [4]
        )
        self.assertEqual([w["id"] for w in preview_candidates(records, set(), 1)], [1])
        self.assertEqual(preview_candidates(records, set(), 1, set()), [])
        self.assertEqual(len(records), 4)  # Other retained pools are not removed.
        for limit in (0, 601):
            with self.assertRaises(ValueError):
                preview_candidates(records, set(), limit)

    def test_attribution_scope_does_not_depend_on_art_photo_template(self):
        for kind in ("Art Photo", "Artwork", "Information"):
            self.assertTrue(
                separate_attribution_declaration(
                    "{{" + kind + "|source={{own}}}}\n"
                    "{{PD-Art|PD-old-auto-expired|deathyear=1892}}"
                    "{{self|cc-by-sa-4.0}}"
                )
            )
        self.assertTrue(separate_attribution_declaration("{{Cc-by-4.0}}"))
        for text in (
            "{{PD-Art|PD-old-100-expired}} {{PD-self}}",
            "{{cc-zero}}",
            "<!-- {{self|cc-by-sa-4.0}} -->",
            "<nowiki>{{Cc-by-4.0}}</nowiki>",
            "A licence called cc-by-sa-4.0 is discussed, not declared.",
        ):
            self.assertFalse(separate_attribution_declaration(text))

    def test_self_attribution_checks_every_positional_licence_not_named_values(self):
        for text in (
            "{{self|CeCILL|Cc-by-sa-2.0-fr}}",
            "{{Self|author={{Creator:Example}}|CC0|Cc-by-4.0}}",
            "{{self|cc-zero|GFDL|cc-by-sa-3.0}}",
        ):
            self.assertTrue(separate_attribution_declaration(text))
        for text in (
            "{{self|CC0|author=cc-by-sa-4.0}}",
            "{{self|CC0|author={{Creator:cc-by-sa-4.0}}}}",
            "{{self|CC0}} cc-by-sa-4.0",
            "<!-- {{self|CeCILL|cc-by-sa-2.0-fr}} -->",
            "<pre>{{self|CeCILL|cc-by-sa-2.0-fr}}</pre>",
        ):
            self.assertFalse(separate_attribution_declaration(text))

    def test_explicit_unitless_dutch_measurements_are_not_invented_or_ignored(self):
        values = physical("|description={{nl|Afmetingen: 170 x 290}}\n|date=1650")
        self.assertEqual(len(values), 1)
        self.assertAlmostEqual(values[0]["ratio"], 290 / 170)
        self.assertIn("units unspecified", values[0]["interpretation"])
        self.assertEqual(physical("|description=170 x 290\n|date=1650"), [])
        self.assertEqual(physical("|description=Afmetingen: 0 x 290\n}}"), [])
        self.assertEqual(physical("|description=Afmetingen: 170 x 290 x 20\n}}"), [])
        self.assertEqual(len(physical("|description=Afmetingen: 170 x 290 cm\n}}")), 1)

    def test_retained_pool_selector_never_accepts_an_arbitrary_path(self):
        self.assertIsNone(research_pool(None))
        self.assertEqual(research_pool("targeted"), "discovery-targeted.json")
        for name in ("", "../source", "/source", "new-provider", "cc-by"):
            with self.assertRaises(ValueError):
                research_pool(name)

    def test_subject_pools_only_map_exact_known_discovery_names(self):
        for name in SINGLE_SUBJECTS:
            self.assertEqual(research_pool(name), f"discovery-subject-{name}.json")
        for name in (
            "lithograph.json",
            "subject-lithograph",
            "Lithograph",
            "../lithograph",
        ):
            with self.assertRaises(ValueError):
                research_pool(name)

    def test_artwork_identity_excludes_nested_maker_and_source_ids(self):
        text = (
            "{{Artwork\n|artist={{Creator|wikidata=Q123}}\n"
            "|source={{Information|wikidata=Q456}}\n|wikidata=Q789\n}}"
        )
        self.assertEqual(declared_artwork_qids(text), {"Q789"})
        self.assertEqual(
            declared_artwork_qids("{{Art Photo|artist={{Creator|wikidata=Q123}}}}"),
            set(),
        )
        self.assertEqual(
            declared_artwork_qids("{{Artwork|artist=Maker|wikidata=Q456}}"), {"Q456"}
        )
        self.assertEqual(
            declared_artwork_qids("{{Artwork|wikidata=Q456 additional text}}"), set()
        )
        for text in (
            "<!-- {{Artwork|wikidata=Q123}} -->",
            "<nowiki>{{Artwork|wikidata=Q123}}</nowiki>",
            "{{Information|wikidata=Q123}}",
        ):
            self.assertEqual(declared_artwork_qids(text), set())

    def test_explicit_pd_self_is_a_release_declaration_not_artwork_clearance(self):
        source = "{{Information|source={{Own}}}}\n{{PD-self}}"
        self.assertEqual(us_basis(template_names(source), source), ["pd-self"])
        for source in (
            "<!-- {{PD-self}} -->",
            "<nowiki>{{PD-self}}</nowiki>",
            "|author=PD-self",
            "{{PD-author}}",
        ):
            self.assertEqual(us_basis(template_names(source), source), [])

    def test_explicit_art_photo_caption_distinguishes_maker(self):
        text = "{{Art Photo\n|artist = \n|photographer = [[User:Photo|Photo]]\n}}"
        caption = (
            "A coastal painting, by Named Maker, 1864-1865, oil on canvas - Museum."
        )
        self.assertEqual(source_artist("Photo", caption, text), "Named Maker")
        self.assertEqual(source_artist("Other", caption, text), "Other")
        self.assertEqual(
            source_artist(
                "Photo",
                caption,
                text.replace("|artist = \n", "|artist = Explicit Maker\n"),
            ),
            "Photo",
        )
        self.assertEqual(
            source_artist("Photo", caption, text.replace("Art Photo", "Information")),
            "Photo",
        )
        self.assertEqual(
            source_artist("Photo", "A painting, maker not supplied", text), "Photo"
        )

    def test_camera_title_uses_only_short_explicit_caption(self):
        self.assertEqual(
            source_title("20050900 DSCN1173a", "sunflowers in a glass", "fallback"),
            "sunflowers in a glass",
        )
        self.assertEqual(
            source_title("DSC1173.jpg", "Sunflowers", "fallback"), "Sunflowers"
        )
        self.assertEqual(
            source_title("Named Artwork", "a different caption", "fallback"),
            "Named Artwork",
        )
        for caption in (
            "",
            "https://example.invalid",
            "x" * 101,
            "{{Unresolved}}",
            "[[Creator:Someone]]",
        ):
            self.assertEqual(source_title("IMG1173", caption, "fallback"), "IMG1173")
        self.assertEqual(
            source_title(None, "description", "Untitled study"), "Untitled study"
        )

    def test_named_size_decimal_commas_do_not_hide_portrait_measurements(self):
        values = physical("{{Size|unit=cm|width=12,4|height=22,9}}")
        self.assertEqual(len(values), 1)
        self.assertAlmostEqual(values[0]["ratio"], 12.4 / 22.9)

    def test_explicit_height_width_single_axis_size_templates_are_combined(self):
        values = physical(
            "|dimensions=drager '''Height:''' {{size|cm|35}} "
            "drager '''Width:''' {{size|cm|55}}\n}}"
        )
        self.assertEqual(len(values), 1)
        self.assertAlmostEqual(values[0]["ratio"], 55 / 35)
        self.assertGreater(abs(values[0]["ratio"] / (16 / 9) - 1), 0.025)

    def test_english_height_width_parenthesized_metric_axes_are_not_lost(self):
        values = physical(
            "|dimensions=H. 6 5/8 in. (16.8 cm); W. 12 1/4 in. (31.1 cm)\n"
            "|institution=Test museum\n}}"
        )
        self.assertEqual(len(values), 1)
        self.assertAlmostEqual(values[0]["ratio"], 31.1 / 16.8)
        self.assertGreater(abs(values[0]["ratio"] / (16 / 9) - 1), 0.025)

    def test_english_metric_axes_preserve_panel_and_frame_scopes(self):
        values = physical(
            "|dimensions=Each Height 389 mm; Width 24.4 cm\n"
            "Frame H. 40 cm; W. 70 cm\n|institution=Test museum\n}}"
        )
        self.assertEqual(len(values), 2)
        self.assertAlmostEqual(values[0]["ratio"], 244 / 389)
        self.assertAlmostEqual(values[1]["ratio"], 1.75)
        self.assertIn("Each", values[0]["raw"])
        self.assertIn("Frame", values[1]["raw"])

    def test_ambiguous_multiple_metric_values_are_not_picked_to_fit(self):
        self.assertEqual(physical("|dimensions=H. 10 cm or 20 cm; W. 18 cm\n}}"), [])

    def test_manual_baseline_scope_resolution_is_exact_evidence_bound(self):
        record = dict(
            id=1, original_sha1="pin", source_revision=2, source_markup_sha256="raw"
        )
        decision = dict(
            **record,
            thumbnail_sha256="preview",
            decision=(
                "measurement scope resolved after actual preview and source review"
            ),
            reason="Explicit frame scope, separately inspected unframed reproduction",
            limits="Small preview review, not a new full-resolution decode",
        )
        self.assertEqual(verify_decision(record, decision, "preview"), decision)
        for key in record:
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_decision(record, dict(decision, **{key: "changed"}), "preview")
        with self.assertRaises(ValueError):
            verify_decision(record, decision, "changed-preview")

    def test_manual_scope_resolution_cannot_be_an_unqualified_auto_approval(self):
        record = dict(
            id=1, original_sha1="pin", source_revision=2, source_markup_sha256="raw"
        )
        for label in ("accepted", "automatically resolved", ""):
            with self.subTest(label=label), self.assertRaises(ValueError):
                verify_decision(
                    record,
                    dict(record, thumbnail_sha256="preview", decision=label),
                    "preview",
                )

    def test_explicit_self_cc0_license_is_source_evidence_not_photo_clearance(self):
        for markup in (
            "{{Self|cc-zero}}",
            "{{self|1=CC-zero|author=Example}}",
            "{{Self|cc-by-sa-4.0|cc-zero}}",
            "{{Self|cc0}}",
        ):
            with self.subTest(markup=markup):
                self.assertIn(
                    us_basis(template_names(markup), markup)[0], {"cc-zero", "cc0"}
                )

    def test_self_cc0_requires_exact_license_parameter_not_author_or_example(self):
        for markup in (
            "{{Self|cc-by-sa-4.0|author=cc-zero}}",
            "{{Self|cc-by-sa-4.0|attribution=cc0}}",
            "{{Self|1=not-cc-zero}}",
            "{{Self|7=cc-zero}}",
            "<!-- {{Self|cc-zero}} -->",
            "<nowiki>{{Self|cc-zero}}</nowiki>",
            "{{Someone-cc-zero}}",
        ):
            with self.subTest(markup=markup):
                self.assertEqual(us_basis(template_names(markup), markup), [])

    def test_single_subjects_do_not_claim_boolean_group_support(self):
        self.assertEqual(SINGLE_SUBJECTS["kusama"], '"Yayoi Kusama"')
        self.assertEqual(SINGLE_SUBJECTS["digital-art"], '"digital art"')
        self.assertEqual(
            SINGLE_SUBJECTS["huile"], 'hastemplate:Artwork insource:"huile"'
        )
        for query in SINGLE_SUBJECTS.values():
            self.assertNotIn(" OR ", query)
            self.assertNotIn("(", query)
            self.assertNotIn(")", query)
        self.assertFalse(eligible(dict(width=3840, height=2400, mime="image/jpeg")))

    def test_multiline_dimensions_retain_sheet_and_plate_scopes(self):
        values = physical(
            "|dimensions=Sheet: 6 x 10 7/8 in. (15.2 x 27.6 cm)\n"
            "Plate: 4 5/8 x 10 1/16 in. (11.7 x 25.6 cm)\n"
            "|institution=Test museum\n}}"
        )
        self.assertEqual(len(values), 4)
        self.assertTrue(any(abs(v["ratio"] / (16 / 9) - 1) > 0.025 for v in values))
        self.assertTrue(any("Plate:" in v["raw"] for v in values))

    def test_size_template_does_not_hide_following_plain_measurement(self):
        values = physical(
            "|dimensions=Image: {{Size|cm|height=100|width=180}}\n"
            "Framed: 150 x 210 cm\n|institution=Test museum\n}}"
        )
        self.assertEqual(len(values), 2)
        self.assertAlmostEqual(values[0]["ratio"], 1.8)
        self.assertAlmostEqual(values[1]["ratio"], 1.4)
        self.assertIn("Framed:", values[1]["raw"])

    def test_broader_genre_discovery_does_not_weaken_eligibility(self):
        for term in (
            "digital art",
            "illustration",
            "engraving",
            "lithograph",
            "Kusama",
        ):
            self.assertIn(term, GENRE_SUBJECT)
        self.assertTrue(eligible(dict(width=3840, height=2160, mime="image/jpeg")))
        self.assertFalse(eligible(dict(width=3000, height=1800, mime="image/jpeg")))
        self.assertFalse(eligible(dict(width=2000, height=1125, mime="image/jpeg")))
        # Discovery terms contain neither a licence override nor an acceptance
        # claim. The separately retained source/rights and visual gates remain.
        self.assertNotIn("cc-by", GENRE_SUBJECT)

    def test_media_discovery_is_not_a_format_or_rights_relaxation(self):
        self.assertTrue(MEDIA_SUBJECT.startswith("hastemplate:Artwork ("))
        for technique in (
            "huile",
            "Öl",
            "tempera",
            "gouache",
            "watercolour",
            "watercolor",
            "olieverf",
        ):
            self.assertIn(f'insource:"{technique}"', MEDIA_SUBJECT)
        self.assertFalse(eligible(dict(width=3840, height=2400, mime="image/jpeg")))
        self.assertFalse(eligible(dict(width=3840, height=2160, mime="image/png")))

    def test_only_saved_search_overload_is_scoped_deferrable(self):
        self.assertTrue(
            busy_refusal({"error": {"code": "cirrussearch-too-busy-error"}})
        )
        for response in (
            None,
            {"error": "cirrussearch-too-busy-error"},
            {"error": {"code": "badtoken"}},
            {"error": {"code": "permissiondenied"}},
            {"warnings": {"search": "unknown warning"}},
        ):
            self.assertFalse(busy_refusal(response))

    def test_art_photo_maker_is_separate_from_photographic_credit(self):
        text = (
            "{{Art Photo\n|artist={{Creator:Alceste Campriani}}\n"
            "|photographer=Uploader\n}}"
        )
        self.assertEqual(source_artist("Uploader", "", text), "Alceste Campriani")
        self.assertEqual(
            source_artist("Uploader", "", "{{Art Photo|author={{Creator:Someone}}}}"),
            "Uploader",
        )
        self.assertEqual(
            source_artist(
                "Creator:Frédéric Houbron", "", "|artist={{Creator:Frédéric Houbron}}"
            ),
            "Frédéric Houbron",
        )
        self.assertEqual(
            source_artist("Known maker", "", text.replace("Art Photo", "Artwork")),
            "Known maker",
        )
        self.assertEqual(
            source_artist("Uploader", "", "<!-- " + text + " -->"), "Uploader"
        )
        self.assertEqual(
            source_artist(
                "Creator:Frédéric Houbron",
                "",
                "{{Information\n|Author={{Creator:Frédéric Houbron}}\n}}",
            ),
            "Frédéric Houbron",
        )
        self.assertEqual(
            source_artist(
                "Creator:Frédéric Houbron",
                "",
                "{{Information\n|Author={{Creator:Someone else}}\n}}",
            ),
            "Creator:Frédéric Houbron",
        )
        self.assertEqual(
            source_artist(
                "Creator:Photographer",
                "",
                "{{Art Photo\n|Author={{Creator:Photographer}}\n}}",
            ),
            "Creator:Photographer",
        )

    def test_unlabelled_depth_is_not_an_original_height(self):
        for text in (
            "|dimensions=Frame: 97 x 153.5 x 14 cm",
            "|dimensions=Frame: 77.5 x 131.5 x 6 cm",
            "|dimensions=Frame: 97 cm x 153.5 cm x 14 cm",
            "|dimensions=Frame: 9 x 16 x 1 inches",
            "|dimensions=Frame: 9 in. x 16 in. x 1 in.",
        ):
            self.assertEqual(physical(text), [])
        measures = physical(
            "|dimensions=Unframed: 72.3 x 128 cm; Frame: 97 x 153.5 x 14 cm"
        )
        self.assertEqual(len(measures), 1)
        self.assertAlmostEqual(measures[0]["ratio"], 128 / 72.3)
        # Two-axis frame measurements are still retained as unresolved scope;
        # this fix must not silently ignore inconvenient ratios.
        measures = physical("|dimensions=Unframed: 72.3 x 128 cm; Frame: 97 x 153.5 cm")
        self.assertEqual(len(measures), 2)
        self.assertAlmostEqual(measures[1]["ratio"], 153.5 / 97)

    def test_fractional_inches_do_not_hide_out_of_band_originals(self):
        values = physical("|dimensions=6 3/8 x 12 ½ in.\n|date=1869")
        self.assertAlmostEqual(values[0]["ratio"], 12.5 / 6.375)
        self.assertGreater(abs(values[0]["ratio"] / (16 / 9) - 1), 0.025)
        self.assertAlmostEqual(
            physical("|dimensions=9 x 16 inches")[0]["ratio"], 16 / 9
        )
        self.assertAlmostEqual(physical('|dimensions=9 x 16"')[0]["ratio"], 16 / 9)
        self.assertEqual(physical("|dimensions=0 x 16 in."), [])

    def test_repeated_units_and_semicolon_axes_preserve_originals(self):
        self.assertAlmostEqual(
            physical("|description=39 cm x 65 cm")[0]["ratio"], 65 / 39
        )
        self.assertAlmostEqual(
            physical("|description=H 78; B 136 cm.")[0]["ratio"], 136 / 78
        )
        self.assertAlmostEqual(
            physical("|dimensions=160 mm x 9 cm")[0]["ratio"], 160 / 90
        )

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
        for artist in ("W.carter", "George Chernilevsky", "CEKeech"):
            self.assertEqual(
                preview_priority(dict(title="Photographic composition", artist=artist)),
                -1,
            )
        self.assertNotEqual(
            preview_priority(
                dict(
                    title="Unrelated old grouped result",
                    artist="Maker",
                    query='hastemplate:CC-zero (painting OR "digital art")',
                )
            ),
            -1,
        )
        self.assertNotEqual(
            preview_priority(
                dict(
                    title="Unrelated old grouped result",
                    artist="Maker",
                    query='hastemplate:Artwork (insource:"huile" OR insource:"oil")',
                )
            ),
            -1,
        )
        self.assertEqual(
            preview_priority(
                dict(
                    title="Celestial photomontage",
                    artist="Maker",
                    query='"digital art"',
                )
            ),
            -1,
        )
        self.assertEqual(
            preview_priority(
                dict(
                    title="Fragment of a digital work",
                    artist="Maker",
                    query='"digital art"',
                )
            ),
            4,
        )
        self.assertEqual(preview_priority(dict(title="Blue coast", artist="Artist")), 0)
        self.assertEqual(
            preview_priority(dict(title="Blue coast", artist="Unknown artist")), 1
        )
        self.assertEqual(
            preview_priority(dict(title="Drawing, a frieze", artist="Artist")), 4
        )
        self.assertEqual(
            preview_priority(dict(title="KU-3102", artist="War Department")), 4
        )
        self.assertEqual(
            preview_priority(
                dict(
                    title="Cascades",
                    artist="Trutat, Eugène. Photographe",
                    direct_templates=["pd-art"],
                )
            ),
            4,
        )
        self.assertEqual(
            preview_priority(dict(title="Fragment of a carpet", artist="Maker")), 4
        )
        self.assertEqual(
            preview_priority(
                dict(
                    title="The Dancing master : country-dances", artist="John Playford"
                )
            ),
            4,
        )
        self.assertEqual(
            preview_priority(
                dict(title="The book", artist="John Playford. Éditeur scientifique")
            ),
            4,
        )
        self.assertEqual(
            preview_priority(
                dict(title="Blue coast", artist="Artist", direct_templates=["pd-art"])
            ),
            0,
        )
        self.assertEqual(
            preview_priority(
                dict(
                    title="Bowl",
                    artist="Artist",
                    query="hastemplate:CC-zero (painting OR abstract)",
                )
            ),
            3,
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

    def test_high_resolution_windows_cover_only_previously_coarse_ranges(self):
        self.assertEqual(HIGH_RES_WINDOWS[0][0], PRECISE_WINDOWS[-1][1] + 1)
        self.assertEqual(HIGH_RES_WINDOWS[-1][1], 100000)
        for previous, current in zip(HIGH_RES_WINDOWS, HIGH_RES_WINDOWS[1:]):
            self.assertEqual(previous[1] + 1, current[0])
        self.assertTrue(eligible(dict(width=32000, height=18000, mime="image/jpeg")))
        self.assertFalse(eligible(dict(width=32000, height=24000, mime="image/jpeg")))

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

    def test_separate_line_metric_axes_preserve_original_album_leaf_shape(self):
        values = physical(
            "|dimensions=H. 8 1/16 in. (20.5 cm)\n"
            "W. 12 3/4 in. (32.4 cm)\n|institution=Met"
        )
        self.assertEqual(len(values), 1)
        self.assertAlmostEqual(values[0]["ratio"], 32.4 / 20.5)
        self.assertGreater(abs(values[0]["ratio"] / (16 / 9) - 1), 0.025)
        self.assertEqual(physical("|dimensions=H. 20.5 cm\n|width=32.4 cm\n"), [])

    def test_blank_artist_in_explicit_rijksmuseum_source_uses_stated_maker(self):
        text = "{{Artwork\n|Institution=Rijksmuseum\n|Artist=\n}}"
        caption = "Vervaardiger: schilder: Gillis Mostaert (I) Datering: 1570"
        self.assertEqual(source_artist("", caption, text), "Gillis Mostaert (I)")
        self.assertEqual(source_artist("Other", caption, text), "Other")
        self.assertEqual(
            source_artist("", caption, text.replace("Rijksmuseum", "Other")), ""
        )
        self.assertEqual(source_artist("", "No maker given", text), "")
        self.assertEqual(source_artist("", caption, "<!-- " + text + " -->"), "")


if __name__ == "__main__":
    unittest.main()
