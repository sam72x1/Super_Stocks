# Plan 028: Add an optional section filter to `test_bot.py` (keep the single exit-0 gate; make iteration cheaper)

> **Executor instructions**: Follow this plan step by step. The single `python3 test_bot.py`
> gate (exit 0 = all pass) MUST remain the default behavior — the filter is opt-in only. If
> a STOP condition occurs, stop and report. When done, update this plan's status row in
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4e9b143..HEAD -- test_bot.py` (large file;
> confirm the `check()` helper and the tail runner still match the excerpts).

## Status

- **Priority**: P3
- **Effort**: M (mechanical but spread across a 21k-line file; low structural risk if the
  filter wraps `check`, not the sections)
- **Risk**: MED — a careless change to `check()`/the runner could drop assertions from the gate.
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `4e9b143`, 2026-08-15

## Why this matters

`test_bot.py` is a single 1.5 MB / ~21k-line file executed top-to-bottom by `python3
test_bot.py`, with a hand-rolled `PASS`/`FAIL` tally and `raise SystemExit(1)` at the end
(`test_bot.py:21414-21422`). There is no discovery, no `-k` filter, no way to run a subset:
every change to one runner's locks forces the full multi-thousand-assert run. That is the
dominant iteration cost for a contributor/executor touching one subsystem. This plan adds an
**opt-in** section filter (via env var) that runs only matching `check()` calls, while the
default no-arg invocation stays exactly the single exit-0 gate the repo relies on. It does
**not** restructure the file or the gate discipline — it only makes authoring faster.

## Current state

`test_bot.py:99-101` (the tally helper — the natural filter point):
```python
def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(("✅" if cond else "❌") + f" {name}" + (f"  [{extra}]" if extra else ""))
```
`test_bot.py:21416-21422` (the runner tail — the gate):
```python
print(f"النتيجة: {len(PASS)} نجح · {len(FAIL)} فشل")
if FAIL:
    print("الفاشل: " + " | ".join(FAIL))
    raise SystemExit(1)
print("✅✅ كل الاختبارات نجحت — الضمان الذهبي")
```
There is no `argparse`/`sys.argv`/pytest usage in the file.

**Constraint**: the offline suite is the official gate; `tests.yml` runs `python3 test_bot.py`
with no args. The filter must be a **no-op** when its env var is unset, so CI behavior is
byte-identical. **However**, a naive `check`-level filter has a hazard: many `check(name,
cond, ...)` calls do real work in their `cond` expression, and code *between* checks builds
shared state. Filtering must not skip state-building code that later (unfiltered) checks
depend on — so the filter can only safely **suppress the tally/print** for non-matching
checks, not skip execution. That still speeds *reading* (only relevant ✅/❌ print) but not
execution. A true execution subset would require sectioning, which is out of scope (too
risky on this file). Set expectations accordingly: this plan delivers **output filtering +
a fast "did my section pass" signal**, not a full execution subset.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Full gate (must stay default) | `python3 test_bot.py` | exit 0, `✅✅ كل الاختبارات نجحت` |
| Filtered view (new) | `TEST_FILTER=press python3 test_bot.py` | prints only matching checks + a filtered tally |
| Confirm no argparse today | `grep -n "sys.argv\|argparse" test_bot.py` | no output |

## Scope

**In scope**:
- `test_bot.py` — the `check()` helper and the tail tally only.

**Out of scope**:
- Splitting the file into modules (too risky; a separate, larger effort).
- Changing any assertion or the default exit-0 gate.
- CI (`tests.yml` stays `python3 test_bot.py` with no args).

## Git workflow

- Branch: `advisor/028-test-suite-selective-run`
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Add an opt-in name filter to `check()`

Read the `TEST_FILTER` env var once near the top (after imports). In `check()`, when
`TEST_FILTER` is set and `TEST_FILTER not in name`, still **evaluate `cond`** (to preserve
side effects/state) but suppress the print and the tally append — and record whether it
would have passed only for the filtered summary. When `TEST_FILTER` is unset, behavior is
**identical to today** (append to PASS/FAIL, print).

Concretely:
```python
_TEST_FILTER = os.environ.get("TEST_FILTER") or ""

def check(name, cond, extra=""):
    ok = bool(cond)                      # always evaluate — preserves shared state
    if _TEST_FILTER and _TEST_FILTER not in name:
        return                            # non-matching: no print, no tally (filtered view only)
    (PASS if ok else FAIL).append(name)
    print(("✅" if ok else "❌") + f" {name}" + (f"  [{extra}]" if extra else ""))
```
Note the subtle but important change: `cond` is evaluated into `ok` **before** the filter
check, so state built inside a `cond` expression still runs. Confirm no `check()` call
relies on `cond` being lazily unevaluated (it can't — Python evaluates args before the call).

### Step 2: Make the tail honest under a filter

When `TEST_FILTER` is set, the tally reflects only matching checks; the `SystemExit(1)` on
any filtered FAIL still fires (so a filtered run is still a real signal for that section). Add
a one-line note in the printed summary when a filter is active, e.g.
`f"(مُرشَّح بـ TEST_FILTER={_TEST_FILTER})"`. The **unfiltered** default path is unchanged.

**Verify**:
- `python3 test_bot.py` → exit 0, `✅✅ كل الاختبارات نجحت` (byte-identical default).
- `TEST_FILTER=zzz_nomatch python3 test_bot.py` → prints 0 checks, exits 0 (nothing matched,
  nothing failed).
- `TEST_FILTER=<a substring of a real check name> python3 test_bot.py` → prints only those
  checks.

### Step 3: Confirm CI parity

The default (no env var) path must be identical. Diff the printed output of `python3
test_bot.py` before and after your change — it should be the same lines (same order, same
tally).

**Verify**: `python3 test_bot.py > /tmp/after.txt; git stash; python3 test_bot.py >
/tmp/before.txt; git stash pop; diff /tmp/before.txt /tmp/after.txt` → no diff.

## Test plan

- The verification commands above are the test (this is test-infra). Optionally add a
  self-check `check("filter noop when unset", ...)` guarded so it doesn't recurse.

## Done criteria

- [ ] `python3 test_bot.py` (no args) is byte-identical in output and still exits 0
- [ ] `TEST_FILTER=<name-substring>` prints only matching checks and a filtered tally
- [ ] `cond` is always evaluated (shared state preserved) — no assertion silently skipped from execution
- [ ] `tests.yml` unchanged (still `python3 test_bot.py`)
- [ ] `git status` shows only `test_bot.py`
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report if:
- Any `check()` call passes a `cond` whose evaluation you must *avoid* under a filter (there
  shouldn't be — Python evaluates args eagerly — but if the codebase wraps `cond` in a lambda
  anywhere, the semantics differ) — report it.
- The default-path output diff (Step 3) is non-empty — your change altered the gate; revert.

## Maintenance notes

- This is deliberately the *minimal* ergonomics win — output filtering, not a true execution
  subset. A real subset needs sectioning the file, which is a much larger, riskier effort
  (the low-leverage reason it's P3). Revisit only if iteration cost becomes acute.
- Reviewer must confirm the unfiltered gate is byte-identical — that's the only thing that
  can go wrong here.
