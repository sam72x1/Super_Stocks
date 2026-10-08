# DKI_FORENSICS (Phase 2) — identity × continuity × pipeline, first divergence (2026-10-08)

## Identity ledger
Ticker DKI · TV `NASDAQ:DKI` · Yahoo `DKI` · no reverse/forward split in Yahoo ∪ Nasdaq calendar · history begins 2025-08-08 (first bar open 140.8, high 240 — IPO day) · 2025-09-30 one-day close ratio 0.123 (−87.7%) — cause UNKNOWN/UNVERIFIED (a crash or an unrecorded corporate action; Faisal's chart annotation «شمعة التقسيم 5.70» suggests a split the sources do not list). Symbol change: UNKNOWN.

## Data continuity
Bot prices (near_watch, Aug→Oct) = TV adjusted closes 1:1 on every snapshot. hi52 as of Sept = 188.8 (the 2025-08/09 regime); drop 98.6–98.7% — inside the band. Extended hours 10-08: pre-market 7.43 (≈10:00 UTC), regular collapse to 0.80.

## Faisal side
08-26 EDU channel reads DKI's group candle (third-party channel, REJECT-style) · 09-13 X_22 FOCUS list (2.66) · ≈09-2x TG_57893/57894 WAIT: «انتظر مسح سيولة إلى 2 تقريبًا · الشراء بعد المسح لا قبله» · later: none in corpus (TG_58386 is the owner's post-collapse chart, undated).

## Bot side (world A)
09-11→10-01: passes M1–M5, soft fails ≤ 8, score ≥ 5; rejected only by `M_لا_مستوى_مختبر` (fresh 30-bar low 2.18 touched once); 10-02→: `M4_base_واسعة` after the −41% collapse. reject_log agrees 20/20. In the near-watch inside bucket (n_out=0) 09-02→10-02; shown once (09-18).

## FIRST DIVERGENCE
Faisal FOCUS (09-13) / WAIT-for-sweep vs bot `candidate rejected` at L5 (anchor rule). Both sides are "waiting" on the same days, but the bot's wait is a rejection with no state, and it was invisible after the display cut.

## Counterfactuals
All worlds identical (no split to vary; ID = A): identity and continuity **cannot** explain DKI. The anchor rule is replicated as the first wall on **27 of 63** independent Faisal-dated cases (`FAISAL_DATED_REPLAY.csv`).

## Classification
Identity: not applicable (Level 0). Continuity: not applicable. Divergence: **anchor definition** (two touches within 1.5% of the 30-bar low) vs Faisal's WATCH (one touch, waiting for the operator) — Level 4 (replicated on independent cases, no single-anchor dependence).
