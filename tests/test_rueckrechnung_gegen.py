from datetime import datetime, timezone

from auswertungen import rueckrechnung_gegenrechnung as g
from bot import rueckrechnung as rr


def test_gegen_zieldatum_aus_fragetext_nicht_aus_enddate():
    e = {"titel": "Lowest temperature in Seoul on April 15?", "ende": "2026-04-16T12:00:00Z",
         "beschr": "This market will resolve to ... in degrees Celsius on 15 Apr '26. The"}
    assert g.ziel_aus_fragetext(e) == ("2026-04-15", "mit_jahr_aus_beschreibung")
    # Beschreibung ohne Datum: Jahr aus endDate (nächstliegend, auch über den Jahreswechsel)
    e2 = {"titel": "Highest temperature in NYC on December 31?", "ende": "2026-01-01T12:00:00Z", "beschr": "text ohne datum"}
    assert g.ziel_aus_fragetext(e2) == ("2025-12-31", "jahr_aus_enddate")
    # Widerspruch zwischen Titel und Beschreibung -> kein Datum
    e3 = {"titel": "Highest temperature in NYC on May 3?", "ende": "2026-05-03T12:00:00Z", "beschr": "... on 4 May '26."}
    assert g.ziel_aus_fragetext(e3)[0] is None
    assert g.ziel_aus_fragetext({"titel": "kaputt", "ende": "2026-05-03T12:00:00Z", "beschr": ""})[0] is None


def test_gegen_stuetzstellen_aus_gewichten_stimmen_mit_hauptrechnung_ueberein():
    for raster in (1, 3):
        for std in range(24):
            t = datetime(2026, 3, 1, std, tzinfo=timezone.utc)
            gegen = sorted(int(x.timestamp()) for x in g.abhaengig_von(t, raster))
            assert gegen == sorted(rr.stuetzstellen(int(t.timestamp()), raster)), (raster, std)


def test_gegen_lauf_chicago_01_03_wie_hauptrechnung():
    tz = "America/Chicago"
    td = g.td_zeit("2026-03-01", tz, 1)
    t = datetime(2026, 3, 1, 17, tzinfo=timezone.utc)
    assert g.lauf_fuer(t, td, 1, 3) == 2 and g.lauf_fuer(t, td, 1, 1) == 1
    hauptr = rr.bekannter_lauf(int(t.timestamp()), rr.entscheidungszeit("2026-03-01", tz, 1), 1, raster_h=3)
    assert hauptr[0] == 2
