"""The Art Institute of Chicago adapter (§9.5, D-132, D-146).

Only the documented API is used, through the guarded gateway:

1. **Count.** ``GET /api/v1/artworks/search`` with ``limit`` 0 reads the
   documented ``pagination.total`` for the filter (cached for a day).
2. **Pages.** Pages of 50 works are sampled without replacement from the
   first ``min(total, 10 000)`` results; the documentation caps every search
   query at 10 000 records. A page whose works were all sent already is
   remembered for 7 days as exhausted (for the same total) and skipped.
   The Elasticsearch query travels as minified JSON in the documented
   ``params`` parameter. Every query requires
   ``is_public_domain`` and an ``image_id``; the period filter adds a range
   on the documented ``date_start``.
3. **Sizes.** One batched request to the documented Images resource,
   ``GET /api/v1/images?ids=...&fields=id,width,height``, reads the native
   sizes of a page's images.

Every record is checked again: ``is_public_domain`` must be ``true``, the
identifiers must match their patterns, and a period filter must hold for
``date_start``. The rendition is the documented public-domain IIIF size
``full/1686,/0/default.jpg``; images narrower than 1686 px are skipped,
because the documentation does not say whether the server upscales them.
Departments, styles, and colours are unsupported in the beta: their values
are not documented (D-146).
"""

from __future__ import annotations

import json
import logging
import math
import re
from collections.abc import Iterator, Mapping, Sequence
from typing import Final

from frame_gallery.budget.deadline import Deadline
from frame_gallery.config.filters import EffectiveFilters
from frame_gallery.domain import Size, SourceKey
from frame_gallery.net.gateway import ProviderChannel
from frame_gallery.net.identity import ClientIdentity
from frame_gallery.net.policy import HostPolicy, https_url, path_segment
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

PROVIDER_KEY: Final = "aic"
API_HOST: Final = "api.artic.edu"
IIIF_HOST: Final = "www.artic.edu"
SEARCH_PATH: Final = "/api/v1/artworks/search"
IMAGES_PATH: Final = "/api/v1/images"
PAGE_SIZE: Final = 50
RESULT_WINDOW: Final = 10_000
RENDITION_WIDTH: Final = 1686
MAX_ARTWORK_ID: Final = 10**10
MAX_IMAGE_SIDE: Final = 100_000

ARTWORK_FIELDS: Final = (
    "id",
    "is_public_domain",
    "title",
    "artist_display",
    "date_display",
    "date_start",
    "image_id",
    "credit_line",
)
IMAGE_ID: Final = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
"""The UUID form of the documentation's ``image_id`` examples."""

_log = logging.getLogger("frame_gallery.providers.aic")


def aic_policy(identity: ClientIdentity) -> HostPolicy:
    """Exactly the two documented hosts, 1 s pacing, and the courtesy header."""
    return HostPolicy(
        provider_key=PROVIDER_KEY,
        hosts=frozenset({API_HOST, IIIF_HOST}),
        courtesy_headers={"AIC-User-Agent": identity.courtesy_agent},
    )


def rendition_size(native: Size) -> Size | None:
    """The size of ``full/1686,``: 1686 px wide at the native aspect ratio,
    or ``None`` for an image narrower than that."""
    if native.width < RENDITION_WIDTH:
        return None
    height = max(1, round(RENDITION_WIDTH * native.height / native.width))
    return Size(RENDITION_WIDTH, height)


def _minified(document: object) -> str:
    return json.dumps(document, separators=(",", ":"), sort_keys=True)


