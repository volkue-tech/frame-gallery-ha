"""Worker-side image tasks (§11.1). The only module that imports Pillow.

``prepare`` runs steps 2 to 9 of the §11.1 pipeline on one source file whose
path the parent chose. A bad image never raises: each expected problem
becomes a ``rejected`` or ``failed`` :class:`PrepareResult`. An invalid
request raises ``ValueError``, which the executor reports as a worker error.

Failure mapping (all ``detail`` strings are short and log-safe):

- the source cannot be opened, is a symlink, or is not a regular file: ``io``;
- Pillow cannot identify the file as JPEG or PNG, or it is the other of the
  two formats: ``format_mismatch``;
- a dimension, pixel, or size limit, Pillow's decompression-bomb check, or a
  cap of the header pre-scan (``source_scan``, including the caps on the
  TIFF structures of EXIF and MPF metadata), before decoding: ``limits``;
- a malformed or truncated file while its header is pre-scanned or its
  header or pixels are read: ``decode``;
- a pixel mode without a safe RGB conversion: ``unsupported_mode``;
- a failure while normalizing, resizing, orienting, or composing: ``render``;
- a JPEG encoder failure: ``encode``; still over the byte limit after the
  quality-85 re-encode: ``output_too_large``;
- the output cannot be created exclusively or written: ``io``.

Pillow's global ``MAX_IMAGE_PIXELS`` is set to :data:`MAX_JPEG_PIXELS` at the
start of every call (§11.3 step 7), so it holds whichever process imports
this module; in Phase 2 that is the parent (in-process executor, D-139).
"""

from __future__ import annotations

import contextlib
import errno
import functools
import io
import os
import stat
import struct
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Final

from PIL import Image, ImageCms, ImageFile, UnidentifiedImageError, features

from frame_gallery.domain import FitMode, Size
from frame_gallery.imaging.contract import (
    JPEG_FALLBACK_QUALITY,
    JPEG_QUALITY,
    MAX_DIMENSION,
    MAX_JPEG_PIXELS,
    MAX_OUTPUT_BYTES,
    MAX_PNG_PIXELS,
    MAX_SOURCE_BYTES,
    ColourHandling,
    ImageFormat,
    InspectRequest,
    InspectResult,
    InspectStatus,
    PrepareFailure,
    PrepareRequest,
    PrepareResult,
    PrepareStatus,
)
from frame_gallery.imaging.fit import contain_layout, cover_crop, scaled_source
from frame_gallery.imaging.source_scan import SourceLimitError, SourceScanError, scan_source
from frame_gallery.isolation.executor import JsonObject
from frame_gallery.selection.geometry import check_rendition

_CMS_AVAILABLE = features.check_module("littlecms2")
"""Whether ImageCms can convert profiles. The pinned wheels bundle LittleCMS;
without it, an embedded profile is ignored (D-122)."""

_FORMATS: Final = (ImageFormat.JPEG.value, ImageFormat.PNG.value)
_ACCEPTED_FORMATS: Final = {
    ImageFormat.JPEG: frozenset({"JPEG", "MPO"}),
    ImageFormat.PNG: frozenset({"PNG"}),
}
"""Pillow reports a JPEG whose MPF index lists more than one image as
``MPO`` (CIPA DC-007), as cameras write for previews. It stays on the first
frame, the primary JPEG, which is the only one limited and decoded (step 3):
nothing here seeks to another frame."""

_SOURCE_FLAGS: Final = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
"""``O_NONBLOCK`` keeps a FIFO from blocking the open; ``fstat`` refuses it."""

_OUTPUT_FLAGS: Final = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
_OUTPUT_MODE: Final = 0o640

_ORIENTATION_TAG: Final = 0x0112
_EXIF_ERRORS: Final = (
    SyntaxError,
    ValueError,
    TypeError,
    KeyError,
    IndexError,
    ArithmeticError,
    EOFError,
    struct.error,
    OSError,
)
"""What Pillow's EXIF reader raises for damaged metadata: an invalid TIFF
header (``SyntaxError``), a short one (``struct.error``), or non-hex text in a
PNG "Raw profile type exif" chunk (``ValueError``), among others."""

_TRANSPOSE: Final = {
    2: Image.Transpose.FLIP_LEFT_RIGHT,
    3: Image.Transpose.ROTATE_180,
    4: Image.Transpose.FLIP_TOP_BOTTOM,
    5: Image.Transpose.TRANSPOSE,
    6: Image.Transpose.ROTATE_270,
    7: Image.Transpose.TRANSVERSE,
    8: Image.Transpose.ROTATE_90,
}
"""How to display a stored image for each EXIF orientation (1 needs nothing)."""

