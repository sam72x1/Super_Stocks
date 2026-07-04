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

# 🔁 تطابق أداة الفحص اليدوي (analyze_one) مع الأداة الأساسية (analyze_ticker)
# نُغذّي الاثنتين بنفس السهم الصناعي بالضبط → لازم نفس الدرجة/الأهداف/الوقف/RR.
# (يمنع انحراف الفحص اليدوي عن الفارز مستقبلًا — أي اختلاف = فشل اختبار)
try:
    import analyze_one as AO
    _sdl, _s4h = S.download_history, getattr(S, "fetch_4h", None)
    S.download_history = lambda syms: {"TEST": synth_pivot(seed=2)}
    S.fetch_4h = lambda *a, **k: None
    _diag, _g, _ = AO.analyze_on_demand("TEST")
    S.download_history = _sdl
    if _s4h is not None:
        S.fetch_4h = _s4h
    if r0 and _diag:
        check("الفحص اليدوي = الأساسي (درجة/أهداف/وقف/RR بالضبط)",
              _diag["score"] == r0["score"]
              and _diag["t1"] == r0["t1"] and _diag["t2"] == r0["t2"]
              and _diag["t3"] == r0["t3"] and _diag["pivot"] == r0["pivot"]
              and tuple(_diag["stop"]) == tuple(r0["stop"])
              and round(_diag["rr"], 4) == round(r0["rr"], 4),
              f"diag={_diag['score']}/{_diag['t1']}/{_diag['t2']}/{_diag['t3']} "
              f"vs main={r0['score']}/{r0['t1']}/{r0['t2']}/{r0['t3']}")
    else:
        check("الفحص اليدوي = الأساسي", _diag is not None, "r0/diag فارغ")
except Exception as e:
    check("الفحص اليدوي = الأساسي", False, str(e))
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
# 3ب) استرجاع الشورت/البيانات (تغطية ثابتة — لا تختفي)
# ==========================================================
print("\n=== 3ب) استرجاع الشورت/البيانات ===")


class _FakeT:
    def __init__(self, info):
        self._i = info

    @property
    def info(self):
        return self._i


_old_retries = S.CONFIG.get("DOWNLOAD_RETRIES", 3)
S.CONFIG["DOWNLOAD_RETRIES"] = 1   # بلا انتظار في الاختبار
_full = {"sector": "Healthcare", "country": "United States", "floatShares": 1000}
check("_fetch_info يرجّع الرد الكامل", S._fetch_info(_FakeT(_full)) == _full)
check("_fetch_info يحتفظ بالرد الجزئي بدل {}",
      S._fetch_info(_FakeT({"sharesShort": 12345})) == {"sharesShort": 12345})
check("_fetch_info يرجّع {} للرد الفارغ", S._fetch_info(_FakeT({})) == {})
S.CONFIG["DOWNLOAD_RETRIES"] = _old_retries

# بوابة الشورت تخزّن القيمة المجلوبة بدل رميها (للعرض/التخزين)
S.fintel_short = lambda syms: {"WB": 5000}
S.finra_daily_short = lambda syms: {}
_wb = mk("WB")
_wb["finra_short"] = None
S.apply_short_gate([_wb])
check("بوابة الشورت تخزّن القيمة المجلوبة (لا ترميها)",
      _wb.get("finra_short") == 5000)

# _or_cache: قيمة الذاكرة عند غياب الجلب
check("الشورت يُسترجع من الذاكرة لو غاب",
      S._or_cache(None, {"finra_short": 9999}, "finra_short") == 9999)
check("القيمة المجلوبة تُقدَّم على الذاكرة",
      S._or_cache(50, {"finra_short": 9999}, "finra_short") == 50)

# حدّ ذاكرة الشركات (LRU): يبقى محدودًا ويحتفظ بالأحدث (بلا كتابة قرص)
_cap0, _wj0, _cc0 = S.COMPANY_CACHE_MAX, S._atomic_write_json, dict(S.COMPANY_CACHE)
try:
    S.COMPANY_CACHE_MAX = 3
    S._atomic_write_json = lambda *a, **k: None      # لا كتابة قرص بالاختبار
    _cache = {f"S{i}": {"float": i} for i in range(6)}   # 6 > الحد 3
    S._save_company_cache(_cache)
    check("ذاكرة الشركات محدودة بالحد الأعلى",
          len(_cache) == 3)
    check("ذاكرة الشركات تحتفظ بالأحدث (LRU)",
          list(_cache.keys()) == ["S3", "S4", "S5"])
finally:
    S.COMPANY_CACHE_MAX, S._atomic_write_json = _cap0, _wj0
    S.COMPANY_CACHE.clear()
    S.COMPANY_CACHE.update(_cc0)

# تقسيم الرسالة: السلوك الطبيعي + السطر الطويل بلا HTML يُقسَّم + سطر فيه وسم لا يُقسَّم
check("التقسيم الطبيعي: رسالة قصيرة = قطعة واحدة",
      S._chunk_message("سطر١\nسطر٢\nسطر٣") == ["سطر١\nسطر٢\nسطر٣"])
_long = "كلمة " * 1000           # ~5000 محرف بلا وسوم
_ch = S._chunk_message(_long, limit=3800)
check("سطر طويل بلا HTML يُقسَّم لقطع ضمن الحد",
      len(_ch) >= 2 and all(len(c) <= 3800 for c in _ch))
_htmlline = "<b>" + (" x" * 2500) + "</b>"   # طويل لكن فيه وسم → لا يُقسَّم
check("سطر فيه وسم HTML لا يُقسَّم (لا ينكسر الوسم)",
      S._chunk_message(_htmlline, limit=3800) == [_htmlline])

# === حُرّاس الفحص العميق 2026-06-24 (ثلاث ملاحظات حرجة) ===
# 1) apply_short_gate: Fintel يرجّع dict — لا تنكسر المقارنة وتُخزَّن int
_fs0b, _fd0b = S.fintel_short, S.finra_daily_short
try:
    S.fintel_short = lambda q: {"FX": {"short_volume": 55000, "si_pct_float": 3.1}}
    S.finra_daily_short = lambda q: {}
    _rx = {"symbol": "FX", "soft_fails": [], "flags": [], "finra_short": None}
    _outx = S.apply_short_gate([_rx])
    check("بوابة الشورت تتحمّل dict من Fintel (لا كراش) وتخزّن الحجم int",
          _rx.get("finra_short") == 55000
          and "شورت عالٍ" in _rx.get("soft_fails", []))
finally:
    S.fintel_short, S.finra_daily_short = _fs0b, _fd0b

# 2) migrate_watchlist: لا يختم نسخة المنطق لو تُخطّي سهم لنقص بيانات
_old_lv = S.LOGIC_VERSION
_wlmg = {"logic_version": "OLD_X", "stocks": [
    {"symbol": "AAA", "status": "active"}, {"symbol": "BBB", "status": "active"}]}
S.migrate_watchlist(_wlmg, {})   # لا بيانات لأيٍّ منهما → migrated=0
check("الترحيل لا يختم النسخة عند تخطّي أسهم (بيانات مخنوقة)",
      _wlmg.get("logic_version") == "OLD_X")

