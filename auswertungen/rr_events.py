"""Rückrechnung, Schritt 1: alle geschlossenen Temperatur-Events laden (Cache) und die 15 Städte festlegen.

Nur Lesezugriffe auf die öffentliche Gamma-API. Abbrechbar und fortsetzbar: der Cursor steht im Cache.

Aufruf:  python auswertungen/rr_events.py [--auswahl]
"""
import argparse
import gzip
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bot.netz import get_json  # noqa: E402

CACHE = Path("daten/cache")
EVENTS = CACHE / "events_alle.json.gz"
KEYSET = "https://gamma-api.polymarket.com/events/keyset"
SLUG = re.compile(r"^(highest|lowest)-temperature-in-(.+?)-on-")


def schlank(ev: dict) -> dict:
    m = SLUG.match(ev["slug"])
    return {
        "slug": ev["slug"], "art": m.group(1), "stadt": m.group(2), "ende": ev["endDate"],
        "start": ev.get("startDate"), "quelle": ev.get("resolutionSource") or "",
        "text_station": _station_text(ev),
        "maerkte": [{"titel": k.get("groupItemTitle"), "token": json.loads(k["clobTokenIds"])[0],
                     "preise": k.get("outcomePrices"), "volumen": k.get("volumeNum")}
                    for k in ev["markets"] if k.get("clobTokenIds")],
    }


def _station_text(ev: dict) -> str | None:
    for text in (ev.get("resolutionSource") or "", ev.get("description") or ""):
        m = re.search(r"(?:site=|wunderground\.com/history/daily/[^\s]*/)([A-Za-z]{4})(?![A-Za-z])", text)
        if m:
            return m.group(1).upper()
    return None


def lade(neu: bool = False) -> list[dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    stand = {"events": [], "cursor": None, "fertig": False}
    if EVENTS.exists() and not neu:
        stand = json.loads(gzip.open(EVENTS, "rt", encoding="utf-8").read())
    if stand["fertig"]:
        return stand["events"]
    n = 0
    while True:
        p = {"tag_slug": "daily-temperature", "closed": "true", "limit": 100}
        if stand["cursor"]:
            p["after_cursor"] = stand["cursor"]
        j = get_json(KEYSET, p, timeout=120)
        stand["events"] += [schlank(e) for e in j["events"] if SLUG.match(e["slug"])]
        stand["cursor"] = j.get("next_cursor")
        n += 1
        if not stand["cursor"] or not j["events"]:
            stand["fertig"] = True
        if n % 10 == 0 or stand["fertig"]:  # Zwischenstand sichern (fortsetzbar)
            with gzip.open(EVENTS, "wt", encoding="utf-8") as f:
                f.write(json.dumps(stand))
            print(f"{len(stand['events'])} Events", flush=True)
        if stand["fertig"]:
            return stand["events"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--auswahl", action="store_true", help="Städte-Rangliste ausgeben")
    ap.add_argument("--neu", action="store_true")
    a = ap.parse_args()
    ev = lade(a.neu)
    print(len(ev), "Events im Cache")
    if a.auswahl:
        erste = {}
        n = {}
        for e in ev:
            d = e["ende"][:10]
            erste[e["stadt"]] = min(erste.get(e["stadt"], "9999"), d)
            n[e["stadt"]] = n.get(e["stadt"], 0) + 1
        for stadt in sorted(erste, key=lambda s: (erste[s], s)):
            print(f"{stadt:15s} erstes Event {erste[stadt]}  Events {n[stadt]}")


if __name__ == "__main__":
    main()
