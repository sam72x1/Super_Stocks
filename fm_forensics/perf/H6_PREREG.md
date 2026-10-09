# H6 — PRE-REGISTERED PROSPECTIVE CONTRACT (final · frozen before any eligible decision exists)

Date: 2026-10-09 · Repository `main` = `b1ece5562661b42c47470264930acbf9abf0b417` (after PR #587) · Owner order: «سجّل عقد H6 وفق النتائج الحالية، بشروط نهائية ومسبقة التسجيل» · Research only.

This contract settles **one** hypothesis with prospective evidence. It does not open a new chain of investigations: after the single analysis in §9 the H6 line of work ends with the verdict file, whatever the verdict (§11).

## 0. What is frozen and what stays untouched
| Item | State |
|---|---|
| Production bot (`Super_stock.py`, roots, thresholds, `LOGIC_VERSION`), V4 (`faisal_method_v4/` freeze `5f291a3b…`), entry/exit rules, Telegram channels | **unchanged** by this contract and by its analysis, whatever the result (owner condition 1) |
| Prior evidence this contract is built on | Phase 5 (`fm_forensics/phase5/PHASE5_PREREG.md` §B–§D: the four feature families; verdicts UNSUPPORTED / NOT TESTABLE), Phase 6 (`fm_forensics/phase6/`: the prospective collector and its ledger), the performance experiment (`fm_forensics/perf/PERFORMANCE_VERDICT.md`: C. NO DEMONSTRATED IMPROVEMENT), Phase 3/4/6 H6 statement: *Faisal uses information outside the candle series (float, borrow, offerings, splits) that the pipeline does not model* — left open, measurable only prospectively |
| Instrumentation added **with** this contract (research only) | `fm_forensics/phase6/collector.py`: a daily **control panel** (§4) drawn from `reject_log.json`; `fm_forensics/perf/h6_test.py`: the gated status/analysis tool (§9); no production module imports either |
| Decision sources | `faisal_method_v41/final_protocol/PROTOCOL_STATUS.json` (`cases`, written by the frozen protocol's `write`), `faisal_method_v41/final_protocol/intake/<BATCH>/annotations.json`, `faisal_validation/PROSPECTIVE_LEDGER.jsonl` — all produced by the existing BLIND-FIRST intake loop; H6 reads them and writes nothing into them |
| Data source | `fm_forensics/phase6/data/PHASE6_LEDGER.jsonl` (append-only, hash-chained) and `fm_forensics/phase6/data/PHASE6_CONTROL_PANEL.jsonl` (append-only) |

## 1. Hypothesis (one) and its negation
**H6:** at the time Faisal posts a decision about a security, **non-price information available at that time** — public float, shares available to borrow, a recent final prospectus, a recent reverse split — separates the securities he posts about from matched identity-eligible securities he does not post about.

**Null (H6₀):** the four pre-registered features have the same prevalence among his posted securities and among matched controls drawn from the same candidate pool on the same day.

Short interest is **descriptive only** (§5): no hypothesis, no verdict row.

## 2. Cutoff and the prospective window
- **Cutoff:** `2026-10-09T04:34:36Z` = `collected_utc` of the first row of the Phase 6 ledger (run `37884481989`); the collector workflow's first run. A Faisal decision is prospective for H6 only if its decision date **T** (New York session day, as established by the intake) is **≥ 2026-10-09**. The B4 batch (CDT · NCT · SXTC, T = 2026-10-07 / 09-24) and every earlier decision are **historical for H6** and never enter the test.
- **Window:** decisions with T in `[2026-10-09, 2027-04-09]`. If the sample floor (§7) is not reached by **2027-04-09**, the result is `INSUFFICIENT_SAMPLE` and is **final** (no extension, no relaxation, no estimate in place of data).

## 3. Units: eligibility, independence, duplicates
A **unit** = (security, episode). Source of candidates: every case in `PROTOCOL_STATUS.json → cases` whose `DECISION_DATE` ≥ 2026-10-09. A unit is **ELIGIBLE** only if all of E1–E7 hold, evaluated in order (the first failing rule is recorded):
- **E1 date established:** `DECISION_DATE` is a single calendar day (not `UNKNOWN`; the intake's `decision_date_max` is null for the defining image). Provenance tier is recorded (`SAMPLE` = PRIMARY for HIGH/MEDIUM confidence, SECONDARY for LOW): both tiers are eligible because H6 needs day precision, not post-second precision; the PRIMARY-only subset is reported as a sensitivity row (§8), never as a rescue.
- **E2 Faisal-authored decision:** `INTAKE_CLASS = NEW_PROSPECTIVE`; `faisal_author` true in the intake; the revealed label (`FAISAL.label` / `effective_label`) is one of WATCH · FOCUS · READY · ENTRY · WAIT(= watch-and-wait). A revealed **REJECT** is excluded from positives and counted separately as a negative mention (descriptive). A case not yet revealed is `PENDING_REVEAL`: it counts toward *nothing* until revealed (the owner's loop seals, runs V4, then reveals).
- **E3 not a duplicate/derivative/contaminated/pre-existing:** the intake's seven-class result must be `NEW_PROSPECTIVE` (DUPLICATE · DERIVATIVE · CONTAMINATED · PRE_EXISTING · INSUFFICIENT_CONTEXT · UNKNOWN are out).
- **E4 independent episode:** no earlier Faisal decision on the same security (any of: `fm_forensics/phase3/FAISAL_TIMELINE.csv` `IS_FAISAL=1`, `fm_forensics/phase5/PHASE5_COHORT_MANIFEST.csv`, an earlier eligible H6 unit, or the B4/B48 cases) with a date within **30 sessions** before T. A repeat within 30 sessions is a `REPEAT` of the earlier unit (recorded, never a second unit). A repeat after more than 30 sessions is a new episode.
- **E5 collected:** the security has at least one Phase 6 ledger row collected within **5 sessions after T** (`collected_utc` date ≤ T + 5 sessions) — the first such run day is the unit's **collection day C**. Collection lag L = sessions(T → C) is recorded. A unit whose first collection is later than T + 5 sessions is `NOT_COVERED` (counted in coverage, §7; not replaced).
- **E6 matched controls:** at least **2** control symbols exist for the unit (§4). Otherwise `NO_CONTROLS` (coverage).
- **E7 comparable frame:** the security's `split_frame` at C equals its frame at T (no reverse split between T and C). Otherwise `FRAME_CHANGED` (coverage).

**Anchors** DKI · SXTC · HUBC are reported separately and never counted (as in every prior phase).

## 4. Matched controls (the instrumentation this contract requires)
Faisal's decisions arrive only after he posts; a control snapshot taken later would be "current data used as historical" (owner condition 5). Therefore the Phase 6 collector draws a **control panel every run day** (`Collector.run_controls`, added with this contract):
- **Pool:** the newest `reject_log.json` entry dated ≤ the run day whose wall `M_لا_مستوى_مختبر` (identity-eligible, rejected by the anchor rule only — the same pool used for Phase 4/5/perf controls) is stored **in full** (`len == walls_n`; a sampled/truncated wall is refused). Pool size on 2026-10-08: 395.
- **Draw:** `CONTROL_K = 16` symbols per run, ranked by `sha256(run_day + "|" + symbol)` (deterministic; the run day is the seed), **excluding** every Faisal mention ticker known to the collector on that day and the three anchors. The draw (run id, day, pool date, pool size, seed, tickers) is appended to `data/PHASE6_CONTROL_PANEL.jsonl`; existing lines are never rewritten.
- **Collection:** the same five blocks as Faisal tickers (Yahoo float/SI/shares, TradingView float, ChartExchange borrow, SEC identity/filings/DEI, Yahoo + Nasdaq splits), with two declared differences: ChartExchange quota reserved for controls = `CONTROL_K` of `CE_QUOTA = 48` (Faisal tickers keep 32 per run with the existing rotation), and SEC filings/DEI points limited to `CONTROL_SEC_DAYS = 200` calendar days before the run day (enough for the 90-day prospectus window and the 120 + 21-day split window; keeps the ledger growth ≈ 30–60 rows per control).
- **Matching rule (fixed):** for an eligible unit with collection day C, its controls are the panel members of the run day **C** (same day; if the panel of C is `NO_POOL`/missing, the nearest panel day within ±1 session, C−1 preferred), excluding the unit's own security and any symbol that is itself an H6 unit or a Faisal mention by that day; the first **4** in panel order with an identity row. Fewer than 2 ⇒ `NO_CONTROLS`.
- **Symmetry:** positives and their controls are measured on the **same collection day C** for the snapshot features (A, C), and against the **same reference date T** for the dated features (B, D). The lag L (0–5 sessions) is a declared limitation, reported with its distribution; it is identical for the unit and its controls by construction.

Cost (declared): ≈ 16 extra tickers per run (≈ 1–2 minutes), ≈ 0.5–1 MB of ledger per month. If the owner judges this unacceptable, `P6_CONTROLS=0` disables the panel and H6 becomes `NOT TESTABLE` by construction (§10).

## 5. Features (fixed; the three share counts are never mixed)
Each feature is computed from ledger rows only, with `evidence_class(rec, ref)` from `collector.py`; a row is usable only if `status = OK`.
| Family | Definition at use | Usable rows | Binary (direction pre-registered) |
|---|---|---|---|
| **A float** | `public_float` from `yahoo_info` on day C (fallback `tv_scan` on day C; never SEC `EntityPublicFloat`, a dollar value) · snapshot `collected_utc` date = C | category 1, same `split_frame` as the unit at T | float ≤ 5,000,000 shares — expected **more** often in positives (`FWD_FLOAT_MAX`, `faisal_adopted`) |
| **B offering** | `sec_filing` rows with form ∈ {424B1, 424B4, 424B5} and `filingDate` in (T − 90 d, T]; requires an `identity` OK row (CIK resolved) | category 2 (provider-dated) | final prospectus ≤ 90 d — expected **less** often in positives («لا إعلان طرح») |
| **C borrow** | `borrow_available` from `chartexchange` on day C | category 1 | available < 20,000 — expected **more** often in positives (`BORROW_AVAIL_MAX`, `faisal_verbatim`) |
| **D split age** | `reverse_split` rows (`yahoo_splits` ∪ `nasdaq_calendar`, ratio < 1) with effective date in (T − 120 d, T] | category 2 | reverse split ≤ 120 d — expected **more** often in positives («توها مقسمة»; window `engineering`) |
| SI (descriptive) | `short_interest` from `yahoo_info` with provider as-of ≤ T and ≥ T − 30 d | category 2 | reported as median per group; **no test** |

**Missing-value rules (fixed):** a unit or control with no usable row for a family is `MISSING` for that family (never imputed, never 0, never carried from another day). Family coverage = share of (units + their controls) with a usable value. A family is **TESTABLE** only if coverage ≥ 80% among eligible units **and** ≥ 80% among their matched controls, and the units with a value number ≥ 15. Otherwise the family is `NOT TESTABLE` (reported with its coverage), and no estimate replaces it. `shares_zero_reported` (available = 0) is a valid value (< 20,000).

## 6. Statistic, false-alarm control, independence
For each testable family: prevalence in positives p₁ (over eligible units with a value) and prevalence in matched controls p₀ (over their matched controls with a value). Effect = p₁ − p₀ in the pre-registered direction (families B: sign flipped so that the expected direction is positive).
- **Interval:** cluster bootstrap by unit (a unit and its matched controls resample together), B = 2000, seed 20261009, percentile interval at **98.75%** (Bonferroni over the 4 families ⇒ family-wise false-alarm 5%). Also reported: Newcombe 95% interval for the difference as a cross-check (never decisive).
- **Clusters:** two units on the same security (episodes > 30 sessions apart) resample as one cluster.
- **No validation split:** the sample is a single confirmatory set (floor 15); there is no development set, so there is nothing to validate against. The ceiling of the verdict is therefore **SUPPORTED (single prospective sample, unreplicated)** — never "validated".

## 7. Sample floor and coverage (operating minimum, not a statistical guarantee)
- **Floor:** 15 eligible units (§3) with at least one testable family. This is the owner's operating minimum; with 15 units the test can detect only large differences (a prevalence gap of about 0.5 at 98.75% two-sided; smaller true effects will read `UNSUPPORTED`). This is stated now so that an `UNSUPPORTED` verdict is read as "not demonstrated at this sample", not as "absent".
- **Coverage of required data:** E5/E6/E7 failures and family `MISSING` are counted; if more than 20% of otherwise-eligible units are `NOT_COVERED`/`NO_CONTROLS`/`FRAME_CHANGED`, the result is `NOT TESTABLE (coverage)` even when the floor is reached.

## 8. Verdict rules (declared before any eligible unit exists)
Per testable family: **SUPPORTED** if the 98.75% lower bound of the directional effect is > 0 **and** the control prevalence of the feature **in its expected direction** is ≤ 0.5 (families A/C/D: p₀; family B: 1 − p₀, i.e. "no final prospectus ≤ 90 d" — a feature most controls already have cannot separate); **REVERSED** if the upper bound is < 0; otherwise **UNSUPPORTED**.

H6 overall (one line, four values):
- `H6 = SUPPORTED` — at least one family SUPPORTED and no family REVERSED;
- `H6 = UNSUPPORTED` — every testable family UNSUPPORTED or REVERSED;
- `H6 = NOT TESTABLE` — no testable family (coverage/§5), or the panel disabled (§4), or §7 coverage failure;
- `H6 = INSUFFICIENT_SAMPLE` — fewer than 15 eligible units by 2027-04-09.

Sensitivity rows (reported, never deciding): PRIMARY-provenance units only; lag L = 0–1 only; family windows 60/252 d for D and 180 d for B; anchors.

Pre-registered predictions (published whatever happens): P1 — the lag L will have median ≤ 2 sessions if the owner seals within a day of each post; P2 — family C (borrow) coverage will be the lowest of the four (ChartExchange quota and 404s); P3 — the floor will not be reached before 2026-12-31 at the observed posting rate (3 cases in 7 days of intake, 2 of them historical for H6).

## 9. Procedure (what runs, when, once)
1. `python3 fm_forensics/perf/h6_test.py status` — may run at any time: counts candidates, eligibility codes, coverage per family, lag distribution, panel health. It prints **no feature prevalence and no effect**; it writes `fm_forensics/perf/out/H6_STATUS.json`.
2. `python3 fm_forensics/perf/h6_test.py analyze` — refuses (exit 8) unless the floor is reached **or** the window has closed (then it writes the `INSUFFICIENT_SAMPLE` verdict). It runs **once**: if `fm_forensics/perf/out/H6_RESULT.json` exists it refuses (exit 8) — there is no re-analysis, no second look, no variant.
3. The verdict is written to `fm_forensics/perf/H6_VERDICT.md` from the JSON; the memory gets one archive item and one `CLAUDE.md` line. Nothing else follows automatically (owner condition 9).

## 10. Stopping rules and what is forbidden
- No change to this file after merge. Any defect found later is recorded in an amendment file (`H6_PREREG_AMENDMENT_<n>.md`) that may **tighten** rules or fix a defect in the tool with a bit-identical check; it may not change hypotheses, thresholds, windows, the floor, the matching rule, or the verdict rules.
- No analysis before the floor; no estimate for missing data; no new family; no threshold or window chosen after seeing numbers; no production change during the waiting period; no new phase after the verdict.
- The collector keeps running only while the owner accepts its cost (§4); stopping it is recorded in the status output as `COLLECTOR_STOPPED <date>` and makes later decisions `NOT_COVERED`.

## 11. Pre-committed interpretation
- `SUPPORTED`: H6 is supported on one prospective sample; the finding is unreplicated and is **not** a production rule (a rule would need its own pre-registered forward test with cost and false-alarm measurement; that is a new owner decision, not a next step of this contract).
- `UNSUPPORTED`: the four pre-registered non-price features do not separate Faisal's posted securities from matched identity-eligible securities at this sample; H6 is closed as measured.
- `NOT TESTABLE` / `INSUFFICIENT_SAMPLE`: H6 remains open and **unmeasured**; the record says so, with the reason, and the H6 line of work ends unless the owner opens a new contract.

Locks: `H6C1`–`H6C4` (control pool/sampling pure and deterministic; panel append-only; Faisal tickers' collection bit-identical with the panel on or off; quota reservation) and `H6T1`–`H6T3` (gate before the floor; eligibility codes; one-shot refusal; this file's SHA-256 pinned in the tool) in `test_bot.py`, each with a mutation that fails it.
