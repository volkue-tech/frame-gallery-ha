"""The file-backed state store (store/state.py, §13, D-137)."""

from __future__ import annotations

import errno
import fcntl
import json
import logging
import os
from collections.abc import Iterator
from datetime import timedelta
from pathlib import Path

import pytest

from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.errors import AlreadyRunning, StateError
from frame_gallery.selection.exclusion import ExclusionSet
from frame_gallery.store.atomic import CommitError, Directory, Staged
from frame_gallery.store.state import FileStateStore
from tests.support.clock import FakeClock


class Stores:
    """Opens stores over one data root, as successive runs would."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.clock = FakeClock()
        self.opened: list[FileStateStore] = []
        self.sweeps = 0

    def sweep(self) -> None:
        self.sweeps += 1

    def open(self) -> FileStateStore:
        store = FileStateStore(self.root, clock=self.clock, sweep=self.sweep)
        self.opened.append(store)
        store.open(Deadline.after(self.clock, 10, "configure"))
        return store

    @property
    def state(self) -> Path:
        return self.root / "state"

    def ledger(self) -> list[dict[str, object]]:
        entries = json.loads((self.state / "upload_ledger.json").read_text())["entries"]
        assert isinstance(entries, list)
        return entries

    def history_ids(self) -> list[str]:
        document = json.loads((self.state / "history.json").read_text())
        return [entry["id"] for entry in document["entries"]]

    def close_all(self) -> None:
        for store in self.opened:
            store.close()


@pytest.fixture
def stores(tmp_path: Path) -> Iterator[Stores]:
    opened = Stores(tmp_path / "data")
    (tmp_path / "data").mkdir()
    yield opened
    opened.close_all()


def names(path: Path) -> list[str]:
    return sorted(entry.name for entry in path.iterdir())


def run_delivery(store: FileStateStore, qualified_id: str, clock: FakeClock) -> None:
    """The store calls of a delivered run, in the runner's order."""
    now = clock.utc_now()
    store.load_exclusions(now)
    store.prestage_history(qualified_id, now)
    store.commit_upload_intent(qualified_id, now)
    store.promote_upload(qualified_id, now)
    store.record_history()


