"""Opted-in coherent reads on ONE established Art socket; no connection factory.

At most one four-getter cycle/minute, five seconds and 64 frames per cycle.
No library getter/open, image download, setter, power, ping or reconnect here.
"""

from __future__ import annotations

import json
import secrets
import time
from collections.abc import Callable, Generator
from typing import Any

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


class StateInterrupted(Exception):
    def __init__(self, change: Change | None) -> None:
        self.change = change


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
        hints = {
            "off": Change("mode", "off"),
            "nav": Change("invalidate"),
            "on": Change("mode", "on"),
        }
        status = body.get("status")
        if isinstance(status, str) and status in hints:
            return hints[status]  # on is a read trigger, never image evidence
    try:
        return decode_event(raw, policy)
    except ValueError:
        return None  # no caption from unknown/correlated/extra-field events


def read_current_state(
    connection: Any,
    bounds: FrameBounds,
    policy: EventPolicy,
    timeout_type: type[BaseException],
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
            if not isinstance(raw, str) or not raw:
                raise ValueError("state refresh transport ended")
            frames += 1
            if frames > MAX_EVENTS:
                raise ValueError("state refresh frame budget")
            outer = _unique_object(raw.encode("utf-8"))
            if not isinstance(outer, dict) or outer.get("event") != "d2d_service_message":
                raise StateInterrupted(notification(raw, policy))
            body = event_body(raw)
            correlations = [body[k] for k in ("id", "request_id") if k in body]
            if correlations:
                if body.get("event") != name or any(v != nonce for v in correlations):
                    raise StateInterrupted(None)
                return body
            change = notification(raw, policy)
            if change != Change("mode", "on"):
                raise StateInterrupted(change)

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
) -> Generator[JsonObject, None, None]:
    """Menu/same-ID recovery and quiet-image checks; never replaces the socket."""
    next_read, art = now() + REFRESH_S, True
    while True:
        bounds.check()
        try:
            raw = connection.recv()
        except timeout_type:
            # Drain queued standby/nav/off before considering any outgoing GET.
            if not art or now() < next_read:
                continue
            next_read = now() + REFRESH_S
            yield {"kind": "state_checking"}
            try:
                content_id = read_current_state(connection, bounds, policy, timeout_type)
            except RefreshExpired:
                continue  # same socket, next cycle no sooner than 60 seconds
            except StateInterrupted as exc:
                change = exc.change
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
        if change.kind == "invalidate":
            art = False  # never query while known navigation is active
        elif change == Change("mode", "on"):
            art = True  # trigger only; the new read still verifies mode/ID twice
        yield {"kind": "change", "change": change.to_json()}
        if change.kind == "standby" or change == Change("mode", "off"):
            return
