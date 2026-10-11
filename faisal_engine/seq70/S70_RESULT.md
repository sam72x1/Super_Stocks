# SEQ70 — result

**DECISION: PROMISING_UNVALIDATED** — by the sealed rules of `S70_PREREG.md` (SHA-256 `1b511ab3…cdeb`, pinned in
`s70_eval.py`; the seal commit `974f9231e` was pushed before any validation or test row was read). One run
(`python3 faisal_engine/seq70/s70_eval.py test` → `data/result.json`). Research only: no production, Telegram,
schedule, threshold, membership, frozen-axis or closed-axis change; READY70 imported read-only; no network request.
No agents or workflows were used.

## 1. DATA_INVENTORY
As sealed (`S70_PREREG.md` §1). In short: daily bars for 3,584 symbols (2024-05-01 → 2026-10-08) · 174,796
pivot-days on 1,108 symbols in 2,738 spells (2025-05-01 → 2026-10-07) · 3,727 clean +70% episodes recomputed with the
bot's detector (95.0% match to the live `scan_explosions` log) · the bot's lists and READY flags from 2026-06-20 only ·
Faisal's dated classes for 41 tickers (4 independent pre-move units) · live alerts for 31 sessions.

## 2. PRIOR_WORK_EXCLUDED
As sealed (§3): READY70, ALERTS70, T-PRELINK, the common-link verdict, T-LINK100/-2, the two-day probe, the T-PRESS
family, T-DORMANT, T-WAKE, T-STABILITY, T-VOLBASE, T-CUMRISE, T-ACC, forensic phases 2–6 and every `CLOSED_RC` axis.

## 3. POINT_IN_TIME_COVERAGE
Pivot-days ↔ +70% episodes link exactly (same bars, same detector, labels from bars after t only). The bot's states
cover 2026-06-20 → 10-10 only and cannot carry a three-window test; Faisal's own states are too few.
**There is no data problem that prevents the test** — the gap is that the bot's state history is short, not that
pivots and events cannot be linked.

## 4. SEQUENCE_HYPOTHESIS (from discovery, 2025)
Before the start of a +70% move every path descriptor sits at chance until two sessions before it; at L−2/L−1
volume and daily range rise while price is still pressed (E2). The carried sequence: **volume arrives while the
5-session price path is still down** — a pivot-day with `r5` < 0 and `v1x` in the session's top quintile (H-S70).
Balanced discovery estimate: K-V 1.134 [0.92, 1.40], K-P 1.083 [0.86, 1.38] (95%) — below the bar; carried with a
written prediction of no edge.

## 5. PRE_REGISTERED_TEST
K-V: flagged vs same-session, same-price-bucket pivot-days with the same 5-session drop and 20-session range (within
0.10 percentile) but no top-quintile volume. K-P: flagged vs the same volume and range but a 5-session return ≥ 0.
f10 = the bot's +70% condition within 10 sessions after the close. Ticker-cluster bootstrap, 2,000 resamples,
98.75% per window; pooled out-of-sample 95%.

## 6. RESULTS_AND_BASELINE

| | validation 2026-01-16 → 05-15 | test 2026-06-02 → 09-24 | pooled (95%) |
|---|---|---|---|
| clean evaluable pivot-days · base f10 rate | 33,604 · 4.34% | 36,369 · 4.27% | |
| flagged evaluable · f10 rate | 3,756 · 7.77% | 4,107 · 10.15% | |
| distinct +70% events among flagged | 122 | 145 | |
| **K-V** flagged vs drop/volatility-matched | 7.23% vs 5.62% (2,919 pairs) · **1.29 [0.90, 1.82]** | 9.28% vs 5.51% (3,285) · **1.69 [1.18, 2.34]** | **1.50 [1.23, 1.80]** |
| **K-P** flagged vs volume/volatility-matched, price not down | 7.30% vs 5.62% (1,959) · **1.30 [0.83, 1.97]** | 9.35% vs 6.06% (2,246) · **1.54 [1.04, 2.16]** | **1.44 [1.14, 1.78]** |

Balance held (K-V: `r5` −12.7 vs −12.4, `range20` percentile 0.76 vs 0.76; K-P: `v1x` percentile 0.885 vs 0.886,
`range20` 0.80 vs 0.78). Floors met in both windows. Per-window lower bounds: validation both below 1.0, test both
above ⇒ not VALIDATED; pooled lower bounds both above 1.0 ⇒ **PROMISING_UNVALIDATED**.

**Timing and burden (the practical side, not decisive):**

