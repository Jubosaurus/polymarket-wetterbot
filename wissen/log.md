# Log

Tagebuch: Datum, Entscheidung oder Erkenntnis, Fundort. Neueste Einträge unten. Regeln: [[REGELN]].

## 2026-10-13

- **Entscheidung:** Neues Projekt, getrennt vom Memecoin-Bot; nur Papierhandel, keine Wallet/Schlüssel. [[Arbeitsregeln]]
- **Erkenntnis:** 49 Temperaturstädte, 254 Tagesevents je Abruf, dazu Niederschlag für 14 US-Städte. [[Machbarkeit Phase 0]], [[Städteübersicht]]
- **Erkenntnis:** Auflösung seit 2026-08-23 über NOAA (vorher Weather Underground), beides METAR; ganze Grad, lokaler Tag. [[Rundung und Auflösung]], [[Zeitzonen und lokaler Tag]]
- **Erkenntnis:** METAR-Tageswerte treffen den Polymarket-Gewinner zu 99,3 % (Sept./Okt.). [[Auflösungsvalidierung METAR]]
- **Erkenntnis:** Hongkong schneidet auf ganze Grad ab (62/62). [[Hongkong Rundung]]
- **Erkenntnis:** Stationen wechselten bei Paris (LFPG→LFPB) und Denver (KDEN→KBKF); Station je Event aus dem Text lesen. [[Stationswechsel]]
- **Erkenntnis:** `prices-history` für geschlossene Märkte nur mit expliziten Zeitstempeln; keine historischen Spreads. [[Polymarket CLOB]]
- **Erkenntnis:** Open-Meteo-Ensemble hat keinen Rückblick (ca. 4 Tage); Previous Runs gibt es deterministisch seit 2024. [[Open-Meteo]]
- **Erkenntnis:** Modellfehler ca. 1–1,5 °C ≈ Bucketbreite. [[Vorhersagegüte Previous Runs]]
- **Entscheidung:** Rückrechnung machbar mit Einschränkungen. [[Rückrechnung Machbarkeit]]
- **Erkenntnis:** Codex-Review fand drei berechtigte Mängel (Station je Event, Schnappschuss-Pairing, volle Stundenreihen), behoben. [[Codex-Review Phase 0]]
- **Entscheidung:** Phase 0 eingespielt (Commit `812c518`). Phase 1: **Live-Protokoll zuerst, Rückrechnung danach.** [[Live-Protokoll]]
- **Erkenntnis:** Gebührenformel verifiziert: `fee = C × feeRate × p × (1 − p)`, Wetter 0,05, nur Taker. [[Polymarket Gebühren]], `docs/gebuehren.md`
- **Erkenntnis:** Open-Meteo-Minutenlimit (429) trat bei 0,5 s Pause auf; jetzt 2 s Pause und 65 s Wartezeit. [[Open-Meteo]]
- **Erkenntnis:** ICON-Meta bei Open-Meteo veraltet (Stand 6.10.); Rückfall auf 6-Stunden-Raster. [[Probelauf Live-Protokoll]]
- **Entscheidung:** Stammdaten des Protokolls nur als Differenz speichern (Token-Kennungen komprimieren schlecht). [[Probelauf Live-Protokoll]]
- **Entscheidung:** Wissensablage `wissen/` als eigener Obsidian-Vault; jede Entscheidung/Erkenntnis ins Wiki und ins Log. [[LIESMICH]]
- **Hinweis:** `docs/projekt_start.md` aus dem Auftrag existiert nicht; Regelseiten stammen aus `CLAUDE.md`. [[Arbeitsregeln]]
- **Erkenntnis:** Zweiter Codex-Review (Live-Protokoll): acht berechtigte Befunde, u. a. verlorene HKO-Events, leere Ensemble-Antworten als „erfasst“, unbegrenzte Wartezeiten, Push-Verlust, Look-ahead bei Ensemble-Empfang. Alle behoben. [[Codex-Review Live-Protokoll]]
- **Entscheidung:** Erfassung eines Modelllaufs gilt erst bei verwertbaren gespeicherten Werten aller Stationen (oder ≥ 90 % nach 3 Versuchen); Auflösungen ohne Messwert bleiben bis 60 Tage in einer Offen-Liste. [[Live-Protokoll]]
- **Entscheidung:** Gemeinsame Frist von 11 Minuten für alle Abrufe; Tageslimit-Pause bei Open-Meteo-„Daily limit“. [[Live-Protokoll]]
- **Erkenntnis:** Erster Lauf auf GitHub (manuell gestartet) grün, 2 min 13 s, Commit durch den Bot, alle Dateien angekommen (Schnappschuss 26 KB, Stamm 265 KB, Ensemble 64 KB, Wahrscheinlichkeiten 11 KB, Auflösung 6 KB; `.git` lokal 1,1 MB). Der Zeitplan (alle 30 Minuten) ist aktiv. [[Live-Protokoll]], [[GitHub-Actions-Workflow]]

