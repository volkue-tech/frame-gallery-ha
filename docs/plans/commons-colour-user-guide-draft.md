# Farbauswahl im kommenden Update

**Noch nicht veröffentlicht.** Diese Anleitung beschreibt den lokalen Entwurf,
nicht die aktuell installierbare Beta 0.1.0b5. Die Erweiterung auf insgesamt
1000 lokal geprüfte Werke ist vorbereitet. Native Releaseprüfung und
Veröffentlichung stehen noch aus; die Farbfunktion gibt es nicht in Beta b5.

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
sein. Der Entwurf verwendet ungefähr fünf Prozent Bildfläche als Schwelle.
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

**Optional und erst mit dem kommenden Update nutzbar.** Ohne diesen Schritt
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
   Commons)** (`color_entity`) diese ID eintragen. Falls verborgen, **Nicht
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

## Welche weiteren Selektoren wären sinnvoll?

Diese Prüfung ist Teil des Update-Scopes; sie fügt **keine weiteren Filter**
zur Oberfläche hinzu. Der eingefrorene Katalog hat 1000 Titel, Künstlerlabels,
Dateimaße und Farbprofile; er enthält 560 unterschiedliche Künstlerlabels.
Nur 299 Datensätze enthalten bereits eine Werk-Identität (Q-ID). „Künstlerlabel“
ist keine Behauptung, dass alle Namen schon kanonisch vereinheitlicht sind.

| Idee | Datenlage und Empfehlung |
| --- | --- |
| Künstler / Künstlerin | Für alle Werke vorhanden. Sinnvollster nächster Filter: suchbare Auswahl statt 560 Radiobuttons. Schreibweisen, unbekannte Urheber und Sammelzuschreibungen vorher normalisieren; kleine Auswahlen können durch den Sendeverlauf schnell leer werden. |
| Blau **und** Gelb | Vollständige Farbanteile und bis zu drei wichtige Farbgruppen sind bereits gespeichert. Später klar zwischen „beide Farben“ und „eine davon“ unterscheiden. Diesmal nur eine Farbe. |
| Helles / dunkles Bild | Aus den gespeicherten RGB-Paletten ableitbar, aber noch kein kalibriertes Helligkeitsmerkmal. Erst mit verschiedenen Werken testen; „ruhig“ oder „warm“ ist nicht automatisch eine objektive Bildfarbe. |
| Epoche / Entstehungsjahr | In den Quelldokumenten teilweise vorhanden, aber kein vollständiges, einheitliches Jahresfeld im Katalog. Nicht aus Titeln oder Lebensdaten des Künstlers raten. Vor einem Filter Daten ergänzen und unbekannte Werte sichtbar behandeln. |
| Motiv / Medium | Landschaft, abstrakt, Fotografie oder Digitales wären attraktiv. Bisher keine konsistenten Tags für alle 1000 Werke; Commons-Kategorien und Dateinamen allein sind kein belastbarer Motivfilter. Kuratierte Tags benötigen eine eigene Recherche. |
| Sammlung / Museum | Die Bildquelle ist schon wählbar. Für Commons ist die Sammlung aber nicht durchgängig normalisiert; die Commons-Datei ist nicht automatisch Museumsbesitz. Dafür nicht dieselbe Vollständigkeit wie beim Künstler versprechen. |
| Format / Rand | Originalmaße liegen für alle Werke vor. Querformat und 16:9-Präferenz existieren bereits; kein weiteres gleichartiges Feld nötig. `contain` schützt weiterhin vor Beschnitt. |

Empfehlung nach diesem Update: zuerst **Künstlerauswahl** planen, dann
**Farbkombinationen** mit den vorhandenen Profilen. Epoche und Motiv brauchen
zuerst vervollständigte Metadaten. Neue Pflicht-Helfer oder eine überladene
Konfigurationsmaske sollen daraus nicht entstehen.

## Stand der Prüfung

Der lokale Update-Katalog enthält genau 1000 aktive Werke: 344 aus dem Bestand
und 656 geprüfte Neuzugänge. Alle besitzen Farbprofile mit festem Bezug zur
Quelldatei. Die [private Farb-Vorschau](http://127.0.0.1:8881/gallery.html)
zeigt standardmäßig diese Auswahl. 56 freigegeben zurückgestellte Bestandsfälle
und sieben geprüfte Reserven sind separat sichtbar; alle ursprünglichen IDs,
Quellen und Analysedaten bleiben erhalten. Das ist kein Zurücksetzen deines
Sendeverlaufs. Labels und Schwelle wurden im visuellen Pilot kalibriert;
die native Releaseprüfung und der spätere Green-Test bleiben offen.
Diese Seite wird erst nach der Freigabe in die öffentliche Installationsanleitung
übernommen. Die veröffentlichte Anleitung bleibt bis dahin bei den Funktionen
der tatsächlich verfügbaren Beta.
