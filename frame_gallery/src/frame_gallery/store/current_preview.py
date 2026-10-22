"""Separate current-image file; never rewrites the existing last-sent preview."""

from __future__ import annotations

import base64
import hashlib
import logging
from pathlib import Path
from typing import Final

from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.errors import StateError
from frame_gallery.imaging.preview_codec import MAX_PREVIEW_BYTES
from frame_gallery.store.artwork_bindings import Binding
from frame_gallery.store.atomic import open_directory
from frame_gallery.store.delivery_associations import DeliveryAssociation
from frame_gallery.store.preview import PREVIEW_PARTS
from frame_gallery.store.preview_cache import PreviewCache

CURRENT_PREVIEW_NAME: Final = "current.jpg"
# Independently generated solid RGB image, not artwork or a TV capture.
NEUTRAL_JPEG: Final = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAoHBwgHBgoICAgLCgoLDhgQDg0NDh0VFhEYIx8lJCIfIiEmKzcv"
    "Jik0KSEiMEExNDk7Pj4+JS5ESUM8SDc9Pjv/2wBDAQoLCw4NDhwQEBw7KCIoOzs7Ozs7Ozs7Ozs7Ozs7"
    "Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozv/wAARCAAJABADASIA"
    "AhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAf/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFAEBAAAAAAAAAAAA"
    "AAAAAAAAAP/EABQRAQAAAAAAAAAAAAAAAAAAAAD/2gAMAwEAAhEDEQA/AJkAD//Z"
)
_log = logging.getLogger("frame_gallery.store")


class CurrentPreview:
    def __init__(self, data: Path, media: Path) -> None:
        self._cache, self._media = PreviewCache(data), media

    def publish(
        self, binding: Binding | DeliveryAssociation | None, deadline: Deadline
    ) -> str | None:
        """Called only AFTER acknowledged preview_available=false publication.

        Missing, stale or rejected associations cannot borrow the last-sent image.
        Disk/cache failure is optional: metadata remains independently usable.
        """
        try:
            image = (
                self._cache.lookup(binding, deadline)
                if isinstance(binding, DeliveryAssociation)
                else None
            )
            data = NEUTRAL_JPEG if image is None else image
            deadline.check()
            with open_directory(self._media, PREVIEW_PARTS, create=True, mode=0o755) as directory:
                if directory.read_bytes(CURRENT_PREVIEW_NAME, MAX_PREVIEW_BYTES) != data:
                    staged = directory.stage(CURRENT_PREVIEW_NAME, data, mode=0o644)
                    try:
                        if directory.read_bytes(staged.temporary, MAX_PREVIEW_BYTES) != data:
                            raise StateError("current preview staging mismatch")
                        deadline.check()
                        directory.commit(staged, refresh_backup=False)
                    finally:
                        directory.discard(staged)
            return None if image is None else hashlib.sha256(image).hexdigest()
        except (StateError, DeadlineExceeded, OSError, ValueError):
            _log.warning("optional current preview unavailable; metadata is retained")
            return None
