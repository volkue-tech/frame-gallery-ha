"""The pre-scan bounds the TIFF structures in a source's metadata (P1).

Pillow reads EXIF (JPEG APP1, PNG ``eXIf``, ``tEXt`` "exif", and text
chunks "Raw profile type exif") and the MPF index (JPEG APP2) as TIFF IFDs,
copying count x type-size bytes for every entry. Each bomb below is small,
passes the segment and chunk caps, and would make Pillow allocate hundreds
of MiB; the pre-scan refuses it as a limit within a second, without
allocating much.
"""

from __future__ import annotations

import io
import struct
import time
import tracemalloc
import zlib
from pathlib import Path

import pytest
from PIL import Image

from frame_gallery.imaging import source_scan
from frame_gallery.imaging.source_scan import (
    MAX_EXIF_BYTES,
    MAX_EXIF_HEADERS,
    MAX_IFD_ENTRIES,
    MAX_MP_IMAGES,
    MAX_RAW_PROFILE_BYTES,
    MAX_TIFF_IFDS,
    MAX_TIFF_STRUCTURES,
    MAX_TIFF_VALUE_BYTES,
    SourceLimitError,
    SourceScanError,
    SourceStructureError,
    scan_source,
)
from tests.support import images
from tests.support.images import (
    EXIF_HEADER,
    EXIF_IFD,
    GPS_IFD,
    INTEROP_IFD,
    MP_NUMBER_OF_IMAGES,
    TIFF_ASCII,
    TIFF_BYTE,
    TIFF_DOUBLE,
    TIFF_IFD,
    TIFF_LONG,
    TIFF_LONG8,
    TIFF_RATIONAL,
    TIFF_SBYTE,
    TIFF_SHORT,
    TIFF_SLONG,
    TIFF_SSHORT,
    TIFF_UNDEFINED,
    TiffEntry,
    TiffIfd,
)

MIB = 1024 * 1024
COLOUR = (90, 140, 200)
JPEG = images.encoded_jpeg(Image.new("RGB", (32, 18), COLOUR))

QUICK_SECONDS = 1.0
ALLOCATION_BOUND = 8 * MIB
"""What a refused scan may allocate at its peak: a few copies of the (at most
1 MiB) metadata. Pillow would allocate 100-200 MiB for the same files."""

LIMIT_VALUES = f"metadata values exceed {MAX_TIFF_VALUE_BYTES} bytes"
LIMIT_EXIF_BYTES = f"an EXIF block exceeds {MAX_EXIF_BYTES} bytes"
SHARED = 960 * 1024
"""Values that 200 entries of a bomb share: the EXIF block stays under its cap."""
LIMIT_ENTRIES = f"a metadata IFD declares more than {MAX_IFD_ENTRIES} entries"
LIMIT_IFDS = f"more than {MAX_TIFF_IFDS} IFDs in a metadata block"


def _scan(data: bytes) -> None:
    file = io.BytesIO(data)
    scan_source(file)
    assert file.tell() == 0


def _refused(data: bytes, error: type[SourceScanError], message: str) -> None:
    with pytest.raises(error, match=message) as caught:
        _scan(data)
    assert len(str(caught.value)) <= 120


def _refused_quickly(data: bytes, message: str, *, bound: int = ALLOCATION_BOUND) -> None:
    """Refused as a limit, within a second and ``bound`` bytes of allocation."""
    tracemalloc.start()
    try:
        started = time.perf_counter()
        with pytest.raises(SourceLimitError, match=message):
            _scan(data)
        elapsed = time.perf_counter() - started
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert elapsed < QUICK_SECONDS
    assert peak < bound, peak


def _exif_jpeg(block: bytes) -> bytes:
    return images.with_segments(JPEG, images.exif_segments(block))


def _mpf_jpeg(block: bytes) -> bytes:
    return images.with_segments(JPEG, images.mpf_segment(block))


def _exif_png(block: bytes) -> bytes:
    return images.exif_png(block)


def _text_exif_png(block: bytes) -> bytes:
    return images.exif_png(block, chunk=b"tEXt", keyword=b"exif\x00")


def _raw_profile_png(kind: bytes, block: bytes, *, compressed: bool = False) -> bytes:
    chunk = images.raw_profile_chunk(kind, images.raw_profile_text(block), compressed=compressed)
    return images.flat_png((8, 4), COLOUR, before=chunk)


