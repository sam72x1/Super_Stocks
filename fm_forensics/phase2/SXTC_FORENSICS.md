# SXTC_FORENSICS (Phase 2) — identity × continuity × pipeline, first divergence (2026-10-08)

## Identity ledger (from `SECURITY_IDENTITY_LEDGER.csv`)
Ticker SXTC · TradingView `NASDAQ:SXTC` (scan map) · Yahoo `SXTC` · internal id = the ticker string · security/company ids: UNKNOWN (none in repo). Reverse splits (Yahoo ∪ Nasdaq calendar): 2021-02-22 1:4 · 2023-10-05 1:25 · 2026-02-03 1:150 · 2026-08-10 1:80 (cumulative ×1,200,000). Symbol change / merger / listing change: UNKNOWN (no source).

## Data continuity
TradingView daily bars, adjustment=splits: 443 bars from 2025-01-02; adjusted 52-week high 83,758 (pre-split regime × cumulative ratio). Bot-recorded prices (near_watch, Aug→Oct) equal TV closes 1:1 → no provider inconsistency on the post-split segment. Extended-hours 10-07: regular high 9.59; 10-08 collapse to 0.32 (−97%).

## Faisal side (chronological, DIRECT unless noted)
09-10 WA_31 READY/entry 1.80–1.90 after pressure · 09-11 X_24 exit ≈3, WAIT retest · 09-13 X_22 FOCUS list (2.56) · ≈09-20 TG_57862 WAIT · 09-24 TG_58527 target 6.31 (author inferred) · post-10-07 TG_58417/58418 re-entry 2.15–2.25 after pressure, «فوق 100% بموجتين».

## Bot side (replay world A, lookahead-safe, 20 scan dates 09-11→10-08)
`M2_هبوط_فوق_97` on every date (drop 100.0% of hi52 83,758). reject_log agrees 20/20. Never a candidate; never READY; shown in the oversold near-watch list 09-08/09 (rank 20/19); presession digests after the moves; three-conditions tool 6 sessions (09-25→10-02).

## FIRST DIVERGENCE
Faisal FOCUS (≤ 09-10) vs bot `candidate rejected` at L2 (M2 ceiling) — **before** any state. READY NOW is not the first failure.

## Counterfactuals (`IDENTITY_COUNTERFACTUAL_RESULTS.csv`)
| World | Result (20 dates) | Reading |
|---|---|---|
| ID (same bars, other label) | identical to A | identity has no effect |
| B_PSH (post-split high as M2 reference) | `M2_هبوط_تحت_40` 19 · M4 1 | drop from the 08-10 post-split high 5.55 to 1.78–2.5 = 55–68% < 71.7% floor |
| B_M4 (+ split-aware base) | same as B_PSH | — |
| B_RAW (unadjusted) | floor 18 · M4 2 | raw hi52 6.98/9.59 → 64–72% |
| B_CUT (history from 08-10) | TOO_FEW_BARS 20 | 22–42 bars < MIN_BARS 120 |
**Identity correction alone does not restore SXTC; continuity correction moves it from the ceiling to the floor.** Faisal's own reference (TG_1811: first post-split open ÷2; TG_1824: post-split high = liberation) makes SXTC's base a ~65% retrace of the post-split regime — a configuration the catalog band (71.7–99.95%) does not describe in either representation.

## Classification
Identity: REJECTED as cause (Level 0 effect). Continuity (cumulative adjustment): STRONG for the *reject code* (Level 5, replicated on 10 controls), NOT sufficient for the miss (Level 2 as explanation). First causally supported failure: **candidate-generation band evaluated on a regime Faisal does not use** (Layer C vs D).
