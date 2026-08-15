# Plan 023: Characterization tests for untested owner-facing runner functions

> **Executor instructions**: Follow this plan step by step. This plan adds **tests only**
> — do not change any runner logic. If a test you write fails against current behavior,
> that is either a real bug (STOP and report it) or your fixture is wrong (fix the
> fixture). Run `python3 test_bot.py` after each block. When done, update this plan's
> status row in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4e9b143..HEAD -- hunter_ledger.py hunter_outcomes.py e2_recover.py press_radar.py`
> If any changed, re-read the target functions before writing tests; on a mismatch, STOP.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW (tests only)
- **Depends on**: none
- **Category**: tests
- **Planned at**: commit `4e9b143`, 2026-08-15

## Why this matters

This repo's core discipline is **"locks that can fall, proven by mutation"** — a function
is only trusted if deliberately breaking it makes a test fail. Several **owner-facing**
runner functions are covered only *transitively* (through a `.run()` entry point), so a
logic change inside them can ship without any lock falling. The highest-blast-radius gaps:

- `hunter_ledger.apply_outcomes` / `pending` — the read-modify-writeback into the 258 KB
  outcome ledger, including a silent `MAX_ROWS` trim. `except: return 0` means a total
  failure looks like "nothing to resolve".
- `hunter_outcomes.resolve` / `report` — builds the "حافّة مُعلَنة" vs "لا حكم" verdict the
  owner reads (a sign/boundary bug mislabels a hunter's edge).
- `e2_recover.rebuild_fire_log` — rewrites the owner's fire log with a `(symbol, date)`
  dedup; a dedup-key bug drops/duplicates real fires in the false-alarm metric.
- `press_radar.prev_qualified` / `runup_pct` — produce owner-facing alert badges over a
  `step=5` sampled lookback (the session-edge boundary where a bug fires/suppresses the
  "qualified" badge). (Note: plan 015 adds the coverage-floor test for `press_radar.run`;
  this plan tests the *pure* lookback helpers.)

Adding direct, mutation-proven tests turns these into real locks.

## Current state

The test harness (so you match it exactly):
- `test_bot.py:99` — `def check(name, cond, extra=""): (PASS if cond else FAIL).append(name); print(...)`.
- Modules are imported under aliases: `hunter_ledger as _LG` (`test_bot.py:16299`),
  `hunter_outcomes as _HO` (`:16300`), `e2_recover as _RC` (`:3314`), `press_radar as _PRD`
  (`:17296`).
- **Existing pattern to copy** — direct `_LG` tests at `test_bot.py:16307-16328`:
  ```python
  _lg_n1 = _LG.record("split", "2026-08-05", _lg_rows, path=_lg_tmp, ...)
  check("ledger dedup 2 keys",
        len({r["key"] for r in _LG.load(_lg_tmp)}) == 2)
  check("ledger score resolved",
        _LG.score(2.0, [3.0]*39)["resolved"] is False
        and _LG.score(2.0, [2.1]*40)["resolved"] is True)
  ```
  This shows: temp file paths (`_lg_tmp`), injected `path=`, and `check(name, cond)` usage.

The target functions (read them in full before testing):
- `hunter_ledger.py:160` `pending(rows, resolved_keys=None)`; `:168` `apply_outcomes(rows,
  outcomes, path=None, log=None)` — trims `cut = max(0, len(rows) - MAX_ROWS)`; `keep =
  rows[cut:]`; writes tmp + `os.replace` (`:181-189`). `MAX_ROWS = 20000` (`:31`).
- `hunter_outcomes.py:60` `resolve(rows, fetch_hist, log=None)` (injectable `fetch_hist`);
  `:91` `report(rows, log)` (verdict branching uses `wilson()` at `:30`); `:41`
  `after_session(df, session)`.
- `e2_recover.py:131` `rebuild_fire_log(best, repo_root=".", log_name=FIRE_LOG)` — dedup
  `seen = {(r.get("symbol"), r.get("date")) ...}`, only `alert_emitted` rows, marks
  `source="e2_reconstructed"`, writes to `os.path.join(repo_root, log_name)`.
- `press_radar.py:223` `runup_pct(hi, lo, j_star, w=W)` (pure, returns pct or 0.0);
  `:240` `prev_qualified(sym, bars, anchor_iso, max_back=120, step=5)` (imports `Super_stock`,
  calls `analyze_ticker` — inject/monkeypatch to avoid real analysis).

**Conventions**: all tests run offline — every fetcher/analyzer must be injected or
monkeypatched. Ledger/log tests write to a **temp path** (never the real
`hunter_ledger.jsonl`/`ignition_log.json`). The suite is one process — restore any
monkeypatched module attribute at the end of your block.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests | `python3 test_bot.py` | exit 0 |
| Read a target | `sed -n '160,195p' hunter_ledger.py` etc. | the function body |
| Find temp-file helper | `grep -n "tempfile\|_lg_tmp\|mkstemp\|NamedTemporary" test_bot.py \| head` | the temp-path idiom the suite uses |

## Scope

**In scope**:
- `test_bot.py` — new characterization tests only.

**Out of scope** (do NOT modify):
- `hunter_ledger.py`, `hunter_outcomes.py`, `e2_recover.py`, `press_radar.py` — this plan
  does not change runner logic. If a test reveals a bug, STOP and report it (a separate
  plan fixes it). The exception: if a target function is genuinely un-unit-testable without
  a tiny pure-extraction, STOP and report rather than refactoring it here.

## Git workflow

- Branch: `advisor/023-runner-characterization-tests`
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: `hunter_ledger.apply_outcomes` / `pending`

Using a temp path (copy the `_lg_tmp` idiom near `test_bot.py:16307`):
- Build known rows via `_LG.build_rows(...)`, write them, then call `_LG.apply_outcomes(rows,
  outcomes, path=tmp)` with an `outcomes` dict keyed by `row["key"]`; assert the written
  JSONL reflects the applied outcomes and the returned count matches.
- **MAX_ROWS boundary**: construct `len(rows) == MAX_ROWS + 1`, call `apply_outcomes`, assert
  exactly 1 oldest row was dropped (`keep = rows[cut:]`). (You can temporarily shrink the
  effective boundary by testing the arithmetic on a small list if constructing 20001 rows is
  impractical — but prefer a real boundary test; if you must, test `rows[cut:]` semantics on
  a helper-sized input and note it.)
- `pending`: assert it returns only rows with no `outcome` and whose key isn't in
  `resolved_keys`.

**Verify**: `python3 test_bot.py` → exit 0; new `✅` lines print. Mutation: change
`rows[cut:]` to `rows[:cut]` (or `cut+1`), confirm the boundary test fails; revert.

### Step 2: `hunter_outcomes.resolve` / `report`

- `resolve`: inject a fake `fetch_hist(syms)` returning a dict of small DataFrames with a
  known post-session high; assert `resolve` returns the expected `{key: outcome}` and that a
  fetch that **raises** yields `{}` (fail-safe) — not a crash.
- `report`: feed rows whose summary makes the verdict cross the threshold both ways;
  capture the `log` output (pass a list-appending `log`) and assert the "حافّة مُعلَنة"
  branch fires **only** when the sample gate + Wilson separation both hold, and "لا حكم"
  otherwise. Mutate one input (shrink the sample / flip the separation) and watch the
  verdict flip — this is the mutation proof the repo demands.

**Verify**: `python3 test_bot.py` → exit 0; mutation flips the verdict as expected.

### Step 3: `e2_recover.rebuild_fire_log`

Build a temp session dir with a `candidates.jsonl` containing a mix of `alert_emitted`
true/false rows and one duplicate of an existing log row; call `_RC.rebuild_fire_log(best,
repo_root=tmp)` and assert: only the new **emitted, non-duplicate** row is appended, it
carries `source="e2_reconstructed"`, and existing rows are untouched.

**Verify**: `python3 test_bot.py` → exit 0. Mutation: remove the `if key in seen` dedup
guard and confirm the duplicate now gets appended (test fails); revert.

### Step 4: `press_radar.runup_pct` / `prev_qualified`

- `runup_pct` (pure): feed known `hi`/`lo` arrays and `j_star`; assert the returned pct
  equals the hand-computed value at a window edge, and that a zero/negative base returns 0.0.
- `prev_qualified`: monkeypatch `Super_stock.analyze_ticker` to return truthy on a specific
  sampled offset and falsy elsewhere; assert `prev_qualified` returns the **sampled** date
  (floor semantics — a qualifying day that falls *between* samples is not returned). Restore
  `analyze_ticker` after. (This documents the `step=5` sampling boundary the finding flags.)

**Verify**: `python3 test_bot.py` → exit 0. Mutation: change `step` handling / the `< anchor_iso`
filter and confirm the boundary test fails; revert.

## Test plan

- Four new `check(...)` blocks (Steps 1-4), each with an explicit mutation round proving the
  lock falls. All fetching/analysis injected or monkeypatched — no network, no real state
  files. Model every block on the existing `_LG` tests at `test_bot.py:16307`.

## Done criteria

- [ ] `python3 test_bot.py` exits 0; new tests for all four target areas present and passing
- [ ] Each new test has a documented mutation round (the lock falls when the code is broken)
- [ ] No runner `.py` file modified (`git status` shows only `test_bot.py`)
- [ ] All tests use temp paths / injected fetchers — no real ledger/log written, no network
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report if:
- A characterization test reveals current behavior is **wrong** (e.g. `apply_outcomes`
  drops the wrong end, or the verdict branch is inverted) — capture it as a finding; a
  separate plan fixes the logic. Do not "fix" the runner here.
- A target function cannot be unit-tested without extracting a pure helper — report it
  (extraction is a separate, logic-touching change needing its own plan).
- The MAX_ROWS boundary is impractical to test at 20001 rows and the arithmetic can't be
  isolated — report the compromise you made.

## Maintenance notes

- These are characterization tests: they pin **current** behavior. If the owner later
  changes a verdict threshold or the trim size on purpose, the test updates alongside it.
- Reviewer should scrutinize the mutation rounds — a characterization test with no mutation
  proof is exactly the "lock that never falls" the repo warns against.
- This plan pairs naturally with plan 027 (hunter_ledger concurrency/perf): those tests
  give the safety net for that refactor.
