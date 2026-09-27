"""Option parsing (§15.1, D-123)."""

from __future__ import annotations

from collections.abc import Mapping
from ipaddress import IPv4Address, IPv4Network
from types import MappingProxyType

import pytest

from frame_gallery.config.filters import ANY, FilterChoice, FilterField, FilterSet, Provenance
from frame_gallery.config.options import (
    ConfigError,
    ConfigIssue,
    LogLevel,
    Options,
    parse_options,
)
from frame_gallery.config.vocabulary import BUILTIN_VOCABULARY
from frame_gallery.domain import BLACK, FitMode, Rgb, SourceKey
from tests.unit.config.synthetic import (
    AIC_DEPARTMENT,
    CMA_DEPARTMENT,
    COLOR,
    OTHER_STYLE,
    PERIOD,
    STYLE,
    VOCABULARY,
)

TV = "192.168.1.20"
CONTAINER = (IPv4Network("172.30.32.0/23"),)


def _parse(**overrides: object) -> Options:
    raw: dict[str, object] = {"tv_host": TV, **overrides}
    return parse_options(raw, vocabulary=VOCABULARY, excluded_networks=CONTAINER)


def _issues(raw: Mapping[str, object]) -> tuple[ConfigIssue, ...]:
    with pytest.raises(ConfigError) as caught:
        parse_options(raw, vocabulary=VOCABULARY, excluded_networks=CONTAINER)
    return caught.value.issues


def _issue(**overrides: object) -> ConfigIssue:
    issues = _issues({"tv_host": TV, **overrides})
    assert len(issues) == 1
    return issues[0]


# -- the whole object -------------------------------------------------------------------------


def test_minimal_options_take_the_accepted_defaults() -> None:
    options = _parse()
    assert options == Options(
        tv_host=IPv4Address(TV), filters=FilterSet(SourceKey.ART_INSTITUTE_CHICAGO)
    )
    assert options.landscape_only is True
    assert options.strict_tv_format is True
    assert options.fit_mode is FitMode.CONTAIN
    assert options.background == BLACK
    assert options.helpers == ()
    assert options.log_level is LogLevel.INFO
    assert options.filters.source is SourceKey.ART_INSTITUTE_CHICAGO
    assert options.filters.source_provenance is Provenance.STATIC
    assert (options.filters.department, options.filters.style, options.filters.color) == (
        ANY,
        ANY,
        ANY,
    )


def test_null_optional_values_take_their_defaults() -> None:
    names = (
        "source",
        "department",
        "style",
        "color",
        "landscape_only",
        "strict_tv_format",
        "fit_mode",
        "background_color",
        "source_helper",
        "department_helper",
        "style_helper",
        "color_helper",
        "log_level",
    )
    assert _parse(**dict.fromkeys(names)) == _parse()


def test_a_full_valid_object() -> None:
    options = _parse(
        source="cleveland_museum_of_art",
        department=CMA_DEPARTMENT,
        style=PERIOD,
        color=COLOR,
        landscape_only=False,
        strict_tv_format=False,
        fit_mode="cover",
        background_color="#1a2B3c",
        source_helper="input_select.frame_source",
        department_helper="select.frame_department",
        style_helper="input_text.frame_style",
        color_helper="input_select.frame_color",
        log_level="debug",
    )
    assert options.tv_host == IPv4Address(TV)
    assert options.filters == FilterSet(
        source=SourceKey.CLEVELAND_MUSEUM_OF_ART,
        department=FilterChoice(CMA_DEPARTMENT, Provenance.STATIC),
        style=FilterChoice(PERIOD, Provenance.STATIC),
        color=FilterChoice(COLOR, Provenance.STATIC),
    )
    assert options.landscape_only is False
    assert options.strict_tv_format is False
    assert options.fit_mode is FitMode.COVER
    assert options.background == Rgb(0x1A, 0x2B, 0x3C)
    assert options.helpers == (
        (FilterField.SOURCE, "input_select.frame_source"),
        (FilterField.DEPARTMENT, "select.frame_department"),
        (FilterField.STYLE, "input_text.frame_style"),
        (FilterField.COLOR, "input_select.frame_color"),
    )
    assert options.log_level is LogLevel.DEBUG