## 2026-10-14

- **Entscheidung:** Rückrechnung (Phase 1b) mit vorab festgeschriebenen Regeln (Commit `0d071ab`, vor dem Laden der Daten): 15 Städte mit der längsten Markthistorie, ECMWF+GFS, Fehlerverteilung nur aus 2024–2025. [[Rückrechnung]]
- **Erkenntnis:** `previous_dayN` = letzter 6-Stunden-Lauf mit Init ≤ Gültigkeit − N·24 h (mit der Single-Runs-API nachgemessen); wegen ~9 h Verfügbarkeitsverzögerung wäre reines `previous_day1` um 18:00 Look-ahead. Lösung: je Stunde der jüngste verfügbare Lauf. [[Open-Meteo]]
- **Erkenntnis:** `POST /batch-prices-history` nimmt höchstens 20 Tokens; ≈ 4 700 Aufrufe für alle Testmärkte. [[Polymarket CLOB]]
- **Erkenntnis:** Gegenrechnung deckte Rundungsrauschen bei exakten x,5-Gleichständen auf (Raster der Werte); behoben, Übereinstimmung auf 2e-12. [[Rückrechnung]]
- **Erkenntnis:** Tiefsttemperatur-Märkte ab August zeigen beim Entscheidungszeitpunkt flache Startpreise (Preissumme bis 2,9); der scheinbare Gewinn der Bestätigungshälfte ist ein Preis-Artefakt. [[Rückrechnung]]
- **Entscheidung (Urteil nach Regel):** **Verwerfen** für das deterministische Verfahren. Aussagen zu echten Ensembles bleiben offen und hängen am Live-Protokoll. [[Rückrechnung]], [[Live-Protokoll]]
- **Hinweis:** Auf Wunsch (Nachtruhe) nicht eingespielt; Prüfung durch Codex steht aus.
- **Erkenntnis:** Live-Protokoll lief über Nacht nur zweimal (21:06 manuell, 00:29 Zeitplan; Lücken 203 und danach 279 min bis zum manuellen Start 05:08 UTC). Ursache vermutet: Überlastung der vollen/halben Stunde bei GitHub, nicht belegt. [[GitHub-Actions-Workflow]]
- **Entscheidung:** Cron von `*/30` auf `7,37 * * * *` umgestellt (Commit `1b8992d`); externer Auslöser (cron-job.org) nur vorgeschlagen, nicht gebaut. [[GitHub-Actions-Workflow]]
- **Erkenntnis:** Codex-Review der Rückrechnung: zwei Fehler bestätigt. (1) Zieltag aus `endDate` falsch bei 44 Events im Cache (2 in den 15 Städten: Seoul, NYC am 15.04.). (2) ECMWF-Stundenwerte sind Catmull-Rom-Interpolationen über 3-h-Stützstellen (gemessen 14 696 von 14 696 Stunden, ≤ 0,08 °C); GFS stündlich nativ. [[Rückrechnung]], [[Open-Meteo]]
- **Entscheidung:** Beide behoben (Zieltag aus Slug; Stundenwert nur bekannt, wenn alle Stützstellen verfügbar, sonst nächstälterer Lauf), Gegenrechnung mit eigenem Zieldatum (Fragetext) und eigener Stützstellen-Ableitung, alles neu gerechnet; Regeln `0d071ab` unverändert, Klarstellungen in `auswertungen/rueckrechnung_klarstellungen.md`. Urteil unverändert **Verwerfen** (Vorlauf 1 Bestätigung −1071 $, Vorlauf 2 +2780 $ nur aus Nein-Wetten). [[Rückrechnung]]
- **Erkenntnis:** Gewinn der Nein-Wetten (Vorlauf 2, Bestätigung) stammt fast vollständig aus Events mit Preissumme über 1,10 (+4 914 $ bei 1 484 Wetten); bei plausibler Preissumme −530 $ (665 Wetten). Alter der Preise nicht bestimmbar (Cache hat nur den letzten Rasterpunkt, Median 9,8 min). [[Rückrechnung]]
- **Entscheidung:** Kein Papierhandel auf Basis der Rückrechnung (Vorlauf 1 verworfen, Vorlauf 2 verdächtig). Neue Hypothese vorab festgeschrieben (Commit `e94b608`): Nein-Wetten Vorlauf 2 mit echten Ensembles, Bias 2024–2025 und echtem Ask mit Tiefe, Auswertung einmal ab 200 aufgelösten Wetten. [[Live-Hypothese 1]]
- **Entscheidung:** Auswerteskript `auswertungen/live_auswertung.py` (nur Auswertung über `daten/`, Zählstand ohne Gewinne bis 200 Wetten aufgelöst, Ergebnisdatei wird nie überschrieben). Tiefe wird nach der Wahl der zwei größten Kanten geprüft (vorsichtigere Auslegung). [[Live-Hypothese 1]]

