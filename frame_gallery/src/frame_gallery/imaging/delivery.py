"""Parent-side validation of ``delivery.jpg`` (§11.3, §13.5, D8).

The parent trusts nothing the worker wrote: it opens the file itself without
following symlinks, checks it, and computes the SHA-256 over exactly the
bytes it read. Those bytes are the television payload, the preview, and the
recorded fingerprint.
"""

from __future__ import annotations

import errno
import hashlib
import os
import stat
from pathlib import Path
from typing import Final

from frame_gallery.domain import CANVAS, Size
from frame_gallery.errors import FrameGalleryError
from frame_gallery.imaging.contract import MAX_OUTPUT_BYTES, DeliveryArtifact
from frame_gallery.imaging.jpeg_header import JpegHeaderError, parse_jpeg

_OPEN_FLAGS: Final = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
"""``O_NONBLOCK`` keeps a FIFO from blocking the open; ``fstat`` refuses it."""

_EOI: Final = b"\xff\xd9"


class DeliveryValidationError(FrameGalleryError):
    """The prepared file is not an acceptable television JPEG.

    The message is log-safe: it never contains the path.
    """


def _errno_name(exc: OSError) -> str:
    return errno.errorcode.get(exc.errno or 0, "error")


def _read_bounded(path: Path, max_bytes: int) -> bytes:
    """The whole file, checked by ``fstat`` first and read at most once."""
    try:
        fd = os.open(path, _OPEN_FLAGS)
    except OSError as exc:
        reason = f"cannot open the delivery file ({_errno_name(exc)})"
        raise DeliveryValidationError(reason) from None
    try:
        # fstat before wrapping the descriptor: a file object refuses a
        # directory with its own error.
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            msg = "the delivery file is not a regular file"
            raise DeliveryValidationError(msg)
        if info.st_size <= 0:
            msg = "the delivery file is empty"
            raise DeliveryValidationError(msg)
        if info.st_size > max_bytes:
            msg = f"the delivery file exceeds {max_bytes} bytes"
            raise DeliveryValidationError(msg)
        with os.fdopen(fd, "rb", closefd=False) as file:
            data = file.read(max_bytes + 1)
    except OSError as exc:
        reason = f"cannot read the delivery file ({_errno_name(exc)})"
        raise DeliveryValidationError(reason) from None
    finally:
        os.close(fd)
    if len(data) != info.st_size:
        msg = "the delivery file changed while it was read"
        raise DeliveryValidationError(msg)
    return data


def validate_delivery(
    path: Path, *, canvas: Size = CANVAS, max_bytes: int = MAX_OUTPUT_BYTES
) -> DeliveryArtifact:
    """Open without following symlinks, check, and hash the delivery file.

    Requires a regular, non-empty file of at most ``max_bytes`` holding a
    baseline (SOF0), 8-bit, three-component JPEG whose dimensions equal
    ``canvas`` and that ends with EOI. Raises :class:`DeliveryValidationError`.
    """
    data = _read_bounded(path, max_bytes)
    try:
        info = parse_jpeg(data)
    except JpegHeaderError as exc:
        reason = f"not a valid JPEG: {exc}"
        raise DeliveryValidationError(reason) from None
    if not info.is_baseline:
        msg = f"not a baseline JPEG (SOF 0x{info.sof_marker:02X})"
        raise DeliveryValidationError(msg)
    if info.precision != 8 or info.components != 3:
        msg = f"not an 8-bit three-component JPEG ({info.precision}-bit, {info.components})"
        raise DeliveryValidationError(msg)
    if info.size != canvas:
        msg = f"JPEG is {info.width}x{info.height}, expected {canvas.width}x{canvas.height}"
        raise DeliveryValidationError(msg)
    if not data.endswith(_EOI):
        msg = "the JPEG has no end-of-image marker"
        raise DeliveryValidationError(msg)
    return DeliveryArtifact(
        path=path,
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
        dims=info.size,
    )
