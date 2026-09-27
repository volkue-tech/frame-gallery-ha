"""The bounded content fingerprint of a file (§9.3, D-118).

SHA-256 over the size (8 bytes, big-endian), the first 64 KiB, and the last
64 KiB. For a file under 64 KiB both parts are the whole file. The local
library identifies its files by it, and the store records it for each
published preview, so a preview copied into the library is recognised
(guard 3, F7).
"""

from __future__ import annotations

import hashlib
import os
from typing import Final

FINGERPRINT_EDGE: Final = 64 * 1024


def _digest(size: int, head: bytes, tail: bytes) -> str:
    return hashlib.sha256(size.to_bytes(8, "big") + head + tail).hexdigest()


def fingerprint_bytes(data: bytes) -> str:
    """The fingerprint of ``data`` (for example a published preview)."""
    size = len(data)
    return _digest(size, data[:FINGERPRINT_EDGE], data[max(0, size - FINGERPRINT_EDGE) :])


def fingerprint_fd(fd: int, size: int) -> str | None:
    """The fingerprint of an open regular file of ``size`` bytes, or ``None``
    if the file is shorter than that (it changed)."""
    edge = min(FINGERPRINT_EDGE, size)
    head = os.pread(fd, edge, 0)
    tail = os.pread(fd, edge, size - edge)
    if len(head) != edge or len(tail) != edge:
        return None
    return _digest(size, head, tail)
