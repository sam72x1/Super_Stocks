# HUBC_FORENSICS (Phase 2) — technical identity/data experiment, Faisal side kept UNKNOWN (2026-10-08)

## Identity ledger
Ticker HUBC · TV `NASDAQ:HUBC` · Yahoo `HUBC` · six reverse splits: 2023-12-15 1:10 · 2025-03-31 1:10 · 2026-01-16 1:15 · 2026-04-20 1:50 · 2026-06-08 1:20 · 2026-09-14 1:25. Symbol change / listing: UNKNOWN.

## Data continuity
Bot prices before 09-15 (near_watch 0.42–0.77) are the pre-split raw prices (= TV adjusted ÷ 25); from 09-23 they equal TV closes 1:1 — the bot's own history for HUBC was rewritten by the provider at the split (consistent, not an error). Adjusted hi52 742,500–1,038,712; drop 100.0%. press_radar ledger 09-23: high 4.125 / low 3.17 / close 3.21.

## Faisal side — evidence status
TG_2098 (2026-04-24 plan, pre-split, 7% stop) is the only dated Faisal text. The 2026-10-07 chart card is the owner's (identified as HUBC by `chart_id_tv.py`, owner-confirmed key); it carries «الهدف من 3-4» but no Faisal authorship evidence. **FAISAL_STATE between 2026-04-24 and 2026-10-08 = UNKNOWN.** Future price movement is not used to infer it.

## Bot side (world A)
`M2_هبوط_فوق_97` 20/20 scan dates (reject_log agrees on 19; on 09-15 the log says M1 price — the replay with TV adjusted bars reads 7.635 while the live scan saw the raw/transition price 0.34: a provider-timing difference on the split day, recorded in `REJECT_LOG_FORENSICS.csv`). Never a candidate. Oversold near-watch list 09-30/10-01/10-02 (rank 19/17/18). Three-conditions tool 10-08: avail unknown + DQ quarantine (CORPORATE_ACTION_PENDING: ÷2 hit 10-07, held 0/3).

## Counterfactuals
B_PSH → M4 11 · M2 floor 8 · anchor 1 ; B_RAW → M4 10 · floor 8 · anchor 1 · M1 1 ; B_CUT → TOO_FEW_BARS 18 ; ID = A. **0 candidate-days in every world.** The 09-11 B_PSH/B_RAW result (anchor rule) is the pre-split base (10.2–13.0 adjusted); after the 1:25 split the post-split base is 0.9–1.0 and the base range of the 15-bar window spans the collapse (M4).

## Classification
Technical: same mechanism as SXTC (cumulative adjustment → ceiling; correction → next gate; identity no effect). Faisal-side divergence: **cannot be asserted** (no Faisal evidence) → the HUBC anchor contributes to the mechanism replication only, not to the "Faisal vs bot" divergence count.
