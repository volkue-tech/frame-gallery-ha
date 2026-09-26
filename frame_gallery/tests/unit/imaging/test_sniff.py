"""Magic-byte sniffing (§11.1 step 1)."""

from __future__ import annotations

import errno
import os
from pathlib import Path

import pytest
from PIL import Image

from frame_gallery.imaging.contract import ImageFormat
from frame_gallery.imaging.sniff import PNG_MAGIC, sniff_bytes, sniff_file
from tests.support.images import encoded_jpeg, png_header_only, save_png, write_bytes


@pytest.mark.parametrize(
    ("head", "expected"),
    [
        (b"\xff\xd8\xff\xe0\x00\x10JFIF", ImageFormat.JPEG),
        (b"\xff\xd8\xff", ImageFormat.JPEG),
        (PNG_MAGIC + b"\x00\x00\x00\rIHDR", ImageFormat.PNG),
        (PNG_MAGIC, ImageFormat.PNG),
        (b"\xff\xd8", None),
        (b"\xff\xd8\x00", None),
        (PNG_MAGIC[:7], None),
        (b"\x89PNG\r\n\x1a\x0b", None),
        (b"GIF89a", None),
        (b"", None),
    ],
)
def test_sniff_bytes(head: bytes, expected: ImageFormat | None) -> None:
    assert sniff_bytes(head) is expected


def test_sniff_file_formats(tmp_path: Path) -> None:
    jpeg = write_bytes(tmp_path / "a.bin", encoded_jpeg(Image.new("RGB", (8, 8))))
    png = save_png(Image.new("RGB", (8, 8)), tmp_path / "b.bin")
    text = write_bytes(tmp_path / "c.txt", b"hello, world")
    empty = write_bytes(tmp_path / "d.bin", b"")
    assert sniff_file(jpeg) is ImageFormat.JPEG
    assert sniff_file(png) is ImageFormat.PNG
    assert sniff_file(text) is None
    assert sniff_file(empty) is None


def test_sniff_file_reads_only_the_head(tmp_path: Path) -> None:
    # A PNG header claiming a huge image: only 16 bytes are ever read.
    huge = write_bytes(tmp_path / "huge.png", png_header_only(50_000, 50_000))
    assert sniff_file(huge) is ImageFormat.PNG


def test_sniff_file_refuses_symlinks(tmp_path: Path) -> None:
    target = write_bytes(tmp_path / "real.jpg", encoded_jpeg(Image.new("RGB", (8, 8))))
    link = tmp_path / "link.jpg"
    link.symlink_to(target)
    assert sniff_file(link) is None


def test_sniff_file_refuses_non_regular_files(tmp_path: Path) -> None:
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    assert sniff_file(fifo) is None  # does not block: opened non-blocking
    assert sniff_file(tmp_path) is None
    assert sniff_file(tmp_path / "missing.jpg") is None


def test_sniff_file_read_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    jpeg = write_bytes(tmp_path / "a.jpg", encoded_jpeg(Image.new("RGB", (8, 8))))

    def failing_read(fd: int, length: int) -> bytes:
        raise OSError(errno.EIO, "I/O error")

    monkeypatch.setattr(os, "read", failing_read)
    assert sniff_file(jpeg) is None
