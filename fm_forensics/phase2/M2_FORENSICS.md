# M2_FORENSICS — what M2 is, what it measures, and whether it is causal (2026-10-08)

## 1. What M2 is in code (`analyze_ticker`, `Super_stock.py:4055–4073`)
```
hi52     = High.tail(252).max()            # on the bars as delivered (TradingView, adjustment=splits)
drop_pct = (1 - price/hi52) * 100
drop_pct > MAX_DROP_PCT (99.95)  → reject  M2_هبوط_فوق_97
drop_pct < MIN_DROP_FLOOR (71.72)→ reject  M2_هبوط_تحت_40
```
The two split-aware branches (`BT_SPLIT_AWARE_M2`, `BT_SPLIT_REF_M2`) are **backtest-only**: in production `_BT_SPLITS_CTX is None`, so neither executes. Both thresholds are catalog-envelope numbers (`FAISAL_ONLY=1`, P100 edges measured on bot-adjusted histories of Faisal's stocks — `FAISAL_SOURCE_LEDGER.md`: `inferred`).

## 2. Which of the §8 categories M2 belongs to (tested, not assumed)
| Candidate meaning | Test | Result |
|---|---|---|
| a security identity | ID world (same bars, other ticker): 26,769 rows, 0 differences | **not identity** |
| a historical price regime | hi52 on adjusted data spans pre-split regimes; SXTC hi52 = 83,758 (4 reverse splits, ×1.2M cumulative), HUBC 742,500–1,038,712 (6 splits) | **yes — it is a regime quantity** |
| a chart anchor | Faisal's chart anchors for split names are the first post-split open/high and ÷2 (TG_1811, TG_1813, TG_1807, TG_1824, TG_2200, IMG_0291, TG_1958) — never a 52-week high | **not Faisal's chart anchor** |
| a pattern reference | the catalog "collapse ≥ 71.7% from the cycle top" | yes for non-split names; for split names the "top" is the adjusted pre-split regime | partial |
| an adjusted-data artifact | B_RAW world removes the ceiling for 186 of 190 ceiling rows; B_PSH for 190/190 | **the ceiling failure is an artifact of cumulative adjustment**; the floor failure under B_PSH is the mirror artifact |
| a state variable | no memory; recomputed daily | not a state |

**Conclusion:** M2 = a historical-price-regime filter computed on provider-adjusted data; its two thresholds encode the catalog envelope of Faisal's stocks *as seen through the same adjusted lens*. It is neither identity nor Faisal's reference frame.

## 3. Who hits the M2 ceiling (world A, 20 scan dates, 232 probe symbols)
| Group | symbols | ceiling rows | share of rows |
|---|---|---|---|
| anchors SXTC, HUBC | 2 | 40 | 100% of their days |
| other symbols with a reverse split inside the 252-bar window | 10 (ELPW, LRHC, NIVF, PAVS, PFSA, RUBI, SMX, WHLR, YYAI, ZNB) | 156 | — |
| all 135 symbols with a reverse split in the window | 12 of 135 hit the ceiling at all | — | **the ceiling is a minority outcome of reverse splits** |
| symbols with no split in the window | 0 | 0 | — |
Necessity (does an identity/continuity issue force the failure?): **no** — 56 reverse-split symbols pass M1–M5 under A on ≥ 1 day (296 PASS rows), including Faisal names AMIX, AZI, DSY, EHGO, ELAB, ERNA, EZRA, LNAI, NUWE, SNAL, SPRC, STKH, WNW (`NEGATIVE_CONTROL_RESULTS.csv`). The ceiling needs *compounded* splits (products of ratios ≥ ~10³–10⁶) inside the window, not a split per se.

## 4. Sufficiency (does correcting the regime restore candidacy?)
| World | Ceiling rows (190) become | Candidates restored |
|---|---|---|
| B_PSH (M2 reference = post-split high; production flag) | M2 floor 145 · M4 30 · M3 20 · anchor 1 | **0** |
| B_RAW (unadjusted prices) | anchor 104 · M4 35 · M2 floor 34 · M1 9 · ceiling 4 · **PASS 10** (PAVS ×5, RUBI ×2, ZNB ×3) | 10 rows, 3 symbols, none an anchor |
| B_CUT (history starts at the split) | TOO_FEW_BARS 186 | 0 (MIN_BARS=120) |
| SXTC / HUBC specifically | B_PSH → floor / M4 / anchor; B_RAW → floor / M4 / anchor; B_CUT → too few bars | **0 candidate-days in any world** |
**Correcting the regime does not restore the anchors; it moves them to the next gate.** Worse, the post-split reference (B_PSH) *removes* candidacy from 33 of the 56 negative controls (296 → 140 PASS rows) and turns 46 of 52 independent Faisal WAIT cases into `M2_هبوط_تحت_40`.

## 5. Independent Faisal-dated cases (70 pairs, 63 non-anchor; world A on the decision day; `FAISAL_DATED_REPLAY.csv`)
| Faisal decision | n | bot candidate | anchor rule | M3 | M4 | M2 ceiling | M2 floor | depth |
|---|---|---|---|---|---|---|---|---|
| READY | 5 | 0 | 4 | 0 | 0 | 0 | 1 | 0 |
| WATCH | 6 | 0 | 0 | 4 | 1 | 0 | 0 | 1 |
| WAIT | 52 | 4 | 23 | 14 | 9 | 2 | 0 | 0 |
| REJECT | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
On Faisal's own dated decisions, the M2 ceiling is the first wall in **2 of 63** cases; the two-touch anchor rule in **27**, M3 in **18**, M4 in **11**.

## 6. Causal classification of M2
- M2 ceiling → SXTC/HUBC rejection: **Level 5 for the mechanism** (replicated across worlds, 20 sessions, 2 anchors + 10 controls: cumulative-split adjustment inflates hi52 above 99.95%).
- M2 ceiling → "the bot misses Faisal-focused stocks": **Level 2 (plausible contributor)** — it is the first wall for 2 anchors but for only 2/63 independent Faisal cases; and removing it (any world) does not produce a candidate for any anchor.
- M2 as the "heavy discovery" of Phase 1: **downgraded**. The heavier, generalized fact is that the identity gates (M2 band, M3 spike floor, M4 base range, two-touch anchor) are all evaluated on the provider's adjusted regime and on bot-defined windows, while Faisal's reference frame starts at the split and his readiness is a lifecycle state — a Layer C vs Layer D mismatch of which the M2 ceiling is one visible symptom.
