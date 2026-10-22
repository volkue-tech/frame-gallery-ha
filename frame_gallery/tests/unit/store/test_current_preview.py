"""No TV/network: identity, size, corruption and publication-failure scenarios."""

from __future__ import annotations

import base64
import fcntl
import hashlib
import io
import json
import os
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.errors import StateError
from frame_gallery.store import preview_cache as module
from frame_gallery.store.atomic import Directory, ReadFailure
from frame_gallery.store.current_preview import NEUTRAL_JPEG, CurrentPreview
from frame_gallery.store.delivery_associations import DeliveryAssociations
from frame_gallery.store.preview_cache import PreviewCache
from frame_gallery.store.records import RunRecordStore
from tests.support.clock import FakeClock
from tests.unit.store.test_delivery_associations import item


def encoded(colour: str = "blue") -> str:
    with Image.new("RGB", (320, 180), colour) as image:
        result = io.BytesIO()
        image.save(result, format="JPEG", quality=70)
        return base64.b64encode(result.getvalue()).decode("ascii")


def deadline() -> Deadline:
    return Deadline.after(FakeClock(), 5, "preview")


def blobs(root: Path) -> list[Path]:
    return sorted((root / "preview-cache").glob("*.json"))


def test_exact_identity_survives_restart_and_never_borrows_other_upload(tmp_path: Path) -> None:
    cache, entry = PreviewCache(tmp_path), item()
    assert cache.lookup(entry, deadline()) is None
    cache.remember(entry, encoded(), deadline())
    assert PreviewCache(tmp_path).lookup(entry, deadline()) == base64.b64decode(encoded())
    for changed in (
        replace(entry, device_id="d" * 64),
        replace(entry, content_id="MY_OTHER"),
        replace(entry, work_id="commons:124"),
        replace(entry, jpeg_sha256="e" * 64),
    ):
        assert cache.lookup(changed, deadline()) is None
    with pytest.raises(ValueError, match="rejected"):
        cache.lookup(replace(entry, image_rejected=True), deadline())
    before = blobs(tmp_path)[0].read_bytes()
    cache.remember(entry, encoded(), deadline())
    assert blobs(tmp_path)[0].read_bytes() == before
    assert not (tmp_path / "state").exists()


@pytest.mark.parametrize("bad", [b"broken JSON", b"[]", b"{}", b"x" * (48 * 1024 + 1)])
def test_corrupt_cache_is_unavailable_not_another_preview(tmp_path: Path, bad: bytes) -> None:
    cache = PreviewCache(tmp_path)
    cache.remember(item(), encoded(), deadline())
    blobs(tmp_path)[0].write_bytes(bad)
    assert cache.lookup(item(), deadline()) is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("format", "other"),
        ("version", True),
        ("version", 2),
        ("identity", ["other TV"]),
        ("image_sha256", "f" * 64),
        ("jpeg", "bad"),
    ],
)
def test_wrong_version_hash_and_identity_are_not_displayed(
    tmp_path: Path,
    field: str,
    value: object,
) -> None:
    cache = PreviewCache(tmp_path)
    cache.remember(item(), encoded(), deadline())
    path = blobs(tmp_path)[0]
    document = json.loads(path.read_text())
    document[field] = value
    path.write_text(json.dumps(document))
    assert cache.lookup(item(), deadline()) is None


def test_cache_byte_and_entry_caps_evict_lru_only_not_associations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(module, "MAX_CACHE_ENTRIES", 2)
    cache = PreviewCache(tmp_path)
    first, second, third = item(), item(content_id="MY_SECOND"), item(content_id="MY_THIRD")
    archive = DeliveryAssociations(tmp_path)
    archive.remember(first, deadline())
    cache.remember(first, encoded(), deadline())
    cache.remember(second, encoded("red"), deadline())
    for path in blobs(tmp_path):
        os.utime(path, (1, 1))
    assert cache.lookup(first, deadline()) is not None
    cache.remember(third, encoded("green"), deadline())
    assert cache.lookup(second, deadline()) is None
    assert cache.lookup(first, deadline()) is not None
    assert len(blobs(tmp_path)) == 2
    assert archive.find(first.device_id, first.content_id) == first
    total = sum(p.stat().st_size for p in blobs(tmp_path))
    monkeypatch.setattr(module, "MAX_CACHE_BYTES", total)
    cache.remember(item(content_id="MY_FOURTH"), encoded(), deadline())
    assert sum(p.stat().st_size for p in blobs(tmp_path)) <= total


