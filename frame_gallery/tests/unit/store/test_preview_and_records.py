"""Preview publication and the run records (store/preview.py,
store/records.py; §13.1, §13.5, D8, F7)."""

from __future__ import annotations

import errno
import hashlib
import json
import logging
import os
import stat
from datetime import UTC, datetime
from pathlib import Path

import pytest

from frame_gallery.app.outcomes import Outcome
from frame_gallery.app.records import (
    AttemptNote,
    RunStats,
    build_current_record,
    build_last_run_record,
)
from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.domain import CANVAS
from frame_gallery.errors import PublishError, StateError
from frame_gallery.fingerprint import fingerprint_bytes
from frame_gallery.imaging.contract import DeliveryArtifact
from frame_gallery.providers.contract import Attribution
from frame_gallery.store.atomic import CommitError, Directory, ReadFailure, Staged
from frame_gallery.store.layout import StoreLayout
from frame_gallery.store.records import (
    MAX_FINGERPRINTS,
    MAX_RECORD_BYTES,
    merged_fingerprints,
    parse_current,
    parse_last_run,
)
from tests.support.clock import FakeClock
from tests.support.fakes import canvas_jpeg_bytes

T0 = datetime(2026, 9, 27, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def layout(tmp_path: Path) -> StoreLayout:
    for name in ("data", "media", "tmp"):
        (tmp_path / name).mkdir()
    return StoreLayout(data=tmp_path / "data", media=tmp_path / "media", tmp=tmp_path / "tmp")


def artifact_for(path: Path, data: bytes) -> DeliveryArtifact:
    path.write_bytes(data)
    return DeliveryArtifact(
        path=path,
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
        dims=CANVAS,
        fingerprint=fingerprint_bytes(data),
    )


def deadline(seconds: float = 5) -> Deadline:
    return Deadline.after(FakeClock(), seconds, "publish")


def preview_dir(layout: StoreLayout) -> Path:
    return layout.media / "frame_gallery" / "preview"


class TestPreview:
    def test_the_preview_is_exactly_the_delivery(self, layout: StoreLayout, tmp_path: Path) -> None:
        """D8: the preview bytes are the television payload."""
        data = canvas_jpeg_bytes()
        layout.preview().publish(artifact_for(tmp_path / "delivery.jpg", data), deadline())
        published = preview_dir(layout) / "latest.jpg"
        assert published.read_bytes() == data
        assert stat.S_IMODE(published.stat().st_mode) == 0o644
        assert stat.S_IMODE(preview_dir(layout).stat().st_mode) == 0o755
        assert sorted(p.name for p in preview_dir(layout).iterdir()) == ["latest.jpg"]

    def test_every_name_receives_the_same_bytes(self, layout: StoreLayout, tmp_path: Path) -> None:
        store = layout.preview(("preview_a.jpg", "preview_b.jpg"))
        store.publish(artifact_for(tmp_path / "one.jpg", b"first"), deadline())
        store.publish(artifact_for(tmp_path / "two.jpg", b"second"), deadline())
        for name in ("preview_a.jpg", "preview_b.jpg"):
            assert (preview_dir(layout) / name).read_bytes() == b"second"

    def test_a_name_that_cannot_be_staged_leaves_every_name_unchanged(
        self, layout: StoreLayout, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Review finding: with two names, nothing is renamed until both are
        written and verified."""
        store = layout.preview(("preview_a.jpg", "preview_b.jpg"))
        store.publish(artifact_for(tmp_path / "old.jpg", b"old"), deadline())
        real_stage = Directory.stage

        def stage(directory: Directory, name: str, data: bytes, *, mode: int = 0o600) -> Staged:
            if name == "preview_b.jpg":
                raise StateError("injected: full")
            return real_stage(directory, name, data, mode=mode)

        monkeypatch.setattr(Directory, "stage", stage)
        with pytest.raises(PublishError, match="injected"):
            store.publish(artifact_for(tmp_path / "new.jpg", b"new"), deadline())
        monkeypatch.undo()
        for name in ("preview_a.jpg", "preview_b.jpg"):
            assert (preview_dir(layout) / name).read_bytes() == b"old"
        assert sorted(p.name for p in preview_dir(layout).iterdir()) == [
            "preview_a.jpg",
            "preview_b.jpg",
        ]

    def test_no_name_is_renamed_when_time_runs_out(
        self, layout: StoreLayout, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = layout.preview(("preview_a.jpg", "preview_b.jpg"))
        store.publish(artifact_for(tmp_path / "old.jpg", b"old"), deadline())
        clock = FakeClock()
        limit = Deadline.after(clock, 5, "publish")
        real_stage = Directory.stage

        def slow_stage(
            directory: Directory, name: str, data: bytes, *, mode: int = 0o600
        ) -> Staged:
            staged = real_stage(directory, name, data, mode=mode)
            clock.advance(3)
            return staged

        monkeypatch.setattr(Directory, "stage", slow_stage)
        with pytest.raises(DeadlineExceeded):
            store.publish(artifact_for(tmp_path / "new.jpg", b"new"), limit)
        monkeypatch.undo()
        assert (preview_dir(layout) / "preview_a.jpg").read_bytes() == b"old"
        assert (preview_dir(layout) / "preview_b.jpg").read_bytes() == b"old"
        assert len(list(preview_dir(layout).iterdir())) == 2

    def test_a_rename_failing_between_the_names_is_reported(
        self, layout: StoreLayout, tmp_path: Path
    ) -> None:
        """The one remaining window (D-158): the run reports it."""
        store = layout.preview(("preview_a.jpg", "preview_b.jpg"))
        store.publish(artifact_for(tmp_path / "old.jpg", b"old"), deadline())
        (preview_dir(layout) / "preview_b.jpg").unlink()
        (preview_dir(layout) / "preview_b.jpg").mkdir()
        (preview_dir(layout) / "preview_b.jpg" / "child").write_text("x")
        with pytest.raises(PublishError, match="cannot replace"):
            store.publish(artifact_for(tmp_path / "new.jpg", b"new"), deadline())
        assert (preview_dir(layout) / "preview_a.jpg").read_bytes() == b"new"
        assert sorted(p.name for p in preview_dir(layout).iterdir()) == [
            "preview_a.jpg",
            "preview_b.jpg",
        ]

    def test_names_are_checked(self, layout: StoreLayout) -> None:
        with pytest.raises(ValueError, match="at least one"):
            layout.preview(())
        with pytest.raises(ValueError, match="invalid file name"):
            layout.preview(("../escape.jpg",))

    def test_an_unavailable_media_folder_is_a_publish_error(
        self, layout: StoreLayout, tmp_path: Path
    ) -> None:
        layout.media.rmdir()
        with pytest.raises(PublishError, match="cannot open"):
            layout.preview().publish(artifact_for(tmp_path / "d.jpg", b"x"), deadline())

    @pytest.mark.parametrize("linked", ["frame_gallery", "frame_gallery/preview"])
    def test_a_linked_component_is_refused(
        self, layout: StoreLayout, tmp_path: Path, linked: str
    ) -> None:
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        target = layout.media / linked
        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(elsewhere)
        with pytest.raises(PublishError, match="symbolic link"):
            layout.preview().publish(artifact_for(tmp_path / "d.jpg", b"x"), deadline())
        assert list(elsewhere.iterdir()) == []

    def test_a_changed_delivery_file_is_refused(self, layout: StoreLayout, tmp_path: Path) -> None:
        layout.preview().publish(artifact_for(tmp_path / "old.jpg", b"old"), deadline())
        artifact = artifact_for(tmp_path / "d.jpg", b"validated")
        (tmp_path / "d.jpg").write_bytes(b"tampered!")
        with pytest.raises(PublishError, match="changed since it was validated"):
            layout.preview().publish(artifact, deadline())
        (tmp_path / "d.jpg").write_bytes(b"short")
        with pytest.raises(PublishError, match="changed since it was validated"):
            layout.preview().publish(artifact, deadline())
        assert (preview_dir(layout) / "latest.jpg").read_bytes() == b"old"

    def test_a_missing_or_linked_delivery_file_is_refused(
        self, layout: StoreLayout, tmp_path: Path
    ) -> None:
        artifact = artifact_for(tmp_path / "d.jpg", b"x")
        (tmp_path / "d.jpg").unlink()
        with pytest.raises(PublishError, match="missing"):
            layout.preview().publish(artifact, deadline())
        (tmp_path / "real.jpg").write_bytes(b"x")
        (tmp_path / "d.jpg").symlink_to(tmp_path / "real.jpg")
        with pytest.raises(PublishError, match="not a regular file"):
            layout.preview().publish(artifact, deadline())

    def test_a_written_preview_that_does_not_read_back_is_discarded(
        self, layout: StoreLayout, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        layout.preview().publish(artifact_for(tmp_path / "old.jpg", b"old"), deadline())
        real_read = Directory.read_bytes

        def corrupted(directory: Directory, name: str, max_bytes: int) -> bytes | ReadFailure:
            if ".tmp-" in name:
                return b"bit flip"
            return real_read(directory, name, max_bytes)

        monkeypatch.setattr(Directory, "read_bytes", corrupted)
        with pytest.raises(PublishError, match="does not match"):
            layout.preview().publish(artifact_for(tmp_path / "d.jpg", b"new"), deadline())
        assert sorted(p.name for p in preview_dir(layout).iterdir()) == ["latest.jpg"]
        assert (preview_dir(layout) / "latest.jpg").read_bytes() == b"old"

    def test_a_full_media_folder_is_a_publish_error(
        self, layout: StoreLayout, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        artifact = artifact_for(tmp_path / "d.jpg", b"x")

        def full(_fd: int, _data: object) -> int:
            raise OSError(errno.ENOSPC, "full")

        monkeypatch.setattr(os, "write", full)
        with pytest.raises(PublishError, match="ENOSPC"):
            layout.preview().publish(artifact, deadline())

    def test_a_failed_replacement_is_a_publish_error(
        self, layout: StoreLayout, tmp_path: Path
    ) -> None:
        (preview_dir(layout) / "latest.jpg").mkdir(parents=True)
        (preview_dir(layout) / "latest.jpg" / "child").write_text("x")
        with pytest.raises(PublishError, match="cannot replace"):
            layout.preview().publish(artifact_for(tmp_path / "d.jpg", b"x"), deadline())

    def test_a_replacement_that_may_not_be_durable_only_warns(
        self,
        layout: StoreLayout,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        real_commit = Directory.commit

        def commit(directory: Directory, staged: Staged, *, refresh_backup: bool) -> None:
            real_commit(directory, staged, refresh_backup=refresh_backup)
            raise CommitError("flush failed", replaced=True)

        monkeypatch.setattr(Directory, "commit", commit)
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            layout.preview().publish(artifact_for(tmp_path / "d.jpg", b"x"), deadline())
        assert "may not be durable yet" in caplog.text
        assert (preview_dir(layout) / "latest.jpg").read_bytes() == b"x"

    def test_an_expired_deadline_publishes_nothing(
        self, layout: StoreLayout, tmp_path: Path
    ) -> None:
        with pytest.raises(DeadlineExceeded):
            layout.preview().publish(artifact_for(tmp_path / "d.jpg", b"x"), deadline(0))
        assert not preview_dir(layout).exists()


def current_record(number: int, *, fingerprint: str | None = None) -> dict[str, object]:
    return build_current_record(
        qualified_id=f"aic:{number}",
        attribution=Attribution(title=f"Work {number}"),
        sha256=hashlib.sha256(str(number).encode()).hexdigest(),
        delivered_at=T0,
        preview_fingerprint=fingerprint or hashlib.sha256(f"fp{number}".encode()).hexdigest(),
    )


def last_run_record(**changes: object) -> dict[str, object]:
    record = build_last_run_record(
        outcome=Outcome.NO_MATCH,
        hint="nothing new left for these filters",
        started_at=T0,
        finished_at=T0,
        elapsed_s=1.5,
        filters=None,
        stats=RunStats(),
        artwork_id=None,
    )
    record.update(changes)
    return record


class TestRecords:
    def test_the_last_ten_preview_fingerprints_are_kept_newest_first(
        self, layout: StoreLayout
    ) -> None:
        records = layout.records(FakeClock())
        for number in range(12):
            records.write_current(current_record(number), deadline())
        records.write_current(current_record(99, fingerprint=_fp(11)), deadline())  # a repeat
        expected = [_fp(n) for n in range(11, 1, -1)]
        assert list(records.preview_fingerprints()) == expected
        document = json.loads((layout.data / "state" / "current.json").read_text())
        assert document["id"] == "aic:99"
        assert document["preview_fingerprints"] == expected

    def test_there_are_no_fingerprints_before_the_first_delivery(self, layout: StoreLayout) -> None:
        assert layout.records(FakeClock()).preview_fingerprints() == ()

    def test_invalid_fingerprints_are_refused(self, layout: StoreLayout) -> None:
        record = current_record(1)
        record["preview_fingerprints"] = ["not hex"]
        with pytest.raises(StateError, match="invalid preview fingerprint"):
            layout.records(FakeClock()).write_current(record, deadline())

    def test_a_damaged_current_record_is_quarantined(
        self, layout: StoreLayout, caplog: pytest.LogCaptureFixture
    ) -> None:
        records = layout.records(FakeClock())
        records.write_current(current_record(1), deadline())
        (layout.data / "state" / "current.json").write_text("{damaged")
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            assert records.preview_fingerprints() == ()
        assert "is damaged" in caplog.text
        assert len(list((layout.data / "state" / "quarantine").iterdir())) == 1
        records.write_current(current_record(2), deadline())
        assert records.preview_fingerprints() == (_fp(2),)

    def test_the_last_run_record_is_written(self, layout: StoreLayout) -> None:
        layout.records(FakeClock()).write_last_run(last_run_record(), deadline())
        document = json.loads((layout.data / "state" / "last_run.json").read_text())
        assert document["outcome"] == "no_match"
        assert oct((layout.data / "state" / "last_run.json").stat().st_mode & 0o777) == "0o600"

    def test_records_over_16_kib_are_refused(self, layout: StoreLayout) -> None:
        with pytest.raises(StateError, match="exceeds 16384 bytes"):
            layout.records(FakeClock()).write_last_run(
                last_run_record(hint="x" * MAX_RECORD_BYTES), deadline()
            )

    def test_the_largest_records_fit_16_kib(self, layout: StoreLayout) -> None:
        """Every bounded field at its limit, in characters that escape to
        twelve bytes each, still fits."""
        wide = "\U0001f5bc" * 1000
        records = layout.records(FakeClock())
        for number in range(MAX_FINGERPRINTS):
            record = build_current_record(
                qualified_id="aic:" + "9" * 196,
                attribution=Attribution(
                    title=wide, creator=wide, date_text=wide, credit_line=wide, detail_url=wide
                ),
                sha256="a" * 64,
                delivered_at=T0,
                preview_fingerprint=_fp(number),
            )
            records.write_current(record, deadline())
        size = (layout.data / "state" / "current.json").stat().st_size
        assert size <= MAX_RECORD_BYTES
        stats = RunStats(
            attempts=[AttemptNote("aic:" + "9" * 196, "fallback", "failed:" + "x" * 40)] * 2
        )
        record = build_last_run_record(
            outcome=Outcome.DELIVERED_WITH_WARNINGS,
            hint="the upload may have reached the TV",
            started_at=T0,
            finished_at=T0,
            elapsed_s=119.9,
            filters=None,
            stats=stats,
            artwork_id="aic:" + "9" * 196,
        )
        records.write_last_run(record, deadline())

    def test_an_expired_deadline_writes_nothing(self, layout: StoreLayout) -> None:
        records = layout.records(FakeClock())
        with pytest.raises(DeadlineExceeded):
            records.write_last_run(last_run_record(), deadline(0))
        with pytest.raises(DeadlineExceeded):
            records.write_current(current_record(1), deadline(0))
        assert not (layout.data / "state").exists()

    def test_a_record_that_may_not_be_durable_only_warns(
        self,
        layout: StoreLayout,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        real_commit = Directory.commit

        def commit(directory: Directory, staged: Staged, *, refresh_backup: bool) -> None:
            real_commit(directory, staged, refresh_backup=refresh_backup)
            raise CommitError("flush failed", replaced=True)

        monkeypatch.setattr(Directory, "commit", commit)
        with caplog.at_level(logging.WARNING, "frame_gallery.store"):
            layout.records(FakeClock()).write_last_run(last_run_record(), deadline())
        assert "last_run.json was written, but it may not be durable yet" in caplog.text

    def test_a_record_that_was_not_written_is_an_error(
        self, layout: StoreLayout, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def commit(directory: Directory, staged: Staged, *, refresh_backup: bool) -> None:
            raise CommitError("rename failed", replaced=False)

        monkeypatch.setattr(Directory, "commit", commit)
        with pytest.raises(StateError, match="rename failed"):
            layout.records(FakeClock()).write_last_run(last_run_record(), deadline())

    def test_a_linked_state_directory_is_refused(self, layout: StoreLayout, tmp_path: Path) -> None:
        (tmp_path / "elsewhere").mkdir()
        (layout.data / "state").symlink_to(tmp_path / "elsewhere")
        records = layout.records(FakeClock())
        with pytest.raises(StateError, match="symbolic link"):
            records.write_last_run(last_run_record(), deadline())
        assert records.preview_fingerprints() == ()


class TestFormats:
    def test_merging_keeps_order_and_bound(self) -> None:
        earlier = tuple(_fp(n) for n in range(10))
        assert merged_fingerprints((_fp(3),), earlier)[:2] == [_fp(3), _fp(0)]
        assert len(merged_fingerprints((_fp(99),), earlier)) == MAX_FINGERPRINTS

    @pytest.mark.parametrize(
        ("changes", "message"),
        [
            ({"id": "bad id"}, "invalid identifier"),
            ({"sha256": "XYZ"}, "invalid sha256"),
            ({"delivered_at": None}, "invalid timestamp"),
            ({"attribution": "text"}, "invalid attribution"),
            ({"preview_fingerprints": "x"}, "invalid preview fingerprints"),
            ({"preview_fingerprints": ["a" * 64] * 11}, "invalid preview fingerprints"),
            ({"preview_fingerprints": [1]}, "invalid preview fingerprint"),
        ],
    )
    def test_invalid_current_records(self, changes: dict[str, object], message: str) -> None:
        record = current_record(1)
        record.update(changes)
        with pytest.raises(ValueError, match=message):
            parse_current(record)

    @pytest.mark.parametrize(
        ("changes", "message"),
        [
            ({"outcome": ""}, "invalid outcome"),
            ({"outcome": 3}, "invalid outcome"),
            ({"finished_at": "later"}, "invalid timestamp"),
        ],
    )
    def test_invalid_last_run_records(self, changes: dict[str, object], message: str) -> None:
        with pytest.raises(ValueError, match=message):
            parse_last_run(last_run_record(**changes))


def _fp(number: int) -> str:
    return hashlib.sha256(f"fp{number}".encode()).hexdigest()
