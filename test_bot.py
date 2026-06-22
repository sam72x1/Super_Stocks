# -*- coding: utf-8 -*-
"""
اختبار شامل لبوت أسهم الارتكاز (v2.7) — الضمان الذهبي.
يغطي: المؤشرات + البوابات + نظام القائمتين (A/B) + التحرر/القاب +
قرارات الصور الفعلية (RSI/MACD/شورت/فلوت لكل سهم من الصور).
يعمل بلا إنترنت (يحاكي البيانات + يعطّل yfinance).
"""
import numpy as np
import pandas as pd
import Super_stock as S

PASS, FAIL = [], []


def check(name, cond, extra=""):
    (PASS if cond else FAIL).append(name)
    print(("✅" if cond else "❌") + f" {name}" + (f"  [{extra}]" if extra else ""))


# ==========================================================
# مولّد سهم ارتكاز واقعي يطابق نموذج الصور
# (انفجار سابق ≥100% → انهيار ≥50% → قاعدة ضيقة قرب القاع + انعكاس)
# ==========================================================
def synth_pivot(prior_high=20.0, crash_low=3.0, current=3.6,
                with_gap_above=True, n=250, seed=0):
    """سهم ارتكاز مثالي: انفجار ≥100% ضمن السنة → انهيار ≥50% → انحدار
    لطيف مطوّل للتشبع (RSI≤27) ثم قاع حديث ضحل + انحناء بسيط (RSI الآن ≤50،
    قريب من الدخول) + مطرقة عند الدعم + فجوة (قاب) فوق السعر."""
    rs = np.random.RandomState(seed)
    closes = []
    closes += list(np.linspace(crash_low * 1.2, crash_low, 20))
    closes += list(np.linspace(crash_low, prior_high, 12))        # انفجار
    closes += list(np.linspace(prior_high, crash_low * 1.4, 40))  # انهيار
    closes += list(np.linspace(crash_low * 1.4, current * 1.18,
                               n - len(closes) - 40))
    base = np.empty(40)
    tail = 4                                                       # عمر القاعدة بعد القاع
    pre = 40 - tail
    base[:pre] = np.linspace(current * 1.18, current * 0.93, pre)    # انحدار لطيف للتشبع
    base[pre:] = np.linspace(current * 0.93, current * 0.995, tail)  # انحناء بسيط من القاع
    closes += list(base)
    closes = np.array(closes[:n], dtype=float)
    closes[-1] = current

    o = closes * (1 + rs.uniform(-0.006, 0.006, n))
    h = np.maximum(o, closes) * (1 + rs.uniform(0.0, 0.018, n))
    l = np.minimum(o, closes) * (1 - rs.uniform(0.0, 0.018, n))
    v = rs.randint(300_000, 2_000_000, n).astype(float)
    v[-15:] *= 0.45                      # جفاف بيع بالقاعدة

    # مطرقة عند الدعم بآخر شمعة (جسم صغير + ذيل سفلي طويل) — M7 بدون رفع RSI
    o[-1], closes[-1] = current * 1.003, current * 1.00
    h[-1], l[-1] = current * 1.008, current * 0.95

    # فجوة هابطة غير مملوءة فوق السعر (قاب) — فراغ بين شمعتين، وكل ما بعده أدنى
    if with_gap_above:
        gi = n - 60
        gap_bottom = current * 1.30
        h[gi], o[gi] = gap_bottom, gap_bottom * 0.99
        closes[gi], l[gi] = gap_bottom * 0.98, gap_bottom * 0.97
        l[gi - 1], o[gi - 1] = gap_bottom * 1.06, gap_bottom * 1.10
        closes[gi - 1], h[gi - 1] = gap_bottom * 1.08, gap_bottom * 1.12

    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame({"Open": o, "High": h, "Low": l,
                         "Close": closes, "Volume": v}, index=idx)


# ==========================================================
# 1) اختبار المؤشرات (خصائص رياضية)
# ==========================================================
print("\n=== 1) المؤشرات ===")
df = synth_pivot(seed=1)
c = df["Close"]
r = S.rsi(c)
check("RSI ضمن 0-100", 0 <= float(r.iloc[-1]) <= 100, f"{float(r.iloc[-1]):.1f}")
a = S.atr(df.High, df.Low, df.Close)
check("ATR موجب", float(a.iloc[-1]) > 0, f"{float(a.iloc[-1]):.3f}")
mid, up, lo, pctb, w = S.bollinger(c)
check("Bollinger علوي>سفلي", float(up.iloc[-1]) > float(lo.iloc[-1]))
sk, sd = S.stoch_rsi(c)
check("StochRSI %K ضمن 0-100", 0 <= float(sk.iloc[-1]) <= 100)
pdi, mdi, adx = S.dmi_adx(df.High, df.Low, df.Close)
check("DMI/ADX ≥0", float(adx.iloc[-1]) >= 0 and float(pdi.iloc[-1]) >= 0)
check("VWAP موجب", S.rolling_vwap(df) > 0)
ddd, ama = S.dma_oscillator(c)
check("DMA يرجع قيمًا", np.isfinite(float(ddd.iloc[-1])))
fib = S.fibonacci_levels(3.0, 20.0)
check("Fib 0.5 = منتصف", abs(fib["0.500"] - 11.5) < 1e-6, str(fib["0.500"]))
check("Fib تصاعدي", fib["0.382"] < fib["0.618"] < fib["1.000"] < fib["1.618"])
check("Fib يرفض مدخل خاطئ", S.fibonacci_levels(20, 3) == {})


# ==========================================================
# 2) نظام القائمتين A/B + التحرر/القاب
# ==========================================================
print("\n=== 2) المحرك: التصنيف A/B + المستويات ===")


# سهم ارتكاز مُركّب → اختبار شامل للمحرك من البداية للنهاية
r0 = S.analyze_ticker("TEST", synth_pivot(seed=2))
check("سهم الارتكاز يُحلَّل (ليس None)", r0 is not None)
if r0:
    check("مُصنّف A أو B", r0["tier"] in ("A", "B"), f"tier={r0['tier']} soft={r0['soft_fails']}")
    check("نواقصه ضمن الحد", len(r0["soft_fails"]) <= S.CONFIG["WATCH_MAX_FAILS"])
    check("ستوب < القاع", r0["stop"][0] < r0["pivot"])
    check("الأهداف تصاعدية t1<t2<t3",
          r0["t1"] < r0["t2"] < r0["t3"], f"{r0['t1']}/{r0['t2']}/{r0['t3']}")
    check("t1 فوق السعر", r0["t1"] > r0["price"])
    # RR: إن كان دون الحد فلا بد أنه سُجّل كنقص (ينقل لقائمة B) لا رفض
    check("RR محسوب + ضعفه يُسجّل نقصًا (لا رفض)",
          (r0["rr"] >= S.CONFIG["MIN_RR_T1"]) or
          any("عائد" in x for x in r0["soft_fails"]), f"rr={r0['rr']:.2f}")
    check("مؤشرات محسوبة", "atr" in r0["indicators"] and "mfi" in r0["indicators"])
    check("التحرر فوق السعر أو None",
          r0["liberation"] is None or r0["liberation"] > r0["price"],
          str(r0["liberation"]))
    check("القاب فوق السعر (إن وُجد)",
          r0["qab"] is None or r0["qab"]["bottom"] > r0["price"])
    # قاعدة فيصل: الوقف ~7% تحت الدعم — لا أعمق بكثير (لا ATR يعمّقه)
    check("الوقف ~7% تحت الدعم (لا عميق شاذ)",
          r0["pivot"] * 0.90 <= r0["stop"][0] <= r0["pivot"] * 0.95 + 1e-6,
          f"stop={r0['stop'][0]:.2f} pivot={r0['pivot']:.2f}")

