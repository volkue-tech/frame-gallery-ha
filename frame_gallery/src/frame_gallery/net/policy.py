"""Host policies and request rules of the guarded gateway (§10, D-108, D-115).

Everything here is pure: URL and address validation, header parsing, and the
per-kind limits. Nothing performs I/O.
"""

from __future__ import annotations

import enum
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network, ip_address
from types import MappingProxyType
from typing import Final
from urllib.parse import quote, urljoin, urlsplit

from frame_gallery.budget.limits import DOWNLOAD_REQUEST_S, METADATA_REQUEST_S
from frame_gallery.imaging.contract import MAX_SOURCE_BYTES
from frame_gallery.net.wire import IPAddress

HTTPS_PORT: Final = 443
MAX_REDIRECTS: Final = 3
MIN_INTERVAL_S: Final = 1.0
"""Pacing for both museums (D-115); the Art Institute's documented scraping rate."""

RETRY_AFTER_MAX_S: Final = 5.0
"""A 429 is retried only if it asks for at most this long (D-115)."""

RETRY_WAIT_MIN_S: Final = 1.0
RETRY_JITTER_S: Final = 0.25

METADATA_MAX_BYTES: Final = 2 * 1024 * 1024
IMAGE_MAX_BYTES: Final = MAX_SOURCE_BYTES
URL_MAX_LENGTH: Final = 4096
MAX_ADDRESSES: Final = 4
"""Resolved addresses tried per request, in resolver order."""

REDIRECT_STATUSES: Final = frozenset({301, 302, 303, 307, 308})
STOP_STATUSES: Final = frozenset({401, 403})
"""Statuses that stop all traffic to a provider for the run (D-115, D-136). A
429 stops too, unless its single retry is permitted."""

RETRY_STATUSES: Final = frozenset({502, 503, 504})
TOO_MANY_REQUESTS: Final = 429
MISSING_STATUSES: Final = frozenset({404, 410})

_LABEL: Final = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", re.ASCII)
_TOKEN: Final = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+", re.ASCII)
_HEADER_VALUE: Final = re.compile(r"[\x20-\x7e]*", re.ASCII)
_URL_CHARACTERS: Final = re.compile(r"[\x21-\x7e]+", re.ASCII)
"""Printable ASCII without the space; a backslash is refused separately."""

_DIGITS: Final = re.compile(r"[0-9]{1,10}", re.ASCII)
_MONTHS: Final = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)
_IMF_FIXDATE: Final = re.compile(
    r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun), ([0-9]{2}) (" + "|".join(_MONTHS) + r") "
    r"([0-9]{4}) ([0-9]{2}):([0-9]{2}):([0-9]{2}) GMT",
    re.ASCII,
)
"""The HTTP-date format senders must generate (RFC 9110 §5.6.7). The obsolete
formats are treated as invalid. (``email.utils`` would load ``socket``.)"""
_NAT64: Final = IPv6Network("64:ff9b::/96")
_SHARED_ADDRESS_SPACE: Final = IPv4Network("100.64.0.0/10")


class RequestKind(enum.StrEnum):
    METADATA = "metadata"
    IMAGE = "image"


@dataclass(frozen=True, slots=True)
class KindRules:
    """The limits of one request kind (§10)."""

    max_bytes: int
    """Cap on the decoded body, and on the bytes received."""

    total_s: float
    """Per-request total (D-108)."""

    media_types: frozenset[str]
    accept: str
    accept_encoding: str
    gzip_allowed: bool
    """One gzip layer may be decoded (metadata only)."""

    retry: bool
    """A single retry is permitted (metadata only, D-115)."""


RULES: Final[Mapping[RequestKind, KindRules]] = MappingProxyType(
    {
        RequestKind.METADATA: KindRules(
            max_bytes=METADATA_MAX_BYTES,
            total_s=METADATA_REQUEST_S,
            media_types=frozenset({"application/json"}),
            accept="application/json",
            accept_encoding="gzip",
            gzip_allowed=True,
            retry=True,
        ),
        RequestKind.IMAGE: KindRules(
            max_bytes=IMAGE_MAX_BYTES,
            total_s=DOWNLOAD_REQUEST_S,
            media_types=frozenset({"image/jpeg", "image/png"}),
            accept="image/jpeg, image/png",
            accept_encoding="identity",
            gzip_allowed=False,
            retry=False,
        ),
    }
)


class PolicyViolation(ValueError):
    """A URL or address that the host policy refuses. The message is log-safe."""


