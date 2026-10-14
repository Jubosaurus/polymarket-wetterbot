# Rückrechnung Phase 1b (2026-10-14)

Nur Auswertung, keine Wetten. Regeln festgeschrieben in `auswertungen/rueckrechnung_regeln.md` (eingespielt vor dem Laden der Daten). Hauptfall: Mittel aus ECMWF und GFS, Spread 0,04, Kante ≥ 0,10, Ja und Nein, höchstens 2 Wetten je Event, 10 $ Einsatz inklusive Gebühr. 15 Städte, Zieldaten 2026-03-01 bis 2026-10-11. Zeitangaben in UTC.

## Urteil: **VERWERFEN**

| Hauptregel, Bestätigungshälfte (Juli–Okt) | Wetten | Trefferquote | Gewinn je Wette ($) | Summe ($) | Summe ohne 3 beste ($) | Brier Modell / Markt (alle Buckets) | Kriterien erfüllt |
|---|---|---|---|---|---|---|---|
| Vorlauf 1 | 3876 | 53.1 % | -0.28 | -1092.52 | -1950.59 | 0.0705 / 0.0693 | nein |
| Vorlauf 2 | 2653 | 64.7 % | +1.05 | +2780.30 | +2241.19 | 0.0713 / 0.0788 | ja |

Kriterien (vorab festgelegt): ≥ 100 Wetten, Summe > 0, Summe ohne die 3 besten > 0 und Brier(Modell) < Brier(Markt), und das für **beide** Vorläufe. „Zu wenig Daten“, wenn die Bestätigungshälfte insgesamt < 100 Wetten hat. Brier: kleiner ist besser.

**Urteil nach den vorab festgelegten Kriterien: VERWERFEN** (unverändert nach der Neuberechnung vom 2026-10-14). Das Verfahren (zwei deterministische Modelle plus gelernte Fehlerverteilung) liefert in diesem Testzeitraum keinen belastbaren, handelbaren Vorteil gegenüber dem Marktpreis.

**Warum, in der Reihenfolge der Belege:**

1. **Findungshälfte (März–Juni): beide Vorläufe verlieren.** Vorlauf 1: 2 168 Wetten, −4 035 $; Vorlauf 2: 1 447 Wetten, −1 350 $. Im Brier-Score ist der Markt klar besser als das Modell (Vorlauf 1: 0,0666 gegen 0,0589; Vorlauf 2: 0,0684 gegen 0,0627).
2. **Bestätigungshälfte (Juli–Oktober), Vorlauf 1: durchgefallen.** 3 876 Wetten, −1 093 $ (−0,28 $ je Wette); ohne die 3 besten −1 951 $. Brier Modell 0,0705, Markt 0,0693, also kein Vorteil.
3. **Bestätigungshälfte, Vorlauf 2: formal bestanden, aber nicht belastbar.** 2 653 Wetten, +2 780 $ (+1,05 $ je Wette; ohne die 3 besten +2 241 $), Brier Modell 0,0713 gegen Markt 0,0788. Das Ergebnis kommt **ausschließlich aus Nein-Wetten** (2 163 Wetten, +4 430 $, Trefferquote 77,5 %); die Ja-Wetten verlieren (490 Wetten, −1 649 $, Trefferquote 8,2 %). Vorlauf 2 ist zudem in der Findungshälfte negativ. Nach der Regel (beide Vorläufe müssen bestehen) zählt es nicht. Die Zusatzauswertung unten bestätigt den Verdacht: Der Gewinn entsteht bei Events mit Preissumme über 1,10 (+4 914 $), bei plausibler Preissumme (0,95–1,10) verlieren die Nein-Wetten (−530 $).
4. **Die Marktpreise der Bestätigungshälfte sind verzerrt, nicht das Modell besser.** Das Modell ist gut kalibriert (Modell sagt 20–30 % → tatsächlich 24,7 %), der Markt nicht (Markt sagt 30–40 % → 24,2 %; 40–50 % → 29,4 %). Ursache laut Zusatzauswertung: Tiefsttemperatur-Märkte ab August wurden erst Stunden vor dem Entscheidungszeitpunkt eröffnet und zeigen flache Startpreise (Preissumme eines Events bis 2,9 statt 1,0). Zu solchen Preisen wäre kein Handel in der angenommenen Größe möglich gewesen. Auf Events mit plausibler Preissumme (0,90–1,15) verlieren **beide Vorläufe in beiden Hälften** (Bestätigung: −5 180 $ bzw. −2 188 $), und der Markt schlägt das Modell im Brier-Score (0,0599 gegen 0,0712 bzw. 0,0627 gegen 0,0716).

**Was das bedeutet und was nicht:**

- **Entscheidung:** Vorlauf 1 verworfen. Vorlauf 2 formal bestanden, aber verdächtig (Gewinn nur bei unplausibler Preissumme). **Kein Papierhandel auf Basis der Rückrechnung.** Die offene Frage nach echten Ensembles wird mit der vorab festgeschriebenen Hypothese 1 am Live-Protokoll geprüft (`auswertungen/live_hypothese_1.md`).
- Verworfen wird dieses Verfahren mit diesen Daten. Es sagt **nichts** über echte Ensemble-Vorhersagen, die das Live-Protokoll sammelt, und nichts über bessere Kalibrierung. Das einzige Positive: Das Modell ist selbst gut kalibriert, nur nicht besser als der Markt.
- Der Markt ist bei Höchstwerten schon einen Tag vorher sehr effizient (Brier 0,059–0,063 gegen 0,067–0,068 beim Modell in der Findungshälfte). Ein Vorteil müsste aus Information kommen, die der Markt um 18:00 Ortszeit noch nicht eingepreist hat (z. B. neuere Läufe, Ensemble-Streuung), nicht aus denselben Modellen.
- Der wirksame Vorlauf des Tageshöchstwerts ist länger als „1 Tag“ (Look-ahead-Schutz, siehe Regeln und Abschnitt „Interpolation“): Nachmittagsstunden stammen bei Vorlauf 1 aus `previous_day2`.

**Prüfhinweise:**

- **Look-ahead:** Alle 10 144 Hauptwetten wurden maschinell geprüft: 0 Läufe (jetzt unter Einbeziehung aller Interpolations-Stützstellen) und 0 Preispunkte nach dem Entscheidungszeitpunkt (Stichprobe von 20 unten).
- **Gegenrechnung:** Eigenes Zieldatum aus dem Fragetext und eigene Ableitung der Stützstellen; alle verglichenen Zahlen stimmen auf 2,5e-12 überein (siehe Abschnitt „Gegenrechnung“).
- **Neuberechnung:** Die beiden Befunde des Codex-Reviews (Zieltag aus `endDate`; Interpolation ohne Stützstellen-Prüfung) sind behoben. Die Auswirkung war klein und ändert das Urteil nicht (Tabelle „Vorher / nachher“).
- Die Zusatzauswertung zur Preisqualität ist nachträglich entstanden (nach Sicht der Daten) und beeinflusst das Urteil nicht.

## Neuberechnung nach Codex-Review (2026-10-14)

Der Review fand zwei Fehler im ersten Lauf: (1) `endDate` statt Zieltag, (2) Interpolation ohne Stützstellen-Prüfung. Beide sind behoben, Kalibrierung, Hauptrechnung, Gegenrechnung und Bericht wurden komplett neu erzeugt. Die Regeln aus Commit `0d071ab` blieben unverändert; die Umsetzung steht in `auswertungen/rueckrechnung_klarstellungen.md`.

### Zieldatum

Der Zieltag kommt jetzt aus dem Slug (`...-on-april-15-2026`), nicht aus `endDate`. Von 14033 Events im Cache (alle Städte) weichen **44** ab (Zieltag ≠ Datum von `endDate`); davon liegen **2** in den 15 Städten und **44** im Testzeitraum. Unlesbare Slugs: 0; Slugs ohne Jahr (frühe Events, Jahr aus `endDate`): 20, alle vor dem Testzeitraum. Die Preisfenster der 2 betroffenen Events der 15 Städte wurden neu geladen. Alle Abweichungen:

