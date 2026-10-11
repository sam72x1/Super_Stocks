# READYNOW — early technical READY conditions vs the historical +70% universe

**FINAL DECISION: NO_INCREMENTAL_EDGE_FOUND** — by the sealed rules of `RN_SPEC.md` (SHA-256 `79a3b8db…a1e7`, pinned in
`rn_eval.py`; seal commit `217ba85e2` pushed and confirmed on the remote before any validation or holdout row was read).
One run: `python3 faisal_engine/readynow/rn_eval.py final` → `data/result.json`. Research only: no production,
Telegram, schedule, threshold, membership, frozen-axis or closed-axis change; READY70 and SEQ70 imported read-only;
no network request; no agents or workflows.

## 1. SOURCE_AND_RULE_AUDIT
**The three-condition tool (exact, from code, `three_cond_daily.py`):** RSI14 (Wilder, `Super_stock.rsi:1126`) below
`rsi_max()` = `S.CONFIG["RSI_OVERSOLD"]` = 33 (`three_cond_daily.py:204`, `flags3` :210) · float below
`OPL.FLOAT_OWNER` = 4,000,000 and available-to-borrow below `OPL.AVAIL_OWNER` = 20,000 (`opentry_link_probe.py:43`,
via `watch_week_probe.flags` :209 and `conj` :218; unknown stays unknown) · stability: the exact low of the last
`PIVOT_LOOKBACK` = 25 sessions from daily lows and hourly extended bars, its first day, `STABILITY_REQ` = 5 sessions
after it and the close above it (`exact_low_stability` :307, constant :103) · not exploded: within `EXPLODE_WIN` = 5
sessions no high (pre/regular, and after-hours on its own close) ≥ `EXPLOSION_PCT` = 50% above the lowest regular close
since the session before the week (`recent_explosion` :339, :105) · gate order hour-data → boom → wait (`gate_of`
:376) · price is a category ($1), not a condition · scheduled `43 1 * * 2-6`.
**Reconstructible historically:** only its technical part, `TC_TECH` = RSI < 33 ∧ hold ≥ 5 on daily lows ∧ no 50%
boom on regular highs. Float and available-to-borrow have no point-in-time series; hourly lows and after-hours highs
are not archived.