_KEPT_MODES: Final = frozenset({"L", "LA", "RGB", "RGBA", "CMYK"})
_COLOUR_KEY_ALPHA: Final = {"L": "LA", "RGB": "RGBA"}
"""A PNG ``tRNS`` colour key on L or RGB becomes a real alpha band."""

_DEEP_GREY_MODES: Final = frozenset({"I;16", "I;16L", "I;16B", "I;16N", "I"})
"""Scaled linearly to 8-bit ``L`` (value / 256, clipped)."""

_GREY_KEY_MODES: Final = frozenset({"1", "L"})
_COLOUR_KEY_MODES: Final = _GREY_KEY_MODES | _DEEP_GREY_MODES | {"RGB"}
_SUB_BYTE_GREY_MAX: Final = {"L;2": 3, "L;4": 15}
"""The largest stored sample of 2- and 4-bit grey PNGs, which Pillow scales
to 0-255 while it reports their ``tRNS`` key unscaled."""

_SIXTEEN_BIT_RGB: Final = "RGB;16B"
_SIXTEEN_BIT_VALUES: Final = 1 << 16

type ColourKey = int | tuple[int, int, int]
"""A ``tRNS`` colour key in the decoded samples' scale: grey or RGB."""

_SIMPLE_TARGETS: Final = {
    "La": "LA",
    "RGBa": "RGBA",
    "RGBX": "RGB",
    "YCbCr": "RGB",
    "HSV": "RGB",
}
"""Exact conversions. Neither JPEG nor PNG decodes to the last three; any
other mode (``F``, ``LAB``, ...) is refused as unsupported."""

_WITHOUT_ALPHA: Final = {"LA": "L", "RGBA": "RGB"}
_DECODE_ERRORS: Final = (OSError, ValueError, SyntaxError, EOFError, struct.error)
_DETAIL_LIMIT: Final = 120


class _Failed(Exception):
    """Ends the pipeline with a ``failed`` result."""

    def __init__(self, failure: PrepareFailure, detail: str) -> None:
        super().__init__(detail)
        self.failure = failure
        self.detail = detail


@dataclass(slots=True)
class _Known:
    """What the pipeline has learned so far; reported with a failure."""

    source_size: Size | None = None
    oriented_size: Size | None = None
    orientation: int | None = None


def _describe(exc: BaseException) -> str:
    """``Type: message`` on one line, cut to a log-safe length."""
    text = f"{type(exc).__name__}: {exc}".replace("\n", " ").replace("\r", " ")
    return text[:_DETAIL_LIMIT]


def _errno_name(exc: OSError) -> str:
    return errno.errorcode.get(exc.errno or 0, "error")


def prepare_task(payload: JsonObject) -> JsonObject:
    """The ``prepare`` task: verify, decode, fit, and encode one image."""
    request = PrepareRequest.from_json(payload)
    return prepare_image(request).to_json()


def inspect_task(payload: JsonObject) -> JsonObject:
    """The ``inspect`` task: one library file's dimensions after EXIF
    orientation, from its header only (§8.3)."""
    request = InspectRequest.from_json(payload)
    return inspect_image(request).to_json()


def inspect_image(request: InspectRequest) -> InspectResult:
    """Open, pre-scan, identify, and limit-check one file, as ``prepare``
    does before decoding, and read its orientation. No pixels are decoded."""
    Image.MAX_IMAGE_PIXELS = MAX_JPEG_PIXELS
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with (
                _open_source(request.path) as file,
                contextlib.closing(_open_image(file, request.declared_format)) as image,
            ):
                size = _check_limits(image, request.declared_format)
                orientation = _orientation(image)
    except _Failed as failed:
        return InspectResult(
            status=InspectStatus.FAILED, failure=failed.failure, detail=failed.detail
        )
    oriented = size.transposed() if orientation >= 5 else size
    return InspectResult(status=InspectStatus.OK, oriented_size=oriented)


