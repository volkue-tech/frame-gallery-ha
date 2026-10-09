"""The app's metadata for the Supervisor: config.yaml and translations/en.yaml
(scripts/app_config.py; ARCHITECTURE.md §15.1, §17.1, §17.4; B1, B5, B8, D-123,
D-129)."""

from __future__ import annotations

import importlib.util
import re
import sys
from ipaddress import IPv4Network
from pathlib import Path
from types import ModuleType
from typing import Any, Final

import pytest

from frame_gallery import __version__
from frame_gallery.config.filters import FilterField
from frame_gallery.config.options import (
    ARTWORK_INFO_ENTITY_ID,
    HELPER_ENTITY_ID,
    HELPER_OPTION_NAMES,
    ConfigError,
    parse_options,
)
from frame_gallery.config.vocabulary import BUILTIN_VOCABULARY
from frame_gallery.domain import DEFAULT_SOURCE, SourceKey

PROJECT: Final = Path(__file__).resolve().parents[3]
CONTAINER: Final = (IPv4Network("172.30.32.0/23"),)


def _script() -> ModuleType:
    path = PROJECT / "scripts" / "app_config.py"
    spec = importlib.util.spec_from_file_location("app_config", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


SCRIPT: Final = _script()
CONFIG: Final[dict[str, Any]] = SCRIPT.config()
SCHEMA: Final[dict[str, str]] = CONFIG["schema"]
OPTIONS: Final[dict[str, object]] = CONFIG["options"]
TEXTS: Final[dict[str, dict[str, str]]] = SCRIPT.translations()["configuration"]


def _choices(rule: str) -> list[str]:
    match = re.fullmatch(r"list\(([^)]*)\)\??", rule)
    assert match is not None, rule
    return match.group(1).split("|")


def _pattern(rule: str) -> re.Pattern[str]:
    match = re.fullmatch(r"match\((.*)\)\??", rule)
    assert match is not None, rule
    return re.compile(match.group(1))


def _parse(**options: object) -> object:
    return parse_options(
        {"tv_host": "10.0.0.5", **options},
        vocabulary=BUILTIN_VOCABULARY,
        excluded_networks=CONTAINER,
    )


def test_the_files_are_what_the_script_writes() -> None:
    assert (PROJECT / "config.yaml").read_text() == SCRIPT.render(CONFIG)
    assert (PROJECT / "translations" / "en.yaml").read_text() == SCRIPT.render(
        SCRIPT.translations()
    )
    assert (PROJECT / "translations" / "de.yaml").read_text() == SCRIPT.render(
        SCRIPT.translations("de")
    )


def test_basic_settings_are_short_and_optional_defaults_preserve_existing_behavior() -> None:
    assert list(OPTIONS) == ["source", "color", "landscape_only", "strict_tv_format", "fit_mode"]
    assert list(SCHEMA)[:6] == [
        "tv_host",
        "source",
        "color",
        "landscape_only",
        "strict_tv_format",
        "fit_mode",
    ]
    assert OPTIONS["color"] == "any"
    for option in ("department", "style", "background_color"):
        assert option not in OPTIONS
        assert SCHEMA[option].endswith("?")
    assert _parse(**OPTIONS) == _parse(
        **OPTIONS, department="any", style="any", background_color="#000000"
    )


def test_german_texts_cover_every_option_and_explain_commons_and_no_crop() -> None:
    texts = SCRIPT.translations("de")["configuration"]
    assert set(texts) == set(SCHEMA)
    assert "ohne API-Key" in texts["source"]["description"]
    assert "2,5 %" in texts["strict_tv_format"]["description"]
    assert "400" in texts["source"]["description"]
    assert "ohne Beschnitt" in texts["fit_mode"]["name"]
    assert "255" in texts["artwork_info_helper"]["description"]
    for text in texts.values():
        assert set(text) == {"name", "description"}
        assert text["name"]
        assert text["description"].endswith(".")
    with pytest.raises(ValueError, match="language"):
        SCRIPT.translations("not-a-language")


def test_store_metadata_keeps_samsung_near_the_start_of_both_search_fields() -> None:
    """Keep the keyword inside HA's current location-sensitive search window.

    This guards our metadata, not the live frontend or the Fuse implementation.
    """
    assert CONFIG["name"] == "Frame Gallery \u2013 Samsung Frame TV"
    assert CONFIG["description"] == ("Samsung Frame TV artwork from museums or your own images.")
    for field in ("name", "description"):
        assert CONFIG[field].lower().index("samsung") <= 20


def test_the_app_is_a_one_shot_without_extra_privileges() -> None:
    """§17.1, D-129, Q-16: what is set, and what is deliberately not set."""
    assert CONFIG["slug"] == "frame_gallery"
    assert CONFIG["version"] == __version__
    assert CONFIG["arch"] == ["aarch64", "amd64"]
    assert CONFIG["url"] == "https://github.com/volkue-tech/frame-gallery-ha"
    assert (CONFIG["startup"], CONFIG["boot"], CONFIG["init"]) == ("once", "manual_only", False)
    assert CONFIG["stage"] == "experimental"
    assert CONFIG["homeassistant"] == "2026.2.0"
    assert CONFIG["homeassistant_api"] is True
    assert CONFIG["tmpfs"] is True
    assert CONFIG["timeout"] == 20
    assert CONFIG["map"] == [{"type": "media", "read_only": False}]
    assert CONFIG["backup_exclude"] == ["cache/**", "state/quarantine/**", "tv/**"]
    for absent in (
        "host_network",
        "privileged",
        "full_access",
        "docker_api",
        "hassio_api",
        "hassio_role",
        "ingress",
        "ports",
        "devices",
        "stdin",
        "watchdog",
        "apparmor",
    ):
        assert absent not in CONFIG


def test_the_public_image_mapping_selects_only_the_verified_own_architectures() -> None:
    assert CONFIG["version"] == __version__
    assert re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+b[1-9][0-9]*", CONFIG["version"])
    assert CONFIG["image"] == "ghcr.io/volkue-tech/frame-gallery-ha-{arch}"
    assert [CONFIG["image"].format(arch=arch) for arch in CONFIG["arch"]] == [
        "ghcr.io/volkue-tech/frame-gallery-ha-aarch64",
        "ghcr.io/volkue-tech/frame-gallery-ha-amd64",
    ]


def test_every_option_has_a_schema_and_a_text() -> None:
    assert set(OPTIONS) <= set(SCHEMA)
    assert set(TEXTS) == set(SCHEMA)
    for text in TEXTS.values():
        assert set(text) == {"name", "description"}
        assert text["name"]
        assert text["description"].endswith(".")


def test_the_tv_address_is_required_without_a_default() -> None:
    """B1: the Supervisor refuses to start the app until it is entered."""
    assert "tv_host" not in OPTIONS
    assert not SCHEMA["tv_host"].endswith("?")
    pattern = _pattern(SCHEMA["tv_host"])
    assert pattern.fullmatch("192.168.1.20")
    assert not pattern.fullmatch("tv.local")
    assert not pattern.fullmatch("fd00::1")


def test_the_defaults_are_the_accepted_ones() -> None:
    """D-123/D-210: no-crop/shape defaults unchanged; Commons is the new source default."""
    options = _parse(**OPTIONS)
    assert OPTIONS["source"] == DEFAULT_SOURCE.value == "wikimedia_commons"
    assert options.filters.source is SourceKey.WIKIMEDIA_COMMONS  # type: ignore[attr-defined]
    assert options == _parse()
    assert options.landscape_only is True  # type: ignore[attr-defined]
    assert options.strict_tv_format is True  # type: ignore[attr-defined]
    assert options.fit_mode.value == "contain"  # type: ignore[attr-defined]


def test_commons_is_first_without_removing_or_renaming_existing_choices() -> None:
    assert _choices(SCHEMA["source"]) == [
        "wikimedia_commons",
        "art_institute_chicago",
        "cleveland_museum_of_art",
        "local_media",
    ]


@pytest.mark.parametrize(
    ("option", "field"),
    [
        ("department", FilterField.DEPARTMENT),
        ("style", FilterField.STYLE),
        ("color", FilterField.COLOR),
    ],
)
def test_the_filter_choices_are_the_vocabulary(option: str, field: FilterField) -> None:
    choices = _choices(SCHEMA[option])
    entries = BUILTIN_VOCABULARY.entries_for(field)
    assert choices == [
        "any",
        *(entry.label if field is FilterField.COLOR else entry.key for entry in entries),
    ]
    for choice in choices:
        _parse(**{option: choice})


def test_the_colour_offers_one_family_and_preserves_the_unfiltered_default() -> None:
    """D-213: one simple colour field; existing missing/null values remain any."""
    assert _choices(SCHEMA["color"]) == [
        "any",
        "Red",
        "Orange",
        "Yellow",
        "Green",
        "Blue",
        "Purple",
        "Pink",
        "Brown",
        "Beige",
        "Gray",
        "Black",
        "White",
    ]
    assert _parse(color=None) == _parse(color="any") == _parse()
    assert _parse(color="Blue") == _parse(color="Blau") == _parse(color="color_blue")


def test_every_listed_choice_is_accepted_by_the_app() -> None:
    for option in ("source", "fit_mode", "log_level"):
        for choice in _choices(SCHEMA[option]):
            _parse(**{option: choice})
    assert sorted(_choices(SCHEMA["source"])) == sorted(key.value for key in SourceKey)


def test_the_helper_pattern_is_the_apps() -> None:
    rule = SCHEMA["source_helper"]
    assert all(SCHEMA[name] == rule for name in HELPER_OPTION_NAMES)
    assert rule.endswith("?")  # optional, with no default (§15.1)
    pattern = _pattern(rule)
    examples = [
        "input_select.frame_gallery",
        "select.x",
        "input_text.a_b_1",
        "input_number.x",
        "input_select.Frame",
        "input_select.",
        "input_select." + "a" * 65,
        "sensor.x",
    ]
    for example in examples:
        assert bool(pattern.fullmatch(example)) == bool(HELPER_ENTITY_ID.fullmatch(example))
    for name in HELPER_OPTION_NAMES:
        assert name not in OPTIONS


def test_artwork_information_is_optional_and_targets_only_text_helpers() -> None:
    assert "artwork_info_helper" not in OPTIONS
    rule = SCHEMA["artwork_info_helper"]
    assert rule.endswith("?")
    pattern = _pattern(rule)
    for example in (
        "input_text.frame_gallery_artwork",
        "sensor.x",
        "input_text.X",
        "input_text.x\n",
    ):
        assert bool(pattern.fullmatch(example)) == bool(ARTWORK_INFO_ENTITY_ID.fullmatch(example))
    assert "255" in TEXTS["artwork_info_helper"]["description"]


def test_the_margin_colour_pattern_is_the_apps() -> None:
    pattern = _pattern(SCHEMA["background_color"])
    for value in ("#000000", "#FfA0b1", "000000", "#00000", "#GG0000"):
        try:
            _parse(background_color=value)
        except ConfigError:
            accepted = False
        else:
            accepted = True
        assert bool(pattern.fullmatch(value)) == accepted, value


def test_the_filter_texts_name_the_sources_they_apply_to() -> None:
    """B8: the option descriptions state the capability matrix."""
    department = TEXTS["department"]["description"]
    assert "Cleveland" in TEXTS["department"]["name"]
    assert "Art Institute of Chicago and your own images do not support" in department
    assert "both museums" in TEXTS["style"]["name"]
    assert "not to your own images" in TEXTS["style"]["description"]
    colour = TEXTS["color"]["description"]
    assert "For Commons" in colour
    assert "Other sources do not apply" in colour
    assert "another colour is never used as a fallback" in colour


def test_the_texts_never_name_the_users_tv_address() -> None:
    text = (PROJECT / "translations" / "en.yaml").read_text()
    assert "192.168.1.20" in text  # the documented example
    assert ("192.168.178" + ".30") not in text


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("plain_word", "plain_word"),
        ("yes", "'yes'"),
        ("Off", "'Off'"),
        ("#000000", "'#000000'"),
        ("it's", "'it''s'"),
        ("a: b", "'a: b'"),
        ("2026.2.0", "'2026.2.0'"),
        (True, "true"),
        (False, "false"),
        (20, "20"),
    ],
)
def test_scalars_are_quoted_when_yaml_would_read_them_otherwise(
    value: str | int, expected: str
) -> None:
    assert SCRIPT._scalar(value) == expected


