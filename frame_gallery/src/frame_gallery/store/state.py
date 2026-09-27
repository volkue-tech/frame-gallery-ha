"""The file-backed state store: lock, history, and the upload ledger (§13).

This implements the runner's ``StateStore`` port over ``/data/state``:

- ``open`` creates the directory (0700), takes ``flock(LOCK_EX | LOCK_NB)``
  on ``.lock`` (contention gives ``already_running``), and then runs the
  startup sweep (§14), so no other run can own the files it removes;
- ``load_exclusions`` reads history and the ledger once per run and returns
  every work in history, every ``uploaded`` work, and every ``uncertain`` work
  whose quarantine has not ended. A file written by a newer
  version, or one that exists but cannot be read, raises ``StateError``;
- ``prestage_history`` writes and ``fsync``s the next history generation as a
  temporary file; ``record_history`` renames it into place after ``selected``;
- ``commit_upload_intent``, ``promote_upload``, and ``remove_upload_intent``
  each write the whole ledger atomically. The intent is committed only when
  it is durable: a failed directory ``fsync`` raises ``StateError`` too, so
  the television is never contacted without a durable intent.

In-memory state always mirrors the files: after a write that failed before
its rename, the previous entries stay; after one that failed only in the
directory ``fsync``, the new entries are kept, because the file holds them.
"""

from __future__ import annotations

import contextlib
import errno
import fcntl
import logging
import os
from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Final

from frame_gallery.budget.clock import Clock
from frame_gallery.budget.deadline import Deadline
from frame_gallery.errors import AlreadyRunning, StateError
from frame_gallery.selection.exclusion import ExclusionSet
from frame_gallery.store.atomic import (
    CommitError,
    Directory,
    DocumentFile,
    Quarantine,
    ReadResult,
    Staged,
    errno_name,
    open_directory,
)
from frame_gallery.store.history import (
    HISTORY_FILE,
    HISTORY_SPEC,
    HistoryEntry,
    append_bounded,
    history_document,
)
from frame_gallery.store.upload_ledger import (
    LEDGER_FILE,
    LEDGER_SPEC,
    LedgerEntry,
    bounded,
    excluded_ids,
    ledger_document,
    promoted,
    pruned,
    with_intent,
    without_intent,
)

STATE_DIRECTORY: Final = "state"
LOCK_FILE: Final = ".lock"
_LOCK_FLAGS: Final = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC

_log = logging.getLogger("frame_gallery.store")

type Sweep = Callable[[], object]
"""The startup sweep (§14); it never raises."""


def _usable[T](result: ReadResult[T], name: str) -> T | None:
    if result.newer_version is not None:
        msg = f"{name} was written by a newer version ({result.newer_version})"
        raise StateError(msg)
    if result.unreadable:
        msg = f"{name} exists but cannot be read"
        raise StateError(msg)
    return result.value


