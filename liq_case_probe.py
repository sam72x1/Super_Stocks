#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔎 **مِجَسُّ الحالة** — «ليه ما وصلني تحديثٌ لسهم كذا؟» يُجاب بالأرقام لا بالرأي.

يُعيد تشغيل **قواعدَ الإنتاج نفسِها** (`liq_stage_events`) على شموع سهمٍ بعينه دقيقةً
دقيقة، ويطبع لكلّ دقيقةٍ **ما فعلته كلُّ بوّابةٍ على حدة** ⇒ فيُقرأ سببُ الصمت
**مُسمًّى** بدل أن يُستنتَج.

🔒 **قراءةٌ/تشخيصٌ فقط:** لا يكتب حالةً ولا يرسل تلغرامًا ولا يمسّ فرزًا ولا جذرًا.
التشغيل: `LIQ_CASE=XOS,AUUD python3 liq_case_probe.py`
"""
import os
import re
import sys

os.environ.setdefault("SCREENER_MODE", "PROBE")
import Super_stock as bot                                          # noqa: E402

WINDOW_MIN = 480
# ‏📉 إغلاقُ الأمس اختياريٌّ من البيئة (‏LIQ_CASE_PREV="ANPA:3.80")
_PREV_CLOSE = {}
for _kv in (os.environ.get("LIQ_CASE_PREV") or "").split(","):
    if ":" in _kv:
        _s, _v = _kv.split(":", 1)
        try:
            _PREV_CLOSE[_s.strip().upper()] = float(_v)
        except ValueError:
            pass


def gate_trace(bars, i):
    """🔬 يفكّك بوّابةَ الدقيقة `i` (فهرسُ شمعةٍ **مكتملة**) إلى شروطها المسمّاة."""
    closed = bars[:i + 1]
    last = closed[-1]
    prior = [float(b["v"]) for b in closed[:-1][-64:]]
    avg = sum(prior) / len(prior) if prior else 0.0
    vx = (float(last["v"]) / avg) if avg > 0 else 0.0
    usd = float(last["c"]) * float(last["v"])
    n = max(1, int(bot.LIQ_CUM_MINUTES))
    cum = sum(float(b["c"]) * float(b["v"]) for b in closed[-n:])
    o_, c_ = float(last.get("o") or last["c"]), float(last["c"])
    h_, l_ = float(last.get("h") or c_), float(last.get("l") or c_)
    rise = ((c_ - o_) / o_ * 100.0) if o_ > 0 else 0.0
    rng = h_ - l_
    cpos = 1.0 if rng <= 0 else (c_ - l_) / rng
    return {"usd": usd, "cum": cum, "vx": vx, "rise": rise, "cpos": cpos,
            "green": c_ >= o_, "price": c_,
            "g_vol": vx >= float(bot.CONFIG["IGNITION_VOL_MULT"]),
            "g_floor": cum >= float(bot.LIQ_MIN_USD),
            "g_green": c_ >= o_,
            "g_rise": rise >= float(bot.LIQ_MIN_MOVE_PCT),
            "g_cpos": cpos >= float(bot.LIQ_CLOSE_POS_MIN)}


def why(t):
    """سببُ الصمت **مُسمًّى** — أوّلُ شرطٍ ساقطٍ بترتيب البوّابة."""
    if not t["g_vol"]:
        return f"قفزةُ حجمٍ {t['vx']:.1f}× دون 3"
    if not t["g_floor"]:
        return f"الأرضيةُ التراكميّة ${t['cum']:,.0f} دون 30 ألفًا"
    if not t["g_green"]:
        return "حمراء"
    if not t["g_rise"]:
        return f"رفعةُ الدقيقة {t['rise']:.1f}% دون 5%"
    if not t["g_cpos"]:
        return f"الإغلاقُ في النصف الأسفل ({t['cpos']:.2f})"
    return "—"


def ny_clock(ms):
    """⏰ ساعةُ نيويورك لطابعٍ بالملّي — فاشلةٌ-آمنة (‏«??:??» عند التعذّر)."""
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        return datetime.fromtimestamp(int(ms) / 1000.0,
                                      ZoneInfo("America/New_York")).strftime("%H:%M")
    except Exception:                                            # noqa: BLE001
        return "??:??"


def pre_anchor_report(bars, anchor, prev_close=None):
    """🕰️ **ما قبل المِرساة** — أينَ ذهب السعرُ ولماذا صمتت البوّابةُ دقيقةً دقيقة.

    الأصلُ كان يبدأ التفكيكَ **من المِرساة** فيَعمى عن السؤال الذي يسأله المالكُ
    عادةً: «السهمُ صعد قبل الإشعار ولم يصلني شيء». هذي الكتلةُ **إضافةٌ محضة**
    (لا تمسّ سطرًا قائمًا): تطبع القمّةَ قبل المِرساة ووقتَها · وكم دقيقةً
    **عبرت كلَّ البوّابات** قبلها (يجب أن تكون **صفرًا**، وإلّا فالحيُّ فوّت
    مِرساةً أبكر) · وجدولَ الأسباب المسمّاة.
    """
    end = (anchor if anchor is not None else len(bars) - 1)
    rng = list(range(3, max(3, end)))
    print("\n🕰️ ما قبل المِرساة — سببُ الصمت دقيقةً دقيقة")
    if not rng:
        print("   (لا دقائقَ قبلها)")
        return
    hi_c = max(float(bars[i]["c"]) for i in rng)
    hi_h = max(float(bars[i].get("h") or bars[i]["c"]) for i in rng)
    i_hi = max(rng, key=lambda i: float(bars[i].get("h") or bars[i]["c"]))
    lo_c = min(float(bars[i]["c"]) for i in rng)
    pc = f" = {(hi_h / prev_close - 1) * 100:+.1f}% عن الأمس" if prev_close else ""
    print(f"   ‏{len(rng)} دقيقةً · أوّلُها {ny_clock(bars[rng[0]]['t'])} "
          f"وآخرُها {ny_clock(bars[rng[-1]]['t'])}")
    print(f"   📈 أعلى قمّةٍ قبل المِرساة: {hi_h:.4f} عند "
          f"{ny_clock(bars[i_hi]['t'])}{pc} · أعلى إغلاق {hi_c:.4f} · "
          f"أدنى إغلاق {lo_c:.4f}")
    passed, reasons = [], {}
    for i in rng:
        t = gate_trace(bars, i)
        if all(t[k] for k in ("g_vol", "g_floor", "g_green", "g_rise", "g_cpos")):
            passed.append((i, t))
        else:
            r = why(t).split("(")[0].split("$")[0].strip()
            r = re.sub(r"[-+]?\d[\d,.]*", "N", r)
            reasons[r] = reasons.get(r, 0) + 1
    print(f"   🚦 عبرت كلَّ البوّابات قبل المِرساة: **{len(passed)}** دقيقة "
          + ("⇒ ✅ متّسقٌ مع الحيّ (لا مِرساةَ أبكر ممكنة)"
             if not passed else "⇒ 🔴 الحيُّ فوّت مِرساةً أبكر!"))
    for i, t in passed[:8]:
        print(f"      [{ny_clock(bars[i]['t'])}] سعر {t['price']:.4f} · "
              f"${t['usd']:,.0f} · {t['vx']:.1f}× · رفعة {t['rise']:.1f}%")
    print("   🔴 أسبابُ الصمت (مُكمِّلةٌ للعابرات — المجموع = عددُ الدقائق):")
    for r, n in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"      {n:>4} × {r}")
    # 🥇 أعنفُ عشرِ دقائقَ رفعةً قبل المِرساة — لِمَ لم تُطلق أيٌّ منها؟
    top = sorted(rng, key=lambda i: -gate_trace(bars, i)["rise"])[:10]
    print("   🥇 أعنفُ الدقائق رفعةً قبل المِرساة (ولماذا صمتت):")
    print("      وقت | سعر | سيولة | قفزة | رفعة | السبب")
    for i in sorted(top):
        t = gate_trace(bars, i)
        print(f"      {ny_clock(bars[i]['t'])} | {t['price']:.4f} | "
              f"${t['usd']:>9,.0f} | {t['vx']:>5.1f}× | {t['rise']:>5.1f}% | {why(t)}")


def run(sym):
    bars = bot.polygon_minute_bars(sym, minutes=WINDOW_MIN)
    if not bars or len(bars) < 5:
        print(f"⛔ {sym}: لا شموع.")
        return
    print("=" * 72)
    print(f"🔎 ${sym} — {len(bars)} شمعةَ دقيقة")
    print("=" * 72)
    # ▶️ إعادةٌ بقواعد الإنتاج: دقيقةٌ مكتملةٌ في كلّ خطوة
    st, evs = {}, []
    for k in range(3, len(bars) + 1):
        e, st = bot.liq_stage_events(bars[max(0, k - bot.LIQ_WINDOW_MIN):k], st)
        for x in (e or []):
            evs.append((k - 2, x))
    print(f"📩 ما كان سيُرسَل بقواعد الإنتاج: **{len(evs)}** حدثًا")
    for k, e in evs:
        print(f"   [دقيقة {k}] {e['stage']} · ${e['usd']:,} · سعر "
              f"{e['price']} · رفعة {e.get('move')}% · {(e.get('class') or ('',''))[0]}")
    if not evs:
        print("   (لا شيء)")

    anchor = evs[0][0] if evs else None
    pre_anchor_report(bars, anchor, prev_close=_PREV_CLOSE.get(sym))
    if anchor is None:
        return
    a = gate_trace(bars, anchor)
    print(f"\n🚩 المِرساةُ عند الدقيقة {anchor}: سعر {a['price']:.4f} · "
          f"سيولة ${a['usd']:,.0f} · قفزةٌ {a['vx']:.0f}× · رفعة {a['rise']:.1f}%")
    # 📈 أين وصل السعرُ بعد المِرساة؟
    after = bars[anchor + 1:]
    if after:
        hi = max(float(b["c"]) for b in after)
        print(f"📈 أعلى إغلاقٍ بعدها: {hi:.4f} = "
              f"{(hi / a['price'] - 1) * 100:+.1f}% عن سعر الإشعار "
              f"(‏{len(after)} دقيقةً تالية)")
    # 🔴 لماذا صمتت البوّابةُ في الدقائق التالية؟ التفكيكُ الكامل
    print("\n🔴 الدقائقُ التالية — لماذا لا تحديث؟ (سببٌ مُسمًّى لكلّ دقيقة)")
    print("   دقيقة | سعر | سيولة | قفزة | رفعة | فوق القمّة؟ | السبب")
    peak = a["usd"]
    n_hw, n_other, n_pass = 0, 0, 0
    for i in range(anchor + 1, len(bars) - 1):
        t = gate_trace(bars, i)
        gates_ok = all(t[k] for k in ("g_vol", "g_floor", "g_green", "g_rise",
                                      "g_cpos"))
        over = t["usd"] > peak
        if gates_ok and not over:
            n_hw += 1
            reason = f"🔴 **قمّةُ الماء** (${t['usd']:,.0f} دون ${peak:,.0f})"
        elif gates_ok and over:
            n_pass += 1
            peak = t["usd"]
            reason = "✅ تحديثٌ يُرسَل"
        else:
            n_other += 1
            reason = why(t)
        if i - anchor <= 12 or gates_ok:
            print(f"   {i:>5} | {t['price']:.4f} | ${t['usd']:>10,.0f} | "
                  f"{t['vx']:>5.1f}× | {t['rise']:>6.1f}% | "
                  f"{'نعم' if over else 'لا':>4} | {reason}")
    print(f"\n   ⇒ الحصيلة: **{n_hw} دقيقةً عبرت كلَّ البوّابات وكتمتها قمّةُ "
          f"الماء** · {n_pass} تحديثًا يُرسَل · {n_other} سقطت لسببٍ آخر")
    # 🕵️ تغطيةُ قراءة المضارب على دقيقة المِرساة
    shares = a["usd"] / a["price"] if a["price"] else 0
    print(f"\n🕵️ تغطيةُ قراءة المضارب: دقيقةُ المِرساة ‏≈{shares:,.0f} سهمًا · "
          f"و`operator_flow` يقرأ **آخر 250 صفقة** فقط ⇒ لو كان وسيطُ الصفقة "
          f"‏≈200 سهمًا فالمقروءُ ‏≈50,000 سهمًا "
          f"(‏{min(100.0, 5_000_000.0 / max(shares, 1)):.0f}% تقديرًا) — "
          "**والمعروضُ في رسالة المالك كان أصغرَ بمراتب**.")


def main():
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        print("⛔ لا مفتاح Polygon — لا قياس.")
        return 2
    syms = [s.strip().upper() for s in
            (os.environ.get("LIQ_CASE") or "XOS").split(",") if s.strip()]
    print(f"🔎 مِجَسُّ الحالة — {', '.join(syms)}\n"
          f"   العتباتُ النافذة: أرضية ${bot.LIQ_MIN_USD:,} على "
          f"{bot.LIQ_CUM_MINUTES} دقائق · رفعة {bot.LIQ_MIN_MOVE_PCT}% · "
          f"قفزةٌ {bot.CONFIG['IGNITION_VOL_MULT']}×\n")
    for s in syms:
        run(s)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
