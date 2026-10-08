# CORPUS_REVERIFICATION_REPORT — evidence status of every image, and whether unverified evidence could change the conclusions (2026-10-08)

> Per-image table: `CORPUS_EVIDENCE_STATUS.csv` (772 files + 2 non-file units). Inherited labels are **not** counted as visual verification.

## 1. Verification status (772 files on disk)
| Status | n | Definition |
|---|---|---|
| VISUALLY_VERIFIED_NOW (Phase 2, this protocol) | 34 | re-read pixel-by-pixel today, selected by materiality keywords (split, pipeline, M2/52-week, rejection, focus, ready, anchors) |
| VISUALLY_VERIFIED_NOW (Phase 1, same day) | 64 | re-read in the Phase 1 mission (anchors, pipeline, RSI/volume/gap rule images, B4) |
| PREVIOUSLY_VISUALLY_VERIFIED | 511 | read by eye in the V4 visual pass (609 units, 2026-10-02), the EX eye pass or the B48 intake (2026-10-07); their *labels* are inherited, their *content* was seen |
| DUPLICATE | 160 | SHA/pHash duplicate of a verified unit (inventory `DUPLICATE_STATUS` ≠ UNIQUE) |
| INHERITED_LABEL_ONLY | 3 | owner screenshots not in any eye pass (TG_58383-family remainder) — UNKNOWN content |
| OCR_VERIFIED / METADATA_ONLY | 0 / 0 | every non-duplicate file had at least one eye pass |
| Non-file units | 2 | the HUBC chart card (verified in Phase 1) · the owner's ≈10 chat screenshots of 2026-10-08 (**INACCESSIBLE**) |

Honesty line: 98 of 772 files (12.7%) were re-read on 2026-10-08; 511 rest on earlier eye passes by the same reader; the inherited **labels** of those 511 were not re-derived.

## 2. Materiality of the 34 Phase 2 re-reads
MATERIAL 20 · NON-MATERIAL 14 (duplicates, third-party, owner UI). Of the 20 material images, **3 change or refine a Phase 1 conclusion**:
1. **X_20260918_13_NUWE** + **IMG_0689**: the trigger has a *no-sweep* branch («ثبات ع الدعم الأول = تحميل مشاركات، أو كسره لسحب السيولة») → the Phase 1 state machine's TRIGGER is MODIFIED (`FAISAL_STATE_MODEL_REASSESSMENT.md`).
2. **TG_1807** (+ TG_1811, TG_1813, TG_1824, TG_2200, IMG_0291, TG_1958): Faisal's time and price reference for a split stock starts **at the split** (MA30 counted from the split date; the first post-split open/high ÷2 as the expected low; the post-split high as the liberation level). This is the corpus answer to §8 "what is M2": Faisal's chart reference is the **post-split regime**, never a 52-week high. It does not change the Phase 1 verdict; it sharpens the mechanism.
3. **X_20260827_checklist_7points**: «تاريخ التقسيم» is an explicit selection input — a split is *context* to Faisal, not a rejection.
The remaining 17 material images reinforce existing rules (post-split ÷2 recipe, hold 3–5 sessions, RSI<30 readiness, operator wait, orders at support, numbered watch items).

## 3. Can unverified evidence change the conclusions?
- The 511 PREVIOUSLY_VISUALLY_VERIFIED files were all seen by eye before; the risk is label drift, not unseen content. The keyword sweep over their OCR text (split 86 · focus 36 · ready 35 · M2 4 · pipeline 3 · anchors 2) was used to pick the 34 re-reads; the remaining keyword hits (≈120 files) are mostly chart cards of single tickers (APP_*, IMG_*) whose text content is short levels; **possible impact: LOW; status UNKNOWN for Phase 2 purposes.**
- The 3 INHERITED_LABEL_ONLY files and the owner's 10 chat screenshots: **UNKNOWN**; the latter could contain new Faisal decisions (the owner must send them to the bot).
- No image in the corpus mentions a 52-week-high drop percentage, a "base range %" or a two-touch anchor; the search for such text was negative (M2 keyword group: 4 hits, all about post-split opens, not 52-week highs).

## 4. Was Phase 1's "no evidence gap" conclusion justified?
Partly. Phase 1 said 708 files were "carried with inherited labels"; it did not claim they were unseen, but it also did not state that 511 of them had an earlier eye pass. The correct statement is above. One material refinement (no-sweep trigger branch) was missed in Phase 1 and is now recorded.
