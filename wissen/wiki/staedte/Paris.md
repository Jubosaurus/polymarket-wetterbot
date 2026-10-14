---
typ: stadt
slug: paris
station: LFPB
zeitzone: Europe/Paris
einheit: C
rundung: kaufm
quelle: NOAA
tags: [stadt]
---
# Paris

| Eigenschaft | Wert |
|---|---|
| Polymarket-Kennung | `paris` |
| Station | **LFPB** – Paris-Le Bourget |
| Koordinaten (Open-Meteo-Abruf) | 48.9672, 2.4272 |
| Auflösungsquelle | NOAA (weather.gov/wrh/timeseries), seit 2026-08-23; vorher Weather Underground |
| Einheit | °C (1-°C-Buckets, z. B. `27°C`) |
| Rundung | kaufmännisch runden (x,5 nach oben) auf ganze Grad |
| Zeitzone des Tages | `Europe/Paris` (lokaler Kalendertag) |
| Märkte | Höchst- und Tiefsttemperatur |
| Spread (Median, Buckets 3–97 %) | 0.07 |
| Liquidität je Bucket (Median) | 1850 $ |
| Validierung METAR gegen Gewinner (2026-09-20 bis 10-05) | alle Treffer |

## Besonderheiten

**Stationswechsel:** bis etwa April 2026 wurde **LFPG** (Charles de Gaulle) verwendet (Events Feb–Apr), danach **LFPB** (Le Bourget). Für Rückrechnungen die Station je Event aus dem Auflösungstext lesen, siehe [[Stationswechsel]]. Mit der heutigen Tabelle lag die Trefferquote im März bei nur 75 %, mit LFPG bei 100 %.

## Siehe auch

[[spaetere_pruefpunkte]] (Fall CDG, April 2026: Manipulation einer Station, Wechsel auf LFPB) · [[Rundung und Auflösung]] · [[Zeitzonen und lokaler Tag]] · [[METAR (IEM)]] · [[Open-Meteo]] · [[Städteübersicht]]

<!-- rueckrechnung -->
## Rückrechnung (Phase 1b)

Eine der 15 Städte mit der längsten Markthistorie. Fehlerverteilung je Station, Vorlauf und Art aus 490 Tagen (Mär–Okt 2024 und 2025), nicht gepoolt. Hauptregel-Wetten dieser Stadt (Kante ≥ 0,10, Spread 0,04, 10 $ je Wette; Summe nach Kosten in $):

| Gruppe | Wetten | Summe ($) |
|---|---|---|
| Vorlauf 1, Finden | 163 | -528 |
| Vorlauf 1, Bestätigen | 299 | -718 |
| Vorlauf 2, Finden | 152 | -110 |
| Vorlauf 2, Bestätigen | 276 | -741 |

Paris wurde mit **zwei Stationen** gerechnet (LFPG bei 48 frühen Events, LFPB danach), jede mit eigener Fehlerverteilung ([[Stationswechsel]]).

Einzelergebnisse sind klein und rauschbehaftet; maßgeblich ist das Gesamturteil **Verwerfen**, siehe [[Rückrechnung]].
