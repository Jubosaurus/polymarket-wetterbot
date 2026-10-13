# Live-Protokoll (Phase 1a)

Ein GitHub-Actions-Workflow (`.github/workflows/protokoll.yml`) ruft alle 30 Minuten `python -m bot.protokoll` auf und committet die Ergebnisse (`[skip ci]`). **Es wird nichts gehandelt**, es gibt keine Schlüssel.

## Ablauf je Lauf (nacheinander)

1. **Märkte:** alle aktiven Wettermärkte (Temperatur, Niederschlag): bestes Bid/Ask mit Größe an der Spitze, letzter Preis, Zeitstempel des Buchs, Gebührenregel aus der API.
2. **Ensemble:** Open-Meteo-Meta (`last_run_initialisation_time`) je Modell prüfen. Nur für Modelle mit **neuem Lauf** wird je Station abgerufen (ein Abruf je Station mit allen neuen Modellen). Gespeichert werden die Tageswerte (Max/Min) **aller Ensemble-Mitglieder** je Modell, Modelllauf, Vorlaufzeit.
3. **Wahrscheinlichkeiten:** nach einem Ensemble-Update je Bucket (gepoolt über die jüngsten Läufe aller Modelle, gleiches Gewicht je Mitglied, Rundungsregel der Station).
4. **Auflösung:** ab 07:00 UTC, höchstens alle 12 h: für abgelaufene Märkte (Rückblick 6 Tage) METAR-Tageswert (IEM) und Polymarket-Gewinner; Abweichung = `treffer 0`. Hong Kong über HKO-Open-Data (abgeschnitten), sobald dort veröffentlicht.
5. **Laufzeit-Log** mit Start, Ende, Dauer, **Lücke zum vorigen Lauf**, Abfragezählern, Größen, Fehlern.

Lücken durch ausgefallene Läufe sind erlaubt und im Log sichtbar (`luecke_min` deutlich über 30; fehlende `maerkte_HHMM`-Dateien). GitHub verschiebt oder überspringt geplante Läufe gelegentlich.

## Dateien unter `daten/JJJJ-MM-TT/` (UTC-Tag des Laufs)

| Datei | Inhalt | Wann |
|---|---|---|
| `maerkte_HHMM.csv.gz` | `idx, bid, ask, bid_groesse, ask_groesse, letzter_preis, preis_mitte, spread` je Bucket | jeder Lauf |
| `maerkte_stamm_HHMM.csv.gz` | Stammdaten **nur neue/geänderte** Marktversionen: `idx, markt_id, token_yes, event_slug, stadt, station, art, datum, einheit, rundung, bucket, bucket_lo/hi, tick, min_groesse, fees_aktiv, fee_typ, fee_rate, fee_exponent, fee_nur_taker, fee_rebate, ende_utc, gesehen_utc` | bei neuen Märkten oder Regeländerung |
| `ensemble_HHMM.csv.gz` | `abruf_utc` (Lauf-Start), `empfangen_utc` (Eingang der Antwort je Station), `stadt, icao, modell, modell_lauf_utc, lauf_details, lauf_sicher, datum, art, vorlauf_h, n_member, ausgeschlossen, werte_c` (Werte aller Mitglieder, getrennt durch Leerzeichen, °C) | wenn ein Modell einen neuen Lauf hat |
| `wahrscheinlichkeiten_HHMM.csv.gz` | `idx, p_modell, n_member, laeufe, verfuegbar_ab_utc` | nach Ensemble-Update |
| `aufloesung.csv.gz` | `event_slug, stadt, art, datum, icao, einheit, gewinner_bucket, messwert, messquelle, n_beobachtungen, treffer, bemerkung` | täglich, nur neue Events |
| `laufzeit.csv` | ein Eintrag je Lauf (siehe unten) | jeder Lauf |
| `../zustand.json` | zuletzt protokollierter Modelllauf je Modell, Zeit der letzten Auflösungsprüfung, Start des letzten Laufs | jeder Lauf |

**Look-ahead vermeiden:** Eine Wahrscheinlichkeit darf erst mit Preisen verbunden werden, die **nach** `verfuegbar_ab_utc` entstanden sind (Eingang der jüngsten verwendeten Ensemble-Antwort). Der Schnappschuss `maerkte_HHMM` desselben Laufs ist **älter** als diese Wahrscheinlichkeit.

`idx` verbindet Schnappschuss/Wahrscheinlichkeit mit den Stammdaten **desselben Tages**. Ändert sich eine Gebührenregel o. Ä., bekommt der Markt einen neuen `idx`.

`HHMM` ist die UTC-Startzeit des Laufs. `vorlauf_h` = Stunden vom Modelllauf bis zum Beginn des lokalen Zieltages (negativ, wenn der Tag schon läuft).

### Modelllauf-Erkennung und ihre Grenzen

