# READY_NOW_V2_prereg — pre-registration of the SHADOW evaluator (written 2026-10-08, BEFORE any shadow number)

> Shadow only. Not production. Not V4. Not Telegram. No ticker name in logic. This contract is frozen when merged; results are reported against it and never relax it.

## H0 / H1
- H0: a staged state model (FOCUS → WATCH → READY → TRIGGER) does not identify Faisal-reconstructed focus/ready stocks better than the current READY NOW flag or the three-conditions filter.
- H1: it does, on cases NOT used to derive it.

## Populations (fixed before numbers)
- DEV (derivation): the 64 eye-read images of this mission + the 19 rules in `READY_NOW_RULE_EVIDENCE_MATRIX.csv`. Anchors DKI/SXTC/HUBC/CRE live here and are **excluded from every score**.
- VAL (validation, Faisal labels): dated inventory rows with a Faisal decision (WAIT/READY/WATCH/REJECT) and a ticker, dated to the day, excluding the four anchors and excluding any ticker that appears in DEV images. Expected n: see `FAISAL_FOCUS_TIMELINE.csv` (302 fully-dated rows across all authors; Faisal-only with decision ≠ NONE is smaller — the count is reported, not assumed). If n < 20 per decision class → that class is UNKNOWN.
- HOLDOUT (independent outcome labels, no Faisal involvement): the bot's explosion register ≥ 100% (279 rows, 2026-07-17 → 10-07) minus anchors, with a matched control of non-exploding symbols drawn from the same near-watch snapshots (1:1 by date, random seed 20261008).

## Shadow model definition (fixed)
States on daily bars only (no intraday, no borrow data — those are UNKNOWN by design in the shadow):
- IDENTITY: current M1–M5 **except** M2 uses `max(pre_split_adjusted_high_in_window)` computed on split-adjusted bars after re-basing at the last reverse split date if a split occurred inside the 52-week window (`split_restart`). Evidence: R-SPLIT-FOUNDING.
- FOCUS: IDENTITY ∧ a base low L (lowest low in the last 30 bars) ∧ ≥ 1 touch. (Current code requires 2 touches → that is WATCH here, not FOCUS.)
- WATCH: FOCUS ∧ L held ≥ 3 sessions (R-BASE-HOLD) ∧ RSI14 ≤ 33 at any point in the base (R-RSI-LOW).
- READY: WATCH ∧ (price within [L, L×1.15]) (R4-ZONE-01 / R-TEST-BOUNCE-RETEST: zone, not first contact) ∧ held ≥ 5 sessions OR a completed test-bounce (≥ 10% off L then back inside the zone).
- TRIGGER: READY ∧ sweep (low < L × (1 − s), s ∈ [0.05, 0.13]) ∧ reclaim close > L within 2 sessions (R-SWEEP-RECLAIM). The reclaim day is the trigger day.
- INVALIDATED: close < L × 0.87 without reclaim in 2 sessions (R4-INV-01) → restart FOCUS from the new L.
- Persistence: a symbol stays in its state until a transition; no daily re-admission; no slot cap.
- All numbers above are **Faisal-stated or ledger-tagged** (3/5 sessions IMG_0151/X_85; 15% zone IMG_0531; 5–13% sweep TG_50584/IMG_0297/TG_57870; 33 RSI = live `RSI_OVERSOLD`). No number may be tuned after a result is seen.

## Comparators
- CURRENT READY NOW: `entry_status` on the watchlist (history from git snapshots).
- THREE-CONDITIONS: `flags3`-equivalent on daily bars (RSI < 33 ∧ exact-low stability 5 ∧ no 50% explosion); float/avail UNKNOWN → counted as pass (optimistic for the comparator).
- V2 shadow (above).

## Metrics (per comparator, VAL and HOLDOUT separately; Wilson 95% intervals; no p-values)
- recall of Faisal READY/ENTRY days (state READY or TRIGGER on that day or within the prior 3 sessions)
- focus detection (state ≥ FOCUS on Faisal WAIT/WATCH days)
- lead time (sessions from first READY to Faisal's READY day; negative = late)
- false positives (READY days on symbols Faisal labelled REJECT/INVALID within ±5 sessions)
- HOLDOUT: share of ≥100% movers in state ≥ WATCH within 14 sessions before the move, vs the matched control's share of WATCH days.
- transition accuracy: UNKNOWN unless ≥ 20 labelled transitions exist (expected: UNKNOWN).

## Decision rule (fixed)
- Branch 1 «V2 is a better shadow»: on HOLDOUT, V2 WATCH-or-higher recall on movers exceeds the control's WATCH rate by a Wilson-separated margin AND on VAL the READY recall ≥ current READY NOW recall with lead time ≥ 0 median; AND the result holds with anchors excluded.
- Branch 2 «no advantage»: any of the above fails.
- Branch 3 «no measurement»: bars unavailable or VAL per-class n < 20 and HOLDOUT control cannot be built.
- Under every branch: no production change; the report names the branch and all falsified predictions are kept.

## Predictions written before running
P1: VAL Faisal-READY n < 20 → READY recall will be reported UNKNOWN. P2: HOLDOUT: V2 WATCH-or-higher on movers ≥ 40% (near-watch inside/oversold already covers 46%). P3: current READY NOW recall on movers stays < 2%. P4: V2 will flag more symbols per day than READY NOW (precision will be the cost; measured, not assumed).
