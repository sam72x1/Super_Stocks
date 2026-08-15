# Plan 019: Fix three imagined-key / boundary bugs in the display & enrichment layer

> **Executor instructions**: Follow this plan step by step. Each of the three fixes is
> independent — do them in order, verify each, and if a STOP condition hits on one, still
> report progress on the others. When done, update this plan's status row in
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4e9b143..HEAD -- Super_stock.py`
> If Super_stock.py drifted, confirm each excerpt below still matches before editing that
> spot; on a mismatch for a given fix, STOP that fix and report.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `4e9b143`, 2026-08-15

## Why this matters

Three separate "the code reads a dict key that isn't there / treats a real value as
missing" bugs in the non-root display & enrichment layer. Each is a small, safe fix, and
each silently degrades a signal the methodology cares about:

- **Fix A** — a gap-edge target is mislabeled because the code reads `gaps_above["zones"]`
  when the real key is `all_zones`; the "حافة فجوة فوقية" (gap-edge) label can never fire.
- **Fix B** — `enrich` treats a genuine **0%** short-of-float as "missing" (`if sp`) and
  overwrites it with a stale cached percentage; a zero-short reading ("صفر شورت", a
  positive pivot signal) can display as non-zero.
- **Fix C** — `_dump_actor` iterates a fallback chain that includes `"fintel_short"`, a key
  that is **never written** anywhere in the repo; the rung is inert.

## Current state

### Fix A — `gaps_above["zones"]` → `all_zones`

`Super_stock.py:2758-2761` (`all_unfilled_gaps_above` return — key is `all_zones`, there is no top-level `zones`):
```python
    return {
        "daily": daily, "weekly": weekly, "monthly": monthly,
        "all_zones": allz, "count": len(allz), "nearest": nearest,
    }
```
`Super_stock.py:3703` stores it: `"gaps_above": gaps_above,`
`Super_stock.py:8616` reads the wrong key (always `None` → loop never runs):
```python
            for z in ((r.get("gaps_above") or {}).get("zones") or []):
                if (isinstance(z, dict) and z.get("bottom")
                        and abs(t2 - round(float(z["bottom"]), 2)) < 0.005):
                    return "حافة فجوة فوقية"
            return "سلّم المقاومات اليومي"
```
Each zone dict carries `"bottom"` (used at 2755 for sorting), so the loop body is correct
once the key is right.

### Fix B — `if sp` treats real 0% short as missing

`Super_stock.py:4939-4941`:
```python
                sp = info.get("shortPercentOfFloat")
                r["short_pct"] = (round(sp * 100, 1) if sp
                                  else cached.get("short_pct") or _prev_short_pct)
```
`if sp` is false for a real `0.0` **and** for `NaN` (Yahoo sometimes returns `nan`). A
genuinely zero-short stock then displays a stale cached non-zero value. Contrast the
correct pattern used elsewhere (`_or_cache`, ~`Super_stock.py:9273`) which tests `not in
(None, "")`. `short_pct` is a **display/context** field (M13 gates on FINRA *volume*, not
this), so this is safe to fix.

### Fix C — `_dump_actor` reads never-written `fintel_short`

`Super_stock.py:10122-10126`:
```python
        srt = None
        for k in ("shares_available", "fintel_short", "finra_short", "short"):
            v = (s or {}).get(k)
            if v is not None:
                srt = float(v)
                break
```
`grep -rn '"fintel_short"' Super_stock.py` → only this line; the key is never assigned.
The intended Fintel figure lives elsewhere; the chain still works via `finra_short`/`short`,
so this is a low-impact dead rung.

**Repo conventions**: fail-safe reads with `(x or {}).get(...)`; NaN-safety is a named
lesson in this repo ("NaN is not None"); enrichment writes display fields, never gates.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests | `python3 test_bot.py` | exit 0 |
| Confirm `fintel_short` never written | `grep -rn 'fintel_short' Super_stock.py` | only the `_dump_actor` read |
| Find the real fintel short field | `grep -n '"fintel"\|short_volume\|fintel_daily' Super_stock.py` | shows where fintel short lives |

## Scope

**In scope**:
- `Super_stock.py` — lines 8616 (Fix A), 4939-4941 (Fix B), 10123 (Fix C).
- `test_bot.py` — tests for A and B (C is a trivial dead-key removal; add a test only if cheap).

**Out of scope**:
- `all_unfilled_gaps_above`, `enrich`'s other logic, `_dump_actor`'s alert building —
  only the three specific lines.
- Any gate/root. `short_pct`, target-source labels, and dump-alert short figures are all
  display/context. No `LOGIC_VERSION`.

## Git workflow

- Branch: `advisor/019-imagined-key-display-fixes`
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1 (Fix A): change `"zones"` to `"all_zones"`

At `Super_stock.py:8616`:
```python
            for z in ((r.get("gaps_above") or {}).get("all_zones") or []):
