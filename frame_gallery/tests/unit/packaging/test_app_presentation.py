"""The app's presentation files: icon, logo, store text, changelog, and the
user documentation (ARCHITECTURE.md §17.4, §16.3; G1, G6, B8, R-29)."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest
from PIL import Image, ImageChops

from frame_gallery import __version__

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


def test_the_dashboard_yaml_is_complete_and_consistent() -> None:
    """G1: script, card, and the scheduling example, copy-and-paste ready,
    and all of them use the same entity IDs and app ID."""
    script, card, automation = _yaml_blocks()
    assert "app: local_frame_gallery" in script
    assert script.count("timer.frame_gallery_run") >= 4
    assert "binary_sensor.frame_gallery_running" in script
    assert "repeat.index >= 3" in script  # 15 s to see the app running
    assert "repeat.index >= 27" in script  # 30 polls at most
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
