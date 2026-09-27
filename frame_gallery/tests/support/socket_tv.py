"""A scripted television on the far end of a socket pair (no network).

It lets the **installed** ``samsungtvws`` 3.0.6 and ``websocket-client`` run
unchanged against the art channel's messages (D-162): the test replaces only
``websocket.create_connection`` (the TCP, TLS, and HTTP upgrade steps) with
:meth:`SocketTV.create_connection`, which returns a real
``websocket.WebSocket`` over one end of ``socket.socketpair()``. A thread on
the other end speaks RFC 6455 frames (unmasked from the server) and the
art-app messages below, as the library expects them. The D2D upload socket
is a real ``socket.connect`` to the address the television names, so the
connect guard and the H2 guard see it.

The message formats are the ones the installed library sends and parses;
they are independently written here from reading that distribution.
"""

from __future__ import annotations

import json
import socket
import struct
import threading
from dataclasses import dataclass, field
from typing import Any

import websocket

D2D_PORT = 49152


@dataclass
class TvScript:
    connections: list[str] = field(default_factory=lambda: ["ok"])
    """One behaviour per connection; the last one repeats. ``ok`` (connect,
    then ready), ``unauthorized``, ``silent`` (nothing after the handshake:
    a pairing prompt), ``no_ready`` (connect, then nothing), ``hang`` (the
    handshake itself times out)."""

    issue_token: str | None = "12345678"  # noqa: S105 - a fake pairing token
    api_version: str = "4.3.4.0"
    d2d_ip: str = "192.0.2.20"
    select_error: str = "-11"


class SocketTV:
    def __init__(self, script: TvScript) -> None:
        self.script = script
        self.urls: list[str] = []
        self.requests: list[str] = []
        self._threads: list[threading.Thread] = []
        self._sockets: list[socket.socket] = []

    # ------------------------------------------------------------ client side

    def create_connection(self, url: str, timeout: float | None = None, **_: Any) -> Any:
        """Stands in for ``websocket.create_connection``."""
        behaviour = self._next_behaviour()
        self.urls.append(url)
        if behaviour == "hang":
            raise websocket.WebSocketTimeoutException("Connection timed out")
        client, server = socket.socketpair()
        self._sockets += [client, server]
        connection = websocket.WebSocket()
        connection.sock = client
        connection.connected = True
        connection.settimeout(timeout)
        thread = threading.Thread(target=self._serve, args=(server, behaviour), daemon=True)
        self._threads.append(thread)
        thread.start()
        return connection

    def _next_behaviour(self) -> str:
        connections = self.script.connections
        return connections.pop(0) if len(connections) > 1 else connections[0]

    def close(self) -> None:
        for sock in self._sockets:
            sock.close()
        for thread in self._threads:
            thread.join(timeout=5)

    # ------------------------------------------------------------ server side

    def _serve(self, sock: socket.socket, behaviour: str) -> None:
        try:
            if behaviour == "unauthorized":
                _send(sock, {"event": "ms.channel.unauthorized"})
            if behaviour in ("ok", "no_ready"):
                data = {} if self.script.issue_token is None else {"token": self.script.issue_token}
                _send(sock, {"event": "ms.channel.connect", "data": data})
            if behaviour == "ok":
                _send(sock, {"event": "ms.channel.ready"})
            while (message := _receive(sock)) is not None:
                self._answer(sock, message)
        except OSError:
            return

    def _answer(self, sock: socket.socket, message: dict[str, Any]) -> None:
        request = json.loads(message["params"]["data"])
        name, request_id = request["request"], request["request_id"]
        self.requests.append(name)
        if name == "api_version":
            reply = {"event": "api_version", "version": self.script.api_version}
        elif name == "send_image":
            info = {"ip": self.script.d2d_ip, "port": D2D_PORT, "key": "k", "secured": False}
            reply = {"event": "ready_to_use", "conn_info": json.dumps(info)}
        else:
            reply = {
                "event": "error",
                "error_code": self.script.select_error,
                "request_data": json.dumps({"request": name}),
            }
        reply |= {"request_id": request_id, "id": request_id}
        _send(sock, {"event": "d2d_service_message", "data": json.dumps(reply)})


def _send(sock: socket.socket, message: dict[str, Any]) -> None:
    payload = json.dumps(message).encode()
    if len(payload) < 126:
        header = struct.pack("!BB", 0x81, len(payload))
    else:
        header = struct.pack("!BBH", 0x81, 126, len(payload))
    sock.sendall(header + payload)


def _receive(sock: socket.socket) -> dict[str, Any] | None:
    """One masked client text frame, or ``None`` when the client is gone."""
    head = _exactly(sock, 2)
    if head is None:
        return None
    length = head[1] & 0x7F
    if length == 126:
        extended = _exactly(sock, 2)
        length = struct.unpack("!H", extended or b"\0\0")[0]
    elif length == 127:
        extended = _exactly(sock, 8)
        length = struct.unpack("!Q", extended or b"\0" * 8)[0]
    mask = _exactly(sock, 4) or b"\0\0\0\0"
    body = _exactly(sock, length) or b""
    text = bytes(byte ^ mask[index % 4] for index, byte in enumerate(body))
    if head[0] & 0x0F != 0x1:
        return None  # a close frame, or anything else: the client is done
    result: dict[str, Any] = json.loads(text)
    return result


def _exactly(sock: socket.socket, size: int) -> bytes | None:
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data