def prepare_image(
    request: PrepareRequest, *, max_output_bytes: int = MAX_OUTPUT_BYTES
) -> PrepareResult:
    """Run §11.1 steps 2-9. ``max_output_bytes`` is injectable for tests."""
    Image.MAX_IMAGE_PIXELS = MAX_JPEG_PIXELS
    known = _Known()
    try:
        with warnings.catch_warnings():
            # Pillow reports damaged metadata (e.g. corrupt EXIF) as a plain
            # UserWarning: not a failure. The decompression-bomb warning is
            # (D-121). Other categories keep the caller's configuration.
            warnings.simplefilter("ignore", UserWarning)
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            return _prepare(request, known, max_output_bytes)
    except _Failed as failed:
        return PrepareResult(
            status=PrepareStatus.FAILED,
            source_size=known.source_size,
            oriented_size=known.oriented_size,
            orientation=known.orientation,
            failure=failed.failure,
            detail=failed.detail,
        )


def _prepare(request: PrepareRequest, known: _Known, max_output_bytes: int) -> PrepareResult:
    # Leaving the block calls Image.close(), which releases the decoded
    # source before the colour, compose, and encode steps (a plain ``with``
    # on the image would only drop its file pointer).
    with (
        _open_source(request.source_path) as file,
        contextlib.closing(_open_image(file, request.declared_format)) as image,
    ):
        source_size = _check_limits(image, request.declared_format)
        known.source_size = source_size
        orientation = _orientation(image)
        known.orientation = orientation
        swapped = orientation >= 5
        oriented_size = source_size.transposed() if swapped else source_size
        known.oriented_size = oriented_size

        # Verify the reason the candidate was chosen before decoding anything.
        rejection = check_rendition(
            oriented_size,
            fit_mode=request.fit_mode,
            landscape_only=request.landscape_only,
            require_near_16_9=request.require_near_16_9,
            canvas=request.canvas,
        )
        if rejection is not None:
            return PrepareResult(
                status=PrepareStatus.REJECTED,
                source_size=source_size,
                oriented_size=oriented_size,
                orientation=orientation,
                rejection=rejection,
                detail=f"oriented size {oriented_size.width}x{oriented_size.height}",
            )

        # Fit in source orientation: centred crops and uniform scaling commute
        # with the EXIF transform, so the canvas axes are swapped for 5-8.
        canvas_in_source = request.canvas.transposed() if swapped else request.canvas
        icc_profile = _icc_profile(image)
        colour_key = _colour_key(image)  # needs the undecoded image
        _decode(image, request, source_size, canvas_in_source)
        fitted = _render(image, request.fit_mode, source_size, canvas_in_source, colour_key)
    oriented = _orient(fitted, orientation)
    rgb, alpha, colour = _to_srgb(oriented, icc_profile)
    canvas = _compose(rgb, alpha, request)
    data, quality = _encode_bounded(canvas, max_output_bytes)
    _write_exclusive(request.output_path, data)
    return PrepareResult(
        status=PrepareStatus.OK,
        source_size=source_size,
        oriented_size=oriented_size,
        orientation=orientation,
        output_bytes=len(data),
        jpeg_quality=quality,
        colour=colour,
    )


def _open_source(path: str) -> IO[bytes]:
    try:
        fd = os.open(path, _SOURCE_FLAGS)
    except OSError as exc:
        detail = f"cannot open the source ({_errno_name(exc)})"
        raise _Failed(PrepareFailure.IO, detail) from None
    try:
        # fstat before wrapping the descriptor: a file object refuses a
        # directory with its own error.
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise _Failed(PrepareFailure.IO, "the source is not a regular file")
        if info.st_size > MAX_SOURCE_BYTES:
            detail = f"the source exceeds {MAX_SOURCE_BYTES} bytes"
            raise _Failed(PrepareFailure.LIMITS, detail)
        return os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise


def _open_image(file: IO[bytes], declared: ImageFormat) -> Image.Image:
    """Pre-scan the header, then identify the file lazily (step 2): no pixel
    data is read here. The pre-scan bounds what Pillow's header readers
    parse (L4-01), including the EXIF and MPF metadata that Pillow reads as
    TIFF directories while it opens the file or reads the orientation (P1);
    its caps are in ``source_scan``."""
    try:
        scan_source(file)
        image = Image.open(file, formats=_FORMATS)
    except SourceLimitError as exc:
        raise _Failed(PrepareFailure.LIMITS, str(exc)[:_DETAIL_LIMIT]) from None
    except SourceScanError as exc:
        raise _Failed(PrepareFailure.DECODE, str(exc)[:_DETAIL_LIMIT]) from None
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise _Failed(PrepareFailure.LIMITS, "pixel limit exceeded") from None
    except UnidentifiedImageError:
        # Pillow could not identify it as JPEG or PNG: not the declared format.
        detail = f"not a readable {declared.value} file"
        raise _Failed(PrepareFailure.FORMAT_MISMATCH, detail) from None
    except _DECODE_ERRORS as exc:
        raise _Failed(PrepareFailure.DECODE, _describe(exc)) from None
    if image.format not in _ACCEPTED_FORMATS[declared]:
        detail = f"declared {declared.value}, found {image.format}"
        raise _Failed(PrepareFailure.FORMAT_MISMATCH, detail)
    return image


