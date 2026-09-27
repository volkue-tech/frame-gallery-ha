"""The real resolver and transport, driven through fake urllib3 connections
and a fake ``getaddrinfo``; nothing here opens a socket (H2)."""

from __future__ import annotations

import http.client
import socket
import ssl
import threading
import time
from collections.abc import Callable, Sequence
from ipaddress import IPv4Address, ip_address
from typing import Any, cast

import certifi
import pytest
import urllib3
from urllib3.connection import HTTPConnection, HTTPSConnection

from frame_gallery.net import transport as transport_module
from frame_gallery.net.transport import (
    AddressInfo,
    SystemResolver,
    Urllib3Transport,
    default_connection,
    make_tls_context,
)
from frame_gallery.net.wire import (
    FailureStage,
    Resolver,
    Transport,
    TransportFailure,
    WireRequest,
)
from tests.conftest import NetworkBlockedError

ADDRESS = ip_address("93.184.216.34")
HOST = "api.example.org"


def _request(*, tls: bool = True, address: IPv4Address = ADDRESS) -> WireRequest:  # type: ignore[assignment]
    return WireRequest(
        address=address,
        host=HOST,
        port=443 if tls else 80,
        tls=tls,
        target="/v1/x?y=1",
        headers={"Host": HOST, "User-Agent": "test"},
    )


class _PlainSocket:
    """Stands in for a connected TCP socket."""

    def __init__(self, peer: object = ("93.184.216.34", 443)) -> None:
        self.peer = peer
        self.timeouts: list[float] = []
        self.shut = threading.Event()

    def getpeername(self) -> object:
        return self.peer

    def settimeout(self, value: float) -> None:
        self.timeouts.append(value)

    def shutdown(self, how: int) -> None:
        self.shut.set()

    def close(self) -> None:
        self.closed = True


class _TlsSocket(ssl.SSLSocket):
    """An ``SSLSocket`` instance without a real socket behind it."""

    def __new__(cls, **_kwargs: object) -> _TlsSocket:
        return socket.socket.__new__(cls)

    def __init__(
        self,
        *,
        version: str | None = "TLSv1.3",
        verify_mode: ssl.VerifyMode = ssl.CERT_REQUIRED,
        check_hostname: bool = True,
        hostname: str = HOST,
        peer: object = ("93.184.216.34", 443),
    ) -> None:
        self._fake_version = version
        self._fake_context = make_tls_context(certifi.where())
        self._fake_context.check_hostname = check_hostname
        if verify_mode is not ssl.CERT_REQUIRED:
            self._fake_context.check_hostname = False
            self._fake_context.verify_mode = verify_mode
        self._fake_hostname = hostname
        self._fake_peer = peer
        self.timeouts: list[float] = []

    def version(self) -> str | None:
        return self._fake_version

    @property
    def context(self) -> ssl.SSLContext:  # type: ignore[override]
        return self._fake_context

    @property
    def server_hostname(self) -> str:  # type: ignore[override]
        return self._fake_hostname

    def getpeername(self) -> Any:
        return self._fake_peer

    def settimeout(self, value: float | None) -> None:
        self.timeouts.append(cast("float", value))

    def shutdown(self, how: int) -> None:
        pass

    def close(self) -> None:
        pass


class _Response:
    def __init__(self, chunks: Sequence[bytes | BaseException] = (b"",), status: int = 200) -> None:
        self.status = status
        self.headers = urllib3.HTTPHeaderDict({"Content-Type": "application/json"})
        self.headers.add("Set-Cookie", "a=1")
        self.headers.add("Set-Cookie", "b=2")
        self._chunks = list(chunks)
        self.read_calls: list[tuple[int, bool]] = []
        self.closed = False
        self.block: threading.Event | None = None

    def read1(self, amt: int, decode_content: bool) -> bytes:
        self.read_calls.append((amt, decode_content))
        if self.block is not None:
            self.block.wait(5)
            return b""
        item = self._chunks.pop(0) if self._chunks else b""
        if isinstance(item, BaseException):
            raise item
        return item

    def close(self) -> None:
        self.closed = True


