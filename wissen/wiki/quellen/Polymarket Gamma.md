---
typ: quelle
tags: [quelle, polymarket]
stand: 2026-10-13
---
# Polymarket Gamma

Marktverzeichnis von Polymarket: `https://gamma-api.polymarket.com`. Kein Schlüssel nötig (lesend).

## Wettermärkte finden

- Aktive Events: `GET /events/keyset?tag_slug=weather&active=true&closed=false&limit=100[&after_cursor=…]` (Tag `weather`: ca. 344 Events; `daily-temperature`: Tagesmärkte Temperatur).
- Geschlossene Events: dieselbe Abfrage mit `closed=true`. Zeitfenster mit `end_date_min` / `end_date_max` (ISO-Zeit). Insgesamt ca. 14 000 geschlossene Temperatur-Events (153 000 Einzelmärkte) seit 2025-12-30.
- Slug-Muster: `highest|lowest-temperature-in-<stadt>-on-<monat>-<tag>-<jahr>`; Niederschlag: `where-will-it-rain-on-<monat>-<tag>-<jahr>`.

## Fallstricke (selbst erlebt)

- **Offset-Paginierung bricht bei Offset 2100 ab** (HTTP 422, „use /events/keyset“). Immer Keyset nehmen.
- `limit` über 100 wird stillschweigend auf 100 gekürzt.
- `endDate` ist nominell 12:00 UTC des Zieltages und **nicht** der Handelsschluss.
- `eventDate` fehlt bei alten Events (dann Datum aus `endDate`).
- `resolutionSource` ist bei Hongkong, Istanbul, Moskau und Tel Aviv **leer**, die Quelle steht nur in `description` (URL mit `site=<ICAO>`). Siehe [[Hongkong]] und [[Stationswechsel]].
- Einzelne Alt-Events (Jinan, Zhengzhou, 20. Mai 2026) sind noch „aktiv“, aber längst vorbei: ignorieren.
- Gewinner: Markt mit `outcomePrices[0] >= 0.99` (Yes).
- Jedes Event ist `negRisk`: genau ein Bucket gewinnt.

## Gebührenfelder je Markt

`feesEnabled`, `feeType` (`weather_fees`), `feeSchedule {rate, exponent, takerOnly, rebateRate}`. Details: [[Polymarket Gebühren]].

Grenzen: Ratenlimit nicht ausgereizt und nicht gemessen. Siehe auch [[Polymarket CLOB]], [[Live-Protokoll]].
