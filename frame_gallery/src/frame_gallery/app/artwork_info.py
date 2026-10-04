"""Compact, plain-text preview attribution for a UI-created Text helper.

No additional museum requests, HTML, image processing, or persistent files.
The single JSON state survives HA restarts when the helper has no Initial value.
"""

from __future__ import annotations

import json
import unicodedata

from frame_gallery.providers.contract import Candidate

_MUSEUMS = {
    "aic": "Art Institute of Chicago",
    "cma": "Cleveland Museum of Art",
    "local": "Local images",
}


def _text(value: str | None) -> str:
    if value is None:
        return ""
    text = " ".join(
        "".join(
            " " if unicodedata.category(char).startswith("C") else char for char in value[:1000]
        ).split()
    )
    return text if len(text) <= 100 else text[:99] + "…"


def artwork_info(candidate: Candidate) -> str:
    """One JSON object, at most 255 characters including JSON escaping.

    Missing title/creator stay empty; the museum label comes only from our
    provider key, never a credit line or an inferred artist. Long fields are
    shortened with an ellipsis, balancing title and artist when needed.
    """
    title, artist = _text(candidate.attribution.title), _text(candidate.attribution.creator)
    title_limit, artist_limit = len(title), len(artist)
    while True:
        data = {
            "title": title if title_limit == len(title) else title[:title_limit] + "…",
            "artist": artist if artist_limit == len(artist) else artist[:artist_limit] + "…",
            "museum": _MUSEUMS.get(candidate.provider_key, ""),
        }
        result = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        if len(result) <= 255:
            return result
        if title_limit >= artist_limit:
            title_limit -= 1
        else:
            artist_limit -= 1
