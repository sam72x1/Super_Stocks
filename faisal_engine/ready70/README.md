# READY70 — READY NOW vs the bot's +70% explosion record (research · offline · read-only)

Question, contract and result: `R70_PREREG.md` (sealed before the held-out window) · `R70_RESULT.md` (verdict B).

Reproduce from the repo root (no network, no secrets; reads git history and `faisal_engine/data/rank/`):

    python3 faisal_engine/ready70/r70_build.py            # rebuild data/ (≈1.5 min)
    python3 faisal_engine/ready70/r70_build.py --check    # every output regenerates byte-identically
    python3 faisal_engine/ready70/r70_eval.py explore     # discovery window only (2025-05-01 → 12-31)
    python3 faisal_engine/ready70/r70_eval.py test        # the sealed held-out comparison (exit 9 if the contract changed)
    python3 faisal_engine/ready70/test_r70.py             # guards L1–L8 (R70_FAST=1 skips the slow L8)
    python3 faisal_engine/ready70/r70_mutate.py           # 8 mutations; each must fell exactly its guard

Nothing here is imported by the bot, scheduled, or sent to Telegram.
