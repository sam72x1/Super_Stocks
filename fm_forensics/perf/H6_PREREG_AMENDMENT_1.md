# H6 — AMENDMENT 1 (2026-10-15) · two instrument-defect fixes, one daily status line, and a dated owner exception to §10

> The contract `H6_PREREG.md` is **unchanged** (SHA-256 `a6f68f745cba189223b1f8258e733dc5e1e538382dfe6533307092d8e942c7ed`, still pinned in
> `h6_test.py`). This file records, as §10 requires, what was fixed after merge and why. The evidence is `H6_COLLECTION_AUDIT.md` (the audit) and
> `h6_audit_proof.py` (the pre-fix reproduction, 13/13).

## 1. The owner's explicit permission (verbatim)
> «اشحن F2 · واشحن سطر الإنذار · واشحن F1 بإذني الصريح (العقد §10) لأن البِركة متجمّدة على 10-08 وكلُّ ضابطٍ قادمٍ بائتٌ بدونه»

## 2. F1 is a dated exception to §10, not a breach
§10 says «no production change during the waiting period». **F1 changes one function of the production module** (`Super_stock.py`,
`build_reject_snapshot` — the research log writer; no screening decision reads it). It is made **by the owner's explicit permission above, on
2026-10-15**, for this reason only:
- `reject_log.json` capped every wall at `REJECT_LOG_MAX_SYMS` = 400 symbols; the control wall `M_لا_مستوى_مختبر` exceeded it in every entry
  from 2026-10-09 (400 of 407 · 414 · 414 · 432) and was written `sampled`;
- §4 refuses a sampled wall ⟵ `collector.control_pool` fell back to the newest full entry, **2026-10-08**, on every panel day since
  (2026-10-09 · 10-10 · 10-13 · 10-14);
- so every control drawn from now on would come from the 2026-10-08 pool, not «the same candidate pool on the same day» (§1).
F1 **restores the condition §4 assumed** (the pool stored in full every day) **without changing the text of §4** — the refusal of a sampled
wall stays exactly as written.

## 3. What changed, exactly
| # | Change | Where | Kind |
|---|---|---|---|
| F2 | `is_session` applies the weekday rule before the holiday table (the same idiom as `faisal_method_v41/runner.py:70`) — `market_calendar.is_trading_day` does not check weekends (its own docstring), so E4 «30 sessions» and E5 «5 sessions» were counted in calendar days | `fm_forensics/perf/h6_test.py` `is_session` | tool-defect fix (§10: allowed) |
| Status | `status` prints one line daily — eligible/floor · cases after the cutoff · newest photo the bot saved and the sessions since · **the control pool date (always) and its lag in `reject_log.json` entries** — plus `::warning::` when the pool lags ≥ 1 entry or no photo came for 5 sessions; new fields in `H6_STATUS.json`: `panel.pool_date_last` · `panel.pool_obs_last` · `panel.pool_lag_entries_last` · `panel.pool_newer_entries` · `cases_after_cutoff` · `inputs.last_photo` · `inputs.sessions_since_last_photo` | `h6_test.py` `pool_lag` · `last_photo` · `load_reject_log` · `alarm_line` · `build_status` · `main`; workflow `fm_phase6_collect.yml` step «H6 daily status (no Telegram)» after the ledger check (`continue-on-error`) and `H6_STATUS.json` committed with the ledger | reporting only |
| F1 | `REJECT_LOG_FULL_WALLS = ("M_لا_مستوى_مختبر",)`: that wall is stored in full; `build_reject_snapshot(..., full_walls=None)` reads the constant at call time | `Super_stock.py` `build_reject_snapshot` | production module, research log only — the owner's exception (§2 above) |

## 4. What stays bit-identical
The contract file and its pin · H6 and H6₀ · the four features and their thresholds · windows (90 d · 120 d · 30 sessions · 5 sessions — now
counted as the contract wrote them) · the floor (15) · the matching rule · the verdict rules · `CONTROL_K` and the draw · `control_pool`
(it still refuses a sampled wall) · every other `reject_log.json` wall, its 400 cap and its deterministic sample · `REJECT_LOG_MAX_SYMS` ·
`REJECT_LOG_DAYS` (20 entries) · the twelve production roots (AST fingerprints unchanged) · V4 · the two-touch anchor · Telegram (none of the
three touches it).

## 5. Switches back to the previous behaviour
- F1: `REJECT_LOG_FULL_WALLS = ()` ⟵ the previous function bit-for-bit (locked by `H6P1`).
- Status: remove the workflow step; the step is `continue-on-error`, so it can never fail the collection.
- F2: no switch — reverting restores a proven defect. Its effect today is zero: `status` on 2026-10-15 is bit-identical with and without it
  (no unit exists yet), proven by `h6_audit_proof.py`.

## 6. Disclosures
- The panel lines of 2026-10-09 · 10-10 · 10-13 · 10-14 stay as written (append-only): drawn from the 2026-10-08 pool (1–4 entries stale). No unit
  existed on those days.
- The entries already written `sampled` (2026-09-30 · 10-01 · 10-03 · 10-09 → 10-14) cannot be recovered in full; F1 acts from the next daily run.
- **F1 counts as working only when the pool moves:** the first panel after the first daily screener run that follows the merge must show a
  `pool_date` after 2026-10-08 and the anchor wall stored in full (not `sampled`). Until then it is shipped, not proven. The result is recorded
  in `H6_COLLECTION_AUDIT.md` §⑧.
- Size: `reject_log.json` keeps 20 entries (`REJECT_LOG_DAYS`), 178,152 bytes on 2026-10-14; ≈ 7.84 bytes per stored symbol ⟵ at 432 symbols
  +251 bytes per entry, ≈ +5 KB on the file; it does not grow month on month (rolling window). Bound: the wall cannot exceed the identity-eligible
  universe (≈ 3,400 symbols ⟵ +23.5 KB per entry, +470 KB on the file at worst). No separate ceiling is proposed.

## 7. Locks (`test_bot.py`, before `LEAK0`) — each fails on the previous code (main `813da7e`) and passes on the fix
- `H6S1` (F2): Saturday, Sunday and a holiday are not sessions · `add_sessions(2026-10-09, 5) = 2026-10-16` · E5 for ANPA (T = 2026-10-14)
  ends 2026-10-21 · `sessions_between(2026-10-09, 2027-04-09) = 124`.
- `H6A1` (status): the pool date is printed even when fresh · ⚠️ and a warning when the pool lags or photos stop for 5 sessions · `status`
  prints the line and the warnings · the workflow runs it after the ledger check and before the commit, `continue-on-error`, commits
  `H6_STATUS.json`, and references no Telegram secret.
- `H6P1` (F1): 300 synthetic days — the control wall in full, the other walls equal to an independent oracle of the 400-cap sample ·
  `control_pool` picks the day's entry · `full_walls=()` equals the oracle without the exemption · `record_rejected_symbols` writes the wall
  in full (temporary file).
- Mutations: 12 of 12 fell, each on its own lock; the pre-fix code fails all three.
