"""The Supervisor helper reader (§15.3, D-112; acceptance items B3-B5)."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from ipaddress import ip_address

import pytest

from frame_gallery.app.ports import HelperReader
from frame_gallery.budget.deadline import Deadline
from frame_gallery.config.filters import FilterField
from frame_gallery.errors import Cancelled
from frame_gallery.ha.client import SupervisorHelperReader
from frame_gallery.net.wire import FailureStage, TransportFailure, WireRequest
from tests.support.clock import FakeClock
from tests.support.net import FakeResolver, FakeResponse, FakeTransport, connect_failure

TOKEN = "fake-supervisor-token-0123456789"  # noqa: S105 - a synthetic test value
SUPERVISOR = ip_address("172.30.32.2")
HELPERS: Mapping[FilterField, str] = {
    FilterField.SOURCE: "input_select.frame_source",
    FilterField.DEPARTMENT: "select.frame_department",
    FilterField.STYLE: "input_text.frame_style",
    FilterField.COLOR: "input_select.frame_colour",
}


def state(value: object, **extra: object) -> FakeResponse:
    body = json.dumps({"entity_id": "x.y", "state": value, "attributes": {}, **extra}).encode()
    return FakeResponse(
        headers={"Content-Type": "application/json", "Content-Length": str(len(body))}, body=body
    )


class Rig:
    def __init__(self, *, token: str | None = TOKEN, resolver: FakeResolver | None = None) -> None:
        self.clock = FakeClock()
        self.resolver = resolver or FakeResolver(default=(SUPERVISOR,), clock=self.clock)
        self.transport = FakeTransport(clock=self.clock)
        self.reader = SupervisorHelperReader(
            token=token, resolver=self.resolver, transport=self.transport
        )

    def deadline(self, seconds: float = 10.0) -> Deadline:
        return Deadline.after(self.clock, seconds, "configure")

    def read(
        self, helpers: Mapping[FilterField, str] = HELPERS, seconds: float = 10.0
    ) -> Mapping[FilterField, str | None]:
        return self.reader.read(helpers, self.deadline(seconds))


@pytest.fixture
def rig() -> Rig:
    return Rig()


def test_reads_each_helper_once(rig: Rig) -> None:
    rig.transport.add(state("art_institute_chicago"), state("cma_prints"), state("Any"))
    rig.transport.add(state("unavailable"))
    assert rig.read() == {
        FilterField.SOURCE: "art_institute_chicago",
        FilterField.DEPARTMENT: "cma_prints",
        FilterField.STYLE: "Any",
        FilterField.COLOR: "unavailable",
    }
    assert rig.resolver.calls == [("supervisor", 80, 3.0)]
    requests = [call.request for call in rig.transport.calls]
    assert [request.target for request in requests] == [
        "/core/api/states/input_select.frame_source",
        "/core/api/states/select.frame_department",
        "/core/api/states/input_text.frame_style",
        "/core/api/states/input_select.frame_colour",
    ]
    first: WireRequest = requests[0]
    assert (first.address, first.host, first.port, first.tls) == (
        SUPERVISOR,
        "supervisor",
        80,
        False,
    )
    assert first.headers["Authorization"] == f"Bearer {TOKEN}"
    assert first.headers["Host"] == "supervisor"
    assert first.headers["Accept"] == "application/json"
    assert first.headers["User-Agent"].startswith("FrameGallery/")
    assert "contact" not in first.headers["User-Agent"]
    assert all(call.exchange_timeout == 3.0 for call in rig.transport.calls)
    assert all(response.closed for response in rig.transport.opened)


def test_no_helpers_means_no_request(rig: Rig) -> None:
    assert rig.read({}) == {}
    assert rig.resolver.calls == []


@pytest.mark.parametrize("token", [None, "", "has space", "line\nbreak", "ä" * 10])
def test_without_a_usable_token_nothing_is_sent(
    token: str | None, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    rig = Rig(token=token)
    assert rig.read() == dict.fromkeys(HELPERS)
    assert rig.resolver.calls == []
    assert rig.transport.calls == []
    assert "no usable Supervisor token" in caplog.text


@pytest.mark.parametrize(
    "answer",
    [
        (ip_address("93.184.216.34"),),
        (SUPERVISOR, ip_address("93.184.216.34")),
        (ip_address("127.0.0.1"),),
        (ip_address("169.254.1.1"),),
        (),
    ],
)
def test_the_token_goes_only_to_a_private_address(answer: tuple[object, ...]) -> None:
    resolver = FakeResolver(default=answer)  # type: ignore[arg-type]
    rig = Rig(resolver=resolver)
    assert rig.read() == dict.fromkeys(HELPERS)
    assert rig.transport.calls == []


def test_resolution_failure(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    failing = TransportFailure(FailureStage.RESOLVE, "gaierror")
    rig = Rig(resolver=FakeResolver({"supervisor": failing}))
    assert rig.read() == dict.fromkeys(HELPERS)
    assert "name resolution failed (gaierror)" in caplog.text


def test_no_time_to_resolve(rig: Rig) -> None:
    deadline = rig.deadline(1.0)
    rig.clock.advance(1.0)
    assert rig.reader.read(HELPERS, deadline) == dict.fromkeys(HELPERS)
    assert rig.resolver.calls == []


@pytest.mark.parametrize(
    "response",
    [
        FakeResponse(status=404),
        FakeResponse(status=401),
        FakeResponse(status=302, headers={"Location": "http://elsewhere/"}),
        FakeResponse(status=500),
        FakeResponse(headers={"Content-Type": "text/plain"}, body=b"on"),
        FakeResponse(headers={"Content-Type": "application/json", "Content-Encoding": "gzip"}),
        FakeResponse(headers={"Content-Type": "application/json", "Content-Length": "x"}),
        FakeResponse(headers={"Content-Type": "application/json", "Content-Length": "70000"}),
        FakeResponse(
            headers={"Content-Type": "application/json", "Content-Length": "40"}, body=b"{}"
        ),
        FakeResponse(headers={"Content-Type": "application/json"}, body=b"[" + b" " * 70_000),
        FakeResponse(headers={"Content-Type": "application/json"}, body=b"{"),
        FakeResponse(headers={"Content-Type": "application/json"}, body=b"\xff"),
        FakeResponse(headers={"Content-Type": "application/json"}, body=b"NaN"),
        FakeResponse(headers={"Content-Type": "application/json"}, body=b'["on"]'),
        state(None),
        state(3),
        state("x" * 256),
        FakeResponse(headers={"Content-Type": "application/json"}, body=b'{"attributes": {}}'),
    ],
)
def test_bad_responses_fall_back(rig: Rig, response: FakeResponse) -> None:
    rig.transport.add(response)
    assert rig.read({FilterField.STYLE: "input_text.frame_style"}) == {FilterField.STYLE: None}
    assert response.closed


def test_a_state_of_255_characters_is_used(rig: Rig) -> None:
    rig.transport.add(state("s" * 255))
    assert rig.read({FilterField.STYLE: "input_text.frame_style"}) == {FilterField.STYLE: "s" * 255}


def test_one_failure_does_not_stop_the_others(rig: Rig) -> None:
    rig.transport.add(
        connect_failure(),
        TransportFailure(FailureStage.EXCHANGE, "reset"),
        state("style_x"),
        FakeResponse(
            headers={"Content-Type": "application/json"},
            body=b"{}",
            fail_after_reads=0,
        ),
    )
    assert rig.read() == {
        FilterField.SOURCE: None,
        FilterField.DEPARTMENT: None,
        FilterField.STYLE: "style_x",
        FilterField.COLOR: None,
    }
    assert len(rig.transport.calls) == 4


def test_invalid_entity_ids_are_never_requested(rig: Rig) -> None:
    helpers = {FilterField.STYLE: "input_text.x/../../config", FilterField.COLOR: "light.kitchen"}
    assert rig.read(helpers) == {FilterField.STYLE: None, FilterField.COLOR: None}
    assert rig.transport.calls == []


def test_each_read_is_bounded_to_three_seconds(rig: Rig) -> None:
    slow = state("late")
    slow.chunk = 2
    slow.read_delay = 1.0
    rig.transport.add(slow, state("on time"))
    assert rig.read({FilterField.STYLE: "input_text.a", FilterField.COLOR: "input_text.b"}) == {
        FilterField.STYLE: None,
        FilterField.COLOR: "on time",
    }
    assert max(timeout for _amount, timeout in slow.reads) <= 3.0


def test_the_configuration_deadline_bounds_all_reads(rig: Rig) -> None:
    slow = state("late")
    slow.chunk = 1
    slow.read_delay = 1.0
    rig.transport.add(slow)
    result = rig.read({FilterField.STYLE: "input_text.a", FilterField.COLOR: "input_text.b"}, 2.5)
    assert result == {FilterField.STYLE: None, FilterField.COLOR: None}
    assert len(rig.transport.calls) == 1  # no time was left for the second read


def test_a_stop_request_propagates(rig: Rig) -> None:
    def cancelled(request: WireRequest) -> FakeResponse:
        raise Cancelled

    rig.transport.add(cancelled)
    with pytest.raises(Cancelled):
        rig.read()


def test_logs_never_contain_the_token_or_values(rig: Rig, caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    rig.transport.add(FakeResponse(status=401), state("secret-looking-value"))
    rig.read({FilterField.STYLE: "input_text.a", FilterField.COLOR: "input_text.b"})
    assert "style_helper could not be read: HTTP 401" in caplog.text
    assert TOKEN not in caplog.text
    assert "secret-looking-value" not in caplog.text
    assert TOKEN not in repr(rig.reader)


def test_the_reader_logs_no_warning_of_its_own(caplog: pytest.LogCaptureFixture) -> None:
    rig = Rig(token=None)
    rig.read()
    assert not [record for record in caplog.records if record.levelno >= logging.WARNING]


def test_conforms_to_the_port(rig: Rig) -> None:
    reader: HelperReader = rig.reader
    assert reader is rig.reader
