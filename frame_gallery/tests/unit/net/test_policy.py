"""Host policies, URL and address validation, and header parsing (§10, D-108)."""

from __future__ import annotations

import re
from datetime import timedelta
from ipaddress import IPv6Address, ip_address
from typing import Any

import pytest

from frame_gallery.net.policy import (
    IMAGE_MAX_BYTES,
    METADATA_MAX_BYTES,
    RULES,
    HostPolicy,
    PolicyViolation,
    RequestKind,
    ValidatedUrl,
    check_header,
    content_length,
    https_url,
    is_private_address,
    is_public_address,
    media_type,
    path_segment,
    resolve_redirect,
    retry_after_seconds,
    validate_url,
)
from tests.support.clock import FAKE_EPOCH

POLICY = HostPolicy("demo", frozenset({"api.example.org", "cdn.example.org"}))


class TestHostPolicy:
    def test_valid_policy(self) -> None:
        policy = HostPolicy(
            "demo", frozenset({"api.example.org"}), 2.0, {"X-Courtesy": "Demo/1 (a@b.org)"}
        )
        assert policy.owns("api.example.org")
        assert not policy.owns("example.org")
        assert not policy.owns("API.example.org")  # hosts are compared after lower-casing
        assert policy.courtesy_headers["X-Courtesy"] == "Demo/1 (a@b.org)"
        with pytest.raises(TypeError):
            policy.courtesy_headers["X"] = "y"  # type: ignore[index]

    @pytest.mark.parametrize(
        "hosts",
        [
            frozenset(),
            frozenset({"localhost"}),
            frozenset({"API.example.org"}),
            frozenset({"api.example.org."}),
            frozenset({"-api.example.org"}),
            frozenset({"api_x.example.org"}),
            frozenset({"93.184.216.34"}),
            frozenset({"api.example.123"}),
            frozenset({"bücher.example"}),
            frozenset({"a" * 64 + ".example.org"}),
        ],
    )
    def test_bad_hosts_are_refused(self, hosts: frozenset[str]) -> None:
        with pytest.raises(ValueError, match="host"):
            HostPolicy("demo", hosts)

    @pytest.mark.parametrize("interval", [-1.0, float("inf"), float("nan")])
    def test_bad_intervals_are_refused(self, interval: float) -> None:
        with pytest.raises(ValueError, match="min_interval_s"):
            HostPolicy("demo", frozenset({"api.example.org"}), interval)

    @pytest.mark.parametrize(
        ("name", "value"),
        [("Bad Name", "x"), ("X-Ok", "line\r\nInjected: 1"), ("X-Ok", "tab\tvalue"), ("", "x")],
    )
    def test_courtesy_headers_are_checked(self, name: str, value: str) -> None:
        with pytest.raises(ValueError, match="invalid header"):
            HostPolicy("demo", frozenset({"api.example.org"}), 1.0, {name: value})

    def test_check_header_accepts_tokens_and_printable_values(self) -> None:
        check_header("AIC-User-Agent", "FrameGallery/1.0 (someone@example.invalid)")


