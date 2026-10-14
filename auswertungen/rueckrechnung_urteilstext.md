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