| Event | Stadt | Zieltag (Slug) | `endDate` | Differenz (Tage) | in den 15 Städten |
|---|---|---|---|---|---|
| highest-temperature-in-taipei-on-march-16-2026 | taipei | 2026-03-16 | 2026-03-17T12:00:00Z | +1 | nein |
| highest-temperature-in-hong-kong-on-march-17-2026 | hong-kong | 2026-03-17 | 2026-03-18T12:00:00Z | +1 | nein |
| highest-temperature-in-madrid-on-march-17-2026 | madrid | 2026-03-17 | 2026-03-18T12:00:00Z | +1 | nein |
| highest-temperature-in-milan-on-march-17-2026 | milan | 2026-03-17 | 2026-03-18T12:00:00Z | +1 | nein |
| highest-temperature-in-taipei-on-march-17-2026 | taipei | 2026-03-17 | 2026-03-18T12:00:00Z | +1 | nein |
| highest-temperature-in-warsaw-on-march-17-2026 | warsaw | 2026-03-17 | 2026-03-18T12:00:00Z | +1 | nein |
| highest-temperature-in-hong-kong-on-march-18-2026 | hong-kong | 2026-03-18 | 2026-03-19T12:00:00Z | +1 | nein |
| highest-temperature-in-madrid-on-march-18-2026 | madrid | 2026-03-18 | 2026-03-19T12:00:00Z | +1 | nein |
| highest-temperature-in-milan-on-march-18-2026 | milan | 2026-03-18 | 2026-03-19T12:00:00Z | +1 | nein |
| highest-temperature-in-taipei-on-march-18-2026 | taipei | 2026-03-18 | 2026-03-19T12:00:00Z | +1 | nein |
| highest-temperature-in-warsaw-on-march-18-2026 | warsaw | 2026-03-18 | 2026-03-19T12:00:00Z | +1 | nein |
| highest-temperature-in-hong-kong-on-march-19-2026 | hong-kong | 2026-03-19 | 2026-03-20T12:00:00Z | +1 | nein |
| highest-temperature-in-madrid-on-march-19-2026 | madrid | 2026-03-19 | 2026-03-20T12:00:00Z | +1 | nein |
| highest-temperature-in-milan-on-march-19-2026 | milan | 2026-03-19 | 2026-03-20T12:00:00Z | +1 | nein |
| highest-temperature-in-taipei-on-march-19-2026 | taipei | 2026-03-19 | 2026-03-20T12:00:00Z | +1 | nein |
| highest-temperature-in-warsaw-on-march-19-2026 | warsaw | 2026-03-19 | 2026-03-20T12:00:00Z | +1 | nein |
| highest-temperature-in-beijing-on-march-20-2026 | beijing | 2026-03-20 | 2026-03-21T12:00:00Z | +1 | nein |
| highest-temperature-in-chengdu-on-march-20-2026 | chengdu | 2026-03-20 | 2026-03-21T12:00:00Z | +1 | nein |
| highest-temperature-in-chongqing-on-march-20-2026 | chongqing | 2026-03-20 | 2026-03-21T12:00:00Z | +1 | nein |
| highest-temperature-in-shenzhen-on-march-20-2026 | shenzhen | 2026-03-20 | 2026-03-21T12:00:00Z | +1 | nein |
| highest-temperature-in-wuhan-on-march-20-2026 | wuhan | 2026-03-20 | 2026-03-21T12:00:00Z | +1 | nein |
| highest-temperature-in-beijing-on-march-21-2026 | beijing | 2026-03-21 | 2026-03-22T12:00:00Z | +1 | nein |
| highest-temperature-in-chengdu-on-march-21-2026 | chengdu | 2026-03-21 | 2026-03-22T12:00:00Z | +1 | nein |
| highest-temperature-in-chongqing-on-march-21-2026 | chongqing | 2026-03-21 | 2026-03-22T12:00:00Z | +1 | nein |
| highest-temperature-in-shenzhen-on-march-21-2026 | shenzhen | 2026-03-21 | 2026-03-22T12:00:00Z | +1 | nein |
| highest-temperature-in-wuhan-on-march-21-2026 | wuhan | 2026-03-21 | 2026-03-22T12:00:00Z | +1 | nein |
| highest-temperature-in-beijing-on-march-22-2026 | beijing | 2026-03-22 | 2026-03-23T12:00:00Z | +1 | nein |
| highest-temperature-in-chongqing-on-march-22-2026 | chongqing | 2026-03-22 | 2026-03-23T12:00:00Z | +1 | nein |
| highest-temperature-in-shenzhen-on-march-22-2026 | shenzhen | 2026-03-22 | 2026-03-23T12:00:00Z | +1 | nein |
| highest-temperature-in-wuhan-on-march-22-2026 | wuhan | 2026-03-22 | 2026-03-23T12:00:00Z | +1 | nein |
| highest-temperature-in-beijing-on-march-23-2026 | beijing | 2026-03-23 | 2026-03-24T12:00:00Z | +1 | nein |
| highest-temperature-in-chengdu-on-march-23-2026 | chengdu | 2026-03-23 | 2026-03-24T12:00:00Z | +1 | nein |
| highest-temperature-in-chongqing-on-march-23-2026 | chongqing | 2026-03-23 | 2026-03-24T12:00:00Z | +1 | nein |
| highest-temperature-in-shenzhen-on-march-23-2026 | shenzhen | 2026-03-23 | 2026-03-24T12:00:00Z | +1 | nein |
| highest-temperature-in-wuhan-on-march-23-2026 | wuhan | 2026-03-23 | 2026-03-24T12:00:00Z | +1 | nein |
| highest-temperature-in-beijing-on-march-24-2026 | beijing | 2026-03-24 | 2026-03-25T12:00:00Z | +1 | nein |
| highest-temperature-in-chengdu-on-march-24-2026 | chengdu | 2026-03-24 | 2026-03-25T12:00:00Z | +1 | nein |
| highest-temperature-in-chongqing-on-march-24-2026 | chongqing | 2026-03-24 | 2026-03-25T12:00:00Z | +1 | nein |
| highest-temperature-in-shenzhen-on-march-24-2026 | shenzhen | 2026-03-24 | 2026-03-25T12:00:00Z | +1 | nein |
| highest-temperature-in-wuhan-on-march-24-2026 | wuhan | 2026-03-24 | 2026-03-25T12:00:00Z | +1 | nein |
| lowest-temperature-in-nyc-on-april-15-2026 | nyc | 2026-04-15 | 2026-04-16T12:00:00Z | +1 | **ja** |
| lowest-temperature-in-seoul-on-april-15-2026 | seoul | 2026-04-15 | 2026-04-16T12:00:00Z | +1 | **ja** |
| lowest-temperature-in-shanghai-on-april-15-2026 | shanghai | 2026-04-15 | 2026-04-16T12:00:00Z | +1 | nein |
| lowest-temperature-in-tokyo-on-april-15-2026 | tokyo | 2026-04-15 | 2026-04-16T12:00:00Z | +1 | nein |

### Interpolation (Stützstellen)

Gemessen am Cache: Die ECMWF-Stundenwerte zwischen den 3-h-Stützstellen sind Catmull-Rom-Interpolationen über vier Stützstellen (a−3 h, a, a+3 h, a+6 h): 14 696 von 14 696 geprüften Stunden stimmen mit höchstens 0,08 °C Abweichung überein (vier Stationen, Vorlauf 1 und 2). GFS ist stündlich nativ (keine Interpolation). Ein Stundenwert gilt jetzt nur als bekannt, wenn **alle** seine Stützstellen aus zum Entscheidungszeitpunkt verfügbaren Läufen stammen (Lauf + 10 h ≤ Td); sonst wird der nächstältere Lauf (N+1, 24 h älter) verwendet, bei N > 3 fällt der Tag aus. Wirkung auf ECMWF (alle Zieltage des Testzeitraums):

