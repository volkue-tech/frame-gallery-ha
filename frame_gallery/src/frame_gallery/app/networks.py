"""The container's own networks (§15.4, D-125, D-148).

The television address must not lie in a network of the container itself,
which includes the Supervisor's internal network, and the helper reader
sends the Supervisor token only to an address inside one of them. On Linux
the networks come from the kernel's IPv4 route table of this network
namespace, ``/proc/net/route``: every route except the default route names a
network the container reaches over one of its interfaces. On Linux a table
that is missing, oversized, not ASCII, or not in the kernel's form fails
closed (``config_invalid``): a table the app cannot understand must not
count as one without networks. A table with only its header is valid (a
container without a network has one). A development host has no such
table, and the list is empty there.
"""

from __future__ import annotations

import os
import re
import sys
from ipaddress import IPv4Address, IPv4Network
from pathlib import Path
from typing import Final, Literal

from frame_gallery.config.options import ConfigError, ConfigIssue

ROUTE_TABLE: Final = Path("/proc/net/route")
MAX_ROUTE_TABLE_BYTES: Final = 64 * 1024
READ_CHUNK: Final = 4096

_HEX: Final = re.compile(r"[0-9A-Fa-f]{8}")
_IFACE: Final = 0
_DESTINATION: Final = 1
_MASK: Final = 7
_UNKNOWN: Final = (
    "The app could not read the container's own networks, so it cannot check the TV "
    "address against them. Start the app again; if this persists, report it."
)


def parse_route_table(
    text: str, byteorder: Literal["little", "big"] = sys.byteorder
) -> tuple[IPv4Network, ...]:
    """The networks of the routes in ``text`` (the format of ``/proc/net/route``),
    without the default route, sorted and without repeats.

    The kernel writes each address as the hexadecimal value of its four bytes
    in network order, read as a number in the host's byte order. Raises
    ``ValueError`` unless the first line is the kernel's header and every
    other non-empty line is a route in that form, with a prefix mask.
    """
    lines = text.splitlines()
    header = lines[0].split() if lines else []
    if len(header) <= _MASK or (header[_IFACE], header[_DESTINATION], header[_MASK]) != (
        "Iface",
        "Destination",
        "Mask",
    ):
        msg = "not the kernel's route table"
        raise ValueError(msg)
    found: set[IPv4Network] = set()
    for line in lines[1:]:
        fields = line.split()
        if not fields:
            continue
        if (
            len(fields) <= _MASK
            or _HEX.fullmatch(fields[_DESTINATION]) is None
            or _HEX.fullmatch(fields[_MASK]) is None
        ):
            msg = "a route in an unknown form"
            raise ValueError(msg)
        address = IPv4Address(int(fields[_DESTINATION], 16).to_bytes(4, byteorder))
        netmask = IPv4Address(int(fields[_MASK], 16).to_bytes(4, byteorder))
        if int(netmask) == 0:
            continue  # the default route
        # A mask that is not a prefix raises ValueError too.
        found.add(IPv4Network((address, str(netmask)), strict=False))
    return tuple(sorted(found))


class ContainerNetworks:
    """The ``NetworkInfo`` port. The route table is read at most once."""

    def __init__(self, route_table: Path = ROUTE_TABLE, *, platform: str = sys.platform) -> None:
        self._route_table = route_table
        self._linux = platform.startswith("linux")
        self._networks: tuple[IPv4Network, ...] | None = None

    def container_networks(self) -> tuple[IPv4Network, ...]:
        """The container's networks; empty on a host other than Linux.

        Raises ``ConfigError`` on Linux when the table cannot be read or
        understood: the TV address could not be checked then, so the run
        fails closed (``config_invalid``).
        """
        if self._networks is None:
            self._networks = self._read() if self._linux else ()
        return self._networks

    def _read(self) -> tuple[IPv4Network, ...]:
        data = bytearray()
        try:
            fd = os.open(self._route_table, os.O_RDONLY | os.O_CLOEXEC)
            try:
                while chunk := os.read(fd, READ_CHUNK):
                    data += chunk
                    if len(data) > MAX_ROUTE_TABLE_BYTES:
                        raise ConfigError([ConfigIssue("tv_host", _UNKNOWN)])
            finally:
                os.close(fd)
            return parse_route_table(data.decode("ascii"))
        except (OSError, ValueError):  # UnicodeDecodeError is a ValueError
            raise ConfigError([ConfigIssue("tv_host", _UNKNOWN)]) from None