class _Connection:
    """Stands in for ``urllib3.connection.HTTP(S)Connection``."""

    def __init__(
        self,
        *,
        sock: object | None = None,
        connect_error: BaseException | None = None,
        request_error: BaseException | None = None,
        response: _Response | BaseException | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self._sock_after_connect = sock if sock is not None else _PlainSocket()
        self.sock: object | None = None
        self.connect_error = connect_error
        self.request_error = request_error
        self.response = response if response is not None else _Response()
        self.close_error = close_error
        self.requests: list[tuple[str, str, dict[str, str], bool, bool]] = []
        self.closed = 0

    def connect(self) -> None:
        if self.connect_error is not None:
            raise self.connect_error
        self.sock = self._sock_after_connect

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        preload_content: bool,
        decode_content: bool,
    ) -> None:
        self.requests.append((method, url, headers, preload_content, decode_content))
        if self.request_error is not None:
            raise self.request_error

    def getresponse(self) -> _Response:
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response

    def close(self) -> None:
        self.closed += 1
        if self.close_error is not None:
            raise self.close_error


def _transport(connection: _Connection) -> tuple[Urllib3Transport, list[tuple[WireRequest, float]]]:
    made: list[tuple[WireRequest, float]] = []

    def factory(request: WireRequest, connect_timeout: float, cafile: str) -> HTTPConnection:
        assert cafile == certifi.where()
        made.append((request, connect_timeout))
        return cast("HTTPConnection", connection)

    return Urllib3Transport(connection_factory=factory), made


