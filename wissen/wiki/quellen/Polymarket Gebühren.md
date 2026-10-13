---
typ: quelle
tags: [quelle, polymarket, gebuehren]
stand: 2026-10-13
---
# Polymarket-Gebühren

Offizielle Formel (geprüft 2026-10-13, <https://docs.polymarket.com/trading/fees>):

```
fee = C × feeRate × p × (1 − p)
```

Wetter: Taker-Rate **0,05**, Maker zahlen nichts, Maker-Rebate 25 %. Rundung auf 5 Nachkommastellen. Beispiel: 100 Anteile bei 0,50 → 1,25 $. API-Felder je Markt: `feesEnabled`, `feeType = weather_fees`, `feeSchedule {rate 0.05, exponent 1, takerOnly true, rebateRate 0.25}`.

Volle Herleitung, Tabelle und offene Punkte: `docs/gebuehren.md` im Repo. Folgen für die Auswertung: [[Gebühren in der Auswertung]]. Siehe auch [[Polymarket Gamma]].
