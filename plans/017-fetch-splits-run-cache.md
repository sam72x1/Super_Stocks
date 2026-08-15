# Plan 017: Cache `_fetch_splits` per run to stop ~300+ duplicate yfinance calls

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving on. If any STOP condition
> occurs, stop and report — do not improvise. When done, update this plan's status row
> in `plans/README.md` (unless a reviewer told you they maintain the index).
>
> **Drift check (run first)**: `git diff --stat 4e9b143..HEAD -- Super_stock.py`
> Super_stock.py is large and changes often — if it drifted, confirm the `_fetch_splits`
> definition and its three call sites still match the excerpts below before proceeding;
> on a mismatch, STOP.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: perf
- **Planned at**: commit `4e9b143`, 2026-08-15

## Why this matters

`_fetch_splits(sym)` makes an uncached `yf.Ticker(sym).splits` network call. It is called
once per active symbol in `update_watchlist_status` **and** once per open alert in
`update_tracking`, **and again** for overlapping symbols in the mg-observe path — so the
same symbol's splits can be fetched 2–3 times in one daily run, and across ~300 active
records that is 300+ sequential yfinance round-trips on the same scraping backend that
already throttles `download_history`, inside a hard job budget. This is the same
fan-out class as the already-fixed `monitor_pullback` bug. A run-scoped memo eliminates
the duplicates with zero logic change: splits data is stable within a run, and the
function is documented as fail-safe (`None → factor 1.0`), so caching `None` preserves
today's behavior on a transient failure.

## Current state

- `Super_stock.py` — `_fetch_splits` is a helper used only in the result-settlement paths
  (outside screening entirely, per its docstring).

`Super_stock.py:10893-10902` (the definition):
```python
def _fetch_splits(sym: str):
    """جلب أحداث التقسيم من ياهو — **فاشل-آمن مطلق** → None (فيصير العامل 1.0 =
    سلوك اليوم حرفيًا، لا تعطيل للحسم بعطل شبكي). تُستدعى فقط في مسارَي تسوية
    النتائج (update_tracking/update_watchlist_status) — خارج الفرز كليًّا."""
    try:
        if yf is None:
            return None
        return yf.Ticker(sym).splits
    except Exception:
        return None
```

The three call sites:
```python
# Super_stock.py:11200  (update_watchlist_status — once per active symbol)
        _raw_splits = _fetch_splits(s["symbol"])
# Super_stock.py:18474  (update_tracking — once per open alert)
            _raw_splits = _fetch_splits(a["symbol"])
# Super_stock.py:18697  (mg-observe path — again, same symbols)
            _spf = _split_scale_factor(_fetch_splits(a["symbol"]), a["date"])
```

**Repo conventions**: fail-safe helpers return a benign default on error; run-scoped
counters/budgets are reset at the start of the daily run (e.g. `_F4_BUDGET[0] = ...` in
`run_daily_watchlist`, near `Super_stock.py:15375`). Match that reset pattern so the cache
does not leak across runs in a long-lived process.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests | `python3 test_bot.py` | exit 0 |
| Find the run reset point | `grep -n "_F4_BUDGET\[0\] =\|_F4_FAILS\[0\] =" Super_stock.py` | shows where per-run counters reset |
| Confirm call sites | `grep -n "_fetch_splits(" Super_stock.py` | the 3 sites above |

## Scope

**In scope**:
- `Super_stock.py` — `_fetch_splits` and a small run-scoped cache reset.
- `test_bot.py` — a test proving the cache returns the memoized value and is injectable.

**Out of scope** (do NOT touch — these are locked roots / documented decisions):
- `_split_scale_factor`, `_scale_divisor`, `update_tracking`/`update_watchlist_status`
  settlement logic — the returned factor must be byte-identical to today.
- Any screening path. No `LOGIC_VERSION` (settlement/display only).

## Git workflow

- Branch: `advisor/017-fetch-splits-run-cache`
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Add a module-level run-scoped cache and use it in `_fetch_splits`

