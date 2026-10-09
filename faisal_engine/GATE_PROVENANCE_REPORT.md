# 🚪🧭 Gate provenance report — generated (`python3 faisal_engine/gate_inventory.py`)

Research only. Generated from `faisal_engine/data/gate_provenance.json` (curated evidence), the code (AST anchors, live
production configuration `FAISAL_ONLY=1`), a frozen snapshot of `reject_log.json`, and the frozen ranking bars. Every number below is produced by the builder; `--check` regenerates and compares. Line numbers are as of the build and move with edits (the check verifies each anchor still sits inside its function).

**49 gates inventoried** · reject codes in `analyze_ticker`: 19 (all inventoried) · silent `return None` paths: 3 (all inventoried) · build errors: 0

## 1. The seven decision questions

1. **Hard exclusions with direct Faisal evidence:** none (the only DIRECT row, `STABILITY_BT`, is a backtest arm and inactive in production).
2. **Hard exclusions inferred from Faisal evidence (catalog envelope / concept):** `M1_PRICE`, `M2_FLOOR`, `M3_FLOOR`, `M4_RISE`, `M10_RSI_OS`, `M10_RSI_NOW`.
3. **Engineering guards:** `D_DEPTH`, `M2_HI52_GUARD`, `M2_CEIL`, `M4_BASE_LO_GUARD`, `M5_DOLLAR_VOL`, `SOFT_COUNT`, `SCORE_MIN`, `RR_SOFT_COUNT`, `ANALYZE_EXCEPTION`, `TIER`, `COVERAGE_GUARD`, `STOPPED_EXCLUSION`, `FILL_ROUNDS` · **owner policy:** `U_NASDAQ`, `M4_RANGE`, `M4_RANGE_PULLBACK`, `ANCHOR_TWO_TOUCH`, `M14_FLOAT`, `DQ_GATE`, `CAPACITY_SLOTS`, `M14_REFLOAT`, `BORROW_AVAIL`.
4. **Possible data/adjustment/order artefacts or frame differences:** `D_DEPTH`, `D_ADJUST`, `M2_CEIL`, `M2_FLOOR`, `DQ_GATE`, `FILL_ROUNDS`, `BORROW_AVAIL`; cases whose first wall is an artefact: none.
5. **Without supporting evidence (UNKNOWN_OR_UNSUPPORTED):** none; rows whose evidence list is only «no Faisal source» are engineering by construction (question 3).
6. **Change the candidate set** (hard, active): `U_NASDAQ`, `D_DEPTH`, `M1_PRICE`, `M2_HI52_GUARD`, `M2_CEIL`, `M2_FLOOR`, `M3_FLOOR`, `M4_BASE_LO_GUARD`, `M4_RANGE`, `M4_RANGE_PULLBACK`, `M4_RISE`, `M5_DOLLAR_VOL`, `M10_RSI_OS`, `M10_RSI_NOW`, `SOFT_COUNT`, `SCORE_MIN`, `ANCHOR_TWO_TOUCH`, `RR_SOFT_COUNT`, `ANALYZE_EXCEPTION`, `M14_FLOAT`, `TIER`, `DQ_GATE`, `COVERAGE_GUARD`, `STOPPED_EXCLUSION`, `CAPACITY_SLOTS`, `FILL_ROUNDS`, `M14_REFLOAT`, `BORROW_AVAIL` · **ranking only:** `RANK_KEY` · **display/readiness only:** `ENTRY_STATUS`, `HC_GATE_DISPLAY`, `HC_VERDICT` · **soft (count toward `SOFT_COUNT`):** `SOFT_M10_RSI`, `SOFT_M11_MACD`, `SOFT_M12_EMA`, `SOFT_M2_IDEAL`, `SOFT_M3_IDEAL`, `SOFT_M6_TF`, `SOFT_M7_PATTERN`, `SOFT_M9_GAP_ABOVE`, `M13_SHORT`.
7. **Highest-value permitted next action:** see §5.

## 2. Gate table (pipeline order)

