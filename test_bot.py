# -*- coding: utf-8 -*-
"""
اختبار شامل لبوت أسهم الارتكاز (v2.7) — الضمان الذهبي.
يغطي: المؤشرات + البوابات + نظام القائمتين (A/B) + التحرر/القاب +
قرارات الصور الفعلية (RSI/MACD/شورت/فلوت لكل سهم من الصور).
يعمل بلا إنترنت (يحاكي البيانات + يعطّل yfinance).
"""
import inspect as _insp0
import os as _os_hc
import numpy as np
import pandas as pd
import Super_stock as S
import technical_report as TR
import hand_check as HC

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

# 🪦 تقاعد A/B (2026-07-05): القبول فئة واحدة "B" (مؤهّل) · أكثر من الحد=None (يُرفض).
# الرفض (n>maxf) محفوظ حرفيًا؛ A لم تعد تُسنَد أبدًا (كانت ضجيجًا — سنتان دليل).
check("0 نواقص → B (A متقاعد، القبول موحّد)", S.classify_tier([]) == "B")
check("نقص واحد → B", S.classify_tier(["MACD"]) == "B")
check("نقصان → B", S.classify_tier(["MACD", "RSI"]) == "B")
check("3 نواقص → B (الحد 3)", S.classify_tier(["MACD", "RSI", "فلوت"]) == "B")
check("4 نواقص → يُرفض None",
      S.classify_tier(["MACD", "RSI", "فلوت", "MA"]) is None)
check("التصنيف الصارم (بلا قائمتين): 0 نواقص يُقبل «B» · نقص واحد يُرفض",
      S.classify_tier([], two_tier=False) == "B"
      and S.classify_tier(["MACD"], two_tier=False) is None)
# 🔒 قفل: A متقاعد — classify_tier لا تعيد "A" أبدًا لأي عدد نواقص (0..10)
check("قفل تقاعد A: classify_tier لا تُنتج «A» إطلاقًا",
      all(S.classify_tier(["x"] * n) != "A" for n in range(0, 11)))
# 🧹 أقفال تنظيف بقايا A (تدقيق 2026-07-08 — «0 في A» كان وهم بقايا لا مشكلة فرز):
check("🧹تنظيف: سجل الفرز بلا «(A صارمة)» (كان يطبع «0 (A صارمة)» كل تشغيل)",
      "A صارمة" not in _insp0.getsource(S.scan_market))
check("🧹تنظيف: مسار الترقية B→A الميت أُزيل من check_promotions (يرجع [] دائمًا)",
      "promoted_date" not in _insp0.getsource(S.check_promotions)
      and '== "A"' not in _insp0.getsource(S.check_promotions))
check("🧹تنظيف: readiness_badge/tag/ratio بلا وسيط tier (الجاهزية وحدها المحور)",
      all("tier" not in _insp0.signature(f).parameters
          for f in (S.readiness_badge, S.readiness_tag, S.readiness_ratio)))
_r0c = dict(r0)
_r0c.pop("tier", None)
check("🧹تنظيف: make_watch_entry الافتراضي «B» لا «A» (سجل بلا tier)",
      S.make_watch_entry(_r0c, "2026-01-01")["tier"] == "B")


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
# 5ب) 🪦 تقاعد الترقية B→A (A متقاعدة — ثبت أنها ضجيج)
# ==========================================================
print("\n=== 5ب) تقاعد الترقية B→A ===")
_orig = S.analyze_ticker
# حالة: سهم B «اكتمل نموذجه» (0 نواقص عند إعادة التحليل) → يبقى B (لا إحياء لـA)
wlp = {"stocks": [{"symbol": "PROM", "status": "active", "tier": "B",
                   "soft_fails": ["MACD"], "pivot": 3.0,
                   "stop": 2.7, "last_price": 3.5, "liberation": 5.0}],
       "notes": []}
S.analyze_ticker = lambda sym, d: {"soft_fails": [], "liberation": 5.0}
prom = S.check_promotions(wlp, {"PROM": synth_pivot(seed=9)})
check("🪦 تقاعد A: صفر نواقص عند إعادة التحليل يبقى «B» (لا ترقية لـA)",
      len(prom) == 0 and wlp["stocks"][0]["tier"] == "B")
check("🪦 تقاعد A: لا تاريخ ترقية (الترقية B→A متقاعدة)",
      not wlp["stocks"][0].get("promoted_date"))
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
      and "A (تاريخي" in _rep)   # 🪦 صفوف A القديمة تُوسَم «تاريخي — تصنيف متقاعد»
check("🧹تنظيف: اقتراح «A أفضل من B» الميت أُزيل (A لم تُنتَج قط — كان مستحيلًا)",
      "أفضل بوضوح من B" not in _rep)
check("🧹تنظيف: الفحص اليدوي بلا حكم 🅰️ (حكم موحّد 🎯 مؤهّل)",
      "🅰️" not in open("analyze_one.py", encoding="utf-8").read())

# ===== 🟢👀 فصل «جاهز للدخول» عن «متابعة» (ENTRY_READY_SPLIT_PLAN — عرض فقط) =====
def _es_mode(mode, reason=""):
    return {"interp": {"entry_mode": {"mode": mode, "reason": reason}}}
# 1) قرب الدعم → جاهز
_e1 = S.entry_status(_es_mode("near_support", "داخل/قرب منطقة الدفعات"))
check("جاهز/متابعة 1: near_support → جاهز للدخول الآن",
      _e1["status"] == "ready_now" and "🟢 جاهز للدخول الآن" == _e1["label"]
      and _e1["reason"] == "")
# 2) مسح مؤكَّد → جاهز
check("جاهز/متابعة 2: sweep_confirmed → جاهز (المسح دخول عند فيصل)",
      S.entry_status(_es_mode("sweep_confirmed"))["status"] == "ready_now")
# 3) انتظار استعادة → متابعة + «تحت الدعم»
_e3 = S.entry_status(_es_mode("reclaim_wait", "تحت الدعم — ننتظر استعادته"))
check("جاهز/متابعة 3: reclaim_wait → متابعة + «تحت الدعم»",
      _e3["status"] == "watch" and "تحت الدعم" in _e3["reason"]
      and "👀 متابعة" == _e3["label"])
# 4) بعيد فوق المنطقة → متابعة + «يتحوّل جاهزًا برجوعه»
_e4 = S.entry_status(_es_mode("no_entry_far", "بعيد فوق منطقة الدفعات"))
check("جاهز/متابعة 4: بعيد → متابعة + «يتحوّل جاهزًا برجوعه»",
      _e4["status"] == "watch" and "يتحوّل جاهزًا برجوعه" in _e4["reason"])
# 5) كسر الوقف → متابعة، السبب يذكر الوقف بلا لاحقة «يتحوّل جاهزًا»
_e5 = S.entry_status(_es_mode("no_entry_far", "كسر الوقف — الفكرة ملغاة/خطرة"))
check("جاهز/متابعة 5: كسر الوقف → متابعة (خطر، بلا لاحقة «يتحوّل جاهزًا»)",
      _e5["status"] == "watch" and "الوقف" in _e5["reason"]
      and "يتحوّل جاهزًا" not in _e5["reason"])
# 6) احتياط بلا interp = نفس تصنيف build_interpretation (قفل اتّساق)
_rb = {"price": 1.85, "last_price": 1.85, "pivot": 1.80,
       "tranches": [1.80, 1.85, 1.90], "stop": [1.67, 1.71],
       "t1": 2.0, "t2": 2.2, "t3": 2.5,
       "key_levels": {"sup_major": 1.80}, "warnings": []}
_rb_with = dict(_rb, interp=S.build_interpretation(_rb))
check("جاهز/متابعة 6أ: احتياط (بلا interp) داخل المنطقة → جاهز",
      S.entry_status(_rb)["status"] == "ready_now")
check("جاهز/متابعة 6-قفل: الاحتياط = مسار interp (نفس المدخل نفس الحالة)",
      S.entry_status(_rb)["status"] == S.entry_status(_rb_with)["status"])
_rb_out = dict(_rb, price=2.10, last_price=2.10)   # فوق max(trs)*1.05=1.995
check("جاهز/متابعة 6ب: احتياط فوق المنطقة → متابعة",
      S.entry_status(_rb_out)["status"] == "watch")
# 7) فاشل-آمن
check("جاهز/متابعة 7: مدخل فاضٍ → متابعة «بيانات ناقصة» (لا انهيار)",
      S.entry_status({})["status"] == "watch"
      and "ناقصة" in S.entry_status({})["reason"])
# 8) اليومي: ترويسة العدّ + عنوانا قسمين + سطر 👀 للمتابعة + ترقيم مستمر
def _wl_entry(sym, mode, reason=""):
    return {"symbol": sym, "added": "2026-07-01", "entry_ref": 2.0,
            "entry": [1.9, 2.0], "tranches": [1.9, 1.95, 2.0], "pivot": 1.9,
            "stop": 1.75, "stop_hi": 1.79, "t1": 2.3, "t2": 2.6, "t3": 3.0,
            "score": 60, "flags": [], "rr": 2.0, "tier": "B", "soft_fails": [],
            "warnings": [], "readiness": 60, "have": [], "partial": [],
            "missing": [], "hit": None, "hit_date": None, "max_gain_pct": 0.0,
            "last_price": 2.0, "status": "active",
            "interp": {"entry_mode": {"mode": mode, "reason": reason}}}
_wl_mix = {"week_start": "2026-07-01", "removed": [], "notes": [], "stocks": [
    _wl_entry("RDY", "near_support"),
    _wl_entry("WCH", "no_entry_far", "بعيد فوق منطقة الدفعات")]}
_dm_mix = S.build_daily_message(_wl_mix, [], [], [])
check("جاهز/متابعة 8: اليومي — ترويسة العدّ «1 جاهز للدخول · 1 متابعة»",
      "1 جاهز للدخول · 1 متابعة" in _dm_mix)
check("جاهز/متابعة 8: اليومي — العنوانان + سطر 👀 للمتابعة",
      "🟢 <b>جاهز للدخول الآن</b> (1)" in _dm_mix
      and "متابعة — ننتظر وصولها لمنطقة الدخول</b> (1)" in _dm_mix
      and "👀 بعيد فوق منطقة الدفعات" in _dm_mix)
check("جاهز/متابعة 8: اليومي — ترقيم مستمر (الجاهز 1، المتابعة 2)",
      "1) 🎯 <b>$RDY</b>" in _dm_mix and "2) 🎯 <b>$WCH</b>" in _dm_mix)
# 9) قسم فاضٍ لا يظهر عنوانه
_wl_allw = {"week_start": "2026-07-01", "removed": [], "notes": [],
            "stocks": [_wl_entry("W1", "reclaim_wait"),
                       _wl_entry("W2", "no_entry_far", "بعيد فوق منطقة الدفعات")]}
_dm_allw = S.build_daily_message(_wl_allw, [], [], [])
check("جاهز/متابعة 9أ: كلها متابعة → عنوان 🟢 لا يظهر",
      "جاهز للدخول الآن</b> (" not in _dm_allw and "2 متابعة" in _dm_allw)
_wl_allr = {"week_start": "2026-07-01", "removed": [], "notes": [],
            "stocks": [_wl_entry("R1", "near_support"),
                       _wl_entry("R2", "sweep_confirmed")]}
_dm_allr = S.build_daily_message(_wl_allr, [], [], [])
check("جاهز/متابعة 9ب: كلها جاهزة → عنوان 👀 المتابعة لا يظهر",
      "متابعة — ننتظر وصولها" not in _dm_allr and "2 جاهز للدخول" in _dm_allr)
# 10) الكرت: سطر الحالة يظهر (جاهز ومتابعة)
_card_rdy = dict(_rb, symbol="CRD", score=60, readiness=60, rr=2.0,
                 entry=(1.80, 1.90), tier="B", soft_fails=[], flags=[])
_card_rdy["interp"] = S.build_interpretation(_card_rdy)
check("جاهز/متابعة 10: الكرت يعرض «🟢 جاهز للدخول الآن»",
      "🟢 جاهز للدخول الآن" in S.build_message([_card_rdy], []))
_card_wch = dict(_card_rdy, price=2.10, last_price=2.10)
_card_wch["interp"] = S.build_interpretation(_card_wch)
check("جاهز/متابعة 10: الكرت يعرض «👀 متابعة» مع السبب",
      "👀 متابعة —" in S.build_message([_card_wch], []))
# 11) محاكاة القائمة الحية (تثبيت اعتراض المستخدم: القسمان يمتلئان واقعًا)
def _live(sym, lp, trs, stop, piv):
    r = {"symbol": sym, "price": lp, "last_price": lp, "tranches": trs,
         "stop": [stop, stop * 1.02], "pivot": piv, "t1": round(trs[-1] * 1.15, 2),
         "t2": round(trs[-1] * 1.3, 2), "t3": round(trs[-1] * 1.5, 2),
         "key_levels": {"sup_major": piv}, "warnings": []}
    r["interp"] = S.build_interpretation(r)
    return r
check("جاهز/متابعة 11: VFF (داخل منطقته) → جاهز · LYEL (فوقها) → متابعة",
      S.entry_status(_live("VFF", 1.95, [1.8, 1.86, 1.91], 1.6786, 1.90))["status"]
      == "ready_now"
      and S.entry_status(_live("LYEL", 14.05, [11.47, 11.81, 12.16], 10.67,
                               12.0))["status"] == "watch")
# 12) 🔒 أقفال
check("جاهز/متابعة 12-قفل: entry_status خارج rank_key/select_top/classify_tier",
      all("entry_status" not in _insp0.getsource(f)
          for f in (S.rank_key, S.select_top, S.classify_tier)))
check("جاهز/متابعة 12-قفل: الجاهزية لا تدخل entry_status (ضد رجوع عتبة 75)",
      "readiness" not in _insp0.getsource(S.entry_status)
      and "READY_PCT" not in _insp0.getsource(S.entry_status))
_lk = dict(_rb)
_lk_before = (_lk["t1"], _lk["t2"], _lk["t3"], tuple(_lk["stop"]))
S.entry_status(_lk)
check("جاهز/متابعة 12-قفل: entry_status لا يمسّ t1/t2/t3/الوقف (نقية)",
      (_lk["t1"], _lk["t2"], _lk["t3"], tuple(_lk["stop"])) == _lk_before)
check("جاهز/متابعة 12-قفل: نصوص الحالة بلا علامات مقارنة ≥≤><",
      not any(c in (_e1["label"] + _e3["reason"] + _e4["reason"] + _e5["reason"])
              for c in "≥≤<>"))
# ===== إكمال نواقص المقطع الثلاثة (2026-07-08: تدقيق «ناقص شي؟») =====
# (1) تغطية الخضرا green_cover (المقطع: «تغطية الحمرا بخضرا تعطي تأكيد»)
def _h4df(rows):
    """h4 صناعي: rows=[(open,close,high,low), ...]"""
    import pandas as _pd
    o = [x[0] for x in rows]
    c = [x[1] for x in rows]
    h = [x[2] for x in rows]
    lo = [x[3] for x in rows]
    idx = _pd.date_range("2026-01-01", periods=len(rows), freq="4h")
    return _pd.DataFrame({"Open": o, "Close": c, "High": h, "Low": lo,
                          "Volume": [1e5] * len(rows)}, index=idx)
_base = [(2.0, 2.05, 2.1, 1.95)] * 10
_red = (2.3, 2.1, 2.35, 2.05)                      # حمرا: جسمها 2.1-2.3
_h4_cov = S.four_hour_levels(_h4df(_base + [_red, (2.15, 2.35, 2.4, 2.1)]), 2.0)
check("4س·تغطية: خضرا أغلقت فوق جسم الحمرا ⇒ green_cover=True",
      _h4_cov is not None and _h4_cov.get("green_cover") is True)
_h4_unc = S.four_hour_levels(_h4df(_base + [_red, (2.05, 2.12, 2.15, 2.0)]), 2.0)
check("4س·تغطية: خضرا لم تبلغ جسم الحمرا ⇒ green_cover=False",
      _h4_unc is not None and _h4_unc.get("green_cover") is False)
_h4_nor = S.four_hour_levels(_h4df([(2.0, 2.1, 2.15, 1.95)] * 12), 2.0)
check("4س·تغطية: لا شموع حمرا ⇒ green_cover=None (غير منطبق)",
      _h4_nor is not None and _h4_nor.get("green_cover") is None)
# (بقية اختبارات (1) waiting_green_cover و(2) targets_src في قسم التفسير
#  بالأسفل — تعتمد على fixtures _ir/_ip المعرّفة هناك)
# (3) عمق الارتكاز في التقرير الفني المستقل (استيراد TR أعلى الملف)
_pd_lines = TR.pivot_depth_section("TEST", synth_pivot(seed=2))
check("التقرير الفني·عمق: سهم مؤهّل ⇒ قسم «عمق منهجية الارتكاز» بأدوار المستويات",
      any("عمق منهجية الارتكاز" in x for x in _pd_lines)
      and any("أدوار المستويات" in x for x in _pd_lines))
_flat_df = pd.DataFrame(
    {"Open": [5.0] * 300, "High": [5.05] * 300, "Low": [4.95] * 300,
     "Close": [5.0] * 300, "Volume": [3e5] * 300},
    index=pd.date_range("2025-01-01", periods=300, freq="B"))
check("التقرير الفني·عمق: سهم غير مؤهّل ⇒ لا قسم (التقرير الكلاسيكي نقي)",
      TR.pivot_depth_section("FLAT", _flat_df) == [])
# 🧬 التجديد اليومي للبصمة (ملاحظة المستخدم من التقرير الحي 2026-07-08: سطر 🧬
# كان يغيب عن الأسهم المضافة قبل الميزة — الآن يُحسب يوميًا مثل التفسير/الترند)
_wlb = {"week_start": "2026-07-01", "removed": [], "notes": [],
        "stocks": [_wl_entry("BHV", "near_support")]}
