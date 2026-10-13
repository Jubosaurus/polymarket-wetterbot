# Machbarkeit Phase 0: Polymarket-Wetterbot (Papierhandel)

Stand der Abfragen: **2026-10-13** (alles mit echten Testabfragen, ohne Schlüssel, nur lesend).
Die Prüfskripte liegen im Repo (`auswertungen/validiere_aufloesung.py`, `bot/maerkte.py`, `bot/wetter.py`).

## Kurzfassung

**Eine Rückrechnung über mehrere Monate ist möglich: Ja, mit einer Einschränkung.**
Alle drei Zutaten gibt es historisch (alte Vorhersage, alter Marktpreis, Messwert). Die Einschränkung: Alte **Ensemble**-Vorhersagen gibt es bei Open-Meteo nicht (nur etwa 4 Tage Rückblick). Für die Rückrechnung muss daher die alte **deterministische** Vorhersage plus eine aus dem Archiv gelernte Fehlerverteilung die Rolle des Ensembles übernehmen. Echte Ensembles lassen sich nur ab jetzt sammeln (Live-Protokoll). Außerdem gibt es keine historischen Spreads, nur Preispunkte.

## 1a) Polymarket: Märkte finden und Regeln

**Alle aktuellen Wettermärkte:** Gamma-API, Keyset-Paginierung (Offset-Paginierung bricht ab Offset 2100 mit 422 ab):

```
GET https://gamma-api.polymarket.com/events/keyset?tag_slug=weather&active=true&closed=false&limit=100[&after_cursor=...]
```

Der Tag `weather` ergab heute 344 aktive Events (258 davon tragen den Tag `daily-temperature`). Davon:

| Art | Events | Anmerkung |
|---|---|---|
| Höchsttemperatur (`highest-temperature-in-<stadt>-on-<datum>`) | 131 | Tag `daily-temperature` |
| Tiefsttemperatur (`lowest-temperature-in-...`) | 123 | Tag `daily-temperature`; gibt es erst seit 2026-04-15 |
| Niederschlag (`where-will-it-rain-on-<datum>`) | 3 (je 14 US-Städte als Einzelmärkte) | Ja/Nein „messbarer Regen ≥ 0,01 in“, Quelle NWS Daily Climate Report (CLI), lokale Standardzeit |
| Sonstiges (Hurrikane, Erdbeben, Vulkane, Jahres-Temperatur-Rang, Masern …) | ca. 83 | langfristig, kein Tagesmarkt, **nicht** im Scope |
| Hängende Alt-Events (z. B. Jinan, Zhengzhou, 20. Mai) | 4 | aktiv, aber längst vorbei, werden ignoriert |

**Laufzeit:** Ein Tagesmarkt wird etwa 2 Tage vor dem Zieltag eröffnet (z. B. Start 2026-10-12 für 2026-10-14) und handelt bis zur Auflösung. Zu jedem Zeitpunkt laufen 3 Zieltage parallel (heute, morgen, übermorgen).

**Städte (49 Temperaturstädte, 254 Tagesevents je Abruf, immer 11 Buckets pro Event):**

- Nur Höchstwert: Kuala Lumpur, Manila, Panama City, Singapur. Alle anderen: Höchst- und Tiefstwert.
- **°F-Märkte (2-°F-Buckets, 11 US-Städte):** Atlanta, Austin, Chicago, Dallas, Denver, Houston, Los Angeles, Miami, NYC, San Francisco, Seattle. Beispiel NYC: `61°F or below, 62-63°F, … 78-79°F, 80°F or higher`.
- **°C-Märkte (1-°C-Buckets, alle anderen):** Beispiel `26°C or below, 27°C, … 35°C, 36°C or higher`. Die Buckets sind immer 9 mittlere plus 2 offene Randbuckets.
- Jedes Event ist `negRisk` (genau ein Bucket gewinnt).

