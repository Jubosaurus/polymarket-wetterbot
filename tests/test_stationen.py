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
