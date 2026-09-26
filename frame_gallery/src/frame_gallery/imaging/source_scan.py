"""A bounded pre-scan of a source's header in the worker (§11.1 step 2, §18.1
"header limits"; review findings L4-01 and P1): standard library only.

Pillow's JPEG and PNG readers loop in Python over every marker segment or
chunk they meet, and keep a record of many of them, without any limit on
their number. The D-121 limits only look at the declared dimensions, so a
small image buried in millions of empty segments would pass them. The worker
therefore walks the same structure first, with fixed caps, before Pillow
opens the file:

- a JPEG from SOI to its first SOS (Pillow parses nothing after it in
  Python), reusing :func:`~frame_gallery.imaging.jpeg_header.parse_jpeg`
  with the stricter source rules below;
- a PNG from its signature to IEND, because Pillow parses the chunks after
  the image data while it decodes.

The walk also bounds the TIFF structures that Pillow parses out of the
metadata (P1): a JPEG's EXIF (its APP1 "Exif" segments, which Pillow joins)
and MPF index (APP2 "MPF"), and a PNG's ``eXIf`` chunk, a ``tEXt`` chunk
with the keyword ``exif``, and a text chunk "Raw profile type exif" (hex).
Pillow's IFD reader copies count x type-size bytes for every entry, so a
few kilobytes of entries that all point at the same large value would make
it allocate gigabytes. See :func:`_walk_exif` and :func:`_walk_tiff`.

A file with neither signature is left to Pillow, which refuses it. The
walk only reads headers: it seeks over chunk data, and it reads a JPEG
header through a window that grows to at most :data:`MAX_HEADER_BYTES`.

:class:`SourceLimitError` (``limits``) reports a cap; :class:`SourceStructureError`
(``decode``) reports a malformed or truncated header. Both messages are log-safe.
"""

from __future__ import annotations

import io
import re
import struct
import zlib
from typing import IO, Final

from frame_gallery.errors import FrameGalleryError
from frame_gallery.imaging.contract import ImageFormat
from frame_gallery.imaging.jpeg_header import (
    APP1,
    APP2,
    JpegHeaderError,
    JpegInfo,
    JpegLimitError,
    JpegTruncatedError,
    parse_jpeg,
)
from frame_gallery.imaging.sniff import PNG_MAGIC, SNIFF_BYTES, sniff_bytes

# Real files stay far below the first two caps. Camera and phone JPEGs carry
# a few dozen segments; even an ICC profile split into the format's maximum
# of 255 APP2 segments, with EXIF, XMP, and extended XMP beside it, needs a
# few hundred. Their metadata rarely exceeds a few MiB (an ICC profile could
# reach 255 x 64 KiB, about 16 MB, which no real profile approaches). Each
# cap bounds what Pillow keeps for every segment or chunk it reads.

MAX_HEADER_SEGMENTS: Final = 1024
"""JPEG markers before the first SOS (SOS included), or PNG chunks other
than image data (IHDR included, IEND not)."""

MAX_HEADER_BYTES: Final = 16 * 1024 * 1024
"""JPEG bytes up to the end of the first SOS segment, or PNG bytes in chunks
other than image data."""

MAX_FILL_BYTES: Final = 4096
"""``0xFF`` fill bytes before JPEG markers, in total. Encoders write none or
a few; Pillow reads each one in a loop step of its own."""

MAX_PNG_DATA_CHUNKS: Final = 65_536
"""IDAT chunks, and the fcTL and fdAT chunks of an animated PNG. Encoders
split the image data into chunks of 8 KiB or more (a few thousand for a
40 MiB source) or one per row (at most 20 000 rows, D-121)."""

# The metadata TIFF structures of real files are small. A camera JPEG's EXIF
# must fit one 64 KiB APP1 segment, MakerNote included; it has five IFDs
# (IFD0, the Exif, GPS, and Interoperability IFDs, and the thumbnail's IFD1)
# of a few to about seventy entries each. An MPF index lists two or three
# images (a primary image and its previews, or a stereo pair). A PNG copies
# the EXIF of the JPEG it was made from.

MAX_TIFF_STRUCTURES: Final = 4
"""EXIF and MPF structures in one source: a JPEG's EXIF (all its APP1
"Exif" segments, which Pillow joins, count once), each APP2 "MPF" segment,
and each PNG chunk that Pillow reads EXIF from. Real files carry one or
two; the cap bounds the total work of the walks."""

MAX_TIFF_IFDS: Final = 16
"""IFDs (distinct offsets) walked in one structure."""

