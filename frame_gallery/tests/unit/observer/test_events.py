from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any

import pytest
from tests.unit.observer.test_backend import Rig as HostRig

from frame_gallery.errors import StateError
from frame_gallery.isolation.executor import IsolationFailure, JsonObject
from frame_gallery.observer import stream
from frame_gallery.observer.event_backend import EventBackend
from frame_gallery.observer.event_controller import EventController
from frame_gallery.observer.model import Action, Command, Evidence, Observation, Status
from frame_gallery.observer.stream import Change, EventPolicy, decode_event
from frame_gallery.store.artwork_bindings import BindingStore

DEVICE = "a" * 64
SEEN = Observation(Status.UNIDENTIFIED, DEVICE, "MY_OFFLINE", "b" * 64)
POLICY = EventPolicy("offline.mode", "offline.content", "offline.invalidate")


def envelope(body: object) -> str:
    return json.dumps({"event": "d2d_service_message", "data": json.dumps(body)})


def test_schema_and_production_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    assert EventPolicy.from_json(POLICY.to_json()) == POLICY
    assert stream.REVIEWED_POLICIES == {}
    assert stream.reviewed_policy(None) is None
    assert stream.reviewed_policy(DEVICE) is None
    monkeypatch.setattr(stream, "REVIEWED_POLICIES", {DEVICE: POLICY})
    assert stream.reviewed_policy(DEVICE) == POLICY
    assert stream.validate_device(DEVICE) == DEVICE
    with pytest.raises(ValueError, match="pinned"):
        stream.validate_device("bad")


@pytest.mark.parametrize(
    "value",
    [
        {},
        {"mode": 1, "content": "c", "invalidate": "i"},
        {"mode": "m", "content": 1, "invalidate": "i"},
        {"mode": "m", "content": "c", "invalidate": 1},
        {"mode": "m", "content": "m", "invalidate": "i"},
        {"mode": "bad name", "content": "c", "invalidate": "i"},
    ],
)
def test_bad_schema(value: JsonObject) -> None:
    with pytest.raises(ValueError, match="event schema"):
        EventPolicy.from_json(value)


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ({"event": POLICY.mode_event, "value": "on"}, Change("mode", "on")),
        ({"event": POLICY.mode_event, "value": "off"}, Change("mode", "off")),
        (
            {"event": POLICY.content_event, "content_id": "MY_OFFLINE"},
            Change("content", "MY_OFFLINE"),
        ),
        ({"event": POLICY.invalidation_event}, Change("invalidate")),
    ],
)
def test_strict_events(body: JsonObject, expected: Change) -> None:
    assert decode_event(envelope(body), POLICY) == expected
    assert Change.from_json(expected.to_json()) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "x" * (stream.MAX_FRAME + 1),
        '"' + "\u20ac" * 30000 + '"',
        "[]",
        "{}",
        '{"event":"d2d_service_message"}',
        '{"event":"d2d_service_message","data":"[]"}',
        envelope({"event": POLICY.content_event, "content_id": "../bad"}),
        envelope({"event": POLICY.mode_event, "value": "unknown"}),
        envelope({"event": POLICY.mode_event, "value": "on", "request_id": "old"}),
        envelope({"event": POLICY.mode_event, "value": "on", "id": "old"}),
        envelope({"event": POLICY.mode_event, "value": "on", "content_id": "MY_OTHER"}),
        envelope({"event": POLICY.content_event, "content_id": "MY_OFFLINE", "extra": True}),
        envelope({"event": POLICY.invalidation_event, "extra": True}),
        envelope({"event": "not-offered"}),
        "{bad json",
    ],
)
def test_bad_unknown_and_replayed_frames_fail_closed(raw: str) -> None:
    with pytest.raises(
        ValueError,
        match=r"event|JSON|json|duplicate|invalid|unexpected|missing|unrecognized|Expecting",
    ):
        decode_event(raw, POLICY)


@pytest.mark.parametrize(
    "value",
    [
        {},
        {"kind": "mode", "value": []},
        {"kind": "mode", "value": "unknown"},
        {"kind": "other", "value": ""},
    ],
)
def test_invalid_changes(value: JsonObject) -> None:
    with pytest.raises(ValueError, match="invalid event"):
        Change.from_json(value)