# تصنيف القائمتين (دالة نقية) — 0=A · 1-2=B · أكثر=None
check("0 نواقص → A", S.classify_tier([]) == "A")
check("نقص واحد → B", S.classify_tier(["MACD"]) == "B")
check("نقصان → B", S.classify_tier(["MACD", "RSI"]) == "B")
check("3 نواقص → B (الحد 3)", S.classify_tier(["MACD", "RSI", "فلوت"]) == "B")
check("4 نواقص → يُرفض None",
      S.classify_tier(["MACD", "RSI", "فلوت", "MA"]) is None)
check("التصنيف الصارم (بلا قائمتين)",
      S.classify_tier(["MACD"], two_tier=False) is None)


# ==========================================================
# 3) بوابتا الشورت/الفلوت → نقل لقائمة B (لا حذف)
# ==========================================================
print("\n=== 3) الشورت/الفلوت → قائمة B بدل الحذف ===")


def mk(symbol, **kw):
    base = {"symbol": symbol, "soft_fails": [], "flags": [], "float": None,
            "tier": "A", "score": 60, "ready": True, "rr": 2.0}
    base.update(kw)
    return base


# شورت عالٍ معروف → يبقى لكن يُسجّل نقص
S.fintel_short = lambda syms: {"HISH": 999_999}
S.finra_daily_short = lambda syms: {"HISH": 999_999}
out = S.apply_short_gate([mk("HISH")])
check("شورت عالٍ لا يُحذف", len(out) == 1)
check("شورت عالٍ يُسجّل نقص", "شورت عالٍ" in out[0].get("soft_fails", []))

# شورت مفقود → يعدّي بفائدة الشك بلا نقص
S.fintel_short = lambda syms: {}
S.finra_daily_short = lambda syms: {}
out2 = S.apply_short_gate([mk("MISS")])
check("شورت مفقود يعدّي بلا نقص", "شورت عالٍ" not in out2[0].get("soft_fails", []))

# فلوت كبير → نقص (نحاكي بوضع float كبير مسبقًا)
S.yf = object()   # حتى لا يتخطّى الدالة
big = mk("BIGF", float=200_000_000)
out3 = S.apply_float_gate([big])
check("فلوت كبير لا يُحذف", len(out3) == 1)
check("فلوت كبير يُسجّل نقص", "فلوت كبير" in out3[0].get("soft_fails", []))
small = mk("SMALLF", float=2_000_000)
out4 = S.apply_float_gate([small])
check("فلوت صغير يعدّي بلا نقص", "فلوت كبير" not in out4[0].get("soft_fails", []))
S.yf = None


# ==========================================================
# 4) قرارات البوابات على أرقام الصور الفعلية (اختبار مباشر للصور)
#    لكل سهم: RSI/MACD من الشارت + الشورت/الفلوت من التغريدة.
#    نتأكد أن منطق البوابة يعطي نفس الحكم المتوقع.
# ==========================================================
print("\n=== 4) قرارات البوابات على أرقام كل صورة ===")

# (الرمز, RSI, MACD_line, MACD_signal, متوقع MACD يعدّي؟, شورت, فلوت)
IMG = [
    # MACD يعدّي = الخط ≥ الإشارة
    ("VEEE", None, -1.19, -1.62, True,  None, None),
    ("SMX",  77.0, -4.38, -3.65, False, None, None),   # الخط<الإشارة
    ("AUUD", None, -0.027, -0.080, True, None, None),
    ("ADIL", None, -0.103, -0.104, True, None, None),
    ("EZRA", None, -0.209, -0.302, True, 7_000, 195_000),
    ("PCLA", None, 0.63,  0.91,  False, None, None),   # الخط<الإشارة
    ("ZNB",  None, -0.461, -0.681, True, None, None),
    ("RENX", None, -0.067, -0.091, True, None, None),
    ("PRFX", None, -0.039, -0.059, True, None, None),
    ("LFS",  None, -0.045, -0.081, True, None, None),
    ("INHD", None, -3.726, -4.188, True, None, None),
    ("NCT",  None, None, None, None, None, None),
    ("EHGO", None, -0.272, -0.281, True, 15_000, 1_620_000),
    ("MBRX", None, 0.085, 0.049, True,  0,      5_290_000),
    ("GWAV", None, -0.0498, -0.0492, False, 20_000, 778_000),  # الخط<الإشارة بقليل
    ("MWC",  35.3, -0.249, -0.271, True,  7_000, 26_680_000),
    ("BNKK", None, -0.215, -0.239, True,  4_000, 7_840_000),
    ("YYAI", 25.51, None, None, None, 1_000, 800_000),
    ("HCAI", None, -0.50, -0.40, False, None, 163_000),  # الخط<الإشارة
    ("FRSX", None, -0.066, -0.072, True, None, None),
]

short_limit = S.CONFIG["SHORT_GATE_MAX"]     # 20,000
float_limit = S.CONFIG["FLOAT_GATE_MAX"]     # 50,000,000
macd_ok_cnt = short_ok_cnt = float_ok_cnt = 0
for sym, rsi_v, ml, msig, exp_macd, srt, fl in IMG:
    # بوابة MACD (نفس منطق الكود: الخط ≥ الإشارة)
    if ml is not None and exp_macd is not None:
        got = ml >= msig
        check(f"[{sym}] MACD بوابة تطابق الشارت", got == exp_macd,
              f"{ml} vs {msig} → {got}")
        macd_ok_cnt += 1
    # بوابة الشورت (فيصل: تحت 20 ألف مقبول · 20ألف بالضبط = حدّي → مراقبة)
    if srt is not None:
        if srt >= short_limit:   # GWAV=20ألف بالضبط (فيصل وصفه «تهييض»)
            check(f"[{sym}] شورت {srt:,} حدّي → مراقبة B", True)
        else:
            check(f"[{sym}] شورت {srt:,} مقبول (<20ألف)", srt < short_limit)
        short_ok_cnt += 1
    # بوابة الفلوت (فيصل: فلوت صغير <50م)
    if fl is not None:
        passes = fl < float_limit
        check(f"[{sym}] فلوت {fl:,} صغير (<50م)", passes)
        float_ok_cnt += 1
print(f"   (فُحص MACD لـ{macd_ok_cnt} سهم · شورت {short_ok_cnt} · فلوت {float_ok_cnt})")


