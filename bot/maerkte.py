"""Holt alle aktiven Polymarket-Wettermärkte (Temperatur + Niederschlag) und
schreibt Stadt, Station, Datum, Art, Buckets, Preise und Spread nach
daten/maerkte.csv. Nur lesend, keine Wallet, keine Schlüssel.

Aufruf:  python -m bot.maerkte [--ausgabe daten/maerkte.csv] [--anhaengen]
"""
import argparse
import csv
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

from bot.buckets import parse_bucket
from bot.netz import get_json, post_json
from bot.stationen import STATIONEN

GAMMA_KEYSET = "https://gamma-api.polymarket.com/events/keyset"
CLOB_BOOKS = "https://clob.polymarket.com/books"
TEMP_SLUG = re.compile(r"^(highest|lowest)-temperature-in-(.+?)-on-")
REGEN_SLUG = re.compile(r"^where-will-it-rain-on-")
ART = {"highest": "hoechst", "lowest": "tiefst"}
BOOK_CHUNK = 100

SPALTEN = [
    "abruf_utc", "event_slug", "markt_id", "stadt", "station", "quelle", "art", "datum",
    "einheit", "rundung", "bucket", "bucket_lo", "bucket_hi", "token_yes", "preis_mitte",
    "bid", "ask", "spread", "ask_groesse", "liquiditaet", "volumen", "tick", "min_groesse",
    "fee_rate", "ende_utc",
]


def hole_events() -> list[dict]:
    """Alle aktiven, nicht geschlossenen Events mit Tag 'weather' (Keyset-Paginierung)."""
    events, cursor = [], None
    while True:
        p = {"tag_slug": "weather", "active": "true", "closed": "false", "limit": 100}
        if cursor:
            p["after_cursor"] = cursor
        j = get_json(GAMMA_KEYSET, p)
        events += j["events"]
        cursor = j.get("next_cursor")
        if not cursor or not j["events"]:
            return events


def _zahl(x, default=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def hole_buecher(tokens: list[str]) -> dict[str, dict]:
    """Bestes Bid/Ask und Größe je Token über CLOB /books (Batch)."""
    out = {}
    for i in range(0, len(tokens), BOOK_CHUNK):
        teil = tokens[i:i + BOOK_CHUNK]
        for b in post_json(CLOB_BOOKS, [{"token_id": t} for t in teil]):
            bids = [(float(x["price"]), float(x["size"])) for x in b.get("bids", [])]
            asks = [(float(x["price"]), float(x["size"])) for x in b.get("asks", [])]
            bid = max(bids)[0] if bids else None
            ask_p = min(asks) if asks else None
            out[b["asset_id"]] = {
                "bid": bid,
                "ask": ask_p[0] if ask_p else None,
                "ask_groesse": ask_p[1] if ask_p else None,
                "tick": _zahl(b.get("tick_size")),
                "min_groesse": _zahl(b.get("min_order_size")),
            }
    return out


def _event_kopf(ev: dict):
    """(art, stadt_slug, stadt_name_fuer_csv, station, quelle, rundung) oder None."""
    slug = ev["slug"]
    m = TEMP_SLUG.match(slug)
    if m:
        stadt = m.group(2)
        st = STATIONEN.get(stadt)
        if st is None:
            return ART[m.group(1)], stadt, "UNBEKANNT", "", ""
        return ART[m.group(1)], stadt, st.icao, st.quelle, st.rundung
    if REGEN_SLUG.match(slug):
        return "niederschlag", None, "NWS-CLI", "NWS", "-"
    return None


def _datum(ev: dict) -> str:
    return ev.get("eventDate") or ev["endDate"][:10]


def zeilen_aus_events(events: list[dict], abruf: datetime, buecher: dict | None, min_datum: str) -> list[dict]:
    zeilen = []
    for ev in events:
        kopf = _event_kopf(ev)
        if kopf is None or _datum(ev) < min_datum:
            continue
        art, stadt, station, quelle, rundung = kopf
        for m in ev.get("markets", []):
            try:
                token = json.loads(m["clobTokenIds"])[0]
                preise = json.loads(m["outcomePrices"])
            except (KeyError, ValueError, TypeError, IndexError):
                continue
            titel = m.get("groupItemTitle") or ""
            if art == "niederschlag":
                einheit, lo, hi, bucket_text = "in", 0.01, "", "Regen >= 0.01 in"
                stadt_name = titel
            else:
                try:
                    b = parse_bucket(titel)
                except ValueError:
                    continue
                einheit, lo, hi, bucket_text = b.einheit, b.lo, b.hi, titel
                stadt_name = stadt
            buch = (buecher or {}).get(token)
            if buch is not None:  # CLOB-Buch hat Vorrang; leere Seite bleibt leer
                bid, ask = buch["bid"], buch["ask"]
            else:  # Rückfall auf Gamma-Werte, falls das Buch fehlt
                buch = {}
                bid, ask = _zahl(m.get("bestBid")), _zahl(m.get("bestAsk"))
            spread = round(ask - bid, 4) if bid is not None and ask is not None else None
            fee = (m.get("feeSchedule") or {}).get("rate")
            zeilen.append({
                "abruf_utc": abruf.isoformat(timespec="seconds"),
                "event_slug": ev["slug"], "markt_id": m.get("conditionId", ""),
                "stadt": stadt_name, "station": station, "quelle": quelle, "art": art,
                "datum": _datum(ev), "einheit": einheit, "rundung": rundung,
                "bucket": bucket_text, "bucket_lo": "" if lo is None else lo,
                "bucket_hi": "" if hi is None else hi, "token_yes": token,
                "preis_mitte": _zahl(preise[0]), "bid": bid, "ask": ask, "spread": spread,
                "ask_groesse": buch.get("ask_groesse"),
                "liquiditaet": _zahl(m.get("liquidityNum")), "volumen": _zahl(m.get("volumeNum")),
                "tick": buch.get("tick", _zahl(m.get("orderPriceMinTickSize"))),
                "min_groesse": buch.get("min_groesse", _zahl(m.get("orderMinSize"))),
                "fee_rate": fee, "ende_utc": ev["endDate"],
            })
    return zeilen


def schreibe_csv(zeilen: list[dict], pfad: Path, anhaengen: bool = False) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    neu = not (anhaengen and pfad.exists())
    with open(pfad, "a" if anhaengen else "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=SPALTEN)
        if neu:
            w.writeheader()
        for z in zeilen:
            w.writerow({k: ("" if z[k] is None else z[k]) for k in SPALTEN})


def lade_csv(pfad: Path) -> list[dict]:
    with open(pfad, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ausgabe", default="daten/maerkte.csv")
    ap.add_argument("--anhaengen", action="store_true")
    a = ap.parse_args(argv)
    jetzt = datetime.now(timezone.utc)
    min_datum = (jetzt - timedelta(days=2)).date().isoformat()  # alte, hängende Events ignorieren
    events = hole_events()
    kandidaten = [e for e in events if _event_kopf(e) and _datum(e) >= min_datum]
    tokens = []
    for e in kandidaten:
        for m in e.get("markets", []):
            try:
                tokens.append(json.loads(m["clobTokenIds"])[0])
            except (KeyError, ValueError, TypeError, IndexError):
                pass
    buecher = hole_buecher(tokens)
    zeilen = zeilen_aus_events(kandidaten, jetzt, buecher, min_datum)
    schreibe_csv(zeilen, Path(a.ausgabe), a.anhaengen)
    print(f"{len(events)} Wetter-Events, {len(kandidaten)} relevant, {len(zeilen)} Buckets -> {a.ausgabe}")


if __name__ == "__main__":
    main()
