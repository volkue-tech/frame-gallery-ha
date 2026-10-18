# Aktuelles Kunstwerk und optionaler Hintergrundmodus

[English](CURRENT_ARTWORK.md) | Deutsch | [Français](CURRENT_ARTWORK.fr.md) | [Español](CURRENT_ARTWORK.es.md) | [Italiano](CURRENT_ARTWORK.it.md)

**Beta b10: experimentell und standardmäßig aus.** Bestehende b7/b8/b9-Bildkarten bleiben nutzbar. Auf Home Assistant Green/OS werden keine API-Schlüssel, zusätzlichen Helfer, HACS-Erweiterungen, Sonderrechte oder weiteren Apps benötigt.

Auch eine lesende Verbindung kann einen Fernseher aufwecken. Kontrollierte Tests erfassten automatische Bildwechsel und einen natürlichen Einschlafvorgang an einem Frame, nicht alle Modelle oder Firmwares. Falls jedes Aufweckrisiko inakzeptabel ist, Hintergrundmodus ausgeschaltet lassen.

## Automatisches Bildgedächtnis

Jeder erfolgreich ausgewählte Upload speichert automatisch TV-Bild-ID, Titel, Künstler und Quelle, auch bei **ausgeschaltetem** Hintergrundmodus. Keine IDs selbst eintragen. Die Zuordnung gehört zur tatsächlichen Geräteidentität, nicht nur zur IP-Adresse: dieselbe Bild-ID auf einem anderen TV bezeichnet nicht dasselbe Werk. Ein neuer erfolgreicher Upload ersetzt eine ältere Zuordnung für diesen TV/diese ID.

Die privaten App-Daten bleiben bei normalen Updates erhalten. Das Zurücksetzen des Auswahlverlaufs löscht keine Zuordnungen; eine Deinstallation mit Datenlöschung dagegen schon. Vor Neuinstallation eine App-Sicherung behalten. Gespeichert werden höchstens die neuesten 2.048 Upload-Zuordnungen und 32 MiB, plus eine Sicherungskopie. Die Bildreferenz ist nur eine kleine RGB-Probe mit 64×36 Pixeln, kein hochauflösendes Bildarchiv. Ältere bildgeprüfte Zuordnungen bleiben kompatibel.

Alte TV-Bilder, Uploads anderer Apps und Sendungen ohne stabile Geräteidentität bleiben unbekannt. Künstler werden nicht geraten; keine Cloud-Bilderkennung.

## Optionale aktuelle Künstlerkarte einrichten

1. Kamera, Timer, bestehende Karten und die Entitäts-ID `script.frame_gallery_new_artwork` behalten.
2. **Hintergrundmodus** einschalten und die App neu starten. Start/Stop steuert jetzt den Dienst, keinen Bildwechsel. Optionaler Systemstart allein verbindet sich nicht mit dem TV.
3. Nur den Script-Inhalt durch das [vollständige Hintergrund-Sende-Script](examples/background-send-script.yaml) ersetzen. App-Slug und vorhandene Timer-ID bei Bedarf anpassen. Aufrufende Karten funktionieren weiter; direkte `hassio.app_start`-Automationen auf das Script umstellen.
4. Bei sichtbar eingeschaltetem Kunstmodus ausdrücklich ein neues Werk anfordern. Erst ein frischer erfolgreicher Sendevorgang mit gespeicherter TV-Zuordnung erlaubt eine experimentelle Ereignissitzung. Start/Neustart/Aktualisieren allein aktiviert sie nicht.
5. Eine manuelle Dashboard-Karte mit dem **vollständigen** YAML unten ergänzen.

Die bisherige Bild-/Farb-/Künstlerkarte zeigt weiterhin die **zuletzt gesendete Vorschau**, keinen Live-Screenshot. Diese zusätzliche native Karte zeigt davon getrennt die aktuelle Information.

```yaml
type: markdown
title: Frame Gallery — Aktuelles Kunstwerk
content: >-
  {% set item = states.sensor.frame_gallery_current_artwork %}
  {% if item is not defined or item is none %}
  Noch keine aktuellen Informationen verfügbar.
  {% elif item.state == 'artwork' and
      as_timestamp(now()) - as_timestamp(item.last_reported, 0) <
      (900 if item.attributes.get('confirmation_method') == 'slideshow_events' else 90) %}
  **{{ item.attributes.get('display_title', '') }}**

  {{ item.attributes.get('display_artist', '') }}

  {{ item.attributes.get('display_source', '') }}

  Zuletzt bestätigt: {{ as_local(item.last_reported).strftime('%H:%M:%S') }}
  {% elif item.state == 'validation_required' %}
  TV-Prüfung gesperrt. App-Protokoll prüfen und ausdrücklich ein Bild senden.
  {% elif item.state == 'checking' %}
  Bildvorgang läuft. Die aktuelle Anzeige ist noch nicht bestätigt.
  {% elif item.state == 'unidentified' %}
  Für das angezeigte Kunstwerk ist keine Zuordnung gespeichert.
  {% else %}
  Aktuelles Kunstwerk nicht bestätigt. Der TV ist eventuell nicht erreichbar oder die Sitzung pausiert.
  {% endif %}
```

