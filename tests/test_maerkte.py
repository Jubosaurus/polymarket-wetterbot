import csv
import json
from datetime import datetime, timezone

from bot.maerkte import SPALTEN, _event_kopf, lade_csv, schreibe_csv, zeilen_aus_events

JETZT = datetime(2026, 10, 13, 12, 0, tzinfo=timezone.utc)


def _markt(titel, yes="0.4", bid="0.38", ask="0.42"):
    return {"groupItemTitle": titel, "clobTokenIds": json.dumps(["tok-" + titel, "no"]),
            "outcomePrices": json.dumps([yes, "0.6"]), "conditionId": "0x" + titel,
            "bestBid": bid, "bestAsk": ask, "liquidityNum": 100.0, "volumeNum": 5.0,
            "orderPriceMinTickSize": 0.01, "orderMinSize": 5, "feeSchedule": {"rate": 0.05}}


def _event(slug, titel, datum="2026-10-14"):
    return {"slug": slug, "eventDate": datum, "endDate": datum + "T12:00:00Z",
            "markets": [_markt(t) for t in titel]}


def test_temperatur_event_wird_zu_zeilen():
    ev = _event("highest-temperature-in-nyc-on-october-14-2026", ["67°F or below", "68-69°F", "70°F or higher"])
    z = zeilen_aus_events([ev], JETZT, None, "2026-10-11")
    assert [r["bucket"] for r in z] == ["67°F or below", "68-69°F", "70°F or higher"]
    r = z[0]
    assert (r["stadt"], r["station"], r["art"], r["einheit"], r["rundung"]) == ("nyc", "KLGA", "hoechst", "F", "kaufm")
    assert r["bucket_lo"] == "" and r["bucket_hi"] == 67
    assert r["spread"] == 0.04 and r["fee_rate"] == 0.05  # Gamma-Rückfall ohne CLOB-Buch


def test_clob_buch_hat_vorrang_und_leere_seite_bleibt_leer():
    ev = _event("lowest-temperature-in-london-on-october-14-2026", ["9°C"])
    buch = {"tok-9°C": {"bid": None, "ask": 0.05, "ask_groesse": 12.0, "tick": 0.001, "min_groesse": 5.0}}
    r = zeilen_aus_events([ev], JETZT, buch, "2026-10-11")[0]
    assert r["bid"] is None and r["ask"] == 0.05 and r["spread"] is None and r["art"] == "tiefst"
    assert r["rundung"] == "kaufm" and r["tick"] == 0.001


def test_hong_kong_schneidet_ab():
    ev = _event("highest-temperature-in-hong-kong-on-october-14-2026", ["30°C"])
    assert zeilen_aus_events([ev], JETZT, None, "2026-10-11")[0]["rundung"] == "abschneiden"


def test_alte_events_und_fremde_maerkte_werden_ignoriert():
    alt = _event("highest-temperature-in-nyc-on-may-20-2026", ["70°F"], datum="2026-05-20")
    fremd = _event("measles-cases-in-us-in-2026", ["10"])
    assert zeilen_aus_events([alt, fremd], JETZT, None, "2026-10-11") == []
    assert _event_kopf(fremd) is None


def test_unbekannte_stadt_wird_markiert():
    ev = _event("highest-temperature-in-atlantis-on-october-14-2026", ["20°C"])
    assert zeilen_aus_events([ev], JETZT, None, "2026-10-11")[0]["station"] == "UNBEKANNT"


def test_regen_event():
    ev = {"slug": "where-will-it-rain-on-october-14-2026", "eventDate": "2026-10-14",
          "endDate": "2026-10-15T18:00:00Z", "markets": [_markt("New York, NY")]}
    r = zeilen_aus_events([ev], JETZT, None, "2026-10-11")[0]
    assert (r["art"], r["stadt"], r["einheit"], r["bucket_lo"]) == ("niederschlag", "New York, NY", "in", 0.01)


def test_ungueltiger_bucket_wird_uebersprungen():
    ev = _event("highest-temperature-in-nyc-on-october-14-2026", ["kaputt", "70°F"])
    assert [r["bucket"] for r in zeilen_aus_events([ev], JETZT, None, "2026-10-11")] == ["70°F"]


def test_csv_roundtrip_und_anhaengen(tmp_path):
    ev = _event("highest-temperature-in-nyc-on-october-14-2026", ["70°F"])
    z = zeilen_aus_events([ev], JETZT, None, "2026-10-11")
    p = tmp_path / "m.csv"
    schreibe_csv(z, p)
    schreibe_csv(z, p, anhaengen=True)
    assert len(lade_csv(p)) == 2
    with open(p, newline="", encoding="utf-8") as f:
        assert next(csv.reader(f)) == SPALTEN
    schreibe_csv(z, p)  # ohne --anhaengen wird überschrieben
    assert len(lade_csv(p)) == 1