def _check_host_name(host: str) -> None:
    labels = host.split(".")
    if (
        len(host) > 253
        or len(labels) < 2
        or not all(_LABEL.fullmatch(part) for part in labels)
        or labels[-1].isdigit()
    ):
        msg = f"not a lowercase DNS host name: {host!r}"
        raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class HostPolicy:
    """What one provider may reach (§10): exact host names, HTTPS on 443."""

    provider_key: str
    hosts: frozenset[str]
    min_interval_s: float = MIN_INTERVAL_S
    courtesy_headers: Mapping[str, str] = field(default_factory=dict)
    """Headers a provider asks for, such as ``AIC-User-Agent`` (D-119)."""

    def __post_init__(self) -> None:
        if not self.hosts:
            msg = "a host policy needs at least one host"
            raise ValueError(msg)
        for host in self.hosts:
            _check_host_name(host)
        if not math.isfinite(self.min_interval_s) or self.min_interval_s < 0:
            msg = "min_interval_s must be a finite, non-negative number"
            raise ValueError(msg)
        for name, value in self.courtesy_headers.items():
            check_header(name, value)
        object.__setattr__(self, "courtesy_headers", MappingProxyType(dict(self.courtesy_headers)))

    def owns(self, host: str) -> bool:
        """Whether ``host`` (already lowercase) is one of this policy's hosts."""
        return host in self.hosts


def check_header(name: str, value: str) -> None:
    """Refuse a header name that is not a token, or a value with control
    characters (no header injection)."""
    if _TOKEN.fullmatch(name) is None or _HEADER_VALUE.fullmatch(value) is None:
        msg = f"invalid header {name!r}"
        raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ValidatedUrl:
    """A URL the host policy allows."""

    host: str
    target: str
    """Path and query, starting with ``/``."""

    @property
    def url(self) -> str:
        return f"https://{self.host}{self.target}"

    @property
    def path(self) -> str:
        """The target without its query: what may be logged (§10)."""
        return self.target.split("?", 1)[0]


def validate_url(url: str, policy: HostPolicy) -> ValidatedUrl:
    """Check ``url`` against ``policy``: ``https``, port 443, one of the
    policy's exact host names, no user information, no IP literal, and no
    fragment. Raises :class:`PolicyViolation`."""
    if (
        not isinstance(url, str)
        or len(url) > URL_MAX_LENGTH
        or _URL_CHARACTERS.fullmatch(url) is None
        or "\\" in url
    ):
        msg = "the URL is not printable ASCII of a bounded length"
        raise PolicyViolation(msg)
    try:
        parts = urlsplit(url)
        port = parts.port
    except ValueError:
        msg = "the URL does not parse"
        raise PolicyViolation(msg) from None
    host = (parts.hostname or "").lower()
    if parts.scheme != "https":
        msg = "only https URLs are allowed"
        raise PolicyViolation(msg)
    if port not in (None, HTTPS_PORT):
        msg = "only port 443 is allowed"
        raise PolicyViolation(msg)
    if _is_ip_literal(host):
        msg = "IP-literal hosts are not allowed"
        raise PolicyViolation(msg)
    if "@" in parts.netloc or parts.netloc.lower() not in (host, f"{host}:{HTTPS_PORT}"):
        msg = "the URL has user information or an unusual authority"
        raise PolicyViolation(msg)
    if not policy.owns(host):
        msg = f"the host {host!r} is not in the {policy.provider_key} host policy"
        raise PolicyViolation(msg)
    if parts.fragment or "#" in url:
        msg = "the URL has a fragment"
        raise PolicyViolation(msg)
    path = parts.path or "/"
    if not path.startswith("/"):  # pragma: no cover - urlsplit keeps the leading slash
        msg = "the URL path is not absolute"
        raise PolicyViolation(msg)
    target = f"{path}?{parts.query}" if parts.query else path
    return ValidatedUrl(host=host, target=target)


def resolve_redirect(current: ValidatedUrl, location: str, policy: HostPolicy) -> ValidatedUrl:
    """The target of a redirect, validated like any other URL."""
    if not isinstance(location, str) or _URL_CHARACTERS.fullmatch(location) is None:
        msg = "the redirect location is not printable ASCII"
        raise PolicyViolation(msg)
    return validate_url(urljoin(current.url, location), policy)


def _is_ip_literal(host: str) -> bool:
    try:
        ip_address(host.strip("[]"))
    except ValueError:
        return False
    return True