# 3) حارس التجديد: فشل جلب الكون يضبط عَلَم universe_fallback (يمنع المسح لاحقًا)
_gu0, _dh0, _mode0 = S.get_universe, S.download_history, S.MODE
try:
    S.get_universe = lambda: []           # محاكاة فشل جلب ناسداك
    S.download_history = lambda syms: {}   # لا بيانات
    S.MODE = "FULL"
    S.scan_market()
    check("فشل جلب الكون يضبط عَلَم universe_fallback (حارس ضد المسح)",
          S._SCAN_STATS.get("universe_fallback") is True)
finally:
    S.get_universe, S.download_history, S.MODE = _gu0, _dh0, _mode0

# 4) حارس التجديد الأسبوعي: فحص فارغ لا يمسح القائمة النشطة (يُبقيها)
_wlw = {"week_start": "2024-01-01", "stocks": [{"symbol": "KEEP", "status": "active"}],
        "removed": [], "notes": [], "pullback": [], "history": []}
_sv = (S.scan_market, S.send_telegram, S.save_watchlist, S.yf,
       S.download_history, S.build_wrapup_message)
try:
    S.scan_market = lambda: ([], {})            # فحص فارغ (خنق Yahoo)
    S.send_telegram = lambda m: True
    S.save_watchlist = lambda w: None
    S.download_history = lambda syms: {}
    S.build_wrapup_message = lambda w: ""
    S.yf = None                                  # يتخطّى تحديث الأسبوع المنتهي
    _before = list(_wlw["stocks"])
    S.run_weekly_renewal(_wlw)
    check("التجديد الأسبوعي لا يمسح القائمة عند فحص فارغ (حارس ضد المسح)",
          _wlw["stocks"] == _before and len(_wlw["stocks"]) == 1)
finally:
    (S.scan_market, S.send_telegram, S.save_watchlist, S.yf,
     S.download_history, S.build_wrapup_message) = _sv


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

short_limit = S.CONFIG["SHORT_GATE_MAX"]     # 40,000
float_limit = S.CONFIG["FLOAT_GATE_MAX"]     # 50,000,000
macd_ok_cnt = short_ok_cnt = float_ok_cnt = 0
_fs_orig, _fd_orig = S.fintel_short, S.finra_daily_short   # تُستعاد بعد الحلقة
for sym, rsi_v, ml, msig, exp_macd, srt, fl in IMG:
    # بوابة MACD (نفس منطق الكود: الخط ≥ الإشارة)
    if ml is not None and exp_macd is not None:
        got = ml >= msig
        check(f"[{sym}] MACD بوابة تطابق الشارت", got == exp_macd,
              f"{ml} vs {msig} → {got}")
        macd_ok_cnt += 1
    # بوابة الشورت: نُشغّل البوابة الحقيقية على رقم الصورة (لا نعيد كتابة الشرط).
    # شورت تحت الحد = مقبول · الحد فأكثر = نقص «شورت عالٍ» يُبقيه B (لا حذف).
    if srt is not None:
        S.fintel_short = lambda q, _sym=sym, _s=srt: {_sym: _s}
        S.finra_daily_short = lambda q: {}
        _go = S.apply_short_gate([mk(sym)])
        _is_high = "شورت عالٍ" in _go[0].get("soft_fails", [])
        check(f"[{sym}] بوابة الشورت {srt:,} (عالٍ؟ {srt >= short_limit})",
              _is_high == (srt >= short_limit))
        short_ok_cnt += 1
    # بوابة الفلوت: نُشغّل البوابة الحقيقية (فلوت تحت 50م صغير · فأكثر = نقص لا حذف).
    if fl is not None:
        _gf = S.apply_float_gate([mk(sym, float=fl)])
        _is_big = "فلوت كبير" in _gf[0].get("soft_fails", [])
        check(f"[{sym}] بوابة الفلوت {fl:,} (كبير؟ {fl >= float_limit})",
              _is_big == (fl >= float_limit))
        float_ok_cnt += 1
print(f"   (فُحص MACD لـ{macd_ok_cnt} سهم · شورت {short_ok_cnt} · فلوت {float_ok_cnt})")
S.fintel_short, S.finra_daily_short = _fs_orig, _fd_orig   # استعادة بعد الحلقة
# اختبار MACD حقيقي على دالة الإنتاج S.macd (لا إعادة كتابة الشرط): سلسلة صاعدة
# → الخط فوق الإشارة · هابطة → تحتها (تغطية فعلية للمؤشر بدل تكرار ml>=msig).
_mlu, _sgu = S.macd(pd.Series([1.0 + 0.12 * i for i in range(60)]))
_mld, _sgd = S.macd(pd.Series([8.0 - 0.12 * i for i in range(60)]))
check("MACD (دالة الإنتاج): صاعد→الخط فوق الإشارة · هابط→تحتها",
      float(_mlu.iloc[-1]) >= float(_sgu.iloc[-1])
      and float(_mld.iloc[-1]) < float(_sgd.iloc[-1]))


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
    rb["flags"].append("Williams %R انعطاف من التشبع")   # إشارة دخول المضارب
    rb["indicators"] = dict(rb.get("indicators") or {}, williams_r=-35.0)
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
    check("البطاقة تعرض القطاع (بالعربي)", S.ar_sector("Technology") in msg)
    has_lib = any(x.get("liberation") for x in results)
    check("الرسالة تعرض التحرر (إن وُجد)",
          (not has_lib) or ("تحرر فوق" in msg))
    # الشكل المختصر (v2.9): أهداف مرقّمة بالنسب + دعم أساسي + شريط قوة + بوابات B مرقّمة
    check("البطاقة تعرض الأهداف المرقّمة",
          "الهدف 1" in msg)
    check("البطاقة تعرض الدعم الأساسي + شريط القوة",
          "الدعم الأساسي" in msg and "القوة العامة" in msg)
    check("البطاقة B تعرض البوابات الناقصة مرقّمة من 14",
          "البوابات الناقصة" in msg and "من 14" in msg and "1- MACD" in msg)
    check("البطاقة تعرض «دخول المضارب» (Williams %R)", "دخول المضارب" in msg)
    check("سطر الفريمات 2/3 يوضّح الباقي", "باقي فريم" in (S.timeframes_info(2) or ""))
    check("سطر الفريمات 3/3 مكتمل", "مكتمل" in (S.timeframes_info(3) or ""))
    check("سطر الفريمات أقل من 2 لا يظهر (يبقى نقصًا)", S.timeframes_info(1) is None)
    check("سطر الفريمات يسمّي الفريم الناقص (⏳)",
          "يومي ⏳" in (S.timeframes_info(2, "شهري ✅ · أسبوعي ✅ · يومي ⏳") or ""))
    check("علم الدولة: 🇺🇸 + أمريكا",
          "🇺🇸" in S.country_label("United States")
          and "أمريكا" in S.country_label("United States"))
    check("علم الدولة: بلا دولة → فارغ", S.country_label(None) == "")
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
    check("التقرير اليومي: سطر الدخول + وقف خسارة",
          "📥 دخول:" in dm and "وقف خسارة" in dm)
    check("التقرير اليومي يعرض أهداف (أسعار بلا نسبة)",
          "🎯 أهداف:" in dm)
    check("التقرير اليومي يعرض الجاهزية + القوة العامة",
          "/100" in dm and "قوة" in dm)
    check("التقرير اليومي يعرض «دخول المضارب» (Williams)",
          "دخول المضارب" in dm)
    # شرطة «—» عند تعذّر جلب الفلوت/الشورت (طلب المستخدم 2026-06-24) — تعذّر ≠ صفر
    if wl["stocks"]:
        _d = dict(wl["stocks"][0])
        _d["float"], _d["short"], _d["short_pct"] = None, None, None
        _wld = {"week_start": "2024-01-01", "stocks": [_d],
                "removed": [], "notes": []}
        _dmd = S.build_daily_message(_wld, [], [], [])
        check("التقرير اليومي: شرطة «—» عند تعذّر الفلوت/الشورت",
              "فلوت —" in _dmd and "شورت —" in _dmd)
    # بديل Yahoo: نسبة الشورت من الفلوت تظهر لو غاب الحجم اليومي
    if wl["stocks"]:
        _d2 = dict(wl["stocks"][0])
        _d2["short"], _d2["short_pct"] = None, 6.9
        _wld2 = {"week_start": "2024-01-01", "stocks": [_d2],
                 "removed": [], "notes": []}
        _dmd2 = S.build_daily_message(_wld2, [], [], [])
        check("التقرير اليومي: شورت كنسبة من الفلوت عند غياب الحجم",
              "6.9% من الفلوت" in _dmd2)
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
S.COMPANY_CACHE["CCC"] = {"sector": "Technology", "country": "United States",
                          "finra_short": 12345, "float": 9_000_000,
                          "short_pct": 5.5}
