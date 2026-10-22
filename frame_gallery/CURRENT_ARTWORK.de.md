# Aktuelles Kunstwerk und optionaler Hintergrundmodus

> **0.1.0b17-Sicherheitsbegrenzung (D-247):** Automatische Start-/
> Aufwach-Verbindungen und Minutenabfragen über `current_state_refresh` sind
> gesperrt, auch bei gespeicherter Freigabe. `resume_state_entity` ist nur noch
> ein Stoppsignal, niemals eine Startfreigabe. Nach einem frischen erfolgreichen
> ausdrücklichen Bildversand kann der passive Empfänger vollständigen Diashow-
> Ereignissen folgen. Unveränderte Bilder veralten; nach Sleep oder Sitzungsverlust
> gibt es keine automatische Wiederherstellung. Dies ersetzt die älteren b11–b16-
> Wiederanlauf-Anweisungen unten. Karten, Script-IDs und Bildzuordnungen bleiben
> erhalten. Verbindungsnebenwirkungen sind damit nicht allgemein ausgeschlossen.

Ab 0.1.0b17: [optionale aktuelle Bildvorschau](CURRENT_PREVIEW.de.md). Bestehende Karten bleiben unverändert. [b17-Prüfbericht und Grenzen](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA17_VALIDATION.md).

[English](CURRENT_ARTWORK.md) | Deutsch | [Français](CURRENT_ARTWORK.fr.md) | [Español](CURRENT_ARTWORK.es.md) | [Italiano](CURRENT_ARTWORK.it.md)

**Historische b16-Parserkorrektur — Abgleich in b17 gesperrt:** Der optionale Zustandsabgleich akzeptiert die echten
Antworten `artmode_status` / `current_artwork` mit strenger Anfrage-ID-Prüfung.
Keine neue Option, Verbindung, Zuordnungsdatei oder Kartenänderung nötig.

**Öffentliche Beta 0.1.0b17: experimentell und standardmäßig aus.** Bestehende b7/b8/b9/b10/b11/b12/b13/b16-Karten bleiben nutzbar. Auf Home Assistant Green/OS werden keine API-Schlüssel, neuen Helfer, HACS-Erweiterungen, Sonderrechte oder weiteren Apps benötigt.

