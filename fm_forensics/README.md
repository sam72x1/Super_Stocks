# fm_forensics — «FAISAL BOT — FORENSIC MASTER MISSION» (2026-10-08) · قراءةٌ فقط · لا إنتاج · لا V4 · لا تلغرام

| File | What |
|---|---|
| `READY_NOW_MASTER_FORENSIC_AUDIT.md` | the 24-section report (start here) |
| `READY_NOW_FINAL_STATUS.md` | the 18-question verdict |
| `READY_NOW_AUDIT_BASELINE.md` | frozen description of the production READY NOW path (L0–L11, live thresholds, output history) |
| `DKI_SXTC_HUBC_FORENSICS.md` | the three anchor cases + CRE control with the lookahead firewall |
| `FAISAL_STATE_MACHINE.md` · `FAISAL_FOCUS_MODEL.md` | reconstructed states/transitions and the focus inputs (hypotheses with evidence classes) |
| `VOLUME_FORENSICS.md` · `GAP_DOWN_FORENSICS.md` · `CRE_FORENSICS.md` · `RSI_READY_FORENSICS.md` · `THREE_CONDITIONS_FORENSICS.md` | modality forensics |
| `PIPELINE_FAILURE_FORENSICS.md` | layer attribution for the anchors and the 279 ≥100% movers |
| `CODE_AND_TEST_AUDIT.md` | sections 32–33 (dead/dormant code, duplicated thresholds, false-confidence tests) |
| `IMAGE_UTILIZATION_FINAL_AUDIT.md` · `IMAGE_UTILIZATION_TABLE.csv` | 772 images: role, trace, eye-read flag |
| `MISSED_INFORMATION_REGISTER.md` | 14 items of information that existed and was not used |
| `READY_NOW_RULE_EVIDENCE_MATRIX.csv` · `READY_NOW_COMPARISON.csv` · `READY_NOW_MISSED_SIGNALS.csv` · `READY_NOW_OUTCOMES.csv` · `FAISAL_FOCUS_TIMELINE.csv` | data tables |
| `READY_NOW_V2_prereg.md` · `READY_NOW_V2_SPEC.md` · `fm_shadow_v2.py` · `READY_NOW_V2_SHADOW_RESULTS.csv` · `shadow/` | the shadow candidate: contract, spec (with the ten adversarial reviews), evaluator, results (branch 2) |
| `fm_bars_probe.py` · `data/bars_2026-10-08.json.gz` | the temporary TradingView bars probe (its workflow was removed after run 37807953508) and its output |

Reproduce the shadow numbers: `python3 fm_forensics/fm_shadow_v2.py` (reads the latest `data/bars_*.json.gz`; deterministic; seed 20261008).

## Phase 2 — «FORENSIC ROOT-CAUSE PROTOCOL — CAUSAL ROOT-CAUSE INVESTIGATION» (2026-10-08) · `phase2/`

Attempted to **disprove** the Phase 1 hypothesis that identity / corporate-action / continuity handling loses Faisal's names before READY NOW. Verdict: identity **rejected** as primary explanation; the first causally supported failure is the **candidate-generation layer** (gate definitions on the provider-adjusted regime vs Faisal's post-split lifecycle frame), Level 4. Read `phase2/PHASE2_FINAL_VERDICT.md` first, then `phase2/PHASE2_ROOT_CAUSE_REPORT.md` (22 answers · Phase 1 re-check · evidence matrix · 15-pass review · integrity checklist).