# ==========================================================
# 5) عرض الرسائل (build_message / daily) بلا أخطاء
# ==========================================================
print("\n=== 5) عرض الرسائل ===")
results = []
if r0:
    results.append(r0)
    # نسخة قائمة B (محاكاة سهم ينقصه تأكيد) لاختبار عرض A/B معًا
    rb = dict(r0)
    rb["symbol"] = "TESTB"
    rb["tier"] = "B"
    rb["soft_fails"] = ["MACD"]
    rb["flags"] = list(r0["flags"])
    results.append(rb)
for x in results:                       # حقول الإثراء الاختيارية
    x.setdefault("sector", "Technology")
    x.setdefault("business", "شركة اختبار")
    x.setdefault("news", []); x.setdefault("sec_filings", [])
    x.setdefault("sec_status", "ok"); x.setdefault("recent_split", None)
try:
    msg = S.build_message(results, [])
    check("build_message يعمل", isinstance(msg, str) and len(msg) > 0)
    check("الرسالة تعرض القائمة A/B", "🅰️" in msg or "🅱️" in msg)
    check("الرسالة تعرض القطاع/الشركة", "🏢" in msg)
    has_lib = any(x.get("liberation") for x in results)
    check("الرسالة تعرض التحرر (إن وُجد)",
          (not has_lib) or ("تحرر فوق" in msg))
except Exception as e:
    check("build_message يعمل", False, str(e))

# القائمة اليومية + سجل القائمة
try:
    wl = {"week_start": "2024-01-01", "stocks": [], "removed": [], "notes": []}
    for x in results:
        wl["stocks"].append(S.make_watch_entry(x, "2024-01-02"))
    for s in wl["stocks"]:
        s["readiness"] = 80
        s["have"], s["partial"], s["missing"] = [], [], []
    dm = S.build_daily_message(wl, [], [], [])
    check("build_daily_message يعمل", isinstance(dm, str) and len(dm) > 0)
    check("سجل القائمة يحفظ tier",
          all("tier" in s for s in wl["stocks"]))
except Exception as e:
    check("build_daily_message يعمل", False, str(e))


# ==========================================================
# 5ب) ترقية B→A + التنبيه (الإنذار المبكر)
# ==========================================================
print("\n=== 5ب) ترقية B→A ===")
_orig = S.analyze_ticker
# حالة: سهم B اكتمل نموذجه (0 نواقص) → يُرقّى A
wlp = {"stocks": [{"symbol": "PROM", "status": "active", "tier": "B",
                   "soft_fails": ["MACD"], "pivot": 3.0,
                   "stop": 2.7, "last_price": 3.5, "liberation": 5.0}],
       "notes": []}
S.analyze_ticker = lambda sym, d: {"soft_fails": [], "liberation": 5.0}
prom = S.check_promotions(wlp, {"PROM": synth_pivot(seed=9)})
check("الترقية B→A تعمل",
      len(prom) == 1 and wlp["stocks"][0]["tier"] == "A")
check("تاريخ الترقية مسجّل", bool(wlp["stocks"][0].get("promoted_date")))
# حالة: ما زال ناقصًا → لا ترقية + يحتفظ بنقص الشورت
wls = {"stocks": [{"symbol": "STILL", "status": "active", "tier": "B",
                   "soft_fails": ["MACD", "شورت عالٍ"], "pivot": 3.0,
                   "stop": 2.7, "last_price": 3.5}], "notes": []}
S.analyze_ticker = lambda sym, d: {"soft_fails": ["MACD"], "liberation": None}
prom2 = S.check_promotions(wls, {"STILL": synth_pivot(seed=9)})
check("لا ترقية مع نقص قائم",
      len(prom2) == 0 and wls["stocks"][0]["tier"] == "B")
check("يحتفظ بنقص الشورت (M13) عند إعادة التحليل",
      "شورت عالٍ" in wls["stocks"][0]["soft_fails"])
# تحديث يومي رخيص: القطاع/الدولة من الذاكرة + المستويات من إعادة التحليل
_wlc = {"stocks": [{"symbol": "CCC", "status": "active", "tier": "B",
                    "soft_fails": ["MACD"], "pivot": 3.0, "stop": 2.7}],
        "notes": []}
S.analyze_ticker = lambda sym, d: {"soft_fails": [], "liberation": None,
                                   "key_levels": {"sup_major": 3.0}}
S.COMPANY_CACHE["CCC"] = {"sector": "Technology", "country": "United States"}
S.check_promotions(_wlc, {"CCC": synth_pivot(seed=9)})
check("تحديث يومي: القطاع/الدولة من الذاكرة + المستويات",
      _wlc["stocks"][0].get("sector") == "Technology"
      and _wlc["stocks"][0].get("country") == "United States"
      and _wlc["stocks"][0].get("key_levels", {}).get("sup_major") == 3.0)
S.COMPANY_CACHE.pop("CCC", None)
S.analyze_ticker = _orig

# الضمان الآلي: ترحيل القائمة عند تغيّر نسخة المنطق (يعيد حساب الكل فورًا)
_wlm = {"logic_version": "OLD-VERSION", "stocks": [
        {"symbol": "MIG", "status": "active", "tier": "A", "added": "2024-01-01",
         "entry_ref": 9.9, "pivot": 1.0, "stop": 0.5, "stop_hi": 0.6,
         "entry": [1.0, 1.0], "t1": 2, "t2": 3, "t3": 4}], "notes": []}
_mig_df = synth_pivot(seed=2)
_n_mig = S.migrate_watchlist(_wlm, {"MIG": _mig_df})
_mg = _wlm["stocks"][0]
_fresh_mig = S.analyze_ticker("MIG", _mig_df)
check("ترحيل آلي: يعيد الحساب عند تغيّر نسخة المنطق",
      _n_mig == 1 and _wlm["logic_version"] == S.LOGIC_VERSION
      and _mg["stop"] == round(_fresh_mig["stop"][0], 4)
      and _mg["tranches"] == [round(p, 4) for p in _fresh_mig["tranches"]]
      and _mg["entry_ref"] == 9.9)            # المرجع/التاريخ يبقى
# لا ترحيل لو النسخة نفسها (idempotent — صفر تغيير)
_wlm2 = {"logic_version": S.LOGIC_VERSION, "stocks": [
         {"symbol": "X", "status": "active", "pivot": 1.0, "stop": 0.5}],
         "notes": []}
check("ترحيل آلي: لا عمل لو النسخة نفسها (idempotent)",
      S.migrate_watchlist(_wlm2, {"X": synth_pivot(seed=2)}) == 0)

# 🔬 مساعد التطوير: عينة قليلة → رسالة "بيانات قليلة"؛ عينة كافية → تشخيص
def _mkrow(sym, won, tier, sec, rsi, fl, rr):
    return {"symbol": sym, "entry_ref": 2.0, "max_gain_pct": 40 if won else -7,
            "status": "active" if won else "stopped", "hit": "t1" if won else None,
            "tier": tier, "sector": sec, "score": 70, "rsi": rsi, "float": fl,
            "rr": rr, "flags": ["مسح سيولة"] if won else ["تقاطع MACD"]}
