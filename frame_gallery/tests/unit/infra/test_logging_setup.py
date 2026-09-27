"""Logging setup: redaction of complete lines, UTC timestamps, levels (§19; H3)."""

from __future__ import annotations

import io
import logging
import re
import sys
from collections.abc import Iterator

import pytest

from frame_gallery.config.options import LogLevel
from frame_gallery.logs.redact import REDACTED, Redactor, active_redactor
from frame_gallery.logs.setup import (
    APP_LOGGER,
    SILENCED_LOGGERS,
    SILENT,
    THIRD_PARTY_LOGGERS,
    RedactingFormatter,
    configure_logging,
)
from frame_gallery.logs.summary import sanitize_for_log
from tests.support.clock import FAKE_EPOCH

SECRET = "tv-pairing-token-7c1f3a9b"  # noqa: S105 - a test value
SUPERVISOR_TOKEN = "c0ffee" * 10 + "c0de"  # a test value, 64 characters
LINE = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z (?P<level>[A-Z]+) (?P<name>\S+): (?P<msg>.*)"
)
TOUCHED_LOGGERS = (
    APP_LOGGER,
    *THIRD_PARTY_LOGGERS,
    *SILENCED_LOGGERS,
    "frame_gallery.selection",
    "other.library",
)


@pytest.fixture(autouse=True)
def _restore_logging() -> Iterator[None]:
    root = logging.getLogger()
    handlers = list(root.handlers)
    root_level = root.level
    levels = {name: logging.getLogger(name).level for name in TOUCHED_LOGGERS}
    try:
        yield
    finally:
        for handler in list(root.handlers):
            if handler not in handlers:
                root.removeHandler(handler)
                handler.close()
        for handler in handlers:
            if handler not in root.handlers:
                root.addHandler(handler)
        root.setLevel(root_level)
        for name, level in levels.items():
            logging.getLogger(name).setLevel(level)


def _installed(root: logging.Logger) -> list[logging.Handler]:
    return [h for h in root.handlers if getattr(h, "frame_gallery_installed", False)]


def _configure(
    level: LogLevel = LogLevel.INFO, secrets: tuple[str, ...] = (SECRET,)
) -> tuple[logging.Logger, io.StringIO]:
    stream = io.StringIO()
    logger = configure_logging(level=level, stream=stream, redactor=Redactor(secrets))
    return logger, stream


def test_returns_the_app_logger() -> None:
    logger, _ = _configure()
    assert logger is logging.getLogger("frame_gallery")


def test_line_format() -> None:
    logger, stream = _configure()
    logger.info("hello %s", "world")
    lines = stream.getvalue().splitlines()
    assert len(lines) == 1
    match = LINE.fullmatch(lines[0])
    assert match is not None
    assert match["level"] == "INFO"
    assert match["name"] == "frame_gallery"
    assert match["msg"] == "hello world"


def test_timestamps_are_utc_iso8601() -> None:
    formatter = RedactingFormatter(Redactor())
    record = logging.makeLogRecord(
        {
            "name": "frame_gallery",
            "levelname": "INFO",
            "levelno": logging.INFO,
            "msg": "started",
            "created": FAKE_EPOCH.timestamp(),
        }
    )
    assert formatter.format(record) == "2026-01-01T12:00:00Z INFO frame_gallery: started"


def test_info_level_hides_debug() -> None:
    logger, stream = _configure(LogLevel.INFO)
    logger.debug("per-candidate decision")
    logging.getLogger("frame_gallery.selection").debug("child decision")
    logger.info("selection summary")
    assert "decision" not in stream.getvalue()
    assert "selection summary" in stream.getvalue()


def test_debug_level_shows_debug() -> None:
    logger, stream = _configure(LogLevel.DEBUG)
    assert logger.level == logging.DEBUG
    logging.getLogger("frame_gallery.selection").debug("child decision")
    assert "DEBUG frame_gallery.selection: child decision" in stream.getvalue()


@pytest.mark.parametrize("name", [*THIRD_PARTY_LOGGERS, "other.library"])
def test_other_loggers_are_capped_at_warning(name: str) -> None:
    _, stream = _configure(LogLevel.DEBUG)
    other = logging.getLogger(name)
    other.debug("debug detail")
    other.info("info detail")
    other.warning("warning detail")
    output = stream.getvalue()
    assert "detail" in output
    assert "debug detail" not in output
    assert "info detail" not in output
    assert f"WARNING {name}: warning detail" in output


def test_levels_are_set() -> None:
    _configure(LogLevel.INFO)
    assert logging.getLogger().level == logging.WARNING
    assert logging.getLogger(APP_LOGGER).level == logging.INFO
    for name in THIRD_PARTY_LOGGERS:
        assert logging.getLogger(name).level == logging.WARNING
    assert THIRD_PARTY_LOGGERS == ("PIL", "samsungtvws", "websocket")
    assert SILENCED_LOGGERS == ("urllib3",)
    assert logging.getLogger("urllib3").level == SILENT


@pytest.mark.parametrize("name", ["urllib3", "urllib3.connection", "urllib3.connectionpool"])
def test_urllib3_is_silenced(name: str) -> None:
    # urllib3 warnings quote the full URL, query included, and unparsed
    # response header data (§10, D-147 item 16).
    _, stream = _configure(LogLevel.DEBUG)
    library = logging.getLogger(name)
    library.warning("Failed to parse headers (url=https://h/p?q=private): x")
    library.error("error detail")
    library.critical("critical detail")
    assert stream.getvalue() == ""


