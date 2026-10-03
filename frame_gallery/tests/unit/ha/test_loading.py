"""D-176: one scoped timer completion, fail-safe on every error."""

from __future__ import annotations

import json
from ipaddress import IPv4Network, ip_address

import pytest

from frame_gallery.budget.deadline import Deadline
from frame_gallery.config.options import ConfigError, parse_options
from frame_gallery.config.vocabulary import BUILTIN_VOCABULARY
from frame_gallery.ha.client import SupervisorHelperReader
from tests.support.clock import FakeClock
from tests.support.net import FakeResolver, FakeResponse, FakeTransport, connect_failure

TIMER = "timer.frame_gallery_test_run"
TOKEN = "synthetic-loading-token-value"  # noqa: S105 - test-only


class Rig:
    def __init__(self, token: str | None = TOKEN, address: str = "172.30.32.2") -> None:
        self.clock = FakeClock()
        self.resolver = FakeResolver(default=(ip_address(address),), clock=self.clock)
        self.transport = FakeTransport(clock=self.clock)
        self.client = SupervisorHelperReader(
            token=token,
            resolver=self.resolver,
            transport=self.transport,
            networks=(IPv4Network("172.30.32.0/23"),),
        )

    def finish(self, timer: str | None = TIMER, seconds: float = 10) -> None:
        self.client.finish_loading(timer, Deadline.after(self.clock, seconds, "finish"))


def test_one_post_cancels_only_the_explicit_timer() -> None:
    rig = Rig()
    response = FakeResponse()
    rig.transport.add(response)
    rig.finish()
    (call,) = rig.transport.calls
    request = call.request
    assert (request.method, request.host, request.target) == (
        "POST",
        "supervisor",
        "/core/api/services/timer/cancel",
    )
    assert json.loads(request.body or b"") == {"entity_id": TIMER}
    assert request.headers["Authorization"] == f"Bearer {TOKEN}"
    assert request.headers["Content-Length"] == str(len(request.body or b""))
    assert rig.resolver.calls == [("supervisor", 80, 2.0)]
    assert call.exchange_timeout == 2.0
    assert response.closed


@pytest.mark.parametrize("timer", [None, "", "light.x", "timer.x,timer.y", "timer.é", "timer.x\n"])
def test_invalid_or_unset_timer_sends_nothing(timer: str | None) -> None:
    rig = Rig()
    rig.finish(timer)
    assert not rig.resolver.calls
    assert not rig.transport.calls


@pytest.mark.parametrize("token", [None, "", "with space", "bad\nheader"])
def test_missing_or_unsafe_token_sends_nothing(token: str | None) -> None:
    rig = Rig(token=token)
    rig.finish()
    assert not rig.resolver.calls
    assert not rig.transport.calls


@pytest.mark.parametrize("address", ["8.8.8.8", "10.0.0.9", "127.0.0.1", "169.254.1.2"])
def test_token_never_goes_to_an_external_or_unrelated_lan_address(address: str) -> None:
    rig = Rig(address=address)
    rig.finish()
    assert not rig.transport.calls


@pytest.mark.parametrize("status", [200, 301, 401, 403, 500])
def test_no_retry_redirect_or_response_body_is_used(
    status: int, caplog: pytest.LogCaptureFixture
) -> None:
    rig = Rig()
    response = FakeResponse(status=status, headers={"Location": "http://elsewhere.invalid/"})
    rig.transport.add(response)
    rig.finish()
    assert len(rig.transport.calls) == 1
    assert response.closed
    assert TOKEN not in caplog.text


def test_transport_failure_does_not_escape_or_retry() -> None:
    rig = Rig()
    rig.transport.add(connect_failure())
    rig.finish()
    assert len(rig.transport.calls) == 1


def test_expired_deadline_sends_nothing() -> None:
    rig = Rig()
    rig.finish(seconds=0)
    assert not rig.transport.calls


def test_short_deadline_clamps_resolution_and_exchange() -> None:
    rig = Rig()
    rig.transport.add(FakeResponse())
    rig.finish(seconds=0.25)
    assert rig.resolver.calls == [("supervisor", 80, 0.25)]
    assert rig.transport.calls[0].exchange_timeout == 0.25


@pytest.mark.parametrize("value", [True, "light.x", "timer.x,timer.y", "timer.X"])
def test_option_validation_rejects_other_targets(value: object) -> None:
    with pytest.raises(ConfigError, match="loading_timer"):
        parse_options(
            {"tv_host": "10.0.0.5", "loading_timer": value},
            vocabulary=BUILTIN_VOCABULARY,
            excluded_networks=(),
        )
