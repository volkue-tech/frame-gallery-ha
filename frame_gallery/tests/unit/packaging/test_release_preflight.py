"""Publication gates fail closed without using a registry or any secret."""

from __future__ import annotations

import hashlib
import io
import json
import sys
import tarfile
import urllib.error
import urllib.request
from http.client import HTTPMessage
from pathlib import Path
from typing import Any, Final

import pytest
from scripts import release_preflight as release
from scripts import source_bundle

COMMIT: Final = "a" * 40


def _fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, dict[str, Any]]:
    root = tmp_path / "own-repository"
    (root / "frame_gallery").mkdir(parents=True)
    (root / "frame_gallery/config.yaml").write_text("version: '0.1.0b1'\n")
    (root / "frame_gallery/src/frame_gallery").mkdir(parents=True)
    (root / "frame_gallery/src/frame_gallery/__init__.py").write_text('__version__ = "0.1.0b1"\n')
    (root / "LICENSES").mkdir()
    row = {"filename": "upstream.tar.gz", "bytes": 1, "sha256": hashlib.sha256(b"s").hexdigest()}
    (root / "LICENSES/source.json").write_text(json.dumps([row]))
    monkeypatch.setattr(source_bundle, "SPECS", (("source.json", None, "fixture"),))
    monkeypatch.setattr(source_bundle, "snapshot", lambda _root: (COMMIT, b"project"))
    index = {
        "schema": 1,
        "project_commit": COMMIT,
        "binary_toolchains_included": False,
        "source_archives": release.expected_records(root),
        "project_archive_bytes": 7,
        "project_archive_sha256": hashlib.sha256(b"project").hexdigest(),
    }
    return root, index


def _package(root: Path, index: dict[str, Any]) -> tuple[Path, str]:
    path = root / "build/candidate.tar"
    path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(path, "w") as archive:
        source_bundle.add(archive, "manifest.json", (json.dumps(index, indent=2) + "\n").encode())
        source_bundle.add(archive, "project-source.tar", b"project")
        source_bundle.add(archive, "fixture/upstream.tar.gz", b"s")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_exact_beta_and_clean_source_snapshot_are_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, index = _fixture(tmp_path, monkeypatch)
    release.metadata(root, "0.1.0b1", COMMIT, COMMIT)
    path, digest = _package(root, index)
    release.package(root, path, digest, COMMIT)


@pytest.mark.parametrize(
    "version", ["0.1.0.dev0", "latest", "0.1.0", "0.1.0b0", "0.1.0b1;echo bad"]
)
def test_unreviewed_or_shell_like_versions_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, version: str
) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="numbered beta"):
        release.metadata(root, version, COMMIT, COMMIT)


def test_wrong_commit_and_version_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    with pytest.raises(ValueError, match="not approved"):
        release.metadata(root, "0.1.0b1", COMMIT, "b" * 40)
    with pytest.raises(ValueError, match="Supervisor metadata"):
        release.metadata(root, "0.1.0b2", COMMIT, COMMIT)
    (root / "frame_gallery/src/frame_gallery/__init__.py").write_text('__version__ = "stale"\n')
    with pytest.raises(ValueError, match="validated runtime"):
        release.metadata(root, "0.1.0b1", COMMIT, COMMIT)


@pytest.mark.parametrize("change", ["commit", "archives", "toolchain", "project", "schema"])
def test_public_source_payload_cannot_be_for_a_different_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    root, index = _fixture(tmp_path, monkeypatch)
    if change == "commit":
        index["project_commit"] = "b" * 40
    elif change == "archives":
        index["source_archives"] = []
    elif change == "toolchain":
        index["binary_toolchains_included"] = True
    elif change == "project":
        index["project_archive_sha256"] = "b" * 64
    else:
        index["schema"] = 2
    path, digest = _package(root, index)
    message = {
        "commit": "not for this release",
        "archives": "checkout source manifests",
        "toolchain": "binary toolchain",
        "project": "snapshot differs",
        "schema": "not for this release",
    }[change]
    with pytest.raises(ValueError, match=message):
        release.package(root, path, digest, COMMIT)


def test_corruption_and_an_unapproved_package_hash_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, index = _fixture(tmp_path, monkeypatch)
    path, _ = _package(root, index)
    with pytest.raises(ValueError, match="approved hash mismatch"):
        release.package(root, path, "b" * 64, COMMIT)
    with pytest.raises(ValueError, match="invalid approved"):
        release.package(root, path, "not a digest", COMMIT)
    with pytest.raises(ValueError, match="outside source boundary"):
        release.package(root, tmp_path / "external.tar", "b" * 64, COMMIT)


