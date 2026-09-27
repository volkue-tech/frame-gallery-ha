"""The guarded gateway (§10, D-108, D-115) against a scripted transport."""

from __future__ import annotations

import errno
import gzip
import logging
import os
import stat
from ipaddress import ip_address
from pathlib import Path

import pytest

from frame_gallery.budget.allowance import Allowance, AllowanceExhausted
from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.net.gateway import Gateway, ProviderChannel
from frame_gallery.net.policy import HostPolicy
from frame_gallery.net.wire import FailureStage, TransportFailure
from frame_gallery.providers.contract import SourceError, SourceErrorKind
from frame_gallery.randomness import SeededRandomSource
from tests.support.clock import FakeClock
from tests.support.net import (
    PLACEHOLDER_CONTACT,
    PUBLIC_V4,
    PUBLIC_V4_B,
    TEST_IDENTITY,
    FakeResolver,
    FakeResponse,
    FakeTransport,
    connect_failure,
    image_response,
    json_response,
    status_response,
)

API = "api.example.org"
CDN = "cdn.example.org"
POLICY = HostPolicy(
    "demo", frozenset({API, CDN}), courtesy_headers={"X-Courtesy": "Demo/1 (courtesy)"}
)
URL = f"https://{API}/v1/search?q=secret-query"


class Rig:
    def __init__(self, *, allowance: int = 15, resolver: FakeResolver | None = None) -> None:
        self.clock = FakeClock()
        self.transport = FakeTransport(clock=self.clock)
        self.resolver = resolver or FakeResolver(clock=self.clock)
        self.gateway = Gateway(
            resolver=self.resolver,
            transport=self.transport,
            clock=self.clock,
            random=SeededRandomSource(7),
            identity=TEST_IDENTITY,
        )
        self.allowance = Allowance("metadata_requests", allowance)
        self.channel: ProviderChannel = self.gateway.channel(
            POLICY, metadata_allowance=self.allowance
        )

    def deadline(self, seconds: float = 30.0) -> Deadline:
        return Deadline.after(self.clock, seconds, "discovery")


@pytest.fixture
def rig() -> Rig:
    return Rig()


def _kind(excinfo: pytest.ExceptionInfo[SourceError]) -> SourceErrorKind:
    return excinfo.value.kind


class TestMetadataSuccess:
    def test_request_shape_and_result(self, rig: Rig) -> None:
        rig.transport.add(json_response({"data": [1, 2]}))
        assert rig.channel.get_json(URL, rig.deadline()) == {"data": [1, 2]}
        (call,) = rig.transport.calls
        request = call.request
        assert request.address == PUBLIC_V4
        assert (request.host, request.port, request.tls) == (API, 443, True)
        assert request.target == "/v1/search?q=secret-query"
        assert dict(request.headers) == {
            "Host": API,
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "User-Agent": f"FrameGallery/0.0.0-test (contact: {PLACEHOLDER_CONTACT})",
            "Connection": "close",
            "X-Courtesy": "Demo/1 (courtesy)",
        }
        assert call.connect_timeout == 5.0
        assert call.exchange_timeout == 10.0
        assert rig.resolver.calls == [(API, 443, 3.0)]
        assert rig.transport.opened[0].closed
        assert rig.channel.metadata_requests == 1
        assert rig.channel.policy is POLICY
        assert not rig.channel.stopped

    def test_gzip_is_decoded(self, rig: Rig) -> None:
        rig.transport.add(json_response({"ok": True}, gzipped=True))
        assert rig.channel.get_json(URL, rig.deadline()) == {"ok": True}

    def test_chunked_reads_are_joined(self, rig: Rig) -> None:
        response = json_response({"text": "x" * 5000})
        response.chunk = 7
        rig.transport.add(response)
        assert rig.channel.get_json(URL, rig.deadline()) == {"text": "x" * 5000}
        assert all(amount == 64 * 1024 for amount, _timeout in response.reads)
        assert all(timeout == 10.0 for _amount, timeout in response.reads)

    def test_body_without_declared_length(self, rig: Rig) -> None:
        rig.transport.add(FakeResponse(headers={"Content-Type": "application/json"}, body=b"[1]"))
        assert rig.channel.get_json(URL, rig.deadline()) == [1]

    def test_logs_omit_the_query(self, rig: Rig, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.DEBUG, logger="frame_gallery.net")
        rig.transport.add(status_response(302, {"Location": "/v1/other?token=abc"}))
        rig.transport.add(json_response({}))
        rig.channel.get_json(URL, rig.deadline())
        text = caplog.text
        assert f"{API}/v1/search -> 302 redirect" in text
        assert f"{API}/v1/other -> 200" in text
        assert "secret-query" not in text
        assert "token" not in text
        assert PLACEHOLDER_CONTACT not in text


