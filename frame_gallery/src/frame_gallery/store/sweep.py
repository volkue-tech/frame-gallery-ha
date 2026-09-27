"""The startup sweep (§14 item 3).

It runs once per run, in CONFIGURE, after the state lock is held, so no
other run can own what it removes:

- leftover run directories ``run-<16 hex digits>`` below the workspace root,
  removed as whole trees without following a symbolic link;
- our own regular temporary files, ``<name>.tmp-<16 hex digits>`` and
  ``<name>.bak.tmp-<16 hex digits>``, in the state, cache, token, and preview
  directories.

Only entries whose names match exactly, and whose kind is right, are
touched: a symbolic link or any other kind of entry is left alone. Each
directory is scanned for at most 1 000 entries, and a missing directory is
skipped. The sweep never raises.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from frame_gallery.errors import StateError
from frame_gallery.store.atomic import TEMPORARY_NAME, Directory, errno_name, open_directory
from frame_gallery.store.workspace import RUN_NAME

SCAN_LIMIT: Final = 1000

type _Matcher = Callable[[Directory, str], bool]

_log = logging.getLogger("frame_gallery.store")


@dataclass(frozen=True, slots=True)
class SweepTarget:
    """A directory ``anchor/parts…`` (opened without following links)."""

    anchor: Path
    parts: tuple[str, ...]


class StartupSweep:
    """Removes what killed runs left behind. Calling it never raises."""

    def __init__(
        self, *, temporary_files: Sequence[SweepTarget], run_directories: SweepTarget
    ) -> None:
        self._temporary_files = tuple(temporary_files)
        self._run_directories = run_directories

    def __call__(self) -> int:
        """The number of entries removed."""
        removed = sum(self._sweep(target, _is_temporary_file) for target in self._temporary_files)
        removed += self._sweep(self._run_directories, _is_run_directory)
        if removed:
            _log.info("removed %d leftovers of earlier runs", removed)
        return removed

    @staticmethod
    def _sweep(target: SweepTarget, matches: _Matcher) -> int:
        try:
            directory = open_directory(target.anchor, target.parts)
        except StateError as exc:
            _log.debug("not swept: %s", exc)
            return 0
        removed = 0
        with directory:
            try:
                names = directory.names(SCAN_LIMIT)
            except OSError as exc:
                _log.warning("%s could not be swept (%s)", directory.label, errno_name(exc))
                return 0
            for name in names:
                try:
                    if matches(directory, name):
                        directory.remove(name)
                        removed += 1
                except OSError as exc:
                    _log.warning(
                        "%s/%s was not removed (%s)", directory.label, name, errno_name(exc)
                    )
        return removed


def _is_temporary_file(directory: Directory, name: str) -> bool:
    return TEMPORARY_NAME.fullmatch(name) is not None and directory.is_regular_file(name)


def _is_run_directory(directory: Directory, name: str) -> bool:
    return RUN_NAME.fullmatch(name) is not None and directory.is_directory(name)
