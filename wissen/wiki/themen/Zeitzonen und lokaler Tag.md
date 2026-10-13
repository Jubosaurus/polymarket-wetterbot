---
typ: thema
tags: [thema, aufloesung]
stand: 2026-10-13
---
# Zeitzonen und lokaler Tag

Der „Tag“ eines Marktes ist der **lokale Kalendertag der Station** (Beobachtungen „on this day“ in Ortszeit). Bestätigt durch die Validierung mit lokalen Kalendertagen ([[Auflösungsvalidierung METAR]]).

- Zeitzonen je Stadt als IANA-Namen in `bot/stationen.py`, auf jeder Städteseite ([[Städteübersicht]]).
- Open-Meteo wird mit `timezone=<IANA>` abgefragt, damit die Stundenachse lokal läuft. Tage mit Zeitumstellung haben 23 oder 25 Stunden.
- Ein Mitglied zählt nur mit **allen** Stundenwerten des lokalen Tages (fehlt die Spitzenstunde, wäre das Tagesmaximum falsch).
- Niederschlag: lokale **Standard**zeit (nicht Sommerzeit).
- `endDate` der Märkte (12:00 UTC) ist nominell; eine Hongkong-Abfrage um 18:48 UTC ist schon der Folgetag, deshalb fehlen dann dessen Vorhersagen für „heute“.
