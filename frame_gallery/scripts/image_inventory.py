"""Inventory of what the app image ships (Phase 6; THIRD_PARTY_NOTICES.md).

It runs inside the image, with the app's own interpreter and only the
standard library and Pillow; no SBOM tool and no network are needed.
``container_check.sh`` pipes it in on stdin:

    docker run --rm -i --network none --entrypoint /opt/frame-gallery/bin/python \\
        frame-gallery:dev-aarch64 -I - < scripts/image_inventory.py

It prints one JSON document:

* ``alpine``: every installed Alpine package, from apk's database (name,
  version, architecture, origin, licence, and project URL);
* ``base``: what the Home Assistant base image installs outside apk: the
  skarnet.org packages of s6-overlay (from their versioned folders), the Go
  programs with their embedded build information (``tempio``), and whether
  the ``bashio`` shell library and the untracked jemalloc library are present;
* ``python``: every distribution in the app's environment (name, version,
  licence expression or field, and licence files);
* ``wheels``: every wheel file under ``/usr`` and ``/opt``; the app ships
  none (D-167), since a wheel would carry code the inventory does not list;
* ``pillow``: each library in ``pillow.libs`` with its SHA-256 and whether it
  matches the wheel's ``RECORD``, the CycloneDX SBOMs that the wheel embeds,
  the features that Pillow reports, the zlib it loads, and the versions
  inside its libavif (the codecs and libyuv).

``--summary FILE`` reads such a document on the host and prints one line per
part; it exits 1 if a library in ``pillow.libs`` differs from the wheel's
``RECORD``, or if the image holds a wheel.

``--notices FILE NOTICES`` holds the third-party notices to such a document
(acceptance item H4, Phase 7): every Alpine package with its version and
apk's licence field, every Python distribution with its version, every
library in ``pillow.libs``, and the components outside apk must be listed. It
prints what is missing and exits 1 if anything is.
"""

from __future__ import annotations

import base64
import ctypes
import hashlib
import json
import re
import sys
from collections.abc import Iterable
from importlib import metadata
from pathlib import Path
from typing import Any, Final

APK_DATABASE: Final = Path("/lib/apk/db/installed")
APK_FIELDS: Final = {
    "P": "name",
    "V": "version",
    "A": "arch",
    "o": "origin",
    "L": "license",
    "U": "url",
}

S6_PACKAGES: Final = Path("/package")
GO_PROGRAMS: Final = (Path("/usr/bin/tempio"),)
BASHIO: Final = Path("/usr/lib/bashio")
JEMALLOC: Final = Path("/usr/local/lib/libjemalloc.so.2")
WHEEL_ROOTS: Final = (Path("/usr"), Path("/opt"))

type Record = dict[str, object]
"""One entry of the inventory, as it goes into the JSON document."""

_VERSIONED: Final = re.compile(r"(?P<name>.+?)-(?P<version>\d+(?:\.\d+)+)")
_GO_LINE: Final = re.compile(rb"(path|mod|dep|build)\t([\x20-\x7e\t]{1,300})")
_GO_RELEASE: Final = re.compile(rb"go1\.\d+(?:\.\d+)?")
_VERSION_STAMP: Final = re.compile(r"-X main\.\w*Version=([^\s\"']+)")


def apk_packages(text: str) -> list[Record]:
    """The packages in the text of apk's database: blocks of ``X:value``
    lines, separated by blank lines; only the fields in ``APK_FIELDS``."""
    packages: list[Record] = []
    for block in text.split("\n\n"):
        fields: Record = {}
        for line in block.splitlines():
            key, separator, value = line.partition(":")
            if separator and key in APK_FIELDS:
                fields[APK_FIELDS[key]] = value
        if "name" in fields:
            packages.append(fields)
    return sorted(packages, key=lambda package: str(package["name"]))


def s6_packages(root: Path) -> list[Record]:
    """Versioned slashpackage directories in every installed S6 category.

    Do not omit the net/web programs or prog libraries, and do not follow
    unversioned package aliases or symlinked category directories.
    """
    found: list[Record] = []
    for category in ("admin", "net", "prog", "web"):
        folder = root / category
        if not folder.is_dir() or folder.is_symlink():
            continue
        for entry in sorted(folder.iterdir()):
            match = _VERSIONED.fullmatch(entry.name)
            if match and entry.is_dir() and not entry.is_symlink():
                found.append({"name": match["name"], "version": match["version"]})
    return sorted(found, key=lambda package: str(package["name"]))


def go_program(path: Path) -> Record | None:
    """A Go program's module, version stamp, revision, Go release, and
    dependencies, from the build information the Go linker embeds; ``None``
    if there is no such file."""
    if not path.is_file():
        return None
    data = path.read_bytes()
    module = revision = stamp = None
    dependencies: list[Record] = []
    for kind, raw in _GO_LINE.findall(data):
        fields = raw.decode().split("\t")
        if kind == b"path" and module is not None:
            break  # the linker may embed the same block twice
        if kind == b"path":
            module = fields[0]
        elif kind == b"dep" and len(fields) >= 2:
            dependencies.append({"module": fields[0], "version": fields[1]})
        elif kind == b"build" and fields[0].startswith("vcs.revision="):
            revision = fields[0].removeprefix("vcs.revision=")
        elif kind == b"build" and (found := _VERSION_STAMP.search(fields[0])):
            stamp = found[1]
    release = _GO_RELEASE.search(data)
    return {
        "file": str(path),
        "module": module,
        "version": stamp,
        "revision": revision,
        "go": release.group().decode() if release else None,
        "dependencies": dependencies,
    }


