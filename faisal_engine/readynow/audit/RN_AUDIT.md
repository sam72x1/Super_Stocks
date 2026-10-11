# READY NOW forensic audit — were the documented technical conditions actually tested?

Audit of `faisal_engine/readynow/` (seal `217ba85e2`, result `318511160`) and `faisal_engine/seq70/S70_RESULT.md`.
Research only: no production, Telegram, schedule, threshold, membership, frozen-axis or sealed-result change; no network
request; no agents or workflows. New evidence produced here: `audit/data/chip_parity.json` (the READYNOW proxies
against the condition states the app itself displays, `rn_chip_parity.py`) and `audit/data/seed_audit.json`
(`rn_seed_audit.py`). Sections 1–6 and the plan in §7 were written and pushed before the evaluation in §7 was run.

**Short answer: no.** READYNOW's negative verdict covers one candidate (RSI < 30 ∧ bounce 10–40%). Of the app's eight
automatic conditions, only two are reproducible from local data with demonstrated parity: distance to the support
and bounce. The proxy READYNOW used for «stability» contradicts the app's own screenshots in 5 of 7 snapshots. Retest
and momentum were never implemented. «Below EMA» has no confirmed definition. Two conditions are unnamed, and the short
condition and float have no point-in-time history.

## 1. SOURCE_TO_TEST_MATRIX
Evaluation layers: **dev** = development 2025-05-01 → 12-31, POS710 labels (onset in 7–10 sessions), `data/dev.json`,
`data/dev_round2.json` · **OOS** = validation + holdout, `data/result.json` · lift = precision ÷ base rate; matched =
vs same-session pivot-days matched on price bucket, volume, volatility and liquidity (95%). Parity = agreement with
the state the app shows on its screenshots (`audit/data/chip_parity.json`).