def test_repeated_calls_replace_only_their_own_handler() -> None:
    root = logging.getLogger()
    foreign_stream = io.StringIO()
    foreign = logging.StreamHandler(foreign_stream)
    root.addHandler(foreign)
    logger, first = _configure()
    logger, second = _configure()
    assert len(_installed(root)) == 1
    assert foreign in root.handlers
    logger.warning("once")
    assert first.getvalue() == ""
    assert second.getvalue().count("once") == 1
    assert "once" in foreign_stream.getvalue()


def test_secrets_in_messages_and_arguments_are_redacted() -> None:
    logger, stream = _configure()
    logger.info("token is %s", SECRET)
    logger.info(f"inline {SECRET}")
    logger.info("header %s", "Authorization: Bearer abc.def")
    output = stream.getvalue()
    assert SECRET not in output
    assert output.count(REDACTED) == 3


def test_the_redactor_becomes_the_active_redactor() -> None:
    first, second = Redactor(), Redactor()
    assert active_redactor() is None
    configure_logging(level=LogLevel.INFO, stream=io.StringIO(), redactor=first)
    assert active_redactor() is first
    configure_logging(level=LogLevel.INFO, stream=io.StringIO(), redactor=second)
    assert active_redactor() is second


@pytest.mark.parametrize("offset", [151, 163, 190])
def test_a_secret_cut_by_sanitize_never_reaches_the_log_h3(offset: int) -> None:
    assert len(SUPERVISOR_TOKEN) == 64
    logger, stream = _configure(secrets=(SUPERVISOR_TOKEN,))
    text = "e" * (offset - len("credential ")) + "credential " + SUPERVISOR_TOKEN + " rejected" * 10
    logger.error("the source failed: %s", sanitize_for_log(text))
    output = stream.getvalue()
    assert "credential [REDACTED" in output  # possibly cut, never the secret
    assert not any(
        SUPERVISOR_TOKEN[start : start + 6] in output for start in range(len(SUPERVISOR_TOKEN) - 5)
    )


def test_exception_text_and_stack_info_are_redacted_h3() -> None:
    logger, stream = _configure()

    def failing_call() -> None:
        msg = f"television refused token {SECRET}"
        raise RuntimeError(msg)

    try:
        try:
            failing_call()
        except RuntimeError as error:
            msg = f"while pairing with {SECRET}"
            raise ConnectionError(msg) from error
    except ConnectionError:
        logger.exception("delivery failed for %s", SECRET, stack_info=True)

    output = stream.getvalue()
    assert "Traceback (most recent call last)" in output
    assert "RuntimeError: television refused token [REDACTED]" in output
    assert "ConnectionError: while pairing with [REDACTED]" in output
    assert "Stack (most recent call last)" in output
    assert "delivery failed for [REDACTED]" in output
    assert SECRET not in output


def test_a_formatting_error_never_prints_the_record(capsys: pytest.CaptureFixture[str]) -> None:
    _, stream = _configure()
    handler = _installed(logging.getLogger())[0]
    record = logging.makeLogRecord(
        {
            "name": "frame_gallery",
            "levelname": "INFO",
            "levelno": logging.INFO,
            "msg": "count %d",
            "args": (f"not a number {SECRET}",),
        }
    )
    handler.handle(record)
    captured = capsys.readouterr()
    assert "a record from frame_gallery was dropped" in captured.err
    assert SECRET not in captured.err
    assert SECRET not in captured.out
    assert SECRET not in stream.getvalue()


def test_a_failing_stderr_is_tolerated(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenStream(io.StringIO):
        def write(self, text: str) -> int:
            msg = "closed"
            raise OSError(msg)

    _configure()
    handler = _installed(logging.getLogger())[0]
    monkeypatch.setattr(sys, "stderr", BrokenStream())
    record = logging.makeLogRecord({"name": "frame_gallery", "msg": "%d", "args": ("x",)})
    handler.handle(record)


@pytest.mark.parametrize(
    ("argument", "credential", "visible"),
    [
        (
            "[('Authorization', 'Basic dXNlcjpwYXNz'), ('Host', 'tv')]",
            "dXNlcjpwYXNz",
            "('Authorization', 'Basic ",
        ),
        ("[('X-Api-Key', 'k3yv4lue99')]", "k3yv4lue99", "('X-Api-Key', '"),
        ("(('token', 'tv-t0ken-777'),)", "tv-t0ken-777", "(('token', '"),
        (
            '{"event": "ms.channel.connect", "data": "{\\"token\\": \\"87654321\\"}"}',
            "87654321",
            '\\"token\\": \\"',
        ),
        ('{"accessToken": "s3cr3tV4lue"}', "s3cr3tV4lue", '"accessToken": "'),
        ('"clientSecret":"s3cr3tV4lue"', "s3cr3tV4lue", '"clientSecret":"'),
        ("refreshToken=s3cr3tV4lue", "s3cr3tV4lue", "refreshToken="),
        ("next=%2Fcb%3Ftoken%3Ds3cr3tV4lue", "s3cr3tV4lue", "%3Ftoken%3D"),
    ],
)
def test_credential_patterns_reach_the_log_redacted_h3(
    argument: str, credential: str, visible: str
) -> None:
    logger, stream = _configure(LogLevel.DEBUG)
    logger.debug("television reply: %s", argument)
    logger.info("the source failed: %s", sanitize_for_log(argument))
    output = stream.getvalue()
    assert credential not in output
    assert output.count(REDACTED) == 2
    assert output.count(visible) == 2


def test_a_digest_after_bearer_text_is_logged_whole() -> None:
    logger, stream = _configure()
    digest = "5f1c2e9a7b3d4c6e8f0a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e4f5a6"
    logger.info("chosen: %s (%s) %s sha256=%s", "aic:1", "strict", "The Standard Bearer", digest)
    assert stream.getvalue().endswith(
        f"chosen: aic:1 (strict) The Standard Bearer sha256={digest}\n"
    )
