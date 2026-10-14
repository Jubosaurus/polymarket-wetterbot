"""Live-Hypothese 1: Auswertung der Protokolldaten (daten/). Nur Auswertung, keine Wett-Logik im Bot.

Regeln (festgeschrieben, nicht ändern): auswertungen/live_hypothese_1.md, Stationskorrektur: auswertungen/live_bias.json.
Kein Netzzugriff.

Aufruf:
  python auswertungen/live_auswertung.py                # Zählstand (keine Gewinne, keine Quoten, kein Brier)
  python auswertungen/live_auswertung.py --auswerten    # einmalige Auswertung; nur wenn die ersten 200 Hauptwetten aufgelöst sind
                                                        # -> auswertungen/live_hypothese_1_ergebnis.md (wird nie überschrieben)

Auslegung an einer Stelle, an der der Text der Hypothese zwei Reihenfolgen zulässt: Es werden zuerst die höchstens zwei
größten Kanten je Event, Seite und Variante gewählt und danach die Tiefe geprüft (wörtliche Reihenfolge im Text); eine
Wette ohne ausreichende Tiefe entfällt ersatzlos und rückt keine dritte Kante nach (vorsichtigere Auslegung).
"""
import argparse
import csv
import gzip
import json
import math
import re
import sys
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bot import rueckrechnung as rr  # noqa: E402
from bot.buckets import c_nach_f, parse_bucket  # noqa: E402
from bot.stationen import STATIONEN  # noqa: E402

DATEN = Path("daten")
BIAS = Path("auswertungen/live_bias.json")
START = Path("auswertungen/live_start.txt")  # UTC-Zeitpunkt, ab dem das Protokoll mit den korrigierten Stationskoordinaten läuft
ERGEBNIS = Path("auswertungen/live_hypothese_1_ergebnis.md")
ZIEL_AB = "2026-10-16"  # Zieltage ab hier (Entscheidung nach der Festschreibung)
EINSATZ = 10.0
KANTE = 0.10
MAX_JE_EVENT = 2
MAX_VERSPAETUNG_S = 60 * 60
N_STICHPROBE = 200
MIN_MODELLE = 2
VARIANTEN = (("nein", 2), ("ja", 2), ("nein", 1), ("ja", 1), ("nein_breit", 2), ("blind", 2))  # erste = Hauptvariante, Rest nur Vergleich
NAMEN = {"nein": "Nein", "ja": "Ja", "nein_breit": "Nein, Ensemble auf Residuenstreuung aufgeweitet",
         "blind": "Blind-Nein (Ja-Ask ≤ 0,10, ohne Modell)"}
BLIND_ASK = 0.10
TAG = re.compile(r"^\d{4}-\d{2}-\d{2}$")
UTC = timezone.utc


