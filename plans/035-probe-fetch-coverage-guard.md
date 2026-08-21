# Plan 035: Session probes must exit non-zero on a throttled/biased fetch (no green-zero on a partial universe)

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving on. If any STOP condition
> occurs, stop and report — do not improvise. When done, update this plan's status
> row in `plans/README.md` (unless a reviewer told you they maintain the index).
>
> **Drift check (run first)**:
> `git diff --stat 5cb88df..HEAD -- gate_probe.py m0_probe.py liq_move_probe.py liq_noise_probe.py cumrise_probe.py alert_filter_check.py kasih2_red_stats.py exit_stop_arms.py`
> This plan was written against `origin/main` (`5cb88df`). These tool files exist
> on `origin/main`, **not** on an older checkout. If `git rev-parse --short HEAD`
> is not `5cb88df` or a descendant, or if `exit_stop_arms.py` does not exist,
> **STOP** — you are on the wrong tree; the operator must update to `origin/main`.
> If any file above changed since `5cb88df`, compare its "Current state" excerpt
> below against the live code before editing; on a mismatch to that file's `main()`
> tail, STOP for that file.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug / tests
- **Planned at**: commit `5cb88df` (origin/main), 2026-08-21

## Why this matters

Six standalone research/probe tools fetch a live universe of ~300+ symbols
(minute or daily bars from Polygon), compute Wilson/median/bucket tables, and
write a markdown result the **owner reads to make live decisions** (e.g. the
2026-08-18 "اطفي M0" call from `m0_result`, the "شغّل c1 / P5" alert-filter calls
from `alert_filter_check`, the `G5` gate call from `gate_result`). Each tool's
`main()` prints how many symbols failed to fetch (`تعذّر {fails}`) but the **only**
coverage gate is `if not data: return 2` (total-zero). If Polygon throttles and
drops, say, 150 of 314 symbols, the tables are computed on the biased survivors
and `main()` falls through to `return 0` — a **green run that signals "real
result."**

This is precisely the measured class the repo already hit and hardened against:
the sibling S3 tool `exit_stop_arms.py` added a `coverage_bad()` guard (its `V4`
gate) **after** a 2024 run silently lost 68 of 194 days and "printed the coverage
and moved on," producing numbers on a subset ~30% smaller and time-biased
(CLAUDE.md, 2026-08-20 exit_stop entry, "🥇 ② حارسُ التغطية V4 منع نشرَ رقمٍ
كاذبٍ ثلاثَ مرّات"). The six session probes predate that lesson and carry no
equivalent guard. `kasih2_red_stats.py` has a related, milder gap: it returns `0`
even when the sample floor isn't met (inconsistent with `exit_stop_arms` returning
a distinguished non-zero code).

The fix: add the same "coverage insufficient ⇒ exit non-zero with a named reason"
guard so a throttled/partial run fails **red** instead of publishing biased
numbers. Because each workflow runs `python <tool>.py` with **no `|| true`**, a
non-zero return surfaces as a red run — the desired outcome.

**Note vs already-planned 032**: plan 032 adds the same class of guard to
`kasih_scan.py` / `kasih2_scan.py` (S3 year-mode, missing **days**). This plan
covers a **different, non-overlapping** set of tools (session probes, missing
**symbols**). Do not edit the 032 tools here.

## Current state

The pattern is identical across the six probes: build `syms` (universe) and
`data` (successfully fetched, a dict); count `fails`; print coverage; gate only on
`if not data`; then `return 0`. Verified sites (locate by text, not line number):

- **`gate_probe.py`** — print at ≈`:330` (`📥 شموعُ اليوم ‏+ إغلاقُ الأمس:
  {len(data)} من {len(syms)} · تعذّر {fails} …`); gate `if not data: return 2`
  ≈`:333`; `return 0` at ≈`:526` (end of `main()`).
- **`m0_probe.py`** — print `📥 شموعُ الدقيقة: {len(data)} من {len(syms)} · تعذّر
  {fails}` ≈`:427`; `if not data: return 2` ≈`:431`; `return 0` at ≈`:714`.