class TestOpen:
    def test_open_creates_the_private_directory_and_sweeps_after_locking(
        self, stores: Stores
    ) -> None:
        stores.open()
        assert stores.state.is_dir()
        assert oct(stores.state.stat().st_mode & 0o777) == "0o700"
        assert (stores.state / ".lock").exists()
        assert stores.sweeps == 1

    def test_a_store_without_a_sweep_opens(self, stores: Stores) -> None:
        store = FileStateStore(stores.root, clock=stores.clock)
        stores.opened.append(store)
        store.open(Deadline.after(stores.clock, 10, "configure"))
        assert store.load_exclusions(stores.clock.utc_now()) == ExclusionSet()

    def test_a_second_run_is_already_running(self, stores: Stores) -> None:
        stores.open()
        with pytest.raises(AlreadyRunning):
            stores.open()
        assert stores.sweeps == 1  # the loser never sweeps

    def test_the_loser_closes_its_lock_descriptor(self, stores: Stores) -> None:
        stores.open()
        before = len(os.listdir("/dev/fd"))  # noqa: PTH208 - counts open descriptors
        for _ in range(3):
            with pytest.raises(AlreadyRunning):
                stores.open()
            stores.opened.pop().close()
        assert len(os.listdir("/dev/fd")) == before  # noqa: PTH208

    def test_the_lock_is_released_on_close(self, stores: Stores) -> None:
        first = stores.open()
        first.close()
        first.close()  # idempotent
        stores.open()

    def test_an_expired_deadline_stops_before_anything(self, stores: Stores) -> None:
        store = FileStateStore(stores.root, clock=stores.clock)
        with pytest.raises(DeadlineExceeded):
            store.open(Deadline.after(stores.clock, 0, "configure"))
        assert not stores.state.exists()

    def test_a_linked_state_directory_is_refused(self, stores: Stores, tmp_path: Path) -> None:
        (tmp_path / "elsewhere").mkdir()
        stores.state.symlink_to(tmp_path / "elsewhere")
        with pytest.raises(StateError, match="symbolic link"):
            stores.open()

    def test_a_linked_lock_is_refused(self, stores: Stores, tmp_path: Path) -> None:
        stores.state.mkdir()
        (stores.state / ".lock").symlink_to(tmp_path / "target")
        with pytest.raises(StateError, match="cannot open the lock"):
            stores.open()
        assert not (tmp_path / "target").exists()

    def test_a_failing_lock_is_a_state_error(
        self, stores: Stores, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def failing_flock(_fd: int, _operation: int) -> None:
            raise OSError(errno.ENOLCK, "no locks")

        monkeypatch.setattr(fcntl, "flock", failing_flock)
        with pytest.raises(StateError, match=r"cannot take the lock .ENOLCK"):
            stores.open()

    def test_a_failing_sweep_only_warns(
        self, stores: Stores, caplog: pytest.LogCaptureFixture
    ) -> None:
        def broken() -> None:
            raise RuntimeError("sweep bug")

        store = FileStateStore(stores.root, clock=stores.clock, sweep=broken)
        stores.opened.append(store)
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            store.open(Deadline.after(stores.clock, 10, "configure"))
        assert "the startup sweep failed" in caplog.text

    def test_a_store_that_is_not_open_refuses_to_work(self, stores: Stores) -> None:
        store = FileStateStore(stores.root, clock=stores.clock)
        with pytest.raises(StateError, match="not open"):
            store.load_exclusions(stores.clock.utc_now())


class TestDelivery:
    def test_a_delivered_run_records_history_and_the_upload(self, stores: Stores) -> None:
        store = stores.open()
        run_delivery(store, "aic:1", stores.clock)
        assert stores.history_ids() == ["aic:1"]
        assert [e["state"] for e in stores.ledger()] == ["uploaded"]
        assert names(stores.state) == [
            ".lock",
            "history.json",
            "upload_ledger.json",
            "upload_ledger.json.bak",
        ]

    def test_the_next_run_excludes_the_work(self, stores: Stores) -> None:
        """E4-E6: exactly one identifier in history; never resent."""
        first = stores.open()
        run_delivery(first, "aic:1", stores.clock)
        first.close()
        second = stores.open()
        exclusions = second.load_exclusions(stores.clock.utc_now())
        expected = ExclusionSet(history=frozenset({"aic:1"}), uploaded=frozenset({"aic:1"}))
        assert exclusions == expected

    def test_the_ledger_prunes_a_work_once_both_history_copies_hold_it(
        self, stores: Stores
    ) -> None:
        for number in (1, 2):
            store = stores.open()
            run_delivery(store, f"aic:{number}", stores.clock)
            store.close()
        # history.json holds aic:1 and aic:2; history.json.bak holds only aic:1.
        third = stores.open()
        third.load_exclusions(stores.clock.utc_now())
        third.commit_upload_intent("aic:3", stores.clock.utc_now())
        assert [(e["id"], e["state"]) for e in stores.ledger()] == [
            ("aic:2", "uploaded"),
            ("aic:3", "uncertain"),
        ]

    def test_a_damaged_history_never_loses_the_newest_delivery(self, stores: Stores) -> None:
        """Review finding: a run whose television was off prunes the ledger;
        a damaged primary then falls back to a .bak that is one generation old."""
        for number in (1, 2):
            store = stores.open()
            run_delivery(store, f"aic:{number}", stores.clock)
            store.close()
        third = stores.open()  # the television is unreachable: no record
        third.load_exclusions(stores.clock.utc_now())
        third.prestage_history("aic:3", stores.clock.utc_now())
        third.commit_upload_intent("aic:3", stores.clock.utc_now())
        third.discard_prestaged_history()
        third.remove_upload_intent("aic:3")
        third.close()
        (stores.state / "history.json").write_bytes(b"{damaged")
        fourth = stores.open()
        exclusions = fourth.load_exclusions(stores.clock.utc_now())
        assert exclusions.history == {"aic:1"}
        assert "aic:2" in exclusions

    def test_history_changes_only_on_record(self, stores: Stores) -> None:
        """E10: pre-staging leaves the visible history untouched."""
        store = stores.open()
        run_delivery(store, "aic:1", stores.clock)
        before = (stores.state / "history.json").read_bytes()
        store.prestage_history("aic:2", stores.clock.utc_now())
        assert (stores.state / "history.json").read_bytes() == before
        store.discard_prestaged_history()
        assert not [n for n in names(stores.state) if ".tmp-" in n]

    def test_record_without_prestage_is_an_error(self, stores: Stores) -> None:
        store = stores.open()
        store.load_exclusions(stores.clock.utc_now())
        with pytest.raises(StateError, match="no history generation was pre-staged"):
            store.record_history()

    def test_a_second_prestage_replaces_the_first(self, stores: Stores) -> None:
        store = stores.open()
        store.prestage_history("aic:1", stores.clock.utc_now())
        store.prestage_history("aic:2", stores.clock.utc_now())
        assert len([n for n in names(stores.state) if ".tmp-" in n]) == 1
        store.record_history()
        assert stores.history_ids() == ["aic:2"]

    def test_close_discards_a_leftover_prestaged_file(self, stores: Stores) -> None:
        store = stores.open()
        store.prestage_history("aic:1", stores.clock.utc_now())
        store.close()
        assert not [n for n in names(stores.state) if ".tmp-" in n]

    def test_a_failed_rename_leaves_history_unrecorded(
        self, stores: Stores, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = stores.open()
        store.prestage_history("aic:1", stores.clock.utc_now())
        real_rename = os.rename

        def failing_rename(
            src: str, dst: str, *, src_dir_fd: int | None = None, dst_dir_fd: int | None = None
        ) -> None:
            if dst == "history.json":
                raise OSError(errno.EIO, "io")
            real_rename(src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd)

        monkeypatch.setattr(os, "rename", failing_rename)
        with pytest.raises(StateError, match="cannot replace"):
            store.record_history()
        assert not (stores.state / "history.json").exists()

    def test_a_failed_flush_after_the_rename_counts_as_recorded(
        self,
        stores: Stores,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        store = stores.open()
        store.prestage_history("aic:1", stores.clock.utc_now())
        real_commit = Directory.commit

        def commit(directory: Directory, staged: Staged, *, refresh_backup: bool) -> None:
            real_commit(directory, staged, refresh_backup=refresh_backup)
            raise CommitError("flush failed", replaced=True)

        monkeypatch.setattr(Directory, "commit", commit)
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            store.record_history()
        assert "may not be durable yet" in caplog.text
        assert stores.history_ids() == ["aic:1"]
        monkeypatch.undo()
        assert store.load_exclusions(stores.clock.utc_now()).history == {"aic:1"}


class TestLedger:
    def test_an_intent_excludes_for_thirty_days(self, stores: Stores) -> None:
        """E9: a killed run's intent quarantines the work on the next runs."""
        first = stores.open()
        first.load_exclusions(stores.clock.utc_now())
        first.commit_upload_intent("cma:7", stores.clock.utc_now())
        first.close()  # the process died without classifying the run
        second = stores.open()
        assert "cma:7" in second.load_exclusions(stores.clock.utc_now())
        second.close()
        stores.clock.advance(timedelta(days=30).total_seconds())
        third = stores.open()
        assert "cma:7" not in third.load_exclusions(stores.clock.utc_now())
        third.commit_upload_intent("cma:8", stores.clock.utc_now())
        assert [e["id"] for e in stores.ledger()] == ["cma:8"]

    def test_removal_and_promotion(self, stores: Stores) -> None:
        store = stores.open()
        now = stores.clock.utc_now()
        store.load_exclusions(now)
        store.commit_upload_intent("cma:1", now)
        store.remove_upload_intent("cma:1")
        assert stores.ledger() == []
        store.commit_upload_intent("cma:2", now)
        store.promote_upload("cma:2", now)
        store.remove_upload_intent("cma:2")  # an upload is never removed
        assert [(e["id"], e["state"]) for e in stores.ledger()] == [("cma:2", "uploaded")]

    def test_removing_nothing_writes_nothing(self, stores: Stores) -> None:
        store = stores.open()
        store.load_exclusions(stores.clock.utc_now())
        store.remove_upload_intent("cma:1")
        assert not (stores.state / "upload_ledger.json").exists()

    def test_a_failed_intent_leaves_nothing_behind(
        self, stores: Stores, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = stores.open()
        store.load_exclusions(stores.clock.utc_now())

        def full(*_args: object, **_kwargs: object) -> int:
            raise OSError(errno.ENOSPC, "full")

        monkeypatch.setattr(os, "write", full)
        with pytest.raises(StateError, match="ENOSPC"):
            store.commit_upload_intent("cma:1", stores.clock.utc_now())
        monkeypatch.undo()
        assert "cma:1" not in store.load_exclusions(stores.clock.utc_now())
        store.remove_upload_intent("cma:1")  # nothing to remove, nothing written
        assert not (stores.state / "upload_ledger.json").exists()

    def test_an_intent_that_may_not_be_durable_is_an_error_but_kept_in_memory(
        self, stores: Stores, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = stores.open()
        store.load_exclusions(stores.clock.utc_now())
        real_commit = Directory.commit

        def commit(directory: Directory, staged: Staged, *, refresh_backup: bool) -> None:
            real_commit(directory, staged, refresh_backup=refresh_backup)
            raise CommitError("flush failed", replaced=True)

        monkeypatch.setattr(Directory, "commit", commit)
        with pytest.raises(StateError, match="flush failed"):
            store.commit_upload_intent("cma:1", stores.clock.utc_now())
        monkeypatch.undo()
        # The runner then removes the intent: the file holds it, so it is written.
        store.remove_upload_intent("cma:1")
        assert stores.ledger() == []

    def test_a_ledger_that_was_not_replaced_keeps_the_previous_entries(
        self, stores: Stores, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = stores.open()
        now = stores.clock.utc_now()
        store.load_exclusions(now)
        store.commit_upload_intent("cma:1", now)
        real_rename = os.rename

        def failing_rename(
            src: str, dst: str, *, src_dir_fd: int | None = None, dst_dir_fd: int | None = None
        ) -> None:
            if dst == "upload_ledger.json":
                raise OSError(errno.EIO, "io")
            real_rename(src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd)

        monkeypatch.setattr(os, "rename", failing_rename)
        with pytest.raises(StateError, match="cannot replace"):
            store.promote_upload("cma:1", now)
        monkeypatch.undo()
        # Memory still says uncertain, so a removal is written and takes it.
        store.remove_upload_intent("cma:1")
        assert stores.ledger() == []

    def test_a_failed_promotion_keeps_the_intent(
        self, stores: Stores, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = stores.open()
        now = stores.clock.utc_now()
        store.load_exclusions(now)
        store.commit_upload_intent("cma:1", now)

        def failing_fsync(_fd: int) -> None:
            raise OSError(errno.EIO, "io")

        monkeypatch.setattr(os, "fsync", failing_fsync)
        with pytest.raises(StateError):
            store.promote_upload("cma:1", now)
        monkeypatch.undo()
        assert [(e["id"], e["state"]) for e in stores.ledger()] == [("cma:1", "uncertain")]


class TestCorruptionAndVersions:
    def test_a_newer_history_is_a_state_error_and_left_alone(self, stores: Stores) -> None:
        stores.state.mkdir()
        content = json.dumps({"format": "frame-gallery-history", "version": 2, "entries": []})
        (stores.state / "history.json").write_text(content)
        store = stores.open()
        with pytest.raises(StateError, match=r"newer version .2."):
            store.load_exclusions(stores.clock.utc_now())
        assert (stores.state / "history.json").read_text() == content

    def test_a_newer_ledger_is_a_state_error(self, stores: Stores) -> None:
        stores.state.mkdir()
        content = json.dumps({"format": "frame-gallery-upload-ledger", "version": 5, "entries": []})
        (stores.state / "upload_ledger.json").write_text(content)
        store = stores.open()
        with pytest.raises(StateError, match=r"upload_ledger\.json was written by a newer version"):
            store.load_exclusions(stores.clock.utc_now())
        with pytest.raises(StateError):
            store.prestage_history("aic:1", stores.clock.utc_now())

    def test_an_unreadable_history_is_a_state_error(
        self, stores: Stores, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = stores.open()
        (stores.state / "history.json").write_text("{}")
        real_open = os.open

        def denied(path: str, flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
            if path == "history.json":
                raise PermissionError(errno.EACCES, "denied")
            return real_open(path, flags, mode, dir_fd=dir_fd)

        monkeypatch.setattr(os, "open", denied)
        with pytest.raises(StateError, match="exists but cannot be read"):
            store.load_exclusions(stores.clock.utc_now())

    def test_a_corrupt_history_is_recovered_from_the_backup(self, stores: Stores) -> None:
        """F5: quarantined and recovered, without a crash."""
        first = stores.open()
        run_delivery(first, "aic:1", stores.clock)
        first.close()
        second = stores.open()
        run_delivery(second, "aic:2", stores.clock)
        second.close()
        (stores.state / "history.json").write_bytes(b"\x00\x01garbage")
        third = stores.open()
        exclusions = third.load_exclusions(stores.clock.utc_now())
        # The backup is one generation old; the ledger keeps the newest work
        # until both copies of history hold it.
        assert exclusions.history == {"aic:1"}
        assert "aic:2" in exclusions
        assert len(names(stores.state / "quarantine")) == 1

    @pytest.mark.parametrize(
        ("name", "document"),
        [
            (
                "history.json",
                {
                    "format": "frame-gallery-history",
                    "version": 1,
                    "entries": [{"id": "aic:1", "at": "0001-01-01T00:00:00+05:00"}],
                },
            ),
            (
                "upload_ledger.json",
                {
                    "format": "frame-gallery-upload-ledger",
                    "version": 1,
                    "entries": [
                        {"id": "aic:1", "state": "uncertain", "at": "9999-12-31T00:00:00+00:00"}
                    ],
                },
            ),
        ],
    )
    def test_a_timestamp_at_the_limits_is_damage_not_a_crash(
        self, stores: Stores, name: str, document: dict[str, object]
    ) -> None:
        """Review finding: these once raised OverflowError on every run."""
        stores.state.mkdir()
        (stores.state / name).write_text(json.dumps(document))
        store = stores.open()
        assert store.load_exclusions(stores.clock.utc_now()) == ExclusionSet()
        store.commit_upload_intent("aic:2", stores.clock.utc_now())
        assert len(names(stores.state / "quarantine")) == 1

    def test_a_corrupt_ledger_without_backup_starts_empty(self, stores: Stores) -> None:
        stores.state.mkdir()
        (stores.state / "upload_ledger.json").write_text("[]")
        store = stores.open()
        assert store.load_exclusions(stores.clock.utc_now()) == ExclusionSet()


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores directory permissions")
def test_a_read_only_state_directory_fails_before_the_television(stores: Stores) -> None:
    """A read-only /data gives state_error while the TV is still untouched."""
    store = stores.open()
    store.load_exclusions(stores.clock.utc_now())
    stores.state.chmod(0o500)
    try:
        with pytest.raises(StateError, match="EACCES"):
            store.prestage_history("aic:1", stores.clock.utc_now())
        with pytest.raises(StateError, match="EACCES"):
            store.commit_upload_intent("aic:1", stores.clock.utc_now())
    finally:
        stores.state.chmod(0o700)
