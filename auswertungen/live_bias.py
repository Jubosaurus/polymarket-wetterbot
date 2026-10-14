"""Stationskorrektur (Bias) für die Live-Hypothese 1, für ALLE Stationen der Stationstabelle mit genug Daten.

Aufruf (nacheinander, abbrechbar und fortsetzbar; Cache in daten/cache/):
    python -m auswertungen.live_bias laden     # Messungen (IEM) und Prognosen (Open-Meteo Previous Runs) 2024/2025
    python -m auswertungen.live_bias rechnen   # schreibt auswertungen/live_bias.json

Gleiche Rechnung wie die Rückrechnung (auswertungen/rueckrechnung.py, Kalibrierung): Mittel aus ECMWF-IFS und GFS,
Komposit nur aus zum Entscheidungszeitpunkt bekannten Läufen, Residuum = Messwert − Vorhersage je Tag, März–Oktober
2024 und 2025. Unterschied zur Rückrechnung: Koordinaten aus der korrigierten Stationstabelle (bot/stationen.py,
Stand 2026-10-14) für ALLE Stationen. Nur Auswertung, keine Wetten. Hong Kong (HKO) hat keine METAR-Messreihe und
entfällt; Stationen mit weniger als MIN_TAGE Tagen je Vorlauf×Art entfallen und werden aufgelistet.
"""
import gzip
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from auswertungen.rr_daten import CACHE, MODELLE, PAUSE_OM, PREV, lade as lade_events  # noqa: E402
from auswertungen.rueckrechnung import KALIB_JAHRE, KALIB_MONATE, MIN_TAGE, RASTER_H, kalib_tage  # noqa: E402
from bot import rueckrechnung as rr  # noqa: E402
from bot.aufloesung import iem_messwerte  # noqa: E402
from bot.buckets import parse_bucket  # noqa: E402
from bot.netz import get_json  # noqa: E402
from bot.stationen import STATIONEN  # noqa: E402

AUS = Path("auswertungen/live_bias.json")
BEREICHE = {"k2024": ("2024-02-28", "2024-11-01"), "k2025": ("2025-02-28", "2025-11-01")}
PROG = CACHE / "prog_korr"  # Prognosen mit den korrigierten Koordinaten (neben dem Rückrechnungs-Cache prog/)
MESS = CACHE / "messung"


def stationen() -> dict[str, tuple[str, object]]:
    """ICAO -> (Stadt-Slug, Station) für alle Stationen mit METAR-Messreihe (ohne HKO)."""
    return {s.icao: (slug, s) for slug, s in STATIONEN.items() if s.quelle != "HKO"}


def einheiten() -> dict[str, str]:
    out = {}
    for e in lade_events():
        if e["stadt"] not in out and e["maerkte"]:
            out[e["stadt"]] = parse_bucket(e["maerkte"][0]["titel"]).einheit
    return out


def laden() -> None:
    PROG.mkdir(parents=True, exist_ok=True)
    MESS.mkdir(parents=True, exist_ok=True)
    for icao, (slug, st) in sorted(stationen().items()):
        for name, (von, bis) in BEREICHE.items():
            pfad = MESS / f"{icao}_{name}.json.gz"
            if not pfad.exists():
                obs = iem_messwerte(icao, von, bis)
                ts = [int(t.replace(tzinfo=timezone.utc).timestamp()) for t, _ in obs]
                with gzip.open(pfad, "wt", encoding="utf-8") as f:
                    f.write(json.dumps({"t": ts, "f": [v for _, v in obs]}))
                print("messung", icao, name, len(obs), flush=True)
            for mkurz, modell in MODELLE.items():
                pfad = PROG / f"{icao}_{mkurz}_{name}.json.gz"
                if pfad.exists():
                    continue
                j = get_json(PREV, {"latitude": st.lat, "longitude": st.lon, "models": modell, "start_date": von, "end_date": bis,
                                    "hourly": "temperature_2m_previous_day1,temperature_2m_previous_day2,temperature_2m_previous_day3",
                                    "timezone": "UTC"}, timeout=120)
                h = j["hourly"]
                ts = [int(datetime.fromisoformat(t).replace(tzinfo=timezone.utc).timestamp()) for t in h["time"]]
                daten = {"t": ts, **{str(n): h[f"temperature_2m_previous_day{n}"] for n in (1, 2, 3)}}
                with gzip.open(pfad, "wt", encoding="utf-8") as f:
                    f.write(json.dumps(daten))
                print("prognose", icao, mkurz, name, len(ts), "Gitterhöhe", j.get("elevation"), flush=True)
                time.sleep(PAUSE_OM)


