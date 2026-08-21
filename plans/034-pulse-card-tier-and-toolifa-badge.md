# Plan 034: Pulse (`Px`) update cards must show the real tier (قوي/متوسط/ضعيف) and keep the "🥇 توليفة" badge

> **Executor instructions**: Follow this plan step by step. Run every verification
> command and confirm the expected result before moving on. If any STOP condition
> occurs, stop and report — do not improvise. When done, update this plan's status
> row in `plans/README.md` (unless a reviewer told you they maintain the index).
>
> **Drift check (run first)**:
> `git diff --stat 5cb88df..HEAD -- Super_stock.py`
> This plan was written against `origin/main` (`5cb88df`). The code it edits
> (`liq_stage_events`, `liq_tier`, `kasih_j1`, `build_liq_stage_alert`) exists on
> `origin/main`, **not** on an older checkout. If `git rev-parse --short HEAD` is
> not `5cb88df` or a descendant, or if `Super_stock.py` has no function named
> `liq_tier`, **STOP** — you are on the wrong tree; the operator must update to
> `origin/main` first. If `Super_stock.py` changed since `5cb88df`, compare the
> "Current state" excerpts below against the live code before editing; on a
> mismatch to those blocks, STOP.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `5cb88df` (origin/main), 2026-08-21

## Why this matters

The live-liquidity alert channel classifies a stock into a three-tier badge —
🥇 قوي / 🥈 متوسط / 🥉 ضعيف — on its `M5` card, and repeats a per-minute "نبض
السيولة" (`Px`, pulse) update card while liquidity keeps moving. The owner
explicitly asked (2026-08-20) that **every update carry its class and stop line**
("ما يوصلني تحديث إلا للأسهم اللي لها تصنيف قوي متوسط ضعيف **ومع قرار الدخول**"),
so he can read the tier straight from the Telegram notification without opening
the app.

The bug: a stock the `M5` card correctly labels **قوي** is re-labeled **متوسط**
(or ضعيف) on **every** subsequent pulse card, and its "🥇 توليفة" badge
disappears. The header line the owner reads therefore understates the strongest
names on exactly the cards meant to say "keep going." This is the repo's own
"imagined key / wrong label in the header" class.

Root cause (verified by reading the code): the tier's قوي branch requires
`kasih_j1(ev)` to be true, and `kasih_j1` derives J1 from `ev["class"]` and
`ev["prev_close"]`. The `M5` event carries `class`; the `Px` (pulse) event **never
carries `class`**, so `kasih_j1(Px)` always returns `(False, False)` and the قوي
branch in `liq_tier` is structurally unreachable for pulses. Pulse cards are
always `Px`-only (pulses only fire after `M5` has already been sent), so the tier
shown on a pulse card is always `liq_tier(Px)`, which can only ever be متوسط or
ضعيف. The stored `k2` (which the pulse copies) holds only the four continuation
components `{c3,c4,v2,v3}` — not the J1 result — so `liq_tier(Px)` computes the
green count correctly but cannot reproduce J1.

The fix: when `M5` fires, stamp its J1 result into the `k2` dict that gets saved
to state and copied onto the pulse event, then have `liq_tier` (and the header's
توليفة badge) read that stored J1 for `Px` events instead of recomputing it from
fields the pulse doesn't have. This is display-only: it does **not** change which
stocks fire, the dedup, or any selection logic — no `LOGIC_VERSION` bump.

## Current state

All excerpts are from `Super_stock.py` at `origin/main` (`5cb88df`). Line numbers
are approximate — locate by the shown text, not the number.

### 1. The `Px` (pulse) event — has `k2`, `anchor_price`, `anchor_low`, but no `class` (≈ line 13392)

