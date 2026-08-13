# -*- coding: utf-8 -*-
"""
==========================================================
تحليل سهم واحد عند الطلب (Manual / On-Demand Analyzer) — v2 موحّد
==========================================================
ملف منفصل — لا يعدّل Super_stock.py ولا يلمس الفرز التلقائي.

v2: مُواءَم بالكامل مع البوت الأساسي الجديد:
  • يفحص كل بوابات الفرز الحالية بتقسيمها الصادق (صلبة ترفض · لينة نقص ·
    «معلومة» خرجت من الشروط بقياس الكاتالوج): الفجوة-فوق، RSI، MACD،
    المتوسط الأسي، الشورت، والفلوت — تماماً كقرار الترشيح، وأرقامها أرقام
    CONFIG الحيّة (معايير فيصل وحدها عند تفعيلها — لا أرقام قديمة مثبّتة).
  • يستخدم المتوسط الأسي (EMA) لا البسيط (SMA) في النقاط — مطابقة لفيصل.
  • نقاط الفجوات والفجوة-هدف مُضافة لتطابق درجة البوت بالضبط.
  • الأهداف من نفس منطق البوت (مقاومات حقيقية + فجوات-هدف).
  • أُضيف حقل entry المفقود (كان غيابه يوقف build_message بخطأ KeyError).
  • يعرض نسبة جاهزية الدخول (entry_readiness) إلى جانب الدرجة الفنية.

التشغيل: ANALYZE=BBLG  →  python analyze_one.py
"""
import os
import math
import numpy as np

# استيراد الملف الرئيسي (يدعم الاسم بحرف كبير في GitHub أو صغير محلياً)
try:
    import Super_stock as bot
except ImportError:
    import super_stock as bot

C = bot.CONFIG