| | validation | test |
|---|---|---|
| flagged pivot-days per session | 46.8 | 53.6 |
| flagged rows with no +70% in 10 sessions | 92.2% | 89.9% |
| trigger episodes (first flag after ≥ 5 quiet sessions) · precision · false triggers per session | 1,201 · 7.0% · 12.9 | 1,348 · 7.8% · 14.8 |
| eligible events · flagged before the +70% level · before the start | 291 · 54.0% · 48.5% | 281 · 65.1% · 52.3% |
| lead, first flag → start L (q25 / median / q75 sessions) | 1 / 5 / 9 | 1 / 4 / 9 |
| lead, first flag → start L10 (first close ≥ 10% above the trough) | 3 / 6 / 10 | 2 / 6 / 10 |
| lead, first flag → +70% crossing | 6 / 10 / 17 | 4 / 10 / 14 |
| burden-matched top volume, any price: recall before +70% · f10 rate | 62.2% · 8.47% | 72.2% · 9.91% |
| burden-matched lowest 5-session return: recall · rate | 54.6% · 8.48% | 60.1% · 8.77% |

⇒ At equal burden, simply flagging the highest-volume pivot-days of each session, whatever the price did, reaches
**more** events before +70% at about the same precision. The sequence carries information *relative to matched
pivot-days*, but it is **not a better alarm than the volume ranking it is built on.**

**Sensitivity (all reported, none chosen):** horizon 20 — validation K-V 1.16 [0.94, 1.42], K-P 1.17 [0.92, 1.46];
test K-V 1.46 [1.20, 1.79], K-P 1.29 [0.99, 1.71] (95%). Split rows included — validation 1.16 [0.91, 1.48] / 1.21
[0.89, 1.62]; test 1.59 [1.29, 1.92] / 1.45 [1.10, 1.80]. Strict label `y10`: K-P 2.75 and 3.26 — mechanical (it
penalises controls already rising), not evidence. **Period:** discovery 1.13 → validation 1.29 → test 1.69 (K-V) —
the effect grows over time and is not stable across the three windows.

**Bot states (test window, descriptive, `data/states.json`):** 1,077 flagged rows were on the bot's lists (953
«تحت المتابعة», 18 watchlist, 59 carried, 47 pullback); 104 were followed by +70%; the bot's READY was on for 39.
Across all 14,248 evaluable list-days, symbol-days followed by +70% had the same tracking age (median 12 vs 11
sessions) and the same READY share (2.9% vs 2.6%) as the rest — no list state or duration separates them.

**Predictions:** P1 ✗ (expected NO_INCREMENTAL_EDGE_FOUND) · P2 ✗ (test K-V 1.69 outside 0.9–1.3) · P3 ✓ (the
volume ranking recalls more) · P4 ✓ (median lead to +70% 10 sessions; to the start 5 and 4) · P5 ✗ in test
(89.9% without +70%, just under 90%; validation 92.2%).

## 7. LIMITATIONS
- Validation alone does not support the signal (both lower bounds below 1.0); the pooled result is driven by the
  test window, and the effect rises from discovery to test — a regime effect cannot be excluded.
- The design changed once on discovery before the seal (calipers added after the first matcher left flagged rows
  more volatile); the E4 carry-forward rule would have stopped there, and C-A was carried anyway (disclosed in the
  prereg).
- READY70 had already read the validation and test windows for other rules.
- Daily bars only: the flag is known at the close of the volume day; intraday timing is not measured.
- Volume adjustment across splits is uncertain (split rows excluded; including them gives the same direction).
- Survivorship (today's listings); bot states exist only from 2026-06-20; 9 in 10 flags are not followed by +70%.
- Guards G1–G7 pass and eight mutations each felled exactly their guard (`data/mutations.json`; a first look-ahead
  mutation survived because the descriptor function truncates the arrays at the decision bar, and was replaced by
  one that removes the truncation) — this shows the pipeline does what the contract says, not that the signal is
  real.

## 8. DECISION
**PROMISING_UNVALIDATED.** Out of sample, pivot-days where heavy volume arrives while the 5-session return is still
negative were followed by +70% about 1.4–1.5 times as often as pivot-days matched on drop and volatility, and as
pivot-days with the same volume whose price was not down (pooled 95% lower bounds 1.23 and 1.14). It did not hold in
the validation window on its own, it grows over time, and as an alarm it is no better than ranking pivot-days by
volume alone (higher recall at the same precision, about 50 flags per session, 9 in 10 false). It is not a READY NOW
rule. The next evidence must be prospective: a sealed forward record of the flag from today, with no rule change.

## 9. Files
`s70_build.py` (`--check`) · `s70_explore.py` (discovery only) · `s70_eval.py` (`dev` discovery dry run · `test`
sealed) · `s70_states.py` (bot states, descriptive) · `test_s70.py` (G1–G7) · `s70_mutate.py` · data:
`traj.csv.gz`, `events.csv.gz`, `inventory.json`, `explore.json`, `dev_discovery.json`, `result.json`,
`states.json`, `mutations.json`.