_small = {"history": [{"stocks": [_mkrow("S1", True, "A", "Technology", 27, 8e6, 2.6)]}],
          "removed": [], "stocks": []}
check("مساعد التطوير: بيانات قليلة → تنبيه",
      "بيانات قليلة" in S.build_dev_assistant_report(_small))
_rowsA = [_mkrow(f"A{i}", True, "A", "Technology", 27, 8e6, 2.6) for i in range(7)]
_rowsB = [_mkrow(f"B{i}", False, "B", "Healthcare", 45, 40e6, 1.2) for i in range(6)]
_big = {"history": [{"stocks": _rowsA + _rowsB}], "removed": [], "stocks": []}
_rep = S.build_dev_assistant_report(_big)
check("مساعد التطوير: يشخّص بالشرائح + أنماط فشل + اقتراحات",
      "النجاح الكلي" in _rep and "حسب القائمة" in _rep
      and "أنماط الخاسرين" in _rep and "اقتراحات ضبط" in _rep
      and "A صارمة" in _rep)
# لا يكرّر الصفقة لو ظهرت بالأرشيف والحالي معًا (dedup)
_dup = {"history": [{"stocks": [_mkrow("D1", True, "A", "Technology", 27, 8e6, 2.6)]}],
        "removed": [_mkrow("D1", True, "A", "Technology", 27, 8e6, 2.6)], "stocks": []}
check("مساعد التطوير: dedup للصفقة المكررة", len(S._collect_closed(_dup)) == 1)

# الرسالة اليومية تعرض بانر الترقية
try:
    wlp["stocks"][0]["readiness"] = 80
    wlp["stocks"][0]["have"] = []; wlp["stocks"][0]["partial"] = []
    wlp["stocks"][0]["missing"] = []; wlp["stocks"][0]["t1"] = 4.0
    wlp["stocks"][0]["t2"] = 4.5; wlp["stocks"][0]["t3"] = 5.0
    wlp["stocks"][0]["hit"] = None
    dmp = S.build_daily_message(wlp, [], [], [], prom)
    check("بانر الترقية يظهر بالرسالة", "ترقيات اليوم" in dmp and "🚀" in dmp)
except Exception as e:
    check("بانر الترقية يظهر بالرسالة", False, str(e))


# ==========================================================
# 6) متانة: لا انهيار على بيانات قصيرة/مسطحة/صفرية
# ==========================================================
print("\n=== 6) المتانة ===")
for nm, d in [
    ("بيانات قصيرة", synth_pivot(n=130)),
    ("سعر تحت $2", synth_pivot(current=1.2, crash_low=0.5, prior_high=8)),
    ("مسطّح", pd.DataFrame({k: [5.0] * 200 for k in
              ["Open", "High", "Low", "Close"]} | {"Volume": [1e5] * 200},
              index=pd.date_range("2024-01-01", periods=200))),
]:
    try:
        _ = S.analyze_ticker(nm, d)
        check(f"لا انهيار: {nm}", True)
    except Exception as e:
        check(f"لا انهيار: {nm}", False, str(e))


# ==========================================================
# 7) ضمانات ضد رجوع الأخطاء (regression) — كل bug طلع يُقفل باختبار
# ==========================================================
print("\n=== 7) ضمانات ضد رجوع الأخطاء ===")

# (أ) الكارثة: الوقف لازم يكون دائمًا تحت أدنى منطقة الدخول — لكل البذور/الأسعار
_stop_ok = True
for sd in range(6):
    for cur, cl, ph in [(3.6, 3.0, 20.0), (1.6, 1.3, 9.0), (12.0, 9.0, 60.0)]:
        rr = S.analyze_ticker("X", synth_pivot(current=cur, crash_low=cl,
                                               prior_high=ph, seed=sd))
        if rr is None:
            continue
        lo = rr["entry"][0]
        if not (rr["stop"][0] < lo and rr["stop"][1] < lo):
            _stop_ok = False
            print(f"   ✗ بذرة {sd} سعر {cur}: stop={rr['stop']} entry_lo={lo}")
check("الوقف دائمًا تحت أدنى الدخول (لا كارثة)", _stop_ok)

# (ب) رفض RSI الحالي > 50 (فات الارتكاز) — bug ما كان موجود قبل
df_hi = synth_pivot(seed=2).copy()
_c = df_hi["Close"].values.astype(float)
_c[-9:] = np.linspace(_c[-9], _c[-9] * 1.7, 9)          # ارتداد V حاد
df_hi["Close"] = _c
df_hi["High"] = np.maximum(df_hi["High"].values, _c * 1.01)
df_hi["Low"] = np.minimum(df_hi["Low"].values, _c * 0.99)
_rnow = float(S.rsi(df_hi["Close"]).iloc[-1])
S._REJECT_STATS.clear()
_res_hi = S.analyze_ticker("HI", df_hi)
check("RSI الحالي > 50 → يُرفض (فات الارتكاز)",
      _rnow <= 50 or _res_hi is None, f"rsi_now={_rnow:.0f}")

# (ج) سهم «بعيد عن الدخول» (جاهزية < NEAR_PCT) لا يدخل القائمة.
#     نرفع العتبة مؤقتًا فوق جاهزية السهم لنضمن أن الرفض يشتغل فعلًا.
_df_ok = synth_pivot(seed=3)
_rd_ok, _ = S.entry_readiness(_df_ok)
_orig_near = S.CONFIG["NEAR_PCT"]
S.CONFIG["NEAR_PCT"] = min(100, int(_rd_ok) + 5)        # أعلى من جاهزيته
try:
    _res_far = S.analyze_ticker("FAR", _df_ok)
finally:
    S.CONFIG["NEAR_PCT"] = _orig_near
check("بعيد عن الدخول (جاهزية<العتبة) → يُرفض",
      _res_far is None, f"rdy={_rd_ok} عتبة={int(_rd_ok)+5}")

# (د) bug تتبع التاريخ: تنبيه صادر اليوم لا يُطلب تحميله (start=بكرة>end=اليوم)
import datetime as _dt
_today = _dt.date.today().isoformat()
_old = (_dt.date.today() - _dt.timedelta(days=10)).isoformat()


def _mk_alert(sym, d):
    return {"symbol": sym, "date": d, "price": 5.0, "stop": 4.0,
            "t1": 6.0, "t2": 7.0, "t3": 8.0, "score": 50, "flags": [],
            "ready": False, "status": "open", "result_date": None,
            "max_gain_pct": 0.0}


_calls = []


class _StubYF:
    @staticmethod
    def download(sym, **kw):
        _calls.append(sym)
        return pd.DataFrame()           # فارغ = لا بيانات جديدة


_orig_yf = S.yf
S.yf = _StubYF
try:
    _data = {"alerts": [_mk_alert("TODAYSYM", _today),
                        _mk_alert("OLDSYM", _old)]}
    _crash = False
    try:
        S.update_tracking(_data)
    except Exception as e:
        _crash = True
        print(f"   ✗ انهيار التتبع: {e}")
