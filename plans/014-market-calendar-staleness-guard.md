# Plan 014: Make the market calendar fail loud when its year lapses (and add 2027 data)

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving on. If any STOP condition
> occurs, stop and report — do not improvise. When done, update this plan's status
> row in `plans/README.md` (unless a reviewer told you they maintain the index).
>
> **Drift check (run first)**: `git diff --stat 4e9b143..HEAD -- market_calendar.py ignition_live.py`
> If either file changed since this plan was written, compare the "Current state"
> excerpts below against the live code before proceeding; on a mismatch, STOP.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `4e9b143`, 2026-08-15

## Why this matters

`market_calendar.py` hard-codes only 2026 US-market holidays and early closes, and
`session_info` returns `session_type="regular"` for **any** date it doesn't recognize.
Today is 2026-08-15. On 2027-01-01 and every 2027+ holiday, the calendar will silently
report "regular" — so `ignition_live.py`'s holiday short-circuit (line 413) no-ops and
the ignition radar runs a full "session" on a **closed** market: it reads a stale daily
candle, may fire alerts to the owner on a day with no trading, and inflates E2 session
tallies. Early-close days would also compute the wrong 16:00 close. There is no runtime
signal that the calendar has lapsed. The fix: make a lapsed calendar **loud** (surface a
warning so the owner refreshes it) instead of silently defaulting to "regular", and add
2027 data. This activates in ~4.5 months, so it is time-sensitive.

## Current state

- `market_calendar.py` — pure, version-pinned US-market calendar. Consumed only by
  `ignition_live.py`.

`market_calendar.py:12-33` (the pinned data — 2026 only):
```python
CALENDAR_VERSION = "2026.1-us-nasdaq"
CALENDAR_SOURCE = "NYSE/Nasdaq holiday schedule 2026 (version-pinned; verify before confirmatory)"

# عطلات السوق الأمريكي 2026 (مغلق كليًّا) — ISO date.
HOLIDAYS = {
    "2026-01-01",  # New Year's Day (خميس)
    ...
    "2026-12-25",  # Christmas
}

EARLY_CLOSES = {
    "2026-11-27": 13 * 60,   # اليوم التالي للثانكسجيفينغ
    "2026-12-24": 13 * 60,   # ليلة الميلاد
}
```

`market_calendar.py:39-54` (the functions that silently default to "regular"):
```python
def session_info(date_iso):
    if date_iso in HOLIDAYS:
        return {"session_type": "holiday", "open_ny_min": None, "close_ny_min": None,
                "calendar_version": CALENDAR_VERSION}
    if date_iso in EARLY_CLOSES:
        return {"session_type": "early_close", "open_ny_min": REGULAR_OPEN_NY_MIN,
                "close_ny_min": EARLY_CLOSES[date_iso], "calendar_version": CALENDAR_VERSION}
    return {"session_type": "regular", "open_ny_min": REGULAR_OPEN_NY_MIN,
            "close_ny_min": REGULAR_CLOSE_NY_MIN, "calendar_version": CALENDAR_VERSION}

def is_trading_day(date_iso):
    return date_iso not in HOLIDAYS
```

`ignition_live.py:283-294` (the only consumer — reads `session_info`):
```python
    _cal = {"session_type": "regular", "calendar_version": None}
    _close_utc = sess["close"]
    try:
        import market_calendar as cal
        _date = now_aware.astimezone(bot.dt.timezone.utc).date().isoformat()
        ci = cal.session_info(_date)
        _cal = {"session_type": ci["session_type"], "calendar_version": ci["calendar_version"]}
        if ci["session_type"] == "early_close" and ci["close_ny_min"] is not None:
            _close_utc = sess["close"] - (cal.REGULAR_CLOSE_NY_MIN - ci["close_ny_min"])
    except Exception:
        pass
```
`ignition_live.py:413` uses `if window.get("session_type") == "holiday": ... return`.

**Repo conventions to follow**: this codebase writes Arabic comments and prefers
fail-safe, explicit behavior with a printed/logged signal rather than silent defaults
(the whole repo doctrine is "no silent miss"). Match the existing comment style. Keep
`market_calendar.py` pure and importable (no side effects at import).

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests   | `python3 test_bot.py` | exit 0, last line `✅✅ كل الاختبارات نجحت` |
| Scope check | `git status --porcelain` | only `market_calendar.py`, `test_bot.py` listed |