class TestValidateUrl:
    @pytest.mark.parametrize(
        ("url", "host", "target"),
        [
            ("https://api.example.org/a/b?x=1&y=2", "api.example.org", "/a/b?x=1&y=2"),
            ("https://API.Example.org/a", "api.example.org", "/a"),
            ("https://api.example.org:443/a", "api.example.org", "/a"),
            ("https://api.example.org", "api.example.org", "/"),
            ("https://api.example.org?x=1", "api.example.org", "/?x=1"),
            ("https://cdn.example.org/p/%20q.jpg", "cdn.example.org", "/p/%20q.jpg"),
        ],
    )
    def test_accepted(self, url: str, host: str, target: str) -> None:
        validated = validate_url(url, POLICY)
        assert validated == ValidatedUrl(host=host, target=target)
        assert validated.url == f"https://{host}{target}"
        assert validated.path == target.split("?", 1)[0]

    @pytest.mark.parametrize(
        ("url", "reason"),
        [
            ("http://api.example.org/a", "only https"),
            ("ftp://api.example.org/a", "only https"),
            ("https://evil.example.net/a", "not in the demo host policy"),
            ("https://api.example.org.evil.net/a", "not in the demo host policy"),
            ("https://example.org/a", "not in the demo host policy"),
            ("https://user@api.example.org/a", "user information"),
            ("https://user:pw@api.example.org/a", "user information"),
            ("https://api.example.org:8443/a", "only port 443"),
            ("https://api.example.org:80/a", "only port 443"),
            ("https://api.example.org:/a", "unusual authority"),
            ("https://api.example.org:abc/a", "does not parse"),
            ("https://93.184.216.34/a", "IP-literal"),
            ("https://[2001:db8::1]/a", "IP-literal"),
            ("https://api.example.org/a#frag", "fragment"),
            ("https://api.example.org/a b", "printable ASCII"),
            ("https://api.example.org/a\\b", "printable ASCII"),
            ("https://api.example.org/ä", "printable ASCII"),
            ("https://api.example.org/\n", "printable ASCII"),
            ("", "printable ASCII"),
            ("https://api.example.org/" + "a" * 5000, "printable ASCII"),
            ("https://[::1/a", "does not parse"),
            ("https:///a", "not in the demo host policy"),
        ],
    )
    def test_refused(self, url: str, reason: str) -> None:
        with pytest.raises(PolicyViolation, match=re.escape(reason)):
            validate_url(url, POLICY)

    def test_non_string_is_refused(self) -> None:
        bad: Any = b"https://api.example.org/"
        with pytest.raises(PolicyViolation):
            validate_url(bad, POLICY)

    def test_redirects_are_resolved_and_validated(self) -> None:
        current = validate_url("https://api.example.org/a/b?q=1", POLICY)
        assert resolve_redirect(current, "/c", POLICY).target == "/c"
        assert resolve_redirect(current, "d?x=2", POLICY).target == "/a/d?x=2"
        assert resolve_redirect(current, "https://cdn.example.org/i.jpg", POLICY).host == (
            "cdn.example.org"
        )
        for location in ("http://api.example.org/a", "https://evil.example.net/", "//evil.net/x"):
            with pytest.raises(PolicyViolation):
                resolve_redirect(current, location, POLICY)
        for location in ("/a b", "", "/ä"):
            with pytest.raises(PolicyViolation, match="redirect location"):
                resolve_redirect(current, location, POLICY)


class TestBuilders:
    def test_https_url_encodes_the_query(self) -> None:
        url = https_url("api.example.org", "/s", [("q", 'a b&c=d/"'), ("n", "1")])
        assert url == "https://api.example.org/s?q=a%20b%26c%3Dd%2F%22&n=1"
        assert https_url("api.example.org", "/s") == "https://api.example.org/s"
        assert validate_url(url, POLICY).target.startswith("/s?q=")

    def test_https_url_rejects_bad_input(self) -> None:
        with pytest.raises(ValueError, match="host name"):
            https_url("Bad Host", "/s")
        with pytest.raises(ValueError, match="start with /"):
            https_url("api.example.org", "s")

    def test_path_segment_checks_then_encodes(self) -> None:
        pattern = re.compile(r"[a-z0-9-]+")
        assert path_segment("abc-1", pattern) == "abc-1"
        assert path_segment("a b", re.compile(r"[a-z ]+")) == "a%20b"
        for value in ("ABC", "a/b", "", "a\nb", "../x"):
            with pytest.raises(ValueError, match="does not match"):
                path_segment(value, pattern)