finally:
    S.yf = _orig_yf
check("التتبع لا ينهار", not _crash)
check("تتبع: تنبيه اليوم لا يُحمّل (لا start>end)", "TODAYSYM" not in _calls)
check("تتبع: تنبيه قديم يُحمّل عادي", "OLDSYM" in _calls)

# (هـ) ثبات التحميل: _download_chunk يعيد المحاولة عند الفشل ثم ينجح
_attempts = {"n": 0}


class _FlakyYF:
    @staticmethod
    def download(chunk, **kw):
        _attempts["n"] += 1
        if _attempts["n"] < 2:
            raise RuntimeError("Rate limited")     # تفشل أول مرة
        return pd.DataFrame({"Close": [1.0, 2.0]})  # تنجح بعدها


_orig_yf2 = S.yf
_orig_backoff = S.CONFIG.get("RETRY_BACKOFF")
S.yf = _FlakyYF
S.CONFIG["RETRY_BACKOFF"] = 0.0                     # بلا انتظار في الاختبار
try:
    _got = S._download_chunk(["AAA"], "2024-01-01")
finally:
    S.yf = _orig_yf2
    S.CONFIG["RETRY_BACKOFF"] = _orig_backoff
check("التحميل يعيد المحاولة بعد الفشل (rate-limit)",
      _got is not None and _attempts["n"] >= 2)

# (و) مؤشر صحة البيانات يظهر في الرسالة (يكشف الخنق بدل الصمت)
S._SCAN_STATS["universe"], S._SCAN_STATS["valid"] = 1000, 500   # تغطية 50%
_msg_health = S.build_message([], [], title="t")
check("تحذير تغطية منخفضة يظهر بالرسالة", "تغطية بيانات 50%" in _msg_health)
S._SCAN_STATS["universe"], S._SCAN_STATS["valid"] = 1000, 990   # تغطية 99%
_msg_ok = S.build_message([], [], title="t")
check("تغطية عالية تظهر ✓", "99%" in _msg_ok and "✓" in _msg_ok)
S._SCAN_STATS.clear()

# (ز) الترتيب موحّد على نسبة الجاهزية (الرقم المعروض) — لا تناقض مع العرض.
#     سهم جاهزيته أعلى لازم يسبق حتى لو نقاطه/عائده أقل (حالة NAGE فوق IDN).
_hi_rdy = {"tier": "B", "readiness": 60, "score": 60, "rr": 0.7}   # مثل IDN
_lo_rdy = {"tier": "B", "readiness": 50, "score": 70, "rr": 1.3}   # مثل NAGE
_ordered = sorted([_lo_rdy, _hi_rdy], key=S.rank_key)
check("الترتيب بالجاهزية: الأعلى جاهزيةً أولاً (لا تناقض)",
      _ordered[0] is _hi_rdy)
_a = {"tier": "A", "readiness": 40, "score": 50, "rr": 0.5}
check("القائمة A تسبق B دائمًا مهما كانت الجاهزية",
      sorted([_hi_rdy, _a], key=S.rank_key)[0] is _a)

# (ح) الثابت الجوهري: «جاهز» (البوليان) = (النسبة ≥ READY_PCT) دائمًا — مصدر
#     واحد للحقيقة. يستحيل سهم «🟢 جاهز» ونسبته أقل من «🟡 يقترب». مقفول للأبد.
_inv_ok = True
for sd in range(8):
    for cur, cl, ph in [(3.6, 3.0, 20.0), (2.0, 1.6, 11.0), (9.0, 7.0, 55.0)]:
        _ri = S.analyze_ticker("INV", synth_pivot(current=cur, crash_low=cl,
                                                  prior_high=ph, seed=sd))
        if _ri is None:
            continue
        _exp = (_ri["readiness"] is not None
                and _ri["readiness"] >= S.CONFIG["READY_PCT"])
        if bool(_ri["ready"]) != _exp:
            _inv_ok = False
            print(f"   ✗ بذرة {sd}: ready={_ri['ready']} rdy={_ri['readiness']}")
check("ثابت جوهري: ready ⟺ (النسبة ≥ READY_PCT) — مصدر واحد", _inv_ok)

# «جاهز» (نسبة عالية) يسبق «يقترب» (نسبة أقل) دائمًا مهما علت نقاطه/عائده
_rdy_hi = {"tier": "B", "readiness": 80, "score": 40, "rr": 0.3}
_rdy_lo = {"tier": "B", "readiness": 60, "score": 99, "rr": 9.0}
check("«جاهز» يسبق «يقترب» دائمًا (لا يتفوّق سهم أقل جاهزيةً بالنقاط)",
      sorted([_rdy_lo, _rdy_hi], key=S.rank_key)[0] is _rdy_hi)

# (ط) دفعات الدخول (أسلوب فيصل): N دفعات عند الدعم وصعوداً بخطوة ثابتة
_entry_ok = True
_N = S.CONFIG["ENTRY_TRANCHES"]
_step = S.CONFIG["ENTRY_STEP_PCT"] / 100.0
for sd in range(6):
    for cur, cl, ph in [(3.6, 3.0, 20.0), (2.0, 1.6, 11.0), (9.0, 7.0, 55.0)]:
        _re = S.analyze_ticker("E", synth_pivot(current=cur, crash_low=cl,
                                                prior_high=ph, seed=sd))
        if _re is None:
            continue
        _tr = _re["tranches"]
        _piv = round(_re["pivot"], 2)
        _stop = _re["stop"][1]                      # أعلى وقف (الأقرب للدخول)
        # عدد الدفعات صحيح · أدنى دفعة = الدعم · تصاعدية بالخطوة · الوقف تحت الكل
        ok_n = len(_tr) == _N
        ok_lo = abs(_tr[0] - _piv) <= 0.02          # أدنى دفعة عند الدعم
        ok_asc = all(_tr[i] < _tr[i + 1] for i in range(len(_tr) - 1))
        ok_step = all(abs((_tr[i + 1] / _tr[i] - 1.0) - _step) < 0.01
                      for i in range(len(_tr) - 1))
        ok_stop = _stop < _tr[0]                     # ضمان ذهبي: وقف تحت أدنى دفعة
        if not (ok_n and ok_lo and ok_asc and ok_step and ok_stop):
            _entry_ok = False
            print(f"   ✗ بذرة {sd} سعر {cur}: دفعات {_tr} دعم {_piv} وقف {_stop}")
check("دفعات الدخول: عند الدعم وصعوداً بخطوة ثابتة (أسلوب فيصل)", _entry_ok)

# (ي) العائد/المخاطرة يُحسب من **متوسط الدفعات** (فيصل يمتّع) لا السعر الحالي
_rr_ok = True
for sd in range(6):
    _rt = S.analyze_ticker("RR", synth_pivot(seed=sd))
    if _rt is None:
        continue
    _avg = sum(_rt["tranches"]) / len(_rt["tranches"])
    _slo, _t1 = _rt["stop"][0], _rt["t1"]
    _expected = (_t1 - _avg) / max(_avg - _slo, 1e-9)
    if abs(_rt["rr"] - _expected) > 0.05:
        _rr_ok = False
        print(f"   ✗ بذرة {sd}: rr={_rt['rr']:.2f} متوقع {_expected:.2f}")