class Source:
    device_id: str | None = DEVICE
    failure: Exception | None = None
    reply = SEEN

    def __init__(self) -> None:
        self.request: JsonObject | Observation = {"host": "192.168.1.20"}
        self.request_error: Exception | None = None

    def session_request(self) -> JsonObject | Observation:
        if self.request_error is not None:
            raise self.request_error
        return self.request

    def accept_snapshot(self, raw: JsonObject) -> Observation:
        if self.failure:
            raise self.failure
        assert raw == {"synthetic": True}
        return self.reply

    def accept_slideshow(self, content_id: str) -> Observation:
        return Observation(Status.UNIDENTIFIED, DEVICE, content_id, None, Evidence.SLIDESHOW)


class Session:
    def __init__(self) -> None:
        self.starts: list[JsonObject] = []
        self.stops = 0
        self.queue: deque[tuple[JsonObject, float]] = deque()

    def start(self, payload: JsonObject) -> None:
        self.starts.append(payload)

    def poll(self) -> tuple[JsonObject, float] | None:
        return self.queue.popleft() if self.queue else None

    def stop(self) -> None:
        self.stops += 1


class Rig:
    def __init__(self) -> None:
        self.now = 10.0
        self.host, self.session = Source(), Session()
        self.backend = EventBackend(self.host, self.session, lambda: self.now, lambda _d: POLICY)

    def add(self, value: JsonObject, at: float = 10.0) -> None:
        self.session.queue.append((value, at))

    def baseline(self) -> None:
        self.add({"kind": "baseline", "observation": {"synthetic": True}})


def test_backend_no_profile_no_worker_and_request_refusal() -> None:
    rig = Rig()
    backend = EventBackend(rig.host, rig.session, lambda: 0)
    assert backend.start().status is Status.VALIDATION_REQUIRED
    assert not rig.session.starts
    rig.host.request = Observation(Status.NOT_AUTHORIZED)
    assert rig.backend.start().status is Status.NOT_AUTHORIZED
    assert not rig.session.starts
    rig.host.request = {"host": "192.168.1.20"}
    assert rig.backend.start().status is Status.CHECKING
    assert len(rig.session.starts) == 1
    assert rig.session.starts[0]["policy"] == POLICY.to_json()


def test_proof_is_not_renewed_by_duplicates_or_mode_on() -> None:
    rig = Rig()
    rig.baseline()
    assert rig.backend.update() == SEEN
    rig.now = 80
    for change in (Change("mode", "on"), Change("content", "MY_OFFLINE")):
        rig.add({"kind": "change", "change": change.to_json()}, 80)
    assert rig.backend.update() is None
    rig.now = 100
    assert rig.backend.update() == Observation(Status.PAUSED)
    rig.backend.stop()
    assert rig.backend.update() is None


@pytest.mark.parametrize(
    ("value", "status"),
    [
        ({"kind": "change", "change": Change("mode", "off").to_json()}, Status.TV_IN_USE),
        ({"kind": "change", "change": Change("content", "MY_OTHER").to_json()}, Status.PAUSED),
        ({"kind": "change", "change": Change("invalidate").to_json()}, Status.PAUSED),
        ({"kind": "end", "status": "not_authorized"}, Status.NOT_AUTHORIZED),
        ({"kind": "end", "status": "bogus"}, Status.UNAVAILABLE),
        ({"kind": "end", "status": []}, Status.UNAVAILABLE),
        ({"kind": "baseline", "observation": {}}, Status.UNAVAILABLE),
        ({"kind": "change", "change": []}, Status.UNAVAILABLE),
        ({"kind": "unknown"}, Status.UNAVAILABLE),
    ],
)
def test_backend_coalesces_and_fails_closed(value: JsonObject, status: Status) -> None:
    rig = Rig()
    rig.baseline()
    rig.add(value)
    assert rig.backend.update() == Observation(status)


@pytest.mark.parametrize(
    "value",
    [
        {"kind": "baseline", "observation": []},
        {"kind": "change", "change": Change("mode", "on").to_json()},
    ],
)
def test_event_before_proof(value: JsonObject) -> None:
    rig = Rig()
    rig.add(value)
    assert rig.backend.update() == Observation(Status.UNAVAILABLE)


