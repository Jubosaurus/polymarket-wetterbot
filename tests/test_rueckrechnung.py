import numpy as np
import pytest

from bot import rueckrechnung as rr
from bot.buckets import parse_bucket


def test_entscheidungszeit_ortszeit_und_sommerzeit():
    # NYC, Zieltag 2026-07-15, Vorlauf 1: 18:00 EDT am 14.7. = 22:00 UTC
    assert rr.entscheidungszeit("2026-07-15", "America/New_York", 1) == rr.lokal_nach_utc_ts("2026-07-14", 22, "UTC")
    # Winter: 18:00 EST = 23:00 UTC; Vorlauf 2 geht zwei Tage zurück
    assert rr.entscheidungszeit("2026-01-15", "America/New_York", 2) == rr.lokal_nach_utc_ts("2026-01-13", 23, "UTC")
    # Seoul (UTC+9): 18:00 = 09:00 UTC
    assert rr.entscheidungszeit("2026-05-02", "Asia/Seoul", 1) == rr.lokal_nach_utc_ts("2026-05-01", 9, "UTC")


def test_tag_stunden_zeitumstellung_und_halbstundenzone():
    assert len(rr.tag_stunden("2026-03-08", "America/New_York")) == 23  # Beginn Sommerzeit
    assert len(rr.tag_stunden("2026-11-01", "America/New_York")) == 25  # Ende Sommerzeit
    assert len(rr.tag_stunden("2026-05-02", "Europe/London")) == 24
    indien = rr.tag_stunden("2026-05-02", "Asia/Kolkata")  # UTC+5:30: volle UTC-Stunden im Tag
    assert len(indien) == 24 and all(t % 3600 == 0 for t in indien)
    start, ende = rr.tag_grenzen("2026-05-02", "Asia/Kolkata")
    assert start <= indien[0] < start + 3600 and indien[-1] < ende


def test_bekannter_lauf_verfuegbarkeit():
    # London (UTC), Zieltag 2026-05-02, Vorlauf 1: Td = 2026-05-01 18:00 UTC
    td = rr.entscheidungszeit("2026-05-02", "Europe/London", 1)  # BST: 17:00 UTC
    h = lambda tag, std: rr.lokal_nach_utc_ts(tag, std, "UTC")
    # Stunde 04:00 am Zieltag: Lauf = floor6(04:00 am 1.5.) = 00Z am 1.5.; +10 h = 10Z <= Td -> N=1
    assert rr.bekannter_lauf(h("2026-05-02", 4), td, 1) == (1, h("2026-05-01", 0))
    # Stunde 15:00: Lauf 12Z am 1.5.; +10 h = 22Z > 17Z -> nicht bekannt, N=2 (12Z am 30.4., 22Z am 30.4.)
    assert rr.bekannter_lauf(h("2026-05-02", 15), td, 1) == (2, h("2026-04-30", 12))
    # Vorlauf 2 beginnt bei N=2, geht für späte Stunden auf N=3
    td2 = rr.entscheidungszeit("2026-05-02", "Europe/London", 2)
    assert rr.bekannter_lauf(h("2026-05-02", 15), td2, 2) == (3, h("2026-04-29", 12))
    # nichts verfügbar (nmax erreicht)
    assert rr.bekannter_lauf(h("2026-05-02", 15), td2 - 40 * 3600, 2) is None


def _serien(wert_n):
    """wert_n: N -> Funktion(stunde_im_tag) liefert Wert; gilt für den Tag 2026-05-02 (London)."""
    out = {}
    for n, f in wert_n.items():
        out[n] = {t: f(i) for i, t in enumerate(rr.tag_stunden("2026-05-02", "Europe/London"))}
    return out


def test_komposit_nutzt_nur_bekannte_laeufe():
    # N=1 liefert 100, N=2 liefert alles andere: spätere Stunden dürfen den N=1-Wert nicht enthalten
    s = _serien({1: lambda i: 100.0, 2: lambda i: 10.0 + i * 0.1, 3: lambda i: -50.0})
    r = rr.komposit_tageswerte(s, "2026-05-02", "Europe/London", 1)
    td = r["td"]
    # Der gemeldete Höchstwert stammt aus einer Stunde, deren Lauf zum Zeitpunkt td verfügbar war
    assert r["max"] == 100.0
    assert r["max_init"] + 10 * 3600 <= td and r["max_n"] == 1
    assert r["verfuegbar_max"] <= td  # kein genutzter Lauf war zum Entscheidungszeitpunkt noch unbekannt
    # und die Stunden mit N=2 stammen nicht aus N=1
    spaet = rr.tag_stunden("2026-05-02", "Europe/London")[-1]
    assert rr.bekannter_lauf(spaet, td, 1)[0] == 2


