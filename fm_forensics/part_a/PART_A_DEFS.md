# Part A — measurement definitions (written before any number · 2026-10-27)

Owner order «الأعطالُ أوّلًا، ثمّ إعادةُ بناء القبول من البيانات» — Part A only. Diagnostics, not experiments: nothing here
is shipped, no threshold changes, no Telegram. Every definition below is fixed **before** the runner probe returns a number;
a definition that turns out wrong is reported as wrong and is not edited to fit the result.

## D1 — A2 «تنبيهُ أوّلِ قفزة» (the alert the bot calls «هنا الدخول») · how late is it?
- **Population:** every distinct anchor `(symbol, day, anchor_ms)` in `op_entry_state.json` on `origin/main` from 2026-10-14
  (Polygon back ≈10-15) to 2026-10-27, read from git history sampled one revision per 10 minutes plus the last revision of
  each day (`walk.py`; the sampling is printed; an anchor created and replaced twice inside 10 minutes can be missed).
  Anchors whose `day` is before 2026-10-14 are carry-over from the first sampled revision and are excluded.
  **Sent** = the anchor carries a non-empty `sent` list (the bot delivered at least one stage message).
- **Bars:** Polygon `/v2/aggs/ticker/{sym}/range/1/minute/{day}/{day}` `adjusted=true` (extended hours, 04:00–20:00 ET).
- `alert_px` = `anchor_price` recorded by the bot. `t_alert` = `anchor_ms`.
- `px_15` = close of the last minute bar with start ≤ `t_alert` − 15 min on the same day (UNKNOWN if none).
- `peak_before` = max high of bars with start < `t_alert` (same day, from 04:00 ET).
- `low_before` = min low of bars with start < `t_alert` (same day).
- `prev_close` = previous regular-session close (Polygon daily, adjusted).
- **Missed (primary, the owner's column) = `alert_px / px_15 − 1`.** Secondary: `alert_px / prev_close − 1` and
  `alert_px / low_before − 1`. The governing number is the **median of the primary**; above 10% ⟶ «the alert reports the past».
- **Cause split (three causes, three fixes):**
  - *definition* — `trig == "T-C"` (fires on a close ≥ +20% over yesterday's close: after the move by construction) vs R1;
  - *source/latency* — `first_seen` commit time − `anchor_ms` (minutes from the bar to the state commit; includes the
    worker cycle and the push);
  - *cron/coverage* — anchors on minutes when no worker was running cannot exist; measured from worker run start/end times.
  - *gate/coverage deferral (added before any number)* — the production `liq_stage_events` is replayed minute by minute on the
    day's Polygon bars with a fresh state, T-C on (yesterday's close), **no operator gate, no alert filter**, positional
    closed-bar rule (as `kasih_scan.first_anchor`) ⟶ the earliest anchor the definition itself allows. `deferral` = first live
    anchor of (sym, day) − replay anchor, in minutes. Reason: the operator gate (`Super_stock.py` `scan_liq_stages`) mutes a
    candidate with no ≥1000-share print and **clears its state with no log line**, so its mutes cannot be counted from saved
    data; the replay is the only way to see what it deferred. Deferral ≥ 5 min ⟶ lateness from the gate/coverage path;
    replay missed ≈ live missed ⟶ lateness is in the definition itself.

- **Amendment 2026-10-28 (after the first number — a measurement fault, not a criterion change).** Run `40597208620` read
  Polygon minute and daily bars with `adjusted=true`, but `anchor_price` is the raw price the live worker saw on its day. A
  reverse split after the alert day therefore puts the bars on a different scale: 41 of 566 rows (13 symbols — BDRX DKI FRGT
  GP HCAI IPW LHSW NIVF NUWE NWGL SBFM SXTC TWG) compare a raw alert price with split-multiplied bars (e.g. TWG 10-14 alert
  0.0761 vs bar 15 minutes earlier 9.04). The first run's numbers stay published as they came out (median 8.1%). The governing
  A2 number is re-measured by mode `a2raw`: the same definition with `adjusted=false` minute and daily bars, so the bars are on
  the alert's own scale. Everything else in D1 (population, columns, the 10% line, the cause split, the replay) is unchanged.

## D2 — A2-b · RSI band × outcome (alerts vs same-day monitored universe)
- Alerts: union of `tier_fwd_ledger.jsonl` (2026-08-24 … 2026-09-29) and the D1 anchors (sent), one row per (symbol, day).
- `RSI14` = Wilder RSI on daily adjusted closes **up to day d−1** (`Super_stock.rsi` formula re-implemented identically).
- Outcome: `max high over sessions d+1 … d+10` (and `… d+20`) ≥ 1.5 × `close(d)` (`EXPLOSION_PCT` = 50 by name).
- Control: every symbol in that day's monitored universe (list `stocks` ∪ `near_watch.json`, read from the last git revision
  of day d) that had **no** anchor on day d, same RSI band, same outcome rule.
