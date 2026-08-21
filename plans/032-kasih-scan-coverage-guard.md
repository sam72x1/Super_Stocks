# Plan 032: kasih_scan / kasih2_scan must exit non-zero on missing S3 coverage (no green-zero)

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving on. If any STOP condition
> occurs, stop and report — do not improvise. When done, update this plan's status
> row in `plans/README.md` (unless a reviewer told you they maintain the index).
>
> **Drift check (run first)**: `git diff --stat 52ffe4f..HEAD -- kasih_scan.py kasih2_scan.py exit_stop_arms.py`
> If any changed, compare the "Current state" excerpts below against the live code before
> proceeding; on a mismatch, STOP.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug / tests
- **Planned at**: commit `52ffe4f` (origin/main), 2026-08-21

## Why this matters

`kasih_scan.py` and `kasih2_scan.py` are dispatch-only research tools that measure the T-KASIH /
T-KASIH-2 bucket tables over three years of Polygon flat files (S3). Their published Wilson tables
(`kasih_result.md` / `kasih2_result.md`) and the JSONL they emit are what the owner reads to make
decisions, and what `kasih2_red_stats.py` / `exit_stop_arms.py` consume downstream.

Both `main()` functions return `0` (green) regardless of how many days actually downloaded. On an
S3 throttle — the documented failure mode — a run can compute its bucket tables on a biased subset
(or on **zero** rows) and the workflow still reads exit-0 as success. This is precisely the
"green zero mis-read as a real result" the repo forbids, and it's the same class the sibling tool
`exit_stop_arms.py` was hardened against **after a measured incident**: a 2024 run silently lost 68
of 194 days and "printed the coverage and moved on," producing numbers on a subset ~30% smaller and
time-biased (the loss was in the tail of the year). `exit_stop_arms.py` added `coverage_bad()` (its
`V4` gate) for exactly this; `kasih_scan`/`kasih2_scan` predate that lesson and carry no equivalent.

The fix: add the same coverage guard so a throttled/empty **year-mode** session exits non-zero with
a named reason instead of green. The single-day display mode (`KASIH_DAY`) can stay lenient (one day
is the whole intended sample there).

## Current state

- `kasih_scan.py` — year/day backtest of T-KASIH. Counters `n_files`, `n_missing`, `n_anchored`,
  `v2_anchors` are maintained in `main()` (`kasih_scan.py:312-314`); `one_day = os.environ["KASIH_DAY"]`
  distinguishes single-day mode (`:291`).
- `kasih2_scan.py` — same shape for T-KASIH-2 (counters at `kasih2_scan.py:262-263`, `one_day` at `:240`).
- `exit_stop_arms.py` — the sibling that already has the guard.

`kasih_scan.py:439-443` (current exit — no coverage/empty check):
```python
    print("\n⚠️ حدودُ الصدق (§⑧): لمسٌ لا تنفيذ · يومٌ واحد · مِرساةٌ/رمز/يوم ·"
          " إغلاقُ الأمس من الشموع · الحكمُ عبر السنوات الثلاث لا سنةً واحدة.")
    if v2_anchors:
        return 3
    return 0
```

`kasih2_scan.py:421-423` (current exit — unconditional `return 0`):
```python
    print("\n⚠️ حدودُ الصدق (العقد §⑦): لمسٌ لا تنفيذ · يومُ المِرساة وحده · ...")
    return 0
```

The pattern to mirror — `exit_stop_arms.py:45-64` (the guard) and `:426-433` (its use):
```python
MAX_MISSING_DAYS = 3

def coverage_bad(n_files: int, n_missing: int) -> bool:
    # ... عدّادٌ مطلق: أكثرُ من MAX_MISSING_DAYS يومَ تداولٍ مفقودٍ ⇒ لا حكم ·
    #     وصفرُ أيامٍ ⇒ لا حكم (لا تُقرأ «تغطيةٌ تامّة»).
    if int(n_files or 0) + int(n_missing or 0) <= 0:
        return True
    return int(n_missing or 0) > MAX_MISSING_DAYS
```
```python
    cov_bad = coverage_bad(n_files, n_missing)
    print(f"   V4  أيامُ تداولٍ مفقودة: {n_missing} من {len(days)} ... "
          + ("✅" if not cov_bad else f"⛔ (الحدّ {MAX_MISSING_DAYS} يومًا)"))
    if v0_bad or ... or cov_bad:
        print("\n⛔ بوّابةُ صلاحيةٍ ساقطة ⇒ **عطبُ أداةٍ لا نتيجة** — لا حكم.")
        return 3
```

**Repo conventions**: Arabic log lines; a distinct non-zero exit (`3`) signals "tool defect / no
verdict" (the repo's "عطبُ أداةٍ لا نتيجة" convention); guards are named (`V4`). The single-day path
must stay green so the owner's interactive `KASIH_DAY` runs still work.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests   | `python3 test_bot.py` | exit 0 |
| Read the sibling guard | `grep -n "coverage_bad\|MAX_MISSING_DAYS" exit_stop_arms.py` | the pattern |
| Confirm counters | `grep -n "n_files\|n_missing\|one_day" kasih_scan.py kasih2_scan.py` | counter sites |
| Scope check | `git status --porcelain` | only `kasih_scan.py`, `kasih2_scan.py`, `test_bot.py` |

