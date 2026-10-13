"""Auflösungsprotokoll: je abgelaufenem Markt den METAR-Tageswert (IEM) und den
Polymarket-Gewinner festhalten und Abweichungen markieren.

Station je Event aus dem Auflösungstext (Paris, Denver haben gewechselt). Hong Kong
(HKO) wird über die HKO-Open-Data-Tageswerte geprüft und auf ganze Grad abgeschnitten.
"""
import csv
import io
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from bot.buckets import auf_ganz, parse_bucket
from bot.netz import anfrage, get_json
from bot.stationen import STATIONEN

KEYSET = "https://gamma-api.polymarket.com/events/keyset"
IEM = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
HKO = "https://data.weather.gov.hk/weatherAPI/opendata/opendata.php"
SLUG = re.compile(r"^(highest|lowest)-temperature-in-(.+?)-on-")
_ICAO = re.compile(r"(?:site=|wunderground\.com/history/daily/[^\s]*/)([A-Za-z]{4})(?![A-Za-z])")
MIN_BEOBACHTUNGEN = 8

SPALTEN_AUFLOESUNG = [
    "erfasst_utc", "event_slug", "stadt", "art", "datum", "icao", "einheit", "gewinner_bucket",
    "messwert", "messquelle", "n_beobachtungen", "treffer", "bemerkung",
]


def geschlossene_events(von: str, bis: str, hole=get_json):
    cursor = None
    while True:
        p = {"tag_slug": "daily-temperature", "closed": "true", "limit": 100,
             "end_date_min": von + "T00:00:00Z", "end_date_max": bis + "T23:59:59Z"}
        if cursor:
            p["after_cursor"] = cursor
        j = hole(KEYSET, p, timeout=120)
        yield from j["events"]
        cursor = j.get("next_cursor")
        if not cursor or not j["events"]:
            return


def station_aus_event(ev) -> str | None:
    """ICAO-Kennung aus dem Auflösungstext (Quelle, sonst Beschreibung); nie aus der
    heutigen Tabelle, da sich Stationen geändert haben."""
    for text in (ev.get("resolutionSource") or "", ev.get("description") or ""):
        m = _ICAO.search(text)
        if m:
            return m.group(1).upper()
    return None


def gewinner_titel(ev) -> str | None:
    for m in ev["markets"]:
        try:
            if float(json.loads(m["outcomePrices"])[0]) >= 0.99:
                return m["groupItemTitle"]
        except (ValueError, KeyError, TypeError, IndexError):
            pass
    return None