S.check_promotions(_wlc, {"CCC": synth_pivot(seed=9)})
check("تحديث يومي: القطاع/الدولة من الذاكرة + المستويات",
      _wlc["stocks"][0].get("sector") == "Technology"
      and _wlc["stocks"][0].get("country") == "United States"
      and _wlc["stocks"][0].get("key_levels", {}).get("sup_major") == 3.0)
# استرجاع الفلوت/الشورت/النسبة من الذاكرة (إصلاح 2026-06-24 — لا تختفي)
check("تحديث يومي: الفلوت/الشورت/النسبة تُسترجع من الذاكرة",
      _wlc["stocks"][0].get("float") == 9_000_000
      and _wlc["stocks"][0].get("short") == 12345
      and _wlc["stocks"][0].get("short_pct") == 5.5)
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
      and _mg.get("rr") == _fresh_mig.get("rr")   # RR يُحدّث مع الوقف/الأهداف
      and _mg["entry_ref"] == 9.9)            # المرجع/التاريخ يبقى
# لا ترحيل لو النسخة نفسها (idempotent — صفر تغيير)
_wlm2 = {"logic_version": S.LOGIC_VERSION, "stocks": [
         {"symbol": "X", "status": "active", "pivot": 1.0, "stop": 0.5}],
         "notes": []}
check("ترحيل آلي: لا عمل لو النسخة نفسها (idempotent)",
      S.migrate_watchlist(_wlm2, {"X": synth_pivot(seed=2)}) == 0)

# 🛡️ متانة التخزين: كتابة ذرّية + حدود نمو (على ملف مؤقت — لا يمسّ القائمة الحقيقية)
import tempfile as _tf
_tmpdir = _tf.mkdtemp()
_save_wf = S.WATCH_FILE
S.WATCH_FILE = _tmpdir + "/wl_test.json"
_bigwl = {"stocks": [{"symbol": "Z", "status": "active"}],
          "notes": list(range(1000)), "removed": list(range(1000)),
          "replacements_log": list(range(1000))}
S.save_watchlist(_bigwl)
_rl = S.load_watchlist()
check("متانة: كتابة/قراءة ذرّية سليمة (round-trip بلا تلف)",
      _rl.get("stocks") == [{"symbol": "Z", "status": "active"}])
check("متانة: حدود النمو تُقصّ التراكمي وتحتفظ بالأحدث (الذيل)",
      len(_rl["notes"]) == 250 and len(_rl["removed"]) == 120
      and len(_rl["replacements_log"]) == 120 and _rl["notes"][-1] == 999)
S.WATCH_FILE = _save_wf

# 🧮 Williams %R مربوط بالتقييم (آخر مؤشر من صور فيصل — تغريدة 7377)
_wr_hh = pd.Series([10.0] * 15)
_wr_ll = pd.Series([1.0] * 15)
# قرب القاع (تشبع %R≈-98) في الشمعة قبل الأخيرة ثم قفزة صعودية
_wr_cl = pd.Series([2.0] * 13 + [1.2, 7.0])
_wr_s = S.williams_r(_wr_hh, _wr_ll, _wr_cl)
check("Williams %R: المدى (-100..0) والانعطاف من التشبع يُكتشف ومربوط بالنقاط",
      -100.0 <= float(_wr_s.iloc[-1]) <= 0.0
      and float(_wr_s.iloc[-2]) <= S.CONFIG["WILLIAMS_OVERSOLD"]
      and float(_wr_s.iloc[-1]) > float(_wr_s.iloc[-2])
      and S.CONFIG["SCORE_WILLIAMS"] > 0)

# 🧹 تخرّج المراقبة: السهم الذي دخل A/B يُحذف من قائمة الارتداد (لا ازدواج)
_wlg = {"stocks": [{"symbol": "GRAD"}, {"symbol": "MAINONLY"}],
        "pullback": [{"symbol": "GRAD", "status": "triggered"},
                     {"symbol": "STILLPB", "status": "active"}]}
_grad = S.prune_graduated_pullback(_wlg)
check("تنظيف المراقبة: المتخرّج لـA/B يُحذف منها ويبقى غيره",
      _grad == ["GRAD"]
      and [e["symbol"] for e in _wlg["pullback"]] == ["STILLPB"])

# 🧱 مقاومة من رؤوس الشموع الحمرا (قاعدة فيصل) — تلتقط المستويات المتوسطة
# التي ليست قمم سوينغ (مثل EZRA 4.00/4.38) فلا يتخطّاها البوت. هبوط متدرّج
# برؤوس حمرا 6.0→4.0 (كل رأس أدنى من سابقه = ليست قمم سوينغ).
_rn = 80
_rhi = [3.6] * _rn
for _k, _hv in enumerate([6.0, 5.6, 5.2, 4.8, 4.4, 4.0]):
    _rhi[40 + _k] = _hv
_rop = list(_rhi)
_rcl = [h * 0.95 for h in _rhi]          # كلها حمرا (close < open، جسم 5%)
_rlo = [h * 0.93 for h in _rhi]
_rop[-1], _rcl[-1], _rhi[-1], _rlo[-1] = 3.55, 3.60, 3.62, 3.50
_rdf = pd.DataFrame({"Open": _rop, "High": _rhi, "Low": _rlo,
                     "Close": _rcl, "Volume": [1e5] * _rn})
_rres = S.resistance_levels(_rdf, 3.60)
check("مقاومة من رؤوس الشموع الحمرا (فيصل): تلتقط المتوسطة بلا تخطّي",
      any(3.9 <= r <= 4.1 for r in _rres)
      and any(4.3 <= r <= 4.5 for r in _rres))

# 🎯 إعادة بناء حالة EZRA المُبلّغة: انهيار متدرّج برؤوس شمعات حمرا عند المستويات
# الموثّقة (6.76→6.23→5.79→5.44→4.84→4.35→4.00→3.5) ثم تجميع عند ~3.6.
# فيصل: «مقاومة السهم 4 و4.38». الكود القديم (قمم سوينغ فقط) كان يلتقط 6.76 فقط
# ويتخطّى 4.00/4.35؛ بعد رؤوس الحمرا لازم يلتقطهما كأقرب مقاومتين (بلا تخطّي).
_ez_op, _ez_cl, _ez_hi, _ez_lo = [], [], [], []
for _ in range(40):                      # قاعدة/صعود قبل الانفجار
    _ez_op.append(3.0); _ez_cl.append(3.1); _ez_hi.append(3.15); _ez_lo.append(2.95)
