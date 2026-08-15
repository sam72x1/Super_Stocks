# Plan 027: Stop concurrent hunters from silently clobbering the shared ledger, and stop the O(n) re-parse on every append

> **Executor instructions**: Follow this plan step by step. This touches the shared
> `git_save` path (used by many runners) and the ledger append path — treat both as
> high-blast-radius. Build/rely on tests before changing behavior. If a STOP condition
> occurs, stop and report. When done, update this plan's status row in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4e9b143..HEAD -- Super_stock.py hunter_ledger.py split_hunter.py split_filter_hunter.py method_hunter.py envelope_hunter.py`
> If any changed, re-read the excerpts before editing; on a mismatch, STOP.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED — `git_save` is the shared persistence path for every runner; a concurrency
  fix must not break single-writer saves.
- **Depends on**: plan 023 (characterization tests for `hunter_ledger` give the safety net) — strongly recommended first.
- **Category**: bug / tech-debt
- **Planned at**: commit `4e9b143`, 2026-08-15

## Why this matters

Four nightly hunters append to the **same** `hunter_ledger.jsonl` (258 KB live) and then
push it via `git_save`. Two problems:

1. **Silent clobber (BUG-03)**: `git_save`'s rebase-conflict branch resets to the remote
   (`git reset --hard FETCH_HEAD`) then overwrites with the local file blob — last-writer-wins.
   That is correct for a **single-writer** file, but the ledger has **four writers** on a
   tight cron stagger (envelope :09, split :13, method :37, split_filter :51) while each job
   runs a multi-minute full-universe scan. If job B checks out `main` before job A's push
   lands, B appends onto the pre-A ledger, hits a conflict, resets to A's remote version, and
   **overwrites it with B's local file — A's freshly-recorded rows are lost, silently**
   (`git_save` reports success). The ledger is the "forward-proof" memory `hunter_outcomes`
   scores from, so lost rows quietly shrink the dataset the whole harvest depends on.
2. **O(n) re-parse (STATE-04)**: `hunter_ledger.record()` calls `load(path)` — reading and
   `json.loads`-ing **every** line — purely to build a dedup key-set before appending a
   handful of rows. The `MAX_ROWS=20000` cap is enforced **only** in `apply_outcomes`, never
   on append, so the file grows to 20k rows and every append + every daily-report summary
   fully re-parses it.

## Current state

`Super_stock.py:18320-18334` (git_save conflict branch — blind overwrite = last-writer-wins):
```python
            if run("git rebase FETCH_HEAD >/dev/null 2>&1") != 0:
                run("git rebase --abort >/dev/null 2>&1")
                # ⑬ حل التعارض فعليًا: اعتمد الريموت ثم أعد ملفاتنا فوقه.
                try:
                    _blobs = {}
                    for fn in filenames:
                        if os.path.exists(fn):
                            with open(fn, "rb") as f:
                                _blobs[fn] = f.read()
                    run("git reset --hard FETCH_HEAD >/dev/null 2>&1")
                    for fn, _b in _blobs.items():
                        with open(fn, "wb") as f:
                            f.write(_b)          # ← clobbers remote's version of an append-only file
                        run(f'git add "{fn}"')
                    run(f'git commit -m "{_msg}"')
```

`hunter_ledger.py:120-133` (record — full `load()` per append for dedup):
```python
def record(hunter, session, rows, ref_of=None, kind="candidate", path=None, log=None) -> int:
    path = path or LEDGER_FILE
    try:
        new = build_rows(hunter, session, rows, ref_of=ref_of, kind=kind)
        if not new:
            return 0
        have = {r.get("key") for r in load(path)}   # ← reads & parses the whole 258KB file
        fresh = [r for r in new if r["key"] not in have]
        ...
        with open(path, "a", encoding="utf-8") as fh:
            for r in fresh:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
```
`hunter_ledger.py:31` `MAX_ROWS = 20000`; the cap is applied only in `apply_outcomes`
(`:181-184`). The four hunters push the ledger: `split_hunter.py:101`,
`split_filter_hunter.py:86`, `method_hunter.py:82`, `envelope_hunter.py:68` (each
`git_save([..., LEDGER.LEDGER_FILE])`).

**Idempotency contract (`H2`)**: no duplicate `(hunter, session, symbol)` across the two
same-day crons — this is test-locked and must survive any dedup shortcut.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests | `python3 test_bot.py` | exit 0 |
| Find git_save test hooks | `grep -n "git_save\|runner=\|SUPER_STOCKS_TESTING" Super_stock.py test_bot.py \| head` | how the suite drives git_save offline |
| Ledger key format | `sed -n '1,40p' hunter_ledger.py` | `_key(hunter, session, sym)` shape |

## Scope

**In scope**:
- `Super_stock.py` — `git_save`'s conflict branch: for **append-only JSONL** files, union-merge
  local-only lines onto the remote instead of clobbering.
- `hunter_ledger.py` — `record`'s dedup: avoid a full `load()` where possible.
- `test_bot.py` — concurrency-merge test + dedup test.

