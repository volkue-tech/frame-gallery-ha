"""The draft AppArmor profile (apparmor.txt; ARCHITECTURE.md §17.6, D-129).

The profile cannot be loaded here (that needs a Linux kernel and
apparmor_parser); these tests hold its rules to §17.6 and check the
structure that the parser needs."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

PROJECT: Final = Path(__file__).resolve().parents[3]
PROFILE: Final = (PROJECT / "apparmor.txt").read_text()
RULES: Final = [
    line.strip()
    for line in PROFILE.splitlines()
    if line.strip() and not line.strip().startswith("#")
]
BODY: Final = RULES[RULES.index(next(r for r in RULES if r.startswith("profile "))) + 1 : -1]

S6_EXAMPLE: Final = (
    "/init ix,",
    "/bin/** ix,",
    "/usr/bin/** ix,",
    "/run/{s6,s6-rc*,service}/** ix,",
    "/package/** ix,",
    "/command/** ix,",
    "/etc/services.d/** rwix,",
    "/etc/cont-init.d/** rwix,",
    "/etc/cont-finish.d/** rwix,",
    "/run/{,**} rwk,",
    "/dev/tty rw,",
)
"""The S6-Overlay lines of the official example profile, unchanged."""


def test_the_profile_is_named_after_the_slug_and_complains_only() -> None:
    """Complain mode in Phases 6 to 8; enforced in Phase 9 (D-129, D-139)."""
    assert RULES[0] == "#include <tunables/global>" or PROFILE.startswith(
        "#include <tunables/global>"
    )
    (header,) = [rule for rule in RULES if rule.startswith("profile ")]
    assert header == (
        "profile frame_gallery flags=(attach_disconnected,mediate_deleted,complain) {"
    )
    assert RULES[-1] == "}"
    assert PROFILE.count("{") - PROFILE.count("${") == PROFILE.count("}")


def test_every_rule_is_complete() -> None:
    for rule in BODY:
        assert rule.startswith("#include") or rule.endswith(","), rule


def test_only_the_needed_capabilities() -> None:
    capabilities = {rule.split()[1].rstrip(",") for rule in BODY if rule.startswith("capability")}
    assert capabilities == {"setuid", "setgid", "chown", "kill"}


def test_raw_and_packet_sockets_are_denied() -> None:
    assert "deny network raw," in BODY
    assert "deny network packet," in BODY
    networks = {rule for rule in BODY if rule.startswith("network ")}
    assert networks == {
        "network inet stream,",
        "network inet6 stream,",
        "network inet dgram,",
        "network inet6 dgram,",
        "network unix stream,",
    }


def test_the_s6_overlay_rules_are_the_official_ones() -> None:
    position = BODY.index(S6_EXAMPLE[0])
    assert tuple(BODY[position : position + len(S6_EXAMPLE)]) == S6_EXAMPLE


def test_media_is_read_only_except_the_preview() -> None:
    """§17.6: /media read-only; preview/ the only writable place; only
    frame_gallery/, preview/, and library/ may be created."""
    media = [rule for rule in BODY if rule.startswith("/media/")]
    assert media == [
        "/media/ r,",
        "/media/** r,",
        "/media/frame_gallery/ w,",
        "/media/frame_gallery/library/ w,",
        "/media/frame_gallery/preview/{,**} rw,",
    ]


def test_state_and_scratch_space_are_writable() -> None:
    assert "/data/{,**} rwk," in BODY
    assert "/tmp/{,**} rwk," in BODY  # noqa: S108 - a profile rule, not a path in use


def test_nothing_runs_unconfined() -> None:
    for rule in BODY:
        assert not re.search(r"\b[uUpPcC]x\b", rule), rule
    assert "/opt/frame-gallery/** mr," in BODY
