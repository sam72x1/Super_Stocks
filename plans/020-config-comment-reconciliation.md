# Plan 020: Reconcile CONFIG/header comments that mislabel soft gates as mandatory (توثيق يكذب على كوده)

> **Executor instructions**: Follow this plan step by step. This plan changes **only
> comments** — no executable code. Run `python3 test_bot.py` after and confirm exit 0
> (proving zero behavior change). If a test fails, a lock is asserting a comment string —
> STOP and report, do not edit the lock. When done, update this plan's status row in
> `plans/README.md`.
>
> **Drift check (run first)**: `git diff --stat 4e9b143..HEAD -- Super_stock.py`
> If Super_stock.py drifted near the CONFIG block (lines 9-490) or the gate functions
> (~3040-3140), re-read each cited line before editing; on a mismatch, STOP.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW (comments only)
- **Depends on**: none
- **Category**: docs
- **Planned at**: commit `4e9b143`, 2026-08-15

## Why this matters

This repo has a documented, recurring failure class the owner calls **"توثيق يكذب على
كوده"** (documentation that lies about its code) — a comment says a gate "rejects"/"is
mandatory" when the code below treats it as a soft deduction, or a comment states a
threshold that differs from the live value. Several were caught on 2026-08-13. Eight more
survive in `Super_stock.py`'s own module header and CONFIG comments. They mislead both the
owner and any automated executor: someone reasoning about "why is nothing passing" would
wrongly loosen a gate that never rejected, or mis-calibrate against a stale number. The
tie-breaker proving the *comments* are the wrong side: `analyze_one.py` already labels
these same gates as soft (نقص لا رفض), and the actual gate code appends `soft_fails`
without rejecting. This plan makes the comments tell the truth. **Zero behavior change.**

## Current state

The contradictions, each verified against both the claim line and the contradicting code:

| # | False claim (comment) | Contradicting code (soft/actual) |
|---|-----------------------|----------------------------------|
| 1 | `Super_stock.py:9-13` header: M6/M7 "شرطان إلزاميان … **ويستبعدان الأسهم**" | `Super_stock.py:3045-3054` — M6/M7 → `soft_fails.append(...)`, no reject (line 3046 comment itself says "كانت رفضًا صلبًا؛ صارت نقصًا") |
| 2 | `Super_stock.py:245-247`: "بوابات البنية الأساسية (**إلزامية دائمًا**) … M6 … M7 … M8" | same soft handling `3045-3065`; also `Super_stock.py:239` `WATCH_SOFT_GATES` lists M6/M7 as soft |
| 3 | `Super_stock.py:152`: `# M11: تقاطع MACD إيجابي إلزامي` | `Super_stock.py:3111-3112` — M11 → `soft_fails.append(...)`, no reject; `analyze_one.py:258` calls it "لينة" |
| 4 | `Super_stock.py:150,153`: section "بوابات فيصل الإلزامية … **بصرامة**" over M12 | `Super_stock.py:3129-3139` — M12 → `soft_fails.append(...)`; `analyze_one.py:265` soft |
| 5 | `Super_stock.py:151`: `# M10: RSI لازم في التشبع (27) وتحت السقف (40)` | hard cutoffs are **32/50** (`Super_stock.py:145` `RSI_OS_HARD=32`, `:148` `RSI_NOW_HARD=50`, reject at `3091-3093`/`3098-3100`); 27/40 are the *soft* band |
| 6 | `Super_stock.py:244`: comment "(مع **SCORE_MIN=35** للجودة)" | `Super_stock.py:231` `"SCORE_MIN": 45` (live value, comment there: "v2.7: رُفع لـ45") |
| 7 | `Super_stock.py:54,58` header: "أفضل **10** أسهم" / "القائمة دائماً ≤ **10**" | `Super_stock.py:280` `"WATCHLIST_SIZE": 15` (owner decision 2026-08-12) |
| 8 | `Super_stock.py:3056`: `# ---- M8: … — إلزامي (v2.4 نسخة B) ----` | reject only under `if CONFIG.get("GAP_REQUIRED", False):` and `Super_stock.py:434` sets `"GAP_REQUIRED": False` |

Exact excerpts of the two anchor regions (read the file to see them in context):

`Super_stock.py:150-153`:
```python
    # ---- بوابات فيصل الإلزامية (v2.6: مطابقة الشروط الستة بصرامة) ----
    "RSI_GATE_REQUIRED": True,   # M10: RSI لازم في التشبع (27) وتحت السقف (40)
    "MACD_GATE_REQUIRED": True,  # M11: تقاطع MACD إيجابي إلزامي
    "MA_GATE_REQUIRED": True,    # M12: السعر على المتوسط الأسي 30/50
```
`Super_stock.py:244-247`:
```python
    "WATCH_MAX_FAILS": 3,        # الوسط: السهم باقي له 2-3 بوابات بالكثير
                                 # (مع SCORE_MIN=35 للجودة). أنزله لـ2 لأصرم
    # بوابات البنية الأساسية (إلزامية دائمًا — فشلها = ليس سهم ارتكاز):
    # M1 سعر · M2 هبوط · M3 انفجار · M4 قاعدة/طزاجة · M5 سيولة ·
    # M6 توافق فريمات · M7 نمط شمعة · M8 فجوة طازجة (لو مفعّلة).
```