| Stadt | Station | Quelle | Einheit | Arten | Spread (Median, Buckets 3–97 %) | Liquidität/Bucket (Median, $) |
|---|---|---|---|---|---|---|
| amsterdam | EHAM | NOAA | °C | ho+ti | 0.02 | 2242 |
| ankara | LTAC | NOAA | °C | ho+ti | 0.055 | 1664 |
| atlanta | KATL | NOAA | °F | ho+ti | 0.033 | 2497 |
| austin | KAUS | NOAA | °F | ho+ti | 0.058 | 1188 |
| beijing | ZBAA | NOAA | °C | ho+ti | 0.025 | 1581 |
| buenos-aires | SAEZ | NOAA | °C | ho+ti | 0.052 | 1349 |
| busan | RKPK | NOAA | °C | ho+ti | 0.05 | 684 |
| cape-town | FACT | NOAA | °C | ho+ti | 0.04 | 1571 |
| chengdu | ZUUU | NOAA | °C | ho+ti | 0.05 | 1002 |
| chicago | KORD | NOAA | °F | ho+ti | 0.03 | 701 |
| chongqing | ZUCK | NOAA | °C | ho+ti | 0.08 | 1228 |
| dallas | KDAL | NOAA | °F | ho+ti | 0.045 | 1033 |
| denver | KBKF | NOAA | °F | ho+ti | 0.04 | 1343 |
| guangzhou | ZGGG | NOAA | °C | ho+ti | 0.13 | 941 |
| helsinki | EFHK | NOAA | °C | ho+ti | 0.02 | 2189 |
| hong-kong | HKO (Observatorium, kein METAR) | HKO | °C | ho+ti | 0.035 | 2005 |
| houston | KHOU | NOAA | °F | ho+ti | 0.072 | 1233 |
| istanbul | LTFM | NOAA | °C | ho+ti | 0.04 | 1238 |
| jeddah | OEJN | NOAA | °C | ho+ti | 0.04 | 1353 |
| karachi | OPKC | NOAA | °C | ho+ti | 0.058 | 1196 |
| kuala-lumpur | WMKK | NOAA | °C | ho | 0.035 | 1729 |
| london | EGLC (City Airport) | NOAA | °C | ho+ti | 0.07 | 2440 |
| los-angeles | KLAX | NOAA | °F | ho+ti | 0.03 | 1549 |
| lucknow | VILK | NOAA | °C | ho+ti | 0.03 | 1477 |
| madrid | LEMD | NOAA | °C | ho+ti | 0.045 | 2298 |
| manila | RPLL | NOAA | °C | ho | 0.03 | 1389 |
| mexico-city | MMMX | NOAA | °C | ho+ti | 0.055 | 887 |
| miami | KMIA | NOAA | °F | ho+ti | 0.083 | 2100 |
| milan | LIMC | NOAA | °C | ho+ti | 0.04 | 1061 |
| moscow | UUWW (Wnukowo) | NOAA | °C | ho+ti | 0.04 | 1211 |
| munich | EDDM | NOAA | °C | ho+ti | 0.03 | 2466 |
| nyc | KLGA (LaGuardia) | NOAA | °F | ho+ti | 0.05 | 1304 |
| panama-city | MPMG | NOAA | °C | ho | 0.04 | 4074 |
| paris | LFPB (Le Bourget) | NOAA | °C | ho+ti | 0.07 | 1850 |
| qingdao | ZSQD | NOAA | °C | ho+ti | 0.019 | 879 |
| san-francisco | KSFO | NOAA | °F | ho+ti | 0.06 | 956 |
| sao-paulo | SBGR | NOAA | °C | ho+ti | 0.04 | 1421 |
| seattle | KSEA | NOAA | °F | ho+ti | 0.03 | 973 |
| seoul | RKSI (Incheon) | NOAA | °C | ho+ti | 0.052 | 1544 |
| shanghai | ZSPD (Pudong) | NOAA | °C | ho+ti | 0.03 | 1485 |
| shenzhen | ZGSZ | NOAA | °C | ho+ti | 0.03 | 903 |
| singapore | WSSS | NOAA | °C | ho | 0.02 | 2593 |
| taipei | RCSS (Songshan) | **Weather Underground** | °C | ho+ti | 0.04 | 1171 |
| tel-aviv | LLBG | NOAA | °C | ho+ti | 0.034 | 1616 |
| tokyo | RJTT (Haneda) | NOAA | °C | ho+ti | 0.076 | 1770 |
| toronto | CYYZ | NOAA | °C | ho+ti | 0.099 | 931 |
| warsaw | EPWA | NOAA | °C | ho+ti | 0.055 | 1640 |
| wellington | NZWN | NOAA | °C | ho+ti | 0.155 | 1989 |
| wuhan | ZHHH | NOAA | °C | ho+ti | 0.03 | 1071 |

