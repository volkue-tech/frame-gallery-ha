"""Atomic preview publication (§13.5, §16.3, D8).

After ``selected``, the parent copies the validated delivery bytes into
``/media/frame_gallery/preview``:

- every directory below ``/media`` is opened without following a symbolic
  link (a link is refused), and missing ones are created with mode 0755;
- the bytes are read again from ``delivery.jpg`` without following a link,
  bounded by the 15 MiB output cap, and must have the size and SHA-256 that
  the parent computed in ATTEMPT, so the preview is exactly the television
  payload (D8);
- each preview name is written with the §13.2 primitive at mode 0644, and
  its temporary file is read back and its SHA-256 checked. Only when every
  name is staged and verified, and time is left, are they renamed in turn;
- every name receives the same bytes. Phase 8 chooses one name or two
  alternating names (D-140). With two, only a rename that fails between the
  first and the second can leave them different; the run then reports
  ``delivered_with_warnings``, and the next delivery writes both again.

Any failure raises ``PublishError``: the runner then reports
``delivered_with_warnings``, for example when ``/media`` is unavailable.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from frame_gallery.budget.deadline import Deadline
from frame_gallery.errors import PublishError, StateError
from frame_gallery.imaging.contract import MAX_OUTPUT_BYTES, DeliveryArtifact
from frame_gallery.store.atomic import (
    CommitError,
    Directory,
    ReadFailure,
    Staged,
    check_name,
    open_directory,
    read_path,
)

PREVIEW_PARTS: Final = ("frame_gallery", "preview")
PREVIEW_NAMES: Final = ("latest.jpg",)
PREVIEW_MODE: Final = 0o644

_log = logging.getLogger("frame_gallery.store")


class PreviewStore:
    """The ``PreviewPublisher`` port over ``<media>/frame_gallery/preview``."""

    def __init__(self, media_root: Path, *, names: Sequence[str] = PREVIEW_NAMES) -> None:
        if not names:
            msg = "at least one preview name is needed"
            raise ValueError(msg)
        self._media_root = media_root
        self._names = tuple(check_name(name) for name in names)

    def publish(self, artifact: DeliveryArtifact, deadline: Deadline) -> None:
        """Publish the delivery bytes under every preview name.

        Raises ``PublishError`` or ``DeadlineExceeded``.
        """
        deadline.check()
        data = _delivery_bytes(artifact)
        try:
            directory = open_directory(self._media_root, PREVIEW_PARTS, create=True, mode=0o755)
        except StateError as exc:
            raise PublishError(str(exc)) from None
        with directory:
            pending: list[Staged] = []
            try:
                for name in self._names:
                    deadline.check()
                    pending.append(_stage_verified(directory, name, data, artifact.sha256))
                deadline.check()
                while pending:
                    _commit(directory, pending[0])
                    pending.pop(0)
            finally:
                for staged in pending:
                    directory.discard(staged)


def _delivery_bytes(artifact: DeliveryArtifact) -> bytes:
    data = read_path(artifact.path, MAX_OUTPUT_BYTES)
    if isinstance(data, ReadFailure):
        msg = f"the delivery file is {data.value}"
        raise PublishError(msg)
    if len(data) != artifact.size_bytes or hashlib.sha256(data).hexdigest() != artifact.sha256:
        msg = "the delivery file changed since it was validated"
        raise PublishError(msg)
    return data


def _stage_verified(directory: Directory, name: str, data: bytes, sha256: str) -> Staged:
    try:
        staged = directory.stage(name, data, mode=PREVIEW_MODE)
    except StateError as exc:
        raise PublishError(str(exc)) from None
    written = directory.read_bytes(staged.temporary, MAX_OUTPUT_BYTES)
    if isinstance(written, ReadFailure) or hashlib.sha256(written).hexdigest() != sha256:
        directory.discard(staged)
        msg = f"{directory.label}/{name}: the written preview does not match"
        raise PublishError(msg)
    return staged


def _commit(directory: Directory, staged: Staged) -> None:
    try:
        directory.commit(staged, refresh_backup=False)
    except CommitError as exc:
        if not exc.replaced:
            raise PublishError(str(exc)) from None
        _log.warning("the preview was published, but it may not be durable yet: %s", exc)
