# PHASE 5 — PRE-REGISTRATION (frozen before any feature–outcome association)

**Mission:** «FAISAL BOT — FORENSIC PHASE 5 — NON-CANDLE INFORMATION × FAISAL STOCK SELECTION — HISTORICAL AVAILABILITY × MATCHED CONTROLS × INDEPENDENT VALIDATION × CAUSAL FALSIFICATION».
**Scope lock (§1):** research only under `fm_forensics/phase5/`. No change to V4, the production scanner, Candidate Gates, READY NOW, thresholds, ranking, Telegram, the prospective validation, the historical labels, the three-condition tool, or the live methodology. No V5 / READY_NOW_V2 / production model, ranking, filter or state machine. **A valid negative result is an acceptable outcome.**
**Status at freeze:** the Phase 4 reconciliation (`PHASE5_PHASE4_RECONCILIATION.md`, 51/51 reproduced) and the outcome-blind availability inventory (`PHASE5_FEATURE_AVAILABILITY.csv`, counts only) were produced **before** this document; **no feature value has been compared with any outcome and no control feature has been read.** The freeze block at the end records the commit, timestamp and hashes.

---

## A. Research questions (kept separate; never collapsed — §0)

- **Q-A HISTORICAL ASSOCIATION.** Among securities that were *identity-eligible for the bot without the anchor gate* on day T, does each of the four non-candle features, as it was knowable **before** T, differ between securities Faisal documented as selected (FOCUS/WATCH/READY/ENTRY) and matched comparison securities?
- **Q-B HISTORICAL AVAILABILITY.** For how many decision episodes can each feature be reconstructed with a **point-in-time vintage** (record date before T) rather than a current value, and from which source?
- **Q-C DIRECT METHOD EVIDENCE.** Does Faisal's own corpus state the rule (verbatim/adopted tag in `FAISAL_SOURCE_LEDGER.md`), and does his documented reasoning on the cohort's units mention the feature?

Each is reported with its own verdict (§23 of the mission): STATISTICAL DISCRIMINATION · HISTORICAL AVAILABILITY · DIRECT METHOD SUPPORT · CAUSAL INTERPRETATION · PRODUCTION RELEVANCE (always "none claimed").

## B. Hypotheses and falsifiers (§22)

