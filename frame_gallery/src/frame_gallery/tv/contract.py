"""Values shared by the television adapter and its worker task (§12.1, D-162).

The parent builds a :class:`TvRequest`; the worker task sends events and
answers with a :func:`result` object. All of them cross the executor seam as
JSON only. The worker sends two kinds of event:

* a **marker** event, ``{"marker": <name>, "content_id": <id or null>}``;
* a **token** event, ``{"token": <token>}``, before ``connected``, when the
  television issued a new pairing token: at most one per connection attempt.
"""

from __future__ import annotations

import enum
import math
import re
from dataclasses import dataclass
from ipaddress import IPv4Address
from pathlib import Path
from typing import Final

from frame_gallery.isolation.executor import JsonObject
from frame_gallery.tv.port import DeliveryStatus, Marker

TOKEN_PATTERN: Final = re.compile(r"[A-Za-z0-9]{6,64}")
"""A pairing token: 6 to 64 ASCII letters or digits. The lower bound is the
redactor's (§18.1): a shorter token could not be kept out of the logs."""

SHA256_PATTERN: Final = re.compile(r"[0-9a-f]{64}")
MAX_DELIVER_S: Final = 60.0
"""No delivery deadline lies further ahead than this when the worker starts."""


class Pairing(enum.StrEnum):
    REJECTED = "rejected"
    """The television refused the token or the connection."""

    PROMPT = "prompt"
    """The pairing prompt was not accepted in time."""


@dataclass(frozen=True, slots=True)
class TvRequest:
    host: IPv4Address
    token: str | None
    """The stored pairing token, or ``None`` for a first pairing."""

    jpeg_path: Path
    jpeg_sha256: str
    """The parent's hash of the validated ``delivery.jpg`` (§11.3): the worker
    uploads only bytes with exactly this hash."""

    deadline: float
    """The end of the delivery on the ``time.monotonic`` scale, which every
    process on the host shares: the worker's clock starts where the parent's
    kill timer started, not after the worker's own start-up."""

    @classmethod
    def from_json(cls, payload: JsonObject) -> TvRequest:
        """Raises ``ValueError`` for anything unexpected."""
        host, token, jpeg_path, sha256, deadline = (
            payload.get("host"),
            payload.get("token"),
            payload.get("jpeg_path"),
            payload.get("jpeg_sha256"),
            payload.get("deadline"),
        )
        if not (
            set(payload) == {"host", "token", "jpeg_path", "jpeg_sha256", "deadline"}
            and isinstance(host, str)
            and (token is None or (isinstance(token, str) and TOKEN_PATTERN.fullmatch(token)))
            and isinstance(jpeg_path, str)
            and isinstance(sha256, str)
            and SHA256_PATTERN.fullmatch(sha256)
            and isinstance(deadline, int | float)
            and not isinstance(deadline, bool)
            and math.isfinite(deadline)
        ):
            msg = "invalid television request"
            raise ValueError(msg)
        address = IPv4Address(host)
        if not address.is_private:
            msg = "invalid television request"
            raise ValueError(msg)
        return cls(address, token, Path(jpeg_path), sha256, float(deadline))

    def to_json(self) -> JsonObject:
        return {
            "host": str(self.host),
            "token": self.token,
            "jpeg_path": str(self.jpeg_path),
            "jpeg_sha256": self.jpeg_sha256,
            "deadline": self.deadline,
        }


def marker_event(marker: Marker, content_id: str | None = None) -> JsonObject:
    return {"marker": marker.value, "content_id": content_id}


def token_event(token: str) -> JsonObject:
    return {"token": token}


def result(status: DeliveryStatus, detail: str, pairing: Pairing | None = None) -> JsonObject:
    return {
        "status": status.value,
        "detail": detail,
        "pairing": None if pairing is None else pairing.value,
    }
