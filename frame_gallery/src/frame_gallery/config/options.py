"""App options and their validation (§15.1, D-123).

The options arrive from the Supervisor as a JSON object. They are untrusted:
the app re-validates every value, even those the Supervisor schema checks.
"""

from __future__ import annotations

import enum
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network
from typing import Final

from frame_gallery.config.filters import ANY, FilterChoice, FilterField, FilterSet, Provenance
from frame_gallery.config.tv_address import TvAddressError, validate_tv_host
from frame_gallery.config.vocabulary import LookupStatus, Vocabulary
from frame_gallery.domain import BLACK, DEFAULT_SOURCE, FitMode, Rgb, SourceKey
from frame_gallery.errors import FrameGalleryError


class LogLevel(enum.StrEnum):
    INFO = "info"
    DEBUG = "debug"


@dataclass(frozen=True, slots=True)
class ConfigIssue:
    """One validation problem, phrased for the user."""

    option: str
    message: str


class ConfigError(FrameGalleryError):
    """The options are invalid (outcome ``config_invalid``)."""

    def __init__(self, issues: Sequence[ConfigIssue]) -> None:
        self.issues = tuple(issues)
        summary = "; ".join(f"{issue.option}: {issue.message}" for issue in self.issues)
        super().__init__(summary or "invalid options")


@dataclass(frozen=True, slots=True)
class Options:
    """Validated options. The defaults are the accepted defaults (D-123)."""

    tv_host: IPv4Address
    filters: FilterSet
    landscape_only: bool = True
    strict_tv_format: bool = True
    fit_mode: FitMode = FitMode.CONTAIN
    background: Rgb = BLACK
    helpers: tuple[tuple[FilterField, str], ...] = ()
    """Configured helper entity IDs, in ``FilterField`` order, unset ones omitted."""

    log_level: LogLevel = LogLevel.INFO

    def helper_for(self, field: FilterField) -> str | None:
        for helper_field, entity_id in self.helpers:
            if helper_field is field:
                return entity_id
        return None


_ECHO_MAX_LENGTH: Final = 40
"""Echoed option values are cut to this many characters."""

_HELPER_ENTITY_ID: Final = re.compile(
    r"(?:input_select|select|input_text)\.[a-z0-9_]{1,64}", re.ASCII
)
_HELPER_OPTIONS: Final = tuple((field, f"{field.value}_helper") for field in FilterField)
"""``(field, option)`` in ``FilterField`` order: ``source_helper`` first."""

_FILTER_NOUNS: Final = {
    FilterField.DEPARTMENT: "department or collection",
    FilterField.STYLE: "style or period",
    FilterField.COLOR: "colour",
}

_SOURCES: Final = {key.value: key for key in SourceKey}
_FIT_MODES: Final = {mode.value: mode for mode in FitMode}
_LOG_LEVELS: Final = {level.value: level for level in LogLevel}

_NOT_A_MAPPING: Final = "The options must be an object of option names and values."
_SOURCE_CHOICES: Final = (
    "The source must be one of art_institute_chicago, cleveland_museum_of_art, or local_media."
)
_FIT_MODE_CHOICES: Final = (
    "The fit mode must be contain (shows the whole artwork) or cover (fills the screen and "
    "may crop)."
)
_BACKGROUND_FORMAT: Final = "The background colour must have the form #RRGGBB, such as #000000."
_HELPER_FORMAT: Final = (
    "The helper must be an entity ID of an input_select, select, or input_text helper, "
    "such as input_select.frame_gallery (lowercase letters, digits, and underscores)."
)
_LOG_LEVEL_CHOICES: Final = "The log level must be info or debug."
_FLAG_FORMAT: Final = "This option must be true or false."


def _quoted(value: str) -> str:
    """``value`` for a message: cut to 40 characters and quoted, never raw."""
    if len(value) > _ECHO_MAX_LENGTH:
        value = value[: _ECHO_MAX_LENGTH - 1] + "…"
    return repr(value)


def _tv_host(
    value: object, excluded_networks: Sequence[IPv4Network], issues: list[ConfigIssue]
) -> IPv4Address | None:
    try:
        return validate_tv_host(value, excluded_networks=excluded_networks)
    except TvAddressError as error:
        issues.append(ConfigIssue("tv_host", str(error)))
        return None


def _source(value: object, issues: list[ConfigIssue]) -> SourceKey:
    """The static source: one of the three keys exactly (no normalization)."""
    if value is None:
        return DEFAULT_SOURCE
    source = _SOURCES.get(value) if isinstance(value, str) else None
    if source is None:
        issues.append(ConfigIssue("source", _SOURCE_CHOICES))
        return DEFAULT_SOURCE
    return source