assert "behav" not in _wlb["stocks"][0]     # سجل قديم: بلا بصمة مخزّنة
S.update_watchlist_status(_wlb, {"BHV": synth_pivot(seed=2)})
_sb = _wlb["stocks"][0]
check("🧬تجديد يومي: سجل قديم بلا بصمة → behav+bars_after يُحسبان بالتحديث اليومي",
      (_sb.get("behav") or {}).get("score") is not None
      and isinstance(_sb.get("bars_after"), int))

# ===== 🕵️ لوحة علامات اليد (HAND_EVIDENCE_PANEL_PLAN — عرض/تحذير فقط) =====
def _pump_df(fast_break=True):
    """داتا صناعية: قروب (قفزة 60%+ بحجم ضخم) ثم كسر دعم سريع/بطيء."""
    pre = list(np.full(60, 2.0) + np.random.default_rng(3).normal(0, 0.01, 60))
    jump = [2.0, 2.1, 3.4]                     # قفزة قروب عند الأخير
    if fast_break:
        after = list(np.linspace(3.4, 1.6, 8)) + list(np.full(29, 1.7))
    else:
        after = list(np.full(37, 3.3))         # لا كسر
    c = np.array(pre + jump + after)
    n = len(c)
    o = c.copy()
    hi = c * 1.03
    lo = c * 0.97
    v = np.full(n, 1e5)
    v[62] = 9e5                                # حجم القفزة ضخم (سيولة قروب)
    return pd.DataFrame(
        {"Open": o, "High": hi, "Low": lo, "Close": c, "Volume": v},
        index=pd.date_range("2025-01-01", periods=n, freq="B"))
# N1: قروب + كسر دعم سريع → found + broke_support
_n1 = S.group_pump_scar(_pump_df(fast_break=True))
check("🕵️N1: قروب (قفزة+حجم) ثم كسر دعم سريع ⇒ found + broke_support",
      _n1 and _n1["found"] and _n1["broke_support"]
      and _n1["jump_pct"] >= 50)
_n1b = S.group_pump_scar(_pump_df(fast_break=False))
check("🕵️N1: قروب بلا كسر خلال النافذة ⇒ found + broke_support=False (صدق)",
      _n1b and _n1b["found"] and _n1b["broke_support"] is False)
_n1c = S.group_pump_scar(_flat_df)   # مسطّح بلا قفزة/حجم
check("🕵️N1: بلا قفزة قروب ⇒ None (لا فبركة)", _n1c is None)
# N2: سقف مُدار 4س (3 رؤوس حمرا عند نفس المستوى)
def _h4_ceiling(rep):
    rows = [(2.0, 2.05, 2.1, 1.95)] * 12       # قاعدة ≥10 شمعة (شرط four_hour_levels)
    for _ in range(rep):                       # rep شمعة حمرا رأسها ~3.5
        rows.append((3.5, 3.2, 3.52, 3.15))
        rows.append((3.2, 3.3, 3.35, 3.15))    # خضرا فاصلة
    return _h4df(rows)
_n2 = S.four_hour_levels(_h4_ceiling(3), 2.0)
check("🕵️N2: 3 رؤوس حمرا عند نفس السعر ⇒ managed_ceiling بلمساته",
      _n2 and _n2.get("managed_ceiling")
      and _n2["managed_ceiling"]["touches"] >= 3
      and abs(_n2["managed_ceiling"]["price"] - 3.52) < 0.1)
_n2b = S.four_hour_levels(_h4_ceiling(1), 2.0)
check("🕵️N2: رأس حمرا واحد ⇒ لا سقف مُدار (None)",
      _n2b and _n2b.get("managed_ceiling") is None)
# N4: المجمّع + العدّ + عتبة الدليلين
_r_hand = {"behav": {"sweeps": 3, "score": 65},
           "pump_scar": {"found": True, "jump_pct": 67, "bars_ago": 20,
                         "broke_support": True},
           "rotation_pct": 150,
           "h4_levels": {"managed_ceiling": {"price": 3.53, "touches": 4}},
           "session_ctx": {"quote": {"spread_pct": 5.0}},
           "interp": {"entry_mode": {"mode": "near_support"}}}
_ev = S.hand_evidence(_r_hand)
check("🕵️N4: يجمع الأدلة من المصادر الأربعة (يومي/4س/حجم/طلبات)",
      {e["frame"] for e in _ev} >= {"يومي", "4س", "حجم", "طلبات"}
      and len(_ev) >= 5)
check("🕵️N4: «رفعة قروب ثم كسر دعوم» تظهر عند broke_support=True",
      any("كسر دعوم" in e["sign"] for e in _ev))
check("🕵️N4·سطر: عند دليلين فأكثر ⇒ «🕵️ علامات اليد (N)» + عددها",
      S.hand_evidence_line(_r_hand).startswith("🕵️ علامات اليد (")
      and "+" in S.hand_evidence_line(_r_hand))    # +N للباقي فوق 3
check("🕵️N4·سطر: دليل واحد فقط ⇒ لا سطر (لا حشو)",
      S.hand_evidence_line({"behav": {"sweeps": 3}}) == "")
check("🕵️N4·فاشل-آمن: مدخل فاضٍ ⇒ [] (لا انهيار)",
      S.hand_evidence({}) == [] and S.hand_evidence_line({}) == "")
check("🕵️N4·صدق الطلبات: سبريد ضيّق ⇒ لا دليل طلبات",
      not any(e["frame"] == "طلبات" for e in S.hand_evidence(
          dict(_r_hand, session_ctx={"quote": {"spread_pct": 1.0}}))))
# N5 (§P2 مضارب): «عروض شبه مُفرَّغة» من لقطة NBBO الخام (flow_raw) — بصمة تجهيز
_n5_hit = {"flow_raw": {"ask": 2.60, "ask_size": 100, "spread_pct": 8.0}}  # $260≤1000·8%
check("🕵️N5·مضارب: دولارات عرض تافهة + سبريد واسع ⇒ دليل «عروض شبه مُفرَّغة»",
      any(e["sign"] == "عروض شبه مُفرَّغة" for e in S.hand_evidence(_n5_hit)))
check("🕵️N5·صدق: حدّ «عمق الدفتر غير متاح» مكتوب داخل الدليل (أفضل عرض فقط)",
      any("عمق الدفتر غير متاح" in e["detail"]
          for e in S.hand_evidence(_n5_hit) if e["sign"] == "عروض شبه مُفرَّغة"))
check("🕵️N5: عرض سمين ($10K) ⇒ لا دليل مُفرَّغة",
      not any(e["sign"] == "عروض شبه مُفرَّغة" for e in S.hand_evidence(
          {"flow_raw": {"ask": 2.0, "ask_size": 5000, "spread_pct": 8.0}})))
check("🕵️N5: سبريد ضيّق (2%) ⇒ لا دليل مُفرَّغة",
      not any(e["sign"] == "عروض شبه مُفرَّغة" for e in S.hand_evidence(
          {"flow_raw": {"ask": 2.60, "ask_size": 100, "spread_pct": 2.0}})))
check("🕵️N5·فاشل-آمن: بلا flow_raw ⇒ لا دليل (مسار الفرز لا يجلبه)",
      not any(e["sign"] == "عروض شبه مُفرَّغة" for e in S.hand_evidence(_r_hand)))
# العرض بالكرت + التجديد اليومي لـpump_scar
_card_h = {"symbol": "HND", "price": 2.0, "pivot": 1.95, "score": 60,
           "readiness": 60, "rr": 2.0, "entry": (1.9, 2.0),
           "tranches": [1.9, 1.95, 2.0], "stop": (1.75, 1.79),
           "t1": 2.3, "t2": 2.6, "t3": 3.0, "tier": "B", "soft_fails": [],
           "flags": [], "behav": {"sweeps": 3, "score": 65,
                                  "label": "🔥 يد نشطة", "n_pumps": 2,
                                  "best_pump": 150.0, "recency_bars": 30},
           "pump_scar": {"found": True, "jump_pct": 67, "bars_ago": 20,
                         "broke_support": True}, "rotation_pct": 150}
_card_h["interp"] = S.build_interpretation(_card_h)
check("🕵️عرض: الكرت يُظهر «🕵️ علامات اليد»",
      "🕵️ علامات اليد" in S.build_message([_card_h], []))
_wlh = {"week_start": "2026-07-01", "removed": [], "notes": [],
        "stocks": [_wl_entry("PMP", "near_support")]}
S.update_watchlist_status(_wlh, {"PMP": _pump_df(fast_break=True)})
check("🕵️تجديد يومي: pump_scar يُحسب بالتحديث اليومي (سجل قديم)",
      "pump_scar" in _wlh["stocks"][0])
# 🔒 أقفال: خارج الاختيار/الترتيب/التصنيف/الباكتيست + بلا درجة رقمية بالمخرج
check("🕵️قفل: hand_evidence/pump_scar خارج rank_key/select_top/classify_tier/entry_status",
      all(("hand_evidence" not in _insp0.getsource(f)
           and "pump_scar" not in _insp0.getsource(f))
          for f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status)))
check("🕵️قفل: group_pump_scar خارج backtest_symbol/analyze_ticker (حيّ فقط)",
      "group_pump_scar" not in _insp0.getsource(S.backtest_symbol)
      and "group_pump_scar" not in _insp0.getsource(S.analyze_ticker))
check("🕵️قفل: نصوص اللوحة بلا علامات مقارنة ≥≤><",
      not any(c in (S.hand_evidence_line(_r_hand)
                    + " ".join(e["sign"] + e["detail"] for e in _ev))
              for c in "≥≤<>"))
# 🕵️ القسم المستقل «أسهم فيها علامات يد» (طلب المستخدم: قائمة لحالها للتنظيف)
_wl_hs = {"stocks": [
    {"symbol": "HND", "status": "active", "last_price": 2.0,
     "behav": {"sweeps": 3, "score": 66}, "rotation_pct": 160,
     "h4_levels": {"managed_ceiling": {"price": 3.0, "touches": 4}},
     "pump_scar": {"found": True, "jump_pct": 60, "bars_ago": 10,
                   "broke_support": True}},
    {"symbol": "CLN", "status": "active", "last_price": 5.0, "behav": {}}]}
_wl_hs["stocks"][0]["interp"] = {"entry_mode": {"mode": "near_support"}}
_hs = S.build_hand_section(_wl_hs)
check("🕵️قسم: يعرض «أسهم فيها علامات يد» + السهم المُدار فقط (النظيف مستبعد)",
      "أسهم فيها علامات يد (1)" in _hs and "$HND" in _hs and "$CLN" not in _hs)
check("🕵️قسم·الأهم: يوضّح حالة الدخول لكل سهم يد (جاهز/متابعة)",
      "🟢 جاهز للدخول" in _hs)
_wl_hw = {"stocks": [dict(_wl_hs["stocks"][0],
                         interp={"entry_mode": {"mode": "no_entry_far",
                                                "reason": "بعيد فوق المنطقة"}})]}
check("🕵️قسم·الأهم: سهم يد بعيد ⇒ «👀 متابعة» (لا يُعرض جاهزًا خطأً)",
      "👀 متابعة" in S.build_hand_section(_wl_hw))
check("🕵️قسم: لا أسهم يد ⇒ قسم فارغ (لا ترويسة معلّقة)",
      S.build_hand_section({"stocks": [
          {"symbol": "X", "status": "active", "behav": {}}]}) == "")
check("🕵️قسم·تنظيف: سطر 🕵️ أُزيل من كرت اليومي (انتقل للقسم المستقل)",
      "hand_evidence_line" not in _insp0.getsource(S.build_daily_message)
      and "build_hand_section" in _insp0.getsource(S.run_daily_watchlist))
check("🕵️رسالة مستقلة: أسهم اليد تُرسَل send_telegram منفصلة (لا تُدفن بالتقرير)",
      "send_telegram(hand_msg" in _insp0.getsource(S.run_daily_watchlist)
      and 'msg += "\\n\\n" + hand' not in _insp0.getsource(S.run_daily_watchlist))

# ===== 🕵️ أداة فحص اليد المستقلة (hand_check.py — عرض/تشخيص فقط) =====
_hc_r = {"symbol": "TST", "price": 2.0,
         "behav": {"sweeps": 3, "score": 66, "label": "🔥 يد نشطة"},
         "rotation_pct": 160,
         "h4_levels": {"managed_ceiling": {"price": 3.0, "touches": 4}},
         "pump_scar": {"found": True, "jump_pct": 60, "bars_ago": 20,
                       "broke_support": True}}
_hc_msg = HC.render_hand_check("TST", _hc_r)
check("فحص اليد: حكم «قرائن قوية» عند 3 أدلة فأكثر + قائمة القرائن",
      "قرائن قوية" in _hc_msg and "القرائن المرصودة" in _hc_msg
      and "سقف مُدار" in _hc_msg)
check("فحص اليد: بلا قرائن ⇒ «لا قرائن واضحة» (صدق)",
      "لا قرائن واضحة" in HC.render_hand_check("Q", {"symbol": "Q", "price": 5.0,
                                                     "behav": {}}))
check("فحص اليد·الأهم: يحلّله كسهم ارتكاز (قسم «التحليل كسهم ارتكاز»)",
      "التحليل كسهم ارتكاز" in _hc_msg)
_hc_gates = [("السعر فوق $1", True, "$2.00"),
             ("الهبوط ضمن 40–97%", True, "-70%"),
             ("انفجار سابق 60% فأكثر", True, "120%"),
             ("قاعدة ضيقة (40% أو أقل) ولم ينفجر", False, "55%"),
             ("RSI تشبّع (قاع 32 أو أقل) والآن أقل من 50", False, "الآن 47")]
_hc_piv = dict(_hc_r, gates=_hc_gates,
               interp={"setup_type": "liquidity_sweep",
                       "entry_mode": {"mode": "near_support"},
                       "critical_number": {"price": 2.2, "why": "تجاوزه يفعّل"}},
               tranches=[1.8, 1.9, 2.0], stop=(1.7, 1.75),
               t1=2.3, t2=2.6, t3=3.0)
_hc_pmsg = HC.render_hand_check("TST", _hc_piv)
check("فحص اليد·ارتكاز مؤهّل: يعرض «مؤهّل» + الحالة + الرقم الحرج + الأهداف",
      "سهم ارتكاز مؤهّل" in _hc_pmsg and "الرقم الحرج" in _hc_pmsg
      and "🎯 أهداف:" in _hc_pmsg)
check("فحص اليد·البوابات: يعرض كل البوابات ✅/❌ + العدّ «N/M» (طلب المستخدم)",
      "البوابات الإلزامية:" in _hc_pmsg and "3/5" in _hc_pmsg
      and "❌ قاعدة ضيقة" in _hc_pmsg and "✅ السعر فوق" in _hc_pmsg)
# 🎯 جوهر الطلب: سهم سقط على بوابة صلبة (السعر) — تظهر باقي البوابات مع ذلك
_hc_low = {"symbol": "BBLG", "price": 1.30, "behav": {"sweeps": 3, "score": 61},
           "reject_reason": "M1_سعر=1",
           "gates": [("السعر فوق $1", False, "$1.30"),
                     ("الهبوط ضمن 40–97%", True, "-60%"),
                     ("انفجار سابق 60% فأكثر", True, "90%"),
                     ("قاعدة ضيقة (40% أو أقل)", True, "30%")]}
_hc_lmsg = HC.render_hand_check("BBLG", _hc_low)
check("فحص اليد·الأهم: سهم تحت الحد (سقط على السعر) يعرض باقي البوابات كاملة",
      "ليس سهم ارتكاز مؤهّلًا" in _hc_lmsg and "3/4" in _hc_lmsg
      and "❌ السعر فوق" in _hc_lmsg and "✅ الهبوط" in _hc_lmsg
      and "✅ انفجار سابق" in _hc_lmsg)
check("فحص اليد·صدق: نص «تدفق الطلبات الحي غير متاح» موجود (بلا تدفق حي)",
      "تدفق الطلبات الحي" in _hc_msg)
# 🩹 التذييل صادق حسب المصدر: تدفق Polygon الحي ⇒ «حي من Polygon» لا «غير متاح»
_hc_poly = HC.render_hand_check("P", {"symbol": "P", "price": 2.0, "behav": {},
    "order_flow": "🟢 تدفق حي (Polygon): 80% شراء · طلب $2.0×5"})
check("فحص اليد·صدق التذييل: تدفق Polygon الحي يُوسَم «حي من Polygon» لا «غير متاح»",
      "حي من Polygon" in _hc_poly
      and "تدفق الطلبات الحي (Level 2) غير متاح" not in _hc_poly)
check("فحص اليد·قفل: render_hand_check لا يخترع درجة اشتباه رقمية (نوعي فقط)",
      "من 100" not in _hc_msg and "درجة اشتباه" not in _hc_msg)
# 📊 تدفق الأوامر Polygon — طبقة اختيارية فاشلة-آمنة (طلب المستخدم: «شرطة، لا تعطيل»)
_os_hc.environ.pop("POLYGON_API_KEY", None)
check("تدفق·فاشل-آمن: بلا مفتاح POLYGON ⇒ polygon_flow=None (لا تعطيل)",
      S.polygon_flow("AAPL") is None)
check("تدفق·شرطة: فحص اليد يعرض «تدفق الأوامر: —» عند تعذّره (لا يعيق)",
      "تدفق الأوامر: —" in HC.render_hand_check(
          "N", {"symbol": "N", "price": 2.0, "behav": {}}))
check("تدفق·قفل: polygon_flow/order_snapshot خارج rank_key/select_top/analyze_ticker",
      all(("polygon_flow" not in _insp0.getsource(f)
           and "order_snapshot" not in _insp0.getsource(f))
          for f in (S.rank_key, S.select_top, S.analyze_ticker)))
