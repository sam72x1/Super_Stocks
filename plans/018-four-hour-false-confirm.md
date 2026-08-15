# Plan 018: Stop the 4h card from printing "sweep tail then reclaim (تأكيد)" on stocks that never swept

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving on. If any STOP condition
> occurs, stop and report — do not improvise. This plan changes a **trader-facing
> display string**, so its STOP conditions are strict. When done, update this plan's
> status row in `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4e9b143..HEAD -- Super_stock.py analyze_one.py`
> If Super_stock.py drifted, confirm the three excerpts below still match; on a mismatch, STOP.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: MED (display-semantics change — the fix decides what "confirmed" means on the 4h line)
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `4e9b143`, 2026-08-15

## Why this matters

The 4h interpretation line prints `🕓 4س: ذيل مسح عند $X ثم استعادة (تأكيد)` — a
trader-facing confirmation that the stock swept a low and reclaimed it. But the gate for
that state is `elif h4l.get("sweep_low"):`, and `sweep_low` is defined as
`round(float(np.min(lo)), 2)` — the plain minimum low of the 4h window, which is a
positive number for every real stock and therefore **always truthy**. Consequences:
1. The `else → "weak"` branch is **dead code** — the intended "weak 4h" assessment never shows.
2. `"confirming"` is the catch-all for every stock not blocked-by-red-head / flipped /
   waiting-green-cover, so the "(تأكيد)" confirmation line prints on a broad class of
   stocks that never swept anything. This is exactly the repo's flagged "display line
   asserting a setup the data doesn't establish" (توثيق/عرض يكذب).

The fix ties "confirming" to an **actual reclaim signal** that already exists in the same
data (`green_cover is True` = a green 4h candle closed back above the last red candle's
open), and makes "weak" reachable.

## Current state

- `Super_stock.py` — `four_hour_levels` (produces the 4h data), `build_interpretation`
  (derives `four_hour_context.state`), `interp_card_lines` (renders the line).
  `analyze_one.py` mirrors the card rendering (the repo keeps "manual check == screener").

`Super_stock.py:2498-2500` (`sweep_low` is just the window min — always truthy):
```python
    return {"supports": supports, "resistances": resistances,
            "flip": flip, "sweep_low": round(float(np.min(lo)), 2),
            "green_cover": green_cover, "managed_ceiling": managed}
```

`Super_stock.py:8530-8545` (the state chain — `else → "weak"` is dead because sweep_low is truthy):
```python
            flip = h4l.get("flip")
            gcov = h4l.get("green_cover")     # المقطع: تغطية الخضرا = تأكيد
            if red_head and red_head > price:
                h4state = "blocked_by_red_head"
            elif flip and flip <= price * 1.01:
                h4state = "support_flipped"
            elif gcov is False:
                h4state = "waiting_green_cover"   # حمرا أخيرة بلا تغطية = ننتظر
            elif h4l.get("sweep_low"):
                h4state = "confirming"
            else:
                h4state = "weak"
            out["four_hour_context"] = {
                "state": h4state, "red_candle_head": red_head, "flip": flip,
                "sweep_low": h4l.get("sweep_low"), "green_cover": gcov}
```

`Super_stock.py:8678-8680` (the render):
```python
    elif h4s == "confirming" and h4c.get("sweep_low"):
        lines.append(f"🕓 4س: ذيل مسح عند ${h4c['sweep_low']:.2f} ثم استعادة "
                     "(تأكيد)")
```

**Note on `green_cover`**: at `Super_stock.py:2496-2497` it is a `bool` derived from
whether a later green candle closed at/above the last red candle's open — i.e. a genuine
reclaim. The existing chain already routes `gcov is False` → "waiting". Making
"confirming" require `gcov is True` is therefore consistent with the existing semantics
and makes the states mutually exhaustive: blocked / flipped / waiting(gcov False) /
confirming(gcov True) / weak(gcov None, e.g. no red candle to reclaim).

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests | `python3 test_bot.py` | exit 0 |
| Confirm interp is display-only | `grep -n "four_hour_context\|h4state\|interp_card_lines" Super_stock.py` | shows it feeds display, not `rank_key` |

## Scope

**In scope**:
- `Super_stock.py` — the single `elif` at line 8538 (state chain) only.
- `test_bot.py` — tests for the four_hour_context state mapping.

**Out of scope** (do NOT touch):
- `four_hour_levels` and `sweep_low`'s value — it's still displayed as a level; only its
  misuse as a boolean is the bug.
- `analyze_one.py` — the card render at 8678 reads `h4c` and does not need changing (the
  fix is upstream in the state derivation). Only touch it if a mirrored copy of the *state
  chain* lives there; confirm with grep first, and if so apply the identical change.