def _filter(
    field: FilterField, value: object, vocabulary: Vocabulary, issues: list[ConfigIssue]
) -> FilterChoice:
    """A static filter value, normalized like a helper value (§15.2)."""
    if value is None:
        return ANY
    noun = _FILTER_NOUNS[field]
    if not isinstance(value, str):
        issues.append(ConfigIssue(field.value, f"The {noun} must be text, such as any."))
        return ANY
    result = vocabulary.lookup(field, value)
    if result.status is LookupStatus.INVALID:
        message = (
            f"{_quoted(value)} is not a known {noun}. Choose any, or one of the values "
            "offered for this option."
        )
        issues.append(ConfigIssue(field.value, message))
        return ANY
    return FilterChoice(result.key, Provenance.STATIC)


def _flag(option: str, value: object, issues: list[ConfigIssue], *, default: bool) -> bool:
    """A real boolean: ``"true"`` and ``1`` are rejected."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    issues.append(ConfigIssue(option, _FLAG_FORMAT))
    return default


def _fit_mode(value: object, issues: list[ConfigIssue]) -> FitMode:
    if value is None:
        return FitMode.CONTAIN
    mode = _FIT_MODES.get(value) if isinstance(value, str) else None
    if mode is None:
        issues.append(ConfigIssue("fit_mode", _FIT_MODE_CHOICES))
        return FitMode.CONTAIN
    return mode


def _as_colour(value: object) -> Rgb | None:
    if not isinstance(value, str):
        return None
    try:
        return Rgb.from_hex(value)
    except ValueError:
        return None


def _background(value: object, issues: list[ConfigIssue]) -> Rgb:
    if value is None:
        return BLACK
    colour = _as_colour(value)
    if colour is None:
        issues.append(ConfigIssue("background_color", _BACKGROUND_FORMAT))
        return BLACK
    return colour


def _helpers(
    raw: Mapping[str, object], issues: list[ConfigIssue]
) -> tuple[tuple[FilterField, str], ...]:
    """The configured helpers; ``None`` and ``""`` mean unset."""
    helpers: list[tuple[FilterField, str]] = []
    for field, option in _HELPER_OPTIONS:
        value = raw.get(option)
        if value is None or value == "":
            continue
        if isinstance(value, str) and _HELPER_ENTITY_ID.fullmatch(value) is not None:
            helpers.append((field, value))
        else:
            issues.append(ConfigIssue(option, _HELPER_FORMAT))
    return tuple(helpers)


def _log_level(value: object, issues: list[ConfigIssue]) -> LogLevel:
    if value is None:
        return LogLevel.INFO
    level = _LOG_LEVELS.get(value) if isinstance(value, str) else None
    if level is None:
        issues.append(ConfigIssue("log_level", _LOG_LEVEL_CHOICES))
        return LogLevel.INFO
    return level


def parse_options(
    raw: Mapping[str, object],
    *,
    vocabulary: Vocabulary,
    excluded_networks: Sequence[IPv4Network],
) -> Options:
    """Validate the raw options object and return :class:`Options`.

    Raises :class:`ConfigError` listing every problem found. An absent or
    ``null`` optional value takes its default; unknown keys are ignored (the
    Supervisor schema governs the key set). Messages never echo more than 40
    characters of a value.
    """
    untrusted: object = raw
    if not isinstance(untrusted, Mapping):
        raise ConfigError([ConfigIssue("options", _NOT_A_MAPPING)])
    issues: list[ConfigIssue] = []
    tv_host = _tv_host(raw.get("tv_host"), excluded_networks, issues)
    source = _source(raw.get("source"), issues)
    department = _filter(FilterField.DEPARTMENT, raw.get("department"), vocabulary, issues)
    style = _filter(FilterField.STYLE, raw.get("style"), vocabulary, issues)
    color = _filter(FilterField.COLOR, raw.get("color"), vocabulary, issues)
    landscape_only = _flag("landscape_only", raw.get("landscape_only"), issues, default=True)
    strict_tv_format = _flag("strict_tv_format", raw.get("strict_tv_format"), issues, default=True)
    fit_mode = _fit_mode(raw.get("fit_mode"), issues)
    background = _background(raw.get("background_color"), issues)
    helpers = _helpers(raw, issues)
    log_level = _log_level(raw.get("log_level"), issues)
    if tv_host is None or issues:
        raise ConfigError(issues)
    return Options(
        tv_host=tv_host,
        filters=FilterSet(source=source, department=department, style=style, color=color),
        landscape_only=landscape_only,
        strict_tv_format=strict_tv_format,
        fit_mode=fit_mode,
        background=background,
        helpers=helpers,
        log_level=log_level,
    )
