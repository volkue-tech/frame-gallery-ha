"""The options the Supervisor writes for the app (§15.1, §17.5).

The Supervisor keeps the user's options in ``/data/options.json``. The file
is read once per run, below the ``/data`` anchor, without following a
symbolic link and never beyond 64 KiB, and parsed as strict JSON
(``decode_json``: no ``NaN`` or ``Infinity``). Anything else ends the run as
``config_invalid``, with a message that says what to do. The values stay
untrusted: ``config.options`` validates every one of them.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Final

from frame_gallery.budget.deadline import Deadline
from frame_gallery.config.options import (
    HELPER_OPTION_NAMES,
    ConfigError,
    ConfigIssue,
    loading_timer,
)
from frame_gallery.errors import StateError
from frame_gallery.store.atomic import ReadFailure, decode_json, open_directory

OPTIONS_NAME: Final = "options.json"
MAX_OPTIONS_BYTES: Final = 64 * 1024

_ISSUE: Final = "options"

_SAVE_AGAIN: Final = (
    " Open the app's Configuration tab, save the options again, and start the app again."
)
"""What to do about a damaged options file: saving makes the Supervisor
write it anew."""

_READ_FAILURES: Final = {
    ReadFailure.MISSING: (
        "The app has no saved options. Open the app's Configuration tab, enter the TV's "
        "address, save, and start the app again."
    ),
    ReadFailure.NOT_REGULAR: "The options file is not a regular file." + _SAVE_AGAIN,
    ReadFailure.OVERSIZE: "The options file is larger than 64 KiB." + _SAVE_AGAIN,
    ReadFailure.UNREADABLE: "The options file cannot be read." + _SAVE_AGAIN,
}
_NOT_JSON: Final = "The options file is not valid JSON." + _SAVE_AGAIN
_NOT_AN_OBJECT: Final = (
    "The options file does not hold an object of option names and values." + _SAVE_AGAIN
)


class OptionsFile:
    """The ``OptionsSource`` port over ``<data>/options.json``.

    The file is read at most once; later calls give the same result, so the
    entry point can look at the helper options before the run starts.
    """

    def __init__(self, data_root: Path) -> None:
        self._data_root = data_root
        self._raw: Mapping[str, object] | None = None
        self._error: ConfigError | None = None

    def load(self, deadline: Deadline) -> Mapping[str, object]:
        """The options as the Supervisor wrote them. Raises ``ConfigError``
        and ``DeadlineExceeded``."""
        deadline.check()
        return self._read()

    def helpers_configured(self) -> bool:
        """Whether any helper option is set, as ``config.options`` reads it
        (neither absent, ``null``, nor empty). ``False`` when the file cannot
        be read: the run then ends as ``config_invalid`` anyway. The entry
        point keeps the Supervisor token only when this is true (§17.5)."""
        try:
            raw = self._read()
        except ConfigError:
            return False
        return any(raw.get(name) not in (None, "") for name in HELPER_OPTION_NAMES)

    def _read(self) -> Mapping[str, object]:
        if self._error is not None:
            raise self._error
        if self._raw is None:
            try:
                self._raw = self._parse()
            except ConfigError as error:
                self._error = error
                raise
        return self._raw

    def loading_timer(self) -> str | None:
        """Independently validate the optional timer, even on a failed run."""
        try:
            return loading_timer(self._read().get("loading_timer"))
        except ConfigError:
            return None

    def _parse(self) -> Mapping[str, object]:
        try:
            with open_directory(self._data_root) as directory:
                data = directory.read_bytes(OPTIONS_NAME, MAX_OPTIONS_BYTES)
        except StateError:
            data = ReadFailure.UNREADABLE
        if isinstance(data, ReadFailure):
            raise ConfigError([ConfigIssue(_ISSUE, _READ_FAILURES[data])])
        try:
            document = decode_json(data)
        except ValueError:
            raise ConfigError([ConfigIssue(_ISSUE, _NOT_JSON)]) from None
        if not isinstance(document, dict):
            raise ConfigError([ConfigIssue(_ISSUE, _NOT_AN_OBJECT)])
        return document
