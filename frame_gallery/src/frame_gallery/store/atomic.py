"""The atomic, recoverable write primitive and the bounded reader (§13.2, D-110).

Every persistent file goes through one primitive that works relative to a
directory file descriptor, so a path component swapped for a symbolic link
during the run cannot redirect a write:

1. the directory is opened with ``O_DIRECTORY | O_NOFOLLOW``;
2. the document is serialized, bounded, and checked by reading it back with
   the same rules the reader applies;
3. ``<name>.tmp-<random>`` is created with ``O_CREAT | O_EXCL | O_NOFOLLOW``,
   written, and ``fsync``ed;
4. for history and the ledger only, ``<name>.bak`` is refreshed from the
   current primary, if that primary is valid, through a hard link
   ``<name>.bak.tmp-<random>`` and a rename. This step is best-effort and
   never blocks step 5;
5. the temporary file is renamed over the target;
6. the directory is ``fsync``ed.

PRE-STAGE runs steps 2 and 3 alone (:meth:`DocumentFile.stage`); RECORD then
runs steps 4 to 6 (:meth:`DocumentFile.commit`), so recording history after
``selected`` is a single rename.

The reader tries the primary, then ``.bak``, then gives up with an empty
result. Only parse and schema failures are quarantined, and at most three
quarantined files are kept. A document written by a newer version, or a file
that exists but cannot be read, is not corruption: the reader reports it and
the caller decides (history and the ledger then end the run with
``state_error``). The reader never raises.
"""

from __future__ import annotations

import contextlib
import enum
import errno
import itertools
import json
import logging
import os
import re
import secrets
import shutil
import stat
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Self

from frame_gallery.errors import StateError

DIRECTORY_FLAGS: Final = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
READ_FLAGS: Final = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
"""``O_NONBLOCK`` keeps a FIFO from blocking the open; ``fstat`` then refuses it."""

CREATE_FLAGS: Final = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC

FILE_NAME: Final = re.compile(r"[A-Za-z0-9_-][A-Za-z0-9_.-]{0,99}")
TEMPORARY_MARKER: Final = ".tmp-"
TEMPORARY_NAME: Final = re.compile(r"[A-Za-z0-9_-][A-Za-z0-9_.-]{0,99}\.tmp-[0-9a-f]{16}")
"""Our own temporary files, ``<name>.tmp-<16 hex digits>`` and
``<name>.bak.tmp-<16 hex digits>``: what the startup sweep removes (§14)."""

BACKUP_SUFFIX: Final = ".bak"
QUARANTINE_DIRECTORY: Final = "quarantine"
QUARANTINE_LIMIT: Final = 3
QUARANTINE_SCAN_LIMIT: Final = 64
READ_CHUNK: Final = 1024 * 1024

_NOT_REGULAR_ERRNOS: Final = frozenset({errno.ELOOP, errno.ENXIO, errno.EOPNOTSUPP})
"""``ELOOP``: a symbolic link (``O_NOFOLLOW``); ``ENXIO`` (Linux) and
``EOPNOTSUPP`` (macOS): a socket."""

_log = logging.getLogger("frame_gallery.store")


def new_token() -> str:
    """16 random hex digits for a temporary name; ``O_EXCL`` guards collisions."""
    return secrets.token_hex(8)


def errno_name(exc: OSError) -> str:
    return errno.errorcode.get(exc.errno or 0, "error")


def _refusal(exc: OSError) -> str:
    if exc.errno in (errno.ELOOP, errno.ENOTDIR):
        return "a symbolic link or not a directory"
    return errno_name(exc)


def check_name(name: str) -> str:
    """A plain file name of ours: no separator, no leading dot, and no
    temporary marker. Raises ``ValueError``."""
    if FILE_NAME.fullmatch(name) is None or TEMPORARY_MARKER in name:
        msg = f"invalid file name {name!r}"
        raise ValueError(msg)
    return name


def _close_quietly(fd: int) -> None:
    with contextlib.suppress(OSError):
        os.close(fd)


class CommitError(StateError):
    """A staged file could not replace its target.

    ``replaced`` is true when the rename succeeded and only the directory
    ``fsync`` failed: the new content is in place but may not be durable.
    """

    def __init__(self, message: str, *, replaced: bool) -> None:
        super().__init__(message)
        self.replaced = replaced


class ReadFailure(enum.StrEnum):
    MISSING = "missing"
    NOT_REGULAR = "not a regular file"
    OVERSIZE = "over its size limit"
    UNREADABLE = "unreadable"


@dataclass(frozen=True, slots=True)
class Staged:
    """A written and ``fsync``ed temporary file that has not replaced its target."""

    name: str
    temporary: str


