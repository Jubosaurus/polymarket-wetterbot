"""Kleine HTTP-Hilfe: Timeout, Wiederholung bei 429/5xx, nur öffentliche GET/POST ohne Schlüssel.

Eine gemeinsame Frist (`setze_frist`) gilt für ALLE Abrufe samt Wiederholungen und Wartezeiten,
damit ein langsamer Dienst den Gesamtlauf nicht über das Job-Limit schieben kann.
"""
import time

import requests

_SESSION = requests.Session()
_SESSION.headers["User-Agent"] = "polymarket-wetterbot-papier/0.1 (nur lesend)"
_FRIST: float | None = None  # time.monotonic()-Wert, bis zu dem Abrufe erlaubt sind


class ZeitbudgetFehler(RuntimeError):
    """Gemeinsame Frist erreicht: kein weiterer Abruf."""


class TageslimitFehler(RuntimeError):
    """Der Dienst meldet sein Tageslimit (Open-Meteo: 'Daily API request limit exceeded')."""


def setze_frist(ende_monotonic: float | None) -> None:
    global _FRIST
    _FRIST = ende_monotonic


def rest_s() -> float | None:
    return None if _FRIST is None else _FRIST - time.monotonic()


def anfrage(methode: str, url: str, *, params=None, json=None, versuche: int = 5, timeout: int = 60):
    letzter = None
    for i in range(versuche):
        rest = rest_s()
        if rest is not None and rest < 2:
            raise ZeitbudgetFehler(f"Zeitbudget erschöpft vor Abruf von {url}")
        t = timeout if rest is None else min(timeout, rest)
        pause = 2 ** i
        try:
            r = _SESSION.request(methode, url, params=params, json=json, timeout=t)
        except requests.RequestException as e:
            letzter = e
        else:
            if r.status_code == 429 and "Daily" in r.text:
                raise TageslimitFehler(f"Tageslimit bei {url}: {r.text[:120]}")
            if r.status_code == 429 or r.status_code >= 500:
                letzter = RuntimeError(f"HTTP {r.status_code} von {url}: {r.text[:120]}")
                if r.status_code == 429 and "Minutely" in r.text:
                    pause = 65  # Minutenlimit (Open-Meteo): eine volle Minute abwarten
            elif r.status_code >= 400:
                raise RuntimeError(f"HTTP {r.status_code} von {url}: {r.text[:200]}")
            else:
                return r
        rest = rest_s()
        if rest is not None and pause >= rest:
            raise ZeitbudgetFehler(f"Zeitbudget erschöpft beim Warten auf {url}")
        time.sleep(pause)
    raise RuntimeError(f"Anfrage fehlgeschlagen nach {versuche} Versuchen: {letzter}")


def get_json(url: str, params=None, **kw):
    return anfrage("GET", url, params=params, **kw).json()


def post_json(url: str, json, **kw):
    return anfrage("POST", url, json=json, **kw).json()
