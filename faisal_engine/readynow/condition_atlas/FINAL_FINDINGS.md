# Faisal technical condition atlas — final findings

Mission «FAISAL TECHNICAL CONDITION ATLAS & HISTORICAL READY-NOW CLASSIFICATION» (2026-10-11). Research only: local
data, no network, no agent or workflow, no production, Telegram, list, membership or frozen-axis change, the stopped
forward logger in `readynow/fwd/` untouched. Every number below is in a JSON file of `data/` and in the generated
reports (`SOURCE_CONDITION_ATLAS.md`, `HISTORICAL_DATA_INVENTORY.md`, `CHART_CASEBOOK.md`, `CANDLE_PATTERN_STUDY.md`,
`CONDITION_STRENGTH_RESULTS.md`, `READY_CLASSIFICATION_SPEC.md`, `HISTORICAL_CLASSIFICATION_RESULTS.md`).

**Reconciled 2026-10-11/12** (task «FINAL EVIDENCE RECONCILIATION»): points 1, 4 and 5 were corrected after a
post-seal check, `RECONCILIATION_ADDENDUM.md`, whose questions were written before it ran. The original wording is
quoted there (§6). The sealed protocol, model, results and verdict are unchanged.

## Answer to the question

**Q: Which conditions and paths separate the strongest pivots from inactive ones; how do we rank readiness while
allowing missing auxiliary conditions; and does that give a useful signal 7–10 sessions before an explosion, beyond the
current rules and simple price/volume rankings?**

1. **RSI oversold is the most consistent raw association among Faisal's readiness conditions, and it adds nothing
   shown beyond volatility.** RSI below 30 has lift 1.36 [1.13, 1.60] in development (2025-05 → 12), 1.40 in
   validation and 1.49 in the holdout; RSI < 33 is similar. Only three of the 65 flags have a lift lower bound above 1
   in all three periods: RSI < 30, RSI < 33 and the group-candle proxy (point 4). Matched on session, price, volume
   and volatility, RSI < 30 keeps a lower bound above 1 in development only (1.49 [1.07, 2.01]; 2026: 1.09 [0.77, 1.52]
   and 1.33 [0.93, 1.89]), and no flag beats the volatility or 5-session-drop ranking at equal
   burden in any window. «RSI lowest of 10 sessions ≤ 27» gives 1.32 in development and 1.36 in validation, but its
   holdout interval reaches below 1. Annual-low proximity and «a dip back to the low» are weak (≈ 1.12) and
   unstable.
2. **The structure of his cycle does not separate on daily bars.** This covers hold 3/5 sessions, the ≈20% test rise,
   the retest, the 5–15% sweep-and-reclaim, the cycle stage, elapsed time since the peak, the tight band above the
   annual low, gaps above, the MACD and EMA crosses, Klinger, Williams %R, up/down volume and support touches.
   Development lifts are 0.76–1.06, with no stable sign in 2026.
3. **No candle separates**, alone, at the support, or in the composite «doji / morning star then engulfing». One hit
   in one 2026 window is what chance predicts with 22 candle flags.
4. **His «no-entry» states are an association, not a forecast and not an entry signal.** These are chasing, an
   explosion within a week, and «group» candles. For Faisal «القروبات» is a validity and risk condition: group
   candles («شموع غبيه توصل 20٪ … بدون جسم ع فريم 4 ساعات») make the chart unreadable and the operator may press the
   stock down, so he stays out (IMG_0151, IMG_0488, IMG_0316). The study's group-candle proxy, a daily stand-in for
   the 4-hour shape, has lift 1.28 / 1.58 / 1.60 across the three periods. But it keeps that lift after volatility
   matching in validation only (development 1.04 [0.76, 1.43], holdout 1.30 [0.89, 1.84]). Its prevalence is flat
   from T−10 to T−1 and about three times higher after a recent episode, and it never beats the volatility or drop
   ranking at equal burden. The 20–31% of eligible events «in that state» on every pivot-day of T−10…T−7 is the union
   of the three states; the group proxy alone is 12–24%. Those events are missed by construction (an invalidated day
   cannot be READY). The six largest missed validation winners were all invalidated (P 0.005 given the missed
   share), but development has 1 of 6 and the holdout 2 of 6. Those six were coming off an earlier spike. It is a
   property of that window's tail, not a rule.
5. **A flexible, weighted three-axis classification does not beat the current tool or the simple rankings.** The
   axes are validity, technical strength and proximity; any auxiliary condition may be missing; only invalidation
   removes a row. Sealed 2026 check: W_k − the tool's technical part **+0.24 pp [−1.11, +1.60]**,
   − 5-session drop **−1.46 [−2.81, −0.08]**, − CAPIT_TC **−1.64 [−3.29, −0.14]**, − volatility −1.61 [−3.64, +0.35].
   Verdict **NO_DEMONSTRATED_IMPROVEMENT**, and its classes are **NOT_GRADED**: no fine difference holds in 2026
   (READY_1 − READY_2 pooled +0.77 pp [−0.48, +2.00]). The coarse READY(1–3) − WATCH (+0.96 [+0.30, +1.61]) is
   descriptive and is not value beyond the baselines. READY_1–3 are score-rank bands, not grades. Counting Faisal's
   conditions does no better (−0.46 pp vs the tool), nor does the app's weighted screen (−0.48 pp). All eight
   predictions written before the run came true. **Not production-ready.**
