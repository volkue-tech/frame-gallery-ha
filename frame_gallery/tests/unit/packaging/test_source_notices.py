"""Offline integrity checks of the retained native-Pillow licence evidence.

These check repository data, not a legal opinion or binary reproducibility.
The image test context does not yet ship the root evidence (a release gate).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Final

import pytest

ROOT: Final = Path(__file__).resolve().parents[4]
LICENSES: Final = ROOT / "LICENSES"
MANIFEST: Final = LICENSES / "pillow-native-source-manifest.json"
pytestmark = pytest.mark.skipif(
    not MANIFEST.is_file(), reason="repository licence evidence is outside the image test context"
)


def _manifest() -> dict[str, Any]:
    result: dict[str, Any] = json.loads(MANIFEST.read_text())
    return result


def test_native_licence_texts_match_the_recorded_original_bytes() -> None:
    manifest = _manifest()
    assert manifest["schema"] == 1
    texts = manifest["texts"]
    assert len(texts) == 27
    assert len({row["path"] for row in texts}) == len(texts)
    for row in texts:
        path = LICENSES / row["path"]
        assert path.is_relative_to(LICENSES)
        assert ".." not in path.parts
        assert not path.is_symlink()
        data = path.read_bytes()
        assert len(data) == row["bytes"], row["path"]
        assert hashlib.sha256(data).hexdigest() == row["sha256"], row["path"]
        assert row["verification"] == "byte-identical to retained source archive member"


def test_native_sources_and_patent_texts_are_not_omitted() -> None:
    manifest = _manifest()
    sources = manifest["sources"]
    assert len(sources) == 17
    assert len({row["filename"] for row in sources}) == len(sources)
    for row in sources + manifest["shared_alpine_sources"]:
        assert row["url"].startswith("https://")
        assert re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
        assert row["bytes"] > 0
    assert {row["filename"] for row in manifest["shared_alpine_sources"]} == {
        "brotli-1.2.0.tar.gz",
        "bzip2-1.0.8.tar.gz",
        "xz-5.8.3.tar.gz",
        "zstd-1.5.7.tar.gz",
    }
    paths = {row["path"] for row in manifest["texts"]}
    assert {
        "aom-3.14.1/LICENSE",
        "aom-3.14.1/PATENTS",
        "libyuv-644251f252a84bf8ce91ff0aca86a9b16b069ab8/PATENTS",
        "libwebp-1.6.0/PATENTS",
        "libjpeg-turbo-3.1.4.1/LICENSE.md",
        "libjpeg-turbo-3.1.4.1/README.ijg",
        "freetype-2.14.3/FTL.TXT",
        "libtiff-4.7.1/LICENSE.md",
    } <= paths


def test_the_tiff_security_patch_and_berkeley_acknowledgement_are_retained() -> None:
    patch = _manifest()["libtiff_patch"]
    assert patch["commit"] == "782a11d6b5b61c6dc21e714950a4af5bf89f023c"
    text = (LICENSES / patch["path"]).read_text()
    assert text.startswith("commit " + patch["commit"] + "\n")
    assert text.count("+    const tmsize_t incr =") == 4
    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text()
    assert (
        "This software includes software developed by the University of California, Berkeley."
        in notices
    )
    assert "AOM Patent License 1.0" in notices
    assert "782a11d6b5b61c6dc21e714950a4af5bf89f023c" in notices