def base_components() -> Record:
    return {
        "s6": s6_packages(S6_PACKAGES),
        "go_programs": [program for path in GO_PROGRAMS if (program := go_program(path))],
        "bashio_present": BASHIO.is_dir(),
        "jemalloc_present": JEMALLOC.is_file(),
    }


def wheel_files(roots: Iterable[Path]) -> list[str]:
    """Every ``*.whl`` file below ``roots``, sorted."""
    found: list[str] = []
    for root in roots:
        if root.is_dir():
            found.extend(str(path) for path in root.rglob("*.whl"))
    return sorted(found)


def python_distributions(paths: Iterable[str]) -> list[Record]:
    """Every distribution found on ``paths``, with its licence metadata."""
    found: dict[str, Record] = {}
    for distribution in metadata.distributions(path=list(paths)):
        meta = distribution.metadata
        name = meta["Name"]
        found[name.lower()] = {
            "name": name,
            "version": distribution.version,
            "license_expression": meta.get("License-Expression"),
            "license": meta.get("License"),
            "license_files": list(meta.get_all("License-File") or []),
        }
    return [found[key] for key in sorted(found)]


def _record_hashes(record: str) -> dict[str, str]:
    """``RECORD`` lines (``path,sha256=<urlsafe base64>,size``) as hex digests."""
    hashes = {}
    for line in record.splitlines():
        path, _, rest = line.partition(",")
        digest = rest.partition(",")[0]
        if digest.startswith("sha256="):
            raw = base64.urlsafe_b64decode(digest[len("sha256=") :] + "==")
            hashes[path] = raw.hex()
    return hashes


def bundled_libraries(site: Path, record: str) -> list[Record]:
    """Each file in ``site/pillow.libs`` with its SHA-256, and whether that
    is the hash the wheel's ``RECORD`` gives for it."""
    expected = _record_hashes(record)
    libraries: list[Record] = []
    folder = site / "pillow.libs"
    for path in sorted(folder.iterdir()) if folder.is_dir() else []:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        relative = f"pillow.libs/{path.name}"
        libraries.append(
            {
                "file": path.name,
                "sha256": digest,
                "matches_record": expected.get(relative) == digest,
            }
        )
    return libraries


def embedded_sboms(distribution: metadata.Distribution) -> Record:
    """The CycloneDX documents in the distribution's ``sboms/`` folder."""
    documents: Record = {}
    for file in distribution.files or []:
        if file.parent.name == "sboms" and file.suffix == ".json":
            documents[file.name] = json.loads(file.read_text(encoding="utf-8"))
    return documents


def pillow_features() -> Record:
    """What the installed Pillow reports: every module, codec, and feature,
    whether it is available, and its version."""
    from PIL import features  # noqa: PLC0415 - only inside the image

    names = sorted({*features.modules, *features.codecs, *features.features})
    return {
        name: {"available": features.check(name), "version": features.version(name)}
        for name in names
    }


def loaded_zlib() -> str | None:
    """The version of the ``libz.so.1`` that Pillow's libraries load: the
    wheels do not bundle zlib."""
    try:
        library = ctypes.CDLL("libz.so.1")
    except OSError:
        return None
    library.zlibVersion.restype = ctypes.c_char_p
    version: bytes = library.zlibVersion()
    return version.decode()


def avif_build(site: Path) -> Record | None:
    """The versions inside the bundled libavif: its own, its codecs (with
    the decoder and encoder libraries it links statically), and libyuv's
    (0 when it was built without libyuv)."""
    candidates = sorted((site / "pillow.libs").glob("libavif-*.so*"))
    if not candidates:
        return None
    library = ctypes.CDLL(str(candidates[0]))
    library.avifVersion.restype = ctypes.c_char_p
    library.avifLibYUVVersion.restype = ctypes.c_uint
    buffer = ctypes.create_string_buffer(256)
    library.avifCodecVersions(buffer)
    version: bytes = library.avifVersion()
    libyuv: int = library.avifLibYUVVersion()
    return {"version": version.decode(), "codecs": buffer.value.decode(), "libyuv": libyuv}


def pillow_inventory() -> Record:
    distribution = metadata.distribution("pillow")
    site = Path(str(distribution.locate_file("")))
    record = distribution.read_text("RECORD") or ""
    return {
        "version": distribution.version,
        "wheel_tags": [
            line.removeprefix("Tag: ")
            for line in (distribution.read_text("WHEEL") or "").splitlines()
            if line.startswith("Tag: ")
        ],
        "libs": bundled_libraries(site, record),
        "sboms": embedded_sboms(distribution),
        "features": pillow_features(),
        "zlib_loaded": loaded_zlib(),
        "avif": avif_build(site),
    }


