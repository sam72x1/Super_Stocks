# SEQ70 — the path of pivot stocks before the bot's +70% events (research · offline · read-only)

Question, inventory, reconstruction and contract: `S70_PREREG.md` (sealed before any validation or test outcome) ·
`S70_RESULT.md` (PROMISING_UNVALIDATED).

Reproduce from the repo root (no network; keep `GIT_ALLOW_PROTOCOL=file` — the clone is partial):

    export GIT_ALLOW_PROTOCOL=file
    python3 faisal_engine/seq70/s70_build.py            # traj/events/inventory from READY70 outputs + bars (≈1 min)
    python3 faisal_engine/seq70/s70_build.py --check    # outputs regenerate byte-identically
    python3 faisal_engine/seq70/s70_explore.py          # discovery-only reconstruction → data/explore.json
    python3 faisal_engine/seq70/s70_eval.py dev         # the sealed code on discovery only → data/dev_discovery.json
    python3 faisal_engine/seq70/s70_eval.py test        # the sealed test (exit 9 if the contract changed)
    python3 faisal_engine/seq70/s70_states.py           # the bot's list states (descriptive) → data/states.json
    python3 faisal_engine/seq70/test_s70.py             # guards G1–G7 (R70_FAST=1 skips the slow G7)
    python3 faisal_engine/seq70/s70_mutate.py           # 8 mutations; each must fell exactly its guard

Imports READY70 (`faisal_engine/ready70/`) read-only. Nothing here is imported by the bot, scheduled, or sent.
