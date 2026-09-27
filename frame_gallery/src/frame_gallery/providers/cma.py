"""The Cleveland Museum of Art adapter (§9.6, D-136, D-146).

Only the documented Open Access API is used, through the guarded gateway:

1. **Count.** ``GET /api/artworks/`` with ``limit=1`` reads the documented
   ``info.total`` for the filter (cached for a day).
2. **Pages.** Pages of 25 works at random ``skip`` offsets, without
   replacement. A page whose works were all sent already is remembered, by
   its index (the offset is 25 times the index), for 7 days as exhausted (for the same
   total) and skipped.

Every request carries the valueless ``cc0`` flag and ``has_image=1``, and
sets ``limit`` explicitly (the documented default is 1000 records). A
department is sent as its exact documented value. A period is sent through
``created_after`` and ``created_before``, each widened by one year, because
the documentation says neither whether they are inclusive nor which date
they compare; the exact range is then enforced on the documented
``creation_date_earliest``.

Every record is checked again: ``share_license_status`` must be ``"CC0"``,
and ``images.print`` must be present. The rendition is only that documented
print JPEG (3400 px long side), on the documented image host; the original
TIFF (``images.full``) is never requested. A print on any other host or
path is skipped and counted in one warning.
"""

from __future__ import annotations

import logging
import math
import re
from collections.abc import Iterator, Mapping, Sequence
from types import MappingProxyType
from typing import Final

from frame_gallery.budget.deadline import Deadline
from frame_gallery.config.filters import EffectiveFilters
from frame_gallery.domain import Size, SourceKey
from frame_gallery.net.gateway import ProviderChannel
from frame_gallery.net.policy import HostPolicy, PolicyViolation, https_url, validate_url
from frame_gallery.providers.cache import (
    COUNT_TTL,
    HINT_TTL,
    MetadataCache,
    known_exhausted,
    offers_nothing_new,
)
from frame_gallery.providers.contract import (
    Attribution,
    Candidate,
    Capabilities,
    DiscoveryContext,
    ImageRef,
    ImageRefKind,
)
from frame_gallery.providers.jsonread import as_count, as_list, as_object, positive_int, text, year
from frame_gallery.providers.periods import YearRange, period_range
from frame_gallery.providers.rights import RightsBasis
from frame_gallery.randomness import RandomSource

PROVIDER_KEY: Final = "cma"
API_HOST: Final = "openaccess-api.clevelandart.org"
IMAGE_HOST: Final = "openaccess-cdn.clevelandart.org"
ARTWORKS_PATH: Final = "/api/artworks/"
PAGE_SIZE: Final = 25
MAX_ARTWORK_ID: Final = 10**12
MAX_IMAGE_SIDE: Final = 100_000
SHUFFLE_LIMIT: Final = 4096
"""Up to this many pages, the page order is a shuffled list; beyond it,
pages are drawn lazily and repeats are skipped."""

DRAW_ATTEMPTS: Final = 64

FIELDS: Final = (
    "id",
    "accession_number",
    "title",
    "creators",
    "creation_date",
    "creation_date_earliest",
    "department",
    "share_license_status",
    "images",
    "url",
)

DOCUMENTED_DEPARTMENTS: Final = (
    "African Art",
    "American Painting and Sculpture",
    "Art of the Americas",
    "Chinese Art",
    "Contemporary Art",
    "Decorative Art and Design",
    "Drawings",
    "Egyptian and Ancient Near Eastern Art",
    "European Painting and Sculpture",
    "Greek and Roman Art",
    "Indian and South East Asian Art",
    "Islamic Art",
    "Japanese Art",
    "Korean Art",
    "Medieval Art",
    "Modern European Painting and Sculpture",
    "Oceania",
    "Performing Arts, Music, & Film",
    "Photography",
    "Prints",
    "Textiles",
)
"""Appendix B of the documentation, verbatim (re-checked on 2026-09-27)."""

DEPARTMENTS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "cma_american_painting_sculpture": "American Painting and Sculpture",
        "cma_european_painting_sculpture": "European Painting and Sculpture",
        "cma_modern_european_painting_sculpture": "Modern European Painting and Sculpture",
        "cma_drawings": "Drawings",
        "cma_prints": "Prints",
        "cma_photography": "Photography",
        "cma_chinese_art": "Chinese Art",
        "cma_japanese_art": "Japanese Art",
        "cma_korean_art": "Korean Art",
        "cma_indian_southeast_asian_art": "Indian and South East Asian Art",
        "cma_islamic_art": "Islamic Art",
        "cma_textiles": "Textiles",
    }
)
"""The curated departments offered (Q-14, D-151): the vocabulary key and the exact
documented value. "Performing Arts, Music, & Film" is left out because the
parsing of a value with commas is undocumented (D-146)."""

