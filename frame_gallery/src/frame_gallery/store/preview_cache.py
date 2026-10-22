"""Private, bounded, disposable previews of exact confirmed uploads (D-246)."""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import os
import re
import stat
from dataclasses import asdict
from pathlib import Path
from typing import Final

from frame_gallery.budget.deadline import Deadline
from frame_gallery.errors import StateError
from frame_gallery.imaging.preview_codec import decode_preview
from frame_gallery.store.atomic import (
    Directory,
    ReadFailure,
    decode_json,
    encode_json,
    open_directory,
)
from frame_gallery.store.delivery_associations import DeliveryAssociation

MAX_CACHE_BYTES: Final = 128 * 1024 * 1024
MAX_CACHE_ENTRIES: Final = 4096
MAX_ENTRY_BYTES: Final = 48 * 1024
MIN_FREE_BYTES: Final = 4 * 1024 * 1024
CACHE_PARTS: Final = ("preview-cache",)
_NAME: Final = re.compile(r"[0-9a-f]{64}\.json")
_TEMP: Final = re.compile(r"[0-9a-f]{64}\.json\.tmp-[0-9a-f]{16}")
_FORMAT: Final = "frame-gallery-preview-cache"


def _identity(binding: DeliveryAssociation) -> list[str]:
    DeliveryAssociation.from_json(asdict(binding))
    if binding.image_rejected:
        raise ValueError("rejected image cannot supply a preview")
    return [binding.device_id, binding.content_id, binding.work_id, binding.jpeg_sha256]


def _name(identity: list[str]) -> str:
    return hashlib.sha256(encode_json({"identity": identity}, 1024)).hexdigest() + ".json"


class PreviewCache:
    def __init__(self, data_root: Path) -> None:
        self._data = data_root

    def remember(self, binding: DeliveryAssociation, encoded: str, deadline: Deadline) -> None:
        identity, image = _identity(binding), decode_preview(encoded)
        raw = encode_json(
            {
                "format": _FORMAT,
                "version": 1,
                "identity": identity,
                "image_sha256": hashlib.sha256(image).hexdigest(),
                "jpeg": encoded,
            },
            MAX_ENTRY_BYTES,
        )
        name = _name(identity)
        deadline.check()
        with open_directory(self._data, CACHE_PARTS, create=True) as directory:
            fd = os.open(
                "cache.lock",
                os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
                0o600,
                dir_fd=directory.fd,
            )
            try:
                if not stat.S_ISREG(os.fstat(fd).st_mode) or os.fstat(fd).st_size:
                    raise StateError("invalid preview cache lock")
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._write(directory, name, raw, deadline)
            finally:
                os.close(fd)

    def _write(self, directory: Directory, name: str, raw: bytes, deadline: Deadline) -> None:
        entries = self._entries(directory, deadline)
        total, count = sum(row[2] for row in entries), len(entries)
        if count > MAX_CACHE_ENTRIES or total > MAX_CACHE_BYTES:
            raise StateError("existing preview cache exceeds limit")
        if directory.read_bytes(name, MAX_ENTRY_BYTES) == raw:
            os.utime(name, dir_fd=directory.fd, follow_symlinks=False)
            return
        space = os.fstatvfs(directory.fd)
        if space.f_bavail * space.f_frsize < MIN_FREE_BYTES + len(raw):
            raise StateError("insufficient free space for optional preview")
        for _, old_name, size in sorted(entries):
            if total + len(raw) <= MAX_CACHE_BYTES and count + 1 <= MAX_CACHE_ENTRIES:
                break
            deadline.check()
            if not directory.unlink(old_name):
                raise StateError("preview cache eviction failed")
            total, count = total - size, count - 1
        if total + len(raw) > MAX_CACHE_BYTES or count + 1 > MAX_CACHE_ENTRIES:
            raise StateError("preview exceeds cache capacity")
        deadline.check()
        staged = directory.stage(name, raw)
        try:
            if directory.read_bytes(staged.temporary, MAX_ENTRY_BYTES) != raw:
                raise StateError("preview cache staging mismatch")
            deadline.check()
            directory.commit(staged, refresh_backup=False)
        finally:
            directory.discard(staged)

    @staticmethod
    def _entries(directory: Directory, deadline: Deadline) -> list[tuple[float, str, int]]:
        entries: list[tuple[float, str, int]] = []
        names = directory.names(MAX_CACHE_ENTRIES + 34)
        if len(names) > MAX_CACHE_ENTRIES + 33:
            raise StateError("preview cache directory limit")
        for entry in names:
            deadline.check()
            if entry == "cache.lock":
                continue
            if _TEMP.fullmatch(entry):
                if not directory.unlink(entry):
                    raise StateError("preview cache temporary cleanup failed")
                continue
            if _NAME.fullmatch(entry) is None:
                raise StateError("unknown preview cache entry")
            info = os.stat(entry, dir_fd=directory.fd, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_ENTRY_BYTES:
                raise StateError("invalid preview cache file")
            entries.append((info.st_mtime, entry, info.st_size))
        return entries

    def lookup(self, binding: DeliveryAssociation, deadline: Deadline) -> bytes | None:
        identity = _identity(binding)
        deadline.check()
        try:
            with open_directory(self._data, CACHE_PARTS) as directory:
                name = _name(identity)
                raw = directory.read_bytes(name, MAX_ENTRY_BYTES)
                if isinstance(raw, ReadFailure):
                    return None
                document = decode_json(raw)
                if (
                    not isinstance(document, dict)
                    or set(document) != {"format", "version", "identity", "image_sha256", "jpeg"}
                    or document["format"] != _FORMAT
                    or type(document["version"]) is not int
                    or document["version"] != 1
                    or document["identity"] != identity
                ):
                    return None
                image = decode_preview(document["jpeg"])
                if document["image_sha256"] != hashlib.sha256(image).hexdigest():
                    return None
                deadline.check()
                # LRU hints are optional; a touch failure cannot lose valid image bytes.
                with contextlib.suppress(OSError):
                    os.utime(name, dir_fd=directory.fd, follow_symlinks=False)
                return image
        except (StateError, ValueError):
            return None
