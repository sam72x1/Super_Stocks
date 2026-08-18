#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🚪🔬 **مِجَسُّ شروط البوّابة** — أيُّ شرطٍ يُؤخّر أوّلَ تنبيه؟

عقدُه `gate_prereg.md` **مدفوعٌ قبل أيّ رقم**. يجيب سؤالَ المالك بنصّه: «التنبيه
وصلني **بعد ما ارتفع السهم فوق 20٪**» ⇒ المقياسُ الحاكم **«التأخّر»** = ارتفاعُ
السهم عن **إغلاق الأمس** لحظةَ أوّلِ تنبيه.

🔒 **قراءةٌ/قياسٌ فقط:** لا يكتب حالةً ولا يرسل تلغرامًا ولا يمسّ فرزًا ولا جذرًا.
🔴 **ورقمان من الثلاثة نصُّ المالك** ($30 ألفًا و5%) ⇒ **كلفتُهما تُعرَض ولا يُوصى
بتغييرهما** — والقابلُ للتوصية `engineering` وحدَه (‏`gate_prereg §②/§⑦`).
"""
import os
import statistics as stt
import sys
import time

import requests

os.environ.setdefault("SCREENER_MODE", "PROBE")
import Super_stock as bot                                          # noqa: E402
import liq_move_probe as LM                                        # noqa: E402
import m0_probe as MZ                                              # noqa: E402

MOVER_PCT = 30.0            # 🔒 منقولٌ حرفيًّا من `liq_noise_prereg` — لا يُحرَّك
T10_PCT = 10.0              # علامةُ «الحركةُ بدأت» (‏§⑥ — مثبَّتةٌ لا قانون)
LATE_SANE_MAX = 500.0       # تأخّرٌ فوقه = تشويهُ تقسيمٍ ⇒ يُعَدّ ويُستبعَد ويُسمّى
WORKERS = 8
JITTER_PP = LM.JITTER_PP    # 3.6 نقطة — تقلّبُ القياس المقيس

# ⚙️ **الأذرعُ السبع مثبَّتةٌ في `gate_prereg.md §④` — ولا تُزاد ذراعٌ بعد الأرقام.**
ARMS = {
    "G0": {},
    "G1": {"close_pos": 0.0},
    "G2": {"vol_mult": 2.0},
    "G3": {"cum_n": 5},
    "G4": {"move_min": 3.0},
    "G5": {"floor": 15_000.0},
    "G6": {"move_min": 0.0, "no_rise": True},
}
ARM_DESC = {
    "G0": "الإنتاجُ كما هو",
    "G1": "بلا موضعِ إغلاق (`engineering` ⇒ قابلٌ للتوصية)",
    "G2": "قفزةُ حجمٍ ‏2× بدل 3 (`engineering`)",
    "G3": "نافذةٌ تراكميّةٌ 5 دقائقَ (`engineering`)",
    "G4": "🔴 رفعةُ الدقيقة 3% — **رقمُ المالك، كلفةٌ لا توصية**",
    "G5": "🔴 أرضيةُ ‏$15 ألفًا — **رقمُ المالك، كلفةٌ لا توصية**",
    "G6": "⛔ بلا شرط رفعةٍ — **حدٌّ أعلى، ليس اقتراحًا**",
}
COACHABLE = ("G1", "G2", "G3")        # 🔒 القابلُ للتوصية — مثبَّتٌ سلفًا
OWNER_COST = ("G4", "G5")             # 🔴 أرقامُ المالك — كلفةٌ تُعرَض
UPPER_BOUND = ("G6",)


def resolve_day(control="AAPL", max_back=7):
    """📅 **الجلسةُ المقيسة تُحسَم مرّةً واحدةً للكلّ** — لا سهمًا سهمًا.

    🔴 **وسببُه عيبٌ وقع فعلًا:** أوّلُ تشغيلةٍ (`32097494557`) وقعت **00:00
    نيويورك** فلم يكن ليومها شمعةٌ واحدة ⇒ **0 من 319**. والارتدادُ سهمًا سهمًا
    كان سيخلط **أيّامًا مختلفةً في جدولٍ واحد** — وهو أسوأُ من الفشل الصريح.
    ⇒ يُجرَّب اليومُ ثم ما قبله بشاهدِ ضبطٍ سائلٍ واحد، **ويُعلَن أيُّ يومٍ قِيس**."""
    from zoneinfo import ZoneInfo
    import datetime as _dt
    d0 = _dt.datetime.now(ZoneInfo("America/New_York")).date()
    for k in range(int(max_back)):
        d = (d0 - _dt.timedelta(days=k)).isoformat()
        bars = MZ.day_minutes(control, day=d)
        if bars and len(bars) >= 100:
            return (d, k, len(bars))
    return (None, None, 0)


def prev_close(sym, day):
    """📉 إغلاقُ **اليومِ السابقِ للجلسة المقيسة** — لا «أمسِ اليومَ الجاري».

    🔴🔴 **عيبٌ كشفه تثبيتُ اليوم:** `/v2/aggs/{sym}/prev` يُرجع اليومَ السابقَ
    **للحظة النداء**؛ فلو قِيست جلسةُ الاثنين وشُغِّل المِجَسُّ فجرَ الثلاثاء
    لأرجع **إغلاقَ الاثنين نفسِه** ⇒ «التأخّر» يُقاس عن يومه هو فيخرج **≈صفر**
    ويُقرأ «لا تأخّر» وهو خطأُ قياسٍ صرف. ⇒ يُطلَب مدًى يوميٌّ وتُؤخذ **آخرُ
    جلسةٍ تاريخُها قبل يوم القياس** (مقفولٌ `GT8`)."""
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key or not day:
        return None
    try:
        import datetime as _dt
        d1 = _dt.date.fromisoformat(str(day))
        d0 = (d1 - _dt.timedelta(days=12)).isoformat()
        r = requests.get(f"https://api.polygon.io/v2/aggs/ticker/"
                         f"{sym.upper()}/range/1/day/{d0}/{day}",
                         headers={"Authorization": f"Bearer {key}"},
                         params={"adjusted": "true", "sort": "asc",
                                 "limit": 50}, timeout=12)
        if r.status_code != 200:
            return None
        res = (r.json() or {}).get("results") or []
        cut = int(_dt.datetime.combine(
            d1, _dt.time()).replace(tzinfo=_dt.timezone.utc).timestamp()) * 1000
        prior = [b for b in res if b.get("t") is not None and int(b["t"]) < cut
                 and b.get("c")]
        return float(prior[-1]["c"]) if prior else None
    except Exception:                                            # noqa: BLE001
        return None


def gate_trace(bars, i, arm, w=None):
    """🔬 يفكّك بوّابةَ المِرساة عند الدقيقة `i` بأعلامِ الذراع.

    يطابق `liq_stage_events` (فرعُ «لا مِرساةَ بعد») **شرطًا شرطًا** — ومقفولٌ
    عليه سلوكيًّا لـ`G0` في `_lock_g0`."""
    W = int(w or bot.LIQ_WINDOW_MIN)
    win = bars[max(0, i + 2 - W): i + 2]
    closed = win[:-1] if len(win) >= 2 else []
    if len(closed) < 2 or closed[-1] is not bars[i]:
        return None
    last = bars[i]
    prior = [float(b["v"]) for b in closed[:-1]]
    avg = (sum(prior) / len(prior)) if prior else 0.0
    vx = (float(last["v"]) / avg) if avg > 0 else 0.0
    n = max(1, int(arm.get("cum_n", bot.LIQ_CUM_MINUTES)))
    floor = float(arm.get("floor", bot.LIQ_MIN_USD))
    cum = (MZ._usd(last) if n <= 1
           else sum(MZ._usd(b) for b in closed[-n:]))
    o_, c_ = float(last.get("o") or last["c"]), float(last["c"])
    h_, l_ = float(last.get("h") or c_), float(last.get("l") or c_)
    rise = ((c_ - o_) / o_ * 100.0) if o_ > 0 else 0.0
    rng = h_ - l_
    cpos = 1.0 if rng <= 0 else (c_ - l_) / rng
    mv = float(arm.get("move_min", bot.LIQ_MIN_MOVE_PCT))
    cp = float(arm.get("close_pos", bot.LIQ_CLOSE_POS_MIN))
    return {
        "vx": vx, "cum": cum, "rise": rise, "cpos": cpos, "price": c_,
        "usd": MZ._usd(last),
        "g_vol": vx >= float(arm.get("vol_mult", bot.CONFIG["IGNITION_VOL_MULT"])),
        "g_floor": cum >= floor,
        "g_green": c_ >= o_,
        "g_rise": True if arm.get("no_rise") else rise >= mv,
        "g_cpos": (rng <= 0) or ((c_ - l_) >= cp * rng),
    }


GATE_ORDER = (("g_vol", "قفزةُ الحجم"), ("g_floor", "الأرضيةُ التراكميّة"),
              ("g_green", "خضراء"), ("g_rise", "رفعةُ الدقيقة"),
              ("g_cpos", "موضعُ الإغلاق"))


def first_wall(t):
    """🧱 **أوّلُ شرطٍ ساقط** بترتيب البوّابة — أو `None` إن عبرت كلُّها."""
    if t is None:
        return "لا نافذة"
    for k, name in GATE_ORDER:
        if not t[k]:
            return name
    return None


def anchor_of(bars, arm):
    """🚩 أوّلُ دقيقةٍ تعبر كلَّ الشروط = المِرساة (الرسالةُ الأولى)."""
    for i in range(2, len(bars) - 1):
        t = gate_trace(bars, i, arm)
        if t and first_wall(t) is None:
            return (i, t)
    return (None, None)


def all_fires(bars, arm):
    """📩 كلُّ دقيقةٍ تعبر (لقياس الكلفة) — عبورُ دقائقَ لا رسائل (‏§⑨-7)."""
    return [i for i in range(2, len(bars) - 1)
            if first_wall(gate_trace(bars, i, arm)) is None]


def _med(xs):
    xs = [x for x in xs if x is not None]
    return stt.median(xs) if xs else None


# ───────────────────────────────── الأقفال ─────────────────────────────────
def _lock_g0():
    """🔒 `LOCK-G0` — `G0` **يطابق بوّابةَ الإنتاج سلوكيًّا** على عيّناتٍ مفرِّقة:
    عابرةٌ · وساقطةٌ بكلّ شرطٍ على حدة. وتفرّقٌ واحدٌ ⇒ **خروج 3 ولا يُنشَر رقم**.

    ⚖️ وتُقارَن **المِرساةُ** لا مجرّدُ العبور: `liq_stage_events` بحالةٍ فارغةٍ
    تُرجع `M1` عند أوّلِ عبور — وهو بعينه ما تُرجعه `anchor_of`."""
    def _b(i, o, h, l, c, v):
        return {"t": i * 60_000, "o": o, "h": h, "l": l, "c": c, "v": v}
    base = [_b(i, 1.0, 1.005, 0.995, 1.0, 500) for i in range(8)]
    cases = [
        ("عابرة", _b(8, 1.00, 1.30, 1.00, 1.29, 40_000), True),
        ("ساقطةٌ بالحجم", _b(8, 1.00, 1.30, 1.00, 1.29, 900), False),
        ("ساقطةٌ بالأرضية", _b(8, 0.10, 0.13, 0.10, 0.129, 40_000), False),
        ("حمراء", _b(8, 1.30, 1.31, 1.00, 1.05, 40_000), False),
        ("ساقطةٌ بالرفعة", _b(8, 1.28, 1.30, 1.27, 1.29, 40_000), False),
        ("ساقطةٌ بموضع الإغلاق", _b(8, 1.00, 1.60, 1.00, 1.10, 40_000), False),
    ]
    ok, notes = True, []
    for name, bar, want in cases:
        bars = base + [bar, _b(9, 1.29, 1.30, 1.28, 1.29, 100)]
        prod = [x["stage"] for x in bot.liq_stage_events(bars, {})[0]] == ["M1"]
        mine = anchor_of(bars, ARMS["G0"])[0] == 8
        same = (prod == mine) and (prod == want)
        notes.append(f"{name}: إنتاج={prod} · مِجَسّ={mine} · متوقَّع={want} "
                     f"{'✅' if same else '❌'}")
        ok = ok and same
    # 🔒 وكلُّ ذراعٍ **تفرّق فعلًا** — وإلّا كانت زينةً تُقرأ «لا فرق» وهي no-op
    bars_cp = base + [_b(8, 1.00, 1.60, 1.00, 1.10, 40_000),
                      _b(9, 1.10, 1.11, 1.09, 1.10, 100)]
    # 🐞 **عيّنةُ `G2` الأولى كانت مستحيلةً حسابيًّا**: قفزةٌ 2.6× بحجمٍ 1,300
    #    سهمًا تعطي ‏$1.7 ألفًا فتسقط على **الأرضية** لا على الحجم ⇒ القفلُ يقيس
    #    شرطًا آخر. ⇒ تُرفَع القاعدةُ إلى 10,000 سهمٍ فتصير القفزةُ 2.6× **والدولارُ
    #    ‏$33.5 ألفًا فوق الأرضية** ⇒ الفارقُ **قفزةُ الحجم وحدَها**.
    base_v = [_b(i, 1.0, 1.005, 0.995, 1.0, 10_000) for i in range(8)]
    bars_vx = base_v + [_b(8, 1.00, 1.30, 1.00, 1.29, 26_000),
                        _b(9, 1.29, 1.30, 1.28, 1.29, 100)]
    bars_mv = base + [_b(8, 1.00, 1.05, 1.00, 1.04, 40_000),
                      _b(9, 1.04, 1.05, 1.03, 1.04, 100)]
    bars_fl = base + [_b(8, 1.00, 1.30, 1.00, 1.29, 16_000),
                      _b(9, 1.29, 1.30, 1.28, 1.29, 100)]
    for nm, bb, arm in (("G1 موضعُ الإغلاق", bars_cp, "G1"),
                        ("G2 قفزةُ الحجم", bars_vx, "G2"),
                        ("G4 الرفعة", bars_mv, "G4"),
                        ("G5 الأرضية", bars_fl, "G5"),
                        ("G6 بلا رفعة", bars_mv, "G6")):
        a0 = anchor_of(bb, ARMS["G0"])[0]
        a1 = anchor_of(bb, ARMS[arm])[0]
        good = (a0 is None) and (a1 == 8)
        notes.append(f"{nm} تفرّق: G0={a0} · {arm}={a1} "
                     f"{'✅' if good else '❌'}")
        ok = ok and good
    # 🔒 و`G3` تفرّق بنافذةٍ أوسع: خمسُ دقائقَ صغيرةٍ مجموعُها فوق الأرضية
    #    وثلاثُها دونها ⇒ `G0` صامتٌ و`G3` يُطلق.
    # 🐞 **وعيّنةُ `G3` الأولى كانت مستحيلةً بنيويًّا**: خمسُ دقائقَ متساويةِ
    #    الحجم **ترفع المتوسّطَ بنفسها** فيستحيل رياضيًّا أن تبلغ الأخيرةُ 3×
    #    (‏`12S ≥ 3(4000+4S)` ⇒ `0 ≥ 12000`). ⇒ التصميمُ الصحيح: دولاراتٌ **قديمة**
    #    داخل نافذة الخمس وخارج الثلاث · ودقيقتان هادئتان بينهما · ثم دقيقةٌ
    #    قافزةٌ صغيرةُ الدولار ⇒ **الثلاثُ دون الأرضية والخمسُ فوقها**.
    slow = [_b(i, 1.0, 1.0, 1.0, 1.0, 100) for i in range(8)]
    slow += [_b(8, 1.0, 1.0, 1.0, 1.0, 12_000),
             _b(9, 1.0, 1.0, 1.0, 1.0, 12_000),
             _b(10, 1.0, 1.0, 1.0, 1.0, 100),
             _b(11, 1.0, 1.0, 1.0, 1.0, 100),
             _b(12, 1.00, 1.30, 1.00, 1.30, 8_000),
             _b(13, 1.30, 1.31, 1.29, 1.30, 50)]
    g0s, g3s = anchor_of(slow, ARMS["G0"])[0], anchor_of(slow, ARMS["G3"])[0]
    notes.append(f"G3 النافذةُ تفرّق: G0={g0s} · G3={g3s} "
                 f"{'✅' if (g0s is None and g3s is not None) else '❌'}")
    ok = ok and g0s is None and g3s is not None
    return ok, notes


def main():                                                       # noqa: C901
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        print("⛔ لا مفتاح Polygon — لا قياس (ولا يُخمَّن رقم).")
        return 2
    print("🚪🔬 مِجَسُّ شروط البوّابة — عقدُه `gate_prereg.md` (قبل أيّ رقم)\n")
    print(f"   النافذُ: قفزةٌ {bot.CONFIG['IGNITION_VOL_MULT']}× · أرضيةُ "
          f"${bot.LIQ_MIN_USD:,} على {bot.LIQ_CUM_MINUTES} دقائق · رفعةُ "
          f"{bot.LIQ_MIN_MOVE_PCT}% · موضعُ إغلاقٍ {bot.LIQ_CLOSE_POS_MIN}\n")
    ok, notes = _lock_g0()
    for n in notes:
        print("   🔒 " + n)
    if not ok:
        print("\n⛔ `LOCK-G0` سقط ⇒ **لا يُنشَر رقم**.")
        return 3
    print("   ✅ `LOCK-G0` عبر — والأذرعُ السبعُ تفرّق فعلًا.\n")

    # 📅 الجلسةُ المقيسةُ **تُحسَم مرّةً واحدةً للكلّ وتُعلَن**
    day = (os.environ.get("GATE_DAY") or "").strip() or None
    if day:
        back, nb = 0, len(MZ.day_minutes("AAPL", day=day) or [])
        if nb < 100:
            print(f"⛔ اليومُ المطلوب {day} بلا بياناتٍ لشاهد الضبط ⇒ لا قياس.")
            return 2
    else:
        day, back, nb = resolve_day()
        if not day:
            print("⛔ لم تُوجَد جلسةٌ فيها بيانات خلال سبعةِ أيام ⇒ لا قياس.")
            return 2
    print(f"📅 **الجلسةُ المقيسة: {day}** (‏{back} يومًا للخلف · شاهدُ الضبط "
          f"`AAPL` {nb} شمعة) — تُحسَم مرّةً واحدةً للكلّ فلا تُخلَط أيّام.\n")

    import operator_entry_live as oel
    try:
        _u, _c, _s, uni_all = oel._load_universe()
    except Exception as e:                                        # noqa: BLE001
        print(f"⛔ تعذّر بناءُ الكون: {type(e).__name__}: {e}")
        return 2
    syms = [r["symbol"] for r in uni_all]
    print(f"👁️ الكون: {len(syms)} سهمًا (نفسُ كونِ المُشغِّل · بلا استثناء)")

    import concurrent.futures as cf
    t0, data, pc, fails = time.time(), {}, {}, 0

    def _one(s):
        try:
            return (s, MZ.day_minutes(s, day=day), prev_close(s, day))
        except Exception:                                        # noqa: BLE001
            return (s, None, None)

    with cf.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for s, bars, p in pool.map(_one, syms):
            if bars and len(bars) >= 5 and p:
                data[s], pc[s] = bars, p
            else:
                fails += 1
    print(f"📥 شموعُ اليوم ‏+ إغلاقُ الأمس: {len(data)} من {len(syms)} · "
          f"تعذّر {fails} · {round(time.time() - t0, 1)}ث")
    if not data:
        print("⛔ صفرُ بيانات — لا قياس.")
        return 2

    # 🏃 المجتمعُ `B`: المتحرّكون (‏§③)
    movers, day_gain = [], {}
    for s, bars in data.items():
        hi = max(float(b["c"]) for b in bars)
        g = (hi / pc[s] - 1.0) * 100.0
        day_gain[s] = g
        if g >= MOVER_PCT:
            movers.append(s)
    print(f"🏃 المتحرّكون (‏+{MOVER_PCT:.0f}% فأكثر عن إغلاق الأمس): "
          f"**{len(movers)}** — {', '.join(sorted(movers)[:14])}"
          f"{' …' if len(movers) > 14 else ''}\n")

    # ── الأذرعُ السبع
    res, dropped = {}, 0
    for an, arm in ARMS.items():
        rows, fires, syms_hit = {}, 0, []
        for s, bars in data.items():
            i, t = anchor_of(bars, arm)
            fires += len(all_fires(bars, arm))
            if i is None:
                continue
            late = (t["price"] / pc[s] - 1.0) * 100.0
            if late > LATE_SANE_MAX:
                continue                       # 🔴 تشويهُ تقسيمٍ ⇒ يُعَدّ خارجًا
            syms_hit.append(s)
            rows[s] = {"i": i, "late": late, "price": t["price"],
                       "fruit": LM.fruit(bars, i, t["price"])}
        fr = [r["fruit"] for r in rows.values() if r["fruit"] is not None]
        res[an] = {"rows": rows, "fires": fires, "syms": syms_hit,
                   "late": _med([r["late"] for r in rows.values()]),
                   "fruit_n": len(fr),
                   "fruit": ((100.0 * sum(1 for f in fr if f >= LM.FRUIT_PCT)
                              / len(fr)) if fr else None)}
    for s, bars in data.items():
        i, t = anchor_of(bars, ARMS["G0"])
        if i is not None and (t["price"] / pc[s] - 1.0) * 100.0 > LATE_SANE_MAX:
            dropped += 1

    print("=" * 74)
    print("① الأذرعُ السبع — التأخّرُ والكلفةُ والإثمار (‏§⑤)")
    print("=" * 74)
    print("  ذراع | تأخّرٌ وسيط | أسهمٌ | إشعارات | أثمر٪ (مقام) | متحرّكون | نوعُ الذراع")
    g0 = res["G0"]
    for an in ARMS:
        c = res[an]
        lt = "—" if c["late"] is None else f"{c['late']:+.1f}%"
        fp = ("—" if c["fruit"] is None
              else f"{c['fruit']:.0f}% ({c['fruit_n']})")
        mv = sum(1 for s in movers if s in c["rows"])
        kind = ("قابلٌ للتوصية" if an in COACHABLE else
                "🔴 رقمُ المالك" if an in OWNER_COST else
                "⛔ حدٌّ أعلى" if an in UPPER_BOUND else "الأساس")
        print(f"  {an:>4} | {lt:>10} | {len(c['syms']):>5} | {c['fires']:>7} | "
              f"{fp:>13} | {mv:>8} | {kind}")
    print(f"\n  📉 مستبعَدون بتشويهِ تقسيمٍ (تأخّرٌ فوق {LATE_SANE_MAX:.0f}%): "
          f"**{dropped}** — يُعَدّون ولا يُخمَّنون (‏§⑨-4)")
    # ⏱️ **§⑤-2 المُسجَّلُ: الأسبقيّةُ بالدقائق — مقترنةً لنفس السهم.**
    #    🔴 وهو المقياسُ **المُقترَن** الذي يعزل أثرَ الذراع عن **تبدّلِ مجموعة
    #    الأسهم**: وسيطُ «التأخّر» يُقاس على مجموعتين مختلفتين فيتحرّك بدخولِ سهمٍ
    #    جديدٍ لا بتحسّنِ سهمٍ قائم. ⇒ يُطبَع الاثنان ولا يُستبدَل أحدُهما بالآخر.
    print("\n  ⏱️ **الأسبقيّةُ مقترنةً لنفس السهم** (‏§⑤-2 — وسيطُ الدقائق قبل "
          "مِرساةِ `G0` · والسالبُ يعني أبطأ):")
    for an in ARMS:
        if an == "G0":
            continue
        pair = [g0["rows"][s]["i"] - res[an]["rows"][s]["i"]
                for s in g0["rows"] if s in res[an]["rows"]]
        dlat = [g0["rows"][s]["late"] - res[an]["rows"][s]["late"]
                for s in g0["rows"] if s in res[an]["rows"]]
        # 📌 **وصفيٌّ خارج قاعدة القرار (لم يُسجَّل):** الوسيطُ المقترَنُ خرج
        #    **صفرًا لكلّ ذراع** — وهو **صحيحٌ حسابيًّا ومُضلِّلٌ ملخَّصًا**: أكثرُ
        #    الأسهم لا يتحرّك أنملةً والمكسبُ **مركَّزٌ في أقلّيّة**. ⇒ يُنشَر معه
        #    **كم سهمًا تحسّن ووسيطُ تحسّنِهم** — يُقرأ ولا يُبنى عليه حكم.
        imp = [x for x in pair if x > 0]
        impl = [x for x in dlat if x > 0.05]
        print(f"   • {an}: وسيطٌ **{_med(pair):+.0f} دقيقة** · وتأخّرٌ أقلُّ بـ"
              f"**{_med(dlat):+.1f} نقطة** (‏{len(pair)} سهمًا مشتركًا)"
              f"\n      ↳ 📌 وصفيٌّ: **تحسّن {len(imp)} من {len(pair)}** "
              f"({100.0 * len(imp) / max(1, len(pair)):.0f}%) · ووسيطُ تحسّنِهم "
              f"**{('—' if not imp else f'{_med(imp):.0f} دقيقة')}** و"
              f"**{('—' if not impl else f'{_med(impl):.1f} نقطة')}**")
    print("  " + " · ".join(f"{k}: {v}" for k, v in ARM_DESC.items()))

    print("\n" + "=" * 74)
    print("② قاعدةُ القرار (‏§⑦) — تُطبَّق على `engineering` وحدَها")
    print("=" * 74)
    best = None
    for an in COACHABLE:
        c = res[an]
        d_late = ((g0["late"] - c["late"])
                  if (c["late"] is not None and g0["late"] is not None) else None)
        d_fr = ((c["fruit"] - g0["fruit"])
                if (c["fruit"] is not None and g0["fruit"] is not None) else None)
        d_n = (100.0 * (c["fires"] - g0["fires"]) / g0["fires"]
               if g0["fires"] else 0.0)
        lost = [s for s in g0["rows"] if s not in c["rows"]]
        k1 = d_late is not None and d_late >= 5.0
        k2 = d_fr is not None and d_fr >= -JITTER_PP
        k3 = d_n <= 50.0
        k4 = not lost
        good = k1 and k2 and k3 and k4
        if good and best is None:
            best = an
        print(f"  {an}: تأخّرٌ أقلُّ بـ"
              f"{('—' if d_late is None else f'{d_late:.1f}ن')} "
              f"{'✅' if k1 else '❌'} · إثمارٌ "
              f"{('—' if d_fr is None else f'{d_fr:+.1f}ن')} "
              f"{'✅' if k2 else '❌'} · إشعاراتٌ {d_n:+.0f}% "
              f"{'✅' if k3 else '❌'} · فَقدُ أسهمٍ {len(lost)} "
              f"{'✅' if k4 else '❌'} ⇒ "
              f"{'✅ تُوصى' if good else '🔴 لا تُوصى'}")
    if best:
        print(f"\n  ⇒ **يُوصى بـ`{best}`** — والقرارُ للمالك.")
    else:
        print("\n  ⇒ 🔴 **لا ذراعَ `engineering` تستوفي الأربعة** ⇒ التأخّرُ ثمنُ "
              "أرقامِ المالك نفسِها (‏`G4`/`G5` أدناه **كلفةً لا توصية**).")

    print("\n" + "=" * 74)
    print("③ 🔴 منحنى كلفةِ أرقامِ المالك — يُعرَض ولا يُوصى به (‏§②/§⑦)")
    print("=" * 74)
    for an in OWNER_COST + UPPER_BOUND:
        c = res[an]
        d_late = ((g0["late"] - c["late"])
                  if (c["late"] is not None and g0["late"] is not None) else None)
        d_n = (100.0 * (c["fires"] - g0["fires"]) / g0["fires"]
               if g0["fires"] else 0.0)
        d_fr = ((c["fruit"] - g0["fruit"])
                if (c["fruit"] is not None and g0["fruit"] is not None) else None)
        print(f"  {an}: تأخّرٌ أقلُّ بـ"
              f"{('—' if d_late is None else f'{d_late:.1f}ن')} · إشعاراتٌ "
              f"{d_n:+.0f}% · أسهمٌ {len(c['syms'])} (‏{len(g0['syms'])} أساسًا) · "
              f"إثمارٌ {('—' if d_fr is None else f'{d_fr:+.1f}ن')}")

    print("\n" + "=" * 74)
    print(f"④ 🧱 جدارُ البداية عند ‏+{T10_PCT:.0f}% (‏§⑥) — مَن يحجب حين تبدأ الحركة؟")
    print("=" * 74)
    walls, n_t10, late_at = {}, 0, []
    for s in movers:
        bars, p = data[s], pc[s]
        t10 = next((i for i in range(2, len(bars) - 1)
                    if (float(bars[i]["c"]) / p - 1.0) * 100.0 >= T10_PCT), None)
        if t10 is None:
            continue
        n_t10 += 1
        w = first_wall(gate_trace(bars, t10, ARMS["G0"]))
        walls[w or "عبرت"] = walls.get(w or "عبرت", 0) + 1
        a, t = anchor_of(bars, ARMS["G0"])
        if a is not None:
            late_at.append(a - t10)
    print(f"  متحرّكون بلغوا ‏+{T10_PCT:.0f}%: **{n_t10}**")
    for w, n in sorted(walls.items(), key=lambda kv: -kv[1]):
        print(f"   • {w}: **{n}** ({100.0 * n / max(1, n_t10):.0f}%)")
    if late_at:
        print(f"  ⏱️ ومن ‏+{T10_PCT:.0f}% إلى المِرساة: وسيطُ "
              f"**{_med(late_at):.0f} دقيقة** (‏{len(late_at)} سهمًا)")

    print("\n" + "=" * 74)
    print("⑤ الأسهمُ بأسمائها — تأخّرُ `G0` مقابل أفضلِ ذراع")
    print("=" * 74)
    shown = 0
    for s in sorted(g0["rows"], key=lambda z: -g0["rows"][z]["late"]):
        if shown >= 25:
            print(f"   … و{len(g0['rows']) - shown} أخرى (قصٌّ **مُعلَن**)")
            break
        r = g0["rows"][s]
        alt = res["G6"]["rows"].get(s)
        print(f"   ${s:<6} تأخّرُ `G0` **{r['late']:+7.1f}%** عند الدقيقة "
              f"{r['i']:>3} بسعر {r['price']:.4f}"
              + (f" · بلا شرطِ رفعةٍ {alt['late']:+.1f}% عند {alt['i']}"
                 if alt else " · بلا شرطِ رفعةٍ: لا مِرساة")
              + f" · قمّةُ اليوم {day_gain[s]:+.0f}%")
        shown += 1
    if not g0["rows"]:
        print("   (لا شيء)")

    print("\n" + "=" * 74)
    print("⑥ حدودُ صدقٍ (‏§⑨ — تُقرأ مع الأرقام لا بعدها)")
    print("=" * 74)
    print("  1. جلسةٌ واحدة ⇒ تشخيصٌ لا تجربةَ عائد · **ولا صفقةَ تُقاس**.")
    print(f"  2. «الإثمار» بلوغُ ‏+{LM.FRUIT_PCT:.0f}% خلال {LM.FRUIT_MIN} دقيقة "
          "— **سعرٌ مطبوعٌ لا تنفيذ** ⇒ سقفٌ متفائل.")
    print("  3. الإعادةُ ترى كلَّ دقيقةٍ والحيُّ يلفّ كلَّ ‏≈60 ثانية ⇒ **الأسبقيّةُ "
          "سقف**.")
    print(f"  4. إغلاقُ الأمس **معدَّلٌ بالتقسيمات** ⇒ استُبعد {dropped} بتأخّرٍ "
          f"فوق {LATE_SANE_MAX:.0f}% (يُعَدّ ولا يُخمَّن).")
    print(f"  5. **`t10` علامةٌ مختارةٌ لا قانون** (‏+{T10_PCT:.0f}%).")
    print("  6. والكونُ رقيقٌ (أسهمُ فيصل) ⇒ لا يُعمَّم على كونٍ سائل.")
    print("  7. و«الإشعارات» **عبورُ دقائقَ لا رسائل** — عمودُ «أسهم» هو عددُ "
          "المراسي أي الرسائلُ الأولى فعلًا.")
    print(f"\n⏱️ زمنُ التشغيل: {round(time.time() - t0, 1)}ث")
    return 0


if __name__ == "__main__":
    sys.exit(main())
