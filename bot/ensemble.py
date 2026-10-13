"""Ensemble-Protokoll: neue Modellläufe erkennen, je Station abrufen und die
Tageswerte ALLER Mitglieder je Modell speichern (nicht nur Bucket-Wahrscheinlichkeiten).

Ein Modelllauf gilt als neu, wenn die von Open-Meteo veröffentlichte
`last_run_initialisation_time` (meta.json des Datensatzes) größer ist als die
zuletzt protokollierte (daten/zustand.json).
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from bot.buckets import bucket_wahrscheinlichkeiten, c_nach_f, parse_bucket
from bot.netz import get_json
from bot.stationen import STATIONEN, Station

ENSEMBLE_URL = "https://ensemble-api.open-meteo.com/v1/ensemble"
META_URL = "https://ensemble-api.open-meteo.com/data/{}/static/meta.json"

# Modellname (API) -> Datensätze, deren Laufzeit den Lauf bestimmt, und Merkmal im Spaltennamen.
# ICON: global und EU; der 3-stündliche D2-Datensatz wird bewusst nicht beobachtet (spart Abfragen).
MODELLE = {
    "ecmwf_ifs025": {"meta": ["ecmwf_ifs025_ensemble"], "merkmal": "ecmwf_ifs025"},
    "gfs025": {"meta": ["ncep_gefs025"], "merkmal": "gefs025"},
    "icon_seamless": {"meta": ["dwd_icon_eps", "dwd_icon_eu_eps"], "merkmal": "icon_seamless_eps"},
    "gem_global": {"meta": ["cmc_gem_geps"], "merkmal": "gem_global_ensemble"},
}
FORECAST_TAGE = 3  # lokal heute, morgen, übermorgen (Märkte laufen höchstens 3 Zieltage)

VERFUEGBAR_PUFFER_S = 600  # Open-Meteo empfiehlt Sicherheitsabstand nach Verfügbarkeit eines Laufs

SPALTEN_ENSEMBLE = [
    "abruf_utc", "empfangen_utc", "stadt", "icao", "modell", "modell_lauf_utc", "lauf_details", "lauf_sicher",
    "datum", "art",
    "vorlauf_h", "n_member", "ausgeschlossen", "werte_c",
]


def iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


MAX_META_ALTER_H = 48  # ältere Meta-Angaben gelten als veraltet (ICON-Meta stand am 13.10.2026 auf dem 6.10.)
RASTER_H = 6


def raster_lauf(jetzt: datetime) -> str:
    """Ersatz-Kennung, wenn die Meta-Angabe fehlt oder veraltet ist: 6-Stunden-Raster mit
    Kennzeichen '~' (kein echter Modelllauf, Abruf alle 6 h)."""
    j = jetzt.astimezone(timezone.utc)
    return j.replace(hour=j.hour - j.hour % RASTER_H, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%MZ") + "~"


def hole_modellinfo(hole=get_json, jetzt: datetime | None = None) -> dict[str, dict]:
    """Je Modell {'lauf', 'details', 'reif'}.

    lauf: aktuellster Initialisierungszeitpunkt (ISO, UTC) oder 6-Stunden-Raster mit '~', wenn die
          Meta-Angabe fehlt oder älter als MAX_META_ALTER_H ist.
    details: alle beobachteten Datensätze mit eigener Laufzeit (ICON: global und EU können verschieden sein).
    reif: nur wenn alle Datensätze denselben Lauf zeigen UND dessen Verfügbarkeit mindestens
          VERFUEGBAR_PUFFER_S zurückliegt. Sonst gilt der Lauf nicht als belegt (lauf_sicher = 0)."""
    jetzt = jetzt or datetime.now(timezone.utc)
    out = {}
    for modell, cfg in MODELLE.items():
        inits, avails, teile = [], [], []
        for datensatz in cfg["meta"]:
            try:
                j = hole(META_URL.format(datensatz), timeout=30)
                i = int(j["last_run_initialisation_time"])
                av = int(j.get("last_run_availability_time", 0))
            except (RuntimeError, KeyError, ValueError, TypeError):
                continue
            inits.append(i)
            avails.append(av)
            teile.append(f"{datensatz}@{iso(i)}")
        if inits and jetzt.timestamp() - max(inits) <= MAX_META_ALTER_H * 3600:
            reif = len(set(inits)) == 1 and jetzt.timestamp() - max(avails) >= VERFUEGBAR_PUFFER_S
            out[modell] = {"lauf": iso(max(inits)), "details": ";".join(teile), "reif": reif}
        else:
            out[modell] = {"lauf": raster_lauf(jetzt), "details": "raster", "reif": False}
    return out


def hole_modelllaeufe(hole=get_json, jetzt: datetime | None = None) -> dict[str, str]:
    return {m: v["lauf"] for m, v in hole_modellinfo(hole, jetzt).items()}


def neue_modelle(aktuell: dict[str, str], bekannt: dict[str, str]) -> list[str]:
    return [m for m, t in aktuell.items() if t > bekannt.get(m, "")]


def hole_ensemble(station: Station, modelle: list[str], hole=get_json) -> dict:
    return hole(ENSEMBLE_URL, {
        "latitude": station.lat, "longitude": station.lon, "hourly": "temperature_2m",
        "models": ",".join(modelle), "forecast_days": FORECAST_TAGE, "timezone": station.tz,
    }, timeout=90)


def tageswerte_je_modell(antwort: dict, modelle: list[str]) -> dict[str, dict[str, dict]]:
    """modell -> datum (lokal) -> {'hoechst': [...], 'tiefst': [...], 'ausgeschlossen': n}.

    Bei mehreren angefragten Modellen steht das Modell im Spaltennamen; bei genau einem
    fehlt es (Open-Meteo lässt das Suffix dann weg), alle Mitglieder gehören dann ihm.
    Ein Mitglied zählt für einen Tag nur, wenn JEDE Stunde dieses lokalen Tages vorhanden ist."""
    h = antwort["hourly"]
    tage = defaultdict(list)
    for i, t in enumerate(h["time"]):
        tage[t[:10]].append(i)
    out: dict[str, dict[str, dict]] = {m: {} for m in modelle}
    for key, reihe in h.items():
        if key == "time" or not key.startswith("temperature_2m"):
            continue
        if len(modelle) == 1:
            modell = modelle[0]
        else:
            modell = next((m for m in modelle if MODELLE[m]["merkmal"] in key), None)
            if modell is None:
                continue
        for datum, idx in tage.items():
            d = out[modell].setdefault(datum, {"hoechst": [], "tiefst": [], "ausgeschlossen": 0})
            werte = [reihe[i] for i in idx if reihe[i] is not None]
            if len(werte) < len(idx):
                d["ausgeschlossen"] += 1
                continue
            d["hoechst"].append(max(werte))
            d["tiefst"].append(min(werte))
    return out


def vorlauf_stunden(modell_lauf_iso: str, datum: str, tz: str) -> float:
    """Stunden vom Modelllauf bis zum Beginn des lokalen Zieltages (kann negativ sein,
    wenn der Zieltag schon läuft)."""
    lauf = datetime.strptime(modell_lauf_iso.rstrip("~"), "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)
    start = datetime.fromisoformat(datum).replace(tzinfo=ZoneInfo(tz)).astimezone(timezone.utc)
    return round((start - lauf).total_seconds() / 3600, 1)


def zeilen_fuer_station(stadt: str, station: Station, antwort: dict, modelle: list[str],
                        laeufe: dict[str, str], sicher: dict[str, bool], abruf_iso: str,
                        empfangen_iso: str = "", details: dict[str, str] | None = None) -> list[dict]:
    zeilen = []
    for modell, tage in tageswerte_je_modell(antwort, modelle).items():
        for datum, d in sorted(tage.items()):
            for art in ("hoechst", "tiefst"):
                if not d[art]:
                    continue
                zeilen.append({
                    "abruf_utc": abruf_iso, "empfangen_utc": empfangen_iso or abruf_iso, "stadt": stadt,
                    "icao": station.icao, "modell": modell, "modell_lauf_utc": laeufe[modell],
                    "lauf_details": (details or {}).get(modell, ""), "lauf_sicher": int(sicher.get(modell, True) and not laeufe[modell].endswith("~")),
                    "datum": datum, "art": art,
                    "vorlauf_h": vorlauf_stunden(laeufe[modell], datum, station.tz),
                    "n_member": len(d[art]), "ausgeschlossen": d["ausgeschlossen"],
                    "werte_c": " ".join(f"{w:.1f}" for w in d[art]),
                })
    return zeilen


def juengste_member(zeilen: list[dict]) -> dict[tuple, dict[str, tuple[str, list[float], str]]]:
    """(stadt, art, datum) -> {modell: (modell_lauf, werte, empfangen_utc)}; je Modell der jüngste
    Lauf, bei gleichem Lauf der zuletzt empfangene Abruf."""
    best: dict[tuple, dict[str, tuple[str, list[float], str]]] = defaultdict(dict)
    for z in zeilen:
        k = (z["stadt"], z["art"], z["datum"])
        emp = z.get("empfangen_utc", "")
        alt = best[k].get(z["modell"])
        if alt is None or (z["modell_lauf_utc"], emp) > (alt[0], alt[2]):
            try:
                werte = [float(x) for x in z["werte_c"].split()]
            except ValueError:
                continue
            if werte:
                best[k][z["modell"]] = (z["modell_lauf_utc"], werte, emp)
    return best


def wahrscheinlichkeiten(stamm: list[dict], member: dict) -> list[dict]:
    """Bucket-Wahrscheinlichkeit je Stamm-Zeile (ein Markt = ein Bucket), gepoolt über alle
    Mitglieder der jüngsten Läufe aller Modelle. Gleiches Gewicht je Mitglied."""
    events = defaultdict(list)
    for z in stamm:
        if z["art"] in ("hoechst", "tiefst") and z["stadt"] in STATIONEN:
            events[(z["stadt"], z["art"], z["datum"])].append(z)
    out = []
    for k, zs in events.items():
        modelle = member.get(k)
        if not modelle:
            continue
        werte_c = [w for _, ws, _ in modelle.values() for w in ws]
        verfuegbar_ab = max(emp for _, _, emp in modelle.values())
        einheit, regel = zs[0]["einheit"], zs[0]["rundung"]
        werte = [c_nach_f(w) for w in werte_c] if einheit == "F" else werte_c
        try:
            ps = bucket_wahrscheinlichkeiten(werte, [parse_bucket(z["bucket"]) for z in zs], regel)
        except ValueError:
            continue
        laeufe = ";".join(f"{m}@{lauf}" for m, (lauf, _, _) in sorted(modelle.items()))
        for z, p in zip(zs, ps):
            out.append({"idx": z["idx"], "p_modell": round(p, 4), "n_member": len(werte), "laeufe": laeufe,
                        "verfuegbar_ab_utc": verfuegbar_ab})
    return out


def tage_zurueck(heute: str, n: int) -> list[str]:
    d = datetime.fromisoformat(heute)
    return [(d - timedelta(days=i)).date().isoformat() for i in range(n + 1)]
