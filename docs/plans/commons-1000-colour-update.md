# Commons Update mit 1000 Werken und Farbauswahl

Stand: 10. Oktober 2026. Arbeitsumfang für das Wochenende am 10. und 11. Oktober 2026, beauftragt von Alexander. Ziel sind 1000 nutzbare Commons-Werke insgesamt und ein einfaches Farbfeld in der App. Die Farbdaten sollen spätere Kombinationen wie Blau und Gelb ermöglichen, ohne sie bereits in diesem Update in die Oberfläche aufzunehmen.

## Ausgangspunkt und Fortschritt

Die veröffentlichte Beta 0.1.0b5 enthält 400 Werke. Der lokale Auswahlbeleg wurde geprüft: 400 Datensätze, 400 eindeutige Commons-IDs, 299 Künstlerbezeichnungen, keine doppelten Upload-Hashes und mindestens 3000 Pixel Quellbreite. Kein Eintrag im Auswahlbeleg enthält bisher ein Farbprofil. Die vorhandene App-Konfiguration bietet bei `color` nur `any` an.

Der Bestand ist `frame_gallery/research/commons-400-selection-2026-10-06.json`. Er enthält außerdem 26 visuell geprüfte Reserve-IDs. Reserven zählen erst nach erneuter Prüfung und vollständiger Aufnahme als neue Werke. Frühere zurückgestellte Fälle bleiben zurückgestellt, solange ihre Gründe nicht geklärt sind.

- [x] Auftrag und Ergänzung zu den drei wichtigsten Farben aufgenommen.
- [x] Bestandszahlen und fehlende Farbdaten lokal geprüft.
- [x] Aktuelle offizielle Dokumentation zu Vorschaubildern und Bildpaletten gelesen.
- [x] Produktumfang, Reihenfolge und Abnahmekriterien festgehalten.
- [x] Vollständige Repository-Pflichtlektüre und anschließender technischer Änderungsentwurf.
- [x] Farbprofil-Pilot mit visuellem Abgleich.
- [ ] 600 zusätzliche Werke recherchiert und geprüft.
- [ ] Farbprofile und lokale Vorschau für alle 1000 Werke vollständig.
- [x] Farbauswahl lokal am 400-Werke-Bestand umgesetzt und getestet.
- [ ] Dokumentation und Releasekandidat geprüft.
- [ ] Veröffentlichung gesondert freigegeben und abgeschlossen.
- [ ] Green-Update und TV-Test gesondert freigegeben und durchgeführt.

Der lokale App-Entwurf enthält inzwischen das einzelne Farbfeld und den geprüften Farbfilter. Der Runtime-Katalog bleibt bei 400 Werken; die veröffentlichte Beta ist unverändert. Ein Wochenendziel ist keine garantierte Fertigstellung: Rechte, Bildqualität und bestandene Prüfungen haben Vorrang vor der Zahl und dem Termin.

