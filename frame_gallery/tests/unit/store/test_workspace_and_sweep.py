"""The workspace lifecycle and the startup sweep (store/workspace.py,
store/sweep.py, store/layout.py; §13.1, §14, F1-F3)."""

from __future__ import annotations

import errno
import logging
import os
import stat
from datetime import timedelta
from pathlib import Path

import pytest

from frame_gallery.budget.deadline import Deadline
from frame_gallery.errors import AlreadyRunning, StateError
from frame_gallery.providers.local_media import LIBRARY_ROOT, PREVIEW_ROOT
from frame_gallery.store import atomic, sweep
from frame_gallery.store.atomic import Directory
from frame_gallery.store.layout import StoreLayout
from frame_gallery.store.sweep import StartupSweep, SweepTarget
from frame_gallery.store.workspace import RUN_NAME
from tests.support.clock import FakeClock

RANDOM_PART = "0123456789abcdef"


def names(path: Path) -> list[str]:
    return sorted(entry.name for entry in path.iterdir())


def mode(path: Path) -> int:
    return stat.S_IMODE(path.lstat().st_mode)


@pytest.fixture
def layout(tmp_path: Path) -> StoreLayout:
    for name in ("data", "media", "tmp"):
        (tmp_path / name).mkdir()
    return StoreLayout(data=tmp_path / "data", media=tmp_path / "media", tmp=tmp_path / "tmp")