| # | gate | where (as of build) | role · kind | provenance | confidence | status | live value | prod/day (median · 10-09) |
|---|---|---|---|---|---|---|---|---|
| 10 | `U_NASDAQ` | `Super_stock.py::get_universe` L1732 | reject · owner_policy | OWNER_POLICY | VERIFIED | OWNER_DECIDED | — | — |
| 20 | `D_DEPTH` | `Super_stock.py::_extract_into` L1813 | reject · coverage_guard | ENGINEERING_GUARD | VERIFIED | OPEN | MIN_BARS=120 | — |
| 25 | `D_ADJUST` | `Super_stock.py::tv_download` L2143 | input · info | ENGINEERING_GUARD | VERIFIED | OPEN | — | — |
| 30 | `M1_PRICE` | `Super_stock.py::analyze_ticker` L4046 | reject · hard | INFERRED_FROM_FAISAL_EVIDENCE | STRONGLY SUPPORTED | OPEN | MIN_PRICE=0.4 | 78 · 81 |
| 31 | `M2_HI52_GUARD` | `Super_stock.py::analyze_ticker` L4068 | reject · ops_safety | ENGINEERING_GUARD | VERIFIED | OPEN | — | 0 · 0 |
| 32 | `M2_CEIL` | `Super_stock.py::analyze_ticker` L4071 | reject · hard | ENGINEERING_GUARD | VERIFIED | CLOSED | MAX_DROP_PCT=99.95 | 23 · 22 |
| 33 | `M2_FLOOR` | `Super_stock.py::analyze_ticker` L4073 | reject · hard | INFERRED_FROM_FAISAL_EVIDENCE | STRONGLY SUPPORTED | CLOSED | MIN_DROP_FLOOR=71.7203 | 2643 · 2612 |
| 34 | `M3_FLOOR` | `Super_stock.py::analyze_ticker` L4085 | reject · hard | INFERRED_FROM_FAISAL_EVIDENCE | INFERRED | OPEN | PRIOR_SPIKE_FLOOR=78.2738 · PRIOR_SPIKE_WINDOW=20 · BASE_WINDOW=15 | 66 · 71 |
| 35 | `M4_BASE_LO_GUARD` | `Super_stock.py::analyze_ticker` L4095 | reject · ops_safety | ENGINEERING_GUARD | VERIFIED | OPEN | — | 0 · 0 |
| 36 | `M4_RANGE` | `Super_stock.py::analyze_ticker` L4117 | reject · hard | OWNER_POLICY | VERIFIED | OWNER_DECIDED | BASE_RANGE_MAX_PCT=120 · BASE_WINDOW=15 | 77 · 88 |
| 37 | `M4_RANGE_PULLBACK` | `Super_stock.py::analyze_ticker` L4128 | reject · owner_policy | OWNER_POLICY | VERIFIED | OWNER_DECIDED | — | 0 · 0 |
| 38 | `M4_RISE` | `Super_stock.py::analyze_ticker` L4139 | reject · hard | INFERRED_FROM_FAISAL_EVIDENCE | INFERRED | OPEN | RECENT_RISE_BLOCK_PCT=214.7287 | 0 · 0 |
| 39 | `M5_DOLLAR_VOL` | `Super_stock.py::analyze_ticker` L4144 | reject · hard | ENGINEERING_GUARD | STRONGLY SUPPORTED | OPEN | MIN_DOLLAR_VOL=14314.7701 | 7 · 5 |
| 40 | `M8_GAP_REQUIRED` | `Super_stock.py::analyze_ticker` L4166 | reject · hard | ENGINEERING_GUARD | VERIFIED | INACTIVE | GAP_REQUIRED=False | — |
| 41 | `M10_RSI_OS` | `Super_stock.py::analyze_ticker` L4194 | reject · hard | INFERRED_FROM_FAISAL_EVIDENCE | STRONGLY SUPPORTED | CLOSED | RSI_OS_HARD=69 · RSI_OS_LOOKBACK=25 | 0 · 0 |
| 42 | `M10_RSI_NOW` | `Super_stock.py::analyze_ticker` L4201 | reject · hard | INFERRED_FROM_FAISAL_EVIDENCE | INFERRED | CLOSED | RSI_NOW_HARD=71.1186 | 2 · 3 |
| 43 | `SOFT_COUNT` | `Super_stock.py::analyze_ticker` L4244 | reject · hard | ENGINEERING_GUARD | VERIFIED | OPEN | WATCH_MAX_FAILS=8 | 0 · 0 |
| 44 | `STABILITY_BT` | `Super_stock.py::analyze_ticker` L4338 | reject · info | DIRECT_FAISAL_EVIDENCE | VERIFIED | CLOSED | BT_STABILITY_GATE= · STABILITY_MIN=3 | 0 · 0 |
| 45 | `NEAR_READINESS` | `Super_stock.py::analyze_ticker` L4355 | reject · hard | ENGINEERING_GUARD | VERIFIED | INACTIVE | NEAR_PCT=0 | 0 · 0 |
| 46 | `SCORE_MIN` | `Super_stock.py::analyze_ticker` L4499 | reject · hard | ENGINEERING_GUARD | VERIFIED | OPEN | SCORE_MIN=5 | 4 · 8 |
| 47 | `ANCHOR_TWO_TOUCH` | `Super_stock.py::analyze_ticker` L4541 | reject · owner_policy | OWNER_POLICY | VERIFIED | FROZEN | ANCHOR_MODE=tested_strict | 395 · 407 |
| 48 | `RR_SOFT_COUNT` | `Super_stock.py::analyze_ticker` L4758 | reject · hard | ENGINEERING_GUARD | VERIFIED | OPEN | MIN_RR_T1=0.5 · WATCH_MAX_FAILS=8 | 0 · 0 |
| 49 | `PULLBACK_NOT_RISEN` | `Super_stock.py::analyze_ticker` L4791 | reject · info | ENGINEERING_GUARD | VERIFIED | OPEN | — | — |
| 50 | `ANALYZE_EXCEPTION` | `Super_stock.py::analyze_ticker` L4834 | reject · ops_safety | ENGINEERING_GUARD | VERIFIED | OPEN | — | — |
| 60 | `SOFT_M10_RSI` | `Super_stock.py::analyze_ticker` L4198 | describe · soft | INFERRED_FROM_FAISAL_EVIDENCE | STRONGLY SUPPORTED | OPEN | RSI_OVERSOLD=33 · RSI_MAX_NOW=35.7789 | — |
| 60 | `SOFT_M11_MACD` | `Super_stock.py::analyze_ticker` L4213 | describe · soft | INFERRED_FROM_FAISAL_EVIDENCE | INFERRED | OPEN | MACD_GATE_REQUIRED=True | — |
| 60 | `SOFT_M12_EMA` | `Super_stock.py::analyze_ticker` L4240 | describe · soft | INFERRED_FROM_FAISAL_EVIDENCE | INFERRED | OPEN | MA_GATE_REQUIRED=True · MA_GATE_MAX_ABOVE_PCT=95.4707 | — |
| 60 | `SOFT_M2_IDEAL` | `Super_stock.py::analyze_ticker` L4079 | describe · soft | INFERRED_FROM_FAISAL_EVIDENCE | INFERRED | OPEN | MIN_DROP_PCT=96.9178 | — |
| 60 | `SOFT_M3_IDEAL` | `Super_stock.py::analyze_ticker` L4088 | describe · soft | INFERRED_FROM_FAISAL_EVIDENCE | INFERRED | OPEN | PRIOR_SPIKE_PCT=164.0212 | — |
| 60 | `SOFT_M6_TF` | `Super_stock.py::analyze_ticker` L4150 | describe · soft | INFERRED_FROM_FAISAL_EVIDENCE | VERIFIED | INACTIVE | TF_MIN_REVERSALS=0 | — |
| 60 | `SOFT_M7_PATTERN` | `Super_stock.py::analyze_ticker` L4155 | describe · soft | INFERRED_FROM_FAISAL_EVIDENCE | INFERRED | OPEN | — | — |
| 60 | `SOFT_M9_GAP_ABOVE` | `Super_stock.py::analyze_ticker` L4180 | describe · soft | INFERRED_FROM_FAISAL_EVIDENCE | INFERRED | OPEN | GAP_ABOVE_REQUIRED=True · GAP_ABOVE_MAX_DIST_PCT=1134.7826 | — |
| 70 | `M13_SHORT` | `Super_stock.py::apply_short_gate` L12602 | describe · soft | OWNER_POLICY | VERIFIED | OWNER_DECIDED | SHORT_GATE_MAX=40000 · SHORT_GATE_REQUIRED=True | — |
| 71 | `M14_FLOAT` | `Super_stock.py::apply_float_gate` L12672 | reject · owner_policy | OWNER_POLICY | VERIFIED | OWNER_DECIDED | FLOAT_GATE_MAX=50000000 · FLOAT_GATE_REQUIRED=True | — |
| 72 | `TIER` | `Super_stock.py::classify_tier` L12973 | reject · hard | ENGINEERING_GUARD | VERIFIED | OPEN | WATCH_MAX_FAILS=8 | — |
| 73 | `RANK_KEY` | `Super_stock.py::rank_key` L12995 | rank · info | ENGINEERING_GUARD | VERIFIED | CLOSED | — | — |
| 80 | `DQ_GATE` | `Super_stock.py::dq_filter` L2429 | reject · coverage_guard | OWNER_POLICY | VERIFIED | OWNER_DECIDED | DQ_GATE=None · DQ_POLICY=None | — |
| 81 | `COVERAGE_GUARD` | `Super_stock.py::run_daily_watchlist` L22144 | reject · coverage_guard | ENGINEERING_GUARD | VERIFIED | OPEN | DATA_HEALTH_MIN_PCT=85 | — |
| 82 | `STOPPED_EXCLUSION` | `Super_stock.py::run_daily_watchlist` L22148 | reject · owner_policy | ENGINEERING_GUARD | VERIFIED | OPEN | EXCLUDE_STOPPED_FROM_RENEWAL=True | — |
| 83 | `CAPACITY_SLOTS` | `Super_stock.py::run_daily_watchlist` L22177 | reject · owner_policy | OWNER_POLICY | VERIFIED | OWNER_DECIDED | WATCHLIST_SIZE=15 | — |
| 84 | `FILL_ROUNDS` | `Super_stock.py::fill_picks` L12893 | reject · ops_safety | ENGINEERING_GUARD | VERIFIED | OPEN | PICK_FILL_ROUNDS=4 | — |
| 85 | `M14_REFLOAT` | `Super_stock.py::refloat_gate_recheck` L12761 | reject · owner_policy | OWNER_POLICY | VERIFIED | OWNER_DECIDED | FLOAT_GATE_MAX=50000000 | — |
| 86 | `BORROW_SECOND_CHANCE` | `Super_stock.py::borrow_second_chance` L12810 | input · coverage_guard | ENGINEERING_GUARD | VERIFIED | OPEN | — | — |
| 87 | `BORROW_AVAIL` | `Super_stock.py::borrow_gate_recheck` L12800 | reject · owner_policy | OWNER_POLICY | VERIFIED | OWNER_DECIDED | BORROW_AVAIL_MAX=20000 · BORROW_GATE_REQUIRED=True | — |
| 90 | `ENTRY_STATUS` | `Super_stock.py::entry_status` L14951 | display · info | INFERRED_FROM_FAISAL_EVIDENCE | INFERRED | OPEN | — | — |
| 95 | `HC_GATE_DISPLAY` | `analyze_one.py::append_short_float_gates` L709 | display · info | OWNER_POLICY | VERIFIED | OPEN | — | — |
| 96 | `HC_VERDICT` | `analyze_one.py::post_enrich_verdict` L746 | display · info | OWNER_POLICY | VERIFIED | OPEN | — | — |
| 97 | `RESEARCH_ENGINE` | `faisal_engine/engine.py::evaluate` L142 | describe · info | INFERRED_FROM_FAISAL_EVIDENCE | STRONGLY SUPPORTED | OPEN | — | — |
| 98 | `V4_FROZEN` | `faisal_method_v4/decision_engine.py::analyze` L215 | describe · info | INFERRED_FROM_FAISAL_EVIDENCE | VERIFIED | FROZEN | — | — |