| Vorlauf | Stunden | Stunden mit älterem Lauf | Tage mit mindestens einer solchen Stunde | Tage ohne Prognose (alte Regel) | Tage ohne Prognose (neu) |
|---|---|---|---|---|---|
| 1 | 63666 | 10612 (16.7 %) | 2653 von 2653 | 0 | 0 |
| 2 | 63666 | 10612 (16.7 %) | 2653 von 2653 | 0 | 0 |

### Unabhängigkeit der Gegenrechnung

Die Gegenrechnung bestimmt jetzt **ihr eigenes Zieldatum aus dem Fragetext** (Event-Titel „… on April 15?“; Jahr aus der Beschreibung „… on 15 Apr '26“, sonst nächstliegend zu `endDate`) und leitet die **Stützstellen selbst** aus den Catmull-Rom-Gewichten ab (Stützstellen mit Gewicht ≠ 0, ohne die Indexarithmetik der Hauptrechnung). Datumsableitung der Gegenrechnung (Events der 15 Städte): jahr_aus_enddate 364, mit_jahr_aus_beschreibung 4534. Events, bei denen ihr Zieldatum vom Slug-Datum der Hauptrechnung abweicht: **0**. Gemeinsam bleiben die Rohdaten (Cache), die Regeln selbst (Td, 10 h, N ≤ 3) und die Annahme, dass eine Stützstelle `s` im Vorlauf-N-Wert aus dem Lauf `floor6(s − 24·N h)` stammt; diese Annahme steht in den Regeln und wurde mit der Single-Runs-API nachgemessen, hier nicht neu geprüft.


### Vorher / nachher (Hauptregel: Mittel ECMWF+GFS, Spread 0,04, Kante ≥ 0,10, Ja und Nein)

„vorher“ = erster Lauf (Zieltag aus `endDate`, Stundenwert ohne Stützstellen-Prüfung); „nachher“ = dieser Bericht. Brier: kleiner ist besser.

| Vorlauf | Hälfte | Stand | Brier Modell | Brier Markt | Wetten | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |
|---|---|---|---|---|---|---|---|---|
| 1 | Finden | vorher | 0.0665 | 0.0588 | 2157 | -1.86 | -4012.54 | -4664.94 |
| 1 | Finden | nachher | 0.0666 | 0.0589 | 2168 | -1.86 | -4034.64 | -4687.04 |
| 1 | Bestätigen | vorher | 0.0702 | 0.0693 | 3888 | -0.19 | -728.92 | -1587.00 |
| 1 | Bestätigen | nachher | 0.0705 | 0.0693 | 3876 | -0.28 | -1092.52 | -1950.59 |
| 2 | Finden | vorher | 0.0682 | 0.0628 | 1455 | -0.74 | -1079.79 | -1757.72 |
| 2 | Finden | nachher | 0.0684 | 0.0627 | 1447 | -0.93 | -1350.10 | -1978.53 |
| 2 | Bestätigen | vorher | 0.0712 | 0.0788 | 2644 | +0.93 | +2470.25 | +1962.88 |
| 2 | Bestätigen | nachher | 0.0713 | 0.0788 | 2653 | +1.05 | +2780.30 | +2241.19 |
| beide | alle | vorher | 0.0691 | 0.0675 | 10144 (Hauptwetten) | | | |
| beide | alle | nachher | 0.0693 | 0.0675 | 10144 (Hauptwetten) | | | |

### Stationsprüfung (2026-10-14): betroffene Städte der Rückrechnung

Die Rückrechnung holt die Koordinaten aus dem IEM-Verzeichnis (`daten/cache/koordinaten.json`), nicht aus `bot/stationen.py`. Gegen `aviationweather.gov` geprüft liegen 15 der 16 Stationen höchstens 0,43 km daneben (unverändert); **Dallas (KDAL) liegt 1,8 km daneben** (Rasterhöhe 144 statt 146 m). Nur Dallas wurde neu abgerufen (Prognosen 2024, 2025, Test) und alles neu gerechnet (Regeln unverändert). Chongqing, Wuhan, Chengdu, Karachi, Qingdao, Shanghai und Hong Kong gehören nicht zu den 15. „vorher“ = Lauf mit den alten Dallas-Koordinaten (Stand nach dem ersten Review), „nachher“ = dieser Bericht.

| Vorlauf | Hälfte | Stand | Brier Modell | Brier Markt | Wetten | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |
|---|---|---|---|---|---|---|---|---|
| 1 | Finden | vorher | 0.0666 | 0.0589 | 2168 | -1.87 | -4060.38 | -4712.78 |
| 1 | Finden | nachher | 0.0666 | 0.0589 | 2168 | -1.86 | -4034.64 | -4687.04 |
| 1 | Bestätigen | vorher | 0.0704 | 0.0693 | 3875 | -0.28 | -1070.72 | -1928.79 |
| 1 | Bestätigen | nachher | 0.0705 | 0.0693 | 3876 | -0.28 | -1092.52 | -1950.59 |
| 2 | Finden | vorher | 0.0684 | 0.0627 | 1447 | -0.93 | -1350.10 | -1978.53 |
| 2 | Finden | nachher | 0.0684 | 0.0627 | 1447 | -0.93 | -1350.10 | -1978.53 |
| 2 | Bestätigen | vorher | 0.0713 | 0.0788 | 2653 | +1.05 | +2780.30 | +2241.19 |
| 2 | Bestätigen | nachher | 0.0713 | 0.0788 | 2653 | +1.05 | +2780.30 | +2241.19 |
| beide | alle | vorher | 0.0693 | 0.0675 | 10143 (Hauptwetten) | | | |
| beide | alle | nachher | 0.0693 | 0.0675 | 10144 (Hauptwetten) | | | |

## Datenbasis

- Events im Testzeitraum (15 Städte): 4674. Auswertbar (Prognose und mindestens ein Preis am Entscheidungszeitpunkt): Vorlauf 1: 4631, Vorlauf 2: 3488.
- Ausgelassen: ohne gewinner 10, ohne preis v1 33, ohne preis v2 1176.
- Fehlerverteilung: 192 Zellen (Station × Vorlauf × Art × Variante) aus Mär–Okt 2024 und 2025, kleinste Zelle 490 Tage, Median 490; **gepoolte Zellen: 0**.

## Treffsicherheit aller Buckets (Brier-Score, kleiner = besser)

| Gruppe | Buckets | Brier Modell | Brier Markt | Modell − Markt |
|---|---|---|---|---|
| alle | 88497 | 0.0693 | 0.0675 | +0.0018 |
| Finden, Vorlauf 1 | 22173 | 0.0666 | 0.0589 | +0.0077 |
| Finden, Vorlauf 2 | 17992 | 0.0684 | 0.0627 | +0.0056 |
| Bestätigen, Vorlauf 1 | 28335 | 0.0705 | 0.0693 | +0.0012 |
| Bestätigen, Vorlauf 2 | 19997 | 0.0713 | 0.0788 | -0.0074 |
| Finden, Vorlauf 1, °F-Städte | 8928 | 0.0631 | 0.0567 | +0.0065 |
| Finden, Vorlauf 1, °C-Städte | 13245 | 0.0689 | 0.0604 | +0.0085 |
| Bestätigen, Vorlauf 1, °F-Städte | 11352 | 0.0699 | 0.0689 | +0.0011 |
| Bestätigen, Vorlauf 1, °C-Städte | 16983 | 0.0709 | 0.0696 | +0.0013 |
| Finden, Vorlauf 2, °F-Städte | 6531 | 0.0631 | 0.0585 | +0.0046 |
| Finden, Vorlauf 2, °C-Städte | 11461 | 0.0714 | 0.0652 | +0.0062 |
| Bestätigen, Vorlauf 2, °F-Städte | 5687 | 0.0694 | 0.0816 | -0.0122 |
| Bestätigen, Vorlauf 2, °C-Städte | 14310 | 0.0721 | 0.0777 | -0.0056 |

**Kalibrierung, Bestätigungshälfte** (Hauptvorhersage und Marktpreis; Spalte „Häufigkeit“ = wie oft der Bucket tatsächlich gewann)

| Modell sagt | Buckets | mittl. Modell-p | Häufigkeit | | Markt sagt | Buckets | mittl. Preis | Häufigkeit |
|---|---|---|---|---|---|---|---|---|
| 0–10 % | 31201 | 0.023 | 0.021 | | 0–10 % | 28266 | 0.020 | 0.010 |
| 10–20 % | 8100 | 0.147 | 0.148 | | 10–20 % | 5186 | 0.153 | 0.094 |
| 20–30 % | 6101 | 0.244 | 0.247 | | 20–30 % | 5854 | 0.242 | 0.183 |
| 30–40 % | 2293 | 0.336 | 0.351 | | 30–40 % | 5189 | 0.343 | 0.242 |
| 40–50 % | 560 | 0.431 | 0.382 | | 40–50 % | 2855 | 0.447 | 0.294 |
| 50–60 % | 63 | 0.532 | 0.429 | | 50–60 % | 826 | 0.528 | 0.437 |
| 60–70 % | 9 | 0.635 | 0.222 | | 60–70 % | 136 | 0.634 | 0.669 |
| 70–80 % | 5 | 0.756 | 0.600 | | 70–80 % | 16 | 0.731 | 0.500 |
| 80–90 % | 0 | – | – | | 80–90 % | 4 | 0.836 | 0.500 |
| 90–100 % | 0 | – | – | | 90–100 % | 0 | – | – |

**Kalibrierung, alle Daten** (Hauptvorhersage und Marktpreis; Spalte „Häufigkeit“ = wie oft der Bucket tatsächlich gewann)

| Modell sagt | Buckets | mittl. Modell-p | Häufigkeit | | Markt sagt | Buckets | mittl. Preis | Häufigkeit |
|---|---|---|---|---|---|---|---|---|
| 0–10 % | 57738 | 0.022 | 0.020 | | 0–10 % | 56148 | 0.019 | 0.011 |
| 10–20 % | 14103 | 0.147 | 0.148 | | 10–20 % | 9310 | 0.150 | 0.111 |
| 20–30 % | 11214 | 0.244 | 0.244 | | 20–30 % | 9783 | 0.244 | 0.210 |
| 30–40 % | 3926 | 0.335 | 0.349 | | 30–40 % | 7923 | 0.342 | 0.281 |
| 40–50 % | 1009 | 0.435 | 0.389 | | 40–50 % | 3767 | 0.444 | 0.340 |
| 50–60 % | 184 | 0.537 | 0.527 | | 50–60 % | 985 | 0.529 | 0.460 |
| 60–70 % | 44 | 0.644 | 0.568 | | 60–70 % | 214 | 0.636 | 0.687 |
| 70–80 % | 55 | 0.746 | 0.800 | | 70–80 % | 74 | 0.747 | 0.689 |
| 80–90 % | 46 | 0.853 | 0.826 | | 80–90 % | 61 | 0.850 | 0.803 |
| 90–100 % | 178 | 0.971 | 0.955 | | 90–100 % | 232 | 0.966 | 0.983 |

## Wetten (Hauptregel: Kante ≥ 0,10, Spread 0,04, Ja und Nein, höchstens 2 je Event)

| | Wetten | Treffer | Quote | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |
|---|---|---|---|---|---|---|
| Vorlauf 1, Finden | 2168 | 842 | 38.8 % | -1.86 | -4034.64 | -4687.04 |
| Vorlauf 1, Bestätigen | 3876 | 2058 | 53.1 % | -0.28 | -1092.52 | -1950.59 |
| Vorlauf 1, alle | 6044 | 2900 | 48.0 % | -0.85 | -5127.16 | -5985.23 |
| Vorlauf 2, Finden | 1447 | 648 | 44.8 % | -0.93 | -1350.10 | -1978.53 |
| Vorlauf 2, Bestätigen | 2653 | 1717 | 64.7 % | +1.05 | +2780.30 | +2241.19 |
| Vorlauf 2, alle | 4100 | 2365 | 57.7 % | +0.35 | +1430.20 | +778.72 |

**Ja und Nein getrennt** (Aufteilung der Hauptwetten)

| | Wetten | Treffer | Quote | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |
|---|---|---|---|---|---|---|
| Vorlauf 1, Finden, Ja | 882 | 96 | 10.9 % | -3.68 | -3248.38 | -3804.80 |
| Vorlauf 1, Finden, Nein | 1286 | 746 | 58.0 % | -0.61 | -786.26 | -1193.68 |
| Vorlauf 1, Bestätigen, Ja | 1005 | 61 | 6.1 % | -4.05 | -4069.89 | -4927.96 |
| Vorlauf 1, Bestätigen, Nein | 2871 | 1997 | 69.6 % | +1.04 | +2977.37 | +2857.92 |
| Vorlauf 2, Finden, Ja | 575 | 85 | 14.8 % | -1.45 | -831.05 | -1433.18 |
| Vorlauf 2, Finden, Nein | 872 | 563 | 64.6 % | -0.60 | -519.05 | -783.66 |
| Vorlauf 2, Bestätigen, Ja | 490 | 40 | 8.2 % | -3.37 | -1649.24 | -2188.35 |
| Vorlauf 2, Bestätigen, Nein | 2163 | 1677 | 77.5 % | +2.05 | +4429.54 | +4358.88 |

**Ja-only und Nein-only als eigene Strategien** (jeweils höchstens 2 Wetten je Event)

| | Wetten | Treffer | Quote | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |
|---|---|---|---|---|---|---|
| nur Ja, Vorlauf 1, Finden | 1296 | 121 | 9.3 % | -3.81 | -4936.91 | -5715.63 |
| nur Ja, Vorlauf 1, Bestätigen | 1740 | 101 | 5.8 % | -5.00 | -8699.92 | -9620.05 |
| nur Ja, Vorlauf 2, Finden | 796 | 98 | 12.3 % | -2.57 | -2042.56 | -2659.55 |
| nur Ja, Vorlauf 2, Bestätigen | 860 | 66 | 7.7 % | -4.74 | -4078.38 | -4617.50 |
| nur Nein, Vorlauf 1, Finden | 1592 | 977 | 61.4 % | -0.48 | -769.24 | -1176.65 |
| nur Nein, Vorlauf 1, Bestätigen | 3282 | 2292 | 69.8 % | +0.87 | +2871.12 | +2751.68 |
| nur Nein, Vorlauf 2, Finden | 1031 | 671 | 65.1 % | -0.70 | -721.29 | -985.90 |
| nur Nein, Vorlauf 2, Bestätigen | 2386 | 1858 | 77.9 % | +1.91 | +4561.69 | +4491.03 |

**°F- und °C-Städte** (Hauptwetten)

| | Wetten | Treffer | Quote | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |
|---|---|---|---|---|---|---|
| Vorlauf 1, Finden, °F | 851 | 353 | 41.5 % | -0.83 | -705.87 | -1118.03 |
| Vorlauf 1, Finden, °C | 1317 | 489 | 37.1 % | -2.53 | -3328.77 | -3981.17 |
| Vorlauf 1, Bestätigen, °F | 1494 | 794 | 53.1 % | -0.37 | -545.44 | -1247.96 |
| Vorlauf 1, Bestätigen, °C | 2382 | 1264 | 53.1 % | -0.23 | -547.07 | -1335.67 |
| Vorlauf 2, Finden, °F | 479 | 209 | 43.6 % | +0.06 | +29.48 | -459.28 |
| Vorlauf 2, Finden, °C | 968 | 439 | 45.4 % | -1.43 | -1379.59 | -1905.98 |
| Vorlauf 2, Bestätigen, °F | 771 | 537 | 69.6 % | +1.43 | +1100.11 | +839.32 |
| Vorlauf 2, Bestätigen, °C | 1882 | 1180 | 62.7 % | +0.89 | +1680.20 | +1141.08 |

**Schwellen** (nur zusätzlich berichtet; Hauptregel 0,10)

| | Wetten | Treffer | Quote | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |
|---|---|---|---|---|---|---|
| Kante ≥ 0,05, Vorlauf 1, Finden | 3228 | 1258 | 39.0 % | -1.76 | -5677.58 | -6435.88 |
| Kante ≥ 0,05, Vorlauf 1, Bestätigen | 4795 | 2370 | 49.4 % | -0.74 | -3569.49 | -4514.84 |
| Kante ≥ 0,05, Vorlauf 2, Finden | 2393 | 1085 | 45.3 % | -0.97 | -2311.30 | -2989.23 |
| Kante ≥ 0,05, Vorlauf 2, Bestätigen | 3346 | 2050 | 61.3 % | +0.73 | +2454.51 | +1616.45 |
| Kante ≥ 0,10, Vorlauf 1, Finden | 2168 | 842 | 38.8 % | -1.86 | -4034.64 | -4687.04 |
| Kante ≥ 0,10, Vorlauf 1, Bestätigen | 3876 | 2058 | 53.1 % | -0.28 | -1092.52 | -1950.59 |
| Kante ≥ 0,10, Vorlauf 2, Finden | 1447 | 648 | 44.8 % | -0.93 | -1350.10 | -1978.53 |
| Kante ≥ 0,10, Vorlauf 2, Bestätigen | 2653 | 1717 | 64.7 % | +1.05 | +2780.30 | +2241.19 |
| Kante ≥ 0,15, Vorlauf 1, Finden | 1303 | 483 | 37.1 % | -1.96 | -2549.88 | -3178.45 |
| Kante ≥ 0,15, Vorlauf 1, Bestätigen | 2849 | 1652 | 58.0 % | +0.14 | +407.12 | -311.41 |
| Kante ≥ 0,15, Vorlauf 2, Finden | 714 | 310 | 43.4 % | -0.96 | -683.59 | -1312.02 |
| Kante ≥ 0,15, Vorlauf 2, Bestätigen | 1930 | 1354 | 70.2 % | +1.63 | +3149.12 | +2780.00 |

**Einzelmodelle** (nur zusätzlich berichtet)

| | Wetten | Treffer | Quote | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |
|---|---|---|---|---|---|---|
| nur ECMWF, Vorlauf 1, Finden | 2393 | 909 | 38.0 % | -1.51 | -3623.45 | -4462.38 |
| nur ECMWF, Vorlauf 1, Bestätigen | 3936 | 2115 | 53.7 % | -0.21 | -817.12 | -1663.09 |
| nur ECMWF, Vorlauf 2, Finden | 1610 | 721 | 44.8 % | -0.98 | -1573.42 | -2395.12 |
| nur ECMWF, Vorlauf 2, Bestätigen | 2659 | 1715 | 64.5 % | +0.78 | +2070.57 | +1571.42 |
| nur GFS, Vorlauf 1, Finden | 2655 | 1117 | 42.1 % | -1.60 | -4247.71 | -5070.26 |
| nur GFS, Vorlauf 1, Bestätigen | 4424 | 2319 | 52.4 % | -0.47 | -2090.72 | -3005.84 |
| nur GFS, Vorlauf 2, Finden | 1854 | 859 | 46.3 % | -1.25 | -2312.69 | -3199.21 |
| nur GFS, Vorlauf 2, Bestätigen | 3059 | 1903 | 62.2 % | +0.21 | +657.22 | +202.77 |

## Zusatzauswertung zur Preisqualität (NACHTRÄGLICH, nicht Teil der festgeschriebenen Regeln, ändert das Urteil nicht)

Beim Prüfen der Kalibrierung fiel auf, dass die Marktpreise der Bestätigungshälfte systematisch zu hoch liegen (Summe der Ja-Preise eines Events statt ca. 1,0 oft 1,3 bis 2,9). Die Summe ist **zum Entscheidungszeitpunkt bekannt**, ein Filter darauf enthält also keinen Blick in die Zukunft. Ursache: Tiefsttemperatur-Märkte ab Mitte August wurden erst kurz vor dem Entscheidungszeitpunkt eröffnet und zeigen dann flache Startpreise (0,2–0,3 für alle Buckets) statt echter Preisbildung. Mittlere Preissumme je Art und Monat (Vorlauf 1, nur Events mit allen Preisen):

| Art | Monat | Events | mittlere Preissumme | Anteil Summe > 1,3 |
|---|---|---|---|---|
| Höchstwert | 2026-03 | 437 | 1.008 | 0.0 % |
| Höchstwert | 2026-04 | 450 | 1.009 | 0.0 % |
| Höchstwert | 2026-05 | 413 | 1.033 | 0.5 % |
| Höchstwert | 2026-06 | 439 | 1.024 | 0.0 % |
| Höchstwert | 2026-07 | 464 | 1.031 | 0.0 % |
| Höchstwert | 2026-08 | 465 | 1.034 | 0.2 % |
| Höchstwert | 2026-09 | 450 | 1.034 | 0.0 % |
| Höchstwert | 2026-10 | 165 | 1.021 | 0.0 % |
| Tiefstwert | 2026-04 | 46 | 1.136 | 10.9 % |
| Tiefstwert | 2026-05 | 120 | 0.992 | 0.8 % |
| Tiefstwert | 2026-06 | 150 | 0.997 | 0.0 % |
| Tiefstwert | 2026-07 | 155 | 1.021 | 0.0 % |
| Tiefstwert | 2026-08 | 262 | 1.417 | 35.5 % |
| Tiefstwert | 2026-09 | 450 | 1.976 | 65.8 % |
| Tiefstwert | 2026-10 | 164 | 2.787 | 89.6 % |

Anteil der Events mit plausibler Preissumme (0,90–1,15, alle Buckets bepreist): Vorlauf 1 84.8 %, Vorlauf 2 70.4 %. Hauptregel nur auf diesen Events:

| | Wetten | Treffer | Quote | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) | Brier Modell / Markt |
|---|---|---|---|---|---|---|---|
| alle Arten, Vorlauf 1, Finden | 2063 | 798 | 38.7 % | -1.88 | -3886.31 | -4538.72 | 0.0665 / 0.0585 |
| alle Arten, Vorlauf 1, Bestätigen | 2776 | 1064 | 38.3 % | -1.87 | -5180.19 | -6038.26 | 0.0712 / 0.0599 |
| alle Arten, Vorlauf 2, Finden | 1244 | 513 | 41.2 % | -1.53 | -1904.07 | -2532.50 | 0.0684 / 0.0619 |
| alle Arten, Vorlauf 2, Bestätigen | 1210 | 525 | 43.4 % | -1.81 | -2187.73 | -2726.84 | 0.0716 / 0.0627 |
| nur Höchstwerte, Vorlauf 1, Finden | 1831 | 697 | 38.1 % | -2.05 | -3758.57 | -4410.98 | 0.0664 / 0.0579 |
| nur Höchstwerte, Vorlauf 1, Bestätigen | 2213 | 866 | 39.1 % | -1.97 | -4359.81 | -5137.91 | 0.0716 / 0.0600 |
| nur Höchstwerte, Vorlauf 2, Finden | 1116 | 450 | 40.3 % | -1.80 | -2003.94 | -2530.33 | 0.0684 / 0.0614 |
| nur Höchstwerte, Vorlauf 2, Bestätigen | 1012 | 456 | 45.1 % | -1.52 | -1535.09 | -2074.20 | 0.0723 / 0.0632 |
| nur Tiefstwerte, Vorlauf 1, Finden | 232 | 101 | 43.5 % | -0.55 | -127.74 | -463.01 | 0.0671 / 0.0626 |
| nur Tiefstwerte, Vorlauf 1, Bestätigen | 563 | 198 | 35.2 % | -1.46 | -820.39 | -1496.39 | 0.0697 / 0.0595 |
| nur Tiefstwerte, Vorlauf 2, Finden | 128 | 63 | 49.2 % | +0.78 | +99.87 | -271.29 | 0.0687 / 0.0670 |
| nur Tiefstwerte, Vorlauf 2, Bestätigen | 198 | 69 | 34.8 % | -3.30 | -652.65 | -847.08 | 0.0677 / 0.0598 |

