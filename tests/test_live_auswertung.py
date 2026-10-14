import csv
import gzip
import json
from collections import defaultdict

import pytest

from auswertungen import live_auswertung as la

SLUG = "highest-temperature-in-london-on-october-16-2026"
STAMM_SPALTEN = ["idx", "gesehen_utc", "markt_id", "token_yes", "event_slug", "stadt", "station", "quelle", "art", "datum", "einheit",
                 "rundung", "bucket", "bucket_lo", "bucket_hi", "tick", "min_groesse", "fees_aktiv", "fee_typ", "fee_rate",
                 "fee_exponent", "fee_nur_taker", "fee_rebate", "ende_utc"]
BUCKETS = ["14°C or below", "15°C", "16°C or higher"]


def schreibe(pfad, spalten, zeilen):
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(pfad, "wt", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=spalten)
        w.writeheader()
        w.writerows(zeilen)


def stamm_zeilen(station="EGLC", exponent="1"):
    return [{"idx": str(i), "gesehen_utc": "2026-10-14T10:00:00Z", "markt_id": f"m{i}", "token_yes": f"t{i}", "event_slug": SLUG,
             "stadt": "london", "station": station, "quelle": "NOAA", "art": "hoechst", "datum": "2026-10-16", "einheit": "C",
             "rundung": "kaufm", "bucket": b, "bucket_lo": "", "bucket_hi": "", "tick": "0.001", "min_groesse": "5.0",
             "fees_aktiv": "True", "fee_typ": "weather_fees", "fee_rate": "0.05", "fee_exponent": exponent, "fee_nur_taker": "True",
             "fee_rebate": "0.25", "ende_utc": "2026-10-16T12:00:00Z"} for i, b in enumerate(BUCKETS)]


def buch(werte):
    """werte: je Bucket (bid, ask, bid_groesse, ask_groesse)."""
    return [{"idx": str(i), "bid": b, "ask": a, "bid_groesse": bg, "ask_groesse": ag, "letzter_preis": "", "preis_mitte": "", "spread": ""}
            for i, (b, a, bg, ag) in enumerate(werte)]


BUCH_SPALTEN = ["idx", "bid", "ask", "bid_groesse", "ask_groesse", "letzter_preis", "preis_mitte", "spread"]
ENS_SPALTEN = ["abruf_utc", "empfangen_utc", "stadt", "icao", "modell", "modell_lauf_utc", "lauf_details", "lauf_sicher", "datum",
               "art", "vorlauf_h", "n_member", "ausgeschlossen", "werte_c"]


def ens(modell, empfangen, werte):
    return {"abruf_utc": empfangen, "empfangen_utc": empfangen, "stadt": "london", "icao": "EGLC", "modell": modell,
            "modell_lauf_utc": "2026-10-14T06:00Z", "lauf_details": "", "lauf_sicher": "1", "datum": "2026-10-16", "art": "hoechst",
            "vorlauf_h": "40", "n_member": str(len(werte)), "ausgeschlossen": "0", "werte_c": " ".join(f"{w:.1f}" for w in werte)}


