"""How the app identifies itself to providers (§10, D-119 as amended).

There is no browser impersonation and no invented project URL. Until a public
project URL is decided (Q-13), the User-Agent names the project contact; the
Art Institute's courtesy header carries the same contact. Tests pass a
placeholder contact; the project contact reaches a provider only in an
explicitly approved live request (Q-22).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from frame_gallery import __version__

PRODUCT: Final = "FrameGallery"

PROJECT_CONTACT: Final = "volkue@gmail.com"
"""The project contact approved for the courtesy headers (Q-22). Replaced by
the public repository URL before publication (D-119)."""

COMMONS_CONTACT: Final = "volkue+commonsapi@gmail.com"
"""User-approved contact for Commons requests only (D-206)."""

_CONTACT: Final = re.compile(
    r"[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+",
    re.ASCII,
)
_VERSION: Final = re.compile(r"[0-9A-Za-z][0-9A-Za-z.+-]{0,31}", re.ASCII)


@dataclass(frozen=True, slots=True)
class ClientIdentity:
    """The product version and the contact named in every request."""

    version: str
    contact: str

    def __post_init__(self) -> None:
        if _VERSION.fullmatch(self.version) is None:
            msg = "invalid version for the User-Agent"
            raise ValueError(msg)
        if len(self.contact) > 254 or _CONTACT.fullmatch(self.contact) is None:
            msg = "the contact must be a plain e-mail address"
            raise ValueError(msg)

    @property
    def user_agent(self) -> str:
        """``FrameGallery/<version> (contact: <contact>)``."""
        return f"{PRODUCT}/{self.version} (contact: {self.contact})"

    @property
    def courtesy_agent(self) -> str:
        """The Art Institute's ``AIC-User-Agent``: project name and contact."""
        return f"{PRODUCT}/{self.version} ({self.contact})"


def project_identity() -> ClientIdentity:
    """The identity used by the production wiring (Phase 6)."""
    return ClientIdentity(version=__version__, contact=PROJECT_CONTACT)


def commons_identity(version: str = __version__) -> ClientIdentity:
    """Commons uses its dedicated contact without changing the museums'."""
    return ClientIdentity(version=version, contact=COMMONS_CONTACT)
