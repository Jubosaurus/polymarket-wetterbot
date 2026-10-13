"""Dateiablage des Protokolls: Tagesordner daten/JJJJ-MM-TT/, komprimierte CSV (csv.gz).

Schreiben ist atomar (temporäre Datei, dann ersetzen), damit ein abgebrochener
Lauf keine halbe Datei hinterlässt, die der nächste Commit einsammelt.
"""
import csv
import gzip
import io
import json
import os
from pathlib import Path

WURZEL = Path("daten")


def tagesordner(datum: str, wurzel: Path = WURZEL) -> Path:
    p = wurzel / datum
    p.mkdir(parents=True, exist_ok=True)
    return p


def _atomar(pfad: Path, daten: bytes) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    tmp = pfad.with_name(pfad.name + ".tmp")
    tmp.write_bytes(daten)
    os.replace(tmp, pfad)


def schreibe_csv_gz(pfad: Path, spalten: list[str], zeilen: list[dict]) -> None:
    puffer = io.StringIO(newline="")
    w = csv.DictWriter(puffer, fieldnames=spalten, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for z in zeilen:
        w.writerow({k: ("" if z.get(k) is None else z.get(k)) for k in spalten})
    # mtime=0: gleiche Inhalte ergeben gleiche Bytes (kein Schein-Unterschied im Git)
    roh = io.BytesIO()
    with gzip.GzipFile(fileobj=roh, mode="wb", compresslevel=9, mtime=0) as g:
        g.write(puffer.getvalue().encode("utf-8"))
    _atomar(pfad, roh.getvalue())


def lies_csv_gz(pfad: Path) -> list[dict]:
    if not pfad.exists():
        return []
    with gzip.open(pfad, "rt", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def haenge_csv_an(pfad: Path, spalten: list[str], zeile: dict) -> None:
    """Hängt eine Zeile an eine unkomprimierte CSV an (kleine Logs wie laufzeit.csv)."""
    neu = not pfad.exists()
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=spalten, extrasaction="ignore", lineterminator="\n")
        if neu:
            w.writeheader()
        w.writerow({k: ("" if zeile.get(k) is None else zeile.get(k)) for k in spalten})


def lies_csv(pfad: Path) -> list[dict]:
    if not pfad.exists():
        return []
    with open(pfad, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def lies_json(pfad: Path, default):
    try:
        return json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def schreibe_json(pfad: Path, obj) -> None:
    _atomar(pfad, (json.dumps(obj, indent=1, sort_keys=True) + "\n").encode("utf-8"))


def groesse_mb(ordner: Path) -> float:
    return round(sum(f.stat().st_size for f in ordner.rglob("*") if f.is_file()) / 1e6, 3) if ordner.exists() else 0.0
