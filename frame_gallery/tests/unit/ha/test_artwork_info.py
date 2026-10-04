"""D-202: explicit text-helper output, no retries or token leakage."""

from __future__ import annotations

import json

import pytest

from frame_gallery.budget.deadline import Deadline
from tests.support.net import FakeResponse, connect_failure
from tests.unit.ha.test_loading import TOKEN, Rig

HELPER = "input_text.frame_gallery_artwork"


def state(value: str = "old metadata", status: int = 200) -> FakeResponse:
    return FakeResponse(
        status=status,
        headers={"content-type": "application/json"},
        body=json.dumps({"state": value}).encode(),
    )


def test_only_existing_helper_get_and_two_scoped_service_posts() -> None:
    rig = Rig()
    get, clear, update = state(), FakeResponse(), FakeResponse()
    rig.transport.add(get, clear, update)
    deadline = Deadline.after(rig.clock, 2, "artwork information")
    assert rig.client.write_artwork_info(HELPER, "", deadline)
    assert rig.client.write_artwork_info(HELPER, '{"title":"Été"}', deadline)
    assert len(rig.resolver.calls) == 1
    assert [call.request.target for call in rig.transport.calls] == [
        "/core/api/states/" + HELPER,
        "/core/api/services/input_text/set_value",
        "/core/api/services/input_text/set_value",
    ]
    assert rig.transport.calls[0].request.method == "GET"
    for call, value in zip(rig.transport.calls[1:], ("", '{"title":"Été"}'), strict=True):
        request = call.request
        assert request.method == "POST"
        assert json.loads(request.body or b"") == {"entity_id": HELPER, "value": value}
        assert request.headers["Authorization"] == f"Bearer {TOKEN}"
        assert request.headers["Content-Length"] == str(len(request.body or b""))
        assert call.exchange_timeout <= 2
    assert all(response.closed for response in (get, clear, update))
    assert not clear.reads
    assert not update.reads


@pytest.mark.parametrize(
    ("entity", "value"),
    [
        ("sensor.x", ""),
        ("input_text.x,input_text.y", ""),
        ("input_text.X", ""),
        ("input_text.x\n", ""),
        (HELPER, "x" * 256),
    ],
)
def test_invalid_target_or_oversize_state_sends_nothing(entity: str, value: str) -> None:
    rig = Rig()
    assert not rig.client.write_artwork_info(entity, value, Deadline.after(rig.clock, 2, "info"))
    assert not rig.resolver.calls
    assert not rig.transport.calls


@pytest.mark.parametrize("token", [None, "", "with space", "bad\nheader"])
def test_missing_token_sends_nothing(token: str | None) -> None:
    rig = Rig(token=token)
    assert not rig.client.write_artwork_info(HELPER, "", Deadline.after(rig.clock, 2, "info"))
    assert not rig.transport.calls


@pytest.mark.parametrize("address", ["8.8.8.8", "10.0.0.9", "127.0.0.1", "169.254.1.2"])
def test_token_never_goes_to_other_networks(address: str) -> None:
    rig = Rig(address=address)
    assert not rig.client.write_artwork_info(HELPER, "", Deadline.after(rig.clock, 2, "info"))
    assert not rig.transport.calls


@pytest.mark.parametrize("status", [301, 400, 401, 403, 404, 500])
@pytest.mark.parametrize("phase", ["get", "post"])
def test_http_failures_close_without_retry_and_auth_failures_disable_later_calls(
    status: int, phase: str, caplog: pytest.LogCaptureFixture
) -> None:
    rig = Rig()
    response = state(status=status)
    rig.transport.add(*([state(), response] if phase == "post" else [response]))
    deadline = Deadline.after(rig.clock, 2, "info")
    assert not rig.client.write_artwork_info(HELPER, "", deadline)
    assert len(rig.transport.calls) == (2 if phase == "post" else 1)
    assert response.closed
    if status in (401, 403):
        before = len(rig.transport.calls)
        assert not rig.client.write_artwork_info(HELPER, "new metadata", deadline)
        rig.finish()
        assert len(rig.transport.calls) == before
    assert TOKEN not in caplog.text
    assert "old metadata" not in caplog.text


@pytest.mark.parametrize(
    ("value", "success"), [("unavailable", False), ("unknown", True), ("", True)]
)
def test_unavailable_helper_is_rejected_but_new_empty_helper_can_start(
    value: str, success: bool
) -> None:
    rig = Rig()
    rig.transport.add(state(value), FakeResponse())
    assert (
        rig.client.write_artwork_info(HELPER, "", Deadline.after(rig.clock, 2, "info")) is success
    )
    assert len(rig.transport.calls) == (2 if success else 1)


@pytest.mark.parametrize("phase", ["get", "post"])
def test_transport_failure_and_expired_shared_budget_are_bounded(phase: str) -> None:
    rig = Rig()
    rig.transport.add(*([state(), connect_failure()] if phase == "post" else [connect_failure()]))
    deadline = Deadline.after(rig.clock, 2, "info")
    assert not rig.client.write_artwork_info(HELPER, "", deadline)
    count = len(rig.transport.calls)
    rig.clock.advance(2)
    assert not rig.client.write_artwork_info(HELPER, "new", deadline)
    assert len(rig.transport.calls) == count


def test_slow_clear_leaves_only_the_remainder_for_final_write() -> None:
    rig = Rig()

    def slow(_request: object) -> FakeResponse:
        rig.clock.advance(1.7)
        return FakeResponse()

    rig.transport.add(state(), slow, FakeResponse())
    deadline = Deadline.after(rig.clock, 2, "info")
    assert rig.client.write_artwork_info(HELPER, "", deadline)
    assert rig.client.write_artwork_info(HELPER, "new", deadline)
    assert rig.transport.calls[-1].exchange_timeout == pytest.approx(0.3)