def test_too_small_capacity_and_low_space_never_grow_cache(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache = PreviewCache(tmp_path)
    monkeypatch.setattr(module, "MAX_CACHE_BYTES", 1)
    with pytest.raises(StateError, match="capacity"):
        cache.remember(item(), encoded(), deadline())
    assert not blobs(tmp_path)
    monkeypatch.setattr(module, "MAX_CACHE_BYTES", 128 * 1024 * 1024)
    monkeypatch.setattr(os, "fstatvfs", lambda _fd: SimpleNamespace(f_bavail=0, f_frsize=1))
    with pytest.raises(StateError, match="free space"):
        cache.remember(item(), encoded(), deadline())
    assert not blobs(tmp_path)


def test_symlink_cache_file_and_directory_cannot_escape(tmp_path: Path) -> None:
    cache = PreviewCache(tmp_path)
    cache.remember(item(), encoded(), deadline())
    path = blobs(tmp_path)[0]
    external = tmp_path / "preserve"
    external.write_bytes(b"user data")
    path.unlink()
    path.symlink_to(external)
    assert cache.lookup(item(), deadline()) is None
    with pytest.raises(StateError, match="invalid preview cache file"):
        cache.remember(item(content_id="MY_OTHER"), encoded(), deadline())
    assert external.read_bytes() == b"user data"
    path.unlink()
    (tmp_path / "preview-cache/cache.lock").unlink()
    (tmp_path / "preview-cache").rmdir()
    (tmp_path / "preview-cache").symlink_to(tmp_path, target_is_directory=True)
    assert cache.lookup(item(), deadline()) is None
    with pytest.raises(StateError):
        cache.remember(item(), encoded(), deadline())


def test_busy_writer_is_nonblocking_and_does_not_change_cache(tmp_path: Path) -> None:
    cache = PreviewCache(tmp_path)
    cache.remember(item(), encoded(), deadline())
    fd = os.open(tmp_path / "preview-cache/cache.lock", os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BlockingIOError):
            cache.remember(item(content_id="MY_OTHER"), encoded(), deadline())
    finally:
        os.close(fd)
    assert len(blobs(tmp_path)) == 1


def test_only_owned_temporary_files_are_cleaned_and_foreign_files_preserved(tmp_path: Path) -> None:
    cache = PreviewCache(tmp_path)
    cache.remember(item(), encoded(), deadline())
    directory = tmp_path / "preview-cache"
    leftover = directory / (("f" * 64) + ".json.tmp-0123456789abcdef")
    leftover.write_bytes(b"interrupted cache staging")
    cache.remember(item(), encoded(), deadline())
    assert not leftover.exists()
    foreign = directory / "keep.txt"
    foreign.write_bytes(b"private")
    with pytest.raises(StateError, match="unknown"):
        cache.remember(item(), encoded(), deadline())
    assert foreign.read_bytes() == b"private"


def test_current_file_separate_from_last_sent_and_neutral_for_missing(tmp_path: Path) -> None:
    data, media = tmp_path / "data", tmp_path / "media"
    data.mkdir()
    (media / "frame_gallery/preview").mkdir(parents=True)
    last = media / "frame_gallery/preview/latest.jpg"
    last.write_bytes(b"last sent remains unchanged")
    cache, current = PreviewCache(data), CurrentPreview(data, media)
    cache.remember(item(), encoded(), deadline())
    raw = base64.b64decode(encoded())
    assert current.publish(item(), deadline()) == hashlib.sha256(raw).hexdigest()
    target = last.with_name("current.jpg")
    assert target.read_bytes() == raw
    assert current.publish(item(), deadline()) == hashlib.sha256(raw).hexdigest()
    assert current.publish(item(content_id="MY_UNKNOWN"), deadline()) is None
    assert target.read_bytes() == NEUTRAL_JPEG
    assert current.publish(None, deadline()) is None
    assert last.read_bytes() == b"last sent remains unchanged"
    with Image.open(io.BytesIO(NEUTRAL_JPEG)) as image:
        image.load()
        assert image.getpixel((0, 0)) == (32, 32, 32)


def test_current_cache_disk_or_deadline_failure_returns_no_advertisable_digest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = CurrentPreview(tmp_path, tmp_path)
    clock = FakeClock()
    expired = Deadline.after(clock, 1, "expired")
    clock.advance(2)
    assert current.publish(None, expired) is None
    monkeypatch.setattr(
        Directory, "stage", lambda *_a, **_kw: (_ for _ in ()).throw(StateError("full"))
    )
    assert current.publish(None, deadline()) is None


def test_transient_delivery_preview_never_enters_association_archive(tmp_path: Path) -> None:
    record: dict[str, object] = {
        "id": "commons:123",
        "attribution": {"title": "A title", "creator": "An artist"},
        "tv_device_id": "a" * 64,
        "tv_content_id": "MY_F0001",
        "tv_target_sha256": "b" * 64,
        "sha256": "c" * 64,
        "delivered_at": "2026-10-18T10:00:00+00:00",
        "delivery_preview_jpeg": encoded(),
    }
    store = RunRecordStore(tmp_path, clock=FakeClock())
    store.write_delivery(record, deadline())
    assert PreviewCache(tmp_path).lookup(item(), deadline()) is not None
    archive = tmp_path / "state/artwork-deliveries.json"
    assert "delivery_preview_jpeg" not in archive.read_text()
    record["delivery_preview_jpeg"] = 123
    store.write_delivery(record, deadline())
    assert len(DeliveryAssociations(tmp_path).all()) == 1
    record["delivery_preview_jpeg"] = "bad"
    store.write_delivery(record, deadline())
    assert len(DeliveryAssociations(tmp_path).all()) == 1


def test_expired_cache_write_does_not_create_files(tmp_path: Path) -> None:
    clock = FakeClock()
    expired = Deadline.after(clock, 1, "expired")
    clock.advance(2)
    with pytest.raises(DeadlineExceeded):
        PreviewCache(tmp_path).remember(item(), encoded(), expired)
    assert not (tmp_path / "preview-cache").exists()


@pytest.mark.parametrize("kind", ["lock", "bytes", "count", "scan"])
def test_damaged_lock_and_existing_limits_fail_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    cache = PreviewCache(tmp_path)
    cache.remember(item(), encoded(), deadline())
    if kind == "lock":
        (tmp_path / "preview-cache/cache.lock").write_bytes(b"foreign")
    elif kind == "bytes":
        monkeypatch.setattr(module, "MAX_CACHE_BYTES", 1)
    elif kind == "count":
        monkeypatch.setattr(module, "MAX_CACHE_ENTRIES", 0)
    else:
        monkeypatch.setattr(Directory, "names", lambda *_args: ["cache.lock"] * 4130)
    with pytest.raises(StateError, match=r"(lock|limit)"):
        cache.remember(item(), encoded(), deadline())


@pytest.mark.parametrize("temporary", [False, True])
def test_eviction_or_temporary_cleanup_failure_preserves_other_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    temporary: bool,
) -> None:
    cache = PreviewCache(tmp_path)
    cache.remember(item(), encoded(), deadline())
    if temporary:
        (tmp_path / "preview-cache" / (("a" * 64) + ".json.tmp-0123456789abcdef")).write_bytes(
            b"own"
        )
    else:
        monkeypatch.setattr(module, "MAX_CACHE_ENTRIES", 1)
    monkeypatch.setattr(Directory, "unlink", lambda *_args: False)
    with pytest.raises(StateError, match=r"(cleanup|eviction)"):
        cache.remember(item(content_id="MY_OTHER"), encoded(), deadline())
    assert blobs(tmp_path)[0].read_bytes()


