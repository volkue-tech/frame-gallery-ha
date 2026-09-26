"""Exceptions shared across components (standard library only).

Component-specific errors live next to the component that raises them; the
classes here cross component boundaries and are classified by the runner.
"""

from __future__ import annotations


class FrameGalleryError(Exception):
    """Base class for every error that Frame Gallery raises deliberately."""


class Cancelled(BaseException):
    """A stop request (SIGTERM) interrupted the run (outcome ``cancelled``).

    Like ``KeyboardInterrupt`` it derives from ``BaseException``, so a generic
    ``except Exception`` (in the standard library's logging handlers, or in an
    adapter) can never swallow a stop request.
    """


class StateError(FrameGalleryError):
    """Persistent state cannot be read or written safely (outcome ``state_error``)."""


class AlreadyRunning(FrameGalleryError):
    """Another run holds the state lock (outcome ``already_running``)."""
