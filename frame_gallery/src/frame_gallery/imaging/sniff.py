"""Magic-byte sniffing in the parent (§11.1 step 1): standard library only."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Final

from frame_gallery.imaging.contract import ImageFormat

JPEG_MAGIC: Final = b"\xff\xd8\xff"
"""SOI followed by the first byte of the next marker."""

PNG_MAGIC: Final = b"\x89PNG\r\n\x1a\n"
"""The 8-byte PNG signature."""

SNIFF_BYTES: Final = 16
"""At most this many leading bytes are read."""

_OPEN_FLAGS: Final = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
"""``O_NONBLOCK`` keeps a FIFO from blocking the open; it does not affect a
regular file, and anything else is refused after ``fstat``."""


def sniff_bytes(head: bytes) -> ImageFormat | None:
    """JPEG or PNG from the leading bytes, otherwise ``None``."""
    if head.startswith(JPEG_MAGIC):
        return ImageFormat.JPEG
    if head.startswith(PNG_MAGIC):
        return ImageFormat.PNG
    return None


def sniff_file(path: Path) -> ImageFormat | None:
    """Sniff the first bytes of ``path``, opened without following symlinks.

    Returns ``None`` instead of raising when ``path`` is a symbolic link, not
    a regular file, or unreadable.
    """
    try:
        fd = os.open(path, _OPEN_FLAGS)
    except OSError:
        return None
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return None
        head = os.read(fd, SNIFF_BYTES)
    except OSError:
        return None
    finally:
        os.close(fd)
    return sniff_bytes(head)
