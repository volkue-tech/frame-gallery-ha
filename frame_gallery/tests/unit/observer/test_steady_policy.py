"""New explicit consent, fresh real data and unchanged card/status semantics."""

from __future__ import annotations

from dataclasses import replace

import pytest
from tests.unit.config.test_options import _parse
from tests.unit.observer.test_events import SEEN, Rig

from frame_gallery.config.options import ConfigError
from frame_gallery.observer.event_backend import EventBackend
from frame_gallery.observer.model import Evidence, Observation, Status
from frame_gallery.observer.stream import SLIDESHOW_POLICY, Change, EventPolicy

POLICY = replace(SLIDESHOW_POLICY, state_refresh=True, art_only_refresh=True)


@pytest.mark.parametrize("flag", [None, False, True])
def test_new_flag_and_required_existing_setup(flag: bool | None) -> None:
    options = _parse(
        background_mode=True,
        resume_state_entity="remote.frame",
        current_state_refresh=True,
        confirm_current_artwork=flag,
    )
    assert options.confirm_current_artwork is (flag is True)
    assert not _parse(current_state_refresh=True, standby_resume=True).confirm_current_artwork


@pytest.mark.parametrize("missing", ["background", "entity", "bad_entity"])
def test_required_stop_setup_is_never_inferred(missing: str) -> None:
    with pytest.raises(ConfigError):
        _parse(
            background_mode=missing != "background",
            confirm_current_artwork=True,
            resume_state_entity=None
            if missing == "entity"
            else "sensor.watts"
            if missing == "bad_entity"
            else "remote.frame",
        )


@pytest.mark.parametrize("flag", [1, 0, "true", [], {}])
def test_no_boolean_coercion(flag: object) -> None:
    with pytest.raises(ConfigError):
        _parse(confirm_current_artwork=flag)


@pytest.mark.parametrize("flag", [1, None, "true"])
def test_internal_policy_is_not_coerced(flag: object) -> None:
    with pytest.raises(ValueError, match="Art-only"):
        EventPolicy.from_json({**POLICY.to_json(), "art_only_refresh": flag})  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="Art-only"):
        replace(POLICY, art_only_refresh=flag)  # type: ignore[arg-type]


def test_internal_policy_requires_state_refresh_and_roundtrips() -> None:
    assert EventPolicy.from_json(POLICY.to_json()) == POLICY
    with pytest.raises(ValueError, match="Art-only"):
        replace(POLICY, state_refresh=False)


def test_quiet_verified_ids_remain_fresh_and_menu_is_terminal_not_recovery() -> None:
    r = Rig()
    r.backend = EventBackend(r.host, r.session, lambda: r.now, lambda _d: POLICY, diagnostics=True)
    r.backend.start()
    r.baseline()
    assert r.backend.update() == SEEN
    for at in range(60, 3601, 60):
        r.now = at
        r.add({"kind": "current_state", "content_id": "MY_OFFLINE"}, at)
        seen = r.backend.update()
        assert seen is not None
        assert seen.evidence is Evidence.CURRENT_STATE
        assert r.backend.update() is None
    r.add({"kind": "change", "change": Change("invalidate").to_json()})
    assert r.backend.update() == Observation(Status.TV_IN_USE)
    assert r.backend._confirmed_at is None
    assert len(r.session.starts) == 1


def test_new_policy_preserves_complete_passive_slideshow_proof() -> None:
    r = Rig()
    r.backend = EventBackend(r.host, r.session, lambda: r.now, lambda _d: POLICY)
    r.backend.start()
    r.baseline()
    r.backend.update()
    for change in (
        Change("selected", "MY_OTHER"),
        Change("rotation", "MY_OTHER"),
        Change("mode", "on"),
    ):
        r.add({"kind": "change", "change": change.to_json()})
        seen = r.backend.update()
    assert seen is not None
    assert seen.evidence is Evidence.SLIDESHOW
    assert r.backend._fresh_s == 900


@pytest.mark.parametrize("problem", ["waiting", "replay", "gap", "no_baseline_time"])
def test_strict_parent_does_not_accept_waiting_or_stale_worker_proof(problem: str) -> None:
    r = Rig()
    r.backend = EventBackend(r.host, r.session, lambda: r.now, lambda _d: POLICY)
    r.backend.start()
    if problem == "waiting":
        r.add({"kind": "waiting_art"})
    else:
        r.baseline()
        r.backend.update()
        r.now = 100 if problem == "gap" else 10
        if problem == "no_baseline_time":
            r.backend._last_confirmation = None
        r.add({"kind": "current_state", "content_id": "MY_OFFLINE"}, r.now)
        if problem == "gap":
            r.backend.update()  # expiry is reported before draining a queued result
    assert r.backend.update() == Observation(Status.UNAVAILABLE)
