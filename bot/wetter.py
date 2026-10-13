"""Holt je Station die Open-Meteo-Ensemble-Vorhersage und rechnet daraus die
Wahrscheinlichkeit je Bucket (inkl. Rundungsregel der Auflösung).

Roh-Ensemble, KEINE Bias-/Streuungskorrektur: Ensembles sind meist zu eng, die
Zahlen sind daher eine Ausgangsbasis, noch kein Handelssignal (siehe docs/machbarkeit.md).

Aufruf:  python -m bot.wetter [--maerkte daten/maerkte.csv] [--ausgabe daten/wahrscheinlichkeiten.csv]
"""
import argparse
import csv
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from bot.buckets import bucket_wahrscheinlichkeiten, c_nach_f, parse_bucket
from bot.netz import get_json
from bot.stationen import STATIONEN

ENSEMBLE_URL = "https://ensemble-api.open-meteo.com/v1/ensemble"
MODELLE = ["ecmwf_ifs025", "gfs025", "icon_seamless", "gem_global"]
PAUSE_S = 2.0  # Schonung der freien API (Grenzen: 600/min, 5000/h, 10000/Tag; Ensemble-Abrufe zählen mehrfach)

AUSGABE_SPALTEN = [
    "markt_id", "stadt", "station", "art", "datum", "bucket", "p_modell", "preis_mitte",
    "bid", "ask", "anzahl_member", "ausgeschlossen", "modelle", "markt_abruf_utc", "ensemble_abruf_utc",
]


def hole_ensemble(station, modelle=MODELLE, tage: int = 4) -> dict:
    return get_json(ENSEMBLE_URL, {
        "latitude": station.lat, "longitude": station.lon, "hourly": "temperature_2m",
        "models": ",".join(modelle), "forecast_days": tage, "timezone": station.tz,
    }, timeout=90)


def tageswerte(antwort: dict) -> dict[str, dict]:
    """datum (lokal) -> {'hoechst': [Tagesmax je Member], 'tiefst': [Tagesmin je Member]} in °C.

    Jeder Eintrag 'temperature_2m*' außer 'time' ist ein Member (Kontrolllauf und
    Störläufe aller angefragten Modelle). Ein Member zählt für einen Tag nur, wenn
    JEDER Stundenwert dieses lokalen Tages vorhanden ist (Extremwerte hängen genau an
    den fehlenden Stunden); sonst wird er ausgelassen und in 'ausgeschlossen' gezählt."""
    h = antwort["hourly"]
    zeiten = h["time"]
    tage = defaultdict(list)
    for i, t in enumerate(zeiten):
        tage[t[:10]].append(i)
    out: dict[str, dict] = {}
    for key, reihe in h.items():
        if key == "time" or not key.startswith("temperature_2m"):
            continue
        for datum, idx in tage.items():
            d = out.setdefault(datum, {"hoechst": [], "tiefst": [], "ausgeschlossen": 0})
            werte = [reihe[i] for i in idx if reihe[i] is not None]
            if len(werte) < len(idx):
                d["ausgeschlossen"] += 1
                continue
            d["hoechst"].append(max(werte))
            d["tiefst"].append(min(werte))
    return out


_MODELL_MERKMALE = {"ecmwf_ifs025": "ecmwf_ifs025", "gfs025": "gefs025",
                    "icon_seamless": "icon_seamless", "gem_global": "gem_global"}


def modellnamen(antwort: dict) -> str:
    keys = [k for k in antwort["hourly"] if k != "time"]
    return "+".join(m for m, merkmal in _MODELL_MERKMALE.items() if any(merkmal in k for k in keys))


def wahrscheinlichkeiten_fuer_event(zeilen: list[dict], member_c: list[float]) -> list[float]:
    """Wahrscheinlichkeit je Bucket-Zeile eines Events. Die Zeilen müssen dieselbe
    Einheit/Rundung haben (ein Event = eine Station)."""
    einheit = zeilen[0]["einheit"]
    regel = zeilen[0]["rundung"]
    werte = [c_nach_f(w) for w in member_c] if einheit == "F" else list(member_c)
    return bucket_wahrscheinlichkeiten(werte, [parse_bucket(z["bucket"]) for z in zeilen], regel)


def neueste_schnappschuesse(maerkte: list[dict]) -> dict[tuple, list[dict]]:
    """Je Event (Stadt, Art, Datum) nur die Zeilen des jüngsten Markt-Abrufs. Ältere
    Schnappschüsse (--anhaengen) dürfen nicht mit der jetzt geholten Vorhersage
    gepaart werden."""
    neuester: dict[tuple, str] = {}
    for z in maerkte:
        if z["art"] in ("hoechst", "tiefst") and z["stadt"] in STATIONEN:
            k = (z["stadt"], z["art"], z["datum"])
            neuester[k] = max(neuester.get(k, ""), z.get("abruf_utc", ""))
    events = defaultdict(list)
    for z in maerkte:
        k = (z["stadt"], z["art"], z["datum"])
        if k in neuester and z.get("abruf_utc", "") == neuester[k]:
            events[k].append(z)
    return events


def berechne(maerkte: list[dict], hole=hole_ensemble, jetzt=None) -> list[dict]:
    events = neueste_schnappschuesse(maerkte)
    cache: dict[str, tuple[dict, str, str]] = {}
    out = []
    for (stadt, art, datum), zeilen in sorted(events.items()):
        if stadt not in cache:
            ant = hole(STATIONEN[stadt])
            stempel = (jetzt or datetime.now(timezone.utc)).isoformat(timespec="seconds")
            cache[stadt] = (tageswerte(ant), modellnamen(ant), stempel)
            time.sleep(PAUSE_S)
        tw, modelle, ens_zeit = cache[stadt]
        member = tw.get(datum, {}).get(art)
        if not member:
            continue  # Datum liegt außerhalb des Vorhersagehorizonts
        ps = wahrscheinlichkeiten_fuer_event(zeilen, member)
        for z, p in zip(zeilen, ps):
            out.append({
                "markt_id": z["markt_id"], "stadt": stadt, "station": z["station"], "art": art,
                "datum": datum, "bucket": z["bucket"], "p_modell": round(p, 4),
                "preis_mitte": z["preis_mitte"], "bid": z["bid"], "ask": z["ask"],
                "anzahl_member": len(member), "ausgeschlossen": tw[datum]["ausgeschlossen"],
                "modelle": modelle, "markt_abruf_utc": z.get("abruf_utc", ""),
                "ensemble_abruf_utc": ens_zeit,
            })
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--maerkte", default="daten/maerkte.csv")
    ap.add_argument("--ausgabe", default="daten/wahrscheinlichkeiten.csv")
    a = ap.parse_args(argv)
    with open(a.maerkte, newline="", encoding="utf-8") as f:
        maerkte = list(csv.DictReader(f))
    ergebnis = berechne(maerkte)
    pfad = Path(a.ausgabe)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=AUSGABE_SPALTEN)
        w.writeheader()
        w.writerows(ergebnis)
    print(f"{len(ergebnis)} Bucket-Wahrscheinlichkeiten -> {a.ausgabe}")


if __name__ == "__main__":
    main()
