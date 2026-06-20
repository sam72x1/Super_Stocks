# -*- coding: utf-8 -*-
"""
==========================================================
تحليل سهم واحد عند الطلب (Manual / On-Demand Analyzer)
==========================================================
ملف منفصل تماماً — لا يعدّل Super_stock.py ولا يلمس الفرز التلقائي.

الفكرة: تكتب رمز سهم، فيحلله بنفس نظام البوت بالضبط (نفس الدوال
والمؤشرات والفريمات والأنماط)، لكن:
  • لا يرفض السهم إذا فشل بوابة — بل يبيّن نجاح/فشل كل بوابة.
  • يعطي درجة فنية من 100 حتى لو فشل بوابات (مثل سهم تحت $2).
  • يحسب المستويات (وقف/أهداف) ويرسل بطاقة كاملة عبر تيليجرام.

التشغيل (عبر GitHub، نفس آلية الإرسال اليومي):
  متغير البيئة:  ANALYZE=BBLG   →   python analyze_one.py

كل العمليات الثقيلة (الرسم، الإثراء، التحميل) مُعاد استخدامها من
الملف الرئيسي — هذا الملف مجرد "غلاف" رفيع فوقه.
"""
import os
import math
import numpy as np

# استيراد الملف الرئيسي (يدعم الاسم بحرف كبير في GitHub أو صغير محلياً)
try:
    import Super_stock as bot
except ImportError:                       # بديل للتشغيل المحلي/الاختبار
    import super_stock as bot

C = bot.CONFIG


