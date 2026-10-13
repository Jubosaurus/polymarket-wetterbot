---
typ: thema
tags: [thema, aufloesung]
stand: 2026-10-13
---
# Rundung und Auflösung

- **Quelle:** seit 2026-08-23 NOAA (`weather.gov/wrh/timeseries?site=<ICAO>`), Spalte „Temp“, höchster/niedrigster Wert aller Beobachtungen des Tages; Ersatz Weather Underground „Daily Observations“. Vorher Weather Underground. [[Taipeh]] läuft noch über WU. Beide beruhen auf METAR ([[METAR (IEM)]]).
- **Genauigkeit:** ganze Grad in der Einheit des Marktes (°F bei elf US-Städten, sonst °C). Korrekturen nach Veröffentlichung zählen nicht.
- **Rundung:** METAR-Tageswerte sind bereits ganzzahlig bzw. werden kaufmännisch gerundet. Ensemble-Werte (kontinuierlich) vor dem Bucket-Vergleich kaufmännisch runden (`floor(x + 0,5)`), bei °F-Märkten erst in °F umrechnen.
- **Ausnahme [[Hongkong]]:** Abschneiden (`floor`), [[Hongkong Rundung]].
- **Buckets:** 11 je Event, 9 mittlere und 2 offene Ränder (`… or below` / `… or higher`). °C: 1 Grad breit; °F: 2 Grad breit.
- **Ausfall:** Fehlen Daten bis 23:59 ET am Folgetag, gewinnt der **unterste Bucket**.
- Niederschlag: NWS Daily Climate Report (CLI), lokale Standardzeit, ≥ 0,01 in, „Spur“ zählt nicht.

Siehe [[Zeitzonen und lokaler Tag]], [[Auflösungsvalidierung METAR]].
