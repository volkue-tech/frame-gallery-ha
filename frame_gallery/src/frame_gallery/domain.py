"""Value types shared across the core (standard library only)."""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

_HEX_COLOUR = re.compile(r"#([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})([0-9A-Fa-f]{2})")

QUALIFIED_ID_MAX_LENGTH: Final = 200
PROVIDER_KEY_PATTERN: Final = re.compile(r"[a-z]{2,16}")
NATIVE_ID_PATTERN: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]*")
"""Native identifiers are plain tokens; adapters apply stricter patterns."""


def is_qualified_id(value: object) -> bool:
    """Whether ``value`` is a persistent identifier ``<provider key>:<native id>``
    of at most 200 characters (the form history and the ledger store)."""
    if not isinstance(value, str) or len(value) > QUALIFIED_ID_MAX_LENGTH:
        return False
    key, separator, native = value.partition(":")
    return (
        separator == ":"
        and PROVIDER_KEY_PATTERN.fullmatch(key) is not None
        and NATIVE_ID_PATTERN.fullmatch(native) is not None
    )


@dataclass(frozen=True, slots=True)
class Size:
    """Pixel dimensions. Both values are positive integers."""

    width: int
    height: int

    def __post_init__(self) -> None:
        for name, value in (("width", self.width), ("height", self.height)):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                msg = f"{name} must be a positive integer, got {value!r}"
                raise ValueError(msg)

    @property
    def ratio(self) -> float:
        """Width divided by height."""
        return self.width / self.height

    @property
    def pixels(self) -> int:
        return self.width * self.height

    def transposed(self) -> Size:
        """The same size with the axes swapped (EXIF orientations 5-8)."""
        return Size(self.height, self.width)


CANVAS = Size(3840, 2160)
"""The television canvas: every delivered JPEG has exactly this size."""


class FitMode(enum.StrEnum):
    """How an artwork is fitted onto the canvas (D-005, §11.2)."""

    CONTAIN = "contain"
    """Scale to fit entirely, never crop; margins in the background colour."""

    COVER = "cover"
    """Scale to fill the canvas; crops one axis. Only when explicitly chosen."""


@dataclass(frozen=True, slots=True)
class Rgb:
    """An 8-bit sRGB colour."""

    red: int
    green: int
    blue: int

    def __post_init__(self) -> None:
        for name, value in (("red", self.red), ("green", self.green), ("blue", self.blue)):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255:
                msg = f"{name} must be an integer in 0..255, got {value!r}"
                raise ValueError(msg)

    @classmethod
    def from_hex(cls, text: str) -> Rgb:
        """Parse ``#RRGGBB`` (either case). Raises ``ValueError`` otherwise."""
        match = _HEX_COLOUR.fullmatch(text)
        if match is None:
            msg = "colour must have the form #RRGGBB"
            raise ValueError(msg)
        return cls(*(int(part, 16) for part in match.groups()))

    def to_hex(self) -> str:
        return f"#{self.red:02x}{self.green:02x}{self.blue:02x}"

    def as_tuple(self) -> tuple[int, int, int]:
        return (self.red, self.green, self.blue)


BLACK = Rgb(0, 0, 0)


class SourceKey(enum.StrEnum):
    """The ``source`` option: which provider supplies the artwork (§9.1)."""

    LOCAL_MEDIA = "local_media"
    ART_INSTITUTE_CHICAGO = "art_institute_chicago"
    CLEVELAND_MUSEUM_OF_ART = "cleveland_museum_of_art"
    WIKIMEDIA_COMMONS = "wikimedia_commons"

    @property
    def provider_key(self) -> str:
        """The persistent history and ledger prefix of this source."""
        return _PROVIDER_KEYS[self]


_PROVIDER_KEYS = {
    SourceKey.LOCAL_MEDIA: "local",
    SourceKey.ART_INSTITUTE_CHICAGO: "aic",
    SourceKey.CLEVELAND_MUSEUM_OF_ART: "cma",
    SourceKey.WIKIMEDIA_COMMONS: "commons",
}

DEFAULT_SOURCE = SourceKey.ART_INSTITUTE_CHICAGO
"""Accepted default remote source (Q-08)."""


@dataclass(frozen=True, slots=True)
class WorkspacePaths:
    """This run's private scratch directory (§13.1)."""

    root: Path
    inbox: Path
    """``in/``: downloads, read-only for the worker."""

    outbox: Path
    """``out/``: the worker's output."""