_DETAIL_URL: Final = re.compile(r"https://(?:www\.)?clevelandart\.org/art/[A-Za-z0-9.\-]{1,64}")
_ACCEPTED_PRINT_PATH: Final = re.compile(r"/[A-Za-z0-9._\-/]{1,300}\.jpg", re.IGNORECASE)

_log = logging.getLogger("frame_gallery.providers.cma")


def cma_policy() -> HostPolicy:
    """Exactly the two documented hosts, and 1 s pacing. Cleveland asks for no
    courtesy header; the honest User-Agent identifies the app (D-119)."""
    return HostPolicy(provider_key=PROVIDER_KEY, hosts=frozenset({API_HOST, IMAGE_HOST}))


class CmaProvider:
    """The ``cleveland_museum_of_art`` source. One instance serves one run."""

    def __init__(self, channel: ProviderChannel, cache: MetadataCache) -> None:
        if channel.policy.provider_key != PROVIDER_KEY:
            msg = "the channel belongs to another provider"
            raise ValueError(msg)
        self._channel = channel
        self._cache = cache
        self._prints: dict[str, str] = {}
        self._off_host = 0

    @property
    def key(self) -> str:
        return PROVIDER_KEY

    def capabilities(self) -> Capabilities:
        return Capabilities(
            source=SourceKey.CLEVELAND_MUSEUM_OF_ART,
            provider_key=PROVIDER_KEY,
            dims_in_metadata=True,
        )

    def iter_candidates(
        self, filters: EffectiveFilters, ctx: DiscoveryContext
    ) -> Iterator[Candidate]:
        department = None if filters.department is None else _department(filters.department)
        period = None if filters.period is None else period_range(filters.period)
        base = _filter_query(department, period)
        signature = f"{filters.department or 'any'}:{filters.period or 'any'}"
        total = self._count(base, signature, ctx.deadline)
        pages = math.ceil(total / PAGE_SIZE)
        hint_key = f"{PROVIDER_KEY}:exhausted:{signature}"
        known = frozenset(
            page
            for page in known_exhausted(self._cache.get_exhausted(hint_key), total)
            if page < pages
        )
        ctx.notes.pages_skipped += len(known)
        self._off_host = 0
        try:
            for page in _page_order(pages, ctx.random, skip=known):
                records = self._page(base, page, ctx.deadline)
                offered = [
                    candidate
                    for candidate in (self._offer(r, department, period) for r in records)
                    if candidate is not None
                ]
                if offers_nothing_new(offered, ctx.is_excluded_for_good):
                    self._cache.add_exhausted(hint_key, total, (page,), HINT_TTL)
                yield from offered
        finally:
            if self._off_host:
                _log.warning(
                    "cma: %d print renditions were skipped: not a JPEG on %s",
                    self._off_host,
                    IMAGE_HOST,
                )

    def full_ref(self, candidate: Candidate) -> ImageRef:
        url = self._prints.get(candidate.native_id)
        if candidate.provider_key != PROVIDER_KEY or url is None:
            msg = "the candidate was not offered by this adapter"
            raise ValueError(msg)
        return ImageRef(ImageRefKind.REMOTE, url)

    # --------------------------------------------------------------- requests

    def _count(
        self, base: Sequence[tuple[str, str | None]], signature: str, deadline: Deadline
    ) -> int:
        cache_key = f"{PROVIDER_KEY}:count:{signature}"
        cached = self._cache.get_count(cache_key)
        if cached is not None:
            return cached
        document = self._get([*base, ("limit", "1"), ("fields", "id")], deadline)
        info = as_object(document.get("info"), "info")
        total = as_count(info.get("total"), "info.total")
        self._cache.put_count(cache_key, total, COUNT_TTL)
        return total

    def _page(
        self, base: Sequence[tuple[str, str | None]], page: int, deadline: Deadline
    ) -> Sequence[object]:
        query = [
            *base,
            ("skip", str(page * PAGE_SIZE)),
            ("limit", str(PAGE_SIZE)),
            ("fields", ",".join(FIELDS)),
        ]
        document = self._get(query, deadline)
        return as_list(document.get("data"), "data")[:PAGE_SIZE]

    def _get(
        self, query: Sequence[tuple[str, str | None]], deadline: Deadline
    ) -> Mapping[str, object]:
        url = https_url(API_HOST, ARTWORKS_PATH, query)
        return as_object(self._channel.get_json(url, deadline), "the response")

    # ----------------------------------------------------------------- offers

    def _offer(
        self, raw: object, department: str | None, period: YearRange | None
    ) -> Candidate | None:
        """A candidate, or ``None`` for a skipped record. A print that is not a
        JPEG on the image host is counted for the warning."""
        artwork_id = _eligible(raw, department, period)
        if artwork_id is None or not isinstance(raw, dict):
            return None
        images = raw.get("images")
        rendition = images.get("print") if isinstance(images, dict) else None
        if not isinstance(rendition, dict):
            return None
        url = _print_url(rendition.get("url"))
        if url is None:
            self._off_host += 1
            return None
        width = positive_int(rendition.get("width"), MAX_IMAGE_SIDE)
        height = positive_int(rendition.get("height"), MAX_IMAGE_SIDE)
        native_id = str(artwork_id)
        self._prints[native_id] = url
        return Candidate(
            provider_key=PROVIDER_KEY,
            native_id=native_id,
            rights_basis=RightsBasis.CC0,
            rights_field="share_license_status",
            attribution=Attribution(
                title=text(raw.get("title")),
                creator=_creator(raw.get("creators")),
                date_text=text(raw.get("creation_date")),
                detail_url=_detail_url(raw.get("url")),
            ),
            dims=None if width is None or height is None else Size(width, height),
        )


