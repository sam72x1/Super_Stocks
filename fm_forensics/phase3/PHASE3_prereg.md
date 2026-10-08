# PHASE 3 — PRE-REGISTRATION (written before any Phase 3 number · 2026-10-08)

Mission: «FORENSIC PHASE 3 — TEMPORAL SELECTION RECONSTRUCTION». Research only. No production, V4, protocol, Telegram, three-condition, threshold or ranking change. No V2/V5. No anchor hard-coding. Lookahead firewall: for every decision date T only bars with date < T (the morning scan sees the previous close) and only evidence dated ≤ T.

## ① Hypotheses and what falsifies each (fixed now)
| H | Claim | Falsified if |
|---|---|---|
| H1 | gates ≈ right, some mis-tuned | leave-one-gate-out (LOGO) on the Faisal-dated set restores ≥50% of Faisal cases for ONE gate while negative controls' PASS rate rises < 2× |
| H2 | a Faisal concept is missing | H1 fails AND a recurring Faisal feature (≥3 independent dated cases, DIRECT) has no bot representation AND its presence separates positive from negative controls |
| H3 | wrong abstraction: temporal vs snapshot | persistent-memory counterfactual (gates unchanged, candidate memory N sessions) reduces first-divergence on Faisal cases by ≥50% AND Faisal attention is persistent (median consecutive-appearance ≥ 2 sessions on multi-dated tickers) |
| H4 | external information | Faisal FOCUS dates precede any price/volume distinguishability by ≥5 sessions in ≥50% of adequately dated cases with no identifiable OHLCV feature |
| H5 | artifact of evidence/dates | dated cases with day precision < 20, or lead-time distribution changes sign when ambiguous-date rows are dropped |
| H6 | H2+H3 | both H2 and H3 survive and neither alone restores ≥50% |

Decision rule: a hypothesis «survives» only if its falsifier does not fire AND it is replicated on the independent sample (not the anchors). Otherwise «NOT PROVEN». No hypothesis is preferred a priori.

## ② Outcome labels (EVALUATION ONLY — never discovery rules)
Move labels, computed from bars strictly after the decision date T (future reveal only after the historical fields are frozen):
- MOVE_25_k, MOVE_50_k, MOVE_100_k for k ∈ {5, 10, 15, 20} sessions: max High in the k sessions after T ≥ close(T−1) × (1+p).
- VOL_ADJ_k: max High after T ≥ close(T−1) × (1 + 3·ATR14(T−1)/close(T−1)) — volatility-adjusted.
- «Major move» for lead-time = first session after T where MOVE_50_20 is first satisfied (primary); MOVE_100_20 and MOVE_25_10 reported as sensitivity.
Denominators always printed. Lead-time test grid: T−1, −2, −3, −4, −5, −6, −7, −8, −9, −10, −15, −20 sessions (no optimisation for 7).

## ③ Faisal-side states (classification before any bot comparison)
Observation classes: MENTION · SCREENING · FOCUS · WATCH · READY · ENTRY · EXIT · UNKNOWN. Source: dated units only (day precision), from `FAISAL_FOCUS_TIMELINE.csv` DECISION + eye notes + V4 `cases_v4.json` labels (statement_date, day precision). Mapping fixed: READY→READY · WAIT→WATCH · WATCH→WATCH · FOCUS_LIST→FOCUS · OPEN_POSITION/TARGET→ENTRY · REJECT→EXIT(rejected) · PLAN→WATCH · UNKNOWN/MULTI/NONE→UNKNOWN or MENTION. No state is inferred from later price. HUBC: UNKNOWN wherever no dated Faisal text exists.

## ④ Bot-side states (from history, lookahead-safe)
- CANDIDATE(T): production `analyze_ticker` replay on bars < T (world A, unmodified code). PASS = candidate.
- WATCHLIST(T): symbol active in `weekly_watchlist.json` at the commit of day T (git history).
- NEAR_WATCH(T): symbol in `near_watch.json` inside/oversold at day T (git history; from 2026-08-16).
- READY(T): `entry_status(s)=="ready_now"` at the commit of day T.
- ENTRY: none (the bot has no transaction state).

## ⑤ Samples (fixed before results)
- Anchors: DKI, SXTC, HUBC (+CRE as negative anchor). Never used to set rules.
- Independent Faisal set: all tickers with ≥1 day-precision dated Faisal decision in the corpus AND probe bars (expected ≈56 tickers / ≈118 rows); anchors excluded from replication counts.
- Positive temporal controls: Faisal-dated tickers whose state reached READY or ENTRY (any date) — list taken from the corpus labels only.
- Negative temporal controls: Phase 2 `groups.json["neg"]` (56 reverse-split names that pass M1–M5 today) ∖ Faisal-positive, plus bot READY days from `ready_days.json` for tickers with no Faisal evidence at all. Selected before any temporal number.
- Matched controls: Phase 2 `groups.json["m2hi"]`.

## ⑥ Measures
- First divergence per ticker-day: first date Faisal has a state (≥FOCUS) while bot has no CANDIDATE/WATCHLIST/NEAR_WATCH representation; then first candidate rejection code; first structural mismatch (gate); first readiness mismatch; first entry mismatch.
- LOGO: for each gate in {M1, M2_ceiling, M2_floor, M3, M4_range, M4_rise, M5, SOFT_FAILS, SCORE, ANCHOR(two-touch), RSI_OS, RSI_NOW} run CURRENT · GATE_REMOVED (neutral threshold) on: Faisal-dated set, anchors, negative controls, matched controls. Report candidate-days and PASS rows per group; «restores» = Faisal row turns PASS.
- Persistence: consecutive dated appearances per ticker (Faisal) vs consecutive CANDIDATE days and consecutive READY days (bot) — medians/IQR.
- Architecture B counterfactual: candidate memory of N ∈ {1,3,5,10,15} sessions over world-A PASS; first divergence recomputed; false positives = negative-control days admitted.
- Feature counterfactual: Faisal features (post-split frame, split date, held level, sweep, gap-below, RSI<33, float, available) computed at T−1 from bars/splits only; test whether any separates positive from negative controls (Fisher/odds, n printed).

## ⑦ Predictions (to be scored)
P1 Faisal median lead-time to MOVE_50_20 is NOT concentrated at 7 sessions (IQR width > 5). P2 ID/continuity worlds unchanged from Phase 2. P3 LOGO: no single gate restores ≥50% of Faisal rows without raising negative-control PASS ≥2×. P4 Persistence: Faisal multi-dated tickers show ≥2 consecutive observations in ≥50% of cases; bot CANDIDATE persistence median ≤ 3 days. P5 Persistent memory alone (N=10) reduces first divergence by <50%. Any failed prediction is published.
