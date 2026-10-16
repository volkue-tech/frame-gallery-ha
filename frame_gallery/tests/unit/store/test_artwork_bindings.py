from __future__ import annotations

import json
import os
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from frame_gallery.errors import StateError
from frame_gallery.observer.model import Action, Command, Observation, Status
from frame_gallery.store import artwork_bindings as module
from frame_gallery.store.artwork_bindings import Binding, BindingStore, ObserverLock


def binding(**changes: str) -> Binding:
    return replace(
        Binding(
            "a" * 64,
            "MY_F1",
            "b" * 64,
            "commons:123",
            "Title",
            "Artist",
            "commons",
            "https://example.invalid/art",
            "2026-10-16T12:00:00+00:00",
        ),
        **changes,
    )


def test_verified_mapping_survives_restart_and_checks_tv_id_and_thumbnail(tmp_path: Path) -> None:
    store = BindingStore(tmp_path)
    assert store.all() == ()
    assert len(store.owner()) == 64
    assert BindingStore(tmp_path).owner() == store.owner()
    item = binding()
    store.remember(item)
    observation = Observation(
        Status.UNIDENTIFIED, item.device_id, item.content_id, item.thumbnail_sha256
    )
    assert BindingStore(tmp_path).resolve(observation) == item
    for change in [
        {"device_id": "c" * 64},
        {"content_id": "MY_F2"},
        {"thumbnail_sha256": "d" * 64},
    ]:
        assert store.resolve(replace(observation, **change)) is None  # type: ignore[arg-type]
    assert store.resolve(Observation(Status.PAUSED)) is None
    store.remember(replace(item, title="Updated"))
    assert len(store.all()) == 1
    assert store.all()[0].title == "Updated"


def test_bindings_evict_oldest_but_never_change_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(module, "MAX_BINDINGS", 2)
    store = BindingStore(tmp_path)
    store.remember(binding())
    state = tmp_path / "state"
    (state / "history.json").write_bytes(b"preserve")
    store.remember(binding(content_id="MY_F2"))
    store.remember(binding(content_id="MY_F3"))
    assert [item.content_id for item in store.all()] == ["MY_F2", "MY_F3"]
    assert (state / "history.json").read_bytes() == b"preserve"


@pytest.mark.parametrize(
    "changes",
    [
        {"device_id": "bad"},
        {"content_id": "../x"},
        {"thumbnail_sha256": "bad"},
        {"work_id": "bad"},
        {"recorded_at": "now"},
        {"title": "x" * 201},
        {"artist": "bad\ntext"},
        {"source": 4},
        {"extra": "x"},
    ],
)
def test_binding_validation(changes: dict[str, object]) -> None:
    value = asdict(binding())
    with pytest.raises(ValueError, match="invalid"):
        Binding.from_json(dict(value, **changes))


@pytest.mark.parametrize("items", [None, {}, [4], [asdict(binding()), asdict(binding())]])
def test_document_rejects_invalid_or_duplicate_records(items: object) -> None:
    with pytest.raises(ValueError, match=r"invalid|duplicate"):
        module.SPEC.parse({"bindings": items})


@pytest.mark.parametrize("owner", [None, "x", "z" * 64, 5])
def test_ownership_validation(owner: object) -> None:
    with pytest.raises(ValueError, match="invalid observer owner"):
        module.OWNER_SPEC.parse({"owner": owner})


def test_corrupt_owner_is_not_silently_replaced(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()
    (state / module.OWNER_FILE).write_text("broken")
    with pytest.raises(StateError):
        BindingStore(tmp_path).owner()
    assert (state / module.OWNER_FILE).read_text() == "broken"


def test_newer_mapping_and_journal_are_preserved(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()
    store = BindingStore(tmp_path)
    (state / module.FILE).write_text(json.dumps({"format": module.FORMAT, "version": 2}))
    with pytest.raises(StateError):
        store.all()
    with pytest.raises(StateError):
        store.remember(binding())
    (state / "observer-requests.json").write_text(
        json.dumps({"format": module.REQUEST_SPEC.format, "version": 2})
    )
    with pytest.raises(StateError):
        store.claim(Command(Action.NEW_ARTWORK, "request_123", 100), 100)


def test_request_claim_is_durable_and_expiry_prevents_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = BindingStore(tmp_path)
    item = Command(Action.NEW_ARTWORK, "request_123", 100)
    assert store.claim(item, 100)
    assert not BindingStore(tmp_path).claim(item, 110)
    assert not store.claim(item, 401)
    assert not store.claim(replace(item, issued_at=1000), 100)
    monkeypatch.setattr(module, "MAX_REQUESTS", 1)
    assert not store.claim(replace(item, request_id="request_456"), 100)
    assert store.claim(replace(item, request_id="request_456", issued_at=401), 401)
    (tmp_path / "state" / "observer-requests.json").write_text("bad")
    (tmp_path / "state" / "observer-requests.json.bak").unlink(missing_ok=True)
    with pytest.raises(StateError):
        store.claim(replace(item, issued_at=402), 402)


@pytest.mark.parametrize("missing", [False, True])
def test_journal_backup_never_replays_the_last_consumed_request(
    tmp_path: Path, missing: bool
) -> None:
    store = BindingStore(tmp_path)
    first = Command(Action.NEW_ARTWORK, "request_123", 100)
    second = replace(first, request_id="request_456")
    assert store.claim(first, 100)
    assert store.claim(second, 100)
    primary = tmp_path / "state" / "observer-requests.json"
    if missing:
        primary.unlink()
    else:
        primary.write_text("damaged")
    with pytest.raises(StateError, match="dispatch disabled"):
        BindingStore(tmp_path).claim(second, 101)


@pytest.mark.parametrize(
    "items",
    [
        None,
        {},
        [None],
        [{}],
        [{"id": "bad", "at": 1}],
        [{"id": "request_123", "at": True}],
        [{"id": "request_123", "at": float("inf")}],
        [{"id": "request_123", "at": 10**400}],
        [{"id": "request_123", "at": "now"}],
    ],
)
def test_journal_parser_limits(items: object) -> None:
    with pytest.raises(ValueError, match="invalid observer request"):
        module.REQUEST_SPEC.parse({"requests": items})


def test_service_lock_does_not_take_or_remove_delivery_lock(tmp_path: Path) -> None:
    first, second = ObserverLock(tmp_path), ObserverLock(tmp_path)
    first.close()
    first.acquire()
    with pytest.raises(StateError, match="already held"):
        first.acquire()
    with pytest.raises(StateError):
        second.acquire()
    first.close()
    first.close()
    second.acquire()
    second.close()
    assert not (tmp_path / "state" / ".lock").exists()


def test_service_lock_cannot_be_a_pipe(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()
    os.mkfifo(state / "observer.lock")
    with pytest.raises(StateError):
        ObserverLock(tmp_path).acquire()
