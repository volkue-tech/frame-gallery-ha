"""The ``prepare`` and ``inspect`` tasks' requests and results, and the
parent's artifact (§8.3, §11).

Requests and results cross the executor seam as JSON objects. ``from_json``
treats its input as untrusted and raises ``ValueError`` on any deviation.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from frame_gallery.domain import CANVAS, FitMode, Rgb, Size
from frame_gallery.isolation.executor import JsonObject, JsonValue
from frame_gallery.selection.geometry import Rejection

MAX_DIMENSION: Final = 20_000
"""Width and height limit of a source image, checked from the header (D-121)."""

MAX_JPEG_PIXELS: Final = 64_000_000
MAX_PNG_PIXELS: Final = 40_000_000
MAX_SOURCE_BYTES: Final = 40 * 1024 * 1024
MAX_OUTPUT_BYTES: Final = 15 * 1024 * 1024
JPEG_QUALITY: Final = 90
JPEG_FALLBACK_QUALITY: Final = 85
"""Used once if the first encoding exceeds :data:`MAX_OUTPUT_BYTES` (Q-05)."""

PREPARE_TASK: Final = "prepare"
INSPECT_TASK: Final = "inspect"
"""The local header inspection (§8.3): dimensions after EXIF orientation."""


class ImageFormat(enum.StrEnum):
    JPEG = "JPEG"
    PNG = "PNG"


class PrepareStatus(enum.StrEnum):
    OK = "ok"
    REJECTED = "rejected"
    """The real dimensions violate the reason the candidate was chosen."""

    FAILED = "failed"


class PrepareFailure(enum.StrEnum):
    FORMAT_MISMATCH = "format_mismatch"
    """The file is not the declared JPEG or PNG."""

    LIMITS = "limits"
    """Dimension or pixel limits exceeded (checked before decoding)."""

    DECODE = "decode"
    UNSUPPORTED_MODE = "unsupported_mode"
    RENDER = "render"
    ENCODE = "encode"
    OUTPUT_TOO_LARGE = "output_too_large"
    """Still over 15 MiB after the single re-encode at quality 85."""

    IO = "io"


class ColourHandling(enum.StrEnum):
    ASSUMED_SRGB = "assumed_srgb"
    """No embedded profile; the pixels are treated as sRGB."""

    CONVERTED = "converted"
    """The embedded ICC profile was converted to sRGB."""

    PROFILE_IGNORED = "profile_ignored"
    """The embedded profile was unusable; the pixels were treated as sRGB."""

    CMYK_UNMANAGED = "cmyk_unmanaged"
    """CMYK without a usable profile; converted without colour management."""


def _field(obj: JsonObject, name: str) -> JsonValue:
    if name not in obj:
        msg = f"missing field {name!r}"
        raise ValueError(msg)
    return obj[name]


def _str(obj: JsonObject, name: str, max_length: int = 4096) -> str:
    value = _field(obj, name)
    if not isinstance(value, str) or not value or len(value) > max_length:
        msg = f"field {name!r} must be a non-empty string"
        raise ValueError(msg)
    return value


def _optional_str(obj: JsonObject, name: str, max_length: int = 512) -> str | None:
    value = _field(obj, name)
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > max_length:
        msg = f"field {name!r} must be a string or null"
        raise ValueError(msg)
    return value


def _bool(obj: JsonObject, name: str) -> bool:
    value = _field(obj, name)
    if not isinstance(value, bool):
        msg = f"field {name!r} must be a boolean"
        raise ValueError(msg)
    return value


def _optional_int(obj: JsonObject, name: str, minimum: int, maximum: int) -> int | None:
    value = _field(obj, name)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        msg = f"field {name!r} must be an integer in {minimum}..{maximum} or null"
        raise ValueError(msg)
    return value


def _size_to_json(size: Size | None) -> JsonValue:
    return None if size is None else [size.width, size.height]


def _size_from_json(obj: JsonObject, name: str) -> Size:
    value = _field(obj, name)
    if not isinstance(value, list) or len(value) != 2:
        msg = f"field {name!r} must be [width, height]"
        raise ValueError(msg)
    width, height = value
    if (
        isinstance(width, bool)
        or isinstance(height, bool)
        or not isinstance(width, int)
        or not isinstance(height, int)
        or not (0 < width <= 1_000_000 and 0 < height <= 1_000_000)
    ):
        msg = f"field {name!r} must hold two positive integers in range"
        raise ValueError(msg)
    return Size(width, height)


MAX_CANVAS_PIXELS: Final = 16_000_000
"""The worker allocates canvas-sized buffers; a request may not ask for more."""


def _canvas_from_json(obj: JsonObject) -> Size:
    canvas = _size_from_json(obj, "canvas")
    if (
        canvas.width > MAX_DIMENSION
        or canvas.height > MAX_DIMENSION
        or canvas.pixels > MAX_CANVAS_PIXELS
    ):
        msg = "field 'canvas' is too large"
        raise ValueError(msg)
    return canvas


def _optional_size_from_json(obj: JsonObject, name: str) -> Size | None:
    if _field(obj, name) is None:
        return None
    return _size_from_json(obj, name)


def _enum[E: enum.StrEnum](obj: JsonObject, name: str, kind: type[E]) -> E:
    value = _field(obj, name)
    if not isinstance(value, str):
        msg = f"field {name!r} must be a string"
        raise ValueError(msg)
    try:
        return kind(value)
    except ValueError:
        msg = f"field {name!r} has an unknown value"
        raise ValueError(msg) from None


def _optional_enum[E: enum.StrEnum](obj: JsonObject, name: str, kind: type[E]) -> E | None:
    if _field(obj, name) is None:
        return None
    return _enum(obj, name, kind)


@dataclass(frozen=True, slots=True)
class PrepareRequest:
    """What the parent asks the ``prepare`` task to do. The parent chooses
    both paths."""

    source_path: str
    output_path: str
    declared_format: ImageFormat
    fit_mode: FitMode
    background: Rgb
    landscape_only: bool
    require_near_16_9: bool
    """Verify the strict near-16:9 reason the candidate was chosen for."""

    canvas: Size = CANVAS

    def to_json(self) -> JsonObject:
        return {
            "source_path": self.source_path,
            "output_path": self.output_path,
            "declared_format": self.declared_format.value,
            "fit_mode": self.fit_mode.value,
            "background": self.background.to_hex(),
            "landscape_only": self.landscape_only,
            "require_near_16_9": self.require_near_16_9,
            "canvas": _size_to_json(self.canvas),
        }

    @classmethod
    def from_json(cls, obj: JsonObject) -> PrepareRequest:
        return cls(
            source_path=_str(obj, "source_path"),
            output_path=_str(obj, "output_path"),
            declared_format=_enum(obj, "declared_format", ImageFormat),
            fit_mode=_enum(obj, "fit_mode", FitMode),
            background=Rgb.from_hex(_str(obj, "background", max_length=7)),
            landscape_only=_bool(obj, "landscape_only"),
            require_near_16_9=_bool(obj, "require_near_16_9"),
            canvas=_canvas_from_json(obj),
        )


@dataclass(frozen=True, slots=True)
class PrepareResult:
    """What the ``prepare`` task reports. The real dimensions come first, so
    the parent can verify the reason a candidate was chosen."""

    status: PrepareStatus
    source_size: Size | None = None
    """The stored dimensions from the header, before EXIF orientation."""

    oriented_size: Size | None = None
    """The dimensions after EXIF orientation."""

    orientation: int | None = None
    """The EXIF orientation, 1 to 8 (1 when absent)."""

    rejection: Rejection | None = None
    failure: PrepareFailure | None = None
    detail: str | None = None
    """A short, log-safe explanation."""

    output_bytes: int | None = None
    jpeg_quality: int | None = None
    colour: ColourHandling | None = None

    def __post_init__(self) -> None:
        if self.status is PrepareStatus.OK:
            if (
                self.source_size is None
                or self.oriented_size is None
                or self.orientation is None
                or self.output_bytes is None
                or self.jpeg_quality is None
                or self.colour is None
            ):
                msg = (
                    "an ok result needs source_size, oriented_size, orientation, "
                    "output_bytes, jpeg_quality, and colour"
                )
                raise ValueError(msg)
            if self.rejection is not None or self.failure is not None:
                msg = "an ok result has neither rejection nor failure"
                raise ValueError(msg)
            return
        if self.output_bytes is not None or self.jpeg_quality is not None:
            msg = "only an ok result reports output details"
            raise ValueError(msg)
        if self.status is PrepareStatus.REJECTED:
            if self.rejection is None or self.oriented_size is None or self.failure is not None:
                msg = "a rejected result needs rejection and oriented_size only"
                raise ValueError(msg)
        elif self.failure is None or self.rejection is not None:
            msg = "a failed result needs failure only"
            raise ValueError(msg)

    def to_json(self) -> JsonObject:
        return {
            "status": self.status.value,
            "source_size": _size_to_json(self.source_size),
            "oriented_size": _size_to_json(self.oriented_size),
            "orientation": self.orientation,
            "rejection": None if self.rejection is None else self.rejection.value,
            "failure": None if self.failure is None else self.failure.value,
            "detail": self.detail,
            "output_bytes": self.output_bytes,
            "jpeg_quality": self.jpeg_quality,
            "colour": None if self.colour is None else self.colour.value,
        }

    @classmethod
    def from_json(cls, obj: JsonObject) -> PrepareResult:
        return cls(
            status=_enum(obj, "status", PrepareStatus),
            source_size=_optional_size_from_json(obj, "source_size"),
            oriented_size=_optional_size_from_json(obj, "oriented_size"),
            orientation=_optional_int(obj, "orientation", 1, 8),
            rejection=_optional_enum(obj, "rejection", Rejection),
            failure=_optional_enum(obj, "failure", PrepareFailure),
            detail=_optional_str(obj, "detail"),
            output_bytes=_optional_int(obj, "output_bytes", 1, MAX_OUTPUT_BYTES),
            jpeg_quality=_optional_int(obj, "jpeg_quality", 1, 100),
            colour=_optional_enum(obj, "colour", ColourHandling),
        )


class InspectStatus(enum.StrEnum):
    OK = "ok"
    FAILED = "failed"
    """The file cannot be read as the declared format within the limits."""


_MAX_FILE_ID: Final = 2**64 - 1


@dataclass(frozen=True, slots=True)
class InspectRequest:
    """Read one library file's header (§8.3). No pixels are decoded.

    ``device`` and ``inode`` pin the file the scan saw: the worker refuses a
    file whose identity differs (D-149)."""

    path: str
    declared_format: ImageFormat
    device: int | None = None
    inode: int | None = None

    def to_json(self) -> JsonObject:
        return {
            "path": self.path,
            "declared_format": self.declared_format.value,
            "device": self.device,
            "inode": self.inode,
        }

    @classmethod
    def from_json(cls, obj: JsonObject) -> InspectRequest:
        return cls(
            path=_str(obj, "path"),
            declared_format=_enum(obj, "declared_format", ImageFormat),
            device=_optional_int(obj, "device", 0, _MAX_FILE_ID),
            inode=_optional_int(obj, "inode", 0, _MAX_FILE_ID),
        )


@dataclass(frozen=True, slots=True)
class InspectResult:
    """The header's dimensions after EXIF orientation, or why it failed."""

    status: InspectStatus
    oriented_size: Size | None = None
    failure: PrepareFailure | None = None
    detail: str | None = None

    def __post_init__(self) -> None:
        ok = self.status is InspectStatus.OK
        if ok != (self.oriented_size is not None) or ok == (self.failure is not None):
            msg = "an ok inspection has a size only; a failed one a failure only"
            raise ValueError(msg)

    def to_json(self) -> JsonObject:
        return {
            "status": self.status.value,
            "oriented_size": _size_to_json(self.oriented_size),
            "failure": None if self.failure is None else self.failure.value,
            "detail": self.detail,
        }

    @classmethod
    def from_json(cls, obj: JsonObject) -> InspectResult:
        return cls(
            status=_enum(obj, "status", InspectStatus),
            oriented_size=_optional_size_from_json(obj, "oriented_size"),
            failure=_optional_enum(obj, "failure", PrepareFailure),
            detail=_optional_str(obj, "detail"),
        )


@dataclass(frozen=True, slots=True)
class DeliveryArtifact:
    """The parent-validated ``delivery.jpg``: one file and one SHA-256 serve as
    the television payload, the preview, and the recorded fingerprint (D8)."""

    path: Path
    sha256: str
    size_bytes: int
    dims: Size
