# CODE_AND_TEST_AUDIT — READY NOW path (sections 32–33 of the mission) (2026-10-08)

## A. Code audit (actual code, traced — see `READY_NOW_AUDIT_BASELINE.md` §1 for the L0–L11 map)
| Finding | Where | Evidence | Class |
|---|---|---|---|
| Entry point / candidate generation / filters / scoring / ranking / state / output / delivery | `scan_market` → `analyze_ticker` → `apply_*_gate` → `classify_tier` → `rank_key` → `fill_picks`/`select_top` → `enrich` → gates → `weekly_watchlist.json` → `update_watchlist_status` → `entry_status` → `build_daily_message(ready_only=True)` → `send_telegram` | traced by reading, line refs in baseline | — |
| **Dead code (never referenced anywhere incl. tests)** | 0 of 614 top-level functions in `Super_stock.py` | AST + repo-wide regex scan | none |
| **Dormant display functions (referenced only by tests)** | `half_down_line`, `key_levels_block`, `split_watch_report`, `build_split_watch_section`, `position_size_line`, `h4_levels_block`, `tranche_avg`, `readiness_ratio`, `liquidity_verdict`, `liquidity_lines`, `silent_accumulation`, `acc_line` (12) | scan | documented as "kept, not deleted" in CLAUDE.md; tests keep them green ⇒ false confidence that they are wired |
| **Stale ranking input** | `h4_confirm` is computed in `enrich` AFTER `rank_key` sorts → always 0 at ranking time | CLAUDE.md note 2026-06-24, code order | stale rule (ranking contribution unreachable) |
| **Duplicated RSI thresholds for one concept** | `RSI_OVERSOLD` 33 (soft fail), `RSI_MAX_NOW` 35.8 (soft fail), `FAISAL_RSI_ENTRY_MAX` 30 (near-watch bucket), three_cond `rsi_max()`=33, `OPL.RSI_OWNER` 30 (research), `PUBLISHED_RSI` 30 | grep | duplicated logic with three different numbers for "oversold" |
| **Contradictory conditions (design-level)** | stop 5–7% below anchor (`STOP_BELOW_LOW_PCT`) vs displayed `PIVOT_SWEEP_PCT`=13 "expected sweep" — the bot expects a sweep deeper than its own stop | config | contradictory (measured consequence: 70/117 READY stopped out) |
| **Unreachable condition** | `ENTRY_READY_BAND_TOL_PCT = 0` makes the band test equivalent to `price ≤ max(tranche)`; the tolerance branch never widens | code | unreachable parameterisation |
| **Thresholds not backed by evidence** (ledger `engineering`) in the READY path | M1 0.40 · M4 120 · `WATCH_MAX_FAILS` 8 · `tested_level` tol 1.5% / 2 touches / 30 bars · `WATCHLIST_SIZE` 15 · `NEAR_WATCH_SHOW` 40 / BUDGET 240 s · `ENTRY_STEP_PCT` 3 · `SCORE_MIN` 5 | ledger | 9 engineering numbers decide membership/visibility |
| **Information lost between stages** | (1) near-watch computed for ≈300 inside symbols, shown 20+20 (L11); (2) time budget cuts (10-07: 468 symbols uncomputed); (3) `BARS_SOURCE_LAST` overwritten by later downloads (fixed for the Yahoo-fallback line, pattern remains); (4) `removed` symbols never re-enter except via pullback list; (5) `reject_log` samples M2_under40 at 400 (counts kept in `walls_n`, symbol names lost) | code + logs | loss points |
| **Split handling split across tools** | split restart exists in `split_hunter._post_split_high`; DQ gate quarantines; READY path uses raw 52w high | code | duplicated/inconsistent logic |
| **Trigger lives outside the READY path** | operator gate only in `pullback_live`/ignition (Polygon, silent since 09-29) | code | READY NOW has no trigger |

## B. Test audit (`test_bot.py`, 5,235 `check(` calls; suite 5,268 ✅ / 0 ❌ on 2026-10-08)
| Category | Count (grep, approximate) | Assessment |
|---|---|---|
| Implementation locks via `getsource`/`inspect` | 862 | prove the code is written as written — **not** methodology evidence |
| AST structural locks | 1,606 | same class (wiring/structure) |
| Byte-identity / SHA locks on roots | 779 | protect against unintended change; say nothing about correctness of the roots |
| Checks naming specific tickers (DKI/SXTC/HUBC/CRE/SNAL/OMH/CIIT) | 31 | known-example fixtures (e.g., `SNL1`, `PSW1/2` simulations) — verify a display line on a stored example |
| `entry_status` checks | 114 | behavioural on synthetic records; cover near/sweep/reclaim/far modes and the band; **no test asserts a recall property** (e.g., "a Faisal-labelled READY day is flagged") |
| Negative/missed-case vocabulary | 152 | mostly "the line is absent when the field is absent" — not missed-signal tests |
| Temporal leakage vocabulary | 155 | present for backtest/forward tools (good); none for `entry_status` (it has no time dimension to leak) |
| Ranking failure | `rank_key` stability locks only | no test that ranking surfaces a Faisal-labelled case |
| Data availability | TV/Yahoo fallback locks (TVB*, YF*) | good coverage of source switching; none for "near-watch budget cut hides X" |

**False-confidence tests (definition: a passing test that an owner could read as "READY NOW is right" while it only pins current behaviour):**
1. The 12 dormant display functions have functional tests — green while unwired.
2. `entry_status` tests fix the 2-value mapping; they would pass for any threshold of the band because `ENTRY_READY_BAND_TOL_PCT` is 0 and the fixtures are built from the same constants.
3. Root byte-identity locks are routinely re-pinned "إقرارًا" when a root changes — they document intent, not validity.
4. No test consumes `weekly_watchlist.json["explosions"]` against READY history; the 2/279 recall number in this audit had never been computed by a test.

## C. What this audit does NOT claim
No code was changed. No test was added or removed. The dormant functions are not recommended for deletion (owner rule: display functions are kept).
