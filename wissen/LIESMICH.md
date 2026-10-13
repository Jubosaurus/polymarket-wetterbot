# Liesmich: Wissensablage Polymarket-Wetterbot

Dieser Ordner (`wissen/`) ist ein **eigener Obsidian-Vault**. Er sammelt, was wir über Polymarket-Wettermärkte, Datenquellen und unsere Experimente herausgefunden haben, damit nichts nur in Chatverläufen steckt.

## Aufbau

| Ort | Inhalt |
|---|---|
| [[index]] | Inhaltsverzeichnis aller Seiten |
| [[log]] | Tagebuch: Datum, Entscheidung oder Erkenntnis (neueste unten) |
| [[REGELN]] | Wie Seiten in diesem Vault geschrieben werden |
| `wiki/staedte/` | eine Seite je Stadt (Station, Quelle, Einheit, Rundung, Zeitzone, Besonderheiten), Einstieg [[Städteübersicht]] |
| `wiki/quellen/` | je Datenquelle: Zugriff, Grenzen, Fallstricke ([[Polymarket Gamma]], [[Polymarket CLOB]], [[Open-Meteo]], [[METAR (IEM)]], [[HKO Open Data]], [[Polymarket Gebühren]]) |
| `wiki/regeln/` | Test-, Arbeits- und Einspielregeln ([[Arbeitsregeln]], [[Testregeln]], [[Einspielregeln]]) |
| `wiki/experimente/` | was wir ausprobiert haben, mit Zahlen und Ergebnis |
| `wiki/werkzeuge/` | Code-Module, Workflow, Umgebung ([[Bot-Module]]) |
| `wiki/themen/` | übergreifende Zusammenhänge ([[Rundung und Auflösung]], [[Stationswechsel]], [[Live-Protokoll]] …) |

## Kurzstand

- Projekt: Papierhandel auf Polymarket-Wettermärkten, **keine Wallet, keine Schlüssel, keine echten Orders**.
- Phase 0 (Machbarkeit) abgeschlossen: [[Machbarkeit Phase 0]].
- Phase 1a (Live-Protokoll) läuft als GitHub-Actions-Job: [[Live-Protokoll]].
- Phase 1b (Rückrechnung) folgt als eigener Auftrag: [[Rückrechnung Machbarkeit]].

Das Repo-Dokument `docs/machbarkeit.md` ist die ausführliche Quelle der ersten Studie; die Seiten hier sind die gepflegte, verlinkte Fassung.

## Benutzung

Vault öffnen: Obsidian → „Ordner als Vault öffnen“ → `wissen/`. Die Obsidian-Einstellungen (`.obsidian/`) sind nicht im Git. Siehe [[Obsidian-Vault]].