@pytest.fixture
def daten(tmp_path):
    root = tmp_path / "daten"
    tag = root / "2026-10-14"
    schreibe(tag / "maerkte_stamm_1000.csv.gz", STAMM_SPALTEN, stamm_zeilen())
    # Td (Vorlauf 2) = 14.10. 18:00 BST = 17:00 UTC. Lauf 16:37 liegt davor (darf nicht genutzt werden), 17:07 danach.
    schreibe(tag / "maerkte_1637.csv.gz", BUCH_SPALTEN, buch([("0.01", "0.02", "999", "999"), ("0.01", "0.02", "999", "999"), ("0.01", "0.02", "999", "999")]))
    schreibe(tag / "maerkte_1707.csv.gz", BUCH_SPALTEN, buch([("0.05", "0.08", "500", "500"), ("0.20", "0.30", "500", "500"), ("0.60", "0.65", "100", "100")]))
    # Mitglieder: um 15 °C; ein späterer Empfang (17:30, nach dem Lauf 17:07) mit 20 °C darf nicht eingehen
    werte = [14.8, 15.0, 15.0, 15.1, 15.2, 14.9, 15.0, 15.1, 15.0, 15.2]
    schreibe(tag / "ensemble_1000.csv.gz", ENS_SPALTEN, [ens("ecmwf_ifs025", "2026-10-14T10:05:00Z", werte),
                                                           ens("gfs025", "2026-10-14T10:06:00Z", werte),
                                                           ens("gfs025", "2026-10-14T17:30:00Z", [20.0] * 10)])
    schreibe(root / "2026-10-17" / "aufloesung.csv.gz", ["erfasst_utc", "event_slug", "stadt", "art", "datum", "icao", "einheit", "gewinner_bucket",
                                                          "messwert", "messquelle", "n_beobachtungen", "treffer", "bemerkung"],
             [{"erfasst_utc": "2026-10-17T07:00:00Z", "event_slug": SLUG, "stadt": "london", "art": "highest", "datum": "2026-10-16",
               "icao": "EGLC", "einheit": "C", "gewinner_bucket": "15°C", "messwert": "15", "messquelle": "METAR", "n_beobachtungen": "48",
               "treffer": "1", "bemerkung": ""}])
    bias = tmp_path / "bias.json"
    bias.write_text(json.dumps({"bias": {"EGLC|V2|hoechst": {"bias": 0.0}, "EGLC|V1|hoechst": {"bias": 0.0}}}), encoding="utf-8")
    return la.Daten(root, bias)


def test_entscheidung_nimmt_ersten_lauf_nach_td_und_kein_spaeteres_ensemble(daten):
    z = defaultdict(int)
    e = la.entscheidung(daten, SLUG, daten.events[SLUG], 2, z)
    assert e is not None and e["snap"] == la.datetime(2026, 10, 14, 17, 7, tzinfo=la.UTC).timestamp()
    # Mitglieder um 15 °C (kaufmännisch gerundet: 15); die 20 °C um 17:30 sind nach dem Lauf empfangen worden und zählen nicht
    p = {b["titel"]: b["p"] for b in e["buckets"]}
    assert p["15°C"] == pytest.approx(0.995) and p["16°C or higher"] == pytest.approx(la.rr.P_MIN)
    assert e["buckets"][1]["bid"] == 0.20  # Buch des Laufs 17:07, nicht das vom Lauf 16:37
    assert e["modelle"] == ["ecmwf_ifs025", "gfs025"]


def test_luecke_wenn_kein_lauf_innerhalb_von_60_minuten(daten):
    # Vorlauf 1: Td = 15.10. 17:00 UTC; es gibt keinen späteren Lauf
    z = defaultdict(int)
    assert la.entscheidung(daten, SLUG, daten.events[SLUG], 1, z) is None and z["luecke_v1"] == 1


def test_ohne_bias_station_wird_gezaehlt(daten, tmp_path):
    bias = tmp_path / "b2.json"
    bias.write_text(json.dumps({"bias": {}}), encoding="utf-8")
    d = la.Daten(daten.daten, bias)
    z = defaultdict(int)
    assert la.entscheidung(d, SLUG, d.events[SLUG], 2, z) is None and z["ohne_bias_oder_station_v2"] == 1


def test_bias_verschiebt_die_wahrscheinlichkeit(daten, tmp_path):
    bias = tmp_path / "b3.json"
    bias.write_text(json.dumps({"bias": {"EGLC|V2|hoechst": {"bias": 1.0}}}), encoding="utf-8")
    d = la.Daten(daten.daten, bias)
    e = la.entscheidung(d, SLUG, d.events[SLUG], 2, defaultdict(int))
    # 15 °C + 1 = 16 °C: Masse wandert in "16°C or higher"
    assert {b["titel"]: b["p"] for b in e["buckets"]}["16°C or higher"] == pytest.approx(0.995)