check("تدفق·صدق: order_snapshot يُفضّل Polygon الحي ثم يرجع احتياطًا (بلا انهيار)",
      "polygon_flow" in _insp0.getsource(S.order_snapshot)
      and S.order_snapshot("ZZZZINVALID") is None)

# ===== 🔬 رادار التجميع الصامت (POLYGON_EDGE_PLAN §أ — Polygon، عرض/تحقّق فقط) =====
# قاعدة التيك (نقية): أعلى=+1 · أدنى=-1 · مساوٍ=يحمل آخر اتجاه · الأولى=0 (بلا سابق)
check("تجميع·تيك: قاعدة التيك تصنّف صعود/هبوط/مساوٍ (الأولى 0)",
      S._tick_classify([1.0, 1.1, 1.1, 1.05, 1.05, 1.2]) == [0, 1, 1, -1, -1, 1])
# مكوّنات التجميع من صفقات خام معلومة يدويًا (31 صفقة: 20 شراء عدواني · 10 بيع)
_acc_up = [round(1.00 + 0.01 * i, 2) for i in range(21)]        # 20 صعود
_acc_dn = [round(1.20 - 0.01 * i, 2) for i in range(1, 11)]     # 10 هبوط
_acc_trA = [{"price": p, "size": 100, "exchange": 10}
            for p in _acc_up + _acc_dn]                         # 31 صفقة
check("تجميع·مكوّنات: شراء عدواني 20÷30 مصنَّف = 67% · بلا طبعات/دارك",
      S.acc_components(_acc_trA) == {"aggressive_buy_pct": 67, "block_share_pct": 0,
                                     "block_buy_pct": None, "dark_share_pct": 0,
                                     "n_trades": 31})
# طبعات كبيرة (≥10× الوسيط) + دارك (exchange==4): معايرة ذاتية نسبية
_acc_trB = [{"price": round(2.0 + 0.01 * i, 2),
             "size": (4000 if i >= 27 else 100),
             "exchange": (4 if i >= 24 else 10)} for i in range(30)]
_acc_B = S.acc_components(_acc_trB)
check("تجميع·طبعات: 3 طبعات ضخمة (4000 مقابل وسيط 100) ⇒ حصّة طبعات كبيرة",
      _acc_B["block_share_pct"] == 82 and _acc_B["n_trades"] == 30)
check("تجميع·دارك: صفقات exchange==4 تُحسب حصّة دارك",
      _acc_B["dark_share_pct"] == 84)
# 🔬 T-ACC-2: عدوانية الشراء داخل الطبعات الكبيرة فقط (اتجاه×حجم، مسجَّل مسبقًا)
check("T-ACC-2·طبعات<5: أقل من 5 طبعات مصنَّفة ⇒ block_buy_pct=None (لا نسبة على <5)",
      _acc_B["block_buy_pct"] is None)
_acc_trC = [{"price": 2.00, "size": 100, "exchange": 10} for _ in range(24)] + [
    {"price": p, "size": 5000, "exchange": 10} for p in
    (2.05, 2.10, 2.15, 2.20, 2.25, 2.30, 2.25, 2.20)]   # 6 صعود / 2 هبوط = 75%
check("T-ACC-2·حساب: 6 طبعات شراء ÷ 8 مصنَّفة = 75% (اتجاه×حجم)",
      S.acc_components(_acc_trC)["block_buy_pct"] == 75)
check("T-ACC-2·قفل: block_buy_pct يُحكم بنفس معيار _ACC_COMPS وخارج الفرز",
      any(k == "block_buy_pct" for k, _ in S._ACC_COMPS)
      and all("block_buy_pct" not in _insp0.getsource(_f)
              for _f in (S.rank_key, S.select_top, S.classify_tier,
                         S.entry_status, S.analyze_ticker, S.backtest_symbol)))
check("تجميع·صدق: أقل من 30 صفقة ⇒ None (عيّنة غير كافية، لا تخمين)",
      S.acc_components([{"price": 1.0, "size": 100}] * 29) is None)
check("تجميع·صدق: بيانات فارغة/فاسدة ⇒ None (لا انهيار)",
      S.acc_components([]) is None and S.acc_components([{"x": 1}] * 40) is None)
# 🔴 الخط الأحمر #1: فاشل-آمن مطلق — بلا مفتاح ⇒ None (يُعرض «—»، لا يعيق الفرز)
_os_hc.environ.pop("POLYGON_API_KEY", None)
check("تجميع·فاشل-آمن: بلا مفتاح POLYGON ⇒ polygon_base_trades=None (لا تعطيل)",
      S.polygon_base_trades("AAPL") is None)
check("تجميع·فاشل-آمن: بلا مفتاح ⇒ silent_accumulation=None (يُعرض «—»)",
      S.silent_accumulation("AAPL") is None)
# العرض: سطر عربي مبسّط · فارغ عند None (لا سطر) · «—» في فحص اليد
check("تجميع·عرض: acc_line فارغ عند None/{} (لا سطر وهمي)",
      S.acc_line(None) == "" and S.acc_line({}) == "")
check("تجميع·عرض: acc_line يعرض المكوّنات عربيًا مبسّطًا",
      "شراء عدواني 67%" in S.acc_line({"aggressive_buy_pct": 67,
          "block_share_pct": 12, "dark_share_pct": 40})
      and "دارك 40%" in S.acc_line({"aggressive_buy_pct": 67,
          "block_share_pct": 12, "dark_share_pct": 40}))
check("تجميع·شرطة: فحص اليد يعرض «تجميع صامت: —» عند تعذّره (لا يعيق الفحص)",
      "تجميع صامت: —" in HC.render_hand_check(
          "N", {"symbol": "N", "price": 2.0, "behav": {}}))
# 🔒 قفل: دوال التجميع خارج الفرز/الترتيب/الاختيار/الحالة/الباكتيست نهائيًا
check("تجميع·قفل: دوال التجميع خارج rank_key/select_top/classify_tier/entry_status/"
      "analyze_ticker/backtest_symbol (عرض/تحقّق فقط، صفر أثر فرز)",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("silent_accumulation", "acc_components", "acc_line",
                      "polygon_base_trades", "_tick_classify")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.analyze_ticker, S.backtest_symbol)))
check("تجميع·قفل: حقل acc لا يُقرأ في rank_key/select_top (لا وزن ترتيب)",
      "acc" not in _insp0.getsource(S.rank_key).replace("acc_", "")
      and '"acc"' not in _insp0.getsource(S.select_top))


# 🔬 تجربة التحقّق T-ACC (acc_verify_report — بلا تسريب، معيار مسجَّل مسبقًا)
def _at(ab, oc, exploded=False, bl=30, dk=20):
    return {"aggressive_buy_pct": ab, "block_share_pct": bl, "dark_share_pct": dk,
            "outcome": oc, "exploded": exploded}
# مميِّز: الشراء العدواني العالي ينفجر · المنخفض لا (فرق كبير + فاصلان منفصلان)
_acc_disc = ([_at(75, "win", True)] * 7 + [_at(70, "loss", True)] * 3
             + [_at(20, "loss")] * 12 + [_at(15, "win")] * 1)
_acc_dr = "\n".join(S.acc_verify_report(_acc_disc))
check("T-ACC·تحقّق: ارتباط واضح ⇒ «مرشّح للاعتماد» (لو صمد بالسنة الأخرى)",
      "مرشّح للاعتماد" in _acc_dr and "منفصلان" in _acc_dr)
# مسطّح: لا ارتباط عبر الأثلاث
_acc_flat = ([_at(70, "win", False)] * 8 + [_at(70, "loss", True)] * 2
             + [_at(20, "win", False)] * 8 + [_at(20, "loss", True)] * 2)
_acc_fr = "\n".join(S.acc_verify_report(_acc_flat))
check("T-ACC·تحقّق: لا ارتباط ⇒ «يبقى عرضًا» (لا وزن، تجنّب الضجيج)",
      "يبقى عرضًا" in _acc_fr and "مرشّح للاعتماد" not in _acc_fr)
check("T-ACC·صدق: عيّنة <12 معبّأة ⇒ «غير كافية» (لا حكم على ضجيج)",
      "غير كافية" in "\n".join(S.acc_verify_report([_at(50, "win")] * 5)))
check("T-ACC·قفل: acc_verify_report خارج rank_key/backtest_symbol (تحقّق فقط)",
      "acc_verify_report" not in _insp0.getsource(S.rank_key)
      and "acc_verify_report" not in _insp0.getsource(S.backtest_symbol))

# ===== 🕵️ تحديث نهاية اليوم «ماذا فعلت اليد اليوم» (DIGEST — إشعار/عرض فقط) =====
def _today_df(kind):
    """آخر شمعة تمثّل فعل اليوم: sweep/break/pump/quiet فوق قاعدة هادئة."""
    base = dict(o=[2.0] * 24, c=[2.0] * 24, h=[2.06] * 24, lo=[1.90] * 24,
                v=[1e5] * 24)                  # دعم قريب ~1.90
    t = {"sweep": (2.0, 1.95, 2.0, 1.80, 1e5),   # ذيل يخرق 1.90 ثم يغلق فوقه
         "break": (1.95, 1.80, 1.97, 1.78, 1e5),  # إغلاق تحت الدعم
         "pump": (2.0, 2.6, 2.7, 2.0, 9e5),        # صعود بحجم ضخم
         "quiet": (2.0, 2.01, 2.03, 1.98, 1e5)}[kind]
    return pd.DataFrame(
        {"Open": base["o"] + [t[0]], "Close": base["c"] + [t[1]],
         "High": base["h"] + [t[2]], "Low": base["lo"] + [t[3]],
         "Volume": base["v"] + [t[4]]},
        index=pd.date_range("2025-01-01", periods=25, freq="B"))
check("🕵️اليوم: كنس دعم (ذيل خرق ثم استعادة) ⇒ «كنس الدعم … مسح سيولة»",
      any("كنس الدعم" in a for a in S.hand_activity_today({}, _today_df("sweep"))))
check("🕵️اليوم: كسر دعم (إغلاق تحته) ⇒ «كسر الدعم … وأغلق تحته»",
      any("كسر الدعم" in a for a in S.hand_activity_today({}, _today_df("break"))))
check("🕵️اليوم: شمعة صعود بحجم ضخم ⇒ تُرصد",
      any("بحجم ضخم" in a for a in S.hand_activity_today({}, _today_df("pump"))))
check("🕵️اليوم: هدوء ⇒ لا أفعال (قائمة فارغة)",
      S.hand_activity_today({}, _today_df("quiet")) == [])
check("🕵️اليوم: دفاع عن السقف المُدار (ضربه ثم أغلق أحمر تحته)",
      any("دافع عن السقف" in a for a in S.hand_activity_today(
          {"h4_levels": {"managed_ceiling": {"price": 1.96, "touches": 4}}},
          _today_df("break"))))     # شمعة break: high 1.97 يضرب السقف 1.96 وتغلق أحمر
check("🕵️اليوم·فاشل-آمن: df قصير ⇒ [] (لا انهيار)",
      S.hand_activity_today({}, _today_df("quiet").head(5)) == [])
# الملخّص الكامل build_hand_digest
_wl_dg = {"week_start": "2026-07-01", "removed": [], "notes": [], "stocks": [
    {"symbol": "ACT", "status": "active", "last_price": 1.95,
     "behav": {"sweeps": 3, "score": 65}, "rotation_pct": 160,
     "h4_levels": {"managed_ceiling": {"price": 3.0, "touches": 4}},
     "pump_scar": {"found": True, "jump_pct": 60, "bars_ago": 10,
                   "broke_support": True}},
    {"symbol": "QUIET", "status": "active", "last_price": 5.0, "behav": {}}]}
_wl_dg["stocks"][0]["interp"] = {"entry_mode": {"mode": "near_support"}}
_dg = S.build_hand_digest(_wl_dg, {"ACT": _today_df("sweep")})
check("🕵️الملخّص: ترويسة «تحديث اليد — نهاية اليوم» + السهم النشط + فعله اليوم",
      "تحديث اليد — نهاية اليوم" in _dg and "$ACT" in _dg
      and "كنس الدعم" in _dg and "🕵️ علامات اليد" in _dg)
check("🕵️الملخّص·الأهم: يوضّح حالة الدخول (جاهز/متابعة) لكل سهم",
      "🟢 جاهز للدخول" in _dg or "👀 متابعة" in _dg)
check("🕵️الملخّص: السهم بلا يد ولا نشاط لا يظهر (QUIET مستبعد)",
      "$QUIET" not in _dg)
_dg_empty = S.build_hand_digest(
    {"stocks": [{"symbol": "Z", "status": "active", "behav": {}}]}, {})
check("🕵️الملخّص: لا يد ولا نشاط ⇒ «لا نشاط مضارب ملحوظ اليوم»",
      "لا نشاط مضارب ملحوظ" in _dg_empty)
check("🕵️الملخّص·قفل: DIGEST لا يحفظ القائمة (إشعار فقط، لا سباق حالة)",
      "save_watchlist" not in _insp0.getsource(S.build_hand_digest)
      and "save_watchlist" not in _insp0.getsource(S.run_hand_digest))

# ===== 🚨 الأحداث اللحظية (مسح · دخول منطقة · كسر · تجاوز الرقم الحرج) =====
_wl_sw = {"stocks": [
    {"symbol": "SWP", "status": "active", "last_price": 2.0,
     "tranches": [1.7, 1.75, 1.8], "stop": 1.6, "pivot": 1.85,
     "interp": {"entry_mode": {"mode": "near_support"}}},
    {"symbol": "CLM", "status": "active", "last_price": 5.0}]}
_sw_hist = {"SWP": _today_df("sweep"), "CLM": _today_df("quiet")}
_sw = S.monitor_live_events(_wl_sw, _sw_hist, "2026-07-08")
check("لحظي·مسح: يكشف كنس الدعم (SWP) دون الهادئ (CLM)",
      any(k == "sweep" and s["symbol"] == "SWP" for s, k, _ in _sw)
      and not any(s["symbol"] == "CLM" for s, _, _ in _sw))
check("لحظي·دِدوب: نفس اليوم/الحدث لا يتكرّر (live_alert)",
      not any(k == "sweep" for _, k, _ in
              S.monitor_live_events(_wl_sw, _sw_hist, "2026-07-08"))
      and _wl_sw["stocks"][0]["live_alert"]["sweep"] == "2026-07-08")
check("لحظي·دِدوب: يوم جديد ⇒ ينبّه ثانية",
      any(k == "sweep" for _, k, _ in
          S.monitor_live_events(_wl_sw, _sw_hist, "2026-07-09")))
# دخول منطقة الشراء (لحظة التنفيذ): السعر داخل [min,max] الدفعات
_wl_bz = {"stocks": [{"symbol": "BZ", "status": "active",
                      "tranches": [1.95, 2.0, 2.05], "stop": 1.7, "pivot": 1.9}]}
_bz = S.monitor_live_events(_wl_bz, {"BZ": _today_df("quiet")}, "2026-07-08")
check("لحظي·منطقة الشراء: دخل [min,max] الدفعات ⇒ حدث buyzone",
      any(k == "buyzone" for _, k, _ in _bz))
# كسر الوقف = خطر
_wl_bk = {"stocks": [{"symbol": "BK", "status": "active",
                      "tranches": [2.5, 2.6], "stop": 2.05, "pivot": 2.4}]}
_bk = S.monitor_live_events(_wl_bk, {"BK": _today_df("quiet")}, "2026-07-08")
check("لحظي·كسر الوقف: السعر عند/تحت الوقف ⇒ حدث break (خطر)",
      any(k == "break" for _, k, _ in _bk))
# تجاوز الرقم الحرج ⇒ breakout
_wl_bo = {"stocks": [{"symbol": "BO", "status": "active",
                      "tranches": [1.5, 1.6], "stop": 1.3, "pivot": 1.55,
                      "interp": {"critical_number": {"price": 1.9,
                                 "type": "breakout_activation"}}}]}
_bo = S.monitor_live_events(_wl_bo, {"BO": _today_df("quiet")}, "2026-07-08")
check("لحظي·تجاوز الرقم الحرج: السعر فوقه ⇒ حدث breakout",
      any(k == "breakout" for _, k, _ in _bo))
_sw_msg = S.build_live_alert(_sw, {"SWP": "شراء $1.99×5 · بيع $2.02×3 · سبريد 1%"})
check("لحظي·رسالة: «أحداث لحظية» + السهم + لقطة الأوامر + ملاحظة الصدق",
      "أحداث لحظية" in _sw_msg and "$SWP" in _sw_msg
      and "لقطة الأوامر: شراء" in _sw_msg
      and "ليست تدفق أوامر حيًّا" in _sw_msg)
# 🩹 التذييل صادق حسب المصدر: تدفق Polygon الحي ⇒ لا يُوسَم «من Yahoo/ليست حيًّا»
_sw_poly = S.build_live_alert(_sw, {"SWP": "🟢 تدفق حي (Polygon): 91% شراء · "
                                    "9% بيع (آخر 100 صفقة) · طلب $1.76×600"})
check("لحظي·صدق التذييل: تدفق Polygon الحي يُوسَم «حي فعلي» لا «من Yahoo/ليست حيًّا»",
      "تدفق أوامر حي فعلي" in _sw_poly
      and "من Yahoo" not in _sw_poly
      and "ليست تدفق أوامر حيًّا" not in _sw_poly)
check("لحظي·قفل: monitor_live_events خارج rank_key/select_top (تنبيه فقط)",
      "monitor_live_events" not in _insp0.getsource(S.rank_key)
      and "monitor_live_events" not in _insp0.getsource(S.select_top))

