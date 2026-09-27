"""The Samsung adapter over an executor (tv/samsung.py; §12, D-141, D-162).

The delivery logic runs in-process through the in-process executor, over the
stand-in of the installed library; a scripted executor covers hostile worker
events and results. The process-based worker has its own tests.
"""

from __future__ import annotations

import hashlib
import logging
import time
from ipaddress import IPv4Address
from pathlib import Path

import pytest

from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.isolation.executor import (
    EventSink,
    Executor,
    JsonObject,
    StopCheck,
    WorkerError,
    WorkerErrorKind,
)
from frame_gallery.isolation.in_process import InProcessExecutor
from frame_gallery.logs.redact import Redactor, set_active_redactor
from frame_gallery.tv.contract import TvRequest
from frame_gallery.tv.port import (
    AuthChange,
    DeliveryRequest,
    DeliveryResult,
    DeliveryStatus,
    Marker,
    MarkerEvent,
)
from frame_gallery.tv.samsung import DELIVER_TASK, DELIVER_TIMEOUT_S, SamsungTelevision
from frame_gallery.tv.samsung_task import run_delivery
from frame_gallery.tv.token_store import TokenStore
from tests.support.clock import FakeClock
from tests.support.fake_samsungtvws import Recorder, Script, make_library

HOST = IPv4Address("192.0.2.20")
JPEG = b"\xff\xd8" + b"x" * 500 + b"\xff\xd9"
STORED = "12345678"
NEW = "99999999"
OTHER = "44444444"
OK: JsonObject = {"status": "ok", "detail": "selected", "pairing": None}
ALL_MARKERS = (Marker.CONNECTED, Marker.UPLOAD_STARTED, Marker.UPLOADED, Marker.SELECTED)


class Rig:
    def __init__(self, tmp_path: Path, **script: object) -> None:
        self.data = tmp_path / "data"
        self.data.mkdir()
        outbox = tmp_path / "run" / "out"
        outbox.mkdir(parents=True)
        self.jpeg = outbox / "delivery-0.jpg"
        self.jpeg.write_bytes(JPEG)
        self.script = Script(**script)  # type: ignore[arg-type]
        self.recorder = Recorder()
        self.clock = FakeClock()
        self.now = 1000.0
        self.tokens = TokenStore(self.data, HOST)
        self.requests: list[TvRequest] = []
        library = make_library(self.script, self.recorder)

        def deliver(payload: JsonObject, emit: EventSink) -> JsonObject:
            request = TvRequest.from_json(payload)
            self.requests.append(request)
            return run_delivery(library, request, emit, monotonic=lambda: self.now)

        self.executor = InProcessExecutor({}, self.clock, event_tasks={DELIVER_TASK: deliver})
        self.markers: list[MarkerEvent] = []
        self.stop = False

    def television(self, executor: Executor | None = None) -> SamsungTelevision:
        return SamsungTelevision(executor or self.executor, self.tokens, monotonic=lambda: self.now)

    def request(self, seconds: float = 40.0) -> DeliveryRequest:
        return DeliveryRequest(
            jpeg_path=self.jpeg,
            jpeg_sha256=hashlib.sha256(JPEG).hexdigest(),
            tv_host=HOST,
            deadline=Deadline.after(self.clock, seconds, "deliver"),
            stop_requested=lambda: self.stop,
        )

    def deliver(self, television: SamsungTelevision | None = None) -> DeliveryResult:
        return (television or self.television()).deliver(self.request(), self.markers.append)


# ------------------------------------------------------------- over the task