6. **So the useful signal 7–10 sessions ahead, beyond the current rules and the simple rankings, is not demonstrated
   with daily bars.** The best daily separator remains a generic «volatile, falling, oversold» profile (CAPIT_TC, the
   5-session drop, RSI). Faisal's conditions say *which pivots to watch*, not *when*.

| claim | association (lift) | 7–10-session prediction beyond volatility | entry suitability | incremental value over tool / drop / volatility | evidence |
|---|---|---|---|---|---|
| RSI < 30 / 33 | yes, all three periods | development only | not tested (no trade rule) | no | development in-sample; 2026 exploratory (read before) — no independent validation |
| group-candle proxy (I04) | yes, all three periods | validation only | no — Faisal's exclusion state | no | same as above |
| invalidation states as exclusion | — | — | they remove events by construction | — | descriptive |
| weighted classifier (W_k) and classes | — | — | — | no (V1–V3 fail); NOT_GRADED | sealed 2026 check, exploratory windows |

**This is a limit of the evidence, not a proof of impossibility.** Faisal states most of his timing conditions on the
4-hour frame, in the order flow, or in extended hours: operator pressure («تبقى الضغط ✅»), pre-market and
after-hours behaviour, groups, the short, float and offering. None of these has history for the pivot population.

## What the sources say (SOURCE_CONDITION_ATLAS.md)

55 conditions with verbatim quotes and image ids: 43 Faisal's own, 7 from app screens (a third-party tool applying
his method), 3 third party, 2 project rules. By kind: 11 pivot validity, 11 technical strength, 17 confirmation, 8
timing, 8 invalidation. By data: 40 testable on daily bars, 9 partial (4-hour rules on daily proxies), 6 not
available. His own summary (`TG_50584`, viewed) is news → moving averages 20/30/50 → short, then bottom →
≈20% test → hold or a sweep of 5% under the low candle → price stability = targets. «تبقى الضغط ✅»: after the
technical conditions, readiness waits for the operator's pressure. Recorded conflicts: above vs below the averages
(his «average» is often elapsed days), the RSI band (23–27 · 22–27 · 20–27 · < 30 · the tool's 33), the sweep depth
(5% · 10% · 10–15% · 7–13%), the hold length (3 · 3–5 · > 5 · the app's 2), and the frame (mostly 4-hour).

## What the data allow (HISTORICAL_DATA_INVENTORY.md)

Daily OHLCV with dated splits for 3,585 symbols (2024-05-01 → 2026-10-08) cover every daily condition point-in-time.
There are no 4-hour, intraday or extended-hours bars for the population (hourly bars for CRE, DKI, HUBC and SXTC only).
There is no historical float or borrow: borrow and pre-session logs start in July–September 2026 and cover the bot's
lists only. SEC filings and share counts exist point-in-time for 238 symbols chosen on 2026-10-08. In that biased
subset, share count < 2 M shows no association (0.92) and a recent final prospectus points the way Faisal says
(0.68) without significance.

## Method and safeguards

- Population: 174,796 READY NOW pivot-days (identity M1–M3 from bars ≤ T). Target: a clean corrected onset (start of
  the final +70% leg) 7–10 sessions later. Onset, the first intraday +70%, the +70% close and the detection are kept
  apart (casebook). Repeated legs of one stock are clustered (ticker bootstrap) and counted once per onset. Seeds and
  HUBC never entered a statistic.
- Features from bars ≤ T only. On truncated bars the recomputation is identical for 80 random rows × 63 columns, plus
  the CA1 guard. Labels use later bars as targets only. Prices are split-adjusted; ratios are split-invariant.
- Development (2025) chose everything. The protocol, frozen model and decision rules were sealed by SHA-256 before the
  only 2026 run (22:30 → 22:32 UTC). The seal stayed local until the owner authorised the commit in the
  reconciliation task; the sealed files were not changed by it (hashes in RECONCILIATION_ADDENDUM.md §5).
- 75 hypotheses in development: 65 condition flags, 6 classifier variants and 4 SEC-subset flags. The protocol's §⑥
  says 66 flags and 76, a miscount; the Bonferroni intervals divide by the 65 flags tested, and no decision rule uses
  them (RECONCILIATION_ADDENDUM.md §5, D1). **2026 is exploratory:** earlier READY NOW studies read those windows.

## What would change the conclusion

Readiness information outside daily bars, recorded point-in-time for every pivot: 4-hour and intraday bars,
extended-hours bars, the order flow (operator blocks, «pressure»), short and borrow availability, float, offering and
news status. Forward collection was excluded by this mission. Whether to collect any of it is the owner's decision.
