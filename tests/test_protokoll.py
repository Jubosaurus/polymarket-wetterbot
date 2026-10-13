import json
from datetime import datetime, timezone

import pytest

import bot.protokoll as pk
from bot import aufloesung, ensemble, speicher


def _markt(titel, yes="0.4", bid="0.38", ask="0.42", fee="0.05"):
    return {"groupItemTitle": titel, "clobTokenIds": json.dumps(["tok-" + titel, "no"]),
            "outcomePrices": json.dumps([yes, "0.6"]), "conditionId": "0x" + titel,
            "bestBid": bid, "bestAsk": ask, "liquidityNum": 100.0, "volumeNum": 5.0,
            "orderPriceMinTickSize": 0.01, "orderMinSize": 5, "feesEnabled": True, "feeType": "weather_fees",
            "feeSchedule": {"rate": fee, "exponent": 1, "takerOnly": True, "rebateRate": 0.25}}


def _event(slug="highest-temperature-in-nyc-on-october-14-2026", titel=("66°F or below", "68-69°F", "70°F or higher"),
           datum="2026-10-14", fee="0.05"):
    return {"slug": slug, "eventDate": datum, "endDate": datum + "T12:00:00Z",
            "markets": [_markt(t, fee=fee) for t in titel]}


def _stamm(tag):
    out = []
    for f in sorted(tag.glob("maerkte_stamm_*.csv.gz")):
        out += speicher.lies_csv_gz(f)
    return out


def _ens_antwort(wert=21.0):
    zeiten = [f"2026-10-{14 + d}T{h:02d}:00" for d in range(3) for h in range(24)]
    haupt = [wert + (5 if h == 14 else 0) for _ in range(3) for h in range(24)]
    h = {"time": zeiten}
    for modell_key in ("ecmwf_ifs025_ensemble", "ncep_gefs025"):
        h[f"temperature_2m_{modell_key}"] = haupt
        h[f"temperature_2m_member01_{modell_key}"] = haupt
    return {"hourly": h}


class FakeApi:
    def __init__(self, events=None, laeufe=None, ens_fehler=False):
        self._events = events if events is not None else [_event()]
        self.laeufe = laeufe or {"ecmwf_ifs025": "2026-10-14T06:00Z", "gfs025": "2026-10-14T06:00Z"}
        self.ens_aufrufe = []
        self.ens_fehler = ens_fehler
        self.reif = True
        self.einzel = {}
        self.ens_leer = False
        self.ens_tageslimit = False
        self.geschl = []

    def events(self):
        return self._events

    def buecher(self, tokens):
        return {t: {"bid": 0.3, "bid_groesse": 10.0, "ask": 0.35, "ask_groesse": 20.0, "letzter_preis": 0.32,
                    "buch_zeit_ms": "1", "tick": 0.01, "min_groesse": 5.0} for t in tokens}

    def modellinfo(self, jetzt):
        return {m: {"lauf": t, "details": f"ds@{t}", "reif": self.reif} for m, t in self.laeufe.items()}

    def event(self, slug):
        return self.einzel.get(slug)

    def ensemble(self, station, modelle):
        if self.ens_fehler:
            raise RuntimeError("429")
        if self.ens_tageslimit:
            raise pk.netz.TageslimitFehler("Daily API request limit exceeded")
        self.ens_aufrufe.append((station.icao, tuple(modelle)))
        if self.ens_leer:
            a = _ens_antwort()
            for k in a["hourly"]:
                if k != "time":
                    a["hourly"][k] = [None] * len(a["hourly"]["time"])
            return a
        return _ens_antwort()

    def geschlossene(self, von, bis):
        return self.geschl

    def obs(self, icao, von, bis):
        return []

    def hko(self, art, j, m):
        return {}


@pytest.fixture(autouse=True)
def schnell(monkeypatch):
    monkeypatch.setattr(pk.time, "sleep", lambda s: None)
    monkeypatch.setattr(pk, "git_pack_mb", lambda: 1.0)
    monkeypatch.setattr(pk, "STATIONEN", {"nyc": pk.STATIONEN["nyc"], "london": pk.STATIONEN["london"]})
    monkeypatch.setattr(ensemble, "STATIONEN", pk.STATIONEN)


JETZT = datetime(2026, 10, 14, 12, 30, tzinfo=timezone.utc)