- `rank_key`/`select_top`/any selection root. `four_hour_context` is display/interp only
  and is documented as locked out of ranking (CLAUDE.md "interp خارج rank_key"). No
  `LOGIC_VERSION`.

## Git workflow

- Branch: `advisor/018-four-hour-false-confirm`
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Verify `four_hour_context` never feeds selection

Confirm `four_hour_context` / `h4state` are read only by display builders
(`interp_card_lines`, `build_message`, `build_daily_message`, `analyze_one`) and never by
`rank_key`/`select_top`/`classify_tier`. Use grep; if any selection path reads it, STOP
and report (the fix would then need owner sign-off + `LOGIC_VERSION`).

**Verify**: grep output shows only display/interp consumers.

### Step 2: Tie "confirming" to an actual reclaim signal

Change the state chain so "confirming" requires a real reclaim (`green_cover is True`),
making "weak" reachable:
```python
            elif gcov is True:
                h4state = "confirming"   # تغطيةُ خضراء فعلية = ذيلُ مسحٍ ثم استعادة
            else:
                h4state = "weak"         # لا تغطية مؤكَّدة (لا شمعة حمرا لتُستعاد) = ضعيف
```
i.e. replace `elif h4l.get("sweep_low"):` with `elif gcov is True:`. Leave the
`out["four_hour_context"] = {...}` dict unchanged (it still carries `sweep_low` for the
render). The render at 8678 already guards on `h4s == "confirming" and h4c.get("sweep_low")`,
so it prints the level only when actually confirming.

**Verify**: read the chain — `gcov is False` → waiting, `gcov is True` → confirming,
`gcov is None` → weak; each state reachable.

### Step 3: Confirm the render no longer fires on non-reclaim stocks

The confirmation line now prints only when `green_cover is True`. Trace: a stock with no
red candle in the 4h window has `gcov is None` (or `False`) → "weak"/"waiting", so no
"(تأكيد)" line. Do not change the render string itself.

**Verify**: `python3 test_bot.py` → exit 0 (no regression).

### Step 4: Add tests for the state mapping

In `test_bot.py`, call `build_interpretation` (or the smallest function that produces
`four_hour_context`) with synthetic inputs that exercise:
- `green_cover=True`, no red-head-above, no flip → state `"confirming"`, render includes "(تأكيد)".
- `green_cover=None` (no red candle) → state `"weak"`, render has **no** "(تأكيد)" line.
- `green_cover=False` → state `"waiting_green_cover"` (unchanged).
Use the existing 4h/interp test fixtures if present (grep `four_hour_context` in
`test_bot.py`); otherwise construct the minimal `h4l` dict the chain reads
(`flip`, `green_cover`, `sweep_low`, `resistances`).

**Verify**: `python3 test_bot.py` → exit 0; new `✅` lines print.

### Step 5: Mutation check

Temporarily revert to `elif h4l.get("sweep_low"):` and confirm the "weak" test **fails**
(state becomes "confirming" when it shouldn't). Revert.

**Verify**: with the mutation, exit 1; after revert, exit 0.

## Test plan

- New `check(...)` cases mapping `green_cover` → state → rendered line, plus a mutation
  round proving "weak" is now reachable. Model after any existing interp/4h test.

## Done criteria

- [ ] `python3 test_bot.py` exits 0; new state-mapping tests present and passing
- [ ] "confirming"/"(تأكيد)" fires only when `green_cover is True`
- [ ] "weak" state is reachable (green_cover None → weak)
- [ ] `four_hour_levels`/`sweep_low` value and the render string are unchanged
- [ ] Confirmed (Step 1) that `four_hour_context` never feeds selection
- [ ] Mutation check passed
- [ ] `git status` shows only `Super_stock.py`, `test_bot.py` (and `analyze_one.py` only if it mirrors the state chain)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report (do not improvise the semantics) if:
- Step 1 finds `four_hour_context` feeding a selection root — this becomes an owner
  decision + `LOGIC_VERSION`, out of scope for this plan.
- `green_cover` turns out NOT to represent a reclaim (re-read `four_hour_levels:2490-2500`)
  — if the reclaim signal is something else, report the correct one rather than guessing.
- The owner's intent for the 4h "confirming" line is ambiguous and no reclaim signal
  cleanly maps to it — report options (require `green_cover`, or drop the line entirely)
  and let the owner choose. This is a display-meaning call.

## Maintenance notes

- The root cause is a value (`sweep_low` = a price level) being used as a boolean (did a
  sweep happen). If a future change adds a real "4h sweep-and-reclaim" boolean to
  `four_hour_levels`, prefer it over `green_cover` here.
- Reviewer should confirm this only changes a *displayed string's* firing condition and
  touches no number, level, stop, or target.
