---
typ: experiment
tags: [experiment, aufloesung, hongkong]
stand: 2026-10-13
---
# Hongkong: Abschneiden statt Runden

Test: 62 Hongkong-Märkte (August 2026), HKO-Tageswerte (`CLMMAXT`/`CLMMINT`, [[HKO Open Data]]) mit drei Regeln gegen den Gewinner-Bucket:

| Regel | Treffer |
|---|---|
| **Abschneiden** (28,9 → 28) | **62 / 62** |
| Kaufmännisch runden | 29 / 62 |
| Banker-Rundung (Python `round`) | 31 / 62 |

Beschluss: Hongkong-Station mit `rundung = abschneiden` ([[Hongkong]], [[Rundung und Auflösung]]). Die Beschreibung im Markt sagt nur „eine Nachkommastelle“ und nennt die Regel nicht.