Die Tabelle ist eine Beschreibung nach Sicht der Daten. Sie zeigt, wie stark das Hauptergebnis der Bestätigungshälfte (vor allem die Nein-Wetten bei Vorlauf 2) von unreifen Marktpreisen abhängt.


## Zusatzauswertung: Ist der Gewinn der Nein-Wetten (Vorlauf 2) ein Artefakt? (NACHTRÄGLICH, nicht Teil der festgeschriebenen Regeln, ändert das Urteil nicht)

Grundgesamtheit: Hauptwetten, Seite Nein, Vorlauf 2, Bestätigungshälfte. Nur vorhandene Daten, keine neuen Abrufe. „Preis des Buckets“ = Ja-Preis des Buckets zum Entscheidungszeitpunkt.

| | Wetten | Treffer | Quote | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |
|---|---|---|---|---|---|---|
| alle Nein-Wetten V2, Bestätigen | 2163 | 1677 | 77.5 % | +2.05 | +4429.54 | +4358.88 |

**Nach Preissumme des Events** (Summe der Ja-Preise aller Buckets, zum Entscheidungszeitpunkt bekannt)

| | Wetten | Treffer | Quote | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |
|---|---|---|---|---|---|---|
| plausibel (0,95–1,10) | 665 | 394 | 59.2 % | -0.80 | -530.42 | -598.82 |
| darüber (> 1,10) | 1484 | 1270 | 85.6 % | +3.31 | +4914.12 | +4872.95 |
| darunter (< 0,95) | 12 | 11 | 91.7 % | +2.70 | +32.45 | +13.30 |
| unbekannt (nicht alle Buckets bepreist) | 2 | 2 | 100.0 % | +6.70 | +13.40 | +0.00 |

