"""Stable TV identity from an existing device response, with no network I/O."""

from __future__ import annotations

import hashlib
import re
from typing import Final

DEVICE_DIGEST: Final = re.compile(r"[0-9a-f]{64}")


def device_digest(info: object) -> str | None:
    if not isinstance(info, dict):
        return None
    device = info.get("device")
    if not isinstance(device, dict):
        return None
    identity = device.get("id")
    if not isinstance(identity, str):
        return None
    identity = identity.strip().lower()
    if not 1 <= len(identity) <= 128 or any(ord(c) < 32 for c in identity):
        return None
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()
