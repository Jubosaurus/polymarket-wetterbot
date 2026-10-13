"""Prüft, ob METAR-Messwerte (IEM-Archiv) den tatsächlichen Polymarket-Gewinner
reproduzieren. Nur Lesezugriffe auf öffentliche APIs, keine Schlüssel.

Aufruf:  python auswertungen/validiere_aufloesung.py --von 2026-09-01 --bis 2026-09-30
"""
import argparse
import csv
import io
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bot.buckets import parse_bucket, runde_ganz  # noqa: E402
from bot.stationen import STATIONEN  # noqa: E402

KEYSET = "https://gamma-api.polymarket.com/events/keyset"
IEM = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
SLUG = re.compile(r"^(highest|lowest)-temperature-in-(.+?)-on-")


def geschlossene_events(von: str, bis: str):
    cursor = None
    while True:
        p = {"tag_slug": "daily-temperature", "closed": "true", "limit": 100,
             "end_date_min": von + "T00:00:00Z", "end_date_max": bis + "T23:59:59Z"}
        if cursor:
            p["after_cursor"] = cursor
        r = requests.get(KEYSET, params=p, timeout=120)
        r.raise_for_status()
        j = r.json()
        yield from j["events"]
        cursor = j.get("next_cursor")
        if not cursor or not j["events"]:
            return


_ICAO = re.compile(r"(?:site=|wunderground\.com/history/daily/[^\s]*/)([A-Za-z]{4})(?![A-Za-z])")


def station_aus_event(ev) -> str | None:
    """ICAO-Kennung aus dem Auflösungstext des Events (Quelle und Beschreibung).
    Die Station hat sich bei manchen Städten geändert (Paris, Denver), daher nie
    aus der heutigen Tabelle nehmen."""
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
        except (ValueError, KeyError, TypeError):
            pass
    return None


def iem_messwerte(icao: str, von: str, bis: str) -> list[tuple[datetime, float]]:
    d0 = datetime.fromisoformat(von) - timedelta(days=1)
    d1 = datetime.fromisoformat(bis) + timedelta(days=2)
    r = requests.get(IEM, params={
        "station": icao, "data": "tmpf", "year1": d0.year, "month1": d0.month, "day1": d0.day,
        "year2": d1.year, "month2": d1.month, "day2": d1.day, "tz": "Etc/UTC",
        "format": "onlycomma", "latlon": "no", "report_type": [3, 4]}, timeout=180)
    r.raise_for_status()
    out = []
    for row in csv.DictReader(io.StringIO(r.text)):
        try:
            t = datetime.strptime(row["valid"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            out.append((t, float(row["tmpf"])))
        except (ValueError, KeyError):
            continue
    return out


def tageswert(obs, tz, datum: str, art: str, einheit: str) -> int | None:
    z = ZoneInfo(tz)
    werte = [f for t, f in obs if t.astimezone(z).date().isoformat() == datum]
    if len(werte) < 8:  # zu wenige Beobachtungen für einen Tageswert
        return None
    w = max(werte) if art == "highest" else min(werte)
    return runde_ganz(w if einheit == "F" else (w - 32.0) * 5.0 / 9.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--von", required=True)
    ap.add_argument("--bis", required=True)
    a = ap.parse_args()

    ereignisse = defaultdict(list)  # (stadt, icao) -> Events
    unklar = 0
    for ev in geschlossene_events(a.von, a.bis):
        m = SLUG.match(ev["slug"])
        if not (m and m.group(2) in STATIONEN and STATIONEN[m.group(2)].quelle != "HKO"):
            continue
        icao = station_aus_event(ev)
        if icao is None:
            unklar += 1  # Station nicht bestimmbar: nicht raten, Event auslassen
            continue
        ereignisse[(m.group(2), icao)].append((m.group(1), ev["endDate"][:10], gewinner_titel(ev)))

    gesamt = treffer = 0
    for (stadt, icao), liste in sorted(ereignisse.items()):
        st = STATIONEN[stadt]
        obs = iem_messwerte(icao, a.von, a.bis)
        n = ok = keine = 0
        fehl = []
        for art, datum, titel in liste:
            if not titel:
                continue
            b = parse_bucket(titel)
            w = tageswert(obs, st.tz, datum, art, b.einheit)
            if w is None:
                keine += 1
                continue
            n += 1
            if b.enthaelt(w):
                ok += 1
            else:
                fehl.append(f"{art[:2]} {datum} gemessen={w} gewinner={titel}")
        gesamt += n
        treffer += ok
        print(f"{stadt:14s}{icao} n={n:3d} treffer={ok:3d} ({(ok / n * 100 if n else 0):5.1f}%) ohne_daten={keine}")
        for f in fehl[:3]:
            print("      ", f)
    print(f"Events ohne bestimmbare Station (ausgelassen): {unklar}")
    print(f"GESAMT n={gesamt} treffer={treffer} ({treffer / gesamt * 100 if gesamt else 0:.1f}%)")


if __name__ == "__main__":
    main()
