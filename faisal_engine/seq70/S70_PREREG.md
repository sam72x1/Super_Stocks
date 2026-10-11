# SEQ70 — preregistration (sealed before any validation or test outcome is read)

**Status:** sealed 2026-10-11. SHA-256 pinned in `s70_eval.py`; `s70_eval.py test` exits 9 if this file changes.
One run, no tuning. Research only: no production, Telegram, schedule, threshold, membership, frozen-axis
(ANCHOR_TWO_TOUCH/H6 · M2 · M3 · M4) or closed-axis change; no network request (every git read with
`GIT_ALLOW_PROTOCOL=file`). READY70 code and outputs are imported, not modified.

**Read before this seal:** the inventory below; discovery-window outcomes (2025-05-01 → 2025-12-31) in
`data/explore.json` and `data/dev_discovery.json`; counts of pivot-days per window (no outcome split by any
descriptor outside discovery). READY70 (sealed earlier) published validation/test-window rates for *other* rules
(stage 1, the READY location rule, drop/volatility/price controls); nothing for the descriptors below.

## 1. DATA_INVENTORY (local only)

| source | path | span | size | what it can carry |
|---|---|---|---|---|
| daily bars | `faisal_engine/data/rank/bars.json.gz` | 2024-05-01 → 2026-10-08 | 3,584 symbols · 612 sessions | OHLCV, TradingView, split-adjusted prices; volume adjustment across splits **uncertain** ⇒ rows with a split in the 60-session lookback are excluded from the primary test (29,575 of 174,796) |
| pivot-days (the tool's own pivot notion, point in time) | `faisal_engine/ready70/data/pi_obs.csv.gz` | 2025-05-01 → 2026-10-07 | 174,796 rows · 1,108 symbols · 2,738 spells (gaps ≤ 5 sessions) | identity M1–M3 per day, READY70 labels `f5/f10/f20`, `y5/y10/y20` |
| +70% episodes (bot detector recomputed on the bars) | `faisal_engine/ready70/data/episodes.csv.gz` | launches 2025-02 → 2026-10 | 3,842 (3,727 OK) | launch L = trough + 1, crossing D1, peak; split-near flagged |
| scan_explosions live log | `weekly_watchlist.json["explosions"]` git history | 2026-06-22 → 10-10 | 2,195 records · 638 symbols | logged events; recompute matches 95.0% of non-suspect records with bars |
| bot lists and states | `weekly_watchlist.json`, `near_watch.json` git history; `reject_log.json` | 2026-06-20 → 10-10 (reject log 09-15 → 10-10) | 339 pivot symbols on lists · 19,993 list-days (near_watch 17,349) | list membership, `cont_status`, pullback status, near_watch first/last seen, READY (`entry_status`) reconstructed; **no FOCUS/ENTRY state in the bot** |
| Faisal's dated classes | `fm_forensics/phase3/` | 2025–2026 | 41 tickers · 235 dated units; 4 independent pre-move units (`gt_audit`) | MENTION/WATCH/FOCUS/READY/ENTRY — too few to test |
| live intraday alerts | `faisal_engine/alerts70/data/` | 2026-08-17 → 09-29 | 1,206 liquidity anchors | alert time and price (ALERTS70: not validated) |
| research stage overlay | `faisal_engine/data/rank/rows.csv.gz` | 2026-07-09 → 10-08 | 65 sessions | research-engine labels, not production states |

## 2. POINT_IN_TIME_COVERAGE — what can be linked
- Pivot-days ↔ +70% episodes: **exact** (same bars, the bot's detector recomputed, labels from bars after t only).
- Bot list states ↔ events: only from 2026-06-20 (inside the test window); READY70 found 12 pre-launch +70%
  episodes inside the bot's pivot lists ⇒ **state-transition sequences of the bot cannot be tested**; they are
  described after the run (§6), never decisive.
- Faisal's states ↔ events: 4 independent units — not testable. Live alerts: 31 sessions (ALERTS70, done).

## 3. PRIOR_WORK_EXCLUDED (not repeated)
READY70 (stage states, drop/volatility/price controls; verdict B) · ALERTS70 (live alerts; not validated) ·
T-PRELINK (58 features at the alert) · the closed common-link verdict (574 qualified) · T-LINK100 (market-wide
+100%: `vol_x ≥ 3` and `ret5 > +20%` the day before — single-day traits, "hot already") · T-LINK100-2 (new 60-day
low) · the two-day pre-explosion probe (`vol_x` rises in [−2, −1], case-crossover, no control population) ·
T-PRESS / T-PRESS-Q / T-PRESS-BT / T-PRESS-BT-2 (pressure to the lowest candle; HOLD3) · T-DORMANT · T-WAKE ·
T-STABILITY · T-VOLBASE · T-CUMRISE · T-ACC · forensic phases 2–6 · every axis with `CLOSED_RC` (EDGAR, FILLOFF,
HRT, HS, PMGATE, RSI40, RSI_RANK, SESSIONS, SUPDEF, TRAIL, WAVES, FCOST). Not tested before: whether the *order*
"volume arrives while the 5-session price path is still down" adds information beyond the drop, the volatility and
the volume level themselves, inside the pivot population, against same-session matched controls.

## 4. Reconstruction on discovery (descriptive, `data/explore.json`)
- **E1 duration:** f10 rate by age in the pivot spell — 0–4 sessions 7.1% · 5–9 6.0% · 10–19 4.6% · 20–39 6.2% ·
  40–79 4.8% · 80+ 3.9% (base 5.0%); not a sequence of changes and likely a recent-drop proxy ⇒ not carried.
- **E2 event study** (within-session percentile among all clean pivot-days; chance median 0.50, top quintile
  0.20): from 20 to 3 sessions before the start L every descriptor sits at chance; at L−2/L−1 volume (`v1x` 0.60 →
  0.64, top quintile 0.28 → 0.33) and range (`tr5x` 0.60) rise while price sits low (mechanical: L−1 is the trough).
  Before the +70% crossing everything rises from about D1−5 (the move is under way).
- **E3 order** (10 sessions before L): volume in the top quintile without price 19.3% of events vs 8.0% of
  date-matched controls; partly mechanical (price is low before L by construction).
- **E4** three candidates declared after E1–E3: C-A (`v1x` top quintile ∧ `r5` < 0) 1.264 [1.032, 1.557] vs
  drop/volatility-matched controls — chosen by the written rule. **E5:** that matcher left flagged rows more
  volatile than controls; with the sealed matcher (calipers) C-A K-V 1.134 [0.92, 1.40], K-P 1.083 [0.86, 1.38];
  C-B 0.94 / 1.06; C-C 1.05 / 0.98 — **no lower bound above 1.0 on discovery once balanced.** The E4 rule would
  stop here; C-A is carried to one out-of-sample test because it is the strongest point in both comparisons and a
  single held-out test answers the question with unseen data (it cannot make a false positive more likely than the
  intervals below allow). Expected result: **NO_INCREMENTAL_EDGE_FOUND**.

## 5. SEQUENCE_HYPOTHESIS (one) and PRE_REGISTERED_TEST
- **H-S70:** on a pivot-day whose 5-session close return is still negative (`r5` < 0), a volume day in the
  session's top quintile of pivot-days (`v1x` within-session percentile ≥ 0.8; `v1x` = volume ÷ median volume of
  sessions t−60..t−11) — volume arriving before price turns — marks a higher chance of the +70% condition within 10
  sessions than (K-V) the same drop and volatility without that volume and (K-P) the same volume and volatility
  without the drop.
- **Unit:** clean pivot-day (symbol, session t): pivot identity true, no split dated in (t−60, t], descriptors
  computed from bars ≤ t. Decision at the close of t (daily bar; no intraday claim).
- **Outcome `f10`** (READY70, unchanged): within (t, t+10], a close-to-close day ≥ 50% or close_k / min(close_t …
  close_{k−1}) − 1 ≥ 70%; DURING / UNKNOWN_SPLIT / CENSORED excluded and counted. Distinct event = (symbol, t + f10_k).
- **Windows:** validation 2026-01-16 → 2026-05-15 · embargo 05-18 → 06-01 (10 sessions) · test 2026-06-02 →
  2026-09-24 (t + 10 ≤ 2026-10-08). Discovery 2025-05-01 → 2025-12-31 is not re-read by the test.
- **K-V:** each flagged row vs one non-flagged clean pivot-day of the same session and traded-price bucket (< $1 ·
  $1–3 · $3–10 · ≥ $10), within 0.10 on the within-session percentiles of `r5` and `range20`, nearest by their sum,
  without replacement, ties by symbol. **K-P:** the same with controls whose `r5` ≥ 0, within 0.10 on `v1x` and
  `range20`. No candidate ⇒ unmatched (counted).
- **Statistic:** ratio of f10 positive rates, ticker-cluster bootstrap 2,000 resamples, seed 20261011, **98.75%**
  intervals (Bonferroni over 2 comparisons × 2 windows); pooled validation ∪ test at 95% for the middle verdict.
- **Floors (per window):** ≥ 300 flagged evaluable rows, ≥ 20 distinct positive events among them, ≥ 250 pairs in
  each of K-V and K-P.
- **DECISION:** **VALIDATED_INCREMENTAL_SIGNAL** — floors met in both windows and all four lower bounds > 1.0 ·
  **PROMISING_UNVALIDATED** — otherwise, if the pooled K-V and K-P lower bounds (95%) are both > 1.0 ·
  **NO_INCREMENTAL_EDGE_FOUND** — otherwise, with floors met in at least one window ·
  **INSUFFICIENT_OR_UNLINKABLE_DATA** — floors fail in both windows. Even a validated signal is not READY NOW:
  timing utility and false-alarm burden (§6) and the owner's decision come first.
- **Power (stated now):** with ≈3,000 pairs per window and a ≈6% base rate, a per-window 98.75% interval spans
  roughly ±0.3–0.4 on the log scale ⇒ an effect near the discovery estimate (≈1.1×) is **not detectable**; about
  1.4× or more would be.

## 6. Reported, never decisive
Per window: base and flagged rates, flags per session, share of flagged rows without +70%, trigger episodes (first
flag after ≥ 5 sessions without one), their precision and false triggers per session; recall of eligible events
(OK episodes with D1 in the window seen as a clean pivot in [L−10, D1−1]) before the +70% level and before the
start; lead first flag → L, → L10 (first close ≥ 10% above the trough, the alternative start) and → D1; recall and
rate of burden-matched generic flags (top `v1x` regardless of price; lowest `r5`); sensitivity: horizon 20, the
strict label `y10` (mechanical against rising controls), split rows included; flagged rows on the bot's lists and
their READY state (test window only).

## 7. Predictions (kept if wrong)
- **P1** decision NO_INCREMENTAL_EDGE_FOUND.
- **P2** K-V point estimate between 0.9 and 1.3 in both windows.
- **P3** burden-matched generic volume or drop flags recall at least as many eligible events before +70% as H-S70.
- **P4** median lead first flag → D1 at least 5 sessions; first flag → start median at most 5 sessions.
- **P5** more than 90% of flagged rows have no +70% within 10 sessions.

## 8. Limits known now
Survivorship (today's listings); daily bars only; volume adjustment across splits uncertain (split rows excluded,
sensitivity reported); the discovery estimate is small and the test underpowered for it; READY70 already read the
validation/test windows for other rules; the bot's states exist only from 2026-06-20.
