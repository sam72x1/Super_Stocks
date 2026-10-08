# CRE_FORENSICS — control case: bot READY while Faisal WAIT (2026-10-08)

## Timeline (lookahead-safe)
| Date | Source | Fact |
|---|---|---|
| 2025-08-02 | TG_2103 (Faisal X list) | «$CRE -10 مفتوحه» — open position; CRE in Faisal's focus ≥ 13 months before any bot READY |
| 2026-08-16 → 09-05 | near_watch | n_out = 0 (inside envelope), RSI 43–48, shown 08-16/17/18 at ranks 10–20 of the inside list |
| 2026-08-29 → 09-24 | near_watch | n_out = 1 (price 2.9–3.9 then back), RSI 46–55 |
| 2026-09-2x | TG_57869 (Faisal) | gap below must be covered → **WAIT** |
| 2026-09-25 → 10-03 | near_watch | n_out = 0 again, RSI 43–50 (never oversold) |
| 2026-10-06 | weekly_watchlist / alerts_history | **added**, `sweep_confirmed`, READY NOW; price 2.67, stop 2.54, t1 3.00, t2 3.42, t3 9.84; flags include «ثبات 5 جلسات فوق القاع» |
| 2026-10-07, 10-08 | wl snapshots | still READY NOW |
| outcome | — | OPEN / UNKNOWN |

## Layer trace
- L2–L5: passed (identity, soft fails, tested level) on 10-05 bars.
- L10: `sweep_confirmed` → ready_now.
- Faisal's validity layer (gap below unfilled) has no bot counterpart → divergence at a **validity** step that the bot does not have, not at a trigger step.

## Classification
- READY_WITHOUT_FOCUS-TRIGGER → **EARLY_READY candidate** (bot ready 10-06; Faisal still waiting). Confirmation requires the gap fill date and the subsequent move (bars probe).
- RSI never below 33 during the whole observed window (43–55): CRE is a case where Faisal's focus is NOT driven by oversold RSI — evidence against making RSI < 30/33 a focus requirement (it is a *readiness* requirement in his words, TG_2043).

## What the owner should expect from this case
If CRE fills the gap and then moves, the bot's READY was early but on-thesis; if it moves without filling, Faisal's gap rule was over-cautious here (one case, no generalization either way).
