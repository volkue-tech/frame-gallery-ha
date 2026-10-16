from __future__ import annotations

from dataclasses import replace

import pytest

from frame_gallery.isolation.executor import JsonObject
from frame_gallery.observer.controller import Controller, SafetyPermit
from frame_gallery.observer.model import Action, Command, Observation, Status
from frame_gallery.observer.service import serve


class Rig:
    def __init__(self, *, validated: bool = False) -> None:
        self.now = 0.0
        self.sends = 0
        self.reads = 0
        self.send_code = 0
        self.statuses: list[Observation] = []
        self.claimed: set[str] = set()
        self.reply = Observation(Status.UNIDENTIFIED, "a" * 64, "MY_F1", "b" * 64)
        self.controller = Controller(
            send=self.send,
            observe=self.read,
            publish=self.statuses.append,
            now=lambda: self.now,
            claim=self.claim,
            permit=SafetyPermit(validated),
        )

    def send(self) -> int:
        self.sends += 1
        return self.send_code

    def read(self) -> Observation:
        self.reads += 1
        return self.reply

    def claim(self, command: Command) -> bool:
        if command.request_id in self.claimed:
            return False
        self.claimed.add(command.request_id)
        return True


def command(action: Action = Action.NEW_ARTWORK, key: str = "request_123") -> Command:
    return Command(action, key, 0.0)


@pytest.mark.parametrize("validated", [False, True])
def test_boot_and_idle_never_contact_tv(validated: bool) -> None:
    rig = Rig(validated=validated)
    rig.controller.start()
    for _ in range(10):
        rig.now += 60
        rig.controller.tick()
    assert rig.sends == rig.reads == 0
    assert rig.statuses[-1].status is (Status.PAUSED if validated else Status.VALIDATION_REQUIRED)


def test_default_has_no_policy_and_cannot_be_enabled_by_refresh() -> None:
    rig = Rig()
    rig.controller.command(command(Action.REFRESH_CURRENT))
    rig.controller.command(command(key="request_456"))
    assert rig.sends == 1
    assert rig.reads == 0
    assert rig.statuses[-1].status is Status.VALIDATION_REQUIRED


def test_explicit_send_arms_only_after_success_and_deduplicates() -> None:
    rig = Rig(validated=True)
    assert rig.controller.command(command())
    assert not rig.controller.command(command())
    assert rig.sends == rig.reads == 1
    rig.controller.tick()
    assert rig.reads == 1
    rig.now = 30
    rig.controller.tick()
    assert rig.reads == 2
    rig.controller.command(command(Action.REFRESH_CURRENT, "refresh_123"))
    assert rig.reads == 3
    assert rig.sends == 1
    rig.controller.stop()
    rig.now = 100
    rig.controller.tick()
    assert rig.reads == 3


@pytest.mark.parametrize(
    "status",
    [
        Status.PAUSED,
        Status.UNAVAILABLE,
        Status.NOT_AUTHORIZED,
        Status.CHECKING,
        Status.VALIDATION_REQUIRED,
        Status.TV_IN_USE,
    ],
)
def test_uncertain_or_off_tv_disarms_without_reconnect(status: Status) -> None:
    rig = Rig(validated=True)
    rig.reply = Observation(status)
    rig.controller.command(command())
    for _ in range(3):
        rig.now += 300
        rig.controller.tick()
    rig.controller.command(command(Action.REFRESH_CURRENT, "refresh_123"))
    assert rig.reads == 1
    assert rig.sends == 1


def test_failed_send_never_arms_reads() -> None:
    rig = Rig(validated=True)
    rig.send_code = 70
    rig.controller.command(command())
    assert rig.reads == 0


def test_experimental_permit_is_not_a_no_wake_validation() -> None:
    rig = Rig()
    permit = SafetyPermit(experimental=True)
    assert permit.enabled
    assert not permit.validated
    controller = Controller(
        send=rig.send,
        observe=rig.read,
        publish=rig.statuses.append,
        now=lambda: rig.now,
        claim=rig.claim,
        permit=permit,
    )
    controller.start()
    controller.command(command(Action.REFRESH_CURRENT))
    rig.now = 120
    controller.tick()
    assert rig.reads == rig.sends == 0
    controller.command(command(key="request_456"))
    assert rig.reads == rig.sends == 1
    rig.reply = Observation(Status.UNAVAILABLE)
    rig.now += 30
    controller.tick()
    assert rig.reads == 2
    rig.now += 300
    controller.tick()
    controller.command(command(Action.REFRESH_CURRENT, "refresh_456"))
    assert rig.reads == 2


