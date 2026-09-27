"""The television port's value types and markers (§12.1)."""

from __future__ import annotations

from ipaddress import IPv4Address
from pathlib import Path

import pytest

from frame_gallery.budget.deadline import Deadline
from frame_gallery.tv.port import (
    CONTENT_ID_PATTERN,
    MARKER_ORDER,
    AuthChange,
    DeliveryRequest,
    DeliveryResult,
    DeliveryStatus,
    Marker,
    MarkerEvent,
)
from tests.support.clock import FakeClock


class TestMarkerEvent:
    @pytest.mark.parametrize(
        "content_id", ["MY_F0042", "a", "A-b_c.d:e", "0" * 64, "x" * 63, "MY-C0002_20260926"]
    )
    def test_uploaded_accepts_a_valid_content_id(self, content_id: str) -> None:
        event = MarkerEvent(Marker.UPLOADED, content_id)
        assert event.content_id == content_id

    def test_uploaded_may_come_without_a_content_id(self) -> None:
        assert MarkerEvent(Marker.UPLOADED).content_id is None

    @pytest.mark.parametrize(
        "content_id",
        [
            "",
            "x" * 65,
            "a b",
            "a/b",
            "a\\b",
            "abc\n",
            "é",
            "a;b",
            "a\x00",
            "<id>",
        ],
    )
    def test_uploaded_rejects_an_invalid_content_id(self, content_id: str) -> None:
        with pytest.raises(ValueError, match="valid content_id"):
            MarkerEvent(Marker.UPLOADED, content_id)

    @pytest.mark.parametrize("marker", [Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.SELECTED])
    def test_other_markers_carry_no_content_id(self, marker: Marker) -> None:
        assert MarkerEvent(marker).content_id is None
        with pytest.raises(ValueError, match=f"the {marker.value} marker carries no content_id"):
            MarkerEvent(marker, "MY_F0042")

    def test_content_id_pattern_bounds(self) -> None:
        assert CONTENT_ID_PATTERN.fullmatch("a" * 64) is not None
        assert CONTENT_ID_PATTERN.fullmatch("a" * 65) is None
        assert CONTENT_ID_PATTERN.fullmatch("") is None


class TestMarkers:
    def test_order(self) -> None:
        assert MARKER_ORDER == (
            Marker.CONNECTED,
            Marker.UPLOAD_STARTED,
            Marker.UPLOADED,
            Marker.SELECTED,
        )
        assert set(MARKER_ORDER) == set(Marker)
        assert [marker.value for marker in MARKER_ORDER] == [
            "connected",
            "upload_started",
            "uploaded",
            "selected",
        ]


class TestDelivery:
    def test_result_defaults(self) -> None:
        result = DeliveryResult(DeliveryStatus.OK)
        assert result.auth is AuthChange.UNCHANGED
        assert result.markers_seen == ()
        assert result.detail == ""

    def test_result_fields(self) -> None:
        result = DeliveryResult(
            DeliveryStatus.UNREACHABLE,
            auth=AuthChange.NEW_TOKEN,
            markers_seen=(Marker.CONNECTED, Marker.UPLOAD_STARTED),
            detail="connection lost",
        )
        assert result.markers_seen == MARKER_ORDER[:2]

    def test_statuses_and_auth_changes(self) -> None:
        assert [status.value for status in DeliveryStatus] == [
            "ok",
            "unreachable",
            "not_authorized",
            "unsupported",
            "refused",
            "protocol",
            "insufficient_time",
        ]
        assert [change.value for change in AuthChange] == [
            "unchanged",
            "new_token",
            "token_rejected",
        ]

    def test_request(self, tmp_path: Path) -> None:
        clock = FakeClock()
        deadline = Deadline.after(clock, 40.0, "deliver")
        request = DeliveryRequest(
            jpeg_path=tmp_path / "delivery.jpg",
            jpeg_sha256="0" * 64,
            tv_host=IPv4Address("10.0.0.5"),
            deadline=deadline,
        )
        assert request.tv_host.is_private
        assert request.deadline is deadline


def test_a_delivery_request_reports_no_stop_by_default() -> None:
    clock = FakeClock()
    request = DeliveryRequest(
        jpeg_path=Path("out/delivery-0.jpg"),
        jpeg_sha256="0" * 64,
        tv_host=IPv4Address("10.0.0.5"),
        deadline=Deadline.after(clock, 40.0, "deliver"),
    )
    assert request.stop_requested() is False