def test_lauf_schreibt_snapshot_stamm_ensemble_prob_und_log(tmp_path):
    api = FakeApi()
    assert pk.lauf(api, tmp_path, JETZT) == 0
    tag = tmp_path / "2026-10-14"
    snap = speicher.lies_csv_gz(tag / "maerkte_1230.csv.gz")
    assert len(snap) == 3 and snap[0]["bid_groesse"] == "10.0" and snap[0]["letzter_preis"] == "0.32"
    stamm = _stamm(tag)
    assert len(stamm) == 3 and stamm[0]["fee_rate"] == "0.05" and stamm[0]["fee_exponent"] == "1"
    assert stamm[0]["fee_nur_taker"] == "True" and stamm[0]["fee_typ"] == "weather_fees"
    ens = speicher.lies_csv_gz(tag / "ensemble_1230.csv.gz")
    assert {z["modell"] for z in ens} == {"ecmwf_ifs025", "gfs025"}
    z = next(z for z in ens if z["modell"] == "gfs025" and z["art"] == "hoechst" and z["datum"] == "2026-10-14")
    assert z["n_member"] == "2" and z["werte_c"] == "26.0 26.0" and float(z["vorlauf_h"]) == -2.0
    prob = speicher.lies_csv_gz(tag / "wahrscheinlichkeiten_1230.csv.gz")
    # alle 4 Mitglieder 26 °C = 78,8 °F -> 79 °F -> Bucket "70°F or higher"
    stamm_bucket = {int(r["idx"]): r["bucket"] for r in stamm}
    p = {stamm_bucket[int(r["idx"])]: float(r["p_modell"]) for r in prob}
    assert p == {"66°F or below": 0.0, "68-69°F": 0.0, "70°F or higher": 1.0}
    assert prob[0]["n_member"] == "4" and "ecmwf_ifs025@2026-10-14T06:00Z" in prob[0]["laeufe"]
    log = speicher.lies_csv(tag / "laufzeit.csv")
    assert log[0]["status"] == "OK" and log[0]["ensemble_modelle_neu"] == "ecmwf_ifs025+gfs025"
    assert int(log[0]["om_anfragen"]) == 2 and log[0]["daten_mb"]
    assert json.loads((tmp_path / "zustand.json").read_text())["modelle"]["gfs025"] == "2026-10-14T06:00Z"


def test_ensemble_nur_bei_neuem_modelllauf(tmp_path):
    api = FakeApi()
    pk.lauf(api, tmp_path, JETZT)
    n = len(api.ens_aufrufe)
    pk.lauf(api, tmp_path, datetime(2026, 10, 14, 13, 0, tzinfo=timezone.utc))
    assert len(api.ens_aufrufe) == n  # kein neuer Lauf, keine Abfrage
    api.laeufe["gfs025"] = "2026-10-14T12:00Z"
    pk.lauf(api, tmp_path, datetime(2026, 10, 14, 13, 30, tzinfo=timezone.utc))
    assert {m for _, m in api.ens_aufrufe[n:]} == {("gfs025",)}  # nur das Modell mit neuem Lauf
    log = speicher.lies_csv(tmp_path / "2026-10-14" / "laufzeit.csv")
    assert [int(z["om_anfragen"]) for z in log] == [2, 0, 2]
    assert [int(z["om_gewicht"]) for z in log] == [4, 0, 2]  # Gewicht = Summe angefragter Modelle
    assert int(log[2]["om_gewicht_heute"]) >= 4
    assert log[1]["luecke_min"] == "30.0" and log[2]["luecke_min"] == "30.0"


def test_stamm_aendert_sich_nur_bei_gebuehrenaenderung(tmp_path):
    pk.lauf(FakeApi(), tmp_path, JETZT)
    pk.lauf(FakeApi(), tmp_path, datetime(2026, 10, 14, 13, 0, tzinfo=timezone.utc))
    tag = tmp_path / "2026-10-14"
    assert len(_stamm(tag)) == 3
    pk.lauf(FakeApi(events=[_event(fee="0.07")]), tmp_path, datetime(2026, 10, 14, 13, 30, tzinfo=timezone.utc))
    stamm = _stamm(tag)
    assert len(stamm) == 6 and {z["fee_rate"] for z in stamm} == {"0.05", "0.07"}
    snap = speicher.lies_csv_gz(tag / "maerkte_1330.csv.gz")
    assert {int(z["idx"]) for z in snap} == {3, 4, 5}


