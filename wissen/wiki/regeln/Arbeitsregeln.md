---
typ: regel
tags: [regel]
stand: 2026-10-13
---
# Arbeitsregeln

Quelle: `CLAUDE.md` im Repo. (Die im Auftrag genannte Datei `docs/projekt_start.md` existiert im Repo nicht; die Regeln stammen aus `CLAUDE.md` und den Auftragstexten, siehe [[log]].)

- **Eigenes Projekt**, getrennt vom Memecoin-Bot. Dessen Ordner/Repo nie anfassen.
- **Nur Papierhandel.** Keine Wallet, keine privaten Schlüssel, keine Signatur, keine Orders, keine authentifizierten Endpunkte. Nur öffentliche, lesende APIs.
- Keine Schlüssel/`.env` im Repo (`.gitignore`). Bräuchten wir je einen, kommt er aus einer Umgebungsvariable.
- Phase 0 hatte keinen Handels-Bot und keine Zeitpläne. Das Live-Protokoll ([[Live-Protokoll]]) hat einen Zeitplan, aber nur zum Protokollieren: **keine Wetten**.
- **Speicher ist knapp:** alles nacheinander, keine parallelen Hintergrundläufe, keine großen Downloads ohne Rückfrage.
- **Jede Entscheidung und Erkenntnis kommt ins Wiki und in [[log]].**

Siehe auch [[Testregeln]], [[Einspielregeln]].
