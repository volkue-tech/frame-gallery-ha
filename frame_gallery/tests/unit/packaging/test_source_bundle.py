"""Offline source-package safety and integrity; no upstream code is executed."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
import tarfile
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

PROJECT: Final = Path(__file__).resolve().parents[3]


def _script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "source_bundle", PROJECT / "scripts/source_bundle.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUNDLE: Final = _script()
COMMIT: Final = "a" * 40


def _snapshot_bytes() -> bytes:
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w") as archive:
        BUNDLE.add(archive, "README.md", b"synthetic clean own source")
    return output.getvalue()


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    root = tmp_path / "repository"
    retained = root / "build/phase9"
    retained.mkdir(parents=True)
    (root / "LICENSES").mkdir()
    archive = retained / "fixture.tar.gz"
    archive.write_bytes(b"inert upstream bytes, not an executable or extracted archive")
    record = {
        "filename": archive.name,
        "bytes": archive.stat().st_size,
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
    }
    (root / "LICENSES/source.json").write_text(json.dumps([record]))
    monkeypatch.setattr(BUNDLE, "SPECS", (("source.json", None, "fixture"),))

    def fake_git(_root: Path, *args: str) -> bytes:
        if args[0] == "status":
            return b""
        if args[0] == "rev-parse":
            return COMMIT.encode() + b"\n"
        assert args == ("archive", "--format=tar", COMMIT)
        return _snapshot_bytes()

    monkeypatch.setattr(BUNDLE, "git", fake_git)
    return root, retained


def test_package_is_deterministic_readback_verified_and_does_not_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, retained = _fixture(tmp_path, monkeypatch)
    output = root / "build/source-packages/first.tar"
    result = BUNDLE.assemble(root, retained, output)
    second = root / "build/source-packages/second.tar"
    assert BUNDLE.assemble(root, retained, second)["sha256"] == result["sha256"]
    assert output.read_bytes() == second.read_bytes()
    assert result["project_commit"] == COMMIT
    assert result["source_archive_count"] == 1
    assert result["binary_toolchains_included"] is False
    with tarfile.open(output) as archive:
        assert archive.getnames() == [
            "manifest.json",
            "project-source.tar",
            "fixture/fixture.tar.gz",
        ]
        member = archive.extractfile("manifest.json")
        assert member is not None
        index = json.load(member)
        assert "path" not in index["source_archives"][0]
        assert all(item.isfile() and item.mtime == 0 for item in archive.getmembers())
    original = output.read_bytes()
    with pytest.raises(FileExistsError):
        BUNDLE.assemble(root, retained, output)
    assert output.read_bytes() == original


@pytest.mark.parametrize("change", ["changed", "missing", "symlink", "directory"])
def test_missing_tampered_or_non_regular_sources_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    root, retained = _fixture(tmp_path, monkeypatch)
    source = retained / "fixture.tar.gz"
    if change == "changed":
        source.write_bytes(b"changed")
    else:
        source.unlink()
        if change == "symlink":
            source.symlink_to(root / "LICENSES/source.json")
        elif change == "directory":
            source.mkdir()
    message = {
        "changed": "missing or mismatched retained source",
        "missing": "missing or mismatched retained source",
        "symlink": "symlink in source path",
        "directory": "not a regular file",
    }[change]
    with pytest.raises(ValueError, match=message):
        BUNDLE.collect(root, retained)


@pytest.mark.parametrize("change", ["traversal", "hash", "size", "duplicate", "bound"])
def test_invalid_records_and_bounds_are_not_silently_ignored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    root, retained = _fixture(tmp_path, monkeypatch)
    manifest = root / "LICENSES/source.json"
    rows = json.loads(manifest.read_text())
    if change == "traversal":
        rows[0]["filename"] = "../outside"
    elif change == "hash":
        rows[0]["sha256"] = "not a digest"
    elif change == "size":
        rows[0]["bytes"] = True
    elif change == "duplicate":
        rows.append(rows[0])
    else:
        monkeypatch.setattr(BUNDLE, "MAX_ARCHIVES", 0)
    manifest.write_text(json.dumps(rows))
    message = {
        "traversal": "invalid source record",
        "hash": "invalid source record",
        "size": "invalid source record",
        "duplicate": "duplicate source package",
        "bound": "source package exceeds bound",
    }[change]
    with pytest.raises(ValueError, match=message):
        BUNDLE.collect(root, retained)


def test_project_snapshot_remains_bounded_after_research_expansion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    assert BUNDLE.MAX_PROJECT_BYTES == 128 * 1024 * 1024
    monkeypatch.setattr(BUNDLE, "MAX_PROJECT_BYTES", len(_snapshot_bytes()) - 1)
    with pytest.raises(ValueError, match="project snapshot exceeds bound"):
        BUNDLE.snapshot(root)


def test_dirty_git_and_changed_head_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(BUNDLE, "git", lambda *_args: b" M user-work\n")
    with pytest.raises(ValueError, match="clean"):
        BUNDLE.snapshot(root)
    calls = 0

    def changed_git(_root: Path, *args: str) -> bytes:
        nonlocal calls
        if args[0] == "status":
            return b""
        if args[0] == "rev-parse":
            calls += 1
            return (COMMIT if calls == 1 else "b" * 40).encode()
        return _snapshot_bytes()

    monkeypatch.setattr(BUNDLE, "git", changed_git)
    with pytest.raises(ValueError, match="HEAD changed"):
        BUNDLE.snapshot(root)


@pytest.mark.parametrize(
    "change",
    ["valid-empty", "missing-original", "missing-copy", "altered-copy", "linked-copy", "bad-hash"],
)
def test_git_snapshot_contains_exact_original_and_shipped_notices(change: str) -> None:
    output = io.BytesIO()
    prefix = "frame_gallery/license_bundle/"
    data = b"notice" if change == "bad-hash" else b""
    # Empty upstream originals still have to be tracked and distributed.
    index = {
        "files": [
            {"path": "LICENSE", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        ]
    }
    with tarfile.open(fileobj=output, mode="w") as archive:
        BUNDLE.add(archive, prefix + "bundle-manifest.json", json.dumps(index).encode())
        if change != "missing-original":
            BUNDLE.add(archive, "LICENSE", data)
        if change == "linked-copy":
            member = tarfile.TarInfo(prefix + "LICENSE")
            member.type, member.linkname = tarfile.SYMTYPE, "LICENSE"
            archive.addfile(member)
        elif change != "missing-copy":
            copy = b"changed" if change == "altered-copy" else data
            if change == "bad-hash":
                copy = b"change"
            BUNDLE.add(archive, prefix + "LICENSE", copy)
    if change == "valid-empty":
        BUNDLE.verify_notice_snapshot(output.getvalue())
    else:
        with pytest.raises(ValueError, match="notice"):
            BUNDLE.verify_notice_snapshot(output.getvalue())


def test_official_go_escaped_module_basename_is_supported_without_execution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, retained = _fixture(tmp_path, monkeypatch)
    manifest = root / "LICENSES/source.json"
    rows = json.loads(manifest.read_text())
    filename = "github.com__!masterminds__sprig__v3-v3.3.0.zip"
    (retained / "fixture.tar.gz").rename(retained / filename)
    rows[0]["filename"] = filename
    manifest.write_text(json.dumps(rows))
    records = BUNDLE.collect(root, retained)
    assert records[0]["name"] == "fixture/" + filename
    assert records[0]["path"] == retained / filename


def test_output_is_owned_and_not_a_link(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root, retained = _fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="own build"):
        BUNDLE.assemble(root, retained, tmp_path / "outside.tar")
    link = root / "build/link"
    link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        BUNDLE.assemble(root, retained, link / "outside.tar")


@pytest.mark.parametrize("change", ["hash", "length", "missing", "extra", "duplicate", "symlink"])
def test_readback_rejects_corrupt_incomplete_and_unsafe_packages(
    tmp_path: Path, change: str
) -> None:
    data = b"upstream source bytes"
    index = {
        "source_archives": [
            {
                "name": "source/archive",
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        ],
        "project_archive_bytes": 1,
        "project_archive_sha256": hashlib.sha256(b"p").hexdigest(),
    }
    output = tmp_path / "candidate.tar"
    with tarfile.open(output, "w") as archive:
        BUNDLE.add(archive, "manifest.json", (json.dumps(index, indent=2) + "\n").encode())
        BUNDLE.add(archive, "project-source.tar", b"p")
        if change != "missing":
            member = tarfile.TarInfo("source/archive")
            member.size = len(data)
            if change == "length":
                member.size -= 1
            if change == "symlink":
                member.type, member.linkname = tarfile.SYMTYPE, "/private"
                archive.addfile(member)
            else:
                content = b"x" * len(data) if change == "hash" else data
                archive.addfile(member, io.BytesIO(content))
        if change in {"extra", "duplicate"}:
            BUNDLE.add(archive, "extra" if change == "extra" else "project-source.tar", b"p")
    message = {
        "hash": "hash mismatch",
        "length": "length mismatch",
        "missing": "missing archive",
        "extra": "unexpected, duplicate or non-regular",
        "duplicate": "unexpected, duplicate",
        "symlink": "non-regular archive member",
    }[change]
    with pytest.raises(ValueError, match=message):
        BUNDLE.verify(output, index)


def test_cli_never_publishes_and_reports_missing_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(BUNDLE, "ROOT", root)
    assert BUNDLE.main(["--output-name", "valid.tar"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["stage"] == "local_source_package_verified"
    assert BUNDLE.main(["--output-name", "valid.tar"]) == 1
    assert "no publication" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        BUNDLE.main(["--output-name", "../unsafe.tar"])