# ==========================================================
# التحليل عند الطلب — يحسب كل بوابة كمعلومة (بلا رفض)
# ==========================================================
def analyze_on_demand(sym: str):
    """يرجع (result_dict, gates) عند النجاح، أو (None, رسالة_خطأ) عند تعذّر البيانات.
    result_dict يحوي كل مفاتيح build_message + درجة فنية محسوبة دائماً.
    gates = قائمة (اسم البوابة، نجح؟، تفصيل) لكل البوابات الإلزامية السبع."""
    sym = sym.strip().upper()
    try:
        data = bot.download_history([sym])
    except Exception as e:
        return None, f"تعذّر الاتصال لجلب بيانات {sym}: {e}"
    df = data.get(sym)
    if df is None or len(df) < C["MIN_BARS"]:
        return None, (f"تعذّر جلب بيانات كافية لـ {sym}. "
                      "غالباً: رمز خاطئ، سهم جديد جداً، أو سيولة شبه معدومة "
                      "(أقل من الحد الأدنى للشموع المطلوبة).")

    close = df["Close"]
    high, low, vol = df["High"], df["Low"], df["Volume"]
    c = close.values
    price = float(c[-1])

    gates = []   # (الاسم، نجح؟، التفصيل)

    # ===== البوابات الإلزامية السبع (تُحسب كلها كمعلومة) =====
    # M1: السعر
    g1 = price >= C["MIN_PRICE"]
    gates.append((f"السعر فوق ${C['MIN_PRICE']:.0f}", g1, f"${price:.2f}"))

    # M2: الهبوط من قمة 52 أسبوع
    hi52 = float(high.tail(252).max())
    drop_pct = (1.0 - price / hi52) * 100.0 if hi52 > 0 else 0.0
    g2 = (drop_pct >= C["MIN_DROP_PCT"]) and (drop_pct <= C["MAX_DROP_PCT"])
    gates.append((f"الهبوط ضمن {C['MIN_DROP_PCT']:.0f}–{C['MAX_DROP_PCT']:.0f}%",
                  g2, f"{drop_pct:.0f}%"))

    # M3: الانفجار السابق
    best_spike, n_spikes = bot.spike_info(c, exclude_last=C["BASE_WINDOW"])
    g3 = best_spike >= C["PRIOR_SPIKE_PCT"]
    gates.append((f"انفجار سابق ≥ {C['PRIOR_SPIKE_PCT']:.0f}%",
                  g3, f"{best_spike:.0f}% ({n_spikes} انفجار موثّق)"))

    # M4: قاعدة ضيقة + لم ينفجر بعد
    bw = C["BASE_WINDOW"]
    base_hi = float(high.tail(bw).max())
    base_lo = float(low.tail(bw).min())
    base_range = (base_hi / base_lo - 1.0) * 100.0 if base_lo > 0 else 9999.0
    gain5 = (c[-1] / c[-6] - 1.0) * 100.0 if len(c) > 6 else 0.0
    g4 = (base_range <= C["BASE_RANGE_MAX_PCT"]) and \
         (gain5 <= C["RECENT_RISE_BLOCK_PCT"])
    gates.append((f"قاعدة ضيقة ≤{C['BASE_RANGE_MAX_PCT']:.0f}% ولم ينفجر",
                  g4, f"مدى القاعدة {base_range:.0f}%، حركة 5 جلسات {gain5:+.0f}%"))

    # M5: السيولة الدولارية
    dvol = float((close * vol).tail(20).mean())
    g5 = math.isfinite(dvol) and dvol >= C["MIN_DOLLAR_VOL"]
    gates.append((f"سيولة ≥ {bot.fmt_money(C['MIN_DOLLAR_VOL'])}/يوم",
                  g5, f"{bot.fmt_money(dvol)}/يوم"))

    # M6: توافق الفريمات
    mtf = bot.multi_timeframe(df)
    g6 = mtf["count"] >= C["TF_MIN_REVERSALS"]
    gates.append((f"توافق الفريمات ≥ {C['TF_MIN_REVERSALS']}/3",
                  g6, f"{mtf['count']}/3 — {mtf['display']}"))

    # M7: نمط شمعة انعكاسي
    patterns = mtf["patterns"]
    g7 = bool(patterns)
    gates.append(("نمط شمعة انعكاسي (يومي/أسبوعي)",
                  g7, "، ".join(patterns) if patterns else "لا يوجد"))

    # ===== حساب الدرجة الفنية (نفس أوزان البوت — تُحسب دائماً) =====
    score = 0
    flags = []
    warnings = []

    if best_spike >= C["SPIKE_VERIFY_PCT"]:
        warnings.append(f"انفجار سابق ضخم ({best_spike:.0f}%) — "
                        "تحقق يدوياً من تقسيم عكسي")
    if dvol < C["LOW_LIQ_WARN"]:
        warnings.append(f"سيولة منخفضة ({bot.fmt_money(dvol)}/يوم)")

    rsi_s = bot.rsi(close)
    r_now, r_prev = float(rsi_s.iloc[-1]), float(rsi_s.iloc[-2])
    r_min_recent = float(rsi_s.tail(C["RSI_RECENT_WINDOW"]).min())
    if (r_min_recent <= C["RSI_OVERSOLD"] and r_now > r_prev
            and r_now <= C["RSI_MAX_NOW"]):
        score += 15
        flags.append(f"RSI تشبع وانحناء (قاع {r_min_recent:.0f}→{r_now:.0f})")

    m_line, m_sig = bot.macd(close)
    if (m_line.iloc[-5:] > m_sig.iloc[-5:]).any() and \
       float(m_line.iloc[-1]) >= float(m_sig.iloc[-1]):
        score += 10
        flags.append("تقاطع MACD")

    k_line, k_sig = bot.kst(close)
    try:
        if float(k_line.iloc[-1]) > float(k_sig.iloc[-1]) and \
           float(k_line.iloc[-1]) > float(k_line.iloc[-3]):
            score += 10
            flags.append("KST صاعد")
    except Exception:
        pass

    v = vol.values.astype(float)
    v20 = float(vol.tail(20).mean())
    v5 = float(vol.tail(5).mean())
    big_green = False
    if v20 > 0 and len(c) > 21:
        for i in range(len(c) - 20, len(c)):
            if v[i] >= C["VOL_SPIKE_MULT"] * v20 and c[i] > df["Open"].values[i]:
                big_green = True
                break
    if big_green:
        score += 10
        flags.append("شمعة فوليوم ضخمة")
    if v20 > 0 and v5 <= C["VOL_DRY_RATIO"] * v20:
        score += 5
        flags.append("جفاف بيع")

    sma30 = float(close.rolling(30).mean().iloc[-1])
    sma50 = float(close.rolling(50).mean().iloc[-1])
    near_ma = any(ma > 0 and abs(price / ma - 1.0) <= 0.05
                  for ma in (sma30, sma50))
    if near_ma:
        score += 10
        flags.append("يرتكز على متوسط 30/50")

    if n_spikes >= 2:
        score += 15
        flags.append(f"معيد إجرام ({n_spikes} انفجارات)")

    ps = bot.pivot_stability(low.values.astype(float), c)
    ready = False
    if ps and ps["held"]:
        score += 15
        ready = bool(ps["ready"])
        flags.append(f"ثبات {ps['bars_after']} جلسات فوق القاع")

    mfi_s = bot.mfi(high, low, close, vol)
    sweep = False
    lows_arr = low.values.astype(float)
    if len(lows_arr) > 35:
        prior_low = float(np.min(lows_arr[-35:-10]))
        recent_min = float(np.min(lows_arr[-10:]))
        if (prior_low > 0 and recent_min < prior_low * 0.995
                and price > prior_low
                and float(mfi_s.iloc[-1]) >= float(mfi_s.tail(10).min())):
            sweep = True
    if sweep:
        score += 10
        flags.append("مسح سيولة (كسر قاع سابق واستعادة)")

    if mtf["count"] >= 3:
        score += 10
        flags.append("توافق 3 فريمات")
    if any(p in bot.STRONG_PATTERNS for p in patterns):
        score += 5
        flags.append("نمط شمعة قوي")

    score = int(min(score, 100))

    # ===== المستويات (نفس منطق البوت) =====
    pivot = ps["pivot"] if ps else float(low.tail(20).min())
    s_lo, s_hi = C["STOP_BELOW_LOW_PCT"]
    stop_hi = pivot * (1 - s_lo / 100.0)
    stop_lo = pivot * (1 - s_hi / 100.0)
    big = price >= C["LARGE_PRICE_CUT"]
    d_lo, d_hi = (C["SWEEP_LARGE_PCT"] if big else C["SWEEP_SMALL_PCT"])
    sweep_lo = pivot * (1 - d_hi / 100.0)
    sweep_hi = pivot * (1 - d_lo / 100.0)

    raw_t1 = bot.first_target(df)
    raw_t2 = max(sma30, sma50)
    raw_t3 = float(high.tail(60).max())
    cap = price * C["TARGET_CAP_MULT"]
    min_first = price * (1.0 + C["MIN_T1_GAIN_PCT"] / 100.0)
    gap = 1.0 + C["MIN_TARGET_GAP_PCT"] / 100.0
    cands = sorted(t for t in (raw_t1, raw_t2, raw_t3) if min_first <= t <= cap)
    targets = []
    for t in cands:
        if not targets or t >= targets[-1] * gap:
            targets.append(round(float(t), 2))
    if not targets:
        targets = [round(price * 1.25, 2)]
    while len(targets) < 3:
        targets.append(round(targets[-1] * 1.25, 2))
    t1, t2, t3 = targets[0], targets[1], targets[2]

    risk = max(price - stop_lo, 1e-9)
    rr = (t1 - price) / risk
    rr2 = (t2 - price) / risk
    if rr < C["MIN_RR_T1"]:
        warnings.append(f"عائد/مخاطرة الهدف الأول ضعيف ({rr:.1f}× < "
                        f"{C['MIN_RR_T1']:.1f}× المطلوب)")

    # نتيجة كاملة بكل المفاتيح التي يحتاجها build_message + الإثراء
    result = {
        "symbol": sym, "price": price, "score": score,
        "drop_pct": drop_pct, "best_spike": best_spike,
        "n_spikes": n_spikes, "base_range": base_range,
        "rsi": r_now, "dollar_vol": dvol,
        "pivot": pivot, "stop": (stop_lo, stop_hi),
        "sweep": (sweep_lo, sweep_hi),
        "t1": t1, "t2": t2, "t3": t3, "rr": rr, "rr2": rr2,
        "ready": ready, "flags": flags, "warnings": warnings,
        "tf_count": mtf["count"], "tf_display": mtf["display"],
        "patterns": patterns,
        # مفاتيح اختيارية يملؤها الإثراء — نهيّئها لتفادي أي خطأ
        "short_pct": None, "float": None, "recent_split": None,
        "news": [], "tf4h": "غير متوفر",
        "sec_status": None, "sec_filings": [],
    }
    return result, gates


