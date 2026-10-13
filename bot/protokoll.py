"""Live-Protokoll (Phase 1a): ein Lauf = ein Schnappschuss. KEINE Wetten, KEIN Papierhandel.

Je Lauf (nacheinander, nie parallel):
  1. alle aktiven Wettermärkte: Bid/Ask/Tiefe/letzter Preis + Gebührenregel (Stammdaten nur als Differenz bei Änderung)
  2. Ensemble je Station, aber nur für Modelle mit neuem Modelllauf (alle Mitglieder-Tageswerte)
  3. Bucket-Wahrscheinlichkeiten, wenn sich das Ensemble geändert hat
  4. täglich: METAR-Tageswert und Polymarket-Gewinner je abgelaufenem Markt
  5. Laufzeit-Log mit Dauer, Lücke zum Vorlauf, Abfragezählern und Größen

Alle Abrufe teilen sich EINE Frist (`ZEITBUDGET_S`, siehe bot.netz), damit der Job sein Limit nie reißt.

Aufruf:  python -m bot.protokoll [--daten daten] [--aufloesung]
"""
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from bot import aufloesung, ensemble, maerkte, netz, speicher
from bot.stationen import STATIONEN

ZEITBUDGET_S = 11 * 60  # Job-Limit 15 min inklusive Einrichtung und Commit/Push
OM_TAGESLIMIT = 4000  # eigene Obergrenze für das GESCHÄTZTE Open-Meteo-Gewicht/Tag (Summe angefragter Modelle)
PAUSE_S = 2.0  # zwischen Ensemble-Abrufen (Minutenlimit)
MAX_VERSUCHE_UNVOLLSTAENDIG = 3  # danach gilt ein zu ≥ 90 % erfasster Modelllauf als erledigt
MIN_ERFOLGSQUOTE = 0.9
AUFLOESUNG_AB_STUNDE_UTC = 7
AUFLOESUNG_ABSTAND = timedelta(hours=12)
AUFLOESUNG_RUECKBLICK_TAGE = 6
OFFEN_MAX_TAGE = 60  # so lange wird ein noch nicht entscheidbares Event nachverfolgt

STAMM_SPALTEN = [
    "idx", "gesehen_utc", "markt_id", "token_yes", "event_slug", "stadt", "station", "quelle", "art",
    "datum", "einheit", "rundung", "bucket", "bucket_lo", "bucket_hi", "tick", "min_groesse",
    "fees_aktiv", "fee_typ", "fee_rate", "fee_exponent", "fee_nur_taker", "fee_rebate", "ende_utc",
]
# Merkmale, deren Änderung eine neue Stammzeile (neuer idx) erzeugt
VERSION_SPALTEN = ["markt_id", "token_yes", "bucket", "tick", "min_groesse", "fees_aktiv", "fee_typ",
                   "fee_rate", "fee_exponent", "fee_nur_taker", "fee_rebate", "ende_utc"]
SNAP_SPALTEN = ["idx", "bid", "ask", "bid_groesse", "ask_groesse", "letzter_preis", "preis_mitte", "spread"]
PROB_SPALTEN = ["idx", "p_modell", "n_member", "laeufe", "verfuegbar_ab_utc"]
LAUF_SPALTEN = [
    "lauf_start_utc", "lauf_ende_utc", "dauer_s", "luecke_min", "status", "events", "maerkte", "neue_stammzeilen",
    "ensemble_modelle_neu", "ensemble_stationen_ok", "ensemble_fehler", "om_anfragen", "om_gewicht",
    "om_gewicht_heute", "om_meta_anfragen", "wahrscheinlichkeiten", "aufloesung_neu", "aufloesung_abweichungen",
    "aufloesung_offen", "daten_mb", "git_pack_mb", "fehler",
]


class LiveApi:
    """Echte Abrufe; in Tests durch eine Attrappe mit denselben Methoden ersetzt."""

    def events(self):
        return maerkte.hole_events()

    def buecher(self, tokens):
        return maerkte.hole_buecher(tokens)

    def modellinfo(self, jetzt):
        return ensemble.hole_modellinfo(jetzt=jetzt)

    def ensemble(self, station, modelle):
        return ensemble.hole_ensemble(station, modelle)

    def geschlossene(self, von, bis):
        return list(aufloesung.geschlossene_events(von, bis))

    def event(self, slug):
        liste = aufloesung.get_json("https://gamma-api.polymarket.com/events", {"slug": slug}, timeout=60)
        return liste[0] if liste else None

    def obs(self, icao, von, bis):
        return aufloesung.iem_messwerte(icao, von, bis)

    def hko(self, art, jahr, monat):
        return aufloesung.hko_tageswerte(art, jahr, monat)