def test_source_index_must_be_the_first_regular_bounded_member(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    path = root / "build/bad.tar"
    path.parent.mkdir()
    with tarfile.open(path, "w") as archive:
        member = tarfile.TarInfo("manifest.json")
        member.type, member.linkname = tarfile.SYMTYPE, "/private"
        archive.addfile(member, io.BytesIO())
    with pytest.raises(ValueError, match="manifest missing or unsafe"):
        release.package(root, path, hashlib.sha256(path.read_bytes()).hexdigest(), COMMIT)


def test_missing_hash_and_invalid_version_fail_the_cli_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root, _ = _fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(release, "ROOT", root)
    args = [
        "release-preflight",
        "--version",
        "0.1.0b1",
        "--commit",
        COMMIT,
        "--approved-commit",
        COMMIT,
    ]
    monkeypatch.setattr(sys, "argv", args)
    assert release.main() == 0
    monkeypatch.setattr(sys, "argv", [*args, "--source-package", str(root / "build/missing")])
    assert release.main() == 1
    assert "do not publish" in capsys.readouterr().err


@pytest.mark.parametrize("status", [200, 302, 401, 403, 404, 500])
def test_registry_only_permits_a_verified_absent_tag_not_auth_failure(
    monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    requests: list[urllib.request.Request] = []

    class Opener:
        def open(self, request: urllib.request.Request, *, timeout: int) -> io.BytesIO:
            assert timeout == 30
            requests.append(request)
            if len(requests) == 1:
                return io.BytesIO(b'{"token":"scoped-registry-token"}')
            assert request.get_method() == "HEAD"
            if status != 200:
                raise urllib.error.HTTPError(request.full_url, status, "test", HTTPMessage(), None)
            return io.BytesIO()

    monkeypatch.setattr(urllib.request, "build_opener", lambda *_handlers: Opener())
    if status == 404:
        release.unused_tag("aarch64", "0.1.0b1", "ghs_test-workflow-token")
    else:
        message = "already exists" if status == 200 else "authentication check failed"
        with pytest.raises(ValueError, match=message):
            release.unused_tag("aarch64", "0.1.0b1", "ghs_test-workflow-token")
    assert len(requests) == 2  # never retry a 401/403 or ambiguous response
    assert requests[0].full_url.startswith("https://ghcr.io/token?")
    assert "volkue-tech%2Fframe-gallery-ha-aarch64" in requests[0].full_url
    assert (
        requests[1].full_url
        == "https://ghcr.io/v2/volkue-tech/frame-gallery-ha-aarch64/manifests/0.1.0b1"
    )


@pytest.mark.parametrize(
    "token", ["", "github_pat_personal", "ghs_newline\n", "ghs_" + "x" * 16384]
)
def test_registry_refuses_other_credentials_without_a_request(token: str) -> None:
    with pytest.raises(ValueError, match="ephemeral workflow token"):
        release.unused_tag("aarch64", "0.1.0b1", token)


def test_failed_registry_auth_closes_body_without_logging_or_retrying(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    body = io.BytesIO(b"synthetic body must not be logged")
    calls = 0

    class Opener:
        def open(self, request: urllib.request.Request, *, timeout: int) -> io.BytesIO:
            nonlocal calls
            calls += 1
            raise urllib.error.HTTPError(request.full_url, 403, "test", HTTPMessage(), body)

    monkeypatch.setattr(urllib.request, "build_opener", lambda *_handlers: Opener())
    with pytest.raises(ValueError, match="scoped authentication failed; no retry"):
        release.unused_tag("amd64", "0.1.0b1", "ghs_test")
    assert calls == 1
    assert body.closed
    assert capsys.readouterr().out == ""


def test_registry_target_and_redirects_are_fixed() -> None:
    with pytest.raises(ValueError, match="invalid registry target"):
        release.unused_tag("other-owner/path", "0.1.0b1", "ghs_test")
    handler = release.NoRedirect()
    assert (
        handler.redirect_request(
            urllib.request.Request("https://ghcr.io/token"),
            None,
            302,
            "redirect",
            {},
            "https://untrusted.invalid/",
        )
        is None
    )
