---
typ: werkzeug
tags: [werkzeug, stationen, koordinaten, open-meteo]
stand: 2026-10-14
---
# Stationsprüfung (Koordinaten, Höhe, Quelle)

**Anlass:** Beim Abgleich der Stationstabelle (`bot/stationen.py`) mit einem unabhängigen Stationsverzeichnis fielen mehrere Koordinaten auf, die Stadtmitten statt Flughäfen waren. Gemessen am 2026-10-14.

## Methode

- Referenz: `https://aviationweather.gov/api/data/stationinfo?ids=<ICAO>&format=json` (Koordinaten und Höhe der METAR-Station, öffentlich, kein Schlüssel).
- Kontrolle: das IEM-Stationsverzeichnis (bisherige Quelle der Tabelle) führt für **ZUCK dieselben alten Stadtkoordinaten** (29,52 / 106,48; WMO 57516, Station Shapingba) und taugt deshalb nicht als Referenz für diese Stationen.
- Auflösungstext jedes Events (Cache `events_alle`): die Station im Text stimmt für alle aktiven Städte mit der Tabelle überein. Qingdao: „Qingdao Jiaodong International Airport“ = ZSQD, also der neue Flughafen (36,36 / 120,09), nicht die frühere Stadtkoordinate und nicht das alte Liuting.
- Open-Meteo: die Rasterhöhe (Antwortfeld `elevation`) wurde mit der Höhe der Station verglichen. Der Abruf übergibt keine eigene `elevation`; Open-Meteo korrigiert die Temperatur auf die Höhe des Geländemodells am Abrufpunkt, daher zählt, dass der Abrufpunkt am Flughafen liegt.

## Befund: Abstand Tabelle ↔ Flughafen

| Stadt | ICAO | vorher (km daneben) | Rasterhöhe vorher → nachher | Höhe Station |
|---|---|---|---|---|
| Qingdao | ZSQD | 39,6 | 38 → 8 m | 2 m |
| Chongqing | ZUCK | 26,9 | 320 → 413 m | 416 m |
| Wuhan | ZHHH | 19,5 | 26 → 32 m | 33 m |
| Chengdu | ZUUU | 11,9 | 507 → 493 m | 494 m |
| Karachi | OPKC | 6,7 | 13 → 19 m | 20 m |
| Jeddah | OEJN | 5,3 | 2 → 6 m | 8 m |
| Panama-Stadt | MPMG | 4,6 | 17 → 6 m | 6 m |
| Shanghai | ZSPD | 4,5 | 3 → 3 m | 4 m |
| Kuala Lumpur | WMKK | 3,7 | 9 → 27 m | 21 m |
| Dallas | KDAL | 1,8 | 144 → 146 m | 148 m |
| Beijing | ZBAA | 1,6 | 33 → 31 m | 31 m |
| Denver | KBKF | 1,4 | 1709 → 1700 m | 1703 m |
| München | EDDM | 1,2 | 442 → 445 m | 445 m |
| Helsinki | EFHK | 1,1 | 48 → 51 m | 56 m |
| Houston | KHOU | 0,9 | 12 → 13 m | 13 m |
| Guangzhou, San Francisco, Shenzhen | ZGGG, KSFO, ZGSZ | 0,8 | – | – |

Alle anderen Stationen liegen unter 0,5 km und blieben unverändert. **Hong Kong** (HKO) hat keinen Flughafen-METAR; die Tabellenkoordinate ist das Observatorium am Tsim Sha Tsui, die Rasterhöhe dort 18 m. Es gibt dafür keine METAR-Messreihe, deshalb keine Stationskorrektur (siehe [[Live-Hypothese 1]]).

## Unabhängiger Handabgleich

Ein manueller Stationscheck vom 14.10. (alle 49 Codes mit Polymarket verglichen: sie stimmen) hat die großen Abweichungen **ZUCK, ZHHH, ZUUU, OPKC und ZSQD** unabhängig von dieser Prüfung bestätigt.

## Betroffene Städte der Rückrechnung

Keine der 15 Städte der [[Rückrechnung]] ist von einer Korrektur betroffen: Die Rückrechnung holte die Koordinaten nicht aus `bot/stationen.py`, sondern aus dem IEM-Verzeichnis (`daten/cache/koordinaten.json`); für die 15 Städte (16 Stationen) liegen diese höchstens **1,8 km** (Dallas, Rasterhöhe 144 statt 146 m) neben der Referenz, sonst unter 0,5 km. Chongqing, Wuhan, Chengdu, Karachi, Qingdao, Shanghai und Hong Kong gehören nicht zu den 15. Die Rückrechnung wurde deshalb **nicht** neu gerechnet. Offen bleibt der Einfluss von Dallas (1,8 km, 2 m Rasterhöhe) auf das Ergebnis; er dürfte weit unter dem liegen, was das Urteil trägt.

## Folgen

- `bot/stationen.py`: 18 Koordinaten korrigiert (Test `test_korrigierte_koordinaten_nahe_am_flughafen`).
- **Live-Protokoll:** Die Ensemble-Abrufe nutzen `station.lat/lon`; alle Läufe bis zum Einspielen dieser Korrektur wurden für die genannten Städte am falschen Punkt abgerufen (nicht für die 15). Sie bleiben im Archiv, werden aber für die [[Live-Hypothese 1]] nicht gewertet (`auswertungen/live_start.txt`).
- Städte, die inzwischen nicht mehr gehandelt werden (Jinan ZSJN, Zhengzhou ZHCC; letzte Events 2026-09-29 bzw. 10-01), stehen nicht in der Tabelle und wurden nicht aufgenommen.

Siehe [[Städteübersicht]], [[Open-Meteo]], [[Bot-Module]], [[spaetere_pruefpunkte]].
