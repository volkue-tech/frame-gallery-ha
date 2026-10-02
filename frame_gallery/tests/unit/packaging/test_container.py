"""The container image's build files (Dockerfile, .dockerignore, and the
requirement files; ARCHITECTURE.md §17.2, D-128, D-130, D-142).

The image itself is built and checked by ``scripts/container_check.sh``;
these tests hold the build files to the decisions without building."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

PROJECT: Final = Path(__file__).resolve().parents[3]
DOCKERFILE: Final = PROJECT / "Dockerfile"
DOCKERIGNORE: Final = PROJECT / ".dockerignore"

BASE: Final = re.compile(
    r"^FROM ghcr\.io/home-assistant/base:(?P<tag>3\.\d+-20\d\d\.\d\d\.\d+)"
    r"@sha256:(?P<digest>[0-9a-f]{64}) AS base$",
    re.MULTILINE,
)


def _dockerfile() -> str:
    return DOCKERFILE.read_text()


def _script() -> ModuleType:
    path = PROJECT / "scripts" / "image_requirements.py"
    spec = importlib.util.spec_from_file_location("image_requirements", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_the_base_image_is_pinned_by_tag_and_digest() -> None:
    """D-130: the official base, pinned; no build argument can replace it."""
    text = _dockerfile()
    assert len(BASE.findall(text)) == 1
    assert "BUILD_FROM" not in text
    assert "ARG BASE" not in text
    assert not re.search(r"^# ?syntax=", text, re.MULTILINE)  # no frontend image is pulled


def test_python3_is_an_exact_apk_version() -> None:
    """The build's interpreter and the app's are the same exact apk version."""
    pins = re.findall(r"apk add --no-cache python3=(3\.14\.\d+-r\d+)\b", _dockerfile())
    assert len(pins) == 2
    assert len(set(pins)) == 1


def test_the_app_has_no_pip() -> None:
    """D-167: the app stage installs the interpreter from the base, not from
    the build's stage, and drops the pip wheel that it bundles for ensurepip
    in the same layer, so no layer of the app holds pip or what it vendors."""
    text = _dockerfile()
    app = text.split("FROM base AS app\n", 1)[1].split("\nFROM ", 1)[0]
    assert "&& apk add --no-cache python3=" in app
    assert "\n    && rm -rf /usr/lib/python3.14/ensurepip/_bundled\n" in app
    instructions = "\n".join(line for line in app.splitlines() if not line.lstrip().startswith("#"))
    assert "pip" not in instructions.replace("ensurepip", "")  # no installer runs here


def test_wheels_come_only_from_pypi_hash_checked_and_binary() -> None:
    text = _dockerfile()
    installs = re.findall(r"pip --isolated .*?-r (\S+)", text, re.DOTALL)
    # No configuration file of the image may add an index (CP-5 of the review).
    assert text.count("PIP_CONFIG_FILE=/dev/null /tmp/build/installer/bin/pip --isolated") == 2
    build = "/tmp/build"  # noqa: S108 - a path inside the image's build stage
    assert installs == [f"{build}/requirements.txt", f"{build}/test-requirements.txt"]
    for flags in re.findall(r"pip --isolated (.*?)-r \S+", text, re.DOTALL):
        for flag in (
            "--index-url https://pypi.org/simple",
            "--require-hashes",
            "--no-deps",
            "--only-binary=:all:",
            "--no-cache-dir",
        ):
            assert flag in flags
    assert "python3 -m venv --without-pip /opt/frame-gallery" in text


def test_the_app_image_runs_the_entry_point_under_the_base_init() -> None:
    """D-130 checks b-d: s6 runs the command once; with-contenv restores the
    container's environment (SUPERVISOR_TOKEN); stop requests reach the app."""
    text = _dockerfile()
    assert text.count("CMD [") == 1
    assert (
        'CMD ["with-contenv", "/opt/frame-gallery/bin/python", "-I", "-B", "-m", "frame_gallery"]'
        in text
    )
    assert "ENV S6_CMD_RECEIVE_SIGNALS=1 S6_VERBOSITY=1" in text
    assert "ENTRYPOINT" not in text
    assert "USER" not in text.split("FROM app AS test")[0]  # the parent runs as root


