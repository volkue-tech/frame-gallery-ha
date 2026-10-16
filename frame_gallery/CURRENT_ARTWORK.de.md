# Aktuelles Kunstwerk und optionaler Hintergrundmodus

[English](CURRENT_ARTWORK.md) | Deutsch | [Français](CURRENT_ARTWORK.fr.md) | [Español](CURRENT_ARTWORK.es.md) | [Italiano](CURRENT_ARTWORK.it.md)

**Lokaler b8-Kandidat; die öffentliche b7 bleibt unverändert. Experimentell und
standardmäßig aus.** Auch lesende Verbindungen könnten einen schlafenden TV
aufwecken. Automatisches Einschlafen ohne Bewegung ist noch nicht geprüft.
Falls Aufwecken inakzeptabel wäre, diesen Modus ausgeschaltet lassen. Keine zusätzlichen Helfer,
API-Schlüssel, HACS-Erweiterungen oder weiteren Apps nötig.

## Vorhandene Karten behalten

Ohne Hintergrundmodus bleiben Einmalbetrieb und Karten unverändert. Zum
Ausprobieren den optionalen Hintergrundmodus aktivieren und die App neu
starten. Start/Stop steuert dann den Dienst, nicht den Bildwechsel. „Beim
Systemstart starten“ ist optional; ein Neustart sendet kein Bild. Nach Änderungen
an App-Optionen die App neu starten.

Im vorhandenen `script.frame_gallery_new_artwork` nur den Inhalt durch das
[vollständige Sende-Script](examples/background-send-script.yaml) ersetzen.
Die Script-ID, Kamera und den Timer behalten. Vorhandene Karten und Automationen,
die dieses Script aufrufen, funktionieren weiter. Direkte Aufrufe von
`hassio.app_start` durch das Script ersetzen. Technische IDs und Befehlswerte
bleiben Englisch. App-Slug und Timer-ID im Beispiel gegebenenfalls anpassen.
Die automatisch erzeugte Anfrage-ID und Zeit nicht durch feste Werte ersetzen.

## Optionale Informationskarte

Eine manuelle Karte hinzufügen und diesen vollständigen Block einfügen.
Die bestehende Bild-/Farb-/Künstlerkarte bleibt bestehen. Ihr Vorschaubild zeigt
weiterhin das zuletzt gesendete Bild, nicht automatisch das aktuelle TV-Bild.

```yaml
type: markdown
title: Frame Gallery — Aktuelles Kunstwerk
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% if item is not defined or item is none %}
  Noch keine aktuellen Informationen verfügbar.
  {% elif item.state == 'artwork' and
      as_timestamp(now()) - as_timestamp(item.last_reported, 0) < 90 %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Zuletzt geprüft: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% elif item.state == 'validation_required' %}
  TV-Abfragen gesperrt. App-Protokoll prüfen und ausdrücklich ein Bild senden.
  {% elif item.state == 'checking' %}
  Bildvorgang läuft. Die aktuelle Anzeige ist noch nicht bestätigt.
  {% elif item.state == 'unidentified' %}
  Das angezeigte Kunstwerk ist noch nicht zugeordnet.
  {% else %}
  Aktuelles Kunstwerk nicht bestätigt. Der TV ist eventuell nicht erreichbar oder die Abfrage pausiert.
  {% endif %}
```

Der HA-Zustand ist keine registrierte Geräteintegration. Nach einem HA-Neustart
kann er vorübergehend fehlen; nach einem App-Ausfall veralten. Die Karte blendet
unbestätigte Titel aus und kann etwa eine Minute zusätzliche Anzeigeverzögerung
haben. Unbekannte alte TV-Bilder bleiben ohne Zuordnung. Den Verlauf dafür
nicht löschen. Eine Cloud-Bilderkennung wird nicht verwendet.

Nach dem Script-Wechsel **bei eingeschaltetem Kunstmodus ein neues Bild
anfordern**. Erst erfolgreiches Senden aktiviert die Abfragen etwa alle 30
Sekunden. Start/Systemstart/Neustart allein verbindet sich nicht mit dem TV.
Die erste Abfrage merkt sich die Geräteidentität; ein anderes Gerät an derselben
Adresse wird abgelehnt. Fehler oder inaktiver Kunstmodus pausieren ohne
Neuverbindung. Zum Fortsetzen den TV selbst in den Kunstmodus bringen und
ausdrücklich ein weiteres Bild senden; reines Aktualisieren aktiviert nichts.
Zum Zurückwechseln den Modus deaktivieren, neu starten und das ursprüngliche
Einmal-Sende-Script wieder einsetzen. Nicht Verlauf oder Gerätezuordnung löschen.

Ein echter Kunstmodus-Abgleich mit Bildvergleich und Titel/Künstler-Anzeige
wurde geprüft, aber nicht das automatische Einschlafen, alle Moduswechsel oder
das langfristige Recorder-Wachstum. Der Beobachter sendet keine Power-,
Wake-on-LAN- oder Kunstmodus-Änderungen. Trotzdem könnte bereits die Verbindung
einen TV aufwecken. Eine sichere automatische Wiederaufnahme wird nicht versprochen.
