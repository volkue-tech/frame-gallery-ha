"""One bounded, correlated ID-only request on an existing verified transport.

No library getter/open/client, network factory, timer/retry or image proof here.
The caller must have consumed an exact mode-on event under its reviewed policy.
"""

from __future__ import annotations

import json
import re
from typing import Any, Final

from frame_gallery.observer.stream import MAX_EVENTS, Change, EventPolicy, decode_event, event_body
from frame_gallery.tv.event_frames import FrameBounds, SessionClosed
from frame_gallery.tv.port import CONTENT_ID_PATTERN

NONCE: Final = re.compile(r"[0-9a-f]{32}")


def current_id_once(
    connection: Any,
    bounds: FrameBounds,
    policy: EventPolicy,
    request_id: str,
    timeout_type: type[BaseException],
) -> str:
    if not policy.current_id_once or NONCE.fullmatch(request_id) is None:
        raise ValueError("unapproved event query")
    if connection is not bounds.connection:
        raise ValueError("event query transport changed")
    bounds.begin_query()  # latches once before send, including failed sends
    request = {"request": "get_current_artwork", "id": request_id, "request_id": request_id}
    connection.send(
        json.dumps(
            {
                "method": "ms.channel.emit",
                "params": {"event": "art_app_request", "to": "host", "data": json.dumps(request)},
            }
        )
    )
    frames = 0
    while True:
        bounds.check()
        try:
            raw = connection.recv()
        except timeout_type:
            continue  # no resend/deadline extension; the original bound still applies
        bounds.check()  # late replies cannot escape the deadline on a fake/slow transport
        if not isinstance(raw, str) or not raw:
            raise ValueError("event query connection ended")
        frames += 1
        if frames > MAX_EVENTS:
            raise ValueError("event query frame limit")
        body = event_body(raw)
        correlation = {key for key in ("request_id", "id") if key in body}
        if correlation:
            if (
                set(body) != {"event", "content_id"} | correlation
                or body.get("event") != "get_current_artwork"
                or any(body[key] != request_id for key in correlation)
            ):
                raise ValueError("unexpected event query reply")
            value = body["content_id"]
            if not isinstance(value, str) or CONTENT_ID_PATTERN.fullmatch(value) is None:
                raise ValueError("invalid event query content ID")
            return value
        if decode_event(raw, policy) != Change("mode", "on"):
            raise SessionClosed  # off/invalidation/content mutation aborts, never queries again
