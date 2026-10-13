# Rückrechnung (Phase 1b): festgeschriebene Regeln

**Festgeschrieben am 2026-10-13, vor dem Abruf von Prognose-, Mess- und Preisdaten für die Rückrechnung. Nach dem Einspielen dieser Datei wird sie nicht mehr geändert.** Spätere Erkenntnisse kommen in den Bericht (`auswertungen/JJJJ-MM-TT_rueckrechnung.md`) und nicht hierher. Nur Auswertung: keine Wetten, kein Eingriff in das Live-Protokoll.

Stand des Vorwissens (ehrlich): Vor dem Festschreiben gesehen wurden (a) die Märkte-Metadaten (Städte, Daten, Gewinner-Titel), (b) in Phase 0 der Vorhersagefehler-Test (6 Städte, September 2026, MAE ≈ 1–1,5 °C) und die Validierung METAR gegen Gewinner. Preise der Testmärkte und Vorhersagen für den Testzeitraum wurden nicht ausgewertet.

## 0. Ergebnisse der Vorab-Prüfung (Plananpassung)

| Frage | Befund |
|---|---|
| Liefert die **Previous Runs API** feste Vorlaufzeiten? | Ja: `temperature_2m_previous_dayN` ist der Wert „N·24 h vor Gültigkeitszeit“. Nachgemessen mit der Single-Runs-API (Läufe mit expliziter Initialzeit): Jede Gültigkeitsstunde stammt aus dem **letzten 6-Stunden-Lauf (00/06/12/18 UTC) mit Init ≤ Gültigkeit − N·24 h**, also 24–29 h (day1) bzw. 48–53 h (day2) Vorlauf (GFS eindeutig; ECMWF überwiegend). Die **Historical Forecast API** wird nicht verwendet (setzt die ersten Stunden vieler Läufe zusammen, Zuordnung Lauf/Zeitpunkt unklar). |
| **Look-ahead-Falle** | Die Modelle sind erst ca. **9 h nach Init** öffentlich verfügbar (Open-Meteo-`meta.json` 2026-10-13: ECMWF IFS 9,0 h, GFS 0,25° 9,3 h). Um 18:00 Ortszeit am Vortag ist der Lauf, der für Nachmittagsstunden des Zieltags in `previous_day1` steckt (Init ≈ 12 UTC am Vortag), **noch nicht verfügbar**. Reines `previous_day1` für den Tageshöchstwert wäre Look-ahead. **Anpassung:** Pro Gültigkeitsstunde wird der jüngste zum Entscheidungszeitpunkt **verfügbare** Lauf verwendet (siehe 3). Folge: Der wirksame Vorlauf des Tageshöchstwerts ist länger als „1 Tag“. |
| Aufrufe `prices-history` | Batch-Endpunkt `POST /batch-prices-history` (max. **20** Tokens je Aufruf, Felder `markets`, `start_ts`, `end_ts`, `fidelity`). Testmärkte: **4 674 Events / 50 954 Märkte** (15 Städte, 2026-03-01 bis 2026-10-11). Mit **einem Aufruf je Event** (ein Zeitfenster deckt beide Entscheidungszeitpunkte ab) ≈ **4 700 Aufrufe** à ≈ 0,4 s ≈ 35 Minuten, nacheinander. Einzelabrufe je Token und Zeitfenster wären ≈ 102 000 Aufrufe und würden nicht verwendet. Grenzen: kein Fehler bei bisherigen Tests (20 Aufrufe/10 s). |
| Open-Meteo-Aufrufe | ≈ 100 (16 Stationen × 2 Modelle × 3 Zeitbereiche), mit Pause und Cache, deutlich unter dem Tageslimit. |

## 1. Märkte und Städte

- Märkte: Höchst- und Tiefsttemperatur (`highest-/lowest-temperature-in-<stadt>-on-…`), Zieldatum **2026-03-01 bis 2026-10-11**. Tiefstwert-Märkte gibt es erst ab 2026-04-15.
- **Die 15 Städte mit der längsten Markthistorie** (Datum des ersten Events, bei Gleichstand alphabetisch). Nur Städte mit METAR-Auflösung kommen in Frage (Hongkong/HKO hätte keine METAR-Kalibrierung, steht aber ohnehin nicht darunter). Festgelegt aus der Event-Liste vor jeder Rechnung:

