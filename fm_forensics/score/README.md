# T-SCORE — a continuous closeness score to Faisal's conditions, weighted from his words (research only)

Owner's prompt 2026-10-14 («T-SCORE: درجةُ قربٍ موزونةٌ من كلام فيصل» — permission for this axis only). No production, V4, H6, Telegram,
threshold or root change. Nothing here is imported by the bot, scheduled, or sent anywhere. No gate is proposed.

| file | role |
|---|---|
| `T_SCORE_prereg.md` | the contract — SHA-256 pinned in `score_test.py`; merged into `main` before any number |
| `score_tags.py` | stage A layer ③: Faisal's own WAIT statements (eye-read register, 772 images) ⟶ `data/wait_tags.json` · `--check` |
| `score_test.py` | the sealed run on the T-HEAT anchor-O units ⟶ `data/score_result.json` · `data/score_units.csv` · `--guards` SG1–SG22 · `--today` |
| `score_mutate.py` | mutation round over the guards (22/22 fall) |
| `score_fetch.py` | runner-side TradingView fetch of today's daily bars (run once on the temporary branch `claude/t-score-fetch`, never merged) |
| `T_SCORE_result.md` | the result — written after the single run (table first, then the verdict) |

Order (repo root; the run needs `git fetch --force origin main` first — it refuses with exit 9 unless origin/main carries the pinned contract):

    python3 fm_forensics/score/score_tags.py --check
    python3 fm_forensics/score/score_test.py --guards
    python3 fm_forensics/score/score_mutate.py
    python3 fm_forensics/score/score_test.py          # once, after the merge
    python3 fm_forensics/score/score_test.py --today  # needs data/today_bars.json.gz
