---
typ: experiment
tags: [experiment, rueckrechnung, phase1b]
stand: 2026-10-14
---
# Rückrechnung (Phase 1b)

**Frage:** Hätte ein Verfahren aus zwei deterministischen Modellen (ECMWF, GFS) und einer aus 2024–2025 gelernten Fehlerverteilung im Testzeitraum März–Oktober 2026 gegen die Polymarket-Preise Geld verdient (nur Papier, nach Spread und Gebühr)?

**Antwort nach den vorab festgelegten Kriterien: Verwerfen.** Vollständiger Bericht: `auswertungen/2026-10-14_rueckrechnung.md`; Regeln (vor dem Laden der Daten eingespielt, Commit `0d071ab`): `auswertungen/rueckrechnung_regeln.md`.

## Aufbau (Kurzfassung)

- 15 Städte mit der längsten Markthistorie ([[Atlanta]], [[Dallas]], [[New York City]], [[Buenos Aires]], [[London]], [[Seattle]], [[Seoul]], [[Toronto]], [[Ankara]], [[Chicago]], [[Miami]], [[Paris]], [[São Paulo]], [[Wellington]], [[Lucknow]]), 4 674 Events, 50 954 Märkte, Höchst- und Tiefstwerte.
- Entscheidungszeitpunkt 18:00 Ortszeit am Vortag (Vorlauf 1) bzw. zwei Tage vorher (Vorlauf 2). Nur Läufe, die dann **verfügbar** waren (Init + 10 h); dadurch ist der wirksame Vorlauf des Tageshöchstwerts länger als der Name ([[Open-Meteo]]).
- Wahrscheinlichkeit je Bucket aus den Residuen (Messwert − Vorhersage) von 490 Tagen je Station, Vorlauf und Art, mit der Rundungsregel der Stadt ([[Rundung und Auflösung]]).
- Kaufpreis = Preis + halber Spread (0,04) + Gebühr ([[Polymarket Gebühren]]), 10 $ je Wette, höchstens 2 je Event, Wette bei Kante ≥ 0,10, Ja und Nein.

## Ergebnis (Hauptregel, Bestätigungshälfte Juli–Oktober)

| | Wetten | Summe ($) | ohne 3 beste ($) | Brier Modell / Markt | Kriterien |
|---|---|---|---|---|---|
| Vorlauf 1 | 3876 | -1093 | -1951 | 0.0705 / 0.0693 | nicht erfüllt |
| Vorlauf 2 | 2653 | +2780 | +2241 | 0.0713 / 0.0788 | formal erfüllt |

Findungshälfte (März–Juni): Vorlauf 1 -4035 $, Vorlauf 2 -1350 $; Brier Modell gegen Markt 0,0666/0,0589 bzw. 0,0684/0,0627 (Markt besser). Stand nach der Neuberechnung vom 2026-10-14 und der Dallas-Koordinatenkorrektur (siehe unten, Erkenntnis 8). Beide Vorläufe müssen bestehen, Vorlauf 1 tut es nicht.

## Erkenntnisse