| File | What |
|---|---|
| `phase2/PHASE2_FINAL_VERDICT.md` · `phase2/PHASE2_ROOT_CAUSE_REPORT.md` | verdict sentence + evidence chain; the full report |
| `phase2/ROOT_CAUSE_MATRIX.csv` · `phase2/ANCHOR_FORENSIC_MATRIX.csv` · `phase2/FIRST_DIVERGENCE_MATRIX.csv` | per-anchor first divergence, necessity/sufficiency, levels; 63 independent Faisal-dated cases |
| `phase2/IDENTITY_PIPELINE_TRACE.md` · `phase2/SECURITY_IDENTITY_LEDGER.csv` | 16-stage code trace of where the ticker/bars/splits flow; 232-symbol identity ledger (UNKNOWN where unavailable) |
| `phase2/M2_FORENSICS.md` · `phase2/SXTC_FORENSICS.md` · `phase2/DKI_FORENSICS.md` · `phase2/HUBC_FORENSICS.md` | what M2 is; the three anchors (HUBC Faisal state = UNKNOWN) |
| `phase2/IDENTITY_COUNTERFACTUAL_RESULTS.csv` · `phase2/MATCHED_CONTROL_RESULTS.csv` · `phase2/NEGATIVE_CONTROL_RESULTS.csv` · `phase2/REJECT_LOG_FORENSICS.csv` · `phase2/FAISAL_DATED_REPLAY.csv` | the controlled experiments (worlds A / ID / B_PSH / B_M4 / B_RAW / B_CUT), matched and negative controls, reject-log reproduction, dated-decision replay |
| `phase2/CORPUS_EVIDENCE_STATUS.csv` · `phase2/CORPUS_REVERIFICATION_REPORT.md` | 772 units by status class; 34 re-read, 20 material, 3 conclusion changes |
| `phase2/FAISAL_STATE_MODEL_REASSESSMENT.md` · `phase2/READY_NOW_TARGET_REASSESSMENT.md` | per-state CONFIRMED/MODIFIED verdicts; READY NOW's target variable |
| `phase2/replay.py` · `phase2/replay_faisal_dates.py` · `phase2/out/` | the replay harness (production `analyze_ticker` unmodified, lookahead-safe) and its raw outputs (`replay_all.csv.gz` 26,769 rows · `replay_anchors.csv` · `groups.json`) |

🔒 Research only: no production, V4, protocol, Telegram or threshold change; no V2/V3/V5 model; no ticker hard-coded as a target.

## Phase 3 — «TEMPORAL SELECTION RECONSTRUCTION — CANDIDATE GENERATION × FOCUS × WATCH × READY × ENTRY WITH STRICT LOOKAHEAD FIREWALL» (2026-10-08) · `phase3/`

Pre-registered (`phase3/PHASE3_prereg.md`, merged before any number). Question: does Faisal select a name **before** it satisfies the bot's candidate gates? Method: Faisal's side reconstructed first from dated units (observation classes MENTION/FOCUS/WATCH/READY/ENTRY/EXIT/UNKNOWN; HUBC UNKNOWN), the bot's side reconstructed per session (candidate = unmodified `analyze_ticker` on bars < date; watchlist / near-watch / READY from git history), then leave-one-gate-out, lead-time with pre-registered labels, persistence, architecture A vs B (memory counterfactual), positive/negative controls, missing-feature matrix, lookahead audit of prior claims. Verdict (Level 4): the first causally supported failure is the **placement of Faisal's trigger rule (two-touch anchor, with M3/M4/M2-ceiling stacked in front) at admission** — his names sit on untested lows when he starts watching; memory alone or any single-threshold relaxation does not restore his timing without ×3 noise. Read `phase3/PHASE3_FINAL_VERDICT.md`, then `phase3/PHASE3_FINAL_REPORT.md` (denominators · 20 answers · 20 adversarial passes · integrity checklist · H1-H6 · P1-P5).

