# Farbauswahl ab Beta 0.1.0b6

Diese Anleitung gilt ab **0.1.0b6** mit 1000 kuratierten Commons-Werken.
In Beta 0.1.0b5 und älteren Versionen ist der Farbfilter noch nicht verfügbar.
Für eine erste Einrichtung zuerst die [Standardanleitung](DOCS.md#dashboard)
befolgen. Die Farbauswahl auf dem Dashboard ist optional.

## Eine Farbe wünschen

1. In **Einstellungen → Apps → Frame Gallery → Konfiguration** gehen.
2. **Wikimedia Commons** als Bildquelle auswählen.
3. Direkt darunter bei **Farbwunsch (Commons)** eine Farbe wählen, beispielsweise
   **Blue** für Blau. **any** bedeutet alle Farben und bleibt der Standard.
4. Speichern. Das nächste über die App oder die bestehende Dashboardkarte
   gestartete Kunstwerk wird innerhalb dieser Auswahl gesucht.

Es ist kein API-Key, neuer Helfer, neues Script oder Austausch der Karte nötig.
Die vorhandene Vorschau und die optionale Künstler-/Titelanzeige bleiben nutzbar.
Ein neuer Katalog setzt den bisherigen Sendeverlauf nicht zurück.

## Was bedeutet „blau“?

Blau muss einen sichtbaren Anteil am Werk haben, aber nicht die größte Fläche
sein. Die Auswahl verwendet ungefähr fünf Prozent Bildfläche als Schwelle.
Ein blau-gelbes Werk kann daher sowohl bei Blau als auch bei Gelb erscheinen.
Ocker- und Goldtöne können unter Gelb fallen. Eine Farbe ist eine grobe Gruppe,
keine exakte Wandfarben- oder HEX-Übereinstimmung.

Angeboten werden Red, Orange, Yellow, Green, Blue, Purple, Pink, Brown, Beige,
Gray, Black und White. Die Analysedaten enthalten auch Flächenanteile und bis
zu drei wichtige unterschiedliche Farbgruppen. Die Oberfläche erlaubt in diesem
Update trotzdem bewusst nur **eine** Farbe. Farbkombinationen folgen nicht
automatisch mit diesem Update.

Die Analyse erfolgt bei der Vorbereitung auf dem Mac. Die App muss nicht erst
zahlreiche Bilder auf den Green laden, um deren Farben auszuprobieren. Schwarze
TV-Ränder aus der Bildanpassung werden nicht als Bildfarbe mitgemessen.

## Kein passendes neues Bild?

Der Lauf endet sauber. Das bisherige TV-Bild, die Vorschau und die Werkdaten
bleiben erhalten. Es wird nicht heimlich eine andere Farbe gewählt. Bereits
gesendete oder hochgeladene Werke bleiben ausgeschlossen; auch eine kleine
Farbauswahl kann irgendwann ausgeschöpft sein.

Du kannst eine andere Farbe oder **any** wählen. Das Protokoll unterscheidet
einen Lauf ohne Treffer von einem Quellenfehler. Wegen der festen Zeit- und
Anfragengrenzen bedeutet ein einzelner Lauf ohne Treffer nicht automatisch,
dass jedes Werk dieser Farbe dauerhaft ausgeschlossen ist.

Die vorhandene **16:9-Präferenz** kann auf ein passendes Querformat mit Rand
zurückfallen, aber nicht auf eine andere Farbe. **contain** bleibt die Empfehlung,
damit das vollständige Kunstwerk ohne Beschnitt erhalten bleibt.

## Andere Bildquellen und optionale Helfer

Die neue Farbauswahl gilt nur für Commons. Chicago, Cleveland und eigene Bilder
bekommen dadurch keinen Farbfilter; ein dort gesetzter Farbwunsch wird im
Protokoll als nicht angewendet ausgewiesen.

Die anderen Quellen bleiben verfügbar. Die unten dokumentierte Kartenvariante
ist bewusst für Commons eingerichtet und bietet keinen Quellenwechsel an.
Wenn du die Quelle in der App-Konfiguration wechselst, gilt der auf der Karte
ausgewählte Farbwunsch dort **nicht**. Deshalb steht direkt am Dropdown
**Farbwunsch (nur Commons)**. Ein späterer Quellenselektor auf dem Dashboard
müsste die unpassenden Filter abhängig von dieser Quellenauswahl ausblenden;
das zuletzt angezeigte Kunstwerk verrät nicht zuverlässig die nächste Quelle.

Ein optionaler Farb-Helfer kann dieselbe Auswahl vom Dashboard steuern.
Er ist für die normale Einrichtung nicht nötig. Die App versteht etwa **Blau**,
**Blue** und **color_blue** als denselben Wert. Mehrere Farben in einem Wert
werden nicht als Kombination interpretiert. Ohne Helfer genügt das einzelne
Farbfeld in der Konfiguration.

## Farbwähler direkt in der Dashboardkarte

**Optional und ab 0.1.0b6 nutzbar.** Ohne diesen Schritt
funktioniert die bisherige Standardkarte weiter. Kein HACS oder neues Script
ist nötig; der neue Dropdown-Helfer ist nur für die Auswahl auf dem Dashboard.

1. **Einstellungen → Geräte & Dienste → Helfer → Helfer erstellen → Dropdown**
   öffnen. Name: `Frame Gallery Colour`.
2. Diese Optionen einzeln und genau so hinzufügen, jeweils eine pro Option:
   `any`, `Red`, `Orange`, `Yellow`, `Green`, `Blue`, `Purple`, `Pink`, `Brown`,
   `Beige`, `Gray`, `Black`, `White`. `any` bedeutet alle Farben. Deutsche
   Farbnamen werden ebenfalls verstanden; die Beispiele verwenden durchgängig
   diese englischen Werte, damit keine Übersetzungsfrage die Einrichtung stört.
3. Speichern und die tatsächliche Entitäts-ID prüfen: Helfer öffnen → **⋮ →
   Details**. Erwartet: `input_select.frame_gallery_colour`. Eine vorhandene
   gleichnamige Entität kann eine andere ID erzeugen.
4. In **Frame Gallery → Konfiguration** bei **Farbe vom Dashboard (optional,
   Commons)** (`color_helper`) diese ID eintragen. Falls verborgen, **Nicht
   verwendete optionale Konfigurationsoptionen einblenden** aktivieren. Commons
   als Quelle behalten und speichern.
5. Den Helfer auf `any` stellen. In deiner Karte den ganzen folgenden Block
   verwenden; abweichende Kamera-, Timer-, Script- und Helfer-IDs überall ersetzen.

Der Farbwähler hat Vorrang vor dem Farbwunsch in der App-Konfiguration. Eine
Änderung startet **nicht** von selbst einen Lauf: erst Farbe wählen, dann auf
das Bild tippen. Eine Änderung während eines laufenden Ladevorgangs gilt erst
beim nächsten Start. Ein nicht lesbarer Helfer fällt auf die gespeicherte
App-Auswahl zurück und wird im Protokoll gemeldet. Mehrere Farben gleichzeitig
werden noch nicht angeboten.

### Vollständige Karte mit Vorschau und Farbwähler

Kamera, Timer und Script aus der bisherigen Standardanleitung werden wiederverwendet.
Der Helfer wird durch YAML **nicht** angelegt; vorher die fünf Schritte oben
erledigen. Alle Karten sind eingebaute Home-Assistant-Komponenten.

```yaml
type: vertical-stack
cards:
  - type: entities
    show_header_toggle: false
    entities:
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

Die optionale Künstler-/Titelkarte kann separat darunter bleiben. Ohne
zusätzliche Dashboard-Erweiterung ist das optisch eine Gruppe nativer Karten,
nicht eine speziell programmierte einzelne Karte.

**Kurzer Funktionstest nach dem Update:** `Blue` auswählen, auf das Bild tippen
und das Laufende abwarten. Danach `any` auswählen und erneut tippen. Falls kein
ungesendetes Werk passt, bleiben Bild und Künstlerdaten erhalten und der Lauf
endet trotzdem. Das Dropdown darf währenddessen sichtbar bleiben.
