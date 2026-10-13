# Regeln für Seiten in diesem Vault

1. **Sprache:** Deutsch, sachlich, kurz. Zahlen mit Einheit und Zeitraum.
2. **Eine Seite = ein Thema.** Dateiname = Titel (`Open-Meteo.md` → `# Open-Meteo`). Links immer in doppelten eckigen Klammern mit dem Dateinamen (ohne `.md`); Anzeigetext nur bei Bedarf mit senkrechtem Strich.
3. **Kopfblock (Frontmatter)** mit `typ` (`stadt`, `quelle`, `regel`, `experiment`, `werkzeug`, `thema`, `uebersicht`), `tags` und `stand` (Datum der letzten Prüfung, `JJJJ-MM-TT`).
4. **Ablage nach Typ:** Städte → `wiki/staedte/`, Datenquellen → `wiki/quellen/`, Regeln → `wiki/regeln/`, Experimente → `wiki/experimente/`, Werkzeuge → `wiki/werkzeuge/`, Zusammenhänge → `wiki/themen/`.
5. **Verknüpfen:** Jede neue Seite verlinkt mindestens auf verwandte Seiten und wird in [[index]] eingetragen. Keine Waisenseiten.
6. **Belegen:** Behauptungen mit Zahl, Datum und Fundort (Skript, API, Doku-URL). **Gemessen** und **vermutet** trennen; Ungeprüftes ausdrücklich „nicht geprüft“ nennen.
7. **Experimente** nennen Frage, Vorgehen (Skript/Zeitraum), Ergebnis (Tabelle) und Folgerung.
8. **Kein Geheimnis ins Wiki:** keine Schlüssel, keine Zugangsdaten, keine Wallet-Angaben. Das Wiki liegt in einem öffentlichen Repo.
9. **Pflege:** Jede Entscheidung und Erkenntnis kommt ins Wiki **und** als Zeile in [[log]] (Datum – was – wo nachzulesen). Ändert sich eine Tatsache, die Seite aktualisieren (`stand` anheben), nicht eine zweite danebenlegen.
10. **Städteseiten** werden aus `bot/stationen.py` und `docs/machbarkeit.md` erzeugt; handgeschriebene Abschnitte (Besonderheiten) bei einer Neuerzeugung nicht verlieren.

Siehe [[LIESMICH]], [[Arbeitsregeln]].