def https_url(host: str, path: str, query: Sequence[tuple[str, str | None]] = ()) -> str:
    """Build an HTTPS URL from a host, an already encoded path, and query
    parameters, which are percent-encoded here (spaces as ``%20``). A value
    of ``None`` is a valueless flag, such as Cleveland's ``cc0``."""
    _check_host_name(host)
    if not path.startswith("/"):
        msg = "the path must start with /"
        raise ValueError(msg)
    if not query:
        return f"https://{host}{path}"
    parts = [
        quote(key, safe="") if value is None else f"{quote(key, safe='')}={quote(value, safe='')}"
        for key, value in query
    ]
    return f"https://{host}{path}?{'&'.join(parts)}"


def path_segment(value: str, pattern: re.Pattern[str]) -> str:
    """Percent-encode ``value`` for one path segment after it ``fullmatch``-es
    ``pattern`` (§10: identifiers placed into URLs)."""
    if pattern.fullmatch(value) is None:
        msg = "the identifier does not match its pattern"
        raise ValueError(msg)
    return quote(value, safe="")


# --- addresses ---------------------------------------------------------------


def _public(address: IPAddress) -> bool:
    return (
        address.is_global
        and not address.is_private
        and not address.is_multicast
        and not address.is_reserved
        and not address.is_unspecified
        and not address.is_loopback
        and not address.is_link_local
        and not (isinstance(address, IPv4Address) and address in _SHARED_ADDRESS_SPACE)
        and not (isinstance(address, IPv6Address) and address.is_site_local)
    )


def _embedded_ipv4(address: IPv6Address) -> IPv4Address | None:
    """The IPv4 address inside a 6to4, Teredo, or NAT64 address."""
    if address.sixtofour is not None:
        return address.sixtofour
    if address.teredo is not None:
        return address.teredo[1]
    if address in _NAT64:
        return IPv4Address(int(address) & 0xFFFFFFFF)
    return None


def is_public_address(address: IPAddress) -> bool:
    """Whether ``address`` is globally routable (§10): not loopback, private,
    link-local, site-local, shared (CGNAT), multicast, reserved, or
    unspecified. Mapped and embedded IPv4 forms are unwrapped and checked too."""
    if isinstance(address, IPv6Address):
        if address.scope_id:
            return False
        mapped = address.ipv4_mapped
        if mapped is not None:
            return _public(mapped)
        embedded = _embedded_ipv4(address)
        if embedded is not None and not _public(embedded):
            return False
    return _public(address)


def is_private_address(address: IPAddress) -> bool:
    """Whether ``address`` is a private unicast address (the Supervisor's
    internal network): private, and not loopback, link-local, multicast,
    reserved, or unspecified."""
    if isinstance(address, IPv6Address):
        mapped = address.ipv4_mapped
        if mapped is not None:
            return is_private_address(mapped)
        if address.scope_id:
            return False
    return (
        address.is_private
        and not address.is_loopback
        and not address.is_link_local
        and not address.is_multicast
        and not address.is_reserved
        and not address.is_unspecified
    )


# --- response headers --------------------------------------------------------


def media_type(value: str | None) -> str | None:
    """The lowercase ``type/subtype`` of a ``Content-Type`` value, or ``None``."""
    if value is None:
        return None
    main = value.split(";", 1)[0].strip().lower()
    if main.count("/") != 1 or not all(_TOKEN.fullmatch(part) for part in main.split("/")):
        return None
    return main


def content_length(value: str | None) -> int | None:
    """The declared body length, or ``None`` if absent. Raises ``ValueError``
    for anything but one plain decimal number (a repeated header is refused)."""
    if value is None:
        return None
    text = value.strip()
    if _DIGITS.fullmatch(text) is None:
        msg = "invalid Content-Length"
        raise ValueError(msg)
    return int(text)


def retry_after_seconds(value: str | None, now: datetime) -> float | None:
    """The wait a ``Retry-After`` value asks for, in seconds (never negative),
    or ``None`` if it is absent or invalid. Accepts delta-seconds and an
    IMF-fixdate HTTP-date (D-115)."""
    if value is None:
        return None
    text = value.strip()
    if _DIGITS.fullmatch(text) is not None:
        return float(int(text))
    match = _IMF_FIXDATE.fullmatch(text)
    if match is None:
        return None
    day, month, year, hour, minute, second = match.groups()
    try:
        when = datetime(
            int(year),
            _MONTHS.index(month) + 1,
            int(day),
            int(hour),
            int(minute),
            int(second),
            tzinfo=UTC,
        )
    except ValueError:
        return None
    return max(0.0, (when - now).total_seconds())