CONTAINERS = {"jpeg": _exif_jpeg, "png-eXIf": _exif_png, "png-tEXt-exif": _text_exif_png}
"""Each way an EXIF block reaches Pillow as raw bytes."""


def _ifd0(*entries: TiffEntry, following: int | None = None) -> TiffIfd:
    return TiffIfd(entries, next=following)


def _padded_exif(size: int) -> bytes:
    """A harmless TIFF block (IFD0 without entries) of ``size`` bytes."""
    block = images.tiff([_ifd0()])
    return block + bytes(size - len(block))


# --- real metadata passes ------------------------------------------------------------


@pytest.mark.parametrize("container", sorted(CONTAINERS))
@pytest.mark.parametrize("big_endian", [False, True], ids=["II", "MM"])
def test_camera_exif_passes(container: str, big_endian: bool) -> None:
    # IFD0, Exif, GPS, Interoperability, and IFD1, with a 60 KiB MakerNote.
    block = images.camera_exif(big_endian=big_endian)
    assert 60 * 1024 < len(block) <= images.EXIF_SEGMENT_DATA
    _scan(CONTAINERS[container](block))


@pytest.mark.parametrize(
    ("kind", "compressed"),
    [(b"tEXt", False), (b"zTXt", True), (b"iTXt", False), (b"iTXt", True)],
    ids=["tEXt", "zTXt", "iTXt", "iTXt-compressed"],
)
def test_camera_exif_as_a_raw_profile_passes(kind: bytes, compressed: bool) -> None:
    data = _raw_profile_png(kind, images.camera_exif(orientation=8), compressed=compressed)
    _scan(data)
    with Image.open(io.BytesIO(data)) as image:  # Pillow reads it
        assert Image.Image.getexif(image)[images.ORIENTATION] == 8


def test_exif_split_across_segments_passes() -> None:
    # Pillow joins the segments; the walk reads the joined block.
    block = images.camera_exif(maker_note_bytes=150_000)
    data = _exif_jpeg(block)
    assert data.count(EXIF_HEADER) == 3
    _scan(data)
    with Image.open(io.BytesIO(data)) as image:
        exif = image.getexif()
        assert len(exif.get_ifd(EXIF_IFD)[images.MAKER_NOTE]) == 150_000


def test_pillow_written_metadata_passes(tmp_path: Path) -> None:
    exif = Image.Exif()
    exif[images.ORIENTATION] = 6
    png = io.BytesIO()
    Image.new("RGB", (32, 18), COLOUR).save(png, "PNG", exif=exif.tobytes())
    assert b"eXIf" in png.getvalue()
    _scan(png.getvalue())
    jpeg = images.save_jpeg(Image.new("RGB", (32, 18)), tmp_path / "o.jpg", orientation=6)
    _scan(jpeg.read_bytes())
    frames = [Image.new("RGB", (32, 18), COLOUR) for _ in range(3)]
    _scan(images.save_mpo(frames, tmp_path / "m.jpg").read_bytes())


@pytest.mark.parametrize("big_endian", [False, True], ids=["II", "MM"])
def test_mpf_index_image_limit_is_inclusive(big_endian: bool) -> None:
    _scan(_mpf_jpeg(images.mp_index(MAX_MP_IMAGES, big_endian=big_endian)))
    _refused(
        _mpf_jpeg(images.mp_index(MAX_MP_IMAGES + 1, big_endian=big_endian)),
        SourceLimitError,
        f"an MPF index lists more than {MAX_MP_IMAGES} images",
    )


# --- bombs: refused quickly, before Pillow sees them ---------------------------------


@pytest.mark.parametrize("container", sorted(CONTAINERS))
def test_shared_value_bomb_is_refused(container: str) -> None:
    # (a), (d): 200 BYTE entries that each declare the same 960 KiB of values.
    block = images.tiff_bomb(200, SHARED, filler=SHARED + 1)
    _refused_quickly(CONTAINERS[container](block), LIMIT_VALUES)


@pytest.mark.parametrize("container", sorted(CONTAINERS))
def test_entry_flood_is_refused(container: str) -> None:
    # (b): 65 535 entries, the most one IFD can declare.
    block = images.tiff([images.crowded_ifd(65_535)])
    _refused_quickly(CONTAINERS[container](block), LIMIT_ENTRIES)


def test_mpf_tag_flood_is_refused() -> None:
    # (c): one 64 KiB APP2 segment whose index IFD declares 1 500 tags.
    block = images.tiff([images.crowded_ifd(1_500)])
    _refused_quickly(_mpf_jpeg(block), LIMIT_ENTRIES)