@pytest.mark.parametrize("age", [-1.0, 90.0])
def test_queued_old_or_future_snapshot_not_made_fresh(age: float) -> None:
    rig = Rig()
    rig.now = 10 + age
    rig.baseline()
    assert rig.backend.update() == Observation(Status.PAUSED)


@pytest.mark.parametrize("error", [ValueError("bad"), StateError("bad"), OSError("bad")])
def test_bad_proof(error: Exception) -> None:
    rig = Rig()
    rig.host.failure = error
    rig.baseline()
    assert rig.backend.update() == Observation(Status.UNAVAILABLE)


def test_non_art_baseline_and_flood() -> None:
    rig = Rig()
    rig.host.reply = Observation(Status.TV_IN_USE)
    rig.baseline()
    assert rig.backend.update() == Observation(Status.TV_IN_USE)
    rig = Rig()
    rig.baseline()
    for _ in range(63):
        rig.add({"kind": "change", "change": Change("mode", "on").to_json()})
    assert rig.backend.update() == Observation(Status.UNAVAILABLE)


class ControllerRig:
    def __init__(self) -> None:
        self.rig = Rig()
        self.sent = 0
        self.code = 0
        self.stopped = False
        self.claimed: set[str] = set()
        self.published: list[Observation] = []
        self.controller = EventController(
            send=self.send,
            source=self.rig.backend,
            publish=self.publish,
            claim=self.claim,
            stopped=lambda: self.stopped,
        )

    def send(self) -> int:
        self.sent += 1
        return self.code

    def publish(self, observation: Observation) -> None:
        self.published.append(observation)

    def claim(self, command: Command) -> bool:
        if command.request_id in self.claimed:
            return False
        self.claimed.add(command.request_id)
        return True


def command(action: Action = Action.NEW_ARTWORK, key: str = "offline_123") -> Command:
    return Command(action, key, 0)


def test_controller_boot_refresh_no_network_and_explicit_one_session() -> None:
    r = ControllerRig()
    c = r.controller
    c.start()
    c.tick()
    c.command(command(Action.REFRESH_CURRENT))
    assert not r.sent
    assert not r.rig.session.starts
    assert c.command(command(key="offline_456"))
    assert len(r.rig.session.starts) == int(r.sent) == 1
    assert not c.command(command(key="offline_456"))
    r.rig.baseline()
    c.tick()
    assert r.published[-1] == SEEN
    c.command(command(Action.REFRESH_CURRENT, "offline_789"))
    assert len(r.rig.session.starts) == int(r.sent) == 1
    r.rig.add({"kind": "change", "change": Change("mode", "off").to_json()})
    c.tick()
    c.tick()
    c.command(command(Action.REFRESH_CURRENT, "offline_999"))
    assert len(r.rig.session.starts) == 1
    c.stop()
    assert r.published[-1].status is Status.PAUSED


def test_controller_failure_and_stop_races() -> None:
    r = ControllerRig()
    r.code = 1
    r.controller.command(command())
    assert not r.rig.session.starts
    r = ControllerRig()
    r.stopped = True
    assert not r.controller.command(command())
    r.controller.tick()
    r = ControllerRig()

    def publish(_seen: Observation) -> None:
        r.stopped = True

    r.controller._publish = publish
    assert not r.controller.command(command())
    assert r.sent == 0
    r = ControllerRig()

    def send() -> int:
        r.stopped = True
        return 0

    r.controller._send = send
    r.controller.command(command())
    assert not r.rig.session.starts


def test_controller_unapproved_profile_stays_closed() -> None:
    r = ControllerRig()
    r.controller._source = EventBackend(r.rig.host, r.rig.session, lambda: 0)
    r.controller.command(command())
    assert r.published[-1].status is Status.VALIDATION_REQUIRED
    assert not r.rig.session.starts


def test_controller_never_delivers_with_unreaped_session(monkeypatch: pytest.MonkeyPatch) -> None:
    r = ControllerRig()

    def refuse() -> None:
        raise IsolationFailure("still active")

    monkeypatch.setattr(r.rig.session, "stop", refuse)
    with pytest.raises(IsolationFailure, match="still active"):
        r.controller.command(command())
    assert r.sent == 0


@pytest.mark.parametrize("error", [OSError("bad"), StateError("bad"), ValueError("bad")])
def test_bad_local_request_does_not_open_session(error: Exception) -> None:
    r = Rig()
    r.host.request_error = error
    assert r.backend.start().status is Status.UNAVAILABLE
    assert not r.session.starts


