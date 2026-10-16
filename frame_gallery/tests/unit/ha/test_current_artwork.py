from __future__ import annotations

import json
from dataclasses import replace
from ipaddress import IPv4Network, ip_address

import pytest

from frame_gallery.budget.deadline import Deadline
from frame_gallery.ha.current_artwork import ENTITY_ID, OWNER_KEY, CurrentArtworkPublisher
from frame_gallery.observer.model import Observation, Status
from tests.support.clock import FakeClock
from tests.support.net import FakeResolver, FakeResponse, FakeTransport, connect_failure
from tests.unit.store.test_artwork_bindings import binding

OWNER = "c" * 64
TOKEN = "fake-observer-token-123456789"  # noqa: S105


def response(
    value: object, status: int = 200, *, headers: dict[str, str] | None = None
) -> FakeResponse:
    return FakeResponse(
        status=status,
        headers={"content-type": "application/json", **(headers or {})},
        body=json.dumps(value).encode(),
    )


class Rig:
    def __init__(self, token: str | None = TOKEN) -> None:
        self.clock = FakeClock()
        self.transport = FakeTransport(clock=self.clock)
        self.resolver = FakeResolver({"supervisor": (ip_address("172.30.32.2"),)})
        self.client = CurrentArtworkPublisher(
            token=token,
            resolver=self.resolver,
            transport=self.transport,
            networks=(IPv4Network("172.30.32.0/23"),),
        )

    def publish(self, value: Observation | None = None) -> bool:
        return self.client.publish(
            OWNER, value or Observation(Status.PAUSED), None, Deadline.after(self.clock, 2, "test")
        )


def test_publish_own_state_without_helper_and_remove_old_caption() -> None:
    rig = Rig()
    rig.transport.add(response({}, 404), response({}))
    assert rig.publish()
    get, post = [call.request for call in rig.transport.calls]
    assert get.target == post.target == "/core/api/states/" + ENTITY_ID
    assert (get.method, post.method) == ("GET", "POST")
    body = json.loads(post.body or b"")
    assert body["state"] == "paused"
    assert body["attributes"][OWNER_KEY] == OWNER
    assert "title" not in body["attributes"]
    assert "force_update" not in body
    assert "observed_at" not in body["attributes"]


def test_only_verified_association_supplies_metadata_and_escaped_display() -> None:
    rig = Rig()
    item = binding(title="[click](https://evil.invalid) <img>", artist="**Author**")
    seen = Observation(Status.UNIDENTIFIED, item.device_id, item.content_id, item.thumbnail_sha256)
    rig.transport.add(response({"attributes": {OWNER_KEY: OWNER}}), response({}))
    assert rig.client.publish(OWNER, seen, item, Deadline.after(rig.clock, 2, "test"))
    payload = json.loads(rig.transport.calls[-1].request.body or b"")
    assert payload["state"] == "artwork"
    attrs = payload["attributes"]
    assert attrs["title"] == item.title
    assert attrs["display_title"].startswith(r"\[click\]\(")
    assert "<img>" not in attrs["display_title"]
    assert attrs["display_source"] == item.source
    with pytest.raises(ValueError, match="caption does not match"):
        rig.client.publish(
            OWNER, replace(seen, content_id="MY_OTHER"), item, Deadline.after(rig.clock, 2, "test")
        )


def test_unknown_artwork_cannot_keep_stale_caption() -> None:
    rig = Rig()
    rig.transport.add(response({}, 404), response({}))
    assert rig.publish(Observation(Status.ARTWORK, "a" * 64, "MY_F1", "b" * 64))
    assert json.loads(rig.transport.calls[-1].request.body or b"")["state"] == "unidentified"


@pytest.mark.parametrize("attrs", [None, {}, {OWNER_KEY: "someone-else"}])
def test_existing_unowned_entity_is_not_overwritten(attrs: object) -> None:
    rig = Rig()
    rig.transport.add(response({"attributes": attrs}))
    assert not rig.publish()
    assert len(rig.transport.calls) == 1


@pytest.mark.parametrize("token", [None, "", "bad\nvalue"])
def test_no_invalid_auth_probe(token: str | None) -> None:
    rig = Rig(token)
    assert not rig.publish()
    assert not rig.transport.calls


@pytest.mark.parametrize("code", [401, 403])
def test_authentication_failure_disables_later_attempts(code: int) -> None:
    rig = Rig()
    before = rig.client.authorization_refused
    assert before is False
    rig.transport.add(response({}, code))
    assert not rig.publish()
    after = rig.client.authorization_refused
    assert after is True
    assert not rig.publish()
    assert len(rig.transport.calls) == 1


@pytest.mark.parametrize(
    "bad",
    [
        response({}, 302),
        response({}, 500),
        response([]),
        FakeResponse(body=b"{", headers={"content-type": "application/json"}),
        response({}, headers={"content-type": "text/html"}),
        response({}, headers={"content-encoding": "gzip"}),
        connect_failure(),
    ],
)
def test_bounded_unexpected_responses_fail_closed(bad: object) -> None:
    rig = Rig()
    rig.transport.add(bad)  # type: ignore[arg-type]
    assert not rig.publish()


def test_owner_is_validated_before_any_request() -> None:
    rig = Rig()
    with pytest.raises(ValueError, match="invalid state owner"):
        rig.client.publish(
            "bad", Observation(Status.PAUSED), None, Deadline.after(rig.clock, 2, "test")
        )
    assert not rig.transport.calls