def test_marktfehler_gibt_exit_1_und_log(tmp_path):
    api = FakeApi(events=[])
    assert pk.lauf(api, tmp_path, JETZT) == 1
    log = speicher.lies_csv(tmp_path / "2026-10-14" / "laufzeit.csv")
    assert log[0]["status"] == "FEHLER_MAERKTE" and "keine Marktzeilen" in log[0]["fehler"]


def test_ensemble_ausfall_aktualisiert_zustand_nicht(tmp_path):
    api = FakeApi(ens_fehler=True)
    assert pk.lauf(api, tmp_path, JETZT) == 0
    assert json.loads((tmp_path / "zustand.json").read_text())["modelle"] == {}
    log = speicher.lies_csv(tmp_path / "2026-10-14" / "laufzeit.csv")
    assert "unvollständig" in log[0]["fehler"] and log[0]["ensemble_stationen_ok"] == "0"


def test_om_tageslimit(tmp_path, monkeypatch):
    monkeypatch.setattr(pk, "OM_TAGESLIMIT", 0)
    api = FakeApi()
    pk.lauf(api, tmp_path, JETZT)
    assert api.ens_aufrufe == []


def test_vorlauf_stunden():
    # Lauf 06:00Z, Zieltag London 2026-10-14 beginnt 23:00Z am Vortag (BST) -> -7 h
    assert ensemble.vorlauf_stunden("2026-10-14T06:00Z", "2026-10-14", "Europe/London") == -7.0
    assert ensemble.vorlauf_stunden("2026-10-13T12:00Z", "2026-10-15", "UTC") == 36.0


def test_modell_zuordnung_einzelmodell_ohne_suffix():
    a = {"hourly": {"time": [f"2026-10-14T{h:02d}:00" for h in range(24)],
                    "temperature_2m": [float(h) for h in range(24)],
                    "temperature_2m_member01": [float(h) + 1 for h in range(24)]}}
    r = ensemble.tageswerte_je_modell(a, ["gfs025"])
    assert r["gfs025"]["2026-10-14"]["hoechst"] == [23.0, 24.0]


def test_juengster_lauf_je_modell_und_pooling():
    zeilen = [
        {"stadt": "nyc", "art": "hoechst", "datum": "d", "modell": "a", "modell_lauf_utc": "1", "werte_c": "10.0 10.0"},
        {"stadt": "nyc", "art": "hoechst", "datum": "d", "modell": "a", "modell_lauf_utc": "2", "werte_c": "20.0"},
        {"stadt": "nyc", "art": "hoechst", "datum": "d", "modell": "b", "modell_lauf_utc": "1", "werte_c": "30.0"},
    ]
    m = ensemble.juengste_member(zeilen)[("nyc", "hoechst", "d")]
    assert m["a"] == ("2", [20.0], "") and m["b"] == ("1", [30.0], "")


def _ev_geschlossen(slug, datum, gewinner, text="https://www.weather.gov/wrh/timeseries?site=KLGA"):
    return {"slug": slug, "endDate": datum + "T12:00:00Z", "resolutionSource": text,
            "markets": [{"groupItemTitle": t, "outcomePrices": json.dumps(["1" if t == gewinner else "0", "1"])}
                        for t in ("68-69°F", "70-71°F")]}


def test_aufloesung_treffer_abweichung_und_offen():
    from datetime import timedelta
    z0 = datetime(2026, 10, 13, 0, tzinfo=timezone.utc)
    obs = [(z0 + timedelta(hours=h + 4), 70.0) for h in range(24)]  # lokaler Tag 13.10. (EDT = UTC-4)
    ev_ok = _ev_geschlossen("highest-temperature-in-nyc-on-october-13-2026", "2026-10-13", "70-71°F")
    ev_ab = _ev_geschlossen("lowest-temperature-in-nyc-on-october-13-2026", "2026-10-13", "68-69°F")
    ev_offen = _ev_geschlossen("highest-temperature-in-nyc-on-october-12-2026", "2026-10-12", "70-71°F")
    ev_unentschieden = _ev_geschlossen("highest-temperature-in-nyc-on-october-11-2026", "2026-10-11", "x")
    rows = aufloesung.pruefe_events([ev_ok, ev_ab, ev_offen, ev_unentschieden], "t", set(),
                                    hole_obs=lambda i, v, b: obs, hole_hko=lambda *a: {})
    d = {r["event_slug"].split("-on-")[0] + r["datum"]: r for r in rows}
    assert d["highest-temperature-in-nyc2026-10-13"]["treffer"] == 1
    assert d["lowest-temperature-in-nyc2026-10-13"]["treffer"] == 0  # Abweichung markiert
    assert d["highest-temperature-in-nyc2026-10-12"].get("_offen")  # keine Beobachtungen
    assert len(rows) == 3  # unentschiedenes Event wird übersprungen
    assert aufloesung.pruefe_events([ev_ok], "t", {ev_ok["slug"]}, hole_obs=lambda *a: obs) == []