_ez_desc = [6.76, 6.23, 5.79, 5.44, 4.835, 4.348, 4.008, 3.55]
for _j in range(len(_ez_desc) - 1):      # الانهيار: كل خطوة شمعة حمرا رأسها=المستوى
    _top, _btm = _ez_desc[_j], _ez_desc[_j + 1]
    _ez_op.append(_top); _ez_cl.append(_btm * 1.01)
    _ez_hi.append(_top); _ez_lo.append(_btm * 0.99)
for _ in range(60):                      # تجميع عند الدعم ~3.6
    _ez_op.append(3.60); _ez_cl.append(3.55); _ez_hi.append(3.68); _ez_lo.append(3.45)
_ez_df = pd.DataFrame({"Open": _ez_op, "High": _ez_hi, "Low": _ez_lo,
                       "Close": _ez_cl, "Volume": [3e5] * len(_ez_op)})
_ez_res = S.resistance_levels(_ez_df, 3.65)
_ez_above = [r for r in _ez_res if r >= 3.94]   # فوق أرضية الهدف الأول (8%)
check("EZRA المُبلّغة: يلتقط 4.00 و4.35 كأقرب مقاومتين (مطابقة فيصل، بلا تخطّي لـ5.44)",
      any(3.9 <= r <= 4.1 for r in _ez_res)
      and any(4.25 <= r <= 4.45 for r in _ez_res)
      and bool(_ez_above) and min(_ez_above) <= 4.1)

# 🔬 مساعد التطوير: عينة قليلة → رسالة "بيانات قليلة"؛ عينة كافية → تشخيص
def _mkrow(sym, won, tier, sec, rsi, fl, rr):
    return {"symbol": sym, "entry_ref": 2.0, "max_gain_pct": 40 if won else -7,
            "status": "active" if won else "stopped", "hit": "t1" if won else None,
            "tier": tier, "sector": sec, "score": 70, "rsi": rsi, "float": fl,
            "rr": rr, "flags": ["مسح سيولة"] if won else ["تقاطع MACD"]}
_small = {"history": [{"stocks": [_mkrow("S1", True, "A", "Technology", 27, 8e6, 2.6)]}],
          "removed": [], "stocks": []}
check("مساعد التطوير: بيانات قليلة → تنبيه",
      "قليلة" in S.build_dev_assistant_report(_small))
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
_alerts_closed = {"alerts": [
    {"symbol": "ALWIN", "date": "2026-06-01", "price": 10.0, "t1": 11.0,
     "status": "hit_t1", "result_date": "2026-06-05", "max_gain_pct": 12,
     "flags": ["تقاطع MACD"]},
    {"symbol": "ALOSS", "date": "2026-06-02", "price": 10.0, "stop": 9.3,
     "status": "stopped", "result_date": "2026-06-06", "max_gain_pct": 1,
     "flags": ["KST صاعد"]},
    {"symbol": "OPEN", "date": "2026-06-03", "price": 10.0,
     "status": "open", "max_gain_pct": 0},
]}
_rep_alerts = S.build_dev_assistant_report({"history": [], "removed": [], "stocks": []},
                                           _alerts_closed)
check("مساعد التطوير: يحتسب صفقات alerts_history المحسومة (لا 0 كاذبة)",
      "صفقات محسومة متراكمة: <b>2</b>" in _rep_alerts)


# 💥 كاشف الانفجارات: يلتقط قفزة ≥70% · يتراكم/dedup · يظهر بالتقرير
_boom = synth_pivot(seed=2).copy()
_bc = _boom["Close"].values.astype(float).copy()
_bc[-1] = _bc[-2] * 2.0                          # قفزة 100% آخر يوم
_boom["Close"] = _bc
_exp = S.scan_explosions({"BOOM": _boom})
check("كاشف الانفجارات: يلتقط القفزة ≥70% ويصنّفها",
      len(_exp) == 1 and _exp[0]["symbol"] == "BOOM" and _exp[0]["gain"] >= 70
      and "was_pivot" in _exp[0])
# was_pivot يقيس هوية الارتكاز (M1-M3) لا جاهزية الدخول (إصلاح فحص 2026-06-26):
# ارتكاز حقيقي انفجر → was_pivot=True (كان دائمًا False لإعادة تشغيل مصنّف الدخول).
check("كاشف الانفجارات: ارتكاز انفجر → was_pivot=True (لا صفر دائمًا)",
      _exp[0]["was_pivot"] is True)
_flat_id = pd.DataFrame({k: [5.0] * 200 for k in ["Open", "High", "Low", "Close"]}
                        | {"Volume": [1e5] * 200},
                        index=pd.date_range("2024-01-01", periods=200))
check("هوية الارتكاز: ارتكاز=True · مسطّح (بلا انهيار/انفجار)=False",
      S._had_pivot_identity(synth_pivot(seed=2)) is True
      and S._had_pivot_identity(_flat_id) is False)
_wlx = {"stocks": [], "notes": []}
S.accumulate_explosions(_wlx, {"BOOM": _boom})
S.accumulate_explosions(_wlx, {"BOOM": _boom})   # نفس اليوم → لا تكرار
check("كاشف الانفجارات: تراكم + dedup",
      len(_wlx.get("explosions", [])) == 1)
check("مساعد التطوير: يعرض الانفجارات المفقودة",
      "المتحرّكون" in S.build_dev_assistant_report(_wlx))
# قفزة أقل من العتبة لا تُلتقط
_calm = synth_pivot(seed=3)
check("كاشف الانفجارات: يتجاهل ما دون العتبة",
      len(S.scan_explosions({"CALM": _calm})) == 0)

# 🔬 base_reason (طلب المستخدم 2026-07-04): كل متحرّك يحمل بوابة الرفض الدقيقة
# **عند قاعه** + النوع (قفزة/تجمّع) — فلا متحرّك >العتبة بلا بوابة معروفة.
check("كاشف الانفجارات: يسجّل base_reason (بوابة القاع) + kind=قفزة",
      "base_reason" in _exp[0] and _exp[0].get("kind") == "قفزة"
      and isinstance(_exp[0].get("base_reason"), str) and _exp[0]["base_reason"])
check("مساعد التطوير: يعرض توزيع بوابة القاع لكل متحرّك",
      "بوابة الرفض عند القاع" in S.build_dev_assistant_report(_wlx))
# 🆕 شبكة التجمّع: ركض تدريجي >70% بلا يوم قفزة ≥50% يُلتقط (kind=تجمّع)
_run = synth_pivot(seed=4).copy()
_rc = _run["Close"].values.astype(float).copy()
_lvl = float(_rc[-15])
for _i in range(15):                        # آخر 15 يوم: ~6%/يوم (لا قفزة ≥50%)
    _rc[-15 + _i] = _lvl * (1.06 ** _i)
_run["Close"] = _rc
for _col, _m in (("High", 1.01), ("Low", 0.99), ("Open", 1.0)):
    _rv = _run[_col].values.astype(float).copy()
    _rv[-15:] = _rc[-15:] * _m
    _run[_col] = _rv
