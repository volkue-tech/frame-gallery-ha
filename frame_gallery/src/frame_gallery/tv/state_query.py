"""Opted-in coherent reads on ONE established Art socket; no connection factory.

At most one four-getter cycle/minute, five seconds and 64 frames per cycle.
No library getter/open, image download, setter, power, ping or reconnect here.
"""

from __future__ import annotations

import json
import secrets
import time
from collections.abc import Callable, Generator
from typing import Any, Final

from frame_gallery.isolation.executor import JsonObject
from frame_gallery.observer.stream import (
    MAX_EVENTS,
    MAX_FRAME,
    REFRESH_S,
    Change,
    EventPolicy,
    _unique_object,
    decode_event,
    event_body,
)
from frame_gallery.tv.event_frames import FrameBounds, RefreshExpired
from frame_gallery.tv.port import CONTENT_ID_PATTERN

_RESPONSE_EVENTS: Final = {
    "get_artmode_status": "artmode_status",
    "get_current_artwork": "current_artwork",
}


class StateInterrupted(Exception):
    def __init__(self, change: Change | None) -> None:
        self.change = change


def _reply(raw: object, name: str, nonce: str, policy: EventPolicy) -> JsonObject | None:
    if not isinstance(raw, str) or not raw:
        raise ValueError("state refresh transport ended")
    outer = _unique_object(raw.encode("utf-8"))
    if not isinstance(outer, dict) or outer.get("event") != "d2d_service_message":
        raise StateInterrupted(notification(raw, policy))
    body = event_body(raw)
    correlations = [body[k] for k in ("id", "request_id") if k in body]
    if correlations:
        expected = _RESPONSE_EVENTS.get(name)
        if (
            expected is None
            or body.get("event") != expected
            or any(v != nonce for v in correlations)
        ):
            raise StateInterrupted(None)
        return body
    change = notification(raw, policy)
    if change != Change("mode", "on"):
        raise StateInterrupted(change)
    return None


def notification(raw: str, policy: EventPolicy) -> Change | None:
    """Unknown bounded notifications invalidate, never prove or kill a read.

    Negative mode evidence is honoured even with extra fields. Other unfamiliar
    shapes carry no positive evidence. Malformed envelopes still fail closed.
    """
    encoded = raw.encode("utf-8")
    if len(encoded) > MAX_FRAME:
        raise ValueError("state notification byte bound")
    outer = _unique_object(encoded)
    if not isinstance(outer, dict) or not isinstance(outer.get("event"), str):
        raise ValueError("invalid notification")
    if outer["event"] == "ms.error":
        raise ValueError("TV channel refused")
    if outer["event"] != "d2d_service_message":
        return None
    body = event_body(raw)
    if body.get("event") == "go_to_standby":
        return Change("standby")
    if body.get("event") == "art_mode_changed":
        hints = {"off": Change("mode", "off"), "nav": Change("invalidate")}
        status = body.get("status")
        if isinstance(status, str) and status in hints:
            return hints[status]  # negative mode evidence only
    try:
        return decode_event(raw, policy)
    except ValueError:
        return None  # no caption from unknown/correlated/extra-field events


def read_current_state(
    connection: Any,
    bounds: FrameBounds,
    policy: EventPolicy,
    timeout_type: type[BaseException],
    *,
    initial_snapshot: Callable[[], str] | None = None,
) -> str:
    if not policy.state_refresh or connection is not bounds.connection:
        raise ValueError("unapproved state refresh transport")
    bounds.begin_refresh()  # consumes budget before sending, including failures
    frames = 0

    def request(name: str) -> JsonObject:
        nonlocal frames
        bounds.check()
        nonce = secrets.token_hex(16)
        connection.send(
            json.dumps(
                {
                    "method": "ms.channel.emit",
                    "params": {
                        "event": "art_app_request",
                        "to": "host",
                        "data": json.dumps(
                            {
                                "request": name,
                                "id": nonce,
                                "request_id": nonce,
                            }
                        ),
                    },
                }
            )
        )
        while True:
            bounds.check()
            try:
                raw = connection.recv()
            except timeout_type:
                continue  # never resend or extend the shared deadline
            bounds.check()
            frames += 1
            if frames > MAX_EVENTS:
                raise ValueError("state refresh frame budget")
            body = _reply(raw, name, nonce, policy)
            if body is not None:
                return body

    def mode() -> None:
        value = request("get_artmode_status").get("value")
        if value != "on":
            raise StateInterrupted(
                Change("mode", "off") if value == "off" else Change("invalidate")
            )

    def content() -> str:
        value = request("get_current_artwork").get("content_id")
        if not isinstance(value, str) or CONTENT_ID_PATTERN.fullmatch(value) is None:
            raise ValueError("invalid state refresh ID")
        return value

    try:
        mode()
        if initial_snapshot is not None:
            try:
                initial_id = initial_snapshot()  # original one-thumbnail proof, same deadline
                bounds.check()
            except RefreshExpired:
                raise ValueError("initial snapshot expired; no repeated thumbnail") from None
            return initial_id
        first, second = content(), content()
        mode()
        if first != second:
            raise StateInterrupted(None)
        return first
    finally:
        bounds.finish_refresh()


def current_state_events(
    connection: Any,
    bounds: FrameBounds,
    policy: EventPolicy,
    timeout_type: type[BaseException],
    *,
    now: Callable[[], float] = time.monotonic,
    initial_snapshot: Callable[[], JsonObject] | None = None,
) -> Generator[JsonObject, None, None]:
    """Menu/same-ID recovery and quiet-image checks; never replaces the socket."""
    next_read = now() + REFRESH_S
    snapshot: JsonObject | None = None

    def capture() -> str:
        nonlocal snapshot
        assert initial_snapshot is not None  # noqa: S101
        snapshot = initial_snapshot()
        content_id = snapshot.get("content_id")
        if not isinstance(content_id, str) or CONTENT_ID_PATTERN.fullmatch(content_id) is None:
            raise ValueError("invalid deferred snapshot ID")
        return content_id

    while True:
        bounds.check()
        try:
            raw = connection.recv()
        except timeout_type:
            # Drain queued standby/nav/off before considering any outgoing GET.
            if now() < next_read:
                continue
            yield {"kind": "state_checking"}
            next_read = now() + REFRESH_S  # includes any parent/backpressure delay
            try:
                content_id = read_current_state(
                    connection,
                    bounds,
                    policy,
                    timeout_type,
                    initial_snapshot=capture if initial_snapshot is not None else None,
                )
            except RefreshExpired:
                continue  # same socket, next cycle no sooner than 60 seconds
            except StateInterrupted as exc:
                change = exc.change
            else:
                if snapshot is not None:
                    yield {"kind": "baseline", "observation": snapshot}
                    snapshot, initial_snapshot = None, None
                else:
                    yield {"kind": "current_state", "content_id": content_id}
                continue
        else:
            if not isinstance(raw, str) or not raw:
                raise ValueError("state event transport ended")
            bounds.check()
            change = notification(raw, policy)
        if change is None:
            yield {"kind": "state_checking"}
            continue
        # Navigation clears attribution but cannot permanently suspend mode
        # checks: the corresponding unsolicited on notification may be lost.
        # A cycle reads ONLY mode until that getter freshly returns on.
        yield {"kind": "change", "change": change.to_json()}
        if change.kind == "standby":
            return