def test_nein_ask_ist_eins_minus_bid_mit_gebuehr_und_tiefe(daten):
    z = defaultdict(int)
    e = la.entscheidung(daten, SLUG, daten.events[SLUG], 2, z)
    nein = la.wetten_aus(e, "nein", z)
    w = next(x for x in nein if x["titel"] == "16°C or higher")
    assert w["q"] == pytest.approx(0.40)  # 1 - Bid 0,60
    assert w["kosten"] == pytest.approx(0.40 + 0.05 * 0.40 * 0.60)
    assert w["anteile"] == pytest.approx(10 / w["kosten"]) and w["kante"] == pytest.approx(0.995 - w["kosten"])
    # Tiefe 100 Anteile reicht für ca. 24; mit Tiefe 10 entfällt die Wette ersatzlos
    e["buckets"][2]["bid_groesse"] = 10.0
    z2 = defaultdict(int)
    assert all(x["titel"] != "16°C or higher" for x in la.wetten_aus(e, "nein", z2)) and z2["ohne_tiefe_nein_v2"] >= 1


def test_ja_nutzt_ask_und_aufloesung(daten):
    z = defaultdict(int)
    e = la.entscheidung(daten, SLUG, daten.events[SLUG], 2, z)
    ja = la.wetten_aus(e, "ja", z)
    w = next(x for x in ja if x["titel"] == "15°C")
    assert w["q"] == pytest.approx(0.30) and w["tiefe"] == 500
    titel = {SLUG: {b["titel"] for b in e["buckets"]}}
    la.lose_auf(w, daten.aufl, titel)
    assert w["gewinnt"] is True and w["gewinn"] == pytest.approx(w["anteile"] - 10)
    n = {"titel": "16°C or higher", "seite": "nein", "slug": SLUG, "anteile": 25.0}
    la.lose_auf(n, daten.aufl, titel)
    assert n["gewinnt"] is True and n["gewinn"] == pytest.approx(15.0)
    # unbekannter Gewinner (nicht unter den Buckets des Events): offen lassen
    la.lose_auf(n, {SLUG: "99°C"}, titel)
    assert n["gewinn"] is None


def test_waehle_hoechstens_zwei_groesste_kanten():
    k = [{"kante": x, "bucket_idx": i} for i, x in enumerate([0.30, 0.12, 0.25, 0.05])]
    assert [x["kante"] for x in la.waehle(k)] == [0.30, 0.25]


def test_zaehlstand_zeigt_keine_gewinne_und_auswerten_wartet_auf_200(daten):
    zaehler, ents, wetten = la.berechne(daten)
    text = la.zaehlstand(zaehler, wetten)
    assert "Gewinn" not in text and "Quote" not in text and "Brier" not in text
    assert not la.bereit(wetten)  # weniger als 200 Hauptwetten


def test_urteil_kriterien():
    gut = [{"gewinn": 1.0}] * 100 + [{"gewinn": 0.5}] * 100
    assert la.urteil(gut)["bestaetigt"]
    # zweite Hälfte negativ -> nicht bestätigt, auch wenn der Gesamtgewinn positiv ist
    h2 = [{"gewinn": 3.0}] * 100 + [{"gewinn": -1.0}] * 99 + [{"gewinn": -1.0}]
    u = la.urteil(h2)
    assert u["gesamt"]["summe"] > 0 and not u["kriterien"]["haelfte2_positiv"] and not u["bestaetigt"]
    # Gewinn nur durch 3 Ausreißer -> ohne die 3 besten negativ
    ausr = [{"gewinn": 100.0}] * 3 + [{"gewinn": -1.0}] * 197
    assert not la.urteil(ausr)["kriterien"]["ohne_top3_positiv"]


