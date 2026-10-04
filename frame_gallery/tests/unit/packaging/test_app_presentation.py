"""The app's presentation files: icon, logo, store text, changelog, and the
user documentation (ARCHITECTURE.md §17.4, §16.3; G1, G6, B8, R-29, Q-06)."""

from __future__ import annotations

import importlib.util
import re
import sys
import tomllib
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest
from PIL import Image, ImageChops

from frame_gallery import __version__


def test_numbered_project_and_lock_versions_match_the_runtime() -> None:
    project = Path(__file__).resolve().parents[3]
    metadata = tomllib.loads((project / "pyproject.toml").read_text())
    lock = tomllib.loads((project / "uv.lock").read_text())
    assert metadata["project"]["version"] == __version__
    own = [row for row in lock["package"] if row["name"] == "frame-gallery"]
    assert len(own) == 1
    assert own[0]["version"] == __version__
    assert own[0]["source"] == {"virtual": "."}


PROJECT: Final = Path(__file__).resolve().parents[3]
DOCS: Final = (PROJECT / "DOCS.md").read_text()


def _images() -> ModuleType:
    path = PROJECT / "scripts" / "app_images.py"
    spec = importlib.util.spec_from_file_location("app_images", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _yaml_blocks() -> list[str]:
    return re.findall(r"```yaml\n(.*?)```", DOCS, re.DOTALL)


def test_the_icon_and_logo_are_what_the_script_draws() -> None:
    images = _images()
    for name, draw, size in (
        ("icon.png", images.icon, (128, 128)),
        ("logo.png", images.logo, (250, 100)),
    ):
        with Image.open(PROJECT / name) as committed:
            assert committed.size == size
            assert ImageChops.difference(committed.convert("RGB"), draw()).getbbox() is None


def test_the_script_writes_both_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    images = _images()
    monkeypatch.setattr(images, "ICON", tmp_path / "icon.png")
    monkeypatch.setattr(images, "LOGO", tmp_path / "logo.png")
    assert images.main() == 0
    assert (tmp_path / "icon.png").exists()
    assert (tmp_path / "logo.png").exists()


def test_the_changelog_names_this_version() -> None:
    assert f"## {__version__} " in (PROJECT / "CHANGELOG.md").read_text()


def test_the_store_text_disclaims_affiliation() -> None:
    readme = (PROJECT / "README.md").read_text()
    assert "not affiliated with or endorsed by Samsung" in readme
    assert "configuration.yaml" in readme


def test_the_store_and_guide_label_the_visual_and_manual_dashboard_setup() -> None:
    """Distinguish the real card from the hero and never promise auto-created UI."""
    image_base = "https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/"
    for text in ((PROJECT / "README.md").read_text(), DOCS):
        assert image_base + "dashboard-preview.png" in text
        assert "Actual dashboard screenshot" in text
        assert "https://www.clevelandart.org/art/1929.342" in text
        assert "https://www.clevelandart.org/open-access" in text
        assert "not installed automatically" in text or "does not add a card automatically" in text
        assert "Watchdog off" in text or "**Watchdog** off" in text
    assert image_base + "frame-gallery-overview.png" in DOCS
    assert "not a screenshot" in DOCS.lower()


def test_the_guide_puts_first_use_before_advanced_options_and_has_help() -> None:
    assert DOCS.index("## Installation") < DOCS.index("## Dashboard") < DOCS.index("## Options")
    assert "## Common questions" in DOCS
    assert "## Validation notes for contributors" in DOCS
    for anchor in ("installation", "first-start-and-pairing", "dashboard", "options"):
        assert f"](#{anchor})" in DOCS


def test_the_dashboard_yaml_is_complete_and_consistent() -> None:
    """G1: script, card, and the scheduling example, copy-and-paste ready,
    and all of them use the same entity IDs and app ID."""
    script, card, automation = _yaml_blocks()
    assert "app: a94fc569_frame_gallery" in script
    assert "app: local_frame_gallery" not in script
    assert "!examples/" in (PROJECT / ".dockerignore").read_text().splitlines()
    installed_script = (PROJECT / "examples/public-beta-test-script.yaml").read_text()
    installed_card = (PROJECT / "examples/public-beta-test-card.yaml").read_text()
    assert "app: a94fc569_frame_gallery" in installed_script
    assert installed_script.count("timer.frame_gallery_beta_run") == 3
    assert "timer.frame_gallery_beta_run" in installed_card
    assert "script.frame_gallery_beta_new_artwork" in installed_card
    assert "camera.frame_gallery_test_preview" in installed_card
    assert script.count("timer.frame_gallery_run") == 3
    assert "binary_sensor.frame_gallery_running" not in script
    assert "repeat:" not in script
    assert "wait_template:" in script
    assert 'timeout: "00:02:30"' in script
    assert 'delay: "00:00:04"' in script
    assert 'duration: "00:02:30"' in script  # the 150 s indicator (§16.3)
    assert "continue_on_error: true" in script
    assert "camera.frame_gallery_preview" in card
    assert "script.frame_gallery_new_artwork" in card
    assert "timer.frame_gallery_run" in card
    assert "script.frame_gallery_new_artwork" in automation
    for block in (script, card, automation):
        assert "\t" not in block


def test_the_setup_needs_no_configuration_file() -> None:
    """G6: no configuration.yaml edit, no SSH, no file copied by hand."""
    assert "No SSH, no command line, and no change to `configuration.yaml`" in DOCS
    assert "/media/frame_gallery/preview/latest.jpg" in DOCS


def test_the_known_limitations_are_stated_plainly() -> None:
    """R-29 among them, in plain language (TASKS Phase 6)."""
    assert "Very old works can come back." in DOCS
    assert "20 000" in DOCS
    assert "about 55 years" in DOCS
    assert "30 days" in DOCS
    assert "0.97" in DOCS


def test_starting_over_is_explained() -> None:
    """Q-06 (D-172): reinstalling is the reset; pairing again needs none."""
    section = DOCS.split("\n## Starting over\n", 1)[1].split("\n## ", 1)[0]
    assert "uninstall the app and install it again" in section
    assert "the pairing key" in section
    assert "the next start asks the TV again" in section


def test_the_capability_matrix_is_published() -> None:
    """B8: the documentation states which source supports which filter."""
    assert "| Department | not supported | not supported | supported |" in DOCS
    assert "| Period | not supported | supported | supported |" in DOCS
    assert "| Colour | not supported | not supported | not supported |" in DOCS


def test_the_documentation_carries_the_required_acknowledgements() -> None:
    assert "Independent JPEG Group" in DOCS
    assert "The FreeType Project" in DOCS


def test_the_documentation_says_the_image_is_not_free_of_gpl_components() -> None:
    """D-102, D-171: the copyleft parts of the image are named, not hidden."""
    assert "LGPL-3.0 library `samsungtvws`" in DOCS
    assert "LGPL-2.1-or-later code inside the Pillow image library" in DOCS
    assert "GPL-3.0-or-later" in DOCS
    assert "not free of GPL components" in DOCS
    assert "libimagequant" not in DOCS  # not in the runtime wheels (D-171)