**Nach Preis des Buckets**

| | Wetten | Treffer | Quote | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |
|---|---|---|---|---|---|---|
| Ja-Preis < 0,05 | 0 | 0 | – | – | +0.00 | +0.00 |
| 0,05 – 0,20 | 81 | 81 | 100.0 % | +1.76 | +142.96 | +136.71 |
| > 0,20 | 2082 | 1596 | 76.7 % | +2.06 | +4286.58 | +4215.91 |

**Kreuztabelle Preissumme × Preis des Buckets**

| | Wetten | Treffer | Quote | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |
|---|---|---|---|---|---|---|
| plausibel (0,95–1,10) / Ja-Preis < 0,05 | 0 | 0 | – | – | +0.00 | +0.00 |
| plausibel (0,95–1,10) / 0,05 – 0,20 | 2 | 2 | 100.0 % | +1.88 | +3.76 | +0.00 |
| plausibel (0,95–1,10) / > 0,20 | 663 | 392 | 59.1 % | -0.81 | -534.18 | -602.57 |
| darüber (> 1,10) / Ja-Preis < 0,05 | 0 | 0 | – | – | +0.00 | +0.00 |
| darüber (> 1,10) / 0,05 – 0,20 | 78 | 78 | 100.0 % | +1.76 | +137.26 | +131.00 |
| darüber (> 1,10) / > 0,20 | 1406 | 1192 | 84.8 % | +3.40 | +4776.85 | +4735.69 |
| darunter (< 0,95) / Ja-Preis < 0,05 | 0 | 0 | – | – | +0.00 | +0.00 |
| darunter (< 0,95) / 0,05 – 0,20 | 1 | 1 | 100.0 % | +1.95 | +1.95 | +0.00 |
| darunter (< 0,95) / > 0,20 | 11 | 10 | 90.9 % | +2.77 | +30.51 | +11.35 |
| unbekannt (nicht alle Buckets bepreist) / Ja-Preis < 0,05 | 0 | 0 | – | – | +0.00 | +0.00 |
| unbekannt (nicht alle Buckets bepreist) / 0,05 – 0,20 | 0 | 0 | – | – | +0.00 | +0.00 |
| unbekannt (nicht alle Buckets bepreist) / > 0,20 | 2 | 2 | 100.0 % | +6.70 | +13.40 | +0.00 |