```python
                ev.append({"stage": "Px", "usd": round(_usd(_b)),
                           "minutes": 1, "anchor_ms": anchor,
                           "last_ms": int(_b["t"]),
                           "price": round(float(_b["c"]), 4),
                           "price_ms": int(_b["t"]),
                           "prev_usd": round(_pu),
                           "pulse_pct": _chg,
                           "k2": _k2p,
                           "anchor_price": st.get("anchor_price"),
                           "anchor_low": st.get("anchor_low")})
```
`_k2p = st.get("k2")` (a few lines above): the pulse copies the `k2` dict that
`M5` stored into state. **`_k2p` is the carrier we will extend.**

### 2. `M5` builds `k2` and saves it to state (≈ line 13453)

```python
            if tag == "M5":
                _evd["k2"] = kasih2_wave_feats(win, anchor,
                                               st.get("anchor_price"))
                # 🥇🥈🥉 **يُحفَظ في الحالة** كي يحمله النبضُ بعده — أمرُ
                #    المالك «ما يوصلني تحديث إلا للأسهم اللي لها تصنيف …
                #    **ومع قرار الدخول**». وقبل `M5` لا تصنيفَ ⇒ لا نبض.
                st["k2"] = _evd["k2"]
            ev.append(_evd)
```
The `_evd` M5 event dict here **does** carry `class` (built at the top of the same
dict: `"class": _ignition_candle_class(tot)`) and gets `prev_close` injected later
(see block 3). So `kasih_j1(_evd)` is computable at this point.

### 3. `prev_close` is injected onto ALL events after the fact (≈ line 13552)

```python
            _pc = polygon_prev_close(row.get("symbol"), today_iso)
            for e in ev:
                e["operator"] = of
                if _pc:
                    e["prev_close"] = _pc
```
Note: at the time `M5` builds `k2` (block 2), `prev_close` is **not yet** on the
event — it is injected here in `scan_liq_stages`, after `liq_stage_events`
returns. This matters: **do not** try to compute J1 inside `liq_stage_events`
(prev_close is absent there). Compute it where prev_close is present. See Step 1.

### 4. `liq_tier` — the قوي branch is unreachable for `Px` (≈ line 14126)

```python
        if str((ev or {}).get("stage") or "") not in ("M5", "Px"):
            return None
        k2 = (ev or {}).get("k2") or {}
        top = {"c3": "صادقت (إغلاقٌ فوق المرساة)", "c4": "خضراء 3-4",
               "v2": "المرساة دون 30% (سيولة تتوالى)",
               "v3": "سيولةٌ داخلة (نبضٌ صافٍ موجب)"}
        got = [f for f in ("c3", "c4", "v2", "v3") if k2.get(f)]
        if not got:
            return None
        green = sum(1 for f in got if k2.get(f) == top[f])
        j1 = kasih_j1(ev)[0]
        if j1 and green >= 3:
            return ("قوي", green, len(got))
        if (not j1) and green <= 1:
            return ("ضعيف", green, len(got))
        return ("متوسط", green, len(got))
```
`j1 = kasih_j1(ev)[0]` — for a `Px` event this is always `False` (missing
`class`). **This is the line to change** so `Px` reads the stored J1.

### 5. `kasih_j1` — reads `ev["class"]` and `ev["prev_close"]` (≈ line 14196)

```python
    try:
        cls = (ev or {}).get("class")
        key = cls[0] if isinstance(cls, (list, tuple)) and cls else None
        if key not in ("strong", "operator"):
            return (False, False)
        gp = (float(ev["anchor_price"]) / float(ev["prev_close"]) - 1.0) * 100.0
        if gp < 30.0:
            return (False, False)
        return (True, key == "strong" and gp >= 75.0)
```
**Do not change `kasih_j1` itself.** It is correct for `M5`. The fix stores its
result and reads the stored value for `Px`.

### 6. The card header — tier + توليفة badge aggregation (≈ line 14354)

