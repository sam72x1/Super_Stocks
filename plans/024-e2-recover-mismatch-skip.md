# Plan 024: Make e2_recover skip a wrong-dated summary instead of merging it under the wrong date

> **Executor instructions**: Follow this plan step by step. Run every verification and
> confirm the result before moving on. If a STOP condition occurs, stop and report. When
> done, update this plan's status row in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4e9b143..HEAD -- e2_recover.py`
> If it changed, re-read the loop guard below; on a mismatch, STOP.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (pairs well with plan 023 Step 3 for the test harness)
- **Category**: bug
- **Planned at**: commit `4e9b143`, 2026-08-15

## Why this matters

`e2_recover.py` reconstructs the lost E2 ignition-session index. Its guard is *meant* to
skip both a missing summary and a summary whose `session_date` doesn't match the
directory-derived date ("ملخّص غائب أو لتاريخ آخر ⇒ لا نخمّن" — don't guess). But the inner
branch only `continue`s the **missing** case; a summary that exists with a **mismatched
date** falls through and gets merged under the wrong date. `_summary_of` falls back to the
run-level `ignition_e2_summary.json`, which can belong to a different session than the
specific `session_<date>` dir — exactly the mismatch case — so its counters
(`n_delivered`/`n_emitted`/…) get written under the wrong date, corrupting the recovered
index. The documented "don't guess" contract isn't enforced.

## Current state

`e2_recover.py:60-70` (the buggy guard — mismatch falls through to `loops = ...`):
```python
    before = set(idx)
    best, conflicts, no_summary = {}, [], []
    for sdir, date in sorted(_session_dirs(download_root).items()):
        summ = _summary_of(sdir)
        if not summ or summ.get("session_date") not in (None, date):
            # ملخّص غائب أو لتاريخ آخر ⇒ لا نخمّن
            if not summ:
                no_summary.append((date, sdir))
                continue
        loops = int(summ.get("loops_completed") or 0)   # ← mismatch reaches here
        prev = best.get(date)
```
So: `summ` present AND `session_date not in (None, date)` → outer `if` True, inner
`if not summ` False → **no `continue`** → the mismatched summary is processed.

**Convention**: the module tracks skipped/rejected cases in named lists (`no_summary`,
`conflicts`) rather than silently dropping — mirror that (add a `skipped_mismatch` list) so
the skip is *observable* in the run output, matching the repo's "no silent miss" doctrine.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests | `python3 test_bot.py` | exit 0 |
| Read the loop + how lists are reported | `sed -n '55,110p' e2_recover.py` | the full loop + the summary print |

## Scope

**In scope**:
- `e2_recover.py` — the guard at 64-68 and the reporting of the new skipped list.
- `test_bot.py` — a test proving the mismatch is skipped (use the `_RC` alias, `test_bot.py:3314`).

**Out of scope**:
- `_summary_of`, `_session_dirs`, the merge/index-write logic — only the guard changes.
- Any screening/root logic. No `LOGIC_VERSION` (recovery tooling).

## Git workflow

- Branch: `advisor/024-e2-recover-mismatch-skip`
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Restructure the guard to `continue` on a date mismatch

Replace the guard with an explicit two-case skip:
```python
    best, conflicts, no_summary, skipped_mismatch = {}, [], [], []
    for sdir, date in sorted(_session_dirs(download_root).items()):
        summ = _summary_of(sdir)
        if not summ:
            no_summary.append((date, sdir))
            continue
        if summ.get("session_date") not in (None, date):
            # ملخّصٌ لتاريخٍ مختلفٍ عن مجلّده ⇒ لا نُخمّن، نتخطّى (يُعلَن لا يُصمَت)
            skipped_mismatch.append((date, sdir, summ.get("session_date")))
            continue
        loops = int(summ.get("loops_completed") or 0)
        prev = best.get(date)
        ...
```
Now a `None` session_date (allowed) still passes; only a *divergent* date is skipped.

### Step 2: Surface the skipped list in the run output

Wherever the loop reports `no_summary`/`conflicts` (read `sed -n '95,110p' e2_recover.py`),
add a line for `skipped_mismatch` so a skipped session is visible (count + the dates), not
silent.

**Verify**: `python3 test_bot.py` → exit 0. Read the loop — a mismatched summary now hits
`continue` before `loops = ...`.

### Step 3: Add a test

Using `_RC` (`test_bot.py:3314`), build (temp dirs) two session dirs: one whose summary
`session_date` matches its dir date, and one whose summary `session_date` differs. Call the
loop entry (or the smallest function exercising the guard — likely `recover(...)` with a temp
`download_root`), and assert: the matched session is indexed under its date, and the
mismatched one is **not** written into the index (it appears in `skipped_mismatch`).

**Verify**: `python3 test_bot.py` → exit 0; new `✅` prints.

### Step 4: Mutation check

Temporarily revert to the old guard (remove the mismatch `continue`); confirm the test
**fails** (the mismatched summary gets indexed under the wrong date). Revert.

**Verify**: with the mutation, exit 1; after revert, exit 0.

## Test plan

- One new `check(...)` block: matched-indexed + mismatched-skipped, plus a mutation round.
  Temp dirs only — never touch the real E2 index. Reuse any e2_recover test setup already in
  `test_bot.py` (grep `_RC.`).

## Done criteria

- [ ] `python3 test_bot.py` exits 0; new mismatch-skip test present and passing
- [ ] A summary whose `session_date` ≠ dir date is skipped (added to `skipped_mismatch`, not indexed)
- [ ] A `None` session_date still passes (allowed case preserved)
- [ ] The skipped count is reported in the run output (not silent)
- [ ] Mutation check passed
- [ ] `git status` shows only `e2_recover.py`, `test_bot.py`
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report if:
- The loop structure differs from the excerpt (drift) — re-read and adapt, or STOP if the
  guard semantics changed.
- `recover()` can't be driven with a temp `download_root` without extensive scaffolding —
  report and test the smallest reachable unit instead.

## Maintenance notes

- This enforces the module's own "لا نُخمّن" contract. If `_summary_of`'s fallback to the
  run-level summary is ever removed, this guard becomes belt-and-suspenders but stays correct.
- Reviewer should confirm the `None` session_date case still passes (it's an intentional
  "unknown but same session" allowance).
