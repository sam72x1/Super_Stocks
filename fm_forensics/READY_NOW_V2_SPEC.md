# READY_NOW_V2_SPEC — shadow candidate (isolated · not production · not V4) (2026-10-08)

## Why a V2 is justified (evidence, not preference)
1. The core divergence is a *state model* mismatch (`PIPELINE_FAILURE_FORENSICS.md` §4), not a threshold; a threshold change cannot express persistence, stages, or a trigger.
2. 73/279 ≥100% movers and DKI (3 weeks) were blocked only at the two-touch anchor — i.e., in Faisal's WATCH stage. 46% of movers were already inside the bot's own near-watch state and invisible.
3. SXTC and HUBC are excluded permanently by the post-split M2 reference; a split-restart is already implemented elsewhere (`split_hunter._post_split_high`) but not in the READY path.
4. Five direct images (3 tickers) put the entry after a sweep+reclaim trigger; the current flag has no trigger.
Counter-evidence acknowledged: V4 (frozen) encodes most of these stages and showed no advantage over "always WAIT" on 7 golden cases and 1 prospective case; T-WAIT/T-RSI axes closed with no tradable edge. V2 therefore targets **detection of focus/ready** (recall/lead time), not profit — its success criterion is defined in `READY_NOW_V2_prereg.md`.

## State model
UNSEEN → IDENTITY → FOCUS → WATCH → READY → TRIGGER → (ENTERED is out of scope) ; INVALIDATED → FOCUS (restart). Persistence until transition.

