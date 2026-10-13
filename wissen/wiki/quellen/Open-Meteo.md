---
typ: quelle
tags: [quelle, wetter]
stand: 2026-10-13
---
# Open-Meteo

Wetter-APIs ohne Schlüssel, frei nur **nicht-kommerziell**. Limits laut Preisseite: 600 Aufrufe/min, 5 000/Stunde, 10 000/Tag (gewichtet).

## Ensemble (live)

`https://ensemble-api.open-meteo.com/v1/ensemble` mit `models=ecmwf_ifs025,gfs025,icon_seamless,gem_global` liefert 143 Läufe (51 + 31 + 40 + 21) mit stündlicher 2-m-Temperatur, `timezone=<IANA>` gibt lokale Zeitachsen.

- Spaltennamen: bei mehreren Modellen mit Modellsuffix (`temperature_2m_member03_ecmwf_ifs025_ensemble`, `temperature_2m_ncep_gefs025`, `…_icon_seamless_eps`, `…_gem_global_ensemble`); bei **genau einem** Modell **ohne** Suffix (`temperature_2m_member03`).
- **Kein Rückblick:** `past_days` liefert höchstens ca. 4 Tage; `start_date` in der Vergangenheit ist formal bis ca. 3 Monate erlaubt, liefert aber nur leere Werte. Ein „Historical Ensemble API“ existiert nicht (Host nicht auflösbar). Alte Ensembles lassen sich deshalb nur selbst sammeln: [[Live-Protokoll]].
- Ein Abruf mit 4 Modellen × 4 Tage zählt mehrfach im Limit. Mit 0,5 s Pause zwischen 49 Stationen kam `429 Minutely API request limit exceeded`. Gegenmaßnahme: 2 s Pause, bei 429 65 s warten.

## Neue Modelläufe erkennen

`https://ensemble-api.open-meteo.com/data/<datensatz>/static/meta.json` mit `last_run_initialisation_time` (Unix-Zeit). Datensätze: `ecmwf_ifs025_ensemble`, `ncep_gefs025`, `cmc_gem_geps`, ICON: `dwd_icon_eps`, `dwd_icon_eu_eps`. Die Meta nennt auch `last_run_availability_time`; ein Lauf gilt erst nach 10 Minuten Sicherheitsabstand als belegt. ICON besteht aus einem globalen und einem EU-Datensatz mit verschiedenen Zyklen (12 h / 6 h). Bei Tageslimit antwortet der Dienst mit 429 und „Daily API request limit exceeded“. **Die ICON-Meta war am 2026-10-13 veraltet (6.10.), obwohl frische Daten kamen**, daher 6-Stunden-Raster als Rückfall (siehe [[Live-Protokoll]]).

## Deterministische Archive

- **Previous Runs** (`previous-runs-api.open-meteo.com`, `temperature_2m_previous_day1…7`): Modelle meist ab Januar 2024, GFS-Temperatur ab März 2021. Daily-Variablen mit `previous_day` gehen nicht, nur stündlich (selbst Tagesmax bilden).
- Historical Forecast (`historical-forecast-api…`): best_match und GFS ab 2022, ICON/GEM/UKMO ab 2024, ECMWF ab 2025.

Güte: [[Vorhersagegüte Previous Runs]]. Siehe auch [[Ensemble und deterministische Vorhersage]].