class TestAllowanceAndPacing:
    def test_every_wire_request_takes_one_unit(self) -> None:
        rig = Rig(allowance=2)
        rig.transport.add(json_response({}), json_response({}))
        rig.channel.get_json(URL, rig.deadline())
        rig.channel.get_json(URL, rig.deadline())
        with pytest.raises(AllowanceExhausted):
            rig.channel.get_json(URL, rig.deadline())
        assert len(rig.transport.calls) == 2
        assert rig.channel.metadata_requests == 2

    def test_downloads_do_not_use_the_metadata_allowance(self, tmp_path: Path) -> None:
        rig = Rig(allowance=0)
        rig.transport.add(image_response(b"\xff\xd8jpeg"))
        rig.channel.download(f"https://{CDN}/a.jpg", tmp_path / "a", rig.deadline())
        assert rig.allowance.used == 0

    def test_requests_are_spaced_start_to_start(self, rig: Rig) -> None:
        rig.transport.add(json_response({}), json_response({}), json_response({}))
        rig.channel.get_json(URL, rig.deadline())
        rig.clock.advance(0.25)
        rig.channel.get_json(URL, rig.deadline())
        assert rig.clock.sleeps == [pytest.approx(0.75)]
        rig.clock.advance(5.0)
        rig.channel.get_json(URL, rig.deadline())
        assert len(rig.clock.sleeps) == 1

    def test_pacing_that_does_not_fit_the_deadline(self, rig: Rig) -> None:
        rig.transport.add(json_response({}))
        rig.channel.get_json(URL, rig.deadline())
        with pytest.raises(DeadlineExceeded):
            rig.channel.get_json(URL, rig.deadline(0.5))
        assert len(rig.transport.calls) == 1

    def test_pacing_longer_than_the_request_limit_is_a_timeout(self) -> None:
        rig = Rig()
        slow = HostPolicy("slow", frozenset({API}), min_interval_s=12.0)
        channel = rig.gateway.channel(slow, metadata_allowance=Allowance("m", 5))
        rig.transport.add(json_response({}))
        channel.get_json(URL, rig.deadline())
        with pytest.raises(SourceError) as excinfo:
            channel.get_json(URL, rig.deadline(60))
        assert _kind(excinfo) is SourceErrorKind.TIMEOUT

    def test_redirects_are_paced_and_counted(self, rig: Rig) -> None:
        rig.transport.add(status_response(301, {"Location": f"https://{CDN}/x"}))
        rig.transport.add(json_response({}))
        rig.channel.get_json(URL, rig.deadline())
        assert rig.transport.targets == [f"{API}/v1/search?q=secret-query", f"{CDN}/x"]
        assert rig.clock.sleeps == [pytest.approx(1.0)]
        assert rig.channel.metadata_requests == 2


