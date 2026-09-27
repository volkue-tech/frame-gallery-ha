"""The local media provider (§9.3, D-118; F7), with a real temporary library
of synthesized images."""

from __future__ import annotations

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
from frame_gallery.config.filters import EffectiveFilters, FilterSet
from frame_gallery.domain import FitMode, Size, SourceKey
from frame_gallery.fingerprint import FINGERPRINT_EDGE, fingerprint_bytes, fingerprint_fd
from frame_gallery.imaging.contract import MAX_SOURCE_BYTES, ImageFormat
from frame_gallery.isolation.executor import JsonObject, WorkerError, WorkerErrorKind
from frame_gallery.isolation.in_process import InProcessExecutor, default_tasks
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
        provider = provider or self.provider()
        return list(provider.iter_candidates(FILTERS, self.context()))


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
        self, library: Library, monkeypatch: pytest.MonkeyPatch
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

    def test_the_warning_is_emitted_when_discovery_stops_early(
        self, library: Library, caplog: pytest.LogCaptureFixture
    ) -> None:
        library.file("a.txt")
        library.jpeg("b.jpg")
        library.jpeg("c.jpg")
        iterator: Iterator[Candidate] = library.provider().iter_candidates(
            FILTERS, library.context()
        )
        next(iterator)
        assert "local library" not in caplog.text
        iterator.close()  # type: ignore[attr-defined]
        assert "unsupported_extension=1" in caplog.text

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
        assert stat.S_IMODE(target.stat().st_mode) == 0o600

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


class TestInspection:
    def _probe(self, library: Library) -> tuple[LocalMediaProvider, LocalInspectionProbe]:
        provider = library.provider()
        executor = InProcessExecutor(default_tasks(), library.clock)
        return provider, LocalInspectionProbe(provider, executor)

    def test_sizes_after_orientation(self, library: Library) -> None:
        oriented_jpeg(library.root, 6, (96, 54))
        provider, probe = self._probe(library)
        (candidate,) = library.candidates(provider)
        assert probe.source is DimensionSource.LOCAL_INSPECTION
        assert probe.measure(candidate, library.context().deadline) == Size(96, 54)

    def test_unreadable_images_give_none(self, library: Library) -> None:
        library.file("broken.jpg", b"\xff\xd8\xff\xe0garbage")
        provider, probe = self._probe(library)
        (candidate,) = library.candidates(provider)
        assert probe.measure(candidate, library.context().deadline) is None
        assert provider.report.counts == {SkipReason.UNREADABLE: 1}

    @pytest.mark.parametrize(
        "outcome",
        [WorkerError(WorkerErrorKind.CRASH, "boom"), {"status": "nonsense"}],
    )
    def test_worker_failures_raise(self, library: Library, outcome: object) -> None:
        library.jpeg("a.jpg")
        provider = library.provider()
        (candidate,) = library.candidates(provider)

        class Broken:
            def run(self, task: str, payload: JsonObject, *, timeout: float) -> JsonObject:
                assert task == "inspect"
                assert timeout == 2.0
                if isinstance(outcome, BaseException):
                    raise outcome
                return outcome  # type: ignore[return-value]

            def terminate_all(self) -> None: ...

        probe = LocalInspectionProbe(provider, Broken())
        with pytest.raises(SourceError) as excinfo:
            probe.measure(candidate, library.context().deadline)
        assert excinfo.value.kind is SourceErrorKind.UNEXPECTED_FORMAT
        assert provider.report.counts == {SkipReason.INSPECTION_FAILED: 1}

    def test_a_timeout_at_the_discovery_deadline_is_not_a_failure(self, library: Library) -> None:
        library.jpeg("healthy.jpg")
        provider = library.provider()
        (candidate,) = library.candidates(provider)
        clock = library.clock
        deadline = Deadline.after(clock, 1.0, "discovery")

        class Slow:
            def run(self, task: str, payload: JsonObject, *, timeout: float) -> JsonObject:
                clock.advance(timeout)
                raise WorkerError(WorkerErrorKind.TIMEOUT, "slow")

            def terminate_all(self) -> None: ...

        with pytest.raises(DeadlineExceeded):
            LocalInspectionProbe(provider, Slow()).measure(candidate, deadline)
        assert provider.report.counts == {}

    def test_the_worker_refuses_a_file_that_changed(self, library: Library) -> None:
        path = library.jpeg("a.jpg")
        provider, probe = self._probe(library)
        (candidate,) = library.candidates(provider)
        data = path.read_bytes()
        path.unlink()
        path.write_bytes(data)  # same bytes, another inode
        assert probe.measure(candidate, library.context().deadline) is None
        assert provider.report.counts == {SkipReason.UNREADABLE: 1}

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
    assert result.end in (DiscoveryEnd.SHORTLIST_FULL, DiscoveryEnd.EXHAUSTED)
