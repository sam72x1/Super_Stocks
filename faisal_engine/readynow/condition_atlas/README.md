# Faisal technical condition atlas & historical READY-NOW classification (2026-10-11)

Research only. Local data, no network, no production change. Reports:

- **FINAL_FINDINGS.md** — the answer and its limits (start here)
- **RECONCILIATION_ADDENDUM.md** — post-seal reconciliation of «شمعة القروب», the missed winners, the READY classes and «RSI only» (`ca_reconcile.py`); corrected points 1, 4, 5
- SOURCE_CONDITION_ATLAS.md — 55 conditions with verbatim quotes and image ids (`ca_atlas.py`, rendered by `ca_docs.py`)
- HISTORICAL_DATA_INVENTORY.md — what the local files allow (`ca_inventory.py`)
- CONDITION_STRENGTH_RESULTS.md · CANDLE_PATTERN_STUDY.md — every condition and candle against the onset 7–10 sessions later
- READY_CLASSIFICATION_SPEC.md · HISTORICAL_CLASSIFICATION_RESULTS.md — the three-axis classifier and its sealed 2026 check (`CA_PROTOCOL.md`)
- CHART_CASEBOOK.md — seeds, HUBC, captured and missed winners, non-exploders, matched controls

Run order from the repo root (all offline):

1. `ca_build.py` — features
2. `ca_inventory.py`
3. `ca_dev.py` — development only
4. `ca_sec.py`
5. `ca_final.py` — sealed; refuses unless `CA_PROTOCOL.md` and `data/model_frozen.json` match the pinned hashes
6. `ca_verdict.py`
7. `ca_casebook.py all`
8. `ca_rows2026.py`
9. `ca_docs.py`
10. `ca_reconcile.py` — post-seal checks R0–R7 (reads the sealed files, never writes them), then `ca_reconcile.py --render`
11. `ca_report.py`

Guards: `test_ca.py` (CA1–CA14; CA_FAST=1 skips the slow regenerations CA2 and CA13). Mutations: `ca_mutate.py`
(runs without bytecode and purges the mutated module's .pyc — CA14).