class TestAddresses:
    @pytest.mark.parametrize(
        "text",
        [
            "93.184.216.34",
            "8.8.8.8",
            "2606:4700:4700::1111",
            "::ffff:93.184.216.34",
        ],
    )
    def test_public(self, text: str) -> None:
        assert is_public_address(ip_address(text))

    @pytest.mark.parametrize(
        "text",
        [
            "127.0.0.1",
            "10.1.2.3",
            "172.16.0.1",
            "172.30.32.2",
            "192.168.1.1",
            "169.254.1.1",
            "100.64.0.1",
            "100.127.255.254",
            "0.0.0.0",  # noqa: S104 - an address value, not a bind
            "224.0.0.1",
            "239.255.255.250",
            "240.0.0.1",
            "255.255.255.255",
            "192.0.2.1",
            "198.51.100.1",
            "203.0.113.1",
            "::1",
            "::",
            "fe80::1",
            "fc00::1",
            "fd12:3456::1",
            "ff02::1",
            "2001:db8::1",
            "::ffff:127.0.0.1",
            "::ffff:10.0.0.1",
            "::ffff:169.254.0.1",
            "2002:0a00:0001::1",  # 6to4 around 10.0.0.1
            "2002:7f00:0001::1",  # 6to4 around 127.0.0.1
            "64:ff9b::a00:1",  # NAT64 around 10.0.0.1
            "64:ff9b::7f00:1",  # NAT64 around 127.0.0.1
            "2001:0:4136:e378:8000:63bf:3fff:fdd2",  # Teredo
            "fe80::1%eth0",
            "fec0::1",  # deprecated site-local
            "fec0:1:2::3",
            # Tunnelled forms are refused even around a public address.
            "2002:5db8:d822::1",  # 6to4 around 93.184.216.34
            "64:ff9b::5db8:d822",  # NAT64 around 93.184.216.34
        ],
    )
    def test_not_public(self, text: str) -> None:
        assert not is_public_address(ip_address(text))

    def test_teredo_client_is_checked(self) -> None:
        # Teredo encodes the client as the inverted last 32 bits.
        address = IPv6Address("2001:0:5db8:d822::a2b7:ffff")  # client 93.72.0.0
        assert address.teredo is not None
        assert not is_public_address(address)  # 2001::/32 itself is not global

    @pytest.mark.parametrize("text", ["172.30.32.2", "10.0.0.5", "192.168.1.9", "fd00::2"])
    def test_private(self, text: str) -> None:
        assert is_private_address(ip_address(text))

    @pytest.mark.parametrize(
        "text",
        [
            "93.184.216.34",
            "127.0.0.1",
            "169.254.1.1",
            "0.0.0.0",  # noqa: S104 - an address value, not a bind
            "::1",
            "fe80::1",
            "fe80::1%eth0",
            "ff02::1",
            "::ffff:93.184.216.34",
            "::ffff:127.0.0.1",
        ],
    )
    def test_not_private(self, text: str) -> None:
        assert not is_private_address(ip_address(text))

    def test_mapped_private(self) -> None:
        assert is_private_address(ip_address("::ffff:10.1.2.3"))


class TestHeaders:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("application/json", "application/json"),
            ("Application/JSON; charset=UTF-8", "application/json"),
            ("  image/jpeg ", "image/jpeg"),
            (None, None),
            ("", None),
            ("json", None),
            ("a/b/c", None),
            ("image/ jpeg", None),
            ("image/jpeg, image/png", None),
        ],
    )
    def test_media_type(self, value: str | None, expected: str | None) -> None:
        assert media_type(value) == expected

    def test_content_length(self) -> None:
        assert content_length(None) is None
        assert content_length(" 42 ") == 42
        assert content_length("0") == 0
        for value in ("-1", "1.0", "0x10", "1, 1", "", "12345678901"):
            with pytest.raises(ValueError, match="Content-Length"):
                content_length(value)

    def test_retry_after(self) -> None:
        now = FAKE_EPOCH
        assert retry_after_seconds(None, now) is None
        assert retry_after_seconds("3", now) == 3.0
        assert retry_after_seconds(" 0 ", now) == 0.0
        date = (now + timedelta(seconds=4)).strftime("%a, %d %b %Y %H:%M:%S GMT")
        assert retry_after_seconds(date, now) == pytest.approx(4.0)
        past = (now - timedelta(seconds=30)).strftime("%a, %d %b %Y %H:%M:%S GMT")
        assert retry_after_seconds(past, now) == 0.0
        for value in (
            "soon",
            "-1",
            "1.5",
            "",
            "Mon, 99 Foo 2026",
            "Thu, 31 Feb 2026 00:00:00 GMT",
            "Thu, 01 Jan 2026 25:00:00 GMT",
            "Thursday, 01-Jan-26 00:00:00 GMT",
            "Thu Jan  1 00:00:00 2026",
            "Thu, 01 Jan 2026 00:00:00 +0000",
        ):
            assert retry_after_seconds(value, now) is None


class TestRules:
    def test_kind_limits(self) -> None:
        metadata, image = RULES[RequestKind.METADATA], RULES[RequestKind.IMAGE]
        assert metadata.max_bytes == METADATA_MAX_BYTES == 2 * 1024 * 1024
        assert image.max_bytes == IMAGE_MAX_BYTES == 40 * 1024 * 1024
        assert (metadata.total_s, image.total_s) == (10.0, 20.0)
        assert metadata.retry
        assert not image.retry
        assert metadata.gzip_allowed
        assert not image.gzip_allowed
        assert image.accept_encoding == "identity"
        assert metadata.media_types == {"application/json"}
        assert image.media_types == {"image/jpeg", "image/png"}