- **`liq_move_probe.py`** — print `📥 شموعٌ مجلوبة: {len(data)} من {len(syms)} ·
  تعذّر {fails}` ≈`:371`; `if not data: return 2` ≈`:373–375`; `return 0` at end.
- **`liq_noise_probe.py`** — print ≈`:366`; `if not data: return 2` ≈`:368–370`;
  `return 0` at end.
- **`cumrise_probe.py`** — print `… تعذّر {fails} (يُعَدّ ولا يُخمَّن) …` ≈`:209`;
  `if not data: return 2` ≈`:210`; `return 0` at end. (This tool already **records**
  `fetch_fails` into its forward ledger row but never gates on it.)
- **`alert_filter_check.py`** — print `… تعذّر {fails} …` ≈`:173`; gate
  `if not rows: return 5` ≈`:174–176` (uses `rows`, not `data`); `return 0` at end.

`kasih2_red_stats.py` (different mechanism — no fetch; reads run-id artifacts):
when the sample floor isn't met it prints "لا حكم — ولا كتم" and then returns
`0` (≈`:196–199`). It should return a distinguished non-zero code instead.

### The in-repo reference to mirror: `exit_stop_arms.py`

```python
def coverage_bad(n_files: int, n_missing: int) -> bool:
    """`V4` — هل التغطيةُ ناقصةٌ بما يُبطل الحكم؟ **نقيّةٌ لتُقفَل سلوكيًّا**
    …"""
    # (percent-missing vs a named floor, holidays excluded from the denominator)
```
and its gate (≈`:426`):
```python
    cov_bad = coverage_bad(n_files, n_missing)
    print(f"   V4  أيامُ تداولٍ مفقودة: {n_missing} من {len(days)} … "
          + ("✅" if not cov_bad else f"⛔ (الحدّ {MAX_MISSING_DAYS} يومًا)"))
    if v0_bad or … or cov_bad:
        print("\n⛔ بوّابةُ صلاحيةٍ ساقطة ⇒ **عطبُ أداةٍ لا نتيجة** — لا حكم.")
        return 3
```
Two sibling tools already do the session-appropriate version and can be cited as
in-repo patterns: `sweep_reclaim_arms.py` (pipe-fail: `lost_pct > PIPE_FAIL_PCT →
3`) and `ceiling_arms.py` (validity gate → 3).

**The session-probe form differs from `exit_stop_arms` in the denominator**: probes
measure a **universe of symbols**, so the floor is on `fails / len(syms)` (fraction
of the universe that failed to fetch), not on missing calendar days. Do not copy
`coverage_bad`'s day math literally — mirror its **shape** (compute a fraction
against a named threshold, print the verdict, return non-zero with a reason).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Test suite (gate) | `python3 test_bot.py; echo "rc=$?"` | `rc=0`, zero failures |
| Byte-compile a tool | `python3 -m py_compile gate_probe.py m0_probe.py liq_move_probe.py liq_noise_probe.py cumrise_probe.py alert_filter_check.py kasih2_red_stats.py` | exit 0, no output |
| Find each `main()` return | `grep -n "return 0\|if not data\|if not rows\|تعذّر {fails}" <tool>.py` | the sites above |

These probes cannot run locally (Polygon/network is blocked in the test env) — you
verify via `py_compile` + the `test_bot.py` lock (see Test plan), **not** by
executing the probe.

## Suggested executor toolkit

- Load **`lock-and-mutate`** before writing the test. The guard's threshold
  comparison must be locked **behaviorally** (a mutation flipping `>` to `<` or
  deleting the guard must fail the test) — the exact class `exit_stop_arms`'s V4
  note records a mutation surviving a structural-only lock.

## Scope

**In scope**:
- `gate_probe.py`, `m0_probe.py`, `liq_move_probe.py`, `liq_noise_probe.py`,
  `cumrise_probe.py`, `alert_filter_check.py` — add the coverage guard in each
  `main()` after the coverage print, before the tables.
- `kasih2_red_stats.py` — return a distinguished non-zero code when the sample
  floor isn't met (instead of `0`).
- `test_bot.py` — add a lock test for a pure helper (see Test plan).

