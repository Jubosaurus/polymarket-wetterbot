---
typ: experiment
tags: [experiment, protokoll]
stand: 2026-10-13
---
# Probelauf Live-Protokoll (lokal, 2026-10-13)

Ein kompletter Lauf von `python -m bot.protokoll --aufloesung` gegen die echten APIs, in ein Wegwerf-Verzeichnis:

- Dauer 136 s; 341 Wetter-Events, 2 803 Buckets; Ensemble für alle 4 Modelle × 49 Stationen = 49 Abrufe (kein 429).
- Größen: Schnappschuss 26 KB, Stamm 268 KB (erster Lauf des Tages), Ensemble 62 KB, Wahrscheinlichkeiten 11 KB, Auflösung 6 KB.
- Auflösung: 583 Events erfasst, 1 Abweichung, 12 offen (Hongkong, HKO-Monatsdaten fehlen noch).
- **Fund:** ICON-Meta war veraltet (Stand 6.10.). Rückfall auf 6-Stunden-Raster eingebaut ([[Open-Meteo]]).
- **Fund:** Der Stamm komprimiert schlecht (lange Token-Kennungen); deshalb nur Differenzen schreiben.

Siehe [[Live-Protokoll]].
