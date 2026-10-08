# PHASE4_FINAL_REPORT — «FIRST TOUCH → ATTENTION → RETEST → TRIGGER vs TWO-TOUCH AS AN EARLY CANDIDATE GATE» (2026-10-08) · research only

Pre-registration `PHASE4_PREREG.md` merged to `main` (`63da8d807e38ef66c66cecbbb78304ac3a92cfa9`, PR #580) **before any number**. Discovery results were committed (`4de1e0619`) **before** the validation set was run; no definition, tolerance, state mapping or ordering rule changed afterwards (no `PHASE4_AMENDMENT.md` was needed). Two implementation bugs were fixed before any set was frozen and are disclosed in §H. Boundary §0 honoured: no production, V4, prospective-validation, Telegram, three-condition, threshold, ranking or methodology change; no V5 / READY_NOW_V2 / production temporal engine / state machine / replacement gate; no agents.

## A. Denominators
| Object | Size | File |
|---|---|---|
| Faisal tickers with bars and a dated FOCUS/WATCH/READY/ENTRY unit | **41** = discovery **22** · validation **16** · anchors **3** (DKI, SXTC, HUBC; never in rule counts) | `POSITIVE_VALIDATION_CASES.csv` |
| Faisal dated rows (units) with bars | **83** = discovery 46 (WATCH 40 · READY 4 · ENTRY 2) · validation 29 (WATCH 23 · FOCUS 5 · READY 1) · anchors 8 | `out/arch_rows_*.csv` |
| Event ledger rows | **415** (5 events × 83 units; forward events in `FWD_*` columns with `FUTURE_REVEAL_DATE`) | `EVENT_LEDGER.csv` |
| Matched negative controls (procedure §⑦, seed 20261008) | **164** control-days = 88 / 64 / 12 per set · 128 full 4-bucket matches · 75 distinct symbols · all identity-eligible on the matched date · zero Faisal units | `NEGATIVE_VALIDATION_CASES.csv` |
| Feature-test universe | **14,294** identity-eligible symbol-days (95 symbols × sessions from 2025-06-20; 5,162 on Faisal tickers) | `FEATURE_TESTS.csv` |
| Lookahead check | 41/41 ordering rows `LOOKAHEAD_SAFE=1` (last bar used < decision date); 16/38 non-anchor first dates are weekend/holiday-mapped (`DATE_AMBIGUOUS`) | `PHASE_ORDERING_MATRIX.csv` |

Production constants read by name at run time: `tested_level(30, 0.015, 2)` · `pivot_cycle_state` (`METHOD_BOUNCE_MIN_PCT` 10 · `METHOD_HOLD_TOL` 0.015 · `PIVOT_SWEEP_PCT` 13 · `STABILITY_MIN` 3 · `PIVOT_CYCLE_WIN` 60) · `ANCHOR_MODE=tested_strict`. None tuned. Identity-eligibility (every gate except the anchor) read from the Phase 3 bot states by a shortcut verified exactly on 1,533/1,533 LOGO rows (eligible ⇔ PASS or first wall = ANCHOR); 3,774 + 673 new production replays for control symbols (`out/extra_states.csv`).

## B. Event definitions as implemented (§5) — not vague "touches"
- **LEVEL(T)** = min Low of the last 30 bars before T. **E1 FIRST TOUCH** = the bar that set it. A lower Low resets both.
- **E2 SECOND TOUCH (production)** = `tested_level` returns ≥2 non-adjacent clusters of Lows within 1.5% of LEVEL, on the same level. Invalidated by any Low < LEVEL×0.985 (new minimum) or by the first-touch bar leaving the 30-bar window.
- **E3 RETEST (Faisal lifecycle, production display function)** = `pivot_cycle_state` stage ≥3: bounce ≥10% from the bottom, then a Low back inside 1.5% above it (`hold`) or below it down to 13% (`sweep`). If its 60-bar bottom differs from LEVEL (an older lower low), E3 is taken on that bottom and `LEVEL_MISMATCH=1` (19/41 cases).
- **E4 TRIGGER (bot-computable proxy of `TG_57872`'s two branches)** = first close back above the tested bottom after a sweep, or stage 4 (held ≥3 sessions).
- **E5 BREAK** = Low < LEVEL×0.87 or 60 sessions without E3.
- Faisal states from dated units only (classes DIRECT_TEXT / DIRECT_CHART / ACTION; the 2026-09-13 app list is an X post and therefore DIRECT_TEXT, 1 APP_SCREENSHOT unit = WATCHLIST); REPEATED_ATTENTION flagged for 9 tickers.

## C. Results
### C1 Ordering (`PHASE_ORDERING_MATRIX.csv`, 38 non-anchor + 3 anchors)
- Pre-registered ORDER_RESULT (FT ≤ STATE < E2/E3; TRIGGER ≤ ENTRY): **EXPECTED 15 · CONTRADICTED 12 · INSUFFICIENT 11** (discovery 10/7/5 · validation 5/5/6). Anchors: DKI EXPECTED, HUBC EXPECTED, SXTC INSUFFICIENT.
- **FT ≤ STATE holds 38/38 — but by construction**: the level in force at the first dated state necessarily formed before it. The informative quantity is the age of that low: median **5 sessions** (IQR 2–11, range 1–30; discovery 5, validation 4); 7/38 first states fall on the session right after the low (+2 anchors). This is **not** evidence that First Touch precedes attention in general (see F·1).
- **E2 (production second touch) on the level Faisal was looking at: NEVER within its window on 32/38 (84%)** — level invalidated by a lower Low 20, first-touch bar left the 30-bar window 12. It occurred on 6: before the first state 2 (CDIO, LIMN), same day 1 (CETX), after 3 (EHGO, MNDR, TRUG). Anchors 3/3 NEVER. **P2 holds (35/38 not occurred by the first state) · P3 holds (84% ≥ 30%).**
- **E3 (Faisal-style retest)** occurred on 27/38 levels within 60 sessions: **sweep 21 · hold 6**; relative to the first state: AFTER 15 · SAME 3 · BEFORE 9 · NEVER 11. Per first-state class: WATCH/FOCUS (34): declared **before** the retest 13, at it 2, after it 8, no retest 9 → among those with a retest, before 13/23 (57%), after 8/23 (35%). READY/ENTRY (6): after/at the retest 2 (PIII, SPRC), before 2 (UPC, GCTK), no retest 2 (AMIX, CRE).
- **O4 sweep-vs-anchor exclusivity**: 21 of the 27 retests were sweeps below the low; every one of them invalidates the production second touch on that level by construction (a new 30-bar minimum). This is the mechanism behind the 84% NEVER.
- **E4 trigger**: 20/38 (sweep-and-reclaim 18, stability 2); vs ENTRY: evaluable 0 (the two dated ENTRY tickers reached no E3 within 60 sessions on their level).

### C2 First-touch / second-touch role (`FIRST_TOUCH_ANALYSIS.csv`, `SECOND_TOUCH_ANALYSIS.csv`, `TEMPORAL_ROLE_ANALYSIS.csv`)
- E2 vs WATCH: before 2 · same 0 · after 3 · never 24 (n with WATCH 29). E3 vs WATCH: before 6 · same 1 · after 14 · never 8 (median E3 − WATCH = +4 sessions, IQR −3…+13). E3 vs READY: before 1 · same 1 · after 2 · never 0 (n = 4). E3 vs ENTRY: never 2/2. **No event reaches the 70% "precedes/follows" bar for any state** → role reading «mixed/insufficient» throughout; **P6 holds** (second touch vs READY/ENTRY is mixed).
- **§18-19 feature tests** (14,294 eligible symbol-days; diagnostic only): P(documented Faisal state within 20 sessions | fresh first touch ≤5 sessions) = 181/5,911 = 3.06% vs 230/8,383 = 2.74% (ratio **1.12**); WATCH 1.18; READY 0.60. P(READY within 20 | E2 present) = 7/2,872 = 0.24% vs 40/11,422 = 0.35% (0.70). P(any state | E3 present) = 10/694 = 1.4% vs 401/13,600 = 2.9% (**0.49**); READY 0/694. **A fresh first touch carries no information about later Faisal attention; a completed retest is negatively associated with it** (his dated attention precedes the retest).

### C3 Architectures (`ARCHITECTURE_COMPARISON.csv`, `STATE_ALIGNMENT_MATRIX.csv`, `MOVE_VS_REMOVE_RESULTS.csv`)
| Set (rows / tickers / control-days) | Arch | object at any stage | matched stage | first-divergence tickers | alert-stage FP | observation-stage FP |
|---|---|---|---|---|---|---|
| discovery (46 / 22 / 88) | A current | 2 | 2 | 22/22 | 0.170 | 0.170 |
| | REMOVE | 13 | 13 | 16/22 | 1.000 | 1.000 |
| | **B** first touch → observation · second touch → alert | **16** | 12 | **14/22** | **0.102** | 1.000 |
| | C (+E3 counts as ready) | 16 | 14 | 14/22 | 0.398 | 1.000 |
| | D (E4 = trigger) | 16 | 14 | 14/22 | 0.341 | 1.000 |
| validation (29 / 16 / 64) — blind | A | 3 | 3 | 14/16 | 0.234 | 0.234 |
| | REMOVE | 21 | 21 | 4/16 | 1.000 | 1.000 |
| | **B** | **24** | 23 | **3/16** | **0.109** | 1.000 |
| | C | 24 | 23 | 3/16 | 0.406 | 1.000 |
| | D | 24 | 23 | 3/16 | 0.328 | 1.000 |
| anchors (8 / 3 / 12) | A · REMOVE · B · C · D | 0 · 2 · 2 · 2 · 2 | 0 · 2 · 2 · 2 · 2 | 3 · 2 · 2 · 2 · 2 | 0.083 · 1.0 · 0.083 · 0.5 · 0.417 | — |

- Observation-stage FP = 1.0 for REMOVE/B/C/D **by construction** (controls were selected identity-eligible on the matched date); the discriminating column is the alert stage.
- **MOVE vs REMOVE (pre-registered rule: recall ≥ 80% of REMOVE's AND alert noise ≤ 1.5× A):** **B passes in discovery, validation and anchors** (recall 16 vs 13, 24 vs 21, 2 vs 2; alert FP 0.10 vs A 0.17, 0.11 vs 0.23, 0.08 vs 0.08). C fails everywhere (noise ×2.3–6). D fails in discovery (0.341 > 0.255) and passes in validation (0.328 ≤ 0.351) — not robust. **P4 holds for B only.**
- State alignment: B at WATCH = 12/40 (30%, Wilson 18–45%) in discovery and **19/23 (83%, 63–93%)** in validation; at READY **0/4 and 0/1** (B's "watch/ready" needs the production second touch, which never fires on his levels); D at READY 2/4 (discovery). The sets differ because the dominant wall differs: older cases fail M3/M4/M2 identity gates (no object in any architecture), recent cases fail the anchor only.
- **Negative controls reproduce the sequence**: forward E3 on the first-state level: positives 17/22 vs controls 72/88 (ratio **0.94**) in discovery, 10/16 vs 40/64 (**1.00**) in validation; E4: 14/22 vs 63/88 (0.89), 6/16 vs 31/64 (0.77); E2: 4/22 vs 17/88, 2/16 vs 16/64. **Matched names on untested lows go through first touch → sweep → reclaim at the same rate whether or not Faisal ever wrote about them.**

### C4 Transitions (§21, `TRANSITION_ANALYSIS.csv`) and data availability (§24-25)
FOCUS→WATCH directly dated 0/30 · WATCH→READY 0/5 · READY→ENTRY 1/3 (SXTC) · WATCH→ENTRY 0/3 → the dated corpus cannot confirm any transition as a sequence; Faisal's text describes them (Phase 3) but his dated units mostly capture one state per ticker. `DATA_AVAILABILITY_AUDIT.csv`: E1/E2/E5 are computable from bot data (MODEL MISSING — no object is created); E3 is computed for display only (STATE MODEL MISSING); E4 is DATA MISSING intraday (operator tape ended 2026-09-29) and STATE MODEL MISSING; Faisal's validity inputs at READY (short <20k, offering closed, operator) are DATA MISSING before candidacy. `PHASE4_GATE_STAGE_MATRIX.csv`: of the gates before the anchor, M4 range and RSI are LATER-stage concepts in Faisal's text; M2 ceiling, M5, SOFT, SCORE, DEPTH have no Faisal stage at all.

## D. Hypotheses (falsifiers as pre-registered)
| H | Falsifier | Fired? | Verdict |
|---|---|---|---|
| H0 current order correct | E2 **after** first state in ≥60% of evaluable cases in both sets and A absent in ≥60% | By the letter: evaluable E2 cases are only 6 (after 3 = 50%) → **does not fire**. By count: E2 had **not** occurred by the first state on 35/38 (92%) and never fires at all on 32/38 → the admission test is not where Faisal's level gets tested | **NOT FALSIFIED BY ITS OWN RULE; untenable as a description** (the rule it defends almost never fires on his levels) |
| H1 two-touch one of several; moving later unnecessary | MOVE represents ≥2× A's rows with observation FP ≤ REMOVE's | B: 16 vs 2 and 24 vs 3 (8×); obs FP = REMOVE's | **FALSIFIED** |
| H2 first touch has no Faisal-state significance | P(state within 20 \| fresh first touch) ≥2× AND first touch precedes state ≥60% | ratio 1.12 (<2) | **NOT FALSIFIED — first touch itself is uninformative** |
| H3 first touch creates opportunity but second touch not decisive | E2/E3 precede READY/ENTRY ≥60% AND absent before FOCUS/WATCH ≥60% | E3 vs READY before 1/4; vs ENTRY never 2/2 | **NOT FALSIFIED — the second touch is not the decisive transition in the dated record** |
| H4 first touch → state → later retest is the correct architecture | any of six | ① FT after state: 0% (no) · ② E2 before state ≥50%: 2/38 (no) · ③ MOVE < REMOVE by >20%: no (B higher) · ④ validation share < half discovery: no (higher) · ⑤ **controls same sequence rate (ratio < 1.5): YES — 0.94 / 1.00** · ⑥ depends on anchors: no (anchors excluded) | **WEAKENED** — ordering survives on Faisal's side and in the architecture replay, but the sequence is generic structure, not a Faisal signature |
| H5 evidence artifact | class changes ≥30% when ambiguous dates dropped / non-direct excluded / lookahead violation | ambiguous dates 16/38 (42%); restricting to the 22 unambiguous rows: EXPECTED 10 · CONTRADICTED 7 · INSUFFICIENT 5 (45/32/23% vs 39/32/29%), E3-before 27% vs 24% — no class flip; all 38 rows are DIRECT_TEXT/CHART/ACTION; lookahead 0 violations | **NOT EXCLUDED but no flip found**; the 9 "retest before attention" cases (large FT→state gaps, e.g. CUPR 30 sessions, CANF 14) are exactly where a late dated post is expected |
| H6 architecture real but another feature needed before/after the retest | H4 survives AND READY/ENTRY alignment <50% while observation alignment ≥70% | B observation at WATCH 83% (validation), at READY 0/5; controls identical on the sequence | **SUPPORTED** — what discriminates Faisal's names is not the first touch, the retest, or the reclaim; it is not in these bars |

Predictions: **P1 holds but is uninformative (by construction) · P2 holds (92%) · P3 holds (84%) · P4 holds for B only · P5 holds (validation E2-not-by-state 15/16 vs 19/22) · P6 holds.**

## E. The twenty required questions (§29)
1. **Is Two-Touch actually a later event in Faisal's process?** In his text, yes (the retest is what he waits for after Watch). In the dated record, the production two-touch (E2) **never happens on 84% of his levels**; his retest is a sweep (21/27), which the production rule cannot represent. So "later" is true only for the lifecycle retest (E3), and even E3 precedes his dated Watch in 6/21 evaluable cases.
2. **Does First Touch precede documented attention?** 38/38 — but by construction (the level in force at the dated state formed earlier). The dated low is typically 5 sessions old (IQR 2–11). Not a test of causation.
3. **Precede Focus?** 5/5 dated FOCUS (by construction); the 09-13 list is a snapshot, Focus age 2–30 sessions.
4. **Precede Watch?** 29/29 (by construction); median 5 sessions.
5. **Does Second Touch follow Focus?** E3 after FOCUS 1, before 2, same 1 (n = 4). Unresolved.
6. **Follow Watch?** E3 after WATCH 14/21 evaluable (67%), before 6, same 1; E2 after 3/5. Majority but not ≥70%.
7. **Precede Ready?** E3 before READY 1/4, same 1, after 2. No.
8. **Precede Trigger?** Trigger is defined from the retest here (E4 ≥ E3 by construction); Faisal's own dated trigger text is absent on all 41.
9. **Precede Entry?** E3 never within 60 sessions on both dated ENTRY levels; E2 never. No.
10. **Which relationship is supported?** Only «Watch is declared on an untested low, usually before the lifecycle retest» (13 before vs 8 after among 23 WATCH/FOCUS with a retest) and «the production two-touch does not fire on his levels» (32/38).
11. **Is First Touch an event or a state?** An event with no information content (ratio 1.12); it does not mark a state.
12. **Is Second Touch an event or a state?** An event; as a production rule it is mostly impossible on his levels; as a lifecycle retest it is generic (controls 0.94–1.0).
13. **Does MOVE-LATER outperform REMOVE?** B: yes on the pre-registered rule in all three sets (same or higher recall, alert noise ≤ A). C: no. D: not robust.
14. **Does moving Two-Touch reduce the first divergence?** B: 22→14 tickers (discovery), 16→3 (validation), vs REMOVE 16 and 4.
15. **Reduce false positives relative to removal?** At the alert stage yes (0.10 vs 1.00; 0.11 vs 1.00); at the observation stage no (equal by construction).
16. **Survive independent validation?** Yes for B (stronger in validation: 24/29 rows, 83% WATCH alignment).
17. **Survive negative controls?** **No**: controls show the same first touch → retest → reclaim rates (ratios 0.77–1.14).
18. **Survive anchor removal?** Yes: all rule counts exclude DKI/SXTC/HUBC; anchors behave like the validation set.
19. **Missing data or wrong architecture?** Both, separately: the stage order is wrong for *holding* a name (STATE MODEL MISSING), and the discriminating information is absent from daily bars (DATA MISSING: operator/intraday, borrow history, offering status, Faisal's own selection criteria).
20. **Exact first causally supported failure?** See `PHASE4_FINAL_VERDICT.md` §30 form.

## F. Twenty adversarial passes (§31)
1. *Assumed First Touch = Focus?* No — tested separately; first touch carries no information (C2). 2. *Second Touch = Trigger?* No — E2, E3, E4 kept apart; E4 is a labelled proxy. 3. *Second Touch = Entry?* No — E2/E3 never precede the two dated entries. 4. *Future outcomes to assign states?* No — states from dated text ≤ date; no outcome label is used anywhere in this phase. 5. *Future outcomes to define event dates?* Forward events are written only to `FWD_*`/forward columns with reveal dates; decision-time columns use bars < T (41/41 checked). 6-8. *DKI/SXTC/HUBC to define the ordering?* No — definitions come from production code and the prereg; anchors are excluded from every count and reported apart. 9. *Validation frozen before analysis?* Yes — set listed in the prereg; discovery results committed (`4de1e0619`) before running validation. 10-11. *Matched/negative controls?* 164 control-days by the frozen procedure; 128 full bucket matches. 12. *REMOVE vs MOVE-LATER?* Tested with the pre-registered rule; B passes, C fails, D not robust. 13. *Data availability separately?* `DATA_AVAILABILITY_AUDIT.csv`. 14. *Event-level vs state-level?* Yes — event-level survives (B holds objects), state-level fails for READY (0/5) and for the discrimination claim. 15. *Timestamps verified?* Weekend mapping flagged (16/38) and sensitivity run (no flip); bot snapshot rule unchanged from Phase 3. 16. *Mentioned vs selected?* 128 MENTION units excluded. 17. *Selected vs entered?* ENTRY only from action words (4 units, 2 with bars). 18. *Optimised a threshold?* No — every constant read by name; the only code changes after freeze were two bug fixes made before any set was frozen (§H). 19. *Modified production?* No (`git diff` on `Super_stock.py` empty; research CONFIG restored in `finally`). 20. *Could the phase-order hypothesis still be evidence incompleteness?* Yes for its Faisal-side timing (42% ambiguous dates, one dated state per ticker, late posts) — but the strongest result does not depend on it: the production rule's impossibility on swept levels (84%) and the controls' identical sequence rates are bar-side facts.

## G. Integrity check (§32)
- [x] prereg committed and merged before outcome numbers (#580) · [x] validation set frozen (prereg §⑦; discovery committed first) · [x] lookahead firewall verified (41/41; forward columns separated) · [x] no V4 changes · [x] no production changes · [x] no Telegram changes · [x] no V2/V5 · [x] no threshold tuning · [x] no anchor hard-coding (anchors reported apart) · [x] First Touch defined independently (E1) · [x] Second Touch defined independently (E2 production; E3 lifecycle) · [x] Faisal state evidence separated from outcomes · [x] event-level vs state-level separated · [x] MOVE vs REMOVE tested · [x] independent validation completed (blind) · [x] negative controls completed · [x] data availability audited · [x] state transitions separately evaluated · [x] Level 5 criteria explicitly checked (§⑪: A partial · B yes · C yes · **D fails** · E B-only · F yes · G yes) · [x] uncertainty reported.

## H. Process disclosures
- Two code bugs were found and fixed **before any set was frozen**: (i) `cycle_scan` skipped mismatched-bottom days instead of taking E3 on `pivot_cycle_state`'s own bottom as the prereg says; (ii) `observation()` started one session late (excluded the session right after the first-touch bar, which the prereg window includes). Both are implementation errors against the written contract, not definition changes.
- The ledger/ordering CSV writer dropped columns absent from the first row; fixed before results were read.
- Controls' observation-stage false-positive rate is 100% by construction (they were selected identity-eligible on the matched date) — the alert stage is the informative one; stated in the prereg (O6).
- `P1` is uninformative by construction and is reported as such rather than as support.
