"""The local media provider (§9.3, D-118).

**Library.** The fixed folder ``/media/frame_gallery/library``, created at
the start of discovery if it is missing. The scan is iterative and bounded:

- at most :data:`~frame_gallery.budget.limits.LOCAL_DIRECTORY_DEPTH` levels
  of subfolders, and at most
  :data:`~frame_gallery.budget.limits.LOCAL_DIRECTORY_ENTRY_ALLOWANCE`
  directory entries in total;
- hidden entries are skipped, and symbolic links are never followed;
- only ``.jpg``, ``.jpeg``, and ``.png`` files are offered, in a shuffled
  order;
- each folder is opened with ``O_NOFOLLOW`` and listed through its
  descriptor, and each folder and file is pinned by its device and inode as
  the scan saw it; a later open (to offer, inspect, or copy a file) must find
  the same file, so replacing a folder by a symbolic link during the run
  cannot lead outside the library;
- each file is opened with ``O_NOFOLLOW`` (and ``O_NONBLOCK``, so a FIFO
  cannot block) and checked with ``fstat``: a regular file of at most 40 MiB.

**Identifier** (D-118): ``local:fp:<sha256(size ‖ first 64 KiB ‖ last 64 KiB)>``,
where the size is 8 bytes, big-endian.

**Preview exclusion** (acceptance item F7), three guards:

1. the preview directory is excluded during the scan (by device and inode);
2. the library folder may not contain the preview directory (checked when
   the provider is built);
3. the fingerprints of the last previews (from ``current.json``, Phase 4)
   are skipped.

**Reporting.** Unsupported, oversized, unreadable, and uninspectable files
are summarized in one aggregated WARNING when discovery ends: counts per
reason and at most 5 sanitized example paths, relative to the library.

**Dimensions** come from the header inspection in the worker
(:class:`LocalInspectionProbe`, its own allowance of 300). **Delivery**
copies the file into the run's workspace (:meth:`LocalMediaProvider.fetch`),
and only a file this scan offered, still matching its fingerprint.
"""

from __future__ import annotations

import enum
import errno
import logging
import os
import re
import stat
from collections.abc import Collection, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from frame_gallery.budget.allowance import AllowanceExhausted
from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.budget.limits import (
    LOCAL_DIRECTORY_DEPTH,
    LOCAL_DIRECTORY_ENTRY_ALLOWANCE,
    LOCAL_INSPECTION_S,
)
from frame_gallery.config.filters import EffectiveFilters
from frame_gallery.domain import Size, SourceKey
from frame_gallery.fingerprint import fingerprint_fd
from frame_gallery.imaging.contract import (
    INSPECT_TASK,
    MAX_SOURCE_BYTES,
    ImageFormat,
    InspectRequest,
    InspectResult,
    InspectStatus,
)
from frame_gallery.isolation.executor import Executor, WorkerError, WorkerErrorKind
from frame_gallery.logs.summary import sanitize_for_log
from frame_gallery.providers.contract import (
    Attribution,
    Candidate,
    Capabilities,
    DimensionSource,
    DiscoveryContext,
    ImageRef,
    ImageRefKind,
    SourceError,
    SourceErrorKind,
)
from frame_gallery.providers.rights import RightsBasis

PROVIDER_KEY: Final = "local"
LIBRARY_ROOT: Final = Path("/media/frame_gallery/library")
PREVIEW_ROOT: Final = Path("/media/frame_gallery/preview")
MAX_EXAMPLES: Final = 5
EXAMPLE_LENGTH: Final = 80
TITLE_LENGTH: Final = 100
COPY_CHUNK: Final = 1024 * 1024

NATIVE_ID: Final = re.compile(r"fp:[0-9a-f]{64}")
EXTENSIONS: Final = {".jpg": ImageFormat.JPEG, ".jpeg": ImageFormat.JPEG, ".png": ImageFormat.PNG}

_READ_FLAGS: Final = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
_DIRECTORY_FLAGS: Final = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_WRITE_FLAGS: Final = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC

_log = logging.getLogger("frame_gallery.providers.local_media")


class SkipReason(enum.StrEnum):
    """Why a library entry was not offered (the aggregated warning, §9.3)."""

    UNSUPPORTED_EXTENSION = "unsupported_extension"
    OVERSIZE = "oversize"
    EMPTY = "empty"
    NOT_REGULAR = "not_regular"
    SYMLINK = "symlink"
    UNREADABLE = "unreadable"
    TOO_DEEP = "too_deep"
    ENTRY_LIMIT = "entry_limit"
    CHANGED = "changed"
    """A folder or file is no longer the one the scan saw (for example
    replaced by a symbolic link)."""

    PREVIEW = "preview"
    INSPECTION_FAILED = "inspection_failed"


type Identity = tuple[int, int]
"""A file's ``(st_dev, st_ino)``: what the scan saw, re-checked on every open."""


def _identity(info: os.stat_result) -> Identity:
    return (info.st_dev, info.st_ino)


def check_preview_outside_library(library: Path, preview: Path) -> None:
    """Guard 2 (F7): the library may not contain the preview directory, nor
    be it. Raises ``ValueError``."""
    library_real = Path(os.path.realpath(library))
    preview_real = Path(os.path.realpath(preview))
    if preview_real == library_real or library_real in preview_real.parents:
        msg = "the preview directory must not be inside the local library"
        raise ValueError(msg)


# --- the scan -------------------------------------------------------------------


@dataclass(slots=True)
class LibraryReport:
    """Counts per skip reason, and a few sanitized example paths."""

    counts: dict[SkipReason, int] = field(default_factory=dict)
    examples: list[str] = field(default_factory=list)

    def skip(self, reason: SkipReason, relative: str | None = None) -> None:
        self.counts[reason] = self.counts.get(reason, 0) + 1
        if relative is not None and len(self.examples) < MAX_EXAMPLES:
            self.examples.append(sanitize_for_log(relative, max_length=EXAMPLE_LENGTH))

    def warning_text(self) -> str | None:
        """The aggregated WARNING, or ``None`` if nothing was skipped."""
        if not self.counts:
            return None
        total = sum(self.counts.values())
        reasons = ", ".join(
            f"{reason.value}={self.counts[reason]}"
            for reason in SkipReason
            if reason in self.counts
        )
        text = f"local library: {total} entries skipped ({reasons})"
        if self.examples:
            text += "; examples: " + ", ".join(self.examples)
        return text


@dataclass(frozen=True, slots=True)
class LibraryFile:
    """A file this scan offered."""

    path: Path
    relative: str
    declared_format: ImageFormat
    size: int
    native_id: str
    identity: Identity


@dataclass(frozen=True, slots=True)
class LocalCopy:
    """A library file copied into the run's workspace."""

    path: Path
    size_bytes: int
    declared_format: ImageFormat


@dataclass(frozen=True, slots=True)
class _Found:
    """A supported file as the scan saw it."""

    path: Path
    relative: str
    declared_format: ImageFormat
    identity: Identity


@dataclass(slots=True)
class _Scan:
    preview: Identity | None
    pending: list[tuple[Path, str, int, Identity]] = field(default_factory=list)
    """Folders still to list: path, relative prefix, depth, and identity."""

    found: list[_Found] = field(default_factory=list)
    entries: int = 0


def _problem(info: os.stat_result, expected: Identity) -> SkipReason | None:
    """Why an opened library file cannot be offered, or ``None``."""
    if _identity(info) != expected:
        return SkipReason.CHANGED
    if not stat.S_ISREG(info.st_mode):
        return SkipReason.NOT_REGULAR
    if info.st_size == 0:
        return SkipReason.EMPTY
    if info.st_size > MAX_SOURCE_BYTES:
        return SkipReason.OVERSIZE
    return None