def test_the_emitter_writes_nested_lists_and_mappings() -> None:
    document = {"map": [{"type": "media", "read_only": False}], "arch": ["a", "b"], "n": {"x": 1}}
    assert SCRIPT.render(document).splitlines()[1:] == [
        "map:",
        "  - type: media",
        "    read_only: false",
        "arch:",
        "  - a",
        "  - b",
        "n:",
        "  x: 1",
    ]


def test_a_list_inside_a_list_is_refused() -> None:
    with pytest.raises(TypeError, match="list inside a list"):
        SCRIPT.render({"x": [["nested"]]})


def test_the_check_mode_reports_and_the_write_mode_repairs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(SCRIPT, "CONFIG", tmp_path / "config.yaml")
    monkeypatch.setattr(SCRIPT, "TRANSLATIONS", tmp_path / "translations" / "en.yaml")
    monkeypatch.setattr(SCRIPT, "GERMAN_TRANSLATIONS", tmp_path / "translations" / "de.yaml")
    monkeypatch.setattr(SCRIPT, "PROJECT", tmp_path)
    assert SCRIPT.main(["--check"]) == 1
    assert SCRIPT.main([]) == 0
    assert SCRIPT.main(["--check"]) == 0
    (tmp_path / "config.yaml").write_text("name: stale\n")
    assert SCRIPT.main(["--check"]) == 1
