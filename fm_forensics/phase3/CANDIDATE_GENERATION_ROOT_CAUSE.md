# CANDIDATE_GENERATION_ROOT_CAUSE — Phase 3 (2026-10-08) · research only · §26 form

Boundary (§1 of the brief) respected: no production file, threshold, ranking, Telegram path, V4 artifact or validation label was modified; everything below is read from `Super_stock.py` at `4ac8a642f` and from research replays under `fm_forensics/phase3/` (lookahead-safe: bars < decision date; weekend Faisal dates evaluated on the next session).

## FIRST FAILURE
The candidate-generation layer admits a symbol only once a **completed structure** exists on the provider-adjusted bars — a second independent touch of the 30-bar low within 1.5% (`tested_level(df,30,0.015,2)`, `ANCHOR_MODE=tested_strict`), a 15-session range ≤120% (`M4_RANGE`), a prior spike ≥78% inside the adjusted series (`M3`), a drop from the adjusted 252-bar high inside [71.7%, 99.95%] (`M2`) — whereas Faisal's first dated act (WATCH) occurs **at the first touch of the low or before it**, and the second touch is what he *waits for* on an already-watched name. The order of evaluation is inverted at one point: the bot's admission rule is Faisal's exit-from-Watch rule.

## WHY
1. The anchor rule is Faisal's *entry* anchor (IMG_0451 «ضربها مرتين ولا كسرها») installed as a *candidate* gate (`analyze_ticker` L4533-4541). On his own dated decisions the price is on an untested low: `tested_touches = 0` on 20/20 anchor-walled rows and 7/7 positive controls.
2. The bot keeps no candidate memory; a name that fails today is re-derived from scratch tomorrow. Faisal keeps a list («قائمتي», `X_20260918_23`) that carries names across the days between touch #1 and the retest.
3. The remaining identity gates (M3 / M2 ceiling / M4 range) are evaluated on windows and a price regime (cumulative split adjustment, 15-bar base, 20-session spike) that do not coincide with Faisal's post-split / lifecycle frame (Phase 2); removing any one of them exposes the anchor wall (M3-walled → ANCHOR 7, M4 5; M2_CEIL-walled → M4 5, ANCHOR 2; M4-walled → ANCHOR 6).

## EVIDENCE (all lookahead-safe)
- **Necessity on Faisal's rows:** 53 dated (ticker,date) rows / 41 tickers: current PASS 3; first wall ANCHOR 20 · M3 13 · M2_CEIL 7 · M4_RANGE 6 · DEPTH 2 · M2_FLOOR 1 · RSI_NOW 1 (`LOGO_SUMMARY.csv`). Anchor at any depth: 35/53.
- **Sufficiency of single gates:** none restores ≥50%; ANCHOR restores 20/53 (ratio 0.40) at ×3.06 control inflation (299 → 914 of 1,320); all identity gates off → 51/53 (P3 holds; H1 falsifier fired).
- **First divergence (41 tickers):** on Faisal's first dated day the bot has candidate 2/41 (CETX, LIMN), watchlist 0/41, ready 0/41, near-watch 11/41; candidate at some point in the 20 sessions before: 15/41; watchlist in the 20 before: 3/41 (`FIRST_DIVERGENCE_TEMPORAL_MATRIX.csv`).
- **Timing:** Faisal's dated decisions are not a fixed lead before the move — lead to +50% median 7.5 sessions, IQR 2–10.5, min 1, max 18 (n = 12 of 34 rows with 20 future sessions; `TEMPORAL_LEAD_TIME_ANALYSIS.csv`); P1 holds. The bot's candidate flag at T−1…T−20 on the same rows: 7, 7, 6, 6, 6, 7, 6, 4, 6, 3, 6, 1 of 53 — never above 13%.
- **Anchors:** DKI rejected by the anchor rule alone on every session 09-08 → 09-16 while near-watch «inside»; the owner's forwarded list has it in FOCUS on 09-13 (`DKI_TIMELINE.csv`). SXTC / HUBC: M2 ceiling (adjusted hi52 83,758 / 1,038,712); no single gate restores; Faisal READY 09-10 / ENTRY 09-11 (SXTC); HUBC UNKNOWN. CRE: M4 range ≈250% → the bot is *late* (candidate + watchlist + READY on 10-06/10-07 = T+17/18, no Faisal evidence) — a case where the bot's process runs where Faisal's did not (negative-direction control).
- **Independent replication:** world A of Phase 2 and Phase 3 `bot_states` agree on 1,520 / 1,520 overlapping (symbol,date) rows (P2 holds).

## COUNTERFACTUAL
- *Persistent memory with unchanged gates* (Architecture B, research replay on world-A PASS flags, `TEMPORAL_ARCHITECTURE_COMPARISON.csv`): memory N = 1 / 3 / 5 / 10 / 15 sessions represents 3 / 8 / 10 / 12 / 16 of 52 Faisal observation-days and 2 / 7 / 9 / 11 / 14 of 41 first observations, while the control candidate-day rate rises 12.1% → 16.7% → 21.0% → 30.0% → 37.3%. Memory alone does not restore Faisal's timing (P5 holds: N = 10 covers 27% of first observations at ×2.5 false-positive rate).
- *Removing the anchor gate* (LOGO): restores 20/53 Faisal rows at ×3.06 control inflation; the bot would then have 914 of 1,320 control rows as candidates with nothing downstream to discriminate them.
- *Perfect pre-Focus features* (`MISSING_FEATURE_MATRIX.csv`): the only feature that separates positives from the pre-registered negatives is `one_touch_fresh_low` (7/7 vs 6/70) — **confounded by construction** (the negatives are bot-candidate days, which have ≥2 touches by definition); the date-matched supplementary control (`MISSING_FEATURE_SUPP_DATE_MATCHED.csv`, post-hoc) is reported in the final report. Post-split reference frame, unfilled gap below, RSI < 33, stability ≥3 sessions: no separation on this sample.

## INDEPENDENT REPLICATION
41 independent tickers (not the three anchors); 7 positive controls defined before results (first observation = READY/ENTRY: AMIX, CRE, GCTK, PIII, SPRC, SXTC, UPC — bot candidate 0/7 on the date); 70 negative controls (bot-candidate days with no Faisal evidence) + 1,320 LOGO control rows; Phase 2 ↔ Phase 3 gate agreement 1,520/1,520.

## REMAINING UNKNOWN
- HUBC's Faisal state on every date (no dated text).
- The owner's 10 current-chat screenshots (not recoverable in this session).
- Faisal-side persistence as a *number* (9/41 tickers multi-dated; 58% of units undated → H5 bounds every persistence statement).
- Whether a stage-ordered architecture would admit Faisal's names without admitting the ×3 control noise: **untested and out of bounds** (no production temporal engine, no V2/V5).
- Replay thresholds are today's envelope, not the envelope of each historical day.
- External information (H4: short availability, offering close, operator presence) appears in Faisal's validity checks (CETX `TG_50828`, LIMN app card) and is absent from bars; its share in *timing* is not measurable here.

## NEXT RESEARCH TARGET (not a fix)
A pre-registered, research-only **stage-order replay**: for every bot-rejected name sitting on an untested 30-bar low (tested_touches = 0, drop/spike within envelope), record the *later* retest (sweep ≥7% below or stability + MA10>20) and measure, with matched controls and the pre-registered labels, whether «watch at touch #1 → act at retest» yields a different candidate set from «admit at touch #2» — on the 2023-2025 window and the 2026 dated corpus. This measures the mismatch; it does not implement anything.
