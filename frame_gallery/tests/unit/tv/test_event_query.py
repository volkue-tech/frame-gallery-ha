"""Pure offline one-shot request tests; no socket is ever opened here."""

from __future__ import annotations

import json
from typing import Any, cast

import pytest

from frame_gallery.observer.stream import MAX_EVENTS, QUERY_S, EventPolicy
from frame_gallery.tv.event_frames import FrameBounds, SessionClosed
from frame_gallery.tv.event_query import current_id_once
from tests.unit.tv.test_event_frames import Connection

POLICY = EventPolicy("offline.mode", "offline.content", "offline.invalidate", "status", True)
NONCE = "a" * 32


def envelope(value: object) -> str:
    return json.dumps({"event": "d2d_service_message", "data": json.dumps(value)})


def reply(**changes: Any) -> str:
    return envelope(
        {"event": "get_current_artwork", "request_id": NONCE, "content_id": "MY_NEW", **changes}
    )


class Rig:
    def __init__(self) -> None:
        self.now = 10.0
        self.cancel = False
        self.connection: Any = cast(Any, Connection())
        self.sent: list[str] = []
        self.connection.send = self.sent.append
        self.responses: list[Any] = [reply()]
        self.connection.recv = self.receive
        self.bounds = FrameBounds(self.connection, lambda: self.now, lambda: self.cancel, 0)
        self.bounds.passive = True

    def receive(self) -> Any:
        response = self.responses.pop(0)
        if callable(response):
            return response()
        return response

    def query(self, policy: EventPolicy = POLICY, nonce: str = NONCE) -> str:
        return current_id_once(self.connection, self.bounds, policy, nonce, TimeoutError)


@pytest.mark.parametrize(
    "value",
    [
        reply(),
        reply(id=NONCE),
        envelope({"event": "get_current_artwork", "id": NONCE, "content_id": "MY_NEW"}),
    ],
)
def test_one_correlated_reply_on_existing_connection(value: str) -> None:
    rig = Rig()
    rig.responses = [value]
    assert rig.query() == "MY_NEW"
    assert len(rig.sent) == 1
    sent = json.loads(rig.sent[0])
    assert sent["method"] == "ms.channel.emit"
    assert sent["params"]["event"] == "art_app_request"
    assert sent["params"]["to"] == "host"
    assert json.loads(sent["params"]["data"]) == {
        "request": "get_current_artwork",
        "id": NONCE,
        "request_id": NONCE,
    }
    with pytest.raises(ValueError, match="once"):
        rig.query()
    assert len(rig.sent) == 1


@pytest.mark.parametrize("setup", ["disabled", "nonce", "transport", "not_passive", "cancel"])
def test_invalid_or_cancelled_request_never_sends(setup: str) -> None:
    rig = Rig()
    policy, nonce = POLICY, NONCE
    if setup == "disabled":
        policy = EventPolicy("m", "c", "i")
    elif setup == "nonce":
        nonce = "invalid"
    elif setup == "transport":
        rig.bounds.connection = Connection()
    elif setup == "not_passive":
        rig.bounds.passive = False
        rig.now = 0
    else:
        rig.cancel = True
    with pytest.raises((ValueError, SessionClosed)):
        rig.query(policy, nonce)
    assert rig.sent == []


@pytest.mark.parametrize(
    "body",
    [
        {"request_id": "b" * 32},
        {"id": "b" * 32},
        {"event": "error"},
        {"event": "not-current"},
        {"content_id": "../bad"},
        {"content_id": None},
        {"unexpected": True},
    ],
)
def test_unmatched_error_or_invalid_reply_fails_without_retry(body: dict[str, Any]) -> None:
    rig = Rig()
    rig.responses = [reply(**body)]
    with pytest.raises(ValueError, match=r"unexpected|invalid"):
        rig.query()
    assert len(rig.sent) == 1


@pytest.mark.parametrize(
    "raw",
    [
        "",
        None,
        b"binary",
        "{}",
        reply(request_id=None),
        '{"event":"d2d_service_message","data":"{\\"event\\":\\"x\\",\\"event\\":\\"y\\"}"}',
    ],
)
def test_bad_frames_and_duplicate_keys_never_create_an_id(raw: Any) -> None:
    rig = Rig()
    rig.responses = [raw]
    with pytest.raises(ValueError, match=r"connection|event|duplicate"):
        rig.query()
    assert len(rig.sent) == 1


@pytest.mark.parametrize(
    "value",
    [
        {"event": POLICY.mode_event, "status": "off"},
        {"event": POLICY.content_event, "content_id": "MY_OTHER"},
        {"event": POLICY.invalidation_event},
    ],
)
def test_mutation_or_off_while_pending_aborts(value: dict[str, Any]) -> None:
    rig = Rig()
    rig.responses = [envelope(value), reply()]
    with pytest.raises(SessionClosed):
        rig.query()
    assert len(rig.sent) == 1
    assert len(rig.responses) == 1


def test_duplicates_do_not_repeat_request_or_extend_deadline() -> None:
    rig = Rig()
    rig.responses = [envelope({"event": POLICY.mode_event, "status": "on"})] * 3 + [reply()]
    assert rig.query() == "MY_NEW"
    assert len(rig.sent) == 1
    assert rig.bounds._query_until == 10 + QUERY_S


def test_frame_flood_is_bounded_even_with_frozen_clock() -> None:
    rig = Rig()
    rig.responses = [envelope({"event": POLICY.mode_event, "status": "on"})] * (MAX_EVENTS + 1)
    with pytest.raises(ValueError, match="frame limit"):
        rig.query()
    assert len(rig.sent) == 1


def test_idle_timeout_does_not_resend_or_renew_deadline() -> None:
    rig = Rig()

    def timeout() -> str:
        rig.now += 0.5
        raise TimeoutError("synthetic")

    rig.responses = [timeout] * 20
    with pytest.raises(ValueError, match="query deadline"):
        rig.query()
    assert len(rig.sent) == 1
    assert rig.now == 10 + QUERY_S


@pytest.mark.parametrize("mutate", ["cancel", "late"])
def test_late_reply_or_cancellation_cannot_escape_post_receive_check(mutate: str) -> None:
    rig = Rig()

    def receive() -> str:
        if mutate == "cancel":
            rig.cancel = True
        else:
            rig.now += QUERY_S
        return reply()

    rig.responses = [receive]
    with pytest.raises((SessionClosed, ValueError)):
        rig.query()
    assert len(rig.sent) == 1


def test_send_failure_is_consumed_and_cannot_retry() -> None:
    rig = Rig()

    def refused(_raw: str) -> None:
        raise OSError("synthetic private data")

    rig.connection.send = refused
    with pytest.raises(OSError, match="synthetic"):
        rig.query()
    with pytest.raises(ValueError, match="once"):
        rig.query()


def test_pending_deadline_clamps_reads_but_not_bounded_cleanup() -> None:
    rig = Rig()
    rig.bounds.begin_query()
    rig.now += QUERY_S - 0.01
    assert rig.bounds.read(1) == b"x"
    assert 0 < rig.connection.timeouts[-1] <= 0.011
    rig.now += 0.02
    rig.bounds.close()
    assert rig.connection.shutdowns == 1
