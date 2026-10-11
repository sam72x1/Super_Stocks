# READY70 — preregistration (sealed before any held-out row is read)

**Status:** sealed 2026-10-11. Its SHA-256 is pinned in `r70_eval.py` (`PREREG_SHA256`); `r70_eval.py test`
refuses to read the held-out window (exit 9) unless this file is byte-identical. One run. No re-tuning.
The result is published whatever it is. Research only: no production, Telegram, schedule, threshold or
membership change; no frozen axis (ANCHOR_TWO_TOUCH/H6 · M2 · M3 · M4 · closed axes) is redefined or bypassed.

## 1. Question
Among pivot stocks, is there a point-in-time state that marks READY NOW — a higher chance that the bot's own
+70% explosion event follows within 10 sessions — better than (a) the current READY NOW rule and (b) simply
watching every pivot, **and** that is not just a generic recent-drop / volatility / low-price effect?

## 2. Sources (all inside the repository; no network)
- **The +70% tool:** `Super_stock.scan_explosions` / `_run_explosion` (daily closes): a one-day close-to-close
  jump of at least `EXPLOSION_PCT`=50 within the last `EXPLOSION_LOOKBACK`=5 sessions, else a trough-to-peak
  close rise of at least `EXPLOSION_RUN_PCT`=70 within `EXPLOSION_RUN_LOOKBACK`=20 sessions. It runs after the
  daily screener and the Friday renewal and logs to `weekly_watchlist.json["explosions"]` (30-day retention).
- **Its real log:** 2,195 unique (symbol, launch-date) records on 638 symbols across 532 commits
  (scan dates 2026-06-22 → 2026-10-10). Recomputing the detector on the archive reproduces **95.0%** of the
  non-suspect records that have bars (1,803 matched; the rest are split artefacts ≥300% or delisted symbols).
- **Bars:** `faisal_engine/data/rank/bars.json.gz` — TradingView daily, regular session, split-adjusted,
  3,584 symbols, 2024-05-01 → 2026-10-08 (the 2026-10-09 bar was fetched intraday and is dropped).
  Splits: `faisal_engine/data/rank/splits.json`.
- **The bot's real lists:** `weekly_watchlist.json` (watchlist, carried, pullback) and `near_watch.json` over
  git history; `reject_log.json` (2026-09-15 → 10-10).

## 3. Units, populations, windows
- **Row** = (symbol, session t). Decision time = before the next session opens; features read bars ≤ t only.
- **Primary population PI** = every archive symbol on every session where the tool's own pivot notion holds:
  `Super_stock._had_pivot_identity` (M1 price ≥ `MIN_PRICE` on the price actually traded that day,
  M2 drop band from the 52-week high, M3 prior spike; live `FAISAL_ONLY=1` constants, read-only).
  Vectorised identity matched the bot's function on 456/456 sampled rows.
- **Discovery:** t ∈ [2025-05-01, 2025-12-31] (used for all exploration below).
- **Embargo:** 2026-01-02 → 2026-01-15 (10 sessions = the horizon) — not used.
- **Held-out test:** t ∈ [2026-01-16, 2026-09-24] (last t whose 10-session window closes by 2026-10-08).
- **Bot-tracked rows** (the bot's real lists, July–September 2026) are inside the test window and are read only
  by the test run (secondary block).

## 4. Outcome (labels are outcomes only; never features)
- **Primary `f10`:** within sessions (t, t+10], the tool's condition measured **from the decision onward**
  (no trough before t): a close-to-close day ≥ 50%, or close_k / min(close_t … close_{k-1}) − 1 ≥ 70%.
  `DURING` = the tool had already detected an episode that has not yet peaked (excluded from rates, counted as
  alerts during an event). `UNKNOWN_SPLIT` = a split dated in (t, t+10] (excluded, counted).
  `CENSORED` = window beyond the last complete bar (excluded, counted).
- **Secondary `y10` (strict):** an episode of the recomputed tool whose launch (trough + 1) is after t and whose
  first detection is within t+10. Discovery showed this label penalises every post-bottom state by construction
  (a later run measured from the old bottom marks the row "in event"), so it is descriptive only.
- **Event unit** (for capture and lead time): (symbol, crossing session) — repeated rows before the same event
  are one event.

## 5. What was examined in discovery (no test row read)
47 cells in total: under `y10` and `f10` each — all pivots, pivot-cycle stage 0–4, stage 3/4 by branch,
first rise, the current location rule, 5-session-return quintiles, 20-session-range quintiles (22 cells × 2);
then burden-matched controls (drop, volatility, price) for stage 1 (3 cells). Discovery numbers under `f10`
(base 5.21%, 798 tickers, 67,684 evaluable rows):
stage 1 ×1.55 vs all (cluster 95% [1.31, 1.83]); stage 1 vs the current rule ×2.15 [1.66, 2.88];
stage 1 vs drop control ×0.78 [0.67, 0.92]; vs volatility control ×0.84 [0.66, 1.11]; vs price control ×1.15
[0.92, 1.48]; stage 2 ×0.98, stage 3 ×0.94, stage 4 ×0.91 [0.74, 1.06]; the current rule ×0.72 vs all.

## 6. Hypothesis H-R70 (one)
READY NOW = **pivot-cycle stage 1** — `Super_stock.pivot_cycle_state` (Faisal's `TG_50584` sequence:
«1- القاع 2- ارتداد لاختبار المقاومه … 3- ثبات القاع او سحب السيوله … 4- ثبات سعري بعد سحب السيوله»)
returns stage 1: the pivot is still at its bottom — the lowest low of the 60-session window with no bounce of
`METHOD_BOUNCE_MIN_PCT`=10 since. Source line for timing: «اي سهم قبل يصعد يضغطه المضارب لادنى شمعه»
(`FAISAL_PRESSURE_MODEL.md`). Existing function, no new threshold.

## 7. Rules compared on the same test rows
- **ALL** — watch every pivot (no READY selection).
- **LOC** — the current READY NOW rule approximated point-in-time: the frozen anchor `Super_stock.tested_level`
  exists and round(anchor, 2) < close ≤ round(anchor × 1.06, 2) (stop = anchor; top tranche = anchor × 1.06).
  It agrees with the bot's stored READY flags on 91.0% of 575 watchlist decisions (sensitivity 79%,
  specificity 98.6%).