Der Median-Spread ist nur über Buckets mit Preis 3–97 % gerechnet (bei Randbuckets nahe 0 ist der Spread kleiner als ein Tick, aber irrelevant). Über alle solchen Buckets: Median 0,04, Mittel 0,14, 90. Perzentil 0,49. Das heißt: Die Spreads sind je nach Bucket sehr unterschiedlich und in der Mitte der Verteilung nicht klein.

### Genaue Auflösungsregeln

- **Quelle: seit 2026-08-23 NOAA** (`weather.gov/wrh/timeseries?site=<ICAO>`): höchster/niedrigster Wert der Spalte „Temp“ über alle Stunden-Beobachtungen des Tages. Fällt NOAA aus, gilt als Ersatz die Weather-Underground-Tabelle „Daily Observations“. Fehlen beide Quellen bis 23:59 ET am Folgetag, gewinnt der **unterste Bucket**.
- **Vor 2026-08-23 war es Weather Underground** (`wunderground.com/history/daily/...`, Tabelle „Daily Observations“, nicht die „Day High & Low“-Zusammenfassung). Beide Quellen basieren auf denselben METAR-Beobachtungen (siehe 1c).
- **Rundung/Einheit:** Die Quelle misst auf **ganze Grad** in der Einheit des Marktes (°F bei US-Städten, sonst °C). Es wird diese Genauigkeit zur Auflösung benutzt. Korrekturen nach Veröffentlichung zählen nicht.
- **Hong Kong:** Quelle ist das Hong Kong Observatory („Absolute Daily Max/Min“ im Daily Extract, eine Nachkommastelle). Die Buckets sind ganze °C. Per Test an 62 Märkten (August 2026) gilt **Abschneiden** (28,9 °C → Bucket „28°C“): 62/62 Treffer; kaufmännisches Runden nur 29/62.
- **Zeitzone des Tages:** lokaler Kalendertag der Station (Beobachtungen „on this day“ in Ortszeit). Bestätigt dadurch, dass die Rückrechnung in 1c mit lokalen Kalendertagen 98–99 % trifft.
- **Enddatum im System:** `endDate` ist 12:00 UTC des Zieltages und hat mit dem echten Handelsschluss nichts zu tun: Die Märkte werden erst aufgelöst, wenn der Folgetag in der Quelle erscheint.
- Niederschlag: NWS-CLI-Bericht der Stadt, lokale Standardzeit (nicht Sommerzeit), `T` (Spur) zählt nicht, Bericht bis 14:00 ET am Folgetag, sonst „Nein“.
- Stationswechsel in der Historie (aus den Auflösungstexten): **Paris LFPG → LFPB (ab April 2026), Denver KDEN → KBKF (März/April 2026), Hong Kong zeitweise VHHH (März 2026).** Eine Rückrechnung muss die Station je Event aus dem Text lesen.
- **Gebühren:** Wettermärkte haben `feesEnabled` mit `feeType: weather_fees`, `rate 0.05`, nur Taker (`takerOnly`), `rebateRate 0.25` für Maker. Offizielle Formel: `fee = C × feeRate × p × (1 − p)`, Wetter-Rate 0,05, nur Taker. Details und Quellen: [gebuehren.md](gebuehren.md).
- Mindestgröße 5 Anteile; Tick 0,001 bei Preisen unter etwa 0,04 bzw. über 0,96, sonst 0,01.

## 1b) Polymarket-Preise

- **Orderbuch live:** `POST https://clob.polymarket.com/books` (Batch bis 100 Tokens je Aufruf getestet) liefert Bids/Asks mit Größe, `tick_size`, `min_order_size`. `GET /spread`, `GET /book`, `GET /fee-rate` (zeigt `base_fee: 1000`) funktionieren ebenfalls ohne Schlüssel. `bot/maerkte.py` nutzt `/books`.
- **Historische Preise:** `GET https://clob.polymarket.com/prices-history?market=<token_yes>&startTs=..&endTs=..&fidelity=<Minuten>`
  - **Wichtig:** Für geschlossene Märkte liefert `interval=max` und `interval=1d` **leere** Listen. Nur mit **expliziten `startTs`/`endTs`** kommen Daten.
  - Auflösung: `fidelity=1` (Minute) funktioniert (≈ 4000 Punkte pro Markt und ~3 Tage Laufzeit); 5, 10 und 60 ebenfalls.
  - Reichweite: zurück bis zum ersten Markt (**2025-12-28/30**). Getestet an NYC-Märkten vom 30.12.2025, 1.3., 1.6. und 1.9.2026: überall Daten.
  - Es sind **nur Preispunkte** (Trade/Mid), **kein historischer Spread und kein Orderbuch**. Für die Rückrechnung muss der Spread angenommen werden (heutiger Median 0,02–0,15 je Stadt, siehe Tabelle).
