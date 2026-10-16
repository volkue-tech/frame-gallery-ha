from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from ipaddress import IPv4Address
from pathlib import Path

import pytest

from frame_gallery.isolation.executor import (
    EventSink,
    JsonObject,
    StopCheck,
    WorkerError,
    WorkerErrorKind,
)
from frame_gallery.observer.backend import HostObserver
from frame_gallery.observer.model import Observation, Status
from frame_gallery.store.artwork_bindings import BindingStore
from frame_gallery.store.observer_targets import TargetStore
from frame_gallery.tv.token_store import TokenStore

HOST = IPv4Address("192.168.1.20")
DEVICE = "a" * 64
THUMBNAIL_HASH = hashlib.sha256(b"x").hexdigest()


class Executor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, JsonObject]] = []
        self.result = Observation(Status.UNIDENTIFIED, DEVICE, "MY_TEST", THUMBNAIL_HASH).to_json()
        self.result["thumbnail"] = "eA=="
        self.matched = True
        self.failure = False

    def run(
        self,
        task: str,
        payload: JsonObject,
        *,
        timeout: float,
        on_event: EventSink | None = None,
        should_stop: StopCheck | None = None,
        files: Sequence[int] = (),
    ) -> JsonObject:
        self.calls.append((task, payload))
        assert timeout <= 5
        if self.failure:
            raise WorkerError(WorkerErrorKind.TIMEOUT)
        return dict(self.result) if task == "observe" else {"matched": self.matched}

    def terminate_all(self) -> None:
        pass


class Rig:
    def __init__(self, root: Path) -> None:
        self.data, self.media = root / "data", root / "media"
        self.data.mkdir()
        self.preview = self.media / "frame_gallery" / "preview"
        self.preview.mkdir(parents=True)
        (self.preview / "latest.jpg").write_bytes(b"synthetic JPEG")
        self.executor = Executor()
        self.observer = HostObserver(self.executor, self.data, self.media, HOST, device_id=DEVICE)
        TokenStore(self.data, HOST).install("12345678")
        self.record: dict[str, object] = {
            "format": "frame-gallery-current",
            "version": 1,
            "tv_content_id": "MY_TEST",
            "id": "commons:123",
            "sha256": "c" * 64,
            "attribution": {"title": "Synthetic work", "creator": "Synthetic Artist"},
        }
        self.save()

    def save(self) -> None:
        directory = self.data / "state"
        directory.mkdir(exist_ok=True)
        (directory / "current.json").write_text(json.dumps(self.record))


def test_no_policy_or_token_means_no_network_worker(tmp_path: Path) -> None:
    executor = Executor()
    observer = HostObserver(executor, tmp_path, tmp_path, HOST)
    assert observer.read().status is Status.VALIDATION_REQUIRED
    observer = HostObserver(executor, tmp_path, tmp_path, HOST, device_id=DEVICE)
    assert observer.read().status is Status.NOT_AUTHORIZED
    assert executor.calls == []


def test_explicit_tokenless_grant_still_requires_identity(tmp_path: Path) -> None:
    executor = Executor()
    observer = HostObserver(executor, tmp_path, tmp_path, HOST, tokenless_grant=True)
    assert observer.read().status is Status.VALIDATION_REQUIRED
    assert executor.calls == []
    observer = HostObserver(
        executor, tmp_path, tmp_path, HOST, device_id=DEVICE, tokenless_grant=True
    )
    assert observer.read().status is Status.UNIDENTIFIED
    assert executor.calls == [
        (
            "observe",
            {
                "host": str(HOST),
                "token": None,
                "device_id": DEVICE,
                "tokenless_grant": True,
                "enroll_device": False,
            },
        )
    ]


