"""Television address validation (§15.4, D-125, accepted).

``tv_host`` must be an IPv4 literal inside an RFC 1918 private range, and
outside the container's own networks (including the Supervisor's internal
network), which are discovered at run time and passed in. No DNS is
involved, and no address is ever a default.
"""

from __future__ import annotations

import enum
import re
from collections.abc import Sequence
from ipaddress import IPv4Address, IPv4Network
from typing import Final

PRIVATE_NETWORKS: Final = (
    IPv4Network("10.0.0.0/8"),
    IPv4Network("172.16.0.0/12"),
    IPv4Network("192.168.0.0/16"),
)
"""The accepted RFC 1918 ranges."""

_DOTTED_QUAD: Final = re.compile(r"(?:0|[1-9][0-9]{0,2})(?:\.(?:0|[1-9][0-9]{0,2})){3}", re.ASCII)
"""Four ASCII decimal octets without leading zeros; the range is checked after."""


class AddressProblem(enum.StrEnum):
    """Why a television address was rejected."""

    REQUIRED = "required"
    NOT_TEXT = "not_text"
    FORMAT = "format"
    OCTET_RANGE = "octet_range"
    UNSPECIFIED = "unspecified"
    LOOPBACK = "loopback"
    LINK_LOCAL = "link_local"
    MULTICAST = "multicast"
    BROADCAST = "broadcast"
    NOT_PRIVATE = "not_private"
    CONTAINER_NETWORK = "container_network"


class TvAddressError(ValueError):
    """The television address is not acceptable; the message is user-facing."""

    def __init__(self, problem: AddressProblem, message: str) -> None:
        super().__init__(message)
        self.problem = problem


_REQUIRED: Final = (
    "The television IP address is required. Enter the IPv4 address of your Frame TV "
    "(reserve it in your router so that it does not change)."
)
_NOT_TEXT: Final = "The television IP address must be text, such as four numbers separated by dots."
_FORMAT: Final = (
    "The television IP address must be an IPv4 address: four numbers separated by dots, "
    "without spaces, leading zeros, a port, or a prefix length. Host names and IPv6 "
    "addresses are not supported."
)
_OCTET_RANGE: Final = "Each of the four numbers in the television IP address must be 0 to 255."

_SPECIAL: Final = (
    (
        IPv4Network("0.0.0.0/32"),
        AddressProblem.UNSPECIFIED,
        "The television IP address {address} is the unspecified address, not a device.",
    ),
    (
        IPv4Network("127.0.0.0/8"),
        AddressProblem.LOOPBACK,
        (
            "The television IP address {address} is a loopback address, which points back "
            "at the app itself."
        ),
    ),
    (
        IPv4Network("169.254.0.0/16"),
        AddressProblem.LINK_LOCAL,
        (
            "The television IP address {address} is a link-local address, which a device "
            "uses only when the network gave it no address. Reserve a fixed address for the "
            "TV in your router."
        ),
    ),
    (
        IPv4Network("224.0.0.0/4"),
        AddressProblem.MULTICAST,
        "The television IP address {address} is a multicast address, not a single device.",
    ),
    (
        IPv4Network("255.255.255.255/32"),
        AddressProblem.BROADCAST,
        "The television IP address {address} is the broadcast address, not a single device.",
    ),
)
"""Checked in this order, before the private-range rule, for specific messages."""

_NOT_PRIVATE: Final = (
    "The television IP address {address} must be a private (RFC 1918) address on your home "
    "network: 10.0.0.0/8, 172.16.0.0/12, or 192.168.0.0/16."
)
_CONTAINER: Final = (
    "The television IP address {address} is inside the app's own container network "
    "({network}). Enter the address of the TV on your home network."
)


def validate_tv_host(value: object, *, excluded_networks: Sequence[IPv4Network]) -> IPv4Address:
    """Return the validated RFC 1918 IPv4 literal or raise :class:`TvAddressError`.

    ``excluded_networks`` are the container's own interface networks and the
    Supervisor's internal network, discovered at run time (never hard-coded).
    Error messages echo the address only once it parsed as an IPv4 literal.
    """
    if value is None:
        raise TvAddressError(AddressProblem.REQUIRED, _REQUIRED)
    if not isinstance(value, str):
        raise TvAddressError(AddressProblem.NOT_TEXT, _NOT_TEXT)
    if not value.strip():
        raise TvAddressError(AddressProblem.REQUIRED, _REQUIRED)
    if _DOTTED_QUAD.fullmatch(value) is None:
        raise TvAddressError(AddressProblem.FORMAT, _FORMAT)
    octets = [int(part) for part in value.split(".")]
    if any(octet > 255 for octet in octets):
        raise TvAddressError(AddressProblem.OCTET_RANGE, _OCTET_RANGE)
    address = IPv4Address(bytes(octets))
    for network, problem, template in _SPECIAL:
        if address in network:
            raise TvAddressError(problem, template.format(address=address))
    if not any(address in network for network in PRIVATE_NETWORKS):
        raise TvAddressError(AddressProblem.NOT_PRIVATE, _NOT_PRIVATE.format(address=address))
    for network in excluded_networks:
        if address in network:
            message = _CONTAINER.format(address=address, network=network)
            raise TvAddressError(AddressProblem.CONTAINER_NETWORK, message)
    return address
