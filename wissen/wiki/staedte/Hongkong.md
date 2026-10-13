---
typ: stadt
slug: hong-kong
station: HKO
zeitzone: Asia/Hong_Kong
einheit: C
rundung: abschneiden
quelle: HKO
tags: [stadt]
---
# Hongkong

| Eigenschaft | Wert |
|---|---|
| Polymarket-Kennung | `hong-kong` |
| Station | **HKO** – Hong Kong Observatory (Hauptquartier, kein Flughafen) |
| Koordinaten (Open-Meteo-Abruf) | 22.3025, 114.1744 |
| Auflösungsquelle | Hong Kong Observatory |
| Einheit | °C (1-°C-Buckets, z. B. `27°C`) |
| Rundung | Abschneiden auf ganze Grad |
| Zeitzone des Tages | `Asia/Hong_Kong` (lokaler Kalendertag) |
| Märkte | Höchst- und Tiefsttemperatur |
| Spread (Median, Buckets 3–97 %) | 0.035 |
| Liquidität je Bucket (Median) | 2005 $ |
| Validierung METAR gegen Gewinner (2026-09-20 bis 10-05) | alle Treffer (HKO, kein METAR) |

## Besonderheiten

**Sonderfall:** Auflösung durch das Hong Kong Observatory („Absolute Daily Max/Min“ im Daily Extract, eine Nachkommastelle), **kein METAR**. Die ganzzahligen Buckets entstehen durch **Abschneiden** (28,9 °C → „28°C“), per Test an 62 Märkten (62/62; Runden nur 29/62). Im März 2026 zeitweise VHHH als Quelle. Der HKO-Open-Data-Monatswert (`CLMMAXT`/`CLMMINT`) erscheint erst nach Monatsabschluss. Siehe [[Rundung und Auflösung]], [[HKO Open Data]].

## Siehe auch

[[Rundung und Auflösung]] · [[Zeitzonen und lokaler Tag]] · [[METAR (IEM)]] · [[Open-Meteo]] · [[Städteübersicht]]
