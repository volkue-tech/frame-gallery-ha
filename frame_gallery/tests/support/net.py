"""Fakes for the network seam (``frame_gallery.net.wire``): scripted resolver
and transport responses, so the gateway and the adapters are tested without
any network access (H2). All bodies are synthesized by the tests."""

from __future__ import annotations

import gzip
import json
from collections import deque
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from ipaddress import ip_address
from typing import Final

from frame_gallery.net.identity import ClientIdentity
from frame_gallery.net.wire import (
    FailureStage,
    IPAddress,
    TransportFailure,
    WireRequest,
)
from tests.support.clock import FakeClock

PLACEHOLDER_CONTACT: Final = "placeholder-contact@example.invalid"
"""The recognizable placeholder used by every test (D-119 as amended)."""

TEST_IDENTITY: Final = ClientIdentity(version="0.0.0-test", contact=PLACEHOLDER_CONTACT)

PUBLIC_V4: Final = ip_address("93.184.216.34")
PUBLIC_V4_B: Final = ip_address("93.184.216.35")
"""Addresses in public space used only as opaque values; nothing connects."""


class FakeResolver:
    """Answers from a table; records every lookup."""

    def __init__(
        self,
        answers: Mapping[str, Sequence[IPAddress] | TransportFailure] | None = None,
        *,
        default: Sequence[IPAddress] = (PUBLIC_V4,),
        clock: FakeClock | None = None,
        delay: float = 0.0,
    ) -> None:
        self.answers = dict(answers or {})
        self.default = tuple(default)
        self.calls: list[tuple[str, int, float]] = []
        self._clock = clock
        self._delay = delay

    def resolve(self, host: str, port: int, timeout: float) -> Sequence[IPAddress]:
        self.calls.append((host, port, timeout))
        if self._clock is not None and self._delay:
            self._clock.advance(min(self._delay, timeout))
        answer = self.answers.get(host, self.default)
        if isinstance(answer, TransportFailure):
            raise answer
        return answer


@dataclass
class FakeResponse:
    """A scripted response. ``body`` is split into reads of at most the
    requested amount; ``chunk`` caps each read further."""

    status: int = 200
    headers: Mapping[str, str] = field(default_factory=dict)
    body: bytes = b""
    chunk: int | None = None
    read_delay: float = 0.0
    """Seconds the fake clock advances on every read."""

    fail_after_reads: int | None = None
    failure: TransportFailure | None = None
    clock: FakeClock | None = None
    reads: list[tuple[int, float]] = field(default_factory=list)
    closed: bool = False
    _position: int = 0

    def header(self, name: str) -> str | None:
        wanted = name.lower()
        values = [value for key, value in self.headers.items() if key.lower() == wanted]
        return ", ".join(values) if values else None

    def read(self, amount: int, timeout: float) -> bytes:
        self.reads.append((amount, timeout))
        if self.clock is not None and self.read_delay:
            self.clock.advance(self.read_delay)
        if self.fail_after_reads is not None and len(self.reads) > self.fail_after_reads:
            raise self.failure or TransportFailure(FailureStage.EXCHANGE, "scripted")
        size = amount if self.chunk is None else min(amount, self.chunk)
        data = self.body[self._position : self._position + size]
        self._position += len(data)
        return data

    def close(self) -> None:
        self.closed = True


type Step = FakeResponse | TransportFailure | Callable[[WireRequest], FakeResponse]


@dataclass
class OpenCall:
    request: WireRequest
    connect_timeout: float
    exchange_timeout: float


class FakeTransport:
    """Plays back one scripted step per ``open``; records every call. When the
    steps run out, ``handler`` (if any) answers every further request."""

    def __init__(
        self,
        steps: Iterable[Step] = (),
        *,
        clock: FakeClock | None = None,
        handler: Callable[[WireRequest], FakeResponse] | None = None,
    ) -> None:
        self.steps: deque[Step] = deque(steps)
        self.calls: list[OpenCall] = []
        self.clock = clock
        self.handler = handler
        self.opened: list[FakeResponse] = []

    def add(self, *steps: Step) -> None:
        self.steps.extend(steps)

    def open(
        self, request: WireRequest, *, connect_timeout: float, exchange_timeout: float
    ) -> FakeResponse:
        self.calls.append(OpenCall(request, connect_timeout, exchange_timeout))
        if not self.steps:
            if self.handler is None:
                msg = f"no scripted response for {request.host}{request.target}"
                raise AssertionError(msg)
            step: Step = self.handler
        else:
            step = self.steps.popleft()
        if isinstance(step, TransportFailure):
            raise step
        response = step if isinstance(step, FakeResponse) else step(request)
        if response.clock is None:
            response.clock = self.clock
        self.opened.append(response)
        return response

    @property
    def targets(self) -> list[str]:
        return [f"{call.request.host}{call.request.target}" for call in self.calls]


def json_response(document: object, *, status: int = 200, gzipped: bool = False) -> FakeResponse:
    """A JSON response with correct length and type headers."""
    body = json.dumps(document).encode()
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if gzipped:
        body = gzip.compress(body)
        headers["Content-Encoding"] = "gzip"
    headers["Content-Length"] = str(len(body))
    return FakeResponse(status=status, headers=headers, body=body)


def image_response(body: bytes, media: str = "image/jpeg", *, status: int = 200) -> FakeResponse:
    return FakeResponse(
        status=status,
        headers={"Content-Type": media, "Content-Length": str(len(body))},
        body=body,
    )


def status_response(status: int, headers: Mapping[str, str] | None = None) -> FakeResponse:
    return FakeResponse(status=status, headers=dict(headers or {}))


def connect_failure(*, timed_out: bool = False) -> TransportFailure:
    return TransportFailure(FailureStage.CONNECT, "scripted connect failure", timed_out=timed_out)