def test_aufloesung_hko_abschneiden():
    ev = {"slug": "highest-temperature-in-hong-kong-on-october-13-2026", "endDate": "2026-10-13T12:00:00Z",
          "markets": [{"groupItemTitle": "28°C", "outcomePrices": json.dumps(["1", "0"])}]}
    r = aufloesung.pruefe_events([ev], "t", set(), hole_hko=lambda art, j, m: {"2026-10-13": 28.9})[0]
    assert r["treffer"] == 1 and r["messwert"] == 28


def test_aufloesung_faellig():
    z = {}
    assert not pk.aufloesung_faellig(z, datetime(2026, 10, 14, 5, tzinfo=timezone.utc), False)
    assert pk.aufloesung_faellig(z, datetime(2026, 10, 14, 7, tzinfo=timezone.utc), False)
    z = {"aufloesung_letzte": "2026-10-14T07:00:00+00:00"}
    assert not pk.aufloesung_faellig(z, datetime(2026, 10, 14, 13, tzinfo=timezone.utc), False)
    assert pk.aufloesung_faellig(z, datetime(2026, 10, 14, 19, 30, tzinfo=timezone.utc), False)
    assert pk.aufloesung_faellig(z, datetime(2026, 10, 14, 8, tzinfo=timezone.utc), True)


def test_leere_ensemble_antwort_zaehlt_nicht_als_erfasst(tmp_path):
    api = FakeApi()
    api.ens_leer = True
    pk.lauf(api, tmp_path, JETZT)
    z = json.loads((tmp_path / "zustand.json").read_text())
    assert z["modelle"] == {} and sum(z["versuche"].values()) == 1  # nicht als erledigt verbucht, Versuch gezählt
    log = speicher.lies_csv(tmp_path / "2026-10-14" / "laufzeit.csv")
    assert log[0]["ensemble_stationen_ok"] == "0" and "leere oder unvollständige" in log[0]["fehler"]
    assert log[0]["status"] == "TEILFEHLER"
    assert not list((tmp_path / "2026-10-14").glob("ensemble_*"))  # nichts Verwertbares gespeichert


def test_unvollstaendiger_lauf_wird_wiederholt_dann_akzeptiert(tmp_path, monkeypatch):
    # 10 Stationen, bei einer fehlt die Antwort: 90 % -> erst nach 3 Versuchen als erledigt
    st = {f"s{i}": pk.STATIONEN["nyc"] for i in range(10)}
    monkeypatch.setattr(pk, "STATIONEN", st)
    api = FakeApi()
    original = api.ensemble
    zaehler = {"n": 0}

    def zehn(station, modelle):
        zaehler["n"] += 1
        if zaehler["n"] % 10 == 0:
            raise RuntimeError("HTTP 500")
        return original(station, modelle)

    api.ensemble = zehn
    for i in range(3):
        pk.lauf(api, tmp_path, datetime(2026, 10, 14, 12 + i, 0, tzinfo=timezone.utc))
        z = json.loads((tmp_path / "zustand.json").read_text())
        assert (z["modelle"] == {}) == (i < 2)
    assert z["versuche"] == {}


