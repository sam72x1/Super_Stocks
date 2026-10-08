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
