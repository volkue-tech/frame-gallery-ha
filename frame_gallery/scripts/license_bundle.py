"""Mechanically stage public repository notices into the Supervisor build context.

No network, archive extraction, runtime state or credentials. The committed
payload lets Supervisor build directly; --check prevents stale/missing copies.
This retains the current evidence, not a finding of legal completeness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

PROJECT: Final = Path(__file__).resolve().parents[1]
ROOT: Final = PROJECT.parent
OUTPUT: Final = PROJECT / "license_bundle"
MANIFEST: Final = "bundle-manifest.json"


def source_files(root: Path) -> dict[str, bytes]:
    paths = [root / name for name in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md")]
    directory = root / "LICENSES"
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("LICENSES must be a regular repository directory")
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("symlink in licence evidence")
        if path.is_file():
            paths.append(path)
        elif not path.is_dir():
            raise ValueError("non-regular licence evidence")
    if len(paths) > 256:
        raise ValueError("licence file count exceeds bound")
    result = {}
    total = 0
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError("required notice is not a regular file")
        size = path.stat().st_size
        total += size
        if size > 2 * 1024 * 1024 or total > 10 * 1024 * 1024:
            raise ValueError("licence evidence exceeds byte bound")
        result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result


def payload(root: Path) -> dict[str, bytes]:
    files = source_files(root)
    rows = [
        {"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        for name, data in sorted(files.items())
    ]
    files[MANIFEST] = (json.dumps({"schema": 1, "files": rows}, indent=2) + "\n").encode()
    return files


def verify(output: Path, expected: dict[str, bytes]) -> bool:
    if output.is_symlink() or not output.is_dir():
        return False
    actual = set()
    for path in output.rglob("*"):
        if path.is_symlink():
            return False
        if path.is_file():
            name = path.relative_to(output).as_posix()
            if name not in expected or path.read_bytes() != expected[name]:
                return False
            actual.add(name)
        elif not path.is_dir():
            return False
    return actual == set(expected)


def stage(output: Path, expected: dict[str, bytes]) -> None:
    if output.is_symlink():
        raise ValueError("licence output is a symlink")
    if output.exists():
        for path in output.rglob("*"):
            if path.is_symlink() or (not path.is_dir() and not path.is_file()):
                raise ValueError("non-regular licence output")
            if path.is_file() and path.relative_to(output).as_posix() not in expected:
                raise ValueError("unexpected output file; preserve it and resolve manually")
    output.mkdir(parents=True, exist_ok=True)
    for name, data in expected.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(0o644)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        expected = payload(ROOT)
        if args.check:
            if not verify(OUTPUT, expected):
                sys.stderr.write("licence bundle missing or stale: run scripts/license_bundle.py\n")
                return 1
        else:
            stage(OUTPUT, expected)
        sys.stdout.write(f"Licence bundle verified: {len(expected) - 1} public evidence files\n")
        return 0
    except (OSError, ValueError):
        sys.stderr.write("licence bundle rejected: invalid or unavailable evidence/output\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
