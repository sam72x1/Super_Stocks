# 🚪🧭 Gate provenance report — generated (`python3 faisal_engine/gate_inventory.py`)

Research only. Generated from `faisal_engine/data/gate_provenance.json` (curated evidence), the code (AST anchors, live
production configuration `FAISAL_ONLY=1`), a frozen snapshot of `reject_log.json`, and the frozen ranking bars. Every number below is produced by the builder; `--check` regenerates and compares. Line numbers are as of the build and move with edits (the check verifies each anchor still sits inside its function).

**49 gates inventoried** · reject codes in `analyze_ticker`: 19 (all inventoried) · silent `return None` paths: 3 (all inventoried) · build errors: 0

## 1. The decision questions

1. **Active rejecting gates with direct Faisal-source support (concept, every number and the hard role):** none.
2. **Active rejecting gates with partial support only** (some part — the concept, a number or the hard role — is supported, but not every part by one kind of evidence; a supported concept does not support the exact threshold): `M1_PRICE`, `M2_FLOOR`, `M3_FLOOR`, `M4_RANGE`, `M4_RANGE_PULLBACK`, `M4_RISE`, `M5_DOLLAR_VOL`, `M10_RSI_OS`, `M10_RSI_NOW`, `SOFT_COUNT`, `SCORE_MIN`, `ANCHOR_TWO_TOUCH`, `RR_SOFT_COUNT`, `M14_FLOAT`, `TIER`, `M14_REFLOAT`.
3. **Justified as engineering guards** (documented operational invariant or tested reliability requirement): `D_ADJUST`, `M2_HI52_GUARD`, `M4_BASE_LO_GUARD`, `PULLBACK_NOT_RISEN`, `ANALYZE_EXCEPTION`, `BORROW_SECOND_CHANCE` · **guards whose concept is supported but whose number is not:** `D_DEPTH`, `DQ_GATE`, `COVERAGE_GUARD`, `FILL_ROUNDS` · **explicit owner requirement** (owner policy — not Faisal's method): `U_NASDAQ`, `M2_CEIL`, `NEAR_READINESS`, `RANK_KEY`, `CAPACITY_SLOTS`, `BORROW_AVAIL`, `HC_GATE_DISPLAY`, `HC_VERDICT`.
4. **Possible data/adjustment/order artefacts or frame differences:** `D_DEPTH`, `D_ADJUST`, `M2_CEIL`, `M2_FLOOR`, `DQ_GATE`, `FILL_ROUNDS`, `BORROW_AVAIL`; cases whose first wall is an artefact: none.
5. **Without supporting evidence (UNJUSTIFIED_BY_CURRENT_EVIDENCE or UNKNOWN):** `M8_GAP_REQUIRED`, `M13_SHORT`, `STOPPED_EXCLUSION` — the absence of a Faisal source, a code comment or an inherited record is never read as support (`gate_audit.derive_justification`).
6. **Change the candidate set** (hard, active): `U_NASDAQ`, `D_DEPTH`, `M1_PRICE`, `M2_HI52_GUARD`, `M2_CEIL`, `M2_FLOOR`, `M3_FLOOR`, `M4_BASE_LO_GUARD`, `M4_RANGE`, `M4_RANGE_PULLBACK`, `M4_RISE`, `M5_DOLLAR_VOL`, `M10_RSI_OS`, `M10_RSI_NOW`, `SOFT_COUNT`, `SCORE_MIN`, `ANCHOR_TWO_TOUCH`, `RR_SOFT_COUNT`, `ANALYZE_EXCEPTION`, `M14_FLOAT`, `TIER`, `DQ_GATE`, `COVERAGE_GUARD`, `STOPPED_EXCLUSION`, `CAPACITY_SLOTS`, `FILL_ROUNDS`, `M14_REFLOAT`, `BORROW_AVAIL` · **ranking only:** `RANK_KEY` · **display/readiness only:** `ENTRY_STATUS`, `HC_GATE_DISPLAY`, `HC_VERDICT` · **soft (count toward `SOFT_COUNT`):** `SOFT_M10_RSI`, `SOFT_M11_MACD`, `SOFT_M12_EMA`, `SOFT_M2_IDEAL`, `SOFT_M3_IDEAL`, `SOFT_M6_TF`, `SOFT_M7_PATTERN`, `SOFT_M9_GAP_ABOVE`, `M13_SHORT`.
7. **Contradicted by a Faisal source** (concept or number): `D_ADJUST`, `M1_PRICE`, `M2_CEIL`, `M4_RISE`, `M5_DOLLAR_VOL`, `M10_RSI_NOW`, `ANCHOR_TWO_TOUCH`, `M13_SHORT`.
8. **Highest-value permitted next action:** see §5.

## 2. Gate table (pipeline order) — four independent dimensions

Origin = where the rule came from · justification = what currently supports the rule **as implemented** (derived from the evidence attached to its concept, to every number and, for rejecting roles, to the hard role) · role = what it does · fidelity = how it maps to Faisal's method. None of the four stands in for another.

| # | gate | where (as of build) | role | origin | justification | fidelity | contradicted | status | live value | prod/day (median · 10-09) |
|---|---|---|---|---|---|---|---|---|---|---|
| 10 | `U_NASDAQ` | `Super_stock.py::get_universe` L1732 | OWNER_TRADING_ELIGIBILITY | EXPLICIT_OWNER_POLICY | EXPLICIT_OWNER_REQUIREMENT | NO_DEFENSIBLE_MAPPING |  | OWNER_DECIDED | — | — |
| 20 | `D_DEPTH` | `Super_stock.py::_extract_into` L1813 | DATA_QUALITY | INHERITED_OR_EXTERNAL | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | NO_DEFENSIBLE_MAPPING |  | OPEN | MIN_BARS=120 | — |
| 25 | `D_ADJUST` | `Super_stock.py::tv_download` L2143 | DATA_QUALITY | INHERITED_OR_EXTERNAL | DOCUMENTED_OPERATIONAL_INVARIANT | NO_DEFENSIBLE_MAPPING | yes | OPEN | — | — |
| 30 | `M1_PRICE` | `Super_stock.py::analyze_ticker` L4046 | HARD_REJECTION | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | SAMPLE_NUMERICAL_RELATIONSHIP | yes | OPEN | MIN_PRICE=0.4 | 78 · 81 |
| 31 | `M2_HI52_GUARD` | `Super_stock.py::analyze_ticker` L4068 | OPS_SAFETY | INHERITED_OR_EXTERNAL | DOCUMENTED_OPERATIONAL_INVARIANT | NO_DEFENSIBLE_MAPPING |  | OPEN | — | 0 · 0 |
| 32 | `M2_CEIL` | `Super_stock.py::analyze_ticker` L4071 | HARD_REJECTION | INHERITED_OR_EXTERNAL | EXPLICIT_OWNER_REQUIREMENT | NO_DEFENSIBLE_MAPPING | yes | CLOSED | MAX_DROP_PCT=99.95 | 23 · 22 |
| 33 | `M2_FLOOR` | `Super_stock.py::analyze_ticker` L4073 | HARD_REJECTION | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | SAMPLE_NUMERICAL_RELATIONSHIP |  | CLOSED | MIN_DROP_FLOOR=71.7203 | 2643 · 2612 |
| 34 | `M3_FLOOR` | `Super_stock.py::analyze_ticker` L4085 | HARD_REJECTION | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | SAMPLE_NUMERICAL_RELATIONSHIP |  | OPEN | PRIOR_SPIKE_FLOOR=78.2738 · PRIOR_SPIKE_WINDOW=20 · BASE_WINDOW=15 | 66 · 71 |
| 35 | `M4_BASE_LO_GUARD` | `Super_stock.py::analyze_ticker` L4095 | OPS_SAFETY | INHERITED_OR_EXTERNAL | DOCUMENTED_OPERATIONAL_INVARIANT | NO_DEFENSIBLE_MAPPING |  | OPEN | — | 0 · 0 |
| 36 | `M4_RANGE` | `Super_stock.py::analyze_ticker` L4117 | HARD_REJECTION | INHERITED_OR_EXTERNAL | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | NO_DEFENSIBLE_MAPPING |  | OWNER_DECIDED | BASE_RANGE_MAX_PCT=120 · BASE_WINDOW=15 | 77 · 88 |
| 37 | `M4_RANGE_PULLBACK` | `Super_stock.py::analyze_ticker` L4128 | HARD_REJECTION | EXPLICIT_OWNER_POLICY | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | NO_DEFENSIBLE_MAPPING |  | OWNER_DECIDED | — | 0 · 0 |
| 38 | `M4_RISE` | `Super_stock.py::analyze_ticker` L4139 | HARD_REJECTION | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | SAMPLE_NUMERICAL_RELATIONSHIP | yes | OPEN | RECENT_RISE_BLOCK_PCT=214.7287 | 0 · 0 |
| 39 | `M5_DOLLAR_VOL` | `Super_stock.py::analyze_ticker` L4144 | HARD_REJECTION | INHERITED_OR_EXTERNAL | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | NO_DEFENSIBLE_MAPPING | yes | OPEN | MIN_DOLLAR_VOL=14314.7701 | 7 · 5 |
| 40 | `M8_GAP_REQUIRED` | `Super_stock.py::analyze_ticker` L4166 | HARD_REJECTION | INHERITED_OR_EXTERNAL | UNJUSTIFIED_BY_CURRENT_EVIDENCE | NO_DEFENSIBLE_MAPPING |  | INACTIVE | GAP_REQUIRED=False | — |
| 41 | `M10_RSI_OS` | `Super_stock.py::analyze_ticker` L4194 | HARD_REJECTION | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | SAMPLE_NUMERICAL_RELATIONSHIP |  | CLOSED | RSI_OS_HARD=69 · RSI_OS_LOOKBACK=25 | 0 · 0 |
| 42 | `M10_RSI_NOW` | `Super_stock.py::analyze_ticker` L4201 | HARD_REJECTION | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | SAMPLE_NUMERICAL_RELATIONSHIP | yes | CLOSED | RSI_NOW_HARD=71.1186 | 2 · 3 |
| 43 | `SOFT_COUNT` | `Super_stock.py::analyze_ticker` L4244 | HARD_REJECTION | ENGINEERING_INTRODUCED | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | NO_DEFENSIBLE_MAPPING |  | OPEN | WATCH_MAX_FAILS=8 | 0 · 0 |
| 44 | `STABILITY_BT` | `Super_stock.py::analyze_ticker` L4338 | OTHER | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | CONCEPT_ONLY |  | CLOSED | BT_STABILITY_GATE= · STABILITY_MIN=3 | 0 · 0 |
| 45 | `NEAR_READINESS` | `Super_stock.py::analyze_ticker` L4355 | HARD_REJECTION | INHERITED_OR_EXTERNAL | EXPLICIT_OWNER_REQUIREMENT | NO_DEFENSIBLE_MAPPING |  | INACTIVE | NEAR_PCT=0 | 0 · 0 |
| 46 | `SCORE_MIN` | `Super_stock.py::analyze_ticker` L4499 | HARD_REJECTION | INHERITED_OR_EXTERNAL | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | NO_DEFENSIBLE_MAPPING |  | OPEN | SCORE_MIN=5 | 4 · 8 |
| 47 | `ANCHOR_TWO_TOUCH` | `Super_stock.py::analyze_ticker` L4541 | HARD_REJECTION | EXPLICIT_OWNER_POLICY | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | CONCEPT_ONLY | yes | FROZEN | ANCHOR_MODE=tested_strict | 395 · 407 |
| 48 | `RR_SOFT_COUNT` | `Super_stock.py::analyze_ticker` L4758 | HARD_REJECTION | INHERITED_OR_EXTERNAL | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | NO_DEFENSIBLE_MAPPING |  | OPEN | MIN_RR_T1=0.5 · WATCH_MAX_FAILS=8 | 0 · 0 |
| 49 | `PULLBACK_NOT_RISEN` | `Super_stock.py::analyze_ticker` L4791 | OTHER | ENGINEERING_INTRODUCED | DOCUMENTED_OPERATIONAL_INVARIANT | NO_DEFENSIBLE_MAPPING |  | OPEN | — | — |
| 50 | `ANALYZE_EXCEPTION` | `Super_stock.py::analyze_ticker` L4834 | OPS_SAFETY | INHERITED_OR_EXTERNAL | DOCUMENTED_OPERATIONAL_INVARIANT | NO_DEFENSIBLE_MAPPING |  | OPEN | — | — |
| 60 | `SOFT_M10_RSI` | `Super_stock.py::analyze_ticker` L4198 | SOFT | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | SAMPLE_NUMERICAL_RELATIONSHIP |  | OPEN | RSI_OVERSOLD=33 · RSI_MAX_NOW=35.7789 | — |
| 60 | `SOFT_M11_MACD` | `Super_stock.py::analyze_ticker` L4213 | SOFT | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | CONCEPT_ONLY |  | OPEN | MACD_GATE_REQUIRED=True | — |
| 60 | `SOFT_M12_EMA` | `Super_stock.py::analyze_ticker` L4240 | SOFT | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | SAMPLE_NUMERICAL_RELATIONSHIP |  | OPEN | MA_GATE_REQUIRED=True · MA_GATE_MAX_ABOVE_PCT=95.4707 | — |
| 60 | `SOFT_M2_IDEAL` | `Super_stock.py::analyze_ticker` L4079 | SOFT | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | CONCEPT_ONLY |  | OPEN | MIN_DROP_PCT=96.9178 | — |
| 60 | `SOFT_M3_IDEAL` | `Super_stock.py::analyze_ticker` L4088 | SOFT | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | CONCEPT_ONLY |  | OPEN | PRIOR_SPIKE_PCT=164.0212 | — |
| 60 | `SOFT_M6_TF` | `Super_stock.py::analyze_ticker` L4150 | SOFT | INHERITED_OR_EXTERNAL | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | NO_DEFENSIBLE_MAPPING |  | INACTIVE | TF_MIN_REVERSALS=0 | — |
| 60 | `SOFT_M7_PATTERN` | `Super_stock.py::analyze_ticker` L4155 | SOFT | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | CONCEPT_ONLY |  | OPEN | — | — |
| 60 | `SOFT_M9_GAP_ABOVE` | `Super_stock.py::analyze_ticker` L4180 | SOFT | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | SAMPLE_NUMERICAL_RELATIONSHIP |  | OPEN | GAP_ABOVE_REQUIRED=True · GAP_ABOVE_MAX_DIST_PCT=1134.7826 | — |
| 70 | `M13_SHORT` | `Super_stock.py::apply_short_gate` L12602 | SOFT | INHERITED_OR_EXTERNAL | UNJUSTIFIED_BY_CURRENT_EVIDENCE | NO_DEFENSIBLE_MAPPING | yes | OWNER_DECIDED | SHORT_GATE_MAX=40000 · SHORT_GATE_REQUIRED=True | — |
| 71 | `M14_FLOAT` | `Super_stock.py::apply_float_gate` L12672 | OWNER_TRADING_ELIGIBILITY | EXPLICIT_OWNER_POLICY | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | CONCEPT_ONLY |  | OWNER_DECIDED | FLOAT_GATE_MAX=50000000 · FLOAT_GATE_REQUIRED=True | — |
| 72 | `TIER` | `Super_stock.py::classify_tier` L12973 | HARD_REJECTION | ENGINEERING_INTRODUCED | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | NO_DEFENSIBLE_MAPPING |  | OPEN | WATCH_MAX_FAILS=8 | — |
| 73 | `RANK_KEY` | `Super_stock.py::rank_key` L12995 | RANKING | ENGINEERING_INTRODUCED | EXPLICIT_OWNER_REQUIREMENT | NO_DEFENSIBLE_MAPPING |  | CLOSED | — | — |
| 80 | `DQ_GATE` | `Super_stock.py::dq_filter` L2429 | DATA_QUALITY | EXPLICIT_OWNER_POLICY | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | NO_DEFENSIBLE_MAPPING |  | OWNER_DECIDED | DQ_GATE=None · DQ_POLICY=None | — |
| 81 | `COVERAGE_GUARD` | `Super_stock.py::run_daily_watchlist` L22144 | DATA_QUALITY | ENGINEERING_INTRODUCED | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | NO_DEFENSIBLE_MAPPING |  | OPEN | DATA_HEALTH_MIN_PCT=85 | — |
| 82 | `STOPPED_EXCLUSION` | `Super_stock.py::run_daily_watchlist` L22148 | HARD_REJECTION | INHERITED_OR_EXTERNAL | UNJUSTIFIED_BY_CURRENT_EVIDENCE | NO_DEFENSIBLE_MAPPING |  | OPEN | EXCLUDE_STOPPED_FROM_RENEWAL=True | — |
| 83 | `CAPACITY_SLOTS` | `Super_stock.py::run_daily_watchlist` L22177 | OTHER | EXPLICIT_OWNER_POLICY | EXPLICIT_OWNER_REQUIREMENT | NO_DEFENSIBLE_MAPPING |  | OWNER_DECIDED | WATCHLIST_SIZE=15 | — |
| 84 | `FILL_ROUNDS` | `Super_stock.py::fill_picks` L12893 | OPS_SAFETY | EXPLICIT_OWNER_POLICY | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | NO_DEFENSIBLE_MAPPING |  | OPEN | PICK_FILL_ROUNDS=4 | — |
| 85 | `M14_REFLOAT` | `Super_stock.py::refloat_gate_recheck` L12761 | OWNER_TRADING_ELIGIBILITY | EXPLICIT_OWNER_POLICY | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | CONCEPT_ONLY |  | OWNER_DECIDED | FLOAT_GATE_MAX=50000000 | — |
| 86 | `BORROW_SECOND_CHANCE` | `Super_stock.py::borrow_second_chance` L12810 | DATA_QUALITY | ENGINEERING_INTRODUCED | TESTED_RELIABILITY_REQUIREMENT | NO_DEFENSIBLE_MAPPING |  | OPEN | — | — |
| 87 | `BORROW_AVAIL` | `Super_stock.py::borrow_gate_recheck` L12800 | OWNER_TRADING_ELIGIBILITY | EXPLICIT_OWNER_POLICY | EXPLICIT_OWNER_REQUIREMENT | SUPPORTED_RECONSTRUCTION |  | OWNER_DECIDED | BORROW_AVAIL_MAX=20000 · BORROW_GATE_REQUIRED=True | — |
| 90 | `ENTRY_STATUS` | `Super_stock.py::entry_status` L14951 | NOTIFICATION_ELIGIBILITY | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | CONCEPT_ONLY |  | OPEN | — | — |
| 95 | `HC_GATE_DISPLAY` | `analyze_one.py::append_short_float_gates` L709 | DISPLAY | EXPLICIT_OWNER_POLICY | EXPLICIT_OWNER_REQUIREMENT | NO_DEFENSIBLE_MAPPING |  | OPEN | — | — |
| 96 | `HC_VERDICT` | `analyze_one.py::post_enrich_verdict` L746 | DISPLAY | EXPLICIT_OWNER_POLICY | EXPLICIT_OWNER_REQUIREMENT | NO_DEFENSIBLE_MAPPING |  | OPEN | — | — |
| 97 | `RESEARCH_ENGINE` | `faisal_engine/engine.py::evaluate` L142 | OTHER | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | CONCEPT_ONLY |  | OPEN | — | — |
| 98 | `V4_FROZEN` | `faisal_method_v4/decision_engine.py::analyze` L215 | OTHER | INFERRED_FROM_FAISAL_SOURCE | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | CONCEPT_ONLY |  | FROZEN | — | — |

## 2b. What changed against the single label of PR #598

PR #598 gave each gate one label and read «no Faisal source» as an engineering guard. Rows = that label; columns = the justification derived now from the evidence (counts of gates).

| PR #598 label | Direct Source Support | Explicit Owner Requirement | Documented Operational Invariant | Tested Reliability Requirement | Empirical Support Under Valid Contract | Partial Or Concept Only Support | Unjustified By Current Evidence | Unknown |
|---|---|---|---|---|---|---|---|---|
| DIRECT_FAISAL_EVIDENCE | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |
| INFERRED_FROM_FAISAL_EVIDENCE | 0 | 0 | 0 | 0 | 0 | 17 | 0 | 0 |
| OWNER_POLICY | 0 | 5 | 0 | 0 | 0 | 6 | 1 | 0 |
| ENGINEERING_GUARD | 0 | 3 | 5 | 1 | 0 | 8 | 2 | 0 |

Gates whose old label does not hold (20): an owner label without a full owner requirement, or an engineering label without a documented invariant or a tested requirement.

| gate | PR #598 label | origin now | justification now | change | why |
|---|---|---|---|---|---|
| `D_DEPTH` | ENGINEERING_GUARD | INHERITED_OR_EXTERNAL | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | support was overstated | the indicators need ≈50+ bars; nothing derives 120 |
| `M2_CEIL` | ENGINEERING_GUARD | INHERITED_OR_EXTERNAL | EXPLICIT_OWNER_REQUIREMENT | re-attributed to the owner (not an engineering guard) | owner-required; contradicted by Faisal's post-split frame (closed axis) |
| `M4_RANGE` | OWNER_POLICY | INHERITED_OR_EXTERNAL | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | support was overstated | the owner set the number; no source supports a range cap as a concept |
| `M4_RANGE_PULLBACK` | OWNER_POLICY | EXPLICIT_OWNER_POLICY | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | support was overstated | pullback routing policy; the half-range split is a disclosed design choice |
| `M5_DOLLAR_VOL` | ENGINEERING_GUARD | INHERITED_OR_EXTERNAL | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | support was overstated | the concept is contradicted as identity evidence; only the number is owner-adopted |
| `M8_GAP_REQUIRED` | ENGINEERING_GUARD | INHERITED_OR_EXTERNAL | UNJUSTIFIED_BY_CURRENT_EVIDENCE | support was overstated | inactive (GAP_REQUIRED=False) |
| `SOFT_COUNT` | ENGINEERING_GUARD | ENGINEERING_INTRODUCED | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | support was overstated | unsupported: concept, hardness |
| `NEAR_READINESS` | ENGINEERING_GUARD | INHERITED_OR_EXTERNAL | EXPLICIT_OWNER_REQUIREMENT | re-attributed to the owner (not an engineering guard) | inactive (catalogue edge 0) |
| `SCORE_MIN` | ENGINEERING_GUARD | INHERITED_OR_EXTERNAL | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | support was overstated | unsupported: concept, hardness |
| `ANCHOR_TWO_TOUCH` | OWNER_POLICY | EXPLICIT_OWNER_POLICY | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | support was overstated | his rule is for the entry and the stop; applied here as candidate rejection (FROZEN by the H6 control pool) |
| `RR_SOFT_COUNT` | ENGINEERING_GUARD | INHERITED_OR_EXTERNAL | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | support was overstated | unsupported: concept, hardness |
| `M13_SHORT` | OWNER_POLICY | INHERITED_OR_EXTERNAL | UNJUSTIFIED_BY_CURRENT_EVIDENCE | support was overstated | PR #598 called this owner policy; no owner order sets 40,000 — tightening experiments were null and the number stayed |
| `M14_FLOAT` | OWNER_POLICY | EXPLICIT_OWNER_POLICY | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | support was overstated | his number is 2M for the split-stock recipe; 50M is ours |
| `TIER` | ENGINEERING_GUARD | ENGINEERING_INTRODUCED | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | support was overstated | unsupported: concept, hardness |
| `RANK_KEY` | ENGINEERING_GUARD | ENGINEERING_INTRODUCED | EXPLICIT_OWNER_REQUIREMENT | re-attributed to the owner (not an engineering guard) | ranking is ours; the proximity-first order is the owner's choice |
| `DQ_GATE` | OWNER_POLICY | EXPLICIT_OWNER_POLICY | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | support was overstated | owner mission; its release condition borrows the split-stock recipe |
| `COVERAGE_GUARD` | ENGINEERING_GUARD | ENGINEERING_INTRODUCED | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | support was overstated | unsupported: threshold:DATA_HEALTH_MIN_PCT |
| `STOPPED_EXCLUSION` | ENGINEERING_GUARD | INHERITED_OR_EXTERNAL | UNJUSTIFIED_BY_CURRENT_EVIDENCE | support was overstated | unsupported: concept, threshold:EXCLUDE_STOPPED_FROM_RENEWAL, hardness |
| `FILL_ROUNDS` | ENGINEERING_GUARD | EXPLICIT_OWNER_POLICY | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | support was overstated | the owner ordered refilling; the cap 4 is ours (quota ≈50 pages per runner) |
| `M14_REFLOAT` | OWNER_POLICY | EXPLICIT_OWNER_POLICY | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | support was overstated | unsupported: threshold:FLOAT_GATE_MAX |

## 3. First exclusion per Faisal episode (frozen bars < T, production `analyze_ticker`)

The cause is the **first** wall; the chain lists what would block next if each wall were neutralised (research only).

| case | T | first wall | value · threshold | case class | chain | frozen replay | operational list |
|---|---|---|---|---|---|---|---|
| AMIX_E1 | 2026-08-24 | M4_RANGE | 703.9088 · BASE_RANGE_MAX_PCT 120 | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | M4_RANGE → ANCHOR → PASS | match | 0 |
| ATPC_E1 | 2026-09-14 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | ANCHOR → PASS | match | 0 |
| BRTX_E1 | 2026-10-05 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | ANCHOR → PASS | match | 0 |
| CETX_E1 | 2026-09-14 | PASS |  ·  | PASS |  → PASS | match | 1 |
| CIIT_E1 | 2026-09-25 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | ANCHOR → PASS | match | 0 |
| CUPR_E1 | 2026-09-14 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | ANCHOR → PASS | match | 0 |
| DCOY_E1 | 2026-09-22 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | ANCHOR → PASS | match | 0 |
| DKI_E1 | 2026-09-14 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | ANCHOR → PASS | match | 0 |
| EDBL_E1 | 2026-09-22 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | ANCHOR → PASS | match | 0 |
| GCTK_E1 | 2026-09-24 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | ANCHOR → PASS | match | 0 |
| IPDN_E1 | 2026-09-23 | M4_RANGE | 122.9428 · BASE_RANGE_MAX_PCT 120 | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | M4_RANGE → ANCHOR → PASS | match | 0 |
| LABT_E1 | 2026-08-24 | DEPTH | 84 · MIN_BARS 120 | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | DEPTH → ANCHOR → PASS | match | 0 |
| LIMN_E1 | 2026-09-22 | PASS |  ·  | PASS |  → PASS | match | 1 |
| MI_E1 | 2026-09-28 | UNIVERSE |  ·  | EXPLICIT_OWNER_REQUIREMENT | UNIVERSE → M3 → PASS | — | — |
| MSGY_E1 | 2026-09-14 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | ANCHOR → PASS | match | 0 |
| NRSN_E1 | 2026-09-28 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | ANCHOR → PASS | match | 0 |
| NUWE_E1 | 2026-09-04 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | ANCHOR → PASS | match | 0 |
| OMH_E1 | 2026-09-28 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | ANCHOR → PASS | match | 0 |
| PPBT_E1 | 2026-09-04 | RSI_NOW | 71.8977 · RSI_NOW_HARD 71.1186 | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | RSI_NOW → ANCHOR → PASS | match | 0 |
| STKH_E1 | 2026-09-04 | M4_RANGE | 172.2944 · BASE_RANGE_MAX_PCT 120 | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | M4_RANGE → ANCHOR → PASS | match | 0 |
| SVRE_E1 | 2026-09-14 | ANCHOR | 1 · ≥2 independent touches of the 30-bar low (±1.5%) | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | ANCHOR → PASS | match | 0 |
| SXTC_E1 | 2026-09-10 | M2_CEIL | 99.9974 · MAX_DROP_PCT 99.95 | EXPLICIT_OWNER_REQUIREMENT | M2_CEIL → M4_RANGE → ANCHOR → PASS | match | 0 |
| YMT_E1 | 2026-09-04 | M3 | 72.9819 · PRIOR_SPIKE_FLOOR 78.2738 | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | M3 → M4_RANGE → ANCHOR → PASS | match | 0 |
| HUBC_2026-04-24 | 2026-04-24 | M4_RANGE | 1012.8931 · BASE_RANGE_MAX_PCT 120 | PARTIAL_OR_CONCEPT_ONLY_SUPPORT | M4_RANGE → ANCHOR → PASS | — | — |

First-wall counts: ANCHOR 13, M4_RANGE 4, PASS 2, DEPTH 1, M2_CEIL 1, M3 1, RSI_NOW 1, UNIVERSE 1 · replay mismatches against the frozen ranking rows: 0 · walls present anywhere in a chain: ANCHOR 21, M4_RANGE 6, M3 2, DEPTH 1, M2_CEIL 1, RSI_NOW 1, UNIVERSE 1 (of 24 cases).

Case notes:
- **IPDN_E1** (M4_RANGE): a reverse split falls inside the 15-bar window but the series is adjusted at that date (no jump): the range is genuine price action, not an adjustment artefact.
- **SXTC_E1** (M2_CEIL): post-split drop 61.4414% is below the floor 71.7203: excluded in either frame — the ceiling name is an adjustment misnomer, not the decisive reason.
- **HUBC_2026-04-24** (M4_RANGE): a reverse split falls inside the 15-bar window but the series is adjusted at that date (no jump): the range is genuine price action, not an adjustment artefact.

## 3b. Exact thresholds of the active gates that reject, guard data or bound the list

One row per number. **number origin** is where the exact value came from (Faisal source · owner · catalogue percentile · inferred · engineering default · inherited · experiment · unexplained) — independent of where the concept came from. A catalogue percentile is a number fitted to his chosen stocks under the owner's 2026-08-06 order, not a number he stated.

| gate | key | live value | concept | window | measurement basis | data at decision | pipeline point | why hard (not soft) | number origin | evidence |
|---|---|---|---|---|---|---|---|---|---|---|
| `U_NASDAQ` | `UNIVERSE` | nasdaqlisted.txt | NASDAQ-listed symbols only | the universe list fetched each run | nasdaqtrader nasdaqlisted.txt | the symbol directory at run time | get_universe — before any data is loaded | the exchange restriction was an explicit request recorded in the initial upload | OWNER | O_NASDAQ_V23 |
| `D_DEPTH` | `MIN_BARS` | 120 | minimum daily history for the indicators | whole downloaded history | count of daily bars | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | _extract_into — data loading, before analyze_ticker | a symbol below the count is dropped before analysis (silent in the reject log) | INHERITED | V23_MIN_BARS |
| `D_ADJUST` | `—` | — | split-adjusted economic frame; Faisal reads reverse-split names in the post-split frame (frame difference, not a data error) | — | — | — | tv_download | — | — | I_ADJUSTED · X_POST_SPLIT_FRAME |
| `M1_PRICE` | `MIN_PRICE` | 0.4 | price floor | last close | last daily close | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | kept strict as the identity block since v2.7; no Faisal or owner statement makes it hard rather than soft | CATALOG_PERCENTILE | S_ENV_P100 · O_FAISAL_ONLY_0806 · O_P100_0808 · X_M1_SCOPE |
| `M2_HI52_GUARD` | `—` | — | no numeric threshold | — | — | — | analyze_ticker | — | — | I_DIV_HI52 |
| `M2_CEIL` | `MAX_DROP_PCT` | 99.95 | exclude dying / split-trap names | 252 bars | (1 − close ÷ max(high, 252 bars)) on split-adjusted bars | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | the owner kept the ceiling as a hard wall after T-CEILING measured its cost | CATALOG_PERCENTILE | S_ENV_P100 · O_FAISAL_ONLY_0806 · O_P100_0808 |
| `M2_FLOOR` | `MIN_DROP_FLOOR` | 71.7203 | collapsed far from the 52-week high | 252 bars | (1 − close ÷ max(high, 252 bars)) on split-adjusted bars | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | kept strict as the identity block since v2.7; no Faisal or owner statement makes it hard rather than soft | CATALOG_PERCENTILE | S_ENV_P100 · O_FAISAL_ONLY_0806 · O_P100_0808 |
| `M3_FLOOR` | `PRIOR_SPIKE_FLOOR` | 78.2738 | exploded before | spike within PRIOR_SPIKE_WINDOW sessions, excluding the last BASE_WINDOW bars | best low-to-high rise of daily closes (spike_info) | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | kept strict as the identity block since v2.7; no Faisal or owner statement makes it hard rather than soft | CATALOG_PERCENTILE | S_ENV_P100 · O_FAISAL_ONLY_0806 · O_P100_0808 |
| `M3_FLOOR` | `PRIOR_SPIKE_WINDOW` | 20 | speed of the prior explosion | 20 sessions | sessions from base to peak | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | kept strict as the identity block since v2.7; no Faisal or owner statement makes it hard rather than soft | INHERITED | V23_PRIOR_SPIKE_WINDOW |
| `M3_FLOOR` | `BASE_WINDOW` | 15 | the current base excluded from the spike search | 15 sessions | last 15 daily bars | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | kept strict as the identity block since v2.7; no Faisal or owner statement makes it hard rather than soft | INHERITED | V23_BASE_WINDOW |
| `M4_BASE_LO_GUARD` | `—` | — | no numeric threshold | — | — | — | analyze_ticker | — | — | I_DIV_BASELO |
| `M4_RANGE` | `BASE_RANGE_MAX_PCT` | 120 | narrow current base | 15 sessions | (max high ÷ min low − 1) over the last 15 bars | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | kept strict as the identity block since v2.7; no Faisal or owner statement makes it hard rather than soft | OWNER | O_BASE120_0810 · E_TBASE2 |
| `M4_RANGE` | `BASE_WINDOW` | 15 | base window | 15 sessions | last 15 daily bars | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | kept strict as the identity block since v2.7; no Faisal or owner statement makes it hard rather than soft | INHERITED | V23_BASE_WINDOW |
| `M4_RANGE_PULLBACK` | `base_rose` | half of the range | a wide base is a pullback candidate only when the price rose | 15 sessions | close in the upper half of the 15-bar range | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker pullback mode | «اقفل الباب»: a falling wide base is rejected | ENGINEERING_DEFAULT | R_MIDPOINT |
| `M4_RISE` | `RECENT_RISE_BLOCK_PCT` | 214.7287 | do not chase a name that already exploded | 5 sessions | close ÷ close 5 sessions earlier − 1 | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | kept strict as the identity block since v2.7; no Faisal or owner statement makes it hard rather than soft | CATALOG_PERCENTILE | S_ENV_P100 · O_FAISAL_ONLY_0806 · O_P100_0808 |
| `M5_DOLLAR_VOL` | `MIN_DOLLAR_VOL` | 14314.7701 | tradability floor | 20 sessions | mean of close × volume over 20 daily bars | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | kept strict as the identity block since v2.7; no Faisal or owner statement makes it hard rather than soft | CATALOG_PERCENTILE | S_ENV_P100 · O_FAISAL_ONLY_0806 · O_P100_0808 |
| `M10_RSI_OS` | `RSI_OS_HARD` | 69 | the RSI reached oversold before the move | RSI_OS_LOOKBACK sessions | minimum RSI(14) over the window | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | split into hard/soft in v2.7; no source makes the floor hard | CATALOG_PERCENTILE | S_ENV_P100 · O_FAISAL_ONLY_0806 · O_P100_0808 |
| `M10_RSI_OS` | `RSI_OS_LOOKBACK` | 25 | how recent the oversold touch must be | 25 sessions | trailing daily bars | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | kept strict as the identity block since v2.7; no Faisal or owner statement makes it hard rather than soft | ENGINEERING_DEFAULT | R_RSI_V27 |
| `M10_RSI_NOW` | `RSI_NOW_HARD` | 71.1186 | not already flown | last bar | RSI(14) of the last close | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | split into hard/soft in v2.7; tightening to his 40 was measured and the axis closed | CATALOG_PERCENTILE | S_ENV_P100 · O_FAISAL_ONLY_0806 · O_P100_0808 |
| `SOFT_COUNT` | `WATCH_MAX_FAILS` | 8 | too many missing confirmations | all soft gates of the current bar | count of soft fails | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | a count limit rejects by definition (v2.7 design) | CATALOG_PERCENTILE | S_ENV_P100 · O_FAISAL_ONLY_0806 · O_P100_0808 |
| `STABILITY_BT` | `STABILITY_MIN` | 3 | held its low for three sessions | sessions after the pivot low | pivot_stability bars_after | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | backtest arm only (BT_STABILITY_GATE); never active in production | FAISAL_SOURCE | F_IMG0151_RECIPE |
| `SCORE_MIN` | `SCORE_MIN` | 5 | enough confirmations | last bar | additive score of the signal flags | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | inherited from v2.3; no source makes it hard | CATALOG_PERCENTILE | S_ENV_P100 · O_FAISAL_ONLY_0806 · O_P100_0808 |
| `ANCHOR_TWO_TOUCH` | `ANCHOR_MODE` | tested_strict | anchor on a tested level; reject when none | — | tested_strict | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | the owner chose the strict arm (reject without a tested level) | OWNER | O_ANCHOR_0814 |
| `ANCHOR_TWO_TOUCH` | `min_touches` | 2 | tested twice | lookback | independent touch clusters within the tolerance | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | kept strict as the identity block since v2.7; no Faisal or owner statement makes it hard rather than soft | FAISAL_SOURCE | F_IMG0451_ANCHOR |
| `ANCHOR_TWO_TOUCH` | `lookback` | 30 | where the touches are counted | 30 sessions | trailing daily lows | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | kept strict as the identity block since v2.7; no Faisal or owner statement makes it hard rather than soft | ENGINEERING_DEFAULT | R_ANCHOR_PARAMS |
| `ANCHOR_TWO_TOUCH` | `tol` | 0.015 | what counts as a touch | lookback | low within 1.5% of the window's lowest low | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | kept strict as the identity block since v2.7; no Faisal or owner statement makes it hard rather than soft | ENGINEERING_DEFAULT | R_ANCHOR_PARAMS |
| `RR_SOFT_COUNT` | `MIN_RR_T1` | 0.5 | reward/risk to the first target | last bar | (t1 − price) ÷ (price − stop) | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | kept strict as the identity block since v2.7; no Faisal or owner statement makes it hard rather than soft | CATALOG_PERCENTILE | S_ENV_P100 · O_FAISAL_ONLY_0806 · O_P100_0808 |
| `RR_SOFT_COUNT` | `WATCH_MAX_FAILS` | 8 | count limit after adding the RR fail | soft gates | count of soft fails | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | a count limit rejects by definition (v2.7 design) | CATALOG_PERCENTILE | S_ENV_P100 · O_FAISAL_ONLY_0806 · O_P100_0808 |
| `ANALYZE_EXCEPTION` | `—` | — | no numeric threshold | — | — | — | analyze_ticker | — | — | I_SCAN_CONTINUES |
| `SOFT_M10_RSI` | `RSI_OVERSOLD` | 33 | ideal oversold depth | 25 sessions | minimum RSI(14) | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | soft (counts toward SOFT_COUNT) | CATALOG_PERCENTILE | S_ENV_MEDIAN · O_SOFT_MEDIAN_0807 |
| `SOFT_M10_RSI` | `RSI_MAX_NOW` | 35.7789 | ideal RSI now | last bar | RSI(14) | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | soft (counts toward SOFT_COUNT) | CATALOG_PERCENTILE | S_ENV_MEDIAN · O_SOFT_MEDIAN_0807 |
| `SOFT_M12_EMA` | `MA_GATE_MAX_ABOVE_PCT` | 95.4707 | price based on its EMA30/50 | EMA30/EMA50 | price ÷ EMA − 1 | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | soft (counts toward SOFT_COUNT) | CATALOG_PERCENTILE | S_ENV_P100 · O_FAISAL_ONLY_0806 · O_P100_0808 |
| `SOFT_M2_IDEAL` | `MIN_DROP_PCT` | 96.9178 | ideal collapse | 252 bars | drop from the 52-week high | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | soft (counts toward SOFT_COUNT) | CATALOG_PERCENTILE | S_ENV_MEDIAN · O_SOFT_MEDIAN_0807 |
| `SOFT_M3_IDEAL` | `PRIOR_SPIKE_PCT` | 164.0212 | ideal prior explosion | 20 sessions | spike_info best rise | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | soft (counts toward SOFT_COUNT) | CATALOG_PERCENTILE | S_ENV_MEDIAN · O_SOFT_MEDIAN_0807 |
| `SOFT_M9_GAP_ABOVE` | `GAP_ABOVE_MAX_DIST_PCT` | 1134.7826 | an unfilled gap above as a target | all unfilled gaps | distance to the nearest gap bottom | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | analyze_ticker inside scan_market — per symbol, before ranking | soft (counts toward SOFT_COUNT) | CATALOG_PERCENTILE | S_ENV_P100 · O_FAISAL_ONLY_0806 · O_P100_0808 |
| `M13_SHORT` | `SHORT_GATE_MAX` | 40000 | high short | last FINRA day | FINRA daily short volume (Fintel/FINRA/cache) | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | apply_short_gate inside scan_market | soft (counts toward SOFT_COUNT) | UNEXPLAINED | A_SHORT_40K |
| `M14_FLOAT` | `FLOAT_GATE_MAX` | 50000000 | small float | latest known float | float shares (Yahoo strict · company cache); unknown passes | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | apply_float_gate inside scan_market (known float) | owner 2026-07-29: a known large float is excluded outright | INHERITED | V23_FLOAT_GATE_MAX · R_M14_50M |
| `M14_FLOAT` | `FLOAT_GATE_REQUIRED` | True | the float gate is on | — | switch | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | apply_float_gate · refloat_gate_recheck | owner 2026-07-29: exclude outright | OWNER | O_M14_HARD_0729 |
| `TIER` | `WATCH_MAX_FAILS` | 8 | soft-fail limit after M13/M14 marks | all soft gates | count of soft fails | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | classify_tier after the scan gates | a count limit rejects by definition | CATALOG_PERCENTILE | S_ENV_P100 · O_FAISAL_ONLY_0806 · O_P100_0808 |
| `DQ_GATE` | `DQ_POLICY` | DEFAULT_POLICY | fail-closed action per data state | per run | state → action (allow/warn/quarantine/block) | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | dq_filter after scan_market | blocked/quarantined states are removed before slots | ENGINEERING_DEFAULT | R_DQ_POLICY |
| `DQ_GATE` | `SPLIT_HELD_SESSIONS` | 3 | quarantine after a reverse split ends after three held sessions | sessions after the split | closes held within the ÷2 band | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | data_quality.classify | quarantine release condition | FAISAL_SOURCE | R_DQ_HELD · F_IMG0151_RECIPE |
| `DQ_GATE` | `split_ratio_tol` | 5% | two sources disagree on a split | split events within tol_days | ratio difference | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | data_quality.classify | SOURCE_CONFLICT blocks | ENGINEERING_DEFAULT | R_DQ_RATIO_TOL |
| `DQ_GATE` | `DQ_GATE` | on unless DQ_GATE=0 | the data-quality gate is on | — | environment switch (DQ_GATE=0 restores the previous path bit for bit) | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | dq_filter | owner mission: prefer UNKNOWN to false confidence | OWNER | O_DQ_1001 |
| `COVERAGE_GUARD` | `DATA_HEALTH_MIN_PCT` | 85 | enough of the universe was measured to trust a new list | the run | valid frames ÷ universe | the run's scan statistics | run_weekly_renewal · run_daily_watchlist | below it the renewal is postponed and the daily list is not refilled | ENGINEERING_DEFAULT | R_COVERAGE_85 |
| `STOPPED_EXCLUSION` | `EXCLUDE_STOPPED_FROM_RENEWAL` | True | a stopped name is not re-picked | until the next renewal | status stopped in wl.removed | the watchlist state | run_weekly_renewal · daily fill (exclude set) | inherited switch; no statement makes it a rule | INHERITED | V23_EXCLUDE_STOPPED_FROM_RENEWAL |
| `CAPACITY_SLOTS` | `WATCHLIST_SIZE` | 15 | list capacity | the list | slots minus holders (hit targets free their slot) | the watchlist state | select_top / fill_picks | names beyond the free slots are not listed | OWNER | O_CAP15_0812 |
| `FILL_ROUNDS` | `PICK_FILL_ROUNDS` | 4 | cost cap on refilling slots | one run | rounds of select_top → enrich → M14/borrow rechecks | the ranked pool and ChartExchange lookups | fill_picks | after the last round the remaining slots stay empty | ENGINEERING_DEFAULT | R_FILL_ROUNDS_4 · R_FILL_CAP |
| `M14_REFLOAT` | `FLOAT_GATE_MAX` | 50000000 | small float after enrichment | latest known float | enriched float; unknown passes | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | refloat_gate_recheck after enrich | owner: re-evaluate M14 after enrichment and exclude outright | INHERITED | V23_FLOAT_GATE_MAX · R_M14_50M |
| `BORROW_SECOND_CHANCE` | `—` | — | adds data only (one more lookup for unknown availability) | — | — | — | borrow_second_chance | — | — | T_BSC |
| `BORROW_AVAIL` | `BORROW_AVAIL_MAX` | 20000 | low available-to-borrow | latest harvested/looked-up value | ChartExchange Available (IBKR); unknown passes | today's harvest row, else a live ChartExchange lookup | borrow_gate_recheck after enrich | owner «طبّق 20» made it a hard gate after enrichment | FAISAL_SOURCE | O_BORROW20_0811 · F_IMG0151_RECIPE |
| `BORROW_AVAIL` | `BORROW_GATE_REQUIRED` | True | the borrow gate is on | — | switch | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | borrow_gate_recheck | owner «طبّق 20» | OWNER | O_BORROW20_0811 |
| `ENTRY_STATUS` | `ENTRY_STEP_PCT` | 3 | entry tranches stepped from the anchor | the tranche band | anchor × (1 + step × i) | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | entry_status (daily) | not a rejection: decides «ready now» versus «watch» | INFERRED | F_TRANCHES_EXAMPLE |
| `ENTRY_STATUS` | `far_above` | 5% | too far above the tranches to be ready | last price | price above the top tranche × 1.05 | daily bars dated up to the last completed session at scan time (TradingView, Yahoo per-symbol fallback), split-adjusted | entry_status (daily) | not a rejection: «watch» instead of «ready» | ENGINEERING_DEFAULT | R_ENTRY_FAR |

## 4. The manual tools (`hand_check.py` · `analyze_one.py`) — the owner's «13 gates»

| displayed gate | inventory id | shown before | shown now | origin · justification |
|---|---|---|---|---|
| السعر | `M1_PRICE` | hard | hard | INFERRED_FROM_FAISAL_SOURCE · PARTIAL_OR_CONCEPT_ONLY_SUPPORT |
| الهبوط ضمن الأرضية–السقف | `M2_FLOOR / M2_CEIL` | hard | hard | INFERRED_FROM_FAISAL_SOURCE · PARTIAL_OR_CONCEPT_ONLY_SUPPORT / INHERITED_OR_EXTERNAL · EXPLICIT_OWNER_REQUIREMENT |
| انفجار سابق | `M3_FLOOR` | hard | hard | INFERRED_FROM_FAISAL_SOURCE · PARTIAL_OR_CONCEPT_ONLY_SUPPORT |
| قاعدة ضيقة ولم ينفجر | `M4_RANGE / M4_RISE` | hard | hard | INHERITED_OR_EXTERNAL · PARTIAL_OR_CONCEPT_ONLY_SUPPORT / INFERRED_FROM_FAISAL_SOURCE · PARTIAL_OR_CONCEPT_ONLY_SUPPORT |
| سيولة | `M5_DOLLAR_VOL` | hard | hard | INHERITED_OR_EXTERNAL · PARTIAL_OR_CONCEPT_ONLY_SUPPORT |
| توافق الفريمات | `SOFT_M6_TF` | info | info | INHERITED_OR_EXTERNAL · PARTIAL_OR_CONCEPT_ONLY_SUPPORT |
| نمط شمعة انعكاسي | `SOFT_M7_PATTERN` | soft | soft | INFERRED_FROM_FAISAL_SOURCE · PARTIAL_OR_CONCEPT_ONLY_SUPPORT |
| فجوة-هدف فوق السعر | `SOFT_M9_GAP_ABOVE` | soft | soft | INFERRED_FROM_FAISAL_SOURCE · PARTIAL_OR_CONCEPT_ONLY_SUPPORT |
| RSI تشبّع والآن | `M10_RSI_OS / M10_RSI_NOW` | hard | hard | INFERRED_FROM_FAISAL_SOURCE · PARTIAL_OR_CONCEPT_ONLY_SUPPORT / INFERRED_FROM_FAISAL_SOURCE · PARTIAL_OR_CONCEPT_ONLY_SUPPORT |
| تقاطع MACD | `SOFT_M11_MACD` | soft | soft | INFERRED_FROM_FAISAL_SOURCE · PARTIAL_OR_CONCEPT_ONLY_SUPPORT |
| السعر قرب متوسطه 30/50 | `SOFT_M12_EMA` | soft | soft | INFERRED_FROM_FAISAL_SOURCE · PARTIAL_OR_CONCEPT_ONLY_SUPPORT |
| الشورت تحت 40K | `M13_SHORT` | hard | soft | INHERITED_OR_EXTERNAL · UNJUSTIFIED_BY_CURRENT_EVIDENCE |
| الفلوت تحت 50M | `M14_FLOAT` | hard | hard | EXPLICIT_OWNER_POLICY · PARTIAL_OR_CONCEPT_ONLY_SUPPORT |
| مِرساة: قاعٌ مُختبَر | `ANCHOR_TWO_TOUCH` | absent | hard | EXPLICIT_OWNER_POLICY · PARTIAL_OR_CONCEPT_ONLY_SUPPORT |
| المتاح للاقتراض 20K أو أقل | `BORROW_AVAIL` | absent | hard | EXPLICIT_OWNER_POLICY · EXPLICIT_OWNER_REQUIREMENT |

Displayed gates now mirror the scanner: M1–M5 + RSI hard (catalog numbers), M6 info at 0, M7/M9/M11/M12 soft, **M13 soft** (was shown hard), **M14 hard**, **borrow hard** (was absent), **anchor hard** (was absent). The verdict line now equals the scanner's post-enrich decision (`post_enrich_verdict`): a stock removed by M14 or the borrow gate is no longer called «مؤهّل — كان سيدخل قائمة المراقبة». Below that verdict both tools now print five separate layers (`analyze_one.verdict_layers`, display only): ① Faisal's observed action and ② the source stage — UNKNOWN unless a source establishes them, never inferred from candles · ③ the technical assessment (the screener's technical gates, not a certificate of Faisal's method) · ④ owner-policy eligibility (float, borrow — unknown stays unknown) · ⑤ actionability (a technical «ready» is a price location, not an entry: without a confirmed trigger it is «not determined»). A name that passes technically and is removed by the float or borrow gate is no longer called «ليس سهم ارتكاز مؤهّلًا» in `hand_check`.

## 4b. Slot filling after the borrow gate (production logs, recorded in `data/gate_fill_observations.json`)

| date | run | free slots | filled | rounds | ejected by borrow | examined | pool after DQ | unexamined (≤) |
|---|---|---|---|---|---|---|---|---|
| 2026-10-07 | 37589176908 | 8 | 2 | 4 | 28 | 30 | — | — |
| 2026-10-08 | 37747202124 | 6 | 1 | 4 | 23 | 24 | 103 | 79 |
| 2026-10-09 | 37902530011 | 12 | 4 | 4 | 40 | 44 | 104 | 60 |

Over these runs 7 of 26 free slots were filled; the borrow gate ejected 91 of 98 examined (93%), and every run stopped at the rounds cap with qualified names unexamined (the «unexamined» column is an upper bound: names already held or stopped are excluded too). Why these days: the first three runs after the ChartExchange parser fix (2026-10-06, merged in #548): before it, availability was unknown and passed by benefit of the doubt, so the borrow gate did not eject.

## 5. Next permitted action

- Two active gates have no supporting evidence at all — `M13_SHORT` (FINRA short volume, 40,000: no Faisal source, no owner order; Faisal's «شورت» is availability) and `STOPPED_EXCLUSION` (inherited switch). Removing or changing either changes live candidate generation ⇒ owner decision; any removal needs a preregistered measurement (the M13 tightening experiments were null).
- Guards with a supported concept and an unsupported number (`COVERAGE_GUARD` 85% · `FILL_ROUNDS` 4 · `D_DEPTH` 120 · the `DQ_GATE` mapping and 5% tolerance): the concept stays; the number is a disclosed engineering default, not evidence.
- The dominant first wall on Faisal's episodes is `ANCHOR_TWO_TOUCH` (owner policy, FROZEN by the H6 control-pool dependency and the perf verdict): no production change is permitted; the admissible evidence is the prospective H6 collection already running.
- `FILL_ROUNDS` × `BORROW_AVAIL` (§4b): the rounds cap, not the pool, ended slot filling in all three post-fix runs. More rounds would push ChartExchange lookups past its ~50-page runner quota, and an unknown availability passes the gate, so raising the cap alone would weaken the borrow gate; harvesting availability for the ranked pool before the screen would not. Either is a change to live candidate generation ⇒ owner decision (and a prereg for a threshold). The new log line (`fill_shortfall_note`) now records the binding cause daily.
- `M2_CEIL` / `M4_RANGE` artefacts on reverse-split names: closed / owner-decided axes; reopening needs the owner.