class TestWorkspace:
    def test_create_makes_a_private_run_directory(self, layout: StoreLayout) -> None:
        workspace = layout.workspace()
        paths = workspace.create()
        assert paths.root.parent == layout.tmp / "frame-gallery"
        assert RUN_NAME.fullmatch(paths.root.name)
        assert paths.inbox == paths.root / "in"
        assert paths.outbox == paths.root / "out"
        for path in (paths.root.parent, paths.root, paths.inbox, paths.outbox):
            assert path.is_dir()
            assert mode(path) == 0o700
        assert workspace.create() == paths  # once per run

    def test_an_existing_root_is_narrowed_to_the_owner(self, layout: StoreLayout) -> None:
        (layout.tmp / "frame-gallery").mkdir(mode=0o755)
        (layout.tmp / "frame-gallery").chmod(0o755)
        layout.workspace().create()
        assert mode(layout.tmp / "frame-gallery") == 0o700

    def test_remove_deletes_everything_the_run_wrote(self, layout: StoreLayout) -> None:
        """F1, F2: downloads and outputs are gone after the run, whatever happened."""
        workspace = layout.workspace()
        paths = workspace.create()
        (paths.inbox / "source-0.bin").write_bytes(b"x" * 1000)
        (paths.outbox / "delivery-0.jpg").write_bytes(b"y" * 1000)
        (paths.outbox / "nested").mkdir()
        (paths.outbox / "nested" / "deep").write_bytes(b"z")
        workspace.remove()
        workspace.remove()  # idempotent
        assert names(layout.tmp / "frame-gallery") == []

    def test_remove_never_follows_a_link_out_of_the_run(
        self, layout: StoreLayout, tmp_path: Path
    ) -> None:
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "keep").write_text("keep")
        workspace = layout.workspace()
        paths = workspace.create()
        (paths.inbox / "link").symlink_to(outside)
        workspace.remove()
        assert (outside / "keep").exists()

    def test_remove_before_create_does_nothing(self, layout: StoreLayout) -> None:
        layout.workspace().remove()
        assert names(layout.tmp) == []

    def test_a_linked_root_is_refused(self, layout: StoreLayout, tmp_path: Path) -> None:
        (tmp_path / "elsewhere").mkdir()
        (layout.tmp / "frame-gallery").symlink_to(tmp_path / "elsewhere")
        with pytest.raises(StateError, match="symbolic link"):
            layout.workspace().create()
        assert names(tmp_path / "elsewhere") == []

    def test_a_root_of_another_user_is_refused(
        self, layout: StoreLayout, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        real_uid = os.geteuid()
        monkeypatch.setattr(os, "geteuid", lambda: real_uid + 1)
        with pytest.raises(StateError, match="belongs to another user"):
            layout.workspace().create()

    def test_a_failed_creation_is_a_state_error(
        self, layout: StoreLayout, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(atomic, "new_token", lambda: RANDOM_PART)
        (layout.tmp / "frame-gallery" / f"run-{RANDOM_PART}").mkdir(parents=True)
        with pytest.raises(StateError, match=r"cannot create the run directory .EEXIST"):
            layout.workspace().create()

    def test_a_failed_removal_only_warns(
        self,
        layout: StoreLayout,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        workspace = layout.workspace()
        workspace.create()

        def failing_remove(_self: Directory, _name: str) -> None:
            raise OSError(errno.EBUSY, "busy")

        monkeypatch.setattr(Directory, "remove", failing_remove)
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            workspace.remove()
        assert "the run directory could not be removed" in caplog.text


class TestSweep:
    def seed(self, layout: StoreLayout, tmp_path: Path) -> None:
        """Leftovers of a killed run, and things the sweep must leave alone."""
        state = layout.data / "state"
        for directory in (state, layout.data / "cache", layout.data / "tv"):
            directory.mkdir(parents=True)
            (directory / f"x.json.tmp-{RANDOM_PART}").write_text("leftover")
            (directory / f"x.json.bak.tmp-{RANDOM_PART}").write_text("leftover")
        (state / "history.json").write_text("{}")
        (state / "history.json.tmp-123").write_text("not ours: wrong token")
        (state / f".x.tmp-{RANDOM_PART}").write_text("not ours: hidden")
        (state / f"link.tmp-{RANDOM_PART}").symlink_to(tmp_path / "target")
        (state / f"dir.tmp-{RANDOM_PART}").mkdir()
        preview = layout.media / "frame_gallery" / "preview"
        preview.mkdir(parents=True)
        (preview / "latest.jpg").write_bytes(b"jpeg")
        (preview / f"latest.jpg.tmp-{RANDOM_PART}").write_bytes(b"partial")
        runs = layout.tmp / "frame-gallery"
        (runs / f"run-{RANDOM_PART}" / "in").mkdir(parents=True)
        (runs / f"run-{RANDOM_PART}" / "in" / "source-0.bin").write_bytes(b"x")
        (runs / "run-other").mkdir()
        (runs / f"run-{RANDOM_PART[::-1]}").write_text("a file, not a run directory")
        (runs / f"run-{RANDOM_PART[1:]}0").symlink_to(tmp_path / "outside")

    def test_leftovers_are_removed_and_nothing_else(
        self, layout: StoreLayout, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        (tmp_path / "outside").mkdir()
        self.seed(layout, tmp_path)
        with caplog.at_level(logging.INFO, "frame_gallery.store"):
            assert layout.startup_sweep()() == 8
        assert "removed 8 leftovers of earlier runs" in caplog.text
        assert names(layout.data / "state") == [
            f".x.tmp-{RANDOM_PART}",
            f"dir.tmp-{RANDOM_PART}",
            "history.json",
            "history.json.tmp-123",
            f"link.tmp-{RANDOM_PART}",
        ]
        assert names(layout.data / "cache") == []
        assert names(layout.data / "tv") == []
        assert names(layout.media / "frame_gallery" / "preview") == ["latest.jpg"]
        assert names(layout.tmp / "frame-gallery") == [
            f"run-{RANDOM_PART[1:]}0",
            f"run-{RANDOM_PART[::-1]}",
            "run-other",
        ]

    def test_a_fresh_installation_has_nothing_to_sweep(
        self, layout: StoreLayout, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.INFO, "frame_gallery.store"):
            assert layout.startup_sweep()() == 0
        assert caplog.text == ""

    def test_the_scan_is_bounded(
        self, layout: StoreLayout, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(sweep, "SCAN_LIMIT", 2)
        cache = layout.data / "cache"
        cache.mkdir()
        for index in range(5):
            (cache / f"f{index}.tmp-{RANDOM_PART}").write_text("x")
        target = SweepTarget(layout.data, ("cache",))
        StartupSweep(temporary_files=[target], run_directories=target)()
        assert len(names(cache)) == 3

    def test_an_unlistable_directory_is_reported(
        self,
        layout: StoreLayout,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        (layout.data / "state").mkdir()

        def failing_names(_self: Directory, _limit: int) -> list[str]:
            raise OSError(errno.EIO, "io")

        monkeypatch.setattr(Directory, "names", failing_names)
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            assert layout.startup_sweep()() == 0
        assert "could not be swept (EIO)" in caplog.text

    def test_an_entry_that_cannot_be_removed_is_reported(
        self,
        layout: StoreLayout,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        (layout.data / "state").mkdir()
        (layout.data / "state" / f"x.tmp-{RANDOM_PART}").write_text("x")

        def failing_remove(_self: Directory, _name: str) -> None:
            raise OSError(errno.EPERM, "denied")

        monkeypatch.setattr(Directory, "remove", failing_remove)
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            assert layout.startup_sweep()() == 0
        assert f"x.tmp-{RANDOM_PART} was not removed (EPERM)" in caplog.text

    def test_the_state_store_sweeps_only_after_taking_the_lock(
        self, layout: StoreLayout, tmp_path: Path
    ) -> None:
        (tmp_path / "outside").mkdir()
        self.seed(layout, tmp_path)
        clock = FakeClock()
        holder = layout.state_store(clock)
        holder.open(Deadline.after(clock, 10, "configure"))
        leftover = layout.data / "cache" / f"late.tmp-{RANDOM_PART}"
        leftover.write_text("written by the running holder")
        contender = layout.state_store(clock)
        with pytest.raises(AlreadyRunning):
            contender.open(Deadline.after(clock, 10, "configure"))
        assert leftover.exists()  # the loser swept nothing
        holder.close()
        contender.close()


class TestLayout:
    def test_the_metadata_cache_lives_below_data(self, layout: StoreLayout) -> None:
        cache = layout.metadata_cache("aic", FakeClock())
        cache.put_count("aic:count:any", 1, timedelta(days=1))
        cache.flush(Deadline.after(FakeClock(), 5, "finish"))
        assert names(layout.data / "cache") == ["aic.json"]

    def test_the_production_layout(self) -> None:
        layout = StoreLayout()
        assert layout.data == Path("/data")
        assert layout.tmp == Path("/tmp")  # noqa: S108 - the documented location
        assert layout.media / "frame_gallery" / "preview" == PREVIEW_ROOT
        assert PREVIEW_ROOT.parent == LIBRARY_ROOT.parent