def test_event_baseline_real_binding_port_without_periodic_worker(tmp_path: Path) -> None:
    host = HostRig(tmp_path)
    history = host.data / "state" / "history.json"
    history.write_bytes(b"preserve history")
    session = Session()
    backend = EventBackend(host.observer, session, lambda: 10, lambda _d: POLICY)
    assert backend.start().status is Status.CHECKING
    assert len(session.starts) == 1
    session.queue.append(({"kind": "baseline", "observation": dict(host.executor.result)}, 10))
    seen = backend.update()
    assert seen is not None
    binding = BindingStore(host.data).resolve(seen)
    assert binding is not None
    assert binding.title == "Synthetic work"
    assert binding.artist == "Synthetic Artist"
    assert [name for name, _ in host.executor.calls] == ["verify_thumbnail"]
    session.queue.append(
        ({"kind": "change", "change": Change("content", "MY_OTHER").to_json()}, 10)
    )
    session.queue.append(({"kind": "change", "change": Change("content", "MY_TEST").to_json()}, 10))
    assert backend.update() == Observation(Status.PAUSED)
    backend.stop()
    assert backend.update() == Observation(Status.UNAVAILABLE)
    assert history.read_bytes() == b"preserve history"


PROBE_POLICY = EventPolicy("offline.mode", "offline.content", "offline.invalidate", "status", True)


def test_optional_probe_schema_and_exact_mode_field() -> None:
    assert EventPolicy.from_json(PROBE_POLICY.to_json()) == PROBE_POLICY
    assert set(POLICY.to_json()) == {"mode", "content", "invalidate"}
    assert decode_event(
        envelope({"event": POLICY.mode_event, "status": "on"}), PROBE_POLICY
    ) == Change("mode", "on")
    with pytest.raises(ValueError, match="fields"):
        decode_event(envelope({"event": POLICY.mode_event, "value": "on"}), PROBE_POLICY)
    with pytest.raises(ValueError, match="fields"):
        decode_event(envelope({"event": POLICY.mode_event, "status": "on"}), POLICY)


@pytest.mark.parametrize(
    "changes",
    [
        {"mode_field": "status"},
        {"current_id_once": True},
        {"mode_field": "invalid", "current_id_once": True},
        {"mode_field": [], "current_id_once": True},
        {"mode_field": "status", "current_id_once": 1},
    ],
)
def test_bad_optional_probe_policy(changes: JsonObject) -> None:
    with pytest.raises(ValueError, match="event schema"):
        EventPolicy.from_json({**POLICY.to_json(), **changes})


def test_direct_probe_policy_rejects_non_boolean() -> None:
    value: Any = 1
    with pytest.raises(ValueError, match="probe"):
        EventPolicy("m", "c", "i", "status", value)


@pytest.mark.parametrize(
    "raw",
    [
        '{"event":"bad","event":"d2d_service_message","data":"{}"}',
        envelope({"event": POLICY.mode_event, "status": "on"}).replace(
            '\\"status\\": \\"on\\"', '\\"status\\": \\"off\\", \\"status\\": \\"on\\"'
        ),
    ],
)
def test_duplicate_event_keys_rejected(raw: str) -> None:
    with pytest.raises(ValueError, match="duplicate"):
        decode_event(raw, PROBE_POLICY)


def probe_rig() -> Rig:
    rig = Rig()
    rig.backend = EventBackend(rig.host, rig.session, lambda: rig.now, lambda _d: PROBE_POLICY)
    assert rig.backend.start().status is Status.CHECKING
    rig.baseline()
    assert rig.backend.update() == SEEN
    return rig


@pytest.mark.parametrize("content_id", ["MY_OFFLINE", "MY_NEW", "MY_OLD"])
def test_query_clears_before_reply_and_bare_id_never_renews_proof(content_id: str) -> None:
    rig = probe_rig()
    rig.add({"kind": "querying"})
    assert rig.backend.update() == Observation(Status.CHECKING)
    assert rig.backend._baseline is None
    assert rig.backend._confirmed_at is None
    rig.now = 14
    rig.add({"kind": "current_id", "content_id": content_id}, 14)
    assert rig.backend.update() == Observation(Status.PAUSED)
    assert len(rig.session.starts) == 1


