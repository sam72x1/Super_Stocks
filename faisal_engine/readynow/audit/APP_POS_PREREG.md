# APP_POS — the app's two reproducible conditions at 7–10 sessions (sealed before any number of this rule is read)

Origin: the READY NOW forensic audit (`RN_AUDIT.md` §1, §4, §6). Of the app's eight automatic technical conditions only
two are reproducible from local daily bars with demonstrated state parity against the app's own screenshots
(`audit/data/chip_parity.json`: within 15% of the support 9 of 9 snapshots, bounce 10–40% 8 of 8; the stability,
retest, below-EMA and momentum proxies disagree with the app on 5 of 7, 6 of 9, 3 of 9 and 1 of 7 snapshots; two
conditions are unnamed). These two were evaluated only in development and only one at a time (RN `data/dev.json`);
together they were never evaluated, and neither was evaluated out of sample on its own (the bounce band only inside
RN_A, together with RSI below 30). READYNOW's «APP3» added a stability proxy
that the audit shows is not the app's condition. This file fixes the one missing evaluation. Research only; no
production, Telegram, schedule, threshold, membership or frozen-axis change; no network request; no agents.

## 1. Rule
**APP_POS(t) = NEAR15 ∧ BOUNCE10_40** exactly as in `rn_lib.COND` (unchanged since the READYNOW seal `217ba85e2`):
the close at t at most 15% above the lowest daily low of the last 25 sessions, and the highest high from the first
day of that low through t between 10% and 40% above it (both computed from bars ≤ t by `rn_build.conditions`).
Known approximation (from the audit, not adjustable): the app's base window is unknown (25 sessions reproduces the
app's support on 8 of 9 snapshots; LIMN differs), and the app measures distance from its last price, not the close.

## 2. Data, population, labels, windows, controls — identical to `RN_SPEC.md` §3–§4
`faisal_engine/readynow/data/rows.csv.gz` as committed in `318511160`; pivot-days only; seeds and HUBC removed;
POS710 (clean onset L in [t+7, t+10]) vs NEG, other labels excluded; validation 2026-01-16 → 05-15 and holdout
2026-06-02 → 08-27; matched controls (same session, same price bucket, `v1x`/`range20`/`dv20` percentiles within 0.10,
no reuse); equal-burden VOL_k and VOLAT_k; «beyond the tool» = rows APP_POS flags and TC_TECH does not, matched to
controls also outside TC_TECH. Ticker-cluster bootstrap, 2,000 resamples, seed 20261011.

## 3. Decision (identical to `RN_SPEC.md` §7, applied to APP_POS)
Per window, 97.5% CIs: **C1** matched ratio lower bound > 1 · **C2** precision minus VOL_k and minus VOLAT_k, both
lower bounds > 0 · **C3** beyond-the-tool matched ratio lower bound > 1 · floors ≥ 20 eligible events, ≥ 300 C1 pairs,
≥ 200 C3 pairs. **VALIDATED_READY_SIGNAL** — C1, C2, C3 in both windows · **PROMISING_UNVALIDATED** — otherwise, if the
pooled (95%) C1 and C3 lower bounds both exceed 1 · **NO_INCREMENTAL_EDGE_FOUND** — otherwise ·
**BLOCKED_BY_SPECIFIC_DATA_GAP** — both windows below a floor.

## 4. Reported, never decisive
APP_POS on the development window (never computed before) · NEAR15 and BOUNCE10_40 alone in both windows (raw lift,
C1) · the app's domain: rows with a reverse split within 120 days (precision, lift, C1 within that subset) · the
sensitivity labels (strict +70%, onset L10, onset IGN — the audit found IGN ≥ 7 sessions after L in 44% of episodes):
raw lift and C1 · flags and triggers per session · recall · lead first flag → onset and → +70%.

## 5. Predictions (written before the run)
Q1 burden above 50 flags per session in both windows · Q2 development raw lift between 0.9 and 1.2 · Q3 C2 fails in
both windows (volatility ranking not beaten) · Q4 C1 fails in at least one window · Q5 status NO_INCREMENTAL_EDGE_FOUND.

## 6. Protection
One command (`python3 faisal_engine/readynow/audit/rn_app_eval.py final` → `audit/data/app_pos_result.json`) after the
SHA-256 check of this file pinned in `rn_app_eval.py` (exit 9 before any read otherwise); the seal commit is pushed and
confirmed on the remote before the run; no rule, window, control or threshold changes after the seal; the READYNOW
sealed result (`318511160`) is not modified.
