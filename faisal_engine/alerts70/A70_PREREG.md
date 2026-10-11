# ALERTS70 — preregistration (sealed before any alert outcome is read)

**Status:** sealed 2026-10-11. SHA-256 pinned in `a70_eval.py`; `a70_eval.py test` exits 9 if this file changes.
One run, no tuning. Research only: no production, Telegram, schedule, threshold, membership or frozen-axis change;
no external request (the clone is partial — every git read runs with `GIT_ALLOW_PROTOCOL=file`). The sealed R70
contract and code are reused by import and are not modified.

**What has been read before this seal:** code paths, schedules, payloads, record formats; counts of alerts,
observed symbol-days and events (no split by alert status, no outcome rate, no lead time, no alert class).

## 1. The stream under test
The liquidity cards of `operator_entry_live.py` (`operator_entry.yml`): every ~60 s during the extended session the
scanner fetches minute bars for every symbol of the bot's live-watch universe (`live_watch_universe`, uncapped:
pullback, candidates, pressure radar, «تحت المتابعة», hunter list, recent movers); `scan_liq_stages` →
`liq_stage_events` fires **M1** at the first completed minute with volume ≥ 3× the prior average, at least $30,000 over
three minutes, a ≥ 5% minute move closing in its upper half — or (from 2026-09-09) the parallel trigger ($100,000
cumulative and close ≥ 20% above the prior close); M5/M30 follow from the anchor. Card headline:
«🔥 $SYM · price · صاعدٌ X% عن الأمس». Owner filter (`alert_filter.json`): M1 and M5 are never muted after 2026-08-18.

**Record used:** the union of (a) anchors whose M1 is stamped in local snapshots of `op_entry_state.json` (stamped after
a successful send; failed sends are rolled back) and (b) delivered M5 cards in `tier_fwd_ledger.jsonl` (an M5 card
implies its M1). 1,206 anchors · 390 symbols · 31 sessions (2026-08-17 → 2026-09-29).
**Observation record:** a `LIQ:<symbol>` key dated that session exists only if the scanner fetched that symbol's minute
bars (`scan_liq_stages`: the state is written only when bars came back) ⇒ per-symbol, per-session observation.

## 2. Unit, window, outcome
- **Unit:** an observed symbol-day (symbol, session t), t ∈ [2026-08-17, 2026-09-24] (t + 10 sessions ≤ 2026-10-08,
  the last complete archived bar). Symbols without archived bars are counted and excluded.
- **Exposure:** `alerted` = at least one liquidity anchor whose **decision session** is t — the session of the
  first regular close (16:00 ET) after the alert: pre-market and regular-hours alerts belong to their own date,
  after-hours alerts to the next session (otherwise the after-hours move would leak into the outcome). An alert
  also proves observation of that symbol-day.
- **Primary outcome `f10`** (R70 definition, unchanged): within sessions (t, t+10], measured from the close of t,
  a close-to-close day ≥ 50% or close_k / min(close_t … close_{k-1}) − 1 ≥ 70%. `DURING` (the tool had already detected
  an episode not yet past its peak), `UNKNOWN_SPLIT` and `CENSORED` rows are excluded and counted.
  Measuring from the close of the alert day is deliberately conservative for alerts (it excludes the alert-day move)
  and symmetric for both groups (no intraday price exists for non-alerted symbols).
- **Secondary outcome `y10`** (R70 strict): an episode launches after t and is detected within t+10 (descriptive).

## 3. The one test
- **K1** rate(f10 = POS | alerted) / rate(f10 = POS | observed, not alerted).
- **K2** rate(f10 = POS | alerted) / rate(f10 = POS | matched control). Matched control: for each alerted symbol-day,
  one observed non-alerted symbol-day **on the same session**, in the same traded-price bucket (< $1 · $1–3 · $3–10 ·
  ≥ $10, split-unadjusted close), nearest by |Δ within-session percentile of ret1| + |Δ within-session percentile of
  volx| (ret1 = close-to-close return of t; volx = volume of t ÷ median of the previous 20 sessions), without
  replacement, ties broken by symbol; no candidate in the bucket ⇒ unmatched (counted, dropped from K2).
  K2 asks whether the alert carries information **beyond the price and volume move visible in the daily bar**.
- **Uncertainty:** ticker-cluster bootstrap, 1,000 resamples, seed 20261011, **97.5%** intervals (Bonferroni, 2 tests).
- **Sample floor:** at least 300 evaluable alerted symbol-days, 20 distinct positive (symbol, crossing) events among
  them, and 250 matched pairs; otherwise **INSUFFICIENT HISTORICAL ALERT DATA**.
- **Verdict:** **HISTORICAL ALERT SIGNAL VALIDATED** only if K1 and K2 lower bounds both exceed 1.0 (above the floor);
  otherwise **HISTORICAL ALERT SIGNAL NOT VALIDATED**. Validation would show discrimination and timing information,
  not a profitable trade (no execution or cost model here; `T-PRELINK` found positioning negative after cost).

## 4. Descriptive (preregistered, never decisive)
- **Alert classes** relative to the nearest tool episode (launch L = trough + 1, crossing D1, peak P; R70 episodes):
  BEFORE_START (alert day < L) · START_DAY (alert day = L, alert price below the +70% level from the trough close) ·
  UNDERWAY_PRE70 (L < day ≤ D1, alert price below that level) · AT_OR_AFTER_70 (alert price already at/above it) ·
  [«day» = the decision session above]
  AFTER_70 (day > D1, before the peak) · NO_EVENT_WITHIN_H · CENSORED · UNKNOWN_SPLIT · NO_BARS. Counted per alert and
  per alert episode (one per symbol and linked event; unlinked alerts grouped by runs of consecutive alert sessions).
- **Lead time** (sessions, day resolution) alert → L and alert → D1; **gain at alert** = alert price ÷ trough close − 1
  (the alert's own intraday price — the only intraday evidence; daily bars are never presented as intraday).
- **Eligible-event capture:** tool episodes (quality OK) with D1 in (2026-08-17, 2026-09-29] on symbols the scanner
  observed in [L−10, D1]: share whose first linked alert is BEFORE_START / START_DAY / UNDERWAY_PRE70 (= before the
  +70% level), and share BEFORE_START.
- **Burden:** alerted symbol-days per session; share with f10 = NEG; share of alerts with NO_EVENT_WITHIN_H.
- **Sensitivity:** K1/K2 on sessions whose final state snapshot is local (alerts after the last local snapshot on the
  other sessions may be missing from the record and could sit in the control group).
- **Side streams:** «هنا الدخول» stamps (950) and ignition fires (117) classified the same way; M5 tier shown, not tested
  (`T-TIERLINK`/`T-STRONG-2` already measured the tier).

## 5. Predictions (kept if wrong)
- **P1** K1 point estimate > 1.
- **P2** K2 point estimate ≥ 1.5 (the live-sample ratio in `T-PRELINK` was 2.7× for +100%; different outcome/control).
- **P3** BEFORE_START is under 25% of linked alerts (the trigger fires on the move itself).
- **P4** median gain at alert for START_DAY + UNDERWAY_PRE70 alerts is above 20%.
- **P5** under 50% of eligible events have an alert before the +70% level.

## 6. Limits known now
Six weeks, one market regime; daily bars after the alert (no intraday path after the alert); the observation record is
"fetched at least once that session", not continuous coverage; on 2026-09-09 → 09-25 only late-session snapshots are
local (sensitivity above); survivorship of the bar archive; anchors on symbols without archived bars are excluded.