[Historischer b16-Prüfbericht](https://github.com/volkue-tech/frame-gallery-ha/blob/main/BETA16_VALIDATION.md) · [Historische passende Quellen](https://github.com/volkue-tech/frame-gallery-ha/releases/tag/sources-v0.1.0b16).

Auch eine lesende Verbindung kann einen Fernseher aufwecken. Kontrollierte Tests erfassten automatische Bildwechsel und einen natürlichen Einschlafvorgang an einem Frame, nicht alle Modelle oder Firmwares. Falls jedes Aufweckrisiko inakzeptabel ist, Hintergrundmodus ausgeschaltet lassen.

## Automatisches Bildgedächtnis

### Startabgleich und nach Sleep fortsetzen — b12, optional

<details>
<summary>Historisches Verhalten b12–b16 — in b17 gesperrt, keine aktuelle Einrichtungsanweisung</summary>

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

Die Wiederanlauf-Überwachung liest diesen gespeicherten HA-Zustand alle fünf
Sekunden; das ist getrennt von den optionalen Art-Socket-Prüfungen unten.
Ein beobachtetes
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

</details>

Jeder erfolgreich ausgewählte Upload speichert automatisch TV-Bild-ID, Titel, Künstler und Quelle, auch bei **ausgeschaltetem** Hintergrundmodus. Keine IDs selbst eintragen. Die Zuordnung gehört zur tatsächlichen Geräteidentität, nicht nur zur IP-Adresse: dieselbe Bild-ID auf einem anderen TV bezeichnet nicht dasselbe Werk. Ein neuer erfolgreicher Upload ersetzt eine ältere Zuordnung für diesen TV/diese ID.

Die privaten App-Daten bleiben bei normalen Updates erhalten. Das Zurücksetzen des Auswahlverlaufs löscht keine Zuordnungen; eine Deinstallation mit Datenlöschung dagegen schon. Vor Neuinstallation eine App-Sicherung behalten. Gespeichert werden höchstens die neuesten 2.048 Upload-Zuordnungen und 32 MiB, plus eine Sicherungskopie. Die Bildreferenz ist nur eine kleine RGB-Probe mit 64×36 Pixeln, kein hochauflösendes Bildarchiv. Ältere bildgeprüfte Zuordnungen bleiben kompatibel.

Alte TV-Bilder, Uploads anderer Apps und Sendungen ohne stabile Geräteidentität bleiben unbekannt. Künstler werden nicht geraten; keine Cloud-Bilderkennung.

### Optionale Aktualisierung des aktuellen Zustands — b16

<details>
<summary>Historische Minutenabfragen — in b17 auch bei gespeicherter Aktivierung gesperrt</summary>

`current_state_refresh` ist ein zusätzlicher optionaler Schalter, **standardmäßig
aus**, und setzt `background_mode` voraus. Er erlaubt höchstens eine lesende
Kohärenzprüfung von aktuellem Kunstmodus und Bild-ID je 60 Sekunden über den
**bereits verbundenen Art-Socket**. Damit sollen bekannte Künstler-/Titeldaten
nach dem TV-Menü oder dem Fortsetzen einer Diashow wieder erscheinen, auch wenn
dasselbe Bild bleibt. Keine neue Verbindung und keine Bild-, Power- oder
Modusbefehle.
Unbekannte Bilder bleiben unbekannt; kein Titel wird erfunden oder übernommen.

Ein frischer erfolgreicher `current_state_read`-Nachweis gilt 90 Sekunden.
Doppelte IDs, Pongs oder Modus-an-Meldungen allein verlängern ihn nicht.

Bei eingeschalteter Option bleibt bei `off` oder `nav` des Art-Kanals **derselbe
Socket** bestehen; diese Zustände sind kein physischer Standby. Ohne aktiven
Kunstmodus werden Künstlerdaten ausgeblendet. Die geplanten Prüfungen laufen auch
ohne Rückkehrmeldung weiter: Innerhalb derselben Minutengrenze wird zunächst nur
der Modus gelesen. Bild-IDs werden erst nach einem frisch gelesenen `on` abgefragt;
reine Menüzyklen können kein Kunstwerk bestätigen. Sieht die Sitzung anfangs
`off` oder `nav`, wartet der ursprüngliche einmalige Vorschaubild-Nachweis auf
Kunstmodus `on` über diesen Socket; er wird nicht wiederholt. Standby,
beobachtetes HA-Aus oder eine geschlossene Verbindung beenden die Sitzung
weiterhin, ohne neuen Socket oder blinde Neuverbindung.

Auch lesende Anfragen über denselben Socket können das automatische Einschlafen
beeinflussen. Falls dieses Risiko inakzeptabel ist, ausgeschaltet lassen.
Offline-Tests bestätigen weder Firmware-Kompatibilität noch Nichtaufwecken.
Bestehende Karten und Scripte brauchen keine Änderung.

</details>

## Optionale aktuelle Künstlerkarte einrichten

1. Kamera, Timer, bestehende Karten und die Entitäts-ID `script.frame_gallery_new_artwork` behalten.
2. **Hintergrundmodus** einschalten und die App neu starten. Start/Stop steuert den Dienst, keinen Bildwechsel. App-Start und HA `on` kontaktieren den TV in b17 auch bei gespeicherten Wiederanlauf-/Abgleichsoptionen nicht. Die optionale Samsung-Entität kann nur stoppen.
3. Nur den Script-Inhalt durch das [vollständige Hintergrund-Sende-Script](examples/background-send-script.yaml) ersetzen. App-Slug und vorhandene Timer-ID bei Bedarf anpassen. Aufrufende Karten funktionieren weiter; direkte `hassio.app_start`-Automationen auf das Script umstellen.
4. Bei sichtbar aktivem Kunstmodus ausdrücklich ein neues Werk über das Script anfordern. Nur ein frischer erfolgreicher Versand erlaubt eine experimentelle passive Ereignissitzung. Dienststart oder Aktualisieren liest kein bereits angezeigtes Bild. Nach Menü/TV-Modus, Sleep oder Verbindungsverlust gibt es keinen automatischen Wiederanlauf; dafür ist ein neuer ausdrücklicher erfolgreicher Versand nötig.
5. Eine manuelle Dashboard-Karte mit dem **vollständigen** YAML unten ergänzen.

Die bisherige Bild-/Farb-/Künstlerkarte zeigt weiterhin die **zuletzt gesendete Vorschau**, keinen Live-Screenshot. Diese zusätzliche native Karte zeigt davon getrennt die aktuelle Information.

Die unveränderte Karte unten enthält noch einen älteren Hilfetext bei `validation_required` zum Startabgleich. Dieser Weg ist in b17 gesperrt: Gemeint ist jetzt ein frischer ausdrücklicher erfolgreicher Versand; eine konfigurierte Entität startet keine Abfrage.

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

In b17 kann ein frischer ausdrücklicher erfolgreicher Versand eine passive
Art-Sitzung starten. Der anfängliche Vorschaubildvergleich bestätigt ein bekanntes
Werk für 90 Sekunden; eine neue vollständige Diashow-Folge (`image_selected`,
passendes `auto_rotation_image_changed`, danach Kunstmodus `on` innerhalb von
fünf Sekunden) gilt höchstens 15 Minuten. Doppelte IDs, Pongs und Modus-an allein
verlängern nichts. Ein festes Bild wird daher unbestätigt; unbekannte IDs
übernehmen niemals die Künstlerdaten eines anderen Werks.

Auch bei gespeicherter Aktivierung gibt es keine Minutenabfragen oder automatischen
Start-/Aufwach-Verbindungen. Menü/TV-Modus, Standby, Verbindungsverlust und Fehler
können die Sitzung beenden; es folgt keine Neuverbindung. Die gespeicherte Samsung-
Entität ist nur ein Stoppsignal. Aktualisieren verarbeitet vorhandene Ereignisse,
keine neue TV-Abfrage. Sitzungen dauern höchstens acht Stunden. Schon die
Verbindung kann Nebenwirkungen haben; dies ist keine Nichtaufweckgarantie.
Bestehende Karten, Scripte und Zuordnungen bleiben kompatibel.

<details>
<summary>Historische Bestätigungs-/Wiederanlaufdetails b10–b16 — gesperrte Wege sind keine b17-Anleitung</summary>

**Historischer b10-Wiederanlauf — reiner Ereignismodus (`current_state_refresh` aus):** Unvollständige Folgen
bekannter Diashow-Meldungen blenden die aktuellen Künstlerdaten aus und warten
auf derselben Verbindung auf eine neue vollständige Folge. Sie bestätigen kein
Werk und lösen keine weitere Abfrage aus. Unbekannte oder fehlerhafte Meldungen,
Standby, TV-Betrieb und Verbindungsverlust beenden die Sitzung weiterhin. Feste
Fehlercodes im App-Protokoll unterscheiden Start-, Empfangs-, Dekodierungs- und
Workerfehler, ohne rohe Nachrichten oder Zugangsdaten auszugeben. Die
b12-Startfunktion und das b13-Startfenster haben keinen neuen Live-TV- oder Einschlafnachweis.

Bei eingeschaltetem `current_state_refresh` blenden strukturell gültige, aber
unbekannte Meldungen sowie `off`/`nav` des Art-Kanals die Künstlerdaten aus und
behalten denselben Socket nach den begrenzten Regeln oben. Sie bestätigen kein
Kunstwerk und erlauben keine neue Verbindung. Physischer Standby, abgewiesene
Anmeldung, fehlerhafte Protokolldaten und ein geschlossener Transport beenden
die Sitzung weiterhin.

Im Protokoll bedeutet `event sequence incomplete`: Künstlerdaten ausgeblendet,
dieselbe Verbindung wartet — kein bestätigtes Werk.
`event session stopped: reason=...; no reconnect` bedeutet: Sitzung beendet,
keine sofortige automatische Wiederholung. Bei einer Fehlermeldung diesen festen Fehlercode,
App-Version und TV-Modell angeben, keine Zugriffstoken oder rohen TV-Daten.

Eine Sitzung dauert höchstens acht Stunden. Im reinen Ereignismodus
(`current_state_refresh` aus) können Einschlafen, TV-Betrieb oder Fehler sie
früher beenden. Die Opt-in-Ausnahmen und endgültigen Stop-Bedingungen oben gelten weiter. Ein konfigurierter neuer Prozessstart oder späterer frischer HA-Weckwechsel oben kann eine neue Abfrage erlauben; auch ein erfolgreicher ausdrücklicher Versand kann eine Sitzung starten.

Nach einer anfänglichen Abfrage mit lokalem Bildvergleich hört eine einzige Verbindung auf die beobachtete Diashow-Folge: `image_selected`, passendes `auto_rotation_image_changed`, danach Kunstmodus `on`, innerhalb von fünf Sekunden. Bei ausgeschaltetem `current_state_refresh` gibt es innerhalb dieser Sitzung keine wiederholten TV-Abfragen, späteren Vorschaubilder oder Neuverbindungen. Eingeschaltet sind nur die begrenzten Prüfungen oben erlaubt, keine neuen Vorschaubilder oder Verbindungen. Ein Ereignis löst die gespeicherte Upload- oder bildgeprüfte Zuordnung dieses TVs auf; unbekannte IDs leeren den Text.

Der anfängliche Bildnachweis gilt 90 Sekunden. Eine vollständige Diashow-Folge gilt höchstens **15 Minuten**, passend zur getesteten Zehn-Minuten-Diashow. Doppelte IDs, Pongs und Modus-an-Meldungen verlängern nichts. Langsamere Diashows können Lücken zeigen; manuelle Wechsel müssen diese Folge nicht liefern. Die Vorlage kann etwa eine Minute Anzeigeverzögerung hinzufügen.

Bei ausgeschalteter Zustandsaktualisierung oder ohne erfolgreiche neue Prüfung
kann ein fest gewähltes unverändertes Bild nach 90 Sekunden unbestätigt sein.
Der Startfix allein verlängert keinen Bildnachweis und fragt nicht
wiederholt ab, um einen statischen Künstlertext aktuell erscheinen zu lassen.

**Reiner Ereignismodus (`current_state_refresh` aus):** Einschlafen, TV-Betrieb, Verbindungsabbruch, ungültige Ereignisse oder Publikationsfehler beenden/pausieren ohne sofortige Neuverbindung. Bei Opt-in gelten stattdessen die begrenzten Same-Socket-Regeln und endgültigen Stop-Bedingungen oben. Erst nach tatsächlichem Sitzungsende bleibt ohne optionale Weckwechsel-Einstellung ein ausdrücklicher neuer Bildversand im sichtbaren Kunstmodus nötig. Manuelles Aktualisieren verarbeitet nur bereits empfangene Ereignisse. Der Beobachter sendet keine Power-, Wake-on-LAN-, Bildauswahl- oder Modusbefehle. Trotzdem kann bereits die Verbindung Nebenwirkungen haben.

Gespeicherte IDs sind historische Zuordnungen, kein fortlaufender Pixelnachweis. Unbeobachtetes externes Ersetzen/Wiederverwenden einer TV-ID ist während reinen Ereignisempfangs nicht auszuschließen. Ein widersprechender anfänglicher Bildvergleich sperrt die gespeicherte Bildunterschrift. Keine allgemeine Firmware-/Nichtaufweckgarantie (D-235).

Der Sensor ist ein von der App publizierter HA-Zustand, keine registrierte Geräteintegration; nach einem Core-Neustart kann er vorübergehend fehlen. Veraltete/pausierte Daten blenden den Titel aus. Zurück zum Einmalbetrieb: Hintergrundmodus aus, App neu starten und ursprüngliches Einmal-Sende-Script wieder einsetzen. Nicht Verlauf oder Gerätezuordnung löschen, um eine Verbindung zu erzwingen.

</details>
