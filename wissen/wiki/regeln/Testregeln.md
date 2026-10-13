---
typ: regel
tags: [regel, test]
stand: 2026-10-13
---
# Testregeln

- `pytest` muss grün sein, bevor etwas eingespielt wird: `.venv\Scripts\python -m pytest -q`.
- Tests laufen **offline** (Netzwerk per Attrappe ersetzt, z. B. `FakeApi` in `tests/test_protokoll.py`). Live-Prüfungen sind eigene Skripte unter `auswertungen/`.
- Jede Fehlerbehebung bekommt einen Test, der vorher fehlschlägt. (In Phase 0 fand ein Test einen echten Fehler: vertauschte Spalten bei unbekannter Stadt.)
- Rechenkern (Bucket-Parser, Rundung, Wahrscheinlichkeiten) braucht Grenzfälle: offene Ränder, negative Werte, x,5, HKO-Abschneiden.
- Zu lasche Assertions vermeiden („oder“-Bedingungen, riesige Toleranzen): beim Protokoll-Test wurden zwei solche nachgeschärft.

Siehe [[Arbeitsregeln]], [[Einspielregeln]].
