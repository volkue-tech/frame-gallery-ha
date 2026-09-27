"""Test-wide guards.

H2 (acceptance item; ARCHITECTURE.md §20.1): outbound networking is disabled
for the whole pytest session, collection included. ``pytest_configure``
installs the guard of ``tests/support/h2.py`` and ``pytest_unconfigure``
restores the originals. The test tasks run in worker processes install the
same guard there; ``tests/support/h2.py`` says which processes are guarded.
The source may not import ``_socket`` at all
(tests/unit/test_architecture_boundaries.py).

Every test also restores Pillow's process-global ``Image.MAX_IMAGE_PIXELS``,
which ``prepare_image`` sets (worker_tasks.py), to the value it started with.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Final

import pytest
from PIL import Image

from frame_gallery.logs.redact import active_redactor, set_active_redactor
from tests.support import h2
from tests.support.h2 import H2_MESSAGE, NetworkBlockedError

__all__ = ["H2_MESSAGE", "NetworkBlockedError"]

_GUARD: Final = pytest.StashKey[pytest.MonkeyPatch]()


def pytest_configure(config: pytest.Config) -> None:
    """Install the H2 guard before collection starts."""
    guard = pytest.MonkeyPatch()
    h2.install(guard.setattr)
    config.stash[_GUARD] = guard


def pytest_unconfigure(config: pytest.Config) -> None:
    """Restore every replaced entry point (inherited methods are deleted again)."""
    guard = config.stash.get(_GUARD, None)
    if guard is not None:
        del config.stash[_GUARD]
        guard.undo()


@pytest.fixture(autouse=True)
def _restore_pillow_global_pixel_limit() -> Iterator[None]:
    """``prepare_image`` sets Pillow's global pixel limit; restore it after each test."""
    saved = Image.MAX_IMAGE_PIXELS
    yield
    Image.MAX_IMAGE_PIXELS = saved


@pytest.fixture(autouse=True)
def _restore_active_redactor() -> Iterator[None]:
    """A test that configures logging cannot leave its redactor active for the
    tests that follow (the redactor is process-wide, §19)."""
    previous = active_redactor()
    try:
        yield
    finally:
        set_active_redactor(previous)
