# Frame Gallery — Installation und erste Dashboardkarte

> **0.1.0b18 — optionaler begrenzter Wiederanlauf (D-247/D-250).** Alte gespeicherte Schalter erlauben weiterhin keine automatischen Abfragen: `current_state_refresh` und Startabrufe bei bereits eingeschaltetem TV bleiben gesperrt. NEU ist `standby_resume`, standardmäßig AUS; erforderlich sind Hintergrundmodus und die vorhandene Samsung-Entität `resume_state_entity`. Die laufende App muss 30 Sekunden durchgehend Aus und danach ein frisches An für 10 Sekunden stabil beobachten, bevor genau eine geräte-/bildgeprüfte Lesesitzung erlaubt wird. Höchstens sechs Versuche pro Stunde, mindestens 60 Sekunden Abstand auch über normale Neustarts. Der Wiederanlauf sendet keine Bild-, Power- oder Modusbefehle, koppelt nicht neu und wiederholt Fehler nicht blind. Bei Verbindungsverlust und weiter bestehendem HA-An ist ein neuer vollständiger Wechsel nötig. Physische Verbindungsnebenwirkungen sind ungeklärt; keine Nichtaufweckgarantie. Karten/Scripte bleiben erhalten. [Vollständige optionale Statuskarte](CURRENT_STATUS.de.md) · [aktuelle Bildvorschau](CURRENT_PREVIEW.de.md) · [b18-Prüfbericht und Grenzen](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA18_VALIDATION.md).