**Alter des Preispunkts zur Entscheidung** (Näherung, siehe Hinweis)

Gemessen wird hier die Zeit zwischen dem letzten Preispunkt im 10-Minuten-Raster und dem Entscheidungszeitpunkt, **nicht** die Zeit seit der letzten Preisänderung oder dem letzten Handel: Die Preishistorie schreibt fehlende Minuten fort, und im Cache liegt je Token nur dieser letzte Rasterpunkt. Das echte Alter eines Preises ist damit **nicht bestimmbar**; dafür wäre ein neuer Abruf der Rohreihen nötig. Verteilung über alle Hauptwetten (Minuten): Minimum 0.0, Median 0.0, 90 % 0.0, 99 % 0.0, Maximum 0.0.

| | Wetten | Treffer | Quote | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |
|---|---|---|---|---|---|---|
| Nein V2 Bestätigen, Rasterpunkt < 1 h alt | 2163 | 1677 | 77.5 % | +2.05 | +4429.54 | +4358.88 |
| Nein V2 Bestätigen, Rasterpunkt 1 – 6 h alt | 0 | 0 | – | – | +0.00 | +0.00 |
| Nein V2 Bestätigen, Rasterpunkt > 6 h alt | 0 | 0 | – | – | +0.00 | +0.00 |
| alle Hauptwetten, Rasterpunkt < 1 h alt | 10124 | 5256 | 51.9 % | -0.36 | -3622.77 | -4480.84 |
| alle Hauptwetten, Rasterpunkt 1 – 6 h alt | 12 | 6 | 50.0 % | -3.67 | -44.09 | -55.47 |
| alle Hauptwetten, Rasterpunkt > 6 h alt | 8 | 3 | 37.5 % | -3.76 | -30.10 | -50.00 |

**Lesart (Stand der Zahlen oben):**

- **Der Gewinn kommt vollständig aus Events mit unplausibler Preissumme.** Von 2 163 Nein-Wetten (Vorlauf 2, Bestätigung, +4 430 $) liegen 1 484 bei einer Preissumme über 1,10: +4 914 $ (+3,31 $ je Wette, Trefferquote 85,6 %). Bei plausibler Preissumme (0,95–1,10) sind es 665 Wetten mit −530 $ (−0,80 $ je Wette, Trefferquote 59,2 %). Die übrigen 14 Wetten (Summe unter 0,95 oder nicht alle Buckets bepreist) sind zu wenige für eine Aussage.
- **Nach Preis des Buckets** steckt der Gewinn bei Ja-Preisen über 0,20 (2 082 Wetten, +4 287 $); die 81 Wetten mit Ja-Preis 0,05–0,20 gewinnen alle (+143 $) und sind zu wenige. Nein-Wetten auf Buckets mit Ja-Preis unter 0,05 kommen nie vor (Kante nach Kosten nicht erreichbar).
- **Alter der Preise: nicht prüfbar.** Alle 2 163 Wetten haben einen Rasterpunkt unter einer Stunde Abstand zum Entscheidungszeitpunkt (Median 9,8 Minuten). Das ist ein Merkmal des fortgeschriebenen 10-Minuten-Rasters, nicht der Preise: ob ein Preis zuletzt vor 10 Minuten oder vor 10 Stunden gehandelt wurde, ist in den vorhandenen Daten nicht enthalten. Die Frage „veraltete Preise?“ ist deshalb nur indirekt beantwortbar: Die Preissumme über 1,10 spricht für unreife oder nicht gehandelte Preise (siehe Zusatzauswertung zur Preisqualität), aber nicht für ein bestimmtes Alter. Eine direkte Antwort bräuchte die Rohreihen (neuer Abruf).
- **Schluss:** Der formale Erfolg von Vorlauf 2 beruht auf Events, deren Preise in sich nicht stimmig sind (Summe der Ja-Preise über 1,10). Dort sind Nein-Wetten zu diesen Preisen praktisch nicht handelbar. Wo die Preise stimmig sind, verliert die Strategie. Das ist die Grundlage für das Urteil unten.



