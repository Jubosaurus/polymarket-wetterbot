---
typ: thema
tags: [thema, aufloesung]
stand: 2026-10-13
---
# Stationswechsel

Die Station steht im Auflösungstext **jedes Events** und hat sich bei einigen Städten geändert:

| Stadt | Alt | Neu | Zeitpunkt |
|---|---|---|---|
| [[Paris]] | LFPG | LFPB | etwa April 2026 |
| [[Denver]] | KDEN | KBKF | März/April 2026 |
| [[Hongkong]] | VHHH | HKO | März 2026 (2 Events) |

**Regel:** Für Rückrechnung und Validierung die Station **je Event aus dem Text** lesen (`bot/aufloesung.py: station_aus_event`), nie aus der heutigen Tabelle. Ein Codex-Review hat genau diesen Fehler gefunden ([[Codex-Review Phase 0]]); mit der richtigen Station stieg die Märztrefferquote von 93,6 % auf 96,1 %.

Außerdem wechselte die Quelle am 2026-08-23 von Weather Underground auf NOAA ([[Rundung und Auflösung]]).
