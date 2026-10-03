"""One-way worker confinement before credentials and no-new-privileges.

Only our Supervisor profile names and built-in children are accepted.
Use AppArmor's dedicated proc interface, not another LSM's generic attribute.
No third-party module, request or image is loaded before the transition.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Final

CURRENT: Final = Path("/proc/self/attr/apparmor/current")
PARENT: Final = re.compile(r"(?:frame_gallery|local_frame_gallery_dev|[0-9a-f]{8}_frame_gallery)")
CHILDREN: Final = {"prepare": "image_worker", "inspect": "image_worker", "deliver": "tv_worker"}


class ProfileError(Exception):
    """Confinement could not be proven; never continue with an artwork."""


def valid_parent(value: str) -> bool:
    return PARENT.fullmatch(value) is not None


def read_current() -> str:
    with CURRENT.open("rb") as stream:
        return stream.read(1025).decode("ascii").rstrip("\n\x00")


def parent_profile() -> str | None:
    """Discover our enforced profile; refuse our own complain-mode profile."""
    is_linux = sys.platform.startswith("linux")
    if not is_linux:
        return None
    try:
        current = read_current()
    except (OSError, UnicodeError):
        return None
    name, _, mode = current.partition(" ")
    if not valid_parent(name):
        return None
    if mode != "(enforce)":
        raise ProfileError("parent_not_enforced")
    return name


def change_profile(target: str) -> None:
    # Same proc protocol as aa_change_profile, written once.
    command = f"changeprofile {target}".encode("ascii")
    with CURRENT.open("wb", buffering=0) as stream:
        if stream.write(command) != len(command):
            raise ProfileError("transition_short_write")


def confine(parent: str | None, task: str) -> str | None:
    if parent is None:
        return None  # development/test launch, never the production app
    if not valid_parent(parent) or task not in CHILDREN:
        raise ProfileError("transition_target")
    target = f"{parent}//{CHILDREN[task]}"
    try:
        if read_current() != f"{parent} (enforce)":
            raise ProfileError("transition_origin")
        change_profile(target)
        if read_current() != f"{target} (enforce)":
            raise ProfileError("transition_not_enforced")
    except (OSError, UnicodeError):
        raise ProfileError("transition_failed") from None
    return target