| Rang | Stadt | erstes Event | Einheit |
|---|---|---|---|
| 1–3 | Atlanta, Dallas, NYC | 2025-12-30 | °F |
| 4–8 | Buenos Aires, London, Seattle, Seoul, Toronto | 2025-12-31 | Seattle °F, sonst °C |
| 9–14 | Ankara, Chicago, Miami, Paris, São Paulo, Wellington | 2026-02-18 | Chicago, Miami °F, sonst °C |
| 15 | Lucknow (Gleichstand 2026-03-05 mit München, alphabetisch) | 2026-03-05 | °C |

- Station **je Event aus dem Auflösungstext** (Paris: LFPG bei 48 frühen Events, LFPB bei 341; alle anderen Städte eine Station). Für Paris werden beide Stationen getrennt kalibriert.
- Events ohne bestimmbare Station, ohne Gewinner oder ohne Preis am Entscheidungszeitpunkt werden ausgelassen und gezählt.

## 2. Wahrheit

Gewinn/Verlust: der **Polymarket-Gewinner** (Markt mit `outcomePrices[0] ≥ 0.99`). METAR dient nur zur Kalibrierung im Vorzeitraum.

## 3. Vorhersage

- Modelle: **ECMWF IFS (`ecmwf_ifs025`) und GFS (`gfs_seamless`)** über die Previous Runs API. **ICON wird nicht verwendet** (die „seamless“-Mischung aus ICON global/EU/D2 hat verschiedene Zyklen; die Zuordnung ist nicht sauber).
- Station-Koordinaten aus dem IEM-Stationsverzeichnis (Position des Flughafens).
- **Entscheidungszeitpunkt** `Td`: **18:00 Ortszeit der Station am Vortag (Vorlauf 1)** bzw. **18:00 Ortszeit zwei Tage vorher (Vorlauf 2)**, umgerechnet nach UTC mit der Zeitzone der Station.
- **Bekannter Lauf je Gültigkeitsstunde `t`:** Für `N = V, V+1, V+2` (V = 1 bzw. 2, höchstens N = 3) ist `I_N(t) = floor₆(t − 24·N h)` (auf 00/06/12/18 UTC abgerundet) der Lauf hinter `previous_dayN`. Er gilt als bekannt, wenn **`I_N(t) + 10 h ≤ Td`** (angenommene Verfügbarkeitsverzögerung 10 h, etwas über den gemessenen 9,0–9,3 h). Verwendet wird das **kleinste** solche `N`. Fehlt für eine Stunde jedes `N ≤ 3`, fällt der Tag aus.
- Tageswert = Maximum bzw. Minimum der 24 (an Zeitumstellungen 23/25) stündlichen Werte des **lokalen Kalendertags** der Zielstadt.
- **Primäre Vorhersage `F`** = Mittelwert der Tageswerte von ECMWF und GFS. Sekundär (nur zusätzlich berichtet): ECMWF allein, GFS allein.
- Einheit: Berechnung in °C; für °F-Städte `F_F = F·9/5 + 32`.

## 4. Fehlerverteilung (nur Vorzeitraum)

- Zeitraum: **2024-03-01 bis 2024-10-31 und 2025-03-01 bis 2025-10-31** (gleiche Jahreszeit wie der Test, vollständig **vor** dem Testzeitraum). Marktdaten werden dafür nicht benötigt.
- Je Station × Vorlauf (V1/V2) × Art (Höchst/Tiefst) werden Residuen `r = Messwert − F` gebildet; Messwert = Tageshöchst-/Tiefstwert der IEM-METAR-Beobachtungen im lokalen Kalendertag (kontinuierlich, ≥ 8 Beobachtungen), Einheit wie der Markt (°C bzw. °F). Die Vorhersage entsteht mit **demselben Verfahren** wie im Test (inklusive Verfügbarkeitsregel), nur mit den Tagen des Vorzeitraums.
- **Mindestmenge 300 Tage** je Zelle; sonst Residuen **gepoolt über alle Stationen** gleicher Einheit, Vorlauf und Art, und im Bericht vermerkt.
- **Wahrscheinlichkeit je Bucket:** `P(Bucket) = Anteil der Residuen r mit rund(F + r) ∈ Bucket`, `rund` = Rundungsregel der Stadt (hier überall kaufmännisch, `floor(x + 0,5)`). Danach auf `[0,005; 0,995]` begrenzt. Keine Glättung, kein Nachtrimmen.
- Der Test-Zeitraum fließt nirgends in diese Verteilung ein.

