# PHASE 5 §2 — Phase 4 reconciliation (audited, not trusted)

Recomputed from `fm_forensics/phase3/FAISAL_TIMELINE.csv` through `p4lib.faisal_timeline`/`first_states` by name, and from the Phase 4 artifacts at HEAD `4980a33d40f5`. No feature value and no feature–outcome number was computed here.

**Checks: 51/51 REPRODUCED.**

| check | recomputed | Phase 4 claim | status | note |
|---|---|---|---|---|
| tickers (dated FOCUS/WATCH/READY/ENTRY · IS_FAISAL=1) | 41 | 41 | REPRODUCED |  |
| discovery tickers | 22 | 22 | REPRODUCED |  |
| validation tickers | 16 | 16 | REPRODUCED |  |
| anchor tickers | 3 | 3 | REPRODUCED |  |
| tickers outside the three sets | 0 | 0 | REPRODUCED |  |
| membership rule (first state <= 2026-08-31 ⇔ discovery) | 0 | 0 | REPRODUCED |  |
| dated rows | 83 | 83 | REPRODUCED |  |
| rows discovery | 46 | 46 | REPRODUCED |  |
| rows validation | 29 | 29 | REPRODUCED |  |
| rows anchor | 8 | 8 | REPRODUCED |  |
| evidence class DIRECT_TEXT | 59 | 59 | REPRODUCED |  |
| evidence class DIRECT_CHART | 20 | 20 | REPRODUCED |  |
| evidence class ACTION | 4 | 4 | REPRODUCED |  |
| evidence class WATCHLIST/UNKNOWN among dated rows | 0 | 0 | REPRODUCED |  |
| weekend/holiday first dates mapped to next session (non-anchor) | 16 | 16 | REPRODUCED |  |
| exact duplicate rows (ticker,session,evidence,state) | 0 | 0 | REPRODUCED |  |
| tickers excluded by Phase 4 for lack of bars (prereg §⑦: 'excluded (counted)') | 4 | 4 | REPRODUCED | ATPC;LABT;MI;UNK |
| POSITIVE_VALIDATION_CASES rows | 41 | 41 | REPRODUCED |  |
| POSITIVE_VALIDATION_CASES first-state dates == recomputed | 41 | 41 | REPRODUCED |  |
| POSITIVE_VALIDATION_CASES first-state class == recomputed | 41 | 41 | REPRODUCED |  |
| controls (control-days) | 164 | 164 | REPRODUCED |  |
| controls discovery | 88 | 88 | REPRODUCED |  |
| controls validation | 64 | 64 | REPRODUCED |  |
| controls anchor | 12 | 12 | REPRODUCED |  |
| controls distinct symbols | 75 | 75 | REPRODUCED |  |
| controls full matches (4/4) | 128 | 128 | REPRODUCED |  |
| controls with any Faisal unit (should be none) | 0 | 0 | REPRODUCED |  |
| controls equal to a positive ticker | 0 | 0 | REPRODUCED |  |
| controls matched on the positive's first-state date | 164 | 164 | REPRODUCED |  |
| controls identity-eligible without anchor at date | 164 | 164 | REPRODUCED |  |
| EVENT_LEDGER rows | 415 | 415 | REPRODUCED |  |
| EVENT_LEDGER decision units | 83 | 83 | REPRODUCED |  |
| EVENT_LEDGER lookahead-safe rows | 415 | 415 | REPRODUCED |  |
| PHASE_ORDERING_MATRIX rows | 41 | 41 | REPRODUCED |  |
| ordering EXPECTED (non-anchor) | 15 | 15 | REPRODUCED |  |
| ordering CONTRADICTED (non-anchor) | 12 | 12 | REPRODUCED |  |
| ordering INSUFFICIENT (non-anchor) | 11 | 11 | REPRODUCED |  |
| E2 LEVEL_INVALIDATED (non-anchor) | 20 | 20 | REPRODUCED |  |
| E2 WINDOW_EXPIRED (non-anchor) | 12 | 12 | REPRODUCED |  |
| E2 occurred (non-anchor) | 6 | 6 | REPRODUCED |  |
| E3 present (non-anchor) | 27 | 27 | REPRODUCED |  |
| FT→state median sessions (non-anchor) | 5.0 | 5 | REPRODUCED | n=38 |
| alert FP discovery/A | 0.17 | 0.17 | REPRODUCED |  |
| alert FP discovery/B | 0.102 | 0.102 | REPRODUCED |  |
| alert FP discovery/C | 0.398 | 0.398 | REPRODUCED |  |
| alert FP discovery/D | 0.341 | 0.341 | REPRODUCED |  |
| alert FP validation/A | 0.234 | 0.234 | REPRODUCED |  |
| alert FP validation/B | 0.109 | 0.109 | REPRODUCED |  |
| alert FP validation/C | 0.406 | 0.406 | REPRODUCED |  |
| alert FP validation/D | 0.328 | 0.328 | REPRODUCED |  |
| alert FP anchor/B | 0.083 | 0.083 | REPRODUCED |  |