class TestOpen:
    def test_plain_exchange(self) -> None:
        response = _Response([b"ab", b"c", b""])
        connection = _Connection(response=response)
        transport, made = _transport(connection)
        wire = transport.open(_request(tls=False), connect_timeout=2.0, exchange_timeout=9.0)
        assert made == [(_request(tls=False), 2.0)]
        assert connection.requests == [
            ("GET", "/v1/x?y=1", {"Host": HOST, "User-Agent": "test"}, False, False)
        ]
        sock = cast("_PlainSocket", connection.sock)
        assert sock.timeouts == [9.0]
        assert wire.status == 200
        assert wire.header("content-type") == "application/json"
        assert wire.header("Set-Cookie") == "a=1, b=2"
        assert wire.header("Location") is None
        assert wire.read(10, 1.5) == b"ab"
        assert wire.read(10, 1.0) == b"c"
        assert wire.read(10, 0.5) == b""
        assert sock.timeouts == [9.0, 1.5, 1.0, 0.5]
        assert response.read_calls == [(10, False)] * 3
        wire.close()
        wire.close()
        assert response.closed
        assert connection.closed == 2

    def test_tls_exchange_is_checked_before_sending(self) -> None:
        connection = _Connection(sock=_TlsSocket())
        transport, _made = _transport(connection)
        wire = transport.open(_request(), connect_timeout=2.0, exchange_timeout=9.0)
        assert wire.status == 200
        wire.close()

    @pytest.mark.parametrize(
        "sock",
        [
            _TlsSocket(version="TLSv1.1"),
            _TlsSocket(version=None),
            _TlsSocket(check_hostname=False),
            _TlsSocket(verify_mode=ssl.CERT_OPTIONAL),
            _TlsSocket(hostname="other.example.org"),
            _PlainSocket(),
        ],
    )
    def test_unverified_tls_is_refused(self, sock: object) -> None:
        connection = _Connection(sock=sock)
        transport, _made = _transport(connection)
        with pytest.raises(TransportFailure, match="not verified") as excinfo:
            transport.open(_request(), connect_timeout=2.0, exchange_timeout=9.0)
        assert excinfo.value.stage is FailureStage.CONNECT
        assert connection.requests == []
        assert connection.closed == 1

    @pytest.mark.parametrize(
        "peer", [("93.184.216.35", 443), ("not-an-ip", 443), (), None, ("::1", 443, 0, 0)]
    )
    def test_the_peer_must_be_the_validated_address(self, peer: object) -> None:
        connection = _Connection(sock=_PlainSocket(peer))
        transport, _made = _transport(connection)
        with pytest.raises(TransportFailure, match="unexpected peer") as excinfo:
            transport.open(_request(tls=False), connect_timeout=2.0, exchange_timeout=9.0)
        assert excinfo.value.stage is FailureStage.CONNECT
        assert connection.requests == []

    def test_no_socket_after_connect(self) -> None:
        connection = _Connection()
        connection.connect = lambda: None  # type: ignore[method-assign]
        transport, _made = _transport(connection)
        with pytest.raises(TransportFailure, match="no socket"):
            transport.open(_request(tls=False), connect_timeout=2.0, exchange_timeout=9.0)

    @pytest.mark.parametrize(
        ("error", "timed_out"),
        [
            (ConnectionRefusedError(), False),
            (TimeoutError(), True),
            (urllib3.exceptions.ConnectTimeoutError(), True),
            (urllib3.exceptions.NewConnectionError(cast("HTTPConnection", None), "refused"), False),
            (ssl.SSLCertVerificationError("bad certificate"), False),
            (ValueError("bad"), False),
        ],
    )
    def test_connect_errors(self, error: BaseException, timed_out: bool) -> None:
        connection = _Connection(connect_error=error, close_error=OSError("close"))
        transport, _made = _transport(connection)
        with pytest.raises(TransportFailure) as excinfo:
            transport.open(_request(tls=False), connect_timeout=2.0, exchange_timeout=9.0)
        assert excinfo.value.stage is FailureStage.CONNECT
        assert excinfo.value.timed_out is timed_out
        assert excinfo.value.detail == type(error).__name__

    @pytest.mark.parametrize(
        "error",
        [
            BrokenPipeError(),
            http.client.RemoteDisconnected("gone"),
            http.client.LineTooLong("header line"),
            urllib3.exceptions.ProtocolError("bad"),
        ],
    )
    def test_exchange_errors(self, error: BaseException) -> None:
        connection = _Connection(response=error)
        transport, _made = _transport(connection)
        with pytest.raises(TransportFailure) as excinfo:
            transport.open(_request(tls=False), connect_timeout=2.0, exchange_timeout=9.0)
        assert excinfo.value.stage is FailureStage.EXCHANGE
        assert not excinfo.value.timed_out
        assert connection.closed == 1

    def test_request_errors(self) -> None:
        connection = _Connection(request_error=OSError("send"))
        transport, _made = _transport(connection)
        with pytest.raises(TransportFailure) as excinfo:
            transport.open(_request(tls=False), connect_timeout=2.0, exchange_timeout=9.0)
        assert excinfo.value.stage is FailureStage.EXCHANGE

    def test_unexpected_errors_propagate(self) -> None:
        connection = _Connection(connect_error=RuntimeError("bug"))
        transport, _made = _transport(connection)
        with pytest.raises(RuntimeError, match="bug"):
            transport.open(_request(tls=False), connect_timeout=2.0, exchange_timeout=9.0)


