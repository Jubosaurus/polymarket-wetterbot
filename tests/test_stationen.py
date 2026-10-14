from zoneinfo import ZoneInfo

from bot.stationen import STATIONEN


def test_alle_zeitzonen_gueltig():
    for s in STATIONEN.values():
        ZoneInfo(s.tz)


def test_koordinaten_und_eindeutigkeit():
    assert all(-90 <= s.lat <= 90 and -180 <= s.lon <= 180 for s in STATIONEN.values())
    assert len({s.icao for s in STATIONEN.values()}) == len(STATIONEN)
    assert all(slug == s.slug for slug, s in STATIONEN.items())


def test_hko_schneidet_ab_rest_rundet():
    assert STATIONEN["hong-kong"].rundung == "abschneiden"
    assert all(s.rundung == "kaufm" for k, s in STATIONEN.items() if k != "hong-kong")


def test_korrigierte_koordinaten_nahe_am_flughafen():
    """Stationsprüfung 2026-10-14: frühere Tabelle hatte Stadtmitten statt Flughäfen (bis 40 km daneben)."""
    import math

    soll = {"chongqing": (29.718, 106.639), "wuhan": (30.783, 114.205), "chengdu": (30.576, 103.95),
            "karachi": (24.902, 67.139), "qingdao": (36.362, 120.087), "shanghai": (31.146, 121.8)}
    for slug, (la, lo) in soll.items():
        s = STATIONEN[slug]
        km = 6371 * math.hypot(math.radians(s.lat - la), math.radians(s.lon - lo) * math.cos(math.radians(la)))
        assert km < 1.0, (slug, km)
