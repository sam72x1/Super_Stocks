# PERFORMANCE BASELINE — the frozen bot (A) under the preregistered definitions

Commit evaluated: `b8b1242e91c9fce079a95e6b32e0c76b0e4ba697` (`Super_stock.py` unchanged by this experiment; roots fingerprint identical before/after). Data: frozen bars (bars < T), Phase 3 daily bot-state reconstruction, Phase 4 matched control-days. Script: `fm_forensics/perf/perf.py` → `out/perf_results.json`, `out/perf_rows.csv`, `out/perf_controls.csv` (seed 20261009, 2000 cluster-bootstrap draws).

## 1. Identification at Faisal's earliest dated decision (TARGET B vs TARGET A)
| Set | Securities | Rows | Identified at T (security-level) | Identified at T (row-level) | Control-days flagged | Wilson 95% (controls) | LR = recall ÷ control rate |
|---|---|---|---|---|---|---|---|
| discovery | 22 | 46 | **0/22** | 2/46 | 15/88 = 17.0% | 0.106–0.262 | 0.00 |
| validation | 16 | 29 | **2/16** (CETX, LIMN) | 3/29 | 15/64 = 23.4% | 0.147–0.351 | 0.53 |
| anchors (diagnostic) | 3 | 8 | 0/3 | 0/8 | 1/12 | — | 0.00 |

Reading: the frozen bot flags matched control-days (identity-eligible names on an untested low, no documented Faisal attention) **more often** than it flags Faisal's own names at his decision date. LR < 1 means a candidate flag is weak evidence *against* Faisal attention within this population.

## 2. Where the bot loses the names (stage classification, mission §5)
From the Phase 6 trace (`phase6/PHASE6_PIPELINE_TRACE.md`) and Phase 3/4 state reconstruction, for all 41 securities: universe inclusion — passed; data — present (≥ 120 bars); identity — continuous; **candidate generation / technical gates — the stage at which every non-identified name is lost** (the two-touch anchor rule first on 20/53 dated rows; M2 ceiling or M4 range on split-distorted series for SXTC/HUBC); state transition / alert — never reached for them. Classification code: **4 (technical-gate rejection)** for the dated rows; **3 (candidate-generation failure)** for the architectural reading (the rule is placed at admission).

## 3. Volume (denominators stated)
- Frozen 232-symbol panel (Phase 3 reconstruction, 328 session days): median 95 symbols evaluated/day, **median 8 candidates/day**, median 37 anchor-rule rejections/day.
- Production logs (universe ≈ 3,410–3,423 valid symbols/day, 2026-09-25 → 10-08): **108–129 passes/day** (valid − Σ rejections), **381–408 anchor-rule rejections/day** (`reject_log` caps the listed names at 400).

## 4. Exploratory, not preregistered (reported because it changes how §1 reads)
The bot *had* flagged many of Faisal's names as candidates at some earlier day within the 60 sessions before his decision: 10/22 (discovery, median 42.5 sessions earlier) and 14/16 (validation, median 37.5). It then lost them before T. The same look-back applied to the matched control securities gives **53/63 and 28/31** — the "seen earlier" property is as common in controls as in Faisal's names, so it is not an identification signal; it only shows that the daily snapshot flips in and out for everyone.

## 5. Target C base rates (price outcome, +50% high within 20 sessions from the T−1 close)
Faisal securities at their earliest decision: 9/22 (discovery), 4/16 (validation — **13/16 right-censored**, decisions after 2026-09-10) · matched control-days: 29/88, 21/64. Not an acceptance input.

## 6. Limitations
Weekend-mapped dates 9/22 and 7/16 securities (first-decision rows); validation set contaminated by one prior view (Phase 4); HUBC state UNKNOWN; thresholds are today's envelope; the frozen panel is not the universe (volume at universe level is a log proxy).
