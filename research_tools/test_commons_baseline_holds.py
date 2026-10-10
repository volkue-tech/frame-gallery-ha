"""Offline regressions for the bounded legacy hold receipt, not new curation."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from research_tools import commons_baseline_holds as subject


class BaselineHoldsTests(unittest.TestCase):
    def fixture(self, root: Path) -> tuple[Path, str]:
        (root / "research").mkdir()
        (root / "build/commons-colours").mkdir(parents=True)
        baseline = root / "baseline.json"
        baseline.write_text(json.dumps(dict(included=[dict(id=i) for i in range(400)])))
        markup = "synthetic source fixture; no original artwork"
        receipt = root / "source.json"
        receipt.write_text(
            json.dumps(
                dict(
                    query=dict(
                        pages=[
                            dict(
                                pageid=i,
                                revisions=[dict(slots=dict(main=dict(content=markup)))],
                            )
                            for i in range(56)
                        ]
                    )
                )
            )
        )
        rows = []
        profiles = []
        for i in range(400):
            row = dict(id=i, review_prompts=["synthetic prompt"] if i < 56 else [])
            if i < 56:
                row.update(
                    original_sha1="synthetic original pin",
                    source_receipt="source.json",
                    source_receipt_sha256=hashlib.sha256(
                        receipt.read_bytes()
                    ).hexdigest(),
                    source_markup_sha256=hashlib.sha256(markup.encode()).hexdigest(),
                )
                preview_bytes = b"synthetic fixture, not an actual inspected image"
                (root / "build/commons-colours" / f"{i}.jpg").write_bytes(preview_bytes)
                profiles.append(
                    dict(
                        id=i,
                        original_sha1=row["original_sha1"],
                        thumbnail_sha256=hashlib.sha256(preview_bytes).hexdigest(),
                    )
                )
            rows.append(row)
        profile_path = (
            root / "frame_gallery/research/commons-colour-profiles-2026-10-09.json"
        )
        profile_path.parent.mkdir(parents=True)
        profile_path.write_text(json.dumps(dict(profiles=profiles)))
        audit = root / "research/commons-baseline-format-audit-2026-10-09.json"
        audit.write_text(
            json.dumps(
                dict(
                    baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),
                    records=rows,
                )
            )
        )
        return baseline, hashlib.sha256(audit.read_bytes()).hexdigest()

    def test_exact_receipt_preserves_all_legacy_ids_without_resolving_prompts(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            baseline, audit_hash = self.fixture(root)
            prior = baseline.read_bytes()
            with (
                patch.object(subject, "ROOT", root),
                patch.object(subject, "BASELINE", baseline),
                patch.object(subject, "INSPECTED_AUDIT_SHA256", audit_hash),
            ):
                subject.holds()
            self.assertEqual(baseline.read_bytes(), prior)
            result = json.loads(
                (
                    root / "research/commons-baseline-held-proposal-2026-10-10.json"
                ).read_text()
            )
            self.assertEqual(result["additional_acceptances_needed_for_1000"], 656)
            self.assertEqual(result["unresolved_held_count"], 56)
            self.assertEqual({r["id"] for r in result["records"]}, set(range(56)))
            self.assertTrue(all(r["review_prompts"] for r in result["records"]))

    def test_changed_audit_cannot_claim_actual_source_review(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            baseline, _ = self.fixture(root)
            with (
                patch.object(subject, "ROOT", root),
                patch.object(subject, "BASELINE", baseline),
                patch.object(subject, "INSPECTED_AUDIT_SHA256", "0" * 64),
                self.assertRaisesRegex(ValueError, "audit bytes changed"),
            ):
                subject.holds()

    def test_changed_source_is_not_a_new_approval(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            baseline, audit_hash = self.fixture(root)
            (root / "source.json").write_bytes(b"changed")
            with (
                patch.object(subject, "ROOT", root),
                patch.object(subject, "BASELINE", baseline),
                patch.object(subject, "INSPECTED_AUDIT_SHA256", audit_hash),
                self.assertRaisesRegex(ValueError, "source receipt changed"),
            ):
                subject.holds()

    def test_changed_preview_cannot_claim_the_actual_inspection(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            baseline, audit_hash = self.fixture(root)
            (root / "build/commons-colours/0.jpg").write_bytes(b"changed thumbnail")
            with (
                patch.object(subject, "ROOT", root),
                patch.object(subject, "BASELINE", baseline),
                patch.object(subject, "INSPECTED_AUDIT_SHA256", audit_hash),
                self.assertRaisesRegex(ValueError, "source-bound preview changed"),
            ):
                subject.holds()

    def test_changed_original_pin_cannot_claim_the_actual_inspection(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            baseline, audit_hash = self.fixture(root)
            path = (
                root / "frame_gallery/research/commons-colour-profiles-2026-10-09.json"
            )
            document = json.loads(path.read_text())
            document["profiles"][0]["original_sha1"] = "different original"
            path.write_text(json.dumps(document))
            with (
                patch.object(subject, "ROOT", root),
                patch.object(subject, "BASELINE", baseline),
                patch.object(subject, "INSPECTED_AUDIT_SHA256", audit_hash),
                self.assertRaisesRegex(ValueError, "source-bound preview changed"),
            ):
                subject.holds()


if __name__ == "__main__":
    unittest.main()
