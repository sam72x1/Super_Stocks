# Plan 015: Add a coverage floor to press_radar so a throttled fetch can't silently kill a session

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving on. If any STOP condition
> occurs, stop and report — do not improvise. When done, update this plan's status row
> in `plans/README.md` (unless a reviewer told you they maintain the index).
>
> **Drift check (run first)**: `git diff --stat 4e9b143..HEAD -- press_radar.py split_hunter.py`
> If either changed since this plan was written, compare the "Current state" excerpts
> below against the live code before proceeding; on a mismatch, STOP.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `4e9b143`, 2026-08-15

## Why this matters

`press_radar.py` is one of five nightly "hunter" runners that message the owner. When
Yahoo throttles, `fetch(pool)` returns an empty/tiny dict — indistinguishable from a
genuine "no ready stock". press_radar then (a) sends the owner nothing and (b)
unconditionally stamps `state["last_session"] = session_iso`, so the 01:25 safety-net
cron sees the stamp and `return 0` before scanning. The result: a session with **no
Telegram and no failure signal** — the exact "silent miss" the other four hunters were
hardened against. `split_hunter.py`, `method_hunter.py`, `envelope_hunter.py`, and
`split_filter_hunter.py` all have a `MIN_COVERAGE_PCT` floor; press_radar is the lone
gap. Adding the same floor makes a throttle look like a throttle (re-scanned by the
second cron) instead of like an empty market.

## Current state

- `press_radar.py` — nightly "pressure radar" hunter; `run()` fetches a curated pool,
  scans, sends a Telegram alert on matches, else stays silent, then stamps the session.

`press_radar.py:401-410` (dedup gate + fetch, no coverage guard):
```python
    if state.get("last_session") == session_iso and not force:
        _log(f"🔁 دِدوب: جلسة {session_iso} فُحصت وسُلّمت — لا إعادة.")
        return 0
    wl = S.load_watchlist() or {}
    pool, cut = build_pool(wl, state, session_iso)
    ...
    fetch = fetch_hist or S.download_history
    hist = fetch(pool) or {}
```

`press_radar.py:442-458` (coverage is LOGGED but never gates; the silent branch stamps unconditionally):
```python
    _log(f"🩺 التغطية: فُحص {len(pool) - failed} · تعذّر {failed} · مطابق {len(rows)}.")
    ...
    if rows:
        msg = build_alert(rows, session_iso)
        send = sender or S.send_telegram
        if not send(msg):
            _log("⛔ إرسال تلغرام فشل — لا ختم ولا سجل (الكرون الثاني يعيد).")
            return 1
        ...
    else:
        _log("📭 لا مطابق هذي الجلسة — صامتٌ عمدًا (قاعدة «الجاهز فقط»)، والتغطية أعلاه دليل الحياة.")
    state["last_session"] = session_iso
    if not save_state(state, state_path):
        ...
```

The proven pattern to mirror — `split_hunter.py:196-204`:
```python
        return _fail(S, "لا بيانات مُحمَّلة إطلاقًا.")
    # 🩺 **حارس التغطية** — الناقل الأخطر: خنق ياهو يُنزل التغطية من ~3400 رمز إلى
    # بضع مئات، فيمشي المسح ويطبع «0 مطابق» ويصمت...
    cov = 100.0 * len(hist) / max(1, len(uni))
    if cov < MIN_COVERAGE_PCT:
        return _fail(S, f"تغطية ناقصة: {len(hist)} من {len(uni)} رمزًا ({cov:.0f}%) — "
                        f"أقل من الأرضية {MIN_COVERAGE_PCT:.0f}%، فلم يُفحَص السوق.")
```

**Key difference for press_radar**: its universe is the *curated pool* (capped, small),
not the ~3400-symbol NASDAQ universe. The denominator must be `len(pool)` (the fetch
target), not a market-wide count. The critical fix is: on a below-floor coverage,
**return without stamping `last_session`** so the second cron re-scans.

**Repo conventions**: Arabic comments; `_log` for output; the runner returns an int exit
code (0 = normal, 1 = "second cron should retry"). Match `split_hunter`'s `MIN_COVERAGE_PCT`
naming and threshold style.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests   | `python3 test_bot.py` | exit 0, last line `✅✅ كل الاختبارات نجحت` |
| Read the floor const | `grep -n "MIN_COVERAGE_PCT" split_hunter.py method_hunter.py press_radar.py` | shows the value used by siblings |

## Scope

**In scope**:
- `press_radar.py`
- `test_bot.py` (add tests using the `_PRD` alias already imported at `test_bot.py:17296`)

**Out of scope**:
- The scan/gate logic (`press_read`, `build_pool`, `build_alert`) — do not change what
  qualifies, only add the coverage guard.
