# Zieltag im Protokoll: Zählung (2026-10-14)

Anlass: Der gemeinsame Codex-Review zeigte, dass `bot/maerkte.py` das Datum eines Events als `eventDate`, sonst `endDate[:10]` speichert und dass `endDate` bei 44 Events der Rückrechnung einen Tag nach dem Zieltag liegt. Hier wurde nur gezählt, nichts geändert (`auswertungen/zieltag_zaehlung.py`, liest Gamma und `daten/`).

## Ergebnis

| Frage | Ergebnis |
|---|---|
| Aktive Temperatur-Events jetzt (Gamma) | 274 |
| davon ohne `eventDate` | **0** |
| davon `eventDate` ≠ Zieltag im Slug | **0** |
| davon `endDate`-Tag ≠ Zieltag im Slug | **0** |
| Events im Protokoll (alle Stammdateien) | 328 |
| davon gespeichertes Datum ≠ Slug-Zieltag | **0** |
| Unlesbare Slugs | 0 |

Die 44 historischen Abweichungen der Rückrechnung (Zieltage 2026-03-16 bis 2026-04-15, immer `endDate` = Zieltag + 1; Städte: Chongqing, Peking, Wuhan, Shenzhen je 5, Taipeh, Chengdu je 4, Hongkong, Mailand, Madrid, Warschau je 3, Seoul, NYC, Tokio, Shanghai je 1; 40 Höchst-, 4 Tiefsttemperatur) haben dagegen **ein korrektes `eventDate`** (an drei Stichproben per Gamma geprüft: `eventDate` = Zieltag, `endDate` = Zieltag + 1 Tag 12:00 UTC). Das Protokoll liest zuerst `eventDate`, wäre von diesen 44 also nicht betroffen gewesen. Die Rückrechnung nutzte den Event-Cache ohne `eventDate`.

## Ensemble-Abruf

`bot/ensemble.py` holt je Station `forecast_days = 3` (lokal heute, morgen, übermorgen) und schreibt **alle** Tage, unabhängig vom Event-Datum; die Zuordnung zum Event läuft erst bei der Auswertung über (Stadt, Art, Datum). Entscheidungen mit Vorlauf 1 und 2 (Td = 18:00 Ortszeit am Tag davor bzw. zwei Tage davor) liegen im Fenster. Bei verschobenem Event-Datum fehlte also nichts im Abruf, nur die Zuordnung wäre falsch gewesen.

## Folgerung

- Im Protokoll tritt der Fehler derzeit **nicht** auf (0 von 328). Der Befund war ein Risiko des Rückfalls auf `endDate`, kein beobachteter Datenfehler.
- Die Korrektur im Auswerteskript (Zieltag aus dem Slug, Abweichungen werden gezählt) reicht für die Hypothese. Ein Umbau im Protokoll wäre Aufräumen: Zieltag aus dem Slug, `eventDate`/`endDate` nur zum Abgleich.
- Nebenbefund: `bot/aufloesung.py` setzt das Datum der Auflösung aus `endDate[:10]`. Die Auflösung der Hypothese nutzt nur `gewinner_bucket` je `event_slug`; betroffen wäre nur die METAR-Gegenprobe (Spalte `treffer`) bei einem Event wie den 44.
- `live_start.txt` muss wegen dieses Befunds **nicht** verschoben werden: Die Protokolldaten sind von ihm nicht betroffen. Es gilt weiter nur für die Koordinatenkorrektur.
