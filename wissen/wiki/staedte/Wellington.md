---
typ: stadt
slug: wellington
station: NZWN
zeitzone: Pacific/Auckland
einheit: C
rundung: kaufm
quelle: NOAA
tags: [stadt]
---
# Wellington

| Eigenschaft | Wert |
|---|---|
| Polymarket-Kennung | `wellington` |
| Station | **NZWN** |
| Koordinaten (Open-Meteo-Abruf) | -41.3272, 174.8053 |
| Auflösungsquelle | NOAA (weather.gov/wrh/timeseries), seit 2026-08-23; vorher Weather Underground |
| Einheit | °C (1-°C-Buckets, z. B. `27°C`) |
| Rundung | kaufmännisch runden (x,5 nach oben) auf ganze Grad |
| Zeitzone des Tages | `Pacific/Auckland` (lokaler Kalendertag) |
| Märkte | Höchst- und Tiefsttemperatur |
| Spread (Median, Buckets 3–97 %) | 0.155 |
| Liquidität je Bucket (Median) | 1989 $ |
| Validierung METAR gegen Gewinner (2026-09-20 bis 10-05) | alle Treffer |

## Besonderheiten

Größter Median-Spread aller Städte (0,155) und damit teuer zu handeln; Zeitzone Pacific/Auckland (Sommerzeit auf der Südhalbkugel).

## Siehe auch

[[Rundung und Auflösung]] · [[Zeitzonen und lokaler Tag]] · [[METAR (IEM)]] · [[Open-Meteo]] · [[Städteübersicht]]

<!-- rueckrechnung -->
## Rückrechnung (Phase 1b)

Eine der 15 Städte mit der längsten Markthistorie. Fehlerverteilung je Station, Vorlauf und Art aus 490 Tagen (Mär–Okt 2024 und 2025), nicht gepoolt. Hauptregel-Wetten dieser Stadt (Kante ≥ 0,10, Spread 0,04, 10 $ je Wette; Summe nach Kosten in $):

| Gruppe | Wetten | Summe ($) |
|---|---|---|
| Vorlauf 1, Finden | 116 | -51 |
| Vorlauf 1, Bestätigen | 238 | +68 |
| Vorlauf 2, Finden | 75 | +142 |
| Vorlauf 2, Bestätigen | 192 | +582 |

Einzelergebnisse sind klein und rauschbehaftet; maßgeblich ist das Gesamturteil **Verwerfen**, siehe [[Rückrechnung]].
