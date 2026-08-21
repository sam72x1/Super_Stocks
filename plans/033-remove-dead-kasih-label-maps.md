# Plan 033: Remove two truly-dead kasih label maps (and confirm what NOT to delete)

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving on. If any STOP condition
> occurs, stop and report — do not improvise. When done, update this plan's status
> row in `plans/README.md` (unless a reviewer told you they maintain the index).
>
> **Drift check (run first)**: `git diff --stat 52ffe4f..HEAD -- Super_stock.py`
> Locate `_KASIH_F2_AR` and `_KASIH2_SHORT` and compare the "Current state" excerpt below
> against the live code before proceeding; on a mismatch, STOP.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: tech-debt
- **Planned at**: commit `52ffe4f` (origin/main), 2026-08-21

## Why this matters

Two module-level constants were introduced in the T-KASIH labeling work and are **never
referenced anywhere** — not in `Super_stock.py`, not in `test_bot.py`, not in any other module:

- `_KASIH_F2_AR` (F2 class labels) — the header badge uses `_LIQ_CLS_AR` instead, so this map is
  orphaned.
- `_KASIH2_SHORT` (continuation-label short forms) — `kasih_tag_line` compresses to a "مواصلة N من M"
  counter instead, so this map is never read.

This is exactly the dead-code class the repo actively removes: CLAUDE.md records `_LIQ_STAGE_TXT`
being deleted on 2026-08-20 as «كودٌ موجودٌ ولا يُنادى = صنفٌ يمسحه تدقيقُنا الدوريّ». No user-facing
effect — the class badge and continuation info still display via their live paths. Pure dead weight.

**Verified zero references** (do this yourself before deleting — Step 1): each token appears exactly
once (its own definition) across the whole repo.

## What NOT to delete (important — corrects an over-broad earlier finding)

An audit initially flagged `liquidity_verdict` (`Super_stock.py:13112`) and `liquidity_lines`
(`:13141`) as dead too. **They are not dead**: they are referenced **8×** and **2×** respectively in
`test_bot.py` (they have test locks). They are the "مضاربٌ أم قروب؟" verdict superseded by the staged
channel but kept **tested-but-unwired** — the repo's documented *deferred-feature* class (like
`key_levels_block`, `readiness_ratio`, `news_links`), which CLAUDE.md explicitly says **do not delete**.
Whether to re-wire them into `build_ignition_alert` or leave them deferred is an owner decision, not a
cleanup. **This plan does not touch them.**

## Current state

`Super_stock.py:13985-13994+` (the two orphaned maps — `_KASIH2_SHORT` continues past the excerpt to
its closing brace):
```python
_KASIH_F2_AR = {"strong": "قوية (فوق $300 ألف)", "operator": "مضارب",
                "mid": "وسط", "group": "قروب (دون $50 ألف)"}
# اختصاراتُ عرضٍ لمؤشّرات المواصلة (المفاتيحُ الكاملة تبقى هي المقياس):
_KASIH2_SHORT = {"صادقت (إغلاقٌ فوق المرساة)": "صادقت",
                 "خضراء 3-4": "3-4", "خضراء 2": "2", "خضراء 0-1": "0-1",
                 ... (continues to a closing `}`) ...}
```

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Prove zero references | `grep -rn "_KASIH_F2_AR\|_KASIH2_SHORT" .` | ONLY the two definitions in `Super_stock.py` |
| Tests   | `python3 test_bot.py` | exit 0 |
| Scope check | `git status --porcelain` | only `Super_stock.py` |

(Offline suite. Use `python3.11` if `python3` is 3.9.)

## Scope

**In scope**:
- `Super_stock.py`: delete the `_KASIH_F2_AR` definition and the `_KASIH2_SHORT` definition (the full
  dict, up to and including its closing `}`), plus the one-line comment above `_KASIH2_SHORT` if it
  only describes that map.

**Out of scope** (do NOT touch):
- `liquidity_verdict` / `liquidity_lines` (tested-but-deferred — see "What NOT to delete").
- `_LIQ_CLS_AR`, `kasih_tag_line`, or anything that still displays. Any screening root. No
  `LOGIC_VERSION`.

## Git workflow

- Branch: `advisor/033-remove-dead-kasih-maps`
- Commit trailer (exactly): `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Prove zero references (gate — do not skip)

Run `grep -rn "_KASIH_F2_AR" .` and `grep -rn "_KASIH2_SHORT" .`. Each must return **exactly one**
hit: its definition in `Super_stock.py`. If either returns any other hit (a use anywhere — including
a test), STOP: it is not dead, mark that map REJECTED and report.

**Verify**: both greps show only the definitions.

### Step 2: Delete the two definitions

Remove the `_KASIH_F2_AR` dict and the `_KASIH2_SHORT` dict (and the comment that only describes
`_KASIH2_SHORT`). Leave surrounding constants (e.g. the dict ending at `:13984` above `_KASIH_F2_AR`)
untouched.

**Verify**: `python3 -c "import Super_stock"` succeeds (no `NameError`); `grep -n "_KASIH_F2_AR\|_KASIH2_SHORT" Super_stock.py` returns nothing.

### Step 3: Run the suite

**Verify**: `python3 test_bot.py` → exit 0. (If any test fails referencing these names, Step 1 was
wrong — STOP and report.)

## Test plan

- No new test needed (deletion of unreferenced constants). The gate is Step 1's grep plus the suite
  staying green. Optionally add a one-line `check(...)` asserting the names are absent from
  `Super_stock` module namespace, to prevent reintroduction — but this is optional and low-value.

## Done criteria

- [ ] `grep -rn "_KASIH_F2_AR\|_KASIH2_SHORT" .` returns nothing
- [ ] `python3 test_bot.py` exits 0
- [ ] `liquidity_verdict` / `liquidity_lines` untouched (still present, still tested)
- [ ] `git status --porcelain` shows only `Super_stock.py`
- [ ] `git diff` shows only deletions (no other change)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report if:
- Either map turns out to be referenced anywhere (Step 1) — do not delete it.
- Deleting `_KASIH2_SHORT` would leave a dangling comment or break indentation of a following
  statement — report the surrounding structure.

## Maintenance notes

- Lowest-priority of the batch — pure hygiene. Its only value is keeping the "code exists and isn't
  called" surface clean, which the repo's periodic audit does anyway.
- The real lesson recorded here is the *distinction*: **tested-but-unwired ≠ dead**. `liquidity_verdict`/
  `liquidity_lines` have tests, so they are a deferred feature to keep or wire (owner's call), not
  cleanup. Only genuinely zero-reference constants like these two maps are safe to delete.
