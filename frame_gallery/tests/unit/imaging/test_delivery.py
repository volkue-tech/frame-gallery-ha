"""Parent-side validation of ``delivery.jpg`` (§11.3, §13.5; acceptance D8)."""

from __future__ import annotations

import errno
import hashlib
import os
from pathlib import Path

import pytest
from PIL import Image

from frame_gallery.domain import CANVAS, Size
from frame_gallery.fingerprint import fingerprint_bytes
from frame_gallery.imaging.delivery import DeliveryValidationError, validate_delivery
from frame_gallery.imaging.worker_tasks import prepare_image
from tests.support import images
from tests.unit.imaging.prepare_helpers import request

TINY = Size(64, 36)


def _tiny_jpeg(tmp_path: Path, name: str = "d.jpg", **options: object) -> Path:
    image = Image.new("RGB", (TINY.width, TINY.height), (120, 60, 30))
    return images.write_bytes(tmp_path / name, images.encoded_jpeg(image, **options))


def test_prepared_output_validates_and_is_fingerprinted(tmp_path: Path) -> None:
    source = images.save_jpeg(images.marked((1600, 1000)), tmp_path / "source.jpg")
    req = request(tmp_path, source)
    prepare_image(req)
    path = Path(req.output_path)
    artifact = validate_delivery(path)
    data = path.read_bytes()
    # D8: one file and one SHA-256 for the television, the preview, and the record.
    assert artifact.sha256 == hashlib.sha256(data).hexdigest()
    assert artifact.size_bytes == len(data)
    assert artifact.dims == CANVAS
    assert artifact.path == path
    assert artifact.fingerprint == fingerprint_bytes(data)


def test_custom_canvas_and_limit(tmp_path: Path) -> None:
    path = _tiny_jpeg(tmp_path)
    size = path.stat().st_size
    artifact = validate_delivery(path, canvas=TINY, max_bytes=size)
    assert artifact.size_bytes == size
    assert artifact.dims == TINY


def _rejected(path: Path, message: str, *, canvas: Size = TINY, max_bytes: int = 10**6) -> None:
    with pytest.raises(DeliveryValidationError, match=message) as caught:
        validate_delivery(path, canvas=canvas, max_bytes=max_bytes)
    assert str(path.parent) not in str(caught.value)


def test_symlink_is_refused(tmp_path: Path) -> None:
    link = tmp_path / "link.jpg"
    link.symlink_to(_tiny_jpeg(tmp_path))
    _rejected(link, r"cannot open the delivery file \(ELOOP\)")


def test_missing_file_is_refused(tmp_path: Path) -> None:
    _rejected(tmp_path / "missing.jpg", r"\(ENOENT\)")


def test_non_regular_files_are_refused(tmp_path: Path) -> None:
    fifo = tmp_path / "fifo"
    os.mkfifo(fifo)
    _rejected(fifo, "not a regular file")
    directory = tmp_path / "dir"
    directory.mkdir()
    _rejected(directory, "not a regular file")


def test_empty_file_is_refused(tmp_path: Path) -> None:
    _rejected(images.write_bytes(tmp_path / "empty.jpg", b""), "empty")


def test_too_large_file_is_refused(tmp_path: Path) -> None:
    path = _tiny_jpeg(tmp_path)
    _rejected(path, "exceeds", max_bytes=path.stat().st_size - 1)


def test_wrong_dimensions_are_refused(tmp_path: Path) -> None:
    _rejected(_tiny_jpeg(tmp_path), "JPEG is 64x36, expected 3840x2160", canvas=CANVAS)


def test_progressive_jpeg_is_refused(tmp_path: Path) -> None:
    _rejected(_tiny_jpeg(tmp_path, progressive=True), r"not a baseline JPEG \(SOF 0xC2\)")


def test_greyscale_jpeg_is_refused(tmp_path: Path) -> None:
    grey = Image.new("L", (TINY.width, TINY.height), 100)
    path = images.write_bytes(tmp_path / "g.jpg", images.encoded_jpeg(grey))
    _rejected(path, "three-component")


def test_cmyk_jpeg_is_refused(tmp_path: Path) -> None:
    cmyk = Image.new("CMYK", (TINY.width, TINY.height))
    path = images.write_bytes(tmp_path / "c.jpg", images.encoded_jpeg(cmyk))
    _rejected(path, "three-component")


def test_twelve_bit_header_is_refused(tmp_path: Path) -> None:
    data = images.jpeg_header_only(TINY.width, TINY.height, precision=12)
    _rejected(images.write_bytes(tmp_path / "t.jpg", data), "8-bit")


def test_not_a_jpeg_is_refused(tmp_path: Path) -> None:
    png = images.save_png(Image.new("RGB", (TINY.width, TINY.height)), tmp_path / "p.jpg")
    _rejected(png, "not a valid JPEG: missing start-of-image marker")


def test_missing_end_of_image_is_refused(tmp_path: Path) -> None:
    data = _tiny_jpeg(tmp_path).read_bytes()
    path = images.write_bytes(tmp_path / "cut.jpg", data[:-2])
    _rejected(path, "end-of-image")


def test_read_errors_are_validation_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = _tiny_jpeg(tmp_path)

    def failing_fstat(fd: int) -> os.stat_result:
        raise OSError(errno.EIO, "I/O error")

    monkeypatch.setattr(os, "fstat", failing_fstat)
    _rejected(path, r"cannot read the delivery file \(EIO\)")


def test_a_file_that_changes_while_read_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _tiny_jpeg(tmp_path)
    real_fstat = os.fstat

    def shrunk_fstat(fd: int) -> os.stat_result:
        info = real_fstat(fd)
        fields = list(info[:10])
        fields[6] = info.st_size - 1  # st_size
        return os.stat_result(fields)

    monkeypatch.setattr(os, "fstat", shrunk_fstat)
    _rejected(path, "changed while it was read")
