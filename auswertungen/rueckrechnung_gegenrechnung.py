"""Unabhängige Gegenrechnung der Rückrechnung (Hauptfall), aus den Rohdaten im Cache.

Bewusst OHNE Import von bot/rueckrechnung.py und auswertungen/rueckrechnung.py, nur aus den Regeln in
auswertungen/rueckrechnung_regeln.md neu geschrieben, mit anderer Technik:
  - Zeitlogik über datetime/zoneinfo (lokaler Tag = UTC-Stunden, deren Ortsdatum der Zieltag ist),
  - Lauf-Rundung über datetime.hour // 6,
  - Bucket-Wahrscheinlichkeit über Intervallgrenzen (rund(x) in [lo, hi]  <=>  lo - 0,5 <= x < hi + 0,5) und bisect,
  - reines Python, kein numpy,
  - (seit 2026-10-14) EIGENES Zieldatum aus dem Fragetext (Event-Titel "... on April 15?", Beschreibung "... on 15 Apr '26"),
    nicht aus dem Slug und nicht aus endDate,
  - (seit 2026-10-14) EIGENE Ableitung der Stützstellen eines Stundenwerts: Welche nativen Stützstellen gehen mit
    Gewicht != 0 in die Catmull-Rom-Interpolation ein? (ECMWF 3 h; GFS stündlich nativ), statt Indexarithmetik.

Aufruf:  python auswertungen/rueckrechnung_gegenrechnung.py   -> auswertungen/rueckrechnung_gegen.json
"""
import bisect
import gzip
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

CACHE = Path("daten/cache")
STAEDTE = "atlanta dallas nyc buenos-aires london seattle seoul toronto ankara chicago miami paris sao-paulo wellington lucknow".split()
TZ = {"atlanta": "America/New_York", "dallas": "America/Chicago", "nyc": "America/New_York", "buenos-aires": "America/Argentina/Buenos_Aires",
      "london": "Europe/London", "seattle": "America/Los_Angeles", "seoul": "Asia/Seoul", "toronto": "America/Toronto",
      "ankara": "Europe/Istanbul", "chicago": "America/Chicago", "miami": "America/New_York", "paris": "Europe/Paris",
      "sao-paulo": "America/Sao_Paulo", "wellington": "Pacific/Auckland", "lucknow": "Asia/Kolkata"}
UTC = timezone.utc
TITEL = re.compile(r"^\s*(-?\d+)(?:\s*-\s*(-?\d+))?\s*°\s*([CF])(?:\s+or\s+(below|higher))?\s*$")


MONAT = {"january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7, "august": 8,
         "september": 9, "october": 10, "november": 11, "december": 12}
KURZ = {k[:3]: v for k, v in MONAT.items()}
TITEL_DATUM = re.compile(r"\bon ([A-Za-z]+) (\d{1,2})\s*\?\s*$")
BESCHR_DATUM = re.compile(r"\bon (\d{1,2}) ([A-Za-z]{3})[a-z]*\.?,? '(\d\d)\b")


def ziel_aus_fragetext(e: dict):
    """Zieltag aus dem Fragetext (Titel: Monat und Tag; Jahr aus der Beschreibung, sonst das Jahr, bei dem das
    Datum am nächsten an endDate liegt). -> (ISO-Datum | None, Hinweis)."""
    m = TITEL_DATUM.search(e.get("titel", ""))
    if not m or m.group(1).lower() not in MONAT:
        return None, "titel_unlesbar"
    monat, tag = MONAT[m.group(1).lower()], int(m.group(2))
    b = BESCHR_DATUM.search(e.get("beschr", ""))
    try:
        if b and b.group(2).lower() in KURZ:
            if (KURZ[b.group(2).lower()], int(b.group(1))) != (monat, tag):
                return None, "titel_beschreibung_widerspruch"
            return datetime(2000 + int(b.group(3)), monat, tag).date().isoformat(), "mit_jahr_aus_beschreibung"
        ende = datetime.fromisoformat(e["ende"][:10]).date()
        kand = []
        for j in (ende.year - 1, ende.year, ende.year + 1):
            try:
                kand.append(datetime(j, monat, tag).date())
            except ValueError:
                pass
        return min(kand, key=lambda d: abs((d - ende).days)).isoformat(), "jahr_aus_enddate"
    except ValueError:
        return None, "datum_ungueltig"


