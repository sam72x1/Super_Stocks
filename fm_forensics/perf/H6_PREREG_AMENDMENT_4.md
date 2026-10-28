# H6 — AMENDMENT 4 (2026-10-28) · one tool-defect fix: the intake reading honours the protocol's own append-only corrections

> The contract `H6_PREREG.md` is **unchanged** (SHA-256 `a6f68f745cba189223b1f8258e733dc5e1e538382dfe6533307092d8e942c7ed`, still pinned in
> `h6_test.py`). §10 allows a tool-defect fix with a bit-identical check; this file records it. Trigger: the owner's order 2026-10-28
> «صحّح وسم المصدر للـ22 صورة إلى فيصل بتصحيح إلحاقي (correct) … وأعد تقييم حالات H6 على هذا الأساس».

## 1. The defect (proven)
- Contract §1 names `intake/<BATCH>/annotations.json` as a decision source. The frozen protocol never edits that file: a later eye reading
  of an image in a sealed batch is an append-only `intake/<BATCH>/CORRECTION_NN.json` (final protocol amendment 1 §⑥), and the protocol's
  own candidates read it (`final_protocol.batch_candidates`: the latest correction replaces the image's candidate).
- `h6_test.py` `load_annotations` read `annotations.json` only. After `B22_20261028/CORRECTION_01` (2026-10-28 10:00 UTC — author ⟶ Faisal on
  the owner's statement), the protocol sealed seven cases (CASE_0009 … CASE_0015, all T = 2026-10-27) while H6 still saw
  `faisal_author = false` for their images ⟶ all seven `INELIGIBLE` (`E1:no_intake_annotation`) on the tool's status run.
- Effect if left: every case created by a correction is permanently ineligible in H6, whatever Faisal later says — the protocol and H6
  disagree about the same image.

## 2. The fix
`load_annotations` reads `annotations.json` as before, then, per batch, applies its `CORRECTION_NN.json` files in file order: each image a
correction names replaces that image's reading (`symbol` · `decision_date` · `decision_date_max` · `faisal_author`) and carries
`corrected_by`. An image the batch's `annotations.json` does not name is ignored (a correction cannot add an image — as the protocol). A
batch without corrections is read bit-identically. Nothing else in H6 changes (E1–E7, windows, controls, families, analysis).

Lock `H6X1` (behavioural, synthetic intake root): the corrected image flips to `faisal_author = true` with `corrected_by`, an uncorrected image
in the same batch is unchanged, a correction naming an unknown image adds nothing, and a batch without corrections reads exactly as before.

## 3. Bit-identical check (repository state of 2026-10-28 after `CORRECTION_01`, old loader vs new loader, `today` = 2026-10-28)
- Every case other than CASE_0009 … CASE_0015 has the same status and code with both loaders (8 of 8: HISTORICAL 3 · REPEAT 1 · NOT_COVERED 1 ·
  ELIGIBLE 3 — BKYI · CYCU · ICMB).
- CASE_0009 … CASE_0015: `INELIGIBLE (E1:no_intake_annotation)` ⟶ `PENDING_REVEAL (E2:not_revealed)` — they wait for the frozen V4 run and
  then Faisal's word, exactly like any other freshly sealed case.
- Eligible units 3/15 before and after; coverage failures 1 before and after.

## 4. What this does not do
It does not make any of the seven a unit. Under the unchanged contract, after the V4 run and the reveal: BRTX (prior Faisal decision
2026-10-05) and CYCU (2026-10-23) fall to `REPEAT` (E4, within 30 sessions); FBGL · GNPX · BTOC · NIVF · BRAI need a positive label (E2) and a
Phase 6 collection day in [2026-10-27, 2026-11-03] (E5) with controls (E6).
