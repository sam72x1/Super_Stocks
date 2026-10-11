# ALERTS70 — result

**Verdict: HISTORICAL ALERT SIGNAL NOT VALIDATED** — by the sealed criteria of `A70_PREREG.md`
(SHA-256 `d8227f46…b8da`, pinned in `a70_eval.py`; the seal commit `53bdf5bd0` was pushed before any alert outcome
was read). One run (`python3 faisal_engine/alerts70/a70_eval.py test` → `data/result.json`). Research only: no
production, Telegram, schedule, threshold, membership or frozen-axis change; the sealed R70 code is imported, not
modified. No agents or workflows were used.

## 1. The live alert paths (code evidence, not terminology)

| stream | path | when | trigger | what it stores |
|---|---|---|---|---|
| **liquidity cards (tested)** | `operator_entry_live.py` `main` → `Super_stock.live_watch_universe` (`Super_stock.py:15720`) → `scan_liq_stages` (`:16517`) → `liq_stage_events` (`:16000`) → `apply_alert_filter` (`:16894`) → `build_liq_stage_alert` (`:17805`) → `send_telegram` (`operator_entry_live.py:682`, `main`) | intraday, a cycle every ~60 s (`INTERVAL_DEFAULT`), 04:00–20:00 ET, `operator_entry.yml` (pre/open/post crons + backups, chained workers) | **M1** = first completed minute with volume ≥ 3× the prior average, ≥ $30,000 over 3 minutes (`LIQ_MIN_USD` `:15591`, `LIQ_CUM_MINUTES` `:15634`), a ≥ 5% minute move (`LIQ_MIN_MOVE_PCT` `:15611`) closing in its upper half (`LIQ_CLOSE_POS_MIN` `:15599`); from 2026-09-09 also the parallel trigger ($100,000 cumulative and close ≥ 20% above the prior close, `LIQ_TC_USD`/`LIQ_TC_PCT` `:15645-15646`); M5/M30/pulses/exit follow the anchor | `op_entry_state.json` `LIQ:<sym>` (stamped after a successful send, pushed each cycle) · delivered **M5** cards appended to `tier_fwd_ledger.jsonl` by `record_tier_fwd` (`Super_stock.py:17489`, called at `operator_entry_live.py:697` after the send) |
| «هنا الدخول» | `scan_operator_entry` (`:15808`) → `build_operator_entry_alert` (`:15855`) → `send_telegram` (`operator_entry_live.py:765`, `main`) | same worker | operator-entry rules on the same minute bars | `{sym: date}` stamp in the same state file — day only, no price |
| ignition radar | `ignition_live.py` (send at `:683`) → `build_ignition_alert` (`:19856`) | intraday segments, `ignition.yml` | volume jump + break of the critical level | `ignition_log.json` (117 fires, price, time from 07-13) |
| pullback monitor | `pullback_live.py` (send at `:146`) → `build_live_alert` (`:19407`) | 15–30 min slots, `pullback_monitor.yml` | sweep / buy zone / break / premarket / dump | `live_alert` `{kind: date}` per watched stock in `weekly_watchlist.json`, overwritten daily — **not extracted** (no price, no time, bot list only) |

Card headline of the liquidity stream in the current code: «🔥 $SYM · price · صاعدٌ X% عن الأمس»
(`build_liq_stage_alert`, `:17869-17880`). The card text changed during the window (it was compressed after the
2026-08-20 report) and no card text is stored per alert, so the wording the owner saw on a given day is not recorded.

**The 1,016-row ledger** (2026-08-24 → 09-29) is established to be the **M5 stage of the liquidity cards**, written only
after the card was delivered. **That the owner used this stream** is in the code itself: the owner's dated reports on
these cards are preserved verbatim — `$RITR` 2026-08-20 (M5 at $0.1261, +84% minutes later, «اختصر الرساله…»,
`build_liq_stage_alert` docstring `:17808-17811`) and 2026-08-28 «معطيني تنبية أول دقيقة وانه مرتفع 70٪… مرتفع أصلا من قبل»
(`liq_stage_events` `:16258`). **Not established:** that the owner's present recollection refers to this stream alone —
the repository holds no record of which cards the owner acted on. Hence the liquidity stream is tested and the other
streams are classified descriptively.

## 2. The record

- **1,206 liquidity anchors**, 390 symbols, 31 sessions (2026-08-17 → 09-29): local state snapshots 327 · state and
  ledger 719 · ledger only 160. Trigger minute (`anchor_ms`) for all; alert price for 1,127; first commit carrying the
  M1 stamp (an upper bound on the send time) for 1,033. `prev_close` is never stored for M1 in the state (0 of 1,033;
  the ledger has it for M5 cards); the pre-alert path (`pre_hi`, `pre_usd`) exists for 630.
- **Snapshot coverage:** 12,643 of the 35,656 historical snapshots of `op_entry_state.json` are in the local object
  store; the final snapshot of the day is local on 18 of 31 sessions; on 13 sessions (09-09 → 09-25) only 4–116 of
  1,371–1,964 are local, so an alert after the last local snapshot that never reached M5 is missing from the record.
