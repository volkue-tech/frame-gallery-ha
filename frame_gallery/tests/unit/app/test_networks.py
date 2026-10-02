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


def test_rows_without_the_expected_form_are_skipped() -> None:
    table = "\n".join(
        [
            HEADER,
            "eth0\t00201EAC",  # too short
            row("XYZ01EAC", "00FEFFFF"),  # not hexadecimal
            row("00201EAC", "00FE"),  # not eight digits
            row("0000A8C0", "00FF00FF"),  # not a prefix: 255.0.255.0
            row("00201EAC", "00FEFFFF"),
            row("00201EAC", "00FEFFFF", iface="eth1"),  # a repeat
            "",
        ]
    )
    assert parse_route_table(table, "little") == (IPv4Network("172.30.32.0/23"),)


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
    [None, b"x" * (MAX_ROUTE_TABLE_BYTES + 1), b"Iface\n\xff\n"],
    ids=["missing", "oversize", "not-ascii"],
)
def test_an_unreadable_table_fails_closed_on_linux(tmp_path: Path, content: bytes | None) -> None:
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