- **Menge:** Für geschlossene Tagesmärkte gibt es **13 989 Events / 152 973 Einzelmärkte** (Höchst 10 444, Tiefst 3 545; 53 Städte seit Dezember 2025). Pro Monat: Dez 11, Jan 8, Feb 154, Mär 721, Apr 1 500, Mai 1 655, Jun 1 693, Jul 1 765, Aug 2 290, Sep 3 034, Okt (bis 13.) 1 158. Dichte Daten gibt es also ab etwa März/April 2026 (ca. 6–7 Monate).
- **Durchsatz:** 20 aufeinanderfolgende `prices-history`-Aufrufe in 10 s ohne Fehler (≈ 0,5 s je Aufruf, ohne Parallelität). Alle 153 k Märkte wären ≈ 21 Stunden; eine Stichprobe (z. B. ein Preis-Aufruf je Event für den wahrscheinlichsten Bucket, oder ausgewählte Städte) ist realistisch.
- **Marktgröße (aktuell):** Liquidität im Median ≈ 1 400 $ je Bucket, Event-Volumen im Median ≈ 1 900 $ (0 bis 71 000 $). Das ist klein: Stakes im Papierhandel sollten klein angenommen werden, sonst verzerrt der Papierhandel die Wirklichkeit.

## 1c) Wetterdaten

**Open-Meteo (kein Schlüssel):**

| Datensatz | Endpunkt | Rückblick (getestet) |
|---|---|---|
| Ensemble live | `ensemble-api.open-meteo.com/v1/ensemble` | Vorhersage ab jetzt; `past_days` liefert max. **~4 Tage** (96 Stunden). `start_date` ≥ 2026-07-12 ist formal erlaubt, liefert für Vergangenes aber **nur Nullwerte**. |
| Deterministische Vorhersage rückwirkend („Historical Forecast“) | `historical-forecast-api.open-meteo.com/v1/forecast` | best_match und GFS ab 2022, ICON/GEM/UKMO ab 2024, ECMWF IFS/AIFS ab 2025 (getestet bis zu den genannten Stichtagen) |
| **Previous Runs** (Vorhersage von vor N Tagen) | `previous-runs-api.open-meteo.com/v1/forecast`, Variablen `temperature_2m_previous_day1…7` | Die meisten Modelle ab **Januar 2024**, GFS-Temperatur ab **März 2021**. Getestet: IFS und GFS liefern Daten für 2026-01-01, 2025-06-01, 2024-06-01; IFS nicht für 2023-06-01. |
| Historisches Ensemble | `historical-ensemble-api...` | **existiert nicht** (Host nicht auflösbar) |

- **Ensemble-Modelle (live getestet):** `ecmwf_ifs025` (51 Member), `gfs025` / NCEP GEFS (31), `icon_seamless` (40), `gem_global` (21): zusammen **143 Läufe** je Station, stündliche 2-m-Temperatur, in der Zeitzone der Station abrufbar (`timezone=<IANA>`), 3 bis 4 Tage Vorlauf bequem.
- Die Daten-Raster-Zelle ist nicht die Station: Die Modell-Temperatur am Flughafen-Gitterpunkt hat einen systematischen Fehler (Bias).
- **Vorhersagegüte (Test, September 2026, 29 Tage, Tageshöchstwert aus Previous Runs gegen METAR-Höchstwert):**

  | Stadt | ECMWF 1 Tag | ECMWF 3 Tage | GFS 1 Tag | GFS 3 Tage |
  |---|---|---|---|---|
  | NYC | MAE 1,00 (Bias +0,3) | 1,14 (+0,1) | 1,14 (+0,1) | 1,83 (+1,2) |
  | London | 1,11 (−0,8) | 1,28 (−0,7) | 0,84 (−0,1) | 1,00 (+0,2) |
  | Tokio | 1,21 (+0,1) | 1,33 (+0,3) | 1,00 (+0,5) | 1,36 (+0,3) |
  | Madrid | 0,75 (−0,6) | 0,91 (−0,2) | 1,06 (−0,9) | 1,07 (−0,7) |
  | São Paulo | 1,41 (+0,5) | 1,95 (+0,7) | 1,70 (+0,8) | 2,08 (+0,5) |
  | Singapur | 1,50 (−1,4) | 1,54 (−1,5) | 1,38 (−1,2) | 1,52 (−1,4) |

  (MAE in °C, in Klammern der mittlere Fehler). Fazit: Der typische Fehler (≈ 1–1,5 °C) liegt in der Größe der Bucketbreite, die Märkte haben also nur dann einen Vorteil, wenn Bias-Korrektur und Streuung gut kalibriert sind. Der Bias ist je Stadt verschieden (Singapur −1,4 °C).

