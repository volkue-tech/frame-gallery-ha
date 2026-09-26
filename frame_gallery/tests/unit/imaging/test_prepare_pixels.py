"""``prepare`` end to end: pixel modes, colour, and alpha (§11.1 steps 4 and 7,
D-122; acceptance D6)."""

from __future__ import annotations

import io
from collections.abc import Callable
from pathlib import Path

import pytest
from PIL import Image, ImageFile, PngImagePlugin

from frame_gallery.domain import BLACK, Rgb, Size
from frame_gallery.imaging import worker_tasks
from frame_gallery.imaging.contract import ColourHandling, ImageFormat, PrepareFailure
from frame_gallery.imaging.sniff import sniff_file
from frame_gallery.imaging.worker_tasks import prepare_image
from tests.support import images
from tests.unit.imaging.prepare_helpers import (
    SMALL,
    Colour,
    assert_ok,
    assert_tv_jpeg,
    mean,
    near,
    output_image,
    request,
)

SIZE = (320, 180)
"""Exactly 16:9 and scaled by 1.2 onto the small canvas: no margins."""

BACKGROUND = Rgb(0x33, 0x66, 0x99)
ORANGE: Colour = (200, 120, 40)
ORANGE_LUMA = 135
"""ITU-R 601 luma of ``ORANGE``: 0.299 * 200 + 0.587 * 120 + 0.114 * 40."""
LEFT_HALF = (96, 108)
RIGHT_HALF = (288, 108)


def _grey(value: int) -> Colour:
    return (value, value, value)


def _png(image: Image.Image) -> Callable[[Path], Path]:
    return lambda directory: images.save_png(image, directory / "source.png")


def _jpeg(image: Image.Image) -> Callable[[Path], Path]:
    return lambda directory: images.save_jpeg(image, directory / "source.jpg")


def _rgb_with_colour_key() -> Image.Image:
    image = Image.new("RGB", SIZE, (1, 2, 3))
    image.paste(ORANGE, (160, 0, 320, 180))
    image.info["transparency"] = (1, 2, 3)
    return image


def _deep_grey(mode: str) -> Image.Image:
    return Image.new(mode, SIZE, 40_000)


def _keyed(
    bit_depth: int, colour_type: int, left: list[int], right: list[int], key: list[int]
) -> Callable[[Path], Path]:
    """A hand-built PNG with a ``tRNS`` colour key (L2-09, L4-04)."""
    data = images.keyed_png(
        SIZE, bit_depth=bit_depth, colour_type=colour_type, left=left, right=right, key=key
    )
    return lambda directory: images.write_bytes(directory / "source.png", data)


def _mpo(first: Image.Image, second: Image.Image) -> Callable[[Path], Path]:
    return lambda directory: images.save_mpo([first, second], directory / "source.jpg")


BLUE: Colour = (30, 40, 220)
KEY_16 = [0x0102, 0x0304, 0x0506]
"""A 16-bit RGB sample whose high bytes, all Pillow keeps, are (1, 3, 5)."""

ORANGE_16 = [0xC800, 0x7800, 0x2800]
"""``ORANGE`` as 16-bit RGB samples."""

