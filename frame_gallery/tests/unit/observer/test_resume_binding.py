"""No-image-send wake validation reuses only exact local pinned-target history."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.unit.observer.test_backend import DEVICE, HOST, Rig
from tests.unit.observer.test_delivery_attribution import deadline
from tests.unit.store.test_delivery_associations import item

from frame_gallery.observer.backend import HostObserver
from frame_gallery.observer.model import Observation, Status
from frame_gallery.observer.stream import SLIDESHOW_POLICY
from frame_gallery.store.delivery_associations import DeliveryAssociations
from frame_gallery.store.observer_targets import TargetStore
from frame_gallery.tv.port import target_fingerprint
from frame_gallery.tv.token_store import TokenStore


@pytest.mark.parametrize("with_token", [False, True])
def test_pinned_historical_upload_can_prepare_once_without_send_or_state_change(
    tmp_path: Path, with_token: bool
) -> None:
    rig = Rig(tmp_path)
    if not with_token:
        TokenStore(rig.data, HOST).remove()
    TargetStore(rig.data).pin(HOST, DEVICE)
    DeliveryAssociations(rig.data).remember(
        item(device_id=DEVICE, target_sha256=target_fingerprint(HOST)), deadline()
    )
    observer = HostObserver(rig.executor, rig.data, rig.media, HOST)
    prior = {p.name: p.read_bytes() for p in (rig.data / "state").iterdir() if p.is_file()}
    assert observer.prepare_resume()
    assert observer.device_id == DEVICE
    assert observer.event_policy(DEVICE) == SLIDESHOW_POLICY
    assert observer.event_policy(DEVICE) is None
    request = observer.session_request()
    assert isinstance(request, dict)
    assert request["enroll_device"] is False
    assert request["tokenless_grant"] is (not with_token)
    assert not rig.executor.calls
    assert prior == {p.name: p.read_bytes() for p in (rig.data / "state").iterdir() if p.is_file()}


@pytest.mark.parametrize(
    "problem",
    [
        "no_pin",
        "no_archive",
        "other_tv",
        "other_target",
        "corrupt_pin",
        "corrupt_archive",
        "corrupt_token",
    ],
)
def test_resume_refuses_uncertain_or_wrong_device_without_any_network(
    tmp_path: Path, problem: str
) -> None:
    rig = Rig(tmp_path)
    if problem != "no_pin":
        TargetStore(rig.data).pin(HOST, DEVICE)
    if problem != "no_archive":
        DeliveryAssociations(rig.data).remember(
            item(
                device_id="f" * 64 if problem == "other_tv" else DEVICE,
                target_sha256="f" * 64 if problem == "other_target" else target_fingerprint(HOST),
            ),
            deadline(),
        )
    if problem == "corrupt_pin":
        (rig.data / "state/observer-targets.json").write_text("corrupt")
    elif problem == "corrupt_archive":
        (rig.data / "state/artwork-deliveries.json").write_text("corrupt")
    elif problem == "corrupt_token":
        (rig.data / "tv" / "192-168-1-20.token").write_text("bad\nline")
    observer = HostObserver(rig.executor, rig.data, rig.media, HOST)
    assert not observer.prepare_resume()
    assert observer.device_id is None
    assert observer.event_policy(DEVICE) is None
    assert not rig.executor.calls


def test_corrupt_stored_token_is_not_a_tokenless_observation_retry(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    (rig.data / "tv/192-168-1-20.token").write_bytes(b"invalid!")
    reply = rig.observer.session_request()
    assert isinstance(reply, Observation)
    assert reply.status is Status.NOT_AUTHORIZED
    assert not rig.executor.calls
