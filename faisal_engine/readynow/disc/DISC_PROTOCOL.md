# READY NOW historical discovery — the single 2026 check (written before any 2026 number of these candidates)

Sealed by its SHA-256, pinned in `rn_disc_cand.py` and `rn_disc_model.py`; their `final` modes refuse (exit 9) on any
other content. Committed and pushed before the first `final` run. Research only: no production file, rule, Telegram
message or candidate membership changes.

## ① What is checked
- **Target** (`rn_disc_build.py`, unchanged): a clean episode of the bot's explosion detector whose corrected onset —
  the start of the final +70% leg — falls 7 to 10 sessions after the decision day (POS710). Onset, the +70% close
  (Q) and the detector's first detection (D1) are kept apart. Rows inside a move are IN_EVENT and never scored.
- **Rows**: READYNOW's pivot-days (M1–M3 identity from bars ≤ t), seeds (DLXY, RETO, DKI, SXTC) and HUBC excluded.
- **Windows**: validation 2026-01-16 → 05-15 and holdout 2026-06-02 → 08-27 (`rn_lib.WINDOWS`), each read once by
  `rn_disc_cand.py final` and `rn_disc_model.py final`.
- **Status of these windows: not pristine.** READYNOW read them for RN_A against its trough onset, READY70 and SEQ70
  for other rules and targets. Nothing in this study's development read them. Every result below is therefore labelled
  **exploratory (previously inspected windows)**, never «validated».

## ② Candidates (formulas in `rn_disc_cand.py`; thresholds fixed; nothing is refitted on 2026)
| name | formula (bars ≤ T) | origin |
|---|---|---|
| BURST_UP | v1x(T) ≥ 5 ∧ r5(T) ≥ 0 | seed bursts with a rising close 7–10 sessions before the leg (DLXY 2026-09-01, RETO 2026-02-13) |
| BURST_UP_3 | max v1x(T−2..T) ≥ 5 ∧ r5(T) ≥ 0 | same, 3-session lookback |
| BURST_ANY_3 | max v1x(T−2..T) ≥ 5 | the burst alone |
| PATH2 | REF_UNION ∨ BURST_UP_3 | the existing rules plus the burst path |
| CAPIT_TC | per session, the k pivot-days with the highest p_range20 + (1 − p_r5); k = TC_TECH's flags that session | profile of the captured group A in development |
| TC_OR_CAPIT | TC_TECH ∨ CAPIT_TC | two paths; development showed almost disjoint event sets |
| M_MAIN · M_INT | ridge logistic models trained on the whole development window (`rn_disc_model.py`) | ceiling of all point-in-time daily features (and pairwise products) |

v1x = volume / median volume of sessions j−60..j−11 (SEQ70). 5 = `VOL_SPIKE_MULT` (production constant). p_ = mid-rank
percentile among the session's pivot-days. TC_TECH = RSI < 33 ∧ hold 5 ∧ no boom (the three-condition tool's technical
part). REF_UNION = TC_TECH ∨ RN_A ∨ H_S70 ∨ STAGE1 ∨ LOC.

## ③ Decision rules (95% intervals; ticker-cluster bootstrap, 2,000 replicates for the candidates and 1,000 for the
AUC ceiling, seed 20261011)
**(a) Burst path.** A burst candidate «adds» only if, in **both** windows: lift CI lower bound > 1, matched ratio CI lower
bound > 1, and its flags outside REF_UNION have a Wilson lower bound above the base rate of the rows REF_UNION does not
flag. Otherwise «BURST_NOT_SUPPORTED».

**(b) CAPIT_TC — the primary candidate.**
- A1: lift CI lower bound > 1 in both windows.
- A2: CAPIT_TC minus TC_TECH precision (percentage points, same per-session burden), pooled over both windows: CI lower
  bound > 0, with a positive point estimate in each window.
- A3: CAPIT_TC minus the DROP_k and minus the VOLAT_k rankings at the same burden, pooled: both CI lower bounds > 0.
- Verdict: **IMPROVES_ON_TOOL_BEYOND_GENERIC** if A1 ∧ A2 ∧ A3 · **IMPROVES_ON_TOOL_EQUAL_TO_GENERIC** if A1 ∧ A2 ∧ ¬A3 ·
  **NO_DEMONSTRATED_IMPROVEMENT** otherwise.

**(c) TC_OR_CAPIT — the two-path rule.** «TWO_PATHS_SUPPORTED» if, in both windows, lift and matched-ratio CI lower
bounds are > 1; «BEATS_GENERIC» in addition if its differences against VOLAT_k, DROP_k and LOWRSI_k at the same burden
are positive point estimates in both windows. Otherwise «TWO_PATHS_NOT_SUPPORTED».

**(d) Ceiling.** «DAILY_FEATURES_BEYOND_VOLATILITY» if M_MAIN or M_INT minus the volatility ranking (AUC) has a CI lower
bound > 0 in both windows, on all rows; otherwise «NO_INFORMATION_BEYOND_VOLATILITY».

No threshold, window, candidate or rule above may change after the first `final` run. A failed criterion is reported as
failed; the report shows every number either way.

## ④ Predictions (published whatever happens)
- Q1 every burst candidate is «BURST_NOT_SUPPORTED».
- Q2 CAPIT_TC passes A1.
- Q3 CAPIT_TC fails A2 (the pooled difference against the tool's technical part includes 0).
- Q4 CAPIT_TC fails A3 against DROP_k (pooled difference includes 0).
- Q5 the ceiling is «NO_INFORMATION_BEYOND_VOLATILITY».
- Q6 TC_OR_CAPIT captures at least 1.5 × TC_TECH's events in each window.

## ⑤ What these results cannot show
Float, available-to-borrow, intraday or pre-market timing and the app's own chip states are not in the daily bars and
are untestable here. The pivot population covers about a third to a half of the events 7–10 sessions ahead. The seeds
and HUBC are anecdotes and enter no statistic. Development informed the choice of CAPIT_TC and TC_OR_CAPIT.