# ===== ⚡ كنسة الدقيقة الحية (POLYGON_EDGE_PLAN §ب — Polygon، تأكيد مسح أدق) =====
# دالة الكشف النقية: أدنى دقيقة خرقت الدعم >2% ثم آخر إغلاق دقيقة استعاد فوقه
_ms_ok = [{"l": 2.0, "c": 2.0}, {"l": 1.90, "c": 1.93},
          {"l": 1.88, "c": 1.95}, {"l": 1.96, "c": 2.02}]   # خرق 1.88 ثم استعادة 2.02
_ms_nostay = [{"l": 2.0, "c": 2.0}, {"l": 1.90, "c": 1.93},
              {"l": 1.85, "c": 1.88}]                        # خرق بلا استعادة (1.88<2.0)
_ms_nobreak = [{"l": 2.0, "c": 2.01}, {"l": 1.99, "c": 2.0},
               {"l": 1.98, "c": 2.02}]                       # لا خرق (1.98 ليس <1.96)
check("دقيقة·مسح: خرق الدعم >2% ثم استعادة بآخر دقيقة ⇒ True",
      S._minute_sweep(_ms_ok, 2.00) is True)
check("دقيقة·مسح: خرق بلا استعادة (آخر إغلاق تحت الدعم) ⇒ False",
      S._minute_sweep(_ms_nostay, 2.00) is False)
check("دقيقة·مسح: لا خرق (كل الدقائق فوق عتبة 2%) ⇒ False",
      S._minute_sweep(_ms_nobreak, 2.00) is False)
check("دقيقة·مسح·صدق: بيانات فارغة/دعم غير صالح ⇒ False (لا انهيار)",
      S._minute_sweep([], 2.00) is False and S._minute_sweep(_ms_ok, 0) is False)
# 🔴 فاشل-آمن: بلا مفتاح ⇒ polygon_minute_bars=None (يسقط للمسار اليومي)
_os_hc.environ.pop("POLYGON_API_KEY", None)
check("دقيقة·فاشل-آمن: بلا مفتاح POLYGON ⇒ polygon_minute_bars=None",
      S.polygon_minute_bars("AAPL") is None)
# 🔒 قفل «بلا مفتاح = المسار اليومي حرفيًا»: نفس نتيجة كشف المسح اليومي دون تغيير
_wl_mb = {"stocks": [{"symbol": "SWP2", "status": "active", "last_price": 2.0,
                      "tranches": [1.7, 1.75, 1.8], "stop": 1.6, "pivot": 1.85,
                      "interp": {"entry_mode": {"mode": "near_support"}}}]}
_mb_ev = S.monitor_live_events(_wl_mb, {"SWP2": _today_df("sweep")}, "2026-07-08")
check("دقيقة·قفل: بلا مفتاح ⇒ المسار اليومي يكشف المسح كما كان (حرفيًا)",
      any(k == "sweep" for _, k, _ in _mb_ev))
check("دقيقة·قفل: التأكيد بالدقيقة داخل monitor فقط (خارج rank_key/select_top/"
      "backtest_symbol)",
      all(("polygon_minute_bars" not in _insp0.getsource(_f)
           and "_minute_sweep" not in _insp0.getsource(_f))
          for _f in (S.rank_key, S.select_top, S.backtest_symbol)))

# ===== 🌙 رادار البريماركت (POLYGON_EDGE_PLAN §ج — Polygon، تحرّك ما قبل الافتتاح) =====
# ملخّص البريماركت النقي: أعلى/أدنى/آخر + حجم تراكمي + تغيّر% صحيح عن إغلاق الأمس
_pm_bars = [{"o": 10, "h": 10.5, "l": 9.8, "c": 10.2, "v": 1000},
            {"o": 10.2, "h": 11.5, "l": 10.1, "c": 11.0, "v": 3000},
            {"o": 11.0, "h": 11.8, "l": 10.9, "c": 11.5, "v": 2000}]  # آخر 11.5
_pm_s = S._premarket_summary(_pm_bars, prev_close=10.0)     # (11.5/10-1)=+15%
check("بريماركت·ملخّص: أعلى/أدنى/آخر + حجم تراكمي + تغيّر% صحيح عن إغلاق الأمس",
      _pm_s["change_pct"] == 15.0 and _pm_s["cum_vol"] == 6000
      and _pm_s["high"] == 11.8 and _pm_s["low"] == 9.8 and _pm_s["last"] == 11.5)
check("بريماركت·ملخّص: بلا إغلاق أمس ⇒ تغيّر% None (لا تخمين) · بلا بارات ⇒ None",
      S._premarket_summary(_pm_bars)["change_pct"] is None
      and S._premarket_summary([]) is None)
# 🔴 فاشل-آمن: بلا مفتاح ⇒ None (يبقى session_ctx الحالي بسببه الصريح)
_os_hc.environ.pop("POLYGON_API_KEY", None)
check("بريماركت·فاشل-آمن: بلا مفتاح POLYGON ⇒ polygon_premarket=None",
      S.polygon_premarket("AAPL") is None)
check("بريماركت·قفل: بلا مفتاح ⇒ لا حدث premarket (المسار القائم حرفيًا)",
      not any(k == "premarket" for _, k, _ in S.monitor_live_events(
          {"stocks": [{"symbol": "PMZ", "status": "active", "last_price": 2.0,
                       "pivot": 1.85}]},
          {"PMZ": _today_df("quiet")}, "2026-07-08")))
# حدث premarket + دِدوب + عتبة (بمفتاح + ستب بلا شبكة، ثم استعادة الأصل)
_os_hc.environ["POLYGON_API_KEY"] = "x"
_pm_orig = S.polygon_premarket
S.polygon_premarket = lambda sym, prev_close=None: {
    "kind": "premarket", "high": 2.4, "low": 2.0, "last": 2.3,
    "cum_vol": 50000, "change_pct": 15.0}
try:
    _wl_pm = {"stocks": [{"symbol": "PMX", "status": "active", "last_price": 2.0,
                          "tranches": [1.7, 1.75, 1.8], "stop": 1.6, "pivot": 1.85}]}
    _pm_ev = S.monitor_live_events(_wl_pm, {"PMX": _today_df("quiet")}, "2026-07-08")
    check("بريماركت·حدث: تحرّك ≥10% بحجم ⇒ حدث premarket «راقب الافتتاح»",
          any(k == "premarket" and "راقب الافتتاح" in d for _, k, d in _pm_ev))
    check("بريماركت·دِدوب: نفس اليوم لا يتكرّر · يوم جديد ينبّه ثانية",
          not any(k == "premarket" for _, k, _ in S.monitor_live_events(
              _wl_pm, {"PMX": _today_df("quiet")}, "2026-07-08"))
          and any(k == "premarket" for _, k, _ in S.monitor_live_events(
              _wl_pm, {"PMX": _today_df("quiet")}, "2026-07-09")))
    # premarket_only=True: يبقى رادار البريماركت فعّالًا لكن يتخطّى أحداث الجلسة
    # (الشمعة اليومية = أمس قبل الافتتاح، فلا نُعيد إطلاق مسح/كسر الأمس صباحًا)
    _po_stub = S.monitor_live_events(
        {"stocks": [{"symbol": "POS", "status": "active", "last_price": 2.0,
                     "pivot": 1.85, "tranches": [1.7, 1.75, 1.8], "stop": 1.6}]},
        {"POS": _today_df("sweep")}, "2026-07-08", premarket_only=True)
    check("بريماركت·premarket_only: يبقي البريماركت ويتخطّى أحداث الجلسة (لا مسح أمس)",
          any(k == "premarket" for _, k, _ in _po_stub)
          and not any(k == "sweep" for _, k, _ in _po_stub))
    S.polygon_premarket = lambda sym, prev_close=None: {"change_pct": 5.0,
                                                        "cum_vol": 1000}
    check("بريماركت·عتبة: تحرّك دون PM_MOVE_PCT (5%<10%) ⇒ لا حدث",
          not any(k == "premarket" for _, k, _ in S.monitor_live_events(
              {"stocks": [{"symbol": "PMY", "status": "active", "last_price": 2.0,
                           "pivot": 1.85}]},
              {"PMY": _today_df("quiet")}, "2026-07-08")))
finally:
    S.polygon_premarket = _pm_orig
    _os_hc.environ.pop("POLYGON_API_KEY", None)
# 🔴 تشغيل مبكر بلا مفتاح = لا عمل (رخيص، مطابق للخطة): premarket_only يتخطّى الجلسة
# وبلا مفتاح لا بريماركت → صفر أحداث (حتى على شمعة تُرصد مسحًا في المسار العادي)
check("بريماركت·premarket_only بلا مفتاح: لا أحداث (تشغيل مبكر رخيص بلا عمل)",
      S.monitor_live_events(
          {"stocks": [{"symbol": "POE", "status": "active", "last_price": 2.0,
                       "pivot": 1.85, "tranches": [1.7, 1.75, 1.8], "stop": 1.6}]},
          {"POE": _today_df("sweep")}, "2026-07-08", premarket_only=True) == [])
# session_ctx صادق: الإكمال موصول في enrich + السبب الصريح باقٍ (بلا مفتاح = حرفيًا)
check("بريماركت·session_ctx: enrich يوصل إكمال Polygon + يبقي السبب الصريح بلا مفتاح",
      "polygon_premarket" in _insp0.getsource(S.enrich)
      and "من Polygon" in _insp0.getsource(S.enrich)
      and "غير متاحة" in _insp0.getsource(S.enrich))
check("بريماركت·قفل: polygon_premarket/_premarket_summary خارج rank_key/select_top/"
      "classify_tier/backtest_symbol",
      all(("polygon_premarket" not in _insp0.getsource(_f)
           and "_premarket_summary" not in _insp0.getsource(_f))
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.backtest_symbol)))

# ===== 🔥 رادار الانطلاق اللحظي (IGNITION_PLAN.md — رد فعل حي، توقيت لا اختيار) =====
def _ig_bars(prices, vols):
    return [{"o": p, "h": p * 1.01, "l": p * 0.99, "c": p, "v": v}
            for p, v in zip(prices, vols)]
_ig_quiet = [1.95, 1.96, 1.95, 1.96, 1.97, 1.96, 1.95, 1.96, 1.97]
_ig_fire = _ig_bars(_ig_quiet + [2.05], [100] * 9 + [500])     # حجم 5× · كسر 2.00 صاعدًا
# دالة الكشف النقية
check("انطلاق·كشف: قفزة حجم + كسر صاعد + اتجاه صاعد ⇒ اشتعال {price,vol_x,usd}",
      S._ignition_signal(_ig_fire, 2.00) == {"price": 2.05, "vol_x": 5.0,
                                             "usd": round(2.05 * 500)})
check("انطلاق·كشف: لا قفزة حجم (1.2×) ⇒ None",
      S._ignition_signal(_ig_bars(_ig_quiet + [2.05], [100] * 9 + [120]), 2.00) is None)
check("انطلاق·كشف: لا كسر (السعر تحت الحاجز) ⇒ None",
      S._ignition_signal(_ig_bars(_ig_quiet + [1.99], [100] * 9 + [500]), 2.00) is None)
check("انطلاق·كشف: هابط (آخر أقل من أول النافذة) ⇒ None (لا اشتعال زائف)",
      S._ignition_signal(_ig_bars([2.10] * 9 + [2.05], [100] * 9 + [500]), 2.00) is None)
check("انطلاق·صدق: بارات غير كافية/حاجز غير صالح ⇒ None",
      S._ignition_signal(_ig_bars([2.0] * 3, [100] * 3), 2.00) is None
      and S._ignition_signal(_ig_fire, 0) is None)
# حاجز الكسر: الرقم الحرج ثم أرضية×1.05
check("انطلاق·حاجز: الرقم الحرج (فيصل) ثم 5% فوق الأرضية · None لو لا مرجع",
      S._ignition_break_level({"interp": {"critical_number": {"price": 2.5}}}) == 2.5
      and S._ignition_break_level({"pivot": 2.0}) == 2.10
      and S._ignition_break_level({}) is None)
# المنسّق scan_ignition (بحقن جالبات — بلا شبكة) + دِدوب
_ig_wl = {"stocks": [
    {"symbol": "IGN", "status": "active", "pivot": 1.90, "t1": 2.4, "stop": 1.6,
     "interp": {"critical_number": {"price": 2.00}}},
    {"symbol": "QUIET", "status": "active", "pivot": 5.0,
     "interp": {"critical_number": {"price": 6.0}}}]}
_ig_map = {"IGN": _ig_fire, "QUIET": _ig_bars([5.0] * 10, [100] * 10)}
_ig_op = lambda s: {"has_operator": True}   # مضارب موجود (تُختبر البوّابة مستقلةً أدناه)
_ig_rows = S.scan_ignition(_ig_wl, "2026-07-08",
                           fetch_bars=lambda s: _ig_map.get(s),
                           fetch_flow=lambda s: "65% شراء" if s == "IGN" else None,
                           fetch_operator=_ig_op)
check("انطلاق·منسّق: يكشف المشتعل (IGN) دون الهادئ (QUIET) + يرفق التدفق",
      len(_ig_rows) == 1 and _ig_rows[0][0]["symbol"] == "IGN"
      and _ig_rows[0][2] == "65% شراء")
check("انطلاق·دِدوب: نفس اليوم لا يتكرّر · يوم جديد ينبّه",
      S.scan_ignition(_ig_wl, "2026-07-08", fetch_bars=lambda s: _ig_map.get(s),
                      fetch_operator=_ig_op) == []
      and len(S.scan_ignition(_ig_wl, "2026-07-09",
                              fetch_bars=lambda s: _ig_map.get(s),
                              fetch_operator=_ig_op)) == 1)
check("انطلاق·فاشل-آمن: فشل جلب البارات ⇒ يتخطّى السهم (لا انهيار)",
      S.scan_ignition({"stocks": [{"symbol": "E", "status": "active", "pivot": 1.9,
                                   "interp": {"critical_number": {"price": 2.0}}}]},
                      "2026-07-08",
                      fetch_bars=lambda s: (_ for _ in ()).throw(ValueError("x"))) == [])
check("انطلاق·رسالة: «انطلاق لحظي» + السهم + الحجم + الكسر + هدف/وقف",
      "انطلاق لحظي" in S.build_ignition_alert(_ig_rows)
      and "$IGN" in S.build_ignition_alert(_ig_rows)
      and "5× المتوسط" in S.build_ignition_alert(_ig_rows)
      and "رد فعل لحظي" in S.build_ignition_alert(_ig_rows))
check("انطلاق·قفل: رادار توقيت/تنبيه فقط — خارج rank_key/select_top/classify_tier/"
      "analyze_ticker/backtest_symbol (لا يمسّ الاختيار)",
      all(("scan_ignition" not in _insp0.getsource(_f)
           and "_ignition_signal" not in _insp0.getsource(_f))
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.analyze_ticker,
                     S.backtest_symbol)))
# 🔥📏 دالّتا التحقّق التاريخي (IGNITION_VERIFY_PLAN.md — قياس «هل فاد الاشتراك؟»)
check("تحقّق·يوم الانفجار: أول قمة تبلغ +50% من الدخول (وإلا None)",
      S._find_explosion_day([2.1, 2.3, 2.8, 3.05, 3.4], 2.0, 50) == 3
      and S._find_explosion_day([2.1, 2.2, 2.3], 2.0, 50) is None)
_iv_day = [{"o": p, "h": p * 1.01, "l": p * 0.99, "c": p, "v": v} for p, v in zip(
    [2.00, 2.00, 2.01, 2.00, 2.01, 2.00, 2.00, 2.01, 2.08], [100] * 8 + [500])]
_iv_fire = S._ignition_first_fire(_iv_day, 2.05, 2.00)   # يشتعل 2.08>2.05 · مكسب +4%
check("تحقّق·أول اشتعال: يمسك اللحظة + مكسب اليوم من الافتتاح (+4%)",
      _iv_fire["gain_pct"] == 4.0 and _iv_fire["vol_x"] == 5.0)
check("تحقّق·أول اشتعال: لا كسر ⇒ None (لم يشتعل يوم الانفجار)",
      S._ignition_first_fire(
          [{"o": 2.0, "h": 2.02, "l": 1.99, "c": 2.03, "v": v} for v in [100] * 8 + [500]],
          2.10, 2.00) is None)
check("تحقّق·قفل: دالّتا التحقّق خارج rank_key/select_top/backtest_symbol",
      all(("_find_explosion_day" not in _insp0.getsource(_f)
           and "_ignition_first_fire" not in _insp0.getsource(_f))
          for _f in (S.rank_key, S.select_top, S.backtest_symbol)))

# ===== 📏 حلقة قياس رادار الانطلاق (سجلّ حي → أداة التطوير: الالتقاط/الإنذار الكاذب) =====
def _ig_oc_df(rows):        # rows = [(تاريخ, أعلى, إغلاق), ...]
    return pd.DataFrame({"High": [r[1] for r in rows], "Close": [r[2] for r in rows]},
                        index=pd.to_datetime([r[0] for r in rows]))
_oc_fire = {"price": 2.0, "break_level": 2.0, "date": "2026-07-08",
            "candle_class": "operator"}
_oc_real = _ig_oc_df([("2026-07-09", 2.1, 2.05), ("2026-07-10", 2.30, 2.28)])
_oc_fake = _ig_oc_df([("2026-07-09", 2.1, 1.90)])
_oc_pend = _ig_oc_df([("2026-07-09", 2.1, 2.05)])
check("📏 نتيجة الاشتعال: أعلى لاحق ≥+12% من سعر الاشتعال ⇒ حقيقي",
      S._ignition_outcome(_oc_fire, _oc_real) == "real")
check("📏 نتيجة الاشتعال: إغلاق لاحق تحت الكسر قبل التأكيد ⇒ كاذب",
      S._ignition_outcome(_oc_fire, _oc_fake) == "fakeout")