def test_mpf_value_bomb_is_refused() -> None:
    # (c): 300 SHORT tags in one 64 KiB APP2 segment that each declare the
    # same 64 000 bytes.
    _refused_quickly(_mpf_jpeg(images.mpf_value_bomb(300)), LIMIT_VALUES)


@pytest.mark.parametrize(
    ("kind", "compressed"),
    [(b"tEXt", False), (b"zTXt", True), (b"iTXt", False), (b"iTXt", True)],
    ids=["tEXt", "zTXt", "iTXt", "iTXt-compressed"],
)
def test_raw_profile_bomb_is_refused(kind: bytes, compressed: bool) -> None:
    # (e): the shared-value bomb as hex text (256 KiB of values, 200 times).
    block = images.tiff_bomb(200, 256 * 1024, filler=256 * 1024 + 1)
    _refused_quickly(_raw_profile_png(kind, block, compressed=compressed), LIMIT_VALUES)


def test_exif_header_flood_is_refused() -> None:
    # Pillow strips each header with a copy of the rest (quadratic): 1 MiB
    # of headers would take it more than a second.
    _refused_quickly(
        _exif_jpeg(EXIF_HEADER * (MIB // 2 // len(EXIF_HEADER))),
        f"more than {MAX_EXIF_HEADERS} EXIF headers in a row",
    )


def test_exif_segment_flood_is_refused() -> None:
    # 255 full APP1 segments of harmless EXIF (16 MiB): Pillow's quadratic
    # joining would cost about 2 GB of copies and 850 MiB of resident memory.
    # The scan reads the header once (and the file is 16 MiB); it does not
    # join the segments.
    data = _exif_jpeg(_padded_exif(255 * images.EXIF_SEGMENT_DATA))
    _refused_quickly(data, LIMIT_EXIF_BYTES, bound=len(data) + ALLOCATION_BOUND)


# --- the walk: caps ------------------------------------------------------------------


def test_exif_block_limit_is_inclusive() -> None:
    # A JPEG's block keeps the first segment's header; Pillow puts one in
    # front of a PNG's eXIf chunk. Either way the header counts.
    room = MAX_EXIF_BYTES - len(EXIF_HEADER)
    for container in (_exif_jpeg, _exif_png):
        _scan(container(_padded_exif(room)))
        _refused(container(_padded_exif(room + 1)), SourceLimitError, LIMIT_EXIF_BYTES)
    _scan(_text_exif_png(_padded_exif(MAX_EXIF_BYTES)))
    _refused(_text_exif_png(_padded_exif(MAX_EXIF_BYTES + 1)), SourceLimitError, LIMIT_EXIF_BYTES)


def test_ifd_limit_is_inclusive() -> None:
    def chain(length: int) -> bytes:
        ifds = [
            TiffIfd((TiffEntry(0x0100, TIFF_SHORT, (1,)),), next=index + 1)
            for index in range(length - 1)
        ]
        return images.tiff([*ifds, TiffIfd(())])

    _scan(_exif_png(chain(MAX_TIFF_IFDS)))
    _refused(_exif_png(chain(MAX_TIFF_IFDS + 1)), SourceLimitError, LIMIT_IFDS)


def test_loops_are_walked_once() -> None:
    # IFD0's next IFD is IFD1, which links back to IFD0 through all three pointers.
    back = tuple(images.tiff_link(tag, 0) for tag in (EXIF_IFD, GPS_IFD, INTEROP_IFD))
    block = images.tiff([_ifd0(following=1), TiffIfd(back, next=0)])
    _scan(_exif_png(block))


def test_entry_limit_is_inclusive() -> None:
    _scan(_exif_png(images.tiff([images.crowded_ifd(MAX_IFD_ENTRIES)])))
    _refused(
        _exif_png(images.tiff([images.crowded_ifd(MAX_IFD_ENTRIES + 1)])),
        SourceLimitError,
        LIMIT_ENTRIES,
    )


def _declaring(kind: int, count: int) -> bytes:
    """IFD0 with one entry declaring ``count`` values of ``kind`` at offset 8."""
    return images.tiff([_ifd0(TiffEntry(0x0100, kind, count=count, field=8))])


@pytest.mark.parametrize(
    ("kind", "size"),
    [
        (TIFF_BYTE, 1),
        (TIFF_ASCII, 1),
        (TIFF_SHORT, 2),
        (TIFF_LONG, 4),
        (TIFF_RATIONAL, 8),
        (TIFF_UNDEFINED, 1),
        (TIFF_DOUBLE, 8),
        (TIFF_LONG8, 8),
        (99, 1),  # unknown: Pillow skips it, the walk counts one byte per value
    ],
    ids=["byte", "ascii", "short", "long", "rational", "undefined", "double", "long8", "unknown"],
)
def test_value_byte_limit_is_inclusive_for_each_type(kind: int, size: int) -> None:
    # Declared counts are checked whether or not the values exist.
    _scan(_exif_png(_declaring(kind, MAX_TIFF_VALUE_BYTES // size)))
    _refused(
        _exif_png(_declaring(kind, MAX_TIFF_VALUE_BYTES // size + 1)),
        SourceLimitError,
        LIMIT_VALUES,
    )


def test_a_huge_count_is_a_limit() -> None:
    # 2**32 - 1 doubles: 32 GiB declared.
    _refused(_exif_png(_declaring(TIFF_DOUBLE, 0xFFFF_FFFF)), SourceLimitError, LIMIT_VALUES)


def test_value_bytes_add_up_across_ifds() -> None:
    half = MAX_TIFF_VALUE_BYTES // 2

    def split(second: int) -> bytes:
        return images.tiff(
            [
                _ifd0(
                    TiffEntry(0x0100, TIFF_UNDEFINED, count=half, field=8),
                    images.tiff_link(EXIF_IFD, 1),
                ),
                TiffIfd((TiffEntry(0x9000, TIFF_UNDEFINED, count=second, field=8),)),
            ]
        )

    # The pointer entry declares one LONG (4 bytes) as well.
    _scan(_exif_png(split(half - 4)))
    _refused(_exif_png(split(half - 3)), SourceLimitError, LIMIT_VALUES)


def test_inline_values_count(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(source_scan, "MAX_TIFF_VALUE_BYTES", 8)
    pair = TiffEntry(0x0100, TIFF_SHORT, (1, 2))  # 4 bytes, inline
    _scan(_exif_png(images.tiff([_ifd0(pair, pair)])))
    _refused(
        _exif_png(images.tiff([_ifd0(pair, pair, pair)])),
        SourceLimitError,
        "metadata values exceed 8 bytes",
    )


# --- the walk: which IFDs it follows -----------------------------------------------------


CROWDED = images.crowded_ifd(MAX_IFD_ENTRIES + 1)
"""An IFD that the walk refuses when it reaches it."""


@pytest.mark.parametrize("tag", [EXIF_IFD, GPS_IFD])
def test_exif_and_gps_pointers_are_followed(tag: int) -> None:
    block = images.tiff([_ifd0(images.tiff_link(tag, 1)), CROWDED])
    _refused(_exif_png(block), SourceLimitError, LIMIT_ENTRIES)


def test_interoperability_pointer_is_followed() -> None:
    exif = TiffIfd((images.tiff_link(INTEROP_IFD, 2),))
    block = images.tiff([_ifd0(images.tiff_link(EXIF_IFD, 1)), exif, CROWDED])
    _refused(_exif_png(block), SourceLimitError, LIMIT_ENTRIES)


def test_next_ifd_is_followed() -> None:
    block = images.tiff([_ifd0(following=1), CROWDED])
    _refused(_exif_png(block), SourceLimitError, LIMIT_ENTRIES)


def test_mpf_next_ifd_is_followed() -> None:
    index = TiffIfd((TiffEntry(MP_NUMBER_OF_IMAGES, TIFF_LONG, (2,)),), next=1)
    _refused(_mpf_jpeg(images.tiff([index, CROWDED])), SourceLimitError, LIMIT_ENTRIES)


def test_other_tags_are_not_followed() -> None:
    # A LONG that is no IFD pointer (here StripOffsets) is not an offset to walk.
    block = images.tiff([_ifd0(images.tiff_link(0x0111, 1)), CROWDED])
    _scan(_exif_png(block))


# IFD0 holds one pointer entry; the crowded IFD follows at offset 26 (8 header
# bytes and an 18-byte IFD0), or at 34 when the pointer's values (8 bytes) sit
# after IFD0.


@pytest.mark.parametrize(
    ("kind", "values"),
    [
        (TIFF_SHORT, (26,)),
        (TIFF_LONG, (26,)),
        (TIFF_SBYTE, (26,)),
        (TIFF_SSHORT, (26,)),
        (TIFF_SLONG, (26,)),
        (TIFF_IFD, (26,)),
        (TIFF_LONG8, (34,)),  # out of line
        (TIFF_LONG, (34, 0)),  # two values, out of line: Pillow keeps the first
        (TIFF_SHORT, (26, 0)),  # two values, inline
    ],
    ids=["short", "long", "sbyte", "sshort", "slong", "ifd", "long8", "long-pair", "short-pair"],
)
def test_integer_pointers_are_followed(kind: int, values: tuple[int, ...]) -> None:
    block = images.tiff([_ifd0(TiffEntry(EXIF_IFD, kind, values)), CROWDED])
    _refused(_exif_png(block), SourceLimitError, LIMIT_ENTRIES)


@pytest.mark.parametrize(
    "entry",
    [
        TiffEntry(EXIF_IFD, TIFF_BYTE, b"\x1a"),
        TiffEntry(EXIF_IFD, TIFF_UNDEFINED, b"\x1a\x00\x00\x00"),
        TiffEntry(EXIF_IFD, TIFF_ASCII, b"\x1a\x00"),
        TiffEntry(EXIF_IFD, TIFF_RATIONAL, (34, 1)),
        TiffEntry(EXIF_IFD, TIFF_DOUBLE, (34.0,)),
        TiffEntry(EXIF_IFD, TIFF_SLONG, (-26,)),
        TiffEntry(EXIF_IFD, TIFF_LONG, count=0, field=26),
        TiffEntry(EXIF_IFD, TIFF_LONG, count=2, field=100_000),  # values outside the block
        TiffEntry(EXIF_IFD, TIFF_LONG, (100_000,)),  # an IFD outside the block
    ],
    ids=[
        "byte",
        "undefined",
        "ascii",
        "rational",
        "double",
        "negative",
        "no-values",
        "values-outside",
        "offset-outside",
    ],
)
def test_pointers_pillow_cannot_use_are_not_followed(entry: TiffEntry) -> None:
    # Pillow decodes these to bytes, text, fractions, or a negative number (or
    # reads nothing): it cannot seek to them.
    _scan(_exif_png(images.tiff([_ifd0(entry), CROWDED])))


def test_a_pointer_to_offset_zero_reads_the_header() -> None:
    # Pillow would read an IFD at offset 0: "II" as an entry count of 18 761.
    block = images.tiff([_ifd0(TiffEntry(EXIF_IFD, TIFF_LONG, (0,)))])
    _refused(_exif_png(block), SourceLimitError, LIMIT_ENTRIES)


def test_offsets_outside_the_block_end_the_walk() -> None:
    _scan(_exif_png(b"II*\x00" + struct.pack("<L", 100_000)))  # IFD0
    empty = images.tiff([_ifd0()])
    _scan(_exif_png(empty[:-4] + struct.pack("<L", 100_000)))  # the next IFD
    _scan(_exif_png(empty[:9]))  # IFD0 at 8: one byte of its entry count


def test_an_ifd_cut_short_is_walked_as_far_as_it_goes() -> None:
    # IFD0 declares 10 entries; the block ends after the second. Pillow reads
    # the whole entries only, and no next-IFD offset.
    ten = images.tiff([images.crowded_ifd(10)])
    _scan(_exif_png(ten[: 8 + 2 + 2 * 12 + 5]))
    # The entries that are there still count.
    big = TiffEntry(0x0100, TIFF_UNDEFINED, count=MAX_TIFF_VALUE_BYTES + 1, field=8)
    shorts = images.crowded_ifd(8).entries
    cut = images.tiff([TiffIfd((shorts[0], big, *shorts[1:]))])
    _refused(_exif_png(cut[: 8 + 2 + 2 * 12]), SourceLimitError, LIMIT_VALUES)


def test_mp_image_count_outside_an_mpf_index_is_ignored() -> None:
    entry = TiffEntry(MP_NUMBER_OF_IMAGES, TIFF_LONG, (MAX_MP_IMAGES + 1,))
    _scan(_exif_png(images.tiff([_ifd0(entry)])))


@pytest.mark.parametrize(
    ("entry", "refused"),
    [
        (TiffEntry(MP_NUMBER_OF_IMAGES, TIFF_SHORT, (MAX_MP_IMAGES + 1,)), True),
        (TiffEntry(MP_NUMBER_OF_IMAGES, TIFF_LONG, (MAX_MP_IMAGES + 1, 0)), True),
        (TiffEntry(MP_NUMBER_OF_IMAGES, TIFF_SLONG, (-5,)), False),
        (TiffEntry(MP_NUMBER_OF_IMAGES, TIFF_RATIONAL, (1000, 1)), False),
    ],
    ids=["short", "first-of-two", "negative", "rational"],
)
def test_mp_image_count_types(entry: TiffEntry, refused: bool) -> None:
    data = _mpf_jpeg(images.tiff([_ifd0(entry)]))
    if refused:
        _refused(data, SourceLimitError, f"an MPF index lists more than {MAX_MP_IMAGES} images")
    else:
        _scan(data)


# --- the walk: headers ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("header", "big_endian"),
    [(b"II\x00*", False), (b"MM*\x00", True)],
    ids=["II-reversed", "MM-reversed"],
)
def test_reversed_magic_numbers_are_walked(header: bytes, big_endian: bool) -> None:
    # Pillow accepts these headers with the byte order of their first two bytes.
    block = images.tiff([images.crowded_ifd(MAX_IFD_ENTRIES + 1)], big_endian=big_endian)
    _refused(_exif_png(header + block[4:]), SourceLimitError, LIMIT_ENTRIES)


@pytest.mark.parametrize("header", [b"II+\x00", b"MM\x00+"])
def test_bigtiff_metadata_is_malformed(header: bytes) -> None:
    block = header + bytes(12)
    _refused(_exif_png(block), SourceStructureError, "BigTIFF metadata is not supported")


@pytest.mark.parametrize(
    "block",
    [
        b"",
        b"II*\x00\x08\x00",  # too short for a header
        b"XX*\x00" + images.tiff_bomb(200, SHARED, filler=SHARED + 1)[4:],  # not TIFF
    ],
    ids=["empty", "short", "not-tiff"],
)
def test_blocks_pillow_cannot_read_are_ignored(block: bytes) -> None:
    data = _exif_png(block)
    _scan(data)
    with Image.open(io.BytesIO(data)) as image:
        # Pillow's EXIF reader parses nothing: it fails, or finds no tags.
        try:
            exif = Image.Image.getexif(image)
        except (SyntaxError, struct.error):
            return
        assert not exif


def test_exif_header_limit_is_inclusive() -> None:
    # A JPEG's first Exif segment has one header of its own; Pillow adds one
    # in front of a PNG's eXIf chunk.
    bomb = images.tiff_bomb(2, MAX_TIFF_VALUE_BYTES)
    extra = EXIF_HEADER * (MAX_EXIF_HEADERS - 1)
    for container in (_exif_jpeg, _exif_png):
        _refused(container(extra + bomb), SourceLimitError, LIMIT_VALUES)
        _refused(
            container(EXIF_HEADER + extra + bomb),
            SourceLimitError,
            f"more than {MAX_EXIF_HEADERS} EXIF headers in a row",
        )


def test_later_exif_segments_lose_their_header() -> None:
    # A first segment with the header only, then the bomb: Pillow joins them.
    header_only = images.jpeg_segment(0xE1, EXIF_HEADER)
    data = images.with_segments(
        JPEG, header_only + images.exif_segments(images.tiff_bomb(2, MAX_TIFF_VALUE_BYTES))
    )
    _refused(data, SourceLimitError, LIMIT_VALUES)


# --- how many structures -------------------------------------------------------------------


def test_jpeg_structure_limit_is_inclusive() -> None:
    # EXIF counts once, however many segments carry it; each MPF segment counts.
    exif = images.exif_segments(images.camera_exif(maker_note_bytes=150_000))
    mpf = images.mpf_segment(images.mp_index(2))
    _scan(images.with_segments(JPEG, exif + mpf * (MAX_TIFF_STRUCTURES - 1)))
    _refused(
        images.with_segments(JPEG, exif + mpf * MAX_TIFF_STRUCTURES),
        SourceLimitError,
        f"more than {MAX_TIFF_STRUCTURES} EXIF or MPF blocks",
    )


def test_png_structure_limit_is_inclusive() -> None:
    block = images.camera_exif(maker_note_bytes=100)
    chunks = [
        images.png_chunk(b"eXIf", block),
        images.png_chunk(b"tEXt", b"exif\x00" + block),
        images.raw_profile_chunk(b"zTXt", images.raw_profile_text(block)),
        images.raw_profile_chunk(b"iTXt", images.raw_profile_text(block)),
    ]
    _scan(images.flat_png((8, 4), COLOUR, before=b"".join(chunks)))
    _refused(
        images.flat_png((8, 4), COLOUR, before=b"".join(chunks), after=chunks[0]),
        SourceLimitError,
        f"more than {MAX_TIFF_STRUCTURES} EXIF or MPF blocks",
    )


# --- PNG text chunks ---------------------------------------------------------------------

BOMB = images.tiff_bomb(200, 256 * 1024, filler=256 * 1024 + 1)


@pytest.mark.parametrize(
    "chunk",
    [
        images.png_chunk(b"tEXt", b"Comment\x00" + BOMB),
        images.png_chunk(b"zTXt", b"exif\x00\x00" + zlib.compress(BOMB)),
        images.png_chunk(b"iTXt", b"exif\x00\x00\x00\x00\x00" + BOMB),
        images.png_chunk(b"tEXt", images.RAW_PROFILE_KEYWORD[:-1]),  # no text at all
        images.png_chunk(b"zTXt", images.RAW_PROFILE_KEYWORD + b"\x01" + zlib.compress(BOMB)),
        images.png_chunk(b"zTXt", images.RAW_PROFILE_KEYWORD + b"\x00not a zlib stream"),
        images.png_chunk(b"iTXt", images.RAW_PROFILE_KEYWORD + b"\x01\x01\x00\x00" + BOMB),
        images.png_chunk(b"iTXt", images.RAW_PROFILE_KEYWORD + b"\x00\x00no separators"),
        images.png_chunk(b"iTXt", images.RAW_PROFILE_KEYWORD + b"\x01\x00\x00\x00broken"),
        images.png_chunk(b"tEXt", images.RAW_PROFILE_KEYWORD + b"\n\nexif\n  10\nnot hex"),
    ],
    ids=[
        "other-keyword",
        "zTXt-exif",
        "iTXt-exif",
        "raw-without-text",
        "zTXt-unknown-method",
        "zTXt-broken-stream",
        "iTXt-unknown-method",
        "iTXt-malformed",
        "iTXt-broken-stream",
        "not-hex",
    ],
)
def test_text_that_pillow_reads_no_exif_from_is_ignored(chunk: bytes) -> None:
    data = images.flat_png((8, 4), COLOUR, before=chunk)
    _scan(data)
    try:
        with Image.open(io.BytesIO(data)) as image:
            exif = Image.Image.getexif(image)
    except (OSError, SyntaxError, TypeError, ValueError):
        return  # Pillow refuses the file or the chunk, or its EXIF reader fails
    assert not exif


def test_raw_profile_chunk_limit_is_inclusive() -> None:
    room = MAX_RAW_PROFILE_BYTES - len(images.RAW_PROFILE_KEYWORD)
    fits = images.png_chunk(b"tEXt", images.RAW_PROFILE_KEYWORD + b"\n" * room)
    _scan(images.flat_png((8, 4), COLOUR, before=fits))
    over = images.png_chunk(b"tEXt", images.RAW_PROFILE_KEYWORD + b"\n" * (room + 1))
    _refused(
        images.flat_png((8, 4), COLOUR, before=over),
        SourceLimitError,
        f"a PNG raw EXIF profile exceeds {MAX_RAW_PROFILE_BYTES} bytes",
    )


@pytest.mark.parametrize("kind", [b"zTXt", b"iTXt"])
def test_raw_profile_inflation_limit_is_inclusive(kind: bytes) -> None:
    def png(text_bytes: int) -> bytes:
        text = b"\n" * text_bytes
        chunk = images.raw_profile_chunk(kind, text, compressed=True)
        return images.flat_png((8, 4), COLOUR, before=chunk)

    _scan(png(MAX_RAW_PROFILE_BYTES))
    _refused(
        png(MAX_RAW_PROFILE_BYTES + 1),
        SourceLimitError,
        f"a PNG raw EXIF profile inflates beyond {MAX_RAW_PROFILE_BYTES} bytes",
    )


def test_exif_after_the_image_data_is_bounded() -> None:
    # Pillow reads the chunks after the image data while it decodes.
    data = images.flat_png((8, 4), COLOUR, after=images.png_chunk(b"eXIf", BOMB))
    _refused(data, SourceLimitError, LIMIT_VALUES)