Lokaler Zwischenstand: 48 Bestandswerke visuell im Farbpilot geprüft und das Verfahren an dunklem Blau und Ockertönen korrigiert. Alle 400 Bestandswerke besitzen vorläufige Farbprofile mit vollständiger Verteilung und Quellenbeleg. Hinzu kommen **346 derzeit lokal kuratierte neue Werke**, ebenfalls mit vollständigen Farbprofilen. Die private [Farbvorschau](http://127.0.0.1:8881/gallery.html) enthält somit **746 Werke** und lässt sich nach Farbgruppe sowie Bestand oder Neuzugängen filtern. **254 weitere Aufnahmen fehlen noch zum nominellen Ziel.** Die [neue Farbanleitung](commons-colour-user-guide-draft.md) bleibt ein unveröffentlichter Entwurf.

Der jüngste feste Metadaten-Prüfstand enthält 14150 zusätzliche Kandidaten
mit Quellen-/Rechtemetadaten; nach der quellengebundenen Self-CC0/PD-self-Prüfung bestehen
6656 die automatische Vorprüfung. Neue Fraktalkunst-Kandidaten werden getrennt
weiter geprüft. Alle 3446 Vorschauen wurden tatsächlich gesichtet, 2622 dabei zunächst
zurückgestellt. 66 Kontaktbögen wurden ein zweites Mal
gesichtet. Zusätzliche Maßangaben im Klartext haben mögliche Ausschnitte sichtbar
gemacht: Die frühere provisorische 127er-Auswahl wurde entsprechend reduziert
und durch weitere tatsächlich geprüfte Werke ergänzt. Der aktuelle Stand ist
346 Aufnahmen, nicht die frühere provisorische Auswahl. 47 ausgewählte Fälle
bleiben zurückgestellt, darunter
Duplikate und widersprüchliche Originalmaße. 347 Werk-Identitäten aus den
Metadaten des Bestands ergänzen die Titel- und Bildvergleiche. Weitere kleine
Vorschauen werden gesammelt; der 400er-Bestand bleibt unverändert.
Einzelne Netzwerk-Ausfälle bleiben separat zurückgestellt und zählen nicht mit.
Prüfstand und Aufnahmebelege sind lokal gesichert; keine Kandidatenzahl ersetzt
600 echte Aufnahmeentscheidungen oder die spätere Releaseprüfung.

Eine ergänzende Bestandsprüfung hat alle 400 Quellenrevisionen und Upload-Pins
abgeglichen. 239 enthalten auswertbare Originalmaßangaben; 60 erzeugten
Prüffragen zu Maßumfang oder Proportionen. Vier sind nach tatsächlicher
Quellen- und Bildsichtung geklärt, 56 bleiben offen. Drei betreffen ausdrücklich
separate Rahmenmaße; Whistlers „Chelsea Shops“ liegt mit den belegten Werkmaßen
exakt auf der erlaubten 2,5-Prozent-Grenze und wurde nur wegen Fließkomma-Rundung
markiert. Das sind keine 56 bestätigten Ausschnitte. Die offenen Fälle müssen vor der abschließenden Behauptung „1000 nutzbare
Werke“ geklärt sein. Die vorhandenen Einträge und der Verlauf bleiben unverändert;
es gibt weder automatische Entfernung noch heimliche Ersatz-Pins. Der Beleg
liegt in `research/commons-baseline-format-audit-2026-10-09.json`.

Die letzte zweite Sichtung hat 56 Werke hinzugefügt. Die erweiterte Prüfung von
Zoll-Brüchen, mehrfach angegebenen Einheiten und H/B-Maßen hat zugleich drei
frühere Neuzugänge zurückgestellt. Quellen, Farbprofile und Vorschau wurden
entsprechend neu abgeglichen. Fotografennamen werden nicht als Künstlernamen
übernommen; ungeklärte Zuschreibungen, Bildfragmente und Rahmen bleiben draußen.

Die anschließende Sichtung hat zehn Werke aufgenommen. Eine Korrektur im
Recherchewerkzeug verhindert, dass die Tiefe eines dreidimensionalen Rahmens
als Bildhöhe gelesen wird; dadurch sind zwei zuvor zurückgestellte Neuzugänge
wieder geklärt. Bei Franz Bunke belegt das ausdrückliche Künstlerfeld der
Quelle den Namen, getrennt vom Fotografen. Nach erneuter Bildsichtung ist auch
dieser Fall aufgenommen. Rechte- und Maßgrenzen bleiben unverändert. Weitere
Vorschauen werden in begrenzten Chargen gesammelt; direkte Kunstwerk-Belege
haben Vorrang vor Archivmaterial. Engere Suchfenster oberhalb von 20000 Pixeln
erschließen hochaufgelöste Quellen, ohne Originalbilder herunterzuladen.

Eine weitere zweite Sichtung hat 17 unterschiedliche Werke aufgenommen. Ein
zusätzlicher Lenore-Scan bleibt nach dem erneuten Bildvergleich zurückgestellt.
Explizite Detail-Aufnahmen, ungeklärte Altartafel-Teile und Fotografennamen als
Künstler werden nicht mitgezählt. Alle 2845 Vorschauen haben inzwischen
Sichtungs- und Bildvergleichsbelege; die erneuerte Vorschau zeigt 319 Neuzugänge.

Die neueste Sichtung hat sechs weitere Werke aufgenommen. Eine zusätzliche
Maßprüfung berücksichtigt jetzt auch nachfolgende Zeilen mit Bild-, Blatt- oder
Rahmenmaßen. Ein zuvor gezählter Guigou bleibt deshalb mit widersprüchlichen
Proportionen zurückgestellt. Drei damals zusätzlich erkannte Bestandsfragen
sind inzwischen durch die unten beschriebenen getrennten Rahmenmaße geklärt.

Bei Guardis „Erminia und die Hirten“, Bards „John Birkbeck“ und Boudins
„On the Beach, Trouville“ trennt die Quelle ausdrücklich Werk- und Rahmenmaße.
Die Werkmaße passen zum Zielbereich und zur tatsächlich gesichteten ungerahmten
Reproduktion. Diese drei Entscheidungen sind an Quellenrevision, Upload- und
Vorschau-Hash gebunden; die ursprünglichen Prüffragen und alle Maßangaben bleiben
im Audit sichtbar. Eine allgemeine automatische Ausnahme für Rahmen gibt es nicht.

Die folgende Sichtung hat 17 weitere vollständige Werke ausgewählt, darunter
Dürers Holzschnitt, historische Landschaftsgrafik und einen vollständigen
dekorativen Bildteppich. Die erweiterte Quellenprüfung behält englische H/W-Maße,
einzelne beschriftete Size-Achsen und Dezimalkommas bei. Dadurch bleibt ein zuvor
gezählter Heusden-Scan mit abweichenden Originalmaßen zurückgestellt; netto sind
335 Neuzugänge enthalten. Ein breites Triptychon und ein Eisen-Druck bleiben
trotz passender Datei-Proportionen wegen ihrer Originalmaßangaben ungeklärt.

Die Recherche verwendet für zusätzliche Medien und zeitgenössische Kunst
getrennte Suchbegriffe. [CirrusSearch unterstützt keine Klammergruppen und warnt
vor ODER in Kombination mit speziellen Suchfeldern](https://www.mediawiki.org/wiki/Help:CirrusSearch/Logical_operators).
Die älteren gruppierten Suchläufe bleiben als Belege erhalten, gelten aber nicht
als vollständige Abdeckung dieser Werkarten. Eine leere oder irrelevante
Trefferliste belegt daher nicht, dass es keine geeigneten Werke gibt.

Die anschließende Sichtung hat elf Werke aufgenommen, darunter eine eigene
digitale Fotomontage und eine abstrakte Wasser-/Lichtaufnahme von W.carter,
CEKeechs Blumenstillleben, ein zeitgenössisches Gemälde von Mironov und fünf
vollständige historische Grafiken. Ein begrenzter Fraktalkunst-Suchlauf hat 472
ungeprüfte Kandidaten geliefert; diese zählen erst nach tatsächlicher Sichtung
und Quellenprüfung. Explizite PD-self-Erklärungen werden anhand der offiziellen
Vorlagen- und Dokumentationsrevision erkannt, nicht aus bloßen Lizenznamen
abgeleitet. Die private Vorschau wurde mit 746 Einträgen im Browser geprüft.

## Umfang dieses Updates

### 1000 tatsächlich unterschiedliche Werke

Die bestehenden 400 Werke bleiben mit ihren IDs und Upload-Pins erhalten. Hinzu kommen 600 unterschiedliche Werke, nicht 600 alternative Scans oder Ausschnitte bestehender Bilder. Der gespeicherte Verlauf bleibt kompatibel; ein Update macht gesendete Bilder nicht erneut auswählbar.

Für neue Werke gelten die bisherigen Grenzen: JPEG, mindestens 3000 Pixel breit, maximal 2,5 Prozent relative Abweichung von 16:9, geeignete vollständige Reproduktion und nachvollziehbare Rechte innerhalb der bestehenden Auswahlregeln. Farbigkeit, modernere Wirkung und eine breite Auswahl bleiben kuratorische Prioritäten. Die Sammlung wird nicht mit dunklen Wiederholungen eines einzigen Motivs oder ungeeigneten Bildern aufgefüllt, nur um 1000 zu erreichen.

Jedes neue Werk erhält eine überprüfbare Quellenreferenz, Künstler und Titel soweit belegbar, Abmessungen, Upload-Identität und dokumentierte visuelle Entscheidung. Rahmen, Papierumrandungen, schlechte Reproduktionen, fotografierte Ausstellungsansichten, Details und bereits bekannte Werkduplikate werden geprüft und gegebenenfalls zurückgestellt. Gleiche Upload-Hashes zu erkennen reicht nicht aus, um verschiedene Scans desselben Werks auszuschließen.

Die strengere App-Präferenz für ungefähr 1 Prozent Abweichung bleibt unverändert. `contain` und der bekannte Querformat-Fallback bleiben erhalten. Auch ein geeignetes Werk kann kleine Ränder haben; dieses Update verspricht weder Randfreiheit noch native 4K-Details für jede Quelle.

### Breite künstlerische Auswahl

Alexanders Ergänzung vom 10. Oktober öffnet die Recherche auch für Illustration,
Grafik, Fotokunst und digitale Werke. Entscheidend sind künstlerischer Anspruch,
erkennbare Werk- oder Künstlerbekanntheit und eine abwechslungsreiche Auswahl;
reines Archivmaterial zählt nicht als Füllmaterial. Zeitgenössische Künstlerinnen
wie Yayoi Kusama sind ausdrücklich als Recherchewunsch aufgenommen, nicht als
bereits verfügbare oder rechtegeklärte Katalogeinträge.

Die bestehenden PD/CC0-Aufnahmeregeln und Formatgrenzen bleiben bestehen.
Bei fotografierten Kunstwerken müssen die Rechte am abgebildeten Werk und an
der Aufnahme getrennt geprüft werden. Eine freie Fotolizenz ist nicht automatisch
eine Freigabe des Kunstwerks ([Commons-Richtlinie zu abgeleiteten Werken](https://commons.wikimedia.org/wiki/Commons:Derivative_works)).
Eine Erweiterung auf andere Lizenzen wäre eine eigene technische und rechtliche
Entscheidung, keine stillschweigende Änderung dieses Updates.

### Ein Farbfeld für den Nutzer

Für Commons kommt ein Feld **Farbwunsch** in die einfache Konfiguration, direkt bei der Bildquelle. Standard ist **Alle Farben**. Der Nutzer wählt zunächst genau eine Farbgruppe, ohne HEX-Eingabe, Prozentregler, mehrere Hilfsentitäten oder neue Dashboard-Erweiterung.

Als Startvokabular werden Rot, Orange, Gelb, Grün, Blau, Violett, Rosa, Braun, Beige, Grau, Schwarz und Weiß geprüft. Die Begriffe müssen in der deutschen und englischen Anleitung verständlich sein. Die endgültige Liste und Grenzfälle werden am Pilotbestand geprüft; Farbnamen dürfen nicht lediglich drei sehr ähnliche Töne desselben Bildes beschreiben.

Ein blaues Bild muss einen bedeutsamen Blauanteil besitzen. Ein einzelner blauer Pixel ist kein Treffer. Umgekehrt muss Blau nicht immer die größte Fläche belegen: Ein Werk mit deutlich sichtbarem Blau neben Gelb und Weiß soll bei Blau auffindbar sein. Diese Bedeutung gehört in die Feldbeschreibung.

Farbe gilt in diesem Update ausschließlich für den kuratierten Commons-Katalog. Andere Quellen bleiben bei ihrem bisherigen Verhalten; ein dort nicht unterstützter Farbwunsch wird ausdrücklich als nicht angewendet gemeldet. Gespeicherte Optionen, vorhandene Karten, Quellen und der Standardbetrieb ohne Farbwunsch bleiben kompatibel. Bestehende optionale Farb-Helfer werden bei der technischen Umsetzung auf dieselben angebotenen Einzelwerte geprüft, ohne für den normalen Nutzer erforderlich zu werden.

### Saubere Daten für spätere Kombinationen

Pro Werk werden bis zu drei bedeutsame, voneinander verschiedene Farbgruppen festgehalten. Ein monochromes Bild erhält keine erfundenen zweite und dritte Farbe. Zu jeder Gruppe gehören ihr Anteil am analysierten Bild und ein repräsentativer Farbwert. Neutralfarben werden nicht einfach entfernt oder zu bunten Farben umbenannt.

Zusätzlich bleibt die vollständige Verteilung über die angebotenen Farbgruppen erhalten. So gehen Informationen außerhalb der drei wichtigsten Gruppen nicht verloren, wenn später Kombinationen oder andere Gewichtungen hinzukommen. Die Daten unterscheiden Rohmessung, daraus abgeleitete Suchfarben und manuell überprüfte Grenzfälle. Eine eventuelle manuelle Korrektur erhält einen Grund und ersetzt die ursprüngliche Messung nicht stillschweigend.

Die Analyse wird an die genaue Quellversion gebunden: Commons-ID, gepinnter Upload-Hash, tatsächlich analysierte Vorschau und deren Hash/Abmessungen, Analysezeitpunkt und Methodenversion. Ändert sich die Quelle, gelten die alten Farbdaten nicht automatisch für die neue Fassung. Das bereits vorhandene Überspringen geänderter Uploads bleibt bestehen.

Analysiert wird das Werk in seiner unverzerrten Vorschau, nicht ein Dashboard-Screenshot oder das vorbereitete TV-Bild mit zusätzlich erzeugten schwarzen Rändern. Reale dunkle Bildflächen bleiben Teil des Kunstwerks. Vorhandene Scanumrandungen werden beim Review erkannt; eine automatische Randkorrektur darf echte schwarze Kompositionsflächen nicht entfernen.

Diese Daten ermöglichen später beispielsweise Blau **und** Gelb mit jeweils relevantem Flächenanteil. Mehrfachauswahl, Kombinationen, Farbstimmungsregler und Rangfolgen für Kombinationen gehören ausdrücklich nicht zur ersten Oberfläche.

## Arbeitspakete

| Paket | Ergebnis | Fertig wenn |
| --- | --- | --- |
| 1 Farbpilot | Rund 40 bis 60 vielfältige Bestandswerke mit Messung und visueller Prüfung | Bunte Geometrie, gedeckte Landschaften, Stillleben und monochrome Werke nachvollziehbar zugeordnet sind; relevante Akzente, Neutralfarben und Randfälle geprüft sind |
| 2 Sammlung erweitern | 600 zusätzliche, brauchbare Werke und nachvollziehbare Reserven | Identitäten, Formate, Seitenverhältnisse, Rechtehinweise und tatsächliche Vorschauen geprüft sind; keine ungeklärten Fälle als akzeptiert gezählt werden |
| 3 Profile und Vorschau | Alle 1000 Werke mit reproduzierbaren Farbdaten | Farbgruppen, Anteile, Quelldaten und Prüfstatus vollständig sind; scrollbare lokale Vorschau Einzelgruppen und Blau-Gelb-Beispiele nachvollziehbar zeigt |
| 4 App und Anleitung | Ein einfaches Farbfeld und kompatible Auswahl | Farbwahl, Verlauf, begrenzte Auswahl, sauberes Ende und bisherige Quellen zusammen funktionieren; Anleitung die Grenzen verständlich erklärt |
| 5 Releaseprüfung | Geprüfter Kandidat mit passenden ARM- und Intel-Images | Lokale und anschließend freigegebene native Prüfungen bestehen, Quellen und Releasebelege passen; Veröffentlichung erst nach Freigabe erfolgt |

Der Farbpilot kommt vor der Analyse aller 1000 Werke. Korrekturen an Farbgruppen und Schwellwerten sollen nicht erst nach einem vollständigen Durchlauf entdeckt werden. Die Recherche kann danach chargenweise erfolgen; akzeptierte, zurückgestellte und noch ungeprüfte Werke bleiben getrennt und der Fortschritt wird nach tatsächlichen Entscheidungen gezählt.

Die exakte Methode, Messauflösung und Bedeutungsschwelle werden nach Pflichtlektüre und Pilotvergleich im technischen Änderungsentwurf festgelegt. Ein fertiges, fachlich geprüftes Farbverfahren ist mit diesem Produktplan noch nicht behauptet.

## Auswahl und Fehlerverhalten

Die App soll zuerst aus den bereits bekannten passenden Farbkandidaten wählen. Ein Farbfilter darf nicht dadurch entstehen, dass der Green wahllos hochauflösende Bilder herunterlädt, ihre Farben ausprobiert und verwirft. Farbprofile werden bei der Vorbereitung auf dem Mac berechnet; auf dem Green werden nur kleine Katalogdaten benötigt. Es wird kein weiterer Cloud-Dienst zur Bildanalyse eingeführt.

Die Farbauswahl muss mit den bisherigen Ausschlüssen für gesendete, hochgeladene oder vorübergehend quarantänisierte Werke zusammenspielen. Die 16:9-Präferenz darf nur das Format lockern, nicht den gewählten Farbwunsch. Wenn kein neues passendes Werk verfügbar ist, endet der Lauf sauber mit verständlichem Hinweis; TV, Vorschau und Werkdaten bleiben unverändert.

Es bleibt bei endlichen Anfrage-, Download- und Zeitgrenzen. Der vorhandene normale Commons-Anfrageumfang wird nicht auf eine Vollsuche über 1000 Werke ausgeweitet. Wenn innerhalb des begrenzten Laufs kein verifizierbarer Treffer verfügbar ist, ist dies von sicher festgestellter Katalogerschöpfung zu unterscheiden. Netzwerkprobleme oder vorübergehende Unsicherheit dürfen nicht als dauerhaft erschöpfter Farbkatalog gespeichert werden.

## Abnahme

- Insgesamt 1000 akzeptierte Werkidentitäten; die 400 Bestandsidentitäten und Pins sind unverändert erhalten. Ein nachweislich ungeeigneter Bestandsfall wird separat dokumentiert und nicht heimlich umgepinnt.
- Alle 1000 akzeptierten Werke haben vollständige, versionsgebundene Farbprofile und geprüfte Vorschauen; unbekannte Farben werden nicht als fertige Analyse gezählt.
- Top-Farben sind Farbgruppen, nicht drei fast identische RGB-Werte. Anteile bleiben plausibel und nachvollziehbar; Monochrombilder, große Neutralflächen und bunte Akzente sind gezielt geprüft.
- Die lokale Vorschau zeigt Trefferzahlen pro Farbe sowie ungesicherte Fälle getrennt. Sie ermöglicht einen visuellen Kontrolllauf und Beispiele für spätere Farbkombinationen.
- **Alle Farben** bleibt Standard. Jede angebotene Farbe hat einen realen, überprüften Trefferbestand; die Dokumentation behauptet keine gleichmäßige Verteilung ohne Zählung.
- Ein Einzel-Farbwunsch wird nachvollziehbar eingehalten, gemeinsam mit Verlauf und Bildformat. Ein No-Match sendet kein Ersatzbild anderer Farbe und lässt den bisherigen Zustand korrekt stehen.
- Alle Farben ohne zusätzlichen Helfer, optionale Helferwerte, fehlende Profile, ungültige Werte, ausgeschöpfte Farbauswahl, Quelländerungen, Netzwerkfehler und Format-Fallback erhalten Tests.
- Temporäre Dateien werden weiterhin nach Erfolg und Fehler entfernt. Ein größerer Katalog erzeugt weder auf dem Green noch im Release eine Sammlung von 1000 Bilddateien.
- Bestehende vollständige Qualitätsprüfungen bleiben erhalten; keine Abschwächung von Sicherheits-, Rechte-, Test- oder Zeitgrenzen, um den Termin zu halten.
- Anleitung, Konfigurationshinweise, Info-Ansicht und Releasebeschreibung stimmen bei Werkzahl und Farbumfang überein. Nutzer müssen keine alten Karten oder Historie löschen.

## Selbständigkeit und Freigaben

Der aktuelle Auftrag umfasst Planung, Recherche und lokale Arbeit für diesen Umfang einschließlich Vorschau-Analyse. Private, begrenzte Vorschaudateien dürfen für diese ausdrücklich angeforderte Arbeit gesammelt werden; keine Vollauflösungs-Mirror-Sammlung und keine Aufnahme von Bilddateien in Runtime oder Release. Alte Recherche und fremde/unabhängige Änderungen bleiben erhalten. Im ersten Schritt werden keine Zugangsdaten benötigt.

Vor Architekturänderungen und Code gilt weiterhin die vollständige Repository-Pflichtlektüre. Materiale Entscheidungen und tatsächlich durchgeführte Prüfungen werden anschließend in den vorgesehenen Projektdokumenten ergänzt. Innerhalb dieses Auftrags sollen gewöhnliche Recherchechargen und lokale Tests keine neuen Einzel-Freigaben auslösen.

Publikation, Container-/Registryzugriff, Rechteerweiterung eines GitHub-Tokens sowie Green-Installation und TV-Senden bleiben die vorhandenen separaten Freigabeschritte. Persönliche Zugangsdaten werden erst zu ihrem notwendigen Schritt geladen, zeitlich begrenzt in Speicher gehalten und weder in Dateien noch in Logs gespeichert. Es gibt keine Änderung an `configuration.yaml`.

Nicht enthalten: IP-Detect, zusätzliche Bildanbieter, Farbfilter für andere Museen, mehrere Farbfelder im UI, Bildvorschlagsrecht, TV-Speicherverwaltung oder ein stabiler Release statt Beta.

## Offizielle Grundlagen

Die [MediaWiki Imageinfo-Dokumentation](https://www.mediawiki.org/wiki/API:Imageinfo) beschreibt Vorschaurenditionen, Quellabmessungen und Upload-Hashes. Eine angeforderte Vorschaubreite ist nicht zwingend die tatsächlich gelieferte Breite; diese muss geprüft und dokumentiert werden. Bestehende Beschränkungen für Bytezahl, Pixelzahl und erlaubte Hosts bleiben deshalb relevant.

Die [Wikimedia User-Agent-Richtlinie](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy) bleibt Grundlage für identifizierbare, schonende Rechercheanfragen mit dem bereits vorgesehenen Projektkontakt `volkue+commonsapi@gmail.com`.

Die vorhandene Bildbibliothek dokumentiert [Palettenbildung in Pillow](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.quantize). Diese liefert nicht automatisch verständliche Farbnamen oder brauchbare Suchkategorien; deren Qualität muss am Pilot und den geprüften Vorschauen nachgewiesen werden. Neue Abhängigkeiten sind durch diesen Plan nicht vorausgewählt.
