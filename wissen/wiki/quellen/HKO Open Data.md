---
typ: quelle
tags: [quelle, messung]
stand: 2026-10-13
---
# HKO Open Data (Hongkong)

`https://data.weather.gov.hk/weatherAPI/opendata/opendata.php?dataType=CLMMAXT|CLMMINT&rformat=json&station=HKO&year=JJJJ&month=M`: Tagesextremwerte des Hong Kong Observatory mit einer Nachkommastelle (`data`: Jahr, Monat, Tag, Wert, Vollständigkeit). Kein Schlüssel.

- Der laufende Monat ist **noch leer** (`data: []`), Daten erscheinen erst nach Monatsabschluss. Das Auflösungsprotokoll markiert HK-Events deshalb als „offen“ und versucht es später erneut.
- Auflösungsregel: **Abschneiden** auf ganze Grad, siehe [[Hongkong]] und [[Rundung und Auflösung]].