def _s(x) -> str:
    return "" if x is None else str(x)


def aktualisiere_stamm(ordner: Path, hhmm: str, zeilen: list[dict], gesehen_iso: str) -> tuple[list[dict], dict[str, int], int]:
    """Stamm = Verzeichnis aller Marktversionen des Tages (Dateien maerkte_stamm_*.csv.gz, je Lauf nur die
    Differenz). Rückgabe: (alle Stammzeilen, token -> aktueller idx, Anzahl neuer Zeilen). Ändert sich eine
    Gebührenregel o. Ä., entsteht eine neue Zeile mit neuem idx."""
    stamm = []
    for f in sorted(ordner.glob("maerkte_stamm_*.csv.gz")):
        stamm += speicher.lies_csv_gz(f)
    for z in stamm:
        z["idx"] = int(z["idx"])
    index: dict[tuple, int] = {tuple(_s(z[c]) for c in VERSION_SPALTEN): z["idx"] for z in stamm}
    naechster = max((z["idx"] for z in stamm), default=-1) + 1
    neu_zeilen = []
    token_idx: dict[str, int] = {}
    for z in zeilen:
        key = tuple(_s(z[c]) for c in VERSION_SPALTEN)
        if key not in index:
            index[key] = naechster
            row = {c: z.get(c) for c in STAMM_SPALTEN}
            row.update(idx=naechster, gesehen_utc=gesehen_iso)
            stamm.append(row)
            neu_zeilen.append(row)
            naechster += 1
        token_idx[z["token_yes"]] = index[key]
    if neu_zeilen:  # nur die Differenz: spart Repo-Platz (Token-Kennungen komprimieren schlecht)
        speicher.schreibe_csv_gz(ordner / f"maerkte_stamm_{hhmm}.csv.gz", STAMM_SPALTEN, neu_zeilen)
    return stamm, token_idx, len(neu_zeilen)


def schnappschuss(ordner: Path, hhmm: str, zeilen: list[dict], token_idx: dict[str, int]) -> int:
    rows = []
    for z in zeilen:
        r = {c: z.get(c) for c in SNAP_SPALTEN}
        r["idx"] = token_idx[z["token_yes"]]
        rows.append(r)
    speicher.schreibe_csv_gz(ordner / f"maerkte_{hhmm}.csv.gz", SNAP_SPALTEN, rows)
    return len(rows)


def git_pack_mb() -> float | None:
    try:
        out = subprocess.run(["git", "count-objects", "-v"], capture_output=True, text=True, timeout=30).stdout
        kb = sum(int(l.split(":")[1]) for l in out.splitlines() if l.split(":")[0] in ("size", "size-pack"))
        return round(kb / 1024, 2)
    except (OSError, ValueError, subprocess.SubprocessError, IndexError):
        return None


def om_gewicht_heute(ordner: Path) -> int:
    return sum(int(float(z.get("om_gewicht") or 0)) for z in speicher.lies_csv(ordner / "laufzeit.csv"))