def _eligible(raw: object, department: str | None, period: YearRange | None) -> int | None:
    """The artwork ID of a CC0 record that matches the filters, or ``None``."""
    if not isinstance(raw, dict):
        return None
    artwork_id = raw.get("id")
    if (
        isinstance(artwork_id, bool)
        or not isinstance(artwork_id, int)
        or not 0 < artwork_id <= MAX_ARTWORK_ID
        or raw.get("share_license_status") != "CC0"
        or (department is not None and raw.get("department") != department)
    ):
        return None
    if period is not None:
        earliest = year(raw.get("creation_date_earliest"))
        if earliest is None or not period.contains(earliest):
            return None
    return artwork_id


def _department(key: str) -> str:
    value = DEPARTMENTS.get(key)
    if value is None:
        msg = f"unknown Cleveland department key {key!r}"
        raise ValueError(msg)
    return value


def _filter_query(department: str | None, period: YearRange | None) -> list[tuple[str, str | None]]:
    query: list[tuple[str, str | None]] = [("cc0", None), ("has_image", "1")]
    if department is not None:
        query.append(("department", department))
    if period is not None:
        if period.first is not None:
            query.append(("created_after", str(period.first - 1)))
        if period.last is not None:
            query.append(("created_before", str(period.last + 1)))
    return query


def _page_order(
    pages: int, random: RandomSource, *, skip: frozenset[int] = frozenset()
) -> Iterator[int]:
    """Page indices without replacement, in a random order, never one in ``skip``."""
    if pages <= SHUFFLE_LIMIT:
        order = [page for page in range(pages) if page not in skip]
        random.shuffle(order)
        yield from order
        return
    used: set[int] = set(skip)
    while True:
        for _ in range(DRAW_ATTEMPTS):
            page = random.randrange(pages)
            if page not in used:
                break
        else:
            return
        used.add(page)
        yield page


def _print_url(value: object) -> str | None:
    """The print URL if it is a ``.jpg`` on the documented image host."""
    if not isinstance(value, str):
        return None
    try:
        validated = validate_url(value, cma_policy())
    except PolicyViolation:
        return None
    if validated.host != IMAGE_HOST or "?" in validated.target:
        return None
    if _ACCEPTED_PRINT_PATH.fullmatch(validated.path) is None:
        return None
    if any(segment in ("", ".", "..") for segment in validated.path.split("/")[1:]):
        return None  # no empty or dot segments
    return validated.url


def _creator(value: object) -> str | None:
    """The first creator's documented ``description``."""
    if not isinstance(value, list) or not value or not isinstance(value[0], dict):
        return None
    return text(value[0].get("description"))


def _detail_url(value: object) -> str | None:
    """The documented link to the artwork's page, if it has the expected form."""
    if isinstance(value, str) and _DETAIL_URL.fullmatch(value):
        return value
    return None