```python
        _tier = next((t for t in (liq_tier(e) for e in evs) if t), None)
        if _tier:
            head.append(_LIQ_TIER_AR[_tier[0]])
        # 🥇 شارةُ التوليفة (‏J1) من أيّ حدثِ M5 في الكرت — قاعدةٌ واحدة.
        _j1 = [kasih_j1(e) for e in evs]
        if any(a for a, _ in _j1):
            head.append("🥇 توليفة"
                        + (" (أقوى خلية)" if any(t for _, t in _j1) else ""))
```
Two problems here: (a) the توليفة badge calls `kasih_j1(e)` over **all** events,
so on a `Px`-only card it is always False (badge vanishes — the bug), and on the
first `M1` card it can fire one window early (`M1` carries `class`+`anchor_price`);
(b) it is a second, independent copy of the J1 logic. The fix routes both through
one helper.

### `k2` currently holds only the continuation components (verified)

`kasih2_wave_feats(...)` returns `{"c3":…, "c4":…, "v2":…, "v3":…}` — **no
`class`, no `prev_close`, no J1 flag.** So `k2` alone cannot yield قوي today.

## Commands you will need

| Purpose | Command | Expected on success |
|---|---|---|
| Test suite (the only gate) | `python3 test_bot.py` | exit 0, zero failures (the last line prints a count; the gate is **exit 0 + zero failures**, not the number) |
| Confirm exit code | `python3 test_bot.py; echo "rc=$?"` | `rc=0` |
| Locate a symbol | `grep -n "def liq_tier\|def kasih_j1\|def kasih2_wave_feats\|def liq_stage_events\|def build_liq_stage_alert" Super_stock.py` | six line numbers |

The test suite runs with **no internet** (all fetchers are injected). Any new test
must inject its inputs and touch no real state file / network.

## Suggested executor toolkit

- Load the repo skill **`wire-check`** before editing: prove the new J1-in-`k2`
  field is actually read on the live path (the header + `liq_tier`), not just
  written. This is the exact "imagined key / dead wire" class the skill guards.
- Load **`lock-and-mutate`** when writing the test: the lock must fail under a
  mutation (see Test plan). A lock that never fails is not a lock.

## Scope

**In scope** (the only files you may modify):
- `Super_stock.py` — `liq_stage_events` (stamp J1 into `k2`), `liq_tier` (read
  stored J1 for `Px`), `build_liq_stage_alert` (route the توليفة badge through one
  helper + gate it to `M5`/`Px`).
- `test_bot.py` — add the lock test (see Test plan).

**Out of scope** (do NOT touch, even though they look related):
- `kasih_j1` body — it is correct for `M5`; changing it risks the `M5` path.
- `kasih2_wave_feats` — the continuation math is published and locked; do not add
  fields to its return. Store J1 **outside** it, in the `M5` handler (Step 1).
- Any firing / dedup / selection logic (`scan_liq_stages` gating, `sent`,
  `pulse_ms`, `_inflow`, thresholds). This plan changes **display only**.
- `LOGIC_VERSION` — must NOT be bumped. If you find yourself wanting to, that is a
  STOP condition (you have strayed into selection logic).

## Git workflow

