# READYNOW — event timelines, label limit, sample inclusion, and the next question (research only)

Mission «RECONCILE EVENT TIMELINES AND RESUME THE ACTUAL READY NOW DISCOVERY» (2026-10-11). Inputs: `audit/RN_AUDIT.md`,
`RN_REPORT.md`, `faisal_engine/seq70/S70_RESULT.md`. Local data only (`faisal_engine/data/rank/bars.json.gz`, the
READY70 detector and pivot population, the READYNOW / READY70 / SEQ70 / ALERTS70 label files). No production change,
no network, no new data, no sealed file rewritten, no frozen or closed axis reopened, no agent or workflow. The
event definition is unchanged. The RSI/bounce candidate, the app pair and the volume-while-down sequence are not
re-tested.

**Answer in one paragraph.**
- **The label limit is real but anchor-specific.** READYNOW stopped at 2026-08-27 because its onset (trough + 1) is
  only known once the detector fires, up to 19 sessions later. A label anchored on the detection itself is known up to
  2026-09-24, which is where READY70, SEQ70 and ALERTS70 stop.
- **The seeds never entered a READYNOW statistic.** They were excluded by symbol, and three of the five seed events
  fall outside READYNOW's windows anyway.
- **The seeds did enter READY70, SEQ70 and ALERTS70**, as ordinary rows.
- **The two statements in RN_REPORT are consistent.** «The candidate missed the seed events» was a descriptive check;
  «seeds excluded» is the sample rule.
- **The material finding is about the anchor.** READYNOW asked «7–10 sessions before the move starts», not «7–10
  sessions before it qualifies»:
  - The two targets share only 22% of their positive rows.
  - Under the detection anchor, the oversold-type rules weaken in development: the tool's technical part falls from
    1.65 to 1.09 and RSI < 30 from 1.55 to 1.32.