def test_tageslimit_pausiert_bis_mitternacht(tmp_path):
    api = FakeApi()
    api.ens_tageslimit = True
    pk.lauf(api, tmp_path, JETZT)
    z = json.loads((tmp_path / "zustand.json").read_text())
    assert z["om_gesperrt_bis"] == "2026-10-15T00:05:00Z" and z["modelle"] == {}
    api.ens_tageslimit = False
    pk.lauf(api, tmp_path, datetime(2026, 10, 14, 13, 0, tzinfo=timezone.utc))
    assert api.ens_aufrufe == []  # pausiert
    pk.lauf(api, tmp_path, datetime(2026, 10, 15, 0, 30, tzinfo=timezone.utc))
    assert api.ens_aufrufe  # nach Mitternacht wieder aktiv


def test_unreifer_lauf_ist_nicht_sicher(tmp_path):
    api = FakeApi()
    api.reif = False
    pk.lauf(api, tmp_path, JETZT)
    ens = speicher.lies_csv_gz(tmp_path / "2026-10-14" / "ensemble_1230.csv.gz")
    assert {z["lauf_sicher"] for z in ens} == {"0"} and ens[0]["lauf_details"].startswith("ds@")
    assert ens[0]["empfangen_utc"]
    prob = speicher.lies_csv_gz(tmp_path / "2026-10-14" / "wahrscheinlichkeiten_1230.csv.gz")
    assert prob[0]["verfuegbar_ab_utc"] == max(z["empfangen_utc"] for z in ens)  # Wahrscheinlichkeit erst ab Empfang verfügbar


def test_modellinfo_reife_und_icon_herkunft():
    jetzt = datetime(2026, 10, 13, 20, 30, tzinfo=timezone.utc)

    def t(h, m=0):
        return int(datetime(2026, 10, 13, h, m, tzinfo=timezone.utc).timestamp())

    metas = {
        "ecmwf_ifs025_ensemble": (t(12), t(20, 29)),  # vor 1 min verfügbar geworden: noch nicht reif
        "ncep_gefs025": (t(12), t(17)),
        "dwd_icon_eps": (t(12), t(16)),
        "dwd_icon_eu_eps": (t(18), t(20)),  # anderer Lauf als global
        "cmc_gem_geps": (t(12), t(18)),
    }

    def hole(url, params=None, **kw):
        ds = url.split("/data/")[1].split("/")[0]
        return {"last_run_initialisation_time": metas[ds][0], "last_run_availability_time": metas[ds][1]}

    info = ensemble.hole_modellinfo(hole, jetzt)
    assert info["ecmwf_ifs025"]["reif"] is False  # Sicherheitsabstand nicht erreicht
    assert info["gfs025"]["reif"] is True
    assert info["icon_seamless"]["reif"] is False and info["icon_seamless"]["lauf"] == "2026-10-13T18:00Z"
    assert "dwd_icon_eps@2026-10-13T12:00Z" in info["icon_seamless"]["details"]  # Herkunft bleibt sichtbar


def test_offene_hko_events_werden_ueber_das_fenster_hinaus_verfolgt(tmp_path):
    ev = {"slug": "highest-temperature-in-hong-kong-on-october-1-2026", "endDate": "2026-10-01T12:00:00Z",
          "markets": [{"groupItemTitle": "28°C", "outcomePrices": json.dumps(["1", "0"])}]}
    api = FakeApi()
    api.geschl = [ev]
    api.hko = lambda art, j, m: {}
    zustand = {}
    pk.aufloesung_phase(api, tmp_path, datetime(2026, 10, 3, 8, tzinfo=timezone.utc), {}, zustand)
    assert zustand["aufloesung_offen"] == {ev["slug"]: "2026-10-01"}
    # 20 Tage später: Event liegt weit außerhalb des 6-Tage-Fensters, HKO hat jetzt veröffentlicht
    api.geschl = []
    api.einzel = {ev["slug"]: ev}
    api.hko = lambda art, j, m: {"2026-10-01": 28.9}
    info = {}
    pk.aufloesung_phase(api, tmp_path, datetime(2026, 10, 23, 8, tzinfo=timezone.utc), info, zustand)
    assert info["aufloesung_neu"] == 1 and zustand["aufloesung_offen"] == {}
    rows = speicher.lies_csv_gz(tmp_path / "2026-10-23" / "aufloesung.csv.gz")
    assert rows[0]["messwert"] == "28" and rows[0]["treffer"] == "1"