def test_a_first_delivery_pairs_and_stores_the_token(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    result = rig.deliver()
    assert result == DeliveryResult(
        DeliveryStatus.OK, AuthChange.NEW_TOKEN, ALL_MARKERS, "selected"
    )
    assert [m.marker for m in rig.markers] == list(ALL_MARKERS)
    assert rig.markers[2].content_id == "MY_F0042"
    assert rig.tokens.load() == "12345678"
    assert rig.requests[0].token is None
    assert "open:ok:token=None:timeout=20.0" in rig.recorder.events


def test_the_request_carries_the_stored_token_hash_and_deadline(tmp_path: Path) -> None:
    rig = Rig(tmp_path, issue_token=STORED)
    rig.tokens.install(STORED)
    result = rig.deliver()
    assert result.auth is AuthChange.UNCHANGED
    request = rig.requests[0]
    assert request.token == STORED
    assert request.jpeg_sha256 == hashlib.sha256(JPEG).hexdigest()
    assert request.deadline == rig.now + DELIVER_TIMEOUT_S
    assert f"open:ok:token={STORED}:timeout=20.0" in rig.recorder.events


def test_no_token_file_is_shared_with_the_worker(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.tokens.install(STORED)
    rig.deliver()
    assert sorted(path.name for path in rig.jpeg.parent.iterdir()) == ["delivery-0.jpg"]


def test_a_new_token_replaces_the_stored_one(tmp_path: Path) -> None:
    rig = Rig(tmp_path, issue_token=NEW)
    rig.tokens.install(STORED)
    assert rig.deliver().auth is AuthChange.NEW_TOKEN
    assert rig.tokens.load() == NEW


def test_a_new_token_is_kept_even_if_the_delivery_fails_later(tmp_path: Path) -> None:
    rig = Rig(tmp_path, upload="lost")
    result = rig.deliver()
    assert (result.status, result.auth) == (DeliveryStatus.UNREACHABLE, AuthChange.NEW_TOKEN)
    assert rig.tokens.load() == "12345678"


def test_a_rejected_token_is_removed(tmp_path: Path) -> None:
    rig = Rig(tmp_path, open=["unauthorized"])
    rig.tokens.install(STORED)
    result = rig.deliver()
    assert result.status is DeliveryStatus.NOT_AUTHORIZED
    assert result.auth is AuthChange.TOKEN_REJECTED
    assert result.markers_seen == ()
    assert rig.tokens.load() is None


def test_a_rejection_without_a_stored_token_changes_nothing(tmp_path: Path) -> None:
    rig = Rig(tmp_path, open=["unauthorized"])
    assert rig.deliver().auth is AuthChange.UNCHANGED


def test_an_unaccepted_prompt_keeps_no_token(tmp_path: Path) -> None:
    rig = Rig(tmp_path, open=["prompt_timeout"])
    result = rig.deliver()
    assert result.status is DeliveryStatus.NOT_AUTHORIZED
    assert result.auth is AuthChange.UNCHANGED
    assert "prompt was not accepted" in result.detail


@pytest.mark.parametrize(
    ("script", "status", "markers"),
    [
        ({"supported": "no"}, DeliveryStatus.UNSUPPORTED, ()),
        ({"supported": "unreachable"}, DeliveryStatus.UNREACHABLE, ()),
        ({"api_version": "0.97"}, DeliveryStatus.UNSUPPORTED, ALL_MARKERS[:1]),
        ({"upload": "lost"}, DeliveryStatus.UNREACHABLE, ALL_MARKERS[:2]),
        ({"upload": "error"}, DeliveryStatus.PROTOCOL, ALL_MARKERS[:2]),
        ({"upload": "bad_id"}, DeliveryStatus.PROTOCOL, ALL_MARKERS[:3]),
        ({"select": "refused"}, DeliveryStatus.REFUSED, ALL_MARKERS[:3]),
    ],
)
def test_results_carry_the_markers_seen(
    tmp_path: Path, script: dict[str, str], status: DeliveryStatus, markers: tuple[Marker, ...]
) -> None:
    rig = Rig(tmp_path, **script)
    result = rig.deliver()
    assert result.status is status
    assert result.markers_seen == markers


def test_an_uploaded_marker_without_an_id_is_relayed(tmp_path: Path) -> None:
    rig = Rig(tmp_path, upload="bad_id")
    rig.deliver()
    assert rig.markers[-1] == MarkerEvent(Marker.UPLOADED, None)


def test_a_stop_request_ends_after_the_marker_already_sent(tmp_path: Path) -> None:
    """D-141: the adapter polls the stop request; every marker sent before
    the kill is still relayed."""
    rig = Rig(tmp_path)

    def stop_after_upload_started(event: MarkerEvent) -> None:
        rig.markers.append(event)
        if event.marker is Marker.UPLOAD_STARTED:
            rig.stop = True

    result = rig.television().deliver(rig.request(), stop_after_upload_started)
    assert result.status is DeliveryStatus.UNREACHABLE
    assert result.markers_seen == ALL_MARKERS[:2]
    assert "stopped" in result.detail
    assert not [e for e in rig.recorder.events if e.startswith("upload:")]


def test_no_time_left_raises_before_anything_starts(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    with pytest.raises(DeadlineExceeded):
        rig.television().deliver(rig.request(seconds=0), rig.markers.append)
    assert rig.recorder.events == []


def test_new_tokens_are_redacted_at_once(tmp_path: Path) -> None:
    redactor = Redactor()
    set_active_redactor(redactor)
    rig = Rig(tmp_path, issue_token=OTHER)
    rig.deliver()
    assert redactor.redact(f"the token {OTHER}") == "the token [REDACTED]"


def test_without_a_redactor_a_new_token_is_still_stored(tmp_path: Path) -> None:
    set_active_redactor(None)
    rig = Rig(tmp_path, issue_token=OTHER)
    assert rig.deliver().auth is AuthChange.NEW_TOKEN


def test_a_token_that_cannot_be_stored_only_warns(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    rig = Rig(tmp_path)
    (rig.data / "tv").write_text("not a directory")
    with caplog.at_level(logging.WARNING, "frame_gallery.tv"):
        result = rig.deliver()
    assert (result.status, result.auth) == (DeliveryStatus.OK, AuthChange.UNCHANGED)
    assert "could not be stored" in caplog.text


def test_the_default_clock_is_the_monotonic_one(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    captured: list[JsonObject] = []

    class Capturing(ScriptedExecutor):
        def run(
            self,
            task: str,
            payload: JsonObject,
            *,
            timeout: float,
            on_event: EventSink | None = None,
            should_stop: StopCheck | None = None,
        ) -> JsonObject:
            captured.append(payload)
            return super().run(
                task, payload, timeout=timeout, on_event=on_event, should_stop=should_stop
            )

    before = time.monotonic()
    SamsungTelevision(Capturing([], OK), rig.tokens).deliver(rig.request(), rig.markers.append)
    deadline = captured[0]["deadline"]
    assert isinstance(deadline, float)
    assert before + DELIVER_TIMEOUT_S <= deadline <= time.monotonic() + DELIVER_TIMEOUT_S


# ------------------------------------------------------ a scripted, hostile worker


class ScriptedExecutor:
    """Emits the given events, then fails or returns the given result."""

    def __init__(self, events: list[JsonObject], outcome: JsonObject | WorkerError) -> None:
        self.events = events
        self.outcome = outcome
        self.timeouts: list[float] = []

    def run(
        self,
        task: str,
        payload: JsonObject,
        *,
        timeout: float,
        on_event: EventSink | None = None,
        should_stop: StopCheck | None = None,
    ) -> JsonObject:
        self.timeouts.append(timeout)
        assert on_event is not None
        try:
            for event in self.events:
                on_event(event)
        except ValueError as exc:
            raise WorkerError(WorkerErrorKind.PROTOCOL, str(exc)) from None
        if isinstance(self.outcome, WorkerError):
            raise self.outcome
        return self.outcome

    def terminate_all(self) -> None:
        """Nothing to kill."""


def scripted(
    tmp_path: Path, events: list[JsonObject], outcome: JsonObject | WorkerError
) -> tuple[Rig, SamsungTelevision, ScriptedExecutor]:
    rig = Rig(tmp_path)
    executor = ScriptedExecutor(events, outcome)
    return rig, rig.television(executor), executor


def markers(*names: str, content_id: str | None = "MY_F0001") -> list[JsonObject]:
    return [
        {"marker": name, "content_id": content_id if name == "uploaded" else None} for name in names
    ]


@pytest.mark.parametrize(
    ("kind", "status"),
    [
        (WorkerErrorKind.TIMEOUT, DeliveryStatus.UNREACHABLE),
        (WorkerErrorKind.STOPPED, DeliveryStatus.UNREACHABLE),
        (WorkerErrorKind.CRASH, DeliveryStatus.PROTOCOL),
        (WorkerErrorKind.MEMORY, DeliveryStatus.PROTOCOL),
        (WorkerErrorKind.PROTOCOL, DeliveryStatus.PROTOCOL),
        (WorkerErrorKind.UNKNOWN_TASK, DeliveryStatus.PROTOCOL),
    ],
)
def test_worker_failures_are_classified_from_the_markers(
    tmp_path: Path, kind: WorkerErrorKind, status: DeliveryStatus
) -> None:
    events = markers("connected", "upload_started", "uploaded")
    rig, television, _ = scripted(tmp_path, events, WorkerError(kind))
    result = rig.deliver(television)
    assert result.status is status
    assert result.markers_seen == ALL_MARKERS[:3]
    assert kind.value in result.detail


@pytest.mark.parametrize(
    "event",
    [
        {"marker": "teleport", "content_id": None},
        {"marker": 5, "content_id": None},
        {"marker": "connected", "content_id": 5},
        {"marker": "connected"},
        {"marker": "connected", "content_id": None, "extra": True},
        {"marker": "uploaded", "content_id": "bad id!"},
        {"marker": "connected", "content_id": "MY_F0001"},
        {"token": "abc"},
        {"token": 12345678},
        {"token": STORED, "marker": "connected"},
        {},
    ],
)
def test_malformed_events_break_the_protocol(tmp_path: Path, event: JsonObject) -> None:
    rig, television, _ = scripted(tmp_path, [event], OK)
    result = rig.deliver(television)
    assert result.status is DeliveryStatus.PROTOCOL
    assert result.markers_seen == ()
    assert result.auth is AuthChange.UNCHANGED


def test_a_marker_out_of_order_is_relayed_then_breaks_the_protocol(tmp_path: Path) -> None:
    """The runner handles the marker conservatively (an ``uploaded`` promotes
    the ledger entry), so it is relayed before the worker is stopped."""
    rig, television, _ = scripted(tmp_path, markers("connected", "uploaded", "selected"), OK)
    result = rig.deliver(television)
    assert result.status is DeliveryStatus.PROTOCOL
    assert result.markers_seen == (Marker.CONNECTED, Marker.UPLOADED)
    assert [m.marker for m in rig.markers] == [Marker.CONNECTED, Marker.UPLOADED]


def test_a_repeated_marker_is_not_relayed_again(tmp_path: Path) -> None:
    rig, television, _ = scripted(tmp_path, markers("connected", "connected"), OK)
    result = rig.deliver(television)
    assert result.status is DeliveryStatus.PROTOCOL
    assert result.markers_seen == (Marker.CONNECTED,)
    assert len(rig.markers) == 1


@pytest.mark.parametrize(
    "events",
    [
        [{"token": NEW}, {"token": NEW}],
        [*markers("connected"), {"token": NEW}],
    ],
)
def test_a_token_only_once_and_only_before_connected(
    tmp_path: Path, events: list[JsonObject]
) -> None:
    rig, television, _ = scripted(tmp_path, events, OK)
    assert rig.deliver(television).status is DeliveryStatus.PROTOCOL


def test_a_token_event_is_installed_at_once(tmp_path: Path) -> None:
    rig, television, _ = scripted(tmp_path, [{"token": NEW}], WorkerError(WorkerErrorKind.CRASH))
    result = rig.deliver(television)
    assert (result.status, result.auth) == (DeliveryStatus.PROTOCOL, AuthChange.NEW_TOKEN)
    assert rig.tokens.load() == NEW


def test_a_new_token_wins_over_a_rejection(tmp_path: Path) -> None:
    rig, television, _ = scripted(
        tmp_path,
        [{"token": NEW}],
        {"status": "not_authorized", "detail": "", "pairing": "rejected"},
    )
    rig.tokens.install(STORED)
    assert rig.deliver(television).auth is AuthChange.NEW_TOKEN
    assert rig.tokens.load() == NEW


@pytest.mark.parametrize(
    ("events", "outcome"),
    [
        # ok needs "selected"
        (markers("connected", "upload_started", "uploaded"), OK),
        # an explicit refusal needs "uploaded", and never follows "selected"
        (
            markers("connected", "upload_started"),
            {"status": "refused", "detail": "", "pairing": None},
        ),
        (
            markers("connected", "upload_started", "uploaded", "selected"),
            {"status": "refused", "detail": "", "pairing": None},
        ),
        # these end before "upload_started"
        (
            markers("connected", "upload_started"),
            {"status": "not_authorized", "detail": "", "pairing": "prompt"},
        ),
        (
            markers("connected", "upload_started"),
            {"status": "unsupported", "detail": "", "pairing": None},
        ),
        (
            markers("connected", "upload_started"),
            {"status": "insufficient_time", "detail": "", "pairing": None},
        ),
        # a failure never follows "selected"
        (
            markers("connected", "upload_started", "uploaded", "selected"),
            {"status": "unreachable", "detail": "", "pairing": None},
        ),
        # a pairing only comes with not_authorized
        ([], {"status": "unreachable", "detail": "", "pairing": "rejected"}),
    ],
)
def test_a_result_that_does_not_fit_the_markers_is_a_protocol_failure(
    tmp_path: Path, events: list[JsonObject], outcome: JsonObject
) -> None:
    """The worker runs the third-party library: its status alone cannot, for
    example, remove the intent of an upload that may have arrived (§12.4)."""
    rig, television, _ = scripted(tmp_path, events, outcome)
    result = rig.deliver(television)
    assert result.status is DeliveryStatus.PROTOCOL
    assert "does not fit its markers" in result.detail


@pytest.mark.parametrize(
    ("events", "outcome", "status"),
    [
        (markers("connected", "upload_started", "uploaded", "selected"), OK, DeliveryStatus.OK),
        (
            markers("connected", "upload_started", "uploaded"),
            {"status": "refused", "detail": "", "pairing": None},
            DeliveryStatus.REFUSED,
        ),
        (
            [],
            {"status": "not_authorized", "detail": "", "pairing": "prompt"},
            DeliveryStatus.NOT_AUTHORIZED,
        ),
        (
            markers("connected"),
            {"status": "unsupported", "detail": "", "pairing": None},
            DeliveryStatus.UNSUPPORTED,
        ),
        (
            markers("connected", "upload_started"),
            {"status": "protocol", "detail": "", "pairing": None},
            DeliveryStatus.PROTOCOL,
        ),
    ],
)
def test_results_that_fit_the_markers_are_kept(
    tmp_path: Path, events: list[JsonObject], outcome: JsonObject, status: DeliveryStatus
) -> None:
    rig, television, _ = scripted(tmp_path, events, outcome)
    assert rig.deliver(television).status is status


@pytest.mark.parametrize(
    "outcome",
    [
        {"status": "teleported", "detail": "", "pairing": None},
        {"status": 1, "detail": "", "pairing": None},
        {"status": "ok", "detail": 5, "pairing": None},
        {"status": "not_authorized", "detail": "", "pairing": "sometimes"},
        {"status": "not_authorized", "detail": "", "pairing": 3},
        {"status": "unreachable", "detail": ""},
        {"status": "unreachable", "detail": "", "pairing": None, "extra": 1},
    ],
)
def test_a_result_that_is_not_understood_is_a_protocol_failure(
    tmp_path: Path, outcome: JsonObject
) -> None:
    rig, television, _ = scripted(tmp_path, [], outcome)
    result = rig.deliver(television)
    assert result.status is DeliveryStatus.PROTOCOL
    assert result.detail == "the television worker's result was not understood"


def test_the_timeout_is_the_deliver_deadline(tmp_path: Path) -> None:
    rig, television, executor = scripted(tmp_path, [], OK)
    television.deliver(rig.request(seconds=25), rig.markers.append)
    assert executor.timeouts == [25.0]


def test_the_detail_is_sanitized(tmp_path: Path) -> None:
    rig, television, _ = scripted(
        tmp_path,
        [],
        {"status": "unreachable", "detail": "line\nbreak " + "x" * 400, "pairing": None},
    )
    detail = rig.deliver(television).detail
    assert "\n" not in detail
    assert len(detail) <= 160