## 3. First exclusion per Faisal episode (frozen bars < T, production `analyze_ticker`)

The cause is the **first** wall; the chain lists what would block next if each wall were neutralised (research only).

| case | T | first wall | value · threshold | case class | chain | frozen replay | operational list |
|---|---|---|---|---|---|---|---|
| AMIX_E1 | 2026-08-24 | M4_RANGE | 703.9088 · BASE_RANGE_MAX_PCT 120 | OWNER_POLICY | M4_RANGE → ANCHOR → PASS | match | 0 |
| ATPC_E1 | 2026-09-14 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | OWNER_POLICY | ANCHOR → PASS | match | 0 |
| BRTX_E1 | 2026-10-05 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | OWNER_POLICY | ANCHOR → PASS | match | 0 |
| CETX_E1 | 2026-09-14 | PASS |  ·  | PASS |  → PASS | match | 1 |
| CIIT_E1 | 2026-09-25 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | OWNER_POLICY | ANCHOR → PASS | match | 0 |
| CUPR_E1 | 2026-09-14 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | OWNER_POLICY | ANCHOR → PASS | match | 0 |
| DCOY_E1 | 2026-09-22 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | OWNER_POLICY | ANCHOR → PASS | match | 0 |
| DKI_E1 | 2026-09-14 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | OWNER_POLICY | ANCHOR → PASS | match | 0 |
| EDBL_E1 | 2026-09-22 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | OWNER_POLICY | ANCHOR → PASS | match | 0 |
| GCTK_E1 | 2026-09-24 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | OWNER_POLICY | ANCHOR → PASS | match | 0 |
| IPDN_E1 | 2026-09-23 | M4_RANGE | 122.9428 · BASE_RANGE_MAX_PCT 120 | OWNER_POLICY | M4_RANGE → ANCHOR → PASS | match | 0 |
| LABT_E1 | 2026-08-24 | DEPTH | 84 · MIN_BARS 120 | ENGINEERING_GUARD | DEPTH → ANCHOR → PASS | match | 0 |
| LIMN_E1 | 2026-09-22 | PASS |  ·  | PASS |  → PASS | match | 1 |
| MI_E1 | 2026-09-28 | UNIVERSE |  ·  | OWNER_POLICY | UNIVERSE → M3 → PASS | — | — |
| MSGY_E1 | 2026-09-14 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | OWNER_POLICY | ANCHOR → PASS | match | 0 |
| NRSN_E1 | 2026-09-28 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | OWNER_POLICY | ANCHOR → PASS | match | 0 |
| NUWE_E1 | 2026-09-04 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | OWNER_POLICY | ANCHOR → PASS | match | 0 |
| OMH_E1 | 2026-09-28 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | OWNER_POLICY | ANCHOR → PASS | match | 0 |
| PPBT_E1 | 2026-09-04 | RSI_NOW | 71.8977 · RSI_NOW_HARD 71.1186 | INFERRED_FROM_FAISAL_EVIDENCE | RSI_NOW → ANCHOR → PASS | match | 0 |
| STKH_E1 | 2026-09-04 | M4_RANGE | 172.2944 · BASE_RANGE_MAX_PCT 120 | OWNER_POLICY | M4_RANGE → ANCHOR → PASS | match | 0 |
| SVRE_E1 | 2026-09-14 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | OWNER_POLICY | ANCHOR → PASS | match | 0 |
| SXTC_E1 | 2026-09-10 | M2_CEIL | 99.9974 · MAX_DROP_PCT 99.95 | ENGINEERING_GUARD | M2_CEIL → M4_RANGE → ANCHOR → PASS | match | 0 |
| YMT_E1 | 2026-09-04 | M3 | 72.9819 · PRIOR_SPIKE_FLOOR 78.2738 | INFERRED_FROM_FAISAL_EVIDENCE | M3 → M4_RANGE → ANCHOR → PASS | match | 0 |
| HUBC_2026-04-24 | 2026-04-24 | M4_RANGE | 1012.8931 · BASE_RANGE_MAX_PCT 120 | OWNER_POLICY | M4_RANGE → ANCHOR → PASS | — | — |

