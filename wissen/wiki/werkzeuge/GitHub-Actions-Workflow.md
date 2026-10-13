---
typ: werkzeug
tags: [werkzeug, github]
stand: 2026-10-13
---
# GitHub-Actions-Workflow „Live-Protokoll“

Datei `.github/workflows/protokoll.yml`.

- `cron: "*/30 * * * *"` plus `workflow_dispatch`. GitHub verschiebt oder überspringt geplante Läufe gelegentlich; Lücken stehen im Laufzeit-Log.
- `concurrency: group: protokoll, cancel-in-progress: false`: nie zwei Läufe gleichzeitig.
- `timeout-minutes: 15`; das Programm hat ein internes Zeitbudget von 13 Minuten.
- `permissions: contents: write`; Commit je Lauf mit `[skip ci]`, auch nach fehlgeschlagenem Lauf (`if: always()`), damit das Log die Lücke zeigt.
- Keine Secrets. Das Repo ist öffentlich.
- GitHub deaktiviert geplante Workflows nach 60 Tagen ohne Repo-Aktivität; die Protokoll-Commits zählen als Aktivität.

Siehe [[Live-Protokoll]], [[Einspielregeln]].
