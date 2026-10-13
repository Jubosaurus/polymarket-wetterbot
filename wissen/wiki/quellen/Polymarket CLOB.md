---
typ: quelle
tags: [quelle, polymarket]
stand: 2026-10-13
---
# Polymarket CLOB (lesend)

Orderbuch und Preisverlauf: `https://clob.polymarket.com`. Kein Schlüssel für lesende Aufrufe. **Orders** brauchen Signatur/Wallet und werden in diesem Projekt nie genutzt (siehe [[Arbeitsregeln]]).

## Aufrufe

- `POST /books` mit `[{"token_id": …}, …]`: Batch (100 Tokens je Aufruf getestet). Liefert `bids`, `asks` (Preis, Größe), `tick_size`, `min_order_size`, `last_trade_price`, `timestamp` (ms).
- `GET /book`, `GET /spread`, `GET /fee-rate` (`base_fee: 1000`, nicht maßgeblich für die Rechnung).
- `GET /prices-history?market=<token_yes>&startTs=…&endTs=…&fidelity=<Minuten>`.

## prices-history für geschlossene Märkte

- `interval=max` und `interval=1d` liefern für **geschlossene Märkte eine leere Liste**. Nur mit **expliziten `startTs`/`endTs`** kommen Daten.
- `fidelity=1` (Minute) geht (ca. 4 000 Punkte pro Markt über 3 Tage), 5/10/60 auch.
- Reichweite: bis zum ersten Markt (2025-12-28). Nur **Preispunkte**, kein historischer Spread und kein Orderbuch.
- Durchsatz: 20 Aufrufe nacheinander in 10 s ohne Fehler. Alle 153 000 Märkte wären etwa 21 Stunden, daher Stichprobe ([[Rückrechnung Machbarkeit]]).

## Marktparameter

Tick 0,001 bei Preisen nahe 0 bzw. 1, sonst 0,01. Mindestgröße 5 (Einheit unklar, siehe [[Polymarket Gebühren]]). Medianliquidität ca. 1 400 $ je Bucket.

Siehe auch [[Polymarket Gamma]].
