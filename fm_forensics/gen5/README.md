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
| `GEN5_RESULT.md` | the verdict, written after the sealed run |

Reproduce (repo root, no network; reads `faisal_engine/data/rank/bars.json.gz` and git history):

    python3 fm_forensics/gen5/gen5_generate.py
    python3 fm_forensics/gen5/gen5_test.py --guards
    python3 fm_forensics/gen5/gen5_test.py