**Stationsmessungen für die Auflösung:**

- **Iowa Environmental Mesonet (IEM, ASOS/METAR-Archiv)**: `mesonet.agron.iastate.edu/cgi-bin/request/asos.py`. **Kein Schlüssel, weltweit** (alle 48 getesteten ICAO-Kennungen lieferten Daten, mit Koordinaten), Beobachtungen im 30-/60-Minuten-Raster plus Specials, Archiv über Jahre. Das ist die empfohlene Quelle für die Rückrechnung.
- Weather Underground und NOAA-„Timeseries“ selbst wurden nicht abgefragt (JS-Seiten ohne dokumentierte freie API). Beide zeigen dieselben METAR-Daten; das deckt sich mit der Validierung unten. Meteostat wurde nicht getestet (braucht je nach Zugang einen Schlüssel). NOAA `api.weather.gov` und `aviationweather.gov` liefern nur etwa die letzten Tage und wurden nicht getestet.
- **Übereinstimmung mit der Polymarket-Auflösung** (`auswertungen/validiere_aufloesung.py`: METAR-Tageswert nach lokalem Kalendertag, Rundung wie oben, verglichen mit dem tatsächlichen Gewinner-Bucket, ohne Hong Kong):

  | Zeitraum | Märkte | Treffer |
  |---|---|---|
  | 2026-03-05 bis 03-20 | 309 | **96,1 %** mit Station je Event aus dem Auflösungstext (5 Events ohne bestimmbare Station ausgelassen). Mit der heutigen Stationstabelle waren es nur 93,6 % (Paris 75 %): Der Stationswechsel erklärt einen großen Teil. |
  | 2026-06-01 bis 06-15 | 826 | **98,2 %** |
  | 2026-09-20 bis 10-05 | 1 492 | **99,3 %** (11 Abweichungen, 10 davon am 20./21.9.) |

  Die schwächere Quote im März liegt zu einem großen Teil am Stationswechsel (Paris LFPG → LFPB); der Rest kommt vermutlich von Eigenheiten der damaligen Weather-Underground-Quelle (nicht weiter untersucht). Das Prüfskript liest die Station deshalb je Event aus dem Auflösungstext. Für die Rückrechnung ab Juni sind die Messwerte praktisch deckungsgleich.
- Einschränkung: Stündliche METAR-Werte und Specials werden mit gemessen. NOAA zeigt in der Tabelle alle diese Beobachtungen. Kleine Abweichungen von 1 Grad am Rand des Buckets bleiben (die ~1 % Fehlquote).

## 1d) API-Grenzen und Kosten

| Quelle | Schlüssel | Kosten | Grenzen |
|---|---|---|---|
| Polymarket Gamma (`gamma-api.polymarket.com`) | nein | frei | Offset-Paginierung max. Offset 2100, danach `/events/keyset`; Ratenlimit nicht ausgereizt (nicht gemessen) |
| Polymarket CLOB lesend (`/books`, `/book`, `/spread`, `/prices-history`) | nein (nur Orders brauchen Signatur, wird hier nie genutzt) | frei | 20 Aufrufe in 10 s ohne Fehler; offizielles Limit nicht geprüft |
| Open-Meteo (Forecast, Ensemble, Historical Forecast, Previous Runs) | nein | frei, **nur nicht-kommerziell** | 600 Aufrufe/min, 5 000/Stunde, 10 000/Tag (laut Preisseite). Ein Ensemble-Abruf je Station (49 Stationen) mit 4 Modellen × 4 Tage zählt **mehrfach**: Mit 0,5 s Pause kam bereits `429 Minutely API request limit exceeded`. `wetter.py` pausiert jetzt 2 s je Station und wartet bei 429 eine Minute |
| IEM (ASOS/METAR-Archiv) | nein | frei | Fair-Use (Betreiber bittet um Maß); wir fragen je Station und Zeitraum einmal ab |
| Hong Kong Observatory Open Data (`CLMMAXT`/`CLMMINT`) | nein | frei | nicht gemessen |

