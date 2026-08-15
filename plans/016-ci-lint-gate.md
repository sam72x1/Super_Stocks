# Plan 016: Add a report-only static-analysis gate to CI (ruff F-codes + pyflakes)

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving on. If any STOP condition
> occurs, stop and report — do not improvise. When done, update this plan's status row
> in `plans/README.md` (unless a reviewer told you they maintain the index).
>
> **Drift check (run first)**: `git diff --stat 4e9b143..HEAD -- .github/workflows/tests.yml`
> If it changed since this plan was written, compare against the excerpt below; on a
> mismatch, STOP.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `4e9b143`, 2026-08-15

## Why this matters

The test suite runs **fully offline by design** — every data fetcher is mocked. That is
correct for logic testing, but it means the suite structurally **cannot** execute the
live-only branches of the runner scripts (`ignition_live.py`, `press_radar.py`,
`split_hunter.py`, …). A `NameError`, an undefined name in an `except` branch, or an
unused-import shadowing bug in one of those branches ships **green** and only surfaces
when the owner's live alert crashes at 3am. The repo already installs `ruff` and
`pyflakes` in its session-start hook (`.claude/hooks/session-start.sh:19-20`) "so static
analysis works in-session" — but nothing runs them, and `grep -rlE 'ruff|pyflakes|mypy'
.github/` returns nothing. This is the cheapest gate in the repo left un-wired: it
catches an entire bug class the offline suite cannot reach, at near-zero cost.

The gate starts **report-only** on a narrow, high-signal rule set (undefined names,
unused imports/vars, a few real-bug F-codes) to avoid a 19k-line noise wall, then can be
promoted to a hard gate once clean.

## Current state

- `.github/workflows/tests.yml` — the one CI gate; runs only `python3 test_bot.py`.

`.github/workflows/tests.yml` (full):
```yaml
name: Tests
permissions:
  contents: read
concurrency:
  group: tests-${{ github.ref }}
  cancel-in-progress: true
on:
  push:
  pull_request:
jobs:
  tests:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run full test suite
        run: python3 test_bot.py
```

`.claude/hooks/session-start.sh:19-20` already installs the tools:
```bash
  echo "🔧 تثبيت أدوات الفحص (ruff, pyflakes)..."
  python3 -m pip install --quiet --disable-pip-version-check ruff pyflakes
```

There is **no** `pyproject.toml`, `ruff.toml`, or `setup.cfg` in the repo (confirm with
`ls pyproject.toml ruff.toml setup.cfg 2>/dev/null`), so ruff config must be added
explicitly or passed on the CLI.

**Repo conventions**: `requirements.txt` documents that *every* non-stdlib import used by
the suite must have a pinned line — but ruff/pyflakes here run in a **separate CI step**,
not imported by the suite, so they are installed ad hoc in that step (do NOT add them to
`requirements.txt`, which is the production install and must stay minimal).

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests | `python3 test_bot.py` | exit 0 |
| Lint (local trial) | `python3 -m pip install ruff pyflakes && ruff check --select F .` | prints findings (may be non-empty) |
| Confirm no ruff config exists | `ls pyproject.toml ruff.toml setup.cfg 2>/dev/null` | no output |

## Scope

**In scope**:
- `.github/workflows/tests.yml` (add a lint step or a parallel `lint` job)
- `ruff.toml` (create — minimal config scoping the rule set)

**Out of scope**:
- `requirements.txt` — do NOT add ruff/pyflakes there (they're CI-only, not runtime deps).
- Fixing the lint findings themselves — this plan only *surfaces* them (report-only).
  A follow-up decides which to fix. (If a finding is a real undefined-name crash you
  can trivially confirm, note it in your report but do not fix it here.)
- Any source `.py` file.

## Git workflow

- Branch: `advisor/016-ci-lint-gate`
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Add a minimal `ruff.toml` scoping the rule set to real-bug F-codes

Create `ruff.toml` in the repo root:
```toml
# فحصٌ ساكن ضيّق النطاق — يلتقط ما لا تراه السويّة (تعمل بلا إنترنت): أسماء غير
# معرّفة · استيراد/متغيّر غير مستعمل · مقارنات معطوبة. لا نمط/تنسيق (ضجيج على 19k سطر).
target-version = "py311"
line-length = 100

