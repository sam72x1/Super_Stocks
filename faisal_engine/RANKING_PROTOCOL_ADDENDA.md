# 🧭🏁 RANKING_PROTOCOL — dated addenda (the contract file itself is frozen by hash)

## Addendum 1 — 2026-10-09 · Iteration 2 diagnosis → Iteration 3 post-hoc correction D1 (written and committed before D1 is run)

**Iteration 1 result (preregistered A/B/C, run `37942829821`):** preferred variant C; exact-date episode capture at K = 108: C 6/22, A 4/22,
B 4/22, operational bot 2/22; C − bot = +0.182 with 98.33 % cluster-bootstrap interval [0.000, 0.409] ⇒ criterion B fails ⇒ verdict 2.
Predictions P1–P6 all held. Reconstruction fidelity: F1 0.037 · F2 recall 0.957 · F3 1.043 ⇒ operational baseline "reproduced".

**Iteration 2 — dominant failure, DISCOVERY fold (13 evaluable episodes, C misses 10):**
1. Candidate generation (6): AMIX M4_RANGE · LABT too few bars · PPBT RSI_NOW · STKH M4_RANGE · SXTC M2_CEIL · YMT M3 — five different
   frozen gates. Three (STKH, SXTC, YMT) share one mechanism: a reverse split fewer than 40 sessions before T, so the post-split frame is
   not evaluated (FE-FRAME-01 / V4 R4-DATA-01 need ≥ 40 bars) and the split-adjusted full frame fails. **Not correctable with existing
   evidence:** the 40-bar floor is V4's own data rule (frozen), and Phase 2 already showed that correcting the M2 cap on adjusted data
   creates no anchor nomination while admitting 33 of 56 negative controls.
2. Candidate ranking (4): DKI, NUWE (FOCUS, below the stage cut-off), CUPR, SVRE (WATCH, persistent, bottoms set in July/June; both
   come from Faisal's app watch-list screenshot).
3. Temporal handling (category 4, inside 2): all 7 in-pool discovery cases are PERSISTENT by stage-entry age, so C's freshness signal did
   not separate them. Both discovery FOCUS misses have the V4 structural bottom on the last bar before T (a new low one session earlier)
   while their stage had been unchanged for 7 sessions: C measured freshness by stage transitions and placed it **under** stage priority,
   so a newly formed base never outranked a stale READY.

**Disclosure:** the iteration-2 diagnostic printout listed validation-fold episodes next to discovery ones. D1 is therefore fully
POST-HOC; per §⑩ it **cannot carry verdict 1** whatever its numbers.

**D1 (one change, label-free, no weight):** first-touch class before stage —
key_D1 = (first-touch class, stage priority, C's temporal class, sessions in stage, B's evidence keys, tie-break), where first-touch
class = 0 when the engine's V4 structural bottom (`bottom_date`, computed from bars < T) lies within the last 5 sessions before T
(0–4 sessions after the bottom bar; same 5-session constant as C and the early window), else 1 (missing bottom ⇒ 1, flagged).
Source of direction: the task's §7 rule (a stale signal must not outrank a newly formed setup) and the Phase 3/4 finding that Faisal's
attention starts at the first touch of an untested base (same corpus — contamination disclosed). A/B/C are unchanged.

**Acceptance test (fixed now):** (i) targeted — at least one of DKI_E1 / NUWE_E1 enters the top 108 on its decision date; (ii) full
evaluation — DISCOVERY-fold exact capture at 108 for D1 ≥ C's 3/13; (iii) every gained and lost case is listed in both folds; (iv) the
same dates, universes, budgets and labels as iteration 1.

**Predictions:** D-P1 — D1 loses at least one READY case that C captured (persistent READY with an old bottom falls behind ~146
first-touch members/day). D-P2 — D1's exact capture at 108 on the full set lies between 5 and 9. D-P3 — D1 does not change any
generation failure (6 discovery + 1 validation REJECTED stay uncaptured).
