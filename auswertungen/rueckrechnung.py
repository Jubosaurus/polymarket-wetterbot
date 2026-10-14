"""Rückrechnung (Phase 1b), Schritt 3: Auswertung aus dem Cache. Nur Auswertung, keine Wetten.

Regeln (festgeschrieben): auswertungen/rueckrechnung_regeln.md. Kein Netzzugriff.

Aufruf:
  python auswertungen/rueckrechnung.py rechnen    # -> auswertungen/rueckrechnung_ergebnis.json, ..._wetten.csv
  python auswertungen/rueckrechnung.py bericht    # -> auswertungen/JJJJ-MM-TT_rueckrechnung.md
"""
import csv
import gzip
import json
import random
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from auswertungen.rr_daten import CACHE, STAEDTE, test_events, zieldatum_abweichungen  # noqa: E402
from bot import rueckrechnung as rr  # noqa: E402
from bot.buckets import parse_bucket  # noqa: E402
from bot.stationen import STATIONEN  # noqa: E402

ERGEBNIS = Path("auswertungen/rueckrechnung_ergebnis.json")
GEGEN = Path("auswertungen/rueckrechnung_gegen.json")
WETTEN = Path("auswertungen/rueckrechnung_wetten.csv")
GRENZE_HAELFTE = "2026-06-30"  # Finden bis einschließlich, Bestätigen danach
MIN_TAGE = 300
VARIANTEN = ("mittel", "ecmwf", "gfs")
SPREADS = (0.02, 0.04, 0.06)
SCHWELLEN = (0.05, 0.10, 0.15)
SEITEN = {"beide": ("ja", "nein"), "ja": ("ja",), "nein": ("nein",)}
HAUPT = {"variante": "mittel", "spread": 0.04, "schwelle": 0.10, "seiten": "beide"}
RASTER_H = {"ecmwf": 3, "gfs": 1}  # natives Zeitraster; ECMWF-Stundenwerte sind Interpolationen (bot/rueckrechnung.stuetzstellen)
KALIB_JAHRE = (2024, 2025)
KALIB_MONATE = range(3, 11)


def haelfte(datum: str) -> str:
    return "finden" if datum <= GRENZE_HAELFTE else "bestaetigen"


def lade_prog(icao: str, mkurz: str) -> dict[int, dict[int, float]]:
    serien = {1: {}, 2: {}, 3: {}}
    for name in ("k2024", "k2025", "test"):
        d = json.loads(gzip.open(CACHE / "prog" / f"{icao}_{mkurz}_{name}.json.gz", "rt", encoding="utf-8").read())
        for n in (1, 2, 3):
            for t, v in zip(d["t"], d[str(n)]):
                if v is not None:
                    serien[n][t] = v
    return serien


def lade_obs(icao: str, einheit: str) -> list[tuple[int, float]]:
    out = []
    for name in ("k2024", "k2025", "test"):
        d = json.loads(gzip.open(CACHE / "messung" / f"{icao}_{name}.json.gz", "rt", encoding="utf-8").read())
        for t, f in zip(d["t"], d["f"]):
            out.append((t, f if einheit == "F" else (f - 32.0) * 5.0 / 9.0))
    out.sort()
    return out


def kalib_tage() -> list[str]:
    out = []
    for j in KALIB_JAHRE:
        d = date(j, 3, 1)
        while d.month in KALIB_MONATE:
            out.append(d.isoformat())
            d += timedelta(days=1)
    return out


def f_aus_komposit(k: dict | None, art: str):
    return None if k is None else (k["max"] if art == "hoechst" else k["min"])


def tagesvorhersagen(prog_e, prog_g, datum, tz, v):
    """Variante -> (F in °C, Komposit-Infos je Modell) für einen Tag; fehlende Modelle fehlen im Ergebnis."""
    return {"ecmwf": rr.komposit_tageswerte(prog_e, datum, tz, v, raster_h=RASTER_H["ecmwf"]),
            "gfs": rr.komposit_tageswerte(prog_g, datum, tz, v, raster_h=RASTER_H["gfs"])}


def f_variante(ks: dict, art: str, variante: str):
    e, g = f_aus_komposit(ks["ecmwf"], art), f_aus_komposit(ks["gfs"], art)
    if variante == "ecmwf":
        return e
    if variante == "gfs":
        return g
    return None if e is None or g is None else (e + g) / 2.0


def lauf_verschiebung(events: list[dict]) -> dict:
    """Wirkung der Stützstellen-Regel (ECMWF, 3-h-Raster) gegenüber der alten Regel (nur die Stunde selbst):
    Anteil der Stunden, die auf einen älteren Lauf (größeres N) ausweichen, und Tage, die dadurch ausfallen."""
    tage = sorted({(e["ziel"], STATIONEN[e["stadt"]].tz) for e in events})
    out = {}
    for v in (1, 2):
        stunden = aelter = tage_aelter = ausfall_alt = ausfall_neu = 0
        for datum, tz in tage:
            td = rr.entscheidungszeit(datum, tz, v)
            hat_aelter = fehlt_alt = fehlt_neu = False
            for t in rr.tag_stunden(datum, tz):
                alt = rr.bekannter_lauf(t, td, v)
                neu = rr.bekannter_lauf(t, td, v, raster_h=RASTER_H["ecmwf"])
                stunden += 1
                fehlt_alt |= alt is None
                fehlt_neu |= neu is None
                if alt is not None and neu is not None and neu[0] > alt[0]:
                    aelter += 1
                    hat_aelter = True
            tage_aelter += hat_aelter
            ausfall_alt += fehlt_alt
            ausfall_neu += fehlt_neu
        out[f"V{v}"] = {"tage": len(tage), "stunden": stunden, "stunden_aelter": aelter, "tage_mit_aelterem_lauf": tage_aelter,
                        "ausfall_alt": ausfall_alt, "ausfall_neu": ausfall_neu}
    return out


