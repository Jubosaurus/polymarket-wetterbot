"""Prüft, ob METAR-Messwerte (IEM-Archiv) den tatsächlichen Polymarket-Gewinner
reproduzieren. Nur Lesezugriffe auf öffentliche APIs, keine Schlüssel.

Aufruf:  python auswertungen/validiere_aufloesung.py --von 2026-09-01 --bis 2026-09-30
"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bot.aufloesung import (  # noqa: E402
    SLUG, geschlossene_events, gewinner_titel, iem_messwerte, station_aus_event, tageswert,
)
from bot.buckets import parse_bucket  # noqa: E402
from bot.stationen import STATIONEN  # noqa: E402


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
            w, _ = tageswert(obs, st.tz, datum, art, b.einheit)
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
