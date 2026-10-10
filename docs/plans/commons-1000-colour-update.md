# Commons Update mit 1000 Werken und Farbauswahl

Stand: 10. Oktober 2026. Arbeitsumfang für das Wochenende am 10. und 11. Oktober 2026, beauftragt von Alexander. Ziel sind 1000 nutzbare Commons-Werke insgesamt und ein einfaches Farbfeld in der App. Die Farbdaten sollen spätere Kombinationen wie Blau und Gelb ermöglichen, ohne sie bereits in diesem Update in die Oberfläche aufzunehmen.

## Ausgangspunkt und Fortschritt

**Aktueller Abschlussstand der lokalen Auswahl (10. Oktober):** Mit Alexanders
ausdrücklicher Freigabe sind die 56 ungeklärten Bestandsfälle vorläufig aus der
zukünftigen Zufallsauswahl genommen und ersetzt. Der lokale Runtime-Katalog
enthält genau **1000 aktive Werke: 344 Bestand + 656 Neuzugänge**. Sieben weitere
geprüfte Neuzugänge bleiben Reserve. Alle 1063 ursprünglichen Rechercheprofile,
400 Bestandsidentitäten und Quellenbelege bleiben erhalten; kein Sendeverlauf
wird zurückgesetzt. Die Vorschau zeigt aktive Werke, zurückgestellte Fälle und
Reserven getrennt. Die Bestandsfragen gelten nicht plötzlich als bewiesener Crop.

Die zusätzliche Scope-Freigabe umfasst die **vollständige native Dashboardkarte
mit optionalem Farbwähler** und eine Prüfung weiterer Selektoren anhand der
vorhandenen Daten. Beides steht in der [neuen Anleitung](commons-colour-user-guide-draft.md).
Die Karte kennzeichnet Farbe als Commons-only, benötigt keine Dashboard-Erweiterung
und verwendet das vorhandene Script und den Timer. Die anderen Bildquellen
bleiben erhalten; inkompatible Filter werden ausdrücklich als ignoriert gemeldet.
Eine künftige Karten-Quellenauswahl müsste die irrelevanten Selektoren ausblenden.
Künstler und spätere Farbkombinationen sind die stärksten nächsten Kandidaten;
Epoche, Motiv und Sammlung brauchen zunächst vollständigere Metadaten.

Die folgenden Zwischenstände dokumentieren die **Recherchehistorie vor dieser
Freigabe**, nicht den aktuellen Runtime-Umfang. Die öffentliche Beta b5 bleibt
bei 400 Werken; native Veröffentlichung und Green-/TV-Test brauchen separate Freigaben.

**Freigabe vom 10. Oktober:** Zusätzlich dürfen CC BY und CC BY-SA recherchiert
werden. Urheber, Titel, Quelle, genaue Lizenz samt Link und Versionsnummer sowie
Hinweise zu Änderungen werden getrennt gesammelt. Rechte am Kunstwerk selbst
müssen geklärt sein; eine freie Ausstellungsfotografie allein genügt nicht.
Für eine spätere Aufnahme in die App braucht es eine verlässlich zugängliche
Pflicht-Attribution, nicht nur die bisher optionale Künstlerkarte. Die
veröffentlichte Version und ihre PD/CC0-Rechteprüfung bleiben unverändert.

Die veröffentlichte Beta 0.1.0b5 enthält 400 Werke. Der lokale Auswahlbeleg wurde geprüft: 400 Datensätze, 400 eindeutige Commons-IDs, 299 Künstlerbezeichnungen, keine doppelten Upload-Hashes und mindestens 3000 Pixel Quellbreite. Kein Eintrag im Auswahlbeleg enthält bisher ein Farbprofil. Die vorhandene App-Konfiguration bietet bei `color` nur `any` an.

Der Bestand ist `frame_gallery/research/commons-400-selection-2026-10-06.json`. Er enthält außerdem 26 visuell geprüfte Reserve-IDs. Reserven zählen erst nach erneuter Prüfung und vollständiger Aufnahme als neue Werke. Frühere zurückgestellte Fälle bleiben zurückgestellt, solange ihre Gründe nicht geklärt sind.

