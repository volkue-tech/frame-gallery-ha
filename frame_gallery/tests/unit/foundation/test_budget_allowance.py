"""Allowance counters that bound every loop (§7.1, §7.2)."""

from __future__ import annotations

from typing import Any

import pytest

from frame_gallery.budget.allowance import Allowance, AllowanceExhausted
from frame_gallery.errors import FrameGalleryError


class TestLimitValidation:
    @pytest.mark.parametrize("limit", [-1, -30, True, False, 1.5, 2.0, "3", None])
    def test_invalid_limits_are_rejected(self, limit: Any) -> None:
        with pytest.raises(ValueError, match="limit must be a non-negative integer"):
            Allowance("probes", limit)

    @pytest.mark.parametrize("limit", [0, 1, 30, 20_000])
    def test_non_negative_integer_limits_are_accepted(self, limit: int) -> None:
        allowance = Allowance("probes", limit)
        assert allowance.limit == limit
        assert allowance.name == "probes"
        assert allowance.used == 0
        assert allowance.remaining == limit


class TestTryTake:
    def test_takes_one_unit_at_a_time_until_the_limit(self) -> None:
        allowance = Allowance("probes", 3)
        assert [allowance.try_take() for _ in range(5)] == [True, True, True, False, False]
        assert allowance.used == 3
        assert allowance.remaining == 0
        assert allowance.exhausted

    def test_takes_several_units_at_once(self) -> None:
        allowance = Allowance("inspections", 300)
        assert allowance.try_take(50)
        assert allowance.used == 50
        assert allowance.remaining == 250
        assert not allowance.exhausted

    def test_is_all_or_nothing(self) -> None:
        allowance = Allowance("inspections", 10)
        assert allowance.try_take(8)
        assert not allowance.try_take(3)
        assert allowance.used == 8
        assert allowance.try_take(2)
        assert allowance.exhausted

    def test_a_zero_limit_is_exhausted_from_the_start(self) -> None:
        allowance = Allowance("none", 0)
        assert allowance.exhausted
        assert not allowance.try_take()
        assert allowance.used == 0

    @pytest.mark.parametrize("units", [0, -1, -50])
    def test_rejects_non_positive_units(self, units: int) -> None:
        allowance = Allowance("probes", 3)
        with pytest.raises(ValueError, match="units must be a positive integer"):
            allowance.try_take(units)
        assert allowance.used == 0

    def test_bounds_a_loop(self) -> None:
        allowance = Allowance("candidates", 150)
        iterations = 0
        while allowance.try_take():
            iterations += 1
        assert iterations == 150


class TestTake:
    def test_exact_exhaustion_at_the_limit(self) -> None:
        allowance = Allowance("metadata", 5)
        allowance.take(4)
        assert allowance.remaining == 1
        allowance.take()
        assert allowance.exhausted
        assert allowance.remaining == 0

    def test_raises_once_exhausted(self) -> None:
        allowance = Allowance("metadata", 2)
        allowance.take(2)
        with pytest.raises(AllowanceExhausted) as caught:
            allowance.take()
        assert caught.value.allowance_name == "metadata"
        assert str(caught.value) == "allowance 'metadata' exhausted"
        assert allowance.used == 2

    def test_raises_without_using_units_when_too_many_are_asked(self) -> None:
        allowance = Allowance("metadata", 5)
        allowance.take(3)
        with pytest.raises(AllowanceExhausted):
            allowance.take(3)
        assert allowance.used == 3

    @pytest.mark.parametrize("units", [0, -2])
    def test_rejects_non_positive_units(self, units: int) -> None:
        allowance = Allowance("probes", 3)
        with pytest.raises(ValueError, match="units must be a positive integer"):
            allowance.take(units)


@pytest.mark.parametrize("units", [True, 1.0, "1"])
def test_units_must_be_a_real_integer(units: object) -> None:
    allowance = Allowance("probes", 3)
    with pytest.raises(ValueError, match="units must be a positive integer"):
        allowance.try_take(units)  # type: ignore[arg-type]
    assert allowance.used == 0


def test_allowance_exhausted_is_a_frame_gallery_error() -> None:
    error = AllowanceExhausted("probes")
    assert isinstance(error, FrameGalleryError)
    assert error.allowance_name == "probes"


def test_repr_shows_usage() -> None:
    allowance = Allowance("probes", 30)
    allowance.take(4)
    assert repr(allowance) == "Allowance('probes', used=4, limit=30)"