def test_stop_during_status_publication_cannot_send_or_read() -> None:
    rig = Rig(validated=True)
    stopped = False

    def publish(_observation: Observation) -> None:
        nonlocal stopped
        stopped = True

    controller = Controller(
        send=rig.send,
        observe=rig.read,
        publish=publish,
        now=lambda: rig.now,
        claim=rig.claim,
        permit=SafetyPermit(True),
        stopped=lambda: stopped,
    )
    assert not controller.command(command())
    controller.tick()
    assert not controller.command(command(key="request_456"))
    assert rig.sends == rig.reads == 0
    assert rig.claimed == {"request_123"}


def test_command_contract() -> None:
    data: JsonObject = {"command": "new_artwork", "request_id": "request_123", "issued_at": 42}
    assert Command.from_json(data) == Command(Action.NEW_ARTWORK, "request_123", 42.0)
    assert Command.from_json(dict(data, command="refresh_current")).action is Action.REFRESH_CURRENT


@pytest.mark.parametrize(
    "change",
    [
        {"command": "shell"},
        {"command": 4},
        {"request_id": "x"},
        {"request_id": "x" * 65},
        {"request_id": 4},
        {"issued_at": True},
        {"issued_at": "now"},
        {"issued_at": float("inf")},
        {"issued_at": float("nan")},
        {"issued_at": 10**400},
        {"issued_at": -1},
        {"extra": 1},
    ],
)
def test_invalid_commands_are_not_executable(change: JsonObject) -> None:
    data: JsonObject = {"command": "new_artwork", "request_id": "request_123", "issued_at": 42}
    with pytest.raises(ValueError, match=r"invalid|valid Action"):
        Command.from_json(dict(data, **change))


def test_observation_round_trip_and_validation() -> None:
    for status in Status:
        if status not in (Status.ARTWORK, Status.UNIDENTIFIED):
            assert Observation.from_json(Observation(status).to_json()) == Observation(status)
            with pytest.raises(ValueError, match="non-artwork observation"):
                Observation(status, "a" * 64)
    original = Observation(Status.ARTWORK, "a" * 64, "MY_F1", "b" * 64)
    assert Observation.from_json(original.to_json()) == original
    for change in [
        {"device_id": None},
        {"device_id": "z" * 64},
        {"content_id": None},
        {"content_id": "../x"},
        {"thumbnail_sha256": None},
        {"thumbnail_sha256": "bad"},
    ]:
        with pytest.raises(ValueError, match="invalid observed artwork identity"):
            replace(original, **change)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "value",
    [
        {},
        {"status": "paused", "extra": 1},
        {"status": 3, "device_id": None, "content_id": None, "thumbnail_sha256": None},
        {"status": "paused", "device_id": 4, "content_id": None, "thumbnail_sha256": None},
    ],
)
def test_invalid_observation_payloads(value: JsonObject) -> None:
    with pytest.raises(ValueError, match="invalid observation"):
        Observation.from_json(value)


def test_service_uses_commands_and_stops_before_pending_command() -> None:
    rig = Rig()
    received = 0

    def receive(timeout: float) -> Command | None:
        nonlocal received
        assert timeout == 0.5
        received += 1
        return command(key=f"request_{received}") if received != 2 else None

    serve(rig.controller, receive, lambda: received >= 3)
    assert rig.sends == 1
    assert rig.statuses[-1].status is Status.PAUSED


def test_already_stopped_service_cleans_up_without_receiving() -> None:
    rig = Rig()

    def receive(_timeout: float) -> Command | None:
        pytest.fail("must not receive while stopping")

    serve(rig.controller, receive, lambda: True)
    assert rig.sends == rig.reads == 0
    assert rig.statuses[-1].status is Status.PAUSED
