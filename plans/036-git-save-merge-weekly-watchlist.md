# Plan 036: `git_save` must key-merge `weekly_watchlist.json` on a rebase conflict (a concurrent cron must not clobber the watchlist)

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving on. If any STOP condition
> occurs, stop and report — do not improvise. This plan is **MED risk**: a wrong
> merge can silently lose new watchlist candidates or resurrect a stopped stock
> (re-notifying the owner about a dead position). Honor every STOP condition.
> When done, update this plan's status row in `plans/README.md` (unless a reviewer
> told you they maintain the index).
>
> **Drift check (run first)**:
> `git diff --stat 5cb88df..HEAD -- Super_stock.py`
> Written against `origin/main` (`5cb88df`). Locate `def git_save` and
> `def _union_jsonl` in `Super_stock.py`. If `git rev-parse --short HEAD` is not
> `5cb88df` or a descendant, or `_union_jsonl` does not exist, **STOP** — you are
> on the wrong tree (the operator must update to `origin/main`). If the conflict-
> resolution block inside `git_save` (the `if run("git rebase FETCH_HEAD…") != 0`
> branch) differs from the "Current state" excerpt, STOP.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: plan 031 recommended first (both edit the same `git_save`
  conflict block; 031 introduces dict-state merge for `op_entry_state.json`, this
  extends the same path to `weekly_watchlist.json`). If 031 has not landed, this
  plan adds its own merge branch and 031 should later reuse it.
- **Category**: bug
- **Planned at**: commit `5cb88df` (origin/main), 2026-08-21

## Why this matters

`git_save` (the helper that commits+pushes bot state) resolves a push race by:
rebase → on conflict, `git reset --hard FETCH_HEAD`, then overwrite each of *its
own* files from an in-memory snapshot and re-commit ("last-writer-wins for our
files"). Plan 027 made **`.jsonl`** ledgers union-merge; **every dict-JSON state
file is still blind-overwritten**, including `weekly_watchlist.json` — the core
watchlist (`WATCH_FILE`).

`weekly_watchlist.json` has multiple independently-scheduled writers:
`pullback_live.py:135` git_saves it every ~30 min (13–23 UTC), and the daily/
renewal path (`run_weekly_renewal`, the Friday ~22:07 UTC cron) also writes it.
Those windows overlap on Fridays. When a `pullback_monitor` run pushes during the
Friday renewal, `git_save` on a rebase conflict overwrites origin's
`weekly_watchlist.json` — which the renewal just rewrote with new candidates, the
fate report, `week_start`, `explosions`, `reject_stats` — with the pullback job's
older loaded copy plus its few field updates, **and logs "✅ حُفظت"**. The
renewal's new membership is silently lost. (`pullback_live` also co-writes
`op_entry_state.json`; that dict is plan 030/031's domain — do **not** re-handle
it here.)

The fix: give `weekly_watchlist.json` a **removal-log-aware key merge** in the
conflict path, so it is reconciled against the freshly-reset remote copy instead of
blind-overwritten. The design must (a) never lose a symbol either side added
(union membership), (b) never resurrect a symbol present in the merged `removed`
log — the repo's rule is "تُشطب بالستوب فقط" (removed only by stop), so resurrecting
a stopped stock is a real harm, and (c) union the append-only lists without
duplicates. This is data-plumbing only — no `LOGIC_VERSION`, no selection change.