## 5. Preise

- Quelle: `POST /batch-prices-history` (Token „Yes“), Fenster `[Td₂ − 12 h, Td₁]`, `fidelity = 10` (Minuten). Preis zum Entscheidungszeitpunkt `Td` = **letzter Preispunkt mit `t ≤ Td`**, höchstens 12 h alt; sonst kein Preis (Bucket entfällt).
- Der Verlauf liefert Preispunkte (Mitte/letzter Handel, genaue Definition unbekannt), **kein Orderbuch**. Der Spread ist angenommen (siehe 6).
- Ja-Preis `p`; Nein-Preis `1 − p`.

## 6. Kosten und Wetten

- Annahme Gesamt-Spread `S = 0,04` (Hauptfall). Kaufpreis `q = Preis + S/2`.
- Gebühr je Anteil nach `docs/gebuehren.md`: `fee = 0,05 · q · (1 − q)` (Taker). Kosten je Anteil `c = q + fee`. Ist `c ≥ 1`, entfällt die Wette.
- **Kante** `= Modell-Wahrscheinlichkeit der Seite − c`. Ja: Seite = `P`; Nein: Seite = `1 − P`.
- **Hauptregel: Wette, wenn Kante ≥ 0,10.** Zusätzlich nur berichtet: 0,05 und 0,15.
- **Einsatz 10 $ inklusive Gebühr:** Anteile `= 10 / c`; bei Gewinn Auszahlung `= Anteile` (1 $ je Anteil), Ergebnis `= Anteile − 10`; bei Verlust `−10`.
- **Höchstens 2 Wetten je Event** (die 2 größten Kanten). Hauptauswertung lässt Ja und Nein zu; zusätzlich getrennt berichtet: „nur Ja“ und „nur Nein“ (jeweils mit eigenem Limit von 2).
- Keine Berücksichtigung von Markttiefe, Tick und Mindestgröße (siehe Bericht, „Was die Rückrechnung nicht zeigt“).

## 7. Hälften

- **Finden:** Zieldatum 2026-03-01 bis 2026-06-30. **Bestätigen:** 2026-07-01 bis 2026-10-11.
- Entscheidungen und Urteil stützen sich auf die **Bestätigungshälfte**; die Findungshälfte dient der Beschreibung. Nichts wird nach Sicht der Zahlen geändert; Abweichungen von diesen Regeln gäbe es nur als ausdrücklich gekennzeichnete Zusatzauswertung.

## 8. Auswertung

- **Brier-Score** aller Buckets mit Preis am Entscheidungszeitpunkt: Modell (`P`) gegen Marktpreis `p`, je Hälfte, Vorlauf, Einheit (°F/°C). Kalibrierungstabelle in Zehnerstufen (Modell sagt 20–30 % → tatsächliche Häufigkeit).
- **Wetten:** Anzahl, Trefferquote, Gewinn je Wette nach Kosten, Summe, Summe ohne die 3 besten Wetten, je Hälfte, Ja/Nein getrennt.
- **Empfindlichkeit:** `S = 0,02 / 0,04 / 0,06`.
- **Look-ahead-Prüfung:** 20 zufällige Wetten der Hauptregel (Zufallssamen 42) mit Zeitstempeln: Lauf (Init und Verfügbarkeit) der Stunde des Tagesextrems, Preispunkt-Zeit, Entscheidungszeit.
- **Urteil (vorab festgelegt):** „Weiter mit Papierhandel“ nur, wenn in der **Bestätigungshälfte** für **beide** Vorläufe (Hauptregel, `S = 0,04`, primäre Vorhersage) gilt: ≥ 100 Wetten, Summe > 0, Summe ohne die 3 besten > 0 und Brier(Modell) < Brier(Markt). „Zu wenig Daten“, wenn die Bestätigungshälfte (beide Vorläufe zusammen) < 100 Wetten hat. Sonst „Verwerfen“.
- **Gegenrechnung:** Ein zweites, unabhängig geschriebenes Skript (`auswertungen/rueckrechnung_gegenrechnung.py`) berechnet die Kernzahlen aus den zwischengespeicherten Rohdaten erneut; Abweichungen werden im Bericht genannt.
- Mehrfachvergleiche: Es gibt zwei Vorläufe × Hälften × Seiten × Schwellen × Spreads. Nur die oben benannte Hauptzelle zählt für das Urteil; alles andere ist Beschreibung.