- Branch: `advisor/034-pulse-tier-badge`.
- Commit message must end with the two trailer lines the repo requires (copy from
  a recent `git log` entry): `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
  and the `Claude-Session:` line.
- Do NOT push or open a PR unless the operator instructs it.

## Steps

### Step 1: Stamp the M5 J1 result into `k2` so the pulse carries it

In `liq_stage_events`, the `if tag == "M5":` block (Current state block 2) builds
`_evd["k2"]` and saves `st["k2"]`. **`prev_close` is not on the event yet here**
(block 3), so you cannot call `kasih_j1(_evd)` at this point. Instead, compute the
two inputs J1 needs directly from data already in hand and store the J1 boolean:

- The pulse's gap uses `anchor_price / prev_close`. `anchor_price` is
  `st.get("anchor_price")`; `prev_close` is fetched in `scan_liq_stages` (block 3),
  **after** this function returns. Therefore compute and store J1 in
  `scan_liq_stages`, at the same loop that injects `prev_close` (block 3), where
  both `class` and `prev_close` are present on the `M5` event.

Concretely, in `scan_liq_stages`, block 3's loop, after `e["prev_close"] = _pc`,
add: for the `M5` event only, if it carries a `k2` dict, compute
`_j1 = kasih_j1(e)` and store both flags into that dict, e.g.
`e["k2"]["j1"], e["k2"]["j1_top"] = _j1`. Because `e["k2"]` **is the same dict
object** referenced by `st["k2"]` (set at block 2) — which is what the pulse later
copies as `_k2p` — the pulse's `k2` will then carry `j1`/`j1_top`.

**Verify this aliasing yourself before relying on it**: `st["k2"] = _evd["k2"]`
(block 2) makes `st["k2"]` and the emitted M5 event's `k2` the same object; and
the pulse does `_k2p = st.get("k2")` then `"k2": _k2p`. So mutating the M5
event's `k2` in `scan_liq_stages` mutates the object the next pulse will copy. If
in the live code these turn out to be distinct copies (e.g. a `dict(...)` or
`copy.deepcopy` was introduced), **STOP** and report — the fix must instead store
`j1`/`j1_top` into `st["k2"]` at the point state is persisted.

**Verify**: `grep -n '"j1"' Super_stock.py` → shows your new stamp site and (after
Step 2/3) the read sites. `python3 test_bot.py; echo rc=$?` → `rc=0` (existing
tests unbroken).

### Step 2: `liq_tier` reads the stored J1 for `Px`, keeps recomputing for `M5`

In `liq_tier` (block 4), replace the single line `j1 = kasih_j1(ev)[0]` with a
stage-aware read: for `stage == "Px"`, take `j1 = bool(k2.get("j1"))` (the value
stamped in Step 1); for `M5`, keep `j1 = kasih_j1(ev)[0]` byte-for-byte. Do not
change the قوي/ضعيف/متوسط thresholds. Fail-safe: a missing `k2["j1"]` (old
in-flight state) yields `False`, i.e. the current behavior — no worse than today.

**Verify**: reading `liq_tier(Px_event_with_k2_j1_true, green>=3)` returns
`("قوي", …)`. Covered by the Step-5 test.

### Step 3: Route the توليفة badge through one helper and gate it to `M5`/`Px`

In `build_liq_stage_alert` (block 6), the badge aggregation `_j1 = [kasih_j1(e)
for e in evs]` must (a) use the same stage-aware J1 as `liq_tier` and (b) only
consider `M5`/`Px` events — matching `liq_tier`'s own `("M5","Px")` guard, so the
badge and the tier agree on which events define J1 (this also fixes the M1
one-card-early badge).

Introduce one small helper used by both `liq_tier` and the header, e.g.
`_event_j1(ev) -> (bool, bool)` that returns `kasih_j1(ev)` for `M5` and
`(bool(k2.get("j1")), bool(k2.get("j1_top")))` for `Px`, and `(False, False)`
otherwise. Have `liq_tier` call it (Step 2 becomes `j1 = _event_j1(ev)[0]`) and
have the header compute `_j1 = [_event_j1(e) for e in evs if e.get("stage") in
("M5", "Px")]`. This makes J1 a single source (the repo's stated rule; see the
`kasih_j1` docstring "مصدرٌ واحدٌ لا نسختان").

**Verify**: `grep -n "kasih_j1" Super_stock.py` → after this step, the header no
longer calls `kasih_j1` directly (it calls `_event_j1`); `kasih_j1` is still
called inside `_event_j1` for `M5`. `python3 test_bot.py; echo rc=$?` → `rc=0`.

### Step 4: Run the full suite

**Verify**: `python3 test_bot.py; echo "rc=$?"` → `rc=0`, zero failures.

## Test plan

Add one lock test to `test_bot.py`, modeled on an existing `liq_tier` /
`kasih_j1` test (find one with `grep -n "liq_tier\|kasih_j1" test_bot.py` and copy
its structure and the repo's `check(...)` helper style).

The test must assert the **differentiating** behavior — a قوي pulse renders قوي,
not متوسط:

1. Build an `M5` event dict whose `class` is `("strong", …)`, `anchor_price` and
   `prev_close` give a gap ≥ 75% (so `kasih_j1` is `(True, True)`), and whose
   `k2` has `c3/c4/v2/v3` set so `green >= 3`. Run the Step-1 stamping path (or
   call `_event_j1`/`liq_tier` after stamping `k2["j1"]=True`) and assert
   `liq_tier(m5)[0] == "قوي"`.
2. Build a `Px` event carrying the **same** `k2` (now including `j1=True`) and the
   same `green>=3`, but **no** `class`. Assert `liq_tier(px)[0] == "قوي"`
   (this is the bug: today it returns "متوسط").
3. Build the same `Px` with `k2["j1"]` absent/False → assert it returns
   "متوسط"/"ضعيف" per the green count (fail-safe unchanged).
4. توليفة badge: build a card whose `evs` is a single `Px` with `k2["j1"]=True`
   and assert `build_liq_stage_alert([...])` contains "🥇 توليفة"; and a card whose
   `evs` is a single `M1` with a strong `class` asserts the badge does **not**
   appear (the one-window-early fix).

**Prove the lock fails under mutation** (per `lock-and-mutate`): temporarily revert
Step 2 (make `liq_tier` call `kasih_j1(ev)[0]` for `Px` again) and confirm the new
test **fails** (the قوي-pulse assertion). Restore. A lock that still passes after
that revert is not testing the fix — rewrite it so it differentiates.

**Verify**: `python3 test_bot.py; echo rc=$?` → `rc=0` with the new test present.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `python3 test_bot.py` exits 0, zero failures.
- [ ] `grep -n '"j1"' Super_stock.py` shows the stamp site (Step 1) and the read
      in `liq_tier`/`_event_j1` (Steps 2–3).
- [ ] The header (`build_liq_stage_alert`) no longer calls `kasih_j1` directly and
      restricts the badge to `M5`/`Px` events: `grep -n "kasih_j1\|_event_j1"
      Super_stock.py` shows `kasih_j1` only inside `_event_j1` (and its own def).
- [ ] The new test asserts a قوي `Px` renders "قوي", and it **fails** when Step 2
      is reverted (demonstrated).
- [ ] `git diff` shows `LOGIC_VERSION` unchanged and no edits outside the in-scope
      files (`git status`).
- [ ] `plans/README.md` status row updated.

## STOP conditions

Stop and report back (do not improvise) if:

- The excerpts in "Current state" don't match the live code (drift since
  `5cb88df`).
- `st["k2"]` and the emitted `M5` event's `k2` are **not** the same object (a
  copy was introduced), so mutating one does not affect the pulse — the aliasing
  assumption in Step 1 is false. Report and switch to stamping J1 at the state-
  persist point instead.
- The fix appears to require changing `kasih_j1`, `kasih2_wave_feats`, any firing/
  dedup logic, or bumping `LOGIC_VERSION`.
- The new test cannot be made to fail under the Step-2 revert (it isn't
  differentiating the bug).

## Maintenance notes

- This adds a `j1`/`j1_top` field to the stored `k2` dict. If `k2` is ever
  serialized to a state file and reloaded, old rows lack `j1` → they fall through
  to the fail-safe `False` (متوسط/ضعيف), same as before the fix — self-healing, no
  migration. Confirm `k2` is transient (per its docstring it is display-only and
  "الإطلاقُ والدِدوبُ لا يقرآنها").
- A reviewer should scrutinize: (1) that `M5` cards are byte-identical (the قوي
  logic there still flows through `kasih_j1`), and (2) that no firing/dedup path
  reads the new field (`wire-check`).
- Related but deliberately out of scope: `kasih_j1`'s two callers were unified
  into `_event_j1`; if a third J1 consumer is added later, it should also use
  `_event_j1` (single source).
