"""Bucket-Parser und Wahrscheinlichkeitsrechnung für Polymarket-Temperaturmärkte.

Die Auflösungsquelle misst auf ganze Grad (°C oder °F). Ein Bucket "68-69°F"
gewinnt daher, wenn der gerundete Tageswert 68 oder 69 ist. Offene Ränder:
"67°F or below" (kein unteres Limit), "86°F or higher" (kein oberes Limit).
"""
import math
import re
from dataclasses import dataclass

_RE = re.compile(
    r"^\s*(-?\d+)(?:\s*-\s*(-?\d+))?\s*°\s*([CF])(?:\s+or\s+(below|higher))?\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Bucket:
    lo: int | None  # inklusive, None = nach unten offen
    hi: int | None  # inklusive, None = nach oben offen
    einheit: str  # "C" oder "F"

    def enthaelt(self, wert_ganz: int) -> bool:
        return (self.lo is None or wert_ganz >= self.lo) and (
            self.hi is None or wert_ganz <= self.hi
        )


def parse_bucket(titel: str) -> Bucket:
    m = _RE.match(titel)
    if not m:
        raise ValueError(f"Bucket-Titel nicht lesbar: {titel!r}")
    a, b, einheit, offen = m.group(1), m.group(2), m.group(3).upper(), m.group(4)
    a = int(a)
    if offen:
        if b is not None:
            raise ValueError(f"Bucket-Titel widersprüchlich: {titel!r}")
        return Bucket(None, a, einheit) if offen.lower() == "below" else Bucket(a, None, einheit)
    return Bucket(a, int(b) if b is not None else a, einheit)


def runde_ganz(x: float) -> int:
    """Kaufmännisch runden (x.5 nach oben, auch bei negativen Werten),
    wie bei der Umrechnung von Messwerten auf ganze Grad."""
    return math.floor(x + 0.5)


def auf_ganz(x: float, regel: str = "kaufm") -> int:
    """Auflösungsregel einer Station: 'kaufm' (runden) oder 'abschneiden' (HKO,
    nach unten, per Test an 62 Hong-Kong-Märkten bestätigt)."""
    if regel == "abschneiden":
        return math.floor(x)
    if regel == "kaufm":
        return runde_ganz(x)
    raise ValueError(f"unbekannte Rundungsregel: {regel!r}")


def c_nach_f(c: float) -> float:
    return c * 9.0 / 5.0 + 32.0


def bucket_wahrscheinlichkeiten(
    werte: list[float], buckets: list[Bucket], regel: str = "kaufm"
) -> list[float]:
    """Anteil der Ensemble-Werte (bereits in der Einheit der Buckets), die nach
    Rundung auf ganze Grad in den jeweiligen Bucket fallen. Die Summe ist 1,
    sofern die Buckets den Wertebereich lückenlos abdecken."""
    if not werte:
        raise ValueError("keine Ensemble-Werte")
    ganz = [auf_ganz(w, regel) for w in werte]
    n = len(ganz)
    return [sum(1 for g in ganz if b.enthaelt(g)) / n for b in buckets]