def _inspect_file(path: Path, expected: Identity) -> tuple[int, str | None, SkipReason | None]:
    """Open a library file safely and fingerprint it: its size, its
    fingerprint, and the reason to skip it (``None`` if it is usable)."""
    try:
        fd = os.open(path, _READ_FLAGS)
    except OSError:
        return 0, None, SkipReason.UNREADABLE
    try:
        info = os.fstat(fd)
        problem = _problem(info, expected)
        fingerprint = None if problem is not None else fingerprint_fd(fd, info.st_size)
    except OSError:
        return 0, None, SkipReason.UNREADABLE
    finally:
        os.close(fd)
    if problem is None and fingerprint is None:
        problem = SkipReason.UNREADABLE
    return info.st_size, fingerprint, problem


def _title(relative: str) -> str:
    name = relative.rsplit("/", 1)[-1]
    stem = name.rsplit(".", 1)[0] or name
    return stem[:TITLE_LENGTH]


class LocalMediaProvider:
    """The ``local_media`` source (§9.3). One instance serves one run."""

    def __init__(
        self,
        *,
        root: Path = LIBRARY_ROOT,
        preview_dir: Path = PREVIEW_ROOT,
        preview_fingerprints: Collection[str] = (),
    ) -> None:
        check_preview_outside_library(root, preview_dir)
        self._root = root
        self._preview_dir = preview_dir
        self._preview_fingerprints = frozenset(preview_fingerprints)
        self._files: dict[str, LibraryFile] = {}
        self.report = LibraryReport()

    @property
    def key(self) -> str:
        return PROVIDER_KEY

    @property
    def root(self) -> Path:
        return self._root

    def capabilities(self) -> Capabilities:
        return Capabilities(
            source=SourceKey.LOCAL_MEDIA, provider_key=PROVIDER_KEY, dims_in_metadata=False
        )

    def iter_candidates(
        self, filters: EffectiveFilters, ctx: DiscoveryContext
    ) -> Iterator[Candidate]:
        """Scan the library, then yield its usable files in a random order.

        No filter applies to local media (§9.2); the runner has already
        reported every configured filter as unsupported.
        """
        del filters
        self.report = LibraryReport()
        self._files = {}
        try:
            root = self._library_ready()
            if root is None:
                return
            found = self._scan(root, ctx.deadline)
            ctx.random.shuffle(found)
            for item in found:
                ctx.deadline.check()
                candidate = self._offer(item)
                if candidate is not None:
                    yield candidate
            if SkipReason.ENTRY_LIMIT in self.report.counts:
                # Part of the library was never listed: a search limit, not an
                # empty library (the no_match hint must say so).
                raise AllowanceExhausted("local_directory_entries")
        finally:
            text = self.report.warning_text()
            if text is not None:
                _log.warning("%s", text)

    def full_ref(self, candidate: Candidate) -> ImageRef:
        return ImageRef(ImageRefKind.LOCAL, str(self.library_file(candidate).path))

    def library_file(self, candidate: Candidate) -> LibraryFile:
        """The file behind a candidate of this scan. Raises ``ValueError``."""
        file = self._files.get(candidate.native_id)
        if candidate.provider_key != PROVIDER_KEY or file is None:
            msg = "the candidate was not offered by this scan"
            raise ValueError(msg)
        return file

    # --------------------------------------------------------------- the scan

    def _library_ready(self) -> Identity | None:
        """The library's identity, once it exists as a real folder."""
        try:
            self._root.mkdir(mode=0o755, parents=True, exist_ok=True)
            info = os.lstat(self._root)
        except OSError:
            _log.warning("the local library %s cannot be created or read", self._root)
            return None
        if not stat.S_ISDIR(info.st_mode):
            _log.warning("the local library %s is not a folder", self._root)
            return None
        return _identity(info)

    def _preview_identity(self) -> Identity | None:
        try:
            return _identity(self._preview_dir.stat())
        except OSError:
            return None

    def _scan(self, root: Identity, deadline: Deadline) -> list[_Found]:
        """Every supported file, sorted by relative path (the order is then
        shuffled with the injected random source, so tests are repeatable)."""
        scan = _Scan(preview=self._preview_identity())
        scan.pending.append((self._root, "", 0, root))
        while scan.pending:
            deadline.check()
            directory, prefix, depth, expected = scan.pending.pop()
            if not self._list(directory, prefix, depth, expected, scan):
                break
        return sorted(scan.found, key=lambda item: item.relative)

    def _list(
        self, directory: Path, prefix: str, depth: int, expected: Identity, scan: _Scan
    ) -> bool:
        """List one folder through its own descriptor; ``False`` once the entry
        limit is reached."""
        try:
            fd = os.open(directory, _DIRECTORY_FLAGS)
        except OSError as exc:
            # ELOOP: now a symbolic link; ENOTDIR: no longer a folder.
            replaced = exc.errno in (errno.ELOOP, errno.ENOTDIR)
            self.report.skip(
                SkipReason.CHANGED if replaced else SkipReason.UNREADABLE, prefix or "."
            )
            return True
        try:
            if _identity(os.fstat(fd)) != expected:
                self.report.skip(SkipReason.CHANGED, prefix or ".")
                return True
            with os.scandir(fd) as listing:
                for entry in listing:
                    scan.entries += 1
                    if scan.entries > LOCAL_DIRECTORY_ENTRY_ALLOWANCE:
                        self.report.skip(SkipReason.ENTRY_LIMIT)
                        return False
                    self._classify(entry, directory, prefix, depth, scan)
        except OSError:
            self.report.skip(SkipReason.UNREADABLE, prefix or ".")
        finally:
            os.close(fd)
        return True

    def _classify(
        self, entry: os.DirEntry[str], directory: Path, prefix: str, depth: int, scan: _Scan
    ) -> None:
        name = entry.name
        if name.startswith("."):
            return
        relative = f"{prefix}{name}"
        if entry.is_symlink():
            self.report.skip(SkipReason.SYMLINK, relative)
            return
        path = directory / name
        if entry.is_file(follow_symlinks=False):
            declared = EXTENSIONS.get(Path(name).suffix.lower())
            if declared is None:
                self.report.skip(SkipReason.UNSUPPORTED_EXTENSION, relative)
            else:
                identity = _identity(entry.stat(follow_symlinks=False))
                scan.found.append(_Found(path, relative, declared, identity))
        elif not entry.is_dir(follow_symlinks=False):
            self.report.skip(SkipReason.NOT_REGULAR, relative)
        elif depth >= LOCAL_DIRECTORY_DEPTH:
            self.report.skip(SkipReason.TOO_DEEP, relative)
        else:
            identity = _identity(entry.stat(follow_symlinks=False))
            if identity != scan.preview:  # guard 1 (F7)
                scan.pending.append((path, f"{relative}/", depth + 1, identity))

    def _offer(self, item: _Found) -> Candidate | None:
        size, fingerprint, reason = _inspect_file(item.path, item.identity)
        if reason is None and fingerprint in self._preview_fingerprints:
            reason = SkipReason.PREVIEW  # guard 3 (F7)
        if reason is not None or fingerprint is None:
            self.report.skip(reason or SkipReason.UNREADABLE, item.relative)
            return None
        native_id = f"fp:{fingerprint}"
        self._files.setdefault(
            native_id,
            LibraryFile(
                path=item.path,
                relative=item.relative,
                declared_format=item.declared_format,
                size=size,
                native_id=native_id,
                identity=item.identity,
            ),
        )
        return Candidate(
            provider_key=PROVIDER_KEY,
            native_id=native_id,
            rights_basis=RightsBasis.USER_SUPPLIED,
            rights_field="library",
            attribution=Attribution(title=_title(item.relative)),
            dims=None,
        )

    # --------------------------------------------------------------- delivery

    def fetch(self, ref: ImageRef, destination: Path, deadline: Deadline) -> LocalCopy:
        """Copy an offered library file to ``destination`` (a new file).

        The file must still be a regular file of the scanned size with the
        scanned fingerprint; otherwise ``SourceError(NOT_FOUND)``, and the
        next candidate is tried. Raises ``DeadlineExceeded`` when time runs out.
        """
        file = next((item for item in self._files.values() if str(item.path) == ref.location), None)
        if ref.kind is not ImageRefKind.LOCAL or file is None:
            raise SourceError(SourceErrorKind.NOT_FOUND, "not a file offered by this scan")
        try:
            source = os.open(file.path, _READ_FLAGS)
        except OSError:
            raise SourceError(SourceErrorKind.NOT_FOUND, "the file is gone") from None
        try:
            self._check_unchanged(source, file)
            _copy(source, destination, file.size, deadline)
        finally:
            os.close(source)
        return LocalCopy(destination, file.size, file.declared_format)

    @staticmethod
    def _check_unchanged(fd: int, file: LibraryFile) -> None:
        try:
            info = os.fstat(fd)
            unchanged = (
                _identity(info) == file.identity
                and stat.S_ISREG(info.st_mode)
                and info.st_size == file.size
                and f"fp:{fingerprint_fd(fd, info.st_size)}" == file.native_id
            )
        except OSError:
            raise SourceError(SourceErrorKind.NOT_FOUND, "the file cannot be read") from None
        if not unchanged:
            raise SourceError(SourceErrorKind.NOT_FOUND, "the file changed since the scan")