class FileStateStore:
    """The ``StateStore`` port over ``<data>/state``. One instance serves one run."""

    def __init__(self, data_root: Path, *, clock: Clock, sweep: Sweep | None = None) -> None:
        self._data_root = data_root
        self._clock = clock
        self._sweep = sweep
        self._directory: Directory | None = None
        self._lock_fd: int | None = None
        self._history_file: DocumentFile[tuple[HistoryEntry, ...]] | None = None
        self._ledger_file: DocumentFile[tuple[LedgerEntry, ...]] | None = None
        self._history: tuple[HistoryEntry, ...] | None = None
        self._ledger: tuple[LedgerEntry, ...] = ()
        self._prestaged: tuple[Staged, tuple[HistoryEntry, ...]] | None = None

    # ---------------------------------------------------------------- open

    def open(self, deadline: Deadline) -> None:
        """Create the directory, take the lock, and sweep leftovers.

        Raises ``AlreadyRunning`` or ``StateError``.
        """
        deadline.check()
        directory = open_directory(self._data_root, (STATE_DIRECTORY,), create=True, mode=0o700)
        self._directory = directory
        self._lock_fd = self._lock(directory)
        quarantine = Quarantine(directory, self._clock.utc_now)
        self._history_file = DocumentFile(
            directory, HISTORY_FILE, HISTORY_SPEC, backup=True, quarantine=quarantine
        )
        self._ledger_file = DocumentFile(
            directory, LEDGER_FILE, LEDGER_SPEC, backup=True, quarantine=quarantine
        )
        if self._sweep is not None:
            try:
                self._sweep()
            except Exception:  # noqa: BLE001 - the sweep is best-effort by design
                _log.warning("the startup sweep failed", exc_info=True)

    @staticmethod
    def _lock(directory: Directory) -> int:
        try:
            fd = os.open(LOCK_FILE, _LOCK_FLAGS, 0o600, dir_fd=directory.fd)
        except OSError as exc:
            msg = f"{directory.label}/{LOCK_FILE}: cannot open the lock ({errno_name(exc)})"
            raise StateError(msg) from None
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(fd)
            if exc.errno in (errno.EWOULDBLOCK, errno.EAGAIN):
                raise AlreadyRunning from None
            msg = f"{directory.label}/{LOCK_FILE}: cannot take the lock ({errno_name(exc)})"
            raise StateError(msg) from None
        return fd

    # ---------------------------------------------------------- exclusions

    def load_exclusions(self, now: datetime) -> ExclusionSet:
        """History, ``uploaded``, and unexpired ``uncertain`` identifiers.

        Raises ``StateError`` for a newer or unreadable history or ledger.
        """
        history = self._loaded_history()
        uploaded, uncertain = excluded_ids(self._ledger, now)
        return ExclusionSet(
            history=frozenset(e.qualified_id for e in history),
            uploaded=uploaded,
            uncertain=uncertain,
        )

    def _loaded_history(self) -> tuple[HistoryEntry, ...]:
        if self._history is None:
            history = _usable(self._files()[0].load(), HISTORY_FILE) or ()
            self._ledger = _usable(self._files()[1].load(), LEDGER_FILE) or ()
            self._history = history
        return self._history

    def _files(
        self,
    ) -> tuple[DocumentFile[tuple[HistoryEntry, ...]], DocumentFile[tuple[LedgerEntry, ...]]]:
        if self._history_file is None or self._ledger_file is None:
            msg = "the state store is not open"
            raise StateError(msg)
        return self._history_file, self._ledger_file

    # ------------------------------------------------------------- history

    def prestage_history(self, qualified_id: str, now: datetime) -> None:
        """Write and ``fsync`` the next history generation as a temporary
        file (steps 2 and 3). Raises ``StateError``."""
        history = self._loaded_history()
        self.discard_prestaged_history()
        entries = append_bounded(history, HistoryEntry(qualified_id, now))
        staged = self._files()[0].stage(history_document(entries))
        self._prestaged = (staged, entries)

    def discard_prestaged_history(self) -> None:
        """Remove the pre-staged generation, if any (never raises)."""
        prestaged, self._prestaged = self._prestaged, None
        if prestaged is not None and self._history_file is not None:
            self._history_file.discard(prestaged[0])

    def record_history(self) -> None:
        """Rename the pre-staged generation into place (steps 4 to 6).

        Raises ``StateError`` if the rename fails. A failed directory
        ``fsync`` after the rename only logs a warning: the history is in
        place, and the ledger's ``uploaded`` entry excludes the work anyway.
        """
        if self._prestaged is None:
            msg = "no history generation was pre-staged"
            raise StateError(msg)
        (staged, entries), self._prestaged = self._prestaged, None
        try:
            self._files()[0].commit(staged)
        except CommitError as exc:
            if not exc.replaced:
                raise
            _log.warning("history was recorded, but it may not be durable yet: %s", exc)
        self._history = entries

    # -------------------------------------------------------------- ledger

    def commit_upload_intent(self, qualified_id: str, now: datetime) -> None:
        """Durably record an ``uncertain`` intent; works now in history and
        expired intents are pruned. Raises ``StateError``."""
        history = {e.qualified_id for e in self._loaded_history()}
        current = pruned(self._ledger, history=history, now=now)
        self._write_ledger(bounded(with_intent(current, qualified_id, now), keep=qualified_id))

    def promote_upload(self, qualified_id: str, now: datetime) -> None:
        """Record the confirmed upload. Raises ``StateError``."""
        self._loaded_history()
        self._write_ledger(bounded(promoted(self._ledger, qualified_id, now), keep=qualified_id))

    def remove_upload_intent(self, qualified_id: str) -> None:
        """Remove the ``uncertain`` intent; an ``uploaded`` entry stays.
        Raises ``StateError``."""
        self._loaded_history()
        entries = without_intent(self._ledger, qualified_id)
        if entries != self._ledger:
            self._write_ledger(entries)

    def _write_ledger(self, entries: Sequence[LedgerEntry]) -> None:
        new = tuple(entries)
        try:
            self._files()[1].write(ledger_document(new))
        except CommitError as exc:
            if exc.replaced:
                self._ledger = new
            raise
        self._ledger = new

    # --------------------------------------------------------------- close

    def close(self) -> None:
        """Discard a leftover pre-staged file and release the lock (never raises)."""
        self.discard_prestaged_history()
        lock_fd, self._lock_fd = self._lock_fd, None
        if lock_fd is not None:
            with contextlib.suppress(OSError):
                os.close(lock_fd)
        directory, self._directory = self._directory, None
        if directory is not None:
            directory.close()
        self._history_file = self._ledger_file = None
