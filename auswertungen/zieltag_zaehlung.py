"""Zählung: Wie oft weicht das Datum, das das Protokoll für ein Event speichert (eventDate, sonst endDate[:10]), vom Zieltag im Slug ab?

Nur Lesen und Zählen (öffentliche Gamma-API und daten/), ändert nichts. Aufruf:  python -m auswertungen.zieltag_zaehlung
Teil 1: aktive Events jetzt (Gamma). Teil 2: alle Events im Protokoll (Stammdateien). Teil 3: Enthält der Ensemble-Abruf den richtigen Tag?
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from auswertungen.live_auswertung import TAG, lese  # noqa: E402
from bot import maerkte  # noqa: E402
from bot import rueckrechnung as rr  # noqa: E402

DATEN = Path("daten")


def teil1() -> dict:
    ev = [e for e in maerkte.hole_events() if maerkte._event_kopf(e) and maerkte._event_kopf(e)[1]]
    aus = {"events": len(ev), "ohne_eventDate": 0, "slug_unlesbar": 0, "abweichend": 0, "eventDate_falsch": 0, "endDate_falsch": 0}
    je_stadt, je_art, bsp = Counter(), Counter(), []
    for e in ev:
        kopf = maerkte._event_kopf(e)
        ziel = rr.zieldatum_aus_slug(e["slug"], e.get("endDate"))
        ed = e.get("eventDate")
        if not ed:
            aus["ohne_eventDate"] += 1
        if ziel is None:
            aus["slug_unlesbar"] += 1
            continue
        if ed and ed != ziel:
            aus["eventDate_falsch"] += 1
        if e["endDate"][:10] != ziel:
            aus["endDate_falsch"] += 1
        if maerkte._datum(e) != ziel:
            aus["abweichend"] += 1
            je_stadt[kopf[1]] += 1
            je_art[kopf[0]] += 1
            if len(bsp) < 8:
                bsp.append((e["slug"], ed, e["endDate"], maerkte._datum(e), ziel))
    aus.update(je_stadt=dict(je_stadt), je_art=dict(je_art), beispiele=bsp)
    return aus


def teil2_3() -> dict:
    events = {}
    for tag in sorted(p for p in DATEN.iterdir() if p.is_dir() and TAG.match(p.name)):
        for f in sorted(tag.glob("maerkte_stamm_*.csv.gz")):
            for z in lese(f):
                if z["art"] in ("hoechst", "tiefst") and z["event_slug"] not in events:
                    events[z["event_slug"]] = z
    ens = {}  # (stadt, art, datum) -> Anzahl Zeilen
    for tag in sorted(p for p in DATEN.iterdir() if p.is_dir() and TAG.match(p.name)):
        for f in tag.glob("ensemble_*.csv.gz"):
            for z in lese(f):
                ens[(z["stadt"], z["art"], z["datum"])] = ens.get((z["stadt"], z["art"], z["datum"]), 0) + 1
    aus = {"events_im_protokoll": len(events), "abweichend": 0, "slug_unlesbar": 0, "ensemble_richtiger_tag_vorhanden": 0,
           "ensemble_nur_stamm_tag": 0, "ensemble_keines": 0}
    je_stadt, je_art, liste = Counter(), Counter(), []
    for slug, z in events.items():
        ziel = rr.zieldatum_aus_slug(slug, z["ende_utc"])
        if ziel is None:
            aus["slug_unlesbar"] += 1
            continue
        if ziel == z["datum"]:
            continue
        aus["abweichend"] += 1
        je_stadt[z["stadt"]] += 1
        je_art[z["art"]] += 1
        r = (z["stadt"], z["art"], ziel) in ens
        s = (z["stadt"], z["art"], z["datum"]) in ens
        aus["ensemble_richtiger_tag_vorhanden"] += r
        aus["ensemble_nur_stamm_tag"] += (s and not r)
        aus["ensemble_keines"] += (not s and not r)
        liste.append((slug, z["datum"], ziel, z["ende_utc"], r))
    aus.update(je_stadt=dict(je_stadt), je_art=dict(je_art), liste=liste[:12])
    return aus


if __name__ == "__main__":
    print(json.dumps({"aktiv_jetzt": teil1(), "protokoll": teil2_3()}, indent=1, ensure_ascii=False))