1. **Das Modell ist kalibriert, aber nicht besser als der Markt.** Bei Höchstwerten ist der Markt einen Tag vorher sehr effizient. Ein Vorteil müsste aus Information kommen, die der Markt um 18:00 noch nicht hat (neuere Läufe, Ensemble-Streuung).
2. **Der Gewinn der Bestätigungshälfte ist ein Preis-Artefakt.** Er stammt nur aus Nein-Wetten; Tiefsttemperatur-Märkte ab August wurden erst Stunden vor dem Entscheidungszeitpunkt eröffnet und zeigen flache Startpreise (Preissumme bis 2,9). Auf Events mit plausibler Preissumme (0,90–1,15, zum Entscheidungszeitpunkt bekannt) verlieren beide Vorläufe in beiden Hälften (Bestätigung −5 180 $ und −2 188 $).
3. **Look-ahead-Falle bei `previous_day1`:** Die Modelle sind erst ca. 9 h nach Init verfügbar; um 18:00 am Vortag ist der Lauf, der für Nachmittagsstunden in `previous_day1` steckt, noch nicht bekannt. Wir nutzen je Stunde den jüngsten verfügbaren Lauf. Geprüft: 0 Verstöße bei 10 143 Wetten (nach der Neuberechnung unter Einbeziehung aller Interpolations-Stützstellen, siehe Erkenntnis 6).
4. **Gegenrechnung deckte einen Rundungsfehler auf:** Werte liegen auf einem 0,05/0,1-Raster, „x,5“ tritt exakt auf; Gleitkomma-Rauschen entschied verschieden. Mit Toleranz 1e-9 behoben, danach Übereinstimmung auf 2e-12. Lehre: bei Rundungsregeln auf Rastern immer exakte Gleichstände testen.
5. **Preishistorie von Polymarket:** Batch-Endpunkt `POST /batch-prices-history` (max. 20 Tokens); die Reihe wird bei `fidelity = 10` fortgeschrieben (alte Preise sehen aktuell aus). Ein Aufruf je Event, ≈ 4 700 Aufrufe in etwa 2 Stunden ([[Polymarket CLOB]]).
6. **Neuberechnung nach Codex-Review (2026-10-14), zwei Fehler behoben.** (a) Der Zieltag kam aus `endDate`; bei 44 Events im Cache liegt es einen Tag später, in den 15 Städten bei 2 (Seoul, NYC, 15.04.). Jetzt Zieltag aus dem Slug, Preisfenster dieser 2 neu geladen. (b) ECMWF-Stundenwerte sind Catmull-Rom-Interpolationen über vier 3-h-Stützstellen (gemessen: 14 696 von 14 696 Stunden, ≤ 0,08 °C); ein Stundenwert gilt jetzt nur als bekannt, wenn alle Stützstellen aus verfügbaren Läufen stammen (etwa 17 % der ECMWF-Stunden weichen auf einen älteren Lauf aus). Die Gegenrechnung nutzt ein eigenes Zieldatum aus dem Fragetext und leitet die Stützstellen aus den Interpolationsgewichten ab; Übereinstimmung auf 2,5e-12. Wirkung: klein (Vorlauf 1 Bestätigung −729 → −1071 $, Vorlauf 2 +2470 → +2780 $; mit Dallas-Korrektur −1093 $), Urteil unverändert. Klarstellungen: `auswertungen/rueckrechnung_klarstellungen.md`, Regeln unverändert. Lehre: Ein Zeitstempel-Test, der gegen dieselbe Annahme prüft wie die Rechnung (Zieltag, Lauf je Stunde), kann nichts finden; Annahmen am Rohdatum nachmessen. [[Open-Meteo]]
7. **Der Gewinn von Vorlauf 2 ist ein Preis-Artefakt (Zusatzauswertung 2026-10-14, nachträglich).** Von 2 163 Nein-Wetten (Vorlauf 2, Bestätigung, +4 430 $) liegen 1 484 bei Preissumme über 1,10: +4 914 $ (+3,31 $ je Wette, Quote 85,6 %); bei plausibler Preissumme (0,95–1,10) 665 Wetten mit −530 $ (−0,80 $ je Wette, Quote 59,2 %). Das **Alter der Preise ist nicht prüfbar**: Im Cache liegt je Token nur der letzte Rasterpunkt des fortgeschriebenen 10-Minuten-Rasters (Median 9,8 Minuten vor Td, bei 10 123 von 10 143 Wetten unter einer Stunde). Die Zeit seit der letzten Preisänderung bräuchte die Rohreihen (neuer Abruf, ca. 4 700 Aufrufe). **Entscheidung:** Vorlauf 1 verworfen, Vorlauf 2 formal bestanden aber verdächtig, **kein Papierhandel auf Basis der Rückrechnung**. Weiter mit [[Live-Hypothese 1]].
8. **Stationsprüfung (2026-10-14): nur Dallas betroffen.** Die Rückrechnung nutzt IEM-Koordinaten (`daten/cache/koordinaten.json`); gegen `aviationweather.gov` liegen 15 von 16 Stationen höchstens 0,43 km daneben, Dallas (KDAL) 1,8 km (Rasterhöhe 144 statt 146 m). Dallas wurde neu abgerufen und alles neu gerechnet. Wirkung: Vorlauf 1 Bestätigung −1071 → −1093 $ (3875 → 3876 Wetten), Vorlauf 2 in allen Kennzahlen unverändert, Urteil unverändert. Die falschen Koordinaten in `bot/stationen.py` betrafen Städte außerhalb der 15 (Chongqing, Wuhan, Chengdu, Karachi, Qingdao, Shanghai u. a.). [[Stationsprüfung]]

## Grenzen

Keine echten Ensembles, angenommener Spread, keine Markttiefe, Quellenwechsel am 2026-08-23, angenommene Lauf-Verfügbarkeit (10 h), 15 Städte und 7 Monate; Mehrfachvergleiche nicht korrigiert. Das Live-Protokoll ([[Live-Protokoll]]) bleibt die Datenbasis für einen Test mit echten Ensembles.

Siehe auch [[Vorhersagegüte Previous Runs]], [[Rückrechnung Machbarkeit]], [[Ensemble und deterministische Vorhersage]].
