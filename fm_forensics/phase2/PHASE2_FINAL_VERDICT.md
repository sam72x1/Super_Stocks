# PHASE2_FINAL_VERDICT (2026-10-08)

**"THE FIRST CAUSALLY SUPPORTED FAILURE IS the candidate-generation layer (Layer C): the identity gates — the M2 drop band, the M3 prior-spike floor, the M4 base range and the two-touch anchor rule, all evaluated on the provider-adjusted price regime over bot-defined windows — reject Faisal-focused stocks before any state exists; security identity is not a cause, corporate-action adjustment is only the carrier of one symptom (the M2 ceiling), and READY NOW is downstream of the loss."**

## Evidence chain
1. Identity has no effect: same bars under another ticker reproduce all 26,769 gate results (`out/replay_all.csv.gz`, ID = A).
2. The M2 ceiling on SXTC/HUBC is a cumulative-adjustment artifact (4 and 6 reverse splits → adjusted hi52 83,758 / 742,500+), replicated on 10 controls — but removing it (post-split reference, raw prices, or post-split history) produces 0 candidate-days for any anchor; the next gate (M2 floor, M4, anchor) takes over (`IDENTITY_COUNTERFACTUAL_RESULTS.csv`, `MATCHED_CONTROL_RESULTS.csv`).
3. Identity/continuity issues are not sufficient: 56 reverse-split symbols pass the same gates today, and CRE passed because of the inflated pre-split high (`NEGATIVE_CONTROL_RESULTS.csv`).
4. DKI has no split at all and is rejected by the two-touch anchor rule for three weeks while Faisal is in WAIT — the same wall stops 27 of 63 independent Faisal-dated decisions; M3 stops 18, M4 11, the M2 ceiling 2 (`FAISAL_DATED_REPLAY.csv`, `FIRST_DIVERGENCE_MATRIX.csv`).
5. Faisal's own reference frame starts at the split (first post-split open/high ÷2, MA30 from the split date — TG_1807, TG_1811, TG_1813, TG_1824, TG_2200), and his readiness is a lifecycle state with an operator trigger (hold-with-loading or sweep-and-reclaim — X_13_NUWE, IMG_0689, TG_57894). None of these objects exist in the bot's candidate generation.
6. Therefore the first divergence is always upstream of READY NOW (L2/L5 for the anchors; L10 for CRE where the bot is early on a validity rule it lacks). READY NOW's target variable is wrong (`READY_NOW_TARGET_REASSESSMENT.md`), but it is not where the names are lost.

## Decision-tree outcome (§36)
Identity correction does nothing → **REJECT IDENTITY AS PRIMARY EXPLANATION**. Corpus re-verification modified one transition (trigger) and refined Focus → **PHASE 1 STATE MODEL = REVISE (minor)**. The generalized failure (gate definitions vs Faisal's post-split lifecycle frame) is replicated on independent cases → **Level 4**; it is not Level 5 because no controlled correction of the gate definitions has been run yet (that is the next, pre-registered, research-only step).

## What is still UNKNOWN
HUBC's Faisal state · DKI's 2025-09-30 event · the owner's 10 chat screenshots · per-symbol display visibility for the 231 movers · whether a post-split-regime gate definition would admit Faisal's names without admitting noise (untested).
