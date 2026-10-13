---
typ: quelle
tags: [quelle, messung]
stand: 2026-10-13
---
# METAR über das Iowa Environmental Mesonet (IEM)

`https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py` mit `station=<ICAO>&data=tmpf&year1…day2&tz=Etc/UTC&format=onlycomma&report_type=3&report_type=4` (routine + Specials). Kein Schlüssel, weltweit (alle 48 getesteten Flughäfen lieferten Daten), Archiv über Jahre; mit `latlon=yes` kommen Koordinaten mit.

- Werte in °F (`tmpf`). Für °C-Märkte zurückrechnen und auf ganze Grad runden.
- Tageswert = Max/Min aller Beobachtungen des **lokalen Kalendertags** ([[Zeitzonen und lokaler Tag]]). Weniger als 8 Beobachtungen: Tag verwerfen.
- Übereinstimmung mit dem Polymarket-Gewinner: 99,3 % (Sept./Okt.), 98,2 % (Juni), 96,1 % (März, mit Station je Event). Siehe [[Auflösungsvalidierung METAR]].
- NOAA und Weather Underground zeigen dieselben METAR-Daten; beide wurden nicht direkt abgefragt (JS-Seiten ohne freie API). Meteostat wurde nicht getestet. `api.weather.gov` und `aviationweather.gov` liefern nur ca. die letzten Tage und wurden nicht getestet.
- Fair-Use: einmal je Station und Zeitraum abfragen.

Siehe auch [[Rundung und Auflösung]], [[Stationswechsel]].