- Bands: ≤20 · 20–25 · 25–30 · 30–40 · >40. Columns also split by available borrow (<20k / ≥20k / UNKNOWN) from
  `ctb_log.jsonl` (latest value on or before d) — unknown stays unknown.
- «Not READY»: the symbol was not READY (`entry_status` ready) in any list snapshot of day d.

## D3 — A3-b · the 117 READY rows (`fm_forensics/READY_NOW_OUTCOMES.csv`)
- `P` = daily close on `first_ready` (adjusted). *Amended before any number (offline dry run):* `first_ready` is a list-snapshot
  date and 25 of 117 fall on a weekend ⟶ `P` = close of the last session on or before `first_ready`; the windows start the next session. **Swept** = min low over sessions 1…10 after ≤ 0.8 P.
  **Exploded** = max high over sessions 1…20 after ≥ 1.5 P. «Swept then exploded» = both, and the first explosion day is
  after the first sweep day. 2×2 printed with names.

## D7 — A3 · SXTC and DKI on their «تحت المتابعة» entry days (added before any number)
- Days = each `first_seen` of the symbol in `near_watch.json` history (SXTC 08-18 · 08-20 · 10-15 · 10-23 · 10-27; DKI 08-16 · 09-02).
- On day d the screener reads closes through d−1 (it runs before the open). Polygon daily adjusted.
- Printed: RSI14 (`Super_stock.rsi`), % above EMA30 and EMA50, 5-session close gain — against the live thresholds
  (`RSI_MAX_NOW` 35.78 · `RSI_NOW_HARD` 71.12 · `MA_GATE_MAX_ABOVE_PCT` 95.47 · `RECENT_RISE_BLOCK_PCT` 214.73) and the
  original ones (40 · 50 · 15 · 35). Descriptive only.

## D4 — A0③ · «شموع الفوليوم» on JEM and ELAB
- Bars: TradingView daily (`tv_data`, splits-adjusted, regular session) and Polygon daily as a cross-check.
- Window: the 120 sessions before the post day (JEM post ≈2026-10-23/24 · ELAB 2026-10-21).
- For k = 1…3: the k highest-volume daily candles in the window; report each candle's date, low, high, volume, and the
  union range [min low, max high] of those **below the current price**. Compare with Faisal's «2 > 2.20» (JEM) and
  «1.80 > 2.20» (ELAB). «Match» = Faisal's range overlaps the computed range and both ends are within 10% of it.
  The bot's definition is read from code (`Super_stock.py` `big_green`: a green candle ≥ 5× the 20-session average in the
  last 20 sessions → a boolean +10) — that part is a code reading, not a measurement.

## D5 — A1-c · depth of book and «Dp»
- One call each on CMMB: `/v3/quotes/CMMB?limit=5` and `/v2/snapshot/locale/us/markets/stocks/tickers/CMMB`; report the
  fields returned (depth = more than one price level per side). No other provider is called.
- Polygon `/v3/reference/conditions?asset_class=stocks&data_type=trade`: the official name/description of the conditions
  the code maps to «خوارزمي» («Average Price», «Derivatively Priced»).
- Off-exchange share (display only): for each active list symbol, all trades of 2026-10-27 from `/v3/trades`; share of
  volume with `exchange == 4` (FINRA TRF/ADF — off-exchange, which includes but is not limited to dark pools).

## D6 — A1-e · the tape fingerprint by Faisal's definition (tagged `faisal_verbatim`)
- From `TG_1850`/`TG_1853` (TRUG), `TG_2113` (ADIL), `TG_1828`/`1829` (ZCMD): window **W = 10 s**, **N ≥ 8** trades,
  every size ∈ {1, 2, 3, 5, 7, 10} or ≤ 10 shares, **≥ 3 price direction changes** inside the window, extended hours included.
- Verification: TRUG — the after-hours window 17:28:25–17:28:40 ET on each session 2026-07-13 … 07-31 (the post says
  «17:28:30-33»; the day is not visible); ADIL — 10:05–10:09 ET on days whose range covers 1.70–1.77 (Jul–Sep 2026);
  ZCMD — 2026-07-02 16:00–20:00 ET. *Added before any number:* TRUG is also read at 10:28:25–10:28:40 ET (the post's clock
  may be Riyadh time, UTC+3, = 10:28 ET in summer); both windows are reported, the 17:28 ET one is primary. Pass = the fingerprint fires on all three (owner's rule: 3 of 3, else the definition is
  wrong, not the idea).
- Three-year availability: one `/v3/trades` call on a 2023 session for TRUG — reports whether odd lots (condition 37)
  and extended hours are present.