## Empfindlichkeit: Spread 0,02 / 0,04 / 0,06 (Kante ≥ 0,10, Ja und Nein)

| | Wetten | Treffer | Quote | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |
|---|---|---|---|---|---|---|
| Spread 0,02, Vorlauf 1, Finden | 2369 | 908 | 38.3 % | -1.34 | -3166.89 | -4227.28 |
| Spread 0,02, Vorlauf 1, Bestätigen | 4094 | 2125 | 51.9 % | +0.05 | +196.68 | -1063.18 |
| Spread 0,02, Vorlauf 2, Finden | 1625 | 736 | 45.3 % | -0.05 | -87.03 | -1004.18 |
| Spread 0,02, Vorlauf 2, Bestätigen | 2800 | 1782 | 63.6 % | +1.26 | +3518.54 | +2836.47 |
| Spread 0,04, Vorlauf 1, Finden | 2168 | 842 | 38.8 % | -1.86 | -4034.64 | -4687.04 |
| Spread 0,04, Vorlauf 1, Bestätigen | 3876 | 2058 | 53.1 % | -0.28 | -1092.52 | -1950.59 |
| Spread 0,04, Vorlauf 2, Finden | 1447 | 648 | 44.8 % | -0.93 | -1350.10 | -1978.53 |
| Spread 0,04, Vorlauf 2, Bestätigen | 2653 | 1717 | 64.7 % | +1.05 | +2780.30 | +2241.19 |
| Spread 0,06, Vorlauf 1, Finden | 1978 | 763 | 38.6 % | -2.18 | -4319.99 | -4839.87 |
| Spread 0,06, Vorlauf 1, Bestätigen | 3673 | 1988 | 54.1 % | -0.51 | -1868.75 | -2516.40 |
| Spread 0,06, Vorlauf 2, Finden | 1273 | 568 | 44.6 % | -1.31 | -1665.26 | -2168.48 |
| Spread 0,06, Vorlauf 2, Bestätigen | 2497 | 1634 | 65.4 % | +0.75 | +1881.43 | +1481.80 |

## Look-ahead-Prüfung

Alle 10144 Hauptwetten wurden maschinell geprüft: Läufe, die nach dem Entscheidungszeitpunkt verfügbar wurden: **0**; Preispunkte nach dem Entscheidungszeitpunkt: **0**. Stichprobe von 20 Wetten (Zufallssamen 42). „Lauf bekannt ab“ = spätester Init der Stützstellen der Stunde des Tagesextrems + 10 h (angenommene Verfügbarkeit); „spätester genutzter Lauf bekannt ab“ gilt für alle 24 Stunden des Tages.

| Event | Vorl. | Wette | Entscheidung Td | Preispunkt | Preis (Ja) | ECMWF-Lauf (Stunde des Extrems) | Lauf bekannt ab | spätester genutzter Lauf bekannt ab | Prognose bekannt vor Td | Preis vor Td |
|---|---|---|---|---|---|---|---|---|---|---|
| dallas 2026-07-10 hoechst | 1 | ja 102-103°F | 2026-07-09 23:00Z | 2026-07-09 22:50Z | 0.075 | N=2, Init 2026-07-08 18:00Z | 2026-07-09 04:00Z | 2026-07-09 22:00Z | ja | ja |
| ankara 2026-05-08 hoechst | 1 | ja 20°C | 2026-05-07 15:00Z | 2026-05-07 14:50Z | 0.145 | N=2, Init 2026-05-06 12:00Z | 2026-05-06 22:00Z | 2026-05-07 10:00Z | ja | ja |
| sao-paulo 2026-04-24 hoechst | 2 | nein 28°C | 2026-04-22 21:00Z | 2026-04-22 20:50Z | 0.210 | N=3, Init 2026-04-21 18:00Z | 2026-04-22 04:00Z | 2026-04-22 16:00Z | ja | ja |
| paris 2026-04-23 hoechst | 1 | ja 20°C | 2026-04-22 16:00Z | 2026-04-22 15:50Z | 0.050 | N=2, Init 2026-04-21 18:00Z | 2026-04-22 04:00Z | 2026-04-22 16:00Z | ja | ja |
| nyc 2026-08-10 hoechst | 1 | nein 92-93°F | 2026-08-09 22:00Z | 2026-08-09 21:50Z | 0.495 | N=2, Init 2026-08-09 00:00Z | 2026-08-09 10:00Z | 2026-08-09 22:00Z | ja | ja |
| london 2026-07-17 hoechst | 1 | ja 30°C | 2026-07-16 17:00Z | 2026-07-16 16:50Z | 0.023 | N=2, Init 2026-07-15 18:00Z | 2026-07-16 04:00Z | 2026-07-16 16:00Z | ja | ja |
| chicago 2026-09-03 hoechst | 2 | nein 88-89°F | 2026-09-01 23:00Z | 2026-09-01 22:40Z | 0.300 | N=3, Init 2026-09-01 00:00Z | 2026-09-01 10:00Z | 2026-09-01 22:00Z | ja | ja |
| paris 2026-10-04 tiefst | 2 | nein 18°C | 2026-10-02 16:00Z | 2026-10-02 15:50Z | 0.350 | N=3, Init 2026-10-01 12:00Z | 2026-10-01 22:00Z | 2026-10-02 16:00Z | ja | ja |
| chicago 2026-08-06 hoechst | 1 | nein 78-79°F | 2026-08-05 23:00Z | 2026-08-05 22:50Z | 0.385 | N=2, Init 2026-08-05 00:00Z | 2026-08-05 10:00Z | 2026-08-05 22:00Z | ja | ja |
| seoul 2026-10-06 tiefst | 1 | nein 12°C | 2026-10-05 09:00Z | 2026-10-05 08:50Z | 0.340 | N=1, Init 2026-10-04 18:00Z | 2026-10-05 04:00Z | 2026-10-05 04:00Z | ja | ja |
| buenos-aires 2026-10-02 tiefst | 2 | nein 15°C or higher | 2026-09-30 21:00Z | 2026-09-30 20:50Z | 0.495 | N=2, Init 2026-09-30 06:00Z | 2026-09-30 16:00Z | 2026-09-30 16:00Z | ja | ja |
| ankara 2026-09-04 hoechst | 1 | nein 28°C | 2026-09-03 15:00Z | 2026-09-03 14:50Z | 0.510 | N=2, Init 2026-09-02 06:00Z | 2026-09-02 16:00Z | 2026-09-03 10:00Z | ja | ja |
| ankara 2026-09-21 hoechst | 2 | nein 25°C | 2026-09-19 15:00Z | 2026-09-19 14:50Z | 0.450 | N=3, Init 2026-09-18 12:00Z | 2026-09-18 22:00Z | 2026-09-19 10:00Z | ja | ja |
| chicago 2026-03-25 hoechst | 1 | ja 64-65°F | 2026-03-24 23:00Z | 2026-03-24 22:50Z | 0.085 | N=2, Init 2026-03-23 18:00Z | 2026-03-24 04:00Z | 2026-03-24 22:00Z | ja | ja |
| miami 2026-09-27 hoechst | 2 | nein 88-89°F | 2026-09-25 22:00Z | 2026-09-25 21:50Z | 0.505 | N=3, Init 2026-09-25 00:00Z | 2026-09-25 10:00Z | 2026-09-25 22:00Z | ja | ja |
| nyc 2026-03-02 hoechst | 2 | nein 30-31°F | 2026-02-28 23:00Z | 2026-02-28 22:50Z | 0.340 | N=3, Init 2026-02-28 00:00Z | 2026-02-28 10:00Z | 2026-02-28 22:00Z | ja | ja |
| miami 2026-09-28 tiefst | 1 | nein 72-73°F | 2026-09-27 22:00Z | 2026-09-27 21:50Z | 0.335 | N=2, Init 2026-09-26 18:00Z | 2026-09-27 04:00Z | 2026-09-27 22:00Z | ja | ja |
| toronto 2026-09-14 tiefst | 2 | nein 6°C or below | 2026-09-12 22:00Z | 2026-09-12 21:50Z | 0.370 | N=2, Init 2026-09-12 12:00Z | 2026-09-12 22:00Z | 2026-09-12 22:00Z | ja | ja |
| ankara 2026-10-05 hoechst | 1 | nein 21°C | 2026-10-04 15:00Z | 2026-10-04 14:50Z | 0.485 | N=2, Init 2026-10-03 12:00Z | 2026-10-03 22:00Z | 2026-10-04 10:00Z | ja | ja |
| sao-paulo 2026-09-26 tiefst | 1 | nein 24°C or higher | 2026-09-25 21:00Z | 2026-09-25 20:50Z | 0.490 | N=2, Init 2026-09-24 12:00Z | 2026-09-24 22:00Z | 2026-09-25 16:00Z | ja | ja |