**Out of scope** (do NOT touch):
- `kasih_scan.py` / `kasih2_scan.py` — those are plan 032's domain (same class,
  different tools). Editing them here creates a merge conflict with 032.
- `exit_stop_arms.py`, `sweep_reclaim_arms.py`, `ceiling_arms.py` — they already
  guard correctly; they are references only.
- Any threshold/statistical logic inside the tables, the `*_prereg.md` contracts,
  or `Super_stock.py`. This plan only adds a fail-red gate; it does not change any
  published number's computation.
- The zero-data gate (`if not data: return 2`) — keep it; the new guard is an
  additional, stricter check (partial coverage), returning a **different** code so
  the two failure modes stay distinguishable.

## Git workflow

- Branch: `advisor/035-probe-coverage-guard`.
- Commit message ends with the repo's two trailer lines (copy from recent
  `git log`). Do NOT push or open a PR unless instructed.

## Steps

### Step 1: Add one pure helper (locatable, testable)

To keep the guard consistent and testable without a network, add a single pure
function — either in each probe (identical 3-line body) or, preferred by the
repo's "one source" culture, in one place the probes already import. The probes
import each other and `alert_helpers`/`kasih_scan`; the lowest-coupling home is a
new small module `probe_common.py` exporting:

```python
def coverage_bad(n_fetched: int, n_universe: int, max_miss_frac: float) -> bool:
    """True when too much of the universe failed to fetch to trust the tables.
    Pure so it can be locked behaviorally. n_universe<=0 ⇒ False (the zero-data
    gate handles the empty case)."""
    if n_universe <= 0:
        return False
    return (n_universe - n_fetched) / n_universe > max_miss_frac
```

If a new module is undesirable in the executor's judgment, inline the identical
3-line body in each probe — but then the test (Step 3) must import and exercise it
from at least one probe. **Do not** reuse `exit_stop_arms.coverage_bad` (its
signature is day-based and its import pulls S3 machinery).

Pick a single named threshold constant per tool (or one shared constant), e.g.
`MAX_MISS_FRAC = 0.20` (fail if more than 20% of the universe failed to fetch).
`0.20` is a reasonable default consistent with `exit_stop_arms`'s ~ "low single-
digit %" tolerance being for a *year* of days; a session universe of one day
tolerates a larger fraction of transient per-symbol failures. State the number in
a comment and mark it `engineering` (an operator-chosen threshold, not a Faisal
number) — see the repo's source-ledger convention. If unsure whether `0.20` is
acceptable, use it and note it in your report for the reviewer; do not block.

**Verify**: `python3 -m py_compile probe_common.py` (or the edited probe) → exit 0.

### Step 2: Wire the guard into each `main()`

In each of the six probes, immediately **after** the existing coverage print and
**after** the `if not data:`/`if not rows:` zero-gate, add:

```python
    if coverage_bad(len(data), len(syms), MAX_MISS_FRAC):   # rows/len(rows) for alert_filter_check
        print(f"⛔ تغطيةٌ ناقصة: {fails} من {len(syms)} تعذّرت "
              f"(الحدّ {MAX_MISS_FRAC:.0%}) ⇒ عطبُ أداةٍ لا نتيجة — لا حكم.")
        return 3
```

Use the tool's actual variable names (`data`/`syms`/`fails`, or `rows` for
`alert_filter_check`). Return code **3** to match `exit_stop_arms`/`sweep_reclaim_
arms`/`ceiling_arms` ("عطبُ أداةٍ لا نتيجة") and to stay distinct from the
zero-data `2`. Keep the guard **before** any table computation so no biased number
is printed.

For **`kasih2_red_stats.py`**: at the floor-not-met branch (≈`:196–199`) that
currently prints "لا حكم" and returns `0`, change the return to a distinguished
non-zero code (use `5`, matching `exit_stop_arms`'s "floor-not-met ⇒ 5"
convention) so a floor-not-met run does not read as "checked, no mute."

