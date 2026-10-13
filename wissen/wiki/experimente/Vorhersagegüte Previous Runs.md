---
typ: experiment
tags: [experiment, wetter]
stand: 2026-10-13
---
# Vorhersagegüte der Previous Runs

Test: Tageshöchstwert aus `temperature_2m_previous_dayN` (Max der 24 Stunden des lokalen Tages) gegen METAR-Höchstwert, September 2026, 29 Tage, 6 Städte. MAE in °C (in Klammern mittlerer Fehler = Bias).

| Stadt | ECMWF 1 Tag | ECMWF 3 Tage | GFS 1 Tag | GFS 3 Tage |
|---|---|---|---|---|
| [[New York City]] | 1,00 (+0,3) | 1,14 (+0,1) | 1,14 (+0,1) | 1,83 (+1,2) |
| [[London]] | 1,11 (−0,8) | 1,28 (−0,7) | 0,84 (−0,1) | 1,00 (+0,2) |
| [[Tokio]] | 1,21 (+0,1) | 1,33 (+0,3) | 1,00 (+0,5) | 1,36 (+0,3) |
| [[Madrid]] | 0,75 (−0,6) | 0,91 (−0,2) | 1,06 (−0,9) | 1,07 (−0,7) |
| [[São Paulo]] | 1,41 (+0,5) | 1,95 (+0,7) | 1,70 (+0,8) | 2,08 (+0,5) |
| [[Singapur]] | 1,50 (−1,4) | 1,54 (−1,5) | 1,38 (−1,2) | 1,52 (−1,4) |

**Erkenntnis:** Der typische Fehler (ca. 1–1,5 °C) liegt in der Größe einer Bucketbreite. Ein Vorteil gegenüber dem Markt entsteht nur bei guter Kalibrierung von Bias (je Stadt verschieden) und Streuung. Siehe [[Ensemble und deterministische Vorhersage]], [[Rückrechnung Machbarkeit]]. Quelle: [[Open-Meteo]].