MODE_CASES = [
    # (id, writer, declared, colour on the left half, colour on the right half)
    ("1", _png(Image.new("1", SIZE, 1)), ImageFormat.PNG, _grey(255), _grey(255)),
    ("L", _png(Image.new("L", SIZE, 180)), ImageFormat.PNG, _grey(180), _grey(180)),
    (
        "LA",
        _png(images.half_transparent("LA", SIZE, ORANGE)),
        ImageFormat.PNG,
        BACKGROUND.as_tuple(),
        _grey(ORANGE_LUMA),
    ),
    ("RGB", _png(Image.new("RGB", SIZE, ORANGE)), ImageFormat.PNG, ORANGE, ORANGE),
    (
        "RGBA",
        _png(images.half_transparent("RGBA", SIZE, ORANGE)),
        ImageFormat.PNG,
        BACKGROUND.as_tuple(),
        ORANGE,
    ),
    (
        "P",
        _png(images.palette(SIZE, ORANGE, transparent_left=False)),
        ImageFormat.PNG,
        _grey(10),
        ORANGE,
    ),
    (
        "P-transparent",
        _png(images.palette(SIZE, ORANGE, transparent_left=True)),
        ImageFormat.PNG,
        BACKGROUND.as_tuple(),
        ORANGE,
    ),
    ("I;16", _png(_deep_grey("I;16")), ImageFormat.PNG, _grey(156), _grey(156)),
    (
        "RGB-colour-key",
        _png(_rgb_with_colour_key()),
        ImageFormat.PNG,
        BACKGROUND.as_tuple(),
        ORANGE,
    ),
    # Colour keys on the other stored depths (L2-09, L4-04). A bilevel key
    # of 0 hides the black half, 1 the white half.
    (
        "1-colour-key-black",
        _keyed(1, images.GREY, [0], [1], [0]),
        ImageFormat.PNG,
        BACKGROUND.as_tuple(),
        _grey(255),
    ),
    (
        "1-colour-key-white",
        _keyed(1, images.GREY, [0], [1], [1]),
        ImageFormat.PNG,
        _grey(0),
        BACKGROUND.as_tuple(),
    ),
    # A 2-bit key of 3 is the sample that decodes to 255.
    (
        "L;2-colour-key",
        _keyed(2, images.GREY, [3], [1], [3]),
        ImageFormat.PNG,
        BACKGROUND.as_tuple(),
        _grey(85),
    ),
    # 1000 and 1001 both scale to 3: the mask must come from the 16-bit samples.
    (
        "I;16-colour-key",
        _keyed(16, images.GREY, [1000], [1001], [1000]),
        ImageFormat.PNG,
        BACKGROUND.as_tuple(),
        _grey(3),
    ),
    # Pillow decodes 16-bit RGB to 8 bits, so its key is ignored: the keyed
    # half keeps its colour, and a black key never hides the near-black art.
    (
        "RGB;16-colour-key-ignored",
        _keyed(16, images.TRUECOLOUR, KEY_16, ORANGE_16, KEY_16),
        ImageFormat.PNG,
        (1, 3, 5),
        ORANGE,
    ),
    (
        "RGB;16-black-key-ignored",
        _keyed(16, images.TRUECOLOUR, [0x0080] * 3, [0x0080] * 3, [0, 0, 0]),
        ImageFormat.PNG,
        _grey(0),
        _grey(0),
    ),
    # A multi-picture JPEG: the first frame only (L1-04, L2-03, L4-02).
    (
        "MPO",
        _mpo(Image.new("RGB", SIZE, ORANGE), Image.new("RGB", (64, 48), BLUE)),
        ImageFormat.JPEG,
        ORANGE,
        ORANGE,
    ),
    ("JPEG-L", _jpeg(Image.new("L", SIZE, 180)), ImageFormat.JPEG, _grey(180), _grey(180)),
    ("JPEG-RGB", _jpeg(Image.new("RGB", SIZE, ORANGE)), ImageFormat.JPEG, ORANGE, ORANGE),
    (
        "JPEG-CMYK",
        _jpeg(Image.new("CMYK", SIZE, (0, 255, 255, 0))),
        ImageFormat.JPEG,
        (255, 0, 0),
        (255, 0, 0),
    ),
]


@pytest.mark.parametrize(
    ("writer", "declared", "left", "right"),
    [case[1:] for case in MODE_CASES],
    ids=[case[0] for case in MODE_CASES],
)
def test_every_mode_becomes_an_rgb_baseline_jpeg(
    tmp_path: Path,
    writer: Callable[[Path], Path],
    declared: ImageFormat,
    left: Colour,
    right: Colour,
) -> None:
    source = writer(tmp_path)
    req = request(tmp_path, source, declared=declared, canvas=SMALL, background=BACKGROUND)
    result = prepare_image(req)
    assert_ok(result, Path(req.output_path))
    assert_tv_jpeg(Path(req.output_path), SMALL)  # D6
    image = output_image(Path(req.output_path))
    assert near(mean(image, LEFT_HALF), left), mean(image, LEFT_HALF)
    assert near(mean(image, RIGHT_HALF), right), mean(image, RIGHT_HALF)