def zeit(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, UTC)


def lade_gz(pfad: Path):
    return json.loads(gzip.open(pfad, "rt", encoding="utf-8").read())


def lokale_stunden(datum: str, tz: str) -> list[datetime]:
    """UTC-Vollstunden, deren Ortsdatum der Zieltag ist."""
    z = ZoneInfo(tz)
    tag = datetime.fromisoformat(datum).date()
    mitte = datetime(tag.year, tag.month, tag.day, 12, tzinfo=UTC)
    out = []
    for k in range(-30, 31):
        t = mitte + timedelta(hours=k)
        if t.astimezone(z).date() == tag:
            out.append(t)
    return out


def td_zeit(datum: str, tz: str, v: int) -> datetime:
    tag = datetime.fromisoformat(datum).date() - timedelta(days=v)
    return datetime(tag.year, tag.month, tag.day, 18, tzinfo=ZoneInfo(tz)).astimezone(UTC)


def cr_gewichte(f: float) -> list[float]:
    """Catmull-Rom-Gewichte der vier Stützstellen (p0, p1, p2, p3) für den Bruchteil f zwischen p1 und p2."""
    return [(-f ** 3 + 2 * f ** 2 - f) / 2, (3 * f ** 3 - 5 * f ** 2 + 2) / 2,
            (-3 * f ** 3 + 4 * f ** 2 + f) / 2, (f ** 3 - f ** 2) / 2]


SCHRITT_H = {"ecmwf": 3, "gfs": 1}  # natives Zeitraster; ECMWF-Stundenwerte dazwischen sind Catmull-Rom-Interpolationen (gemessen)


def abhaengig_von(t: datetime, schritt_h: int) -> list[datetime]:
    """Native Stützstellen (UTC), die mit Gewicht != 0 in den Stundenwert t eingehen."""
    if schritt_h == 1:
        return [t]
    versatz = t.hour % schritt_h
    a = t - timedelta(hours=versatz)
    f = versatz / schritt_h
    stellen = [a + timedelta(hours=schritt_h * k) for k in (-1, 0, 1, 2)]
    return [s_ for s_, w in zip(stellen, cr_gewichte(f)) if abs(w) > 1e-12]


