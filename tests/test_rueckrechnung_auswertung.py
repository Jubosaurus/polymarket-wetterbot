import pytest

from auswertungen import rueckrechnung as ra
from bot import rueckrechnung as rr


def _rec(preise, ps, ys, v=1, datum="2026-07-10"):
    return {"slug": "highest-temperature-in-nyc-on-july-10-2026", "stadt": "nyc", "einheit": "F", "art": "hoechst",
            "datum": datum, "v": v, "haelfte": ra.haelfte(datum), "td": 1000, "preissumme": sum(p for p in preise if p is not None),
            "varianten": {"mittel": {"p": ps}},
            "buckets": [{"titel": f"b{i}", "y": y, "preis": p, "preis_t": 900} for i, (p, y) in enumerate(zip(preise, ys))],
            "lauf": {}}


def test_haelfte_grenze():
    assert ra.haelfte("2026-06-30") == "finden" and ra.haelfte("2026-07-01") == "bestaetigen"


def test_stat_summen_trefferquote_und_ohne_top3():
    s = ra.stat([5.0, -10.0, 3.0, 1.0, -10.0])
    assert s["n"] == 5 and s["wins"] == 3 and s["rate"] == 0.6
    assert s["summe"] == pytest.approx(-11.0)
    assert s["ohne_top3"] == pytest.approx(-11.0 - (5.0 + 3.0 + 1.0))
    assert ra.stat([])["n"] == 0
    assert ra.stat([2.0, 1.0])["ohne_top3"] == 0.0  # weniger als 3 Wetten: alles entfällt


def test_wetten_hoechstens_zwei_je_event_und_gewinnrechnung():
    # Modell sieht Bucket 0 viel wahrscheinlicher als der Markt (Ja-Wette), Bucket 2 viel unwahrscheinlicher (Nein-Wette)
    rec = _rec(preise=[0.20, 0.50, 0.60], ps=[0.50, 0.45, 0.10], ys=[1, 0, 0])
    w = ra.wetten_fuer([rec], "mittel", 0.04, 0.10, "beide")
    assert len(w) == 2
    ja = next(x for x in w if x["seite"] == "ja")
    nein = next(x for x in w if x["seite"] == "nein")
    assert ja["bucket"] == "b0" and ja["gewinnt"] == 1
    assert ja["gewinn"] == pytest.approx(10 / rr.kosten_je_anteil(0.20, 0.04) - 10)
    assert nein["bucket"] == "b2" and nein["gewinnt"] == 1  # Bucket 2 gewann nicht -> Nein gewinnt
    assert nein["kosten"] == pytest.approx(rr.kosten_je_anteil(0.40, 0.04))
    # nur Ja: eine Wette; nur Nein: mehrere Kandidaten, aber höchstens 2
    assert [x["seite"] for x in ra.wetten_fuer([rec], "mittel", 0.04, 0.10, "ja")] == ["ja"]
    assert len(ra.wetten_fuer([rec], "mittel", 0.04, 0.10, "nein")) <= 2
    # höhere Schwelle -> weniger Wetten
    assert len(ra.wetten_fuer([rec], "mittel", 0.04, 0.45, "beide")) < 2


def test_bucket_ohne_preis_wird_uebersprungen_und_unbekannte_variante_ignoriert():
    rec = _rec(preise=[None, 0.5], ps=[0.9, 0.1], ys=[1, 0])
    assert [x["bucket"] for x in ra.wetten_fuer([rec], "mittel", 0.04, 0.10, "beide")] == ["b1"]
    assert ra.wetten_fuer([rec], "gfs", 0.04, 0.10, "beide") == []


def test_auswerten_brier_und_lookahead_pruefung(tmp_path, monkeypatch):
    monkeypatch.setattr(ra, "WETTEN", tmp_path / "w.csv")
    rec = _rec(preise=[0.20, 0.50, 0.60], ps=[0.50, 0.45, 0.10], ys=[1, 0, 0])
    rec["lauf"] = {"ecmwf": {"verfuegbar_max": 2000, "init": 0, "n": 1, "extrem_t": 0}}  # nach td = 1000 -> Verstoß
    erg = ra.auswerten([rec])
    b = erg["brier"]["bestaetigen|V1|alle"]
    assert b["n"] == 3
    assert b["modell"] == pytest.approx(((0.5 - 1) ** 2 + 0.45 ** 2 + 0.1 ** 2) / 3)
    assert b["markt"] == pytest.approx(((0.2 - 1) ** 2 + 0.5 ** 2 + 0.6 ** 2) / 3)
    assert erg["verstoesse"]["lauf_nach_entscheidung"] == erg["haupt_wetten_n"] > 0
    assert erg["verstoesse"]["preis_nach_entscheidung"] == 0
