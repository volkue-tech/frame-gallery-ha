"""One cached Core state read, never a network call to the television."""

from __future__ import annotations

import json
from ipaddress import ip_address

import pytest

from frame_gallery.observer.wake import WakeSample
from tests.support.net import FakeResolver, FakeResponse, connect_failure
from tests.unit.ha.test_client import TOKEN, Rig

ENTITY = "media_player.frame"


def response(**changes: object) -> FakeResponse:
    value = {"entity_id": ENTITY, "state": "on", "last_changed": "2026-10-18T21:00:00Z", **changes}
    body = json.dumps(value).encode()
    return FakeResponse(
        headers={"Content-Type": "application/json", "Content-Length": str(len(body))}, body=body
    )


def test_exact_cached_get_and_bound_no_tv_or_extra_permissions() -> None:
    rig = Rig()
    rig.transport.add(response())
    seen = rig.reader.read_wake_state(ENTITY, rig.deadline(2))
    assert isinstance(seen, WakeSample)
    assert seen.state == "on"
    request = rig.transport.calls[0].request
    assert request.target == "/core/api/states/media_player.frame"
    assert request.host == "supervisor"
    assert request.method == "GET"
    assert request.headers["Authorization"] == "Bearer " + TOKEN
    assert len(rig.transport.calls) == 1
    assert rig.transport.calls[0].exchange_timeout <= 2
    assert rig.transport.opened[0].closed


@pytest.mark.parametrize("entity", ["", "media_player../x", "remote.A", "input_text.frame"])
def test_bad_entity_never_loads_transport(entity: str) -> None:
    rig = Rig()
    assert rig.reader.read_wake_state(entity, rig.deadline()) is None
    assert rig.resolver.calls == []
    assert rig.transport.calls == []


@pytest.mark.parametrize("token", [None, "", "has space"])
def test_missing_token_makes_no_request(token: str | None) -> None:
    rig = Rig(token=token)
    assert rig.reader.read_wake_state(ENTITY, rig.deadline()) is None
    assert not rig.transport.calls


@pytest.mark.parametrize("status", [401, 403])
def test_auth_refusal_latches_no_further_requests(status: int) -> None:
    rig = Rig()
    rig.transport.add(FakeResponse(status=status), response())
    for _ in range(3):
        assert rig.reader.read_wake_state(ENTITY, rig.deadline()) is None
    assert len(rig.transport.calls) == 1


@pytest.mark.parametrize(
    "problem",
    [
        "wrong_entity",
        "malformed",
        "large",
        "missing",
        "redirect",
        "network",
        "public_dns",
        "timeout",
    ],
)
def test_bad_missing_redirect_or_failed_reads_return_no_authority(problem: str) -> None:
    rig = Rig()
    value = response(entity_id="media_player.other") if problem == "wrong_entity" else response()
    if problem == "malformed":
        value = FakeResponse(headers={"Content-Type": "application/json"}, body=b"{")
    elif problem == "large":
        value = FakeResponse(
            headers={"Content-Type": "application/json", "Content-Length": "70000"}
        )
    elif problem == "missing":
        value.status = 404
    elif problem == "redirect":
        value.status = 302
        value.headers = {"Location": "http://192.168.1.20/"}
    elif problem == "public_dns":
        rig = Rig(resolver=FakeResolver(default=(ip_address("93.184.216.34"),)))
    rig.transport.add(connect_failure() if problem == "network" else value)
    assert (
        rig.reader.read_wake_state(ENTITY, rig.deadline(0 if problem == "timeout" else 2)) is None
    )
    assert len(rig.transport.calls) <= 1
