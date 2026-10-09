# PERFORMANCE COMPARISON — frozen bot (A) vs architecture B vs simple screen (BASE2), matched controls (BASE3)

All numbers from `fm_forensics/perf/out/perf_results.json` (one run, no variant search). Anchors excluded from acceptance.

## 1. Primary metric — identification at a common **alert** stage, on/before Faisal's earliest dated decision
| Set | Method | Security-level recall | Row-level | Control-days flagged | LR (recall ÷ control rate) |
|---|---|---|---|---|---|
| discovery (22 sec · 88 ctrl-days) | A frozen bot | 0/22 | 2/46 | 15/88 = 17.0% | 0.00 |
| | **B alert** (first touch held, second touch = alert) | 1/22 | 2/46 | 9/88 = 10.2% | 0.44 |
| | BASE2 (RSI14 < 33 ∧ drop ≥ 70%) | 5/22 | 10/46 | 22/88 = 25.0% | 0.91 |
| validation (16 sec · 64 ctrl-days) | A frozen bot | 2/16 | 3/29 | 15/64 = 23.4% | 0.53 |
| | **B alert** | 2/16 | 3/29 | 7/64 = 10.9% | 1.14 |
| | BASE2 | 5/16 | 9/29 | 10/64 = 15.6% | 2.00 |

Cluster bootstrap by security (2000 draws): recall_B − recall_A 95% CI = [0.00, +0.14] (discovery), [0.00, 0.00] (validation); LR_B / LR_A 95% CI = [0, 0] (discovery; LR_A = 0 in most draws) and [0, 4.0] (validation) — both include "no ratio ≥ 2".

**Why B's alert equals A:** B's alert event is the production second touch (`tested_level(30, 1.5%, 2)`), the same event A requires at admission; holding the name earlier changes *when* the object exists, not *whether* the alert fires. On Faisal's dated rows the second touch occurs on 2/46 and 3/29 rows for both. B's only measurable difference at the alert stage is fewer control flags (10% vs 17–23%), because names that reach the second touch without ever having been identity-eligible on their first touch are excluded.

## 2. Observation stage (B's early "discovery" pool) — reported, not the primary metric
| Set | B observation recall (securities) | rows | control-days observed | LR |
|---|---|---|---|---|
| discovery | 8/22 | 16/46 | 88/88 = 100% | 0.36 |
| validation | 13/16 | 24/29 | 64/64 = 100% | 0.81 |
Observation flags every matched control by construction (the control population *is* the observation population), so the observation stage identifies Faisal's names only in the sense that it holds ≈ 380–410 symbols/day (universe anchor-rule rejections) of which his names are a small fraction. LR < 1 in both sets.

## 3. Lead time (sessions from first identification to Faisal's earliest dated decision; positive = before)
| Set | A (candidate at any day ≤ T within 60) | B observation | B alert |
|---|---|---|---|
| discovery | n 10 · median 42.5 (IQR 33–56) · before: 10/10 | n 8 · median 3.5 (0–8) · before: 5/8 | n 1 · 4 |
| validation | n 14 · median 37.5 (18.5–52.8) · before: 14/14 | n 13 · median 2 (0–6) · before: 9/13 | n 2 · median 1.5 (0–3) · before: 1/2 |
A's long lead is the exploratory "seen earlier then lost" effect (also present in 84–90% of control securities, `PERFORMANCE_BASELINE.md §4`); B's observation typically begins 0–6 sessions before Faisal's Watch/Focus, which matches Phase 4's "his Watch sits on a fresh, untested low" but — per §2 — does not distinguish his names.

## 4. Target C (price outcome), separate from selection
+50% within 20 sessions, flagged objects only (small n; validation mostly right-censored):
| Set | A pos / ctrl | B alert pos / ctrl | B obs pos / ctrl | BASE2 pos / ctrl | all pos / all ctrl |
|---|---|---|---|---|---|
| discovery | 0/0 · 5/15 | 1/1 · 5/9 | 5/8 · 29/88 | 2/5 · 6/22 | 9/22 · 29/88 |
| validation | 0/2 · 3/15 | 0/2 · 3/7 | 3/13 · 21/64 | 2/5 · 4/10 | 4/16 · 21/64 |
No method's flagged Faisal names make the move more often than its flagged controls with any confidence at these sizes (e.g. B-observation 5/8 vs 29/88 in discovery is the largest gap and rests on 8 names; validation is censored). Adverse-move medians and horizon/threshold sensitivity are in `out/perf_results.json` (`ADV*`, `MOVE30/100`, horizons 10/40/60) — none changes the direction above.

## 5. Acceptance rules (preregistered §6) — outcome
| Rule | discovery | validation |
|---|---|---|
| 1 LR_B ≥ 2·LR_A with CI excluding 1 | ✗ (0.44 vs 0; CI [0,0]) | ✗ (1.14 vs 0.53 = 2.15×, but CI [0, 4.0] includes 1) |
| 2 recall gain ≥ +0.10 with CI lower bound > 0 | ✗ (+0.045; CI [0, 0.14]) | ✗ (0.00) |
| 3 B control rate ≤ A | ✓ (10.2% ≤ 17.0%) | ✓ (10.9% ≤ 23.4%) |
| 4 median lead ≥ 1 session before Faisal | ✓ (n = 1) | ✓ (n = 2) |
| 5 robustness (no ambiguous dates / no strong-only securities) | ✓ direction kept | ✗ (no-ambiguous subset: recall 1/9 = 1/9) |
| 6 B beats BASE2 on LR | ✗ (0.44 < 0.91) | ✗ (1.14 < 2.00) |
Result: rules 1, 2 and 6 fail in both sets ⇒ **C. NO DEMONSTRATED IMPROVEMENT**. Evaluable securities 22/16 ≥ 10, so "insufficient evidence" does not apply to the comparison itself.

## 6. The unplanned but material finding
The two-condition screen (BASE2: RSI14 < 33 and ≥ 70% below the 52-week high — Faisal's own stated conditions as the bot already encodes them) has the highest LR in both sets (0.91, 2.00) and flags 5/22 and 5/16 of his securities at his date while flagging 25%/16% of matched controls. It was a preregistered baseline, not a candidate; its LR is still ≤ 2, its recall ≤ 31%, and it was not tested against an untouched set — it is **not** a validated improvement either, only evidence that neither the anchor gate nor B adds discrimination beyond the simplest screen inside this population.