def test_komposit_fehlende_stunde_ergibt_none():
    s = _serien({1: lambda i: 1.0, 2: lambda i: 1.0, 3: lambda i: 1.0})
    stunden = rr.tag_stunden("2026-05-02", "Europe/London")
    del s[2][stunden[-1]]
    assert rr.komposit_tageswerte(s, "2026-05-02", "Europe/London", 1) is None


def test_messung_tageswert_lokaler_tag():
    start, ende = rr.tag_grenzen("2026-05-02", "Europe/London")
    beob = [(start - 60, 99.0)] + [(start + i * 1800, 10.0 + i % 5) for i in range(48)] + [(ende, 99.0)]
    assert rr.tageswert_messung(beob, "2026-05-02", "Europe/London", "hoechst") == 14.0
    assert rr.tageswert_messung(beob, "2026-05-02", "Europe/London", "tiefst") == 10.0
    assert rr.tageswert_messung(beob[:5], "2026-05-02", "Europe/London", "hoechst") is None


def test_bucket_p_rundung_offene_raender_und_summe():
    buckets = [parse_bucket(t) for t in ["10°C or below", "11°C", "12°C", "13°C or higher"]]
    res = np.array([-2.0, -1.0, 0.0, 0.0, 0.4, 0.6, 1.5, 3.0])
    p = rr.bucket_p(12.0, res, buckets)
    # F+r: 10, 11, 12, 12, 12.4->12, 12.6->13, 13.5->14, 15 -> <=10:1, 11:1, 12:3, >=13:3 (mit Begrenzung)
    assert p == pytest.approx([1 / 8, 1 / 8, 3 / 8, 3 / 8])
    assert sum(p) == pytest.approx(1.0)
    # Abschneiden (HKO-Regel): 12.6 -> 12
    p2 = rr.bucket_p(12.0, np.array([0.6]), buckets, "abschneiden")
    assert p2[2] == pytest.approx(rr.P_MAX) and p2[3] == pytest.approx(rr.P_MIN)


def test_bucket_p_exakte_halbe_runden_nach_oben_ohne_gleitkommarauschen():
    # F = 12,3 und Residuum 0,2 liefert in Gleitkomma 12,5 +/- Rauschen; x,5 muss immer nach oben (13) runden
    buckets = [parse_bucket("12°C"), parse_bucket("13°C")]
    for f, r in [(12.3, 0.2), (12.1, 0.4), (11.7, 0.8), (68.3, 0.2), (0.1 + 0.2, 0.2)]:
        p = rr.bucket_p(f, np.array([r]), [parse_bucket(f"{int(f + r + 0.5)}°C"), parse_bucket(f"{int(f + r - 0.5)}°C")])
        assert p[0] == pytest.approx(rr.P_MAX), (f, r)
    assert rr.bucket_p(12.0, np.array([0.5]), buckets) == [rr.P_MIN, rr.P_MAX]
    assert rr.bucket_p(12.0, np.array([0.5]), buckets, "abschneiden") == [rr.P_MAX, rr.P_MIN]


def test_bucket_p_in_fahrenheit_und_begrenzung():
    assert rr.in_einheit(20.0, "F") == 68.0 and rr.in_einheit(20.0, "C") == 20.0
    p = rr.bucket_p(68.0, np.zeros(10), [parse_bucket("68-69°F"), parse_bucket("70°F or higher")])
    assert p == [rr.P_MAX, rr.P_MIN]


def test_kosten_und_gebuehr_gegen_dokumentation():
    # docs/gebuehren.md: 100 Anteile bei 0,50 -> 1,25 $ Gebühr, also 0,0125 je Anteil
    c = rr.kosten_je_anteil(0.48, 0.04)  # q = 0,50
    assert c == pytest.approx(0.50 + 0.0125)
    assert rr.kosten_je_anteil(0.10, 0.0) == pytest.approx(0.10 + 0.05 * 0.1 * 0.9)


def test_kandidaten_ja_nein_und_ungueltig():
    k = {x["seite"]: x for x in rr.kandidaten(0.60, 0.40, 0.04)}
    assert k["ja"]["kante"] == pytest.approx(0.60 - rr.kosten_je_anteil(0.40, 0.04))
    assert k["nein"]["kante"] == pytest.approx(0.40 - rr.kosten_je_anteil(0.60, 0.04))
    # Preis 0,99 + halber Spread: Ja-Kosten >= 1 entfallen
    assert [x["seite"] for x in rr.kandidaten(0.99, 0.99, 0.04)] == ["nein"]


