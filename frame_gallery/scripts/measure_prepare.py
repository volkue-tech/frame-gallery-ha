"""Measure worst-case preparation time and memory (D-121, §11.1, R-09, Phase 5).

Generates the worst legal cases in a temporary directory, runs each through
the production ``prepare`` task in a real worker process (the process
executor with this host's production launch), and prints one row per run:
the result, the wall time, and the worker's own CPU time and peak resident
memory (``ru_maxrss``, in bytes on every platform). Each source is made as
large as the 40 MiB source cap allows, so the decoders have the most work.

The cases: 64 MP JPEGs (baseline, progressive, progressive 4:4:4, CMYK,
progressive CMYK; a 16:9 frame in ``contain`` and a 19 999 x 3 200 panorama
in ``cover``, where decoding at a reduced scale cannot help), one behind a
header flood just under the D-144 caps, and 40 MP PNGs (RGB, RGBA, palette
with transparency, grey with a transparent key, 16-bit grey), one behind a
chunk flood. The files are handed to the worker as the runner does (D-164),
so the script also works as root, where every worker drops to 65534.

``--inspections N`` also times N ``inspect`` tasks, one worker each, as a
local-media scan runs them (D-149).

The address-space limit (``RLIMIT_AS``, 1 GiB) is enforced only on Linux;
on another host each row says so. Nothing here uses the network. The exit
status is 1 if any case did not end ``ok``.

    .venv/bin/python scripts/measure_prepare.py [--repeat N] [--inspections N] [--json FILE]
"""

from __future__ import annotations

import argparse
import io
import json
import os
import platform
import shutil
import struct
import sys
import tempfile
import time
import zlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from frame_gallery.budget.clock import SystemClock
from frame_gallery.domain import BLACK, FitMode
from frame_gallery.imaging.contract import (
    MAX_SOURCE_BYTES,
    ImageFormat,
    InspectRequest,
    PrepareRequest,
)
from frame_gallery.isolation.executor import WorkerError
from frame_gallery.isolation.launch import Limit
from frame_gallery.isolation.process import Launch, ProcessExecutor
from frame_gallery.store.workspace import HANDED_OVER_FILE, RunWorkspace

FRAME_64MP = (10_666, 6_000)  # 63.996 MP, 16:9
PANORAMA_64MP = (19_999, 3_200)  # 63.997 MP; width just under the 20 000 px cap
PNG_40MP = (8_432, 4_743)  # 39.993 MP, 16:9
PREPARE_TIMEOUT_S = 15.0
INSPECT_TIMEOUT_S = 2.0
FLOOD_ROOM = 17 * 1024 * 1024
"""Left free for a header flood of just under 16 MiB."""

NEAR = 1024 * 1024
"""A source counts as filling its budget within this many bytes."""


@dataclass(frozen=True)
class Case:
    declared: ImageFormat
    fit: FitMode
    make: Callable[[], bytes]


def _noise(size: tuple[int, int], amplitude: float, mode: str = "RGB") -> Image.Image:
    """A gradient with seeded noise of ``amplitude`` (0-255): detail
    everywhere, so neither the JPEG entropy decoder nor zlib gets an easy
    image."""
    width, height = size
    gradient = Image.linear_gradient("L").resize(size)
    channels = [gradient, gradient.transpose(Image.Transpose.ROTATE_90).resize(size), gradient]
    base = Image.merge("RGB", channels)
    noise = Image.frombytes("RGB", size, os.urandom(width * height * 3))
    image = Image.blend(base, noise, amplitude / 255)
    if mode == "RGBA":
        image.putalpha(Image.linear_gradient("L").resize(size))
    elif mode in ("CMYK", "L", "P"):
        image = image.convert(mode)
    elif mode == "I;16":
        image = image.convert("L").point(lambda value: value * 257, "I").convert("I;16")
    return image


def _fill(encode: Callable[[float], bytes], budget: int) -> bytes:
    """Bisect the noise amplitude for the largest file within ``budget``;
    stop once it is within :data:`NEAR` of it."""
    low, high = 0.0, 255.0
    best = encode(low)
    if len(best) > budget:
        msg = "even a noiseless source is over the budget"
        raise RuntimeError(msg)
    for _ in range(12):
        middle = (low + high) / 2
        data = encode(middle)
        if len(data) <= budget:
            low, best = middle, data
            if budget - len(data) <= NEAR:
                break
        else:
            high = middle
    return best


