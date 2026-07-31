#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⚡ T-EVENT-EXEC — أدوات اختبار **التوقيت والتنفيذ** (`event_exec_prereg.md`).

**السؤال:** هل حدثُ الاشتعال يضيف توقّعًا **قابلًا للتنفيذ** فوق كون ARMED؟
وهي أوّل اختبارٍ **مباشر** لدعوى «الحافة = التوقيت» بعد أربعة عشر تأكيدًا أنها
ليست في الاختيار.

🔒 **بحث/قياس — خارج الإنتاج تمامًا.** الزناد **ليس منسوخًا**: تُستدعى دوالّ
الإنتاج نفسها (`_ignition_break_level` · `_ignition_signal` · `_operator_blocks`)
فيستحيل أن ينحرف المقيس عن المُشغَّل. والجالبات هنا **تاريخية بحثية** لأن نظيراتها
الإنتاجية لحظيةٌ بالبناء (تقرأ `time.time()`).

⚠️ **صفر ضبطٍ للعتبات** — أيّ تعديلٍ بعد رؤية الأرقام = `p-hacking` صريح.
"""
from __future__ import annotations

import datetime as dt
import os
import time
from zoneinfo import ZoneInfo

import requests

NY = ZoneInfo("America/New_York")
RADAR_WINDOW = 30      # نافذة الرادار الحيّ: `polygon_minute_bars(sym, minutes=30)`
MIN_BARS = 6           # `_ignition_signal(min_bars=6)`
MAX_QUOTE_AGE_MS = 5_000   # §④: «أوّل ask عمره ≤5 ثوانٍ» — مسجَّل، لا يُلمَس

_CALLS = {"aggs": 0, "quotes": 0, "trades": 0, "fail": 0}


# ═══════════════════ دوالّ نقيّة (بلا شبكة · قابلة للاختبار) ═══════════════════
def ny_session_key(ts_ms: int):
    """(تاريخ الجلسة ISO، دقيقة اليوم بتوقيت نيويورك) لطابعٍ زمنيّ بالملّي.
    **يعيد `None` لما خارج الجلسة النظامية** (‏09:30–16:00 نيويورك) — فالرادار الحيّ
    يعمل داخلها، وقياسُه على الممتدّ يقيس شيئًا لا يقع."""
    try:
        d = dt.datetime.fromtimestamp(int(ts_ms) / 1000.0, tz=NY)
    except (TypeError, ValueError, OSError, OverflowError):
        return None
    mod = d.hour * 60 + d.minute
    if mod < 9 * 60 + 30 or mod >= 16 * 60:
        return None
    return (d.date().isoformat(), mod)


def group_sessions(bars):
    """يقسّم شموع الدقيقة إلى جلساتٍ نظامية: `{تاريخ: [شمعة…]}` مرتَّبةً زمنيًّا.
    كلُّ شمعةٍ تكتسب `sess`/`mod` (دقيقة اليوم) لتُستعمل في المطابقة الزمنية."""
    out: dict[str, list] = {}
    for b in (bars or []):
        k = ny_session_key(b.get("t"))
        if k is None:
            continue
        day, mod = k
        out.setdefault(day, []).append(dict(b, sess=day, mod=mod))
    for day in out:
        out[day].sort(key=lambda b: b["t"])
    return out


def replay_trigger(session_bars, break_level, signal_fn, vol_mult=3.0,
                   window=RADAR_WINDOW, min_bars=MIN_BARS):
    """يُعيد تشغيل **زناد الرادار الحيّ** على جلسةٍ كاملة، دقيقةً بدقيقة.

    الرادار يستدعي `polygon_minute_bars(sym, minutes=30)` ثم `_ignition_signal`.
    🔴 **تصحيح (مراجعة Codex الثانية): النافذة زمنيّة لا عدديّة.** كانت `session_bars[
    i-window+1 : i+1]` = آخر **30 شمعةً موجودة** مهما امتدّ الزمن الذي تغطّيه — وفي
    سهمٍ رقيق (وهو كوننا كلُّه) قد تغطّي ستُّ شمعاتٍ ساعتين، فيرى التاريخيُّ سياقًا
    لا يراه الحيّ أبدًا. الآن **آخر `window` دقيقة بالطابع الزمنيّ** حرفيًّا كالحيّ،
    فالشموع الغائبة (دقائق بلا تداول) تبقى غائبة في الطرفين.
    يرجّع `(فهرس شمعة الزناد، الإشارة)` لأوّل اشتعال — **أوّل حدثٍ لكل جلسة** كما
    سُجِّل — أو `None`.

    `signal_fn` مُحقَن ليكون **دالّة الإنتاج نفسها** (لا نسخة منها)."""
    if not session_bars or not break_level:
        return None
    span = int(window) * 60_000                 # نافذةٌ زمنيّة بالملّي ثانية
    for i in range(len(session_bars)):
        t_i = session_bars[i].get("t")
        if t_i is None:                         # بلا طابعٍ لا نخمّن نافذةً زمنية
            continue
        lo = int(t_i) - span + 60_000           # الشمعة الحالية داخل النافذة
        win = [b for b in session_bars[:i + 1]
               if b.get("t") is not None and int(b["t"]) >= lo]
        if len(win) < min_bars:
            continue
        sig = signal_fn(win, break_level, vol_mult=vol_mult)
        if sig:
            return (i, sig)
    return None


def cross_trigger(session_bars, break_level, window=RADAR_WINDOW,
                  min_bars=MIN_BARS):
    """ذراع **E-CROSS**: عبورٌ بسيط للمستوى صاعدًا — **بلا** شرط قفزة الحجم وبلا
    شرط الاتجاه. يعزل السؤال: «هل الـ3× تضيف شيئًا فوق مجرّد العبور؟».
    نفس شرط النافذة الدنيا حتى تُقارَن الذراعان على أرضٍ واحدة."""
    if not session_bars or not break_level:
        return None
    for i in range(len(session_bars)):
        if i + 1 < min_bars:
            continue
        try:
            c = float(session_bars[i]["c"])
        except (TypeError, ValueError, KeyError):
            continue
        if c > float(break_level):
            return (i, {"price": round(c, 4),
                        "usd": round(c * float(session_bars[i].get("v") or 0))})
    return None


def band_triggers(session_bars, break_level, signal_fn, vol_mult=3.0,
                  lo=0.99, hi=1.01, window=RADAR_WINDOW, min_bars=MIN_BARS):
    """🔬 **‏T-NEARMISS** — أوّل دقيقةٍ في **كلّ** من الذراعين داخل الجلسة.

    الذراعان لا يفترقان إلا في **أيّ جانبٍ من الخطّ** وقع الإغلاق:
      • **`cross`** ⇒ الإغلاق في `(break, break×hi]` — **عبر بشعرة**.
      • **`miss`**  ⇒ الإغلاق في `[break×lo, break]` — **وقف تحته بشعرة**.

    🔑 **وشرطا الحجم والاتجاه يُقيَّمان بدالّة الإنتاج نفسها** (`signal_fn` مُحقَنة)
    بمستوًى **مُخفَّض** `break×lo` — فتشترك الذراعان في الحجم والاتجاه والوقت والسهم
    واليوم، **ولا نُعيد تطبيق أيّ شرطٍ يدويًّا**.

    يرجّع `{"cross": (فهرس، إشارة)، "miss": (…)}` بما وُجد. دالّة **نقيّة**."""
    out = {}
    if not session_bars or not break_level or break_level <= 0:
        return out
    probe = float(break_level) * float(lo)
    for i in range(len(session_bars)):
        if len(out) == 2:
            break
        win = session_bars[max(0, i - window + 1): i + 1]
        if len(win) < min_bars:
            continue
        sig = signal_fn(win, probe, vol_mult=vol_mult)
        if not sig:
            continue
        try:
            c = float(session_bars[i]["c"])
        except (TypeError, ValueError, KeyError):
            continue
        if break_level < c <= float(break_level) * float(hi):
            out.setdefault("cross", (i, sig))
        elif float(break_level) * float(lo) <= c <= break_level:
            out.setdefault("miss", (i, sig))
    return out


def relabel(bars_all, bars_reg, entry, stop, thresholds=(30.0, 50.0, 100.0)):
    """🔬 **‏T-LABEL-AUDIT** — الوسم على **الجلسة النظامية** مقابل **كلّ الدقائق**.

    لكلّ مجموعةٍ يُحسب: أقصى صعودٍ **قبل** ضرب الوقف · وأقصى صعود **بعده** (‏«خرجنا
    ثم انفجر») · وفهرسُ الوقف (ليُقارَن تقديمُه). ثم تُقارَن العتبات.

    ⚠️ **الوسم ليس ربحًا:** بلوغُ عتبةٍ في الافتر لا يعني إمكان البيع عندها — ولذلك
    يُرجَع **حجمُ الدقيقة** التي بلغت العتبة ليُنشَر معها. دالّة **نقيّة**."""
    def _scan(bars):
        if not bars or not entry or entry <= 0:
            return None
        pre, post, hit_v, stopped = 0.0, 0.0, None, False
        for b in bars:
            try:
                h, lo_ = float(b["h"]), float(b["l"])
            except (TypeError, ValueError, KeyError):
                continue
            g = (h / float(entry) - 1.0) * 100.0
            if stopped:
                post = max(post, g)
                continue
            if lo_ <= float(stop):
                stopped = True
                continue
            if g > pre:
                pre, hit_v = g, b.get("v")
        return {"pre": round(pre, 2), "post": round(post, 2),
                "stopped": stopped, "peak_vol": hit_v}
    reg, ext = _scan(bars_reg), _scan(bars_all)
    if reg is None or ext is None:
        return None
    flips = {}
    for t in thresholds:
        flips[t] = {"appeared": (ext["pre"] >= t > reg["pre"]),
                    "vanished": (reg["pre"] >= t > ext["pre"])}
    return {"reg": reg, "ext": ext, "flips": flips,
            "stop_earlier": bool(ext["stopped"] and not reg["stopped"])}


def pick_entry_quote(quotes, trigger_end_ms, max_age_ms=MAX_QUOTE_AGE_MS):
    """§④ **قاعدة الدخول المسجَّلة:** أوّل اقتباسٍ بعد إغلاق شمعة الزناد له `ask`
    صالح **وعمرُه ‏≤5 ثوانٍ** عن لحظة القرار.

    🔴 **وغيابُه ليس ثغرةً تُسدّ بسعرٍ مريح** — يُعاد `None` ويُسجَّل
    `non_executable` ويبقى **في المقام**. (هذا شرطٌ مسجَّل، لا اجتهاد.)"""
    if not quotes:
        return None
    for q in quotes:
        ts = q.get("t")
        ask, bid = q.get("ask"), q.get("bid")
        if ts is None or not ask or ask <= 0:
            continue
        if ts < trigger_end_ms:
            continue
        if ts - trigger_end_ms > max_age_ms:
            return None            # مرّت النافذة بلا اقتباسٍ صالح
        return {"ask": float(ask), "bid": (float(bid) if bid else None),
                "t": ts, "age_ms": ts - trigger_end_ms}
    return None


def runner_exit(bars, t1, t3, reclaim_min=15, hold_sessions=5):
    """🎚️ **‏T-MANAGE-25 · السياسة ب** — مسارُ **الربع المُمتَّع** بعد بيع 75% عند
    `t1`. `bars` = شموع الدقيقة **من الدقيقة التالية لبلوغ الهدف**، وكلٌّ يحمل `sess`.

    تخرج بأوّل ما يقع (المُسجَّل في `manage25_prereg.md` §②، ولا يُختار بعد الأرقام):
      **①** **كسرُ `t1`** بإغلاق دقيقةٍ تحته **بلا استعادةٍ** (إغلاق فوقه) خلال
          `reclaim_min` دقيقة ⇒ الخروج عند إغلاق دقيقة المهلة.
      **②** بلوغ `t3` (لمسةً) ⇒ الخروج عنده.
      **③** انقضاء `hold_sessions` جلسة ⇒ الخروج عند آخر إغلاقٍ متاح.
    يرجّع `(سبب، سعر)` أو `None` لو لا شموع. **الوقف على الربع = `t1`** لا الوقف
    الأصليّ (اختيارٌ مسجَّل، مصرَّحٌ به). دالّة **نقيّة** بلا شبكة."""
    if not bars:
        return None
    sess0 = bars[0].get("sess")
    seen, broke_at = [sess0], None
    for b in bars:
        s = b.get("sess")
        if s not in seen:
            seen.append(s)
            if len(seen) > hold_sessions:
                return ("time", float(bars[bars.index(b) - 1]["c"]))
        try:
            c, h = float(b["c"]), float(b["h"])
        except (TypeError, ValueError, KeyError):
            continue
        if t3 and h >= float(t3):
            return ("t3", float(t3))
        if broke_at is None:
            if c < float(t1):
                broke_at = b["t"]
        else:
            if c >= float(t1):
                broke_at = None                      # استعادةٌ داخل المهلة
            elif b["t"] - broke_at >= reclaim_min * 60_000:
                return ("broke", c)                  # كُسر ولم يُستعَد
    return ("end", float(bars[-1]["c"]))


def manage_b_r(raw_a_ret, t1_ret, runner_ret, spr, frac=0.75):
    """صافي R للسياسة **ب** مركَّبًا من جزأين بتكلفتَي خروجٍ **مستقلّتين**.

    `t1_ret`/`runner_ret` = عائدا الجزأين **خامَين** (قبل التكاليف) بالنسبة المئوية.
    كلُّ خروجٍ يدفع **نصف السبريد** ⇒ **الإدارة ليست مجّانية** (خروجان = تكلفتان).
    وصفقةٌ لم تبلغ `t1` ⇒ **ب = أ حرفيًّا** (يُمرَّر `runner_ret=None`)."""
    def _net(r):
        return (1.0 + float(r) / 100.0) * (1.0 - float(spr or 0.0) / 2.0) - 1.0
    if runner_ret is None:
        return _net(raw_a_ret) * 100.0
    return (frac * _net(t1_ret) + (1.0 - frac) * _net(runner_ret)) * 100.0


def spread_frac(q):
    """كسرُ السبريد عند الدخول `(ask − bid) / ask` — تكلفة الخروج الصريحة.
    بلا `bid` صالح ⇒ `None` (لا يُخمَّن؛ الصفقة تُعدّ غير قابلةٍ للتسعير)."""
    try:
        a, b = float(q["ask"]), float(q["bid"])
        if a <= 0 or b <= 0 or b > a:
            return None
        return (a - b) / a
    except (TypeError, ValueError, KeyError):
        return None


def net_r(raw_ret_pct, entry_ask, stop, spr):
    """**صافي R بعد التكاليف.**

    الدخول عند `ask` **حقيقيّ** ⇒ نصفُ السبريد مدفوعٌ واقعًا ولا يُحتسب مرّتين.
    والخروج يُخصَم منه **نصف السبريد المقيس عند الدخول**:
    `صافي = (1 + خام/100) × (1 − s/2) − 1`.
    والمخاطرة `(ask − stop)/ask` ⇒ **الوقف = −1R بالبناء** قبل التكاليف."""
    try:
        e, st = float(entry_ask), float(stop)
        if e <= 0 or e - st <= 0:
            return None
        s = float(spr or 0.0)
        net_pct = ((1.0 + float(raw_ret_pct) / 100.0) * (1.0 - s / 2.0) - 1.0) * 100.0
        return net_pct / ((e - st) / e * 100.0)
    except (TypeError, ValueError):
        return None


def match_pseudo(real_day, quiet_days):
    """**‏E-PSEUDO** (فكرة المراجِع `case-crossover`): أقرب جلسة ARMED **لنفس الرمز**
    **بلا زناد**، وتُؤخَذ عندها **نفس دقيقة الساعة**.

    ⚖️ ولماذا هي أثمن ما في التصميم: المقارنة داخل الرمز نفسه **تضبط تلقائيًّا**
    الهوية والفلوت والقطاع والتاريخ ⇒ **يبقى الفرق = قيمة التوقيت وحدها**.
    الأقرب زمنيًّا، وعند التساوي **الأسبق** (حتميّ). `None` لو لا يومَ مطابقًا."""
    if not quiet_days:
        return None
    return min(sorted(quiet_days), key=lambda d: (abs(_dnum(d) - _dnum(real_day)), d))


def _dnum(day_iso):
    try:
        return dt.date.fromisoformat(str(day_iso)).toordinal()
    except (TypeError, ValueError):
        return 0


def scale_mismatch(first_session_bars, plan_entry, tol=0.5):
    """§⑩-1 **حارس اختلاف مقياس التعديل:** كون ARMED مُجمَّد `as-of 2026-07-22` بينما
    شموع الدقيقة تُجلَب اليوم — فتقسيمٌ بينهما يجعل المقياسَين مختلفَين **بصمت**،
    فيُقارَن مستوًى بمستوًى خاطئ وتخرج أرقامٌ لا معنى لها.

    يُقارَن **وسيط إغلاقات أوّل جلسةٍ مسلَّحة** (= يوم الإشارة نفسه) بـ**سعر خطّة
    الدخول** المخزَّن على مقياس اللقطة. تجاوزُ `tol` (‏±50%) ⇒ **يُستبعَد ويُعدّ**.

    ⚖️ **ولماذا هذي المقارنة بالذات:** تُجرى **مرّةً على يوم الإشارة** لا كلَّ جلسة —
    فالسعر يتحرّك مشروعًا بعد الإشارة (وارتفاعُه هو ما نبحث عنه!) وفحصُه يوميًّا كان
    سيُقصي الرابحين. **وأيّ تقسيمٍ حقيقيّ ‏≥2×** فيقع خارج ‏±50% حتمًا.
    بيانات ناقصة ⇒ `False` (لا نُسقط بالشكّ وحده)."""
    try:
        cl = [float(b["c"]) for b in (first_session_bars or [])
              if b.get("c") is not None]
        e = float(plan_entry or 0)
        if not cl or e <= 0:
            return False
        med = sorted(cl)[len(cl) // 2]
        return abs(med / e - 1.0) > float(tol)
    except (TypeError, ValueError, KeyError):
        return False


def concentration(rows, key):
    """§⑧-5: أكبر حصّةٍ من **الربح** يصنعها مفتاحٌ واحد (رمز/جلسة).
    تُحسب على الموجب فقط — «حصّة من الربح» لا من الصافي (فالمقام لا ينقلب)."""
    tot, by = 0.0, {}
    for r in rows:
        v = r.get("net_r")
        if v is None or v <= 0:
            continue
        tot += v
        by[r.get(key)] = by.get(r.get(key), 0.0) + v
    if tot <= 0 or not by:
        return 0.0
    return max(by.values()) / tot


def cluster_bootstrap_mean(rows, key="symbol", n=10000, seed=99991, level=0.95):
    """§⑦: `cluster bootstrap` بالرمز على **متوسط** صافي R (صفقات الرمز مرتبطة)."""
    import random
    groups: dict = {}
    for r in rows:
        if r.get("net_r") is not None:
            groups.setdefault(r.get(key), []).append(float(r["net_r"]))
    ks = sorted(groups)
    if not ks:
        return {"lo": 0.0, "hi": 0.0, "mean": 0.0, "n": 0, "k": 0}
    flat = [v for k in ks for v in groups[k]]
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        vals = []
        for _ in ks:
            vals.extend(groups[ks[rng.randrange(len(ks))]])
        out.append(sum(vals) / len(vals) if vals else 0.0)
    out.sort()
    a = (1.0 - level) / 2.0

    def _p(q):
        return out[min(max(int(round(q * (len(out) - 1))), 0), len(out) - 1)]
    return {"lo": _p(a), "hi": _p(1.0 - a), "mean": sum(flat) / len(flat),
            "n": len(flat), "k": len(ks)}


def paired_diff(real_rows, pseudo_rows, n=10000, seed=13337, level=0.95):
    """الفرق **المزدوج داخل الرمز** `E-REAL − E-PSEUDO` بإعادة معاينة الرموز.
    المزاوجة بـ`(رمز، مفتاح الحدث)` فلا يُقارَن حدثٌ بغير نظيره."""
    import random
    pmap = {(r.get("symbol"), r.get("pair_key")): r for r in pseudo_rows}
    pairs: dict = {}
    for r in real_rows:
        p = pmap.get((r.get("symbol"), r.get("pair_key")))
        if p is None or r.get("net_r") is None or p.get("net_r") is None:
            continue
        pairs.setdefault(r["symbol"], []).append(float(r["net_r"]) - float(p["net_r"]))
    ks = sorted(pairs)
    if not ks:
        return {"lo": 0.0, "hi": 0.0, "mean": 0.0, "n": 0, "k": 0}
    flat = [v for k in ks for v in pairs[k]]
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        vals = []
        for _ in ks:
            vals.extend(pairs[ks[rng.randrange(len(ks))]])
        out.append(sum(vals) / len(vals) if vals else 0.0)
    out.sort()
    a = (1.0 - level) / 2.0

    def _p(q):
        return out[min(max(int(round(q * (len(out) - 1))), 0), len(out) - 1)]
    return {"lo": _p(a), "hi": _p(1.0 - a), "mean": sum(flat) / len(flat),
            "n": len(flat), "k": len(ks)}


# ═══════════════════ جالبات تاريخية (بحثية · فاشلة-آمنة) ═══════════════════
def has_key():
    """هل مفتاح Polygon متاح؟ (يُقرأ **وقت النداء** كنمط الإنتاج)."""
    return bool(_key())


def _key():
    return os.environ.get("POLYGON_API_KEY", "").strip()


def _get(url, params=None, timeout=25):
    k = _key()
    if not k:
        return None
    try:
        r = requests.get(url, params=params, timeout=timeout,
                         headers={"Authorization": f"Bearer {k}"})
        if r.status_code != 200:
            _CALLS["fail"] += 1
            return None
        return r.json() or {}
    except Exception:
        _CALLS["fail"] += 1
        return None


def hist_minute_bars(sym, frm_iso, to_iso, cap_pages=12, pause=0.06):
    """شموع الدقيقة **التاريخية** لمدًى من التواريخ (نظير `polygon_minute_bars`
    اللحظيّة التي تقرأ `time.time()` فلا تصلح للتاريخ). `adjusted=true` **عمدًا**
    ليطابق مقياس اللقطة المجمَّدة (`auto_adjust=True`) — والحارس `scale_mismatch`
    يلتقط ما تبقّى. فاشل-آمن ⇒ `None`."""
    url = (f"https://api.polygon.io/v2/aggs/ticker/{str(sym).upper()}"
           f"/range/1/minute/{frm_iso}/{to_iso}")
    params = {"adjusted": "true", "sort": "asc", "limit": 50000}
    bars, page = [], 0
    while url and page < cap_pages:
        j = _get(url, params=params)
        _CALLS["aggs"] += 1
        if not j:
            return bars or None
        for b in (j.get("results") or []):
            if b.get("c") is not None and b.get("t") is not None:
                bars.append({"o": b.get("o"), "h": b.get("h"), "l": b.get("l"),
                             "c": b.get("c"), "v": b.get("v"), "t": b.get("t")})
        url, params, page = j.get("next_url"), {"limit": 50000}, page + 1
        if url:
            time.sleep(pause)
    return bars or None


def hist_quotes(sym, start_ms, end_ms, limit=200, pause=0.04):
    """‏NBBO **التاريخيّ** (`/v3/quotes`) — القناة التي أثبت مِجَسّ 2026-07-30 أنها
    متاحة لاشتراكنا ‏≥1200 يومًا **وللمغمورة**. الطوابع بالنانو ⇒ تُحوَّل للملّي."""
    j = _get(f"https://api.polygon.io/v3/quotes/{str(sym).upper()}",
             {"timestamp.gte": int(start_ms) * 1_000_000,
              "timestamp.lt": int(end_ms) * 1_000_000,
              "order": "asc", "limit": int(limit)})
    _CALLS["quotes"] += 1
    time.sleep(pause)
    if not j:
        return None
    out = []
    for q in (j.get("results") or []):
        ts = q.get("sip_timestamp") or q.get("participant_timestamp")
        if ts is None:
            continue
        out.append({"bid": q.get("bid_price"), "ask": q.get("ask_price"),
                    "t": int(ts) // 1_000_000})
    return out or None


def hist_trades(sym, start_ms, end_ms, limit=500, pause=0.04):
    """الصفقات التاريخية للحظة الزناد — تُغذّي `_operator_blocks` الإنتاجيّة
    (الذراع **الثانوية** `E-OPERATOR`)."""
    j = _get(f"https://api.polygon.io/v3/trades/{str(sym).upper()}",
             {"timestamp.gte": int(start_ms) * 1_000_000,
              "timestamp.lt": int(end_ms) * 1_000_000,
              "order": "asc", "limit": int(limit)})
    _CALLS["trades"] += 1
    time.sleep(pause)
    if not j:
        return None
    out = [{"p": t.get("price"), "s": t.get("size")}
           for t in (j.get("results") or [])
           if t.get("price") is not None and t.get("size") is not None]
    return out or None


def call_stats():
    return dict(_CALLS)