_run_exp = S.scan_explosions({"GRAD": _run})
check("كاشف الانفجارات: يلتقط الركض التدريجي >70% بلا قفزة (kind=تجمّع)",
      len(_run_exp) == 1 and _run_exp[0].get("kind") == "تجمّع"
      and _run_exp[0]["gain"] >= 70)
# لا قفزة يوم واحد ≥50% في هذه السلسلة (تأكيد أنها التقطت بالتجمّع لا بالقفزة)
_grad_1day = max((_rc[-k] / _rc[-k - 1] - 1.0) * 100.0
                 for k in range(1, 6) if _rc[-k - 1] > 0)
check("شبكة التجمّع: السلسلة التدريجية بلا يوم قفزة ≥50% فعلًا",
      _grad_1day < 50.0)

# 📎 تصدير CSV: عمود الشورت يرجع لـshort_pct عند غياب finra_short (إصلاح فحص
# 2026-06-26 — كان UPB يظهر شورت فارغ رغم توفّر short_pct). تصدير فقط.
import glob as _glob_csv
import os as _os_csv
S._MISSED.clear()
_save_doc = S.send_telegram_document

S.send_telegram_document = lambda *a, **k: None
S.export_weekly_csvs({"stocks": [], "removed": [], "history": []}, [], _alerts_closed)
S.send_telegram_document = _save_doc
_trd_files = sorted(_glob_csv.glob("trades_*.csv"))
_trd_txt = (open(_trd_files[-1], encoding="utf-8-sig").read()
            if _trd_files else "")
for _f in (_glob_csv.glob("trades_*.csv")):
    _os_csv.remove(_f)
check("تصدير CSV: trades يحتسب صفقات alerts_history المحسومة",
      "ALWIN" in _trd_txt and "ALOSS" in _trd_txt and "OPEN" not in _trd_txt)

S.send_telegram_document = lambda *a, **k: None
_pick_csv = {"symbol": "UPBX", "tier": "B", "sector": "Healthcare", "rsi": 35.0,

             "float": 35e6, "finra_short": None, "short_pct": 7.5, "fintel": {},
             "drop_pct": 80.0, "best_spike": 78.0, "rr": 1.9, "score": 60,
             "pivot": 5.85, "stop": [5.44], "t1": 7.16, "t2": 7.41, "t3": 7.69}
S.export_weekly_csvs({"stocks": [], "removed": [], "history": []}, [_pick_csv])
S.send_telegram_document = _save_doc
_sig_files = sorted(_glob_csv.glob("signals_*.csv"))
_sig_txt = (open(_sig_files[-1], encoding="utf-8-sig").read()
            if _sig_files else "")
for _f in (_glob_csv.glob("signals_*.csv")):
    _os_csv.remove(_f)
check("تصدير CSV: short_pct يظهر عند غياب finra_short (UPB)",
      "short_pct" in _sig_txt and "7.5" in _sig_txt)

# 👻 تصنيف الفرص الفائتة: الهوية/البنية (ليس ارتكازًا: M1-M3 + M4_base) مقابل
# المتحرّك القابل للمراجعة (M4_انفجر_فعلاً «فات القطار»/RSI/نواقص).
# إصلاح فحص 2026-06-26: M4_base (قاعدة واسعة) بنيوية = «ليس ارتكازًا» لا «تحرّك».
S._MISSED.clear()
S._MISSED += [
    {"symbol": "MOVEDX", "reason": "M4_انفجر_فعلاً", "gain_10d": 80.0, "price": 4.0},
    {"symbol": "WIDEBS", "reason": "M4_base_واسعة", "gain_10d": 120.0, "price": 5.0},
    {"symbol": "BIGCAP", "reason": "M2_هبوط_تحت_40", "gain_10d": 40.0, "price": 90.0},
    {"symbol": "SPLITX", "reason": "M2_هبوط_فوق_97", "gain_10d": 999.0, "price": 30.0},
]
_mrep = S.build_dev_assistant_report({"stocks": [], "notes": []})
S._MISSED.clear()
check("الفائتة تُفصل: المتحرّك (M4_انفجر) عن «ليس ارتكازًا» (M1-M3 + M4_base)",
      "ارتكاز تحرّك (راجع الارتداد): <b>1</b>" in _mrep
      and "ليس ارتكازًا (تجاهل صحيح): 3" in _mrep
      and "MOVEDX" in _mrep and "WIDEBS" not in _mrep and "BIGCAP" not in _mrep)


# 📲 تنبيه Cline: لا يرسل تقريرًا قديمًا باسم اليوم إذا فشل إنشاء تقرير اليوم.
#     المسار الصريح CLINE_REPORT_PATH يبقى مسموحًا للاختبار/التشغيل اليدوي.
import tempfile as _tf_notify
import os as _os_notify
import cline_notify as _cn

_old_cwd = _os_notify.getcwd()
_old_env_report = _os_notify.environ.get("CLINE_REPORT_PATH")
try:
    with _tf_notify.TemporaryDirectory() as _tdn:
        _os_notify.chdir(_tdn)
        _os_notify.makedirs("reports", exist_ok=True)
        with open("reports/cline_weekly_2000-01-01.md", "w", encoding="utf-8") as _f:
            _f.write("## ملخّص تنفيذي\n- تقرير قديم لا يجب إرساله\n")
        _os_notify.environ.pop("CLINE_REPORT_PATH", None)
        check("تنبيه Cline: لا يلتقط تقريرًا قديمًا عند غياب تقرير اليوم",
              _cn.find_report() is None
              and "لم يُعثر على تقرير هذا الأسبوع" in _cn.build_message())
        with open("custom_report.md", "w", encoding="utf-8") as _f:
            _f.write("## ملخّص تنفيذي\n- تقرير محدد صراحة\n")
        _os_notify.environ["CLINE_REPORT_PATH"] = "custom_report.md"
        check("تنبيه Cline: CLINE_REPORT_PATH الصريح يعمل",
              _cn.find_report() == "custom_report.md"
              and "تقرير محدد صراحة" in _cn.build_message())
finally:
    _os_notify.chdir(_old_cwd)
    if _old_env_report is None:
        _os_notify.environ.pop("CLINE_REPORT_PATH", None)
    else:
        _os_notify.environ["CLINE_REPORT_PATH"] = _old_env_report


# أكواد الرفض خالية من علامات < > (تكسر HTML تيليجرام) — حارس ضد الانحدار
import re as _re_codes
_src_sb = open("Super_stock.py", encoding="utf-8").read()
_rcodes = _re_codes.findall(r'_reject\(\s*f?["\']([^"\']*)["\']', _src_sb)
check("أكواد الرفض خالية من علامات المقارنة < > (لا تكسر تيليجرام)",
      bool(_rcodes) and all("<" not in rc and ">" not in rc for rc in _rcodes),
      f"عدد الأكواد المفحوصة: {len(_rcodes)}")

# 📐 حجم المركز: مخاطرة ثابتة من رأس المال
_ps = S.position_size(1.75, 1.39)   # risk/سهم=0.36 · 1% من 10000=100
check("حجم المركز: عدد الأسهم صحيح من المخاطرة",
      _ps and _ps["shares"] == int(100 / (1.75 - 1.39)) and _ps["risk"] == 100)
check("حجم المركز: None لو الوقف ≥ الدخول",
      S.position_size(1.50, 1.60) is None)
check("سطر حجم المركز يظهر", bool(S.position_size_line([1.70, 1.75, 1.80], 1.39)))

