"""Logging configuration for the parent and, from Phase 5, the workers (§19).

One handler on the root logger writes UTC ISO-8601 lines. Its formatter
redacts the complete formatted text, including exception text and stack
information (§18.1); the same redactor becomes the active redactor for
untrusted text that is truncated before it is logged. Frame Gallery logs at
INFO or DEBUG; everything else, and the third-party loggers in particular,
stays at WARNING. ``urllib3`` is silenced completely: its warnings quote the
full request URL, query included, and unparsed response header data (§10),
and the gateway reports every failure itself.
"""

from __future__ import annotations

import contextlib
import logging
import sys
import time
from typing import Final, TextIO

from frame_gallery.config.options import LogLevel
from frame_gallery.logs.redact import Redactor, set_active_redactor

APP_LOGGER: Final = "frame_gallery"
THIRD_PARTY_LOGGERS: Final = ("PIL", "samsungtvws", "websocket")
SILENCED_LOGGERS: Final = ("urllib3",)
SILENT: Final = logging.CRITICAL + 10
"""Above every level a library uses: nothing from these loggers is emitted."""

LOG_FORMAT: Final = "%(asctime)s %(levelname)s %(name)s: %(message)s"
DATE_FORMAT: Final = "%Y-%m-%dT%H:%M:%SZ"

_LEVELS: Final = {LogLevel.INFO: logging.INFO, LogLevel.DEBUG: logging.DEBUG}


class RedactingFormatter(logging.Formatter):
    """Formats a record, then redacts the whole result. Timestamps are UTC."""

    def __init__(
        self, redactor: Redactor, fmt: str = LOG_FORMAT, datefmt: str = DATE_FORMAT
    ) -> None:
        super().__init__(fmt=fmt, datefmt=datefmt)
        self.converter = time.gmtime
        self._redactor = redactor

    def format(self, record: logging.LogRecord) -> str:
        return self._redactor.redact(super().format(record))


class _RedactingStreamHandler(logging.StreamHandler[TextIO]):
    """The handler :func:`configure_logging` installs, recognised by its marker."""

    frame_gallery_installed: Final = True

    def handleError(self, record: logging.LogRecord) -> None:  # noqa: N802 - logging API
        # The default prints the unredacted message and arguments to stderr.
        # Only fixed text is written here; the record itself is dropped.
        with contextlib.suppress(Exception):
            sys.stderr.write(f"--- logging error: a record from {record.name} was dropped ---\n")


def _is_installed(handler: logging.Handler) -> bool:
    return getattr(handler, "frame_gallery_installed", False) is True


def configure_logging(*, level: LogLevel, stream: TextIO, redactor: Redactor) -> logging.Logger:
    """Install the redacting handler on the root logger and set the levels.

    ``redactor`` also becomes the active redactor, which
    :func:`~frame_gallery.logs.summary.sanitize_for_log` applies before it
    truncates (§19; H3). Idempotent: a repeated call replaces only the
    handler an earlier call installed, and the active redactor. Returns the
    ``frame_gallery`` logger.
    """
    set_active_redactor(redactor)
    root = logging.getLogger()
    for handler in list(root.handlers):
        if _is_installed(handler):
            root.removeHandler(handler)
            handler.close()
    handler = _RedactingStreamHandler(stream)
    handler.setFormatter(RedactingFormatter(redactor))
    root.addHandler(handler)
    root.setLevel(logging.WARNING)
    for name in THIRD_PARTY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
    for name in SILENCED_LOGGERS:
        logging.getLogger(name).setLevel(SILENT)
    app_logger = logging.getLogger(APP_LOGGER)
    app_logger.setLevel(_LEVELS[level])
    return app_logger
