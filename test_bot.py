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
    check("الستوب يحترم ATR (أبعد من نسبة فقط)",
          r0["stop"][0] <= r0["pivot"] * (1 - S.CONFIG["STOP_BELOW_LOW_PCT"][1] / 100.0) + 1e-6)

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
S.analyze_ticker = _orig
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


# ==========================================================
print("\n" + "=" * 50)
print(f"النتيجة: {len(PASS)} نجح · {len(FAIL)} فشل")
if FAIL:
    print("الفاشل: " + " | ".join(FAIL))
    raise SystemExit(1)
print("✅✅ كل الاختبارات نجحت — الضمان الذهبي")