| File | What |
|---|---|
| `phase3/PHASE3_FINAL_VERDICT.md` · `phase3/PHASE3_FINAL_REPORT.md` · `phase3/CANDIDATE_GENERATION_ROOT_CAUSE.md` | verdict + evidence chain; the full report; the §26 root-cause form |
| `phase3/FAISAL_TIMELINE.csv` · `phase3/FAISAL_DAILY_TIMELINE.csv` · `phase3/EARLIEST_FOCUS.csv` | 306 dated observations with classes (235 Faisal); −20..+20 daily grid for 15 tickers; earliest defensible Focus per ticker (never backfilled) |
| `phase3/FIRST_DIVERGENCE_TEMPORAL_MATRIX.csv` | 41 tickers: Faisal's first dated state vs the bot's candidate / watchlist / near-watch / READY on that session and in the 20 before; first structural, state, readiness, entry mismatch |
| `phase3/CANDIDATE_GATE_FORENSICS.md` · `phase3/GATE_CONCEPT_MATRIX.csv` · `phase3/LOGO_SUMMARY.csv` · `phase3/ANCHOR_VARIANTS.csv` | production trace (code read); 16 gates concept/evidence/necessity/sufficiency; leave-one-gate-out on 53 Faisal rows + 160 anchor-days + 1,320 controls; five anchor-rule variants |
| `phase3/TEMPORAL_LEAD_TIME_ANALYSIS.csv` · `phase3/TEMPORAL_PERSISTENCE_ANALYSIS.csv` · `phase3/TEMPORAL_ARCHITECTURE_COMPARISON.csv` · `phase3/TEMPORAL_WINDOW_DISTINGUISHABILITY.csv` | lead time with pre-registered labels and DATA_CUTOFF/DECISION_TIME/LOOKAHEAD_PROTECTION/FUTURE_REVEAL_TIME; persistence both sides; memory N=1/3/5/10/15 vs snapshot; feature separation at T−1…T−15 |
| `phase3/POSITIVE_TEMPORAL_CONTROLS.csv` · `phase3/NEGATIVE_TEMPORAL_CONTROLS.csv` · `phase3/MISSING_FEATURE_MATRIX.csv` · `phase3/MISSING_FEATURE_SUPP_DATE_MATCHED.csv` | 7 positives / 70 negatives (rule fixed in prereg); 10 features; post-hoc date-matched supplement (confound stated) |
| `phase3/DKI_TIMELINE.csv` · `phase3/SXTC_TIMELINE.csv` · `phase3/HUBC_TIMELINE.csv` · `phase3/CRE_TIMELINE.csv` | T−20..T+20 around 2026-09-11: price/volume/structure, bot gates, gates whose removal alone restores, bot states, dated Faisal evidence |
| `phase3/LOOKAHEAD_AUDIT.csv` · `phase3/CORPUS_MATERIALITY_P3.csv` · `phase3/STATE_MODEL_PHASE3_REASSESSMENT.md` | 13 prior claims classified; 11 eye re-reads + recovered owner card + the 10 unrecoverable chat screenshots; Focus/Watch/Ready/Trigger/Entry re-verdicts |
| `phase3/p3lib.py` · `phase3/bot_states.py` · `phase3/logo.py` · `phase3/build_timeline.py` · `phase3/gate_matrix.py` · `phase3/temporal.py` · `phase3/anchor_timelines.py` · `phase3/features.py` · `phase3/variants.py` · `phase3/window_probe.py` · `phase3/out/` | the research harness (CONFIG and `tested_level` restored in `finally`; lookahead-safe) and raw outputs (`bot_states.csv.gz` 30,698 rows · `logo_rows.csv` 1,533 · summaries) |

🔒 Research only: no production, V4, protocol, Telegram, three-condition or threshold change; no V2/V5/temporal engine; no agents; the anchors are 3 of 41 tickers and never a target in logic.

## Phase 4 — «PRE-REGISTERED CAUSAL TEST: FIRST TOUCH → ATTENTION/FOCUS/WATCH → RETEST → TRIGGER/ENTRY vs TWO-TOUCH AS AN EARLY CANDIDATE GATE» (2026-10-08) · `phase4/`

