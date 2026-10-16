"""Verified per-TV associations, bounded and atomically stored independently of history."""

from __future__ import annotations

import fcntl
import os
import secrets
import stat
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

from frame_gallery.errors import StateError
from frame_gallery.observer.model import DEVICE_ID, REQUEST_ID, THUMBNAIL_HASH, Command, Observation
from frame_gallery.store.atomic import DocumentFile, DocumentSpec, ReadFailure, open_directory
from frame_gallery.store.fields import parse_qualified_id, parse_timestamp
from frame_gallery.tv.port import CONTENT_ID_PATTERN

MAX_BINDINGS: Final = 4096
MAX_BINDING_BYTES: Final = 8 * 1024 * 1024
FORMAT: Final = "frame-gallery-artwork-bindings"
FILE: Final = "artwork-bindings.json"
OWNER_FILE: Final = "observer-owner.json"
REQUEST_TTL_S: Final = 300.0
MAX_REQUESTS: Final = 128


def _string(value: object, limit: int = 200) -> str:
    if not isinstance(value, str) or len(value) > limit or any(ord(c) < 32 for c in value):
        raise ValueError("invalid binding text")
    return value


@dataclass(frozen=True, slots=True)
class Binding:
    device_id: str
    content_id: str
    thumbnail_sha256: str
    work_id: str
    title: str
    artist: str
    source: str
    detail_url: str
    recorded_at: str

    @classmethod
    def from_json(cls, value: Mapping[str, object]) -> Binding:
        if set(value) != set(cls.__dataclass_fields__):
            raise ValueError("invalid binding fields")
        result = cls(**{name: _string(value[name]) for name in cls.__dataclass_fields__})
        if (
            DEVICE_ID.fullmatch(result.device_id) is None
            or CONTENT_ID_PATTERN.fullmatch(result.content_id) is None
            or THUMBNAIL_HASH.fullmatch(result.thumbnail_sha256) is None
        ):
            raise ValueError("invalid binding identity")
        parse_qualified_id(result.work_id)
        parse_timestamp(result.recorded_at)
        return result

    def matches(self, observation: Observation) -> bool:
        return (
            self.device_id == observation.device_id
            and self.content_id == observation.content_id
            and self.thumbnail_sha256 == observation.thumbnail_sha256
        )


def _bindings(document: Mapping[str, object]) -> tuple[Binding, ...]:
    items = document.get("bindings")
    if not isinstance(items, list) or len(items) > MAX_BINDINGS:
        raise ValueError("invalid binding count")
    result = []
    keys: set[tuple[str, str]] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("invalid binding")
        binding = Binding.from_json(item)
        key = binding.device_id, binding.content_id
        if key in keys:
            raise ValueError("duplicate TV binding")
        keys.add(key)
        result.append(binding)
    return tuple(result)


def _owner(document: Mapping[str, object]) -> str:
    value = document.get("owner")
    if not isinstance(value, str) or len(value) != 64 or DEVICE_ID.fullmatch(value) is None:
        raise ValueError("invalid observer owner")
    return value


SPEC: Final = DocumentSpec(FORMAT, 1, MAX_BINDING_BYTES, _bindings)
OWNER_SPEC: Final = DocumentSpec("frame-gallery-observer-owner", 1, 1024, _owner)


def _requests(document: Mapping[str, object]) -> tuple[tuple[str, float], ...]:
    items = document.get("requests")
    if not isinstance(items, list) or len(items) > MAX_REQUESTS:
        raise ValueError("invalid observer request journal")
    result = []
    for item in items:
        if not isinstance(item, dict) or set(item) != {"id", "at"}:
            raise ValueError("invalid observer request")
        request_id, at = item["id"], item["at"]
        if (
            not isinstance(request_id, str)
            or REQUEST_ID.fullmatch(request_id) is None
            or not isinstance(at, int | float)
            or isinstance(at, bool)
            or not 0 <= at <= 253402300799
        ):
            raise ValueError("invalid observer request value")
        result.append((request_id, float(at)))
    return tuple(result)


REQUEST_SPEC: Final = DocumentSpec("frame-gallery-observer-requests", 1, 32 * 1024, _requests)