(No install step — the suite runs fully offline.)

## Scope

**In scope**:
- `market_calendar.py`
- `test_bot.py` (add tests)
- `ignition_live.py` — **only** the small consumer block at 283-294 / 413 IF step 3 requires it; prefer to keep the conservative handling inside `market_calendar` and leave `ignition_live` untouched.

**Out of scope** (do NOT touch):
- Any screening/root logic. `market_calendar` is display/timing infra only — no `LOGIC_VERSION` bump is warranted.
- The 2026 holiday/early-close values — they are correct; only add years, never edit existing entries.

## Git workflow

- Branch: `advisor/014-market-calendar-staleness`
- Commit style matches the repo (Arabic subject + trailer). End the commit message with:
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Add a covered-years set and a staleness signal to `market_calendar.py`

Add near the top (after `CALENDAR_VERSION`):
```python
# السنواتُ المُغطّاة بهذا التقويم — إذا جاء تاريخٌ خارجها فالتقويمُ **بائت**
# ويجب أن يُعلَن لا أن يُفترَض «يوم تداول عادي» بصمت.
COVERED_YEARS = {"2026", "2027"}
```
(Set the years to exactly those you actually populate in Step 2. If you do NOT add 2027
data in Step 2 because you cannot verify it — see STOP conditions — then `COVERED_YEARS`
is `{"2026"}`.)

In `session_info`, add — **before** the existing `if date_iso in HOLIDAYS:` — a stale
branch that flags an uncovered year with a distinct type, and add the flag to every
returned dict:
```python
def session_info(date_iso):
    covered = str(date_iso)[:4] in COVERED_YEARS
    if not covered:
        # التقويمُ لا يغطّي هذه السنة — لا نُخمّن «عادي». نُعيد نوعًا مميّزًا
        # يعامله المُستهلك بحذر ويُعلَن مرّة، ونُبقي أوقاتَ الجلسة العادية
        # حتى لا يتعطّل التداولُ في يومٍ عاديّ بينما نطالب بتحديث التقويم.
        return {"session_type": "unknown_calendar", "open_ny_min": REGULAR_OPEN_NY_MIN,
                "close_ny_min": REGULAR_CLOSE_NY_MIN, "calendar_version": CALENDAR_VERSION,
                "calendar_stale": True}
    if date_iso in HOLIDAYS:
        return {"session_type": "holiday", ..., "calendar_stale": False}
    if date_iso in EARLY_CLOSES:
        return {"session_type": "early_close", ..., "calendar_stale": False}
    return {"session_type": "regular", ..., "calendar_stale": False}
```
Add `"calendar_stale": False` to the three existing returns (holiday / early_close /
regular). **Design rationale to preserve**: `unknown_calendar` keeps regular session
*times* (so a normal weekday still trades) but is a distinct `session_type`, so a
consumer can log "calendar lapsed, refresh me" without treating the day as a holiday.

**Verify**: `python3 -c "import market_calendar as c; print(c.session_info('2099-01-01'))"`
→ prints a dict with `session_type='unknown_calendar'` and `calendar_stale=True`.
`python3 -c "import market_calendar as c; print(c.session_info('2026-12-25')['session_type'])"`
→ `holiday`.

### Step 2: Add 2027 holiday and early-close data — ONLY if you can verify it

Add 2027 entries to `HOLIDAYS` and `EARLY_CLOSES`. **US market observed-holiday dates
shift when a holiday falls on a weekend (e.g. July 4 observed on the adjacent weekday),
and the exact early-close dates vary.** You MUST verify each 2027 date against the
official NYSE/Nasdaq 2027 schedule before adding it. If you cannot verify (no reliable
source available to you), **do NOT guess dates** — set `COVERED_YEARS = {"2026"}`, skip
this step, and note in your report that 2027 data is a follow-up for the owner. The
staleness guard (Step 1) is the load-bearing fix; the 2027 data is the convenience.

If verified, follow the existing entry format exactly (ISO date + Arabic comment naming
the holiday), and never edit the 2026 entries.

