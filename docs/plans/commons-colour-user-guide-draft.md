# Farbauswahl im kommenden Update

**Noch nicht veröffentlicht.** Diese Anleitung beschreibt den lokalen Entwurf,
nicht die aktuell installierbare Beta 0.1.0b5. Die Erweiterung auf insgesamt
1000 geprüfte Werke ist noch nicht abgeschlossen.

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

Ein optionaler Farb-Helfer kann später dieselbe Auswahl vom Dashboard steuern.
Er ist für die normale Einrichtung nicht nötig. Die App versteht etwa **Blau**,
**Blue** und **color_blue** als denselben Wert. Mehrere Farben in einem Wert
werden nicht als Kombination interpretiert. Ohne Helfer genügt das einzelne
Farbfeld in der Konfiguration.

## Stand der Prüfung

Alle 400 Bestandswerke besitzen lokal Farbprofile mit festem Bezug zur Quelldatei. Die
[private Farb-Vorschau](http://127.0.0.1:8881/gallery.html) zeigt den vorläufigen
Abgleich. Labels und Schwelle wurden an 48 visuell gesichteten Werken kalibriert;
die restliche Kuratierung und die native Releaseprüfung bleiben offen.
Diese Seite wird erst nach der Freigabe in die öffentliche Installationsanleitung
übernommen. Die veröffentlichte Anleitung bleibt bis dahin bei den Funktionen
der tatsächlich verfügbaren Beta.