**Why not "newer wins" per entry**: watch entries key on `"symbol"` but carry no
per-entry `updated_at` timestamp (only `"added"`, the nomination date). So a
same-symbol field conflict cannot be resolved by timestamp. The design below
accepts a small, bounded residual (on the rare same-symbol concurrent field edit,
the local copy's fields win) in exchange for eliminating the two real harms
(membership loss and stopped-stock resurrection). This tradeoff is deliberate and
documented; do not try to invent a timestamp.

## Current state

`Super_stock.py` at `5cb88df`. The conflict-resolution block inside `git_save`
(≈ line 21344), showing that only `.jsonl` is merged and everything else is
blind-overwritten:

```python
                    run("git reset --hard FETCH_HEAD >/dev/null 2>&1")
                    for fn, _b in _blobs.items():
                        # 🌱 خطة 027 … سجلّاتُ `.jsonl` تُدمَج **اتّحادًا** …
                        if str(fn).endswith(".jsonl") and os.path.exists(fn):
                            try:
                                with open(fn, "rb") as f:
                                    _remote = f.read()
                                _b = _union_jsonl(_remote, _b)
                                log(f"🌱 اتّحادُ سجلٍّ مُلحَق: {fn}")
                            except Exception as _ue:
                                log(f"⚠️ تعذّر اتّحاد {fn} ({_ue}) — أُبقيت نسختُنا")
                        with open(fn, "wb") as f:
                            f.write(_b)
                        run(f'git add "{fn}"')
```
Here `_blobs[fn]` is our in-memory copy (loaded before our edits + our edits); after
`git reset --hard FETCH_HEAD`, the file on disk (if it exists) is the **remote**
copy. `_union_jsonl` reads that remote copy and unions it with `_b`. **You will add
a parallel branch for `weekly_watchlist.json`** that does the same read-remote-then-
merge, but with dict semantics.

`_union_jsonl` (≈ line 21274) is the reference for the shape (read remote file,
merge with local blob, return merged bytes, fail-safe to local on error).

Watch-entry / top-level structure (verified via `make_watch_entry` and `wl[...]`
usage): top-level dict with keys `stocks` (list of dicts, each with `"symbol"`),
`pullback` (list of dicts with `"symbol"`), `removed` (append list), `history`,
`explosions`, `replacements_log`/`notes` (append lists, if present),
`week_start`, `reject_stats`, `tie_harvest`, `added_last`, `pruned`,
`logic_version`. `WATCH_FILE` names the file (find with
`grep -n "WATCH_FILE" Super_stock.py`; it resolves to `weekly_watchlist.json`).

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Test suite (gate) | `python3 test_bot.py; echo "rc=$?"` | `rc=0`, zero failures |
| Locate helpers | `grep -n "def git_save\|def _union_jsonl\|WATCH_FILE =" Super_stock.py` | three lines |
| Inspect `removed` shape | `grep -n '"removed"' Super_stock.py \| head` + read the write sites | list of str symbols or list of dicts with `"symbol"` |

The suite runs with no internet. Your merge helper must be a **pure function**
(bytes/dict in, bytes/dict out) so it can be locked without git or network.

## Suggested executor toolkit

- Load **`lock-and-mutate`**: the merge's three guarantees (no membership loss, no
  resurrection, dedup) each need a mutation-failing test. A structural "the branch
  exists" check is not enough.

## Scope

**In scope**:
- `Super_stock.py` — add `_merge_watchlist(remote_bytes, local_bytes) -> bytes`
  (pure) and route `weekly_watchlist.json` through it in the `git_save` conflict
  block (alongside the existing `.jsonl` branch).
- `test_bot.py` — lock tests for `_merge_watchlist`.

**Out of scope** (do NOT touch):
- `op_entry_state.json` handling — plan 030/031. If 031's dict-merge entry point
  exists, extend it; do not duplicate it. If it doesn't, add a sibling branch.
- `_union_jsonl` and the `.jsonl` path — unchanged.
- `pullback_live.py`, `run_weekly_renewal`, `save_watchlist`, `make_watch_entry`,
  any selection/membership logic. This plan changes only how a conflict is
  reconciled, not what gets written.
- `LOGIC_VERSION` — must NOT change.

## Git workflow

- Branch: `advisor/036-git-save-watchlist-merge`.
- Commit message ends with the repo's two trailer lines. Do NOT push/PR unless
  instructed.

## Steps

### Step 1: Investigate structure and confirm safe merge is possible (STOP gate)

