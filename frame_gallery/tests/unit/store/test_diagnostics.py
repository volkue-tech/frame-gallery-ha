"""Own-directory, count-only diagnostics: read-only and strictly bounded."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest

from frame_gallery.budget.deadline import Deadline
from frame_gallery.store import diagnostics
from frame_gallery.store.atomic import Directory
from frame_gallery.store.diagnostics import (
    ENTRY_LIMIT,
    StorageStats,
    inspect_directory,
    log_storage,
)
from frame_gallery.store.layout import StoreLayout
from tests.support.clock import FakeClock


def test_statistics_do_not_read_contents_follow_links_or_recurse(tmp_path: Path) -> None:
    (tmp_path / "history.json").write_bytes(b"private-content")
    (tmp_path / "history.json.tmp-0123456789abcdef").write_bytes(b"abc")
    (tmp_path / "subdirectory").mkdir()
    (tmp_path / "subdirectory" / "ignored").write_bytes(b"x" * 1000)
    (tmp_path / "run-0123456789abcdef").mkdir()
    (tmp_path / "linked").symlink_to(tmp_path / "subdirectory", target_is_directory=True)
    os.mkfifo(tmp_path / "fifo")
    before = sorted(p.name for p in tmp_path.iterdir())
    result = inspect_directory(tmp_path, (), Deadline.after(FakeClock(), 1, "scan"))
    assert result == StorageStats(
        files=2, bytes=18, temporary_files=1, run_directories=1, other_entries=3
    )
    assert sorted(p.name for p in tmp_path.iterdir()) == before
    assert (tmp_path / "history.json").read_bytes() == b"private-content"


def test_missing_and_symlinked_directories_are_not_empty_or_created(tmp_path: Path) -> None:
    (tmp_path / "link").symlink_to(tmp_path, target_is_directory=True)
    for parts in (("absent",), ("link",)):
        result = inspect_directory(tmp_path, parts, Deadline.after(FakeClock(), 1, "scan"))
        assert result.status == "unavailable"
    assert not (tmp_path / "absent").exists()


def test_scan_is_capped_at_128_entries(tmp_path: Path) -> None:
    for number in range(ENTRY_LIMIT + 10):
        (tmp_path / f"item-{number}").write_bytes(b"x")
    result = inspect_directory(tmp_path, (), Deadline.after(FakeClock(), 1, "scan"))
    assert result.files == result.bytes == ENTRY_LIMIT
    assert result.truncated


def test_time_budget_marks_a_partial_scan(tmp_path: Path) -> None:
    (tmp_path / "item").write_bytes(b"x")
    clock = FakeClock()
    deadline = Deadline.after(clock, 1, "scan")
    clock.advance(2)
    result = inspect_directory(tmp_path, (), deadline)
    assert result.files == 0
    assert result.truncated


def test_vanished_entry_is_marked_unreadable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "item").write_bytes(b"x")

    def vanished(*args: object, **kwargs: object) -> os.stat_result:
        raise FileNotFoundError

    with monkeypatch.context() as patch:
        patch.setattr(os, "stat", vanished)
        result = inspect_directory(tmp_path, (), Deadline.after(FakeClock(), 1, "scan"))
    assert result.unreadable_entries == 1
    assert result.files == 0


def test_listing_failure_is_not_reported_as_an_empty_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failed(self: Directory, limit: int) -> list[str]:
        raise OSError("private-path-not-to-log")

    monkeypatch.setattr(Directory, "names", failed)
    assert inspect_directory(tmp_path, (), Deadline.after(FakeClock(), 1, "scan")).status == (
        "unavailable"
    )


def test_logs_contain_only_fixed_labels_and_counts(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "sensitive-name.json").write_bytes(b"super-secret-value")
    layout = StoreLayout(tmp_path, tmp_path, tmp_path)
    with caplog.at_level(logging.INFO, logger="frame_gallery.storage"):
        log_storage(layout, FakeClock())
    assert "bucket=state status=ok files=1 bytes=18" in caplog.text
    assert "bucket=scratch status=unavailable" in caplog.text
    assert "sensitive-name" not in caplog.text
    assert "super-secret-value" not in caplog.text
    assert str(tmp_path) not in caplog.text
    assert len(caplog.records) == 6


def test_all_buckets_share_one_time_budget(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = FakeClock()

    def slow(anchor: Path, parts: tuple[str, ...], deadline: Deadline) -> StorageStats:
        clock.advance(1)
        return StorageStats()

    monkeypatch.setattr(diagnostics, "inspect_directory", slow)
    with caplog.at_level(logging.INFO, logger="frame_gallery.storage"):
        log_storage(StoreLayout(tmp_path, tmp_path, tmp_path), clock)
    assert "bucket=state status=ok" in caplog.text
    assert caplog.text.count("status=not_scanned truncated=true") == 5