def summary(inventory: dict[str, Any]) -> tuple[list[str], bool]:
    """One line per part of an inventory, and whether it is consistent:
    every library in ``pillow.libs`` is the one the wheel's ``RECORD``
    names, and the image holds no wheel."""
    pillow = inventory["pillow"]
    libs = pillow["libs"]
    mismatched = [lib["file"] for lib in libs if not lib["matches_record"]]
    avif = pillow["avif"] or {}
    sboms = ", ".join(sorted(pillow["sboms"]))
    base = inventory["base"]
    s6 = ", ".join(f"{package['name']} {package['version']}" for package in base["s6"])
    programs = ", ".join(
        f"{program['module']} {program['version']}" for program in base["go_programs"]
    )
    lines = [
        f"{len(inventory['alpine'])} Alpine packages",
        (
            f"outside apk: {s6 or 'no s6'}; {programs or 'no Go program'}; "
            f"bashio {'present' if base['bashio_present'] else 'absent'}"
            + ("; jemalloc present" if base.get("jemalloc_present") else "")
        ),
        f"{len(inventory['python'])} Python distributions",
        (
            f"Pillow {pillow['version']} ({', '.join(pillow['wheel_tags'])}): {len(libs)} bundled "
            f"libraries, {len(libs) - len(mismatched)} as in RECORD; SBOMs: {sboms}"
        ),
        (
            f"zlib loaded: {pillow['zlib_loaded']}; libavif {avif.get('version')}: "
            f"{avif.get('codecs')}; libyuv {avif.get('libyuv')}"
        ),
    ]
    lines.extend(f"differs from RECORD: {name}" for name in mismatched)
    wheels = inventory["wheels"]
    lines.append(f"wheels in the image: {', '.join(wheels) or 'none'}")
    return lines, not mismatched and not wheels


def _listed(notices: str, *patterns: str) -> bool:
    return any(re.search(pattern, notices, re.MULTILINE | re.IGNORECASE) for pattern in patterns)


def notices_problems(inventory: dict[str, Any], notices: str) -> list[str]:
    """What the third-party notices do not list of an inventory (H4)."""
    problems: list[str] = []
    for package in inventory["alpine"]:
        name, version, licence = package["name"], package["version"], package["license"]
        if f"| `{name}` | {version} | `{licence}` |" not in notices:
            problems.append(f"Alpine package {name} {version} ({licence})")
    for distribution in inventory["python"]:
        name, version = re.escape(distribution["name"]), re.escape(distribution["version"])
        if not _listed(notices, rf"^### {name} {version}$", rf"^\| `{name}` \| {version} \|"):
            problems.append(f"Python distribution {distribution['name']} {distribution['version']}")
    for library in inventory["pillow"]["libs"]:
        stem = library["file"].split("-", 1)[0].split(".", 1)[0]
        if not _listed(notices, rf"\b{re.escape(stem)}\b"):
            problems.append(f"Pillow's bundled {stem}")
    base = inventory["base"]
    for package in base["s6"]:
        name, version = re.escape(package["name"]), re.escape(package["version"])
        if not _listed(notices, rf"\b{name} {version}\b", rf"^\| {name} \| {version} \|"):
            problems.append(f"{package['name']} {package['version']} (outside apk)")
    for program in base["go_programs"]:
        name = program["module"].rsplit("/", 1)[-1]
        modules = len(program.get("dependencies", []))
        go = str(program.get("go", "")).removeprefix("go")
        listed = f"| {name} | {program['version']} |" in notices
        if not listed or f"Go {go} and {modules} Go modules" not in notices:
            problems.append(f"{name} {program['version']} (Go {go}, {modules} Go modules)")
    if base["bashio_present"] and "| bashio |" not in notices:
        problems.append("bashio (outside apk)")
    if base.get("jemalloc_present") and "| jemalloc |" not in notices:
        problems.append("jemalloc (outside apk)")
    return problems


def main(argv: list[str]) -> int:
    if argv[:1] == ["--notices"] and len(argv) == 3:
        found = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
        problems = notices_problems(found, Path(argv[2]).read_text(encoding="utf-8"))
        sys.stdout.write("".join(f"not in the notices: {problem}\n" for problem in problems))
        if not problems:
            sys.stdout.write(
                f"the notices list the image's {len(found['alpine'])} Alpine packages, "
                f"{len(found['python'])} Python distributions, "
                f"{len(found['pillow']['libs'])} Pillow libraries, "
                "and the components outside apk\n"
            )
        return 1 if problems else 0
    if argv[:1] == ["--summary"] and len(argv) == 2:
        lines, consistent = summary(json.loads(Path(argv[1]).read_text(encoding="utf-8")))
        sys.stdout.write("\n".join(lines) + "\n")
        return 0 if consistent else 1
    inventory: Record = {
        "alpine": apk_packages(APK_DATABASE.read_text(encoding="utf-8")),
        "base": base_components(),
        "python": python_distributions(sys.path),
        "wheels": wheel_files(WHEEL_ROOTS),
        "pillow": pillow_inventory(),
    }
    json.dump(inventory, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
