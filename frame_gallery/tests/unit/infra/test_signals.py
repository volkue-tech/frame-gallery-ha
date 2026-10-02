"""Stop requests and their deferral (§7.6)."""

from __future__ import annotations

import os
import signal
import time
from collections.abc import Callable, Iterator
from types import FrameType

import pytest

from frame_gallery.app.signals import (
    CancellationController,
    deferring,
    install_sigterm_handler,
)
from frame_gallery.errors import Cancelled


class RecordingHandler:
    """Stands in as the "previous" handler, so a stray SIGTERM never kills pytest."""

    def __init__(self) -> None:
        self.signals: list[int] = []

    def __call__(self, signum: int, frame: FrameType | None) -> None:
        self.signals.append(signum)


@pytest.fixture
def previous_handler() -> Iterator[RecordingHandler]:
    original = signal.getsignal(signal.SIGTERM)
    recorder = RecordingHandler()
    signal.signal(signal.SIGTERM, recorder)
    try:
        yield recorder
    finally:
        signal.signal(signal.SIGTERM, original)


def _spin_until(condition: Callable[[], bool], limit_s: float = 2.0) -> None:
    """Run bytecode until ``condition`` holds; Python handlers run between bytecodes."""
    end = time.monotonic() + limit_s
    while not condition() and time.monotonic() < end:
        pass


def _send_sigterm() -> None:
    os.kill(os.getpid(), signal.SIGTERM)


def _send_sigterm_and_run_handlers() -> None:
    _send_sigterm()
    _spin_until(lambda: False)


def _deferred(controller: CancellationController) -> bool:
    """Read afresh (mypy would keep an earlier narrowing of the property)."""
    return controller.deferred


# --- the controller ---------------------------------------------------------


def test_initially_no_stop() -> None:
    controller = CancellationController()
    assert not controller.stop_requested
    assert not controller.deferred
    controller.check()


def test_request_stop_raises_cancelled() -> None:
    controller = CancellationController()
    with pytest.raises(Cancelled):
        controller.request_stop()
    assert controller.stop_requested


def test_check_raises_after_a_stop_request() -> None:
    controller = CancellationController()
    with pytest.raises(Cancelled):
        controller.request_stop()
    with pytest.raises(Cancelled):
        controller.check()


def test_a_repeated_request_while_unwinding_does_not_raise_again() -> None:
    controller = CancellationController()
    with pytest.raises(Cancelled):
        controller.request_stop()
    controller.request_stop()
    assert controller.stop_requested


def test_a_deferred_request_is_only_recorded() -> None:
    controller = CancellationController()
    controller.begin_deferral()
    assert controller.deferred
    controller.request_stop()
    assert controller.stop_requested
    controller.check()
    assert controller.end_deferral() is True
    assert not _deferred(controller)
    with pytest.raises(Cancelled):
        controller.check()


def test_a_request_after_a_deferral_ended_raises() -> None:
    controller = CancellationController()
    controller.begin_deferral()
    controller.request_stop()
    assert controller.end_deferral() is True
    with pytest.raises(Cancelled):
        controller.request_stop()


def test_check_marks_the_run_as_unwinding() -> None:
    controller = CancellationController()
    controller.begin_deferral()
    controller.request_stop()
    controller.end_deferral()
    with pytest.raises(Cancelled):
        controller.check()
    controller.request_stop()


def test_end_deferral_without_a_request_reports_false() -> None:
    controller = CancellationController()
    controller.begin_deferral()
    assert controller.end_deferral() is False
    controller.check()


def test_deferrals_nest() -> None:
    controller = CancellationController()
    controller.begin_deferral()
    controller.begin_deferral()
    controller.request_stop()
    assert controller.end_deferral() is True
    assert _deferred(controller)
    controller.check()
    assert controller.end_deferral() is True
    with pytest.raises(Cancelled):
        controller.check()


def test_end_deferral_without_begin_is_an_error() -> None:
    controller = CancellationController()
    with pytest.raises(RuntimeError, match="without begin_deferral"):
        controller.end_deferral()


# --- the SIGTERM handler ----------------------------------------------------


def test_sigterm_raises_cancelled_in_the_main_thread(
    previous_handler: RecordingHandler,
) -> None:
    controller = CancellationController()
    restore = install_sigterm_handler(controller)
    try:
        with pytest.raises(Cancelled):
            _send_sigterm_and_run_handlers()
    finally:
        restore()
    assert controller.stop_requested
    assert previous_handler.signals == []


def test_sigterm_during_a_deferral_is_recorded(previous_handler: RecordingHandler) -> None:
    controller = CancellationController()
    restore = install_sigterm_handler(controller)
    try:
        controller.begin_deferral()
        _send_sigterm()
        _spin_until(lambda: controller.stop_requested)
        assert controller.stop_requested
        assert controller.end_deferral() is True
        with pytest.raises(Cancelled):
            controller.check()
    finally:
        restore()


def test_restore_reinstalls_the_previous_handler(previous_handler: RecordingHandler) -> None:
    received = previous_handler.signals
    restore = install_sigterm_handler(CancellationController())
    assert signal.getsignal(signal.SIGTERM) is not previous_handler
    restore()
    assert signal.getsignal(signal.SIGTERM) is previous_handler
    restore()
    assert signal.getsignal(signal.SIGTERM) is previous_handler
    _send_sigterm()
    _spin_until(lambda: bool(received))
    assert received == [signal.SIGTERM]


def test_restore_falls_back_to_the_default_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[object] = []

    def fake_signal(signum: int, handler: object) -> None:
        calls.append(handler)

    monkeypatch.setattr(signal, "signal", fake_signal)
    restore = install_sigterm_handler(CancellationController())
    restore()
    assert calls[-1] is signal.SIG_DFL
    assert len(calls) == 2


def _stop_inside(controller: CancellationController) -> None:
    with deferring(controller):
        controller.request_stop()  # only recorded inside the block
        assert controller.stop_requested


def test_deferring_holds_a_request_until_the_block_ends() -> None:
    controller = CancellationController()
    with pytest.raises(Cancelled):
        _stop_inside(controller)
    assert not controller.deferred


def test_deferring_without_a_request_raises_nothing() -> None:
    controller = CancellationController()
    with deferring(controller):
        assert controller.deferred
    assert not controller.deferred


def _stop_and_fail_inside(controller: CancellationController) -> None:
    with deferring(controller):
        controller.request_stop()
        raise KeyError


def test_deferring_lets_the_blocks_own_exception_through() -> None:
    controller = CancellationController()
    with pytest.raises(KeyError):
        _stop_and_fail_inside(controller)
    assert controller.stop_requested
    assert not controller.deferred
    with pytest.raises(Cancelled):
        controller.check()


def test_deferring_inside_an_outer_deferral_leaves_the_request_pending() -> None:
    controller = CancellationController(start_deferred=True)
    with deferring(controller):
        controller.request_stop()
    assert controller.deferred  # the start deferral is still active
    controller.end_start_deferral()
    with pytest.raises(Cancelled):
        controller.check()