def _jpeg(
    size: tuple[int, int], mode: str = "RGB", budget: int = MAX_SOURCE_BYTES, **options: object
) -> bytes:
    def encode(amplitude: float) -> bytes:
        buffer = io.BytesIO()
        _noise(size, amplitude, mode).save(buffer, "JPEG", quality=95, **options)
        return buffer.getvalue()

    return _fill(encode, budget)


def _png(
    size: tuple[int, int], mode: str, budget: int = MAX_SOURCE_BYTES, **options: object
) -> bytes:
    def encode(amplitude: float) -> bytes:
        buffer = io.BytesIO()
        _noise(size, amplitude, mode).save(buffer, "PNG", compress_level=6, **options)
        return buffer.getvalue()

    return _fill(encode, budget)


def _jpeg_segment_flood(data: bytes, count: int, size: int) -> bytes:
    """``count`` APP15 segments of ``size`` bytes after SOI: with the image's
    own nine or so segments, just under the pre-scan's 1 024 segments and
    16 MiB (D-144)."""
    segment = b"\xff\xef" + struct.pack(">H", size + 2) + b"\x00" * size
    return data[:2] + segment * count + data[2:]


def _png_chunk_flood(data: bytes, count: int, size: int) -> bytes:
    body = b"\x00" * size
    chunk = struct.pack(">I", size) + b"prVt" + body + struct.pack(">I", zlib.crc32(b"prVt" + body))
    ihdr_end = 8 + 8 + 13 + 4
    return data[:ihdr_end] + chunk * count + data[ihdr_end:]


def cases() -> dict[str, Case]:
    jpeg, png, contain, cover = ImageFormat.JPEG, ImageFormat.PNG, FitMode.CONTAIN, FitMode.COVER
    flooded = MAX_SOURCE_BYTES - FLOOD_ROOM
    return {
        "jpeg-64mp-baseline": Case(jpeg, contain, lambda: _jpeg(FRAME_64MP)),
        "jpeg-64mp-progressive": Case(jpeg, contain, lambda: _jpeg(FRAME_64MP, progressive=True)),
        "jpeg-64mp-progressive-444": Case(
            jpeg, contain, lambda: _jpeg(FRAME_64MP, progressive=True, subsampling=0)
        ),
        "jpeg-64mp-cmyk-panorama-cover": Case(jpeg, cover, lambda: _jpeg(PANORAMA_64MP, "CMYK")),
        "jpeg-64mp-progressive-cmyk-panorama-cover": Case(
            jpeg, cover, lambda: _jpeg(PANORAMA_64MP, "CMYK", progressive=True)
        ),
        "jpeg-64mp-progressive-444-panorama-cover": Case(
            jpeg, cover, lambda: _jpeg(PANORAMA_64MP, progressive=True, subsampling=0)
        ),
        "jpeg-64mp-header-flood": Case(
            jpeg,
            contain,
            lambda: _jpeg_segment_flood(_jpeg(FRAME_64MP, budget=flooded), 1_010, 16_500),
        ),
        "png-40mp-rgb": Case(png, contain, lambda: _png(PNG_40MP, "RGB")),
        "png-40mp-rgba": Case(png, contain, lambda: _png(PNG_40MP, "RGBA")),
        "png-40mp-palette-transparency": Case(
            png, contain, lambda: _png(PNG_40MP, "P", transparency=0)
        ),
        "png-40mp-grey-key": Case(png, contain, lambda: _png(PNG_40MP, "L", transparency=0)),
        "png-40mp-grey-16bit": Case(png, contain, lambda: _png(PNG_40MP, "I;16")),
        "png-40mp-chunk-flood": Case(
            png,
            contain,
            lambda: _png_chunk_flood(_png(PNG_40MP, "RGB", flooded), 1_020, 16_000),
        ),
    }


def _mib(value: object) -> float | None:
    return round(value / 2**20, 1) if isinstance(value, int) else None


