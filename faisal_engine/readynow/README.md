# READYNOW — early technical readiness before a +70% move (research only)

Mission «RECONSTRUCT READY NOW — DISCOVER EARLY TECHNICAL CONDITIONS AND VALIDATE AGAINST THE HISTORICAL EXPLOSION
UNIVERSE» (2026-10-11). Offline, read-only, no production change. Main report: `RN_REPORT.md`. Sealed specification:
`RN_SPEC.md` (SHA-256 pinned in `rn_eval.py`).

| file | role |
|---|---|
| `rn_build.py` | builds `data/rows.csv.gz` (every pivot-day: conditions from bars ≤ t, onset labels), `events.csv.gz`, `seeds.csv.gz`, `ewin.csv.gz` (every clean episode's T−10 … T−7, pivot or not), `calendar.json`, `inventory.json`; `--check` regenerates and compares |
| `rn_lib.py` | the conditions, combinations, candidate, comparators, windows, matching, equal-burden rankings, bootstrap — shared by development and evaluation |
| `rn_dev.py` | `seeds` → `data/seeds_matrix.json` · `dev` → `data/dev.json` · `dev2` → `data/dev_round2.json` (development window only) |
| `rn_eval.py` | `final` → `data/result.json`: validation and holdout once, after the specification hash check; HUBC's current state |
| `test_rn.py` | guards G1–G8 (`R70_FAST=1` skips the slow G7) |
| `rn_mutate.py` | one mutation per guard → `data/mutations.json` |

Reused read-only: READY70 (`faisal_engine/ready70/`: bars, splits, the bot's explosion detector, the pivot population
`pi_obs.csv.gz`, its features) and SEQ70 (`faisal_engine/seq70/`: path descriptors, L10).
Run order: `rn_build.py` → `rn_dev.py seeds|dev|dev2` → (seal) → `rn_eval.py final` → `test_rn.py` → `rn_mutate.py`.
All git reads with `GIT_ALLOW_PROTOCOL=file` (partial clone).

**Audit (2026-10-11): `audit/RN_AUDIT.md`.** Did READYNOW test the documented conditions? It tested one candidate. Only
two of the app's eight conditions are reproducible from local data, with parity shown in `audit/data/chip_parity.json`.
Those two (within 15% ∧ bounce 10–40%) were evaluated once under `audit/APP_POS_PREREG.md`: PROMISING_UNVALIDATED,
but not a READY signal. `audit/test_audit.py` (A1–A5) · `audit/audit_mutate.py`.

**Reconciliation (2026-10-11): `recon/RN_RECON.md`.**
- **Seed timelines.** Every episode of DLXY, RETO, DKI and SXTC is covered; HUBC is kept separate. DKI's reported
  2026-10-07 move is intraday only and is not a daily-close event; DKI's two earlier daily-close events are listed.
- **Why the label limit is 2026-08-27.** READYNOW anchors its onset on the trough, and the detector fires up to 19
  sessions later. A label anchored on the detection date runs to 2026-09-24.
- **Seed inclusion.** The seeds entered no READYNOW or APP_POS statistic. They did enter READY70, SEQ70 and ALERTS70,
  as ordinary rows.
- **The anchor changes the answer.** READYNOW measured «7–10 sessions before the move starts», not «before it
  qualifies»; only 22% of positive rows agree between the two. In development, the oversold-type rules weaken under
  the detection anchor.
- **Development-only discovery.** Two never-tested source-backed structures — room to the nearest resistance and
  unfilled gaps above — show no separation.
- **Next step.** The single next experiment is prospective: the tool's float and available-to-borrow conditions,
  captured forward.
- **Files.** `recon/rn_recon.py` (`--check`) · `rn_anchor_dev.py` · `rn_room_dev.py` · `rn_gap_dev.py` ·
  `test_recon.py` (RC1–RC7) · `recon_mutate.py`.