@pytest.mark.parametrize("current", [False, True])
def test_staging_readback_mismatch_is_not_published(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    current: bool,
) -> None:
    original = Directory.read_bytes

    def changed(self: Directory, name: str, limit: int) -> bytes | ReadFailure:
        return ReadFailure.UNREADABLE if ".tmp-" in name else original(self, name, limit)

    monkeypatch.setattr(Directory, "read_bytes", changed)
    if current:
        assert CurrentPreview(tmp_path, tmp_path).publish(None, deadline()) is None
        assert not (tmp_path / "frame_gallery/preview/current.jpg").exists()
    else:
        with pytest.raises(StateError, match="staging mismatch"):
            PreviewCache(tmp_path).remember(item(), encoded(), deadline())
        assert not blobs(tmp_path)


def test_cache_touch_failure_keeps_valid_preview(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = PreviewCache(tmp_path)
    cache.remember(item(), encoded(), deadline())

    def refused(*_args: object, **_kwargs: object) -> None:
        raise OSError("readonly filesystem")

    monkeypatch.setattr(os, "utime", refused)
    assert cache.lookup(item(), deadline()) == base64.b64decode(encoded())


def test_fifo_lock_is_refused_without_blocking(tmp_path: Path) -> None:
    directory = tmp_path / "preview-cache"
    directory.mkdir()
    os.mkfifo(directory / "cache.lock")
    with pytest.raises(StateError, match="invalid preview cache lock"):
        PreviewCache(tmp_path).remember(item(), encoded(), deadline())
