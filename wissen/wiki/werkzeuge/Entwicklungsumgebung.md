---
typ: werkzeug
tags: [werkzeug]
stand: 2026-10-13
---
# Entwicklungsumgebung

- Windows 11, Python 3.11, eigene venv in `.venv/` (nicht im Git), `requirements.txt`: `requests`, `numpy`, `tzdata`, `pytest`.
- `tzdata` ist nötig, weil Windows keine IANA-Zeitzonen mitbringt (`zoneinfo`).
- Tests: `.venv\Scripts\python -m pytest -q`. Siehe [[Testregeln]].
- Kurze Heredocs in der Git-Bash scheiterten mehrfach an Sonderzeichen; längere Dateien lieber mit dem Schreibwerkzeug anlegen.