- **Observation record:** 13,957 symbol-days (a `LIQ:` key that session — written only when the scanner fetched the
  symbol's minute bars — or proven by an alert). Unobserved symbol-days are excluded, never labelled negative.
- **Network disclosure:** the clone is partial (`blob:none`). The first extraction run let git download historical
  `op_entry_state.json` snapshots on demand from the project's own GitHub remote before it was stopped: 2,866
  on-demand packs in that hour, ≈25 MB compressed (the 12,616 distinct snapshots now local are ≈612 MB as JSON); the
  earlier R70 history reads did the same for other files. No market-data, Telegram or paid endpoint was called. Every
  git read of this folder now runs with `GIT_ALLOW_PROTOCOL=file` and only local blobs are read (guard G6).
  Consequence: the extraction is reproducible against this object store; another partial clone holds fewer snapshots
  and would give a smaller record.

## 3. Linkage to the +70% events (R70 definition, unchanged)

Alert day = the **decision session** (the first regular close after the alert: after-hours alerts belong to the next
session — 209 alerts). Classes relative to the nearest unfinished tool episode (launch L, crossing D1, peak P):

| per alert (1,206) | n | | per alert episode (705) | n |
|---|---|---|---|---|
| BEFORE_START | 61 | | linked to an event | 113 |
| START_DAY | 52 | | — first alert before the +70% level | 90 |
| UNDERWAY_PRE70 | 68 | | — BEFORE_START / START_DAY / UNDERWAY | 33 / 29 / 28 |
| AT_OR_AFTER_70 | 17 | | — AT_OR_AFTER_70 / AFTER_70 / UNKNOWN_SPLIT | 4 / 12 / 7 |
| AFTER_70 | 78 | | unlinked runs of alert sessions | 592 |
| NO_EVENT_WITHIN_H (10 sessions) | 765 | | — no event / censored | 520 / 72 |
| CENSORED · UNKNOWN_SPLIT · NO_BARS | 111 · 24 · 30 | | | |

- **Eligible events** (tool episodes, quality OK, D1 in (08-17, 09-29], symbol observed in [L−10, D1]): **119 on 107
  symbols** (57 excluded: split or unobserved). First linked alert **before the +70% level: 80 (67.2%, Wilson 95%
  58.4–75.0)** — before the start 26 (21.8%), on the start session 26, underway 28; at/after the level 9; **no alert 30**.
- **Lead time** (first alert of the 90 episodes alerted before the level; sessions, day resolution): to the launch
  q25/median/q75 = −1 / **0** / +3; to the +70% close q25/median/q75/q90 = 0 / **3** / 8 / 11; **32 of 90 (35.6%) on
  the crossing session itself**.
- **Gain at alert** (alert price ÷ trough close − 1; START_DAY + UNDERWAY first alerts): q25/median/q75 = 18.6 /
  **25.2** / 38.4%. This is the alert's own intraday price; nothing else here is intraday.
- **Burden:** 30.75 alerted symbol-days per session; **91.0% of alerted symbol-days (613/674) had no +70% within 10
  sessions**; 765 of 1,041 classified alerts (73.5%) had no event; per alert episode, 90 of 705 (12.8%) preceded the
  +70% level of an event.

## 4. The sealed test (window 2026-08-17 → 09-24, `f10` from the close of the decision session)

| | alerted | comparison | ratio (97.5%, ticker-cluster bootstrap) |
|---|---|---|---|
| **K1** vs observed, not alerted | 61/674 = 9.1% | 555/10,941 = 5.1% | **1.784 [1.21, 2.436]** |
| **K2** vs matched control (same session, price bucket, nearest ret1/volx percentile) | 61/674 = 9.1% | 60/674 = 8.9% | **1.017 [0.60, 1.705]** |

- Floors met: 674 alerted evaluable symbol-days (≥ 300), 39 distinct positive events (≥ 20), 674 pairs (≥ 250).
  K1 lower bound above 1, K2 lower bound below 1 ⇒ **NOT VALIDATED**.
- Matching left a residual volume gap (median volx 11.79 alerted vs 4.12 controls; ret1 2.73% vs 2.05%) — the
  controls carried *less* volume and exploded at the same rate.
- **Reading:** alerted symbol-days explode more often than other watched symbol-days, but no more often than watched
  symbol-days with the same daily price and volume move. The alert carries no information beyond what the session's
  daily bar already shows.
- Sensitivity (preregistered), sessions whose final snapshot is local: K1 2.016 [0.976, 3.276] · K2 1.125 [0.462,
  2.444]. Strict label `y10`: K1 1.484 [0.96, 2.046] (95%).
- Post-hoc, not preregistered (`a70_posthoc.py` → `data/post_hoc.json`): 49 of the 674 matched controls (7 positive)
  were symbol-days on which the scanner alerted after 16:00 the same day (the sealed rule moves that alert to the next
  session). Leaving all 129 such rows out: K1 1.822 [1.233, 2.471] · K2 1.109 [0.644, 1.878] — same verdict. For 795
  alerts that belong to their own session, the alert came at a median +20.1% above the prior close and **the session
  closed a median 5.0% below the alert price** (q25/q75 −12.1 / +1.9%; 544 closed below it).

**Predictions (kept as written):** P1 K1 > 1 ✓ · P2 K2 ≥ 1.5 ✗ (1.017) · P3 BEFORE_START under 25% of linked alerts ✓
(61/300 = 20.3%) · P4 median gain at alert above 20% ✓ (25.2%) · P5 under 50% of eligible events alerted before the
level ✗ (67.2%).

## 5. Early versus ordinary alerts — descriptive only

No discriminator was tested (the mission excludes a new indicator search). Descriptively: BEFORE_START alerts are 61
of 1,041 classified (5.9%), outnumbered 12.5 to 1 by alerts with no event; by recorded M5 tier, the share of
classified alerts that came before the +70% level is «قوي» 47/212 (22.2%) · «متوسط» 34/177 (19.2%) · «ضعيف» 59/363
(16.3%) — no tier isolates early alerts (`T-TIERLINK`/`T-STRONG-2` already measured the tier). `T-PRELINK`
(2026-09-25) found on 413 live and 44,151 reconstructed anchors no feature at the alert that separates later
explosions, and positioning between alert and explosion negative after cost. Side streams: «هنا الدخول» stamps —
BEFORE_START 58 · START_DAY 13 · UNDERWAY 44 · AFTER_70 57 · no event 649 · censored 88 · split 9 · no bars 32; ignition
fires — UNDERWAY 7 · BEFORE_START 1 · AFTER_70 2 · no event 99 · censored 5 · no bars 3.

**Reconciliation with the owner's experience:** the liquidity cards did come before the +70% level for two thirds of
the eligible events — the owner's memory of alerts arriving early is accurate. But they fire on the move itself
(median on the launch session, +25% already done), about 31 symbol-days per session, and 91% of them are not followed
by a +70% run; against symbol-days with the same daily move they are no more likely to explode.

## 6. What is missing (the observability gap, separate from the result above)

| item | status |
|---|---|
| raw intraday bars / trades around each alert | **missing** — minute bars were fetched live and discarded; no trades stored; Polygon ended 2026-09-29 and the owner declined renewal, so they cannot be rebuilt (daily bars are archived) |
| alert-time snapshots | **partial** — trigger minute, price, minute $ volume, vol_x, pre-path for most anchors; no card text; no `prev_close` for M1 in the state; snapshots after the last local one missing on 13 sessions |
| feature values at the alert | **partial** — daily features reconstructable from archived bars (used in K2); intraday features beyond the stored ones (order flow, minute path before and after the trigger) missing |
| rejection / anchor / cycle state at the alert | **missing** — the live-watch universe mixes lists; «تحت المتابعة» entries store no rejection code; no tested-level anchor or pivot-cycle stage at alert time |
| complete observation windows | **missing** — the record proves "fetched at least once that session", not continuous minute coverage; 23,013 history snapshots are on GitHub only (fetching them needs the owner's authorization) |

Logging rejection codes alone would not recover intraday trade pressure.

**Minimal diagnostic logging (described, not implemented):** at each delivered M1, where `record_tier_fwd` already
appends M5 rows, append one row to a ledger: symbol, `anchor_ms`, send time, alert price, prior close, move, minute
$ volume, vol_x, trigger tag, the universe list(s) the symbol came from, and for «تحت المتابعة» names the existing
`_REJECT_REASONS` code, the tested-level anchor and the pivot-cycle stage of that run; plus one coverage row per session
(universe size, symbols with bars, cycles, first/last cycle). All values are in memory at the send — no new request.
It only matters if an intraday source returns: the liquidity stream is silent since 2026-09-29.

## 7. Files, tests, reproduction

`a70_extract.py` (git history → `liq_alerts`, `entry_alerts`, `oe_days`; offline) · `a70_build.py` (links to the
R70 episodes and labels; `--check`) · `a70_eval.py` (sealed `test`) · `a70_posthoc.py` (post-hoc descriptives;
`--check`) · `test_a70.py` (G1–G8, all pass; `R70_FAST=1` skips the regeneration check) · `a70_mutate.py` (10
mutations, each felled exactly its guard, cleanly: `data/mutations.json`) · data: `liq_alerts.csv.gz`,
`entry_alerts.csv.gz`, `oe_days.json`, `alerts.csv.gz`, `obs.csv.gz`, `events.csv.gz`, `side.csv.gz`, `result.json`,
`post_hoc.json`, `mutations.json`.

## 8. Limits

Six weeks, one regime; outcomes on daily closes after the alert session (no intraday path after the alert); the
observation record is "fetched at least once that session"; local snapshot gaps on 13 sessions (sensitivity above);
survivorship of the bar archive (30 anchors without bars excluded); split windows excluded, not repaired; the
pullback-monitor stamps were not extracted. Passing tests show the pipeline does what the preregistration says, not
that any signal exists.
