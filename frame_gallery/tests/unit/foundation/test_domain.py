"""Shared value types (domain.py)."""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest

from frame_gallery.config.filters import FilterField, FilterSet
from frame_gallery.domain import (
    BLACK,
    CANVAS,
    DEFAULT_SOURCE,
    FitMode,
    Rgb,
    Size,
    SourceKey,
)
from frame_gallery.providers.contract import PROVIDER_KEY_PATTERN


class TestSize:
    @pytest.mark.parametrize(
        ("width", "height"),
        [(0, 1), (1, 0), (-1, 5), (5, -1), (0, 0), (True, 5), (5, False), (1.5, 2), (2, 3.0)],
    )
    def test_rejects_non_positive_and_non_integer_values(self, width: Any, height: Any) -> None:
        with pytest.raises(ValueError, match="must be a positive integer"):
            Size(width, height)

    def test_names_the_offending_field(self) -> None:
        with pytest.raises(ValueError, match="height"):
            Size(10, 0)
        with pytest.raises(ValueError, match="width"):
            Size(0, 10)

    def test_ratio_pixels_and_transposed(self) -> None:
        size = Size(4000, 3000)
        assert size.ratio == 4000 / 3000
        assert size.pixels == 12_000_000
        assert size.transposed() == Size(3000, 4000)
        assert size.transposed().transposed() == size

    def test_is_frozen_and_comparable(self) -> None:
        size = Size(1, 2)
        assert size == Size(1, 2)
        assert hash(size) == hash(Size(1, 2))
        with pytest.raises(dataclasses.FrozenInstanceError):
            size.width = 5  # type: ignore[misc]

    def test_canvas_is_3840_by_2160(self) -> None:
        assert (CANVAS.width, CANVAS.height) == (3840, 2160)
        assert CANVAS.ratio == 16 / 9
        assert CANVAS.pixels == 8_294_400


class TestRgb:
    @pytest.mark.parametrize("value", [-1, 256, 1000, True, False, 1.0, "12", None])
    @pytest.mark.parametrize("channel", ["red", "green", "blue"])
    def test_rejects_out_of_range_and_non_integer_channels(self, channel: str, value: Any) -> None:
        channels: dict[str, Any] = {"red": 0, "green": 0, "blue": 0, channel: value}
        with pytest.raises(ValueError, match=channel):
            Rgb(**channels)

    @pytest.mark.parametrize("value", [0, 1, 128, 254, 255])
    def test_accepts_channel_bounds(self, value: int) -> None:
        assert Rgb(value, value, value).as_tuple() == (value, value, value)

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("#000000", Rgb(0, 0, 0)),
            ("#ffffff", Rgb(255, 255, 255)),
            ("#FFFFFF", Rgb(255, 255, 255)),
            ("#0A0b0C", Rgb(10, 11, 12)),
            ("#1a2B3c", Rgb(0x1A, 0x2B, 0x3C)),
        ],
    )
    def test_from_hex_accepts_either_case(self, text: str, expected: Rgb) -> None:
        assert Rgb.from_hex(text) == expected

    @pytest.mark.parametrize(
        "text",
        [
            "#12345",
            "123456",
            "#GGGGGG",
            "#1234567",
            "",
            "#",
            " #123456",
            "#123456 ",
            "#123456\n",
            "#12 456",
            "##123456",
            "0x123456",
            "#\uff11\uff12\uff13\uff14\uff15\uff16",  # full-width digits
        ],
    )
    def test_from_hex_rejects_other_forms(self, text: str) -> None:
        with pytest.raises(ValueError, match="#RRGGBB"):
            Rgb.from_hex(text)

    @pytest.mark.parametrize(
        "colour", [Rgb(0, 0, 0), Rgb(255, 255, 255), Rgb(1, 2, 3), Rgb(0xAB, 0xCD, 0xEF)]
    )
    def test_hex_round_trip(self, colour: Rgb) -> None:
        text = colour.to_hex()
        assert len(text) == 7
        assert text == text.lower()
        assert Rgb.from_hex(text) == colour
        assert Rgb.from_hex(text.upper()) == colour

    def test_to_hex_is_lowercase_and_zero_padded(self) -> None:
        assert Rgb(10, 11, 12).to_hex() == "#0a0b0c"
        assert Rgb.from_hex("#ABCDEF").to_hex() == "#abcdef"

    def test_black(self) -> None:
        assert BLACK.as_tuple() == (0, 0, 0)
        assert BLACK.to_hex() == "#000000"


class TestSourceKey:
    def test_values(self) -> None:
        assert [key.value for key in SourceKey] == [
            "local_media",
            "art_institute_chicago",
            "cleveland_museum_of_art",
        ]

    @pytest.mark.parametrize(
        ("source", "provider_key"),
        [
            (SourceKey.LOCAL_MEDIA, "local"),
            (SourceKey.ART_INSTITUTE_CHICAGO, "aic"),
            (SourceKey.CLEVELAND_MUSEUM_OF_ART, "cma"),
        ],
    )
    def test_provider_key(self, source: SourceKey, provider_key: str) -> None:
        assert source.provider_key == provider_key

    def test_provider_keys_are_distinct_valid_prefixes(self) -> None:
        keys = [source.provider_key for source in SourceKey]
        assert len(set(keys)) == len(keys)
        for key in keys:
            assert PROVIDER_KEY_PATTERN.fullmatch(key) is not None

    def test_default_source_is_the_art_institute(self) -> None:
        assert DEFAULT_SOURCE is SourceKey.ART_INSTITUTE_CHICAGO
        assert DEFAULT_SOURCE.value == "art_institute_chicago"

    def test_parses_from_option_text(self) -> None:
        assert SourceKey("cleveland_museum_of_art") is SourceKey.CLEVELAND_MUSEUM_OF_ART
        with pytest.raises(ValueError, match="bing"):
            SourceKey("bing")


class TestFitMode:
    def test_values(self) -> None:
        assert str(FitMode.CONTAIN) == "contain"
        assert str(FitMode.COVER) == "cover"
        assert [mode.value for mode in FitMode] == ["contain", "cover"]
        assert FitMode("contain") is FitMode.CONTAIN


def test_the_source_is_not_a_filter_choice() -> None:
    filters = FilterSet(source=SourceKey.LOCAL_MEDIA)
    with pytest.raises(ValueError, match="not a FilterChoice"):
        filters.choice(FilterField.SOURCE)
