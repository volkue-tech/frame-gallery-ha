"""Deadlines: remaining time, expiry, children, and clamping (§7.1)."""

from __future__ import annotations

import pytest

from frame_gallery.budget.clock import Clock
from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.errors import FrameGalleryError
from frame_gallery.randomness import SeededRandomSource
from tests.support.clock import FakeClock

START = 1000.0


def _deadline(seconds: float = 10.0, name: str = "phase") -> tuple[FakeClock, Deadline]:
    clock = FakeClock(START)
    return clock, Deadline(clock, START + seconds, name)


class TestRemainingAndExpiry:
    def test_remaining_counts_down_with_the_clock(self) -> None:
        clock, deadline = _deadline(10.0)
        assert deadline.remaining() == 10.0
        clock.advance(4.0)
        assert deadline.remaining() == 6.0
        assert not deadline.expired()

    def test_expired_at_exactly_expires_at(self) -> None:
        clock, deadline = _deadline(10.0)
        clock.advance_to(deadline.expires_at - 0.001)
        assert not deadline.expired()
        clock.advance_to(deadline.expires_at)
        assert deadline.expired()
        assert deadline.remaining() == 0.0

    def test_remaining_is_never_negative(self) -> None:
        clock, deadline = _deadline(10.0)
        clock.advance(25.0)
        assert deadline.remaining() == 0.0
        assert deadline.expired()

    def test_a_deadline_in_the_past_is_expired_immediately(self) -> None:
        clock = FakeClock(START)
        deadline = Deadline(clock, START - 5.0, "past")
        assert deadline.expired()
        assert deadline.remaining() == 0.0

    def test_attributes_and_clock(self) -> None:
        clock, deadline = _deadline(10.0, "configure")
        assert deadline.name == "configure"
        assert deadline.expires_at == START + 10.0
        assert deadline.clock is clock

    def test_repr_names_the_deadline(self) -> None:
        _, deadline = _deadline(10.0, "content")
        assert repr(deadline) == "Deadline('content', expires_at=1010.0)"


class TestCheck:
    def test_check_passes_before_expiry(self) -> None:
        clock, deadline = _deadline(10.0)
        clock.advance(9.5)
        deadline.check()

    @pytest.mark.parametrize("elapsed", [10.0, 10.5, 500.0])
    def test_check_raises_at_and_after_expiry(self, elapsed: float) -> None:
        clock, deadline = _deadline(10.0, "discovery")
        clock.advance(elapsed)
        with pytest.raises(DeadlineExceeded) as caught:
            deadline.check()
        assert caught.value.deadline_name == "discovery"
        assert str(caught.value) == "deadline 'discovery' exceeded"
        assert isinstance(caught.value, FrameGalleryError)


class TestAfter:
    def test_after_counts_from_now(self) -> None:
        clock = FakeClock(START)
        clock.advance(7.0)
        deadline = Deadline.after(clock, 5.0, "request")
        assert deadline.expires_at == START + 12.0
        assert deadline.name == "request"
        assert deadline.clock is clock

    @pytest.mark.parametrize("seconds", [0.0, -0.5, -30.0])
    def test_after_with_zero_or_negative_seconds_expires_now(self, seconds: float) -> None:
        clock = FakeClock(START)
        deadline = Deadline.after(clock, seconds, "now")
        assert deadline.expires_at == START
        assert deadline.expired()