def rechnen() -> None:
    ev = test_events()
    einheit_von = {}
    for e in ev:
        if e["stadt"] not in einheit_von:
            einheit_von[e["stadt"]] = parse_bucket(e["maerkte"][0]["titel"]).einheit
    icaos = sorted({(e["text_station"], e["stadt"]) for e in ev if e["text_station"]})
    prog = {}
    obs = {}
    for icao, stadt in icaos:
        prog[icao] = {m: lade_prog(icao, m) for m in ("ecmwf", "gfs")}
        obs[icao] = lade_obs(icao, einheit_von[stadt])

    # ---- Fehlerverteilung nur aus dem Vorzeitraum
    zellen = defaultdict(list)  # (icao, V, art, variante) -> Residuen
    tage = kalib_tage()
    for icao, stadt in icaos:
        tz, einh = STATIONEN[stadt].tz, einheit_von[stadt]
        for v in (1, 2):
            for d in tage:
                ks = tagesvorhersagen(prog[icao]["ecmwf"], prog[icao]["gfs"], d, tz, v)
                for art in ("hoechst", "tiefst"):
                    m = rr.tageswert_messung(obs[icao], d, tz, art)
                    if m is None:
                        continue
                    for var in VARIANTEN:
                        f = f_variante(ks, art, var)
                        if f is not None:
                            zellen[(icao, v, art, var)].append(m - rr.in_einheit(f, einh))
    gepoolt = defaultdict(list)
    for (icao, v, art, var), res in zellen.items():
        stadt = next(s for i, s in icaos if i == icao)
        gepoolt[(einheit_von[stadt], v, art, var)] += res

    def residuen_fuer(icao, stadt, v, art, var):
        res = zellen.get((icao, v, art, var), [])
        if len(res) >= MIN_TAGE:
            return np.array(res), False, len(res)
        return np.array(gepoolt[(einheit_von[stadt], v, art, var)]), True, len(res)

    # ---- Test
    preise = {}
    for zeile in (CACHE / "preise.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            z = json.loads(zeile)
            preise[z["slug"]] = z
        except ValueError:
            continue
    zaehler = defaultdict(int)
    records = []
    for e in ev:
        zaehler["events_gesamt"] += 1
        if not e["text_station"]:
            zaehler["ohne_station"] += 1
            continue
        if e["slug"] not in preise:
            zaehler["ohne_preisabruf"] += 1
            continue
        stadt, icao, datum = e["stadt"], e["text_station"], e["ziel"]
        tz, einh = STATIONEN[stadt].tz, einheit_von[stadt]
        art = "hoechst" if e["art"] == "highest" else "tiefst"
        try:
            buckets = [parse_bucket(m["titel"]) for m in e["maerkte"]]
            ys = [1 if float(json.loads(m["preise"])[0]) >= 0.99 else 0 for m in e["maerkte"]]
        except (ValueError, TypeError, KeyError):
            zaehler["bucket_unlesbar"] += 1
            continue
        if sum(ys) != 1:
            zaehler["ohne_gewinner"] += 1
            continue
        for v in (1, 2):
            ks = tagesvorhersagen(prog[icao]["ecmwf"], prog[icao]["gfs"], datum, tz, v)
            rec = {"slug": e["slug"], "stadt": stadt, "icao": icao, "einheit": einh, "art": art, "datum": datum,
                   "v": v, "haelfte": haelfte(datum), "td": rr.entscheidungszeit(datum, tz, v), "varianten": {},
                   "buckets": []}
            for i, m in enumerate(e["maerkte"]):
                pz = preise[e["slug"]]["tok"].get(m["token"], {}).get(str(v))
                rec["buckets"].append({"titel": m["titel"], "y": ys[i],
                                       "preis": pz[1] if pz else None, "preis_t": pz[0] if pz else None})
            for var in VARIANTEN:
                f_c = f_variante(ks, art, var)
                if f_c is None:
                    continue
                res, pooled, n_eig = residuen_fuer(icao, stadt, v, art, var)
                f_u = rr.in_einheit(f_c, einh)
                rec["varianten"][var] = {"f": f_u, "p": rr.bucket_p(f_u, res, buckets), "gepoolt": pooled, "n_res": len(res), "n_eig": n_eig}
            preise_v = [b["preis"] for b in rec["buckets"]]
            rec["preissumme"] = sum(preise_v) if all(x is not None for x in preise_v) else None
            # Look-ahead-relevante Angaben (Modell-Läufe, Verfügbarkeit)
            rec["lauf"] = {}
            for mk in ("ecmwf", "gfs"):
                k = ks[mk]
                if k is not None:
                    pre = "max" if art == "hoechst" else "min"
                    rec["lauf"][mk] = {"extrem_t": k[f"{pre}_t"], "n": k[f"{pre}_n"], "init": k[f"{pre}_init"],
                                       "verfuegbar_max": k["verfuegbar_max"]}
            if "mittel" not in rec["varianten"]:
                zaehler[f"ohne_prognose_v{v}"] += 1
                continue
            if all(b["preis"] is None for b in rec["buckets"]):
                zaehler[f"ohne_preis_v{v}"] += 1
                continue
            zaehler[f"auswertbar_v{v}"] += 1
            records.append(rec)
    zaehler["zellen_gepoolt"] = sum(1 for (icao, v, art, var), r in zellen.items() if len(r) < MIN_TAGE)
    zaehler["zellen_gesamt"] = len(zellen)
    zaehler["kalib_tage_min"] = min(len(r) for r in zellen.values())
    zaehler["kalib_tage_median"] = int(np.median([len(r) for r in zellen.values()]))

    ergebnis = auswerten(records)
    ergebnis["zaehler"] = dict(zaehler)
    ergebnis["interpolation"] = lauf_verschiebung(ev)
    ergebnis["zieldatum"] = {k: v for k, v in zieldatum_abweichungen().items()}
    ergebnis["stadt_zellen"] = {f"{k[0]}|V{k[1]}|{k[2]}|{k[3]}": len(r) for k, r in sorted(zellen.items()) if k[3] == "mittel"}
    ERGEBNIS.write_text(json.dumps(ergebnis, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(ergebnis["zaehler"], indent=1))


SUMMEN_KLASSEN = (("plausibel (0,95–1,10)", lambda x: x is not None and 0.95 <= x <= 1.10),
                  ("darüber (> 1,10)", lambda x: x is not None and x > 1.10),
                  ("darunter (< 0,95)", lambda x: x is not None and x < 0.95),
                  ("unbekannt (nicht alle Buckets bepreist)", lambda x: x is None))
PREIS_KLASSEN = (("Ja-Preis < 0,05", lambda p: p < 0.05), ("0,05 – 0,20", lambda p: 0.05 <= p <= 0.20),
                 ("> 0,20", lambda p: p > 0.20))
ALTER_KLASSEN = (("< 1 h", lambda m: m < 60), ("1 – 6 h", lambda m: 60 <= m <= 360), ("> 6 h", lambda m: m > 360))


def artefakt_auswertung(haupt_wetten: list[dict]) -> dict:
    """Zusatz (nachträglich, nach Sicht der Daten): Nein-Wetten Vorlauf 2, Bestätigungshälfte, nach Preissumme des Events,
    Preis des Buckets und Alter des Preispunkts. Nur vorhandene Daten, keine neuen Abrufe."""
    basis = [x for x in haupt_wetten if x["seite"] == "nein" and x["v"] == 2 and x["haelfte"] == "bestaetigen"]
    out = {"basis": stat([x["gewinn"] for x in basis]), "nach_summe": {}, "nach_preis": {}, "kreuz": {}, "alter": {}, "alter_alle": {}}
    for sn, sf in SUMMEN_KLASSEN:
        teil = [x for x in basis if sf(x["preissumme"])]
        out["nach_summe"][sn] = stat([x["gewinn"] for x in teil])
        for pn, pf in PREIS_KLASSEN:
            out["kreuz"][f"{sn}|{pn}"] = stat([x["gewinn"] for x in teil if pf(x["preis_ja"])])
    for pn, pf in PREIS_KLASSEN:
        out["nach_preis"][pn] = stat([x["gewinn"] for x in basis if pf(x["preis_ja"])])
    for an, af in ALTER_KLASSEN:
        out["alter"][an] = stat([x["gewinn"] for x in basis if x["alter_min"] is not None and af(x["alter_min"])])
        out["alter_alle"][an] = stat([x["gewinn"] for x in haupt_wetten if x["alter_min"] is not None and af(x["alter_min"])])
    am = sorted(x["alter_min"] for x in haupt_wetten if x["alter_min"] is not None)
    out["alter_perzentile"] = {q: am[int(q / 100 * (len(am) - 1))] for q in (0, 50, 90, 99, 100)} if am else {}
    return out


def stat(profite: list[float]) -> dict:
    n = len(profite)
    if n == 0:
        return {"n": 0, "wins": 0, "rate": None, "summe": 0.0, "je_wette": None, "ohne_top3": 0.0}
    wins = sum(1 for p in profite if p > 0)
    s = sum(profite)
    return {"n": n, "wins": wins, "rate": wins / n, "summe": s, "je_wette": s / n,
            "ohne_top3": s - sum(sorted(profite, reverse=True)[:3])}


def wetten_fuer(records, variante, spread, schwelle, seiten) -> list[dict]:
    out = []
    for rec in records:
        var = rec["varianten"].get(variante)
        if var is None:
            continue
        cand = []
        for i, b in enumerate(rec["buckets"]):
            if b["preis"] is None:
                continue
            for k in rr.kandidaten(var["p"][i], b["preis"], spread):
                k["bucket_idx"] = i
                cand.append(k)
        for k in rr.waehle_wetten(cand, schwelle, SEITEN[seiten]):
            b = rec["buckets"][k["bucket_idx"]]
            gewinnt = b["y"] == 1 if k["seite"] == "ja" else b["y"] == 0
            out.append({"slug": rec["slug"], "stadt": rec["stadt"], "einheit": rec["einheit"], "art": rec["art"],
                        "datum": rec["datum"], "v": rec["v"], "haelfte": rec["haelfte"], "seite": k["seite"],
                        "bucket": b["titel"], "p_modell": var["p"][k["bucket_idx"]], "preis_ja": b["preis"],
                        "preis_t": b["preis_t"], "td": rec["td"], "kosten": k["kosten"], "kante": k["kante"],
                        "gewinnt": int(gewinnt), "gewinn": rr.wett_ergebnis(k["kosten"], gewinnt),
                        "preissumme": rec["preissumme"],
                        "alter_min": None if b["preis_t"] is None else (rec["td"] - b["preis_t"]) / 60.0,
                        "lauf": rec["lauf"]})
    return out


def auswerten(records: list[dict]) -> dict:
    erg = {"haupt": HAUPT, "wetten": {}, "brier": {}, "kalib": {}, "verstoesse": {}}
    # --- Wetten: Raster
    raster = [("mittel", s, th, se) for s in SPREADS for th in SCHWELLEN for se in SEITEN]
    raster += [(var, 0.04, 0.10, "beide") for var in ("ecmwf", "gfs")]
    haupt_wetten = []
    for var, s, th, se in raster:
        w = wetten_fuer(records, var, s, th, se)
        if (var, s, th, se) == (HAUPT["variante"], HAUPT["spread"], HAUPT["schwelle"], HAUPT["seiten"]):
            haupt_wetten = w
        for v in (1, 2):
            for h in ("finden", "bestaetigen", "alle"):
                sel = [x["gewinn"] for x in w if x["v"] == v and (h == "alle" or x["haelfte"] == h)]
                erg["wetten"][f"{var}|S{s}|T{th}|{se}|V{v}|{h}"] = stat(sel)
    # Ja/Nein-Aufteilung der Hauptwetten, Einheit, Art
    for v in (1, 2):
        for h in ("finden", "bestaetigen"):
            for seite in ("ja", "nein"):
                erg["wetten"][f"haupt|V{v}|{h}|{seite}"] = stat([x["gewinn"] for x in haupt_wetten if x["v"] == v and x["haelfte"] == h and x["seite"] == seite])
            for einh in ("F", "C"):
                erg["wetten"][f"haupt|V{v}|{h}|{einh}"] = stat([x["gewinn"] for x in haupt_wetten if x["v"] == v and x["haelfte"] == h and x["einheit"] == einh])
    # --- Brier über alle Buckets mit Preis
    gruppen = defaultdict(lambda: {"pm": [], "pk": [], "y": []})
    for rec in records:
        var = rec["varianten"]["mittel"]
        for i, b in enumerate(rec["buckets"]):
            if b["preis"] is None:
                continue
            for key in (("alle", "alle", "alle"), (rec["haelfte"], "alle", "alle"), (rec["haelfte"], f"V{rec['v']}", "alle"),
                        (rec["haelfte"], f"V{rec['v']}", rec["einheit"]), ("alle", f"V{rec['v']}", "alle")):
                g = gruppen[key]
                g["pm"].append(var["p"][i]); g["pk"].append(b["preis"]); g["y"].append(b["y"])
    for key, g in gruppen.items():
        erg["brier"]["|".join(key)] = {"n": len(g["y"]), "modell": rr.brier(g["pm"], g["y"]), "markt": rr.brier(g["pk"], g["y"])}
    # --- Kalibrierung (alle Buckets, Hauptvorhersage)
    for name, filt in (("alle", lambda r: True), ("bestaetigen", lambda r: r["haelfte"] == "bestaetigen")):
        pm, pk, y = [], [], []
        for rec in records:
            if not filt(rec):
                continue
            for i, b in enumerate(rec["buckets"]):
                if b["preis"] is not None:
                    pm.append(rec["varianten"]["mittel"]["p"][i]); pk.append(b["preis"]); y.append(b["y"])
        erg["kalib"][name] = {"modell": rr.kalibrierung(pm, y), "markt": rr.kalibrierung(pk, y)}
    # --- ZUSATZ (nachträglich, nicht Teil der festgeschriebenen Regeln): Preisqualität
    erg["zusatz"] = {"wetten": {}, "brier": {}, "qualitaet": {}}
    for art in ("hoechst", "tiefst"):
        for monat in sorted({r["datum"][:7] for r in records}):
            sel = [r["preissumme"] for r in records if r["v"] == 1 and r["art"] == art and r["datum"][:7] == monat
                   and r.get("preissumme") is not None]
            if sel:
                erg["zusatz"]["qualitaet"][f"{art}|{monat}"] = {
                    "n": len(sel), "mittel": sum(sel) / len(sel), "anteil_ueber_1_3": sum(1 for x in sel if x > 1.3) / len(sel)}
    plausibel = [r for r in records if r.get("preissumme") is not None and 0.90 <= r["preissumme"] <= 1.15]
    erg["zusatz"]["anteil_plausibel"] = {f"V{v}": len([r for r in plausibel if r["v"] == v]) / max(1, len([r for r in records if r["v"] == v]))
                                         for v in (1, 2)}
    for name, teil in (("plausibel", plausibel),
                       ("plausibel_hoechst", [r for r in plausibel if r["art"] == "hoechst"]),
                       ("plausibel_tiefst", [r for r in plausibel if r["art"] == "tiefst"])):
        w = wetten_fuer(teil, "mittel", 0.04, 0.10, "beide")
        for v in (1, 2):
            for h in ("finden", "bestaetigen"):
                erg["zusatz"]["wetten"][f"{name}|V{v}|{h}"] = stat([x["gewinn"] for x in w if x["v"] == v and x["haelfte"] == h])
                pm, pk, y = [], [], []
                for rec in teil:
                    if rec["v"] != v or rec["haelfte"] != h:
                        continue
                    for i, b in enumerate(rec["buckets"]):
                        if b["preis"] is not None:
                            pm.append(rec["varianten"]["mittel"]["p"][i]); pk.append(b["preis"]); y.append(b["y"])
                erg["zusatz"]["brier"][f"{name}|V{v}|{h}"] = {"n": len(y), "modell": rr.brier(pm, y) if y else None,
                                                             "markt": rr.brier(pk, y) if y else None}
    # --- Look-ahead: alle Wetten prüfen, 20 zeigen
    verstoss = {"lauf_nach_entscheidung": 0, "preis_nach_entscheidung": 0}
    for x in haupt_wetten:
        if x["preis_t"] is None or x["preis_t"] > x["td"]:
            verstoss["preis_nach_entscheidung"] += 1
        for mk, info in x["lauf"].items():
            if info["verfuegbar_max"] > x["td"]:
                verstoss["lauf_nach_entscheidung"] += 1
    erg["artefakt"] = artefakt_auswertung(haupt_wetten)
    erg["verstoesse"] = verstoss
    erg["haupt_wetten_n"] = len(haupt_wetten)
    stichprobe = sorted(haupt_wetten, key=lambda x: (x["slug"], x["v"], x["bucket"], x["seite"]))
    stichprobe = random.Random(42).sample(stichprobe, min(20, len(stichprobe)))
    erg["stichprobe"] = stichprobe
    with open(WETTEN, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[k for k in haupt_wetten[0] if k != "lauf"] if haupt_wetten else ["leer"], extrasaction="ignore")
        w.writeheader()
        w.writerows(haupt_wetten)
    return erg


def iso(t: int) -> str:
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%MZ")


def pct(x) -> str:
    return "–" if x is None else f"{x * 100:.1f} %"


def usd(x) -> str:
    return "–" if x is None else f"{x:+.2f}"


def w_zeile(name: str, w: dict) -> str:
    return (f"| {name} | {w['n']} | {w['wins']} | {pct(w['rate'])} | {usd(w['je_wette'])} | {usd(w['summe'])} | "
            f"{usd(w['ohne_top3'])} |")


VORHER = CACHE / "vorher" / "rueckrechnung_ergebnis.json"
VORHER_STATION = CACHE / "vorher2" / "rueckrechnung_ergebnis.json"  # vor der Koordinatenkorrektur von Dallas


def _events() -> list[dict]:
    from auswertungen.rr_events import lade
    return lade()


def klarstellungen_abschnitt(erg: dict, gegen: dict | None, hw) -> str:
    """Zieldatum, Stützstellen-Regel, Unabhängigkeit der Gegenrechnung, Vorher/Nachher (Klarstellungen 2026-10-14)."""
    zd, ip = erg["zieldatum"], erg["interpolation"]
    ab = zd["abweichend"]
    n15 = sum(1 for x in ab if x["in_15_staedten"])
    L = ["## Neuberechnung nach Codex-Review (2026-10-14)\n",
         "Der Review fand zwei Fehler im ersten Lauf: (1) `endDate` statt Zieltag, (2) Interpolation ohne Stützstellen-Prüfung. "
         "Beide sind behoben, Kalibrierung, Hauptrechnung, Gegenrechnung und Bericht wurden komplett neu erzeugt. Die Regeln aus "
         "Commit `0d071ab` blieben unverändert; die Umsetzung steht in `auswertungen/rueckrechnung_klarstellungen.md`.\n",
         "### Zieldatum\n",
         f"Der Zieltag kommt jetzt aus dem Slug (`...-on-april-15-2026`), nicht aus `endDate`. Von {zd['events']} Events im Cache "
         f"(alle Städte) weichen **{len(ab)}** ab (Zieltag ≠ Datum von `endDate`); davon liegen **{n15}** in den 15 Städten und "
         f"**{sum(1 for x in ab if x['im_testzeitraum'])}** im Testzeitraum. Unlesbare Slugs: {len(zd['unlesbar'])}; "
         f"Slugs ohne Jahr (frühe Events, Jahr aus `endDate`): {zd['slug_ohne_jahr']}, alle vor dem Testzeitraum. "
         f"Die Preisfenster der {n15} betroffenen Events der 15 Städte wurden neu geladen. Alle Abweichungen:\n",
         "| Event | Stadt | Zieltag (Slug) | `endDate` | Differenz (Tage) | in den 15 Städten |\n|---|---|---|---|---|---|"]
    for x in sorted(ab, key=lambda x: (x["ziel"], x["slug"])):
        L.append(f"| {x['slug']} | {x['stadt']} | {x['ziel']} | {x['ende']} | {x['tage']:+d} | {'**ja**' if x['in_15_staedten'] else 'nein'} |")
    L += ["", "### Interpolation (Stützstellen)\n",
          "Gemessen am Cache: Die ECMWF-Stundenwerte zwischen den 3-h-Stützstellen sind Catmull-Rom-Interpolationen über vier "
          "Stützstellen (a−3 h, a, a+3 h, a+6 h): 14 696 von 14 696 geprüften Stunden stimmen mit höchstens 0,08 °C Abweichung "
          "überein (vier Stationen, Vorlauf 1 und 2). GFS ist stündlich nativ (keine Interpolation). Ein Stundenwert gilt jetzt nur "
          "als bekannt, wenn **alle** seine Stützstellen aus zum Entscheidungszeitpunkt verfügbaren Läufen stammen "
          "(Lauf + 10 h ≤ Td); sonst wird der nächstältere Lauf (N+1, 24 h älter) verwendet, bei N > 3 fällt der Tag aus. "
          "Wirkung auf ECMWF (alle Zieltage des Testzeitraums):\n",
          "| Vorlauf | Stunden | Stunden mit älterem Lauf | Tage mit mindestens einer solchen Stunde | Tage ohne Prognose (alte Regel) | Tage ohne Prognose (neu) |\n|---|---|---|---|---|---|"]
    for v in ("V1", "V2"):
        i = ip[v]
        L.append(f"| {v[1]} | {i['stunden']} | {i['stunden_aelter']} ({pct(i['stunden_aelter'] / i['stunden'])}) | "
                 f"{i['tage_mit_aelterem_lauf']} von {i['tage']} | {i['ausfall_alt']} | {i['ausfall_neu']} |")
    if gegen is not None:
        endes = {e["slug"]: e["ende"] for e in _events()}
        verschieden = sorted(sl for sl, z in gegen["ziele"].items() if z != rr.zieldatum_aus_slug(sl, endes.get(sl)))
        hinw = gegen.get("ziel_hinweise", {})
        L += ["", "### Unabhängigkeit der Gegenrechnung\n",
              "Die Gegenrechnung bestimmt jetzt **ihr eigenes Zieldatum aus dem Fragetext** (Event-Titel „… on April 15?“; Jahr aus der "
              "Beschreibung „… on 15 Apr '26“, sonst nächstliegend zu `endDate`) und leitet die **Stützstellen selbst** aus den "
              "Catmull-Rom-Gewichten ab (Stützstellen mit Gewicht ≠ 0, ohne die Indexarithmetik der Hauptrechnung). "
              f"Datumsableitung der Gegenrechnung (Events der 15 Städte): {', '.join(f'{k} {v}' for k, v in sorted(hinw.items()))}. "
              f"Events, bei denen ihr Zieldatum vom Slug-Datum der Hauptrechnung abweicht: **{len(verschieden)}**"
              + (f" ({', '.join(verschieden[:10])})" if verschieden else "") + ". "
              "Gemeinsam bleiben die Rohdaten (Cache), die Regeln selbst (Td, 10 h, N ≤ 3) und die Annahme, dass eine Stützstelle `s` im "
              "Vorlauf-N-Wert aus dem Lauf `floor6(s − 24·N h)` stammt; diese Annahme steht in den Regeln und wurde mit der Single-Runs-API "
              "nachgemessen, hier nicht neu geprüft.\n"]
    if VORHER.exists():
        alt = json.loads(VORHER.read_text(encoding="utf-8"))
        L += ["", "### Vorher / nachher (Hauptregel: Mittel ECMWF+GFS, Spread 0,04, Kante ≥ 0,10, Ja und Nein)\n",
              "„vorher“ = erster Lauf (Zieltag aus `endDate`, Stundenwert ohne Stützstellen-Prüfung); „nachher“ = dieser Bericht. "
              "Brier: kleiner ist besser.\n",
              "| Vorlauf | Hälfte | Stand | Brier Modell | Brier Markt | Wetten | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |\n|---|---|---|---|---|---|---|---|---|"]
        for v in (1, 2):
            for h, hn in (("finden", "Finden"), ("bestaetigen", "Bestätigen")):
                for nm, d in (("vorher", alt), ("nachher", erg)):
                    w = d["wetten"][f"mittel|S0.04|T0.1|beide|V{v}|{h}"]
                    b = d["brier"][f"{h}|V{v}|alle"]
                    L.append(f"| {v} | {hn} | {nm} | {b['modell']:.4f} | {b['markt']:.4f} | {w['n']} | {usd(w['je_wette'])} | {usd(w['summe'])} | {usd(w['ohne_top3'])} |")
        for nm, d in (("vorher", alt), ("nachher", erg)):
            b = d["brier"]["alle|alle|alle"]
            L.append(f"| beide | alle | {nm} | {b['modell']:.4f} | {b['markt']:.4f} | {d['haupt_wetten_n']} (Hauptwetten) | | | |")
    if VORHER_STATION.exists():
        alt = json.loads(VORHER_STATION.read_text(encoding="utf-8"))
        L += ["", "### Stationsprüfung (2026-10-14): betroffene Städte der Rückrechnung\n",
              "Die Rückrechnung holt die Koordinaten aus dem IEM-Verzeichnis (`daten/cache/koordinaten.json`), nicht aus `bot/stationen.py`. "
              "Gegen `aviationweather.gov` geprüft liegen 15 der 16 Stationen höchstens 0,43 km daneben (unverändert); **Dallas (KDAL) liegt 1,8 km daneben** "
              "(Rasterhöhe 144 statt 146 m). Nur Dallas wurde neu abgerufen (Prognosen 2024, 2025, Test) und alles neu gerechnet "
              "(Regeln unverändert). Chongqing, Wuhan, Chengdu, Karachi, Qingdao, Shanghai und Hong Kong gehören nicht zu den 15. "
              "„vorher“ = Lauf mit den alten Dallas-Koordinaten (Stand nach dem ersten Review), „nachher“ = dieser Bericht.\n",
              "| Vorlauf | Hälfte | Stand | Brier Modell | Brier Markt | Wetten | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |\n|---|---|---|---|---|---|---|---|---|"]
        for v in (1, 2):
            for h, hn in (("finden", "Finden"), ("bestaetigen", "Bestätigen")):
                for nm, d in (("vorher", alt), ("nachher", erg)):
                    w = d["wetten"][f"mittel|S0.04|T0.1|beide|V{v}|{h}"]
                    b = d["brier"][f"{h}|V{v}|alle"]
                    L.append(f"| {v} | {hn} | {nm} | {b['modell']:.4f} | {b['markt']:.4f} | {w['n']} | {usd(w['je_wette'])} | {usd(w['summe'])} | {usd(w['ohne_top3'])} |")
        for nm, d in (("vorher", alt), ("nachher", erg)):
            b = d["brier"]["alle|alle|alle"]
            L.append(f"| beide | alle | {nm} | {b['modell']:.4f} | {b['markt']:.4f} | {d['haupt_wetten_n']} (Hauptwetten) | | | |")
    return "\n".join(L) + "\n"


KOPF_W = "| | Wetten | Treffer | Quote | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |\n|---|---|---|---|---|---|---|"


def artefakt_abschnitt(a: dict) -> str:
    L = ["\n## Zusatzauswertung: Ist der Gewinn der Nein-Wetten (Vorlauf 2) ein Artefakt? (NACHTRÄGLICH, nicht Teil der festgeschriebenen Regeln, ändert das Urteil nicht)\n",
         "Grundgesamtheit: Hauptwetten, Seite Nein, Vorlauf 2, Bestätigungshälfte. Nur vorhandene Daten, keine neuen Abrufe. "
         "„Preis des Buckets“ = Ja-Preis des Buckets zum Entscheidungszeitpunkt.\n",
         KOPF_W, w_zeile("alle Nein-Wetten V2, Bestätigen", a["basis"]),
         "\n**Nach Preissumme des Events** (Summe der Ja-Preise aller Buckets, zum Entscheidungszeitpunkt bekannt)\n", KOPF_W]
    for k, w in a["nach_summe"].items():
        L.append(w_zeile(k, w))
    L += ["\n**Nach Preis des Buckets**\n", KOPF_W]
    for k, w in a["nach_preis"].items():
        L.append(w_zeile(k, w))
    L += ["\n**Kreuztabelle Preissumme × Preis des Buckets**\n", KOPF_W]
    for k, w in a["kreuz"].items():
        L.append(w_zeile(k.replace("|", " / "), w))
    pz = a["alter_perzentile"]
    L += ["\n**Alter des Preispunkts zur Entscheidung** (Näherung, siehe Hinweis)\n",
          "Gemessen wird hier die Zeit zwischen dem letzten Preispunkt im 10-Minuten-Raster und dem Entscheidungszeitpunkt, **nicht** die Zeit "
          "seit der letzten Preisänderung oder dem letzten Handel: Die Preishistorie schreibt fehlende Minuten fort, und im Cache liegt je Token "
          "nur dieser letzte Rasterpunkt. Das echte Alter eines Preises ist damit **nicht bestimmbar**; dafür wäre ein neuer Abruf der Rohreihen nötig. "
          f"Verteilung über alle Hauptwetten (Minuten): Minimum {pz.get(0, 0):.1f}, Median {pz.get(50, 0):.1f}, 90 % {pz.get(90, 0):.1f}, "
          f"99 % {pz.get(99, 0):.1f}, Maximum {pz.get(100, 0):.1f}.\n",
          KOPF_W]
    for k, w in a["alter"].items():
        L.append(w_zeile(f"Nein V2 Bestätigen, Rasterpunkt {k} alt", w))
    for k, w in a["alter_alle"].items():
        L.append(w_zeile(f"alle Hauptwetten, Rasterpunkt {k} alt", w))
    L.append("")
    L.append(Path("auswertungen/rueckrechnung_artefakttext.md").read_text(encoding="utf-8") if Path("auswertungen/rueckrechnung_artefakttext.md").exists() else "")
    return "\n".join(L) + "\n"


def bericht() -> None:
    erg = json.loads(ERGEBNIS.read_text(encoding="utf-8"))
    gegen = json.loads(GEGEN.read_text(encoding="utf-8")) if GEGEN.exists() else None
    W, B, Z = erg["wetten"], erg["brier"], erg["zaehler"]

    def hw(v, h, s="0.04", th="0.1", se="beide", var="mittel"):
        return W[f"{var}|S{s}|T{th}|{se}|V{v}|{h}"]

    bestehen, zeilen = {}, []
    for v in (1, 2):
        w, br = hw(v, "bestaetigen"), B[f"bestaetigen|V{v}|alle"]
        ok = w["n"] >= 100 and w["summe"] > 0 and w["ohne_top3"] > 0 and br["modell"] < br["markt"]
        bestehen[v] = ok
        zeilen.append(f"| Vorlauf {v} | {w['n']} | {pct(w['rate'])} | {usd(w['je_wette'])} | {usd(w['summe'])} | "
                      f"{usd(w['ohne_top3'])} | {br['modell']:.4f} / {br['markt']:.4f} | {'ja' if ok else 'nein'} |")
    n_best = hw(1, "bestaetigen")["n"] + hw(2, "bestaetigen")["n"]
    urteil = "ZU WENIG DATEN" if n_best < 100 else ("WEITER MIT PAPIERHANDEL" if all(bestehen.values()) else "VERWERFEN")
    datum = date.today().isoformat()
    L = [f"# Rückrechnung Phase 1b ({datum})\n",
         "Nur Auswertung, keine Wetten. Regeln festgeschrieben in `auswertungen/rueckrechnung_regeln.md` (eingespielt vor dem "
         "Laden der Daten). Hauptfall: Mittel aus ECMWF und GFS, Spread 0,04, Kante ≥ 0,10, Ja und Nein, höchstens 2 Wetten je "
         "Event, 10 $ Einsatz inklusive Gebühr. 15 Städte, Zieldaten 2026-03-01 bis 2026-10-11. Zeitangaben in UTC.\n",
         f"## Urteil: **{urteil}**\n",
         "| Hauptregel, Bestätigungshälfte (Juli–Okt) | Wetten | Trefferquote | Gewinn je Wette ($) | Summe ($) | "
         "Summe ohne 3 beste ($) | Brier Modell / Markt (alle Buckets) | Kriterien erfüllt |\n|---|---|---|---|---|---|---|---|"]
    L += zeilen
    L.append("\nKriterien (vorab festgelegt): ≥ 100 Wetten, Summe > 0, Summe ohne die 3 besten > 0 und Brier(Modell) < "
             "Brier(Markt), und das für **beide** Vorläufe. „Zu wenig Daten“, wenn die Bestätigungshälfte insgesamt "
             "< 100 Wetten hat. Brier: kleiner ist besser.\n")
    text = Path("auswertungen/rueckrechnung_urteilstext.md")
    L.append(text.read_text(encoding="utf-8") if text.exists() else "")

    L.append(klarstellungen_abschnitt(erg, gegen, hw))

    # ---- Datenbasis
    L.append("## Datenbasis\n")
    L.append(f"- Events im Testzeitraum (15 Städte): {Z['events_gesamt']}. Auswertbar (Prognose und mindestens ein Preis am "
             f"Entscheidungszeitpunkt): Vorlauf 1: {Z.get('auswertbar_v1', 0)}, Vorlauf 2: {Z.get('auswertbar_v2', 0)}.")
    L.append("- Ausgelassen: " + ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in sorted(Z.items())
                                           if k.startswith(("ohne_", "bucket_"))) + ".")
    L.append(f"- Fehlerverteilung: {Z['zellen_gesamt']} Zellen (Station × Vorlauf × Art × Variante) aus Mär–Okt 2024 und 2025, "
             f"kleinste Zelle {Z['kalib_tage_min']} Tage, Median {Z['kalib_tage_median']}; **gepoolte Zellen: {Z['zellen_gepoolt']}**.\n")

    # ---- Treffsicherheit aller Buckets
    L.append("## Treffsicherheit aller Buckets (Brier-Score, kleiner = besser)\n")
    L.append("| Gruppe | Buckets | Brier Modell | Brier Markt | Modell − Markt |\n|---|---|---|---|---|")
    for key in ("alle|alle|alle", "finden|V1|alle", "finden|V2|alle", "bestaetigen|V1|alle", "bestaetigen|V2|alle",
                "finden|V1|F", "finden|V1|C", "bestaetigen|V1|F", "bestaetigen|V1|C",
                "finden|V2|F", "finden|V2|C", "bestaetigen|V2|F", "bestaetigen|V2|C"):
        if key in B:
            b = B[key]
            h, v, e = key.split("|")
            name = f"{'Finden' if h == 'finden' else 'Bestätigen' if h == 'bestaetigen' else 'alle'}"
            name += "" if v == "alle" else f", Vorlauf {v[1]}"
            name += "" if e == "alle" else f", {'°F-Städte' if e == 'F' else '°C-Städte'}"
            L.append(f"| {name} | {b['n']} | {b['modell']:.4f} | {b['markt']:.4f} | {b['modell'] - b['markt']:+.4f} |")
    for name, titel in (("bestaetigen", "Bestätigungshälfte"), ("alle", "alle Daten")):
        k = erg["kalib"][name]
        L.append(f"\n**Kalibrierung, {titel}** (Hauptvorhersage und Marktpreis; Spalte „Häufigkeit“ = wie oft der Bucket tatsächlich gewann)\n")
        L.append("| Modell sagt | Buckets | mittl. Modell-p | Häufigkeit | | Markt sagt | Buckets | mittl. Preis | Häufigkeit |\n|---|---|---|---|---|---|---|---|---|")
        for m, k2 in zip(k["modell"], k["markt"]):
            def f(x):
                return "–" if x is None or x != x else f"{x:.3f}"
            L.append(f"| {int(m[0] * 100)}–{int(m[1] * 100)} % | {m[2]} | {f(m[3])} | {f(m[4])} | | {int(k2[0] * 100)}–{int(k2[1] * 100)} % | {k2[2]} | {f(k2[3])} | {f(k2[4])} |")

    # ---- Wetten
    L.append("\n## Wetten (Hauptregel: Kante ≥ 0,10, Spread 0,04, Ja und Nein, höchstens 2 je Event)\n")
    L.append(KOPF_W)
    for v in (1, 2):
        for h, hn in (("finden", "Finden"), ("bestaetigen", "Bestätigen"), ("alle", "alle")):
            L.append(w_zeile(f"Vorlauf {v}, {hn}", hw(v, h)))
    L.append("\n**Ja und Nein getrennt** (Aufteilung der Hauptwetten)\n")
    L.append(KOPF_W)
    for v in (1, 2):
        for h, hn in (("finden", "Finden"), ("bestaetigen", "Bestätigen")):
            for seite in ("ja", "nein"):
                L.append(w_zeile(f"Vorlauf {v}, {hn}, {seite.capitalize()}", W[f"haupt|V{v}|{h}|{seite}"]))
    L.append("\n**Ja-only und Nein-only als eigene Strategien** (jeweils höchstens 2 Wetten je Event)\n")
    L.append(KOPF_W)
    for se, sn in (("ja", "nur Ja"), ("nein", "nur Nein")):
        for v in (1, 2):
            for h, hn in (("finden", "Finden"), ("bestaetigen", "Bestätigen")):
                L.append(w_zeile(f"{sn}, Vorlauf {v}, {hn}", hw(v, h, se=se)))
    L.append("\n**°F- und °C-Städte** (Hauptwetten)\n")
    L.append(KOPF_W)
    for v in (1, 2):
        for h, hn in (("finden", "Finden"), ("bestaetigen", "Bestätigen")):
            for einh in ("F", "C"):
                L.append(w_zeile(f"Vorlauf {v}, {hn}, °{einh}", W[f"haupt|V{v}|{h}|{einh}"]))
    L.append("\n**Schwellen** (nur zusätzlich berichtet; Hauptregel 0,10)\n")
    L.append(KOPF_W)
    for th in ("0.05", "0.1", "0.15"):
        for v in (1, 2):
            for h, hn in (("finden", "Finden"), ("bestaetigen", "Bestätigen")):
                L.append(w_zeile(f"Kante ≥ {th.replace('.', ',') if th != '0.1' else '0,10'}, Vorlauf {v}, {hn}", hw(v, h, th=th)))
    L.append("\n**Einzelmodelle** (nur zusätzlich berichtet)\n")
    L.append(KOPF_W)
    for var, vn in (("ecmwf", "nur ECMWF"), ("gfs", "nur GFS")):
        for v in (1, 2):
            for h, hn in (("finden", "Finden"), ("bestaetigen", "Bestätigen")):
                L.append(w_zeile(f"{vn}, Vorlauf {v}, {hn}", hw(v, h, var=var)))

    # ---- Zusatz: Preisqualität
    Zs = erg["zusatz"]
    L.append("\n## Zusatzauswertung zur Preisqualität (NACHTRÄGLICH, nicht Teil der festgeschriebenen Regeln, ändert das Urteil nicht)\n")
    L.append("Beim Prüfen der Kalibrierung fiel auf, dass die Marktpreise der Bestätigungshälfte systematisch zu hoch liegen "
             "(Summe der Ja-Preise eines Events statt ca. 1,0 oft 1,3 bis 2,9). Die Summe ist **zum Entscheidungszeitpunkt bekannt**, "
             "ein Filter darauf enthält also keinen Blick in die Zukunft. Ursache: Tiefsttemperatur-Märkte ab Mitte August wurden "
             "erst kurz vor dem Entscheidungszeitpunkt eröffnet und zeigen dann flache Startpreise (0,2–0,3 für alle Buckets) statt "
             "echter Preisbildung. Mittlere Preissumme je Art und Monat (Vorlauf 1, nur Events mit allen Preisen):\n")
    L.append("| Art | Monat | Events | mittlere Preissumme | Anteil Summe > 1,3 |\n|---|---|---|---|---|")
    for k, q in Zs["qualitaet"].items():
        art_, mon_ = k.split("|")
        L.append(f"| {'Höchstwert' if art_ == 'hoechst' else 'Tiefstwert'} | {mon_} | {q['n']} | {q['mittel']:.3f} | {pct(q['anteil_ueber_1_3'])} |")
    L.append(f"\nAnteil der Events mit plausibler Preissumme (0,90–1,15, alle Buckets bepreist): Vorlauf 1 {pct(Zs['anteil_plausibel']['V1'])}, "
             f"Vorlauf 2 {pct(Zs['anteil_plausibel']['V2'])}. Hauptregel nur auf diesen Events:\n")
    L.append("| | Wetten | Treffer | Quote | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) | Brier Modell / Markt |\n|---|---|---|---|---|---|---|---|")
    for name, nn in (("plausibel", "alle Arten"), ("plausibel_hoechst", "nur Höchstwerte"), ("plausibel_tiefst", "nur Tiefstwerte")):
        for v in (1, 2):
            for h, hn in (("finden", "Finden"), ("bestaetigen", "Bestätigen")):
                w, br = Zs["wetten"][f"{name}|V{v}|{h}"], Zs["brier"][f"{name}|V{v}|{h}"]
                bt = "–" if br["modell"] is None else f"{br['modell']:.4f} / {br['markt']:.4f}"
                L.append(w_zeile(f"{nn}, Vorlauf {v}, {hn}", w) + f" {bt} |")
    L.append("\nDie Tabelle ist eine Beschreibung nach Sicht der Daten. Sie zeigt, wie stark das Hauptergebnis der Bestätigungshälfte "
             "(vor allem die Nein-Wetten bei Vorlauf 2) von unreifen Marktpreisen abhängt.\n")

    # ---- Zusatz: Artefakt-Prüfung Nein-Wetten Vorlauf 2
    L.append(artefakt_abschnitt(erg["artefakt"]))

    # ---- Empfindlichkeit
    L.append("\n## Empfindlichkeit: Spread 0,02 / 0,04 / 0,06 (Kante ≥ 0,10, Ja und Nein)\n")
    L.append(KOPF_W)
    for s_ in ("0.02", "0.04", "0.06"):
        for v in (1, 2):
            for h, hn in (("finden", "Finden"), ("bestaetigen", "Bestätigen")):
                L.append(w_zeile(f"Spread {s_.replace('.', ',')}, Vorlauf {v}, {hn}", hw(v, h, s=s_)))

    # ---- Look-ahead
    vs = erg["verstoesse"]
    L.append("\n## Look-ahead-Prüfung\n")
    L.append(f"Alle {erg['haupt_wetten_n']} Hauptwetten wurden maschinell geprüft: Läufe, die nach dem Entscheidungszeitpunkt "
             f"verfügbar wurden: **{vs['lauf_nach_entscheidung']}**; Preispunkte nach dem Entscheidungszeitpunkt: **{vs['preis_nach_entscheidung']}**. "
             "Stichprobe von 20 Wetten (Zufallssamen 42). „Lauf bekannt ab“ = spätester Init der Stützstellen der Stunde des Tagesextrems "
             "+ 10 h (angenommene Verfügbarkeit); „spätester genutzter Lauf bekannt ab“ gilt für alle 24 Stunden des Tages.\n")
    L.append("| Event | Vorl. | Wette | Entscheidung Td | Preispunkt | Preis (Ja) | ECMWF-Lauf (Stunde des Extrems) | Lauf bekannt ab | spätester genutzter Lauf bekannt ab | Prognose bekannt vor Td | Preis vor Td |\n|---|---|---|---|---|---|---|---|---|---|---|")
    for x in erg["stichprobe"]:
        lauf = x["lauf"].get("ecmwf") or {}
        init = lauf.get("init")
        spaet = max(i["verfuegbar_max"] for i in x["lauf"].values())
        L.append(f"| {x['stadt']} {x['datum']} {x['art']} | {x['v']} | {x['seite']} {x['bucket']} | {iso(x['td'])} | {iso(x['preis_t'])} | "
                 f"{x['preis_ja']:.3f} | N={lauf.get('n')}, Init {iso(init) if init else '–'} | {iso(init + 36000) if init else '–'} | "
                 f"{iso(spaet)} | {'ja' if spaet <= x['td'] else 'NEIN'} | {'ja' if x['preis_t'] <= x['td'] else 'NEIN'} |")

    # ---- Gegenrechnung
    L.append("\n## Gegenrechnung mit einem unabhängigen Skript\n")
    if gegen is None:
        L.append("Noch nicht ausgeführt.")
    else:
        L.append("`auswertungen/rueckrechnung_gegenrechnung.py` (eigene Zeitlogik, Intervall-Wahrscheinlichkeit statt Runden, kein numpy, "
                 "ohne Import des Hauptskripts) rechnet aus denselben Rohdaten. Vergleich (Hauptregel; Differenz in $ bzw. Brier):\n")
        L.append("| Größe | Hauptskript | Gegenrechnung | Differenz |\n|---|---|---|---|")
        maxdiff = 0.0
        for v in (1, 2):
            for h in ("finden", "bestaetigen"):
                for s_ in ("0.02", "0.04", "0.06"):
                    a_ = hw(v, h, s=s_)
                    g_ = gegen["wetten"].get(f"V{v}|{h}|S{float(s_)}", {"n": 0, "summe": 0.0, "ohne_top3": 0.0})
                    d = a_["summe"] - g_["summe"]
                    maxdiff = max(maxdiff, abs(d), abs(a_["n"] - g_["n"]))
                    L.append(f"| Wetten/Summe V{v} {h} S{s_} | {a_['n']} / {a_['summe']:+.2f} | {g_['n']} / {g_['summe']:+.2f} | {a_['n'] - g_['n']:+d} / {d:+.4f} |")
                    if s_ == "0.04":
                        d3 = a_["ohne_top3"] - g_["ohne_top3"]
                        maxdiff = max(maxdiff, abs(d3))
                        L.append(f"| ohne 3 beste V{v} {h} | {a_['ohne_top3']:+.2f} | {g_['ohne_top3']:+.2f} | {d3:+.4f} |")
            for h in ("finden", "bestaetigen"):
                bm, bg = B[f"{h}|V{v}|alle"], gegen["brier"][f"{h}|V{v}"]
                for nm, key in (("Brier Modell", "modell"), ("Brier Markt", "markt")):
                    d = bm[key] - bg[key]
                    maxdiff = max(maxdiff, abs(d))
                    L.append(f"| {nm} V{v} {h} (n={bm['n']}/{bg['n']}) | {bm[key]:.6f} | {bg[key]:.6f} | {d:+.2e} |")
        L.append(f"\nGrößte Abweichung: {maxdiff:.2e}. " + ("**Übereinstimmung.**" if maxdiff < 1e-6 else "**Abweichungen vorhanden, siehe oben.**"))

    # ---- Grenzen
    L.append("""
## Was die Rückrechnung nicht zeigt

- **Keine echten Ensembles.** Die Wahrscheinlichkeiten stammen aus zwei deterministischen Modellen plus einer aus 2024–2025 gelernten Fehlerverteilung (je Station, Vorlauf und Art, Mar–Okt). Das Live-Protokoll sammelt echte Ensembles; dieses Verfahren sagt nichts darüber, ob sie besser wären.
- **Angenommener Spread** (0,02/0,04/0,06) statt echter Geld-/Brief-Kurse. Die Preishistorie liefert nur Preispunkte (Mitte oder letzter Handel, genaue Definition unbekannt) und, mit `fidelity = 10`, ein 10-Minuten-Raster, das fehlende Handelsminuten fortschreibt: ein „letzter Preispunkt“ kann alt sein. Der Nein-Preis ist als 1 − Ja-Preis angenommen.
- **Keine Markttiefe.** 10 $ je Wette wurden vollständig zum angenommenen Preis gefüllt angenommen. Die Medianliquidität liegt bei ca. 1 400 $ je Bucket; bei dünnen Büchern wäre die Ausführung schlechter, und bei vielen gleichzeitigen Wetten (mehrere Städte, gleiche Tage) bewegt man den Preis. Tick und Mindestgröße sind nicht berücksichtigt.
- **Quellenwechsel am 2026-08-23** (Weather Underground → NOAA): Die Fehlerverteilung kommt aus METAR; die Auflösung der frühen Märkte lief über Weather Underground, die späten über NOAA. Beide beruhen auf METAR (Übereinstimmung ≥ 96 % mit dem Gewinner), die restlichen Abweichungen sind nicht untersucht und sind in den Ergebnissen als Rauschen enthalten.
- **Angenommene Verfügbarkeit der Läufe** (10 h nach Init, gemessen 9,0–9,3 h heute). Historisch kann sie anders gewesen sein; ein späterer Zeitpunkt wäre vorsichtiger, ein früherer würde bei Vorlauf 1 mehr Stunden aus `previous_day1` zulassen.
- **Zusammensetzung statt „reinem“ Vorlauf:** Wegen der Verfügbarkeit stammt der Tageshöchstwert bei Vorlauf 1 großteils aus `previous_day2` (und bei Vorlauf 2 aus `previous_day3`). Der wirksame Vorlauf ist länger als der Name.
- **Preis zum Entscheidungszeitpunkt:** Der Preis um 18:00 Ortszeit spiegelt nur Informationen bis dahin; spätere (bessere) Vorhersagen am Abend und am Tag selbst, die der Markt aufnimmt, sind nicht erfasst. Das ist die vereinbarte Regel, nicht der Zeitpunkt mit dem besten Preis.
- **Kleine Stichprobe und viele Zellen:** 15 Städte, 7 Monate, ein Jahr Markthistorie. Mehrfachvergleiche (Vorlauf × Hälfte × Seite × Schwelle × Spread) wurden nicht korrigiert; nur die vorab genannte Hauptzelle zählt für das Urteil.
- **Gebühren:** nach `docs/gebuehren.md`; Maker-Rebate und Taker-Rebate-Stufen sind nicht eingerechnet.
- **Nicht untersucht:** Hongkong, die übrigen 34 Städte und die Wirkung von ICON.
""")
    p = Path(f"auswertungen/{datum}_rueckrechnung.md")
    p.write_text("\n".join(L), encoding="utf-8")
    print(p, urteil)


if __name__ == "__main__":
    {"rechnen": rechnen, "bericht": bericht}[sys.argv[1]]()