def lauf_fuer(t: datetime, td: datetime, v: int, schritt_h: int):
    """Kleinstes N in v..3, für das jede Stützstelle von t aus einem Lauf stammt, der bis td verfügbar war."""
    for n in range(v, 4):
        ok = True
        for s_ in abhaengig_von(t, schritt_h):
            r = s_ - timedelta(hours=24 * n)
            init = r.replace(hour=(r.hour // 6) * 6, minute=0, second=0, microsecond=0)
            if init + timedelta(hours=10) > td:
                ok = False
                break
        if ok:
            return n
    return None


def tageswerte(serie: dict, datum: str, tz: str, v: int, modell: str):
    """-> (max, min) oder None; serie: n -> {unix: wert}."""
    td = td_zeit(datum, tz, v)
    werte = []
    for t in lokale_stunden(datum, tz):
        n = lauf_fuer(t, td, v, SCHRITT_H[modell])
        if n is None:
            return None
        x = serie[n].get(int(t.timestamp()))
        if x is None:
            return None
        werte.append(x)
    return max(werte), min(werte)


def prog_laden(icao: str, m: str):
    s = {1: {}, 2: {}, 3: {}}
    for name in ("k2024", "k2025", "test"):
        d = lade_gz(CACHE / "prog" / f"{icao}_{m}_{name}.json.gz")
        for n in (1, 2, 3):
            for t, x in zip(d["t"], d[str(n)]):
                if x is not None:
                    s[n][t] = x
    return s


def messung_tag(beob: list, datum: str, tz: str, art: str):
    z = ZoneInfo(tz)
    tag = datetime.fromisoformat(datum).date()
    w = [x for t, x in beob if zeit(t).astimezone(z).date() == tag]
    if len(w) < 8:
        return None
    return max(w) if art == "hoechst" else min(w)


def main():
    ev_alle = lade_gz(CACHE / "events_alle.json.gz")["events"]
    ev, ziele, ziel_hinweise = [], {}, {}
    for e in ev_alle:
        if e["stadt"] not in STAEDTE:
            continue
        z, hinweis = ziel_aus_fragetext(e)
        ziel_hinweise[hinweis] = ziel_hinweise.get(hinweis, 0) + 1
        ziele[e["slug"]] = z
        if z and "2026-03-01" <= z <= "2026-10-11":
            ev.append({**e, "ziel": z})
    einheit = {}
    for e in ev:
        einheit.setdefault(e["stadt"], TITEL.match(e["maerkte"][0]["titel"]).group(3))
    stationen = sorted({(e["text_station"], e["stadt"]) for e in ev if e["text_station"]})
    prog, obs = {}, {}
    for icao, stadt in stationen:
        prog[icao] = {m: prog_laden(icao, m) for m in ("ecmwf", "gfs")}
        o = []
        for name in ("k2024", "k2025", "test"):
            d = lade_gz(CACHE / "messung" / f"{icao}_{name}.json.gz")
            o += [(t, f if einheit[stadt] == "F" else (f - 32) * 5 / 9) for t, f in zip(d["t"], d["f"])]
        obs[icao] = sorted(o)

    # Fehlerverteilung aus 2024-03..10 und 2025-03..10
    tage = []
    for jahr in (2024, 2025):
        d = datetime(jahr, 3, 1).date()
        while d <= datetime(jahr, 10, 31).date():
            tage.append(d.isoformat())
            d += timedelta(days=1)
    zelle = {}
    for icao, stadt in stationen:
        tz = TZ[stadt]
        for v in (1, 2):
            for art in ("hoechst", "tiefst"):
                res = []
                for d in tage:
                    e_, g_ = tageswerte(prog[icao]["ecmwf"], d, tz, v, "ecmwf"), tageswerte(prog[icao]["gfs"], d, tz, v, "gfs")
                    m = messung_tag(obs[icao], d, tz, art)
                    if e_ is None or g_ is None or m is None:
                        continue
                    i = 0 if art == "hoechst" else 1
                    f = (e_[i] + g_[i]) / 2
                    f = f * 1.8 + 32 if einheit[stadt] == "F" else f
                    res.append(m - f)
                zelle[(icao, v, art)] = sorted(res)
    pool = {}
    for (icao, v, art), res in zelle.items():
        st = next(s for i, s in stationen if i == icao)
        pool.setdefault((einheit[st], v, art), []).extend(res)
    for k in pool:
        pool[k].sort()

    preise = {}
    for zeile in (CACHE / "preise.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            z = json.loads(zeile)
            preise[z["slug"]] = z
        except ValueError:
            pass

    def wahrscheinlichkeit(f, res, lo, hi):
        """P(lo <= rund(f + r) <= hi) mit rund(x) = floor(x + 0,5); begrenzt auf [0,005; 0,995]."""
        # Toleranz 1e-9: Werte liegen auf einem 0,05/0,1-Raster, x,5 tritt exakt auf und rundet nach oben
        unten = -float("inf") if lo is None else lo - 0.5 - f - 1e-9  # r >= unten
        oben = float("inf") if hi is None else hi + 0.5 - f - 1e-9  # r < oben
        n = bisect.bisect_left(res, oben) - bisect.bisect_left(res, unten)
        return min(0.995, max(0.005, n / len(res)))

    def gebuehrkosten(preis, spread):
        q = preis + spread / 2
        return q + 0.05 * q * (1 - q)

    ergebnis_wetten = {}
    brier = {}
    n_ausw = {1: 0, 2: 0}
    for e in ev:
        if not e["text_station"] or e["slug"] not in preise:
            continue
        stadt, icao, datum = e["stadt"], e["text_station"], e["ziel"]
        art = "hoechst" if e["art"] == "highest" else "tiefst"
        grenzen = []
        for m in e["maerkte"]:
            mt = TITEL.match(m["titel"])
            a, b, _, zusatz = mt.groups()
            if zusatz == "below":
                grenzen.append((None, int(a)))
            elif zusatz == "higher":
                grenzen.append((int(a), None))
            else:
                grenzen.append((int(a), int(b) if b is not None else int(a)))
        ys = [1 if float(json.loads(m["preise"])[0]) >= 0.99 else 0 for m in e["maerkte"]]
        if sum(ys) != 1:
            continue
        h = "finden" if datum <= "2026-06-30" else "bestaetigen"
        for v in (1, 2):
            e_, g_ = tageswerte(prog[icao]["ecmwf"], datum, TZ[stadt], v, "ecmwf"), tageswerte(prog[icao]["gfs"], datum, TZ[stadt], v, "gfs")
            if e_ is None or g_ is None:
                continue
            i = 0 if art == "hoechst" else 1
            f = (e_[i] + g_[i]) / 2
            f = f * 1.8 + 32 if einheit[stadt] == "F" else f
            res = zelle[(icao, v, art)]
            if len(res) < 300:
                res = pool[(einheit[stadt], v, art)]
            p = [wahrscheinlichkeit(f, res, lo, hi) for lo, hi in grenzen]
            pr = [preise[e["slug"]]["tok"].get(m["token"], {}).get(str(v)) for m in e["maerkte"]]
            if all(x is None for x in pr):
                continue
            n_ausw[v] += 1
            for k, x in enumerate(pr):
                if x is None:
                    continue
                for schluessel in (f"{h}|V{v}", f"alle|V{v}"):
                    b = brier.setdefault(schluessel, [0, 0.0, 0.0])
                    b[0] += 1
                    b[1] += (p[k] - ys[k]) ** 2
                    b[2] += (x[1] - ys[k]) ** 2
            for spread in (0.02, 0.04, 0.06):
                kand = []
                for k, x in enumerate(pr):
                    if x is None:
                        continue
                    for seite, ps, preis in (("ja", p[k], x[1]), ("nein", 1 - p[k], 1 - x[1])):
                        c = gebuehrkosten(preis, spread)
                        if c < 1 and ps - c >= 0.10:
                            kand.append((ps - c, k, seite, c))
                kand.sort(key=lambda z: (-z[0], z[1], z[2]))
                for kante, k, seite, c in kand[:2]:
                    gewinnt = ys[k] == 1 if seite == "ja" else ys[k] == 0
                    gewinn = 10 / c - 10 if gewinnt else -10
                    ergebnis_wetten.setdefault(f"V{v}|{h}|S{spread}", []).append(gewinn)
                    ergebnis_wetten.setdefault(f"V{v}|alle|S{spread}", []).append(gewinn)

    aus = {"wetten": {}, "brier": {}, "auswertbar": n_ausw, "ziele": ziele, "ziel_hinweise": ziel_hinweise, "events_testzeitraum": len(ev)}
    for k, liste in ergebnis_wetten.items():
        s = sum(liste)
        aus["wetten"][k] = {"n": len(liste), "summe": s, "ohne_top3": s - sum(sorted(liste, reverse=True)[:3])}
    for k, (n, sm, sk) in brier.items():
        aus["brier"][k] = {"n": n, "modell": sm / n, "markt": sk / n}
    Path("auswertungen/rueckrechnung_gegen.json").write_text(json.dumps(aus, indent=1), encoding="utf-8")
    print(json.dumps({"auswertbar": n_ausw, "wetten": {k: v["n"] for k, v in aus["wetten"].items() if "alle" in k and "S0.04" in k}}))


if __name__ == "__main__":
    main()