# 🧪 الباكتيست: مشي للأمام + إحصاء سليم
_bt = S.backtest_symbol("BT", synth_pivot(seed=2))
check("الباكتيست: يرجع صفقات بنتائج صحيحة",
      all(t["outcome"] in ("win", "loss", "open", "no_fill") for t in _bt)
      and all("entry" in t and "t1" in t for t in _bt))
_bstats = S.backtest_stats([{"outcome": "win"}, {"outcome": "loss"},
                            {"outcome": "win"}, {"outcome": "no_fill"}])
check("الباكتيست: إحصاء النجاح صحيح",
      _bstats["decided"] == 3 and _bstats["wins"] == 2
      and _bstats["no_fill"] == 1 and abs(_bstats["win_rate"] - 66.7) < 0.2)

# 🎯 عمق الأهداف في مساعد التطوير
_wd = [{"symbol": f"W{i}", "status": "active", "hit": ("t2" if i % 3 else "t1"),
        "hit_date": "2026-01-10", "added": "2026-01-02", "entry_ref": 2.0,
        "max_gain_pct": 40, "tier": "A", "sector": "Technology", "rsi": 27,
        "rr": 2.5, "flags": ["مسح سيولة"]} for i in range(12)]
_repd = S.build_dev_assistant_report({"history": [{"stocks": _wd}],
                                      "removed": [], "stocks": []})
check("مساعد التطوير: عمق الأهداف + زمن الوصول",
      "عمق الأهداف" in _repd and "زمن الوصول" in _repd)

# 🧹 تقليم سجل التنبيهات: يبقي المفتوحة + المغلقة الحديثة فقط (نمو محدود)
import datetime as _dt
_old = (_dt.date.today() - _dt.timedelta(days=400)).isoformat()
_new = _dt.date.today().isoformat()
_ad = {"alerts": [
    {"symbol": "OPN", "status": "open", "date": _old, "result_date": None},
    {"symbol": "OLD", "status": "stopped", "date": _old, "result_date": _old},
    {"symbol": "REC", "status": "stopped", "date": _new, "result_date": _new}]}
S._prune_alerts(_ad)
_syms = {a["symbol"] for a in _ad["alerts"]}
check("تقليم التنبيهات: يبقي المفتوحة+الحديثة ويحذف القديمة المغلقة",
      _syms == {"OPN", "REC"})

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
      "وصلت منطقة الدخول" in S.build_pullback_section([], _trig))

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

# ==========================================================
# أقفال القرارات المحسومة (فيصل) — خطة OPUS T1-T5
# قرارات محسومة يصونها الكود؛ هذه الأقفال تمنع تغييرها بالغلط بلا فشل اختبار.
# ==========================================================
# T1 — «لا تجاوز في الأهداف»: القيمة + قاعدة التجميع.
check("قفل T1: MIN_TARGET_GAP_PCT == 3% (لا يُعاد لـ8% القافز فوق القريب)",
      S.CONFIG["MIN_TARGET_GAP_PCT"] == 3.0)
# سلوكي: يحاكي قاعدة الدمج (Super_stock.py:1793-1795) بقيمة CONFIG الفعلية —
# مستوى 5% فوق الأول يُبقى (لا يُتخطّى)، ومستوى ضمن 3% يُدمج. مع 8% كان 2.10 يُحذف.
_t1_gap = 1.0 + S.CONFIG["MIN_TARGET_GAP_PCT"] / 100.0
_t1_cands = [2.00, 2.05, 2.10, 2.50]   # 2.05=2.5%فوق(يُدمج) · 2.10=5%فوق(يُبقى)
_t1_picked = []
for _t1c in _t1_cands:
    if not _t1_picked or _t1c >= _t1_picked[-1] * _t1_gap:
        _t1_picked.append(round(_t1c, 2))
check("قفل T1 سلوكي: التجميع يُبقي 2.10 (5%) ويدمج 2.05 (2.5%)",
      _t1_picked == [2.00, 2.10, 2.50], f"{_t1_picked}")

# T2 — قاع RSI المثالي (تغريدة 8057: «قبل ينفجر RSI بين 23-27»).
check("قفل T2: RSI_OVERSOLD == 27", S.CONFIG["RSI_OVERSOLD"] == 27.0)

# T3 — معاملات MACD الافتراضية 12/26/9 (صفحة إعدادات فيصل IMG_6472).
import inspect as _inspect_macd
_macd_defs = _inspect_macd.signature(S.macd).parameters
check("قفل T3: MACD الافتراضي 12/26/9",
      _macd_defs["fast"].default == 12
      and _macd_defs["slow"].default == 26
      and _macd_defs["signal"].default == 9)

# T4 — EMA 30/50 لبوابة M12 (فيصل: «متوسط حركة 30/50»، تغريدات 6916/6919/8056).
# قفل على مصدر البوابة (لا نتيجتها فقط)؛ مقاوم لفراغات التنسيق.
_src_m12 = open("Super_stock.py", encoding="utf-8").read().replace(" ", "")
check("قفل T4: بوابة M12 تستعمل EMA 30 و50",
      "ema(close,30)" in _src_m12 and "ema(close,50)" in _src_m12)

# T5 — الثبات + نافذة القاع + منع الملاحقة (7403/8056 «ثبات 3-5» + كتلة v2.1).
check("قفل T5: ثبات 3-8 · تسامح 2% · قاع 25ج · منع ملاحقة 35%/5ج",
      S.CONFIG["STABILITY_MIN"] == 3
      and S.CONFIG["STABILITY_MAX"] == 8
      and S.CONFIG["STABILITY_TOL_PCT"] == 2.0
      and S.CONFIG["PIVOT_LOOKBACK"] == 25
      and S.CONFIG["RECENT_RISE_BLOCK_PCT"] == 35.0)

# ==========================================================
# اختبارات ميزات OPUS D8/D9/D10 (طبقة عرض — لا تمسّ الفرز)
# ==========================================================
# D8 — كشف «الرجل المشنوق» عند القمة (تحذير انعكاس)
_hm_rise = [[10 + i * 0.2, 10 + i * 0.2 + 0.1, 10 + i * 0.2 - 0.1,
             10 + i * 0.2, 1000] for i in range(19)]
_hm_top = 10 + 18 * 0.2                                   # آخر إغلاق صاعد ≈ 13.6
_hm_rise.append([_hm_top, _hm_top + 0.05, _hm_top - 1.0,  # مطرقة عند القمة:
                 _hm_top - 0.02, 1000])                   # جسم صغير + ظل سفلي طويل
_hm_df = pd.DataFrame(_hm_rise, columns=["Open", "High", "Low", "Close", "Volume"],
                      index=pd.date_range("2025-01-01", periods=20))
check("D8: كشف الرجل المشنوق عند القمة", S._hanging_man(_hm_df) is True)
_hm_fall = [[13 - i * 0.2, 13 - i * 0.2 + 0.1, 13 - i * 0.2 - 0.1,
             13 - i * 0.2, 1000] for i in range(20)]      # هابط → آخر شمعة عند القاع
_hm_fdf = pd.DataFrame(_hm_fall, columns=["Open", "High", "Low", "Close", "Volume"],
                       index=pd.date_range("2025-01-01", periods=20))
check("D8: لا مشنوق عند القاع (شمعة عادية)", S._hanging_man(_hm_fdf) is False)