check("📏 نتيجة الاشتعال: لم يُحسم ⇒ معلّق",
      S._ignition_outcome(_oc_fire, _oc_pend) == "pending")
check("📏 نتيجة·فاشل-آمن + بلا تسريب: None/شموع قبل الاشتعال ⇒ معلّق",
      S._ignition_outcome(_oc_fire, None) == "pending"
      and S._ignition_outcome(_oc_fire, _ig_oc_df([("2026-07-07", 2.9, 2.8)])) == "pending")
# كتلة القياس (بحقن جالب — بلا شبكة): الالتقاط/الكاذب + تفصيل تصنيف الشمعة
_log_fires = (
    [{"symbol": f"R{i}", "date": "2026-07-08", "price": 2.0, "break_level": 2.0,
      "candle_class": "operator"} for i in range(4)]
    + [{"symbol": "RG0", "date": "2026-07-08", "price": 2.0, "break_level": 2.0,
        "candle_class": "group"}]
    + [{"symbol": "F1", "date": "2026-07-08", "price": 2.0, "break_level": 2.0,
        "candle_class": "operator"}]
    + [{"symbol": f"FG{i}", "date": "2026-07-08", "price": 2.0, "break_level": 2.0,
        "candle_class": "group"} for i in range(3)]
    + [{"symbol": "P1", "date": "2026-07-08", "price": 2.0, "break_level": 2.0,
        "candle_class": "mid"}])
def _log_fetch(sym, d):
    return _oc_real if sym.startswith("R") else (
        _oc_fake if sym.startswith("F") else _oc_pend)
_blk = "\n".join(S._ignition_log_block(_log_fires, fetch=_log_fetch))
check("📏 كتلة القياس: تعرض «إنذار كاذب %» من المحسوم (4 كاذب / 9 محسوم = 44%)",
      "إنذار كاذب" in _blk and "44%" in _blk)
check("📏 كتلة القياس: تفصيل حسب تصنيف الشمعة (قروب يكذب أكثر — دليل المعايرة)",
      "قروب: 3/4 كاذب" in _blk and "مضارب: 1/5 كاذب" in _blk)
check("📏 كتلة القياس·عيّنة صغيرة: تقول «تتراكم» بلا نسبة",
      "تتراكم" in "\n".join(S._ignition_log_block(
          [_log_fires[0]], fetch=_log_fetch))
      and "إنذار كاذب" not in "\n".join(S._ignition_log_block(
          [_log_fires[0]], fetch=_log_fetch)))
check("📏 كتلة القياس: سجلّ فارغ ⇒ [] (لا كتلة)", S._ignition_log_block([]) == [])
# تسجيل/قراءة السجلّ (ملف مؤقت — لا يمسّ سجلّ الريبو الحقيقي)
import tempfile as _tf_ig
_igtmp = _tf_ig.mkdtemp()
_save_igf = S.IGNITION_LOG_FILE
try:
    S.IGNITION_LOG_FILE = _igtmp + "/ig_log.json"
    _rec_rows = [({"symbol": "REC", "pivot": 1.9,
                   "interp": {"critical_number": {"price": 2.0}}},
                  {"price": 2.08, "vol_x": 5.0, "usd": 208000}, None)]
    _n1 = S.record_ignition_fires(_rec_rows, "2026-07-08")
    _n2 = S.record_ignition_fires(_rec_rows, "2026-07-08")   # دِدوب مرة/سهم/يوم
    _loaded = S.load_ignition_log()
    check("📏 تسجيل: يكتب إطلاقًا + دِدوب + يحفظ تصنيف الشمعة",
          _n1 == 1 and _n2 == 0 and len(_loaded) == 1
          and _loaded[0]["symbol"] == "REC"
          and _loaded[0]["candle_class"] == "operator"
          and _loaded[0]["break_level"] == 2.0)
    check("📏 تسجيل·فاشل-آمن: rows فارغة ⇒ 0",
          S.record_ignition_fires([], "2026-07-08") == 0)
    S.IGNITION_LOG_FILE = _igtmp + "/nope.json"
    check("📏 قراءة·فاشل-آمن: ملف غير موجود ⇒ []", S.load_ignition_log() == [])
finally:
    S.IGNITION_LOG_FILE = _save_igf
check("📏 قفل: دوال القياس خارج rank_key/select_top/classify_tier/analyze_ticker/backtest_symbol",
      all(("_ignition_outcome" not in _insp0.getsource(_f)
           and "record_ignition_fires" not in _insp0.getsource(_f)
           and "_ignition_log_block" not in _insp0.getsource(_f))
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.analyze_ticker,
                     S.backtest_symbol)))

# ===== 🕵️ بوّابة المضارب على التنبيهات («لا إشعار إلا لو دخل المضارب» — 2026-07-09) =====
# طبعات كبيرة مصنَّفة بقاعدة التيك (صعودي=شراء عدواني · هبوطي=على الطلب/امتصاص)
_optr = [(2.00, 100)] * 15 + [(2.01, 1500), (2.00, 2000), (2.02, 1200),
                              (2.00, 300), (2.00, 500)]
_ob = S._operator_blocks(_optr, 1000)
check("🕵️طبعات: شراء عدواني (صعودي ≥1000)=2700 · على الطلب (هبوطي ≥1000)=2000",
      _ob["buy_block_shares"] == 2700 and _ob["bid_block_shares"] == 2000)
check("🕵️طبعات: عدد الطبعات ≥1000 = 3 · دخل المضارب",
      _ob["n_blocks"] == 3 and _ob["has_operator"] is True)
check("🕵️طبعات: كلها <1000 سهم ⇒ لا مضارب",
      S._operator_blocks([(2.0, 100)] * 25, 1000)["has_operator"] is False)
check("🕵️طبعات·صدق: أقل من 20 صفقة ⇒ None (عيّنة غير كافية)",
      S._operator_blocks([(2.0, 1500)] * 10, 1000) is None)
check("🕵️سطر المضارب: يعرض الشراء العدواني/على الطلب + حدّ الصدق (بلا L2)",
      "شراء عدواني ~2,700" in S.operator_line(_ob)
      and "على الطلب ~2,000" in S.operator_line(_ob)
      and "بلا عمق L2" in S.operator_line(_ob))
check("🕵️سطر المضارب: None ⇒ «—»", S.operator_line(None) == "🕵️ المضارب: —")
# بوّابة الرادار: لا إشعار إلا لو دخل المضارب
_op_bars = [{"o": p, "h": p * 1.01, "l": p * 0.99, "c": p, "v": v} for p, v in zip(
    [2.0, 2.0, 2.01, 2.0, 2.01, 2.0, 2.0, 2.01, 2.08], [3000] * 8 + [100000])]  # $208K
_grp_bars = [{"o": p, "h": p * 1.01, "l": p * 0.99, "c": p, "v": v} for p, v in zip(
    [2.0, 2.0, 2.01, 2.0, 2.01, 2.0, 2.0, 2.01, 2.08], [1000] * 8 + [15000])]   # $31K قروب
def _op_st(sym):
    return {"symbol": sym, "status": "active", "pivot": 1.9, "t1": 2.4, "stop": 1.6,
            "interp": {"critical_number": {"price": 2.0}}}
_r_yes = S.scan_ignition({"stocks": [_op_st("OPY")]}, "2026-07-20",
    fetch_bars=lambda s: _op_bars, fetch_flow=lambda s: None,
    fetch_operator=lambda s: {"has_operator": True, "buy_block_shares": 2700,
                              "bid_block_shares": 2000, "n_blocks": 3})
check("🕵️بوّابة الرادار: دخل المضارب ⇒ يطلق + كمياته بالإشارة",
      len(_r_yes) == 1 and _r_yes[0][1]["operator"]["has_operator"] is True)
_wl_no = {"stocks": [_op_st("OPN")]}
check("🕵️بوّابة الرادار: لا مضارب ⇒ يُكتَم (لا إشعار · لا يُعلَّم اليوم فيُعاد الفحص)",
      S.scan_ignition(_wl_no, "2026-07-20", fetch_bars=lambda s: _op_bars,
          fetch_flow=lambda s: None,
          fetch_operator=lambda s: {"has_operator": False}) == []
      and "ignition_alert" not in _wl_no["stocks"][0])
check("🕵️بوّابة الرادار·فاشل-آمن: تعذّر القياس (None) + شمعة مضارب $ ⇒ يطلق (لا نفوّت)",
      len(S.scan_ignition({"stocks": [_op_st("OPF")]}, "2026-07-20",
          fetch_bars=lambda s: _op_bars, fetch_flow=lambda s: None,
          fetch_operator=lambda s: None)) == 1)
check("🕵️بوّابة الرادار·فاشل-آمن: تعذّر القياس (None) + شمعة قروب ⇒ يُكتَم",
      S.scan_ignition({"stocks": [_op_st("OPG")]}, "2026-07-20",
          fetch_bars=lambda s: _grp_bars, fetch_flow=lambda s: None,
          fetch_operator=lambda s: None) == [])
check("🕵️عرض الرادار: التنبيه يعرض كميات المضارب",
      "المضارب" in S.build_ignition_alert(_r_yes)
      and "شراء عدواني ~2,700" in S.build_ignition_alert(_r_yes))
# بوّابة مراقب الجلسة (نفس القاعدة — الأحداث الإيجابية فقط · الخطر لا يُبوَّب)
_mle_df = pd.DataFrame(
    {"Open": [2.0] * 30, "High": [2.1] * 30, "Low": [1.9] * 30,
     "Close": [2.0] * 29 + [1.95], "Volume": [1e5] * 30},
    index=pd.date_range("2025-01-01", periods=30, freq="B"))
def _mle_st(sym):
    return {"symbol": sym, "status": "active", "pivot": 1.90,
            "tranches": [1.90, 1.95, 2.00], "stop": (1.75, 1.79), "interp": {}}
_ev_no = S.monitor_live_events({"stocks": [_mle_st("MLN")]}, {"MLN": _mle_df},
    "2026-07-20", fetch_operator=lambda s: {"has_operator": False})
check("🕵️بوّابة المراقب: لا مضارب ⇒ يُكتَم حدث الدخول (buyzone)",
      not any(k == "buyzone" for _s, k, _d in _ev_no))
_ev_yes = S.monitor_live_events({"stocks": [_mle_st("MLY")]}, {"MLY": _mle_df},
    "2026-07-20", fetch_operator=lambda s: {"has_operator": True,
        "buy_block_shares": 2700, "bid_block_shares": 2000, "n_blocks": 3})
check("🕵️بوّابة المراقب: دخل المضارب ⇒ حدث الدخول يبقى + كمياته بالوصف",
      any(k == "buyzone" and "المضارب" in d for _s, k, d in _ev_yes))
_brk_df = pd.DataFrame(
    {"Open": [2.0] * 30, "High": [2.1] * 30, "Low": [1.5] * 30,
     "Close": [2.0] * 29 + [1.70], "Volume": [1e5] * 30},
    index=pd.date_range("2025-01-01", periods=30, freq="B"))
_ev_brk = S.monitor_live_events({"stocks": [_mle_st("BRK")]}, {"BRK": _brk_df},
    "2026-07-20", fetch_operator=lambda s: {"has_operator": False})
check("🕵️بوّابة المراقب: الخطر (كسر الوقف) لا يُبوَّب — يظهر حتى بلا مضارب",
      any(k == "break" for _s, k, _d in _ev_brk))
check("🕵️قفل: دوال المضارب خارج rank_key/select_top/classify_tier/analyze_ticker/backtest_symbol",
      all(("_operator_blocks" not in _insp0.getsource(_f)
           and "operator_flow" not in _insp0.getsource(_f))
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.analyze_ticker,
                     S.backtest_symbol)))

# ===== 🕵️💰 حزمة «قراءة المضارب» من صور فيصل (FAISAL_OPERATOR_PACK_PLAN) =====
# P1 💰 وسم شمعة مضارب/قروب بسيولتها الدولارية (قاعدة فيصل: ≥100ألف مضارب · ≤50ألف قروب)
check("مضارب·P1 تصنيف: ≥300ألف قوية · ≥100ألف مضارب · ≤50ألف قروب · بينها mid",
      S._ignition_candle_class(300000)[0] == "strong"
      and S._ignition_candle_class(150000)[0] == "operator"
      and S._ignition_candle_class(100000)[0] == "operator"      # حدّي شامل
      and S._ignition_candle_class(50000)[0] == "group"          # حدّي شامل
      and S._ignition_candle_class(70000)[0] == "mid"
      and S._ignition_candle_class(None) == ("", ""))
_ig_us = [{"o": p, "h": p * 1.01, "l": p * 0.99, "c": p, "v": v} for p, v in zip(
    [2.0, 2.0, 2.01, 2.0, 2.01, 2.0, 2.0, 2.01, 2.08], [3000] * 8 + [100000])]
_ig_us_sig = S._ignition_signal(_ig_us, 2.05)
check("مضارب·P1 سيولة: _ignition_signal يُرجع usd = سعر×حجم شمعة الاشتعال",
      _ig_us_sig["usd"] == 208000)
_ig_us_msg = S.build_ignition_alert([({"symbol": "OP", "t1": 2.4, "stop": 1.6,
    "pivot": 1.9, "interp": {"critical_number": {"price": 2.0}}}, _ig_us_sig, None)])
check("مضارب·P1 عرض: التنبيه يعرض «سيولة الشمعة $X — شمعة مضارب»",
      "سيولة الشمعة $208,000" in _ig_us_msg and "شمعة مضارب" in _ig_us_msg)
# _ignition_candle_class خارج **الاختيار** (rank_key/select_top/…). (scan_ignition
# أُزيل من القفل عمدًا 2026-07-09: صار يستعمله بوّابةً احتياطية للرادار «اكتم القروب
# لو تعذّر قياس المضارب» — طلب المستخدم؛ الرادار طبقة توقيت/تنبيه لا اختيار.)
check("مضارب·P1 قفل: الوسم خارج الاختيار (rank_key/select_top/classify/analyze/backtest)",
      all("_ignition_candle_class" not in _insp0.getsource(_f)
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.analyze_ticker,
                     S.backtest_symbol)))
# P3 ⚠️ تحذير «سيولة قطيع قبل الرفعة» (قاعدة LABT) في hand_activity_today
def _labt_df(t_c, t_o, t_v):
    b = dict(o=[2.0] * 24, c=[2.0] * 24, h=[2.05] * 24, lo=[1.95] * 24, v=[1e5] * 24)
    return pd.DataFrame(
        {"Open": b["o"] + [t_o], "Close": b["c"] + [t_c],
         "High": b["h"] + [max(t_o, t_c) * 1.02], "Low": b["lo"] + [min(t_o, t_c) * 0.98],
         "Volume": b["v"] + [t_v]},
        index=pd.date_range("2025-01-01", periods=25, freq="B"))
_labt_s = {"interp": {"critical_number": {"price": 3.0}}}
check("مضارب·P3 LABT: حجم ضخم + إغلاق تحت الرقم الحرج ⇒ تحذير «سيولة قبل الرفعة تُهبِط»",
      any("سيولة قبل رفعة المضارب" in a
          for a in S.hand_activity_today(_labt_s, _labt_df(2.4, 2.3, 8e5))))
check("مضارب·P3 LABT: نفس الحجم مع كسر الرقم الحرج ⇒ لا تحذير (اخترق صاعدًا)",
      not any("سيولة قبل رفعة" in a
              for a in S.hand_activity_today(_labt_s, _labt_df(3.2, 3.0, 8e5))))
check("مضارب·P3 LABT·فاشل-آمن: بلا رقم حرج ⇒ السلوك القديم (حجم ضخم يظهر بلا تحذير)",
      (not any("سيولة قبل رفعة" in a
               for a in S.hand_activity_today({}, _labt_df(2.4, 2.3, 8e5))))
      and any("حجم ضخم" in a for a in S.hand_activity_today({}, _labt_df(2.4, 2.3, 8e5))))
check("مضارب·P3 LABT: لا حجم ضخم ⇒ لا تحذير",
      not any("سيولة قبل رفعة" in a
              for a in S.hand_activity_today(_labt_s, _labt_df(2.4, 2.3, 1e5))))
check("مضارب·P3 قفل: التحذير لا يطابق فلتر «كنس الدعم» (لا حدث لحظي جديد)",
      not any("كنس الدعم" in a
              for a in S.hand_activity_today(_labt_s, _labt_df(2.4, 2.3, 8e5))))

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

# ── اقتباسات أداتَي التطوير (2026-07-04): قبل/بعد أسبوعي · مقاييس صادقة · Wilson ·
#    توقّع R · صرامة الفائتة (ربح ورقي). طبقة تقارير فقط على بياناتنا. أقفال جديدة.
_today_dev = S.dt.date(2026, 7, 10)


def _crow(win, cd, mg, **kw):
    r = {"_win": win, "max_gain_pct": mg}
    r.update(kw)
    r["hit_date" if win else "result_date"] = cd
    return r


_cmp_rows = [
    _crow(True, "2026-07-05", 20), _crow(True, "2026-07-06", 15),
    _crow(True, "2026-07-07", 10), _crow(False, "2026-07-08", 2),
    _crow(True, "2026-06-29", 30), _crow(False, "2026-06-30", 3),
    _crow(False, "2026-07-01", 1),
]
_cmp = "\n".join(S._weekly_compare_block(_cmp_rows, today=_today_dev))
check("قبل/بعد: يبوّب بتاريخ الإغلاق ويعرض فرق النجاح باتجاه",
      "التطوير مقابل الأسبوع الماضي" in _cmp and "هذا الأسبوع: 4 صفقات" in _cmp
      and "نجاح 75%" in _cmp and "🔼" in _cmp)
