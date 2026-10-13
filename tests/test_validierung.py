from auswertungen.validiere_aufloesung import station_aus_event


def test_station_je_event_nicht_aus_heutiger_tabelle():
    assert station_aus_event({"resolutionSource": "https://www.weather.gov/wrh/timeseries?site=LFPG"}) == "LFPG"
    assert station_aus_event({"resolutionSource": "https://www.wunderground.com/history/daily/tw/taipei/RCSS"}) == "RCSS"


def test_station_aus_beschreibung_wenn_quelle_leer():
    ev = {"resolutionSource": "", "description": "available here: https://www.weather.gov/wrh/timeseries?site=LLBG\n"}
    assert station_aus_event(ev) == "LLBG"


def test_station_unbestimmbar():
    assert station_aus_event({"resolutionSource": "https://www.weather.gov.hk/en/cis/climat.htm"}) is None