(Offline suite. Use `python3.11` if `python3` is 3.9.)

## Scope

**In scope**:
- `kasih_scan.py` and `kasih2_scan.py`: add a coverage guard in **year mode only** before the
  final `return`.
- `test_bot.py` (add tests for the guard predicate).

**Out of scope** (do NOT touch):
- `exit_stop_arms.py` (already has the guard — reuse its logic, don't edit it).
- The bucket-table math, `resolve`, `f2_usd5`, any threshold, or the single-day (`KASIH_DAY`)
  display path. These are research tools outside production — **no `LOGIC_VERSION`**, no screening root.
- The `if v2_anchors: return 3` path in `kasih_scan` (leave it; add the coverage check as an
  additional gate, not a replacement).

## Git workflow

- Branch: `advisor/032-kasih-coverage-guard`
- Commit trailer (exactly): `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Add a coverage guard to `kasih_scan.py` (year mode)

Add a `coverage_bad`-style check (reuse the exact predicate: zero days ⇒ bad; `n_missing >
MAX_MISSING_DAYS` ⇒ bad). You may either import `exit_stop_arms.coverage_bad` (a lazy `import
exit_stop_arms` inside `main`, matching the repo's lazy-import style) **or** define a small local
`MAX_MISSING_DAYS`/predicate — prefer importing to keep a single source of truth. Just before the
final return, when **not** `one_day`, print a named `V4`-style coverage line and, if coverage is bad
(or `n_anchored == 0`), print the "عطبُ أداةٍ لا نتيجة" line and `return 3`. Keep the existing
`if v2_anchors: return 3` and `return 0` for the covered case.

**Verify**: read the code — year mode with too many missing days (or zero anchors) now returns `3`
and prints a named reason; `one_day` mode is unchanged.

### Step 2: Add the same guard to `kasih2_scan.py`

Same change before its `return 0`, using the same predicate and its `n_files`/`n_missing`/`n_anchored`
counters, guarded by `not one_day`.

**Verify**: read the code — symmetric to Step 1.

### Step 3: Run the suite

**Verify**: `python3 test_bot.py` → exit 0.

### Step 4: Add tests

Using `check(...)`, test the **predicate** deterministically (no S3 needed):
1. `coverage_bad(0, 0)` is `True` (zero days ⇒ no verdict).
2. `coverage_bad(n_files=190, n_missing=68)` is `True` (the measured incident's shape).
3. `coverage_bad(n_files=250, n_missing=3)` is `False` (a clean run passes).
If you imported `exit_stop_arms.coverage_bad`, assert on it directly; if you added a local predicate,
assert on that. Additionally add a lightweight assertion that both `kasih_scan.main` and
`kasih2_scan.main` reference the guard (a source/AST assertion that the year-mode return path is gated
by the coverage predicate) — enough to catch a future removal.

**Verify**: `python3 test_bot.py` → exit 0; new `✅` lines print.

### Step 5: Mutation check

Temporarily flip the guard's comparison (`>` → `<`, or make it always-`False`), run
`python3 test_bot.py`, and confirm a coverage test **fails**. Restore. (This mirrors the exact
mutation `exit_stop_arms` documents surviving a structural-only lock — so make sure your lock reads
the predicate's **behavior**, not just its presence.)

**Verify**: with the mutation, exit 1; after restore, exit 0.

## Test plan

- Three predicate cases + a presence-of-guard assertion for both tools, plus a mutation round. All
  offline (the predicate is pure; no network).

## Done criteria

- [ ] `python3 test_bot.py` exits 0; new tests present and passing
- [ ] Year mode with `n_missing > MAX_MISSING_DAYS` or zero days/anchors returns `3` with a named reason
- [ ] `KASIH_DAY` single-day mode still returns `0` (unchanged)
- [ ] The bucket-table math and all thresholds are byte-identical
- [ ] Mutation check passed
- [ ] `git status --porcelain` shows only `kasih_scan.py`, `kasih2_scan.py`, `test_bot.py`
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report if:
- `n_files`/`n_missing` are not both maintained in a `main()` you can guard (structure changed) —
  report the actual counters.
- `KASIH_DAY` mode shares the same return path as year mode such that guarding year mode would also
  gate single-day runs — report; the single-day path must stay green.
- Importing `exit_stop_arms` from `kasih_scan`/`kasih2_scan` triggers a heavy import chain or a
  circular import — fall back to a local `MAX_MISSING_DAYS`/predicate and note it.

## Maintenance notes

- The doctrine: **a measurement tool that publishes numbers must detect when it measured nothing (or
  a biased subset) and fail loudly**, not print coverage and return green. `press_radar` (plan 015)
  and `exit_stop_arms` (`V4`) are the precedents; this closes the same gap in the kasih tools.
- Reviewer should confirm the threshold matches `exit_stop_arms.MAX_MISSING_DAYS` (single source of
  truth preferred) and that the single-day path is untouched.
