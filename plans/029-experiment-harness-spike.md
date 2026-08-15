# Plan 029 (SPIKE): Design a shared experiment harness for the ~25 one-shot `*_arms.py`/`*_scan.py` tools

> **Executor instructions**: This is a **design/spike plan, not a build-everything plan**.
> The deliverable is a written proposal + a *small* prototype extraction behind a flag,
> NOT a migration of all 25 tools. Do not refactor any existing experiment tool's behavior.
> When done, produce the design doc and update this plan's status row in `plans/README.md`.
>
> **Drift check (run first)**: `ls *_arms.py *_scan.py | wc -l` (baseline: 25 families).

## Status

- **Priority**: P3
- **Effort**: L (spike is M; a full migration would be XL and is explicitly out of scope)
- **Risk**: LOW (spike touches nothing live; a future migration would be higher)
- **Depends on**: none
- **Category**: direction (design)
- **Planned at**: commit `4e9b143`, 2026-08-15

## Why this matters

The repo has ~25 one-shot experiment tools (`*_arms.py`, `*_scan.py`, `press_backtest.py`,
`opfire_scan.py`, …), each re-implementing the same scaffolding: point-in-time frozen-dataset
loading, a self-re-exec/`child_env` mutation-worker pattern (8 tools), a `wilson()` interval
(≥4 copies), fixed-budget arm dispatch, and a prereg/result markdown pairing. That
duplication is **where the repo's recurring defects breed**: several documented "dead lock",
"docs-lie", and "no-op flag" bugs (e.g. `BT_CANDLE` dead in the overrides table, a lock that
read a docstring, a `child_env` omission that made a run a silent no-op) recurred *because*
each tool hand-rolls the harness. `architecture_proposal.md` and `PIVOT_V2_PLAN.md` already
articulate the owner's direction ("أقلّ درجة من الكاتالوج = الحافة حقّتنا"); a shared
`experiment.py` the tools import would make a new experiment a *config*, not a 500-line file,
and shrink the surface these defects live on. **Grounding**: 25 families; 8 self-reexec
copies; 4 `wilson` copies; frozen-load duplicated across `base_arms`/`base2_arms`/`anchor_arms`/
`ranker*_arms`/`stability_arms`/`press_scan`/`cliff_scan`/… .

This is a **maintainer decision**, presented as a grounded option. The spike de-risks it;
the migration (if the owner wants it) is separate work.

## Deliverable

A design doc `plans/029-experiment-harness-design.md` (written by the executor) containing:
1. **Inventory** — the exact shared concerns, with `file:line` evidence per tool of each
   duplicated piece (frozen-load, `child_env`/re-exec, `wilson`, arm dispatch, result-writer,
   prereg parsing). Confirm the 25/8/4 counts and list which tools share which piece.
