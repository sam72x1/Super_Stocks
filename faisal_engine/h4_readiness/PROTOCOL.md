# T-H4b — daily + 4H readiness among real-time alerts · pre-registration (exploratory)

> Written 2026-10-12, before any four-hour number exists. Nothing was requested from Massive/Polygon or any other vendor.
> No workflow was created and no secret was moved. `faisal_engine/readynow/fwd/` was not touched. Production, READY
> rules, the radar, Telegram and schedules are unchanged, and nothing was committed. Counts quoted here come from
> `SIZING.md` and `COVERAGE.md`, which are generated offline by `h4p_sizing.py` and `h4r_coverage.py` (`--check`
> regenerates both).

## 0. Status, authorization and seal

- **Authorization.** On 2026-10-12 the owner wrote: «أريد متابعة بحث T-H4 … جهّز بروتوكولًا مسبق التسجيل للبحث فقط … توقّف
  بعد ذلك بانتظار موافقتي الصريحة على جلب البيانات».
  - This authorizes the protocol stage only. **Fetching needs a separate, explicit approval.**
  - This is a **new** pre-registration. T-H4's closed contract (`h4_prereg.md`, failed gate HV0) is not revived.
- **Seal.** The SHA-256 of this file is given in chat.
  - Commit and push are forbidden in this phase, so the seal carries no remote timestamp. That is weaker than the project
    rule («merged before any number»).
  - The fetch approval should therefore also allow pushing this file to the branch **before** the pilot.
  - Any later change is a dated amendment section appended below. The text above it is never edited.
- **Classification.** Every result of this study is **EXPLORATORY**. The alert window (2026-07 → 09) was already read by
  ALERTS70, READY70, SEQ70, READYNOW, the condition atlas and ALERTS100.
  - Nothing here is an independent validation.
  - **`INCREMENTAL_EDGE_SUPPORTED` cannot be reached in this phase.**

## 1. Question

Take real-time alerted runs. Use only bars that had closed before the alert. Do the two Faisal four-hour conditions that
can be rebuilt faithfully select more future +100% winners, at the same number of picks per decision session, than:

- their daily counterparts, and
- the existing baselines?

## 2. Population and outcomes (frozen)

- **Units.** The ALERTS100 alerted runs (`faisal_engine/alerts100/data/units.csv.gz`, SHA-256 `ef0573ec1dc6b9e1…`).
  - Labels are unchanged: WIN (66 runs, 65 events) and CTRL (544).
  - The 92 excluded runs stay excluded (censored or unknown split).
- **Primary population.** CTRL plus WIN runs whose first alert precedes the launch (`pre_move=1`, 29 winners): 573 runs
  over the decision sessions of A100's equal-burden table.
