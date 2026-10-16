"""Isolated TV observation and image-verified binding capture.

No credentials or image bytes are retained in mappings. Enrollment is allowed
only following a fresh successful explicit delivery in the opted-in service.
"""

from __future__ import annotations

import base64
import hashlib
import os
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from ipaddress import IPv4Address
from pathlib import Path
from typing import cast

from frame_gallery.errors import StateError
from frame_gallery.isolation.executor import Executor, WorkerError
from frame_gallery.observer.model import READ_S, Observation, Status
from frame_gallery.store.artwork_bindings import Binding, BindingStore
from frame_gallery.store.atomic import ReadFailure, decode_json, open_directory
from frame_gallery.store.observer_targets import MAX_TARGETS, TargetStore
from frame_gallery.tv.port import CONTENT_ID_PATTERN
from frame_gallery.tv.token_store import TokenStore


class HostObserver:
    def __init__(
        self,
        executor: Executor,
        data: Path,
        media: Path,
        host: IPv4Address,
        *,
        device_id: str | None = None,
        tokenless_grant: bool = False,
        stopped: Callable[[], bool] = lambda: False,
    ) -> None:
        self._executor, self._data, self._media, self._host = executor, data, media, host
        self._device, self._stopped = device_id, stopped
        # Only a reviewed identity/channel policy can select this mode. It is
        # neither a user option nor a retry after a stored-token rejection.
        self._tokenless = tokenless_grant
        self._bindings = BindingStore(data)
        self._targets = TargetStore(data)
        self._enroll = False

    def delivery_snapshot(self) -> bytes | None:
        """A bounded before/after receipt; exit 0 alone also includes no_match.

        Distinguish a missing record from an unreadable one. If the initial
        snapshot fails, the explicit delivery still runs but cannot arm reads.
        """
        try:
            with open_directory(self._data, ("state",)) as directory:
                raw = directory.read_bytes("current.json", 16 * 1024)
            if raw is ReadFailure.MISSING:
                return b""
            return raw if isinstance(raw, bytes) else None
        except StateError:
            return None

    def after_delivery(self, before: bytes | None) -> bool:
        """Grant one service session; the caller must have observed send success.

        No network I/O here. Do not recover a damaged pin table into enrollment,
        or infer a tokenless grant during ordinary reads after token rejection.
        """
        self._device, self._enroll, self._tokenless = None, False, False
        try:
            after = self.delivery_snapshot()
            record = self._current()
            content_id = None if record is None else record.get("tv_content_id")
            if (
                before is None
                or not after
                or before == after
                or not isinstance(content_id, str)
                or CONTENT_ID_PATTERN.fullmatch(content_id) is None
            ):
                return False
            targets = self._targets.targets()
            self._device = targets.get(str(self._host))
            if self._device is None and len(targets) >= MAX_TARGETS:
                return False
            self._tokenless = TokenStore(self._data, self._host).load() is None
            self._enroll = self._device is None
        except StateError:
            return False
        return True

    def read(self) -> Observation:
        if self._device is None and not self._enroll:
            return Observation(Status.VALIDATION_REQUIRED)
        token = None if self._tokenless else TokenStore(self._data, self._host).load()
        if token is None and not self._tokenless:
            return Observation(Status.NOT_AUTHORIZED)
        try:
            result = self._executor.run(
                "observe",
                {
                    "host": str(self._host),
                    "token": token,
                    "device_id": self._device,
                    "tokenless_grant": self._tokenless,
                    "enroll_device": self._enroll,
                },
                timeout=READ_S,
                should_stop=self._stopped,
            )
            thumbnail = result.pop("thumbnail", None)
            observation = Observation.from_json(result)
            if self._device is not None and observation.device_id not in (None, self._device):
                raise ValueError("observation belongs to another TV")
            if observation.content_id is not None and not _thumbnail_matches(
                observation, thumbnail
            ):
                raise ValueError("inconsistent observed thumbnail")
            if self._enroll and observation.device_id is not None:
                self._targets.pin(self._host, observation.device_id)
                self._device, self._enroll = observation.device_id, False
            if observation.content_id is not None and self._bindings.resolve(observation) is None:
                self._capture(observation, cast(str, thumbnail))
            return observation
        except (WorkerError, ValueError, StateError, OSError):
            return Observation(Status.UNAVAILABLE)

    def _capture(self, observation: Observation, thumbnail: str) -> None:
        record = self._current()
        if record is None or record.get("tv_content_id") != observation.content_id:
            return
        metadata = record.get("attribution")
        sha256 = record.get("sha256")
        if not isinstance(metadata, dict) or not isinstance(sha256, str):
            return
        with open_directory(self._media, ("frame_gallery", "preview")) as directory:
            fd = os.open(
                "latest.jpg",
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                dir_fd=directory.fd,
            )
        try:
            verified = self._executor.run(
                "verify_thumbnail",
                {"fd": fd, "sha256": sha256, "thumbnail": thumbnail},
                timeout=5.0,
                files=(fd,),
                should_stop=self._stopped,
            )
        finally:
            os.close(fd)
        if verified != {"matched": True}:
            return
        fields: dict[str, object] = {
            "device_id": observation.device_id,
            "content_id": observation.content_id,
            "thumbnail_sha256": observation.thumbnail_sha256,
            "work_id": record.get("id"),
            "title": metadata.get("title") or "",
            "artist": metadata.get("creator") or "",
            "source": str(record.get("id", "")).partition(":")[0],
            "detail_url": metadata.get("detail_url") or "",
            "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        self._bindings.remember(Binding.from_json(fields))

    def _current(self) -> Mapping[str, object] | None:
        try:
            with open_directory(self._data, ("state",)) as directory:
                raw = directory.read_bytes("current.json", 16 * 1024)
            if isinstance(raw, ReadFailure):
                return None
            record = decode_json(raw)
            if (
                not isinstance(record, dict)
                or record.get("format") != "frame-gallery-current"
                or record.get("version") != 1
            ):
                return None
            return record
        except (StateError, ValueError):
            return None


def _thumbnail_matches(observation: Observation, thumbnail: object) -> bool:
    if not isinstance(thumbnail, str) or len(thumbnail) > 56 * 1024:
        return False
    raw = base64.b64decode(thumbnail, validate=True)
    return (
        0 < len(raw) <= 40 * 1024
        and hashlib.sha256(raw).hexdigest() == observation.thumbnail_sha256
    )
