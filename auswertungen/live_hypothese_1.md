# Live-Hypothese 1: Nein-Wetten bei etwa zwei Tagen Vorlauf, echte Ensembles, echter Ask

**Festgeschrieben am 2026-10-14, bevor ein Auswerteskript für diese Hypothese existiert und bevor irgendeine Wette dieser Hypothese ausgewertet wurde. Nach dem Einspielen dieser Datei wird sie nicht mehr geändert.** Spätere Erkenntnisse kommen in den Auswertungsbericht, nicht hierher. Nur Auswertung der Protokolldaten (`daten/`): keine Wetten, keine Wett-Logik im Bot, kein Eingriff in den Workflow.

## Anlass

Die Rückrechnung (`auswertungen/2026-10-14_rueckrechnung.md`) hat mit zwei deterministischen Modellen und Preispunkten kein Verfahren gezeigt, das nach Kosten gewinnt. Vorlauf 2 bestand formal, aber nur bei Events mit unplausibler Preissumme (Ja-Preise über 1,10). Offen bleibt, ob **echte Ensembles** gegen **echte Geld-/Briefkurse mit Tiefe** etwas bringen. Diese Hypothese prüft das mit dem Live-Protokoll.

## Hypothese

Nein-Wetten auf einzelne Temperatur-Buckets, entschieden 18:00 Ortszeit zwei Tage vor dem Zieltag, haben nach Spread, Gebühr und Tiefe einen Erwartungswert über null, wenn die Wahrscheinlichkeit aus den Ensembles des Protokolls (mit Stationskorrektur) die Kante von mindestens 0,10 gegen den echten Ask zeigt.

## Festgelegte Regeln

**Grundgesamtheit.** Alle Events „Höchst-/Tiefsttemperatur“ im Protokoll, deren Station in `auswertungen/live_bias.json` vorkommt (die 16 Stationen der 15 Rückrechnungs-Städte; alle anderen Städte werden nicht gewertet), mit Zieltag **ab 2026-10-16** (Entscheidung nach der Festschreibung). Jedes Event zählt höchstens einmal je Variante.

**Entscheidungszeitpunkt `Td`.** 18:00 Ortszeit der Station am Tag (Zieltag − 2) (Hauptvariante) bzw. (Zieltag − 1) (Vergleich Vorlauf 1).

**Entscheidungs-Schnappschuss.** Der erste Protokoll-Lauf (`maerkte_HHMM`, UTC-Startzeit `HHMM` im Tagesordner) mit Startzeit ≥ `Td`, höchstens 60 Minuten nach `Td`. Gibt es keinen, zählt das Event für diese Variante als „Lücke“ (wird gezählt und berichtet, nicht ersetzt). Fehlt der Markt dort (nicht im Schnappschuss), entfällt das Event ebenso.

**Wahrscheinlichkeit.**
1. Ensemble-Mitglieder: je (Stadt, Art, Zieltag, Modell) die Zeile aus `ensemble_*.csv.gz` mit dem jüngsten `empfangen_utc` ≤ Startzeit des Entscheidungs-Schnappschusses (kein Blick in die Zukunft). Alle Modelle des Protokolls (`ecmwf_ifs025`, `gfs025`, `icon_seamless`, `gem_global`), unabhängig von `lauf_sicher`. Mindestens 2 Modelle, sonst entfällt das Event.
2. Alle Mitglieder gepoolt, gleiches Gewicht je Mitglied (wie `bot/ensemble.wahrscheinlichkeiten`).
3. °C → °F für °F-Märkte; **Stationskorrektur:** zu jedem Mitgliedswert wird der Bias addiert, d. h. der Mittelwert der Residuen (Messwert − Vorhersage) 2024–2025 (März–Oktober) der Rückrechnung für Station × Vorlauf (V2 für die Hauptvariante, V1 für den Vergleich) × Art, in Markteinheit (`auswertungen/live_bias.json`, mit dem Einspielen dieser Datei festgeschrieben). Nur der Bias: die Streuung bleibt die des Ensembles (die Residuenstreuung der Rückrechnung gehört zu einer einzelnen deterministischen Vorhersage und würde die Ensemble-Streuung doppelt zählen).
4. Rundung je Station aus dem Stamm (`rundung`: kaufmännisch, HKO abschneidend), wie `bot/rueckrechnung.bucket_p` (Toleranz 1e-9 für exakte x,5); Wahrscheinlichkeit = Anteil der Mitglieder im Bucket, danach auf [0,005; 0,995] begrenzt.