def test_rejected_stored_token_does_not_retry_tokenless(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.executor.result = Observation(Status.NOT_AUTHORIZED).to_json()
    assert rig.observer.read().status is Status.NOT_AUTHORIZED
    assert len(rig.executor.calls) == 1
    assert rig.executor.calls[0][1]["tokenless_grant"] is False
    assert rig.executor.calls[0][1]["token"] == "12345678"  # noqa: S105


def test_verified_current_image_creates_mapping_but_never_changes_history(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    (rig.data / "state" / "history.json").write_bytes(b"preserve")
    observation = rig.observer.read()
    store = BindingStore(rig.data)
    assert store.resolve(observation) is not None
    assert [task for task, _ in rig.executor.calls] == ["observe", "verify_thumbnail"]
    assert rig.observer.read() == observation
    assert [task for task, _ in rig.executor.calls] == ["observe", "verify_thumbnail", "observe"]
    assert (rig.data / "state" / "history.json").read_bytes() == b"preserve"


def test_concurrent_upload_or_wrong_preview_never_creates_a_caption(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.executor.matched = False
    seen = rig.observer.read()
    assert seen.status is Status.UNIDENTIFIED
    assert BindingStore(rig.data).resolve(seen) is None


@pytest.mark.parametrize(
    "change",
    [
        {"tv_content_id": "OTHER"},
        {"attribution": None},
        {"sha256": None},
        {"format": "wrong"},
        {"version": 2},
    ],
)
def test_unknown_or_legacy_records_are_not_guessed(
    tmp_path: Path, change: dict[str, object]
) -> None:
    rig = Rig(tmp_path)
    rig.record.update(change)
    rig.save()
    assert rig.observer.read().status is Status.UNIDENTIFIED
    assert len(rig.executor.calls) == 1


@pytest.mark.parametrize("thumbnail", [None, 4, "x" * (56 * 1024 + 1)])
def test_missing_or_large_thumbnail_is_not_compared(tmp_path: Path, thumbnail: object) -> None:
    rig = Rig(tmp_path)
    rig.executor.result["thumbnail"] = thumbnail  # type: ignore[assignment]
    assert rig.observer.read().status is Status.UNAVAILABLE
    assert len(rig.executor.calls) == 1


def test_other_tv_and_failed_worker_are_unavailable(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.executor.result["device_id"] = "d" * 64
    assert rig.observer.read().status is Status.UNAVAILABLE
    rig.executor.failure = True
    assert rig.observer.read().status is Status.UNAVAILABLE


@pytest.mark.parametrize("thumbnail", ["!", "", "eQ==", "eA==" * (41 * 1024)])
def test_inconsistent_thumbnail_bytes_cannot_reuse_a_mapping(
    tmp_path: Path, thumbnail: str
) -> None:
    rig = Rig(tmp_path)
    rig.observer.read()
    rig.executor.result["thumbnail"] = thumbnail
    assert rig.observer.read().status is Status.UNAVAILABLE


@pytest.mark.parametrize("raw", [None, "bad JSON", "[]"])
def test_missing_or_damaged_record_preserves_unknown(tmp_path: Path, raw: str | None) -> None:
    rig = Rig(tmp_path)
    record = rig.data / "state" / "current.json"
    if raw is None:
        record.unlink()
    else:
        record.write_text(raw)
    assert rig.observer.read().status is Status.UNIDENTIFIED


def test_preview_symlink_is_not_followed(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    preview = rig.preview / "latest.jpg"
    preview.unlink()
    preview.symlink_to(rig.data / "state" / "current.json")
    assert rig.observer.read().status is Status.UNAVAILABLE


@pytest.mark.parametrize("with_token", [False, True])
def test_successful_delivery_enrolls_and_pins_without_any_extra_setup(
    tmp_path: Path, with_token: bool
) -> None:
    rig = Rig(tmp_path)
    if not with_token:
        TokenStore(rig.data, HOST).remove()
    observer = HostObserver(rig.executor, rig.data, rig.media, HOST)
    assert observer.read().status is Status.VALIDATION_REQUIRED
    assert observer.after_delivery(b"")
    assert rig.executor.calls == []  # Granting does not connect.
    seen = observer.read()
    assert seen.status is Status.UNIDENTIFIED
    payload = rig.executor.calls[0][1]
    assert payload["enroll_device"] is True
    assert payload["device_id"] is None
    assert payload["tokenless_grant"] is (not with_token)
    assert payload["token"] == ("12345678" if with_token else None)
    assert TargetStore(rig.data).targets() == {str(HOST): DEVICE}
    assert BindingStore(rig.data).resolve(seen) is not None
    observer.read()
    assert rig.executor.calls[-1][1]["device_id"] == DEVICE
    assert rig.executor.calls[-1][1]["enroll_device"] is False

    restarted = HostObserver(rig.executor, rig.data, rig.media, HOST)
    count = len(rig.executor.calls)
    assert restarted.read().status is Status.VALIDATION_REQUIRED
    assert len(rig.executor.calls) == count
    assert restarted.after_delivery(b"")
    restarted.read()
    assert rig.executor.calls[-1][1]["device_id"] == DEVICE
    assert rig.executor.calls[-1][1]["enroll_device"] is False


def test_failed_enrollment_never_pins_a_device(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    observer = HostObserver(rig.executor, rig.data, rig.media, HOST)
    assert observer.after_delivery(b"")
    rig.executor.result = Observation(Status.TV_IN_USE).to_json()
    assert observer.read().status is Status.TV_IN_USE
    assert TargetStore(rig.data).targets() == {}


@pytest.mark.parametrize("full", [False, True])
def test_bad_or_full_pin_table_blocks_post_delivery_network(tmp_path: Path, full: bool) -> None:
    rig = Rig(tmp_path)
    if full:
        for value in range(32):
            TargetStore(rig.data).pin(IPv4Address(f"192.168.2.{value + 1}"), DEVICE)
    else:
        (rig.data / "state" / "observer-targets.json").write_text("broken")
    observer = HostObserver(rig.executor, rig.data, rig.media, HOST)
    assert not observer.after_delivery(b"")
    assert observer.read().status is Status.VALIDATION_REQUIRED
    assert rig.executor.calls == []


@pytest.mark.parametrize("before", [None, b""])
def test_snapshot_distinguishes_missing_from_unreadable(
    tmp_path: Path, before: bytes | None
) -> None:
    rig = Rig(tmp_path)
    observer = HostObserver(rig.executor, rig.data, rig.media, HOST)
    if before is None:
        assert not observer.after_delivery(None)
    else:
        current = rig.data / "state" / "current.json"
        current.unlink()
        assert observer.delivery_snapshot() == b""
        assert not observer.after_delivery(before)
        current.symlink_to(rig.data / "state" / "history.json")
        assert observer.delivery_snapshot() is None
    assert observer.read().status is Status.VALIDATION_REQUIRED
    assert rig.executor.calls == []


def test_no_match_or_failed_send_cannot_arm_from_the_previous_record(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    observer = HostObserver(rig.executor, rig.data, rig.media, HOST)
    before = observer.delivery_snapshot()
    assert before
    assert not observer.after_delivery(before)
    assert observer.read().status is Status.VALIDATION_REQUIRED
    assert rig.executor.calls == []


def test_missing_or_inaccessible_state_directory_cannot_supply_a_receipt(tmp_path: Path) -> None:
    executor = Executor()
    observer = HostObserver(executor, tmp_path, tmp_path, HOST)
    assert observer.delivery_snapshot() is None
    assert not observer.after_delivery(None)
    assert executor.calls == []


@pytest.mark.parametrize("record", ["bad", "[]", '{"format":"wrong"}'])
def test_changed_but_invalid_record_cannot_arm_reads(tmp_path: Path, record: str) -> None:
    rig = Rig(tmp_path)
    observer = HostObserver(rig.executor, rig.data, rig.media, HOST)
    (rig.data / "state" / "current.json").write_text(record)
    assert not observer.after_delivery(b"")
    assert observer.read().status is Status.VALIDATION_REQUIRED


@pytest.mark.parametrize("content_id", [None, 4, "../bad"])
def test_fresh_record_needs_a_valid_tv_id(tmp_path: Path, content_id: object) -> None:
    rig = Rig(tmp_path)
    observer = HostObserver(rig.executor, rig.data, rig.media, HOST)
    rig.record["tv_content_id"] = content_id
    rig.save()
    assert not observer.after_delivery(b"")
    assert rig.executor.calls == []