Above `_fetch_splits`, add a module-level dict (near the other run-scoped state):
```python
_SPLITS_CACHE = {}   # ذاكرةُ تقسيماتٍ محدودةٌ بالتشغيلة الواحدة (تُصفّر في بدء المسار اليومي)
```
Rewrite `_fetch_splits` to consult it (cache `None` too, so a transient failure behaves
exactly like today — factor 1.0 — for the rest of the run):
```python
def _fetch_splits(sym: str):
    """... (نفس docstring) ... 🔒 مُخبَّأٌ بالتشغيلة: النتيجة (بما فيها None) تُحفَظ
    فلا يُعاد جلبُ الرمز نفسِه مرّتين/ثلاثًا في نفس المسار. التقسيماتُ ثابتةٌ داخل التشغيلة."""
    if sym in _SPLITS_CACHE:
        return _SPLITS_CACHE[sym]
    val = None
    try:
        if yf is not None:
            val = yf.Ticker(sym).splits
    except Exception:
        val = None
    _SPLITS_CACHE[sym] = val
    return val
```
Do NOT change the three call sites — they keep calling `_fetch_splits(...)` and
transparently hit the cache.

**Verify**: read the code — behavior for a first call is identical (fetch → return);
second call for the same symbol returns the stored value without touching `yf`.

### Step 2: Reset the cache at the start of the daily run

Find the per-run reset block in `run_daily_watchlist` (grep `_F4_BUDGET[0] =`). Add, right
next to it:
```python
    _SPLITS_CACHE.clear()   # ذاكرة التقسيمات محدودة بالتشغيلة — تُصفّر كل مسار
```
This prevents stale splits carrying across runs if the module is reused (the runners
re-import `Super_stock`; a long-lived process would otherwise keep the cache).

**Verify**: `grep -n "_SPLITS_CACHE" Super_stock.py` shows the definition, the use in
`_fetch_splits`, and the `.clear()` in the daily-run reset.

### Step 3: Make the fetch injectable for testing (minimal)

The cleanest test injects the underlying fetch. If `_fetch_splits` is easy to test by
monkeypatching `yf`, do that in the test (Step 4) without changing production code. Only
if the test can't reach it cleanly, add an optional injected fetcher parameter with a
default that preserves current behavior — but prefer monkeypatching `yf` in the test to
keep the signature unchanged.

**Verify**: `python3 test_bot.py` → exit 0.

### Step 4: Add a test proving the cache memoizes (including `None`)

In `test_bot.py`, using the module alias for `Super_stock` (grep for how the suite imports
it — likely `import Super_stock as S` or similar), add a test that:
- Sets a counter-wrapped fake on `S.yf` (or monkeypatches `S._SPLITS_CACHE` + a fake
  `S.yf.Ticker`) so you can count underlying calls.
- Calls `S._fetch_splits("FAKE")` twice; asserts the underlying fetch ran **once** and both
  returns are equal.
- Calls it for a symbol whose fetch raises; asserts it returns `None`, is cached, and a
  second call does **not** re-invoke the fetch.
- Asserts `S._SPLITS_CACHE.clear()` empties it.

Restore any monkeypatched attributes at the end of the block (the suite is one process).

**Verify**: `python3 test_bot.py` → exit 0; new `✅` lines print.

### Step 5: Mutation check

Temporarily make `_fetch_splits` ignore the cache (always re-fetch). Confirm the
"underlying fetch ran once" assertion **fails**. Revert.

**Verify**: with the mutation, exit 1; after revert, exit 0.

## Test plan

- One new `check(...)` block: memoize-hit (call twice → one underlying fetch), memoize-None
  (raising fetch cached as None), and `.clear()` behavior. Plus a mutation round. Keep all
  fetching mocked — no network.

## Done criteria

- [ ] `python3 test_bot.py` exits 0; new cache tests present and passing
- [ ] `_fetch_splits` consults `_SPLITS_CACHE` and stores results including `None`
- [ ] `_SPLITS_CACHE.clear()` is called at the daily-run reset point
- [ ] The three call sites are unchanged (`git diff` shows no edits at 11200/18474/18697)
- [ ] The returned split factor is byte-identical to before for the same input (no logic change)
- [ ] Mutation check passed
- [ ] `git status` shows only `Super_stock.py`, `test_bot.py`
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report if:
- The three call sites don't match the excerpts (Super_stock.py drifted) — re-verify.
- There is an existing test that asserts `_fetch_splits` re-fetches on every call (a lock
  expecting no cache) — report it; do not delete it blindly.
- Caching `None` would suppress an intended in-run retry (search the settlement path for a
  `_split_suspected`/retry-on-None branch) — if found, cache only successful (non-None)
  results and report the nuance.

## Maintenance notes

- The cache is run-scoped on purpose (splits are stable within a run, not across days).
  The `.clear()` at run start is load-bearing for any long-lived/re-imported process.
- Reviewer should confirm no call site was changed and that the split *factor* output is
  identical — this is a pure memoization, not a logic change.
- If splits ever need to be fetched inside the screening path (they must not, per the
  docstring), the run-scoped cache must not leak across the screen/settle boundary.
