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
