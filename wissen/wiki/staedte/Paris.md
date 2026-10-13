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

[[Rundung und Auflösung]] · [[Zeitzonen und lokaler Tag]] · [[METAR (IEM)]] · [[Open-Meteo]] · [[Städteübersicht]]
