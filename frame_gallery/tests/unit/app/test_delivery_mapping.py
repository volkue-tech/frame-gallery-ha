"""Real durable store plus runner, injected TV only, no HA/network access."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from frame_gallery.app.outcomes import Outcome
from frame_gallery.errors import PublishError, StateError
from frame_gallery.store.delivery_associations import DeliveryAssociations
from frame_gallery.store.records import RunRecordStore
from frame_gallery.tv.port import DeliveryRequest, DeliveryResult, Marker, MarkerSink
from tests.support.fakes import FakeTelevision
from tests.unit.app.harness import Harness


@pytest.fixture(autouse=True)
def data_directory(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()


@pytest.mark.parametrize("background", [False, True])
@pytest.mark.parametrize("failure", ["none", "preview", "history", "cancel"])
def test_selected_upload_survives_mode_restart_and_later_failures(
    tmp_path: Path, background: bool, failure: str
) -> None:
    h = Harness(tmp_path, raw={"tv_host": "192.168.1.20", "background_mode": background})
    data = tmp_path / "data"
    h.records_port = RunRecordStore(data, clock=h.clock)
    if failure == "preview":
        h.preview.error = PublishError("injected preview failure")
    elif failure == "history":
        h.state.fail["record_history"] = StateError("injected history failure")
    elif failure == "cancel":
        h.tv.during = lambda marker: (
            h.cancellation.request_stop() if marker is Marker.SELECTED else None
        )
    h.run()
    records = DeliveryAssociations(data).all()
    assert len(records) == 1
    record = records[0]
    assert record.device_id == "d" * 64
    assert record.content_id == "MY_F0001"
    assert record.work_id == "aic:1001"
    assert record.reference_rgb is None  # this runner fixture uses the old synthetic preparer
    assert len(h.tv.requests) == 1  # no identity/image/observer round-trip added
    assert not h.workspace.root.exists()
    if failure == "cancel":
        assert not (data / "state/current.json").exists()


@pytest.mark.parametrize("last", [Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED])
def test_failed_or_uncertain_send_never_creates_successful_mapping(
    tmp_path: Path, last: Marker
) -> None:
    h = Harness(tmp_path)
    h.records_port = RunRecordStore(tmp_path / "data", clock=h.clock)
    h.tv.markers = [Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED][
        : [Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED].index(last) + 1
    ]
    h.run()
    assert DeliveryAssociations(tmp_path / "data").all() == ()


def test_missing_device_identity_reports_warning_without_guessing(tmp_path: Path) -> None:
    h = Harness(tmp_path)
    h.records_port = RunRecordStore(tmp_path / "data", clock=h.clock)

    class LegacyTV(FakeTelevision):
        def deliver(self, request: DeliveryRequest, on_marker: MarkerSink) -> DeliveryResult:
            return replace(super().deliver(request, on_marker), device_id=None)

    h.tv = LegacyTV(h.events, h.clock)
    result = h.run()
    assert result.outcome is Outcome.DELIVERED_WITH_WARNINGS
    assert DeliveryAssociations(tmp_path / "data").all() == ()
    assert (tmp_path / "data/state/current.json").exists()