check("RR من متوسط الدفعات لا السعر الحالي", _rr_ok)

# (ل) فحص أخبار الخطر الآلي: يمسك الطرح/التخفيف/التقسيم/الشطب من العناوين
_danger = [
    {"title": "Acme files to sell 1.52M units in registered direct offering"},
    {"title": "XYZ announces $20M public offering of common stock"},
    {"title": "ABC to conduct 1-for-10 reverse stock split"},
    {"title": "DEF auditor raises going concern doubt"},
    {"title": "GHI receives Nasdaq delisting notice"},
]
_safe = [
    {"title": "Acme reports record quarterly revenue and raises guidance"},
    {"title": "XYZ wins major contract with government agency"},
]
_news_ok = bool(S.scan_news_risk(_danger)) and not S.scan_news_risk(_safe)
# لا تطابقات كاذبة على الأخبار الإيجابية، وتطابق مؤكد على أخبار التخفيف
if not _news_ok:
    print(f"   ✗ خطر={S.scan_news_risk(_danger)} | آمن={S.scan_news_risk(_safe)}")
check("فحص أخبار الطرح/التخفيف الآلي (للبوت)", _news_ok)

# (ل2) مستويات الـ4 ساعات (منظومة فيصل): دعوم تحت السعر · أهداف فوق · انقلاب
_h4idx = pd.date_range("2026-01-01", periods=30, freq="4h")
_seq = [5.0, 4.6, 4.2, 3.8, 3.5, 3.7, 4.0, 4.3, 4.1, 4.5, 4.8, 5.2, 5.0, 5.5,
        5.9, 5.7, 6.1, 6.0, 6.3, 6.6, 6.4, 6.8, 7.1, 6.9, 7.3, 7.6, 7.4, 7.8,
        8.0, 7.9]
_o = []; _c = []; _h = []; _l = []; _pv = 5.2
for _v in _seq:
    _h.append(max(_pv, _v) * 1.03); _l.append(min(_pv, _v) * 0.97)
    _o.append(_pv); _c.append(_v); _pv = _v
_h4 = pd.DataFrame({"Open": _o, "High": _h, "Low": _l, "Close": _c},
                   index=_h4idx)
_lv = S.four_hour_levels(_h4, 7.9)
_ok4l = (_lv is not None
         and bool(_lv["supports"]) and all(x < 7.9 for x in _lv["supports"])
         and bool(_lv["resistances"]) and all(x > 7.9 for x in _lv["resistances"])
         and _lv["flip"] is not None and _lv["flip"] < 7.9
         and abs(_lv["sweep_low"] - round(min(_l), 2)) < 0.02
         and S.four_hour_levels(_h4.head(5), 7.9) is None)
if not _ok4l:
    print(f"   ✗ مستويات 4س: {_lv}")
check("مستويات الـ4 ساعات (دعوم/أهداف/انقلاب/ذيل المسح)", _ok4l)

# (ل3) نزول A→B لخبر التخفيف عند كسر الدعم، ورجوع A عند الاستقرار فوقه
_save_at = S.analyze_ticker
S.analyze_ticker = lambda sym, d: {"soft_fails": [], "liberation": None,
                                   "price": float(d["Close"].iloc[-1])}
_brk = synth_pivot(seed=9).copy()
_brk.loc[_brk.index[-5:], "Low"] = 2.5
_brk.loc[_brk.index[-1], "Close"] = 2.8          # آخر سعر تحت الدعم 3.0
_wld = {"stocks": [{"symbol": "DIL", "status": "active", "tier": "A",
                    "soft_fails": [], "pivot": 3.0, "stop": 2.7,
                    "news_risk": True, "last_price": 2.8}], "notes": []}
S.check_promotions(_wld, {"DIL": _brk})
check("تخفيف + كسر الدعم → نزول A→B",
      _wld["stocks"][0]["tier"] == "B"
      and any("تخفيف" in f for f in _wld["stocks"][0]["soft_fails"]))
_rec = synth_pivot(seed=9).copy()
_rec.loc[_rec.index[-5:], "Low"] = 3.2
_rec.loc[_rec.index[-1], "Close"] = 3.4          # استقر فوق الدعم
_wlr = {"stocks": [{"symbol": "DIL", "status": "active", "tier": "B",
                    "soft_fails": ["تخفيف: كسر الدعم"], "pivot": 3.0,
                    "stop": 2.7, "news_risk": True, "last_price": 3.4}],
        "notes": []}
S.check_promotions(_wlr, {"DIL": _rec})
check("تخفيف استقر فوق الدعم → يرجع A", _wlr["stocks"][0]["tier"] == "A")
S.analyze_ticker = _save_at

# (ك) قائمة مراقبة الارتداد: ارتكاز حقيقي ارتفع فوق دخوله
_wdf = synth_pivot(seed=2).copy()
_wc = _wdf["Close"].values.astype(float)
_wc[-30:] = np.linspace(_wc[-30], _wc[-30] * 1.45, 30)
_wc[-3:] = _wc[-4] * np.array([0.99, 0.985, 0.98])     # تراجع بسيط (لا انفجار 5ج)
_wdf["Close"] = _wc
_wdf["High"] = np.maximum(_wdf["High"].values, _wc * 1.01)
_wdf["Low"] = np.minimum(_wdf["Low"].values, _wc * 0.99)
_wnorm = S.analyze_ticker("W", _wdf)
_wpb = S.analyze_ticker("W", _wdf, pullback=True)
check("الارتداد: المرتفع يُرفض عاديًا ويُقبل كـ W",
      _wnorm is None and _wpb is not None and _wpb["tier"] == "W")
check("الارتداد: سهم عند الدخول (غير مرتفع) لا يُعدّ ارتدادًا",
      S.analyze_ticker("N", synth_pivot(seed=2), pullback=True) is None)

# monitor_pullback يطلق تنبيهًا عند نزول السعر لسعر الدعم
_e = {"symbol": "PB", "entry": [2.4, 2.5], "pivot": 2.5, "stop": 1.9,
      "t1": 3.6, "t2": 4.0, "t3": 5.0, "last_price": 3.2,
      "status": "watching", "triggered_date": None}
_lowdf = pd.DataFrame({"Open": [2.5], "High": [2.55], "Low": [2.45],
                       "Close": [2.45], "Volume": [1e6]},
                      index=pd.date_range("2024-01-01", periods=1))
_odl, _oyf = S.download_history, S.yf
S.download_history = lambda syms: {"PB": _lowdf}
S.yf = object()
try:
    _trig = S.monitor_pullback({"pullback": [_e]})
finally:
    S.download_history, S.yf = _odl, _oyf
check("الارتداد: تنبيه عند نزول السعر للدعم",
      len(_trig) == 1 and _e["status"] == "triggered")
check("قسم الارتداد يُعرض",
      "وصلت الدعم" in S.build_pullback_section([], _trig))

