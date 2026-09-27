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
- each file is opened with ``O_NOFOLLOW`` (and ``O_NONBLOCK``, so a FIFO
  cannot block) and checked with ``fstat``: a regular file of at most 40 MiB.

**Identifier** (D-118): ``local:fp:<sha256(size ‖ first 64 KiB ‖ last 64 KiB)>``,
where the size is 8 bytes, big-endian.

**Preview exclusion** (acceptance item F7), three guards:

1. the preview directory is excluded by its real path during the scan;
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
import hashlib
import logging
import os
import re
import stat
from collections.abc import Collection, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from frame_gallery.budget.deadline import Deadline
from frame_gallery.budget.limits import (
    LOCAL_DIRECTORY_DEPTH,
    LOCAL_DIRECTORY_ENTRY_ALLOWANCE,
    LOCAL_INSPECTION_S,
)
from frame_gallery.config.filters import EffectiveFilters
from frame_gallery.domain import Size, SourceKey
from frame_gallery.imaging.contract import (
    INSPECT_TASK,
    MAX_SOURCE_BYTES,
    ImageFormat,
    InspectRequest,
    InspectResult,
    InspectStatus,
)
from frame_gallery.isolation.executor import Executor, WorkerError
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
FINGERPRINT_EDGE: Final = 64 * 1024
MAX_EXAMPLES: Final = 5
EXAMPLE_LENGTH: Final = 80
TITLE_LENGTH: Final = 100
COPY_CHUNK: Final = 1024 * 1024

NATIVE_ID: Final = re.compile(r"fp:[0-9a-f]{64}")
EXTENSIONS: Final = {".jpg": ImageFormat.JPEG, ".jpeg": ImageFormat.JPEG, ".png": ImageFormat.PNG}

_READ_FLAGS: Final = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
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
    PREVIEW = "preview"
    INSPECTION_FAILED = "inspection_failed"


# --- fingerprints (D-118) ------------------------------------------------------


def _digest(size: int, head: bytes, tail: bytes) -> str:
    return hashlib.sha256(size.to_bytes(8, "big") + head + tail).hexdigest()


def fingerprint_bytes(data: bytes) -> str:
    """The D-118 fingerprint of ``data`` (for example a published preview)."""
    size = len(data)
    return _digest(size, data[:FINGERPRINT_EDGE], data[max(0, size - FINGERPRINT_EDGE) :])


def fingerprint_fd(fd: int, size: int) -> str | None:
    """The D-118 fingerprint of an open regular file of ``size`` bytes, or
    ``None`` if the file is shorter than that (it changed)."""
    edge = min(FINGERPRINT_EDGE, size)
    head = os.pread(fd, edge, 0)
    tail = os.pread(fd, edge, size - edge)
    if len(head) != edge or len(tail) != edge:
        return None
    return _digest(size, head, tail)


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


@dataclass(frozen=True, slots=True)
class LocalCopy:
    """A library file copied into the run's workspace."""

    path: Path
    size_bytes: int
    declared_format: ImageFormat


type _Found = tuple[Path, str, ImageFormat]
"""A supported file: its path, its path relative to the library, and its format."""


@dataclass(slots=True)
class _Scan:
    preview_real: str
    pending: list[tuple[Path, str, int]] = field(default_factory=list)
    """Directories still to list: path, relative prefix, and depth."""

    found: list[_Found] = field(default_factory=list)