## Bestätigung und Grenzen

**Wiederanlauf-Fix in Beta b10:** Unvollständige Folgen
bekannter Diashow-Meldungen blenden die aktuellen Künstlerdaten aus und warten
auf derselben Verbindung auf eine neue vollständige Folge. Sie bestätigen kein
Werk und lösen keine weitere Abfrage aus. Unbekannte oder fehlerhafte Meldungen,
Standby, TV-Betrieb und Verbindungsverlust beenden die Sitzung weiterhin. Feste
Fehlercodes im App-Protokoll unterscheiden Start-, Empfangs-, Dekodierungs- und
Workerfehler, ohne rohe Nachrichten oder Zugangsdaten auszugeben. Diese
b10-Version ist weder installiert noch am TV getestet.

Im Protokoll bedeutet `event sequence incomplete`: Künstlerdaten ausgeblendet,
dieselbe Verbindung wartet — kein bestätigtes Werk.
`event session stopped: reason=...; no reconnect` bedeutet: Sitzung beendet,
kein automatischer Neustart. Bei einer Fehlermeldung diesen festen Fehlercode,
App-Version und TV-Modell angeben, keine Zugriffstoken oder rohen TV-Daten.

Eine Sitzung dauert höchstens acht Stunden und endet bei Einschlafen, TV-Betrieb
oder Fehlern früher. Beim erneuten Aufwachen wird sie nicht heimlich fortgesetzt.

Nach einer anfänglichen Abfrage mit lokalem Bildvergleich hört eine einzige Verbindung auf die beobachtete Diashow-Folge: `image_selected`, passendes `auto_rotation_image_changed`, danach Kunstmodus `on`, innerhalb von fünf Sekunden. Keine wiederholten TV-Abfragen alle 30 Sekunden, späteren Vorschaubilder oder automatischen Neuverbindungen. Ein Ereignis löst die gespeicherte Upload- oder bildgeprüfte Zuordnung dieses TVs auf; unbekannte IDs leeren den Text.

Der anfängliche Bildnachweis gilt 90 Sekunden. Eine vollständige Diashow-Folge gilt höchstens **15 Minuten**, passend zur getesteten Zehn-Minuten-Diashow. Doppelte IDs, Pongs und Modus-an-Meldungen verlängern nichts. Langsamere Diashows können Lücken zeigen; manuelle Wechsel müssen diese Folge nicht liefern. Die Vorlage kann etwa eine Minute Anzeigeverzögerung hinzufügen.

Einschlafen, TV-Betrieb, Verbindungsabbruch, ungültige Ereignisse oder Publikationsfehler beenden/pausieren ohne Neuverbindung. Zum Fortsetzen den TV selbst in den Kunstmodus bringen und ausdrücklich ein weiteres Werk senden. Aktualisieren verarbeitet nur bereits empfangene Ereignisse. Der Beobachter sendet keine Power-, Wake-on-LAN-, Bildauswahl- oder Modusbefehle. Trotzdem kann bereits die Verbindung Nebenwirkungen haben.

Gespeicherte IDs sind historische Zuordnungen, kein fortlaufender Pixelnachweis. Unbeobachtetes externes Ersetzen/Wiederverwenden einer TV-ID ist während reinen Ereignisempfangs nicht auszuschließen. Ein widersprechender anfänglicher Bildvergleich sperrt die gespeicherte Bildunterschrift. Keine allgemeine Firmware-/Nichtaufweckgarantie (D-235).

Der Sensor ist ein von der App publizierter HA-Zustand, keine registrierte Geräteintegration; nach einem Core-Neustart kann er vorübergehend fehlen. Veraltete/pausierte Daten blenden den Titel aus. Zurück zum Einmalbetrieb: Hintergrundmodus aus, App neu starten und ursprüngliches Einmal-Sende-Script wieder einsetzen. Nicht Verlauf oder Gerätezuordnung löschen, um eine Verbindung zu erzwingen.