**Technical-condition images (Faisal's app «مراقب استراتيجية فيصل»; `faisal_batches/2026-10-01/EVIDENCE_REPORT.md`,
`APP_PARITY_PREREG.md`, `FAISAL_IMAGES_CATALOG.md` §ثلاثون):** score = 100 − 12 × missing technical (8) − 5 × missing
short. Verified and used: distance to the support within 15% (`TG_57917` «منطقة اختبار 0%–15%», `TG_57914`) · bounce
10–40% (`TG_57924`/`57929` «الارتداد خارج النطاق المثالي 10–40%») · MACD positive (line above signal, `TG_57917`) ·
daily stability (`TG_57913`, the count's exact rule partly unknown; 2 used) · below EMA20/30/50 (`TG_57914`,
`TG_57915`; the app's exact definition failed parity, plain reading used and labelled) · Faisal's own panel EMA 9/26
(`TG_57927`/`57928`). UNKNOWN or unobservable: «successful daily retest», daily/4-hour momentum (4-hour bars not
archived), the base-low window, and the two unnamed conditions (no source; owner: «هذي جميع الصور اللي عندي في التطبيق
فقط»). Faisal texts: `IMG_0151` hold 3 sessions · `IMG_0486` bounce 10–15% · `TG_50584` cycle (bottom → ~20% test →
hold/sweep → stability; `pivot_cycle_state` :8005) · `IMG_0297` sweep 7–13% · DRCT «rsi اقل من 30» · `IMG_6814` pivot
conditions (bottom · RSI oversold · bearish averages · high gaps · high profit).
**Exact missing paths:** `faisal_images/TG_57920.jpg` (received, not saved; catalogued as identical to `TG_50592`,
which exists) · `IMG_6814` (text record only, `FAISAL_IMAGES_CATALOG.md:161`; no image file in the repository).
**Closed and frozen axes untouched:** ANCHOR_TWO_TOUCH/H6 (READY70's `loc` reads `tested_level` read-only), M2, M3, M4,
and every `CLOSED_RC` axis; RSI is used as the tool's own READY condition, not as the screener gate of T-RSI40 nor the
ranking key of T-RSI-RANK. Not rerun: the 58-feature search, the alert comparison, the sequence experiment.

## 2. SEED_CASES_DAILY_RECONSTRUCTION
Onset rule (one, for all): L = the session after the trough close of a clean episode of the bot's explosion detector.

| seed | onset L | +70% close | Faisal timestamp (local corpus) | at T−10 … T−7 (4 days) |
|---|---|---|---|---|
| DLXY | 2026-08-31 (ignition 09-16) | 09-16 | none; raised by the owner 2026-09-26 | pivot 4/4 · hold ≥ 5 4/4 · bounce 38% · RSI 46–54 · within 15%: 0 |
| RETO | 2026-09-15 | 09-15 | none; raised by the owner 2026-09-26 | pivot 4/4 · RSI 31–36 (RSI < 33 on 1) · oversold at the low 4/4 · split ≤ 120 d 4/4 · distance 20–52% |
| SXTC | 2026-06-08 | 06-12 | READY 09-10 · ENTRY 09-11 (later move) | pivot 4/4 · RSI 31.6–35 · within 15% 4/4 · bounce 11–15% |
| SXTC | 2026-07-30 | 08-04 | — | pivot 4/4 · RSI 53–61 · EMA 9/26 up 4/4 · distance 29–62% |
| SXTC | 2026-10-07 | 10-07 | ENTRY inferred 09-24 (T−9) | **outside the pivot population (M2)** · RSI 26 4/4 · hold 9–12 · bounce 68.5% |
| DKI | **no qualifying onset** | — | FOCUS 09-13 · WAIT | 10-07 closed +22.8% after an intraday +168%; at T−10 … T−7 of it RSI 34.2 · 45.0 · 41.1 · 38.4 (the specification's «34–38» read the two ends only) |

Only «held ≥ 5 sessions above the 25-session low» and «no 50% boom in a week» hold on all five seed events, and both
are true for most pivot-days. RSI below 33 appears on SXTC-10/07 (4 of 4), SXTC-06/08 (2) and RETO (1); the tool's
technical part held on SXTC-10/07 (4), RETO (1), SXTC-06/08 (1). **The final candidate held on none of them.** Faisal's
SXTC entry inferred on 09-24 sits 9 sessions before the 10-07 onset — inside the ideal window, but outside the
pivot population. File: `data/seeds_matrix.json`.

## 3. INITIAL_READY_CANDIDATE
From development only (2025-05-01 → 2025-12-31): **RN_A = RSI14 below 30 at the close, and a bounce of 10–40% from
the 25-session low** (Faisal's RSI text + the app's bounce band). Choice rule (stated before the seal): the largest
development «beyond the tool» lower bound, burden as tie-break — RSI30 1.126 vs RN_A 1.118 (tie) → RN_A (27 vs 45
flags/session). Development: lift 1.65 [1.36, 1.94], precision 5.05%, recall 18.9% (97 of 513 events), matched 1.64
[1.16, 2.35], beyond the tool 1.65 [1.12, 2.49], vs volume ranking +2.08 pp [1.07, 3.23], **vs volatility ranking
+0.53 pp [−0.52, 1.78]** (already no better than flagging the most volatile pivot-days).
Contribution of each condition (development · validation · holdout): RSI < 30 carries the information (alone: lift
1.55 · 1.35 · 1.57); the bounce band cuts signals by 40% · 39% · 39% and false positives by 40% · 38% · 39%, loses
22% · 25% · 27% of captured events, keeps precision (5.05 vs 4.75% · 4.35 vs 4.28% · 4.40 vs 3.90%) and brings the
median first signal 2 · 2 · 2 sessions closer to the onset (12 vs 14 · 13 vs 15 · 10 vs 12).

## 4. HISTORICAL_UNIVERSE_AND_CONTROL_COVERAGE
Bars: 3,584 symbols, 2024-05-01 → 2026-10-08 (TradingView daily, split-adjusted). Pivot population: 174,796
pivot-days on 1,108 symbols (2025-05-01 → 2026-10-07). Episodes of the bot's detector: 3,842, of which 3,727 clean;
longest launch-to-detection gap 19 sessions ⇒ last label-known decision 2026-08-27. Labels overall: POS710 4,276 ·
NEG 140,229 · IN_EVENT 13,506 · UNKNOWN_SPLIT 279 · CENSORED 16,506 (never counted as negative).

| window | pivot-days | evaluable | base POS710 | clean events in window | eligible (POS710 row in T−10…T−7) | no pivot-day at T−10…T−7 |
|---|---|---|---|---|---|---|
| development | 69,794 | 63,708 | 3.06% | 1,581 | 513 | 1,020 |
| validation | 42,029 | 38,669 | 3.18% | 854 | 333 | 491 |
| holdout | 34,673 | 32,167 | 2.49% | 424 | 208 | 200 |

Only 35% · 43% · 53% of the bot's clean +70% events (development · validation · holdout) had at least one pivot-day
7–10 sessions before their onset; the rest were outside the pivot identity population (M1–M3) at that time — a
population question this mission does not reopen.
Controls: same session, same traded-price bucket, within 0.10 on the session percentiles of volume ratio, 20-session
range and median dollar volume; balance held (e.g. holdout C1: `v1x` 0.661 vs 0.661, `range20` 0.696 vs 0.695,
`dv20` 0.540 vs 0.541). Unmatched flagged rows (dropped from C1): validation 1,273 of 3,429, holdout 674 of 2,366.

## 5. MISSED_WINNERS_AND_ALTERNATIVE_STRUCTURES
Structure at the first eligible day (mutually exclusive, declared before outcomes): FRESH_LOW (low < 3 sessions old) ·
BASE_OVERSOLD (within 15% of the low, RSI < 33) · BASE_NOT_OVERSOLD · LIFTED (15–40% above) · EXTENDED (> 40%).

| structure | POS710 rate dev · val · holdout | events missed by RN_A val · holdout | caught val · holdout |
|---|---|---|---|
| FRESH_LOW | 3.42% · 3.71% · 3.00% | 74 · 53 | 46 · 28 |
| BASE_OVERSOLD | 4.00% · 4.26% · 4.16% | 6 · 2 | 13 · 10 |
| BASE_NOT_OVERSOLD | 2.81% · 2.84% · 1.74% | 60 · 29 | 1 · 2 |
| LIFTED | 2.85% · 2.60% · 2.16% | 75 · 45 | 7 · 3 |
| EXTENDED | 3.01% · 3.50% · 2.88% | 51 · 36 | 0 · 0 |

The richest structure per row is the oversold base (≈ 4% vs 2.5–3.2% base) but it is 3–4% of pivot-days; most winners
come from fresh lows, lifted and extended bases where no technical condition here separates them. Events outside the
pivot population: the candidate held at least once on 37 of 505 (validation) and 19 of 229 (holdout); the tool's part
on 9 and 12.

## 6. INDIVIDUAL_CONDITION_VALUE (development, Layer A and B; 95%)
| condition | flags/session | lift vs base | matched (price, volume, volatility, liquidity) |
|---|---|---|---|
| RSI < 30 | 45.1 | **1.55 [1.33, 1.80]** | **1.62 [1.17, 2.20]** |
| RSI < 33 | 71.7 | 1.41 [1.25, 1.59] | 1.47 [1.14, 1.91] |
| oversold at the low | 164.5 | 1.11 [1.01, 1.21] | 1.15 [0.91, 1.45] |
| hold 2 / 3 / 5 | 322 / 300 / 265 | 0.96 / 0.95 / 0.96 | 0.84 / 0.87 / 0.97 |
| within 15% | 206.1 | 1.02 [0.96, 1.09] | 1.23 [1.01, 1.49] |
| bounce 10–40% | 200.4 | 1.07 [1.00, 1.15] | 1.34 [1.11, 1.63] |
| below EMA20/30/50 | 289.7 | 1.05 [1.01, 1.09] | 1.25 [1.00, 1.55] |
| EMA 9 > 26 / cross in 5 | 100.2 / 32.8 | 0.91 / **0.75 [0.55, 0.97]** | 0.93 / **0.49 [0.28, 0.76]** |
| MACD positive | 229.2 | 0.95 [0.86, 1.02] | 0.95 [0.76, 1.16] |
| no 50% boom | 388.3 | 1.00 | — (nearly all rows) |
| reverse split ≤ 120 d | 85.2 | 1.16 [0.99, 1.34] | 1.06 [0.80, 1.41] |
| cycle stage ≥ 3 | 177.8 | 1.00 [0.92, 1.08] | 1.07 [0.86, 1.30] |

Only RSI oversold now carries information on its own; holding above the low is neutral to slightly negative; the
momentum turn is negative (fresh EMA crosses precede fewer onsets).

## 7. COMBINATION_AND_SEQUENCE_RESULTS (development)
Declared combinations: app trio (within 15% ∧ bounce 10–40% ∧ hold 2) 0.98 · oversold at the low ∧ hold 3 ∧ within 15%
1.15 [0.94, 1.38] · plus EMA/MACD turn 1.27 [0.98, 1.59] · cycle ≥ 3 ∧ within 15% 1.03 · tool ∧ fresh split 1.32 [0.69,
2.14]. **Order test:** «oversold at the low, then hold 3» 0.96 [0.84, 1.10] vs «oversold now and hold 3» 1.49 [1.16,
1.86] — the sequence adds nothing; being oversold now does. Within the tool's part, adding the app chips changes
nothing (bounce 1.09 [0.60, 2.17], within 15% 0.68 [0.39, 1.23], both 0.70 [0.37, 1.29]). The tool's part itself:
lift 1.65 [1.18, 2.15] at 13.7 flags/session — the best development combination, and not improved by any app condition.

## 8. OUT_OF_SAMPLE_READINESS_PERFORMANCE (RN_A; 97.5% per window)
| | validation 2026-01-16 → 05-15 | holdout 2026-06-02 → 08-27 |
|---|---|---|
| flags per session · triggers per session | 41.9 · 8.5 | 40.1 · 8.1 |
| precision (Wilson 95%) · base | 4.35% [3.71, 5.08] · 3.18% | 4.40% [3.64, 5.30] · 2.49% |
| lift vs base | 1.37 [0.99, 1.77] | 1.76 [1.21, 2.35] |
| recall (events) · FPR | 20.1% (67 of 333) · 8.8% | 20.7% (43 of 208) · 7.2% |
| groups A/B/C/D | 149 / 1,081 / 3,280 / 34,159 | 104 / 698 / 2,262 / 29,103 |
| trigger precision | 3.55% [2.42, 5.19] | 5.73% [3.99, 8.15] |
| lead first signal → onset (q25/med/q75) · → +70% | 10 / 13 / 17 · 14 / 19 / 23 | 8 / 10 / 16.5 · 11 / 17 / 23 |
| **C1** matched ratio | 1.23 [0.74, 1.98] ✗ | 1.29 [0.74, 2.20] ✗ |
| **C2** minus volume ranking · minus volatility ranking (pp) | +0.14 [−1.33, 1.71] · +0.28 [−1.43, 1.98] ✗ | +1.25 [−0.54, 3.15] · +0.13 [−2.03, 2.26] ✗ |
| **C3** beyond the tool | 1.31 [0.79, 2.13] ✗ | 1.13 [0.61, 2.00] ✗ |

Pooled (95%): C1 1.25 [0.90, 1.71] · C3 1.23 [0.89, 1.69] — both include 1. Both windows met their floors.
Sensitivity (never decisive): lift with the strict +70% label 1.32 · 1.69; onset L10 1.46 · 1.79; onset IGN 1.48 · 1.76.
By month the precision moved 2.2%–7.0% (validation) and 2.8%–5.5% (holdout). One third of RN_A's rows are also SEQ70
flag rows (1,133 of 3,429; 774 of 2,366); C1 matches on volume.
**Predictions:** P1 ✗ (C1 failed in the holdout) · P2 ✓ · P3 ✓ (C3 passed in neither) · P4 ✗ (expected
PROMISING_UNVALIDATED) · P5 ✓ (median lead 13 and 10) · P6 ✓ (67 vs 27; 43 vs 21 events).

## 9. COMPARISON_WITH_EXISTING_TOOL_AND_BASELINES
| validation · holdout | flags/session | precision | lift | recall (events) | matched |
|---|---|---|---|---|---|
| RN_A (candidate) | 41.9 · 40.1 | 4.35% · 4.40% | 1.37 · 1.76 | 67 · 43 | 1.23 · 1.29 |
| three-condition tool, technical part | 21.6 · 20.2 | 3.39% · 4.09% | 1.07 [0.61, 1.62] · 1.64 [0.81, 2.54] | 27 · 21 | 0.70 · 2.11 |
| RSI < 30 alone (ablation) | 68.3 · 65.6 | 4.28% · 3.90% | 1.35 · 1.57 | 89 · 59 | 1.03 · 1.46 |
| current READY location rule (LOC) | 30.2 · 35.1 | 2.82% · 2.63% | 0.89 · 1.05 | 50 · 31 | 1.13 · 1.52 |
| volume ranking at RN_A's burden | = | 4.21% · 3.14% | — | 63 · 31 | — |
| volatility ranking at RN_A's burden | = | 4.07% · 4.26% | — | 50 · 28 | — |
| lowest-price ranking at RN_A's burden | = | 4.43% · 3.08% | — | 61 · 25 | — |

Events: RN_A only 55 · 30, the tool only 15 · 8, both 12 · 13. RN_A reaches about twice the tool's events at about
twice its burden; per signal it is no better than ranking pivot-days by volume, volatility or low price. The tool's
technical part had no edge in validation (1.07) and an unstable one in the holdout (1.64, CI includes 1); the current
READY location rule had none.

## 10. HUBC_CURRENT_STATE (after the seal; descriptive)
Last bar 2026-10-08: close $1.00, RSI 21.65, 25-session low $0.8826 (2026-09-30), held 6 sessions, 13.3% above the low,
bounce 28.0%, no boom (14.2%), reverse split 1:25 on 2026-09-14. RN_A has been on since 2026-09-30 (off on 09-29 when
the bounce was 52%); the tool's technical part since 10-07 (hold reached 5). HUBC is outside the pivot population (M2
ceiling, frozen) and the data-quality gate quarantines recent splits. **With the decision below, this state carries no
validated forecast**; its outcome after 10-08 is unknown. No statistic of this study involves HUBC.

## 11. LIMITATIONS
- The event is the bot's daily-close detector; moves that happen intraday or pre-market (DKI 10-07) are invisible to it.
- Float, available-to-borrow, hourly lows and after-hours highs cannot be reconstructed; the tool is tested on its
  technical part only, and the full tool may behave differently.
- The pivot population covers 35–53% of the events 7–10 sessions ahead; conclusions are about pivot-days.
- Round 2 and the choice of RN_A were made after reading development (disclosed); the RSI30/RN_A tie was broken by
  burden. Validation and holdout were read once, after the seal.
- 28–37% of flagged rows found no matched control (extreme profiles); the matched ratios describe the matched part.
- The burden rose from 27 (development) to ~41 flags/session out of sample; precision stays near 1 in 23 even when lift
  is above 1. Seeds and HUBC are anecdotes; the candidate missed all five seed events.
- Daily bars, survivorship (today's listings), split-adjusted volume; READY70/SEQ70 had read these windows for other rules.
- Guards G1–G8 pass and ten mutations each felled exactly their guard (`data/mutations.json`) — the pipeline does what
  the specification says; that is not evidence for or against the signal.

## 12. FINAL_DECISION
**NO_INCREMENTAL_EDGE_FOUND.** Among the source-backed technical conditions (the tool, Faisal's texts, his app), only
«RSI oversold now» separated future +70% onsets in development; the app's distance, bounce, stability, EMA/MACD and
cycle conditions, and the order «oversold first, then hold», added nothing. The compact candidate built from it (RSI
below 30 with a 10–40% bounce) was followed by a qualifying onset 7–10 sessions later more often than the average
pivot-day (lift 1.37 and 1.76), but not more often than pivot-days with the same price, volume, volatility and
liquidity (pooled 1.25 [0.90, 1.71]); it was no better than ranking pivot-days by volume or volatility at the same
burden; and its rows outside the tool added nothing measurable (pooled 1.23 [0.89, 1.69]). The three-condition tool's
own technical part was not stronger. Do not change READY NOW on this basis.
**Next evidence (proposal, not executed):** the gap is information that daily technical bars do not carry — float and
available-to-borrow point in time (the forward borrow harvest exists since 2026-08), intraday/pre-market timing, and
the pivot population that half to two-thirds of the events sit outside. Any further test needs a sealed forward
record, not a new condition.

## Files
`rn_build.py` (`--check`) · `rn_lib.py` · `rn_dev.py` (`seeds` · `dev` · `dev2`) · `rn_eval.py` (`final`, sealed) ·
`test_rn.py` (G1–G8) · `rn_mutate.py` · `RN_SPEC.md` · data: `rows.csv.gz`, `events.csv.gz`, `seeds.csv.gz`,
`ewin.csv.gz`, `calendar.json`, `inventory.json`, `seeds_matrix.json`, `dev.json`, `dev_round2.json`, `result.json`,
`mutations.json`.