| # | source condition (official wording) | source reference | definition status | READYNOW implementation | history · PIT | evaluated | result | status |
|---|---|---|---|---|---|---|---|---|
| A1 | «أسفل EMA20/30/50» — price below the three daily EMAs | `TG_57914`, `TG_57915`, `TG_57876`, `TG_57880`, `TG_57882`; `faisal_batches/2026-10-01/EVIDENCE_REPORT.md` §⑨ | EMA values confirmed (`ewm(adjust=False)`, last 250 bars); **the condition is UNKNOWN** (parity P6 6/8, visible 3/5) | `BELOW3`: close < EMA20, EMA30 and EMA50 on the full adjusted history (`rn_build.py:103`) | daily ✓ · PIT ✓ (G1) | dev only, alone | lift 1.05 [1.01, 1.09] · matched 1.25 [1.00, 1.55] · **parity 6/9** | partially tested; not equivalent |
| A2 | «ثبات يومي جلستين على الأقل» — daily stability, at least two sessions | `TG_57913`, `TG_57924`, `TG_57925`, `TG_57876`, `TG_57880` | **UNKNOWN** (EVIDENCE §⑥ CUSTOM-02) | `HOLD2`: ≥ 2 sessions since the 25-session low, close above it (`rn_lib.py:63`) | daily ✓ · PIT ✓ | dev: alone + inside APP3 | lift 0.96 · matched 0.84 · **parity 2/7** (the app shows it missing for NTCL 15 sessions after its low, and for ZNB, OMH and CIIT) | **not tested** (proxy contradicts the app) |
| A3 | «السعر خارج نطاق 15% من الدعم» / «منطقة اختبار الدعم 0%–15%» | `TG_57913`, `TG_57917`, `TG_57880`, `TG_50592` | support = lowest daily low (confirmed 8/8; **window UNKNOWN**); distance = app price ÷ support − 1 | `NEAR15`: close ≤ 1.15 × 25-session low (`rn_build.py:83`, `rn_lib.py:66`) | daily ✓ · PIT ✓ | dev: alone, APP3, SEQ_BASE, SEQ_TURN, CYCLE_NEAR, TC_NEAR, TC_APP · **never OOS** | lift 1.02 [0.96, 1.09] · matched 1.23 [1.01, 1.49] · **parity 9/9** (LIMN's base 3.32 vs 3.29) | tested in dev only |
| A4 | «الارتداد خارج النطاق المثالي 10–40%» | `TG_57924`; EVIDENCE §⑨ (bounce 7/7) | **confirmed**: highest high from the low day inclusive ÷ low − 1 | `BOUNCE10_40` (`rn_build.py:82`, `rn_lib.py:67`) | daily ✓ · PIT ✓ | dev: alone, APP3, TC_BOUNCE, TC_APP · **OOS only inside RN_A** | lift 1.07 [1.00, 1.15] · matched 1.34 [1.11, 1.63] · **parity 8/8** | tested in dev; OOS only combined with RSI < 30 |
| A5 | «بانتظار إعادة اختبار يومي ناجح» / «اختبار ناجح» | `TG_57924`, `TG_57913` | **UNKNOWN** (CUSTOM-02) | **none** (`CYCLE3` = Faisal's TG_50584 cycle, a different source) | — | never | CYCLE3 vs the app's retest: parity 3/9 | **not tested** |
| A6 | «الزخم اليومي و4H تحسّن» | `TG_57876` | **UNKNOWN** (P7: MACD daily ∧ 4H 6/7 · 5/7) | **none**; `MACD_POS` (the app's MACD *display field*, `rn_build.py:104`) tested as a daily stand-in | 4-hour bars not archived | dev, MACD_POS alone | MACD_POS lift 0.95 · matched 0.95 · parity vs the chip 6/7 | **not tested** |
| A7–A8 | two unnamed conditions | count from «اكتمال الشروط …/8» | **no source** (owner: «هذي جميع الصور …»); satisfied in all 7 counter snapshots | none | — | never | — | untestable |
| A9 | «شرط الشورت» (iBorrowDesk; «حالة الشورت: إيجابي») | `TG_57916`, `TG_57914` | criterion UNKNOWN | none | **no point-in-time history** (ChartExchange harvest from 2026-08, bot lists only) | never | — | untestable |
| A10 | Free float ≤ 5 M («الحد النهائي 5 ملايين») | `TG_57915`, `TG_57918`, `TG_57919` | list filter (TradingView float) | none | **no point-in-time float** | never | — | untestable |
| A11 | score 100 − 12 × missing − 5 × short; «قريب من الجاهزية» / «مراقبة مبكرة» | EVIDENCE §③-٤ (6/6) | label thresholds UNKNOWN | none | depends on A1–A9 | never | — | untestable |
| A12 | the app's universe: split-cycle stocks («أفضل فرص دورة التقسيم … من أسهم التقسيم فقط») | `TG_57926` | list criteria UNKNOWN | population = pivot identity M1–M3 (`pi_obs`); recent reverse splits partly excluded by the frozen M2 ceiling | — | split ≤ 120 d as one condition (dev) | SPLIT120 lift 1.16 [0.99, 1.34] | not evaluated on the app's own domain |
| T1 | tool: RSI14 < 33 | `three_cond_daily.py:204,210` | exact | `RSI33` (`Super_stock.rsi`) | ✓ | dev alone; OOS inside TC_TECH | lift 1.41 [1.25, 1.59] · matched 1.47 [1.14, 1.91] | tested |
| T2 | tool: float < 4,000,000 | `opentry_link_probe.py:43` | exact | none | **no PIT float** | never | — | untestable |
| T3 | tool: available-to-borrow < 20,000 | `opentry_link_probe.py:43` | exact | none | **no PIT borrow** | never | — | untestable |
| T4 | tool: 5 sessions above the exact low (hourly extended + daily lows) | `three_cond_daily.py:307` | exact | `HOLD5` on daily lows only | hourly bars not archived | dev alone; OOS inside TC_TECH | lift 0.96 · matched 0.97 | approximate |
| T5 | tool: no +50% within 5 sessions (incl. after-hours highs) | `three_cond_daily.py:339` | exact | `NO_BOOM` on regular highs | after-hours not archived | dev alone; OOS inside TC_TECH | lift 1.00 | approximate |
| T6 | tool's technical conjunction | — | — | `TC_TECH` = T1 ∧ T4 ∧ T5 | — | dev; OOS comparator | dev 1.65 · validation 1.07 · holdout 1.64 | tested (technical part only) |
| F1 | Faisal: «rsi اقل من 30» | DRCT | exact | `RSI30` | ✓ | dev; OOS ablation; inside RN_A | dev 1.55 · val 1.35 · hold 1.57 | tested |
| F2 | Faisal: hold the bottom 3 sessions | `IMG_0151` | reading «sessions after the low» | `HOLD3` | ✓ | dev | lift 0.95 · matched 0.87 | tested (dev) |
| F3 | Faisal: oversold reached at the bottom · bearish averages | `IMG_6814` (text record only) | reading | `OS_AT_LOW` · `BELOW3` | ✓ | dev | 1.11 · 1.05 | tested (dev) |
| F4 | Faisal: «فجواته عالية» · «ربحه عالي» | `IMG_6814` | gaps computable; «high profit» has no formula | none | ✓ (gaps) | never | — | not tested |
| F5 | Faisal's cycle: bottom → ~20% test → hold/sweep 7–13% → stability | `TG_50584`, `IMG_0297` | codified as `pivot_cycle_state` | `CYCLE3` (stage ≥ 3) | ✓ | dev alone + CYCLE_NEAR | 1.00 · 1.03 | tested (dev) |
| F6 | Faisal's panel: EMA 9/26 cross | `TG_57927`/`57928` | indicator, no stated condition | `EMA_UP`, `EMA_X5` (cross up ≤ 5 sessions) — an interpretation | ✓ | dev | 0.91 · **0.75 [0.55, 0.97]** | tested (dev, interpretation) |

Combinations and order (dev only): APP3 (A2 proxy ∧ A3 ∧ A4) 0.98 · SEQ_BASE 1.15 · SEQ_TURN 1.27 · CYCLE_NEAR 1.03 ·
TC_SPLIT 1.32 · «oversold at the low, then hold» 0.96 vs «oversold now and hold» 1.49 · round 2: TC∧A4 1.72 (within
the tool 1.09), TC∧A3 (0.68 within), TC∧A3∧A4 (0.70 within), RN_A 1.65. **The pair A3 ∧ A4 alone was never evaluated.**

## 2. SEED_TIMELINE_AUDIT (`audit/data/seed_audit.json`)
Onset rule used everywhere: L = the session after the trough close of a clean episode of the bot's daily-close
detector (one-day close jump ≥ 50% or ≥ 70% run in 20 sessions; READY70 `episodes_for`). IGN = largest one-day close
gain in [L, D1]. Labels are known only for decisions up to 2026-08-27.

| seed | qualifying event? | L · IGN · +70% close | T−10…T−7 under L (label) | under IGN | conditions in the 30 sessions before IGN |
|---|---|---|---|---|---|
| DLXY | yes, jump +451.8% (D1 09-16) | **08-31** · 09-16 · 09-16 | 08-17…08-20, pivot, POS710 | 09-01…09-04, pivot, **IN_EVENT under L** | RSI never below 33; A3 ∧ A4 on 12 sessions from 08-04, **none at T−10…T−7** (distance 18–30%) |
| RETO | yes, jump +676.3% | 09-15 · 09-15 · 09-15 | 08-31…09-03, pivot, **CENSORED** | same | tool's part first 09-03 (7 before), RSI < 30 from 08-11, RN_A and A3 ∧ A4 only from 09-11 (2 before) |
| SXTC | yes, run +78.5% | 06-08 · 06-11 · 06-12 | 05-22…05-28, pivot, POS710 | 05-28…06-02 | **A3 ∧ A4 on 4/4 days under L**; RN_A not (RSI 31.6–35); tool's part 1 day |
| SXTC | yes, jump; peak +134.5% | 07-30 · 08-04 · 08-04 | 07-16…07-21, pivot, POS710 | 07-21…07-24 (2 outside the population) | RN_A from 07-28, A3 ∧ A4 from 07-29 (5 and 4 before IGN) |
| SXTC | yes, jump +126.4% | 10-07 · 10-07 · 10-07 | 09-23…09-28, **outside the population (M2)**, CENSORED | same | tool's part 4/4; RN_A 0 (bounce 68.5%); RSI < 30 for 30 sessions |
| DKI | **no**: 10-07 closed +22.8% (1.36 → 1.67) after an intraday +168%; 10-08 closed 0.7457 | — | — | — | not a daily-close event and after 08-27: **neither a success nor a failure** of any rule here |

- **Onset reliability:** L for DLXY is a detector artefact. The jump was detected on 09-16, and later run detections
  moved the start back to the 08-28 trough over a flat base ($0.38–0.44). The pre-jump days were therefore labelled
  IN_EVENT and dropped. Over all 3,727 clean episodes, IGN falls on L in 21%; **IGN comes ≥ 7 sessions after L in
  44%** (runs 55%, jumps 26%; median 5, max 19); the +70% close falls on L in 9.5% (median 10 sessions after).
- **Timestamps:** the T−10…T−7 sessions were the correct ones for L. Only DLXY-L, SXTC-06/08 and SXTC-07/30 are
  label-known. Every seed was excluded from all statistics (`rn_lib.EXCLUDE`), so the «captured none» statement is
  descriptive (verified: RN_A held on none of the five windows).
- **Multiple episodes:** handled consistently. Each wave is a separate episode, rows inside an episode are IN_EVENT,
  and rows between waves are labelled against the next onset (SXTC 06-08 → 07-30 → 10-07; HUBC 05-28 → 06-15).
- **Intention vs result:** the seeds share no technical signature at T−10…T−7 (the matrix in `seeds_matrix.json`).
  The candidate came from the 2025 universe, not from the seeds, and missed all five. The app's reproducible pair
  (A3 ∧ A4) did hold for SXTC-06/08 at T−10…T−7 and for HUBC's 05-28 jump (3 of 4 days).
- **HUBC (current, descriptive):** outside the pivot population; 10-08 RSI 21.65, 13.3% above the 0.8826 low, bounce
  28.0%, held 6 sessions; RN_A on since 09-30, the tool's part since 10-07, A3 ∧ A4 on 10-02, 10-05, 10-07 and 10-08.
  HUBC was excluded from every statistic, including its past episodes.

## 3. NEGATIVE_RESULT_SCOPE
- **A. Tested directly (faithful definition):** RSI14 < 33 (tool), RSI < 30 (Faisal), within 15% (app; parity 9/9,
  base-window caveat) and bounce 10–40% (app; parity 8/8). The RSI conditions were tested in dev and OOS. Within 15%
  was tested in dev only. The bounce band was tested in dev, and OOS only inside RN_A.
- **B. Approximately or indirectly:**
  - **Tool proxies:** hold ≥ 5 on daily lows (the tool uses hourly extended lows); no boom without after-hours highs.
  - **Condition-level proxies:** «below EMA» on its plain reading (P6 failed; 6/9); MACD daily as momentum (daily part
    only; 6/7); EMA 9/26 cross (an interpretation); oversold at the low; hold 3.
  - **Proxies shown not to be the app's condition:** HOLD2 as «stability» (2/7) and CYCLE3 standing near «retest» (3/9).
- **C. Never implemented or evaluated:**
  - **App:** retest; momentum (needs 4-hour bars); the two unnamed conditions; the short condition; float ≤ 5 M; the
    score and its labels; the app's own split-cycle population.
  - **Tool:** float < 4 M and available < 20 k.
  - **Faisal:** high gaps and high profit (`IMG_6814`).
- **D. Excluded for missing data or definitions — yes:**
  - **Missing data:** point-in-time float and borrow; 4-hour and hourly bars; after-hours highs.
  - **Missing definitions:** two unnamed app conditions; the stability, retest, momentum and below-EMA rules.
  - **Missing images:** no condition lost. `TG_57920` is byte-identical to `TG_50592`, which exists and was read.
    `IMG_6814` survives as a verbatim text record of its five conditions and carried no formula.
- **E. Interactions:** mostly evaluated one at a time (dev Layer A), plus 5 declared combinations, 4 post-hoc ones and
  one order test — all in dev. The app's conditions were never evaluated as a set; APP3 contained the non-equivalent
  stability proxy. Out of sample, exactly one conjunction (RN_A) and the comparators (the tool's part, LOC, RSI30).
- **F. The 7–10-session horizon** was applied to every implemented condition, but only in development. Out of sample
  it was applied only to RN_A and the comparators. The decisive tests C1–C3 used onset L only; IGN, L10 and strict +70%
  appeared as raw lifts.
- **G. The verdict covers the selected candidate RN_A only.** It does not cover the app's set, the tool with float and
  borrow, or any untested condition.

## 4. MISSING_OR_APPROXIMATED_CONDITIONS
- **Unavailable source definition** (not «tested and found unhelpful»):
  - **No formula:** the two unnamed conditions; the stability, retest and momentum rules; the condition behind
    «below EMA»; the base-low window; the label thresholds; the split-list criteria.
  - **Unrecoverable source:** `TG_57920` — no impact, because its content is `TG_50592`.
  - **Text-only source:** `IMG_6814` — the text record carries all five of its conditions.
- **Unavailable data:** point-in-time float (tool < 4 M; app ≤ 5 M), point-in-time available-to-borrow (tool < 20 k;
  the app's short condition), 4-hour and hourly bars, after-hours highs.
- **Approximated, with demonstrated non-equivalence:** stability (2/7), retest via CYCLE3 (3/9), below EMA (6/9),
  momentum via daily MACD (6/7).
- **Approximated, with demonstrated equivalence of state:** within 15% (9/9) and bounce 10–40% (8/8). Remaining
  differences: the 25-session window (LIMN 3.29 vs 3.32) and close vs the app's last price.
- **Why it matters:** the app labels a stock «near ready» when at most two of the eight technical conditions are
  missing. With six of eight not reproducible, the app's readiness state cannot be reconstructed historically from
  local data.

## 5. METHODOLOGY_AUDIT
1. **Point-in-time:** conditions use bars ≤ t (guard G1, 80 random rows; mutation M1 fell). READY70's cycle and
   location fields come from a frame cut at t. Labels use the future by design. Ratios are invariant to later splits;
   `dv20` depends on volume adjustment, which is uncertain.
2. **7–10 target vs +70% crossing:** they are distinct by definition (POS710 uses L; x70 is reported separately).
   But the target is «7–10 sessions before the detector's trough + 1». For 44% of events that is 14+ sessions before
   the largest day, and the true pre-jump sessions can be IN_EVENT (DLXY).
3. **Overlap:**
   - **Clustering:** up to four POS710 rows per event, and persistent flags. These are handled by the ticker-cluster
     bootstrap of the flagged ticker, plus event-level recall and triggers.
   - **Control side:** its dependence is not clustered, so CIs may be somewhat narrow. That cannot turn a negative
     verdict positive.
   - **Unmatched rows:** 28–37% of flagged rows found no control and were dropped from C1.
4. **The tool:** represented by its technical part only, so its burden is not comparable with the real tool's. The
   real tool first ran on 2026-09-25 and named SXTC 09-25 → 10-02; the technical part alone already held on SXTC on 14
   of the 30 sessions before its 10-07 jump, starting 08-25.
5. **Baselines:** in dev every condition had matched controls and equal-burden volume, volatility and low-price
   rankings. Out of sample only RN_A and the comparators did.
6. **Specification vs evaluator:** RN_A and TC_TECH match (G8), and the RN_SPEC §2 formulas match the code. Two known
   documentation errors:
   - **Seed range:** the DKI RSI range «34–38» in RN_SPEC (disclosed in RN_REPORT §2).
   - **Source attribution (found by this audit):** RN_SPEC/RN_REPORT call MACD_POS an app condition and HOLD2 the app's
     stability. That makes RN_REPORT's lines «the app's distance, bounce, stability, EMA/MACD … added nothing» (§3, §12)
     too broad. **No sealed number changes;** the RN_A verdict is unaffected.

## 6. MATERIAL_GAPS
| gap | class | resolvable with local data? |
|---|---|---|
| G1 app stability: the proxy contradicts the app (2/7) | DEFINITION_GAP (with an implementation mismatch) | no — the rule is unknown; inferring it from 7 snapshots would be fitting |
| G2 app retest | DEFINITION_GAP | no |
| G3 app momentum (daily + 4H) | DEFINITION_GAP + DATA_GAP | no (no 4-hour history) |
| G4 app «below EMA» | DEFINITION_GAP (P6) | no |
| G5 two unnamed app conditions | DEFINITION_GAP | no (no source) |
| G6 app short condition, app float ≤ 5 M, tool float < 4 M, tool available < 20 k | DATA_GAP | no (no point-in-time series) |
| G7 app score and labels | DEFINITION_GAP (depends on G1–G6) | no |
| **G8 the app's reproducible pair, within 15% ∧ bounce 10–40%: never evaluated together, never out of sample on its own** | **EVALUATION_GAP** | **yes — the one missing evaluation (§7)** |
| G9 the app's split-cycle population vs the pivot population | DEFINITION_GAP (list criteria) + EVALUATION_GAP | partly — the recent-split subset inside pivot rows is reported in §7 |
| G10 decisive tests used onset L only (IGN ≥ 7 after L in 44%) | methodology limitation (documented rule; not a defect) | IGN-label C1 reported in §7 as sensitivity |
| G11 RN_REPORT attribution wording (MACD as a condition, HOLD2 as stability) | documentation defect | corrected here; sealed files untouched |
| G12 `IMG_6814` high gaps / high profit | not tested; identity-level; «high profit» has no formula | not pursued (a new hypothesis, outside the app's set) |
| NO_GAP | RSI33 and RSI30 at 7–10 (dev and OOS) · the tool's technical part as defined · the RN_A verdict itself | — |

## 7. MINIMUM_REQUIRED_NEXT_ACTION
**One evaluation closes G8, and it is fully specified by the source and the parity evidence.** APP_POS = within 15%
of the 25-session low ∧ bounce 10–40%, at 7–10 sessions, with READYNOW's own windows, labels, controls, baselines and
decision rules (C1–C3). The specification is `audit/APP_POS_PREREG.md`, its SHA-256 is pinned in `rn_app_eval.py`, and
it was pushed before the run. Nothing else is resolvable with local data.

*Result: pending (filled in after the sealed run).*

## 8. FINAL_DECISION
*Pending the §7 run.*
