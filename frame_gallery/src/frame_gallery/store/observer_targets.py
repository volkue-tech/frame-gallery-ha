"""Bounded device pins, never a persisted permission to connect or resume."""

from __future__ import annotations

from collections.abc import Mapping
from ipaddress import IPv4Address
from pathlib import Path
from typing import Final

from frame_gallery.config.tv_address import validate_tv_host
from frame_gallery.errors import StateError
from frame_gallery.observer.model import DEVICE_ID
from frame_gallery.store.atomic import DocumentFile, DocumentSpec, ReadFailure, open_directory

FILE: Final = "observer-targets.json"
MAX_TARGETS: Final = 32
MAX_BYTES: Final = 16 * 1024


def _parse(document: Mapping[str, object]) -> dict[str, str]:
    targets = document.get("targets")
    if not isinstance(targets, dict) or len(targets) > MAX_TARGETS:
        raise ValueError("invalid observer targets")
    result = {}
    for host, identity in targets.items():
        if (
            not isinstance(host, str)
            or not isinstance(identity, str)
            or DEVICE_ID.fullmatch(identity) is None
        ):
            raise ValueError("invalid observer target")
        validate_tv_host(host, excluded_networks=())
        result[host] = identity
    return result


SPEC: Final = DocumentSpec("frame-gallery-observer-targets", 1, MAX_BYTES, _parse)


class TargetStore:
    def __init__(self, data: Path) -> None:
        self._data = data

    def targets(self) -> dict[str, str]:
        with open_directory(self._data, ("state",), create=True, mode=0o700) as directory:
            loaded = DocumentFile(directory, FILE, SPEC).load()
            if loaded.newer_version is not None or loaded.unreadable:
                raise StateError("observer device pins unavailable")
            if (
                loaded.value is None
                and directory.read_bytes(FILE, MAX_BYTES) is not ReadFailure.MISSING
            ):
                # No quarantine or backup fallback here: a damaged primary
                # stays in place and cannot become absence on a later call.
                raise StateError("observer device pins damaged")
            return loaded.value or {}

    def pin(self, host: IPv4Address, identity: str) -> None:
        targets = self.targets()
        key = str(host)
        if DEVICE_ID.fullmatch(identity) is None:
            raise ValueError("invalid observer device identity")
        previous = targets.get(key)
        if previous is not None and previous != identity:
            raise StateError("observer TV identity changed")
        if previous is None and len(targets) >= MAX_TARGETS:
            raise StateError("observer device pin capacity reached")
        if previous == identity:
            return
        with open_directory(self._data, ("state",), create=True, mode=0o700) as directory:
            DocumentFile(directory, FILE, SPEC).write(
                {"format": SPEC.format, "version": 1, "targets": dict(targets, **{key: identity})}
            )