# --- directories ----------------------------------------------------------------


def open_directory(
    anchor: Path, parts: Sequence[str] = (), *, create: bool = False, mode: int = 0o700
) -> Directory:
    """Open ``anchor/parts…`` as a :class:`Directory`.

    Neither the anchor's last component nor any of ``parts`` may be a symbolic
    link. Missing ``parts`` are created with ``mode`` if ``create`` is set.
    Raises :class:`StateError`.
    """
    for part in parts:
        check_name(part)
    label = str(anchor.joinpath(*parts))
    try:
        fd = os.open(anchor, DIRECTORY_FLAGS)
    except OSError as exc:
        msg = f"{label}: cannot open {anchor} ({_refusal(exc)})"
        raise StateError(msg) from None
    for part in parts:
        fd = _open_child(fd, part, label, create=create, mode=mode)
    return Directory(fd, label)


def _open_child(parent: int, name: str, label: str, *, create: bool, mode: int) -> int:
    """Open, and create if asked, the directory ``name`` below ``parent``.

    Always closes ``parent``. Raises :class:`StateError`.
    """
    try:
        try:
            return os.open(name, DIRECTORY_FLAGS, dir_fd=parent)
        except FileNotFoundError:
            if not create:
                raise
        with contextlib.suppress(FileExistsError):  # created meanwhile: open it
            os.mkdir(name, mode, dir_fd=parent)
        return os.open(name, DIRECTORY_FLAGS, dir_fd=parent)
    except OSError as exc:
        msg = f"{label}: cannot open {name} ({_refusal(exc)})"
        raise StateError(msg) from None
    finally:
        _close_quietly(parent)