[English](DOCS.md#installation) | **Deutsch** | [Français](SETUP.fr.md) | [Español](SETUP.es.md) | [Italiano](SETUP.it.md)

Die Anleitung wird über die Sprachlinks gewählt, nicht automatisch durch Home Assistant. Ab **0.1.0b7** gibt es die App-Konfiguration auf Englisch, Deutsch, Französisch, Spanisch und Italienisch sowie die [optionale Künstlerauswahl](COMMONS_ARTIST.de.md). Die Konfigurationsbeschriftungen folgen der Sprache deiner HA-Oberfläche; technische Werte, IDs und Pfade bleiben unverändert. Unter b6 gibt es nur englische/deutsche App-Texte und keine Künstlerauswahl. Technische Hintergrunddokumente bleiben [Englisch](DOCS.md#options).

## 1. Installieren

Du brauchst Home Assistant OS mit Supervisor/Apps, etwa HA Green, mit HA 2026.2 oder neuer. Container- und Core-only-Installationen können diese App nicht installieren. Dein Samsung Frame muss im selben lokalen Netz/Subnetz erreichbar sein. Keine API-Keys, kein SSH, kein HACS und keine Änderung an configuration.yaml sind erforderlich.

1. [Repository zu Home Assistant hinzufügen](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fvolkue-tech%2Fframe-gallery-ha). Alternativ: Einstellungen → Apps → App-Store → ⋮ → Repositorys und `https://github.com/volkue-tech/frame-gallery-ha` hinzufügen.
2. Nach **Samsung** oder **Frame Gallery** suchen. **Frame Gallery – Samsung Frame TV** öffnen und **Installieren** wählen. Der Green lädt ein fertiges Image, er baut nichts selbst.
3. In Konfiguration die feste private IPv4-Adresse des TV unter **TV-IP-Adresse** (`tv_host`) eintragen, zum Beispiel `192.168.1.20`, und speichern. Im Router reservieren; Gerätenamen wie `tv.local` werden nicht akzeptiert.
4. Watchdog und **Beim Systemstart starten** ausgeschaltet lassen: Die App lädt bei jedem Start ein Werk und beendet sich danach. Sie soll nicht in einer Neustartschleife laufen oder bei jedem HA-Neustart das Bild wechseln.

Bei Updates die bestehende App aktualisieren, **nicht deinstallieren**. Einstellungen und Sendeverlauf bleiben erhalten.

## 2. Erstes Werk auf dem TV

TV einschalten, dann im Info-Reiter der App **Starten**. Im **Protokoll** den Ablauf verfolgen. Beim ersten Verbindungsversuch die Anfrage auf dem TV innerhalb von **20 Sekunden** bestätigen. Falls dein Modell die Benachrichtigung für externe Geräte anbietet, ist „Nur beim ersten Mal“ sinnvoll.

Bei `outcome=tv_not_authorized` erneut starten und bestätigen. `outcome=delivered` bedeutet, dass Upload und Auswahl vom TV-Protokoll bestätigt wurden; prüfe auch das tatsächliche Bild. **Gestoppt** nach dem Lauf ist normal. Für ein neues Bild die App erneut starten.

| Konfigurationsfeld | Empfehlung |
| --- | --- |
| Bildquelle (`source`) | `wikimedia_commons`, Standard bei Neuinstallation. |
| Farbwunsch (Commons) (`color`) | `any` für alle Farben, einzelne Farbe optional. |
| Nur Querformat (`landscape_only`) | An. |
| 16:9 bevorzugen (kann länger dauern) (`strict_tv_format`) | An für die engere Auswahl; aus für die gesamte Commons-Auswahl. |
| Bildanpassung (contain = ohne Beschnitt) (`fit_mode`) | `contain` zeigt das ganze Werk; `cover` kann Ränder abschneiden. |

1000 Commons-Werke liegen höchstens 2,5 % neben 16:9. Die engere Präferenz nutzt etwa 1 %; kleine Ränder können bleiben. Optionale Felder bei Bedarf über **Nicht verwendete optionale Konfigurationsoptionen anzeigen** einblenden. Eine Dashboardkarte entsteht nicht automatisch.

## 3. Vorschaukamera anlegen

Nach einem erfolgreichen Lauf: Einstellungen → Geräte & Dienste → Integration hinzufügen → **Local File**. Die Vorschaudatei muss bereits existieren.

![Local-File-Dialog vor Eingabe, mit Name und Dateipfad.](https://raw.githubusercontent.com/volkue-tech/frame-gallery-ha/main/docs/images/local-file-setup.png)

| Feld | Eingabe |
| --- | --- |
| Name | `Frame Gallery Preview`, statt des Vorgabewerts Local File. |
| Dateipfad | `/media/frame_gallery/preview/latest.jpg` |

Mit OK wird automatisch eine **Kamera-Entität** angelegt. Sie zeigt eine Datei, keine echte Kamera. Die Integrationsseite heißt weiterhin Local File. **1 Entität** heißt: die Entität ist schon da, kein weiterer Installationsschritt.

**1 Entität → Zeile Frame Gallery Preview → ⋮ → Details → ID**. Erwartet: `camera.frame_gallery_preview`. Bei anderem ID-Wert deinen tatsächlichen Wert überall im YAML einsetzen. Ein bereits verwendeter Name kann einen Suffix erzeugen. Nachträgliches Umbenennen verändert die ID nicht automatisch. Bereits vorhandene Kamera wiederverwenden, keine zweite mit gleichem Pfad anlegen. Im Karteneditor nach dem Anzeigenamen suchen, nicht nur nach der ID.

**Datenschutz:** In Details stehen auch Zugriffstoken. Nur ID und Dateipfad teilen, niemals den ganzen Attributbereich.

## 4. Lade-Timer erstellen

Einstellungen → Geräte & Dienste → Helfer → Helfer erstellen → Timer. Name: `Frame Gallery run`, Dauer: `0:02:30`. ID prüfen: `timer.frame_gallery_run`.

In der App unter **Dashboard-Ladeanzeige (optional)** (`loading_timer`) diesen Wert eintragen und speichern. Erst dieses Feld verknüpft den Laufabschluss mit dem Timer. Einen eigenen Timer nur für diese App verwenden.

## 5. Skript erstellen

Einstellungen → Automationen & Szenen → Skripte → Skript erstellen → ⋮ → In YAML bearbeiten. Diesen vollständigen Block einfügen, speichern, ID `script.frame_gallery_new_artwork` prüfen. Der englische Alias hält die vorgeschlagene technische ID stabil. Das öffentliche App-ID-Beispiel `a94fc569_frame_gallery` in der App-URL prüfen; keine alte lokale Test-App verwenden. Abweichende IDs überall anpassen.

```yaml
alias: Frame Gallery new artwork
description: Startet die Frame-Gallery-App und zeigt währenddessen einen Ladehinweis im Dashboard.
mode: single
sequence:
  - condition: state
    entity_id: timer.frame_gallery_run
    state: idle
  - action: timer.start
    target:
      entity_id: timer.frame_gallery_run
    data:
      duration: "00:02:30"
  - action: hassio.app_start
    data:
      app: a94fc569_frame_gallery
    continue_on_error: true
  - wait_template: "{{ not is_state('timer.frame_gallery_run', 'active') }}"
    timeout: "00:02:30"
    continue_on_timeout: true
  - delay: "00:00:04"
```

## 6. Karte hinzufügen

Dashboard bearbeiten → Karte hinzufügen → Manuell. Den kompletten Block einfügen, gegebenenfalls IDs anpassen und speichern. Administrator-Konto verwenden.

```yaml
type: vertical-stack
cards:
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

Bild antippen für ein neues Werk, lange drücken für die Vorschau. Der Ladetext erscheint nur beim aktiven Timer. Nach dem Aufräumen wird dieser beendet, auch ohne Treffer oder nach sauberem Abbruch. Nach 150 Sekunden begrenzt die Timer-Dauer die Anzeige, falls die Benachrichtigung ausfällt. Das Verschwinden beweist keinen erfolgreichen Upload: Protokoll prüfen. Die Aktualisierung des Bildes ist davon unabhängig.

Bei fehlender Entität IDs prüfen, nicht eine weitere Kamera anlegen. Die Editor-Vorschau des Ladetexts beweist keinen aktiven Lauf.

## Optional und Hilfe

- [Farbwähler](COMMONS_COLOUR.de.md): ein zusätzlicher Dropdown-Helfer, kein neues Skript.
- [Künstlerauswahl](COMMONS_ARTIST.de.md): ab b7 verfügbar; vorher von b6 aktualisieren.
- [Titel und Künstler anzeigen](ARTWORK_INFO.md): englische Anleitung, separater Text-Helfer; die Standardkarte funktioniert ohne ihn.

Auf GitHub haben Codeblöcke einen Kopierbutton. Fehlt dieser im HA-Dokumentationsreiter, diese Anleitung auf GitHub öffnen. Nur YAML kopieren, keine Markdown-Begrenzungszeichen.

Ohne neues passendes Werk bleiben Bild, Vorschau und Informationen unverändert. Bereits gesendete Werke bleiben ausgeschlossen. Temporäre Downloads werden aufgeräumt; Bilder im TV-Speicher löscht die App nicht. Die Kompatibilität mit jedem TV-Modell ist nicht garantiert. [Problem melden](https://github.com/volkue-tech/frame-gallery-ha/issues) mit Version, Modell und Protokollergebnis, ohne Geheimnisse.

Unabhängiges Projekt ohne Verbindung zu Samsung, Wikimedia, Museen oder Home Assistant. [Technische Hilfe und Lizenzen](DOCS.md#reading-the-log) bleiben Englisch.
