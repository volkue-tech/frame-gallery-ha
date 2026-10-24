"""Art-only renewal on the existing verified socket. Never open, retry or set.

The initial byte/device proof and independent HA stop monitor belong to the
caller. A lost proof/mode, clock gap, query failure or unknown frame ends this
session; unlike the historical reader this never waits/queries in menu/TV mode.
"""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Generator
from typing import Any

from frame_gallery.isolation.executor import JsonObject
from frame_gallery.observer.model import FRESH_S
from frame_gallery.observer.stream import IDLE_S, QUERY_S, REFRESH_S, Change, EventPolicy
from frame_gallery.tv.event_frames import FrameBounds, RefreshExpired
from frame_gallery.tv.state_query import StateInterrupted, notification, read_current_state


def _confirm(
    connection: Any,
    bounds: FrameBounds,
    policy: EventPolicy,
    timeout_type: type[BaseException],
    now: Callable[[], float],
) -> tuple[JsonObject, float]:
    at = now()
    try:
        content_id = read_current_state(connection, bounds, policy, timeout_type)
    except RefreshExpired:
        raise ValueError("Art confirmation timeout; no retry") from None
    except StateInterrupted as exc:
        if exc.change is not None and exc.change in (
            Change("mode", "off"),
            Change("invalidate"),
            Change("standby"),
        ):
            return {"kind": "change", "change": exc.change.to_json()}, at
        raise ValueError("Art confirmation interrupted; no retry") from None
    finished = now()
    if not math.isfinite(finished) or not 0 <= finished - at < QUERY_S:
        raise ValueError("Art confirmation reply clock or deadline")
    return {"kind": "current_state", "content_id": content_id}, finished


def confirmed_art_events(
    connection: Any,
    bounds: FrameBounds,
    policy: EventPolicy,
    timeout_type: type[BaseException],
    *,
    confirmed_at: float,
    now: Callable[[], float] = time.monotonic,
) -> Generator[JsonObject, None, None]:
    """One coherent cycle/60s, only while the same baseline remains fresh.

    Ordinary reads retain still-valid visible proof; mutation/failure clears
    through the existing parent. Only a complete reply publishes a new receipt.
    """
    if (
        not policy.art_only_refresh
        or not policy.state_refresh
        or connection is not bounds.connection
    ):
        raise ValueError("unapproved Art-only confirmation")
    confirmed = last_clock = confirmed_at
    next_read = confirmed + REFRESH_S
    art_mode = True  # caller already completed initial mode/ID/thumbnail proof
    idle_timeouts = 0
    while True:
        at = now()
        if not math.isfinite(at) or at < last_clock or not 0 <= at - confirmed < FRESH_S:
            raise ValueError("Art confirmation clock or proof gap")
        last_clock = at
        bounds.check()
        try:
            raw = connection.recv()
        except timeout_type:
            idle_timeouts += 1
            if idle_timeouts > FRESH_S / IDLE_S:
                raise ValueError("Art confirmation clock did not progress") from None
            # Queued standby/nav/off is drained before the first outgoing GET.
            if now() < next_read:
                continue
            at = now()
            if not art_mode or not math.isfinite(at) or not 0 <= at - confirmed < FRESH_S:
                raise ValueError("Art mode or fresh proof lost before confirmation") from None
            next_read = at + REFRESH_S  # actual attempt time, not parent receipt time
            event, confirmed = _confirm(connection, bounds, policy, timeout_type, now)
            idle_timeouts = 0
            last_clock = confirmed
            yield event
            if event["kind"] != "current_state":
                return
            continue
        if not isinstance(raw, str) or not raw:
            raise ValueError("Art confirmation transport ended")
        bounds.check()
        change = notification(raw, policy)
        if change is None:
            raise ValueError("unrecognized Art notification; no retry")
        yield {"kind": "change", "change": change.to_json()}
        if change.kind in {"standby", "invalidate"} or change == Change("mode", "off"):
            return
        art_mode = change == Change("mode", "on")  # hint only, never image proof