@pytest.mark.parametrize("at", [4.9, 11.0])
def test_stale_future_query_start_is_not_accepted(at: float) -> None:
    rig = probe_rig()
    rig.add({"kind": "querying"}, at)
    assert rig.backend.update() == Observation(Status.PAUSED)


def test_missing_result_expires_without_any_new_session() -> None:
    rig = probe_rig()
    rig.add({"kind": "querying"})
    assert rig.backend.update() == Observation(Status.CHECKING)
    rig.now = 14.9
    assert rig.backend.update() is None
    rig.now = 15
    assert rig.backend.update() == Observation(Status.PAUSED)
    assert len(rig.session.starts) == 1


@pytest.mark.parametrize(
    ("value", "at"),
    [
        ({"kind": "querying", "extra": True}, 10),
        ({"kind": "querying"}, 10),
        ({"kind": "current_id", "content_id": "../invalid"}, 10),
        ({"kind": "current_id", "content_id": None}, 10),
        ({"kind": "current_id", "content_id": "MY_NEW"}, 9),
        ({"kind": "current_id", "content_id": "MY_NEW"}, 11),
        ({"kind": "current_id"}, 10),
        ({"kind": "baseline", "observation": {"synthetic": True}}, 10),
        ({"kind": []}, 10),
    ],
)
def test_unexpected_pending_records_fail_closed(value: JsonObject, at: float) -> None:
    rig = probe_rig()
    rig.add({"kind": "querying"})
    assert rig.backend.update() == Observation(Status.CHECKING)
    rig.add(value, at)
    assert rig.backend.update() == Observation(Status.UNAVAILABLE)


def test_query_requires_policy_and_baseline() -> None:
    rig = Rig()
    rig.baseline()
    rig.add({"kind": "querying"})
    assert rig.backend.update() == Observation(Status.UNAVAILABLE)
    rig = probe_rig()
    rig.backend.stop()
    rig.add({"kind": "querying"})
    assert rig.backend.update() == Observation(Status.UNAVAILABLE)
    rig.add({"kind": "current_id", "content_id": "MY_NEW"})
    assert rig.backend.update() == Observation(Status.UNAVAILABLE)


def test_controller_keeps_only_bounded_pending_checking_alive() -> None:
    rig = ControllerRig()
    rig.rig.backend = EventBackend(
        rig.rig.host, rig.rig.session, lambda: rig.rig.now, lambda _d: PROBE_POLICY
    )
    rig.controller._source = rig.rig.backend
    rig.controller.command(command())
    rig.rig.baseline()
    rig.controller.tick()
    stops = rig.rig.session.stops
    rig.rig.add({"kind": "querying"})
    rig.controller.tick()
    assert rig.published[-1] == Observation(Status.CHECKING)
    assert rig.rig.session.stops == stops
    rig.rig.add({"kind": "current_id", "content_id": "MY_NEW"})
    rig.controller.tick()
    assert rig.published[-1] == Observation(Status.PAUSED)
    assert rig.rig.session.stops == stops + 1
    rig.controller.command(command(Action.REFRESH_CURRENT, "offline_refresh"))
    assert len(rig.rig.session.starts) == 1
    assert rig.sent == 1


def test_id_probe_never_re_verifies_or_updates_real_binding_history(tmp_path: Path) -> None:
    host = HostRig(tmp_path)
    history = host.data / "state" / "history.json"
    history.write_bytes(b"preserve history")
    session = Session()
    backend = EventBackend(host.observer, session, lambda: 10, lambda _d: PROBE_POLICY)
    backend.start()
    session.queue.append(({"kind": "baseline", "observation": dict(host.executor.result)}, 10))
    backend.update()
    bindings = host.data / "state" / "artwork-bindings.json"
    before = bindings.read_bytes()
    session.queue.append(({"kind": "querying"}, 10))
    assert backend.update() == Observation(Status.CHECKING)
    session.queue.append(({"kind": "current_id", "content_id": "MY_TEST"}, 10))
    assert backend.update() == Observation(Status.PAUSED)
    assert [name for name, _ in host.executor.calls] == ["verify_thumbnail"]
    assert bindings.read_bytes() == before
    assert history.read_bytes() == b"preserve history"