First-wall counts: ANCHOR 13, M4_RANGE 4, PASS 2, DEPTH 1, M2_CEIL 1, M3 1, RSI_NOW 1, UNIVERSE 1 · replay mismatches against the frozen ranking rows: 0 · walls present anywhere in a chain: ANCHOR 21, M4_RANGE 6, M3 2, DEPTH 1, M2_CEIL 1, RSI_NOW 1, UNIVERSE 1 (of 24 cases).

Case notes:
- **IPDN_E1** (M4_RANGE): a reverse split falls inside the 15-bar window but the series is adjusted at that date (no jump): the range is genuine price action, not an adjustment artefact.
- **SXTC_E1** (M2_CEIL): post-split drop 61.4414% is below the floor 71.7203: excluded in either frame — the ceiling name is an adjustment misnomer, not the decisive reason.
- **HUBC_2026-04-24** (M4_RANGE): a reverse split falls inside the 15-bar window but the series is adjusted at that date (no jump): the range is genuine price action, not an adjustment artefact.

## 4. The manual tools (`hand_check.py` · `analyze_one.py`) — the owner's «13 gates»

| displayed gate | inventory id | shown before | shown now | scanner provenance |
|---|---|---|---|---|
| السعر | `M1_PRICE` | hard | hard | INFERRED_FROM_FAISAL_EVIDENCE |
| الهبوط ضمن الأرضية–السقف | `M2_FLOOR / M2_CEIL` | hard | hard | INFERRED_FROM_FAISAL_EVIDENCE / ENGINEERING_GUARD |
| انفجار سابق | `M3_FLOOR` | hard | hard | INFERRED_FROM_FAISAL_EVIDENCE |
| قاعدة ضيقة ولم ينفجر | `M4_RANGE / M4_RISE` | hard | hard | OWNER_POLICY / INFERRED_FROM_FAISAL_EVIDENCE |
| سيولة | `M5_DOLLAR_VOL` | hard | hard | ENGINEERING_GUARD |
| توافق الفريمات | `SOFT_M6_TF` | info | info | INFERRED_FROM_FAISAL_EVIDENCE |
| نمط شمعة انعكاسي | `SOFT_M7_PATTERN` | soft | soft | INFERRED_FROM_FAISAL_EVIDENCE |
| فجوة-هدف فوق السعر | `SOFT_M9_GAP_ABOVE` | soft | soft | INFERRED_FROM_FAISAL_EVIDENCE |
| RSI تشبّع والآن | `M10_RSI_OS / M10_RSI_NOW` | hard | hard | INFERRED_FROM_FAISAL_EVIDENCE / INFERRED_FROM_FAISAL_EVIDENCE |
| تقاطع MACD | `SOFT_M11_MACD` | soft | soft | INFERRED_FROM_FAISAL_EVIDENCE |
| السعر قرب متوسطه 30/50 | `SOFT_M12_EMA` | soft | soft | INFERRED_FROM_FAISAL_EVIDENCE |
| الشورت تحت 40K | `M13_SHORT` | hard | soft | OWNER_POLICY |
| الفلوت تحت 50M | `M14_FLOAT` | hard | hard | OWNER_POLICY |
| مِرساة: قاعٌ مُختبَر | `ANCHOR_TWO_TOUCH` | absent | hard | OWNER_POLICY |
| المتاح للاقتراض 20K أو أقل | `BORROW_AVAIL` | absent | hard | OWNER_POLICY |

