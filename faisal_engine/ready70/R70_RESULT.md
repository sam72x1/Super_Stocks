# READY70 — result

**Verdict: B. NO VALIDATED IMPROVEMENT** — by the sealed criteria of `R70_PREREG.md`
(SHA-256 `67be5d57…68ee08`, pinned in `r70_eval.py`; the seal commit `5431c848c` was pushed before the held-out
window was read). One run (`python3 faisal_engine/ready70/r70_eval.py test` → `data/result.json`). Research only:
no production, Telegram, schedule, threshold, membership or frozen-axis change.

## 1. The +70% tool and its record
- **Tool:** `Super_stock.scan_explosions` / `_run_explosion` (`Super_stock.py`): on daily closes, a one-day jump of
  at least 50% in the last 5 sessions (`قفزة`), else a trough-to-peak rise of at least 70% within 20 sessions (`تجمّع`).
  It runs after the daily screener and the Friday renewal (`accumulate_explosions`), not intraday, and keeps
  30 days in `weekly_watchlist.json["explosions"]` with `was_pivot` (= `_had_pivot_identity` on the pre-move slice)
  and `base_reason` (the gate that rejected it at its base).
- **Its record (git history, 532 commits):** 2,195 unique (symbol, launch) records on 638 symbols, scan dates
  2026-06-22 → 2026-10-10 (kinds: run 1,601 · jump 430 · early untyped 164; 339 flagged ≥300% split-suspect).
- **Reproduction:** recomputing the detector on the archive (`faisal_engine/data/rank/bars.json.gz`, TradingView
  daily, split-adjusted, 3,584 symbols, 2024-05-01 → 2026-10-08) matches **95.0%** of the non-suspect records
  that have bars (1,803 matched · 96 no bars · the rest split artefacts). Guard L5: the recompute equals the live
  `scan_explosions` on synthetic histories (kind, day, gain).
- Other in-repo live ledgers (inventory only, `data/inventory.json`): liquidity alerts `tier_fwd_ledger.jsonl`
  1,016 rows (08-24 → 09-29) · `ignition_log.json` 117 fires · `presession_outcomes.jsonl` 2,568 · hunters
  4,635 · pressure radar 1,141. None of them is a +70% record; the live intraday tools stopped with Polygon (09-29).

## 2. Size of the treasure
- Bot-tracked pivots (watchlist, carried, pullback): **339 tickers** (2026-06-20 → 10-10); "تحت المتابعة":
  2,484 tickers (from 2026-08-14). Inside those lists only **7 pre-launch +70% episodes** (strict label) fell in July–mid-August
  and **5** in September — too few for a test. Hence the population below.
