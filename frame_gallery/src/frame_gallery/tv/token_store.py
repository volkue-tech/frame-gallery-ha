"""The television pairing token (§12.2, §13.1).

The token the television issues on the first accepted pairing is kept in
``/data/tv/<address>.token``, for example ``/data/tv/192-168-1-20.token``:
mode 0600, written with the store's atomic primitive, never through a
symbolic link, and excluded from backups (``backup_exclude: tv/**``). Only
the current address's token is kept; tokens of other addresses are removed.

A token comes from the television and is untrusted: it must be 6 to 64
ASCII letters or digits (``TOKEN_PATTERN``). Every token read or installed is
registered with the process-wide redactor, so no log line can show it
(§18.1, D-145).
"""

from __future__ import annotations

import logging
from ipaddress import IPv4Address
from pathlib import Path
from typing import Final

from frame_gallery.errors import StateError
from frame_gallery.logs.redact import active_redactor
from frame_gallery.store.atomic import (
    Directory,
    ReadFailure,
    errno_name,
    open_directory,
)
from frame_gallery.tv.contract import TOKEN_PATTERN

TOKEN_DIRECTORY: Final = "tv"  # noqa: S105 - a directory name, not a secret
TOKEN_SUFFIX: Final = ".token"  # noqa: S105 - a file suffix, not a secret
MAX_TOKEN_FILE_BYTES: Final = 256
SCAN_LIMIT: Final = 64

_log = logging.getLogger("frame_gallery.tv")


def parse_token(data: bytes) -> str | None:
    """The token in ``data``: its first line without surrounding whitespace,
    if it has the expected form; otherwise ``None``."""
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError:
        return None
    lines = text.splitlines()
    token = lines[0].strip() if lines else ""
    return token if TOKEN_PATTERN.fullmatch(token) else None


def _register(token: str) -> None:
    redactor = active_redactor()
    if redactor is not None:
        redactor.add_secret(token)


def token_file_name(host: IPv4Address) -> str:
    return str(host).replace(".", "-") + TOKEN_SUFFIX


class TokenStore:
    """The pairing token of one television address, below ``<data>/tv``."""

    def __init__(self, data_root: Path, host: IPv4Address) -> None:
        self._data_root = data_root
        self._name = token_file_name(host)

    def load(self) -> str | None:
        """The stored token, or ``None`` when there is none or it is unusable.
        Never raises."""
        try:
            directory = open_directory(self._data_root, (TOKEN_DIRECTORY,))
        except StateError as exc:
            _log.debug("no stored token: %s", exc)
            return None
        with directory:
            data = directory.read_bytes(self._name, MAX_TOKEN_FILE_BYTES)
        if isinstance(data, ReadFailure):
            if data is not ReadFailure.MISSING:
                _log.warning("the stored television token is %s; pairing again", data.value)
            return None
        token = parse_token(data)
        if token is None:
            _log.warning("the stored television token is invalid; pairing again")
            return None
        _register(token)
        return token

    def install(self, token: str) -> None:
        """Store ``token`` (mode 0600) and remove every other address's token.
        Raises ``StateError`` for a token of the wrong form or a failed write."""
        if TOKEN_PATTERN.fullmatch(token) is None:
            msg = "refusing to store a token of an unexpected form"
            raise StateError(msg)
        _register(token)
        with open_directory(
            self._data_root, (TOKEN_DIRECTORY,), create=True, mode=0o700
        ) as directory:
            directory.write(self._name, (token + "\n").encode("ascii"), mode=0o600)
            self._remove_others(directory)

    def remove(self) -> None:
        """Forget the token, for example after the television rejected it.
        Never raises."""
        try:
            with open_directory(self._data_root, (TOKEN_DIRECTORY,)) as directory:
                directory.unlink(self._name)
        except StateError as exc:
            _log.debug("no token to remove: %s", exc)

    def _remove_others(self, directory: Directory) -> None:
        try:
            names = directory.names(SCAN_LIMIT)
        except OSError as exc:
            _log.warning("old television tokens were not removed (%s)", errno_name(exc))
            return
        for name in names:
            if name != self._name and name.endswith(TOKEN_SUFFIX):
                directory.unlink(name)