2. **Proposed `experiment.py` surface** — a minimal API the tools would import:
   - `load_frozen(run_id) -> dataset` (single PIT loader; today duplicated),
   - `run_arms(arms, budget, snapshot) -> results` (fixed-budget dispatch — the karpathy
     "constant budget" rule already adopted ad hoc; centralize it),
   - `wilson(k, n)` (one copy),
   - `write_result(prereg_path, results) -> md` (the result-writer pattern),
   - the mutation-worker/`child_env` helper (so the "run in foreground, restore on SIGTERM,
     git-status after each round" lessons live in ONE place).
   For each, cite the current N copies it replaces.
3. **A working prototype** — extract **one** of these (recommend `wilson` + `load_frozen`,
   the safest) into `experiment.py`, and migrate **exactly one** tool (recommend the
   simplest `*_arms.py`) to import it, behind a proof that its output is byte-identical to
   today. Do NOT migrate the others.
4. **Migration plan + risks** — order, blast radius per tool, and the hard constraints the
   migration must honor (see below), plus open questions for the owner.

## Hard constraints the design must honor (from CLAUDE.md)

- Experiment results are **pre-registered before numbers**; a harness must not make it easier
  to move a target after seeing results. The `write_result` API should refuse to emit if the
  prereg is missing/edited-after (or at least flag it).
- The "constant budget in one run" rule (adopted from `karpathy/autoresearch`) is a
  correctness invariant — arms must share one snapshot/budget or a comparison is invalid
  (`T-CLIFF` was corrupted by violating this). The harness must enforce it structurally.
- Locks must be able to fall (mutation). The mutation-worker helper must keep the documented
  lessons: foreground-only mutation, `atexit`+SIGTERM restore, `git status` after each round,
  `PYTHONDONTWRITEBYTECODE=1` + `rm -rf __pycache__`.
- Zero change to any *published experiment's numbers* — a migrated tool must reproduce its
  `*_result.md` byte-for-byte (or the migration is wrong).

## Commands you will need

| Purpose | Command | Expected |
|---------|---------|----------|
| Inventory the duplication | `grep -ln "def wilson\|child_env\|load_frozen\|frozen_run_id" *_arms.py *_scan.py *.py` | the per-piece tool lists |
| Tests | `python3 test_bot.py` | exit 0 (the prototype must not break the suite) |
| Prototype parity | run the one migrated tool's workflow / compare its output to its `*_result.md` | byte-identical |

## Scope

**In scope**:
- `plans/029-experiment-harness-design.md` (the design doc — the primary deliverable).
- `experiment.py` (create — prototype with 1-2 extracted helpers).
- **One** experiment tool migrated to import the prototype, with parity proof.
- `test_bot.py` — a test for the extracted `wilson`/`load_frozen` (they're pure, testable).

**Out of scope**:
- Migrating more than one tool.
- Changing any experiment's logic, arms, thresholds, or published numbers.
- Any production screening path (`Super_stock.py` roots) — untouched.

## Git workflow

- Branch: `advisor/029-experiment-harness-spike`
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Inventory (evidence-based)

Produce the duplication map with `file:line` per piece per tool. Confirm counts. Write it
into the design doc.

**Verify**: the doc lists ≥4 `wilson` copies, ≥8 `child_env`/re-exec copies, and the
frozen-load duplication, each with citations.

### Step 2: Propose the API

Write the `experiment.py` surface (signatures + one-line contracts), each annotated with the
N current copies it replaces and how it enforces the constant-budget + prereg constraints.

**Verify**: the doc has a concrete API section; each function names its constraint.

### Step 3: Prototype the two safest helpers + migrate one tool

Create `experiment.py` with `wilson()` and `load_frozen()` extracted **verbatim** from an
existing tool (pick the canonical copy). Migrate **one** simple `*_arms.py` to import them.
Prove byte-identical output (compare to its `*_result.md`, or a deterministic dry-run).

**Verify**: `python3 test_bot.py` → exit 0; the migrated tool reproduces its published output
exactly; a unit test for `experiment.wilson` matches the old copies.

### Step 4: Write the migration plan + open questions

In the design doc, list migration order, per-tool blast radius, and the open questions for the
owner (e.g. "should `write_result` hard-refuse on an edited prereg, or just warn?"; "is a
full migration worth it, or only new experiments adopt the harness?").

**Verify**: the doc ends with a clear owner-decision section.

## Done criteria

- [ ] `plans/029-experiment-harness-design.md` exists with inventory, API, migration plan, open questions
- [ ] `experiment.py` exists with `wilson` + `load_frozen` extracted verbatim
- [ ] Exactly ONE tool migrated, with byte-identical-output proof
- [ ] `python3 test_bot.py` exits 0; a `wilson` unit test passes
- [ ] No experiment's published numbers changed; no production root touched
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report if:
- The migrated tool's output is NOT byte-identical — the extraction diverged; report the
  diff, do not "accept" it.
- Any extraction would require changing a tool's logic to fit the API — that means the API is
  wrong; note it as an open question rather than forcing the tool.
- The owner has not signaled they want this direction — the spike is fine to produce, but do
  NOT begin migrating tools beyond the one prototype without explicit approval.

## Maintenance notes

- This is the "make the experiment infrastructure a library" half of the audit's direction
  finding D2; the D1 half (hunter-harvest reliability) is delivered concretely by plan 027.
- The whole value is *shrinking the surface* where the repo's documented harness defects
  recur — so the migration, if pursued, must preserve every lesson those defects taught
  (listed in "Hard constraints"). A harness that loses those lessons would be a net negative.
- Keep it a spike until the owner decides; a 25-tool migration is XL and only worth it if
  more experiments are coming.