- **Erkenntnis:** Stationsprüfung: In `bot/stationen.py` standen bei 18 Stationen Koordinaten, die bis zu 40 km neben dem Flughafen lagen (Qingdao 39,6 km, Chongqing 26,9, Wuhan 19,5, Chengdu 11,9, Karachi 6,7, Jeddah, Panama, Shanghai, Kuala Lumpur 3–5 km, weitere 1–2 km). Das IEM-Verzeichnis führt für ZUCK dieselben alten Werte; Referenz jetzt `aviationweather.gov`. Das Live-Protokoll rief die Ensembles dieser Städte am falschen Punkt ab. [[Stationsprüfung]]
- **Entscheidung:** Koordinaten korrigiert (Test ergänzt); von den 15 Städten der Rückrechnung ist nur Dallas betroffen (1,8 km), neu abgerufen und neu gerechnet: Vorlauf 1 Bestätigung −1071 → −1093 $, Vorlauf 2 unverändert, Urteil unverändert. [[Rückrechnung]], [[Stationsprüfung]]
- **Entscheidung:** Live-Hypothese 1 vor Datenbeginn überarbeitet (neuer Commit über `e94b608`): Bias neu für alle 48 Stationen mit korrigierten Koordinaten (nur Hong Kong ausgeschlossen), Ensemble-Abrufe vor der Korrektur zählen nicht (`live_start.txt`), Vergleichszeilen aufgeweitetes Ensemble und Blind-Nein. [[Live-Hypothese 1]]
- **Erkenntnis:** Gemeinsamer Codex-Review (Stationen, Dallas, Bias, Auswerteskript): ein Befund. Das Auswerteskript nahm den Zieltag aus dem Stamm; das Protokoll nimmt bei fehlendem eventDate `endDate`, und das liegt bei einzelnen Events einen Tag später (Seoul-Fall reproduziert: Td und Ensemble für den falschen Tag). Die 192 Bias-Zellen und die Dallas-Zahlen ließen sich exakt reproduzieren. [[Live-Hypothese 1]]
- **Entscheidung:** Befund behoben: `live_auswertung.py` bestimmt den Zieltag aus dem Slug (`rr.zieldatum_aus_slug`), zählt Abweichungen zum Stamm (`zieltag_weicht_vom_stamm_ab`), Regressionstest ergänzt (106 Tests grün). Die Regeldatei der Hypothese bleibt unverändert (sie sagt nur „Zieltag“; der Slug ist die Umsetzung wie in der Rückrechnung). [[Live-Hypothese 1]]
- **Entscheidung:** Anzeigename „Schanghai“ → „Shanghai“ (Seite umbenannt, Links angepasst). Handabgleich der Stationen vermerkt (bestätigt ZUCK, ZHHH, ZUUU, OPKC, ZSQD). Neue Seite [[spaetere_pruefpunkte]] (Höhe, Flughafeneffekte, Manipulation/Fall CDG), nur notiert, nichts gebaut. [[Stationsprüfung]]
