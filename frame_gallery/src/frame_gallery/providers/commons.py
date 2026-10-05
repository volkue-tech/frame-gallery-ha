"""Curated Wikimedia Commons source via the documented MediaWiki Action API.

Five imageinfo records per paced request; no scraping, key, arbitrary categories
or HTML attribution parsing. Original hashes pin the reviewed reproductions.
Current rights are rechecked before a bounded JPEG rendition is offered.
All requests and downloads share the existing guarded provider channel.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from typing import Final

from frame_gallery import __version__
from frame_gallery.config.filters import EffectiveFilters
from frame_gallery.domain import Size, SourceKey
from frame_gallery.net.gateway import ProviderChannel
from frame_gallery.net.identity import commons_identity
from frame_gallery.net.policy import HostPolicy, PolicyViolation, https_url, validate_url
from frame_gallery.providers.commons_catalog import CATALOG, CuratedWork
from frame_gallery.providers.contract import (
    Attribution,
    Candidate,
    Capabilities,
    DiscoveryContext,
    ImageRef,
    ImageRefKind,
)
from frame_gallery.providers.jsonread import as_list, as_object, malformed, positive_int
from frame_gallery.providers.rights import RightsBasis

PROVIDER_KEY: Final = "commons"
API_HOST: Final = "commons.wikimedia.org"
IMAGE_HOSTS: Final = frozenset({"upload.wikimedia.org", "thumb.wikimedia.org"})
BATCH_SIZE: Final = 5
RENDITION_WIDTH: Final = 3840
MAX_RENDITION_HEIGHT: Final = 3840
RIGHTS_FIELDS: Final = "LicenseShortName|LicenseUrl|Copyrighted|AttributionRequired|Restrictions"
CC0_URLS: Final = frozenset(
    f"{scheme}://creativecommons.org/publicdomain/zero/1.0/{suffix}"
    for scheme in ("https", "http")
    for suffix in ("", "deed.en")
)


def commons_policy(version: str = __version__) -> HostPolicy:
    return HostPolicy(
        provider_key=PROVIDER_KEY,
        hosts=IMAGE_HOSTS | {API_HOST},
        courtesy_headers={"User-Agent": commons_identity(version).user_agent},
    )


class CommonsProvider:
    """One finite curated selection, shuffled afresh for each run (D-206)."""

    def __init__(self, channel: ProviderChannel, catalog: Sequence[CuratedWork] = CATALOG) -> None:
        if channel.policy.provider_key != PROVIDER_KEY:
            raise ValueError("the channel belongs to another provider")
        self._channel = channel
        self._catalog = tuple(catalog)
        self._refs: dict[str, str] = {}

    @property
    def key(self) -> str:
        return PROVIDER_KEY

    def capabilities(self) -> Capabilities:
        return Capabilities(SourceKey.WIKIMEDIA_COMMONS, PROVIDER_KEY, dims_in_metadata=True)

    def iter_candidates(
        self, filters: EffectiveFilters, ctx: DiscoveryContext
    ) -> Iterator[Candidate]:
        if filters.source is not SourceKey.WIKIMEDIA_COMMONS:
            raise ValueError("the filters belong to another source")
        self._refs.clear()
        order = list(self._catalog)
        ctx.random.shuffle(order)
        for offset in range(0, len(order), BATCH_SIZE):
            ctx.deadline.check()
            batch = order[offset : offset + BATCH_SIZE]
            # No persistent cache needed: an entirely sent batch can be skipped
            # using the existing history/upload-ledger predicate, never quarantine.
            if all(ctx.is_excluded_for_good(f"commons:{work.page_id}") for work in batch):
                ctx.notes.pages_skipped += 1
                continue
            query = (
                ("action", "query"),
                ("format", "json"),
                ("formatversion", "2"),
                ("pageids", "|".join(str(work.page_id) for work in batch)),
                ("prop", "imageinfo"),
                ("iiprop", "size|mime|sha1|url|extmetadata|thumbmime"),
                ("iilimit", "1"),
                ("iiurlwidth", str(RENDITION_WIDTH)),
                ("iiextmetadatalanguage", "en"),
                ("iiextmetadatafilter", RIGHTS_FIELDS),
                ("maxlag", "5"),
            )
            document = as_object(
                self._channel.get_json(https_url(API_HOST, "/w/api.php", query), ctx.deadline),
                "the Commons response",
            )
            if "error" in document or "warnings" in document:
                malformed("Commons refused or did not fully understand the metadata query")
            pages = as_list(as_object(document.get("query"), "query").get("pages"), "pages")
            expected = {work.page_id: work for work in batch}
            seen: set[int] = set()
            for raw in pages[:BATCH_SIZE]:
                ctx.deadline.check()
                if not isinstance(raw, dict):
                    continue
                page_id = positive_int(raw.get("pageid"))
                if page_id is None or page_id not in expected or page_id in seen:
                    continue
                seen.add(page_id)
                candidate = self._offer(raw, expected[page_id])
                if candidate is not None:
                    yield candidate

    def full_ref(self, candidate: Candidate) -> ImageRef:
        url = self._refs.get(candidate.native_id)
        if candidate.provider_key != self.key or url is None:
            raise ValueError("the candidate was not offered by this adapter")
        return ImageRef(ImageRefKind.REMOTE, url)

    def _offer(self, page: Mapping[str, object], work: CuratedWork) -> Candidate | None:
        infos = page.get("imageinfo")
        if (
            page.get("ns") != 6
            or page.get("title") != work.file_title
            or page.get("imagerepository") != "local"
            or not isinstance(infos, list)
            or len(infos) != 1
            or not isinstance(infos[0], dict)
        ):
            return None
        info = infos[0]
        if info.get("sha1") != work.sha1 or info.get("mime") != "image/jpeg":
            return None
        rights = _rights(info.get("extmetadata"))
        if rights is None:
            return None
        rendition = _rendition(info, self._channel.policy)
        if rendition is None:
            return None
        url, size = rendition
        native_id = str(work.page_id)
        self._refs[native_id] = url
        return Candidate(
            PROVIDER_KEY,
            native_id,
            rights,
            "imageinfo.extmetadata (curated file and pinned sha1)",
            Attribution(
                title=work.title,
                creator=work.artist,
                detail_url=https_url(API_HOST, "/w/index.php", (("curid", native_id),)),
            ),
            size,
        )


def _rendition(info: Mapping[str, object], policy: HostPolicy) -> tuple[str, Size] | None:
    width = positive_int(info.get("width"), 100_000)
    height = positive_int(info.get("height"), 100_000)
    if width is None or height is None:
        return None
    # Never download a huge original when a thumbnail is absent or broken.
    if width > RENDITION_WIDTH:
        width = positive_int(info.get("thumbwidth"), RENDITION_WIDTH)
        height = positive_int(info.get("thumbheight"), MAX_RENDITION_HEIGHT)
        location = info.get("thumburl")
        if info.get("thumbmime") != "image/jpeg":
            return None
    else:
        location = info.get("url")
    if width is None or height is None or height > MAX_RENDITION_HEIGHT:
        return None
    url = _image_url(location, policy)
    if url is None:
        return None
    return url, Size(width, height)


def _rights(raw: object) -> RightsBasis | None:
    if not isinstance(raw, dict):
        return None
    values = {key: field.get("value") for key, field in raw.items() if isinstance(field, dict)}
    if values.get("AttributionRequired") != "false" or values.get("Restrictions", "") != "":
        return None
    label = values.get("LicenseShortName")
    if label == "Public domain" and values.get("Copyrighted") in ("False", "false"):
        return RightsBasis.PUBLIC_DOMAIN
    # Commons can report Copyrighted=True for a CC0 dedication. Require the
    # canonical dedication URL as well, not merely a permissive label.
    url = values.get("LicenseUrl")
    if label == "CC0" and isinstance(url, str) and url in CC0_URLS:
        return RightsBasis.CC0
    return None


def _image_url(raw: object, policy: HostPolicy) -> str | None:
    if not isinstance(raw, str):
        return None
    try:
        validated = validate_url(raw, policy)
    except PolicyViolation:
        return None
    if validated.host not in IMAGE_HOSTS or not validated.path.startswith("/wikipedia/commons/"):
        return None
    return validated.url
