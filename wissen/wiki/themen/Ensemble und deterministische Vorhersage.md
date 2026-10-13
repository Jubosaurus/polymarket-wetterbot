---
typ: thema
tags: [thema, wetter]
stand: 2026-10-13
---
# Ensemble und deterministische Vorhersage

- **Ensemble** (143 Mitglieder aus vier Modellen) liefert direkt eine Verteilung, ist aber meist zu eng (zu sicher) und hat Bias gegenüber der Station. Roh-Wahrscheinlichkeiten sind eine Ausgangsbasis, noch kein Handelssignal.
- **Deterministische Previous Runs** gibt es historisch (seit 2024), echte Ensembles nicht ([[Open-Meteo]]). Eine Rückrechnung muss die Verteilung aus der historischen Fehlerverteilung bauen und ist damit ein anderes Modell als das Live-Ensemble ([[Rückrechnung Machbarkeit]]).
- Deshalb sammelt das [[Live-Protokoll]] die Rohwerte aller Mitglieder: Bias-/Streuungskorrektur und Pooling lassen sich später beliebig ändern, ohne dass Daten fehlen.
- Pooling im Protokoll: gleiches Gewicht je Mitglied über die jüngsten Läufe aller Modelle (ECMWF 51, GEFS 31, ICON 40, GEM 21). Das ist eine Setzung, keine Optimierung.

Güte der Basis: [[Vorhersagegüte Previous Runs]].
