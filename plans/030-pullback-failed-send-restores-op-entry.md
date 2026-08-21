# Plan 030: pullback_live must re-push op-entry dedup on a failed send (so "هنا الدخول" retries)

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving on. If any STOP condition
> occurs, stop and report — do not improvise. When done, update this plan's status
> row in `plans/README.md` (unless a reviewer told you they maintain the index).
>
> **Drift check (run first)**: `git diff --stat 52ffe4f..HEAD -- pullback_live.py`
> If it changed since this plan was written, compare the "Current state" excerpt below
> against the live code before proceeding; on a mismatch, STOP.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none (but touches the same file family as plan 031 — see that plan)
- **Category**: bug
- **Planned at**: commit `52ffe4f` (origin/main), 2026-08-21

## Why this matters

`pullback_live.py` runs every ~30 min during/around market hours and sends the owner the
"🎯 هنا الدخول" (operator-entry) alerts. To avoid re-sending the same alert, it stamps a
per-day dedup file `op_entry_state.json` **before** sending (a deliberate trade-off:
stamp-before-send prevents duplicates, and on a send failure the stamps are *restored* so
the next cycle retries). This restore-on-failure contract is the same one the repo fixed
for the watchlist stamps on 2026-07-27 ("a stop-break alert consumed on a message that
never arrived, and the job stays green").

The bug: on a Telegram send failure, the code correctly (a) restores the watchlist stamps
and (b) pops the op-entry symbols from `_op_seen` and re-saves `op_entry_state.json`
locally — **but the failure-branch `git_save` pushes `[bot.WATCH_FILE]` only, omitting
`OP_ENTRY_STATE_FILE`**. So the watchlist restore reaches origin, but the op-entry restore
stays on the dying runner's local disk. origin/main keeps the *stamped* `op_entry_state.json`
from the pre-send push, the next run (fresh checkout) loads it and skips those symbols, and
**the operator-entry alert that failed to send is silently never retried for the rest of the
day** (dedup is per-day). This is the exact asymmetry: `WATCH_FILE` is re-pushed on failure,
`OP_ENTRY_STATE_FILE` is not.

## Current state

- `pullback_live.py` — the 30-min live monitor. The success path already pushes op-entry
  state; the failure branch does not.

`pullback_live.py:130-166` (the success push includes op-entry at line 135; the failure
branch at line 163 omits it):
```python
    _op_files = []
    if _op_rows and _op_seen is not None:
        if bot.save_op_entry_state(_op_seen):
            _op_files = [bot.OP_ENTRY_STATE_FILE]
    try:
        bot.git_save([bot.WATCH_FILE] + _op_files)          # ← success path: op-entry INCLUDED
    except Exception as e:
        bot.log(f"⚠️ حفظ الحالة: {e}")
    # ... (send loop; `failed` counts rejects) ...
    if failed:
        bot.log(...)
        _stamp_restore(wl, snap)
        # 🎯 والدِدوبُ الجديد يُنزَع فتُعاد محاولةُ «هنا الدخول» أيضًا — وإلّا
        #    استُهلك ختمُ السهم على رسالةٍ لم تصل (عينُ عيب 2026-07-27).
        if _op_rows and _op_seen is not None:
            for _r, _v, _o in _op_rows:
                _op_seen.pop(_r.get("symbol"), None)
            bot.save_op_entry_state(_op_seen)               # ← restore saved LOCALLY only
        bot.save_watchlist(wl)
        try:
            bot.git_save([bot.WATCH_FILE])                  # ← BUG: omits _op_files
        except Exception as e:                              # noqa: BLE001
            bot.log(f"⚠️ استرجاع الأختام: {e}")
        return 1
    return 0
```

The comment at the restore block explicitly states the intent ("the new dedup is removed so
'هنا الدخول' is retried too") — the code does the local restore but never pushes it. `_op_files`
is already computed above (line 130-133) and still holds `[bot.OP_ENTRY_STATE_FILE]` (or `[]`
if there were no op rows / the earlier save failed), so the fix reuses it.

**Repo conventions**: Arabic comments; `bot.log` for output; the runner returns `1` on a
failed send so the next 30-min cron retries, `0` on success. Match the existing style.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests   | `python3 test_bot.py` | exit 0, last line `✅✅ كل الاختبارات نجحت — الضمان الذهبي` |
| Scope check | `git status --porcelain` | only `pullback_live.py`, `test_bot.py` |
| Confirm the fix location | `grep -n "git_save(\[bot.WATCH_FILE\])" pullback_live.py` | the single failure-branch line |

(No install step — the suite runs fully offline. If `python3` is 3.9, use `python3.11`; the
suite needs 3.10+ for `sys.stdlib_module_names`.)

## Scope

**In scope**:
- `pullback_live.py` — the one failure-branch `git_save` call.
- `test_bot.py` (add a test).

**Out of scope** (do NOT touch):
- The success-path push (line 135) — already correct.
- The stamp-before-send trade-off, `_stamp_restore`, `scan_operator_entry`, or any screening
  root. This is a display/notification-path fix — **no `LOGIC_VERSION` bump**.
- `operator_entry_live.py` and `git_save`'s merge logic — those are plan 031's territory; do
  not change them here.

## Git workflow

- Branch: `advisor/030-pullback-failed-send-op-entry`
- Commit trailer (exactly): `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Add `_op_files` to the failure-branch git_save

Change the failure-branch call from `bot.git_save([bot.WATCH_FILE])` to
`bot.git_save([bot.WATCH_FILE] + _op_files)` (mirroring the success path at line 135).
`_op_files` is already in scope from line 130-133; when there were no op rows it is `[]`, so
the call degrades to exactly the current behavior. Keep the surrounding `try/except` and the
`return 1` unchanged.

**Verify**: read the code — the failure branch now pushes `[bot.WATCH_FILE] + _op_files`, and
`_op_files` is the same variable set before the send loop. `grep -n "git_save(\[bot.WATCH_FILE\] + _op_files)" pullback_live.py` returns **two** lines (success + failure).

### Step 2: Run the suite

**Verify**: `python3 test_bot.py` → exit 0 (no regression).

### Step 3: Add a test

Find how the suite exercises `pullback_live` (`grep -n "pullback_live\|import pullback_live\|_op_files\|save_op_entry_state" test_bot.py`). Using the existing `check(name, cond, extra="")` helper (defined at `test_bot.py:99`), add a test that:
1. Injects a `git_save` spy (a fake that records the `filenames` list it was called with — the
   real `git_save` already accepts a `runner`/`sender` for testing, but `pullback_live` calls
   `bot.git_save(...)` directly, so the cleanest approach is to monkeypatch `bot.git_save` to a
   recorder for the duration of the test), a `send_telegram` that returns falsy (simulating a
   reject), a non-empty `_op_rows`/`_op_seen`, and a fresh watchlist.
2. Drives the failure branch (send fails → `failed > 0`) and asserts the **last** recorded
   `git_save` call's filename list **contains `OP_ENTRY_STATE_FILE`** (i.e. the restored
   op-entry state is re-pushed), and that the runner returned `1`.

If wiring a full `main()` call is impractical, assert at the structural level instead: read
`pullback_live` source and assert the failure-branch `git_save` includes `_op_files` (a
behavioral lock is preferred, but a source assertion that the two `git_save` calls have the
same filename shape is acceptable if you document why). Model the injection after any existing
`pullback_live` test you found.

**Verify**: `python3 test_bot.py` → exit 0; your new `✅` line prints.

### Step 4: Mutation check (prove the test can fail)

Temporarily revert Step 1 (put back `bot.git_save([bot.WATCH_FILE])`), run `python3 test_bot.py`,
and confirm your new test **fails** (`❌`, exit 1). Restore the fix. Per repo doctrine: "a lock
that never falls is not a lock."

**Verify**: with the mutation, exit 1; after restore, exit 0.

## Test plan

- One new `check(...)` case proving the failure branch re-pushes `OP_ENTRY_STATE_FILE`, plus a
  mutation round proving it's real. Never touch the network (inject `git_save`/`send_telegram`).

## Done criteria

- [ ] `python3 test_bot.py` exits 0; new test present and passing
- [ ] Failure branch calls `git_save([bot.WATCH_FILE] + _op_files)`; success branch unchanged
- [ ] Mutation check passed (test falls when the fix is reverted)
- [ ] `git status --porcelain` shows only `pullback_live.py`, `test_bot.py`
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report if:
- `_op_files` is not in scope at the failure branch (e.g. the code was restructured so it's
  computed inside the `try`) — report the actual structure; do not recompute it blindly.
- The failure branch already includes `_op_files` (drift fixed it independently) — mark
  REJECTED "fixed independently" and report.
- Adding the test requires importing modules that hit the network — report; all fetchers/senders
  must be injectable.

## Maintenance notes

- The invariant: **every `git_save` in a failure/restore branch must include every state file
  the success branch pushed.** If a future change adds another per-day dedup file to the success
  push, it must also join the failure-branch push.
- Reviewer should confirm the fix reuses the existing `_op_files` (no second `save_op_entry_state`
  path introduced) and that the `return 1` still fires so the next cron retries.
