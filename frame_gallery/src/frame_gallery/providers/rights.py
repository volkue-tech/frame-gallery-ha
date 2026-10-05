"""Rights bases and the per-source allowlist (§9.1, D-134)."""

from __future__ import annotations

import enum
from typing import Final

from frame_gallery.domain import SourceKey


class RightsBasis(enum.StrEnum):
    """Why the app may show a work."""

    USER_SUPPLIED = "user_supplied"
    """The user's own image from the local library."""

    CC0 = "cc0"
    """A museum image dedicated to the public domain under CC0."""

    PUBLIC_DOMAIN = "public_domain"
    """An individually curated Commons reproduction labelled public domain.

    This is not a warranty of worldwide legal clearance (D-206).
    """


ALLOWED_RIGHTS: Final[dict[SourceKey, frozenset[RightsBasis]]] = {
    SourceKey.LOCAL_MEDIA: frozenset({RightsBasis.USER_SUPPLIED}),
    SourceKey.ART_INSTITUTE_CHICAGO: frozenset({RightsBasis.CC0}),
    SourceKey.CLEVELAND_MUSEUM_OF_ART: frozenset({RightsBasis.CC0}),
    SourceKey.WIKIMEDIA_COMMONS: frozenset({RightsBasis.CC0, RightsBasis.PUBLIC_DOMAIN}),
}
"""Selection rejects any candidate whose rights basis is not listed here."""
