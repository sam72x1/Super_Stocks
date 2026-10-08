# READY_NOW_MASTER_FORENSIC_AUDIT — «FAISAL BOT — FORENSIC MASTER MISSION» (2026-10-08)

> Main branch at mission start: `bc1681f9e`. Nothing in production, V4, prospective validation, Telegram output or the live scanner was modified. All artifacts live under `fm_forensics/`. Shadow numbers depend on the TradingView bars probe (PR #575); wherever they are not yet available this report says PENDING, not a number.

## 1. EXECUTIVE SUMMARY
- READY NOW is a **price-location flag on a daily-recomputed 15-slot watchlist** (`entry_status`: near_support/sweep_confirmed ∧ price ≤ top tranche). It has no persistence, no stage, no trigger.
- Faisal's visible process is a **persistent, staged focus pipeline** (فرز أول → فرز ثاني → تحت الجاهزية → جاهز 100%) with the **entry on a trigger** (operator pressure: sweep 7–13% under the base then reclaim) — 5 direct images across 3 tickers, plus the pipeline screenshot of 2026-09-13.
- The three anchors never entered the watchlist (526 snapshots). SXTC and HUBC were blocked every day at M2 (post-reverse-split 52-week high → drop > 99.95%); DKI passed every identity gate for three weeks and was blocked only by the two-touch anchor rule (`tested_level`) — exactly Faisal's WATCH stage.
- Broad sample: of 279 ≥100% movers in the bot's own register, **2** were READY NOW within 14 days before the move (0.7%); 73 were blocked at the anchor rule and 46% were already inside the bot's near-watch state but invisible (top-20 display cut).
- Of 117 symbols ever READY NOW, 29 reached the bot's t1, **70 were stopped out** (stop 5–7% below anchor, inside the 7–13% sweep Faisal waits for).
- Verdict (§24): **J. MULTIPLE LAYERS**, dominated by **G (WATCH/READY state failure)** with **H (trigger)** and **D/C (split-reference and anchor at candidate generation)** as the mechanical causes, and **I (output cut)** as the visibility cause. Not A, not B, not K.
- A shadow V2 was justified as a *state* model, pre-registered, and run: **branch 2 (no advantage over a matched control)**, and it exposed that the identity band itself (drop 71.7–99.95% from the 52-week high) cannot admit post-split bases whichever reference high is used — the deeper mismatch sits in candidate generation, not only in the state flag.

## 2. THE CORE FAILURE
State-model mismatch. The bot asks every day "is this stock at its tested support right now, inside my 15 slots?"; Faisal asks "which of my focus names has matured to the pressure stage?". The first question cannot express the second: membership is recomputed (no persistence), readiness is a location (no stage), and the entry has no trigger. Evidence: `PIPELINE_FAILURE_FORENSICS.md` §3–4; `FAISAL_STATE_MACHINE.md`.

## 3. WHAT FAISAL ACTUALLY APPEARS TO DO
(Evidence classes in `FAISAL_STATE_MACHINE.md`.) Universe → first screen (post-split/offering collapse, prior concentrated liquidity in the base) → second screen (averages 20/30/50, short availability < 20k, news/offering, groups) → "under readiness" (base holds 3–5 sessions, RSI low, test bounce 10–20%, retest) → "ready 100%" (all indicators) → wait for the operator → enter after the sweep/reclaim with staged orders → exit at the first resistance → re-enter on the next sweep. Focus persists for weeks/months (CRE 13+ months; HUBC across a 1:25 split; SXTC two waves). UNKNOWN: how he drops names; whether the first screen is quantitative.

## 4. FAISAL FOCUS VS READY NOW
| | Faisal | READY NOW |
|---|---|---|
| Membership | persistent focus set, event-driven | recomputed daily, 15 slots, borrow gate |
| Readiness | state (indicators + stability) | location (price ≤ top tranche) |
| Trigger | pressure/sweep/reclaim | none (sweep flag optional) |
| Post-split | base restarts | 52-week high keeps the pre-split level |
| Re-entry | after exit, on next sweep | removed on stop, no re-admission |
| Visibility | ≈12 names in an app list | 15 cards + 20+20 cut of 300 |
FIRST DIVERGENCE: L5/L8 (anchor + membership) for DKI; L2 (split reference) for SXTC/HUBC; L10/L11 for visibility and trigger. `READY_NOW_COMPARISON.csv`.

## 5. DKI FORENSICS
Inside the Faisal envelope 09-02 → 10-02 (RSI 21–45), rejected daily only by `M_لا_مستوى_مختبر`; shown to the owner once (09-18). Faisal: in the 09-13 list; late-Sept WAIT for a sweep to ≈2 then buy. The sweep came far deeper (to 1.29 on 10-02 = −41%), which under Faisal's own rule is a new base, and the bot moved DKI to `M4_base_واسعة`. DKI's "major move" VERIFIED from the probe's hourly bars: 1.36 (10-06 close) → 7.43 pre-market 10-08 (+446%) → 0.80 the same regular session (−89%, below the base). Full table in `DKI_SXTC_HUBC_FORENSICS.md`.

## 6. SXTC FORENSICS
1:80 reverse split 08-10 → M2 ceiling every day. Faisal READY on the pressure day ≈09-10 (1.80–1.90), exit 09-11 at ≈3, retest WAIT, re-entry 2.15–2.25 after the 10-07 sweep (10-07 regular high 9.59 = +667% from the 10-06 close, close 2.83; 10-08 collapse to 0.33). The bot showed SXTC only in the oversold list 09-08/09 (bottom of 20) and after the moves in presession digests; the three-conditions tool named it 6 sessions in a row (09-25 → 10-02). The 6.31 target (TG_58527) failed (max 3.27).

## 7. HUBC FORENSICS
1:25 reverse split 09-14; +139% in the week of 09-22 (presession PM alert 09-22 rank 2, sent, during the move); then collapse to ≈1.0. Bot: M2 ceiling every day since 09-23; oversold list 09-30/10-01/10-02 (rank 17–19). Faisal's current thesis rests on the owner's 10-07 chart card («الهدف من 3-4»); **no dated Faisal HUBC text exists in the corpus between 04-24 and 10-07** → the "currently centered on HUBC" premise is owner-reported, chart-verified, Faisal-text UNKNOWN.

## 8. CURRENT BOT FAILURE POINTS
L2 split reference (M2 ceiling) · L5 two-touch anchor (= Faisal's WATCH) · L6 stop inside the sweep zone · L8 daily recomputation / 15 slots / borrow gate (10-07: 2 of 8 slots filled; 28 excluded) · L9 no re-entry · L10 READY = location · L11 display cut 20+20 of ≈300 and a 240 s budget (468 symbols uncomputed on 10-07). `PIPELINE_FAILURE_FORENSICS.md`.

## 9. VOLUME FINDINGS
Faisal's volume = *prior concentrated liquidity in the base* + *a pressure event*; **no numeric threshold anywhere** (X_61_VEEE explicitly rejects current liquidity as the basis). Bot: M5 floor + spike warning. Do not add a volume threshold. `VOLUME_FORENSICS.md`.

## 10. GAP-DOWN FINDINGS
"Gap below must fill" is DIRECTLY_SUPPORTED as Faisal's wait rule (CRE, SNAL — 2 cases) and unconfirmed as a historical magnet (T-GAPBELOW: 53% filled, no advantage, sample under floor). Not modelled in the bot; CRE is the live divergence. `GAP_DOWN_FORENSICS.md`.

## 11. CRE FINDINGS
Open Faisal position since 2025-08 (TG_2103); bot READY NOW 10-06/07/08 on `sweep_confirmed` while Faisal waits for the gap fill → EARLY_READY candidate; RSI 43–55 throughout → focus does not require oversold RSI. Outcome OPEN. `CRE_FORENSICS.md`.

## 12. RSI FINDINGS
"RSI above 40 = ready": **CONTRADICTED** (TG_2043 «مستحيل يصعد إذا RSI بمناطق 40»; 0 supporting images). Low RSI (22–27, ≤33) is a readiness component, not a focus or trigger condition. Already live as soft fail / near-watch bucket / three-cond. `RSI_READY_FORENSICS.md`.

## 13. THREE-CONDITION FINDINGS
A whole-market WATCH-state filter (RSI<33 ∧ float<4M ∧ avail<20k ∧ 5-session hold ∧ no 50% explosion). Orthogonal to READY NOW (universe, anchor, trigger). It named SXTC 6 sessions before its second wave; its precision is UNKNOWN (no outcome harvest). **Do not merge it into READY NOW.** `THREE_CONDITIONS_FORENSICS.md`.

## 14. NEGATIVE EVIDENCE
Per rule in `READY_NOW_RULE_EVIDENCE_MATRIX.csv`: direct rises without retest (X_85, TG_1985); same-day READY on the pressure day (WA_31) against the hold rule; SPRC one-session hold; ENPH/ELAB deep breaks then rallies against the 13% invalidation; ONCO plan with 150k short against the 20k rule; YMT «لا يهم لو دخل قروب» against the groups rule; 6.31 SXTC target failed; the three-condition tool had 0 matches 10-05 → 10-07 right before SXTC's wave; RSI>40 rule has zero support. Corpus decision labels: WAIT 141 vs READY 21.

## 15. IMAGE UTILIZATION AUDIT
772 on disk; 64 re-read by eye in this mission; 708 carried with inherited labels and flagged as not re-read. Trace classes: 114 production-ledger-cited, 42 V4-rule-cited, 565 V4 visual pass, 31 traced, 20 not traced (13 owner screenshots, 2 low-info, 4 B4 read here, 1 case). The pipeline screenshot (X_22) and the volume stance (X_61) were in the corpus and used by nothing. `IMAGE_UTILIZATION_FINAL_AUDIT.md`, `IMAGE_UTILIZATION_TABLE.csv`.

## 16. RULE EVIDENCE MATRIX
19 rules: DIRECTLY_SUPPORTED 10 · STRONGLY_SUPPORTED 3 · SUPPORTED 2 · CONFIRMED (measured) 1 · UNSUPPORTED 1 (volume threshold) · CONTRADICTED 1 (RSI>40) · mixed 1. Of the directly supported rules, 3 are not implemented in the READY path at all (prior liquidity, gap-below wait, focus persistence) and 3 are display-only (sweep trigger, operator wait, test-bounce/retest). `READY_NOW_RULE_EVIDENCE_MATRIX.csv`.

## 17. STATE MACHINE
UNSEEN → SCREENED → FOCUS → DEVELOPING → WATCH → READY → TRIGGERED → ENTERED → (exit → WATCH loop); INVALIDATED/ABANDONED. Transition evidence table in `FAISAL_STATE_MACHINE.md`. READY NOW ≈ Faisal's "inside the zone" sub-condition, not his READY and not his TRIGGER.

## 18. SHADOW V2
Justified as a state model (`READY_NOW_V2_SPEC.md`), pre-registered before any number (`READY_NOW_V2_prereg.md`), evaluator written and self-tested on synthetic bars (`fm_shadow_v2.py`: FOCUS→WATCH→READY→TRIGGER sequence reproduced). Ten adversarial reviews with the 20 questions recorded in the spec; Q20 (unseen examples) is UNKNOWN until the holdout runs. **Isolated: no import from production, no Telegram, no state writes, anchors excluded from scores.**

## 19. CURRENT VS V2
Run on `bars_2026-10-08.json.gz` (232 symbols, probe run 37807953508). HOLDOUT (275 non-anchor ≥100% movers): V2 WATCH-or-higher within 14 sessions before the move **30.2% [25.1, 35.9]** vs date-matched control **25.1% [20.3, 30.5]**; READY-or-higher 23.3% [18.7, 28.6] vs 17.5% [13.4, 22.4]; three-conditions approximation 16.7%; **current READY NOW 1.1% [0.4, 3.2]**. VAL (69 dated non-anchor Faisal rows with bars): WAIT 57 → V2 REJECT_M2_LO 46 / READY 3 / TRIGGER 3 / FOCUS 2 / WATCH 1 / M4 2; READY 5 → FOCUS 3, REJECT 2 (**0/5 READY recall; n < 20 ⇒ UNKNOWN by contract**). Full rows in `READY_NOW_V2_SHADOW_RESULTS.csv`.

## 20. GENERALIZATION / HOLDOUT RESULTS
**Prereg branch 2 — no advantage.** The Wilson intervals of movers and control overlap on both WATCH+ and READY+; P2 (≥40%) FAILED; P1 (VAL n < 20 per class) held; P3 (current READY NOW < 2%) held; P4 (V2 flags more) held. Deviation disclosed: the control was drawn from the probe population (watchlist/V4-case tickers) rather than from near-watch snapshots, which makes the control a *selected* set and the comparison conservative. **Identity finding (more important than the branch):** with the post-split high as the M2 reference (`split_restart`), SXTC and CRE are REJECT_M2_LO every day and 46 of 57 Faisal WAIT rows fall below the 71.7% drop floor; without the restart they exceed the 99.95% ceiling. The catalog envelope band cannot describe a post-split base either way — the band, not only the anchor rule, is the mismatch. Anchors (descriptive only): DKI READY 09-15→09-29 (Faisal's WAIT window), TRIGGER 09-09, INVALIDATED 09-30; HUBC WATCH/READY before its 09-14 split then REJECT; SXTC/CRE REJECT throughout. **Conclusion: the V2 as specified is not accepted; the state model is not refuted either — it was never allowed to see Faisal's names because the identity band removed them. Next measurable step: a pre-registered identity definition for post-split bases (research queue), not a production change.**

## 21. DEVELOPMENT PERCENTAGES (numerator / denominator / definition / evidence / uncertainty)
| Dimension | Value | Numerator / Denominator | Definition | Evidence | Uncertainty |
|---|---|---|---|---|---|
| CORPUS UTILIZATION (traced) | 97.4% | 752 / 772 | images with any trace (ledger, V4 rule, V4 pass, EX trace) | utilization table | inherited for 708; trace ≠ decision use |
| CORPUS UTILIZATION (decision-bearing in READY path) | 14.8% | 114 / 772 | images cited for a live threshold/line in the ledger | ledger citations | many cited rules are display-only |
| EVIDENCE COVERAGE (eye, this mission) | 8.3% | 64 / 772 | pixels re-read in this mission | EYE_READ_FM | the remaining 91.7% rely on prior passes |
| RULE RECONSTRUCTION | 52.6% | 10 / 19 | rules DIRECTLY_SUPPORTED (≥2 images, Faisal's words) | matrix | class boundaries are judgement |
| FAISAL FOCUS RECONSTRUCTION | 60% | 6 / 10 | focus inputs with DIRECT/STRONG support (focus-model table) | `FAISAL_FOCUS_MODEL.md` §1 | no explicit drop rule; list size unknown |
| READY RECONSTRUCTION | 75% | 3 / 4 | READY components (zone, hold, RSI, indicators) directly supported | state-machine table | "all indicators" list not enumerated by Faisal |
| TRIGGER RECONSTRUCTION | 100% of the stated mechanism / 0% observable | 5 images, 3 tickers; intraday flow unavailable since 09-29 | sweep+reclaim+operator | TG_57894, WA_31, TG_58417, TG_2097, TG_57870 | daily bars see only the sweep/reclaim part |
| CURRENT BOT IMPLEMENTATION (of the 10 directly supported rules) | 40% | 4 / 10 | rule acts on READY membership or state (not display-only) | matrix CODE_LOCATION | — |
| VALIDATION (shadow V2 vs Faisal labels) | 0% READY recall (n=5 ⇒ UNKNOWN) | 0 / 5 | V2 READY-or-higher on dated Faisal READY days | shadow CSV | n < 20; identity band removed most rows |
| GENERALIZATION (holdout advantage over control) | NOT SHOWN | 83/275 vs 69/275 | WATCH+ before a ≥100% move, movers vs control | shadow CSV | intervals overlap; control is a selected pool |
| READY NOW recall on ≥100% movers | 0.7% | 2 / 279 | READY within 14 d before the move | missed-signals CSV | register is bot-built, not Faisal's picks |
| READY NOW precision (bot's own t1) | 24.8% | 29 / 117 | ever-READY symbols that hit t1+ | outcomes CSV | stop inside sweep zone inflates FALSE_READY |

## 22. REMAINING UNKNOWN INFORMATION
HUBC Faisal text 04-24 → 10-07 · exact dates of «2026-09-2x» posts · three-condition precision · split dates for the holdout population (probe will fetch Yahoo ∪ NASDAQ) · the ≈10 chat screenshots the owner sent on 10-08 (unreadable here) · Faisal's first-screen criteria and list churn · intraday operator flow (no source since Polygon ended).

## 23. RECOMMENDED NEXT DEVELOPMENT STEP
1. Done: probe + shadow ran → branch 2; the identity band (M2 71.7–99.95%) is the first thing to re-define for post-split bases, by a new pre-registered contract (3 years, matched control) — research, not production.
2. Only after that contract passes: owner decision on a **shadow display** (not a replacement) — a persistent "تحت الجاهزية" list with state per name and the trigger line; measured prospectively for ≥ 20 cases before any production use.
3. Independently of V2 (owner decisions, each reversible): (a) raise the near-watch display cut or sort "inside" by hold/RSI rather than readiness; (b) harvest outcomes for three-condition matches; (c) a pre-registered test of the post-split M2 reference on the READY path (3 years, matched control).

## 24. FINAL VERDICT
**J. MULTIPLE LAYERS** — with the evidence ranked: G WATCH/READY STATE FAILURE (READY = location, no persistence; 73/279 + DKI at the anchor), H TRIGGER FAILURE (no trigger in the READY path; 70/117 stop-outs inside the sweep zone), C/D CANDIDATE GENERATION (post-split M2 reference removes SXTC/HUBC permanently), I OUTPUT (46% of movers were in near-watch state and invisible). Not A (data arrives and splits are known), not B (universe contains all three), not K (the corpus contains direct, multi-image evidence for the process). Eighteen-question verdict: `READY_NOW_FINAL_STATUS.md`.
