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
