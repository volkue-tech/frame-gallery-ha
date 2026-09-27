"""Duplicate prevention and bounded state, end to end (§12.4, §13, §14).

The runner works over the real state store, workspace, preview, and run
records in a temporary directory; the television is a fake that emits its
progress markers (E7-E10). Each run builds fresh ports over the same
directories, as a new process would, and a later run checks what an earlier
one left behind.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pytest

from frame_gallery.app.outcomes import Hint, Outcome
from frame_gallery.budget.deadline import Deadline
from frame_gallery.config.filters import EffectiveFilters, FilterSet
from frame_gallery.domain import SourceKey
from frame_gallery.fingerprint import fingerprint_bytes
from frame_gallery.providers.contract import DiscoveryContext
from frame_gallery.providers.local_media import LocalMediaProvider, SkipReason
from frame_gallery.randomness import SeededRandomSource
from frame_gallery.store.atomic import Directory, Staged
from frame_gallery.store.state import FileStateStore
from frame_gallery.tv.port import DeliveryStatus, Marker
from tests.support.fakes import canvas_jpeg_bytes, make_candidate
from tests.support.persistent import PersistentRig, ProcessKilled

UPLOADED_THEN = (Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED)


@pytest.fixture
def rig(tmp_path: Path) -> PersistentRig:
    return PersistentRig(tmp_path / "rig")


def kill_at(marker: Marker) -> Callable[[Marker], None]:
    def during(seen: Marker) -> None:
        if seen is marker:
            raise ProcessKilled

    return during


# ----------------------------------------------------------------- delivered


def test_a_delivered_run_changes_history_ledger_preview_and_records(rig: PersistentRig) -> None:
    """E1, E5, E10, D8: exactly one identifier in history; the preview is the payload."""
    h = rig.harness()
    result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert rig.history() == ["aic:1001"]
    assert rig.ledger() == {"aic:1001": "uploaded"}
    payload = h.tv.payloads[0]
    assert rig.preview_file.read_bytes() == payload
    current = rig.current()
    assert current is not None
    assert current["id"] == "aic:1001"
    assert current["sha256"] == hashlib.sha256(payload).hexdigest()
    assert current["preview_fingerprints"] == [fingerprint_bytes(payload)]
    assert rig.last_run()["outcome"] == "delivered"
    assert rig.leftovers() == []  # F1: nothing temporary is left


def test_the_next_runs_never_resend_and_prune_the_ledger(rig: PersistentRig) -> None:
    """E6, C3, D8: across restarts, each run delivers a new work, and the
    preview and the record follow each delivery."""
    delivered: list[str | None] = []
    previews: list[bytes] = []
    for day in range(3):
        h = rig.harness(days=day)
        delivered.append(h.run().delivered_id)
        payload = h.tv.payloads[0]
        assert rig.preview_file.read_bytes() == payload
        current = rig.current()
        assert current is not None
        assert current["sha256"] == hashlib.sha256(payload).hexdigest()
        previews.append(payload)
    assert delivered == ["aic:1001", "aic:1002", "aic:1003"]
    assert len(set(previews)) == 3
    current = rig.current()
    assert current is not None
    assert current["preview_fingerprints"] == [fingerprint_bytes(p) for p in reversed(previews)]
    assert rig.history() == ["aic:1001", "aic:1002", "aic:1003"]
    # A work leaves the ledger once both copies of history hold it (D-154).
    assert rig.ledger() == {"aic:1002": "uploaded", "aic:1003": "uploaded"}
    result = rig.harness(days=3).run()
    assert result.outcome is Outcome.NO_MATCH
    assert result.hint == Hint.NOTHING_NEW


def test_repeated_runs_do_not_grow_temporary_or_state_storage(rig: PersistentRig) -> None:
    """F3: temporary storage stays empty and state files stay the same set."""
    rig.candidates = [make_candidate(str(number)) for number in range(2000, 2008)]
    names: list[list[str]] = []
    for day in range(6):
        rig.harness(days=day).run()
        names.append(sorted(p.name for p in rig.state.iterdir()))
        assert rig.leftovers() == []
        assert list((rig.layout.tmp / "frame-gallery").iterdir()) == []
    assert names[-1] == names[-2] == names[-3]
    assert names[-1] == [
        ".lock",
        "current.json",
        "history.json",
        "history.json.bak",
        "last_run.json",
        "upload_ledger.json",
        "upload_ledger.json.bak",
    ]


# ------------------------------------------------------- the ledger (E7-E9)


def test_e7_selection_refused_after_the_upload(rig: PersistentRig) -> None:
    h = rig.harness()
    h.tv.markers = list(UPLOADED_THEN)
    h.tv.status = DeliveryStatus.REFUSED
    result = h.run()
    assert result.outcome is Outcome.TV_REJECTED
    assert rig.ledger() == {"aic:1001": "uploaded"}
    assert rig.history() == []
    assert not rig.preview_file.exists()
    assert rig.current() is None  # E10: nothing changes without selected
    next_run = rig.harness(days=45)
    assert next_run.run().delivered_id == "aic:1002"
    assert len(next_run.tv.payloads) == 1


def test_e8_connection_lost_during_selection(rig: PersistentRig) -> None:
    h = rig.harness()
    h.tv.markers = list(UPLOADED_THEN)
    h.tv.status = DeliveryStatus.UNREACHABLE
    result = h.run()
    assert result.outcome is Outcome.TV_UNREACHABLE
    assert result.hint == Hint.STORED_ON_TV
    assert rig.ledger() == {"aic:1001": "uploaded"}
    assert rig.harness(days=45).run().delivered_id == "aic:1002"


def test_e9_killed_after_the_intent_quarantines_the_work(rig: PersistentRig) -> None:
    h = rig.harness()
    h.tv.markers = [Marker.CONNECTED]
    h.tv.during = kill_at(Marker.CONNECTED)
    with pytest.raises(ProcessKilled):
        h.run()
    assert rig.ledger() == {"aic:1001": "uncertain"}
    assert rig.harness(days=29).run().delivered_id == "aic:1002"
    # After the 30-day quarantine the work may be offered again.
    assert rig.harness(days=31).run().delivered_id == "aic:1001"


def test_e9_killed_after_uploaded_never_resends(rig: PersistentRig) -> None:
    h = rig.harness()
    h.tv.during = kill_at(Marker.UPLOADED)
    with pytest.raises(ProcessKilled):
        h.run()
    assert rig.ledger() == {"aic:1001": "uploaded"}
    assert rig.history() == []
    assert rig.harness(days=1).run().delivered_id == "aic:1002"
    assert rig.harness(days=400).run().delivered_id == "aic:1003"


def test_e9_killed_before_the_promotion_was_written_quarantines_the_work(
    rig: PersistentRig, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = rig.harness()
    real_commit = Directory.commit

    def commit(directory: Directory, staged: Staged, *, refresh_backup: bool) -> None:
        if staged.name == "upload_ledger.json" and "tv.marker:uploaded" in h.events:
            raise ProcessKilled
        real_commit(directory, staged, refresh_backup=refresh_backup)

    monkeypatch.setattr(Directory, "commit", commit)
    with pytest.raises(ProcessKilled):
        h.run()
    monkeypatch.undo()
    assert rig.ledger() == {"aic:1001": "uncertain"}
    assert rig.harness(days=1).run().delivered_id == "aic:1002"
    assert rig.harness(days=31).run().delivered_id == "aic:1001"


def test_a_failed_promotion_keeps_the_quarantine_and_the_outcome(
    rig: PersistentRig, monkeypatch: pytest.MonkeyPatch
) -> None:
    """§13.6 step 4: the promotion write fails; ERROR, outcome unchanged."""
    h = rig.harness()
    h.tv.markers = list(UPLOADED_THEN)
    h.tv.status = DeliveryStatus.REFUSED
    store = h.state_store
    assert isinstance(store, FileStateStore)
    promoting: list[bool] = []
    real_promote = store.promote_upload

    def promote(qualified_id: str, now: datetime) -> None:
        promoting.append(True)
        try:
            real_promote(qualified_id, now)
        finally:
            promoting.clear()

    real_write = os.write

    def write(fd: int, data: bytes) -> int:
        if promoting:
            raise OSError(errno.ENOSPC, "full")
        return real_write(fd, data)

    monkeypatch.setattr(store, "promote_upload", promote)
    monkeypatch.setattr(os, "write", write)
    result = h.run()
    monkeypatch.undo()
    assert result.outcome is Outcome.TV_REJECTED
    assert rig.ledger() == {"aic:1001": "uncertain"}
    assert rig.harness(days=1).run().delivered_id == "aic:1002"


def test_an_uncertain_upload_is_quarantined(rig: PersistentRig) -> None:
    h = rig.harness()
    h.tv.markers = [Marker.CONNECTED, Marker.UPLOAD_STARTED]
    h.tv.status = DeliveryStatus.UNREACHABLE
    result = h.run()
    assert result.outcome is Outcome.TV_UNREACHABLE
    assert result.hint == Hint.UPLOAD_MAY_HAVE_REACHED_TV
    assert rig.ledger() == {"aic:1001": "uncertain"}
    assert rig.harness(days=10).run().delivered_id == "aic:1002"


@pytest.mark.parametrize(
    ("markers", "status", "outcome"),
    [
        ([Marker.CONNECTED], DeliveryStatus.NOT_AUTHORIZED, Outcome.TV_NOT_AUTHORIZED),
        ([Marker.CONNECTED], DeliveryStatus.UNSUPPORTED, Outcome.TV_REJECTED),
        ([Marker.CONNECTED], DeliveryStatus.INSUFFICIENT_TIME, Outcome.DEADLINE_EXCEEDED),
        (
            [Marker.CONNECTED, Marker.UPLOAD_STARTED],
            DeliveryStatus.REFUSED,
            Outcome.TV_REJECTED,
        ),
    ],
)
def test_results_that_prove_nothing_was_stored_remove_the_intent(
    rig: PersistentRig, markers: list[Marker], status: DeliveryStatus, outcome: Outcome
) -> None:
    """§12.4 rows 2, 3, 4, and 6 against the real ledger."""
    h = rig.harness()
    h.tv.markers = markers
    h.tv.status = status
    assert h.run().outcome is outcome
    assert rig.ledger() == {}
    assert rig.history() == []
    assert rig.harness(days=1).run().delivered_id == "aic:1001"


def test_no_upload_started_removes_the_intent(rig: PersistentRig) -> None:
    h = rig.harness()
    h.tv.markers = [Marker.CONNECTED]
    h.tv.status = DeliveryStatus.UNREACHABLE
    assert h.run().outcome is Outcome.TV_UNREACHABLE
    assert rig.ledger() == {}
    assert rig.leftovers() == []
    assert rig.harness(days=1).run().delivered_id == "aic:1001"


def test_a_stop_request_after_upload_started_keeps_the_quarantine(rig: PersistentRig) -> None:
    h = rig.harness()
    h.tv.markers = [Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED, Marker.SELECTED]

    def stop(marker: Marker) -> None:
        if marker is Marker.UPLOAD_STARTED:
            h.cancellation.request_stop()

    h.tv.during = stop
    assert h.run().outcome is Outcome.CANCELLED
    assert rig.ledger() == {"aic:1001": "uncertain"}
    assert rig.history() == []


def test_a_stop_request_after_selected_still_records(rig: PersistentRig) -> None:
    """§7.6: after selected, RECORD runs; PUBLISH is skipped."""
    h = rig.harness()

    def stop(marker: Marker) -> None:
        if marker is Marker.SELECTED:
            h.cancellation.request_stop()

    h.tv.during = stop
    result = h.run()
    assert result.outcome is Outcome.DELIVERED_WITH_WARNINGS
    assert rig.history() == ["aic:1001"]
    assert not rig.preview_file.exists()
    assert rig.current() is None
    assert rig.last_run()["outcome"] == "delivered_with_warnings"


# ------------------------------------------------------------ state errors


def test_a_full_data_partition_stops_before_the_television(
    rig: PersistentRig, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = rig.harness()

    def full(fd: int, data: object) -> int:
        raise OSError(errno.ENOSPC, "full")

    monkeypatch.setattr(os, "write", full)
    result = h.run()
    monkeypatch.undo()
    assert result.outcome is Outcome.STATE_ERROR
    assert h.tv.requests == []
    assert rig.ledger() == {}
    assert rig.leftovers() == []


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores directory permissions")
def test_a_read_only_data_partition_stops_before_the_television(rig: PersistentRig) -> None:
    rig.harness().run()  # creates the state directory and one delivery
    rig.state.chmod(0o500)
    try:
        h = rig.harness(days=1)
        result = h.run()
    finally:
        rig.state.chmod(0o700)
    assert result.outcome is Outcome.STATE_ERROR
    assert h.tv.requests == []
    assert rig.history() == ["aic:1001"]


def test_a_newer_history_stops_the_run_and_is_kept(rig: PersistentRig) -> None:
    rig.state.mkdir(parents=True)
    newer = json.dumps({"format": "frame-gallery-history", "version": 2, "entries": []})
    (rig.state / "history.json").write_text(newer)
    h = rig.harness()
    assert h.run().outcome is Outcome.STATE_ERROR
    assert h.tv.requests == []
    assert (rig.state / "history.json").read_text() == newer


def test_a_corrupt_history_is_recovered_and_the_run_continues(rig: PersistentRig) -> None:
    """F5: quarantined and recovered without a crash; nothing is resent."""
    for day in range(2):
        rig.harness(days=day).run()
    (rig.state / "history.json").write_bytes(b"\x00garbage")
    result = rig.harness(days=2).run()
    assert result.outcome is Outcome.DELIVERED
    assert result.delivered_id == "aic:1003"
    assert len(list((rig.state / "quarantine").iterdir())) == 1


def test_a_failed_history_rename_is_unrecorded_but_never_resent(
    rig: PersistentRig, monkeypatch: pytest.MonkeyPatch
) -> None:
    h = rig.harness()
    real_rename = os.rename

    def rename(
        src: str, dst: str, *, src_dir_fd: int | None = None, dst_dir_fd: int | None = None
    ) -> None:
        if dst == "history.json":
            raise OSError(errno.EIO, "io")
        real_rename(src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd)

    monkeypatch.setattr(os, "rename", rename)
    result = h.run()
    monkeypatch.undo()
    assert result.outcome is Outcome.DELIVERED_UNRECORDED
    assert rig.history() == []
    assert rig.ledger() == {"aic:1001": "uploaded"}
    assert rig.preview_file.exists()  # PUBLISH still ran
    assert rig.harness(days=1).run().delivered_id == "aic:1002"


def test_an_unavailable_media_folder_is_delivered_with_warnings(rig: PersistentRig) -> None:
    rig.layout.media.rmdir()
    result = rig.harness().run()
    assert result.outcome is Outcome.DELIVERED_WITH_WARNINGS
    assert rig.history() == ["aic:1001"]
    current = rig.current()
    assert current is not None
    assert current["id"] == "aic:1001"


# ------------------------------------------------------- the preview guard


def test_a_published_preview_copied_into_the_library_is_never_offered(
    rig: PersistentRig,
) -> None:
    """F7, guard 3: current.json's fingerprints reach the local library."""
    h = rig.harness()
    assert h.run().outcome is Outcome.DELIVERED
    library = rig.layout.media / "frame_gallery" / "library"
    library.mkdir()
    (library / "copy.jpg").write_bytes(rig.preview_file.read_bytes())
    (library / "own.jpg").write_bytes(canvas_jpeg_bytes()[:-2] + b"\x00\xff\xd9")
    records = rig.layout.records(h.clock)
    provider = LocalMediaProvider(
        root=library,
        preview_dir=rig.preview_file.parent,
        preview_fingerprints=records.preview_fingerprints(),
    )
    filters = EffectiveFilters(
        source=SourceKey.LOCAL_MEDIA,
        department=None,
        style=None,
        period=None,
        color=None,
        ignored=(),
        requested=FilterSet(source=SourceKey.LOCAL_MEDIA),
    )
    context = DiscoveryContext(
        deadline=Deadline.after(h.clock, 30, "discovery"), random=SeededRandomSource(1)
    )
    offered = [c.native_id for c in provider.iter_candidates(filters, context)]
    assert len(offered) == 1
    assert provider.report.counts[SkipReason.PREVIEW] == 1