**Keine** dieser Quellen braucht einen Schlüssel. Die kostenpflichtige Open-Meteo-Version wird nur bei kommerzieller Nutzung nötig; Papierhandel ist nicht kommerziell.

## 1e) Antwort: Ist eine Rückrechnung über mehrere Monate möglich?

**Ja, für ca. 6–7 Monate (März/April bis Oktober 2026), mit folgenden Bedingungen:**

| Zutat | Verfügbar? | Wie |
|---|---|---|
| Alte Vorhersage | **Teilweise** | Deterministisch (IFS, GFS, ICON, GEM …) über Previous Runs seit Jan 2024 / 2021: ja. **Echte Ensembles: nein** (nur ~4 Tage). Ersatz: die Fehlerverteilung (Bias, Streuung je Stadt/Jahreszeit) aus dem langen Previous-Runs-Archiv lernen und damit eine Wahrscheinlichkeitsverteilung je Bucket bauen. Das ist ein anderes Modell als das Live-Ensemble, die Ergebnisse gelten nur eingeschränkt für den Live-Betrieb. |
| Alter Marktpreis | **Ja** | `prices-history` ab Dezember 2025, bis 1 Minute genau, nur mit expliziten Zeitstempeln. **Kein historischer Spread und kein Orderbuch:** Kosten müssen mit angenommenem Spread (≈ 0,02–0,15) und der Taker-Gebühr modelliert werden, sonst wird die Rückrechnung zu optimistisch. |
| Gemessener Wert | **Ja** | IEM-METAR, 98–99 % Übereinstimmung ab Juni; Station je Event aus dem Auflösungstext lesen (Paris, Denver); Hong Kong separat (HKO, Abschneiden). |

Zusätzliche Fallstricke für die Rückrechnung:

1. **Zeitabgleich:** „Vorhersage von vor N Tagen“ (`previous_dayN`) muss zum Zeitpunkt des verwendeten Marktpreises passen. Nur Informationen verwenden, die zu diesem Zeitpunkt schon bekannt waren.
2. **Marktgröße:** Median ca. 1 400 $ Liquidität je Bucket; ein Papierhandel mit größeren Beträgen wäre unrealistisch.
3. **Auswahlverzerrung:** Der Markt kennt die gleichen Wettermodelle. Dass ein Modell „besser“ als der Marktpreis ist, muss die Rückrechnung erst zeigen, es folgt nicht aus der Machbarkeit.
4. **Tiefstwerte** erst seit 15.4.2026, Städte wechseln (53 verschiedene Städte seit Dezember, 49 aktuell), Stationswechsel (siehe oben).

## Empfehlung für Phase 1

**Beides, aber in dieser Reihenfolge:**

1. **Sofort (klein, billig): Live-Protokoll als reines Sammeln** (kein Handel). Pro Lauf `maerkte.py` + `wetter.py` mit `--anhaengen`, und zusätzlich die Roh-Ensembles speichern. Begründung: Echte Ensemble-Vorhersagen lassen sich **nicht** nachträglich beschaffen. Jeder Tag ohne Protokoll ist für immer verloren. (Dafür bräuchte es einen Zeitplan; der ist in Phase 0 ausdrücklich ausgeschlossen und sollte erst nach Freigabe kommen.)
2. **Rückrechnung als erste Auswertung** auf einer Stichprobe: ca. 10–15 Städte (je Einheit und Klimazone gemischt) × März bis Oktober, ein Preispunkt je Markt zu einem festen Zeitpunkt (z. B. 24 h vor Tagesende), Previous-Runs-Vorhersage plus gelernte Fehlerverteilung. Ergebnis in wenigen Tagen. Sie zeigt, ob das Verfahren überhaupt eine Kante gegen den Marktpreis nach Spread und Gebühr hat. Nur wenn ja, lohnt der Aufwand für Live-Papierhandel.

Offene Punkte vor Phase 1: restliche März-Abweichungen (WU-Ära) klären; Hong-Kong-Archiv (HKO-Open-Data lieferte für Sep 2026 noch keine Monatsdaten, August ja) in die Rückrechnung einbauen oder ausklammern.
