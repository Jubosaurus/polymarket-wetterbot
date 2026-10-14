"""Rückrechnung (Phase 1b): reine Rechenfunktionen, keine Netzzugriffe.

Regeln (festgeschrieben, nicht ändern): auswertungen/rueckrechnung_regeln.md
Nur Auswertung, keine Wetten.
"""
import math
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from bot.buckets import Bucket

LAG_H = 10  # angenommene Verfügbarkeitsverzögerung eines Modelllaufs (gemessen 9,0-9,3 h)
ZYKLUS_S = 6 * 3600  # Läufe 00/06/12/18 UTC
FEE_RATE = 0.05  # docs/gebuehren.md, Kategorie Wetter, nur Taker
EINSATZ = 10.0
P_MIN, P_MAX = 0.005, 0.995
EPS = 1e-9  # Vorhersage und Messung liegen auf einem 0,05/0,1-Raster: x,5 tritt exakt auf; die Toleranz verhindert Gleitkomma-Rauschen (x,5 rundet nach oben)


MONATE = {m: i + 1 for i, m in enumerate("january february march april may june july august september october november december".split())}
_SLUG_DATUM = re.compile(r"-on-([a-z]+)-(\d{1,2})(?:-(\d{4}))?$")


def zieldatum_aus_slug(slug: str, ende: str | None = None) -> str | None:
    """Zieltag (lokaler Kalendertag der Station) aus dem Event-Slug, z. B. '...-on-april-15-2026'.
    Nicht `endDate`: bei manchen Events liegt es einen Tag später. Fehlt das Jahr im Slug (frühe Events),
    gilt das Jahr, bei dem das Datum am nächsten an `ende` (ISO-Text) liegt. Unlesbar -> None."""
    m = _SLUG_DATUM.search(slug)
    if not m or m.group(1) not in MONATE:
        return None
    monat, tag = MONATE[m.group(1)], int(m.group(2))
    try:
        if m.group(3):
            return date(int(m.group(3)), monat, tag).isoformat()
        if not ende:
            return None
        e = date.fromisoformat(ende[:10])
        kand = []
        for j in (e.year - 1, e.year, e.year + 1):
            try:
                kand.append(date(j, monat, tag))
            except ValueError:
                pass
        return min(kand, key=lambda d: abs((d - e).days)).isoformat() if kand else None
    except ValueError:
        return None


def preiszeile_gueltig(zeile: dict, ziel_datum: str, tz: str) -> bool:
    """Eine zwischengespeicherte Preiszeile gilt nur, wenn ihre Entscheidungszeiten zum Zieltag passen."""
    td = zeile.get("td")
    return bool(td) and all(td.get(str(v)) == entscheidungszeit(ziel_datum, tz, v) for v in (1, 2))


def lokal_nach_utc_ts(datum: str, stunde: int, tz: str) -> int:
    d = date.fromisoformat(datum)
    return int(datetime(d.year, d.month, d.day, stunde, tzinfo=ZoneInfo(tz)).timestamp())


def entscheidungszeit(ziel_datum: str, tz: str, vorlauf: int) -> int:
    """18:00 Ortszeit am Tag (Zieltag - Vorlauf), als Unix-Zeit."""
    d = date.fromisoformat(ziel_datum) - timedelta(days=vorlauf)
    return lokal_nach_utc_ts(d.isoformat(), 18, tz)


def tag_grenzen(datum: str, tz: str) -> tuple[int, int]:
    """[Beginn, Ende) des lokalen Kalendertags als Unix-Zeit (Ende = Beginn des Folgetags)."""
    d = date.fromisoformat(datum)
    return lokal_nach_utc_ts(d.isoformat(), 0, tz), lokal_nach_utc_ts((d + timedelta(days=1)).isoformat(), 0, tz)