class BindingStore:
    """One writer, serialized by the service; never clears the upload protections."""

    def __init__(self, data: Path) -> None:
        self._data = data

    def owner(self) -> str:
        with open_directory(self._data, ("state",), create=True, mode=0o700) as directory:
            document = DocumentFile(directory, OWNER_FILE, OWNER_SPEC)
            loaded = document.load()
            if loaded.newer_version is not None or loaded.unreadable or loaded.value is None:
                # Only a missing file can establish a new identity. Corruption is not absence.
                if directory.read_bytes(OWNER_FILE, 1024) is not ReadFailure.MISSING:
                    raise StateError("observer ownership cannot be established")
                owner = secrets.token_hex(32)
                document.write({"format": OWNER_SPEC.format, "version": 1, "owner": owner})
                return owner
            return loaded.value

    def claim(self, command: Command, now: float) -> bool:
        """Durably consume a fresh command before any delivery. Never evict a live ID."""
        if not -30 <= now - command.issued_at <= REQUEST_TTL_S:
            return False
        with open_directory(self._data, ("state",), create=True, mode=0o700) as directory:
            document = DocumentFile(directory, "observer-requests.json", REQUEST_SPEC, backup=True)
            loaded = document.load()
            if loaded.newer_version is not None or loaded.unreadable:
                raise StateError("observer request journal unavailable")
            if loaded.value is not None and not loaded.primary_valid:
                # A backup can predate the last consumed command. Never replay it.
                raise StateError("observer request journal needs recovery; dispatch disabled")
            if (
                loaded.value is None
                and directory.read_bytes("observer-requests.json", 32768) is not ReadFailure.MISSING
            ):
                raise StateError("observer request journal damaged")
            live = tuple((key, at) for key, at in (loaded.value or ()) if now - at <= REQUEST_TTL_S)
            if any(key == command.request_id for key, _ in live) or len(live) >= MAX_REQUESTS:
                return False
            document.write(
                {
                    "format": REQUEST_SPEC.format,
                    "version": 1,
                    "requests": [
                        {"id": key, "at": at}
                        for key, at in (*live, (command.request_id, command.issued_at))
                    ],
                }
            )
            return True

    def all(self) -> tuple[Binding, ...]:
        with open_directory(self._data, ("state",), create=True, mode=0o700) as directory:
            loaded = DocumentFile(directory, FILE, SPEC, backup=True).load()
            if loaded.newer_version is not None or loaded.unreadable:
                raise StateError("TV associations cannot be read safely")
            return loaded.value or ()

    def resolve(self, observation: Observation) -> Binding | None:
        if observation.content_id is None:
            return None
        return next((binding for binding in self.all() if binding.matches(observation)), None)

    def remember(self, binding: Binding) -> None:
        Binding.from_json(asdict(binding))
        with open_directory(self._data, ("state",), create=True, mode=0o700) as directory:
            document = DocumentFile(directory, FILE, SPEC, backup=True)
            loaded = document.load()
            if loaded.newer_version is not None or loaded.unreadable:
                raise StateError("TV associations cannot be replaced safely")
            prior = tuple(
                item
                for item in (loaded.value or ())
                if (item.device_id, item.content_id) != (binding.device_id, binding.content_id)
            )
            bounded = (*prior[-(MAX_BINDINGS - 1) :], binding)
            document.write(
                {
                    "format": FORMAT,
                    "version": 1,
                    "bindings": [asdict(item) for item in bounded],
                }
            )


class ObserverLock:
    """Independent service lock; the one-shot runner retains its existing state lock."""

    def __init__(self, data: Path) -> None:
        self._data, self._fd = data, -1

    def acquire(self) -> None:
        if self._fd >= 0:
            raise StateError("observer lock is already held")
        with open_directory(self._data, ("state",), create=True, mode=0o700) as directory:
            fd = os.open(
                "observer.lock",
                os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
                0o600,
                dir_fd=directory.fd,
            )
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise OSError("observer lock is not a regular file")
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            raise StateError("another Frame Gallery observer is already running") from None
        self._fd = fd

    def close(self) -> None:
        if self._fd >= 0:
            os.close(self._fd)
            self._fd = -1
