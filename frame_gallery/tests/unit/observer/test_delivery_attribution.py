"""Confirmed sends, archived image proof and later events, without a real TV."""

from __future__ import annotations

import base64
from dataclasses import replace
from pathlib import Path

import pytest
from tests.support.clock import FakeClock
from tests.unit.observer.test_backend import DEVICE, HOST, THUMBNAIL_HASH, Rig
from tests.unit.store.test_delivery_associations import item

from frame_gallery.budget.deadline import Deadline
from frame_gallery.observer.backend import HostObserver
from frame_gallery.observer.model import Evidence, Observation, Status
from frame_gallery.observer.stream import SLIDESHOW_POLICY
from frame_gallery.store.artwork_bindings import Binding, BindingStore
from frame_gallery.store.delivery_associations import DeliveryAssociations
from frame_gallery.store.observer_targets import TargetStore
from frame_gallery.tv.port import target_fingerprint


def deadline() -> Deadline:
    return Deadline.after(FakeClock(), 5, "test association")


def test_archived_send_can_be_verified_when_it_is_not_last_preview(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    association = item(
        device_id=DEVICE,
        content_id="MY_OLDER",
        target_sha256=target_fingerprint(HOST),
        reference_rgb=base64.b64encode(bytes(range(256)) * 27).decode(),
    )
    archive = DeliveryAssociations(rig.data)
    archive.remember(association, deadline())
    initial = Observation(Status.UNIDENTIFIED, DEVICE, "MY_OLDER", THUMBNAIL_HASH)
    snapshot = {**initial.to_json(), "thumbnail": "eA=="}
    current = (rig.data / "state/current.json").read_bytes()
    assert rig.observer.accept_snapshot(snapshot) == initial
    resolved = BindingStore(rig.data).resolve(initial)
    assert isinstance(resolved, Binding)
    assert resolved.title == association.title
    assert rig.executor.calls == [
        ("verify_thumbnail", {"reference_rgb": association.reference_rgb, "thumbnail": "eA=="})
    ]
    assert (rig.data / "state/current.json").read_bytes() == current
    # Later automatic ID changes use the genuine upload association; no new
    # thumbnail is invented, requested or downloaded.
    seen = rig.observer.accept_slideshow("MY_OLDER")
    assert seen.evidence is Evidence.SLIDESHOW
    assert seen.thumbnail_sha256 is None
    assert BindingStore(rig.data).resolve(seen) == association
    assert len(rig.executor.calls) == 1


def test_thumbnail_mismatch_invalidates_receipt_and_old_caption_until_reverified(
    tmp_path: Path,
) -> None:
    rig = Rig(tmp_path)
    association = item(
        device_id=DEVICE, content_id="MY_TEST", reference_rgb=base64.b64encode(b"x" * 6912).decode()
    )
    archive = DeliveryAssociations(rig.data)
    archive.remember(association, deadline())
    rig.executor.matched = False
    initial = Observation(Status.UNIDENTIFIED, DEVICE, "MY_TEST", THUMBNAIL_HASH)
    rig.observer.accept_snapshot({**initial.to_json(), "thumbnail": "eA=="})
    rejected = archive.find(DEVICE, "MY_TEST")
    assert rejected is not None
    assert rejected.image_rejected
    assert BindingStore(rig.data).resolve(rig.observer.accept_slideshow("MY_TEST")) is None
    assert BindingStore(rig.data).resolve(initial) is None
    rig.executor.matched = True
    rig.observer.accept_snapshot({**initial.to_json(), "thumbnail": "eA=="})
    restored = archive.find(DEVICE, "MY_TEST")
    assert restored is not None
    assert not restored.image_rejected
    assert BindingStore(rig.data).resolve(initial) is not None


@pytest.mark.parametrize("wrong", ["device", "content"])
def test_other_tv_or_content_never_borrows_metadata(tmp_path: Path, wrong: str) -> None:
    rig = Rig(tmp_path)
    association = item(device_id=DEVICE, content_id="MY_TEST")
    DeliveryAssociations(rig.data).remember(association, deadline())
    seen = Observation(
        Status.UNIDENTIFIED,
        "f" * 64 if wrong == "device" else DEVICE,
        "MY_OTHER" if wrong == "content" else "MY_TEST",
        None,
        Evidence.SLIDESHOW,
    )
    assert BindingStore(rig.data).resolve(seen) is None
    assert not rig.executor.calls


def test_new_acknowledged_upload_with_reused_id_cannot_resolve_old_image_binding(
    tmp_path: Path,
) -> None:
    rig = Rig(tmp_path)
    initial = rig.observer.read()
    assert BindingStore(rig.data).resolve(initial) is not None
    DeliveryAssociations(rig.data).remember(
        item(device_id=DEVICE, content_id="MY_TEST", work_id="commons:999"), deadline()
    )
    assert BindingStore(rig.data).resolve(initial) is None
    event = rig.observer.accept_slideshow("MY_TEST")
    chosen = BindingStore(rig.data).resolve(event)
    assert chosen is not None
    assert chosen.work_id == "commons:999"


def test_only_a_fresh_exact_persisted_sender_receipt_grants_one_generic_session(
    tmp_path: Path,
) -> None:
    rig = Rig(tmp_path)
    observer = HostObserver(rig.executor, rig.data, rig.media, HOST)
    assert observer.event_policy(DEVICE) is None  # no persisted resume permission
    before = observer.delivery_snapshot()
    association = item(
        device_id=DEVICE, content_id="MY_TEST", target_sha256=target_fingerprint(HOST)
    )
    DeliveryAssociations(rig.data).remember(association, deadline())
    rig.record.update(tv_device_id=DEVICE, sha256=association.jpeg_sha256)
    rig.save()
    assert observer.after_delivery(before)
    assert observer.event_policy(DEVICE) == SLIDESHOW_POLICY
    assert observer.event_policy(DEVICE) is None  # consumed, no reconnect/refresh grant
    assert TargetStore(rig.data).targets()[str(HOST)] == DEVICE
    assert not rig.executor.calls


@pytest.mark.parametrize(
    "broken", ["missing", "bad_device", "wrong_target", "wrong_sha", "wrong_work", "rejected"]
)
def test_invalid_or_unpersisted_delivery_never_grants_session(tmp_path: Path, broken: str) -> None:
    rig = Rig(tmp_path)
    observer = HostObserver(rig.executor, rig.data, rig.media, HOST)
    before = observer.delivery_snapshot()
    association = item(
        device_id=DEVICE, content_id="MY_TEST", target_sha256=target_fingerprint(HOST)
    )
    if broken != "missing":
        DeliveryAssociations(rig.data).remember(
            replace(
                association,
                target_sha256="e" * 64 if broken == "wrong_target" else association.target_sha256,
                jpeg_sha256="f" * 64 if broken == "wrong_sha" else association.jpeg_sha256,
                work_id="commons:999" if broken == "wrong_work" else association.work_id,
                image_rejected=broken == "rejected",
            ),
            deadline(),
        )
    rig.record.update(
        tv_device_id="bad" if broken == "bad_device" else DEVICE, sha256=association.jpeg_sha256
    )
    rig.save()
    assert not observer.after_delivery(before)
    assert observer.event_policy(DEVICE) is None
    assert not rig.executor.calls
