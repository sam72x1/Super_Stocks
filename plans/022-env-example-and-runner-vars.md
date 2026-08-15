# Plan 022: Add `.env.example` and a documented runner environment-variable table

> **Executor instructions**: Follow this plan step by step. This plan only adds
> documentation/config-template files — no source code. Run `python3 test_bot.py` after
> (exit 0, proving nothing broke). When done, update this plan's status row in
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4e9b143..HEAD -- README.md` (light — this
> plan mostly adds new files).

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `4e9b143`, 2026-08-15

## Why this matters

The live runner scripts need environment variables that are documented **nowhere**: a new
contributor or executor cannot run any live path without reverse-engineering the required
secrets and toggles from source. There is no `.env.example` (glob returns nothing) and
`README.md` points only at `python3 test_bot.py`. Because the test suite passes fully
offline, a green suite tells the operator nothing about whether a live path is wired. A
names-only `.env.example` plus a README table (var → which runner consumes it → secret vs
toggle) removes that friction without exposing any value.

## Current state

- No `.env*` file exists.
- `README.md` documents the test command and the deps-upgrade protocol, but no env vars.
- Env vars consumed by runners (gathered by `grep -rn "os.environ" *.py` and the workflow
  `env:` blocks — **the executor must re-derive the full list from source, this is the
  starting set, not exhaustive**):
  - **Secrets**: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `POLYGON_API_KEY`,
    `POLYGON_S3_KEY`, `POLYGON_S3_SECRET`, `CLINE_API_KEY`, and (optional data-source keys)
    `ALPHAVANTAGE_KEY`, `FMP_API_KEY`.
  - **Force/toggle vars**: `SUPER_STOCKS_TESTING`, `SCREENER_MODE` (e.g. `DIGEST`/`BACKTEST`),
    `RENEW_ON_CLOSE`, `HUNTER_FORCE`, `PRESS_RADAR_FORCE`, `METHOD_FORCE`, `ENVELOPE_FORCE`,
    plus the `IGNITION_*` family (`IGNITION_HANDOFF_IN/OUT`, `IGNITION_SEGMENT`,
    `IGNITION_END_UTC`, `IGNITION_MAX_RUNTIME_MIN`, `IGNITION_INTERVAL`), `CTB_*`
    (`CTB_HARVEST_CAP`, `CTB_CONTROL_SIZE`, `CTB_LOG`), and the various `BT_*`/`FAISAL_ONLY`
    experiment flags.

**Repo conventions**: `.gitignore` already excludes `*.csv` and measurement dirs but has no
`.env` rule; add one so a real `.env` is never committed. Comments in Arabic are the norm.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Enumerate env vars | `grep -rhoE "os\.environ(\.get)?\(\s*['\"][A-Z0-9_]+" *.py \| grep -oE "[A-Z0-9_]+$" \| sort -u` | the full var list |
| Tests | `python3 test_bot.py` | exit 0 |
| Confirm no real .env exists | `ls .env 2>/dev/null` | no output |

## Scope

**In scope**:
- `.env.example` (create — names + one-line Arabic description each, **no values**)
- `.gitignore` (add `.env` so a real one is never committed; keep `!.env.example` tracked)
- `README.md` (add a "Runner environment" section with a table)

**Out of scope**:
- Any `.py` source. This is documentation only.
- Reproducing any secret value — names and descriptions only (Hard Rule 4).

## Git workflow

- Branch: `advisor/022-env-example`
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Enumerate the real env-var set from source

Run the grep in "Commands" and cross-check against the `env:` blocks in `.github/workflows/`.
Build the authoritative list (the "Current state" set is a starting point — trust the grep
over it). For each var, note: is it a **secret** (token/key) or a **toggle** (force/mode/
config), and which runner(s)/workflow(s) consume it.

**Verify**: your list ⊇ the "Current state" set and every entry maps to at least one file.

### Step 2: Write `.env.example` (names only)

Create `.env.example` with each variable name, `=`, an empty placeholder, and an Arabic
one-line description. **Never** put a real value. Example shape:
```bash
# أسرار (لا تُلصق قيمها هنا — هذا قالب. القيم الحقيقية في GitHub Secrets / بيئتك المحلية)
TELEGRAM_BOT_TOKEN=      # توكن بوت تيليجرام — تنبيهات المالك
TELEGRAM_CHAT_ID=        # معرّف الدردشة (يقبل عدة أرقام بفاصلة)
POLYGON_API_KEY=         # مفتاح Polygon — التدفق اللحظي والصفقات
POLYGON_S3_KEY=          # مفتاح S3 للملفّات المجمَّعة (اختياري)
POLYGON_S3_SECRET=       # سرّ S3 (اختياري)
# مفاتيح تشغيل (toggles) — ليست أسرارًا:
SCREENER_MODE=           # DIGEST | BACKTEST | (فارغ = الفرز اليومي)
HUNTER_FORCE=            # 1 = تجاوز الدِدوب/البوابة (تشغيل يدوي)
# ... (بقية المتغيّرات من الخطوة 1)
```

**Verify**: `.env.example` lists every var from Step 1; contains no value that looks like a
real credential (`grep -nE ':[A-Za-z0-9_-]{20,}' .env.example` → nothing).

### Step 3: Add `.env` to `.gitignore`

Append to `.gitignore`:
```
# متغيّرات البيئة المحلية — لا تُلتزَم أبدًا (القالب .env.example فقط يُتابَع)
.env
!.env.example
```

**Verify**: `git check-ignore .env` → prints `.env`; `git check-ignore .env.example` →
prints nothing (still tracked).

### Step 4: Add a "Runner environment" table to README.md

Add a section documenting: each var, secret-vs-toggle, which runner/workflow consumes it,
and required-vs-optional. Keep it a compact Markdown table. Reference `.env.example` as the
canonical list. Note that secrets live in GitHub Secrets for CI and are never committed.

**Verify**: `python3 -c "print(open('README.md').read().count('TELEGRAM_BOT_TOKEN')>0)"` →
`True`; the table renders (eyeball the Markdown).

### Step 5: Confirm nothing broke

**Verify**: `python3 test_bot.py` → exit 0 (docs-only change).

## Test plan

- No `test_bot.py` tests (documentation). Verification is: `.env` is git-ignored,
  `.env.example` is tracked and value-free, README references the vars, suite still green.

## Done criteria

- [ ] `.env.example` exists, lists every env var found in Step 1, contains **no** values
- [ ] `.gitignore` ignores `.env` but keeps `.env.example` tracked (`git check-ignore` confirms)
- [ ] `README.md` has a runner-environment table mapping var → consumer → secret/toggle
- [ ] `python3 test_bot.py` exits 0
- [ ] No secret value anywhere in the diff
- [ ] `git status` shows only `.env.example`, `.gitignore`, `README.md`
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report if:
- The grep surfaces an env var whose purpose you cannot determine from source — list it in
  the README table as "purpose unclear — confirm with owner" rather than guessing.
- Any existing committed file already contains a real secret value (you'd notice while
  cross-checking) — report the location and type only; do not reproduce it.

## Maintenance notes

- When a new runner adds an env var, add it to `.env.example` and the README table in the
  same PR — otherwise this doc drifts (the very problem it solves).
- Keep `.env.example` values-free forever; it's a template, not a store.