def lese(pfad: Path) -> list[dict]:
    with gzip.open(pfad, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def zeit(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def zahl(text):
    try:
        return float(text) if text not in ("", None) else None
    except ValueError:
        return None


# ------------------------------------------------------------------ Daten laden

def schnappschuesse(daten: Path) -> list[tuple[int, Path, Path]]:
    """(Startzeit als Unix-Zeit, Schnappschuss-Datei, Tagesordner), nach Zeit sortiert."""
    out = []
    for tag in sorted(p for p in daten.iterdir() if p.is_dir() and TAG.match(p.name)):
        for f in tag.glob("maerkte_[0-9][0-9][0-9][0-9].csv.gz"):
            hhmm = f.name[len("maerkte_"):len("maerkte_") + 4]
            start = datetime.strptime(tag.name + hhmm, "%Y-%m-%d%H%M").replace(tzinfo=UTC)
            out.append((int(start.timestamp()), f, tag))
    return sorted(out)


def stamm_des_tages(tag: Path) -> dict[str, dict]:
    """idx -> Stammzeile; spätere Dateien des Tages überschreiben frühere."""
    out = {}
    for f in sorted(tag.glob("maerkte_stamm_*.csv.gz")):
        for z in lese(f):
            out[z["idx"]] = z
    return out


def ensemble_index(daten: Path) -> dict[tuple, dict[str, list[tuple[datetime, list[float]]]]]:
    """(stadt, art, datum) -> {modell: [(empfangen_utc, werte_c)]}, nach Empfang sortiert."""
    idx = defaultdict(lambda: defaultdict(list))
    for tag in sorted(p for p in daten.iterdir() if p.is_dir() and TAG.match(p.name)):
        for f in sorted(tag.glob("ensemble_*.csv.gz")):
            for z in lese(f):
                try:
                    werte = [float(x) for x in z["werte_c"].split()]
                    emp = zeit(z["empfangen_utc"])
                except (ValueError, KeyError):
                    continue
                if werte:
                    idx[(z["stadt"], z["art"], z["datum"])][z["modell"]].append((emp, werte))
    for modelle in idx.values():
        for v in modelle.values():
            v.sort(key=lambda x: x[0])
    return idx


def aufloesungen(daten: Path) -> dict[str, str]:
    """event_slug -> gewinner_bucket (Polymarket-Gewinner); jüngster Eintrag gilt."""
    out = {}
    for tag in sorted(p for p in daten.iterdir() if p.is_dir() and TAG.match(p.name)):
        f = tag / "aufloesung.csv.gz"
        if f.exists():
            for z in lese(f):
                if z.get("gewinner_bucket"):
                    out[z["event_slug"]] = z["gewinner_bucket"]
    return out


def events_aus_stamm(daten: Path) -> dict[str, dict]:
    """event_slug -> Merkmale (Stadt, Station, Art, Zieltag, Einheit, Rundung) aus allen Stammdateien.
    Der Zieltag kommt aus dem Slug (rr.zieldatum_aus_slug, wie in der Rückrechnung), nicht aus dem Stamm-Datum: Das Protokoll
    nimmt bei fehlendem eventDate `endDate`, und das liegt bei einzelnen Events einen Tag später (Codex-Review 2026-10-14).
    Das Stamm-Datum steht als `stamm_datum` daneben; Abweichungen werden gezählt. Unlesbarer Slug: Event entfällt."""
    out = {}
    for tag in sorted(p for p in daten.iterdir() if p.is_dir() and TAG.match(p.name)):
        for f in sorted(tag.glob("maerkte_stamm_*.csv.gz")):
            for z in lese(f):
                if z["art"] in ("hoechst", "tiefst") and z["event_slug"] not in out:
                    ziel = rr.zieldatum_aus_slug(z["event_slug"], z.get("ende_utc"))
                    ev = {k: z[k] for k in ("stadt", "station", "art", "datum", "einheit", "rundung")}
                    ev["stamm_datum"], ev["datum"] = z["datum"], ziel
                    out[z["event_slug"]] = ev
    return out


# ------------------------------------------------------------------ Rechenkern

def kosten(preis: float, fee_rate: float) -> float:
    """Kosten je Anteil: Kaufpreis plus Taker-Gebühr fee_rate * q * (1 - q) (docs/gebuehren.md)."""
    return preis + fee_rate * preis * (1.0 - preis)


def pool_mitglieder(index: dict, stadt: str, art: str, datum: str, bis: datetime, ab: datetime | None = None) -> tuple[list[float], list[str]]:
    """Je Modell die Zeile mit dem jüngsten Empfang <= bis (und >= ab: nur Abrufe mit korrigierten Koordinaten);
    alle Mitglieder gepoolt (gleiches Gewicht je Mitglied)."""
    werte, modelle = [], []
    for m, zeilen in sorted(index.get((stadt, art, datum), {}).items()):
        ok = [z for z in zeilen if z[0] <= bis and (ab is None or z[0] >= ab)]
        if ok:
            werte += ok[-1][1]
            modelle.append(m)
    return werte, modelle


def bucket_p(werte_c: list[float], einheit: str, bias: float, buckets: list, regel: str, sd_res: float | None = None) -> list[float]:
    """Anteil der Mitglieder (plus Bias) im Bucket, Rundung wie bot/rueckrechnung.bucket_p, begrenzt auf [P_MIN, P_MAX].
    Mit sd_res (nur Vergleichsvariante): Streuung der Mitglieder um ihr Mittel auf die Residuenstreuung aufgeweitet,
    falls sie kleiner ist."""
    x = [(c_nach_f(w) if einheit == "F" else w) for w in werte_c]
    if sd_res:
        m = sum(x) / len(x)
        sd = math.sqrt(sum((v - m) ** 2 for v in x) / len(x))
        if 0 < sd < sd_res:
            x = [m + (v - m) * sd_res / sd for v in x]
    x = [v + bias for v in x]
    ganz = [math.floor(v + rr.EPS) if regel == "abschneiden" else math.floor(v + 0.5 + rr.EPS) for v in x]
    return [min(rr.P_MAX, max(rr.P_MIN, sum(1 for g in ganz if b.enthaelt(g)) / len(ganz))) for b in buckets]


def waehle(kandidaten: list[dict]) -> list[dict]:
    ok = [k for k in kandidaten if k["kante"] >= KANTE]
    ok.sort(key=lambda k: (-k["kante"], k["bucket_idx"]))
    return ok[:MAX_JE_EVENT]


def stat(profite: list[float]) -> dict:
    n = len(profite)
    if n == 0:
        return {"n": 0, "wins": 0, "rate": None, "summe": 0.0, "je_wette": None, "ohne_top3": 0.0}
    s = sum(profite)
    return {"n": n, "wins": sum(1 for p in profite if p > 0), "rate": sum(1 for p in profite if p > 0) / n, "summe": s,
            "je_wette": s / n, "ohne_top3": s - sum(sorted(profite, reverse=True)[:3])}


class Daten:
    def __init__(self, daten: Path = DATEN, bias_pfad: Path = BIAS, ab: datetime | None = None):
        self.daten = daten
        self.ab = ab
        self.snaps = schnappschuesse(daten)
        self.starts = [s[0] for s in self.snaps]
        self.ens = ensemble_index(daten)
        self.aufl = aufloesungen(daten)
        self.events = events_aus_stamm(daten)
        self.bias = json.loads(bias_pfad.read_text(encoding="utf-8"))["bias"]
        self._stamm, self._snap = {}, {}

    def stamm(self, tag: Path) -> dict:
        if tag not in self._stamm:
            self._stamm[tag] = stamm_des_tages(tag)
        return self._stamm[tag]

    def snapshot(self, pfad: Path) -> dict:
        if pfad not in self._snap:
            self._snap[pfad] = {z["idx"]: z for z in lese(pfad)}
        return self._snap[pfad]


def entscheidung(d: Daten, slug: str, ev: dict, v: int, zaehler: dict):
    """Entscheidungsgrundlage eines Events für Vorlauf v oder None (Grund im Zähler)."""
    tz = STATIONEN[ev["stadt"]].tz if ev["stadt"] in STATIONEN else None
    if tz is None or f"{ev['station']}|V{v}|{ev['art']}" not in d.bias:
        zaehler[f"ohne_bias_oder_station_v{v}"] += 1
        return None
    td = rr.entscheidungszeit(ev["datum"], tz, v)
    if d.ab is not None and td < d.ab.timestamp():
        zaehler[f"vor_koordinatenkorrektur_v{v}"] += 1
        return None
    i = bisect_left(d.starts, td)
    if i >= len(d.starts) or d.starts[i] - td > MAX_VERSPAETUNG_S:
        zaehler[f"luecke_v{v}"] += 1
        return None
    start, snap_pfad, tag = d.snaps[i]
    stamm = d.stamm(tag)
    snap = d.snapshot(snap_pfad)
    zeilen = sorted((z for idx, z in stamm.items() if z["event_slug"] == slug and idx in snap), key=lambda z: int(z["idx"]))
    if not zeilen:
        zaehler[f"kein_markt_v{v}"] += 1
        return None
    werte, modelle = pool_mitglieder(d.ens, ev["stadt"], ev["art"], ev["datum"], datetime.fromtimestamp(start, UTC), d.ab)
    if len(modelle) < MIN_MODELLE:
        zaehler[f"zu_wenig_modelle_v{v}"] += 1
        return None
    try:
        buckets = [parse_bucket(z["bucket"]) for z in zeilen]
    except ValueError:
        zaehler[f"bucket_unlesbar_v{v}"] += 1
        return None
    bz = d.bias[f"{ev['station']}|V{v}|{ev['art']}"]
    ps = bucket_p(werte, ev["einheit"], bz["bias"], buckets, ev["rundung"])
    ps_breit = bucket_p(werte, ev["einheit"], bz["bias"], buckets, ev["rundung"], sd_res=bz.get("sd"))
    bs = []
    for z, p, pb in zip(zeilen, ps, ps_breit):
        s = snap[z["idx"]]
        bs.append({"titel": z["bucket"], "p": p, "p_breit": pb, "bid": zahl(s["bid"]), "ask": zahl(s["ask"]),
                   "bid_groesse": zahl(s["bid_groesse"]), "ask_groesse": zahl(s["ask_groesse"]),
                   "fee_rate": zahl(z["fee_rate"]) if z["fees_aktiv"] == "True" else 0.0,
                   "fee_exponent": zahl(z["fee_exponent"]), "min_groesse": zahl(z["min_groesse"]) or 0.0})
    mitten = [(b["bid"] + b["ask"]) / 2 for b in bs if b["bid"] is not None and b["ask"] is not None]
    return {"slug": slug, "stadt": ev["stadt"], "datum": ev["datum"], "art": ev["art"], "v": v, "td": td, "snap": start,
            "buckets": bs, "preissumme": sum(mitten) if len(mitten) == len(bs) else None, "modelle": modelle}


def wetten_aus(e: dict, seite: str, zaehler: dict, pkey: str = "p", tag: str | None = None) -> list[dict]:
    tag = tag or seite
    kand = []
    for i, b in enumerate(e["buckets"]):
        if b["fee_exponent"] not in (None, 1.0) and b["fee_rate"]:
            continue  # Gebührenexponent ≠ 1: nicht raten (docs/gebuehren.md)
        if seite == "nein":
            if b["bid"] is None:
                continue
            q, tiefe, p_seite = 1.0 - b["bid"], b["bid_groesse"], 1.0 - b[pkey]
        else:
            if b["ask"] is None:
                continue
            q, tiefe, p_seite = b["ask"], b["ask_groesse"], b[pkey]
        c = kosten(q, b["fee_rate"])
        if not 0.0 < q < 1.0 or c >= 1.0:
            continue
        kand.append({"bucket_idx": i, "titel": b["titel"], "seite": seite, "q": q, "kosten": c, "p_seite": p_seite,
                     "kante": p_seite - c, "tiefe": tiefe, "min_groesse": b["min_groesse"]})
    out = []
    for k in waehle(kand):
        anteile = EINSATZ / k["kosten"]
        if k["tiefe"] is None or k["tiefe"] < anteile or anteile < k["min_groesse"]:
            zaehler[f"ohne_tiefe_{tag}_v{e['v']}"] += 1
            continue
        out.append({**k, "slug": e["slug"], "stadt": e["stadt"], "datum": e["datum"], "art": e["art"], "v": e["v"], "td": e["td"],
                    "anteile": anteile, "preissumme": e["preissumme"]})
    return out


def blind_nein(e: dict, zaehler: dict) -> list[dict]:
    """Vergleichsgruppe ohne Modell: Nein auf jeden Bucket mit Ja-Ask <= BLIND_ASK (Nein-Ask = 1 - bester Ja-Bid), gleiche
    Gebühr- und Tiefenregel, keine Kantenschwelle, keine Begrenzung je Event."""
    out = []
    for i, b in enumerate(e["buckets"]):
        if b["ask"] is None or b["ask"] > BLIND_ASK or b["bid"] is None:
            continue
        if b["fee_exponent"] not in (None, 1.0) and b["fee_rate"]:
            continue
        q = 1.0 - b["bid"]
        c = kosten(q, b["fee_rate"])
        if not 0.0 < q < 1.0 or c >= 1.0:
            continue
        anteile = EINSATZ / c
        if b["bid_groesse"] is None or b["bid_groesse"] < anteile or anteile < b["min_groesse"]:
            zaehler[f"ohne_tiefe_blind_v{e['v']}"] += 1
            continue
        out.append({"bucket_idx": i, "titel": b["titel"], "seite": "nein", "q": q, "kosten": c, "p_seite": None, "kante": None,
                    "tiefe": b["bid_groesse"], "min_groesse": b["min_groesse"], "slug": e["slug"], "stadt": e["stadt"],
                    "datum": e["datum"], "art": e["art"], "v": e["v"], "td": e["td"], "anteile": anteile,
                    "preissumme": e["preissumme"]})
    return out


def lose_auf(w: dict, aufl: dict, titel_je_slug: dict) -> None:
    """Setzt gewinnt/gewinn, wenn der Polymarket-Gewinner bekannt und einer der Buckets des Events ist."""
    g = aufl.get(w["slug"])
    w["gewinnt"], w["gewinn"] = None, None
    if g is None or g not in titel_je_slug.get(w["slug"], ()):
        return
    w["gewinnt"] = (g == w["titel"]) if w["seite"] == "ja" else (g != w["titel"])
    w["gewinn"] = w["anteile"] - EINSATZ if w["gewinnt"] else -EINSATZ


def berechne(d: Daten):
    zaehler = defaultdict(int)
    entscheidungen, wetten = {}, defaultdict(list)
    titel_je_slug = {}
    for slug, ev in sorted(d.events.items()):
        if ev["datum"] is None:
            zaehler["zieltag_unlesbar"] += 1
            continue
        if ev["datum"] != ev["stamm_datum"]:
            zaehler["zieltag_weicht_vom_stamm_ab"] += 1
        if ev["datum"] < ZIEL_AB:
            continue
        for v in (1, 2):
            e = entscheidung(d, slug, ev, v, zaehler)
            if e is None:
                continue
            entscheidungen[(slug, v)] = e
            titel_je_slug[slug] = {b["titel"] for b in e["buckets"]}
            zaehler[f"entscheidungen_v{v}"] += 1
            for seite in ("nein", "ja"):
                for w in wetten_aus(e, seite, zaehler):
                    lose_auf(w, d.aufl, titel_je_slug)
                    wetten[(seite, v)].append(w)
            if v == 2:
                for w in wetten_aus(e, "nein", zaehler, pkey="p_breit", tag="nein_breit"):
                    lose_auf(w, d.aufl, titel_je_slug)
                    wetten[("nein_breit", 2)].append(w)
                for w in blind_nein(e, zaehler):
                    lose_auf(w, d.aufl, titel_je_slug)
                    wetten[("blind", 2)].append(w)
    for k in wetten:
        wetten[k].sort(key=lambda w: (w["td"], w["slug"], w["bucket_idx"]))
    return dict(zaehler), entscheidungen, dict(wetten)


def stichprobe(wetten: dict) -> list[dict]:
    return wetten.get(VARIANTEN[0], [])[:N_STICHPROBE]


def bereit(wetten: dict) -> bool:
    s = stichprobe(wetten)
    return len(s) >= N_STICHPROBE and all(w["gewinn"] is not None for w in s)


def urteil(s: list[dict]) -> dict:
    """Kriterien der Hypothese: Gewinn je Wette > 0, Summe ohne die 3 besten > 0, Summe > 0 in beiden Hälften."""
    gew = [w["gewinn"] for w in s]
    h = len(gew) // 2
    gesamt, h1, h2 = stat(gew), stat(gew[:h]), stat(gew[h:])
    k = {"je_wette_positiv": gesamt["je_wette"] is not None and gesamt["je_wette"] > 0,
         "ohne_top3_positiv": gesamt["ohne_top3"] > 0, "haelfte1_positiv": h1["summe"] > 0, "haelfte2_positiv": h2["summe"] > 0}
    return {"gesamt": gesamt, "haelfte1": h1, "haelfte2": h2, "kriterien": k, "bestaetigt": all(k.values())}


# ------------------------------------------------------------------ Ausgabe

def zaehlstand(zaehler: dict, wetten: dict) -> str:
    L = ["Zählstand (nur Anzahlen, vor Erreichen der Stichprobe wird nichts anderes ausgegeben):"]
    for k, v in sorted(zaehler.items()):
        L.append(f"  {k}: {v}")
    for (seite, v), ws in sorted(wetten.items()):
        aufg = sum(1 for w in ws if w["gewinn"] is not None)
        L.append(f"  Wetten {seite} Vorlauf {v}: {len(ws)}, davon aufgelöst {aufg}")
    s = stichprobe(wetten)
    L.append(f"  Hauptvariante (Nein, Vorlauf 2): {len(wetten.get(VARIANTEN[0], []))} von {N_STICHPROBE} nötigen; "
             f"davon in der Stichprobe aufgelöst {sum(1 for w in s if w['gewinn'] is not None)}")
    return "\n".join(L)


def usd(x) -> str:
    return "–" if x is None else f"{x:+.2f}"


def zeile(name: str, w: dict) -> str:
    rate = "–" if w["rate"] is None else f"{w['rate'] * 100:.1f} %"
    return f"| {name} | {w['n']} | {w['wins']} | {rate} | {usd(w['je_wette'])} | {usd(w['summe'])} | {usd(w['ohne_top3'])} |"


KOPF = "| | Wetten | Treffer | Quote | Gewinn je Wette ($) | Summe ($) | ohne 3 beste ($) |\n|---|---|---|---|---|---|---|"


def bericht(d: Daten, zaehler: dict, entscheidungen: dict, wetten: dict) -> str:
    s = stichprobe(wetten)
    u = urteil(s)
    td_ende = s[-1]["td"]
    L = [f"# Live-Hypothese 1: Auswertung ({datetime.now(UTC).strftime('%Y-%m-%d')})\n",
         "Regeln: `auswertungen/live_hypothese_1.md` (vorab festgeschrieben). Nur Auswertung der Protokolldaten, keine Wetten.\n",
         f"## Urteil: **{'BESTÄTIGT' if u['bestaetigt'] else 'NICHT BESTÄTIGT'}**\n",
         "Kriterien (vorab): Gewinn je Wette > 0, Summe ohne die 3 besten > 0, Summe > 0 in beiden Hälften (nach Zeit). Messlatte null nach Kosten.\n",
         "| Kriterium | erfüllt |\n|---|---|"]
    for k, v in u["kriterien"].items():
        L.append(f"| {k} | {'ja' if v else 'nein'} |")
    L += ["", "## Hauptvariante: Nein-Wetten, Vorlauf 2, die ersten 200 nach Entscheidungszeit\n", KOPF,
          zeile("alle 200", u["gesamt"]), zeile("erste Hälfte", u["haelfte1"]), zeile("zweite Hälfte", u["haelfte2"])]
    slugs = {w["slug"] for w in s}
    pm, pk, y = [], [], []
    for slug in sorted(slugs):
        e = entscheidungen[(slug, 2)]
        g = d.aufl.get(slug)
        for b in e["buckets"]:
            if b["bid"] is not None and b["ask"] is not None and g is not None:
                pm.append(b["p"]); pk.append((b["bid"] + b["ask"]) / 2); y.append(1 if b["titel"] == g else 0)
    if y:
        L.append(f"\nBrier über alle Buckets der {len(slugs)} Events der Stichprobe ({len(y)} Buckets): Modell {rr.brier(pm, y):.4f}, "
                 f"Mitte des Ja-Preises {rr.brier(pk, y):.4f}.")
    sums = sorted(w["preissumme"] for w in s if w["preissumme"] is not None)
    if sums:
        L.append(f"Preissumme der Events (Summe der Ja-Mitten, nur Beschreibung): Median {sums[len(sums) // 2]:.3f}, "
                 f"Minimum {sums[0]:.3f}, Maximum {sums[-1]:.3f}, Wetten mit bekannter Summe {len(sums)} von {len(s)}.")
    L += ["", "## Zählstand und Ausfälle\n", "```", zaehlstand(zaehler, wetten), "```",
          "", "## Zum Vergleich (nicht Entscheidungsgrundlage): gleiche Regel, Wetten mit Entscheidung bis zum Zeitpunkt der 200. Hauptwette, ohne Mindestzahl\n",
          KOPF]
    for (seite, v) in VARIANTEN[1:]:
        ws = [w for w in wetten.get((seite, v), []) if w["td"] <= td_ende and w["gewinn"] is not None]
        L.append(zeile(f"{NAMEN[seite]}, Vorlauf {v}", stat([w["gewinn"] for w in ws])))
    L.append("\nAlle Hauptwetten der Stichprobe stehen mit Zeitpunkt, Preis, Tiefe und Ergebnis in `auswertungen/live_hypothese_1_wetten.csv`.")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--auswerten", action="store_true")
    a = ap.parse_args()
    if not START.exists():
        print(f"{START} fehlt: Zeitpunkt (UTC, ISO), ab dem das Protokoll mit den korrigierten Koordinaten läuft. "
              "Ohne ihn keine Auswertung.")
        return 2
    d = Daten(ab=zeit(START.read_text(encoding="utf-8").strip()))
    zaehler, entscheidungen, wetten = berechne(d)
    if not a.auswerten:
        print(zaehlstand(zaehler, wetten))
        return 0
    if ERGEBNIS.exists():
        print(f"{ERGEBNIS} existiert bereits: die Auswertung gilt einmal und wird nicht überschrieben.")
        return 1
    if not bereit(wetten):
        print("Noch nicht bereit: die ersten 200 Hauptwetten sind nicht vollständig aufgelöst.\n" + zaehlstand(zaehler, wetten))
        return 1
    ERGEBNIS.write_text(bericht(d, zaehler, entscheidungen, wetten), encoding="utf-8")
    s = stichprobe(wetten)
    with open(ERGEBNIS.with_name("live_hypothese_1_wetten.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(s[0]), extrasaction="ignore")
        w.writeheader()
        w.writerows(s)
    print(ERGEBNIS, "geschrieben")
    return 0


if __name__ == "__main__":
    sys.exit(main())