class AicProvider:
    """The ``art_institute_chicago`` source. One instance serves one run."""

    def __init__(self, channel: ProviderChannel, cache: MetadataCache) -> None:
        if channel.policy.provider_key != PROVIDER_KEY:
            msg = "the channel belongs to another provider"
            raise ValueError(msg)
        self._channel = channel
        self._cache = cache
        self._images: dict[str, str] = {}

    @property
    def key(self) -> str:
        return PROVIDER_KEY

    def capabilities(self) -> Capabilities:
        return Capabilities(
            source=SourceKey.ART_INSTITUTE_CHICAGO,
            provider_key=PROVIDER_KEY,
            dims_in_metadata=True,
        )

    def iter_candidates(
        self, filters: EffectiveFilters, ctx: DiscoveryContext
    ) -> Iterator[Candidate]:
        period = None if filters.period is None else period_range(filters.period)
        query = _query(period)
        signature = filters.period or "any"
        total = self._count(query, signature, ctx.deadline)
        page_count = math.ceil(min(total, RESULT_WINDOW) / PAGE_SIZE)
        hint_key = f"{PROVIDER_KEY}:exhausted:{signature}"
        known = known_exhausted(self._cache.get_exhausted(hint_key), total)
        pages = [page for page in range(1, page_count + 1) if page not in known]
        ctx.notes.pages_skipped += page_count - len(pages)
        ctx.random.shuffle(pages)
        for page in pages:
            records = self._search(query, page, ctx.deadline)
            offered = list(self._offer(records, period, page, ctx.deadline))
            if offers_nothing_new(offered, ctx.is_excluded_for_good):
                self._cache.add_exhausted(hint_key, total, (page,), HINT_TTL)
            yield from offered

    def full_ref(self, candidate: Candidate) -> ImageRef:
        image_id = self._images.get(candidate.native_id)
        if candidate.provider_key != PROVIDER_KEY or image_id is None:
            msg = "the candidate was not offered by this adapter"
            raise ValueError(msg)
        path = f"/iiif/2/{path_segment(image_id, IMAGE_ID)}/full/{RENDITION_WIDTH},/0/default.jpg"
        return ImageRef(ImageRefKind.REMOTE, https_url(IIIF_HOST, path))

    # --------------------------------------------------------------- requests

    def _count(self, query: Mapping[str, object], signature: str, deadline: Deadline) -> int:
        cache_key = f"{PROVIDER_KEY}:count:{signature}"
        cached = self._cache.get_count(cache_key)
        if cached is not None:
            return cached
        document = self._get(_search_url({"query": query, "limit": 0}), deadline)
        pagination = as_object(document.get("pagination"), "pagination")
        total = as_count(pagination.get("total"), "pagination.total")
        self._cache.put_count(cache_key, total, COUNT_TTL)
        return total

    def _search(
        self, query: Mapping[str, object], page: int, deadline: Deadline
    ) -> Sequence[object]:
        params = {"query": query, "fields": list(ARTWORK_FIELDS), "limit": PAGE_SIZE, "page": page}
        document = self._get(_search_url(params), deadline)
        return as_list(document.get("data"), "data")[:PAGE_SIZE]

    def _image_sizes(self, image_ids: Sequence[str], deadline: Deadline) -> dict[str, Size]:
        url = https_url(
            API_HOST,
            IMAGES_PATH,
            [
                ("ids", ",".join(image_ids)),
                ("fields", "id,width,height"),
                ("limit", str(len(image_ids))),
            ],
        )
        document = self._get(url, deadline)
        sizes: dict[str, Size] = {}
        for raw in as_list(document.get("data"), "data")[: len(image_ids)]:
            if not isinstance(raw, dict):
                continue
            image_id = raw.get("id")
            width = positive_int(raw.get("width"), MAX_IMAGE_SIDE)
            height = positive_int(raw.get("height"), MAX_IMAGE_SIDE)
            if (
                isinstance(image_id, str)
                and IMAGE_ID.fullmatch(image_id)
                and width is not None
                and height is not None
            ):
                sizes[image_id] = Size(width, height)
        return sizes

    def _get(self, url: str, deadline: Deadline) -> Mapping[str, object]:
        return as_object(self._channel.get_json(url, deadline), "the response")

    # ----------------------------------------------------------------- offers

    def _offer(
        self,
        records: Sequence[object],
        period: YearRange | None,
        page: int,
        deadline: Deadline,
    ) -> Iterator[Candidate]:
        accepted = [item for item in (_accepted(raw, period) for raw in records) if item]
        _log.debug("aic page %d: %d records, %d usable", page, len(records), len(accepted))
        if not accepted:
            return
        image_ids = list(dict.fromkeys(image_id for _record, _id, image_id in accepted))
        sizes = self._image_sizes(image_ids, deadline)
        for record, artwork_id, image_id in accepted:
            native = sizes.get(image_id)
            dims = None if native is None else rendition_size(native)
            if native is not None and dims is None:
                continue  # narrower than the rendition: never upscaled (D-146)
            native_id = str(artwork_id)
            self._images[native_id] = image_id
            yield Candidate(
                provider_key=PROVIDER_KEY,
                native_id=native_id,
                rights_basis=RightsBasis.CC0,
                rights_field="is_public_domain",
                attribution=Attribution(
                    title=text(record.get("title")),
                    creator=text(record.get("artist_display")),
                    date_text=text(record.get("date_display")),
                    credit_line=text(record.get("credit_line")),
                ),
                dims=dims,
            )


def _query(period: YearRange | None) -> dict[str, object]:
    clauses: list[object] = [
        {"term": {"is_public_domain": True}},
        {"exists": {"field": "image_id"}},
    ]
    if period is not None:
        bounds: dict[str, int] = {}
        if period.first is not None:
            bounds["gte"] = period.first
        if period.last is not None:
            bounds["lte"] = period.last
        clauses.append({"range": {"date_start": bounds}})
    return {"bool": {"filter": clauses}}


def _search_url(params: Mapping[str, object]) -> str:
    return https_url(API_HOST, SEARCH_PATH, [("params", _minified(params))])


def _accepted(
    raw: object, period: YearRange | None
) -> tuple[Mapping[str, object], int, str] | None:
    """The record, its artwork ID, and its image ID, if it may be offered."""
    if not isinstance(raw, dict):
        return None
    artwork_id = raw.get("id")
    image_id = raw.get("image_id")
    if (
        isinstance(artwork_id, bool)
        or not isinstance(artwork_id, int)
        or not 0 < artwork_id <= MAX_ARTWORK_ID
        or raw.get("is_public_domain") is not True
        or not isinstance(image_id, str)
        or IMAGE_ID.fullmatch(image_id) is None
    ):
        return None
    if period is not None:
        start = year(raw.get("date_start"))
        if start is None or not period.contains(start):
            return None
    return raw, artwork_id, image_id