def _lade_prog(icao: str, mkurz: str) -> dict:
    serien = {1: {}, 2: {}, 3: {}}
    for name in BEREICHE:
        d = json.loads(gzip.open(PROG / f"{icao}_{mkurz}_{name}.json.gz", "rt", encoding="utf-8").read())
        for n in (1, 2, 3):
            for t, v in zip(d["t"], d[str(n)]):
                if v is not None:
                    serien[n][t] = v
    return serien


def _lade_obs(icao: str, einheit: str) -> list:
    out = []
    for name in BEREICHE:
        d = json.loads(gzip.open(MESS / f"{icao}_{name}.json.gz", "rt", encoding="utf-8").read())
        out += [(t, f if einheit == "F" else (f - 32.0) * 5.0 / 9.0) for t, f in zip(d["t"], d["f"])]
    out.sort()
    return out


def rechnen() -> None:
    einh = einheiten()
    tage = kalib_tage()
    bias, ausgeschlossen = {}, []
    for icao, (slug, st) in sorted(stationen().items()):
        if slug not in einh:
            ausgeschlossen.append({"station": icao, "stadt": slug, "grund": "kein Markt im Event-Cache (Einheit unbekannt)"})
            continue
        try:
            pe, pg, obs = _lade_prog(icao, "ecmwf"), _lade_prog(icao, "gfs"), _lade_obs(icao, einh[slug])
        except FileNotFoundError:
            ausgeschlossen.append({"station": icao, "stadt": slug, "grund": "Messungen/Prognosen nicht geladen"})
            continue
        zellen = {}
        for v in (1, 2):
            for d in tage:
                ke = rr.komposit_tageswerte(pe, d, st.tz, v, raster_h=RASTER_H["ecmwf"])
                kg = rr.komposit_tageswerte(pg, d, st.tz, v, raster_h=RASTER_H["gfs"])
                if ke is None or kg is None:
                    continue
                for art, pre in (("hoechst", "max"), ("tiefst", "min")):
                    m = rr.tageswert_messung(obs, d, st.tz, art)
                    if m is None:
                        continue
                    f = (ke[pre] + kg[pre]) / 2.0
                    zellen.setdefault((v, art), []).append(m - rr.in_einheit(f, einh[slug]))
        n_min = min((len(zellen.get((v, a), [])) for v in (1, 2) for a in ("hoechst", "tiefst")), default=0)
        if n_min < MIN_TAGE:
            ausgeschlossen.append({"station": icao, "stadt": slug, "grund": f"zu wenige Tage (Minimum {n_min} < {MIN_TAGE})"})
            continue
        for (v, art), res in sorted(zellen.items()):
            bias[f"{icao}|V{v}|{art}"] = {"bias": round(float(np.mean(res)), 4), "sd": round(float(np.std(res)), 4),
                                          "n": len(res), "einheit": einh[slug]}
    ausgeschlossen.append({"station": "HKO", "stadt": "hong-kong", "grund": "Auflösung durch das Hong Kong Observatory, keine METAR-Messreihe"})
    AUS.write_text(json.dumps({
        "quelle": "auswertungen/live_bias.py rechnen (Kalibrierung 2024-03..10, 2025-03..10, korrigierte Koordinaten bot/stationen.py)",
        "stand": "2026-10-14", "min_tage": MIN_TAGE, "ausgeschlossen": ausgeschlossen, "bias": bias},
        indent=1, ensure_ascii=False), encoding="utf-8")
    print(len({k.split("|")[0] for k in bias}), "Stationen mit Bias;", len(ausgeschlossen), "ausgeschlossen")
    for a in ausgeschlossen:
        print("  ausgeschlossen:", a)


if __name__ == "__main__":
    {"laden": laden, "rechnen": rechnen}[sys.argv[1]]()