class Directory:
    """An open directory. Every operation is relative to its descriptor."""

    __slots__ = ("_fd", "label")

    def __init__(self, fd: int, label: str) -> None:
        self._fd: int | None = fd
        self.label = label
        """The path, for log messages only."""

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    @property
    def fd(self) -> int:
        if self._fd is None:
            msg = f"{self.label}: the directory is closed"
            raise StateError(msg)
        return self._fd

    def close(self) -> None:
        """Idempotent; never raises."""
        fd, self._fd = self._fd, None
        if fd is not None:
            _close_quietly(fd)

    def child(self, name: str, *, create: bool = False, mode: int = 0o700) -> Directory:
        """Open the subdirectory ``name`` without following a symbolic link.
        Raises :class:`StateError`."""
        check_name(name)
        label = f"{self.label}/{name}"
        try:
            parent = os.dup(self.fd)
        except OSError as exc:
            msg = f"{label}: cannot open ({errno_name(exc)})"
            raise StateError(msg) from None
        return Directory(_open_child(parent, name, label, create=create, mode=mode), label)

    # ---------------------------------------------------------------- reading

    def read_bytes(self, name: str, max_bytes: int) -> bytes | ReadFailure:
        """The whole regular file ``name``, read at most once and never more
        than ``max_bytes``; otherwise why not. Never raises ``OSError``."""
        try:
            fd = os.open(name, READ_FLAGS, dir_fd=self.fd)
        except FileNotFoundError:
            return ReadFailure.MISSING
        except OSError as exc:
            if exc.errno in _NOT_REGULAR_ERRNOS:
                return ReadFailure.NOT_REGULAR
            return ReadFailure.UNREADABLE
        try:
            return _read_regular(fd, max_bytes)
        except OSError:
            return ReadFailure.UNREADABLE
        finally:
            _close_quietly(fd)

    def names(self, limit: int) -> list[str]:
        """At most ``limit`` entry names, in no particular order. Raises ``OSError``."""
        with os.scandir(self.fd) as entries:
            return [entry.name for entry in itertools.islice(entries, limit)]

    def is_regular_file(self, name: str) -> bool:
        """Whether ``name`` is a regular file (a link is not). Raises ``OSError``."""
        return stat.S_ISREG(os.stat(name, dir_fd=self.fd, follow_symlinks=False).st_mode)

    def is_directory(self, name: str) -> bool:
        """Whether ``name`` is a directory (a link is not). Raises ``OSError``."""
        return stat.S_ISDIR(os.stat(name, dir_fd=self.fd, follow_symlinks=False).st_mode)

    # ---------------------------------------------------------------- writing

    def stage(self, name: str, data: bytes, *, mode: int = 0o600) -> Staged:
        """Step 3: write ``data`` to a new temporary file with exactly ``mode``
        and ``fsync`` it. Raises :class:`StateError`."""
        check_name(name)
        temporary = f"{name}{TEMPORARY_MARKER}{new_token()}"
        try:
            fd = os.open(temporary, CREATE_FLAGS, mode, dir_fd=self.fd)
        except OSError as exc:
            msg = f"{self.label}/{name}: cannot create a temporary file ({errno_name(exc)})"
            raise StateError(msg) from None
        try:
            try:
                os.fchmod(fd, mode)  # the umask may have narrowed the mode
                _write_all(fd, data)
                os.fsync(fd)
            finally:
                os.close(fd)
        except OSError as exc:
            self.unlink(temporary)
            msg = f"{self.label}/{name}: cannot write ({errno_name(exc)})"
            raise StateError(msg) from None
        return Staged(name, temporary)

    def commit(self, staged: Staged, *, refresh_backup: bool) -> None:
        """Steps 4 to 6. Raises :class:`CommitError`."""
        fd = self.fd
        if refresh_backup:
            self._refresh_backup(staged.name)
        try:
            os.rename(staged.temporary, staged.name, src_dir_fd=fd, dst_dir_fd=fd)
        except OSError as exc:
            self.unlink(staged.temporary)
            msg = f"{self.label}/{staged.name}: cannot replace the file ({errno_name(exc)})"
            raise CommitError(msg, replaced=False) from None
        try:
            os.fsync(fd)
        except OSError as exc:
            msg = f"{self.label}: the directory could not be flushed ({errno_name(exc)})"
            raise CommitError(msg, replaced=True) from None

    def discard(self, staged: Staged) -> None:
        """Remove a staged file that will not be committed (never raises)."""
        self.unlink(staged.temporary)

    def write(
        self, name: str, data: bytes, *, refresh_backup: bool = False, mode: int = 0o600
    ) -> None:
        """Steps 3 to 6. Raises :class:`StateError`."""
        self.commit(self.stage(name, data, mode=mode), refresh_backup=refresh_backup)

    def unlink(self, name: str) -> bool:
        """Remove the file or link ``name``; whether it was removed (never raises)."""
        try:
            os.unlink(name, dir_fd=self.fd)
        except OSError:
            return False
        return True

    def remove(self, name: str) -> None:
        """Remove the file, link, or whole directory tree ``name``, never
        following a link. Raises ``OSError``."""
        if self.is_directory(name):
            shutil.rmtree(name, dir_fd=self.fd)
        else:
            os.unlink(name, dir_fd=self.fd)

    def rename_into(self, name: str, other: Directory, new_name: str) -> None:
        """Move ``name`` into ``other`` as ``new_name``. Raises ``OSError``."""
        os.rename(name, new_name, src_dir_fd=self.fd, dst_dir_fd=other.fd)

    def _refresh_backup(self, name: str) -> None:
        """Step 4: point ``<name>.bak`` at the current primary (never raises)."""
        fd = self.fd
        temporary = f"{name}{BACKUP_SUFFIX}{TEMPORARY_MARKER}{new_token()}"
        try:
            os.link(name, temporary, src_dir_fd=fd, dst_dir_fd=fd, follow_symlinks=False)
            try:
                os.rename(temporary, name + BACKUP_SUFFIX, src_dir_fd=fd, dst_dir_fd=fd)
            except OSError:
                self.unlink(temporary)
                raise
        except OSError as exc:
            _log.warning(
                "%s/%s: the backup copy was not refreshed (%s)",
                self.label,
                name,
                errno_name(exc),
            )


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError(errno.EIO, "no progress while writing")
        view = view[written:]


def _read_regular(fd: int, max_bytes: int) -> bytes | ReadFailure:
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode):
        return ReadFailure.NOT_REGULAR
    if info.st_size > max_bytes:
        return ReadFailure.OVERSIZE
    data = _read_at_most(fd, max_bytes + 1)
    return ReadFailure.OVERSIZE if len(data) > max_bytes else data


def _read_at_most(fd: int, limit: int) -> bytes:
    chunks: list[bytes] = []
    remaining = limit
    while remaining > 0:
        chunk = os.read(fd, min(READ_CHUNK, remaining))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


# --- documents -----------------------------------------------------------------


def _refuse_constant(name: str) -> object:
    msg = f"{name} is not allowed"
    raise ValueError(msg)


def decode_json(data: bytes) -> object:
    """Parse JSON; ``NaN`` and ``Infinity`` are refused. Raises ``ValueError``."""
    try:
        return json.loads(data, parse_constant=_refuse_constant)
    except RecursionError:
        msg = "nested too deeply"
        raise ValueError(msg) from None


