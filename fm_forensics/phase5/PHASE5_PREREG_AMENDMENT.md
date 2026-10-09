# PHASE 5 — PRE-REGISTRATION AMENDMENTS

## A1 — §N "≥ 80% POINT_IN_TIME_VERIFIED" for H4 (recorded after results were seen; **non-confirmatory**)

- **Old:** §N requires that ≥ 80% of the values used in a family carry `POINT_IN_TIME_VERIFIED=1`; for H4 the prereg (§C-D) defined verification as an SEC 8-K item 5.03/3.03 within ±21 days of the Yahoo split date.
- **New (interpretation, not a rule change):** the criterion stays as written and the pre-registered verdict for H4 stands (**UNSUPPORTED by §N**). This amendment records *why* it fails: foreign private issuers file 6-K/20-F and never file an 8-K, so their reverse splits cannot be SEC-confirmed by the chosen rule. Confirmation by filer type: positives domestic 17/18, foreign 0/22; controls domestic 56/58, foreign 1/46. The split *dates* are historical facts whose lookahead safety does not depend on the confirmation; what is unverified is the vendor's completeness for foreign issuers.
- **Reason:** the verification rule conflated "lookahead-safe" with "SEC-confirmed" and was unattainable by construction for 53% of the positives (20/38 foreign filers).
- **Timestamp:** 2026-10-08 (after `results_discovery.csv` and `results_validation.csv` were written).
- **Evidence seen before writing:** all results tables (discovery, validation, pooled, placebo, sensitivity windows).
- **Experiments affected:** H4 verdict wording only. A **post-hoc** sensitivity (`posthoc_h4.py` → `out/results_posthoc_h4_domestic.csv`) restricts H4 to domestic filers (where verification is 85–91%): discovery 9 positives and validation 9 positives are each below the §O floor of 10 (NOT TESTABLE); pooled 18 positives / 14 strata give a matched difference of +0.333 with a 98.75% CI of (0.000, 0.643), touching 0.
- **Invalidates?** No pre-registered result is changed. The post-hoc estimate is reported as exploratory and is never used to upgrade the H4 verdict.
