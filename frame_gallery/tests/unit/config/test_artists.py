"""Commons-only artist vocabulary, compatibility and native-helper overrides."""

from __future__ import annotations

import re

import pytest

from frame_gallery.config.capabilities import resolve_effective_filters
from frame_gallery.config.filters import FilterDimension, FilterField, Provenance
from frame_gallery.config.options import ConfigError, Options, parse_options
from frame_gallery.config.overrides import apply_helper_values
from frame_gallery.config.vocabulary import BUILTIN_VOCABULARY, artist_key
from frame_gallery.domain import SourceKey
from frame_gallery.providers.commons_catalog import CATALOG

FIELD = FilterField.ARTIST
VOCAB = BUILTIN_VOCABULARY


def options(**raw: object) -> Options:
    return parse_options({"tv_host": "10.0.0.5", **raw}, vocabulary=VOCAB, excluded_networks=())


def test_every_catalogue_attribution_has_one_bounded_unambiguous_choice() -> None:
    entries = VOCAB.entries_for(FIELD)
    assert len(entries) == 557  # 560 labels; three punctuation/case duplicates.
    assert len({entry.key for entry in entries}) == len(entries)
    assert [entry.label.casefold() for entry in entries] == sorted(
        entry.label.casefold() for entry in entries
    )
    for work in CATALOG:
        key = artist_key(work.artist)
        assert len(key) <= 64
        assert re.fullmatch(r"artist_[a-z0-9_]+", key)
        entry = VOCAB.entry(key)
        assert entry is not None
        assert entry.dimension is FilterDimension.ARTIST
        assert len(entry.label) <= 100
        assert VOCAB.lookup(FIELD, entry.label).key == key
        assert VOCAB.lookup(FIELD, entry.key).key == key
    assert artist_key("Jean-Baptiste-Camille Corot") == artist_key("Jean-Baptiste Camille Corot")
    assert artist_key("Antoine GUILLEMET") == artist_key("Antoine Guillemet")
    assert artist_key("Anonymous") == artist_key("anonymous")
    # A case-fold tie must not choose a different display label with each
    # process's hash seed; documentation and runtime offer identical labels.
    anonymous = VOCAB.entry(artist_key("anonymous"))
    assert anonymous is not None
    assert anonymous.label == "Anonymous"
    guillemet = VOCAB.entry(artist_key("Antoine Guillemet"))
    assert guillemet is not None
    assert guillemet.label == "Antoine GUILLEMET"
    assert artist_key("Eugène Boudin") != artist_key("Eugène Louis Boudin")
    unspecified = VOCAB.entry(artist_key(""))
    assert unspecified is not None
    assert unspecified.label == "Unspecified artist"


@pytest.mark.parametrize(
    "value",
    [None, "", "any", "All artists", "Alle Künstler", "Tous les artistes", "Todos los artistas"],
)
def test_absent_optional_artist_is_backward_compatible(value: object) -> None:
    assert options(artist=value) == options()


@pytest.mark.parametrize(
    "name",
    ["Wassily Kandinsky", "  WASSILY KANDINSKY  ", "wassily_kandinsky", "artist_wassily_kandinsky"],
)
def test_names_keys_and_normalization_select_only_offered_artist(name: str) -> None:
    assert options(artist=name).filters.artist.key == "artist_wassily_kandinsky"


@pytest.mark.parametrize(
    "value",
    [
        42,
        True,
        [],
        "Kandinsky",
        "Monet or Klee",
        "not-an-artist",
        "All artists\n<script>",
        "x" * 256,
    ],
)
def test_invalid_or_partial_names_cannot_silently_match(value: object) -> None:
    with pytest.raises(ConfigError, match="artist"):
        options(artist=value)


@pytest.mark.parametrize("source", list(SourceKey))
def test_capabilities_apply_artist_and_colour_only_to_commons(source: SourceKey) -> None:
    configured = options(source=source.value, artist="Wassily Kandinsky", color="Blue")
    effective = resolve_effective_filters(configured.filters, VOCAB)
    if source is SourceKey.WIKIMEDIA_COMMONS:
        assert effective.artist == "artist_wassily_kandinsky"
        assert effective.color == "color_blue"
        assert effective.active()[FilterDimension.ARTIST] == effective.artist
        assert effective.ignored == ()
    else:
        assert effective.artist is None
        assert effective.color is None
        assert {item.field for item in effective.ignored} == {FIELD, FilterField.COLOR}
        assert all(item.reason.value == "unsupported_by_source" for item in effective.ignored)


@pytest.mark.parametrize("value", [None, "unknown", "unavailable", "Kandinsky", "not-known"])
def test_unusable_helper_warns_and_falls_back_without_echoing_value(value: str | None) -> None:
    static = options(artist="Wassily Kandinsky").filters
    merged = apply_helper_values(static, {FIELD: value}, VOCAB)
    assert merged.filters == static
    assert len(merged.warnings) == 1
    assert merged.warnings[0].startswith("artist_helper ")
    if value in {"Kandinsky", "not-known"}:
        assert value not in merged.warnings[0]


@pytest.mark.parametrize("value", ["Claude Monet", "All artists"])
def test_valid_helper_overrides_static_and_records_provenance(value: str) -> None:
    configured = options(
        artist="Wassily Kandinsky", artist_helper="input_select.frame_gallery_artist"
    )
    assert configured.helper_for(FIELD) == "input_select.frame_gallery_artist"
    merged = apply_helper_values(configured.filters, {FIELD: value}, VOCAB)
    assert merged.warnings == ()
    assert merged.filters.artist.provenance is Provenance.HELPER
    assert merged.filters.artist.key == ("artist_claude_monet" if value == "Claude Monet" else None)


def test_artist_helper_cannot_share_caption_helper() -> None:
    with pytest.raises(ConfigError, match="dedicated"):
        options(artist_helper="input_text.shared", artwork_info_helper="input_text.shared")