def test_png_file_modes_are_the_ones_under_test(tmp_path: Path) -> None:
    # Guards the table above: Pillow reopens these files in these modes,
    # with these raw sample layouts and colour keys.
    expected: dict[str, tuple[str, str | None, object]] = {
        "1": ("1", "1", None),
        "L": ("L", "L", None),
        "LA": ("LA", "LA", None),
        "P": ("P", "P", None),
        "I;16": ("I;16", "I;16B", None),
        "1-colour-key-black": ("1", "1", 0),
        "1-colour-key-white": ("1", "1", 255),
        "L;2-colour-key": ("L", "L;2", 3),
        "I;16-colour-key": ("I;16", "I;16B", 1000),
        "RGB;16-colour-key-ignored": ("RGB", "RGB;16B", (0x0102, 0x0304, 0x0506)),
        "RGB;16-black-key-ignored": ("RGB", "RGB;16B", (0, 0, 0)),
    }
    for case in MODE_CASES:
        name = case[0]
        if name in expected:
            with Image.open(case[1](tmp_path)) as image:
                assert isinstance(image, ImageFile.ImageFile)
                mode, rawmode, key = expected[name]
                assert image.mode == mode, name
                assert image.tile[0].args == rawmode, name
                assert image.info.get("transparency") == key, name
    with Image.open(_jpeg(Image.new("CMYK", SIZE))(tmp_path)) as cmyk:
        assert cmyk.mode == "CMYK"


def test_mpo_uses_only_the_first_frame(tmp_path: Path) -> None:
    # The second frame is larger and blue; nothing of it may reach the output.
    source = images.save_mpo(
        [Image.new("RGB", SIZE, ORANGE), Image.new("RGB", (640, 360), BLUE)],
        tmp_path / "camera.jpg",
    )
    with Image.open(source) as check:
        assert check.format == "MPO"
        assert getattr(check, "n_frames", 1) == 2
    assert sniff_file(source) is ImageFormat.JPEG  # the parent accepts it as JPEG
    req = request(tmp_path, source, canvas=SMALL)
    result = prepare_image(req)
    assert_ok(result, Path(req.output_path))
    assert result.source_size == Size(*SIZE)
    assert_tv_jpeg(Path(req.output_path), SMALL)
    image = output_image(Path(req.output_path))
    assert near(mean(image, LEFT_HALF), ORANGE)
    assert near(mean(image, RIGHT_HALF), ORANGE)


def test_mpo_declared_as_png_is_a_mismatch(tmp_path: Path) -> None:
    source = images.save_mpo(
        [Image.new("RGB", SIZE, ORANGE), Image.new("RGB", SIZE, BLUE)], tmp_path / "s.png"
    )
    req = request(tmp_path, source, declared=ImageFormat.PNG, canvas=SMALL)
    result = prepare_image(req)
    assert result.failure is PrepareFailure.FORMAT_MISMATCH
    assert result.detail == "declared PNG, found MPO"


def _colour_case(
    tmp_path: Path,
    image: Image.Image,
    *,
    icc: bytes | None,
    png: bool = False,
    background: Rgb = BLACK,
) -> tuple[ColourHandling | None, Image.Image]:
    if png:
        source = images.save_png(image, tmp_path / "source.png", icc_profile=icc)
        declared = ImageFormat.PNG
    else:
        source = images.save_jpeg(image, tmp_path / "source.jpg", icc_profile=icc)
        declared = ImageFormat.JPEG
    req = request(tmp_path, source, declared=declared, canvas=SMALL, background=background)
    result = prepare_image(req)
    assert_ok(result, Path(req.output_path))
    assert_tv_jpeg(Path(req.output_path), SMALL)
    return result.colour, output_image(Path(req.output_path))


def test_srgb_profile_is_converted(tmp_path: Path) -> None:
    colour, image = _colour_case(tmp_path, Image.new("RGB", SIZE, ORANGE), icc=images.srgb_icc())
    assert colour is ColourHandling.CONVERTED
    assert near(mean(image, RIGHT_HALF), ORANGE)


def test_grey_profile_is_converted_to_rgb(tmp_path: Path) -> None:
    colour, image = _colour_case(tmp_path, Image.new("L", SIZE, 180), icc=images.grey_icc())
    assert colour is ColourHandling.CONVERTED
    assert near(mean(image, RIGHT_HALF), _grey(180))


def test_garbage_profile_is_ignored(tmp_path: Path) -> None:
    colour, image = _colour_case(tmp_path, Image.new("RGB", SIZE, ORANGE), icc=images.GARBAGE_ICC)
    assert colour is ColourHandling.PROFILE_IGNORED
    assert near(mean(image, RIGHT_HALF), ORANGE)


def test_mismatched_profile_is_ignored(tmp_path: Path) -> None:
    # An RGB profile cannot describe a greyscale image.
    colour, image = _colour_case(
        tmp_path, Image.new("L", SIZE, 180), icc=images.srgb_icc(), png=True
    )
    assert colour is ColourHandling.PROFILE_IGNORED
    assert near(mean(image, RIGHT_HALF), _grey(180))


