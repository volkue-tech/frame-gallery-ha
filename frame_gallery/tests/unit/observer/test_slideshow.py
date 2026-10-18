"""Authored replay of the observed lab4 shapes, NOT another hardware test."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from tests.unit.ha.test_current_artwork import OWNER, response
from tests.unit.ha.test_current_artwork import Rig as PublisherRig
from tests.unit.observer.test_backend import DEVICE, HOST
from tests.unit.observer.test_backend import Rig as HostRig
from tests.unit.observer.test_events import SEEN, Rig, Session, envelope

from frame_gallery.budget.deadline import Deadline
from frame_gallery.isolation.executor import JsonObject
from frame_gallery.observer.backend import HostObserver
from frame_gallery.observer.event_backend import EventBackend
from frame_gallery.observer.model import SLIDESHOW_FRESH_S, Evidence, Observation, Status
from frame_gallery.observer.slideshow import SlideshowSequence
from frame_gallery.observer.stream import SLIDESHOW_POLICY, Change, EventPolicy, decode_event
from frame_gallery.store.artwork_bindings import BindingStore


def selected(content_id: str = "MY_NEXT") -> JsonObject:
    return {
        "event": "image_selected",
        "content_id": content_id,
        "is_shown": "Yes",
        "matte_id": "none",
        "portrait_matte_id": "shadowbox_polar",
    }


def rotation(content_id: str = "MY_NEXT") -> JsonObject:
    return {
        "event": "auto_rotation_image_changed",
        "current_content_id": content_id,
        "type": "shuffleslideshow",
    }


def changes(content_id: str = "MY_NEXT") -> tuple[Change, ...]:
    return (Change("selected", content_id), Change("rotation", content_id), Change("mode", "on"))


def rig() -> Rig:
    r = Rig()
    r.backend = EventBackend(r.host, r.session, lambda: r.now, lambda _d: SLIDESHOW_POLICY)
    assert r.backend.start().status is Status.CHECKING
    r.baseline()
    assert r.backend.update() == SEEN
    return r


def add(r: Rig, change: Change, at: float) -> None:
    r.add({"kind": "change", "change": change.to_json()}, at)


def triple(r: Rig, content_id: str, at: float) -> Observation | None:
    r.now = at
    for change in changes(content_id):
        add(r, change, at)
    assert r.backend.update() == Observation(Status.CHECKING)
    return r.backend.update()


def test_exact_observed_contract_and_inert_policy_registry() -> None:
    assert EventPolicy.from_json(SLIDESHOW_POLICY.to_json()) == SLIDESHOW_POLICY
    for body, change in zip(
        (selected(), rotation(), {"event": "art_mode_changed", "status": "on"}),
        changes(),
        strict=True,
    ):
        assert decode_event(envelope(body), SLIDESHOW_POLICY) == change
    assert decode_event(
        envelope({"event": "art_mode_changed", "status": "nav"}), SLIDESHOW_POLICY
    ) == Change("invalidate")
    assert decode_event(
        envelope({"event": "art_mode_changed", "status": "off"}), SLIDESHOW_POLICY
    ) == Change("mode", "off")
    assert decode_event(envelope({"event": "go_to_standby"}), SLIDESHOW_POLICY) == Change("standby")


@pytest.mark.parametrize(
    "body",
    [
        {**selected(), "is_shown": "No"},
        {**selected(), "is_shown": True},
        {**selected(), "matte_id": None},
        {**selected(), "portrait_matte_id": "bad/path"},
        {**selected(), "content_id": "../bad"},
        {**selected(), "extra": True},
        {**selected(), "id": "old_reply"},
        {**rotation(), "request_id": "old_reply"},
        {**rotation(), "type": "slideshow"},
        {**rotation(), "current_content_id": 3},
        {"event": "image_selected", "content_id": "MY_NEXT"},
        {"event": "art_mode_changed", "status": "ON"},
        {"event": "art_mode_changed", "status": "on", "extra": True},
        {"event": "unknown"},
        {"event": "go_to_standby", "extra": True},
        {"event": "go_to_standby", "status": "off"},
        {"event": "go_to_standby", "id": "correlated-reply"},
    ],
)
def test_unobserved_or_ambiguous_shapes_never_confirm(body: dict[str, object]) -> None:
    with pytest.raises(ValueError, match=r"slideshow|event|correlated"):
        decode_event(envelope(body), SLIDESHOW_POLICY)


@pytest.mark.parametrize("value", [1, None, "yes"])
def test_policy_boolean_is_not_coerced(value: Any) -> None:
    with pytest.raises(ValueError, match="slideshow"):
        EventPolicy.from_json({**SLIDESHOW_POLICY.to_json(), "slideshow": value})
    with pytest.raises(ValueError, match="slideshow"):
        EventPolicy("m", "c", "i", slideshow=value)


@pytest.mark.parametrize(
    "kwargs", [{"mode_event": "other"}, {"mode_field": "value"}, {"current_id_once": True}]
)
def test_slideshow_cannot_be_arbitrary_names_or_enable_queries(kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="slideshow"):
        replace(SLIDESHOW_POLICY, **kwargs)


def test_listener_outlives_old_proof_and_accepts_repeated_ten_minute_cycles() -> None:
    r = rig()
    r.now = 100
    assert r.backend.update() == Observation(Status.CHECKING)
    assert r.backend.update() is None
    for at, content_id in [(610, "MY_NEXT"), (1210, "MY_THIRD"), (1810, "MY_NEXT")]:
        result = triple(r, content_id, at)
        assert result == Observation(
            Status.UNIDENTIFIED, DEVICE, content_id, None, Evidence.SLIDESHOW
        )
    assert len(r.session.starts) == 1
    r.now = 1810 + SLIDESHOW_FRESH_S
    assert r.backend.update() == Observation(Status.CHECKING)
    assert r.backend.update() is None
    assert triple(r, "MY_THIRD", r.now + 10) is not None
    assert len(r.session.starts) == 1


def test_same_id_triplet_mode_on_and_navigation_do_not_freshen() -> None:
    def confirmed(r: Rig) -> float | None:
        return r.backend._confirmed_at

    r = rig()
    add(r, Change("mode", "on"), 10)
    assert r.backend.update() is None
    assert confirmed(r) == 10
    assert triple(r, "MY_OFFLINE", 20) is None
    assert confirmed(r) is None
    assert triple(r, "MY_NEXT", 30) is not None
    assert confirmed(r) == 30
    add(r, Change("mode", "on"), 30)
    assert r.backend.update() is None
    assert confirmed(r) == 30
    add(r, Change("invalidate"), 30)
    assert r.backend.update() == Observation(Status.CHECKING)
    assert confirmed(r) is None
    assert triple(r, "MY_NEXT", 31) is None


@pytest.mark.parametrize(
    "sequence",
    [
        [Change("rotation", "MY_NEXT")],
        [Change("selected", "MY_NEXT"), Change("mode", "on")],
        [Change("selected", "MY_NEXT"), Change("rotation", "MY_OTHER")],
        [Change("selected", "MY_NEXT"), Change("selected", "MY_NEXT")],
        [
            Change("selected", "MY_NEXT"),
            Change("rotation", "MY_NEXT"),
            Change("rotation", "MY_NEXT"),
        ],
        [Change("content", "MY_NEXT")],
    ],
)
def test_bad_order_conflict_overlap_and_duplicates_fail_closed(sequence: list[Change]) -> None:
    state = SlideshowSequence("MY_OLD", 0)
    for change in sequence[:-1]:
        state.consume(change, 1, 1)
    with pytest.raises(ValueError, match="slideshow"):
        state.consume(sequence[-1], 1, 1)


def test_pending_timeout_nav_reset_and_stale_or_future_events() -> None:
    r = rig()
    add(r, Change("selected", "MY_NEXT"), 10)
    assert r.backend.update() == Observation(Status.CHECKING)
    r.now = 15
    assert r.backend.update() == Observation(Status.CHECKING)
    assert r.backend._slideshow is not None
    assert r.backend._slideshow.pending_at is None
    state = SlideshowSequence("MY_OLD", 0)
    state.consume(Change("selected", "MY_NEXT"), 1, 1)
    with pytest.raises(ValueError, match="expired"):
        state.consume(Change("rotation", "MY_NEXT"), 6, 6)
    state = SlideshowSequence("MY_OLD", 0)
    state.consume(Change("selected", "MY_NEXT"), 1, 1)
    state.consume(Change("invalidate"), 2, 2)
    assert state.pending_at is None
    for at, now in [(1, 1), (3, 2), (3, 8)]:
        with pytest.raises(ValueError, match="stale or future"):
            state.consume(Change("mode", "on"), at, now)


def test_mode_off_and_end_clear_without_reconnect() -> None:
    r = rig()
    add(r, Change("selected", "MY_NEXT"), 10)
    assert r.backend.update() == Observation(Status.CHECKING)
    add(r, Change("mode", "off"), 10)
    assert r.backend.update() == Observation(Status.TV_IN_USE)
    r.backend.stop()
    assert r.backend._slideshow is None
    assert len(r.session.starts) == 1


def test_exact_standby_clears_pending_caption_as_normal_pause() -> None:
    r = rig()
    add(r, Change("selected", "MY_NEXT"), 10)
    assert r.backend.update() == Observation(Status.CHECKING)
    add(r, Change("standby"), 10)
    assert r.backend.update() == Observation(Status.PAUSED)
    r.backend.stop()
    assert r.backend._slideshow is None
    assert len(r.session.starts) == 1


@pytest.mark.parametrize("change", [Change("selected", "MY_NEXT"), Change("rotation", "MY_NEXT")])
def test_slideshow_records_require_selected_policy(change: Change) -> None:
    r = Rig()
    r.baseline()
    add(r, change, 10)
    assert r.backend.update() == Observation(Status.UNAVAILABLE)


def test_known_device_mapping_supplies_artist_unknown_does_not_and_store_is_untouched(
    tmp_path: Path,
) -> None:
    host = HostRig(tmp_path)
    initial = host.observer.read()
    store = BindingStore(host.data)
    item = store.resolve(initial)
    from frame_gallery.store.artwork_bindings import Binding  # noqa: PLC0415

    assert isinstance(item, Binding)
    known = replace(
        item,
        content_id="MY_NEXT",
        title="Next work",
        artist="Next Artist",
        thumbnail_sha256="d" * 64,
    )
    store.remember(known)
    store.remember(replace(known, device_id="f" * 64, content_id="MY_OTHER_DEVICE"))
    state_path = host.data / "state" / "artwork-bindings.json"
    before = state_path.read_bytes()
    current = (host.data / "state" / "current.json").read_bytes()
    history = host.data / "state" / "history.json"
    history.write_bytes(b"unchanged")
    session = Session()
    now = [0.0]
    backend = EventBackend(host.observer, session, lambda: now[0], lambda _d: SLIDESHOW_POLICY)
    backend.start()
    session.queue.append(({"kind": "baseline", "observation": dict(host.executor.result)}, 0))
    backend.update()
    now[0] = 90
    assert backend.update() == Observation(Status.CHECKING)
    session.queue.append(
        ({"kind": "change", "change": Change("rotation", "MY_NEXT").to_json()}, now[0])
    )
    assert backend.update() == Observation(Status.CHECKING)
    assert store.resolve(Observation(Status.CHECKING)) is None
    for content_id, expected in [
        ("MY_NEXT", known),
        ("MY_UNKNOWN", None),
        ("MY_OTHER_DEVICE", None),
        ("MY_NEXT", known),
    ]:
        now[0] += 600
        for change in changes(content_id):
            session.queue.append(({"kind": "change", "change": change.to_json()}, now[0]))
        assert backend.update() == Observation(Status.CHECKING)
        seen = backend.update()
        assert seen is not None
        assert seen.evidence is Evidence.SLIDESHOW
        assert store.resolve(seen) == expected
        publisher = PublisherRig()
        publisher.transport.add(response({}, 404), response({}))
        assert publisher.client.publish(
            OWNER, seen, expected, Deadline.after(publisher.clock, 2, "test")
        )
        body = json.loads(publisher.transport.calls[-1].request.body or b"")
        assert body["attributes"]["confirmation_method"] == "slideshow_events"
        if expected is None:
            assert body["state"] == "unidentified"
            assert "artist" not in body["attributes"]
        else:
            assert body["state"] == "artwork"
            assert body["attributes"]["artist"] == "Next Artist"
    assert [name for name, _ in host.executor.calls] == ["observe", "verify_thumbnail"]
    assert state_path.read_bytes() == before
    assert (host.data / "state" / "current.json").read_bytes() == current
    assert history.read_bytes() == b"unchanged"


def test_mapper_requires_identity_and_snapshot_cannot_claim_event_proof(tmp_path: Path) -> None:
    h = HostRig(tmp_path)
    with pytest.raises(ValueError, match="identity"):
        h.observer.accept_slideshow("../bad")
    unpinned = HostObserver(h.executor, h.data, h.media, HOST)
    with pytest.raises(ValueError, match="identity"):
        unpinned.accept_slideshow("MY_NEXT")
    raw = Observation(Status.UNIDENTIFIED, DEVICE, "MY_NEXT", None, Evidence.SLIDESHOW).to_json()
    with pytest.raises(ValueError, match="snapshot"):
        h.observer.accept_snapshot(raw)


@pytest.mark.parametrize(
    "wrong",
    [
        Observation(Status.UNIDENTIFIED, "f" * 64, "MY_NEXT", None, Evidence.SLIDESHOW),
        Observation(Status.UNIDENTIFIED, DEVICE, "MY_OTHER", None, Evidence.SLIDESHOW),
        Observation(Status.UNIDENTIFIED, DEVICE, "MY_NEXT", "b" * 64),
    ],
)
def test_wrong_mapper_evidence_or_identity_refused(
    wrong: Observation, monkeypatch: pytest.MonkeyPatch
) -> None:
    r = rig()
    monkeypatch.setattr(r.host, "accept_slideshow", lambda _id: wrong)
    assert triple(r, "MY_NEXT", 20) == Observation(Status.UNAVAILABLE)


def test_event_observation_json_preserves_old_shape_and_marks_historical_digest() -> None:
    assert set(SEEN.to_json()) == {"status", "device_id", "content_id", "thumbnail_sha256"}
    event = Observation(Status.UNIDENTIFIED, DEVICE, "MY_NEXT", None, Evidence.SLIDESHOW)
    assert Observation.from_json(event.to_json()) == event
    bad_fields: list[dict[str, Any]] = [{"evidence": []}, {"evidence": "bad"}]
    for fields in bad_fields:
        with pytest.raises(ValueError, match=r"evidence|bad"):
            Observation.from_json({**event.to_json(), **fields})
    value: Any = "slideshow"
    with pytest.raises(ValueError, match="evidence"):
        Observation(Status.PAUSED, evidence=value)
    with pytest.raises(ValueError, match="identity"):
        Observation(Status.PAUSED, evidence=Evidence.SLIDESHOW)
    with pytest.raises(ValueError, match="identity"):
        Observation(Status.ARTWORK, DEVICE, "MY_NEXT", None, Evidence.SLIDESHOW)