def test_wahl_hoechstens_zwei_und_seitenfilter():
    liste = [{"seite": s, "kante": k, "bucket_idx": i, "kosten": 0.5}
             for i, (s, k) in enumerate([("ja", 0.30), ("nein", 0.25), ("ja", 0.20), ("nein", 0.05)])]
    assert [x["kante"] for x in rr.waehle_wetten(liste, 0.10)] == [0.30, 0.25]
    assert [x["kante"] for x in rr.waehle_wetten(liste, 0.10, seiten=("ja",))] == [0.30, 0.20]
    assert [x["kante"] for x in rr.waehle_wetten(liste, 0.04, seiten=("nein",))] == [0.25, 0.05]
    assert rr.waehle_wetten(liste, 0.50) == []


def test_wett_ergebnis_einsatz_inklusive_gebuehr():
    c = rr.kosten_je_anteil(0.18, 0.04)  # q = 0,20, Gebühr 0,008 -> c = 0,208
    assert rr.wett_ergebnis(c, True) == pytest.approx(10 / 0.208 - 10)
    assert rr.wett_ergebnis(c, False) == -10.0


def test_brier_und_kalibrierung():
    assert rr.brier([1.0, 0.0], [1, 0]) == 0.0
    assert rr.brier([0.5, 0.5], [1, 0]) == pytest.approx(0.25)
    k = rr.kalibrierung([0.05, 0.25, 0.28, 1.0], [0, 1, 0, 1])
    assert k[0][2] == 1 and k[2][2] == 2 and k[2][4] == 0.5 and k[9][2] == 1
    assert k[5][2] == 0


# ---- Klarstellung 2026-10-14 (Codex-Review): Zieldatum und Interpolations-Stützstellen

def test_zieldatum_aus_slug_gegen_enddate():
    # echte Abweichung: endDate liegt einen Tag nach dem Zieltag im Slug
    assert rr.zieldatum_aus_slug("lowest-temperature-in-seoul-on-april-15-2026", "2026-04-16T12:00:00Z") == "2026-04-15"
    assert rr.zieldatum_aus_slug("highest-temperature-in-nyc-on-march-1-2026", "2026-03-01T12:00:00Z") == "2026-03-01"
    assert rr.zieldatum_aus_slug("highest-temperature-in-sao-paulo-on-october-11-2026") == "2026-10-11"
    # ohne Jahr im Slug (frühe Events): Jahr aus endDate, nächstliegend (auch über den Jahreswechsel)
    assert rr.zieldatum_aus_slug("highest-temperature-in-nyc-on-december-30", "2025-12-30T12:00:00Z") == "2025-12-30"
    assert rr.zieldatum_aus_slug("highest-temperature-in-nyc-on-january-1", "2025-12-31T12:00:00Z") == "2026-01-01"
    # unlesbar -> None
    assert rr.zieldatum_aus_slug("highest-temperature-in-nyc-on-smarch-1-2026") is None
    assert rr.zieldatum_aus_slug("highest-temperature-in-nyc-on-february-30-2026") is None


def test_preiszeile_nur_gueltig_wenn_entscheidungszeit_zum_zieltag_passt():
    td = {v: rr.entscheidungszeit("2026-04-15", "Asia/Seoul", v) for v in (1, 2)}
    zeile = {"slug": "x", "td": {"1": td[1], "2": td[2]}}
    assert rr.preiszeile_gueltig(zeile, "2026-04-15", "Asia/Seoul")
    # alte Zeile wurde mit dem um einen Tag verschobenen Datum (endDate) abgerufen -> ungültig, neu laden
    alt = {"slug": "x", "td": {str(v): rr.entscheidungszeit("2026-04-16", "Asia/Seoul", v) for v in (1, 2)}}
    assert not rr.preiszeile_gueltig(alt, "2026-04-15", "Asia/Seoul")
    assert not rr.preiszeile_gueltig({"slug": "x"}, "2026-04-15", "Asia/Seoul")


def test_stuetzstellen_ecmwf_3h_catmull_rom_gemessen():
    h = lambda std: rr.lokal_nach_utc_ts("2026-03-01", std, "UTC")
    # Stunde 17 UTC liegt zwischen den Stützstellen 15 und 18: Catmull-Rom nutzt 12, 15, 18, 21
    assert rr.stuetzstellen(h(17), 3) == [h(12), h(15), h(18), h(21)]
    assert rr.stuetzstellen(h(16), 3) == [h(12), h(15), h(18), h(21)]
    # auf einer Stützstelle ist der Wert nativ
    assert rr.stuetzstellen(h(15), 3) == [h(15)]
    # stündlich native Modelle (GFS): nur die Stunde selbst
    assert rr.stuetzstellen(h(17), 1) == [h(17)]