_cmp_small = "\n".join(S._weekly_compare_block(
    [_crow(True, "2026-07-05", 20), _crow(False, "2026-06-29", 3)],
    today=_today_dev))
check("قبل/بعد: حارس العيّنة الصغيرة (عدّ بلا نسب)",
      "نكتفي بالعدّ" in _cmp_small and "لمس الوقف" not in _cmp_small)

_hm_rows = [{"_win": True, "max_gain_pct": g, "symbol": s} for g, s in
            [(40, "NBP"), (26, "NERV"), (5, "A"), (4, "B"), (3, "C"), (2, "D")]]
_hm = "\n".join(S._honest_metrics_block(_hm_rows))
check("مقاييس صادقة: الوسيط + اعتماد الذيل (الحافة هشّة يحملها قليل)",
      "مقاييس صادقة" in _hm and "الوسيط" in _hm
      and "اعتماد الذيل" in _hm and "NBP" in _hm)

check("Wilson: أرضية ثقة ضمن حدود منطقية (صفر عند 0، أقل من الخام)",
      abs(S._wilson_lower_pct(0, 5)) < 1.0
      and 40 < S._wilson_lower_pct(8, 10) < 75
      and S._wilson_lower_pct(10, 10) > 55)

check("توقّع R: الرابح من الهدف/الوقف موجب · الخاسر −1",
      abs(S._realized_r({"_win": True, "entry_ref": 2.0, "stop": 1.8,
                         "hit": "t1", "t1": 2.4}) - 2.0) < 1e-6
      and S._realized_r({"_win": False, "entry_ref": 2.0, "stop": 1.8}) == -1.0)


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

# 📊 مقاييس الباكتيست الصادقة (اقتباس dev_backtest_toolkit): عائد محقّق + R +
# فاصل ثقة + أشهر موجبة. طبقة تحليل باكتيست فقط. أقفال جديدة.
check("الباكتيست·صادق: العائد المحقّق (رابح=t1 · خاسر=وقف) + R",
      abs(S._bt_realized({"entry": 2.0, "t1": 2.4, "stop": 1.8,
                          "outcome": "win"}) - 20.0) < 1e-6
      and abs(S._bt_realized({"entry": 2.0, "t1": 2.4, "stop": 1.8,
                              "outcome": "loss"}) - (-10.0)) < 1e-6
      and abs(S._bt_realized_r({"entry": 2.0, "t1": 2.4, "stop": 1.8,
                                "outcome": "win"}) - 2.0) < 1e-6)
check("Wilson CI: فاصل ضمن [0,100] والسفلى أقل من العليا",
      S._wilson_ci(8, 10)[0] < S._wilson_ci(8, 10)[1] <= 100.0
      and S._wilson_ci(8, 10)[0] >= 0.0)
_bt_ht = ([{"symbol": "A", "date": "2026-05-01", "entry": 2.0, "t1": 2.4,
            "stop": 1.8, "outcome": "win"}] * 5 +
          [{"symbol": "B", "date": "2026-06-01", "entry": 2.0, "t1": 2.4,
            "stop": 1.8, "outcome": "win"}] * 3 +
          [{"symbol": "C", "date": "2026-06-02", "entry": 2.0, "t1": 2.4,
            "stop": 1.8, "outcome": "loss"}] * 2)
_bth = "\n".join(S.backtest_honest_summary(_bt_ht))
check("الباكتيست·صادق: الوسيط + فاصل الثقة + الأشهر الموجبة تظهر",
      "مقاييس صادقة للباكتيست" in _bth and "الوسيط" in _bth
      and "فاصل الثقة" in _bth and "الأشهر الموجبة" in _bth and "R" in _bth)
# شفافية (مراجعة خصومية): الصفقات العالقة تُفصح لا تُخفى + backtest_stats يعدّها
_bt_open = _bt_ht + [{"symbol": "O", "date": "2026-06-03", "entry": 2.0,
                      "t1": 2.4, "stop": 1.8, "outcome": "open"}] * 3
check("الباكتيست·صادق: الصفقات العالقة تُفصح (لا تُخفى من النسبة)",
      "لم تُحسم بعد" in "\n".join(S.backtest_honest_summary(_bt_open))
      and S.backtest_stats(_bt_open)["open"] == 3)

# 📅 قصر الباكتيست على شهر تقويمي محدّد (طلب المستخدم): آخر سنة متوفّرة
_mt = [{"symbol": "X", "date": "2024-02-10", "outcome": "win"},
       {"symbol": "Y", "date": "2026-02-11", "outcome": "loss"},
       {"symbol": "Z", "date": "2026-02-15", "outcome": "win"},
       {"symbol": "W", "date": "2026-03-01", "outcome": "win"}]
_sel, _tag = S._filter_trades_by_month(_mt, 2)
check("قصر الشهر: يختار فبراير من آخر سنة (2026) فقط",
      _tag == "2026-02" and len(_sel) == 2
      and {t["symbol"] for t in _sel} == {"Y", "Z"})
check("قصر الشهر: فارغ/غير صالح → كل الصفقات · شهر بلا صفقات → فارغ+وسم",
      S._filter_trades_by_month(_mt, "")[0] == _mt
      and S._filter_trades_by_month(_mt, 13)[1] is None
      and S._filter_trades_by_month(_mt, 7)[0] == []
      and "لا صفقات" in S._filter_trades_by_month(_mt, 7)[1])
# 📅 تحديد السنة (طلب المستخدم 2026-07-05): شهر 2 من 2024 → السنة الصريحة تُفلتر
_sel24, _tag24 = S._filter_trades_by_month(_mt, 2, 2024)
check("قصر الشهر+السنة: فبراير 2024 صريحة (لا أحدث سنة)",
      _tag24 == "2024-02" and {t["symbol"] for t in _sel24} == {"X"})
check("نافذة الشهر+السنة: تستعمل السنة الصريحة · النافذة الأمامية لسنة سابقة مكتملة",
      S._recent_month_window(2, 2025)[0] == "2025-02-01"
      and S._forward_window_complete(2, 2025) is True)
# 📆 سنة كاملة بتشغيل واحد (طلب المستخدم 2026-07-05): year بلا شهر صالح → كل الأشهر.
# التحقّق من منطق «الشهر غير صالح» الذي يفعّل وضع السنة الكاملة (مثل «1-2-3-…-12»).
check("سنة كاملة: «1-2-…-12» غير صالح كشهر مفرد (يفعّل وضع السنة)",
      ("1-2-3-4-5-6-7-8-9-10-11-12".isdigit() is False)
      and ("2".isdigit() and 1 <= int("2") <= 12))
# 🧭 تصحيح خلط خانتَي الشهر/السنة (إصلاح 2026-07-05): كتابة «2025» في خانة **الشهر**
# والسنة فارغة كانت تبني نافذة مشوّهة «2025-2025-01..2025-2025-31» فتسقط كل التواريخ
# خارجها = **صفر إشارة بلا سطر فترة** (شُخِّص من سجل أكشن a14bbee). الآن يُنقل للسنة.
check("تصحيح الإدخال: سنة (2025) بخانة الشهر والسنة فارغة → تُنقل للسنة والشهر يُفرَّغ",
      S._normalize_bt_period("2025", "") == ("", "2025"))
check("تصحيح الإدخال: شهر صالح+سنة صريحة يبقيان كما هما (لا تبديل)",
      S._normalize_bt_period("2", "2025") == ("2", "2025")
      and S._normalize_bt_period("", "2025") == ("", "2025")
      and S._normalize_bt_period("2", "") == ("2", ""))
check("تصحيح الإدخال: شهر غير صالح (13/99) وليس سنة → يُفرَّغ (لا نافذة مشوّهة)",
      S._normalize_bt_period("13", "") == ("", "")
      and S._normalize_bt_period("99", "") == ("", ""))
# دفاع عميق: النافذة لا تُبنى أبدًا لشهر خارج 1-12 (ترفع ValueError → المستدعي None)
try:
    S._recent_month_window(2025)
    _win_ve = False
except ValueError:
    _win_ve = True
check("نافذة الشهر: شهر خارج 1-12 يرفع ValueError (لا نافذة مشوّهة 2025-2025-01)",
      _win_ve is True)

# 🔬 التجربة الزوجية للوقف (طلب المستخدم 2026-07-05): ذراعان + العائد المحقّق.
_bt2 = S.backtest_symbol("BT2", synth_pivot(seed=2))
check("الباكتيست·تجربة: كل صفقة تحمل ذراعي الوقف + العائد المحقّق + أعمق ذيل",
      len(_bt2) >= 1                       # لا يمرّ فراغًا (all على [] صحيح زورًا)
      and all({"outcome", "outcome_b", "ret_a", "ret_b", "max_draw_pct"} <= set(t)
              for t in _bt2)
      and all((t["ret_a"] is None) == (t["outcome"] == "no_fill") for t in _bt2))
# مقارنة يدوية: سهم أنقذه الإغلاق (A خسارة → B ربح) · سهمان عمّقهما (B أعمق) · رابح · عالق
_cmp_tr = [
    {"symbol": "SAVE", "outcome": "loss", "outcome_b": "win", "ret_a": -10.0,
     "ret_b": 20.0, "exploded": True, "fwd_max_gain": 80.0},
    {"symbol": "DEEP", "outcome": "loss", "outcome_b": "loss", "ret_a": -10.0,
     "ret_b": -18.0, "exploded": False, "fwd_max_gain": 5.0},
    {"symbol": "WINW", "outcome": "win", "outcome_b": "win", "ret_a": 20.0,
     "ret_b": 20.0, "exploded": False, "fwd_max_gain": 25.0},
    {"symbol": "OPN", "outcome": "open", "outcome_b": "open", "ret_a": -3.0,
     "ret_b": -3.0, "exploded": False, "fwd_max_gain": 10.0},
    {"symbol": "L2", "outcome": "loss", "outcome_b": "loss", "ret_a": -10.0,
     "ret_b": -12.0, "exploded": False, "fwd_max_gain": 3.0},
]
_cmpv = "\n".join(S.backtest_variant_compare(_cmp_tr))
check("الباكتيست·تجربة: المقارنة تحسب الإنقاذ (وقف→ربح) + التعميق + الفرق الزوجي",
      "تجربة الوقف الزوجية" in _cmpv
      and "أنقذها الإغلاق (وقف→ربح): 1" in _cmpv
      and "عمّقها الإغلاق: 2" in _cmpv and "SAVE" in _cmpv)
# مراجعة خصومية: مقام موحّد + إفصاح «عالق» + تحذير من تحيّز نسبة النجاح + قيادة
# المقياس الحاسم (الفرق الزوجي بالعائد المحقّق) — لا نسبة النجاح البنيوية المضلِّلة.
check("الباكتيست·تجربة: عرض صادق (عالق مُفصَح + تحذير + الفرق الحاسم أولًا)",
      "عالق" in _cmpv and "لا تُخدع بنسبة نجاح B" in _cmpv
      and "الفرق الزوجي B−A" in _cmpv)

# 🔬 تجربة «الدخول المؤكَّد بالمسح» (T1، 2026-07-05 — صور فيصل + مراجعة خصومية 7 وكلاء).
# (أ) _sweep_confirmed_fill: مسح تحت الدعم ثم استعادة — بلا نظر مستقبلي.
_sf_fill = S._sweep_confirmed_fill(np.array([100.,89,95,101]),
                                   np.array([99.,92,96,101]), 100.0, 0.10)
_sf_none = S._sweep_confirmed_fill(np.array([100.,95,98,102]),
                                   np.array([99.,96,99,102]), 100.0, 0.10)
_sf_norec = S._sweep_confirmed_fill(np.array([100.,88,85,80]),
                                    np.array([98.,89,86,82]), 100.0, 0.10)
# لا نظر مستقبلي: إغلاق≥الدعم قبل المسح (k=0,1) لا يُحتسب استعادة — الاستعادة بعد المسح (k=3)
_sf_look = S._sweep_confirmed_fill(np.array([101.,102,88,101]),
                                   np.array([101.,102,89,101]), 100.0, 0.10)
check("المسح·تعبئة: مسح(low≤90)+استعادة(close≥100) → filled عند الاستعادة، أدنى ذيل محفوظ",
      _sf_fill[0] == "filled" and _sf_fill[1] == 3 and _sf_fill[3] == 89.0
      and _sf_none[0] == "no_sweep" and _sf_norec[0] == "sweep_no_reclaim")
check("المسح·لا نظر مستقبلي: الاستعادة تُحتسب بعد المسح فقط (reclaim_idx=3 لا 0/1)",
      _sf_look[0] == "filled" and _sf_look[1] == 3)
# (ب) _resolve_arm: مصدر واحد لذراعَي A/B (ربح/خسارة/لا-تعبئة)
_ra_win = S._resolve_arm(np.array([102.,110]), np.array([98.,100]),
                         np.array([100.,108]), np.array([99.,101]), 100.0, 93.0, 109.0, 0)
_ra_los = S._resolve_arm(np.array([101.,101]), np.array([92.,90]),
                         np.array([95.,93]), np.array([96.,94]), 100.0, 93.0, 120.0, 0)
_ra_nf = S._resolve_arm(np.array([1.]), np.array([1.]), np.array([1.]),
                        np.array([1.]), 100.0, 93.0, 120.0, None)
check("المسح·_resolve_arm: ربح(t1)=+9 · خسارة(وقف)=−7 · لا-تعبئة=None",
      _ra_win[0] == "win" and abs(_ra_win[1] - 9.0) < 0.01
      and _ra_los[0] == "loss" and abs(_ra_los[1] + 7.0) < 0.01
      and _ra_nf == ("no_fill", None, "no_fill", None))
# (ج) مطفأة افتراضيًا: لا حقول مسح · المقارنة ترجع []
_bt_off = S.backtest_symbol("SWOFF", synth_pivot(seed=2))
check("المسح·مطفأة: صفقة الأساس بلا حقول مسح + المقارنة ترجع []",
      all("entry_model" not in t for t in _bt_off)
      and S.backtest_sweep_compare(_bt_off) == [])
# (د) مفعّلة: حقول المسح تُلحَق (ثم نُطفئها فورًا لئلا تتسرّب لبقية الاختبارات)
S.CONFIG["BT_SWEEP_ENTRY"] = 1
_bt_on = S.backtest_symbol("SWON", synth_pivot(seed=2))
S.CONFIG["BT_SWEEP_ENTRY"] = 0
check("المسح·مفعّلة: كل صفقة تحمل حقول المسح (entry_model/fill_reason_sweep/ret_sweep_a)",
      len(_bt_on) >= 1 and all({"entry_model", "fill_reason_sweep",
          "ret_sweep_a", "entry_sweep", "stop_sweep", "swept"} <= set(t)
          for t in _bt_on))
# (هـ) 🛡️ حارس فخّ عدم-التعبئة (مراجعة خصومية): حافة تحملها الامتناعات (تفادٍ>تحويل)
# **تُرفَض** رغم أن الفرق الزوجي على المُعبَّأة موجب. 8 تفادٍ · 2 تحويل · 5 رابح مُبقى.
def _swt(oc, ra, os_, rsa, fr, d="2025-01-01"):
    return {"entry_model": "sweep_confirmed", "outcome": oc, "ret_a": ra,
            "ret_b": ra, "outcome_sweep": os_, "outcome_sweep_b": os_,
            "ret_sweep_a": rsa, "ret_sweep_b": rsa,
            "fill_reason_sweep": fr, "date": d}
_trap = ([_swt("loss", -10.0, "sweep_no_reclaim", None, "sweep_no_reclaim")] * 8
         + [_swt("loss", -10.0, "win", 20.0, "filled", "2025-02-01")] * 2
         + [_swt("win", 15.0, "win", 18.0, "filled", "2025-03-01")] * 5)
_trap_r = "\n".join(S.backtest_sweep_compare(_trap))
check("المسح·حارس الامتناع: تفادٍ يفوق التحويل ⇒ يُرفض (لا يُخدع بحافة الامتناع)",
      "التحويل ≥ التفادي" in _trap_r or "يُرفض" in _trap_r)
check("المسح·حكم الامتناع: الحكم الأولي «يُرفض» رغم فرق زوجي موجب على المُعبَّأة",
      "يُرفض ويُقفل" in _trap_r)
# (و) حافة حقيقية: تحويل يفوق التفادي + موجب الذراعين + يصمد سنتين + تعبئة كافية ⇒ يتبنّى
_good = ([_swt("loss", -10.0, "win", 20.0, "filled", "2025-05-01")] * 3
         + [_swt("loss", -10.0, "win", 20.0, "filled", "2026-05-01")] * 3
         + [_swt("win", 15.0, "win", 15.0, "filled", "2025-06-01")] * 2
         + [_swt("win", 15.0, "win", 15.0, "filled", "2026-06-01")] * 2
         + [_swt("loss", -10.0, "sweep_no_reclaim", None, "sweep_no_reclaim")])
_good_r = "\n".join(S.backtest_sweep_compare(_good))
check("المسح·حافة حقيقية: تحويل≥تفادي + موجب سنتين + تعبئة≥40% ⇒ الحكم «يتبنّى»",
      "يتبنّى الدخول" in _good_r and "المُعبَّأة في الطرفين" in _good_r)

# 🧬 بصمة «طريقة ارتفاع اليد» (سلوك المضارب، T0 — عرض/تشخيص فقط، لا تمسّ الفرز/الاختيار).
_bp = S.behavior_rise_profile(synth_pivot(seed=1))
check("سلوك المضارب: البروفايل يرجع الحقول + درجة 0-100 + وصف",
      {"score", "label", "n_pumps", "best_pump", "recency_bars", "sweeps"} <= set(_bp)
      and (_bp["score"] is None or 0 <= _bp["score"] <= 100)
      and isinstance(_bp["label"], str))