Before writing any merge, confirm from the code:
1. `WATCH_FILE` resolves to `weekly_watchlist.json` (`grep`).
2. The element shape of `wl["removed"]`: read its write sites (e.g. in
   `run_daily_watchlist`/`run_weekly_renewal` where entries are appended). Record
   whether elements are plain symbol strings or dicts carrying `"symbol"`.
3. That there is **no** per-entry monotonic timestamp on `stocks` entries (only
   `"added"`). Confirm this — if a reliable `updated`/`last_update` field actually
   exists, prefer it for same-symbol conflict resolution and note the change.

**STOP** and report if: `removed` is not a symbol-bearing list you can read
symbols from (you cannot safely prevent resurrection), or the top-level structure
is not the dict described in "Current state". A blind union without a working
removal filter is **not acceptable** — report back rather than risk resurrecting a
stopped stock.

**Verify**: your report names the `removed` element shape and the symbol key.

### Step 2: Write the pure merge helper

Add `_merge_watchlist(remote_bytes, local_bytes) -> bytes` near `_union_jsonl`:

- Parse both blobs as dict; on any parse error, **return `local_bytes`** (fail-safe
  to current behavior — never worse than today). Log via the caller.
- **Membership union with removal-prune**:
  - Build `removed_syms` = the set of symbols from `remote["removed"]` ∪
    `local["removed"]` (extract per the Step-1 element shape).
  - For each keyed collection in `("stocks", "pullback")`: union entries by
    `"symbol"`. For a symbol present in both, keep the **local** entry (bounded
    residual — see Why). Then **drop** any entry whose symbol is in `removed_syms`.
  - Result: no symbol either side added is lost; no symbol in `removed` survives.
- **Append-only lists** `("removed", "history", "explosions", "replacements_log",
  "notes")` (only those that exist): union with de-duplication. For lists of dicts,
  dedup by a stable key (e.g. `(symbol, date)` if present) or by JSON-serialized
  identity; for lists of scalars, set-union preserving order.
- **Scalar / dict fields** `("week_start", "logic_version", "reject_stats",
  "tie_harvest", "added_last", "pruned")` and **any key not handled above**: prefer
  the side with the newer `week_start` (the renewal advances `week_start`); if
  `week_start` is equal or absent, keep **local**. This keeps the renewal's fresh
  bookkeeping when it is the newer writer. Preserve **all** unknown top-level keys
  (do not drop a field you didn't enumerate — default to local's value, then fill
  any key only remote has).
- Serialize back to bytes with the **same** `json.dumps` options the repo uses for
  this file (match `save_watchlist` — find it and copy its `ensure_ascii`/`indent`
  args) so the diff stays clean.

Keep the function pure (no I/O). Fail-safe on **any** exception → return
`local_bytes`.

**Verify**: `python3 -c "import Super_stock"` imports without error;
`grep -n "_merge_watchlist" Super_stock.py` shows the def.

### Step 3: Route `weekly_watchlist.json` through the merge in `git_save`

In the conflict block (Current state), add a branch **before** the blind
`with open(fn,"wb")` write, parallel to the `.jsonl` branch:

```python
                        elif os.path.basename(str(fn)) == os.path.basename(WATCH_FILE) and os.path.exists(fn):
                            try:
                                with open(fn, "rb") as f:
                                    _remote = f.read()
                                _b = _merge_watchlist(_remote, _b)
                                log(f"🌱 دمجُ القائمة بالمفتاح: {fn}")
                            except Exception as _me:
                                log(f"⚠️ تعذّر دمج {fn} ({_me}) — أُبقيت نسختُنا")
```

Match how the existing `.jsonl` branch reads the remote copy (post-`reset --hard`
the file on disk is the remote). Keep the final `with open(fn,"wb"): f.write(_b)` +
`git add` unchanged — `_b` is now the merged bytes.