- **Pivot-identity population (the tool's own pivot notion, point in time):** 174,796 pivot-days on 1,108 symbols,
  2025-05-01 → 2026-10-07. Discovery 2025-05-01 → 12-31: 67,684 evaluable rows, 798 tickers, 640 distinct events (383 tickers;
  same event key as the test — the `events_flagged_before` field of `explore.json` used a cruder calendar key and
  over-counts; it was not used by the sealed contract).
  Held-out 2026-01-16 → 09-24: **90,542 evaluable rows, 987 tickers, 173 sessions, 4,771 positive rows,
  843 distinct events**.
- Timing of the events (3,727 clean episodes, 1,520 symbols): start of the move → +70% crossing median
  **11 sessions** (quartiles 4–16, 90th percentile 19); median peak +104%.

## 3. Reconstruction before the move
Daily bars only (no intraday claim). Decision before the next open; features read bars ≤ t (guard L1, 160 random
rows with every later bar altered); labels read bars after t (L2). Splits inside the horizon are excluded
(`UNKNOWN_SPLIT`), not repaired. The current READY rule is rebuilt as LOC (frozen `tested_level` anchor band);
it agrees with the bot's stored READY flags on 91.0% of 575 decisions.

## 4. Hypothesis and why
Discovery (47 cells, `data/explore.json`): every Faisal pivot-cycle stage sits at the base rate except **stage 1**
(the bottom is still forming) at ×1.55; stage 4 «ثبات سعري بعد سحب السيوله» ×0.91; the current rule ×0.72.
But burden-matched generic controls beat stage 1 (recent drop ×1.98, volatility ×1.85). The single sealed
hypothesis: READY = stage 1, judged against the current rule, watch-all, and three governing generic controls.

## 5. Out of sample (2026-01-16 → 09-24, `f10` = the tool's +70% condition within 10 sessions after the decision)

| rule | flagged rows | +70% rate (Wilson 95%) | flags/day | events caught before | lead (median) | median drawdown | spells ending without event |
|---|---|---|---|---|---|---|---|
| ALL — watch every pivot | 90,542 | 5.27% [5.13, 5.42] | 523 | 843 / 843 | 10 | −10.4% | 81% |
| LOC — current READY rule | 5,848 | 3.78% [3.32, 4.30] | 33.8 | 127 (15.1%) | 8 | −9.0% | 95% |
| **STAGE1 — hypothesis** | 6,732 | **7.81% [7.20, 8.48]** | 38.9 | 237 (28.1%) | 7 | −12.2% | 90% |
| DROP-k — generic | 6,706 | 12.06% [11.31, 12.87] | 38.8 | 296 (35.1%) | 7 | −15.2% | 88% |
| VOL-k — generic | 6,222 | 12.50% [11.71, 13.35] | 36.0 | 205 (24.3%) | 8 | −18.1% | 84% |
| PRICE-k — generic | 6,345 | 7.69% [7.06, 8.37] | 36.7 | 151 (17.9%) | 8 | −11.7% | 89% |

Ticker-cluster bootstrap, 1,000 resamples, **99%**:
- C1 STAGE1 / LOC **2.07 [1.53, 2.83] ✅** · C2 STAGE1 / ALL **1.48 [1.24, 1.75] ✅**
- C3 STAGE1 / DROP-k **0.65 [0.55, 0.77] ❌** · / VOL-k **0.63 [0.49, 0.82] ❌** · / PRICE-k 1.02 [0.77, 1.38] ❌
- C4 burden 1.15× the current rule ✅ (limit 2×)
- ⇒ **B**: stage 1 times explosions better than the current rule and better than watching everything, but it is
  a weaker version of a generic recent-drop / volatility effect, not a distinct READY signal.
- Predictions P1–P5 all held (P3 = C3 fails · P4 stage 4 ×0.86 [0.73, 0.98] · P5 LOC ×0.72).

## 6. Stability and the bot's real lists
- Monthly (9/9): STAGE1 > ALL and > LOC in every month; DROP-k > STAGE1 in every month.
- Tickers never seen in discovery (291): STAGE1 / ALL 1.18 [0.85, 1.52] (95%) — not separated on new names.
- Strict label (launch after the decision): STAGE1 / ALL 2.17; LOC / ALL 1.05 [0.84, 1.24].
- Horizons 5 and 20 keep the same order (DROP-k > STAGE1 > ALL > LOC).
- Post-hoc sensitivity (`data/post_hoc.json`): removing the 260 positive rows whose gain is 300% or more
  (possible split artefacts) leaves every ratio in place — STAGE1/LOC 2.04 · /ALL 1.47 · /DROP-k 0.65 ·
  /VOL-k 0.62 · /PRICE-k 1.07.
- **Bot's real lists, July–September 2026 (same rows):** pivot lists — all 3.86% (2,022) · actual bot READY
  5.46% (20/366) · LOC 5.72% (19/332) · STAGE1 8.33% (7/84). "تحت المتابعة" — all 4.96% (12,226) · **actual
  bot READY: 0 rows (never evaluated)** · STAGE1 8.47% (110/1,298) · LOC 3.01% (9/299). Small samples; descriptive.

## 7. Pipeline diagnosis (mission §9)
- 159 distinct +70% events on bot-tracked symbols in the window: **138 (87%) were on "تحت المتابعة" only**,
  21 on the pivot lists. The bot's READY fired before **8** of 159; a stage-1 state existed before 45; LOC before 15.
- The real rejection wall was logged for 78 of them (`reject_log.json` exists only from 2026-09-15): anchor
  `M_لا_مستوى_مختبر` 40 · M4 16 · M1 12 · M3 5 · M2 2 · M5 1. For the other 81 the wall is **UNKNOWN** (not
  inferred).
- Post-hoc (not preregistered, `data/post_hoc.json`): the frozen anchor exists in 4.7% of stage-1 pivot-days
  (20.2% overall) and in 15.5% of pre-event rows; event rate 4.05% with an anchor vs 5.58% without.
- **Smallest diagnostic change (documented only, not applied):** when `near_watch_entry` is written, also store
  the rejection code already present in `_REJECT_REASONS` at the call site, plus the anchor level and the
  pivot-cycle stage of that run. Without them a "تحت المتابعة" row cannot be re-evaluated for READY later, and
  "لا شيء خارج الظرف" hides the real wall (measured earlier: 6,737 of 12,419 entry-days).

## 8. Frozen-axis constraint
No frozen axis was changed or bypassed (the anchor and identity functions were called read-only). The
measurements show the anchor gate removes most higher-hazard pivot states before READY is evaluated; using that
would require the owner's written REOPEN of H6 — this result is not such an authorization, and no validated factor
was found to justify one.

## 9. Files, tests, reproduction
`r70_build.py` (build; `--check` regenerates every output byte-identically) · `r70_eval.py` (`explore` discovery
only · `test` sealed) · `r70_disc_controls.py` (discovery controls) · `test_r70.py` (L1–L8, all pass) ·
`r70_mutate.py` (8 mutations, each felled exactly its guard: `data/mutations.json`) · data: `episodes.csv.gz`,
`log_events.csv.gz`, `obs.csv.gz`, `pi_obs.csv.gz`, `inventory.json`, `explore.json`, `result.json`, `post_hoc.json`.

## 10. Limits
Survivorship (today's listings only); daily bars only; TradingView split adjustment (split windows excluded);
the population is wider than the bot's lists; LOC is a 91%-agreement approximation of the current rule; prices
before 2025-05 limit the 52-week window early in discovery; the prior family (`T-PRESS`, `T-PRESS-Q`, the closed
common-link verdict, `T-PRELINK`) already showed behaviour features dissolving against controls — this run agrees.
