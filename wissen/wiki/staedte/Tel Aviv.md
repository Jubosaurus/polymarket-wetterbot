---
typ: stadt
slug: tel-aviv
station: LLBG
zeitzone: Asia/Jerusalem
einheit: C
rundung: kaufm
quelle: NOAA
tags: [stadt]
---
# Tel Aviv

| Eigenschaft | Wert |
|---|---|
| Polymarket-Kennung | `tel-aviv` |
| Station | **LLBG** – Ben Gurion |
| Koordinaten (Open-Meteo-Abruf) | 32.0114, 34.8867 |
| Auflösungsquelle | NOAA (weather.gov/wrh/timeseries), seit 2026-08-23; vorher Weather Underground |
| Einheit | °C (1-°C-Buckets, z. B. `27°C`) |
| Rundung | kaufmännisch runden (x,5 nach oben) auf ganze Grad |
| Zeitzone des Tages | `Asia/Jerusalem` (lokaler Kalendertag) |
| Märkte | Höchst- und Tiefsttemperatur |
| Spread (Median, Buckets 3–97 %) | 0.034 |
| Liquidität je Bucket (Median) | 1616 $ |
| Validierung METAR gegen Gewinner (2026-09-20 bis 10-05) | 31/32 |

## Besonderheiten

Das Feld `resolutionSource` der API ist leer; die Quelle (NOAA, `site=LLBG`) steht nur im Beschreibungstext. Siehe [[Polymarket Gamma]].

## Siehe auch

[[Rundung und Auflösung]] · [[Zeitzonen und lokaler Tag]] · [[METAR (IEM)]] · [[Open-Meteo]] · [[Städteübersicht]]