def test_unknown_keys_are_ignored() -> None:
    assert _parse(time_limit=30, library_path="/share/art", extra={"a": 1}) == _parse()


def test_any_mapping_is_accepted() -> None:
    raw = MappingProxyType({"tv_host": TV, "fit_mode": "cover"})
    options = parse_options(raw, vocabulary=VOCABULARY, excluded_networks=())
    assert options.fit_mode is FitMode.COVER


@pytest.mark.parametrize("raw", [None, [], ["tv_host", TV], "tv_host", 3, (("tv_host", TV),)])
def test_a_non_mapping_is_rejected(raw: object) -> None:
    issues = _issues(raw)  # type: ignore[arg-type]
    assert issues == (
        ConfigIssue("options", "The options must be an object of option names and values."),
    )


def test_every_issue_is_collected_in_option_order() -> None:
    raw = {
        "tv_host": "tv.example",
        "source": "moma",
        "department": "aic_missing",
        "style": 7,
        "color": "no such colour",
        "landscape_only": "true",
        "strict_tv_format": 1,
        "fit_mode": "stretch",
        "background_color": "black",
        "source_helper": "sensor.frame",
        "department_helper": "input_select.ok_one",
        "style_helper": "Input_Select.frame",
        "color_helper": 5,
        "log_level": "verbose",
    }
    issues = _issues(raw)
    assert [issue.option for issue in issues] == [
        "tv_host",
        "source",
        "department",
        "style",
        "color",
        "landscape_only",
        "strict_tv_format",
        "fit_mode",
        "background_color",
        "source_helper",
        "style_helper",
        "color_helper",
        "log_level",
    ]
    error = ConfigError(issues)
    assert str(error).startswith("tv_host: The television IP address must be an IPv4 address")
    assert "; source: The source must be one of" in str(error)


def test_config_error_without_issues_has_a_summary() -> None:
    assert str(ConfigError([])) == "invalid options"


# -- tv_host ----------------------------------------------------------------------------------


@pytest.mark.parametrize("raw", [{}, {"tv_host": None}, {"tv_host": ""}, {"tv_host": "  "}])
def test_missing_tv_host_is_reported(raw: dict[str, object]) -> None:
    issues = _issues(raw)
    assert len(issues) == 1
    assert issues[0].option == "tv_host"
    assert issues[0].message.startswith("The television IP address is required.")


@pytest.mark.parametrize(
    ("value", "phrase"),
    [
        (19216812, "must be text"),
        ("192.168.1.020", "must be an IPv4 address"),
        ("169.254.1.1", "link-local"),
        ("8.8.8.8", "private (RFC 1918)"),
        ("172.30.32.9", "container network"),
    ],
)
def test_invalid_tv_host_is_reported(value: object, phrase: str) -> None:
    issue = _issue(tv_host=value)
    assert issue.option == "tv_host"
    assert phrase in issue.message


def test_tv_host_outside_the_excluded_networks_is_accepted() -> None:
    assert _parse(tv_host="172.30.40.9").tv_host == IPv4Address("172.30.40.9")


# -- source -----------------------------------------------------------------------------------


@pytest.mark.parametrize("source", list(SourceKey))
def test_each_source_key_is_accepted(source: SourceKey) -> None:
    options = _parse(source=source.value)
    assert options.filters.source is source
    assert options.filters.source_provenance is Provenance.STATIC


@pytest.mark.parametrize(
    "value",
    ["Art Institute Chicago", "ART_INSTITUTE_CHICAGO", " local_media", "aic", "any", "", 3, True],
)
def test_static_source_is_exact(value: object) -> None:
    issue = _issue(source=value)
    assert issue.option == "source"
    assert "art_institute_chicago, cleveland_museum_of_art, or local_media" in issue.message


