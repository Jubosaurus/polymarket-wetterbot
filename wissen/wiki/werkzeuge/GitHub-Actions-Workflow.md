---
typ: werkzeug
tags: [werkzeug, github]
stand: 2026-10-14
---
# GitHub-Actions-Workflow „Live-Protokoll“

Datei `.github/workflows/protokoll.yml`.

- `cron: "7,37 * * * *"` (seit 2026-10-14; vorher `*/30 * * * *`) plus `workflow_dispatch`. GitHub verschiebt oder überspringt geplante Läufe; Lücken stehen im Laufzeit-Log.
- `concurrency: group: protokoll, cancel-in-progress: false`: nie zwei Läufe gleichzeitig.
- `timeout-minutes: 15`; das Programm hat ein internes Zeitbudget von 13 Minuten.
- `permissions: contents: write`; Commit je Lauf mit `[skip ci]`, auch nach fehlgeschlagenem Lauf (`if: always()`), damit das Log die Lücke zeigt.
- Keine Secrets. Das Repo ist öffentlich.
- GitHub deaktiviert geplante Workflows nach 60 Tagen ohne Repo-Aktivität; die Protokoll-Commits zählen als Aktivität.

## Befund 2026-10-14: Zeitplan läuft kaum (gemessen)

- Seit dem ersten manuellen Lauf (2026-10-13 21:06 UTC) liefen über Nacht nur **zwei** Läufe statt ca. 16: 21:06 (manuell) und 00:29 (Zeitplan), Lücke 203 min. Danach bis zum manuellen Start um 05:08 UTC kein Lauf mehr (weitere 279 min). Quelle: `gh run list`.
- **Vermutet, nicht belegt:** Geplante Läufe zur vollen und halben Stunde sind bei GitHub besonders überlastet und werden verzögert oder verworfen; zudem hat GitHub für geplante Läufe keine Zusage. Ob ein junges Repo zusätzlich benachteiligt wird, ist unbekannt.
- **Maßnahme:** Start auf ungerade Minuten (7 und 37) verlegt. Wirkung steht aus und wird an der Lückenverteilung der nächsten Tage gemessen.
- **Entscheidung 2026-10-14 (Projektinhaber): externer Auslöser wird Haupttakt.** Grund (gemessen): seit der Cron-Umstellung (~05:10 UTC) nur ein geplanter Lauf in 5½ h (10:34, Lücke 326 min); so werden die meisten Entscheidungszeitpunkte der Hypothese verpasst. cron-job.org ruft zu :07 und :37 `workflow_dispatch` über die GitHub-API auf. Anleitung: `docs/externer_ausloeser.md`.
- **Sicherheit:** Fein-Token nur für dieses Repo, nur „Actions: Read and write“, Ablauf 90 Tage. Es liegt **nur bei cron-job.org**, nie im Repo. **Erinnerung:** vor Ablauf erneuern (Regenerate, Header bei cron-job.org ersetzen); Ablaufdatum beim Anlegen notieren. Fällt der Auslöser aus, läuft nur der GitHub-Cron (Rückfall).
- GitHub-Cron und `concurrency` bleiben unverändert; die Workflow-Datei wurde dafür nicht geändert. Beide Auslöser feuern zu :07/:37, der zweite Lauf wird per `concurrency` angehängt (harmlose Doppelung; Versetzen des Cron wäre eine Workflow-Änderung mit Review, nicht umgesetzt).
- **Wirkung steht aus:** Lückenverteilung nach Einrichtung messen (Erwartung ≤ ca. 35 min).

## Offene Punkte (zurückgestellt, 2026-10-14)

- **Zieltag überall aus dem Slug** (`...-on-april-15-2026`), `eventDate`/`endDate` nur noch zum Abgleich: in `bot/maerkte.py` (`_datum`, heute `eventDate`, sonst `endDate[:10]`), im Ensemble-Abruf (Zuordnung über den Stamm) und in `bot/aufloesung.py` (heute `endDate[:10]`). Beobachtet ist der Fehler im Protokoll nicht (0 von 328 Events, alle mit `eventDate`; siehe `auswertungen/2026-10-14_zieltag_zaehlung.md`), es ist ein Rückfallrisiko und Aufräumen.
- **Umsetzung gemeinsam mit der nächsten Workflow-Änderung**, die ohnehin einen Review braucht (der externe Auslöser ist keine, siehe oben), damit es nur einen Review gibt. Vorher dem Nutzer sagen, ab wann es gilt und ob `auswertungen/live_start.txt` verschoben werden muss (nach heutigem Stand nicht nötig).

Siehe [[Live-Protokoll]], [[Einspielregeln]].