Pre-registered (`phase4/PHASE4_PREREG.md`, merged via #580 before any number; discovery results committed before the frozen validation set was run). Events in production formulas (`tested_level` second touch; `pivot_cycle_state` retest / trigger / break), five research architectures (A current · REMOVE · B · C · D), 164 matched negative controls, feature tests on 14,294 eligible symbol-days. Verdict: the two-touch rule is misplaced at admission — the production second touch never fires on 32/38 of Faisal's levels (his retest is a sweep), his dated Watch precedes the lifecycle retest more often than not, and architecture B (first touch → observation, second touch → alert) keeps his names as objects at lower alert noise than the current gate (replicated blind) — **but matched controls show the same first-touch → retest → reclaim sequence at the same rate**, so the misplaced event is a container, not the discriminator. **LEVEL 5 NOT ESTABLISHED** (criterion D fails); Level 4 stands. Read `phase4/PHASE4_FINAL_VERDICT.md`, then `phase4/PHASE4_FINAL_REPORT.md`.

| File | What |
|---|---|
| `phase4/PHASE4_PREREG.md` · `phase4/PHASE4_FINAL_VERDICT.md` · `phase4/PHASE4_FINAL_REPORT.md` | contract; §30 root-cause form + final sentence; denominators · results · H0-H6 · P1-P6 · 20 answers · 20 adversarial passes · integrity · disclosures |
| `phase4/EVENT_LEDGER.csv` · `phase4/PHASE_ORDERING_MATRIX.csv` | 415 event rows (E1 first touch · E2 production second touch · E3 retest · E4 trigger · E5 break) with DECISION_DATE / DATA_CUTOFF / EVIDENCE_CUTOFF / FUTURE_REVEAL_DATE; per-ticker ordering (EXPECTED 15 · CONTRADICTED 12 · INSUFFICIENT 11) with per-class reading |
| `phase4/FIRST_TOUCH_ANALYSIS.csv` · `phase4/SECOND_TOUCH_ANALYSIS.csv` · `phase4/TEMPORAL_ROLE_ANALYSIS.csv` · `phase4/FEATURE_TESTS.csv` · `phase4/TRANSITION_ANALYSIS.csv` | lead times first touch → states; E2/E3/E4 position vs each state; role reading; §18-19 feature tests; §21 transitions |
| `phase4/ARCHITECTURE_COMPARISON.csv` · `phase4/STATE_ALIGNMENT_MATRIX.csv` · `phase4/MOVE_VS_REMOVE_RESULTS.csv` | A/REMOVE/B/C/D per set: recall any/matched stage, first divergence, alert- and observation-stage false positives, transition timing; per-state alignment with Wilson intervals; the pre-registered MOVE-vs-REMOVE rule |
| `phase4/POSITIVE_VALIDATION_CASES.csv` · `phase4/NEGATIVE_VALIDATION_CASES.csv` | 41 positives with buckets; 164 matched control-days (procedure §⑦, seed 20261008) |
| `phase4/DATA_AVAILABILITY_AUDIT.csv` · `phase4/PHASE4_GATE_STAGE_MATRIX.csv` | §24 data vs model vs state-model missing per event; §25 stage of every gate before the anchor |
| `phase4/p4lib.py` · `ledger.py` · `controls.py` · `arch.py` · `features.py` · `audits.py` · `phase4/out/` | the harness (production code unmodified; CONFIG restored in `finally`) and raw outputs (`extra_states.csv` replays for control symbols · per-set rows · sequence comparisons) |

🔒 Research only: no production, V4, protocol, Telegram, three-condition or threshold change; no V2/V5/temporal engine; no agents; anchors (DKI/SXTC/HUBC) excluded from every rule count.

## Phase 5 — non-candle information × Faisal selection (2026-10-08 · `phase5/`)

Pre-registered (`phase5/PHASE5_PREREG.md`, PR #582 before any number): four feature families with point-in-time vintages — float ≤ 5M, final prospectus ≤ 90 d (SEC EDGAR), borrow available < 20k, reverse split ≤ 120 d — on 38 primary Faisal selections vs 134 matched control-days (matching never uses the tested features), discovery 23 / validation 15 by hash, Bonferroni 98.75% CIs, placebo at T−60, Phase 4 audited first (`PHASE5_PHASE4_RECONCILIATION.md`, 51/51 reproduced; 4 bar-less tickers named). **Verdict** (`PHASE5_FINAL_VERDICT.md`): float and borrow **NOT TESTABLE** (no point-in-time history before the bot's own records); offering status **UNSUPPORTED** (sign flips between halves); split age — association present and directionally replicated (+0.30 / +0.27) but **UNSUPPORTED by the pre-registered verification floor** (foreign filers cannot be SEC-confirmed; amendment A1) and not distinguishable from the eligible population's split profile; H6 null stands. Outputs: manifest, availability inventory (`PHASE5_FEATURE_AVAILABILITY.csv`), source ledger, matched-control manifest, exploratory register, `out/results_*.csv`, report. SEC data collected once on a runner (`phase5/sec_probe.py` → `data/sec_2026-10-08.json.gz`; the temporary workflow was removed). No production change.