[lint]
# F = pyflakes (أخطاء حقيقية) — نبدأ منها فقط.
select = ["F"]
# تجاهل ملفات البيانات/الأدوات المؤقتة إن لزم لاحقًا.
```
Rationale: `--select F` = the pyflakes rule family (undefined names `F821`, unused
imports `F401`, unused vars `F841`, f-string/format bugs, redefinitions) — the highest
signal, lowest noise set. Broader rulesets (`E`, `W`, style) would drown the signal on a
1.2 MB file.

**Verify**: `ruff check .` (locally, after `pip install ruff`) runs and honors the config
(reports only F-codes). Note whether the output is empty or lists findings — record the
count in your report.

### Step 2: Add a report-only lint step to `tests.yml`

Add, **after** the existing "Run full test suite" step (so a lint finding never blocks the
real gate yet), a report-only step:
```yaml
      # فحصٌ ساكن (F-codes فقط) — تقريرٌ لا بوّابة بعد: يلتقط أخطاء الفروع الحيّة
      # التي تعمى عنها السويّة (بلا إنترنت). يُرقّى بوّابةً بعد أن يُنظَّف.
      - name: Static analysis (report-only)
        continue-on-error: true
        run: |
          python3 -m pip install --quiet ruff pyflakes
          echo "::group::ruff (F-codes)"
          ruff check --output-format=github . || true
          echo "::endgroup::"
          echo "::group::pyflakes"
          python3 -m pyflakes Super_stock.py analyze_one.py ignition_live.py press_radar.py \
            split_hunter.py split_filter_hunter.py method_hunter.py envelope_hunter.py \
            pullback_live.py hunter_ledger.py hunter_outcomes.py e2_recover.py \
            ignition_e2_assemble.py telegram_collect.py ctb_harvest.py market_calendar.py || true
          echo "::endgroup::"
```
`continue-on-error: true` + `|| true` = report-only (surfaces findings in the run log /
annotations, never fails the build). This is deliberate: promote it to a hard gate only
after the F-code findings are triaged (a separate follow-up).

**Verify**: the YAML is valid — `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/tests.yml'))"`
→ no error.

### Step 3: Confirm the test suite still gates and the lint step is non-blocking

Re-read the file: the "Run full test suite" step has NO `continue-on-error`, so it remains
the hard gate; the new lint step is `continue-on-error: true`. Order matters only for
readability.

**Verify**: `python3 test_bot.py` → exit 0 (unchanged locally). `python3 -c "import yaml,sys;
d=yaml.safe_load(open('.github/workflows/tests.yml'));
steps=d['jobs']['tests']['steps'];
assert any('test_bot.py' in (s.get('run') or '') and not s.get('continue-on-error') for s in steps);
print('gate intact')"` → prints `gate intact`.

## Test plan

- No new `test_bot.py` tests (this is CI config). Verification is the YAML-validity check
  and the "gate intact" assertion above. Optionally note the ruff finding count in the
  plan's report so the owner can decide the promotion-to-gate follow-up.

## Done criteria

- [ ] `ruff.toml` exists, scopes `select = ["F"]`, `target-version = "py311"`
- [ ] `tests.yml` has a `continue-on-error: true` static-analysis step running ruff + pyflakes
- [ ] The `test_bot.py` step still has no `continue-on-error` (remains the hard gate)
- [ ] `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/tests.yml'))"` succeeds
- [ ] `requirements.txt` unchanged (ruff/pyflakes NOT added there)
- [ ] `git status` shows only `.github/workflows/tests.yml`, `ruff.toml`
- [ ] Report records the current ruff F-code finding count (baseline for the promotion follow-up)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report if:
- `ruff check --select F .` surfaces a finding you can confirm is a **real undefined-name
  crash on a live path** (e.g. `F821` in an `except` branch of a runner) — that is a real
  bug; report it prominently so a follow-up plan fixes it (do not fix it here).
- The repo already has a ruff/pyproject config that conflicts with the new `ruff.toml` —
  report it (the drift check should have caught this; reconcile rather than duplicate).

## Maintenance notes

- Promotion to a hard gate is a deliberate follow-up: once the F-code findings are zero
  (or explicitly `# noqa`-annotated with reasons), remove `continue-on-error`/`|| true`
  from the ruff invocation so undefined-name regressions fail CI.
- Keep the ruleset narrow. Expanding to `E`/`W`/style on this codebase would generate
  thousands of low-value findings and erode trust in the gate.
- The pyflakes step lists the runner files explicitly so it stays fast and focused on the
  live paths the offline suite can't reach; ruff covers the whole tree.
