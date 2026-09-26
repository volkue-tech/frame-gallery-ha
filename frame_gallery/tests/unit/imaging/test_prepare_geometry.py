"""``prepare`` end to end: canvas, fit, and orientation (§11.1, §11.2;
acceptance B6, D1-D5)."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image, JpegImagePlugin

from frame_gallery.domain import CANVAS, FitMode, Rgb, Size
from frame_gallery.imaging.contract import ColourHandling, ImageFormat, PrepareStatus
from frame_gallery.imaging.worker_tasks import prepare_image
from tests.support import images
from tests.unit.imaging.prepare_helpers import (
    SMALL,
    assert_ok,
    assert_tv_jpeg,
    extrema_max,
    mean,
    near,
    output_image,
    request,
)

# A 1600 x 1000 source on the 3840 x 2160 canvas: contain scales by 2.16 to
# 3456 x 2160 at x = 192 (both multiples of 16, so JPEG blocks align).
LEFT, RIGHT = 192, 3648
CONTENT_W = RIGHT - LEFT
MARK_W, MARK_H = CONTENT_W // images.MARK_DIVISOR, 2160 // images.MARK_DIVISOR
CORNERS = {
    "red": (LEFT + MARK_W // 2, MARK_H // 2),
    "green": (RIGHT - MARK_W // 2, MARK_H // 2),
    "blue": (LEFT + MARK_W // 2, 2160 - MARK_H // 2),
    "yellow": (RIGHT - MARK_W // 2, 2160 - MARK_H // 2),
}


def _assert_corner_marks(image: Image.Image) -> None:
    for name, centre in CORNERS.items():
        colour = mean(image, centre, radius=8)
        assert near(colour, images.MARKS[name], tolerance=16), (name, colour)


def test_contain_default_keeps_the_whole_artwork(tmp_path: Path) -> None:
    source = images.save_jpeg(images.marked((1600, 1000)), tmp_path / "source.jpg")
    req = request(tmp_path, source)
    result = prepare_image(req)
    output = Path(req.output_path)
    assert_ok(result, output)
    assert result.source_size == Size(1600, 1000)
    assert result.oriented_size == Size(1600, 1000)
    assert result.orientation == 1
    assert result.jpeg_quality == 90
    assert result.colour is ColourHandling.ASSUMED_SRGB
    assert_tv_jpeg(output, CANVAS)  # D1

    image = output_image(output)
    # D3: black margins, exactly outside the content region.
    assert extrema_max(image, (0, 0, LEFT - 2, 2160)) <= 6
    assert extrema_max(image, (RIGHT + 2, 0, 3840, 2160)) <= 6
    # D2/B6: every corner of the artwork is present, so nothing was cropped.
    _assert_corner_marks(image)
    for x in (LEFT + 2, RIGHT - 3):
        assert min(mean(image, (x, 1080), radius=1)) >= 90
    # The content is the bright source, not a margin.
    assert min(mean(image, (1920, 1080))) >= 100


def test_contain_margins_use_the_background_colour(tmp_path: Path) -> None:
    source = images.save_jpeg(images.marked((1600, 1000)), tmp_path / "source.jpg")
    teal = Rgb(0x20, 0x80, 0x90)
    req = request(tmp_path, source, background=teal)
    assert_ok(prepare_image(req), Path(req.output_path))
    image = output_image(Path(req.output_path))
    assert near(mean(image, (96, 1080)), teal.as_tuple(), tolerance=3)
    assert near(mean(image, (3744, 100)), teal.as_tuple(), tolerance=3)
    _assert_corner_marks(image)


def test_contain_panorama_gets_top_and_bottom_margins(tmp_path: Path) -> None:
    source = images.save_jpeg(images.marked((4000, 1000)), tmp_path / "wide.jpg")
    req = request(tmp_path, source)
    assert_ok(prepare_image(req), Path(req.output_path))
    image = output_image(Path(req.output_path))
    # 3840 x 960 at y = 600.
    assert extrema_max(image, (0, 0, 3840, 598)) <= 6
    assert extrema_max(image, (0, 1562, 3840, 2160)) <= 6
    assert near(mean(image, (100, 650)), images.RED, tolerance=16)
    assert near(mean(image, (3740, 1510)), images.YELLOW, tolerance=16)


def test_square_is_centred_with_side_margins(tmp_path: Path) -> None:
    source = images.save_jpeg(images.marked((1200, 1200)), tmp_path / "square.jpg")
    rejected = prepare_image(request(tmp_path, source, output="rejected.jpg"))
    assert rejected.status is PrepareStatus.REJECTED
    req = request(tmp_path, source, landscape_only=False)
    assert_ok(prepare_image(req), Path(req.output_path))
    image = output_image(Path(req.output_path))
    # 2160 x 2160 at x = 840. The edges fall inside 16 px JPEG blocks, so
    # the margins are checked up to the nearest block boundaries.
    assert extrema_max(image, (0, 0, 832, 2160)) <= 6
    assert extrema_max(image, (3008, 0, 3840, 2160)) <= 6
    assert near(mean(image, (840 + 216, 216)), images.RED, tolerance=16)
    assert near(mean(image, (3000 - 216, 2160 - 216)), images.YELLOW, tolerance=16)


def test_exact_16_9_fills_the_canvas(tmp_path: Path) -> None:
    source = images.save_jpeg(images.marked((1920, 1080)), tmp_path / "tv.jpg")
    req = request(tmp_path, source, require_near_16_9=True)
    assert_ok(prepare_image(req), Path(req.output_path))
    image = output_image(Path(req.output_path))
    assert near(mean(image, (100, 100)), images.RED, tolerance=16)
    assert near(mean(image, (3740, 2060)), images.YELLOW, tolerance=16)


def test_cover_crops_only_the_overflowing_axis(tmp_path: Path) -> None:
    # 1600 x 1000 in cover: s = 2.4, keep rows 50-950. The 40-row bands at
    # the top and bottom are cropped; the side bands are kept whole.
    source = images.save_jpeg(images.banded((1600, 1000), 40), tmp_path / "banded.jpg")
    req = request(tmp_path, source, fit_mode=FitMode.COVER)
    assert_ok(prepare_image(req), Path(req.output_path))
    assert_tv_jpeg(Path(req.output_path), CANVAS)
    image = output_image(Path(req.output_path))
    top = mean(image, (1920, 6), radius=4)
    bottom = mean(image, (1920, 2153), radius=4)
    assert not near(top, images.RED, tolerance=60), top
    assert not near(bottom, images.BLUE, tolerance=60), bottom
    assert near(mean(image, (40, 1080)), images.GREEN, tolerance=16)
    assert near(mean(image, (3800, 1080)), images.YELLOW, tolerance=16)
    # No margins: the corner shows the kept side band.
    assert near(mean(image, (2, 2), radius=1), images.GREEN, tolerance=16)


def test_contain_keeps_the_bands_that_cover_would_crop(tmp_path: Path) -> None:
    source = images.save_jpeg(images.banded((1600, 1000), 40), tmp_path / "banded.jpg")
    req = request(tmp_path, source)
    assert_ok(prepare_image(req), Path(req.output_path))
    image = output_image(Path(req.output_path))
    assert near(mean(image, (1920, 20)), images.RED, tolerance=16)
    assert near(mean(image, (1920, 2140)), images.BLUE, tolerance=16)


def test_cover_crops_the_width_of_a_panorama(tmp_path: Path) -> None:
    # 4000 x 1000 in cover: s = 2.16, keep columns 1111-2889 of the source.
    source = images.save_jpeg(images.banded((4000, 1000), 40), tmp_path / "wide.jpg")
    req = request(tmp_path, source, fit_mode=FitMode.COVER)
    assert_ok(prepare_image(req), Path(req.output_path))
    image = output_image(Path(req.output_path))
    assert near(mean(image, (1920, 30)), images.RED, tolerance=16)
    assert near(mean(image, (1920, 2130)), images.BLUE, tolerance=16)
    assert not near(mean(image, (20, 1080)), images.GREEN, tolerance=60)
    assert not near(mean(image, (3820, 1080)), images.YELLOW, tolerance=60)


@pytest.mark.parametrize("orientation", range(1, 9))
def test_orientation_fixtures_follow_the_exif_table(orientation: int) -> None:
    display = Image.new("L", (3, 2))
    display.putdata([10, 20, 30, 40, 50, 60])
    stored = images.to_stored(display, orientation)
    for row in range(stored.height):
        for column in range(stored.width):
            x, y = images.display_position(orientation, (column, row), display.size)
            assert stored.getpixel((column, row)) == display.getpixel((x, y))


@pytest.mark.parametrize("orientation", range(1, 9))
def test_exif_orientation_is_applied(tmp_path: Path, orientation: int) -> None:
    source = images.oriented_jpeg(tmp_path, orientation, (1600, 1000))
    req = request(tmp_path, source)
    result = prepare_image(req)
    assert_ok(result, Path(req.output_path))
    assert result.orientation == orientation
    stored = Size(1000, 1600) if orientation >= 5 else Size(1600, 1000)
    assert result.source_size == stored
    assert result.oriented_size == Size(1600, 1000)
    assert_tv_jpeg(Path(req.output_path), CANVAS)  # D5: no orientation tag survives
    _assert_corner_marks(output_image(Path(req.output_path)))


def test_png_orientation_from_an_exif_chunk_before_the_pixels(tmp_path: Path) -> None:
    exif = Image.Exif()
    exif[0x0112] = 6
    source = tmp_path / "s.png"
    images.to_stored(images.marked((1600, 1000)), 6).save(source, "PNG", exif=exif.tobytes())
    req = request(tmp_path, source, declared=ImageFormat.PNG)
    result = prepare_image(req)
    assert_ok(result, Path(req.output_path))
    assert result.orientation == 6
    assert result.source_size == Size(1000, 1600)
    _assert_corner_marks(output_image(Path(req.output_path)))


def test_camera_exif_passes_the_pre_scan_and_is_read(tmp_path: Path) -> None:
    # IFD0, Exif (60 KiB MakerNote), GPS, Interoperability, and IFD1 (P1).
    stored = images.to_stored(images.marked((1600, 1000)), 6)
    exif = images.exif_segments(images.camera_exif(orientation=6))
    data = images.with_segments(images.encoded_jpeg(stored, quality=92), exif)
    source = images.write_bytes(tmp_path / "camera.jpg", data)
    req = request(tmp_path, source)
    result = prepare_image(req)
    assert_ok(result, Path(req.output_path))
    assert result.orientation == 6
    assert result.source_size == Size(1000, 1600)
    _assert_corner_marks(output_image(Path(req.output_path)))


@pytest.mark.parametrize(("kind", "compressed"), [(b"zTXt", True), (b"iTXt", False)])
def test_png_orientation_from_a_raw_exif_profile(
    tmp_path: Path, kind: bytes, compressed: bool
) -> None:
    # ImageMagick's "Raw profile type exif" text chunk, before the pixels (P1).
    buffer = io.BytesIO()
    images.to_stored(images.marked((1600, 1000)), 6).save(buffer, "PNG")
    png = buffer.getvalue()
    text = images.raw_profile_text(images.camera_exif(orientation=6))
    chunk = images.raw_profile_chunk(kind, text, compressed=compressed)
    ihdr_end = len(images.PNG_SIGNATURE) + 25
    source = images.write_bytes(tmp_path / "s.png", png[:ihdr_end] + chunk + png[ihdr_end:])
    req = request(tmp_path, source, declared=ImageFormat.PNG)
    result = prepare_image(req)
    assert_ok(result, Path(req.output_path))
    assert result.orientation == 6
    assert result.source_size == Size(1000, 1600)
    _assert_corner_marks(output_image(Path(req.output_path)))


def test_mpo_primary_image_is_prepared(tmp_path: Path) -> None:
    # A Pillow-written multi-picture JPEG: its MPF index passes the pre-scan.
    frames = [images.marked((1600, 1000)), Image.new("RGB", (160, 100), (0, 0, 0))]
    source = images.save_mpo(frames, tmp_path / "s.jpg")
    req = request(tmp_path, source)
    result = prepare_image(req)
    assert_ok(result, Path(req.output_path))
    assert result.source_size == Size(1600, 1000)
    _assert_corner_marks(output_image(Path(req.output_path)))


@pytest.mark.parametrize("orientation", [5, 6, 7, 8])
def test_cover_crops_in_source_coordinates_for_swapped_orientations(
    tmp_path: Path, orientation: int
) -> None:
    display = images.banded((1600, 1000), 40)
    source = images.save_jpeg(
        images.to_stored(display, orientation), tmp_path / "s.jpg", orientation=orientation
    )
    req = request(tmp_path, source, fit_mode=FitMode.COVER)
    assert_ok(prepare_image(req), Path(req.output_path))
    image = output_image(Path(req.output_path))
    assert not near(mean(image, (1920, 6)), images.RED, tolerance=60)
    assert near(mean(image, (40, 1080)), images.GREEN, tolerance=16)
    assert near(mean(image, (3800, 1080)), images.YELLOW, tolerance=16)


class _DraftSpy:
    def __init__(self) -> None:
        self.calls: list[tuple[tuple[int, int] | None, tuple[int, int]]] = []


@pytest.fixture
def draft_spy(monkeypatch: pytest.MonkeyPatch) -> _DraftSpy:
    spy = _DraftSpy()
    original = JpegImagePlugin.JpegImageFile.draft

    def draft(
        self: JpegImagePlugin.JpegImageFile, mode: str | None, size: tuple[int, int] | None
    ) -> object:
        outcome = original(self, mode, size)
        spy.calls.append((size, self.size))
        return outcome

    monkeypatch.setattr(JpegImagePlugin.JpegImageFile, "draft", draft)
    return spy


def test_jpeg_draft_reduces_to_the_fitted_size(tmp_path: Path, draft_spy: _DraftSpy) -> None:
    source = images.save_jpeg(images.marked((1600, 900)), tmp_path / "big.jpg")
    req = request(tmp_path, source, canvas=SMALL)
    assert_ok(prepare_image(req), Path(req.output_path))
    # The fitted size is 384 x 216; the DCT scale 1/4 gives 400 x 225.
    assert draft_spy.calls == [((384, 216), (400, 225))]
    image = output_image(Path(req.output_path))
    assert near(mean(image, (38, 21), radius=3), images.RED, tolerance=20)


def test_jpeg_draft_uses_swapped_axes_for_orientation_6(
    tmp_path: Path, draft_spy: _DraftSpy
) -> None:
    source = images.oriented_jpeg(tmp_path, 6, (1600, 900))
    req = request(tmp_path, source, canvas=SMALL)
    result = prepare_image(req)
    assert_ok(result, Path(req.output_path))
    assert result.source_size == Size(900, 1600)
    assert draft_spy.calls == [((216, 384), (225, 400))]
    image = output_image(Path(req.output_path))
    assert near(mean(image, (38, 21), radius=3), images.RED, tolerance=20)
    assert near(mean(image, (345, 194), radius=3), images.YELLOW, tolerance=20)


def test_jpeg_draft_for_cover_keeps_the_cover_scale(tmp_path: Path, draft_spy: _DraftSpy) -> None:
    source = images.save_jpeg(images.banded((1600, 1000), 40), tmp_path / "big.jpg")
    req = request(tmp_path, source, canvas=SMALL, fit_mode=FitMode.COVER)
    assert_ok(prepare_image(req), Path(req.output_path))
    # Cover scale 0.24: the whole source at that scale is 384 x 240.
    assert draft_spy.calls == [((384, 240), (400, 250))]
    image = output_image(Path(req.output_path))
    assert not near(mean(image, (192, 1), radius=1), images.RED, tolerance=60)
    assert near(mean(image, (4, 108), radius=2), images.GREEN, tolerance=20)


def test_upscaled_jpeg_is_not_reduced(tmp_path: Path, draft_spy: _DraftSpy) -> None:
    source = images.save_jpeg(images.marked((1600, 1000)), tmp_path / "s.jpg")
    req = request(tmp_path, source)
    assert_ok(prepare_image(req), Path(req.output_path))
    assert draft_spy.calls == [((3456, 2160), (1600, 1000))]


def test_png_is_never_drafted(tmp_path: Path, draft_spy: _DraftSpy) -> None:
    source = images.save_png(images.marked((1600, 900)), tmp_path / "s.png")
    req = request(tmp_path, source, declared=ImageFormat.PNG, canvas=SMALL)
    assert_ok(prepare_image(req), Path(req.output_path))
    assert draft_spy.calls == []


def test_multi_frame_png_uses_the_first_frame(tmp_path: Path) -> None:
    frames = [Image.new("RGB", (320, 180), colour) for colour in (images.RED, images.GREEN)]
    source = images.save_apng(frames, tmp_path / "anim.png")
    with Image.open(source) as check:
        assert getattr(check, "n_frames", 1) == 2
    req = request(tmp_path, source, declared=ImageFormat.PNG, canvas=SMALL)
    assert_ok(prepare_image(req), Path(req.output_path))
    image = output_image(Path(req.output_path))
    assert near(mean(image, (192, 108)), images.RED, tolerance=10)


@pytest.mark.parametrize("fit_mode", list(FitMode))
def test_output_is_deterministic(tmp_path: Path, fit_mode: FitMode) -> None:
    source = images.oriented_jpeg(tmp_path, 6, (1600, 1000))
    first = request(tmp_path, source, fit_mode=fit_mode, output="first.jpg")
    second = request(tmp_path, source, fit_mode=fit_mode, output="second.jpg")
    one, two = prepare_image(first), prepare_image(second)
    assert one == two
    assert one.status is PrepareStatus.OK
    assert Path(first.output_path).read_bytes() == Path(second.output_path).read_bytes()
