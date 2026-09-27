"""The atomic write primitive and the bounded reader (store/atomic.py, §13.2)."""

from __future__ import annotations

import errno
import json
import logging
import os
import stat
from collections.abc import Callable, Iterator, Mapping
from datetime import UTC, datetime
from pathlib import Path

import pytest

from frame_gallery.errors import StateError
from frame_gallery.store import atomic
from frame_gallery.store.atomic import (
    BACKUP_SUFFIX,
    QUARANTINE_DIRECTORY,
    TEMPORARY_NAME,
    CommitError,
    Directory,
    DocumentFile,
    DocumentSpec,
    Origin,
    Quarantine,
    ReadFailure,
    check_name,
    decode_json,
    encode_json,
    open_directory,
    read_document,
)

NOW = datetime(2026, 9, 27, 12, 0, 0, tzinfo=UTC)


def parse_items(document: Mapping[str, object]) -> list[int]:
    items = document.get("items")
    if not isinstance(items, list) or not all(isinstance(i, int) for i in items):
        msg = "items must be a list of integers"
        raise ValueError(msg)
    return list(items)


SPEC = DocumentSpec("test-doc", 2, 4096, parse_items)


def document(items: list[int], version: int = 2) -> dict[str, object]:
    return {"format": "test-doc", "version": version, "items": items}


def raw(value: object) -> bytes:
    return json.dumps(value).encode()


@pytest.fixture
def directory(tmp_path: Path) -> Iterator[Directory]:
    with open_directory(tmp_path, ("state",), create=True) as opened:
        yield opened


def state_path(directory: Directory) -> Path:
    return Path(directory.label)


def put(directory: Directory, name: str, data: bytes) -> None:
    (state_path(directory) / name).write_bytes(data)


def quarantine_of(directory: Directory) -> Quarantine:
    return Quarantine(directory, lambda: NOW)


def quarantined(directory: Directory) -> list[str]:
    holding = state_path(directory) / QUARANTINE_DIRECTORY
    return sorted(p.name for p in holding.iterdir()) if holding.exists() else []


class TestNames:
    @pytest.mark.parametrize("name", ["history.json", "a", "upload_ledger.json", "x-1.bak"])
    def test_plain_names_are_accepted(self, name: str) -> None:
        assert check_name(name) == name

    @pytest.mark.parametrize(
        "name", ["", ".hidden", "..", "a/b", "a\\b", "x.tmp-0123", "é", "a" * 101]
    )
    def test_other_names_are_refused(self, name: str) -> None:
        with pytest.raises(ValueError, match="invalid file name"):
            check_name(name)

    def test_the_temporary_pattern_matches_both_forms(self) -> None:
        assert TEMPORARY_NAME.fullmatch("history.json.tmp-0123456789abcdef")
        assert TEMPORARY_NAME.fullmatch("history.json.bak.tmp-0123456789abcdef")
        assert not TEMPORARY_NAME.fullmatch("history.json.tmp-0123")
        assert not TEMPORARY_NAME.fullmatch(".x.tmp-0123456789abcdef")


