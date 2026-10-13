# Polymarket-Gebühren (Wettermärkte)

Geprüft am **2026-10-13** gegen die offizielle Dokumentation und gegen die API-Antworten der Wettermärkte.

## Quellen

- Gebührenformel und Tabellen: <https://docs.polymarket.com/trading/fees>
- Gebührenfelder im Markt-Objekt: <https://docs.polymarket.com/market-data/market-details> (Abschnitt „Trading Fees“)
- Live-Werte: Gamma-API `GET /events` bzw. `/events/keyset`, Felder je Markt (`feesEnabled`, `feeType`, `feeSchedule`)

## Formel (offiziell)

```
fee = C × feeRate × p × (1 − p)
```

- `C` = Anzahl gehandelter Anteile, `p` = Preis eines Anteils (0 bis 1)
- **Nur der Taker zahlt.** Maker zahlen nie Gebühren (Maker-Rate 0).
- Gebühr in USDC; symmetrisch um 50 %: ein Kauf bei 0,30 kostet dieselbe Gebühr wie bei 0,70. Maximum bei p = 0,5.
- Rundung: **5 Nachkommastellen**, kleinste Gebühr 0,00001 USDC; Kleineres wird zu 0.
- Maker-Rebate: Teil der Taker-Gebühren wird täglich an Maker zurückverteilt (Programm „Maker Rebates“). Takern steht ein gestuftes „Taker Rebate Program“ offen (nicht untersucht).

**Kategorie Wetter:** Taker-Rate **0,05**, Maker-Rate 0, Maker-Rebate **25 %**.

Beispiel (offizielle Tabelle „Economics / Culture / Weather / Other“, 100 Anteile):

| Preis | Handelswert | Taker-Gebühr (USDC) |
|---|---|---|
| 0,05 | 5 $ | 0,24 |
| 0,10 | 10 $ | 0,45 |
| 0,30 | 30 $ | 1,05 |
| 0,50 | 50 $ | **1,25** (Maximum) |
| 0,70 | 70 $ | 1,05 |
| 0,95 | 95 $ | 0,24 |

Nachrechnung: 100 × 0,05 × 0,5 × 0,5 = 1,25. ✔

## Was die API je Markt liefert

Beobachtet an allen aktiven Temperaturmärkten (Stand 2026-10-13):

| Feld (Gamma) | Wert | Bedeutung |
|---|---|---|
| `feesEnabled` | `true` | Gebühren aktiv |
| `feeType` | `weather_fees` | Kategorie Wetter |
| `feeSchedule.rate` | `0.05` | `feeRate` der Formel |
| `feeSchedule.exponent` | `1` | Exponent „auf die Preiskomponente“; mit 1 entspricht das der Formel oben. Bei einem anderen Wert die Formel **nicht** raten, sondern in der Doku nachsehen. |
| `feeSchedule.takerOnly` | `true` | nur Taker zahlt |
| `feeSchedule.rebateRate` | `0.25` | Maker-Rebate als Anteil der Taker-Gebühr |
| CLOB `GET /fee-rate` | `base_fee: 1000` | alte Basisangabe in Basispunkten, für die Rechnung nicht maßgeblich |

Das Protokoll (`bot/protokoll.py`) schreibt diese Felder je Marktversion in die Stammdaten (`maerkte_stamm_*.csv.gz`: `fees_aktiv`, `fee_typ`, `fee_rate`, `fee_exponent`, `fee_nur_taker`, `fee_rebate`). Ändert sich eine Regel, entsteht eine neue Stammzeile mit neuem `idx`; die Änderung ist damit datiert (`gesehen_utc`).

## Folgen für die Auswertung

- Gebühr je Anteil beim Kauf zu Preis p: `0,05 × p × (1 − p)`. Bei p = 0,40 sind das 0,012 USDC je Anteil (3 % des Preises), bei p = 0,10 0,0045 (4,5 %), bei p = 0,02 0,00098 (4,9 %).
- Die Gebühr fällt **auf Kosten und Erlös des Takers** an. Im Papierhandel muss jede Taker-Order (gegen Ask/Bid) mit dieser Gebühr belastet werden; Maker-Orders zahlen nichts, bekommen aber nicht zwingend eine Ausführung.
- Ob bei der Auflösung (Anteil läuft auf 1 oder 0 ab) eine Gebühr anfällt, steht auf der gelesenen Seite nicht; es wird als „nein“ angenommen, **nicht geprüft**.

## Offene Punkte

- Die Doku nennt `orderMinSize` in USDC, die API liefert 5 (die CLOB-Antworten nennen `min_order_size` ohne Einheit). Ob 5 Anteile oder 5 USDC gemeint sind, ist nicht geklärt. Für Mindestgrößen in der Auswertung vorsichtig mit dem höheren Wert rechnen.
- Taker-Rebate-Stufen (<https://docs.polymarket.com/programs/taker-rebates>) wurden nicht gelesen.