class TestRead:
    def _open(self, response: _Response, exchange: float = 9.0) -> tuple[Any, _Connection]:
        connection = _Connection(response=response)
        transport, _made = _transport(connection)
        wire = transport.open(_request(tls=False), connect_timeout=2.0, exchange_timeout=exchange)
        return wire, connection

    @pytest.mark.parametrize(
        ("error", "timed_out"),
        [
            (TimeoutError(), True),
            (urllib3.exceptions.ReadTimeoutError(None, None, "slow"), True),  # type: ignore[arg-type]
            (urllib3.exceptions.IncompleteRead(3, 7), False),
            (ConnectionResetError(), False),
        ],
    )
    def test_read_errors(self, error: BaseException, timed_out: bool) -> None:
        wire, _connection = self._open(_Response([error]))
        with pytest.raises(TransportFailure) as excinfo:
            wire.read(10, 1.0)
        assert excinfo.value.stage is FailureStage.EXCHANGE
        assert excinfo.value.timed_out is timed_out
        wire.close()

    def test_the_exchange_limit_shuts_the_socket(self) -> None:
        response = _Response()
        response.block = threading.Event()
        wire, connection = self._open(response, exchange=0.05)
        sock = cast("_PlainSocket", connection.sock)

        def release() -> None:
            sock.shut.wait(5)
            assert response.block is not None
            response.block.set()

        releaser = threading.Thread(target=release)
        releaser.start()
        with pytest.raises(TransportFailure, match="exchange time limit") as excinfo:
            wire.read(10, 1.0)
        releaser.join(5)
        assert excinfo.value.timed_out
        assert sock.shut.is_set()
        with pytest.raises(TransportFailure, match="exchange time limit"):
            wire.read(10, 1.0)
        wire.close()

    def test_a_fired_guard_during_open_is_a_timeout(self) -> None:
        connection = _Connection()
        fired = threading.Event()

        def slow_response() -> _Response:
            sock = cast("_PlainSocket", connection.sock)
            sock.shut.wait(5)
            fired.set()
            raise OSError("socket shut down")

        connection.getresponse = slow_response  # type: ignore[method-assign]
        transport, _made = _transport(connection)
        with pytest.raises(TransportFailure, match="exchange time limit") as excinfo:
            transport.open(_request(tls=False), connect_timeout=2.0, exchange_timeout=0.05)
        assert fired.is_set()
        assert excinfo.value.timed_out
        assert excinfo.value.stage is FailureStage.EXCHANGE

    def test_a_guard_after_close_is_harmless(self) -> None:
        wire, connection = self._open(_Response(), exchange=0.01)
        connection.sock = None
        wire.close()
        # A guard that fires once the socket is gone has nothing to shut down.
        guard = transport_module._ExchangeGuard(cast("HTTPConnection", connection), 0.0)
        guard._timer.join(5)
        assert guard.fired

    def test_reads_use_the_socket_captured_at_connect(self) -> None:
        # With "Connection: close", http.client drops the connection's socket
        # reference inside getresponse(); the body is still read from it.
        wire, connection = self._open(_Response([b"x"]))
        sock = cast("_PlainSocket", connection.sock)
        connection.sock = None
        assert wire.read(10, 1.5) == b"x"
        assert sock.timeouts[-1] == 1.5
        wire.close()
        assert sock.closed

    def test_close_suppresses_errors(self) -> None:
        response = _Response()
        wire, connection = self._open(response)

        def failing_close() -> None:
            raise OSError("close")

        response.close = failing_close  # type: ignore[method-assign]
        connection.close_error = OSError("close")
        sock = cast("_PlainSocket", connection.sock)
        sock.close = failing_close  # type: ignore[method-assign]
        wire.close()


class TestConnectionFactory:
    def test_https_connection_is_pinned_to_the_address(self) -> None:
        connection = default_connection(_request(), 4.0, certifi.where())
        assert isinstance(connection, HTTPSConnection)
        assert connection.host == "93.184.216.34"
        assert connection.port == 443
        assert connection.server_hostname == HOST
        assert connection.assert_hostname is None
        assert connection.timeout == 4.0
        assert connection.sock is None
        assert connection.proxy is None
        context = connection.ssl_context
        assert context is not None
        assert context.verify_mode is ssl.CERT_REQUIRED
        assert context.check_hostname
        assert context.minimum_version is ssl.TLSVersion.TLSv1_2
        assert context.cert_store_stats()["x509_ca"] > 100

    def test_ipv6_addresses_are_used_bare(self) -> None:
        request = WireRequest(
            address=ip_address("2606:4700:4700::1111"), host=HOST, port=443, tls=True, target="/"
        )
        connection = default_connection(request, 4.0, certifi.where())
        assert connection.host == "2606:4700:4700::1111"

    def test_plain_connection(self) -> None:
        connection = default_connection(_request(tls=False), 3.0, certifi.where())
        assert type(connection) is HTTPConnection
        assert connection.port == 80

    def test_contexts_are_fresh_and_trust_only_the_bundle(self) -> None:
        first = make_tls_context(certifi.where())
        second = make_tls_context(certifi.where())
        assert first is not second
        assert first.protocol is ssl.PROTOCOL_TLS_CLIENT

    def test_default_transport_uses_certifi(self) -> None:
        transport = Urllib3Transport()
        assert transport._cafile == certifi.where()
        assert transport._factory is default_connection


def _info(family: socket.AddressFamily, address: str) -> AddressInfo:
    sockaddr: tuple[str, int] | tuple[str, int, int, int]
    sockaddr = (address, 443) if family == socket.AF_INET else (address, 443, 0, 0)
    return (family, socket.SOCK_STREAM, 6, "", sockaddr)


