# READY_NOW_AUDIT_BASELINE — frozen description of the production READY NOW path (as of 2026-10-08, main `bc1681f9e`)

> Read-only baseline written BEFORE any analysis conclusion, so that every later claim can be checked against it.
> Nothing in this file changes production. Thresholds are the LIVE values (`FAISAL_ONLY=1`), read by importing the module,
> not the fallback table values (which differ and have misled earlier memory lines).

## 1. What "READY NOW" literally is in code

| Layer | Function / file | What it does | Decision type |
|---|---|---|---|
| L0 DATA | `download_history` (`Super_stock.py:2528`) | TradingView daily bars (`BARS_SOURCE=tradingview`, since 2026-09-30 #491) with Yahoo fallback per symbol. 10-07 run: TV 3354/3577, Yahoo 64, valid 3418. | data |
| L1 UNIVERSE | `get_universe` | NASDAQ ≈3577 symbols after filtering. | data |
| L2 IDENTITY GATES | `analyze_ticker` (`:4029…`) | M1 price ≥ 0.40 · M2 drop from 52w high within [71.72%, 99.95%] (above → `M2_هبوط_فوق_97`, below → `M2_هبوط_تحت_40`) · M3 prior spike ≥ 78.27% · M4 base range (15 bars) ≤ 120% + recent-rise block 214.7% · M5 $-volume ≥ $14.3K. | hard reject |
| L3 SOFT FAILS | `analyze_ticker` | ≤ 8 soft fails (`WATCH_MAX_FAILS`): M2 ideal, M3 ideal, M6 timeframes (0 required), M7 pattern, M9 gap above (`GAP_ABOVE_REQUIRED`), M10 RSI (oversold ideal 33 / hard 69; now ideal 35.8 / hard 71.1 → reject), M11 MACD, M12 MA band, RR < 0.5. | membership |
| L4 SCORE | `analyze_ticker` | score ≥ 5. Pivot stability (`STABILITY_MIN=3`) is computed and displayed, NOT a gate. | membership |
| L5 ANCHOR | `tested_level` (`:10030`), `ANCHOR_MODE=tested_strict` | lowest low of last 30 bars must be touched by ≥ 2 separate clusters within 1.5%; otherwise reject `M_لا_مستوى_مختبر` (owner decision 2026-08-14). | hard reject |
| L6 PLAN | `analyze_ticker` | tranches = anchor × (1, 1.03, 1.06); stop 5–7% below; targets ladder; RR. | plan |
| L7 POST GATES | `apply_short_gate`, `apply_float_gate`, `classify_tier`, `rank_key` (`:12924–12990`) | short (FINRA) soft fail; float ≥ 50M hard; tier B if fails ≤ 8; rank = in-entry-band first, then readiness, h4, score, rr. | membership/order |
| L8 SELECTION | `fill_picks` (`:12860`), `select_top` (`:14133`), `enrich`, `refloat_gate_recheck`, `borrow_second_chance`, `borrow_gate_recheck` | 15 slots; ChartExchange available-to-borrow must be ≤ 20,000 (`BORROW_AVAIL_MAX`); up to 4 refill rounds. 10-07: only 2 of 8 free slots filled, 28 candidates excluded for availability > 20k. | membership |
| L9 STATE | `weekly_watchlist.json` (stocks / pullback / removed / history / explosions) | daily `update_watchlist_status` refreshes price, `interp.entry_mode`. | state |
| L10 READY NOW | `entry_status(s)` (`:14914`) | `ready_now` iff `interp.entry_mode.mode ∈ {near_support, sweep_confirmed}` AND `last_price ≤ max(tranches) × (1 + ENTRY_READY_BAND_TOL_PCT=0)`. Otherwise `watch`. | **display classification only** |
| L11 OUTPUT | `build_daily_message(ready_only=True)` (`:20476`), `run_daily_watchlist` (`:22280`) | Telegram: ready cards + counts of watch, «تحت المتابعة» section (`near_watch_buckets`: inside n_out=0 top 20 by readiness · oversold rsi<30 top 20; display cap 40), hand section, split radar. | delivery |

`entry_mode` (`build_interpretation`, `:10931–10948`): stop hit → `no_entry_far`; price < pivot×0.995 → `reclaim_wait`; price > hi_zone×1.05 → `no_entry_far`; liquidity sweep detected → `sweep_confirmed`; else `near_support`.

**Verdict on the nature of READY NOW (from code, not opinion):** it is a *price-location flag on an already-selected watchlist member*. It has no notion of time-in-state, no operator/pressure trigger, no cycle stage. It was introduced 2026-07-08 (PR #83) as a display split of the daily message; the band rule was added 2026-08-06, ranking 2026-08-07, the tested-level anchor 2026-08-13/14, the near-watch section 2026-08-16, Faisal-only thresholds 2026-08-06.

## 2. Thresholds and their evidence class (ledger `FAISAL_SOURCE_LEDGER.md`)

| Key | Live value | Ledger tag | Image evidence |
|---|---|---|---|
| M1 `MIN_PRICE` | 0.40 | engineering | — |
| M2 drop band | 71.72–99.95% | inferred (catalog envelope P100) | catalog of Faisal stocks |
| M3 `PRIOR_SPIKE` | 78.27% | inferred (envelope) | catalog |
| M4 `BASE_RANGE_MAX_PCT` | 120 | engineering / owner decision (T-BASE-2) | none — Faisal never states a base-range % |
| M5 `MIN_DOLLAR_VOL` | $14.3K | inferred (envelope) | catalog |
| `WATCH_MAX_FAILS` | 8 | engineering | none |
| M9 `GAP_ABOVE_REQUIRED` | True | faisal_inferred | IMG_0153, ONCO cards (gap above = target) |
| M10 `RSI_OVERSOLD` / `RSI_MAX_NOW` | 33 / 35.8 (hard 69 / 71.1) | faisal_verbatim (TG_2043 «RSI 23–27»; «مستحيل يصعد إذا RSI بمناطق 40») — numbers themselves from envelope | TG_2043, TG_1870, IMG_0531 |
| `STABILITY_MIN` | 3 (display) | faisal_verbatim (IMG_0151 «حافظ ع قاعه 3 جلسات») | IMG_0151, TG_57913… |
| `ANCHOR_MODE=tested_strict` tol 1.5%, 2 touches | engineering (owner "1" 2026-08-14) | none for the numbers |
| `ENTRY_READY_BAND_TOL_PCT` | 0 | engineering | none |
| `BORROW_AVAIL_MAX` | 20,000 | faisal_verbatim («طبّق 20» · IMG_0150 «شورت تحت 20 ألف») | IMG_0150, TG_50578 |
| `WATCHLIST_SIZE` | 15 | engineering (owner «اعتمد سعة 15») | none |
| `FAISAL_RSI_ENTRY_MAX` (near-watch oversold bucket) | 30 | faisal_verbatim («rsi اقل من 30» DRCT) | DRCT card |

## 3. Output history (from 525 git snapshots of `weekly_watchlist.json`, `entry_status` re-applied)

| Metric | Value |
|---|---|
| Days with a snapshot | 90 (2026-06-20 → 2026-10-08) |
| Days with ≥ 1 ready_now | 74 |
| Distinct symbols ever ready_now | 117 |
| Mean ready_now per day | 3.1 (Jun 0.78 · Jul 1.12 · Aug 3.36 · Sep 4.76 · Oct 6.0) |
| Median consecutive ready-days per symbol | 2 |
| near_watch snapshots | 48 (2026-08-16 → 2026-10-08); inside-envelope mean 297 symbols, oversold mean 122, shown ≤ 40 |

## 4. Outcome of every symbol that was ever READY NOW (bot's own targets/stops; `weekly_watchlist.json` stocks/removed/history)

| Class (definition) | n | share |
|---|---|---|
| TRUE_READY — later hit t1 or higher (bot target) | 29 | 24.8% |
| FALSE_READY — removed on stop without any target hit | 70 | 59.8% |
| UNRESOLVED/ACTIVE — neither (still active or < 20% gain) | 18 | 15.4% |
| Total | 117 | 100% |

Denominator caveat: outcomes are judged by the bot's own t1/stop (5–7% below anchor), not by Faisal's exits; a stop 7% below support can be hit by the very 8–13% sweep Faisal waits for (TG_57870), so part of FALSE_READY is EARLY_READY in Faisal's terms. Not separable without bars (see `fm_bars_probe`).

## 5. Explosion register cross-check (`weekly_watchlist.json["explosions"]`, 2026-07-17 → 2026-10-07)

| | n |
|---|---|
| Explosions ≥ 100% (gain field) | 279 (217 «تجمّع» gradual, 62 «قفزة» single-day; 124 had pivot identity M1–M3 at base) |
| …READY NOW within 14 days BEFORE the explosion date | **2** (PSIG 08-19, QTEX 09-30) |
| …READY NOW only at another time | 7 |
| …never READY NOW | 270 |
| …in near-watch INSIDE bucket (n_out=0) within 14 days before (snapshots exist from 08-16) | 81 of 231 with a snapshot |
| …in near-watch OVERSOLD bucket | 26 |
| …not in near-watch at all | 124 |
| no snapshot available (before 08-16) | 48 |
| base_reason at the base (why not a candidate) | M2_under40 79 · no_tested_level 73 · M1 66 · M4 40 · «مرشّح» 10 · M3 6 · M2_over97 4 · M5 1 |

## 6. Daily reject walls (`reject_log.json`, 20 sessions 09-11 → 10-08, full counts `walls_n`, universe n ≈ 3,290)

Typical day (2026-10-07): M2_under40 2,624 · **no_tested_level 395** · M4 97 · M1 80 · M3 71 · M2_over97 24 · M5 6 · score<5 2 · M10 RSI 0–4.
The anchor gate (`tested_level`) is the second-largest wall every day and the largest wall that acts on stocks that already have the identity (M1–M5 passed).

## 7. Parallel outputs that touch the same stocks (not READY NOW)

- `three_cond_daily.py` (02:43 UTC Tue–Sat): RSI < 33 ∧ float < 4M ∧ avail < 20k ∧ 5-session stability above exact low ∧ no 50% explosion in 5 sessions; DQ gate quarantines recent reverse splits.
- `presession_radar.py` digest (PM/AH movers of the price universe; `sent` per row).
- `pullback_live.py` live alerts; hunters; «هنا الدخول» (silent since Polygon ended 2026-09-29).
