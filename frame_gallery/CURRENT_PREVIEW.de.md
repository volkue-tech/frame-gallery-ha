# Vorschau des aktuellen Kunstwerks

[English](CURRENT_PREVIEW.md) | **Deutsch** | [Français](CURRENT_PREVIEW.fr.md) | [Español](CURRENT_PREVIEW.es.md) | [Italiano](CURRENT_PREVIEW.it.md)

**Öffentliche Beta 0.1.0b17 — separate optionale aktuelle Bildvorschau.**

**Sicherheitsbegrenzung des Abgleichs (D-247):** Der Hintergrundmodus bleibt
experimentell und standardmäßig aus. Automatische Start-/Aufwach-Verbindungen
und Minutenabfragen sind auch bei gespeicherter Freigabe gesperrt. Nur ein
frischer ausdrücklich angeforderter erfolgreicher Versand kann passive Diashow-
Ereignisse verfolgen. Unveränderte Bilder veralten; nach Menü/TV-Modus, Sleep oder
Verbindungsverlust gibt es keinen automatischen Wiederanlauf. Eine Verbindung
kann den TV trotzdem beeinflussen: keine Nichtaufweckgarantie. Zuerst die
[Einrichtung und Grenzen der aktuellen Künstleranzeige](CURRENT_ARTWORK.de.md) lesen.

Die bisherige Bildkarte bleibt die Vorschau des zuletzt gesendeten Werks. Diese zusätzliche optionale Karte zeigt eine gespeicherte Vorschau nur bei frisch bestätigten aktuellen Künstler-/Titeldaten. Sie ist kein Live-Screenshot.

1. Bestehende Einrichtung der aktuellen Künstleranzeige, Karten und Scripte behalten. Keine neue App-Option, Sonderrechte, HACS-Erweiterung oder Änderung an configuration.yaml nötig.
2. Nach einem erfolgreichen Versand mit dieser Version wird automatisch ein kleines JPEG gespeichert, auch im Einmalmodus. Die aktuelle Anzeige benötigt den bestehenden optionalen Hintergrundabgleich. Alte TV-Bilder werden nicht automatisch nachgeladen; es gibt keine zusätzliche TV-Abfrage.
3. Nach der Initialisierung des Hintergrunddiensts unter Einstellungen → Geräte & Dienste die Integration Local File ergänzen. Name: `Frame Gallery Current Preview`; Dateipfad: `/media/frame_gallery/preview/current.jpg`. Die bisherige Local-File-Kamera nicht ersetzen.
4. Die tatsächliche Entitäts-ID der neuen Kamera prüfen. Das Beispiel verwendet `camera.frame_gallery_current_preview`; bei abweichender ID nur `camera_entity` unten anpassen. Die vollständige optionale manuelle Karte unten ergänzen.

```yaml
type: markdown
title: Frame Gallery — Aktuelles Kunstwerk
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% set camera_entity = 'camera.frame_gallery_current_preview' %}
  {% if item is defined and item is not none %}
    {% set age = as_timestamp(now()) - as_timestamp(item.last_reported, 0) %}
  {% else %}
    {% set age = -1 %}
  {% endif %}
  {% if item is defined and item is not none and item.state == 'artwork'
      and age >= 0 and age <
      (900 if item.attributes.get('confirmation_method') == 'slideshow_events' else 90) %}
    {% set picture = state_attr(camera_entity, 'entity_picture') %}
    {% if item.attributes.get('preview_available', false)
        and picture is string and picture
        and state_attr(camera_entity, 'file_path') == '/media/frame_gallery/preview/current.jpg'
        and states(camera_entity) not in ['unknown', 'unavailable'] %}
      {% set separator = '&' if '?' in picture else '?' %}
  <img src="{{ (picture ~ separator ~ 'fg=' ~ item.attributes.get('preview_sha256', '')) | e }}" alt="Aktuelles Kunstwerk">

    {% else %}
  Keine gespeicherte Vorschau für dieses Werk; Künstlerdaten bleiben verfügbar.

    {% endif %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Zuletzt bestätigt: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% else %}
  Kein frisch bestätigtes Kunstwerk verfügbar.
  {% endif %}
```

Vorschauen haben höchstens 640×360 Pixel und 32 KiB JPEG-Daten. Der private Cache ist einschließlich Speicher-Overhead auf 128 MiB und 4.096 Einträge begrenzt; Verdrängung löscht niemals Zuordnungen oder Verlauf. Unbekannte, alte, abgewiesene oder verdrängte Bilder bekommen keine erfundene Vorschau. Wenig Speicher oder Cachefehler dürfen Künstlerdaten nicht blockieren.

Die vollständige abgesicherte Karte verwenden, keine ungeschützte Einzelkamera für current.jpg: Nach einem Absturz kann die Datei den letzten Inhalt behalten, die Karte blendet jedoch veraltete Nachweise aus. Vor dem Dateitausch wird die Vorschau in HA deaktiviert und erst nach geprüftem atomarem Schreiben wieder freigegeben. Die Prüfsumme umgeht den Browser-Bildcache; sie ist kein neuer TV-Nachweis. latest.jpg und bestehende Karten bleiben unberührt. Keine zusätzliche TV-Vorschaubildabfrage, Cloud-Erkennung oder Verbindung.

[Anleitung zur aktuellen Künstleranzeige](CURRENT_ARTWORK.de.md)

Lokaler unveröffentlichter Kandidat: [begrenzter Standby-Wiederanlauf und vollständige Statuskarte](CURRENT_STATUS.de.md). Das bestehende vollständige YAML unten bleibt unverändert; keine Live-Änderung oder Veröffentlichung.