## Inputs
Daily OHLCV (split-adjusted) with the reverse-split dates; RSI14; nothing else. Borrow availability, float, groups, offerings: **UNKNOWN by design** in the shadow (they are validity filters in Faisal's second screen and would be applied as display tags, not states).

## Feature definitions (each with source · rationale · counterexample status)
| Feature | Definition | Source | Counterexample status |
|---|---|---|---|
| split_restart | if a reverse split falls inside the 52w window, the M2 reference high is the post-split high | IMG_0151/0153, split hunter code | none for pivot stocks; momentum names unaffected |
| base_low L | min low of last 30 bars | tested_level (current) | V3.1 C1: Faisal's support sometimes sits above the tail (handled: zone, not point) |
| hold_n | sessions since L without a lower low | IMG_0151 (3), X_85 (5) | WA_31 SXTC READY on the pressure day (trigger beats hold) |
| rsi_min_base | min RSI14 since L | TG_2043 (23–27), live 33 | CRE focus at 45–55 (focus ≠ ready → RSI applies to WATCH/READY only) |
| zone | [L, 1.15·L] | IMG_0531 (5–15%) | ERNA orders 35% above an old low (different reference low) |
| test_bounce | high ≥ 1.10·L then close back inside zone | IMG_0486, TG_50584 (20% typical) | X_85: «يصعد مباشرة … نادر» |
| sweep_reclaim | low < L·(1−s), s ≤ 0.13, close > L within 2 sessions | TG_50584, IMG_0297, TG_57870, TG_57894 | IMG_0153 split recipe (−27%); stop placement conflict (C-STOP-VS-SWEEP) |
| invalidation | close < 0.87·L and no reclaim | X_20260905_10/07 | ENPH/ELAB deeper breaks then rallies (TG_2017/2127) |

## Transition logic
As in the prereg. Deterministic; one evaluation per session close; no look-ahead (features use bars ≤ t).

## Confidence per emitted state
Each state carries the count of supporting images for the rule that produced it (from the evidence matrix) and the count of counterexamples; a state produced by a rule with counterexamples ≥ supporting images is emitted with confidence LOW.

## Missing-data handling
< 40 bars → UNKNOWN; split date unknown → split_restart not applied and the symbol tagged SPLIT_UNVERIFIED; RSI unavailable → WATCH/READY impossible (stays FOCUS).

## Explainability
Every state line lists: L, hold_n, rsi_min_base, zone bounds, last sweep depth, the rule IDs fired.

## Rejection conditions (for the candidate itself)
Rejected if: it only explains the anchors; HOLDOUT advantage absent; VAL lead time negative in median; or any adversarial review (below) finds future information or a tuned threshold.

## Ten adversarial reviews — the 20 questions (recorded before any number)
Lenses: 1 anchor-fitting, 2 state confusion, 3 temporal leakage, 4 negative evidence, 5 single-image rules, 6 visualization artifacts, 7 code-correctness assumptions, 8 thresholds, 9 volume/conversation/attention/maturity omissions, 10 generalization.
| Q | Review result |
|---|---|
| 1–3 Fitting DKI/SXTC/HUBC? | Anchors are excluded from every score (prereg). Rules are cited to ≥ 2 non-anchor images each (matrix) except split_restart whose non-anchor witnesses are the split-hunter corpus (IMG_0151/0153, CCHH, OMH, CIIT). Residual risk: the *choice* of which rules to combine was made after seeing the anchors — mitigated only by HOLDOUT. |
| 4 Fitting CRE? | CRE is a counter-case (bot early); V2 would still mark CRE READY on the sweep because gap-below is not modelled → V2 does not "fix" CRE. Recorded. |
| 5 Focus vs Ready? | Separated explicitly: FOCUS (identity + one touch) vs READY (zone + hold/bounce + RSI). |
| 6 Ready vs Trigger? | TRIGGER = sweep+reclaim only; READY never implies entry. |
| 7 Future information? | Features use bars ≤ t; split dates are known on their effective date; Faisal labels enter only in scoring. Risk: inventory dates like «2026-09-2x» are ranges → such rows are excluded from lead-time metrics. |
| 8 Negative evidence ignored? | Logged per rule in the matrix (X_85 «rare direct rise», TG_1985, WA_31 same-day READY, ENPH/ELAB deep breaks). The hold requirement will miss same-day-pressure entries like SXTC 09-10 — accepted and measured. |
| 9 One image? | No rule rests on one image; weakest is gap-below (2) which is NOT in V2. |
| 10 Visualization artifact? | Chart colours (blue/black) are display conventions, not rules in V2; the 4h-vs-daily low difference (Polygon UTC offset) is excluded by using daily bars only. |
| 11 Current code assumed correct? | No: M2 reference and two-touch anchor are treated as hypotheses; `tested_level` is reused only as the L definition. |
| 12 Arbitrary thresholds? | 3/5 sessions, 15% zone, 5–13% sweep, 33 RSI, 0.87 invalidation (= 1 − 0.13) are all Faisal-stated or ledger-tagged; 30-bar window and 2-session reclaim are engineering and flagged as such. |
| 13 Volume ignored? | Yes, deliberately: the corpus gives no numeric volume rule; "prior concentrated liquidity" is listed as a future FOCUS feature requiring its own prereg. |
| 14 Conversations ignored? | Conversation evidence (X_61_VEEE, TG_57894, TG_58417) was used for the trigger and the volume stance; owner's unreadable chat images remain UNKNOWN. |
| 15 Repeated attention ignored? | Persistence (no daily re-admission) is the model's core; attention counts across images are not a feature (would leak Faisal). |
| 16 Maturity ignored? | hold_n and test_bounce are the maturity proxies; MA 20/30/50 ladder is NOT included (T-MA-LADDER found n collapses to 50; third-party source). |
| 17 RSI > 40 assumed hard? | No; RSI ≤ 33 is a WATCH/READY condition, RSI > 40 is simply "not ready" per TG_2043. |
| 18 Gap-down fixed meaning? | Not modelled (2 images, T-GAPBELOW under floor). |
| 19 Three-condition tool as proxy? | It is a comparator, not an input. |
| 20 Survives unseen examples? | UNKNOWN until HOLDOUT runs (bars probe pending). This is the only honest answer. |

## Status
RUN on 2026-10-08 (`fm_shadow_v2.py` on `data/bars_2026-10-08.json.gz`). **Prereg branch 2 — no advantage** (HOLDOUT WATCH+ 30.2% vs control 25.1%, overlapping Wilson intervals; VAL READY 0/5 ⇒ UNKNOWN). Predictions: P1 ✓ · P2 ✗ (kept) · P3 ✓ · P4 ✓. Adversarial Q20 answered: the rule set did NOT survive unseen examples as a detector. Identity finding: `split_restart` + the M2 band contradict each other on post-split bases (SXTC/CRE REJECT_M2_LO; 46/57 Faisal WAIT rows). The candidate is not accepted. Nothing is promoted.
