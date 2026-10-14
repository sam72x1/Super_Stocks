# T-LAYERS — three layers: follow-up ⟶ readiness ⟶ TRIGGER (research and display only)

Owner's prompt 2026-10-14 («T-LAYERS: ثلاث طبقات · متابعة ⟵ استعداد ⟵ زناد» — permission for this axis only). No production, V4, H6,
Telegram, threshold, root or LOGIC_VERSION change. Nothing here is imported by the bot, scheduled, or sent anywhere. No gate is proposed.

| file | role |
|---|---|
| `T_LAYERS_prereg.md` | the contract — SHA-256 pinned in `layers_test.py`; merged into `main` (#619) before any trigger is counted |
| `T_LAYERS_addendum_1.md` | addendum 1 (2026-10-14): GEN5 daily bars carry no volume (the first sealed run crashed before any count) ⟶ one volume source per symbol (today_bars, else the rank archive) · unknown ≠ zero · undetermined combo days excluded · under 15 of 20 ⟶ no measure · pinned and merged before any count |
| `T_LAYERS_addendum_2.md` | addendum 2 (2026-10-14): the not-first search stopped at a day reading another base (INDP 08-21/08-25 on base 1.01) instead of skipping it as the contract says ⟶ fixed · the descriptive source agreement the contract asked for · run 1 published verbatim and kept in `data/run1/` · the verdict is read on run 2 |
| `layers_test.py` | stage A (frequency over 20 sessions) and stage B (the 107 movers: captured · missed with the failing condition · false alarms · production ready on the same window · sweep depth) ⟶ `data/layers_result.json` · `data/*.csv` · `--guards` LG1–LG30 |
| `layers_mutate.py` | mutation round over the guards (43/43 fall, no crash) |

The trigger is read on the production cycle `Super_stock.pivot_cycle_state` by name (base = `pc.bottom`); the five core conditions are
Faisal's words (`IMG_0297` 7–13 % · `TG_57894` the reclaim · one trigger per base · invalidation under the sweep low). The boosters VOL
(`link100_probe.daily_feats`, by name) · NODE and CANDLE (engineering) are measured one by one and combined only by the written rule.

Order (repo root; the run refuses with exit 9 unless origin/main carries the pinned contract and addenda 1–2 and the production functions are unchanged):

    git fetch --force origin main
    python3 fm_forensics/layers/layers_test.py --guards
    python3 fm_forensics/layers/layers_mutate.py
    python3 fm_forensics/layers/layers_test.py          # once, after the merge
