# PHASE 5 — FINAL VERDICT

**Mission:** NON-CANDLE INFORMATION × FAISAL STOCK SELECTION — historical availability × matched controls × independent validation × causal falsification.
**Pre-registration:** `PHASE5_PREREG.md` merged in PR #582 (`4249c764`) before any feature–outcome number. Discovery frozen at `f4751b3b` before validation was read. Numbers: `out/results_{discovery,validation,all}.csv`, built into `PHASE5_FINAL_REPORT.md` by `report.py`.
**Scope lock honoured:** no change to V4, the scanner, gates, thresholds, Telegram, the prospective validation or the labels; no V5/READY_NOW_V2; research files only under `fm_forensics/phase5/` (the temporary SEC probe workflow was removed after its single read-only run `37857848711`).

## Cohort (§5)

38 primary units (one per non-anchor security with bars; discovery 23 / validation 15) from 45 securities, 46 episodes, 88 dated units; anchors DKI/SXTC/HUBC descriptive only; ATPC/LABT/MI/UNK listed and excluded (no bars). Matched controls: 134 control-days, 71 securities, 34/38 positives matched (prereg §H; tested features not used for matching).

## Separate verdicts (§23) — per family

| family | STATISTICAL DISCRIMINATION | HISTORICAL AVAILABILITY | DIRECT METHOD SUPPORT | CAUSAL INTERPRETATION | PRODUCTION RELEVANCE |
|---|---|---|---|---|---|
| **H1 float ≤ 5M** | **NOT TESTABLE** (5/23 discovery · 5/15 validation positives with a point-in-time float; §O floor 10) | **UNVERIFIED for the cohort**: point-in-time float exists only where a bot state file stored it (12/46 episodes); controls 40/129; `dei` shares outstanding (36/43 positives) is an upper bound, not float | **SUPPORTED (direct)** — «الحد النهائي 5 ملايين» (`faisal_adopted`) | not reachable | none claimed |
| **H2 final prospectus ≤ 90 d (fewer in selected)** | **UNSUPPORTED** — discovery +0.132 (98.75% CI −0.132, +0.421; sign *opposite* to the hypothesis); validation −0.167 (−0.317, −0.050); pooled 0.000 (−0.177, +0.191). The two halves disagree in sign ⇒ no replicated association | **VERIFIED** — EDGAR filings with acceptance timestamps for 23/23 and 15/15 positives, 73/73 and 59/59 controls (CIK unresolved for 3 of 46 episodes) | **CONTRADICTED/AMBIGUOUS** — the corpus states «لا إعلان طرح» (exclusion) and «طرح» as a founding event | not established | none claimed |
| **H3 borrow available < 20k** | **NOT TESTABLE** (3/23 · 1/15 positives with a dated snapshot; §O) ⇒ **BORROW_AVAILABILITY_HYPOTHESIS = NOT TESTABLE WITH AVAILABLE DATA** | **ABSENT before 2026-07-30** (no snapshot source); after it only the harvest cohorts | **SUPPORTED (verbatim)** — «تحت 20 ألف» | not reachable | none claimed |
| **H4 reverse split ≤ 120 d (more in selected)** | **UNSUPPORTED by §N** — the association *is* present: discovery +0.303 (98.75% CI +0.066, +0.540; MH OR 3.9), validation +0.267 (−0.050, +0.567; same sign, ≥ half the magnitude), pooled +0.287 (+0.096, +0.478); but §N's verification floor fails (0.42 / 0.46 verified) because foreign filers cannot be SEC-confirmed (amendment A1). Post-hoc domestic-only: pooled +0.333 (0.000, +0.643), touching 0 | **PARTIAL** — split dates are historical facts from a current vendor snapshot; SEC-confirmed 73/76 domestic, 1/68 foreign | **SUPPORTED (concept)** — «توها مقسمة», founding event; the 120-day number is engineering (`unsourced`) | **NOT ESTABLISHED** — placebo at T−60 sessions drops the difference to +0.079 / +0.183 / +0.125 (all CIs include 0): the signal is decision-time-specific, which is consistent with Faisal looking at recently split names *and* with "recently split" being a property of the eligible population at the time he looks; necessity fails for 26% of positives | none claimed |
| **H5 joint (H2+H4)** | discovery +0.434 (+0.040, +0.829); validation +0.100 (−0.283, +0.483) ⇒ **not replicated** | — | — | — | none claimed |
| **H6 null** | **SUPPORTED as the pre-registered outcome**: no family meets §N in discovery *and* validation | — | — | — | — |

## Attribution of what was found (§0 secondary objective)

- H4: **A (relevant feature) is possible but not demonstrated under §N; D (data-availability artifact) explains the §N failure, not the association; E (weak comparison group) cannot be excluded** — the pool is the Phase 2 bot-adjacent universe (160 symbols) in which 43% of matched controls had a reverse split within 120 days anyway.
- H2: **G (insufficient power) + sign instability** across the two halves.
- H1, H3: **F (untestable — missing history)**; for H1 also **D** (availability is itself a selection artifact: the bot stores float only for securities it selected; differential −16.6 points in discovery).

## Falsification record (§22)

H1 not falsifiable (untestable) · H2 falsified in discovery (CI includes 0, wrong sign) · H3 not falsifiable (untestable) · H4 not falsified on the association, falsified on §N verification · H5 not replicated · H6 stands.

## Predictions written before any number

P1 ✅ (H3 not testable) · P2 ✅ (float availability differential; `dei` does not rescue float) · P3 ✅ (H4 testable for 38/38) · P4 ✅ (234/238 CIKs resolved) · P5 ✅ (no family meets §N in both halves) · P6 ✅ (H5 not decisive).

## Final statement

**HISTORICAL ASSOCIATION:** unsupported for float, offering status and borrow availability (two untestable, one unreplicated); a reverse-split-age association is present and directionally replicated but does not meet the pre-registered verification floor and is not distinguishable from the eligible population's own split profile.
**HISTORICAL AVAILABILITY:** verified for SEC filings and split dates; unverified/absent for float and borrow before the bot's own records.
**DIRECT FAISAL METHOD EVIDENCE:** supported for float and borrow rules (verbatim/adopted), concept-only for split age, ambiguous for offerings.
**THE AVAILABLE HISTORICAL DATA DO NOT IDENTIFY A NON-CANDLE FEATURE THAT DISTINGUISHES FAISAL'S SELECTIONS FROM MATCHED COMPARISON SECURITIES UNDER THE PRE-REGISTERED CRITERIA. THIS IS A VALID NEGATIVE RESULT, NOT A CONTRADICTION OF THE METHOD.** No production recommendation (§24).
