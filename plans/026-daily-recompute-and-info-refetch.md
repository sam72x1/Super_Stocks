# Plan 026: Compute the per-symbol indicator/interp bundle once per daily run, and reuse the float gate's `.info` in enrich

> **Executor instructions**: This is the **highest-risk plan in this batch**. It touches
> functions guarded by "byte-identical membership" locks and a documented "display-only,
> never affects selection" contract. Do NOT start it until plan 023 (or an equivalent
> characterization/parity net) exists, or you have built the parity snapshot in Step 1.
> Follow every step; run the parity gate after every change; if ANY parity check differs,
> STOP and revert. When done, update this plan's status row in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4e9b143..HEAD -- Super_stock.py`
> Confirm the call sites and function bodies below still match before proceeding; on a
> mismatch, STOP.

## Status

- **Priority**: P3 (do last; requires the parity net)
- **Effort**: M
- **Risk**: MED — consolidation must preserve exact values, ordering, and the "never
  affects selection" contract; the repo has locks asserting byte-identical behavior.
- **Depends on**: plan 023 (characterization tests give a safety net) — recommended, or
  build the parity snapshot in Step 1.
- **Category**: perf
- **Planned at**: commit `4e9b143`, 2026-08-15

## Why this matters

Two redundant-compute wastes in the daily run over ~300 active records:

- **PERF-01**: `run_daily_watchlist` walks the active set through three overlapping passes —
  `update_watchlist_status` (`Super_stock.py:15285`), `check_promotions` (`:15370`, calls
  `analyze_ticker` **again**), and `compute_readiness` (`:15373`, `entry_readiness` again).
  `build_interpretation` runs **twice** per symbol; the stochastic/CCI/Klinger/pivot
  indicator family is computed 2-3× per symbol. Roughly 3× the necessary DataFrame indicator
  work on every daily job.
- **PERF-03**: a selected symbol fetches `yf.Ticker().info` **twice** — once in
  `apply_float_gate` (`:10061`, the slow `.info` endpoint, before `enrich`) and again in
  `enrich` (`:4934`, `_fetch_info`). `.info` is the heaviest yfinance endpoint (the code
  itself flags it "بطيء").

**Why P3/last**: the payoff is CI-time/network, but the risk is real — these functions are
locked for byte-identical selection behavior. A consolidation that changes even one value's
rounding or ordering breaks a lock and, worse, could silently shift what reaches the owner.
The plan therefore centers on a **parity gate**: the emitted daily report/state must be
byte-identical before and after.

## Current state

The three passes (call sites in `run_daily_watchlist`):
```python
# Super_stock.py:15285
        stopped_today = update_watchlist_status(wl, hist)   # per symbol: full_stoch, klinger,
                                                            # cci, bottom_test, pivot_stability,
                                                            # group_pump_scar, trendline, build_interpretation
# Super_stock.py:15370
        promoted = check_promotions(wl, hist)               # per symbol: analyze_ticker AGAIN + build_interpretation AGAIN
# Super_stock.py:15373
        compute_readiness(wl, hist)                         # per symbol: entry_readiness AGAIN
```
`update_watchlist_status` computes the indicator bundle + interp at `Super_stock.py:11160-11186`;
`check_promotions` re-calls `analyze_ticker` at `:11374` and `build_interpretation` at `:11419`;
`compute_readiness` calls `entry_readiness` at `:11435`.

The `.info` double-fetch:
```python
# Super_stock.py:10061-10066  (apply_float_gate — runs BEFORE enrich, over all M13-passing candidates)
            try:
                info = yf.Ticker(r["symbol"]).info or {}
                fl = info.get("floatShares")
                r["float"] = fl
                sp = info.get("shortPercentOfFloat")
                if r.get("short_pct") is None and sp:
                    r["short_pct"] = round(sp * 100, 1)
            except Exception:
                fl = None
# Super_stock.py:4934-4936  (enrich — fetches the FULL info again for the selected subset)
                info = _fetch_info(t)                 # مع إعادة محاولة
```

**Critical constraints** (from CLAUDE.md and inline locks):
- `interp` and the indicator bundle are **display-only** and locked *out* of `rank_key`/
  `select_top`. The consolidation must not change what `select_top` returns, in what order.
- `entry_ref` = nomination price (owner decision), unaffected.
- `enrich` needs the **full** `.info` dict (sector, summary, session ctx, quote), not just
  the float subset — so cache the **raw** info dict, not derived fields.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests | `python3 test_bot.py` | exit 0 |
| Parity snapshot (Step 1) | see Step 1 | identical report/state bytes before vs after |
| Confirm call sites | `grep -n "update_watchlist_status(wl\|check_promotions(wl\|compute_readiness(wl" Super_stock.py` | the 3 sites |

## Scope