class TestChild:
    def test_child_shorter_than_parent(self) -> None:
        clock, parent = _deadline(10.0)
        clock.advance(2.0)
        child = parent.child(3.0, "helper")
        assert child.expires_at == START + 5.0
        assert child.name == "helper"
        assert child.clock is clock

    def test_child_is_capped_at_the_parent(self) -> None:
        clock, parent = _deadline(10.0)
        clock.advance(8.0)
        child = parent.child(20.0, "download")
        assert child.expires_at == parent.expires_at
        assert child.remaining() == 2.0

    @pytest.mark.parametrize("seconds", [0.0, -1.0, -1000.0])
    def test_zero_or_negative_child_expires_now(self, seconds: float) -> None:
        clock, parent = _deadline(10.0)
        clock.advance(3.0)
        child = parent.child(seconds, "late")
        assert child.expires_at == START + 3.0
        assert child.expired()

    def test_child_of_an_expired_parent_is_expired(self) -> None:
        clock, parent = _deadline(10.0)
        clock.advance(12.0)
        child = parent.child(5.0, "late")
        assert child.expires_at == parent.expires_at
        assert child.expired()

    def test_child_is_never_later_than_parent(self) -> None:
        rng = SeededRandomSource(114)
        for _ in range(500):
            clock, parent = _deadline(rng.random() * 120.0)
            clock.advance(rng.random() * 130.0)
            seconds = (rng.random() - 0.25) * 200.0
            child = parent.child(seconds, "child")
            assert child.expires_at <= parent.expires_at
            assert child.expires_at <= clock.monotonic() + max(0.0, seconds)
            grandchild = child.child(seconds * 2.0, "grandchild")
            assert grandchild.expires_at <= child.expires_at


class TestCapAt:
    def test_cap_at_an_earlier_time(self) -> None:
        _, parent = _deadline(60.0, "content")
        capped = parent.cap_at(START + 58.0, "attempts")
        assert capped.expires_at == START + 58.0
        assert capped.name == "attempts"
        assert capped.clock is parent.clock

    def test_cap_at_a_later_time_keeps_the_parent(self) -> None:
        _, parent = _deadline(60.0)
        capped = parent.cap_at(START + 90.0, "later")
        assert capped.expires_at == parent.expires_at

    def test_cap_at_does_not_depend_on_the_clock(self) -> None:
        clock, parent = _deadline(60.0)
        clock.advance(59.0)
        capped = parent.cap_at(START + 58.0, "attempts")
        assert capped.expires_at == START + 58.0
        assert capped.expired()


class TestClamp:
    def test_clamp_returns_the_timeout_when_time_remains(self) -> None:
        clock, deadline = _deadline(10.0)
        clock.advance(2.0)
        assert deadline.clamp(3.0) == 3.0

    def test_clamp_returns_the_remaining_time_when_shorter(self) -> None:
        clock, deadline = _deadline(10.0)
        clock.advance(8.5)
        assert deadline.clamp(5.0) == 1.5

    def test_clamp_with_timeout_equal_to_remaining(self) -> None:
        clock, deadline = _deadline(10.0)
        clock.advance(5.0)
        assert deadline.clamp(5.0) == 5.0

    @pytest.mark.parametrize("timeout", [0.0, -0.001, -5.0])
    def test_clamp_rejects_non_positive_timeouts(self, timeout: float) -> None:
        _, deadline = _deadline(10.0)
        with pytest.raises(ValueError, match="timeout must be positive"):
            deadline.clamp(timeout)

    def test_non_positive_timeout_is_reported_even_after_expiry(self) -> None:
        clock, deadline = _deadline(10.0)
        clock.advance(20.0)
        with pytest.raises(ValueError, match="timeout must be positive"):
            deadline.clamp(0.0)

    @pytest.mark.parametrize("elapsed", [10.0, 11.0])
    def test_clamp_raises_when_no_time_remains(self, elapsed: float) -> None:
        clock, deadline = _deadline(10.0, "download")
        clock.advance(elapsed)
        with pytest.raises(DeadlineExceeded) as caught:
            deadline.clamp(5.0)
        assert caught.value.deadline_name == "download"

    def test_clamp_never_exceeds_timeout_or_remaining(self) -> None:
        rng = SeededRandomSource(20)
        for _ in range(500):
            clock, deadline = _deadline(rng.random() * 60.0)
            clock.advance(rng.random() * 59.0)
            timeout = 0.001 + rng.random() * 30.0
            if deadline.remaining() <= 0:
                with pytest.raises(DeadlineExceeded):
                    deadline.clamp(timeout)
                continue
            clamped = deadline.clamp(timeout)
            assert 0 < clamped <= timeout
            assert clamped <= deadline.remaining()
            assert clamped == min(timeout, deadline.remaining())


def test_fake_clock_satisfies_the_clock_protocol() -> None:
    clock: Clock = FakeClock(START)
    deadline = Deadline.after(clock, 1.0, "typed")
    assert deadline.remaining() == 1.0
