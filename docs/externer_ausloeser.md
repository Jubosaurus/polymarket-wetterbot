# Externer Auslöser (cron-job.org → GitHub `workflow_dispatch`)

Haupttakt des Live-Protokolls. Der GitHub-Cron in `.github/workflows/protokoll.yml` bleibt als Rückfall.
**Das Token liegt nur bei cron-job.org, nie im Repo, nie im Chat, nie in Dateien.**

## a) Fein-granulares GitHub-Token

1. github.com → Profilbild oben rechts → **Settings**.
2. Links ganz unten **Developer settings** → **Personal access tokens** → **Fine-grained tokens**.
3. **Generate new token**.
4. **Token name:** `cron-job-protokoll`.
5. **Expiration:** 90 days (Ablaufdatum notieren, siehe unten).
6. **Resource owner:** `Jubosaurus`.
7. **Repository access:** **Only select repositories** → `polymarket-wetterbot`.
8. **Permissions** → **Repository permissions** → **Actions: Read and write**. Sonst nichts. (`Metadata: Read-only` setzt GitHub automatisch.)
9. **Generate token**. Das Token (`github_pat_…`) wird **nur einmal** angezeigt: sofort kopieren und direkt bei cron-job.org einfügen (Schritt b), nirgends sonst speichern.

## b) cron-job.org

1. Konto anlegen auf cron-job.org (Registrieren, E-Mail bestätigen), einloggen.
2. **CREATE CRONJOB**.
3. Reiter **Common**:
   - **Title:** `Wetterbot Protokoll`
   - **URL:** `https://api.github.com/repos/Jubosaurus/polymarket-wetterbot/actions/workflows/protokoll.yml/dispatches`
   - **Execution schedule:** **User-defined**; **Minutes:** nur 7 und 37 wählen; **Hours:** alle; Tage/Monate: alle. Zeitzone egal (jede Stunde).
   - Haken bei **Enable job**.
   - Haken bei **Notify me when the execution fails** (und optional bei „…when the job is disabled“ / „…after successful run after failure“).
4. Reiter **Advanced**:
   - **Request method:** `POST`
   - **Headers** (je Zeile Name + Wert hinzufügen):
     - `Authorization` = `Bearer github_pat_…` (das Token aus a)
     - `Accept` = `application/vnd.github+json`
     - `X-GitHub-Api-Version` = `2022-11-28`
     - `Content-Type` = `application/json`
   - **Request body:** `{"ref":"main"}`
   - **Timeout** 30 s (Standard) reicht; GitHub antwortet sofort.
   - Unter **Treat redirects with HTTP 3xx status code as success** nichts ändern. Erfolg ist hier **204**; cron-job.org wertet 2xx als Erfolg.
5. **CREATE**.

## c) Test

1. Beim Job **TEST RUN** (oder „Test run“ im Job-Menü) → Ergebnis ansehen: **HTTP-Status 204** (leere Antwort) = Auslöser angenommen.
   - 401: Token falsch/abgelaufen oder Header „Bearer“ fehlt. 403/404: Repo oder Berechtigung „Actions: Read and write“ falsch. 422: `ref` falsch oder Workflow hat kein `workflow_dispatch`.
2. github.com/Jubosaurus/polymarket-wetterbot → **Actions** → **Live-Protokoll**: innerhalb weniger Sekunden erscheint ein neuer Lauf mit „Event: workflow_dispatch“ (von dir ausgelöst).
3. Nach dem ersten echten Termin (:07 oder :37) im Job-**History**-Reiter prüfen, dass der Status 204 ist, und in Actions, dass ein Lauf entstanden ist.
4. Über ein, zwei Tage: Lücken im Laufzeit-Log sollten ≤ ca. 35 Minuten sein.

## Betrieb

- **Token-Ablauf:** nach 90 Tagen endet das Token. Ablaufdatum eintragen (Kalender-Erinnerung ca. 7 Tage vorher). Erneuern: GitHub → Developer settings → Fine-grained tokens → Token → **Regenerate**, neuen Wert bei cron-job.org im Header `Authorization` ersetzen. GitHub schickt außerdem Ablauf-Mails.
- Fällt der Auslöser aus, greift der GitHub-Cron weiter (unregelmäßiger).
- Doppelläufe: Beide Auslöser feuern zu :07/:37. `concurrency: protokoll` reiht den zweiten Lauf hinter den ersten, er läuft dann zusätzlich und kurz (neue Daten gibt es kaum). Harmlos, aber unnötige Läufe. Mögliche Abhilfe wäre, den GitHub-Cron zu versetzen (Änderung an der Workflow-Datei, nur nach Absprache und mit Review).