# -- department, style, color -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("option", "value", "key"),
    [
        ("department", AIC_DEPARTMENT, AIC_DEPARTMENT),
        ("department", CMA_DEPARTMENT, CMA_DEPARTMENT),
        ("department", "Test Paintings", AIC_DEPARTMENT),
        ("style", STYLE, STYLE),
        ("style", "second test style", OTHER_STYLE),
        ("style", PERIOD, PERIOD),
        ("color", COLOR, COLOR),
        ("color", "TEST AZURE", COLOR),
    ],
)
def test_static_filter_values_are_normalized(option: str, value: str, key: str) -> None:
    options = _parse(**{option: value})
    assert options.filters.choice(FilterField(option)) == FilterChoice(key, Provenance.STATIC)


@pytest.mark.parametrize("option", ["department", "style", "color"])
@pytest.mark.parametrize("value", ["any", "ANY", "all", "random", "none", "", " "])
def test_static_no_filter_values(option: str, value: str) -> None:
    assert _parse(**{option: value}).filters.choice(FilterField(option)) == ANY


@pytest.mark.parametrize(
    ("option", "value", "noun"),
    [
        ("department", "aic_missing", "department or collection"),
        ("department", STYLE, "department or collection"),
        ("style", COLOR, "style or period"),
        ("style", AIC_DEPARTMENT, "style or period"),
        ("color", PERIOD, "colour"),
        ("color", "日本", "colour"),
    ],
)
def test_unknown_static_filter_values_are_reported(option: str, value: str, noun: str) -> None:
    issue = _issue(**{option: value})
    assert issue.option == option
    assert issue.message == (
        f"{value!r} is not a known {noun}. Choose any, or one of the values offered for "
        "this option."
    )


@pytest.mark.parametrize("option", ["department", "style", "color"])
@pytest.mark.parametrize("value", [3, True, ["aic_test_paintings"], {"key": "x"}])
def test_non_text_static_filter_values_are_reported(option: str, value: object) -> None:
    issue = _issue(**{option: value})
    assert issue.option == option
    assert "must be text" in issue.message
    assert "aic_test_paintings" not in issue.message


def test_long_values_are_never_echoed_in_full() -> None:
    value = "secret-looking-" + "x" * 500
    issue = _issue(department=value)
    assert value not in issue.message
    assert "x" * 40 not in issue.message
    assert repr(value[:39] + "…") in issue.message


def test_a_40_character_value_is_echoed_whole() -> None:
    value = "y" * 40
    assert repr(value) in _issue(color=value).message


def test_control_characters_are_escaped_in_messages() -> None:
    issue = _issue(style="bad\nline")
    assert "\n" not in issue.message
    assert "'bad\\nline'" in issue.message


def test_builtin_vocabulary_v1_accepts_only_offered_values() -> None:
    raw: dict[str, object] = {"tv_host": TV, "department": "any", "style": "", "color": None}
    options = parse_options(raw, vocabulary=BUILTIN_VOCABULARY, excluded_networks=())
    assert options.filters == FilterSet(SourceKey.ART_INSTITUTE_CHICAGO)
    with pytest.raises(ConfigError) as caught:
        parse_options(
            {"tv_host": TV, "department": AIC_DEPARTMENT},
            vocabulary=BUILTIN_VOCABULARY,
            excluded_networks=(),
        )
    assert [issue.option for issue in caught.value.issues] == ["department"]


# -- landscape_only, strict_tv_format ---------------------------------------------------------


@pytest.mark.parametrize("option", ["landscape_only", "strict_tv_format"])
@pytest.mark.parametrize("value", [True, False])
def test_flags_accept_booleans(option: str, value: bool) -> None:
    assert getattr(_parse(**{option: value}), option) is value


@pytest.mark.parametrize("option", ["landscape_only", "strict_tv_format"])
@pytest.mark.parametrize("value", ["true", "false", 1, 0, "", "yes", [True]])
def test_flags_reject_non_booleans(option: str, value: object) -> None:
    issue = _issue(**{option: value})
    assert issue == ConfigIssue(option, "This option must be true or false.")


