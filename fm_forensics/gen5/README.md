# GEN5 — readiness combination generated on five stocks, tested on tracked pivot movers (research only)

Owner's prompt v4 (2026-10-13). No production, V4, H6, Telegram, threshold or root change. Nothing here is imported
by the bot, scheduled, or sent anywhere.

| file | role |
|---|---|
| `GEN5_PREREG.md` | the contract — sealed (SHA-256 pinned in `gen5_test.py`) and pushed before any test number |
| `gen5_features.py` | point-in-time components at decision session t from bars[0..t] (production functions by name) |
| `gen5_pit.py` | float / available-to-borrow as the bot stored them before the next open (git history of `origin/main`) |
| `gen5_generate.py` | stage A on the five ⟶ `data/gen5_generation_days.csv` |
| `gen5_test.py` | stage C (the sealed run ⟶ `data/gen5_result.json`) · `--guards` = 9 synthetic guards |
| `gen5_post.py` | post-run readings the contract declared (LR · strict 99.5% · P5 · coverage) ⟶ `data/gen5_post.json` |
| `GEN5_RESULT.md` | the FIRST verdict (C) — **fallen by a measurement defect** (close-only outcome window), kept published |
| `GEN5_ADDENDUM_1.md` | addendum 1 — extended-session outcome · split-adjusted · anchor B · weakest reading (sealed before any corrected number) |
| `gen5_ext.py` | extended-session pure functions + the runner-side TradingView fetch ⟶ `data/gen5_ext.json.gz` |
| `gen5_fix.py` | the corrected run (two anchors) · `--guards` = 11 synthetic guards ⟶ `data/gen5_fix_result.json` · `data/gen5_fix_rows.csv` · `data/gen5_fix_generation.csv` |
| `GEN5_FIX_RESULT.md` | the corrected verdict: **C under both anchors** — rows table first, the 18 by name, contamination D1, the onset limit (§⑧) |
| (removed) `.github/workflows/gen5_ext_fetch.yml` | one-off push-triggered fetch on the session branch (TradingView is blocked in the container) — deleted after use; recoverable from commit `c5c015d` |

Reproduce (repo root, no network; reads `faisal_engine/data/rank/bars.json.gz` and git history):

    python3 fm_forensics/gen5/gen5_generate.py
    python3 fm_forensics/gen5/gen5_test.py --guards
    python3 fm_forensics/gen5/gen5_test.py
    python3 fm_forensics/gen5/gen5_post.py
    python3 fm_forensics/gen5/gen5_fix.py --guards
    python3 fm_forensics/gen5/gen5_fix.py        # needs data/gen5_ext.json.gz