- **Secondary population.** Every WIN run (66) plus CTRL.
- **Outcome definitions are kept apart and never merged:**

  | id | definition | role |
  |---|---|---|
  | D1 | +100% on the **close** from the trough reference (the frozen label) | primary |
  | D2 | +100% on the **regular-session high** (`alt_definitions.w100_high` of the run's linked event; a CTRL run without an event stays CTRL) | robustness |
  | D3 | +100% **after the first priced alert** (`w100_after_alert`) | secondary |
  | D4 | timing class of the first alert vs launch and the +100% crossing (`cohort.csv.gz`), including SAME_SESSION_ORDER_UNKNOWN | capture is reported per class |

  - Under D3, runs with no priced alert are UNKNOWN, not CTRL. D3 is reported by the alert's session: pre-market,
    regular or after-hours.
  - YMAT|2026-09-09 is reported row by row under D1, D2 and D3. So are the other events that reach +100% only at an alert
    price: DBGI|2026-09-04, DXST|2026-09-29 and ONCO|2026-08-31.

## 3. Information set — strictly point in time

- **Daily bars.** The local TradingView regular-session bars, split-adjusted (`faisal_engine/data/rank/bars.json.gz`),
  used as they are.
- **Intraday bars.**
  - Source: Massive/Polygon **30-minute aggregates**, `adjusted=true`, 04:00–20:00 New York.
  - Timestamps are UTC milliseconds and are converted to America/New_York.
  - A bar is identified by its start; it is usable only once its **end** has passed.
- **Cutoff session t0\*.**
  - For an alert whose time is exact (liquidity card trigger minute, ignition `fired_at`): t0\* = ALERTS100's `t0`, the
    last regular close before the alert.
  - For a stamp whose time is only an upper bound (`operator_entry`, `pullback_monitor`), dated on its own `t0`: t0\* = the
    session before the stamp's date. The alert may have come before that date's close. This moves 85 runs back one
    session: CTRL 72, WIN 13 (5 pre-move).
- **Cutoff time C.** The regular close of t0\*: 16:00 ET, or the early-close time from `market_calendar.EARLY_CLOSES`
  (there are none in the window).
  - Every feature, the daily ones and every comparator included, is computed from information available at C.
  - Comparators are **re-evaluated at t0\***. ALERTS100's published equal-burden numbers are not reused, because they were
    read at `t0`.
  - The evening of t0\* and the pre-market of the alert day are deliberately excluded. This loses information but can
    never leak.
- **Equal-burden grouping.** Runs are grouped by `decision_t`, the session in which the alert reaches the user, exactly
  as in ALERTS100.
- **Launch-relative evaluation (winners only, secondary).** At the close of each session T−10 … T−1 before the launch,
  with C at that session's regular close.

## 4. Conditions (definitions fixed here; code is written only after the seal)

**Grids**, used by R4H-8 only:

- **G_APP (primary):** 04:00 · 05:30 · 09:30 · 13:30 · 17:30 · 20:00. It is inferred from the HUBC blind card and is weak
  evidence (n = 1).
- **G_NY (reported beside it):** 04:00 · 08:00 · 12:00 · 16:00 · 20:00.

A four-hour bar is the fold of the 30-minute bars inside one bucket: O = first, H = max, L = min, C = last, V = sum. Only
buckets closed by C are used. An empty bucket is dropped, never filled.

### R4H-2 → `X_HOLD5` (primary; grid-free by construction)

- **Code.** `three_cond_daily.exact_low_stability(daily, ext_bars, t0*, need=5, look=25)`, called by name.
  - The exact low is the minimum, over the last 25 sessions, of the extended-hours lows and the daily lows.
  - Its day is the first day that low was reached.
  - `bars_after` counts the daily sessions after that day up to t0\*.
  - **stable** = close(t0\*) above the low **and** `bars_after` ≥ 5.
- **Source.** This is the owner's own reading of the rule (2026-09-26): «الفريم اليومي يستخدم للحساب عدد الجلسات الثبات و فريم 4 ساعات عشان نعرف بالضبط قيمة ادنى قاع» together with «ثبات 5 جلسات».
- **Built for…** the «شروطك الثلاثة» daily tool, which feeds it end-of-day hourly bars.
  - Here it is fed 30-minute bars cut at C.
  - A minimum is the same whatever the bar size, so it is grid-free.
  - Feeding it bars after C would leak, and guard G-LOOK (§8) forbids that.
- **Daily counterpart `D_HOLD5`.** The same computation on daily bars only, with the extended candidates removed.
- **Secondary reading `X_HOLD5_BARS[G]`.** Counts the hold in four-hour bars of grid G (≥ 5 bars after the exact-low bar)
  instead of daily sessions. This is the other reading of «ثبات ٥ جلسات» on the 4H frame (`TG_20260905_09`). Reported,
  never primary.

### R4H-8 → `X_SWEEP[G_APP]` and `X_SWEEP[G_NY]` (primary)

| step | definition | source tag |
|---|---|---|
| base | For each session s in [t0\* − 6, t0\*]: B(s) = the exact low over the 25 sessions before s, held at the close of s − 1 for at least `STABILITY_MIN` = 3 sessions. | `IMG_0151` «حافظ ع قاعه لمدة 3 جلسات», `faisal_verbatim`; window `PIVOT_LOOKBACK`, `faisal_inferred` |
| sweep | A four-hour bar b in session s with B × (1 − 0.13) ≤ low_b < B × (1 − 0.015). | `PIVOT_SWEEP_PCT` = 13, `faisal_adopted` (Faisal's own examples 8–12%, EHGO ≈ 10%); `METHOD_HOLD_TOL` = 0.015, `engineering` — the live `pivot_cycle_state` boundary between hold and sweep |
| broken base | low_b < B × (1 − 0.13) is a broken base, not a sweep. | `pivot_cycle_state` rule |
| reclaim | The first four-hour bar b′ ≥ b (b itself allowed) with close ≥ B, closed by C, in sessions s … s + 2. | R4-SWEEP-01 «عودةٌ خلال جلستين», V4 engine parameter — `engineering` |
| recency | b′ falls in [t0\* − 4, t0\*]. | `engineering` (one trading week) |
| still above | Daily close(t0\*) ≥ B. | — |

`X_SWEEP[G]` = 1 when any sweep and reclaim satisfies every row.

**Daily counterpart `D_SWEEP`.** The identical construction on daily bars, with the base taken from daily lows only.

### Combination and exclusions

**Combination.** `D_x ∧ X_x` is computed only if the gate holds: `X_x`'s winners minus `D_x`'s winners at equal burden
has a point estimate > 0. Otherwise it is not computed. No other combination is tested.

**Excluded, with the reason:**

| rule | reason |
|---|---|
| R4H-1, R4H-3, R4H-5 | no calculation in the source; any version would be a proxy |
| R4H-4 | direction only; also, C excludes the evening and pre-market it needs |
| R4H-6 | closed axis T-SUPDEF |
| R4H-7 | closed axis T-CANDLE |
| R4H-9 | targets, not readiness |

## 5. Comparisons at equal burden

The comparison reuses ALERTS100's `take` and `baselines` logic **by name and without change**.

- **Burden.** In each decision session, k is the number of runs the candidate flag selects. Every comparator then picks
  k runs in that session.
- **Ranking comparators:**
  - `CAPIT_TC` (`capit`)
  - `DROP5` (−`r5`)
  - `VOLAT` (`range20`)
  - `VOLUME` (`v1x`)

  All are read at t0\*. Missing values go last; ties are broken by symbol.
- **Binary comparators:**
  - `BOT_READY` (operational READY at t0\*)
  - `TC_TECH`
  - `ATLAS_READY_1`
  - `NEAR_WATCH` (`src` = near-watch at t0\*, i.e. Watch without READY)
  - the condition's own daily counterpart

  Flagged runs come first and the rest are filled at random. Wins are scored as the **expectation** of that fill, so no
  draw is made.
- **Random comparator.** k × the session's base rate, as an expectation.
- **Population.** Runs evaluable for both the flag and its daily counterpart (§6). Every comparator is scored on the same
  runs.
- **Reported for every flag:**
  - runs flagged, in total and per session;
  - winners captured;
  - precision with a Wilson 95% interval;
  - recall of the population's winners;
  - the difference against each comparator, with a 1,000-draw symbol-cluster bootstrap (fixed seed);
  - the difference against the **strongest** comparator, recomputed as the maximum inside every draw, at **98.33%**
    (Bonferroni over the three primary flags);
  - lead from the alert's decision session to the launch and to the first +100% close (q25 / median / q75);
  - breakdowns by chronological third (cuts 2026-08-13 and 2026-09-03), price (< $1 / ≥ $1), the first alert's session
    (pre-market / regular / after-hours), first stream and list at t0\*;
  - every UNKNOWN count.
- **Raw versus incremental.** For each flag, its raw association (AUC, as in ALERTS100) and the same association within
  terciles of decline (`r5`), volatility (`range20`) and volume (`v1x`).
- **D4 windows.** Winner capture is reported by the first alert's class: T−10…T−7, T−6…T−3, T−2…alert, launch day and
  later.
- **Launch-relative diagnostic (winners only).** At T−10…T−1, whether each flag was on, reported **beside** the controls'
  rate at t0\*. The anchors differ, so the comparison is labelled descriptive.

## 6. Evaluability and decision rule (fixed before any number)

**Evaluability.** A run is evaluable for a flag when its 32-session window has bars on at least 90% of sessions and on
every one of the last 7 sessions. That means 30-minute bars for X flags and daily bars for D flags. A run that fails is
**UNKNOWN**: counted and reported, never set to false.

The labels, in order:

1. **`INSUFFICIENT_DATA`** if any of these holds:
   - a pilot gate PG1–PG5 fails;
   - fewer than 27 of the 29 primary winners, or fewer than 490 of the 544 controls, are 4H-evaluable;
   - every primary flag selects fewer than 10 runs.
2. **`PROMISING_BUT_UNVALIDATED`** (the best label reachable here) if at least one primary flag (`X_HOLD5`,
   `X_SWEEP[G_APP]`, `X_SWEEP[G_NY]`) meets all of:
   - **a.** Under D1, the 98.33% lower bound of its winners minus the strongest comparator's is above 0.
   - **b.** Its point estimate against its own daily counterpart is above 0, so the 4H frame adds to the daily one.
   - **c.** Its point estimate against the strongest comparator is ≥ 0 in every chronological third that holds a winner.
   - **d.** Its point estimate is above 0 under D2.
   - **e.** For at least half of its captured winners, the first alert came before the launch.
3. **`NO_INCREMENTAL_EDGE_FOUND`** if coverage is adequate and no primary flag meets a–e.
4. **`INCREMENTAL_EDGE_SUPPORTED`** is not reachable in this phase. It needs a separate pre-registration on alerts after
   the seal.

**Power, stated in advance.**

- In ALERTS100, the 95% intervals of flag-minus-ranking differences at a burden of about 29 runs spanned 6 to 9
  winners (`TC_TECH` and `ATLAS_READY_1` rows of §6).
- So an edge smaller than about 5 winners cannot meet criterion a, which is read at 98.33% and is wider still.
- A `NO_INCREMENTAL_EDGE_FOUND` result therefore does not show that no edge exists.

**No moving targets.** No threshold, window, grid, tolerance, cutoff or definition changes after any number has been
seen. A gate that fails is reported, not loosened.

## 7. Massive verification before any download — the pilot

The pilot comes first. It uses **29 requests** (`SIZING.md`).

**Sample.** 20 symbols chosen by hash:

- DXST, because its local 30-minute bars give a cross-check;
- four symbols carrying a reverse split within 120 calendar days before t0 (`split120`, `SPLIT_LOOKBACK_DAYS`): AMIX, WXM, SLMT, ZCMD;
- AAPL as the liquid witness.

**Gates:**

| gate | check | on failure |
|---|---|---|
| PG0 | The key is readable by the fetch environment without being printed, and the host is allowed by the network policy. Judged by the status of the first request only. | stop |
| PG1 | Every pilot request returns HTTP 200 with status OK. | 401/403 ⇒ stop: the plan lacks access |
| PG2 | Every pilot symbol has bars in the first 3 sessions of its earliest window (from 2026-06-01), so history reaches the window start. | stop |
| PG3 | AAPL has bars before 09:30 and after 16:00 on ≥ 95% of pilot sessions, and ≥ 10 of the 20 symbols have a bar outside 09:30–16:00 in their windows. | stop |
| PG4 | Every 30-minute bar starts on :00 or :30 New York. For 3 hash-chosen symbol-days, the 30-minute OHLC equals the fold of the one-minute bars exactly, and volume is within 0.5%. | stop |
| PG5 | The regular-session fold (09:30–16:00) and the local daily bars agree within 1% on low, high and close on ≥ 95% of pilot symbol-sessions found in both. The split-flagged symbols are included. | stop |
| PG6 | Report only: missing sessions, empty answers, and windows where bars start or stop inside the window (possible ticker renames). | — |

After the pilot, its full result is reported. The main fetch (≤ 559 requests, `SIZING.md`) runs only if PG0–PG5 all pass
**and** the owner's approval covers it. No gate is re-run with a looser threshold.

## 8. Guards in the tool phase (each must fall to a mutation)

| guard | check |
|---|---|
| G-LOOK | Every feature is recomputed after randomizing all bars that end after C; the result must be identical. |
| G-SPLIT | Every bar before a synthetic split day is multiplied by k; the features must not change. |
| G-GRID | Buckets match the declared grids, and no bucket ending after C is used. |
| G-CUT | t0\* follows §3, including the 85 moved runs. |
| G-REBUILD | `--check` regenerates every output byte for byte from the cached raw bars. |
| G-SEALED | The sealed A100, atlas and ALERTS70 files are unchanged by hash. |
| G-FWD | No path under `readynow/fwd`. No network library in the analysis code; the fetcher is a separate file. |

## 9. Storage and scope

- Raw vendor bars stay **outside git**, in the session scratchpad, because the repository is public.
- With separate permission, the following may be committed later: a manifest (parameters, counts, SHA-256 of each cache
  file), per-run flags and aggregates.
- Not touched by this study: production, READY, the radar, Telegram and schedules. No forward logger is created.
  `fwd/` is not touched.

## 10. Predictions (published as they fall)

| id | prediction |
|---|---|
| P1 | `X_HOLD5` does not beat the strongest comparator (point estimate ≤ 0). Reason: in ALERTS100, winners had held the daily low for fewer sessions than controls (median 1 vs 6). |
| P2 | `X_HOLD5` and `D_HOLD5` agree on ≥ 85% of evaluable runs. |
| P3 | `X_SWEEP[G_APP]` and `X_SWEEP[G_NY]` agree on ≥ 90% of evaluable runs. |
| P4 | Each sweep flag selects fewer than 15% of primary runs. |
| P5 | The final label is `NO_INCREMENTAL_EDGE_FOUND` or `INSUFFICIENT_DATA`. |
| P6 | The pilot passes PG1–PG5. |

## 11. Gaps this protocol cannot close

1. **Faisal's frame.** The evidence is one blind card. Both grids are declared, and R4H-2 is grid-free.
2. **Faisal's other 4H readings.** Five of his nine are either not faithfully testable or belong to closed axes.
3. **Power.** There are 29 pre-move winners.
4. **No untouched historical holdout.** Every period was read before.
5. **Massive plan.** Tier, history depth and rate limits are unknown until PG1–PG3.
6. **Ticker renames.** A run whose ticker changed between the window and today may return nothing. Such runs are counted
   UNKNOWN (PG6).
7. **Upper-bound alert times.** The safe cutoff t0\* drops up to one session of information for 85 runs.
8. **Where the fetch runs.** The key is absent from this container. Either the owner adds it as an environment secret,
   which needs no repository change, or a temporary workflow is used, which needs commit and push.
9. **Seal strength.** The seal is local until a push is allowed.