def _naechste_mitternacht_utc(jetzt: datetime) -> str:
    return (jetzt + timedelta(days=1)).replace(hour=0, minute=5, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensemble_phase(api, ordner: Path, hhmm: str, jetzt: datetime, zustand: dict, bis: float, info: dict) -> bool:
    """True, wenn neue Ensemble-Daten gespeichert wurden (dann Wahrscheinlichkeiten neu rechnen).

    Eine Station zählt nur als erfasst, wenn für JEDES angefragte Modell verwertbare Werte
    gespeichert wurden. Ein Modelllauf gilt erst als erledigt (zustand.json), wenn alle Stationen
    erfasst sind, oder nach MAX_VERSUCHE_UNVOLLSTAENDIG Versuchen zu ≥ 90 %."""
    jetzt_iso = jetzt.strftime("%Y-%m-%dT%H:%M:%SZ")
    if zustand.get("om_gesperrt_bis", "") > jetzt_iso:
        info["fehler"].append(f"Ensemble pausiert (Open-Meteo-Tageslimit bis {zustand['om_gesperrt_bis']})")
        return False
    modellinfo = api.modellinfo(jetzt)
    aktuell = {m: v["lauf"] for m, v in modellinfo.items()}
    info["om_meta_anfragen"] = sum(len(c["meta"]) for c in ensemble.MODELLE.values())
    neu = ensemble.neue_modelle(aktuell, zustand["modelle"])
    info["ensemble_modelle_neu"] = "+".join(neu)
    if not neu:
        return False
    stationen = list(STATIONEN.items())
    abruf_iso = jetzt_iso
    rohdaten = []  # (stadt, station, antwort, empfangen_iso)
    for stadt, st in stationen:
        if time.monotonic() > bis or info["om_gewicht_heute"] >= OM_TAGESLIMIT:
            info["fehler"].append("Ensemble: Zeitbudget oder Tagesgewicht erreicht")
            break
        try:
            ant = api.ensemble(st, neu)
            rohdaten.append((stadt, st, ant, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))
        except netz.TageslimitFehler:
            zustand["om_gesperrt_bis"] = _naechste_mitternacht_utc(jetzt)
            info["fehler"].append("Ensemble: Open-Meteo-Tageslimit gemeldet, Pause bis Mitternacht UTC")
            break
        except RuntimeError as e:
            info["fehler"].append(f"Ensemble {stadt}: {str(e)[:60]}")
            if isinstance(e, netz.ZeitbudgetFehler):
                break
        info["om_anfragen"] += 1
        info["om_gewicht"] += len(neu)
        info["om_gewicht_heute"] += len(neu)
        time.sleep(min(PAUSE_S, max(0.0, bis - time.monotonic())))
    nach = api.modellinfo(jetzt)  # Lauf zwischen Meta-Abfrage und Abruf veröffentlicht?
    sicher = {m: modellinfo[m]["reif"] and nach.get(m, modellinfo[m])["lauf"] == modellinfo[m]["lauf"] for m in neu}
    details = {m: modellinfo[m]["details"] for m in neu}
    zeilen, ok_stationen = [], 0
    for stadt, st, ant, empf in rohdaten:
        z = ensemble.zeilen_fuer_station(stadt, st, ant, neu, aktuell, sicher, abruf_iso, empf, details)
        if {r["modell"] for r in z} == set(neu):  # verwertbare Werte für jedes angefragte Modell
            ok_stationen += 1
        else:
            info["fehler"].append(f"Ensemble {stadt}: leere oder unvollständige Antwort")
        zeilen += z
    if zeilen:
        speicher.schreibe_csv_gz(ordner / f"ensemble_{hhmm}.csv.gz", ensemble.SPALTEN_ENSEMBLE, zeilen)
    info["ensemble_stationen_ok"] = ok_stationen
    info["ensemble_fehler"] = len(stationen) - ok_stationen
    schluessel = ";".join(f"{m}@{aktuell[m]}" for m in sorted(neu))
    versuche = zustand.setdefault("versuche", {})
    n_versuche = versuche.get(schluessel, 0) + 1
    vollstaendig = ok_stationen == len(stationen)
    if vollstaendig or (ok_stationen >= MIN_ERFOLGSQUOTE * len(stationen) and n_versuche >= MAX_VERSUCHE_UNVOLLSTAENDIG):
        zustand["modelle"].update({m: aktuell[m] for m in neu})
        zustand["versuche"] = {}
        if not vollstaendig:
            info["fehler"].append(f"Ensemble nach {n_versuche} Versuchen nur {ok_stationen}/{len(stationen)} Stationen: abgeschlossen")
    else:
        versuche[schluessel] = n_versuche
        info["fehler"].append(f"Ensemble unvollständig ({ok_stationen}/{len(stationen)}), Versuch {n_versuche}: wird wiederholt")
    return bool(zeilen)


def wahrscheinlichkeits_phase(wurzel: Path, ordner: Path, hhmm: str, heute: str,
                              stamm: list[dict], aktuelle_idx: set[int]) -> int:
    ens = []
    for tag in ensemble.tage_zurueck(heute, 1):
        d = wurzel / tag
        if d.exists():
            for f in sorted(d.glob("ensemble_*.csv.gz")):
                ens += speicher.lies_csv_gz(f)
    member = ensemble.juengste_member(ens)
    aktuell = [z for z in stamm if z["idx"] in aktuelle_idx]
    rows = ensemble.wahrscheinlichkeiten(aktuell, member)
    if rows:
        speicher.schreibe_csv_gz(ordner / f"wahrscheinlichkeiten_{hhmm}.csv.gz", PROB_SPALTEN, rows)
    return len(rows)


def aufloesung_faellig(zustand: dict, jetzt: datetime, erzwingen: bool) -> bool:
    if erzwingen:
        return True
    if jetzt.hour < AUFLOESUNG_AB_STUNDE_UTC:
        return False
    letzte = zustand.get("aufloesung_letzte")
    return not letzte or jetzt - datetime.fromisoformat(letzte) >= AUFLOESUNG_ABSTAND


def aufloesung_phase(api, wurzel: Path, jetzt: datetime, info: dict, zustand: dict | None = None) -> None:
    """Erfasst entschiedene Events. Noch nicht entscheidbare (HKO-Wert fehlt, METAR-Ausfall, Gewinner offen)
    stehen dauerhaft in zustand['aufloesung_offen'] (Slug -> Datum) und werden unabhängig vom Rückblickfenster
    erneut geprüft, höchstens OFFEN_MAX_TAGE lang."""
    zustand = zustand if zustand is not None else {}
    offen_alt: dict = zustand.setdefault("aufloesung_offen", {})
    heute = jetzt.date().isoformat()
    von = (jetzt - timedelta(days=AUFLOESUNG_RUECKBLICK_TAGE)).date().isoformat()
    bereits = set()
    for tag in ensemble.tage_zurueck(heute, AUFLOESUNG_RUECKBLICK_TAGE + 1):
        bereits |= {z["event_slug"] for z in speicher.lies_csv_gz(wurzel / tag / "aufloesung.csv.gz")}
    events = api.geschlossene(von, heute)
    im_fenster = {e["slug"] for e in events}
    grenze = (jetzt - timedelta(days=OFFEN_MAX_TAGE)).date().isoformat()
    for slug, datum in list(offen_alt.items()):
        if datum < grenze or slug in bereits:
            del offen_alt[slug]
        elif slug not in im_fenster:
            try:
                ev = api.event(slug)
            except RuntimeError:
                ev = None
            if ev:
                events.append(ev)
    rows = aufloesung.pruefe_events(events, jetzt.strftime("%Y-%m-%dT%H:%M:%SZ"), bereits,
                                    hole_obs=api.obs, hole_hko=api.hko)
    offen = [r for r in rows if r.get("_offen")]
    final = [r for r in rows if not r.get("_offen")]
    erfasst = {r["event_slug"] for r in rows}
    for r in final:
        offen_alt.pop(r["event_slug"], None)
    for r in offen:
        offen_alt[r["event_slug"]] = r["datum"]
    for e in events:  # geschlossen, aber Gewinner noch nicht lesbar: ebenfalls vormerken
        m = aufloesung.SLUG.match(e["slug"])
        if m and e["slug"] not in bereits and e["slug"] not in erfasst and aufloesung.gewinner_titel(e) is None:
            offen_alt.setdefault(e["slug"], e["endDate"][:10])
    info["aufloesung_offen"] = len(offen_alt)
    info["aufloesung_neu"] = len(final)
    info["aufloesung_abweichungen"] = sum(1 for r in final if r.get("treffer") == 0)
    if final:
        pfad = speicher.tagesordner(heute, wurzel) / "aufloesung.csv.gz"
        alt = speicher.lies_csv_gz(pfad)
        speicher.schreibe_csv_gz(pfad, aufloesung.SPALTEN_AUFLOESUNG, alt + final)


def lauf(api, wurzel: Path, jetzt: datetime, aufloesung_erzwingen: bool = False) -> int:
    start = time.monotonic()
    bis = start + ZEITBUDGET_S
    netz.setze_frist(bis)
    try:
        return _lauf(api, wurzel, jetzt, aufloesung_erzwingen, start, bis)
    finally:
        netz.setze_frist(None)


def _lauf(api, wurzel: Path, jetzt: datetime, aufloesung_erzwingen: bool, start: float, bis: float) -> int:
    heute = jetzt.date().isoformat()
    hhmm = jetzt.strftime("%H%M")
    ordner = speicher.tagesordner(heute, wurzel)
    zustand = speicher.lies_json(wurzel / "zustand.json", {})
    zustand.setdefault("modelle", {})
    info = {"lauf_start_utc": jetzt.strftime("%Y-%m-%dT%H:%M:%SZ"), "status": "OK", "om_anfragen": 0, "om_gewicht": 0,
            "om_gewicht_heute": om_gewicht_heute(ordner), "fehler": []}
    if zustand.get("letzter_start"):
        info["luecke_min"] = round((jetzt - datetime.fromisoformat(zustand["letzter_start"])).total_seconds() / 60, 1)
    exit_code = 0
    stamm, aktuelle_idx = [], set()
    try:
        events = api.events()
        min_datum = (jetzt - timedelta(days=2)).date().isoformat()
        kand = [e for e in events if maerkte._event_kopf(e) and maerkte._datum(e) >= min_datum]
        tokens = [json.loads(m["clobTokenIds"])[0] for e in kand for m in e.get("markets", [])
                  if m.get("clobTokenIds")]
        buecher = api.buecher(tokens)
        zeilen = maerkte.zeilen_aus_events(kand, jetzt, buecher, min_datum)
        if not zeilen:
            raise RuntimeError("keine Marktzeilen")
        stamm, token_idx, neu = aktualisiere_stamm(ordner, hhmm, zeilen, jetzt.strftime("%Y-%m-%dT%H:%M:%SZ"))
        info.update(events=len(events), maerkte=schnappschuss(ordner, hhmm, zeilen, token_idx),
                    neue_stammzeilen=neu)
        aktuelle_idx = set(token_idx.values())
    except Exception as e:  # noqa: BLE001 - Protokoll muss den Fehler festhalten statt abzustürzen
        info["status"] = "FEHLER_MAERKTE"
        info["fehler"].append(f"Märkte: {type(e).__name__}: {str(e)[:100]}")
        exit_code = 1

    if exit_code == 0:
        try:
            if ensemble_phase(api, ordner, hhmm, jetzt, zustand, bis, info):
                info["wahrscheinlichkeiten"] = wahrscheinlichkeits_phase(wurzel, ordner, hhmm, heute, stamm, aktuelle_idx)
        except Exception as e:  # noqa: BLE001
            info["fehler"].append(f"Ensemble: {type(e).__name__}: {str(e)[:100]}")
            info["status"] = "TEILFEHLER"
        try:
            if aufloesung_faellig(zustand, jetzt, aufloesung_erzwingen):
                aufloesung_phase(api, wurzel, jetzt, info, zustand)
                zustand["aufloesung_letzte"] = jetzt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        except Exception as e:  # noqa: BLE001
            info["fehler"].append(f"Auflösung: {type(e).__name__}: {str(e)[:100]}")
            info["status"] = "TEILFEHLER"
    if info["status"] == "OK" and any("unvollständig" in f or "Zeitbudget" in f or "pausiert" in f for f in info["fehler"]):
        info["status"] = "TEILFEHLER"

    ende = datetime.now(timezone.utc)
    zustand["letzter_start"] = jetzt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    speicher.schreibe_json(wurzel / "zustand.json", zustand)
    info.update(lauf_ende_utc=ende.strftime("%Y-%m-%dT%H:%M:%SZ"), dauer_s=round(time.monotonic() - start, 1),
                daten_mb=speicher.groesse_mb(wurzel), git_pack_mb=git_pack_mb(), fehler=" | ".join(info["fehler"]))
    speicher.haenge_csv_an(ordner / "laufzeit.csv", LAUF_SPALTEN, info)
    print({k: info.get(k) for k in ("lauf_start_utc", "status", "dauer_s", "maerkte", "ensemble_modelle_neu",
                                    "om_gewicht_heute", "aufloesung_neu", "daten_mb", "fehler")})
    return exit_code


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--daten", default="daten")
    ap.add_argument("--aufloesung", action="store_true", help="Auflösungsprüfung jetzt erzwingen")
    a = ap.parse_args(argv)
    return lauf(LiveApi(), Path(a.daten), datetime.now(timezone.utc), a.aufloesung)


if __name__ == "__main__":
    sys.exit(main())