- **Discovery found nothing to carry forward.** Two source-backed structures had never been tested: room to the
  nearest overhead resistance (Faisal's colour key) and unfilled gaps above («فجواته عالية»). Development only, against
  the detection anchor and early-move-matched controls, neither separated. So no out-of-sample experiment is forced.
- **The blocker is data, not method.** The source conditions not yet tested faithfully need point-in-time float,
  available-to-borrow, hourly and after-hours history, or the app's rule definitions. None of these exist locally.
- **The single next experiment is prospective** (§6) and needs one owner decision.

## 1. SEED_TIMELINE_RECONCILIATION (`recon/data/recon.json` · `recon/data/seed_dates.csv.gz`)

**The existing detector (unchanged; `ready70/r70_build.detect_asof` + `episodes_for` = `Super_stock.scan_explosions`).**

| field | definition |
|---|---|
| event fires | a one-day close-to-close gain ≥ 50% within the last 5 sessions (**jump**), else the largest trough-to-later-close rise within the last 20 sessions ≥ 70% (**run**, `_run_explosion`) |
| D1 | the first session the detector fires for the episode. **This is the qualifying event date**, observable that day. A jump qualifies at +50%. |
| L (READYNOW's onset) | the session after the trough close. It is moved earlier when a later detection of the same move reveals an earlier trough, but never before the previous episode's peak. It is known only at detection. |
| L10 | first close ≥ 10% above the trough |
| x70 | first close ≥ 1.70 × the trough close; retrospective, because it needs L |
| IGN | largest one-day close gain in [L, D1] |
| quality | SPLIT_NEAR if any split is dated in [L − 5 days, D1 + 1 day] |

Source records: `ready70/data/episodes.csv.gz` (launch, d1, peak, last_det, kind, gain_d1, peak_gain, sessions_to_d1,
split_near, extreme, quality) and `seq70/data/events.csv.gz` (the same plus l10). x70 = D1 in all five seed events.

**Columns used in the tables below.**
- **Date availability.** Every listed date has a daily OHLCV bar (TradingView, split-adjusted). None has hourly/4H or
  after-hours bars, point-in-time float, point-in-time available-to-borrow, or the app's condition states.
- **«Bot list»** = the bot's own list snapshot of that day (`ready70/data/obs.csv.gz`, from 2026-07-01).
- **«L-label / D1-label»** = READYNOW's label / the detection-anchored label of `rn_recon.label_d1`.
- **Label-known rule.** L-labels are known for t ≤ 2026-08-27; D1-labels for t ≤ 2026-09-24.
- **«R70 · S70 · A70»** = the row is in READY70's / SEQ70's / ALERTS70's evaluable set (their filters, replicated),
  with its f10 label.

### DLXY — qualifying event D1 2026-09-16 (jump +451.8% close-to-close; peak gain 554.1%; `extreme` ≥ 300%, quality OK)
Trough close 08-28 → L 2026-08-31 → L10 09-01 → IGN = x70 = D1 = 2026-09-16 (L→D1 = 11 sessions). Reverse split 1:5 on
09-28 (outside the split-near window).

| anchor | dates | pivot | L-label · D1-label | window | READYNOW | R70 · S70 · A70 | bot list |
|---|---|---|---|---|---|---|---|
| before L (onset) | 08-17 · 08-18 · 08-19 · 08-20 | 4/4 | POS710 · NEG | holdout | excluded (symbol) | NEG · NEG · 08-20 NEG | near-watch |
| before D1 = x70 = IGN | 09-01 · 09-02 · 09-03 · 09-04 | 4/4 | **IN_EVENT** · POS710 | after the L-limit | not labelled | POS · POS · 09-02/03 POS | near-watch |

The «onset» window sits 19–22 sessions before the jump, over a flat base. Its L is a run-trough inside that base. The
actual pre-jump days are IN_EVENT under L and after the L-limit.

### RETO — qualifying event D1 2026-09-15 (jump +676.3%, `extreme`, OK)
L = IGN = x70 = D1 = 2026-09-15 (trough close 09-14). The same four dates serve every anchor: 08-31 · 09-01 · 09-02 ·
09-03.
- pivot 4/4; L-label **CENSORED** (after 08-27) · D1-label POS710 (known).
- READYNOW: not labelled. R70 and S70: POS 4/4. A70: 09-02 POS. Bot list: near-watch.

### SXTC — three qualifying events since May 2026
| event (D1) | detector | dates before L | dates before D1 | notes |
|---|---|---|---|---|
| 2026-06-12, run +78.5% (L 06-08 · L10 06-10 · IGN 06-11 +28.4% · x70 06-12) | OK | 05-22 · 05-26 · 05-27 · 05-28: pivot · POS710 / NEG · **embargo gap** (validation ends 05-15, holdout starts 06-02) · R70 NEG · S70 not in its windows | 05-29 · 06-01 · 06-02 · 06-03: pivot · **NEG under L** (L is 4–5 sessions ahead) / POS710 · 06-02/03 holdout · R70 POS · S70 POS (06-02/03) | the L- and D1-windows label the same days oppositely |
| 2026-08-04, jump +60.1%, peak 134.5% (L 07-30 · IGN = x70 = D1 08-04) | OK | 07-16 · 07-17 · 07-20 · 07-21: pivot · POS710 · holdout · excluded (symbol) · R70/S70 NEG ×3, POS 07-21 | 07-21 · 07-22 (pivot) · 07-23 · 07-24 (**not pivot-days**) · D1 POS710 · R70 POS 07-21/22 | — |
| 2026-10-07, jump +126.4% (L = IGN = x70 = D1) | OK | 09-23 · 09-24 · 09-25 · 09-28 (same for all anchors): **not pivot-days** (outside the pivot population) · L CENSORED · D1 POS710 09-23/24, CENSORED 09-25/28 · A70 POS 09-23/24 · near-watch | — | the three-condition tool named SXTC 09-25 → 10-02 (RN_REPORT §2) |

### DKI — no qualifying daily-close event for the reported move; two earlier qualifying events exist
**Reported move, 2026-10-07 (daily bars).**
- Prior close (10-06) 1.36. On 10-07: open 1.27 · high 3.64 · low 1.27 · close 1.67. The next day (10-08) closed 0.7457.
- Close-to-close +22.8%; high vs prior close +167.6%.
- `detect_asof` returns nothing on 10-06, 10-07 and 10-08. An intraday-only move is not a daily-close event and is
  not treated as one.

**Earlier daily-close events (the previous audit's table started at 2026-05-01 and did not list them).**

| event | dates | anchor windows | status |
|---|---|---|---|
| 2026-02-02 · jump +185.3% | L = D1 | window 01-16 … 01-22: not pivot-days | validation |
| 2026-04-01 → 04-09 · jump +142.7% on 04-09 · peak 228.1% | L 04-01 · IGN = x70 = D1 04-09 | L-window 03-18 … 03-23: pivot, POS710 / NEG · D1-window 03-25 … 03-30: pivot, NEG / POS710 | validation · excluded by symbol from READYNOW · in R70/S70 |

### Earlier episodes of the seed symbols (not the owner-raised events)

| symbol | episodes (L → D1) |
|---|---|
| DLXY | 2025-12-29 → 12-30 · 2026-03-04 · 2026-04-02 → 04-21 |
| RETO | 2026-02-24 → 03-03 · 04-14 → 04-16 |
| SXTC | 2025-04-17 · 2025-04-21 → 04-25 · 2025-05-19 → 06-06 · 2026-03-30 → 04-08 |

All fall in development, validation or before the pivot population.

**What the symbol-level exclusion removed from READYNOW.**
- 18 other episodes: these 11 plus HUBC's seven.
- Eight of them would have been eligible events (a POS710 pivot-day inside a window), alongside the two eligible seed
  events (DLXY-08-31 and SXTC-07-30, holdout).
- 972 evaluable rows: development 457 NEG + 10 POS · validation 288 + 24 · holdout 185 + 8.

### HUBC — kept separate (a current observation, not a seed)
Seven clean episodes (2025-07-03 … 2026-06-15), all excluded by symbol. On 2026-10-07 and 10-08 the rules computed
point in time hold:
- RSI 21.3 / 21.7; low 0.8826; held 5–6 sessions; within 7.1% / 13.3%; bounce 28%.
- RN_A, APP_POS and TC_TECH all hold. HUBC is not a pivot-day.

Its outcome after 10-08 is unknown. No statistic here involves HUBC.

### Which question each timestamp answers
- **L** answers «when did the rise start?». It is retrospective.
- **D1** answers «when did the stock qualify as a +70% move?». It is observable.
- **x70** answers «when did the close first sit 70% above the trough?».
- **IGN** is the largest single day.

For a READY NOW signal 7–10 sessions ahead, early move detection («the rise has already started») and prediction of
the threshold crossing must not be conflated. Under the D1 anchor, 45.5% of development positives are already inside
their run at t (L ≤ t).

## 2. LABEL_LIMIT_AND_SAMPLE_INCLUSION

**Why 2026-08-27.**
- A READYNOW NEG at decision t requires that no clean onset L can still appear in [t+7, t+10].
- L is known only at the first detection. The run detector looks back 20 sessions, so L→D1 ≤ 19 by construction. The
  observed maximum is 19, reached by 325 clean episodes.
- Hence t + 10 + 19 must not pass the last complete session (2026-10-08): t ≤ 2026-08-27.
- The rule censors positives and negatives alike, which prevents a positives-only bias. READYNOW's holdout ends
  there.
- A detection-anchored label needs only t + 10 ≤ 2026-10-08, so t ≤ 2026-09-24. That is the end of READY70's and
  SEQ70's test windows and of ALERTS70's units (all three use f10, measured forward from t).

**Were the seed events in any statistic?** The dates analysed are the 7–10-session windows of the five seed events.

| study | rule | seed dates in the evaluated sample |
|---|---|---|
| READYNOW (RN_A) | `EXCLUDE` by symbol in `window_rows` and `events_index` | **none** (descriptive only: `seeds_matrix.json`) |
| APP_POS | same rows (`rn_lib.window_rows`) | **none** |
| READY70 (f10, test 2026-01-16 → 09-24) | no exclusion | before L: 5 POS + 11 NEG · before D1: 14 POS |
| SEQ70 (f10, split60 = 0, test 06-02 → 09-24) | no exclusion | before L: 5 POS + 7 NEG · before D1: 12 POS (≈ 0.07% of test rows) |
| ALERTS70 (f10, units 08-17 → 09-24) | no exclusion | before L: 3 POS + 1 NEG · before D1: 5 POS |

- Even without the exclusion, three of READYNOW's five seed windows (RETO, SXTC-10/07 after the limit; SXTC-06/08 in
  the embargo gap) could not have entered.
- The two that could (DLXY, SXTC-07/30 before L) are «move start» windows, not pre-expansion windows.
- The effect of the seed rows on READY70 and SEQ70's sealed ratios was not recomputed; that would re-run sealed
  evaluations. Their weight is a handful of rows among tens of thousands.

**Reconciling the two statements in RN_REPORT.**
- «The candidate missed all five seed events» is a descriptive reading of `seeds.csv.gz` (every session, pivot or
  not).
- «Seeds and HUBC are excluded» is the sample rule.
- They do not conflict: the seeds were never used as evidence for or against RN_A.

**The sample, all 3,727 clean episodes (same window rule as `rn_lib.events_index`).**

| window | L-anchored: events · with a pivot-day · eligible | D1-anchored: events · with a pivot-day · eligible | eligible under both | D1-window pivot-days IN_EVENT under L |
|---|---|---|---|---|
| development | 1,581 · 561 · **513** | 1,579 · 558 · **546** | 442 | 1,063 of 2,080 (51%); 249 events entirely |
| validation | 854 · 363 · **333** | 786 · 319 · **311** | 280 | 514 of 1,180 (44%); 125 events |
| holdout | 424 · 224 · **208** | 476 · 247 · **237** | 189 | 436 of 918 (47%); 102 events |

The L-anchored counts reproduce RN_REPORT §4 exactly (513 · 333 · 208; guard RC3).

**Label defects found, with their size.**
1. **Anchor (material for the owner's question).**
   - Row agreement: of 1,952 development rows positive under L, only 425 (22%) are positive under D1.
   - 1,013 D1-positive rows were IN_EVENT under L, i.e. never asked.
   - L→D1 ≥ 7 in 62.8% of clean episodes.
   - READYNOW answered «7–10 sessions before the move starts». It did not answer «7–10 before it qualifies».
2. **L at the run window's edge.**
   - 325 clean episodes (8.7%) have L exactly 19 sessions before D1: the «trough» is the first close of the 20-session
     window.
   - In 236 of them (6.3% of all) a lower close exists in the 20 sessions before, so L marks the window edge, not the
     trough.
3. **D1 later than the +70% close.**
   - In 171 of 3,487 episodes reaching +70% (4.9%), the detector first merged the move into an earlier episode.
   - Example: HUBC, x70 06-16, D1 06-30.
   - Handled in `label_d1`: the event period starts at min(x70, D1) (guard RC1; mutation RM7).
   - 138 jumps qualify at +50% before +70%. 240 clean episodes never reach +70% over the trough.
4. **Symbol exclusion removes more than the seeds.**
   - 18 other episodes of the five symbols, eight of them eligible, and 972 evaluable rows.
   - Small, but it removes exactly the names most like the owner's targets.

**Resolution (no event definition changed).**
- The detection-anchored label is written (`rn_recon.label_d1`), guarded and quantified.
- Development diagnostic (`recon/data/anchor_dev.json`, descriptive, no other window read): raw lift under L → under
  D1.
  - RSI < 30: 1.55 → 1.32
  - RSI < 33: 1.41 → 1.20
  - tool technical part: 1.65 → 1.09
  - RN_A: 1.65 → 1.42
  - APP_POS: 1.07 → 0.93
  - within 15%: 1.02 → 0.86
  - bounce 10–40%: 1.07 → 0.96
- **Reading.** Oversold states sit just before troughs, so a trough-anchored target rewards them partly by
  construction. Against the qualification date the advantage mostly disappears. These are raw lifts in development
  only, not a test; RSI/bounce are not re-tested.

## 3. SOURCE_CONDITION_COVERAGE

Starting point: `audit/RN_AUDIT.md` §1. Added here: the anchor, and the two structures examined in development.
- **Parity** = the condition reproduces the app's own displayed state.
- **Proxy** = a stand-in whose equivalence is unproven or disproved.

| condition (source) | definition | data / PIT | implementation | lead-time evaluation | smallest remaining gap |
|---|---|---|---|---|---|
| app «within 15% of support» | support = lowest daily low; window unknown | daily ✓ | **parity 9/9** | L: dev + OOS (APP_POS) · D1: dev raw 0.86 | the base-low window (25 vs the app's) — minor; no further test (no repeat) |
| app «bounce 10–40%» | confirmed | daily ✓ | **parity 8/8** | L: dev + OOS · D1: dev raw 0.96 | none material |
| app «below EMA20/30/50» | EMA values known; **comparator unknown** | daily ✓ | proxy BELOW3, parity 6/9 | L dev only | the rule (all three? close vs which?) — from the app's author |
| app «daily stability ≥ 2 sessions» | **unknown** | daily ✓ | proxy HOLD2 contradicts (2/7) | — | the rule |
| app «successful daily retest» | **unknown** | daily ✓ | none (CYCLE3 3/9) | — | the rule |
| app «daily + 4H momentum» | **unknown** | **no 4H history** | none (MACD field 6/7) | — | rule + 4H bars |
| app's two unnamed conditions · score labels · split-list criteria | **no source** | — | none | — | the definitions |
| app short condition · app float ≤ 5 M | criterion unknown · list filter | **no PIT borrow / float** | none | — | point-in-time series |
| tool RSI < 33 | exact | ✓ | exact | L dev + OOS (inside TC_TECH) · D1 dev 1.20 | none (no repeat) |
| tool float < 4 M · available < 20 k | exact | **no PIT float / borrow** | none | never | **point-in-time series (prospective only)** |
| tool 5 sessions above the exact (hourly) low · no +50% in 5 (incl. after-hours) | exact | **no hourly / after-hours** | daily approximations HOLD5 · NO_BOOM | inside TC_TECH | hourly and after-hours bars |
| Faisal «rsi اقل من 30» | exact | ✓ | exact | L dev + OOS · D1 dev 1.32 | none (no repeat) |
| Faisal «hold the bottom 3 sessions» · «oversold at the bottom» · «bearish averages» · cycle (TG_50584) · EMA 9/26 | readings | ✓ | HOLD3 · OS_AT_LOW · BELOW3 · CYCLE3 · EMA_UP / EMA_X5 | L dev | anchor D1 untested — but none had development value under L |
| **Faisal «فجواته عالية»** (IMG_6814) | **wording, no formula** | ✓ | **new:** the bot's `unfilled_gaps_above` (M9's detector, 120 sessions), three readings fixed before any number: any gap · nearest gap ≥ 70% above · largest gap ≥ 30% | **D1 dev only** | development: no separation (§3a). The exact rule is unknown (not inferred) |
| Faisal «ربحه عالي» (IMG_6814) | no formula | — | none | — | the definition |
| Faisal colour key «🔵 a target with no resistance» (IMG_6748) | concept | ✓ | **new:** room to the nearest real level of the bot's resistance map (`_swing_highs` 3/6, `_red_candle_heads`, weekly swing highs, clustered at 3%) | **D1 dev only** | development: no separation (§3a) |

### 3a. Development-only discovery: the two structures never tested (2025-05-01 → 12-31)
**Setup.**
- Target: a clean episode first detected 7–10 sessions later (D1-label). Base 3.02% of 67,788 evaluable pivot-days.
- Matched controls: same session and price bucket; within-session percentiles of distance above the 25-session low,
  range20 and v1x, each within 0.10. This holds the early-move state constant.
- Uncertainty: ticker-cluster bootstrap, 2,000 resamples, 95%.

**Room to the nearest overhead resistance (`recon/data/room_dev.json`).**
- The map is dense: median room 7.0%, q90 20.7%, never «open».
- Rate by room: < 10%: 3.07% · 10–30%: 2.99% · 30–70%: 2.23% · ≥ 70%: 7.2% (194 rows, 14 positives).
- Matched: ≥ 70% 4.0 [0.5, 13.0] on 116 pairs (uninformative) · ≥ 30% 1.00 [0.64, 1.50] · < 10% 0.94 [0.78, 1.13].

**Unfilled gaps above (`recon/data/gap_dev.json`).**
- Gaps above exist on 20% of pivot-days; nearest-gap median 90.7% above.
- Any gap: raw 0.99 · matched 0.90 [0.68, 1.17].
- Nearest ≥ 70%: 1.08 · 1.10 [0.77, 1.54].
- Largest ≥ 30%: 1.28 · 1.25 [0.74, 1.96].

**Verdict: neither structure separates in development, so neither is carried to a sealed test.** No validation or
holdout row was read (guard RC5).

**Already tested (from the request's list).**
- **Support side:** distance and bounce (READYNOW / APP_POS), tested-level distance and location (READY70).
- **Candlestick sequences:**
  - `T-CANDLE` (reversal candles; failed, closed for selection)
  - `clv5` (SEQ70: at chance before L−2)
  - `close_pos0` and `inside_k` (`T-PRELINK`)
- **Moving averages:** BELOW3 and EMA 9/26 (READYNOW), `sma_pos` (`T-LINK100`), `T-MA-LADDER` (failed).
- **Base and changing range:**
  - range20 (READY70 cells; `T-PRELINK`)
  - `range_c` compression (`T-LINK100`)
  - `T-PRESS` family (`T-PRESS-Q` failed)
  - `tr5x` (SEQ70)
- **Retests and failed downside moves:**
  - cycle stage and branch (READY70)
  - CYCLE3 (READYNOW)
  - `sweeps20` (`T-PRELINK`)
  - `newlow60_5` (`T-LINK100-2`, failed)
  - `T-SWEEP-RECLAIM` (failed)
- **Order and interactions:** READYNOW sequences («oversold then hold» 0.96) and SEQ70.

## 4. REMAINING_MATERIAL_GAPS

| # | gap | class | resolvable locally? |
|---|---|---|---|
| 1 | point-in-time float (tool < 4 M; app ≤ 5 M) and available-to-borrow (tool < 20 k; app short condition) | DATA_GAP | **no** — only prospective capture |
| 2 | hourly / 4H / after-hours history (tool's exact low and after-hours boom; app momentum) | DATA_GAP | no |
| 3 | the app's stability, retest, momentum, below-EMA comparator, two unnamed conditions, score labels, split list | DEFINITION_GAP | no — the app's author is the only source |
| 4 | every sealed out-of-sample verdict (RN_A, APP_POS) is on the L anchor; the D1 anchor exists only as development diagnostics here | EVALUATION_GAP | technically yes, but a D1 re-test of RSI/bounce is a repeat the mission forbids |
| 5 | **no untouched historical holdout remains** (validation and holdout read by READYNOW and APP_POS; 2026-06-02 → 09-24 by READY70 and SEQ70) | DESIGN | no — any new historical OOS test carries cross-study multiplicity; only forward data is clean |
| 6 | the pivot population holds 35–52% of the events at their D1-window (558 of 1,579 · 319 of 786 · 247 of 476) | SCOPE | partly (conclusions are about pivot-days) |
| 7 | L-anchor artefacts (window edge in 6.3% of episodes) · D1 lag (4.9%) | DEFINITION (documented) | handled in labels; event unchanged |
| 8 | «ربحه عالي» and the exact meaning of «فجواته عالية» | DEFINITION_GAP | no |

## 5. NEXT_UNANSWERED_RESEARCH_QUESTION
**Do the tool's two non-price conditions add information about qualification 7–10 sessions later, beyond its
technical part?**
- The conditions are float below 4 million and available-to-borrow below 20 thousand.
- «Qualification» = the detector's first firing, D1.
- The comparison holds the early-move state constant.

Why this question:
- These are the conditions the owner and Faisal actually select on.
- They are exact (`three_cond_daily.py`), and they have never been testable because no point-in-time history exists.
- Every daily-price alternative has either been tested (§3) or shows nothing in development (§3a).

## 6. RECOMMENDED_SINGLE_NEXT_EXPERIMENT
**Blocker under today's restrictions.**
- No sound new experiment can run on local data.
- The untested source conditions need point-in-time float, borrow, hourly and after-hours data, or the app's
  definitions.
- The untested daily structures that have a source showed no development signal.
- All historical windows have been read. Forcing a sealed historical test would only add multiplicity.

**The one experiment (prospective, to be sealed before the first captured day): `T-TC-FWD`.**
- **Units:** every (symbol, session) on which the three-condition tool's technical part passes in its live daily run
  (`three_cond_daily.py`: RSI14 < 33 ∧ 5 sessions above the exact low ∧ no +50% in 5 sessions). Its whole universe,
  not only pivot-days.
- **Capture (append-only, before any outcome exists):** the tool's own values that day — float (TradingView scanner),
  available-to-borrow (harvest, then ChartExchange), RSI, the exact low and the stability count. UNKNOWN stays UNKNOWN,
  never zero.
- **Outcome:** `label_d1` on TradingView daily bars — a clean episode of the unchanged detector first detected 7–10
  sessions later; f10 as secondary. Read only after t + 10 sessions.
- **Contrast:** full tool (technical ∧ float < 4 M ∧ available < 20 k) vs technical-only rows that fail float or
  borrow.
  - Matching: same session, price bucket, and distance-above-low / range20 / v1x percentiles within 0.10.
  - Uncertainty: ticker-cluster bootstrap, 2,000 resamples, 95%.
  - The same contrast is also run for float alone and borrow alone, reported and not decisive.
- **Floor and horizon:**
  - Floor: ≥ 30 distinct D1 events among technical passes and ≥ 300 full-tool rows.
  - Planning rate from development: about 14 technical passes per session inside the pivot population, about 4–5
    distinct events a month. The tool's universe is wider.
  - Fixed end: 2027-03-31. Floor not met by then ⇒ INSUFFICIENT.
- **Decision rule:** VALIDATED only if the matched lower bound > 1.0 and the full tool beats an equal-burden
  volatility ranking. Otherwise not validated.
- **What it needs:** one owner decision — a daily append-only capture added to the tool's run, or a separate
  read-only job. This is a state write the restrictions of this mission do not allow me to create.

**Not recommended:**
- re-testing RSI/bounce on the D1 anchor (a repeat)
- inferring the app's rules from screenshots
- reopening any frozen or closed axis

**Classification of everything examined.**
- **Tested and rejected, or not a READY signal:**
  - RN_A (NO_INCREMENTAL_EDGE_FOUND)
  - APP_POS (PROMISING_UNVALIDATED, not READY)
  - SEQ70 volume-while-down (PROMISING_UNVALIDATED, short lead)
  - READY70's 44 combinations
  - the archive families of §3a
- **Source-backed, not yet tested faithfully:**
  - the app's stability, retest, momentum, below-EMA rule, two unnamed conditions and short condition
  - the tool's float, borrow, exact hourly low and after-hours boom
  - Faisal's «ربحه عالي»
  - «فجواته عالية» was tested only in development, through one bot-based reading.
- **Technical hypotheses examined now, development only:** room to resistance, unfilled gaps above — no separation,
  not carried.
  - Other daily structures remain untested, e.g. specific MA arrangements beyond BELOW3 / EMA 9/26, or multi-day
    candle sequences.
  - None has a source or development evidence that would justify a sealed test.
- **Genuine data limitations:**
  - point-in-time float and borrow
  - hourly, 4H and after-hours bars
  - the app's states
  - no untouched historical holdout

## Files
- `recon/rn_recon.py` (`--check`) → `recon/data/recon.json`, `recon/data/seed_dates.csv.gz`
- `recon/rn_anchor_dev.py` → `anchor_dev.json`
- `recon/rn_room_dev.py` → `room_dev.json`
- `recon/rn_gap_dev.py` → `gap_dev.json`
- `recon/test_recon.py` (RC1–RC7; `R70_FAST=1` skips the 10-minute ROOM rerun)
- `recon/recon_mutate.py` → `recon/data/mutations.json`
- Reused read-only: `rn_build`, `rn_lib`, READY70 (`r70_build`), the bot's `_swing_highs`, `_red_candle_heads`,
  `resample_ohlc` and `unfilled_gaps_above`.
- All git reads with `GIT_ALLOW_PROTOCOL=file`.
