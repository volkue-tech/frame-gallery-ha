"""The provider contract (§9.1).

Providers are lazy: ``iter_candidates`` yields one candidate at a time and
makes further requests only when the caller asks for more. All remote traffic
goes through the guarded gateway (Phase 3). Providers never decide
eligibility; selection does.
"""

from __future__ import annotations

import enum
import re
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Final, Protocol

from frame_gallery.budget.deadline import Deadline
from frame_gallery.config.filters import EffectiveFilters
from frame_gallery.domain import Size, SourceKey
from frame_gallery.errors import FrameGalleryError
from frame_gallery.providers.rights import RightsBasis
from frame_gallery.randomness import RandomSource

QUALIFIED_ID_MAX_LENGTH: Final = 200
PROVIDER_KEY_PATTERN: Final = re.compile(r"[a-z]{2,16}")
NATIVE_ID_PATTERN: Final = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]*")
"""Native identifiers are plain tokens; adapters apply stricter patterns."""


@dataclass(frozen=True, slots=True)
class Attribution:
    """Display and credit information. Every field is untrusted text."""

    title: str | None = None
    creator: str | None = None
    date_text: str | None = None
    credit_line: str | None = None
    detail_url: str | None = None


@dataclass(frozen=True, slots=True)
class Candidate:
    """One artwork offered by a provider."""

    provider_key: str
    native_id: str
    rights_basis: RightsBasis
    rights_field: str
    """The metadata field the rights basis came from, e.g. ``is_public_domain``."""

    attribution: Attribution
    dims: Size | None
    """Dimensions of the rendition ``full_ref`` delivers, after EXIF
    orientation, when the metadata provides them; otherwise ``None``."""

    def __post_init__(self) -> None:
        if PROVIDER_KEY_PATTERN.fullmatch(self.provider_key) is None:
            msg = "invalid provider key"
            raise ValueError(msg)
        if NATIVE_ID_PATTERN.fullmatch(self.native_id) is None:
            msg = "invalid native identifier"
            raise ValueError(msg)
        if len(self.qualified_id) > QUALIFIED_ID_MAX_LENGTH:
            msg = "qualified identifier too long"
            raise ValueError(msg)

    @property
    def qualified_id(self) -> str:
        """The persistent identifier: ``<provider key>:<native id>``."""
        return f"{self.provider_key}:{self.native_id}"


class ImageRefKind(enum.StrEnum):
    REMOTE = "remote"
    LOCAL = "local"


@dataclass(frozen=True, slots=True)
class ImageRef:
    """Where the bytes of a rendition come from. Resolved by the fetcher."""

    kind: ImageRefKind
    location: str
    """An HTTPS URL on the provider's policy host, or a library path."""


class DimensionSource(enum.StrEnum):
    """How a candidate's dimensions are learned, and which allowance pays."""

    REMOTE_PROBE = "remote_probe"
    """A remote request (30 per run, C4)."""

    LOCAL_INSPECTION = "local_inspection"
    """A local header inspection (a separate allowance of 300)."""


@dataclass(frozen=True, slots=True)
class Capabilities:
    """What a provider declares about itself."""

    source: SourceKey
    provider_key: str
    dims_in_metadata: bool
    """True when the source's documented metadata gives the rendition's size,
    so no probe is bound. A candidate whose metadata lacks it carries ``None``
    and selection counts it as ``dims_unavailable`` (D-152)."""


class SourceErrorKind(enum.StrEnum):
    """Provider and transport failures (§4.2 classification)."""

    TRANSPORT = "transport"
    """Connect, TLS, DNS, or a connection lost mid-response."""

    TIMEOUT = "timeout"
    """The request's own timeout (not the phase deadline)."""

    HTTP_ERROR = "http_error"
    """A non-success status other than 403 or 429, including a 404 or 410
    from a discovery (search) endpoint: the source itself is failing."""

    STOPPED = "stopped"
    """HTTP 403, or 429 without the single permitted retry: the 403/429 stop.
    No further request goes to this provider in this run."""

    NOT_FOUND = "not_found"
    """HTTP 404 or 410 for one resource (a rendition or a probe target): move on
    to the next candidate. Never used for a discovery endpoint (see HTTP_ERROR)."""

    OVER_CAP = "over_cap"
    """A response over its byte cap or its declared ``Content-Length``."""

    UNEXPECTED_FORMAT = "unexpected_format"
    """A response that does not parse as the documented format."""


class SourceError(FrameGalleryError):
    """A provider or transport failure. ``detail`` is safe to log."""

    def __init__(self, kind: SourceErrorKind, detail: str = "") -> None:
        super().__init__(f"{kind.value}: {detail}" if detail else kind.value)
        self.kind = kind
        self.detail = detail

    @property
    def is_transport_failure(self) -> bool:
        """Counts towards ``source_failed`` (everything except 404 or 410)."""
        return self.kind is not SourceErrorKind.NOT_FOUND


@dataclass(frozen=True, slots=True)
class DiscoveryContext:
    """What a provider receives for one discovery pass."""

    deadline: Deadline
    """The discovery deadline; every request is clamped to it."""

    random: RandomSource


class Provider(Protocol):
    """A source of candidates (§9.1)."""

    @property
    def key(self) -> str:
        """The history and ledger prefix, e.g. ``aic``."""
        ...

    def capabilities(self) -> Capabilities: ...

    def iter_candidates(
        self, filters: EffectiveFilters, ctx: DiscoveryContext
    ) -> Iterator[Candidate]:
        """Yield candidates lazily. May raise :class:`SourceError`,
        ``DeadlineExceeded``, or ``Cancelled`` from any ``next()`` call."""
        ...

    def full_ref(self, candidate: Candidate) -> ImageRef:
        """The rendition to download for delivery."""
        ...


class DimensionProbe(Protocol):
    """Learns a candidate's dimensions when the metadata lacks them."""

    @property
    def source(self) -> DimensionSource: ...

    def measure(self, candidate: Candidate, deadline: Deadline) -> Size | None:
        """The rendition's dimensions after EXIF orientation, or ``None`` if they
        cannot be determined. May raise :class:`SourceError`,
        ``DeadlineExceeded``, or ``Cancelled``.

        A local inspection returns ``None`` for a file it cannot read (counted in
        the aggregated warning, §9.3); if it raises, the failure counts as an
        inspection failure, never as a transport failure."""
        ...