class TestResolver:
    def test_answers_are_deduplicated_in_order(self) -> None:
        calls: list[tuple[str, int, int, int, int]] = []

        def lookup(host: str, port: int, family: int, kind: int, proto: int) -> list[AddressInfo]:
            calls.append((host, port, family, kind, proto))
            return [
                _info(socket.AF_INET6, "2606:4700:4700::1111"),
                _info(socket.AF_INET, "93.184.216.34"),
                _info(socket.AF_INET, "93.184.216.34"),
                _info(socket.AF_INET6, "fe80::1%en0"),
                (socket.AF_UNIX, socket.SOCK_STREAM, 0, "", (0, b"")),
            ]

        addresses = SystemResolver(lookup).resolve(HOST, 443, 1.0)
        # A scoped address is passed on; the gateway refuses it as not public.
        assert addresses == (
            ip_address("2606:4700:4700::1111"),
            ip_address("93.184.216.34"),
            ip_address("fe80::1%en0"),
        )
        assert calls == [(HOST, 443, 0, socket.SOCK_STREAM, socket.IPPROTO_TCP)]

    def test_failures(self) -> None:
        def lookup(*_args: object) -> list[AddressInfo]:
            raise socket.gaierror(socket.EAI_NONAME, "unknown")

        with pytest.raises(TransportFailure, match="gaierror") as excinfo:
            SystemResolver(lookup).resolve(HOST, 443, 1.0)
        assert excinfo.value.stage is FailureStage.RESOLVE
        assert not excinfo.value.timed_out

    def test_no_usable_address(self) -> None:
        def lookup(*_args: object) -> list[AddressInfo]:
            return [_info(socket.AF_INET, "not-an-address")]

        with pytest.raises(TransportFailure, match="no usable address"):
            SystemResolver(lookup).resolve(HOST, 443, 1.0)

    def test_timeout(self) -> None:
        release = threading.Event()

        def lookup(*_args: object) -> list[AddressInfo]:
            release.wait(5)
            return []

        try:
            with pytest.raises(TransportFailure, match="timed out") as excinfo:
                SystemResolver(lookup).resolve(HOST, 443, 0.05)
            assert excinfo.value.timed_out
        finally:
            release.set()

    def test_the_default_lookup_is_the_guarded_socket_function(self) -> None:
        # The session guard (H2) replaced socket.getaddrinfo: the resolver
        # looks it up at call time, so it is blocked like any other lookup.
        with pytest.raises(TransportFailure, match=NetworkBlockedError.__name__):
            SystemResolver().resolve(HOST, 443, 1.0)


def test_protocol_conformance() -> None:
    resolver: Resolver = SystemResolver()
    transport: Transport = Urllib3Transport()
    assert resolver is not None
    assert transport is not None
    factory: Callable[[WireRequest, float, str], HTTPConnection] = default_connection
    assert factory is default_connection


# --- the real http.client and urllib3 stack over a local socket pair ----------


class _PeerSocket(socket.socket):
    """One end of a socket pair that reports the validated address as its peer."""

    def getpeername(self) -> Any:
        return ("93.184.216.34", 80)


class _PairedConnection(HTTPConnection):
    """A real urllib3 connection whose connect() takes over one end of a pair."""

    def __init__(self, sock: socket.socket, timeout: float) -> None:
        super().__init__("93.184.216.34", 80, timeout=timeout)
        self._paired = sock

    def connect(self) -> None:
        self.sock = self._paired


class _Server:
    """Answers one request on the other end of the pair with scripted parts."""

    def __init__(self, parts: Sequence[tuple[float, bytes]]) -> None:
        client, self.peer = socket.socketpair()
        self.client = _PeerSocket(fileno=client.detach())
        self.parts = parts
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self) -> None:
        received = b""
        with self.peer:
            while b"\r\n\r\n" not in received:
                chunk = self.peer.recv(4096)
                if not chunk:
                    return
                received += chunk
            for delay, data in self.parts:
                if delay:
                    time.sleep(delay)
                try:
                    self.peer.sendall(data)
                except OSError:
                    return

    def transport(self, connect_timeout: float) -> Urllib3Transport:
        def factory(request: WireRequest, timeout: float, cafile: str) -> HTTPConnection:
            return _PairedConnection(self.client, timeout)

        return Urllib3Transport(connection_factory=factory)


