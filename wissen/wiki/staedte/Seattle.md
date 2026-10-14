---
typ: stadt
slug: seattle
station: KSEA
zeitzone: America/Los_Angeles
einheit: F
rundung: kaufm
quelle: NOAA
tags: [stadt]
---
# Seattle

| Eigenschaft | Wert |
|---|---|
| Polymarket-Kennung | `seattle` |
| Station | **KSEA** |
| Koordinaten (Open-Meteo-Abruf) | 47.4447, -122.3144 |
| Auflösungsquelle | NOAA (weather.gov/wrh/timeseries), seit 2026-08-23; vorher Weather Underground |
| Einheit | °F (2-°F-Buckets, z. B. `68-69°F`) |
| Rundung | kaufmännisch runden (x,5 nach oben) auf ganze Grad |
| Zeitzone des Tages | `America/Los_Angeles` (lokaler Kalendertag) |
| Märkte | Höchst- und Tiefsttemperatur |
| Spread (Median, Buckets 3–97 %) | 0.03 |
| Liquidität je Bucket (Median) | 973 $ |
| Validierung METAR gegen Gewinner (2026-09-20 bis 10-05) | alle Treffer |

## Siehe auch

[[Rundung und Auflösung]] · [[Zeitzonen und lokaler Tag]] · [[METAR (IEM)]] · [[Open-Meteo]] · [[Städteübersicht]]

<!-- rueckrechnung -->
## Rückrechnung (Phase 1b)

Eine der 15 Städte mit der längsten Markthistorie. Fehlerverteilung je Station, Vorlauf und Art aus 490 Tagen (Mär–Okt 2024 und 2025), nicht gepoolt. Hauptregel-Wetten dieser Stadt (Kante ≥ 0,10, Spread 0,04, 10 $ je Wette; Summe nach Kosten in $):

| Gruppe | Wetten | Summe ($) |
|---|---|---|
| Vorlauf 1, Finden | 123 | -34 |
| Vorlauf 1, Bestätigen | 247 | +98 |
| Vorlauf 2, Finden | 73 | -51 |
| Vorlauf 2, Bestätigen | 133 | +325 |

Einzelergebnisse sind klein und rauschbehaftet; maßgeblich ist das Gesamturteil **Verwerfen**, siehe [[Rückrechnung]].