def test_the_labels_come_from_required_build_arguments() -> None:
    text = _dockerfile()
    assert 'io.hass.type="app"' in text
    assert 'io.hass.arch="${BUILD_ARCH}"' in text
    assert 'io.hass.version="${BUILD_VERSION}"' in text
    # The base's OCI labels would describe the base: version, source, and time.
    assert 'org.opencontainers.image.version="${BUILD_VERSION}"' in text
    assert 'org.opencontainers.image.source=""' in text
    assert 'org.opencontainers.image.created=""' in text
    assert "licenses" not in text  # D-130: the OCI licenses label is omitted
    assert 'test -n "${BUILD_VERSION}"' in text
    assert "arm64/aarch64|amd64/amd64" in text


def test_the_app_image_is_the_last_stage() -> None:
    """A build without a target (the Supervisor's) produces the last stage:
    it must be the app, never the test stage (CP-1 of the review)."""
    text = _dockerfile()
    stages = re.findall(r"^FROM (\S+) AS (\w+)$", text, re.MULTILINE)
    assert [name for _, name in stages] == ["base", "python", "builder", "app", "test", "runtime"]
    parents = {name: parent for parent, name in stages}
    assert parents["app"] == "base"  # not the build's stage, which holds pip's wheel
    assert parents["test"] == parents["runtime"] == "app"
    assert text.rstrip().endswith("FROM app AS runtime")


def test_the_build_context_is_an_allowlist() -> None:
    lines = [
        line
        for line in DOCKERIGNORE.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert lines[0] == "*"
    allowed = {line[1:].rstrip("/") for line in lines if line.startswith("!")}
    checked = [
        path.name
        for path in PROJECT.iterdir()
        if path.suffix in {".yaml", ".txt", ".md", ".png"} or path.name == "translations"
    ]
    for needed in (
        "pyproject.toml",
        "uv.lock",
        "requirements",
        "src/frame_gallery",
        "tests",
        "scripts",
        *checked,
    ):
        assert needed in allowed, needed
    assert ".venv" not in allowed
    assert "**/__pycache__" in lines


def test_the_image_requirements_match_the_lock() -> None:
    """A changed lock must regenerate the image's requirement files."""
    script = _script()
    packages = script.load_packages()
    for kind, path in script.OUTPUTS.items():
        assert path.read_text() == script.render(script.selected_wheels(packages, kind), kind)


def test_each_native_package_has_one_wheel_per_architecture() -> None:
    script = _script()
    wheels = script.selected_wheels(script.load_packages(), "runtime")
    assert set(wheels) == {
        "certifi",
        "charset-normalizer",
        "idna",
        "multidict",
        "pillow",
        "propcache",
        "requests",
        "samsungtvws",
        "urllib3",
        "websocket-client",
        "yarl",
    }
    assert [wheel.filename for wheel in wheels["pillow"]] == [
        "pillow-12.3.0-cp314-cp314-musllinux_1_2_aarch64.whl",
        "pillow-12.3.0-cp314-cp314-musllinux_1_2_x86_64.whl",
    ]
    assert len(wheels["samsungtvws"]) == 1  # pure Python: one wheel serves both


def test_the_test_tools_are_not_in_the_runtime_set() -> None:
    script = _script()
    packages = script.load_packages()
    runtime = set(script.selected_wheels(packages, "runtime"))
    tools = set(script.selected_wheels(packages, "test"))
    assert {"pytest", "pytest-cov", "coverage"} <= tools
    assert not runtime & tools


def test_the_check_mode_reports_a_stale_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = _script()
    stale = tmp_path / "image-runtime.txt"
    stale.write_text("pillow==1.0\n")
    monkeypatch.setattr(script, "OUTPUTS", {"runtime": stale, "test": tmp_path / "missing.txt"})
    monkeypatch.setattr(script, "PROJECT", tmp_path)
    assert script.main(["--check"]) == 1
    assert script.main([]) == 0
    assert script.main(["--check"]) == 0


def test_a_package_without_a_musl_wheel_is_refused() -> None:
    script = _script()
    package = {
        "name": "native",
        "version": "1.0",
        "wheels": [
            {
                "url": "https://files.example.invalid/native-1.0-cp314-cp314-win_amd64.whl",
                "hash": "sha256:" + "0" * 64,
            }
        ],
    }
    with pytest.raises(ValueError, match=r"no wheel for CPython 3\.14 on musl"):
        script._best_wheel(package, "aarch64")


def test_only_sha256_hashes_are_accepted() -> None:
    script = _script()
    package = {
        "name": "pure",
        "version": "1.0",
        "wheels": [
            {
                "url": "https://files.example.invalid/pure-1.0-py3-none-any.whl",
                "hash": "md5:" + "0" * 32,
            }
        ],
    }
    with pytest.raises(ValueError, match="unexpected hash algorithm"):
        script._best_wheel(package, "x86_64")
