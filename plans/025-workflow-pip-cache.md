# Plan 025: Add `cache: pip` to the research/runner workflows that lack it

> **Executor instructions**: Follow this plan step by step. This is a mechanical,
> repetitive YAML edit across many files — verify each file's YAML still parses. If a
> STOP condition occurs, stop and report. When done, update this plan's status row in
> `plans/README.md`.
>
> **Drift check (run first)**: `ls .github/workflows/ | wc -l` and
> `grep -rL "cache:" .github/workflows/*.yml | head` to see the current set lacking cache.

## Status

- **Priority**: P3
- **Effort**: S (mechanical, but touches many files)
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `4e9b143`, 2026-08-15

## Why this matters

Only `tests.yml` sets `cache: pip` on `actions/setup-python`; ~69 other workflows
cold-install `pandas==3.0.5`, `numpy==2.4.6`, `yfinance`, and (for the suite) `PyYAML`
every run — tens of seconds of avoidable heavy-wheel install per job, multiplied across
~23 cron workflows (several daily) plus research/backtest jobs with `timeout-minutes:
300-350`. The caching pattern is already known and demonstrated in `tests.yml`; this just
applies it everywhere. Low individual leverage (CI minutes only), but cheap and repeatable.
Because `requirements.txt` is pinned, the cache key is stable.

## Current state

`tests.yml` (the pattern to replicate):
```yaml
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
```

A typical uncached workflow — `press_radar.yml:22-27`:
```yaml
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: pip install -r requirements.txt
```
i.e. the only change is adding `cache: pip` under the `setup-python` `with:`.

**Convention**: `setup-python@v5` with `cache: pip` keys the cache on the resolved
`requirements.txt` hash automatically — no extra config needed.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| List workflows lacking cache | `for f in .github/workflows/*.yml; do grep -q "cache:" "$f" \|\| echo "$f"; done` | the files to edit |
| Validate one file | `python3 -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" <file>` | no error |
| Validate all | `for f in .github/workflows/*.yml; do python3 -c "import yaml,sys; yaml.safe_load(open('$f'))" \|\| echo "BAD $f"; done` | no `BAD` lines |

## Scope

**In scope**:
- Every `.github/workflows/*.yml` that has an `actions/setup-python` step **without**
  `cache: pip`. Add `cache: pip` under that step's `with:`.

**Out of scope**:
- `tests.yml` (already cached).
- Workflows that do NOT use `setup-python` (nothing to cache).
- Any `run:`/logic/step-ordering change — **only** add the one `cache: pip` line per
  setup-python step. Do not "improve" anything else while in the file.
- Any Python source.

## Git workflow

- Branch: `advisor/025-workflow-pip-cache`
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Enumerate the target files

Run the "list workflows lacking cache" command. That is your exact work list. Record the
count.

**Verify**: the list is non-empty and excludes `tests.yml`.

### Step 2: Add `cache: pip` to each setup-python step

For each file, find the `uses: actions/setup-python@v5` step and add `cache: pip` under its
`with:` block, matching indentation exactly (see the `tests.yml` excerpt). If a workflow has
a setup-python step but no `with:` block, add one:
```yaml
        with:
          python-version: "3.11"
          cache: pip
```
Only edit the setup-python step. Leave everything else byte-identical.

**Verify** (per file, or batch at the end): the all-files validation command prints no `BAD`
lines. `git diff --stat` shows only the workflow files, each with a tiny (+1 or +3 line)
change.

### Step 3: Confirm no behavior change beyond caching

Read `git diff` and confirm every hunk is exactly the `cache: pip` addition (and, where
needed, a `with:`/`python-version` line) — no reordered steps, no changed commands.

**Verify**: `git diff` review; the all-files YAML validation passes.

## Test plan

- No `test_bot.py` tests (CI config). Verification is: every touched workflow still parses
  as valid YAML, and the diff is confined to the `cache: pip` additions.

## Done criteria

- [ ] Every `setup-python` workflow (except `tests.yml`, already done) has `cache: pip`
- [ ] All `.github/workflows/*.yml` parse as valid YAML (no `BAD` lines)
- [ ] `git diff` shows only `cache: pip` (and minimal `with:`) additions — no other change
- [ ] `git status` shows only workflow files
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report if:
- A workflow uses a different Python setup mechanism (e.g. a container, or `setup-python`
  at a non-`v5` version with a different `with:` schema) — handle it correctly or report it
  rather than forcing the pattern.
- Any file fails YAML validation after your edit — revert that file and report.

## Maintenance notes

- Low-leverage but harmless; the value is faster/cheaper CI, especially on the
  timeout-300 research jobs.
- Consider (future, out of scope here) a shared composite action for Python setup so this
  can't drift across ~70 files again.
