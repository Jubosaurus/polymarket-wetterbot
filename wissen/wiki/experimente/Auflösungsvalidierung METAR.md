---
typ: experiment
tags: [experiment, aufloesung]
stand: 2026-10-13
---
# Auflösungsvalidierung METAR gegen Polymarket-Gewinner

Skript: `auswertungen/validiere_aufloesung.py`. Frage: Reproduziert der METAR-Tageswert (lokaler Kalendertag, [[Rundung und Auflösung]]) den tatsächlichen Gewinner-Bucket? Quelle der Messwerte: [[METAR (IEM)]].

| Zeitraum | Märkte | Treffer |
|---|---|---|
| 2026-03-05 bis 03-20 | 309 | **96,1 %** (Station je Event aus dem Text; 5 Events ohne bestimmbare Station ausgelassen) |
| 2026-03-05 bis 03-20 (heutige Stationstabelle) | 314 | 93,6 % (Paris nur 75 %) |
| 2026-06-01 bis 06-15 | 826 | 98,2 % |
| 2026-09-20 bis 10-05 | 1 492 | **99,3 %** (11 Abweichungen, 10 davon am 20./21.9.) |

**Erkenntnisse:** Der Stationswechsel ([[Stationswechsel]]) erklärt einen großen Teil der März-Abweichungen; das Skript liest deshalb die Station je Event. Der Rest im März (Weather-Underground-Ära) ist nicht weiter untersucht. Tag = lokaler Kalendertag ist bestätigt ([[Zeitzonen und lokaler Tag]]).

Das [[Live-Protokoll]] setzt diese Prüfung täglich fort (Probelauf: 583 Events, 1 Abweichung: Paris 2026-10-07, gemessen 19 °C, Gewinner „18°C“).