class TestOpenDirectory:
    def test_missing_parts_are_created_with_the_mode(self, tmp_path: Path) -> None:
        with open_directory(tmp_path, ("a", "b"), create=True, mode=0o700) as opened:
            assert opened.label == str(tmp_path / "a" / "b")
        assert stat.S_IMODE((tmp_path / "a" / "b").stat().st_mode) == 0o700

    def test_an_existing_directory_is_opened(self, tmp_path: Path) -> None:
        (tmp_path / "a").mkdir()
        with open_directory(tmp_path, ("a",)) as opened:
            assert os.path.samestat(os.fstat(opened.fd), (tmp_path / "a").stat())

    def test_a_missing_part_is_an_error_without_create(self, tmp_path: Path) -> None:
        with pytest.raises(StateError, match="ENOENT"):
            open_directory(tmp_path, ("missing",))

    def test_a_linked_part_is_refused(self, tmp_path: Path) -> None:
        (tmp_path / "real").mkdir()
        (tmp_path / "link").symlink_to(tmp_path / "real")
        with pytest.raises(StateError, match="symbolic link or not a directory"):
            open_directory(tmp_path, ("link",), create=True)

    def test_a_linked_anchor_is_refused(self, tmp_path: Path) -> None:
        (tmp_path / "real").mkdir()
        (tmp_path / "link").symlink_to(tmp_path / "real")
        with pytest.raises(StateError, match="symbolic link or not a directory"):
            open_directory(tmp_path / "link")

    def test_a_file_in_place_of_a_part_is_refused(self, tmp_path: Path) -> None:
        (tmp_path / "file").write_text("x")
        with pytest.raises(StateError, match="symbolic link or not a directory"):
            open_directory(tmp_path, ("file",), create=True)

    def test_a_part_created_concurrently_is_opened(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        real_mkdir = os.mkdir

        def racing_mkdir(name: str, mode: int = 0o777, *, dir_fd: int | None = None) -> None:
            real_mkdir(name, mode, dir_fd=dir_fd)
            raise FileExistsError(errno.EEXIST, "exists")

        monkeypatch.setattr(os, "mkdir", racing_mkdir)
        with open_directory(tmp_path, ("raced",), create=True) as opened:
            assert opened.label.endswith("raced")

    def test_invalid_parts_are_refused_before_anything_is_opened(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="invalid file name"):
            open_directory(tmp_path, ("..",))


class TestDirectory:
    def test_a_closed_directory_refuses_to_work(self, tmp_path: Path) -> None:
        opened = open_directory(tmp_path)
        opened.close()
        opened.close()  # idempotent
        with pytest.raises(StateError, match="closed"):
            _ = opened.fd

    def test_close_ignores_errors(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        opened = open_directory(tmp_path)
        fd = opened.fd

        def failing_close(_fd: int) -> None:
            raise OSError(errno.EIO, "io")

        monkeypatch.setattr(os, "close", failing_close)
        opened.close()
        monkeypatch.undo()
        os.close(fd)

    def test_child_opens_and_creates(self, directory: Directory) -> None:
        with directory.child("sub", create=True) as sub:
            assert sub.label == f"{directory.label}/sub"
        assert (state_path(directory) / "sub").is_dir()

    def test_child_refuses_a_link(self, directory: Directory, tmp_path: Path) -> None:
        (state_path(directory) / "sub").symlink_to(tmp_path)
        with pytest.raises(StateError, match="symbolic link"):
            directory.child("sub")

    def test_child_reports_a_failed_dup(
        self, directory: Directory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def failing_dup(_fd: int) -> int:
            raise OSError(errno.EMFILE, "too many")

        monkeypatch.setattr(os, "dup", failing_dup)
        with pytest.raises(StateError, match="EMFILE"):
            directory.child("sub", create=True)

    def test_names_are_bounded(self, directory: Directory) -> None:
        for index in range(5):
            put(directory, f"f{index}", b"x")
        assert len(directory.names(3)) == 3
        assert sorted(directory.names(10)) == [f"f{i}" for i in range(5)]

    def test_file_kinds(self, directory: Directory, tmp_path: Path) -> None:
        put(directory, "file", b"x")
        (state_path(directory) / "dir").mkdir()
        (state_path(directory) / "link").symlink_to(tmp_path)
        assert directory.is_regular_file("file")
        assert not directory.is_regular_file("link")
        assert directory.is_directory("dir")
        assert not directory.is_directory("link")

    def test_remove_handles_files_links_and_trees(
        self, directory: Directory, tmp_path: Path
    ) -> None:
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "keep").write_text("keep")
        put(directory, "file", b"x")
        (state_path(directory) / "link").symlink_to(outside)
        (state_path(directory) / "tree" / "deep").mkdir(parents=True)
        (state_path(directory) / "tree" / "deep" / "leaf").write_text("x")
        for name in ("file", "link", "tree"):
            directory.remove(name)
        assert directory.names(10) == []
        assert (outside / "keep").exists()

    def test_unlink_reports_whether_it_removed(self, directory: Directory) -> None:
        put(directory, "file", b"x")
        assert directory.unlink("file")
        assert not directory.unlink("file")

    def test_rename_into_moves_between_directories(self, directory: Directory) -> None:
        put(directory, "file", b"x")
        with directory.child("other", create=True) as other:
            directory.rename_into("file", other, "moved")
        assert (state_path(directory) / "other" / "moved").read_bytes() == b"x"


class TestReadBytes:
    def test_a_regular_file_is_read(self, directory: Directory) -> None:
        put(directory, "f", b"hello")
        assert directory.read_bytes("f", 5) == b"hello"

    def test_a_large_file_is_read_in_chunks(
        self, directory: Directory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(atomic, "READ_CHUNK", 3)
        put(directory, "f", b"0123456789")
        assert directory.read_bytes("f", 10) == b"0123456789"

    def test_missing(self, directory: Directory) -> None:
        assert directory.read_bytes("f", 5) is ReadFailure.MISSING

    def test_a_link_is_not_followed(self, directory: Directory, tmp_path: Path) -> None:
        target = tmp_path / "target"
        target.write_bytes(b"secret")
        (state_path(directory) / "f").symlink_to(target)
        assert directory.read_bytes("f", 100) is ReadFailure.NOT_REGULAR

    def test_a_directory_is_not_regular(self, directory: Directory) -> None:
        (state_path(directory) / "f").mkdir()
        assert directory.read_bytes("f", 100) is ReadFailure.NOT_REGULAR

    def test_a_fifo_is_not_regular_and_never_blocks(self, directory: Directory) -> None:
        os.mkfifo(state_path(directory) / "f")
        assert directory.read_bytes("f", 100) is ReadFailure.NOT_REGULAR

    @pytest.mark.parametrize("code", [errno.ENXIO, errno.EOPNOTSUPP])
    def test_a_socket_is_not_regular(
        self, directory: Directory, monkeypatch: pytest.MonkeyPatch, code: int
    ) -> None:
        def failing_open(*_args: object, **_kwargs: object) -> int:
            raise OSError(code, "socket")

        monkeypatch.setattr(os, "open", failing_open)
        assert directory.read_bytes("f", 100) is ReadFailure.NOT_REGULAR

    def test_a_file_that_cannot_be_opened_is_unreadable(
        self, directory: Directory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def failing_open(*_args: object, **_kwargs: object) -> int:
            raise PermissionError(errno.EACCES, "denied")

        monkeypatch.setattr(os, "open", failing_open)
        assert directory.read_bytes("f", 100) is ReadFailure.UNREADABLE

    def test_a_read_error_is_unreadable(
        self, directory: Directory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        put(directory, "f", b"hello")

        def failing_read(_fd: int, _size: int) -> bytes:
            raise OSError(errno.EIO, "io")

        monkeypatch.setattr(os, "read", failing_read)
        assert directory.read_bytes("f", 100) is ReadFailure.UNREADABLE

    def test_a_file_over_the_limit_is_oversize(self, directory: Directory) -> None:
        put(directory, "f", b"123456")
        assert directory.read_bytes("f", 5) is ReadFailure.OVERSIZE

    def test_a_file_that_grows_while_read_is_oversize(
        self, directory: Directory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        put(directory, "f", b"123456")
        real_fstat = os.fstat

        class Shrunk:
            def __init__(self, info: os.stat_result) -> None:
                self.st_mode = info.st_mode
                self.st_size = 1

        monkeypatch.setattr(os, "fstat", lambda fd: Shrunk(real_fstat(fd)))
        assert directory.read_bytes("f", 5) is ReadFailure.OVERSIZE


class TestStageAndCommit:
    def test_write_replaces_the_target_with_the_mode(self, directory: Directory) -> None:
        old = os.umask(0o077)
        try:
            directory.write("f", b"one", mode=0o644)
        finally:
            os.umask(old)
        path = state_path(directory) / "f"
        assert path.read_bytes() == b"one"
        assert stat.S_IMODE(path.stat().st_mode) == 0o644
        assert directory.names(10) == ["f"]

    def test_stage_leaves_the_target_alone_until_commit(self, directory: Directory) -> None:
        put(directory, "f", b"old")
        staged = directory.stage("f", b"new")
        assert TEMPORARY_NAME.fullmatch(staged.temporary)
        assert (state_path(directory) / "f").read_bytes() == b"old"
        directory.commit(staged, refresh_backup=False)
        assert (state_path(directory) / "f").read_bytes() == b"new"

    def test_discard_removes_the_staged_file(self, directory: Directory) -> None:
        staged = directory.stage("f", b"new")
        directory.discard(staged)
        directory.discard(staged)  # never raises
        assert directory.names(10) == []

    def test_a_temporary_name_collision_is_an_error(
        self, directory: Directory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(atomic, "_token", lambda: "0123456789abcdef")
        put(directory, "f.tmp-0123456789abcdef", b"someone else's")
        with pytest.raises(StateError, match=r"cannot create a temporary file .EEXIST"):
            directory.stage("f", b"new")
        assert (state_path(directory) / "f.tmp-0123456789abcdef").read_bytes() == b"someone else's"

    @pytest.mark.parametrize("failing", ["write", "fsync", "fchmod", "close"])
    def test_a_failed_write_removes_the_temporary_file(
        self, directory: Directory, monkeypatch: pytest.MonkeyPatch, failing: str
    ) -> None:
        real = getattr(os, failing)

        def fail(*args: object, **kwargs: object) -> object:
            if failing == "close":
                real(*args, **kwargs)
            raise OSError(errno.ENOSPC, "full")

        monkeypatch.setattr(os, failing, fail)
        with pytest.raises(StateError, match=r"cannot write .ENOSPC"):
            directory.stage("f", b"new")
        monkeypatch.undo()
        assert directory.names(10) == []

    def test_a_write_without_progress_is_an_error(
        self, directory: Directory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(os, "write", lambda _fd, _data: 0)
        with pytest.raises(StateError, match=r"cannot write .EIO"):
            directory.stage("f", b"new")

    def test_partial_writes_are_continued(
        self, directory: Directory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        real_write = os.write
        monkeypatch.setattr(os, "write", lambda fd, data: real_write(fd, bytes(data[:2])))
        directory.write("f", b"abcdefg")
        assert (state_path(directory) / "f").read_bytes() == b"abcdefg"

    def test_a_failed_rename_is_not_replaced(self, directory: Directory) -> None:
        (state_path(directory) / "f").mkdir()
        (state_path(directory) / "f" / "child").write_text("x")
        staged = directory.stage("f", b"new")
        with pytest.raises(CommitError) as caught:
            directory.commit(staged, refresh_backup=False)
        assert caught.value.replaced is False
        assert directory.names(10) == ["f"]

    def test_a_failed_directory_flush_is_replaced(
        self, directory: Directory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        staged = directory.stage("f", b"new")
        real_fsync = os.fsync

        def fsync(fd: int) -> None:
            if fd == directory.fd:
                raise OSError(errno.EIO, "io")
            real_fsync(fd)

        monkeypatch.setattr(os, "fsync", fsync)
        with pytest.raises(CommitError, match="could not be flushed") as caught:
            directory.commit(staged, refresh_backup=False)
        assert caught.value.replaced is True
        assert (state_path(directory) / "f").read_bytes() == b"new"


class TestBackup:
    def test_the_backup_is_the_previous_generation(self, directory: Directory) -> None:
        directory.write("f", b"one")
        directory.write("f", b"two", refresh_backup=True)
        assert (state_path(directory) / "f").read_bytes() == b"two"
        assert (state_path(directory) / ("f" + BACKUP_SUFFIX)).read_bytes() == b"one"
        assert sorted(directory.names(10)) == ["f", "f.bak"]

    def test_a_missing_primary_only_skips_the_backup(
        self, directory: Directory, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            directory.write("f", b"one", refresh_backup=True)
        assert (state_path(directory) / "f").read_bytes() == b"one"
        assert "backup copy was not refreshed (ENOENT)" in caplog.text
        assert directory.names(10) == ["f"]

    def test_a_failed_backup_rename_never_blocks_the_write(
        self, directory: Directory, caplog: pytest.LogCaptureFixture
    ) -> None:
        directory.write("f", b"one")
        (state_path(directory) / "f.bak").mkdir()
        (state_path(directory) / "f.bak" / "child").write_text("x")
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            directory.write("f", b"two", refresh_backup=True)
        assert (state_path(directory) / "f").read_bytes() == b"two"
        assert "backup copy was not refreshed" in caplog.text
        assert sorted(directory.names(10)) == ["f", "f.bak"]


class TestJson:
    def test_encoding_is_compact_ascii(self) -> None:
        data = encode_json({"a": "é", "b": [1, 2]}, 100)
        assert data == b'{"a":"\\u00e9","b":[1,2]}'

    def test_lone_surrogates_are_escaped(self) -> None:
        assert decode_json(encode_json({"a": "\ud800"}, 100)) == {"a": "\ud800"}

    @pytest.mark.parametrize(
        ("value", "message"),
        [
            ({"a": {1, 2}}, "cannot be serialized"),
            ({"a": float("nan")}, "cannot be serialized"),
            ({"a": "x" * 100}, "exceeds 50 bytes"),
            ({"a": (1, 2)}, "does not survive"),
            ({"a": {1: "x"}}, "does not survive"),
        ],
    )
    def test_documents_that_cannot_be_stored_are_refused(
        self, value: dict[str, object], message: str
    ) -> None:
        with pytest.raises(StateError, match=message):
            encode_json(value, 50)

    @pytest.mark.parametrize("text", [b"NaN", b"[Infinity]", b"-Infinity", b"{", b"\xff"])
    def test_invalid_json_is_refused(self, text: bytes) -> None:
        with pytest.raises(ValueError, match=r"."):
            decode_json(text)

    def test_deep_nesting_is_refused(self) -> None:
        with pytest.raises(ValueError, match="nested too deeply"):
            decode_json(b"[" * 100_000 + b"]" * 100_000)


class TestReadDocument:
    def read(self, directory: Directory, *, backup: bool = True) -> atomic.ReadResult[list[int]]:
        return read_document(
            directory, "doc.json", SPEC, backup=backup, quarantine=quarantine_of(directory)
        )

    def test_a_valid_primary_is_used(self, directory: Directory) -> None:
        put(directory, "doc.json", raw(document([1, 2])))
        result = self.read(directory)
        assert result.value == [1, 2]
        assert result.origin is Origin.PRIMARY
        assert result.primary_valid
        assert result.usable

    def test_nothing_at_all_is_empty_without_warnings(
        self, directory: Directory, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            result = self.read(directory)
        assert result.value is None
        assert result.origin is Origin.EMPTY
        assert not result.primary_valid
        assert result.usable
        assert caplog.text == ""

    @pytest.mark.parametrize(
        ("content", "reason"),
        [
            (b"{broken", "not valid JSON"),
            (raw([1, 2]), "not a test-doc document"),
            (raw({"format": "other", "version": 2, "items": []}), "not a test-doc document"),
            (raw({"format": "test-doc", "items": []}), "no valid version"),
            (raw({"format": "test-doc", "version": True, "items": []}), "no valid version"),
            (raw({"format": "test-doc", "version": "2", "items": []}), "no valid version"),
            (raw(document([], version=1)), "unsupported version 1"),
            (raw(document([], version=-3)), "unsupported version -3"),
            (raw({"format": "test-doc", "version": 2, "items": ["x"]}), "invalid content"),
            (b"x" * 5000, "over its size limit"),
        ],
    )
    def test_a_damaged_primary_is_quarantined_and_the_backup_used(
        self,
        directory: Directory,
        caplog: pytest.LogCaptureFixture,
        content: bytes,
        reason: str,
    ) -> None:
        put(directory, "doc.json", content)
        put(directory, "doc.json.bak", raw(document([7])))
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            result = self.read(directory)
        assert result.value == [7]
        assert result.origin is Origin.BACKUP
        assert not result.primary_valid
        assert reason in caplog.text
        assert "using the backup copy" in caplog.text
        assert not (state_path(directory) / "doc.json").exists()
        [moved] = quarantined(directory)
        assert moved.startswith("20260927T120000Z-")
        assert moved.endswith("-doc.json")

    def test_a_linked_primary_is_set_aside_without_touching_its_target(
        self, directory: Directory, tmp_path: Path
    ) -> None:
        target = tmp_path / "target.json"
        target.write_bytes(raw(document([9])))
        (state_path(directory) / "doc.json").symlink_to(target)
        result = self.read(directory)
        assert result.origin is Origin.EMPTY
        assert target.exists()
        [moved] = quarantined(directory)
        assert (state_path(directory) / QUARANTINE_DIRECTORY / moved).is_symlink()

    def test_a_missing_primary_falls_back_to_the_backup(self, directory: Directory) -> None:
        put(directory, "doc.json.bak", raw(document([3])))
        result = self.read(directory)
        assert result.value == [3]
        assert result.origin is Origin.BACKUP
        assert quarantined(directory) == []

    def test_both_damaged_is_empty_with_a_warning(
        self, directory: Directory, caplog: pytest.LogCaptureFixture
    ) -> None:
        put(directory, "doc.json", b"{")
        put(directory, "doc.json.bak", b"[")
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            result = self.read(directory)
        assert result.origin is Origin.EMPTY
        assert result.usable
        assert "no usable copy is left" in caplog.text
        assert len(quarantined(directory)) == 2

    def test_a_damaged_backup_alone_is_quarantined(self, directory: Directory) -> None:
        put(directory, "doc.json.bak", b"[")
        result = self.read(directory)
        assert result.origin is Origin.EMPTY
        assert len(quarantined(directory)) == 1

    def test_without_backup_the_copy_is_never_read(self, directory: Directory) -> None:
        put(directory, "doc.json", b"{")
        put(directory, "doc.json.bak", raw(document([3])))
        result = self.read(directory, backup=False)
        assert result.origin is Origin.EMPTY
        assert (state_path(directory) / "doc.json.bak").exists()

    def test_without_quarantine_a_damaged_file_stays(self, directory: Directory) -> None:
        put(directory, "doc.json", b"{")
        result = read_document(directory, "doc.json", SPEC, backup=False, quarantine=None)
        assert result.origin is Origin.EMPTY
        assert (state_path(directory) / "doc.json").exists()

    def test_a_newer_primary_is_reported_and_kept(self, directory: Directory) -> None:
        put(directory, "doc.json", raw(document([1], version=3)))
        put(directory, "doc.json.bak", raw(document([7])))
        result = self.read(directory)
        assert result.newer_version == 3
        assert result.value is None
        assert not result.usable
        assert (state_path(directory) / "doc.json").exists()
        assert quarantined(directory) == []

    def test_a_newer_backup_is_reported(self, directory: Directory) -> None:
        put(directory, "doc.json", b"{")
        put(directory, "doc.json.bak", raw(document([1], version=4)))
        result = self.read(directory)
        assert result.newer_version == 4
        assert not result.usable

    def test_an_unreadable_primary_is_reported_not_quarantined(
        self, directory: Directory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        put(directory, "doc.json", raw(document([1])))
        monkeypatch.setattr(Directory, "read_bytes", lambda *_: ReadFailure.UNREADABLE)
        result = self.read(directory)
        assert result.unreadable
        assert not result.usable
        assert quarantined(directory) == []

    def test_an_unreadable_backup_is_reported(
        self, directory: Directory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        answers = iter([ReadFailure.MISSING, ReadFailure.UNREADABLE])
        monkeypatch.setattr(Directory, "read_bytes", lambda *_: next(answers))
        assert self.read(directory).unreadable


class TestQuarantine:
    def test_at_most_three_files_are_kept_the_newest(self, directory: Directory) -> None:
        moments = iter(datetime(2026, 9, day, tzinfo=UTC) for day in range(1, 10))
        quarantine = Quarantine(directory, lambda: next(moments))
        for index in range(5):
            put(directory, f"f{index}", b"x")
            assert quarantine.take(f"f{index}")
        names = quarantined(directory)
        assert len(names) == 3
        assert [name.rsplit("-", 1)[1] for name in names] == ["f2", "f3", "f4"]

    def test_a_trimmed_directory_entry_is_removed_as_a_tree(self, directory: Directory) -> None:
        moments = iter(datetime(2026, 9, day, tzinfo=UTC) for day in range(1, 10))
        quarantine = Quarantine(directory, lambda: next(moments), limit=1)
        (state_path(directory) / "d" / "sub").mkdir(parents=True)
        assert quarantine.take("d")
        put(directory, "f", b"x")
        assert quarantine.take("f")
        assert [name.rsplit("-", 1)[1] for name in quarantined(directory)] == ["f"]

    def test_a_missing_file_is_reported(
        self, directory: Directory, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            assert not quarantine_of(directory).take("missing")
        assert "could not be quarantined (ENOENT)" in caplog.text

    def test_an_unusable_quarantine_directory_is_reported(
        self, directory: Directory, caplog: pytest.LogCaptureFixture
    ) -> None:
        put(directory, QUARANTINE_DIRECTORY, b"not a directory")
        put(directory, "f", b"x")
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            assert not quarantine_of(directory).take("f")
        assert "could not be quarantined" in caplog.text
        assert (state_path(directory) / "f").exists()

    def test_a_failed_trim_is_reported(
        self,
        directory: Directory,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        def failing_names(_self: Directory, _limit: int) -> list[str]:
            raise OSError(errno.EIO, "io")

        monkeypatch.setattr(Directory, "names", failing_names)
        put(directory, "f", b"x")
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            assert quarantine_of(directory).take("f")
        assert "old entries were not removed (EIO)" in caplog.text


class TestDocumentFile:
    def file(self, directory: Directory, *, backup: bool = True) -> DocumentFile[list[int]]:
        return DocumentFile(
            directory, "doc.json", SPEC, backup=backup, quarantine=quarantine_of(directory)
        )

    def test_write_then_load_round_trips(self, directory: Directory) -> None:
        file = self.file(directory)
        file.write(document([1, 2, 3]))
        assert self.file(directory).load().value == [1, 2, 3]

    def test_the_backup_is_refreshed_only_from_a_valid_primary(self, directory: Directory) -> None:
        put(directory, "doc.json", b"{damaged")
        put(directory, "doc.json.bak", raw(document([1])))
        file = self.file(directory)
        assert file.load().origin is Origin.BACKUP
        file.write(document([1, 2]))
        # The damaged primary was not copied over the good backup.
        assert json.loads((state_path(directory) / "doc.json.bak").read_bytes())["items"] == [1]
        file.write(document([1, 2, 3]))
        assert json.loads((state_path(directory) / "doc.json.bak").read_bytes())["items"] == [
            1,
            2,
        ]

    def test_without_backup_no_copy_is_made(self, directory: Directory) -> None:
        file = self.file(directory, backup=False)
        file.write(document([1]))
        file.write(document([2]))
        assert directory.names(10) == ["doc.json"]

    def test_an_invalid_document_is_never_written(self, directory: Directory) -> None:
        file = self.file(directory)
        for bad in (
            {"format": "test-doc", "version": 2, "items": ["x"]},
            {"format": "other", "version": 2, "items": []},
            document([], version=3),
        ):
            with pytest.raises(StateError, match="refusing to write an invalid document"):
                file.stage(bad)
        assert directory.names(10) == []

    def test_stage_and_discard(self, directory: Directory) -> None:
        file = self.file(directory)
        staged = file.stage(document([1]))
        file.discard(staged)
        assert directory.names(10) == []

    def test_a_replaced_primary_counts_as_valid_after_a_failed_flush(
        self, directory: Directory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        file = self.file(directory)
        staged = file.stage(document([1]))
        failing = FailingCommit(replaced=True)
        monkeypatch.setattr(Directory, "commit", failing.method())
        with pytest.raises(CommitError):
            file.commit(staged)
        monkeypatch.undo()
        file.write(document([2]))
        assert failing.refresh == [False]
        assert (state_path(directory) / "doc.json.bak").exists()

    def test_a_primary_not_replaced_stays_invalid(
        self, directory: Directory, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        file = self.file(directory)
        staged = file.stage(document([1]))
        monkeypatch.setattr(Directory, "commit", FailingCommit(replaced=False).method())
        with pytest.raises(CommitError):
            file.commit(staged)
        monkeypatch.undo()
        file.discard(staged)
        file.write(document([2]))
        assert not (state_path(directory) / "doc.json.bak").exists()


class FailingCommit:
    """Replaces ``Directory.commit``: records the call, then fails."""

    def __init__(self, *, replaced: bool) -> None:
        self.replaced = replaced
        self.refresh: list[bool] = []

    def __call__(
        self, directory: Directory, staged: atomic.Staged, *, refresh_backup: bool
    ) -> None:
        self.refresh.append(refresh_backup)
        if self.replaced:
            os.rename(
                staged.temporary, staged.name, src_dir_fd=directory.fd, dst_dir_fd=directory.fd
            )
        raise CommitError("injected", replaced=self.replaced)

    def method(self) -> Callable[..., None]:
        def commit(directory: Directory, staged: atomic.Staged, *, refresh_backup: bool) -> None:
            self(directory, staged, refresh_backup=refresh_backup)

        return commit
