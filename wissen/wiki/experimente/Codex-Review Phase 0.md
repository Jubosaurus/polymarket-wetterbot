---
typ: experiment
tags: [experiment, review]
stand: 2026-10-13
---
# Codex-Review der Phase 0 (2026-10-13)

Verdikt „needs-attention“, drei berechtigte Befunde, alle behoben und mit Tests abgedeckt:

1. **Validierung nutzte die heutige Station für alte Events** → Station je Event aus dem Auflösungstext ([[Stationswechsel]]).
2. **Angehängte Schnappschüsse (`--anhaengen`) wurden mit der frischen Vorhersage gepaart** (Look-ahead) → nur der jüngste Schnappschuss je Event, Zeitstempel mitgeführt.
3. **Fehlende Spitzenstunden ergaben falsche Tagesextremwerte** (20-Stunden-Schwelle) → Mitglied zählt nur mit allen Stundenwerten, Ausschlüsse werden gezählt.

Die Korrekturen wurden mit dem Live-Protokoll erneut zur Prüfung vorgelegt. Siehe [[Einspielregeln]], [[Codex-Review]].