**Out of scope**:
- The scoring logic (`hunter_outcomes`, `LEDGER.score/summary`) — do not change verdicts.
- `git_save`'s single-writer behavior for non-JSONL files (weekly_watchlist.json,
  alerts_history.json) — those are genuinely single-writer; last-writer-wins is correct for
  them. Only the append-only JSONL case changes.
- Any screening/root logic. No `LOGIC_VERSION`.

## Git workflow

- Branch: `advisor/027-hunter-ledger-concurrency`
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Make `git_save`'s conflict branch union-merge append-only JSONL

In the conflict branch, for any filename ending `.jsonl` (or an explicit allowlist of the
append-only ledgers), instead of overwriting the remote with the local blob:
1. After `git reset --hard FETCH_HEAD`, read the **remote** version of the file (now on disk).
2. Read the **local** lines you captured before the reset.
3. Write the union: remote lines + local lines whose dedup key (`json.loads(line)["key"]`)
   isn't already present in the remote. Preserve order (remote first, then new local-only).
For non-JSONL files, keep the existing overwrite (single-writer, correct).

This makes a concurrent hunter's rows survive: B's append merges onto A's remote instead of
replacing it. Keep it fail-safe — if a line doesn't parse, fall back to the current overwrite
for that file and log it (never lose the local data).

**Verify**: a unit test (Step 3) drives the conflict branch with a fake `runner` and two
divergent JSONL versions and asserts the union.

### Step 2: Bound the ledger dedup read (STATE-04)

Since duplicates only arise between the **two same-day crons** (contract `H2`), `record()`'s
dedup only needs to check rows from the **current session**, not all 20k. Change the dedup
to scan only the tail / current-session rows:
- Option A (minimal): keep `load()` but only build the key-set from rows whose `session`
  equals the session being recorded (still reads the file, but this is a correctness-neutral
  scoping — the O(n) read remains; prefer Option B if the read cost matters).
- Option B (better): read the file **backwards** and stop once you pass rows older than the
  current session (JSONL is append-ordered by time), building the key-set from just the tail.
Choose based on effort; Option B removes the O(n) read. Either way, `H2` (no same-session
duplicate) must still hold.

Optionally also enforce `MAX_ROWS` on append (not just in `apply_outcomes`) if the file is
observed to exceed it — but only with an explicit, logged trim (the repo's rule: "cap is
announced, never silent"). This is optional; the clobber fix (Step 1) is the priority.

**Verify**: the existing `H2` dedup lock still passes; a new test confirms two same-session
`record()` calls produce no duplicate.

### Step 3: Tests

- **Concurrency merge**: build two divergent JSONL contents (A has row a1, B has row b1, both
  share an older row), drive `git_save`'s conflict path with an injected `runner` (see the
  `SUPER_STOCKS_TESTING`/`runner=` hook at `Super_stock.py:18300`), and assert the merged
  file contains a1, b1, and the shared row **once** — not a1 lost.
- **Dedup scoping**: `record()` twice for the same `(hunter, session)` → no duplicate; for a
  *different* session with a same symbol → both kept (H2 boundary).

Use temp paths; never touch the real ledger. Add a mutation round for each (revert to the
clobber / revert the dedup scoping and confirm the tests fail).

**Verify**: `python3 test_bot.py` → exit 0; new `✅` lines print; mutations fail as expected.

## Test plan

- Concurrency-merge test + dedup-scoping test, each with a mutation round. All offline, temp
  paths, injected `runner`. Reuse the git_save test scaffolding already in `test_bot.py`
  (grep `git_save`).

## Done criteria

- [ ] `python3 test_bot.py` exits 0; existing `H2`/git_save locks still pass; new tests present
- [ ] `git_save`'s conflict branch union-merges append-only JSONL (a concurrent writer's rows survive)
- [ ] Non-JSONL single-writer files still use the existing overwrite (unchanged)
- [ ] `record()` dedup no longer requires the guarantee that only same-session dups matter is violated (H2 preserved), and (Option B) avoids the full re-parse
- [ ] Mutation rounds pass (clobber / dedup-scoping tests fall when broken)
- [ ] `git status` shows only `Super_stock.py`, `hunter_ledger.py`, `test_bot.py`
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report if:
- The union-merge would change behavior for a **single-writer** file (weekly_watchlist.json,
  alerts_history.json) — it must not; scope the JSONL-merge strictly and report if the
  filename detection is ambiguous.
- You cannot drive `git_save`'s conflict branch offline with the existing test hook — report
  the harness limitation rather than testing against real git.
- Backwards-reading the JSONL (Option B) risks missing a same-session dup that appears out of
  order — if append order isn't guaranteed monotonic by session, fall back to Option A and
  report.

## Maintenance notes

- This is the concrete core of the broader "make the hunter forward-harvest reliable"
  direction (D1 in the audit). A fuller version would give each hunter its own ledger shard
  that `hunter_outcomes` unions — which sidesteps the shared-file conflict entirely. Consider
  that if more hunters are added; this plan is the minimal, in-place fix.
- Reviewer must confirm the single-writer path is untouched — that's where a regression would
  hide.
- The forward-harvest ledger is the only positive-evidence loop the methodology cites
  ("الصيّاد التقط NUWE قبل انفجاره"); silently losing its rows undermines that claim, so this
  fix protects a load-bearing measurement.
