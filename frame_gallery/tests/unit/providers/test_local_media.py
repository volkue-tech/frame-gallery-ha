"""The local media provider (§9.3, D-118; F7), with a real temporary library
of synthesized images."""

from __future__ import annotations

import errno
import hashlib
import logging
import os
import stat
from collections.abc import Iterator, MutableSequence
from pathlib import Path
from typing import Any

import pytest

from frame_gallery.budget.allowance import Allowance, AllowanceExhausted
from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.budget.limits import LOCAL_INSPECTION_S
from frame_gallery.config.filters import EffectiveFilters, FilterSet
from frame_gallery.domain import FitMode, Size, SourceKey
from frame_gallery.errors import Cancelled
from frame_gallery.fingerprint import FINGERPRINT_EDGE, fingerprint_bytes, fingerprint_fd
from frame_gallery.imaging.contract import (
    MAX_INSPECT_BATCH,
    MAX_SOURCE_BYTES,
    ImageFormat,
    InspectBatch,
    InspectResult,
    InspectStatus,
    PrepareFailure,
    inspected_event,
)
from frame_gallery.isolation.executor import (
    EventSink,
    IsolationFailure,
    JsonObject,
    WorkerError,
    WorkerErrorKind,
)
from frame_gallery.isolation.in_process import InProcessExecutor, default_executor
from frame_gallery.providers import local_media
from frame_gallery.providers.contract import (
    Attribution,
    Candidate,
    DimensionSource,
    DiscoveryContext,
    ImageRef,
    ImageRefKind,
    SourceError,
    SourceErrorKind,
)
from frame_gallery.providers.local_media import (
    LIBRARY_ROOT,
    PREVIEW_ROOT,
    LibraryReport,
    LocalInspectionProbe,
    LocalMediaProvider,
    SkipReason,
    check_preview_outside_library,
)
from frame_gallery.providers.rights import RightsBasis
from frame_gallery.randomness import SeededRandomSource
from frame_gallery.selection.exclusion import ExclusionSet
from frame_gallery.selection.shortlist import DiscoveryEnd, SelectionPolicy, build_shortlist
from tests.support.clock import FakeClock
from tests.support.images import marked, oriented_jpeg, save_jpeg, save_png

FILTERS = EffectiveFilters(
    source=SourceKey.LOCAL_MEDIA,
    department=None,
    style=None,
    period=None,
    color=None,
    ignored=(),
    requested=FilterSet(source=SourceKey.LOCAL_MEDIA),
)


class Library:
    def __init__(self, tmp_path: Path) -> None:
        self.root = tmp_path / "media" / "frame_gallery" / "library"
        self.preview = tmp_path / "media" / "frame_gallery" / "preview"
        self.root.mkdir(parents=True)
        self.clock = FakeClock()

    def jpeg(self, relative: str, size: tuple[int, int] = (64, 36)) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        return save_jpeg(marked(size), path)

    def png(self, relative: str, size: tuple[int, int] = (64, 36)) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        return save_png(marked(size), path)

    def file(self, relative: str, data: bytes = b"x") -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def provider(self, fingerprints: frozenset[str] = frozenset()) -> LocalMediaProvider:
        return LocalMediaProvider(
            root=self.root, preview_dir=self.preview, preview_fingerprints=fingerprints
        )

    def context(self, seconds: float = 30.0, seed: int = 3) -> DiscoveryContext:
        return DiscoveryContext(
            deadline=Deadline.after(self.clock, seconds, "discovery"),
            random=SeededRandomSource(seed),
        )

    def candidates(self, provider: LocalMediaProvider | None = None) -> list[Candidate]:
        """Every candidate, then the aggregated warning, as the runner asks
        for it once selection is done."""
        provider = provider or self.provider()
        found = list(provider.iter_candidates(FILTERS, self.context()))
        provider.report_discovery()
        return found


@pytest.fixture
def library(tmp_path: Path) -> Library:
    return Library(tmp_path)


def _titles(candidates: list[Candidate]) -> list[str]:
    return sorted(candidate.attribution.title or "" for candidate in candidates)


