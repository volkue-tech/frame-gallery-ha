"""Successful-send associations are bounded and never a current-TV shortcut."""

from __future__ import annotations

import base64
from dataclasses import asdict
from pathlib import Path

import pytest

from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.errors import StateError
from frame_gallery.imaging.reference import REFERENCE_BYTES
from frame_gallery.observer.model import Evidence, Observation, Status
from frame_gallery.store import delivery_associations as module
from frame_gallery.store.delivery_associations import DeliveryAssociation, DeliveryAssociations
from tests.support.clock import FakeClock


def item(**changes: object) -> DeliveryAssociation:
    fields: dict[str, object] = {
        "device_id": "a" * 64,
        "content_id": "MY_F0001",
        "target_sha256": "b" * 64,
        "jpeg_sha256": "c" * 64,
        "work_id": "commons:123",
        "source": "commons",
        "title": "A title",
        "artist": "An artist",
        "detail_url": "https://example.test/work",
        "recorded_at": "2026-10-18T10:00:00+00:00",
        "reference_rgb": None,
        "image_rejected": False,
    }
    return DeliveryAssociation.from_json({**fields, **changes})


def deadline(seconds: float = 5) -> Deadline:
    return Deadline.after(FakeClock(), seconds, "associations")


def test_saved_per_device_ids_survive_restart_and_same_id_replacement(tmp_path: Path) -> None:
    store = DeliveryAssociations(tmp_path)
    assert store.all() == ()
    store.remember(item(), deadline())
    store.remember(item(device_id="d" * 64, title="Other TV"), deadline())
    store.remember(item(title="New confirmed upload"), deadline())
    reopened = DeliveryAssociations(tmp_path)
    assert len(reopened.all()) == 2
    first, second = reopened.find("a" * 64, "MY_F0001"), reopened.find("d" * 64, "MY_F0001")
    assert first is not None
    assert first.title == "New confirmed upload"
    assert second is not None
    assert second.title == "Other TV"
    assert reopened.find("e" * 64, "MY_F0001") is None
    assert not (tmp_path / "state/artwork-bindings.json").exists()
    assert not (tmp_path / "state/current.json").exists()


def test_mapping_is_not_current_proof_or_a_thumbnail_hash() -> None:
    association = item()
    assert association.matches(
        Observation(Status.UNIDENTIFIED, "a" * 64, "MY_F0001", None, Evidence.SLIDESHOW)
    )
    assert not association.matches(Observation(Status.UNIDENTIFIED, "a" * 64, "MY_F0001", "f" * 64))
    assert not association.matches(
        Observation(Status.UNIDENTIFIED, "d" * 64, "MY_F0001", None, Evidence.SLIDESHOW)
    )
    assert not association.matches(Observation(Status.PAUSED))


@pytest.mark.parametrize(
    "changes",
    [
        {"device_id": "192.168.1.20"},
        {"content_id": "../bad"},
        {"target_sha256": "bad"},
        {"jpeg_sha256": "bad"},
        {"work_id": "bad"},
        {"source": "wrong"},
        {"title": "x" * 201},
        {"artist": "bad\ntext"},
        {"recorded_at": "bad"},
        {"reference_rgb": "bad"},
        {"image_rejected": 1},
        {"reference_rgb": "!" * (REFERENCE_BYTES * 4 // 3)},
        {"unexpected": "refused"},
    ],
)
def test_invalid_fields_are_refused(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="invalid"):
        item(**changes)


def test_reference_and_record_conversion_have_explicit_provenance() -> None:
    reference = base64.b64encode(b"x" * REFERENCE_BYTES).decode()
    association = item(reference_rgb=reference)
    record: dict[str, object] = {
        "id": association.work_id,
        "tv_device_id": association.device_id,
        "tv_content_id": association.content_id,
        "tv_target_sha256": association.target_sha256,
        "sha256": association.jpeg_sha256,
        "delivered_at": association.recorded_at,
        "delivery_reference_rgb": reference,
        "attribution": {
            "title": association.title,
            "creator": association.artist,
            "detail_url": association.detail_url,
        },
    }
    assert DeliveryAssociation.from_record(record) == association
    with pytest.raises(ValueError, match="missing delivery metadata"):
        DeliveryAssociation.from_record({**record, "attribution": None})
    assert DeliveryAssociation.from_record({**record, "attribution": {}}).title == ""


def test_count_and_byte_bounds_keep_newest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "MAX_DELIVERIES", 2)
    store = DeliveryAssociations(tmp_path)
    for n in range(3):
        store.remember(item(content_id=f"MY_F{n}"), deadline())
    assert [b.content_id for b in store.all()] == ["MY_F1", "MY_F2"]
    monkeypatch.setattr(module, "MAX_BYTES", 650)
    store.remember(item(content_id="MY_F3"), deadline())
    assert [b.content_id for b in store.all()] == ["MY_F3"]


def test_deadline_and_corruption_never_overwrite_prior(tmp_path: Path) -> None:
    store = DeliveryAssociations(tmp_path)
    with pytest.raises(DeadlineExceeded):
        store.remember(item(), deadline(0))
    state = tmp_path / "state"
    state.mkdir()
    path = state / module.FILE
    path.write_text("not JSON")
    with pytest.raises(StateError):
        store.remember(item(), deadline())
    assert path.read_text() == "not JSON"


@pytest.mark.parametrize(
    "rows",
    [
        None,
        [None],
        [asdict(item()), asdict(item())],
        [asdict(item())] * (module.MAX_DELIVERIES + 1),
    ],
)
def test_invalid_document_structure(rows: object) -> None:
    with pytest.raises(ValueError, match=r"invalid|duplicate"):
        module._read({"deliveries": rows})


def test_corrupt_primary_never_rolls_back_a_reused_id_to_backup(tmp_path: Path) -> None:
    store = DeliveryAssociations(tmp_path)
    store.remember(item(), deadline())
    store.remember(item(title="Replacement"), deadline())
    backup = tmp_path / "state" / (module.FILE + ".bak")
    assert b"A title" in backup.read_bytes()
    (tmp_path / "state" / module.FILE).write_text("damaged")
    with pytest.raises(StateError, match="older backup"):
        store.find("a" * 64, "MY_F0001")
    assert b"A title" in backup.read_bytes()


def test_future_schema_never_gets_replaced(tmp_path: Path) -> None:
    store = DeliveryAssociations(tmp_path)
    store.remember(item(), deadline())
    path = tmp_path / "state" / module.FILE
    content = path.read_text().replace('"version":1', '"version":2')
    path.write_text(content)
    with pytest.raises(StateError, match="safely"):
        store.remember(item(title="Do not overwrite"), deadline())
    assert path.read_text() == content