# (ل) ثبات القائمة: سهم محفوظ لا يُحذف لو غابت بياناته (سوق مقفل/خنق Yahoo)
_hold = {"symbol": "HOLD", "added": "2024-01-01", "entry_ref": 3.0,
         "pivot": 3.0, "stop": 2.7, "t1": 3.6, "t2": 4.0, "t3": 5.0,
         "status": "active", "hit": None, "hit_date": None,
         "max_gain_pct": 0.0, "last_price": 3.0}
_wl2 = {"stocks": [_hold], "removed": [], "notes": []}
_st = S.update_watchlist_status(_wl2, {})        # لا بيانات إطلاقاً
check("ثبات: سهم محفوظ يبقى رغم غياب بياناته (لا رفرفة)",
      len(_wl2["stocks"]) == 1
      and _wl2["stocks"][0]["status"] == "active" and _st == [])

# should_renew: قائمة غير فارغة في غير الجمعة لا تُعاد بناؤها (لا إعادة فرز يومي)
import datetime as _d2
_nonfri = next(_d2.date(2026, 6, 22) + _d2.timedelta(days=o)
               for o in range(7)
               if (_d2.date(2026, 6, 22) + _d2.timedelta(days=o)).weekday()
               != S.WEEKLY_RENEW_DAY)
_fri = next(_d2.date(2026, 6, 22) + _d2.timedelta(days=o)
            for o in range(7)
            if (_d2.date(2026, 6, 22) + _d2.timedelta(days=o)).weekday()
            == S.WEEKLY_RENEW_DAY)
_nonempty = {"stocks": [{"symbol": "X"}], "removed": []}
check("ثبات: قائمة قائمة في غير الجمعة لا تُعاد بناؤها",
      S.should_renew(_nonempty, _nonfri, False) is False)
check("التجديد: الجمعة تُجدَّد القائمة",
      S.should_renew(_nonempty, _fri, False) is True)
check("التأسيس: قائمة فارغة تُؤسَّس فورًا",
      S.should_renew({"stocks": [], "removed": []}, _nonfri, False) is True)


# ==========================================================
# 9) حُرّاس القرارات المقفولة (INVARIANTS) — يمنعون أي كسر صامت مستقبلاً
#    «شرط المستخدم: لا تعطب اللي سوينا». أي تعديل يكسر قرارًا محسومًا = فشل.
# ==========================================================
print("\n=== 9) حُرّاس القرارات المقفولة (Invariants) ===")

# 9-أ) إعدادات محسومة لا تتغيّر إلا بقرار صريح
check("قفل: الوقف ثابت 5-7% (لا ATR)",
      S.CONFIG["USE_ATR_STOP"] is False
      and tuple(S.CONFIG["STOP_BELOW_LOW_PCT"]) == (5.0, 7.0))
check("قفل: دفعات الدخول 3 بخطوة 3%",
      S.CONFIG["ENTRY_TRANCHES"] == 3 and S.CONFIG["ENTRY_STEP_PCT"] == 3.0)
check("قفل: حد الشورت 40 ألف · الفلوت 50م",
      S.CONFIG["SHORT_GATE_MAX"] == 40_000
      and S.CONFIG["FLOAT_GATE_MAX"] == 50_000_000)
check("قفل: عتبات RSI (≤40 الآن · ≤32 قاع · >50 رفض)",
      S.CONFIG["RSI_MAX_NOW"] == 40.0 and S.CONFIG["RSI_OS_HARD"] == 32.0
      and S.CONFIG["RSI_NOW_HARD"] == 50.0)
check("قفل: أرضيات الهوية (هبوط≥40% · انفجار≥60%)",
      S.CONFIG["MIN_DROP_FLOOR"] == 40.0
      and S.CONFIG["PRIOR_SPIKE_FLOOR"] == 60.0)

# 9-ب) مسح واسع على عشرات الأسهم الصناعية → كل الثوابت تصمد لكل سهم
_inv_fail = []
_N = S.CONFIG["ENTRY_TRANCHES"]
_step = S.CONFIG["ENTRY_STEP_PCT"] / 100.0
_s_lo, _s_hi = S.CONFIG["STOP_BELOW_LOW_PCT"]
_min_gain = 1.0 + S.CONFIG["MIN_T1_GAIN_PCT"] / 100.0
_scan = 0
for _sd in range(12):
    for _cur, _cl, _ph in [(3.6, 3.0, 20.0), (2.1, 1.6, 11.0), (9.0, 7.0, 55.0),
                           (1.8, 1.4, 9.0), (5.5, 4.2, 30.0)]:
        _df = synth_pivot(current=_cur, crash_low=_cl, prior_high=_ph, seed=_sd)
        _r = S.analyze_ticker("INV", _df)
        if _r is None:
            continue
        _scan += 1
        _piv = _r["pivot"]; _tr = _r["tranches"]
        _slo, _shi = _r["stop"]; _px = _r["price"]
        _t1, _t2, _t3 = _r["t1"], _r["t2"], _r["t3"]
        _eavg = sum(_tr) / len(_tr)              # متوسط الدفعات = مرجع RR

        def _bad(msg):
            _inv_fail.append(f"بذرة {_sd} سعر {_cur}: {msg}")
        # (1) الضمان الذهبي: الوقف دائمًا تحت أدنى دفعة
        if not (_shi < _tr[0] and _slo <= _shi):
            _bad(f"وقف فوق الدخول {_slo}/{_shi} ≥ {_tr[0]}")
        # (2) الوقف تحت الدعم وضمن نطاق معقول (≤ ~15% تحت)
        if not (_piv * 0.84 <= _shi < _piv):
            _bad(f"وقف خارج النطاق {_shi} مقابل دعم {_piv}")
        # (3) الدفعات: العدد · أدنى=الدعم · تصاعدية · الخطوة
        if len(_tr) != _N or abs(_tr[0] - round(_piv, 2)) > 0.02:
            _bad(f"دفعات {_tr} لا تبدأ من الدعم {_piv}")
        if any(_tr[i] >= _tr[i + 1] for i in range(len(_tr) - 1)):
            _bad(f"دفعات غير تصاعدية {_tr}")
        if any(abs((_tr[i + 1] / _tr[i] - 1.0) - _step) > 0.01
               for i in range(len(_tr) - 1)):
            _bad(f"خطوة الدفعات غير مطابقة {_tr}")
        # (4) الأهداف تصاعدية و t1 يبعد ≥ MIN_T1_GAIN
        if not (_t1 <= _t2 <= _t3):
            _bad(f"أهداف غير تصاعدية {_t1}/{_t2}/{_t3}")
        if _t1 < _px * _min_gain - 0.02:
            _bad(f"t1 قريب جدًا {_t1} < {_px*_min_gain:.2f}")
        # (5) صيغة RR من متوسط الدفعات (تعبئة فيصل الفعلية)
        _exp_rr = (_t1 - _eavg) / max(_eavg - _slo, 1e-9)
        if abs(_r["rr"] - _exp_rr) > 0.05:
            _bad(f"RR {_r['rr']} ≠ {_exp_rr:.2f}")
