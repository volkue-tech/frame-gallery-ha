"""The ``inspect`` worker task: header-only dimensions after EXIF
orientation, for local media (§8.3), over descriptors the parent opened
(Phase 5 gate decision). Images are synthesized with Pillow."""

from __future__ import annotations

import errno
import os
from pathlib import Path

import pytest
from PIL import Image

from frame_gallery.domain import Size
from frame_gallery.imaging.contract import (
    INSPECT_TASK,
    MAX_INSPECT_BATCH,
    ImageFormat,
    InspectBatch,
    InspectFile,
    InspectResult,
    InspectStatus,
    PrepareFailure,
    inspected_event,
    parse_inspected_event,
)
from frame_gallery.imaging.worker_tasks import inspect_file, inspect_task
from frame_gallery.isolation.executor import JsonObject
from tests.support.images import (
    jpeg_header_only,
    marked,
    oriented_jpeg,
    save_jpeg,
    save_png,
    write_bytes,
)


def _file(path: Path, declared: ImageFormat = ImageFormat.JPEG) -> InspectFile:
    """Open ``path`` as the parent does, and describe it as the scan saw it."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    info = os.fstat(fd)
    return InspectFile(fd, declared, info.st_dev, info.st_ino)


def _open(fd: int) -> bool:
    try:
        os.fstat(fd)
    except OSError as exc:
        return exc.errno != errno.EBADF
    return True


def _inspect(path: Path, declared: ImageFormat = ImageFormat.JPEG) -> InspectResult:
    file = _file(path, declared)
    try:
        return inspect_file(file)
    finally:
        assert _open(file.fd)  # lent, so never closed by the task
        os.close(file.fd)


def test_the_task_name() -> None:
    assert INSPECT_TASK == "inspect"


@pytest.mark.parametrize(
    ("orientation", "expected"),
    [(1, Size(64, 36)), (3, Size(64, 36)), (5, Size(64, 36)), (6, Size(64, 36)), (8, Size(64, 36))],
)
def test_jpeg_sizes_after_orientation(tmp_path: Path, orientation: int, expected: Size) -> None:
    # oriented_jpeg stores the image so that the orientation displays it at 64 x 36.
    path = oriented_jpeg(tmp_path, orientation, (64, 36))
    with Image.open(path) as image:
        stored = image.size
    result = _inspect(path)
    assert result == InspectResult(status=InspectStatus.OK, oriented_size=expected)
    if orientation >= 5:
        assert stored == (36, 64)


def test_png(tmp_path: Path) -> None:
    path = save_png(marked((50, 20)), tmp_path / "a.png")
    assert _inspect(path, ImageFormat.PNG).oriented_size == Size(50, 20)


def test_the_task_reports_each_file_in_order(tmp_path: Path) -> None:
    first = save_jpeg(marked((40, 30)), tmp_path / "a.jpg")
    second = write_bytes(tmp_path / "junk.png", b"not an image")
    third = save_png(marked((10, 20)), tmp_path / "c.png")
    batch = InspectBatch(
        (_file(first), _file(second, ImageFormat.PNG), _file(third, ImageFormat.PNG))
    )
    events: list[JsonObject] = []
    try:
        assert inspect_task(batch.to_json(), events.append) == {"inspected": 3}
        assert all(_open(file.fd) for file in batch.files)
    finally:
        for file in batch.files:
            os.close(file.fd)
    results = [parse_inspected_event(event, index) for index, event in enumerate(events)]
    assert [result.oriented_size for result in results] == [Size(40, 30), None, Size(10, 20)]
    assert results[1].status is InspectStatus.FAILED
    assert events[0] == {
        "index": 0,
        "result": {"status": "ok", "oriented_size": [40, 30], "failure": None, "detail": None},
    }


@pytest.mark.parametrize(
    ("setup", "declared", "failure"),
    [
        (lambda d: d, ImageFormat.JPEG, PrepareFailure.IO),
        (
            lambda d: save_png(marked((8, 8)), d / "really.png"),
            ImageFormat.JPEG,
            PrepareFailure.FORMAT_MISMATCH,
        ),
        (
            lambda d: write_bytes(d / "huge.jpg", jpeg_header_only(30_000, 100)),
            ImageFormat.JPEG,
            PrepareFailure.LIMITS,
        ),
        (
            lambda d: write_bytes(d / "cut.jpg", b"\xff\xd8\xff\xe0\x00\x10JFIF"),
            ImageFormat.JPEG,
            PrepareFailure.DECODE,
        ),
        (lambda d: write_bytes(d / "junk.png", b"not an image"), ImageFormat.PNG, None),
    ],
    ids=["a-folder", "png-as-jpeg", "over-the-limits", "cut-header", "junk"],
)
def test_unreadable_files_fail_without_raising(
    tmp_path: Path, setup: object, declared: ImageFormat, failure: PrepareFailure | None
) -> None:
    path = setup(tmp_path)  # type: ignore[operator]
    result = _inspect(path, declared)
    assert result.status is InspectStatus.FAILED
    assert result.oriented_size is None
    assert result.failure is not None
    if failure is not None:
        assert result.failure is failure


def test_a_descriptor_that_is_not_open_fails(tmp_path: Path) -> None:
    file = _file(save_jpeg(marked((8, 8)), tmp_path / "a.jpg"))
    os.close(file.fd)
    result = inspect_file(file)
    assert result.failure is PrepareFailure.IO
    assert result.detail == "cannot read the source (EBADF)"


def test_the_worker_checks_the_scanned_identity(tmp_path: Path) -> None:
    path = save_jpeg(marked((40, 30)), tmp_path / "a.jpg")
    file = _file(path)
    try:
        assert inspect_file(file).oriented_size == Size(40, 30)
        moved = InspectFile(file.fd, file.declared_format, file.device, file.inode + 1)
        result = inspect_file(moved)
        assert result.failure is PrepareFailure.IO
        assert result.detail == "the source is not the file the scan saw"
        assert _open(file.fd)
    finally:
        os.close(file.fd)


def test_result_validation() -> None:
    with pytest.raises(ValueError, match="ok inspection"):
        InspectResult(status=InspectStatus.OK)
    with pytest.raises(ValueError, match="ok inspection"):
        InspectResult(status=InspectStatus.FAILED)
    with pytest.raises(ValueError, match="ok inspection"):
        InspectResult(status=InspectStatus.OK, oriented_size=Size(1, 1), failure=PrepareFailure.IO)
    with pytest.raises(ValueError, match="ok inspection"):
        InspectResult(
            status=InspectStatus.FAILED, oriented_size=Size(1, 1), failure=PrepareFailure.IO
        )
    with pytest.raises(ValueError, match="status"):
        InspectResult.from_json({"status": "maybe"})


def _batch(*fds: int) -> InspectBatch:
    return InspectBatch(tuple(InspectFile(fd, ImageFormat.JPEG, 1, 2) for fd in fds))


def test_a_batch_round_trips_json() -> None:
    batch = _batch(5, 9)
    assert batch.to_json() == {
        "files": [
            {"fd": 5, "declared_format": "JPEG", "device": 1, "inode": 2},
            {"fd": 9, "declared_format": "JPEG", "device": 1, "inode": 2},
        ]
    }
    assert InspectBatch.from_json(batch.to_json()) == batch


def test_a_batch_holds_one_to_sixteen_distinct_descriptors() -> None:
    assert MAX_INSPECT_BATCH == 16
    _batch(*range(3, 3 + MAX_INSPECT_BATCH))
    for fds in ((), tuple(range(3, 4 + MAX_INSPECT_BATCH)), (5, 5)):
        with pytest.raises(ValueError, match="1 to 16 files"):
            _batch(*fds)


@pytest.mark.parametrize(
    "request_json",
    [
        {"files": [], "extra": 1},
        {"files": "not a list"},
        {"items": []},
        {"files": ["not an object"]},
        {"files": [{"fd": 5, "declared_format": "JPEG", "device": 1}]},
        {"files": [{"fd": 5, "declared_format": "JPEG", "device": 1, "inode": 2, "path": "x"}]},
        {"files": [{"fd": 2, "declared_format": "JPEG", "device": 1, "inode": 2}]},
        {"files": [{"fd": True, "declared_format": "JPEG", "device": 1, "inode": 2}]},
        {"files": [{"fd": 5, "declared_format": "GIF", "device": 1, "inode": 2}]},
        {"files": [{"fd": 5, "declared_format": "JPEG", "device": -1, "inode": 2}]},
        {"files": [{"fd": 5, "declared_format": "JPEG", "device": 1, "inode": None}]},
    ],
    ids=[
        "extra-key",
        "not-a-list",
        "no-files",
        "not-an-object",
        "missing-field",
        "extra-field",
        "standard-descriptor",
        "boolean-descriptor",
        "unknown-format",
        "negative-device",
        "null-inode",
    ],
)
def test_malformed_requests_are_refused(request_json: JsonObject) -> None:
    with pytest.raises(ValueError):  # noqa: PT011 - any refusal; the message varies
        InspectBatch.from_json(request_json)


def test_events_must_come_in_order_with_their_result() -> None:
    result = InspectResult(status=InspectStatus.OK, oriented_size=Size(3, 2))
    event = inspected_event(1, result)
    assert parse_inspected_event(event, 1) == result
    bad_events: list[JsonObject] = [
        inspected_event(0, result),
        {**event, "extra": 1},
        {"index": True, "result": event["result"]},
        {"index": 1, "result": "ok"},
    ]
    for bad in bad_events:
        with pytest.raises(ValueError, match="expected the result of file 1"):
            parse_inspected_event(bad, 1)
