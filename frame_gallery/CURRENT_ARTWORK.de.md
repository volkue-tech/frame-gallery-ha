# Aktuelles Kunstwerk und optionaler Hintergrundmodus

[English](CURRENT_ARTWORK.md) | Deutsch | [Français](CURRENT_ARTWORK.fr.md) | [Español](CURRENT_ARTWORK.es.md) | [Italiano](CURRENT_ARTWORK.it.md)

**Öffentliche Beta b13: experimentell und standardmäßig aus.** Bestehende b7/b8/b9/b10/b11/b12-Karten bleiben nutzbar. Auf Home Assistant Green/OS werden keine API-Schlüssel, neuen Helfer, HACS-Erweiterungen, Sonderrechte oder weiteren Apps benötigt.

Auch eine lesende Verbindung kann einen Fernseher aufwecken. Kontrollierte Tests erfassten automatische Bildwechsel und einen natürlichen Einschlafvorgang an einem Frame, nicht alle Modelle oder Firmwares. Falls jedes Aufweckrisiko inakzeptabel ist, Hintergrundmodus ausgeschaltet lassen.

## Automatisches Bildgedächtnis

### Startabgleich und nach Sleep fortsetzen — b12, optional

Nach einem früheren erfolgreichen Frame-Gallery-Bildversand den **Hintergrundmodus**
aktivieren und bei **Startabgleich / nach Sleep fortsetzen** (`resume_state_entity`) die vorhandene
Samsung-Entitäts-ID dieses TVs (`media_player` oder `remote`) eintragen. Sie steht
unter Einstellungen → Geräte & Dienste → Entitäten. Danach die App neu starten.
Keine neuen Helfer, kein erneuter Bildversand und keine Kartenänderung nötig.

Die erste gespeicherte HA-Abfrage bei jedem so konfigurierten App-Start erlaubt
**genau einen Startabgleich bei `on`**, auch nach Stunden ohne Zustandswechsel.
Vor Künstlerdaten werden Geräteidentität, Kunstmodus, aktuelle ID und Bild neu
geprüft; kein Bild wird gesendet. Fehlender, ungültiger, zukünftiger, ausgeschalteter,
unbekannter oder fehlgeschlagener erster Zustand verbraucht die Startgelegenheit.
Ein späteres `on` wiederholt den Startversuch nicht.

**Startfenster — b13:** Ein festes Zeitfenster von zehn Sekunden gibt
einem angenommenen neuen Bildauftrag Vorrang vor dem automatischen Startabgleich.
Mit der Annahme verfällt die übrig gebliebene Startgelegenheit vor dem Versand,
auch wenn dieser später fehlschlägt oder kein passendes Bild findet (`no_match`).
Nur ein gültiger erfolgreicher Versand darf danach seine eigene Lesesitzung
starten. Ohne angenommenen Bildauftrag bleibt der eigenständige Startabgleich
nach dem Fenster möglich, solange der gespeicherte HA-Zustand gültig und `on`
bleibt. Die späteren Regeln für echte `off`/`on`-Wechsel bleiben unverändert.

Dieses begrenzte Fenster kann beliebig verspätete Scripte nicht vorhersagen.
Läuft bereits ein eigenständiger Empfänger, muss ein späterer Versand ihn zuerst
stoppen und sein Ende abwarten. Die Offline-Tests dieses Fixes liefern keinen
neuen Hardware-Nachweis gegen Aufwecken oder einen Moduswechsel des TVs.

Danach liest die App nur diesen HA-Zustand alle fünf Sekunden. Ein beobachtetes
`off` und ein neueres, höchstens 30 Sekunden altes `on` erlauben einen weiteren
Versuch. Beide Wege teilen sich höchstens sechs Versuche pro rollender Stunde
**in diesem Dienstprozess**. Doppelte/veraltete Weckwechsel und Beobachtungslücken
erlauben keine Wiederholung. Abgewiesene Anmeldung sperrt automatische Abfragen
im Prozess. Ein Neustart ist eine neue Startgelegenheit, keine dauerhafte
Neustart-übergreifende Begrenzung; keine Neustartschleifen verwenden.

