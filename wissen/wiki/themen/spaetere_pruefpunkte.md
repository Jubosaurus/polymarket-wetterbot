---
typ: thema
tags: [thema, pruefpunkte, stationen, manipulation]
stand: 2026-10-14
---
# Spätere Prüfpunkte (nur notiert, nichts gebaut)

Ideen, die bei der [[Stationsprüfung]] aufkamen. Nichts davon ist umgesetzt. **Wenn der Bot bei einer Stadt oft danebenliegt, zuerst diese Punkte prüfen**, bevor an Modell oder Schwellen gedreht wird.

## 1. Höhe

Rasterhöhe von Open-Meteo am Abrufpunkt gegen die Höhe der Station vergleichen, vor allem bei auffälligen Städten. Open-Meteo gleicht die Temperatur an das Geländemodell am Abrufpunkt an; liegt der Punkt falsch oder die Rasterhöhe weit von der Stationshöhe entfernt, entsteht ein fester Versatz. Stand 2026-10-14: nach der Koordinatenkorrektur höchstens etwa 9 m Unterschied (Kuala Lumpur 27 gegen 21 m, London 4 gegen 10 m), grob 0,06 °C je 10 m; der Bias der Hypothese fängt das mit auf.

## 2. Flughafeneffekte

- **Wärmeinsel:** Asphalt und Bebauung geben der Station einen festen Versatz gegenüber dem Modellgitter. Das ist ein Bias und wird von der Stationskorrektur in [[Live-Hypothese 1]] erfasst, solange er stabil ist.
- **Kurze Ausreißer:** Abgas von Triebwerken kann einzelne Messungen hochtreiben. Für Tagesmaximum und -minimum zählt jede Meldung; ein einzelner Ausreißer reicht, um einen Bucket zu kippen.

## 3. Manipulation einer Station

Fall **Paris-Charles-de-Gaulle (LFPG), April 2026:** Die Temperatur sprang nur an dieser Station, die Polizei ermittelte wegen eines vermuteten Eingriffs am Messgerät nach einer auffälligen Polymarket-Wette; Polymarket wechselte die Auflösungsstation auf **LFPB** (siehe [[Stationswechsel]] und [[Paris]]). Quelle: https://www.gpb.org/news/2026/04/24/french-police-probe-suspected-weather-device-tampering-after-odd-polymarket-bet

Idee für später: das Tagesmaximum (und -minimum) einer Station mit ein bis zwei Nachbarstationen vergleichen und Sprünge markieren, die an den Nachbarn nicht auftreten. Märkte solcher Tage nicht werten oder getrennt ausweisen. Das schützt auch vor einem Bias, der nur aus einem Manipulationstag stammt.

Siehe auch [[Stationsprüfung]], [[Rundung und Auflösung]], [[Open-Meteo]].
