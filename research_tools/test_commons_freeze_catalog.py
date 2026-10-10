"""Offline synthetic fail-closed partition tests; not curation evidence."""

from __future__ import annotations

import ast
import copy
import unittest
from unittest.mock import patch

from research_tools.commons_freeze_catalog import RESERVE_IDS, render_catalog, select


def fixtures() -> dict:
    def work(i: int) -> dict:
        return dict(
            id=i,
            sha1=f"{i:040x}",
            file_title=f"File:Synthetic {i}.jpg",
            title=f"Synthetic {i}",
            artist="Fixture artist",
            width=3000,
            height=1687,
            rights_label_observed="CC0",
        )

    old = [work(i) for i in range(1, 401)]
    new = [work(i) for i in range(401, 1057)] + [work(i) for i in sorted(RESERVE_IDS)]
    held = [dict(id=w["id"], sha1=w["sha1"]) for w in old[:56]]
    return dict(
        baseline=dict(
            included=old, criteria=dict(minimum_source_width_px=3000, relative_16_9_tolerance=0.025)
        ),
        curation=dict(included=new, baseline_sha256="baseline"),
        proposal=dict(
            baseline_sha256="baseline",
            records=[dict(id=w["id"], retained_catalogue_entry=w) for w in old[:56]],
        ),
        approval=dict(
            answer="Ja, vorläufig zurückstellen und ersetzen",
            baseline_sha256="baseline",
            proposal_sha256="proposal",
            held_pins=held,
        ),
        old_colours=dict(profiles=[dict(id=w["id"]) for w in old]),
        new_colours=dict(curation_sha256="curation", profiles=[dict(id=w["id"]) for w in new]),
        hashes=dict(baseline="baseline", proposal="proposal", curation="curation"),
    )


class FreezeTests(unittest.TestCase):
    def test_duplicate_profile_is_not_silently_overwritten(self) -> None:
        data = fixtures()
        data["new_colours"]["profiles"].append(data["new_colours"]["profiles"][0])
        with (
            patch("research_tools.commons_freeze_catalog.verify_profile"),
            self.assertRaises(ValueError),
        ):
            select(**data)

    def test_long_unicode_literals_round_trip_without_changing_catalogue_data(self) -> None:
        row = fixtures()["curation"]["included"][0]
        row["file_title"] = "File:" + 'é’–日本\\"' * 90 + ".jpg"
        row["title"] = "ä long title\n" * 90
        code = render_catalog(dict(included=[row]))
        self.assertTrue(all(len(line) <= 100 for line in code.splitlines()))
        tree = ast.parse(code)
        call = next(
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "CuratedWork"
        )
        self.assertEqual(
            [ast.literal_eval(arg) for arg in call.args],
            [row["id"], row["file_title"], row["sha1"], row["title"], row["artist"]],
        )

    def test_exact_partition_retains_order_pins_and_inputs(self) -> None:
        data = fixtures()
        before = copy.deepcopy(data)
        with patch("research_tools.commons_freeze_catalog.verify_profile") as verify:
            manifest, colours = select(**data)
        self.assertEqual(verify.call_count, 1063)
        self.assertEqual(data, before)
        self.assertEqual(len(manifest["included"]), 1000)
        self.assertEqual(len(colours["profiles"]), 1000)
        self.assertEqual(manifest["included"][:344], data["baseline"]["included"][56:])
        self.assertEqual({w["id"] for w in manifest["reserve"]}, RESERVE_IDS)
        self.assertTrue(set(manifest["held_ids"]).isdisjoint(w["id"] for w in manifest["included"]))
        self.assertIn("commons:{page_id}", manifest["history_policy"])
        self.assertIn("class CuratedWork:", render_catalog(manifest))

    def test_changed_approval_or_evidence_is_refused(self) -> None:
        for field in ("answer", "proposal_sha256", "baseline_sha256"):
            data = fixtures()
            data["approval"][field] = "changed"
            with self.subTest(field=field), self.assertRaises(ValueError):
                select(**data)
        data = fixtures()
        data["new_colours"]["curation_sha256"] = "changed"
        with self.assertRaises(ValueError):
            select(**data)

    def test_unapproved_hold_pin_scope_or_missing_reserve_is_refused(self) -> None:
        for mutation in ("pin", "extra", "duplicate", "reserve"):
            data = fixtures()
            if mutation == "pin":
                data["approval"]["held_pins"][0]["sha1"] = "changed"
            elif mutation == "extra":
                data["approval"]["held_pins"].append(dict(id=57, sha1="changed"))
            elif mutation == "duplicate":
                data["approval"]["held_pins"][1] = data["approval"]["held_pins"][0]
            else:
                data["curation"]["included"][-1]["id"] = 2000
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                select(**data)

    def test_no_duplicates_or_weakened_dimension_rights_or_profile_gates(self) -> None:
        for mutation in ("id", "sha1", "label", "width", "ratio", "rights", "profile"):
            data = fixtures()
            row = data["curation"]["included"][0]
            if mutation in {"id", "sha1"}:
                row[mutation] = data["baseline"]["included"][-1][mutation]
            elif mutation == "label":
                row["title"] = data["baseline"]["included"][-1]["title"]
            elif mutation == "width":
                row["width"] = 2999
            elif mutation == "ratio":
                row["height"] = 2000
            elif mutation == "rights":
                row["rights_label_observed"] = "CC BY-SA"
            else:
                data["new_colours"]["profiles"].pop()
            with (
                self.subTest(mutation=mutation),
                patch("research_tools.commons_freeze_catalog.verify_profile"),
                self.assertRaises(ValueError),
            ):
                select(**data)
        with (
            patch(
                "research_tools.commons_freeze_catalog.verify_profile",
                side_effect=ValueError("palette/pin changed"),
            ),
            self.assertRaises(ValueError),
        ):
            select(**fixtures())


if __name__ == "__main__":
    unittest.main()
