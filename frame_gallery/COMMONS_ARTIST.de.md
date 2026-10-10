# Künstlerauswahl — ab Beta 0.1.0b7

[English](COMMONS_ARTIST.md) | **Deutsch** | [Français](COMMONS_ARTIST.fr.md) | [Español](COMMONS_ARTIST.es.md) | [Italiano](COMMONS_ARTIST.it.md)

Benötigt 0.1.0b7 oder neuer; unter 0.1.0b6 keine Künstleroptionen einrichten. Wähle optional einen Künstlerwunsch für Commons. Kein neuer Pflicht-Helfer und kein Kartenaustausch: Die Standardkarte bleibt nutzbar. Andere Quellen melden den Wunsch als nicht unterstützt.

Ohne Dashboard-Auswahl: Nicht verwendete optionale Optionen in Frame Gallery → Konfiguration einblenden. Bei **Künstlerwunsch (Commons, optional)** (`artist`) einen vollständigen angebotenen Namen aus der [Auswahlliste](ARTIST_CHOICES.md) eintragen, z. B. `Wassily Kandinsky`. Leer oder `All artists` bedeutet ohne Einschränkung. Speichern und die App wie gewohnt starten.

## Einrichtung

Für ein Dropdown: Einstellungen → Geräte & Dienste → Helfer → Helfer erstellen → Dropdown. Name: `Frame Gallery Artist`. `All artists` und nur deine bevorzugten Namen aus der Liste als einzelne Optionen hinzufügen. Unten steht eine Startauswahl. Künstlernamen und technische Werte nicht übersetzen.

```text
All artists
Wassily Kandinsky
Claude Monet
Vincent van Gogh
Pierre-Auguste Renoir
Winslow Homer
W.carter
```

Helfer öffnen → ⋮ → Details und die tatsächliche ID prüfen, normalerweise `input_select.frame_gallery_artist`. Bei bestehenden Namen kann ein Suffix entstehen. Diese ID bei **Künstler vom Dashboard (optional, Commons)** (`artist_helper`) eintragen, Commons als Quelle behalten und speichern. Zunächst `All artists` wählen. Nicht denselben Text-Helfer wie für die Werkinformation verwenden.

Das Dropdown hat Vorrang vor dem gespeicherten Künstlerwunsch. Nicht lesbare, nicht verfügbare oder ungültige Werte fallen mit Warnung auf den gespeicherten Wunsch zurück. Ändern startet keinen Lauf: erst wählen, dann auf das Werk tippen. Änderungen während eines Laufs gelten beim nächsten Start.

Künstler und Farbe müssen beide passen. Die Format-Ausweichregel darf 16:9 lockern, nie Künstler oder Farbe. Bereits gesendete/hochgeladene Werke bleiben ausgeschlossen. Die Liste zeigt Gesamtzahlen, nicht ungesendete Werke: Kandinsky und Monet haben derzeit je ein Werk. Nach dessen Nutzung kann die Auswahl ausgeschöpft sein. Ohne Treffer bleiben TV, Vorschau und Beschriftung erhalten; der Lauf endet sauber. Mit `All artists` oder `any` breiter wählen. Kein automatischer Verlaufsreset.

## Nur Künstler

Karte nur mit Künstler: Kamera, Timer und Script aus der [Einrichtung](SETUP.de.md) weiterverwenden. Nur das Künstler-Dropdown kommt dazu. Abweichende IDs überall ersetzen. YAML legt keine Helfer an. Kein HACS, SSH oder configuration.yaml nötig.

```yaml
type: vertical-stack
cards:
  - type: entities
    show_header_toggle: false
    entities:
      - entity: input_select.frame_gallery_artist
        name: Künstler (nur Commons)
  - type: picture-entity
    entity: camera.frame_gallery_preview
    name: Neues Kunstwerk laden
    show_state: false
    show_name: true
    camera_view: auto
    aspect_ratio: "16:9"
    tap_action:
      action: perform-action
      perform_action: script.turn_on
      target:
        entity_id: script.frame_gallery_new_artwork
    hold_action:
      action: more-info
  - type: conditional
    conditions:
      - condition: state
        entity: timer.frame_gallery_run
        state: active
    card:
      type: markdown
      content: Kunstwerk wird geladen …
```

## Künstler und Farbe

Karte mit Künstler und Farbe: Zusätzlich die [Farb-Helfer-Einrichtung](COMMONS_COLOUR.de.md) durchführen. `input_select.frame_gallery_colour` und `color_helper` bleiben erhalten. Dasselbe Script, dieselbe Kamera und derselbe Timer. Ein nativer Stapel, keine zusätzliche Dashboard-Erweiterung.

```yaml
type: vertical-stack
cards:
  - type: entities
    show_header_toggle: false
    entities:
      - entity: input_select.frame_gallery_artist
        name: Künstler (nur Commons)
      - entity: input_select.frame_gallery_colour
        name: Farbwunsch (nur Commons)
  - type: picture-entity
    entity: camera.frame_gallery_preview
    name: Neues Kunstwerk laden
    show_state: false
    show_name: true
    camera_view: auto
    aspect_ratio: "16:9"
    tap_action:
      action: perform-action
      perform_action: script.turn_on
      target:
        entity_id: script.frame_gallery_new_artwork
    hold_action:
      action: more-info
  - type: conditional
    conditions:
      - condition: state
        entity: timer.frame_gallery_run
        state: active
    card:
      type: markdown
      content: Kunstwerk wird geladen …
```

Die [optionale Werkinformationskarte](ARTWORK_INFO.md) bleibt separat und unverändert. Der Künstler des aktuellen Vorschaubilds ist nicht automatisch die nächste Auswahl. Die App installiert keine Karten, legt keine Helfer an und befüllt nicht automatisch die vollständige Liste.