def test_chicago_01_03_interpolation_darf_keinen_spaeteren_lauf_enthalten():
    # Chicago, Zieltag 2026-03-01, Vorlauf 1: Td = 28.2. 18:00 CST = 01.03. 00:00 UTC.
    td = rr.entscheidungszeit("2026-03-01", "America/Chicago", 1)
    t = rr.lokal_nach_utc_ts("2026-03-01", 17, "UTC")
    assert td == rr.lokal_nach_utc_ts("2026-03-01", 0, "UTC")
    # alte Regel (nur die Stunde selbst): Lauf 28.2. 12Z, bekannt ab 22Z -> N=1
    assert rr.bekannter_lauf(t, td, 1) == (1, rr.lokal_nach_utc_ts("2026-02-28", 12, "UTC"))
    # ECMWF: die Stützstelle 18Z hängt an Lauf 28.2. 18Z (bekannt erst 01.03. 04Z) -> N=1 unzulässig, N=2
    n, init = rr.bekannter_lauf(t, td, 1, raster_h=3)
    assert n == 2
    assert init + 10 * 3600 <= td  # der spätere der genutzten Läufe war bekannt


def test_stuetzstellen_grenzfaelle_an_laufwechseln():
    td = rr.lokal_nach_utc_ts("2026-05-01", 18, "UTC")  # Td = 18Z
    h = lambda tag, std: rr.lokal_nach_utc_ts(tag, std, "UTC")
    # Zeitpunkt 02.5. 01:00: Stützstellen 02.5. 00,03,06 und 01.5. 21; Läufe (N=1): 01.5. 18Z (18Z+10=04Z 2.5. > Td)
    # N=1: 21Z am 1.5. -> Lauf 20.4... : floor6(21Z 1.5. - 24 h)= 30.4. 18Z, ok; 06Z am 2.5. -> 1.5. 06Z + 10 h = 16Z ok
    # -> alle <= Td: N=1 zulässig
    assert rr.bekannter_lauf(h("2026-05-02", 4), td, 1, raster_h=3)[0] == 1
    # Stunde 07: Stützstellen 03,06,09,12 am 2.5.; 12Z -> Lauf 1.5. 12Z, bekannt 22Z > 18Z -> N=2
    assert rr.bekannter_lauf(h("2026-05-02", 7), td, 1, raster_h=3)[0] == 2
    # genau am Rand: Lauf + 10 h == Td zählt als bekannt (<=)
    assert rr.bekannter_lauf(h("2026-05-02", 6), td - 0, 1, raster_h=3)[0] == 1  # nativ 06Z: Lauf 1.5. 06Z + 10 = 16Z
    assert rr.bekannter_lauf(h("2026-05-02", 8), h("2026-05-01", 22), 1, raster_h=3)[0] == 1  # Stützst. 06..15: Lauf 12Z+10h=22Z == Td
    assert rr.bekannter_lauf(h("2026-05-02", 8), h("2026-05-01", 21), 1, raster_h=3)[0] == 2


def test_komposit_mit_raster_ruft_nur_bekannte_staetzstellen_ab():
    s = {1: {}, 2: {}, 3: {}}
    for n in s:
        for t in rr.tag_stunden("2026-03-01", "America/Chicago"):
            s[n][t] = 100.0 if n == 1 else 10.0
    r1 = rr.komposit_tageswerte(s, "2026-03-01", "America/Chicago", 1, raster_h=3)
    r0 = rr.komposit_tageswerte(s, "2026-03-01", "America/Chicago", 1, raster_h=1)
    assert r1["verfuegbar_max"] <= r1["td"]
    # mit Raster werden weniger Stunden aus N=1 genommen als ohne
    assert r1["max"] == 100.0 and r0["max"] == 100.0
    n1 = sum(1 for t in rr.tag_stunden("2026-03-01", "America/Chicago") if rr.bekannter_lauf(t, r1["td"], 1, raster_h=3)[0] == 1)
    n0 = sum(1 for t in rr.tag_stunden("2026-03-01", "America/Chicago") if rr.bekannter_lauf(t, r1["td"], 1, raster_h=1)[0] == 1)
    assert n1 < n0
