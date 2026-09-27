"""The ``inspect`` worker task: header-only dimensions after EXIF
orientation, for local media (§8.3). Images are synthesized with Pillow."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from frame_gallery.domain import Size
from frame_gallery.imaging.contract import (
    INSPECT_TASK,
    ImageFormat,
    InspectRequest,
    InspectResult,
    InspectStatus,
    PrepareFailure,
)
from frame_gallery.imaging.worker_tasks import inspect_image, inspect_task
from tests.support.images import (
    jpeg_header_only,
    marked,
    oriented_jpeg,
    save_jpeg,
    save_png,
    write_bytes,
)


def _inspect(path: Path, declared: ImageFormat = ImageFormat.JPEG) -> InspectResult:
    return inspect_image(InspectRequest(str(path), declared))


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


def test_the_task_round_trips_json(tmp_path: Path) -> None:
    path = save_jpeg(marked((40, 30)), tmp_path / "a.jpg")
    raw = inspect_task(InspectRequest(str(path), ImageFormat.JPEG).to_json())
    assert raw == {
        "status": "ok",
        "oriented_size": [40, 30],
        "failure": None,
        "detail": None,
    }
    assert InspectResult.from_json(raw).oriented_size == Size(40, 30)


@pytest.mark.parametrize(
    ("setup", "declared", "failure"),
    [
        (lambda d: d / "missing.jpg", ImageFormat.JPEG, PrepareFailure.IO),
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


def test_symlinks_are_refused(tmp_path: Path) -> None:
    target = save_jpeg(marked((8, 8)), tmp_path / "real.jpg")
    link = tmp_path / "link.jpg"
    link.symlink_to(target)
    assert _inspect(link).failure is PrepareFailure.IO


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
    with pytest.raises(ValueError, match="path"):
        InspectRequest.from_json({"declared_format": "JPEG"})
    request = InspectRequest("x.png", ImageFormat.PNG)
    assert InspectRequest.from_json(request.to_json()) == request
