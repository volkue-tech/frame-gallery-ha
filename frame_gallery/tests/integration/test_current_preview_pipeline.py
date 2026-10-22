"""Real image/store pipeline with injected TV and Core transports, no live I/O."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from frame_gallery.app.outcomes import Outcome
from frame_gallery.budget.deadline import Deadline
from frame_gallery.imaging.worker_tasks import prepare_image
from frame_gallery.observer.model import Evidence, Observation, Status
from frame_gallery.store.current_preview import NEUTRAL_JPEG, CurrentPreview
from frame_gallery.store.delivery_associations import DeliveryAssociations
from frame_gallery.store.preview_cache import PreviewCache
from frame_gallery.store.records import RunRecordStore
from tests.support.clock import FakeClock
from tests.unit.app.harness import Harness
from tests.unit.ha.test_current_artwork import OWNER, Rig, response
from tests.unit.imaging.test_verify_thumbnail import jpeg


@pytest.mark.parametrize("background", [False, True])
def test_real_prepare_send_cache_restart_and_current_caption(
    tmp_path: Path,
    background: bool,
) -> None:
    data, media = tmp_path / "data", tmp_path / "media"
    data.mkdir()
    media.mkdir()
    clock = FakeClock()
    h = Harness(
        tmp_path,
        clock=clock,
        raw={"tv_host": "192.168.1.20", "background_mode": background},
        records_port=RunRecordStore(data, clock=clock),
    )
    h.fetcher.payloads["1001"] = jpeg((3840, 2160))
    h.executor.behaviours = [lambda request: prepare_image(request).to_json()]
    result = h.run()
    assert result.outcome is Outcome.DELIVERED
    assert result.delivered_id == "aic:1001"
    binding = DeliveryAssociations(data).find("d" * 64, "MY_F0001")
    assert binding is not None
    assert binding.jpeg_sha256 == hashlib.sha256(h.tv.payloads[0]).hexdigest()
    cached = PreviewCache(data).lookup(binding, Deadline.after(clock, 5, "cache"))
    assert cached is not None
    assert cached != h.tv.payloads[0]  # Small derivative, not the full television payload.
    assert len(cached) < 32 * 1024
    current = CurrentPreview(data, media)  # Reopened state after a process restart.
    rig = Rig()
    rig.transport.add(response({}, 404), response({}), response({}))
    seen = Observation(
        Status.UNIDENTIFIED, binding.device_id, binding.content_id, None, Evidence.CURRENT_STATE
    )
    assert rig.client.publish(
        OWNER,
        seen,
        binding,
        Deadline.after(rig.clock, 2, "current"),
        prepare_preview=current.publish,
    )
    body = json.loads(rig.transport.calls[-1].request.body or b"")
    assert body["state"] == "artwork"
    assert body["attributes"]["artist"] == "Test Painter"
    assert body["attributes"]["preview_sha256"] == hashlib.sha256(cached).hexdigest()
    assert (media / "frame_gallery/preview/current.jpg").read_bytes() == cached
    assert not (
        media / "frame_gallery/preview/latest.jpg"
    ).exists()  # Existing preview is its own port.
    rig.transport.add(response({"attributes": {"frame_gallery_owner": OWNER}}), response({}))
    assert rig.client.publish(
        OWNER,
        Observation(Status.PAUSED),
        None,
        Deadline.after(rig.clock, 2, "pause"),
        prepare_preview=current.publish,
    )
    paused = json.loads(rig.transport.calls[-1].request.body or b"")
    assert paused["state"] == "paused"
    assert paused["attributes"]["preview_available"] is False
    assert "artist" not in paused["attributes"]
    assert (media / "frame_gallery/preview/current.jpg").read_bytes() == NEUTRAL_JPEG
    assert DeliveryAssociations(data).find("d" * 64, "MY_F0001") == binding