def _copy(source: int, destination: Path, size: int, deadline: Deadline) -> None:
    target = os.open(destination, _WRITE_FLAGS, 0o600)
    done = False
    try:
        copied = 0
        while copied < size:
            deadline.check()
            try:
                chunk = os.pread(source, min(COPY_CHUNK, size - copied), copied)
            except OSError:
                raise SourceError(SourceErrorKind.NOT_FOUND, "the file cannot be read") from None
            if not chunk:
                raise SourceError(SourceErrorKind.NOT_FOUND, "the file changed during the copy")
            view = memoryview(chunk)
            while view:
                view = view[os.write(target, view) :]
            copied += len(chunk)
        done = True
    finally:
        os.close(target)
        if not done:
            destination.unlink(missing_ok=True)


class LocalInspectionProbe:
    """Header inspection in the worker (§8.3): ``source`` is local, so the
    selection charges its own allowance of 300 and counts a failure as an
    inspection failure, never as a transport failure."""

    def __init__(self, provider: LocalMediaProvider, executor: Executor) -> None:
        self._provider = provider
        self._executor = executor

    @property
    def source(self) -> DimensionSource:
        return DimensionSource.LOCAL_INSPECTION

    def measure(self, candidate: Candidate, deadline: Deadline) -> Size | None:
        """The dimensions after EXIF orientation; ``None`` for a file that
        cannot be read as its format (counted in the aggregated warning).
        A worker failure raises ``SourceError`` (an inspection failure)."""
        file = self._provider.library_file(candidate)
        device, inode = file.identity
        request = InspectRequest(
            path=str(file.path),
            declared_format=file.declared_format,
            device=device,
            inode=inode,
        )
        timeout = deadline.clamp(LOCAL_INSPECTION_S)
        try:
            raw = self._executor.run(INSPECT_TASK, request.to_json(), timeout=timeout)
            result = InspectResult.from_json(raw)
        except (WorkerError, ValueError) as exc:
            if (
                isinstance(exc, WorkerError)
                and exc.kind is WorkerErrorKind.TIMEOUT
                and deadline.expired()
            ):
                # Cut off by discovery's own deadline: not the file's fault.
                raise DeadlineExceeded(deadline.name) from None
            self._provider.report.skip(SkipReason.INSPECTION_FAILED, file.relative)
            detail = exc.kind.value if isinstance(exc, WorkerError) else "invalid result"
            raise SourceError(
                SourceErrorKind.UNEXPECTED_FORMAT, f"inspection failed ({detail})"
            ) from None
        if result.status is InspectStatus.FAILED:
            self._provider.report.skip(SkipReason.UNREADABLE, file.relative)
            return None
        return result.oriented_size
