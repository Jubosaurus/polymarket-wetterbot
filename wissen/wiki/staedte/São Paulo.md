---
typ: stadt
slug: sao-paulo
station: SBGR
zeitzone: America/Sao_Paulo
einheit: C
rundung: kaufm
quelle: NOAA
tags: [stadt]
---
# São Paulo

| Eigenschaft | Wert |
|---|---|
| Polymarket-Kennung | `sao-paulo` |
| Station | **SBGR** |
| Koordinaten (Open-Meteo-Abruf) | -23.4321, -46.4695 |
| Auflösungsquelle | NOAA (weather.gov/wrh/timeseries), seit 2026-08-23; vorher Weather Underground |
| Einheit | °C (1-°C-Buckets, z. B. `27°C`) |
| Rundung | kaufmännisch runden (x,5 nach oben) auf ganze Grad |
| Zeitzone des Tages | `America/Sao_Paulo` (lokaler Kalendertag) |
| Märkte | Höchst- und Tiefsttemperatur |
| Spread (Median, Buckets 3–97 %) | 0.04 |
| Liquidität je Bucket (Median) | 1421 $ |
| Validierung METAR gegen Gewinner (2026-09-20 bis 10-05) | alle Treffer |

## Siehe auch

[[Rundung und Auflösung]] · [[Zeitzonen und lokaler Tag]] · [[METAR (IEM)]] · [[Open-Meteo]] · [[Städteübersicht]]

<!-- rueckrechnung -->
## Rückrechnung (Phase 1b)

Eine der 15 Städte mit der längsten Markthistorie. Fehlerverteilung je Station, Vorlauf und Art aus 490 Tagen (Mär–Okt 2024 und 2025), nicht gepoolt. Hauptregel-Wetten dieser Stadt (Kante ≥ 0,10, Spread 0,04, 10 $ je Wette; Summe nach Kosten in $):

| Gruppe | Wetten | Summe ($) |
|---|---|---|
| Vorlauf 1, Finden | 95 | +105 |
| Vorlauf 1, Bestätigen | 221 | +221 |
| Vorlauf 2, Finden | 56 | -43 |
| Vorlauf 2, Bestätigen | 132 | +454 |

Einzelergebnisse sind klein und rauschbehaftet; maßgeblich ist das Gesamturteil **Verwerfen**, siehe [[Rückrechnung]].