class TestScan:
    def test_offers_supported_files_at_every_allowed_depth(self, library: Library) -> None:
        library.jpeg("top.jpg")
        library.jpeg("a/one.JPG")
        library.png("a/b/two.png")
        library.jpeg("a/b/c/three.jpeg")
        library.jpeg("a/b/c/d/four.jpg")
        found = library.candidates()
        assert _titles(found) == ["four", "one", "three", "top", "two"]
        assert all(candidate.provider_key == "local" for candidate in found)
        assert all(candidate.rights_basis is RightsBasis.USER_SUPPLIED for candidate in found)
        assert all(candidate.rights_field == "library" for candidate in found)
        assert all(candidate.dims is None for candidate in found)

    def test_folders_below_four_levels_are_not_entered(
        self, library: Library, caplog: pytest.LogCaptureFixture
    ) -> None:
        library.jpeg("a/b/c/d/e/deep.jpg")
        provider = library.provider()
        assert library.candidates(provider) == []
        assert provider.report.counts == {SkipReason.TOO_DEEP: 1}
        assert "too_deep=1" in caplog.text
        assert "a/b/c/d/e" in caplog.text

    def test_hidden_entries_are_skipped_silently(self, library: Library) -> None:
        library.jpeg(".hidden.jpg")
        library.jpeg(".cache/inside.jpg")
        provider = library.provider()
        assert library.candidates(provider) == []
        assert provider.report.counts == {}

    def test_symbolic_links_are_never_followed(self, library: Library, tmp_path: Path) -> None:
        outside = tmp_path / "outside"
        outside.mkdir()
        save_jpeg(marked((8, 8)), outside / "secret.jpg")
        (library.root / "linked_dir").symlink_to(outside, target_is_directory=True)
        (library.root / "linked.jpg").symlink_to(outside / "secret.jpg")
        provider = library.provider()
        assert library.candidates(provider) == []
        assert provider.report.counts == {SkipReason.SYMLINK: 2}

    def test_unsupported_empty_special_and_oversized_files(self, library: Library) -> None:
        library.file("notes.txt")
        library.file("art.gif")
        library.file("empty.jpg", b"")
        os.mkfifo(library.root / "pipe.jpg")
        big = library.file("big.jpg", b"\xff\xd8")
        with big.open("r+b") as handle:
            handle.truncate(MAX_SOURCE_BYTES + 1)  # sparse
        library.jpeg("ok.jpg")
        provider = library.provider()
        assert _titles(library.candidates(provider)) == ["ok"]
        assert provider.report.counts == {
            SkipReason.UNSUPPORTED_EXTENSION: 2,
            SkipReason.EMPTY: 1,
            SkipReason.NOT_REGULAR: 1,
            SkipReason.OVERSIZE: 1,
        }

    def test_a_file_of_exactly_the_limit_is_offered(self, library: Library) -> None:
        exact = library.file("exact.jpg", b"\xff\xd8")
        with exact.open("r+b") as handle:
            handle.truncate(MAX_SOURCE_BYTES)
        assert _titles(library.candidates()) == ["exact"]

    @pytest.mark.skipif(os.geteuid() == 0, reason="root ignores file permissions")
    def test_unreadable_files_and_folders(self, library: Library) -> None:
        locked_file = library.jpeg("locked.jpg")
        locked_dir = library.root / "private"
        library.jpeg("private/inside.jpg")
        locked_file.chmod(0)
        locked_dir.chmod(0)
        try:
            provider = library.provider()
            assert library.candidates(provider) == []
            assert provider.report.counts == {SkipReason.UNREADABLE: 2}
        finally:
            locked_dir.chmod(0o755)
            locked_file.chmod(0o644)

    def test_files_that_change_between_scan_and_open(
        self, library: Library, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A file replaced by a FIFO after the scan listed it, and a read error
        # while fingerprinting: both are skipped, neither blocks or raises.
        fifo = library.root / "was_a_file.jpg"
        os.mkfifo(fifo)
        fifo_identity = (fifo.lstat().st_dev, fifo.lstat().st_ino)
        assert local_media._inspect_file(fifo, fifo_identity) == (0, None, SkipReason.NOT_REGULAR)
        path = library.jpeg("a.jpg")
        identity = (path.stat().st_dev, path.stat().st_ino)
        assert local_media._inspect_file(path, (identity[0], identity[1] + 1))[2] is (
            SkipReason.CHANGED
        )

        def failing_pread(fd: int, length: int, offset: int) -> bytes:
            raise OSError("I/O error")

        monkeypatch.setattr(os, "pread", failing_pread)
        assert local_media._inspect_file(path, identity) == (0, None, SkipReason.UNREADABLE)

    def test_a_folder_swapped_for_a_symlink_after_the_scan(
        self, library: Library, tmp_path: Path
    ) -> None:
        # The review's race: "sub" is listed, then replaced by a link to a
        # folder outside the library that holds a file of the same name.
        library.jpeg("a.jpg")
        library.jpeg("sub/x.jpg", (80, 45))
        outside = tmp_path / "outside"
        outside.mkdir()
        save_jpeg(marked((80, 45)), outside / "x.jpg")
        provider = library.provider()

        class InOrder(SeededRandomSource):
            def shuffle(self, items: MutableSequence[Any]) -> None:
                pass  # keep the sorted order: a.jpg first, then sub/x.jpg

        context = DiscoveryContext(Deadline.after(library.clock, 30, "d"), InOrder(0))
        iterator = provider.iter_candidates(FILTERS, context)
        first = next(iterator)  # the scan has run; offers are made lazily
        assert first.attribution.title == "a"
        (library.root / "sub").rename(tmp_path / "moved")
        (library.root / "sub").symlink_to(outside, target_is_directory=True)
        assert list(iterator) == []
        assert provider.report.counts == {SkipReason.CHANGED: 1}

    def test_an_offered_file_swapped_before_the_copy(
        self, library: Library, tmp_path: Path
    ) -> None:
        library.jpeg("sub/x.jpg", (80, 45))
        outside = tmp_path / "outside"
        outside.mkdir()
        save_jpeg(marked((80, 45)), outside / "x.jpg")
        provider = library.provider()
        (candidate,) = library.candidates(provider)
        (library.root / "sub").rename(tmp_path / "moved")
        (library.root / "sub").symlink_to(outside, target_is_directory=True)
        with pytest.raises(SourceError, match="changed") as excinfo:
            provider.fetch(
                provider.full_ref(candidate), tmp_path / "copy", library.context().deadline
            )
        assert excinfo.value.kind is SourceErrorKind.NOT_FOUND
        assert not (tmp_path / "copy").exists()

    def test_a_folder_that_is_not_the_one_listed_is_not_entered(
        self, library: Library, tmp_path: Path
    ) -> None:
        library.jpeg("sub/x.jpg")
        provider = library.provider()
        scan = local_media._Scan(preview=None)
        sub = library.root / "sub"
        wrong = (sub.stat().st_dev, sub.stat().st_ino + 1)
        assert provider._list(sub, "sub/", 1, wrong, scan)
        assert scan.found == []
        assert provider.report.counts == {SkipReason.CHANGED: 1}
        # A folder that became a symbolic link is refused as changed as well.
        sub.rename(tmp_path / "gone")
        sub.symlink_to(tmp_path / "gone", target_is_directory=True)
        right = ((tmp_path / "gone").stat().st_dev, (tmp_path / "gone").stat().st_ino)
        assert provider._list(sub, "sub/", 1, right, scan)
        assert scan.found == []
        assert provider.report.counts == {SkipReason.CHANGED: 2}

    def test_a_file_that_shrinks_before_it_is_fingerprinted(
        self, library: Library, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = library.jpeg("a.jpg")
        identity = (path.stat().st_dev, path.stat().st_ino)
        monkeypatch.setattr(local_media, "fingerprint_fd", lambda fd, size: None)
        size, fingerprint, reason = local_media._inspect_file(path, identity)
        assert (fingerprint, reason) == (None, SkipReason.UNREADABLE)
        assert size == path.stat().st_size

    def test_a_listing_error_skips_the_folder(
        self, library: Library, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        library.jpeg("a.jpg")

        def failing_scandir(fd: int) -> Iterator[os.DirEntry[str]]:
            raise OSError(5, "Input/output error")

        monkeypatch.setattr(os, "scandir", failing_scandir)
        provider = library.provider()
        assert library.candidates(provider) == []
        assert provider.report.counts == {SkipReason.UNREADABLE: 1}

    def test_the_entry_limit_ends_the_scan(
        self, library: Library, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        monkeypatch.setattr(local_media, "LOCAL_DIRECTORY_ENTRY_ALLOWANCE", 3)
        for index in range(5):
            library.jpeg(f"img{index}.jpg")
        provider = library.provider()
        found: list[Candidate] = []
        with pytest.raises(AllowanceExhausted, match="local_directory_entries"):
            found.extend(provider.iter_candidates(FILTERS, library.context()))
        # A library cut short is a search limit, never an empty library.
        assert len(found) == 3
        assert provider.report.counts == {SkipReason.ENTRY_LIMIT: 1}
        with caplog.at_level(logging.WARNING):
            provider.report_discovery()
        assert caplog.messages == ["local library: 1 entries skipped (entry_limit=1)"]

    def test_the_order_is_shuffled_by_the_injected_source(self, library: Library) -> None:
        for index in range(12):
            library.jpeg(f"img{index:02}.jpg")
        provider = library.provider()

        def order(seed: int) -> list[str]:
            context = library.context(seed=seed)
            return [c.attribution.title or "" for c in provider.iter_candidates(FILTERS, context)]

        assert order(1) == order(1)
        assert order(1) != order(2)
        assert sorted(order(1)) == sorted(order(2))

    def test_the_deadline_bounds_discovery(self, library: Library) -> None:
        library.jpeg("a.jpg")
        context = library.context(seconds=1.0)
        library.clock.advance(1.0)
        with pytest.raises(DeadlineExceeded):
            next(iter(library.provider().iter_candidates(FILTERS, context)))

    def test_the_library_is_created_when_missing(self, tmp_path: Path) -> None:
        root = tmp_path / "fresh" / "library"
        provider = LocalMediaProvider(root=root, preview_dir=tmp_path / "fresh" / "preview")
        clock = FakeClock()
        context = DiscoveryContext(Deadline.after(clock, 5, "d"), SeededRandomSource(1))
        assert list(provider.iter_candidates(FILTERS, context)) == []
        assert root.is_dir()
        assert provider.root == root

    @pytest.mark.parametrize("kind", ["file", "blocked"])
    def test_an_unusable_library(
        self, tmp_path: Path, kind: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        if kind == "file":
            root = tmp_path / "library"
            root.write_bytes(b"not a folder")
            expected = "cannot be created or read"
        else:
            (tmp_path / "blocked").write_bytes(b"")
            root = tmp_path / "blocked" / "library"
            expected = "cannot be created or read"
        provider = LocalMediaProvider(root=root, preview_dir=tmp_path / "preview")
        clock = FakeClock()
        context = DiscoveryContext(Deadline.after(clock, 5, "d"), SeededRandomSource(1))
        assert list(provider.iter_candidates(FILTERS, context)) == []
        assert expected in caplog.text

    def test_a_symlinked_library_is_refused(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        real = tmp_path / "real"
        real.mkdir()
        save_jpeg(marked((8, 8)), real / "a.jpg")
        root = tmp_path / "library"
        root.symlink_to(real, target_is_directory=True)
        provider = LocalMediaProvider(root=root, preview_dir=tmp_path / "preview")
        clock = FakeClock()
        context = DiscoveryContext(Deadline.after(clock, 5, "d"), SeededRandomSource(1))
        assert list(provider.iter_candidates(FILTERS, context)) == []
        assert "is not a folder" in caplog.text


class TestIdentifiers:
    def test_the_fingerprint_follows_d118(self, library: Library) -> None:
        path = library.jpeg("a.jpg", (400, 300))
        data = path.read_bytes()
        size = len(data)
        head, tail = data[:FINGERPRINT_EDGE], data[max(0, size - FINGERPRINT_EDGE) :]
        expected = hashlib.sha256(size.to_bytes(8, "big") + head + tail).hexdigest()
        (candidate,) = library.candidates()
        assert candidate.native_id == f"fp:{expected}"
        assert candidate.qualified_id == f"local:fp:{expected}"
        assert fingerprint_bytes(data) == expected

    def test_large_files_use_only_the_edges(self) -> None:
        middle_a = b"a" * FINGERPRINT_EDGE * 3
        middle_b = b"b" * FINGERPRINT_EDGE * 3
        edge = b"e" * FINGERPRINT_EDGE
        assert fingerprint_bytes(edge + middle_a + edge) == fingerprint_bytes(
            edge + middle_b + edge
        )
        assert fingerprint_bytes(edge + middle_a + edge) != fingerprint_bytes(edge + middle_a)

    def test_file_and_bytes_fingerprints_agree(self, tmp_path: Path) -> None:
        for size in (1, 100, FINGERPRINT_EDGE, FINGERPRINT_EDGE + 1, 3 * FINGERPRINT_EDGE + 7):
            data = os.urandom(size)
            path = tmp_path / f"f{size}"
            path.write_bytes(data)
            fd = os.open(path, os.O_RDONLY)
            try:
                assert fingerprint_fd(fd, size) == fingerprint_bytes(data)
                assert fingerprint_fd(fd, size + 1) is None  # the file is shorter
            finally:
                os.close(fd)

    def test_identical_files_share_an_identifier(self, library: Library) -> None:
        first = library.jpeg("a.jpg")
        library.file("copy/a.jpg", first.read_bytes())
        found = library.candidates()
        assert len(found) == 2
        assert found[0].qualified_id == found[1].qualified_id

    def test_titles_come_from_the_file_name(self, library: Library) -> None:
        library.jpeg("Sunset over the bay.jpg")
        library.jpeg(".jpg/x.jpg")  # a hidden folder: skipped
        library.file("weird..png", library.jpeg("tmp.jpg").read_bytes())
        titles = _titles(library.candidates())
        assert titles == ["Sunset over the bay", "tmp", "weird."]


class TestPreviewGuards:
    def test_guard_2_the_library_may_not_contain_the_preview(self, tmp_path: Path) -> None:
        library = tmp_path / "library"
        with pytest.raises(ValueError, match="preview directory"):
            LocalMediaProvider(root=library, preview_dir=library / "preview")
        with pytest.raises(ValueError, match="preview directory"):
            check_preview_outside_library(library, library)
        check_preview_outside_library(library, tmp_path / "preview")

    def test_guard_2_holds_for_the_production_paths(self) -> None:
        check_preview_outside_library(LIBRARY_ROOT, PREVIEW_ROOT)
        assert Path("/media/frame_gallery/library") == LIBRARY_ROOT

    def test_guard_1_skips_the_preview_folder_by_real_path(self, library: Library) -> None:
        library.jpeg("preview/latest.jpg")
        library.jpeg("art.jpg")
        provider = library.provider()
        # Even if guard 2 were bypassed, the scan never enters the preview folder.
        provider._preview_dir = library.root / "preview"
        assert _titles(library.candidates(provider)) == ["art"]
        assert provider.report.counts == {}

    def test_guard_3_skips_recent_preview_fingerprints(self, library: Library) -> None:
        preview_copy = library.jpeg("copied_preview.jpg")
        library.jpeg("art.jpg", (80, 45))
        fingerprints = frozenset({fingerprint_bytes(preview_copy.read_bytes())})
        provider = library.provider(fingerprints)
        assert _titles(library.candidates(provider)) == ["art"]
        assert provider.report.counts == {SkipReason.PREVIEW: 1}


class TestReport:
    def test_one_aggregated_warning_with_five_examples(
        self, library: Library, caplog: pytest.LogCaptureFixture
    ) -> None:
        for index in range(8):
            library.file(f"doc{index}.txt")
        library.jpeg("ok.jpg")
        provider = library.provider()
        with caplog.at_level(logging.WARNING):
            library.candidates(provider)
        (record,) = [r for r in caplog.records if r.levelno == logging.WARNING]
        message = record.getMessage()
        assert message.startswith("local library: 8 entries skipped (unsupported_extension=8)")
        assert len(provider.report.examples) == 5
        assert message.endswith("; examples: " + ", ".join(provider.report.examples))

    def test_example_paths_are_sanitized(
        self, library: Library, caplog: pytest.LogCaptureFixture
    ) -> None:
        library.file("bad\nname\u202e\u0007.gif")
        with caplog.at_level(logging.WARNING):
            library.candidates()
        (record,) = [r for r in caplog.records if r.levelno == logging.WARNING]
        message = record.getMessage()
        assert "examples: bad name" in message
        assert "\n" not in message
        assert "\u202e" not in message
        assert "\u0007" not in message

    def test_no_warning_when_nothing_is_skipped(
        self, library: Library, caplog: pytest.LogCaptureFixture
    ) -> None:
        library.jpeg("ok.jpg")
        library.candidates()
        assert caplog.records == []

    def test_the_warning_waits_for_the_end_of_discovery(
        self, library: Library, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Selection measures its last batch after the scan has ended, so
        the warning comes only when the runner asks for it, and only once."""
        library.file("a.txt")
        library.jpeg("b.jpg")
        library.jpeg("c.jpg")
        provider = library.provider()
        iterator: Iterator[Candidate] = provider.iter_candidates(FILTERS, library.context())
        next(iterator)
        iterator.close()  # type: ignore[attr-defined]
        assert "local library" not in caplog.text
        with caplog.at_level(logging.WARNING):
            provider.report_discovery()
            provider.report_discovery()
        (record,) = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert "unsupported_extension=1" in record.getMessage()

    def test_report_text(self) -> None:
        report = LibraryReport()
        assert report.warning_text() is None
        report.skip(SkipReason.ENTRY_LIMIT)
        report.skip(SkipReason.OVERSIZE, "x" * 200)
        text = report.warning_text()
        assert text is not None
        assert text.startswith("local library: 2 entries skipped (oversize=1, entry_limit=1)")
        assert text.endswith("…")


class TestRefsAndCapabilities:
    def test_capabilities(self, library: Library) -> None:
        provider = library.provider()
        capabilities = provider.capabilities()
        assert (capabilities.source, capabilities.provider_key) == (SourceKey.LOCAL_MEDIA, "local")
        assert not capabilities.dims_in_metadata
        assert provider.key == "local"

    def test_full_ref_points_at_the_library_file(self, library: Library) -> None:
        path = library.jpeg("a.jpg")
        provider = library.provider()
        (candidate,) = library.candidates(provider)
        assert provider.full_ref(candidate) == ImageRef(ImageRefKind.LOCAL, str(path))

    def test_foreign_candidates_are_refused(self, library: Library) -> None:
        provider = library.provider()
        stranger = Candidate(
            provider_key="aic",
            native_id="fp:" + "0" * 64,
            rights_basis=RightsBasis.CC0,
            rights_field="x",
            attribution=Attribution(),
            dims=None,
        )
        with pytest.raises(ValueError, match="not offered"):
            provider.full_ref(stranger)


class TestFetch:
    def _offered(self, library: Library) -> tuple[LocalMediaProvider, Candidate, Path]:
        path = library.jpeg("a.jpg", (200, 100))
        provider = library.provider()
        (candidate,) = library.candidates(provider)
        return provider, candidate, path

    def test_copies_the_file(self, library: Library, tmp_path: Path) -> None:
        provider, candidate, path = self._offered(library)
        target = tmp_path / "in" / "source-0.bin"
        target.parent.mkdir()
        copy = provider.fetch(provider.full_ref(candidate), target, library.context().deadline)
        assert copy.path == target
        assert copy.size_bytes == path.stat().st_size
        assert copy.declared_format is ImageFormat.JPEG
        assert target.read_bytes() == path.read_bytes()
        assert stat.S_IMODE(target.stat().st_mode) == 0o640  # readable by the worker (D-164)

    def test_the_copy_is_0640_whatever_the_umask(self, library: Library, tmp_path: Path) -> None:
        provider, candidate, _path = self._offered(library)
        target = tmp_path / "source-0.bin"
        previous = os.umask(0o077)
        try:
            provider.fetch(provider.full_ref(candidate), target, library.context().deadline)
        finally:
            os.umask(previous)
        assert stat.S_IMODE(target.stat().st_mode) == 0o640  # D-164

    def test_a_copy_whose_mode_cannot_be_set_is_removed(
        self, library: Library, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        provider, candidate, _path = self._offered(library)

        def refuse(_fd: int, _mode: int) -> None:
            raise PermissionError(errno.EPERM, "not permitted")

        monkeypatch.setattr(os, "fchmod", refuse)
        target = tmp_path / "source-0.bin"
        with pytest.raises(PermissionError):
            provider.fetch(provider.full_ref(candidate), target, library.context().deadline)
        assert not target.exists()

    def test_large_files_are_copied_in_chunks(self, library: Library, tmp_path: Path) -> None:
        data = b"\x89PNG" + os.urandom(3 * 1024 * 1024)
        library.file("big.png", data)
        provider = library.provider()
        (candidate,) = library.candidates(provider)
        target = tmp_path / "copy"
        copy = provider.fetch(provider.full_ref(candidate), target, library.context().deadline)
        assert copy.declared_format is ImageFormat.PNG
        assert target.read_bytes() == data

    @pytest.mark.parametrize(
        "ref",
        [
            ImageRef(ImageRefKind.LOCAL, "/etc/passwd"),
            ImageRef(ImageRefKind.REMOTE, "https://example.org/a.jpg"),
        ],
    )
    def test_only_offered_files(self, library: Library, tmp_path: Path, ref: ImageRef) -> None:
        provider, _candidate, _path = self._offered(library)
        with pytest.raises(SourceError) as excinfo:
            provider.fetch(ref, tmp_path / "x", library.context().deadline)
        assert excinfo.value.kind is SourceErrorKind.NOT_FOUND
        assert not (tmp_path / "x").exists()

    @pytest.mark.parametrize("change", ["removed", "rewritten", "truncated", "replaced_by_dir"])
    def test_changed_files_are_not_found(
        self, library: Library, tmp_path: Path, change: str
    ) -> None:
        provider, candidate, path = self._offered(library)
        data = path.read_bytes()
        if change == "removed":
            path.unlink()
        elif change == "rewritten":
            path.write_bytes(bytes(reversed(data)))
        elif change == "truncated":
            path.write_bytes(data[:-10])
        else:
            path.unlink()
            path.mkdir()
        with pytest.raises(SourceError) as excinfo:
            provider.fetch(provider.full_ref(candidate), tmp_path / "x", library.context().deadline)
        assert excinfo.value.kind is SourceErrorKind.NOT_FOUND
        assert not (tmp_path / "x").exists()

    def test_a_file_shrinking_during_the_copy(
        self, library: Library, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        provider, candidate, _path = self._offered(library)
        real_pread = os.pread
        calls = {"n": 0}

        def pread(fd: int, length: int, offset: int) -> bytes:
            calls["n"] += 1
            return real_pread(fd, length, offset) if calls["n"] <= 2 else b""

        monkeypatch.setattr(os, "pread", pread)
        with pytest.raises(SourceError, match="during the copy"):
            provider.fetch(provider.full_ref(candidate), tmp_path / "x", library.context().deadline)
        assert not (tmp_path / "x").exists()

    def test_the_deadline_bounds_the_copy(self, library: Library, tmp_path: Path) -> None:
        provider, candidate, _path = self._offered(library)
        deadline = Deadline.after(library.clock, 1.0, "download")
        library.clock.advance(1.0)
        with pytest.raises(DeadlineExceeded):
            provider.fetch(provider.full_ref(candidate), tmp_path / "x", deadline)
        assert not (tmp_path / "x").exists()

    @pytest.mark.parametrize("failing", ["fstat", "pread"])
    def test_read_errors_are_not_found(
        self,
        library: Library,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        failing: str,
    ) -> None:
        # An I/O error on the library file tries the next candidate; it never
        # ends the run as an internal error (review finding).
        provider, candidate, _path = self._offered(library)
        real_pread = os.pread
        calls = {"n": 0}

        def pread(fd: int, length: int, offset: int) -> bytes:
            calls["n"] += 1
            if calls["n"] <= 2:
                return real_pread(fd, length, offset)
            raise OSError(5, "Input/output error")

        def fstat(fd: int) -> os.stat_result:
            raise OSError(5, "Input/output error")

        if failing == "pread":
            monkeypatch.setattr(os, "pread", pread)
        else:
            monkeypatch.setattr(os, "fstat", fstat)
        with pytest.raises(SourceError, match="cannot be read") as excinfo:
            provider.fetch(provider.full_ref(candidate), tmp_path / "x", library.context().deadline)
        assert excinfo.value.kind is SourceErrorKind.NOT_FOUND
        assert not (tmp_path / "x").exists()

    def test_a_different_file_with_the_same_content_is_refused(
        self, library: Library, tmp_path: Path
    ) -> None:
        provider, candidate, path = self._offered(library)
        data = path.read_bytes()
        path.unlink()
        path.write_bytes(data)  # a new inode with identical bytes
        with pytest.raises(SourceError, match="changed"):
            provider.fetch(provider.full_ref(candidate), tmp_path / "x", library.context().deadline)

    def test_the_destination_is_never_overwritten(self, library: Library, tmp_path: Path) -> None:
        provider, candidate, _path = self._offered(library)
        target = tmp_path / "x"
        target.write_bytes(b"keep")
        with pytest.raises(FileExistsError):
            provider.fetch(provider.full_ref(candidate), target, library.context().deadline)
        assert target.read_bytes() == b"keep"


def _open_fds() -> set[int]:
    found = set()
    for fd in range(256):
        try:
            os.fstat(fd)
        except OSError:
            continue
        found.add(fd)
    return found


class ScriptedInspector:
    """Stands in for the worker: answers a batch with scripted events per
    call, checks what it was given, and records it."""

    def __init__(self, *calls: object) -> None:
        self.calls = list(calls)
        self.batches: list[list[int]] = []
        self.timeouts: list[float] = []

    def run(
        self,
        task: str,
        payload: JsonObject,
        *,
        timeout: float,
        on_event: Any = None,
        should_stop: Any = None,
        files: Any = (),
    ) -> JsonObject:
        assert task == "inspect"
        batch = InspectBatch.from_json(payload)
        assert [file.fd for file in batch.files] == list(files)
        assert all(os.fstat(fd) for fd in files)  # open while the worker runs
        self.batches.append(list(files))
        self.timeouts.append(timeout)
        script = self.calls.pop(0)
        assert callable(script)
        return script(batch, on_event, should_stop)  # type: ignore[no-any-return]

    def terminate_all(self) -> None: ...


def _sizes(*sizes: Size | None) -> Any:
    """A script that reports these sizes in order and then returns."""

    def answer(batch: InspectBatch, on_event: Any, _stop: Any) -> JsonObject:
        for index, size in enumerate(sizes):
            if size is None:
                result = InspectResult(status=InspectStatus.FAILED, failure=PrepareFailure.DECODE)
            else:
                result = InspectResult(status=InspectStatus.OK, oriented_size=size)
            on_event(inspected_event(index, result))
        return {"inspected": len(batch.files)}

    return answer


def _then_fail(*sizes: Size, error: WorkerError) -> Any:
    """A script that reports these sizes, then fails like a worker would."""

    def answer(batch: InspectBatch, on_event: Any, _stop: Any) -> JsonObject:
        for index, size in enumerate(sizes):
            on_event(inspected_event(index, InspectResult(InspectStatus.OK, oriented_size=size)))
        raise error

    return answer


class TestInspection:
    def _probe(self, library: Library) -> tuple[LocalMediaProvider, LocalInspectionProbe]:
        provider = library.provider()
        executor = default_executor(library.clock)
        return provider, LocalInspectionProbe(provider, executor)

    def test_sizes_after_orientation(self, library: Library) -> None:
        oriented_jpeg(library.root, 6, (96, 54))
        provider, probe = self._probe(library)
        (candidate,) = library.candidates(provider)
        assert probe.source is DimensionSource.LOCAL_INSPECTION
        assert probe.max_batch == MAX_INSPECT_BATCH
        assert probe.measure(candidate, library.context().deadline) == Size(96, 54)

    def test_a_batch_runs_in_one_worker_and_closes_its_descriptors(self, library: Library) -> None:
        library.jpeg("a.jpg", (40, 30))
        library.png("b.png", (30, 40))
        library.file("c.jpg", b"\xff\xd8\xff\xe0garbage")
        provider = library.provider()
        candidates = sorted(library.candidates(provider), key=lambda c: c.attribution.title or "")
        before = _open_fds()
        inspector = ScriptedInspector(_sizes(Size(40, 30), Size(30, 40), None))
        probe = LocalInspectionProbe(provider, inspector)
        measurements = probe.measure_batch(candidates, library.context().deadline)
        assert [m.size for m in measurements] == [Size(40, 30), Size(30, 40), None]
        assert all(m.error is None for m in measurements)
        assert len(inspector.batches) == 1
        assert inspector.timeouts == [3 * LOCAL_INSPECTION_S]
        assert _open_fds() == before
        assert provider.report.counts == {SkipReason.UNREADABLE: 1}

    def test_the_real_task_reads_the_passed_descriptors(self, library: Library) -> None:
        library.jpeg("a.jpg", (40, 30))
        library.file("b.jpg", b"\xff\xd8\xff\xe0garbage")
        provider, probe = self._probe(library)
        candidates = sorted(library.candidates(provider), key=lambda c: c.attribution.title or "")
        before = _open_fds()
        measurements = probe.measure_batch(candidates, library.context().deadline)
        assert [m.size for m in measurements] == [Size(40, 30), None]
        assert _open_fds() == before
        assert provider.report.counts == {SkipReason.UNREADABLE: 1}

    def test_a_file_that_is_too_slow_fails_and_the_rest_go_to_a_new_worker(
        self, library: Library
    ) -> None:
        for name in ("a", "b", "c", "d"):
            library.jpeg(f"{name}.jpg")
        provider = library.provider()
        candidates = sorted(library.candidates(provider), key=lambda c: c.attribution.title or "")
        now = [100.0]
        stops: list[bool] = []

        def slow_third(batch: InspectBatch, on_event: Any, should_stop: Any) -> JsonObject:
            for index in range(2):
                on_event(inspected_event(index, InspectResult(InspectStatus.OK, Size(4, 3))))
            stops.append(should_stop())
            now[0] += LOCAL_INSPECTION_S + 0.1
            stops.append(should_stop())
            raise WorkerError(WorkerErrorKind.STOPPED)

        inspector = ScriptedInspector(slow_third, _sizes(Size(8, 6)))
        probe = LocalInspectionProbe(provider, inspector, monotonic=lambda: now[0])
        measurements = probe.measure_batch(candidates, library.context().deadline)
        assert stops == [False, True]
        assert [m.size for m in measurements] == [Size(4, 3), Size(4, 3), None, Size(8, 6)]
        failed = measurements[2].error
        assert failed is not None
        assert failed.kind is SourceErrorKind.UNEXPECTED_FORMAT
        assert str(failed).endswith("inspection failed (too slow)")
        assert [len(batch) for batch in inspector.batches] == [4, 1]
        assert provider.report.counts == {SkipReason.INSPECTION_FAILED: 1}

    def test_a_worker_that_fails_after_every_event_fails_no_file(self, library: Library) -> None:
        library.jpeg("a.jpg")
        provider = library.provider()
        (candidate,) = library.candidates(provider)
        inspector = ScriptedInspector(
            _then_fail(Size(4, 3), error=WorkerError(WorkerErrorKind.CRASH, "late"))
        )
        probe = LocalInspectionProbe(provider, inspector)
        assert probe.measure(candidate, library.context().deadline) == Size(4, 3)
        assert len(inspector.batches) == 1

    @pytest.mark.parametrize(
        ("error", "detail"),
        [
            (WorkerError(WorkerErrorKind.CRASH, "boom"), "crash"),
            (WorkerError(WorkerErrorKind.PROTOCOL, "event"), "protocol"),
            (WorkerError(WorkerErrorKind.TIMEOUT, "slow"), "timeout"),
        ],
    )
    def test_a_failed_worker_fails_the_file_in_progress(
        self, library: Library, error: WorkerError, detail: str
    ) -> None:
        library.jpeg("a.jpg")
        provider = library.provider()
        (candidate,) = library.candidates(provider)
        probe = LocalInspectionProbe(provider, ScriptedInspector(_then_fail(error=error)))
        with pytest.raises(SourceError) as excinfo:
            probe.measure(candidate, library.context().deadline)
        assert excinfo.value.kind is SourceErrorKind.UNEXPECTED_FORMAT
        assert str(excinfo.value).endswith(f"inspection failed ({detail})")
        assert provider.report.counts == {SkipReason.INSPECTION_FAILED: 1}

    @pytest.mark.parametrize("result", [{"inspected": 7}, {"status": "nonsense"}])
    def test_an_invalid_result_fails_the_files_without_an_event(
        self, library: Library, result: JsonObject
    ) -> None:
        library.jpeg("a.jpg")
        library.jpeg("b.jpg")
        provider = library.provider()
        candidates = sorted(library.candidates(provider), key=lambda c: c.attribution.title or "")

        def one_event(batch: InspectBatch, on_event: Any, _stop: Any) -> JsonObject:
            on_event(inspected_event(0, InspectResult(InspectStatus.OK, Size(4, 3))))
            return result

        probe = LocalInspectionProbe(provider, ScriptedInspector(one_event))
        measurements = probe.measure_batch(candidates, library.context().deadline)
        assert measurements[0].size == Size(4, 3)
        assert measurements[1].error is not None
        assert str(measurements[1].error).endswith("inspection failed (invalid result)")

    def test_a_wrong_result_after_every_event_changes_nothing(self, library: Library) -> None:
        library.jpeg("a.jpg")
        provider = library.provider()
        (candidate,) = library.candidates(provider)

        def odd_result(batch: InspectBatch, on_event: Any, _stop: Any) -> JsonObject:
            on_event(inspected_event(0, InspectResult(InspectStatus.OK, Size(4, 3))))
            return {"inspected": 2}

        probe = LocalInspectionProbe(provider, ScriptedInspector(odd_result))
        assert probe.measure(candidate, library.context().deadline) == Size(4, 3)

    def test_an_event_too_many_is_a_protocol_failure(self, library: Library) -> None:
        """A worker that reports a file it was not given fails as `protocol`
        in the executor; the files it did report keep their results."""
        library.jpeg("a.jpg")
        provider = library.provider()
        (candidate,) = library.candidates(provider)

        def two_events(payload: JsonObject, emit: EventSink) -> JsonObject:
            for index in (0, 1):
                emit(inspected_event(index, InspectResult(InspectStatus.OK, Size(4, 3))))
            return {"inspected": 2}

        executor = InProcessExecutor({}, library.clock, event_tasks={"inspect": two_events})
        probe = LocalInspectionProbe(provider, executor)
        assert probe.measure(candidate, library.context().deadline) == Size(4, 3)

    def test_an_isolation_failure_is_not_an_inspection_failure(self, library: Library) -> None:
        """D-163: it ends the run as internal_error instead of skipping files."""
        library.jpeg("a.jpg")
        provider = library.provider()
        (candidate,) = library.candidates(provider)
        before = _open_fds()

        def refuse(batch: InspectBatch, on_event: Any, _stop: Any) -> JsonObject:
            raise IsolationFailure("the worker refused to run (environment)")

        probe = LocalInspectionProbe(provider, ScriptedInspector(refuse))
        with pytest.raises(IsolationFailure):
            probe.measure(candidate, library.context().deadline)
        assert _open_fds() == before

    def test_a_timeout_at_the_discovery_deadline_is_not_a_failure(self, library: Library) -> None:
        library.jpeg("healthy.jpg")
        provider = library.provider()
        (candidate,) = library.candidates(provider)
        clock = library.clock
        deadline = Deadline.after(clock, 1.0, "discovery")

        def slow(batch: InspectBatch, on_event: Any, _stop: Any) -> JsonObject:
            clock.advance(1.0)
            raise WorkerError(WorkerErrorKind.TIMEOUT, "slow")

        with pytest.raises(DeadlineExceeded):
            LocalInspectionProbe(provider, ScriptedInspector(slow)).measure(candidate, deadline)
        assert provider.report.counts == {}

    def test_the_parent_refuses_a_file_that_changed(self, library: Library) -> None:
        path = library.jpeg("a.jpg")
        provider = library.provider()
        (candidate,) = library.candidates(provider)
        data = path.read_bytes()
        path.unlink()
        path.write_bytes(data)  # same bytes, another inode
        inspector = ScriptedInspector()
        probe = LocalInspectionProbe(provider, inspector)
        assert probe.measure(candidate, library.context().deadline) is None
        assert inspector.batches == []  # no worker for it
        assert provider.report.counts == {SkipReason.CHANGED: 1}

    def test_the_parent_never_follows_a_link(self, library: Library) -> None:
        path = library.jpeg("a.jpg")
        provider = library.provider()
        (candidate,) = library.candidates(provider)
        real = path.with_name("elsewhere.jpg")
        path.rename(real)
        path.symlink_to(real)
        probe = LocalInspectionProbe(provider, ScriptedInspector())
        assert probe.measure(candidate, library.context().deadline) is None
        assert provider.report.counts == {SkipReason.UNREADABLE: 1}

    def test_a_file_whose_status_cannot_be_read_is_unreadable(
        self, library: Library, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        library.jpeg("a.jpg")
        provider = library.provider()
        (candidate,) = library.candidates(provider)
        before = _open_fds()

        def failing_fstat(fd: int) -> os.stat_result:
            raise OSError(errno.EIO, "I/O error")

        monkeypatch.setattr(os, "fstat", failing_fstat)
        probe = LocalInspectionProbe(provider, ScriptedInspector())
        assert probe.measure(candidate, library.context().deadline) is None
        monkeypatch.undo()
        assert _open_fds() == before
        assert provider.report.counts == {SkipReason.UNREADABLE: 1}

    def test_an_interruption_while_opening_closes_what_was_opened(
        self, library: Library, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        library.jpeg("a.jpg")
        library.jpeg("b.jpg")
        provider = library.provider()
        candidates = sorted(library.candidates(provider), key=lambda c: c.attribution.title or "")
        before = _open_fds()
        real_open = os.open
        opened: list[int] = []

        def open_once(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
            if opened:
                raise Cancelled
            fd = real_open(path, flags, *args, **kwargs)
            opened.append(fd)
            return fd

        monkeypatch.setattr(os, "open", open_once)
        probe = LocalInspectionProbe(provider, ScriptedInspector())
        with pytest.raises(Cancelled):
            probe.measure_batch(candidates, library.context().deadline)
        monkeypatch.undo()
        assert _open_fds() == before

    def test_no_time_left(self, library: Library) -> None:
        library.jpeg("a.jpg")
        provider, probe = self._probe(library)
        (candidate,) = library.candidates(provider)
        deadline = Deadline.after(library.clock, 1.0, "discovery")
        library.clock.advance(1.0)
        with pytest.raises(DeadlineExceeded):
            probe.measure(candidate, deadline)


def test_selection_over_a_real_library(library: Library, caplog: pytest.LogCaptureFixture) -> None:
    """The provider, the probe, and selection together: landscape works near
    16:9 are shortlisted; portraits, junk, and a broken file are not."""
    library.jpeg("wide.jpg", (1920, 1080))
    library.png("also_wide.png", (1600, 900))
    library.jpeg("portrait.jpg", (900, 1600))
    library.file("broken.jpg", b"\xff\xd8\xff\xe0garbage")
    library.file("notes.txt")
    provider, probe = TestInspection()._probe(library)
    context = library.context()
    with caplog.at_level(logging.WARNING):
        result = build_shortlist(
            provider.iter_candidates(FILTERS, context),
            exclusions=ExclusionSet(),
            policy=SelectionPolicy(
                landscape_only=True, strict_tv_format=True, fit_mode=FitMode.CONTAIN
            ),
            allowed_rights=frozenset({RightsBasis.USER_SUPPLIED}),
            deadline=context.deadline,
            random=SeededRandomSource(1),
            candidate_allowance=Allowance("candidates", 150),
            probe_allowance=Allowance("remote_probes", 30),
            inspection_allowance=Allowance("local_inspections", 300),
            probe=probe,
        )
    assert sorted(entry.candidate.attribution.title or "" for entry in result.entries) == [
        "also_wide",
        "wide",
    ]
    assert result.stats.inspections_used >= 2
    assert result.stats.probes_used == 0
    assert not result.transport_failure
    # The four images form one batch, measured after the scan had ended; the
    # warning still counts the broken one.
    assert "local library" not in caplog.text
    with caplog.at_level(logging.WARNING):
        provider.report_discovery()
    assert "unreadable=1" in caplog.text
    assert "unsupported_extension=1" in caplog.text
    assert result.end in (DiscoveryEnd.SHORTLIST_FULL, DiscoveryEnd.EXHAUSTED)