**Verify**: `grep -n "coverage_bad\|return 3" <each probe>.py` shows the new guard
above the tables; `grep -n "return 5\|return 0" kasih2_red_stats.py` shows the
floor branch now returns 5. `python3 -m py_compile <all edited files>` → exit 0.

### Step 3: (see Test plan) — lock the helper behaviorally

### Step 4: Full suite

**Verify**: `python3 test_bot.py; echo "rc=$?"` → `rc=0`, zero failures.

## Test plan

Add one lock test to `test_bot.py` (model it on an existing probe/helper test —
`grep -n "coverage_bad\|exit_stop_arms\|sweep_reclaim" test_bot.py` for the
pattern, and use the repo's `check(...)` helper).

Assert the **differentiating** behavior of `coverage_bad`:
- `coverage_bad(50, 100, 0.20)` → `True` (50% missing > 20%).
- `coverage_bad(85, 100, 0.20)` → `False` (15% missing ≤ 20%).
- boundary: `coverage_bad(80, 100, 0.20)` → `False` (exactly 20% missing is not
  `>`); `coverage_bad(79, 100, 0.20)` → `True`.
- `coverage_bad(0, 0, 0.20)` → `False` (empty universe deferred to the zero-gate).

**Prove the lock fails under mutation** (`lock-and-mutate`): flip the `>` to `<`
(or `>=`) in `coverage_bad` and confirm the boundary assertions fail; restore.
Also confirm that deleting the guard call from one probe's `main()` is caught — if
you cannot exercise `main()` without a network, at minimum add a structural check
that each of the seven files contains a non-zero return keyed on coverage (e.g.
`grep`-style assertion in the test that the guard line is present), and pair it
with the behavioral `coverage_bad` mutation test above so the numeric logic is
truly locked, not just its presence.

**Verify**: `python3 test_bot.py; echo rc=$?` → `rc=0` with the new test; the
boundary assertions fail when `>` is mutated (demonstrated), then restored.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `python3 test_bot.py` exits 0, zero failures.
- [ ] `python3 -m py_compile gate_probe.py m0_probe.py liq_move_probe.py liq_noise_probe.py cumrise_probe.py alert_filter_check.py kasih2_red_stats.py` exits 0.
- [ ] Each of the six probes returns a non-zero code (3) on insufficient coverage,
      placed **before** the table computation:
      `grep -n "coverage_bad" gate_probe.py m0_probe.py liq_move_probe.py liq_noise_probe.py cumrise_probe.py alert_filter_check.py` → one hit each.
- [ ] `kasih2_red_stats.py` returns non-zero (5) at the floor-not-met branch.
- [ ] The `coverage_bad` helper is locked behaviorally and the lock fails when `>`
      is mutated (demonstrated).
- [ ] No edits to `kasih_scan.py` / `kasih2_scan.py` (032's files), no
      `LOGIC_VERSION` change, nothing outside the in-scope list (`git status`).
- [ ] `plans/README.md` status row updated.

## STOP conditions

Stop and report if:

- Any probe's `main()` does not match the "print coverage → zero-gate → tables →
  return 0" shape in "Current state" (drift, or an already-different structure).
- A probe already contains a coverage/partial-fetch guard you didn't expect
  (someone landed a fix) — report and skip that file.
- Adding `probe_common.py` would create an import cycle (a probe imported by the
  module) — fall back to the inlined 3-line body.
- The threshold choice feels load-bearing to a published number (it should only
  gate a *degraded* run) — report your chosen value rather than guessing high.

## Maintenance notes

- These seven tools share ~7 copy-pasted blocks (see the direction note attached
  to spike plan **029**). If 029 lands a shared `research_common.py`, this
  `coverage_bad` helper is a natural first tenant — fold `probe_common.py` into
  it then. Until then, keep the guard's numeric logic in one function so it can't
  drift silently between tools.
- A reviewer should confirm: the guard sits **before** any table/`print` of a
  statistic, the return code is 3 (distinct from the zero-data 2), and no
  published-number computation changed.
- The threshold is `engineering` (operator-chosen). If a future run legitimately
  tolerates higher per-symbol failure (a thin universe), raise `MAX_MISS_FRAC`
  with a comment — do not remove the guard.