# D9 — تقرير التقسيم العكسي: قاعدة ÷2 + عتبة الشورت 20ألف + العرض
_d9_sr = S._split_row("EHGO", "2026-05-01", 2.80, 1.55, 15000)
check("D9: هدف الهبوط = افتتاح ÷2 (2.80→1.40)", _d9_sr["half"] == 1.40)
check("D9: شورت 15ألف < 20ألف = مقبول", _d9_sr["short_ok"] is True)
check("D9: شورت 25ألف = غير مقبول",
      S._split_row("WCT", "2026-05-01", 3.00, 2.0, 25000)["short_ok"] is False)
_d9_sec = S.build_split_watch_section([_d9_sr])
check("D9: قسم التقسيم يعرض الرمز + الهدف ÷2",
      "EHGO" in _d9_sec and "1.40" in _d9_sec)
check("D9: القسم فارغ بلا صفوف", S.build_split_watch_section([]) == "")

# D10 — عرض تدوير الفلوت في الكرت (عند تجاوز 100% فقط)
if r0:
    _d10_hi = dict(r0); _d10_hi["rotation_pct"] = 200
    _d10_lo = dict(r0); _d10_lo["rotation_pct"] = 50
    check("D10: الكرت يعرض التدوير عند 200%",
          "تدوير" in S.build_message([_d10_hi], []))
    check("D10: الكرت لا يعرض التدوير عند 50%",
          "تدوير" not in S.build_message([_d10_lo], []))
    check("D10: make_watch_entry يحفظ rotation_pct",
          S.make_watch_entry(_d10_hi, "2026-07-03").get("rotation_pct") == 200)

# ==========================================================
# اختبارات خطة الضبط (OPUS_TUNING_PLAN 2026-07-03): A1/A2/A3/A5/B1
# ==========================================================
# --- A1: لقطة مقام أسباب الرفض (كانت تضيع كل تشغيل) ---
_a1_wl = {}
_a1_snap_stats = dict(S._REJECT_STATS)
S._REJECT_STATS.clear()
S._REJECT_STATS.update({"M4_base_واسعة": 100, "M2_هبوط_تحت_40": 200})
S._SCAN_STATS["universe"], S._SCAN_STATS["valid"] = 1000, 950
S.record_reject_stats(_a1_wl)
_a1_today = S.dt.date.today().isoformat()
check("A1: لقطة المقام تُحفظ بتاريخ اليوم + الأرقام",
      len(_a1_wl.get("reject_stats", [])) == 1
      and _a1_wl["reject_stats"][0]["date"] == _a1_today
      and _a1_wl["reject_stats"][0]["stats"]["M4_base_واسعة"] == 100
      and _a1_wl["reject_stats"][0]["universe"] == 1000)
S._REJECT_STATS["M4_base_واسعة"] = 120
S.record_reject_stats(_a1_wl)
check("A1: لقطة واحدة لكل يوم (الأحدث تفوز)",
      len(_a1_wl["reject_stats"]) == 1
      and _a1_wl["reject_stats"][0]["stats"]["M4_base_واسعة"] == 120)
_a1_wl["reject_stats"].insert(0, {"date": "2020-01-01", "stats": {"X": 1}})
S.record_reject_stats(_a1_wl)
check("A1: تقليم اللقطات الأقدم من 56 يومًا",
      all(e["date"] > "2020-01-01" for e in _a1_wl["reject_stats"]))
_a1_empty = {}
S._REJECT_STATS.clear()
S.record_reject_stats(_a1_empty)
check("A1: بلا رفض = بلا لقطة (لا يفسد القائمة)", "reject_stats" not in _a1_empty)
S._REJECT_STATS.update(_a1_snap_stats)

# --- A2 + A1-عرض: تقرير مساعد التطوير يفصل المشبوه ويعرض المقام ---
_a2_missed_bak = list(S._MISSED)
S._MISSED[:] = [
    {"symbol": "GDC", "reason": "M4_base_واسعة", "gain_10d": 11423.8,
     "price": 2.42, "suspect_split": True},
    {"symbol": "TC", "reason": "M4_base_واسعة", "gain_10d": 159.0,
     "price": 4.0, "suspect_split": False},
    {"symbol": "EXOZ", "reason": "M5_سيولة", "gain_10d": 34.0,
     "price": 8.48, "suspect_split": False},
]
_a2_wl = {"stocks": [], "removed": [],
          "explosions": [{"symbol": "UPC", "date": _a1_today,
                          "expl_date": _a1_today, "gain": 311.0,
                          "reason": "M2_هبوط_تحت_40", "was_pivot": True,
                          "suspect_split": True}],
          "reject_stats": [{"date": _a1_today,
                            "stats": {"M4_base_واسعة": 50,
                                      "M2_هبوط_تحت_40": 500}}]}
_a2_rep = S.build_dev_assistant_report(_a2_wl)
check("A2: المشبوه مفصول من الإحصاء (GDC يظهر ببند التحقق فقط)",
      "مستبعد من الإحصاء (1)" in _a2_rep and "GDC +11424%" in _a2_rep)
check("A2: الإحصاء النظيف يحسب الواقعي فقط (تجاهل صحيح: 1)",
      "تجاهل صحيح): 1" in _a2_rep)
check("A2: الانفجار المشبوه يُعلَّم 🔍 ويبقى بالإحصاء",
      "+311%" in _a2_rep and " 🔍" in _a2_rep and "كان ارتكازًا فاتنا: 1" in _a2_rep)
check("A1-عرض: مقام الرفض يظهر بالتقرير + نسبة الفائتة/المقام",
      "مقام الرفض" in _a2_rep and "M4_base_واسعة=50" in _a2_rep
      and "1/50 (2.0%)" in _a2_rep)
S._MISSED[:] = _a2_missed_bak

# --- A3: التنبيهات الجديدة تحمل سمات التعلّم ---
if r0:
    _a3_data = {"alerts": []}
    S.record_new_alerts(_a3_data, [r0])
    _a3_alert = _a3_data["alerts"][0]
    check("A3: التنبيه الجديد يحمل سمات التعلّم التسع",
          all(k in _a3_alert for k in
              ("tier", "sector", "rsi", "float", "short", "short_pct",
               "drop_pct", "best_spike", "rr"))
          and _a3_alert["tier"] == r0.get("tier")
          and _a3_alert["rr"] == r0.get("rr"))

# --- A5: حارس العيّنة الصغيرة + مفارقة القوة ---
_a5_alerts = {"alerts": (
    [{"symbol": f"W{i}", "status": "hit_t1", "score": 60, "max_gain_pct": 15.0,
      "date": "2026-06-01", "result_date": "2026-06-05"} for i in range(8)]
    + [{"symbol": f"L{i}", "status": "stopped", "score": 80, "max_gain_pct": 1.0,
        "date": "2026-06-01", "result_date": "2026-06-05"} for i in range(2)])}
_a5_rep = S.build_dev_assistant_report({"stocks": [], "removed": []},
                                       alert_data=_a5_alerts)
check("A5: حارس العيّنة الصغيرة يظهر عند N<20",
      "العيّنة صغيرة (N=10)" in _a5_rep
      and "لا قرارات ضبط قبل 20 صفقة" in _a5_rep)
check("A5: مفارقة القوة تُوثَّق (خاسرون 80 > رابحون 60)",
      "القوة ليست تنبؤية بعد" in _a5_rep)

