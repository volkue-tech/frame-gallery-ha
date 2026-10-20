"""Fresh same-socket state proof, not fake renewal of the last delivered work."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from tests.support.clock import FakeClock
from tests.unit.ha.test_current_artwork import OWNER, response
from tests.unit.ha.test_current_artwork import Rig as PublisherRig
from tests.unit.observer.test_backend import HOST
from tests.unit.observer.test_backend import Rig as HostRig
from tests.unit.observer.test_events import DEVICE, SEEN, Rig
from tests.unit.store.test_delivery_associations import item

from frame_gallery.budget.deadline import Deadline
from frame_gallery.observer.backend import HostObserver
from frame_gallery.observer.event_backend import EventBackend
from frame_gallery.observer.event_controller import EventController
from frame_gallery.observer.model import Action, Command, Evidence, Observation, Status
from frame_gallery.observer.stream import SLIDESHOW_POLICY, Change, EventPolicy
from frame_gallery.store.artwork_bindings import BindingStore
from frame_gallery.store.delivery_associations import DeliveryAssociations
from frame_gallery.tv.port import target_fingerprint

POLICY = replace(SLIDESHOW_POLICY, state_refresh=True)


def rig() -> Rig:
    r = Rig()
    r.backend = EventBackend(r.host, r.session, lambda: r.now, lambda _d: POLICY)
    assert r.backend.start().status is Status.CHECKING
    r.baseline()
    assert r.backend.update() == SEEN
    return r


def test_same_id_after_expiry_and_repeated_menu_cycles_recovers_without_start() -> None:
    r = rig()
    for at, identity in [(110, "MY_OFFLINE"), (180, "MY_OTHER"), (240, "MY_OFFLINE")]:
        r.now = at
        r.add({"kind": "state_checking"}, at)
        assert r.backend.update() == Observation(Status.CHECKING)
        r.add({"kind": "current_state", "content_id": identity}, at)
        assert r.backend.update() == Observation(
            Status.UNIDENTIFIED, DEVICE, identity, None, Evidence.CURRENT_STATE
        )
    assert len(r.session.starts) == 1
    r.now = 330
    assert r.backend.update() == Observation(Status.CHECKING)


@pytest.mark.parametrize(
    ("record", "at"),
    [
        ({"kind": "current_state", "content_id": "../bad"}, 10),
        ({"kind": "current_state", "content_id": None}, 10),
        ({"kind": "current_state"}, 10),
        ({"kind": "current_state", "content_id": "MY_OFFLINE", "extra": True}, 10),
        ({"kind": "state_checking", "extra": True}, 10),
        ({"kind": "current_state", "content_id": "MY_OFFLINE"}, 11),
        ({"kind": "current_state", "content_id": "MY_OFFLINE"}, -81),
    ],
)
def test_untrusted_or_stale_records_never_publish(record: dict[str, object], at: float) -> None:
    r = rig()
    r.add(record, at)  # type: ignore[arg-type]
    assert r.backend.update() == Observation(Status.UNAVAILABLE)


def test_default_policy_cannot_accept_new_state_records_and_baseline_required() -> None:
    r = Rig()
    r.backend.start()
    r.add({"kind": "state_checking"})
    assert r.backend.update() == Observation(Status.UNAVAILABLE)
    r = rig()
    r.backend._baseline = None
    r.add({"kind": "current_state", "content_id": "MY_OFFLINE"})
    assert r.backend.update() == Observation(Status.UNAVAILABLE)


@pytest.mark.parametrize("wrong", ["device", "content", "evidence"])
def test_lookup_must_keep_device_content_and_evidence(
    wrong: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    r = rig()
    seen = Observation(Status.UNIDENTIFIED, DEVICE, "MY_OFFLINE", None, Evidence.CURRENT_STATE)
    if wrong == "device":
        seen = replace(seen, device_id="f" * 64)
    elif wrong == "content":
        seen = replace(seen, content_id="MY_WRONG")
    else:
        seen = replace(seen, evidence=Evidence.SLIDESHOW)
    monkeypatch.setattr(r.host, "accept_current_state", lambda _id: seen)
    r.add({"kind": "current_state", "content_id": "MY_OFFLINE"})
    assert r.backend.update() == Observation(Status.UNAVAILABLE)


def test_duplicate_invalidation_does_not_republish_or_reconnect() -> None:
    r = rig()
    r.add({"kind": "state_checking"})
    assert r.backend.update() == Observation(Status.CHECKING)
    r.add({"kind": "state_checking"})
    assert r.backend.update() is None
    assert len(r.session.starts) == 1


def test_notifications_are_only_hints_in_refresh_mode_never_a_false_proof() -> None:
    r = rig()
    for change in (
        Change("invalidate"),
        Change("selected", "MY_NEW"),
        Change("rotation", "MY_NEW"),
        Change("mode", "on"),
    ):
        r.add({"kind": "change", "change": change.to_json()})
        seen = r.backend.update()
        assert seen is None or seen.status is Status.CHECKING
    assert r.backend._confirmed_at is None
    r.add({"kind": "current_state", "content_id": "MY_NEW"})
    seen = r.backend.update()
    assert seen is not None
    assert seen.evidence is Evidence.CURRENT_STATE


@pytest.mark.parametrize("pending", [False, True])
def test_mode_off_clears_caption_but_opted_in_controller_keeps_one_session(pending: bool) -> None:
    r = Rig()
    backend = EventBackend(r.host, r.session, lambda: r.now, lambda _d: POLICY)
    publications: list[Observation] = []
    controller = EventController(
        send=lambda: 0,
        source=backend,
        publish=publications.append,
        claim=lambda _c: True,
        stopped=lambda: False,
        keep_tv_session=True,
    )
    assert controller.command(Command(Action.NEW_ARTWORK, "request_123", 0))
    if pending:
        r.add({"kind": "waiting_art"})
        controller.tick()
        assert publications[-1].status is Status.TV_IN_USE
        r.add({"kind": "state_checking"})
        controller.tick()
        r.add({"kind": "change", "change": Change("invalidate").to_json()})
        controller.tick()
        r.add({"kind": "change", "change": Change("mode", "on").to_json()})
        controller.tick()
    r.baseline()
    controller.tick()
    assert publications[-1] == SEEN
    r.add({"kind": "change", "change": Change("mode", "off").to_json()})
    controller.tick()
    assert publications[-1] == Observation(Status.TV_IN_USE)
    assert backend._confirmed_at is None
    r.add({"kind": "state_checking"})
    controller.tick()
    r.add({"kind": "current_state", "content_id": "MY_OFFLINE"})
    controller.tick()
    assert publications[-1].evidence is Evidence.CURRENT_STATE
    assert len(r.session.starts) == 1
    r.add({"kind": "change", "change": Change("standby").to_json()})
    controller.tick()
    assert publications[-1].status is Status.PAUSED
    assert not controller._active


def test_waiting_art_is_not_authorized_by_the_default_event_only_policy() -> None:
    r = Rig()
    r.backend.start()
    r.add({"kind": "waiting_art"})
    assert r.backend.update() == Observation(Status.UNAVAILABLE)


def test_opted_in_policy_still_requires_consumed_exact_delivery_grant(tmp_path: Path) -> None:
    h = HostRig(tmp_path)
    observer = HostObserver(h.executor, h.data, h.media, HOST, current_state_refresh=True)
    assert observer.event_policy(DEVICE) is None
    before = observer.delivery_snapshot()
    association = item(
        device_id=DEVICE, content_id="MY_TEST", target_sha256=target_fingerprint(HOST)
    )
    DeliveryAssociations(h.data).remember(association, Deadline.after(FakeClock(), 5, "test"))
    h.record.update(tv_device_id=DEVICE, sha256=association.jpeg_sha256)
    h.save()
    assert observer.after_delivery(before)
    assert observer.event_policy(DEVICE) == POLICY
    assert observer.event_policy(DEVICE) is None
    assert not h.executor.calls


@pytest.mark.parametrize("known", [True, False])
def test_fresh_state_uses_only_same_device_known_archive_and_unchanged_card_shape(
    tmp_path: Path, known: bool
) -> None:
    h = HostRig(tmp_path)
    association = item(device_id=h.observer.device_id or "a" * 64, content_id="MY_TEST")
    DeliveryAssociations(h.data).remember(association, Deadline.after(FakeClock(), 5, "test"))
    seen = h.observer.accept_current_state("MY_TEST" if known else "MY_UNKNOWN")
    assert Observation.from_json(seen.to_json()) == seen
    assert seen.evidence is Evidence.CURRENT_STATE
    mapped = BindingStore(h.data).resolve(seen)
    assert (mapped is not None) is known
    p = PublisherRig()
    p.transport.add(response({}, 404), response({}))
    assert p.client.publish(OWNER, seen, mapped, Deadline.after(p.clock, 2, "test"))
    body = json.loads(p.transport.calls[-1].request.body or b"")
    assert body["state"] == ("artwork" if known else "unidentified")
    assert body["attributes"]["confirmation_method"] == "current_state_read"
    assert body["attributes"]["confirmation_max_age"] == 90
    assert ("title" in body["attributes"]) is known
    assert not h.executor.calls


@pytest.mark.parametrize("value", [None, 0, "true", []])
def test_refresh_policy_is_not_coerced(value: object) -> None:
    with pytest.raises(ValueError, match="state refresh"):
        EventPolicy.from_json({**POLICY.to_json(), "state_refresh": value})  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="state refresh"):
        replace(SLIDESHOW_POLICY, state_refresh=value)  # type: ignore[arg-type]


def test_refresh_cannot_be_attached_to_an_arbitrary_non_slideshow_policy() -> None:
    with pytest.raises(ValueError, match="state refresh"):
        EventPolicy("m", "c", "i", state_refresh=True)