Displayed gates now mirror the scanner: M1–M5 + RSI hard (catalog numbers), M6 info at 0, M7/M9/M11/M12 soft, **M13 soft** (was shown hard), **M14 hard**, **borrow hard** (was absent), **anchor hard** (was absent). The verdict line now equals the scanner's post-enrich decision (`post_enrich_verdict`): a stock removed by M14 or the borrow gate is no longer called «مؤهّل — كان سيدخل قائمة المراقبة». Attention (technical identity) and owner eligibility remain one verdict in production; separating them is proposed research-only (no production change).

## 4b. Slot filling after the borrow gate (production logs, recorded in `data/gate_fill_observations.json`)

| date | run | free slots | filled | rounds | ejected by borrow | examined | pool after DQ | unexamined (≤) |
|---|---|---|---|---|---|---|---|---|
| 2026-10-07 | 37589176908 | 8 | 2 | 4 | 28 | 30 | — | — |
| 2026-10-08 | 37747202124 | 6 | 1 | 4 | 23 | 24 | 103 | 79 |
| 2026-10-09 | 37902530011 | 12 | 4 | 4 | 40 | 44 | 104 | 60 |

Over these runs 7 of 26 free slots were filled; the borrow gate ejected 91 of 98 examined (93%), and every run stopped at the rounds cap with qualified names unexamined (the «unexamined» column is an upper bound: names already held or stopped are excluded too). Why these days: the first three runs after the ChartExchange parser fix (2026-10-06, merged in #548): before it, availability was unknown and passed by benefit of the doubt, so the borrow gate did not eject.

## 5. Next permitted action

- The dominant first wall on Faisal's episodes is `ANCHOR_TWO_TOUCH` (owner policy, FROZEN by the H6 control-pool dependency and the perf verdict): no production change is permitted; the admissible evidence is the prospective H6 collection already running.
- `FILL_ROUNDS` × `BORROW_AVAIL` (§4b): the rounds cap, not the pool, ended slot filling in all three post-fix runs. More rounds would push ChartExchange lookups past its ~50-page runner quota, and an unknown availability passes the gate, so raising the cap alone would weaken the borrow gate; harvesting availability for the ranked pool before the screen would not. Either is a change to live candidate generation ⇒ owner decision (and a prereg for a threshold). The new log line (`fill_shortfall_note`) now records the binding cause daily.
- `M2_CEIL` / `M4_RANGE` artefacts on reverse-split names: closed / owner-decided axes; reopening needs the owner.