| id | hypothesis (direction fixed now) | source of the direction | falsified when |
|---|---|---|---|
| **H1 float** | Faisal-selected securities have **smaller public float** at T than matched controls; binary form: float ≤ 5,000,000 shares more often | `FWD_FLOAT_MAX=5_000_000` (`head_shoulders.py:1694`, `faisal_adopted`, TG_57915/57918/57919) | matched-pair difference in P(float ≤ 5M) has a 98.75% CI that includes 0 in discovery, **or** the validation direction reverses, **or** the family is NOT TESTABLE (§N/§O) |
| **H2 offering** | Faisal-selected securities **less often** have a **final prospectus (424B1/424B4/424B5) filed within the 90 calendar days before T** (Faisal's condition «لا إعلان طرح», method hunter ⑤) | `_FOUNDING_OFFERING_FORMS` (`Super_stock.py:6099`) · `FAISAL_SCIENTIFIC_METHOD.md` ⑤ | same rule as H1 on P(final prospectus ≤ 90d); registration statements (S-1/F-1/S-3/F-3) within 365 d are **exploratory only** (direction not fixed: Faisal names «طرح» as a *founding event* in TG_2077 and as an *exclusion* in the method) |
| **H3 borrow** | Faisal-selected securities have **fewer shares available to borrow** before T; binary: available < 20,000 | `BORROW_AVAIL_MAX=20_000` (`faisal_verbatim`, IMG_0151 «تحت 20 ألف») | same rule; **declared NOT TESTABLE** if fewer than 10 primary positives have a point-in-time snapshot before T (inventory at freeze: **5 of 46 episodes**) ⇒ "BORROW_AVAILABILITY_HYPOTHESIS = NOT TESTABLE WITH AVAILABLE DATA" |
| **H4 split age** | Faisal-selected securities **more often** had a confirmed reverse split within the **120 calendar days** before T («توها مقسمة» · founding event); continuous form: fewer sessions since the last reverse split | `SPLIT_LOOKBACK_DAYS=120` (production window, tagged `unsourced` in the ledger; the *concept* is Faisal's, the number is engineering — stated as such) | same rule on P(reverse split ≤ 120 d); sensitivity windows 60 and 252 d reported, never used to rescue |
| **H5 joint** | the count of satisfied conditions among the **testable** families (0..k) is higher in selected securities | combination prespecified here; computed only if ≥ 2 families are testable | CI of the matched-pair mean difference includes 0 |
| **H6 null (legitimate)** | the available historical data cannot distinguish selected from matched securities on these features | — | any of H1–H4 passes §N |

Direction and thresholds above are **final**. Any other cut-point, window or form is exploratory and goes to `PHASE5_EXPLORATORY_FEATURES.csv` with `EXPLORATORY_ONLY=1`.

## C. Feature definitions (§7)

- **A FLOAT_SHARES**: public float in shares as recorded by a bot state file **before T** (`weekly_watchlist.json` history S01, `company_cache.json` first appearance S02, `near_watch_float.json` S03); the latest value-date before T wins. `log10(float)` continuous; binary ≤ 5,000,000. **SHARES_OUTSTANDING_DEI** (SEC `dei:EntityCommonStockSharesOutstanding`, `filed` < T) is recorded as an *upper bound* and used only in a sensitivity analysis (float ≤ shares outstanding). A current vendor value is **NON_CONFIRMATORY** and never enters a test.
- **B OFFERING_STATUS_AS_OF_DECISION**: from SEC EDGAR submissions (S07): `DAYS_SINCE_LAST_FINAL_PROSPECTUS` (424B1/424B4/424B5, `filingDate` < T) → binary ≤ 90 d. Classification scheme (fixed): FINAL_PROSPECTUS = {424B1, 424B4, 424B5}; REGISTRATION = {S-1, S-1/A, S-3, S-3/A, F-1, F-1/A, F-3, F-3/A, F-10}; OTHER_PROSPECTUS = {424B2, 424B3, 424B7, 424B8, 424H}; EFFECT = notice of effectiveness. `OFFERING_STATUS_AS_OF_DECISION` ∈ {FINAL_PROSPECTUS_≤90D, REGISTRATION_ONLY_≤365D, DOCUMENTED_ABSENCE (CIK resolved, filings exist, none in window), UNKNOWN (no CIK / fetch failed)}.
- **C AVAILABLE_SHARES**: IBKR shares available to borrow from a dated snapshot before T (S04 `ctb_log.jsonl`, S05 watchlist `borrow_hist`, S01 `shares_available` at commit); latest snapshot before T; binary < 20,000. **No short-volume or short-interest proxy is accepted** for this family.
- **D SESSIONS_SINCE_LAST_REVERSE_SPLIT**: from Yahoo splits (S06; ratio < 1; same-ratio duplicates within 7 days merged as in production `SPLIT_DUP_DAYS`), split date < T; confirmed `HIGH` when an 8-K with item 5.03/3.03 lies within ±21 days of the split date in S07, else `MEDIUM`; `NO_CONFIRMED_PRIOR_REVERSE_SPLIT` is an explicit value. Binary: calendar days ≤ 120.

## D. Timestamp rules (§6)

- `DECISION_TIMESTAMP` = Faisal's session date T (post time unknown ⇒ the whole session is treated as after the cutoff). `DATA_CUTOFF_TIMESTAMP` = T 00:00 America/New_York.
- A value is **LOOKAHEAD_SAFE** only if its `SOURCE_RECORD_DATE` (git commit day · harvest day · SEC `filingDate` · split effective date) is **strictly before T**.
- SEC: `acceptanceDateTime` is the publication timestamp; filings accepted after 17:30 ET are public the next business day, so `filingDate` < T is the rule (conservative by one day).
- `HISTORICAL_AVAILABILITY_UNVERIFIED` when the record date is unknown; such values are reported but excluded from confirmatory tests.
- Yahoo splits are a **current snapshot of historical dates**: `POINT_IN_TIME_VERIFIED=0` unless SEC-confirmed; H4 therefore carries `AVAILABILITY = partially verified` unless ≥ 80% of the used split dates are SEC-confirmed.

## E. Primary outcome (§14)

`DOCUMENTED_FAISAL_SELECTION` at the **primary unit** of each non-anchor security with bars (38 securities; `PHASE5_PRIMARY_UNIT=1` in the manifest): tier ≥ FOCUS_OR_WATCH, label `POSITIVE_DIRECT` (`HIGH` for DIRECT_TEXT/ACTION, `MEDIUM` for DIRECT_CHART). Secondary (descriptive only): READY/ENTRY tiers. **No price outcome is ever a label.** Anchors DKI/SXTC/HUBC are descriptive only; HUBC's label is never invented. The four bar-less securities (ATPC, LABT, MI, UNK) are listed in every denominator with `HAS_BARS=0` and excluded from tests (category D).

## F. Control definitions and negative-label tiers (§11–§12)

- Pool: the probe universe of `fm_forensics/data/bars_2026-10-08.json.gz` (232 symbols with daily bars) **minus** every security with any Faisal unit of any class (MENTION/UNKNOWN/EXIT included; 72 symbols) and minus the anchors ⇒ **160 pool symbols at freeze**. The pool is the one Phase 2 assembled for the replay (bot-adjacent symbols); its composition is a recorded limitation (category E) and is not widened after this freeze.
- Eligibility at the matching date D (= the positive's primary date): identity-eligible without the anchor gate (`p4lib.eligible`, production gates by name), ≥ 120 bars before D.
- Label tier for controls: **UNKNOWN by default** (absence of a post is not a negative); `NEGATIVE_OBSERVED` only for controls whose symbol appears in the three-condition / watch-period tools' coverage on D with no Faisal unit within ±30 sessions (coverage argument recorded per row); `NEGATIVE_DIRECT` only from an explicit Faisal rejection unit (none exist in the corpus for pool symbols at freeze).
- Sensitivity: tests repeated on `NEGATIVE_OBSERVED` controls only, if ≥ 10 exist.

## G. Discovery / validation partition (§10, §13)

Phase 4's validation membership is **contaminated** (labels revealed). New partition **by security**, fixed now: `DISCOVERY` if `sha256("P5-2026-10-08:" + SECURITY_ID)` has an even last hex digit, else `VALIDATION`. Membership is written in the freeze block below. Control features for VALIDATION securities are not read until the discovery results are committed (commit SHA recorded in the final report). Nothing moves between sets after this commit.

## H. Matching procedure (§11)

For each positive primary unit at D: candidates = eligible pool symbols on D. Distance = Euclidean in (`log10 price`, `ATR14% / 10`, `log10 dollar-volume-20 / 2`) with a caliper of 1.5; up to **4** nearest; ties broken by symbol order; seed 20261008 for any random step. **The tested features are not matching variables** (Phase 4 matched on `rsplit_252`; Phase 5 does not, because it is H4). Market-cap class is **not** matched (no reliable point-in-time shares figure for the pool) — recorded as a limitation and used as a sensitivity stratifier where `SHARES_OUTSTANDING_DEI` exists. Exchange = NASDAQ for the whole pool. Balance diagnostics (standardized mean differences of the three matching variables, plus of `rsplit_252` as a non-matched check) are written to `PHASE5_MATCHED_CONTROL_MANIFEST.csv`. A control may serve several positives; inference clusters by `SECURITY_ID`.

## I. Missing data (§9, §17)

Every missing value carries one `MISSING_REASON` ∈ {NOT_COLLECTED, NO_HISTORICAL_SOURCE, NO_RECORD_FOUND, RECORD_NOT_APPLICABLE, SOURCE_CONFLICT, IDENTIFIER_UNRESOLVED, UNKNOWN}. Primary tests are complete-case within matched strata (a stratum is used when the positive **and** ≥ 1 of its controls have a value). The availability rate is compared between positives and controls per family; a **differential > 20 points** marks the family **AVAILABILITY-CONFOUNDED** (category D) regardless of the association result, because the bot stores float/borrow only for securities it selected — availability is itself a selection artifact.

## J. Confounders (§15)

Bot-selection-driven availability (above) · price regime · volatility · liquidity · time period (controls share D) · sector/industry (recorded from SIC in S07; not matched) · data depth · corporate-action profile (H4 itself; reported as a stratifier for H1–H3) · corpus coverage (Faisal's visible output is a sample of his attention).

## K. Statistics (§16)

Per family: counts with denominators (positives with value / total; controls with value / total); unadjusted proportions with Wilson 95% CIs and Fisher's exact p (reported, not decisive); **matched**: mean within-stratum difference P(positive condition) − P(control condition) with a cluster bootstrap by `SECURITY_ID` (B = 2,000, seed 20261008) giving a **98.75% CI** (Bonferroni α = 0.05/4); **adjusted**: Mantel–Haenszel across price buckets (<1 / 1–5 / >5). Continuous forms: median difference with the same bootstrap. H5: mean difference in the count of satisfied conditions. Everything printed with `n`.

## L. Multiple testing

Four primary families ⇒ Bonferroni at α = 0.05 (98.75% CIs). Exploratory features are never corrected because they are never confirmatory.

## M. Falsification tests (§20, §22)

For any family that passes §N: (i) ablation — remove that feature from H5 and report the drop; (ii) necessity — share of positives that fail the condition (a feature cannot be necessary if > 20% of positives fail it); (iii) time-shift placebo — recompute the feature at T − 60 sessions for the same securities; if the association is unchanged the feature is a security trait, not a decision-time signal; (iv) availability-swap — restrict to strata where the control's value comes from the same source type as the positive's.

## N. Minimum evidence for a positive claim

A family is **SUPPORTED (association)** only if: ≥ 10 primary positives with a point-in-time value; ≥ 10 matched strata; discovery matched-difference 98.75% CI excludes 0; validation difference has the same sign and at least half the discovery magnitude; availability differential ≤ 20 points; ≥ 80% of used values `POINT_IN_TIME_VERIFIED=1`. Otherwise: UNSUPPORTED, NOT TESTABLE (F), INSUFFICIENT POWER (G) or AVAILABILITY-CONFOUNDED (D), named explicitly.

## O. Stopping rules

Availability is read **once** (this inventory). No new source is added for a family after any association number exists; a source found later goes to an amendment with `EVIDENCE_SEEN` stated. If a family has < 10 primary positives with a value, it stops at NOT TESTABLE and no threshold is relaxed to reach 10.

## P. Prohibited conclusions

No production recommendation; no "Faisal uses X" from association alone (Q-A ≠ Q-C); no causal language without §M; no new threshold proposed from these data; no treatment of UNKNOWN controls as negatives in prose; no pooling of discovery and validation to reach significance; no claim about H3 beyond "NOT TESTABLE" if §N fails on availability.

## Predictions written before any number (P1–P6)

- P1: H3 is NOT TESTABLE (5/46 episodes with a snapshot before T).
- P2: Float availability is differential: positives in the bot's lists have stored floats, pool controls mostly do not ⇒ H1 is AVAILABILITY-CONFOUNDED unless the SEC `dei` sensitivity rescues coverage.
- P3: H4 is testable for ≥ 30 primary positives (Yahoo splits) and for most controls.
- P4: H2 is testable if the SEC probe resolves ≥ 70% of CIKs.
- P5: No family meets §N in both discovery and validation (prior: Phases 1–4 found no discriminating candle feature; non-candle features are confounded by availability).
- P6: The cohort is too small for H5 to be decisive (≤ 19 positives per half).

Predictions that fail are published, not deleted.

---

## FREEZE BLOCK

- Written at: 2026-10-08T23:02:06.671565+00:00
- Base commit (HEAD when written): `428afb59cd184b4ec8c99155c2a49059a9cf4ac1`; the merge commit of this file is the freeze reference.
- `PHASE5_COHORT_MANIFEST.csv` sha256[:16] = `d652b8538e19c345` (88 rows · 45 securities · primary units 38)
- `PHASE5_FEATURE_AVAILABILITY.csv` sha256[:16] = `5ce6c83c655492d8` (positives only · counts read, no outcome join · SEC family NOT_COLLECTED at freeze)
- Config hash (p5lib.py + inventory.py + reconcile.py + controls.py) = `1e7954f3d9848a3b`
- DISCOVERY (23): AMIX, BETA, CDIO, CIIT, CRE, CUPR, DXST, EDBL, ELAB, ELPW, FRSX, IPDN, LIMN, MNDR, NUWE, OMH, PPBT, SMX, SPRC, STKH, UPC, YMT, ZCMD
- VALIDATION (15): BRTX, CANF, CETX, DCOY, EHGO, GCTK, MSGY, NRSN, ONCO, PIII, SLXN, SVRE, TRUG, WORX, ZNB
- Anchors (descriptive only): DKI, SXTC, HUBC · bar-less (excluded, listed): ATPC, LABT, MI, UNK
- Amendments only via `PHASE5_PREREG_AMENDMENT.md` (old · new · reason · timestamp · evidence seen · experiments affected · invalidates?).
