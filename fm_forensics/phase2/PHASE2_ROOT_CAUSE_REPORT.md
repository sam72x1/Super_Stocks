# PHASE2_ROOT_CAUSE_REPORT — causal root-cause investigation (2026-10-08, main `519f7d3bc`, read-only)

> Phase 1's hypothesis under test: *the bot loses Faisal-focused stocks before READY NOW because of security identity / corporate-action / historical-continuity handling.* This phase tried to disprove it. Artifacts: `fm_forensics/phase2/` (index in `README.md`). Nothing in production, V4, prospective validation, Telegram, thresholds or ranking was modified. No ticker is hard-coded in any logic; anchors appear only as experiment labels.

## A. Method (what was actually done)
1. Code trace of the real pipeline, line-referenced (`IDENTITY_PIPELINE_TRACE.md`).
2. Identity ledger for the anchors and the 232 probe symbols (`SECURITY_IDENTITY_LEDGER.csv`; splits from Yahoo ∪ Nasdaq calendar via the bot's own `_fetch_splits_dq`, fetched by the Phase 1 probe run 37807953508).
3. Controlled replay of the **production** `analyze_ticker` (unmodified) on the probe bars, lookahead-safe (bars ≤ scan date − 1), 232 symbols × 20 scan dates × 6 worlds = 26,769 evaluations (`phase2/replay.py`, `out/replay_all.csv.gz`): A production · ID identity-only · B_PSH/B_M4 continuity-only via the existing backtest flags · B_RAW unadjusted · B_CUT history from the split.
4. The same replay on 70 **independent Faisal-dated decisions** (63 non-anchor) on their decision day (`FAISAL_DATED_REPLAY.csv`).
5. Matched controls (the 10 other symbols hitting the M2 ceiling), negative controls (56 reverse-split symbols the bot accepts), reject-log audit (`REJECT_LOG_FORENSICS.csv`, 76/80 anchor rows reproduced; 3 CRE candidate days; 1 HUBC split-day timing difference).
6. Corpus re-verification: 34 images re-read by eye, status classes for all 772 (`CORPUS_EVIDENCE_STATUS.csv`, `CORPUS_REVERIFICATION_REPORT.md`).
7. State-model and READY NOW target re-tests; Phase 1 numbers recomputed with explicit denominators.

## B. Answers to the 22 required questions
1. **Is security identity a root cause?** NO. The bot has no identity object; the ticker string is the provider key. Same bars under another label reproduce every result bit-for-bit (26,769/26,769). Level 0 effect.
2. **Is corporate-action handling a root cause?** NO as a root cause; a **contributing mechanism** for two anchors: the READY path does no split handling, so cumulative reverse splits inflate the adjusted 52-week high and trip the M2 ceiling (SXTC, HUBC, +10 controls). Correcting it never yields a candidate for any anchor (Level 2 as explanation; Level 5 for the mechanism itself).
3. **Is historical data continuity a root cause?** NO. Bot prices equal provider closes 1:1 on every snapshot for all four anchors; the only continuity "issue" is the provider's correct split adjustment compounding across regimes. B_CUT (treating the post-split history as a new security) fails on depth (MIN_BARS 120).
4. **Is M2 actually causal?** For the *reject code* on SXTC/HUBC, yes (replicated). For *the miss*, no: under every corrected representation the anchors fail the next gate (floor/M4/anchor); on 63 independent Faisal-dated cases the M2 ceiling is the first wall in 2.
5. **Is M2 merely correlated with the failure?** For the generalized miss — yes, correlated through reverse splits (which Faisal selects for) but neither necessary (DKI, 27 anchor-rule cases) nor sufficient (56 split names pass).
6. **Does identity correction alone restore SXTC?** NO (ID = A). Continuity correction: NO (floor/M4; 0 candidate-days).
7. **Does identity correction alone restore DKI?** NO — nothing to correct; all worlds identical; the anchor rule is the wall.
8. **Does identity correction alone restore HUBC technically?** NO (0 candidate-days in all worlds).
9. **Is Faisal evidence for HUBC actually available?** NO dated Faisal text between 2026-04-24 and 2026-10-08; the current thesis is an owner chart card. FAISAL_STATE = UNKNOWN.
10. **FIRST divergence per anchor:** SXTC L2 M2 ceiling (candidate generation) · DKI L5 anchor rule (candidate generation) · HUBC L2 M2 ceiling (technical; Faisal side unknown) · CRE L10 (bot READY while Faisal waits on a validity rule the bot lacks). In no anchor is READY NOW the first failure.
11. **Same divergence in independent controls?** YES for the gate-definition divergence: 63 Faisal-dated cases → candidate 4, anchor rule 27, M3 18, M4 11, ceiling 2, floor 1, depth 1. The M2-ceiling mechanism replicates on 10 controls.
12. **Negative controls that falsify the identity hypothesis?** YES: 56 reverse-split symbols pass M1–M5 under the current representation (296 symbol-days), including 13 Faisal names; CRE passed *because* of the adjusted pre-split high. Identity/continuity problems exist in 135 symbols and the ceiling failure in 12.
13. **Did identity correction change the three-condition tool?** Not through the bot's price regime: the tool's RSI/stability/explosion conditions read consistently adjusted bars and are regime-free (DKI/CRE 0/20 dates differ even under raw prices; SXTC would differ on 11/20 dates *only* if fed unadjusted data, which the tool does not). The only identity-dependent element is the DQ split quarantine (HUBC 10-08: CORPORATE_ACTION_PENDING). Tool untouched.
14. **Is Focus a distinct state?** YES — CONFIRMED and refined: anchored on the split date (TG_1807, TG_1811, TG_1824, X_checklist «تاريخ التقسيم»).
15. **Is Watch a distinct state?** YES (X_13_NUWE, IMG_0689, TG_2185, TG_2191).
16. **Is Ready a distinct state?** YES (TG_2218/TG_2089, TG_1810, X_checklist).
17. **Is Trigger distinct from Ready?** YES — MODIFIED: two forms, hold-with-loading at the first support OR sweep-and-reclaim (X_13_NUWE, IMG_0689, TG_2200 vs TG_57894, TG_57879).
18. **Is READY NOW targeting the wrong variable?** YES: it is a daily price-location classifier on a 15-slot set; Faisal's "ready" is a lifecycle state awaiting an operator event (`READY_NOW_TARGET_REASSESSMENT.md`).
19. **Did corpus re-verification reveal material new evidence?** YES, one modification (no-sweep trigger branch) and one refinement (post-split regime is Faisal's reference frame); no verdict reversal.
20. **Was Phase 1's "no evidence gap" conclusion justified?** PARTLY: the 708 inherited files had earlier eye passes (511) or are duplicates (160); the statement should have said so; 3 files + the owner's 10 chat screenshots remain UNKNOWN.
21. **What remains UNKNOWN?** HUBC Faisal state; DKI's 2025-09-30 −87.7% day; the owner's 10-08 screenshots; whether any Faisal name failed *only* because of the ceiling (none found among 63 dated cases); the display cut's per-symbol visibility for the 231 movers (membership verified, visibility inferred).
22. **What should be investigated NEXT?** A pre-registered definition of the identity gates on the **post-split regime** (reference high = post-split, base/spike/anchor windows started at the split date, depth requirement relaxed for post-split histories) tested on 3 years with matched controls — research only. Not a V2, not a threshold tweak.

## C. Phase 1 claims re-checked
| Claim | Re-check | Status |
|---|---|---|
| "identity before state" | identity has zero effect; the gates' *definitions* (band, spike, range, anchor, depth) are the divergence | **corrected**: it is gate-definition-before-state, with continuity as a symptom carrier |
| "M2 is the heavy discovery" | 2/63 independent cases; 0 restorations | **downgraded** to contributor |
| "708-image corpus sufficiently covered" | 511 previously eye-verified, 160 duplicates, 34 re-read now, 3 unknown | **restated** honestly |
| "READY NOW is the primary failure" | first failures are all at candidate generation (L2/L5) or validity (CRE) | **corrected**: READY NOW is downstream; its target variable is wrong, but it is not where Faisal's names are lost |
| "46% hidden in watch" | (81+26)/231 = 46.3% **in near-watch membership** within 14 days before the move; "hidden" verified for the anchors (shown ranks), inferred for the rest (20-row cut per bucket of 120–300) | **membership reproduced; visibility partly UNKNOWN** |
| "READY NOW 1.1%" | the evaluator's rule was same-calendar-month, not 14 days → withdrawn; the reproducible figure is **2/279 = 0.72%** (READY within 14 calendar days before or on the move date; same strictly-before) | **withdrawn / replaced** |
| "DKI/SXTC/HUBC demonstrate the same failure" | SXTC and HUBC share the ceiling mechanism; DKI does not (anchor rule); HUBC's Faisal side is unknown | **corrected** |

## D. Evidence status matrix (key claims)
| Claim | Source | Evidence type | Direct/Inferred | Supporting | Contradictory | Confidence | Status |
|---|---|---|---|---|---|---|---|
| Identity has no effect on gate results | replay ID vs A | SYNTHETIC_TEST on real bars | direct | 26,769/26,769 identical | none | L5 | established |
| Cumulative splits trip the M2 ceiling | replay A; splits ledger | HISTORICAL_DATA + CODE | direct | 12 symbols, 190 rows | 123 split symbols do not | L5 (mechanism) | established |
| Correcting the regime does not create candidates for the anchors | replay B_* | SYNTHETIC_TEST | direct | 0 candidate-days ×3 worlds ×3 anchors | B_RAW restores 10 rows for PAVS/RUBI/ZNB | L4 | established |
| Faisal's reference frame starts at the split | TG_1807, TG_1811, TG_1813, TG_1824, TG_2200, IMG_0291, TG_1958 | DIRECT_FAISAL_TEXT | direct | 7 images, 6 tickers | none | L4 | established |
| The anchor rule is the main wall on Faisal's dated names | FAISAL_DATED_REPLAY | SYNTHETIC_TEST on real bars | direct | 27/63 | — | L4 | established |
| Trigger has a no-sweep branch | X_13_NUWE, IMG_0689, TG_2200 | DIRECT_FAISAL_TEXT | direct | 3 | TG_57870 «90% سحب» (not contradiction: majority) | L3 | established |
| HUBC is in Faisal's focus now | owner chart card | OWNER | inferred | 1 | no Faisal text | L0 | UNKNOWN |
| DKI/SXTC "major moves" | probe hourly bars | FUTURE_OUTCOME | — | — | — | — | used only for description, never as decision evidence |

## E. Adversarial review — 15 passes
1. Assuming M2 causal? No — tested; downgraded to contributor. 2. Confusing identity with continuity? Separated by ID vs B_* worlds; identity 0, continuity symptom-only. 3. Using future prices? Replays use bars ≤ scan date − 1; Faisal-dated replays use bars ≤ decision day; outcomes appear only in descriptions. 4–6. Fitting DKI/SXTC/HUBC? Every mechanism was re-tested on 10 matched + 56 negative controls + 63 independent Faisal cases; HUBC's Faisal side left UNKNOWN. 7. Negative controls inspected? Yes (56; CRE itself). 8. Matched controls? Yes (10 ceiling symbols; 135 split symbols). 9. Identity correction alone caused the change? There was no change under identity; continuity changes were isolated by flag/representation only. 10. Accidentally changed another variable? Thresholds, filters, windows, ranking untouched; `CONFIG` flags reset per run; verified by the no-split groups being bit-identical across worlds (944 + 920 rows). 11. "Ticker returned" ≠ "Faisal behavior restored"? No ticker returned in any world; the question did not arise. 12. Inherited labels counted as visual? No — status classes separate them. 13. 46% validated? Membership yes; visibility partly UNKNOWN. 14. 1.1% validated? Withdrawn; 0.72% reproducible. 15. Could the real failure still be Focus/Watch/Ready? YES — the generalized divergence is a state/definition mismatch at candidate generation (plus the absent lifecycle), consistent with Phase 1's G/H verdict; identity is not it.

## F. Integrity checklist
V4 untouched ✔ · production untouched ✔ (only `fm_forensics/phase2/` added) · prospective validation untouched ✔ · no Telegram changes ✔ · no thresholds changed (flags set only inside the replay process) ✔ · no DKI/SXTC/HUBC hard-coding in logic (labels only) ✔ · no future leakage ✔ · code traced ✔ · reject_log inspected ✔ · identity/history separated ✔ · identity-only counterfactual ✔ · data-only counterfactual ✔ · matched controls ✔ · negative controls ✔ · corpus status separated ✔ · inherited ≠ visual ✔ · materiality tested ✔ · Phase 1 claims re-checked ✔ · states re-evaluated ✔ · no V2 ✔ · no unsupported root-cause claim ✔ · uncertainty reported ✔.
