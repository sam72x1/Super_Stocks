# Plan 037: Refresh CLAUDE.md — add the 5 undocumented new tools and update the stale workflow inventory

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving on. If any STOP condition
> occurs, stop and report — do not improvise. When done, update this plan's status
> row in `plans/README.md` (unless a reviewer told you they maintain the index).
>
> **Drift check (run first)**:
> `git diff --stat 5cb88df..HEAD -- CLAUDE.md`
> Written against `origin/main` (`5cb88df`). If `git rev-parse --short HEAD` is not
> `5cb88df` or a descendant, or if `CLAUDE.md` has no section heading
> `## الملفات المهمة`, **STOP** — you are on the wrong tree (the operator must
> update to `origin/main`). If the workflow-inventory bullet (see "Current state")
> is no longer at/near line 109 or its text differs materially, locate it by its
> leading token `` `.github/workflows/` — `` before editing.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: docs
- **Planned at**: commit `5cb88df` (origin/main), 2026-08-21

## Why this matters

`CLAUDE.md` is this repo's single onboarding surface — the first file every new
session reads. It grew ~1,800 lines in this development batch and documents most
new tools, but **five new tools have zero mention** (verified: grep-count 0 each):
`ceiling_arms`, `liq_noise_probe`, `liq_case_probe`, `sweep_reclaim_arms`,
`method_window_arms`. Each has a real scheduled or dispatch workflow
(`.github/workflows/ceiling.yml`, `liq_noise.yml`, `liq_case.yml`,
`sweep_reclaim.yml`, `method_window.yml`).

Separately, the onboarding **workflow inventory** at `CLAUDE.md:109` still lists
only the original handful (`daily_screener`, `pullback_monitor`, `scan_earnings`,
`hand_digest`, `acc_verify`, `ignition`, `backtest`, `analyze`/`technical`) and
none of the ~20 workflows added in this batch — while CLAUDE.md's own 2026-08-16
"فحص صحة شامل" entry says "فُحص **17 workflow مجدولًا**". The doc is internally
inconsistent (line 109 enumerates ~8; the prose says 17 scheduled exist) and an
onboarding agent will not learn these tools/workflows exist.

Cost is concrete precisely because the repo's convention is that CLAUDE.md is
authoritative for onboarding. This is a docs-only fix — no code, no tests, no
behavior change.

## Current state

`CLAUDE.md` at `5cb88df`.

- **Tool inventory**: the `## الملفات المهمة` section is a list of `- ` bullets,
  one per notable tool, each a short description of role + workflow + guard notes.
  It already documents e.g. `kasih_scan.py`, `kasih2_scan.py`, `exit_stop_arms.py`,
  `gate_probe`, `m0_probe`, etc. The five tools above are missing.
- **Workflow inventory bullet** (line 109):
  ```
  - `.github/workflows/` — daily_screener.yml (10ص السعودية) · pullback_monitor.yml (كل 30د) · scan_earnings.yml (أداة الأرباح، يومي 06:00 UTC) · **hand_digest.yml (…)** · **acc_verify.yml (…)** · **ignition.yml (…)** · backtest.yml · analyze.yml/technical.yml (يدوي).
  ```
  This enumerates ~8 of the ~20+ workflows now present under `.github/workflows/`.

To see the current tool→workflow reality:
`ls .github/workflows/*.yml` and `grep -l "on:" .github/workflows/*.yml`.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| List all workflows | `ls .github/workflows/*.yml` | the full set incl. `ceiling.yml`, `liq_noise.yml`, `liq_case.yml`, `sweep_reclaim.yml`, `method_window.yml` |
| Confirm tools absent (before) | `for t in ceiling_arms liq_noise_probe liq_case_probe sweep_reclaim_arms method_window_arms; do echo "$t $(grep -c "$t" CLAUDE.md)"; done` | each `0` |
| Confirm tools present (after) | same command | each `≥1` |
| Read a tool's purpose | open `ceiling_arms.py` / `liq_noise_probe.py` / etc. and read the module docstring | one-line role for each |
| Regression (no code touched) | `python3 test_bot.py; echo "rc=$?"` | `rc=0` (CLAUDE.md changes don't affect tests; run to prove nothing else changed) |

## Scope

**In scope** (the only file to modify):
- `CLAUDE.md` — add 5 tool bullets to `## الملفات المهمة`; refresh the workflow
  bullet at line 109.

**Out of scope** (do NOT touch):
- Any `.py`, `.yml`, or state file. This is documentation only.
- The dated decision-log entries in CLAUDE.md (the "قرارات مطابِقة لفيصل" and
  history sections) — do not rewrite them; only add the tool bullets and refresh
  the workflow line.
- `LOGIC_VERSION`, tests. No code path changes.

## Git workflow

- Branch: `advisor/037-claude-md-inventory`.
- Commit message ends with the repo's two trailer lines (copy from recent
  `git log`). Do NOT push/PR unless instructed.