def _check_limits(image: Image.Image, declared: ImageFormat) -> Size:
    """The D-121 limits, from the header only (before decoding)."""
    width, height = image.size
    if width <= 0 or height <= 0:
        raise _Failed(PrepareFailure.DECODE, "the header declares a zero dimension")
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        detail = f"{width}x{height} exceeds {MAX_DIMENSION} px per side"
        raise _Failed(PrepareFailure.LIMITS, detail)
    limit = MAX_JPEG_PIXELS if declared is ImageFormat.JPEG else MAX_PNG_PIXELS
    if width * height > limit:
        detail = f"{width}x{height} exceeds {limit} pixels for {declared.value}"
        raise _Failed(PrepareFailure.LIMITS, detail)
    return Size(width, height)


def _orientation(image: Image.Image) -> int:
    """The EXIF orientation; absent or invalid values mean 1, and so does
    EXIF that cannot be parsed (L4-03): a decodable artwork is not lost to
    damaged metadata.

    The base-class reader parses only the metadata that opening the file has
    already read. The PNG plugin's own ``getexif`` would decode the whole
    image to look for an ``eXIf`` chunk after the pixel data, before the
    limits and the verification (§11.1); such a late chunk is ignored.
    """
    try:
        value = Image.Image.getexif(image).get(_ORIENTATION_TAG)
    except _EXIF_ERRORS:
        return 1
    if isinstance(value, int) and 1 <= value <= 8:
        return int(value)
    return 1


def _icc_profile(image: Image.Image) -> bytes | None:
    profile = image.info.get("icc_profile")
    if isinstance(profile, bytes) and profile:
        return profile
    return None


def _decode(
    image: Image.Image, request: PrepareRequest, source_size: Size, canvas_in_source: Size
) -> None:
    """Decode the first frame (step 3), reduced by the JPEG DCT scaling.

    The draft request is the fitted size in source orientation (for ``cover``,
    the whole source at the cover scale). Pillow picks the largest reduction
    whose result still covers it, so the fit never has to upscale more.
    """
    if request.declared_format is ImageFormat.JPEG:
        if request.fit_mode is FitMode.CONTAIN:
            needed = contain_layout(source_size, canvas_in_source).scaled
        else:
            needed = scaled_source(source_size, cover_crop(source_size, canvas_in_source).scale)
        image.draft(image.mode, (needed.width, needed.height))
    try:
        image.load()
    except _DECODE_ERRORS as exc:
        raise _Failed(PrepareFailure.DECODE, _describe(exc)) from None


def _eight_bit(value: Image.ImagePointTransform) -> Image.ImagePointTransform:
    return value / 256


def _rawmode(image: Image.Image) -> str:
    """How a lazily opened PNG stores its samples (its tile's raw mode), or
    ``""`` once decoded and for other images."""
    tile = image.tile if isinstance(image, ImageFile.ImageFile) else []
    args = tile[0].args if len(tile) == 1 else None
    return args if isinstance(args, str) else ""