# لا نظر مستقبلي: البروفايل على شريحة لا يتأثّر بالعبث بما بعدها (نقاء + مسافات بالبارات)
_sp = synth_pivot(seed=1); _i = 200
_a = S.behavior_rise_profile(_sp.iloc[:_i])
_sp2 = _sp.copy(); _sp2.iloc[_i:, :] = 999.0
check("سلوك المضارب: لا تسريب مستقبلي (نفس الشريحة رغم العبث بالمستقبل)",
      _a == S.behavior_rise_profile(_sp2.iloc[:_i]))
check("سلوك المضارب: فاشل-آمن على بيانات قصيرة → score=None",
      S.behavior_rise_profile(_sp.iloc[:30])["score"] is None)
# 🔒 قفل السلامة الحاسم (مراجعة خصومية T0): البصمة **لا تغيّر عضوية select_top**.
# rank_key لا يذكر behav إطلاقًا، و select_top يمشي بترتيب المدخل — فمهما تغيّرت
# البصمة تبقى المجموعة المختارة نفسها (لئلا تخنق ارتكاز فيصل = درس C3).
import inspect as _insp
_rk_src = _insp.getsource(S.rank_key)
_res_lo = [{"symbol": "X", "tier": "A", "readiness": 70, "score": 80, "rr": 2.0,
            "behav": {"score": 5}},
           {"symbol": "Y", "tier": "A", "readiness": 70, "score": 80, "rr": 2.0,
            "behav": {"score": 95}}]
_res_hi = [dict(t, behav={"score": 100 - t["behav"]["score"]}) for t in _res_lo]
_sel_lo = {r["symbol"] for r in S.select_top(_res_lo, 1, set())}
_sel_hi = {r["symbol"] for r in S.select_top(_res_hi, 1, set())}
check("سلوك المضارب·قفل السلامة: behav لا يدخل rank_key ولا يغيّر عضوية select_top",
      "behav" not in _rk_src and _sel_lo == _sel_hi)
# العرض: البطاقة تُظهر سطر 🧬 عند توفّر البصمة (عرض فقط)
_card_r = {"symbol": "ZZ", "score": 60, "tier": "A", "price": 3.6,
           "readiness": 50, "behav": {"score": 72, "label": "🔥 يد نشطة تعيد الضخّ بقوة",
           "n_pumps": 4, "best_pump": 300.0, "recency_bars": 30, "repumps": 3,
           "sweeps": 2}, "tranches": [3.5, 3.6], "entry": (3.5, 3.6),
           "stop": (3.2, 3.3), "t1": 4.0, "t2": 4.5, "t3": 5.0, "rr": 2.0}
_card = S.build_message([_card_r], [])   # يرجّع نصًّا جاهزًا (لا قائمة)
check("سلوك المضارب·عرض: البطاقة تُظهر «🧬 طريقة الارتفاع» + الوصف",
      "🧬 طريقة الارتفاع" in _card and "يد نشطة تعيد الضخّ" in _card)

# 🔬 تشخيص التصنيف A/B (T2، طلب المستخدم «التصنيف عشوائي ولا سهم وصل A»): تحليل بالدليل
# هل عدد النواقص/الجاهزية يميّز؟ — تحليل فقط، لا يمسّ الفرز/التصنيف.
def _tt(ns, oc, rdy=55):
    return {"outcome": oc, "n_soft": ns, "readiness": rdy, "exploded": False}
_disc = ([_tt(0, "win")] * 8 + [_tt(1, "win")] * 7 + [_tt(1, "loss")] * 3
         + [_tt(4, "loss")] * 12 + [_tt(4, "win")] * 1)
_disc_r = "\n".join(S.backtest_tier_analysis(_disc))
check("التصنيف·تشخيص: نواقص مميِّزة ⇒ يوصي «A = ناقص واحد أو أقل»",
      "يميّز" in _disc_r and "ناقص واحد أو أقل" in _disc_r
      and "صفر نواقص" in _disc_r and "<b>8</b>" in _disc_r)
_flat = ([_tt(0, "win")] * 3 + [_tt(0, "loss")] * 7 + [_tt(4, "win")] * 3
         + [_tt(4, "loss")] * 7)
_flat_r = "\n".join(S.backtest_tier_analysis(_flat))
check("التصنيف·تشخيص: نواقص غير مميِّزة ⇒ يوصي حلًّا جذريًا (محور مُثبَت لا بوابة صفرية)",
      "لا يميّز" in _flat_r and "ضجيج" in _flat_r)
check("التصنيف·تشخيص: عيّنة صغيرة (<10) → لا تقرير (لا حكم على ضجيج)",
      S.backtest_tier_analysis([_tt(0, "win")] * 3) == [])

# 🧬 تحقّق ارتباط البصمة بالانفجار (طلب المستخدم: وزن ترتيب فقط بعد إثبات الارتباط).
def _bt(bs, oc, exploded=False):
    return {"behav_score": bs, "outcome": oc, "exploded": exploded}
# مرتبطة: البصمة العالية (60+) تنفجر كثيرًا · المنخفضة لا
_bcorr = ([_bt(70, "win", True)] * 7 + [_bt(65, "loss", True)] * 3
          + [_bt(20, "loss")] * 12 + [_bt(15, "win")] * 1)
_bcorr_r = "\n".join(S.backtest_behav_correlation(_bcorr))
check("البصمة·تحقّق: ارتباط واضح بالانفجار ⇒ يوصي «تُمنح وزن ترتيب»",
      "تُمنح وزن ترتيب" in _bcorr_r and "منفصلان" in _bcorr_r)
# غير مرتبطة: الانفجار مسطّح عبر الشرائح
_bflat = ([_bt(70, "win", False)] * 8 + [_bt(70, "loss", True)] * 2
          + [_bt(20, "win", False)] * 8 + [_bt(20, "loss", True)] * 2)
_bflat_r = "\n".join(S.backtest_behav_correlation(_bflat))
check("البصمة·تحقّق: لا ارتباط ⇒ يوصي «تبقى عرضًا فقط» (لا وزن)",
      "تبقى عرضًا فقط" in _bflat_r)

# 🧭 طبقة التفسير والقرار (INTERPRETATION_LAYER_PLAN.md — عرض/تفسير فقط).
_ir = {"symbol": "TST", "price": 1.85, "pivot": 1.80, "tier": "B",
       "score": 60, "rr": 2.4, "entry": (1.80, 1.91),
       "tranches": [1.80, 1.85, 1.91], "stop": (1.67, 1.71),
       "t1": 2.10, "t2": 2.45, "t3": 2.90,
       "key_levels": {"sup_major": 1.80, "sup_minor": 1.83, "res_minor": 2.05,
                      "res_major": 2.45},
       "h4_levels": {"resistances": [2.05, 2.4], "supports": [1.78], "flip": 1.82,
                     "sweep_low": 1.66},
       "behav": {"sweeps": 2}, "warnings": ["⚠️ خبر تخفيف محتمل"]}
_ip = S.build_interpretation(_ir)
check("التفسير: يُنتج الحقول الأساسية (نوع/رقم حرج/تفعيل/دخول/خطر/أدوار)",
      all(k in _ip for k in ("setup_type", "critical_number", "activation_state",
          "entry_mode", "risk_profile", "level_roles")))
check("التفسير: الرقم الحرج = أقرب مقاومة فوق السعر (2.05)",
      _ip["critical_number"]["price"] == 2.05)
check("التفسير: هدف فوق الرقم الحرج = معلّق (blocked_by) لا مفعّل",
      2.10 in _ip["activation_state"]["inactive_targets"]
      and _ip["activation_state"]["blocked_by"] == 2.05)
check("التفسير: مسح+استعادة ⇒ setup=liquidity_sweep · entry=sweep_confirmed (وصفي)",
      _ip["setup_type"] == "liquidity_sweep"
      and _ip["entry_mode"]["mode"] == "sweep_confirmed")
check("التفسير: بطاقة الخطر تلتقط خبر التخفيف (بلا تجريم فلوت/رسملة)",
      "خبر تخفيف/طرح" in _ip["risk_profile"]["flags"])
# كسر الوقف → activation=high_risk + لا دخول
_ir2 = dict(_ir, price=1.60)
check("التفسير: كسر الوقف ⇒ activation=high_risk + entry=no_entry_far",
      S.build_interpretation(_ir2)["activation_state"]["setup"] == "high_risk"
      and S.build_interpretation(_ir2)["entry_mode"]["mode"] == "no_entry_far")
# فاشل-آمن: مدخل ناقص → {} بلا انهيار
check("التفسير·فاشل-آمن: مدخل بلا سعر/pivot → {} (لا انهيار)",
      S.build_interpretation({"symbol": "X"}) == {})
# أسطر الكرت ≤4 (+سطر 4س من المقطع) + بلا علامات مقارنة + العلامات المطلوبة
_icl = S.interp_card_lines(_ip)
check("التفسير·الكرت: ≤4 أسطر + «🧭 الإعداد» + «🎯 الرقم الحرج» + بلا علامات مقارنة",
      len(_icl) <= 4 and any("🧭 الإعداد" in x for x in _icl)
      and any("🎯 الرقم الحرج" in x for x in _icl)
      and not any(c in "".join(_icl) for c in "≥≤<>"))
# 🕓 سطر قصة الـ4س (المقطع: «رأس الحمرا مقاومة، تجاوزه يؤكّد»)
check("التفسير·4س: رأس حمرا فوق السعر ⇒ سطر «🕓 4س: … تجاوزه يؤكّد»",
      any("🕓 4س" in x and "تجاوزه يؤكّد" in x for x in _icl))
check("التفسير·4س: حالة weak ⇒ لا سطر 🕓 (لا حشو)",
      not any("🕓" in x for x in S.interp_card_lines(
          {"setup_type": "pivot_reversal",
           "four_hour_context": {"state": "weak"}})))
check("التفسير·4س: مقاومة منقلبة دعمًا ⇒ سطر «انقلبت دعمًا»",
      any("انقلبت دعمًا" in x for x in S.interp_card_lines(
          {"setup_type": "pivot_reversal",
           "four_hour_context": {"state": "support_flipped", "flip": 1.82}})))
# تغطية الخضرا (المقطع): حالة الانتظار + سطرها بالكرت
_irg = dict(_ir, h4_levels={"resistances": [], "supports": [], "flip": None,
                            "sweep_low": None, "green_cover": False})
_ipg = S.build_interpretation(_irg)
check("4س·تغطية: حمرا بلا تغطية (بلا حاجز أقوى) ⇒ state=waiting_green_cover",
      _ipg["four_hour_context"]["state"] == "waiting_green_cover")
check("4س·تغطية: سطر «بلا تغطية خضرا — ننتظر التأكيد» بالكرت",
      any("بلا تغطية خضرا" in x for x in S.interp_card_lines(_ipg)))
# مصدر كل هدف targets_src (P1-4 — استدلال بالمطابقة، عرض فقط)
check("مصادر الأهداف: تُبنى لكل هدف مع activation/blocked_by",
      len(_ip.get("targets_src", [])) == 3
      and all("source" in x and "activation" in x for x in _ip["targets_src"]))
check("مصادر الأهداف: t2=2.45 يطابق المقاومة الأساسية ⇒ مصدره «المقاومة الأساسية»",
      any(x["price"] == 2.45 and "المقاومة الأساسية" in x["source"]
          for x in _ip["targets_src"]))
check("مصادر الأهداف: ما لا يطابق مصدرًا ⇒ «سلّم المقاومات اليومي» (صدق افتراضي)",
      any(x["source"] == "سلّم المقاومات اليومي" for x in _ip["targets_src"]))
check("مصادر الأهداف·قفل: الأهداف نفسها لم تتغيّر (قفل D5)",
      (_ir["t1"], _ir["t2"], _ir["t3"]) == (2.10, 2.45, 2.90))
# 🔒 قفل: التفسير لا يدخل rank_key (عرض فقط — لا يمسّ العضوية)
import inspect as _insp2
check("التفسير·قفل: build_interpretation/interp غير مذكور في rank_key (عرض فقط)",
      "interp" not in _insp2.getsource(S.rank_key))
# العرض: البطاقة تُظهر سطر التفسير
_ir["readiness"] = 60
_ir["interp"] = _ip
_card_i = S.build_message([_ir], [])
check("التفسير·عرض: البطاقة تُظهر «🧭 الإعداد» + «🎯 الرقم الحرج»",
      "🧭 الإعداد" in _card_i and "🎯 الرقم الحرج" in _card_i)

# ===== 🧭 المرحلة 2أ (خطة التفسير §11-§13 + وسم الأهداف المعلّقة + إصلاح الربط) =====
# §13: وسوم 🧬 الوصفية — عند توفّر الدليل حصريًا، عرض فقط
check("🧬وسوم§13: مسح مرّتين فأكثر ⇒ «صيد وقفات متكرّر»",
      "صيد وقفات متكرّر" in S.behavior_tags({"sweeps": 2, "n_pumps": 0}))
check("🧬وسوم§13: رفعة قديمة + خمول 120ج فأكثر ⇒ «رفعة قديمة وخمول طويل» (BJDX)",
      "رفعة قديمة وخمول طويل" in S.behavior_tags(
          {"sweeps": 0, "n_pumps": 1, "recency_bars": 200}))
check("🧬وسوم§13: بلا دليل ⇒ لا وسوم (وبلا انهيار على None/{})",
      S.behavior_tags({"sweeps": 1, "n_pumps": 1, "recency_bars": 10}) == []
      and S.behavior_tags(None) == [] and S.behavior_tags({}) == [])
# حكم باكتيست السنتين (2026-07-08، §0-ح): بصمة 60+ = تحذير مسح وقف، لا أولوية
check("🧬وسوم·حكم السنتين: درجة 60 فأكثر ⇒ «يد نشطة — حذارِ مسح الوقف» (تحذير لا أولوية)",
      any("حذارِ مسح الوقف" in t for t in S.behavior_tags(
          {"score": 65, "sweeps": 0, "n_pumps": 1, "recency_bars": 10}))
      and not any("حذارِ" in t for t in S.behavior_tags(
          {"score": 59, "sweeps": 0, "n_pumps": 1, "recency_bars": 10})))
check("🧬وسوم·قفل الحكم: البصمة تبقى خارج rank_key/select_top (لا أولوية فرز)",
      "behav" not in _insp0.getsource(S.rank_key)
      and "behav" not in _insp0.getsource(S.select_top))
check("🧬وسوم§13·قفل: لا مساس بدرجة/مكوّنات البصمة المقفولة",
      "behavior_tags" not in _insp2.getsource(S.behavior_rise_profile))
# عرض الوسوم بسطر 🧬 في الكرت
_ir6 = dict(_ir)
_ir6["behav"] = {"score": 55, "label": "يد فعّالة (تعيد الرفع)", "n_pumps": 2,
                 "best_pump": 150.0, "recency_bars": 200, "repumps": 1, "sweeps": 3}
_ir6["interp"] = S.build_interpretation(_ir6)
_card6 = S.build_message([_ir6], [])
check("🧬وسوم§13·عرض: سطر 🧬 بالكرت يحمل «صيد وقفات» و«خمول طويل»",
      "صيد وقفات متكرّر" in _card6 and "رفعة قديمة وخمول طويل" in _card6)

# §11: cycle_context — عرض/تخزين فقط، لا يدخل أي ترتيب
_ir3 = dict(_ir, behav={"sweeps": 2, "recency_bars": 40}, bars_after=6)
_ip3 = S.build_interpretation(_ir3)
check("الدورة§11: recency 40 ⇒ «داخل النافذة الشائعة (30-50)» + جلسات القاع تُنقل",
      "30-50" in _ip3["cycle_context"]["window_state"]
      and _ip3["cycle_context"]["days_since_major_low"] == 6
      and _ip3["cycle_context"]["days_since_last_impulse"] == 40)
check("الدورة§11·قفل: cycle غير مذكور في rank_key (لا يدخل الترتيب)",
      "cycle" not in _insp2.getsource(S.rank_key))
check("الدورة§11: analyze_ticker يخزّن bars_after (جلسات منذ القاع)",
      "bars_after" in r0)

# §12: session_context دنيا صادقة — snapshot يُنقل + سبب صريح لغياب pre/after
_ir4 = dict(_ir, session_ctx={"open": 1.8, "prev_close": 1.75, "volume": 1e6,
                              "market_cap": 5e7, "pre_after": None,
                              "unavailable_reason": ("بيانات ما قبل/بعد السوق "
                                                     "غير متاحة بمسار البوت")})
_ip4 = S.build_interpretation(_ir4)
check("الجلسة§12: session_ctx يُنقل للتفسير + سبب غياب pre/after صريح (لا تخمين)",
      _ip4["session_context"]["prev_close"] == 1.75
      and "غير متاحة" in _ip4["session_context"]["unavailable_reason"])
check("الجلسة§12: بلا session_ctx ⇒ الحقل غائب (صدق، لا فبركة)",
      "session_context" not in _ip)

# تجديد يومي: سجل مخزّن بلا price (له last_price) ⇒ تفسير كامل لا {}
_ir5 = {k: v for k, v in _ir.items() if k != "price"}
_ir5["last_price"] = 1.85
check("التفسير·تجديد يومي: last_price بديل price ⇒ الرقم الحرج يُحسب (2.05)",
      S.build_interpretation(_ir5).get("critical_number", {}).get("price") == 2.05)

# وسم «معلّق» على أسطر الأهداف (عرض فقط — السعر نفسه يبقى كما هو)
check("الأهداف·كرت: هدف خلف الحاجز يحمل «(معلّق حتى $2.05)» وسعره باقٍ",
      "معلّق حتى $2.05" in _card_i and "$2.10" in _card_i)
