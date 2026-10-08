# IMAGE_UTILIZATION_FINAL_AUDIT — every image on disk, classified and traced (2026-10-08)

> Per-image table: `IMAGE_UTILIZATION_TABLE.csv` (772 rows = every file in `faisal_images/`). This file is the summary and the honesty statement about coverage.

## 1. Coverage — what was actually inspected in THIS mission (not inherited)
| Set | n | How |
|---|---|---|
| Images on disk | 772 | `ls faisal_images/` (552 TG · 105 IMG · 70 X · 22 CH · 13 EDU · 8 APP · 2 WA) |
| Re-inspected by eye in this mission (pixels, not OCR) | **64** | listed in `EYE_READ_FM=yes`; chosen by mission relevance: DKI/SXTC/HUBC/CRE, pipeline/app screenshots, RSI/volume/gap/wait/ready rule images, B4 batch |
| OCR snippet pass (keyword hits) | 203 | rsi 71 · volume 129 · gap 11 · wait 66 · ready 25 (overlapping) — text only |
| Inherited classification (V3/V4/EX inventory, 769 rows) | 772 − 4 | every disk image except TG_58524–58527 (B4 batch, eye-read here) |
| Not in inventory | 4 | TG_58524–58527 (B4, sealed 2026-10-08, eye-read in the previous segment of this mission) |
| Inventory-only (no file) | 1 | UPLOAD_owner-2026-10-07-1 (the HUBC chart card; not pushed by rule) |

**Honesty statement:** 708 of 772 images were NOT re-read pixel-by-pixel in this mission; their ROLE/DECISION come from prior passes (V3 forensic index, V4 visual pass 609 units, EX corpus audit). The mission text asked to distrust prior manifests; the compromise taken: every mission-relevant image (anchor tickers, pipeline, volume/gap/RSI/readiness rules, B4) was re-read, and the remainder is carried with its inherited label and the explicit flag `EYE_READ_FM=""`. Re-reading all 772 by eye is a separate task (estimated ≥ 10 hours of inspection) and is listed as an open item, not claimed done.

## 2. Classification (inherited + eye corrections)
| ROLE | n |
|---|---|
| VALIDATION_CASE (dated/ticker decision) | 263 |
| CONTEXT_ONLY | 256 |
| RULE_EVIDENCE | 219 |
| COUNTEREXAMPLE | 22 |
| NON_EVIDENCE | 8 |
| NOT_IN_INVENTORY (B4) | 4 |

Faisal decision labels across images: NONE 483 · WAIT 141 · UNKNOWN 52 · READY 21 · WATCH 20 · MULTI 8 · REJECT 6 · (B4) 4. **WAIT outnumbers READY 7:1** — the corpus is a corpus of waiting, which itself is evidence about the method.

## 3. "Was the information actually used?" — per image, by trace class
| USED_CLASS | n | Meaning |
|---|---|---|
| PRODUCTION_LEDGER_CITED | 114 | cited as evidence for a live threshold/line in `FAISAL_SOURCE_LEDGER.md` (tags: faisal_verbatim 176 citations, faisal_adopted 52, third_party 43, faisal_inferred 30, engineering 18) |
| V4_RULE_CITED | 42 | cited in `rules_v4.py` (frozen V4 engine, research — not production) |
| V4_VISUAL_PASS | 565 | read in the V4 eye pass (609 units), used for cases/labels, no production effect |
| TRACED (EX inventory T-CASE/T-CLOSED/T-PROD/T-NONGEN) | 31 | traced to a case, a closed axis, or a production doc |
| NOT_TRACED | 20 | 13 CONTEXT_ONLY + 4 B4 + 2 RULE_EVIDENCE (TG_1806, TG_2076) + 1 VALIDATION_CASE — see §5 |

**Production reality check:** "cited in the ledger" ≠ "drives READY NOW". Of the 114 production-cited images, the only ones whose rule is a *decision* input to READY NOW are those behind M9 (gap above), M10 (RSI band), the borrow gate (20k) and the split recipe (separate tool). The images behind the sweep/pressure trigger (TG_57894, TG_57870, TG_2097, WA_31, TG_1822 — 5 images, DIRECTLY_SUPPORTED) feed **display lines only** (`pivot_cycle`, `PIVOT_SWEEP_PCT`) and the optional `sweep_confirmed` mode. The images behind the staged pipeline (X_22/X_23) feed **nothing** in code.

## 4. Mission-relevant images re-read by eye (64) — key corrections vs inherited labels
- EDU_20260827_ma_rizq_rule_sle: inventory ticker = DKI (WAIT); the visible chart is SLE and the text is from the educational channel (third-party). DKI attribution UNVERIFIED by eye.
- TG_58386: owner chart (DKI post-collapse), undated → cannot be a decision; inherited CONTEXT_ONLY is correct.
- TG_58527: author inferred (no name); its 6.31 target failed (max 3.27) — a forecast kept as negative evidence.
- X_20260918_61_VEEE: carries the clearest statement that current volume is not the basis (prior concentrated liquidity is) — inherited as "V4_RULE_CITED" for R4-ENT-02/STOP only; its volume statement was NOT used anywhere → added to `VOLUME_FORENSICS.md`.
- TG_2103: CRE open since 2025-08 — inherited CONTEXT_ONLY; now used as focus-persistence evidence.
- IMG_0486 (UPC): the retest-entry example — inherited V4 cited (R4-CYC-01 via IMG_0488 sibling); used here for EARLY_READY mechanism.

## 5. Not traced (20) — disposition
- TG_58383/84/85/88/89/95/97/98/99, TG_58405/10/12/22 (13, CONTEXT_ONLY, B48 batch, mostly owner screenshots of charts/apps): no rule content by inherited pass; not re-read here except TG_58386 — **UNVERIFIED**.
- TG_1806, TG_2076 (RULE_EVIDENCE, low-info): inherited as duplicates of catalogued rules; not re-read — UNVERIFIED.
- TG_58524–58527 (B4): sealed cases CASE_0002/0003 + SXTC contaminated; fully read in this mission.

## 6. Answer to "is the entire corpus primary evidence?"
It is treated as such for every image that carries a dated decision or a rule statement; 302 inventory rows are fully dated, the rest carry partial/unknown dates and cannot enter a timeline without inference (dates marked «2026-09-2x» etc. are kept as ranges, never collapsed to a day).