def iem_messwerte(icao: str, von: str, bis: str) -> list[tuple[datetime, float]]:
    d0 = datetime.fromisoformat(von) - timedelta(days=1)
    d1 = datetime.fromisoformat(bis) + timedelta(days=2)
    r = anfrage("GET", IEM, params={
        "station": icao, "data": "tmpf", "year1": d0.year, "month1": d0.month, "day1": d0.day,
        "year2": d1.year, "month2": d1.month, "day2": d1.day, "tz": "Etc/UTC",
        "format": "onlycomma", "latlon": "no", "report_type": [3, 4]}, timeout=180)
    out = []
    for row in csv.DictReader(io.StringIO(r.text)):
        try:
            t = datetime.strptime(row["valid"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            out.append((t, float(row["tmpf"])))
        except (ValueError, KeyError):
            continue
    return out


def tageswert(obs, tz: str, datum: str, art: str, einheit: str):
    """(ganzzahliger Tageswert, Anzahl Beobachtungen) oder (None, n) bei zu wenig Daten.
    Lokaler Kalendertag; Tmax/Tmin aller Beobachtungen; °C-Märkte rechnen aus °F zurück."""
    z = ZoneInfo(tz)
    werte = [f for t, f in obs if t.astimezone(z).date().isoformat() == datum]
    if len(werte) < MIN_BEOBACHTUNGEN:
        return None, len(werte)
    w = max(werte) if art == "highest" else min(werte)
    c_oder_f = w if einheit == "F" else (w - 32.0) * 5.0 / 9.0
    return auf_ganz(c_oder_f, "kaufm"), len(werte)


def hko_tageswerte(art: str, jahr: int, monat: int, hole=get_json) -> dict[str, float]:
    """datum -> Wert (°C, eine Nachkommastelle) aus den HKO-Open-Data (Monatsdatei).
    Leer, solange der Monat dort noch nicht veröffentlicht ist."""
    kind = "CLMMAXT" if art == "highest" else "CLMMINT"
    j = hole(HKO, {"dataType": kind, "rformat": "json", "station": "HKO", "year": jahr, "month": monat}, timeout=60)
    out = {}
    for zeile in j.get("data", []):
        try:
            out[f"{int(zeile[0]):04d}-{int(zeile[1]):02d}-{int(zeile[2]):02d}"] = float(zeile[3])
        except (ValueError, TypeError, IndexError):
            continue
    return out


def pruefe_events(events: list[dict], erfasst_iso: str, bereits: set[str],
                  hole_obs=iem_messwerte, hole_hko=hko_tageswerte) -> list[dict]:
    """Zeilen für noch nicht erfasste, entschiedene Events. Abweichung = treffer 0.
    Zeilen mit `_offen` haben noch keinen Messwert und werden vom Aufrufer nicht gespeichert,
    damit ein späterer Lauf sie erneut versucht."""
    kandidaten = defaultdict(list)
    zeilen = []
    for ev in events:
        m = SLUG.match(ev["slug"])
        if not m or ev["slug"] in bereits or m.group(2) not in STATIONEN:
            continue
        titel = gewinner_titel(ev)
        if titel is None:
            continue  # noch nicht entschieden: beim nächsten Mal erneut
        stadt, art = m.group(2), m.group(1)
        datum = ev["endDate"][:10]
        try:
            b = parse_bucket(titel)
        except ValueError:
            zeilen.append({"erfasst_utc": erfasst_iso, "event_slug": ev["slug"], "stadt": stadt, "art": art,
                           "datum": datum, "gewinner_bucket": titel, "bemerkung": "Bucket nicht lesbar"})
            continue
        base = {"erfasst_utc": erfasst_iso, "event_slug": ev["slug"], "stadt": stadt, "art": art,
                "datum": datum, "einheit": b.einheit, "gewinner_bucket": titel}
        if STATIONEN[stadt].quelle == "HKO":
            base["icao"] = "HKO"
            zeilen.append({**base, "_hko": True, "_bucket": b})
            continue
        icao = station_aus_event(ev)
        if icao is None:
            zeilen.append({**base, "bemerkung": "Station im Text nicht bestimmbar"})
            continue
        base["icao"] = icao
        kandidaten[icao].append({**base, "_bucket": b})
    fertig = [z for z in zeilen if "_hko" not in z]
    for z in zeilen:
        if "_hko" in z:
            b = z.pop("_bucket"); z.pop("_hko")
            jahr, monat = int(z["datum"][:4]), int(z["datum"][5:7])
            wert = hole_hko(z["art"], jahr, monat).get(z["datum"])
            if wert is None:
                z.update(bemerkung="HKO-Tageswert noch nicht veröffentlicht", _offen=True)
            else:
                ganz = auf_ganz(wert, "abschneiden")
                z.update(messwert=ganz, messquelle="HKO", treffer=int(b.enthaelt(ganz)),
                         bemerkung=f"HKO roh {wert:.1f}, abgeschnitten")
            fertig.append(z)
    for icao, liste in kandidaten.items():
        daten = sorted(z["datum"] for z in liste)
        try:
            obs = hole_obs(icao, daten[0], daten[-1])
        except RuntimeError as e:
            for z in liste:
                z.pop("_bucket")
                fertig.append({**z, "bemerkung": f"METAR-Abruf fehlgeschlagen: {str(e)[:80]}", "_offen": True})
            continue
        for z in liste:
            b = z.pop("_bucket")
            w, n = tageswert(obs, STATIONEN[z["stadt"]].tz, z["datum"], z["art"], b.einheit)
            z["n_beobachtungen"] = n
            if w is None:
                z.update(bemerkung="zu wenige METAR-Beobachtungen (späterer Lauf versucht es erneut)", _offen=True)
            else:
                z.update(messwert=w, messquelle="METAR", treffer=int(b.enthaelt(w)))
            fertig.append(z)
    return fertig
