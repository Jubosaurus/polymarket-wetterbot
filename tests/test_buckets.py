import pytest

from bot.buckets import Bucket, auf_ganz, bucket_wahrscheinlichkeiten, c_nach_f, parse_bucket, runde_ganz


@pytest.mark.parametrize("titel,erwartet", [
    ("67°F or below", Bucket(None, 67, "F")),
    ("86°F or higher", Bucket(86, None, "F")),
    ("68-69°F", Bucket(68, 69, "F")),
    ("27°C", Bucket(27, 27, "C")),
    ("8°C or below", Bucket(None, 8, "C")),
    ("-5°C", Bucket(-5, -5, "C")),
    ("-3--2°C", Bucket(-3, -2, "C")),
    ("36°C or higher", Bucket(36, None, "C")),
])
def test_parse_bucket(titel, erwartet):
    assert parse_bucket(titel) == erwartet


@pytest.mark.parametrize("titel", ["", "warm", "68-69", "68°K", "5-6°C or higher"])
def test_parse_bucket_fehler(titel):
    with pytest.raises(ValueError):
        parse_bucket(titel)


def test_rundung():
    assert runde_ganz(20.5) == 21
    assert runde_ganz(20.49) == 20
    assert runde_ganz(-0.5) == 0
    assert runde_ganz(-1.5) == -1
    assert auf_ganz(26.9, "abschneiden") == 26
    assert auf_ganz(-0.1, "abschneiden") == -1
    assert auf_ganz(26.9, "kaufm") == 27
    with pytest.raises(ValueError):
        auf_ganz(1.0, "zufall")


def test_enthaelt_offene_raender():
    assert Bucket(None, 67, "F").enthaelt(-40)
    assert not Bucket(None, 67, "F").enthaelt(68)
    assert Bucket(86, None, "F").enthaelt(120)
    assert Bucket(68, 69, "F").enthaelt(69) and not Bucket(68, 69, "F").enthaelt(70)


def test_c_nach_f():
    assert c_nach_f(0) == 32 and c_nach_f(100) == 212


def test_wahrscheinlichkeiten_summe_eins():
    buckets = [parse_bucket(t) for t in ["10°C or below", "11°C", "12°C", "13°C", "14°C or higher"]]
    werte = [9.0, 10.4, 11.5, 11.49, 12.6, 13.2, 20.0, 12.0]
    p = bucket_wahrscheinlichkeiten(werte, buckets)
    assert sum(p) == pytest.approx(1.0)
    # 9.0 und 10.4 -> <=10; 11.49 -> 11; 11.5 und 12.0 -> 12; 12.6 und 13.2 -> 13; 20.0 -> >=14
    assert p == pytest.approx([2 / 8, 1 / 8, 2 / 8, 2 / 8, 1 / 8])
    # 12.6 rundet auf 13, wird aber bei HKO-Regel auf 12 abgeschnitten
    assert bucket_wahrscheinlichkeiten([12.6], buckets, "abschneiden")[2] == 1.0


def test_wahrscheinlichkeiten_leer():
    with pytest.raises(ValueError):
        bucket_wahrscheinlichkeiten([], [Bucket(None, 1, "C")])