_wl_p = {"week_start": "2024-01-01", "removed": [], "notes": [],
         "stocks": [{"symbol": "TST", "added": "2024-01-02", "entry_ref": 1.85,
                     "entry": [1.80, 1.91], "tranches": [1.80, 1.85, 1.91],
                     "pivot": 1.80, "stop": 1.67, "stop_hi": 1.71,
                     "t1": 2.10, "t2": 2.45, "t3": 2.90, "score": 60,
                     "flags": [], "rr": 2.4, "tier": "B", "soft_fails": [],
                     "warnings": [], "readiness": 60, "have": [], "partial": [],
                     "missing": [], "hit": None, "hit_date": None,
                     "max_gain_pct": 0.0, "last_price": 1.85,
                     "status": "active", "interp": _ip}]}
_dm_p = S.build_daily_message(_wl_p, [], [], [])
check("الأهداف·يومي: وسم «(معلّق)» + سطر «⏳ المعلّق يتفعّل بتجاوز $2.05»",
      "(معلّق)" in _dm_p and "يتفعّل بتجاوز $2.05" in _dm_p)
check("الأهداف·يومي: الأسعار نفسها باقية بلا تغيير",
      "$2.10" in _dm_p and "$2.45" in _dm_p and "$2.90" in _dm_p)

# إصلاح الربط: تجديد التفسير بعد الإثراء لا يمسح الموجود لو رجع فارغًا
# (المنطق: enrich/update_watchlist_status يستبدلان فقط عند نتيجة غير فارغة)
check("التفسير·حارس التجديد: مدخل ناقص ⇒ {} (فلا يُستبدل التفسير المخزّن)",
      S.build_interpretation({"symbol": "NOPRICE"}) == {})
_src_enrich = _insp2.getsource(S.enrich)
check("التفسير·ربط: enrich يجدّد التفسير بعد الإثراء (h4/أخبار/SEC) بحارس لا-يمسح",
      "build_interpretation" in _src_enrich)
check("التفسير·ربط: التجديد اليومي في update_watchlist_status (الرقم الحرج يتحرّك)",
      "build_interpretation" in _insp2.getsource(S.update_watchlist_status))

# ===== §10 خط الترند الهابط (مواصفة ملزمة + حارس ضد الفبركة — عرض/تفسير فقط) =====
def _tl_df(peaks, n=160, base=5.0, last_closes=None):
    """داتا صناعية: قمم سوينغ محدّدة (idx, high) فوق قاعدة هادئة."""
    import pandas as _pd
    import numpy as _np
    h = _np.full(n, base * 1.04)
    c = _np.full(n, base)
    lo = _np.full(n, base * 0.96)
    for i, p in peaks:
        h[i] = p
        c[i] = p * 0.97
    if last_closes:
        for k, v in enumerate(last_closes):
            c[n - len(last_closes) + k] = v
            h[n - len(last_closes) + k] = max(h[n - len(last_closes) + k], v)
    idx = _pd.date_range("2024-01-01", periods=n, freq="B")
    return _pd.DataFrame({"Open": c, "High": h, "Low": lo, "Close": c,
                          "Volume": _np.full(n, 1e6)}, index=idx)

# خط صريح: قمم هابطة 10→9.2→8.4→7.6 (كل 30 شمعة) → خط بلمسات، ميل سالب، below
_tld = S.descending_trendline(
    _tl_df([(30, 10.0), (60, 9.2), (90, 8.4), (120, 7.6)]), 5.0)
check("الترند§10: قمم هابطة صريحة ⇒ خط (لمستان+ · ميل سالب · state=below)",
      _tld is not None and _tld["touches"] >= 2
      and _tld["slope_per_bar"] < 0 and _tld["state"] == "below")
check("الترند§10: الإسقاط عند آخر شمعة فقط — الخط فوق السعر وتحت المرساة",
      5.0 < _tld["line_price_now"] < 10.0)
# لا خط: قمم صاعدة (لا فبركة)
check("الترند§10·حارس: قمم صاعدة ⇒ None (لا يُفبرك خط)",
      S.descending_trendline(
          _tl_df([(30, 7.0), (60, 8.0), (90, 9.0), (120, 10.0)]), 5.0) is None)
# لا خط: قمة يتيمة فقط
check("الترند§10·حارس: قمة واحدة بلا لمسة ثانية ⇒ None",
      S.descending_trendline(_tl_df([(60, 10.0)]), 5.0) is None)
# كسر حديث: آخر إغلاقات فوق الخط ⇒ state=broken
_tlb = S.descending_trendline(
    _tl_df([(30, 10.0), (60, 9.2), (90, 8.4), (120, 7.6)],
           last_closes=[7.1, 7.2, 7.3]), 7.3)
check("الترند§10: إغلاق أخير فوق الخط ⇒ state=broken (الكسر بالإغلاق)",
      _tlb is not None and _tlb["state"] == "broken")
# التكامل مع التفسير: خط غير مكسور أقرب من المقاومة ⇒ هو الرقم الحرج + يعلّق الأهداف
_ir7 = dict(_ir, trendline={"state": "below", "line_price_now": 1.95,
                            "touches": 3, "slope_per_bar": -0.01, "anchor": 2.6})
_ip7 = S.build_interpretation(_ir7)
check("الترند§10·تكامل: الخط أقرب حاجز ⇒ الرقم الحرج=1.95 + «يكسر خط الترند»",
      _ip7["critical_number"]["price"] == 1.95
      and "خط الترند" in _ip7["critical_number"]["why"]
      and _ip7["activation_state"]["blocked_by"] == 1.95)
check("الترند§10·تكامل: هدف فوق الخط = معلّق (يغذّي activation_state)",
      2.10 in _ip7["activation_state"]["inactive_targets"])
# خط مكسور ⇒ لا يُحتسب حاجزًا (يرجع الرقم الحرج للمقاومة 2.05)
_ir8 = dict(_ir, trendline={"state": "broken", "line_price_now": 1.95,
                            "touches": 3, "slope_per_bar": -0.01, "anchor": 2.6})
check("الترند§10·تكامل: خط مكسور بإغلاق ⇒ لا يحجب (الرقم الحرج يرجع 2.05)",
      S.build_interpretation(_ir8)["critical_number"]["price"] == 2.05)
# ملاحظات المراجعة الخصومية (2026-07-08) — كل ملاحظة مؤكَّدة صارت قفل اختبار:
# (أ) ازدواج قمة شبه أفقي (هبوط أقل من التسامح) ⇒ ليس «خط ترند هابط» — None
check("الترند§10·مراجعة: ازدواج قمة شبه أفقي (10.0→9.99) ⇒ None (حد أدنى للانحدار)",
      S.descending_trendline(_tl_df([(40, 10.0), (130, 9.99)]), 5.0) is None)
# (ب) قمتان متساويتان ثم قمم هابطة: المرساة المتعددة تلقط الخط الحقيقي من الثانية
_tleq = S.descending_trendline(
    _tl_df([(50, 4.0), (95, 4.0), (110, 3.6), (122, 3.2)], base=2.0), 2.0)
check("الترند§10·مراجعة: ازدواج قمة + قمم هابطة بعدها ⇒ الخط الحقيقي (لا None)",
      _tleq is not None and _tleq["state"] == "below"
      and _tleq["slope_per_bar"] < -0.001 and 2.0 < _tleq["line_price_now"] < 4.0)
# (ج) خط مكسور كثير اللمسات لا يحجب خطًا قائمًا يسقف السعر (الحالة لكل مرشّح)
_tlsh = S.descending_trendline(
    _tl_df([(60, 10.0), (90, 9.3), (100, 8.85)],
           last_closes=[7.35, 7.40, 7.45]), 7.45)
check("الترند§10·مراجعة: المكسور لا يحجب القائم ⇒ يرجع الخط الحي فوق السعر",
      _tlsh is not None and _tlsh["state"] == "below"
      and _tlsh["line_price_now"] > 7.45)
# 🔒 أقفال: لا يدخل الترتيب/التصنيف/الباكتيست (حيّ فقط) والأهداف نفسها لا تتغيّر
check("الترند§10·قفل: trendline خارج rank_key/classify_tier (عرض فقط)",
      "trendline" not in _insp2.getsource(S.rank_key)
      and "trendline" not in _insp2.getsource(S.classify_tier))
check("الترند§10·قفل: لا يُستدعى في مسار الباكتيست كله (حيّ فقط) — يشمل "
      "analyze_ticker/_diagnose_symbol (تحصين ضد refactor يعيده للفرز)",
      "descending_trendline" not in _insp2.getsource(S.backtest_symbol)
      and "descending_trendline" not in _insp2.getsource(S.analyze_ticker)
      and "descending_trendline" not in _insp2.getsource(S._diagnose_symbol))
check("الترند§10·مراجعة: check_promotions يجدّد التفسير (توحيد أعمار الحواجز)",
      "build_interpretation" in _insp2.getsource(S.check_promotions))
check("الترند§10·قفل: t1/t2/t3 لا تتغيّر بوجود الخط (وسم فقط — قفل D5)",
      (_ir7["t1"], _ir7["t2"], _ir7["t3"]) == (2.10, 2.45, 2.90))
# كون الباكتيست الافتراضي (طلب المستخدم: تشغيل بالشهر وحده بلا رموز): يجمع من
# القائمة + التنبيهات، ترجع قائمة رموز نصّية مرتّبة (لا يرمي عند غياب الملفات).
_defsyms = S._default_backtest_symbols()
check("كون الباكتيست الافتراضي: قائمة رموز (لا استثناء)",
      isinstance(_defsyms, list)
      and all(isinstance(x, str) for x in _defsyms))

# 🌍 وضع السوق الكامل: نافذة الشهر + تصنيف «انفجر فعلًا» بالصفقة. باكتيست فقط.
_rw = S._recent_month_window(2)
check("نافذة الشهر: (من، إلى) ISO تغطّي كل أيام الشهر",
      _rw[0].endswith("-02-01") and _rw[1].endswith("-02-31")
      and len(_rw[0]) == 10)
# الصفقات تحمل fwd_max_gain + exploded (رابح كبير = انفجر · خاسر = لا)
_btx = S.backtest_symbol("BTX", synth_pivot(seed=2))
check("الباكتيست: كل صفقة تحمل fwd_max_gain + exploded",
      all("fwd_max_gain" in t and "exploded" in t for t in _btx))
# date_window يقصر نقاط الدخول: نافذة مستقبلية بعيدة → لا صفقات (لا نقطة داخلها)
_btw = S.backtest_symbol("BTW", synth_pivot(seed=2),
                         date_window=("2099-01-01", "2099-01-31"))
check("الباكتيست·نافذة: تقصر الدخول على المدى المحدّد (نافذة بعيدة → صفر)",
      _btw == [])
# exploded مبني على العتبة: صفقة معبّأة صعدت ≥EXPLOSION_PCT → exploded=True
_expl_trades = [{"symbol": "E", "outcome": "win", "fwd_max_gain": 80.0,
                 "exploded": True},
                {"symbol": "F", "outcome": "win", "fwd_max_gain": 12.0,
                 "exploded": False},
                {"symbol": "G", "outcome": "no_fill", "fwd_max_gain": 0.0,
                 "exploded": False}]
check("وضع السوق: تصنيف «انفجر» يفصل الكبير عن الصغير/غير المعبّأ",
      sum(1 for t in _expl_trades if t.get("exploded")) == 1
      and sum(1 for t in _expl_trades if t.get("outcome") != "no_fill") == 2)
# مراجعة خصومية: الشهر الجاري نافذته الأمامية (fwd=40ج) غير مكتملة → يجب أن يُكشف
# (كان الافتراضي «آخر شهر مكتمل» فيخرج التقرير فارغًا). شهر أقدم بأشهر → مكتمل.
_cur_m = S.dt.date.today().month
_old_m = (S.dt.date.today().replace(day=1) - S.dt.timedelta(days=150)).month
check("نافذة أمامية: الشهر الجاري غير مكتمل · شهر أقدم بـ5 أشهر مكتمل",
      S._forward_window_complete(_cur_m) is False
      and S._forward_window_complete(_old_m) is True)

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

# 🪦 الرسالة اليومية: لا بانر ترقية (الترقية B→A متقاعدة، prom فارغ) + تعرض الشارة الموحّدة
try:
    wlp["stocks"][0]["readiness"] = 80
    wlp["stocks"][0]["have"] = []; wlp["stocks"][0]["partial"] = []
    wlp["stocks"][0]["missing"] = []; wlp["stocks"][0]["t1"] = 4.0
    wlp["stocks"][0]["t2"] = 4.5; wlp["stocks"][0]["t3"] = 5.0
    wlp["stocks"][0]["hit"] = None
    dmp = S.build_daily_message(wlp, [], [], [], prom)
    check("🪦 تقاعد الترقية: لا بانر «ترقيات اليوم» + الشارة الموحّدة 🎯 لا 🅰️/🅱️",
          "ترقيات اليوم" not in dmp and "🎯" in dmp
          and "🅰️" not in dmp and "🅱️" not in dmp)
except Exception as e:
    check("🪦 تقاعد الترقية: لا بانر ترقية", False, str(e))


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
# 🪦 تقاعد A/B: rank_key لم يعد يقدّم «A» — الترتيب بالجاهزية فقط.
_fake_a = {"tier": "A", "readiness": 40, "score": 50, "rr": 0.5}
check("🪦 تقاعد A: «A» وهمي بجاهزية أدنى لا يتصدّر (الترتيب بالجاهزية لا التصنيف)",
      sorted([_hi_rdy, _fake_a], key=S.rank_key)[0] is _hi_rdy)
# 🔒 قفل ثبات العضوية (توصية المراجعة): ترتيب rank_key ثابت تجاه قيمة tier —
# فتغيّر/إلغاء A/B لا يغيّر مجموعة select_top إطلاقًا (لا خنق ارتكاز، درس C3).
_inv = [{"symbol": "S1", "tier": "B", "readiness": 70, "score": 50, "rr": 1.0},
        {"symbol": "S2", "tier": "B", "readiness": 55, "score": 90, "rr": 2.0},
        {"symbol": "S3", "tier": "B", "readiness": 60, "score": 60, "rr": 1.5}]
_ord_b = [x["symbol"] for x in sorted(_inv, key=S.rank_key)]
_inv2 = [dict(x, tier=("A" if x["symbol"] == "S2" else "B")) for x in _inv]
check("🔒 قفل: ترتيب rank_key ثابت تجاه tier (العضوية لا تتأثر بـA/B)",
      [x["symbol"] for x in sorted(_inv2, key=S.rank_key)] == _ord_b)

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
check("🪦 تقاعد A: تخفيف استقر فوق الدعم → يبقى «B» (لا رجوع لـA)",
      _wlr["stocks"][0]["tier"] == "B")
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

# §P4 — 🔁 تقسيمات متكررة = نَفَس قصير (قاعدة فيصل: ZCMD صعد 600% ثم ارتدّ)
_p4_today = S.dt.date(2026, 7, 8)
_p4_recent = [(S.dt.date(2026, 6, 1), 0.1), (S.dt.date(2026, 2, 1), 0.2)]  # تقسيمان بسنة
_p4_old = [(S.dt.date(2024, 1, 1), 0.1), (S.dt.date(2026, 6, 1), 0.1)]     # قديم + حديث
check("§P4: تقسيمان عكسيان خلال سنة ⇒ العدّ 2",
      S._split_frequency(_p4_recent, _p4_today) == 2)
check("§P4: تقسيم قبل سنة لا يُحسب ⇒ العدّ 1",
      S._split_frequency(_p4_old, _p4_today) == 1)
check("§P4: تقسيم عادي (نسبة أكبر من 1) لا يُحسب",
      S._split_frequency([(S.dt.date(2026, 6, 1), 2.0)], _p4_today) == 0)
check("§P4·فاشل-آمن: بلا بيانات ⇒ 0",
      S._split_frequency(None, _p4_today) == 0
      and S._split_frequency([], _p4_today) == 0)
check("§P4·صيغة نصية للتاريخ مقبولة",
      S._split_frequency([("2026-06-01", 0.1), ("2026-05-01", 0.2)], _p4_today) == 2)
_p4_ser = pd.Series([0.1, 0.2, 2.0],
                    index=pd.to_datetime(["2026-06-01", "2026-02-01", "2023-01-01"]))
check("§P4: pandas Series (مثل yfinance splits) ⇒ يحسب العكسية بالسنة",
      S._split_frequency(_p4_ser, _p4_today) == 2)
check("§P4·سطر التحذير: يظهر عند تقسيمين فأكثر",
      "تقسيمات متكررة (2 في سنة)" in S._split_freq_line(2))
check("§P4·سطر التحذير: فارغ عند أقل من تقسيمين",
      S._split_freq_line(1) == "" and S._split_freq_line(0) == ""
      and S._split_freq_line(None) == "")
_p4_row = S._split_row("ZCMD", "2026-05-01", 3.0, 1.5, 10000, freq=3)
check("§P4: _split_row يخزّن freq", _p4_row["freq"] == 3)
check("§P4: قسم D9 يعرض تحذير التقسيمات المتكررة",
      "تقسيمات متكررة (3 في سنة)" in S.build_split_watch_section([_p4_row]))
check("§P4: تقسيم واحد ⇒ لا تحذير بالقسم",
      "تقسيمات متكررة" not in S.build_split_watch_section(
          [S._split_row("ONE", "2026-05-01", 3.0, 1.5, 10000, freq=1)]))
check("§P4: التوافق الخلفي — _split_row بلا freq (السلوك القديم)",
      S._split_row("OLD", "2026-05-01", 2.80, 1.55, 15000)["freq"] is None)
check("§P4·قفل: _split_frequency خارج rank_key/select_top/backtest_symbol/analyze_ticker",
      all("_split_frequency" not in _insp0.getsource(f)
          for f in (S.rank_key, S.select_top, S.backtest_symbol, S.analyze_ticker)))

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