HA `on` beweist keinen Kunstmodus. Bereits die Verbindung kann aufwecken oder den
Modus beeinflussen; für diesen neuen Weg liegen Simulationen, keine neuen
Hardware-Sicherheitsnachweise vor. Leer lassen zum Deaktivieren. Eine gestoppte
App erkennt kein Aufwachen. Die 90-Sekunden-/15-Minuten-Anzeigegrenzen bleiben.

Jeder erfolgreich ausgewählte Upload speichert automatisch TV-Bild-ID, Titel, Künstler und Quelle, auch bei **ausgeschaltetem** Hintergrundmodus. Keine IDs selbst eintragen. Die Zuordnung gehört zur tatsächlichen Geräteidentität, nicht nur zur IP-Adresse: dieselbe Bild-ID auf einem anderen TV bezeichnet nicht dasselbe Werk. Ein neuer erfolgreicher Upload ersetzt eine ältere Zuordnung für diesen TV/diese ID.

Die privaten App-Daten bleiben bei normalen Updates erhalten. Das Zurücksetzen des Auswahlverlaufs löscht keine Zuordnungen; eine Deinstallation mit Datenlöschung dagegen schon. Vor Neuinstallation eine App-Sicherung behalten. Gespeichert werden höchstens die neuesten 2.048 Upload-Zuordnungen und 32 MiB, plus eine Sicherungskopie. Die Bildreferenz ist nur eine kleine RGB-Probe mit 64×36 Pixeln, kein hochauflösendes Bildarchiv. Ältere bildgeprüfte Zuordnungen bleiben kompatibel.

Alte TV-Bilder, Uploads anderer Apps und Sendungen ohne stabile Geräteidentität bleiben unbekannt. Künstler werden nicht geraten; keine Cloud-Bilderkennung.

### Optionale Aktualisierung des aktuellen Zustands — b14-Kandidat

`current_state_refresh` ist ein zusätzlicher optionaler Schalter, **standardmäßig
aus**, und setzt `background_mode` voraus. Er erlaubt höchstens eine lesende
Kohärenzprüfung von aktuellem Kunstmodus und Bild-ID je 60 Sekunden über den
**bereits verbundenen Art-Socket**. Damit sollen bekannte Künstler-/Titeldaten
nach dem TV-Menü oder dem Fortsetzen einer Diashow wieder erscheinen, auch wenn
dasselbe Bild bleibt. Keine neue Verbindung und keine Bild-, Power- oder
Modusbefehle. Standby oder ein beobachtetes HA-Aus beendet die Sitzung.
Unbekannte Bilder bleiben unbekannt; kein Titel wird erfunden oder übernommen.

Auch lesende Anfragen über denselben Socket können das automatische Einschlafen
beeinflussen. Falls dieses Risiko inakzeptabel ist, ausgeschaltet lassen.
Offline-Tests bestätigen weder Firmware-Kompatibilität noch Nichtaufwecken.
Bestehende Karten und Scripte brauchen keine Änderung.

## Optionale aktuelle Künstlerkarte einrichten

1. Kamera, Timer, bestehende Karten und die Entitäts-ID `script.frame_gallery_new_artwork` behalten.
2. **Hintergrundmodus** einschalten und die App neu starten. Start/Stop steuert den Dienst, keinen Bildwechsel. Ohne optionale Entität oben keine Startverbindung; mit ihr kann das erste HA `on` nach dem Zehn-Sekunden-Fenster einen Startabgleich erlauben, sofern kein angenommener Bildauftrag ihn ersetzt.
3. Nur den Script-Inhalt durch das [vollständige Hintergrund-Sende-Script](examples/background-send-script.yaml) ersetzen. App-Slug und vorhandene Timer-ID bei Bedarf anpassen. Aufrufende Karten funktionieren weiter; direkte `hassio.app_start`-Automationen auf das Script umstellen.
4. Nach einem früheren erfolgreichen Versand die optionale Entität oben konfigurieren: Das bereits sichtbare Werk wird ohne neuen Versand geprüft. Bei einer Neuinstallation ohne gespeicherte TV-Zuordnung einmal das erste neue Werk im sichtbaren Kunstmodus anfordern; ein erfolgreicher Versand erlaubt eine experimentelle Ereignissitzung. Aktualisieren allein öffnet keine Verbindung.
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
  Warte auf einen freigegebenen Abgleich. Hintergrund-/Entitätseinstellungen und App-Protokoll prüfen; ein konfigurierter Startabgleich braucht kein neues Bild.
  {% elif item.state == 'checking' %}
  Aktuelle Anzeige noch nicht bestätigt. Warte auf einen gültigen Bild- oder Diashow-Nachweis.
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
Workerfehler, ohne rohe Nachrichten oder Zugangsdaten auszugeben. Die
b12-Startfunktion und das b13-Startfenster haben keinen neuen Live-TV- oder Einschlafnachweis.