def _colour_key(image: Image.Image) -> ColourKey | None:
    """The PNG ``tRNS`` colour key in the scale of the decoded samples, or
    ``None`` (§11.1 step 7, D-122; L2-09, L4-04).

    Call it before decoding: the tile's raw mode is the only record of the
    stored bit depth, and Pillow reports the key in the stored scale (a
    bilevel key already as 0 or 255). So:

    - a 2- or 4-bit grey key is scaled to 0-255 like the samples;
    - a 16-bit grey key is kept, and the alpha mask is built from the 16-bit
      samples before they are scaled to 8 bits;
    - a 16-bit RGB key is ignored: Pillow decodes those samples to 8 bits,
      and comparing the key with them could hide opaque artwork;
    - a key outside the stored sample range is ignored, so the artwork
      stays opaque.

    Palette transparency is not a colour key; its conversion handles it.
    """
    key = image.info.get("transparency")
    mode = image.mode
    if key is None or mode not in _COLOUR_KEY_MODES:
        return None
    rawmode = _rawmode(image)
    if mode == "RGB":
        if (
            rawmode == _SIXTEEN_BIT_RGB
            or not isinstance(key, tuple)
            or len(key) != 3
            or not all(isinstance(value, int) and 0 <= value <= 0xFF for value in key)
        ):
            return None
        return (key[0], key[1], key[2])
    if not isinstance(key, int):
        return None
    if mode in _DEEP_GREY_MODES:
        return key if 0 <= key < _SIXTEEN_BIT_VALUES else None
    top = _SUB_BYTE_GREY_MAX.get(rawmode, 0xFF)
    return key * 0xFF // top if 0 <= key <= top else None


def _target_mode(image: Image.Image, *, keyed: bool) -> str | None:
    """The mode that step 4 converts ``image`` to, or ``None`` if unsupported.
    ``keyed``: the image has a usable colour key (:func:`_colour_key`)."""
    mode = image.mode
    if mode in _KEPT_MODES:
        return _COLOUR_KEY_ALPHA.get(mode, mode) if keyed else mode
    if mode in ("P", "PA"):
        return "RGBA" if "transparency" in image.info or mode == "PA" else "RGB"
    if mode in _DEEP_GREY_MODES or mode == "1":
        return "LA" if keyed else "L"
    return _SIMPLE_TARGETS.get(mode)


def _normalize_mode(image: Image.Image, colour_key: ColourKey | None) -> Image.Image:
    """Step 4: bring every mode to L, LA, RGB, RGBA, or CMYK before resizing.

    ``colour_key`` comes from :func:`_colour_key`. For 8-bit RGB it equals
    ``info["transparency"]``, which Pillow's own conversion applies.
    """
    target = _target_mode(image, keyed=colour_key is not None)
    if target is None:
        raise _Failed(PrepareFailure.UNSUPPORTED_MODE, f"unsupported pixel mode {image.mode}")
    if target == image.mode:
        return image
    if image.mode in _DEEP_GREY_MODES:
        return _deep_grey(image, colour_key)
    if isinstance(colour_key, int):
        return _keyed_grey(image, colour_key)
    return image.convert(target)


def _deep_grey(image: Image.Image, colour_key: ColourKey | None) -> Image.Image:
    """16-bit grey as 8-bit ``L``, or as ``LA`` with the colour key matched
    against the 16-bit samples: two samples that scale to the same 8-bit
    value stay apart."""
    wide = image.convert("I")
    grey = wide.point(_eight_bit).convert("L")
    if not isinstance(colour_key, int):
        return grey
    table = [0xFF] * _SIXTEEN_BIT_VALUES
    table[colour_key] = 0
    return Image.merge("LA", (grey, wide.point(table, "L")))


def _keyed_grey(image: Image.Image, colour_key: int) -> Image.Image:
    """Bilevel or 8-bit grey with a colour key (in 0-255) as ``LA``."""
    grey = image.convert("L") if image.mode == "1" else image
    alpha = grey.point(lambda value: 0 if value == colour_key else 0xFF)
    return Image.merge("LA", (grey, alpha))


def _render(
    image: Image.Image,
    fit_mode: FitMode,
    source_size: Size,
    canvas_in_source: Size,
    colour_key: ColourKey | None,
) -> Image.Image:
    """Steps 4-5: normalize, then crop (``cover``) and resize with Lanczos.

    ``cover`` crops in source coordinates of the decoded (possibly reduced)
    image and resizes in the same step. Every buffer from here on is at most
    canvas-sized.
    """
    try:
        normalized = _normalize_mode(image, colour_key)
        if fit_mode is FitMode.COVER:
            box = cover_crop(Size(*normalized.size), canvas_in_source).box
            target = canvas_in_source
            return normalized.resize(
                (target.width, target.height), Image.Resampling.LANCZOS, box=box
            )
        target = contain_layout(source_size, canvas_in_source).scaled
        return normalized.resize((target.width, target.height), Image.Resampling.LANCZOS)
    except (OSError, ValueError) as exc:
        raise _Failed(PrepareFailure.RENDER, _describe(exc)) from None