**In scope**:
- `Super_stock.py` — `update_watchlist_status`, `check_promotions`, `compute_readiness`
  (add read-through of a cached per-symbol bundle) and `apply_float_gate`/`enrich` (share
  the raw `.info`).
- `test_bot.py` — a parity test + the injected-fetch counting test.

**Out of scope** (must stay byte-identical):
- `rank_key`, `select_top`, `classify_tier`, `analyze_ticker`'s return, `entry_status`,
  `backtest_symbol`. If consolidation would change any of their outputs, STOP.
- The emitted daily report/state content — must be identical.
- No `LOGIC_VERSION` bump is intended; if you find one is needed, that means behavior
  changed → STOP.

## Git workflow

- Branch: `advisor/026-daily-recompute-and-info-refetch`
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Build a parity gate BEFORE touching anything

Write a test (or a scratch harness in `test_bot.py`) that runs the daily-status pipeline on
a fixed synthetic watchlist + injected `hist` (reuse the offline fixtures the suite already
uses for `run_daily_watchlist`/`update_watchlist_status`) and captures the **exact** emitted
artifacts: the resulting `wl` record fields (interp, readiness, indicator fields, promotions,
stops) and the built message text. Serialize them to a canonical string. This is your golden
snapshot. Every later step must reproduce it byte-for-byte.

**Verify**: the snapshot test passes on unmodified code and is deterministic across two runs.

### Step 2: Introduce a per-symbol enrichment cache, populated once

Add a single per-symbol compute that produces the indicator bundle + `build_interpretation`
result keyed by `(symbol, id(df))` (or by symbol within the run), computed on the **first**
pass, and have the later passes **read** it instead of recomputing. Key design rule: the
first pass must compute exactly what it computes today (same functions, same order, same
rounding); the later passes read the stored result. Do **not** merge the passes into one
function — keep the three call sites, just make passes 2 and 3 consult the cache.

`build_interpretation` must run **once** per symbol; `check_promotions` reads the stored
interp rather than recomputing. `entry_readiness` likewise computed once.

**Verify**: parity snapshot (Step 1) is byte-identical. `python3 test_bot.py` → exit 0.

### Step 3: Share the raw `.info` between the float gate and enrich

In `apply_float_gate`, store the raw `info` dict on the record (`r["_info"] = info`) after
fetching it. In `enrich`, have `_fetch_info(t)` prefer `r.get("_info")` if present before
hitting the network; drop `_info` before serialization (so it's not persisted). Cache the
**raw dict**, not derived fields — enrich needs sector/summary/quote too.

**Verify**: with an injected `.info` fetcher that counts calls, a symbol that passes M14 and
is selected triggers **one** `.info` fetch, not two. Parity snapshot unchanged. `_info` is
not present in the serialized `wl`.

### Step 4: Full parity + suite

Run the parity snapshot and the whole suite.

**Verify**: parity snapshot byte-identical; `python3 test_bot.py` → exit 0, including the
existing byte-identical-membership locks (they must still pass — if any fails, the
consolidation changed selection, STOP).

## Test plan

- The parity snapshot test (Step 1) becomes a permanent regression test.
- A `.info`-call-count test proving one fetch per selected symbol.
- Confirm existing selection locks still pass (they are the real guard here).
- Mutation: make pass 2 recompute a *different* value and confirm the parity test fails.

## Done criteria

- [ ] `python3 test_bot.py` exits 0; all existing selection/membership locks still pass
- [ ] Parity snapshot is byte-identical before vs after (report/state unchanged)
- [ ] `build_interpretation` and `entry_readiness` run once per symbol per run (verified by a call-count test)
- [ ] A selected symbol fetches `.info` once, not twice (verified by a call-count test)
- [ ] `_info` is not persisted in `wl`
- [ ] No change to `rank_key`/`select_top`/`analyze_ticker` outputs; no `LOGIC_VERSION` bump
- [ ] `git status` shows only `Super_stock.py`, `test_bot.py`
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and revert if:
- The parity snapshot differs by even one byte at any step — the consolidation changed
  behavior; do not "accept" the diff.
- Any existing byte-identical-membership / selection lock fails.
- You discover an indicator has a hidden dependency on being recomputed (e.g. it mutates
  `df` in place) so caching changes a later pass's input — report it.
- Sharing `.info` changes `enrich`'s output for any field (it needs the full dict) — report.

## Maintenance notes

- The safe invariant is: **first pass computes as today; later passes read the cache.** Never
  refactor the compute itself while consolidating — that's how a rounding/ordering diff
  sneaks in.
- Reviewer must treat the parity snapshot as the acceptance criterion, not the perf win.
- This is the lowest-priority plan in the batch precisely because the risk/reward is worst;
  it's included for completeness. If the daily job is not actually time-constrained, consider
  deferring it indefinitely.
