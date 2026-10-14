"""Rückrechnung, Schritt 2: Rohdaten laden und zwischenspeichern (daten/cache/, nicht im Git).

Nur Lesezugriffe auf öffentliche APIs, nacheinander, abbrechbar und fortsetzbar (vorhandene Cache-Dateien
werden übersprungen). Regeln: auswertungen/rueckrechnung_regeln.md

Aufruf:  python auswertungen/rr_daten.py stationen|messungen|prognosen|preise
"""
import csv
import gzip
import io
import json
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from auswertungen.rr_events import lade  # noqa: E402
from bot import rueckrechnung as rr  # noqa: E402
from bot.aufloesung import iem_messwerte  # noqa: E402
from bot.netz import anfrage, get_json, post_json  # noqa: E402
from bot.stationen import STATIONEN  # noqa: E402

CACHE = Path("daten/cache")
STAEDTE = "atlanta dallas nyc buenos-aires london seattle seoul toronto ankara chicago miami paris sao-paulo wellington lucknow".split()
TEST_VON, TEST_BIS = "2026-03-01", "2026-10-11"
BEREICHE = {  # Name -> (von, bis), jeweils mit einem Tag Rand für Zeitzonen
    "k2024": ("2024-02-28", "2024-11-01"),
    "k2025": ("2025-02-28", "2025-11-01"),
    "test": ("2026-02-26", "2026-10-13"),
}
MODELLE = {"ecmwf": "ecmwf_ifs025", "gfs": "gfs_seamless"}
PREV = "https://previous-runs-api.open-meteo.com/v1/forecast"
IEM_INFO = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"
BATCH = "https://clob.polymarket.com/batch-prices-history"
PAUSE_OM = 2.5


def test_events() -> list[dict]:
    """Events der 15 Städte mit Zieltag im Testzeitraum. Zieltag aus dem Slug (`ziel`), nicht aus `endDate`
    (Klarstellung 2026-10-14: bei einzelnen Events liegt `endDate` einen Tag später)."""
    ev = []
    for e in lade():
        if e["stadt"] not in STAEDTE:
            continue
        z = rr.zieldatum_aus_slug(e["slug"], e["ende"])
        if z and TEST_VON <= z <= TEST_BIS:
            ev.append({**e, "ziel": z})
    return sorted(ev, key=lambda e: (e["ziel"], e["slug"]))


def zieldatum_abweichungen() -> dict:
    """Alle Events (alle Städte), bei denen der Zieltag aus dem Slug nicht dem Datum von `endDate` entspricht,
    dazu Zähler für den Bericht. Unlesbare Slugs werden gezählt."""
    abw, unlesbar, ohne_jahr, gesamt = [], [], 0, 0
    for e in lade():
        gesamt += 1
        z = rr.zieldatum_aus_slug(e["slug"], e["ende"])
        if z is None:
            unlesbar.append(e["slug"])
            continue
        if not re.search(r"-on-[a-z]+-\d{1,2}-\d{4}$", e["slug"]):
            ohne_jahr += 1
        if z != e["ende"][:10]:
            abw.append({"slug": e["slug"], "stadt": e["stadt"], "ziel": z, "ende": e["ende"],
                        "tage": (date.fromisoformat(e["ende"][:10]) - date.fromisoformat(z)).days,
                        "in_15_staedten": e["stadt"] in STAEDTE,
                        "im_testzeitraum": TEST_VON <= z <= TEST_BIS})
    return {"events": gesamt, "abweichend": abw, "unlesbar": unlesbar, "slug_ohne_jahr": ohne_jahr}


def stationen_der_staedte() -> dict[str, str]:
    """ICAO -> Stadt (Paris hat zwei: LFPG und LFPB)."""
    out = {}
    for e in test_events():
        if e["text_station"]:
            out[e["text_station"]] = e["stadt"]
    return out


def koordinaten() -> dict[str, tuple[float, float]]:
    pfad = CACHE / "koordinaten.json"
    if pfad.exists():
        return json.loads(pfad.read_text(encoding="utf-8"))
    out = {}
    for icao in sorted(stationen_der_staedte()):
        r = anfrage("GET", IEM_INFO, params=dict(station=icao, data="tmpf", year1=2026, month1=10, day1=10, year2=2026,
                                                 month2=10, day2=11, tz="Etc/UTC", format="onlycomma", latlon="yes"))
        z = next(csv.DictReader(io.StringIO(r.text)))
        out[icao] = (round(float(z["lat"]), 4), round(float(z["lon"]), 4))
    pfad.write_text(json.dumps(out), encoding="utf-8")
    return out


