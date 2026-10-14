---
typ: stadt
slug: toronto
station: CYYZ
zeitzone: America/Toronto
einheit: C
rundung: kaufm
quelle: NOAA
tags: [stadt]
---
# Toronto

| Eigenschaft | Wert |
|---|---|
| Polymarket-Kennung | `toronto` |
| Station | **CYYZ** |
| Koordinaten (Open-Meteo-Abruf) | 43.6772, -79.6306 |
| Auflösungsquelle | NOAA (weather.gov/wrh/timeseries), seit 2026-08-23; vorher Weather Underground |
| Einheit | °C (1-°C-Buckets, z. B. `27°C`) |
| Rundung | kaufmännisch runden (x,5 nach oben) auf ganze Grad |
| Zeitzone des Tages | `America/Toronto` (lokaler Kalendertag) |
| Märkte | Höchst- und Tiefsttemperatur |
| Spread (Median, Buckets 3–97 %) | 0.099 |
| Liquidität je Bucket (Median) | 931 $ |
| Validierung METAR gegen Gewinner (2026-09-20 bis 10-05) | alle Treffer |

## Siehe auch

[[Rundung und Auflösung]] · [[Zeitzonen und lokaler Tag]] · [[METAR (IEM)]] · [[Open-Meteo]] · [[Städteübersicht]]

<!-- rueckrechnung -->
## Rückrechnung (Phase 1b)

Eine der 15 Städte mit der längsten Markthistorie. Fehlerverteilung je Station, Vorlauf und Art aus 490 Tagen (Mär–Okt 2024 und 2025), nicht gepoolt. Hauptregel-Wetten dieser Stadt (Kante ≥ 0,10, Spread 0,04, 10 $ je Wette; Summe nach Kosten in $):

| Gruppe | Wetten | Summe ($) |
|---|---|---|
| Vorlauf 1, Finden | 113 | -491 |
| Vorlauf 1, Bestätigen | 249 | +584 |
| Vorlauf 2, Finden | 66 | -40 |
| Vorlauf 2, Bestätigen | 140 | +592 |

Einzelergebnisse sind klein und rauschbehaftet; maßgeblich ist das Gesamturteil **Verwerfen**, siehe [[Rückrechnung]].
