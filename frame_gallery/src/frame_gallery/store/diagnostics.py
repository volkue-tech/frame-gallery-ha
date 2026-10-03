"""Read-only, bounded storage statistics, without paths, names or contents.

After normal cleanup the parent reports only counts and apparent byte sizes
of fixed app-owned directories. It never follows symlinks, opens file contents,
creates a directory or removes anything. An unavailable or partial scan is
explicitly marked; it is not evidence that a directory is empty (D-175).
"""

from __future__ import annotations

import logging
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from frame_gallery.budget.clock import Clock
from frame_gallery.budget.deadline import Deadline
from frame_gallery.errors import StateError
from frame_gallery.store.atomic import TEMPORARY_NAME, open_directory
from frame_gallery.store.workspace import RUN_NAME

if TYPE_CHECKING:
    from frame_gallery.store.layout import StoreLayout

ENTRY_LIMIT: Final = 128
REPORT_SECONDS: Final = 0.5
_log = logging.getLogger("frame_gallery.storage")


@dataclass(slots=True)
class StorageStats:
    status: str = "ok"
    files: int = 0
    bytes: int = 0
    temporary_files: int = 0
    run_directories: int = 0
    other_entries: int = 0
    unreadable_entries: int = 0
    truncated: bool = False


def inspect_directory(anchor: Path, parts: tuple[str, ...], deadline: Deadline) -> StorageStats:
    """At most 128 direct entries, using directory descriptors and lstat."""
    result = StorageStats()
    try:
        with open_directory(anchor, parts) as directory:
            names = directory.names(ENTRY_LIMIT + 1)
            result.truncated = len(names) > ENTRY_LIMIT
            for name in names[:ENTRY_LIMIT]:
                if deadline.remaining() <= 0:
                    result.truncated = True
                    break
                try:
                    info = os.stat(name, dir_fd=directory.fd, follow_symlinks=False)
                except OSError:
                    result.unreadable_entries += 1
                    continue
                if stat.S_ISREG(info.st_mode):
                    result.files += 1
                    result.bytes += info.st_size
                    result.temporary_files += int(TEMPORARY_NAME.fullmatch(name) is not None)
                elif stat.S_ISDIR(info.st_mode) and RUN_NAME.fullmatch(name):
                    result.run_directories += 1
                else:
                    result.other_entries += 1
    except (StateError, OSError):
        result.status = "unavailable"
    return result


def log_storage(layout: StoreLayout, clock: Clock) -> None:
    """One shared half-second budget, six fixed shallow scans, count-only logs."""
    deadline = Deadline.after(clock, REPORT_SECONDS, "storage_report")
    buckets = (
        ("state", layout.data, ("state",)),
        ("quarantine", layout.data, ("state", "quarantine")),
        ("cache", layout.data, ("cache",)),
        ("tv", layout.data, ("tv",)),
        ("preview", layout.media, ("frame_gallery", "preview")),
        ("scratch", layout.tmp, ("frame-gallery",)),
    )
    for label, anchor, parts in buckets:
        if deadline.remaining() <= 0:
            _log.info("storage: bucket=%s status=not_scanned truncated=true", label)
            continue
        result = inspect_directory(anchor, parts, deadline)
        _log.info(
            "storage: bucket=%s status=%s files=%d bytes=%d temporary_files=%d "
            "run_directories=%d other_entries=%d unreadable_entries=%d truncated=%s",
            label,
            result.status,
            result.files,
            result.bytes,
            result.temporary_files,
            result.run_directories,
            result.other_entries,
            result.unreadable_entries,
            str(result.truncated).lower(),
        )
