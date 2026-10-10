"""The complete native colour card and documented helper key stay usable."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest
from scripts.app_config import schema, translations

from frame_gallery.config.filters import FilterField
from frame_gallery.config.vocabulary import BUILTIN_VOCABULARY

LABELS: Final = {
    "en": ("Colour wish (Commons only)", "Load new artwork", "Updating artwork…"),
    "de": ("Farbwunsch (nur Commons)", "Neues Kunstwerk laden", "Kunstwerk wird geladen …"),
    "fr": (
        "Couleur souhaitée (Commons uniquement)",
        "Afficher une nouvelle œuvre",
        "Chargement de l\u2019œuvre…",
    ),
    "es": ("Color deseado (solo Commons)", "Mostrar una nueva obra", "Cargando la obra…"),
    "it": ("Colore desiderato (solo Commons)", "Mostra una nuova opera", "Caricamento dell'opera…"),
}

SCRIPT_DESCRIPTIONS: Final = {
    "de": "Startet die Frame-Gallery-App und zeigt währenddessen einen Ladehinweis im Dashboard.",
    "fr": "Démarre Frame Gallery et affiche une indication de chargement sur le tableau de bord.",
    "es": "Inicia Frame Gallery y muestra una indicación de carga en el panel.",
    "it": "Avvia Frame Gallery e mostra un messaggio di caricamento nella dashboard.",
}


def _suffix(language: str) -> str:
    return "" if language == "en" else f".{language}"


def _english_labels(text: str, language: str) -> str:
    for local, english in zip(LABELS[language], LABELS["en"], strict=True):
        text = text.replace(local, english)
    return text


@pytest.mark.parametrize("language", list(LABELS))
def test_colour_guide_matches_complete_native_example(language: str) -> None:
    root = Path(__file__).resolve().parents[3]
    suffix = _suffix(language)
    guide_name = f"COMMONS_COLOUR{suffix}.md"
    guide = (root / guide_name).read_text()
    assert f"!{guide_name}" in (root / ".dockerignore").read_text().splitlines()
    blocks = re.findall(r"```yaml\n(.*?)\n```", guide, re.DOTALL)
    assert len(blocks) == 1
    example = (root / f"examples/commons-colour-card{suffix}.yaml").read_text()
    assert blocks[0] + "\n" == example
    assert example.startswith("type: vertical-stack\ncards:\n")
    assert "\t" not in example
    assert "type: entities" in example
    assert "entity: input_select.frame_gallery_colour" in example
    label = LABELS[language][0]
    assert f"name: {label}" in example
    basic_guide = (root / "DOCS.md").read_text()
    basic = re.findall(r"```yaml\n(.*?)\n```", basic_guide, re.DOTALL)[1]
    native_image_and_loading = basic[basic.index("  - type: picture-entity") :]
    assert _english_labels(example, language).endswith(native_image_and_loading + "\n")
    assert "`color_helper`" in guide
    assert "color_helper" in schema()
    assert "color_entity" not in guide


@pytest.mark.parametrize("language", list(LABELS))
def test_documented_dropdown_offers_every_runtime_colour_and_no_multicolour_value(
    language: str,
) -> None:
    root = Path(__file__).resolve().parents[3]
    suffix = _suffix(language)
    guide = (root / f"COMMONS_COLOUR{suffix}.md").read_text()
    options = ["any"] + [e.label for e in BUILTIN_VOCABULARY.entries_for(FilterField.COLOR)]
    assert len(options) == 13
    for option in options:
        assert f"`{option}`" in guide
    if language == "de":
        assert "nicht** von selbst einen Lauf" in guide
        assert "Mehrere Farben gleichzeitig" in guide
    elif language == "en":
        assert "not** automatically start a run" in guide
        assert "Selecting multiple colours at once is not offered" in guide
    elif language == "fr":
        assert "ne lance pas automatiquement" in guide
        assert "La sélection simultanée de plusieurs couleurs n\u2019est pas proposée" in guide
    elif language == "es":
        assert "no inicia automáticamente" in guide
        assert "No se ofrece la selección simultánea de varios colores" in guide
    else:
        assert "non avvia automaticamente" in guide
        assert "La selezione simultanea di più colori non è disponibile" in guide


@pytest.mark.parametrize("language", list(LABELS))
def test_colour_guides_have_reciprocal_language_links_and_identical_card_wiring(
    language: str,
) -> None:
    root = Path(__file__).resolve().parents[3]
    suffix = _suffix(language)
    guide = (root / f"COMMONS_COLOUR{suffix}.md").read_text()
    names = {"en": "English", "de": "Deutsch", "fr": "Français", "es": "Español", "it": "Italiano"}
    for other in LABELS:
        if language == other:
            assert f"**{names[other]}**" in guide
        else:
            assert f"[{names[other]}](COMMONS_COLOUR{_suffix(other)}.md)" in guide
    example = (root / f"examples/commons-colour-card{suffix}.yaml").read_text()
    en_example = (root / "examples/commons-colour-card.yaml").read_text()
    assert _english_labels(example, language) == en_example


@pytest.mark.parametrize("language", ["de", "fr", "es", "it"])
def test_localized_setup_keeps_complete_script_and_basic_card_wiring(language: str) -> None:
    root = Path(__file__).resolve().parents[3]
    name = f"SETUP.{language}.md"
    guide = (root / name).read_text()
    assert f"!{name}" in (root / ".dockerignore").read_text().splitlines()
    blocks = re.findall(r"```yaml\n(.*?)\n```", guide, re.DOTALL)
    basic = re.findall(r"```yaml\n(.*?)\n```", (root / "DOCS.md").read_text(), re.DOTALL)
    assert len(blocks) == 2
    english_description = (
        "Starts the Frame Gallery app and shows a note on the dashboard while it runs."
    )
    assert SCRIPT_DESCRIPTIONS[language] in blocks[0]
    assert blocks[0].replace(SCRIPT_DESCRIPTIONS[language], english_description) == basic[0]
    assert _english_labels(blocks[1], language) == basic[1]
    for value in (
        "/media/frame_gallery/preview/latest.jpg",
        "Frame Gallery Preview",
        "Frame Gallery run",
        "camera.frame_gallery_preview",
        "timer.frame_gallery_run",
        "script.frame_gallery_new_artwork",
        "a94fc569_frame_gallery",
        "`loading_timer`",
    ):
        assert value in " ".join(guide.split())
    fields = translations(language)["configuration"]
    assert isinstance(fields, dict)
    timer = fields["loading_timer"]
    assert isinstance(timer, dict)
    timer_name = timer["name"]
    assert isinstance(timer_name, str)
    assert timer_name in " ".join(guide.split())
    assert f"(COMMONS_COLOUR.{language}.md)" in guide
    assert "(DOCS.md#installation)" in guide
    for other in ("de", "fr", "es", "it"):
        if other != language:
            assert f"(SETUP.{other}.md)" in guide


def test_public_guide_language_links_resolve_to_files_in_app_context() -> None:
    root = Path(__file__).resolve().parents[3]
    for name in (
        "DOCS.md",
        "COMMONS_COLOUR.md",
        "COMMONS_COLOUR.de.md",
        "COMMONS_COLOUR.fr.md",
        "COMMONS_COLOUR.es.md",
        "COMMONS_COLOUR.it.md",
        "SETUP.de.md",
        "SETUP.fr.md",
        "SETUP.es.md",
        "SETUP.it.md",
        "COMMONS_ARTIST.md",
        "COMMONS_ARTIST.de.md",
        "COMMONS_ARTIST.fr.md",
        "COMMONS_ARTIST.es.md",
        "COMMONS_ARTIST.it.md",
        "ARTIST_CHOICES.md",
    ):
        guide = (root / name).read_text()
        for target in re.findall(r"\]\(([^)]+)\)", guide):
            if target.startswith(("https://", "#")):
                continue
            path = target.split("#", 1)[0]
            assert (root / path).is_file(), (name, target)
