"""Offline preview regressions; synthetic fixtures are not curation evidence."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from research_tools import commons_legacy_samples as subject


class LegacySampleTests(unittest.TestCase):
    def fixture(self, root: Path) -> tuple[Path, Path]:
        output = root / "build/commons-colours"
        output.mkdir(parents=True)
        (root / "research").mkdir()
        thumbnail = output / "123.jpg"
        thumbnail.write_bytes(b"synthetic thumbnail hash fixture, not an image")
        receipt = root / "research/commons-baseline-held-proposal-2026-10-10.json"
        receipt.write_text(
            json.dumps(
                dict(
                    records=[
                        dict(
                            id=123,
                            title='<script>alert("not executable")</script>',
                            artist="Example <Artist>",
                            thumbnail_sha256=hashlib.sha256(
                                thumbnail.read_bytes()
                            ).hexdigest(),
                            source_markup_sha256="a" * 64,
                            retained_catalogue_entry=dict(width=3200, height=1800),
                            physical_measurements=[dict(ratio=1.7)],
                        )
                    ]
                )
            )
        )
        return output, receipt

    def render_fixture(self, root: Path, output: Path) -> None:
        with (
            patch.object(subject, "ROOT", root),
            patch.object(subject, "OUTPUT", output),
            patch.object(subject, "SAMPLES", ((123, 0, "quoted label", "note"),)),
        ):
            subject.render()

    def test_preview_escapes_source_text_and_does_not_change_selection_receipt(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            output, receipt = self.fixture(root)
            original = receipt.read_bytes()
            self.render_fixture(root, output)
            markup = (output / "legacy-samples.html").read_text()
            self.assertNotIn("<script>", markup)
            self.assertIn("&lt;script&gt;", markup)
            self.assertIn("Example &lt;Artist&gt;", markup)
            self.assertIn("object-fit:contain", markup)
            self.assertIn("aspect-ratio:16/9", markup)
            self.assertNotIn("height:330px", markup)
            self.assertNotIn("height:260px", markup)
            self.assertIn("Kein bewiesener Beschnitt", markup)
            self.assertIn("Special:Redirect/page/123", markup)
            self.assertEqual(receipt.read_bytes(), original)

    def test_receipt_binds_html_source_thumbnail_and_numeric_measurement(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            output, receipt = self.fixture(root)
            self.render_fixture(root, output)
            result = json.loads((output / "legacy-samples-receipt.json").read_text())
            self.assertEqual(
                result["source_receipt_sha256"],
                hashlib.sha256(receipt.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                result["html_sha256"],
                hashlib.sha256(
                    (output / "legacy-samples.html").read_bytes()
                ).hexdigest(),
            )
            sample = result["samples"][0]
            self.assertEqual(sample["measurement_index"], 0)
            self.assertEqual(sample["work_ratio"], 1.7)
            self.assertAlmostEqual(sample["file_ratio"], 16 / 9)
            self.assertAlmostEqual(
                sample["work_deviation_percent"], (1.7 / (16 / 9) - 1) * 100
            )

    def test_changed_thumbnail_is_not_displayed_as_the_reviewed_sample(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            output, _ = self.fixture(root)
            (output / "123.jpg").write_bytes(b"different bytes")
            with self.assertRaisesRegex(ValueError, "thumbnail differs"):
                self.render_fixture(root, output)
            self.assertFalse((output / "legacy-samples.html").exists())

    def test_regeneration_retains_the_previous_page_and_receipt(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            output, _ = self.fixture(root)
            old_html = b"previous locally displayed page"
            old_receipt = b"previous locally displayed receipt"
            (output / "legacy-samples.html").write_bytes(old_html)
            (output / "legacy-samples-receipt.json").write_bytes(old_receipt)
            self.render_fixture(root, output)
            for name, payload in (
                ("legacy-samples.html", old_html),
                ("legacy-samples-receipt.json", old_receipt),
            ):
                digest = hashlib.sha256(payload).hexdigest()
                archive = output / f"retained-{digest}-{name}"
                self.assertEqual(archive.read_bytes(), payload)

    def test_real_sample_plan_has_ten_unique_ids_without_a_selection_mutation(self):
        self.assertEqual(len(subject.SAMPLES), 10)
        self.assertEqual(len({r[0] for r in subject.SAMPLES}), 10)
        self.assertTrue(all(type(r[1]) is int and r[1] >= 0 for r in subject.SAMPLES))


if __name__ == "__main__":
    unittest.main()
