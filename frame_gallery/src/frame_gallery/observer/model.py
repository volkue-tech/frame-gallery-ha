"""Bounded observation contracts. No I/O and no assumption that last sent is current."""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from typing import Final

from frame_gallery.isolation.executor import JsonObject
from frame_gallery.tv.port import CONTENT_ID_PATTERN

DEVICE_ID: Final = re.compile(r"[0-9a-f]{64}")
THUMBNAIL_HASH: Final = re.compile(r"[0-9a-f]{64}")
POLL_S: Final = 30.0
FRESH_S: Final = 90.0
SLIDESHOW_FRESH_S: Final = 15 * 60.0
READ_S: Final = 5.0
MAX_COMMAND_BYTES: Final = 1024
REQUEST_ID: Final = re.compile(r"[A-Za-z0-9_-]{8,64}")


class Status(enum.StrEnum):
    CHECKING = "checking"
    ARTWORK = "artwork"
    UNIDENTIFIED = "unidentified"
    TV_IN_USE = "tv_in_use"
    UNAVAILABLE = "unavailable"
    NOT_AUTHORIZED = "not_authorized"
    VALIDATION_REQUIRED = "validation_required"
    PAUSED = "paused"


class Action(enum.StrEnum):
    NEW_ARTWORK = "new_artwork"
    REFRESH_CURRENT = "refresh_current"


class Evidence(enum.StrEnum):
    THUMBNAIL = "thumbnail"
    SLIDESHOW = "slideshow"


class SessionFailure(enum.StrEnum):
    """Fixed diagnostic codes only: no frame, identity, URL or exception text."""

    STARTUP = "startup_failed"
    RECEIVE = "receive_failed"
    DECODE = "event_rejected"
    QUERY = "id_query_failed"
    WORKER = "worker_failed"
    QUEUE = "event_queue_limit"
    CONTRACT = "event_contract_rejected"
    END = "session_ended"


@dataclass(frozen=True, slots=True)
class Command:
    action: Action
    request_id: str
    issued_at: float

    @classmethod
    def from_json(cls, value: JsonObject) -> Command:
        action, request_id, issued = (
            value.get("command"),
            value.get("request_id"),
            value.get("issued_at"),
        )
        if (
            set(value) != {"command", "request_id", "issued_at"}
            or not isinstance(action, str)
            or not isinstance(request_id, str)
            or REQUEST_ID.fullmatch(request_id) is None
            or not isinstance(issued, int | float)
            or isinstance(issued, bool)
            or not 0 <= issued <= 253402300799  # bounded Unix timestamp through year 9999
        ):
            raise ValueError("invalid observer command")
        return cls(Action(action), request_id, float(issued))


@dataclass(frozen=True, slots=True)
class Observation:
    status: Status
    device_id: str | None = None
    content_id: str | None = None
    thumbnail_sha256: str | None = None
    evidence: Evidence = Evidence.THUMBNAIL

    def __post_init__(self) -> None:
        if not isinstance(self.evidence, Evidence):
            raise ValueError("invalid observation evidence")
        if self.status not in {Status.ARTWORK, Status.UNIDENTIFIED}:
            if any((self.device_id, self.content_id, self.thumbnail_sha256)) or (
                self.evidence is not Evidence.THUMBNAIL
            ):
                raise ValueError("non-artwork observation contains artwork identity")
            return
        if (
            self.device_id is None
            or DEVICE_ID.fullmatch(self.device_id) is None
            or self.content_id is None
            or CONTENT_ID_PATTERN.fullmatch(self.content_id) is None
            or (
                self.thumbnail_sha256 is None
                and not (self.evidence is Evidence.SLIDESHOW and self.status is Status.UNIDENTIFIED)
            )
            or (
                self.thumbnail_sha256 is not None
                and THUMBNAIL_HASH.fullmatch(self.thumbnail_sha256) is None
            )
        ):
            raise ValueError("invalid observed artwork identity")

    @classmethod
    def from_json(cls, value: JsonObject) -> Observation:
        fields_set = {"status", "device_id", "content_id", "thumbnail_sha256"}
        if set(value) not in (fields_set, fields_set | {"evidence"}):
            raise ValueError("invalid observation fields")
        evidence = value.get("evidence", Evidence.THUMBNAIL.value)
        if not isinstance(evidence, str):
            raise ValueError("invalid observation evidence")
        status = value["status"]
        fields = [value[name] for name in ("device_id", "content_id", "thumbnail_sha256")]
        if not isinstance(status, str) or any(
            field is not None and not isinstance(field, str) for field in fields
        ):
            raise ValueError("invalid observation types")
        device_id, content_id, thumbnail = fields
        assert device_id is None or isinstance(device_id, str)  # noqa: S101
        assert content_id is None or isinstance(content_id, str)  # noqa: S101
        assert thumbnail is None or isinstance(thumbnail, str)  # noqa: S101
        return cls(Status(status), device_id, content_id, thumbnail, Evidence(evidence))

    def to_json(self) -> JsonObject:
        value: JsonObject = {
            "status": self.status.value,
            "device_id": self.device_id,
            "content_id": self.content_id,
            "thumbnail_sha256": self.thumbnail_sha256,
        }
        if self.evidence is not Evidence.THUMBNAIL:
            value["evidence"] = self.evidence.value
        return value