def _orient(image: Image.Image, orientation: int) -> Image.Image:
    """Step 6: apply the EXIF orientation to the fitted image."""
    method = _TRANSPOSE.get(orientation)
    if method is None:
        return image
    try:
        return image.transpose(method)
    except (OSError, ValueError) as exc:
        raise _Failed(PrepareFailure.RENDER, _describe(exc)) from None


@functools.cache
def _srgb_profile() -> ImageCms.ImageCmsProfile:
    return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))


def _to_srgb(
    image: Image.Image, icc_profile: bytes | None
) -> tuple[Image.Image, Image.Image | None, ColourHandling]:
    """Step 7 (D-122): the colour as sRGB ``RGB``, the alpha band if any, and
    how the colour was handled. Alpha is kept apart from the colour transform.
    """
    alpha = image.getchannel("A") if image.mode in _WITHOUT_ALPHA else None
    colour = image.convert(_WITHOUT_ALPHA[image.mode]) if alpha is not None else image
    if icc_profile is not None and _CMS_AVAILABLE:
        converted = _convert_profile(colour, icc_profile)
        if converted is not None:
            return converted, alpha, ColourHandling.CONVERTED
    if colour.mode == "CMYK":
        handling = ColourHandling.CMYK_UNMANAGED
    elif icc_profile is not None:
        handling = ColourHandling.PROFILE_IGNORED
    else:
        handling = ColourHandling.ASSUMED_SRGB
    return colour.convert("RGB"), alpha, handling


def _convert_profile(image: Image.Image, icc_profile: bytes) -> Image.Image | None:
    """Convert ``image`` (L, RGB, or CMYK) to sRGB ``RGB``; ``None`` if the
    profile is unusable for it."""
    try:
        source_profile = ImageCms.getOpenProfile(io.BytesIO(icc_profile))
        return ImageCms.profileToProfile(image, source_profile, _srgb_profile(), outputMode="RGB")
    except ImageCms.PyCMSError:
        return None


def _compose(rgb: Image.Image, alpha: Image.Image | None, request: PrepareRequest) -> Image.Image:
    """Step 8: a brand-new canvas, so no metadata survives. ``contain`` is
    centred on the background; ``cover`` fills it exactly. Alpha composites
    over the background here, after the colour conversion."""
    canvas_size = request.canvas
    try:
        canvas = Image.new(
            "RGB", (canvas_size.width, canvas_size.height), request.background.as_tuple()
        )
        offset = ((canvas_size.width - rgb.width) // 2, (canvas_size.height - rgb.height) // 2)
        canvas.paste(rgb, offset, alpha)
    except (OSError, ValueError) as exc:
        raise _Failed(PrepareFailure.RENDER, _describe(exc)) from None
    return canvas


def _encode(canvas: Image.Image, quality: int) -> bytes:
    buffer = io.BytesIO()
    try:
        canvas.save(
            buffer,
            format="JPEG",
            quality=quality,
            optimize=False,
            progressive=False,
            subsampling="4:2:0",
        )
    except (OSError, ValueError) as exc:
        raise _Failed(PrepareFailure.ENCODE, _describe(exc)) from None
    return buffer.getvalue()


def _encode_bounded(canvas: Image.Image, max_output_bytes: int) -> tuple[bytes, int]:
    """Step 9: a baseline JPEG at quality 90, re-encoded once at 85 if it
    exceeds ``max_output_bytes`` (Q-05)."""
    data = _encode(canvas, JPEG_QUALITY)
    if len(data) <= max_output_bytes:
        return data, JPEG_QUALITY
    data = _encode(canvas, JPEG_FALLBACK_QUALITY)
    if len(data) <= max_output_bytes:
        return data, JPEG_FALLBACK_QUALITY
    detail = f"{len(data)} bytes at quality {JPEG_FALLBACK_QUALITY} exceed {max_output_bytes}"
    raise _Failed(PrepareFailure.OUTPUT_TOO_LARGE, detail)


def _write_exclusive(path: str, data: bytes) -> None:
    """Create ``path`` exclusively (never through a symlink) and write ``data``."""
    try:
        fd = os.open(path, _OUTPUT_FLAGS, _OUTPUT_MODE)
    except OSError as exc:
        detail = f"cannot create the output ({_errno_name(exc)})"
        raise _Failed(PrepareFailure.IO, detail) from None
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(data)
    except OSError as exc:
        with contextlib.suppress(OSError):
            Path(path).unlink()
        detail = f"cannot write the output ({_errno_name(exc)})"
        raise _Failed(PrepareFailure.IO, detail) from None
