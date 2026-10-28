# H6 — AMENDMENT 3 (2026-10-28) · one tool-defect fix: E5 is not judged before its window closes

> The contract `H6_PREREG.md` is **unchanged** (SHA-256 `a6f68f745cba189223b1f8258e733dc5e1e538382dfe6533307092d8e942c7ed`, still pinned in
> `h6_test.py`). §10 allows a tool-defect fix with a bit-identical check; this file records it. Owner's order 2026-10-28 «إصلاح h6_test.py».

## 1. The defect (proven)
- Contract §3 E5: «A unit whose first collection is later than T + 5 sessions is `NOT_COVERED`». Before T + 5 sessions have passed, no
  collection can yet be «later than T + 5 sessions».
- `h6_test.py` `eligibility` returned `NOT_COVERED` (`E5:no_collection_within_5_sessions`) whenever the Phase 6 ledger had no row in
  [T, T + 5 sessions] **as of the run day**, without asking whether that window had already closed.
- Seen live on 2026-10-28 (`status` on main `dffe13934`): BKYI (T 2026-10-22), CYCU (10-23), ICMB (10-24) were reported `NOT_COVERED` and
  counted as coverage failures (4 of 4 with ANPA) while their windows were open until 10-29 / 10-30 / 10-30. The batch was sealed
  2026-10-27 21:50 UTC, after the collector's last run (10-27 08:22 UTC), so the collector had not yet seen them.
- Effect if left: interim status overstates coverage failures; at `analyze` a unit whose window is still open would be counted as a coverage
  failure instead of nothing (the §7 «more than 20% NOT_COVERED ⇒ NOT TESTABLE (coverage)» rule would read it).

## 2. The fix
| E5 situation on run day `today` | Before | After |
|---|---|---|
| a ledger day in [T, T + 5 sessions] | `ELIGIBLE` path (C = first such day) | **unchanged** |
| no such day and `today` ≤ T + 5 sessions (window still open; the last day is included) | `NOT_COVERED` | `PENDING_COLLECTION` (`E5:window_open_until_<T+5>`) — counts toward nothing, like `PENDING_REVEAL` (E2) |
| no such day and `today` > T + 5 sessions | `NOT_COVERED` | **unchanged** |
| `eligibility(...)` called without `today` | `NOT_COVERED` | **unchanged** (bit-identical default) |

Where: `h6_test.py` `eligibility(..., today=None)` and `build_status` passing its `today`. `PENDING_COLLECTION` is not in the coverage-failure
set, so it is neither a unit nor a failure. Lock `H6W1` (behavioural: direct calls at 10-28 / 10-29 / 10-30 and without `today`, plus
`build_status` on a synthetic world at 11-01 and 11-05). Mutations: 5 of 6 caught; the sixth (dropping `today is not None`) is equivalent —
`str(None)` sorts after every ISO date, so no output changes.

## 3. Bit-identical check (main `dffe13934` data, old tool vs new tool, `today` = 10-28 · 10-29 · 10-30 · 10-31 · now)
- Every field of the status other than `items` / `by_status` / `coverage_failures` / `coverage_failure_share` is identical on all five days.
- 10-28 and 10-29: exactly three cases change — CASE_0004 CYCU and CASE_0005 ICMB ⟶ `PENDING_COLLECTION` (until 10-30), CASE_0006 BKYI ⟶
  `PENDING_COLLECTION` (until 10-29); coverage failures 4 ⟶ 1 (ANPA, window closed 10-21).
- 10-30: CYCU and ICMB pending, BKYI back to `NOT_COVERED` if still uncollected; 10-31: identical to the old tool (4 failures).
- Eligible units 0 on every day, before and after.
- **Live, after the owner-ordered manual collector run** (`40652395902`, 2026-10-28 07:47–07:55 UTC, after the 10-28 screener wrote a full
  anchor wall): BKYI, CYCU and ICMB were collected on 10-28 inside their windows ⟶ **eligible 3/15** (lag 4 · 3 · 3 sessions; four controls
  each from the 10-28 panel, pool 2026-10-28) — the same with the old and the new tool, because the windows were still open when
  collection arrived. ANPA stays `NOT_COVERED` (window closed 10-21); NCT stays `REPEAT`.

## 4. What does not change
The contract and its pin · H6/H6₀ · features, thresholds, windows, the floor, the matching rule, the verdict rules · the control panel and the
collector · the append-only ledgers · E1–E4, E6, E7 · production · V4 · Telegram.

## 5. Switch back
None — reverting restores a proven defect. Its effect after every window closes is zero by §3.