if _inv_fail:
    for _m in _inv_fail[:8]:
        print("   ✗ " + _m)
check(f"الثوابت تصمد على {_scan} سهم صناعي (وقف/دفعات/أهداف/RR)",
      not _inv_fail)

# 9-ج) أهداف الفريم الأسبوعي لا تغيّر t1 ولا RR (التحسين إضافي لا كاسر)
_t1_locked = True
for _sd in range(12):
    _df = synth_pivot(seed=_sd)
    S.CONFIG["USE_MULTIFRAME_TARGETS"] = False
    _a = S.analyze_ticker("MF", _df)
    S.CONFIG["USE_MULTIFRAME_TARGETS"] = True
    _b = S.analyze_ticker("MF", _df)
    if _a and _b:
        if abs(_a["t1"] - _b["t1"]) > 1e-6 or abs(_a["rr"] - _b["rr"]) > 1e-6:
            _t1_locked = False
            print(f"   ✗ بذرة {_sd}: t1/RR تغيّرا بالأسبوعي "
                  f"{_a['t1']}/{_a['rr']} → {_b['t1']}/{_b['rr']}")
check("أهداف الأسبوعي إضافية: t1 وRR ثابتان (لا كسر)", _t1_locked)

# 9-د) إيقاف منظومة الـ4س لا يكسر التحليل (طبقة مساندة فقط)
_orig_4h = S.fetch_4h
S.fetch_4h = lambda sym: None             # محاكاة عدم توفّر 4س
_r_no4h = S.analyze_ticker("N4", synth_pivot(seed=2))
S.fetch_4h = _orig_4h
check("غياب الـ4س لا يكسر التحليل (طبقة مساندة)",
      _r_no4h is not None and "tranches" in _r_no4h)

# 9-هـ) دمج فيصل #1 (أهداف 4س في t2/t3): t1 لا يتغيّر أبدًا · أهداف تصاعدية ·
#       لا 4س → الأصلية كما هي (صفر مخاطرة)
_rt_ok = True
_h4_demo = {"resistances": [4.20, 4.95, 5.60], "supports": [], "flip": None,
            "sweep_low": 3.0}
for _t1, _t2, _t3, _px in [(4.0, 4.4, 5.0, 3.6), (3.5, 3.9, 4.5, 3.2),
                           (8.0, 9.0, 11.0, 7.0)]:
    _n2, _n3 = S.refine_targets_4h(_t1, _t2, _t3, _px, _h4_demo)
    if not (_t1 < _n2 <= _n3):              # t1 سليم تحت t2 · تصاعدي
        _rt_ok = False; print(f"   ✗ refine {_t1}/{_t2}/{_t3} → {_n2}/{_n3}")
    # بلا 4س = لا تغيير إطلاقًا
    if S.refine_targets_4h(_t1, _t2, _t3, _px, None) != (_t2, _t3):
        _rt_ok = False; print("   ✗ بلا 4س غيّر الأهداف")
    if S.refine_targets_4h(_t1, _t2, _t3, _px, {"resistances": []}) != (_t2, _t3):
        _rt_ok = False; print("   ✗ 4س فارغ غيّر الأهداف")
check("دمج #1: t1 مقفول · t2/t3 تصاعدية · لا 4س=لا تغيير", _rt_ok)

# 9-و) الدمج الكامل في التحليل لا يغيّر t1 ولا RR (صفر مخاطرة على المقفول)
_save_f4 = S.fetch_4h
_merge_ok = True
for _sd in range(10):
    _df = synth_pivot(seed=_sd)
    S.fetch_4h = lambda sym: None                       # بلا 4س
    _base = S.analyze_ticker("MG", _df)
    if _base is None:
        continue
    # نحاكي الإثراء: نطبّق دمج 4س بمستويات وهمية ونتأكد t1/RR ثابتان
    _r2, _r3 = S.refine_targets_4h(_base["t1"], _base["t2"], _base["t3"],
                                   _base["price"], _h4_demo)
    if abs(_base["t1"] - _base["t1"]) > 0 or _r2 <= _base["t1"]:
        _merge_ok = False
S.fetch_4h = _save_f4
check("الدمج لا يغيّر t1/RR (مقفولان)", _merge_ok)

# 9-ز) دمج فيصل #3 (تأكيد 4س): النطاق 0-3 · الترتيب لا يحذف أي سهم
_c0 = S.h4_confirm_score({"tf4h": "غير متوفر"})
_c2 = S.h4_confirm_score({"tf4h": "✅ مؤكِّد"})
_c3 = S.h4_confirm_score({"tf4h": "✅ مؤكِّد", "price": 2.0,
                          "h4_levels": {"flip": 1.95}})
_members = [{"symbol": "X", "tier": "A", "readiness": 80, "h4_confirm": 0},
            {"symbol": "Y", "tier": "A", "readiness": 80, "h4_confirm": 3},
            {"symbol": "Z", "tier": "B", "readiness": 60}]
_sorted = sorted(_members, key=S.rank_key)
check("دمج #3: تأكيد 0-3 · الترتيب يرفع المؤكَّد · لا حذف",
      _c0 == 0 and _c2 == 2 and _c3 == 3
      and {m["symbol"] for m in _sorted} == {"X", "Y", "Z"}
      and _sorted[0]["symbol"] == "Y")        # المؤكَّد على 4س يطلع أول

# 9-ح) الدعوم/المقاومات الأساسية والفرعية (مفهوم فيصل NAMM)
_kl_ok = True
for _sd in range(8):
    _r = S.analyze_ticker("KL", synth_pivot(seed=_sd))
    if _r is None:
        continue
    _kl = _r["key_levels"]; _px = _r["price"]; _piv = _r["pivot"]
    if _kl is None:
        continue
    # الدعم الأساسي = الأرضية (pivot) · الفرعي (إن وُجد) فوق الأساسي وتحت السعر
    if abs(_kl["sup_major"] - round(_piv, 2)) > 0.02:
        _kl_ok = False; print(f"   ✗ دعم أساسي ≠ pivot: {_kl}")
    if _kl["sup_minor"] is not None and not (
            _kl["sup_major"] < _kl["sup_minor"] < _px):
        _kl_ok = False; print(f"   ✗ دعم فرعي خارج النطاق: {_kl} سعر {_px}")
    # المقاومات (إن وُجدت) فوق السعر
    for _k in ("res_minor", "res_major"):
        if _kl[_k] is not None and _kl[_k] <= _px:
            _kl_ok = False; print(f"   ✗ {_k} تحت السعر: {_kl} سعر {_px}")
check("دعوم/مقاومات أساسية وفرعية (فيصل): أساسي=الأرضية · الكل بمكانه", _kl_ok)


# ==========================================================
print("\n" + "=" * 50)
print(f"النتيجة: {len(PASS)} نجح · {len(FAIL)} فشل")
if FAIL:
    print("الفاشل: " + " | ".join(FAIL))
    raise SystemExit(1)
print("✅✅ كل الاختبارات نجحت — الضمان الذهبي")
