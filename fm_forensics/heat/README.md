# T-HEAT — does pre-move "heat" separate movers inside the bot's tracked population? (research only)

Owner's prompt 2026-10-13 («`T-HEAT`: هل السخونة قبل الحركة تميّز داخل مجتمع متابعتي؟» — permission for this axis only).
No production, V4, H6, Telegram, threshold or root change. Nothing here is imported by the bot, scheduled, or sent anywhere.
GEN5 (verdict C, `f10fb23`) is not redone; its functions are reused by name only.

| file | role |
|---|---|
| `T_HEAT_prereg.md` | the contract — SHA-256 pinned in `heat_test.py`; merged into `main` before any number |
| `heat_test.py` | the sealed run (anchors O and B, verdict by the weakest) ⟶ `data/heat_result.json` · `data/heat_units.csv` · `--guards` = synthetic guards H1–H12 |
| `heat_mutate.py` | mutation round over the guards (each mutation must fall, not crash) |
| `T_HEAT_result.md` | the result: **D «لا قياس»** (onset anchor O: 31 events, design MDE 0.275 > 0.25) · leaky anchor B: C (Δ UNION +0.022) — table first, leads, leakage, deviations (post-seal crash fix `9b0778450`), predictions 3/7, how to enlarge |

Order (repo root, no network; reads GEN5 inputs `faisal_engine/data/rank/bars.json.gz`, `fm_forensics/gen5/data/gen5_ext.json.gz` and git history):

    git fetch --force origin main                 # run() refuses (exit 9) unless origin/main carries the pinned contract
    python3 fm_forensics/heat/heat_test.py --guards
    python3 fm_forensics/heat/heat_mutate.py
    python3 fm_forensics/heat/heat_test.py        # once, after the merge
