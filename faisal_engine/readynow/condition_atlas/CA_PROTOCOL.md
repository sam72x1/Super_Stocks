# Faisal condition atlas — the sealed 2026 check (protocol)

Written 2026-10-11 22:30 UTC, after the development analysis (2025-05-01 → 12-31) and **before any 2026 number of
this study was computed**. `ca_final.py` refuses to score unless this file and `data/model_frozen.json` match the
SHA-256 values pinned in it.

**Disclosure.** (1) The 2026 windows were read by the earlier READY NOW studies (READYNOW, SEQ70, READY_DISCOVERY), so
this check is **exploratory, not an independent validation**. (2) The seal is local: the owner did not authorise a
commit or push, so this protocol was not pushed before the run. Its hash is pinned in the scorer and the run time is
recorded in `data/final.json`. (3) The atlas conditions were declared in `ca_atlas.py` / `ca_lib.py` before any
development rate was computed. The penalty grid was widened once in development, because the first run chose its
edge; that change is recorded in `ca_dev.py`.

## ① What is frozen

| item | file | SHA-256 |
|---|---|---|
| feature build | `ca_build.py` | `8ce2db9cab641209fe0836f550572e6e93d9e73feb2d2f3c306b2711f93b552b` |
| condition flags, classifiers, rankings | `ca_lib.py` | `8053c9078a6486d766733728e51dd0c0164b418827a55daefb3786164ff67640` |
| development analysis, classes | `ca_dev.py` | `ce7d02297b35d6208f2e7a23dde3d4d923a2c9355d718509dc13829ceb671ce2` |
| atlas | `ca_atlas.py` | `a188464a1f1f1ae664e77b52bf3d80c005390a3183d9c984335e23fcb0b88b3b` |
| frozen axis models | `data/model_frozen.json` | `482b9d580c3cccaf5aace7c06deab312356f4b10baa73f46054ada94e4d2d849` |
| features (all windows) | `data/ca_rows.csv.gz` | `423937f24c59478d9223c68861dd8e44732344d567dc7f9c2c6fb2e4587147df` |
| development results | `data/strength_dev.json` · `data/model_dev.json` | `887c1b2e…0c581` · `de54d390…14414` |

Windows: validation 2026-01-16 → 05-15, holdout 2026-06-02 → 08-27 (`rn_lib.WINDOWS`). Target: POS710 = a clean
corrected onset (start of the final +70% leg) 7–10 sessions after T. Population: the READY NOW pivot-days; seeds and
HUBC are excluded.

## ② The classifier

- **Axes** (ridge logistic regressions on the binary atlas flags, fitted on the whole development window and frozen):
  A = validity (9 flags, λ 100) · B = technical state and candles (λ 1000) · C = every flag, including invalidation
  and timing (λ 10000). Each λ was chosen by the development test-half AUC (train 2025-05 → 09, test 10 → 12).
- **Invalidation** (Faisal's explicit «no entry» states, `ca_lib.INVALID`): chasing (dist > 40% or 5-session
  return > 30%), exploded within 5 sessions, and a daily group-candle proxy in the last 10 sessions.
- **Classes per session** (k = the number of pivot-days the tool's technical part flags that session): the
  non-invalidated pivot-days ranked by C → READY_1 the top k · READY_2 the next k · READY_3 the next 2k · the rest
  WATCH when B ≥ the session median, else NOT_READY · invalidated → INVALIDATED. Missing auxiliary conditions simply
  contribute 0; nothing is required except not being invalidated.
- **Per-stock output:** each flag's state, the three axis scores, the top contributors and blockers (positive and
  negative coefficient × flag), and a confidence note (float, borrow, offering, groups and operator are always
  UNKNOWN for history).

## ③ Comparisons (all at the tool's per-session burden k)

TC_TECH (the tool's reconstructible technical part) · CAPIT_TC (READY_DISCOVERY's sealed ranking) · DROP_k
(5-session decline) · VOLAT_k (20-session range) · VOL_k (volume ratio) · COUNT_k (number of Faisal's 11 counted daily
conditions satisfied) · APPW_k (the app's weighted score TG_58420, daily proxies) · W_k (READY_1 of the classifier) ·
W_k_noinval (the same without the invalidation filter) · B_k and A_k (single axes). Metrics: flags per session,
precision, false-positive rate, lift vs the window base (ticker-cluster CI), events captured and recall, differences
in percentage points with ticker-cluster CIs (2,000 resamples, seed 20261011), pooled over the two windows. Per-class
precision and the events touched. Every atlas flag's 2026 lift (descriptive).

## ④ Decision rules (applied mechanically by `ca_verdict.py`)

- **V1 — beats the tool:** W_k − TC_TECH pooled CI lower bound > 0 and the difference positive in each window.
- **V2 — beyond generic price/volatility:** W_k − DROP_k and W_k − VOLAT_k pooled lower bounds both > 0.
- **V3 — beyond the earlier discovery:** W_k − CAPIT_TC pooled lower bound > 0.
- **V4 — weights beat counting:** W_k − COUNT_k pooled lower bound > 0.
- **V5 — graded classes:** precision READY_1 ≥ READY_2 ≥ READY_3 ≥ WATCH ≥ NOT_READY in both windows, and W_k's lift
  lower bound > 1 in both windows.
- **Verdict:** IMPROVES_BEYOND_GENERIC if V1 ∧ V2 ∧ V3 · IMPROVES_ON_TOOL_EQUAL_TO_GENERIC if V1 only · otherwise
  NO_DEMONSTRATED_IMPROVEMENT. Classification GRADED if V5, else NOT_GRADED.

## ⑤ Predictions (written before the run; any that fail are reported, not removed)

From the development test half (W_k 2.77% vs TC_TECH 4.00%, CAPIT_TC 6.28%, DROP_k 5.54%, VOLAT_k 4.35%; classes not
monotone; INVALIDATED 3.05% above WATCH 2.38%):
- **Q1** V1 fails (W_k does not beat the tool).
- **Q2** V2 fails.
- **Q3** V3 fails.
- **Q4** V5 fails (classes not graded).
- **Q5** COUNT_k and APPW_k do not beat TC_TECH (pooled CI includes 0 or lies below it).
- **Q6** RSI < 33 (B01b) has a lift point estimate above 1 in both 2026 windows.
- **Q7** No candle flag (K*) has a lift lower bound above 1 in both 2026 windows.
- **Q8** The group-candle proxy I04 has a lift point estimate at or above 1 in both windows (Faisal's invalidation
  does not lower the odds of the onset).

## ⑥ Hypotheses counted

Development: 66 condition flags, 6 classifier variants and 4 SEC-subset flags = 76. 2026: one primary ranking (W_k)
judged by V1–V5, eight predictions, and descriptive lifts for the 66 flags (no claim rests on a single descriptive
lift).