MAX_IFD_ENTRIES: Final = 512
"""Entries that one IFD may declare."""

MAX_TIFF_VALUE_BYTES: Final = 1024 * 1024
"""Declared value bytes (count x type size) of all entries of one
structure, inline or not: 16 times the most that a JPEG's EXIF segment
holds. Pillow decodes a number into a Python object about 30 times its
size; at this cap its copies stay near 30 MiB (at 4 MiB they reach
160 MiB)."""

MAX_MP_IMAGES: Final = 64
"""Images that an MPF index (tag 0xB001) may list."""

MAX_EXIF_BYTES: Final = 1024 * 1024
"""One EXIF block as Pillow holds it, headers included: a JPEG's APP1 "Exif"
segments joined, or a PNG chunk's EXIF. The EXIF standard keeps it within
one 64 KiB segment. Pillow joins a JPEG's segments by appending each to the
whole block so far, quadratic in their number: 255 full segments (16 MiB)
cost it about 2 GB of copies and 850 MiB of resident memory; within this cap
the cost stays at a few MiB."""

MAX_EXIF_HEADERS: Final = 8
"""Leading "Exif\\0\\0" headers of one EXIF block. Pillow strips them one
at a time, copying the rest of the block each time: quadratic in their
number. A block has one, or two when a PNG's ``eXIf`` chunk repeats it."""

MAX_RAW_PROFILE_BYTES: Final = 1024 * 1024
"""A PNG text chunk "Raw profile type exif": the chunk, and its text after
decompression. ImageMagick writes 64 KiB of EXIF as about 130 KB of hex;
Pillow itself stops inflating a text chunk at 1 MiB."""

_LENGTHLESS_IN_PILLOW: Final = frozenset({0xC8, *range(0xF0, 0xFE)})
"""JPG and JPG0-JPG13: reserved markers that have a length field in the JPEG
syntax, but that Pillow's header reader steps over as if they had none. The
two walks would disagree about where the next marker starts, so a source may
not use them before its scan; ordinary JPEG files never do."""

_FIRST_JPEG_WINDOW: Final = 64 * 1024
_WINDOW_GROWTH: Final = 4

_CHUNK_HEADER: Final = 8
"""A PNG chunk's length and type; its CRC follows the data."""

_CHUNK_OVERHEAD: Final = 12
_CHUNK_TYPE: Final = re.compile(rb"[A-Za-z]{4}")
_CRITICAL_CHUNKS: Final = frozenset({b"IHDR", b"PLTE", b"IDAT", b"IEND"})
_FRAME_CHUNKS: Final = frozenset({b"IDAT", b"fdAT", b"fcTL"})
_FRAME_CONTROL: Final = b"fcTL"
_IEND: Final = b"IEND"

_EXIF_HEADER: Final = b"Exif\x00\x00"
_MPF_HEADER: Final = b"MPF\x00"

_EXIF_CHUNK: Final = b"eXIf"
_TEXT: Final = b"tEXt"
_COMPRESSED_TEXT: Final = b"zTXt"
_INTERNATIONAL_TEXT: Final = b"iTXt"
_TEXT_CHUNKS: Final = frozenset({_TEXT, _COMPRESSED_TEXT, _INTERNATIONAL_TEXT})
_EXIF_KEYWORD: Final = b"exif\x00"
"""A ``tEXt`` chunk with this keyword gives Pillow raw EXIF bytes (the other
text chunks give it text, which its EXIF reader refuses)."""

_RAW_PROFILE_KEYWORD: Final = b"Raw profile type exif\x00"
"""ImageMagick's hex dump of EXIF, in any of the three text chunks."""

_RAW_PROFILE_PREAMBLE_LINES: Final = 3
"""Pillow skips an empty line, the profile name, and the length."""

_TIFF_ORDERS: Final = {b"II*\x00": "<", b"II\x00*": "<", b"MM\x00*": ">", b"MM*\x00": ">"}
"""The classic TIFF headers that Pillow's IFD reader accepts, and their byte
order. It accepts the last two, with the magic number reversed, as well."""

_BIGTIFF_HEADERS: Final = frozenset({b"II+\x00", b"MM\x00+"})
_TIFF_HEADER_BYTES: Final = 8
_IFD_COUNT_BYTES: Final = 2
_IFD_ENTRY_BYTES: Final = 12
_IFD_NEXT_BYTES: Final = 4

