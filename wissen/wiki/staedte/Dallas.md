---
typ: stadt
slug: dallas
station: KDAL
zeitzone: America/Chicago
einheit: F
rundung: kaufm
quelle: NOAA
tags: [stadt]
---
# Dallas

| Eigenschaft | Wert |
|---|---|
| Polymarket-Kennung | `dallas` |
| Station | **KDAL** |
| Koordinaten (Open-Meteo-Abruf) | 32.83836, -96.83584 (korrigiert 2026-10-14, vorher 32.8471, -96.8518: 1.8 km daneben, siehe [[Stationsprüfung]]) |
| Auflösungsquelle | NOAA (weather.gov/wrh/timeseries), seit 2026-08-23; vorher Weather Underground |
| Einheit | °F (2-°F-Buckets, z. B. `68-69°F`) |
| Rundung | kaufmännisch runden (x,5 nach oben) auf ganze Grad |
| Zeitzone des Tages | `America/Chicago` (lokaler Kalendertag) |
| Märkte | Höchst- und Tiefsttemperatur |
| Spread (Median, Buckets 3–97 %) | 0.045 |
| Liquidität je Bucket (Median) | 1033 $ |
| Validierung METAR gegen Gewinner (2026-09-20 bis 10-05) | alle Treffer |

## Siehe auch

[[Rundung und Auflösung]] · [[Zeitzonen und lokaler Tag]] · [[METAR (IEM)]] · [[Open-Meteo]] · [[Städteübersicht]]

<!-- rueckrechnung -->
## Rückrechnung (Phase 1b)

Eine der 15 Städte mit der längsten Markthistorie. Fehlerverteilung je Station, Vorlauf und Art aus 490 Tagen (Mär–Okt 2024 und 2025), nicht gepoolt. Hauptregel-Wetten dieser Stadt (Kante ≥ 0,10, Spread 0,04, 10 $ je Wette; Summe nach Kosten in $):

| Gruppe | Wetten | Summe ($) |
|---|---|---|
| Vorlauf 1, Finden | 109 | -359 |
| Vorlauf 1, Bestätigen | 247 | -102 |
| Vorlauf 2, Finden | 92 | -402 |
| Vorlauf 2, Bestätigen | 131 | +232 |

Einzelergebnisse sind klein und rauschbehaftet; maßgeblich ist das Gesamturteil **Verwerfen**, siehe [[Rückrechnung]].
