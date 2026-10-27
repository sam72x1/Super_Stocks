# H6 — AMENDMENT 2 (2026-10-27) · one instrument-defect fix in the mention registry (precision tag only)

> The contract `H6_PREREG.md` is **unchanged** (SHA-256 `a6f68f745cba189223b1f8258e733dc5e1e538382dfe6533307092d8e942c7ed`, still pinned in
> `h6_test.py`). §10 allows a tool-defect fix with a bit-identical check; this file records it.

## 1. The defect (proven)
- `faisal_validation/phase_b.py write` stores `faisal_timestamp` as `"YYYY-MM-DD (New-York day)"` when the post shows no timestamp (the decision
  day is inferred; `phase_b.py` line `"faisal_timestamp": prec or (day and f"{day} (New-York day)")`).
- `fm_forensics/phase6/collector.py` `build_mentions` copied any non-empty `faisal_timestamp` into `post_timestamp` with `post_tz="UTC"` and
  `ts_precision="TIMESTAMP"`.
- The first batch that produced such rows (`B36_20261027`, sealed 2026-10-27) gave **14 mentions** tagged TIMESTAMP whose value `parse_ts`
  cannot read; the suite lock `P6C2` («a mention's timestamp is UNKNOWN or tz-aware») failed on them.

## 2. The fix
| Input `faisal_timestamp` | `post_date` | `post_timestamp` | `post_tz` | `ts_precision` |
|---|---|---|---|---|
| tz-aware ISO (e.g. `2026-10-14T21:10:00Z`) | its first 10 characters | the value | `UTC` | `TIMESTAMP` — **unchanged** |
| exactly `YYYY-MM-DD (New-York day)` | that day | `UNKNOWN` | `America/New_York` | `DATE` — **was** the raw string · `UTC` · `TIMESTAMP` |
| absent | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` — **unchanged** |
| anything else (naive ISO, free text) | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` | `UNKNOWN` — a naive value is never assumed UTC or New York |

Where: `collector.py` `build_mentions` (the `PROSPECTIVE_LEDGER.jsonl` branch), `NY_DAY_SUFFIX`, `_iso_day`. Lock `P6C14` (behavioural, five rows,
plus the producer string in `phase_b.py`).

## 3. Bit-identical check (on the tree that carries `B36_20261027`, before vs after the fix)
- mentions 402 = 402 · the same `mention_id` set in the same order;
- `mention_tickers` (Faisal only and all) identical — **the collected ticker set does not change**;
- exactly 14 rows differ, and only in `post_timestamp` · `post_tz` · `ts_precision`.

## 4. What does not change
The contract and its pin · H6/H6₀ · features, thresholds, windows, floor, matching, verdict rules · the control panel · `h6_test.py`
(it reads decisions from `PROTOCOL_STATUS.json` and the intake annotations, not from the mention registry) · the append-only ledgers (no row is
rewritten: `PROSPECTIVE_LEDGER.jsonl` keeps its strings; only how the collector reads them changes) · production · V4 · Telegram.

## 5. Switch back
None — reverting restores a proven defect. Its effect on collection is zero by §3.