def _n(x) -> str:
    """رقم عتبة للعرض: الصحيح كما هو، وغيره بعُشرية واحدة — حتى لا يكذب
    التقريبُ على الحكم (مسكة المالك 2026-08-08: «قاع 44» معروضًا مع ❌ والحد
    المعروض «44 أو أقل» — القيمة الحقيقية كانت 44.4 والتدوير أخفاها)."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return str(x)
    return f"{v:.0f}" if abs(v - round(v)) < 0.05 else f"{v:.1f}"


def _gate_kind(g) -> str:
    """نوع البوابة من الرباعية؛ الثلاثيات القديمة تُعامل «صلبة» (توافق خلفي)."""
    return g[3] if len(g) > 3 else "hard"


def truthful_drop(price, ref):
    """🧭 «الهبوط الصادق»: من **قمة ما بعد آخر تقسيم عكسي** لا القمة المعدَّلة.
    دالّة نقيّة — `None` عند غياب المرجع أو تلفه (فلا سطر، ولا تخمين)."""
    try:
        p, r = float(price), float(ref)
        if not (p > 0 and r > 0):
            return None
        return (1.0 - p / r) * 100.0
    except (TypeError, ValueError):
        return None


def drop_verdict(d, floor, cap):
    """حكم النطاق على قيمة هبوط: «تحت الأرضية» · «داخل النطاق» · «فوق السقف»."""
    try:
        d, floor, cap = float(d), float(floor), float(cap)
    except (TypeError, ValueError):
        return None
    if d < floor:
        return "تحت الأرضية"
    return "داخل النطاق" if d <= cap else "فوق السقف"


REJECT_CEILING_MARK = "فوق_97"          # اسمُ جدار السقف في عدّاد الرفض


def truthful_drop_lines(price, ref, floor=None, cap=None, reason=None) -> list:
    """🧭 أسطرُ «الهبوط الصادق» — **عرض/تشخيص فقط، لا يغيّر حكمًا**.

    سببُه (مسكة المالك 2026-08-08 «طيب هذي تعتبر مشكلة هل حليتها؟»): الفارز
    يقيس M2 على سلسلةٍ **معدَّلة بالتقسيمات**، فالمقسَّم عكسيًّا يُرفَض بسببٍ
    **مغلوطٍ في اسمه**: TDIC سُجِّل «هبوط فوق السقف 99.7%» وهبوطه الصادق من
    قمّته الحقيقية ‏$10.5 هو **‏74.8% = تحت الأرضية**. القرارُ صحيحٌ في الحالتين
    (رفضٌ ⟵ رفض) لكنّ **التفسير** كان كاذبًا — **وقد ضلّلني بنفسي** في أوّل
    تشخيصٍ قدّمتُه للمالك عن TDIC.
    ⚖️ **ولا يمسّ الحكم:** `T-M2REF`/`T-ENVREF` قاستا اعتماد المرجع الصادق في
    **القرار** وأُغلق الملفّ بقرار المالك — وهذا **صدقٌ في التفسير** لا أكثر.
    و`reason` (اختياريّ) يُنتج تنبيهًا صريحًا عند تعارض اسم الجدار مع الصدق."""
    d = truthful_drop(price, ref)
    if d is None:
        return []
    v = (drop_verdict(d, floor, cap)
         if (floor is not None and cap is not None) else None)
    L = [f"🧭 الهبوط الصادق (من قمة ما بعد آخر تقسيم عكسي ${float(ref):,.2f}): "
         f"<b>{d:.1f}%</b>" + (f" ⟶ {v}" if v else "")]
    if reason and REJECT_CEILING_MARK in str(reason) and v == "تحت الأرضية":
        L.append("⚠️ <b>اسم السبب المُسجَّل مضلِّل</b>: «الهبوط فوق السقف» مقيسٌ "
                 "على القمة المعدَّلة بالتقسيم — والسبب الحقيقي أنه <b>تحت "
                 "الأرضية</b> (لم يبلغ انهيار فيصل). الرفض صحيح، والاسم لا.")
    else:
        L.append("<i>الفارز يحسب M2 على السلسلة المعدَّلة بالتقسيمات — فهذا "
                 "السطر يصحّح فهم السبب لا الحكم.</i>")
    return L


def render_gate_lines(gates, truthful=None) -> list:
    """🚪 أسطر عرض البوابات بتقسيمها الصادق — **عرض فقط** (لا قرار).

    تصحيح مسكة المالك (2026-08-08 «13 بوابة هذي أصلًا من البوابات اللي حنا
    مسوينها مب اللي من فيصل»): كان العرض يسمّي الثلاث عشرة كلّها «البوابات
    الإلزامية» بينما الفارز الحقيقي يفرّق: **صلبة ترفض** (السعر/الهبوط/الانفجار/
    القاعدة/السيولة/RSI/الشورت/الفلوت — أرقامها من ظرف كتالوج فيصل، والشورت/
    الفلوت بقرار المالك) · **لينة نقص لا رفض** (نمط الشمعة/الفجوة-هدف/MACD/
    المتوسط — تُحسب ضمن حد النواقص) · **معلومة** (توافق الفريمات عند حدّ 0 —
    قياس الكاتالوج أخرجه من الشروط فلا يُعدّ ولا يُوسَم ✅/❌)."""
    hard = [g for g in gates if _gate_kind(g) == "hard"]
    soft = [g for g in gates if _gate_kind(g) == "soft"]
    info = [g for g in gates if _gate_kind(g) == "info"]
    L = []
    if hard:
        hp = sum(1 for g in hard if g[1])
        L.append(f"🚪 بوابات فيصل الصلبة (ترفض): <b>{hp}/{len(hard)}</b> — "
                 "أرقامها مقيسة من كتالوجه (ظرف P90) · الشورت/الفلوت بقرار "
                 "المالك · تظهر كاملة حتى لو سقط على واحدة:")
        for g in hard:
            L.append(f"  {'✅' if g[1] else '❌'} {g[0]} — {g[2]}")
    if soft:
        sp = sum(1 for g in soft if g[1])
        L.append(f"🔸 تأكيدات لينة (نقصها لا يرفض — يُحسب ضمن حد النواقص "
                 f"{int(C.get('WATCH_MAX_FAILS', 3))}): <b>{sp}/{len(soft)}</b>:")
        for g in soft:
            L.append(f"  {'✅' if g[1] else '❌'} {g[0]} — {g[2]}")
    for g in info:
        L.append(f"  ℹ️ {g[0]} — {g[2]}")
    # 🧭 «الهبوط الصادق» تحت البوابات الصلبة (مسكة المالك 2026-08-08) — يُمرَّر
    # من نقطة النداء التي تملك التقسيمات (فحص اليد)؛ غيابُه ⇒ صفر سطر (بت-بت).
    if truthful:
        L += truthful_drop_lines(truthful.get("price"), truthful.get("ref"),
                                 truthful.get("floor"), truthful.get("cap"),
                                 truthful.get("reason"))
    return L


# ==========================================================
# التحليل عند الطلب — يحسب كل بوابة كمعلومة (بلا رفض)
# ==========================================================
def analyze_on_demand(sym: str):
    """يرجع (result_dict, gates) عند النجاح، أو (None, رسالة) عند تعذّر البيانات.
    gates = قائمة (اسم، نجح؟، تفصيل، نوع) لكل بوابات الفرز الحالية في البوت —
    النوع: hard صلبة ترفض · soft لينة نقص · info خرجت بقياس الكاتالوج
    (الشورت والفلوت يُضافان لاحقاً في main بعد الإثراء)."""
    sym = sym.strip().upper()
    try:
        data = bot.download_history([sym])
    except Exception as e:
        return None, f"تعذّر الاتصال لجلب بيانات {sym}: {e}", None
    df = data.get(sym)
    if df is None or len(df) < C["MIN_BARS"]:
        return None, (f"تعذّر جلب بيانات كافية لـ {sym}. "
                      "غالباً: رمز خاطئ، سهم جديد جداً، أو سيولة شبه معدومة "
                      "(أقل من الحد الأدنى للشموع المطلوبة)."), None

    close = df["Close"]
    high, low, vol = df["High"], df["Low"], df["Volume"]
    c = close.values
    price = float(c[-1])

    # ---- المؤشرات تُحسب مرة واحدة وتُعاد في البوابات والنقاط (لا ازدواج) ----
    rsi_s = bot.rsi(close)
    r_now = float(rsi_s.iloc[-1])
    r_prev = float(rsi_s.iloc[-2])
    r_min_recent = float(rsi_s.tail(C["RSI_RECENT_WINDOW"]).min())
    m_line, m_sig = bot.macd(close)
    ema30 = bot.ema(close, 30)
    ema50 = bot.ema(close, 50)
    mtf = bot.multi_timeframe(df)
    patterns = mtf["patterns"]
    gaps = bot.gap_analysis(df)
    gaps_above = bot.all_unfilled_gaps_above(df)
    maxd = C["GAP_ABOVE_MAX_DIST_PCT"]
    near_zones = [z for z in gaps_above["all_zones"]
                  if (z["bottom"] / price - 1.0) * 100.0 <= maxd]
    best_spike, n_spikes = bot.spike_info(c, exclude_last=C["BASE_WINDOW"])

    # (الاسم، نجح؟، التفصيل، النوع) — النوع «مطابق للفارز الحقيقي»: hard ترفض ·
    # soft نقص يُحسب ضمن حد النواقص · info خرجت من الشروط بقياس الكاتالوج.
    # (مسكة المالك 2026-08-08: كانت الثلاث عشرة كلها تُعرض «إلزامية» — كذبة إطار.)
    gates = []

    # M1: السعر (صلبة) — العتبة بخانتين لا مدوّرة ($1.65 كانت تظهر «$2»)
    g1 = price >= C["MIN_PRICE"]
    gates.append((f"السعر فوق ${C['MIN_PRICE']:.2f}", g1, f"${price:.2f}", "hard"))

    # M2: الهبوط من قمة 52 أسبوع (صلبة عند الأرضية/السقف · «المثالي» نقص بالحكم)
    hi52 = float(high.tail(252).max())
    drop_pct = (1.0 - price / hi52) * 100.0 if hi52 > 0 else 0.0
    g2 = (drop_pct >= C["MIN_DROP_FLOOR"]) and (drop_pct <= C["MAX_DROP_PCT"])
    gates.append((f"الهبوط ضمن {_n(C['MIN_DROP_FLOOR'])}–{_n(C['MAX_DROP_PCT'])}%"
                  f" (المثالي {_n(C['MIN_DROP_PCT'])}% فأكثر)",
                  g2, f"{drop_pct:.1f}%", "hard"))

    # M3: الانفجار السابق (صلبة عند الأرضية · «المثالي» نقص بالحكم)
    g3 = best_spike >= C["PRIOR_SPIKE_FLOOR"]
    gates.append((f"انفجار سابق {_n(C['PRIOR_SPIKE_FLOOR'])}% فأكثر"
                  f" (المثالي {_n(C['PRIOR_SPIKE_PCT'])}%)",
                  g3, f"{best_spike:.1f}% ({n_spikes} انفجار موثّق)", "hard"))

    # M4: قاعدة ضيقة + لم ينفجر بعد (صلبة — حدّ الحركة معروض حتى يُقرأ الحكم)
    bw = C["BASE_WINDOW"]
    base_hi = float(high.tail(bw).max())
    base_lo = float(low.tail(bw).min())
    base_range = (base_hi / base_lo - 1.0) * 100.0 if base_lo > 0 else 9999.0
    gain5 = (c[-1] / c[-6] - 1.0) * 100.0 if len(c) > 6 else 0.0
    g4 = (base_range <= C["BASE_RANGE_MAX_PCT"]) and \
         (gain5 <= C["RECENT_RISE_BLOCK_PCT"])
    gates.append((f"قاعدة ضيقة ({_n(C['BASE_RANGE_MAX_PCT'])}% أو أقل) ولم ينفجر "
                  f"(حركة 5ج {_n(C['RECENT_RISE_BLOCK_PCT'])}% أو أقل)",
                  g4, f"مدى القاعدة {base_range:.1f}%، حركة 5 جلسات {gain5:+.1f}%",
                  "hard"))

    # M5: السيولة الدولارية (صلبة)
    dvol = float((close * vol).tail(20).mean())
    g5 = math.isfinite(dvol) and dvol >= C["MIN_DOLLAR_VOL"]
    gates.append((f"سيولة {bot.fmt_money(C['MIN_DOLLAR_VOL'])}/يوم أو أكثر",
                  g5, f"{bot.fmt_money(dvol)}/يوم", "hard"))

    # M6: توافق الفريمات — لينة بالفارز (نقص لا رفض)؛ وعند حدّ 0 (قياس الكاتالوج:
    # أسهم فيصل عند قيعانها 0/3) تخرج من الشروط ⇒ «معلومة» بلا ✅/❌ ولا عدّ —
    # كان سطر «0 من 3 على الأقل ✅» يتحقّق دائمًا فينفخ العدّاد بلا معنى.
    if C["TF_MIN_REVERSALS"] >= 1:
        g6 = mtf["count"] >= C["TF_MIN_REVERSALS"]
        gates.append((f"توافق الفريمات {int(C['TF_MIN_REVERSALS'])} من 3 على الأقل",
                      g6, f"{mtf['count']}/3 — {mtf['display']}", "soft"))
    else:
        gates.append(("توافق الفريمات — خرج من الشروط بقياس الكاتالوج", True,
                      f"الحال: {mtf['count']}/3 — {mtf['display']}", "info"))

    # M7: نمط شمعة انعكاسي (لينة — الفارز يسجّله نقصًا لا رفضًا)
    g7 = bool(patterns)
    gates.append(("نمط شمعة انعكاسي (يومي/أسبوعي)",
                  g7, "، ".join(patterns) if patterns else "لا يوجد", "soft"))

    # M9: فجوة-هدف غير مملوءة فوق السعر (لينة — الفارز يسجّلها نقصًا لا رفضًا)
    if C.get("GAP_ABOVE_REQUIRED", False):
        g9 = bool(near_zones)
        d9 = (f"{len(near_zones)} منطقة (أقرب ${near_zones[0]['bottom']:.2f})"
              if near_zones else "لا توجد فجوة-هدف فوق السعر")
        gates.append(("فجوة-هدف غير مملوءة فوق السعر", g9, d9, "soft"))

    # M10: RSI متدرّج (صلبة — سقفا الرفض بالفارز) · القيم بعُشرية حتى لا يناقض
    # العرضُ الحكمَ (قاع 44.4 كان يظهر «44» مع ❌ والحد «44 أو أقل»)
    if C.get("RSI_GATE_REQUIRED", False):
        r_min_os = float(rsi_s.tail(C["RSI_OS_LOOKBACK"]).min())
        g10 = (r_min_os <= C["RSI_OS_HARD"] and r_now <= C["RSI_NOW_HARD"])
        gates.append((f"RSI تشبّع (قاع {_n(C['RSI_OS_HARD'])} أو أقل) والآن "
                      f"{_n(C['RSI_NOW_HARD'])} أو أقل", g10,
                      f"قاع {r_min_os:.1f} / الآن {r_now:.1f}", "hard"))

    # M11: تقاطع MACD إيجابي (لينة — الفارز يسجّله نقصًا لا رفضًا)
    if C.get("MACD_GATE_REQUIRED", False):
        g11 = (float(m_line.iloc[-1]) >= float(m_sig.iloc[-1])
               or (m_line.iloc[-5:] > m_sig.iloc[-5:]).any())
        gates.append(("تقاطع MACD إيجابي", g11,
                      "إيجابي" if g11 else "سلبي/لا تقاطع", "soft"))

    # M12: السعر على المتوسط الأسي 30/50 (لينة — الفارز يسجّلها نقصًا لا رفضًا)
    if C.get("MA_GATE_REQUIRED", False):
        band = C["MA_GATE_MAX_ABOVE_PCT"] / 100.0
        g12 = any(m > 0 and price >= m * 0.98 and (price / m - 1.0) <= band
                  for m in (ema30, ema50))
        ma_dist = ((price / ema30 - 1.0) * 100.0) if ema30 > 0 else 0.0
        if ma_dist < 0:
            _rise = ((ema30 * 0.98 / price - 1.0) * 100.0) if price else 0.0
            _d12 = (f"السعر أقل بـ{abs(ma_dist):.0f}% من متوسطه المتحرك "
                    f"(يفتح بصعود ~{_rise:.0f}% أو بثبات أسابيع)")
        else:
            _d12 = (f"السعر أعلى بـ{ma_dist:.0f}% من متوسطه المتحرك "
                    "(يفتح برجوعه قرب متوسطه)")
        gates.append(("السعر قرب متوسطه المتحرك 30/50", g12, _d12, "soft"))

    # ===== الدرجة الفنية (نفس أوزان البوت — تُحسب دائماً) =====
    score = 0
    flags = []
    warnings = []

    if best_spike >= C["SPIKE_VERIFY_PCT"]:
        warnings.append(f"انفجار سابق ضخم ({best_spike:.0f}%) — "
                        "تحقق يدوياً من تقسيم عكسي")
    if dvol < C["LOW_LIQ_WARN"]:
        warnings.append(f"سيولة منخفضة ({bot.fmt_money(dvol)}/يوم)")

    if (r_min_recent <= C["RSI_OVERSOLD"] and r_now > r_prev
            and r_now <= C["RSI_MAX_NOW"]):
        score += 15
        flags.append(f"RSI تشبع وانحناء (قاع {r_min_recent:.0f}→{r_now:.0f})")

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

    # المتوسط الأسي (EMA) لا البسيط (SMA) — مطابقة للبوت الأساسي وفيصل
    near_ma = any(ma > 0 and abs(price / ma - 1.0) <= 0.05
                  for ma in (ema30, ema50))
    if near_ma:
        score += 10
        flags.append("يرتكز على متوسط 30/50")

    if n_spikes >= 2:
        score += 15
        flags.append(f"معيد إجرام ({n_spikes} انفجارات)")

    ps = bot.pivot_stability(low.values.astype(float), c)
    if ps and ps["held"]:
        score += 15
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

    # ===== مؤشرات فيصل الإضافية (v2.7) — مطابقة analyze_ticker بالحرف =====
    # (أي اختلاف هنا = فشل اختبار «تطابق الفحص اليدوي مع الأساسي» في test_bot)
    ind = {}
    try:
        ind["atr"] = float(bot.atr(high, low, close, C["ATR_PERIOD"]).iloc[-1])
    except Exception:
        ind["atr"] = 0.0
    try:
        mfi_now = float(mfi_s.iloc[-1])
        mfi_min = float(mfi_s.tail(10).min())
        ind["mfi"] = mfi_now
        if sweep and mfi_now > mfi_min and mfi_min <= C["MFI_OVERSOLD"]:
            score += C["MFI_DIVERGENCE_SCORE"]
            flags.append(f"تباعد MFI صعودي ({mfi_min:.0f}→{mfi_now:.0f}) — سيولة مخفية")
    except Exception:
        ind["mfi"] = 50.0
    try:
        _bm, _bu, _bl, _pctb, _bw = bot.bollinger(close)
        ind["boll_pctb"] = float(_pctb.iloc[-1])
        bw_tail = _bw.dropna().tail(60)
        if len(bw_tail) >= 20:
            thr = float(bw_tail.quantile(C["BOLL_SQUEEZE_PCTL"]))
            if float(_bw.iloc[-1]) <= thr:
                score += C["SCORE_BOLLINGER_SQUEEZE"]
                flags.append("انكماش حزمة كلنجر (تجميع)")
    except Exception:
        pass
    try:
        _sk, _sd = bot.stoch_rsi(close)
        ind["stochrsi_k"] = float(_sk.iloc[-1])
        if float(_sk.iloc[-2]) <= 20 and float(_sk.iloc[-1]) > float(_sk.iloc[-2]):
            score += C["SCORE_STOCHRSI"]
            flags.append("StochRSI انعطاف من التشبع")
    except Exception:
        pass
    try:
        _wlr = bot.williams_r(high, low, close)
        ind["williams_r"] = float(_wlr.iloc[-1])
        if (float(_wlr.iloc[-2]) <= C["WILLIAMS_OVERSOLD"]
                and float(_wlr.iloc[-1]) > float(_wlr.iloc[-2])):
            score += C["SCORE_WILLIAMS"]
            flags.append("Williams %R انعطاف من التشبع")
    except Exception:
        pass
    try:
        _pdi, _mdi, _adx = bot.dmi_adx(high, low, close)
        ind["plus_di"] = float(_pdi.iloc[-1])
        ind["minus_di"] = float(_mdi.iloc[-1])
        ind["adx"] = float(_adx.iloc[-1])
        if float(_pdi.iloc[-1]) > float(_mdi.iloc[-1]):
            score += C["SCORE_DMI"]
            flags.append("DMI: ‎+DI فوق ‎-DI")
    except Exception:
        pass
    try:
        ma5 = float(close.rolling(5).mean().iloc[-1])
        ma20 = float(close.rolling(20).mean().iloc[-1])
        ind["ma5"], ind["ma20"] = ma5, ma20
        if ma5 > 0 and price >= ma5 and ma5 >= ma20 * 0.99:
            score += C["SCORE_MA_SHORT"]
            flags.append("استعاد MA5/MA20 (تجميع)")
    except Exception:
        pass
    try:
        ind["vwap"] = bot.rolling_vwap(df)
        _ddd, _ama = bot.dma_oscillator(close)
        ind["dma_ddd"] = float(_ddd.iloc[-1])
        ind["dma_ama"] = float(_ama.iloc[-1])
    except Exception:
        pass

    # نقاط الفجوات الصاعدة (مطابقة للبوت)
    if gaps["count"] > 0:
        if gaps["max_gap"] >= C["GAP_BIG_PCT"]:
            score += C["GAP_SCORE_BIG"]
            flags.append(f"فجوة عالية يومي {gaps['max_gap']:.0f}%")
        else:
            score += C["GAP_SCORE_NORMAL"]
            flags.append(f"فجوة صاعدة يومي {gaps['max_gap']:.0f}%")
        if gaps.get("frames_with_gaps", 1) >= 2:
            score += C["GAP_SCORE_MULTIFRAME"]
            flags.append("فجوات متعددة الفريمات")

    # نقاط الفجوة-هدف فوق السعر (مطابقة للبوت)
    if near_zones:
        score += C["GAP_ABOVE_SCORE"]
        nz = near_zones[0]
        dist = round((nz["bottom"] / price - 1.0) * 100.0, 1)
        flags.append(f"فجوة-هدف فوق السعر عند ${nz['bottom']:.2f} (+{dist:.0f}%)")

    score = int(min(score, 100))

    # ===== نسبة جاهزية الدخول (نفس دالة البوت بالضبط) =====
    try:
        readiness_pct, readiness_comp = bot.entry_readiness(df)
    except Exception:
        readiness_pct, readiness_comp = None, {}
    # «جاهز» مشتقّة حصريًا من النسبة (مطابق للبوت — مصدر واحد، لا تناقض)
    ready = (readiness_pct is not None and readiness_pct >= C["READY_PCT"])
    have = [k for k, (p, m) in readiness_comp.items() if p >= m]
    partial = [k for k, (p, m) in readiness_comp.items() if 0 < p < m]
    missing = [k for k, (p, m) in readiness_comp.items() if p == 0]

    # ===== المستويات (مطابقة للبوت الأساسي بالحرف) =====
    pivot = ps["pivot"] if ps else float(low.tail(20).min())
    s_lo, s_hi = C["STOP_BELOW_LOW_PCT"]
    stop_hi = pivot * (1 - s_lo / 100.0)
    stop_lo = pivot * (1 - s_hi / 100.0)
    # وقف ATR أُلغي عمدًا (USE_ATR_STOP=False) — منهجية فيصل: 5-7% تحت القاع فقط
    # (مطابق للبوت بعد إزالة فرع ATR الميت).
    big = price >= C["LARGE_PRICE_CUT"]
    d_lo, d_hi = (C["SWEEP_LARGE_PCT"] if big else C["SWEEP_SMALL_PCT"])
    sweep_lo = pivot * (1 - d_hi / 100.0)
    sweep_hi = pivot * (1 - d_lo / 100.0)

    # دفعات الدخول (أسلوب فيصل): أوامر عند الدعم وصعوداً بخطوة ثابتة
    n_tr = max(1, int(C["ENTRY_TRANCHES"]))
    step = C["ENTRY_STEP_PCT"] / 100.0
    tranches = [round(pivot * (1 + step * i), 2) for i in range(n_tr)]
    entry_lo = tranches[0]
    entry_hi = tranches[-1]
    # الضمان الذهبي: الوقف دائمًا تحت أدنى الدخول
    entry_floor = min(entry_lo, entry_hi)
    if stop_hi >= entry_floor:
        stop_hi = round(entry_floor * (1 - s_lo / 100.0), 2)
    if stop_lo >= stop_hi:
        stop_lo = round(entry_floor * (1 - s_hi / 100.0), 2)

    # الأهداف (مقاومات حقيقية + فجوات-هدف — نفس منطق البوت، لا SMA عشوائي)
    resist = bot.resistance_levels(df, price)
    raw_t1 = bot.first_target(df)
    raw_t3 = float(high.tail(60).max())
    cap = price * C["TARGET_CAP_MULT"]
    min_first = price * (1.0 + C["MIN_T1_GAIN_PCT"] / 100.0)
    gapm = 1.0 + C["MIN_TARGET_GAP_PCT"] / 100.0
    target_cands = list(resist) + [raw_t1, raw_t3]
    # أهداف الفريم الأسبوعي (مطابقة analyze_ticker — فيصل: يومي + أسبوعي)
    if C.get("USE_MULTIFRAME_TARGETS", True):
        try:
            wk = bot.resample_ohlc(df, "W")
            if wk is not None and len(wk) >= 10:
                target_cands += list(bot.resistance_levels(
                    wk, price, include_red_heads=False))
                target_cands.append(bot.first_target(wk))
        except Exception:
            pass
    if C.get("GAP_ABOVE_USE_AS_TARGET", False):
        for z in near_zones:
            target_cands.append(z["bottom"])
    # Fibonacci كأهداف (مطابقة analyze_ticker — فيصل IMG_6473)
    if C.get("USE_FIB_TARGETS", False):
        try:
            fib = bot.fibonacci_levels(pivot, raw_t3)
            for key in ("0.382", "0.500", "0.618", "0.786", "1.000"):
                if fib.get(key):
                    target_cands.append(fib[key])
        except Exception:
            pass
    cands = sorted(t for t in target_cands if min_first <= t <= cap)
    targets = []
    for t in cands:
        if not targets or t >= targets[-1] * gapm:
            targets.append(round(float(t), 2))
    if not targets:
        above = sorted(t for t in (list(resist) + [raw_t3]) if t > price)
        targets = [round(above[0], 2)] if above else [round(price * 1.25, 2)]
    while len(targets) < 3:
        nxt = next((t for t in cands if t > targets[-1] * gapm), None)
        targets.append(round(nxt, 2) if nxt else round(targets[-1] * 1.25, 2))
    t1, t2, t3 = targets[0], targets[1], targets[2]

    # ===== ألوان فيصل: t2=أقرب كبير · t3=القمة الزرقاء · وسم لون كل هدف =====
    # مطابقة analyze_ticker بالحرف (⚫ مقاومة · 🔵 هدف بلا مقاومة). t1 محفوظ · التحرر لا يُمسّ.
    targets_kind = None
    try:
        cycle_peak = float(hi52)
        # 🛡️ حارس phantom التقسيم (مطابقة analyze_ticker): hi52 المتضخّم بتعديل تقسيم رجعي
        _rtop = max([x for x in resist if x > price], default=0.0)
        if _rtop > 0 and cycle_peak > _rtop * 2.0:
            cycle_peak = _rtop * (1.0 + C["TARGET_BLUE_EXTEND_PCT"] / 100.0)
        _mg = 1.0 + C["TARGET_MAJOR_GAP_PCT"] / 100.0
        _major_cap = max(
            cycle_peak * (1.0 + C["TARGET_ANCHOR_HEADROOM_PCT"] / 100.0),
            price * C["TARGET_CAP_MULT"])
        _blk = set(round(float(x), 2) for x in resist)
        _blk.add(round(float(raw_t1), 2))
        _blue = {round(float(cycle_peak), 2)}    # 🔵 القمة = هدف بلا مقاومة
        _cand = list(resist) + [raw_t1, cycle_peak]
        if C.get("USE_MULTIFRAME_TARGETS", True):
            try:
                _wkm = bot.resample_ohlc(df, "W")
                if _wkm is not None and len(_wkm) >= 10:
                    _wr = list(bot.resistance_levels(
                        _wkm, price, include_red_heads=False))
                    _wf = bot.first_target(_wkm)
                    _cand += _wr + [_wf]
                    for _x in _wr + [_wf]:
                        _blk.add(round(float(_x), 2))
            except Exception:
                pass
        if C.get("GAP_ABOVE_USE_AS_TARGET", False):
            for z in near_zones:
                _cand.append(z["bottom"])
                _blue.add(round(float(z["bottom"]), 2))
        if C.get("USE_FIB_TARGETS", False):
            try:
                _fibf = bot.fibonacci_levels(pivot, cycle_peak)
                for _k in ("0.382", "0.500", "0.618", "0.786", "1.000"):
                    if _fibf.get(_k):
                        _cand.append(_fibf[_k])
                        _blue.add(round(float(_fibf[_k]), 2))
            except Exception:
                pass
        _majors = sorted(set(round(float(t), 2)
                             for t in _cand if t1 < t <= _major_cap))
        if _majors:
            _t2 = next((t for t in _majors if t >= t1 * _mg), _majors[0])
            _t3 = _majors[-1]
            if _t3 <= _t2 * _mg:
                _t3 = next((t for t in _majors if t >= _t2 * _mg),
                           round(_t2 * _mg, 2))
            t2, t3 = round(_t2, 2), round(_t3, 2)

        def _tkind(v):
            if any(_b > 0 and abs(v / _b - 1.0) <= 0.015 for _b in _blue):
                return "🔵"
            return ("⚫" if any(_b > 0 and abs(v / _b - 1.0) <= 0.015
                                for _b in _blk) else "🔵")
        targets_kind = [_tkind(t1), _tkind(t2), _tkind(t3)]
    except Exception:
        targets_kind = None

    entry_ref = round(sum(tranches) / len(tranches), 4)  # متوسط الدفعات (فيصل يمتّع)
    risk = max(entry_ref - stop_lo, 1e-9)
    rr = (t1 - entry_ref) / risk
    rr2 = (t2 - entry_ref) / risk
    # 🎯 صدقُ RR — **مرآةُ `analyze_ticker` حرفيًّا** (أ-1، 2026-08-13): فوق نطاق
    #    الدفعات يُقاس العائدُ من السعر الحالي. **إلزاميّةٌ لا اختيارية**: بدونها
    #    ينكسر قفلُ «الفحص اليدوي = الأساسي (RR بالضبط)». داخل النطاق ⇒ بت-بت.
    _band_top = max(tranches) * (1 + C.get("ENTRY_READY_BAND_TOL_PCT", 0.0) / 100.0)
    if price > _band_top:
        _risk_now = max(price - stop_lo, 1e-9)
        rr = (t1 - price) / _risk_now
        rr2 = (t2 - price) / _risk_now
    if rr < C["MIN_RR_T1"]:
        warnings.append(f"العائد مقابل المخاطرة منخفض ({rr:.1f}× — "
                        f"المطلوب {C['MIN_RR_T1']:.1f}× على الأقل)")

    # مستويات الـ4 ساعات (منظومة فيصل) — طبقة مساندة، لا تمسّ الخطة اليومية
    try:
        _h4 = bot.fetch_4h(sym)
        h4_levels = bot.four_hour_levels(_h4, price) if _h4 is not None else None
    except Exception:
        h4_levels = None
    # دمج فيصل #1: تنقيح t2/t3 بأهداف الـ4س (t1/RR مقفولان) — مطابقة لِما يُنقّح
    # في enrich بالمسار الأساسي، فالفحص اليدوي = ما يراه المستخدم بالكرت بالضبط.
    if h4_levels:
        t2, t3 = bot.refine_targets_4h(t1, t2, t3, price, h4_levels)
        rr2 = (t2 - entry_ref) / risk

    # نتيجة كاملة بكل المفاتيح التي يحتاجها build_message + الإثراء
    result = {
        "symbol": sym, "price": price, "score": score,
        "drop_pct": drop_pct, "best_spike": best_spike,
        "n_spikes": n_spikes, "base_range": base_range,
        "rsi": r_now, "dollar_vol": dvol,
        "pivot": pivot, "stop": (stop_lo, stop_hi),
        "entry": (entry_lo, entry_hi), "tranches": tranches,
        "h4_levels": h4_levels,
        "key_levels": bot.key_levels(df, price, pivot),  # بلا 4س — مطابق للبوت
        "indicators": ind,                 # MFI/ADX/كلنجر%B/%R — يطابق البطاقة
        "sweep": (sweep_lo, sweep_hi),
        "t1": t1, "t2": t2, "t3": t3, "rr": rr, "rr2": rr2,
        "targets_kind": targets_kind,          # 🎨 لون كل هدف (فيصل)
        "ready": ready, "flags": flags, "warnings": warnings,
        "tf_count": mtf["count"], "tf_display": mtf["display"],
        "patterns": patterns,
        "gaps": gaps, "gaps_above": gaps_above,
        "readiness": readiness_pct,
        "readiness_have": have, "readiness_partial": partial,
        "readiness_missing": missing,
        # مفاتيح اختيارية يملؤها الإثراء — نهيّئها لتفادي أي خطأ
        "short_pct": None, "float": None, "recent_split": None,
        "news": [], "tf4h": "غير متوفر",
        "sec_status": None, "sec_filings": [],
    }
    return result, gates, df


def append_short_float_gates(result: dict, gates: list) -> list:
    """يضيف بوابتي الشورت (M13) والفلوت (M14) بعد الإثراء — لأنهما يحتاجان
    بيانات شبكية يجلبها enrich. نفس منطق البوت: يعدّي لو البيانة مفقودة."""
    gates = list(gates)
    # M13 — الشورت العالي (صلبة · الرقم قرار المالك C3 — خارج قياس الكاتالوج)
    if C.get("SHORT_GATE_REQUIRED", False):
        fd = result.get("fintel") or {}
        srt = fd.get("short_volume")
        if srt is None:
            srt = result.get("finra_short")
        g13 = (srt is None) or (srt < C["SHORT_GATE_MAX"])
        d13 = (f"{bot.fmt_money(srt)} (الحد {bot.fmt_money(C['SHORT_GATE_MAX'])})"
               if srt is not None else "غير متاح — مُرِّر بفائدة الشك")
        gates.append((f"الشورت تحت {bot.fmt_money(C['SHORT_GATE_MAX'])}",
                      g13, d13, "hard"))
    # M14 — الفلوت الكبير (صلبة · الرقم قرار المالك 2026-07-29 — خارج الكاتالوج)
    if C.get("FLOAT_GATE_REQUIRED", False):
        fl = result.get("float")
        g14 = (fl is None) or (fl < C["FLOAT_GATE_MAX"])
        d14 = (f"{bot.fmt_money(fl)} (الحد {bot.fmt_money(C['FLOAT_GATE_MAX'])})"
               if fl is not None else "غير متاح — مُرِّر بفائدة الشك")
        gates.append((f"الفلوت تحت {bot.fmt_money(C['FLOAT_GATE_MAX'])}",
                      g14, d14, "hard"))
    return gates


# ==========================================================
# بناء الرسالة: ترويسة البوابات + النسبة + البطاقة الكاملة
# ==========================================================
def render_ondemand(result: dict, gates: list, official, reject_reason=None,
                    pullback=None) -> str:
    # ترويسة العدّ على **الصلبة وحدها** — عدّ الثلاث عشرة كلها كان يعرض
    # التأكيدات اللينة والميّت (توافق=0) كأنها شروط رفض (مسكة المالك 2026-08-08)
    _hard = [g for g in gates if _gate_kind(g) == "hard"]
    _hp = sum(1 for g in _hard if g[1])

    head = [
        f"🔎 <b>تحليل يدوي عند الطلب: {result['symbol']}</b>",
        f"نسبة جاهزية الدخول: "
        f"{bot.readiness_badge(result.get('readiness'))}  "
        "(متى أدخل — التوقيت)",
        f"الدرجة الفنية: <b>{result['score']}/100</b>  "
        "(قوة الإشارات الفنية)",
        f"بوابات فيصل الصلبة: <b>{_hp}/{len(_hard)}</b>",
    ]
    # الحكم = قرار البوت الأساسي نفسه (مؤهّل / ارتداد / مرفوض) — لا تناقض
    # (🪦 A/B متقاعد 2026-07-05: فئة واحدة مؤهّلة، الجاهزية هي المحور)
    if official is not None:
        sf = official.get("soft_fails", [])
        tail = (f" (بوابات التأكيد الناقصة: {'، '.join(sf)})" if sf
                else " (اجتاز كل بوابات التأكيد)")
        head.append(f"الحكم: 🎯 <b>مؤهّل — كان سيدخل قائمة المراقبة</b>{tail}")
    elif pullback is not None:
        tgt = pullback["entry"][1]
        wr = "، ".join(pullback.get("watch_reasons", [])) or "ارتفع عن دخوله"
        head.append(f"الحكم: 👁️ <b>مراقبة ارتداد</b> — سهم ارتكاز حقيقي لكنه "
                    f"ارتفع ({wr}). انتظر رجوعه لسعر الدعم "
                    f"<b>${tgt:.2f}</b> ثم ادخل.")
    else:
        # سبب الرفض الاحتياطي من **الصلبة الساقطة وحدها** — ناقص لين ليس سبب رفض
        why = reject_reason or "؛ ".join(
            g[0] for g in gates if not g[1] and _gate_kind(g) == "hard") \
            or "لم يجتز بوابة صلبة"
        head.append(f"الحكم: ❌ <b>لم يكن البوت ليرشّحه</b> (السبب: {why})")
    head.append("")
    # تفصيل نسبة الجاهزية (المتوفر/الجزئي/الناقص)
    if result.get("readiness") is not None:
        if result.get("readiness_have"):
            head.append("✅ متوفر: " + "، ".join(result["readiness_have"]))
        if result.get("readiness_partial"):
            head.append("🔸 جزئي: " + "، ".join(result["readiness_partial"]))
        if result.get("readiness_missing"):
            head.append("⏳ ناقص: " + "، ".join(result["readiness_missing"]))
        head.append("")
    head.append("📋 <b>تفصيل البوابات:</b>")
    head += render_gate_lines(gates)
    head.append("")
    head.append("— — — البطاقة الكاملة — — —")

    result["interp"] = bot.build_interpretation(result)   # 🧭 التفسير/القرار (مطابقة الفرز)
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
    result, gates, df = analyze_on_demand(sym)
    if result is None:
        # عند الفشل: gates تحمل رسالة الخطأ النصية
        msg = f"🔎 <b>تحليل يدوي: {sym.upper()}</b>\n\n⚠️ {gates}\n\n{bot.FOOTER}"
        bot.send_telegram(msg)
        bot.log(f"تعذّر التحليل: {gates}")
        return

    # ===== القرار الرسمي من البوت الأساسي (يضمن التطابق التام للأبد) =====
    # نفس analyze_ticker الذي يستخدمه الفرز: دخول ضيّق + وقف مضمون + جاهزية
    # موحّدة + قاب + تحرّر + مؤشرات. لو رُفض، نلتقط السبب من عدّاد الرفض.
    bot._REJECT_STATS.clear()
    official = None
    try:
        official = bot.analyze_ticker(sym, df)
    except Exception as e:
        bot.log(f"⚠️ analyze_ticker: {e}")
    reject_reason = None
    if official is None and getattr(bot, "_REJECT_STATS", None):
        reject_reason = " · ".join(f"{k}={v}"
                                   for k, v in bot._REJECT_STATS.items())

    # لو رُفض عاديًا: نجرّب «مراقبة الارتداد» (ارتكاز حقيقي ارتفع فوق دخوله)
    pull = None
    if official is None:
        try:
            pull = bot.analyze_ticker(sym, df, pullback=True)
        except Exception as e:
            bot.log(f"⚠️ تحليل الارتداد: {e}")

    # البطاقة: الرسمية إن اجتاز، وإلا الارتداد إن وُجد، وإلا التشخيصية
    card_result = official or pull or result
    # ⚠️ **إصلاح 2026-07-28:** تفصيل الجاهزية (متوفر/جزئي/ناقص) يُكتَب على سجلّ
    # **التشخيص** (`result`) وحده، والبطاقة تُبنى من `official` عند التأهّل ⇒ كتلة
    # «تفصيل نسبة الجاهزية» في `render_ondemand` **ميتة تمامًا للسهم المؤهّل** (وهو
    # الحالة التي يهمّ فيها «لماذا الجاهزية 60/100؟»). نحملها للبطاقة بلا دهس.
    for _k in ("readiness_have", "readiness_partial", "readiness_missing"):
        if result.get(_k) is not None:
            card_result.setdefault(_k, result[_k])
    if official is None and pull is None:
        card_result["tier"] = "B"   # عرض فقط — الحكم بالأعلى يوضّح الرفض

    # 🧬 بصمة طريقة الارتفاع + جلسات القاع (تطابق scan_market — عرض/تفسير فقط):
    # كانتا ناقصتين بالفحص اليدوي فيغيب سطر 🧬 وسياق الدورة عن بطاقته (إصلاح 2026-07-07)
    try:
        card_result["behav"] = bot.behavior_rise_profile(df)
        card_result["pump_scar"] = bot.group_pump_scar(df)   # 🕵️ N1 (تطابق الفرز)
        card_result["trendline"] = bot.descending_trendline(
            df, card_result.get("price") or 0)          # §10 (تطابق الفرز)
        if card_result.get("bars_after") is None:
            _ps = bot.pivot_stability(df["Low"].values.astype(float),
                                      df["Close"].values.astype(float))
            card_result["bars_after"] = int(_ps["bars_after"]) if _ps else None
    except Exception:
        pass

    # إثراء (SEC + شورت + فلوت + أخبار + قطاع/دولة) — نفس دالة البوت
    try:
        bot.enrich([card_result])
    except Exception as e:
        bot.log(f"⚠️ الإثراء فشل (نُكمل بدونه): {e}")

    # تثبيت تصنيف A/B بعد الشورت/الفلوت (مطابق لـ scan_market تمامًا)
    if official is not None:
        sf = list(official.get("soft_fails", []))
        srt = ((official.get("fintel") or {}).get("short_volume")
               or official.get("finra_short"))
        if srt is not None and srt >= C["SHORT_GATE_MAX"]:
            sf.append("شورت عالٍ")
        fl = official.get("float")
        if fl is not None and fl >= C["FLOAT_GATE_MAX"]:
            sf.append("فلوت كبير")
        official["soft_fails"] = sf
        official["tier"] = bot.classify_tier(sf)
        if official["tier"] is None:        # تجاوز حد النواقص بعد الشورت/الفلوت
            reject_reason = (f"نواقص أكثر من الحد ({len(sf)}): "
                             + "، ".join(sf))
            official = None                 # يُعرض كمرفوض

    gates = append_short_float_gates(card_result, gates)
    msg = render_ondemand(card_result, gates, official, reject_reason, pull)
    bot.send_telegram(msg)
    bot.log("✅ أُرسل التحليل اليدوي.")


if __name__ == "__main__":
    main()
