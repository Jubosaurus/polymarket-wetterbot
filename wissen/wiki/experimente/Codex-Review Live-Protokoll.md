---
typ: experiment
tags: [experiment, review, protokoll]
stand: 2026-10-13
---
# Codex-Review des Live-Protokolls (2026-10-13)

Verdikt „needs-attention“. Alle acht Befunde waren sachlich berechtigt und wurden behoben (Tests in `tests/test_protokoll.py`):

| Befund | Schwere | Behebung |
|---|---|---|
| Offene HKO-Auflösungen fielen nach 6 Tagen aus dem Rückblick und gingen verloren | hoch | Dauerhafte Offen-Liste in `zustand.json` (bis 60 Tage), Nachprüfung per Slug ([[Hongkong]], [[HKO Open Data]]) |
| Leere (`null`) Ensemble-Antworten zählten als erfasst; 45 von 49 Stationen genügten dauerhaft | hoch | Station zählt nur mit verwertbaren Werten je Modell; Wiederholung, nach 3 Versuchen ab 90 % |
| Initialisierungszeit beweist keine Verfügbarkeit | hoch | Verfügbarkeitszeit plus 10 Minuten Sicherheitsabstand; sonst `lauf_sicher = 0` ([[Open-Meteo]]) |
| Auflösungsabrufe konnten das ganze Job-Limit verbrauchen | hoch | Gemeinsame Frist (11 min) für alle Abrufe, Wiederholungen und Wartezeiten (`bot/netz.py`) |
| Push-Konflikte oder -Ausfälle vernichteten die Läufe | hoch | `pull --rebase -X theirs`, Rebase-Abbruch, 4 Versuche, Artefakt-Sicherung bei Fehler ([[GitHub-Actions-Workflow]]) |
| Ensemble-Verfügbarkeit auf den früheren Marktzeitpunkt zurückdatiert (Look-ahead) | hoch | `empfangen_utc` je Station, `verfuegbar_ab_utc` bei den Wahrscheinlichkeiten ([[Live-Protokoll]]) |
| ICON-EU-Laufzeit wurde auch dem globalen ICON zugeschrieben | mittel | `lauf_details` nennt beide Datensätze; verschiedene Läufe ⇒ `lauf_sicher = 0` |
| Tageslimit zählte HTTP-Aufrufe statt Verbrauch | mittel | Geschätztes Gewicht (Summe angefragter Modelle); bei „Daily limit“ Pause bis 00:05 UTC |

**Lehre:** Der Plan „Meta-Datei zeigt neuen Lauf ⇒ Lauf erfasst“ war zu naiv; Erfassung muss an gespeicherte, verwertbare Daten gebunden sein, nicht an eine HTTP-Antwort. Siehe auch [[Codex-Review Phase 0]], [[Einspielregeln]].
