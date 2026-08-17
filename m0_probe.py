#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🚨🔬 **مِجَسُّ M0** — هل إشعارُ ما قبل الإغلاق يستحقّ خطرَه؟ ‏+ تغطيةُ المضارب.

عقدُه `m0_prereg.md` **مدفوعٌ قبل أيّ رقم**. يقيس بشموع **الثانية** لا بكسرٍ من
الدقيقة (‏§②) ⇒ **يُوقَف بخروجٍ غيرِ صفريّ إن تعذّرت** ولا يُنشَر رقم.

🔒 **قراءةٌ/قياسٌ فقط:** لا يكتب حالةً ولا يرسل تلغرامًا ولا يمسّ فرزًا ولا جذرًا.

⚖️ **و`E1` تُقفَل على الإنتاج في التشغيلة نفسِها** (‏`_lock_e1`) — وهذا **ليس
«نسخةً تُطارد الإنتاج»**: المقيسُ هو **المشحونُ اليوم** بأمر المالك، فلو تفرّق
المِجَسُّ عن `liq_stage_events` لصار يقيس شيئًا آخرَ ويسمّيه باسمه ⇒ **خروج 3**.
"""
import os
import statistics as stt
import sys
import time

import requests

os.environ.setdefault("SCREENER_MODE", "PROBE")
import Super_stock as bot                                          # noqa: E402
import liq_move_probe as LM                                        # noqa: E402

WINDOW_MIN = 480            # 🔒 نفسُ نافذةِ `liq_move_probe` حرفيًّا
SEC_CAP = 600               # سقفُ نداءاتِ شموع الثانية — **يُعلَن قصُّه**
OP_SAMPLE = 12              # عيّنةُ قياسِ تغطية المضارب — **تُعلَن**
BUDGET_SEC = 900
WORKERS = 8
LAT_SAMPLE = 3              # عيّنةُ قياسِ كلفة الزمن لكلّ سقف — **تُعلَن**
# 🔒 والسقفُ المشحونُ **داخلٌ في القائمة بالبناء** فلا يصير المعيارُ ② بلا رقم.
OP_CAPS = tuple(sorted({250, 5_000, 20_000, 50_000,
                        int(bot.LIQ_OPERATOR_TRADES)}))

# ⚙️ **الأذرعُ مثبَّتةٌ في `m0_prereg.md §④` — ولا تُزاد ذراعٌ بعد الأرقام.**
ARMS = {
    "E0": {"off": True},
    "E1": {},                                  # 🥇 المشحونُ الآن
    "E2": {"floor_mult": 2.0},                 # سيولةٌ ضِعفا الأرضية
    "E3": {"min_elapsed": 20},                 # بعد عشرين ثانيةً من الدقيقة
}
ARM_DESC = {
    "E0": "بلا `M0` إطلاقًا (الأساسُ = `M1` وحده)",
    "E1": "🥇 **المشحونُ الآن**: القفزةُ والأرضيةُ والاتجاهُ والرفعةُ ‏≥5%",
    "E2": "`E1` ‏+ سيولةٌ ضِعفا الأرضية (‏$60 ألفًا)",
    "E3": "`E1` ‏+ مضيُّ عشرين ثانيةً فأكثر",
}


# ─────────────────────────── الشبكة (شموعُ الثانية) ───────────────────────────
def second_bars(sym, t0_ms, t1_ms, tries=3):
    """⏱️ شموعُ **الثانية** لدقيقةٍ واحدة. `None` عند التعذّر — **ولا تُخمَّن**."""
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        return None
    url = (f"https://api.polygon.io/v2/aggs/ticker/{sym.upper()}"
           f"/range/1/second/{int(t0_ms)}/{int(t1_ms)}"
           f"?adjusted=true&sort=asc&limit=50000")
    for _ in range(int(tries)):
        try:
            r = requests.get(url, headers={"Authorization": f"Bearer {key}"},
                             timeout=12)
            if r.status_code == 200:
                res = (r.json() or {}).get("results") or []
                return [{"o": b.get("o"), "h": b.get("h"), "l": b.get("l"),
                         "c": b.get("c"), "v": b.get("v"), "t": b.get("t")}
                        for b in res if b.get("c") is not None]
            if r.status_code == 429:
                time.sleep(1.0)
                continue
            return None
        except Exception:                                        # noqa: BLE001
            time.sleep(0.5)
    return None


def day_minutes(sym):
    """📥 شموعُ **اليومِ كاملًا** (بريماركتَ وجلسةً وأفترَ) بنداءٍ واحد.

    `polygon_minute_bars` مسقوفٌ بـ500 شمعة ⇒ في تشغيلةٍ مسائيّةٍ **لا يبلغ
    الافتتاح**، وهو أنشطُ نافذةٍ وأهمُّ موضعٍ يُقاس فيه `M0`. الشكلُ **مطابقٌ
    مفتاحًا مفتاحًا** لشموع الإنتاج (مقفولٌ `MZ4`)، **والنافذةُ تبقى
    `LIQ_WINDOW_MIN` كما في الحيّ** ⇒ اتّساعُ التاريخ لا يغيّر ما تراه البوّابة.
    تعذّرٌ ⇒ `None` ⇒ يرتدّ النداءُ إلى `polygon_minute_bars`."""
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        return None
    try:
        from zoneinfo import ZoneInfo
        import datetime as _dt
        d = _dt.datetime.now(ZoneInfo("America/New_York")).date().isoformat()
        r = requests.get(f"https://api.polygon.io/v2/aggs/ticker/{sym.upper()}"
                         f"/range/1/minute/{d}/{d}",
                         headers={"Authorization": f"Bearer {key}"},
                         params={"adjusted": "true", "sort": "asc",
                                 "limit": 50_000},
                         timeout=15)
        if r.status_code != 200:
            return None
        res = (r.json() or {}).get("results") or []
        bars = [{"o": b.get("o"), "h": b.get("h"), "l": b.get("l"),
                 "c": b.get("c"), "v": b.get("v"), "t": b.get("t"),
                 "vw": b.get("vw")} for b in res
                if b.get("l") is not None and b.get("c") is not None]
        return bars or None
    except Exception:                                            # noqa: BLE001
        return None


def minute_trades(sym, t0_ms, t1_ms, limit=50_000):
    """🕵️ صفقاتُ دقيقةٍ بعينها — `(عدد، صفقاتٌ تصاعديّة، ثوانيُ الكلفة)`."""
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        return (None, None, None)
    t0 = time.time()
    try:
        r = requests.get(f"https://api.polygon.io/v3/trades/{sym.upper()}",
                         headers={"Authorization": f"Bearer {key}"},
                         params={"timestamp.gte": int(t0_ms) * 1_000_000,
                                 "timestamp.lt": int(t1_ms) * 1_000_000,
                                 "limit": int(limit), "order": "asc"},
                         timeout=25)
        el = time.time() - t0
        if r.status_code != 200:
            return (None, None, el)
        res = (r.json() or {}).get("results") or []
        rows = [(t.get("price"), t.get("size")) for t in res
                if t.get("price") and t.get("size")]
        return (len(res), rows, el)
    except Exception:                                            # noqa: BLE001
        return (None, None, time.time() - t0)


# ─────────────────────────── البوّابةُ بأعلام الذراع ───────────────────────────
def _usd(b):
    return float(b["c"]) * float(b["v"])


def _inflow(b):
    """💵 **نسخةُ `_inflow` الإنتاجيّة حرفيًّا** — مقفولةٌ عليها في `_lock_e1`."""
    try:
        o_, c_ = float(b.get("o") or b["c"]), float(b["c"])
        h_, l_ = float(b.get("h") or c_), float(b.get("l") or c_)
        if c_ < o_:
            return False
        if o_ > 0 and (c_ - o_) / o_ * 100.0 < float(bot.LIQ_MIN_MOVE_PCT):
            return False
        rng = h_ - l_
        return rng <= 0 or (c_ - l_) >= float(bot.LIQ_CLOSE_POS_MIN) * rng
    except Exception:                                            # noqa: BLE001
        return False


def m0_gate(closed, form, arm):
    """🚨 فرعُ `M0` في `liq_stage_events` بأعلامِ الذراع. `None` = لا عبور."""
    try:
        if arm.get("off"):
            return None
        vm = float(bot.CONFIG["IGNITION_VOL_MULT"])
        n = max(1, int(bot.LIQ_CUM_MINUTES))
        pv = [float(b["v"]) for b in closed]
        pavg = (sum(pv) / len(pv)) if pv else 0.0
        fvx = (float(form["v"]) / pavg) if pavg > 0 else 0.0
        u = _usd(form)
        fcum = u if n <= 1 else u + sum(_usd(b) for b in closed[-(n - 1):])
        floor = float(bot.LIQ_MIN_USD) * float(arm.get("floor_mult") or 1.0)
        if fvx < vm or fcum < floor or not _inflow(form):
            return None
        return {"vol_x": fvx, "usd": u, "cum": fcum}
    except Exception:                                            # noqa: BLE001
        return None


def m1_gate(bars, i, w=None):
    """✅ ثلاثيّةُ الدقيقة **المكتملة** كما يراها الإنتاج (‏`_ok_now`)."""
    try:
        W = int(w or bot.LIQ_WINDOW_MIN)
        win = bars[max(0, i + 2 - W): i + 2]
        closed = win[:-1] if len(win) >= 2 else []
        if len(closed) < 2 or closed[-1] is not bars[i]:
            return None
        last = bars[i]
        prior = [float(b["v"]) for b in closed[:-1]]
        avg = (sum(prior) / len(prior)) if prior else 0.0
        vx = (float(last["v"]) / avg) if avg > 0 else 0.0
        n = max(1, int(bot.LIQ_CUM_MINUTES))
        cum = (_usd(last) if n <= 1
               else sum(_usd(b) for b in closed[-n:]))
        ok = not (vx < float(bot.CONFIG["IGNITION_VOL_MULT"])
                  or cum < float(bot.LIQ_MIN_USD) or not _inflow(last))
        return {"ok": ok, "vol_x": vx, "usd": _usd(last), "cum": cum}
    except Exception:                                            # noqa: BLE001
        return None


def prune_bounds(bars, i, w=None):
    """✂️ **حدودٌ عُلويّةٌ مُبرهَنة** للجزئيّة ⇒ إقصاءٌ بلا خطرِ تفويت:

    ① حجمُ الجزئيّة ‏≤ حجمِ المكتملة **وبنفس المقام** (‏`closed` حتى `i-1` في
       المسارَين) ⇒ `v(i)/avg` سقفٌ لـ`fvx`.
    ② `c×v` للجزئيّة ‏≤ `h(i)×v(i)` ⇒ سقفٌ للأرضية التراكميّة.
    ③ رفعةُ الجزئيّة ‏≤ `(h−o)/o` (الفتحُ ثابتٌ = أوّلُ صفقةٍ في الدقيقة).
    ⇒ إن سقط أيُّ سقفٍ **استحال** عبورُ الجزئيّة، فالإقصاءُ **صفرُ فقدٍ** لا تقدير."""
    try:
        W = int(w or bot.LIQ_WINDOW_MIN)
        win = bars[max(0, i + 1 - W): i + 1]
        closed = win[:-1]
        if len(closed) < 2:
            return None
        pv = [float(b["v"]) for b in closed]
        pavg = (sum(pv) / len(pv)) if pv else 0.0
        b = bars[i]
        o_, c_ = float(b.get("o") or b["c"]), float(b["c"])
        h_ = float(b.get("h") or c_)
        v_ = float(b["v"])
        n = max(1, int(bot.LIQ_CUM_MINUTES))
        tail = 0.0 if n <= 1 else sum(_usd(x) for x in closed[-(n - 1):])
        return {"vx_hi": (v_ / pavg) if pavg > 0 else 0.0,
                "cum_hi": h_ * v_ + tail,
                "rise_hi": ((h_ - o_) / o_ * 100.0) if o_ > 0 else 0.0,
                "closed": closed}
    except Exception:                                            # noqa: BLE001
        return None


def partials(secs, minute_start):
    """🧱 إعادةُ بناءِ الجزئيّة **ثانيةً ثانية** — بناءٌ حقيقيٌّ لا كسرٌ مُقدَّر."""
    out, o, h, l, v = [], None, None, None, 0.0
    for b in secs or []:
        try:
            c = float(b["c"])
        except Exception:                                        # noqa: BLE001
            continue
        if o is None:
            o = float(b.get("o") or c)
            h = float(b.get("h") or c)
            l = float(b.get("l") or c)
        else:
            h = max(h, float(b.get("h") or c))
            l = min(l, float(b.get("l") or c))
        v += float(b.get("v") or 0.0)
        el = int((int(b["t"]) - int(minute_start)) // 1000) + 1
        out.append((el, {"t": int(minute_start), "o": o, "h": h, "l": l,
                         "c": c, "v": v}))
    return out


# ───────────────────────────────── الأقفال ─────────────────────────────────
def _lock_e1():
    """🔒 `LOCK-E1` — فرعُ `M0` عندي **يطابق `liq_stage_events` سلوكيًّا** على
    عيّناتٍ **مفرِّقة**: عابرةٌ · ساقطةٌ بالحجم · بالأرضية · بالرفعة · بالإغلاق.
    وتفرّقٌ واحدٌ ⇒ **خروج 3 ولا يُنشَر رقم**."""
    def _b(i, o, h, l, c, v):
        return {"t": i * 60_000, "o": o, "h": h, "l": l, "c": c, "v": v}

    # قاعدةٌ هادئةٌ ثم دقيقةٌ مكتملةٌ **ساقطةٌ** (فيُبلَغ فرعُ `M0`) ثم متكوّنة
    base = [_b(i, 1.0, 1.005, 0.995, 1.0, 500) for i in range(8)]
    dead = _b(8, 1.0, 1.005, 0.995, 1.0, 300)      # مكتملةٌ ميّتة ⇒ الفرعُ يُبلَغ
    cases = [
        ("عابرة", _b(9, 1.00, 1.30, 1.00, 1.29, 40_000), True),
        ("ساقطةٌ بالحجم", _b(9, 1.00, 1.30, 1.00, 1.29, 900), False),
        ("ساقطةٌ بالأرضية", _b(9, 0.10, 0.13, 0.10, 0.129, 40_000), False),
        ("ساقطةٌ بالرفعة", _b(9, 1.28, 1.30, 1.27, 1.29, 40_000), False),
        ("ساقطةٌ بالإغلاق", _b(9, 1.00, 1.60, 1.00, 1.10, 40_000), False),
    ]
    ok, notes = True, []
    for name, form, want in cases:
        bars = base + [dead, form]
        evs, _ = bot.liq_stage_events(bars, {})
        prod = bool([e for e in (evs or []) if e.get("stage") == "M0"])
        mine = m0_gate(bars[:-1], form, ARMS["E1"]) is not None
        same = (prod == mine) and (prod == want)
        notes.append(f"{name}: إنتاج={prod} · مِجَسّ={mine} · متوقَّع={want} "
                     f"{'✅' if same else '❌'}")
        ok = ok and same
    # 🔒 وشاهدٌ يفرّق الذراعَين: العابرةُ أعلاه سيولتُها ‏≈$51.6 ألفًا
    #    ⇒ تعبر `E1` وتسقط في `E2` (الأرضيةُ ‏$60 ألفًا) ⇒ الذراعُ ليست زينة.
    _f = cases[0][1]
    e1 = m0_gate(base + [dead], _f, ARMS["E1"]) is not None
    e2 = m0_gate(base + [dead], _f, ARMS["E2"]) is not None
    notes.append(f"الذراعُ `E2` تفرّق: E1={e1} · E2={e2} "
                 f"{'✅' if (e1 and not e2) else '❌'}")
    ok = ok and e1 and not e2
    # 🔒 و`E0` صامتةٌ بنيويًّا
    e0 = m0_gate(base + [dead], _f, ARMS["E0"]) is None
    notes.append(f"الذراعُ `E0` صامتة: {e0} {'✅' if e0 else '❌'}")
    ok = ok and e0
    # 🔒 وحدُّ `E3` يفرّق على الجزئيّة المبكّرة
    p10 = m0_gate(base + [dead], _f, ARMS["E3"])
    notes.append("الذراعُ `E3` حدُّها الزمنُ لا الرقم: "
                 f"{'✅' if p10 is not None else '❌'} (تُفحَص بالثواني)")
    ok = ok and p10 is not None
    return ok, notes


def _lock_prune():
    """🔒 `LOCK-PRUNE` — الحدودُ العُلويّةُ **لا تُقصي عابرًا**: تُبنى دقيقةٌ عابرةٌ
    وتُثبَت أن سقوفَها الثلاثة فوق عتباتها، ودقيقةٌ ميّتةٌ يُثبَت سقوطُ سقفها."""
    def _b(i, o, h, l, c, v):
        return {"t": i * 60_000, "o": o, "h": h, "l": l, "c": c, "v": v}
    base = [_b(i, 1.0, 1.005, 0.995, 1.0, 500) for i in range(8)]
    hot = base + [_b(8, 1.00, 1.30, 1.00, 1.29, 40_000)]
    cold = base + [_b(8, 1.00, 1.004, 0.999, 1.001, 400)]
    # 🔴 **العيّنةُ الحاسمة (‏`B` بعينها):** دقيقةٌ **حمراءُ** قمّتُها ‏+30% ثم
    #    انهارت إلى 0.20 ⇒ جزئيّتُها قد تكون عبرت في وسطها ثم ارتدّت. فلو قِيس
    #    السقفُ **بالإغلاق** لا بالقمّة (‏`c` بدل `h`) لأُقصيت **بنيويًّا** ⇒
    #    وصار «صفرُ ارتداد» أثرَ قصٍّ لا نتيجةً. وهي تُسقط طفرتَي الرفعة والأرضية.
    rev = base + [_b(8, 1.00, 1.30, 0.19, 0.20, 40_000)]
    a = prune_bounds(hot, 8)
    b = prune_bounds(cold, 8)
    c = prune_bounds(rev, 8)
    vm = float(bot.CONFIG["IGNITION_VOL_MULT"])
    fl = float(bot.LIQ_MIN_USD)
    mv = float(bot.LIQ_MIN_MOVE_PCT)
    ok1 = (a and a["vx_hi"] >= vm and a["cum_hi"] >= fl and a["rise_hi"] >= mv)
    ok2 = (b and (b["vx_hi"] < vm or b["cum_hi"] < fl or b["rise_hi"] < mv))
    ok3 = (c and c["vx_hi"] >= vm and c["cum_hi"] >= fl and c["rise_hi"] >= mv)
    return (bool(ok1) and bool(ok2) and bool(ok3),
            [f"الحارّةُ تعبر السقوف: {bool(ok1)} {'✅' if ok1 else '❌'}",
             f"الباردةُ يسقط سقفُها: {bool(ok2)} {'✅' if ok2 else '❌'}",
             f"الحمراءُ ذاتُ القمّةِ **لا تُقصى**: {bool(ok3)} "
             f"{'✅' if ok3 else '❌'} "
             f"(أرضيةٌ {0 if not c else c['cum_hi']:,.0f} · "
             f"رفعةٌ {0 if not c else c['rise_hi']:.0f}%)"])


# ───────────────────────────────── القياس ─────────────────────────────────
def classify(bars, cands, secs_by_i, arm):
    """🔖 التصنيفُ الثلاثيُّ (‏§③) لكلّ دقيقةٍ مرشَّحة: `A` · `B` · `C`."""
    rows = []
    for i in cands:
        pb = prune_bounds(bars, i)
        mg = m1_gate(bars, i)
        if pb is None or mg is None:
            continue
        cross = None
        for el, part in partials(secs_by_i.get(i) or [], bars[i]["t"]):
            if arm.get("min_elapsed") and el < int(arm["min_elapsed"]):
                continue
            g = m0_gate(pb["closed"], part, arm)
            if g:
                cross = {"el": el, "price": float(part["c"]), **g}
                break
        if cross and mg["ok"]:
            k = "A"
        elif cross:
            k = "B"
        elif mg["ok"]:
            k = "C"
        else:
            continue
        rows.append({"i": i, "cls": k, "cross": cross,
                     "close": float(bars[i]["c"]), "m1": mg})
    return rows


def _med(xs):
    xs = [x for x in xs if x is not None]
    return stt.median(xs) if xs else None


def main():                                                       # noqa: C901
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        print("⛔ لا مفتاح Polygon — لا قياس (ولا يُخمَّن رقم).")
        return 2
    print("🚨🔬 مِجَسُّ M0 — عقدُه `m0_prereg.md` (مدفوعٌ قبل أيّ رقم)\n")
    print(f"   العتباتُ النافذة: أرضية ${bot.LIQ_MIN_USD:,} على "
          f"{bot.LIQ_CUM_MINUTES} دقائق · رفعة {bot.LIQ_MIN_MOVE_PCT}% · "
          f"قفزةٌ {bot.CONFIG['IGNITION_VOL_MULT']}× · "
          f"موضعُ الإغلاق {bot.LIQ_CLOSE_POS_MIN}\n")
    for nm, fn in (("LOCK-E1", _lock_e1), ("LOCK-PRUNE", _lock_prune)):
        ok, notes = fn()
        for n in notes:
            print("   🔒 " + n)
        if not ok:
            print(f"\n⛔ `{nm}` سقط ⇒ **لا يُنشَر رقم**.")
            return 3
        print(f"   ✅ `{nm}` عبر.\n")

    import operator_entry_live as oel
    try:
        _u, _c, _s, uni_all = oel._load_universe()
    except Exception as e:                                        # noqa: BLE001
        print(f"⛔ تعذّر بناءُ الكون: {type(e).__name__}: {e}")
        return 2
    syms = [r["symbol"] for r in uni_all]
    print(f"👁️ الكون: {len(syms)} سهمًا (نفسُ كونِ المُشغِّل · بلا استثناء)")

    import concurrent.futures as cf
    t0, data, fails = time.time(), {}, 0

    def _one(s):
        try:
            b = day_minutes(s)
            if b and len(b) >= 5:
                return (s, b, "يوم")
            return (s, bot.polygon_minute_bars(s, minutes=WINDOW_MIN), "نافذة")
        except Exception:                                        # noqa: BLE001
            return (s, None, "تعذّر")

    src = {"يوم": 0, "نافذة": 0}
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for s, bars, how in pool.map(_one, syms):
            if bars and len(bars) >= 5:
                data[s] = bars
                src[how] = src.get(how, 0) + 1
            else:
                fails += 1
    print(f"📥 شموعُ الدقيقة: {len(data)} من {len(syms)} · تعذّر {fails} · "
          f"{round(time.time() - t0, 1)}ث "
          f"(يومٌ كامل {src['يوم']} · نافذةُ 480 {src['نافذة']})")
    if not data:
        print("⛔ صفرُ شموع — لا قياس.")
        return 2

    # ✂️ الترشيحُ بالحدود العُلويّةِ المُبرهَنة
    vm = float(bot.CONFIG["IGNITION_VOL_MULT"])
    cands, n_scan = {}, 0
    for s, bars in data.items():
        keep = []
        for i in range(2, len(bars) - 1):
            n_scan += 1
            pb = prune_bounds(bars, i)
            if pb is None:
                continue
            if (pb["vx_hi"] >= vm and pb["cum_hi"] >= float(bot.LIQ_MIN_USD)
                    and pb["rise_hi"] >= float(bot.LIQ_MIN_MOVE_PCT)):
                keep.append(i)
        if keep:
            cands[s] = keep
    n_cand = sum(len(v) for v in cands.values())
    print(f"✂️ الدقائقُ المرشَّحة: **{n_cand}** من {n_scan:,} مفحوصة في "
          f"{len(cands)} سهمًا (بحدودٍ عُلويّةٍ مُبرهَنة ⇒ صفرُ فقد)")
    if not n_cand:
        print("\n⛔ صفرُ دقيقةٍ مرشَّحة في الجلسة ⇒ **لا مادّةَ تُقاس** ⇒ لا حكم.")
        return 5

    # ⏱️ شموعُ الثانية — نداءٌ لكلّ دقيقةٍ مرشَّحة (بسقفٍ يُعلَن قصُّه)
    jobs = [(s, i) for s, ks in sorted(cands.items()) for i in ks]
    cut = max(0, len(jobs) - SEC_CAP)
    if cut:
        print(f"   ⚠️ **قُصَّ {cut} مرشَّحًا** بسقف {SEC_CAP} (يُعلَن لا يُخفى)")
        jobs = jobs[:SEC_CAP]

    def _sec(job):
        s, i = job
        t = int(data[s][i]["t"])
        return (s, i, second_bars(s, t, t + 59_999))

    t1, secs, sec_fail = time.time(), {}, 0
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for s, i, sb in pool.map(_sec, jobs):
            if sb is None:
                sec_fail += 1
                continue
            secs.setdefault(s, {})[i] = sb
    got = sum(len(v) for v in secs.values())
    print(f"⏱️ شموعُ الثانية: {got} دقيقةً · **تعذّر {sec_fail}** · "
          f"{round(time.time() - t1, 1)}ث")
    if got == 0:
        print("\n⛔ شموعُ الثانية غيرُ متاحة ⇒ **يُوقَف ولا يُنشَر رقم** (‏§②).")
        return 4
    empty = sum(1 for s in secs for i in secs[s] if not secs[s][i])
    print(f"   ↳ ومنها **{empty}** دقيقةً بلا صفقاتِ ثانيةٍ (تُعَدّ وتُستبعَد · ‏§⑨-4)")

    # 🔖 التصنيفُ لكلّ ذراع
    res = {}
    for an, arm in ARMS.items():
        rows, per = [], {}
        for s in sorted(secs):
            r = classify(data[s], sorted(secs[s]), secs[s], arm)
            if r:
                per[s] = r
                rows.extend([dict(x, sym=s) for x in r])
        A = [x for x in rows if x["cls"] == "A"]
        B = [x for x in rows if x["cls"] == "B"]
        C = [x for x in rows if x["cls"] == "C"]
        rev = (100.0 * len(B) / (len(A) + len(B))) if (A or B) else None
        secs_saved = [60 - x["cross"]["el"] for x in A]
        px_gain = [(x["close"] / x["cross"]["price"] - 1.0) * 100.0
                   for x in A if x["cross"]["price"] > 0]
        fr = {}
        for k, grp in (("A", A), ("B", B)):
            vals = [LM.fruit(data[x["sym"]], x["i"], x["cross"]["price"])
                    for x in grp]
            ok = [v for v in vals if v is not None]
            fr[k] = {"n": len(ok), "unres": len(vals) - len(ok),
                     "hit": sum(1 for v in ok if v >= LM.FRUIT_PCT),
                     "pct": ((100.0 * sum(1 for v in ok if v >= LM.FRUIT_PCT)
                              / len(ok)) if ok else None)}
        # 📌 **وصفيٌّ خارج قاعدة القرار (‏§⑤-4 يعدّ الدقائق لا الرسائل):** في
        #    الإنتاج **أوّلُ** عبورٍ لكلّ سهمٍ يضع المِرساةَ وما بعده تحديثات ⇒
        #    عددُ **المِرساة** هو ما يصل المالكَ فعلًا رسالةً جديدة. يُنشَر ولا
        #    يُبنى عليه حكم (لم يُسجَّل مسبقًا).
        first = {}
        for _s2, _r2 in per.items():
            ab = sorted([x for x in _r2 if x["cls"] in ("A", "B")],
                        key=lambda z: z["i"])
            if ab:
                first[_s2] = ab[0]["cls"]
        res[an] = {"A": A, "B": B, "C": C, "rev": rev, "per": per,
                   "sec": _med(secs_saved), "px": _med(px_gain), "fruit": fr,
                   "first": first}

    print("\n" + "=" * 72)
    print("① التصنيفُ الثلاثيُّ ونسبةُ الارتداد (‏§③/§⑤)")
    print("=" * 72)
    print("  ذراع |   A |   B |   C | ارتداد٪ | ثوانٍ | فرقُ سعر٪ | أثمر A | أثمر B")
    for an in ARMS:
        c = res[an]
        rv = "—" if c["rev"] is None else f"{c['rev']:.1f}%"
        sc = "—" if c["sec"] is None else f"{c['sec']:.0f}"
        px = "—" if c["px"] is None else f"{c['px']:+.2f}"
        fa = c["fruit"]["A"]
        fb = c["fruit"]["B"]
        fas = "—" if fa["pct"] is None else f"{fa['pct']:.0f}% ({fa['n']})"
        fbs = "—" if fb["pct"] is None else f"{fb['pct']:.0f}% ({fb['n']})"
        print(f"  {an:>4} | {len(c['A']):>3} | {len(c['B']):>3} | "
              f"{len(c['C']):>3} | {rv:>7} | {sc:>5} | {px:>9} | "
              f"{fas:>7} | {fbs:>7}")
    print("\n  " + " · ".join(f"{k}: {v}" for k, v in ARM_DESC.items()))
    print("  ⚖️ `A` مكسبٌ خالص · `B` **الخطرُ الجديد كلُّه** · `C` لا يُضيف شيئًا.")
    print("\n  📌 **وصفيٌّ خارج الحكم — مِرساةُ كلّ سهم** (أوّلُ عبورٍ يضع المِرساةَ "
          "وما بعده تحديثات ⇒ هذي هي الرسائلُ الجديدة فعلًا):")
    for an in ARMS:
        fst = res[an].get("first") or {}
        na = sum(1 for v in fst.values() if v == "A")
        nb = sum(1 for v in fst.values() if v == "B")
        tot = na + nb
        print(f"   • {an}: أسهمٌ تُطلِق {tot} — مِرساتُها `A` {na} · "
              f"`B` {nb}" + (f" ⇒ **{100.0 * nb / tot:.0f}% من المراسي ارتداد**"
                             if tot else ""))

    print("\n" + "=" * 72)
    print("② كلُّ دقيقةٍ مصنَّفةٍ تحت `E1` — بأسمائها لا مجمَّعةً")
    print("=" * 72)
    e1 = res["E1"]
    shown = 0
    for x in sorted(e1["A"] + e1["B"], key=lambda z: (z["sym"], z["i"])):
        if shown >= 40:
            print(f"   … و{len(e1['A']) + len(e1['B']) - shown} أخرى "
                  "(قصٌّ **مُعلَن** في العرض · والحساب على الكلّ)")
            break
        cr = x["cross"]
        print(f"   {x['cls']} ${x['sym']:<6} دقيقة {x['i']:>3} · عبرَت عند "
              f"الثانية {cr['el']:>2} بسعر {cr['price']:.4f} · إغلاقُها "
              f"{x['close']:.4f} ({(x['close'] / cr['price'] - 1) * 100:+.2f}%) "
              f"· سيولةٌ ${cr['usd']:,.0f} · قفزةٌ {cr['vol_x']:.0f}×")
        shown += 1
    if not (e1["A"] or e1["B"]):
        print("   (لا شيء)")
    if e1["C"]:
        print(f"   ↳ و`C` (المكتملةُ عبرت ولا جزئيّةَ سبقتها): "
              f"{', '.join(sorted({'$' + x['sym'] for x in e1['C']}))}")

    print("\n" + "=" * 72)
    print("③ قاعدةُ القرار المسجَّلة (‏§⑥) — تُطبَّق كما كُتبت")
    print("=" * 72)
    verdict = None
    for an in ("E1", "E2", "E3"):
        c = res[an]
        d1 = c["rev"] is not None and c["rev"] <= 40.0
        d2 = c["px"] is not None and c["px"] >= 1.5
        fa, fb = c["fruit"]["A"]["pct"], c["fruit"]["B"]["pct"]
        d3 = (fa is None or fb is None) or (fb >= fa - LM.JITTER_PP)
        good = d1 and d2 and d3
        rv = "—" if c["rev"] is None else "{:.1f}%".format(c["rev"])
        px = "—" if c["px"] is None else "{:+.2f}%".format(c["px"])
        fas = "—" if fa is None else "{:.0f}%".format(fa)
        fbs = "—" if fb is None else "{:.0f}%".format(fb)
        print(f"  {an}: ارتدادٌ {rv} (الحدّ 40%) {'✅' if d1 else '❌'} · "
              f"فرقُ سعرٍ {px} (الحدّ 1.5%) {'✅' if d2 else '❌'} · "
              f"إثمارُ B {fbs} مقابل A {fas} (الحدّ ‏−{LM.JITTER_PP}ن) "
              f"{'✅' if d3 else '❌'} ⇒ "
              f"{'✅ تستوفي' if good else '🔴 لا تستوفي'}")
        if good and verdict is None:
            verdict = an
    if verdict == "E1":
        print("\n  ⇒ **`M0` يبقى مُشتغِلًا كما هو** (الذراعُ المشحونةُ تستوفي الثلاثة).")
    elif verdict:
        print(f"\n  ⇒ **يُوصى بتشديد `M0` إلى `{verdict}`** (‏§⑥: أشدُّ ذراعٍ تستوفي).")
    else:
        print("\n  ⇒ 🔴 **لا ذراعَ تستوفي ⇒ يُوصى بإطفاء `M0`** (‏§⑥) — "
              "**والحكمُ للمالك**.")

    # 🕵️ تغطيةُ المضارب (‏§⑦)
    print("\n" + "=" * 72)
    print("④ تغطيةُ قراءة المضارب (‏§⑦) — بالأرقام لا بالتقدير")
    print("=" * 72)
    alerts = sorted(e1["A"] + e1["B"] + e1["C"],
                    key=lambda z: -(z["cross"]["usd"] if z["cross"]
                                    else z["m1"]["usd"]))
    smp = alerts[:OP_SAMPLE]
    if len(alerts) > OP_SAMPLE:
        print(f"  ⚠️ **عيّنةٌ من {OP_SAMPLE} إشعارًا من {len(alerts)}** "
              "(الأضخمُ سيولةً — والقصُّ مُعلَن)")
    covs = {c: [] for c in OP_CAPS}
    lats = {c: [] for c in OP_CAPS}
    flips, ns, prop_cap = 0, [], int(bot.LIQ_OPERATOR_TRADES)
    mutes = {c: 0 for c in OP_CAPS}
    print("  سهم | دقيقة | صفقاتُ الدقيقة | " +
          " | ".join(f"تغطية {c:,}" for c in OP_CAPS) + " | حكمٌ يتغيّر؟")
    for x in smp:
        s, i = x["sym"], x["i"]
        t = int(data[s][i]["t"])
        n, rows, _e = minute_trades(s, t, t + 60_000)
        if not n or not rows:
            print(f"  ${s:<6} | {i:>5} | ⛔ تعذّر")
            continue
        ns.append(n)
        vs, line = {}, []
        for cap in OP_CAPS:
            cv = 100.0 * min(cap, n) / n
            covs[cap].append(cv)
            ob = bot._operator_blocks(rows[-cap:],
                                      bot.CONFIG["OPERATOR_MIN_SHARES"])
            vs[cap] = None if ob is None else bool(ob.get("has_operator"))
            line.append(f"{cv:>5.0f}%")
            if len(lats[cap]) < LAT_SAMPLE:       # كلفةُ الزمن على عيّنةٍ مُعلَنة
                _n2, _r2, el2 = minute_trades(s, t, t + 60_000, limit=cap)
                if el2 is not None:
                    lats[cap].append(el2)
        known = [v for v in vs.values() if v is not None]
        flip = bool(known) and (any(known) != all(known))
        # 🔴 «يقلب حكمًا إلى الكتم» بنصّ §⑦-4: الأضيقُ (‏250) يقول «مضاربٌ حاضر»
        #    والسقفُ الأوسعُ يقول «غائب» ⇒ الرفعُ شدَّ الكتمَ وهو ما يمنعه العقد.
        # 🔒 ويُقاس **لكلّ سقفٍ مرشَّح** لا للمشحون وحده: §⑦-2 يُعدِّد أربعةَ سقوف،
        #    فلا يُختار أحدُها ومعيارُه الرابع غيرُ مقيسٍ عليه.
        for cap in OP_CAPS:
            if bool(vs.get(250)) and (vs.get(cap) is False):
                mutes[cap] = mutes.get(cap, 0) + 1
        mute = bool(vs.get(250)) and (vs.get(prop_cap) is False)
        flips += 1 if mute else 0
        print(f"  ${s:<6} | {i:>5} | {n:>13,} | " + " | ".join(line) +
              f" | {'🔴 نعم' if mute else ('تغيّرَ ' if flip else 'لا')}")
    if ns:
        print(f"\n  وسيطُ صفقاتِ دقيقةِ الإشعار: **{_med(ns):,.0f}** صفقة")
        for cap in OP_CAPS:
            mc, ml = _med(covs[cap]), _med(lats[cap])
            print(f"   • سقف {cap:>6,}: تغطيةٌ وسيطُها "
                  f"**{(0 if mc is None else mc):.0f}%** · كلفةٌ "
                  f"{('—' if ml is None else f'{ml:.2f}ث')}")
        m250 = _med(covs[250]) or 0.0
        c1 = m250 < 50.0
        print("\n  🔎 معاييرُ §⑦ — تُقيَّم لكلّ سقفٍ مرشَّحٍ لا للمشحون وحده:")
        print(f"   ① ‏250 يغطّي أقلَّ من نصفِ الدقيقة وسيطًا: {m250:.0f}% "
              f"{'✅' if c1 else '❌'} (شرطٌ عامٌّ لكلّ الأذرع)")
        best = None
        for cap in OP_CAPS:
            if cap == 250:
                continue
            mc = _med(covs.get(cap) or [])
            ml = _med(lats.get(cap) or [])
            k2 = mc is not None and mc >= 90.0
            k3 = ml is not None and ml <= 3.0
            k4 = mutes.get(cap, 0) == 0
            good = c1 and k2 and k3 and k4
            if good and best is None:
                best = cap                      # 🥇 **أصغرُ** سقفٍ يستوفي الأربعة
            print(f"   • {cap:>6,}: تغطيةٌ "
                  f"{('—' if mc is None else f'{mc:.0f}%')} "
                  f"{'✅' if k2 else '❌'} · كلفةٌ "
                  f"{('—' if ml is None else f'{ml:.2f}ث')} "
                  f"{'✅' if k3 else '❌'} · يقلب للكتم {mutes.get(cap, 0)} "
                  f"{'✅' if k4 else '❌'} ⇒ "
                  f"{'✅ مسنودٌ بالدليل' if good else '🔴 لا يُعتمَد'}")
        if best:
            print(f"\n   ⇒ **يُرفَع إلى {best:,}** — أصغرُ سقفٍ يستوفي الأربعة "
                  f"(والمشحونُ الآن {prop_cap:,})"
                  + ("  ✅ **وهو المشحونُ فعلًا ⇒ لا تغيير**"
                     if best == prop_cap else ""))
        else:
            print("\n   ⇒ 🔴 **لا سقفَ يستوفي الأربعة ⇒ لا يُرفَع، ويُبلَّغ الرقم**.")
    else:
        print("\n  ⛔ صفرُ إشعارٍ مقيسِ الصفقات ⇒ **لا حكمَ على التغطية**.")

    print("\n" + "=" * 72)
    print("⑤ حدودُ صدقٍ (‏§⑨ — تُقرأ مع الأرقام لا بعدها)")
    print("=" * 72)
    print("  1. جلسةٌ واحدة ⇒ مِجَسُّ خطرٍ لا تجربةَ عائد · **ولا صفقةَ تُقاس**.")
    print("  2. الإعادةُ ترى الجزئيّةَ في **لحظة عبورها** والحيُّ يلفّ كلَّ ‏≈60 ثانية")
    print("     ⇒ أرقامُ الأسبقيّة **سقف** · ونسبةُ الارتدادِ على العبور الأوّل = "
          "**أسوأُ حالة**.")
    print(f"  3. «الإثمار» بلوغُ ‏+{LM.FRUIT_PCT:.0f}% خلال {LM.FRUIT_MIN} دقيقة — "
          "**سعرٌ مطبوعٌ لا تنفيذ** ⇒ سقفٌ متفائل.")
    print(f"  4. ودقائقُ بلا شموعِ ثانية: {sec_fail} متعذّرة · {empty} فارغة — "
          "**تُعَدّ وتُستبعَد ولا تُخمَّن**.")
    print("  5. والكونُ رقيقٌ (أسهمُ فيصل) ⇒ لا يُعمَّم على كونٍ سائل.")
    print(f"  6. والشموعُ **يومٌ كامل** لا نافذةُ 480 (‏{src['يوم']} سهمًا) كي يُقاس "
          f"الافتتاح · **والنافذةُ الحاكمةُ {bot.LIQ_WINDOW_MIN} كما في الحيّ**.")
    print("  7. وتغطيةُ المضارب تُقاس **بصفقات دقيقةِ الإشعار**، والحيُّ يقرأ آخرَ "
          "`limit` صفقةٍ **بلا قيدٍ زمنيّ** ⇒ تقريبٌ مُعلَنٌ عند نهاية الدقيقة "
          "(والسقفُ الأوسعُ يُضيف صفقاتٍ أقدمَ ⇒ **يُرخي لا يشدّ** بنيويًّا).")
    print(f"\n⏱️ زمنُ التشغيل: {round(time.time() - t0, 1)}ث "
          f"(الميزانيةُ {BUDGET_SEC}ث)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
