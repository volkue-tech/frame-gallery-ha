"""Generated test images (§20.3): no third-party artwork, no committed binaries.

Every helper builds a small, deterministic image with Pillow (or crafts the
bytes directly) and writes it into a directory the test provides, normally
pytest's ``tmp_path``.

Orientation fixtures follow the EXIF definition of tag 0x0112, which states
where the stored row 0 and column 0 appear on the display:

====  ===============  ==================
 tag   row 0 shown at   column 0 shown at
====  ===============  ==================
  1    top              left
  2    top              right
  3    bottom           right
  4    bottom           left
  5    left             top
  6    right            top
  7    right            bottom
  8    left             bottom
====  ===============  ==================

:func:`display_position` encodes this table directly, and :func:`to_stored`
builds the stored image that a camera would write for a given display image.
"""

from __future__ import annotations

import io
import struct
import zlib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from PIL import Image, ImageCms

Colour = tuple[int, int, int]

RED: Final[Colour] = (230, 20, 20)
GREEN: Final[Colour] = (20, 200, 40)
BLUE: Final[Colour] = (30, 40, 220)
YELLOW: Final[Colour] = (230, 220, 30)
MARKS: Final = {"red": RED, "green": GREEN, "blue": BLUE, "yellow": YELLOW}
"""Corner marks: top-left, top-right, bottom-left, bottom-right."""

MARK_DIVISOR: Final = 5
"""Each corner mark covers one fifth of each side."""

PNG_SIGNATURE: Final = b"\x89PNG\r\n\x1a\n"


# --- pixel content --------------------------------------------------------