## Steps

### Step 1: Read each new tool's purpose from its own docstring

For each of `ceiling_arms.py`, `liq_noise_probe.py`, `liq_case_probe.py`,
`sweep_reclaim_arms.py`, `method_window_arms.py`, open the file and read its
module/`main` docstring to get an accurate one-line role and its workflow name.
Do **not** invent a description — quote/paraphrase the docstring so the doc matches
reality. If a docstring is missing or unclear, read enough of `main()` to state
what the tool measures and STOP if you cannot describe it truthfully.

**Verify**: you have a one-line, source-grounded role for each of the five.

### Step 2: Add 5 bullets to `## الملفات المهمة`

Add one `- ` bullet per tool, matching the surrounding style (Arabic, short,
naming the tool file + its workflow + whether it's dispatch/scheduled + the
one-line role). Place them near the related existing entries (the research/probe
tools are grouped together; put `ceiling_arms`/`sweep_reclaim_arms`/
`method_window_arms` near `exit_stop_arms`/`kasih` entries, and `liq_noise_probe`/
`liq_case_probe` near `gate_probe`/`m0_probe`/`liq_move_probe` if that entry
exists). Keep each factual and short — this is an index, not an essay.

**Verify**: the after-grep (`for t in …`) shows each of the five `≥1`.

### Step 3: Refresh the workflow inventory bullet (line 109)

Either (a) extend the enumeration to include the new scheduled/dispatch workflows,
or (b) — cleaner and drift-proof — make it explicitly representative and point to
the directory, e.g. append: "‏— والقائمةُ الكاملةُ (‏~20 workflow) في
`.github/workflows/`؛ هذا تعدادٌ تمثيليّ لا حصريّ." Prefer (b) so the line does not
go stale again the next time a workflow is added; if the operator/reviewer prefers
a full list, enumerate from `ls .github/workflows/*.yml`. Do not leave the line
implying only ~8 workflows exist when CLAUDE.md's own prose says 17 are scheduled.

**Verify**: line 109 (or the moved bullet) no longer reads as an exhaustive list of
~8; `git diff CLAUDE.md` shows only the two additions (tool bullets + workflow
line).

### Step 4: Regression

**Verify**: `python3 test_bot.py; echo "rc=$?"` → `rc=0` (proves no code changed);
`git status` shows only `CLAUDE.md` modified.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `for t in ceiling_arms liq_noise_probe liq_case_probe sweep_reclaim_arms method_window_arms; do grep -q "$t" CLAUDE.md || echo "MISSING $t"; done` prints nothing (all five present).
- [ ] The workflow bullet (line ~109) either enumerates the new workflows or is
      marked representative with a pointer to `.github/workflows/`.
- [ ] `git status` shows **only** `CLAUDE.md` modified — no `.py`/`.yml`/state file.
- [ ] `python3 test_bot.py` exits 0 (nothing else changed).
- [ ] Each new bullet's description is grounded in the tool's own docstring (a
      reviewer reading the tool file agrees the bullet is accurate).
- [ ] `plans/README.md` status row updated.

## STOP conditions

Stop and report if:

- A tool's purpose cannot be described truthfully from its source (don't guess).
- The `## الملفات المهمة` section or the workflow bullet isn't found where
  described (drift) — locate by heading/token, and if still absent, STOP.
- Editing would require changing a dated decision-log entry (out of scope).

## Maintenance notes

- Making line 109 "representative — see `.github/workflows/`" (option b) is the
  durable fix: it stops going stale each time a workflow is added. If the reviewer
  wants an exhaustive list instead, add a note that it must be updated when
  workflows are added, or (better) leave a tiny check — the repo's own prose figure
  ("17 مجدولًا") is what exposed this drift; a representative pointer avoids
  re-introducing a hard count that ages.
- Whenever a new standalone tool + workflow is added in a future session, add its
  CLAUDE.md bullet in the same commit (the repo's "update CLAUDE.md with every
  significant change" rule) so this inventory doesn't drift again.