_TYPE_SIZES: Final = {
    1: 1,  # BYTE
    2: 1,  # ASCII
    3: 2,  # SHORT
    4: 4,  # LONG
    5: 8,  # RATIONAL
    6: 1,  # SBYTE
    7: 1,  # UNDEFINED
    8: 2,  # SSHORT
    9: 4,  # SLONG
    10: 8,  # SRATIONAL
    11: 4,  # FLOAT
    12: 8,  # DOUBLE
    13: 4,  # IFD
    16: 8,  # LONG8 (BigTIFF)
    17: 8,  # SLONG8 (BigTIFF)
    18: 8,  # IFD8 (BigTIFF)
}
"""Bytes per value of the TIFF 6.0 and BigTIFF field types."""

_UNKNOWN_TYPE_SIZE: Final = 1
"""Pillow skips an entry of a type it does not know; the walk counts one
byte per value for it all the same, so a huge count is still refused."""

_INTEGER_FORMATS: Final = {3: "H", 4: "L", 6: "b", 8: "h", 9: "l", 13: "L", 16: "Q"}
"""The integer field types. Pillow takes the first value of such an entry as
an IFD offset or an image count; it decodes the other types to bytes, text,
fractions, or floats, which it cannot use as either."""

_SUB_IFD_TAGS: Final = frozenset({0x8769, 0x8825, 0xA005})
"""The Exif, GPS, and Interoperability IFD pointers. Pillow follows the first
two from IFD0 and the third from the Exif IFD; the walk follows them from any
IFD. (Pillow parses a MakerNote or the SubIFDs only when asked for them
explicitly, which the worker never does.)"""

_MP_NUMBER_OF_IMAGES: Final = 0xB001


class SourceScanError(FrameGalleryError):
    """The source's header is refused before Pillow parses it. Log-safe."""


class SourceLimitError(SourceScanError):
    """The header exceeds a pre-scan cap (reported as ``limits``)."""


class SourceStructureError(SourceScanError):
    """The header is malformed or truncated (reported as ``decode``)."""


def scan_source(file: IO[bytes]) -> None:
    """Walk the header of a JPEG or PNG source, then rewind ``file``.

    Raises :class:`SourceLimitError` or :class:`SourceStructureError`; read
    errors propagate as ``OSError``.
    """
    size = file.seek(0, io.SEEK_END)
    file.seek(0)
    kind = sniff_bytes(file.read(SNIFF_BYTES))
    if kind is ImageFormat.JPEG:
        data, info = _scan_jpeg(file)
        _scan_jpeg_metadata(data, info)
    elif kind is ImageFormat.PNG:
        _scan_png(file, size)
    file.seek(0)


def _scan_jpeg(file: IO[bytes]) -> tuple[bytes, JpegInfo]:
    """Parse the header with the source rules through a growing window;
    return the window and what it declares."""
    window = min(_FIRST_JPEG_WINDOW, MAX_HEADER_BYTES)
    while True:
        file.seek(0)
        data = file.read(window)
        try:
            info = parse_jpeg(
                data,
                max_segments=MAX_HEADER_SEGMENTS,
                max_fill_bytes=MAX_FILL_BYTES,
                refused_markers=_LENGTHLESS_IN_PILLOW,
            )
        except JpegTruncatedError as exc:
            if len(data) < window:  # the file itself ends here
                raise SourceStructureError(str(exc)) from None
            if window >= MAX_HEADER_BYTES:
                msg = f"the JPEG header exceeds {MAX_HEADER_BYTES} bytes"
                raise SourceLimitError(msg) from None
            window = min(window * _WINDOW_GROWTH, MAX_HEADER_BYTES)
        except JpegLimitError as exc:
            raise SourceLimitError(str(exc)) from None
        except JpegHeaderError as exc:
            raise SourceStructureError(str(exc)) from None
        else:
            return data, info


def _scan_jpeg_metadata(data: bytes, info: JpegInfo) -> None:
    """Bound the EXIF and MPF structures that Pillow reads from the header.

    Pillow joins the APP1 "Exif" segments into one EXIF block: the first
    payload whole, each later one without its header. It reads the MPF
    index from the payload of the last APP2 "MPF" segment; the walk checks
    every such segment.
    """
    structures = _Structures()
    exif: list[tuple[int, int]] = []
    for segment in info.segments:
        start, end = segment.start, segment.end
        if segment.marker == APP1 and data.startswith(_EXIF_HEADER, start, end):
            exif.append((start + len(_EXIF_HEADER) if exif else start, end))
        elif segment.marker == APP2 and data.startswith(_MPF_HEADER, start, end):
            structures.add()
            _walk_tiff(data[start + len(_MPF_HEADER) : end], multi_picture=True)
    if exif:
        structures.add()
        _check_exif_size(sum(end - start for start, end in exif))
        _walk_exif(b"".join(data[start:end] for start, end in exif))