def test_ensemble_vor_einem_spaeteren_lauf_kein_blick_in_die_zukunft(daten):
    from datetime import datetime, timezone
    vor = datetime(2026, 10, 14, 10, 5, 30, tzinfo=timezone.utc)
    werte, modelle = la.pool_mitglieder(daten.ens, "london", "hoechst", "2026-10-16", vor)
    assert modelle == ["ecmwf_ifs025"] and len(werte) == 10  # gfs025 wurde erst um 10:06 empfangen


def test_blind_nein_auf_billige_buckets_ohne_modell(daten):
    z = defaultdict(int)
    e = la.entscheidung(daten, SLUG, daten.events[SLUG], 2, z)
    ws = la.blind_nein(e, z)
    assert [w["titel"] for w in ws] == ["14°C or below"]  # nur Ja-Ask 0,08 <= 0,10
    w = ws[0]
    assert w["q"] == pytest.approx(0.95) and w["kosten"] == pytest.approx(0.95 + 0.05 * 0.95 * 0.05)
    la.lose_auf(w, daten.aufl, {SLUG: {b["titel"] for b in e["buckets"]}})
    assert w["gewinnt"] is True and w["gewinn"] == pytest.approx(w["anteile"] - 10)


def test_aufweitung_nur_in_der_vergleichsvariante():
    b = [la.parse_bucket("13°C or below")]
    assert la.bucket_p([14.0, 16.0], "C", 0.0, b, "kaufm")[0] == pytest.approx(la.rr.P_MIN)
    assert la.bucket_p([14.0, 16.0], "C", 0.0, b, "kaufm", sd_res=2.0)[0] == pytest.approx(0.5)  # 14/16 -> 13/17
    # schon breiter als die Residuenstreuung: unverändert
    assert la.bucket_p([14.0, 16.0], "C", 0.0, b, "kaufm", sd_res=0.5)[0] == pytest.approx(la.rr.P_MIN)


def test_nur_abrufe_ab_koordinatenkorrektur(daten):
    from datetime import datetime, timezone
    bis = datetime(2026, 10, 14, 17, 7, tzinfo=timezone.utc)
    ab = datetime(2026, 10, 14, 10, 5, 30, tzinfo=timezone.utc)
    werte, modelle = la.pool_mitglieder(daten.ens, "london", "hoechst", "2026-10-16", bis, ab)
    assert modelle == ["gfs025"]  # ecmwf wurde vor der Korrektur abgerufen
    d = la.Daten(daten.daten, daten.daten.parent / "bias.json", ab=datetime(2026, 10, 15, tzinfo=timezone.utc))
    z = defaultdict(int)
    assert la.entscheidung(d, SLUG, d.events[SLUG], 2, z) is None and z["vor_koordinatenkorrektur_v2"] == 1


def test_zieltag_kommt_aus_dem_slug_nicht_aus_dem_stamm(daten):
    """Codex-Review 2026-10-14: Das Protokoll nimmt bei fehlendem eventDate endDate; das kann einen Tag später liegen."""
    zeilen = stamm_zeilen()
    for z in zeilen:
        z["datum"] = "2026-10-17"  # verschoben, der Slug sagt 16. Oktober
    schreibe(daten.daten / "2026-10-14" / "maerkte_stamm_1000.csv.gz", STAMM_SPALTEN, zeilen)
    d = la.Daten(daten.daten, daten.daten.parent / "bias.json")
    ev = d.events[SLUG]
    assert ev["datum"] == "2026-10-16" and ev["stamm_datum"] == "2026-10-17"
    e = la.entscheidung(d, SLUG, ev, 2, defaultdict(int))
    # Td und Ensemble gehören zum 16.: gleiche Entscheidung wie ohne Verschiebung
    assert e is not None and e["datum"] == "2026-10-16" and e["snap"] == la.datetime(2026, 10, 14, 17, 7, tzinfo=la.UTC).timestamp()
    zaehler, _, _ = la.berechne(d)
    assert zaehler["zieltag_weicht_vom_stamm_ab"] == 1
