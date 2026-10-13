---
typ: stadt
slug: moscow
station: UUWW
zeitzone: Europe/Moscow
einheit: C
rundung: kaufm
quelle: NOAA
tags: [stadt]
---
# Moskau

| Eigenschaft | Wert |
|---|---|
| Polymarket-Kennung | `moscow` |
| Station | **UUWW** – Wnukowo |
| Koordinaten (Open-Meteo-Abruf) | 55.5915, 37.2615 |
| Auflösungsquelle | NOAA (weather.gov/wrh/timeseries), seit 2026-08-23; vorher Weather Underground |
| Einheit | °C (1-°C-Buckets, z. B. `27°C`) |
| Rundung | kaufmännisch runden (x,5 nach oben) auf ganze Grad |
| Zeitzone des Tages | `Europe/Moscow` (lokaler Kalendertag) |
| Märkte | Höchst- und Tiefsttemperatur |
| Spread (Median, Buckets 3–97 %) | 0.04 |
| Liquidität je Bucket (Median) | 1211 $ |
| Validierung METAR gegen Gewinner (2026-09-20 bis 10-05) | alle Treffer |

## Besonderheiten

Das Feld `resolutionSource` der API ist leer; die Quelle (NOAA, `site=UUWW`, Wnukowo) steht nur im Beschreibungstext. Siehe [[Polymarket Gamma]].

## Siehe auch

[[Rundung und Auflösung]] · [[Zeitzonen und lokaler Tag]] · [[METAR (IEM)]] · [[Open-Meteo]] · [[Städteübersicht]]