def measure(repeat: int, inspections: int) -> tuple[list[dict[str, object]], dict[str, object]]:
    launch = Launch.production()
    executor = ProcessExecutor(launch, SystemClock())
    rows: list[dict[str, object]] = []
    anchor = Path(tempfile.mkdtemp(prefix="frame-gallery-measure-", dir="/tmp"))
    anchor.chmod(0o711)  # mkdtemp makes it 0700; a dropped worker must pass through
    workspace = RunWorkspace(
        anchor, worker_gid=None if launch.identity is None else launch.identity[1]
    )
    inspected: dict[str, object] = {}
    try:
        paths = workspace.create()
        for name, case in cases().items():
            source = paths.inbox / f"{name}.bin"
            source.write_bytes(case.make())
            source.chmod(HANDED_OVER_FILE)
            rows.extend(
                _prepare(executor, launch, name, case, source, paths.outbox / f"{name}-{n}.jpg")
                for n in range(repeat)
            )
            source.unlink()
        if inspections:
            inspected = _inspect(executor, paths.inbox, inspections)
    finally:
        workspace.remove()
        shutil.rmtree(anchor, ignore_errors=True)
    return rows, inspected


def _prepare(  # noqa: PLR0917 - one row's inputs
    executor: ProcessExecutor, launch: Launch, name: str, case: Case, source: Path, output: Path
) -> dict[str, object]:
    request = PrepareRequest(
        source_path=str(source),
        output_path=str(output),
        declared_format=case.declared,
        fit_mode=case.fit,
        background=BLACK,
        landscape_only=True,
        require_near_16_9=False,
    )
    executor.last_usage = None
    started = time.monotonic()
    try:
        result = executor.run("prepare", request.to_json(), timeout=PREPARE_TIMEOUT_S)
        outcome = f"{result.get('status')}:{result.get('failure')}"
    except WorkerError as error:
        outcome = f"worker_{error.kind.value}"
    elapsed = time.monotonic() - started
    usage: dict[str, object] = dict(executor.last_usage or {})
    output.unlink(missing_ok=True)
    return {
        "case": name,
        "fit": case.fit.value,
        "source_mib": _mib(source.stat().st_size),
        "outcome": outcome,
        "wall_s": round(elapsed, 2),
        "cpu_s": usage.get("cpu_s"),
        "peak_rss_mib": _mib(usage.get("max_rss_bytes")),
        "rlimit_as": (
            "not enforced on this host" if Limit.ADDRESS_SPACE in launch.skip_limits else "1 GiB"
        ),
    }


def _inspect(executor: ProcessExecutor, inbox: Path, count: int) -> dict[str, object]:
    """``count`` inspections of one small JPEG, one worker each (D-149)."""
    source = inbox / "inspect.jpg"
    Image.new("RGB", (1920, 1080), (40, 90, 160)).save(source, "JPEG", quality=85)
    source.chmod(HANDED_OVER_FILE)
    request = InspectRequest(str(source), ImageFormat.JPEG).to_json()
    started = time.monotonic()
    failures = 0
    for _ in range(count):
        result = executor.run("inspect", request, timeout=INSPECT_TIMEOUT_S)
        failures += result.get("status") != "ok"
    elapsed = time.monotonic() - started
    return {
        "inspections": count,
        "total_s": round(elapsed, 2),
        "each_s": round(elapsed / count, 3),
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--inspections", type=int, default=0)
    parser.add_argument("--json", type=Path)
    arguments = parser.parse_args()
    rows, inspected = measure(arguments.repeat, arguments.inspections)
    launch = Launch.production()
    worker = "the parent's identity" if launch.identity is None else f"uid/gid {launch.identity}"
    host = f"{platform.system()} {platform.machine()}, Python {platform.python_version()}"
    lines = [f"host: {host}; parent euid {os.geteuid()}; workers run as {worker}"]
    columns = ("case", "fit", "source_mib", "outcome", "wall_s", "cpu_s", "peak_rss_mib")
    lines.append(" | ".join((*columns, "rlimit_as")))
    lines += [" | ".join(str(row[column]) for column in (*columns, "rlimit_as")) for row in rows]
    if inspected:
        lines.append(f"inspect: {inspected}")
    sys.stdout.write("\n".join(lines) + "\n")
    if arguments.json is not None:
        arguments.json.write_text(
            json.dumps({"host": host, "rows": rows, "inspect": inspected}, indent=2)
        )
    if any(row["outcome"] != "ok:None" for row in rows) or inspected.get("failures"):
        sys.exit(1)


if __name__ == "__main__":
    main()