def test_no_profile_is_assumed_srgb(tmp_path: Path) -> None:
    colour, _ = _colour_case(tmp_path, Image.new("RGB", SIZE, ORANGE), icc=None, png=True)
    assert colour is ColourHandling.ASSUMED_SRGB


def test_cmyk_with_a_profile_is_converted(tmp_path: Path) -> None:
    image = Image.new("CMYK", SIZE, (0, 0, 0, 0))
    image.paste((255, 0, 0, 0), (160, 0, 320, 180))
    colour, output = _colour_case(tmp_path, image, icc=images.cmyk_icc())
    assert colour is ColourHandling.CONVERTED
    assert near(mean(output, LEFT_HALF), (255, 255, 255))
    assert near(mean(output, RIGHT_HALF), (0, 0, 0))


def test_cmyk_without_a_profile_is_unmanaged(tmp_path: Path) -> None:
    colour, output = _colour_case(tmp_path, Image.new("CMYK", SIZE, (0, 255, 255, 0)), icc=None)
    assert colour is ColourHandling.CMYK_UNMANAGED
    assert near(mean(output, RIGHT_HALF), (255, 0, 0))


def test_cmyk_with_an_unusable_profile_is_unmanaged(tmp_path: Path) -> None:
    colour, output = _colour_case(
        tmp_path, Image.new("CMYK", SIZE, (0, 255, 255, 0)), icc=images.srgb_icc()
    )
    assert colour is ColourHandling.CMYK_UNMANAGED
    assert near(mean(output, RIGHT_HALF), (255, 0, 0))


def test_alpha_is_composited_after_the_profile_conversion(tmp_path: Path) -> None:
    colour, output = _colour_case(
        tmp_path,
        images.half_transparent("RGBA", SIZE, ORANGE),
        icc=images.srgb_icc(),
        png=True,
        background=BACKGROUND,
    )
    assert colour is ColourHandling.CONVERTED
    assert near(mean(output, LEFT_HALF), BACKGROUND.as_tuple())
    assert near(mean(output, RIGHT_HALF), ORANGE)


def test_grey_alpha_with_a_grey_profile(tmp_path: Path) -> None:
    colour, output = _colour_case(
        tmp_path,
        images.half_transparent("LA", SIZE, (180, 180, 180)),
        icc=images.grey_icc(),
        png=True,
        background=BACKGROUND,
    )
    assert colour is ColourHandling.CONVERTED
    assert near(mean(output, LEFT_HALF), BACKGROUND.as_tuple())
    assert near(mean(output, RIGHT_HALF), _grey(180))


def test_without_littlecms_a_profile_is_ignored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(worker_tasks, "_CMS_AVAILABLE", False)
    rgb_dir, cmyk_dir = tmp_path / "rgb", tmp_path / "cmyk"
    rgb_dir.mkdir()
    cmyk_dir.mkdir()
    colour, _ = _colour_case(rgb_dir, Image.new("RGB", SIZE, ORANGE), icc=images.srgb_icc())
    assert colour is ColourHandling.PROFILE_IGNORED
    colour, _ = _colour_case(
        cmyk_dir, Image.new("CMYK", SIZE, (0, 255, 255, 0)), icc=images.cmyk_icc()
    )
    assert colour is ColourHandling.CMYK_UNMANAGED


def test_corrupt_exif_is_ignored(tmp_path: Path) -> None:
    source = tmp_path / "source.jpg"
    Image.new("RGB", SIZE, ORANGE).save(source, "JPEG", exif=b"Exif\x00\x00II*\x00\xff\xff\x00\x00")
    req = request(tmp_path, source, canvas=SMALL)
    result = prepare_image(req)
    assert_ok(result, Path(req.output_path))
    assert result.orientation == 1


def _raw_profile(text: str) -> PngImagePlugin.PngInfo:
    info = PngImagePlugin.PngInfo()
    info.add_text("Raw profile type exif", text)
    return info