def _inspect_file(path: Path) -> tuple[int, str | None, SkipReason | None]:
    """Open a library file safely and fingerprint it: its size, its
    fingerprint, and the reason to skip it (``None`` if it is usable)."""
    try:
        fd = os.open(path, _READ_FLAGS)
    except OSError:
        return 0, None, SkipReason.UNREADABLE
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            return 0, None, SkipReason.NOT_REGULAR
        if info.st_size == 0:
            return 0, None, SkipReason.EMPTY
        if info.st_size > MAX_SOURCE_BYTES:
            return info.st_size, None, SkipReason.OVERSIZE
        fingerprint = fingerprint_fd(fd, info.st_size)
    except OSError:
        return 0, None, SkipReason.UNREADABLE
    finally:
        os.close(fd)
    return info.st_size, fingerprint, None if fingerprint is not None else SkipReason.UNREADABLE


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
            if not self._library_ready():
                return
            paths = self._scan(ctx.deadline)
            ctx.random.shuffle(paths)
            for path, relative, declared in paths:
                ctx.deadline.check()
                candidate = self._offer(path, relative, declared)
                if candidate is not None:
                    yield candidate
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

    def _library_ready(self) -> bool:
        try:
            self._root.mkdir(mode=0o755, parents=True, exist_ok=True)
            info = os.lstat(self._root)
        except OSError:
            _log.warning("the local library %s cannot be created or read", self._root)
            return False
        if not stat.S_ISDIR(info.st_mode):
            _log.warning("the local library %s is not a folder", self._root)
            return False
        return True

    def _scan(self, deadline: Deadline) -> list[_Found]:
        """Every supported file, sorted by relative path (the order is then
        shuffled with the injected random source, so tests are repeatable)."""
        scan = _Scan(preview_real=os.path.realpath(self._preview_dir))
        scan.pending.append((self._root, "", 0))
        entries = 0
        while scan.pending:
            deadline.check()
            directory, prefix, depth = scan.pending.pop()
            try:
                with os.scandir(directory) as listing:
                    for entry in listing:
                        entries += 1
                        if entries > LOCAL_DIRECTORY_ENTRY_ALLOWANCE:
                            self.report.skip(SkipReason.ENTRY_LIMIT)
                            return sorted(scan.found, key=lambda item: item[1])
                        self._classify(entry, prefix, depth, scan)
            except OSError:
                self.report.skip(SkipReason.UNREADABLE, prefix or ".")
        return sorted(scan.found, key=lambda item: item[1])

    def _classify(self, entry: os.DirEntry[str], prefix: str, depth: int, scan: _Scan) -> None:
        name = entry.name
        if name.startswith("."):
            return
        relative = f"{prefix}{name}"
        path = Path(entry.path)
        if entry.is_symlink():
            self.report.skip(SkipReason.SYMLINK, relative)
        elif entry.is_dir(follow_symlinks=False):
            if os.path.realpath(path) == scan.preview_real:
                return  # guard 1 (F7)
            if depth >= LOCAL_DIRECTORY_DEPTH:
                self.report.skip(SkipReason.TOO_DEEP, relative)
            else:
                scan.pending.append((path, f"{relative}/", depth + 1))
        elif entry.is_file(follow_symlinks=False):
            declared = EXTENSIONS.get(Path(name).suffix.lower())
            if declared is None:
                self.report.skip(SkipReason.UNSUPPORTED_EXTENSION, relative)
            else:
                scan.found.append((path, relative, declared))
        else:
            self.report.skip(SkipReason.NOT_REGULAR, relative)

    def _offer(self, path: Path, relative: str, declared: ImageFormat) -> Candidate | None:
        size, fingerprint, reason = _inspect_file(path)
        if reason is None and fingerprint in self._preview_fingerprints:
            reason = SkipReason.PREVIEW  # guard 3 (F7)
        if reason is not None or fingerprint is None:
            self.report.skip(reason or SkipReason.UNREADABLE, relative)
            return None
        native_id = f"fp:{fingerprint}"
        self._files.setdefault(
            native_id,
            LibraryFile(
                path=path,
                relative=relative,
                declared_format=declared,
                size=size,
                native_id=native_id,
            ),
        )
        return Candidate(
            provider_key=PROVIDER_KEY,
            native_id=native_id,
            rights_basis=RightsBasis.USER_SUPPLIED,
            rights_field="library",
            attribution=Attribution(title=_title(relative)),
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
        info = os.fstat(fd)
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_size != file.size
            or f"fp:{fingerprint_fd(fd, info.st_size)}" != file.native_id
        ):
            raise SourceError(SourceErrorKind.NOT_FOUND, "the file changed since the scan")


def _copy(source: int, destination: Path, size: int, deadline: Deadline) -> None:
    target = os.open(destination, _WRITE_FLAGS, 0o600)
    done = False
    try:
        copied = 0
        while copied < size:
            deadline.check()
            chunk = os.pread(source, min(COPY_CHUNK, size - copied), copied)
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
        request = InspectRequest(path=str(file.path), declared_format=file.declared_format)
        timeout = deadline.clamp(LOCAL_INSPECTION_S)
        try:
            raw = self._executor.run(INSPECT_TASK, request.to_json(), timeout=timeout)
            result = InspectResult.from_json(raw)
        except (WorkerError, ValueError) as exc:
            self._provider.report.skip(SkipReason.INSPECTION_FAILED, file.relative)
            detail = exc.kind.value if isinstance(exc, WorkerError) else "invalid result"
            raise SourceError(
                SourceErrorKind.UNEXPECTED_FORMAT, f"inspection failed ({detail})"
            ) from None
        if result.status is InspectStatus.FAILED:
            self._provider.report.skip(SkipReason.UNREADABLE, file.relative)
            return None
        return result.oriented_size