def test_unentschiedenes_event_wird_vorgemerkt(tmp_path):
    ev = _ev_geschlossen("highest-temperature-in-nyc-on-october-13-2026", "2026-10-13", "gibt-es-nicht")
    api = FakeApi()
    api.geschl = [ev]
    zustand = {}
    pk.aufloesung_phase(api, tmp_path, datetime(2026, 10, 14, 8, tzinfo=timezone.utc), {}, zustand)
    assert list(zustand["aufloesung_offen"]) == [ev["slug"]]


def test_netz_frist_und_tageslimit(monkeypatch):
    from bot import netz

    class R:
        def __init__(self, code, text):
            self.status_code, self.text = code, text

    monkeypatch.setattr(netz._SESSION, "request", lambda *a, **k: R(429, '{"reason":"Daily API request limit exceeded"}'))
    with pytest.raises(netz.TageslimitFehler):
        netz.anfrage("GET", "http://x")
    monkeypatch.setattr(netz._SESSION, "request", lambda *a, **k: R(429, '{"reason":"Minutely limit"}'))
    netz.setze_frist(netz.time.monotonic() + 30)  # Wartezeit 65 s passt nicht in die Frist
    try:
        with pytest.raises(netz.ZeitbudgetFehler):
            netz.anfrage("GET", "http://x")
    finally:
        netz.setze_frist(None)
    netz.setze_frist(netz.time.monotonic() - 1)
    try:
        with pytest.raises(netz.ZeitbudgetFehler):
            netz.anfrage("GET", "http://x")
    finally:
        netz.setze_frist(None)


def test_aufloesung_phase_speichert_und_dedupliziert(tmp_path):
    from datetime import timedelta
    z0 = datetime(2026, 10, 13, 0, tzinfo=timezone.utc)
    obs = [(z0 + timedelta(hours=h + 4), 70.0) for h in range(24)]
    api = FakeApi()
    api.geschl = [_ev_geschlossen("highest-temperature-in-nyc-on-october-13-2026", "2026-10-13", "70-71°F")]
    api.obs = lambda i, v, b: obs
    jetzt = datetime(2026, 10, 14, 8, tzinfo=timezone.utc)
    info = {}
    pk.aufloesung_phase(api, tmp_path, jetzt, info)
    assert info["aufloesung_neu"] == 1 and info["aufloesung_abweichungen"] == 0
    info2 = {}
    pk.aufloesung_phase(api, tmp_path, jetzt + timedelta(hours=12), info2)
    assert info2["aufloesung_neu"] == 0  # schon erfasst


def test_stamm_wird_nur_als_differenz_geschrieben(tmp_path):
    pk.lauf(FakeApi(), tmp_path, JETZT)
    pk.lauf(FakeApi(), tmp_path, datetime(2026, 10, 14, 13, 0, tzinfo=timezone.utc))
    assert [f.name for f in sorted((tmp_path / "2026-10-14").glob("maerkte_stamm_*"))] == ["maerkte_stamm_1230.csv.gz"]


def test_veraltete_meta_faellt_auf_raster_zurueck():
    jetzt = datetime(2026, 10, 13, 20, 30, tzinfo=timezone.utc)
    meta = {"last_run_initialisation_time": int(datetime(2026, 10, 6, tzinfo=timezone.utc).timestamp())}
    frisch = {"last_run_initialisation_time": int(datetime(2026, 10, 13, 12, tzinfo=timezone.utc).timestamp())}

    def hole(url, params=None, **kw):
        return meta if "icon" in url else frisch

    r = ensemble.hole_modelllaeufe(hole, jetzt)
    assert r["icon_seamless"] == "2026-10-13T18:00Z~"
    assert r["ecmwf_ifs025"] == "2026-10-13T12:00Z"
    assert ensemble.neue_modelle(r, dict(r)) == []  # gleiche Läufe/Raster: nichts neu
    assert ensemble.neue_modelle({"icon_seamless": "2026-10-14T00:00Z~"}, {"icon_seamless": "2026-10-13T18:00Z~"}) == ["icon_seamless"]
    assert ensemble.vorlauf_stunden("2026-10-13T18:00Z~", "2026-10-14", "UTC") == 6.0


def test_meta_ausfall_nutzt_raster():
    def hole(url, params=None, **kw):
        raise RuntimeError("down")
    assert ensemble.hole_modelllaeufe(hole, datetime(2026, 10, 13, 7, tzinfo=timezone.utc))["gfs025"] == "2026-10-13T06:00Z~"