## Reconciliation notes

- third-party rows with a state class, excluded by `IS_FAISAL==1`: **22**
- Faisal rows excluded by class: {'MENTION': 128, 'UNKNOWN': 15, 'EXIT': 4} (MENTION/UNKNOWN carry no selection tier · EXIT = post-selection exit, not a pre-selection negative)
- tickers with more than one dated row: **20** (max 6 · [('ONCO', 6), ('CANF', 5), ('SXTC', 5), ('CIIT', 4), ('DXST', 4)])
- unique sessions 32 · ticker×session pairs 52 · rows 83 (same ticker, same session, several evidence units: 31)
- evidence units naming more than one ticker: **2** → {'X_20260918_23_watchlist': ['CETX', 'CUPR', 'DKI', 'MSGY', 'SVRE', 'SXTC', 'YMT'], 'X_20260918_22_pipeline': ['DKI', 'SXTC']}
- **Phase 4 excluded 4 dated Faisal tickers without bars** (['ATPC', 'LABT', 'MI', 'UNK'] · 5 rows): the prereg says 'excluded (counted)' but the report's 41/83 never lists them by name. Under Phase 5 §0 this is a **data-availability exclusion (category D)**; they stay in the manifest with `HAS_BARS=0` and `PHASE4_SET=other`, outside primary inference, and are reported in every denominator audit. `UNK` is an unresolved ticker from an image; `MI` is a single TG unit.
- control symbols reused across positives: **39** (max 8 · top [('FRGT', 8), ('WCT', 5), ('BNKK', 5), ('WKHS', 5), ('TNMG', 5)]) — Phase 4 treated each control-day as independent; Phase 5 clusters by security
- controls per positive: {4: 41} (positives with 0 controls: [])
- FEATURE_TESTS rows 10 (values checked by eye against the report: fresh-first-touch 181/5,911 vs 230/8,383 · E3-present 10/694 vs 401/13,600)
- arch rows discovery: rows 46 · tickers 22 · unique decision dates 22 · ticker×date pairs 28
- arch rows validation: rows 29 · tickers 16 · unique decision dates 8 · ticker×date pairs 18
- arch rows anchor: rows 8 · tickers 3 · unique decision dates 5 · ticker×date pairs 6
- labels in Phase 4: positives = documented Faisal state (all DIRECT · IS_FAISAL=1); controls = **absence of any Faisal unit** — under Phase 5 §4 that is `UNKNOWN`, not `NEGATIVE_DIRECT`
- Phase 4 validation labels were **revealed** (validation rows were analysed after the discovery freeze) ⇒ for Phase 5 they are contaminated as a blind set (§10)
- episodes (gap > 30 sessions opens a new one): **46** over 45 securities · securities with 2+ episodes: [('DXST', 2)]
- primary units (one per non-anchor security with bars · earliest unit of episode 1): **38**
- manifest rows 88 · unique securities 45 · unique episodes 46 · unique evidence units 80

## Decisions for Phase 5 (from this audit)

1. **Unit of analysis** = `DECISION_EPISODE_ID` (security × episode; a gap over 30 sessions between dated units opens a new episode). Primary inference uses **one primary unit per non-anchor security** (earliest unit of episode 1); repeated units are evidence within the episode, never independent rows. Clustering by `SECURITY_ID`.
2. **Anchors DKI/SXTC/HUBC** carry `ANCHOR_EXCLUDED=1` and are outside primary inference (descriptive only). HUBC's label is never invented.
3. **Phase 4 controls** have no negative label: their status under §4 is `UNKNOWN` (absence of a post). Phase 5 builds its control manifest fresh (§11) and assigns tiers (§12) explicitly; Phase 4 control identities are kept for comparison only.
4. **Phase 4 validation membership is contaminated** (labels revealed in Phase 4) ⇒ Phase 5 does not reuse it as a blind set. A new security-level partition is defined in the prereg (§G) before any feature value is joined to an outcome.
5. Evidence quality: `DIRECT_CHART` units (20) are labelled MEDIUM confidence; `DIRECT_TEXT`/`ACTION` HIGH. Sensitivity to label quality is pre-registered.
6. Repeated tickers (20 of 41 with more than one dated row) explain why rows (83) exceed securities (41): Phase 4 reported both; nothing is hidden.
7. The four bar-less tickers (ATPC · LABT · MI · UNK) are a **documented data-availability exclusion**, not a hidden one; Phase 5 keeps them in the manifest (`HAS_BARS=0`) and lists them in every denominator.
