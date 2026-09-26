"""The shared error hierarchy (errors.py)."""

from __future__ import annotations

import pytest

from frame_gallery.budget.allowance import AllowanceExhausted
from frame_gallery.budget.deadline import DeadlineExceeded
from frame_gallery.errors import AlreadyRunning, Cancelled, FrameGalleryError, StateError
from frame_gallery.providers.contract import SourceError, SourceErrorKind


def test_base_is_an_exception() -> None:
    assert issubclass(FrameGalleryError, Exception)
    assert not issubclass(FrameGalleryError, (KeyboardInterrupt, SystemExit))


def _behind_a_generic_handler() -> str:
    try:
        raise Cancelled
    except Exception:  # noqa: BLE001 - the handler a stop request must pass through
        return "swallowed"


def test_a_stop_request_is_not_an_exception() -> None:
    # Like KeyboardInterrupt: no ``except Exception`` (logging, an adapter)
    # can swallow a stop request.
    assert issubclass(Cancelled, BaseException)
    assert not issubclass(Cancelled, Exception)
    assert not issubclass(Cancelled, FrameGalleryError)
    with pytest.raises(Cancelled):
        _behind_a_generic_handler()


@pytest.mark.parametrize(
    "error",
    [
        StateError("history written by a newer version"),
        AlreadyRunning(),
        DeadlineExceeded("total"),
        AllowanceExhausted("probes"),
        SourceError(SourceErrorKind.TRANSPORT),
    ],
    ids=lambda error: type(error).__name__,
)
def test_every_shared_error_is_a_frame_gallery_error(error: Exception) -> None:
    assert isinstance(error, FrameGalleryError)
    with pytest.raises(FrameGalleryError):
        raise error


def test_the_classes_are_distinct() -> None:
    classes = [
        Cancelled,
        StateError,
        AlreadyRunning,
        DeadlineExceeded,
        AllowanceExhausted,
        SourceError,
    ]
    for cls in classes:
        others = tuple(other for other in classes if other is not cls)
        assert not issubclass(cls, others)


def test_messages_are_kept() -> None:
    assert str(StateError("read-only /data")) == "read-only /data"
    assert str(Cancelled()) == ""