# ==========================================================
# بناء الرسالة: ترويسة البوابات + البطاقة الكاملة (إعادة استخدام build_message)
# ==========================================================
def render_ondemand(result: dict, gates: list) -> str:
    passed = sum(1 for _, ok, _ in gates if ok)
    total = len(gates)
    failed = [name for name, ok, _ in gates if not ok]
    qualifies = (passed == total
                 and result["score"] >= C["SCORE_MIN"]
                 and result["rr"] >= C["MIN_RR_T1"])

    head = [
        f"🔎 <b>تحليل يدوي عند الطلب: {result['symbol']}</b>",
        f"الدرجة الفنية: <b>{result['score']}/100</b>  "
        f"(نقاط الإشارات الفنية فقط)",
        f"البوابات الإلزامية: <b>{passed}/{total}</b> ✅",
    ]
    if qualifies:
        head.append("الحكم: ✅ <b>يطابق كل شروط البوت</b> — كان سيُرشَّح في القائمة")
    else:
        why = "، ".join(failed) if failed else "عائد/مخاطرة أو الحد الأدنى للنقاط"
        head.append(f"الحكم: ❌ <b>لم يكن البوت ليرشّحه</b> (سبب الاستبعاد: {why})")
    head.append("")
    head.append("📋 <b>تفصيل البوابات السبع:</b>")
    for name, ok, detail in gates:
        head.append(f"  {'✅' if ok else '❌'} {name} — {detail}")
    head.append("")
    head.append("— — — البطاقة الكاملة — — —")

    card = bot.build_message([result], [], title="📊 <b>التفاصيل الفنية</b>")
    return "\n".join(head) + "\n" + card


# ==========================================================
# التشغيل
# ==========================================================
def main():
    sym = os.environ.get("ANALYZE", "").strip()
    if not sym:
        bot.log("⚠️ لم يُحدَّد رمز. ضع متغير البيئة ANALYZE=الرمز (مثل ANALYZE=VOR).")
        return
    bot.log(f"🔎 تحليل يدوي للسهم: {sym}")
    result, gates = analyze_on_demand(sym)
    if result is None:
        # عند الفشل: gates تحمل رسالة الخطأ النصية
        msg = f"🔎 <b>تحليل يدوي: {sym.upper()}</b>\n\n⚠️ {gates}\n\n{bot.FOOTER}"
        bot.send_telegram(msg)
        bot.log(f"تعذّر التحليل: {gates}")
        return
    # إثراء (SEC + شورت + أخبار + تأكيد 4 ساعات) — نفس دالة البوت
    try:
        bot.enrich([result])
    except Exception as e:
        bot.log(f"⚠️ الإثراء فشل (نُكمل بدونه): {e}")
    msg = render_ondemand(result, gates)
    bot.send_telegram(msg)
    bot.log("✅ أُرسل التحليل اليدوي.")


if __name__ == "__main__":
    main()
