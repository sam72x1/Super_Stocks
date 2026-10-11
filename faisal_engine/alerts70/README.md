# ALERTS70 — the historical live alerts vs the bot's +70% events (research · offline · read-only)

Question, contract and result: `A70_PREREG.md` (sealed before any alert outcome) · `A70_RESULT.md`
(HISTORICAL ALERT SIGNAL NOT VALIDATED).

Reproduce from the repo root. The clone is partial: keep `GIT_ALLOW_PROTOCOL=file` so git never downloads missing
history; the extraction then reads only the snapshots already in the local object store (`A70_RESULT.md` §2).

    export GIT_ALLOW_PROTOCOL=file
    python3 faisal_engine/alerts70/a70_extract.py            # git history of op_entry_state.json → data/ (≈30 s)
    python3 faisal_engine/alerts70/a70_build.py              # link to the R70 episodes and labels → data/
    python3 faisal_engine/alerts70/a70_build.py --check      # outputs regenerate byte-identically (same for a70_extract.py)
    python3 faisal_engine/alerts70/a70_eval.py test          # the sealed test (exit 9 if the contract changed)
    python3 faisal_engine/alerts70/a70_posthoc.py --check    # post-hoc descriptives, not preregistered
    python3 faisal_engine/alerts70/test_a70.py               # guards G1–G8 (R70_FAST=1 skips the slow G8)
    python3 faisal_engine/alerts70/a70_mutate.py             # 10 mutations; each must fell exactly its guard

Imports the sealed R70 code (`faisal_engine/ready70/r70_build.py`) read-only. Nothing here is imported by the bot,
scheduled, or sent to Telegram.