- `split_hunter.py` and the other hunters — they already have the floor; do not touch.
- Any screening root. No `LOGIC_VERSION` bump (this is a display/alert-path guard).

## Git workflow

- Branch: `advisor/015-press-radar-coverage-floor`
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Add a `MIN_COVERAGE_PCT` constant to press_radar

At the top of `press_radar.py` with the other module constants, add (match the sibling
value — read it with the grep above; if siblings use `50.0`, use the same):
```python
MIN_COVERAGE_PCT = 50.0   # حارس التغطية: خنق ياهو ⇒ لا نصمت ولا نختم — الكرون الثاني يعيد.
```

### Step 2: Insert the coverage floor after the fetch, before scanning

Immediately after `hist = fetch(pool) or {}` (`press_radar.py:410`), add:
```python
    _cov_ok = sum(1 for s in pool if hist.get(s) is not None)
    cov = 100.0 * _cov_ok / max(1, len(pool))
    if cov < MIN_COVERAGE_PCT and not force:
        _log(f"🩺 تغطية ناقصة: {_cov_ok} من {len(pool)} ({cov:.0f}%) — أقل من "
             f"الأرضية {MIN_COVERAGE_PCT:.0f}%، لم تُفحَص البِركة. لا ختم — الكرون الثاني يعيد.")
        return 1
```
This runs **before** any `state["last_session"]` write, so a throttled session is not
stamped and the second cron re-scans. `not force` mirrors the manual-override behavior
(a `*_FORCE` run should still proceed).

**Verify**: read the code — the new block sits between the fetch and the scan loop, and
there is no `state["last_session"] = ...` between the fetch and this guard.

### Step 3: Confirm the stamp still happens on a real (covered) empty session

Trace: when coverage ≥ floor and `rows` is empty, control still reaches
`state["last_session"] = session_iso` at line 457 and stamps normally (a genuine "no
match" is correctly deduped). Only the *below-floor* case skips the stamp. Do not change
the `else:` silent branch — a covered empty session should stay silent-and-stamped.

**Verify**: `python3 test_bot.py` → exit 0 (no regression in existing press_radar tests).

### Step 4: Add tests

Using the `_PRD` alias (`test_bot.py:17296`) and injecting `fetch_hist`/`sender` as the
existing PRD tests do, add two cases:
1. **Throttle case**: call `run(...)` with a `fetch_hist` that returns `{}` (or data for
   fewer than the floor fraction of `pool`) and a fresh state; assert the return is `1`
   and that `state.get("last_session")` was **NOT** set to the session (the second cron
   would re-scan). Capture `_log` output and assert it mentions the coverage shortfall.
2. **Covered-empty case**: `fetch_hist` returns full-coverage data that yields zero
   matches; assert the session **is** stamped and no alert is sent (existing behavior
   preserved).

Model the injection/setup after the existing `_PRD.run` test (search `test_bot.py` for
`_PRD.run`).

**Verify**: `python3 test_bot.py` → exit 0; your two new `✅` lines print.

### Step 5: Mutation check

Temporarily change the guard to `if cov < 0.0` (never fires). Run `python3 test_bot.py`
and confirm the throttle-case test **fails** (the session gets stamped / return isn't 1).
Revert.

**Verify**: with the mutation, exit 1; after revert, exit 0.

## Test plan

- Two new `check(...)` cases as above, plus a mutation round proving the throttle test is
  real. Reuse the injection pattern from the existing `_PRD.run` test so the new tests
  never touch the network (all fetchers injected).

## Done criteria

- [ ] `python3 test_bot.py` exits 0; two new press_radar tests present and passing
- [ ] Below-floor coverage: `run()` returns `1`, logs the shortfall, and does **not** set `state["last_session"]`
- [ ] Covered-empty session: unchanged (silent + stamped)
- [ ] `MIN_COVERAGE_PCT` uses the same value as the sibling hunters
- [ ] Mutation check passed
- [ ] `git status` shows only `press_radar.py`, `test_bot.py`
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report if:
- `run()`'s control flow between fetch and the stamp is not as excerpted (e.g. the stamp
  moved) — the guard must precede any stamp; report the actual structure.
- The sibling `MIN_COVERAGE_PCT` value can't be found — report and use `50.0` explicitly,
  noting the assumption.
- A `*_FORCE`/manual-dispatch path relies on running even under throttle — confirm the
  `not force` clause preserves it; if `force` isn't a parameter of `run()`, report.

## Maintenance notes

- The denominator is deliberately the **pool** (fetch target), not the market universe —
  press_radar scans a curated pool, unlike the market-wide hunters. If `build_pool` ever
  changes to scan the full universe, revisit the denominator.
- Reviewer should confirm the guard sits before every `state` write and that `force`
  still bypasses it (manual runs must not be blocked by a transient throttle).
