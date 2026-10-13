"""Kleine HTTP-Hilfe: Timeout, Wiederholung bei 429/5xx, nur öffentliche GET/POST ohne Schlüssel."""
import time

import requests

_SESSION = requests.Session()
_SESSION.headers["User-Agent"] = "polymarket-wetterbot-papier/0.1 (nur lesend)"


def anfrage(methode: str, url: str, *, params=None, json=None, versuche: int = 5, timeout: int = 60):
    letzter = None
    for i in range(versuche):
        try:
            r = _SESSION.request(methode, url, params=params, json=json, timeout=timeout)
        except requests.RequestException as e:
            letzter = e
        else:
            if r.status_code == 429 or r.status_code >= 500:
                letzter = RuntimeError(f"HTTP {r.status_code} von {url}: {r.text[:120]}")
                if r.status_code == 429 and "Minutely" in r.text:
                    time.sleep(65)  # Minutenlimit (Open-Meteo): eine volle Minute abwarten
                    continue
            elif r.status_code >= 400:
                raise RuntimeError(f"HTTP {r.status_code} von {url}: {r.text[:200]}")
            else:
                return r
        time.sleep(2 ** i)
    raise RuntimeError(f"Anfrage fehlgeschlagen nach {versuche} Versuchen: {letzter}")


def get_json(url: str, params=None, **kw):
    return anfrage("GET", url, params=params, **kw).json()


def post_json(url: str, json, **kw):
    return anfrage("POST", url, json=json, **kw).json()
