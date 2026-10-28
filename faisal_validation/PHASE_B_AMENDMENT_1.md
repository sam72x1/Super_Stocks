# PHASE B — AMENDMENT 1 (2026-10-28) · an item closed EXCLUDED stays excluded after a later protocol correction

> The contract `PHASE_B_prereg.md` is **unchanged** (SHA-256 `615bf037dd33e108de01e41a2727a272b636f2ec8fd8f327adf9310c708d0737`). This file
> records how the tool applies two of its own sentences when they meet for the first time. (Not to be confused with the final protocol's
> amendment 1, which governs intake.)

## 1. What happened
- 2026-10-28 09:29 UTC: `B22_20261028` sealed; the Phase B ledger recorded its 22 images (seq ≤ 129), seven of them `CAPTURED ⟶ EXCLUDED`
  at intake (author not Faisal / not established).
- 2026-10-28 10:00 UTC: the owner stated «قناة تعليمية» is Faisal's own channel; the frozen protocol's append-only correction
  `B22_20261028/CORRECTION_01` re-classified 18 images and sealed seven cases (CASE_0009 … CASE_0015) on those seven images.
- `phase_b.py write` then computed a new due path `CAPTURED ⟶ SEALED_INPUT` for each of the seven and reported a regression on each ⟶
  `VALIDATION_BLOCKED` (`check` exit 1).

## 2. The two sentences
- §⑫: «A candidate's later events must extend its earlier ones — a regression in the protocol state is a ledger problem
  (⟶ `VALIDATION_BLOCKED`), never a deletion.»
- §⑬ (integrity test): «… an excluded case stays excluded …»

## 3. The rule applied (tool)
An item whose ledger events already end in `EXCLUDED`, and whose current protocol candidate carries `corrected_by` (the protocol's own
append-only correction), **stays `EXCLUDED` in Phase B**: no new event, no rescue, no relabelling, and its row says why
(«excluded at capture; the protocol's CORRECTION_NN re-classified it later — stays excluded in Phase B»). **Every other regression still
blocks** (§⑫ unchanged). The protocol, V4, H6 and the case files are untouched by this rule — it only decides what Phase B counts.

Effect on 2026-10-28: the seven stay excluded in Phase B (they never had a PRIMARY path: provenance LOW ⟶ SECONDARY anyway); the ledger keeps
129 records (no new event); `check` exit 0; state `INSUFFICIENT_SAMPLE` as before.

Lock `PHB12` (synthetic): an item closed EXCLUDED then corrected stays excluded with no new event and no problem; the same item without
`corrected_by` still reports the regression.

## 4. Dated addition (2026-10-28, after the V4 run `40674079524`)
- The row keeps **the exclusion code it was closed with at capture** (read from that ledger record's notes; here `E6` for all seven) instead of an
  empty code — "no relabelling" applies to the code too. Before this, the status breakdown printed a blank label («( 7, …»).
- `phase_b.py write` after the V4 run fills `v4_decision = WAIT` on the seven rows (display only); the ledger still holds 129 records and `check`
  exits 0. The V4 run workflow does not run `phase_b.py write`, so after any V4 run the loop's next step (`write` ⟶ `check`) is done by hand and
  merged — until then lock `PHB1` reads the Phase B outputs as stale (it did on `960ad80`).
- Lock `PHB12` now also requires the kept code (two mutations: empty code · a fixed wrong code — both caught).
