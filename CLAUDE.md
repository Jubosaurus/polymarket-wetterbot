# Polymarket-Wetterbot (Papierhandel)

Eigenständiges Projekt, **völlig getrennt vom Memecoin-Bot**. Den Memecoin-Ordner/-Repo nie anfassen, nichts von dort importieren oder kopieren, was Schlüssel, Konfiguration oder Zustand betrifft.

## Harte Regeln

- **Nur Papierhandel.** Keine Wallet, keine privaten Schlüssel, keine Signatur, kein Senden von Orders, keine authentifizierten Polymarket-Endpunkte. Es werden nur öffentliche, lesende APIs genutzt (Gamma, CLOB-Lesen, Open-Meteo, IEM).
- Keine Schlüssel, keine `.env`, keine Zugangsdaten im Repo (siehe `.gitignore`). Brauchen wir je einen API-Schlüssel, kommt er aus einer Umgebungsvariable und nie ins Repo.
- **Kein Handels-Bot, keine Wetten.** Einziger Zeitplan ist der Workflow `.github/workflows/protokoll.yml` (Live-Protokoll, nur Sammeln). **Haupttakt: externer Auslöser** (cron-job.org ruft `workflow_dispatch` per GitHub-API zu :07/:37 auf, Anleitung `docs/externer_ausloeser.md`); der GitHub-Cron ist nur Rückfall. Das Fein-Token (nur dieses Repo, nur „Actions: Read and write“, 90 Tage) liegt **ausschließlich bei cron-job.org**, nie im Repo/Chat/Dateien; Ablauf rechtzeitig erneuern. Sonst kein Cron, keine Dauerschleife, kein Hintergrunddienst.
- **Speicher ist knapp:** alles nacheinander ausführen, keine parallelen Hintergrundläufe, keine großen Rohdaten-Downloads ohne Rückfrage. Protokolldaten liegen in `daten/` (vom Workflow eingecheckt); lokale Phase-0-Dateien (`daten/maerkte.csv`) nicht.

## Wissensablage (Pflicht)

- `wissen/` ist ein eigener Obsidian-Vault (Aufbau: `wissen/LIESMICH.md`, Schreibregeln: `wissen/REGELN.md`).
- **Jede Entscheidung und jede Erkenntnis kommt ins Wiki (`wissen/wiki/…`) und als Zeile in `wissen/log.md`**, im selben Commit wie die Änderung. Neue Seiten in `wissen/index.md` eintragen und verlinken. Gemessenes und Vermutetes trennen.

## Testregeln

- `pytest` muss grün sein, bevor etwas eingespielt wird: `.venv\Scripts\python -m pytest -q`.
- Tests laufen **offline** (Netzwerk wird per Stub/Fixture ersetzt). Live-Prüfungen sind eigene Skripte unter `auswertungen/`.
- Jede Fehlerbehebung bekommt einen Test, der vorher fehlschlägt.
- Rechenkern (Bucket-Parser, Rundung, Wahrscheinlichkeiten) braucht Grenzfälle: offene Ränder, negative Werte, x.5, HKO-Abschneiden.

## Einspielen

1. Tests grün.
2. Prüfung durch Codex vor dem Einspielen: `/codex:adversarial-review` (wie im Memecoin-Projekt). Befunde bewerten, berechtigte beheben, Tests erneut laufen lassen.
3. Erst dann committen und pushen. Commits mit klarer deutscher Beschreibung.

## Aufbau

- `bot/` Module: `stationen.py` (Stadt -> Station/Zeitzone/Rundung), `buckets.py` (Parser, Rundung, Wahrscheinlichkeit), `maerkte.py` (aktive Märkte -> `daten/maerkte.csv`), `wetter.py` (Phase-0-Ensemble -> Wahrscheinlichkeit), `ensemble.py`, `aufloesung.py`, `speicher.py`, `protokoll.py` (Live-Protokoll), `netz.py` (HTTP mit Wiederholung).
- `daten/JJJJ-MM-TT/` Protokolldaten (csv.gz) und `daten/zustand.json`, werden vom Workflow eingecheckt; Format in `docs/protokoll.md`. `auswertungen/` Prüf- und Analyseskripte. `docs/` Dokumentation (`machbarkeit.md`, `gebuehren.md`, `protokoll.md`). `tests/` pytest.
- Aufruf: `python -m bot.protokoll` (ein Protokoll-Lauf), `python -m bot.maerkte` / `python -m bot.wetter` (Phase 0, lokale CSV).

## Wissenswertes zur Auflösung (Details in docs/machbarkeit.md)

- Je Event steht die Station im Auflösungstext; sie hat sich bei Paris (LFPG -> LFPB) und Denver (KDEN -> KBKF) geändert. Für Rückrechnung die Station je Event aus dem Text lesen, nicht aus der aktuellen Tabelle.
- Hong Kong (HKO) schneidet auf ganze Grad **ab**; alle anderen Stationen runden kaufmännisch.
- Tag = lokaler Kalendertag der Station.
