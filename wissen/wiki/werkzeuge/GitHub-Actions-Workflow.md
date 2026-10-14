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
- **Vorschlag, nicht umgesetzt:** externer Auslöser (cron-job.org ruft `workflow_dispatch` über die GitHub-API auf, feingranulares Token nur für dieses Repo, nur „Actions: write“). `concurrency` verhindert Doppelläufe, wenn beide Auslöser parallel laufen. Abwägung steht im Gesprächsprotokoll vom 2026-10-14; Entscheidung beim Projektinhaber.

Siehe [[Live-Protokoll]], [[Einspielregeln]].