def _open(server: _Server, *, connect_timeout: float, exchange_timeout: float) -> Any:
    return server.transport(connect_timeout).open(
        _request(tls=False), connect_timeout=connect_timeout, exchange_timeout=exchange_timeout
    )


HEADERS_CLOSE_CHUNKED = (
    b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"
    b"Connection: close\r\nTransfer-Encoding: chunked\r\n\r\n"
)


class TestRealStack:
    def test_a_dripping_peer_is_cut_off_at_the_exchange_limit(self) -> None:
        # One byte of chunk framing every 50 ms for 3 s, after "Connection: close".
        drip = [(0.05, b"1")] * 60
        server = _Server([(0.0, HEADERS_CLOSE_CHUNKED), *drip])
        started = time.monotonic()
        wire = _open(server, connect_timeout=0.2, exchange_timeout=0.4)

        def drain() -> None:
            while wire.read(65536, 0.3):
                pass

        with pytest.raises(TransportFailure) as excinfo:
            drain()
        elapsed = time.monotonic() - started
        wire.close()
        assert excinfo.value.timed_out
        assert elapsed < 1.5

    def test_headers_may_take_longer_than_the_connect_timeout(self) -> None:
        body = b'{"ok": true}'
        server = _Server(
            [
                (0.3, b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n"),
                (0.0, b"Content-Length: %d\r\nConnection: close\r\n\r\n" % len(body)),
                (0.0, body),
            ]
        )
        wire = _open(server, connect_timeout=0.1, exchange_timeout=3.0)
        assert wire.status == 200
        assert wire.read(65536, 2.0) == body
        wire.close()

    def test_body_reads_wait_for_the_read_timeout(self) -> None:
        body = b"0123456789"
        server = _Server(
            [
                (0.0, b"HTTP/1.1 200 OK\r\nContent-Length: 10\r\nConnection: close\r\n\r\n"),
                (0.3, body),
            ]
        )
        wire = _open(server, connect_timeout=0.1, exchange_timeout=3.0)
        assert wire.read(65536, 2.0) == body
        assert wire.read(65536, 2.0) == b""
        wire.close()

    def test_a_stalled_body_times_out_after_the_read_timeout(self) -> None:
        server = _Server(
            [
                (0.0, b"HTTP/1.1 200 OK\r\nContent-Length: 10\r\nConnection: close\r\n\r\n"),
                (2.0, b"too late!!"),
            ]
        )
        wire = _open(server, connect_timeout=1.5, exchange_timeout=5.0)
        started = time.monotonic()
        with pytest.raises(TransportFailure) as excinfo:
            wire.read(65536, 0.2)
        elapsed = time.monotonic() - started
        wire.close()
        assert excinfo.value.timed_out
        assert elapsed < 1.0


@pytest.mark.parametrize(
    ("head", "body_parts"),
    [
        (b"Content-Length: 10\r\nConnection: close\r\n", [b'{"a":', b" 123}"]),
        (
            b"Transfer-Encoding: chunked\r\nConnection: close\r\n",
            [b'5\r\n{"a":\r\n', b"5\r\n 123}\r\n0\r\n\r\n"],
        ),
        (b"Connection: close\r\n", [b'{"a":', b" 123}"]),
        (b"Content-Length: 12\r\n", [b'{"a": 123}  ']),
    ],
    ids=["length-close", "chunked-close", "close-delimited", "length-keep-alive"],
)
def test_bodies_read_to_the_end_over_the_real_stack(head: bytes, body_parts: list[bytes]) -> None:
    parts = [(0.0, b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n" + head + b"\r\n")]
    parts += [(0.05, part) for part in body_parts]
    server = _Server(parts)
    wire = _open(server, connect_timeout=1.0, exchange_timeout=5.0)
    received = b""
    while chunk := wire.read(65536, 2.0):
        received += chunk
    wire.close()
    assert received.strip() == b'{"a": 123}'