MALFORMED_EXIF: list[tuple[str, str, dict[str, object]]] = [
    # (id, format, save options). With a JFIF density, Pillow does not read
    # the EXIF while opening, so the damage surfaces in the orientation read.
    ("jpeg-density-bad-header", "JPEG", {"dpi": (300, 300), "exif": b"Exif\x00\x00GARBAGE!"}),
    ("jpeg-density-short-header", "JPEG", {"dpi": (300, 300), "exif": b"Exif\x00\x00II*\x00"}),
    ("png-exif-bad-header", "PNG", {"exif": b"Exif\x00\x00NOTATIFF"}),
    ("png-raw-profile-not-hex", "PNG", {"pnginfo": _raw_profile("\nexif\n 10\nzzzz")}),
    ("png-raw-profile-not-tiff", "PNG", {"pnginfo": _raw_profile("\nexif\n 4\n41424344")}),
]


@pytest.mark.parametrize(
    ("kind", "options"),
    [case[1:] for case in MALFORMED_EXIF],
    ids=[case[0] for case in MALFORMED_EXIF],
)
def test_malformed_exif_means_upright(
    tmp_path: Path, kind: str, options: dict[str, object]
) -> None:
    # L4-03: absent or invalid EXIF means orientation 1, never a crash.
    source = tmp_path / f"source.{kind.lower()}"
    Image.new("RGB", SIZE, ORANGE).save(source, kind, **options)
    req = request(tmp_path, source, declared=ImageFormat(kind), canvas=SMALL)
    result = prepare_image(req)
    assert_ok(result, Path(req.output_path))
    assert result.orientation == 1
    assert near(mean(output_image(Path(req.output_path)), RIGHT_HALF), ORANGE)


@pytest.mark.parametrize("value", [0, 9, 65535])
def test_invalid_orientation_means_upright(tmp_path: Path, value: int) -> None:
    source = images.save_jpeg(Image.new("RGB", SIZE, ORANGE), tmp_path / "s.jpg", orientation=value)
    req = request(tmp_path, source, canvas=SMALL)
    result = prepare_image(req)
    assert_ok(result, Path(req.output_path))
    assert result.orientation == 1


def test_non_integer_orientation_means_upright(tmp_path: Path) -> None:
    # A big-endian IFD whose single entry stores tag 0x0112 as ASCII "abc".
    exif = b"Exif\x00\x00MM\x00*\x00\x00\x00\x08\x00\x01\x01\x12\x00\x02"
    exif += b"\x00\x00\x00\x04abc\x00\x00\x00\x00\x00"
    source = tmp_path / "s.jpg"
    Image.new("RGB", SIZE, ORANGE).save(source, "JPEG", exif=exif)
    with Image.open(source) as check:
        assert check.getexif().get(0x0112) == "abc"
    req = request(tmp_path, source, canvas=SMALL)
    result = prepare_image(req)
    assert_ok(result, Path(req.output_path))
    assert result.orientation == 1


# --- step 4 in isolation ------------------------------------------------------


@pytest.mark.parametrize(
    ("mode", "info", "expected"),
    [
        ("1", {}, "L"),
        ("1", {"transparency": 0}, "LA"),
        ("L", {}, "L"),
        ("L", {"transparency": 0}, "LA"),
        ("L", {"transparency": 256}, "L"),
        ("LA", {}, "LA"),
        ("RGB", {}, "RGB"),
        ("RGB", {"transparency": (0, 0, 0)}, "RGBA"),
        ("RGB", {"transparency": (0, 0, 256)}, "RGB"),
        ("RGBA", {}, "RGBA"),
        ("CMYK", {}, "CMYK"),
        ("P", {}, "RGB"),
        ("P", {"transparency": 0}, "RGBA"),
        ("PA", {}, "RGBA"),
        ("I;16", {}, "L"),
        ("I;16", {"transparency": 0}, "LA"),
        ("I;16L", {}, "L"),
        ("I;16B", {}, "L"),
        ("I;16N", {}, "L"),
        ("I", {}, "L"),
        ("I", {"transparency": 0}, "LA"),
        ("La", {}, "LA"),
        ("RGBa", {}, "RGBA"),
        ("RGBX", {}, "RGB"),
        ("YCbCr", {}, "RGB"),
        ("HSV", {}, "RGB"),
    ],
)
def test_normalize_mode(mode: str, info: dict[str, object], expected: str) -> None:
    image = Image.new(mode, (4, 2))
    image.info.update(info)
    normalized = worker_tasks._normalize_mode(image, worker_tasks._colour_key(image))
    assert normalized.mode == expected
    if expected == mode:
        assert normalized is image