- ECMWF IFS, GEFS, GEM: Meta-Datei des Open-Meteo-Datensatzes (`.../data/<datensatz>/static/meta.json`): Initialisierungs- und Verfügbarkeitszeit.
- **`lauf_sicher = 1` nur, wenn** alle Datensätze des Modells denselben Lauf zeigen, dessen Verfügbarkeit mindestens 10 Minuten zurückliegt (Empfehlung von Open-Meteo) und die Meta vor und nach dem Abruf gleich war. **ICON** besteht aus globalem (12-stündlich) und EU-Datensatz (6-stündlich); zeigen sie verschiedene Läufe, ist `lauf_sicher = 0` und `lauf_details` nennt beide Läufe. Auch dann bleibt unbelegt, welcher Datensatz an einer Station gerade die Werte liefert.
- **ICON-Meta war am 2026-10-13 veraltet** (Stand 6.10., obwohl frische Daten kamen). Ist die Meta älter als 48 h oder nicht lesbar, gilt ein **6-Stunden-Raster** mit Kennzeichen `~` (z. B. `2026-10-13T18:00Z~`), `lauf_sicher = 0`. Solche Zeilen haben keinen belegten Modelllauf.
- `lauf_sicher = 0` auch, wenn zwischen Meta-Abfrage und Abruf ein neuer Lauf erschien.
- Ein Mitglied zählt für einen Tag nur mit **allen** Stundenwerten; sonst wird es ausgelassen (`ausgeschlossen`).

### Wiederholungen und Fehlerbehandlung

- Eine Station zählt nur als erfasst, wenn für **jedes** angefragte Modell verwertbare Werte gespeichert wurden (leere/`null`-Antworten zählen nicht). Ein Modelllauf gilt erst als erledigt (`zustand.json`), wenn alle Stationen erfasst sind; zu ≥ 90 % erst nach 3 Versuchen. Sonst wird beim nächsten Lauf wiederholt (Doppelzeilen sind unschädlich: der Leser nimmt je Modell den jüngsten Lauf und Empfang).
- **Auflösung:** Nicht entscheidbare Events (HKO-Monatswert noch nicht veröffentlicht, METAR-Ausfall, Gewinner noch offen) stehen mit Datum in `zustand.json` (`aufloesung_offen`) und werden bis zu 60 Tage lang unabhängig vom 6-Tage-Fenster erneut abgefragt (per Slug).
- **Frist:** Alle Abrufe samt Wiederholungen und Wartezeiten teilen eine gemeinsame Frist von 11 Minuten (`bot/netz.py`). Ist sie erreicht, endet der Lauf geordnet, schreibt das Log und lässt den Commit zu.
- **Open-Meteo-Tageslimit:** Meldet der Dienst „Daily limit“, pausiert das Ensemble bis 00:05 UTC (`om_gesperrt_bis`). Die eigene Obergrenze zählt ein geschätztes Gewicht (Summe angefragter Modelle), nicht HTTP-Aufrufe.
- **Push:** `git pull --rebase -X theirs` (eigener Stand gewinnt), hängender Rebase wird abgebrochen, 4 Versuche; schlägt alles fehl, werden die Daten dieses Laufs als Workflow-Artefakt (14 Tage) gesichert.

### Spalten `laufzeit.csv`

`lauf_start_utc, lauf_ende_utc, dauer_s, luecke_min, status (OK | TEILFEHLER | FEHLER_MAERKTE), events, maerkte, neue_stammzeilen, ensemble_modelle_neu, ensemble_stationen_ok, ensemble_fehler, om_anfragen, om_gewicht, om_gewicht_heute, om_meta_anfragen, wahrscheinlichkeiten, aufloesung_neu, aufloesung_abweichungen, aufloesung_offen, daten_mb, git_pack_mb, fehler`

## Open-Meteo-Grenzen

Frei: 600 Aufrufe/min, 5 000/Stunde, 10 000/Tag (gewichtet; Ensemble-Abrufe zählen mehrfach). Maßnahmen: Abruf nur bei neuem Lauf, 2 s Pause je Station, Warten von 65 s bei „Minutely limit“ (innerhalb der Gesamtfrist), eigene Tagesobergrenze 4 000 für das geschätzte Gewicht (`OM_TAGESLIMIT`, gezählt in `om_gewicht_heute`; `om_anfragen` zählt die HTTP-Aufrufe). Die GitHub-Runner teilen sich IP-Adressen mit anderen Nutzern; 429-Antworten sind deshalb möglich und stehen im Log.

## Größe

Messung (Probelauf 2026-10-13, 2 803 Buckets): Schnappschuss ≈ 26 KB je Lauf (→ ca. 1,3 MB/Tag bei 48 Läufen), Stamm ≈ 270 KB beim ersten Lauf des Tages (danach nur Differenzen), Ensemble ≈ 62 KB bei Update aller vier Modelle, Wahrscheinlichkeiten ≈ 11 KB. Hochrechnung: **ca. 2–2,5 MB/Tag, 60–75 MB/Monat** im Git-Verlauf. Das Laufzeit-Log führt `daten_mb` (Arbeitskopie) und `git_pack_mb`. Beobachten; bei Bedarf Schnappschuss-Frequenz senken oder alte Tage in eine Archiv-Verzeichnis-/Release-Datei verlagern (der Git-Verlauf bleibt aber bestehen).

## Hinweise

- GitHub deaktiviert geplante Workflows nach 60 Tagen ohne Repository-Aktivität; die Protokoll-Commits zählen als Aktivität.
- Öffentliches Repo: die Daten sind öffentlich. Keine Schlüssel im Spiel.