- [x] Auftrag und Ergänzung zu den drei wichtigsten Farben aufgenommen.
- [x] Bestandszahlen und fehlende Farbdaten lokal geprüft.
- [x] Aktuelle offizielle Dokumentation zu Vorschaubildern und Bildpaletten gelesen.
- [x] Produktumfang, Reihenfolge und Abnahmekriterien festgehalten.
- [x] Vollständige Repository-Pflichtlektüre und anschließender technischer Änderungsentwurf.
- [x] Farbprofil-Pilot mit visuellem Abgleich.
- [x] Mindestens 600 zusätzliche Werke recherchiert und geprüft.
- [x] Farbprofile und lokale Vorschau für alle 1000 Werke vollständig.
- [x] Farbauswahl lokal umgesetzt; auf 1000 Werke erweitert.
- [x] Vollständige optionale Dashboardkarte mit Farbwähler dokumentiert.
- [x] Weitere mögliche Selektoren und Grenzen nach tatsächlicher Datenlage bewertet.
- [x] Lokale Dokumentation, Katalog und Farbauswahl geprüft (5.027 Tests,
  105 Recherchetests; 100 % Line-/Branch-Coverage).
- [ ] Native Release-Images nach gesonderter Freigabe prüfen.
- [ ] Veröffentlichung gesondert freigegeben und abgeschlossen.
- [ ] Green-Update und TV-Test gesondert freigegeben und durchgeführt.

Der lokale App-Entwurf enthält inzwischen das einzelne Farbfeld und den geprüften Farbfilter. Der Runtime-Katalog bleibt bei 400 Werken; die veröffentlichte Beta ist unverändert. Ein Wochenendziel ist keine garantierte Fertigstellung: Rechte, Bildqualität und bestandene Prüfungen haben Vorrang vor der Zahl und dem Termin.

