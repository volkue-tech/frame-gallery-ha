"""The draft AppArmor profile (apparmor.txt; ARCHITECTURE.md §17.6, D-129).

The profile cannot be loaded here (that needs a Linux kernel and
apparmor_parser); these tests hold its rules to §17.6 and check the
structure that the parser needs."""

from __future__ import annotations

# ruff: noqa: S108 - these are policy patterns, not temporary-file creation
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
BODY: Final = RULES[
    RULES.index(next(r for r in RULES if r.startswith("profile "))) + 1 : RULES.index(
        next(r for r in RULES if r.startswith("profile image_worker"))
    )
]


def child(name: str) -> list[str]:
    start = RULES.index(next(r for r in RULES if r.startswith(f"profile {name} ")))
    end = RULES.index("}", start)
    return RULES[start + 1 : end]


S6_EXAMPLE: Final = (
    "/init rix,",
    "/bin/** rix,",
    "/usr/bin/** rix,",
    "/run/{s6,s6-rc*,service}/** rix,",
    "/package/** rix,",
    "/command/** rix,",
    "/etc/services.d/** rwix,",
    "/etc/cont-init.d/** rwix,",
    "/etc/cont-finish.d/** rwix,",
    "/run/{,**} rwk,",
    "/dev/tty rw,",
)
"""S6 rules derived from the official example, with script read permission."""


def test_the_parent_and_children_are_enforced() -> None:
    assert RULES[0] == "#include <tunables/global>" or PROFILE.startswith(
        "#include <tunables/global>"
    )
    headers = [rule for rule in RULES if rule.startswith("profile ")]
    assert headers == [
        f"profile {name} flags=(attach_disconnected,mediate_deleted) {{"
        for name in ("frame_gallery", "image_worker", "tv_worker")
    ]
    assert "complain" not in PROFILE
    assert RULES[-1] == "}"
    assert PROFILE.count("{") - PROFILE.count("${") == PROFILE.count("}")


def test_every_rule_is_complete() -> None:
    for rule in [*BODY, *child("image_worker"), *child("tv_worker")]:
        assert rule.startswith("#include") or rule.endswith(","), rule


def test_only_the_needed_capabilities() -> None:
    """The drop to 65534 (setuid, setgid), the workspace handed to the
    worker's group (chown, and fsetid for its setgid folders), reading the
    worker's output (Docker's existing dac_override), and ending workers (kill)."""
    capabilities = {rule.split()[1].rstrip(",") for rule in BODY if rule.startswith("capability")}
    assert capabilities == {"setuid", "setgid", "chown", "fsetid", "dac_override", "kill"}
    assert "dac_read_search" not in capabilities


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
    assert "/tmp/{,**} rwk," in BODY


def test_backup_links_are_parent_only_and_pair_specific() -> None:
    assert [rule for rule in BODY if rule.startswith("link ")] == [
        "link subset /data/state/history.json.bak.tmp-* -> /data/state/history.json,",
        "link subset /data/state/upload_ledger.json.bak.tmp-* -> /data/state/upload_ledger.json,",
    ]
    for name in ("image_worker", "tv_worker"):
        assert not any(rule.startswith("link ") for rule in child(name))


def test_nothing_runs_unconfined() -> None:
    for rule in BODY:
        assert not re.search(r"\b[uUpPcC]x\b", rule), rule
    assert "/opt/frame-gallery/** mr," in BODY


def test_child_privileges_and_one_way_transition() -> None:
    for name in ("image_worker", "tv_worker"):
        rules = child(name)
        assert {r for r in rules if r.startswith("capability")} == {
            "capability setuid,",
            "capability setgid,",
        }
        assert not any("change_profile" in r or re.search(r"\b[a-zA-Z]*x,", r) for r in rules)
        assert not any(r.startswith(("/data/", "/dev/shm/")) for r in rules)
    assert "change_profile -> **//image_worker," in BODY
    assert "change_profile -> **//tv_worker," in BODY


def test_image_worker_has_no_network_or_arbitrary_writes() -> None:
    rules = child("image_worker")
    assert "deny network," in rules
    assert not any(r.startswith("network ") for r in rules)
    writes = [r for r in rules if r.startswith("/") and re.search(r"\s\w*w\w*,", r)]
    assert writes == [
        "/dev/null rw,",
        "/tmp/frame-gallery/run-*/out/ rw,",
        "/tmp/frame-gallery/run-*/out/delivery-*.jpg rw,",
    ]


def test_tv_worker_only_reads_output_and_uses_ipv4_tcp() -> None:
    rules = child("tv_worker")
    assert [r for r in rules if r.startswith("network ")] == ["network inet stream,"]
    assert [r for r in rules if r.startswith("/tmp/")] == [
        "/tmp/frame-gallery/run-*/out/delivery-*.jpg r,"
    ]
    assert [r for r in rules if r.startswith("/") and re.search(r"\s\w*w\w*,", r)] == [
        "/dev/null rw,"
    ]