**Verify**: `grep -n "_merge_watchlist\|_union_jsonl" Super_stock.py` shows both
branches inside `git_save`. `python3 test_bot.py; echo rc=$?` → `rc=0`.

### Step 4: Full suite

**Verify**: `python3 test_bot.py; echo "rc=$?"` → `rc=0`, zero failures.

## Test plan

Add lock tests to `test_bot.py` for `_merge_watchlist` (pure — build two small dict
blobs, `json.dumps` them, call, `json.loads` the result). Model on an existing
`_union_jsonl` test (`grep -n "_union_jsonl" test_bot.py`). Assert all three
guarantees, each **differentiating** (per `lock-and-mutate`):

1. **No membership loss**: remote has symbol `A` (a candidate the renewal added),
   local has symbol `B`; neither in `removed`. Merge → result `stocks` contains
   **both** `A` and `B`. (Mutation: make the merge take local only → this fails.)
2. **No resurrection**: local `removed` lists `C`; remote `stocks` still contains
   `C` (the concurrent writer hadn't pruned it yet). Merge → `C` is **absent** from
   `stocks`. (Mutation: skip the removal-prune → this fails.)
3. **Append-only union + dedup**: remote `removed=[X]`, local `removed=[X, Y]` →
   merged `removed` is `{X, Y}` with no duplicate `X`.
4. **Fail-safe**: `_merge_watchlist(b"not json", local_bytes)` returns
   `local_bytes` unchanged.
5. **Unknown key preserved**: a top-level key you didn't enumerate (e.g.
   `"future_field"`) present on local survives the merge.

**Prove each lock fails under its mutation** (temporarily break that guarantee,
confirm the test fails, restore). A test that passes with the guarantee removed is
not testing it.

**Verify**: `python3 test_bot.py; echo rc=$?` → `rc=0` with the new tests; each
mutation demonstrated to fail its assertion, then restored.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `python3 test_bot.py` exits 0, zero failures.
- [ ] `python3 -c "import Super_stock"` imports clean.
- [ ] `grep -n "_merge_watchlist" Super_stock.py` shows the pure helper **and** the
      branch inside `git_save`.
- [ ] The three guarantees are locked and each fails under its own mutation
      (demonstrated): membership-union, removal-prune, dedup.
- [ ] `_union_jsonl`, `op_entry_state.json` handling, `pullback_live.py`, and
      `LOGIC_VERSION` are unchanged (`git diff`).
- [ ] Nothing outside the in-scope files modified (`git status`).
- [ ] `plans/README.md` status row updated.

## STOP conditions

Stop and report (do not improvise) if:

- Step 1's structure check fails (no readable `removed` symbols, or a different
  top-level shape) — a merge that can't prevent resurrection is unacceptable.
- The `git_save` conflict block differs from the excerpt (drift, or 031 already
  restructured it in a way that conflicts — in that case, **extend 031's merge
  dispatch** rather than adding a second branch).
- You find a per-entry timestamp after all and are tempted to change conflict
  semantics — report it; that's a scope change.
- Any test cannot be made to fail under its mutation.
- The merge would require touching `save_watchlist`/`make_watch_entry` or any
  membership/selection code.

## Maintenance notes

- **Documented residual**: on the rare event that both writers edit the **same
  symbol's fields** concurrently, the local copy's fields win (no timestamp to
  arbitrate). This is bounded and far better than today's whole-file clobber; a
  reviewer should confirm it's acceptable. If per-entry `updated_at` is ever added,
  upgrade the same-symbol resolution to newest-wins.
- If plan 031 lands a generic dict-merge dispatch in `git_save`, collapse this
  `weekly_watchlist` branch into it (single conflict-resolution path).
- Whenever a new dict-JSON state file gains a second concurrent writer, it needs
  the same treatment — the blind-overwrite default is only safe for single-writer
  dict state.
- Watch in review: that `json.dumps` options match `save_watchlist` exactly, or the
  merged file will produce noisy diffs / churn.
