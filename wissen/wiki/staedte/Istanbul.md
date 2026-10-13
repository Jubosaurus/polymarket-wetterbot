---
typ: stadt
slug: istanbul
station: LTFM
zeitzone: Europe/Istanbul
einheit: C
rundung: kaufm
quelle: NOAA
tags: [stadt]
---
# Istanbul

| Eigenschaft | Wert |
|---|---|
| Polymarket-Kennung | `istanbul` |
| Station | **LTFM** – Istanbul Airport |
| Koordinaten (Open-Meteo-Abruf) | 41.2629, 28.7413 |
| Auflösungsquelle | NOAA (weather.gov/wrh/timeseries), seit 2026-08-23; vorher Weather Underground |
| Einheit | °C (1-°C-Buckets, z. B. `27°C`) |
| Rundung | kaufmännisch runden (x,5 nach oben) auf ganze Grad |
| Zeitzone des Tages | `Europe/Istanbul` (lokaler Kalendertag) |
| Märkte | Höchst- und Tiefsttemperatur |
| Spread (Median, Buckets 3–97 %) | 0.04 |
| Liquidität je Bucket (Median) | 1238 $ |
| Validierung METAR gegen Gewinner (2026-09-20 bis 10-05) | alle Treffer |

## Besonderheiten

Das Feld `resolutionSource` der API ist leer; die Quelle (NOAA, `site=LTFM`) steht nur im Beschreibungstext. Siehe [[Polymarket Gamma]].

## Siehe auch

[[Rundung und Auflösung]] · [[Zeitzonen und lokaler Tag]] · [[METAR (IEM)]] · [[Open-Meteo]] · [[Städteübersicht]]
