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
