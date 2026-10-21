"""Sanitized device replies, not generated from the production parser.

Source: build/event-sequence-live-20261017/slideshow-capture.log, SHA-256
d11d2ad875499a11e32b75f10d1557aba5876596ecb14f9d3141d4a9feb5bfac.
Request/reply lines: 42/43, 44/45, 48/49, 50/51 (2026-10-17 11:05:48 UTC).
Only the request nonces and target client identifier are replaced below.
All reply body keys, event names, mode/ID/matte values and id-only correlation
shapes are retained. Outer routing identifiers are not needed by this parser.
No token, connection key, thumbnail bytes or device address is included.

Each tuple is (outgoing request name, outgoing nonce, incoming reply body).
Keep these literal expectations independent of any request/reply mapping code.
"""

from typing import Any

RECORDED_STATE_REPLIES: tuple[tuple[str, str, dict[str, Any]], ...] = (
    (
        "get_artmode_status",
        "11111111111111111111111111111111",
        {
            "event": "artmode_status",
            "id": "11111111111111111111111111111111",
            "target_client_id": "offline-client",
            "value": "on",
        },
    ),
    (
        "get_current_artwork",
        "22222222222222222222222222222222",
        {
            "content_id": "MY_F0015",
            "event": "current_artwork",
            "id": "22222222222222222222222222222222",
            "matte_id": "none",
            "portrait_matte_id": "shadowbox_polar",
            "target_client_id": "offline-client",
        },
    ),
    (
        "get_current_artwork",
        "33333333333333333333333333333333",
        {
            "content_id": "MY_F0015",
            "event": "current_artwork",
            "id": "33333333333333333333333333333333",
            "matte_id": "none",
            "portrait_matte_id": "shadowbox_polar",
            "target_client_id": "offline-client",
        },
    ),
    (
        "get_artmode_status",
        "44444444444444444444444444444444",
        {
            "event": "artmode_status",
            "id": "44444444444444444444444444444444",
            "target_client_id": "offline-client",
            "value": "on",
        },
    ),
)
