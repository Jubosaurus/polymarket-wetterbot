---
typ: stadt
slug: nyc
station: KLGA
zeitzone: America/New_York
einheit: F
rundung: kaufm
quelle: NOAA
tags: [stadt]
---
# New York City

| Eigenschaft | Wert |
|---|---|
| Polymarket-Kennung | `nyc` |
| Station | **KLGA** – LaGuardia |
| Koordinaten (Open-Meteo-Abruf) | 40.7794, -73.8803 |
| Auflösungsquelle | NOAA (weather.gov/wrh/timeseries), seit 2026-08-23; vorher Weather Underground |
| Einheit | °F (2-°F-Buckets, z. B. `68-69°F`) |
| Rundung | kaufmännisch runden (x,5 nach oben) auf ganze Grad |
| Zeitzone des Tages | `America/New_York` (lokaler Kalendertag) |
| Märkte | Höchst- und Tiefsttemperatur |
| Spread (Median, Buckets 3–97 %) | 0.05 |
| Liquidität je Bucket (Median) | 1304 $ |
| Validierung METAR gegen Gewinner (2026-09-20 bis 10-05) | alle Treffer |

## Besonderheiten

Beispiel für °F-Märkte: Buckets in 2-°F-Schritten (`68-69°F`). Vorhersagetest September 2026: ECMWF 1 Tag MAE 1,0 °C, Bias +0,3 °C, siehe [[Vorhersagegüte Previous Runs]].

## Siehe auch

[[Rundung und Auflösung]] · [[Zeitzonen und lokaler Tag]] · [[METAR (IEM)]] · [[Open-Meteo]] · [[Städteübersicht]]

<!-- rueckrechnung -->
## Rückrechnung (Phase 1b)

Eine der 15 Städte mit der längsten Markthistorie. Fehlerverteilung je Station, Vorlauf und Art aus 490 Tagen (Mär–Okt 2024 und 2025), nicht gepoolt. Hauptregel-Wetten dieser Stadt (Kante ≥ 0,10, Spread 0,04, 10 $ je Wette; Summe nach Kosten in $):

| Gruppe | Wetten | Summe ($) |
|---|---|---|
| Vorlauf 1, Finden | 214 | -444 |
| Vorlauf 1, Bestätigen | 307 | -713 |
| Vorlauf 2, Finden | 85 | +276 |
| Vorlauf 2, Bestätigen | 117 | -14 |

Einzelergebnisse sind klein und rauschbehaftet; maßgeblich ist das Gesamturteil **Verwerfen**, siehe [[Rückrechnung]].