def encode_json(document: Mapping[str, object], max_bytes: int) -> bytes:
    """Compact, ASCII-only JSON of at most ``max_bytes`` that parses back to an
    equal value. Raises :class:`StateError`."""
    try:
        text = json.dumps(document, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        msg = f"the document cannot be serialized ({type(exc).__name__})"
        raise StateError(msg) from None
    data = text.encode("ascii")
    if len(data) > max_bytes:
        msg = f"the document exceeds {max_bytes} bytes"
        raise StateError(msg)
    if decode_json(data) != dict(document):
        msg = "the document does not survive serialization"
        raise StateError(msg)
    return data


@dataclass(frozen=True, slots=True)
class DocumentSpec[T]:
    """What a valid document looks like."""

    format: str
    version: int
    """The newest version this code writes and reads."""

    max_bytes: int
    parse: Callable[[Mapping[str, object]], T]
    """Validates the whole document and returns its value; raises ``ValueError``."""


class Origin(enum.StrEnum):
    PRIMARY = "primary"
    BACKUP = "backup"
    EMPTY = "empty"


@dataclass(frozen=True, slots=True)
class ReadResult[T]:
    value: T | None
    """``None`` when no usable copy was found (``origin`` is ``EMPTY``)."""

    origin: Origin
    primary_valid: bool
    newer_version: int | None = None
    """Set when the primary or ``.bak`` was written by a newer version."""

    unreadable: bool = False
    """Set when the primary or ``.bak`` exists but cannot be read (for example
    ``EACCES`` or ``EIO``). Such a file is not quarantined."""

    @property
    def usable(self) -> bool:
        """Neither a newer version nor an unreadable file was found."""
        return self.newer_version is None and not self.unreadable


class _Kind(enum.Enum):
    VALID = enum.auto()
    MISSING = enum.auto()
    CORRUPT = enum.auto()
    NEWER = enum.auto()
    UNREADABLE = enum.auto()


_FAILURE_KINDS: Final = {
    ReadFailure.MISSING: _Kind.MISSING,
    ReadFailure.UNREADABLE: _Kind.UNREADABLE,
}
"""Every other read failure (not a regular file, oversize) is damage."""


@dataclass(frozen=True, slots=True)
class _Verdict[T]:
    kind: _Kind
    value: T | None = None
    version: int | None = None
    reason: str = ""


class _Damaged(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class _Newer(Exception):
    def __init__(self, version: int) -> None:
        super().__init__(version)
        self.version = version


def _decode_document[T](raw: bytes, spec: DocumentSpec[T]) -> T:
    """The document's value. Raises :class:`_Damaged` or :class:`_Newer`."""
    try:
        document = decode_json(raw)
    except ValueError:
        raise _Damaged("not valid JSON") from None
    if not isinstance(document, dict) or document.get("format") != spec.format:
        raise _Damaged(f"not a {spec.format} document")
    version = document.get("version")
    if isinstance(version, bool) or not isinstance(version, int):
        raise _Damaged("no valid version")
    if version > spec.version:
        raise _Newer(version)
    if version != spec.version:
        raise _Damaged(f"unsupported version {version}")
    try:
        return spec.parse(document)
    except ValueError as exc:
        raise _Damaged(f"invalid content: {exc}") from None


def _judge[T](raw: bytes | ReadFailure, spec: DocumentSpec[T]) -> _Verdict[T]:
    if isinstance(raw, ReadFailure):
        return _Verdict(_FAILURE_KINDS.get(raw, _Kind.CORRUPT), reason=raw.value)
    try:
        return _Verdict(_Kind.VALID, value=_decode_document(raw, spec))
    except _Newer as newer:
        return _Verdict(_Kind.NEWER, version=newer.version)
    except _Damaged as damaged:
        return _Verdict(_Kind.CORRUPT, reason=damaged.reason)


def _conclusive[T](verdict: _Verdict[T], origin: Origin) -> ReadResult[T] | None:
    """The result if ``verdict`` ends the search, otherwise ``None``."""
    if verdict.kind is _Kind.VALID:
        return ReadResult(verdict.value, origin, primary_valid=origin is Origin.PRIMARY)
    if verdict.kind is _Kind.NEWER:
        return ReadResult(None, Origin.EMPTY, primary_valid=False, newer_version=verdict.version)
    if verdict.kind is _Kind.UNREADABLE:
        return ReadResult(None, Origin.EMPTY, primary_valid=False, unreadable=True)
    return None


def _set_aside_if_damaged[T](
    verdict: _Verdict[T], directory: Directory, name: str, quarantine: Quarantine | None
) -> bool:
    if verdict.kind is not _Kind.CORRUPT:
        return False
    _log.warning("%s/%s is damaged (%s)", directory.label, name, verdict.reason)
    if quarantine is not None:
        quarantine.take(name)
    return True


def read_document[T](
    directory: Directory,
    name: str,
    spec: DocumentSpec[T],
    *,
    backup: bool,
    quarantine: Quarantine | None,
) -> ReadResult[T]:
    """Primary, then ``.bak`` (if ``backup``), then empty. Never raises."""
    primary = _judge(directory.read_bytes(name, spec.max_bytes), spec)
    result = _conclusive(primary, Origin.PRIMARY)
    if result is not None:
        return result
    damaged = _set_aside_if_damaged(primary, directory, name, quarantine)
    if backup:
        copy = name + BACKUP_SUFFIX
        second = _judge(directory.read_bytes(copy, spec.max_bytes), spec)
        result = _conclusive(second, Origin.BACKUP)
        if result is not None:
            if result.origin is Origin.BACKUP:
                _log.warning("%s/%s: using the backup copy", directory.label, name)
            return result
        damaged = _set_aside_if_damaged(second, directory, copy, quarantine) or damaged
    if damaged:
        _log.warning("%s/%s: no usable copy is left; starting empty", directory.label, name)
    return ReadResult(None, Origin.EMPTY, primary_valid=False)


class Quarantine:
    """Keeps damaged state files for diagnostics, at most three (§13.1)."""

    def __init__(
        self,
        directory: Directory,
        now: Callable[[], datetime],
        *,
        limit: int = QUARANTINE_LIMIT,
    ) -> None:
        self._directory = directory
        self._now = now
        self._limit = limit

    def take(self, name: str) -> bool:
        """Move ``name`` into ``quarantine/``, then drop the oldest entries
        beyond the limit. Best-effort; never raises."""
        stamp = self._now().astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
        target = f"{stamp}-{new_token()}-{name}"
        label = f"{self._directory.label}/{name}"
        try:
            holding = self._directory.child(QUARANTINE_DIRECTORY, create=True)
        except StateError as exc:
            _log.warning("%s could not be quarantined: %s", label, exc)
            return False
        with holding:
            try:
                self._directory.rename_into(name, holding, target)
            except OSError as exc:
                _log.warning("%s could not be quarantined (%s)", label, errno_name(exc))
                return False
            _log.warning("%s was moved to %s/%s", label, holding.label, target)
            self._trim(holding)
        return True

    def _trim(self, holding: Directory) -> None:
        try:
            names = sorted(holding.names(QUARANTINE_SCAN_LIMIT))
            for name in names[: max(0, len(names) - self._limit)]:
                holding.remove(name)
        except OSError as exc:
            _log.warning("%s: old entries were not removed (%s)", holding.label, errno_name(exc))


class DocumentFile[T]:
    """One JSON document in a directory, written with the atomic primitive."""

    def __init__(
        self,
        directory: Directory,
        name: str,
        spec: DocumentSpec[T],
        *,
        backup: bool = False,
        quarantine: Quarantine | None = None,
        mode: int = 0o600,
    ) -> None:
        self.directory = directory
        self.name = check_name(name)
        self.spec = spec
        self._backup = backup
        self._quarantine = quarantine
        self._mode = mode
        self._primary_valid = False

    def load(self) -> ReadResult[T]:
        """Read the document (primary, ``.bak``, empty). Never raises."""
        result = read_document(
            self.directory,
            self.name,
            self.spec,
            backup=self._backup,
            quarantine=self._quarantine,
        )
        self._primary_valid = result.primary_valid
        return result

    def stage(self, document: Mapping[str, object]) -> Staged:
        """Steps 2 and 3. The document must pass the reader's own checks.
        Raises :class:`StateError`."""
        data = encode_json(document, self.spec.max_bytes)
        verdict = _judge(data, self.spec)
        if verdict.kind is not _Kind.VALID:
            msg = f"{self.directory.label}/{self.name}: refusing to write an invalid document"
            raise StateError(msg)
        return self.directory.stage(self.name, data, mode=self._mode)

    def commit(self, staged: Staged) -> None:
        """Steps 4 to 6. The ``.bak`` copy is refreshed only from a primary that
        was valid. Raises :class:`CommitError`."""
        try:
            self.directory.commit(staged, refresh_backup=self._backup and self._primary_valid)
        except CommitError as exc:
            self._primary_valid = self._primary_valid or exc.replaced
            raise
        self._primary_valid = True

    def discard(self, staged: Staged) -> None:
        self.directory.discard(staged)

    def write(self, document: Mapping[str, object]) -> None:
        """Steps 2 to 6. Raises :class:`StateError`."""
        self.commit(self.stage(document))
