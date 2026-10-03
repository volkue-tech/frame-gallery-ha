"""Reads helper states through the Supervisor's Core API proxy (§15.3, D-112).

Each configured helper is read with exactly one request, and there are at
most four helpers:

- ``GET http://supervisor/core/api/states/<entity_id>``, where the entity ID
  is re-validated with ``fullmatch`` and percent-encoded;
- the name ``supervisor`` is resolved once per run, and every address must be
  private and inside one of the container's own networks (which include the
  Supervisor's internal network), so the token can never reach another host;
- ``Authorization: Bearer <SUPERVISOR_TOKEN>`` is sent only here;
- no redirects and no retries; each read takes at most 3 s, clamped to the
  configuration deadline;
- at most 64 KiB of JSON, of which only the ``state`` string (at most 255
  characters) is used.

Any failure gives ``None`` for that helper, and the merge falls back to the
static value with exactly one warning (B3-B5); the reader itself logs its
reasons at INFO and DEBUG only. Home Assistant's ``unavailable`` and
``unknown`` states are returned as they are. Nothing is ever raised for a
failed read; only ``Cancelled`` (a stop request) propagates. Log lines name
the helper and the reason, never the token or the helper's value.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping, Sequence
from ipaddress import IPv4Network, IPv6Network
from typing import Final, NoReturn

from frame_gallery import __version__
from frame_gallery.budget.deadline import Deadline, DeadlineExceeded
from frame_gallery.budget.limits import CONNECT_S, DNS_S, HELPER_REQUEST_S, READ_S
from frame_gallery.config.filters import FilterField
from frame_gallery.config.options import HELPER_ENTITY_ID, TIMER_ENTITY_ID
from frame_gallery.errors import FrameGalleryError
from frame_gallery.net.policy import content_length, is_private_address, media_type, path_segment
from frame_gallery.net.wire import (
    IPAddress,
    Resolver,
    Transport,
    TransportFailure,
    WireRequest,
    WireResponse,
)

SUPERVISOR_HOST: Final = "supervisor"
SUPERVISOR_PORT: Final = 80
STATES_PATH: Final = "/core/api/states/"
MAX_BODY_BYTES: Final = 64 * 1024
MAX_STATE_LENGTH: Final = 255
READ_CHUNK: Final = 16 * 1024

_TOKEN: Final = re.compile(r"[\x21-\x7e]{1,4096}", re.ASCII)
"""A bearer token is printable ASCII without spaces (no header injection)."""

_log = logging.getLogger("frame_gallery.ha")


class _ReadFailed(FrameGalleryError):
    """One helper could not be read; the message is log-safe."""


def _fail(reason: str) -> NoReturn:
    raise _ReadFailed(reason)


class SupervisorHelperReader:
    """The production :class:`~frame_gallery.app.ports.HelperReader`."""

    def __init__(
        self,
        *,
        token: str | None,
        resolver: Resolver,
        transport: Transport,
        networks: Sequence[IPv4Network | IPv6Network],
    ) -> None:
        """``networks`` are the container's own interface networks
        (``NetworkInfo.container_networks()``); the Supervisor must be in one."""
        self._token = token
        self._resolver = resolver
        self._transport = transport
        self._networks = tuple(networks)

    def __repr__(self) -> str:
        return "SupervisorHelperReader(token=<hidden>)"

    def finish_loading(self, timer: str | None, deadline: Deadline) -> None:
        """D-176: one bounded cancel of the explicitly configured timer.

        No retry, redirect, arbitrary service, response body, or outcome change.
        The timer's own 150-second expiry remains the fail-safe.
        """
        if timer is None:
            return
        token = self._token
        if (
            TIMER_ENTITY_ID.fullmatch(timer) is None
            or token is None
            or _TOKEN.fullmatch(token) is None
        ):
            _log.warning("loading timer cannot be notified: invalid timer or missing token")
            return
        attempt = deadline.child(2.0, "loading timer")
        try:
            addresses = self._resolve(attempt)
            body = json.dumps({"entity_id": timer}, separators=(",", ":")).encode("ascii")
            request = WireRequest(
                address=addresses[0],
                host=SUPERVISOR_HOST,
                port=SUPERVISOR_PORT,
                tls=False,
                target="/core/api/services/timer/cancel",
                method="POST",
                body=body,
                headers={
                    "Host": SUPERVISOR_HOST,
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body)),
                    "Connection": "close",
                },
            )
            response = self._transport.open(
                request,
                connect_timeout=attempt.clamp(CONNECT_S),
                exchange_timeout=attempt.clamp(2.0),
            )
            try:
                if response.status != 200:
                    _log.warning("loading timer notification failed: HTTP %s", response.status)
                else:
                    _log.info("loading timer completion acknowledged")
            finally:
                response.close()
        except (_ReadFailed, TransportFailure, DeadlineExceeded):
            _log.warning("loading timer notification unavailable; timer will expire normally")

    def read(
        self, helpers: Mapping[FilterField, str], deadline: Deadline
    ) -> Mapping[FilterField, str | None]:
        results: dict[FilterField, str | None] = dict.fromkeys(helpers)
        if not helpers:
            return results
        token = self._token
        if token is None or _TOKEN.fullmatch(token) is None:
            _log.info("helpers are configured, but no usable Supervisor token is available")
            return results
        try:
            addresses = self._resolve(deadline)
        except _ReadFailed as exc:
            _log.info("the Supervisor cannot be reached: %s", exc)
            return results
        for field, entity_id in helpers.items():
            try:
                results[field] = self._read_one(entity_id, token, addresses, deadline)
            except _ReadFailed as exc:
                _log.debug("%s_helper could not be read: %s", field.value, exc)
        return results

    def _resolve(self, deadline: Deadline) -> Sequence[IPAddress]:
        try:
            addresses = self._resolver.resolve(
                SUPERVISOR_HOST, SUPERVISOR_PORT, deadline.clamp(DNS_S)
            )
        except TransportFailure as exc:
            _fail(f"name resolution failed ({exc.detail})")
        except DeadlineExceeded:
            _fail("no time left")
        if not addresses or not all(self._trusted(address) for address in addresses):
            _fail("the name did not resolve to an address in the container's networks")
        return addresses

    def _trusted(self, address: IPAddress) -> bool:
        return is_private_address(address) and any(
            address.version == network.version and address in network for network in self._networks
        )

    def _read_one(
        self,
        entity_id: str,
        token: str,
        addresses: Sequence[IPAddress],
        deadline: Deadline,
    ) -> str:
        try:
            segment = path_segment(entity_id, HELPER_ENTITY_ID)
        except ValueError:
            _fail("invalid entity ID")
        attempt = deadline.child(HELPER_REQUEST_S, "helper read")
        request = WireRequest(
            address=addresses[0],
            host=SUPERVISOR_HOST,
            port=SUPERVISOR_PORT,
            tls=False,
            target=STATES_PATH + segment,
            headers={
                "Host": SUPERVISOR_HOST,
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Accept-Encoding": "identity",
                "User-Agent": f"FrameGallery/{__version__}",
                "Connection": "close",
            },
        )
        try:
            response = self._transport.open(
                request,
                connect_timeout=attempt.clamp(CONNECT_S),
                exchange_timeout=attempt.clamp(HELPER_REQUEST_S),
            )
        except TransportFailure as exc:
            _fail(f"{exc.stage.value} failed")
        except DeadlineExceeded:
            _fail("no time left")
        try:
            if response.status != 200:
                _fail(f"HTTP {response.status}")
            if media_type(response.header("content-type")) != "application/json":
                _fail("not JSON")
            encoding = (response.header("content-encoding") or "identity").strip().lower()
            if encoding != "identity":
                _fail("unexpected content encoding")
            try:
                declared = content_length(response.header("content-length"))
            except ValueError:
                _fail("invalid Content-Length")
            if declared is not None and declared > MAX_BODY_BYTES:
                _fail("response too large")
            body = self._read_body(response, attempt)
        finally:
            response.close()
        if declared is not None and len(body) != declared:
            _fail("response shorter than declared")
        return _state(body)

    def _read_body(self, response: WireResponse, attempt: Deadline) -> bytes:
        body = bytearray()
        while True:
            try:
                chunk = response.read(READ_CHUNK, attempt.clamp(READ_S))
            except TransportFailure:
                _fail("the response could not be read")
            except DeadlineExceeded:
                _fail("no time left")
            if not chunk:
                return bytes(body)
            body += chunk
            if len(body) > MAX_BODY_BYTES:
                _fail("response too large")


def _reject_constant(name: str) -> NoReturn:
    msg = f"non-standard JSON constant {name}"
    raise ValueError(msg)


def _state(body: bytes) -> str:
    """The ``state`` string of a Core API state object."""
    try:
        document: object = json.loads(body.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, ValueError, RecursionError):
        _fail("invalid JSON")
    if not isinstance(document, dict):
        _fail("not a state object")
    state = document.get("state")
    if not isinstance(state, str):
        _fail("no state")
    if len(state) > MAX_STATE_LENGTH:
        _fail("state too long")
    return state
