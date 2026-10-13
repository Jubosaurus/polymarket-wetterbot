---
typ: werkzeug
tags: [werkzeug, code]
stand: 2026-10-13
---
# Bot-Module (`bot/`)

| Modul | Aufgabe |
|---|---|
| `stationen.py` | Stadt → Station (ICAO), Zeitzone, Koordinaten, Rundungsregel. Siehe [[Städteübersicht]] |
| `buckets.py` | Bucket-Parser, Rundung (`kaufm` / `abschneiden`), Wahrscheinlichkeit je Bucket |
| `maerkte.py` | aktive Wettermärkte, Orderbuch (CLOB `/books`), Gebührenfelder → `daten/maerkte.csv` |
| `wetter.py` | Phase-0-Ensemble → Bucket-Wahrscheinlichkeit (Roh-Ensemble, ohne Korrektur) |
| `ensemble.py` | Modelllauf-Erkennung, Tageswerte aller Mitglieder je Modell, Pooling |
| `aufloesung.py` | METAR-Tageswert und Gewinner je abgelaufenem Markt, Abweichungen markieren |
| `speicher.py` | Tagesordner, csv.gz atomar schreiben, Zustand |
| `protokoll.py` | Orchestrierung eines Laufs, Laufzeit-Log, Budgets |
| `netz.py` | HTTP mit Wiederholung, Warten bei „Minutely limit“ |

Aufruf: `python -m bot.protokoll`. Siehe [[Live-Protokoll]], [[Testregeln]].