**Verify** (only if you added 2027): `python3 -c "import market_calendar as c; print(c.session_info('2027-01-01')['session_type'])"`
→ `holiday` (or whatever the verified 2027 New Year observation is).

### Step 3: Confirm the consumer surfaces the stale signal (no code change expected)

Read `ignition_live.py:410-416`. The holiday short-circuit already returns for
`session_type == "holiday"`; for `unknown_calendar` it will (correctly) fall through and
run a regular session on a normal weekday. That is the intended behavior. The stale
signal is surfaced by the calendar's distinct `session_type` in the logged
`calendar_version`/window. **Do not** add a hard block for `unknown_calendar` in
`ignition_live` — that would silence the radar for a whole future year. If you want the
lapse to reach the owner, add a one-line log (not a Telegram alert) inside the existing
`try` block at `ignition_live.py:290`, e.g. after `_cal = {...}`:
```python
        if ci.get("calendar_stale"):
            bot.log(f"⚠️ تقويم السوق بائت (لا يغطّي {_date[:4]}) — يُفترَض عادي، حدّث market_calendar.")
```
This is optional and additive; if in doubt, skip it and leave `ignition_live` untouched.

**Verify**: `python3 test_bot.py` → exit 0.

### Step 4: Add tests

Add a small test block in `test_bot.py` using the existing `check(name, cond, extra="")`
helper (defined at `test_bot.py:99`). Import `market_calendar` and assert:
- `session_info("2099-06-15")["session_type"] == "unknown_calendar"` and `["calendar_stale"] is True`
- `session_info("2026-12-25")["session_type"] == "holiday"` and `["calendar_stale"] is False`
- `session_info("2026-06-15")["session_type"] == "regular"`
- if you added 2027: one 2027 holiday returns `"holiday"`.

**Verify**: `python3 test_bot.py` → exit 0; your new `✅` lines print.

### Step 5: Mutation check (prove the tests can fail)

Temporarily change `COVERED_YEARS` to include `"2099"`, run `python3 test_bot.py`, and
confirm the `unknown_calendar` assertion **fails** (`❌`, exit 1). Revert the change.
Per repo doctrine: "a lock that never falls is not a lock."

**Verify**: with the mutation, `python3 test_bot.py` exits 1; after revert, exit 0.

## Test plan

- New tests in `test_bot.py` (model after the existing `check(...)` calls, e.g. the
  `_LG` block around `test_bot.py:16307`): the four assertions above, plus a mutation
  round proving the `unknown_calendar` assertion is real.

## Done criteria

- [ ] `python3 test_bot.py` exits 0; new calendar tests present and passing
- [ ] `session_info` returns `unknown_calendar` + `calendar_stale=True` for any year not in `COVERED_YEARS`, and `calendar_stale=False` for covered dates
- [ ] `COVERED_YEARS` matches exactly the years actually populated (no year claimed without data)
- [ ] 2026 `HOLIDAYS`/`EARLY_CLOSES` entries unchanged (`git diff` shows only additions)
- [ ] Mutation check passed (assertion falls when broken)
- [ ] `git status` shows only `market_calendar.py`, `test_bot.py` (and optionally `ignition_live.py` if Step 3's one-liner was added)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report if:
- You cannot verify 2027 holiday dates from a reliable source — ship Step 1 only, set `COVERED_YEARS={"2026"}`, report 2027 as follow-up. (This is expected and fine.)
- Adding the `calendar_stale` field breaks an existing test that asserts the old 3-key return shape — report which test; the lock may need a dated update, but do not edit it blindly.
- `ignition_live` turns out to depend on `session_info` returning exactly 4 keys (a strict `==` on the dict) — report it.

## Maintenance notes

- This calendar needs an annual refresh; the staleness guard now makes a lapse visible.
  When adding a new year, extend both the data sets and `COVERED_YEARS` together.
- Observed-holiday rules (weekend shift) are the easy thing to get wrong — always verify
  against the official schedule, per the file's own `CALENDAR_SOURCE` note.
- Reviewer should scrutinize: that `unknown_calendar` keeps regular session *times*
  (so it does not silence the radar on ordinary future weekdays) and only changes the
  *type*.
