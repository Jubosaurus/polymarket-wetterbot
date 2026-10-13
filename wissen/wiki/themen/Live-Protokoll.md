---
typ: thema
tags: [thema, protokoll]
stand: 2026-10-13
---
# Live-Protokoll (Phase 1a)

Sammeln ohne Handeln. GitHub-Actions-Lauf alle 30 Minuten ([[GitHub-Actions-Workflow]]), Commit je Lauf. Begründung: Echte Ensemble-Vorhersagen lassen sich nicht nachträglich beschaffen, jeder Tag ohne Protokoll ist verloren.

- Märkte: Bid/Ask/Tiefe/letzter Preis, Gebührenregel je Marktversion ([[Polymarket Gebühren]]).
- Ensemble nur bei **neuem Modelllauf**, mit allen Mitgliedswerten; ICON-Rückfall auf 6-h-Raster, weil die Meta veraltet ist ([[Open-Meteo]]).
- Wahrscheinlichkeit je Bucket nach jedem Ensemble-Update.
- Täglich: METAR-Tageswert und Gewinner, Abweichungen markiert.
- Laufzeit-Log mit Lücken, Abfragezählern, Größen.
- Robustheit (nach [[Codex-Review Live-Protokoll]]): gemeinsame Frist für alle Abrufe, Erfassung nur mit verwertbaren Werten, dauerhafte Offen-Liste für Auflösungen, Tageslimit-Pause, Push mit Rebase-Strategie und Artefakt-Sicherung.
- Look-ahead: Wahrscheinlichkeiten tragen `verfuegbar_ab_utc`; nur mit Preisen danach verbinden.
- Größe: ca. 2–2,5 MB/Tag erwartet ([[Probelauf Live-Protokoll]]); im Auge behalten.

Volle Dateibeschreibung: `docs/protokoll.md`. Module: [[Bot-Module]]. Regeln: [[Arbeitsregeln]] (keine Wetten).
