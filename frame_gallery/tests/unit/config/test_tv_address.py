"""Television address validation (§15.4, D-125, accepted; B1, B7)."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network

import pytest

from frame_gallery.config.tv_address import (
    PRIVATE_NETWORKS,
    AddressProblem,
    TvAddressError,
    validate_tv_host,
)

CONTAINER = IPv4Network("172.30.32.0/23")
"""A synthetic container network for the tests (injected, never hard-coded)."""


def _problem(value: object, excluded: tuple[IPv4Network, ...] = ()) -> TvAddressError:
    with pytest.raises(TvAddressError) as caught:
        validate_tv_host(value, excluded_networks=excluded)
    return caught.value


def test_private_networks_are_rfc_1918() -> None:
    expected = (
        IPv4Network("10.0.0.0/8"),
        IPv4Network("172.16.0.0/12"),
        IPv4Network("192.168.0.0/16"),
    )
    assert expected == PRIVATE_NETWORKS


@pytest.mark.parametrize(
    "value",
    [
        "10.0.0.0",
        "10.0.0.5",
        "10.255.255.255",
        "172.16.0.0",
        "172.16.4.2",
        "172.31.255.255",
        "192.168.0.0",
        "192.168.1.20",
        "192.168.255.255",
        "10.0.0.10",
        "10.100.200.250",
    ],
)
def test_accepts_rfc_1918_literals(value: str) -> None:
    address = validate_tv_host(value, excluded_networks=())
    assert isinstance(address, IPv4Address)
    assert address == IPv4Address(value)


def test_error_is_a_value_error() -> None:
    assert issubclass(TvAddressError, ValueError)


@pytest.mark.parametrize("value", [None, "", " ", "   ", "\t\n", "\u3000"])
def test_missing_address_is_required(value: object) -> None:
    error = _problem(value)
    assert error.problem is AddressProblem.REQUIRED
    assert "The television IP address is required." in str(error)


@pytest.mark.parametrize("value", [10, 167772165, 10.5, True, b"10.0.0.5", ["10.0.0.5"]])
def test_non_text_is_rejected(value: object) -> None:
    error = _problem(value)
    assert error.problem is AddressProblem.NOT_TEXT
    assert "must be text" in str(error)


def test_ipv4_address_object_is_not_text() -> None:
    assert _problem(IPv4Address("10.0.0.5")).problem is AddressProblem.NOT_TEXT


@pytest.mark.parametrize(
    "value",
    [
        "10.0.0",
        "10.0.0.5.6",
        "10.0.0.5.",
        ".10.0.0.5",
        "10..0.5",
        "10.0.0.",
        "010.0.0.5",
        "10.0.0.05",
        "10.00.0.5",
        "10.0.0.00",
        " 10.0.0.5",
        "10.0.0.5 ",
        "10.0.0.5\n",
        "10.0. 0.5",
        "\uff11\uff10.0.0.1",  # full-width digits
        "10.0.0.\u0665",  # Arabic-Indic digit
        "10.0.0.5/24",
        "10.0.0.5:8001",
        "10.0.0.5%eth0",
        "fd00::1",
        "::ffff:10.0.0.5",
        "frame-tv.local",
        "tv",
        "1000.0.0.1",
        "0x0a.0.0.1",
        "10.0.0.+5",
        "10.0.0.-5",
        "10,0,0,5",
        "167772165",
    ],
)
def test_malformed_literals_are_rejected_without_echo(value: str) -> None:
    error = _problem(value)
    assert error.problem is AddressProblem.FORMAT
    assert "IPv4 address" in str(error)
    if value.strip():
        assert value.strip() not in str(error)


@pytest.mark.parametrize("value", ["256.0.0.1", "10.0.0.256", "10.999.0.1", "192.168.300.1"])
def test_octets_above_255_are_rejected(value: str) -> None:
    error = _problem(value)
    assert error.problem is AddressProblem.OCTET_RANGE
    assert "0 to 255" in str(error)


@pytest.mark.parametrize(
    ("value", "problem", "phrase"),
    [
        ("0.0.0.0", AddressProblem.UNSPECIFIED, "unspecified"),  # noqa: S104
        ("127.0.0.1", AddressProblem.LOOPBACK, "loopback"),
        ("127.255.255.254", AddressProblem.LOOPBACK, "loopback"),
        ("169.254.0.0", AddressProblem.LINK_LOCAL, "link-local"),
        ("169.254.1.1", AddressProblem.LINK_LOCAL, "link-local"),
        ("169.254.255.255", AddressProblem.LINK_LOCAL, "link-local"),
        ("224.0.0.1", AddressProblem.MULTICAST, "multicast"),
        ("239.255.255.250", AddressProblem.MULTICAST, "multicast"),
        ("255.255.255.255", AddressProblem.BROADCAST, "broadcast"),
    ],
)
def test_special_addresses_have_specific_messages(
    value: str, problem: AddressProblem, phrase: str
) -> None:
    error = _problem(value)
    assert error.problem is problem
    assert phrase in str(error)
    assert value in str(error)


@pytest.mark.parametrize(
    "value",
    [
        "0.0.0.1",
        "9.255.255.255",
        "11.0.0.0",
        "8.8.8.8",
        "100.64.0.1",  # carrier-grade NAT
        "126.255.255.255",
        "128.0.0.1",
        "169.253.255.255",
        "169.255.0.0",
        "172.15.255.255",
        "172.32.0.0",
        "192.0.2.1",
        "192.167.255.255",
        "192.169.0.0",
        "198.18.0.1",
        "223.255.255.255",
        "240.0.0.1",  # reserved
        "255.255.255.254",
    ],
)
def test_non_private_addresses_are_rejected(value: str) -> None:
    error = _problem(value)
    assert error.problem is AddressProblem.NOT_PRIVATE
    assert "private (RFC 1918)" in str(error)
    assert value in str(error)


def test_address_in_the_container_network_is_rejected() -> None:
    error = _problem("172.30.32.5", (CONTAINER,))
    assert error.problem is AddressProblem.CONTAINER_NETWORK
    assert "container network (172.30.32.0/23)" in str(error)
    assert "172.30.32.5" in str(error)


def test_address_outside_the_container_network_is_accepted() -> None:
    assert validate_tv_host("172.30.34.1", excluded_networks=[CONTAINER]) == IPv4Address(
        "172.30.34.1"
    )


def test_every_excluded_network_is_checked() -> None:
    excluded = (IPv4Network("10.0.5.0/24"), CONTAINER, IPv4Network("192.168.64.0/20"))
    error = _problem("172.30.33.2", excluded)
    assert error.problem is AddressProblem.CONTAINER_NETWORK
    assert "172.30.32.0/23" in str(error)
    assert _problem("10.0.5.1", excluded).problem is AddressProblem.CONTAINER_NETWORK
    assert _problem("192.168.70.1", excluded).problem is AddressProblem.CONTAINER_NETWORK
    assert validate_tv_host("192.168.1.20", excluded_networks=excluded) == IPv4Address(
        "192.168.1.20"
    )


def test_range_rules_come_before_the_container_rule() -> None:
    excluded = (IPv4Network("127.0.0.0/8"), IPv4Network("100.64.0.0/10"))
    assert _problem("127.0.0.1", excluded).problem is AddressProblem.LOOPBACK
    assert _problem("100.64.0.1", excluded).problem is AddressProblem.NOT_PRIVATE