Lokaler Zwischenstand: 48 Bestandswerke visuell im Farbpilot geprüft und das Verfahren an dunklem Blau und Ockertönen korrigiert. Alle 400 Bestandswerke besitzen vorläufige Farbprofile mit vollständiger Verteilung und Quellenbeleg. Hinzu kommen **663 derzeit lokal kuratierte neue Werke**, ebenfalls mit vollständigen Farbprofilen. Die private [Farbvorschau](http://127.0.0.1:8881/gallery.html) enthält somit **1063 nominelle Einträge** und lässt sich nach Farbgruppe sowie Bestand oder Neuzugängen filtern. Ohne die 56 ungeklärten Bestandsfälle mitzuzählen sind es **1007**: Die Zusatzrecherche reicht zahlenmäßig aus, ohne diese offenen Fälle vorauszusetzen. Eine Zurückstellung dieser Bestandsfälle ist noch nicht freigegeben; endgültige Auswahl und Runtime-Export bleiben offen. Die [neue Farbanleitung](commons-colour-user-guide-draft.md) bleibt ein unveröffentlichter Entwurf.

Der jüngste abgeschlossene Metadaten-Prüfstand enthält 18662 zusätzliche Kandidaten
mit Quellen-/Rechtemetadaten; nach der quellengebundenen Self-CC0/PD-self-Prüfung bestehen
8092 die automatische Vorprüfung. Die Fraktalkunst-Treffer haben gesonderte
CC-Lizenzen und werden seit der gesonderten Freigabe getrennt geprüft; sie zählen
noch nicht als Aufnahmen. Neue Künstler-Kandidaten
werden weiter geprüft. Alle 5432 Vorschauen des festen Sichtungsstands wurden tatsächlich gesichtet, 4172 dabei zunächst
zurückgestellt. 123 Kontaktbögen wurden ein zweites Mal
gesichtet. Zusätzliche Maßangaben im Klartext haben mögliche Ausschnitte sichtbar
gemacht: Die frühere provisorische 127er-Auswahl wurde entsprechend reduziert
und durch weitere tatsächlich geprüfte Werke ergänzt. Der aktuelle Stand ist
663 Aufnahmen, nicht die frühere provisorische Auswahl. 58 ausgewählte Fälle
bleiben zurückgestellt, darunter
Duplikate und widersprüchliche Originalmaße. 307 konkret zugeordnete Werk-Identitäten aus den
Metadaten des Bestands ergänzen die Titel- und Bildvergleiche. Weitere kleine
Vorschauen werden gesammelt; der 400er-Bestand bleibt unverändert.
Einzelne Netzwerk-Ausfälle bleiben separat zurückgestellt und zählen nicht mit.
Prüfstand und Aufnahmebelege sind lokal gesichert; keine Kandidatenzahl ersetzt
600 echte Aufnahmeentscheidungen oder die spätere Releaseprüfung.

Die letzten Zweitsichtungen ergänzen 48 und 23 eigenständige CC0-Fotokompositionen.
Ähnliche I-Träger- und Wolkenvarianten sowie schwächere Dokumentationsmotive
bleiben ungezählt. Fokus-Stacking und verlinkte Ausschnitt-Alternativen werden
in den Quellenbelegen ausdrücklich beschrieben; ausgewählt ist jeweils nur die
geprüfte Originalkomposition. Die aktuelle Browserprüfung bestätigt 663 Neuzugänge
und 290 blaue Neuzugänge; die Filter sind danach auf die ganze Sammlung gesetzt.
Bestandsdatei, veröffentlichte App und Sendeverlauf bleiben unverändert.

Die genehmigte CC-Recherche hat daneben 90 kleine Vorschauen tatsächlich gesichtet
und vollständige Lizenz-/Quellenangaben gesichert. 21 interessante Motive sind
in einer [separaten Recherchevorschau](http://127.0.0.1:8881/cc-gallery.html)
mit Urheber, Lizenzlink und mitgelieferten Hinweisen sichtbar. Sie zählen noch
nicht als Aufnahmen. Rechte am vollständigen Werk, doppelte Varianten, konkrete
Assets und eine verlässlich erreichbare Namensnennung in der späteren App müssen
abschließend geklärt werden. Die optionale Künstlerkarte allein genügt dafür nicht.

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

Auf Alexanders Wunsch sind [zehn gemischte Stichproben](http://127.0.0.1:8881/legacy-samples.html)
mit Vorschaubild, Dateimaßen, angegebenen Werkmaßen und Quellenlink vorbereitet.
Alle zehn Bilder wurden im Browser als geladen geprüft. Die Abweichung bezieht
sich auf das Werkmaß-Verhältnis gegenüber 16:9, nicht auf eine behauptete Menge
abgeschnittener Bildfläche. Der Vorschlag zur Zurückstellung ist ausdrücklich
noch keine Auswahländerung; während Alexander entscheidet, werden zusätzliche
Reserven unabhängig davon recherchiert. Bestandsdatei und Sendeverlauf bleiben
unangetastet.

Alexander hat die zehn Stichproben manuell angesehen und die schwarzen Ränder
als zu breit beurteilt. Die Vorschau verwendet deshalb jetzt responsive,
exakte 16:9-Bildfelder statt fester Höhen; die früher angezeigte Seite und ihr
Beleg bleiben hashgebunden erhalten. Kein Bild wurde beschnitten oder ersetzt.
Alle zehn Felder und geladenen Bilder wurden im Browser geprüft. Die explizite
Freigabe zur vorläufigen Zurückstellung der 56 Fälle ist weiterhin offen;
Vorschau-Ränder und widersprüchliche Werkmaße sind getrennte Beobachtungen.

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

Unter dem breiteren Kunstbegriff wurden vier frühere Reserven tatsächlich neu
gesichtet und aufgenommen: McArdles eigenständige 1901er-Fassung von „The Battle
of San Jacinto“, Carraccis „The Lamentation“, Stanfields „The Battle of Trafalgar“
und Shen Zhous „Branch of Fruit Bearing Tree“. Künstler-IDs in eingebetteten
Creator-Vorlagen zählen nicht mehr als Werk-Identitäten; die ursprünglichen
Quellen bleiben unverändert. Die Farbprofile wurden auf 750 Einträge aktualisiert.

Die folgende echte Zweitsichtung hat sechs weitere vollständige Werke geprüft.
Ein genauerer Lizenzabgleich hat zugleich neun frühere Vorschläge zurückgestellt:
Eine separat erklärte Fotolizenz muss auch bei einer „Artwork“-Beschreibung
geklärt werden, nicht nur bei „Art Photo“. Die lokale Vorschau enthält daher
747 Einträge, ohne die zurückgestellten Fälle oder ungeprüfte Treffer mitzuzählen.
54 Offline-Recherchetests und die sechzehnte vollständige lokale Prüfung bestehen.
Quellen, Vorschauen und die vollständigen Farbanteile der weiterhin ausgewählten
Werke bleiben erhalten; veröffentlichte App und HA-Installation sind unverändert.

Die jüngste tatsächliche Zweitsichtung nimmt sieben vollständige Grafiken und
Gemälde auf, darunter Nooms' Blick auf Tripolis und Guillemets Küstenlandschaft
bei Villerville. Sechs direkte Bildvergleiche bestätigen dagegen zusätzliche
Scans bereits vorhandener Motive; diese zählen nicht mit. Niederländische
Höhen-/Breitenangaben behalten ihre Einheiten und den Maßumfang. Auftraggeber,
Entstehungsort und Datum werden nicht an den Künstlernamen angehängt; vorhandene
Zuschreibungsqualifikationen bleiben erhalten. 59 Offline-Recherchetests bestehen.

## Umfang dieses Updates

Der oben dokumentierte aktuelle Freeze und D-215/D-216 haben Vorrang vor den
folgenden historischen Recherchezwischenständen. Der vorbereitete
[Info-Text](commons-next-info.md) und die vollständige
[Farbkarten-Anleitung](commons-colour-user-guide-draft.md) werden erst nach
Freigabe der neuen Version in die öffentliche Anleitung übernommen. Aktuelle
b5-Releasebelege werden nicht mit neuen, noch nicht durchgeführten Tests vermischt.

Die nächste Zweitsichtung nimmt weitere vollständige Gemälde, Grafik und
architektonische Zeichnungen auf, darunter Nevinsons „Harvest of Battle“,
Shinsais vollständigen Surimono-Druck, Breitner/Maris und Rummells Princeton.
Eine attraktive persische Miniatur bleibt dagegen zurückgestellt: Die getrennt
in Zeilen angegebenen Original-H/W-Maße passen nicht zur breiten Datei. Diese
Maßangaben werden jetzt ebenso wie Semikolon-Paare geprüft. 63 Offline-Tests
bestehen; bekannte Medien-Suchpools können begrenzte Prüfläufe gezielt eingrenzen.
Die Generativkunst-Suche hat zwei ungeprüfte Kandidaten ergeben; ein neuer
Tempera-Lauf endete nach zwölf Kandidaten an einem dokumentierten Timeout.
Die betroffene Anfrage wird nicht automatisch wiederholt. Beide Suchzahlen
zählen nicht als Aufnahmen oder als Nachweis, dass die Werkarten ausgeschöpft sind.
Mednyánszkys „Pastier svíň“ ist nach tatsächlichem Quellen- und Bildabgleich
ebenfalls aufgenommen; ein neuer Wilhjelm-Scan gehört dagegen zu einem Werk,
das schon im Bestand vertreten ist. Die zwanzigste vollständige lokale Prüfung
besteht unverändert mit 5020 Tests und elf plattformbedingten Auslassungen.
Willem Maris' vollständiges „Heuvellandschap“ ist ebenfalls quellengebunden und
zweimal gesichtet aufgenommen. Ein Roelofs-Motiv bleibt wegen abweichender
Originalmaße draußen. Der begrenzte Künstler-Suchlauf hat 2617 Fenster erledigt;
248 nominelle Fenster und weitere Medien-Suchläufe sind noch offen. Die Auswahl
ist deshalb nicht als abgeschlossene Commons-Recherche oder 1000er-Katalog markiert.

### 1000 tatsächlich unterschiedliche Werke

Die bestehenden 400 Werke bleiben mit ihren IDs und Upload-Pins im Archiv erhalten.
Gemäß der ausdrücklichen Freigabe zählen künftig 344 davon zur aktiven Auswahl;
56 bleiben vorläufig zurückgestellt. 656 unterschiedliche Neuzugänge ergänzen
auf 1000 aktive Werke, sieben weitere bleiben Reserve. Alternative Scans oder
Ausschnitte bestehender Bilder zählen nicht als neue Werke. Der gespeicherte
Verlauf bleibt kompatibel; ein Update macht gesendete Bilder nicht erneut auswählbar.

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

Die Recherchefreigabe für CC BY und CC BY-SA liegt seit dem 10. Oktober vor.
Die Aufnahme bleibt eine Einzelentscheidung mit vollständiger Namensnennung,
Lizenzverlinkung und gegebenenfalls Änderungs-/Weitergabehinweisen. Die gefundenen
Fraktalkunst-Kandidaten und Anadol-Ausstellungsaufnahmen sind allein dadurch keine
Aufnahmen. Bei Anadol oder Kusama wäre zusätzlich die Freigabe des tatsächlich
abgebildeten Kunstwerks nötig; die Foto-Lizenz löst diese Frage nicht. Der erste
CC-Pilot ist ein Recherchevorrat, keine Erweiterung des Runtime-Rechtefilters.

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
