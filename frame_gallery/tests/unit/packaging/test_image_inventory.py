"""The image inventory (scripts/image_inventory.py; Phase 6,
THIRD_PARTY_NOTICES.md).

Its parts are checked here on a synthesized apk database and synthesized
distributions; ``scripts/container_check.sh`` runs it inside the image."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import sys
from importlib import metadata
from pathlib import Path
from types import ModuleType
from typing import Any, Final

import pytest

PROJECT: Final = Path(__file__).resolve().parents[3]


def _script() -> ModuleType:
    path = PROJECT / "scripts" / "image_inventory.py"
    spec = importlib.util.spec_from_file_location("image_inventory", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


INVENTORY: Final = _script()

APK_DATABASE: Final = """\
C:Q1checksum=
P:zlib
V:1.3.2-r0
A:aarch64
S:51234
L:Zlib
o:zlib
U:https://zlib.net/
F:usr/lib
R:libz.so.1

P:busybox
V:1.37.0-r31
A:aarch64
L:GPL-2.0-only
o:busybox
U:https://busybox.net/

F:a-block-without-a-package-name
"""


def _dist_info(site: Path, name: str, version: str, *lines: str, record: str = "") -> Path:
    folder = site / f"{name}-{version}.dist-info"
    folder.mkdir(parents=True)
    header = ["Metadata-Version: 2.4", f"Name: {name}", f"Version: {version}"]
    (folder / "METADATA").write_text("\n".join([*header, *lines]) + "\n")
    (folder / "RECORD").write_text(record)
    return folder


def _record_digest(data: bytes) -> str:
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
    return f"sha256={digest.decode()}"


def test_alpine_packages_come_from_apks_database() -> None:
    assert INVENTORY.apk_packages(APK_DATABASE) == [
        {
            "name": "busybox",
            "version": "1.37.0-r31",
            "arch": "aarch64",
            "license": "GPL-2.0-only",
            "origin": "busybox",
            "url": "https://busybox.net/",
        },
        {
            "name": "zlib",
            "version": "1.3.2-r0",
            "arch": "aarch64",
            "license": "Zlib",
            "origin": "zlib",
            "url": "https://zlib.net/",
        },
    ]


def test_python_distributions_carry_their_licence_metadata(tmp_path: Path) -> None:
    _dist_info(tmp_path, "Zeta", "1.0", "License-Expression: MIT", "License-File: LICENSE")
    _dist_info(
        tmp_path, "alpha", "2.0", "License: BSD", "License-File: LICENSE", "License-File: NOTICE"
    )
    assert INVENTORY.python_distributions([str(tmp_path)]) == [
        {
            "name": "alpha",
            "version": "2.0",
            "license_expression": None,
            "license": "BSD",
            "license_files": ["LICENSE", "NOTICE"],
        },
        {
            "name": "Zeta",
            "version": "1.0",
            "license_expression": "MIT",
            "license": None,
            "license_files": ["LICENSE"],
        },
    ]


def test_bundled_libraries_are_held_to_the_wheels_record(tmp_path: Path) -> None:
    libs = tmp_path / "pillow.libs"
    libs.mkdir()
    (libs / "libgood-1234abcd.so.1").write_bytes(b"as shipped")
    (libs / "libbad-5678abcd.so.2").write_bytes(b"changed")
    record = "\n".join(
        [
            f"pillow.libs/libgood-1234abcd.so.1,{_record_digest(b'as shipped')},10",
            f"pillow.libs/libbad-5678abcd.so.2,{_record_digest(b'as shipped')},10",
            "pillow-12.3.0.dist-info/RECORD,,",
        ]
    )
    assert INVENTORY.bundled_libraries(tmp_path, record) == [
        {
            "file": "libbad-5678abcd.so.2",
            "sha256": hashlib.sha256(b"changed").hexdigest(),
            "matches_record": False,
        },
        {
            "file": "libgood-1234abcd.so.1",
            "sha256": hashlib.sha256(b"as shipped").hexdigest(),
            "matches_record": True,
        },
    ]
    assert INVENTORY.bundled_libraries(tmp_path / "no-such-site", record) == []
    assert INVENTORY.avif_build(tmp_path) is None  # no libavif here


def test_embedded_sboms_are_read_from_the_dist_info(tmp_path: Path) -> None:
    record = "demo-1.0.dist-info/sboms/demo.cdx.json,,\ndemo-1.0.dist-info/METADATA,,\n"
    folder = _dist_info(tmp_path, "demo", "1.0", record=record)
    (folder / "sboms").mkdir()
    (folder / "sboms" / "demo.cdx.json").write_text(json.dumps({"bomFormat": "CycloneDX"}))
    (distribution,) = metadata.distributions(path=[str(tmp_path)])
    assert INVENTORY.embedded_sboms(distribution) == {"demo.cdx.json": {"bomFormat": "CycloneDX"}}


def test_s6_packages_come_from_their_versioned_folders(tmp_path: Path) -> None:
    admin = tmp_path / "admin"
    for name in ("s6-2.15.0.0", "s6-overlay-3.2.3.0", "execline-2.9.9.0", "unversioned"):
        (admin / name).mkdir(parents=True)
    (admin / "s6").symlink_to("s6-2.15.0.0")
    (admin / "notes-1.0").write_text("a file, not a package")
    assert INVENTORY.s6_packages(admin) == [
        {"name": "execline", "version": "2.9.9.0"},
        {"name": "s6", "version": "2.15.0.0"},
        {"name": "s6-overlay", "version": "3.2.3.0"},
    ]
    assert INVENTORY.s6_packages(tmp_path / "no-such-folder") == []


GO_BUILD_INFO: Final = (
    b"path\texample.org/tool\n"
    b"mod\texample.org/tool\tv0.0.0-20260717161527-56918dfb7db5\t\n"
    b"dep\texample.org/dependency\tv1.2.3\th1:checksum=\n"
    b'build\t-ldflags="-s -w -X main.ToolVersion=2026.07.0"\n'
    b"build\tvcs.revision=56918dfb7db5fec2161b2c5b37ee42f49176d34b\n"
)


def test_a_go_programs_build_information_is_read(tmp_path: Path) -> None:
    binary = tmp_path / "tool"
    # The linker may embed the block twice; the second copy adds nothing.
    binary.write_bytes(b"\x7fELF..go1.26.5.." + GO_BUILD_INFO + b"\0\0" + GO_BUILD_INFO)
    assert INVENTORY.go_program(binary) == {
        "file": str(binary),
        "module": "example.org/tool",
        "version": "2026.07.0",
        "revision": "56918dfb7db5fec2161b2c5b37ee42f49176d34b",
        "go": "go1.26.5",
        "dependencies": [{"module": "example.org/dependency", "version": "v1.2.3"}],
    }
    binary.write_bytes(b"no build information")
    assert INVENTORY.go_program(binary) == {
        "file": str(binary),
        "module": None,
        "version": None,
        "revision": None,
        "go": None,
        "dependencies": [],
    }
    assert INVENTORY.go_program(tmp_path / "missing") is None


def test_the_base_components_outside_apk(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "admin" / "s6-overlay-3.2.3.0").mkdir(parents=True)
    (tmp_path / "bashio").mkdir()
    (tmp_path / "tool").write_bytes(GO_BUILD_INFO)
    monkeypatch.setattr(INVENTORY, "S6_PACKAGES", tmp_path / "admin")
    monkeypatch.setattr(INVENTORY, "GO_PROGRAMS", (tmp_path / "tool", tmp_path / "missing"))
    monkeypatch.setattr(INVENTORY, "BASHIO", tmp_path / "bashio")
    base = INVENTORY.base_components()
    assert base["s6"] == [{"name": "s6-overlay", "version": "3.2.3.0"}]
    assert [program["module"] for program in base["go_programs"]] == ["example.org/tool"]
    assert base["bashio_present"] is True


def test_the_installed_pillow_is_described() -> None:
    """Here the development wheel; in the image's test stage the musllinux
    wheel, whose bundled libraries must all match its RECORD."""
    pillow = INVENTORY.pillow_inventory()
    assert pillow["version"] == metadata.version("pillow")
    assert pillow["wheel_tags"]
    assert pillow["features"]["jpg"]["available"] is True
    assert all(library["matches_record"] for library in pillow["libs"])
    if sys.platform == "linux":
        assert pillow["libs"]
        assert pillow["zlib_loaded"]
        assert pillow["avif"]["version"]


def _inventory() -> dict[str, Any]:
    return {
        "alpine": [{"name": "zlib"}],
        "base": {
            "s6": [{"name": "s6-overlay", "version": "3.2.3.0"}],
            "go_programs": [{"module": "example.org/tool", "version": "2026.07.0"}],
            "bashio_present": True,
        },
        "python": [{"name": "pillow"}, {"name": "urllib3"}],
        "wheels": [],
        "pillow": {
            "version": "12.3.0",
            "wheel_tags": ["cp314-cp314-musllinux_1_2_aarch64"],
            "libs": [
                {"file": "liba.so.1", "matches_record": True},
                {"file": "libb.so.2", "matches_record": True},
            ],
            "sboms": {"pillow.cdx.json": {}, "auditwheel.cdx.json": {}},
            "zlib_loaded": "1.3.2",
            "avif": {"version": "1.4.2", "codecs": "dav1d [dec]:1.5.3", "libyuv": 1916},
        },
    }


def test_the_summary_names_each_part(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    inventory = _inventory()
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(inventory))
    assert INVENTORY.main(["--summary", str(path)]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "1 Alpine packages",
        "outside apk: s6-overlay 3.2.3.0; example.org/tool 2026.07.0; bashio present",
        "2 Python distributions",
        (
            "Pillow 12.3.0 (cp314-cp314-musllinux_1_2_aarch64): 2 bundled libraries, 2 as in "
            "RECORD; SBOMs: auditwheel.cdx.json, pillow.cdx.json"
        ),
        "zlib loaded: 1.3.2; libavif 1.4.2: dav1d [dec]:1.5.3; libyuv 1916",
        "wheels in the image: none",
    ]


def test_the_summary_fails_for_a_library_that_differs(tmp_path: Path) -> None:
    inventory = _inventory()
    inventory["pillow"]["libs"][1]["matches_record"] = False
    inventory["pillow"]["avif"] = None
    inventory["base"] = {"s6": [], "go_programs": [], "bashio_present": False}
    lines, consistent = INVENTORY.summary(inventory)
    assert not consistent
    assert lines[1] == "outside apk: no s6; no Go program; bashio absent"
    assert lines[-3:] == [
        "zlib loaded: 1.3.2; libavif None: None; libyuv None",
        "differs from RECORD: libb.so.2",
        "wheels in the image: none",
    ]
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps(inventory))
    assert INVENTORY.main(["--summary", str(path)]) == 1


def test_a_wheel_in_the_image_is_found_and_fails_the_summary(tmp_path: Path) -> None:
    """D-167: a wheel (for example the one Python bundles for ensurepip)
    would ship code the inventory does not list."""
    bundled = tmp_path / "usr" / "lib" / "python3.14" / "ensurepip" / "_bundled"
    bundled.mkdir(parents=True)
    (bundled / "pip-26.2.1-py3-none-any.whl").write_bytes(b"PK")
    (tmp_path / "usr" / "lib" / "other.txt").write_text("not a wheel")
    found = INVENTORY.wheel_files([tmp_path / "usr", tmp_path / "missing"])
    assert found == [str(bundled / "pip-26.2.1-py3-none-any.whl")]
    inventory = _inventory()
    inventory["wheels"] = found
    lines, consistent = INVENTORY.summary(inventory)
    assert not consistent
    assert lines[-1] == f"wheels in the image: {found[0]}"


def test_the_inventory_is_one_json_document(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    database = tmp_path / "installed"
    database.write_text(APK_DATABASE)
    monkeypatch.setattr(INVENTORY, "APK_DATABASE", database)
    monkeypatch.setattr(INVENTORY, "S6_PACKAGES", tmp_path / "admin")
    monkeypatch.setattr(INVENTORY, "GO_PROGRAMS", ())
    monkeypatch.setattr(INVENTORY, "BASHIO", tmp_path / "bashio")
    monkeypatch.setattr(INVENTORY, "WHEEL_ROOTS", (tmp_path,))
    assert INVENTORY.main([]) == 0
    document = json.loads(capsys.readouterr().out)
    assert set(document) == {"alpine", "base", "python", "pillow", "wheels"}
    assert document["wheels"] == []
    assert document["base"] == {"s6": [], "go_programs": [], "bashio_present": False}
    assert [package["name"] for package in document["alpine"]] == ["busybox", "zlib"]
    assert "pillow" in {distribution["name"].lower() for distribution in document["python"]}
