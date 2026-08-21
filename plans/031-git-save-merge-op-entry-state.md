# Plan 031: git_save must merge-by-key op_entry_state.json (two live runners clobber it)

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving on. If any STOP condition
> occurs, stop and report — do not improvise. When done, update this plan's status
> row in `plans/README.md` (unless a reviewer told you they maintain the index).
>
> **Drift check (run first)**: `git diff --stat 52ffe4f..HEAD -- Super_stock.py`
> `Super_stock.py` changes often. Locate `def git_save` and `def _union_jsonl` and compare the
> "Current state" excerpt below against the live code before proceeding; on a mismatch to the
> merge block, STOP.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: plan 030 recommended first (same file family; 030's fix is a strict subset)
- **Category**: bug
- **Planned at**: commit `52ffe4f` (origin/main), 2026-08-21

## Why this matters

`op_entry_state.json` is the per-day dedup for the "🎯 هنا الدخول" operator-entry alerts. **Two
independently-scheduled live runners write it**: `operator_entry_live.py` (a ~5.5h session worker,
git_saves every loop at lines 388/409/464) and `pullback_live.py` (every 30 min, git_saves it on
the success path at line 135). They run in **separate concurrency groups**, so they overlap during
market hours.

`git_save` resolves a rebase conflict by **union-merging only `.jsonl` files** (plan 027's fix);
every other file — including the JSON **dict** `op_entry_state.json` — is **last-writer-wins**
(`open(fn,"wb"); write(local_blob)`). So when `pullback_live` pushes, it overwrites origin's
`op_entry_state.json` with the copy it loaded from its own (stale) checkout plus a few new rows —
**erasing every per-symbol dedup stamp `operator_entry_live` wrote in the overlap window**.

Effect: those symbols lose their per-day stamp, so the next time either runner sees them it
re-fires `🎯 هنا الدخول` / `💰 سيولة الشمعة` for them = **duplicate owner notifications** (the exact
noise CLAUDE.md repeatedly records the owner hating). It partially self-heals — `operator_entry_live`
re-reads `seen` from FETCH_HEAD each loop (`_load_universe`, line 277), so it picks up the clobbered
state rather than recovering the lost stamps — but the clobber still costs a duplicate-alert window,
and can reset the M5/M30 liquidity-stage progression for a symbol mid-sequence.

The fix mirrors the repo's own `.jsonl` precedent: treat `op_entry_state.json` in `git_save` as a
**merge-by-key** (per symbol, keep the newer stamp) instead of a blind overwrite.

## Current state

- `Super_stock.py` — `git_save` (currently at line 21303) and the pure helper `_union_jsonl`
  (line 21274). `OP_ENTRY_STATE_FILE` is a module constant in `Super_stock.py` (find with
  `grep -n 'OP_ENTRY_STATE_FILE =' Super_stock.py`).

`Super_stock.py:21356-21374` (the conflict-resolution loop — `.jsonl` merges, everything else is
last-writer-wins):
```python
                    for fn, _b in _blobs.items():
                        # ... (plan 027 comment: .jsonl merged as a union) ...
                        if str(fn).endswith(".jsonl") and os.path.exists(fn):
                            try:
                                with open(fn, "rb") as f:
                                    _remote = f.read()
                                _b = _union_jsonl(_remote, _b)
                                log(f"🌱 اتّحادُ سجلٍّ مُلحَق: {fn}")
                            except Exception as _ue:             # noqa: BLE001
                                log(f"⚠️ تعذّر اتّحاد {fn} ({_ue}) — أُبقيت نسختُنا")
                        with open(fn, "wb") as f:                # ← op_entry_state.json: local overwrites remote
                            f.write(_b)
                        run(f'git add "{fn}"')
```

`_union_jsonl` (line 21274) is the pure, fail-safe pattern to mirror — on any error it returns the
local bytes (behaviour-identical to today), so the fix can never become a new failure vector.

The dict shape to merge (from `save_op_entry_state`/`load_op_entry_state`): a top-level
`{symbol: entry}` dict where each `entry` is itself a dict carrying at least `date` (the trading
day, ISO string) and `sent` (a list of stage names already sent). The merge rule that preserves the
"don't lose a sent stamp" invariant (confirmed by how `operator_entry_live._stamps_covered` at
`operator_entry_live.py:167-201` reasons about it):
- For each symbol present in either side: if one side's `date` is **newer**, keep that side's entry
  whole (a newer day resets `sent` intentionally).
- If both sides have the **same** `date`: keep the entry whose `sent` is the **union** (superset) of
  both — i.e. never drop a `sent` stamp that either side recorded.
- Symbols present on only one side: keep them.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests   | `python3 test_bot.py` | exit 0, last line `✅✅ كل الاختبارات نجحت — الضمان الذهبي` |
| Find the constant | `grep -n "OP_ENTRY_STATE_FILE =" Super_stock.py` | its definition |
| Find existing git_save/union tests | `grep -n "_union_jsonl\|git_save" test_bot.py` | the tests to model after |
| Scope check | `git status --porcelain` | only `Super_stock.py`, `test_bot.py` |

(Offline suite. Use `python3.11` if `python3` is 3.9.)

## Scope

**In scope**:
- `Super_stock.py`: add one pure helper `_merge_op_entry(remote_bytes, local_bytes) -> bytes`
  next to `_union_jsonl`, and add a branch in the `git_save` conflict loop that calls it for
  `OP_ENTRY_STATE_FILE` (analogous to the `.jsonl` branch). Nothing else in `git_save` changes.
- `test_bot.py` (add tests).

**Out of scope** (do NOT touch):
- The `.jsonl` union branch, the last-writer-wins path for **other** dict state files
  (`weekly_watchlist.json`, `near_watch.json`, `press_radar_state.json`, etc. — those have a
  single writer or are handled elsewhere; do NOT generalize the merge to them), `operator_entry_live.py`,
  `pullback_live.py`, or any screening root.
- No `LOGIC_VERSION` bump — this is state-persistence plumbing, not selection logic.

## Git workflow

- Branch: `advisor/031-git-save-merge-op-entry`
- Commit trailer (exactly): `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Add the pure merge helper

Next to `_union_jsonl` (around `Super_stock.py:21300`), add `_merge_op_entry(remote_bytes,
local_bytes) -> bytes` implementing the three-rule merge above. Make it **fail-safe like
`_union_jsonl`**: wrap the whole body in `try/except` and on any error `return local_bytes` (the
current last-writer-wins behaviour), so a corrupt/unexpected shape can never make the fix worse
than today. Parse both sides with `json.loads`; if either is not a dict, return `local_bytes`.
Emit the merged dict with `json.dumps(..., ensure_ascii=False)` encoded to bytes (match how
`save_op_entry_state` writes the file — check it so the on-disk format is unchanged; if it uses
`indent`, match it).

### Step 2: Branch git_save's conflict loop to use it for op_entry_state.json

In the conflict loop (line ~21365), add — parallel to the `.jsonl` branch, **before** the
`with open(fn, "wb")` write — a branch: if `str(fn) == OP_ENTRY_STATE_FILE and os.path.exists(fn)`,
read the remote blob (`_remote = open(fn,"rb").read()` — at this point in the loop `fn` on disk is
the remote copy after `reset --hard FETCH_HEAD`, and `_b` is our local blob captured before the
reset — verify this matches how the `.jsonl` branch reads `_remote`), then `_b = _merge_op_entry(_remote, _b)`
inside its own `try/except` that logs and falls back to keeping our blob, mirroring the `.jsonl`
branch exactly. The `with open(fn,"wb"); f.write(_b); git add` that follows is unchanged.

**Verify**: read the code — for a `.jsonl` file the behaviour is byte-identical to before (the new
branch's `==` guard doesn't match); for other dict files the behaviour is byte-identical (last-writer-wins);
only `OP_ENTRY_STATE_FILE` now merges.

### Step 3: Run the suite

**Verify**: `python3 test_bot.py` → exit 0 (existing `git_save`/`_union_jsonl` tests still pass — the
non-op-entry paths are untouched).

### Step 4: Add tests

Model after the existing `_union_jsonl` test (`grep -n "_union_jsonl" test_bot.py`). Add, using
`check(...)`:
1. **Merge keeps both stamps**: `remote = {"AAA": {"date":"2026-08-21","sent":["M1","M5"]}}`,
   `local = {"AAA": {"date":"2026-08-21","sent":["M1"]}, "BBB": {"date":"2026-08-21","sent":["M1"]}}`.
   Assert the merged dict has `AAA.sent == {"M1","M5"}` (as a set) and `BBB` present — i.e. neither
   `M5` (remote-only) nor `BBB` (local-only) is lost.
2. **Newer day wins whole**: `remote = {"AAA": {"date":"2026-08-22","sent":[]}}`,
   `local = {"AAA": {"date":"2026-08-21","sent":["M1","M5"]}}` → merged `AAA.date == "2026-08-22"`
   and `AAA.sent == []` (the newer day correctly resets).
3. **Fail-safe**: pass garbage bytes (`b"not json"`) as remote → returns `local_bytes` unchanged.
4. **Clobber regression at the git_save layer**: using the injected `runner`/`sender` that
   `git_save` already accepts, simulate a rebase conflict where the remote `op_entry_state.json`
   has a stamp our local copy lacks, and assert the file written back contains **both** stamps
   (i.e. the union survived the "conflict"). Model the git-mock after the existing `git_save`
   conflict test if one exists; if not, at minimum unit-test `_merge_op_entry` (cases 1–3) and add
   one behavioral assertion that `git_save` routes `OP_ENTRY_STATE_FILE` through the merge (e.g. a
   source/AST assertion that the merge branch names `OP_ENTRY_STATE_FILE`), and note the limitation.

**Verify**: `python3 test_bot.py` → exit 0; new `✅` lines print.

### Step 5: Mutation check

Temporarily change the git_save branch guard so it never matches `OP_ENTRY_STATE_FILE` (e.g.
compare to a nonexistent name). Run `python3 test_bot.py` and confirm case 4 (the clobber
regression / routing assertion) **fails**. Restore.

**Verify**: with the mutation, exit 1; after restore, exit 0.

## Test plan

- Unit tests for `_merge_op_entry` (union, newer-day, fail-safe) + a git_save-layer test proving
  `OP_ENTRY_STATE_FILE` is routed through the merge, plus a mutation round. All offline (inject
  `runner`/`sender`; no real git).

## Done criteria

- [ ] `python3 test_bot.py` exits 0; new tests present and passing
- [ ] `_merge_op_entry` is pure and fail-safe (garbage → returns `local_bytes`)
- [ ] git_save merges only `OP_ENTRY_STATE_FILE`; `.jsonl` union and all other files byte-identical
- [ ] On-disk format of `op_entry_state.json` unchanged (matches `save_op_entry_state`)
- [ ] Mutation check passed
- [ ] `git status --porcelain` shows only `Super_stock.py`, `test_bot.py`
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report if:
- The `op_entry_state.json` entry shape is **not** `{symbol: {date, sent, ...}}` when you read
  `save_op_entry_state`/`load_op_entry_state` — report the actual shape; the merge rule depends on it.
- `git_save`'s conflict loop no longer captures local blobs before `reset --hard` (structure changed)
  — report; the merge needs the remote-vs-local pair the `.jsonl` branch relies on.
- Merging would require `git_save` to know about a second dict file — do NOT generalize; report and
  keep the scope to `OP_ENTRY_STATE_FILE` only.

## Maintenance notes

- This is deliberately **scoped to one file**. Other dict state files stay last-writer-wins because
  they have a single writer or their multi-writer risk hasn't been measured. If another dict file
  gains a second concurrent writer, revisit — but with its own plan and its own merge rule.
- Reviewer should confirm the `.jsonl` path and every non-op-entry write are byte-identical (diff the
  loop), and that `_merge_op_entry`'s fail-safe returns `local_bytes` on any parse error (so the fix
  can never lose data relative to today).
- Related: plan 030 (the pullback failed-send restore). Together they close the op-entry dedup
  durability gap — 030 stops a lost-alert-on-reject, 031 stops the cross-runner clobber.
