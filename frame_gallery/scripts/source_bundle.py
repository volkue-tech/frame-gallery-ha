"""Assemble retained public sources offline; never download, extract or execute them.

Only fixed repository manifests and a clean Git HEAD are accepted. Publication
and licence applicability are separate gates, not consequences of a passed hash.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final
from urllib.parse import urlsplit

ROOT: Final = Path(__file__).resolve().parents[2]
SPECS: Final = (
    ("python-source-manifest.json", None, "python"),
    ("skarnet-source-manifest.json", None, "skarnet"),
    ("base-source-manifest.json", None, "base"),
    ("go-source-manifest.json", None, "go"),
    ("pillow-libbsd-libmd-source-manifest.json", None, "pillow-bsd"),
    ("static-source-manifest.json", "sources", "static"),
    ("pillow-native-source-manifest.json", "sources", "pillow-native"),
    ("alpine-source-manifest.json", "sources", "alpine-sources"),
    ("alpine-source-manifest.json", "recipes", "alpine-recipes"),
)
MAX_BYTES: Final = 1024 * 1024 * 1024
MAX_ARCHIVES: Final = 200
MAX_PROJECT_BYTES: Final = 32 * 1024 * 1024


def regular(path: Path, boundary: Path) -> None:
    if not path.is_relative_to(boundary):
        raise ValueError("path outside source boundary")
    if any(parent.is_symlink() for parent in (path, *path.parents)):
        raise ValueError("symlink in source path")
    if not path.is_file():
        raise ValueError("source is not a regular file")


def sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def collect(root: Path, retained: Path) -> list[dict[str, Any]]:
    """Hash-check manifest-named files only, without following directory links."""
    if retained.is_symlink() or not retained.is_dir():
        raise ValueError("retained source directory unavailable")
    records: list[dict[str, Any]] = []
    total = 0
    for manifest, key, category in SPECS:
        path = root / "LICENSES" / manifest
        regular(path, root)
        if path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("source manifest exceeds bound")
        data = json.loads(path.read_bytes())
        rows = data[key] if key else data
        if not isinstance(rows, list):
            raise ValueError("source manifest is not a list")
        for item in rows:
            filename = item.get("filename") or Path(urlsplit(item["url"]).path).name
            digest = item["sha256"]
            size = item.get("bytes", item.get("size"))
            if (
                not isinstance(filename, str)
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", filename)
                or not isinstance(digest, str)
                or not re.fullmatch(r"[0-9a-f]{64}", digest)
                or type(size) is not int
                or not 0 < size <= MAX_BYTES
            ):
                raise ValueError("invalid source record")
            total += size
            if total > MAX_BYTES or len(records) >= MAX_ARCHIVES:
                raise ValueError("source package exceeds bound")
            found = None
            for candidate in sorted(retained.rglob(filename)):
                regular(candidate, retained)
                if candidate.stat().st_size == size and sha256(candidate) == digest:
                    found = candidate
                    break
            if found is None:
                raise ValueError("missing or mismatched retained source: " + filename)
            records.append(
                {
                    "name": category + "/" + filename,
                    "source_manifest": manifest,
                    "sha256": digest,
                    "bytes": size,
                    "path": found,
                }
            )
    if not records or len({row["name"] for row in records}) != len(records):
        raise ValueError("empty or duplicate source package")
    return sorted(records, key=lambda row: row["name"])


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(  # noqa: S603 -- fixed git operations, no shell
        ["git", *args],  # noqa: S607 -- development tool only
        cwd=root,
        timeout=60,
    )


def snapshot(root: Path) -> tuple[str, bytes]:
    if git(root, "status", "--porcelain", "--untracked-files=normal").strip():
        raise ValueError("source checkout must be clean")
    commit = git(root, "rev-parse", "HEAD").decode().strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("invalid project commit")
    source = git(root, "archive", "--format=tar", commit)
    if not 0 < len(source) <= MAX_PROJECT_BYTES:
        raise ValueError("project snapshot exceeds bound")
    if git(root, "status", "--porcelain", "--untracked-files=normal").strip():
        raise ValueError("checkout changed while taking snapshot")
    if git(root, "rev-parse", "HEAD").decode().strip() != commit:
        raise ValueError("HEAD changed while taking snapshot")
    return commit, source


def add(package: tarfile.TarFile, name: str, data: bytes) -> None:
    entry = tarfile.TarInfo(name)
    entry.size, entry.mode, entry.mtime = len(data), 0o644, 0
    package.addfile(entry, io.BytesIO(data))


def verify(path: Path, index: dict[str, Any]) -> None:
    expected = {row["name"]: row for row in index["source_archives"]}
    expected["project-source.tar"] = {
        "bytes": index["project_archive_bytes"],
        "sha256": index["project_archive_sha256"],
    }
    index_bytes = (json.dumps(index, indent=2) + "\n").encode()
    expected["manifest.json"] = {
        "bytes": len(index_bytes),
        "sha256": hashlib.sha256(index_bytes).hexdigest(),
    }
    seen = set()
    with tarfile.open(path, "r|") as package:
        for member in package:
            if member.name in seen or member.name not in expected or not member.isfile():
                raise ValueError("unexpected, duplicate or non-regular archive member")
            row = expected[member.name]
            if member.size != row["bytes"]:
                raise ValueError("archive member length mismatch")
            handle = package.extractfile(member)
            if handle is None:
                raise ValueError("archive member unavailable")
            with handle:
                digest = hashlib.sha256()
                while chunk := handle.read(1024 * 1024):
                    digest.update(chunk)
                if digest.hexdigest() != row["sha256"]:
                    raise ValueError("archive member hash mismatch")
            seen.add(member.name)
    if seen != set(expected):
        raise ValueError("missing archive members")


def assemble(root: Path, retained: Path, output: Path) -> dict[str, Any]:
    commit, project = snapshot(root)
    records = collect(root, retained)
    if not output.is_relative_to(root / "build"):
        raise ValueError("output must be inside the own build directory")
    if any(parent.is_symlink() for parent in (output, *output.parents)):
        raise ValueError("symlink in output path")
    index = {
        "schema": 1,
        "project_commit": commit,
        "scope": "retained public sources; not legal clearance or binary reproducibility proof",
        "source_archives": [{k: v for k, v in row.items() if k != "path"} for row in records],
        "project_archive_bytes": len(project),
        "project_archive_sha256": hashlib.sha256(project).hexdigest(),
        "binary_toolchains_included": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation deliberately preserves any existing package on retries.
    with output.open("xb") as handle, tarfile.open(fileobj=handle, mode="w") as package:
        add(package, "manifest.json", (json.dumps(index, indent=2) + "\n").encode())
        add(package, "project-source.tar", project)
        for row in records:
            regular(row["path"], retained)
            entry = tarfile.TarInfo(row["name"])
            entry.size, entry.mode, entry.mtime = row["bytes"], 0o644, 0
            with row["path"].open("rb") as source:
                package.addfile(entry, source)
    verify(output, index)
    if git(root, "status", "--porcelain", "--untracked-files=normal").strip():
        raise ValueError("checkout changed while assembling package")
    if git(root, "rev-parse", "HEAD").decode().strip() != commit:
        raise ValueError("HEAD changed while assembling package")
    return {
        "stage": "local_source_package_verified",
        "project_commit": commit,
        "archive": output.name,
        "bytes": output.stat().st_size,
        "sha256": sha256(output),
        "source_archive_count": len(records),
        "binary_toolchains_included": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-name", required=True)
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*\.tar", args.output_name):
        parser.error("output-name must be a simple .tar filename")
    try:
        result = assemble(
            ROOT, ROOT / "build/phase9", ROOT / "build/source-packages" / args.output_name
        )
        sys.stdout.write(json.dumps(result, indent=2) + "\n")
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, tarfile.TarError):
        sys.stderr.write(
            "Source package rejected; no publication. Preserve partial output for inspection.\n"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