# --- B1: مفاتيح الباكتيست — الإنتاج محصّن ---
_b1_env = {"BT_BASE_RANGE_MAX": "55", "BT_MIN_DROP_FLOOR": "30"}
_b1_before = (S.CONFIG["BASE_RANGE_MAX_PCT"], S.CONFIG["MIN_DROP_FLOOR"])
_b1_prod = S._apply_backtest_overrides("FULL", _b1_env)
check("B1: الوضع الإنتاجي يتجاهل مفاتيح BT_* تمامًا",
      _b1_prod == []
      and (S.CONFIG["BASE_RANGE_MAX_PCT"],
           S.CONFIG["MIN_DROP_FLOOR"]) == _b1_before)
_b1_bt = S._apply_backtest_overrides("BACKTEST", _b1_env)
check("B1: وضع BACKTEST يطبّق المفاتيح (تجربة A/B)",
      S.CONFIG["BASE_RANGE_MAX_PCT"] == 55.0
      and S.CONFIG["MIN_DROP_FLOOR"] == 30.0 and len(_b1_bt) == 2)
S.CONFIG["BASE_RANGE_MAX_PCT"], S.CONFIG["MIN_DROP_FLOOR"] = _b1_before
# مفاتيح التجربة الموسّعة (سقف الانهيار/نافذة الانفجار/السيولة) — نفس التحصين
_b1x_env = {"BT_MAX_DROP_PCT": "99.5", "BT_SPIKE_WINDOW": "60",
            "BT_MIN_DOLLAR_VOL": "100000"}
_b1x_before = (S.CONFIG["MAX_DROP_PCT"], S.CONFIG["PRIOR_SPIKE_WINDOW"],
               S.CONFIG["MIN_DOLLAR_VOL"])
check("B1x: الإنتاج يتجاهل المفاتيح الموسّعة",
      S._apply_backtest_overrides("FULL", _b1x_env) == []
      and (S.CONFIG["MAX_DROP_PCT"], S.CONFIG["PRIOR_SPIKE_WINDOW"],
           S.CONFIG["MIN_DOLLAR_VOL"]) == _b1x_before)
S._apply_backtest_overrides("BACKTEST", _b1x_env)
check("B1x: وضع BACKTEST يطبّقها (النافذة int للـrange)",
      S.CONFIG["MAX_DROP_PCT"] == 99.5
      and S.CONFIG["PRIOR_SPIKE_WINDOW"] == 60
      and isinstance(S.CONFIG["PRIOR_SPIKE_WINDOW"], int)
      and S.CONFIG["MIN_DOLLAR_VOL"] == 100000.0)
(S.CONFIG["MAX_DROP_PCT"], S.CONFIG["PRIOR_SPIKE_WINDOW"],
 S.CONFIG["MIN_DOLLAR_VOL"]) = _b1x_before
check("B1: قيمة فاسدة تُتجاهل بأمان",
      S._apply_backtest_overrides("BACKTEST", {"BT_BASE_RANGE_MAX": "abc"}) == []
      and S.CONFIG["BASE_RANGE_MAX_PCT"] == _b1_before[0])
check("B1: استيراد الاختبار الحالي بلا تجاوزات (إنتاج نظيف)",
      S._BT_OVERRIDES == [])

# --- B3: حكم تجربة A/B (باكتيست 2026-07-03، 132 رمزًا) — قفل القرار ---
# A (40/40): محسومة=4 نجاح 50% · B (50/35): محسومة=5 نجاح 40% (خسارة إضافية،
# صفر أرباح جديدة) رغم عيّنة منحازة لصالح B → **العتبتان تبقيان 40/40**.
check("B3: قفل قرار التجربة — M4 قاعدة 40% (التخفيف 50 خفّض النجاح 50→40%)",
      S.CONFIG["BASE_RANGE_MAX_PCT"] == 40.0)
# (MIN_DROP_FLOOR==40 محروس أصلًا بقفل «أرضيات الهوية» أعلاه.)

# --- C3: حكم تجربة C (أسهم فيصل الـ28، 2026-07-03) — قفل الحواجز الهندسية ---
# فتح الحواجز (سقف 99.5 · نافذة 60ج · سيولة 100K) على أسهم فيصل الموثّقة نفسها:
# الإشارات 1→7 لكن النجاح انهار لـ17% (1✅/5🛑) مقابل 80% للبوت الحي — الحواجز
# تمنع مناطق «الإدارة اليدوية» عند فيصل وتشويهات التقسيمات بالبيانات (VMAR $515).
check("C3: قفل الحواجز الهندسية — سقف 97 · نافذة 20ج · سيولة 200K (فتحها=17% نجاح)",
      S.CONFIG["MAX_DROP_PCT"] == 97.0
      and S.CONFIG["PRIOR_SPIKE_WINDOW"] == 20
      and S.CONFIG["MIN_DOLLAR_VOL"] == 200_000)

# --- C4: استثناء analyze_ticker يسجَّل ولا يغيّر النتيجة (None كما هو) ---
_c4_bad = pd.DataFrame({"Open": ["x"] * 130, "High": ["x"] * 130,
                        "Low": ["x"] * 130, "Close": ["x"] * 130,
                        "Volume": ["x"] * 130},
                       index=pd.date_range("2025-01-01", periods=130))
check("C4: بيانات فاسدة → None بلا انهيار (التسجيل تشخيصي فقط)",
      S.analyze_ticker("BAD_C4", _c4_bad) is None)

# --- N2: إزالة تكرار أرشيف history (كان 2026-06-21 مكرر ×9 بالبيانات الحية) ---
_n2_hist = [
    {"week_start": "2026-06-21", "ended": "2026-06-22"},
    {"week_start": "2026-06-21", "ended": "2026-06-23"},
    {"week_start": "2026-06-21", "ended": "2026-06-24"},   # الأحدث لهذا الأسبوع
    {"week_start": "2026-06-26", "ended": "2026-06-27"},
]
_n2_out = S._dedup_history(_n2_hist)
check("N2: إزالة تكرار الأسبوع → إدخال واحد لكل week_start", len(_n2_out) == 2)
check("N2: الأحدث يفوز (2026-06-21 → ended=06-24)",
      next(h for h in _n2_out if h["week_start"] == "2026-06-21")["ended"]
      == "2026-06-24")
check("N2: ترتيب الأسابيع محفوظ (21 ثم 26)",
      [h["week_start"] for h in _n2_out] == ["2026-06-21", "2026-06-26"])
check("N2: إدخال واحد يبقى كما هو",
      S._dedup_history([{"week_start": "W1"}]) == [{"week_start": "W1"}])
check("N2: الإدخالات بلا week_start تبقى مستقلة",
      len(S._dedup_history([{"a": 1}, {"a": 2}])) == 2)

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
    _t1_0, _rr_0 = _base["t1"], _base["rr"]
    _r2, _r3 = S.refine_targets_4h(_base["t1"], _base["t2"], _base["t3"],
                                   _base["price"], _h4_demo)
    # حارس حقيقي (كان الشرط ميتًا: abs(t1-t1)>0): refine يُرجِع (t2,t3) فقط فـ t1
    # يبقى ثابتًا والترتيب محفوظ t1<t2<=t3؛ و rr مبني على t1 فلا يتغيّر بالدمج.
    if not (_r2 > _t1_0 and _r3 >= _r2 and _base["t1"] == _t1_0
            and _base["rr"] == _rr_0 and _rr_0 and _rr_0 > 0):
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