```
Nothing else changes — the loop already reads `z["bottom"]`.

**Verify**: read line 8616 — key is `all_zones`. `python3 test_bot.py` → exit 0.

### Step 2 (Fix A test): assert the gap-edge label now fires

Add a test that builds an `r` with a `gaps_above` dict shaped like the real return (an
`all_zones` list of `{"bottom": X}`) and a `t2` matching one zone's bottom, then asserts
the target-source function returns `"حافة فجوة فوقية"` (not `"سلّم المقاومات اليومي"`).
Grep `test_bot.py` for existing `_target_source`/`targets_src`/`gaps_above` tests to find
the callable and pattern.

**Verify**: `python3 test_bot.py` → exit 0; new `✅` prints.

### Step 3 (Fix B): make the short-of-float read 0.0-safe and NaN-safe

At `Super_stock.py:4939-4941`:
```python
                sp = info.get("shortPercentOfFloat")
                _sp_ok = isinstance(sp, (int, float)) and sp == sp   # ليس None وليس NaN
                r["short_pct"] = (round(sp * 100, 1) if _sp_ok
                                  else cached.get("short_pct") or _prev_short_pct)
```
`sp == sp` is the standard NaN test (NaN != NaN). Now a real `0.0` yields `short_pct = 0.0`
(displayed as zero short), and only a truly absent/NaN value falls back to cache.

**Verify**: read the lines. `python3 test_bot.py` → exit 0.

### Step 4 (Fix B test): assert 0.0 is preserved, None falls back

Add a test that calls the smallest unit exercising this (or a helper if `enrich` is hard
to isolate — otherwise construct `info={'shortPercentOfFloat': 0.0}` and assert the
resulting `short_pct` is `0.0`, and `info={}` (missing) falls back to the cached value).
If `enrich` can't be unit-isolated without network, extract the two-line decision into a
tiny pure helper `_short_pct_from(sp, cached, prev)` and test that — but only if it stays
byte-identical for all non-zero inputs. Prefer testing in place if feasible.

**Verify**: `python3 test_bot.py` → exit 0; new `✅` prints; mutation: revert to `if sp`
and confirm the 0.0 test fails.

### Step 5 (Fix C): remove or repoint the dead `fintel_short` rung

Simplest correct fix — drop the inert key from the chain:
```python
        for k in ("shares_available", "finra_short", "short"):
```
Only if the grep in "Commands" shows a real fintel short field that *should* be a rung
(e.g. `(s.get("fintel") or {}).get("short_volume")`), repoint it instead — but do that
only if you can confirm that field is populated on the records reaching `_dump_actor`;
otherwise just remove the dead key. Removal is behavior-preserving (the key was always
`None`).

**Verify**: `grep -rn 'fintel_short' Super_stock.py` returns nothing. `python3 test_bot.py`
→ exit 0.

## Test plan

- Fix A: gap-edge label fires on a matching zone (was impossible before).
- Fix B: `short_pct` preserves a real `0.0`, falls back only on None/NaN; mutation round.
- Fix C: no test needed for a dead-key removal, but confirm no test asserted the old
  4-element chain (grep `fintel_short` in `test_bot.py`).

## Done criteria

- [ ] `python3 test_bot.py` exits 0; new tests for A and B present and passing
- [ ] Line 8616 reads `all_zones`; the gap-edge label can now fire
- [ ] Short-of-float read is 0.0-safe and NaN-safe
- [ ] `grep -rn 'fintel_short' Super_stock.py` returns nothing (or the rung points at a real, populated field)
- [ ] Mutation check passed for Fix B
- [ ] `git status` shows only `Super_stock.py`, `test_bot.py`
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop the affected fix and report if:
- (A) `all_unfilled_gaps_above` no longer returns `all_zones` (drift) — report the actual key.
- (B) A test asserts the old `if sp` behavior, or `short_pct` turns out to feed a gate
  (grep — it should not) — report before changing.
- (C) `_dump_actor` records actually carry a `fintel_short` key from a path you didn't see
  — report it (the grep says no, but verify on the record shape passed in).

## Maintenance notes

- These three are the same recurring class the repo keeps catching ("imagined key" /
  "display line with no field" / "NaN is not None"). A ruff/pyflakes gate (plan 016) would
  not catch these (the keys are dynamic strings), so they need review vigilance.
- Reviewer should confirm each change touches only display/context, no gate/number.
