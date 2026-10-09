"""Source-bound, offline-prepared Commons colour families (D-213).

No decoding, cache, network request or artwork bytes. A source pin mismatch
cannot reuse an earlier colour observation. Full research distributions remain
available for future multi-colour matching outside this small runtime index.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Final

from frame_gallery.providers.commons_catalog import CuratedWork
from frame_gallery.providers.commons_colour_data import COLOUR_DATA

COLOUR_PROFILES: Final = MappingProxyType(
    {page_id: (sha1, frozenset(keys)) for page_id, sha1, keys in COLOUR_DATA}
)


def matches_colour(work: CuratedWork, key: str) -> bool:
    """Only a meaningful measured family of this exact pinned source matches."""
    profile = COLOUR_PROFILES.get(work.page_id)
    return profile is not None and profile[0] == work.sha1 and key in profile[1]