**Note**: the M13 "يرفض الشورت العالي" lie was already fixed (it now carries a dated 🔴
correction at `Super_stock.py:154-158`). Match that **exact style** for these fixes:
correct the text, and where useful add a short dated note that the *text* was corrected
and no behavior changed.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Tests (proves zero behavior change) | `python3 test_bot.py` | exit 0 |
| Confirm no code lines changed | `git diff Super_stock.py` | only comment characters differ |

## Scope

**In scope**:
- `Super_stock.py` — comments only, at the 8 locations above.

**Out of scope**:
- Any executable line, any CONFIG **value** (do not change `45`, `15`, `32`, `50`, thresholds).
- The gate functions themselves. This plan does not change what any gate does.
- `analyze_one.py` — already correct.

## Git workflow

- Branch: `advisor/020-config-comment-reconciliation`
- Commit trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- Do NOT push or open a PR.

## Steps

### Step 1: Fix the M10/M11/M12 CONFIG comments (rows 3, 4, 5)

At `Super_stock.py:150-153`, reword so the mandatory-vs-soft split is honest. Suggested:
```python
    # ---- بوابات فيصل: M10-M12 نواقص لينة (نقص لا رفض) — تُحسَب ضمن WATCH_MAX_FAILS ----
    "RSI_GATE_REQUIRED": True,   # M10 (لين): قاع RSI مثالي ≤27 وحالي <40 — نقص لا رفض.
                                 #   الرفض الصلب على RSI_OS_HARD=32 / RSI_NOW_HARD=50 فقط.
    "MACD_GATE_REQUIRED": True,  # M11 (لين): تقاطع MACD إيجابي — نقص لا رفض.
    "MA_GATE_REQUIRED": True,    # M12 (لين): السعر على المتوسط الأسي 30/50 — نقص لا رفض.
```
Keep the flag names/values (`True`) exactly — only the trailing comments and the section
header change.

### Step 2: Fix the `SCORE_MIN=35` stale number (row 6)

At `Super_stock.py:244`, change `SCORE_MIN=35` → `SCORE_MIN=45` in the comment (the live
value at line 231 is 45).

### Step 3: Fix the "إلزامية دائمًا" basic-structure list (rows 1, 2)

At `Super_stock.py:245-247`, keep only the true-hard gates (M1-M5) as "إلزامية"; move
M6/M7/M8 to a "soft confirmation" note. Suggested:
```python
    # بوابات الهوية الصلبة (فشلها = ليس سهم ارتكاز): M1 سعر · M2 هبوط · M3 انفجار ·
    #   M4 قاعدة/طزاجة · M5 سيولة (+ أرضية RSI الصلبة 32/50).
    # بوابات تأكيد لينة (نقص لا رفض، ضمن WATCH_MAX_FAILS): M6 توافق فريمات · M7 نمط
    #   شمعة · M8 فجوة طازجة (مطفأة افتراضيًّا، GAP_REQUIRED=False) · M9-M13.
```
Then fix the module header at `Super_stock.py:9-13`: reword the v2.3 changelog so M6/M7
are described as soft confirmations (نقص لا رفض) rather than "إلزاميان … يستبعدان".

### Step 4: Fix the capacity "10" → "15" in the header (row 7)

At `Super_stock.py:54,58`, change the v2.0 changelog text from "أفضل 10 أسهم" / "القائمة
دائماً ≤ 10" to reference `WATCHLIST_SIZE` (=15), e.g. "أفضل `WATCHLIST_SIZE` أسهم
(=15، قرار المالك 2026-08-12)" / "القائمة ≤ `WATCHLIST_SIZE`". Do not touch the value at
line 280.

### Step 5: Fix the M8 inline "إلزامي" label (row 8)

At `Super_stock.py:3056`, change the M8 header comment to reflect that it is off by
default:
```python
    # ---- M8: فجوة سعرية معتبرة حديثة — بوابة اختيارية مطفأة افتراضيًّا (GAP_REQUIRED=False): نقاط فقط ----
```

### Step 6: Verify zero behavior change

**Verify**: `python3 test_bot.py` → exit 0. `git diff Super_stock.py` shows only comment
text changed (no code token on any line moved). If any test fails, a lock is asserting one
of these comment strings — STOP and report which; do not edit the lock.

## Test plan

- No new tests (comments only). The verification is `python3 test_bot.py` exit 0 (behavior
  unchanged) plus a manual `git diff` read confirming only comments changed.

## Done criteria

- [ ] All 8 comment locations corrected to match the code
- [ ] No CONFIG **value** changed; no executable line changed (`git diff` = comments only)
- [ ] `python3 test_bot.py` exits 0
- [ ] `git status` shows only `Super_stock.py`
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report if:
- `python3 test_bot.py` fails after a comment edit — a text-lock asserts the old comment;
  report which lock and which comment (the fix may need to update the lock's expected
  string *with* the corrected text, but that is a separate judgment — do not blind-edit it).
- Re-reading a gate function shows it actually **does** reject (i.e. the comment was
  right and the earlier analysis wrong) — report the discrepancy instead of "fixing" a
  true comment.

## Maintenance notes

- These comments feed both the owner and future executors as ground truth; keeping them
  honest is the whole point of the exercise. When a gate's hard/soft status changes,
  update the comment in the same commit.
- Reviewer should confirm the diff is comments-only and that no CONFIG value moved.
