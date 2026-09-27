"""The seam between the gateway and the network (§10, §20.2).

The gateway validates every URL, address, status, header, and byte; the
transport behind this seam only resolves names, connects to the address it is
given, and moves bytes. The real transport lives in
:mod:`frame_gallery.net.transport`; tests use fakes.
"""

from __future__ import annotations

import enum
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from ipaddress import IPv4Address, IPv6Address
from types import MappingProxyType
from typing import Protocol

from frame_gallery.errors import FrameGalleryError

type IPAddress = IPv4Address | IPv6Address


class FailureStage(enum.StrEnum):
    """Where a transport failure happened; decides whether a retry is allowed."""

    RESOLVE = "resolve"
    """Name resolution."""

    CONNECT = "connect"
    """TCP connect, TLS handshake, or the peer check: nothing was sent yet."""

    EXCHANGE = "exchange"
    """Sending the request or receiving the response."""


class TransportFailure(FrameGalleryError):
    """A resolver or transport failure. ``detail`` is log-safe (no URL query,
    header value, or body)."""

    def __init__(self, stage: FailureStage, detail: str, *, timed_out: bool = False) -> None:
        super().__init__(f"{stage.value}: {detail}")
        self.stage = stage
        self.detail = detail
        self.timed_out = timed_out


@dataclass(frozen=True, slots=True)
class WireRequest:
    """One GET to one already validated address."""

    address: IPAddress
    host: str
    """The validated host name: for SNI, the certificate check, and ``Host``."""

    port: int
    tls: bool
    target: str
    """The request target: path and query, starting with ``/``."""

    headers: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "headers", MappingProxyType(dict(self.headers)))


class WireResponse(Protocol):
    """A response whose status line and headers have arrived."""

    @property
    def status(self) -> int: ...

    def header(self, name: str) -> str | None:
        """The value of a header (case-insensitive); repeated headers are
        joined with ``", "``. ``None`` if absent."""
        ...

    def read(self, amount: int, timeout: float) -> bytes:
        """Up to ``amount`` body bytes after at most one socket read (plus
        chunk framing), waiting at most ``timeout`` seconds for each socket
        read; ``b""`` at the end of the body. Raises :class:`TransportFailure`."""
        ...

    def close(self) -> None:
        """Close the connection (idempotent, never raises)."""
        ...


class Transport(Protocol):
    def open(
        self, request: WireRequest, *, connect_timeout: float, exchange_timeout: float
    ) -> WireResponse:
        """Connect to ``request.address``, check the peer, send the request,
        and return once the status line and headers have arrived.

        ``connect_timeout`` bounds the connection and TLS handshake;
        ``exchange_timeout`` bounds everything from the connect until the
        response is closed. Raises :class:`TransportFailure`.
        """
        ...


class Resolver(Protocol):
    def resolve(self, host: str, port: int, timeout: float) -> Sequence[IPAddress]:
        """The addresses of ``host``, without duplicates, in resolver order.

        Raises :class:`TransportFailure` (stage ``RESOLVE``) on failure or when
        ``timeout`` expires; never returns an empty sequence.
        """
        ...
