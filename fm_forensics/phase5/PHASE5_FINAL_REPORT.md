# PHASE 5 — FINAL REPORT (non-candle information × Faisal selection)

Built by `report.py` from `out/results_*.csv` at `f4751b3be9d8`. Pre-registration: `PHASE5_PREREG.md` (merged in PR #582, `4249c764`). Discovery frozen at `9b4b5a904095` (`results_discovery.csv` sha 7e0fc526b02e5748).

## 1. Denominators (§5)

- Manifest rows 88 · securities 45 · episodes 46 · evidence units 80
- Primary units (one per non-anchor security with bars): **38** · discovery 23 · validation 15 · anchors 3 (descriptive) · bar-less 4 (ATPC, LABT, MI, UNK — listed, excluded)
- Matched controls: 134 control-days · 71 distinct securities · positives matched 34 of 38 (unmatched: ['AMIX', 'DXST', 'ELAB', 'SMX'])
- Balance (SMD pos−ctrl): SMD log10price=-0.004 · ATR14=0.081 · log10dv=0.1 · rsplit252(not matched)=0.633

## 2. Historical availability (§9/§17 — Q-B)

| role | family | feature | available/total | point-in-time verified |
|---|---|---|---|---|
| CONTROL | A_FLOAT | FLOAT_SHARES | 40/129 | 40 |
| CONTROL | A_FLOAT | SHARES_OUTSTANDING_DEI | 103/129 | 103 |
| CONTROL | B_SEC_OFFERING | DAYS_SINCE_LAST_FINAL_PROSPECTUS | 118/129 | 118 |
| CONTROL | B_SEC_OFFERING | DAYS_SINCE_LAST_OFFERING_FORM | 129/129 | 129 |
| CONTROL | C_BORROW | AVAILABLE_SHARES | 23/129 | 23 |
| CONTROL | D_SPLIT_AGE | SESSIONS_SINCE_LAST_REVERSE_SPLIT | 104/129 | 57 |
| POSITIVE | A_FLOAT | FLOAT_SHARES | 12/46 | 12 |
| POSITIVE | A_FLOAT | SHARES_OUTSTANDING_DEI | 36/43 | 36 |
| POSITIVE | B_SEC_OFFERING | DAYS_SINCE_LAST_FINAL_PROSPECTUS | 40/43 | 40 |
| POSITIVE | B_SEC_OFFERING | DAYS_SINCE_LAST_OFFERING_FORM | 43/43 | 43 |
| POSITIVE | B_SEC_OFFERING | OFFERING_STATUS_AS_OF_DECISION | 0/3 | 0 |
| POSITIVE | C_BORROW | AVAILABLE_SHARES | 5/46 | 5 |
| POSITIVE | D_SPLIT_AGE | SESSIONS_SINCE_LAST_REVERSE_SPLIT | 40/46 | 17 |

## 3. Results (§16) — discovery, validation (blind until freeze), pooled (descriptive)

### Discovery (23 securities)

| family | status | n pos (value/total) | n ctrl (value/total) | avail diff (pts) | pos rate [95%] | ctrl rate [95%] | Fisher p | matched diff [98.75%] | excludes 0 | MH OR (price) | necessity fail | verified |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H1_FLOAT | NOT_TESTABLE (fewer than 10 positives with a point-in-time value — prereg §O) | 5/23 | 28/73 | -16.6 |   |   |  |   |  |  |  | 1.0 |
| H2_OFFERING | TESTED | 23/23 | 73/73 | 0.0 | 0.348 (0.188, 0.551) | 0.178 (0.107, 0.281) | 0.1452 | 0.1316 (-0.1316, 0.4211) | 0 | 2.088 | 0.652 | 1.0 |
| H3_BORROW | NOT_TESTABLE (fewer than 10 positives with a point-in-time value — prereg §O) | 3/23 | 14/73 | -6.1 |   |   |  |   |  |  |  | 1.0 |
| H4_SPLIT | TESTED | 23/23 | 73/73 | 0.0 | 0.739 (0.535, 0.875) | 0.384 (0.281, 0.498) | 0.0038 | 0.3026 (0.0658, 0.5395) | 1 | 3.883 | 0.261 | 0.417 |
| H4_SPLIT_60D · sensitivity | TESTED | 23/23 | 73/73 | 0.0 | 0.478 (0.292, 0.67) | 0.274 (0.185, 0.386) | 0.0786 | 0.2632 (0.0, 0.5263) | 0 | 3.103 | 0.522 | 0.417 |
| H4_SPLIT_252D · sensitivity | TESTED | 23/23 | 73/73 | 0.0 | 0.826 (0.629, 0.93) | 0.548 (0.434, 0.657) | 0.0257 | 0.2368 (-0.0526, 0.4474) | 0 | 3.137 | 0.174 | 0.417 |
| H5_JOINT | TESTED | /23 | / |  |   |   |  | 0.4342 (0.0395, 0.8289) |  |  |  |  |
| H2_OFFERING · placebo T-60 sessions | TESTED | 23/23 | 73/73 | 0.0 | 0.13 (0.045, 0.321) | 0.151 (0.086, 0.25) | 1.0 | -0.0526 (-0.2105, 0.1316) | 0 | 0.654 | 0.87 | 1.0 |
| H4_SPLIT · placebo T-60 sessions | TESTED | 23/23 | 73/73 | 0.0 | 0.391 (0.222, 0.592) | 0.233 (0.151, 0.342) | 0.1788 | 0.0789 (-0.1579, 0.3289) | 0 | 1.475 | 0.609 | 0.354 |

### Validation (15 securities)

| family | status | n pos (value/total) | n ctrl (value/total) | avail diff (pts) | pos rate [95%] | ctrl rate [95%] | Fisher p | matched diff [98.75%] | excludes 0 | MH OR (price) | necessity fail | verified |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H1_FLOAT | NOT_TESTABLE (fewer than 10 positives with a point-in-time value — prereg §O) | 5/15 | 15/59 | 7.9 |   |   |  |   |  |  |  | 1.0 |
| H2_OFFERING | TESTED | 15/15 | 59/59 | 0.0 | 0.0 (-0.0, 0.204) | 0.169 (0.095, 0.285) | 0.1975 | -0.1667 (-0.3167, -0.05) | 1 | 0.0 | 1.0 | 1.0 |
| H3_BORROW | NOT_TESTABLE (fewer than 10 positives with a point-in-time value — prereg §O) | 1/15 | 12/59 | -13.7 |   |   |  |   |  |  |  | 1.0 |
| H4_SPLIT | TESTED | 15/15 | 59/59 | 0.0 | 0.733 (0.48, 0.891) | 0.475 (0.353, 0.6) | 0.0887 | 0.2667 (-0.05, 0.5667) | 0 | 3.087 | 0.267 | 0.459 |
| H4_SPLIT_60D · sensitivity | TESTED | 15/15 | 59/59 | 0.0 | 0.533 (0.301, 0.752) | 0.271 (0.174, 0.396) | 0.0679 | 0.2667 (-0.0667, 0.6333) | 0 | 3.182 | 0.467 | 0.459 |
| H4_SPLIT_252D · sensitivity | TESTED | 15/15 | 59/59 | 0.0 | 0.933 (0.702, 0.988) | 0.559 (0.433, 0.678) | 0.0069 | 0.3833 (0.1667, 0.6) | 1 | 12.5 | 0.067 | 0.459 |
| H5_JOINT | TESTED | /15 | / |  |   |   |  | 0.1 (-0.2833, 0.4833) |  |  |  |  |
| H2_OFFERING · placebo T-60 sessions | TESTED | 15/15 | 59/59 | 0.0 | 0.067 (0.012, 0.298) | 0.237 (0.147, 0.36) | 0.2783 | -0.1667 (-0.35, 0.1167) | 0 | 0.236 | 0.933 | 1.0 |
| H4_SPLIT · placebo T-60 sessions | TESTED | 15/15 | 59/59 | 0.0 | 0.4 (0.198, 0.643) | 0.22 (0.134, 0.341) | 0.1902 | 0.1833 (-0.1167, 0.5) | 0 | 2.375 | 0.6 | 0.365 |

### Pooled — descriptive only (§P: never used to reach significance)

| family | status | n pos (value/total) | n ctrl (value/total) | avail diff (pts) | pos rate [95%] | ctrl rate [95%] | Fisher p | matched diff [98.75%] | excludes 0 | MH OR (price) | necessity fail | verified |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H1_FLOAT | INSUFFICIENT_MATCHED_STRATA (fewer than 10 — prereg §N) | 10/38 | 40/129 | -4.7 | 0.9 (0.596, 0.982) | 0.8 (0.652, 0.895) | 0.6651 |   |  |  |  | 1.0 |
| H2_OFFERING | TESTED | 38/38 | 129/129 | 0.0 | 0.211 (0.111, 0.363) | 0.178 (0.122, 0.253) | 0.6407 | 0.0 (-0.1765, 0.1912) | 0 | 1.02 | 0.789 | 1.0 |
| H3_BORROW | NOT_TESTABLE (fewer than 10 positives with a point-in-time value — prereg §O) | 4/38 | 23/129 | -7.3 |   |   |  |   |  |  |  | 1.0 |
| H4_SPLIT | TESTED | 38/38 | 129/129 | 0.0 | 0.737 (0.58, 0.85) | 0.426 (0.344, 0.513) | 0.0009 | 0.2868 (0.0956, 0.4779) | 1 | 3.444 | 0.263 | 0.437 |
| H4_SPLIT_60D · sensitivity | TESTED | 38/38 | 129/129 | 0.0 | 0.5 (0.348, 0.652) | 0.279 (0.209, 0.362) | 0.0176 | 0.2647 (0.0441, 0.4706) | 1 | 3.071 | 0.5 | 0.437 |
| H4_SPLIT_252D · sensitivity | TESTED | 38/38 | 129/129 | 0.0 | 0.868 (0.727, 0.942) | 0.55 (0.464, 0.634) | 0.0003 | 0.3015 (0.1103, 0.4706) | 1 | 4.893 | 0.132 | 0.437 |
| H5_JOINT | TESTED | /38 | / |  |   |   |  | 0.2868 (0.0074, 0.5809) |  |  |  |  |
| H2_OFFERING · placebo T-60 sessions | TESTED | 38/38 | 129/129 | 0.0 | 0.105 (0.042, 0.241) | 0.178 (0.122, 0.253) | 0.3286 | -0.1029 (-0.2353, 0.0441) | 0 | 0.418 | 0.895 | 1.0 |
| H4_SPLIT · placebo T-60 sessions | TESTED | 38/38 | 129/129 | 0.0 | 0.395 (0.256, 0.553) | 0.217 (0.155, 0.296) | 0.0352 | 0.125 (-0.0662, 0.3162) | 0 | 1.84 | 0.605 | 0.359 |

## 4. Hypotheses (§22)

| id | verdict (association) | evidence |
|---|---|---|
| H1_FLOAT | **NOT TESTABLE (F — missing history)** | NOT_TESTABLE (fewer than 10 positives with a point-in-time value — prereg §O) |
| H2_OFFERING | **UNSUPPORTED (98.75% CI includes 0)** | discovery +0.132 (-0.1316, 0.4211) · validation -0.1667 · pooled 0.0 (-0.1765, 0.1912) |
| H3_BORROW | **NOT TESTABLE (F — missing history)** | NOT_TESTABLE (fewer than 10 positives with a point-in-time value — prereg §O) |
| H4_SPLIT | **UNSUPPORTED (availability not point-in-time verified ≥ 80%)** | 0.417 |
| H5_JOINT | **TESTED** | 0.4342 (0.0395, 0.8289) |
| H6_NULL | **SUPPORTED** | the available historical data cannot distinguish selected from matched securities on these features |

## 5. Separate verdicts (§23)

### H1_FLOAT
- STATISTICAL DISCRIMINATION: **NOT TESTABLE (F — missing history)** — NOT_TESTABLE (fewer than 10 positives with a point-in-time value — prereg §O)
- HISTORICAL AVAILABILITY: **VERIFIED (point-in-time)** — positives 5/23 · controls 28/73 · differential -16.6 pts · verified share 1.0
- DIRECT METHOD SUPPORT: **SUPPORTED (direct)** — «الحد النهائي 5 ملايين» · «5 ملايين أو أقل — مطابق» (TG_57915/57918/57919 · `faisal_adopted` · `FWD_FLOAT_MAX`)
- CAUSAL INTERPRETATION: **NOT ESTABLISHED** (association ≠ use; §M falsifiers reported in the tables: placebo/necessity)
- PRODUCTION RELEVANCE: **none claimed** (§24)

### H2_OFFERING
- STATISTICAL DISCRIMINATION: **UNSUPPORTED (98.75% CI includes 0)** — discovery +0.132 (-0.1316, 0.4211) · validation -0.1667 · pooled 0.0 (-0.1765, 0.1912)
- HISTORICAL AVAILABILITY: **VERIFIED (point-in-time)** — positives 23/23 · controls 73/73 · differential 0.0 pts · verified share 1.0
- DIRECT METHOD SUPPORT: **CONTRADICTED/AMBIGUOUS** — «لا إعلان طرح» as an exclusion (method ⑤) **and** «طرح» as a founding event (TG_2077) — the corpus states both directions
- CAUSAL INTERPRETATION: **NOT ESTABLISHED** (association ≠ use; §M falsifiers reported in the tables: placebo/necessity)
- PRODUCTION RELEVANCE: **none claimed** (§24)

### H3_BORROW
- STATISTICAL DISCRIMINATION: **NOT TESTABLE (F — missing history)** — NOT_TESTABLE (fewer than 10 positives with a point-in-time value — prereg §O)
- HISTORICAL AVAILABILITY: **VERIFIED (point-in-time)** — positives 3/23 · controls 14/73 · differential -6.1 pts · verified share 1.0
- DIRECT METHOD SUPPORT: **SUPPORTED (verbatim)** — «تحت 20 ألف» (IMG_0151 · `BORROW_AVAIL_MAX` · `faisal_verbatim`) · «شورته 10K» · «باقي 80 الف شورت ننتظر»
- CAUSAL INTERPRETATION: **NOT ESTABLISHED** (association ≠ use; §M falsifiers reported in the tables: placebo/necessity)
- PRODUCTION RELEVANCE: **none claimed** (§24)

### H4_SPLIT
- STATISTICAL DISCRIMINATION: **UNSUPPORTED (availability not point-in-time verified ≥ 80%)** — 0.417
- HISTORICAL AVAILABILITY: **PARTIAL** — positives 23/23 · controls 73/73 · differential 0.0 pts · verified share 0.417
- DIRECT METHOD SUPPORT: **SUPPORTED (concept) · number engineering** — «توها مقسمة» · founding event «مقسم أو طرح أو نقل من otc» (TG_2077); the 120-day window is `SPLIT_LOOKBACK_DAYS` (tagged `unsourced`)
- CAUSAL INTERPRETATION: **NOT ESTABLISHED** (association ≠ use; §M falsifiers reported in the tables: placebo/necessity)
- PRODUCTION RELEVANCE: **none claimed** (§24)

## 6. Predictions P1–P6 (written before any number)

- P1 ✅ H3 NOT TESTABLE (3/23 · 1/15). · P2 ✅ float availability differential −16.6 pts (discovery), `dei` is shares outstanding not float. · P3 ✅ H4 testable 38/38. · P4 ✅ CIK resolved 234/238 (3/46 episodes unresolved). · P5 ✅ no family meets §N in both halves. · P6 ✅ H5 not decisive (validation CI includes 0).

## 7. Verification limitation behind the H4 verdict (amendment A1)

| group | domestic filers (8-K/10-Q) | foreign filers (6-K/20-F) |
|---|---|---|
| positives (filer type) | 18 | 20 |
| controls (filer type) | 38 | 33 |
| SEC-confirmed reverse splits · positives | 17/18 | 0/22 |
| SEC-confirmed reverse splits · controls | 56/58 | 1/46 |

Post-hoc (non-confirmatory) H4 on domestic filers only:

| mode | positives | strata | pos rate | ctrl rate | matched diff [98.75%] | verified | status |
|---|---|---|---|---|---|---|---|
| discovery | 9/9 |  |  |  |   | 0.905 | NOT_TESTABLE (fewer than 10 positives with a point-in-time v |
| validation | 9/9 |  |  |  |   | 0.846 | NOT_TESTABLE (fewer than 10 positives with a point-in-time v |
| all | 18/18 | 14 | 0.778 | 0.393 | 0.3333 (0.0, 0.6429) | 0.87 | TESTED |

## 8. Lookahead and integrity check

- Every value used carries a record date strictly before T (git commit day, harvest day, SEC `filingDate`, split effective date); `LOOKAHEAD_SAFE=1` on all used rows; SEC `acceptanceDateTime` recorded per filing.
- Discovery results were committed (`f4751b3b`) before `analysis.py validation` was run; validation membership was fixed by hash in the prereg (PR #582).
- Matching never used the tested features; balance SMDs on the matching variables are −0.004 / 0.081 / 0.100; the non-matched `rsplit_252` SMD is 0.633 (that is H4 itself, reported not hidden).
- Controls carry `UNKNOWN` labels (absence of a post); no UNKNOWN was treated as a negative in prose; the only alternative tier (`NEGATIVE_OBSERVED`) needed a coverage argument that the corpus cannot supply for the pool, so the sensitivity in prereg §F was not run (0 qualifying controls).
- No threshold, window or classification was changed after seeing numbers; the only post-hoc computation is labelled POST-HOC and recorded in `PHASE5_PREREG_AMENDMENT.md`.
- Anchors DKI/SXTC/HUBC and the four bar-less tickers appear in no test; HUBC's label was not invented.

## 9. Adversarial passes (10)

1. *Is the H4 signal a pool artifact?* Partly possible: 43% of matched controls were themselves split within 120 d; the matched difference is within eligible, price/ATR/volume-matched securities, but the pool is bot-adjacent (category E).
2. *Could Yahoo have back-filled splits after T?* Split effective dates are public before T; the risk is omission (foreign issuers), which biases H4 **toward the null** for foreign names, not away.
3. *Is H2's validation CI (−0.317, −0.050) a real effect hidden by discovery?* The prereg requires discovery first; the discovery sign is opposite; pooled is 0.000. Treated as instability, not as evidence.
4. *Did the bot's own selections leak into float availability?* Yes — that is P2; H1 is therefore untestable and availability-confounded, not merely underpowered.
5. *Are controls truly non-Faisal?* They have no unit of any class (MENTION/UNKNOWN/EXIT included); but Faisal's visible output is a sample, so their label is UNKNOWN (§4).
6. *Does the placebo prove decision-time specificity?* It shows the difference is smaller at T−60 (CIs include 0); it does not prove that Faisal *used* the split (Q-A ≠ Q-C).
7. *Multiple testing:* 4 families at 98.75%; sensitivity windows and H5 are reported but not corrected because they are not confirmatory.
8. *Cluster reuse of controls (max 6):* bootstrap resamples positive strata; control reuse induces positive correlation that narrows CIs slightly — the direction of this bias is toward false positives, so it strengthens the negative verdicts and weakens the H4 discovery CI.
9. *Small n:* 23/15 positives; a true effect of +0.15 would be missed with high probability (G).
10. *Could the verification floor have been foreseen?* Yes; it is an error in the prereg's operationalisation (A1). The verdict is reported as the prereg demands, and the error is published.
