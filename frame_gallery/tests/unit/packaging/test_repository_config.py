"""Required repository descriptor: real host gate and portable fixture regressions."""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts import repository_config


def _fixture(root: Path) -> None:
    (root / "repository.yaml").write_text(repository_config.DECLARATION, encoding="utf-8")
    app = root / "frame_gallery"
    app.mkdir()
    (app / "config.yaml").write_text("name: fixture\n", encoding="utf-8")


def test_real_root_gate_accepts_exact_own_metadata_and_app_location(tmp_path: Path) -> None:
    _fixture(tmp_path)
    assert repository_config.main(tmp_path) == 0


@pytest.mark.parametrize(
    "text",
    [
        "",
        "name: 'Frame Gallery'\n",
        repository_config.DECLARATION.replace("volkue-tech", "another-owner"),
        repository_config.DECLARATION + "name: duplicate\n",
    ],
)
def test_wrong_or_incomplete_repository_metadata_is_refused(text: str) -> None:
    with pytest.raises(ValueError, match="metadata differs"):
        repository_config.require_repository(text)


@pytest.mark.parametrize("relative", ["repository.yaml", "frame_gallery/config.yaml"])
def test_missing_actual_descriptor_fails_closed(relative: str, tmp_path: Path) -> None:
    _fixture(tmp_path)
    (tmp_path / relative).unlink()
    assert repository_config.main(tmp_path) == 1


@pytest.mark.parametrize("relative", ["repository.yaml", "frame_gallery/config.yaml"])
def test_linked_actual_descriptor_fails_closed(relative: str, tmp_path: Path) -> None:
    _fixture(tmp_path)
    path = tmp_path / relative
    original = tmp_path / "original"
    path.rename(original)
    path.symlink_to(original)
    assert repository_config.main(tmp_path) == 1


def test_linked_app_directory_fails_closed(tmp_path: Path) -> None:
    _fixture(tmp_path)
    app = tmp_path / "frame_gallery"
    original = tmp_path / "original"
    app.rename(original)
    app.symlink_to(original, target_is_directory=True)
    assert repository_config.main(tmp_path) == 1


@pytest.mark.parametrize("data", [b"wrong metadata\n", b"\xff"])
def test_unusable_actual_metadata_fails_closed(data: bytes, tmp_path: Path) -> None:
    _fixture(tmp_path)
    (tmp_path / "repository.yaml").write_bytes(data)
    assert repository_config.main(tmp_path) == 1


def test_host_quality_gate_requires_actual_repository_validation() -> None:
    project = Path(__file__).resolve().parents[3]
    assert (
        '"$BIN/python" scripts/repository_config.py' in (project / "scripts/check.sh").read_text()
    )
