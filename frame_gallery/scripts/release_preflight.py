"""Offline release/source checks before granting a publisher any registry work."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
import tarfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Final, override
from urllib.parse import urlencode, urlsplit

from scripts import source_bundle

ROOT: Final = Path(__file__).resolve().parents[2]
VERSION: Final = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+b[1-9][0-9]*")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    @override
    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def unused_tag(arch: str, version: str, token: str) -> None:
    """Authenticated read-only registry check; only a real 404 permits creation."""
    if arch not in {"aarch64", "amd64"} or not VERSION.fullmatch(version):
        raise ValueError("invalid registry target")
    if not token.startswith("ghs_") or len(token) > 16384 or any(c.isspace() for c in token):
        raise ValueError("only the ephemeral workflow token is accepted")
    image = "volkue-tech/frame-gallery-ha-" + arch
    query = urlencode({"service": "ghcr.io", "scope": "repository:" + image + ":pull,push"})
    authorization = base64.b64encode(("volkue-tech:" + token).encode()).decode()
    opener = urllib.request.build_opener(NoRedirect())
    request = urllib.request.Request(
        "https://ghcr.io/token?" + query, headers={"Authorization": "Basic " + authorization}
    )
    try:
        with opener.open(request, timeout=30) as response:
            body = response.read(65537)
            if len(body) > 65536:
                raise ValueError("registry token response exceeds bound")
            bearer = json.loads(body).get("token")
    except urllib.error.HTTPError as exc:
        exc.close()
        raise ValueError("registry scoped authentication failed; no retry") from None
    if (
        not isinstance(bearer, str)
        or not bearer
        or len(bearer) > 65536
        or any(c.isspace() for c in bearer)
    ):
        raise ValueError("registry did not return a scoped token")
    head = urllib.request.Request(
        "https://ghcr.io/v2/" + image + "/manifests/" + version,
        method="HEAD",
        headers={
            "Authorization": "Bearer " + bearer,
            "Accept": "application/vnd.oci.image.manifest.v1+json, "
            "application/vnd.docker.distribution.manifest.v2+json",
        },
    )
    try:
        with opener.open(head, timeout=30):
            raise ValueError("version tag already exists; preserve it")
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        if status != 404:
            raise ValueError("registry availability/authentication check failed") from None


def metadata(root: Path, version: str, commit: str, approved: str) -> None:
    if not VERSION.fullmatch(version):
        raise ValueError("only an explicit numbered beta version is permitted")
    if not re.fullmatch(r"[0-9a-f]{40}", commit) or commit != approved:
        raise ValueError("this exact source commit is not approved for publication")
    config = (root / "frame_gallery/config.yaml").read_text()
    if f"version: '{version}'\n" not in config:
        raise ValueError("release version does not match Supervisor metadata")
    source = (root / "frame_gallery/src/frame_gallery/__init__.py").read_text()
    if f'__version__ = "{version}"\n' not in source:
        raise ValueError("release version does not match the validated runtime")


def expected_records(root: Path) -> list[dict[str, Any]]:
    result = []
    for manifest, key, category in source_bundle.SPECS:
        path = root / "LICENSES" / manifest
        source_bundle.regular(path, root)
        if path.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("source manifest exceeds bound")
        data = json.loads(path.read_bytes())
        rows = data[key] if key else data
        for row in rows:
            name = row.get("filename") or Path(urlsplit(row["url"]).path).name
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+!\-]*", name):
                raise ValueError("invalid source basename")
            result.append(
                {
                    "name": category + "/" + name,
                    "source_manifest": manifest,
                    "sha256": row["sha256"],
                    "bytes": row.get("bytes", row.get("size")),
                }
            )
    if not 0 < len(result) <= source_bundle.MAX_ARCHIVES:
        raise ValueError("source record count exceeds bound")
    if len({row["name"] for row in result}) != len(result):
        raise ValueError("duplicate source record")
    return sorted(result, key=lambda row: row["name"])


def package(root: Path, path: Path, digest: str, commit: str) -> None:
    source_bundle.regular(path, root / "build")
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("invalid approved source package hash")
    maximum = source_bundle.MAX_BYTES + source_bundle.MAX_PROJECT_BYTES + 1024 * 1024
    if path.stat().st_size > maximum or source_bundle.sha256(path) != digest:
        raise ValueError("source package length or approved hash mismatch")
    with tarfile.open(path, "r|") as archive:
        first = next(iter(archive), None)
        if (
            first is None
            or first.name != "manifest.json"
            or not first.isfile()
            or first.size > 2 * 1024 * 1024
        ):
            raise ValueError("source package manifest missing or unsafe")
        handle = archive.extractfile(first)
        if handle is None:
            raise ValueError("source package manifest unavailable")
        with handle:
            index = json.load(handle)
    if index.get("schema") != 1 or index.get("project_commit") != commit:
        raise ValueError("source package is not for this release commit")
    if index.get("binary_toolchains_included") is not False:
        raise ValueError("unexpected binary toolchain distribution")
    if index.get("source_archives") != expected_records(root):
        raise ValueError("source package does not match the checkout source manifests")
    actual_commit, project = source_bundle.snapshot(root)
    if (
        actual_commit != commit
        or index.get("project_archive_bytes") != len(project)
        or index.get("project_archive_sha256") != hashlib.sha256(project).hexdigest()
    ):
        raise ValueError("project source snapshot differs from the build checkout")
    source_bundle.verify(path, index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--approved-commit", required=True)
    parser.add_argument("--source-package", type=Path)
    parser.add_argument("--source-sha256")
    args = parser.parse_args()
    try:
        metadata(ROOT, args.version, args.commit, args.approved_commit)
        if args.source_package is not None:
            if args.source_sha256 is None:
                raise ValueError("source package approval hash is missing")
            package(ROOT, args.source_package, args.source_sha256, args.commit)
        sys.stdout.write("Exact beta version/commit and supplied source checks passed.\n")
        return 0
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError):
        sys.stderr.write("Release preflight rejected; do not publish images.\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