**Preise und Kosten (Taker).** Das Protokoll enthält nur das Ja-Buch. Nein-Ask = 1 − bester Ja-Bid; Tiefe an der Spitze = `bid_groesse`. Ja-Ask = `ask`; Tiefe = `ask_groesse`. Fehlt der nötige Bid/Ask, gibt es für diese Seite keine Wette. Kaufpreis `q` = der Ask (kein zusätzlicher Spread). Gebühr je Anteil `fee_rate · q · (1 − q)` mit `fee_rate` aus dem Stamm (nur wenn `fees_aktiv`, Taker; `docs/gebuehren.md`); Kosten je Anteil `c = q + fee`.

**Kante und Auswahl.** Kante = Wahrscheinlichkeit der Seite − `c` (Nein: 1 − P). Wette, wenn Kante ≥ **0,10**; je Event und Variante höchstens 2 Wetten (die größten Kanten, bei Gleichstand kleinerer Bucket-Index), Nein und Ja getrennt gezählt.

**Tiefe.** Einsatz 10 $ inklusive Gebühr: Anteile `a = 10 / c`. Wette nur, wenn die Tiefe an der Spitze ≥ `a` ist und `a` ≥ `min_groesse` des Marktes. Keine Teilfüllung, kein Durchlaufen des Buchs.

**Ergebnis.** Wahrheit = Polymarket-Gewinner (`gewinner_bucket` in `aufloesung.csv.gz`). Nein gewinnt, wenn der Bucket nicht der Gewinner ist. Gewinn = `a − 10` bei Treffer, sonst `−10`. Noch nicht aufgelöste Wetten zählen nicht.

## Auswertung

- **Hauptvariante:** Nein-Wetten, Vorlauf 2. **Stichprobe = die ersten 200 Hauptwetten nach `Td`** (bei Gleichstand nach Event-Slug, Bucket-Index); sie wird erst ausgewertet, wenn alle 200 aufgelöst sind. Erst dann, **einmal**. Bis dahin gibt das Auswerteskript nur Zählstände aus (Wetten, aufgelöste Wetten, Lücken, Ausfälle), **keine** Gewinne, Quoten oder Brier-Werte. Kein Zwischenstand-Tuning; kein Ändern von Schwelle, Gewichten, Korrektur, Zeitpunkt oder Auswahl.
- **Hälften nach Zeit:** erste 100 und zweite 100 der Stichprobe (nach `Td`).
- **Messlatte: null nach Kosten.** Die Hypothese gilt als **bestätigt**, wenn (1) Gewinn je Wette über alle 200 > 0, (2) die Summe ohne die 3 besten Wetten > 0 und (3) die Summe in **jeder** der beiden Hälften > 0. Sonst **nicht bestätigt**. Berichtet werden zusätzlich Trefferquote, Summe, Brier-Score (Modell gegen Mitte des Ja-Preises, alle Buckets der Hauptwetten-Events) und die Preissumme der Events als Beschreibung (kein Filter).
- **Zum Vergleich, nicht Entscheidungsgrundlage:** Ja-Wetten Vorlauf 2, Nein-Wetten Vorlauf 1, Ja-Wetten Vorlauf 1, nach derselben Regel, im selben Zeitraum (Zieltage bis zum `Td` der 200. Hauptwette), ohne Mindestzahl.

## Vorab benannte Schwächen

- 200 Wetten sind wenige und korreliert (gleiche Wetterlage, mehrere Städte am selben Tag, höchstens 2 Wetten je Event). Ein positives Ergebnis ist ein Hinweis, kein Beleg.
- Nur Bias-Korrektur; Ensembles sind oft zu eng gestreut (zu sichere Wahrscheinlichkeiten). Das wird nicht nachträglich korrigiert.
- Der Bias stammt von der Mittelung zweier deterministischer Modelle, nicht von Ensemble-Mitgliedern.
- Mitglieder-Pool: ECMWF-ENS, GEFS, ICON-EPS und GEM-GEPS haben verschiedene Mitgliederzahlen; die Gewichtung je Mitglied lässt größere Ensembles stärker zählen.
- Ein Schnappschuss je Entscheidung; der Zeitplan des Protokolls hat Lücken (siehe `wissen/wiki/werkzeuge/GitHub-Actions-Workflow.md`); Ereignisse ohne Schnappschuss innerhalb von 60 Minuten entfallen und können das Ergebnis verzerren (werden gezählt).
- Die Tiefe an der Spitze sagt nichts über Preisbewegung durch die eigene Order und über Ausführungsrisiken; Maker-Rebates sind nicht eingerechnet.
- Auflösungsabweichungen zwischen METAR und Polymarket-Gewinner (kleiner einstelliger Prozentbereich) sind Rauschen; es zählt der Gewinner.
