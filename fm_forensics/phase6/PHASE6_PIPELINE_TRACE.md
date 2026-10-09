# PHASE 6 — PIPELINE TRACE (Workstream B · `trace.py` → `out/PHASE6_TRACE_SUMMARY.csv`, `out/PHASE6_TRACE_STAGES.csv`)

Scope: every Faisal-dated mention of DKI, SXTC, HUBC in the registry (6 rows; HUBC's Faisal state is kept UNKNOWN per mission).
Lookahead firewall: bars strictly before the mention date T (the morning screener sees the previous close). Data: frozen
`fm_forensics/data/bars_2026-10-08.json.gz` (TradingView, split-adjusted), Phase 2 identity ledger, Phase 3 daily bot-state
reconstruction (`bot_states.csv.gz`), production state files (`alerts_history.json`, `near_watch.json`). Gate execution uses the
**unmodified** production `analyze_ticker` through `p3lib.run_gates`; per-gate pass/fail is obtained by neutralising every
*other* gate through `CONFIG` values that are restored afterwards (no production code change). Phase 1–5 experiments are not
repeated; their outputs are only used as independent reproducibility checks.

Weekend mentions (DKI/SXTC 2026-09-13, a Sunday) are keyed to the next session (2026-09-14) by the Phase 5 cohort manifest; the
bars visible are the same (through 2026-09-11) so the Phase 3 rows keyed on 09-13 are directly comparable.

## 1. Summary (one row per ticker × mention date)
| ticker | T | evidence | Faisal state | as-of bar | bars<T | production result | first failing gate (sequence) | gates failing independently | earliest ineligible stage | bot_states | LOGO |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DKI | 2026-09-14 | X_20260918_22_pipeline | FOCUS | 2026-09-11 | 275 | REJECT `M_لا_مستوى_مختبر` | ANCHOR | ANCHOR | S4/ANCHOR | agrees | agrees |
| HUBC | 2026-04-24 | TG_2098 | UNKNOWN | 2026-04-23 | 327 | REJECT `M4_base_واسعة` | M4_RANGE | M4_RANGE, ANCHOR | S4/M4_RANGE | agrees | agrees |
| SXTC | 2026-09-10 | WA_20260918_31_SXTC | READY | 2026-09-09 | 422 | REJECT `M2_هبوط_فوق_97` | M2_CEIL | M2_CEIL, M4_RANGE, ANCHOR | S4/M2_CEIL | agrees | agrees |
| SXTC | 2026-09-11 | X_20260918_24_SXTC | ENTRY | 2026-09-10 | 423 | REJECT `M2_هبوط_فوق_97` | M2_CEIL | M2_CEIL, M4_RANGE, ANCHOR | S4/M2_CEIL | agrees | agrees |
| SXTC | 2026-09-14 | X_20260918_22_pipeline | FOCUS | 2026-09-11 | 424 | REJECT `M2_هبوط_فوق_97` | M2_CEIL | M2_CEIL, M4_RANGE, ANCHOR | S4/M2_CEIL | agrees | agrees |
| SXTC | 2026-09-24 | TG_58527 | ENTRY | 2026-09-23 | 432 | REJECT `M2_هبوط_فوق_97` | M2_CEIL | M2_CEIL, ANCHOR | S4/M2_CEIL | agrees | agrees |

Reproducibility: 6/6 rows reproduce Phase 3's independent daily reconstruction and its leave-one-gate-out table bit-for-bit
(`bot_states_agrees=YES`, `logo_agrees=YES`). One reproducibility hazard was found and fixed in Phase 6's own tooling: the catalog
envelope (`envelope_p100.json`, source of the live thresholds) is loaded relative to the working directory; a script started from
another directory silently falls back to the engineering thresholds (`MAX_DROP_PCT` 97 instead of 99.95) and attributes DKI and
HUBC to `M2_CEIL`. Both Phase 6 scripts now `chdir` to the repository root before importing the bot (lock `P6T5`).

## 2. Stage walk (identical structure for every row; values from `out/PHASE6_TRACE_STAGES.csv`)
| stage | function / location | inputs & timestamp | predicate + live parameters | ran? | DKI 09-14 | HUBC 04-24 | SXTC 09-10 |
|---|---|---|---|---|---|---|---|
| S0 raw data | frozen TradingView bars | bars<T, last bar = T−1 session | ≥ 2 bars | yes | PASS (275) | PASS (327; 4 reverse splits ≤T, last 2026-04-20) | PASS (422; 4 reverse splits ≤T, last 2026-08-10) |
| S1 identity | `phase2/SECURITY_IDENTITY_LEDGER.csv`; bot keys by ticker string | security id UNKNOWN (bot has none); symbol-change source absent | one continuous series | yes | PASS | PASS | PASS |
| S2 universe | `get_universe` :1729 | `bot_states` row present | listed on NASDAQ | yes | PASS (nw_known=1) | PASS | PASS (nw_known=1) |
| S3 DQ gate | `dq_filter` :2429 | shipped 2026-10-01 | allow/warn | **no — did not exist at T** | n/a | n/a | n/a |
| S4 DEPTH | `MIN_BARS`=120 | bars | bars < 120 | yes | PASS | PASS | PASS |
| S4 M1 | :4046 | close | < `MIN_PRICE` 0.4 | yes | PASS (2.66) | PASS (870.0 adj.) | PASS (2.14) |
| S4 M2_CEIL | :4071 | hi52, drop | drop > `MAX_DROP_PCT` 99.95 | yes | PASS (98.59) | PASS (99.95 — at the edge) | **FAIL** (100.00; hi52 83,758 adj.) |
| S4 M2_FLOOR | :4073 | drop | drop < `MIN_DROP_FLOOR` 71.72 | yes | PASS | PASS | PASS |
| S4 M3 | :4085 | best prior spike | < `PRIOR_SPIKE_FLOOR` 78.27 (window 20) | yes | PASS (228.1) | PASS (137.0) | PASS (145.7) |
| S4 M4_RANGE | :4117 | base range (15 bars) | > `BASE_RANGE_MAX_PCT` 120 | yes | PASS (85.3) | **FAIL** (1012.9) | FAIL (147.6) |
| S4 M4_RISE | :4139 | dist from 30-bar low | > `RECENT_RISE_BLOCK_PCT` 214.7 | yes | PASS (14.66) | PASS (9.43) | PASS (3.88) |
| S4 M5 | :4144 | 20-day $ volume | < `MIN_DOLLAR_VOL` 14,315 | yes | PASS (186,180) | PASS (13.6M) | PASS (8.0M) |
| S4 RSI_OS | :4194 | RSI min 25 | > `RSI_OS_HARD` 69 | yes | PASS (22.5) | PASS (21.1) | PASS (22.3) |
| S4 RSI_NOW | :4201 | RSI14 | > `RSI_NOW_HARD` 71.1 | yes | PASS (29.3) | PASS (30.4) | PASS (23.3) |
| S4 SOFT | :4244 | soft fails | > `WATCH_MAX_FAILS` 8 | yes | PASS | PASS | PASS |
| S4 ANCHOR | :4541 (`tested_level` :10030) | touches, level | no level with ≥2 touches within 1.5 % over 30 bars | yes | **FAIL** (touches 0) | FAIL (touches 0) | FAIL (touches 0) |
| S4 SCORE | :4499 | score | < `SCORE_MIN` 5 | yes | PASS | PASS | PASS |
| S5 selection | `select_top` :14133 · `fill_picks` :12860 · `borrow_gate_recheck` :12764 | watchlist flag | top-N with borrow ≤ 20k | **not reached** | — | — | — |
| S6 near-watch | `near_watch_entry` :13532 | reconstruction | rejected near the walls | yes | IN (inside) | not in | IN (oversold) |
| S7 ready | `entry_status` :14914 | ready flag | price in tranche zone | not reached | — | — | — |
| S8 trigger | `pullback_live` / Polygon (dead since 2026-09-29) | watchlist membership | liquidity anchor | not reached | — | — | — |
| S9 notification | `build_daily_message` :20454 → `send_telegram` :11532 | `alerts_history` rows ≤T | ready card | no | none sent | none sent | none sent |

Notes on "ran?": `analyze_ticker` is sequential and stops at the first rejection; the "gates failing independently" column is the
ablation result (gate g judged with every other gate neutralised). HUBC's M2 ceiling reads 99.95 after rounding but passes in
production (drop below the 99.94998 threshold by a hair) — the pass is borderline, not comfortable.

## 3. Answers required by the mission
- **Earliest stage at which each became ineligible:** S4 candidate gates for all six rows — DKI: anchor rule (two touches);
  SXTC: M2 ceiling (drop from adjusted 52-week high > 99.95 %), with M4 range and the anchor rule also failing independently;
  HUBC: M4 base range, with the anchor rule also failing independently. No row is lost earlier (data present, identity continuous,
  universe membership confirmed) and none reaches selection/ready/trigger/notification.
- **Justified by documented rules?** Yes for the mechanics: each failing predicate and its live parameter exist in code and
  `CONFIG` (`FAISAL_ONLY=1` envelope). Provenance of the parameters is mixed (`FAISAL_SOURCE_LEDGER.md`): the M2 ceiling and
  M4 range are catalog-envelope (`inferred`) numbers; the anchor rule is an engineering rule later shown (Phase 3/4) to encode
  Faisal's *trigger* at the *acceptance* step. "Documented" is therefore true; "matches Faisal's own method" is not established.
- **Input data unavailable?** No — bars were present for every row (≥ 275 before T). The DQ gate did not exist at T. Non-candle
  inputs (float, borrow, SI) are not consulted by S4 at all, so their unavailability cannot explain these rejections.
- **Reproducible?** Yes — 6/6 against two independent reconstructions; and the trace is deterministic on the frozen data.
- **Lookahead / contamination:** only bars < T are used; Faisal states are read from the dated registry (not from prices after T);
  the registry rows for these anchors come from Phase 3/5 (already reviewed for lookahead in `phase3/LOOKAHEAD_AUDIT.csv`).

## 4. What the trace cannot say
It cannot say whether the bot *should* have accepted these names: that is the methodological question Phases 2–5 addressed and
left at Level 4 (first causally supported failure = candidate-generation definitions on the adjusted series vs Faisal's post-split
frame; anchor rule at acceptance). The trace establishes *where* and *why* in the code each name was dropped, and that nothing
downstream of S4 ever ran for them; it does not establish that changing a gate would have produced a Faisal-like selection
(Phase 2's replay showed it would not, at the cost of large false-positive growth).