class TestStops:
    @pytest.mark.parametrize("status", [401, 403])
    def test_stop_statuses(self, rig: Rig, status: int, caplog: pytest.LogCaptureFixture) -> None:
        rig.transport.add(status_response(status))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.STOPPED
        assert rig.channel.stopped
        assert f"HTTP {status}" in caplog.text
        with pytest.raises(SourceError) as again:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(again) is SourceErrorKind.STOPPED
        assert len(rig.transport.calls) == 1
        assert rig.allowance.used == 1

    def test_a_stop_also_blocks_downloads(self, rig: Rig, tmp_path: Path) -> None:
        rig.transport.add(status_response(403))
        with pytest.raises(SourceError):
            rig.channel.get_json(URL, rig.deadline())
        with pytest.raises(SourceError) as excinfo:
            rig.channel.download(f"https://{CDN}/a.jpg", tmp_path / "a", rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.STOPPED
        assert not (tmp_path / "a").exists()

    def test_image_403_stops(self, rig: Rig, tmp_path: Path) -> None:
        rig.transport.add(status_response(403))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.download(f"https://{CDN}/a.jpg", tmp_path / "a", rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.STOPPED
        assert rig.channel.stopped

    @pytest.mark.parametrize("retry_after", [None, "6", "later", "Wed, 01 Jan 2031 00:00:00 GMT"])
    def test_429_without_a_short_retry_after_stops(self, rig: Rig, retry_after: str | None) -> None:
        headers = {} if retry_after is None else {"Retry-After": retry_after}
        rig.transport.add(status_response(429, headers))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.STOPPED
        assert rig.channel.stopped
        assert len(rig.transport.calls) == 1

    @pytest.mark.parametrize(("retry_after", "minimum"), [("2", 2.0), ("0", 1.0), ("5", 5.0)])
    def test_429_with_a_short_retry_after_is_retried_once(
        self, rig: Rig, retry_after: str, minimum: float
    ) -> None:
        rig.transport.add(status_response(429, {"Retry-After": retry_after}))
        rig.transport.add(json_response({"ok": 1}))
        assert rig.channel.get_json(URL, rig.deadline()) == {"ok": 1}
        (wait,) = rig.clock.sleeps
        assert minimum <= wait <= minimum + 0.25
        assert not rig.channel.stopped
        assert rig.allowance.used == 2

    def test_a_second_429_stops(self, rig: Rig, caplog: pytest.LogCaptureFixture) -> None:
        rig.transport.add(status_response(429, {"Retry-After": "1"}))
        rig.transport.add(status_response(429, {"Retry-After": "1"}))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.STOPPED
        assert rig.channel.stopped
        assert "429 without a permitted retry" in caplog.text

    def test_a_429_retry_that_does_not_fit_the_deadline_stops(self, rig: Rig) -> None:
        rig.transport.add(status_response(429, {"Retry-After": "4"}))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline(6))
        assert _kind(excinfo) is SourceErrorKind.STOPPED
        assert rig.channel.stopped
        assert rig.clock.sleeps == []

    def test_a_429_retry_needs_an_allowance_unit(self) -> None:
        rig = Rig(allowance=1)
        rig.transport.add(status_response(429, {"Retry-After": "1"}))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.STOPPED

    def test_image_429_is_never_retried(self, rig: Rig, tmp_path: Path) -> None:
        rig.transport.add(status_response(429, {"Retry-After": "1"}))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.download(f"https://{CDN}/a.jpg", tmp_path / "a", rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.STOPPED
        assert rig.channel.stopped


class TestRetries:
    @pytest.mark.parametrize("status", [502, 503, 504])
    def test_gateway_errors_are_retried_once(self, rig: Rig, status: int) -> None:
        rig.transport.add(status_response(status), json_response([]))
        assert rig.channel.get_json(URL, rig.deadline()) == []
        (wait,) = rig.clock.sleeps
        assert 1.0 <= wait <= 1.25

    def test_a_second_gateway_error_fails(self, rig: Rig) -> None:
        rig.transport.add(status_response(503), status_response(502))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.HTTP_ERROR
        assert not rig.channel.stopped

    @pytest.mark.parametrize("status", [500, 400, 204, 206, 304, 418])
    def test_other_statuses_are_not_retried(self, rig: Rig, status: int) -> None:
        rig.transport.add(status_response(status))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.HTTP_ERROR
        assert len(rig.transport.calls) == 1

    def test_connect_failure_is_retried_once(self, rig: Rig) -> None:
        rig.transport.add(connect_failure(), json_response({}))
        assert rig.channel.get_json(URL, rig.deadline()) == {}
        assert len(rig.transport.calls) == 2

    def test_two_connect_failures(self, rig: Rig) -> None:
        rig.transport.add(connect_failure(), connect_failure())
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.TRANSPORT
        assert "connect" in str(excinfo.value)

    def test_the_next_address_is_tried_before_a_retry(self) -> None:
        rig = Rig(resolver=FakeResolver(default=(PUBLIC_V4, PUBLIC_V4_B)))
        rig.transport.add(connect_failure(), json_response({}))
        rig.channel.get_json(URL, rig.deadline())
        assert [call.request.address for call in rig.transport.calls] == [PUBLIC_V4, PUBLIC_V4_B]
        assert rig.allowance.used == 1
        assert rig.clock.sleeps == []

    def test_at_most_four_addresses_are_tried(self) -> None:
        addresses = tuple(PUBLIC_V4 + offset for offset in range(6))
        rig = Rig(resolver=FakeResolver(default=addresses))
        rig.transport.add(*(connect_failure() for _ in range(8)))
        with pytest.raises(SourceError):
            rig.channel.get_json(URL, rig.deadline())
        assert len(rig.transport.calls) == 8  # 4 per attempt, 2 attempts

    def test_resolution_failure_is_retried(self) -> None:
        failing = TransportFailure(FailureStage.RESOLVE, "gaierror")
        rig = Rig(resolver=FakeResolver({API: failing}))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.TRANSPORT
        assert "name resolution" in str(excinfo.value)
        assert len(rig.resolver.calls) == 2
        assert rig.transport.calls == []

    def test_download_failures_are_not_retried(self, rig: Rig, tmp_path: Path) -> None:
        rig.transport.add(connect_failure())
        with pytest.raises(SourceError) as excinfo:
            rig.channel.download(f"https://{CDN}/a.jpg", tmp_path / "a", rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.TRANSPORT
        assert len(rig.transport.calls) == 1
        rig.transport.add(status_response(503))
        with pytest.raises(SourceError) as again:
            rig.channel.download(f"https://{CDN}/a.jpg", tmp_path / "b", rig.deadline())
        assert _kind(again) is SourceErrorKind.HTTP_ERROR

    def test_exchange_failures_are_not_retried(self, rig: Rig) -> None:
        rig.transport.add(TransportFailure(FailureStage.EXCHANGE, "reset"))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.TRANSPORT
        assert len(rig.transport.calls) == 1


class TestAddressesAndUrls:
    @pytest.mark.parametrize(
        "addresses",
        [
            ("10.0.0.1",),
            ("93.184.216.34", "127.0.0.1"),
            ("::ffff:192.168.0.1",),
            ("169.254.169.254",),
        ],
    )
    def test_non_public_answers_are_refused(self, addresses: tuple[str, ...]) -> None:
        rig = Rig(resolver=FakeResolver(default=tuple(ip_address(a) for a in addresses)))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.TRANSPORT
        assert "non-public" in str(excinfo.value)
        assert rig.transport.calls == []
        assert len(rig.resolver.calls) == 1

    def test_an_empty_answer_is_refused(self) -> None:
        rig = Rig(resolver=FakeResolver(default=()))
        with pytest.raises(SourceError, match="non-public"):
            rig.channel.get_json(URL, rig.deadline())

    @pytest.mark.parametrize(
        "url",
        [
            "http://api.example.org/x",
            "https://evil.example.net/x",
            "https://api.example.org:8443/x",
            "https://93.184.216.34/x",
        ],
    )
    def test_urls_outside_the_policy_are_refused(self, rig: Rig, url: str) -> None:
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(url, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.UNEXPECTED_FORMAT
        assert rig.resolver.calls == []
        assert rig.allowance.used == 0


class TestRedirects:
    def test_relative_redirect(self, rig: Rig) -> None:
        rig.transport.add(status_response(307, {"Location": "next?page=2"}), json_response(1))
        assert rig.channel.get_json(URL, rig.deadline()) == 1
        assert rig.transport.targets[-1] == f"{API}/v1/next?page=2"

    def test_three_redirects_are_followed(self, rig: Rig) -> None:
        for _ in range(3):
            rig.transport.add(status_response(308, {"Location": "/again"}))
        rig.transport.add(json_response("done"))
        assert rig.channel.get_json(URL, rig.deadline()) == "done"

    def test_a_fourth_redirect_fails(self, rig: Rig) -> None:
        for _ in range(4):
            rig.transport.add(status_response(302, {"Location": "/again"}))
        with pytest.raises(SourceError, match="too many redirects") as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.HTTP_ERROR
        assert all(response.closed for response in rig.transport.opened)

    @pytest.mark.parametrize(
        "location",
        ["https://evil.example.net/x", "http://api.example.org/x", "https://10.0.0.1/", "/a b"],
    )
    def test_redirects_outside_the_policy_fail(self, rig: Rig, location: str) -> None:
        rig.transport.add(status_response(303, {"Location": location}))
        with pytest.raises(SourceError, match="redirect is outside") as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.HTTP_ERROR
        assert len(rig.transport.calls) == 1

    def test_a_redirect_without_location_fails(self, rig: Rig) -> None:
        rig.transport.add(status_response(301))
        with pytest.raises(SourceError, match="without a location"):
            rig.channel.get_json(URL, rig.deadline())


class TestBodies:
    @pytest.mark.parametrize(
        ("headers", "fragment"),
        [
            ({"Content-Type": "text/html"}, "media type"),
            ({}, "media type"),
            ({"Content-Type": "application/json", "Content-Encoding": "br"}, "encoding"),
            ({"Content-Type": "application/json", "Content-Encoding": "gzip, gzip"}, "encoding"),
            ({"Content-Type": "application/json", "Content-Length": "1, 1"}, "Content-Length"),
            ({"Content-Type": "application/json", "Content-Length": "-3"}, "Content-Length"),
        ],
    )
    def test_header_checks(self, rig: Rig, headers: dict[str, str], fragment: str) -> None:
        rig.transport.add(FakeResponse(headers=headers, body=b"{}"))
        with pytest.raises(SourceError, match=fragment) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.UNEXPECTED_FORMAT
        assert rig.transport.opened[0].closed

    def test_declared_length_over_the_cap(self, rig: Rig) -> None:
        headers = {"Content-Type": "application/json", "Content-Length": str(2 * 1024 * 1024 + 1)}
        rig.transport.add(FakeResponse(headers=headers))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.OVER_CAP
        assert rig.transport.opened[0].reads == []

    def test_body_over_the_cap(self, rig: Rig) -> None:
        body = b"[" + b"1," * (1024 * 1024) + b"1]"
        rig.transport.add(FakeResponse(headers={"Content-Type": "application/json"}, body=body))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.OVER_CAP

    def test_body_exactly_at_the_cap(self, rig: Rig) -> None:
        body = b'"' + b"a" * (2 * 1024 * 1024 - 2) + b'"'
        rig.transport.add(FakeResponse(headers={"Content-Type": "application/json"}, body=body))
        assert len(rig.channel.get_json(URL, rig.deadline())) == 2 * 1024 * 1024 - 2  # type: ignore[arg-type]

    def test_gzip_bomb(self, rig: Rig) -> None:
        body = gzip.compress(b"[" + b" " * (8 * 1024 * 1024) + b"]")
        assert len(body) < 2 * 1024 * 1024
        rig.transport.add(
            FakeResponse(
                headers={"Content-Type": "application/json", "Content-Encoding": "gzip"},
                body=body,
            )
        )
        with pytest.raises(SourceError, match="decoded body over the cap") as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.OVER_CAP

    def test_gzip_exactly_one_byte_over_the_cap(self, rig: Rig) -> None:
        # Small reads: the decoder never has input left over when it overflows.
        body = gzip.compress(b'"' + b"a" * (2 * 1024 * 1024 - 1) + b'"')
        response = FakeResponse(
            headers={"Content-Type": "application/json", "Content-Encoding": "gzip"},
            body=body,
            chunk=16,
        )
        rig.transport.add(response)
        with pytest.raises(SourceError, match="decoded body over the cap"):
            rig.channel.get_json(URL, rig.deadline())

    def test_gzip_decoded_size_over_the_cap_in_one_step(self, rig: Rig) -> None:
        # The whole bomb arrives in one read, so the decoder stops with input left.
        body = gzip.compress(b"[" + b" " * (3 * 1024 * 1024) + b"]")
        response = FakeResponse(
            headers={"Content-Type": "application/json", "Content-Encoding": "gzip"}, body=body
        )
        rig.transport.add(response)
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.OVER_CAP

    @pytest.mark.parametrize(
        ("body", "fragment"),
        [
            (gzip.compress(b"[1]")[:-4], "truncated gzip"),
            (gzip.compress(b"[1]") + gzip.compress(b"[2]"), "data after the gzip body"),
            (gzip.compress(b"[1]") + b"junk", "data after the gzip body"),
            (b"\x1f\x8b\x08\x00garbage-garbage", "invalid gzip"),
        ],
    )
    def test_bad_gzip(self, rig: Rig, body: bytes, fragment: str) -> None:
        rig.transport.add(
            FakeResponse(
                headers={"Content-Type": "application/json", "Content-Encoding": "gzip"},
                body=body,
            )
        )
        with pytest.raises(SourceError, match=fragment) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.UNEXPECTED_FORMAT

    def test_data_after_a_complete_gzip_member_in_a_later_read(self, rig: Rig) -> None:
        member = gzip.compress(b"[1]")
        response = FakeResponse(
            headers={"Content-Type": "application/json", "Content-Encoding": "gzip"},
            body=member + b"more",
            chunk=len(member),
        )
        rig.transport.add(response)
        with pytest.raises(SourceError, match="data after the gzip body"):
            rig.channel.get_json(URL, rig.deadline())

    def test_short_body(self, rig: Rig) -> None:
        rig.transport.add(
            FakeResponse(
                headers={"Content-Type": "application/json", "Content-Length": "10"}, body=b"{}"
            )
        )
        with pytest.raises(SourceError, match="shorter than declared") as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.TRANSPORT

    @pytest.mark.parametrize(
        "body",
        [b"{", b"NaN", b"[Infinity]", b"\xff\xfe", b"[" * 100_000 + b"]" * 100_000, b""],
    )
    def test_invalid_json(self, rig: Rig, body: bytes) -> None:
        rig.transport.add(FakeResponse(headers={"Content-Type": "application/json"}, body=body))
        with pytest.raises(SourceError, match="not valid JSON") as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.UNEXPECTED_FORMAT

    def test_read_failure(self, rig: Rig) -> None:
        response = json_response({"a": 1})
        response.fail_after_reads = 0
        rig.transport.add(response)
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.TRANSPORT
        assert response.closed


class TestTime:
    def test_slow_body_hits_the_request_limit(self, rig: Rig) -> None:
        response = json_response({"text": "y" * 100})
        response.chunk = 10
        response.read_delay = 3.0
        rig.transport.add(response)
        with pytest.raises(SourceError, match="time limit") as excinfo:
            rig.channel.get_json(URL, rig.deadline(60))
        assert _kind(excinfo) is SourceErrorKind.TIMEOUT
        assert response.closed
        # Each read waits at most what remains of the request's 10 s.
        timeouts = [timeout for _amount, timeout in response.reads]
        assert timeouts[0] == 10.0
        assert timeouts == sorted(timeouts, reverse=True)

    def test_slow_body_hits_the_callers_deadline(self, rig: Rig) -> None:
        response = json_response({"text": "y" * 100})
        response.chunk = 10
        response.read_delay = 3.0
        rig.transport.add(response)
        with pytest.raises(DeadlineExceeded):
            rig.channel.get_json(URL, rig.deadline(5))

    def test_a_stalled_read_is_a_timeout(self, rig: Rig) -> None:
        response = json_response({})
        response.fail_after_reads = 0
        response.failure = TransportFailure(FailureStage.EXCHANGE, "stall", timed_out=True)
        rig.transport.add(response)
        with pytest.raises(SourceError, match="stopped responding") as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.TIMEOUT

    def test_a_timed_out_read_after_the_limit(self, rig: Rig) -> None:
        response = json_response({})
        response.fail_after_reads = 0
        response.read_delay = 10.0
        response.failure = TransportFailure(FailureStage.EXCHANGE, "stall", timed_out=True)
        rig.transport.add(response)
        with pytest.raises(SourceError, match="time limit") as excinfo:
            rig.channel.get_json(URL, rig.deadline(60))
        assert _kind(excinfo) is SourceErrorKind.TIMEOUT

    def test_connect_timeouts_until_the_limit(self) -> None:
        clock_rig = Rig()

        def slow_failure(request: object) -> FakeResponse:
            clock_rig.clock.advance(10.0)
            raise connect_failure(timed_out=True)

        clock_rig.transport.add(slow_failure)
        with pytest.raises(SourceError) as excinfo:
            clock_rig.channel.get_json(URL, clock_rig.deadline(60))
        assert _kind(excinfo) is SourceErrorKind.TIMEOUT

    def test_a_connect_timeout_before_the_limit_is_retried(self, rig: Rig) -> None:
        rig.transport.add(connect_failure(timed_out=True), json_response({}))
        assert rig.channel.get_json(URL, rig.deadline()) == {}

    def test_resolution_timeout_at_the_limit(self) -> None:
        clock = FakeClock()
        failure = TransportFailure(FailureStage.RESOLVE, "timed out", timed_out=True)
        resolver = FakeResolver({API: failure}, clock=clock, delay=3.0)
        rig = Rig(resolver=resolver)
        rig.clock = clock
        rig.gateway = Gateway(
            resolver=resolver,
            transport=rig.transport,
            clock=clock,
            random=SeededRandomSource(1),
            identity=TEST_IDENTITY,
        )
        channel = rig.gateway.channel(POLICY, metadata_allowance=Allowance("m", 5))
        with pytest.raises(DeadlineExceeded):
            channel.get_json(URL, Deadline.after(clock, 3.0, "discovery"))

    def test_no_time_left_at_all(self, rig: Rig) -> None:
        deadline = rig.deadline(1)
        rig.clock.advance(1)
        with pytest.raises(DeadlineExceeded):
            rig.channel.get_json(URL, deadline)

    def test_a_retry_needs_time_for_the_wait_and_a_connect(self, rig: Rig) -> None:
        rig.transport.add(status_response(503))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline(5))
        assert _kind(excinfo) is SourceErrorKind.HTTP_ERROR
        assert len(rig.transport.calls) == 1


class TestDownload:
    def test_a_file_whose_mode_cannot_be_set_is_removed(
        self, rig: Rig, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def refuse(_fd: int, _mode: int) -> None:
            raise PermissionError(errno.EPERM, "not permitted")

        monkeypatch.setattr(os, "fchmod", refuse)
        target = tmp_path / "source-0.bin"
        with pytest.raises(PermissionError):
            rig.channel.download(f"https://{CDN}/i/a.png", target, rig.deadline())
        assert not target.exists()
        assert rig.transport.calls == []

    def test_writes_a_new_file_the_worker_group_can_read(self, rig: Rig, tmp_path: Path) -> None:
        body = b"\x89PNG\r\n\x1a\n" + b"p" * 1000
        rig.transport.add(image_response(body, "image/png"))
        target = tmp_path / "source-0.bin"
        result = rig.channel.download(f"https://{CDN}/i/a.png", target, rig.deadline())
        assert result.path == target
        assert result.size_bytes == len(body)
        assert result.media_type == "image/png"
        assert target.read_bytes() == body
        assert stat.S_IMODE(target.stat().st_mode) == 0o640  # D-164
        request = rig.transport.calls[0].request
        assert request.headers["Accept"] == "image/jpeg, image/png"
        assert request.headers["Accept-Encoding"] == "identity"
        assert rig.transport.calls[0].exchange_timeout == 20.0

    @pytest.mark.parametrize("status", [404, 410])
    def test_missing_images_are_not_found(self, rig: Rig, tmp_path: Path, status: int) -> None:
        rig.transport.add(status_response(status))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.download(f"https://{CDN}/a.jpg", tmp_path / "a", rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.NOT_FOUND
        assert not (tmp_path / "a").exists()

    @pytest.mark.parametrize("status", [404, 410])
    def test_missing_metadata_is_an_http_error(self, rig: Rig, status: int) -> None:
        rig.transport.add(status_response(status))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.get_json(URL, rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.HTTP_ERROR

    def test_partial_file_is_removed(self, rig: Rig, tmp_path: Path) -> None:
        response = image_response(b"\xff\xd8" + b"j" * 100_000)
        response.chunk = 1000
        response.fail_after_reads = 3
        rig.transport.add(response)
        with pytest.raises(SourceError):
            rig.channel.download(f"https://{CDN}/a.jpg", tmp_path / "a", rig.deadline())
        assert list(tmp_path.iterdir()) == []

    def test_gzip_images_are_refused(self, rig: Rig, tmp_path: Path) -> None:
        response = image_response(b"\xff\xd8jpeg")
        response.headers = {**response.headers, "Content-Encoding": "gzip"}
        rig.transport.add(response)
        with pytest.raises(SourceError, match="encoding"):
            rig.channel.download(f"https://{CDN}/a.jpg", tmp_path / "a", rig.deadline())

    def test_non_image_media_types_are_refused(self, rig: Rig, tmp_path: Path) -> None:
        rig.transport.add(image_response(b"<html>", "text/html"))
        with pytest.raises(SourceError) as excinfo:
            rig.channel.download(f"https://{CDN}/a.jpg", tmp_path / "a", rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.UNEXPECTED_FORMAT
        assert not (tmp_path / "a").exists()

    def test_oversized_images(self, rig: Rig, tmp_path: Path) -> None:
        response = image_response(b"")
        response.headers = {"Content-Type": "image/jpeg", "Content-Length": str(40 * 2**20 + 1)}
        rig.transport.add(response)
        with pytest.raises(SourceError) as excinfo:
            rig.channel.download(f"https://{CDN}/a.jpg", tmp_path / "a", rig.deadline())
        assert _kind(excinfo) is SourceErrorKind.OVER_CAP

    def test_existing_destination_is_never_overwritten(self, rig: Rig, tmp_path: Path) -> None:
        target = tmp_path / "a"
        target.write_bytes(b"keep")
        with pytest.raises(FileExistsError):
            rig.channel.download(f"https://{CDN}/a.jpg", target, rig.deadline())
        assert target.read_bytes() == b"keep"
        assert rig.transport.calls == []

    def test_symlinked_destination_is_refused(self, rig: Rig, tmp_path: Path) -> None:
        outside = tmp_path / "outside"
        (tmp_path / "a").symlink_to(outside)
        with pytest.raises(FileExistsError):
            rig.channel.download(f"https://{CDN}/a.jpg", tmp_path / "a", rig.deadline())
        assert not outside.exists()
