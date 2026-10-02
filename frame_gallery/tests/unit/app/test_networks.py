"""The container's own networks (app/networks.py; §15.4, D-125, D-148)."""

from __future__ import annotations

from ipaddress import IPv4Network
from pathlib import Path

import pytest

from frame_gallery.app.networks import (
    MAX_ROUTE_TABLE_BYTES,
    ContainerNetworks,
    parse_route_table,
)
from frame_gallery.config.options import ConfigError

HEADER = "Iface\tDestination\tGateway \tFlags\tRefCnt\tUse\tMetric\tMask\t\tMTU\tWindow\tIRTT"


def row(destination: str, mask: str, iface: str = "eth0", gateway: str = "00000000") -> str:
    return f"{iface}\t{destination}\t{gateway}\t0001\t0\t0\t0\t{mask}\t0\t0\t0"


# The routes of an app container on the Supervisor's network, as a
# little-endian kernel writes them: the default route via 172.30.32.1, the
# app network 172.30.32.0/23, and a second interface's 10.20.0.0/16.
HASSIO_TABLE = "\n".join(
    [
        HEADER,
        row("00000000", "00000000", gateway="01201EAC"),
        row("00201EAC", "00FEFFFF"),
        row("0000140A", "0000FFFF", iface="eth1"),
    ]
)


def test_the_route_table_gives_every_network_but_the_default_route() -> None:
    assert parse_route_table(HASSIO_TABLE, "little") == (
        IPv4Network("10.20.0.0/16"),
        IPv4Network("172.30.32.0/23"),
    )


def test_a_big_endian_kernel_writes_the_bytes_in_order() -> None:
    table = "\n".join([HEADER, row("AC1E2000", "FFFFFE00")])
    assert parse_route_table(table, "big") == (IPv4Network("172.30.32.0/23"),)


def test_repeats_and_empty_lines_are_left_out() -> None:
    table = "\n".join(
        [
            HEADER,
            row("00201EAC", "00FEFFFF"),
            "  ",
            row("00201EAC", "00FEFFFF", iface="eth1"),  # a repeat
            "",
        ]
    )
    assert parse_route_table(table, "little") == (IPv4Network("172.30.32.0/23"),)


@pytest.mark.parametrize(
    "line",
    [
        "eth0\t00201EAC",
        row("XYZ01EAC", "00FEFFFF"),
        row("00201EAC", "00FE"),
        row("0000A8C0", "00FF00FF"),  # 255.0.255.0
    ],
    ids=["too-short", "not-hexadecimal", "not-eight-digits", "not-a-prefix"],
)
def test_a_route_in_another_form_makes_the_table_unusable(line: str) -> None:
    """D-166: the TV-address rule depends on this table, so a table the app
    cannot understand never counts as one without networks."""
    table = "\n".join([HEADER, row("00201EAC", "00FEFFFF"), line])
    with pytest.raises(ValueError):  # noqa: PT011 - the reason does not matter
        parse_route_table(table, "little")


@pytest.mark.parametrize(
    "text",
    ["", "garbage that is not a route table\nfoo bar baz\n", "Iface\tDestination\n"],
    ids=["empty", "garbage", "short-header"],
)
def test_a_table_without_the_kernels_header_is_unusable(text: str) -> None:
    with pytest.raises(ValueError, match="not the kernel's route table"):
        parse_route_table(text, "little")


def test_a_host_route_and_unaligned_destinations_are_kept_as_networks() -> None:
    table = "\n".join([HEADER, row("0520A8C0", "FFFFFFFF"), row("0520A8C0", "00FFFFFF")])
    assert parse_route_table(table, "little") == (
        IPv4Network("192.168.32.0/24"),
        IPv4Network("192.168.32.5/32"),
    )


def test_a_header_alone_gives_no_network() -> None:
    assert parse_route_table(HEADER + "\n", "little") == ()


def test_the_table_is_read_on_linux_once(tmp_path: Path) -> None:
    table = tmp_path / "route"
    table.write_text(HASSIO_TABLE)
    networks = ContainerNetworks(table, platform="linux")
    first = networks.container_networks()
    table.unlink()
    assert networks.container_networks() is first
    assert IPv4Network("172.30.32.0/23") in first


def test_a_host_other_than_linux_has_no_route_table(tmp_path: Path) -> None:
    networks = ContainerNetworks(tmp_path / "absent", platform="darwin")
    assert networks.container_networks() == ()


@pytest.mark.parametrize(
    "content",
    [
        None,
        b"x" * (MAX_ROUTE_TABLE_BYTES + 1),
        b"Iface\n\xff\n",
        b"garbage that is not a route table\nfoo bar baz\n",
        (HEADER + "\neth0\tnot-a-route\n").encode(),
    ],
    ids=["missing", "oversize", "not-ascii", "not-the-kernels", "malformed-row"],
)
def test_an_unusable_table_fails_closed_on_linux(tmp_path: Path, content: bytes | None) -> None:
    table = tmp_path / "route"
    if content is not None:
        table.write_bytes(content)
    networks = ContainerNetworks(table, platform="linux")
    with pytest.raises(ConfigError) as error:
        networks.container_networks()
    (issue,) = error.value.issues
    assert issue.option == "tv_host"
    assert "could not read the container's own networks" in issue.message
    with pytest.raises(ConfigError):
        networks.container_networks()  # not remembered as empty


def test_this_hosts_own_table_parses() -> None:
    """On Linux the real table of the test's network namespace parses; on
    another host the production default yields no network."""
    networks = ContainerNetworks().container_networks()
    assert all(isinstance(network, IPv4Network) for network in networks)
