---
typ: experiment
tags: [experiment, hypothese, live-protokoll]
stand: 2026-10-14
---
# Live-Hypothese 1: Nein-Wetten, echte Ensembles, echter Ask

**Status:** vorab festgeschrieben am 2026-10-14 (Commit `e94b608`, vor Auswerteskript und vor jeder Auswertung); am selben Tag **vor Datenbeginn** überarbeitet (eigener Commit darüber, Abschnitt „Änderungen vor Datenbeginn“ in der Regeldatei, siehe unten). Regeln: `auswertungen/live_hypothese_1.md` (nicht mehr ändern), Stationskorrektur: `auswertungen/live_bias.json` (berechnet mit `auswertungen/live_bias.py`), Auswerteskript: `auswertungen/live_auswertung.py` (nur Auswertung, keine Wett-Logik im Bot).

**Frage:** Haben Nein-Wetten bei etwa zwei Tagen Vorlauf (Entscheidung 18:00 Ortszeit, Zieltag − 2) nach Kosten einen Erwartungswert über null, wenn die Wahrscheinlichkeit aus den **echten Ensembles** des Protokolls (mit Bias-Korrektur) gegen den **echten Ask** (Nein-Ask = 1 − Ja-Bid) eine Kante von mindestens 0,10 zeigt und die Tiefe an der Spitze für 10 $ reicht?

## Festlegungen (Kurzfassung)

- **Alle 48 Stationen** der Tabelle mit METAR-Reihe (192 Zellen Station × Vorlauf × Art, jeweils 457–490 Tage 2024–2025; Hong Kong entfällt: keine METAR-Reihe), Zieltag ab 2026-10-16 und Entscheidung nicht vor `auswertungen/live_start.txt` (Beginn des Protokolls mit korrigierten Koordinaten). Entscheidungs-Schnappschuss = erster Protokoll-Lauf ab Td, höchstens 60 min später (sonst „Lücke“, gezählt).
- Ensemble: je Modell der jüngste Empfang bis zum Schnappschuss (kein Blick in die Zukunft), alle Modelle gepoolt, gleiches Gewicht je Mitglied, **nur Bias** aus der Fehlerverteilung 2024–2025 (Streuung bleibt die des Ensembles, sonst doppelt gezählt).
- Kosten: Ask + Taker-Gebühr `0,05·q·(1−q)`, 10 $ inklusive Gebühr, Tiefe an der Spitze ≥ Anteile, keine Teilfüllung, höchstens 2 Wetten je Event.
- Auswertung **einmal**, wenn die ersten **200** Hauptwetten (Nein, Vorlauf 2, nach Td) aufgelöst sind. Bestätigt nur, wenn Gewinn je Wette > 0, Summe ohne die 3 besten > 0 und Summe > 0 in beiden Hälften (nach Zeit). Bis dahin nur Zählstände, kein Zwischenstand-Tuning.
- Zum Vergleich (keine Entscheidungsgrundlage): Ja-Wetten Vorlauf 2, Nein und Ja Vorlauf 1, **Nein mit auf die Residuenstreuung aufgeweitetem Ensemble**, **Blind-Nein** (Ja-Ask ≤ 0,10, ohne Modell).

## Änderungen vor Datenbeginn (2026-10-14)

1. **Falsche Koordinaten** in `bot/stationen.py` (Stadtmitten statt Flughäfen, bis 40 km daneben, siehe [[Stationsprüfung]]): korrigiert; `live_bias.json` mit den korrigierten Koordinaten für alle Stationen neu berechnet (die 60 Zellen der 15 alten Städte stimmen bis auf Dallas bis auf 4 Stellen mit der ersten Fassung überein, ein Nachweis, dass Rechnung und Daten reproduzierbar sind). Ensemble-Abrufe aus der Zeit vor der Korrektur zählen nicht (`live_start.txt`, im Skript erzwungen).
2. **Erweiterung auf alle Städte** mit mindestens 300 Tagen Daten; ausgeschlossen: nur Hong Kong.
3. **Vergleichszeilen** aufgeweitetes Ensemble und Blind-Nein ergänzt.
4. Der alte Commit `e94b608` bleibt unverändert im Verlauf.

## Auslegung im Skript

Der Text lässt offen, ob die Tiefe vor oder nach der Wahl der zwei größten Kanten geprüft wird. Das Skript wählt zuerst die zwei größten Kanten und prüft danach die Tiefe; eine Wette ohne Tiefe entfällt ersatzlos (vorsichtigere Auslegung). Der Zählstand führt die Ausfälle mit (`ohne_tiefe_…`).

**Zieltag:** aus dem Slug (`...-on-april-15-2026`), nicht aus dem Datum im Stamm; das Protokoll nimmt bei fehlendem `eventDate` das `endDate`, das bei einzelnen Events einen Tag später liegt (Fund des gemeinsamen Codex-Reviews, behoben, Test vorhanden). Abweichungen stehen im Zählstand (`zieltag_weicht_vom_stamm_ab`); für solche Events fehlt das Ensemble des richtigen Tages, sie entfallen dann als „zu wenig Modelle“.

## Bekannte Schwächen (vorab genannt)

200 korrelierte Wetten sind wenig; nur Bias-Korrektur (Ensembles oft zu eng); Bias stammt von zwei deterministischen Modellen; größere Ensembles zählen stärker; Protokoll-Lücken; keine Marktwirkung der eigenen Order.

Siehe [[Rückrechnung]], [[Live-Protokoll]], [[GitHub-Actions-Workflow]], [[Polymarket Gebühren]].
