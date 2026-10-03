"""Generated original notices shipped with the app; no network or legal claims."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

PROJECT: Final = Path(__file__).resolve().parents[3]


def _script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "license_bundle", PROJECT / "scripts/license_bundle.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUNDLE: Final = _script()


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "source"
    (root / "LICENSES/component").mkdir(parents=True)
    for name in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md"):
        (root / name).write_bytes(b"original public notice\n")
    (root / "LICENSES/component/PATENTS").write_bytes(b"exact patent text without final newline")
    return root


def test_generation_is_exact_deterministic_and_independently_manifested(tmp_path: Path) -> None:
    root = _root(tmp_path)
    files = BUNDLE.payload(root)
    assert BUNDLE.payload(root) == files
    rows = json.loads(files[BUNDLE.MANIFEST])["files"]
    assert len(rows) == 4
    assert "LICENSES/component/PATENTS" in files
    assert not files["LICENSES/component/PATENTS"].endswith(b"\n")
    for row in rows:
        assert len(files[row["path"]]) == row["bytes"]
        assert hashlib.sha256(files[row["path"]]).hexdigest() == row["sha256"]
    output = tmp_path / "output"
    assert not BUNDLE.verify(output, files)
    BUNDLE.stage(output, files)
    assert BUNDLE.verify(output, files)
    assert all((output / name).stat().st_mode & 0o777 == 0o644 for name in files)


@pytest.mark.parametrize("corruption", ["changed", "missing", "extra", "symlink"])
def test_stale_missing_extra_and_symlinked_payloads_are_rejected(
    tmp_path: Path, corruption: str
) -> None:
    files = BUNDLE.payload(_root(tmp_path))
    output = tmp_path / "output"
    BUNDLE.stage(output, files)
    notice = output / "NOTICE"
    if corruption == "changed":
        notice.write_bytes(b"altered")
    elif corruption == "missing":
        notice.unlink()
    elif corruption == "extra":
        (output / "unexpected").write_bytes(b"preserve this")
        with pytest.raises(ValueError, match="unexpected output file"):
            BUNDLE.stage(output, files)
        assert (output / "unexpected").read_bytes() == b"preserve this"
    else:
        notice.unlink()
        notice.symlink_to(tmp_path / "unavailable")
        with pytest.raises(ValueError, match="non-regular licence output"):
            BUNDLE.stage(output, files)
    assert not BUNDLE.verify(output, files)


def test_input_symlinks_and_missing_notices_are_refused(tmp_path: Path) -> None:
    root = _root(tmp_path)
    notice = root / "NOTICE"
    notice.unlink()
    with pytest.raises(ValueError, match="required notice"):
        BUNDLE.payload(root)
    notice.symlink_to(root / "LICENSE")
    with pytest.raises(ValueError, match="required notice"):
        BUNDLE.payload(root)
    notice.unlink()
    notice.write_bytes(b"notice")
    (root / "LICENSES/linked").symlink_to(root / "LICENSE")
    with pytest.raises(ValueError, match="symlink in licence evidence"):
        BUNDLE.payload(root)


def test_check_mode_reports_stale_output_and_normal_mode_regenerates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _root(tmp_path)
    output = tmp_path / "output"
    monkeypatch.setattr(BUNDLE, "ROOT", root)
    monkeypatch.setattr(BUNDLE, "OUTPUT", output)
    assert BUNDLE.main(["--check"]) == 1
    assert "missing or stale" in capsys.readouterr().err
    assert BUNDLE.main([]) == 0
    assert BUNDLE.main(["--check"]) == 0
    (root / "NOTICE").unlink()
    assert BUNDLE.main([]) == 1
    assert "invalid or unavailable" in capsys.readouterr().err


def test_committed_payload_and_docker_shipping_are_present() -> None:
    output = PROJECT / "license_bundle"
    manifest = json.loads((output / BUNDLE.MANIFEST).read_text())
    files = {}
    for row in manifest["files"]:
        data = (output / row["path"]).read_bytes()
        assert len(data) == row["bytes"]
        assert hashlib.sha256(data).hexdigest() == row["sha256"]
        files[row["path"]] = data
    files[BUNDLE.MANIFEST] = (output / BUNDLE.MANIFEST).read_bytes()
    assert BUNDLE.verify(output, files)
    assert (
        "COPY license_bundle /usr/share/frame-gallery/licenses"
        in (PROJECT / "Dockerfile").read_text()
    )
    assert "!license_bundle/" in (PROJECT / ".dockerignore").read_text()
    if (PROJECT.parent / "LICENSE").is_file():
        assert BUNDLE.verify(output, BUNDLE.payload(PROJECT.parent))