def tag_stunden(datum: str, tz: str) -> list[int]:
    """Volle UTC-Stunden, die im lokalen Kalendertag liegen (23/25 an Zeitumstellungen,
    bei halbstündigen Zeitzonen wie Indien die vollen Stunden innerhalb des Tags)."""
    start, ende = tag_grenzen(datum, tz)
    erste = -(-start // 3600) * 3600
    return list(range(erste, ende, 3600))


def stuetzstellen(t: int, raster_h: int = 1) -> list[int]:
    """UTC-Zeiten der nativen Stützstellen, aus denen der Stundenwert t entsteht.

    Gemessen (Cache, 14 696 Stunden je Modell): ECMWF IFS-Stundenwerte außerhalb des 3-h-Rasters sind
    Catmull-Rom-Interpolationen über vier Stützstellen (a-3 h, a, a+3 h, a+6 h; max. Abweichung 0,08 °C).
    Auf einer Stützstelle ist der Wert nativ. GFS ist stündlich nativ (raster_h = 1)."""
    s = raster_h * 3600
    if raster_h <= 1 or t % s == 0:
        return [t]
    a = t // s * s
    return [a - s, a, a + s, a + 2 * s]


def bekannter_lauf(t: int, td: int, vorlauf: int, lag_h: float = LAG_H, nmax: int = 3, raster_h: int = 1):
    """Kleinstes N >= vorlauf (höchstens nmax), für das ALLE Stützstellen des Stundenwerts t zum Entscheidungszeitpunkt
    td aus verfügbaren Läufen stammen. Lauf einer Stützstelle s = floor6(s - 24*N h). -> (N, spätester Lauf) oder None."""
    for n in range(vorlauf, nmax + 1):
        inits = [(s - 24 * 3600 * n) // ZYKLUS_S * ZYKLUS_S for s in stuetzstellen(t, raster_h)]
        if max(inits) + lag_h * 3600 <= td:
            return n, max(inits)
    return None


def komposit_tageswerte(serien: dict[int, dict[int, float]], datum: str, tz: str, vorlauf: int,
                        lag_h: float = LAG_H, raster_h: int = 1):
    """Tageshöchst-/Tiefstwert aus dem zum Entscheidungszeitpunkt bekannten Lauf je Stunde.

    serien: N -> {unix_stunde: wert}. raster_h: natives Zeitraster des Modells (ECMWF 3, GFS 1).
    Rückgabe None, wenn für eine Stunde kein bekannter Lauf oder kein Wert existiert. Sonst
    dict(max, min, max_t, min_t, max_n, max_init, min_n, min_init, td)."""
    td = entscheidungszeit(datum, tz, vorlauf)
    zeilen = []
    for t in tag_stunden(datum, tz):
        k = bekannter_lauf(t, td, vorlauf, lag_h, raster_h=raster_h)
        if k is None:
            return None
        n, init = k
        v = serien.get(n, {}).get(t)
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return None
        zeilen.append((v, t, n, init))
    hoch = max(zeilen, key=lambda z: (z[0], -z[1]))
    tief = min(zeilen, key=lambda z: (z[0], z[1]))
    return {"max": hoch[0], "max_t": hoch[1], "max_n": hoch[2], "max_init": hoch[3],
            "min": tief[0], "min_t": tief[1], "min_n": tief[2], "min_init": tief[3], "td": td,
            "verfuegbar_max": max(z[3] for z in zeilen) + int(lag_h * 3600)}  # späteste Verfügbarkeit aller genutzten Läufe


def tageswert_messung(beobachtungen: list[tuple[int, float]], datum: str, tz: str, art: str, min_beob: int = 8):
    """Tageshöchst-/Tiefstwert der Messung (Unix-Zeit, Wert) im lokalen Kalendertag, sonst None."""
    start, ende = tag_grenzen(datum, tz)
    w = [v for t, v in beobachtungen if start <= t < ende]
    if len(w) < min_beob:
        return None
    return max(w) if art == "hoechst" else min(w)


def in_einheit(wert_c: float, einheit: str) -> float:
    return wert_c * 9.0 / 5.0 + 32.0 if einheit == "F" else wert_c


def residuen(paare: list[tuple[float, float]]) -> np.ndarray:
    """paare: (Vorhersage, Messwert) in Markteinheit -> Messwert - Vorhersage."""
    return np.array([m - f for f, m in paare], dtype=float)


def bucket_p(f_einheit: float, res: np.ndarray, buckets: list[Bucket], regel: str = "kaufm") -> list[float]:
    """P(Bucket) = Anteil der Residuen mit rund(F + r) im Bucket, begrenzt auf [P_MIN, P_MAX]."""
    if len(res) == 0:
        raise ValueError("keine Residuen")
    x = f_einheit + res
    ganz = np.floor(x + EPS) if regel == "abschneiden" else np.floor(x + 0.5 + EPS)
    out = []
    for b in buckets:
        ok = np.ones(len(ganz), dtype=bool)
        if b.lo is not None:
            ok &= ganz >= b.lo
        if b.hi is not None:
            ok &= ganz <= b.hi
        out.append(min(P_MAX, max(P_MIN, float(ok.mean()))))
    return out


def kosten_je_anteil(preis: float, spread: float) -> float:
    """Kaufpreis (Preis + halber Spread) plus Taker-Gebühr 0,05*q*(1-q), je Anteil."""
    q = preis + spread / 2.0
    return q + FEE_RATE * q * (1.0 - q)


def kandidaten(p_modell: float, preis_ja: float, spread: float) -> list[dict]:
    """Ja- und Nein-Seite eines Buckets mit Kosten und Kante; ungültig (Kosten >= 1) entfällt."""
    out = []
    for seite, p_seite, preis in (("ja", p_modell, preis_ja), ("nein", 1.0 - p_modell, 1.0 - preis_ja)):
        c = kosten_je_anteil(preis, spread)
        if c >= 1.0 or preis < 0.0:
            continue
        out.append({"seite": seite, "kosten": c, "kante": p_seite - c, "p_seite": p_seite, "preis": preis})
    return out


def waehle_wetten(liste: list[dict], schwelle: float, seiten=("ja", "nein"), max_je_event: int = 2) -> list[dict]:
    ok = [k for k in liste if k["seite"] in seiten and k["kante"] >= schwelle]
    ok.sort(key=lambda k: (-k["kante"], k["bucket_idx"], k["seite"]))
    return ok[:max_je_event]


def wett_ergebnis(kosten: float, gewonnen: bool, einsatz: float = EINSATZ) -> float:
    """Einsatz inklusive Gebühr: Anteile = einsatz/kosten, Auszahlung 1 $ je Anteil."""
    return einsatz / kosten - einsatz if gewonnen else -einsatz


def brier(p: list[float], y: list[int]) -> float:
    return sum((a - b) ** 2 for a, b in zip(p, y)) / len(p)


def kalibrierung(p: list[float], y: list[int], stufen: int = 10) -> list[tuple[float, float, int, float, float]]:
    """Je Stufe [i/stufen, (i+1)/stufen): (von, bis, n, mittleres p, Häufigkeit)."""
    out = []
    for i in range(stufen):
        lo, hi = i / stufen, (i + 1) / stufen
        idx = [k for k, a in enumerate(p) if lo <= a < hi or (i == stufen - 1 and a == 1.0)]
        if idx:
            out.append((lo, hi, len(idx), sum(p[k] for k in idx) / len(idx), sum(y[k] for k in idx) / len(idx)))
        else:
            out.append((lo, hi, 0, float("nan"), float("nan")))
    return out
