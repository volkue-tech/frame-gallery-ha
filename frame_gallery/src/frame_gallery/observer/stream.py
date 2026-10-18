"""Event contracts, not a claim about any television's unsolicited events.

Production has no approved hardware profile. Synthetic schemas used by offline
tests cannot be selected through options/stdin or inferred from HA availability.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from frame_gallery.isolation.executor import JsonObject
from frame_gallery.observer.model import DEVICE_ID
from frame_gallery.store.atomic import decode_json
from frame_gallery.tv.port import CONTENT_ID_PATTERN

SESSION_S: Final = 8 * 60 * 60.0
START_S: Final = 5.0
STOP_S: Final = 2.0
MAX_EVENTS: Final = 64
MAX_FRAME: Final = 64 * 1024
IDLE_S: Final = 0.25
QUERY_S: Final = 5.0
_NAME: Final = re.compile(r"[A-Za-z_][A-Za-z0-9_.]{0,63}")


@dataclass(frozen=True, slots=True)
class EventPolicy:
    """A software-reviewed schema for an exact previously pinned device.

    Not user configuration. These names must be learned/verified under a
    separate device-test approval, never guessed from synthetic test fixtures.
    """

    mode_event: str
    content_event: str
    invalidation_event: str
    mode_field: str = "value"
    current_id_once: bool = False
    slideshow: bool = False

    def __post_init__(self) -> None:
        names = (self.mode_event, self.content_event, self.invalidation_event)
        if len(set(names)) != 3 or any(_NAME.fullmatch(name) is None for name in names):
            raise ValueError("invalid event schema")
        if self.mode_field not in {"value", "status"} or not isinstance(self.current_id_once, bool):
            raise ValueError("invalid event schema probe")
        if not isinstance(self.slideshow, bool) or (
            self.slideshow
            and (
                names != ("art_mode_changed", "image_selected", "auto_rotation_image_changed")
                or self.mode_field != "status"
                or self.current_id_once
            )
        ):
            raise ValueError("invalid slideshow event schema")

    def to_json(self) -> JsonObject:
        result: JsonObject = {
            "mode": self.mode_event,
            "content": self.content_event,
            "invalidate": self.invalidation_event,
        }
        if self.mode_field != "value" or self.current_id_once:
            result.update(mode_field=self.mode_field, current_id_once=self.current_id_once)
        if self.slideshow:
            result["slideshow"] = True
        return result

    @classmethod
    def from_json(cls, value: JsonObject) -> EventPolicy:
        fields = {"mode", "content", "invalidate"}
        extended = fields | {"mode_field", "current_id_once"}
        if set(value) not in (fields, extended, extended | {"slideshow"}):
            raise ValueError("invalid event schema fields")
        mode, content, invalidate = value["mode"], value["content"], value["invalidate"]
        if (
            not isinstance(mode, str)
            or not isinstance(content, str)
            or not isinstance(invalidate, str)
        ):
            raise ValueError("invalid event schema types")
        mode_field, once = value.get("mode_field", "value"), value.get("current_id_once", False)
        if not isinstance(mode_field, str) or not isinstance(once, bool):
            raise ValueError("invalid event schema probe")
        slideshow = value.get("slideshow", False)
        if not isinstance(slideshow, bool):
            raise ValueError("invalid slideshow event schema")
        return cls(mode, content, invalidate, mode_field, once, slideshow)


SLIDESHOW_POLICY: Final = EventPolicy(
    "art_mode_changed", "image_selected", "auto_rotation_image_changed", "status", slideshow=True
)
"""Observed lab4 contract, available for injected offline tests, NOT live approval."""


REVIEWED_POLICIES: Final[Mapping[str, EventPolicy]] = MappingProxyType({})
"""Intentionally empty until event coverage and sleep safety are validated."""


def reviewed_policy(device_id: str | None) -> EventPolicy | None:
    return REVIEWED_POLICIES.get(device_id) if device_id is not None else None


@dataclass(frozen=True, slots=True)
class Change:
    kind: str
    value: str = ""

    def to_json(self) -> JsonObject:
        return {"kind": self.kind, "value": self.value}

    @classmethod
    def from_json(cls, value: JsonObject) -> Change:
        if set(value) != {"kind", "value"}:
            raise ValueError("invalid event fields")
        kind, item = value["kind"], value["value"]
        if not isinstance(item, str) or not (
            (kind == "mode" and item in {"on", "off"})
            or (
                kind in {"content", "selected", "rotation"}
                and CONTENT_ID_PATTERN.fullmatch(item) is not None
            )
            or (kind in {"invalidate", "standby"} and item == "")
        ):
            raise ValueError("invalid event values")
        return cls(str(kind), item)


def event_body(raw: str) -> JsonObject:
    """Bounded duplicate-key-free envelopes shared with the one pending reply."""
    if len(raw) > MAX_FRAME:
        raise ValueError("event message cap")
    encoded = raw.encode("utf-8")
    if len(encoded) > MAX_FRAME:
        raise ValueError("event message byte cap")
    frame = _unique_object(encoded)
    if not isinstance(frame, dict) or frame.get("event") != "d2d_service_message":
        raise ValueError("unexpected event envelope")
    data = frame.get("data")
    if not isinstance(data, str):
        raise ValueError("missing event body")
    body = _unique_object(data.encode("utf-8"))
    if not isinstance(body, dict):
        raise ValueError("invalid event body")
    return body


def _unique_object(data: bytes) -> object:
    decode_json(data)  # preserve the existing finite-number/depth guard

    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate event JSON key")
            result[key] = value
        return result

    return json.loads(data, object_pairs_hook=unique)


def decode_event(raw: str, policy: EventPolicy) -> Change:
    """Unknown frames fail closed; no heuristic name/field matching or reply replay."""
    body = event_body(raw)
    # There is no pending request in the listening phase. Correlated replies
    # must not be mistaken for a new unsolicited confirmation.
    if "request_id" in body or "id" in body:
        raise ValueError("unexpected correlated reply")
    if policy.slideshow:
        return _slideshow_change(body)
    event = body.get("event")
    if event == policy.mode_event:
        if set(body) != {"event", policy.mode_field}:
            raise ValueError("unexpected mode event fields")
        return Change.from_json({"kind": "mode", "value": body.get(policy.mode_field)})
    if event == policy.content_event:
        if set(body) != {"event", "content_id"}:
            raise ValueError("unexpected content event fields")
        return Change.from_json({"kind": "content", "value": body.get("content_id")})
    if event == policy.invalidation_event:
        if set(body) != {"event"}:
            raise ValueError("unexpected invalidation event fields")
        return Change("invalidate")
    raise ValueError("unrecognized event")


def _slideshow_change(body: JsonObject) -> Change:
    event = body.get("event")
    if body == {"event": "go_to_standby"}:
        return Change("standby")
    if event == "art_mode_changed" and set(body) == {"event", "status"}:
        if body["status"] == "nav":
            return Change("invalidate")  # navigation is NOT Art Mode on
        return Change.from_json({"kind": "mode", "value": body["status"]})
    if event == "image_selected" and set(body) == {
        "event",
        "content_id",
        "is_shown",
        "matte_id",
        "portrait_matte_id",
    }:
        if body["is_shown"] != "Yes" or any(
            not isinstance(body[key], str)
            or re.fullmatch(r"[a-z0-9_]{1,64}", str(body[key])) is None
            for key in ("matte_id", "portrait_matte_id")
        ):
            raise ValueError("unconfirmed slideshow selection")
        return Change.from_json({"kind": "selected", "value": body["content_id"]})
    if (
        event == "auto_rotation_image_changed"
        and set(body) == {"event", "current_content_id", "type"}
        and body["type"] == "shuffleslideshow"
    ):
        return Change.from_json({"kind": "rotation", "value": body["current_content_id"]})
    raise ValueError("unexpected slideshow event fields or value")


def validate_device(value: object) -> str:
    if not isinstance(value, str) or DEVICE_ID.fullmatch(value) is None:
        raise ValueError("missing pinned event-session device")
    return value