## Gegenrechnung mit einem unabhängigen Skript

`auswertungen/rueckrechnung_gegenrechnung.py` (eigene Zeitlogik, Intervall-Wahrscheinlichkeit statt Runden, kein numpy, ohne Import des Hauptskripts) rechnet aus denselben Rohdaten. Vergleich (Hauptregel; Differenz in $ bzw. Brier):

| Größe | Hauptskript | Gegenrechnung | Differenz |
|---|---|---|---|
| Wetten/Summe V1 finden S0.02 | 2369 / -3166.89 | 2369 / -3166.89 | +0 / -0.0000 |
| Wetten/Summe V1 finden S0.04 | 2168 / -4034.64 | 2168 / -4034.64 | +0 / -0.0000 |
| ohne 3 beste V1 finden | -4687.04 | -4687.04 | -0.0000 |
| Wetten/Summe V1 finden S0.06 | 1978 / -4319.99 | 1978 / -4319.99 | +0 / -0.0000 |
| Wetten/Summe V1 bestaetigen S0.02 | 4094 / +196.68 | 4094 / +196.68 | +0 / +0.0000 |
| Wetten/Summe V1 bestaetigen S0.04 | 3876 / -1092.52 | 3876 / -1092.52 | +0 / +0.0000 |
| ohne 3 beste V1 bestaetigen | -1950.59 | -1950.59 | +0.0000 |
| Wetten/Summe V1 bestaetigen S0.06 | 3673 / -1868.75 | 3673 / -1868.75 | +0 / +0.0000 |
| Brier Modell V1 finden (n=22173/22173) | 0.066590 | 0.066590 | +1.39e-17 |
| Brier Markt V1 finden (n=22173/22173) | 0.058880 | 0.058880 | +0.00e+00 |
| Brier Modell V1 bestaetigen (n=28335/28335) | 0.070501 | 0.070501 | -1.39e-17 |
| Brier Markt V1 bestaetigen (n=28335/28335) | 0.069289 | 0.069289 | -6.94e-17 |
| Wetten/Summe V2 finden S0.02 | 1625 / -87.03 | 1625 / -87.03 | +0 / -0.0000 |
| Wetten/Summe V2 finden S0.04 | 1447 / -1350.10 | 1447 / -1350.10 | +0 / -0.0000 |
| ohne 3 beste V2 finden | -1978.53 | -1978.53 | -0.0000 |
| Wetten/Summe V2 finden S0.06 | 1273 / -1665.26 | 1273 / -1665.26 | +0 / +0.0000 |
| Wetten/Summe V2 bestaetigen S0.02 | 2800 / +3518.54 | 2800 / +3518.54 | +0 / +0.0000 |
| Wetten/Summe V2 bestaetigen S0.04 | 2653 / +2780.30 | 2653 / +2780.30 | +0 / +0.0000 |
| ohne 3 beste V2 bestaetigen | +2241.19 | +2241.19 | +0.0000 |
| Wetten/Summe V2 bestaetigen S0.06 | 2497 / +1881.43 | 2497 / +1881.43 | +0 / +0.0000 |
| Brier Modell V2 finden (n=17992/17992) | 0.068366 | 0.068366 | -2.78e-17 |
| Brier Markt V2 finden (n=17992/17992) | 0.062749 | 0.062749 | -8.33e-17 |
| Brier Modell V2 bestaetigen (n=19997/19997) | 0.071336 | 0.071336 | +0.00e+00 |
| Brier Markt V2 bestaetigen (n=19997/19997) | 0.078781 | 0.078781 | -2.78e-17 |

Größte Abweichung: 2.50e-12. **Übereinstimmung.**

## Was die Rückrechnung nicht zeigt

- **Keine echten Ensembles.** Die Wahrscheinlichkeiten stammen aus zwei deterministischen Modellen plus einer aus 2024–2025 gelernten Fehlerverteilung (je Station, Vorlauf und Art, Mar–Okt). Das Live-Protokoll sammelt echte Ensembles; dieses Verfahren sagt nichts darüber, ob sie besser wären.
- **Angenommener Spread** (0,02/0,04/0,06) statt echter Geld-/Brief-Kurse. Die Preishistorie liefert nur Preispunkte (Mitte oder letzter Handel, genaue Definition unbekannt) und, mit `fidelity = 10`, ein 10-Minuten-Raster, das fehlende Handelsminuten fortschreibt: ein „letzter Preispunkt“ kann alt sein. Der Nein-Preis ist als 1 − Ja-Preis angenommen.
- **Keine Markttiefe.** 10 $ je Wette wurden vollständig zum angenommenen Preis gefüllt angenommen. Die Medianliquidität liegt bei ca. 1 400 $ je Bucket; bei dünnen Büchern wäre die Ausführung schlechter, und bei vielen gleichzeitigen Wetten (mehrere Städte, gleiche Tage) bewegt man den Preis. Tick und Mindestgröße sind nicht berücksichtigt.
- **Quellenwechsel am 2026-08-23** (Weather Underground → NOAA): Die Fehlerverteilung kommt aus METAR; die Auflösung der frühen Märkte lief über Weather Underground, die späten über NOAA. Beide beruhen auf METAR (Übereinstimmung ≥ 96 % mit dem Gewinner), die restlichen Abweichungen sind nicht untersucht und sind in den Ergebnissen als Rauschen enthalten.
- **Angenommene Verfügbarkeit der Läufe** (10 h nach Init, gemessen 9,0–9,3 h heute). Historisch kann sie anders gewesen sein; ein späterer Zeitpunkt wäre vorsichtiger, ein früherer würde bei Vorlauf 1 mehr Stunden aus `previous_day1` zulassen.
- **Zusammensetzung statt „reinem“ Vorlauf:** Wegen der Verfügbarkeit stammt der Tageshöchstwert bei Vorlauf 1 großteils aus `previous_day2` (und bei Vorlauf 2 aus `previous_day3`). Der wirksame Vorlauf ist länger als der Name.
- **Preis zum Entscheidungszeitpunkt:** Der Preis um 18:00 Ortszeit spiegelt nur Informationen bis dahin; spätere (bessere) Vorhersagen am Abend und am Tag selbst, die der Markt aufnimmt, sind nicht erfasst. Das ist die vereinbarte Regel, nicht der Zeitpunkt mit dem besten Preis.
- **Kleine Stichprobe und viele Zellen:** 15 Städte, 7 Monate, ein Jahr Markthistorie. Mehrfachvergleiche (Vorlauf × Hälfte × Seite × Schwelle × Spread) wurden nicht korrigiert; nur die vorab genannte Hauptzelle zählt für das Urteil.
- **Gebühren:** nach `docs/gebuehren.md`; Maker-Rebate und Taker-Rebate-Stufen sind nicht eingerechnet.
- **Nicht untersucht:** Hongkong, die übrigen 34 Städte und die Wirkung von ICON.