- **STAGE1** — the hypothesis.
- **Governing generic controls, burden-matched to STAGE1 each day** (k = number of STAGE1 rows that day; ties
  by symbol): **DROP-k** lowest 5-session return · **VOL-k** highest 20-session range · **PRICE-k** lowest
  traded price.

## 8. Criteria (decision)
Ratios of the `f10` positive rate, ticker-cluster bootstrap, 1,000 resamples, seed 20261011, **99% interval**
(Bonferroni over the 5 comparisons):
- **C1** STAGE1 / LOC: lower bound > 1.0.
- **C2** STAGE1 / ALL: lower bound > 1.0.
- **C3** STAGE1 / DROP-k, STAGE1 / VOL-k, STAGE1 / PRICE-k: every lower bound > 1.0 (the project rule: a timing
  signal is judged against a governing generic control).
- **C4** burden: STAGE1 flags per day at most 2× LOC flags per day (the 2× limit of `UNIVERSE_TEST_PROTOCOL.md`).
- **Sample floor:** at least 200 positive rows and 100 distinct events in the test window, else
  **C. INSUFFICIENT DATA**.
- **A. VALIDATED SHADOW IMPROVEMENT** only if C1 ∧ C2 ∧ C3 ∧ C4. Otherwise **B. NO VALIDATED IMPROVEMENT**.
  Even under A nothing is shipped: the recommendation goes to the owner.

## 9. Also reported (descriptive, never decisive)
Per rule: positive rate with Wilson 95%, unproductive READY rows, flags and tickers per day, alerts during a
detected event, capture (events with a flag before the crossing / all events), lead time (sessions), median gain
and drawdown from the decision close, READY spells and the share that end without an event. Monthly stability,
tickers seen in discovery vs new, stages 0–4 vs all, the strict label, horizons 5 and 20, and the bot's real
lists (actual bot READY flags vs STAGE1 vs LOC on the same rows; where each +70% event on a tracked symbol
stood before it — section 9 of the mission).

## 10. Predictions (written now, kept if wrong)
- **P1** C1 passes (stage 1 beats the current rule).
- **P2** C2 passes (stage 1 beats watching everything).
- **P3** C3 fails — the drop control is at least as good as stage 1 ⇒ expected verdict **B**.
- **P4** stage 4 (Faisal's «ثبات سعري بعد سحب السيوله») is not above all pivots (ratio ≤ 1.0).
- **P5** the current rule (LOC) is below all pivots (ratio < 1.0).

## 11. Known limits (stated before the run)
Survivorship: the archive holds today's listings only (delisted pivots are absent). Daily bars only — no
intraday timing claim. TradingView split adjustment; split windows are excluded, not repaired. The PI population
is wider than the bot's lists (they are a subset, reported separately). Price composition is a known confound
(`T-PRESS`: the market-wide pressure effect was mostly price) — hence PRICE-k. Prior family results
(`T-PRESS`, `T-PRESS-Q`, the closed common-link verdict, `T-PRELINK`) predict that behaviour features dissolve
against controls; this test is a READY-timing question on a new unit and outcome, not a reopening.