# -- fit_mode ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "mode"), [("contain", FitMode.CONTAIN), ("cover", FitMode.COVER)]
)
def test_fit_modes(value: str, mode: FitMode) -> None:
    assert _parse(fit_mode=value).fit_mode is mode


@pytest.mark.parametrize("value", ["Contain", "COVER", " cover", "fill", "", 0, True])
def test_invalid_fit_mode(value: object) -> None:
    issue = _issue(fit_mode=value)
    assert issue.option == "fit_mode"
    assert "contain" in issue.message
    assert "cover" in issue.message


# -- background_color -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "colour"),
    [
        ("#000000", BLACK),
        ("#FFFFFF", Rgb(255, 255, 255)),
        ("#ffffff", Rgb(255, 255, 255)),
        ("#0a0B0c", Rgb(10, 11, 12)),
    ],
)
def test_background_colour(value: str, colour: Rgb) -> None:
    assert _parse(background_color=value).background == colour


@pytest.mark.parametrize(
    "value", ["000000", "#000", "#0000000", "#GGGGGG", "black", "", " #000000", 0, [0, 0, 0]]
)
def test_invalid_background_colour(value: object) -> None:
    issue = _issue(background_color=value)
    assert issue == ConfigIssue(
        "background_color", "The background colour must have the form #RRGGBB, such as #000000."
    )


# -- helpers ----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "entity_id",
    [
        "input_select.frame_gallery",
        "select.a",
        "input_text.x9_",
        "input_select." + "a" * 64,
        "select.0",
    ],
)
@pytest.mark.parametrize(
    ("option", "field"),
    [
        ("source_helper", FilterField.SOURCE),
        ("department_helper", FilterField.DEPARTMENT),
        ("style_helper", FilterField.STYLE),
        ("color_helper", FilterField.COLOR),
    ],
)
def test_valid_helper_entity_ids(option: str, field: FilterField, entity_id: str) -> None:
    options = _parse(**{option: entity_id})
    assert options.helpers == ((field, entity_id),)
    assert options.helper_for(field) == entity_id
    for other in FilterField:
        if other is not field:
            assert options.helper_for(other) is None


@pytest.mark.parametrize(
    "value",
    [
        "sensor.frame",
        "input_boolean.frame",
        "input_select.",
        "input_select.Frame",
        "input_select.frame-gallery",
        "input_select.frame gallery",
        "input_select.frame\n",
        " input_select.frame",
        "input_select." + "a" * 65,
        "input_select.fráme",
        "input_select.frame.extra",
        "http://supervisor/core/api/states/input_select.frame",
        "../input_select.frame",
        "input_select.frame%2F",
        " ",
        3,
        True,
        ["input_select.frame"],
    ],
)
def test_invalid_helper_entity_ids(value: object) -> None:
    issue = _issue(department_helper=value)
    assert issue.option == "department_helper"
    assert "input_select, select, or input_text" in issue.message


def test_empty_helpers_are_unset_and_order_is_field_order() -> None:
    options = _parse(
        color_helper="input_select.c",
        style_helper="",
        source_helper="input_select.s",
        department_helper=None,
    )
    assert options.helpers == (
        (FilterField.SOURCE, "input_select.s"),
        (FilterField.COLOR, "input_select.c"),
    )
    assert options.helper_for(FilterField.STYLE) is None


# -- log_level --------------------------------------------------------------------------------


@pytest.mark.parametrize(("value", "level"), [("info", LogLevel.INFO), ("debug", LogLevel.DEBUG)])
def test_log_levels(value: str, level: LogLevel) -> None:
    assert _parse(log_level=value).log_level is level


@pytest.mark.parametrize("value", ["DEBUG", "warning", "trace", "", 10, False])
def test_invalid_log_level(value: object) -> None:
    assert _issue(log_level=value) == ConfigIssue(
        "log_level", "The log level must be info or debug."
    )
