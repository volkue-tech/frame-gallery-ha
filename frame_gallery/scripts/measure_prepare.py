"""Measure worst-case preparation time and memory (D-121, R-09, Phase 5).

Generates the D-121 worst cases in a temporary directory, runs each through
the production ``prepare`` task in a real worker process (the process
executor with this host's production launch), and prints one row per case:
the result, the wall time, and the worker's own CPU time and peak resident
memory (``ru_maxrss``, in bytes on every platform).

The address-space limit (``RLIMIT_AS``, 1 GiB) is enforced only on Linux;
on another host the row says so. Nothing here uses the network.

    .venv/bin/python scripts/measure_prepare.py [--repeat N] [--json FILE]
"""

from __future__ import annotations

import argparse
import io
import json
import os
import platform
import struct
import sys
import tempfile
import time
import zlib
from collections.abc import Callable
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from frame_gallery.budget.clock import SystemClock
from frame_gallery.domain import BLACK, FitMode
from frame_gallery.imaging.contract import (
    MAX_SOURCE_BYTES,
    ImageFormat,
    PrepareRequest,
)
from frame_gallery.isolation.executor import WorkerError
from frame_gallery.isolation.launch import Limit
from frame_gallery.isolation.process import Launch, ProcessExecutor

JPEG_64MP = (10_666, 6_000)  # 63.996 MP, landscape
PNG_40MP = (8_432, 4_743)  # 39.993 MP
PREPARE_TIMEOUT_S = 15.0


def _noise(size: tuple[int, int], amplitude: int, mode: str = "RGB") -> Image.Image:
    """A gradient with seeded noise: detail everywhere, so neither the JPEG
    entropy decoder nor zlib gets an easy image."""
    width, height = size
    gradient = Image.linear_gradient("L").resize(size)
    channels = [gradient, gradient.transpose(Image.Transpose.ROTATE_90).resize(size), gradient]
    base = Image.merge("RGB", channels)
    noise = Image.frombytes("RGB", size, os.urandom(width * height * 3))
    image = Image.blend(base, noise, amplitude / 255)
    if mode == "RGBA":
        alpha = Image.linear_gradient("L").resize(size)
        image.putalpha(alpha)
    return image


FLOOD_ROOM = 17 * 1024 * 1024
"""Left free for a header flood of just under 16 MiB."""


def _jpeg_under_cap(image: Image.Image, budget: int = MAX_SOURCE_BYTES, **options: object) -> bytes:
    """The best quality whose file stays within ``budget`` (the 40 MiB source cap)."""
    for quality in (92, 85, 75, 65, 55, 45, 35):
        buffer = io.BytesIO()
        image.save(buffer, "JPEG", quality=quality, **options)
        if buffer.tell() <= budget:
            return buffer.getvalue()
    msg = "no quality fits"
    raise RuntimeError(msg)


def _png_under_cap(size: tuple[int, int], mode: str, budget: int = MAX_SOURCE_BYTES) -> bytes:
    """The noisiest PNG of ``size`` that stays within ``budget``: zlib then
    has the most work that the source cap allows."""
    for amplitude in (8, 6, 4, 3, 2, 1):
        buffer = io.BytesIO()
        _noise(size, amplitude, mode).save(buffer, "PNG", compress_level=6)
        if buffer.tell() <= budget:
            return buffer.getvalue()
    msg = "no PNG fits"
    raise RuntimeError(msg)


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


def cases() -> dict[str, tuple[ImageFormat, Callable[[], bytes]]]:
    return {
        "jpeg-64mp-baseline": (
            ImageFormat.JPEG,
            lambda: _jpeg_under_cap(_noise(JPEG_64MP, 60)),
        ),
        "jpeg-64mp-progressive": (
            ImageFormat.JPEG,
            lambda: _jpeg_under_cap(_noise(JPEG_64MP, 60), progressive=True),
        ),
        "jpeg-64mp-header-flood": (
            ImageFormat.JPEG,
            lambda: _jpeg_segment_flood(
                _jpeg_under_cap(_noise(JPEG_64MP, 60), MAX_SOURCE_BYTES - FLOOD_ROOM), 1_010, 16_500
            ),
        ),
        "png-40mp-rgb": (ImageFormat.PNG, lambda: _png_under_cap(PNG_40MP, "RGB")),
        "png-40mp-rgba": (ImageFormat.PNG, lambda: _png_under_cap(PNG_40MP, "RGBA")),
        "png-40mp-chunk-flood": (
            ImageFormat.PNG,
            lambda: _png_chunk_flood(
                _png_under_cap(PNG_40MP, "RGB", MAX_SOURCE_BYTES - FLOOD_ROOM), 1_020, 16_000
            ),
        ),
    }


def _mib(value: object) -> int | None:
    return round(value / 2**20) if isinstance(value, int) else None


def measure(repeat: int) -> list[dict[str, object]]:
    launch = Launch.production()
    executor = ProcessExecutor(launch, SystemClock())
    rows: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="frame-gallery-measure-") as folder:
        root = Path(folder)
        for name, (declared, make) in cases().items():
            source = root / f"{name}.bin"
            source.write_bytes(make())
            for attempt in range(repeat):
                output = root / f"{name}-{attempt}.jpg"
                request = PrepareRequest(
                    source_path=str(source),
                    output_path=str(output),
                    declared_format=declared,
                    fit_mode=FitMode.CONTAIN,
                    background=BLACK,
                    landscape_only=True,
                    require_near_16_9=False,
                )
                started = time.monotonic()
                try:
                    result = executor.run("prepare", request.to_json(), timeout=PREPARE_TIMEOUT_S)
                    outcome = f"{result.get('status')}:{result.get('failure')}"
                except WorkerError as error:
                    outcome = f"worker_{error.kind.value}"
                elapsed = time.monotonic() - started
                usage = executor.last_usage or {}
                rows.append(
                    {
                        "case": name,
                        "source_mib": round(source.stat().st_size / 2**20, 1),
                        "outcome": outcome,
                        "wall_s": round(elapsed, 2),
                        "cpu_s": usage.get("cpu_s"),
                        "peak_rss_mib": _mib(usage.get("max_rss_bytes")),
                        "rlimit_as": (
                            "not enforced on this host"
                            if Limit.ADDRESS_SPACE in launch.skip_limits
                            else "1 GiB"
                        ),
                    }
                )
                output.unlink(missing_ok=True)
                executor.last_usage = None
            source.unlink()
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--json", type=Path)
    arguments = parser.parse_args()
    rows = measure(arguments.repeat)
    host = f"{platform.system()} {platform.machine()}, Python {platform.python_version()}"
    lines = [f"host: {host}; parent euid {os.geteuid()}"]
    columns = ("case", "source_mib", "outcome", "wall_s", "cpu_s", "peak_rss_mib", "rlimit_as")
    lines.append(" | ".join(columns))
    lines += [" | ".join(str(row[column]) for column in columns) for row in rows]
    sys.stdout.write("\n".join(lines) + "\n")
    if arguments.json is not None:
        arguments.json.write_text(json.dumps({"host": host, "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
