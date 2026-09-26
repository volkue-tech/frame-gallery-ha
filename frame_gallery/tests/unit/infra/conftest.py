"""Fixtures for the infrastructure tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from frame_gallery.logs.redact import active_redactor, set_active_redactor


@pytest.fixture(autouse=True)
def _no_active_redactor() -> Iterator[None]:
    """Each test starts without an active redactor; the previous one is restored."""
    previous = active_redactor()
    set_active_redactor(None)
    try:
        yield
    finally:
        set_active_redactor(previous)