def _scan_png(file: IO[bytes], size: int) -> None:
    """Walk the chunks from the signature to IEND.

    Every chunk type must be four ASCII letters, an unknown critical chunk
    (upper-case first letter) is refused as the PNG format requires, and
    every chunk's data must lie within the file. Before the image data, the
    file must not end; after it, the walk ends at the end of the file, as
    Pillow's reader does. EXIF is bounded wherever it appears: Pillow reads
    the chunks after the image data while it decodes.
    """
    pos = len(PNG_MAGIC)
    counts = _PngCounts()
    structures = _Structures()
    while True:
        file.seek(pos)
        header = file.read(_CHUNK_HEADER)
        if len(header) < _CHUNK_HEADER:
            if counts.image_data:
                return
            msg = "the PNG ends before its image data"
            raise SourceStructureError(msg)
        length, kind = struct.unpack(">I4s", header)
        if not _CHUNK_TYPE.fullmatch(kind):
            msg = "invalid PNG chunk type"
            raise SourceStructureError(msg)
        if pos + _CHUNK_HEADER + length > size:
            msg = "a PNG chunk runs past the end of the file"
            raise SourceStructureError(msg)
        if kind == _IEND:
            return
        if kind[:1].isupper() and kind not in _CRITICAL_CHUNKS:
            msg = f"unknown critical PNG chunk {kind.decode('ascii')}"
            raise SourceStructureError(msg)
        counts.add(kind, length)
        if kind == _EXIF_CHUNK or kind in _TEXT_CHUNKS:
            _scan_png_exif(file, pos + _CHUNK_HEADER, kind, length, structures)
        pos += _CHUNK_OVERHEAD + length


class _PngCounts:
    """What the PNG walk has seen, checked against the caps."""

    __slots__ = ("data_chunks", "image_data", "metadata_bytes", "metadata_chunks")

    def __init__(self) -> None:
        self.image_data = False
        self.data_chunks = 0
        self.metadata_chunks = 0
        self.metadata_bytes = 0

    def add(self, kind: bytes, length: int) -> None:
        if kind in _FRAME_CHUNKS:
            # A frame control chunk may precede the first image data.
            self.image_data = self.image_data or kind != _FRAME_CONTROL
            self.data_chunks += 1
            if self.data_chunks > MAX_PNG_DATA_CHUNKS:
                msg = f"more than {MAX_PNG_DATA_CHUNKS} PNG image data chunks"
                raise SourceLimitError(msg)
            return
        self.metadata_chunks += 1
        self.metadata_bytes += _CHUNK_OVERHEAD + length
        if self.metadata_chunks > MAX_HEADER_SEGMENTS:
            msg = f"more than {MAX_HEADER_SEGMENTS} PNG chunks besides the image data"
            raise SourceLimitError(msg)
        if self.metadata_bytes > MAX_HEADER_BYTES:
            msg = f"PNG metadata exceeds {MAX_HEADER_BYTES} bytes"
            raise SourceLimitError(msg)


# --- metadata TIFF structures (P1) -----------------------------------------------


class _Structures:
    """The EXIF and MPF structures of one source, checked against
    :data:`MAX_TIFF_STRUCTURES` before each is read."""

    __slots__ = ("count",)

    def __init__(self) -> None:
        self.count = 0

    def add(self) -> None:
        self.count += 1
        if self.count > MAX_TIFF_STRUCTURES:
            msg = f"more than {MAX_TIFF_STRUCTURES} EXIF or MPF blocks"
            raise SourceLimitError(msg)


def _read(file: IO[bytes], start: int, length: int) -> bytes:
    file.seek(start)
    return file.read(length)