def cmd_stationen():
    CACHE.mkdir(parents=True, exist_ok=True)
    st = stationen_der_staedte()
    print(len(st), "Stationen:", st)
    print(koordinaten())


def cmd_messungen():
    (CACHE / "messung").mkdir(parents=True, exist_ok=True)
    for icao in sorted(stationen_der_staedte()):
        for name, (von, bis) in BEREICHE.items():
            pfad = CACHE / "messung" / f"{icao}_{name}.json.gz"
            if pfad.exists():
                continue
            obs = iem_messwerte(icao, von, bis)
            ts = [int(t.replace(tzinfo=timezone.utc).timestamp()) for t, _ in obs]
            with gzip.open(pfad, "wt", encoding="utf-8") as f:
                f.write(json.dumps({"t": ts, "f": [v for _, v in obs]}))
            print(icao, name, len(obs), flush=True)


def cmd_prognosen():
    (CACHE / "prog").mkdir(parents=True, exist_ok=True)
    koord = koordinaten()
    for icao in sorted(koord):
        lat, lon = koord[icao]
        for mkurz, modell in MODELLE.items():
            for name, (von, bis) in BEREICHE.items():
                pfad = CACHE / "prog" / f"{icao}_{mkurz}_{name}.json.gz"
                if pfad.exists():
                    continue
                j = get_json(PREV, {"latitude": lat, "longitude": lon, "models": modell, "start_date": von, "end_date": bis,
                                    "hourly": "temperature_2m_previous_day1,temperature_2m_previous_day2,temperature_2m_previous_day3",
                                    "timezone": "UTC"}, timeout=120)
                h = j["hourly"]
                ts = [int(datetime.fromisoformat(t).replace(tzinfo=timezone.utc).timestamp()) for t in h["time"]]
                daten = {"t": ts}
                for n in (1, 2, 3):
                    daten[str(n)] = h[f"temperature_2m_previous_day{n}"]
                with gzip.open(pfad, "wt", encoding="utf-8") as f:
                    f.write(json.dumps(daten))
                print(icao, mkurz, name, len(ts), flush=True)
                time.sleep(PAUSE_OM)


def cmd_preise():
    CACHE.mkdir(parents=True, exist_ok=True)
    pfad = CACHE / "preise.jsonl"
    alle = test_events()
    soll = {e["slug"]: e for e in alle}
    behalten, verworfen = [], 0
    if pfad.exists():
        for zeile in pfad.read_text(encoding="utf-8").splitlines():
            try:
                z = json.loads(zeile)
            except ValueError:
                continue  # halb geschriebene letzte Zeile: wird neu geholt
            e = soll.get(z["slug"])
            # Zeilen, die mit einem anderen Zieltag abgerufen wurden (alt: endDate), werden verworfen und neu geholt
            if e is not None and rr.preiszeile_gueltig(z, e["ziel"], STATIONEN[e["stadt"]].tz):
                behalten.append(zeile)
            else:
                verworfen += 1
        pfad.write_text("".join(z + "\n" for z in behalten), encoding="utf-8")
    fertig = {json.loads(z)["slug"] for z in behalten}
    ev = [e for e in alle if e["slug"] not in fertig]
    print(len(ev), "Events offen,", len(fertig), "fertig,", verworfen, "alte Zeilen verworfen", flush=True)
    with open(pfad, "a", encoding="utf-8") as out:
        for i, e in enumerate(ev):
            tz = STATIONEN[e["stadt"]].tz
            datum = e["ziel"]
            td = {v: rr.entscheidungszeit(datum, tz, v) for v in (1, 2)}
            fenster = (td[2] - 12 * 3600, td[1])
            tokens = [m["token"] for m in e["maerkte"]]
            antwort = post_json(BATCH, {"markets": tokens, "start_ts": fenster[0], "end_ts": fenster[1], "fidelity": 10}, timeout=60)
            hist = antwort.get("history", {})
            zeile = {"slug": e["slug"], "fenster": fenster, "td": td, "tok": {}}
            for tok in tokens:
                pts = hist.get(tok, [])
                je_v = {}
                for v in (1, 2):
                    ok = [(x["t"], x["p"]) for x in pts if td[v] - 12 * 3600 <= x["t"] <= td[v]]
                    je_v[str(v)] = [*max(ok), len(ok)] if ok else None
                zeile["tok"][tok] = je_v
            out.write(json.dumps(zeile) + "\n")
            out.flush()
            if (i + 1) % 200 == 0:
                print(f"{i + 1}/{len(ev)}", flush=True)
            time.sleep(0.25)


if __name__ == "__main__":
    {"stationen": cmd_stationen, "messungen": cmd_messungen, "prognosen": cmd_prognosen, "preise": cmd_preise}[sys.argv[1]]()