def test_deep_grey_is_scaled_to_eight_bits() -> None:
    image = Image.new("I", (3, 1))
    image.putdata([0, 40_000, 65_535])
    normalized = worker_tasks._normalize_mode(image, None)
    assert [normalized.getpixel((x, 0)) for x in range(3)] == [0, 156, 255]


def test_deep_grey_key_is_matched_before_scaling() -> None:
    # 1000 and 1001 both scale to 3; only the keyed sample becomes transparent.
    image = Image.new("I;16", (3, 1))
    image.putdata([1000, 1001, 65_535])
    normalized = worker_tasks._normalize_mode(image, 1000)
    assert normalized.mode == "LA"
    assert [normalized.getpixel((x, 0)) for x in range(3)] == [(3, 0), (3, 255), (255, 255)]


def test_grey_key_becomes_alpha() -> None:
    image = Image.new("L", (3, 1))
    image.putdata([7, 8, 255])
    normalized = worker_tasks._normalize_mode(image, 8)
    assert [normalized.getpixel((x, 0)) for x in range(3)] == [(7, 255), (8, 0), (255, 255)]


@pytest.mark.parametrize(
    ("mode", "info", "expected"),
    [
        ("L", {}, None),
        ("L", {"transparency": 7}, 7),
        ("L", {"transparency": 255}, 255),
        ("L", {"transparency": 256}, None),
        ("L", {"transparency": -1}, None),
        ("L", {"transparency": (1, 2, 3)}, None),
        ("1", {"transparency": 255}, 255),
        ("I;16", {"transparency": 65_535}, 65_535),
        ("I;16", {"transparency": 65_536}, None),
        ("I", {"transparency": 1000}, 1000),
        ("RGB", {"transparency": (1, 2, 3)}, (1, 2, 3)),
        ("RGB", {"transparency": (1, 2, 256)}, None),
        ("RGB", {"transparency": (1, 2)}, None),
        ("RGB", {"transparency": ("a", 2, 3)}, None),
        ("RGB", {"transparency": 5}, None),
        ("P", {"transparency": 0}, None),
        ("LA", {"transparency": 0}, None),
    ],
)
def test_colour_key_in_memory(mode: str, info: dict[str, object], expected: object) -> None:
    # Without a tile, the key is read at the mode's own depth.
    image = Image.new(mode, (2, 2))
    image.info.update(info)
    assert worker_tasks._colour_key(image) == expected


@pytest.mark.parametrize(
    ("bit_depth", "colour_type", "key", "expected"),
    [
        (2, images.GREY, [3], 255),
        (2, images.GREY, [1], 85),
        (2, images.GREY, [4], None),
        (4, images.GREY, [15], 255),
        (4, images.GREY, [2], 34),
        (4, images.GREY, [16], None),
        (8, images.GREY, [200], 200),
        (16, images.GREY, [1000], 1000),
        (8, images.TRUECOLOUR, [1, 2, 3], (1, 2, 3)),
        (16, images.TRUECOLOUR, [0, 0, 0], None),
    ],
)
def test_colour_key_follows_the_stored_depth(
    bit_depth: int, colour_type: int, key: list[int], expected: object
) -> None:
    channels = 3 if colour_type == images.TRUECOLOUR else 1
    data = images.keyed_png(
        (4, 2),
        bit_depth=bit_depth,
        colour_type=colour_type,
        left=[0] * channels,
        right=[1] * channels,
        key=key,
    )
    with Image.open(io.BytesIO(data)) as image:
        assert worker_tasks._colour_key(image) == expected
        image.load()
        # Once decoded, the stored depth is no longer known.
        assert worker_tasks._rawmode(image) == ""


def test_rawmode_is_only_known_for_a_lazily_opened_png() -> None:
    assert worker_tasks._rawmode(Image.new("L", (2, 2))) == ""
    jpeg = images.encoded_jpeg(Image.new("RGB", (8, 8)))
    with Image.open(io.BytesIO(jpeg)) as image:
        assert worker_tasks._rawmode(image) == ""
    with Image.open(io.BytesIO(images.flat_png((2, 2), ORANGE))) as image:
        assert worker_tasks._rawmode(image) == "RGB"


@pytest.mark.parametrize("mode", ["F", "LAB"])
def test_unsupported_modes_are_refused(mode: str) -> None:
    with pytest.raises(worker_tasks._Failed) as caught:
        worker_tasks._normalize_mode(Image.new(mode, (2, 2)), None)
    assert caught.value.failure is PrepareFailure.UNSUPPORTED_MODE
    assert mode in caught.value.detail
