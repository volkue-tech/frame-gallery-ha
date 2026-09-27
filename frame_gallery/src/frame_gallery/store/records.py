"""The run records in ``/data/state`` (§13.1).

- ``current.json``: the artwork on the television, written only after
  ``selected``. Besides the runner's record it keeps the D-118 fingerprints
  of the last 10 published previews, newest first, which the local library
  skips (guard 3, F7). The runner passes the new fingerprint as a one-item
  ``preview_fingerprints`` list; the store adds the earlier ones.
- ``last_run.json``: the outcome and statistics of the latest run, written for
  every outcome except watchdog termination.

Both are at most 16 KiB and written with the atomic primitive, without
``.bak``. A damaged ``current.json`` is quarantined; its fingerprints are then
lost, and guards 1 and 2 still keep the preview directory out of the library.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from frame_gallery.budget.clock import Clock
from frame_gallery.budget.deadline import Deadline
from frame_gallery.errors import StateError
from frame_gallery.store.atomic import (
    CommitError,
    Directory,
    DocumentFile,
    DocumentSpec,
    Quarantine,
    open_directory,
)
from frame_gallery.store.fields import parse_qualified_id, parse_timestamp

STATE_DIRECTORY: Final = "state"
CURRENT_FILE: Final = "current.json"
LAST_RUN_FILE: Final = "last_run.json"
CURRENT_FORMAT: Final = "frame-gallery-current"
LAST_RUN_FORMAT: Final = "frame-gallery-last-run"
RECORD_VERSION: Final = 1
MAX_RECORD_BYTES: Final = 16 * 1024
MAX_FINGERPRINTS: Final = 10
FINGERPRINT: Final = re.compile(r"[0-9a-f]{64}")

_log = logging.getLogger("frame_gallery.store")


def _fingerprints(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > MAX_FINGERPRINTS:
        msg = "invalid preview fingerprints"
        raise ValueError(msg)
    for item in value:
        if not isinstance(item, str) or FINGERPRINT.fullmatch(item) is None:
            msg = "invalid preview fingerprint"
            raise ValueError(msg)
    return tuple(value)


def parse_current(document: Mapping[str, object]) -> tuple[str, ...]:
    """The preview fingerprints of a valid ``current.json``. Raises ``ValueError``."""
    parse_qualified_id(document.get("id"))
    sha256 = document.get("sha256")
    if not isinstance(sha256, str) or FINGERPRINT.fullmatch(sha256) is None:
        msg = "invalid sha256"
        raise ValueError(msg)
    parse_timestamp(document.get("delivered_at"))
    if not isinstance(document.get("attribution"), dict):
        msg = "invalid attribution"
        raise ValueError(msg)
    return _fingerprints(document.get("preview_fingerprints"))


def parse_last_run(document: Mapping[str, object]) -> str:
    """The outcome of a valid ``last_run.json``. Raises ``ValueError``."""
    outcome = document.get("outcome")
    if not isinstance(outcome, str) or not outcome:
        msg = "invalid outcome"
        raise ValueError(msg)
    parse_timestamp(document.get("finished_at"))
    return outcome


CURRENT_SPEC: Final = DocumentSpec(CURRENT_FORMAT, RECORD_VERSION, MAX_RECORD_BYTES, parse_current)
LAST_RUN_SPEC: Final = DocumentSpec(
    LAST_RUN_FORMAT, RECORD_VERSION, MAX_RECORD_BYTES, parse_last_run
)


def merged_fingerprints(new: tuple[str, ...], earlier: tuple[str, ...]) -> list[str]:
    """Newest first, without repeats, at most :data:`MAX_FINGERPRINTS`."""
    return list(dict.fromkeys((*new, *earlier)))[:MAX_FINGERPRINTS]


class RunRecordStore:
    """The ``RunRecords`` port over ``<data>/state``."""

    def __init__(self, data_root: Path, *, clock: Clock) -> None:
        self._data_root = data_root
        self._clock = clock

    def write_current(self, record: Mapping[str, object], deadline: Deadline) -> None:
        """Write ``current.json`` with the last preview fingerprints.
        Raises ``StateError`` or ``DeadlineExceeded``."""
        deadline.check()
        try:
            new = _fingerprints(record.get("preview_fingerprints"))
        except ValueError as exc:
            raise StateError(str(exc)) from None
        with self._open() as directory:
            earlier = self._current(directory).load().value or ()
            document = dict(record, preview_fingerprints=merged_fingerprints(new, earlier))
            _write(DocumentFile(directory, CURRENT_FILE, CURRENT_SPEC), document)

    def write_last_run(self, record: Mapping[str, object], deadline: Deadline) -> None:
        """Write ``last_run.json``. Raises ``StateError`` or ``DeadlineExceeded``."""
        deadline.check()
        with self._open() as directory:
            _write(DocumentFile(directory, LAST_RUN_FILE, LAST_RUN_SPEC), record)

    def preview_fingerprints(self) -> tuple[str, ...]:
        """The fingerprints of the last published previews, newest first, for
        the local library's guard 3. Never raises."""
        try:
            directory = open_directory(self._data_root, (STATE_DIRECTORY,))
        except StateError as exc:
            _log.debug("no run records: %s", exc)
            return ()
        with directory:
            return self._current(directory).load().value or ()

    def _open(self) -> Directory:
        return open_directory(self._data_root, (STATE_DIRECTORY,), create=True, mode=0o700)

    def _current(self, directory: Directory) -> DocumentFile[tuple[str, ...]]:
        quarantine = Quarantine(directory, self._clock.utc_now)
        return DocumentFile(directory, CURRENT_FILE, CURRENT_SPEC, quarantine=quarantine)


def _write[T](file: DocumentFile[T], document: Mapping[str, object]) -> None:
    try:
        file.write(document)
    except CommitError as exc:
        if not exc.replaced:
            raise
        _log.warning("%s was written, but it may not be durable yet: %s", file.name, exc)