def bright_gradient(size: tuple[int, int]) -> Image.Image:
    """An RGB gradient whose channels all stay between 120 and 255."""
    width, height = size
    ramp = Image.linear_gradient("L").point(lambda value: 120 + value // 2)
    red = ramp.rotate(90).resize((width, height))
    green = ramp.resize((width, height))
    blue = Image.new("L", (width, height), 170)
    return Image.merge("RGB", (red, green, blue))


def marked(size: tuple[int, int]) -> Image.Image:
    """A bright gradient with a distinctive colour in each corner."""
    image = bright_gradient(size)
    width, height = size
    mark_w, mark_h = width // MARK_DIVISOR, height // MARK_DIVISOR
    corners = {
        RED: (0, 0),
        GREEN: (width - mark_w, 0),
        BLUE: (0, height - mark_h),
        YELLOW: (width - mark_w, height - mark_h),
    }
    for colour, (left, top) in corners.items():
        image.paste(colour, (left, top, left + mark_w, top + mark_h))
    return image


def banded(size: tuple[int, int], band: int) -> Image.Image:
    """A bright gradient with a ``band``-pixel red strip at the top, a blue
    strip at the bottom, a green strip on the left, and a yellow strip on
    the right (for crop checks)."""
    image = bright_gradient(size)
    width, height = size
    image.paste(RED, (0, 0, width, band))
    image.paste(BLUE, (0, height - band, width, height))
    image.paste(GREEN, (0, band, band, height - band))
    image.paste(YELLOW, (width - band, band, width, height - band))
    return image


def half_transparent(mode: str, size: tuple[int, int], colour: Colour) -> Image.Image:
    """``RGBA`` or ``LA``: the left half fully transparent, the right half
    opaque ``colour`` (its luminance for ``LA``)."""
    width, height = size
    base = Image.new("RGB", size, colour)
    alpha = Image.new("L", size, 0)
    alpha.paste(255, (width // 2, 0, width, height))
    if mode == "LA":
        return Image.merge("LA", (base.convert("L"), alpha))
    red, green, blue = base.split()
    return Image.merge("RGBA", (red, green, blue, alpha))


def palette(size: tuple[int, int], colour: Colour, *, transparent_left: bool) -> Image.Image:
    """A ``P`` image: ``colour`` on the right half; the left half uses index
    1, which is transparent when ``transparent_left`` is set."""
    width, height = size
    image = Image.new("P", size, 1)
    image.putpalette([0, 0, 0, 10, 10, 10, *colour] + [0, 0, 0] * 253)
    image.paste(2, (width // 2, 0, width, height))
    if transparent_left:
        image.info["transparency"] = 1
    return image


# --- orientation ------------------------------------------------------------


def display_position(
    orientation: int, stored_xy: tuple[int, int], display_size: tuple[int, int]
) -> tuple[int, int]:
    """Where the stored pixel ``(column, row)`` appears on the display."""
    column, row = stored_xy
    width, height = display_size
    positions = {
        1: (column, row),
        2: (width - 1 - column, row),
        3: (width - 1 - column, height - 1 - row),
        4: (column, height - 1 - row),
        5: (row, column),
        6: (width - 1 - row, column),
        7: (width - 1 - row, height - 1 - column),
        8: (row, height - 1 - column),
    }
    return positions[orientation]


_TO_STORED: Final = {
    1: None,
    2: Image.Transpose.FLIP_LEFT_RIGHT,
    3: Image.Transpose.ROTATE_180,
    4: Image.Transpose.FLIP_TOP_BOTTOM,
    5: Image.Transpose.TRANSPOSE,
    6: Image.Transpose.ROTATE_90,
    7: Image.Transpose.TRANSVERSE,
    8: Image.Transpose.ROTATE_270,
}
"""Checked pixel by pixel against :func:`display_position` in the tests."""


def to_stored(display: Image.Image, orientation: int) -> Image.Image:
    """The stored image whose EXIF ``orientation`` displays as ``display``."""
    method = _TO_STORED[orientation]
    return display.copy() if method is None else display.transpose(method)


# --- ICC profiles -----------------------------------------------------------


def srgb_icc() -> bytes:
    """Pillow's built-in sRGB profile, serialized."""
    return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


D50: Final = (0.9642, 1.0, 0.8249)
"""The ICC profile connection space illuminant (XYZ)."""


def _s15(value: float) -> bytes:
    return struct.pack(">i", round(value * 65536))


def _xyz_tag(x: float, y: float, z: float) -> bytes:
    return b"XYZ " + bytes(4) + _s15(x) + _s15(y) + _s15(z)


def _desc_tag(text: str) -> bytes:
    """An ICC v2 ``textDescriptionType``: the ASCII text, then empty Unicode
    (language code and count) and ScriptCode (code, count, 67 bytes) parts."""
    ascii_text = text.encode("ascii") + b"\0"
    ascii_part = struct.pack(">I", len(ascii_text)) + ascii_text
    return b"desc" + bytes(4) + ascii_part + bytes(4 + 4) + bytes(2 + 1 + 67)


def _icc(
    colour_space: bytes, device_class: bytes, pcs: bytes, tags: list[tuple[bytes, bytes]]
) -> bytes:
    """A minimal ICC v2.1 profile with a D50 illuminant."""
    table_end = 128 + 4 + 12 * len(tags)
    table = b""
    body = b""
    for signature, data in tags:
        body += bytes(-(table_end + len(body)) % 4)
        table += signature + struct.pack(">II", table_end + len(body), len(data))
        body += data
    header = (
        struct.pack(">I", table_end + len(body))
        + bytes(4)
        + struct.pack(">I", 0x02100000)
        + device_class
        + colour_space
        + pcs
        + bytes(12)
        + b"acsp"
        + bytes(24)
        + struct.pack(">I", 0)
        + _xyz_tag(*D50)[8:]
        + bytes(48)
    )
    return header + struct.pack(">I", len(tags)) + table + body


def grey_icc(gamma: float = 2.2) -> bytes:
    """A grey display profile with a pure gamma curve."""
    curve = b"curv" + bytes(4) + struct.pack(">IH", 1, round(gamma * 256))
    return _icc(
        b"GRAY",
        b"mntr",
        b"XYZ ",
        [(b"desc", _desc_tag("Test grey")), (b"wtpt", _xyz_tag(*D50)), (b"kTRC", curve)],
    )


def cmyk_icc() -> bytes:
    """A CMYK output profile (lut16 AToB0 to Lab): no ink is white, and any
    full-strength ink is black. Enough for LittleCMS to build a transform."""
    grid = 2
    lut = b"mft2" + bytes(4) + bytes([4, 3, grid, 0])
    lut += b"".join(_s15(1.0 if row == col else 0.0) for row in range(3) for col in range(3))
    lut += struct.pack(">HH", 2, 2)
    lut += struct.pack(">HH", 0, 0xFFFF) * 4
    for index in range(grid**4):
        lightness = 100.0 if index == 0 else 0.0
        lut += struct.pack(">HHH", round(lightness * 0xFF00 / 100), 0x8000, 0x8000)
    lut += struct.pack(">HH", 0, 0xFFFF) * 3
    return _icc(
        b"CMYK",
        b"prtr",
        b"Lab ",
        [(b"desc", _desc_tag("Test CMYK")), (b"wtpt", _xyz_tag(*D50)), (b"A2B0", lut)],
    )


GARBAGE_ICC: Final = b"this is not an ICC profile" * 4


# --- writers ----------------------------------------------------------------


def save_jpeg(
    image: Image.Image,
    path: Path,
    *,
    orientation: int | None = None,
    icc_profile: bytes | None = None,
    progressive: bool = False,
    quality: int = 92,
) -> Path:
    """Write ``image`` as a JPEG, optionally with EXIF orientation and ICC."""
    options: dict[str, object] = {"quality": quality, "progressive": progressive}
    if orientation is not None:
        exif = Image.Exif()
        exif[0x0112] = orientation
        options["exif"] = exif.tobytes()
    if icc_profile is not None:
        options["icc_profile"] = icc_profile
    image.save(path, "JPEG", **options)
    return path


def save_png(image: Image.Image, path: Path, *, icc_profile: bytes | None = None) -> Path:
    """Write ``image`` as a PNG (keeping its ``transparency``), optionally with ICC."""
    options: dict[str, object] = {}
    if "transparency" in image.info:
        options["transparency"] = image.info["transparency"]
    if icc_profile is not None:
        options["icc_profile"] = icc_profile
    image.save(path, "PNG", **options)
    return path


def save_apng(frames: list[Image.Image], path: Path) -> Path:
    """An animated PNG: the first frame is the default image."""
    frames[0].save(path, "PNG", save_all=True, append_images=frames[1:], duration=100)
    return path


def save_mpo(frames: list[Image.Image], path: Path) -> Path:
    """A multi-picture JPEG (CIPA DC-007): a baseline JPEG whose MPF index
    lists the further frames, as cameras write for previews. It starts with
    the JPEG magic bytes, and Pillow reports it as ``MPO``."""
    frames[0].save(path, "MPO", save_all=True, append_images=frames[1:])
    return path


def oriented_jpeg(directory: Path, orientation: int, display_size: tuple[int, int]) -> Path:
    """A marked image stored so that EXIF ``orientation`` displays it upright."""
    stored = to_stored(marked(display_size), orientation)
    return save_jpeg(stored, directory / f"orientation-{orientation}.jpg", orientation=orientation)


def write_bytes(path: Path, data: bytes) -> Path:
    path.write_bytes(data)
    return path


# --- crafted headers (limits without allocation) -----------------------------


def png_chunk(kind: bytes, data: bytes) -> bytes:
    """Length, type, data, and the CRC over type and data."""
    crc = zlib.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


PNG_IEND: Final = png_chunk(b"IEND", b"")

GREY: Final = 0
TRUECOLOUR: Final = 2
"""PNG colour types used by :func:`png_ihdr`."""


def png_ihdr(
    width: int, height: int, *, bit_depth: int = 8, colour_type: int = TRUECOLOUR
) -> bytes:
    return png_chunk(
        b"IHDR", struct.pack(">IIBBBBB", width, height, bit_depth, colour_type, 0, 0, 0)
    )


def png_idat(rows: list[bytes]) -> bytes:
    """One IDAT chunk holding ``rows`` of packed samples, each with filter type 0."""
    return png_chunk(b"IDAT", zlib.compress(b"".join(b"\x00" + row for row in rows)))


def png_file(*chunks: bytes) -> bytes:
    return PNG_SIGNATURE + b"".join(chunks)


def pack_samples(samples: list[int], bit_depth: int) -> bytes:
    """One PNG row: ``samples`` packed most significant bits first (1, 2, 4,
    or 8 bits) or as big-endian 16-bit values."""
    if bit_depth == 16:
        return b"".join(struct.pack(">H", sample) for sample in samples)
    per_byte = 8 // bit_depth
    packed = bytearray()
    for start in range(0, len(samples), per_byte):
        byte = 0
        group = samples[start : start + per_byte]
        for index in range(per_byte):
            byte = (byte << bit_depth) | (group[index] if index < len(group) else 0)
        packed.append(byte)
    return bytes(packed)


def keyed_png(
    size: tuple[int, int],
    *,
    bit_depth: int,
    colour_type: int,
    left: list[int],
    right: list[int],
    key: list[int],
) -> bytes:
    """A greyscale or truecolour PNG with a ``tRNS`` colour key.

    ``left`` and ``right`` are the stored samples of one pixel (one value
    for grey, three for RGB) filling each half; ``key`` is the stored key,
    written as big-endian 16-bit fields as the PNG format requires.
    """
    width, height = size
    half = width // 2
    row = pack_samples(left * half + right * (width - half), bit_depth)
    return png_file(
        png_ihdr(width, height, bit_depth=bit_depth, colour_type=colour_type),
        png_chunk(b"tRNS", b"".join(struct.pack(">H", value) for value in key)),
        png_idat([row] * height),
        PNG_IEND,
    )


def png_header_only(width: int, height: int) -> bytes:
    """A PNG whose IHDR claims ``width`` x ``height`` (8-bit RGB) but whose
    image data is empty: opening it reads the header only."""
    return png_file(png_ihdr(width, height), png_chunk(b"IDAT", zlib.compress(b"")), PNG_IEND)


def png_truncated_chunk() -> bytes:
    """A valid IHDR followed by an iCCP chunk cut short."""
    return png_file(png_ihdr(4, 4), struct.pack(">I", 1000) + b"iCCPabc")


def flat_png(
    size: tuple[int, int], colour: Colour, *, before: bytes = b"", after: bytes = b""
) -> bytes:
    """A decodable one-colour RGB PNG with extra chunks ``before`` and
    ``after`` its image data."""
    width, height = size
    return png_file(
        png_ihdr(width, height), before, png_idat([bytes(colour) * width] * height), after, PNG_IEND
    )


def jpeg_segment(marker: int, payload: bytes) -> bytes:
    """``FF marker`` with a big-endian length that includes itself."""
    return bytes([0xFF, marker]) + struct.pack(">H", len(payload) + 2) + payload


def sof_payload(width: int, height: int, *, components: int = 3, precision: int = 8) -> bytes:
    body = bytes([precision]) + struct.pack(">HH", height, width) + bytes([components])
    return body + b"".join(bytes([index + 1, 0x11, 0]) for index in range(components))


def sos_payload(components: int = 3) -> bytes:
    selectors = b"".join(bytes([index + 1, 0]) for index in range(components))
    return bytes([components]) + selectors + bytes([0, 63, 0])


def jpeg_header_only(
    width: int, height: int, *, components: int = 3, sof: int = 0xC0, precision: int = 8
) -> bytes:
    """SOI, a frame header, SOS, and EOI: enough for a header parser or for
    Pillow to open (but not decode) the file."""
    return (
        b"\xff\xd8"
        + jpeg_segment(sof, sof_payload(width, height, components=components, precision=precision))
        + jpeg_segment(0xDA, sos_payload(components))
        + b"\xff\xd9"
    )


def encoded_jpeg(image: Image.Image, **options: object) -> bytes:
    """``image`` encoded as JPEG in memory."""
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", **options)
    return buffer.getvalue()


def with_segments(jpeg: bytes, segments: bytes) -> bytes:
    """``jpeg`` with ``segments`` inserted right after its SOI marker."""
    return jpeg[:2] + segments + jpeg[2:]


# --- TIFF structures in metadata: EXIF and MPF -------------------------------------

TIFF_BYTE: Final = 1
TIFF_ASCII: Final = 2
TIFF_SHORT: Final = 3
TIFF_LONG: Final = 4
TIFF_RATIONAL: Final = 5
TIFF_SBYTE: Final = 6
TIFF_UNDEFINED: Final = 7
TIFF_SSHORT: Final = 8
TIFF_SLONG: Final = 9
TIFF_DOUBLE: Final = 12
TIFF_IFD: Final = 13
TIFF_LONG8: Final = 16

_TIFF_FORMATS: Final = {
    TIFF_SHORT: "H",
    TIFF_LONG: "L",
    TIFF_RATIONAL: "L",
    TIFF_SBYTE: "b",
    TIFF_SSHORT: "h",
    TIFF_SLONG: "l",
    TIFF_DOUBLE: "d",
    TIFF_IFD: "L",
    TIFF_LONG8: "Q",
}
_TIFF_NUMBERS_PER_VALUE: Final = {TIFF_RATIONAL: 2}
"""A rational is two numbers: numerator and denominator."""

ORIENTATION: Final = 0x0112
EXIF_IFD: Final = 0x8769
GPS_IFD: Final = 0x8825
INTEROP_IFD: Final = 0xA005
MAKER_NOTE: Final = 0x927C
MP_NUMBER_OF_IMAGES: Final = 0xB001

EXIF_HEADER: Final = b"Exif\x00\x00"
EXIF_SEGMENT_DATA: Final = 65_533 - len(EXIF_HEADER)
"""The most TIFF bytes one APP1 "Exif" segment holds."""


@dataclass(frozen=True, slots=True)
class TiffEntry:
    """One IFD entry of :func:`tiff`.

    ``values`` is the packed value (bytes) or numbers packed as ``type``
    (a rational as two numbers); it sits inline when it fits in four bytes
    and after the IFD otherwise. ``count`` overrides the number of values,
    ``field`` writes the four-byte value field as a raw offset, and ``link``
    makes the field the offset of another IFD of the structure (its index).
    """

    tag: int
    type: int
    values: bytes | tuple[int | float, ...] = b""
    count: int | None = None
    field: int | None = None
    link: int | None = None


@dataclass(frozen=True, slots=True)
class TiffIfd:
    entries: tuple[TiffEntry, ...]
    next: int | None = None
    """The index of the next IFD in the chain (``None`` ends it)."""


def tiff_link(tag: int, index: int) -> TiffEntry:
    """A LONG pointer entry to the IFD at ``index``."""
    return TiffEntry(tag, TIFF_LONG, link=index)


def _tiff_packed(entry: TiffEntry, order: str) -> bytes:
    if isinstance(entry.values, bytes):
        return entry.values
    form = _TIFF_FORMATS[entry.type]
    return struct.pack(f"{order}{len(entry.values)}{form}", *entry.values)


def _tiff_count(entry: TiffEntry) -> int:
    if entry.count is not None:
        return entry.count
    if entry.link is not None:
        return 1
    if isinstance(entry.values, bytes):
        return len(entry.values)
    return len(entry.values) // _TIFF_NUMBERS_PER_VALUE.get(entry.type, 1)


def _tiff_out_of_line(entry: TiffEntry, order: str) -> bytes:
    """The value bytes stored after the IFD, if any."""
    if entry.field is not None or entry.link is not None:
        return b""
    data = _tiff_packed(entry, order)
    return data if len(data) > 4 else b""


def tiff(ifds: Sequence[TiffIfd], *, big_endian: bool = False) -> bytes:
    """A classic TIFF structure, as EXIF and MPF carry it: the header (IFD0
    is ``ifds[0]``), then each IFD followed by its out-of-line values."""
    order = ">" if big_endian else "<"
    offsets: list[int] = []
    pos = 8
    for ifd in ifds:
        offsets.append(pos)
        pos += 2 + 12 * len(ifd.entries) + 4
        pos += sum(len(_tiff_out_of_line(entry, order)) for entry in ifd.entries)
    magic = b"MM\x00*" if big_endian else b"II*\x00"
    parts = [magic, struct.pack(order + "L", offsets[0])]
    for offset, ifd in zip(offsets, ifds, strict=True):
        values_at = offset + 2 + 12 * len(ifd.entries) + 4
        parts.append(struct.pack(order + "H", len(ifd.entries)))
        extra: list[bytes] = []
        for entry in ifd.entries:
            out_of_line = _tiff_out_of_line(entry, order)
            if entry.link is not None:
                field = struct.pack(order + "L", offsets[entry.link])
            elif entry.field is not None:
                field = struct.pack(order + "L", entry.field)
            elif out_of_line:
                field = struct.pack(order + "L", values_at)
                values_at += len(out_of_line)
                extra.append(out_of_line)
            else:
                field = _tiff_packed(entry, order).ljust(4, b"\x00")
            parts.append(struct.pack(order + "HHL", entry.tag, entry.type, _tiff_count(entry)))
            parts.append(field)
        parts.append(struct.pack(order + "L", 0 if ifd.next is None else offsets[ifd.next]))
        parts.extend(extra)
    return b"".join(parts)


def tiff_bomb(entries: int, value_bytes: int, *, filler: int = 0) -> bytes:
    """IFD0 with ``entries`` BYTE entries (distinct tags) that each declare
    ``value_bytes`` values at offset 0, and at least ``filler`` bytes in
    total, so the shared values exist: Pillow would copy them once per entry."""
    ifd0 = TiffIfd(
        tuple(
            TiffEntry(1 + index, TIFF_BYTE, count=value_bytes, field=0) for index in range(entries)
        )
    )
    block = tiff([ifd0])
    return block + bytes(max(0, filler - len(block)))


MPF_SEGMENT_DATA: Final = 65_533 - 4
"""The most TIFF bytes one APP2 "MPF" segment holds."""


def mpf_value_bomb(tags: int) -> bytes:
    """An MPF index that fills one APP2 segment: ``tags`` SHORT tags that
    each declare the same 64 000 bytes of values. Pillow decodes every tag
    of the index into Python integers (about 110 MiB for 300 tags)."""
    entries = tuple(
        TiffEntry(0xC000 + index, TIFF_SHORT, count=32_000, field=8) for index in range(tags)
    )
    block = tiff([TiffIfd(entries)])
    return block + bytes(MPF_SEGMENT_DATA - len(block))


def crowded_ifd(entries: int) -> TiffIfd:
    """An IFD of ``entries`` one-value SHORT entries (values inline), none of
    them an IFD pointer (tags 0x1000-0x7FFF)."""
    return TiffIfd(
        tuple(TiffEntry(0x1000 + index % 0x7000, TIFF_SHORT, (1,)) for index in range(entries))
    )


def _ascii(value: str) -> bytes:
    return value.encode("ascii") + b"\x00"


def camera_exif(
    *, orientation: int = 1, maker_note_bytes: int = 60 * 1024, big_endian: bool = False
) -> bytes:
    """A camera-like EXIF structure (the TIFF block, without the EXIF header).

    IFD0 links to the thumbnail's IFD1, an Exif IFD (with a MakerNote of
    ``maker_note_bytes`` and an Interoperability IFD), and a GPS IFD. With
    the default MakerNote it fills most of one APP1 segment, as real files do.
    """
    maker_note = (b"Maker\x00II" + bytes(range(256)) * (maker_note_bytes // 256 + 1))[
        :maker_note_bytes
    ]
    ifd0 = TiffIfd(
        (
            TiffEntry(0x010F, TIFF_ASCII, _ascii("Example Camera Co.")),  # Make
            TiffEntry(0x0110, TIFF_ASCII, _ascii("EC-1")),  # Model
            TiffEntry(ORIENTATION, TIFF_SHORT, (orientation,)),
            TiffEntry(0x011A, TIFF_RATIONAL, (300, 1)),  # XResolution
            TiffEntry(0x011B, TIFF_RATIONAL, (300, 1)),  # YResolution
            TiffEntry(0x0128, TIFF_SHORT, (2,)),  # ResolutionUnit: inches
            TiffEntry(0x0131, TIFF_ASCII, _ascii("Firmware 1.0")),  # Software
            TiffEntry(0x0132, TIFF_ASCII, _ascii("2026:09:26 12:00:00")),  # DateTime
            TiffEntry(0x0213, TIFF_SHORT, (2,)),  # YCbCrPositioning
            tiff_link(EXIF_IFD, 1),
            tiff_link(GPS_IFD, 2),
        ),
        next=4,
    )
    exif = TiffIfd(
        (
            TiffEntry(0x829A, TIFF_RATIONAL, (1, 250)),  # ExposureTime
            TiffEntry(0x829D, TIFF_RATIONAL, (28, 10)),  # FNumber
            TiffEntry(0x8822, TIFF_SHORT, (2,)),  # ExposureProgram
            TiffEntry(0x8827, TIFF_SHORT, (200,)),  # ISO
            TiffEntry(0x9000, TIFF_UNDEFINED, b"0232"),  # ExifVersion
            TiffEntry(0x9003, TIFF_ASCII, _ascii("2026:09:26 12:00:00")),  # DateTimeOriginal
            TiffEntry(0x9004, TIFF_ASCII, _ascii("2026:09:26 12:00:00")),  # DateTimeDigitized
            TiffEntry(0x9101, TIFF_UNDEFINED, b"\x01\x02\x03\x00"),  # ComponentsConfiguration
            TiffEntry(0x920A, TIFF_RATIONAL, (50, 1)),  # FocalLength
            TiffEntry(MAKER_NOTE, TIFF_UNDEFINED, maker_note),
            TiffEntry(0x9286, TIFF_UNDEFINED, b"ASCII\x00\x00\x00holiday"),  # UserComment
            TiffEntry(0xA000, TIFF_UNDEFINED, b"0100"),  # FlashpixVersion
            TiffEntry(0xA001, TIFF_SHORT, (1,)),  # ColorSpace: sRGB
            TiffEntry(0xA002, TIFF_LONG, (6000,)),  # PixelXDimension
            TiffEntry(0xA003, TIFF_LONG, (4000,)),  # PixelYDimension
            tiff_link(INTEROP_IFD, 3),
        )
    )
    gps = TiffIfd(
        (
            TiffEntry(0x0000, TIFF_BYTE, b"\x02\x03\x00\x00"),  # GPSVersionID
            TiffEntry(0x0001, TIFF_ASCII, _ascii("N")),
            TiffEntry(0x0002, TIFF_RATIONAL, (52, 1, 31, 1, 1234, 100)),  # GPSLatitude
            TiffEntry(0x0003, TIFF_ASCII, _ascii("E")),
            TiffEntry(0x0004, TIFF_RATIONAL, (13, 1, 24, 1, 5678, 100)),  # GPSLongitude
            TiffEntry(0x0005, TIFF_BYTE, b"\x00"),  # GPSAltitudeRef
            TiffEntry(0x0006, TIFF_RATIONAL, (3400, 100)),  # GPSAltitude
            TiffEntry(0x0007, TIFF_RATIONAL, (12, 1, 0, 1, 0, 1)),  # GPSTimeStamp
            TiffEntry(0x001D, TIFF_ASCII, _ascii("2026:09:26")),  # GPSDateStamp
        )
    )
    interop = TiffIfd(
        (
            TiffEntry(0x0001, TIFF_ASCII, _ascii("R98")),  # InteroperabilityIndex
            TiffEntry(0x0002, TIFF_UNDEFINED, b"0100"),  # InteroperabilityVersion
        )
    )
    thumbnail = TiffIfd(
        (
            TiffEntry(0x0103, TIFF_SHORT, (6,)),  # Compression: JPEG
            TiffEntry(0x011A, TIFF_RATIONAL, (72, 1)),
            TiffEntry(0x011B, TIFF_RATIONAL, (72, 1)),
            TiffEntry(0x0128, TIFF_SHORT, (2,)),
        )
    )
    return tiff((ifd0, exif, gps, interop, thumbnail), big_endian=big_endian)


def exif_segments(block: bytes) -> bytes:
    """The TIFF ``block`` as APP1 "Exif" segments of at most
    :data:`EXIF_SEGMENT_DATA` bytes each; Pillow joins them again."""
    return b"".join(
        jpeg_segment(0xE1, EXIF_HEADER + block[start : start + EXIF_SEGMENT_DATA])
        for start in range(0, len(block), EXIF_SEGMENT_DATA)
    )


def mpf_segment(block: bytes) -> bytes:
    """An APP2 "MPF" segment holding the TIFF ``block`` (a multi-picture index)."""
    return jpeg_segment(0xE2, b"MPF\x00" + block)


def mp_index(images: int, *, big_endian: bool = False) -> bytes:
    """An MPF index IFD (CIPA DC-007) that lists ``images`` images."""
    order = ">" if big_endian else "<"
    entries = b"".join(
        struct.pack(order + "LLLHH", 0x20030000 if index == 0 else 0, 1000, 0, 0, 0)
        for index in range(images)
    )
    index_ifd = TiffIfd(
        (
            TiffEntry(0xB000, TIFF_UNDEFINED, b"0100"),  # MPFVersion
            TiffEntry(MP_NUMBER_OF_IMAGES, TIFF_LONG, (images,)),
            TiffEntry(0xB002, TIFF_UNDEFINED, entries),  # MPEntry
        )
    )
    return tiff([index_ifd], big_endian=big_endian)


def exif_png(block: bytes, *, chunk: bytes = b"eXIf", keyword: bytes = b"") -> bytes:
    """A decodable PNG whose ``chunk`` (before the image data) holds
    ``keyword`` and ``block``."""
    return flat_png((8, 4), RED, before=png_chunk(chunk, keyword + block))


def raw_profile_text(block: bytes) -> bytes:
    """``block`` as ImageMagick's "Raw profile type exif" text: an empty
    line, the profile name, its length, then hex in lines of 72 digits."""
    digits = block.hex()
    lines = [digits[start : start + 72] for start in range(0, len(digits), 72)]
    return f"\nexif\n{len(block):8d}\n".encode("ascii") + "\n".join(lines).encode("ascii") + b"\n"


RAW_PROFILE_KEYWORD: Final = b"Raw profile type exif\x00"


def raw_profile_chunk(kind: bytes, text: bytes, *, compressed: bool = False) -> bytes:
    """A "Raw profile type exif" text chunk: ``tEXt``, ``zTXt`` (always
    compressed), or ``iTXt`` (compressed if asked, empty language and
    translated keyword)."""
    if kind == b"tEXt":
        data = text
    elif kind == b"zTXt":
        data = b"\x00" + zlib.compress(text)
    else:
        body = zlib.compress(text) if compressed else text
        data = bytes([int(compressed), 0]) + b"\x00\x00" + body
    return png_chunk(kind, RAW_PROFILE_KEYWORD + data)
