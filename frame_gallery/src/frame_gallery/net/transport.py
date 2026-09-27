"""The real resolver and transport (§10, D-108, D-131).

This is the only module that imports ``socket``, ``ssl``, ``http.client``,
``urllib3``, and ``certifi`` (the architecture boundary test enforces it). It
performs no policy decisions: the gateway validates every URL and address
before calling it. What it does guarantee:

- **One address.** It connects to exactly the address it is given (urllib3
  resolves an IP literal without DNS), then checks ``getpeername()`` against
  it before anything is sent.
- **TLS.** A fresh context per connection: ``CERT_REQUIRED``, host-name
  checking against the validated host name (also the SNI), TLS 1.2 or newer,
  and only the CA bundle of the pinned ``certifi``. The system and
  environment certificate stores are never loaded. The negotiated socket is
  checked again before the request is sent.
- **No hidden behaviour.** urllib3 is used at the connection level: no pool,
  no retries, no redirects, no proxies, no cookies, and no content decoding.
- **Bounded time.** The connect has its own timeout. Once connected, the
  connection's own timeout becomes the exchange time, because urllib3 resets
  the socket timeout to it before sending and before reading the headers. A
  timer shuts the socket down when the exchange time runs out, which also
  bounds a peer that sends headers or body one byte at a time; each body read
  re-clamps the socket timeout and performs at most one socket read. The
  socket is captured right after the connect: a response with
  ``Connection: close`` makes http.client drop the connection's reference to
  it while the body is still being read from it.
- **Bounded resolution.** Name resolution runs in a daemon thread that the
  caller stops waiting for after its timeout.
"""

from __future__ import annotations

import http.client
import socket
import ssl
import threading
from collections.abc import Callable, Sequence
from contextlib import suppress
from ipaddress import ip_address
from typing import Final

import certifi
import urllib3
from urllib3.connection import HTTPConnection, HTTPSConnection

from frame_gallery.net.wire import (
    FailureStage,
    IPAddress,
    TransportFailure,
    WireRequest,
    WireResponse,
)

TLS_VERSIONS: Final = frozenset({"TLSv1.2", "TLSv1.3"})

type SocketAddress = tuple[str, int] | tuple[str, int, int, int] | tuple[int, bytes]
type AddressInfo = tuple[socket.AddressFamily, socket.SocketKind, int, str, SocketAddress]
type GetAddrInfo = Callable[[str, int, int, int, int], Sequence[AddressInfo]]
type ConnectionFactory = Callable[[WireRequest, float, str], HTTPConnection]


