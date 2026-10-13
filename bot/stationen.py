"""Stationstabelle: Polymarket-Stadt-Slug -> Messstation (ICAO), Zeitzone, Koordinaten.

Quelle der Zuordnung: Auflösungstexte der aktiven Polymarket-Wettermärkte
(Stand 2026-10-13, siehe docs/machbarkeit.md). Koordinaten stammen aus dem
IEM-ASOS-Stationsverzeichnis. Hong Kong wird vom Hong Kong Observatory (HKO)
aufgelöst, nicht von einem Flughafen-METAR; die Koordinaten sind die des HKO-
Hauptquartiers.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Station:
    slug: str
    icao: str
    tz: str
    lat: float
    lon: float
    quelle: str = "NOAA"  # NOAA | WU | HKO
    rundung: str = "kaufm"  # kaufm | abschneiden (HKO schneidet auf ganze Grad ab)


def _s(slug, icao, tz, lat, lon, quelle="NOAA"):
    rundung = "abschneiden" if quelle == "HKO" else "kaufm"
    return slug, Station(slug, icao, tz, lat, lon, quelle, rundung)


STATIONEN: dict[str, Station] = dict([
    _s("amsterdam", "EHAM", "Europe/Amsterdam", 52.3154, 4.7902),
    _s("ankara", "LTAC", "Europe/Istanbul", 40.1281, 32.9951),
    _s("atlanta", "KATL", "America/New_York", 33.6301, -84.4418),
    _s("austin", "KAUS", "America/Chicago", 30.183, -97.6799),
    _s("beijing", "ZBAA", "Asia/Shanghai", 40.0741, 116.587),
    _s("buenos-aires", "SAEZ", "America/Argentina/Buenos_Aires", -34.8222, -58.5358),
    _s("busan", "RKPK", "Asia/Seoul", 35.1795, 128.9382),
    _s("cape-town", "FACT", "Africa/Johannesburg", -33.9667, 18.6),
    _s("chengdu", "ZUUU", "Asia/Shanghai", 30.6667, 104.0167),
    _s("chicago", "KORD", "America/Chicago", 41.9602, -87.9316),
    _s("chongqing", "ZUCK", "Asia/Shanghai", 29.52, 106.48),
    _s("dallas", "KDAL", "America/Chicago", 32.8471, -96.8518),
    _s("denver", "KBKF", "America/Denver", 39.7017, -104.7517),
    _s("guangzhou", "ZGGG", "Asia/Shanghai", 23.3964, 113.3008),
    _s("helsinki", "EFHK", "Europe/Helsinki", 60.3172, 24.9633),
    _s("hong-kong", "HKO", "Asia/Hong_Kong", 22.3025, 114.1744, "HKO"),
    _s("houston", "KHOU", "America/Chicago", 29.6375, -95.2824),
    _s("istanbul", "LTFM", "Europe/Istanbul", 41.2629, 28.7413),
    _s("jeddah", "OEJN", "Asia/Riyadh", 21.6598, 39.1222),
    _s("karachi", "OPKC", "Asia/Karachi", 24.8456, 67.1614),
    _s("kuala-lumpur", "WMKK", "Asia/Kuala_Lumpur", 2.7167, 101.7),
    _s("london", "EGLC", "Europe/London", 51.5053, 0.0553),
    _s("los-angeles", "KLAX", "America/Los_Angeles", 33.9382, -118.3865),
    _s("lucknow", "VILK", "Asia/Kolkata", 26.7606, 80.8893),
    _s("madrid", "LEMD", "Europe/Madrid", 40.4667, -3.5556),
    _s("manila", "RPLL", "Asia/Manila", 14.5069, 121.0042),
    _s("mexico-city", "MMMX", "America/Mexico_City", 19.4363, -99.0721),
    _s("miami", "KMIA", "America/New_York", 25.788, -80.3169),
    _s("milan", "LIMC", "Europe/Rome", 45.63, 8.7231),
    _s("moscow", "UUWW", "Europe/Moscow", 55.5915, 37.2615),
    _s("munich", "EDDM", "Europe/Berlin", 48.3583, 11.8092),
    _s("nyc", "KLGA", "America/New_York", 40.7794, -73.8803),
    _s("panama-city", "MPMG", "America/Panama", 8.9833, -79.5167),
    _s("paris", "LFPB", "Europe/Paris", 48.9672, 2.4272),
    _s("qingdao", "ZSQD", "Asia/Shanghai", 36.0667, 120.3333),
    _s("san-francisco", "KSFO", "America/Los_Angeles", 37.619, -122.3749),
    _s("sao-paulo", "SBGR", "America/Sao_Paulo", -23.4321, -46.4695),
    _s("seattle", "KSEA", "America/Los_Angeles", 47.4447, -122.3144),
    _s("seoul", "RKSI", "Asia/Seoul", 37.4667, 126.45),
    _s("shanghai", "ZSPD", "Asia/Shanghai", 31.1167, 121.7667),
    _s("shenzhen", "ZGSZ", "Asia/Shanghai", 22.6323, 113.8056),
    _s("singapore", "WSSS", "Asia/Singapore", 1.3667, 103.9833),
    _s("taipei", "RCSS", "Asia/Taipei", 25.0694, 121.5517, "WU"),
    _s("tel-aviv", "LLBG", "Asia/Jerusalem", 32.0114, 34.8867),
    _s("tokyo", "RJTT", "Asia/Tokyo", 35.5533, 139.7811),
    _s("toronto", "CYYZ", "America/Toronto", 43.6772, -79.6306),
    _s("warsaw", "EPWA", "Europe/Warsaw", 52.1628, 20.9611),
    _s("wellington", "NZWN", "Pacific/Auckland", -41.3272, 174.8053),
    _s("wuhan", "ZHHH", "Asia/Shanghai", 30.62, 114.13),
])
