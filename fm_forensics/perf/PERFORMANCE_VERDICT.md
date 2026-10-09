# PERFORMANCE VERDICT

## C. NO DEMONSTRATED IMPROVEMENT

**What was tested.** One preregistered comparison (`PERFORMANCE_EXPERIMENT_PREREG.md`, PR #586 merged `b7cadb70` before any number): the frozen production bot (A, `b8b1242e`) against the frozen Phase 4 architecture B (anchor rule moved from admission to the alert stage; name held from its first touch of the 30-bar low) with a simple screen baseline (BASE2: RSI14 < 33 ∧ ≥ 70% below the 52-week high) and matched control-days (BASE3).

**What changed in the research branch.** Nothing in production: `fm_forensics/perf/perf.py` + outputs + these reports; roots fingerprint and `Super_stock.py` identical before and after; no V4, Telegram, threshold or three-condition change.

**Sample.** 83 dated Faisal rows / 41 securities with bars: development (discovery) 46 rows / 22 securities, validation 29 rows / 16 securities (contaminated by one prior view in Phase 4; no untouched Faisal decision after 2026-10-08 exists), anchors 8 / 3 excluded from counts. Controls: 88 + 64 matched control-days (63 + 31 securities).

**Primary metric (denominators).** Likelihood ratio at the alert stage = security-level recall ÷ control-day flag rate. A: 0/22 ÷ 15/88 = 0.00 (discovery), 2/16 ÷ 15/64 = 0.53 (validation). B: 1/22 ÷ 9/88 = 0.44, 2/16 ÷ 7/64 = 1.14. BASE2: 5/22 ÷ 22/88 = 0.91, 5/16 ÷ 10/64 = 2.00.

**False positives.** B lowers control flags (10.2% / 10.9% vs 17.0% / 23.4%) but its observation pool flags 100% of matched controls (≈ 380–410 symbols/day at universe level). Alert volume does not rise; identification does not either.

**Against each baseline.** vs A: recall unchanged (+1 security in discovery, 0 in validation; CI lower bounds 0); vs BASE2: lower LR in both sets; vs matched controls: no method separates Faisal's names from controls at the alert stage with any confidence.

**Independent validation.** Not available — the only holdout was viewed once before (declared in the prereg, verdict ceiling "promising but unvalidated"); the result did not reach even that ceiling.

**Uncertainty.** Cluster bootstrap by security (2000): recall_B − recall_A 95% CI [0.00, +0.14] / [0.00, 0.00]; LR_B/LR_A CI [0, 0] / [0, 4.0]. Sixteen to twenty-two securities per set: a true +0.10 recall gain would have had a reasonable chance of showing; the observed gain is 0–1 security.

**Earliest failure.** Established as a location (candidate generation; anchor rule first on 20/53 rows; M2/M4 split artefacts for SXTC/HUBC) — `FIRST_DIVERGENCE_REPORT.md`. Not established as a defect whose correction improves identification.

**What would change the verdict.** (1) A new, untouched set of ≥ 15 dated Faisal decisions after 2026-10-09 (collected prospectively; Phase 6 collector is already recording the non-candle fields) on which a preregistered method reaches LR ≥ 2 × A with a CI excluding 1; or (2) a non-candle input with point-in-time history that separates his names from matched controls on the untested low (Phase 5 found none testable before today). A method that only changes candle-based gate placement is unlikely to change it: its alert event is the one A already uses.

**Target C (separate).** Faisal's securities made +50% within 20 sessions in 9/22 (development) and 4/16 (validation, 13/16 right-censored) vs matched controls 29/88 and 21/64; no flagged subset differs from its flagged controls with confidence at these sizes.

**FINAL QUESTION — "Did the single preregistered experiment demonstrate a reproducible, material improvement in identifying Faisal-selected stocks before their major moves, without unacceptable false positives?"  → NO.**

Evidence: `out/perf_results.json` (verdict field, acceptance rules 1/2/6 false in both sets), `out/perf_rows.csv`, `out/perf_controls.csv`; isolated suite and CI identifiers in the PR body and memory.

## Adversarial audit (mission §13)
- Target measures Faisal's selection: yes — positives are dated FOCUS/WATCH/READY/ENTRY units with provenance; controls are UNKNOWN, never negatives; the 2 NEGATIVE_DIRECT rows are too few to use.
- Unknown treated as negative: no — control flags are "flags without documented attention"; Phase 4 bounds later-documented attention among such names at ≈ 3%.
- Repeated tickers inflating n: no — all acceptance quantities are security-level; row-level shown alongside.
- Known winners shaping the alternative: B was frozen in Phase 4 before this experiment; anchors excluded; no parameter set here.
- Current data leaking into history: bars < T; states from units ≤ T; thresholds are today's envelope (declared limitation).
- Baseline reproduced exactly: A at T agrees with Phase 3/4 (2/46, 3/29, 15/88, 15/64); Phase 6 trace 6/6.
- Controls eligible and fairly matched: Phase 4 procedure (no future outcomes); B observes 100% of them by construction — stated.
- Alert volume / FP: B's control alert rate lower; observation pool large (≈ 11–12% of the universe/day) — stated.
- Validation truly independent: no — declared before the run; verdict unaffected because the result fails anyway.
- Survives alternative assumptions: robustness subsets keep the failing direction; BASE2 beats B under every subset.
- Production behaviour changed: no (fingerprints).
- Conclusion within evidence: yes — "no demonstrated improvement", not "impossible".
