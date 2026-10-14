"""Zusatzdiagnose zur Rückrechnung (NICHT Teil der festgeschriebenen Regeln, ändert kein Ergebnis):
Wie brauchbar sind die Preispunkte am Entscheidungszeitpunkt?

Aufruf:  python auswertungen/rr_preisdiagnose.py   -> Ausgabe auf der Konsole (Zahlen für den Bericht)
"""
import json
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from auswertungen.rr_daten import CACHE, test_events  # noqa: E402


def ts(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def main():
    preise = {}
    for zeile in (CACHE / "preise.jsonl").read_text(encoding="utf-8").splitlines():
        z = json.loads(zeile)
        preise[z["slug"]] = z
    summen = defaultdict(list)  # (v, haelfte) -> Summen der Ja-Preise je Event (nur Events mit allen Preisen)
    alter = defaultdict(list)  # (v, haelfte) -> Stunden zwischen Marktstart und Entscheidungszeitpunkt
    punkte = defaultdict(list)  # (v, haelfte) -> Anzahl Preispunkte im 12-h-Fenster (max. 72)
    mitte05 = defaultdict(int)  # Buckets mit Preis exakt 0,5
    gesamt = defaultdict(int)
    for e in test_events():
        z = preise.get(e["slug"])
        if not z:
            continue
        h = "finden" if e["ziel"] <= "2026-06-30" else "bestaetigen"
        for v in (1, 2):
            pr = [z["tok"].get(m["token"], {}).get(str(v)) for m in e["maerkte"]]
            if all(p is not None for p in pr):
                summen[(v, h)].append(sum(p[1] for p in pr))
            if e["start"]:
                alter[(v, h)].append((z["td"][str(v)] - ts(e["start"])) / 3600)
            for p in pr:
                if p is not None:
                    gesamt[(v, h)] += 1
                    punkte[(v, h)].append(p[2])
                    if abs(p[1] - 0.5) < 1e-9:
                        mitte05[(v, h)] += 1
    print("Summe der Ja-Preise je Event (sollte ca. 1,0 sein): V, Haelfte, Events, Median, Mittel, 10./90. Perzentil")
    for k in sorted(summen):
        s = sorted(summen[k])
        print(k, len(s), round(st.median(s), 3), round(st.mean(s), 3), round(s[len(s) // 10], 3), round(s[len(s) * 9 // 10], 3))
    print("\nAlter des Marktes am Entscheidungszeitpunkt in Stunden (negativ = Markt noch nicht eröffnet): Median, 10. Perzentil, Anteil < 3 h")
    for k in sorted(alter):
        a = sorted(alter[k])
        print(k, len(a), round(st.median(a), 1), round(a[len(a) // 10], 1), round(sum(1 for x in a if x < 3) / len(a), 3))
    print("\nPreispunkte im 12-h-Fenster (max. 72): Median; Anteil Buckets mit Preis exakt 0,5")
    for k in sorted(punkte):
        print(k, int(st.median(punkte[k])), round(mitte05[k] / gesamt[k], 4))


if __name__ == "__main__":
    main()