def make_tls_context(cafile: str) -> ssl.SSLContext:
    """A client context that trusts only ``cafile`` (§10)."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    context.load_verify_locations(cafile=cafile)
    return context


def default_connection(request: WireRequest, connect_timeout: float, cafile: str) -> HTTPConnection:
    """A urllib3 connection to ``request.address`` that has not connected yet."""
    host = str(request.address)
    if request.tls:
        return HTTPSConnection(
            host,
            request.port,
            timeout=connect_timeout,
            server_hostname=request.host,
            ssl_context=make_tls_context(cafile),
        )
    return HTTPConnection(host, request.port, timeout=connect_timeout)


class SystemResolver:
    """``getaddrinfo`` with a timeout (a daemon thread per lookup)."""

    def __init__(self, getaddrinfo: GetAddrInfo | None = None) -> None:
        self._getaddrinfo = getaddrinfo

    def resolve(self, host: str, port: int, timeout: float) -> Sequence[IPAddress]:
        lookup = self._getaddrinfo or socket.getaddrinfo
        answers: list[AddressInfo] = []
        failed: list[BaseException] = []
        done = threading.Event()

        def work() -> None:
            try:
                answers.extend(lookup(host, port, 0, socket.SOCK_STREAM, socket.IPPROTO_TCP))
            except Exception as exc:  # noqa: BLE001 - reported below as a resolver failure
                failed.append(exc)
            finally:
                done.set()

        threading.Thread(target=work, name="frame-gallery-resolver", daemon=True).start()
        if not done.wait(timeout):
            raise TransportFailure(FailureStage.RESOLVE, "timed out", timed_out=True)
        if failed:
            raise TransportFailure(FailureStage.RESOLVE, type(failed[0]).__name__)
        addresses: dict[IPAddress, None] = {}
        for family, _kind, _proto, _name, sockaddr in answers:
            if family not in (socket.AF_INET, socket.AF_INET6):
                continue
            try:
                addresses[ip_address(sockaddr[0])] = None
            except ValueError:
                continue
        if not addresses:
            raise TransportFailure(FailureStage.RESOLVE, "no usable address")
        return tuple(addresses)


class _ExchangeGuard:
    """Shuts the socket down when the exchange time runs out.

    Until :meth:`bind` is called it uses whatever socket the connection holds
    (so a slow TLS handshake is cut off too); afterwards it keeps the socket
    it was given, which outlives the connection's own reference to it.
    """

    def __init__(self, connection: HTTPConnection, seconds: float) -> None:
        self.fired = False
        self._connection = connection
        self._sock: socket.socket | None = None
        self._timer = threading.Timer(seconds, self._fire)
        self._timer.daemon = True
        self._timer.start()

    def bind(self, sock: socket.socket) -> None:
        self._sock = sock

    def _fire(self) -> None:
        self.fired = True
        sock = self._sock if self._sock is not None else self._connection.sock
        if sock is not None:
            with suppress(OSError):
                sock.shutdown(socket.SHUT_RDWR)

    def cancel(self) -> None:
        self._timer.cancel()


_FAILURES: Final = (OSError, urllib3.exceptions.HTTPError, http.client.HTTPException, ValueError)
"""What the network stack raises for a failed exchange (``ssl.SSLError`` and
``TimeoutError`` are ``OSError`` subclasses)."""

_TIMEOUTS: Final = (TimeoutError, urllib3.exceptions.TimeoutError)


def _failure(exc: Exception, stage: FailureStage, guard: _ExchangeGuard) -> TransportFailure:
    # urllib3 derives NewConnectionError (a refused or failed connect) from
    # ConnectTimeoutError for compatibility; it is not a timeout.
    timed_out = guard.fired or (
        isinstance(exc, _TIMEOUTS) and not isinstance(exc, urllib3.exceptions.NewConnectionError)
    )
    detail = "exchange time limit reached" if guard.fired else type(exc).__name__
    return TransportFailure(stage, detail, timed_out=timed_out)


class _Response:
    """A :class:`WireResponse` over a urllib3 response and its connection."""

    def __init__(
        self,
        connection: HTTPConnection,
        sock: socket.socket,
        response: urllib3.BaseHTTPResponse,
        guard: _ExchangeGuard,
    ) -> None:
        self._connection = connection
        self._sock = sock
        self._response = response
        self._guard = guard

    @property
    def status(self) -> int:
        return self._response.status

    def header(self, name: str) -> str | None:
        return self._response.headers.get(name)

    def read(self, amount: int, timeout: float) -> bytes:
        if self._guard.fired:
            raise TransportFailure(
                FailureStage.EXCHANGE, "exchange time limit reached", timed_out=True
            )
        try:
            # Once the body is complete, http.client has closed the socket;
            # the read below then reports the end of the body.
            with suppress(OSError):
                self._sock.settimeout(timeout)
            data = self._response.read1(amount, decode_content=False)
        except _FAILURES as exc:
            raise _failure(exc, FailureStage.EXCHANGE, self._guard) from None
        if self._guard.fired:
            # The shutdown looks like the end of the body; it is not.
            raise TransportFailure(
                FailureStage.EXCHANGE, "exchange time limit reached", timed_out=True
            )
        return data

    def close(self) -> None:
        self._guard.cancel()
        with suppress(*_FAILURES):
            self._response.close()
        with suppress(*_FAILURES):
            self._connection.close()
        with suppress(OSError):
            self._sock.close()


class Urllib3Transport:
    """The production :class:`~frame_gallery.net.wire.Transport`."""

    def __init__(
        self, *, cafile: str | None = None, connection_factory: ConnectionFactory | None = None
    ) -> None:
        self._cafile = cafile if cafile is not None else certifi.where()
        self._factory = connection_factory if connection_factory is not None else default_connection

    def open(
        self, request: WireRequest, *, connect_timeout: float, exchange_timeout: float
    ) -> WireResponse:
        connection = self._factory(request, connect_timeout, self._cafile)
        guard = _ExchangeGuard(connection, exchange_timeout)
        stage = FailureStage.CONNECT
        try:
            connection.connect()
            sock = connection.sock
            if sock is None:
                raise TransportFailure(stage, "no socket after connect")
            guard.bind(sock)
            _check_peer(sock, request)
            if request.tls:
                _check_tls(sock, request)
            stage = FailureStage.EXCHANGE
            # urllib3 applies the connection's timeout to the socket before it
            # sends and before it reads the headers.
            connection.timeout = exchange_timeout
            sock.settimeout(exchange_timeout)
            connection.request(
                "GET",
                request.target,
                headers=dict(request.headers),
                preload_content=False,
                decode_content=False,
            )
            response = connection.getresponse()
        except TransportFailure:
            guard.cancel()
            with suppress(*_FAILURES):
                connection.close()
            raise
        except _FAILURES as exc:
            guard.cancel()
            with suppress(*_FAILURES):
                connection.close()
            raise _failure(exc, stage, guard) from None
        return _Response(connection, sock, response, guard)


def _check_peer(sock: socket.socket, request: WireRequest) -> None:
    peer = sock.getpeername()
    try:
        connected = ip_address(peer[0])
    except (ValueError, TypeError, IndexError):
        connected = None
    if connected != request.address:
        raise TransportFailure(FailureStage.CONNECT, "connected to an unexpected peer")


def _check_tls(sock: socket.socket, request: WireRequest) -> None:
    if not (
        isinstance(sock, ssl.SSLSocket)
        and sock.version() in TLS_VERSIONS
        and sock.context.verify_mode == ssl.CERT_REQUIRED
        and sock.context.check_hostname
        and sock.server_hostname == request.host
    ):
        raise TransportFailure(FailureStage.CONNECT, "the TLS session is not verified")