def _scan_png_exif(
    file: IO[bytes], start: int, kind: bytes, length: int, structures: _Structures
) -> None:
    """Bound the EXIF that Pillow reads from the chunk whose data (of
    ``length`` bytes) starts at ``start``: an ``eXIf`` chunk, a ``tEXt``
    chunk with the keyword ``exif``, or a text chunk "Raw profile type exif".
    Other text chunks are left alone."""
    if kind == _EXIF_CHUNK:
        structures.add()
        # Pillow puts an EXIF header in front of the chunk's data.
        _check_exif_size(len(_EXIF_HEADER) + length)
        _walk_exif(_EXIF_HEADER + _read(file, start, length))
        return
    keyword = _read(file, start, min(length, len(_RAW_PROFILE_KEYWORD)))
    if kind == _TEXT and keyword.startswith(_EXIF_KEYWORD):
        structures.add()
        _check_exif_size(length - len(_EXIF_KEYWORD))
        _walk_exif(_read(file, start, length)[len(_EXIF_KEYWORD) :])
    elif keyword == _RAW_PROFILE_KEYWORD:
        structures.add()
        if length > MAX_RAW_PROFILE_BYTES:
            msg = f"a PNG raw EXIF profile exceeds {MAX_RAW_PROFILE_BYTES} bytes"
            raise SourceLimitError(msg)
        text = _read(file, start, length)[len(_RAW_PROFILE_KEYWORD) :]
        profile = _raw_profile(kind, text)
        if profile is not None:
            _check_exif_size(len(profile))  # half the text at most: within the cap
            _walk_exif(profile)


def _raw_profile(kind: bytes, text: bytes) -> bytes | None:
    """The EXIF bytes that Pillow decodes from a "Raw profile type exif"
    chunk (``text`` follows the keyword), or ``None`` if it decodes none:
    a malformed chunk, an unknown compression, a broken stream, or text
    that is not hex after the preamble."""
    if kind == _COMPRESSED_TEXT:
        if text[:1] not in (b"", b"\x00"):
            return None  # an unknown compression method: Pillow refuses the chunk
        body = _inflate(text[1:])
    elif kind == _INTERNATIONAL_TEXT:
        # Compression flag and method, language tag, translated keyword, text.
        parts = text[2:].split(b"\x00", 2)
        if len(parts) < 3:
            return None
        if not text[0]:
            body = parts[2]
        elif not text[1]:
            body = _inflate(parts[2])
        else:
            return None  # an unknown compression method: Pillow skips the chunk
    else:
        body = text
    if body is None:
        return None
    lines = body.decode("latin-1").split("\n")[_RAW_PROFILE_PREAMBLE_LINES:]
    try:
        return bytes.fromhex("".join(lines))
    except ValueError:
        return None  # Pillow's EXIF reader fails on the same text


def _inflate(data: bytes) -> bytes | None:
    """Decompress text within :data:`MAX_RAW_PROFILE_BYTES`, as Pillow does
    within its own limit; ``None`` for a broken stream, which Pillow reads
    as no text."""
    inflater = zlib.decompressobj()
    try:
        text = inflater.decompress(data, MAX_RAW_PROFILE_BYTES)
    except zlib.error:
        return None
    if inflater.unconsumed_tail:
        msg = f"a PNG raw EXIF profile inflates beyond {MAX_RAW_PROFILE_BYTES} bytes"
        raise SourceLimitError(msg)
    return text


def _check_exif_size(size: int) -> None:
    """Refuse an EXIF block of ``size`` bytes over :data:`MAX_EXIF_BYTES`
    before it is read or joined."""
    if size > MAX_EXIF_BYTES:
        msg = f"an EXIF block exceeds {MAX_EXIF_BYTES} bytes"
        raise SourceLimitError(msg)


def _walk_exif(block: bytes) -> None:
    """Bound an EXIF block as Pillow's EXIF reader loads it: without its
    leading "Exif\\0\\0" headers, which it strips one copy at a time."""
    start = 0
    while block.startswith(_EXIF_HEADER, start):
        start += len(_EXIF_HEADER)
        if start > MAX_EXIF_HEADERS * len(_EXIF_HEADER):
            msg = f"more than {MAX_EXIF_HEADERS} EXIF headers in a row"
            raise SourceLimitError(msg)
    _walk_tiff(block[start:], multi_picture=False)


