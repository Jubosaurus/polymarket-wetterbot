import pytest

from bot.wetter import berechne, modellnamen, neueste_schnappschuesse, tageswerte


def _antwort(tage=2, fehlende_stunden=0):
    zeiten = [f"2026-10-1{3 + d}T{h:02d}:00" for d in range(tage) for h in range(24)]
    ctrl = [10.0 + (h % 12) for _ in range(tage) for h in range(24)]  # Tagesmax 21, Tagesmin 10
    mem = list(ctrl)
    for i in range(fehlende_stunden):
        mem[-1 - i] = None
    return {"hourly": {
        "time": zeiten,
        "temperature_2m_ecmwf_ifs025_ensemble": ctrl,
        "temperature_2m_member01_ecmwf_ifs025_ensemble": mem,
        "temperature_2m_ncep_gefs025": ctrl,
        "wind_speed_10m": [99.0] * len(zeiten),  # darf nicht als Member zählen
    }}


def test_tageswerte_max_min_und_member():
    tw = tageswerte(_antwort())
    assert tw["2026-10-13"]["hoechst"] == [21.0, 21.0, 21.0]
    assert tw["2026-10-13"]["tiefst"] == [10.0, 10.0, 10.0]


def test_tageswerte_unvollstaendiger_tag_wird_ausgelassen():
    tw = tageswerte(_antwort(fehlende_stunden=5))  # ein Member hat am letzten Tag nur 19 Werte
    assert len(tw["2026-10-13"]["hoechst"]) == 3
    assert len(tw["2026-10-14"]["hoechst"]) == 2
    assert tw["2026-10-14"]["ausgeschlossen"] == 1 and tw["2026-10-13"]["ausgeschlossen"] == 0


def test_eine_fehlende_stunde_genuegt_zum_ausschluss():
    # fehlt genau die wärmste Stunde, darf kein falsches Tagesmaximum entstehen
    a = _antwort(tage=1)
    a["hourly"]["temperature_2m_member01_ecmwf_ifs025_ensemble"][11] = None  # Stunde des Maximums (21 °C)
    tw = tageswerte(a)
    assert tw["2026-10-13"]["hoechst"] == [21.0, 21.0]
    assert tw["2026-10-13"]["ausgeschlossen"] == 1


def test_nur_juengster_schnappschuss_je_event():
    alt = {**_zeile("nyc", "70-71°F", einheit="F"), "abruf_utc": "2026-10-13T08:00:00+00:00", "preis_mitte": "0.1"}
    neu = {**_zeile("nyc", "70-71°F", einheit="F"), "abruf_utc": "2026-10-13T12:00:00+00:00", "preis_mitte": "0.4"}
    ev = neueste_schnappschuesse([alt, neu])
    assert [z["preis_mitte"] for z in ev[("nyc", "hoechst", "2026-10-14")]] == ["0.4"]
    out = berechne([alt, neu], hole=lambda st: _antwort())
    assert len(out) == 1 and out[0]["markt_abruf_utc"] == "2026-10-13T12:00:00+00:00" and out[0]["ensemble_abruf_utc"]


def test_modellnamen():
    assert modellnamen(_antwort()) == "ecmwf_ifs025+gfs025"


def _zeile(stadt, bucket, art="hoechst", datum="2026-10-14", einheit="C", rundung="kaufm"):
    return {"art": art, "stadt": stadt, "datum": datum, "bucket": bucket, "einheit": einheit,
            "rundung": rundung, "markt_id": "m" + bucket, "station": "X", "preis_mitte": "0.5",
            "bid": "", "ask": ""}


def test_berechne_mit_stub_und_einheit_f():
    # alle Member 21 °C = 69.8 °F -> gerundet 70 -> Bucket "70-71°F"
    antwort = _antwort()
    zeilen = [_zeile("nyc", b, einheit="F") for b in ["67°F or below", "68-69°F", "70-71°F", "72°F or higher"]]
    out = berechne(zeilen, hole=lambda st: antwort)
    p = {z["bucket"]: z["p_modell"] for z in out}
    assert p["70-71°F"] == 1.0 and sum(p.values()) == pytest.approx(1.0)


def test_berechne_ueberspringt_regen_unbekannte_stadt_und_ausserhalb_horizont():
    antwort = _antwort()
    zeilen = [
        {**_zeile("nyc", "x"), "art": "niederschlag"},
        _zeile("atlantis", "20°C"),
        _zeile("nyc", "20°C", datum="2030-01-01"),
    ]
    assert berechne(zeilen, hole=lambda st: antwort) == []