Im Protokoll bedeutet `event sequence incomplete`: Künstlerdaten ausgeblendet,
dieselbe Verbindung wartet — kein bestätigtes Werk.
`event session stopped: reason=...; no reconnect` bedeutet: Sitzung beendet,
keine sofortige automatische Wiederholung. Bei einer Fehlermeldung diesen festen Fehlercode,
App-Version und TV-Modell angeben, keine Zugriffstoken oder rohen TV-Daten.

Eine Sitzung dauert höchstens acht Stunden und endet bei Einschlafen, TV-Betrieb
oder Fehlern früher. Ein konfigurierter neuer Prozessstart oder späterer frischer HA-Weckwechsel oben kann eine neue Abfrage erlauben; auch ein erfolgreicher ausdrücklicher Versand kann eine Sitzung starten.

Nach einer anfänglichen Abfrage mit lokalem Bildvergleich hört eine einzige Verbindung auf die beobachtete Diashow-Folge: `image_selected`, passendes `auto_rotation_image_changed`, danach Kunstmodus `on`, innerhalb von fünf Sekunden. Bei ausgeschaltetem `current_state_refresh` gibt es innerhalb dieser Sitzung keine wiederholten TV-Abfragen, späteren Vorschaubilder oder Neuverbindungen. Eingeschaltet sind nur die begrenzten Prüfungen oben erlaubt, keine neuen Vorschaubilder oder Verbindungen. Ein Ereignis löst die gespeicherte Upload- oder bildgeprüfte Zuordnung dieses TVs auf; unbekannte IDs leeren den Text.

Der anfängliche Bildnachweis gilt 90 Sekunden. Eine vollständige Diashow-Folge gilt höchstens **15 Minuten**, passend zur getesteten Zehn-Minuten-Diashow. Doppelte IDs, Pongs und Modus-an-Meldungen verlängern nichts. Langsamere Diashows können Lücken zeigen; manuelle Wechsel müssen diese Folge nicht liefern. Die Vorlage kann etwa eine Minute Anzeigeverzögerung hinzufügen.

Bei ausgeschalteter Zustandsaktualisierung oder ohne erfolgreiche neue Prüfung
kann ein fest gewähltes unverändertes Bild nach 90 Sekunden unbestätigt sein.
Der Startfix allein verlängert keinen Bildnachweis und fragt nicht
wiederholt ab, um einen statischen Künstlertext aktuell erscheinen zu lassen.

Einschlafen, TV-Betrieb, Verbindungsabbruch, ungültige Ereignisse oder Publikationsfehler beenden/pausieren ohne sofortige Neuverbindung. Ohne die optionale Weckwechsel-Einstellung bleibt ein ausdrücklicher neuer Bildversand im sichtbaren Kunstmodus nötig. Manuelles Aktualisieren verarbeitet nur bereits empfangene Ereignisse. Der Beobachter sendet keine Power-, Wake-on-LAN-, Bildauswahl- oder Modusbefehle. Trotzdem kann bereits die Verbindung Nebenwirkungen haben.

Gespeicherte IDs sind historische Zuordnungen, kein fortlaufender Pixelnachweis. Unbeobachtetes externes Ersetzen/Wiederverwenden einer TV-ID ist während reinen Ereignisempfangs nicht auszuschließen. Ein widersprechender anfänglicher Bildvergleich sperrt die gespeicherte Bildunterschrift. Keine allgemeine Firmware-/Nichtaufweckgarantie (D-235).

Der Sensor ist ein von der App publizierter HA-Zustand, keine registrierte Geräteintegration; nach einem Core-Neustart kann er vorübergehend fehlen. Veraltete/pausierte Daten blenden den Titel aus. Zurück zum Einmalbetrieb: Hintergrundmodus aus, App neu starten und ursprüngliches Einmal-Sende-Script wieder einsetzen. Nicht Verlauf oder Gerätezuordnung löschen, um eine Verbindung zu erzwingen.