def _walk_tiff(block: bytes, *, multi_picture: bool) -> None:
    """Bound one TIFF structure as Pillow's IFD reader would load it.

    The walk visits IFD0, the chain of next IFDs, and the Exif, GPS, and
    Interoperability IFDs, each distinct offset once, and applies
    :data:`MAX_TIFF_IFDS`, :data:`MAX_IFD_ENTRIES`, and
    :data:`MAX_TIFF_VALUE_BYTES`; in an MPF index (``multi_picture``) also
    :data:`MAX_MP_IMAGES`. It is conservative: it follows more IFDs than
    Pillow does, and counts the entries that Pillow would skip.

    A block whose header Pillow refuses, or that is too short for one,
    leaves Pillow nothing to parse and is ignored. A BigTIFF header is
    refused as malformed: no real EXIF uses one. An IFD offset outside the
    block, or an entry cut short, ends that part of the walk, as it ends
    Pillow's reading.
    """
    header = block[:4]
    if header in _BIGTIFF_HEADERS:
        msg = "BigTIFF metadata is not supported"
        raise SourceStructureError(msg)
    order = _TIFF_ORDERS.get(header)
    if order is None or len(block) < _TIFF_HEADER_BYTES:
        return
    walk = _TiffWalk(block, order, multi_picture=multi_picture)
    pending = [walk.long_at(4)]
    visited: set[int] = set()
    while pending:
        offset = pending.pop()
        if offset in visited:
            continue
        visited.add(offset)
        if len(visited) > MAX_TIFF_IFDS:
            msg = f"more than {MAX_TIFF_IFDS} IFDs in a metadata block"
            raise SourceLimitError(msg)
        pending.extend(walk.ifd(offset))


class _TiffWalk:
    """One TIFF structure: reads its IFDs and adds up their value bytes."""

    __slots__ = ("_block", "_entry", "_long", "_order", "_short", "multi_picture", "value_bytes")

    def __init__(self, block: bytes, order: str, *, multi_picture: bool) -> None:
        self._block = block
        self._order = order
        self._short = struct.Struct(order + "H")
        self._long = struct.Struct(order + "L")
        self._entry = struct.Struct(order + "HHL4s")
        self.multi_picture = multi_picture
        self.value_bytes = 0

    def long_at(self, offset: int) -> int:
        value: int = self._long.unpack_from(self._block, offset)[0]
        return value

    def ifd(self, offset: int) -> list[int]:
        """Check the IFD at ``offset``; return the offsets it links to."""
        block = self._block
        if offset + _IFD_COUNT_BYTES > len(block):
            return []  # Pillow reads nothing here
        entries: int = self._short.unpack_from(block, offset)[0]
        if entries > MAX_IFD_ENTRIES:
            msg = f"a metadata IFD declares more than {MAX_IFD_ENTRIES} entries"
            raise SourceLimitError(msg)
        links: list[int] = []
        first = offset + _IFD_COUNT_BYTES
        after = first + entries * _IFD_ENTRY_BYTES
        # Only whole entries: Pillow stops reading at an entry cut short.
        stop = min(after, len(block) - _IFD_ENTRY_BYTES + 1)
        for pos in range(first, stop, _IFD_ENTRY_BYTES):
            tag, kind, count, field = self._entry.unpack_from(block, pos)
            link = self._entry_value(tag, kind, count, field)
            if link is not None:
                links.append(link)
        if after + _IFD_NEXT_BYTES <= len(block):
            following = self.long_at(after)
            if following:  # zero ends the chain
                links.append(following)
        return links

    def _entry_value(self, tag: int, kind: int, count: int, field: bytes) -> int | None:
        """Count the entry's value bytes; return the IFD offset it holds."""
        self.value_bytes += count * _TYPE_SIZES.get(kind, _UNKNOWN_TYPE_SIZE)
        if self.value_bytes > MAX_TIFF_VALUE_BYTES:
            msg = f"metadata values exceed {MAX_TIFF_VALUE_BYTES} bytes"
            raise SourceLimitError(msg)
        is_count = self.multi_picture and tag == _MP_NUMBER_OF_IMAGES
        if tag not in _SUB_IFD_TAGS and not is_count:
            return None
        value = self._first_integer(kind, count, field)
        if value is None or value < 0:
            return None  # Pillow can neither seek to it nor count with it
        if is_count:
            if value > MAX_MP_IMAGES:
                msg = f"an MPF index lists more than {MAX_MP_IMAGES} images"
                raise SourceLimitError(msg)
            return None
        return value

    def _first_integer(self, kind: int, count: int, field: bytes) -> int | None:
        """The entry's first value, read where Pillow reads it (inline when
        all values fit in the field); ``None`` for a type that is not an
        integer, no values, or a value outside the block."""
        form = _INTEGER_FORMATS.get(kind)
        if form is None or count == 0:
            return None
        size = _TYPE_SIZES[kind]
        source, at = field, 0
        if count * size > len(field):
            source, at = self._block, self._long.unpack(field)[0]
            if at + size > len(source):
                return None
        value: int = struct.unpack_from(self._order + form, source, at)[0]
        return value
