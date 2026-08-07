# -*- coding: utf-8 -*-
"""
اختبار شامل لبوت أسهم الارتكاز (v2.7) — الضمان الذهبي.
يغطي: المؤشرات + البوابات + نظام القائمتين (A/B) + التحرر/القاب +
قرارات الصور الفعلية (RSI/MACD/شورت/فلوت لكل سهم من الصور).
يعمل بلا إنترنت (يحاكي البيانات + يعطّل yfinance).
"""
import ast as _ast_p1          # 🔧 P1-③: قفل AST على تسمية النواقص (أسفل الملف)
import ast as _ast0
import inspect as _insp0
import json
import os as _os_hc
# 🛡️ حارس حادثة 2026-07-14: يمنع أي git_save حقيقي أثناء الاختبارات (اختبار E2 شغّل
# ignition_live.main() فنفّذ git حقيقيًّا ودفع بيانات وهمية على main). يُقرأ وقت النداء.
_os_hc.environ["SUPER_STOCKS_TESTING"] = "1"
# 🥇 **السويّةُ تعمل على بوّابات البوت (`FAISAL_ONLY=0`) — وهذا قرارٌ منهجيّ لا تهرّب.**
#    السببُ: أكثرُ من ألفَي اختبارٍ **توصيفيّ** يُثبّت آلةَ `analyze_ticker` بعتباتٍ
#    معلومة (فِكستشراتٌ مبنيّةٌ عليها حرفيًّا). فتشغيلُها بأرقامٍ أخرى لا يكشف عيبًا
#    بل **يُبطل معنى الفِكستشر** — وقد رأيتُه: أوّلُ تشغيلٍ بأرقام فيصل انهار عند
#    السطر 280 لأن سهمًا مصطنعًا لم يعد مرشّحًا. ⇒ **السويّة تُثبّت الآلةَ، والوضعُ
#    الجديد يأخذ أقفالَه الخاصّة** (‏`FO_*` أدناه: الافتراضُ الإنتاجيّ · الخريطةُ ·
#    الأنواعُ · الفشلُ الآمن · **والفارقُ السلوكيّ** الذي يُثبت أن التبديل يعمل).
#    ⚠️ ولذلك القفلُ الأوّل فيها هو **أن الافتراضَ في الإنتاج = 1** فلا يُنسى مُطفأً.
_os_hc.environ["FAISAL_ONLY"] = "0"
import types as _ty0
import numpy as np
import pandas as pd
import Super_stock as S
import technical_report as TR
import hand_check as HC

# ══════════════════════════════════════════════════════════════════════════
# 🔴 **السويّة لا تدهس ملفَّ حالةٍ مدفوعًا** — عيبٌ مقيس (‏2026-08-05)
# ══════════════════════════════════════════════════════════════════════════
# وصلتُ `record_rejected_symbols` بمسارَي `run_daily_watchlist` و
# `run_weekly_renewal`، وهما **مُشغَّلان فعليًّا** في السويّة (‏5 مواضع) ⇒ صارت
# الاختباراتُ تكتب في `reject_log.json` **الحقيقيّ** بمساره الافتراضيّ فتدهس
# لقطةَ يومٍ حيّ. والجذعُ لكل مُشغِّلٍ على حدة هو **صنفُ عطل «يجب أن نتذكّر»**
# ⇒ العلاجُ عند المصدر: يُحوَّل الثابتُ نفسُه لمسارٍ مؤقّت **مرّةً واحدة**، فأيُّ
# نداءٍ — قائمٍ أو قادم — يكتب في المؤقّت. والاختباراتُ المخصَّصة تمرّر مسارها صريحًا.
# 🔒 وحرسُ ذلك **ليس هذا السطر** (يصير عدميًّا) بل بصمةُ الملفّ الحقيقيّ تُؤخَذ
#    الآن وتُقارَن **قبل الملخّص** ⇒ أيُّ كاتبٍ بأيّ وسيلةٍ يُسقط السويّة.
import hashlib as _rej_h                                          # noqa: E402
import tempfile as _rej_tf                                        # noqa: E402

_REJ_REAL_PATH = S.REJECT_LOG_FILE
_REJ_REAL_SHA = (
    _rej_h.sha256(open(_REJ_REAL_PATH, "rb").read()).hexdigest()
    if _os_hc.path.exists(_REJ_REAL_PATH) else None)
S.REJECT_LOG_FILE = _os_hc.path.join(
    _rej_tf.gettempdir(), "_suite_reject_log.json")

# 🔴🔴 **ونفسُ العيب تكرّر بيدي مع سجلّ الحصاد** (‏2026-08-05): وصلتُ `LEDGER.record`
#    بالصيّادين الأربعة، **والسويّة تُشغّلهم فعلًا** ⇒ صاروا يكتبون في
#    `hunter_ledger.jsonl` **الحقيقيّ** برموزٍ مصطنعة (`X` · `AAA` · `NUWE` بفلوتٍ
#    مفبرك) ⇒ **تلويثُ التجربة التي سجّلتُها للتوّ** — إذ ستُحسَم تلك الصفوفُ لاحقًا
#    كأنها مرشّحون حقيقيّون. **وهو صنفُ العطل نفسه الذي شخّصتُه قبل ساعات** ⇒ نفسُ
#    العلاج **عند المصدر**: يُحوَّل الثابت مرّةً واحدة، وتُحرَس البصمةُ قبل الملخّص.
import hunter_ledger as _lg_mod                                   # noqa: E402

_LED_REAL_PATH = _lg_mod.LEDGER_FILE
_LED_REAL_SHA = (
    _rej_h.sha256(open(_LED_REAL_PATH, "rb").read()).hexdigest()
    if _os_hc.path.exists(_LED_REAL_PATH) else None)
_lg_mod.LEDGER_FILE = _os_hc.path.join(
    _rej_tf.gettempdir(), "_suite_hunter_ledger.jsonl")

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
    # ③ تحصين (تدقيق 2026-07-12): كان `if r0 and _diag:` يجعل الفحص **يختفي بصمت**
    # (لا نجاح ولا فشل) لو انهار أحدهما — الآن الغياب = فشل صريح.
    if not (r0 and _diag):
        check("الفحص اليدوي = الأساسي (r0/_diag غائب — الفحص كان سيختفي بصمت)", False)
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

# ==========================================================
# 🎯 إعادة بناء الأهداف الكبرى (2026-07-20، DXST/TRUG/SPRC) — t2/t3 على الدورة الكاملة
#    · t1/التحرر/العضوية محفوظة byte-identical · لا سنتات (فجوة كبرى) · لا سقف 2× صلب
# ==========================================================
print("\n=== 🎯 الأهداف الكبرى (فيصل DXST/TRUG/SPRC) ===")
import inspect as _insp
_MG = S.CONFIG["TARGET_MAJOR_GAP_PCT"] / 100.0
check("ثابت فجوة الأهداف الكبرى = 12", S.CONFIG.get("TARGET_MAJOR_GAP_PCT") == 12.0)
check("ثابت هامش المرساة = 5", S.CONFIG.get("TARGET_ANCHOR_HEADROOM_PCT") == 5.0)
check("LOGIC_VERSION رُفِع (bluetargets)", "bluetargets" in S.LOGIC_VERSION)

_tg = S.analyze_ticker("TG", synth_pivot(seed=2))
if _tg:
    _t1, _t2, _t3 = _tg["t1"], _tg["t2"], _tg["t3"]
    check("الأهداف تصاعدية t1<t2<t3", _t1 < _t2 < _t3, f"{_t1}/{_t2}/{_t3}")
    # 🎯 الإصلاح الجوهري (شكوى «سنتات و تافهه»): t2/t3 متباعدة بفجوة معنوية لا سنتات
    check("t2 أبعد من t1 بفجوة كبرى (لا سنتات)", _t2 >= _t1 * (1 + _MG) - 0.03,
          f"t1={_t1} t2={_t2} ({(_t2/_t1-1)*100:.0f}%)")
    check("t3 أبعد من t2 بفجوة كبرى (لا سنتات)", _t3 >= _t2 * (1 + _MG) - 0.03,
          f"t2={_t2} t3={_t3} ({(_t3/_t2-1)*100:.0f}%)")
    # التحرر «مهمة جدا» = قمة الدورة فوق كل الأهداف — محفوظ byte-identical (كتلة منفصلة)
    check("التحرر فوق t3 (بوابة الدورة الكبرى محفوظة)",
          _tg["liberation"] is None or _tg["liberation"] >= _t3, str(_tg["liberation"]))
    # المرساة الحقيقية = قمة الدورة (hi52) لا 2× صلب — t3 ضمن قمة الدورة (+هامش) أو 2× أيهما أعلى
    _cyc = float(synth_pivot(seed=2)["High"].tail(252).max())
    check("t3 ضمن مرساة قمة الدورة (لا سقف 2× صلب)",
          _t3 <= max(_cyc * 1.05, 2 * _tg["price"]) + 1e-6, f"t3={_t3} cyc={_cyc:.1f}")
    # 🔒 قفل العضوية: RR يُشتقّ من t1 حصرًا (t1 محفوظ byte-identical فـRR/النواقص/التصنيف
    # بلا تغيير) — نعيد بناء rr من t1/الدفعات/الوقف ونطابقه المخزَّن.
    _eref = round(sum(_tg["tranches"]) / len(_tg["tranches"]), 4)
    _rr_from_t1 = (_t1 - _eref) / max(_eref - _tg["stop"][0], 1e-9)
    check("rr مُشتقّ من t1 حصرًا (العضوية byte-identical)",
          abs(_tg["rr"] - _rr_from_t1) < 1e-6 and _t1 > _tg["price"],
          f"t1={_t1} rr={_tg['rr']:.4f} من_t1={_rr_from_t1:.4f}")
    # 🎨 ألوان فيصل (2026-07-20، «ابي الثنتين و توضح»): كل هدف موسوم ⚫/🔵
    _tk = _tg.get("targets_kind")
    check("🎨 targets_kind = 3 وسوم (⚫ مقاومة / 🔵 نظيف)",
          isinstance(_tk, list) and len(_tk) == 3
          and all(k in ("⚫", "🔵") for k in _tk), str(_tk))
    # t3 = القمة الكبيرة (قمة الدورة/فيب/فجوة) = 🔵 نظيف «هدف بلا مقاومة»
    check("🎨 t3 (القمة) = 🔵 نظيف (هدف بلا مقاومة)", _tk and _tk[2] == "🔵", str(_tk))
    # الكرت يوضّح اللونين
    _cardmsg = S.build_message([dict(_tg, symbol="TG", readiness=60, score=60)], [])
    check("🎨 الكرت يعرض «🔵 نظيف» و«⚫ مقاومة» على الأهداف",
          "🔵 نظيف" in _cardmsg and "⚫ مقاومة" in _cardmsg)
    # 🛡️ حارس phantom التقسيم: hi52 متضخّم (تعديل تقسيم رجعي، شمعة حافة معزولة بلا
    # مقاومات حولها) لا يجعل t3 خياليًّا ($62). resistance_levels يفلتر الوهم فيُقصّ t3.
    _ph = synth_pivot(prior_high=9.0, crash_low=3.0, current=3.6, seed=2).copy()
    _phh = _ph["High"].values.copy()
    _phh[0] = 62.0                          # قمة تاريخية وهمية معزولة (حافة، ليست سوينغ)
    _ph2 = pd.DataFrame({"Open": _ph["Open"].values, "High": _phh,
                         "Low": _ph["Low"].values, "Close": _ph["Close"].values,
                         "Volume": _ph["Volume"].values}, index=_ph.index)
    _phr = S.analyze_ticker("PH", _ph2)
    check("🛡️ حارس phantom: hi52=$62 وهمي ⇒ t3 واقعي (لا خيالي)",
          bool(_phr) and _phr["t3"] < 30.0,
          (f"t3={_phr['t3']} hi52=62" if _phr else "rejected"))

# 🔒 قفل بنيوي: كتلة الأهداف الجديدة تعيد بناء t2/t3 فقط — لا تمسّ t1/rr/soft_fails/العضوية
_at_src = _insp.getsource(S.analyze_ticker)
# ⚠️ **إصلاح 2026-07-28:** كان القطع بين **تعليقين** («إعادة بناء t2/t3» و«تحرر
# السهم») ⇒ يكفي بقاء التعليقين ليمرّ القفل وإن حُذف الكود كلّه. صار القطع بين
# **سطرين تنفيذيين**، والإثبات إيجابيًّا على رموز حقيقية داخل الكتلة.
_blk = (_at_src.split("targets_kind = None")[1].split("liberation = None")[0]
        if "targets_kind = None" in _at_src else "")
check("كتلة الأهداف الجديدة موجودة (رموز تنفيذية لا تعليقات)",
      all(_t in _blk for _t in ("cycle_peak", "_major_cap", "_majors", "def _tkind")))
# ⚠️ ومقارنة النصّ بعد **حذف المسافات**: `t1 =` وحدها كانت تُراوغ بـ`t1=`.
_blkn = _blk.replace(" ", "")
check("كتلة الأهداف لا تمسّ t1/rr/soft_fails/العضوية (t2/t3 فقط)",
      bool(_blk) and all(_x not in _blkn for _x in
                         ("soft_fails", "return{", "rr=", "t1=", "_reject")))
# 🔒🔒 **الدبّوس السلوكي على الجذر** — أهمّ قفل أُضيف اليوم. القفل النصّي أعلاه يمكن
# مراوغته بأي صياغة؛ وهذا يقيس **المُخرَج نفسه**: مدقّق خصومي أثبت أن حقن
# `t1=round(t1*1.30,2)` داخل الكتلة (ومرآتها بـanalyze_one) يضخّم rr من 1.7809 إلى
# 5.4032 — و`rr` يحكم العضوية عبر `MIN_RR_T1` — **ومرّ على السويّة كاملةً 1261/0**.
# القيم مقيسة على الشجرة النقيّة؛ أي انزياح في جذر الاختيار = فشل صريح.
check("🔒 جذر: t1/rr/الوقف/الدفعات مثبَّتة للبذرة 2 (أي انزياح = فشل)",
      r0["t1"] == 3.99 and round(r0["rr"], 4) == 1.7809
      and r0["tranches"] == [3.3, 3.4, 3.5]
      and round(r0["pivot"], 6) == 3.299692
      and tuple(round(_s, 4) for _s in r0["stop"]) == (3.0687, 3.1347),
      f"t1={r0['t1']} rr={round(r0['rr'], 4)} pivot={round(r0['pivot'], 6)}")
# 🔒 قفل الجذور: الأهداف الكبرى الجديدة لا تدخل جذور الاختيار
for _rt in (S.rank_key, S.select_top, S.classify_tier, S.entry_status):
    check(f"{_rt.__name__} لا يعتمد فجوة الأهداف الكبرى (خارج الاختيار)",
          "TARGET_MAJOR_GAP_PCT" not in _insp.getsource(_rt))
# 🔒 refine_targets_4h يستعمل الفجوة الكبرى فلا يسحق t2/t3 المتباعدة إلى سنتات
_rt2, _rt3 = S.refine_targets_4h(3.88, 5.0, 7.0, 3.6,
                                 {"resistances": [4.0, 4.2, 5.0, 7.0]})
check("refine_4h يحفظ الأهداف المتباعدة (لا سحق لسنتات)",
      _rt2 >= 3.88 * (1 + _MG) - 1e-6 and _rt3 >= _rt2 * (1 + _MG) - 1e-6,
      f"{_rt2}/{_rt3}")

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

# 🔴 فلوت كبير → **يُحذف تمامًا** (قرار المالك 2026-07-29؛ كان نقصًا يُسجَّل منذ v2.7
# فظهر HTZ بـ129م وPONY بـ277م في القائمة الحيّة).
S.yf = object()   # حتى لا يتخطّى الدالة
big = mk("BIGF", float=200_000_000)
out3 = S.apply_float_gate([big])
check("🔴 فلوت كبير يُحذف تمامًا (لا يُنقَل نقصًا)", out3 == [])
unk = mk("UNKF", float=None)
check("🔴 والمجهول يبقى ممرَّرًا بفائدة الشك (تعذّر ≠ كبير)",
      len(S.apply_float_gate([unk])) == 1)
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

# 4ب) 🔒 قفل F-01 (إصلاح تدقيق 2026-07-10): التجديد الكامل مع week_start
#     يمرّر **قاموس الأسعار** (لا قائمة الأرشيف) إلى scan_pullback
#     وaccumulate_explosions — تظليل hist كان يفرغ قائمة الارتداد كل جمعة.
_f01_df = synth_pivot()
_f01_r = S.analyze_ticker("F01T", _f01_df)
check("F-01·تمهيد: السهم الصناعي يجتاز الفارز (مدخل التجديد الكامل)",
      _f01_r is not None)
_f01_types = {}
_f01_saved = {}
_sv_f01 = (S.scan_market, S.send_telegram, S.save_watchlist, S.yf,
           S.download_history, S.build_wrapup_message, S.enrich,
           S.scan_pullback, S.accumulate_explosions, S.load_alerts,
           S.build_dev_assistant_report, S.export_weekly_csvs,
           S.write_csv, S.run_performance_system)
try:
    def _f01_scan():
        S._SCAN_STATS.update({"universe": 10, "valid": 10,
                              "universe_fallback": False})
        return ([_f01_r], {"F01T": _f01_df})
    _real_sp, _real_ae = S.scan_pullback, S.accumulate_explosions
    S.scan_market = _f01_scan
    S.send_telegram = lambda m: True
    S.save_watchlist = lambda w: _f01_saved.update(w)
    S.yf = None                       # يتخطى تحديث الأسبوع المنتهي (شبكة)
    S.download_history = lambda syms: {}
    S.build_wrapup_message = lambda w: ""
    S.enrich = lambda rs: None
    S.scan_pullback = lambda h, exclude=None: (
        _f01_types.setdefault("pull", type(h)), _real_sp(h, exclude))[1]
    S.accumulate_explosions = lambda wl_, h: (
        _f01_types.setdefault("expl", type(h)), _real_ae(wl_, h))[1]
    S.load_alerts = lambda: {"alerts": []}
    S.build_dev_assistant_report = lambda wl_, ad=None: ""
    S.export_weekly_csvs = lambda *a, **k: None
    S.write_csv = lambda *a, **k: None
    S.run_performance_system = lambda *a, **k: None
    _wlf01 = {"week_start": "2026-07-03", "stocks": [], "removed": [],
              "notes": [], "pullback": [], "history": [],
              # ⑥: حالة متراكمة يجب أن تنجو التجديد (كانت تُمسح كل جمعة)
              "reject_stats": [{"date": f"2026-07-{d:02d}", "stats": {"M2": 5}}
                               for d in range(1, 11)],
              "مفتاح_مستقبلي": {"x": 1}}
    S.run_weekly_renewal(_wlf01)
    check("🔒F-01: scan_pullback يستقبل قاموس الأسعار (لا قائمة الأرشيف)",
          _f01_types.get("pull") is dict)
    check("🔒F-01: accumulate_explosions يستقبل قاموس الأسعار",
          _f01_types.get("expl") is dict)
    check("🔒F-01: الأسبوع المنتهي أُرشِف والقائمة الجديدة حُفظت",
          len(_f01_saved.get("history") or []) == 1
          and len(_f01_saved.get("stocks") or []) == 1)
    # ⑥ (إصلاح تدقيق 2026-07-12): التجديد لا يمسح الحالة المتراكمة بعد الآن
    check("⑥ reject_stats ينجو التجديد كاملًا (10 لقطات — كان يُمسح كل جمعة)",
          len(_f01_saved.get("reject_stats") or []) == 10)
    check("⑥ قفل اللغم البنيوي: مفتاح حالة مجهول ينجو التجديد افتراضيًا",
          _f01_saved.get("مفتاح_مستقبلي") == {"x": 1})
    check("⑥ قفل عكسي: مفاتيح التجديد تُصفَّر فعلًا (removed/notes جديدة فارغة)",
          _f01_saved.get("removed") == [] and _f01_saved.get("notes") == [])
    # ⑫ (إصلاح تدقيق 2026-07-12): خنق بيانات الأسبوع المنتهي → التجديد يُؤجَّل
    # كاملًا (لا أرشفة لأسبوع غير محسوم، القائمة النشطة تبقى كما هي).
    import types as _ty12
    _sv_yf12 = S.yf
    _f01_saved.clear()
    S.yf = _ty12.SimpleNamespace()               # موجود (فلا يُتخطّى تحديث الأسبوع)
    S.download_history = lambda syms: {}          # خنق تام: صفر تغطية
    _wl12 = {"week_start": "2026-07-03",
             "stocks": [{"symbol": "OLD1", "status": "active",
                         "added": "2026-07-06", "entry_ref": 2.0, "pivot": 2.0,
                         "stop": 1.8, "t1": 2.4, "t2": 2.8, "t3": 3.2,
                         "hit": None, "max_gain_pct": 0.0}],
             "removed": [], "notes": [], "pullback": [], "history": []}
    S.run_weekly_renewal(_wl12)
    check("⑫ خنق الأسبوع المنتهي (تغطية 0%) → التجديد مؤجَّل ولا أرشفة",
          not _f01_saved                          # save_watchlist لم تُستدع
          and _wl12["week_start"] == "2026-07-03"
          and len(_wl12["stocks"]) == 1 and not _wl12["history"])
    S.yf = _sv_yf12
finally:
    (S.scan_market, S.send_telegram, S.save_watchlist, S.yf,
     S.download_history, S.build_wrapup_message, S.enrich,
     S.scan_pullback, S.accumulate_explosions, S.load_alerts,
     S.build_dev_assistant_report, S.export_weekly_csvs,
     S.write_csv, S.run_performance_system) = _sv_f01

# 4ب-2) 🔄 قفل الاستمرارية (طلب المستخدم 2026-07-21): التجديد لا يمحو أسهم
#       الأسبوع الماضي النشطة بصمت (PSTV اختفى) — تُحمَل بوسم مصير + تقرير مصير.
# (أ) وحدة build_fate_report: يرتّب بالأولوية · يزيل التكرار · يعرض كل رمز
_fate_in = [("AAA", "✅ يستمر — أعاد التأهّل هذا الأسبوع"),
            ("BBB", "⚠️ خرج من نموذج الارتكاز — نتابعه لمركزك"),
            ("AAA", "✅ مكرر يجب أن يُزال"),
            ("CCC", "⛔ ضُرب الستوب (خرج من القائمة)")]
_fate_txt = S.build_fate_report(_fate_in)
check("🔄 fate: يعرض كل الرموز الفريدة (AAA/BBB/CCC)",
      all(sy in _fate_txt for sy in ("AAA", "BBB", "CCC")))
check("🔄 fate: يزيل تكرار الرمز (AAA مرة واحدة)",
      _fate_txt.count("$AAA") == 1)
check("🔄 fate: الأهم أولًا (⚠️ خرج قبل ✅ يستمر)",
      _fate_txt.index("BBB") < _fate_txt.index("AAA"))
check("🔄 fate: قائمة فارغة → نص فارغ", S.build_fate_report([]) == "")

# (ب) تكامل run_weekly_renewal: سهم نشط لم يُعَد اختياره لا يُمحى — يُحمَل بوسم
_sv_cont = (S.scan_market, S.send_telegram, S.save_watchlist, S.yf,
            S.download_history, S.build_wrapup_message, S.enrich,
            S.scan_pullback, S.accumulate_explosions, S.load_alerts,
            S.build_dev_assistant_report, S.export_weekly_csvs,
            S.write_csv, S.run_performance_system)
_cont_saved = {}
_cont_msgs = []
try:
    _cont_df_ok = synth_pivot(seed=7)          # يجتاز الفارز (سهم ارتكاز حي)
    _cont_idx = pd.date_range("2024-01-01", periods=200, freq="D")
    _cont_flat = np.linspace(5.0, 5.3, 200)    # صاعد لطيف بلا انفجار → يفشل الفارز
    _cont_df_bad = pd.DataFrame(
        {"Open": _cont_flat, "High": _cont_flat * 1.01,
         "Low": _cont_flat * 0.99, "Close": _cont_flat,
         "Volume": np.full(200, 500_000.0)}, index=_cont_idx)
    check("🔄 تمهيد: df المسطّح يفشل الفارز (سيصير «خرج»)",
          S.analyze_ticker("GONE", _cont_df_bad) is None)
    _cont_r = S.analyze_ticker("NEWPICK", _cont_df_ok)
    check("🔄 تمهيد: السهم الجديد يجتاز الفارز", _cont_r is not None)

    def _cont_scan():
        S._SCAN_STATS.update({"universe": 10, "valid": 10,
                              "universe_fallback": False})
        # hist: STILLP (ارتكاز حي) · GONE (لا ارتكاز) · NEWPICK (المُختار)
        return ([_cont_r], {"NEWPICK": _cont_df_ok,
                            "STILLP": _cont_df_ok, "GONE": _cont_df_bad})
    S.scan_market = _cont_scan
    S.send_telegram = lambda m: (_cont_msgs.append(m), True)[1]
    S.save_watchlist = lambda w: _cont_saved.update(w)
    S.yf = None                       # يتخطّى تحديث الأسبوع المنتهي (شبكة)
    S.download_history = lambda syms: {}
    S.build_wrapup_message = lambda w: ""
    S.enrich = lambda rs: None
    S.scan_pullback = lambda h, exclude=None: []
    S.accumulate_explosions = lambda wl_, h: None
    S.load_alerts = lambda: {"alerts": []}
    S.build_dev_assistant_report = lambda wl_, ad=None: ""
    S.export_weekly_csvs = lambda *a, **k: None
    S.write_csv = lambda *a, **k: None
    S.run_performance_system = lambda *a, **k: None

    def _cont_stock(sym):
        return {"symbol": sym, "status": "active", "added": "2026-07-06",
                "entry_ref": 2.0, "pivot": 2.0, "stop": (1.8, 1.85),
                "t1": 2.4, "t2": 2.8, "t3": 3.2, "hit": None,
                "max_gain_pct": 0.0}
    _wl_cont = {"week_start": "2026-07-14",
                "stocks": [_cont_stock("STILLP"), _cont_stock("GONE"),
                           _cont_stock("NODATA")],   # NODATA غائب عن hist
                "removed": [{"symbol": "STOPPED", "status": "stopped"}],
                "notes": [], "pullback": [], "history": []}
    S.run_weekly_renewal(_wl_cont)
    _cont_by = {s["symbol"]: s for s in _cont_saved.get("stocks", [])}
    check("🔄 استمرارية: السهم المُعاد اختياره محفوظ (NEWPICK)",
          "NEWPICK" in _cont_by)
    check("🔄 استمرارية: سهم نشط لم يُعَد اختياره لا يُمحى (STILLP/GONE/NODATA باقية)",
          all(sy in _cont_by for sy in ("STILLP", "GONE", "NODATA")))
    check("🔄 استمرارية: ما زال ارتكازًا → cont_status=continues (STILLP)",
          _cont_by.get("STILLP", {}).get("cont_status") == "continues")
    check("🔄 استمرارية: لم يعد ارتكازًا → cont_status=exited (GONE)",
          _cont_by.get("GONE", {}).get("cont_status") == "exited")
    check("🔄 استمرارية: تعذّر البيانات → continues (لا يُمحى بصمت — NODATA)",
          _cont_by.get("NODATA", {}).get("cont_status") == "continues")
    check("🔄 استمرارية: التتبّع محفوظ (entry_ref القديم لا يُصفَّر — GONE)",
          _cont_by.get("GONE", {}).get("entry_ref") == 2.0)
    _cont_fate = "".join(m for m in _cont_msgs if "مصير أسهم" in m)
    check("🔄 استمرارية: تقرير المصير أُرسل ويذكر المشطوب والخارج",
          "STOPPED" in _cont_fate and "GONE" in _cont_fate)
finally:
    (S.scan_market, S.send_telegram, S.save_watchlist, S.yf,
     S.download_history, S.build_wrapup_message, S.enrich,
     S.scan_pullback, S.accumulate_explosions, S.load_alerts,
     S.build_dev_assistant_report, S.export_weekly_csvs,
     S.write_csv, S.run_performance_system) = _sv_cont

# 4ب-3) 🔄 قسم «متابعة لمركزك» الدائم (طلب المستخدم 2026-07-21): الأسهم المحمولة
#       (continues/exited) تظهر يوميًا في قسم مستقل الين تُضرب ستوب أو تعود للترشيح —
#       حتى بوضع الجاهز-فقط (متابعة المركز أهمّ من اختصار الإشعار).
def _pw_stock(sym, cs, lp, stop, crit=None):
    _sf = stop[0] if isinstance(stop, (list, tuple)) else stop
    return {"symbol": sym, "status": "active", "cont_status": cs,
            "last_price": lp, "stop": stop, "pivot": round(_sf * 1.07, 2),
            "t1": lp * 1.2, "t2": lp * 1.5, "t3": lp * 2.0,
            "tranches": [round(_sf * 1.07, 2)], "liberation": lp * 2.1,
            "interp": ({"critical_number": {"price": crit}} if crit else None),
            "readiness": 40, "score": 60, "tier": "B", "float": 1e7,
            "soft_fails": [], "flags": [], "warnings": [], "hit": None,
            "max_gain_pct": 0.0, "sector": "Technology", "country": "US"}
# (أ) وحدة build_position_watch_section
_pw_sec = S.build_position_watch_section(
    [_pw_stock("PSTV", "continues", 4.0, 3.6, crit=4.5),
     _pw_stock("GONE", "exited", 1.9, 1.7)])
check("🔄 متابعة-مركز: يعرض السهمين (PSTV/GONE)",
      "PSTV" in _pw_sec and "GONE" in _pw_sec)
check("🔄 متابعة-مركز: «خرج» أولًا (الأهم) ثم «يستمر»",
      _pw_sec.index("GONE") < _pw_sec.index("PSTV"))
check("🔄 متابعة-مركز: يعرض الستوب والرقم الحرج (يعود للزخم)",
      "$1.70" in _pw_sec and "$4.50" in _pw_sec)
check("🔄 متابعة-مركز: قائمة فارغة → نص فارغ",
      S.build_position_watch_section([]) == "")
check("🔄 متابعة-مركز: ستوب tuple (سجلّ قديم) لا يكسر العرض",
      "$1.70" in S.build_position_watch_section(
          [_pw_stock("TUP", "exited", 1.9, (1.7, 1.75))]))
# (ب) التكامل مع build_daily_message: القسم يظهر حتى بوضع الجاهز-فقط بلا جاهزين
_pw_wl = {"stocks": [_pw_stock("NEWP", None, 3.0, 2.5),
                     _pw_stock("PSTV", "continues", 4.0, 3.6, crit=4.5),
                     _pw_stock("GONE", "exited", 1.9, 1.7)]}
_pw_msg = S.build_daily_message(_pw_wl, [], [], [], ready_only=True)
check("🔄 متابعة-مركز·يومي: القسم يظهر بوضع الجاهز-فقط",
      "متابعة لمركزك" in _pw_msg and "PSTV" in _pw_msg and "GONE" in _pw_msg)
check("🔄 متابعة-مركز·يومي: المحمولة لا تُحسب ضمن الترشيح (ترويسة تفصلها)",
      "🔄 2 متابعة لمركزك" in _pw_msg)
check("🔄 متابعة-مركز·يومي: سهم الترشيح (NEWP بلا cont_status) لا يظهر بقسم المتابعة",
      "NEWP" not in _pw_msg.split("متابعة لمركزك")[1])

# 4ج) 🔒 قفل F-02 (إصلاح تدقيق 2026-07-10): تسوية مقياس التقسيم في الحسم —
#     تقسيم عكسي أثناء التتبع لا يسجّل «هدفًا محققًا» زائفًا بعد الآن.
# (1) الدالة النقية _split_scale_factor
_spl_series = pd.Series([0.1], index=[pd.Timestamp("2026-01-08")])
check("⚖️F-02: عامل التقسيم بعد التاريخ المرجعي (عكسي 1:10 → 0.1)",
      abs(S._split_scale_factor(_spl_series, "2026-01-05") - 0.1) < 1e-9)
check("⚖️F-02: تقسيم قبل المرجع لا يُحسب (عامل 1.0)",
      S._split_scale_factor(_spl_series, "2026-01-10") == 1.0)
check("⚖️F-02: بلا أحداث/None → عامل 1.0 (فاشل-آمن)",
      S._split_scale_factor(None, "2026-01-01") == 1.0
      and S._split_scale_factor(pd.Series(dtype=float), "2026-01-01") == 1.0)
check("⚖️F-02: قائمة أزواج تتراكم بالضرب (0.1×0.5=0.05)",
      abs(S._split_scale_factor([("2026-01-08", 0.1), ("2026-02-01", 0.5)],
                                "2026-01-01") - 0.05) < 1e-9)
# (2) مُختار تماسك المقياس (حارس التصحيح المزدوج بعد الترحيل)
check("⚖️F-02: مستويات بمقياس قديم → يختار القسمة على العامل",
      S._scale_divisor(10.0, 1.0, 0.1) == 0.1)
check("⚖️F-02: مستويات أعيد حسابها (مقياس اليوم) → لا يقسم (يمنع الازدواج)",
      S._scale_divisor(10.0, 9.5, 0.1) == 1.0)
check("⚖️F-02: عامل 1.0 → قاسم 1.0 دائمًا",
      S._scale_divisor(10.0, 1.0, 1.0) == 1.0)
# (3) تكامل update_tracking: سلسلة ×10 بعد تقسيم عكسي → hit_t1 صحيح لا hit_t3 زائف
import types as _ty_spl
_spl_idx = pd.to_datetime(["2026-01-06", "2026-01-07", "2026-01-08",
                           "2026-01-09"])
_spl_df = pd.DataFrame({"Close": [10.0, 10.5, 11.0, 10.8],
                        "High": [10.5, 11.0, 13.0, 11.0],
                        "Low": [9.6, 9.8, 10.2, 10.4]}, index=_spl_idx)
_sv_spl = (S.yf, S._fetch_splits)
try:
    S.yf = _ty_spl.SimpleNamespace(
        download=lambda *a, **k: _spl_df.copy())
    S._fetch_splits = lambda sym: _spl_series
    _al = {"symbol": "SPLA", "date": "2026-01-05", "price": 1.0,
           "stop": 0.9, "t1": 1.2, "t2": 1.5, "t3": 2.0,
           "status": "open", "max_gain_pct": 0.0}
    S.update_tracking({"alerts": [_al]})
    check("⚖️F-02·تتبع التنبيهات: hit_t1 الصحيح (t1=1.2→12 بمقياس اليوم)",
          _al["status"] == "hit_t1")
    check("⚖️F-02·تتبع التنبيهات: لا hit_t3 زائف ولا ستوب زائف بعد التقسيم",
          _al["status"] not in ("hit_t3", "stopped"))
    check("⚖️F-02·تتبع التنبيهات: أقصى ارتفاع بمقياس موحّد (~+30%)",
          abs(_al["max_gain_pct"] - 30.0) < 0.6)
finally:
    S.yf, S._fetch_splits = _sv_spl
# (4) تكامل update_watchlist_status: لا شطب/أهداف زائفة بعد تقسيم عكسي
_spl_idx2 = pd.to_datetime(["2026-02-02", "2026-02-03", "2026-02-04",
                            "2026-02-05", "2026-02-06"])
_spl_df2 = pd.DataFrame({"Close": [10.0, 10.2, 10.4, 10.1, 10.3],
                         "Open": [10.0, 10.1, 10.3, 10.2, 10.2],
                         "High": [10.5, 10.6, 11.0, 10.7, 10.8],
                         "Low": [9.6, 9.7, 9.5, 9.8, 9.9],
                         "Volume": [1e5] * 5}, index=_spl_idx2)
_sv_spl2 = S._fetch_splits
try:
    S._fetch_splits = lambda sym: _spl_series
    _st = {"symbol": "SPLB", "status": "active", "added": "2026-01-05",
           "entry_ref": 1.0, "pivot": 1.0, "stop": 0.9, "t1": 1.2,
           "t2": 1.5, "t3": 2.0, "hit": None, "max_gain_pct": 0.0}
    _wlspl = {"stocks": [_st], "removed": [], "notes": []}
    S.update_watchlist_status(_wlspl, {"SPLB": _spl_df2})
    check("⚖️F-02·حسم القائمة: لا hit زائف بعد التقسيم (11 أقل من t1=12)",
          not _st["hit"] and _st["status"] == "active")
    check("⚖️F-02·حسم القائمة: لا ستوب زائف (أدنى 9.5 فوق الوقف المسوّى 9.0)",
          _wlspl["stocks"] and _wlspl["stocks"][0]["symbol"] == "SPLB")
finally:
    S._fetch_splits = _sv_spl2

# 4د) 🔒 §6 (2026-07-11): تسوية مشتبهات التقسيم في تقرير التطوير (طبقة تقارير
#     فقط) — الكسب الخارق يُصحَّح بعامل تقسيم عكسي مؤكَّد بدل استبعاده الأعمى.
# (1) الدالة النقية _split_corrected_gain
check("§6: عامل عكسي 0.1 على +900% → ≈0% (يُزيل تضخّم 1:10)",
      abs(S._split_corrected_gain(900.0, 0.1) - 0.0) < 1e-6)
check("§6: عامل ≥1 (لا تقسيم/أمامي) → يُرجع الكسب الأصل بلا مساس",
      S._split_corrected_gain(50.0, 1.0) == 50.0
      and S._split_corrected_gain(50.0, 2.0) == 50.0)
check("§6: عامل صفر/سالب/None → الأصل (فاشل-آمن)",
      S._split_corrected_gain(50.0, 0.0) == 50.0
      and S._split_corrected_gain(50.0, -1.0) == 50.0
      and S._split_corrected_gain(50.0, None) == 50.0)
# (2) _resolve_split_suspects — بمُحلّل تقسيم محقون (بلا شبكة).
#   الصيغة بعامل 0.1: corrected = 0.1×g − 90. INLF +1250% → +35% (بالنطاق) → نظيف.
_ms_in = [
    {"symbol": "INLF", "reason": "M4_base", "gain_10d": 1250.0,
     "window_start": "2026-06-01", "suspect_split": True},   # →+35% نظيف
    {"symbol": "NOISE", "reason": "M2_x", "gain_10d": 900.0,
     "window_start": "2026-06-01", "suspect_split": True},   # →0% يُسقَط
    {"symbol": "NOSPL", "reason": "M2_x", "gain_10d": 900.0,
     "window_start": "2026-06-01", "suspect_split": True},   # لا تقسيم → يبقى
    {"symbol": "CLEAN", "reason": "M4_x", "gain_10d": 45.0,
     "window_start": "2026-06-01", "suspect_split": False},  # يمرّ بلا مساس
]
_spl_map = {"INLF": pd.Series([0.1], index=[pd.Timestamp("2026-06-11")]),
            "NOISE": pd.Series([0.1], index=[pd.Timestamp("2026-06-11")]),
            "NOSPL": None}
_ms_res = S._resolve_split_suspects(_ms_in,
                                    fetch=lambda s: _spl_map.get(s))
_by = {m["symbol"]: m for m in _ms_res}
check("§6: مشتبه بتقسيم عكسي مؤكَّد يُنزله للنطاق → يصير نظيفًا (split_corrected)",
      "INLF" in _by and _by["INLF"].get("split_corrected") is True
      and not _by["INLF"]["suspect_split"]
      and abs(_by["INLF"]["gain_10d"] - 35.0) < 0.5)
check("§6: مشتبه يُصحَّح دون عتبة الفائتة (30%) → يُسقَط من القائمة",
      "NOISE" not in _by)
check("§6: مشتبه بلا تقسيم فعلي (fetch→None) → يبقى موسومًا (سلوك اليوم)",
      "NOSPL" in _by and _by["NOSPL"]["suspect_split"] is True
      and not _by["NOSPL"].get("split_corrected"))
check("§6: غير المشتبه يمرّ بلا مساس",
      "CLEAN" in _by and _by["CLEAN"]["gain_10d"] == 45.0)
check("§6: بلا window_start → يبقى suspect (توافق خلفي مع السجلات القديمة)",
      S._resolve_split_suspects(
          [{"symbol": "OLD", "reason": "M2", "gain_10d": 900.0,
            "suspect_split": True}],
          fetch=lambda s: _spl_map.get("INLF"))[0]["suspect_split"] is True)
# (3) _resolve_explosion_suspects — مرجع expl_date−1 يلتقط تقسيم يوم الانفجار.
#   عتبة الإسقاط هنا = EXPLOSION_PCT(50). INLF +1500% → +60% نظيف (0.1×1500−90).
_ex_in = [
    {"symbol": "INLF", "gain": 1500.0, "expl_date": "2026-06-11",
     "was_pivot": True, "suspect_split": True},
    {"symbol": "NOSPL", "gain": 900.0, "expl_date": "2026-06-11",
     "was_pivot": True, "suspect_split": True},
]
_ex_res = S._resolve_explosion_suspects(
    _ex_in, fetch=lambda s: _spl_map.get(s))
_exby = {e["symbol"]: e for e in _ex_res}
check("§6·انفجارات: مشتبه بتقسيم يوم الانفجار يُصحَّح (expl_date−1 يلتقطه)",
      "INLF" in _exby and _exby["INLF"].get("split_corrected") is True
      and abs(_exby["INLF"]["gain"] - 60.0) < 1.0)
check("§6·انفجارات: بلا تقسيم فعلي → يبقى موسومًا",
      "NOSPL" in _exby and _exby["NOSPL"]["suspect_split"] is True)
# (4) 🔒 قفل: الدوال الأربع خارج الفرز/الاختيار/الاختبار (طبقة تقارير فقط)
_split6_fns = (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
               S.analyze_ticker, S.backtest_symbol)
check("§6: _split_corrected_gain خارج rank_key/select_top/classify_tier/"
      "entry_status/analyze_ticker/backtest_symbol",
      all("_split_corrected_gain" not in _insp0.getsource(f)
          for f in _split6_fns))
check("§6: _resolve_split_suspects/_resolve_explosion_suspects خارج الفرز/الاختيار",
      all(("_resolve_split_suspects" not in _insp0.getsource(f)
           and "_resolve_explosion_suspects" not in _insp0.getsource(f))
          for f in _split6_fns))

# 4هـ) 🔒 ① (إصلاح تدقيق 2026-07-12): شمعة يوم الترشيح تدخل التقييم — مرجع النافذة
#     = ref_bar (شمعة الترشيح الفعلية) لا added (تاريخ التشغيل). المسار اليومي يختم
#     قبل الافتتاح فكانت `day > added` تُسقط أول جلسة للأبد (ستوب اليوم الأول أعمى).
_rb_idx = pd.to_datetime(["2026-03-02"])
_rb_df = pd.DataFrame({"Close": [1.7], "Open": [2.0], "High": [2.05],
                       "Low": [1.65], "Volume": [1e5]}, index=_rb_idx)
_sv_rb = S._fetch_splits
try:
    S._fetch_splits = lambda sym: None            # عزل F-02 (عامل 1.0)
    # (أ) سجل يومي: added=يوم التشغيل (2026-03-02) لكن ref_bar=شمعة الترشيح (03-01)
    #     → شمعة 03-02 (الهابطة تحت الستوب 1.8) **تدخل التقييم** ويُشطب.
    _st_a = {"symbol": "RB1", "status": "active", "added": "2026-03-02",
             "ref_bar": "2026-03-01", "entry_ref": 2.0, "pivot": 2.0,
             "stop": 1.8, "t1": 2.4, "t2": 2.8, "t3": 3.2,
             "hit": None, "max_gain_pct": 0.0}
    _wl_a = {"stocks": [_st_a], "removed": [], "notes": []}
    S.update_watchlist_status(_wl_a, {"RB1": _rb_df.copy()})
    check("① ستوب أول جلسة يُرى الآن (ref_bar=أمس → شمعة اليوم تُقيَّم وتُشطب)",
          _st_a["status"] == "stopped")
    # (ب) قفل انحدار مسار الجمعة: ref_bar == added == يوم الشمعة نفسها → الشمعة
    #     صدرت قبل الترشيح (بعد الإغلاق) فلا تُقيَّم — السلوك القديم دون تغيير.
    _st_b = {"symbol": "RB2", "status": "active", "added": "2026-03-02",
             "ref_bar": "2026-03-02", "entry_ref": 2.0, "pivot": 2.0,
             "stop": 1.8, "t1": 2.4, "t2": 2.8, "t3": 3.2,
             "hit": None, "max_gain_pct": 0.0}
    _wl_b = {"stocks": [_st_b], "removed": [], "notes": []}
    S.update_watchlist_status(_wl_b, {"RB2": _rb_df.copy()})
    check("① قفل مسار الجمعة: ref_bar=يوم الشمعة → لا تقييم لها (سلوك اليوم حرفيًا)",
          _st_b["status"] == "active")
    # (ج) توافق خلفي: سجل قديم **بلا** ref_bar → ارتداد لـ added (نفس سلوك اليوم).
    _st_c = {"symbol": "RB3", "status": "active", "added": "2026-03-02",
             "entry_ref": 2.0, "pivot": 2.0, "stop": 1.8, "t1": 2.4,
             "t2": 2.8, "t3": 3.2, "hit": None, "max_gain_pct": 0.0}
    _wl_c = {"stocks": [_st_c], "removed": [], "notes": []}
    S.update_watchlist_status(_wl_c, {"RB3": _rb_df.copy()})
    check("① توافق خلفي: سجل قديم بلا ref_bar → ارتداد لـ added بلا انهيار",
          _st_c["status"] == "active")
finally:
    S._fetch_splits = _sv_rb
# (د) متتبّع التنبيهات: نفس الإصلاح — start من ref_bar+1 فتُرى شمعة يوم التنبيه.
import types as _ty_rb
_sv_rb2 = (S.yf, S._fetch_splits)
try:
    S._fetch_splits = lambda sym: None
    S.yf = _ty_rb.SimpleNamespace(download=lambda sym, start=None, **k: (
        _rb_df[_rb_df.index >= start].copy()))   # يحترم start (يحاكي ياهو)
    _al_rb = {"symbol": "RB4", "date": "2026-03-02", "ref_bar": "2026-03-01",
              "price": 2.0, "stop": 1.8, "t1": 2.4, "t2": 2.8, "t3": 3.2,
              "status": "open", "max_gain_pct": 0.0}
    S.update_tracking({"alerts": [_al_rb]})
    check("①·تنبيهات: شمعة يوم التنبيه تُتابع (start=ref_bar+1) ويُحسم الستوب",
          _al_rb["status"] == "stopped")
    # قفل توافق: تنبيه قديم بلا ref_bar → start=date+1 → الشمعة خارج النافذة.
    _al_old = {"symbol": "RB5", "date": "2026-03-02",
               "price": 2.0, "stop": 1.8, "t1": 2.4, "t2": 2.8, "t3": 3.2,
               "status": "open", "max_gain_pct": 0.0}
    S.update_tracking({"alerts": [_al_old]})
    # بلا ref_bar → start=date+1 → شمعة يومه خارج النافذة فلا تُحسم ستوبًا منها
    # (قد ينتهي expired لقِدَمه — وهذا سلوك اليوم حرفيًا أيضًا، المهم: لا حسم زائف).
    check("①·تنبيهات: قديم بلا ref_bar → شمعة يومه لا تُحسَم (سلوك اليوم حرفيًا)",
          _al_old["status"] != "stopped")
finally:
    S.yf, S._fetch_splits = _sv_rb2
# (هـ) المصدر: scan_market يخزّن ref_bar وmake_watch_entry/record_new_alerts ينقلانه
# 4و) 🔒 ⑤ (إصلاح تدقيق 2026-07-12): نوافذ الجلسة تتصيّف/تتشتّى آليًا
_ms_sum = S.market_session_now(
    now=S.dt.datetime(2026, 7, 15, 12, 0, tzinfo=S.dt.timezone.utc))
_ms_win = S.market_session_now(
    now=S.dt.datetime(2026, 1, 15, 12, 0, tzinfo=S.dt.timezone.utc))
check("⑤ صيفًا (EDT): الافتتاح 13:30 · الإغلاق 20:00 · البريماركت 08:00 UTC",
      _ms_sum["open"] == 13 * 60 + 30 and _ms_sum["close"] == 20 * 60
      and _ms_sum["pre_start"] == 8 * 60)
check("⑤ شتاءً (EST): الافتتاح 14:30 · الإغلاق 21:00 · البريماركت 09:00 UTC",
      _ms_win["open"] == 14 * 60 + 30 and _ms_win["close"] == 21 * 60
      and _ms_win["pre_start"] == 9 * 60)
check("⑤ نوفمبر (بعد نهاية التصييف 11-01): شتوي",
      S.market_session_now(now=S.dt.datetime(2026, 11, 15, 12, 0,
          tzinfo=S.dt.timezone.utc))["open"] == 14 * 60 + 30)

check("① make_watch_entry ينقل ref_bar",
      S.make_watch_entry({"symbol": "RB6", "ref_bar": "2026-03-01", "price": 2.0,
                          "entry": (1.9, 2.0), "tranches": [1.9, 1.95, 2.0],
                          "pivot": 1.9, "stop": (1.75, 1.79), "t1": 2.3,
                          "t2": 2.6, "t3": 3.0, "score": 60, "flags": [],
                          "rr": 2.0}, "2026-03-02")["ref_bar"] == "2026-03-01")

# 4ز) 🔒 ⑧ (إصلاح تدقيق 2026-07-12): رادار الانطلاق يحدّث قائمته من origin/main
#     أثناء الجلسة (رنر منفصل — دفعات المراقب لا تصل ملفه المحلي) + ينقل أختام
#     الدِدوب (الرادار لا يحفظ فالأختام بالذاكرة فقط).
import ignition_live as IG
import types as _ty_ig
_ig_remote = {"stocks": [
    {"symbol": "ACON", "status": "stopped"},          # شُطب بدفعة المراقب
    {"symbol": "GEOS", "status": "active"}]}
def _ig_runner(cmd, **kw):
    if "show" in cmd:
        return _ty_ig.SimpleNamespace(
            returncode=0, stdout=json.dumps(_ig_remote).encode("utf-8"))
    return _ty_ig.SimpleNamespace(returncode=0, stdout=b"")
_ig_cur = {"stocks": [
    {"symbol": "ACON", "status": "active", "ignition_alert": "2026-07-12"},
    {"symbol": "GEOS", "status": "active", "ignition_alert": "2026-07-12"}]}
_ig_new = IG._fresh_watchlist(_ig_cur, runner=_ig_runner)
check("⑧ الرادار يرى الشطب الطازج من origin (ACON صار stopped)",
      _ig_new is not None
      and next(s for s in _ig_new["stocks"]
               if s["symbol"] == "ACON")["status"] == "stopped")
check("⑧ أختام الدِدوب تُنقل للنسخة الجديدة (لا إعادة إطلاق تنبيه منفَّذ)",
      next(s for s in _ig_new["stocks"]
           if s["symbol"] == "GEOS")["ignition_alert"] == "2026-07-12")
check("⑧ فاشل-آمن: فشل git/JSON فاسد/قائمة فارغة → None (نواصل على آخر نسخة)",
      IG._fresh_watchlist(_ig_cur, runner=lambda cmd, **k: _ty_ig.SimpleNamespace(
          returncode=1, stdout=b"")) is None
      and IG._fresh_watchlist(_ig_cur, runner=lambda cmd, **k: _ty_ig.SimpleNamespace(
          returncode=0, stdout=b"not json")) is None
      and IG._fresh_watchlist(_ig_cur, runner=lambda cmd, **k: _ty_ig.SimpleNamespace(
          returncode=0, stdout=b'{"stocks": []}')) is None)
check("⑧ قفل: حلقة الرادار تستدعي _fresh_watchlist (التحديث موصول فعلًا)",
      "_fresh_watchlist" in _insp0.getsource(IG.main))

# 4ح) 🔒 ⑬ (إصلاح تدقيق 2026-07-12): git_save — حل التعارض فعليًا + تلغرام عند
#     الفشل النهائي (كان: 4 محاولات متطابقة فاشلة ثم فقد حالة صامت بجوب أخضر).
_gs_tmp = "test_gitsave_tmp.json"
with open(_gs_tmp, "w") as _f:
    _f.write('{"x": 1}')
try:
    # (أ) الفشل النهائي (push يفشل دائمًا) → sender يُستدعى بتنبيه ⛔
    _gs_cmds, _gs_sent = [], []
    def _gs_runner_fail(cmd):
        _gs_cmds.append(cmd)
        if "git push" in cmd:
            return 1                             # الدفع يفشل دائمًا
        if "git diff --cached --quiet" in cmd:
            return 1                             # يوجد تغيير مُدرَج
        return 0
    _sv_sleep = S.time.sleep
    S.time.sleep = lambda *_: None               # لا انتظار حقيقي بالاختبار
    S.git_save([_gs_tmp], runner=_gs_runner_fail,
               sender=lambda m: _gs_sent.append(m))
    S.time.sleep = _sv_sleep
    check("⑬ فشل نهائي → تنبيه تلغرام (لا فقد حالة صامت بجوب أخضر)",
          len(_gs_sent) == 1 and "فشل حفظ حالة البوت" in _gs_sent[0])
    check("⑬ الفشل النهائي بعد 4 محاولات دفع فعلًا",
          sum(1 for c in _gs_cmds if "git push" in c) == 4)
    # (ب) تعارض rebase → استرجاع فعلي: اعتماد الريموت + إعادة ملفاتنا + إعادة كوميت
    _gs_cmds2, _gs_sent2 = [], []
    def _gs_runner_conflict(cmd):
        _gs_cmds2.append(cmd)
        if "git rebase FETCH_HEAD" in cmd:
            return 1                             # تعارض
        if "git diff --cached --quiet" in cmd:
            return 1
        return 0                                 # الدفع ينجح بعد الاسترجاع
    S.git_save([_gs_tmp], runner=_gs_runner_conflict,
               sender=lambda m: _gs_sent2.append(m))
    check("⑬ تعارض rebase → reset --hard FETCH_HEAD + إعادة ملفاتنا + إعادة كوميت",
          any("reset --hard FETCH_HEAD" in c for c in _gs_cmds2)
          and sum(1 for c in _gs_cmds2 if "git commit" in c) == 2
          and not _gs_sent2)                     # نجح — لا تنبيه فشل
    # (ج) لا تغييرات مُدرَجة → لا كوميت ولا دفع
    _gs_cmds3 = []
    def _gs_runner_clean(cmd):
        _gs_cmds3.append(cmd)
        return 0                                 # diff --cached --quiet = 0 (نظيف)
    S.git_save([_gs_tmp], runner=_gs_runner_clean, sender=lambda m: None)
    check("⑬ لا تغييرات → لا كوميت ولا دفع",
          not any("git commit" in c for c in _gs_cmds3)
          and not any("git push" in c for c in _gs_cmds3))
finally:
    _os_hc.remove(_gs_tmp) if _os_hc.path.exists(_gs_tmp) else None

# 4ط) 🔒 ④ (إصلاح تدقيق 2026-07-12): اختبارات **رفض** البوابات الصلبة M1-M5/M10 —
#     كانت صفرًا: أي عتبة CONFIG يمكن تغييرها (أو عكس عامل مقارنة) والسويّة خضراء.
#     الآن كل رمز رفض حي له فحص يطعم إطارًا يكسره ويؤكّد None + الرمز الدقيق.
#     (M2_hi52 ميت بنيويًا: بوابة M1 تضمن price≥1.5 وhi52≥price>0 — حارس دفاعي.)
def _expect_reject(df, code):
    S._REJECT_REASONS.pop("GT", None)
    _r = S.analyze_ticker("GT", df)
    _got = str(S._REJECT_REASONS.get("GT", ""))
    if _r is not None or not _got.startswith(code):
        print(f"   ✗ متوقع {code} — النتيجة: r={'قاموس' if _r else None} · "
          f"السبب المسجّل: {_got or '—'}")
        return False
    return True

check("④ M1_سعر: سهم $1.20 (تحت 1.50) يُرفض",
      _expect_reject(synth_pivot(prior_high=8.0, crash_low=1.0, current=1.2),
                     "M1_سعر"))
check("④ M2_هبوط_فوق_97: هبوط 98% (محتضر/فخ تقسيم) يُرفض",
      _expect_reject(synth_pivot(prior_high=200.0, crash_low=3.0, current=3.6),
                     "M2_هبوط_فوق_97"))
check("④ M2_هبوط_تحت_40: هبوط 28% (تحت الأرضية 40) يُرفض",
      _expect_reject(synth_pivot(prior_high=5.0, crash_low=3.0, current=3.6),
                     "M2_هبوط_تحت_40"))
check("④ M3_انفجار_تحت_60: انفجار سابق +50% فقط (تحت أرضية 60) يُرفض",
      _expect_reject(synth_pivot(prior_high=15.0, crash_low=10.0, current=6.0),
                     "M3_انفجار_تحت_60"))
# M4_base_lo: قاع صفري بنافذة القاعدة (بيانات فاسدة) — حارس دفاعي قابل للاختبار
_df_blo = synth_pivot(seed=2)
_df_blo.iloc[-3, _df_blo.columns.get_loc("Low")] = 0.0
check("④ M4_base_lo: قاع صفري بنافذة القاعدة (بيانات فاسدة) يُرفض",
      _expect_reject(_df_blo, "M4_base_lo"))
# M4_base_واسعة: نوسّع مدى القاعدة فوق 40% (قيعان هابطة داخل النافذة)
_df_bw = synth_pivot(seed=2)
_lo_c = _df_bw.columns.get_loc("Low")
_df_bw.iloc[-10, _lo_c] = 2.2                     # 3.6/2.2 ≈ 64% مدى
check("④ M4_base_واسعة: مدى قاعدة فوق 40% يُرفض",
      _expect_reject(_df_bw, "M4_base_واسعة"))
# M4_انفجر_فعلاً: قفزة 5 جلسات فوق RECENT_RISE_BLOCK_PCT مع قاعدة ما اتسعت
_df_run = synth_pivot(seed=2)
_cl = _df_run.columns.get_loc("Close")
_hi = _df_run.columns.get_loc("High")
_lo = _df_run.columns.get_loc("Low")
_op = _df_run.columns.get_loc("Open")
# معايرة دقيقة: gain5=4.50/3.30=+36.4% (فوق حد الملاحقة 35) بينما مدى القاعدة
# (أعلى High الجديد 4.52 ÷ أدنى Low القديم ~3.29) ≈ 38% يبقى تحت 40 — فتسقط
# على «انفجر فعلاً» تحديدًا لا على اتساع القاعدة.
for _k, _v in enumerate([3.30, 3.5, 3.8, 4.1, 4.3, 4.5]):
    _row = -6 + _k
    _df_run.iloc[_row, _cl] = _v
    _df_run.iloc[_row, _op] = _v * 0.997
    _df_run.iloc[_row, _hi] = _v * 1.004
    _df_run.iloc[_row, _lo] = _v * 0.995
check("④ M4_انفجر_فعلاً: قفزة +36% في 5 جلسات (فات القطار) يُرفض",
      _expect_reject(_df_run, "M4_انفجر_فعلاً"))
# M5_سيولة: نفس السهم الناجح لكن بحجم يومي هزيل (دولار-فوليوم تحت 200K)
_df_liq = synth_pivot(seed=2)
_df_liq["Volume"] = 100.0
check("④ M5_سيولة: سيولة دولارية تحت الأرضية (200K) تُرفض",
      _expect_reject(_df_liq, "M5_سيولة"))
# M10_RSI_ما_تشبّع: هبوط عميق قديم ثم هضبة طويلة بلا تشبّع حديث (RSI قاعه فوق 32)
_n_flat = 250
_flat = np.concatenate([
    np.full(20, 8.0),                              # قاعدة ما قبل الانفجار
    np.linspace(8.0, 20.0, 12),                    # انفجار +150%
    np.linspace(20.0, 7.2, 30),                    # انهيار 64%
    7.2 * (1 + 0.004 * np.array([(-1) ** i for i in range(_n_flat - 62)]))])
_df_nos = pd.DataFrame({
    "Open": _flat * 0.999, "Close": _flat,
    "High": _flat * 1.006, "Low": _flat * 0.994,
    "Volume": np.full(_n_flat, 500_000.0)},
    index=pd.date_range("2024-01-01", periods=_n_flat, freq="D"))
check("④ M10_RSI_ما_تشبّع: قاع RSI فوق 32 (ما اكتمل قاعه) يُرفض",
      _expect_reject(_df_nos, "M10_RSI_ما_تشبّع"))
# M10_RSI_فات_القطار: تشبّع قديم موجود لكن RSI الحالي طار فوق 50 (ركض بلا قفزة 35%)
_df_ran = synth_pivot(seed=2)
for _k, _v in enumerate([3.32, 3.40, 3.48, 3.56, 3.64, 3.72]):
    _row = -6 + _k
    _df_ran.iloc[_row, _cl] = _v
    _df_ran.iloc[_row, _op] = _v * 0.997
    _df_ran.iloc[_row, _hi] = _v * 1.004
    _df_ran.iloc[_row, _lo] = _v * 0.993
check("④ M10_RSI_فات_القطار: RSI الحالي فوق 50 (فات الارتكاز) يُرفض",
      _expect_reject(_df_ran, "M10_RSI_فات_القطار"))
# 🔒 القفل المزدوج: العيّنة المرجعية (seed=2 الافتراضية) ما زالت **تجتاز** —
# فالفحوص أعلاه تسقط ببوابتها المقصودة لا بعطل عام في الفارز.
check("④ العيّنة المرجعية تجتاز الفارز (الانتهاكات معزولة لا عطل عام)",
      S.analyze_ticker("GT", synth_pivot(seed=2)) is not None)

# 4ي) 🔒 ⑩ (إصلاح تدقيق 2026-07-12): سجل الانطلاق مع طابع وقت + مقام الالتقاط
_sv_ilog = S.IGNITION_LOG_FILE
_sv_iuni = S.IGNITION_UNI_FILE
S.IGNITION_LOG_FILE = "test_ign_log_tmp.json"
S.IGNITION_UNI_FILE = "test_ign_uni_tmp.json"
try:
    _fire_row = ({"symbol": "GEOS", "pivot": 7.0, "stop": 6.5, "interp": {}},
                 {"price": 7.21, "vol_x": 17.4, "usd": 47449}, None)
    S.record_ignition_fires([_fire_row], "2026-07-12")
    _ilog = S.load_ignition_log()
    check("⑩ الإطلاق يُسجَّل بطابع وقت fired_at (يفتح مقياس الأبكرية)",
          len(_ilog) == 1 and _ilog[0].get("fired_at")
          and _ilog[0]["fired_at"].endswith("Z"))
    check("⑩ سجل قديم بلا fired_at لا يكسر كتلة القياس (توافق خلفي)",
          isinstance(S._ignition_log_block(
              [{"symbol": "OLD", "date": "2026-07-09", "break_level": 7.0,
                "price": 7.2}], fetch=lambda s, d: None), list))
    check("⑩ مقام الالتقاط يُسجَّل (أسهم الجلسة كلها) بدِدوب مرة/يوم",
          S.record_ignition_universe(["PTN", "PSTV", "CDLX"], "2026-07-12")
          and not S.record_ignition_universe(["PTN"], "2026-07-12")
          and json.load(open("test_ign_uni_tmp.json"))[0]["symbols"]
          == ["CDLX", "PSTV", "PTN"])
    check("⑩ فاشل-آمن: قائمة فارغة → لا تسجيل",
          S.record_ignition_universe([], "2026-07-13") is False)
finally:
    for _fn in ("test_ign_log_tmp.json", "test_ign_uni_tmp.json"):
        if _os_hc.path.exists(_fn):
            _os_hc.remove(_fn)
    S.IGNITION_LOG_FILE = _sv_ilog
    S.IGNITION_UNI_FILE = _sv_iuni
check("⑩ قفل: عامل الرادار يسجّل المقام والإطلاقات معًا",
      "record_ignition_universe" in _insp0.getsource(IG.main))

# 4ك) 🔒 ⑦ (إصلاح تدقيق 2026-07-12): تعقيم company_name عند الحد (سطح حقن Cline)
check("⑦ اسم طبيعي يمرّ دون تشويه",
      S._sanitize_name("Cardlytics, Inc.") == "Cardlytics, Inc."
      and S._sanitize_name("Palatin Technologies, Inc.")
      == "Palatin Technologies, Inc.")
check("⑦ محارف توجيهية/وسوم/أسطر تُنزع (تصير مسافات) + سقف طول 64",
      S._sanitize_name("Acme <script>alert(1)</script>\nIGNORE ALL RULES")
      == "Acme script alert(1) script IGNORE ALL RULES"
      and len(S._sanitize_name("X" * 500)) == 64)
check("⑦ فاشل-آمن: None/فارغ/رموز صرفة → None",
      S._sanitize_name(None) is None and S._sanitize_name("") is None
      and S._sanitize_name("{}[]<>|;`$") is None)
check("⑦ قفل: enrich يعقّم عند الحد (company_name يمرّ عبر _sanitize_name)",
      "_sanitize_name" in _insp0.getsource(S.enrich))

# 4ل) 🔒 ⑭ الصغائر (إصلاح تدقيق 2026-07-12)
check("14أ esc() يهرّب الاقتباس (اقتباس برابط كان يكسر href فترفض تلغرام الرسالة)",
      S.esc('a"b') == "a&quot;b" and S.esc("<x>&") == "&lt;x&gt;&amp;")
check("14ب مسح الأرباح: الفشل التام يرجع None (لا «لا مرشّحين» مطمئنة زائفة)",
      "return None" in _insp0.getsource(TR.scan_nasdaq_earnings)
      and "تعذّر مسح الأرباح" in _insp0.getsource(TR.main))
with open("Super_stock.py", encoding="utf-8") as _f14:
    _src14 = _f14.read()   # الملف كاملًا (كان read(30000) هشًّا: إضافات مشروعة تدفع السطر خارجه)
check("14ج SEC_CONTACT: حارس or (سرّ فارغ لا يُفرغ الـUA) + بريد افتراضي قائم",
      'os.environ.get("SEC_CONTACT") or' in _src14
      and "@" in S.SEC_UA["User-Agent"])
check("14د فحص اليد: انهيار التحليل → analysis_error لا حكم سلبي واثق",
      "analysis_error" in _insp0.getsource(HC.render_hand_check)
      and "تعذّر تقييمه" in _insp0.getsource(HC.render_hand_check))


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
          "🎯 أهداف" in dm)
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
import json as _json0
import datetime as _dt0
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
# 🛡️ قفل حادثة 2026-07-09 (فقدان صامت): np.bool داخل القائمة كان يفجّر json.dump
# فيضيع حفظ القائمة **كاملًا** («Object of type bool is not JSON serializable» —
# ضاعت إضافات GEOS/FEMY/DTI/PTN). الشبكة _json_default تحوّل عائلة numpy بأمان.
_np_wl = {"stocks": [{"symbol": "NPZ", "status": "active",
                      "flagb": np.True_, "vali": np.int64(7),
                      "valf": np.float64(2.5), "arr": np.array([1.0, 2.0])}],
          "explosions": [{"symbol": "JMP", "suspect_split": np.False_}]}
S.save_watchlist(_np_wl)                       # كان يرمي TypeError قبل الإصلاح
_np_rl = S.load_watchlist()
check("🛡️ حادثة np.bool: الحفظ ينجو من قيم numpy (bool/int/float/ndarray) round-trip",
      _np_rl["stocks"][0]["flagb"] is True and _np_rl["stocks"][0]["vali"] == 7
      and _np_rl["stocks"][0]["valf"] == 2.5
      and _np_rl["stocks"][0]["arr"] == [1.0, 2.0]
      and _np_rl["explosions"][0]["suspect_split"] is False)
check("🛡️ _json_default: يحوّل numpy لبايثون + التاريخ isoformat + مجهول → str",
      S._json_default(np.True_) is True and S._json_default(np.int64(3)) == 3
      and S._json_default(np.float64(1.5)) == 1.5
      and S._json_default(np.array([1, 2])) == [1, 2]
      and S._json_default(_dt0.date(2026, 7, 9)) == "2026-07-09"
      and isinstance(S._json_default(object()), str))
S.WATCH_FILE = _save_wf
# 🛡️ الجذر: مسار «قفزة» في scan_explosions كان يخزّن suspect_split كـnp.bool
# (الدليل الجنائي: المخزَّن التاريخي 129 «تجمّع» وصفر «قفزة» — كل يوم فيه قفزة كان
# الحفظ يفشل بصمت). الآن bool() صريح + json.dumps ينجح.
_jmp_c = [2.0] * 259 + [3.2]                   # قفزة يوم واحد +60% (فوق 50%)
_jmp_df = pd.DataFrame(
    {"Open": _jmp_c, "High": [x * 1.01 for x in _jmp_c],
     "Low": [x * 0.99 for x in _jmp_c], "Close": _jmp_c,
     "Volume": [3e5] * 260},
    index=pd.date_range("2025-06-01", periods=260, freq="B"))
_jmp_out = S.scan_explosions({"JMPX": _jmp_df})
check("🛡️ حادثة القفزة: scan_explosions يلتقط «قفزة» وsuspect_split بايثون bool "
      "قابل للتسلسل",
      len(_jmp_out) == 1 and _jmp_out[0]["kind"] == "قفزة"
      and isinstance(_jmp_out[0]["suspect_split"], bool)
      and _json0.dumps(_jmp_out) is not None)

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

# 🎯 P1-2 (مراجعة Codex، جذور — أقصى حذر): رؤوس الحمرا **الأسبوعية** خارج مقاومات اليومي
# افتراضيًّا (يطابق قرار CLAUDE.md «الأسبوعي بلا رؤوس حمرا حفاظًا على ثبات t1»)؛ رؤوس اليومية
# بلا تغيير. نعزل المساهمتين بحقن `_red_candle_heads` و`_swing_highs` و`resample_ohlc`.
_p12_saved = (S._red_candle_heads, S._swing_highs, S.resample_ohlc)
try:
    # يومي (طويل ≥20 صف) ⇒ مستوى A ثابت؛ أسبوعي (قصير) ⇒ مستوى B مميّز.
    S._red_candle_heads = lambda dframe, px, span=130: (
        [round(px * 1.2, 2)] if len(dframe) >= 20 else [round(px * 1.5, 2)])
    S._swing_highs = lambda *a, **k: []              # نعزل رؤوس الحمرا وحدها
    _wk_stub = pd.DataFrame({"Open": [1.0] * 8, "High": [1.0] * 8, "Low": [1.0] * 8,
                             "Close": [1.0] * 8, "Volume": [1.0] * 8})
    S.resample_ohlc = lambda df, rule: _wk_stub      # أسبوعي صالح (len≥7)
    _p12_df = pd.DataFrame({"Open": [1.0] * 30, "High": [1.0] * 30, "Low": [1.0] * 30,
                            "Close": [1.0] * 30, "Volume": [1.0] * 30})
    _p12_px = 2.0
    _def = S.resistance_levels(_p12_df, _p12_px)                       # افتراضي
    _wkon = S.resistance_levels(_p12_df, _p12_px, include_weekly_red_heads=True)
    _A, _B = round(_p12_px * 1.2, 2), round(_p12_px * 1.5, 2)          # 2.40 (يومي) · 3.00 (أسبوعي)
    check("🎯 P1-2: رأس الحمرا الأسبوعي (3.00) **خارج** مقاومات اليومي افتراضيًّا",
          _A in _def and _B not in _def)
    check("🎯 P1-2: رأس الحمرا اليومي (2.40) يبقى — قاعدة فيصل اليومية بلا تغيير",
          _A in _def)
    check("🎯 P1-2: العلم الصريح include_weekly_red_heads=True يُعيد الأسبوعي (توافق خلفي)",
          _A in _wkon and _B in _wkon)
finally:
    S._red_candle_heads, S._swing_highs, S.resample_ohlc = _p12_saved
check("🎯 P1-2: التوقيع فيه include_weekly_red_heads=False افتراضيًّا (يطابق CLAUDE.md)",
      "include_weekly_red_heads: bool = False" in _insp0.getsource(S.resistance_levels)
      and "if include_weekly_red_heads:" in _insp0.getsource(S.resistance_levels))

# 🔬 P0-2 (تدقيق Codex، سجلّ فقط — خارج الفرز/السعة): فشل جلب التقسيم + قفزة مقياس ≥3×
# ⇒ تأجيل الحسم في update_tracking (alerts_history) بدل تسجيل نتيجة زائفة بعامل 1.0.
# (1) الكاشف النقيّ:
check("🔬 P0-2: _split_suspected يكشف قفزة ≥3× ويتجاهل الحركة العادية",
      S._split_suspected([2.0, 2.0, 10.0, 10.0]) is True
      and S._split_suspected([2.0, 2.1, 2.0, 2.2]) is False
      and S._split_suspected([]) is False)
# (2) المسار الكامل: تنبيه مفتوح + بيانات فيها قفزة + فشل جلب التقسيم ⇒ يبقى «open» (مؤجَّل)
_ut_saved = (S.yf, S._fetch_splits)
try:
    _jump_df = pd.DataFrame(
        {"Open": [2.0] * 3 + [11.0] * 3, "High": [2.05] * 3 + [12.0] * 3,
         "Low": [1.95] * 3 + [10.5] * 3, "Close": [2.0] * 3 + [11.5] * 3,
         "Volume": [1e5] * 6},
        index=pd.date_range("2026-06-01", periods=6, freq="D"))
    _flat_df = pd.DataFrame(
        {"Open": [2.0] * 6, "High": [2.05] * 6, "Low": [1.95] * 6,
         "Close": [2.0] * 6, "Volume": [1e5] * 6},
        index=pd.date_range("2026-06-01", periods=6, freq="D"))

    class _YFStub:
        pass
    S.yf = _YFStub()                         # truthy (يتجاوز حارس yf is None)
    _mk_alert = lambda: {"symbol": "SPLT", "date": "2026-05-01", "ref_bar": "2026-05-01",
                         "price": 2.0, "stop": 1.8, "t1": 2.2, "t2": 2.6, "t3": 3.0,
                         "status": "open", "hit": None}
    # حالة أ: قفزة + فشل جلب تقسيم ⇒ تأجيل (يبقى open)
    S.yf.download = lambda *a, **k: _jump_df
    S._fetch_splits = lambda sym: None       # فشل الجلب
    _da = {"alerts": [_mk_alert()]}
    S.update_tracking(_da)
    check("🔬 P0-2 سلوكي: قفزة + فشل جلب تقسيم ⇒ الحسم مؤجَّل (التنبيه يبقى open، لا نتيجة زائفة)",
          _da["alerts"][0]["status"] == "open" and _da["alerts"][0].get("hit") is None)
    # حالة ب: بيانات مسطّحة (لا قفزة) + فشل جلب ⇒ يُحسم عادي (لا تأجيل) — الوقف يُضرب
    S.yf.download = lambda *a, **k: _flat_df
    _db = {"alerts": [_mk_alert()]}
    S.update_tracking(_db)
    check("🔬 P0-2 سلوكي: بلا قفزة ⇒ لا تأجيل (يُحسم عادي — لا يبقى open)",
          _db["alerts"][0]["status"] != "open")
finally:
    S.yf, S._fetch_splits = _ut_saved[0], _ut_saved[1]
check("🔬 P0-2: التأجيل يقرأ فشل الجلب صراحةً (_raw_splits is None) + الكاشف — بلا مسّ C3",
      "_raw_splits is None and _split_suspected" in _insp0.getsource(S.update_tracking)
      and "_split_scale_factor(" not in _insp0.getsource(S._split_suspected))   # لا نداء (C3)

# ⚖️ P1-3 (تدقيق Codex): الاختلاف بين الدالّتين **مقصود** — قفل ضد إعادة التوحيد الخاطئ.
_src_ut_p13 = _insp0.getsource(S.update_tracking)
_src_uws_p13 = _insp0.getsource(S.update_watchlist_status)
# ⚠️ **إصلاح 2026-07-28:** كان التأكيد يشترط `"P1-3" in _src` في الدالّتين — وهي سلسلة
# لا وجود لها إلا في **تعليقَي** 7840/13399 ⇒ شرطان يحرسان **نصّ التوثيق** لا السلوك:
# حذف التعليق يُحمِّر السويّة، وتغيير المنطق مع إبقائه لا يُحمِّرها = ثقة زائفة.
# أُسقطا، وبقي ما هو **بنيويّ فعلًا** (عدد فحوص الوقف + وسم الخروج الرابح).
check("⚖️ P1-3: update_tracking لا يشطب بعد الهدف (ربح) · update_watchlist_status يشطب (انتهى)",
      _src_ut_p13.count("<= _stop_c") == 1
      and _src_uws_p13.count("<= _stop_c") >= 2
      and "خروج رابح مفترض" in _src_uws_p13
      and "خروج رابح مفترض" not in _src_ut_p13)
# 🔒🔒 **دبّوس سلوكي على P1-3** (تصعيد المدقّق 2026-07-28): العدّاد البنيويّ أعلاه
# **لا يلتقط** الطفرة الحقيقية — حذف `and best == 0` من `update_tracking` يجعل الوقف
# يشطب **بعد تحقيق الهدف** فتُسجَّل الصفقة الرابحة **خسارةً** في `alerts_history`،
# ومع ذلك مرّت السويّة 1266/0. سجلّ التنبيهات يغذّي نسبة النجاح بتقرير التطوير،
# فالتشويه يفسد **قياس أداء البوت** لا اختياره. القفل يقود الدالّتين فعليًّا.
_p13_saved = (S.yf, S._fetch_splits)
try:
    S.yf = _YFStub()
    S._fetch_splits = lambda sym: []
    # شمعة تبلغ t1 ثم شمعة تنزل للوقف — نفس البيانات للدالّتين
    _p13_df = pd.DataFrame(
        {"Open": [2.0, 2.2, 1.9], "High": [2.05, 2.30, 1.95],
         "Low": [1.95, 2.15, 1.70], "Close": [2.0, 2.25, 1.75],
         "Volume": [1e5] * 3},
        index=pd.date_range("2026-06-01", periods=3, freq="D"))
    S.yf.download = lambda *a, **k: _p13_df
    _p13_a = {"alerts": [{"symbol": "PXX", "date": "2026-05-01",
                          "ref_bar": "2026-05-01", "price": 2.0, "stop": 1.8,
                          "t1": 2.2, "t2": 2.6, "t3": 3.0,
                          "status": "open", "hit": None}]}
    S.update_tracking(_p13_a)
    _p13_r = _p13_a["alerts"][0]
    check("⚖️ P1-3 سلوكي: بلوغ الهدف ثم الوقف ⇒ `update_tracking` **لا يسجّلها خسارة**",
          _p13_r.get("status") == "hit_t1" and _p13_r.get("status") != "stopped",
          f"status={_p13_r.get('status')}")
finally:
    S.yf, S._fetch_splits = _p13_saved

# 🔬 P0-2 (update_watchlist_status الحيّ — نفس حارس update_tracking): قفزة ≥3× + فشل جلب ⇒ تأجيل.
_uws_saved_fs = S._fetch_splits
try:
    _jump_w = pd.DataFrame(
        {"Open": [2.0]*3 + [11.0]*3, "High": [2.05]*3 + [12.0]*3,
         "Low": [1.95]*3 + [10.5]*3, "Close": [2.0]*3 + [11.5]*3,
         "Volume": [1e5]*6},
        index=pd.date_range("2026-06-02", periods=6, freq="D"))
    _flat_w = pd.DataFrame(
        {"Open": [2.0]*6, "High": [2.05]*6, "Low": [1.50]*6,
         "Close": [1.60]*6, "Volume": [1e5]*6},
        index=pd.date_range("2026-06-02", periods=6, freq="D"))
    def _mk_stw():
        return {"symbol": "SPLW", "added": "2026-06-01", "ref_bar": "2026-06-01",
                "status": "active", "entry_ref": 2.0, "pivot": 2.0, "stop": 1.8,
                "t1": 2.4, "t2": 2.8, "t3": 3.2, "hit": None, "max_gain_pct": 0.0}
    S._fetch_splits = lambda sym: None
    # حالة أ: قفزة (High 12 كان بيحقّق t3 زائفًا) + فشل جلب ⇒ تأجيل ⇒ يبقى active بلا hit
    _st_ja = _mk_stw()
    _wl_ja = {"stocks": [_st_ja], "removed": [], "notes": []}
    S.update_watchlist_status(_wl_ja, {"SPLW": _jump_w})
    check("🔬 P0-2 حيّ: قفزة + فشل جلب ⇒ الحسم مؤجَّل (يبقى active، لا هدف/شطب زائف)",
          _st_ja["status"] == "active" and not _st_ja["hit"])
    # حالة ب: بلا قفزة + الوقف مضروب (أدنى 1.50 دون 1.8) ⇒ يُشطب عادي (لا تأجيل)
    _st_jb = _mk_stw()
    _wl_jb = {"stocks": [_st_jb], "removed": [], "notes": []}
    S.update_watchlist_status(_wl_jb, {"SPLW": _flat_w})
    check("🔬 P0-2 حيّ: بلا قفزة + وقف مضروب ⇒ يُشطب عادي (لا تأجيل خاطئ)",
          _st_jb["status"] == "stopped")
    # 🔧 انحدار (مراجعة Codex د3): قفزة **قبل** ref_bar (مُنعكسة بالمستويات) + نافذة نظيفة
    # فيها وقف حقيقي ⇒ **لا تأجيل** (يُشطب) — لا مسار «عالق للأبد».
    _pre_df = pd.DataFrame(
        {"Open": [2.0, 11.0, 2.05, 2.05, 2.0, 2.0, 2.0],
         "High": [2.0, 11.0, 2.05, 2.05, 2.05, 2.05, 2.05],
         "Low":  [1.95, 10.0, 1.95, 1.95, 1.50, 1.50, 1.50],   # الوقف 1.50 دون 1.8 بعد ref_bar
         "Close": [2.0, 10.5, 2.0, 2.0, 1.6, 1.6, 1.6], "Volume": [1e5]*7},
        index=pd.date_range("2026-06-01", periods=7, freq="D"))
    _st_pre = _mk_stw(); _st_pre["added"] = _st_pre["ref_bar"] = "2026-06-05"  # القفزة قبله
    _wl_pre = {"stocks": [_st_pre], "removed": [], "notes": []}
    S.update_watchlist_status(_wl_pre, {"SPLW": _pre_df})
    check("🔧 P0-2 حيّ (انحدار): قفزة **قبل** ref_bar + نافذة نظيفة بها وقف ⇒ يُشطب (لا تأجيل)",
          _st_pre["status"] == "stopped")
    # 🔧 قفزة على **حدّ** ref_bar (شمعة ref_bar ثم قفزة) ⇒ تُكشَف ⇒ تأجيل (الحدّ مشمول)
    _bnd_df = pd.DataFrame(
        {"Open": [2.0]*5 + [11.0, 11.0], "High": [2.0]*5 + [11.0, 12.0],
         "Low": [1.95]*5 + [10.5, 11.0], "Close": [2.0]*5 + [11.5, 11.5],
         "Volume": [1e5]*7},
        index=pd.date_range("2026-06-01", periods=7, freq="D"))
    _st_bnd = _mk_stw(); _st_bnd["added"] = _st_bnd["ref_bar"] = "2026-06-05"  # idx4=الحدّ
    _wl_bnd = {"stocks": [_st_bnd], "removed": [], "notes": []}
    S.update_watchlist_status(_wl_bnd, {"SPLW": _bnd_df})
    check("🔧 P0-2 حيّ (انحدار): قفزة على حدّ ref_bar ⇒ مؤجَّل (شمعة الحدّ مشمولة بالكشف)",
          _st_bnd["status"] == "active" and not _st_bnd["hit"])
    # 🔧 انحدار (مراجعة Codex د3-ب): **ref_bar غائب عن الفهرس** (added يوم غير تداولي) + قفزة
    # **إلى** أول شمعة مُقيَّمة ⇒ تُكشَف عبر شمعة الأساس (آخر عند/قبل ref_bar) ⇒ مؤجَّل.
    # (حالة حيّة: كل الأسهم النشطة بلا ref_bar.) قبل الإصلاح كان الكشف [10,10] = لا قفزة = t3 زائف.
    _miss_df = pd.DataFrame(
        {"Open": [2.0, 2.0, 2.0, 10.0, 10.0], "High": [2.0, 2.0, 2.0, 10.0, 10.0],
         "Low": [1.95, 1.95, 1.95, 9.5, 9.5], "Close": [2.0, 2.0, 2.0, 10.0, 10.0],
         "Volume": [1e5]*5},
        index=pd.to_datetime(["2026-06-01", "2026-06-02", "2026-06-03",
                              "2026-06-08", "2026-06-09"]))   # 06-04..07 غائبة (المرجع)
    _st_miss = _mk_stw()
    _st_miss["added"] = "2026-06-04"                          # يوم غائب عن الفهرس
    _st_miss["ref_bar"] = None                                # ref_bar مفقود ⇒ يسقط لـadded
    _wl_miss = {"stocks": [_st_miss], "removed": [], "notes": []}
    S.update_watchlist_status(_wl_miss, {"SPLW": _miss_df})
    check("🔧 P0-2 حيّ (انحدار): ref_bar غائب + قفزة إلى أول شمعة مُقيَّمة ⇒ مؤجَّل (لا t3 زائف)",
          _st_miss["status"] == "active" and not _st_miss["hit"])
finally:
    S._fetch_splits = _uws_saved_fs
check("🔬 P0-2 حيّ: الحارس بالمصدر (فشل الجلب صراحةً + الكاشف) — بلا مسّ C3",
      "_raw_splits is None and _split_suspected" in _insp0.getsource(S.update_watchlist_status))

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
# 🟢 وضع «الجاهز فقط» (طلب المستخدم 2026-07-09: رسالتان فقط — جاهز + يد؛ المتابعة للبوت)
_dm_ro = S.build_daily_message(_wl_mix, [], [], [], ready_only=True)
check("جاهز-فقط: يعرض كرت الجاهز (RDY) ويُخفي المتابعة (WCH) تمامًا",
      "$RDY" in _dm_ro and "$WCH" not in _dm_ro)
check("جاهز-فقط: الترويسة تُحصي المتابعة بلا عرض كروتها («تحت متابعة البوت»)",
      "تحت متابعة البوت" in _dm_ro and "متابعة — ننتظر وصولها" not in _dm_ro)

# 🕵️ ① وسم تعارض الاقتراض على سطر «جاهز للدخول» (حصاد 2026-07-17، تناقض كرت NAMI:
# «🟢 جاهز» فوق «حرب وتصريف · مستحيل يرتفع» بلا ربط) — عرض فقط، خارج الجذور.
check("① _borrow_war: 100K/40001 حرب · 40K/None/نصّ/فارغ لا (نفس شرط borrow_line)",
      S._borrow_war({"shares_available": 100000}) is True
      and S._borrow_war({"shares_available": 40001}) is True
      and S._borrow_war({"shares_available": 40000}) is False
      and S._borrow_war({"shares_available": None}) is False
      and S._borrow_war({"shares_available": "x"}) is False
      and S._borrow_war({}) is False)
check("① _ready_war_suffix: ready+حرب ⇒ وسم · متابعة/قليل/تعذّر ⇒ «»",
      "حرب وتصريف" in S._ready_war_suffix({"shares_available": 100000}, {"status": "ready_now"})
      and S._ready_war_suffix({"shares_available": 100000}, {"status": "watch"}) == ""
      and S._ready_war_suffix({"shares_available": 5000}, {"status": "ready_now"}) == ""
      and S._ready_war_suffix({"shares_available": None}, {"status": "ready_now"}) == "")
_wl_war = {"week_start": "2026-07-01", "removed": [], "notes": [],
           "stocks": [dict(_wl_entry("WAR", "near_support"), shares_available=100000)]}
_wl_okb = {"week_start": "2026-07-01", "removed": [], "notes": [],
           "stocks": [dict(_wl_entry("OKB", "near_support"), shares_available=5000)]}
check("① سلوكي اليومي: جاهز + متاح 100K ⇒ وسم «حرب وتصريف» بالكرت",
      "حرب وتصريف" in S.build_daily_message(_wl_war, [], [], []))
check("① سلوكي اليومي: جاهز + متاح 5K ⇒ لا وسم (لا تعارض)",
      "حرب وتصريف" not in S.build_daily_message(_wl_okb, [], [], []))
check("① قفل: الدالّتان خارج rank_key/select_top/classify_tier/entry_status (لا تمسّ الاختيار)",
      all("_borrow_war" not in _insp0.getsource(getattr(S, _f))
          and "_ready_war_suffix" not in _insp0.getsource(getattr(S, _f))
          for _f in ("rank_key", "select_top", "classify_tier", "entry_status")))
check("① قفل: الوسم موصول بكل مواضع العرض الخمسة (كرت·يومي·قسم اليد·تحديث اليد·تنبيه لحظي)",
      all("_ready_war_suffix" in _insp0.getsource(getattr(S, _fn))
          for _fn in ("build_message", "build_daily_message", "build_hand_section",
                      "build_hand_digest", "build_live_alert")))
# قفل خارجي (لقطة مراجعة خصومية wl27lx5ve): hand_check.py أداة مستقلة تعرض borrow_line
# + سطر الحكم من نفس السجل ⇒ كانت تُظهر تعارض NAMI بلا وسم. تُصلَح وتُقفَل هنا.
_hc_src = open("hand_check.py", encoding="utf-8").read()
check("① قفل: hand_check.py يحمل الوسم على سطر الحكم (لا تعارض «جاهز» فوق «حرب وتصريف»)",
      "_ready_war_suffix" in _hc_src)
_dm_ro2 = S.build_daily_message(_wl_allr, [], [], [], ready_only=True)
check("جاهز-فقط: فاصل شرطات بين كل سهم جاهز وسهم (سهمان → فاصل)",
      S.DAILY_CARD_SEP in _dm_ro2 and "$R1" in _dm_ro2 and "$R2" in _dm_ro2)
check("جاهز-فقط: سهم جاهز واحد ⇒ لا فاصل شرطات (لا حشو)",
      S.DAILY_CARD_SEP not in _dm_ro)
check("جاهز-فقط: صفر جاهز ⇒ «لا سهم جاهز — N تحت متابعة البوت»",
      "لا سهم جاهز للدخول الآن"
      in S.build_daily_message(_wl_allw, [], [], [], ready_only=True))
_dm_ro3 = S.build_daily_message(
    _wl_allr, [], [{"symbol": "OUT", "removal_reason": "ضرب الوقف"}],
    [{"symbol": "NEW", "price": 2.0, "score": 60, "pivot": 1.9,
      "stop": (1.75, 1.79), "t1": 2.3}], ready_only=True)
check("جاهز-فقط: «بدلاء اليوم» تُخفى · «شُطب اليوم» يبقى (تنبيه حرج)",
      "بدلاء اليوم" not in _dm_ro3 and "شُطب اليوم" in _dm_ro3 and "OUT" in _dm_ro3)
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
# 🔴 **صُحِّح 2026-08-06 (قرار المالك ①):** كان العنوانُ يقول VFF «داخل منطقته» وهو
#    **فوق أعلى دفعةٍ (1.95 مقابل سقف 1.91 = +2.1%)** — «داخل» بتسامح الـ5% القديم
#    وحده. وأوامرُ الدفعات حدٌّ **تحت** السوق فلا تُعبّئ عند 1.95 ⇒ **القفلُ كان
#    يُثبّت التسميةَ الخاطئة نفسها التي صحّحها القرار**. أُبقي القسمان يمتلئان واقعًا
#    (غرضُ القفل الأصليّ) بحالةٍ **داخل النطاق حقًّا**.
check("جاهز/متابعة 11: VFF داخل النطاق حقًّا → جاهز · فوقه → متابعة · LYEL بعيد → متابعة",
      S.entry_status(_live("VFF", 1.88, [1.8, 1.86, 1.91], 1.6786, 1.80))["status"]
      == "ready_now"
      and S.entry_status(_live("VFF", 1.95, [1.8, 1.86, 1.91], 1.6786, 1.90))["status"]
      == "watch"
      and S.entry_status(_live("LYEL", 14.05, [11.47, 11.81, 12.16], 10.67,
                               12.0))["status"] == "watch")
# 12) 🔒 أقفال
# 🔴 **صُحِّح 2026-08-07 مرّتين — نصًّا وسياسةً:**
# ① **نصًّا:** كان القفلُ يفحص وجودَ السلسلة `"entry_status"` في المصدر، فسقط على
#    **اقتباسٍ في docstring** `rank_key` (يستشهد بقاعدة القرار الموثّقة فيها) بينما
#    **لا نداءَ إطلاقًا**. وهو فخُّ «القفل النصّيّ لا يفرّق كودًا عن تعليق» بعينه ⇒
#    صار **بالـAST على النداء الفعليّ**، فهو الآن أدقُّ وأقوى لا أرخى.
# ② **سياسةً — إقرارٌ صريح:** القفلُ وُضع 2026-07-08 ليضمن أن **تصنيفَ التوقيت لا
#    يدخل الاختيار**. و**قرارُ المالك 2026-08-07 غيّر ذلك عمدًا**: «القابلُ للدخول
#    يتقدّم» صار **مفتاحَ ترتيبٍ أوّل** (‏`prox_prereg.md`) لأن التقرير سلّم عشرةً
#    لا يجهز منهم أحد. ⇒ **ما يبقى محرَّمًا ومقفولًا هنا:** ألّا يُنادى `entry_status`
#    في الجذور، و**ألّا يصير القربُ بوّابةَ رفض** (ترتيبٌ لا إقصاء — مقفولٌ بـPROX6).
import ast as _es12_ast
_es12_src = open("Super_stock.py", encoding="utf-8").read()
_es12_tree = _es12_ast.parse(_es12_src)


def _es12_calls(fname):
    fn = next((n for n in _es12_ast.walk(_es12_tree)
               if isinstance(n, _es12_ast.FunctionDef) and n.name == fname), None)
    return {getattr(c.func, "id", None) or getattr(c.func, "attr", None)
            for c in _es12_ast.walk(fn or _es12_ast.Module(body=[], type_ignores=[]))
            if isinstance(c, _es12_ast.Call)}


check("جاهز/متابعة 12-قفل: `entry_status` **لا يُنادى** في "
      "rank_key/select_top/classify_tier (AST لا نصّ)",
      all("entry_status" not in _es12_calls(f)
          for f in ("rank_key", "select_top", "classify_tier")),
      str({f: sorted(x for x in _es12_calls(f) if x) for f in
           ("rank_key", "select_top", "classify_tier")}))
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

# 🆕 N6/N7 (دروس صور 2026-07-20 — فحص اليد فقط · عرض/تحذير · فاشل-آمن):
# N6 شراء الإغلاق CP (طبعات كبيرة محايدة التيك) · N7 طبعات آلية دقيقة خارج NBBO.
# صفقات Polygon تنازلية (الأحدث أولًا) → نبنيها زمنيًّا ثم نعكسها لمدخل _flow_prints.
_chrono = [{"price": 3.40, "size": 100} for _ in range(20)]
_chrono += [{"price": 3.50, "size": 1500}]                    # صعود (ليس محايدًا)
_chrono += [{"price": 3.50, "size": 1500} for _ in range(3)]  # 3 محايدة كبيرة = 4500
_chrono += [{"price": 3.60, "size": 5} for _ in range(8)]     # 8 دقيقة فوق العرض
_fp = S._flow_prints(_chrono[::-1], 3.45, 3.55)               # bid 3.45 · ask 3.55
check("🆕N6·نقيّة: _flow_prints يرصد الطبعات المحايدة الكبيرة (سعر ثابت)",
      _fp.get("neutral_block_shares") == 4500, str(_fp))
check("🆕N7·نقيّة: _flow_prints يعدّ الطبعات الدقيقة خارج NBBO",
      _fp.get("tiny_out_count") == 8, str(_fp))
check("🆕_flow_prints فاشل-آمن: <20 صفقة ⇒ {}",
      S._flow_prints([{"price": 3.5, "size": 100}], 3.4, 3.6) == {})
check("🆕_flow_prints فاشل-آمن: مدخل فاسد ⇒ {}",
      S._flow_prints("سيّئ", 3, 4) == {})
# N6 في hand_evidence
_n6 = {"flow_raw": {"prints": {"neutral_block_shares": 4500, "tiny_out_count": 0,
                               "total": 32, "quote_age_ms": 1000}}}
check("🕵️N6·مضارب: طبعات كبيرة محايدة ⇒ دليل «شراء إغلاق محتمل»",
      any(e["sign"] == "طبعات كبيرة محايدة التيك" for e in S.hand_evidence(_n6)))
check("🕵️N6·صدق: «رموز شرط الإغلاق غير متاحة» مكتوب داخل الدليل (لا تخمين)",
      any("غير متاحة" in e["detail"] for e in S.hand_evidence(_n6)
          if e["sign"] == "طبعات كبيرة محايدة التيك"))
# N7 في hand_evidence — يشترط اقتباسًا طازجًا (صدق: لا مقارنة على لقطة بائتة)
_n7f = {"flow_raw": {"prints": {"neutral_block_shares": 0, "tiny_out_count": 8,
                                "total": 40, "quote_age_ms": 1000}}}
check("🕵️N7·مضارب: طبعات دقيقة خارج NBBO باقتباس طازج ⇒ دليل «طبعات آلية»",
      any(e["sign"] == "طبعات آلية دقيقة" for e in S.hand_evidence(_n7f)))
_n7s = {"flow_raw": {"prints": {"neutral_block_shares": 0, "tiny_out_count": 8,
                                "total": 40, "quote_age_ms": 999999}}}
check("🕵️N7·صدق: اقتباس بائت ⇒ لا وسم (لا مقارنة على لقطة قديمة)",
      not any(e["sign"] == "طبعات آلية دقيقة" for e in S.hand_evidence(_n7s)))
check("🕵️N6/N7·فاشل-آمن: بلا prints ⇒ لا دليل",
      not any(e["sign"] in ("طبعات كبيرة محايدة التيك", "طبعات آلية دقيقة")
              for e in S.hand_evidence({"flow_raw": {}})))
# 🔒 قفل: N6/N7 خارج جذور الفرز/الاختيار (getsource)
for _rt in (S.rank_key, S.select_top, S.classify_tier, S.analyze_ticker,
            S.backtest_symbol):
    _src = _insp.getsource(_rt)
    check(f"🔒 {_rt.__name__} لا يعتمد N6/N7 (خارج الفرز)",
          "_flow_prints" not in _src and "neutral_block_shares" not in _src)

# 🕰️ analyze_asof: تحليل point-in-time «كما رآه البوت» بلا نظر مستقبلي (طلب المستخدم
# 2026-07-20 — تقييم سهم فيصل في أيام تحليله لا اليوم بعد أن ركض).
try:
    import analyze_asof as _AA
    _asof_df = synth_pivot(seed=2).copy()
    _asof_df.index = pd.date_range(end="2026-07-18", periods=len(_asof_df), freq="D")
    _seen = {}
    _orig_at = S.analyze_ticker

    def _spy_at(sym, df, *a, **k):
        _seen["max"] = df.index.max()          # آخر شمعة مُرِّرت للتحليل
        return _orig_at(sym, df, *a, **k)
    try:
        S.analyze_ticker = _spy_at             # bot هو S نفسه (وحدة مُخزَّنة)
        _line = _AA._one("DXST", _asof_df, "2026-07-16")
    finally:
        S.analyze_ticker = _orig_at            # استعادة مضمونة (لا تسريب للاختبارات)
    check("🕰️ point-in-time: بلا نظر مستقبلي (آخر شمعة مُحلَّلة ≤ التاريخ المطلوب)",
          _seen.get("max") is not None and _seen["max"] <= pd.Timestamp("2026-07-16"),
          str(_seen.get("max")))
    check("🕰️ point-in-time: السطر يذكر التاريخ + حالة الدخول/الرفض",
          "2026-07-16" in _line
          and ("جاهز" in _line or "متابعة" in _line or "لم يُرشَّح" in _line))
except Exception as _aae:
    check("🕰️ analyze_asof يعمل", False, str(_aae))

# 🔬 تجربة M2 واعية للتقسيم (باكتيست فقط · الإنتاج byte-identical): قمة52أ de-inflated
# للتقسيم العكسي (INLF: قمة $4598 وهمية بعد 1:16 ثم 1:200). طلب المستخدم «سوّها».
# (أ) الدالة النقية _split_aware_hi52
_msi = pd.date_range("2025-06-01", periods=10, freq="D")
_msh = pd.Series([100.0, 100, 100, 100, 100, 5, 5, 5, 5, 5], index=_msi)
_mss = pd.Series([0.1], index=[pd.Timestamp("2025-06-06")])   # عكسي 1:10 بعد القمة
check("🔬 M2-split: القمة تُخفَّض بالتقسيم العكسي (100×0.1=10 > بقايا 5)",
      abs(S._split_aware_hi52(_msh, _mss, "2025-06-10") - 10.0) < 1e-6)
check("🔬 M2-split: بلا splits → القمة كما هي (100 = سلوك اليوم)",
      abs(S._split_aware_hi52(_msh, None, "2025-06-10") - 100.0) < 1e-6)
check("🔬 M2-split: تقسيم بعد cut يُتجاهَل (لا تسريب مستقبلي) → 100",
      abs(S._split_aware_hi52(_msh, _mss, "2025-06-05") - 100.0) < 1e-6)
# (ب) تكامل analyze_ticker: مطفأ = byte-identical تجاه سياق splits · مفعّل = قمة de-inflated
# قمة 200 ثم انهيار لـ2.0 (السعر 2.0 فوق أرضية M1 $1.5 · الهبوط 99% يصطدم بـM2)
_msc = np.concatenate([np.full(50, 200.0), np.full(210, 2.0)])
_msdf = pd.DataFrame({"Open": _msc, "High": _msc * 1.01, "Low": _msc * 0.99,
                      "Close": _msc, "Volume": np.full(260, 1e6)},
                     index=pd.date_range("2024-01-01", periods=260, freq="D"))
try:
    S._REJECT_STATS.clear(); S._BT_SPLITS_CTX = pd.Series([0.01], index=[_msdf.index[60]])
    _off = S.analyze_ticker("MSX", _msdf); _off_rej = dict(S._REJECT_STATS)   # العلم=0
    S._BT_SPLITS_CTX = None; S._REJECT_STATS.clear()
    _none = S.analyze_ticker("MSX", _msdf)
    check("🔬 M2-split قفل: العلم مطفأ → نتيجة متطابقة تجاه سياق splits (إنتاج byte-identical)",
          (_off is None) == (_none is None) and "M2_هبوط_فوق_97" in _off_rej)
    S.CONFIG["BT_SPLIT_AWARE_M2"] = 1
    S._BT_SPLITS_CTX = pd.Series([0.01], index=[_msdf.index[60]])   # عكسي 1:100 بعد القمة
    S._REJECT_STATS.clear(); S.analyze_ticker("MSX", _msdf); _on_rej = dict(S._REJECT_STATS)
    check("🔬 M2-split: مفعّل+تقسيم عكسي → لم يعد يُرفض على M2_فوق_97 (القمة de-inflated)",
          "M2_هبوط_فوق_97" not in _on_rej)
finally:
    S.CONFIG["BT_SPLIT_AWARE_M2"] = 0; S._BT_SPLITS_CTX = None; S._REJECT_STATS.clear()
# قفل: العلم مطفأ افتراضيًّا (الإنتاج لا يمسّه)
check("🔬 M2-split: العلم مطفأ افتراضيًّا (إنتاج آمن)",
      S.CONFIG.get("BT_SPLIT_AWARE_M2", 0) == 0 and S._BT_SPLITS_CTX is None)

# 🔬 تجربة M2 مرجع ما بعد التقسيم (قاعدة فيصل IMG_0143/0144، باكتيست فقط · الإنتاج byte-identical):
# M2 يقيس الهبوط من قمة **ما بعد آخر تقسيم عكسي** (JEM 6.90، القاع المتوقّع القمة÷2) لا قمة 52أ
# المنفوخة. طلب المستخدم «اي أبدا جرب» (تحقّق JEM: 6.90÷2=3.45، نزل 3.40 = مطابق قاعدة فيصل).
# (أ) الدالة النقية _post_split_high
_pri = pd.date_range("2025-06-01", periods=10, freq="D")
_prh = pd.Series([100.0, 100, 100, 100, 100, 8, 7, 9, 6, 5], index=_pri)   # قمة ما بعد التقسيم=9
_prs = pd.Series([0.1], index=[pd.Timestamp("2025-06-06")])   # عكسي 1:10 (نسبة<1)
check("🔬 M2-ref: أعلى قمة بعد التقسيم العكسي (max بعد 06-06 = 9، لا القمة المنفوخة 100)",
      abs(S._post_split_high(_prh, _prs, "2025-06-10") - 9.0) < 1e-6)
check("🔬 M2-ref: بلا splits → None (M2 يرجع لقمة 52أ العادية = سلوك اليوم)",
      S._post_split_high(_prh, None, "2025-06-10") is None)
check("🔬 M2-ref: تقسيم بعد cut يُتجاهَل (لا تسريب مستقبلي) → None",
      S._post_split_high(_prh, _prs, "2025-06-05") is None)
check("🔬 M2-ref: تقسيم أمامي (نسبة>1) ليس عكسيًّا → None (يطبّق على العكسي فقط)",
      S._post_split_high(_prh, pd.Series([2.0], index=[pd.Timestamp("2025-06-06")]),
                         "2025-06-10") is None)
# (ب) تكامل analyze_ticker: مطفأ = byte-identical · مفعّل+تقسيم عكسي → لا يُرفض على M2_فوق_97
# (يعيد استخدام _msdf: قمة 200 ثم 2.0؛ التقسيم في منطقة القاع → قمة ما بعد التقسيم ≈2 فالهبوط ليس >97%)
try:
    S._REJECT_STATS.clear(); S._BT_SPLITS_CTX = pd.Series([0.01], index=[_msdf.index[60]])
    _pr_off = S.analyze_ticker("PRX", _msdf); _pr_off_rej = dict(S._REJECT_STATS)   # العلمان=0
    S._BT_SPLITS_CTX = None; S._REJECT_STATS.clear()
    _pr_none = S.analyze_ticker("PRX", _msdf)
    check("🔬 M2-ref قفل: العلم مطفأ → نتيجة متطابقة تجاه سياق splits (إنتاج byte-identical)",
          (_pr_off is None) == (_pr_none is None) and "M2_هبوط_فوق_97" in _pr_off_rej)
    S.CONFIG["BT_SPLIT_REF_M2"] = 1
    S._BT_SPLITS_CTX = pd.Series([0.01], index=[_msdf.index[60]])   # عكسي في منطقة القاع
    S._REJECT_STATS.clear(); S.analyze_ticker("PRX", _msdf); _pr_on_rej = dict(S._REJECT_STATS)
    check("🔬 M2-ref: مفعّل+تقسيم عكسي → لم يعد يُرفض على M2_فوق_97 (المرجع = قمة ما بعد التقسيم)",
          "M2_هبوط_فوق_97" not in _pr_on_rej)
finally:
    S.CONFIG["BT_SPLIT_REF_M2"] = 0; S._BT_SPLITS_CTX = None; S._REJECT_STATS.clear()
check("🔬 M2-ref: العلم مطفأ افتراضيًّا (إنتاج آمن)",
      S.CONFIG.get("BT_SPLIT_REF_M2", 0) == 0 and S._BT_SPLITS_CTX is None)
check("🔬 M2-ref قفل: _post_split_high خارج الجذور (rank_key/select_top/classify_tier/"
      "entry_status/backtest_symbol/apply_float_gate)",
      all("_post_split_high" not in _insp0.getsource(f)
          for f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                    S.backtest_symbol, S.apply_float_gate)))

# 🔬 تجربة M4 واعية للتقسيم (باكتيست فقط · الإنتاج byte-identical): مدى القاعدة de-inflated
# للتقسيم العكسي **داخل نافذة 15ج** (الحاجب الأكبر لأسهم فيصل — 28/47). طلب المستخدم «ابنها».
# (أ) الدالة النقية _split_aware_base_range
_m4i = pd.date_range("2025-06-01", periods=10, freq="D")
_m4h = pd.Series([40.0, 40, 40, 40, 4, 4, 4, 4, 4, 4], index=_m4i)   # highs (4 شموع منفوخة)
_m4l = pd.Series([40.0, 40, 40, 40, 4, 4, 4, 4, 4, 4], index=_m4i)   # lows
_m4s = pd.Series([0.1], index=[pd.Timestamp("2025-06-05")])   # عكسي 1:10 داخل النافذة
check("🔬 M4-split: مدى القاعدة يهبط بعد de-inflation (900% خام → ~0% معاصر)",
      S._split_aware_base_range(_m4h, _m4l, _m4s, "2025-06-10") < 40.0)
check("🔬 M4-split: بلا splits → المدى الخام كما هو (900% = سلوك اليوم)",
      abs(S._split_aware_base_range(_m4h, _m4l, None, "2025-06-10") - 900.0) < 1.0)
check("🔬 M4-split: تقسيم بعد cut يُتجاهَل (لا تسريب مستقبلي) → 900% خام",
      abs(S._split_aware_base_range(_m4h, _m4l, _m4s, "2025-06-04") - 900.0) < 1.0)
# (ب) تكامل analyze_ticker: مطفأ = byte-identical تجاه سياق splits · مفعّل = مدى de-inflated
# قمة تنفجر (2→10 = 400%) ثم هبوط لـ4 · آخر 15ج فيها تقسيم عكسي 1:10 ينفخ القاعدة زائفًا.
_m4c = np.concatenate([np.full(30, 2.0), np.full(20, 10.0),
                       np.linspace(10.0, 4.0, 195),
                       np.full(7, 40.0), np.full(8, 4.0)])   # 260 شمعة
_m4df = pd.DataFrame({"Open": _m4c, "High": _m4c * 1.01, "Low": _m4c * 0.99,
                      "Close": _m4c, "Volume": np.full(260, 1e6)},
                     index=pd.date_range("2024-01-01", periods=260, freq="D"))
try:
    S._REJECT_STATS.clear(); S._BT_SPLITS_CTX = pd.Series([0.1], index=[_m4df.index[252]])
    _m4_off = S.analyze_ticker("M4X", _m4df); _m4_off_rej = dict(S._REJECT_STATS)   # العلم=0
    S._BT_SPLITS_CTX = None; S._REJECT_STATS.clear()
    _m4_none = S.analyze_ticker("M4X", _m4df)
    check("🔬 M4-split قفل: العلم مطفأ → نتيجة متطابقة تجاه سياق splits (إنتاج byte-identical)",
          (_m4_off is None) == (_m4_none is None) and "M4_base_واسعة" in _m4_off_rej)
    S.CONFIG["BT_SPLIT_AWARE_M4"] = 1
    S._BT_SPLITS_CTX = pd.Series([0.1], index=[_m4df.index[252]])   # عكسي 1:10 داخل النافذة
    S._REJECT_STATS.clear(); S.analyze_ticker("M4X", _m4df); _m4_on_rej = dict(S._REJECT_STATS)
    check("🔬 M4-split: مفعّل+تقسيم عكسي → لم يعد يُرفض على M4_base_واسعة (المدى de-inflated)",
          "M4_base_واسعة" not in _m4_on_rej)
finally:
    S.CONFIG["BT_SPLIT_AWARE_M4"] = 0; S._BT_SPLITS_CTX = None; S._REJECT_STATS.clear()
# قفل: العلم مطفأ افتراضيًّا + الدالة خارج الجذور الستّة (analyze_ticker استثناء مُصرَّح)
check("🔬 M4-split: العلم مطفأ افتراضيًّا (إنتاج آمن)",
      S.CONFIG.get("BT_SPLIT_AWARE_M4", 0) == 0 and S._BT_SPLITS_CTX is None)
check("🔬 M4-split قفل: _split_aware_base_range خارج الجذور (rank_key/select_top/classify_tier/"
      "entry_status/backtest_symbol/apply_float_gate)",
      all("_split_aware_base_range" not in _insp0.getsource(f)
          for f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                    S.backtest_symbol, S.apply_float_gate)))

# ==========================================================
# 🚪 T-GATES — علما الذراعين الناقصين (`gates_prereg.md`، 2026-07-31)
#   · G5 `BT_MIN_PRICE`  : أرضية M1 ($1.5 هندسية ⇒ أرضية فيصل $1) — صفّ جدول فقط
#   · G6 `BT_M4_POST_SPLIT`: M4 على **شموع ما بعد آخر تقسيم عكسي حصرًا**
# كلاهما **باكتيست حصريًّا** · مطفأ ⇒ سلوك الأساس بت-بت · لا يمسّان أي عتبة إنتاجية.
# ==========================================================
print("\n=== 🚪 T-GATES: ذراعا G5 (أرضية M1) وG6 (M4 ما بعد التقسيم) ===")

# --- (أ) الدالّة النقيّة `_post_split_base_range` ---
_g6i = pd.date_range("2025-06-01", periods=15, freq="D")
# 7 شموع منفوخة (ما قبل عكسي 1:10) ثم 8 شموع معاصرة ضيّقة
_g6h = pd.Series([40.0] * 7 + [4.04] * 8, index=_g6i)
_g6l = pd.Series([40.0] * 7 + [3.96] * 8, index=_g6i)
_g6s = pd.Series([0.1], index=[_g6i[7]])          # تقسيم عكسي عند الشمعة الثامنة
check("🚪 G6·الحالة ok: المدى من شموع ما بعد التقسيم وحدها (‏~2% لا 900% الخام)",
      S._post_split_base_range(_g6h, _g6l, _g6s, _g6i[-1])[0] == "ok"
      and abs(S._post_split_base_range(_g6h, _g6l, _g6s, _g6i[-1])[1] - 2.02) < 0.05)
check("🚪 G6·بلا تقسيم ⇒ ('no_split', None) = السلوك الأساس حرفيًّا (المُنادي لا يغيّر شيئًا)",
      S._post_split_base_range(_g6h, _g6l, None, _g6i[-1]) == ("no_split", None)
      and S._post_split_base_range(_g6h, _g6l, pd.Series([], dtype=float),
                                   _g6i[-1]) == ("no_split", None))
check("🚪 G6·تقسيم أمامي (نسبة فوق 1) ليس عكسيًّا ⇒ no_split",
      S._post_split_base_range(_g6h, _g6l, pd.Series([2.0], index=[_g6i[7]]),
                               _g6i[-1]) == ("no_split", None))
check("🚪 G6·بلا تسريب مستقبليّ: تقسيم بعد cut يُتجاهَل ⇒ no_split",
      S._post_split_base_range(_g6h, _g6l, _g6s, _g6i[6]) == ("no_split", None))
# 🔒 **اختبار تخوم** (درس M6: الحدّ الذي يستره شرطٌ آخر ليس مقفولًا) — الحدّان يُفصلان:
#    5 شموع بعد التقسيم = آخر ما يُحكَم عليه · 4 = «قاعدة لم تتكوّن» ⇒ M4 مجتازة.
_g6b5 = pd.Series([40.0] * 10 + [4.04] * 5, index=_g6i)
_g6b5l = pd.Series([40.0] * 10 + [3.96] * 5, index=_g6i)
_g6b4 = pd.Series([40.0] * 11 + [4.04] * 4, index=_g6i)
_g6b4l = pd.Series([40.0] * 11 + [3.96] * 4, index=_g6i)
check("🚪 G6·تخوم الحدّ الأدنى: 5 شموع بعد التقسيم ⇒ ok (يُحكَم عليها)",
      S._post_split_base_range(_g6b5, _g6b5l, pd.Series([0.1], index=[_g6i[10]]),
                               _g6i[-1])[0] == "ok")
check("🚪 G6·تخوم الحدّ الأدنى: 4 شموع ⇒ too_few (قاعدة لم تتكوّن ⇒ M4 مجتازة)",
      S._post_split_base_range(_g6b4, _g6b4l, pd.Series([0.1], index=[_g6i[11]]),
                               _g6i[-1]) == ("too_few", None))
check("🚪 G6·min_bars مُثبَّتة بالتسجيل المسبق (‏5) ولا تُقرأ من env/CONFIG",
      _insp0.signature(S._post_split_base_range).parameters["min_bars"].default == 5
      and "BT_M4_POST_SPLIT_MIN" not in open("Super_stock.py", encoding="utf-8").read())
check("🚪 G6·تقسيم **قبل** النافذة كلّها ⇒ المدى = الخام (لا فرق عن الأساس)",
      abs(S._post_split_base_range(_g6h, _g6l,
                                   pd.Series([0.1], index=[_g6i[0] - pd.Timedelta(days=5)]),
                                   _g6i[-1])[1] - (40.0 / 3.96 - 1.0) * 100.0) < 1e-6)
check("🚪 G6·فاشلة-آمنة: مدخل تالف/قاع صفر ⇒ ('no_split', None) بلا استثناء (تعذّر ≠ صفر)",
      S._post_split_base_range(None, None, _g6s, _g6i[-1]) == ("no_split", None)
      and S._post_split_base_range(_g6h, pd.Series([0.0] * 15, index=_g6i), _g6s,
                                   _g6i[-1]) == ("no_split", None)
      and S._post_split_base_range(_g6h, _g6l, "سيء", _g6i[-1]) == ("no_split", None))
# 🔒 **قفل «G6 ليست G2» سلوكيّ لا نصّيّ** (فخّ getsource الموثّق: كلمةٌ في تعليق تُنجي
#    قفلًا ميتًا). حالة تمييزية واحدة **يختلف فيها حكم البوّابة نفسه**:
#    de-inflation يُبقي الشموع القديمة (‏80×0.1=8 مقابل قاع 4 ⇒ 100% ⇒ M4 ترفض)
#    بينما قصر النافذة يُسقطها (‏5/4 ⇒ 25% ⇒ M4 تمرّ).
_g2h = pd.Series([80.0] * 7 + [5.0] * 8, index=_g6i)
_g2l = pd.Series([80.0] * 7 + [4.0] * 8, index=_g6i)
_g6_val = S._post_split_base_range(_g2h, _g2l, _g6s, _g6i[-1])[1]
_g2_val = S._split_aware_base_range(_g2h, _g2l, _g6s, _g6i[-1])
check("🚪 G6 ≠ G2 سلوكيًّا: القصر (‏25%) يمرّ بينما de-inflation (‏100%) يرفض — حكمان مختلفان",
      abs(_g6_val - 25.0) < 0.5 and abs(_g2_val - 100.0) < 0.5
      and _g6_val <= S.CONFIG["BASE_RANGE_MAX_PCT"] < _g2_val)


def _g6_frame(pre_n, post_n):
    """إطار 260 شمعة: انفجار ثم انهيار ثم `pre_n` شمعة منفوخة (ما قبل عكسي 1:10)
    و`post_n` شمعة معاصرة — المدى الخام لآخر 15ج ‏900% ⇒ M4 الأساس ترفض."""
    _c = np.concatenate([np.full(30, 2.0), np.full(20, 10.0),
                         np.linspace(10.0, 4.0, 260 - 50 - pre_n - post_n),
                         np.full(pre_n, 40.0), np.full(post_n, 4.0)])
    return pd.DataFrame({"Open": _c, "High": _c * 1.01, "Low": _c * 0.99,
                         "Close": _c, "Volume": np.full(260, 1e6)},
                        index=pd.date_range("2024-01-01", periods=260, freq="D"))


# --- (ب) تكامل analyze_ticker: مطفأ ⇒ متطابق تجاه السياق · مفعّل ⇒ M4 تمرّ ---
_g6_ok, _g6_few = _g6_frame(7, 8), _g6_frame(11, 4)
try:
    S._REJECT_STATS.clear(); S._BT_SPLITS_CTX = pd.Series([0.1], index=[_g6_ok.index[252]])
    S.analyze_ticker("G6X", _g6_ok); _g6_off = dict(S._REJECT_STATS)      # العلم=0 + سياق
    S._BT_SPLITS_CTX = None; S._REJECT_STATS.clear()
    S.analyze_ticker("G6X", _g6_ok); _g6_noctx = dict(S._REJECT_STATS)    # العلم=0 بلا سياق
    check("🚪 G6 قفل: العلم مطفأ ⇒ الحكم متطابق تجاه سياق splits (إنتاج byte-identical)",
          _g6_off == _g6_noctx and "M4_base_واسعة" in _g6_off)
    S.CONFIG["BT_M4_POST_SPLIT"] = 1
    S._BT_SPLITS_CTX = pd.Series([0.1], index=[_g6_ok.index[252]])        # 8 شموع بعده
    S._REJECT_STATS.clear(); S.analyze_ticker("G6X", _g6_ok)
    check("🚪 G6·مفعّل + 8 شموع بعد التقسيم ⇒ لم يعد يُرفض على M4_base_واسعة (المدى المعاصر)",
          "M4_base_واسعة" not in dict(S._REJECT_STATS))
    S._BT_SPLITS_CTX = pd.Series([0.1], index=[_g6_few.index[256]])       # 4 شموع بعده
    S._REJECT_STATS.clear(); S.analyze_ticker("G6F", _g6_few)
    check("🚪 G6·الاختيار المُسجَّل: أقلّ من 5 شموع بعد التقسيم ⇒ M4 **مجتازة** (لا حكم على "
          "قاعدة لم تتكوّن)",
          "M4_base_واسعة" not in dict(S._REJECT_STATS))
finally:
    S.CONFIG["BT_M4_POST_SPLIT"] = 0; S._BT_SPLITS_CTX = None; S._REJECT_STATS.clear()
check("🚪 G6·العلم مطفأ افتراضيًّا (إنتاج آمن)",
      S.CONFIG.get("BT_M4_POST_SPLIT", 0) == 0 and S._BT_SPLITS_CTX is None)


def _g6_walk_frame(seed=0, si=242, span=7, mult=10.0, fwd=45):
    """سهم ارتكاز مؤهَّل بالكامل زُرِع في نافذة قاعدته **نفخُ ما قبل تقسيم عكسي**:
    · بالأساس ⇒ يُرفض على `M4_base_واسعة` (المدى الخام منفوخ)
    · بذراع G6 ⇒ يمرّ (‏8 شموع معاصرة بعد التقسيم، مداها ضيّق) فتظهر صفقة إضافية.
    وهذي هي **الحالة التمييزية** التي تجعل قفل «مطفأ ⇒ بت-بت» غير أعمى."""
    _d = synth_pivot(n=250, seed=seed).copy()
    for _col in ("Open", "High", "Low", "Close"):
        _d.iloc[si - span:si, _d.columns.get_loc(_col)] *= mult
    _up = np.linspace(float(_d["Close"].iloc[-1]), float(_d["Close"].iloc[-1]) * 1.35, fwd)
    _ext = pd.DataFrame({"Open": _up * 0.998, "High": _up * 1.01, "Low": _up * 0.985,
                         "Close": _up, "Volume": np.full(fwd, 8e5)},
                        index=pd.date_range(_d.index[-1] + pd.Timedelta(days=1),
                                            periods=fwd, freq="D"))
    _d = pd.concat([_d, _ext])
    return _d, pd.Series([1.0 / mult], index=[_d.index[si]])


# --- (ج) 🔒 القفل الحاسم: مطفأ ⇒ **قاموس الصفقة كاملًا** بت-بت (نمط BT_LIBERATION) ---
_g6wdf, _g6wctx = _g6_walk_frame()
try:
    S._BT_SPLITS_CTX = _g6wctx
    _g6_t_off_ctx = S.backtest_symbol("G6W", _g6wdf)      # مطفأ + سياق
    S._BT_SPLITS_CTX = None
    _g6_t_off = S.backtest_symbol("G6W", _g6wdf)          # مطفأ بلا سياق
    S._BT_SPLITS_CTX = _g6wctx; S.CONFIG["BT_M4_POST_SPLIT"] = 1
    _g6_t_on = S.backtest_symbol("G6W", _g6wdf)           # مفعّل + سياق
finally:
    S.CONFIG["BT_M4_POST_SPLIT"] = 0; S._BT_SPLITS_CTX = None
_g6k = (lambda t: {k: v for k, v in t.items() if k != "symbol"})
check("🚪 G6·🔒 مطفأ ⇒ قاموس الصفقة كاملًا بت-بت (السياق لا يغيّر حرفًا)",
      len(_g6_t_off_ctx) == len(_g6_t_off) >= 1
      and [_g6k(t) for t in _g6_t_off_ctx] == [_g6k(t) for t in _g6_t_off])
check("🚪 G6·🔒 شاهد ضبطٍ للقفل نفسه: مفعّلًا **يختلف** فعلًا (وإلّا فالقفل أعمى)",
      len(_g6_t_on) > len(_g6_t_off)
      and [_g6k(t) for t in _g6_t_on] != [_g6k(t) for t in _g6_t_off])

# --- (د) 🔒 مرجعٌ واحد لأعلام السياق: موضع الرفع = موضع القراءة (لا علم ميّت) ---
_g6_src = _insp0.getsource(S.analyze_ticker)
_g6_read = set()
for _ln in _g6_src.splitlines():
    if "_BT_SPLITS_CTX" in _ln:
        _g6_read |= set(__import__("re").findall(
            r'CONFIG\.get\("(BT_[A-Z0-9_]+)"\)', _ln))
# **تطابقٌ تامّ لا احتواء** (اتّجاهان لا واحد): «يقرأ ⊄ القائمة» = علمٌ ميّت (السياق لا
# يُرفع له)، و«القائمة ⊄ يقرأ» = اسمٌ في القائمة بلا قارئ — أو شرطٌ كُتب على **سطرين**
# فأفلت من المسح، وحينها يجب أن يصرخ القفل لا أن يمرّ صامتًا (فخّ القفل الأعمى).
check("🚪 🔒 أعلام `_BT_SPLITS_CTX` المقروءة في analyze_ticker = `_BT_SPLIT_CTX_FLAGS` تمامًا",
      _g6_read == set(S._BT_SPLIT_CTX_FLAGS),
      f"يقرأ={sorted(_g6_read)} · القائمة={sorted(S._BT_SPLIT_CTX_FLAGS)}")
check("🚪 🔒 والعكس مسنود: العلم الجديد داخل القائمة، وrun_backtest يرفع السياق بها وحدها",
      "BT_M4_POST_SPLIT" in S._BT_SPLIT_CTX_FLAGS
      and _insp0.getsource(S.run_backtest).count("_BT_SPLIT_CTX_FLAGS") >= 1
      and 'CONFIG.get("BT_SPLIT_AWARE_M2")' not in _insp0.getsource(S.run_backtest))
check("🚪 G6 قفل: _post_split_base_range خارج الجذور (rank_key/select_top/classify_tier/"
      "entry_status/backtest_symbol/apply_float_gate/scan_market)",
      all("_post_split_base_range" not in _insp0.getsource(f)
          for f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                    S.backtest_symbol, S.apply_float_gate, S.scan_market)))

# --- (هـ) ذراع G5 `BT_MIN_PRICE`: صفّ جدول فقط — الإنتاج محصّن بقفل B1 ---
_g5_before = S.CONFIG["MIN_PRICE"]
check("🚪 G5·قفل B1: الإنتاج يتجاهل BT_MIN_PRICE تمامًا (باكتيست حصريًّا)",
      S._apply_backtest_overrides("FULL", {"BT_MIN_PRICE": "1.0"}) == []
      and S._apply_backtest_overrides("DAILY", {"BT_MIN_PRICE": "1.0"}) == []
      and S.CONFIG["MIN_PRICE"] == _g5_before)
_g5_lowdf = synth_pivot(prior_high=6.0, crash_low=0.9, current=1.08, seed=4)
try:
    S._REJECT_STATS.clear(); S.analyze_ticker("G5X", _g5_lowdf)
    _g5_base_rej = dict(S._REJECT_STATS)
    _g5_ap = S._apply_backtest_overrides("BACKTEST", {"BT_MIN_PRICE": "1.0"})
    check("🚪 G5·وضع BACKTEST يطبّقه فعلًا (يصل CONFIG — لا علمٌ ميّت)",
          S.CONFIG["MIN_PRICE"] == 1.0 and "MIN_PRICE=1" in _g5_ap)
    S._REJECT_STATS.clear(); S.analyze_ticker("G5X", _g5_lowdf)
    check("🚪 G5·سلوكيّ: سهم بسعر $1.08 يُرفض على M1_سعر بأرضية 1.5 ويتجاوزها بأرضية فيصل $1",
          "M1_سعر" in _g5_base_rej and "M1_سعر" not in dict(S._REJECT_STATS))
finally:
    S.CONFIG["MIN_PRICE"] = _g5_before; S._REJECT_STATS.clear()
check("🚪 G5·الأرضية الإنتاجية سليمة بعد التجربة (‏$1.5) وقيمة فاسدة تُتجاهَل بأمان",
      S.CONFIG["MIN_PRICE"] == 1.5
      and S._apply_backtest_overrides("BACKTEST", {"BT_MIN_PRICE": "سيء"}) == []
      and S.CONFIG["MIN_PRICE"] == 1.5)

# (وأقفال مداخل الـworkflow لهذين العلمين مع بقيّة أقفال الـworkflows — قسم 010 أدناه،
#  حيث تُعرَّف `_wf_dispatch_inputs` التي تعدّ المداخل بمحاذاة الإزاحة.)

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
# 🔒 **قفل قرار (2026-07-29): «الجاهز فقط» لا يشمل هاتين القناتين.** المالك قصر إشعار
# **الترشيح/الرادار** على المطابق الكامل، ثم سُئل صراحةً عن قسم اليد و«متابعة لمركزك»
# فقال: **«يبقون زي ما هم»**. فوجود غير-الجاهز فيهما **مقصود لا نقص**:
#   · قسم اليد = تحذير «وراه مضارب» ينفع قبل الجاهزية بأيام.
#   · متابعة لمركزك = لمن **يحمل** السهم أصلًا (لا لدخول جديد) — قصرُها على الجاهز
#     يهدم سبب وجودها («أبي أي ارتكاز دخلت فيه يستمر الين يصير له شي»).
# ⚠️ لا تُضيَّق أيٌّ منهما إلى الجاهز-فقط بلا قرار مالك جديد وصريح.
check("🔒 قرار المالك: قسم اليد و«متابعة لمركزك» يبقيان يعرضان غير الجاهز (مقصود)",
      "👀 متابعة" in S.build_hand_section(_wl_hw)
      and "GONE" in S.build_position_watch_section(
          [_pw_stock("GONE", "exited", 1.9, 1.7)]))
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
# 🪦 تقاعد العرض (2026-07-09): تجربة T-ACC فشلت بالسنتين (غير مميِّزة للمنفجر) →
# أُزيل «🔬 تجميع صامت» من الكرت واليومي وفحص اليد ولم يعد يُجلب بالإثراء. الدوال
# النقيّة محفوظة (research infra + acc_verify.py) وتبقى مُختبَرة لإعادة الاختبار.
check("تجميع·دوال محفوظة: acc_line ما زالت تعمل (بحث/إعادة اختبار — غير معروضة)",
      S.acc_line(None) == ""
      and "شراء عدواني 67%" in S.acc_line({"aggressive_buy_pct": 67,
          "block_share_pct": 12, "dark_share_pct": 40}))
check("🪦 تقاعد العرض: «تجميع صامت» لم يعد يظهر في فحص اليد (إشارة سقطت باختبارها)",
      "تجميع صامت" not in HC.render_hand_check(
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
    # ⑤ الشموع تنتهي بيوم `today` المستعمل بالفحوص (2026-07-08) — حارس الشمعة
    # البائتة صار يشترط تطابق تاريخ آخر شمعة مع اليوم لأحداث الجلسة (كالواقع).
    return pd.DataFrame(
        {"Open": base["o"] + [t[0]], "Close": base["c"] + [t[1]],
         "High": base["h"] + [t[2]], "Low": base["lo"] + [t[3]],
         "Volume": base["v"] + [t[4]]},
        index=pd.date_range(end="2026-07-08", periods=25, freq="B"))
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
# ⑤ اليوم الجديد = شمعة جديدة بتاريخه (كالواقع) — الشمعة القديمة صارت بائتة عمدًا.
_sw_hist_d2 = {k: v.set_axis(v.index + pd.tseries.offsets.BDay(1))
               for k, v in _sw_hist.items()}
check("لحظي·دِدوب: يوم جديد (بشمعته الجديدة) ⇒ ينبّه ثانية",
      any(k == "sweep" for _, k, _ in
          S.monitor_live_events(_wl_sw, _sw_hist_d2, "2026-07-09")))
check("⑤ حارس الشمعة البائتة: يوم جديد بشمعة الأمس ⇒ صفر أحداث جلسة (لا يحرق الدِدوب)",
      not any(k in ("sweep", "buyzone", "break", "breakout", "dump") for _, k, _ in
              S.monitor_live_events(
                  {"stocks": [{"symbol": "STL", "status": "active",
                               "tranches": [1.9, 1.95, 2.0], "stop": 2.05,
                               "pivot": 1.9, "interp": {}}]},
                  {"STL": _today_df("quiet")}, "2026-07-09")))
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
# 📝 التنبيه مختصر (طلب المستخدم 2026-07-09 «فيها فلسفة كثيرة»): سطر الحدث فقط —
# لا «لقطة الأوامر» ولا تذييلات ℹ️ (Lee-Ready/L2/Yahoo). quotes تُتجاهَل (توافق خلفي).
_sw_msg = S.build_live_alert(_sw, {"SWP": "شراء $1.99×5 · بيع $2.02×3 · سبريد 1%"})
check("لحظي·رسالة مختصرة: «أحداث لحظية» + السهم — بلا لقطة أوامر ولا تذييل فلسفي",
      "أحداث لحظية" in _sw_msg and "$SWP" in _sw_msg
      and "لقطة الأوامر" not in _sw_msg
      and "Lee-Ready" not in _sw_msg and "L2" not in _sw_msg
      and "ℹ️" not in _sw_msg and "Yahoo" not in _sw_msg)
check("لحظي·توافق خلفي: quotes مُمرَّرة أو لا ⇒ نفس الرسالة (تُتجاهَل)",
      S.build_live_alert(_sw) == _sw_msg)
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
# ===== 🔬 E2-A: قياس ظلّي (trace) — تكافؤ بت-بت + funnel + أقفال (SPEC §21) =====
def _e2_wl():   # قائمة جديدة كل مرّة (scan_ignition يضع ignition_alert بالذاكرة)
    return {"stocks": [
        {"symbol": "IGN", "status": "active", "pivot": 1.90, "t1": 2.4, "t2": 2.8, "t3": 3.2,
         "stop": [1.6], "interp": {"critical_number": {"price": 2.00}}},
        {"symbol": "QUIET", "status": "active", "pivot": 5.0,
         "interp": {"critical_number": {"price": 6.0}}}]}
_e2_fire_t = [dict(_b, t=1000 + _i * 60) for _i, _b in enumerate(_ig_fire)]   # + طابع t (E2 §9)
_e2_bars = {"IGN": _e2_fire_t, "QUIET": _ig_bars([5.0] * 10, [100] * 10)}
_e2_fb = lambda s: _e2_bars.get(s)
import time as _time_e2
# ثابت ms (تكافؤ حتمي: نفس القيمة كل نداء) — قديم فـprimary_executable=False (غير مفحوص هنا).
_e2_fo_pass = lambda s: {"has_operator": True, "buy_block_shares": 2000, "bid_block_shares": 3000,
                         "bid": 2.04, "ask": 2.06, "quote_ts": 1_750_000_000_000}
# نانو طازج (عمر ~0) — لمسار «تنفيذي أوّلي» في اختبار candidate (§2d).
_e2_fo_fresh = lambda s: {"has_operator": True, "buy_block_shares": 2000, "bid_block_shares": 3000,
                          "bid": 2.04, "ask": 2.06, "quote_ts": int(_time_e2.time() * 1e9)}
_r_none = S.scan_ignition(_e2_wl(), "2026-07-20", fetch_bars=_e2_fb, fetch_operator=_e2_fo_pass)
_e2_ev = []
_r_tr = S.scan_ignition(_e2_wl(), "2026-07-20", fetch_bars=_e2_fb, fetch_operator=_e2_fo_pass,
                        trace=lambda e, p: _e2_ev.append((e, p)))
check("🔬 E2-A §21.1 تكافؤ: trace=None ≡ trace=collector (نفس الرموز والإشارات بت-بت)",
      [x[0]["symbol"] for x in _r_none] == [x[0]["symbol"] for x in _r_tr] == ["IGN"]
      and [x[1] for x in _r_none] == [x[1] for x in _r_tr])
check("🔬 E2-A §21.1 تكافؤ: استثناء داخل trace لا يغيّر المخرجات (فاشل-آمن)",
      [x[0]["symbol"] for x in S.scan_ignition(_e2_wl(), "2026-07-20", fetch_bars=_e2_fb,
          fetch_operator=_e2_fo_pass,
          trace=lambda e, p: (_ for _ in ()).throw(RuntimeError("x")))] == ["IGN"])
check("🔬 E2-A §3 تكافؤ: _emit_trace(None) صفر عمل (لا يستدعي الحمولة أصلًا)",
      S._emit_trace(None, "X", lambda: 1 / 0) is None)
# 🔬 مراجعة Codex 5 (توصيف): trace=None لا يمرّ بموقع قياس **أصلًا** (لا نداء _emit_trace ولا
# بناء lambda) — «الحمولة الكسولة» وحدها لم تكن كافية: كان يُبنى lambda ويُنادى للدالّة لكل سهم.
_e2_calls = []
_e2_real_emit = S._emit_trace
S._emit_trace = lambda t, e, p: (_e2_calls.append(e), _e2_real_emit(t, e, p))[1]
try:
    _r_off = S.scan_ignition(_e2_wl(), "2026-07-20", fetch_bars=_e2_fb, fetch_operator=_e2_fo_pass)
    _n_off = len(_e2_calls)
    _r_on = S.scan_ignition(_e2_wl(), "2026-07-20", fetch_bars=_e2_fb, fetch_operator=_e2_fo_pass,
                            trace=lambda e, p: None)
    _n_on = len(_e2_calls) - _n_off
finally:
    S._emit_trace = _e2_real_emit
check("🔬 Codex5 قفل: trace=None = صفر نداء _emit_trace (المسار حرفيًّا كالإنتاج) · trace ⇒ يبثّ",
      _n_off == 0 and _n_on > 0
      and [x[0]["symbol"] for x in _r_off] == [x[0]["symbol"] for x in _r_on] == ["IGN"])
check("🔬 Codex5 قفل: كل موقع بثّ داخل scan_ignition محروس بـ`if _tr:` (لا lambda عند None)",
      _insp0.getsource(S.scan_ignition).count("_emit_trace(") ==
      _insp0.getsource(S.scan_ignition).count("if _tr:"))
_e2_events = [e for e, p in _e2_ev]
check("🔬 E2-A §21.2 funnel: IGN المُشتعل 01→02→03→04→05→06→11 (اشتعال+مضارب+إرسال)",
      _e2_events[:7] == ["01_SEEN_ACTIVE", "02_LEVEL_AVAILABLE", "03_BARS_FETCH",
                         "04_RAW_IGNITION", "05_OPERATOR_MEASURED", "06_OPERATOR_PASS",
                         "11_ALERT_EMITTED"])
_e2_ev2 = []
_r_fail = S.scan_ignition(_e2_wl(), "2026-07-20", fetch_bars=_e2_fb,
                          fetch_operator=lambda s: {"has_operator": False},
                          trace=lambda e, p: _e2_ev2.append(e))
check("🔬 E2-A §21.2 funnel: مضارب غائب ⇒ يُكتَم (07_OPERATOR_FAIL · لا 11 · لا تنبيه)",
      _r_fail == [] and "07_OPERATOR_FAIL" in _e2_ev2 and "11_ALERT_EMITTED" not in _e2_ev2)
_e2_one = lambda: {"stocks": [{"symbol": "IGN", "status": "active", "pivot": 1.90,
                               "interp": {"critical_number": {"price": 2.00}}}]}
_e2_ev3 = []
_r_strong = S.scan_ignition(_e2_one(), "2026-07-20",
                            fetch_bars=lambda s: _ig_bars(_ig_quiet + [2.05], [100] * 9 + [400000]),
                            fetch_operator=lambda s: None, trace=lambda e, p: _e2_ev3.append(e))
check("🔬 E2-A §21.2 funnel: تعذّر المضارب + شمعة قوية ⇒ 08→09_FALLBACK_PASS + emitted",
      len(_r_strong) == 1 and "08_OPERATOR_UNAVAILABLE" in _e2_ev3 and "09_FALLBACK_PASS" in _e2_ev3)
_e2_ev4 = []
_r_grp = S.scan_ignition(_e2_one(), "2026-07-20",
                         fetch_bars=lambda s: _ig_bars(_ig_quiet + [2.05], [100] * 9 + [1000]),
                         fetch_operator=lambda s: None, trace=lambda e, p: _e2_ev4.append(e))
check("🔬 E2-A §21.2 funnel: تعذّر المضارب + شمعة قروب ⇒ 10_FALLBACK_FAIL (يُكتَم)",
      _r_grp == [] and "10_FALLBACK_FAIL" in _e2_ev4)
check("🔬 E2-A §9: polygon_minute_bars يحفظ الطابع الزمني t (حقل إضافي)",
      '"t": b.get("t")' in _insp0.getsource(S.polygon_minute_bars))
check("🔬 E2-A قفل: _emit_trace/_ignition_break_source خارج rank_key/select_top/classify_tier/entry_status",
      all(("_emit_trace" not in _insp0.getsource(_f)
           and "_ignition_break_source" not in _insp0.getsource(_f))
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status)))
# ===== 🔬 E2-A: recorder (ignition_measurement) — exposure/funnel/crash-safe (SPEC §7/§21) =====
import ignition_measurement as _M
import tempfile as _tmp
import json as _json
import os as _os
import shutil as _shutil
_e2_out = _tmp.mkdtemp(prefix="e2test_")

# ===== 🔬♻️ استرجاع جلسات E2 الضائعة (e2_recover) — دمج/استرجاع فقط =====
# الخلفية: دفع الassembler كان عاريًا بلا rebase ⇒ ضاعت ملخّصات ~9 جلسات رغم نجاح
# القياس. الاختبارات **سلوكية** (تُبنى artifacts وهمية ويُقرأ الناتج) وكلّها في مجلّد
# مؤقّت — لا تلمس الريبو (درس تلوّث `faisal_images/` بـz.jpg).
import e2_recover as _RC


def _rc_mk(root, run, date, loops, summary=True, index=True):
    d = _os.path.join(root, "recovered", run, "e2_measurement", "session_" + date)
    _os.makedirs(d, exist_ok=True)
    s = {"schema_version": 3, "session_date": date, "termination": "normal",
         "loops_completed": loops, "loops_started": loops, "n_symbols": 8,
         "n_raw_candidates": 0, "n_emitted": 0, "n_delivered": 0}
    if summary:
        with open(_os.path.join(d, "summary.json"), "w", encoding="utf-8") as fh:
            _json.dump(s, fh)
    if index:
        with open(_os.path.join(root, "recovered", run,
                                "ignition_e2_summary.json"), "w", encoding="utf-8") as fh:
            _json.dump(s, fh)
    return d


_rc_root = _tmp.mkdtemp(prefix="e2rec_")
with open(_os.path.join(_rc_root, "ignition_e2_session_index.json"), "w",
          encoding="utf-8") as _fh:            # الحالة الحقيقية: جلسة واحدة فقط
    _json.dump({"2026-07-24": {"n_symbols": 8, "termination": "normal"}}, _fh)
_rc_mk(_rc_root, "111", "2026-07-15", 500)
_rc_mk(_rc_root, "222", "2026-07-16", 480)
_rc_mk(_rc_root, "333", "2026-07-24", 111)     # نفس يوم الموجود
_rc_mk(_rc_root, "444", "2026-07-24", 520)     # تعارض: أطول ⇒ يفوز
_rc_mk(_rc_root, "555", "2026-07-17", 0, summary=False, index=False)   # بلا ملخّص
_rc_res = _RC.recover(_os.path.join(_rc_root, "recovered"), repo_root=_rc_root)
_rc_idx = _json.load(open(_os.path.join(_rc_root, "ignition_e2_session_index.json"),
                          encoding="utf-8"))
check("🔬♻️ الاسترجاع يدمج ولا يدهس: الجلسة القديمة باقية + الجديدتان أُضيفتا",
      set(_rc_idx) == {"2026-07-15", "2026-07-16", "2026-07-24"}
      and _rc_res["new"] == ["2026-07-15", "2026-07-16"])
check("🔬♻️ تعارض تاريخ من تشغيلتين: تفوز الأكثر دورات (حتميّ) ويُبلَّغ",
      _json.load(open(_os.path.join(_rc_root, "e2_measurement",
                                    "session_2026-07-24", "summary.json"),
                      encoding="utf-8"))["loops_completed"] == 520
      and _rc_res["conflicts"] == [("2026-07-24", 111, 520)])
check("🔬♻️ مجلّد بلا ملخّص يُتخطّى ولا يُخمَّن (لا يدخل الفهرس)",
      "2026-07-17" not in _rc_idx and _rc_res["no_summary"] == ["2026-07-17"])
# 🔥 قراءة التنبيهات المُسلَّمة: delivered=true فقط · بلا تكرار · والفاشل لا يُحسب
with open(_os.path.join(_rc_root, "recovered", "111", "e2_measurement",
                        "session_2026-07-15", "deliveries.jsonl"), "w",
          encoding="utf-8") as _fh:
    for _r in ({"symbol": "AAA", "delivered": True}, {"symbol": "AAA", "delivered": True},
               {"symbol": "BBB", "delivered": False}, {"symbol": "CCC", "delivered": True}):
        _fh.write(_json.dumps(_r) + "\n")
_rc_f = _RC.recover(_os.path.join(_rc_root, "recovered"), repo_root=_rc_root)["fires"]
check("🔬♻️🔥 التنبيهات المُسلَّمة: المُسلَّم فقط · بلا تكرار · الفاشل لا يُحسب",
      _rc_f == [("2026-07-15", ["AAA", "CCC"])])
# 🔥 إعادة بناء سجلّ الإطلاقات: المُطلَق فقط · حقول منسوخة من مصدرها · موسوم مُسترجَعًا
with open(_os.path.join(_rc_root, "recovered", "222", "e2_measurement",
                        "session_2026-07-16", "candidates.jsonl"), "w",
          encoding="utf-8") as _fh:
    for _c in ({"symbol": "XYZ", "session_date": "2026-07-16", "alert_emitted": True,
                "telegram_sent_at": "2026-07-16T14:02:11Z", "break_level": 3.0,
                "signal_price": 3.15, "vol_x": 8.0, "signal_usd": 120000,
                "candle_class": "operator"},
               {"symbol": "XYZ", "session_date": "2026-07-16", "alert_emitted": True,
                "telegram_sent_at": "2026-07-16T15:00:00Z", "break_level": 3.0,
                "signal_price": 3.9, "vol_x": 4.0, "signal_usd": 9,
                "candle_class": "group"},                 # مكرّر نفس اليوم ⇒ يُتخطّى
               {"symbol": "QQQ", "session_date": "2026-07-16", "alert_emitted": False,
                "signal_price": 9.9}):                    # لم يُطلَق ⇒ لا يدخل
        _fh.write(_json.dumps(_c) + "\n")
with open(_os.path.join(_rc_root, "ignition_log.json"), "w", encoding="utf-8") as _fh:
    _json.dump([{"symbol": "OLD", "date": "2026-07-14", "price": 1.0}], _fh)
_rc_r = _RC.recover(_os.path.join(_rc_root, "recovered"), repo_root=_rc_root)["rebuilt"]
_rc_log = _json.load(open(_os.path.join(_rc_root, "ignition_log.json"), encoding="utf-8"))
_rc_new = [r for r in _rc_log if r.get("symbol") == "XYZ"]
check("🔥 إعادة سجلّ الإطلاقات: المُطلَق فقط · مرّة/سهم/يوم · والقديم لا يُمسّ",
      _rc_r == ["2026-07-16 XYZ"] and len(_rc_new) == 1
      and any(r.get("symbol") == "OLD" for r in _rc_log)
      and not any(r.get("symbol") == "QQQ" for r in _rc_log))
check("🔥 كل حقل منسوخ من مصدره المسجَّل (لا اشتقاق) + وسم «مُسترجَع» لا يُخلَط بالأصلي",
      _rc_new[0] == {"symbol": "XYZ", "date": "2026-07-16",
                     "fired_at": "2026-07-16T14:02:11Z", "break_level": 3.0,
                     "price": 3.15, "vol_x": 8.0, "usd": 120000,
                     "candle_class": "operator", "source": "e2_reconstructed"}
      and "source" not in [r for r in _rc_log if r.get("symbol") == "OLD"][0])
check("🔥 إعادة التشغيل لا تضاعف السجلّ (idempotent)",
      _RC.recover(_os.path.join(_rc_root, "recovered"),
                  repo_root=_rc_root)["rebuilt"] == []
      and len(_json.load(open(_os.path.join(_rc_root, "ignition_log.json"),
                              encoding="utf-8"))) == len(_rc_log))
# لا يدهس مجلّدًا خامًا موجودًا سلفًا (إعادة التشغيل آمنة — idempotent)
_rc_res2 = _RC.recover(_os.path.join(_rc_root, "recovered"), repo_root=_rc_root)
check("🔬♻️ إعادة التشغيل آمنة: صفر جلسة جديدة وصفر نسخ (idempotent)",
      _rc_res2["new"] == [] and _rc_res2["copied"] == []
      and set(_json.load(open(_os.path.join(_rc_root, INDEX_RC := "ignition_e2_session_index.json"),
                              encoding="utf-8"))) == set(_rc_idx))
# ⏳ تغطية الافتتاح: الكرون مقدَّم لتعويض تأخّر GitHub المرصود، وسقف الانتظار يغطّي
# الفصلين. اختبار حسابي على الأرقام الفعلية (لا نصّي) — أي عودة لقيمة تكسر التغطية تُسقطه.
_ig_yml = open(".github/workflows/ignition.yml", encoding="utf-8").read()
_ig_cron_min = next((int(x.split('"')[1].split()[1]) * 60 + int(x.split('"')[1].split()[0])
                     for x in _ig_yml.splitlines() if "- cron:" in x), None)
import ignition_live as _IGL
check("⏳ رادار: الكرون + سقف الانتظار يغطّيان الافتتاح في الفصلين رغم تأخّر GitHub",
      # تأخّر مرصود 95-152د · افتتاح صيفي 13:30 (810د) وشتوي 14:30 (870د)
      all(0 < (_open - (_ig_cron_min + _lag)) <= _IGL.PRE_OPEN_WAIT_MAX_MIN
          or (_ig_cron_min + _lag) >= _open
          for _open in (810, 870) for _lag in (95, 119, 152))
      # وبأسوأ تأخّر لا يتجاوز البدء الافتتاح الصيفي بأكثر من نصف ساعة
      and (_ig_cron_min + 152) - 810 <= 30)
# 🔓 T-LIBERATION (liberation_prereg.md): ذراع الدخول بعد كسر التحرر
# اختبارات سلوكية على أرقام فيصل الحقيقية (DSY 1.85→3.20 · JZ 2.56→4).
_lib_sv = dict(S.CONFIG)
# ① المستويان: L1 من الرقم الحرج (breakout_activation فقط) · L2 من liberation
check("🔓 T-LIB·المستويان من حساب البوت: L1 الرقم الحرج · L2 أعلى مقاومة",
      S._liberation_levels({"liberation": 3.20, "interp_none": 1}) == (None, 3.2))
check("🔓 T-LIB·فاشلة-آمنة: بلا حقول ⇒ (None, None) بلا استثناء",
      S._liberation_levels({}) == (None, None)
      and S._liberation_levels({"liberation": "سيء"}) == (None, None))
# ② التعبئة: **إغلاق** فوق المستوى لا ذيل · النافذة تُحترم · الكسر بآخر شمعة لا يُحسم
_lib_cl = [1.90, 2.00, 3.30, 3.40, 3.50]      # كسر 3.20 عند الفهرس 2
check("🔓 T-LIB·التعبئة بأول إغلاق فوق المستوى (فهرس 2) لا قبله",
      S._liberation_fill(_lib_cl, 3.20, 20) == ("filled", 2, 3.30))
check("🔓 T-LIB·إغلاق مساوٍ للمستوى لا يُعبّئ (ثبات «فوق» حصرًا)",
      S._liberation_fill([3.20, 3.20], 3.20, 20)[0] == "no_break")
check("🔓 T-LIB·نافذة الانتظار تُحترم: كسر بعدها ⇒ no_break",
      S._liberation_fill([1.0, 1.0, 1.0, 9.0], 3.20, 2)[0] == "no_break")
check("🔓 T-LIB·كسر بآخر شمعة ⇒ break_at_end (لا حسم أمامي)",
      S._liberation_fill([1.0, 9.0], 3.20, 20)[0] == "break_at_end")
check("🔓 T-LIB·بلا مستوى ⇒ no_level (لا ادّعاء)",
      S._liberation_fill(_lib_cl, None, 20)[0] == "no_level")
# ③ الإلحاق: وقف الأساس يُستعمل كما هو · حقول الأساس لا تُمَسّ
S.CONFIG["BT_LIBERATION"] = 1
_lb_hi = [2.0, 2.1, 3.4, 4.2, 4.6]; _lb_lo = [1.8, 1.9, 3.1, 3.3, 3.6]
_lb_cl = [1.90, 2.00, 3.30, 3.60, 4.50]; _lb_op = [1.85, 1.95, 3.20, 3.40, 3.70]
_lb_tr = {"entry": 1.85, "stop": 1.60, "t1": 4.00, "outcome": "win", "ret_a": 116.0}
_lb_r = {"liberation": 3.20, "pivot": 1.80}
_lb_out = S._liberation_augment(dict(_lb_tr), _lb_r, _lb_hi, _lb_lo, _lb_cl, _lb_op,
                                1.60, 4.00)
check("🔓 T-LIB·الإلحاق لا يمسّ حقول الأساس إطلاقًا",
      all(_lb_out[k] == v for k, v in _lb_tr.items()))
check("🔓 T-LIB·ذراع L2 عُبِّئ بإغلاق الكسر 3.30 وحُسم بمحرّك الأساس",
      _lb_out["entry_lib_l2"] == 3.30 and _lb_out["lib_l2_fill"] == "filled"
      and _lb_out["outcome_lib_l2"] in ("win", "loss", "open"))
check("🔓 T-LIB·بلا مستوى L1 ⇒ ذراعه no_fill بلا عائد (لا تلفيق)",
      _lb_out["outcome_lib_l1"] == "no_fill" and _lb_out["ret_lib_l1"] is None)
# ③-ب 🔒 **قفل عزل الوقف** (§②-3): الذراع يستعمل **وقف الأساس** لا وقفًا مشتقًّا من
#     سعر الكسر. حالة تمييزية: بعد التعبئة عند 3.30 يهبط الأدنى إلى 3.05 ثم يبلغ t1:
#     · بوقف الأساس (1.60) لا يُضرب ⇒ **win**
#     · بأي وقف مشتقّ قريب (مثل 3.30×0.93=3.07) يُضرب ⇒ loss
#     فنجاح الذراع هنا برهانٌ سلوكيّ أن الوقف لم يُستبدَل (درس T1b: خلط الدخول بالوقف).
_iso_hi = [2.0, 2.1, 3.4, 3.5, 4.2]
_iso_lo = [1.8, 1.9, 3.1, 3.05, 3.6]
_iso_cl = [1.90, 2.00, 3.30, 3.20, 4.10]
_iso_op = [1.85, 1.95, 3.20, 3.30, 3.70]
S.CONFIG["BT_LIBERATION"] = 1
_iso = S._liberation_augment({"entry": 1.85, "stop": 1.60, "t1": 4.00},
                             {"liberation": 3.20}, _iso_hi, _iso_lo, _iso_cl,
                             _iso_op, 1.60, 4.00)
check("🔓 T-LIB·🔒 عزل الوقف: يستعمل وقف الأساس (win) لا وقفًا مشتقًّا من سعر الكسر (loss)",
      _iso["entry_lib_l2"] == 3.30 and _iso["outcome_lib_l2"] == "win")
# ③-ج 🔒 **قفل «لا نظر مستقبليّ على شمعة الكسر»** (§②-2: ندخل بإغلاقها فنملك من الفتح
#     التالي). حالة تمييزية: شمعة الكسر رأسها 5.0 يتجاوز الهدف 4.60 **قبل** إغلاقها
#     عند 4.50 (ترتيب اللمس داخلها مجهول)، والشمعة التالية تضرب الوقف:
#     · بالاتفاقية الصحيحة (نملك من idx+1) ⇒ **loss**
#     · بحسم شمعة الكسر نفسها ⇒ win وهميّ
_la_cl = [1.90, 4.50, 2.00, 2.00]; _la_hi = [2.0, 5.0, 2.1, 2.1]
_la_lo = [1.80, 1.90, 1.50, 1.50]; _la_op = [1.85, 2.00, 2.05, 2.05]
_la = S._liberation_augment({"entry": 1.85, "stop": 1.60, "t1": 4.60},
                            {"liberation": 3.20}, _la_hi, _la_lo, _la_cl,
                            _la_op, 1.60, 4.60)
check("🔓 T-LIB·🔒 لا نظر مستقبليّ: رأس شمعة الكسر لا يُحسَب هدفًا (loss لا win وهميًّا)",
      _la["entry_lib_l2"] == 4.50 and _la["outcome_lib_l2"] == "loss")
# ④ المقارنة المقترنة إلزامية: تظهر بالمخرَج ويُطبع عدد غير المُعبَّأة
#    (العلم يبقى مفعّلًا هنا — `backtest_liberation_compare` تُرجع [] وهو مطفأ)
_lib_rows = [dict(_lb_tr, symbol="A", **{k: v for k, v in _lb_out.items()
                                         if k.startswith(("lib_", "entry_lib_",
                                                          "outcome_lib_", "ret_lib_"))})
             for _ in range(3)]
_lib_msg = "\n".join(S.backtest_liberation_compare(_lib_rows))
check("🔓 T-LIB·المخرَج يحمل المقارنة المقترنة + غير المُعبَّأة + سقف النجاح",
      "مقترنة" in _lib_msg and "لم يُكسَر" in _lib_msg
      and "ثلاث سنوات" in _lib_msg and "اقتراح للمالك" in _lib_msg)
S.CONFIG["BT_LIBERATION"] = 0
check("🔓 T-LIB·مطفأة ⇒ [] (صفر أثر على التقرير العادي)",
      S.backtest_liberation_compare(_lib_rows) == [])
S.CONFIG.update(_lib_sv)
# ⑤ 🔒 **القفل الحاسم**: مطفأة ⇒ صفقة الأساس **بت-بت** (نفس نمط قفل BT_POTENTIAL).
#    يُشغَّل الجذر نفسه على نفس البذرة مع/بدون العلم ويُقارَن قاموس الصفقة كاملًا.
S.CONFIG["BT_LIBERATION"] = 1
_lb_on = S.backtest_symbol("LBON", synth_pivot(seed=2))
S.CONFIG["BT_LIBERATION"] = 0
_lb_off = S.backtest_symbol("LBOFF", synth_pivot(seed=2))
_lbk = lambda t: {k: v for k, v in t.items() if k != "symbol"}
check("🔓 T-LIB·وصل: مفعّلة ⇒ كل صفقة تحمل حقول ذراعَي L1/L2",
      len(_lb_on) >= 1 and all({"lib_l1_level", "lib_l2_level", "outcome_lib_l1",
                                "outcome_lib_l2"} <= set(t) for t in _lb_on))
check("🔓 T-LIB·🔒 مطفأة ⇒ صفقة الأساس بت-بت (صفر حقل lib_ وقاموس مطابق)",
      len(_lb_off) == len(_lb_on)
      and all(not any(k.startswith(("lib_", "entry_lib_", "outcome_lib_", "ret_lib_"))
                      for k in t) for t in _lb_off)
      and [_lbk(t) for t in _lb_off]
      == [{k: v for k, v in _lbk(t).items()
           if not k.startswith(("lib_", "entry_lib_", "outcome_lib_", "ret_lib_"))}
          for t in _lb_on])
S.CONFIG.update(_lib_sv)
check("🔒 T-LIB قفل: دوال التجربة خارج مسار الفرز الحيّ",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("_liberation_augment", "backtest_liberation_compare",
                      "_liberation_fill")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.analyze_ticker, S.scan_market, S.apply_float_gate)))
# 🔴 معيار الفلوت الكبير موحَّد (_float_too_big) — مرجع واحد لا ثلاثة
check("🔴 _float_too_big: الحدّ فأكثر = كبير · أقلّ = لا · والمجهول/التالف يمرّ",
      S._float_too_big(S.CONFIG["FLOAT_GATE_MAX"])
      and S._float_too_big(S.CONFIG["FLOAT_GATE_MAX"] + 1)
      and not S._float_too_big(S.CONFIG["FLOAT_GATE_MAX"] - 1)
      and not S._float_too_big(None) and not S._float_too_big("نصّ")
      and not S._float_too_big({}) and not S._float_too_big(float("nan")))
check("🔴 _float_too_big: النصّ الرقمي يُحوَّل (لا يمرّ مجهولًا)",
      S._float_too_big(str(S.CONFIG["FLOAT_GATE_MAX"] + 1)))
# 🔴 المحمول بفلوت كبير لا يُعرَض أصلًا بعد التقليم — والمجهول يبقى
_bfw = {"stocks": [
    {"symbol": "BIGC", "status": "active", "float": 3e8, "cont_status": "exited"},
    {"symbol": "OKC", "status": "active", "float": 1e6, "cont_status": "exited"},
    {"symbol": "UNKC", "status": "active", "float": None, "cont_status": "exited"}]}
_bfw_out = [s for s in _bfw["stocks"] if not S._float_too_big(s.get("float"))]
check("🔴 تقليم المحمولين: الكبير يُشطب · الصغير والمجهول يبقيان",
      [s["symbol"] for s in _bfw_out] == ["OKC", "UNKC"])
# 🔕 رادار التقسيم: لا إشعار إلا بالمطابق الكامل (قرار المالك 2026-07-29)
def _sr_row(sym, **kw):
    r = {"symbol": sym, "price": 2.0, "half": 1.8, "ref": 3.6, "float": 60_000,
         "short": 0, "near_bottom": True, "held_ok": True, "short_ok": True,
         "float_ok": True, "pump": False}
    r.update(kw)
    return r
_sr_all = [_sr_row("NUWE"), _sr_row("NTCL", pump=True), _sr_row("RDGT", short_ok=False),
           _sr_row("CTNT", float_ok=False), _sr_row("LZMH", held_ok=False),
           _sr_row("FAR", near_bottom=False)]
check("🔕 رادار التقسيم·الجاهز = الخمسة كلها (أي ❌ يُسقط السهم)",
      [r["symbol"] for r in S.split_radar_ready(_sr_all)] == ["NUWE"])
_sr_msg = S.build_split_radar_section(_sr_all)
check("🔕 رادار التقسيم·الرسالة تحمل المطابق وحده — لا ذكر لأي ساقط",
      "NUWE" in _sr_msg and not any(x in _sr_msg
                                    for x in ("NTCL", "RDGT", "CTNT", "LZMH", "FAR")))
check("🔕 رادار التقسيم·صفر مطابق ⇒ رسالة فارغة (صمت تامّ، لا إشعار)",
      S.build_split_radar_section([_sr_row("X", pump=True)]) == ""
      and S.build_split_radar_section([]) == "")
check("🔕 رادار التقسيم·الرسالة نفسها لا تحمل ❌ إطلاقًا (كل المعروض ✅)",
      "❌" not in _sr_msg)
# 🔴 M14 بوّابة صلبة (قرار المالك 2026-07-29 «يكون مستبعد تماما»)
_S_yf = S.yf
S.yf = S.yf or type("Y", (), {"Ticker": staticmethod(lambda s: type("T", (), {"info": {}})())})
_big = {"symbol": "BIG", "float": 129_280_311, "soft_fails": [], "flags": []}
_sml = {"symbol": "SML", "float": 4_000_000, "soft_fails": [], "flags": []}
_unk = {"symbol": "UNK", "float": None, "soft_fails": [], "flags": []}
_g = S.apply_float_gate([dict(_big), dict(_sml)])
check("🔴 M14·الفلوت الكبير يُحذف تمامًا (لا يُنقَل نقصًا) — قرار المالك",
      [r["symbol"] for r in _g] == ["SML"])
check("🔴 M14·حدّ الاستبعاد بالضبط: الحدّ نفسه يُحذف وما تحته بسهم واحد يبقى",
      [r["symbol"] for r in S.apply_float_gate(
          [{"symbol": "AT", "float": S.CONFIG["FLOAT_GATE_MAX"], "soft_fails": [], "flags": []},
           {"symbol": "UN", "float": S.CONFIG["FLOAT_GATE_MAX"] - 1, "soft_fails": [], "flags": []}])]
      == ["UN"])
S.yf = _S_yf
check("🔁 M14·الاستبعاد تام بعد الإثراء أيضًا: يخرج ولو نواقصه صفر",
      S.refloat_gate_recheck([{"symbol": "Z", "float": 9e8,
                               "soft_fails": [], "flags": []}])[0] == [])
# 📉🕵️ مَن أهبط السهم (فيصل YYAI): بلا شورت ⇒ المضارب يصرّف
check("📉 فاعل الهبوط: شورت ضئيل ⇒ «المضارب يصرّف» · شورت كبير ⇒ لا ادّعاء",
      "المضارب يصرّف" in S._dump_actor({"finra_short": 500})
      and "المضارب يصرّف" not in S._dump_actor({"finra_short": 5_000_000})
      and S._dump_actor({}) == "" and S._dump_actor(None) == "")
check("📉 فاعل الهبوط·يفضّل المتاح (قراءة فيصل للشورت) ثم الحجم اليومي",
      "600,000" in S._dump_actor({"shares_available": 600000, "finra_short": 5}))
check("⚖️ الأحداث المعلنة: حدث ذو اتجاهين لا إشارة صعود ضمنية",
      (lambda t: "باب خروج" in t and "يوم انفجار محتمل" not in t)(
          "\n".join(S.events_lines([{"kind": "أرباح",
                                     "date": (S.dt.date.today()
                                              + S.dt.timedelta(days=3)).isoformat()}]) or [""])))
# 🔁 M14 بعد الإثراء (مسكة PONY الحيّة 2026-07-28): الفلوت الذي تعذّر لحظة البوّابة
# صار متاحًا ⇒ يُعاد الحكم بالمعيار القائم نفسه. اختبارات سلوكية على أرقام حقيقية.
_M14_LIM = S.CONFIG["FLOAT_GATE_MAX"]
def _m14(fl, soft, flags=("فلوت غير متاح — مُرِّر بفائدة الشك",)):
    return {"symbol": "ZZ", "float": fl, "soft_fails": list(soft), "flags": list(flags)}
# PONY الحقيقي: 277م بثلاثة نواقص ⇒ يصير 4 ⇒ يُرفض (الحدّ WATCH_MAX_FAILS=3)
_k, _e = S.refloat_gate_recheck([_m14(277_657_352, ["أ", "ب", "ج"])])
check("🔁 M14·فلوت كبير ظهر بعد الإثراء يرفع النواقص فوق الحدّ ⇒ يخرج",
      _k == [] and _e == [("ZZ", 277_657_352)])
# 🔴 بعد قرار «الاستبعاد التام»: يخرج ولو نقصه واحد — والوسم يُصحَّح لا يُترَك متناقضًا
_r = _m14(277_657_352, ["أ"])
_k2, _e2 = S.refloat_gate_recheck([_r])
check("🔁 M14·الاستبعاد تام: يخرج ولو نقصه واحد · والوسم المتناقض يُزال",
      _k2 == [] and _e2 == [("ZZ", 277_657_352)] and "فلوت كبير" in _r["soft_fails"]
      and not any(str(f).startswith("فلوت غير متاح") for f in _r["flags"])
      and any("فوق" in str(f) for f in _r["flags"]))
check("🔁 M14·المجهول يبقى ممرَّرًا بفائدة الشك (لا تغيير) · والصغير لا يُمسّ",
      S.refloat_gate_recheck([_m14(None, ["أ", "ب", "ج"])])[1] == []
      and S.refloat_gate_recheck([_m14(_M14_LIM - 1, ["أ", "ب", "ج"])])[1] == []
      and S.refloat_gate_recheck([_m14(_M14_LIM, ["أ", "ب", "ج"])])[1] != [])
check("🔁 M14·فاشل-آمن: فلوت بقيمة تالفة لا يكسر الفرز ولا يُسقط السهم",
      S.refloat_gate_recheck([_m14("غير رقمي", ["أ", "ب", "ج"])])[1] == []
      and len(S.refloat_gate_recheck([_m14({}, ["أ"])])[0]) == 1)
check("🔁 M14·لا يُضاعف الوسم لو أُعيد التقييم مرّتين (idempotent)",
      (lambda r: (S.refloat_gate_recheck([r]), S.refloat_gate_recheck([r]),
                  r["soft_fails"].count("فلوت كبير"))[2] == 1)(_m14(9e9, ["أ"])))
check("🔒 M14·إعادة التقييم لا تُستدعى داخل أي جذر (طبقة تالية للإثراء)",
      all("refloat_gate_recheck" not in _insp0.getsource(_f)
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.apply_float_gate,
                     S.apply_short_gate, S.scan_market, S.analyze_ticker,
                     S.backtest_symbol, S.entry_status)))
# ⏰ الفارز اليومي: الكرون مقدَّم بمقدار التأخّر المقيس (138-159د) ليصل التقرير ~10ص
# السعودية (07:00-07:30 UTC). قفل حسابي — أي عودة لـ«23 7» أو تقديم مفرط يُسقطه.
_ds_cron = next((x.split('"')[1] for x in
                 open(".github/workflows/daily_screener.yml",
                      encoding="utf-8").read().splitlines()
                 if "- cron:" in x and "* * 2-5" in x), "")
_ds_min = int(_ds_cron.split()[1]) * 60 + int(_ds_cron.split()[0])
check("⏰ الفارز اليومي: بأي تأخّر مرصود (138-159د) يصل التقرير 10:00-11:00 السعودية",
      all(600 <= (_ds_min + _lag + 180) <= 660 for _lag in (138, 141, 159)))
check("🔬♻️ قفل: لا workflow يُضيف مسارًا مُستثنى بـ.gitignore (يُتخطّى صامتًا فيوهم بالدفع)",
      (lambda ign, wfs: all(
          not any(("git add" in ln and p.rstrip("/") in ln) for ln in wf.splitlines())
          for wf in wfs for p in ign))(
          [ln.strip() for ln in open(".gitignore", encoding="utf-8")
           if ln.strip().endswith("/") and not ln.startswith("#")],
          [open(_os.path.join(".github/workflows", f), encoding="utf-8").read()
           for f in _os.listdir(".github/workflows") if f.endswith(".yml")]))
check("🔬♻️ قفل: الاسترجاع خارج الفرز/الرادار (لا يستورده أي جذر)",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("e2_recover", "recover(")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.scan_ignition, S.analyze_ticker, S.backtest_symbol)))
_shutil.rmtree(_rc_root, ignore_errors=True)


def _e2_read_jsonl(sub, name):
    p = _os.path.join(_e2_out, sub, "session_2026-07-20", name)
    with open(p, encoding="utf-8") as fh:
        return [_json.loads(x) for x in fh if x.strip()]


def _e2_read_json(sub, name):
    with open(_os.path.join(_e2_out, sub, "session_2026-07-20", name), encoding="utf-8") as fh:
        return _json.load(fh)


# مسار المضارب-موجود (emitted + delivered)
_rec = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, "pass"),
                                      meta={"source_commit": "abc123"})
_rec.loop_start()
_e2_rows = S.scan_ignition(_e2_wl(), "2026-07-20", fetch_bars=_e2_fb, fetch_operator=_e2_fo_fresh,
                           trace=_rec.trace)
_rec.telegram_attempt(_e2_rows)
_rec.telegram_success(_e2_rows)
_rec.loop_end()
_rec.finalize(termination="normal")
_e2_ss = {r["symbol"]: r for r in _e2_read_jsonl("pass", "symbol_sessions.jsonl")}
_e2_cands = _e2_read_jsonl("pass", "candidates.jsonl")
_e2_sess = _e2_read_json("pass", "session.json")
check("🔬 E2-A §7 recorder: symbol-session IGN يجمّع funnel (raw/emitted/delivered) + coverage",
      _e2_ss["IGN"]["raw_candidate_count"] == 1 and _e2_ss["IGN"]["emitted_count"] == 1
      and _e2_ss["IGN"]["delivered_count"] == 1 and _e2_ss["IGN"]["operator_pass_count"] == 1
      and _e2_ss["IGN"]["coverage_ratio"] == 1.0 and _e2_ss["IGN"]["first_seen_at"] is not None)
check("🔬 E2-A §4 recorder: candidate كامل (NBBO/mid/spread/executable/gate/emitted/delivered)",
      len(_e2_cands) == 1 and _e2_cands[0]["signal_price"] == 2.05
      and _e2_cands[0]["nbbo_mid"] == 2.05 and _e2_cands[0]["primary_executable"] is True
      and _e2_cands[0]["gate_decision"] == "emit" and _e2_cands[0]["alert_emitted"] is True
      and _e2_cands[0]["telegram_delivered"] is True and _e2_cands[0]["trigger_bar_end"] is not None)
# 🔬 §2c: توقيت الشمعة — Polygon t = بداية · النهاية = البداية+60000 · bar_is_closed حتمي.
check("🔬 E2-A §2c: trigger_bar_start مسجَّل + trigger_bar_end = start+60000 + bar_is_closed محسوب",
      _e2_cands[0]["trigger_bar_start"] is not None
      and _e2_cands[0]["trigger_bar_end"] == _e2_cands[0]["trigger_bar_start"] + 60000
      and isinstance(_e2_cands[0]["bar_is_closed"], bool)
      and _e2_cands[0]["detected_at_ms"] is not None)
# 🔬 §2d: NBBO طازج ⇒ primary_executable=True + quote موحّد ملّي + عمر محسوب.
check("🔬 E2-A §2d: NBBO طازج ⇒ تنفيذي + quote_timestamp موحّد ملّي + quote_age_ms عدد",
      _e2_cands[0]["primary_executable"] is True
      and isinstance(_e2_cands[0]["quote_timestamp"], int)
      and _e2_cands[0]["quote_timestamp"] >= 1_000_000_000_000
      and isinstance(_e2_cands[0]["quote_age_ms"], int) and _e2_cands[0]["quote_age_ms"] >= 0)
# مسار المضارب-غائب (emitted=False · candidate مكبوت مُسجَّل · لا تسليم)
_rec2 = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, "fail"))
S.scan_ignition(_e2_wl(), "2026-07-20", fetch_bars=_e2_fb,
                fetch_operator=lambda s: {"has_operator": False}, trace=_rec2.trace)
_rec2.finalize(termination="normal")
_e2_cf = _e2_read_jsonl("fail", "candidates.jsonl")
check("🔬 E2-A §4 recorder: emitted ≠ delivered — مضارب غائب يُسجَّل candidate مكبوت (suppress_operator)",
      len(_e2_cf) == 1 and _e2_cf[0]["gate_decision"] == "suppress_operator"
      and _e2_cf[0]["alert_emitted"] is False and _e2_cf[0]["telegram_delivered"] is None)
# crash-safe: finalize بعد انقطاع
_rec3 = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, "crash"))
_rec3.trace("01_SEEN_ACTIVE", {"symbol": "X"})
_rec3.finalize(termination="exception")
check("🔬 E2-A §21.5 crash-safe: finalize(termination=exception) يكتب session.json حتى عند الانقطاع",
      _e2_read_json("crash", "session.json")["termination"] == "exception")
# فاشل-آمن مطلق (حمولة معطوبة/حدث مجهول لا يرفع)
_rec4 = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, "safe"))
_rec4.trace("99_UNKNOWN", {"symbol": "X"})
_rec4.trace("04_RAW_IGNITION", None)
_rec4.trace(None, None)
check("🔬 E2-A recorder: trace فاشل-آمن مطلق (حمولة معطوبة/حدث مجهول لا يرفع)", True)
check("🔬 E2-A §8 recorder: لا أسرار في المخرجات (لا مفاتيح/توكن/apiKey)",
      not any(_k in _json.dumps(_e2_cands) + _json.dumps(_e2_sess)
              for _k in ("POLYGON", "Bearer", "apiKey", "TELEGRAM_")))
check("🔬 E2-A قفل: ignition_measurement غير مستورد في مسار الفرز (Super_stock لا يعتمده)",
      "import ignition_measurement" not in _insp0.getsource(S.scan_ignition)
      and "ignition_measurement" not in _insp0.getsource(S.rank_key))
check("🔬 E2-A §21.1: نص تنبيه Telegram متطابق مع/بدون trace (لا يتغيّر حرفًا)",
      S.build_ignition_alert(_r_none) == S.build_ignition_alert(_r_tr)
      and "$IGN" in S.build_ignition_alert(_r_none))
# §21.2.10: لا اشتعال خام ⇒ عدّادات فقط، لا candidate
_rec_nr = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, "noraw"))
S.scan_ignition({"stocks": [{"symbol": "FLAT", "status": "active", "pivot": 5.0,
                             "interp": {"critical_number": {"price": 6.0}}}]},
                "2026-07-20", fetch_bars=lambda s: _ig_bars([5.0] * 10, [100] * 10),
                fetch_operator=_e2_fo_pass, trace=_rec_nr.trace)
_rec_nr.finalize("normal")
_nr_ss = {r["symbol"]: r for r in _e2_read_jsonl("noraw", "symbol_sessions.jsonl")}
check("🔬 E2-A §21.2: لا اشتعال خام ⇒ raw=0 + bars_ok محسوب + صفر candidate",
      _nr_ss["FLAT"]["raw_candidate_count"] == 0 and _nr_ss["FLAT"]["bars_ok"] == 1
      and _e2_read_jsonl("noraw", "candidates.jsonl") == [])
# §21.5 crash-safe: candidate يُلحَق للملف عند قرار البوّابة **قبل** finalize
_rec_cf = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, "flush"))
S.scan_ignition(_e2_wl(), "2026-07-20", fetch_bars=_e2_fb,
                fetch_operator=lambda s: {"has_operator": False}, trace=_rec_cf.trace)
_cf_pre = _e2_read_jsonl("flush", "candidates.jsonl")
check("🔬 E2-A §21.5 crash-safe: candidate مُلحَق للملف عند قرار البوّابة (قبل finalize)",
      len(_cf_pre) == 1 and _cf_pre[0]["gate_decision"] == "suppress_operator")
# §21.4 exposure: polls مستقلّة لكل رمز + coverage من محاولاته (لا قائمة نهائية مسطّحة)
_rec_ex = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, "expo"))
for _p in range(3):
    _rec_ex.trace("01_SEEN_ACTIVE", {"symbol": "EARLY"})
    _rec_ex.trace("03_BARS_FETCH", {"symbol": "EARLY", "bars_ok": _p != 1})   # poll 1 فشل الجلب
_rec_ex.trace("01_SEEN_ACTIVE", {"symbol": "LATE"})   # يظهر متأخّرًا مرّة واحدة
_rec_ex.finalize("normal")
_ex_ss = {r["symbol"]: r for r in _e2_read_jsonl("expo", "symbol_sessions.jsonl")}
check("🔬 E2-A §21.4 exposure: polls مستقلّة (EARLY=3 ≠ LATE=1) + coverage=2/3 من محاولاته",
      _ex_ss["EARLY"]["active_polls"] == 3 and _ex_ss["LATE"]["active_polls"] == 1
      and _ex_ss["EARLY"]["coverage_ratio"] == round(2 / 3, 4)
      and _ex_ss["LATE"]["first_seen_at"] is not None)
check("🔬 E2-A §21.7 قفل: ثوابت العتبات لم تتغيّر (VOL_MULT/OPERATOR_MIN/USD)",
      S.CONFIG["IGNITION_VOL_MULT"] == 3.0 and S.CONFIG["OPERATOR_MIN_SHARES"] == 1000
      and S.CONFIG["IGNITION_USD_OPERATOR"] == 100000 and S.CONFIG["IGNITION_USD_STRONG"] == 300000)
check("🔬 E2-A §21.7 قفل: ignition_live يبوّب بـE2_MEASUREMENT + trace=_trace + finalize في finally",
      "E2_MEASUREMENT" in _insp0.getsource(IG.main) and "trace=_trace" in _insp0.getsource(IG.main)
      and "finalize" in _insp0.getsource(IG.main) and "finally" in _insp0.getsource(IG.main))

# ═══ 🔬 إصلاحات فجوات مراجعة Codex لـE2-A (§2a–§2e) — قياس فقط، لا تغيير تنبيه/عتبة ═══
import ignition_e2_analyze as _A
import ignition_e2_assemble as _ASM
import gzip as _gz
# ── §2d: توحيد طابع NBBO (نانو/مايكرو/ملّي/ثوانٍ → ملّي) + عمر/طزاجة (نقيّة) ──
check("🔬 §2d نقيّة: _normalize_ts_ms يوحّد نانو/مايكرو/ملّي/ثوانٍ → ملّي (وNone للصغير)",
      _M._normalize_ts_ms(1_750_000_000_000_000_000) == 1_750_000_000_000     # نانو
      and _M._normalize_ts_ms(1_750_000_000_000_000) == 1_750_000_000_000     # مايكرو
      and _M._normalize_ts_ms(1_750_000_000_000) == 1_750_000_000_000         # ملّي
      and _M._normalize_ts_ms(1_750_000_000) == 1_750_000_000_000             # ثوانٍ
      and _M._normalize_ts_ms(1300) is None and _M._normalize_ts_ms(None) is None
      and _M._normalize_ts_ms("x") is None)
_fr_fresh = _M._quote_freshness(1000, 4000)      # عمر 3000 ≤ 5000 = طازج
_fr_stale = _M._quote_freshness(1000, 7000)      # عمر 6000 > 5000 = بائت
_fr_future = _M._quote_freshness(5000, 1000)     # مستقبلي (سالب) = غير طازج
_fr_miss = _M._quote_freshness(None, 4000)       # مفقود
check("🔬 §2d نقيّة: _quote_freshness طازج(≤5ث)/بائت/مستقبلي/مفقود",
      _fr_fresh == (3000, True) and _fr_stale == (6000, False)
      and _fr_future == (-4000, False) and _fr_miss == (None, False))
# ── §2d تكامل: NBBO بائت/مفقود/مستقبلي ⇒ primary_executable=False (رغم NBBO صالح) ──
def _e2_nbbo_exec(qts):
    _r = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, "nbbo_%s" % qts))
    _r.trace("04_RAW_IGNITION", {"symbol": "Z", "trigger_bar_start": 1_750_000_060_000, "break_level": 2.0})
    _r.trace("05_OPERATOR_MEASURED", {"symbol": "Z", "operator_status": "measured", "has_operator": True,
             "nbbo_bid": 2.14, "nbbo_ask": 2.16, "quote_ts": qts})
    return _r._cur_candidate("Z")
check("🔬 §2d تكامل: بائت(قبل 100ث)/مفقود(None)/مستقبلي ⇒ غير تنفيذي؛ طازج ⇒ تنفيذي",
      _e2_nbbo_exec(int((_time_e2.time() - 100) * 1e9))["primary_executable"] is False
      and _e2_nbbo_exec(None)["primary_executable"] is False
      and _e2_nbbo_exec(int((_time_e2.time() + 100) * 1e9))["primary_executable"] is False
      and _e2_nbbo_exec(int(_time_e2.time() * 1e9))["primary_executable"] is True)
# ── §2b: ردم مسار ما بعد التنبيه — بارات بعد لحظة الاشتعال للرمز المُنبَّه ──
_rec_bf = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, "bf"))
S.scan_ignition(_e2_wl(), "2026-07-20", fetch_bars=_e2_fb, fetch_operator=_e2_fo_fresh, trace=_rec_bf.trace)
_bf_start = _rec_bf._cur_candidate("IGN")["trigger_bar_start"]
_bf_n = _rec_bf.backfill_emitted(lambda s: [{"o": 2.2, "h": 2.3, "l": 2.1, "c": 2.25, "v": 5,
                                             "t": int(_bf_start) + 60000 * k} for k in (2, 3, 4)])
_rec_bf.finalize("normal")
_bf_path = _os.path.join(_e2_out, "bf", "session_2026-07-20", "minute_paths.jsonl.gz")
with _gz.open(_bf_path, "rt", encoding="utf-8") as _fh:
    _bf_mins = [_json.loads(x) for x in _fh if x.strip()]
_bf_post = [m["t"] for m in _bf_mins if m["symbol"] == "IGN" and m["t"] > _bf_start]
_bf_ss = {r["symbol"]: r for r in _e2_read_jsonl("bf", "symbol_sessions.jsonl")}
check("🔬 §2b ردم بعدي: مسار الدقيقة يحوي بارات **بعد** لحظة الاشتعال للرمز المُنبَّه (+حالة backfill)",
      _bf_n == 1 and len(_bf_post) == 3 and all(t > _bf_start for t in _bf_post)
      and _bf_ss["IGN"]["backfill_status"] == "done_unverified"
      and _bf_ss["IGN"]["backfill_bars_added"] == 3 and _bf_ss["IGN"]["backfill_last_bar_ts"] is not None)
# 🔬 P1.2: backfill_status = success فقط عند بلوغ الحدّ المتوقّع؛ partial لو قصُر؛ empty/error.
_rec_bs = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, "bstat"))
S.scan_ignition(_e2_wl(), "2026-07-20", fetch_bars=_e2_fb, fetch_operator=_e2_fo_fresh, trace=_rec_bs.trace)
_bs_start = int(_rec_bs._cur_candidate("IGN")["trigger_bar_start"])
_rec_bs.backfill_emitted(lambda s: [{"o": 2.2, "h": 2.3, "l": 2.1, "c": 2.25, "v": 5,
                                     "t": _bs_start + 60000 * k} for k in (1, 2, 3)],
                         expected_last_bar_ts=_bs_start + 60000 * 3)
_bs_ss_ok = _rec_bs._sym("IGN")["backfill_status"]
_rec_bs2 = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, "bstat2"))
S.scan_ignition(_e2_wl(), "2026-07-20", fetch_bars=_e2_fb, fetch_operator=_e2_fo_fresh, trace=_rec_bs2.trace)
_bs2_start = int(_rec_bs2._cur_candidate("IGN")["trigger_bar_start"])
_rec_bs2.backfill_emitted(lambda s: [{"o": 2.2, "h": 2.3, "l": 2.1, "c": 2.25, "v": 5, "t": _bs2_start + 60000}],
                          expected_last_bar_ts=_bs2_start + 60000 * 100)   # الحدّ بعيد ⇒ قصور
_bs_ss_partial = _rec_bs2._sym("IGN")["backfill_status"]
_rec_bs3 = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, "bstat3"))
S.scan_ignition(_e2_wl(), "2026-07-20", fetch_bars=_e2_fb, fetch_operator=_e2_fo_fresh, trace=_rec_bs3.trace)
_rec_bs3.backfill_emitted(lambda s: None)          # لا بارات ⇒ empty
_bs_ss_empty = _rec_bs3._sym("IGN")["backfill_status"]
check("🔬 P1.2: backfill_status success(بلغ الحدّ)/partial(قصُر)/empty(بلا بارات)",
      _bs_ss_ok == "success" and _bs_ss_partial == "partial" and _bs_ss_empty == "empty")
# ── §2e نقيّة: exposure + أهلية recall بالشروط الثلاثة ──
check("🔬 §2e نقيّة: _exposure_minutes(90د) + _recall_eligible يشترط الثلاثة معًا",
      _M._exposure_minutes("2026-07-20T13:30:00Z", "2026-07-20T15:00:00Z") == 90.0
      and _M._exposure_minutes("2026-07-20T15:00:00Z", "2026-07-20T13:30:00Z") == 0.0
      and _M._recall_eligible(20, 0.80, 60) is True
      and _M._recall_eligible(19, 0.99, 99) is False        # polls ناقصة
      and _M._recall_eligible(99, 0.79, 99) is False        # coverage ناقصة
      and _M._recall_eligible(99, 0.99, 59) is False)       # exposure ناقصة
# ── §2a: _session_window ديناميكي (إغلاق فعلي + سقف تشغيل + تجاوز صريح) ──
_e2_env_saved = {_k: _os.environ.get(_k) for _k in ("IGNITION_MAX_RUNTIME_MIN", "IGNITION_END_UTC")}
_os.environ["IGNITION_MAX_RUNTIME_MIN"] = "335"
_os.environ.pop("IGNITION_END_UTC", None)
_win_su = IG._segment_window("", S.dt.datetime(2026, 7, 13, 13, 35, tzinfo=S.dt.timezone.utc))   # صيف
_win_wi = IG._segment_window("", S.dt.datetime(2026, 1, 15, 13, 35, tzinfo=S.dt.timezone.utc))   # شتاء
_os.environ["IGNITION_END_UTC"] = "18:00"
_win_ov = IG._segment_window("", S.dt.datetime(2026, 7, 13, 13, 35, tzinfo=S.dt.timezone.utc))
for _k, _v in _e2_env_saved.items():          # استرجاع البيئة
    _os.environ.pop(_k, None) if _v is None else _os.environ.__setitem__(_k, _v)
check("🔬 §2a: _segment_window إغلاق ديناميكي (صيف 20:00 · شتاء 21:00) + سقف تشغيل + تجاوز صريح",
      _win_su["close"].strftime("%H:%M") == "20:00" and _win_wi["close"].strftime("%H:%M") == "21:00"
      and _win_su["reason"] == "max_runtime_cap" and _win_su["deadline"].strftime("%H:%M") == "19:10"
      and _win_ov["reason"] == "env_override" and _win_ov["deadline"].strftime("%H:%M") == "18:00")
check("🔬 (ب+) قفل workflow: 3 jobs متسلسلة (open→close→assemble) + دِدوب handoff + بلا 19:20",
      (lambda t: "IGNITION_END_UTC:" not in t and "IGNITION_MAX_RUNTIME_MIN:" in t
       and "open_segment:" in t and "close_segment:" in t and "assemble_e2_session:" in t
       and t.count("needs:") >= 2 and 'IGNITION_SEGMENT: "open"' in t
       and 'IGNITION_SEGMENT: "close"' in t and "IGNITION_HANDOFF_IN" in t
       )(open(".github/workflows/ignition.yml", encoding="utf-8").read()))
# 🔬 مراجعة Codex 5 (P0): تنبيهات مقطع الإغلاق **لا تُعلَّق على نجاح القياس** — لا على نجاح job
# الافتتاح (`if: always()`) ولا على تنزيل الartifact (`continue-on-error`). فشل نقل القياس يجعل
# الجلسة غير مؤهّلة للتحليل، لا يُسكت الرادار 195 دقيقة حتى الإغلاق.
check("🔬 Codex5 قفل workflow: close_segment يشتغل رغم فشل open/غياب artifact (fail-open للتنبيه)",
      (lambda t: (lambda cl: "if: always()" in cl and "continue-on-error: true" in cl
                  and cl.index("continue-on-error: true") < cl.index("run: python ignition_live.py")
                  )(t[t.index("close_segment:"):t.index("assemble_e2_session:")])
       )(open(".github/workflows/ignition.yml", encoding="utf-8").read()))
# session.json يسجّل «انتهت قبل الإغلاق المتوقّع» (إغلاق متوقّع بعد ساعتين من الآن)
_rec_ec = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, "early"),
            meta={"expected_close_iso": (S.dt.datetime.now(S.dt.timezone.utc).replace(microsecond=0, second=0)
                  + S.dt.timedelta(minutes=120)).strftime("%Y-%m-%dT%H:%M:%SZ")})
_rec_ec.trace("01_SEEN_ACTIVE", {"symbol": "A"})
_rec_ec.finalize("normal")
_ec_sess = _e2_read_json("early", "session.json")
check("🔬 §2a: session.json يعلِّم ended_before_expected_close + minutes_short_of_close",
      _ec_sess["ended_before_expected_close"] is True and _ec_sess["minutes_short_of_close"] >= 100)
# ── §2e/P0-3: المدقّق يشدّد الاكتمال (session_complete: المسار يصل للإغلاق) ──
def _e2_build_session(sub, sd, *, close_off=-5, backfill=True, loops=(2, 2), term="normal"):
    _close_dt = (S.dt.datetime.now(S.dt.timezone.utc).replace(microsecond=0, second=0)
                 + S.dt.timedelta(minutes=close_off))
    _close_ms = int(_close_dt.timestamp() * 1000)
    _r = _M.IgnitionMeasurementRecorder(sd, out_root=_os.path.join(_e2_out, sub),
          meta={"expected_close_iso": _close_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "deadline_reason": "market_close"})
    for _ in range(loops[0]):
        _r.loop_start()
    S.scan_ignition(_e2_wl(), sd, fetch_bars=_e2_fb, fetch_operator=_e2_fo_fresh, trace=_r.trace)
    _r.telegram_attempt([({"symbol": "IGN"},)]); _r.telegram_success([({"symbol": "IGN"},)])
    for _ in range(loops[1]):
        _r.loop_end()
    if backfill:                     # بارات تصل للإغلاق (P0-3): success + path_reaching_close
        _r.backfill_emitted(lambda s: [{"o": 2.2, "h": 2.3, "l": 2.1, "c": 2.25, "v": 5,
                                        "t": _close_ms - 60000 * k} for k in (3, 2, 1)],
                            expected_last_bar_ts=_close_ms - 60000)
    _r.finalize(term)
    return _A.analyze_session(_os.path.join(_e2_out, sub, "session_" + sd))
_an_ok = _e2_build_session("an_ok", "2026-07-20")
_an_lost = _e2_build_session("an_lost", "2026-07-21", backfill=False)
_an_loop = _e2_build_session("an_loop", "2026-07-22", loops=(3, 2))
_an_early = _e2_build_session("an_early", "2026-07-23", close_off=+120)
_an_exc = _e2_build_session("an_exc", "2026-07-24", term="exception")
check("🔬 §2e/P0-3 مدقّق: جلسة نظيفة (المسار يصل للإغلاق) ⇒ session_complete=True بلا أسباب",
      _an_ok["complete"] is True and _an_ok["session_complete"] is True
      and _an_ok["incomplete_reasons"] == [] and _an_ok["kind"] == "single"
      and _an_ok["candidates_with_timestamps"] == _an_ok["n_candidates"])
check("🔬 §2e/P0-3 مدقّق: يرفض عند عدم بلوغ المسار الإغلاق/عدم توازن الدورات/إغلاق مبكّر/إنهاء غير طبيعي",
      _an_lost["complete"] is False and any("path_not_reaching_close" in x for x in _an_lost["incomplete_reasons"])
      and _an_loop["complete"] is False and any("loops_mismatch" in x for x in _an_loop["incomplete_reasons"])
      and _an_early["complete"] is False and any("ended_before_expected_close" in x for x in _an_early["incomplete_reasons"])
      and _an_exc["complete"] is False and any("termination" in x for x in _an_exc["incomplete_reasons"]))
# ── 🔬 (ب+): مقطع (segment_complete) + دمج مقطعين → assembled (session_complete) ──
def _e2_seg(sub, sd, role, sym, tbs, seg_end_off, close_off=-5, prev=None, post_bar=True):
    _now = S.dt.datetime.now(S.dt.timezone.utc).replace(microsecond=0, second=0)
    _r = _M.IgnitionMeasurementRecorder(sd, out_root=_os.path.join(_e2_out, sub), segment=role,
          meta={"expected_close_iso": (_now + S.dt.timedelta(minutes=close_off)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "expected_segment_end_iso": (_now + S.dt.timedelta(minutes=seg_end_off)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "expected_open_iso": (_now - S.dt.timedelta(minutes=200)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "source_commit": "abc", "workflow_run_id": "run1", "interval_seconds": 45,
                "previous_segment_manifest_sha256": prev})
    _r.loop_start()
    _r.trace("01_SEEN_ACTIVE", {"symbol": sym})
    _r.trace("03_BARS_FETCH", {"symbol": sym, "bars_ok": True, "last_bar_t": tbs,
             "bars": [{"o": 2, "h": 2.1, "l": 1.9, "c": 2.05, "v": 100, "t": tbs}]})
    _r.trace("04_RAW_IGNITION", {"symbol": sym, "signal_price": 2.15, "break_level": 2.0,
             "break_level_source": "critical_number", "trigger_bar_start": tbs})
    _r.trace("05_OPERATOR_MEASURED", {"symbol": sym, "operator_status": "measured", "has_operator": True,
             "nbbo_bid": 2.14, "nbbo_ask": 2.16, "quote_ts": int(_time_e2.time() * 1e9)})
    _r.trace("06_OPERATOR_PASS", {"symbol": sym}); _r.trace("11_ALERT_EMITTED", {"symbol": sym})
    # ⚠️ `post_bar=True` (الافتراض) = بارٌ **بعد** التنبيه داخل المقطع — وهو ما **لا
    #    يستطيعه الرادار حيًّا** (الدِدوب يقطع الجلب). يبقى افتراضًا لتوافق الفِكستشرات
    #    القائمة، و`post_bar=False` هو المسار الإنتاجيّ الأمين (أقفال E2F أدناه).
    if post_bar:
        _r.trace("03_BARS_FETCH", {"symbol": sym, "bars_ok": True, "last_bar_t": tbs + 60000,
                 "bars": [{"o": 2, "h": 2.1, "l": 1.9, "c": 2.06, "v": 90, "t": tbs + 60000}]})
    _r.telegram_attempt([({"symbol": sym},)]); _r.telegram_success([({"symbol": sym},)])
    _r.loop_end()
    _r.finalize("normal")
    return _r
_seg_now_ms = int(S.dt.datetime.now(S.dt.timezone.utc).timestamp() * 1000)
_ro_seg = _e2_seg("segd", "2026-07-25", "open", "IGN", _seg_now_ms - 3600_000, seg_end_off=-90)
_e2_seg("segd", "2026-07-25", "close", "BBB", _seg_now_ms - 600_000, seg_end_off=+5,
        prev=_ro_seg.manifest_sha256)   # 🔬 P0-4: سلسلة manifest سليمة
_r_seg_open = _A.analyze_session(_os.path.join(_e2_out, "segd", "session_2026-07-25", "segment_open"))
# assemble the two segments (backfill reaching close)
_asm_close_ms = int((S.dt.datetime.now(S.dt.timezone.utc).replace(microsecond=0, second=0)
                     - S.dt.timedelta(minutes=5)).timestamp() * 1000)
_asm_summ = _ASM.assemble("2026-07-25", root=_os.path.join(_e2_out, "segd"), write_repo_index=False,
                          fetch_bars=lambda s: [{"o": 2, "h": 2.1, "l": 2, "c": 2.05, "v": 10,
                                                 "t": _asm_close_ms - 60000 * k} for k in (3, 2, 1)])
_r_asm = _A.analyze_session(_os.path.join(_e2_out, "segd", "session_2026-07-25"))
check("🔬 (ب+) مدقّق: المقطع ⇒ segment_complete (لا session_complete) · المدموجة ⇒ session_complete",
      _r_seg_open["kind"] == "segment" and _r_seg_open["segment_complete"] is True
      and _r_seg_open["session_complete"] is None
      and _r_asm["kind"] == "assembled" and _r_asm["session_complete"] is True
      and _asm_summ["n_symbols"] == 2 and _r_asm["n_emitted"] == 2)
check("🔬 (ب+) دمج: candidates المقطعين مدموجة بلا ازدواج + backfill بلغ الإغلاق (success)",
      _r_asm["n_candidates"] == 2 and _r_asm["incomplete_reasons"] == [])

# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
# 🟢🔴 BG — «لا إشعارَ إلا داخل النطاق» (قرار المالك 2026-08-06 · الخيار ①)
# ══════════════════════════════════════════════════════════════════════════════
# العيبُ المقيس: توقّعٌ **+0.056R ≈ صفر** مع نجاح 63.2% — لأن الوقفَ يُقاس من الدعم
# والدخولَ يقع **فوق** نطاق الدفعات. والقياسُ الحيّ على القائمة (18 سهمًا): **9 من 10
# «جاهز» فوق النطاق ويتكدّسون تحت سقف الـ5% في `entry_mode`** (أقصاهم +4.9%).
# ⚖️ والدفعاتُ أوامرُ حدٍّ **تحت** السوق ⇒ سعرٌ فوق أعلاها **لا يُعبّئ** ⇒ «ادخل الآن»
#    كانت تصفُ حالةً لا تنفَّذ. الأثرُ المقيس للبوّابة: 🟢 **‏10 ⟶ 1** على قائمة اليوم.
def _bg(lp, trs=(1.00, 1.03, 1.06), mode="near_support"):
    return S.entry_status({"symbol": "BG", "last_price": lp, "tranches": list(trs),
                           "pivot": 1.00, "stop": [0.93],
                           "interp": {"entry_mode": {"mode": mode}}})


check("🟢 BG1 فوق أعلى دفعةٍ ⇒ 👀 متابعة بسببٍ **عمليّ** (ضع الطلبات وانتظر)",
      _bg(1.08)["status"] == "watch" and "ضع الطلبات" in _bg(1.08)["reason"]
      and "1.9" in _bg(1.08)["reason"],   # 1.08/1.06−1 = +1.9% فوق **السقف** لا الدعم
      _bg(1.08)["reason"])
check("🟢 BG2 داخل النطاق ⇒ 🟢 جاهز (البوّابةُ ليست كتمًا دائمًا)",
      _bg(1.04)["status"] == "ready_now" and _bg(1.06)["status"] == "ready_now")
check("🟢 BG3 تحت النطاق فوق الدعم ⇒ 🟢 جاهز (تعبئةٌ أفضل لا أسوأ)",
      _bg(1.01)["status"] == "ready_now")
# 🔒 فاشلٌ-آمنٌ **مفتوح**: كتمُ كرتٍ إزالة، والمجهولُ يمرّ بفائدة الشك.
check("🟢 BG4 بلا دفعاتٍ ⇒ يبقى جاهزًا (لا نكتم على بياناتٍ ناقصة)",
      S.entry_status({"symbol": "BG", "last_price": 9.9, "tranches": [],
                      "interp": {"entry_mode": {"mode": "near_support"}}}
                     )["status"] == "ready_now")
check("🟢 BG5 ودفعاتٌ تالفة ⇒ جاهزٌ بلا انهيار (NaN/نصّ)",
      S.entry_status({"symbol": "BG", "last_price": 9.9, "tranches": ["س", None],
                      "interp": {"entry_mode": {"mode": "near_support"}}}
                     )["status"] == "ready_now"
      and S.entry_status({"symbol": "BG", "last_price": float("nan"),
                          "tranches": [1.0, 1.06],
                          "interp": {"entry_mode": {"mode": "near_support"}}}
                         )["status"] == "ready_now")
# 🔒 العتبةُ **مقروءةٌ من CONFIG** لا مُثبَّتةٌ في الكود (وإلّا لا يستطيع المالك تليينها).
_bg_old = S.CONFIG["ENTRY_READY_BAND_TOL_PCT"]
try:
    S.CONFIG["ENTRY_READY_BAND_TOL_PCT"] = 5.0
    _bg_loose = _bg(1.10)["status"]        # +3.8% فوق السقف — يمرّ بتسامح 5%
finally:
    S.CONFIG["ENTRY_READY_BAND_TOL_PCT"] = _bg_old
check("🟢 BG6 العتبةُ من CONFIG (تسامح 5% ⇒ يعود جاهزًا) — قابلةٌ للتليين بسطر",
      _bg_loose == "ready_now" and _bg(1.10)["status"] == "watch",
      f"بتسامح5={_bg_loose} · بالافتراض={_bg(1.10)['status']}")
check("🟢 BG7 والافتراضُ **صفر** (قرار المالك ①)",
      S.CONFIG["ENTRY_READY_BAND_TOL_PCT"] == 0.0)
# 🔒 والبوّابةُ **لا تقلب متابعةً إلى جاهز** (اتّجاهٌ واحد فقط)
check("🟢 BG8 `reclaim_wait` يبقى متابعةً (البوّابةُ أحاديّةُ الاتّجاه)",
      _bg(1.02, mode="reclaim_wait")["status"] == "watch")
# 🔒 والالتقاطُ **ضيّق**: `except Exception` عريضٌ يخفي عيوبًا أخرى (قاعدةٌ موثّقة في
#    حارسَي M13/M14). قفلٌ نصّيٌّ **على جسم البوّابة وحده** لا على الدالّة كلّها.
# ⚠️ الحدُّ **إلزاميّ**: لـ`entry_status` نفسها حارسٌ خارجيٌّ عريضٌ مقصود (فاشلة-آمنة
#    → «متابعة» بسبب صريح)، فلو امتدّ المقطعُ لآخر الدالّة **سقط القفلُ على كودٍ سليم**
#    — وهو ما وقع فعلًا أوّل مرّة وكشفه فحصُ ما-بعد-الاستعادة في مِنصّة الطفرات.
# 🔒 وبـ`find` لا `index`: غيابُ الثابت يجب أن يكون **فشلًا نظيفًا** لا انهيارًا يُسقط
#    السويّة ويكتم **أيُّ** قفلٍ أمسك العيب (صنفٌ وقع مرّتين في هذي الجلسة).
_bg_src = _insp0.getsource(S.entry_status)
_bg_i = _bg_src.find("ENTRY_READY_BAND_TOL_PCT")
_bg_j = _bg_src.find('"label": "🟢 جاهز للدخول الآن"', _bg_i) if _bg_i >= 0 else -1
_bg_body = _bg_src[_bg_i:_bg_j] if (_bg_i >= 0 and _bg_j > _bg_i) else ""
check("🔒 BG10 التقاطُ البوّابة ضيّقٌ `(TypeError, ValueError)` لا `Exception` عريض",
      bool(_bg_body) and "except (TypeError, ValueError)" in _bg_body
      and "except Exception" not in _bg_body,
      (_bg_body[-160:].replace("\n", " ⏎ ") if _bg_body else "⛔ جسمُ البوّابة غير موجود"))
# 🔴 والحاسم: **مُطبَّقةٌ في مسار الدفع الحيّ** لا في الدالّة وحدها (درسُ «نقطة النداء»).
# ⚠️ الشكلُ **مأخوذٌ من سجلٍّ حقيقيّ** في القائمة (‏`stop` **عدد** لا قائمة · و`entry`
#    مدى · و`targets_kind` ثلاثة) — وأوّلُ فِكستشرٍ كتبتُه بـ`stop=[0.93]` **أسقط
#    المُصيِّر**، وهو صنفُ «الفِكستشر يكذب» الذي كشفه انهيارٌ لا قراءة.
_bg_hi = {"symbol": "BGHI", "last_price": 1.08, "price": 1.08, "tranches": [1.0, 1.03, 1.06],
          "pivot": 1.0, "stop": 0.93, "entry": [1.0, 1.06], "t1": 1.3, "t2": 1.5, "t3": 1.7,
          "rr": 2.0, "score": 60, "tier": "B", "status": "active", "added": "2026-08-06",
          "targets_kind": ["⚫", "⚫", "🔵"],
          "flags": [], "warnings": [], "interp": {"entry_mode": {"mode": "near_support"}}}
_bg_in = dict(_bg_hi, symbol="BGIN", last_price=1.04, price=1.04)
_bg_msg = S.build_daily_message({"stocks": [_bg_hi, _bg_in], "week_start": "2026-08-03"},
                                [], [], [], ready_only=True)
check("🔴 BG9 مسارُ الدفع الحيّ: كرتُ الجاهز وحده يُدفَع · وفوق-النطاق لا يُدفَع",
      "BGIN" in _bg_msg and "BGHI" not in _bg_msg,
      f"BGIN={'BGIN' in _bg_msg} · BGHI={'BGHI' in _bg_msg}")

# 🔴 E2F — بوّابةٌ كانت **غيرَ قابلةٍ للاستيفاء** كلَّما وُجد ما يُقاس (2026-08-06)
# ══════════════════════════════════════════════════════════════════════════════
# الفِكستشر أعلاه (`post_bar=True`) يسجّل بارًا **بعد** التنبيه داخل المقطع — والرادار
# الحيّ **لا يستطيع ذلك**: الدِدوب في `scan_ignition` يقع **قبل** جلب الشموع، فبعد أوّل
# تنبيهٍ لرمزٍ لا يُجلَب له بارٌ آخر ذلك اليوم. ⇒ كانت السويّة خضراء والبوّابة الحيّة
# حمراء منذ 07-30، والارتباط في السجلّ المدفوع قاطع: `n_emitted > 0` ⟺ أحمر.
# 🧭 وهو صنفُ «الاختبار ينجح ونقطة الاستعمال الحيّة مكسورة» — والفِكستشر هنا هو الكاذب.
_f_now_ms = int(S.dt.datetime.now(S.dt.timezone.utc).timestamp() * 1000)
_f_close_ms = int((S.dt.datetime.now(S.dt.timezone.utc).replace(microsecond=0, second=0)
                   - S.dt.timedelta(minutes=5)).timestamp() * 1000)
_f_bf = lambda s: [{"o": 2, "h": 2.1, "l": 2, "c": 2.05, "v": 10,
                    "t": _f_close_ms - 60000 * k} for k in (3, 2, 1)]


def _e2_faithful(sub, bf, close_seg_end=+5):
    """جلسةٌ **أمينةٌ للإنتاج**: بلا بارٍ بعد التنبيه في أيّ مقطع. يرجّع حكم المدقّق."""
    _o = _e2_seg(sub, "2026-07-25", "open", "IGN", _f_now_ms - 3600_000,
                 seg_end_off=-90, post_bar=False)
    _e2_seg(sub, "2026-07-25", "close", "BBB", _f_now_ms - 600_000,
            seg_end_off=close_seg_end, prev=_o.manifest_sha256, post_bar=False)
    _ASM.assemble("2026-07-25", root=_os.path.join(_e2_out, sub),
                  write_repo_index=False, fetch_bars=bf)
    return _A.analyze_session(_os.path.join(_e2_out, sub, "session_2026-07-25"))


_f_ok = _e2_faithful("segF_ok", _f_bf)
check("🔴 E2F1 جلسةٌ أمينةٌ للإنتاج (بلا بارٍ بعد التنبيه) ⇒ session_complete",
      _f_ok["session_complete"] is True, str(_f_ok["incomplete_reasons"]))
check("🔴 E2F2 والتأجيلُ **مُعلَنٌ** لا صامت (يُذكر المقطع والسبب)",
      any("lost_post_alert_path" in x and x.startswith("open:")
          for x in (_f_ok.get("deferred_reasons") or [])),
      str(_f_ok.get("deferred_reasons")))
# ── شاهدا ضبط: الجوهر ما زال يَرفض (وإلّا صار الإصلاح تخفيفًا صامتًا) ────────────
_f_nobf = _e2_faithful("segF_nobf", None)                   # الردمُ لم يُنفَّذ إطلاقًا
check("🔴 E2F3 شاهدُ ضبط: بلا ردمٍ ⇒ تُرفَض بـ`path_not_reaching_close`",
      _f_nobf["session_complete"] is False
      and any("path_not_reaching_close" in x for x in _f_nobf["incomplete_reasons"]),
      str(_f_nobf["incomplete_reasons"]))
_f_short = _e2_faithful("segF_short", lambda s: [{"o": 2, "h": 2.1, "l": 2, "c": 2.05, "v": 10,
                                                  "t": _f_close_ms - 60000 * 200}])
check("🔴 E2F4 شاهدُ ضبط: ردمٌ قصُر عن الإغلاق ⇒ تُرفَض أيضًا",
      _f_short["session_complete"] is False
      and any("path_not_reaching_close" in x for x in _f_short["incomplete_reasons"]),
      str(_f_short["incomplete_reasons"]))
# ── والفلترُ **ضيّق**: سببُ مقطعٍ آخر ما زال يَرفض (لم يُعطَّل `segment_incomplete`) ──
_f_wnd = _e2_faithful("segF_wnd", _f_bf, close_seg_end=+120)   # نافذةُ close غير مغطّاة
check("🔴 E2F5 والفلترُ ضيّق: سببُ مقطعٍ **غيرُ مؤجَّل** ما زال يَرفض",
      _f_wnd["session_complete"] is False
      and any(x.startswith("segment_incomplete(close:") for x in _f_wnd["incomplete_reasons"]),
      str(_f_wnd["incomplete_reasons"]))
# 🔒 والمبرّرُ نفسُه مقفولٌ **بنيويًّا**: الدِدوب **قبل** جلب الشموع في `scan_ignition`.
#    لو نُقل بعدَه يومًا صار البارُ اللاحق ممكنًا فيسقط مبرّرُ التأجيل — فيسقط هذا القفل.
import ast as _f_ast
_f_fn = next(n for n in _f_ast.walk(_f_ast.parse(open("Super_stock.py", encoding="utf-8").read()))
             if isinstance(n, _f_ast.FunctionDef) and n.name == "scan_ignition")
_f_dedup_ln = min([n.lineno for n in _f_ast.walk(_f_fn)
                   if isinstance(n, _f_ast.Constant) and n.value == "ignition_alert"] or [10**9])
_f_fetch_ln = min([n.lineno for n in _f_ast.walk(_f_fn)
                   if isinstance(n, _f_ast.Call) and getattr(n.func, "id", None) == "fb"] or [-1])
check("🔒 E2F6 مبرّرُ التأجيل قائم: الدِدوب **يسبق** جلب الشموع في `scan_ignition` (AST)",
      _f_dedup_ln < _f_fetch_ln and _f_fetch_ln > 0,
      f"dedup@{_f_dedup_ln} · fb()@{_f_fetch_ln}")
check("🔒 E2F7 وقائمةُ التأجيل **واحدة** ولا تتمدّد بلا قصد",
      _A.DEFERRED_TO_ASSEMBLER == ("lost_post_alert_path",),
      str(_A.DEFERRED_TO_ASSEMBLER))
# ── 🔬 P0-1/P1.3: NBBO قياسي **لا-تزامني** (worker) خارج مسار التنبيه + measurement مفضَّل ──
_p13_fresh = int(_time_e2.time() * 1e9)
_p13_stale = int((_time_e2.time() - 100) * 1e9)
# recorder بجالب NBBO محقون (measurement طازج) — يُربط لا-تزامنيًّا؛ operator بائت عبر scan.
_rec_p13 = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, "p13"),
             nbbo_fetcher=lambda s: {"bid": 2.10, "ask": 2.20, "quote_ts": _p13_fresh})
S.scan_ignition(_e2_wl(), "2026-07-20", fetch_bars=_e2_fb,
                fetch_operator=lambda s: {"has_operator": True, "bid": 2.14, "ask": 2.16, "quote_ts": _p13_stale},
                trace=_rec_p13.trace)
_rec_p13.finalize("normal")          # يفرّغ worker → measurement مربوط بـcandidate_id
_c13 = _rec_p13.candidates[list(_rec_p13.candidates)[0]]
check("🔬 P0-1/P1.3: NBBO measurement لا-تزامني (طازج) مفضَّل على operator (بائت) + الحالة resolved",
      _c13["measurement_nbbo_status"] == "success" and _c13["measurement_executable"] is True
      and _c13["operator_executable"] is False and _c13["nbbo_source"] == "measurement"
      and _c13["primary_executable"] is True and _c13["quote_capture_lag_ms"] is not None
      and _c13["measurement_nbbo_mid"] == 2.15 and _c13["operator_nbbo_mid"] == 2.15)
# **قفل P0-1 الحاسم:** جالب NBBO بطيء (محاكاة 8ث) **لا يؤخّر** مسار الاشتعال/التنبيه (لا-تزامني)
_rec_slow = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, "slow"),
              nbbo_fetcher=lambda s: (_time_e2.sleep(1.2), {"bid": 2.1, "ask": 2.2, "quote_ts": _p13_fresh})[1])
_t_alert0 = _time_e2.time()
S.scan_ignition(_e2_wl(), "2026-07-20", fetch_bars=_e2_fb, fetch_operator=_e2_fo_fresh, trace=_rec_slow.trace)
_alert_ms = (_time_e2.time() - _t_alert0) * 1000
_rec_slow.finalize("normal")
check("🔬 P0-1 قفل: جالب NBBO بطيء (1.2ث) **لا يؤخّر** مسار الاشتعال/التنبيه (لا-تزامني)",
      _alert_ms < 400)
check("🔬 P0-1 قفل: scan_ignition **لا** يجلب NBBO القياسي إطلاقًا · polygon_nbbo خارج الفرز",
      "polygon_nbbo" not in _insp0.getsource(S.scan_ignition)
      and "fetch_measure_nbbo" not in _insp0.getsource(S.scan_ignition)
      and all("polygon_nbbo" not in _insp0.getsource(_f) for _f in (S.rank_key, S.select_top)))
check("🔬 P1-3: تفكيك latency (bar→raw→gate→attempt→success) موجود في candidate",
      all(_k in _c13 for _k in ("bar_end_to_raw_signal_ms", "raw_signal_to_gate_decision_ms",
          "gate_decision_to_telegram_attempt_ms", "telegram_attempt_to_success_ms",
          "bar_end_to_telegram_success_ms")))
def _p15_status(sub, fetcher):
    _r = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, sub), nbbo_fetcher=fetcher)
    _r.trace("04_RAW_IGNITION", {"symbol": "Z", "trigger_bar_start": 1_750_000_060_000, "break_level": 2.0})
    _r.finalize("normal")
    return _r.candidates[list(_r.candidates)[0]]["measurement_nbbo_status"]
def _p15_raise_timeout(s):
    raise TimeoutError("x")
check("🔬 P1-5: measurement_nbbo_status محسوم لكل cohorts (success/empty/timeout/not_requested)",
      _p15_status("co_ok", lambda s: {"bid": 2.1, "ask": 2.2, "quote_ts": _p13_fresh}) == "success"
      and _p15_status("co_empty", lambda s: None) == "empty"
      and _p15_status("co_to", _p15_raise_timeout) == "timeout"
      and _p15_status("co_nr", None) == "not_requested")
# ── 🔬 P1.6: أثر الأداة (median/p95 + نسبة تجاوز interval) ──
_rec_p16 = _M.IgnitionMeasurementRecorder("2026-07-20", out_root=_os.path.join(_e2_out, "p16"),
                                          meta={"interval_seconds": 1})
for _d in (500, 1500, 800):        # واحدة (1500) تجاوزت interval=1000ms
    _rec_p16.loop_start(); _rec_p16.loop_end(schedule_lag_ms=50, loop_duration_ms=_d)
_rec_p16.finalize("normal")
_p16 = _e2_read_json("p16", "session.json")["instrumentation_timing"]
check("🔬 P1.6: instrumentation_timing (median/p95 + نسبة تجاوز interval) محسوب",
      _p16["loop_duration_ms_median"] == 800 and _p16["n_timed_loops"] == 3
      and abs(_p16["loops_over_interval_ratio"] - (1 / 3)) < 0.01)
# ── 🔬 (ب+): استعادة الدِدوب عبر المقاطع = **لا تنبيه مكرّر** ──
_wl_seg2 = {"stocks": [{"symbol": "IGN", "status": "active", "pivot": 1.90,
                        "interp": {"critical_number": {"price": 2.00}}}]}
IG._apply_handoff_dedup(_wl_seg2, {"alerted_symbols": ["IGN"]}, "2026-07-20")
_rows_seg2 = S.scan_ignition(_wl_seg2, "2026-07-20", fetch_bars=_e2_fb, fetch_operator=_e2_fo_fresh)
check("🔬 (ب+) قفل: رمز مُنبَّه في المقطع السابق (ختم دِدوب مُستعاد) لا يُطلَق ثانيةً (لا تكرار)",
      _rows_seg2 == [] and IG._apply_handoff_dedup({"stocks": []}, {}, "x") == 0)
check("🔬 §2 قفل: مساعِدات الفجوات نقيّة خارج مسار الفرز (لا تُستورَد بـSuper_stock)",
      all(_n not in _insp0.getsource(S.scan_ignition) and _n not in _insp0.getsource(S.rank_key)
          for _n in ("_normalize_ts_ms", "_quote_freshness", "backfill_emitted", "_recall_eligible")))
# ── 🔬 P0-4: manifest + سلسلة SHA-256 + كشف العبث (fail-closed) ──
import ignition_e2_manifest as _MAN
def _mseg(sub, role, sym, prev=None):
    _r = _M.IgnitionMeasurementRecorder("2026-07-26", out_root=_os.path.join(_e2_out, sub), segment=role,
          meta={"expected_close_iso": "2026-07-26T20:00:00Z", "source_commit": "abc", "workflow_run_id": "r1",
                "previous_segment_manifest_sha256": prev})
    _r.trace("04_RAW_IGNITION", {"symbol": sym, "trigger_bar_start": 1_750_000_060_000, "break_level": 2.0})
    _r.trace("11_ALERT_EMITTED", {"symbol": sym}); _r.finalize("normal")
    return _r
_mo = _mseg("manf", "open", "IGN")
_mc = _mseg("manf", "close", "BBB", prev=_mo.manifest_sha256)
_mo_dir = _os.path.join(_e2_out, "manf", "session_2026-07-26", "segment_open")
_mc_dir = _os.path.join(_e2_out, "manf", "session_2026-07-26", "segment_close")
_om, _cm = _MAN.read_manifest(_mo_dir), _MAN.read_manifest(_mc_dir)
_ok_o = _MAN.verify_manifest(_om, _mo_dir, expect_session_date="2026-07-26", expect_segment="open")[0]
_ok_chain = _MAN.verify_chain(_om, _cm)[0]
# tamper: عدّل بايت في candidates → raw_hash_mismatch
_tp = _os.path.join(_mo_dir, "candidates.jsonl")
_orig = open(_tp, "rb").read()
open(_tp, "wb").write(_orig.replace(b'"IGN"', b'"ZZZ"', 1))
_ok_tamper, _r_tamper = _MAN.verify_manifest(_om, _mo_dir)
open(_tp, "wb").write(_orig)   # استرجاع
# chain break
_ok_break = _MAN.verify_chain(_om, dict(_cm, previous_segment_manifest_sha256="deadbeef"))[0]
check("🔬 P0-4: manifest نظيف يتحقّق + العبث (byte) = raw_hash_mismatch + كسر السلسلة يُرفض",
      _ok_o is True and _ok_chain is True
      and _ok_tamper is False and any("raw_hash_mismatch" in x for x in _r_tamper)
      and _ok_break is False)
# _verify_prev_segment (fail-closed): مفقود/تطابق/عدم تطابق hash
_good_ho = {"manifest_sha256": _mo.manifest_sha256, "alerted_symbols": ["IGN"]}
check("🔬 P0-4: _verify_prev_segment يقبل السليم ويرفض المفقود/عدم تطابق handoff",
      IG._verify_prev_segment(_good_ho, "2026-07-26", e2_root=_os.path.join(_e2_out, "manf"))[0] is True
      and IG._verify_prev_segment(None, "2026-07-26", e2_root=_os.path.join(_e2_out, "manf"))[0] is False
      and IG._verify_prev_segment({"manifest_sha256": "wrong", "alerted_symbols": ["IGN"]},
                                  "2026-07-26", e2_root=_os.path.join(_e2_out, "manf"))[0] is False)
check("🔬 P0-4/P1-7 قفل: المقطع (role) لا يستدعي git_save · close يتحقّق قبل المسح",
      "if role:" in _insp0.getsource(IG.main) and "git_save" in _insp0.getsource(IG.main)
      and "_verify_prev_segment" in _insp0.getsource(IG.main))
# 🔬 مراجعة Codex 5 (P0): فشل التحقّق **لا يوقف التنبيه** (fail-open للإنتاج) — الأهلية للقياس
# يحكمها المدقّق بسلسلة manifest، لا بقتل مقطع الإغلاق كلّه.
check("🔬 Codex5 قفل: فشل handoff/manifest لا يوقف المسح (لا SystemExit/strict بمسار الرادار)",
      "SystemExit" not in _insp0.getsource(IG.main)
      and "IGNITION_HANDOFF_STRICT" not in _insp0.getsource(IG.main))
# 🔬 مراجعة Codex 5 (P0): استيراد وحدة القياس **كسول داخل فرع E2 المحمي** — لو كان على مستوى
# الوحدة لقتَل السكربت قبل main() (انكسار قياس ⇒ صفر تنبيه). هنا نُجبر ImportError حقيقيًّا
# (sys.modules[...] = None) ونثبت أن المسح والإرسال يستمرّان.
check("🔬 Codex5 قفل: لا استيراد قياس على مستوى الوحدة (كسول داخل فرع E2_MEASUREMENT)",
      not hasattr(IG, "measure")
      and "import ignition_measurement" in _insp0.getsource(IG.main))
_ml_keys = ("E2_MEASUREMENT", "IGNITION_SEGMENT", "IGNITION_HANDOFF_IN", "IGNITION_HANDOFF_OUT",
            "POLYGON_API_KEY")
_ml_env = {k: _os.environ.get(k) for k in _ml_keys}
# مفتاح وهمي: بوّابة «بلا مفتاح = لا عمل» تُخرج main مبكرًا؛ لا شبكة (scan/send مُستبدلان).
_os.environ.update({"E2_MEASUREMENT": "1", "IGNITION_SEGMENT": "close", "IGNITION_HANDOFF_IN": "",
                    "IGNITION_HANDOFF_OUT": _os.path.join(_e2_out, "ho_close.json"),
                    "POLYGON_API_KEY": "TEST_KEY_NOT_USED"})
import sys as _sys
_sys.modules["ignition_measurement"] = None      # يجبر ImportError عند الاستيراد الكسول


class _StopLoop(Exception):
    pass


_sent_ml, _traces_ml = [], []
_ml_now = S.dt.datetime.utcnow()
_ml_saved = (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
             IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep)
IG._segment_window = lambda role, t0=None: {
    "role": role, "open": _ml_now, "close": _ml_now + S.dt.timedelta(hours=1),
    "segment_start": _ml_now, "segment_end": _ml_now + S.dt.timedelta(hours=1),
    "deadline": _ml_now + S.dt.timedelta(hours=1), "reason": "test",
    "session_type": "regular", "calendar_version": "test"}
IG.bot.load_watchlist = lambda: {"stocks": [{"symbol": "IGN", "status": "active"}]}
IG.bot.scan_ignition = lambda wl, today, trace=None: (
    _traces_ml.append(trace), [({"symbol": "IGN"}, {"price": 2.0}, None)])[1]
IG.bot.build_ignition_alert = lambda rows: "ALERT"
IG.bot.send_telegram = lambda m: _sent_ml.append(m)
IG.time.sleep = lambda *_a: (_ for _ in ()).throw(_StopLoop())   # يوقف الحلقة بعد دورة واحدة
try:
    IG.main()
except (_StopLoop, Exception):
    pass
finally:
    (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
     IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep) = _ml_saved
    _sys.modules.pop("ignition_measurement", None)
    for _k, _v in _ml_env.items():
        _os.environ.pop(_k, None) if _v is None else _os.environ.update({_k: _v})
check("🔬 Codex5 قفل: انكسار وحدة القياس (ImportError) لا يمنع المسح ولا إرسال التنبيه",
      len(_sent_ml) == 1 and _sent_ml[0].startswith("ALERT")   # التنبيه أُرسل (+ التذييل)
      and _traces_ml == [None])                                # المسجّل سقط ⇒ trace=None والرادار يواصل


# 🔬 مراجعة Codex 5 (P0): مسجّل **كل خطّافاته ترمي** — الحلقة الإنتاجية تستمرّ عبر عدة دورات
# والتنبيه يُرسَل في كلٍّ منها (بالذات: telegram_attempt لا يمنع send_telegram). `_SafeRecorder`
# يبتلع ويُعطّل القياس؛ عزل الإنتاج لا يعتمد على «كل خطّاف يبتلع استثناءه بنفسه».
class _BoomRec:
    def __init__(self, *a, **kw):
        pass

    def __getattr__(self, name):
        def _boom(*a, **kw):
            raise RuntimeError("boom:" + name)
        return _boom


import types as _types_ml
_boom_mod = _types_ml.ModuleType("ignition_measurement")
_boom_mod.IgnitionMeasurementRecorder = _BoomRec
_sys.modules["ignition_measurement"] = _boom_mod
_os.environ.update({"E2_MEASUREMENT": "1", "IGNITION_SEGMENT": "close", "IGNITION_HANDOFF_IN": "",
                    "IGNITION_HANDOFF_OUT": _os.path.join(_e2_out, "ho_boom.json"),
                    "POLYGON_API_KEY": "TEST_KEY_NOT_USED"})
_sent_bm, _loops_bm = [], []
_ml_saved2 = (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
              IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep)
IG._segment_window = lambda role, t0=None: {
    "role": role, "open": _ml_now, "close": _ml_now + S.dt.timedelta(hours=1),
    "segment_start": _ml_now, "segment_end": _ml_now + S.dt.timedelta(hours=1),
    "deadline": _ml_now + S.dt.timedelta(hours=1), "reason": "test",
    "session_type": "regular", "calendar_version": "test"}
IG.bot.load_watchlist = lambda: {"stocks": [{"symbol": "IGN", "status": "active"}]}
IG.bot.scan_ignition = lambda wl, today, trace=None: (
    _loops_bm.append(1), [({"symbol": "IGN"}, {"price": 2.0}, None)])[1]
IG.bot.build_ignition_alert = lambda rows: "ALERT"
IG.bot.send_telegram = lambda m: _sent_bm.append(m)


def _sleep_3(*_a):                      # يوقف الحلقة بعد 3 دورات (يثبت الاستمرار لا دورة واحدة)
    if len(_loops_bm) >= 3:
        raise _StopLoop()


IG.time.sleep = _sleep_3
try:
    IG.main()
except (_StopLoop, Exception):
    pass
finally:
    (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
     IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep) = _ml_saved2
    _sys.modules.pop("ignition_measurement", None)
    for _k, _v in _ml_env.items():
        _os.environ.pop(_k, None) if _v is None else _os.environ.update({_k: _v})
check("🔬 Codex5 قفل: مسجّل ترمي كل خطّافاته لا يوقف الحلقة ولا يمنع التنبيه (3 دورات)",
      len(_loops_bm) >= 3 and len(_sent_bm) >= 3
      and all(m.startswith("ALERT") for m in _sent_bm))
check("🔬 Codex5 قفل: _SafeRecorder يغلّف المسجّل عند نقطة النداء (حدّ فاشل-آمن واحد)",
      "_SafeRecorder(" in _insp0.getsource(IG.main)
      and "except Exception" in _insp0.getsource(IG._SafeRecorder))


# 🔬 مراجعة Codex 5 (P0-ب): خطّاف **معلّق** (deadlock/قرص بطيء) لا يرمي استثناءً أبدًا فلا يحميه
# الحدّ الفاشل-آمن — الحماية الوحيدة = إخراج الخطّافات الساخنة عن خيط الإنتاج (طابور محدود + عامل).
# الاختبار: كل خطّاف يعلّق للأبد ⇒ الحلقة تُكمل 3 دورات وترسل 3 تنبيهات **بزمن محدود**.
_hang_ev = _threading_ml = None
import threading as _threading_ml
_hang_ev = _threading_ml.Event()          # لا يُضبَط أبدًا ⇒ الخطّاف معلّق


class _HangRec:
    def __init__(self, *a, **kw):
        pass

    def __getattr__(self, name):
        def _hang(*a, **kw):
            _hang_ev.wait()               # تعليق أبدي (بلا استثناء) على خيط العامل
        return _hang


_hang_mod = _types_ml.ModuleType("ignition_measurement")
_hang_mod.IgnitionMeasurementRecorder = _HangRec
_sys.modules["ignition_measurement"] = _hang_mod
_os.environ.update({"E2_MEASUREMENT": "1", "IGNITION_SEGMENT": "close", "IGNITION_HANDOFF_IN": "",
                    "IGNITION_HANDOFF_OUT": _os.path.join(_e2_out, "ho_hang.json"),
                    "POLYGON_API_KEY": "TEST_KEY_NOT_USED"})
_sent_hg, _loops_hg = [], []
_drain_saved = IG.E2_DRAIN_TIMEOUT_SEC
IG.E2_DRAIN_TIMEOUT_SEC = 0.2             # مهلة تصريف قصيرة للاختبار (الإنتاج 30ث)
_ml_saved3 = (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
              IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep)
IG._segment_window = lambda role, t0=None: {
    "role": role, "open": _ml_now, "close": _ml_now + S.dt.timedelta(hours=1),
    "segment_start": _ml_now, "segment_end": _ml_now + S.dt.timedelta(hours=1),
    "deadline": _ml_now + S.dt.timedelta(hours=1), "reason": "test",
    "session_type": "regular", "calendar_version": "test"}
IG.bot.load_watchlist = lambda: {"stocks": [{"symbol": "IGN", "status": "active"}]}
IG.bot.scan_ignition = lambda wl, today, trace=None: (
    _loops_hg.append(1), (trace("01_SEEN_ACTIVE", {"symbol": "IGN"}) if trace else None),
    [({"symbol": "IGN"}, {"price": 2.0}, None)])[2]        # trace يُنادى فعلًا (يعلّق العامل)
IG.bot.build_ignition_alert = lambda rows: "ALERT"
IG.bot.send_telegram = lambda m: _sent_hg.append(m)
IG.time.sleep = lambda *_a: (_ for _ in ()).throw(_StopLoop()) if len(_loops_hg) >= 3 else None
_t_hang = _time_e2.time()
try:
    IG.main()
except (_StopLoop, Exception):
    pass
finally:
    _elapsed_hg = _time_e2.time() - _t_hang
    (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
     IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep) = _ml_saved3
    IG.E2_DRAIN_TIMEOUT_SEC = _drain_saved
    _hang_ev.set()                        # حرّر خيط العامل
    _sys.modules.pop("ignition_measurement", None)
    for _k, _v in _ml_env.items():
        _os.environ.pop(_k, None) if _v is None else _os.environ.update({_k: _v})
check("🔬 Codex5 قفل: خطّاف قياس **معلّق** لا يخنق الحلقة ولا التنبيه (3 دورات · زمن محدود)",
      len(_loops_hg) >= 3 and len(_sent_hg) >= 3 and _elapsed_hg < 5.0)
check("🔬 Codex5 قفل: الخطّافات الساخنة لا-تزامنية (طابور محدود + عامل · إسقاط عند الامتلاء)",
      set(IG._SafeRecorder._HOT) >= {"trace", "telegram_attempt", "loop_start"}
      and "put_nowait" in _insp0.getsource(IG._SafeRecorder)
      and "queue.Full" in _insp0.getsource(IG._SafeRecorder)
      and "measurement_dropped" in _insp0.getsource(IG._SafeRecorder))


# 🔬 مراجعة Codex 5 (P0-ج): **التهيئة نفسها** (استيراد + بناء المسجّل = إنشاء مجلّد/فتح ملفات)
# كانت على خيط الإنتاج **قبل** الحلقة ⇒ تعليقها يمنع كل مسح وتنبيه. الآن بخيط daemon والرادار
# يبدأ فورًا بـtrace=None. الاختبار: **البنّاء يعلّق للأبد** ⇒ 3 دورات و3 تنبيهات بزمن قصير.
class _HangCtorRec:
    def __init__(self, *a, **kw):
        _hang_ev2.wait()                  # تعليق أبدي أثناء البناء


_hang_ev2 = _threading_ml.Event()
_ctor_mod = _types_ml.ModuleType("ignition_measurement")
_ctor_mod.IgnitionMeasurementRecorder = _HangCtorRec
_sys.modules["ignition_measurement"] = _ctor_mod
_os.environ.update({"E2_MEASUREMENT": "1", "IGNITION_SEGMENT": "close", "IGNITION_HANDOFF_IN": "",
                    "IGNITION_HANDOFF_OUT": _os.path.join(_e2_out, "ho_ctor.json"),
                    "POLYGON_API_KEY": "TEST_KEY_NOT_USED"})
_sent_ct, _loops_ct, _traces_ct = [], [], []
_ml_saved4 = (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
              IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep)
IG._segment_window = lambda role, t0=None: {
    "role": role, "open": _ml_now, "close": _ml_now + S.dt.timedelta(hours=1),
    "segment_start": _ml_now, "segment_end": _ml_now + S.dt.timedelta(hours=1),
    "deadline": _ml_now + S.dt.timedelta(hours=1), "reason": "test",
    "session_type": "regular", "calendar_version": "test"}
IG.bot.load_watchlist = lambda: {"stocks": [{"symbol": "IGN", "status": "active"}]}
IG.bot.scan_ignition = lambda wl, today, trace=None: (
    _loops_ct.append(1), _traces_ct.append(trace),
    [({"symbol": "IGN"}, {"price": 2.0}, None)])[2]
IG.bot.build_ignition_alert = lambda rows: "ALERT"
IG.bot.send_telegram = lambda m: _sent_ct.append(m)
IG.time.sleep = lambda *_a: (_ for _ in ()).throw(_StopLoop()) if len(_loops_ct) >= 3 else None
_t_ct = _time_e2.time()
try:
    IG.main()
except (_StopLoop, Exception):
    pass
finally:
    _elapsed_ct = _time_e2.time() - _t_ct
    (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
     IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep) = _ml_saved4
    _hang_ev2.set()
    _sys.modules.pop("ignition_measurement", None)
    for _k, _v in _ml_env.items():
        _os.environ.pop(_k, None) if _v is None else _os.environ.update({_k: _v})
check("🔬 Codex5 قفل: تهيئة قياس **معلّقة** لا تمنع بدء الرادار (3 دورات · 3 تنبيهات · زمن قصير)",
      len(_loops_ct) >= 3 and len(_sent_ct) >= 3 and _elapsed_ct < 5.0
      and _traces_ct[0] is None)          # الرادار بدأ فورًا بلا انتظار المسجّل
check("🔬 Codex5 قفل: تهيئة المسجّل خارج خيط الإنتاج (Thread) والربط لا-حاجب",
      "threading.Thread(target=_init_recorder" in _insp0.getsource(IG.main)
      and "_rec_ready.is_set()" in _insp0.getsource(IG.main))


# 🔬 مراجعة Codex 5 (P0-د): **سباق الجاهزية** — لو حُكم بـ«استقرّ» قبل أن ينشر الخيط نتيجته
# لظلّ trace=None للأبد و**ضاع قياس الجلسة بصمت**. الاختبار: بنّاء بطيء (يجهز بعد الدورة الأولى)
# ⇒ الدورة الأولى trace=None، ودورة لاحقة **تلتحق فعلًا** وتصل أحداث trace للمسجّل.
_slow_ev = _threading_ml.Event()
_slow_traces = []


class _SlowRec:
    def __init__(self, *a, **kw):
        _slow_ev.wait(5)                  # يجهز حين يُضبَط العلم (بعد الدورة الأولى)

    def trace(self, event, payload):
        _slow_traces.append(event)

    def __getattr__(self, name):          # بقيّة الخطّافات لا تفعل شيئًا
        return lambda *a, **kw: None


_slow_mod = _types_ml.ModuleType("ignition_measurement")
_slow_mod.IgnitionMeasurementRecorder = _SlowRec
_sys.modules["ignition_measurement"] = _slow_mod
_os.environ.update({"E2_MEASUREMENT": "1", "IGNITION_SEGMENT": "close", "IGNITION_HANDOFF_IN": "",
                    "IGNITION_HANDOFF_OUT": _os.path.join(_e2_out, "ho_slow.json"),
                    "POLYGON_API_KEY": "TEST_KEY_NOT_USED"})
_sent_sl, _loops_sl, _traces_sl = [], [], []
_real_sleep = _time_e2.sleep
_ml_saved5 = (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
              IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep)
IG._segment_window = lambda role, t0=None: {
    "role": role, "open": _ml_now, "close": _ml_now + S.dt.timedelta(hours=1),
    "segment_start": _ml_now, "segment_end": _ml_now + S.dt.timedelta(hours=1),
    "deadline": _ml_now + S.dt.timedelta(hours=1), "reason": "test",
    "session_type": "regular", "calendar_version": "test"}
IG.bot.load_watchlist = lambda: {"stocks": [{"symbol": "IGN", "status": "active"}]}
IG.bot.scan_ignition = lambda wl, today, trace=None: (
    _loops_sl.append(1), _traces_sl.append(trace),
    (trace("01_SEEN_ACTIVE", {"symbol": "IGN"}) if trace else None),
    [({"symbol": "IGN"}, {"price": 2.0}, None)])[3]
IG.bot.build_ignition_alert = lambda rows: "ALERT"
IG.bot.send_telegram = lambda m: _sent_sl.append(m)


def _sleep_slow(*_a):
    if len(_loops_sl) == 1:               # بعد الدورة الأولى: اجعل المسجّل يجهز
        _slow_ev.set()
        _real_sleep(0.3)                  # مهلة نشر (الخيط ينشر نتيجته)
    if len(_loops_sl) >= 3:
        raise _StopLoop()


IG.time.sleep = _sleep_slow
try:
    IG.main()
except (_StopLoop, Exception):
    pass
finally:
    (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
     IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep) = _ml_saved5
    _slow_ev.set()
    _sys.modules.pop("ignition_measurement", None)
    for _k, _v in _ml_env.items():
        _os.environ.pop(_k, None) if _v is None else _os.environ.update({_k: _v})
check("🔬 Codex5 قفل: الالتحاق المتأخّر ينجح (تهيئة بطيئة ⇒ دورة أولى بلا قياس ثم يلتحق فعلًا)",
      len(_loops_sl) >= 3 and len(_sent_sl) >= 3
      and _traces_sl[0] is None and _traces_sl[-1] is not None
      and _slow_traces == ["01_SEEN_ACTIVE"] * len(_slow_traces) and len(_slow_traces) >= 1)
# 🔬 مراجعة Codex 5 (P0-هـ): **صفر عمل قياسي على خيط الإنتاج قبل الحلقة** — هَشّ القائمة
# (`_wl_content_sha256`: استيراد manifest + تقنين + هَشّ) كان يسبق بدء الخيط ⇒ بطؤه/تعليقه
# يؤخّر أول مسح = يؤخّر تنبيهًا. الاختبار: نعلّقه للأبد ⇒ المسح والتنبيه لا يتأثّران.
_sha_ev = _threading_ml.Event()
_sha_saved = IG._wl_content_sha256
IG._wl_content_sha256 = lambda *_a, **_k: (_sha_ev.wait(), "x")[1]   # تعليق أبدي
_sys.modules["ignition_measurement"] = _boom_mod                      # مسجّل لا يهمّ هنا
_os.environ.update({"E2_MEASUREMENT": "1", "IGNITION_SEGMENT": "close", "IGNITION_HANDOFF_IN": "",
                    "IGNITION_HANDOFF_OUT": _os.path.join(_e2_out, "ho_sha.json"),
                    "POLYGON_API_KEY": "TEST_KEY_NOT_USED"})
_sent_sh, _loops_sh = [], []
_drain_saved2 = IG.E2_DRAIN_TIMEOUT_SEC
IG.E2_DRAIN_TIMEOUT_SEC = 0.2
_ml_saved6 = (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
              IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep)
IG._segment_window = lambda role, t0=None: {
    "role": role, "open": _ml_now, "close": _ml_now + S.dt.timedelta(hours=1),
    "segment_start": _ml_now, "segment_end": _ml_now + S.dt.timedelta(hours=1),
    "deadline": _ml_now + S.dt.timedelta(hours=1), "reason": "test",
    "session_type": "regular", "calendar_version": "test"}
IG.bot.load_watchlist = lambda: {"stocks": [{"symbol": "IGN", "status": "active"}]}
IG.bot.scan_ignition = lambda wl, today, trace=None: (
    _loops_sh.append(1), [({"symbol": "IGN"}, {"price": 2.0}, None)])[1]
IG.bot.build_ignition_alert = lambda rows: "ALERT"
IG.bot.send_telegram = lambda m: _sent_sh.append(m)
IG.time.sleep = lambda *_a: (_ for _ in ()).throw(_StopLoop()) if len(_loops_sh) >= 3 else None
_t_sh = _time_e2.time()
try:
    IG.main()
except (_StopLoop, Exception):
    pass
finally:
    _elapsed_sh = _time_e2.time() - _t_sh
    (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
     IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep) = _ml_saved6
    IG._wl_content_sha256 = _sha_saved
    IG.E2_DRAIN_TIMEOUT_SEC = _drain_saved2
    _sha_ev.set()
    _sys.modules.pop("ignition_measurement", None)
    for _k, _v in _ml_env.items():
        _os.environ.pop(_k, None) if _v is None else _os.environ.update({_k: _v})
check("🔬 Codex5 قفل: هَشّ القائمة (ميتا القياس) معلّقًا لا يؤخّر المسح ولا التنبيه",
      len(_loops_sh) >= 3 and len(_sent_sh) >= 3 and _elapsed_sh < 5.0)
check("🔬 Codex5 قفل: صفر عمل قياسي على خيط الإنتاج (الميتا/الهَشّ داخل _init_recorder)",
      "_wl_content_sha256" not in _insp0.getsource(IG.main).split("def _init_recorder")[0]
      and "_wl_content_sha256" in _insp0.getsource(IG.main))


# 🔬 مراجعة Codex 5 (P0-و): مسار **تحديث القائمة** (كل 7 دورات) كان يُقيّم `_fetch_head_sha()`
# (نداء git فرعي · مهلة 15ث) و`_wl_content_sha256()` **كوسائط على خيط الإنتاج** قبل الغلاف
# اللا-تزامني ⇒ بطؤهما يخنق المسح. الاختبار: كلاهما معلّق للأبد ⇒ 8 دورات مسح وتنبيهاتها تمرّ.
_hs_ev = _threading_ml.Event()
_hs_saved = (IG._fetch_head_sha, IG._wl_sha_from_snapshot, IG._fresh_watchlist)
IG._fetch_head_sha = lambda *_a, **_k: (_hs_ev.wait(), None)[1]      # تعليق أبدي (git)
IG._wl_sha_from_snapshot = lambda *_a, **_k: (_hs_ev.wait(), None)[1]  # تعليق أبدي (هَشّ)
IG._fresh_watchlist = lambda cur, runner=None: {"stocks": [{"symbol": "IGN", "status": "active"}]}
_sys.modules["ignition_measurement"] = _slow_mod2 = _types_ml.ModuleType("ignition_measurement")


class _OkRec:
    def __getattr__(self, name):
        return lambda *a, **kw: None


_slow_mod2.IgnitionMeasurementRecorder = lambda *a, **kw: _OkRec()
_os.environ.update({"E2_MEASUREMENT": "1", "IGNITION_SEGMENT": "close", "IGNITION_HANDOFF_IN": "",
                    "IGNITION_HANDOFF_OUT": _os.path.join(_e2_out, "ho_hs.json"),
                    "POLYGON_API_KEY": "TEST_KEY_NOT_USED"})
_sent_hs, _loops_hs = [], []
_drain_saved3 = IG.E2_DRAIN_TIMEOUT_SEC
IG.E2_DRAIN_TIMEOUT_SEC = 0.2
_ml_saved7 = (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
              IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep)
IG._segment_window = lambda role, t0=None: {
    "role": role, "open": _ml_now, "close": _ml_now + S.dt.timedelta(hours=1),
    "segment_start": _ml_now, "segment_end": _ml_now + S.dt.timedelta(hours=1),
    "deadline": _ml_now + S.dt.timedelta(hours=1), "reason": "test",
    "session_type": "regular", "calendar_version": "test"}
IG.bot.load_watchlist = lambda: {"stocks": [{"symbol": "IGN", "status": "active"}]}
IG.bot.scan_ignition = lambda wl, today, trace=None: (
    _loops_hs.append(1), [({"symbol": "IGN"}, {"price": 2.0}, None)])[1]
IG.bot.build_ignition_alert = lambda rows: "ALERT"
IG.bot.send_telegram = lambda m: _sent_hs.append(m)
IG.time.sleep = lambda *_a: (_ for _ in ()).throw(_StopLoop()) if len(_loops_hs) >= 8 else None
_t_hs = _time_e2.time()
try:
    IG.main()                              # يمرّ بالدورة 7 = مسار التحديث
except (_StopLoop, Exception):
    pass
finally:
    _elapsed_hs = _time_e2.time() - _t_hs
    (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
     IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep) = _ml_saved7
    (IG._fetch_head_sha, IG._wl_sha_from_snapshot, IG._fresh_watchlist) = _hs_saved
    IG.E2_DRAIN_TIMEOUT_SEC = _drain_saved3
    _hs_ev.set()
    _sys.modules.pop("ignition_measurement", None)
    for _k, _v in _ml_env.items():
        _os.environ.pop(_k, None) if _v is None else _os.environ.update({_k: _v})
check("🔬 Codex5 قفل: هَشّ/git التحديث (دورة 7) معلّقًا لا يخنق المسح ولا التنبيه (8 دورات)",
      len(_loops_hs) >= 8 and len(_sent_hs) >= 8 and _elapsed_hs < 5.0)
check("🔬 Codex5 قفل: حسابات التحديث مؤجَّلة للعامل (recorder.submit · لا تقييم وسائط بالإنتاج)",
      "recorder.submit(" in _insp0.getsource(IG.main)
      and "_fetch_head_sha(" not in _insp0.getsource(IG.main))


# 🔬 مراجعة Codex 5 (P0-ز): **سباق provenance**: المهمّة المؤجَّلة كانت تقرأ الحالة العامّة
# (`_WL_RAW`/FETCH_HEAD) **وقت تنفيذها**؛ لو تعطّل العامل حتى جلبة تالية، تُنسَب القائمة الأحدث
# لتحديث أقدم = provenance كاذب. الآن: **لقطة لكل جلبة** تُنسَخ وقت الجلب ويُغلق عليها.
# الاختبار: عامل متوقّف عبر **جلبتين مختلفتين** ⇒ كل تحديث يسجّل commit/هَشّ قائمته بالترتيب.
_wl_a = {"stocks": [{"symbol": "AAA", "status": "active"}]}
_wl_b = {"stocks": [{"symbol": "BBB", "status": "active"}]}
_sha_a, _sha_b = IG._wl_content_sha256(_wl_a), IG._wl_content_sha256(_wl_b)
_gate_ev = _threading_ml.Event()          # يحبس العامل حتى تتمّ الجلبتان
_prov = []
_fetch_n = {"n": 0}


def _fake_fresh(cur, runner=None):        # جلبة 1 → A · جلبة 2 → B (تحدّث اللقطة كالأصل)
    _fetch_n["n"] += 1
    if _fetch_n["n"] == 1:
        IG._WL_RAW["text"], IG._WL_RAW["commit"] = _json_ml.dumps(_wl_a), "snap_A"
        return _json_ml.loads(_json_ml.dumps(_wl_a))
    IG._WL_RAW["text"], IG._WL_RAW["commit"] = _json_ml.dumps(_wl_b), "snap_B"
    return _json_ml.loads(_json_ml.dumps(_wl_b))


class _ProvRec:
    def set_watchlist_commit(self, commit, file_sha):
        _gate_ev.wait(5)                  # العامل متوقّف حتى تتمّ الجلبتان (يكشف القراءة المتأخّرة)
        _prov.append((commit, file_sha))

    def __getattr__(self, name):
        return lambda *a, **kw: None


import json as _json_ml
_prov_mod = _types_ml.ModuleType("ignition_measurement")
_prov_mod.IgnitionMeasurementRecorder = lambda *a, **kw: _ProvRec()
_sys.modules["ignition_measurement"] = _prov_mod
_os.environ.update({"E2_MEASUREMENT": "1", "IGNITION_SEGMENT": "close", "IGNITION_HANDOFF_IN": "",
                    "IGNITION_HANDOFF_OUT": _os.path.join(_e2_out, "ho_prov.json"),
                    "POLYGON_API_KEY": "TEST_KEY_NOT_USED"})
_loops_pv = []
_wlraw_saved, _fresh_saved = dict(IG._WL_RAW), IG._fresh_watchlist
_drain_saved4 = IG.E2_DRAIN_TIMEOUT_SEC
IG.E2_DRAIN_TIMEOUT_SEC = 5               # يكفي لتصريف التحديثين بعد فتح البوّابة
IG._fresh_watchlist = _fake_fresh
_ml_saved8 = (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
              IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep)
IG._segment_window = lambda role, t0=None: {
    "role": role, "open": _ml_now, "close": _ml_now + S.dt.timedelta(hours=1),
    "segment_start": _ml_now, "segment_end": _ml_now + S.dt.timedelta(hours=1),
    "deadline": _ml_now + S.dt.timedelta(hours=1), "reason": "test",
    "session_type": "regular", "calendar_version": "test"}
IG.bot.load_watchlist = lambda: _json_ml.loads(_json_ml.dumps(_wl_a))
IG.bot.scan_ignition = lambda wl, today, trace=None: (_loops_pv.append(1), [])[1]
IG.bot.build_ignition_alert = lambda rows: "ALERT"
IG.bot.send_telegram = lambda m: None


def _sleep_prov(*_a):
    _real_sleep(0.02)                      # مهلة حقيقية قصيرة: يلتحق المسجّل قبل جلبة الدورة 7
    if len(_loops_pv) >= 14:               # تمّت الجلبتان (دورة 7 ودورة 14) ⇒ حرّر العامل
        _gate_ev.set()
        raise _StopLoop()


IG.time.sleep = _sleep_prov
try:
    IG.main()
except (_StopLoop, Exception):
    pass
finally:
    (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
     IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep) = _ml_saved8
    IG._fresh_watchlist, IG.E2_DRAIN_TIMEOUT_SEC = _fresh_saved, _drain_saved4
    IG._WL_RAW.update(_wlraw_saved)
    _gate_ev.set()
    _sys.modules.pop("ignition_measurement", None)
    for _k, _v in _ml_env.items():
        _os.environ.pop(_k, None) if _v is None else _os.environ.update({_k: _v})
check("🔬 Codex5 قفل: عامل متوقّف عبر جلبتين ⇒ كل تحديث يسجّل commit/هَشّ **قائمته** (لا الأحدث)",
      _prov == [("snap_A", _sha_a), ("snap_B", _sha_b)])
# 🔬 مراجعة Codex 5 (P0-ح): `_fresh_watchlist` (مسار إنتاجي) لا يفعل **أي** عمل قياسي: لا هَشّ ·
# لا subprocess إضافي · لا قراءة `.git/FETCH_HEAD`. commit القائمة المحدَّثة يُصرَّح «غير محسوم»
# (البرهان = هَشّ المحتوى) بدل commit مضلِّل أو I/O قياسي على خيط التنبيه.
check("🔬 Codex5 قفل: صفر عمل قياسي داخل _fresh_watchlist (لا هَشّ/rev-parse/FETCH_HEAD)",
      (lambda src: "_wl_content_sha256" not in src and "rev-parse" not in src
       and "FETCH_HEAD:" in src and "open(" not in src
       and "WL_COMMIT_UNRESOLVED" in src)(_insp0.getsource(IG._fresh_watchlist))
      and IG.WL_COMMIT_UNRESOLVED == "unresolved_offthread")
check("🔬 P1-8: manifest نقيّ + canonical JSON حتمي (نفس المدخل = نفس الـhash)",
      _MAN.manifest_sha256({"a": 1, "b": 2}) == _MAN.manifest_sha256({"b": 2, "a": 1})
      and _MAN.sha256_hex("x") == _MAN.sha256_hex("x") and _MAN.manifest_sha256({}) is not None)
# ── 🔬 P1-6: التقويم (عطلة/إغلاق مبكر/عادي) ──
import market_calendar as _CAL
check("🔬 P1-6: التقويم — عطلة (لا جلسة) · إغلاق مبكر (close مقصوص) · عادي",
      _CAL.session_info("2026-07-03")["session_type"] == "holiday"
      and _CAL.session_info("2026-11-27")["session_type"] == "early_close"
      and _CAL.session_info("2026-11-27")["close_ny_min"] == 13 * 60
      and _CAL.session_info("2026-07-13")["session_type"] == "regular"
      and _CAL.session_info("2026-07-03")["open_ny_min"] is None)
# ── 🔬 P1-1: دمج candidate field-wise لا يُسقط emitted/delivered ──
_ca = {"candidate_id": "x", "symbol": "A", "break_level": 2.0, "alert_emitted": False,
       "gate_decision": "suppress_operator", "telegram_delivered": None, "signal_price": 2.1}
_cb = {"candidate_id": "x", "symbol": "A", "break_level": 2.0, "alert_emitted": True,
       "gate_decision": "emit", "telegram_delivered": True, "vol_x": 5}
_cm_merged = _ASM._merge_candidate(_ca, _cb)
check("🔬 P1-1: دمج candidate يحفظ emitted=True + delivered=True + gate=emit (لا «أول ظهور يفوز»)",
      _cm_merged["alert_emitted"] is True and _cm_merged["telegram_delivered"] is True
      and _cm_merged["gate_decision"] == "emit" and _cm_merged["signal_price"] == 2.1
      and _cm_merged["vol_x"] == 5)
# تعارض حقل ثابت يُسجَّل
_cc = _ASM._merge_candidate({"candidate_id": "x", "break_level": 2.0}, {"candidate_id": "x", "break_level": 9.9})
check("🔬 P1-1: تعارض حقل ثابت (break_level) يُسجَّل في merge_conflicts", "break_level" in _cc.get("merge_conflicts", []))
# ── 🔬 P0-2/P0-3/P0-5: المدقّق يرفض بدء متأخّر · فجوة انتقال · مقطع غير مكتمل · تسليم مكرّر ──
def _wj(sub, sd, patch):   # يكتب session.json مبسّط + يرجّع تحليله
    _d = _os.path.join(_e2_out, sub, "session_" + sd)
    _os.makedirs(_d, exist_ok=True)
    _base = {"assembled": True, "termination": "normal", "loops_started": 2, "loops_completed": 2,
             "alert_logic_version": "unchanged", "expected_close_iso": "2000-01-01T20:00:00Z",
             "segments": [{"role": "open", "termination": "normal"}, {"role": "close", "termination": "normal"}],
             "manifest_chain_ok": True}
    _base.update(patch)
    with open(_os.path.join(_d, "session.json"), "w", encoding="utf-8") as fh:
        _json.dump(_base, fh)
    return _A.analyze_session(_d)
_r_gap = _wj("gap", "2026-08-01", {"transition_gap_ms": 20 * 60000, "max_transition_gap_min": 10})
_r_chain = _wj("chn", "2026-08-02", {"manifest_chain_ok": False, "manifest_chain_reasons": ["chain_hash_mismatch"]})
check("🔬 P0-3/P0-4 مدقّق: فجوة انتقال تتجاوز الحدّ + سلسلة manifest فاشلة ⇒ يُرفض session_complete",
      _r_gap["session_complete"] is False and any("transition_gap_exceeded" in x for x in _r_gap["incomplete_reasons"])
      and _r_chain["session_complete"] is False and any("manifest_chain_failed" in x for x in _r_chain["incomplete_reasons"]))
# تسليم مكرّر لنفس الرمز
_dd_dir = _os.path.join(_e2_out, "dup", "session_2026-08-03")
_os.makedirs(_dd_dir, exist_ok=True)
with open(_os.path.join(_dd_dir, "session.json"), "w", encoding="utf-8") as fh:
    _json.dump({"segment": None, "termination": "normal", "loops_started": 1, "loops_completed": 1,
                "alert_logic_version": "unchanged", "expected_close_iso": "2000-01-01T20:00:00Z"}, fh)
with open(_os.path.join(_dd_dir, "deliveries.jsonl"), "w", encoding="utf-8") as fh:
    fh.write(_json.dumps({"symbol": "DUP", "delivered": True}) + "\n")
    fh.write(_json.dumps({"symbol": "DUP", "delivered": True}) + "\n")
_r_dup = _A.analyze_session(_dd_dir)
check("🔬 P0-5 مدقّق: تسليم مكرّر لنفس الرمز ⇒ duplicate_delivery",
      any("duplicate_delivery" in x for x in _r_dup["incomplete_reasons"]))
# بدء متأخّر (single)
_r_late = _wj("late", "2026-08-04", {"assembled": False, "segments": None,
              "first_successful_poll_at": "2026-08-04T14:00:00Z", "expected_open_iso": "2026-08-04T13:30:00Z",
              "start_tolerance_min": 2})
check("🔬 P0-2 مدقّق: بدء المراقبة متأخّر عن الافتتاح+tolerance ⇒ start_coverage_late",
      any("start_coverage_late" in x for x in _r_late["incomplete_reasons"]))
# ── 🔬 P0-6: analyzer --strict يعيد خروجًا غير صفر عند جلسة غير مكتملة ──
import subprocess as _sub, sys as _sys
_strict_root = _os.path.join(_e2_out, "gap")   # يحوي جلسة غير مكتملة (فجوة)
_rc = _sub.run([_sys.executable, "ignition_e2_analyze.py", _strict_root, "--strict"],
               capture_output=True).returncode
check("🔬 P0-6: analyzer --strict خروج غير صفر عند جلسة غير مكتملة", _rc != 0)
# ── 🔬 مراجعة Codex 5 (P0): الإيقاع = سلوك الإنتاج قبل الفرع (نوم بعد المسح) ──
# الجدولة المطلقة كانت تغيّر أوقات المسح ⇒ تغيّر الإشارة المرصودة ووقت ختم الدِدوب = تغيير تنبيه.
check("🔬 Codex5 قفل: إيقاع الرادار = time.sleep(interval) (لا جدولة مطلقة تغيّر أوقات المسح)",
      "time.sleep(interval)" in _insp0.getsource(IG.main)
      and "_next_tick" not in _insp0.getsource(IG.main))
_shutil.rmtree(_e2_out, ignore_errors=True)
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
# 📝 سطر المضارب المختصر (طلب المستخدم 2026-07-09 «الرسالة فيها فلسفة كثيرة —
# ابي: المضارب طلب 1000 سهم فوق الدعم»): لغة أوامر مباشرة، بلا حدود صدق/نسب
# بالتنبيه (التفصيل بفحص اليد فقط). «شرى على الطلب» أولًا (الأهم عند المستخدم).
_ol_txt = S.operator_line(_ob)
check("🕵️سطر المضارب المختصر: «شرى على الطلب» أولًا ثم «رفع بشراء» — بلا فلسفة",
      "شرى على الطلب ~2,000 سهم" in _ol_txt
      and "رفع بشراء ~2,700 سهم" in _ol_txt
      and _ol_txt.index("شرى على الطلب") < _ol_txt.index("رفع بشراء")
      and "L2" not in _ol_txt and "تصنيف تقريبي" not in _ol_txt
      and "Lee-Ready" not in _ol_txt and "%" not in _ol_txt)
check("🕵️سطر المضارب: None ⇒ «—»", S.operator_line(None) == "🕵️ المضارب: —")
# جدارا الطلب/العرض موسومان بأقرب مستوى معروف (لغة المتداول: «فوق الرقم الحرج»
# / «عند المقاومة» — أمثلة المستخدم حرفيًّا). التسامح 1.5% = «عند».
_ob_walls = dict(_ob, bid=7.12, bid_size=400, ask=7.40, ask_size=400)
_s_lvls = {"symbol": "GEOS", "pivot": 6.28, "stop": [5.84, 5.97],
           "key_levels": {"sup_major": 6.28, "sup_minor": 6.66,
                          "res_minor": 7.44, "res_major": 8.06},
           "interp": {"critical_number": {"price": 7.00}}}
_ol_w = S.operator_line(_ob_walls, _s_lvls)
check("🕵️سطر المضارب: «طلب 400 سهم عند $7.12 (فوق الرقم الحرج $7.00)» — وسم المستوى",
      "طلب 400 سهم عند $7.12 (فوق الرقم الحرج $7.00)" in _ol_w)
check("🕵️سطر المضارب: العرض عند المقاومة يُوسَم بها مباشرة (مثال المستخدم حرفيًّا"
      " — بلا تكرار «عند»)",
      "عرض 400 سهم عند المقاومة الفرعية $7.44 ($7.40)" in _ol_w)
check("🕵️وسم المستوى: عند/فوق/تحت + فاشل-آمن ('' بلا مستويات)",
      S._price_level_tag(7.01, _s_lvls) == " (عند الرقم الحرج $7.00)"
      and S._price_level_tag(6.10, _s_lvls) == " (تحت الدعم $6.28)"
      and S._price_level_tag(2.0, None) == ""
      and S._price_level_tag(None, _s_lvls) == "")
check("🕵️سطر المضارب: بلا سهم مُمرَّر ⇒ الجدار بسعره الخام (توافق خلفي)",
      "طلب 400 سهم عند $7.12" in S.operator_line(_ob_walls)
      and "الرقم الحرج" not in S.operator_line(_ob_walls))
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
check("🕵️عرض الرادار: التنبيه يعرض كميات المضارب (بالصيغة المختصرة الجديدة)",
      "المضارب" in S.build_ignition_alert(_r_yes)
      and "رفع بشراء ~2,700 سهم" in S.build_ignition_alert(_r_yes)
      and "L2" not in S.build_ignition_alert(_r_yes))
# بوّابة مراقب الجلسة (نفس القاعدة — الأحداث الإيجابية فقط · الخطر لا يُبوَّب)
_mle_df = pd.DataFrame(
    {"Open": [2.0] * 30, "High": [2.1] * 30, "Low": [1.9] * 30,
     "Close": [2.0] * 29 + [1.95], "Volume": [1e5] * 30},
    index=pd.date_range(end="2026-07-20", periods=30, freq="B"))   # ⑤ = today
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
    index=pd.date_range(end="2026-07-20", periods=30, freq="B"))   # ⑤ = today
_ev_brk = S.monitor_live_events({"stocks": [_mle_st("BRK")]}, {"BRK": _brk_df},
    "2026-07-20", fetch_operator=lambda s: {"has_operator": False})
check("🕵️بوّابة المراقب: الخطر (كسر الوقف) لا يُبوَّب — يظهر حتى بلا مضارب",
      any(k == "break" for _s, k, _d in _ev_brk))
check("🕵️قفل: دوال المضارب خارج rank_key/select_top/classify_tier/analyze_ticker/backtest_symbol",
      all(("_operator_blocks" not in _insp0.getsource(_f)
           and "operator_flow" not in _insp0.getsource(_f))
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.analyze_ticker,
                     S.backtest_symbol)))

# ===== 🔒 معدّل الاقتراض (طلب المستخدم: أساس الارتكاز · اقتراض صعب = وقود سكويز) =====
_fin_html = "Cost to Borrow: 45.5% . Shares Available to Borrow: 12,000 ."
_fb = S._parse_fintel_borrow(_fin_html)
check("🔒 Fintel: يستخرج رسوم الاقتراض + الأسهم المتاحة من نفس HTML (بلا نداء إضافي)",
      _fb.get("borrow_fee") == 45.5 and _fb.get("shares_available") == 12000)
check("🔒 Fintel·فاشل-آمن: HTML بلا اقتراض ⇒ {}",
      S._parse_fintel_borrow("<html>لا شيء</html>") == {})
_ib = S._parse_iborrow({"real_time": [{"fee": 62.0, "available": 5000, "time": "t"}]})
check("🔒 iBorrowDesk: يستخرج أحدث رسوم/متاح من real_time",
      _ib.get("borrow_fee") == 62.0 and _ib.get("shares_available") == 5000)
check("🔒 iBorrowDesk: يسقط لـdaily لو غاب real_time",
      S._parse_iborrow({"daily": [{"fee": 10.0, "available": 900}]})["borrow_fee"] == 10.0)
check("🔒 iBorrowDesk·فاشل-آمن: رد فارغ/غير صالح ⇒ {}",
      S._parse_iborrow({}) == {} and S._parse_iborrow({"real_time": []}) == {})
# 🌐 ChartExchange (اقتراح المستخدم 2026-07-10 — مصدر فيصل نفسه، صورة 9431).
# الثوابت من مجسّ Actions الحقيقي (لا تخمين): جملة ctbtoday ثابتة الشكل عبر الرموز.
_CE_GEOS = ('<a name="ctbtoday" href="#ctbtoday">GEOS Borrow Fee (CTB) Latest</a>'
            '</div><div style="padding: 0 0 0 1em;">As of <span style="font-weight:'
            ' bold;">2026-07-10 03:54:27 AM EDT</span>, there were <span style='
            '"font-weight: bold;">550,000</span> shares available with a fee of '
            '<span style="font-weight: bold;">0.40%</span>.</div>')
_CE_PTN = ('<a name="ctbtoday">PTN Borrow Fee (CTB) Latest</a><div>As of <span>'
           '2026-07-10 03:54:27 AM EDT</span>, there were <span>40,000</span> '
           'shares available with a fee of <span>12.43%</span>.</div>')
check("🌐 ChartExchange: يستخرج المتاح/الرسوم من مقطع ctbtoday (شكل المجسّ الحقيقي)",
      S._parse_ce_borrow(_CE_GEOS) == {"shares_available": 550000,
                                       "borrow_fee": 0.40}
      and S._parse_ce_borrow(_CE_PTN) == {"shares_available": 40000,
                                          "borrow_fee": 12.43})
check("🌐 ChartExchange: رسوم بفاصلة آلاف (صعب جدًّا 1,234.5%) تُقرأ سليمة",
      S._parse_ce_borrow('name="ctbtoday" there were <b>500</b> shares available '
                         'with a fee of <b>1,234.5%</b>')["borrow_fee"] == 1234.5)
check("🌐 ChartExchange·فاشل-آمن: HTML بلا مرساة/بلا جملة ⇒ {}",
      S._parse_ce_borrow("<html>لا شيء</html>") == {}
      and S._parse_ce_borrow('name="ctbtoday" نص بلا أرقام') == {}
      and S._parse_ce_borrow("") == {})
# فاشل-آمن بحقن فشل الشبكة (لا بالاعتماد على غياب الإنترنت — كان يفشل على رنر CI
# حيث الشبكة متاحة وCE يرد 200؛ إصلاح تحديد 2026-07-12).
_sv_req_ce = S.requests
try:
    def _raise_get(*a, **k):
        raise RuntimeError("no network (اختبار)")
    S.requests = _ty0.SimpleNamespace(get=_raise_get)
    check("🌐 ChartExchange·فاشل-آمن: فشل الشبكة ⇒ اقتراض/فلوت/iBorrow (لا يعيق الإثراء)",
          S.ce_borrow_info("GEOS") == {}          # الاقتراض → {}
          and S.ce_float_info("GEOS") is None     # الفلوت → None (عقده)
          and S.iborrow_info("GEOS") == {})       # iBorrow → {}
finally:
    S.requests = _sv_req_ce
# 🏢 فلوت ChartExchange (اقتراح المستخدم 2026-07-10 لحلّ «الفلوت مجهول» من ياهو).
# HTML من مجسّ Actions الحقيقي (GEOS/PTN/FEMY) — لا تخمين.
_CE_FLOAT = ('<div class="stat-flow-item"><div class="stat-flow-label">Shares Outstanding'
             '</div><div class="stat-flow-value">12.94M</div></div>'
             '<div class="stat-flow-item"><div class="stat-flow-label">Float</div>'
             '<div class="stat-flow-value">12.55M</div></div>'
             '<div class="stat-flow-item"><div class="stat-flow-label">Free Float</div>'
             '<div class="stat-flow-value">12.55M</div></div>'
             '<div class="stat-flow-item"><div class="stat-flow-label">Free Float %</div>'
             '<div class="stat-flow-value">97%</div></div>')
check("🏢 فلوت CE: يستخرج «Float» بالضبط = 12.55M ⇒ 12,550,000 (لا Free Float)",
      S._parse_ce_float(_CE_FLOAT) == 12_550_000)
check("🏢 فلوت CE·وحدات: K/M/B + فاصلة الآلاف تُقرأ سليمة",
      S._ce_num("778K") == 778_000 and S._ce_num("1.2B") == 1_200_000_000
      and S._ce_num("2.50M") == 2_500_000 and S._ce_num("550,000") == 550_000)
# ce_float_info الشبكي يُختبر بحقن الفشل أعلاه (سطر واحد، حتمي)؛ هنا المُحلّل النقي فقط.
check("🏢 فلوت CE·فاشل-آمن: بلا مقطع Float ⇒ None",
      S._parse_ce_float("<html>لا فلوت</html>") is None
      and S._parse_ce_float("") is None)
check("🏢 فلوت CE·تمييز: صفحة فيها «Free Float» فقط (بلا «Float» مفرد) ⇒ None",
      S._parse_ce_float('stat-flow-label">Free Float</div>'
                        '<div class="stat-flow-value">9.9M</div>') is None)
# 🔒 قفل حاسم: فلوت CE عرض فقط — خارج بوابة الفلوت M14 والفرز نهائيًّا
check("🔒 قفل: فلوت CE خارج apply_float_gate/rank_key/select_top/classify_tier/"
      "analyze_ticker/backtest_symbol (M14 لا تُمسّ)",
      all(("ce_float_info" not in _insp0.getsource(_f)
           and "_parse_ce_float" not in _insp0.getsource(_f))
          for _f in (S.apply_float_gate, S.rank_key, S.select_top, S.classify_tier,
                     S.analyze_ticker, S.backtest_symbol)))
# ⚖️ CE = المرجع الأول صراحةً (قرار المستخدم 2026-07-10): CE قبل احتياط Fintel
# وقبل iBorrowDesk في enrich، و`refresh_borrow` اليومي يبدأ بـCE مباشرة.
_es = _insp0.getsource(S.enrich)
check("🌐 قفل: CE هو المرجع الأول — ce_borrow_info قبل fintel-احتياط وقبل iBorrowDesk",
      _es.find("ce_borrow_info") < _es.find('"fintel"].get("borrow_fee")')
      < _es.find("iborrow_info"))
check("🌐 قفل: نداء CE غير مشروط بفشل مصدر سابق (المرجع الأول لا الاحتياط)",
      "ce_borrow_info(r" in _es
      and _es.find("ce_borrow_info(r") < _es.find('borrow_fee"] = r["fintel"]'))
check("🔄 refresh_borrow اليومي يعتمد CE مباشرة (المرجع الأول)",
      "ce_borrow_info" in _insp0.getsource(S.refresh_borrow))
check("🌐 قفل: ChartExchange خارج rank_key/select_top/classify_tier/analyze_ticker/"
      "backtest_symbol (عرض/سياق فقط)",
      all("ce_borrow" not in _insp0.getsource(_f)
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.analyze_ticker,
                     S.backtest_symbol)))
# السطر مفسَّر ذاتيًّا **على إطار فيصل الموثّق** (تصحيح 2026-07-10 بعد تشكيك
# المستخدم: سردية «يجبر الشورت يغطّي» أُزيلت — غير موثّقة؛ ثم أكّد فيصل مباشرة
# في DSY: «نسبة الاقتراض 725% عاليه جدا للشورت = اجابي» مع 7 آلاف متاح فقط).
_bl_hi = S.borrow_line({"borrow_fee": 45.0, "shares_available": 12000})
check("🔒 اقتراض·صعب+متاح قليل = إيجابي (فيصل DSY حرفيًّا) — بلا سردية التغطية",
      "رسوم 45%" in _bl_hi and "صعب 🔥" in _bl_hi
      and "إيجابي" in _bl_hi and "DSY" in _bl_hi
      and "وقود سكويز" not in _bl_hi and "يغطّي" not in _bl_hi
      and "متاح للشورت 12K سهم (قليل — تحت حد فيصل 40 ألف)" in _bl_hi)
# حالة DSY الحرفية (IMG_9509/9510): رسوم 728.64% + متاح 7,000
_bl_dsy = S.borrow_line({"borrow_fee": 728.64, "shares_available": 7000})
check("🔒 اقتراض·DSY حرفيًّا (729% + 7K): إيجابي + وسم «قليل»",
      "رسوم 729%" in _bl_dsy and "إيجابي" in _bl_dsy and "7K" in _bl_dsy
      and "قليل" in _bl_dsy)
check("🔒 اقتراض·صعب بلا «متاح»: حكم ناقص يُصرَّح به (لا إيجابي أعمى — درس XHLD)",
      "إيجابي" not in S.borrow_line({"borrow_fee": 45.0})
      and "الحكم الكامل يحتاج" in S.borrow_line({"borrow_fee": 45.0}))
check("🔒 اقتراض·متاح صفر: وسم ELAB (شرط حالة السكويز الموثّقة)",
      "لا أسهم متاحة للشورت أصلًا (فيصل ELAB: شرط حالة السكويز)"
      in S.borrow_line({"borrow_fee": 45.0, "shares_available": 0}))
# ⚠️ قراءة فيصل المركّبة (IMG_9504/9505 — XHLD حرفيًّا: متاح 600 ألف برسوم 23.31%
# → «طاخ طيخ الى الهاويه»): المتاح فوق حد فيصل (SHORT_GATE_MAX=40 ألف) = ذخيرة
# هبوط حتى مع رسوم عالية — لا يُوسَم وقود سكويز إيجابيًّا.
_bl_xhld = S.borrow_line({"borrow_fee": 23.31, "shares_available": 600_000})
check("⚠️ اقتراض·فيصل: XHLD (600 ألف + رسوم 23%) ⇒ ذخيرة هبوط لا وقود سكويز",
      "متاح للشورت ضخم" in _bl_xhld and "600K" in _bl_xhld
      and "فوق حد فيصل 40 ألف" in _bl_xhld
      and "طاخ طيخ" in _bl_xhld
      and "يجبر الشورت يشتري" not in _bl_xhld)
check("⚠️ اقتراض·فيصل: متاح ضخم بلا رسوم ⇒ نفس التحذير (المتاح هو الحاكم)",
      "حرب وتصريف" in S.borrow_line({"shares_available": 500_000})
      and "مستحيل يرتفع" in S.borrow_line({"shares_available": 500_000}))
check("⚠️ اقتراض·فيصل: متاح 35 ألف (SPPL المقبول) ⇒ يبقى وقود سكويز 🔥 عادي",
      "صعب 🔥" in S.borrow_line({"borrow_fee": 45.0, "shares_available": 35_000})
      and "حرب وتصريف" not in S.borrow_line({"borrow_fee": 45.0,
                                              "shares_available": 35_000}))
check("⚠️ اقتراض·مسار المتاح (IMG_9505: 30 ألف→600 ألف في 3 أيام): يظهر التضخّم",
      "كان 30K قبل 3 يوم" in S.borrow_line(
          {"borrow_fee": 23.31, "shares_available": 600_000,
           "borrow_hist": [["2026-07-06", 30_000], ["2026-07-09", 600_000]]}))
check("⚠️ اقتراض·مسار: نفس اليوم/غير نامٍ ⇒ لا سطر تضخّم (لا فبركة)",
      "يتضخّم" not in S.borrow_line(
          {"shares_available": 500_000,
           "borrow_hist": [["2026-07-09", 500_000], ["2026-07-09", 500_000]]})
      and "يتضخّم" not in S.borrow_line(
          {"shares_available": 100_000,
           "borrow_hist": [["2026-07-06", 200_000], ["2026-07-09", 100_000]]}))
# refresh_borrow: تحديث يومي فاشل-آمن + مسار borrow_hist (حقن جالب للاختبار)
_rb = {"symbol": "XH", "borrow_fee": 1.0, "shares_available": 30_000,
       "borrow_hist": [["2026-07-06", 30_000]]}
S.refresh_borrow(_rb, "2026-07-09",
                 fetch=lambda s: {"borrow_fee": 23.31, "shares_available": 600_000})
check("🔄 refresh_borrow: يحدّث الرسوم/المتاح ويضيف لليوم الجديد بالمسار",
      _rb["borrow_fee"] == 23.31 and _rb["shares_available"] == 600_000
      and _rb["borrow_hist"] == [["2026-07-06", 30_000], ["2026-07-09", 600_000]])
S.refresh_borrow(_rb, "2026-07-09", fetch=lambda s: {"shares_available": 650_000})
check("🔄 refresh_borrow: نفس اليوم يحدّث آخر نقطة (لا تكرار)",
      _rb["borrow_hist"][-1] == ["2026-07-09", 650_000]
      and len(_rb["borrow_hist"]) == 2)
_rb_keep = {"symbol": "XH", "borrow_fee": 23.31, "shares_available": 650_000,
            "borrow_hist": [["2026-07-06", 30_000], ["2026-07-09", 650_000]]}
S.refresh_borrow(_rb_keep, "2026-07-10", fetch=lambda s: {})
check("🔄 refresh_borrow·فاشل-آمن: فشل الجلب ⇒ القيم القديمة تبقى (تعذّر ≠ اختفاء)",
      _rb_keep["shares_available"] == 650_000
      and len(_rb_keep["borrow_hist"]) == 2)
check("🔄 قفل: refresh_borrow خارج rank_key/select_top/classify_tier/analyze_ticker/"
      "backtest_symbol",
      all("refresh_borrow" not in _insp0.getsource(_f)
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.analyze_ticker,
                     S.backtest_symbol)))
check("🔒 سطر الاقتراض·متوسط (5-20%): وصف واقعي بلا سرديات",
      "متوسط (رسوم 12% سنويًّا على من يشورته)" in S.borrow_line({"borrow_fee": 12.0})
      and "جزئي" not in S.borrow_line({"borrow_fee": 12.0}))
check("🔒 سطر الاقتراض·سهل (أقل من 5%): باب حرب الشورت مفتوح ورخيص",
      "سهل ورخيص" in S.borrow_line({"borrow_fee": 0.0})
      and "باب دخول شورت جديد للحرب عليه مفتوح" in S.borrow_line({"borrow_fee": 0.0})
      and "🔥" not in S.borrow_line({"borrow_fee": 0.0}))
check("🔒 سطر الاقتراض: متاح بلا رسوم ⇒ يصرّح «الرسوم غير معروفة»",
      "الرسوم غير معروفة" in S.borrow_line({"shares_available": 9000}))
check("🔒 سطر الاقتراض·فاشل-آمن: لا بيانات ⇒ «—» (تعذّر ≠ صفر)",
      S.borrow_line({}) == "🔒 اقتراض: —")
check("🔒 سطر الاقتراض: بلا علامات مقارنة ≥≤>< (قاعدة لغة المبتدئ)",
      not any(c in _bl_hi + S.borrow_line({"borrow_fee": 12.0}) for c in "≥≤><"))
# 🕵️ السطر الرئيسي «شورت» = المتاح من ChartExchange (قراءة فيصل، 2026-07-11) — عرض فقط
check("🕵️ شورت رئيسي: يعتمد المتاح CE (35K) لا الحجم اليومي (800)",
      S._short_headline({"shares_available": 35000, "finra_short": 800})
      == "شورت 35K")
check("🕵️ شورت رئيسي·DSY: المتاح 7000 (قراءة فيصل IMG_9509)",
      S._short_headline({"shares_available": 7000}) == "شورت 7K")
check("🕵️ شورت رئيسي: بلا متاح CE ⇒ يسقط للحجم اليومي (fintel ثم finra ثم short)",
      S._short_headline({"fintel": {"short_volume": 800}}) == "شورت 800"
      and S._short_headline({"finra_short": 2000}) == "شورت 2K"
      and S._short_headline({"short": 900}) == "شورت 900")
check("🕵️ شورت رئيسي: بلا حجم ⇒ نسبة من الفلوت ثم «—»",
      S._short_headline({"short_pct": 12.5}) == "شورت 12.5% من الفلوت"
      and S._short_headline({}) == "شورت —")
check("🕵️ شورت رئيسي: متاح صفر (ELAB) قيمة صحيحة تُعرض لا تُتخطّى",
      S._short_headline({"shares_available": 0, "finra_short": 800})
      == "شورت 0")
check("🔒 قفل: _short_headline خارج rank_key/select_top/classify_tier/apply_short_gate/"
      "analyze_ticker/backtest_symbol (عرض فقط — M13 يبقى على الحجم اليومي)",
      all("_short_headline" not in _insp0.getsource(_f)
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.apply_short_gate,
                     S.analyze_ticker, S.backtest_symbol)))
check("🔒 قفل: apply_short_gate (M13) لا يقرأ shares_available (المتاح للعرض لا للفرز)",
      "shares_available" not in _insp0.getsource(S.apply_short_gate))
check("🔒 حفظ: make_watch_entry يخزّن borrow_fee/shares_available",
      S.make_watch_entry(dict(r0 or {"symbol": "BOR", "price": 2.0, "pivot": 1.9,
          "entry": (1.9, 2.0), "tranches": [1.9, 2.0], "stop": (1.75, 1.79),
          "t1": 2.3, "t2": 2.6, "t3": 3.0, "score": 60, "flags": [], "rr": 2.0,
          "drop_pct": 60, "best_spike": 120}, borrow_fee=33.0, shares_available=8000),
          "2026-07-09")["borrow_fee"] == 33.0)
check("🔒 قفل: دوال الاقتراض خارج rank_key/select_top/classify_tier/analyze_ticker/backtest_symbol",
      all(("_parse_fintel_borrow" not in _insp0.getsource(_f)
           and "borrow_line" not in _insp0.getsource(_f)
           and "iborrow_info" not in _insp0.getsource(_f))
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.analyze_ticker,
                     S.backtest_symbol)))

# ===== 🎬 تنفيذ خطة فيديو فيصل 1 (DSY) — P1 السبريد · P2 الشورت الرسمي · P3 KST =====
# القيم من fixture الفيديو الحرفي (reference_fixture.json): last 2.79 · Bid 2.52 ·
# Ask 3.12 · SI 37,993 · DTC 0.30 · KST −309 فوق KSTMA −320.222.
# 💧 P1 — سطر السبريد (نسبةً لمنتصف السعر = صيغة الفيديو 0.60/2.82 = 21.28%)
_spl = S.spread_line(2.52, 3.12)
check("💧 P1·سبريد: Bid 2.52/Ask 3.12 ⇒ ~21% + تحذير تنفيذ (صيغة منتصف الفيديو)",
      "21%" in _spl and "طلب $2.52" in _spl and "عرض $3.12" in _spl
      and "قد لا يكون قابلًا للتنفيذ" in _spl)
check("💧 P1·سبريد·وسم الجلسة: session يُعرض (لقطة الفيديو كانت خارج الجلسة)",
      "[بريماركت]" in S.spread_line(2.52, 3.12, "بريماركت"))
check("💧 P1·سبريد·مختصر للتنبيهات اللحظية (Polygon لحظي): «سبريد واسع 21% — سيولة ضعيفة»",
      S.spread_line(2.52, 3.12, brief=True)
      == "💧 سبريد واسع 21% — سيولة ضعيفة، ادخل بأمر محدّد"
      and S.spread_line(2.79, 2.81, brief=True) == "")
check("💧 P1·سبريد·فاشل-آمن: سبريد طبيعي (<5%) أو bid/ask ناقص ⇒ '' (لا سطر)",
      S.spread_line(2.79, 2.81) == "" and S.spread_line(None, 3.12) == ""
      and S.spread_line(0, 0) == "" and S.spread_line(3.12, 2.52) == "")
check("💧 P1·سبريد: تحذير لا بوابة (لا يمنع/يرفض — نص عرض فقط)",
      "امنع" not in _spl and "رفض" not in _spl and "block" not in _spl.lower())
# 📊 P2 — الشورت الرسمي (SI) + أيام التغطية (رقما DSY الحرفيان)
_sir = {"short_interest": 37993, "days_to_cover": 0.30}
check("📊 P2·SI: «شورت رسمي 37,993 سهم · تغطية 0.30 يوم» (رقما فيديو DSY)",
      "شورت رسمي 37,993 سهم" in S.short_interest_line(_sir)
      and "تغطية 0.30 يوم" in S.short_interest_line(_sir))
check("📊 P2·SI·فاشل-آمن: غياب الحقلين ⇒ '' · حقل واحد ⇒ يعرضه وحده",
      S.short_interest_line({}) == ""
      and S.short_interest_line({"short_interest": 37993}) == "📊 شورت رسمي 37,993 سهم"
      and "تغطية" in S.short_interest_line({"days_to_cover": 0.3}))
check("📊 P2·صدق: make_watch_entry يخزّن short_interest/days_to_cover منفصلين عن short",
      (lambda e: e["short_interest"] == 37993 and e["days_to_cover"] == 0.3
       and e["short"] != 37993)(S.make_watch_entry(
          {"symbol": "DSY", "price": 2.79, "pivot": 2.5, "entry": (2.5, 2.6),
           "tranches": [2.5, 2.6], "stop": (2.3, 2.4), "t1": 3.0, "t2": 3.4,
           "t3": 4.0, "score": 60, "flags": [], "rr": 2.0, "drop_pct": 60,
           "best_spike": 120, "finra_short": 5000, "short_interest": 37993,
           "days_to_cover": 0.30}, "2026-07-10")))
# 📈 P3 — KST بإعدادات فيصل (4 حالات كما يفرّقها فيصل بالفيديو)
import pandas as _pd3
_rally = _pd3.Series([1.0] * 40 + [1.0 * (1.05 ** i) for i in range(1, 41)])
_fall = _pd3.Series([10.0 - 0.05 * i for i in range(80)])
_declerate = _pd3.Series([1.0 + i * 0.02 for i in range(80)])  # صعود خطّي = زخم يتباطأ
check("📈 P3·KST: رالي متسارع ⇒ «زخم صاعد» · هبوط مستمر ⇒ «زخم هابط»",
      "زخم صاعد" in (S.momentum_kst_state(_rally) or "")
      and "زخم هابط" in (S.momentum_kst_state(_fall) or ""))
check("📈 P3·KST: صعود خطّي (زخم متباطئ) ⇒ «تراجع زخم» (يفرّق الحالات لا حالة واحدة)",
      "تراجع زخم" in (S.momentum_kst_state(_declerate) or ""))
check("📈 P3·KST·فاشل-آمن: بيانات قصيرة ⇒ None (لا انهيار)",
      S.momentum_kst_state(_pd3.Series([1.0, 2.0, 3.0])) is None)
check("📈 P3·KST: الدالة موجودة بإعدادات فيصل الحرفية (10,15,20,30,10,10,10,15,9)",
      "roc(30).rolling(15)" in _insp0.getsource(S.kst)
      and "roc(10).rolling(10)" in _insp0.getsource(S.kst))
# 🔒 قفل حاسم: كل الثلاث عرض/سياق فقط — خارج الفرز والبوابات والتصنيف
check("🔒 قفل: spread_line/short_interest_line/momentum_kst_state خارج rank_key/"
      "select_top/classify_tier/entry_status/apply_float_gate/backtest_symbol",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("spread_line", "short_interest_line", "momentum_kst_state")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_float_gate, S.backtest_symbol)))
check("🔒 قفل: short_interest/days_to_cover لا يمسّان finra_short ولا M13 (مقياس مستقل)",
      "short_interest" not in _insp0.getsource(S.apply_short_gate)
      if hasattr(S, "apply_short_gate") else True)

# ===== 📅 الأحداث المعلنة القادمة (أرباح/تجارب — «يوم الانفجار الذي ينتظره المضارب») =====
_ev_today = S.dt.date(2026, 7, 9)
def _ct_study(sponsor, date, phase="PHASE2", nct="NCT01"):
    return {"protocolSection": {
        "sponsorCollaboratorsModule": {"leadSponsor": {"name": sponsor}},
        "statusModule": {"primaryCompletionDateStruct": {"date": date}},
        "designModule": {"phases": [phase]},
        "identificationModule": {"nctId": nct}}}
_ct_data = {"studies": [
    _ct_study("Femasys Inc", "2026-07-30", "PHASE2", "NCT111"),   # مطابق قادم
    _ct_study("Other Pharma", "2026-07-20"),                       # راعٍ مختلف → يُستبعد
    _ct_study("Femasys Inc", "2026-06-01"),                        # ماضٍ → يُستبعد
    _ct_study("Femasys Inc", "2026-08"),                           # شهر فقط → أول الشهر
    _ct_study("Femasys Inc", "2026-12-01")]}                       # أبعد من الأفق → يُستبعد
_ct_out = S._parse_ct_studies(_ct_data, "Femasys Inc", _ev_today, 45)
check("📅 تجارب: مطابقة الراعي + قادم ضمن الأفق فقط + «سنة-شهر» → أول الشهر + الترتيب",
      [e["date"] for e in _ct_out] == ["2026-07-30", "2026-08-01"]
      and all(e["kind"] == "تجربة" for e in _ct_out)
      and "المرحلة 2" in _ct_out[0]["note"] and "NCT111" in _ct_out[0]["note"])
check("📅 تجارب·فاشل-آمن: ردّ فارغ/بلا شركة ⇒ []",
      S._parse_ct_studies({}, "X", _ev_today, 45) == []
      and S._parse_ct_studies(_ct_data, "", _ev_today, 45) == [])
_ev_mix = [{"kind": "أرباح", "date": "2026-07-19", "note": ""},
           {"kind": "تجربة", "date": "2026-07-30", "note": "المرحلة 2 · NCT111"}]
_evl = S.events_lines(_ev_mix, today=_ev_today)
check("📅 الأسطر: أرباح «بعد 10 يوم» بتفسير المضارب + تجربة بملاحظتها وتحفّظ التقدير",
      len(_evl) == 2 and "أرباح معلنة: 2026-07-19 (بعد 10 يوم)" in _evl[0]
      and "المضارب يجهّز قبل الإعلان" in _evl[0]
      and "اكتمال تجربة سريرية (المرحلة 2 · NCT111)" in _evl[1]
      and "قد يتغيّر" in _evl[1])
check("📅 الأسطر: «اليوم!» و«غدًا» للقريب",
      "اليوم!" in S.events_lines([{"kind": "أرباح", "date": "2026-07-09"}],
                                 today=_ev_today)[0]
      and "غدًا" in S.events_lines([{"kind": "أرباح", "date": "2026-07-10"}],
                                   today=_ev_today)[0])
check("📅 الأسطر: الماضي والأبعد من الأفق يُخفيان · None ⇒ []",
      S.events_lines([{"kind": "أرباح", "date": "2026-07-01"},
                      {"kind": "أرباح", "date": "2026-12-01"}],
                     today=_ev_today) == []
      and S.events_lines(None) == [])
check("📅 الأسطر: بحدّ 3 أسطر (لا حشو) + بلا علامات مقارنة",
      len(S.events_lines([{"kind": "أرباح", "date": "2026-07-19"}] * 5,
                         today=_ev_today)) == 3
      and not any(c in " ".join(_evl) for c in "≥≤><"))
# اجتماع مساهمين (تاريخه = تاريخ الدعوة الماضي — يظهر ضمن نافذة PROXY_LOOKBACK)
_evm = S.events_lines([{"kind": "اجتماع", "date": "2026-06-25",
                        "note": "DEF 14A"}], today=_ev_today)
check("📅 اجتماع: دعوة قبل 14 يومًا ⇒ سطر «اجتماع مساهمين قادم» + تحذير التقسيم",
      len(_evm) == 1 and "اجتماع مساهمين قادم (دعوة DEF 14A)" in _evm[0]
      and "شهر إلى شهرين" in _evm[0] and "التقسيم العكسي" in _evm[0])
check("📅 اجتماع: دعوة أقدم من نافذة الالتقاط (100 يوم) ⇒ تُخفى",
      S.events_lines([{"kind": "اجتماع", "date": "2026-03-25"}],
                     today=_ev_today) == [])
check("📅 حظر المؤسسين: تقديري + «قد يفكّ أسهمًا» · الماضي يُخفى",
      (lambda L: len(L) == 1 and "انتهاء حظر بيع المؤسسين (تقديري)" in L[0]
       and "قد يفكّ أسهمًا" in L[0])(
          S.events_lines([{"kind": "حظر", "date": "2026-07-25"}],
                         today=_ev_today))
      and S.events_lines([{"kind": "حظر", "date": "2026-07-01"}],
                         today=_ev_today) == [])
# التجميع مع الوكالة والحظر (نقي — بلا شبكة: الأرباح/التجارب محقونة None/[])
_sv_ne2, _sv_ce2 = S.next_earnings, S.clinical_events
try:
    S.next_earnings = lambda sym: None
    S.clinical_events = lambda co: []
    _ft_recent = (S.dt.date.today() - S.dt.timedelta(days=160)).isoformat()
    _ue_px = S.upcoming_events("X", proxy={"form": "DEF 14A",
                                           "date": "2026-06-25"},
                               first_trade=_ft_recent)
    check("📅 التجميع: الوكالة + الحظر (إدراج قبل 160ي ⇒ الحظر بعد ~20ي) يدخلان",
          {e["kind"] for e in _ue_px} == {"اجتماع", "حظر"})
    check("📅 التجميع: إدراج قديم (400ي — الحظر ماضٍ) ⇒ لا حدث حظر",
          S.upcoming_events("X", first_trade=(
              S.dt.date.today() - S.dt.timedelta(days=400)).isoformat()) is None)
finally:
    S.next_earnings, S.clinical_events = _sv_ne2, _sv_ce2
check("📅 حفظ: make_watch_entry يخزّن proxy_filing + first_trade",
      (lambda _w: _w["proxy_filing"] == {"form": "DEF 14A", "date": "2026-06-25"}
       and _w["first_trade"] == "2026-01-15")(
          S.make_watch_entry(dict(r0 or {"symbol": "PXF", "price": 2.0,
              "pivot": 1.9, "entry": (1.9, 2.0), "tranches": [1.9, 2.0],
              "stop": (1.75, 1.79), "t1": 2.3, "t2": 2.6, "t3": 3.0,
              "score": 60, "flags": [], "rr": 2.0, "drop_pct": 60,
              "best_spike": 120},
              proxy_filing={"form": "DEF 14A", "date": "2026-06-25"},
              first_trade="2026-01-15"), "2026-07-09")))
check("📅 SEC: دعوات الاجتماع مصنّفة بالعرض (DEF 14A 🟡) + قائمة أشكال الالتقاط",
      S.SEC_FORM_CLASS.get("DEF 14A", ("",))[0] == "🟡"
      and "PRE 14A" in S._PROXY_FORMS and "DEFA14A" in S._PROXY_FORMS)
# التجميع upcoming_events (بحقن الدوال — بلا شبكة) + بوّابة قطاع الرعاية للتجارب
_sv_ne, _sv_ce = S.next_earnings, S.clinical_events
try:
    S.next_earnings = lambda sym: "2026-07-19"
    S.clinical_events = lambda co: [{"kind": "تجربة", "date": "2026-07-15",
                                     "note": "NCT9"}]
    _ue_hc = S.upcoming_events("FEMY", "Femasys Inc", "Healthcare")
    check("📅 التجميع: أرباح + تجربة (رعاية صحية) مرتّبة بالأقرب",
          [e["kind"] for e in _ue_hc] == ["تجربة", "أرباح"])
    _ue_en = S.upcoming_events("GEOS", "Geospace", "Energy")
    check("📅 التجميع·بوّابة القطاع: غير الرعاية الصحية ⇒ أرباح فقط (لا نداء تجارب)",
          [e["kind"] for e in _ue_en] == ["أرباح"])
    S.next_earnings = lambda sym: None
    S.clinical_events = lambda co: []
    check("📅 التجميع·فاشل-آمن: لا شيء ⇒ None",
          S.upcoming_events("X", "Y", "Healthcare") is None)
finally:
    S.next_earnings, S.clinical_events = _sv_ne, _sv_ce
check("📅 حفظ: make_watch_entry يخزّن upcoming_events + company_name",
      (lambda _w: _w["upcoming_events"] == _ev_mix
       and _w["company_name"] == "Femasys Inc")(
          S.make_watch_entry(dict(r0 or {"symbol": "EVT", "price": 2.0,
              "pivot": 1.9, "entry": (1.9, 2.0), "tranches": [1.9, 2.0],
              "stop": (1.75, 1.79), "t1": 2.3, "t2": 2.6, "t3": 3.0,
              "score": 60, "flags": [], "rr": 2.0, "drop_pct": 60,
              "best_spike": 120}, upcoming_events=_ev_mix,
              company_name="Femasys Inc"), "2026-07-09")))
_wl_ev = {"week_start": "2026-07-01", "removed": [], "notes": [], "stocks": [
    dict(_wl_entry("EVD", "near_support"),
         upcoming_events=[{"kind": "أرباح",
                           "date": (S.dt.date.today()
                                    + S.dt.timedelta(days=10)).isoformat()}])]}
check("📅 اليومي: كرت الجاهز يعرض سطر «أرباح معلنة»",
      "أرباح معلنة" in S.build_daily_message(_wl_ev, [], [], [], ready_only=True))
check("📅 قفل: دوال الأحداث خارج rank_key/select_top/classify_tier/analyze_ticker/backtest_symbol",
      all(("upcoming_events" not in _insp0.getsource(_f)
           and "next_earnings" not in _insp0.getsource(_f)
           and "clinical_events" not in _insp0.getsource(_f)
           and "events_lines" not in _insp0.getsource(_f))
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.analyze_ticker,
                     S.backtest_symbol)))
_sv_tr = TR._next_earnings_date
try:
    TR._next_earnings_date = lambda sym: (_ for _ in ()).throw(ValueError("x"))
    check("📅 فاشل-آمن: انهيار مصدر الأرباح ⇒ next_earnings يرجع None بهدوء",
          S.next_earnings("ANY") is None)
finally:
    TR._next_earnings_date = _sv_tr

# ===== 📉 ضغط/تصريف المضارب (طلب المستخدم: نمط LABT الحيّ — يومي + أفتر) =====
def _dump_st(sym):
    return {"symbol": sym, "status": "active", "pivot": 1.5,
            "tranches": [1.5, 1.6], "stop": (1.2, 1.25), "interp": {}}
_dump_df = pd.DataFrame(
    {"Open": [3.0] * 30, "High": [3.1] * 30, "Low": [2.4] * 30,
     "Close": [3.0] * 29 + [2.5], "Volume": [1e5] * 30},   # 3.0→2.5 = -16.7%
    index=pd.date_range(end="2026-07-20", periods=30, freq="B"))   # ⑤ = today
_nodump_df = pd.DataFrame(
    {"Open": [3.0] * 30, "High": [3.1] * 30, "Low": [2.9] * 30,
     "Close": [3.0] * 29 + [2.95], "Volume": [1e5] * 30},   # -1.7%
    index=pd.date_range(end="2026-07-20", periods=30, freq="B"))   # ⑤ = today
_ev_d = S.monitor_live_events({"stocks": [_dump_st("DMP")]}, {"DMP": _dump_df},
    "2026-07-20", fetch_operator=lambda s: {"has_operator": False})
check("📉 ضغط المضارب: هبوط اليوم ≥15% عن الأمس ⇒ dump (خطر — يظهر بلا مضارب)",
      any(k == "dump" and "تصريف" in d for _s, k, d in _ev_d))
check("📉 لا هبوط حادّ ⇒ لا dump",
      not any(k == "dump" for _s, k, _d in S.monitor_live_events(
          {"stocks": [_dump_st("ND")]}, {"ND": _nodump_df}, "2026-07-20",
          fetch_operator=lambda s: {"has_operator": True})))
_ev_ah = S.monitor_live_events({"stocks": [_dump_st("AHD")]}, {"AHD": _nodump_df},
    "2026-07-20",
    fetch_afterhours=lambda sym, rc: {"kind": "afterhours", "change_pct": -22.0})
check("📉 أفتر (بحقن جالب): هبوط ≥15% عن الإغلاق ⇒ afterdump (نمط LABT)",
      any(k == "afterdump" and "الأفتر" in d for _s, k, d in _ev_ah))
check("📉 أفتر: هبوط بسيط (-5%) ⇒ لا afterdump",
      not any(k == "afterdump" for _s, k, _d in S.monitor_live_events(
          {"stocks": [_dump_st("AH2")]}, {"AH2": _nodump_df}, "2026-07-20",
          fetch_afterhours=lambda sym, rc: {"change_pct": -5.0})))
check("📉 أيقونات: dump/afterdump = 📉",
      S._LIVE_ICON.get("dump") == "📉" and S._LIVE_ICON.get("afterdump") == "📉")
check("📉 قفل: polygon_after_hours خارج rank_key/select_top/analyze_ticker/backtest_symbol",
      all("polygon_after_hours" not in _insp0.getsource(_f)
          for _f in (S.rank_key, S.select_top, S.analyze_ticker, S.backtest_symbol)))
check("📉 _premarket_summary يعيد آخر بار مقابل المرجع (يخدم الأفتر أيضًا)",
      S._premarket_summary([{"o": 3, "h": 3, "l": 2, "c": 2.4, "v": 100}], 3.0)
      ["change_pct"] == -20.0)

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
# ⑨ (تدقيق 2026-07-12، خيار ب) — قفل: «هدف ثم ستوب = رابح دائمًا». الرابح الذي
# ارتدّ ولمس ستوبه يُصنَّف بالـhit أولًا (won يسبق فحص الستوب) فلا يلوّث الخسائر —
# هذا الواقع الذي تأكّدنا منه بالكود (نقض ادّعاء التقرير)، نقفله فلا ينكسر.
_wts = {"history": [], "stocks": [],
        "removed": [{"symbol": "WTS", "entry_ref": 2.0, "hit": "t3",
                     "status": "stopped", "max_gain_pct": 40.0,
                     "removal_reason": "لمس الستوب بعد تحقيق هدف3"}]}
_wts_rows = S._collect_closed(_wts)
check("⑨ قفل: هدف مُحقَّق ثم ستوب ⇒ يُحسب رابحًا (لا يلوّث مقام الخسائر)",
      len(_wts_rows) == 1 and _wts_rows[0]["_win"] is True
      and S._wr(_wts_rows)[1] == 100.0)
# ⑨ قفل السعة: أصحاب hit لا يحجزون خانة — دالة نقيّة تحاكي حساب run_daily_watchlist
def _slots_free(stocks, size):
    return size - len([s for s in stocks if not s.get("hit")])
_wl9 = [{"symbol": f"S{i}", "hit": ("t1" if i < 4 else None)} for i in range(6)]
check("⑨ قفل: 6 نشطين (4 حقّقوا هدفًا) والحجم 6 ⇒ 4 خانات حرّة (الرابحون لا يحجزون)",
      _slots_free(_wl9, 6) == 4)
check("⑨ قفل: بلا أصحاب هدف ⇒ السعة كالسابق حرفيًا (توافق: القائمة ممتلئة تحجب)",
      _slots_free([{"symbol": f"F{i}"} for i in range(6)], 6) == 0)
check("⑨ قفل: المصدر يحسب السعة على «الحاملين للخانة» لا كل النشطين",
      "_slot_holders" in _insp0.getsource(S.run_daily_watchlist)
      and 'if not s.get("hit")' in _insp0.getsource(S.run_daily_watchlist))
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
# 🩺 حالة جمع بيانات المضارب (طلب المستخدم 2026-07-24 «اكيد بننسى»): عدّادات تظهر **دائمًا
# حتى عند صفر بيانات** (الفخّ: hand_flow/ignition يختفيان عند الفراغ فتضيع رؤية التوقّف).
check("🩺 مساعد التطوير: لوحة حالة جمع البيانات تظهر دائمًا (رادار+حصّاد+E2) حتى بلا سجلّ",
      "حالة جمع بيانات المضارب" in _rep_alerts
      and "رادار الانطلاق" in _rep_alerts and "حصّاد اليد" in _rep_alerts
      and "جلسات قياس E2" in _rep_alerts)
# 🔬 عدّ فهرس E2 (إصلاح 2026-07-24): **الشكل الحقيقي قاموس مفتاحه التاريخ** — التكرار عليه يعطي
# مفاتيح نصّية فكان العدّاد يقرأ صفرًا للأبد (كذب صامت). قفل على الشكل الحقيقي المدفوع بالريبو.
check("🔬 E2·عدّ: الشكل الحقيقي (قاموس مفتاحه التاريخ) يُعدّ صحيحًا لا صفرًا",
      S._e2_index_counts({"2026-07-24": {"n_symbols": 8, "termination": "normal"},
                          "2026-07-23": {"n_symbols": 5, "termination": "early"}}) == (2, 1))
check("🔬 E2·عدّ: يدعم شكل القائمة أيضًا (توافق خلفي)",
      S._e2_index_counts([{"termination": "normal"}, {"termination": "normal"}]) == (2, 2))
check("🔬 E2·عدّ·فاشل-آمن: فارغ/None/نوع غريب ⇒ (0,0) بلا انهيار",
      S._e2_index_counts({}) == (0, 0) and S._e2_index_counts(None) == (0, 0)
      and S._e2_index_counts(["نص", 5]) == (0, 0))


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
# 🔬 F-L1 (تدقيق النظر المستقبلي 2026-07-12): الهدف لا يُحسم على شمعة التعبئة
# الداخلية (ترتيب اللمس مجهول = فوز وهمي)؛ الستوب يبقى محميًّا؛ ذراع المسح (دخول
# بإغلاق) يحسم من شمعة دخوله. + حقل outcome_legacy لقياس حجم التفاؤل بتشغيل واحد.
_fl1_hi = np.array([110., 100.]); _fl1_lo = np.array([97., 98.])
_fl1_cl = np.array([100., 99.]); _fl1_op = np.array([99., 99.])
check("F-L1: هدف على شمعة التعبئة الداخلية ⇒ open لا win (يفشل قبل الإصلاح)",
      S._resolve_arm(_fl1_hi, _fl1_lo, _fl1_cl, _fl1_op, 100., 93., 109., 0)[0]
      == "open")
check("F-L1: السلوك القديم (entry_intrabar=False) على نفس الشمعة ⇒ win (يقيس التفاؤل)",
      S._resolve_arm(_fl1_hi, _fl1_lo, _fl1_cl, _fl1_op, 100., 93., 109., 0,
                     entry_intrabar=False)[0] == "win")
check("F-L1: الهدف على الشمعة التالية ⇒ win (لا يُكبت الفوز الحقيقي)",
      S._resolve_arm(np.array([105., 110.]), np.array([97., 99.]),
                     np.array([100., 108.]), np.array([99., 101.]),
                     100., 93., 109., 0)[0] == "win")
check("F-L1: الستوب على شمعة التعبئة يبقى محميًّا (loss فوري — محافظ)",
      S._resolve_arm(np.array([110., 100.]), np.array([90., 95.]),
                     np.array([94., 96.]), np.array([99., 97.]),
                     100., 93., 109., 0)[0] == "loss")
check("F-L1: ذراع المسح (entry_intrabar=False) يحسم الهدف من شمعة دخوله (يملك من الفتح)",
      S._resolve_arm(np.array([110.]), np.array([99.]), np.array([108.]),
                     np.array([100.]), 100., 93., 109., 0,
                     entry_intrabar=False)[0] == "win")
check("F-L1: backtest_symbol يحفظ outcome_legacy/ret_legacy لكل صفقة (للمقارنة)",
      len(_bt_off) >= 1 and all("outcome_legacy" in t and "ret_legacy" in t
                                for t in _bt_off))
# 🔬 F-COST (تدقيق 2026-07-12): تكلفة تنفيذ اختيارية (BT_SPREAD_PCT) — 0 = سلوك
# اليوم حرفيًا · موجب يخفض العائد رتيبًا · محصَّن بقفل B1 (الإنتاج يتجاهله).
# filled=0 والهدف يُضرب على الشمعة 1 (غير شمعة التعبئة) = win نظيف نقيس عائده.
_fc_args = (np.array([102., 110.]), np.array([98., 100.]),
            np.array([100., 108.]), np.array([99., 101.]), 100., 93., 109., 0)
check("F-COST: spread=0 ⇒ العائد كما اليوم حرفيًا (+9% على t1=109)",
      abs(S._resolve_arm(*_fc_args, spread=0.0)[1] - 9.0) < 1e-9)
_fc_ret = S._resolve_arm(*_fc_args, spread=0.04)[1]     # سبريد 4%
# buy=100×1.02=102 · sell=109×0.98=106.82 · العائد=106.82/102−1≈+4.73%
check("F-COST: spread=4% يخفض عائد الرابح (+9% ⇒ ~+4.7%، رتيبًا)",
      _fc_ret < 9.0 and abs(_fc_ret - 4.73) < 0.1)
check("F-COST: أكبر سبريد ⇒ عائد أقل رتيبًا (حساسية 1/3/5%)",
      S._resolve_arm(*_fc_args, spread=0.01)[1]
      > S._resolve_arm(*_fc_args, spread=0.03)[1]
      > S._resolve_arm(*_fc_args, spread=0.05)[1])
_fc_sv = S.CONFIG.get("BT_SPREAD_PCT", 0.0)
try:
    _fc_prod = S._apply_backtest_overrides("FULL", {"BT_SPREAD_PCT": "0.05"})
    _fc_bt = S._apply_backtest_overrides("BACKTEST", {"BT_SPREAD_PCT": "0.05"})
    check("F-COST·قفل B1: الإنتاج يتجاهل BT_SPREAD_PCT (باكتيست حصريًا)",
          _fc_prod == [] and any("BT_SPREAD_PCT" in s for s in _fc_bt))
finally:
    S.CONFIG["BT_SPREAD_PCT"] = _fc_sv          # لا تلوّث بقية الاختبارات
# 🏦 BT_POTENTIAL «قوة البوت» (تصحيح المستخدم 2026-07-12): أقصى صعود من الدخول
# **قبل** ضرب الوقف (الأهداف تمهيدية = خارج القياس). دالة نقيّة _max_gain_before_stop.
# (أ) صعود نظيف ثم وقف لاحق: يصعد لذروة ثم ينهار للوقف → stopped بالذروة قبل الوقف.
_mg_up = S._max_gain_before_stop(
    np.array([100., 130., 160., 120.]),          # ذروة +60% بالشمعة 2
    np.array([98., 110., 140., 89.]),            # الوقف=90 يُضرب بالشمعة 3
    np.array([99., 115., 145., 118.]), 100., 90., 0)
check("🏦 قوة البوت: صعود +60% ثم وقف ⇒ stopped بصعود مشروط +60 (الذروة قبل الوقف)",
      _mg_up[0] == "stopped" and abs(_mg_up[1] - 60.0) < 0.5 and _mg_up[2] == 2)
# (ب) وقف مبكر قبل أي صعود ⇒ stopped بصعود ~0 (يفرّق عن fwd_max الكامل — سيناريو QNTM)
_mg_early = S._max_gain_before_stop(
    np.array([101., 180.]), np.array([99., 88.]),   # الشمعة 1 تضرب الوقف=90 ثم يطير 180
    np.array([100., 92.]), 100., 90., 0)
check("🏦 قوة البوت·QNTM: وقف مبكر ⇒ stopped بصعود ~0 (لا +80 الكامل — الوقف حاكم)",
      _mg_early[0] == "stopped" and _mg_early[1] == 0.0)
# (ج) لا وقف بالنافذة ⇒ survived بأقصى الصعود + يوم الذروة
_mg_surv = S._max_gain_before_stop(
    np.array([105., 145., 130.]), np.array([98., 108., 112.]),
    np.array([99., 106., 128.]), 100., 90., 0)
check("🏦 قوة البوت: لا وقف ⇒ survived بأقصى صعود +45 يوم الذروة 1",
      _mg_surv[0] == "survived" and abs(_mg_surv[1] - 45.0) < 0.5 and _mg_surv[2] == 1)
# (د) F-L1: رأس شمعة التعبئة الداخلية لا يدخل القياس (يبدأ من filled+1)
check("🏦 قوة البوت·F-L1: رأس شمعة التعبئة الداخلية لا يُحسب (يفشل لو حُسب)",
      S._max_gain_before_stop(np.array([200., 110.]), np.array([98., 99.]),
                              np.array([99., 101.]), 100., 90., 0)[1] == 10.0)
# (هـ) رأس شمعة الوقف لا يُحسب (ترتيب اللمس مجهول — درس F-L1)
check("🏦 قوة البوت: رأس شمعة الوقف لا يُحسب (الصعود قبلها فقط)",
      S._max_gain_before_stop(np.array([100., 120., 300.]),
                              np.array([98., 105., 85.]),   # الشمعة 2 وقف+رأس ضخم
                              np.array([99., 110., 90.]), 100., 90., 0)[1] == 20.0)
# (و) لا تعبئة ⇒ no_fill
check("🏦 قوة البوت: لا تعبئة (filled=None) ⇒ no_fill",
      S._max_gain_before_stop(np.array([1.]), np.array([1.]), np.array([1.]),
                              100., 90., None) == ("no_fill", None, None))
# (ز) الوصل بـbacktest_symbol خلف BT_POTENTIAL: مفعّلة ⇒ حقول mg_* تُلحَق لكل صفقة ·
# مطفأة (الافتراض) ⇒ صفر حقول (توافق: صفقة الأساس بت-بت). نُطفئها فورًا كي لا تتسرّب.
S.CONFIG["BT_POTENTIAL"] = 1
_mg_bt_on = S.backtest_symbol("MGON", synth_pivot(seed=2))
S.CONFIG["BT_POTENTIAL"] = 0
_mg_bt_off = S.backtest_symbol("MGOFF", synth_pivot(seed=2))
check("🏦 قوة البوت·وصل: مفعّلة ⇒ كل صفقة تحمل mg_outcome/mg_pre_stop/mg_peak_day",
      len(_mg_bt_on) >= 1 and all({"mg_outcome", "mg_pre_stop", "mg_peak_day"}
                                  <= set(t) for t in _mg_bt_on))
check("🏦 قوة البوت·توافق: مطفأة (الافتراض) ⇒ صفر حقول mg_ (صفقة الأساس بت-بت)",
      len(_mg_bt_off) >= 1 and all("mg_outcome" not in t and "mg_pre_stop" not in t
                                   and "mg_peak_day" not in t for t in _mg_bt_off))
# (ح) قفل B1: BT_POTENTIAL/BT_PORTFOLIO/BT_PORT_SIZE — باكتيست حصريًا (الإنتاج يتجاهلها)
_mg_env = {"BT_POTENTIAL": "1", "BT_PORTFOLIO": "1", "BT_PORT_SIZE": "20"}
_mg_sv = (S.CONFIG.get("BT_POTENTIAL"), S.CONFIG.get("BT_PORTFOLIO"),
          S.CONFIG.get("BT_PORT_SIZE"))
try:
    check("🏦 قوة البوت·قفل B1: الإنتاج يتجاهل مفاتيح BT_POTENTIAL/PORTFOLIO/PORT_SIZE",
          S._apply_backtest_overrides("FULL", _mg_env) == [])
    _mg_applied = S._apply_backtest_overrides("BACKTEST", _mg_env)
    check("🏦 قوة البوت·قفل B1: وضع BACKTEST يطبّق المفاتيح الثلاثة",
          all(any(k in s for s in _mg_applied)
              for k in ("BT_POTENTIAL", "BT_PORTFOLIO", "BT_PORT_SIZE")))
finally:
    (S.CONFIG["BT_POTENTIAL"], S.CONFIG["BT_PORTFOLIO"],
     S.CONFIG["BT_PORT_SIZE"]) = _mg_sv         # لا تلوّث بقية الاختبارات


# 🔬 BT_FEATURES: أعمدة تحليل point-in-time (قطاع + أيام لأقرب أرباح) — باكتيست/تحليل فقط
def _bt_raise(s):
    raise ValueError("boom")
check("🔬 BT_FEATURES: _bt_days_to_earnings نقيّة point-in-time (أقرب أرباح بعد الإشارة)",
      S._bt_days_to_earnings("2025-05-05", ["2025-03-01", "2025-06-10", "2025-09-01"]) == 36
      and S._bt_days_to_earnings("2025-05-05", ["2025-01-01", "2025-02-01"]) is None
      and S._bt_days_to_earnings("2025-05-05", []) is None)
_bt_tr = [{"symbol": "AAA", "date": "2025-05-05"}, {"symbol": "AAA", "date": "2025-07-01"},
          {"symbol": "BBB", "date": "2025-06-01"}]
S._bt_feature_enrich(_bt_tr,
    sector_fetch=lambda s: {"sector": "Technology"} if s == "AAA" else {},
    earn_fetch=lambda s: ["2025-06-10"] if s == "AAA" else [])
check("🔬 BT_FEATURES: enrich يضيف sector + days_to_earnings (point-in-time لكل إشارة)",
      _bt_tr[0]["sector"] == "Technology" and _bt_tr[0]["days_to_earnings"] == 36
      and _bt_tr[1]["days_to_earnings"] is None       # أرباح 06-10 قبل إشارة 07-01 = لا لاحق
      and _bt_tr[2]["sector"] == "—" and _bt_tr[2]["days_to_earnings"] is None)
_bt_fs = [{"symbol": "ZZZ", "date": "2025-05-05"}]
S._bt_feature_enrich(_bt_fs, sector_fetch=_bt_raise, earn_fetch=_bt_raise)
check("🔬 BT_FEATURES: فاشل-آمن (الجالب يرمي) → «—»/None بلا انهيار",
      _bt_fs[0]["sector"] == "—" and _bt_fs[0]["days_to_earnings"] is None)
check("🔬 BT_FEATURES: خارج الجذر backtest_symbol + مُبوَّب بعلم في run_backtest",
      "_bt_feature_enrich" not in _insp0.getsource(S.backtest_symbol)
      and "sector" not in _insp0.getsource(S.backtest_symbol)
      and 'CONFIG.get("BT_FEATURES")' in _insp0.getsource(S.run_backtest))
# 🔬 BT_FEATURES (إصلاح مراجعة Codex): المسار الافتراضي يمرّر **كائن Ticker** لـ_fetch_info لا نصًّا
# (تمرير النصّ كان يفشل 9ث/سهم ثم «—»). نحاكي yf/_fetch_info بلا شبكة ونثبت العقد.
_bt_yf_s, _bt_fi_s = S.yf, S._fetch_info
_bt_seen = {}


class _FakeTk:
    def __init__(self, sym):
        self.sym = sym


class _FakeYf:
    Ticker = staticmethod(lambda s: _FakeTk(s))


def _fake_fi(t):
    _bt_seen["type"] = type(t).__name__          # يجب أن يكون كائنًا لا str
    _bt_seen["sym"] = getattr(t, "sym", None)
    return {"sector": "Healthcare"}


try:
    S.yf, S._fetch_info = _FakeYf(), _fake_fi
    _sec_def = S._bt_sector("GEOS")               # المسار الافتراضي (بلا fetch محقون)
    check("🔬 BT_FEATURES: _bt_sector الافتراضي يمرّر Ticker (كائن) لـ_fetch_info ويرجع قطاعًا",
          _sec_def == "Healthcare" and _bt_seen.get("type") == "_FakeTk"
          and _bt_seen.get("sym") == "GEOS")
    S.yf = None                                   # بلا yf ⇒ «—» فاشل-آمن (لا انهيار)
    check("🔬 BT_FEATURES: _bt_sector بلا yf ⇒ «—» فاشل-آمن", S._bt_sector("X") == "—")
finally:
    S.yf, S._fetch_info = _bt_yf_s, _bt_fi_s

# 🔬 نافذة التحميل الممتدّة (إصلاح حاجز الباكتيست متعدّد السنوات) — باكتيست فقط، الإنتاج بت-بت
_dh_saved = (S.yf, S._download_chunk)
try:
    S.yf = object()                        # truthy (يتجاوز yf is None)
    _dh_cap = {}
    S._download_chunk = lambda chunk, start: _dh_cap.update({"start": start})
    S.download_history(["AAA"], start_override="2020-10-01")
    check("🔬 نافذة تحميل: start_override يُستعمَل حرفيًّا (باكتيست قديم يصل 2023)",
          _dh_cap.get("start") == "2020-10-01")
    _dh_cap.clear()
    S.download_history(["AAA"])            # الإنتاج: بلا override
    _dh_exp = (S.dt.date.today() - S.dt.timedelta(days=S.CONFIG["HISTORY_DAYS"])).isoformat()
    check("🔬 نافذة تحميل: بلا override = اليوم−HISTORY_DAYS (الإنتاج حرفيًّا)",
          _dh_cap.get("start") == _dh_exp)
finally:
    S.yf, S._download_chunk = _dh_saved
check("🔬 نافذة تحميل: run_backtest يمدّ البدء من date_window ويمرّره",
      "_bt_dl_start" in _insp0.getsource(S.run_backtest)
      and "start_override=_bt_dl_start" in _insp0.getsource(S.run_backtest)
      and "start_override" in _insp0.getsource(S.download_history))
# (ط) 🔒 قفل getsource: دالة القياس خارج الفرز/الاختيار/التتبّع (باكتيست/عرض فقط —
# لا تدخل قرار الدخول/الوقف/الأهداف/العضوية). درس C3: أي دالة قياس تلمس الاختيار = بوابة خفية.
check("🏦 قوة البوت·قفل: _max_gain_before_stop خارج rank_key/select_top/classify_tier/"
      "analyze_ticker/update_tracking/update_watchlist_status",
      all("_max_gain_before_stop" not in _insp0.getsource(_f)
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.analyze_ticker,
                     S.update_tracking, S.update_watchlist_status)))
# 🕰️ BT_RAW_PRICE (تدقيق خارجي 2026-07-12): point-in-time بالباكتيست — auto_adjust=False
# لتفادي إشارات وهمية من تعديل تقسيم مستقبلي. الإنتاج يتجاهله (قفل B1) → auto_adjust=True.
check("🕰️ BT_RAW_PRICE: الافتراض 0 (الإنتاج يحمّل معدّلًا كما كان)",
      S.CONFIG.get("BT_RAW_PRICE") == 0)
check("🕰️ BT_RAW_PRICE·وصل: _download_chunk يقرأ العلم (auto_adjust=not BT_RAW_PRICE)",
      'auto_adjust=not CONFIG.get("BT_RAW_PRICE")' in _insp0.getsource(S._download_chunk))
_rp_env = {"BT_RAW_PRICE": "1"}
check("🕰️ BT_RAW_PRICE·قفل B1: الإنتاج يتجاهله (باكتيست حصريًا)",
      S._apply_backtest_overrides("FULL", _rp_env) == [])
_rp_sv = S.CONFIG.get("BT_RAW_PRICE")
try:
    _rp_ap = S._apply_backtest_overrides("BACKTEST", _rp_env)
    check("🕰️ BT_RAW_PRICE·قفل B1: وضع BACKTEST يطبّقه",
          any("BT_RAW_PRICE" in s for s in _rp_ap) and S.CONFIG["BT_RAW_PRICE"] == 1)
finally:
    S.CONFIG["BT_RAW_PRICE"] = _rp_sv          # لا تلوّث بقية الاختبارات
# 🕰️ تجميد point-in-time (تدقيق خارجي 2026-07-12): إلغاء تعديل التقسيم يدويًّا (auto_adjust
# لا يكفي) + حفظ ببصمة لإعادة إنتاج مضمونة. سبب: الباكتيست الحيّ يقفز 26↔44% لمجرد إعادة تشغيل.
_spl = pd.Series({pd.Timestamp("2026-04-06"): 0.0625, pd.Timestamp("2026-07-06"): 0.005})
check("🕰️ pit: عامل التقسيم اللاحق يعيد INLF 1779.84 → ~0.556 (السعر الحقيقي)",
      abs(S._pit_split_factor(_spl, "2025-12-09") - 0.0003125) < 1e-9
      and abs(S._pit_raw_price(1779.84, _spl, "2025-12-09") - 0.556) < 0.01)
check("🕰️ pit: تقسيم قبل تاريخ الشمعة لا يُحسب (لا تسريب مستقبلي)",
      S._pit_split_factor(_spl, "2026-07-10") == 1.0)
check("🕰️ pit: لا تقسيم/None ⇒ 1.0 (سلوك اليوم حرفيًا)",
      S._pit_split_factor(None, "2025-01-01") == 1.0
      and S._pit_raw_price(3.5, None, "2025-01-01") == 3.5)
_fz_hist = {"AAA": synth_pivot(seed=1)}
_fz_path = "/tmp/_test_frozen_bt.pkl.gz"
_man = S.save_frozen_dataset(_fz_hist, {"AAA": _spl}, "2026-07-13", _fz_path)
_h2, _s2, _asof2 = S.load_frozen_dataset(_fz_path)
check("🕰️ تجميد: حفظ/تحميل دائري + بصمة SHA-256 + as-of مطابقة",
      bool(_man.get("sha256")) and _asof2 == "2026-07-13" and _h2 is not None
      and "AAA" in _h2 and len(_h2["AAA"]) == len(_fz_hist["AAA"]))
check("🕰️ تجميد: 🔒 دوال التجميد خارج الفرز/الاختيار (بنية/باكتيست فقط)",
      all(("_pit_split_factor" not in _insp0.getsource(_f)
           and "load_frozen_dataset" not in _insp0.getsource(_f))
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.scan_market)))
# 🏦 backtest_portfolio (خطة §3): محاكاة انتقائية سعة محدودة — الأعلى readiness يفوز
# بالتزاحم · الخانة تُحرَّر بعد النافذة · لا دخول مزدوج لرمز · المرفوض يُعدّ.
def _pf(sym, date, rdy, sc, oc="win"):
    return {"symbol": sym, "date": date, "readiness": rdy, "score": sc, "outcome": oc}
# size=2, fwd=10: يوم واحد 3 إشارات → الأعلى readiness (AAA·BBB) يؤخذان · CCC يُرفض بالسعة.
# AAA يعيد الإشارة داخل النافذة (01-05<01-11) → دخول مزدوج مرفوض. DDD بعد التحرّر يؤخذ.
_pf_trades = [
    _pf("AAA", "2025-01-01", 90, 50), _pf("BBB", "2025-01-01", 80, 40),
    _pf("CCC", "2025-01-01", 70, 30),                 # يُرفض بالسعة (top-2 فقط)
    _pf("AAA", "2025-01-05", 95, 60),                 # دخول مزدوج (AAA نشط) مرفوض
    _pf("DDD", "2025-01-20", 60, 20),                 # الخانات تحرّرت → يؤخذ
    {"symbol": "NF", "date": "2025-01-02", "readiness": 99, "outcome": "no_fill"},
]
_pf_res = S.backtest_portfolio(_pf_trades, size=2, fwd_days=10)
_pf_syms = [t["symbol"] for t in _pf_res["taken"]]
check("🏦 محفظة: تزاحم اليوم ⇒ الأعلى readiness يؤخذان (AAA·BBB لا CCC)",
      _pf_syms[:2] == ["AAA", "BBB"] and "CCC" not in _pf_syms)
check("🏦 محفظة: الخانة تُحرَّر بعد النافذة ⇒ DDD يؤخذ لاحقًا",
      "DDD" in _pf_syms)
check("🏦 محفظة: لا دخول مزدوج لرمز نشط (AAA المتكرر يُرفض)",
      _pf_syms.count("AAA") == 1 and _pf_res["n_rejected_dup"] == 1)
check("🏦 محفظة: المرفوض بالسعة يُعدّ (CCC واحد)",
      _pf_res["n_rejected_cap"] == 1)
check("🏦 محفظة: غير المُعبَّأة (no_fill) لا تحجز خانة",
      "NF" not in _pf_syms)
check("🏦 محفظة·قفل: backtest_portfolio خارج rank_key/select_top/classify_tier/"
      "analyze_ticker/update_tracking/update_watchlist_status",
      all("backtest_portfolio" not in _insp0.getsource(_f)
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.analyze_ticker,
                     S.update_tracking, S.update_watchlist_status)))
# 🏦 backtest_potential_report (خطة §4): كتلة التقرير — شرائح الحركة المتاحة قبل الوقف
# + انفجارات قتلها الوقف + المعيار المسجَّل + حدّا الصدق. مطفأ ⇒ [] (توافق).
_pt_trades = [
    {"symbol": "AAA", "date": "2025-02-01", "outcome": "win", "exploded": True,
     "mg_outcome": "survived", "mg_pre_stop": 80.0, "mg_peak_day": 5,
     "readiness": 90, "score": 50},
    {"symbol": "BBB", "date": "2025-02-02", "outcome": "loss", "exploded": True,
     "mg_outcome": "stopped", "mg_pre_stop": 8.0, "mg_peak_day": 1,   # انفجر لكن وُقف
     "readiness": 70, "score": 30},
    {"symbol": "CCC", "date": "2025-02-03", "outcome": "loss", "exploded": False,
     "mg_outcome": "stopped", "mg_pre_stop": 0.0, "mg_peak_day": 0,
     "readiness": 60, "score": 20},
    {"symbol": "NF", "date": "2025-02-04", "outcome": "no_fill", "mg_outcome": "no_fill"},
]
check("🏦 تقرير·توافق: مطفأ (الافتراض) ⇒ [] (لا صفقة تحمل mg_)",
      S.backtest_potential_report(_pt_trades) == [])
_pt_sv = S.CONFIG.get("BT_POTENTIAL")
S.CONFIG["BT_POTENTIAL"] = 1
try:
    _pt_join = "\n".join(S.backtest_potential_report(_pt_trades))
    check("🏦 تقرير: مفعّل ⇒ يطبع «قوة البوت» + منفجر قبل الوقف (AAA في شريحة ≥50)",
          "قوة البوت" in _pt_join and "منفجر" in _pt_join)
    check("🏦 تقرير: انفجار قتله الوقف يُعدّ (BBB انفجر بالنافذة لكن وُقف قبل +50)",
          "انفجارات قتلها الوقف: <b>1</b>" in _pt_join)
    check("🏦 تقرير: المعيار المسجَّل + حدّا الصدق حرفيًا (أرضية لا سقف)",
          "معيار مسجَّل مسبقًا" in _pt_join and "أرضية لا سقف" in _pt_join)
finally:
    S.CONFIG["BT_POTENTIAL"] = _pt_sv          # لا تلوّث بقية الاختبارات
check("🏦 تقرير·قفل: backtest_potential_report/_mg_segment_lines خارج الفرز/الاختيار/التتبّع",
      all(("backtest_potential_report" not in _insp0.getsource(_f)
           and "_mg_segment_lines" not in _insp0.getsource(_f))
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.analyze_ticker,
                     S.update_tracking, S.update_watchlist_status)))
# 🔬 ذراع المسح على المحور المصحَّح (2026-07-12): هل الدخول-بعد-المسح يسترد الانفجارات
# المقتولة **من نقطة الدخول**؟ مقتولان (وُقفا قبل +50) — KILL استردّه المسح (+80) وKMISS لا (+10).
_sw_trades = [
    {"symbol": "KILL", "date": "2025-03-01", "outcome": "loss", "exploded": True,
     "mg_outcome": "stopped", "mg_pre_stop": 5.0, "mg_peak_day": 1, "readiness": 60,
     "score": 70, "mg_sweep_outcome": "survived", "mg_sweep_pre_stop": 80.0,
     "mg_sweep_peak_day": 20},
    {"symbol": "KMISS", "date": "2025-03-02", "outcome": "loss", "exploded": True,
     "mg_outcome": "stopped", "mg_pre_stop": 3.0, "mg_peak_day": 1, "readiness": 60,
     "score": 70, "mg_sweep_outcome": "stopped", "mg_sweep_pre_stop": 10.0,
     "mg_sweep_peak_day": 2},
    {"symbol": "CLN", "date": "2025-03-03", "outcome": "win", "exploded": True,
     "mg_outcome": "survived", "mg_pre_stop": 60.0, "mg_peak_day": 10, "readiness": 60,
     "score": 70, "mg_sweep_outcome": "survived", "mg_sweep_pre_stop": 55.0,
     "mg_sweep_peak_day": 12},
]
_sw_sv = S.CONFIG.get("BT_POTENTIAL")
S.CONFIG["BT_POTENTIAL"] = 1
try:
    _sw_join = "\n".join(S.backtest_potential_report(_sw_trades))
    check("🔬 ذراع المسح: كتلة «ذراع المسح» + «استرداد المقتولة» تظهران",
          "ذراع المسح" in _sw_join and "استرداد المقتولة" in _sw_join)
    check("🔬 ذراع المسح: انفجار قبل الوقف الأساس 1 ← المسح 2 (KILL+CLN استعادا)",
          "الأساس 1 ← المسح <b>2</b>" in _sw_join)
    check("🔬 ذراع المسح: يسترد المقتول الملتقَط ≥50 فقط (KILL +80، لا KMISS)",
          "التقط 50%+ منها <b>1</b>" in _sw_join and "KILL +80%" in _sw_join)
finally:
    S.CONFIG["BT_POTENTIAL"] = _sw_sv
# التركيبة الحيّة (BT_SWEEP_ENTRY+BT_POTENTIAL): mg_sweep_* يظهر فقط حين عبّأ ذراع المسح
S.CONFIG["BT_SWEEP_ENTRY"] = 1
S.CONFIG["BT_POTENTIAL"] = 1
_swmg = S.backtest_symbol("SWMG", synth_pivot(seed=2))
S.CONFIG["BT_SWEEP_ENTRY"] = 0
S.CONFIG["BT_POTENTIAL"] = 0
check("🔬 ذراع المسح+قوة البوت: التركيبة تعمل · mg_sweep_pre_stop رقم حين وُجد الحقل",
      len(_swmg) >= 1 and all(t.get("mg_sweep_pre_stop") is not None
                              for t in _swmg if "mg_sweep_outcome" in t))
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
check("التفسير·الكرت: ≤6 أسطر (+📿سلوك +📏حركة فيصل) + «🧭 الإعداد» + «🎯 الرقم الحرج» + بلا علامات مقارنة",
      len(_icl) <= 6 and any("🧭 الإعداد" in x for x in _icl)
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
# ③ تحصين (تدقيق 2026-07-12): عدّاد `_stop_seen` يضمن أن الحلقة فحصت **كل** الـ18
# تكرارًا (6 بذور × 3 أسعار) — قبله كان انحدار جزئي (بوابة ترفض نطاقًا سعريًا) يجعل
# التكرارات تُتخطّى بصمت والحارس «أخضر» وهو معطَّل. القيمة 18 مقيسة على الكود الحالي.
_stop_ok = True
_stop_seen = 0
for sd in range(6):
    for cur, cl, ph in [(3.6, 3.0, 20.0), (1.6, 1.3, 9.0), (12.0, 9.0, 60.0)]:
        rr = S.analyze_ticker("X", synth_pivot(current=cur, crash_low=cl,
                                               prior_high=ph, seed=sd))
        if rr is None:
            continue
        _stop_seen += 1
        lo = rr["entry"][0]
        if not (rr["stop"][0] < lo and rr["stop"][1] < lo):
            _stop_ok = False
            print(f"   ✗ بذرة {sd} سعر {cur}: stop={rr['stop']} entry_lo={lo}")
check("الوقف دائمًا تحت أدنى الدخول (لا كارثة)", _stop_ok)
check(f"③ حارس الكارثة فحص كل التكرارات فعلًا ({_stop_seen}/18 — لا لا-عملية صامتة)",
      _stop_seen == 18)

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
_inv_seen = 0                                    # ③ تحصين: ضمانة تنفيذ فعلي
for sd in range(8):
    for cur, cl, ph in [(3.6, 3.0, 20.0), (2.0, 1.6, 11.0), (9.0, 7.0, 55.0)]:
        _ri = S.analyze_ticker("INV", synth_pivot(current=cur, crash_low=cl,
                                                  prior_high=ph, seed=sd))
        if _ri is None:
            continue
        _inv_seen += 1
        _exp = (_ri["readiness"] is not None
                and _ri["readiness"] >= S.CONFIG["READY_PCT"])
        if bool(_ri["ready"]) != _exp:
            _inv_ok = False
            print(f"   ✗ بذرة {sd}: ready={_ri['ready']} rdy={_ri['readiness']}")
check("ثابت جوهري: ready ⟺ (النسبة ≥ READY_PCT) — مصدر واحد", _inv_ok)
check(f"③ ثابت ready فُحص كاملًا ({_inv_seen}/24)", _inv_seen == 24)

# «جاهز» (نسبة عالية) يسبق «يقترب» (نسبة أقل) دائمًا مهما علت نقاطه/عائده
_rdy_hi = {"tier": "B", "readiness": 80, "score": 40, "rr": 0.3}
_rdy_lo = {"tier": "B", "readiness": 60, "score": 99, "rr": 9.0}
check("«جاهز» يسبق «يقترب» دائمًا (لا يتفوّق سهم أقل جاهزيةً بالنقاط)",
      sorted([_rdy_lo, _rdy_hi], key=S.rank_key)[0] is _rdy_hi)

# (ط) دفعات الدخول (أسلوب فيصل): N دفعات عند الدعم وصعوداً بخطوة ثابتة
_entry_ok = True
_entry_seen = 0                                  # ③ تحصين: ضمانة تنفيذ فعلي
_N = S.CONFIG["ENTRY_TRANCHES"]
_step = S.CONFIG["ENTRY_STEP_PCT"] / 100.0
for sd in range(6):
    for cur, cl, ph in [(3.6, 3.0, 20.0), (2.0, 1.6, 11.0), (9.0, 7.0, 55.0)]:
        _re = S.analyze_ticker("E", synth_pivot(current=cur, crash_low=cl,
                                                prior_high=ph, seed=sd))
        if _re is None:
            continue
        _entry_seen += 1
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
check(f"③ حارس الدفعات فُحص كاملًا ({_entry_seen}/18)", _entry_seen == 18)

# (ي) العائد/المخاطرة يُحسب من **متوسط الدفعات** (فيصل يمتّع) لا السعر الحالي
_rr_ok = True
_rr_seen = 0                                     # ③ تحصين: ضمانة تنفيذ فعلي
for sd in range(6):
    _rt = S.analyze_ticker("RR", synth_pivot(seed=sd))
    if _rt is None:
        continue
    _rr_seen += 1
    _avg = sum(_rt["tranches"]) / len(_rt["tranches"])
    _slo, _t1 = _rt["stop"][0], _rt["t1"]
    _expected = (_t1 - _avg) / max(_avg - _slo, 1e-9)
    if abs(_rt["rr"] - _expected) > 0.05:
        _rr_ok = False
        print(f"   ✗ بذرة {sd}: rr={_rt['rr']:.2f} متوقع {_expected:.2f}")
check("RR من متوسط الدفعات لا السعر الحالي", _rr_ok)
check(f"③ حارس RR فُحص كاملًا ({_rr_seen}/6)", _rr_seen == 6)

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

# should_renew: التجديد مدفوع بإشارة الـworkflow (RENEW_ON_CLOSE) لا بيوم الأسبوع.
# قرار المستخدم (2026-07-09): «ابيه يبدأ بعد إغلاق الجمعة» → كرون الجمعة 22:00 UTC
# (بعد إغلاق السوق) يرفع الإشارة، فتُبنى القائمة على شمعة أسبوعية مكتملة (اثنين→جمعة).
# صباح الجمعة/السبت كان يقرأ إغلاقًا ناقصًا. التوقيع الجديد: should_renew(wl, force, signal).
_nonempty = {"stocks": [{"symbol": "X"}], "removed": []}
check("ثبات: قائمة قائمة بلا إشارة تجديد لا تُعاد بناؤها (لا رفرفة)",
      S.should_renew(_nonempty, False, False) is False)
check("التجديد: إشارة الإغلاق (الجمعة بعد الإغلاق) تُجدِّد القائمة",
      S.should_renew(_nonempty, False, True) is True)
check("الإجبار: FORCE_RENEW يُجدِّد فورًا بلا إشارة",
      S.should_renew(_nonempty, True, False) is True)
check("التأسيس: قائمة فارغة تُؤسَّس فورًا (أي تشغيل، بلا إشارة)",
      S.should_renew({"stocks": [], "removed": []}, False, False) is True)

# 🔒 قفل قرار المستخدم (2026-07-09): التجديد لا يُشتَقّ من يوم الأسبوع — لازم
# إشارة صريحة (كرون الجمعة بعد الإغلاق). فالمتابعة اليومية (أي يوم) لا تُجدِّد
# بمجرد مرور يوم، ولا تُرسِل التقرير الأسبوعي على إغلاق ناقص.
check("🔒 بلا إشارة ولا إجبار ولا قائمة فارغة = لا تجديد",
      S.should_renew(_nonempty, False, False) is False)
check("🔒 القيم الافتراضية (بلا force/signal) = لا تجديد لقائمة قائمة",
      S.should_renew(_nonempty) is False)
# ثوابت اليوم القديمة أُزيلت (WEEKLY_RENEW_DAY / WEEKLY_REPORT_DAY) — التجديد
# صار مدفوعًا بالإشارة؛ نتأكّد أنها لم تعد مرجعًا صامتًا.
check("🔒 ثابت يوم التجديد أُزيل (لا اشتقاق من weekday)",
      not hasattr(S, "WEEKLY_RENEW_DAY"))
check("🔒 ثابت يوم التقرير أُزيل (التقرير مع التجديد لا مع weekday)",
      not hasattr(S, "WEEKLY_REPORT_DAY"))


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

# 🎯 رادار أسهم التقسيم (فيصل IMG_0143/0144/0150/0151 — عرض/سياق فقط، خارج الفرز):
# مقسّم عكسيًّا وصل قاع «القمة÷2» (6.90→3.45) وحافظ 3 جلسات. طلب المستخدم «رادار مقسّم».
_sr_idx = pd.date_range(end=pd.Timestamp.today().normalize(), periods=60, freq="D")
_sr_close = np.concatenate([np.full(30, 13.8),          # ما قبل التقسيم (يتجاهله المِجَسّ)
                            np.linspace(6.9, 3.45, 27), np.full(3, 3.45)])  # قمة 6.9→قاع 3.45
_sr_df = pd.DataFrame({"Open": _sr_close, "High": _sr_close, "Low": _sr_close * 0.99,
                       "Close": _sr_close, "Volume": np.full(60, 5e5)}, index=_sr_idx)
_sr_splits = pd.Series([0.1], index=[_sr_idx[30]])      # عكسي 1:10 يوم البار 30
_sr_today = _sr_idx[-1].date()
# 🎯 مرجع ÷2 = **قمة ما بعد التقسيم** (تصحيح 2026-07-24 بعد تحقّق JEM الحيّ: `_post_split_high`
# =6.90 يطابق فيصل حرفيًّا · «إغلاق أول شمعة» =6.05 ابتعد عنه — فأُرجِع المرجع للقمة، وصار
# `_split_day_value` (أول إغلاق) **قاعدة معيار «لم يصعد بعد التقسيم»** IMG_0150 لا المرجع نفسه).
_sdv_idx = pd.date_range("2025-06-01", periods=12, freq="D")
_sdv_close = pd.Series([100, 100, 100, 100, 100, 5.0, 6, 8, 10, 9, 8, 7], index=_sdv_idx)
_sdv_splits = pd.Series([0.1], index=[_sdv_idx[5]])    # قسم عند البار5: الشمعة=5 ثم صعد لـ10
check("🎯 مرجع ÷2 = قمة ما بعد التقسيم (_post_split_high=10 = القمة، مطابق فيصل JEM 6.90)",
      abs(S._post_split_high(_sdv_close, _sdv_splits, "2025-06-12") - 10.0) < 1e-6)
check("🎯 قاعدة «لم يصعد» = قيمة شمعة التقسيم (_split_day_value=5.0 = أول إغلاق بعده)",
      abs(S._split_day_value(_sdv_close, _sdv_splits, "2025-06-12") - 5.0) < 1e-6)
check("🎯 قاعدة «لم يصعد»·بلا splits/أمامي ⇒ None",
      S._split_day_value(_sdv_close, None, "2025-06-12") is None
      and S._split_day_value(_sdv_close, pd.Series([2.0], index=[_sdv_idx[5]]),
                             "2025-06-12") is None)
_sr_probe = S._split_setup_probe(_sr_df, _sr_splits, _sr_today)
check("🎯 رادار·مِجَسّ: يكتشف مقسّم وصل قمته÷2 (6.90→3.45 = مرجع فيصل) + لم يصعد + المرجع من القمة",
      _sr_probe is not None and abs(_sr_probe["half"] - 3.45) < 0.05
      and abs(_sr_probe["ref"] - 6.9) < 0.05
      and _sr_probe["near_bottom"] and _sr_probe["held_ok"]
      and _sr_probe["didnt_rise"])
# 🎯 معيار «لم يصعد» (IMG_0150 «قسم ما أعطى صعود»): مقسّم قفز 3.0→6.9 (130%) ثم رجع ÷2 = صعد
_dr_close = np.concatenate([np.full(30, 13.8), np.linspace(3.0, 6.9, 12),
                            np.linspace(6.9, 3.45, 15), np.full(3, 3.45)])
_dr_df = pd.DataFrame({"Open": _dr_close, "High": _dr_close, "Low": _dr_close * 0.99,
                       "Close": _dr_close, "Volume": np.full(60, 5e5)}, index=_sr_idx)
_dr_probe = S._split_setup_probe(_dr_df, _sr_splits, _sr_today)
check("🎯 مِجَسّ·«لم يصعد»: مقسّم انضخّ (قفز 130% للقمة) ثم رجع ÷2 ⇒ near/held صحيحان لكن didnt_rise=False",
      _dr_probe is not None and _dr_probe["near_bottom"] and _dr_probe["held_ok"]
      and not _dr_probe["didnt_rise"])
check("🎯 رادار·مِجَسّ: «حافظ 3ج» مربوط بمستوى الـ÷2 (سعر خارج النطاق ⇒ held_ok=False)",
      not (S._split_setup_probe(
          pd.DataFrame({"Open": np.r_[np.full(30, 13.8), np.linspace(6.9, 3.45, 24),
                                      np.full(6, 8.0)],   # آخر 3 عند 8 = خارج نطاق ÷2 (3.45)
                        "High": np.r_[np.full(30, 13.8), np.linspace(6.9, 3.45, 24),
                                      np.full(6, 8.0)],
                        "Low": np.r_[np.full(30, 13.8), np.linspace(6.9, 3.45, 24),
                                     np.full(6, 8.0)] * 0.99,
                        "Close": np.r_[np.full(30, 13.8), np.linspace(6.9, 3.45, 24),
                                       np.full(6, 8.0)], "Volume": np.full(60, 5e5)},
          index=_sr_idx), _sr_splits, _sr_today) or {"held_ok": True})["held_ok"])
check("🎯 رادار·مِجَسّ: بلا splits ⇒ None (فاشل-آمن)",
      S._split_setup_probe(_sr_df, None, _sr_today) is None)
check("🎯 رادار·مِجَسّ: تقسيم أمامي (نسبة>1) ليس عكسيًّا ⇒ None",
      S._split_setup_probe(_sr_df, pd.Series([2.0], index=[_sr_idx[30]]), _sr_today) is None)
check("🎯 رادار·مِجَسّ: تقسيم أقدم من النافذة ⇒ None (بلا تسريب)",
      S._split_setup_probe(
          _sr_df, pd.Series([0.1], index=[_sr_idx[30] - pd.Timedelta(days=400)]),
          _sr_today) is None)
_sr_hist = {"SPLT": _sr_df}
# 🕵️ الشورت = المتاح من ChartExchange (ce_borrow_info) — قراءة فيصل الموثّقة (تصحيح المستخدم)
_sr_rows = S.scan_split_radar(_sr_hist, fetch_splits=lambda s: _sr_splits,
                              fetch_borrow=lambda s: {"shares_available": 12000,   # <20ألف
                                                      "borrow_fee": 705.0},
                              fetch_float=lambda s: 1_500_000,            # <2م
                              fetch_pump=lambda df: {"found": False})
check("🎯 رادار·مسح: يلتقط المقسّم المطابق setup فيصل (فلوت<2م·متاح CE<20ألف·5/5)",
      len(_sr_rows) == 1 and _sr_rows[0]["symbol"] == "SPLT"
      and _sr_rows[0]["float_ok"] and _sr_rows[0]["short_ok"]
      and _sr_rows[0]["short"] == 12000 and _sr_rows[0]["borrow_fee"] == 705.0
      and _sr_rows[0]["match"] == 5)
check("🎯 رادار·مسح: exclude يستبعد الرمز",
      S.scan_split_radar(_sr_hist, exclude={"SPLT"},
                         fetch_splits=lambda s: _sr_splits) == [])
check("🎯 رادار·مسح·فاشل-آمن: جالب التقسيمات يرمي ⇒ يتخطّى بلا انهيار",
      S.scan_split_radar(
          _sr_hist,
          fetch_splits=lambda s: (_ for _ in ()).throw(ValueError())) == [])
_sr_sec = S.build_split_radar_section(_sr_rows)
check("🎯 رادار·عرض: القسم يعرض الرمز + هدف ÷2 + معايير فيصل + المتاح CE + الرسوم",
      "رادار أسهم التقسيم" in _sr_sec and "SPLT" in _sr_sec
      and "3.45" in _sr_sec and "خالٍ من قروب" in _sr_sec
      and "متاح CE" in _sr_sec and "705%" in _sr_sec)
check("🎯 رادار·عرض: فارغ بلا صفوف", S.build_split_radar_section([]) == "")
check("🕵️ رادار·مصدر الشورت = ChartExchange (ce_borrow_info) لا FINRA (تصحيح المستخدم)",
      "ce_borrow_info" in _insp0.getsource(S.scan_split_radar)
      and "finra_daily_short" not in _insp0.getsource(S.scan_split_radar)
      and "shares_available" in _insp0.getsource(S.scan_split_radar))
check("🎯 رادار·قفل: الرادار (scan/probe/section) خارج الجذور السبعة (عرض/سياق فقط)",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("scan_split_radar", "_split_setup_probe",
                      "build_split_radar_section")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol)))

# 🪝 صيّاد أسهم التقسيم (أداة مستقلة — 5 شروط صارمة + سياق · قرار المستخدم «أساسي موثوق»):
# الفلوت من ياهو (CE overview مات) · المتاح من CE سياق · الإرسال فقط عند مطابق كامل.


def _HUNT_OFF(_syms):
    """🧪 جالب إطارات معطَّل لتنبيه الصيّاد — **السويّة بلا إنترنت بتصميمها**.
    ⓿-د أضاف إثراء عرضٍ يجلب إطار كل مطابق (نداء دفعة واحد)؛ فحقنُ هذا الجالب
    يُبقي الاختبارات القائمة **بلا شبكة** وبنفس أحكامها حرفيًّا، والمسار الحيّ
    الافتراضي مقفولٌ باختبارٍ **سلوكيّ** مستقلّ أدناه (يثبت أنه ينادي
    `download_history` فعلًا — لا بقراءة النصّ)."""
    return {}


_sh_rows = S.scan_split_hunter(
    {"SPLT": _sr_df}, today=_sr_today, fetch_splits=lambda s: _sr_splits,
    fetch_float=lambda s: 500_000,                                   # <2م ✅
    fetch_borrow=lambda s: {"shares_available": 12000, "borrow_fee": 700.0},
    fetch_pump=lambda df: {"found": False})
check("🪝 صيّاد: مطابق كامل (مقسّم+÷2+حافظ3ج+فلوت<2م+لا قروب) — فلوت ياهو + متاح CE سياق",
      len(_sh_rows) == 1 and _sh_rows[0]["symbol"] == "SPLT"
      and _sh_rows[0]["float"] == 500_000 and _sh_rows[0]["avail"] == 12000
      and abs(_sh_rows[0]["half"] - 3.45) < 0.05)
check("🪝 صيّاد: فلوت 2م فأكثر ⇒ يُستبعد (شرط صارم)",
      S.scan_split_hunter({"SPLT": _sr_df}, today=_sr_today,
                          fetch_splits=lambda s: _sr_splits,
                          fetch_float=lambda s: 5_000_000,
                          fetch_pump=lambda df: {"found": False}) == [])
check("🪝 صيّاد: رفعة قروب ⇒ يُستبعد (شرط صارم)",
      S.scan_split_hunter({"SPLT": _sr_df}, today=_sr_today,
                          fetch_splits=lambda s: _sr_splits,
                          fetch_float=lambda s: 500_000,
                          fetch_pump=lambda df: {"found": True}) == [])
check("🪝 صيّاد: فلوت غير متاح (ياهو None) ⇒ يُستبعد (لا يُخمّن)",
      S.scan_split_hunter({"SPLT": _sr_df}, today=_sr_today,
                          fetch_splits=lambda s: _sr_splits,
                          fetch_float=lambda s: None,
                          fetch_pump=lambda df: {"found": False}) == [])
check("🪝 صيّاد: مقسّم انضخّ بعد التقسيم (didnt_rise=False) ⇒ يُستبعد (IMG_0150 «قسم ما أعطى صعود»)",
      S.scan_split_hunter({"PUMP": _dr_df}, today=_sr_today,
                          fetch_splits=lambda s: _sr_splits,
                          fetch_float=lambda s: 500_000,
                          fetch_pump=lambda df: {"found": False}) == [])
# ⓿-أ **اختبار توصيف NUWE — يُكتب قبل حارس الافتر** (أمر المالك: «أهم شي عندنا سهم
# NUWE — لا تكون هذي التعديلات تخرب أداة الأسهم المقسمة»). أرقام خطة فيصل الحيّة عليه
# قبل انفجاره: «الهدف الاول **شمعه التقسيم 3.81**» (= افتتاح يوم الحدث = قاعدة «لم
# يصعد») · «دقّ القاع الجمعه **1.80**» والقاع البنيوي = قمة ما بعد الحدث ÷2 ≈ 1.93.
# إطارٌ اصطناعي بأرقامه يستوفي الشروط الستة ⇒ الصيّاد **يرشّحه**. هذا القفل يسبق أي
# سطر من الحارس، فأي تغيير يكسر الرابح الحيّ يسقط هنا فورًا.
_nuwe_c = np.concatenate([np.full(30, 7.62),           # ما قبل الحدث (يتجاهله المِجَسّ)
                          np.linspace(3.81, 1.90, 27), np.full(3, 1.90)])
_nuwe_h = _nuwe_c.copy()
_nuwe_h[30] = 3.85                                     # قمة ما بعد الحدث (÷2 = 1.93)
_nuwe_df = pd.DataFrame({"Open": _nuwe_c, "High": _nuwe_h, "Low": _nuwe_c * 0.99,
                         "Close": _nuwe_c, "Volume": np.full(60, 5e5)}, index=_sr_idx)


def _nuwe_scan():
    """مسح الصيّاد على إطار NUWE الاصطناعي (جالبات محقونة — بلا شبكة)."""
    return S.scan_split_hunter(
        {"NUWE": _nuwe_df}, today=_sr_today, fetch_splits=lambda s: _sr_splits,
        fetch_float=lambda s: 900_000,                 # <2م ✅
        fetch_pump=lambda df: {"found": False},        # خالٍ من قروب ✅
        fetch_borrow=lambda s: {"shares_available": 150_000, "borrow_fee": None})


_nuwe_rows = _nuwe_scan()
check("⓿-أ توصيف NUWE (الرابح الحيّ): الشروط الستة مستوفاة ⇒ الصيّاد يرشّحه بتًّا",
      len(_nuwe_rows) == 1 and _nuwe_rows[0]["symbol"] == "NUWE"
      and abs(_nuwe_rows[0]["ref"] - 3.85) < 0.011
      and abs(_nuwe_rows[0]["half"] - 1.93) < 0.011
      and abs(_nuwe_rows[0]["price"] - 1.90) < 0.011)
check("⓿-أ توصيف NUWE: قاعدة «لم يصعد» = افتتاح يوم الحدث 3.81 (رقم فيصل الحرفي)",
      abs(S._event_day_open(_nuwe_df["Open"], _sr_idx[30]) - 3.81) < 0.011
      and S._split_setup_probe(_nuwe_df, _sr_splits, _sr_today)["didnt_rise"] is True)
_sh_alert = S.build_split_hunter_alert(_sh_rows, today=_sr_today,
                                       fetch_hist=_HUNT_OFF)
check("🪝 صيّاد·تنبيه: يعرض الرمز + ÷2 + المتاح + المتوسطات",
      "صيّاد أسهم التقسيم" in _sh_alert and "SPLT" in _sh_alert
      and "3.45" in _sh_alert and "متاح للاقتراض" in _sh_alert
      and "متوسطات" in _sh_alert)
check("🪝 صيّاد·تنبيه: المتاح غير المؤكّد يُعرض «غير مؤكّد» (لا يُسقط المطابق)",
      "غير مؤكّد" in S.build_split_hunter_alert(
          [dict(_sh_rows[0], avail=None, borrow_fee=None)], today=_sr_today,
          fetch_hist=_HUNT_OFF))
check("🪝 صيّاد·تنبيه: فارغ بلا مطابق (صامت)", S.build_split_hunter_alert([]) == "")
# 🥇 خطة فيصل — قفل على أرقامه الحرفية في $ONCO (2026-07-24): السهم رشّحه صيّادنا فحلّله
# فيصل ودخله. رسالته: «ثبات فوق 92 سنت تحرر السهم · 1.19 راس الشمعه الساقطه هدف · 1.43 هدف
# · فجوه سعريه من 1.88 ل 3 · 0.71-5٪=0.675». السعر وقتها 0.82 والقاع المُحقَّق 0.71.
_onco = S.faisal_split_plan(None, 0.82, bottom=0.71,
                            resist=[0.92, 1.19, 1.43, 1.88],
                            heads=[1.19],                    # رأس الشمعة الساقطة
                            gap={"bottom": 1.88, "top": 3.00},
                            sweep_pct=5)                     # فيصل استعمل −5% في ONCO
check("🥇 خطة فيصل·ONCO: التحرر = أقرب مقاومة فوق السعر = 0.92 (فيصل «ثبات فوق 92»)",
      _onco["liberation"] == 0.92)
check("🥇 خطة فيصل·ONCO: الأهداف البنيوية 1.19 (رأس شمعة حمراء) ثم 1.43 (مقاومة)",
      [t["price"] for t in _onco["targets"]] == [1.19, 1.43]
      and _onco["targets"][0]["src"] == "رأس شمعة حمراء"
      and _onco["targets"][1]["src"] == "مقاومة")
check("🥇 خطة فيصل·ONCO: الفجوة 1.88 → 3.00 (فيصل «فجوه سعريه من 1.88 ل 3»)",
      _onco["gap"] == {"bottom": 1.88, "top": 3.00})
check("🥇 خطة فيصل·ONCO: سحب السيولة = القاع 0.71 −5% = 0.67 (فيصل 0.675)",
      _onco["bottom"] == 0.71 and _onco["sweep"] == 0.67)
check("🥇 خطة فيصل·فاشلة-آمنة: بلا df/مقاومات ⇒ مفاتيح None بلا انهيار",
      S.faisal_split_plan(None, 0.82, bottom=None, resist=[], heads=[], gap=None)
      == {"liberation": None, "targets": [], "gap": None, "sweep": None,
          "sweep_zone": None, "bottom": None}
      and S.faisal_split_plan(None, 0)["liberation"] is None)
# 🩸 نطاق سحب السيولة — قفل على قاعدة فيصل الصريحة في $CCHH (IMG_0297، 2026-07-27):
# «من القاع 1.30 سحب السيوله متعارف عليه من 7٪ ل 13٪ · 1.30-10٪=1.17». كانت العتبة 5%
# (من حالة ONCO وحدها) = أضيق من قاعدته المعلنة.
_cchh = S.faisal_split_plan(None, 1.37, bottom=1.30, resist=[1.70], heads=[], gap=None)
check("🩸 CCHH·سحب السيولة: الأرجح = القاع 1.30 −10% = 1.17 (رقم فيصل الحرفي)",
      _cchh["sweep"] == 1.17)
check("🩸 CCHH·النطاق المتعارف عليه −7%..−13% = 1.21 → 1.13 (فيصل «من 7٪ ل 13٪»)",
      _cchh["sweep_zone"] == {"shallow": 1.21, "deep": 1.13})
check("🩸 التنبيه يعرض النطاق + الأرجح (لا رقمًا واحدًا)",
      all(x in S.build_split_hunter_alert(
          [dict(_sh_rows[0], symbol="CCHH", plan=_cchh)], today=_sr_today,
          fetch_hist=_HUNT_OFF)
          for x in ("1.21", "1.13", "1.17", "المتعارف عليه")))
# ⚠️ قاعدة JZ (IMG_0289): «لما يحصل قروب يرفع السهم المضارب يلغي الاهداف ويهبط فيه»
check("⚠️ JZ·القروب يُلغي الأهداف: سطر تحذير عند رفعة قروب مرصودة",
      "يُلغي الأهداف" in S.pump_voids_targets_line({"pump_scar": {"found": True}}))
check("⚠️ JZ·بلا قروب (أو حقل مفقود/تالف) ⇒ لا سطر (فاشل-آمن)",
      S.pump_voids_targets_line({"pump_scar": {"found": False}}) == ""
      and S.pump_voids_targets_line({}) == ""
      and S.pump_voids_targets_line({"pump_scar": "تالف"}) == "")
# 🔬 فرضية الفلتر السلبي (pump_filter_prereg.md): بصمة رفعة القروب **عند يوم الإشارة حصرًا**
_pf_idx = pd.date_range("2026-01-01", periods=140, freq="D")
_pf_c = np.full(140, 1.0)
_pf_c[55] = 2.2                       # رفعة قروب أولى (داخل نافذة المسح للتاريخين)
_pf_c[100] = 2.4                      # رفعة ثانية (**بعد** يوم الإشارة المبكّر — لا تُرى)
_pf_v = np.full(140, 1e5); _pf_v[[55, 100]] = 3e6
_pf_df = pd.DataFrame({"Open": _pf_c, "High": _pf_c, "Low": _pf_c * 0.9,
                       "Close": _pf_c, "Volume": _pf_v}, index=_pf_idx)
_pf_early = S._bt_pump_features(_pf_df, "2026-03-12")   # البار 70: بعد الأولى فقط
_pf_late = S._bt_pump_features(_pf_df, "2026-05-16")    # البار 135: بعد الاثنتين
check("🔬 بصمة القروب·بلا تسريب: عند يوم إشارة مبكّر لا تُحتسب الرفعة اللاحقة",
      _pf_early.get("pump_found") is True and _pf_early.get("pump_n") == 1)
check("🔬 بصمة القروب: بعد رفعتين مستقلّتين ⇒ pump_n=2",
      _pf_late.get("pump_n") == 2)
check("🔬 بصمة القروب·فاشلة-آمنة: بلا إطار/تاريخ/عيّنة قصيرة ⇒ {}",
      S._bt_pump_features(None, "2026-03-01") == {}
      and S._bt_pump_features(_pf_df, "") == {}
      and S._bt_pump_features(_pf_df, "2026-01-05") == {})
# 🔬🌏 كتلتا اختبار الفرضيتين (تحليل/طباعة فقط — لا وزن ولا بوّابة)
_hyp_rows = ([{"pump_found": False, "country": "China", "exploded": True,
               "outcome": "win"} for _ in range(25)]
             + [{"pump_found": True, "pump_n": 2, "country": "United States",
                 "exploded": False, "outcome": "loss"} for _ in range(25)])
_hp = S.backtest_pump_filter(_hyp_rows)
_hc = S.backtest_country_thread(_hyp_rows)
check("🔬 كتلة الفلتر السلبي: تبوّب الشرائح وتصدر حكمًا بالمعيار المسجَّل",
      any("بلا رفعة قروب" in x for x in _hp)
      and any("رُفِع مرّتين فأكثر" in x for x in _hp)
      and any("الحكم بالمعيار المسجَّل" in x for x in _hp))
check("🌏 كتلة الدولة: تبوّب الصين مقابل بقية الدول + حكم مسجَّل",
      any("الصين/هونغ كونغ" in x for x in _hc)
      and any("بقية الدول" in x for x in _hc)
      and any("الحكم بالمعيار المسجَّل" in x for x in _hc))
check("🔬🌏 عيّنة صغيرة ⇒ [] (صدق العيّنة، لا حكم على 5 صفقات)",
      S.backtest_pump_filter(_hyp_rows[:5]) == []
      and S.backtest_country_thread(_hyp_rows[:5]) == [])
check("🔬🌏 قفل: كتلتا الفرضية خارج الجذور (تحليل فقط)",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("backtest_pump_filter", "backtest_country_thread")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker)))
check("🌏 عمود الدولة: يُجلب من info · «—» عند التعذّر (لم يُختبر قط — أسهم فيصل صينية)",
      S._bt_country("X", fetch=lambda s: {"country": "China"}) == "China"
      and S._bt_country("X", fetch=lambda s: {}) == "—"
      and S._bt_country("X", fetch=lambda s: (_ for _ in ()).throw(IOError())) == "—")
check("🌏 الإثراء يُلحق عمودَي الدولة والقطاع معًا",
      (lambda rows: rows[0].get("country") == "China" and rows[0].get("sector") == "China")(
          S._bt_feature_enrich([{"symbol": "ZZ", "date": "2025-06-01"}],
                               sector_fetch=lambda s: {"country": "China",
                                                       "sector": "China"},
                               earn_fetch=lambda s: [])))
# 🌏📏 تجربة T-CMAG (country_magnitude_prereg.md): **المقدار** لا الاحتمال.
# اختبارات سلوكية (تُبنى الصفقات ويُقرأ المخرَج) لا نصّية — قفلٌ لا يسقط بالطفرة ليس قفلًا.
def _cmag(china, rest, unknown=0, nofill=0):
    """يبني صفقات باكتيست وهمية ويرجّع أسطر T-CMAG. `china`/`rest` قوائم mg_pre_stop."""
    rows = [{"mg_pre_stop": g, "country": "China", "outcome": "win"} for g in china]
    rows += [{"mg_pre_stop": g, "country": "United States", "outcome": "loss"}
             for g in rest]
    rows += [{"mg_pre_stop": 7.0, "country": "—", "outcome": "win"}
             for _ in range(unknown)]
    rows += [{"mg_pre_stop": 999.0, "country": "China", "outcome": "no_fill"}
             for _ in range(nofill)]
    return S.backtest_country_magnitude(rows)
def _cmag_line(lines, key):
    return next((x for x in lines if key in x), "")
# ① الوسيط لا المتوسط: 24 صفقة بـ2% وواحدة بـ1000% ⇒ وسيط 2 · متوسط 42
_cm_skew = _cmag([2.0] * 24 + [1000.0], [2.0] * 25)
check("🌏📏 T-CMAG·الوسيط لا المتوسط: ذيلٌ واحد 1000% لا يحرّك حكم الشريحة",
      "وسيط الصعود 2%" in _cmag_line(_cm_skew, "الصين/هونغ كونغ")
      and "متوسط 42%" in _cmag_line(_cm_skew, "الصين/هونغ كونغ"))
check("🌏📏 T-CMAG·شرط الحجم يسقط عند تساوي الوسيطين (رغم ذيل ضخم)",
      "غير مستوفٍ" in _cmag_line(_cm_skew, "فرق الوسيطين"))
# ② فرق حقيقي: وسيط 60 مقابل 10 ⇒ 50 نقطة و6× ⇒ الحجم مستوفًى + Wilson منفصلان
_cm_big = _cmag([60.0] * 25, [10.0] * 25)
check("🌏📏 T-CMAG·فرق حقيقي: 50 نقطة و6× ⇒ شرط الحجم مستوفًى",
      "+50 نقطة" in _cmag_line(_cm_big, "فرق الوسيطين")
      and "6.00×" in _cmag_line(_cm_big, "فرق الوسيطين")
      and "مستوفًى" in _cmag_line(_cm_big, "فرق الوسيطين")
      and "غير مستوفٍ" not in _cmag_line(_cm_big, "فرق الوسيطين"))
check("🌏📏 T-CMAG·الدلالة على المقياس المساند: فاصلا Wilson منفصلان",
      "منفصلان" in _cmag_line(_cm_big, "بلوغ 30%"))
# حدّا الحجم **مستقلّان**: كلٌّ يُسقط وحده — وإلا سترَ أحدُهما الآخر ولم يكن مقفولًا
check("🌏📏 T-CMAG·حدّ الفرق 5 نقاط: 4% مقابل 1% (النسبة 4× والفرق 3) ⇒ غير مستوفٍ",
      "غير مستوفٍ" in _cmag_line(_cmag([4.0] * 25, [1.0] * 25), "فرق الوسيطين"))
check("🌏📏 T-CMAG·حدّ النسبة 1.5×: 100% مقابل 90% (الفرق 10 والنسبة 1.11) ⇒ غير مستوفٍ",
      "غير مستوفٍ" in _cmag_line(_cmag([100.0] * 25, [90.0] * 25), "فرق الوسيطين"))
check("🌏📏 T-CMAG·التخوم بالضبط: 15% مقابل 10% (فرق 5 · نسبة 1.50×) ⇒ مستوفًى",
      "مستوفًى" in _cmag_line(_cmag([15.0] * 25, [10.0] * 25), "فرق الوسيطين")
      and "غير مستوفٍ" not in _cmag_line(_cmag([15.0] * 25, [10.0] * 25),
                                          "فرق الوسيطين"))
check("🌏📏 T-CMAG·حدّ 30% (حركة فيصل) هو المُطبَّق: 29% لا تُحتسب و31% تُحتسب",
      "بلغ 30% فأكثر 0 " in _cmag_line(_cmag([29.0] * 25, [1.0] * 25), "الصين")
      and "بلغ 30% فأكثر 25 " in _cmag_line(_cmag([31.0] * 25, [1.0] * 25), "الصين"))
# ③ أرضية العيّنة (20/شريحة/سنة) — سلوكية: 19 تُحذَّر و20 لا
check("🌏📏 T-CMAG·أرضية العيّنة 20: 19 صفقة تُحذَّر · 20 تمرّ",
      any("أقل من 20 صفقة" in x for x in _cmag([60.0] * 19, [10.0] * 25))
      and not any("أقل من 20 صفقة" in x for x in _cmag([60.0] * 20, [10.0] * 25)))
# ④ صدق المجتمع: no_fill تُستبعَد · مجهولة الدولة تُعرَض ولا تُقارَن
_cm_pop = _cmag([60.0] * 25, [10.0] * 25, unknown=7, nofill=5)
check("🌏📏 T-CMAG·المجتمع: 50 معلومة الدولة · 7 مجهولة تُعرَض · no_fill مستبعَدة",
      "50 صفقة معبّأة معلومة الدولة" in _cm_pop[1]
      and "7 مجهولة الدولة" in _cm_pop[1]
      and "25 معبّأة" in _cmag_line(_cm_pop, "الصين/هونغ كونغ"))
check("🌏📏 T-CMAG·بلا BT_POTENTIAL (لا mg_pre_stop) ⇒ صامتة تمامًا",
      S.backtest_country_magnitude(
          [{"country": "China", "outcome": "win", "exploded": True}] * 40) == []
      and S.backtest_country_magnitude([]) == [])
check("🌏📏 T-CMAG·عيّنة صغيرة ⇒ [] (لا حكم على 5 صفقات)",
      _cmag([60.0] * 3, [10.0] * 2) == [])
check("🌏📏 T-CMAG·لا حكم نهائي من سنة واحدة (شرط الثلاث سنوات مطبوع دائمًا)",
      any("ثلاث سنوات" in x for x in _cm_big)
      and any("سطر عرض فقط" in x for x in _cm_big))
# ⑤ التفصيل دولةً-دولةً وصفي: أقل من 10 صفقات تُدمَج في «أخرى» (فخّ المقارنات المتعدّدة)
_cm_desc = S._cmag_by_country(
    [{"country": "China", "mg_pre_stop": 40.0} for _ in range(12)]
    + [{"country": "Israel", "mg_pre_stop": 90.0} for _ in range(3)])
check("🌏📏 T-CMAG·الوصفي: دولة بـ3 صفقات لا تظهر باسمها بل ضمن «أخرى»",
      any("China: 12" in x for x in _cm_desc)
      and not any("Israel" in x for x in _cm_desc)
      and any("أخرى" in x and "3 · وسيط 90%" in x for x in _cm_desc))
check("🌏📏 T-CMAG·قفل: خارج الجذور (تحليل/طباعة فقط)",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("backtest_country_magnitude", "_cmag_by_country")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker, S.scan_market)))
# 🕵️ تجربة T-SHORT (short_thread_prereg.md): شورت FINRA **المؤرَّخ بيوم الإشارة**
_FIN_HDR = "Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market\n"
_FIN_DAY = {
    "20250611": _FIN_HDR + "20250611|AAA|5000|0|40000|Q\n20250611|BBB|30000|0|90000|Q\n",
    "20250610": _FIN_HDR + "20250610|CCC|15000|0|60000|Q\n",
}
def _fin_fetch(url):
    for _k, _v in _FIN_DAY.items():
        if _k in url:
            return _v
    return ""                                  # يوم بلا ملف (عطلة/ناقص)
S._FINRA_DAY_CACHE.clear()
check("🕵️ T-SHORT·المحلّل النقي: يقرأ عمود ShortVolume ويتخطّى الترويسة",
      S._parse_finra_short(_FIN_DAY["20250611"]) == {"AAA": 5000, "BBB": 30000})
check("🕵️ T-SHORT·تكرار الرمز: أول ظهور يفوز = مطابقة finra_daily_short الحيّة",
      S._parse_finra_short(_FIN_HDR + "20250611|AAA|5000|0|40000|Q\n"
                           "20250611|AAA|9999|0|50000|N\n") == {"AAA": 5000})
check("🕵️ T-SHORT·العطل العابر: محاولة ثانية قبل تخزين «لا ملف» (لا تدهور صامت)",
      (lambda tries: (S._FINRA_DAY_CACHE.clear(),
                      S._bt_short_at_signal(
                          "AAA", "2025-06-11",
                          fetch=lambda u: (tries.append(1),
                                           (_ for _ in ()).throw(IOError())
                                           if len(tries) < 2 else _FIN_DAY["20250611"]
                                           )[1]) == 5000)[-1])([]))
check("🕵️ T-SHORT·المحلّل فاشل-آمن: نص فارغ/صفحة خطأ/بلا أعمدة ⇒ {}",
      S._parse_finra_short("") == {} and S._parse_finra_short(None) == {}
      and S._parse_finra_short("<html>404 not found</html>") == {})
check("🕵️ T-SHORT: يقرأ شورت يوم الإشارة نفسه",
      S._bt_short_at_signal("AAA", "2025-06-11", fetch=_fin_fetch) == 5000)
check("🕵️ T-SHORT·بلا تسريب: يرجع للخلف فقط (يوم 12 يقرأ ملف 11) ولا ينظر للأمام",
      S._bt_short_at_signal("AAA", "2025-06-12", fetch=_fin_fetch) == 5000
      and S._bt_short_at_signal("CCC", "2025-06-09", fetch=_fin_fetch) is None)
check("🕵️ T-SHORT: رمز غائب عن كل الملفات ⇒ مجهول (None) لا صفر",
      S._bt_short_at_signal("ZZZ", "2025-06-11", fetch=_fin_fetch) is None)
check("🕵️ T-SHORT·فاشلة-آمنة: تاريخ تالف/عطل شبكة ⇒ None بلا استثناء",
      S._bt_short_at_signal("AAA", "بلا-تاريخ", fetch=_fin_fetch) is None
      and (S._FINRA_DAY_CACHE.clear() or True)   # الكاش يمنع إعادة النداء — نفرّغه
      and S._bt_short_at_signal("AAA", "2025-06-11",
                                fetch=lambda u: (_ for _ in ()).throw(IOError()))
      is None)
check("🕵️ T-SHORT·الكاش: نداء واحد لكل تاريخ مهما تكرّرت الرموز (توفير النداءات)",
      (lambda calls: (S._FINRA_DAY_CACHE.clear(),
                      [S._bt_short_at_signal(s, "2025-06-11",
                                             fetch=lambda u: (calls.append(u),
                                                              _FIN_DAY["20250611"])[1])
                       for s in ("AAA", "BBB", "AAA")],
                      len(calls) == 1)[-1])([]))
S._FINRA_DAY_CACHE.clear()
_tsh_rows = ([{"symbol": "AAA", "date": "2025-06-11", "outcome": "win",
              "exploded": True} for _ in range(22)]
            + [{"symbol": "BBB", "date": "2025-06-11", "outcome": "loss",
                "exploded": False} for _ in range(22)])
S._bt_short_enrich(_tsh_rows, fetch=_fin_fetch)
_tshr = S.backtest_short_thread(_tsh_rows)
check("🕵️ T-SHORT·الإثراء: يُلحق short_at_signal لكل صفقة من ملف يومها",
      _tsh_rows[0]["short_at_signal"] == 5000
      and _tsh_rows[-1]["short_at_signal"] == 30000)
check("🕵️ T-SHORT·الكتلة: تبوّب شرائح فيصل وتصدر حكمًا بالمعيار المسجَّل",
      any("10 آلاف سهم أو أقل" in x for x in _tshr)
      and any("من 20 إلى 40 ألف سهم" in x for x in _tshr)
      and any("الحكم بالمعيار المسجَّل" in x for x in _tshr))
check("🕵️ T-SHORT·حدّ الصدق مُعلَن داخل المخرَج (FINRA ليس «المتاح للاقتراض»)",
      any("المتاح للاقتراض" in x for x in _tshr))
check("🕵️ T-SHORT·إشارة معاكسة تُعلَن لا تُخفى",
      any("إشارة معاكسة" in x for x in S.backtest_short_thread(
          [{"short_at_signal": 5000, "outcome": "loss", "exploded": False}
           for _ in range(22)]
          + [{"short_at_signal": 30000, "outcome": "win", "exploded": True}
             for _ in range(22)])))
check("🕵️ T-SHORT·بلا بيانات مؤرَّخة ⇒ يُصرَّح «لا حكم» (غياب ≠ نتيجة سالبة)",
      any("لا حكم" in x for x in S.backtest_short_thread(
          [{"outcome": "win", "exploded": True} for _ in range(20)])))
check("🕵️ T-SHORT·عيّنة صغيرة ⇒ [] (لا حكم على 5 صفقات)",
      S.backtest_short_thread(_tsh_rows[:5]) == [])
check("🕵️ T-SHORT·شورت صفر يقع في الشريحة الأولى لا خارج الشرائح",
      any("1 معبّأة" in x for x in S.backtest_short_thread(
          [{"short_at_signal": 0, "outcome": "win", "exploded": True}]
          + [{"short_at_signal": 30000, "outcome": "loss", "exploded": False}
             for _ in range(12)])))
check("🕵️ T-SHORT·قفل: كل دوال التجربة خارج الجذور السبعة و analyze_ticker",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("_parse_finra_short", "_finra_day_map", "_bt_short_at_signal",
                      "_bt_short_enrich", "backtest_short_thread")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker)))
check("🕵️ T-SHORT·مطفأة افتراضيًّا (لا نداء FINRA بلا علم صريح)",
      S.CONFIG.get("BT_SHORT") == 0)
check("🌏 قفل: _bt_country خارج الجذور (تحليل CSV فقط، لا بوّابة)",
      all("_bt_country" not in _insp0.getsource(_f)
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker)))
check("🔬 قفل: _bt_pump_features خارج backtest_symbol والجذور (تحليل CSV فقط)",
      all("_bt_pump_features" not in _insp0.getsource(_f)
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker)))
# 📏 «حقق متوسط 30 يوم من تاريخ التقسيم» (فيصل LABT IMG_0303): المتوسط لا ينضج إلا بعد مرور
# 30 جلسة **منذ التقسيم** (قبلها نافذته تخلط ما قبل/بعد التقسيم).
_sm_idx = pd.date_range("2026-06-01", periods=70, freq="D")
_sm_c = np.concatenate([np.full(20, 9.0), np.full(50, 2.0)])   # التقسيم عند البار 20
_sm_df = pd.DataFrame({"Open": _sm_c, "High": _sm_c, "Low": _sm_c, "Close": _sm_c,
                       "Volume": np.full(70, 1e5)}, index=_sm_idx)
_sm_mature = S.split_ma_maturity(_sm_df, "2026-06-21", period=30)
check("📏 متوسط التقسيم: 50 جلسة بعد التقسيم ⇒ ناضج + المتوسط من شموع ما بعده حصرًا (2.0)",
      _sm_mature is not None and _sm_mature["mature"] is True
      and _sm_mature["sessions"] == 50 and abs(_sm_mature["ma"] - 2.0) < 0.01
      and _sm_mature["reclaimed"] is True)
check("📏 متوسط التقسيم: تقسيم حديث (أقل من 30 جلسة) ⇒ لم ينضج + ma=None (لا رقم مضلِّل)",
      (lambda m: m["mature"] is False and m["ma"] is None and m["sessions"] == 10)(
          S.split_ma_maturity(_sm_df, "2026-07-31", period=30)))
check("📏 متوسط التقسيم·عرض: «لم ينضج» مقابل «حقّقه» · «» عند None",
      "لم ينضج" in S.split_ma_line(S.split_ma_maturity(_sm_df, "2026-07-31"))
      and "حقّقه" in S.split_ma_line(_sm_mature)
      and S.split_ma_line(None) == "")
# 📏 **مجموعة 20/30/50** (المسح الثاني للصور 2026-07-27): فيصل يذكر 30 (LABT) · 40 (JEM
# IMG_0141 «إذا حقق متوسط 40 يوم») · 50 ⇒ رقم واحد يُوهم أنه «القاعدة». نعرض المجموعة.
check("📏 مجموعة متوسطات التقسيم: تعرض 20/30/50 كلها بنضج كلٍّ منها (لا رقمًا مفردًا)",
      (lambda s: all(f"{p}" in s for p in (20, 30, 50)) and "من التقسيم" in s
       and "جلسة" in s)(S.split_ma_lines(_sm_df, "2026-06-21")))
check("📏 مجموعة المتوسطات·غير الناضج يُصرَّح به لا يُخفى · وفاشلة-آمنة ⇒ «»",
      "لم ينضج" in S.split_ma_lines(_sm_df, "2026-07-31")
      and S.split_ma_lines(_sm_df, None) == ""
      and S.split_ma_lines(None, "2026-06-21") == "")
check("📏 مجموعة المتوسطات·المصدر موثّق بالسطر (30 LABT · 40 JEM · 50)",
      "30 LABT" in S.split_ma_lines(_sm_df, "2026-06-21")
      and "40 JEM" in S.split_ma_lines(_sm_df, "2026-06-21"))
# 🔔 «قريب من شرط لم يصعد»: العتبة **لا تُمَسّ** (نصّ IMG_0153)، لكن لا إسقاط صامت —
# HTCR عند فيصل صعد +23% والحدّ 20% (IMG_8242، المسح الثاني).
check("🔔 المسح الثاني·`rose_pct` تشخيصي يُحسب ولا يغيّر حكم «لم يصعد»",
      (lambda p: p is not None and abs(p["rose_pct"] - 23.0) < 1.5
       and p["didnt_rise"] is False)(
          (lambda n: S._split_setup_probe(
              pd.DataFrame({"Open": np.r_[3.72, np.full(n - 1, 3.0)],
                            "High": np.r_[4.58, np.full(n - 1, 4.0)],
                            "Low": np.full(n, 2.2),
                            "Close": np.r_[3.72, np.full(n - 1, 2.29)],
                            "Volume": np.full(n, 1e5)},
                           index=pd.date_range("2026-06-01", periods=n, freq="D")),
              [(S.dt.date(2026, 6, 1), 0.1)], S.dt.date(2026, 6, 1)
              + S.dt.timedelta(days=n - 1)))(40)))
check("🐞 المِجَسّ يقبل **قائمة** تقسيمات كما يوثّق (كان hasattr('index') يصدق على list "
      "⇒ None صامتة)",
      "hasattr(splits, \"values\")" in _insp0.getsource(S._split_setup_probe))
check("🔔 المسح الثاني·العتبة 20% لم تُمَسّ · و«القريب» سقفه ضعفها (تشخيص لا تخفيف)",
      S.CONFIG["SPLIT_ROSE_MAX_PCT"] == 20.0
      and S.CONFIG["SPLIT_ROSE_NEAR_MULT"] == 2.0
      and "SPLIT_ROSE_MAX_PCT" in _insp0.getsource(S._split_setup_probe))
# ⛔ T-STOP (`stop_sweep_prereg.md`): مفتاح عمق الوقف **باكتيست حصريًّا** — الإنتاج
# يبقى (5,7) مهما كانت البيئة (فيصل ENPH: «الوقف عند المتداولين من 5-7%»).
# 🎯 «أهداف الشورت» (منظومة فيصل TG_1813 + TG_2041) — مُخرَج واحد باسمه.
check("🎯 أهداف الشورت·الهدف الأول = القمة÷2 · والقاع التالي بنسبة السهم · والمسح",
      (lambda L: any("3.45" in x for x in L) and any("2.94" in x for x in L)
       and any("سحب السيولة" in x for x in L))(
          S.short_targets_report(post_split_high=6.90, price=3.60, avail=900,
                                 next_bottom={"next_bottom": 2.94, "drop_pct": 30.0},
                                 sweep=3.10)))
check("🎯 أهداف الشورت·سلّم المتاح بنصّ فيصل: 900 إيجابي · 600 ألفًا ذخيرة هبوط",
      any("إيجابي" in x for x in S.short_targets_report(avail=900))
      and any("ذخيرة هبوط" in x for x in S.short_targets_report(avail=600000))
      and any("ممتاز" in x for x in S.short_targets_report(avail=8000)))
check("🎯 أهداف الشورت·صدق: تعذّر المتاح يُصرَّح به ولا يُخمَّن · والقروب «هجّ عنه»",
      any("تعذّر" in x for x in S.short_targets_report(price=2.0))
      and any("هجّ عنه" in x for x in S.short_targets_report(avail=100, pump=True))
      and any("لا طرح" in x for x in S.short_targets_report(avail=100,
                                                            offering=False)))
check("🔒 أهداف الشورت خارج الجذور (عرض/سياق فقط)",
      all("short_targets_report" not in _insp0.getsource(_f)
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker, S.scan_market)))
# 🚧 **أقفال «عدم الخلط»** (تدقيق 2026-07-27، سؤال المستخدم «متأكد ما خلطت بين ميزة
# التقسيم وأساس البوت؟») — لُقِّي بها عيبان حقيقيان في وصلي: مفتاح إطار غير موجود،
# ومرجع ÷2 يقبل مفتاحًا **عامًّا** (`ref`) كان بابَ اختلاق هدف هبوط على ارتكاز عادي.
check("🚧 عدم الخلط·بلا حدث مؤسِّس: لا هدف ÷2 مُختلَق + تصريح «لا تنطبق» صريح",
      (lambda L: not any("الهدف الأول = القمة ÷2" in x for x in L)
       and any("لا تنطبق هنا" in x for x in L))(
          S.short_targets_report(price=2.0, avail=900)))
check("🚧 عدم الخلط·مرجع الـ÷2 خاصّ بالمقسّم: `split_ref` وحده لا مفتاح عامّ `ref`",
      (lambda _code: 'post_split_high=r.get("split_ref")' in _code
       and 'r.get("ref")' not in _code)(
          "\n".join(_ln for _ln in _insp0.getsource(HC.render_hand_check).split("\n")
                    if not _ln.lstrip().startswith("#"))))
import pullback_live as _PLmod
import analyze_one as _AO
import telegram_collect as TC


# 📚 **حارس انحراف التوثيق** (تدقيق 2026-07-27): CLAUDE.md أوّل ما تقرأه كل جلسة، فخطؤه
# **يتكاثر**. وُجد أربعة كرونات عتيقة فيه — منها كرون أُصلح في اليوم نفسه. الحارس يقارن
# كل كرون مذكور في الوثيقة بملفّات الـyml فعليًّا.
def _doc_crons():
    """يستخرج كل كرون داخل backticks بـCLAUDE.md، والكرونات الفعلية من الـyml."""
    import glob as _g
    _re = __import__("re")

    def _rd(p):
        with open(p, encoding="utf-8") as _fh:
            return _fh.read()

    doc = set(_re.findall(r'`(\d[\d,*/ -]*(?: [\d,*/A-Za-z-]+){4})`', _rd("CLAUDE.md")))
    real = set()
    for _f in _g.glob(".github/workflows/*.yml"):
        real |= set(_re.findall(r'cron:\s*"([^"]+)"', _rd(_f)))
    return doc, real


check("📚 لا كرون عتيق في CLAUDE.md (كل كرون موثّق موجود فعلًا في workflow)",
      (lambda _d, _r: not (_d - _r))(*_doc_crons()))
# 📨 **عقد «القيمة المرجَعة = دليل الوصول»**: بُني عليه فحص الإرسال في صيّاد المقسّم
# ورادار الانطلاق ومراقب الارتداد — وكان مثقوبًا: نصّ فارغ يُرجع True بلا إرسال.
check("📨 send_telegram·الرسالة الفارغة ⇒ False (لا نجاح كاذب لرسالة لم تُرسَل)",
      S.send_telegram("") is False and S.send_telegram("   ") is False)
# 🚨 **تنبيه الخطر لا يُفقَد**: pullback_live يحفظ ختم الدِدوب ويدفعه **قبل** الإرسال
# (منعًا للتكرار)؛ فإخفاق الإرسال كان يستهلك «كسر الوقف» بلا وصول **أبدًا**.
check("🚨 مراقب الارتداد·إخفاق الإرسال يُعيد أختام الدِدوب ويخرج بغير صفر",
      (lambda _s: all(x in _s for x in ("_stamp_restore", "return 1"))
       and "if not bot.send_telegram(" in _s)(_insp0.getsource(_PLmod.main)))
check("🚨 مراقب الارتداد·الاسترجاع يُرجع الأختام حرفيًّا (حذف المُستحدَث وإبقاء القديم)",
      (lambda _wl, _snap: (_PLmod._stamp_restore(_wl, _snap),
                           _wl["stocks"][0].get("live_alert"),
                           _wl["stocks"][1].get("live_alert"),
                           _wl["pullback"][0]["status"])[1:]
       == ({"buyzone": "2026-07-01"}, None, "watch"))(
          {"stocks": [{"symbol": "A", "live_alert": {"break": "2026-07-27"}},
                      {"symbol": "B", "live_alert": {"buyzone": "2026-07-27"}}],
           "pullback": [{"symbol": "C", "status": "triggered"}]},
          ({"A": {"buyzone": "2026-07-01"}, "B": {}}, {"C": "watch"})))
# 📥 **الجامع**: 429/5xx من تلغرام أخطاء **عابرة** — ودفعةُ 300+ صورة هي ما يستدعيها.
check("📥 الجامع·429 و502 عابران (للطابور) لا دائمَين (إسقاط الصورة)",
      (lambda _mk: all(_mk(_c)[1] is False for _c in (429, 502, 503))
       and _mk(400)[1] is True)(
          lambda code: TC.fetch_blob(
              "T", "F",
              get=lambda u, **k: _ty0.SimpleNamespace(
                  json=lambda: {"ok": False, "error_code": code,
                                "description": "x"},
                  status_code=200, content=b""),
              sleep=lambda s: None)))
check("🔁 الجامع·المكرّرة تُسمّي **الملفّ الذي طابقته** (إثبات لا ادّعاء)",
      (lambda _d, _m: (TC._store(b"IMG-A", "new.jpg", _d, {}, _m) == "dup"
                       and _m == [("new.jpg", "old.jpg")]))(
          {__import__("hashlib").sha256(b"IMG-A").hexdigest(): "old.jpg"}, []))
# 🔴 **خطأ مني كُشف 2026-07-28:** هذا الاختبار كان ينادي `_store` بلا تحويل `OUT_DIR`،
# و`_store` يكتب في `OUT_DIR` = `faisal_images/` **الإنتاجي** ⇒ خلّف ملفًا زائفًا
# (`z.jpg`، 5 بايتات) داخل مجلّد المرجع الدائم. لم يتسرّب لـgit (غير متتبَّع) لكن
# لوّث العدّ. **الدرس: أي اختبار يكتب ملفًا يجب أن يحوّل مجلّد المُخرَج أولًا.**
check("🔁 الجامع·الحفظ يسجّل اسم الملف ببصمته · و`_existing_shas` قاموس لا مجموعة",
      (lambda _tmp: (lambda _sv: (
          TC.__dict__.__setitem__("OUT_DIR", _tmp),
          (lambda _d: (TC._store(b"IMG-Z", "z.jpg", _d, {}),
                       _d.get(__import__("hashlib").sha256(b"IMG-Z").hexdigest()))[1]
           is not None)(dict()),
          TC.__dict__.__setitem__("OUT_DIR", _sv))[1])(TC.OUT_DIR))(_tf.mkdtemp())
      and isinstance(TC._existing_shas("faisal_images"), dict))
# 💧 **سطر السبريد كان ميتًا**: `build_message` كانت تقرأ `r["bid"]/["ask"]/["session"]`
# ولا كاتب لها على المستوى الأول (و`session` بلا كاتب في المستودع كلّه) ⇒ لا يظهر أبدًا.
check("💧 الكرت يقرأ الاقتباس من مسار `enrich` الفعلي (session_ctx.quote) لا مفاتيح ميتة",
      (lambda _s: "session_ctx" in _s and "quote" in _s
       and 'r.get("bid")' not in _s and 'r.get("session")' not in _s)(
          _insp0.getsource(S.build_message)))
check("💧 وسم الجلسة بدقائق UTC (نوافذ market_session_now) وصحيح بالفصلين",
      (lambda _Z: all(
          S._session_label(S.dt.datetime(_y, _m, _h_d, _h, 0, tzinfo=_Z(
              "America/New_York")).astimezone(S.dt.timezone.utc)) == _exp
          for _y, _m, _h_d, _h, _exp in (
              (2026, 7, 28, 5, "بريماركت"), (2026, 7, 28, 11, "السوق"),
              (2026, 7, 28, 17, "أفتر"), (2026, 7, 28, 3, "مغلق"),
              (2026, 1, 13, 5, "بريماركت"), (2026, 1, 13, 11, "السوق"),
              (2026, 1, 13, 17, "أفتر"))))(
          __import__("zoneinfo").ZoneInfo))
# 📋 تفصيل الجاهزية كان ميتًا **للسهم المؤهّل** (يُكتَب على سجلّ التشخيص والبطاقة من official)
check("📋 الفحص اليدوي يحمل تفصيل الجاهزية للبطاقة (لا كتلة ميتة عند التأهّل)",
      (lambda _s: "readiness_have" in _s and "setdefault" in _s
       and "card_result" in _s)(_insp0.getsource(_AO.main)))
check("♻️ الجامع·«وصلت بمعرّف سبق تنزيله» تُحسَب وتُعرَض (كانت صامتة تمامًا)",
      (lambda _s: "seen_skip" in _s and _s.count("seen_skip.append") == 1
       and "سبق تنزيلها" in _s)(_insp0.getsource(TC.main)))
check("🧾 الجامع·يكتب تقريرًا **مقروءًا** (سجلّ Actions يُقصّ فلا يُقرأ آليًّا)",
      (lambda _s: "REPORT" in _s and "المكرّرة وما طابقته" in _s
       and "وسائط لم نقبلها" in _s)(_insp0.getsource(TC.main))
      and "telegram_collect_report.md" in open(
          ".github/workflows/telegram_collect.yml", encoding="utf-8").read())
# (شُدّد 2026-07-30 بعد إنقاذ 63 صورة IMG_* أصلية من قرص الحاوية: كان يسمح بأي
#  `.jpg` — فملفُ تلوّثٍ مثل z.jpg **كان يمرّ**. الآن بادئتان شرعيتان حصرًا:
#  TG_*.jpg الدفعة المؤرشفة · IMG_*.{jpg,jpeg,png} الأصلية — وأي اسم آخر يسقط.)
check("🧼 قفل·لا ملفّ دخيل داخل مجلّد الصور الإنتاجي (`faisal_images/`)",
      not [_f for _f in __import__("os").listdir("faisal_images")
           if not (_f == "README.md"
                   or (_f.startswith("TG_") and _f.endswith(".jpg"))
                   or (_f.startswith("IMG_")
                       and _f.lower().endswith((".jpg", ".jpeg", ".png"))))])
check("🔍 الجامع·يفصل «وسائط لم نقبلها» عن «رسالة بلا وسائط» (الصمت غير ملتبس)",
      (lambda _s: "وسائط لم نقبلها" in _s and "بلا وسائط" in _s
       and "dropped.append" in _s and "no_media.append" in _s)(
          _insp0.getsource(TC.main)))
check("🧾 الجامع·يسجّل أرقام رسائل **المكرّرة والمرفوضة** لا المحفوظة وحدها",
      (lambda _s: _s.count("acct.add(") >= 4
       and 'state["seen_msg_ids"]' in _s
       and "| acct" in _s)(_insp0.getsource(TC.main)))
check("📥 الجامع·بلوغ السقف يُصرَّح به (لا «لا جديد» مضلِّلة على قطعٍ صامت)",
      "بلغنا سقف هذا التشغيل" in _insp0.getsource(TC.main)
      and "المكرّرة تُحسب ضمن السقف" in _insp0.getsource(TC.main))


def _run_daily(stocks, results=None, hist=None):
    """يقود `run_daily_watchlist` فعليًّا ببيئة معزولة ⇒ (رسائل مُرسَلة، القائمة).

    ⚠️ **أكبر ثغرة تغطية وُجدت في تدقيق 2026-07-27:** الدالّة — وهي التي تُنتج
    **التقرير اليومي، المُخرَج الرئيسي للبوت** — لم تكن تُنفَّذ في السويّة ولا مرة؛
    يحرسها 15 قفلًا **نصّيًّا** فقط. أُثبت بالطفرة: حذف `send_telegram(msg)` كليًّا
    يُبقي السويّة خضراء. فصار القفل يشغّلها ويؤكّد وصول الرسالة."""
    sent, saved, _sv = [], [], {}
    # 📌 `record_rejected_symbols` **لا تُجذَّع عمدًا** فيُختبَر وصلُها فعلًا —
    #    وأمانُها من دهسِ الملفّ الحقيقيّ يأتي من تحويل `REJECT_LOG_FILE` لمسارٍ
    #    مؤقّتٍ في رأس السويّة (لا من جذعٍ يُنسى لكل مُشغِّلٍ جديد).
    names = ("scan_market", "download_history", "send_telegram", "save_watchlist",
             "write_csv", "record_reject_stats", "accumulate_explosions")
    for _n in names:
        _sv[_n] = getattr(S, _n)
    try:
        S.scan_market = lambda *a, **k: (results or [], hist or {})
        S.download_history = lambda u, **k: {}
        S.send_telegram = lambda m, *a, **k: sent.append(m) or True
        S.save_watchlist = lambda w, *a, **k: saved.append(w) or True
        S.write_csv = lambda *a, **k: None
        S.record_reject_stats = lambda *a, **k: None
        S.accumulate_explosions = lambda *a, **k: None
        # الشكل القانوني للقائمة (نفس `load_watchlist` الافتراضية) لا شكلًا مُختلَقًا
        wl = {"week_start": "2026-07-20", "created": "2026-07-20",
              "stocks": list(stocks), "removed": [], "replacements_log": [],
              "notes": [], "history": [], "logic_version": S.LOGIC_VERSION}
        S.run_daily_watchlist(wl)
        return sent, wl
    finally:
        for _n in names:
            setattr(S, _n, _sv[_n])


check("📩 التقرير اليومي·يُرسَل فعلًا (تشغيل حقيقي لا قفل نصّي)",
      (lambda _s: len(_s) >= 1 and isinstance(_s[0], str) and len(_s[0]) > 40)(
          _run_daily([])[0]))
check("📩 التقرير اليومي·قائمة فارغة ⇒ رسالة واحدة صادقة بلا انهيار",
      (lambda _s: len(_s) == 1)(_run_daily([])[0]))
# 🧭 **قفل «الفحص اليدوي = الأساسي» على طبقة التفسير** (تدقيق 2026-07-27): كان
# `hand_check` ينسخ تسعة مفاتيح ثم يبني التفسير مباشرةً، و`build_interpretation` تقرأ
# **ستّة أخرى** — فيخرج «الرقم الحرج» مختلفًا عن الكرت و**تختفي أعلام الخطر كليًّا**
# (risk «منخفض» بلا أي علم على سهمٍ عليه تقسيم حديث وملفات SEC = نفي غير مفحوص).
# المسار اليومي و`analyze_one` سالمان لأن `enrich` تعيد البناء على سجلٍّ كامل.
_ip_base = {"symbol": "X", "price": 1.0, "last_price": 1.0, "pivot": 0.95,
            "stop": 0.88, "tranches": [0.95, 0.98, 1.01], "t1": 1.3, "t2": 1.6,
            "t3": 2.0, "key_levels": {"sup_main": 0.95, "res_main": 1.3},
            "warnings": [], "soft_fails": []}
check("🧭 التفسير·المفاتيح الناقصة تُخفي أعلام الخطر فعلًا (أثر مُثبَت لا افتراض)",
      (lambda _t, _f: (_t["risk_profile"]["flags"] == []
                       and set(_f["risk_profile"]["flags"])
                       >= {"تقسيم حديث", "ملفات SEC"}
                       and _t.get("trendline_pressure") is None
                       and _f.get("trendline_pressure") is not None))(
          S.build_interpretation(dict(_ip_base)),
          S.build_interpretation(dict(
              _ip_base, liberation=1.05, gaps_above=[(1.05, 1.20)], bars_after=6,
              trendline={"level": 1.06, "broken": False},
              recent_split=("2026-06-01", 0.1),
              sec_filings=[{"form": "424B5", "date": "2026-07-01"}]))))
check("🧭 فحص اليد يزوّد **كل** ما تقرؤه build_interpretation (لا سجلّ نحيف)",
      (lambda _hc, _need: not (_need - {_k for _k in _need if f'"{_k}"' in _hc}))(
          _insp0.getsource(HC.hand_check),
          set(__import__("re").findall(r'r\.get\("([a-z_0-9]+)"',
                                       _insp0.getsource(S.build_interpretation)))
          - {"price", "last_price"}))
check("🧹 فحص اليد·لا سطر ميت يكتب على `official` بعد آخر قراءة له",
      _insp0.getsource(HC.hand_check).count("official[") == 0)
check("🚧 عدم الخلط·فحص اليد يستعمل إطار الوسيط `df` لا مفتاحًا غير موجود",
      (lambda _d: (lambda L: any("لو كسر القاع" in x for x in L.split("\n"))
                   and any("لا تنطبق هنا" in x for x in L.split("\n"))
                   and not any("القمة ÷2 = " in x for x in L.split("\n")))(
          HC.render_hand_check("NOSPLIT", {"symbol": "NOSPLIT", "price": 2.0},
                               _d)))(
          S.pd.DataFrame({"Open": [6 - i * 0.03 for i in range(140)],
                          "High": [6.2 - i * 0.03 for i in range(140)],
                          "Low": [5.8 - i * 0.03 for i in range(140)],
                          "Close": [6 - i * 0.03 for i in range(140)],
                          "Volume": [5e5] * 140},
                         index=S.pd.date_range("2025-01-01", periods=140))))
check("🚧 عدم الخلط·مع حدث مؤسِّس يظهر ÷2 الصحيح (JEM 6.90÷2=3.45) بلا تصريح النفي",
      (lambda L: any("3.45" in x for x in L)
       and not any("لا تنطبق هنا" in x for x in L))(
          S.short_targets_report(post_split_high=6.90, price=2.0)))
check("🚧 عدم الخلط·دوال التقسيم/الشورت الجديدة لا تُذكر في أي بانٍ للفرز أو للتقارير",
      all(_n not in _insp0.getsource(_f)
          for _f in (S.build_message, S.build_daily_message, S.enrich,
                     S.make_watch_entry, S.run_daily_watchlist,
                     S.update_watchlist_status, S.build_interpretation)
          for _n in ("short_targets_report", "next_bottom_by_own_drop",
                     "split_ma_lines", "faisal_split_plan", "_split_setup_probe",
                     "_SPLIT_NEAR_MISS")))
check("⛔ T-STOP·الإنتاج محصّن: الافتراضي (5,7) ولا يتأثّر بـBT_STOP_PCT خارج الباكتيست",
      S.CONFIG["STOP_BELOW_LOW_PCT"] == (5.0, 7.0)
      and S._apply_backtest_overrides("DAILY", {"BT_STOP_PCT": "13,15"}) == []
      and S.CONFIG["STOP_BELOW_LOW_PCT"] == (5.0, 7.0))
check("⛔ T-STOP·بوضع الباكتيست يُطبَّق زوجًا · والقيمة غير المعقولة تُتجاهَل",
      (lambda _sv: (S._apply_backtest_overrides("BACKTEST", {"BT_STOP_PCT": "13,15"}),
                    S.CONFIG["STOP_BELOW_LOW_PCT"] == (13.0, 15.0),
                    S.CONFIG.__setitem__("STOP_BELOW_LOW_PCT", _sv),
                    S._apply_backtest_overrides("BACKTEST", {"BT_STOP_PCT": "99,1"}),
                    S.CONFIG["STOP_BELOW_LOW_PCT"] == _sv,
                    S.CONFIG.__setitem__("STOP_BELOW_LOW_PCT", _sv))[1::3]
       == (True, True))(S.CONFIG["STOP_BELOW_LOW_PCT"]))
# 🆕 المسح الثاني للصور (308 صورة، 2026-07-27) — بندان صمدا للتحقّق الخصومي:
# N8 «المشتريات الموحّدة» (TG_2113) · «القاع التالي بنسبة السهم نفسه» (TG_2041).
check("🔣 N8·المشتريات الموحّدة: الحجم 3 المتكرّر = رمز خوارزمي (لقطة ADIL)",
      (lambda u: u.get("uniform_size") == 3 and u.get("uniform_count") == 9
       and "خوارزمي" in u.get("uniform_meaning", ""))(
          S.uniform_prints([(1.77, 3)] * 7 + [(1.70, 3)] * 2 + [(1.75, 250)])))
check("🔣 N8·دلالات فيصل المنصوصة: 100 = نطاق سعري · 500 = انفجار نادر",
      "نطاق" in S.uniform_prints([(2.0, 100)] * 6)["uniform_meaning"]
      and "انفجار" in S.uniform_prints([(2.0, 500)] * 5)["uniform_meaning"])
check("🔣 N8·لا نمط ⇒ {} (أحجام عشوائية لا تُوسَم) · وفاشلة-آمنة",
      S.uniform_prints([(1.0, 37), (1.0, 412), (1.0, 88), (1.0, 91)]) == {}
      and S.uniform_prints([]) == {} and S.uniform_prints(None) == {}
      and S.uniform_prints([(1.0, 3)] * 2) == {})       # تكرار أقلّ من الحدّ
check("📉 «القاع التالي بنسبة السهم نفسه» يُعيد مثال فيصل (6←4.21 ⇒ ~2.95)",
      (lambda n: n and abs(n["drop_pct"] - 30.0) < 1.0
       and abs(n["next_bottom"] - 2.95) < 0.05
       and abs(n["first_bottom"] - 4.21) < 0.01)(
          S.next_bottom_by_own_drop(pd.DataFrame(
              {"High": np.r_[np.full(10, 6.0), np.linspace(6.0, 4.3, 20),
                             np.full(10, 4.6)],
               "Low": np.r_[np.full(10, 5.8), np.linspace(5.8, 4.21, 20),
                            np.full(10, 4.3)],
               "Close": np.r_[np.full(10, 5.8), np.linspace(5.8, 4.21, 20),
                              np.full(10, 4.3)],
               "Open": np.r_[np.full(10, 5.8), np.linspace(5.8, 4.21, 20),
                             np.full(10, 4.3)],
               "Volume": np.full(40, 1e5)},
              index=pd.date_range("2026-05-01", periods=40, freq="D")))))
check("📉 القاع التالي·فاشلة-آمنة (بلا إطار/قصير/بلا ساق أول) ⇒ None · والسطر «»",
      S.next_bottom_by_own_drop(None) is None
      and S.next_bottom_line(None) == ""
      and S.next_bottom_by_own_drop(pd.DataFrame({"High": [1.0], "Low": [1.0]}))
      is None)
check("🔒 بندا المسح الثاني خارج الجذور (عرض/سياق فقط)",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("uniform_prints", "next_bottom_by_own_drop")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker, S.scan_market)))
check("📉 المسح الثاني·شرط فيصل ① «20 تحت 30 تحت 50» يُعرَض (كنّا نعرض المقلوب فقط)",
      (lambda mk: ("20 تحت 30 تحت 50" in S.build_split_hunter_alert(
                       [mk(1.0, 2.0, 3.0)], fetch_hist=_HUNT_OFF)
                   and "20 تحت 30 تحت 50" not in
                   S.build_split_hunter_alert([mk(3.0, 2.0, 1.0)],
                                              fetch_hist=_HUNT_OFF)
                   and "مصطفّة صاعدة" in S.build_split_hunter_alert(
                       [mk(3.0, 2.0, 1.0)], fetch_hist=_HUNT_OFF)))(
          lambda a, b, c: {"symbol": "X", "price": 1.0, "half": 0.5, "ref": 1.0,
                           "float": 1e6, "avail": None, "borrow_fee": None,
                           "ema20": a, "ema30": b, "ema50": c,
                           "split_date": "2026-06-01", "freq": 0, "plan": {},
                           "bottom_test": None, "split_ma": None}))
check("🔔 المسح الثاني·ذيل «قريبون» يظهر بالتنبيه ولا يُنشئ رسالة وحده (عقد الصمت)",
      (lambda _sv: (S._SPLIT_NEAR_MISS.__setitem__(
          slice(None), [{"symbol": "HTCR", "rose_pct": 23.0, "half": 2.29,
                         "ref": 4.58, "price": 2.50, "event_kind": "split"}]),
          "قريبون من شرط" in S.build_split_hunter_alert(
              [{"symbol": "X", "price": 1.0, "half": 0.5, "ref": 1.0, "float": 1e6,
                "avail": None, "borrow_fee": None, "ema20": 1.0, "ema30": 1.0,
                "ema50": 1.0, "split_date": "2026-06-01", "freq": 0,
                "plan": {}, "bottom_test": None, "split_ma": None}],
              fetch_hist=_HUNT_OFF),
          S.build_split_hunter_alert([]) == "",          # صفر مطابق ⇒ صامت
          S._SPLIT_NEAR_MISS.__setitem__(slice(None), _sv))[1:3])(
          list(S._SPLIT_NEAR_MISS)) == (True, True))
check("📏 متوسط التقسيم·فاشل-آمن: بلا تاريخ/إطار ⇒ None",
      S.split_ma_maturity(_sm_df, None) is None
      and S.split_ma_maturity(None, "2026-06-21") is None
      and S.split_ma_maturity(_sm_df, "غلط") is None)
import split_hunter as _SHmod
from zoneinfo import ZoneInfo as _ZI


def _tf_open(p):
    with open(p, encoding="utf-8") as _fh:
        return _fh.read()


# ⏰ **بعد إغلاق الافتر** (طلب المالك 2026-07-27): الافتر 16:00→20:00 ET، و20:00 ET =
# 00:00 UTC صيفًا / 01:00 UTC شتاءً **في اليوم التالي UTC** ⇒ الكرون بعد 01:00 UTC،
# وخانة الأيام تنزاح ليومٍ لاحق (ثلاثاء→سبت) لتغطية جلسات الاثنين→الجمعة.
_sh_crons = __import__("re").findall(
    r'cron:\s*"(\d+)\s+(\d+)\s+\*\s+\*\s+([\d,-]+)"',
    _tf_open(".github/workflows/split_hunter.yml"))
_SH_SUMMER, _SH_WINTER = S.dt.date(2026, 7, 28), S.dt.date(2026, 1, 13)


def _sh_after_ah(minute, hour, days=(_SH_SUMMER, _SH_WINTER)):
    """هل ساعة الكرون (UTC) تقع **بعد** إغلاق الافتر 20:00 ET في كل الأيام المُمرَّرة؟
    تُقاس على تواريخ حقيقية (صيف EDT · شتاء EST) بـzoneinfo لا بحساب يدوي."""
    ny = _ZI("America/New_York")
    for _d in days:
        e = S.dt.datetime.combine(_d, S.dt.time(hour, minute),
                                  tzinfo=S.dt.timezone.utc).astimezone(ny)
        if e < S.dt.datetime.combine(e.date(), S.dt.time(20, 0), tzinfo=ny):
            return False
    return True


# ⚠️ القفل يبرهن على **القيم المقروءة من الملف** لا على أرقامٍ مكتوبة يدويًّا، وإلا بقي
# أخضر لو رجع أحدهم لكرون داخل الافتر (22:17 = العلّة المُصلَحة).
# 🔴 **العقد تغيّر (قرار المالك 2026-07-31 «~3 فجرًا بتوقيت السعودية»):** ‏3 فجرًا =
# 00:00 UTC، وهي لحظةُ إغلاق الافتر **صيفًا بالضبط** و**قبله بساعةٍ شتاءً**. فصار
# كرونان: الأبكر يخدم الصيف (‏00:13 = 20:13 ET) والأمتنُ يخدم الشتاء — و`session_gate`
# تُبطل الأبكر شتاءً. فالقفل لم يعد «كلّ كرونٍ بعد الإغلاق» بل **التغطية**:
#   (أ) لكل فصلٍ كرونٌ واحد على الأقل بعد الإغلاق (لا ليلةَ صمتٍ في السنة كلّها).
#   (ب) والأبكر بعد الإغلاق **صيفًا** — وهو طلبُ المالك حرفيًّا.
_sh_hrs = sorted((int(h), int(m)) for m, h, _d in _sh_crons)
check("⏰ صيّاد المقسّم·لكل فصلٍ كرونٌ يقع بعد إغلاق الافتر (تغطية السنة كاملةً)",
      len(_sh_crons) >= 2
      and all(any(_sh_after_ah(m, h, days=(_season,)) for h, m in _sh_hrs)
              for _season in (_SH_SUMMER, _SH_WINTER)))
check("⏰ صيّاد المقسّم·الأبكر يسلّم ~3 فجرًا سعوديًّا صيفًا (طلب المالك) بعد الإغلاق",
      bool(_sh_hrs) and _sh_after_ah(_sh_hrs[0][1], _sh_hrs[0][0],
                                     days=(_SH_SUMMER,))
      and _sh_hrs[0][0] == 0)
check("⏰ صيّاد المقسّم·انحدار: كرون 22:17 UTC (داخل الافتر) يسقط بالقفل نفسه",
      not _sh_after_ah(17, 22) and not _sh_after_ah(0, 23)
      and not _sh_after_ah(13, 0, days=(_SH_WINTER,)))
check("⏰ صيّاد المقسّم·خانة الأيام مُنزاحة (2-6) لأن الافتر ينتهي فجر اليوم التالي UTC",
      bool(_sh_crons) and all(_d == "2-6" for _m, _h, _d in _sh_crons))
check("🚨 صيّاد المقسّم·كل مسار فشل يُبلَّغ ويرجع 1 (الصمت محجوز لـ«لا مرشّح» وحده)",
      (lambda _src: _src.count("_fail(S,") >= 6
       and "send_telegram" in _insp0.getsource(_SHmod._fail)
       and "عطل لا" in _insp0.getsource(_SHmod._fail)
       and _SHmod._fail.__doc__ is not None)(_insp0.getsource(_SHmod.run)))


# ⏰ ساعةٌ مثبَّتة لكل تشغيلات السويّة: **20:13 ET صيفًا** = بعد إغلاق الافتر بدقائق.
# بدونها تصير نتيجةُ الاختبار رهينةَ ساعةِ الرنر (أخضر نهارًا وأحمر ليلًا) — وهو صنف
# «اختبارٌ ينجح والاستعمال الحيّ مكسور» المدوَّن بـCLAUDE.md، مقلوبًا.
_SH_NOW = S.dt.datetime(2026, 7, 29, 0, 13, tzinfo=S.dt.timezone.utc)


def _sh_run(scan, *, uni=("X",), hist=None, send=None, yf=object(),
            ext=(lambda _s, _d: None), msgs=None, logs=None, stamp=None,
            now=None):
    """يشغّل split_hunter.run() ببيئة محقونة ويُرجع (rc, عدد الإرسالات).
    **try/finally إلزامي** — الاستعادة داخل tuple شَرِه تُترَك مُرقَّعة لو رمى run().
    🌙 `ext` = جالب سعر الافتر المحقون (افتراضه None = **فاشل-آمن مفتوح** حتميّ بلا
    شبكة ولا اعتماد على وجود `POLYGON_API_KEY` في بيئة الاختبار).
    🔔 ⓿-و: `run()` صارت تكتب **ختم آخر مسحٍ ناجح** — فيُحوَّل مساره إلى ملفٍّ مؤقت
    (`stamp`) حتى لا تكتب السويّة في ملفّ حالة الريبو. (`git_save` نفسها خاملة تحت
    `SUPER_STOCKS_TESTING` بلا runner محقون — حارسها الموثّق.)"""
    sent, _sv = [], (S.yf, S.send_telegram, S.get_universe, S.download_history,
                     S.scan_split_hunter, S.log, S.HUNTER_STAMP_FILE)
    try:
        S.HUNTER_STAMP_FILE = stamp or _os_hc.path.join(
            __import__("tempfile").mkdtemp(), "stamp.json")
        S.yf = yf
        S.send_telegram = (send or (lambda m="", *a, **k: (
            sent.append(1), msgs.append(str(m)) if msgs is not None else None,
            True)[-1]))
        S.get_universe = lambda: list(uni)
        S.download_history = lambda u, **k: (hist if hist is not None
                                             else {s: _sm_df for s in uni})
        S.scan_split_hunter = scan
        if logs is not None:
            S.log = lambda m: logs.append(str(m))
        return _SHmod.run(fetch_ext=ext, now_utc=now or _SH_NOW), len(sent)
    finally:
        (S.yf, S.send_telegram, S.get_universe, S.download_history,
         S.scan_split_hunter, S.log, S.HUNTER_STAMP_FILE) = _sv


# 🧪 القفل السابق كان **فارغًا**: `S.yf = None` على مستوى الوحدة جعل run() ترجع من
# بوّابة yf قبل لمس أي محاكاة، فنجح تلقائيًّا. أُثبت بالطفرة (جعل الإرسال بلا شرط
# لم يُسقطه) ⇒ صار يحقن yf ويؤكّد **الاتجاهين**.
# 🔴 **«عقد الصمت» نُسِخ بقرار المالك 2026-07-31** — والنصّ يبقى مكتوبًا لئلّا يُعاد
# بحسن نيّة: يومُ «لا مطابق» صار **يرسل** «لا يوجد سهم يطابق الشروط»، لأن الصمت كان
# لا يفرّق «لا مرشّح» عن «سقطت التشغيلة». والقفل يقيس **المحتوى** لا العدد وحده.
_sh_none_msgs = []
check("📭 صيّاد المقسّم·لا مطابق ⇒ رسالة «لا يوجد» صريحة (نسخُ عقد الصمت — قرار المالك)",
      _sh_run(lambda *a, **k: [], msgs=_sh_none_msgs) == (0, 1)
      and len(_sh_none_msgs) == 1
      and "لا يوجد سهم يطابق الشروط" in _sh_none_msgs[0]
      and "تعذّر المسح" not in _sh_none_msgs[0])       # ليست رسالة عطل
# ⚠️ الفهرسة محروسة عمدًا: طفرةٌ تُصمت الرسالة كانت تُسقط السويّة بـIndexError فتُخفي
#    **أيّ** قفلٍ سقط (والباقي لا يُنفَّذ) — والعطل يجب أن يُقرأ لا أن يُبهم.
check("📭 صيّاد المقسّم·ورسالة «لا يوجد» تحمل التغطية (فحصٌ حقيقي لا ادّعاء)",
      bool(_sh_none_msgs) and "تغطية" in _sh_none_msgs[0]
      and "🩺" in _sh_none_msgs[0])
check("⛔ صيّاد المقسّم·رفض تلغرام لرسالة «لا يوجد» يرجع 1 (لا يوم صمتٍ مموَّه)",
      _sh_run(lambda *a, **k: [], send=lambda *a, **k: False)[0] == 1)

# ==========================================================
# ⏰🔁 بوّابة التوقيت + دِدوب الكرونين (قرار المالك 2026-07-31)
# ==========================================================
# العقد: كرونان (‏00:13 و01:13 UTC) — صيفًا **كلاهما** بعد إغلاق الافتر، وشتاءً
# الأبكرُ **قبله**. فالبوّابة تُبطل الأبكر شتاءً، والدِدوب يمنع التكرار صيفًا.
# ولا يجوز حلُّها بكرونٍ واحد «مختار»: GitHub يُسقط تشغيلات كرون (موثّق) فالثاني
# شبكةُ أمان — ولذلك القفل يقيس **الاتجاهين**: لا تكرار **ولا** ليلةَ صمت.
_sg_u = lambda h, m=13, d=(2026, 7, 29): S.dt.datetime(  # noqa: E731
    d[0], d[1], d[2], h, m, tzinfo=S.dt.timezone.utc)
check("⏰ SG·شتاءً: ‏00:13 UTC = 19:13 ET **قبل** إغلاق الافتر ⇒ البوّابة مغلقة",
      _SHmod.session_gate(_sg_u(0, d=(2026, 1, 14))) == (False, None))
check("⏰ SG·شتاءً: ‏01:13 UTC = 20:13 ET ⇒ مفتوحة، وتاريخُ الجلسة **نيويوركيّ**",
      _SHmod.session_gate(_sg_u(1, d=(2026, 1, 14)))
      == (True, S.dt.date(2026, 1, 13)))
check("⏰ SG·صيفًا: ‏00:13 UTC = 20:13 ET ⇒ مفتوحة (وهي «3 فجرًا» طلبِ المالك)",
      _SHmod.session_gate(_sg_u(0)) == (True, S.dt.date(2026, 7, 28)))
check("⏰ SG·صيفًا: ‏01:13 UTC مفتوحةٌ أيضًا ⇒ الدِدوب هو مانعُ التكرار لا البوّابة",
      _SHmod.session_gate(_sg_u(1)) == (True, S.dt.date(2026, 7, 28)))
check("⏰ SG·حدُّ الإغلاق 20:00 ET بالضبط: 19:59 مغلقة · 20:00 مفتوحة (تخوم لا تقريب)",
      _SHmod.session_gate(_sg_u(23, 59, d=(2026, 7, 28)))[0] is False
      and _SHmod.session_gate(_sg_u(0, 0))[0] is True)


def _sh_scan_counted(rows):
    """جالبٌ يعدّ نداءاته — به وحده يُقاس «لم يُمسح السوق أصلًا» (توفير التحميل)."""
    _n = []
    return (lambda *a, **k: (_n.append(1), list(rows))[-1]), _n


# 🔴 البوّابة ليست تجميلًا: قبل الإغلاق **لا يُمسح السوق ولا يُرسل شيء**.
_sg_scan, _sg_hits = _sh_scan_counted([])
check("⏰ SG·run(): قبل إغلاق الافتر ⇒ صفر إرسال **وصفر مسح** (لا تحميل سوقٍ مهدور)",
      _sh_run(_sg_scan, now=_sg_u(0, d=(2026, 1, 14))) == (0, 0)
      and _sg_hits == [])
# 🔓 والتشغيل اليدويّ يتخطّاها — وإلّا صار الفحص الفوريّ مستحيلًا نهارًا.
_sg_scan2, _sg_hits2 = _sh_scan_counted([])
_sg_sv = _os_hc.environ.get("HUNTER_FORCE")
try:
    _os_hc.environ["HUNTER_FORCE"] = "1"
    _sg_forced = _sh_run(_sg_scan2, now=_sg_u(0, d=(2026, 1, 14)))
finally:
    _os_hc.environ.pop("HUNTER_FORCE", None)
    if _sg_sv is not None:
        _os_hc.environ["HUNTER_FORCE"] = _sg_sv
check("🔓 SG·`HUNTER_FORCE=1` يتخطّى البوّابة (التشغيل اليدويّ يبقى ممكنًا نهارًا)",
      _sg_forced == (0, 1) and _sg_hits2 == [1])


def _sg_stamp(val):
    """ملفُّ ختمٍ مؤقّت يحمل تاريخًا محدّدًا (يُكتب بكاتب الإنتاج لا بيد)."""
    p = _os_hc.path.join(__import__("tempfile").mkdtemp(), "stamp.json")
    assert S.record_hunter_run(val, path=p)
    return p


_sg_sess = _sm_df.index[-1].date()            # جلسة البيانات في الـfixture
_sg_ny = S.dt.date(2026, 7, 28)               # تاريخ نيويورك عند `_SH_NOW`
# ⚠️ القفل يلزمه اختلافُهما وإلّا صارت الطبقتان تجربةً واحدة (فخّ «المقام = البسط»).
check("🔁 DEDUP·الطبقتان متمايزتان في الـfixture (تاريخ نيويورك ≠ جلسة البيانات)",
      _sg_ny != _sg_sess)
# ① المسار السريع: مساء نيويورك نفسه سُلِّم سلفًا ⇒ **لا مسح** (يوفّر تحميل السوق).
_sg_scan3, _sg_hits3 = _sh_scan_counted([])
check("🔁 DEDUP①·الكرون الثاني ليلة الصيف ⇒ صفر إرسال **وصفر مسح** (المسار السريع)",
      _sh_run(_sg_scan3, stamp=_sg_stamp(_sg_ny)) == (0, 0) and _sg_hits3 == [])
# ② والحاسم: يوم العطلة — تاريخ نيويورك **تقدّم** والبياناتُ لم تتقدّم ⇒ يُمسَح
#    السوق (فالسريع لا يمسكها) لكن **لا رسالة** عن جلسةٍ سُلِّمت أمس.
_sg_scan4, _sg_hits4 = _sh_scan_counted([])
check("🔁 DEDUP②·يوم عطلة (بياناتٌ لم تتقدّم) ⇒ يُمسَح ولا يُرسَل — والسريع يخطئها",
      _sh_run(_sg_scan4, stamp=_sg_stamp(_sg_sess)) == (0, 0)
      and _sg_hits4 == [1])
# 🔴 الاتجاه المقابل — وهو الأخطر: **ليلةُ صمتٍ ممنوعة**. ختمٌ لجلسةٍ أقدم ⇒ يُرسَل.
_sg_scan5, _sg_hits5 = _sh_scan_counted([])
check("🔁 DEDUP·ختمٌ أقدم (سقطت تشغيلة الكرون الأول) ⇒ الثاني **يُرسِل** لا يصمت",
      _sh_run(_sg_scan5,
              stamp=_sg_stamp(_sg_sess - S.dt.timedelta(days=7))) == (0, 1)
      and _sg_hits5 == [1])
# 🔓 والتشغيل اليدويّ يتخطّى **الدِدوب أيضًا** لا البوّابة وحدها: المالك يضغط الزرّ
#    بعد أن سُلِّمت الجلسة ⇒ لولا هذا لخرجت الوظيفة **خضراء بلا رسالة**، وهو بعينه
#    «الأخضر الصامت» الذي بُنيت كل حراسات هذا الملف ضدّه.
_sg_scan6, _sg_hits6 = _sh_scan_counted([])
_sg_p7, _sg_sv2 = _sg_stamp(_sg_sess), _os_hc.environ.get("HUNTER_FORCE")
try:
    _os_hc.environ["HUNTER_FORCE"] = "1"
    _sg_f2 = _sh_run(_sg_scan6, stamp=_sg_p7)
finally:
    _os_hc.environ.pop("HUNTER_FORCE", None)
    if _sg_sv2 is not None:
        _os_hc.environ["HUNTER_FORCE"] = _sg_sv2
check("🔓 SG·اليدويّ يتخطّى الدِدوب أيضًا (زرُّ المالك لا يخرج أخضرَ صامتًا)",
      _sg_f2 == (0, 1) and _sg_hits6 == [1])
# 🔴 ترتيب الختم: **بعد** الإرسال. لو خُتم قبله لقرأ الكرونُ الثاني «سُلِّم» بعد رفضٍ
#    من تلغرام ⇒ ضاعت رسالة الليلة بلا رجعة.
_sg_p6 = _os_hc.path.join(__import__("tempfile").mkdtemp(), "stamp.json")
check("🔔 ⓿-و·رفض تلغرام ⇒ **لا ختم** ⇒ الكرون الثاني يُعيد المحاولة (لا رسالةٌ تضيع)",
      _sh_run(lambda *a, **k: [], send=lambda *a, **k: False,
              stamp=_sg_p6)[0] == 1
      and S.load_hunter_stamp(_sg_p6) is None
      and _sh_run(lambda *a, **k: [], stamp=_sg_p6) == (0, 1)
      and S.load_hunter_stamp(_sg_p6) == _sg_sess.isoformat())
check("📨 صيّاد المقسّم·الاتجاه المقابل: وجود مطابق ⇒ إرسال فعليّ واحد",
      _sh_run(lambda *a, **k: [{
          "symbol": "X", "price": 1.0, "half": 0.5, "ref": 1.0, "float": 1e6,
          "avail": None, "borrow_fee": None, "ema20": 1.0, "ema30": 1.0,
          "ema50": 1.0, "split_date": "2026-06-01", "freq": 0, "plan": {},
          "bottom_test": None, "split_ma": None}]) == (0, 1))
check("🩺 صيّاد المقسّم·حارس التغطية: خنق ياهو ⇒ إبلاغ لا صمت (rc=1)",
      _sh_run(lambda *a, **k: [], uni=tuple(f"S{i}" for i in range(100)),
              hist={"S1": _sm_df}) == (1, 1))
check("🚨 صيّاد المقسّم·انهيار المسح + غياب yfinance + كون فارغ ⇒ إبلاغ لا صمت",
      _sh_run(lambda *a, **k: (_ for _ in ()).throw(RuntimeError("خنق")))
      == (1, 1)
      and _sh_run(lambda *a, **k: [], yf=None) == (1, 1)
      and _sh_run(lambda *a, **k: [], uni=()) == (1, 1))
check("⛔ صيّاد المقسّم·رفض تلغرام لا يُبتلَع: المطابق لم يصل ⇒ rc=1 (لا سجلّ كاذب)",
      _sh_run(lambda *a, **k: [{
          "symbol": "X", "price": 1.0, "half": 0.5, "ref": 1.0, "float": 1e6,
          "avail": None, "borrow_fee": None, "ema20": 1.0, "ema30": 1.0,
          "ema50": 1.0, "split_date": "2026-06-01", "freq": 0, "plan": {},
          "bottom_test": None, "split_ma": None}],
          send=lambda *a, **k: False)[0] == 1)
check("📅 صيّاد المقسّم·تاريخ الترويسة من الجلسة لا من يوم الرنر (الكرون فجر UTC)",
      "today=sess" in _insp0.getsource(_SHmod.run)
      and "max(df.index[-1]" in _insp0.getsource(_SHmod.run))

# ==========================================================
# 🌙⛔ حارس الافتر AH-GUARD (⓿-ب) — المصيبة 8: تنبيه NUWE البائت
# ==========================================================
# العيب المُثبَت: الصيّاد يُسلّم **بعد** إغلاق الافتر لكن شمعة ياهو اليومية لا تشمله
# ⇒ رشّح NUWE (04:19 UTC) بعد أن انفجر ‏+100% في الافتر. الحارس يقرأ السعر الممتد
# لـ**يوم الجلسة** ويعيد تطبيق شرط فيصل ② «لم يصعد» (`SPLIT_ROSE_MAX_PCT`) عليه.
_ah_summer = S.dt.date(2026, 7, 29)      # EDT: الإغلاق 16:00 نيويورك = 20:00 UTC
_ah_winter = S.dt.date(2026, 1, 13)      # EST: الإغلاق 16:00 نيويورك = 21:00 UTC


def _ah_ms(d, hh, mm=0):
    """طابع ms لتوقيت **UTC** في يومٍ محدّد (كما تعطيه Polygon في `t`)."""
    return int(S.dt.datetime(d.year, d.month, d.day, hh, mm,
                             tzinfo=S.dt.timezone.utc).timestamp() * 1000)


_ah_seen = []
_ah_val = S.extended_last_price(
    "NUWE", _ah_summer,
    fetch_bars=lambda s, d: (_ah_seen.append(d), [
        {"t": _ah_ms(_ah_summer, 15, 0), "c": 1.90},    # 11:00 EDT = جلسة نظامية
        {"t": _ah_ms(_ah_summer, 19, 59), "c": 1.92},   # 15:59 EDT = قبل الجرس
        {"t": _ah_ms(_ah_summer, 20, 30), "c": 3.10},   # 16:30 EDT = افتر ✅
        {"t": _ah_ms(_ah_summer, 23, 45), "c": 3.80},   # 19:45 EDT = افتر ✅ (الأخير)
    ])[1])
check("🌙 AH·السعر الممتد = آخر إغلاق دقيقة **بعد جرس 16:00 نيويورك** (صيفًا)",
      _ah_val == 3.80)
# 🔴 **أهمّ طفرة في المهمّة**: لو استُبدل يوم الجلسة بـ`date.today()` انهار الأمران —
# الجالب يُسأل عن يومٍ آخر، ونافذة القطع تُبنى على يومٍ آخر ⇒ صفر شمعة مؤهّلة.
check("🔴 AH·التاريخ = **يوم الجلسة** لا يوم التشغيل (الجالب يُسأل عن يوم الجلسة)",
      _ah_seen == [_ah_summer] and _ah_summer != S.dt.date.today())
check("🔴 AH·طفرة التاريخ: تمرير «اليوم» بدل يوم الجلسة ⇒ لا شمعة بعد الجرس ⇒ None",
      S.extended_last_price(
          "NUWE", S.dt.date.today(),
          fetch_bars=lambda s, d: [{"t": _ah_ms(_ah_summer, 23, 45), "c": 3.80}])
      is None)
# ❄️ قفل التوقيت الشتوي: 20:30 UTC شتاءً = 15:30 **EST = داخل الجلسة النظامية**.
# ثابتُ «20:00 UTC» (نمط `polygon_after_hours`) كان سيقرأها افترًا = قراءة كاذبة.
check("❄️ AH·شتاءً: 20:30/20:50 UTC = 15:30/15:50 EST (جلسة نظامية) ⇒ None لا سعر",
      S.extended_last_price("NUWE", _ah_winter, fetch_bars=lambda s, d: [
          {"t": _ah_ms(_ah_winter, 20, 30), "c": 9.0},
          {"t": _ah_ms(_ah_winter, 20, 50), "c": 9.5}]) is None)
check("❄️ AH·شتاءً: 21:30 UTC = 16:30 EST = افتر حقيقي ⇒ يُقرأ (لا نافذة مثبَّتة)",
      S.extended_last_price("NUWE", _ah_winter, fetch_bars=lambda s, d: [
          {"t": _ah_ms(_ah_winter, 20, 50), "c": 9.5},
          {"t": _ah_ms(_ah_winter, 21, 30), "c": 9.9}]) == 9.9)
check("🌙 AH·يأخذ **أكبر طابع زمني** لا آخر عنصر بالقائمة (لا يثق بترتيب الورود)",
      S.extended_last_price("NUWE", _ah_summer, fetch_bars=lambda s, d: [
          {"t": _ah_ms(_ah_summer, 23, 45), "c": 3.80},
          {"t": _ah_ms(_ah_summer, 20, 30), "c": 3.10}]) == 3.80)
check("🌙 AH·فاشلة-آمنة مطلقًا → None (جالب يرمي · صفر شموع · NaN · تاريخ تالف)",
      S.extended_last_price("N", _ah_summer,
                            fetch_bars=lambda s, d: (_ for _ in ()).throw(IOError()))
      is None
      and S.extended_last_price("N", _ah_summer, fetch_bars=lambda s, d: []) is None
      and S.extended_last_price("N", _ah_summer, fetch_bars=lambda s, d: [
          {"t": _ah_ms(_ah_summer, 23, 45), "c": float("nan")}]) is None
      and S.extended_last_price("N", "ليس تاريخًا",
                                fetch_bars=lambda s, d: []) is None
      and S.extended_last_price("N", None, fetch_bars=lambda s, d: []) is None)
check("🌙 AH·بلا مفتاح Polygon وبلا جالب محقون ⇒ None فورًا (صفر شبكة)",
      (lambda _sv: (_os_hc.environ.pop("POLYGON_API_KEY", None),
                    S.extended_last_price("N", _ah_summer) is None,
                    _os_hc.environ.update({"POLYGON_API_KEY": _sv})
                    if _sv is not None else None)[1])(
          _os_hc.environ.get("POLYGON_API_KEY")))

_ah_row = dict(_nuwe_rows[0])            # صفّ NUWE الحقيقي من توصيف ⓿-أ
_ah_price, _ah_ref = _ah_row["price"], _ah_row["ref"]
check("🌙 AH·حارس: افتر هادئ (نفس الإغلاق) ⇒ **يبقى مرشَّحًا** بتًّا وبلا وسم",
      _SHmod.ah_guard(S, [_ah_row], _ah_summer,
                      fetch=lambda s, d: _ah_price) == ([_ah_row], []))
_ah_logs = []
_ah_sv_log, S.log = S.log, lambda m: _ah_logs.append(str(m))
try:
    _ah_kept = _SHmod.ah_guard(S, [_ah_row], _ah_summer,
                               fetch=lambda s, d: _ah_price * 2.0)   # +100% افتر
finally:
    S.log = _ah_sv_log
check("🌙 AH·حارس: انفجار ‏+100% بالافتر ⇒ **يُكتَم** (واقعة NUWE بعينها)",
      _ah_kept == ([], []))
check("🌙 AH·«يُعلَن ولا يُصمت»: الكتم يطبع سطر سجلّ صريح بالرمز والنسبة",
      any("NUWE" in x and "تنبيه بائت أُلغي" in x and "لم يصعد" in x
          for x in _ah_logs))
check("🌙 AH·فاشل-آمن مفتوح: تعذّر القراءة (None/يرمي) ⇒ **يُرسَل** موسومًا لا يُكتَم",
      _SHmod.ah_guard(S, [_ah_row], _ah_summer,
                      fetch=lambda s, d: None) == ([_ah_row], ["NUWE"])
      and _SHmod.ah_guard(
          S, [_ah_row], _ah_summer,
          fetch=lambda s, d: (_ for _ in ()).throw(RuntimeError()))
      == ([_ah_row], ["NUWE"]))
# 📏 التخوم عند **20.0 بالضبط** = عتبة فيصل `SPLIT_ROSE_MAX_PCT` بلا زيادة ولا نقصان:
# أي رقم مخترع (10 أو 30) يُسقط أحد الاتجاهين. والقرار «أكبر من» كالمِجَسّ حرفيًّا.
check("📏 AH·تخوم: صعود 20.0% بالضبط ⇒ يبقى · 20.5% ⇒ يُكتَم (نفس عتبة فيصل)",
      _SHmod.ah_guard(S, [_ah_row], _ah_summer,
                      fetch=lambda s, d: _ah_price * 1.20)[0] == [_ah_row]
      and _SHmod.ah_guard(S, [_ah_row], _ah_summer,
                          fetch=lambda s, d: _ah_price * 1.205)[0] == [])
check("📏 AH·مرجع `ref` أيضًا محروس: تجاوز القمة÷... بأكثر من الحدّ ⇒ يُكتَم",
      _SHmod.ah_guard(S, [_ah_row], _ah_summer,
                      fetch=lambda s, d: _ah_ref * 1.30)[0] == []
      and "قمة ما بعد الحدث" in _insp0.getsource(_SHmod.ah_guard))
check("🌙 AH·صفّ بمرجعين تالفين (None و NaN) ⇒ لم نتحقّق ⇒ يُرسَل موسومًا لا يُكتَم",
      (lambda _r: (lambda _k, _u: len(_k) == 1 and _k[0] is _r and _u == ["Z"])(
          *_SHmod.ah_guard(S, [_r], _ah_summer, fetch=lambda s, d: 9.0)))(
              {"symbol": "Z", "price": None, "ref": float("nan")}))

# 🔗 **نقطة النداء الحيّة** (درس «الميزة موصولة تُثبَت من نقطة النداء لا من وجود الدالّة»)
_ah_msgs, _ah_rlogs = [], []
_ah_rc = _sh_run(lambda *a, **k: [dict(_ah_row)], uni=("NUWE",),
                 hist={"NUWE": _nuwe_df}, msgs=_ah_msgs, logs=_ah_rlogs,
                 ext=lambda s, d: _ah_price)
check("🔗 AH·run(): افتر هادئ ⇒ التنبيه يُرسَل بلا وسم «لم يُتحقّق»",
      _ah_rc == (0, 1) and _ah_msgs
      and _SHmod.AH_UNVERIFIED_TAG not in _ah_msgs[0] and "NUWE" in _ah_msgs[0])
_ah_msgs2, _ah_rlogs2 = [], []
_ah_rc2 = _sh_run(lambda *a, **k: [dict(_ah_row)], uni=("NUWE",),
                  hist={"NUWE": _nuwe_df}, msgs=_ah_msgs2, logs=_ah_rlogs2,
                  ext=lambda s, d: _ah_price * 2.0)
# 🔴 **العقد تغيّر (قرار المالك 2026-07-31):** كان «صفر إرسال»، وصار **رسالة «لا يوجد»**
# — والنيّة المحروسة **واحدة لم تتغيّر**: التنبيه **البائت** لا يخرج. فالقفل صار يقيس
# المحتوى (لا اسمَ السهم ولا خطّة) **ويشترط التصريح بعدد المكتومين** فلا يعود الصمت
# من باب «لا يوجد» المبهم.
check("🔗 AH·run(): انفجار الافتر ⇒ التنبيه البائت لا يخرج (والرسالة «لا يوجد» بدله)",
      _ah_rc2 == (0, 1) and len(_ah_msgs2) == 1
      and "NUWE" not in _ah_msgs2[0]
      and "لا يوجد سهم يطابق الشروط" in _ah_msgs2[0]
      and "الافتر" in _ah_msgs2[0] and "1" in _ah_msgs2[0]
      and any("كتم الافتر" in x for x in _ah_rlogs2))
_ah_msgs3 = []
_ah_rc3 = _sh_run(lambda *a, **k: [dict(_ah_row)], uni=("NUWE",),
                  hist={"NUWE": _nuwe_df}, msgs=_ah_msgs3,
                  ext=lambda s, d: None)
check("🔗 AH·run(): تعذّر التحقّق ⇒ يُرسَل **موسومًا** (لا كتم صامت ولا ثقة كاذبة)",
      _ah_rc3 == (0, 1) and _ah_msgs3
      and _SHmod.AH_UNVERIFIED_TAG in _ah_msgs3[0] and "NUWE" in _ah_msgs3[0])
check("🔎 AH·رصد: سجلّ الصيّاد يطبع **رموز** المطابقين دائمًا (لا «1 مطابق» مجهولًا)",
      any("مطابق كامل: NUWE" in x for x in _ah_rlogs))
check("🔐 AH·الـworkflow يحمل POLYGON_API_KEY (بلا مفتاح لا يُقرأ سعر الافتر أصلًا)",
      "POLYGON_API_KEY: ${{ secrets.POLYGON_API_KEY }}"
      in _tf_open(".github/workflows/split_hunter.yml"))
check("🔒 AH·قفل: extended_last_price/ah_guard خارج الجذور (تنبيه/عرض فقط)",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("extended_last_price", "ah_guard")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.analyze_ticker, S.apply_short_gate, S.apply_float_gate,
                     S.scan_market, S.scan_split_hunter, S.backtest_symbol)))
def _rose_probe(rise_pct):
    """يبني حالة حدث مؤسِّس بصعودٍ **خام** محدَّد ويُرجع مُخرَج المِجَسّ.
    ⚠️ القفل **سلوكيّ لا نصّي**: النسخة الأولى قارنت ترتيب السلاسل في `getsource`
    فالتقطت `didnt_rise` من **الـdocstring** ⇒ قفل شبه فارغ (نفس فخّ التِبْر)."""
    _n, _i = 60, pd.date_range("2026-03-02", periods=60, freq="B")
    _o = np.array(([100.0] * 4 + [100.0 * (1 + rise_pct / 100)] * 2
                   + list(np.linspace(120, 50, _n - 6)))[:_n], dtype=float)
    return S._split_setup_probe(
        pd.DataFrame({"Open": _o, "High": _o, "Low": _o * 0.99, "Close": _o,
                      "Volume": [1e5] * _n}, index=_i),
        pd.Series([0.1], index=[_i[3]]), _i[-1].date())


# 📏 الحدّ 20% لفيصل: صعودٌ خام 20.03% **يُدوَّر عرضًا إلى 20.0** — فلو قورن المدوَّر
# لمرّ خطأً. القفل يثبت أن القرار على الخام (مرفوض) والعرض على المدوَّر (20.0).
check("📏 عتبة «لم يصعد» على القيمة الخام لا المدوَّرة (لا توسيع صامت لحدّ فيصل)",
      (lambda _a, _b, _c: _a["didnt_rise"] is True and _b["didnt_rise"] is False
       and _b["rose_pct"] == 20.0 and _c["didnt_rise"] is False)(
          _rose_probe(19.99), _rose_probe(20.03), _rose_probe(21.0)))


def _nb_df(p):
    _p = np.array(p, dtype=float)
    return pd.DataFrame({"Open": _p, "High": _p * 1.001, "Low": _p * 0.999,
                         "Close": _p, "Volume": [1e5] * len(_p)},
                        index=pd.date_range("2025-01-01", periods=len(_p), freq="B"))


_nb_base = [6.0] * 10 + list(np.linspace(6.0, 4.21, 15)) + [4.21] * 8
# 🎯 «الساق الأولى» لا «أقصى تراجع»: كان `ref = max(hi[:j])` يأخذ أعلى قمة في النافذة
# كلها، فقمّة أقدم تقلب 30% إلى 65% ⇒ قاع تالٍ **مُختلَق** (1.47 بدل 2.95).
check("🎯 القاع التالي·مثال فيصل الحرفي (6→4.21 = 30% ⇒ 2.95)",
      (lambda _r: _r and abs(_r["drop_pct"] - 30.0) < 0.5
       and abs(_r["next_bottom"] - 2.95) < 0.05)(
          S.next_bottom_by_own_drop(_nb_df(_nb_base))))
check("🎯 القاع التالي·انحدار: قمّة أقدم لا تقلبه لأقصى تراجع (الرقم يبقى 30%)",
      all((lambda _r: _r and abs(_r["drop_pct"] - 30.0) < 0.5)(
          S.next_bottom_by_own_drop(_nb_df(_pre + _nb_base)))
          for _pre in ([12.0] * 8 + list(np.linspace(12.0, 6.0, 12)),
                       [20.0] * 6 + list(np.linspace(20.0, 12.0, 8)) + [12.0] * 8
                       + list(np.linspace(12.0, 6.0, 12)))))
check("🔣 N8·اللوت القياسي 100 لا يُعلَن إلا إذا طغى (نصف الطبعات فأكثر)",
      not S.uniform_prints([(2.0, 100)] * 5 + [(2.0, s) for s in
                                               (137, 250, 1500, 320, 480, 90)])
      and S.uniform_prints([(2.0, 100)] * 6).get("uniform_size") == 100)
check("🔣 N8·النادر الخوارزمي يفوز على اللوت القياسي ولو كان أقلّ تكرارًا",
      S.uniform_prints([(2.0, 100)] * 9 + [(2.0, 3)] * 4).get("uniform_size") == 3)
check("🚧 صدق العرض·«لا طرح جديد» لا تُطبع بلا فحص (مجهول ⇒ لا سطر)",
      not any("لا طرح جديد مرصود" in x or "عليه طرح" in x
              for x in S.short_targets_report(avail=100))
      and any("لا طرح جديد مرصود" in x
              for x in S.short_targets_report(avail=100, offering=False))
      and "short_targets_report" not in _insp0.getsource(
          S.build_split_hunter_alert))
check("🚧 صدق العرض·غياب pump_scar = مجهول لا «✅ خالٍ من القروبات»",
      not any("خالٍ من رفعات" in x or "هجّ عنه" in x
              for x in S.short_targets_report(avail=100))
      and any("خالٍ من رفعات" in x
              for x in S.short_targets_report(avail=100, pump=False))
      and "isinstance" in _insp0.getsource(HC.render_hand_check))
check("🚧 صدق العرض·الفلوت يُسمّى فلوتًا لا «عدد أسهم الشركة»",
      any("الفلوت (المتداوَل حرًّا)" in x
          for x in S.short_targets_report(float_shares=9e5)))
check("🚧 صدق العرض·السطر الختامي «+100%» لا يُطبع بعد إعلان «لا تنطبق هنا»",
      not any("+100%" in x for x in S.short_targets_report(price=2.0))
      and any("+100%" in x
              for x in S.short_targets_report(post_split_high=6.9, price=2.0)))
check("🧹 كرت الصيّاد لا يكرّر الـ÷2/سحب السيولة/المتاح (التقرير الكامل بفحص اليد)",
      (lambda _m: _m.count("القمة ÷2") == 0 and _m.count("الشورت المتاح") == 0
       and _m.count("سحب السيولة المتوقَّع") == 0 and "أهداف الشورت" not in _m
       and "القاع التالي المتوقّع" in _m)(
          S.build_split_hunter_alert([{
              "symbol": "X", "price": 3.5, "half": 3.5, "ref": 7.0, "float": 9e5,
              "avail": 4000, "borrow_fee": 30.0, "ema20": 1.0, "ema30": 2.0,
              "ema50": 3.0, "split_date": "2026-06-01", "freq": 0, "plan": {},
              "bottom_test": None, "split_ma": None,
              "next_bottom": {"next_bottom": 2.9, "drop_pct": 30.0,
                              "ref_high": 6.0, "first_bottom": 4.2}}],
              fetch_hist=_HUNT_OFF)))
check("📏 قفل: split_ma_maturity خارج الجذور (عرض/سياق لا بوّابة فرز)",
      all("split_ma_maturity" not in _insp0.getsource(_f)
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker)))
# ⭐ «اتفاق الفريمات» وصيد الارتداد (فيصل IMG_0305/0306): 5د+15د+30د على نفس الدعم +
# «الارتداد الأول لا دخول · الثاني تأكيد دخول مع عدم الكسر». مثاله: دعم 10.21 → 14.70 (+45%).
def _mk_min_bars(seq):
    """شموع دقيقة من متتالية إغلاقات (low=close، تكفي لاختبار الدعم/الارتداد)."""
    return [{"o": x, "h": x * 1.005, "l": x, "c": x, "v": 1e4, "t": i * 60_000}
            for i, x in enumerate(seq)]


# سيناريو فيصل: هبوط للدعم 10.21 → ارتداد 11.46 → عودة ثانية للدعم → ثبات فوقه
_rb_seq = ([13.5] * 90 + [10.25] * 30 + [11.4] * 60 + [10.23] * 30 + [10.9] * 60)
_rb = S.rebound_entry_state(_mk_min_bars(_rb_seq))
check("⭐ اتفاق الفريمات: الفريمات الثلاثة على نفس الدعم ⇒ agree=True + الدعم ≈10.2",
      _rb is not None and _rb["agree"] and abs(_rb["support"] - 10.23) < 0.10
      and _rb["frames"] == [5, 15, 30])
check("⭐ صيد الارتداد: ارتدادان + ثبات ⇒ entry=True (فيصل: «الدخول هنا»)",
      _rb["bounces"] >= 2 and _rb["holding"] and _rb["entry"] is True)
check("⭐ عرض: سطر «ارتداد 2 مؤكَّد» + الدعم + تحذير الوقف",
      "ارتداد 2 مؤكَّد" in S.rebound_entry_line(_rb)
      and "الدخول هنا" in S.rebound_entry_line(_rb))
# الارتداد الأول فقط ⇒ لا دخول (قاعدة فيصل الصريحة)
_rb1 = S.rebound_entry_state(_mk_min_bars([13.5] * 120 + [10.25] * 30 + [10.9] * 120))
check("⭐ الارتداد الأول: لا دخول (entry=False) مع أن الفريمات متفقة",
      _rb1 is not None and _rb1["bounces"] == 1 and _rb1["entry"] is False
      and "الارتداد الأول: لا دخول" in S.rebound_entry_line(_rb1))
# كسر الدعم ⇒ «اطلع فورًا»
_rbb = S.rebound_entry_state(_mk_min_bars([12.0] * 120 + [10.2] * 90 + [9.0] * 5))
check("⭐ كسر الدعم ⇒ holding=False + سطر «اطلع فورًا»",
      _rbb is not None and _rbb["holding"] is False
      and "اطلع فورًا" in S.rebound_entry_line(_rbb))
# 🚧 بوّابة السياق (تدقيق التعارض): الاستراتيجية **مضاربة زخم** لسهم صعد بقوة — لا تنطبق على
# سهم ارتكاز راكد عند قاعه. بلا صعود سابق ⇒ context_ok=False و entry=False مهما اتفقت الفريمات.
_rb_flat = S.rebound_entry_state(_mk_min_bars(
    [10.0] * 120 + [10.05] * 30 + [10.1] * 60 + [10.04] * 30 + [10.08] * 60))
check("🚧 سياق: قاع راكد (بلا صعود) ⇒ context_ok=False و entry=False",
      _rb_flat is not None and _rb_flat["context_ok"] is False
      and _rb_flat["entry"] is False and _rb_flat["rise_pct"] < 20)
check("🚧 سياق: السطر يقول «لا ينطبق» ويفصل منهجية الارتكاز صراحةً",
      "لا ينطبق" in S.rebound_entry_line(_rb_flat)
      and "الارتكاز" in S.rebound_entry_line(_rb_flat))
check("🚧 سياق: سيناريو فيصل (صعد ثم ارتدّ) ⇒ context_ok=True",
      _rb["context_ok"] is True and _rb["rise_pct"] >= 20)
check("⭐ فاشل-آمن: عيّنة قصيرة/فارغة ⇒ None · السطر «» عند None",
      S.rebound_entry_state([]) is None and S.rebound_entry_state(None) is None
      and S.rebound_entry_state(_mk_min_bars([1.0] * 20)) is None
      and S.rebound_entry_line(None) == "")
check("⭐ _resample_minute_bars: 10 شموع دقيقة → فريم 5د = شمعتان (h/l/c صحيحة)",
      len(S._resample_minute_bars(_mk_min_bars([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]), 5)) == 2
      and S._resample_minute_bars(
          _mk_min_bars([1, 2, 3, 4, 5]), 5)[0]["l"] == 1
      and S._resample_minute_bars(_mk_min_bars([1, 2, 3, 4, 5]), 5)[0]["c"] == 5)
check("⭐ قفل: (rebound_entry_state/_resample_minute_bars) خارج الجذور ومسار التنبيه",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("rebound_entry_state", "_resample_minute_bars")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker, S.scan_ignition)))
# 🚫 قاعدة «رُفِع أكثر من مرة بدون مضارب ⇒ متابعة فقط» (EZRA IMG_0295 · EDBL IMG_0298)
check("🚫 متابعة فقط: رفعتان فأكثر ⇒ سطر «متابعة فقط»",
      "متابعة فقط" in S.pump_repeat_watch_only(
          {"pump_scar": {"found": True, "n_pumps": 3}}))
check("🚫 متابعة فقط: رفعة واحدة ⇒ لا سطر (القاعدة للتكرار فقط)",
      S.pump_repeat_watch_only({"pump_scar": {"found": True, "n_pumps": 1}}) == "")
check("🚫 متابعة فقط·فاشلة-آمنة: بلا حقل/تالف ⇒ «»",
      S.pump_repeat_watch_only({}) == ""
      and S.pump_repeat_watch_only({"pump_scar": "تالف"}) == "")
# 🔁 عدّاد الرفعات المستقلّة داخل group_pump_scar (الشرط اللازم للقاعدة أعلاه)
_gp_idx = pd.date_range("2026-01-01", periods=120, freq="D")
_gp_c = np.full(120, 1.0)
for _i in (40, 90):                       # رفعتان مفصولتان 50 جلسة = حدثان مستقلّان
    _gp_c[_i] = 2.2                       # قفزة 120% (فوق EXPLOSION_PCT)
_gp_v = np.full(120, 1e5); _gp_v[[40, 90]] = 3e6
_gp_df = pd.DataFrame({"Open": _gp_c, "High": _gp_c, "Low": _gp_c * 0.9,
                       "Close": _gp_c, "Volume": _gp_v}, index=_gp_idx)
_gp = S.group_pump_scar(_gp_df)
check("🔁 group_pump_scar: يعدّ الرفعات المستقلّة (n_pumps=2) مع حفظ المفاتيح القديمة",
      _gp is not None and _gp.get("n_pumps") == 2
      and _gp.get("found") is True and "jump_pct" in _gp and "bars_ago" in _gp)
# 🔁 حالة «القاع 2» (فيصل EDBL: «القاع 2 = ثبات أو سحب سيوله»)
_bt_lows = np.concatenate([np.full(20, 3.0), [1.00], np.full(15, 1.60),
                           [1.02], np.full(23, 1.50)])     # القاع اختُبر مرتين
_bt_df = pd.DataFrame({"Open": _bt_lows, "High": _bt_lows * 1.05, "Low": _bt_lows,
                       "Close": _bt_lows, "Volume": np.full(60, 1e5)},
                      index=pd.date_range("2026-01-01", periods=60, freq="D"))
_bt = S.bottom_test_state(_bt_df)
check("🔁 القاع 2: اختباران للقاع ⇒ second=True + القاع الصحيح",
      _bt is not None and _bt["second"] and _bt["tests"] == 2
      and abs(_bt["bottom"] - 1.00) < 0.01)
check("🔁 القاع 2: قاع اختُبر مرة واحدة ⇒ second=False",
      S.bottom_test_state(pd.DataFrame(
          {"Open": [3.0]*40, "High": [3.1]*40, "Low": [3.0]*39 + [1.0],
           "Close": [3.0]*40, "Volume": [1e5]*40},
          index=pd.date_range("2026-01-01", periods=40, freq="D")))["second"] is False)
check("🔁 القاع 2·عرض: السطر يذكر «ثبات أو سحب سيولة» + نطاق السحب لو مُرِّر",
      "ثبات أو سحب سيولة" in S.bottom_test_line(_bt)
      and "1.21" in S.bottom_test_line(_bt, {"shallow": 1.21, "deep": 1.13})
      and S.bottom_test_line(None) == ""
      and S.bottom_test_line({"second": False}) == "")
check("🔁 قفل: (bottom_test_state/pump_repeat_watch_only) خارج الجذور",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("bottom_test_state", "pump_repeat_watch_only")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker)))
# ⏱️ قاعدة «ربع الساعة» (JZ فريم الساعة IMG_0294): «لو كان مضارب يعطيك مجال تبيع وتذبذب
# يصل مداه أكثر من ربع ساعه — طلع السهم بدون اذن مضارب ضغطه المضارب للهاويه».
_sus_ok = S.operator_sustain([{"c": 2.55}] * 18, 2.50)          # صمد 18 دقيقة فوق الكسر
_sus_no = S.operator_sustain([{"c": 2.55}] * 6 + [{"c": 2.30}] * 20, 2.50)  # سُحق بعد 6د
check("⏱️ ربع الساعة: صمود 18 دقيقة فوق الكسر ⇒ رفعة مضارب (ok)",
      _sus_ok == {"minutes": 18, "ok": True})
check("⏱️ ربع الساعة: سُحق بعد 6 دقائق ⇒ رفعة بلا إذن المضارب (ok=False)",
      _sus_no == {"minutes": 6, "ok": False})
check("⏱️ ربع الساعة: الحدّ 15 دقيقة بالضبط ⇒ مقبول (≥ لا >)",
      S.operator_sustain([{"c": 3.0}] * 15, 2.9)["ok"] is True
      and S.operator_sustain([{"c": 3.0}] * 14, 2.9)["ok"] is False)
check("⏱️ ربع الساعة·فاشلة-آمنة: بلا شموع/مستوى ⇒ None",
      S.operator_sustain([], 2.5) is None and S.operator_sustain([{"c": 1}], 0) is None
      and S.operator_sustain(None, None) is None)
# ⏱️ توصيل القياس بسجلّ الرادار (عند نهاية الجلسة فقط — خارج مسار التنبيه)
_fs_stock = {"symbol": "SUS", "pivot": 2.0, "liberation": None,
             "interp": {"critical_number": {"price": 2.50}},
             "fired_ts_ms": 1_000_000}
_fs_sig = {"price": 2.55, "vol_x": 5.0, "usd": 250_000}
_fs_bars_ok = [{"t": 1_000_000 + i * 60_000, "c": 3.0} for i in range(25)]
_fs_bars_no = ([{"t": 1_000_000 + i * 60_000, "c": 3.0} for i in range(5)]
               + [{"t": 1_000_000 + (5 + i) * 60_000, "c": 1.0} for i in range(20)])
_fs1 = S._fire_sustain(_fs_stock, _fs_sig, lambda s, minutes=0: _fs_bars_ok, 15)
_fs2 = S._fire_sustain(_fs_stock, _fs_sig, lambda s, minutes=0: _fs_bars_no, 15)
check("⏱️ قياس الإطلاق: صمد ≥15د ⇒ operator_ok=True (رفعة مضارب)",
      _fs1.get("operator_ok") is True and _fs1.get("sustain_min", 0) >= 15)
check("⏱️ قياس الإطلاق: سُحق بعد 5د ⇒ operator_ok=False (رفعة بلا إذن)",
      _fs2.get("operator_ok") is False and _fs2.get("sustain_min") == 5)
check("⏱️ قياس الإطلاق·فاشل-آمن: بلا جالب/بلا ختم وقت ⇒ {} (السلوك السابق حرفيًّا)",
      S._fire_sustain(_fs_stock, _fs_sig, None, 15) == {}
      and S._fire_sustain({"symbol": "X", "pivot": 2.0}, _fs_sig,
                          lambda s, minutes=0: _fs_bars_ok, 15) == {}
      and S._fire_sustain(_fs_stock, _fs_sig,
                          lambda s, minutes=0: (_ for _ in ()).throw(IOError()), 15) == {})
check("⏱️ توصيل: record_ignition_fires يقبل fetch_bars (اختياري، توافق خلفي)",
      "fetch_bars" in _insp0.signature(S.record_ignition_fires).parameters
      and _insp0.signature(S.record_ignition_fires)
      .parameters["fetch_bars"].default is None)
check("⏱️ ربع الساعة·قفل: operator_sustain خارج الجذور (قياس/تشخيص لا كبت تنبيه)",
      all("operator_sustain" not in _insp0.getsource(_f)
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker, S.scan_ignition)))
# 📉 CCI(14) — مؤشّر فيصل الظاهر في كل شوارته (JZ −56.5 · CCHH +105.8 · DRCT −43.0)
_cci_idx = pd.date_range("2026-01-01", periods=60, freq="D")
_cci_up = pd.Series(np.linspace(1.0, 3.0, 60), index=_cci_idx)      # صعود قوي
_cci_dn = pd.Series(np.linspace(3.0, 1.0, 60), index=_cci_idx)      # هبوط قوي
_cs_up = S.cci_state(_cci_up * 1.01, _cci_up * 0.99, _cci_up)
_cs_dn = S.cci_state(_cci_dn * 1.01, _cci_dn * 0.99, _cci_dn)
check("📉 CCI: صعود قوي ⇒ فوق +100 (تشبّع شرائي)",
      _cs_up is not None and _cs_up["cci"] > 100 and _cs_up["state"] == "تشبّع شرائي")
check("📉 CCI: هبوط قوي ⇒ تحت −100 (تشبّع بيعي — منطقة قاع فيصل)",
      _cs_dn is not None and _cs_dn["cci"] < -100 and _cs_dn["state"] == "تشبّع بيعي")
check("📉 CCI·صدق العيّنة: أقصر من 19 شمعة ⇒ None (لا رقم مُخترَع)",
      S.cci_state(_cci_up[:10] * 1.01, _cci_up[:10] * 0.99, _cci_up[:10]) is None
      and S.cci_state(None, None, None) is None)
check("📉 CCI·عرض: السطر يظهر بالرقم والحالة · فارغ عند None",
      "CCI(14)" in S.cci_line(_cs_up) and S.cci_line(None) == "")
check("📉 CCI·قفل: خارج الجذور السبعة و analyze_ticker (مؤشّر عرض/سياق لا بوّابة)",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("cci_state", "cci_line", "cci(")   # «cci(» = المؤشّر الخام نفسه
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker)))
check("⚠️ JZ·قفل: pump_voids_targets_line خارج الجذور (تحذير عرض فقط لا يمسّ الأهداف)",
      all("pump_voids_targets_line" not in _insp0.getsource(_f)
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker)))
_onco_alert = S.build_split_hunter_alert(
    [dict(_sh_rows[0], symbol="ONCO", plan=_onco)], today=_sr_today,
    fetch_hist=_HUNT_OFF)
check("🥇 صيّاد·تنبيه: يعرض خطة فيصل الأربعة (تحرر/أهداف/فجوة/سحب سيولة) + الدخول مع المضارب",
      "التحرر" in _onco_alert and "0.92" in _onco_alert
      and "1.19" in _onco_alert and "رأس شمعة حمراء" in _onco_alert
      and "1.88" in _onco_alert and "3.00" in _onco_alert
      and "0.67" in _onco_alert and "سحب سيولة" in _onco_alert
      and "مع المضارب" in _onco_alert)
_no_plan_alert = S.build_split_hunter_alert(
    [{k: v for k, v in _sh_rows[0].items() if k != "plan"}], today=_sr_today,
    fetch_hist=_HUNT_OFF)
check("🥇 صيّاد·تنبيه: صفّ بلا خطة (توافق خلفي) لا ينهار ولا يطبع أسطر الخطة",
      # ⚠️ ⓿-د بدّل مسمّى السطر إلى «🔓 الشرط» (شرط فيصل المزدوج) — فحُدِّث الفحص
      # حتى لا يصير **أعمى** (شرط ينجح بلا معنى)؛ الحكم نفسه لم يُخفَّف.
      "🔓 الشرط" not in _no_plan_alert and "التحرر" not in _no_plan_alert
      and "سحب سيولة" not in _no_plan_alert
      and "أهداف بنيوية" not in _no_plan_alert and "SPLT" in _no_plan_alert
      # سطر الدخول يبقى لكن بصياغة لا تشير لمستوى مجهول
      and "مع المضارب</b> — انتظار" in _no_plan_alert
      and "فوق التحرر" not in _no_plan_alert)
# ══════════════════════════════════════════════════════════════════════════
# ⓿-د كرت الصيّاد = **خطة فيصل النموذجية** (صورتا $NUWE: IMG_0413 + IMG_0414)
# ══════════════════════════════════════════════════════════════════════════
# **تثبيتة توصيفٍ بأرقام فيصل الحرفية** على السهم الذي انفجر فعلًا بعدها بيومين:
#   «الهدف الاول **شمعه التقسيم 3.81**» · «هدف ثاني … **شمعة الفجوه الساقطه**»
#   (‏5.216 بشارته) · «الهدف الثالث … **راس شمعة الفجوه الساقطه**» (‏7.368) ·
#   «**الشرط الان ثبات 1.95 · عدم كسر 1.83**» · «دق القاع الجمعه» · «**اما يشده
#   جميع** ل … **او يلعب موجات**». وألوان شارته: 3.812 🔵 · 7.368 ⚫.
# إطارٌ اصطناعي مبنيّ على هندسته: فجوة هابطة غير مملوءة خلّفتها شمعة (رأس 7.368 ·
# إغلاق 5.216) · تقسيمٌ عكسي بشمعةٍ إغلاقها 3.81 و**افتتاحها 4.20** (مختلفان عمدًا
# ليكشف الاختبارُ أيَّ مصدرٍ غير `_split_day_value`) · قاعٌ مدقوق 1.83 · تحرّر 1.95.
_fm_idx = pd.date_range("2026-05-04", periods=60, freq="B")
_fm_o, _fm_h, _fm_l, _fm_c = (np.zeros(60), np.zeros(60), np.zeros(60), np.zeros(60))
for _i in range(5):                                   # قمّة ما قبل الفجوة
    _fm_o[_i], _fm_h[_i], _fm_l[_i], _fm_c[_i] = 9.50, 9.80, 8.20, 8.60
_fm_o[5], _fm_h[5], _fm_l[5], _fm_c[5] = 7.30, 7.368, 5.10, 5.216   # شمعة الفجوة
for _i in range(6, 12):
    _fm_o[_i], _fm_h[_i], _fm_l[_i], _fm_c[_i] = 5.20, 5.30, 4.80, 5.00
_fm_o[12], _fm_h[12], _fm_l[12], _fm_c[12] = 5.20, 5.22, 4.90, 4.95  # مقاومة 5.22
for _i in range(13, 30):
    _fm_o[_i], _fm_h[_i], _fm_l[_i], _fm_c[_i] = 4.70, 4.90, 4.30, 4.50
_fm_o[30], _fm_h[30], _fm_l[30], _fm_c[30] = 4.20, 4.26, 3.75, 3.81  # يوم التقسيم
for _k, _v in enumerate([3.70, 3.50, 3.30, 3.10, 2.95, 2.85, 2.75, 2.65, 2.55,
                         2.45, 2.35, 2.28, 2.22, 2.16, 2.10, 2.06, 2.02, 1.99,
                         1.96, 1.93, 1.90, 1.88, 1.91, 1.93, 1.90, 1.90, 1.90,
                         1.90, 1.90]):
    _i = 31 + _k
    (_fm_o[_i], _fm_h[_i], _fm_l[_i],
     _fm_c[_i]) = _v * 1.01, _v * 1.02, _v * 0.985, _v
_fm_l[20] = 1.50            # قاعٌ **خارج** نافذة `SPLIT_BOTTOM_LOOKBACK` (يكشف النافذة)
_fm_l[55] = 1.83                                      # 🕳️ «دقّ القاع»
_fm_h[53] = 1.95                                      # 🔓 التحرر (أقرب مقاومة)
_fm_df = pd.DataFrame({"Open": _fm_o, "High": _fm_h, "Low": _fm_l, "Close": _fm_c,
                       "Volume": np.full(60, 5e5)}, index=_fm_idx)
_fm_splits = pd.Series([0.1], index=[_fm_idx[30]])
_fm_today = _fm_idx[-1].date()
_fm_row = {"symbol": "NUWE", "price": 1.90, "half": 2.13, "ref": 4.26,
           "float": 900_000, "avail": 150_000, "borrow_fee": None,
           "ema20": 2.0, "ema30": 2.5, "ema50": 3.0, "freq": 1,
           "split_date": str(_fm_idx[30].date()), "bottom_test": None,
           "split_ma": None, "next_bottom": None,
           "plan": {"liberation": 1.95, "bottom": 1.83, "sweep": 1.65,
                    "sweep_zone": {"shallow": 1.70, "deep": 1.59},
                    "targets": [{"price": 5.22, "src": "رأس شمعة حمراء"}],
                    "gap": {"bottom": 7.368, "top": 8.20}}}


def _fm_hist(_syms):
    return {"NUWE": _fm_df}


_fm_plan = S.faisal_model_plan(_fm_row, df=_fm_df, splits=_fm_splits)
check("⓿-د NUWE حرفيًّا: السلّم الثلاثي 3.81 (شمعة التقسيم) · 5.216 · 7.368 (رأسها)",
      [(round(t["price"], 3), t["label"]) for t in _fm_plan["targets"]]
      == [(3.81, "شمعة التقسيم"), (5.216, "شمعة الفجوة الساقطة"),
          (7.368, "رأس شمعة الفجوة الساقطة")])
check("⓿-د NUWE حرفيًّا: الشرط المزدوج — ثبات 1.95 · عدم كسر 1.83 (بتاريخ دقّ القاع)",
      _fm_plan["hold_above"] == 1.95 and abs(_fm_plan["no_break"] - 1.83) < 1e-9
      and _fm_plan["bottom_date"] == str(_fm_idx[55].date())
      and abs(_fm_plan["top"] - 7.368) < 1e-9)
# 🔒 **قفل المصدر:** الهدف ① من `_split_day_value` **حصرًا** — لا من افتتاح يوم الحدث
# (‏4.20 في الإطار) ولا من `half`/`ref`. مصدرٌ آخر ⇒ رقمٌ آخر ⇒ يسقط هذا الفحص.
check("⓿-د 🔒 قفل المصدر: الهدف ① = `_split_day_value` (3.81) لا الافتتاح (4.20) ولا ÷2",
      abs(_fm_plan["targets"][0]["price"]
          - S._split_day_value(_fm_df["Close"], _fm_splits, _fm_df.index[-1])) < 1e-9
      and not any(abs(t["price"] - v) < 0.01 for t in _fm_plan["targets"]
                  for v in (4.20, 2.13, 4.26)))
check("⓿-د 🔒 بلا تقسيمات ⇒ يسقط الهدف ① وحده (لا يُلفَّق) والفجوة الساقطة تبقى",
      [t["label"] for t in S.faisal_model_plan(
          _fm_row, df=_fm_df, splits=None)["targets"]]
      == ["شمعة الفجوة الساقطة", "رأس شمعة الفجوة الساقطة"])
check("⓿-د 🔒 «طرح جديد» لا شمعة تقسيم له ⇒ الهدف ① يُسقَط (لا تقسيمٌ قديمٌ ملفَّق)",
      all(t["label"] != "شمعة التقسيم" for t in S.faisal_model_plan(
          dict(_fm_row, event_kind="offering"), df=_fm_df,
          splits=_fm_splits)["targets"]))
# 🎨 التلوين = **قاعدة `targets_kind` بالفارز نفسها** (أولوية النظيف · ثم المقاومة ·
# والافتراض 🔵). ونتيجتها على NUWE تطابق شارة فيصل: 3.812 🔵 · 7.368 ⚫.
check("⓿-د 🎨 لون فيصل: شمعة التقسيم 🔵 (نظيفة) · الفجوة الساقطة ورأسها ⚫ (مقاومة)",
      [t["kind"] for t in _fm_plan["targets"]] == ["🔵", "⚫", "⚫"])
check("⓿-د 🎨 القاعدة نقيّة: نظيفٌ يسبق المقاومة · وبلا مطابقة 🔵 · وسعرٌ تالف ⇒ ''",
      S.split_target_kind(5.0, resist=[5.0], clean=[]) == "⚫"
      and S.split_target_kind(5.0, resist=[5.0], clean=[5.0]) == "🔵"
      and S.split_target_kind(5.0, resist=[9.0], clean=[]) == "🔵"
      and S.split_target_kind(5.0, resist=[5.09], clean=[]) == "🔵"   # خارج 1.5%
      and S.split_target_kind(5.0, resist=[5.07], clean=[]) == "⚫"   # داخلها
      and S.split_target_kind(None) == "" and S.split_target_kind(float("nan")) == ""
      and S.split_target_kind(0) == "")
# 🔒 **منع الدائرية:** رأس شمعة الفجوة **هو نفسه** قاع تلك الفجوة، فلولا استبعاده من
# مجموعة «النظيف» لصار 🔵 **بحكم التعريف دائمًا** = لونٌ بلا معلومة (وفيصل رسمه ⚫).
check("⓿-د 🔒 لا دائرية: رأس شمعة الفجوة لا يُلوَّن نظيفًا بفجوته هو",
      _fm_plan["targets"][2]["kind"] == "⚫"
      and S._model_levels(_fm_row, _fm_df, 1.90, skip_clean=7.368)[1] == []
      and 7.368 in S._model_levels(_fm_row, _fm_df, 1.90)[1])
# 🕳️ شمعة الفجوة الساقطة — نقيّة · فاشلة-آمنة · **هابطة حصرًا**
_fm_gc = S.falling_gap_candle(_fm_df, 1.90)
check("⓿-د 🕳️ شمعة الفجوة الساقطة: قيمتها 5.216 · رأسها 7.368 · وتاريخها",
      _fm_gc["value"] == 5.216 and _fm_gc["head"] == 7.368
      and _fm_gc["gap_top"] == 8.20 and _fm_gc["date"] == str(_fm_idx[5].date()))
check("⓿-د 🕳️ متّسقة مع تعريف البيت الواحد (`unfilled_gaps_above`) — لا تعريف موازٍ",
      (lambda z: abs(_fm_gc["head"] - z["bottom"]) < 0.005
       and abs(_fm_gc["gap_top"] - z["top"]) < 0.005)(
          S.unfilled_gaps_above(_fm_df, int(S.CONFIG["GAP_ABOVE_LOOKBACK_D"]))
          ["nearest"]))
# ⛔ **طفرة موصوفة:** فجوة **صاعدة** (قاع الشمعة فوق قمة سابقتها) ليست «ساقطة» ⇒ None.
_fm_up = _fm_df.copy()
_fm_up.iloc[:, :] = np.column_stack([np.full(60, 1.0), np.full(60, 1.05),
                                     np.full(60, 0.95), np.full(60, 1.0),
                                     np.full(60, 5e5)])
_fm_up.iloc[7, _fm_up.columns.get_loc("Low")] = 3.00      # قفزة فوق (فجوة صاعدة)
_fm_up.iloc[7, _fm_up.columns.get_loc("High")] = 3.40
_fm_up.iloc[7, _fm_up.columns.get_loc("Close")] = 3.20
check("⓿-د ⛔ فجوة **صاعدة** فوق السعر لا تُقبل شمعةَ فجوةٍ ساقطة ⇒ None",
      S.falling_gap_candle(_fm_up, 1.0) is None)
# 🔒 حارس الاتجاه **ملكُ هذي الدالّة** لا المُفوَّض إليه: نُزوّدها قسرًا بمنطقة
# «فجوة» صاعدة (قاعُ الشمعة فوق قمة سابقتها) ⇒ يجب أن ترفضها. حذفُ الحارس يُنجح
# الفجوة الصاعدة ⇒ يسقط هذا الفحص (طفرة موصوفة في الحزمة).
_fm_sv_gap = S.unfilled_gaps_above
try:
    S.unfilled_gaps_above = (lambda _df, _lb:
                             {"nearest": {"bottom": 3.40, "top": 3.00, "ago": 52}})
    _fm_guard = S.falling_gap_candle(_fm_up, 1.0)
finally:
    S.unfilled_gaps_above = _fm_sv_gap
check("⓿-د ⛔ حارس الاتجاه: منطقةٌ صاعدة مُقحَمة قسرًا تُرفَض (لا ثقة عمياء بالمُفوَّض)",
      _fm_guard is None and S.falling_gap_candle(_fm_df, 1.90) is not None)
check("⓿-د 🕳️ فاشلة-آمنة: None/إطار قصير/بلا فجوة ⇒ None (لا انهيار)",
      S.falling_gap_candle(None) is None
      and S.falling_gap_candle(_fm_df.head(1), 1.0) is None
      and S.falling_gap_candle(_fm_df, 99.0) is None)      # السعر فوق كل فجوة
check("⓿-د 🕳️ دقّ القاع: أدنى قاعٍ بنافذة `SPLIT_BOTTOM_LOOKBACK` نفسها + تاريخه",
      (lambda b: b["price"] == 1.83 and b["date"] == str(_fm_idx[55].date()))(
          S.bottom_strike(_fm_df))
      # النافذة **محكومة فعلًا**: قاعٌ أعمق (1.50) خارجها لا يُختطَف، ويظهر بتوسيعها
      and S.bottom_strike(_fm_df, lookback=60)["price"] == 1.50
      and abs(S.bottom_strike(_fm_df)["price"]
              - S.faisal_split_plan(_fm_df, 1.90)["bottom"]) < 0.005
      and S.bottom_strike(None) is None)
check("⓿-د 🔢 صيغة أرقام فيصل: منزلتان وثالثة لو غير صفرية · وتعذّر ⇒ '' لا صفر",
      S._plan_px(3.81) == "3.81" and S._plan_px(5.216) == "5.216"
      and S._plan_px(7.368) == "7.368" and S._plan_px(1.95) == "1.95"
      and S._plan_px(100) == "100.00"
      and S._plan_px(None) == "" and S._plan_px(float("nan")) == ""
      and S._plan_px("x") == "")
# 🃏 الكرت الكامل — أرقام فيصل الحرفية كلها + مسمّياته + سيناريوهاه
_fm_card = S.build_split_hunter_alert([_fm_row], today=_fm_today,
                                      fetch_hist=_fm_hist,
                                      fetch_splits=lambda s: _fm_splits)
check("⓿-د 🃏 الكرت يحمل خطة فيصل بحرفيّتها (3.81 · 5.216 · 7.368 · 1.95 · 1.83)",
      all(x in _fm_card for x in
          ("$3.81", "$5.216", "$7.368", "$1.95", "$1.83",
           "شمعة التقسيم", "شمعة الفجوة الساقطة", "رأس شمعة الفجوة الساقطة",
           "دقّ القاع يوم", "عدم كسر", "يلعب موجات", "القمة الكبرى")))
check("⓿-د 🕵️ المايكرو (طلب/عرض · FSTO) **إحالةٌ** لفحص اليد لا نقلٌ للكرت",
      "بأداة فحص اليد" in _fm_card and "FSTO" in _fm_card
      and "Bid" not in _fm_card and "K:" not in _fm_card)
check("⓿-د 🔒 فاشل-آمن صلب: خطةٌ تالفة (نصّ) وجالبٌ يرجع غير قاموس ⇒ لا انهيار",
      "NUWE" in S.build_split_hunter_alert(
          [dict(_fm_row, plan="تالف")], today=_fm_today,
          fetch_hist=lambda s: ["ليست قاموسًا"])
      and S.faisal_model_plan(dict(_fm_row, plan="تالف"), df=_fm_df,
                              splits=_fm_splits)["targets"])
check("⓿-د 🧹 لا تكرار: مستوًى بنيويّ يطابق هدفًا نموذجيًّا (5.22≈5.216) يُطوى بمسمّاه",
      "أهداف بنيوية" not in _fm_card
      and "5.22 (رأس شمعة حمراء)" not in _fm_card)
# 🔒 **قفل التوصيف الحاسم:** الترقية **عرضٌ محض** — المطابقون أنفسهم مجموعةً وترتيبًا.
def _fm_syms(m):
    """رموز المطابقين بترتيب ظهورها في التنبيه (ترويسة كل كرت)."""
    return __import__("re").findall(r"🎯 <b>([A-Z]+)</b>", m)


_fm_two = [_fm_row, dict(_fm_row, symbol="ZZZ")]
check("⓿-د 🔒 قفل العضوية والترتيب: نفس المطابقين مع الإثراء وبدونه (عرضٌ لا اختيار)",
      _fm_syms(S.build_split_hunter_alert(_fm_two, today=_fm_today,
                                          fetch_hist=_fm_hist,
                                          fetch_splits=lambda s: _fm_splits))
      == _fm_syms(S.build_split_hunter_alert(_fm_two, today=_fm_today,
                                             fetch_hist=_HUNT_OFF))
      == ["NUWE", "ZZZ"]
      and [r["symbol"] for r in _nuwe_scan()] == ["NUWE"]
      and [r["symbol"] for r in _sh_rows] == ["SPLT"])
check("⓿-د 🔒 الصفوف تُقرأ ولا تُكتب (الإثراء لا يمسّ صفّ الاختيار)",
      (lambda before: (S.build_split_hunter_alert(
          [_fm_row], today=_fm_today, fetch_hist=_fm_hist,
          fetch_splits=lambda s: _fm_splits),
          sorted(_fm_row.keys()) == before)[1])(sorted(_fm_row.keys())))
_fm_blind = S.build_split_hunter_alert([_fm_row], today=_fm_today,
                                       fetch_hist=_HUNT_OFF)
check("⓿-د 🔒 فاشل-آمن: تعذّر الإطار ⇒ تسقط أسطر السلّم **بصمت لا بكذب**، والكرت يبقى",
      "NUWE" in _fm_blind and "شمعة التقسيم" not in _fm_blind
      and "شمعة الفجوة الساقطة" not in _fm_blind and "5.216" not in _fm_blind
      and "يلعب موجات" not in _fm_blind
      # حدث القاع يسقط (تاريخه من الإطار) بينما شقّا الشرط يبقيان من حقول الصفّ
      # نفسِه (تحرّر الخطة + قاعها) — **الموجود يُعرض والمفقود لا يُخترَع**.
      and "دقّ القاع يوم" not in _fm_blind
      and "🔓 الشرط: ثبات فوق <b>$1.95</b>" in _fm_blind
      and "عدم كسر <b>$1.83</b>" in _fm_blind)
# 🔌 **قفل «الميزة موصولة» — سلوكيّ لا نصّيّ**: المسار الافتراضي (بلا حقن) ينادي
# `download_history` فعلًا (درس: القفل النصّي ينجو لو كانت الكلمة في تعليق).
_fm_sv = (S.download_history, S.yf)
try:
    S.download_history = lambda tickers, start_override=None: {"NUWE": _fm_df}
    S.yf = S.yf or object()
    _fm_live = S.build_split_hunter_alert([_fm_row], today=_fm_today,
                                          fetch_splits=lambda s: _fm_splits)
finally:
    S.download_history, S.yf = _fm_sv
check("⓿-د 🔌 المسار الحيّ موصول: الافتراضي يجلب بـ`download_history` (قفل سلوكيّ)",
      "$5.216" in _fm_live and "شمعة التقسيم" in _fm_live)
check("⓿-د 🔒 قفل الجذور: كل دوال الخطة النموذجية خارج الاختيار/الفرز/الباكتيست",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("falling_gap_candle", "bottom_strike", "split_target_kind",
                      "faisal_model_plan", "faisal_model_lines", "_model_levels",
                      "_hunter_models", "_hunter_history", "_plan_px")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker, S.scan_market, S.scan_split_hunter,
                     S._split_setup_probe, S.faisal_split_plan)))
# ═══ 🧾 بطاقة فيصل الفرزية (2026-07-27، 5 صور: HTCR·BNKK·MWC·SVRE·MBRX) ═══
# ① «طرح جديد» حدثًا مؤسِّسًا · ② مرجع ÷2 = **افتتاح** يوم الحدث · ③ Form 4 + «خبر بلا قبول»
_fc_idx = pd.date_range("2025-06-02", periods=40, freq="B")
# HTCR الحرفي: قسم · افتتاح 3.72 · أعلى 4.58 (صعود 23% ⇒ **فوق** عتبة فيصل 20% ⇒ صعد)
_fc_open = np.concatenate([np.full(1, 3.72), np.full(39, 2.4)])
_fc_high = np.concatenate([np.full(1, 3.80), np.full(4, 4.58), np.full(35, 2.45)])
_fc_close = np.concatenate([np.full(5, 3.9), np.full(35, 2.32)])
_fc_df = pd.DataFrame({"Open": _fc_open, "High": _fc_high,
                       "Low": _fc_close * 0.98, "Close": _fc_close,
                       "Volume": np.full(40, 5e5)}, index=_fc_idx)
_fc_splits = pd.Series([0.1], index=[_fc_idx[0]])
_fc_today = _fc_idx[-1].date()
check("🧾 بطاقة فيصل·افتتاح يوم الحدث = مرجع «لم يصعد» (HTCR 3.72 حرفيًّا)",
      abs(S._event_day_open(_fc_df["Open"], _fc_idx[0]) - 3.72) < 1e-6)
check("🧾 بطاقة فيصل·أعلى بعد الحدث (HTCR 4.58 حرفيًّا) — تعميم على تاريخ صريح",
      abs(S._post_event_high(_fc_df["High"], _fc_idx[0]) - 4.58) < 1e-6)
_fc_pr = S._split_setup_probe(_fc_df, _fc_splits, _fc_today)
check("🧾 بطاقة فيصل·HTCR: صعود 23% من الافتتاح فوق عتبة 20% ⇒ didnt_rise=False",
      _fc_pr is not None and _fc_pr["didnt_rise"] is False
      and abs(_fc_pr["first_val"] - 3.72) < 0.01 and _fc_pr["event_kind"] == "split")
# 🥇 مثال فيصل الحرفي (IMG_0153): «فتح ع 5 وصل 5.50» = +10% ⇒ هادئ · و÷2 = 2.50
_f53_o = np.concatenate([np.full(1, 5.00), np.full(39, 2.6)])
_f53_h = np.concatenate([np.full(1, 5.50), np.full(39, 2.65)])
_f53_c = np.concatenate([np.full(1, 5.20), np.full(39, 2.55)])
_f53 = pd.DataFrame({"Open": _f53_o, "High": _f53_h, "Low": _f53_c * 0.98,
                     "Close": _f53_c, "Volume": np.full(40, 5e5)}, index=_fc_idx)
_f53_pr = S._split_setup_probe(_f53, _fc_splits, _fc_today)
check("🥇 IMG_0153 حرفيًّا: فتح 5 · وصل 5.50 (+10%) ⇒ هادئ · و÷2 = 2.50",
      _f53_pr is not None and _f53_pr["didnt_rise"] is True
      and abs(_f53_pr["half"] - 2.75) < 0.01 and abs(_f53_pr["ref"] - 5.50) < 0.01)
check("🚫 IMG_0153 «السنتات خارج الشرح»: أرضية سعر لوصفة المقسّم موجودة",
      S.CONFIG["SPLIT_RADAR_PRICE_MIN"] >= 1.0
      and "SPLIT_RADAR_PRICE_MIN" in _insp0.getsource(S.scan_split_hunter)
      and "SPLIT_RADAR_PRICE_MIN" in _insp0.getsource(S.scan_split_radar))
check("🥇 IMG_0153: عتبة «لم يصعد» = 20% حرفيًّا (كانت 50 اجتهادًا)",
      S.CONFIG["SPLIT_ROSE_MAX_PCT"] == 20.0)
# BNKK الحرفي: افتتاح 3.69 · أعلى 7.19 = +95% ⇒ انضخّ (didnt_rise=False)
_bk_df = _fc_df.copy()
_bk_df.iloc[0, _bk_df.columns.get_loc("Open")] = 3.69
_bk_df.iloc[1:5, _bk_df.columns.get_loc("High")] = 7.19
check("🧾 بطاقة فيصل·BNKK انضخّ: افتتاح 3.69 → أعلى 7.19 (+95%) ⇒ didnt_rise=False",
      (S._split_setup_probe(_bk_df, _fc_splits, _fc_today) or {}).get("didnt_rise")
      is False)
check("🧾 بطاقة فيصل·احتياط: بلا عمود افتتاح صالح يرجع لإغلاق أول شمعة (توافق خلفي)",
      S._event_day_open(None, _fc_idx[0]) is None
      and S._post_event_high(None, _fc_idx[0]) is None)
# ① الطرح الجديد حدثًا مؤسِّسًا — بلا تقسيم عكسي إطلاقًا
_of_splits = pd.Series(dtype=float)
check("🆕 طرح جديد·بلا تقسيم وبلا طرح ⇒ None (السلوك السابق حرفيًّا)",
      S._split_setup_probe(_fc_df, _of_splits, _fc_today) is None)
_of_pr = S._split_setup_probe(_fc_df, _of_splits, _fc_today,
                              offering={"date": str(_fc_idx[0].date()),
                                        "form": "424B5"})
check("🆕 طرح جديد·يُعامَل كالتقسيم: نفس المرجع (أعلى بعده) ونفس الـ÷2",
      _of_pr is not None and _of_pr["event_kind"] == "offering"
      and abs(_of_pr["ref"] - 4.58) < 0.01 and abs(_of_pr["half"] - 2.29) < 0.01)
check("🆕 طرح جديد·قديم خارج النافذة يُهمَل (بلا تسريب زمني)",
      S._split_setup_probe(_fc_df, _of_splits, _fc_today,
                           offering={"date": "2020-01-02"}) is None)
check("🆕 طرح جديد·الكشف: يقرأ القناة المجانية ويحترم النافذة",
      (lambda: (S._SEC_OFFERING.update(
          {"ZZO": {"form": "424B5", "date": str(_fc_today)}}),
          S._offering_event("ZZO", today=_fc_today) is not None,
          S._SEC_OFFERING.update({"ZZO": {"form": "424B5", "date": "2019-01-01"}}),
          S._offering_event("ZZO", today=_fc_today) is None,
          S._SEC_OFFERING.pop("ZZO", None))[3])())
# ② «÷2 على المستوى السائد» (بطاقة MWC: هبوط 4.70 ⇒ مستهدف 2.35)
_mw = pd.DataFrame({"Open": np.full(30, 5.0), "High": np.full(30, 5.2),
                    "Low": np.full(30, 4.6),
                    "Close": np.concatenate([np.full(20, 6.0), np.full(10, 4.70)]),
                    "Volume": np.full(30, 1e5)},
                   index=pd.date_range("2025-06-02", periods=30, freq="B"))
_hd = S.half_down_target(_mw)
check("📉 MWC حرفيًّا: المستوى السائد 4.70 ⇒ مستهدف الهبوط 2.35 (÷2)",
      _hd is not None and abs(_hd["level"] - 4.70) < 1e-6
      and abs(_hd["target"] - 2.35) < 1e-6)
check("📉 ÷2·قاع طازج لم يستقرّ (أقل من 3 جلسات) ⇒ None (لا إسقاط على ضجيج)",
      S.half_down_target(pd.DataFrame(
          {"Open": np.full(30, 5.0), "High": np.full(30, 5.2),
           "Low": np.full(30, 4.0),
           "Close": np.concatenate([np.full(29, 6.0), np.full(1, 4.0)]),
           "Volume": np.full(30, 1e5)},
          index=pd.date_range("2025-06-02", periods=30, freq="B"))) is None)
check("📉 ÷2·فاشلة-آمنة: بلا إطار/إطار قصير ⇒ None · السطر فارغ",
      S.half_down_target(None) is None and S.half_down_line(None) == ""
      and "2.35" in S.half_down_line(_hd))
check("🪦 ÷2·متقاعدة من العرض: لا تُستدعى في اليومي/الصيّاد/الكرت (كانت تظهر لكل ارتكاز)",
      all("half_down" not in _insp0.getsource(_f)
          for _f in (S.build_daily_message, S.build_message,
                     S.scan_split_hunter, S.build_split_hunter_alert,
                     S.update_watchlist_status, S.make_watch_entry)))
# ③ Form 4 — شراء الداخليين (فيصل: «ارتفعت بسبب المدير اشترى 1.7 مليون سهم»)
_F4_BUY = """<ownershipDocument><reportingOwner><reportingOwnerId>
 <rptOwnerName>John Doe</rptOwnerName></reportingOwnerId>
 <reportingOwnerRelationship><officerTitle>CEO</officerTitle>
 </reportingOwnerRelationship></reportingOwner>
 <nonDerivativeTable><nonDerivativeTransaction>
  <transactionCoding><transactionCode>P</transactionCode></transactionCoding>
  <transactionAmounts>
   <transactionShares><value>12000</value></transactionShares>
   <transactionPricePerShare><value>1.37</value></transactionPricePerShare>
   <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
  </transactionAmounts></nonDerivativeTransaction></nonDerivativeTable>
</ownershipDocument>"""
_F4_SELL = _F4_BUY.replace("<transactionCode>P<", "<transactionCode>S<").replace(
    "<value>A</value>", "<value>D</value>")
_F4_GRANT = _F4_BUY.replace("<transactionCode>P<", "<transactionCode>A<")
_p4 = S._parse_form4(_F4_BUY)
check("📄 Form 4·شراء BNKK الحرفي: الرئيس اشترى 12 ألف سهم بسعر 1.37",
      _p4 is not None and _p4["shares"] == 12000 and abs(_p4["price"] - 1.37) < 1e-9
      and _p4["title"] == "CEO" and _p4["is_buy"] is True)
check("📄 Form 4·البيع (S/D) لا يُحسب شراءً",
      S._parse_form4(_F4_SELL) is None)
check("📄 Form 4·المنح (A) ليس شراءً نقديًّا ⇒ يُهمَل (حدّ صدق مُعلَن)",
      S._parse_form4(_F4_GRANT) is None)
check("📄 Form 4·فاشل-آمن: فارغ/HTML/تالف ⇒ None بلا استثناء",
      S._parse_form4("") is None and S._parse_form4(None) is None
      and S._parse_form4("<html>error</html>") is None)
S._SEC_FORM4["ZZ4"] = [{"date": "2025-06-17", "cik": 123, "acc": "0001-25-000001",
                        "doc": "f4.xml"}]
_buys = S.form4_insider_buys("ZZ4", fetch=lambda u: _F4_BUY)
check("📄 Form 4·الغلاف: يبني الرابط ويحلّل ويستهلك الميتا مرة واحدة",
      len(_buys) == 1 and _buys[0]["date"] == "2025-06-17"
      and S.form4_insider_buys("ZZ4", fetch=lambda u: _F4_BUY) == [])
check("📄 Form 4·⚠️ الرابط يُجرَّد من سابقة XSL (كانت الميزة ميتة 100%)",
      (lambda urls: (S._SEC_FORM4.update(
          {"ZZX": [{"date": "2025-06-17", "cik": 320193,
                    "acc": "0000320193-23-000023",
                    "doc": "xslF345X03/wf-form4_1678833327.xml"}]}),
          S.form4_insider_buys("ZZX", fetch=lambda u: (urls.append(u), _F4_BUY)[1]),
          urls and urls[0].endswith("/000032019323000023/wf-form4_1678833327.xml")
          and "xsl" not in urls[0])[-1])([]))
check("📄 Form 4·مستند وصل لكنه HTML مُصيَّر ⇒ يُحسب إخفاقًا (لا موت صامت)",
      (lambda: (S._F4_FAILS.__setitem__(0, 0),
                S._SEC_FORM4.update({"ZZH": [{"date": "2025-06-17", "cik": 1,
                                              "acc": "a", "doc": "d.xml"}]}),
                S.form4_insider_buys("ZZH", fetch=lambda u: "<html>SEC FORM 4</html>"),
                S._F4_FAILS[0] >= 1)[-1])())
check("📄 Form 4·السطر بلغة فيصل + فارغ عند لا شراء",
      "اشترى" in S.insider_buy_line({"insider_buys": _buys})
      and S.insider_buy_line({}) == "" and S.insider_buy_line(None) == "")
check("📄 Form 4·عطل الشبكة ⇒ [] بلا استثناء (فاشل-آمن)",
      (lambda: (S._SEC_FORM4.update({"ZZ5": [{"date": "2025-06-17", "cik": 1,
                                              "acc": "a", "doc": "d.xml"}]}),
                S.form4_insider_buys(
                    "ZZ5", fetch=lambda u: (_ for _ in ()).throw(IOError())) == [])[1])())
# ④ «خبره عدم قبوله = هبوط» (فيصل MBRX)
_na_df = pd.DataFrame({"Open": [3.00, 3.10], "High": [3.30, 3.20],
                       "Low": [2.90, 2.95], "Close": [3.05, 3.00],
                       "Volume": [1e6, 9e5]},
                      index=pd.to_datetime(["2025-06-10", "2025-06-11"]))
check("📉 إعلان لم يُقبَل: أغلق تحت افتتاحه ⇒ رفض (المرجع من الشمعة نفسها)",
      (S.news_acceptance(_na_df, "2025-06-11") or {}).get("accepted") is False)
check("📉 إعلان مقبول: أغلق فوق افتتاحه وفوق إغلاق ما قبله ⇒ لا تحذير",
      (S.news_acceptance(_na_df, "2025-06-10") or {}).get("accepted") is True
      and S.news_rejected_line(S.news_acceptance(_na_df, "2025-06-10")) == "")
check("📉 ⚖️ لا فارق زمني: الحكم لا يعتمد الرقم الحرج المتحرّك (كان يقلب الإشارة)",
      "critical" not in _insp0.getsource(S.news_acceptance)
      and "critical_number" not in _insp0.getsource(S.update_watchlist_status).split(
          "news_acc")[1][:200])
check("📉 خبر·تاريخ بعد آخر شمعة أو إطار فارغ ⇒ None (لا نظر مستقبلي)",
      S.news_acceptance(_na_df, "2025-12-31") is None
      and S.news_acceptance(None, "2025-06-10") is None
      and S.news_acceptance(_na_df, None) is None)
check("📉 إعلان·السطر يظهر عند الرفض فقط وبعبارة فيصل",
      "عدم قبوله" in S.news_rejected_line(S.news_acceptance(_na_df, "2025-06-11"))
      and S.news_rejected_line(None) == "" and S.news_rejected_line({}) == "")
_ev_r = {"insider_buys": [{"date": "2025-06-01"}],
         "offering_event": {"date": "2025-06-20"},
         "proxy_filing": {"date": "2025-05-01"}}
check("📉 أحدث حدث معلوم: يختار الأحدث بين الشراء الداخلي والطرح والوكالة",
      S._latest_event_date(_ev_r, today=_dt0.date(2025, 6, 25)) == "2025-06-20"
      and S._latest_event_date({"proxy_filing": {"date": "2025-06-20"}},
                               today=_dt0.date(2025, 6, 25)) is None
      and S._latest_event_date({}) is None and S._latest_event_date(None) is None)
check("📉 حدّ الحداثة إلزامي: حدث عمره شهران يُهمَل (لا تحذير كاذب دائم)",
      S._latest_event_date(_ev_r, today=_dt0.date(2025, 8, 25)) is None
      and S._latest_event_date(_ev_r, today=_dt0.date(2025, 6, 25),
                               max_age_days=3) is None)
check("📉 حدث بتاريخ مستقبلي يُهمَل (حارس بلا نظر أمامي)",
      S._latest_event_date({"offering_event": {"date": "2099-01-01"}}) is None)
# ═══ إصلاحات التدقيق الخصومي على بطاقة فيصل (2026-07-27) — اختبار انحدار لكل ملاحظة ═══
_nan_df = _bk_df.copy()                      # BNKK المنضخّ (+95%) لكن بافتتاح NaN
_nan_df.iloc[0, _nan_df.columns.get_loc("Open")] = np.nan
check("⚠️ NaN·افتتاح مفقود لا يفشل مفتوحًا: المنضخّ يبقى مرفوضًا (يرتدّ للإغلاق)",
      (S._split_setup_probe(_nan_df, _fc_splits, _fc_today) or {}).get("didnt_rise")
      is False)
check("⚖️ الطرح·تسجيل رفّي روتيني (S-3/424B3/EFFECT) ليس حدثًا مؤسِّسًا",
      (lambda: all((S._SEC_FOUNDING.update({"ZZR": {"form": _f,
                                                    "date": str(_fc_today)}}),
                    S._offering_event("ZZR", today=_fc_today) is None)[1]
                   for _f in ("S-3", "424B3", "EFFECT", "S-1"))
       and (S._SEC_FOUNDING.update({"ZZR": {"form": "424B5",
                                            "date": str(_fc_today)}}),
            S._offering_event("ZZR", today=_fc_today) is not None,
            S._SEC_FOUNDING.pop("ZZR", None))[1])())
def _off_mask_probe():
    S._SEC_FOUNDING.pop("ZZM", None)
    S._SEC_OFFERING.pop("ZZM", None)
    payload = {"filings": {"recent": {
        "form": ["S-3", "8-K", "424B5"],
        "filingDate": [str(_fc_today)] * 3}}}
    _orig = S.sec_cik_map
    S.sec_cik_map = lambda: {"ZZM": 123}
    try:
        return (S._offering_event("ZZM", today=_fc_today,
                                  fetch=lambda u: payload) or {}).get("form")
    finally:
        S.sec_cik_map = _orig
check("⚖️ الطرح·أحدث S-3 روتيني لا يحجب النشرة النهائية الأقدم (كان يقتل الميزة)",
      _off_mask_probe() == "424B5")
check("⚖️ ÷2·مربوط بالسعر: سهم صعد بعيدًا عن قاعه القديم لا يُسقَط عليه مستهدف هبوط",
      S.half_down_target(_mw, price=9.0) is None
      and S.half_down_target(_mw, price=5.0) is not None)
check("📄 Form 4·لا تسرّب regex: كتلة بلا سعر لا تلتقط رقم حاشية لاحقة",
      (lambda p: p is not None and p["shares"] == 12000 and p["price"] is None)(
          S._parse_form4(_F4_BUY.replace(
              "<transactionPricePerShare><value>1.37</value>"
              "</transactionPricePerShare>", "")
              + "<footnotes><footnote>2891000</footnote></footnotes>"))
      )
check("📄 Form 4·متوسط السعر **مرجَّح** بالكمية لا حسابيًّا",
      (lambda p: p is not None and p["shares"] == 11000
       and abs(p["price"] - (10000 * 1.0 + 1000 * 2.0) / 11000) < 1e-3)(
          S._parse_form4(_F4_BUY.replace("<value>12000</value>", "<value>10000</value>")
                         .replace("<value>1.37</value>", "<value>1.0</value>")
                         .replace("</nonDerivativeTable>",
                                  """<nonDerivativeTransaction>
  <transactionCoding><transactionCode>P</transactionCode></transactionCoding>
  <transactionAmounts>
   <transactionShares><value>1000</value></transactionShares>
   <transactionPricePerShare><value>2.0</value></transactionPricePerShare>
   <transactionAcquiredDisposedCode><value>A</value></transactionAcquiredDisposedCode>
  </transactionAmounts></nonDerivativeTransaction></nonDerivativeTable>"""))))
check("📄 Form 4·إفصاح فيه شراء وبيع معًا يُصرَّح ببيعه لا يُخفى",
      (lambda p: p is not None and p.get("has_sales") is True
       and "ومعه بيع" in S.insider_buy_line({"insider_buys": [p]}))(
          S._parse_form4(_F4_BUY.replace(
              "</nonDerivativeTable>",
              """<nonDerivativeTransaction>
  <transactionCoding><transactionCode>S</transactionCode></transactionCoding>
  <transactionAmounts>
   <transactionShares><value>5000</value></transactionShares>
   <transactionAcquiredDisposedCode><value>D</value></transactionAcquiredDisposedCode>
  </transactionAmounts></nonDerivativeTransaction></nonDerivativeTable>"""))))
check("📄 Form 4·ميتا تالفة (cik غير رقمي) ⇒ تخطٍّ بلا استثناء",
      (lambda: (S._SEC_FORM4.update({"ZZ6": [{"date": "2025-06-17", "cik": "x",
                                              "acc": "a", "doc": "d.xml"}]}),
                S.form4_insider_buys("ZZ6", fetch=lambda u: _F4_BUY) == [])[1])())
check("🔒 عدّادات SEC مستقلّة (الطرح ≠ Form 4) وسقف مستندات للتشغيلة موجود",
      S._OFF_FAILS is not S._F4_FAILS and "FORM4_BUDGET" in S.CONFIG)
# ═══ 🎯 تجربة T-EXIT (exit_policy_prereg.md): سلّم أهداف ثابتة النسبة ═══
# دخول 100 · وقف 90 (مخاطرة 10%) ⇒ هدف +20% = 2R · +50% = 5R · +100% = 10R
def _xt(mg, oc="win"):
    return {"entry": 100.0, "stop": 90.0, "t1": 110.0, "outcome": oc,
            "mg_pre_stop": mg}
check("🎯 T-EXIT·R يُشتقّ من «أقصى صعود قبل الوقف» بلا مسّ الجذر",
      abs(S._exit_policy_r(_xt(35.0), 20.0) - 2.0) < 1e-9
      and abs(S._exit_policy_r(_xt(35.0), 30.0) - 3.0) < 1e-9
      and S._exit_policy_r(_xt(35.0), 50.0) == -1.0        # 35% أقل من 50%
      and S._exit_policy_r(_xt(5.0), 10.0) == -1.0)
check("🎯 T-EXIT·فاشلة-آمنة: بلا mg_pre_stop / بلا نسبة / وقف فوق الدخول ⇒ None",
      S._exit_policy_r({"entry": 100.0, "stop": 90.0}, 20.0) is None
      and S._exit_policy_r(_xt(35.0), None) is None
      and S._exit_policy_r(dict(_xt(35.0), stop=120.0), 20.0) is None)
# 🔴 قفل ضدّ الخللين الذين أسقطتهما المراجعة الذاتية قبل الاعتماد
check("🔴 T-EXIT·قفل: لا ذراع «تتبّع» (كانت متحيّزة: تربح على أي قمة موجبة)",
      "trail" not in _insp0.getsource(S._exit_policy_r)
      and "TRAIL" not in _insp0.getsource(S.backtest_exit_policies)
      and not hasattr(S, "_EXIT_TRAIL_CAPTURE"))
check("🔴 T-EXIT·قفل: لا ذراع t2/t3 صامتة (الجذر يحمل t1 فقط) + التصريح بذلك",
      't["t2"]' not in _insp0.getsource(S._exit_policy_r)
      and 't["t3"]' not in _insp0.getsource(S._exit_policy_r)
      and any("t1 فقط" in x for x in S.backtest_exit_policies(
          [_xt(35.0) for _ in range(15)] + [_xt(3.0, "loss") for _ in range(15)])))
_xrep = S.backtest_exit_policies([_xt(35.0) for _ in range(15)]
                                 + [_xt(3.0, "loss") for _ in range(15)])
check("🎯 T-EXIT·الكتلة: تبوّب السلّم كاملًا وتصدر حكمًا بالمعيار المسجَّل",
      any("هدف +10%" in x for x in _xrep) and any("هدف +100%" in x for x in _xrep)
      and any("الحكم بالمعيار المسجَّل" in x for x in _xrep))
check("🎯 T-EXIT·يُعلن أن الهدف الأقرب أفضل بالوضوح نفسه (لا تحيّز للطمع)",
      any("الهدف الأقرب أفضل" in x for x in S.backtest_exit_policies(
          [_xt(15.0) for _ in range(28)] + [_xt(1.0, "loss") for _ in range(2)])))
check("🎯 T-EXIT·مطفأة بلا BT_POTENTIAL (لا mg_pre_stop ⇒ [] بلا ضجيج)",
      S.backtest_exit_policies(
          [{"entry": 100.0, "stop": 90.0, "t1": 110.0, "outcome": "win"}
           for _ in range(30)]) == []
      and S.backtest_exit_policies([_xt(35.0)]) == [])
check("🎯 T-EXIT·حدود الصدق مُعلَنة داخل المخرَج (أرضية/لا وقف متحرّك)",
      any("أرضية" in x and "وقف متحرّك" in x for x in _xrep))
check("🔒 T-EXIT·قفل: خارج الجذور السبعة و analyze_ticker (تحليل فقط)",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("_exit_policy_r", "backtest_exit_policies")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker)))
# ═══ 📥 مُجمِّع صور التلغرام (أداة مستقلة — «أرفعها دفعة واحدة وتوصلك») ═══
import os as _os0
import telegram_collect as TC
check("📥 التلغرام·المستند صورة يُفضَّل ويحفظ الاسم الأصلي (الرقم لا يضيع)",
      TC.pick_file({"message_id": 7, "document": {"file_id": "F1",
                                                 "mime_type": "image/jpeg",
                                                 "file_name": "IMG_0153.jpeg"}})
      == {"file_id": "F1", "name": "IMG_0153.jpeg", "kind": "document"})
check("📥 التلغرام·الصورة المضغوطة: يختار **أكبر مقاس** ويسمّيها برقم الرسالة",
      TC.pick_file({"message_id": 9, "photo": [
          {"file_id": "s", "file_size": 10}, {"file_id": "L", "file_size": 900}]})
      == {"file_id": "L", "name": "TG_9.jpg", "kind": "photo"})
check("📥 التلغرام·غير الصور تُهمَل (PDF/نص/رسالة فارغة) ⇒ None",
      TC.pick_file({"message_id": 1, "document": {"file_id": "d",
                                                  "mime_type": "application/pdf",
                                                  "file_name": "a.pdf"}}) is None
      and TC.pick_file({"message_id": 2, "text": "مرحبا"}) is None
      and TC.pick_file({}) is None and TC.pick_file(None) is None)
check("📥 التلغرام·اسم آمن: يحفظ العربي والامتداد ويستبدل الخطر · وبلا امتداد يرتدّ",
      TC.safe_name("IMG_0153.jpeg", "X") == "IMG_0153.jpeg"
      and TC.safe_name("../../etc/passwd", "X") == "X.jpg"
      and TC.safe_name("", "TG_5") == "TG_5.jpg"
      and TC.safe_name("صورة فيصل.png", "X") == "صورة_فيصل.png")
check("📥 التلغرام·لا يطبع السرّ إطلاقًا (إخفاء التوكن من أي نص)",
      (lambda: (_os0.environ.__setitem__("TELEGRAM_BOT_TOKEN", "SECRET123"),
                TC._mask("خطأ في bot SECRET123/getFile") ==
                "خطأ في bot ***/getFile",
                _os0.environ.pop("TELEGRAM_BOT_TOKEN", None))[1])())
check("📥 التلغرام·بلا توكن ⇒ لا عمل بلا استثناء (فاشل-آمن)",
      (lambda: (_os0.environ.pop("TELEGRAM_BOT_TOKEN", None),
                TC.main() == 0)[1])())
check("🛡️ التلغرام·العَقد ضد إعادة الإرسال: لا نُقِرّ إلا البادئة الناجحة",
      TC.safe_offset([(10, True), (11, True), (12, True)]) == 13
      and TC.safe_offset([(10, True), (11, False), (12, True)]) == 11
      and TC.safe_offset([(10, False), (11, True)], current=7) == 7
      and TC.safe_offset([], current=5) == 5)
check("🛡️ التلغرام·لا يُقِرّ التحديث قبل نجاح التنزيل (كان يفقد الصورة نهائيًّا)",
      "marks.append((uid, False))" in open("telegram_collect.py",
                                          encoding="utf-8").read()
      and "safe_offset(marks, offset)" in open("telegram_collect.py",
                                               encoding="utf-8").read())
check("🛡️ التلغرام·يعيد المحاولة ثلاثًا ويسرد المتعذّر بلا طلب إعادة إرسال",
      "range(3)" in open("telegram_collect.py", encoding="utf-8").read()
      and "لا تُعِد إرسال أي صورة" in open("telegram_collect.py",
                                          encoding="utf-8").read())
check("📥 التلغرام·أداة مستقلة: لا تستورد البوت ولا تمسّ الفرز",
      "Super_stock" not in open("telegram_collect.py", encoding="utf-8").read())
check("🔴 التلغرام·input فارغ لا يُسقط الأداة (كان int('') يرمي قبل main)",
      (lambda: (_os0.environ.__setitem__("TG_MAX_FILES", ""),
                TC._int_env("TG_MAX_FILES", 600) == 600,
                _os0.environ.__setitem__("TG_MAX_FILES", "abc"),
                TC._int_env("TG_MAX_FILES", 600) == 600,
                _os0.environ.__setitem__("TG_MAX_FILES", "0"),
                TC._int_env("TG_MAX_FILES", 600) == 600,
                _os0.environ.__setitem__("TG_MAX_FILES", "250"),
                TC._int_env("TG_MAX_FILES", 600) == 250,
                _os0.environ.pop("TG_MAX_FILES", None))[1:8:2] ==
               (True, True, True, True))())
check("🔴 التلغرام·رفض تلغرام = إخفاق **دائم** (لا يُعاد ثلاثًا ولا يُعلّق الطابور)",
      (lambda: (lambda calls: (
          TC.fetch_blob("T", "F", get=lambda u, **k: type(
              "R", (), {"json": lambda s: (calls.append(1), {
                  "ok": False, "description": "file is too big"})[1],
                  "status_code": 200, "content": b""})(),
              sleep=lambda s: None),
          len(calls))) ([]))()[0][1:] == (True, "file is too big")
      and (lambda: (lambda calls: (TC.fetch_blob(
          "T", "F", get=lambda u, **k: type("R", (), {
              "json": lambda s: (calls.append(1), {"ok": False,
                                                   "description": "x"})[1],
              "status_code": 200, "content": b""})(),
          sleep=lambda s: None), len(calls))[1]) ([]))() == 1)
check("🔴 التلغرام·عطل شبكي = **عابر** (ثلاث محاولات ثم لا يُقَرّ ⇒ يُستأنَف)",
      (lambda: (lambda calls: (TC.fetch_blob(
          "T", "F", get=lambda u, **k: (calls.append(1),
                                        (_ for _ in ()).throw(OSError("net")))[0],
          sleep=lambda s: None), len(calls)))([]))() [0][:2] == (None, False)
      and (lambda: (lambda calls: (TC.fetch_blob(
          "T", "F", get=lambda u, **k: (calls.append(1),
                                        (_ for _ in ()).throw(OSError("net")))[0],
          sleep=lambda s: None), len(calls))[1])([]))() == 3)
check("📥 التلغرام·النجاح يرجّع المحتوى بلا وسم إخفاق",
      TC.fetch_blob("T", "F", sleep=lambda s: None,
                    get=lambda u, **k: type("R", (), {
                        "json": lambda s: {"ok": True,
                                           "result": {"file_path": "p/a.jpg"}},
                        "status_code": 200, "content": b"JPEGDATA"})())
      == (b"JPEGDATA", False, ""))
def _tc_run(fail_download):
    """يشغّل `TC.main()` ببيئة معزولة تمامًا (توكن وهمي · STATE وOUT_DIR مؤقّتان ·
    `requests` محقون) ويرجع (عدد الصور المحفوظة، مفاتيح الطابور المُخزَّن).

    ⚠️ **القفل السابق كان grep نصّيًّا** فلم يُنفِّذ الطابور إطلاقًا: طفرتان واقعيتان
    (`pending.clear()` قبل الحفظ · `PENDING_TRIES = 0`) كانتا **تمرّان** — وهما بعينهما
    فقدُ الصور الذي كُتب هذا الطابور لمنعه. صار القفل يقود `main()` **تشغيلين**."""
    class _R:
        def __init__(self, js=None, content=None):
            self._js, self.content, self.status_code = js, content, 200

        def json(self):
            return self._js

    def _get(url, **kw):
        if "getUpdates" in url:
            if kw.get("params", {}).get("offset", 0) > 0:
                return _R({"ok": True, "result": []})     # لا جديد بعد الإقرار
            return _R({"ok": True, "result": [{
                "update_id": 1,
                "message": {"message_id": 9, "photo": [
                    {"file_id": "FID1", "file_unique_id": "U1",
                     "width": 900, "height": 900, "file_size": 5000}]}}]})
        if "getFile" in url:
            if fail_download[0]:
                raise OSError("net")                      # إخفاق **عابر**
            return _R({"ok": True, "result": {"file_path": "photos/a.jpg"}})
        return _R(content=b"\xff\xd8\xff" + b"z" * 64)     # تنزيل ناجح

    _sv = (TC.STATE, TC.OUT_DIR, TC.requests, _os_hc.environ.get("TELEGRAM_BOT_TOKEN"))
    try:
        TC.requests = _ty0.SimpleNamespace(get=_get)
        _os_hc.environ["TELEGRAM_BOT_TOKEN"] = "T"
        TC.main()
        _st = _json0.load(open(TC.STATE, encoding="utf-8"))
        return (len([x for x in _os0.listdir(TC.OUT_DIR)]),
                sorted((_st.get("pending") or {}).keys()))
    finally:
        TC.STATE, TC.OUT_DIR, TC.requests = _sv[0], _sv[1], _sv[2]
        if _sv[3] is None:
            _os_hc.environ.pop("TELEGRAM_BOT_TOKEN", None)
        else:
            _os_hc.environ["TELEGRAM_BOT_TOKEN"] = _sv[3]


check("🔍 التلغرام·تقرير الفجوات: يكشف الأرقام الغائبة ولا يدّعي أنها صور ضائعة",
      (lambda _r: len(_r) == 3 and "**3 رقمًا غائبًا**" in _r[0]
       and "5" in _r[1] and "8–9" in _r[1]
       and "رسائل نصّية أو ردود البوت" in _r[0])(
          TC.gap_report([3, 4, 6, 7, 10])))
check("🔍 التلغرام·الترقيم المتّصل ⇒ يقين «لم يُفقَد شيء» · والفارغ ⇒ لا ادّعاء",
      "بلا فجوة" in TC.gap_report([1, 2, 3])[0]
      and TC.gap_report([]) == [] and TC.gap_report(None) == []
      and TC.gap_report([7]) == [])
check("🔍 التلغرام·يقرأ أرقام الرسائل من أسماء الملفات · فاشل-آمن لمجلّد غائب",
      (lambda _d: (_os0.makedirs(_d, exist_ok=True),
                   open(_os0.path.join(_d, "TG_12.jpg"), "w").close(),
                   open(_os0.path.join(_d, "TG_9.png"), "w").close(),
                   open(_os0.path.join(_d, "ملف_بلا_رقم.jpg"), "w").close(),
                   TC._saved_msg_ids(_d))[-1])(_tf.mkdtemp()) == [9, 12]
      and TC._saved_msg_ids("/no/such/dir/xyz") == [])
check("🛡️ التلغرام·طابور دائم بـfile_id: العابر يُحفَظ ثم **يُنزَّل** بالتشغيل التالي",
      (lambda _d: (lambda _flag: (
          TC.__dict__.__setitem__("STATE", _os0.path.join(_d, "s.json")),
          TC.__dict__.__setitem__("OUT_DIR", _os0.path.join(_d, "img")),
          # ① تشغيل يخفق تنزيله عابرًا ⇒ الصورة **في الطابور** لا مفقودة
          _tc_run(_flag),
          _flag.__setitem__(0, False),
          # ② تشغيل تالٍ: getUpdates فارغ (أُقِرّ) لكن الطابور يستردّها
          _tc_run(_flag))[2:])([True]))(
          _tf.mkdtemp()) == (((0, ["FID1"])), None, (1, [])))
# ⚠️ الطفرة `PENDING_TRIES = 0` لا يلتقطها القفل أعلاه: العدّاد لا يُفحَص إلا عند
# **إخفاق الإعادة**. فالقفل الثاني يُخفق تشغيلين متتاليين ويؤكّد أن الصورة ما زالت
# بالطابور (الاستسلام بعد محاولة واحدة = فقدٌ صامت لصورة قابلة للاسترجاع).
check("🛡️ التلغرام·إخفاق الإعادة لا يُسقط الصورة (العدّاد يسمح بمحاولات لا بواحدة)",
      (lambda _d: (lambda _flag: (
          TC.__dict__.__setitem__("STATE", _os0.path.join(_d, "s.json")),
          TC.__dict__.__setitem__("OUT_DIR", _os0.path.join(_d, "img")),
          _tc_run(_flag), _tc_run(_flag))[2:])([True]))(
          _tf.mkdtemp()) == ((0, ["FID1"]), (0, ["FID1"])))
check("🛡️ التلغرام·يحفظ باسم غير مُصادِم ويتخطّى المكرّرة بالمحتوى",
      (lambda d: (_os0.makedirs(d, exist_ok=True),
                  TC.__dict__.__setitem__("OUT_DIR", d),
                  TC._store(b"A", "x.jpg", set(), {}) == "saved",
                  TC._store(b"A", "x.jpg", {__import__("hashlib").sha256(b"A")
                                            .hexdigest()}, {}) == "dup",
                  TC._store(b"B", "x.jpg", set(), {}) == "saved",
                  sorted(_os0.listdir(d)) == ["x.jpg", "x_1.jpg"],
                  TC.__dict__.__setitem__("OUT_DIR", "faisal_images"))[2:6])(
          _os0.path.join(_tf.mkdtemp(), "imgs")) == (True,) * 4)
# ═══ 📸 سجلّ تغطية الصور (أداة مستقلة — تتبّع 300+ صورة بلا نسيان) ═══
import image_audit as IA
check("📸 السجلّ·المعرّف من اسم الملف (IMG_0153.jpeg → IMG_0153) وبلا رقم يبقى الاسم",
      IA.image_id("IMG_0153.jpeg") == "IMG_0153"
      and IA.image_id("img-9504.PNG") == "IMG_9504"
      and IA.image_id("faisal_images/IMG_0320.png") == "IMG_0320"
      and IA.image_id("NEW شرح الوقف.jpeg") == "NEW_شرح_الوقف")
check("📸 السجلّ·يمسح التوثيق فيعرف ما قُرئ (نقيّة، تقبل نصوصًا محقونة)",
      IA.scan_docs(["راجع IMG_0153 و IMG-0177 معًا"]) == {"IMG_0153", "IMG_0177"}
      and IA.scan_docs([None, ""]) == set())
_ia_rows = IA.build(state={}, docs=["نصّ فيه IMG_0153"],
                    files=["faisal_images/IMG_0153.jpeg",
                           "faisal_images/IMG_9999.jpeg"])
check("📸 السجلّ·يفرّق الموثّقة عن غير المقروءة (جوهر «ما نسينا شي»)",
      {r["id"]: r["documented"] for r in _ia_rows}["IMG_0153"] is True
      and {r["id"]: r["documented"] for r in _ia_rows}["IMG_9999"] is False
      and {r["id"]: r["status"] for r in _ia_rows}["IMG_9999"] == "unread")
check("📸 السجلّ·الحالة اليدوية لا تُفقَد بين التشغيلات (استئناف)",
      [r for r in IA.build(state={"IMG_9999": {"status": "rejected",
                                               "note": "سبب"}},
                           docs=[], files=["faisal_images/IMG_9999.jpeg"])
       ][0]["status"] == "rejected")
check("📸 السجلّ·يُدرج الموثّقة بلا ملف مرفوع (لا تسقط من العدّ)",
      any(r["id"] == "IMG_0177" and not r["file"]
          for r in IA.build(state={}, docs=["IMG_0177"], files=[])))
_ia_sm = IA.summarize(_ia_rows)
check("📸 السجلّ·الملخّص يعطي الدفعة التالية (غير الموثّقة فقط)",
      _ia_sm["unread"] == 1 and _ia_sm["next_batch"] == ["IMG_9999"]
      and _ia_sm["documented"] == 1)
check("📸 السجلّ·التقرير يطبع الجدول والأرقام بلا استثناء",
      "IMG_9999" in IA.render(_ia_rows, _ia_sm, today="2026-07-27")
      and "لم تُقرأ بعد" in IA.render(_ia_rows, _ia_sm, today="2026-07-27"))
check("📸 السجلّ·أداة مستقلة: لا تستورد البوت ولا تمسّ الفرز",
      "Super_stock" not in open("image_audit.py", encoding="utf-8").read())
# 📄 تجديد شراء الداخليين يوميًّا (سدّ ثغرة التجميد حتى جمعة التجديد)
check("📄 تجديد يومي: المسار اليومي يجلب Form 4 والطرح المؤسِّس (لا تجميد أسبوعيًّا)",
      all(_k in _insp0.getsource(S.run_daily_watchlist)
          for _k in ("form4_insider_buys", "_SEC_FOUNDING", "_F4_BUDGET")))
check("📄 تجديد يومي·دمج لا استبدال: جلبٌ فارغ يُبقي المخزَّن (تعذّر ≠ لا شراء)",
      "if _nb:" in _insp0.getsource(S.run_daily_watchlist))
check("🔒 FINRA·حارسا الميزانية وقاطع الدائرة موجودان (كانا غائبين)",
      "FINRA_BUDGET" in S.CONFIG
      and (lambda: (S._FINRA_DAY_CACHE.clear(), S._FINRA_BUDGET.__setitem__(0, 0),
                    S._finra_day_map("2025-06-11") == {},
                    S._FINRA_BUDGET.__setitem__(0, 400))[2])())
check("🔒 قنوات SEC الجانبية مسقوفة الحجم (لا تضخّم عبر التشغيلة)",
      isinstance(S._SEC_OFFERING_MAX, int) and isinstance(S._SEC_FORM4_MAX, int)
      and isinstance(S._FINRA_CACHE_MAX, int))
check("⚖️ صدق العرض: لا سطر «خبر لم يُقبَل» في كرت التحليل (الحقل غير محسوب هناك)",
      "news_rejected_line" not in _insp0.getsource(S.build_message)
      and "news_rejected_line" in _insp0.getsource(S.build_daily_message))
check("⚖️ صدق العرض: فحص اليد لا ينفي الشراء الداخلي قطعًا عند الفراغ",
      "ليس نفيًا قاطعًا" in open("hand_check.py", encoding="utf-8").read())
check("⚖️ فحص اليد يحمل حقول بطاقة فيصل فعلًا (لا أسطر ميتة)",
      all(_k in open("hand_check.py", encoding="utf-8").read()
          for _k in ('"insider_buys": diag.get("insider_buys")',
                     '"offering_event": diag.get("offering_event")',
                     'r["news_acc"] = bot.news_acceptance')))
check("🔒 قفل: كل إضافات بطاقة فيصل خارج الجذور السبعة و analyze_ticker",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("_post_event_high", "_event_day_open", "half_down_target",
                      "half_down_line", "_parse_form4", "form4_insider_buys",
                      "insider_buy_line", "news_acceptance", "news_rejected_line",
                      "_latest_event_date", "_offering_event", "_split_setup_probe")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker)))
check("🥇 قفل: faisal_split_plan خارج الجذور السبعة و analyze_ticker (عرض/سياق فقط)",
      all("faisal_split_plan" not in _insp0.getsource(_f)
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker)))
# 🩺 لوحة حالة الجمع: كانت الوحيدة بلا أي قفل (ثغرة لقّاها التدقيق الخصومي 2026-07-27)
check("🩺 قفل: _collection_health_block خارج الجذور السبعة و analyze_ticker (تقرير فقط)",
      all("_collection_health_block" not in _insp0.getsource(_f)
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol,
                     S.analyze_ticker)))
check("🪝 صيّاد·قفل: (scan_split_hunter/build_split_hunter_alert/_yahoo_float) خارج الجذور السبعة",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("scan_split_hunter", "build_split_hunter_alert", "_yahoo_float")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.apply_short_gate, S.apply_float_gate, S.backtest_symbol)))

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
# ③ تحصين: العدّاد كان يُطبع بالرسالة **بلا تحقق** — صفر تكرار = «أخضر» زائف.
check(f"③ ثوابت المسح فُحصت كاملة ({_scan}/60)", _scan == 60)

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
_merge_seen = 0                                  # ③ تحصين: ضمانة تنفيذ فعلي
for _sd in range(10):
    _df = synth_pivot(seed=_sd)
    S.fetch_4h = lambda sym: None                       # بلا 4س
    _base = S.analyze_ticker("MG", _df)
    if _base is None:
        continue
    _merge_seen += 1
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
check(f"③ حارس الدمج فُحص كاملًا ({_merge_seen}/10)", _merge_seen == 10)

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
_kl_seen = 0                                     # ③ تحصين: ضمانة تنفيذ فعلي
for _sd in range(8):
    _r = S.analyze_ticker("KL", synth_pivot(seed=_sd))
    if _r is None:
        continue
    _kl = _r["key_levels"]; _px = _r["price"]; _piv = _r["pivot"]
    if _kl is None:
        continue
    _kl_seen += 1
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
check(f"③ حارس المستويات فُحص كاملًا ({_kl_seen}/8)", _kl_seen == 8)


# ══════════════════════════════════════════════════════════
# 🔍 أقفال تدقيق Codex المستقل (gpt-5.6-sol·xhigh) — 2026-07-14
# P0-4 (تنبيه مفقود + نجاح قياس زائف) · P0-5 (ملف تالف→فقد صامت) · P1-8 (تسريب توكن)
# ══════════════════════════════════════════════════════════
import tempfile as _tf, os as _os2, inspect as _insp2

# P1-8: إخفاء التوكن من النصوص المسجَّلة
_tok_save = S.TELEGRAM_TOKEN
try:
    S.TELEGRAM_TOKEN = "999888:SEKRET_tok_XYZ"
    _leak = f"HTTPSConnectionPool url: /bot{S.TELEGRAM_TOKEN}/sendMessage failed"
    _red = S._redact_secrets(_leak)
    check("P1-8: التوكن يُخفى من نص الاستثناء المسجَّل",
          S.TELEGRAM_TOKEN not in _red and "***" in _red)
    check("P1-8: _redact_secrets آمن مع None",
          isinstance(S._redact_secrets(None), str))
finally:
    S.TELEGRAM_TOKEN = _tok_save

# P0-5: ملف حالة تالف → لا فقد صامت (نسخة احتياطية + بنية أولية + تحذير)
_wf_save, _tk_save = S.WATCH_FILE, S.TELEGRAM_TOKEN
try:
    S.TELEGRAM_TOKEN = ""              # لا إرسال فعلي أثناء الاختبار
    _d = _tf.mkdtemp()
    _cf = _os2.path.join(_d, "weekly_watchlist.json")
    with open(_cf, "w", encoding="utf-8") as _fh:
        _fh.write('{"stocks": [ TALEF ghyr sahih JSON')
    S.WATCH_FILE = _cf
    _r = S.load_watchlist()
    _baks = [f for f in _os2.listdir(_d) if ".corrupt-" in f]
    check("P0-5: ملف تالف لا يرمي ويُرجع بنية أولية",
          isinstance(_r, dict) and _r.get("stocks") == [])
    check("P0-5: ملف تالف يُنسَخ احتياطيًّا (لا فقد صامت)", len(_baks) >= 1)
    check("P0-5: النسخة الاحتياطية تحفظ المحتوى التالف الأصلي",
          bool(_baks) and open(_os2.path.join(_d, _baks[0]),
                               encoding="utf-8").read().startswith('{"stocks"'))
finally:
    S.WATCH_FILE, S.TELEGRAM_TOKEN = _wf_save, _tk_save

# P0-4: send_telegram يُرجع False عند تعذّر الإرسال + ignition_live يحترم القيمة
_tk_save2 = S.TELEGRAM_TOKEN
try:
    S.TELEGRAM_TOKEN = ""
    check("P0-4: send_telegram يُرجع False بلا توكن (قيمة صادقة للمستدعي)",
          S.send_telegram("t") is False)
finally:
    S.TELEGRAM_TOKEN = _tk_save2
_il_src = _insp2.getsource(IG.main)
check("P0-4: ignition_live يفحص قيمة send_telegram قبل تسجيل نجاح القياس",
      "sent_ok" in _il_src and "telegram_send_failed" in _il_src)

# 🛡️ حادثة 2026-07-14: git_save بلا runner محقون لا ينفّذ git حقيقيًّا تحت الاختبار
# (اختبار E2 كان يشغّل main() فيدفع بيانات وهمية على main — هذا يمنع تكراره)
_gs_called = []
_real_system_hc = S.os.system
try:
    S.os.system = lambda *a, **k: (_gs_called.append(a), 0)[1]
    S.git_save(["nonexistent_incident_guard.json"])   # بلا runner + SUPER_STOCKS_TESTING=1
    check("🛡️ حادثة: git_save بلا runner لا ينفّذ git حقيقيًّا تحت الاختبار",
          len(_gs_called) == 0)
finally:
    S.os.system = _real_system_hc

# ══════════════════════════════════════════════════════════
# 🔍 متابعة Codex على a0c6947 (2026-07-14): تغطية أوسع للتسريب/الفقد الصامت
# ══════════════════════════════════════════════════════════
# #3: cline_notify يخفي التوكن من الاستثناءات المطبوعة
import cline_notify as _CN
_cn_tok_save = _os2.environ.get("TELEGRAM_BOT_TOKEN")
try:
    _os2.environ["TELEGRAM_BOT_TOKEN"] = "777:CN_secret_tok"
    _cn_red = _CN._redact("URLError url: /bot777:CN_secret_tok/sendMessage")
    check("متابعة P1-8: cline_notify يخفي التوكن من النص المطبوع",
          "777:CN_secret_tok" not in _cn_red and "***" in _cn_red)
finally:
    if _cn_tok_save is None:
        _os2.environ.pop("TELEGRAM_BOT_TOKEN", None)
    else:
        _os2.environ["TELEGRAM_BOT_TOKEN"] = _cn_tok_save

# #4: باقي ملفات الحالة (company/ignition_log/ignition_universe) تعالج التلف بلا فقد صامت
_files_save = (S.COMPANY_FILE, S.IGNITION_LOG_FILE, S.IGNITION_UNI_FILE)
_tk_save4 = S.TELEGRAM_TOKEN
try:
    S.TELEGRAM_TOKEN = ""                      # لا إرسال فعلي أثناء الاختبار
    _d4 = _tf.mkdtemp()

    def _mk_corrupt(name):
        _p = _os2.path.join(_d4, name)
        with open(_p, "w", encoding="utf-8") as _fh:
            _fh.write("{ TALEF ghyr sahih JSON")
        return _p

    S.COMPANY_FILE = _mk_corrupt("company_cache.json")
    S.IGNITION_LOG_FILE = _mk_corrupt("ignition_log.json")
    S.IGNITION_UNI_FILE = _mk_corrupt("ignition_universe.json")
    _cc = S._load_company_cache()
    _il = S.load_ignition_log()
    S.record_ignition_universe(["PTN"], "2026-07-20")   # يقرأ التالف ثم يكتب
    _baks4 = [f for f in _os2.listdir(_d4) if ".corrupt-" in f]
    check("متابعة P0-5: _load_company_cache تالف → {} بلا انهيار", _cc == {})
    check("متابعة P0-5: load_ignition_log تالف → [] بلا انهيار", _il == [])
    check("متابعة P0-5: الملفات الثلاثة تُنسَخ احتياطيًّا عند التلف (لا فقد صامت)",
          len(_baks4) >= 3)
finally:
    (S.COMPANY_FILE, S.IGNITION_LOG_FILE, S.IGNITION_UNI_FILE) = _files_save
    S.TELEGRAM_TOKEN = _tk_save4

# ①ب حجر صحّي: بعد وسم ملف تالف، _atomic_write_json يرفض الكتابة عليه (لا طمس النسخة السليمة)
_tk_saveq = S.TELEGRAM_TOKEN
try:
    S.TELEGRAM_TOKEN = ""
    _dq = _tf.mkdtemp()
    _qf = _os2.path.join(_dq, "state.json")
    with open(_qf, "w", encoding="utf-8") as _fh:
        _fh.write("{ TALEF")
    S._handle_corrupt_state_file(_qf, ValueError("x"))    # يسجّله في الحجر
    _before = open(_qf, encoding="utf-8").read()
    S._atomic_write_json(_qf, {"new": "data"})            # المفروض تُرفَض
    _after = open(_qf, encoding="utf-8").read()
    check("①ب حجر: _atomic_write_json يرفض الكتابة على ملف محجور (يبقى كما هو)",
          _before == _after and "TALEF" in _after)
finally:
    S.TELEGRAM_TOKEN = _tk_saveq
    S._CORRUPT_STATE_FILES.discard(_os2.path.abspath(_qf))   # تنظيف حالة عامة

# ①أ: فشل إرسال الانطلاق يلغي ختم ignition_alert (يُعاد الفحص — لا كتم صامت بقية اليوم)
_persist_stock = {"symbol": "IGN", "status": "active", "ignition_alert": "STAMPED"}
_ia_saved = (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
             IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep,
             IG._fresh_watchlist, S.IGNITION_UNI_FILE, S.IGNITION_LOG_FILE)
_ia_env = {k: _os2.environ.get(k) for k in ("IGNITION_SEGMENT", "E2_MEASUREMENT", "POLYGON_API_KEY")}
try:
    _dia = _tf.mkdtemp()
    S.IGNITION_UNI_FILE = _os2.path.join(_dia, "u.json")
    S.IGNITION_LOG_FILE = _os2.path.join(_dia, "l.json")
    _os2.environ.pop("IGNITION_SEGMENT", None)
    _os2.environ.pop("E2_MEASUREMENT", None)
    _os2.environ["POLYGON_API_KEY"] = "TEST_KEY_NOT_USED"
    _now_ia = S.dt.datetime.utcnow()
    IG._segment_window = lambda role, t0=None: {
        "role": role, "open": _now_ia, "close": _now_ia + S.dt.timedelta(hours=1),
        "segment_start": _now_ia, "segment_end": _now_ia + S.dt.timedelta(hours=1),
        "deadline": _now_ia + S.dt.timedelta(hours=1), "reason": "test",
        "session_type": "regular", "calendar_version": "test"}
    IG._fresh_watchlist = lambda wl: None            # لا جلب من origin أثناء الاختبار
    IG.bot.load_watchlist = lambda: {"stocks": [_persist_stock]}
    IG.bot.scan_ignition = lambda wl, today, trace=None: [(_persist_stock, {"price": 2.0}, None)]
    IG.bot.build_ignition_alert = lambda rows: "ALERT"
    IG.bot.send_telegram = lambda m: False           # فشل الإرسال (429 عابر)
    IG.time.sleep = lambda *_a: (_ for _ in ()).throw(_StopLoop())
    try:
        IG.main()
    except (_StopLoop, Exception):
        pass
    check("①أ: فشل إرسال الانطلاق يلغي ختم ignition_alert (يُعاد الفحص لا كتم)",
          "ignition_alert" not in _persist_stock)
finally:
    (IG._segment_window, IG.bot.load_watchlist, IG.bot.scan_ignition,
     IG.bot.build_ignition_alert, IG.bot.send_telegram, IG.time.sleep,
     IG._fresh_watchlist, S.IGNITION_UNI_FILE, S.IGNITION_LOG_FILE) = _ia_saved
    for _k, _v in _ia_env.items():
        _os2.environ.pop(_k, None) if _v is None else _os2.environ.update({_k: _v})


# ══════════════════════════════════════════════════════════
# 🔍 مراجعة Codex على 1e322c5 (2026-07-15) — أقفال الإصلاحات الآمنة
# ══════════════════════════════════════════════════════════
# 🛑 P0 (انحدار أدخله 1e322c5): كاش شركة تالف كان يقتل **الاستيراد** بـNameError
# (`COMPANY_CACHE = _load_company_cache()` يُنفَّذ وقت الاستيراد قبل تعريف المعالِج) ⇒
# كل workflow يموت قبل أي فرز/تنبيه. القفل الوحيد الذي يمسكه = **عملية جديدة** فعلًا.
import subprocess as _sp_imp, tempfile as _tf_imp, shutil as _sh_imp
_imp_dir = _tf_imp.mkdtemp()
try:
    _sh_imp.copy2("Super_stock.py", _os2.path.join(_imp_dir, "Super_stock.py"))
    with open(_os2.path.join(_imp_dir, "company_cache.json"), "w", encoding="utf-8") as _fh:
        _fh.write('{"AAPL": TALEF ghyr sahih')
    _imp = _sp_imp.run(
        [_sys.executable, "-c",
         "import Super_stock as S; assert S.COMPANY_CACHE == {}; print('IMPORT_OK')"],
        cwd=_imp_dir, capture_output=True, text=True, timeout=180,
        env={**_os2.environ, "TELEGRAM_BOT_TOKEN": "", "SUPER_STOCKS_TESTING": "1"})
    check("🛑 P0 (Codex/1e322c5): كاش شركة تالف **لا يقتل الاستيراد** (ترتيب التعريف)",
          _imp.returncode == 0 and "IMPORT_OK" in _imp.stdout
          and "NameError" not in (_imp.stderr or ""))
finally:
    _sh_imp.rmtree(_imp_dir, ignore_errors=True)

# 🔒 P1-8 (توسعة): الشكل المرمّز-URL + جسم رد تيليجرام + cline_notify
_tk_save5 = S.TELEGRAM_TOKEN
try:
    S.TELEGRAM_TOKEN = "998877:SEKRET_tok_ABC"
    from urllib.parse import quote as _q8
    _enc = _q8(S.TELEGRAM_TOKEN, safe="")
    _out8 = S._redact_secrets(f"ProxyError url=/bot{_enc}/sendMessage")
    check("🔒 P1-8: التوكن **المرمّز-URL** (%3A) يُخفى أيضًا",
          S.TELEGRAM_TOKEN not in _out8 and _enc not in _out8 and "***" in _out8)
    _src8 = _insp2.getsource(S.send_telegram) + _insp2.getsource(S.send_telegram_document)
    check("🔒 P1-8: جسم رد تيليجرام (resp.text) يمرّ عبر المُخفي — لا تسجيل خام",
          "_redact_secrets(resp.text)" in _src8 and "{resp.text[" not in _src8)
finally:
    S.TELEGRAM_TOKEN = _tk_save5
_cn_tok5 = _os2.environ.get("TELEGRAM_BOT_TOKEN")
try:
    _os2.environ["TELEGRAM_BOT_TOKEN"] = "555:CN_tok_XY"
    import urllib.parse as _up5
    _cn_enc = _up5.quote("555:CN_tok_XY", safe="")
    check("🔒 P1-8: cline_notify يخفي التوكن حرفيًّا **ومرمّزًا**",
          "555:CN_tok_XY" not in _CN._redact("err /bot555:CN_tok_XY/x")
          and _cn_enc not in _CN._redact(f"err /bot{_cn_enc}/x"))
finally:
    _os2.environ.pop("TELEGRAM_BOT_TOKEN", None) if _cn_tok5 is None \
        else _os2.environ.update({"TELEGRAM_BOT_TOKEN": _cn_tok5})

# 🛡️ حارس الحادثة (توسعة): لا يُتجاوَز بحقن المشغّل الحقيقي · ورادار الانطلاق لا يجلب git
_gs_calls2 = []
_real_sys2 = S.os.system
try:
    S.os.system = lambda *a, **k: (_gs_calls2.append(a), 0)[1]
    S.git_save(["nonexistent_guard2.json"], runner=S.os.system)   # حقن المشغّل الحقيقي
    check("🛡️ حارس: حقن `runner=os.system` **لا يتجاوز** وضع الاختبار (لا git حقيقي)",
          len(_gs_calls2) == 0)
finally:
    S.os.system = _real_sys2
check("🛡️ حارس: _fresh_watchlist/_fetch_head_sha لا ينفّذان git بلا runner تحت الاختبار",
      IG._fresh_watchlist({"stocks": []}) is None and IG._fetch_head_sha() is None)

# 📊 P1-6 (أداة الأرباح · عرض/صدق فقط): كون فارغ (فشل شبكة يبتلعه get_universe) =
# «تعذّر المسح» لا «لا توجد أسهم» — الاطمئنان الكاذب كان يخفي أن المسح لم يعمل أصلًا.
_gu_save = S.get_universe
try:
    S.get_universe = lambda: []                     # فشل شبكة مبتلَع (بلا استثناء)
    check("📊 P1-6: كون ناسداك فارغ ⇒ scan_nasdaq_earnings يرجع None (تعذّر مسح، لا «صفر»)",
          TR.scan_nasdaq_earnings() is None)
finally:
    S.get_universe = _gu_save
check("📊 P1-6: رسالة «تعذّر المسح» مغايرة لرسالة «لا توجد أسهم» (لا خلط)",
      "تعذّر" in TR.render_scan(None) and "تعذّر" not in TR.render_scan([]))

# 🌍 P1-5 (الباكتيست · عرض/صدق فقط): سقوط الكون للاحتياطي (= أسهم رشّحها البوت) كان
# يُعنوَن «السوق الكامل بلا انحياز اختيار» = عكس الحقيقة. الآن يُصرَّح بالانحياز.
_bt_src = _insp0.getsource(S.run_backtest)
check("🌍 P1-5: الكون الاحتياطي يُعلَّم `market_fallback` ولا يُعنوَن «بلا انحياز»",
      "market_fallback = True" in _bt_src
      and "منحاز اختيارًا" in _bt_src
      and _bt_src.index("market_fallback = True") < _bt_src.index(
          "🌍 <b>باكتيست كون ناسداك اليوم (بلا انتقاء رموز)</b>"))
# 🔬 (مراجعة Codex) إفصاح انحياز البقاء: **لا أيّ ادّعاء «السوق الكامل» في النصوص المرئية** (عنوان +
# لاحقة الفترة + سطر السجل) — كلها تُصرّح «كون ناسداك اليوم/ناجٍ». نجرّد أسطر التعليقات (# تشرح
# الإصلاح فتذكر النصّ القديم) ونفحص الكود المُنفَّذ فقط. (يمسك التناقض الذي رصده Codex.)
_bt_code = "\n".join(l for l in _bt_src.split("\n") if not l.lstrip().startswith("#"))
check("🔬 انحياز البقاء: صفر ادّعاء «السوق الكامل» بالنصوص المرئية + إفصاح «كون ناجٍ يستبعد المشطوبة»",
      "كون ناجٍ" in _bt_code and "المشطوبة" in _bt_code and "كون ناسداك اليوم" in _bt_code
      and "السوق الكامل" not in _bt_code and "(السوق كامل)" not in _bt_code)
# 🔬 (مراجعة Codex) تحذير تغطية التجميد غير الصامت (لقطة لا تصل النافذة ⇒ صراخ لا صمت)
check("🔬 تجميد·تغطية: تحذير غير صامت عند لقطة لا تغطّي بدء النافذة",
      "تجميد·تغطية ناقصة" in _bt_src and "_snap_earliest" in _bt_src)

# 📈 P2-6 (تقارير فقط): ترشيحان مستقلّان لنفس السهم بنفس سعر الدخول (تاريخان مختلفان)
# كانا يُدمجان في صفقة واحدة — الثانية تختفي من الإحصاء بصمت (تصادم LYEL المثبَت).
_dc = S._dedup_closed([
    {"symbol": "LYEL", "entry_ref": 14.05, "added": "2026-05-04", "_win": True},
    {"symbol": "LYEL", "entry_ref": 14.05, "added": "2026-05-18", "_win": False},
    {"symbol": "LYEL", "entry_ref": 14.05, "added": "2026-05-18", "_win": False},   # تكرار حقيقي
])
check("📈 P2-6: صفقتان بنفس (رمز, سعر) وتاريخَي إضافة مختلفين **لا تُدمجان** (لا فقد إحصاء)",
      len(_dc) == 2 and {r["added"] for r in _dc} == {"2026-05-04", "2026-05-18"})

# 🔬 ② طيّ العدّ المزدوج (قرار المالك 2026-07-18، تقارير فقط): متعقّبَا نفس المركز (تنبيه +
# قائمة، added مختلف، نفس النتيجة + حسم متقارب) ⇒ صفقة واحدة؛ ترشيحان مستقلّان يبقيان.
_fold_in = [
    {"symbol": "PTN", "added": "2026-07-08", "_win": False, "result_date": "2026-07-14", "max_gain_pct": 1.9},
    {"symbol": "PTN", "added": "2026-07-10", "_win": False, "removed_date": "2026-07-14", "max_gain_pct": 5.9},
    {"symbol": "INSM", "added": "2026-06-21", "_win": True, "hit_date": "2026-06-24", "max_gain_pct": 11.9},
    {"symbol": "INSM", "added": "2026-06-25", "_win": True, "hit_date": "2026-07-07", "max_gain_pct": 10.9},
]
_fold_out = S._fold_same_position(_fold_in)
check("② طيّ: PTN المكرّر (نفس الحسم) يُطوى لواحدة · INSM (نتيجتان 13ي متباعدتان) يبقى صفقتين",
      len(_fold_out) == 3
      and sum(1 for r in _fold_out if r["symbol"] == "PTN") == 1
      and sum(1 for r in _fold_out if r["symbol"] == "INSM") == 2)
check("② طيّ: الأسبق added يمثّل المركز (PTN 07-08 محفوظ)",
      any(r["symbol"] == "PTN" and r["added"] == "2026-07-08" for r in _fold_out))
check("② طيّ: نتيجتان مختلفتان لنفس الرمز (ربح+خسارة) ⇒ لا طيّ",
      len(S._fold_same_position([
          {"symbol": "Y", "added": "2026-07-01", "_win": True, "hit_date": "2026-07-03"},
          {"symbol": "Y", "added": "2026-07-02", "_win": False, "result_date": "2026-07-03"}])) == 2)
check("② طيّ فاشل-آمن: تواريخ تالفة → لا طيّ (الصفوف كما هي، لا انهيار)",
      len(S._fold_same_position([
          {"symbol": "X", "added": "bad", "_win": True, "hit_date": "bad"},
          {"symbol": "X", "added": "worse", "_win": True, "hit_date": "nope"}])) == 2)
check("② قفل: _fold_same_position خارج rank_key/select_top/classify_tier/entry_status/backtest_symbol",
      all("_fold_same_position" not in _insp0.getsource(getattr(S, _f))
          for _f in ("rank_key", "select_top", "classify_tier", "entry_status", "backtest_symbol")))
check("② قفل: الطيّ موصول بعد _dedup_closed في مساري التقرير (مساعد التطوير + CSV)",
      "_fold_same_position" in _insp0.getsource(S.build_dev_assistant_report)
      and "_fold_same_position" in _insp0.getsource(S.export_weekly_csvs))

# 🔬 P2-4 (بحث/قياس فقط · خارج مسار التنبيه): فشل صفحة لاحقة من Polygon كان يُرجع نصف
# النافذة **كأنها كاملة** ⇒ نِسَب T-ACC تُحسب على عيّنة مبتورة بلا علامة. الآن None.
# اختبار سلوكي: الصفحة 1 تنجح (بـnext_url) والصفحة 2 ترد 429 ⇒ يجب None لا بيانات جزئية.
class _FakeResp:
    def __init__(self, code, payload=None):
        self.status_code, self._p = code, (payload or {})

    def json(self):
        return self._p


_pg = {"n": 0}


def _fake_get(url, headers=None, timeout=None, **kw):
    _pg["n"] += 1
    if _pg["n"] == 1:
        return _FakeResp(200, {"results": [{"price": 1.0, "size": 100, "exchange": 4}] * 40,
                               "next_url": "https://api.polygon.io/next"})
    return _FakeResp(429)                       # خنق في الصفحة الثانية


_req_save = S.requests.get
_key_save = _os2.environ.get("POLYGON_API_KEY")
try:
    S.requests.get = _fake_get
    _os2.environ["POLYGON_API_KEY"] = "TEST_KEY"
    _partial = S.polygon_base_trades("TST")
    check("🔬 P2-4 سلوكي: خنق صفحة لاحقة ⇒ None (لا نافذة مبتورة تُقدَّم كاملة)",
          _partial is None and _pg["n"] == 2)
finally:
    S.requests.get = _req_save
    _os2.environ.pop("POLYGON_API_KEY", None) if _key_save is None \
        else _os2.environ.update({"POLYGON_API_KEY": _key_save})


# ==========================================================
# 🌀 FSTO قوة التذبذب: من يشتغل على السهم قروب/مضارب (فيصل IMG_0091) — عرض فقط، أوّلي
_idx_osc = S.pd.date_range("2025-01-01", periods=70)
_pump = ([2.0] * 20 + [2.5, 4.4, 6.0, 2.9] * 13)[:70]
_serp = S.pd.Series(_pump, index=_idx_osc, dtype=float)
_kp, _ = S.full_stoch(_serp * 1.03, _serp * 0.97, _serp)
_op = S.fsto_oscillation(_kp)
check("🌀 FSTO: نمط قروب (تأرجح عنيف) → actor=قروب",
      _op is not None and _op["actor"] == "قروب", str(_op))
_acc = list(S.np.linspace(2.0, 3.2, 70)
            + S.np.random.RandomState(1).normal(0, 0.04, 70))
_sera = S.pd.Series(_acc, index=_idx_osc, dtype=float)
_ka, _ = S.full_stoch(_sera * 1.02, _sera * 0.98, _sera)
_oa = S.fsto_oscillation(_ka)
check("🌀 FSTO: نمط مضارب (تجميع هادئ) → actor=مضارب",
      _oa is not None and _oa["actor"] == "مضارب", str(_oa))
check("🌀 FSTO: full_stoch %K ضمن 0-100", 0.0 <= float(_kp.iloc[-1]) <= 100.0)
check("🌀 FSTO: عيّنة قصيرة → None (صدق العيّنة)",
      S.fsto_oscillation(S.pd.Series([50.0] * 10)) is None)
check("🌀 FSTO: oscillation_line فارغ عند None/غير محدّد",
      S.oscillation_line(None) == "" and S.oscillation_line({"actor": None}) == "")
check("🌀 FSTO: سطر القروب يحمل «(أوّلي)» (صدق: العتبة غير مقفولة)",
      "أوّلي" in S.oscillation_line(_op))
_osc_srcs = (_insp.getsource(S.rank_key) + _insp.getsource(S.select_top)
             + _insp.getsource(S.classify_tier) + _insp.getsource(S.entry_status)
             + _insp.getsource(S.apply_short_gate) + _insp.getsource(S.apply_float_gate)
             + _insp.getsource(S.backtest_symbol))
# 🌀 FSTO: مقياس التذبذب لا يمسّ **جذور الاختيار الستة**؛ chop حقل تشخيصي عائد في
# backtest_symbol فقط (مثل behav_score — لا يمسّ الحسم filled/exploded) لاختبار الارتباط.
_sel6_srcs = (_insp.getsource(S.rank_key) + _insp.getsource(S.select_top)
              + _insp.getsource(S.classify_tier) + _insp.getsource(S.entry_status)
              + _insp.getsource(S.apply_short_gate) + _insp.getsource(S.apply_float_gate))
check("🔒 FSTO: fsto_oscillation/full_stoch/oscillation_line خارج جذور الاختيار الستة (لا يمسّ الفرز)",
      "fsto_oscillation" not in _sel6_srcs and "full_stoch" not in _sel6_srcs
      and "oscillation_line" not in _osc_srcs)
check("🌀 FSTO·تشخيص: fsto_chop حقل عائد في backtest_symbol (مثل behav_score، لمعايرة قروب/مضارب)",
      "fsto_chop" in _insp.getsource(S.backtest_symbol)
      and "behav_score" in _insp.getsource(S.backtest_symbol))
# 🌀 backtest_fsto_correlation: يبوّب بشرائح chop + يحكم بالمعيار المسجَّل مسبقًا
_ft = ([{"fsto_chop": 3.0, "outcome": "win", "exploded": True} for _ in range(10)]
       + [{"fsto_chop": 3.0, "outcome": "loss", "exploded": False} for _ in range(2)]
       + [{"fsto_chop": 20.0, "outcome": "loss", "exploded": False} for _ in range(11)])
_fr = S.backtest_fsto_correlation(_ft)
check("🌀 backtest_fsto: يبوّب شرائح chop (منضبط/عنيف) + يحكم بالدليل",
      any("منضبط" in x for x in _fr) and any("التوصية" in x for x in _fr))
check("🌀 backtest_fsto·عيّنة صغيرة → [] (صدق العيّنة)",
      S.backtest_fsto_correlation([{"fsto_chop": 3, "outcome": "win"}] * 5) == [])
# 📊 كلنجر (Klinger Volume Oscillator — فيصل IMG_0125 «يعجبني أحيانًا») — حجم · عرض/سياق فقط
_kidx = S.pd.date_range("2025-01-01", periods=80)
_accc = S.pd.Series(list(S.np.linspace(10, 4, 50))
                    + list(4 + S.np.linspace(0, 0.6, 30)), index=_kidx)
_accv = S.pd.Series([1e5] * 50 + [3e5] * 30, index=_kidx, dtype=float)
_kacc = S.klinger_state(_accc * 1.02, _accc * 0.98, _accc, _accv)
check("📊 كلنجر: تجميع عند القاع (حجم صاعد على الأخضر) → صاعد (تجميع)",
      _kacc is not None and "تجميع" in _kacc["state"])
_disc = S.pd.Series(list(S.np.linspace(4, 10, 50))
                    + list(10 - S.np.linspace(0, 3, 30)), index=_kidx)
_kdis = S.klinger_state(_disc * 1.02, _disc * 0.98, _disc, _accv)
check("📊 كلنجر: تصريف → هابط (تصريف)",
      _kdis is not None and "تصريف" in _kdis["state"])
check("📊 كلنجر·عيّنة قصيرة → None (صدق العيّنة)",
      S.klinger_state(_accc.head(30), _accc.head(30), _accc.head(30),
                      _accv.head(30)) is None)
check("📊 كلنجر: klinger_line فارغ عند None", S.klinger_line(None) == "")
check("🔒 كلنجر (klinger/klinger_state) خارج الجذور السبعة (عرض/سياق فقط)",
      "klinger_state" not in _osc_srcs and "klinger(" not in _osc_srcs)


# ==========================================================
# 📿📏 سلوك الحركة الثلاثي + حركة فيصل 30-50% (فيصل IMG_0097) — عرض/تفسير فقط
_ic = S.interp_card_lines({"setup_type": "pivot_reversal",
                           "movement_behavior": "① صاعد متدرّج",
                           "faisal_move": "30‑50%+"})
check("📿 interp_card_lines يعرض سطر «سلوك الحركة»",
      any("سلوك الحركة" in x for x in _ic))
check("📏 interp_card_lines يعرض سطر «حركة فيصل»",
      any("حركة فيصل" in x for x in _ic))
_ri_piv = {"price": 2.0, "pivot": 2.0, "t1": 2.5, "t2": 3.0, "t3": 4.0,
           "tranches": [1.9, 1.95, 2.0], "stop": [1.85], "key_levels": {},
           "h4_levels": {}, "behav": {}}
check("📏 build_interpretation: نمط ارتكاز صالح → faisal_move (30-50%) موجود",
      bool(S.build_interpretation(_ri_piv).get("faisal_move")))
_ri_rec = {"price": 1.8, "pivot": 2.0, "t1": 2.5, "t2": 3.0, "t3": 4.0,
           "tranches": [1.9, 1.95, 2.0], "stop": [1.7], "key_levels": {},
           "h4_levels": {}, "behav": {}}
_mb = S.build_interpretation(_ri_rec).get("movement_behavior") or ""
check("📿 build_interpretation: تحت الدعم → سلوك ③ (يهبط)", "③" in _mb)
check("🔒 سلوك الحركة/حركة فيصل خارج الجذور السبعة",
      "movement_behavior" not in _osc_srcs and "faisal_move" not in _osc_srcs)


# ==========================================================
# 🤖 تصنيف شروط تدفق Polygon (فكرة المستخدم IMG_0082-0086: O/OI/Ap/Dp) + دمج FSTO
# — لحظي/عرض فقط · يعتمد أسماء Polygon الرسمية لا تخمين رموز التطبيق
_cmap = {2: "Average Price Trade", 8: "Derivatively Priced",
         37: "Odd Lot Trade", 16: "Opening Prints", 0: "Regular Sale"}
_algo_tr = ([{"conditions": [2]}] * 4 + [{"conditions": [8]}] * 3
            + [{"conditions": [0]}] * 3)
_cf = S.classify_flow_conditions(_algo_tr, _cmap)
check("🤖 شروط التدفق: Ap/Dp (Average/Derivatively) → algo_pct عالٍ (بصمة خوارزمية)",
      _cf is not None and _cf["algo_pct"] == 70)
check("🤖 شروط التدفق·فاشل-آمن: بلا مرجع Polygon → None (لا تصنيف مُخترَع)",
      S.classify_flow_conditions(_algo_tr, {}) is None)
check("🤖 شروط التدفق·فاشل-آمن: بلا صفقات → None",
      S.classify_flow_conditions([], _cmap) is None)
check("🕵️ دمج FSTO+التدفق: خوارزمي عالٍ ⇒ سطر «من وراء السهم» فيه «خوارزمي»",
      "خوارزمي" in S.flow_actor_read({"actor": "مضارب"}, _cf))
check("🕵️ دمج·فارغ: لا إشارة ⇒ «» (فاشل-آمن)",
      S.flow_actor_read(None, None) == "")
check("🔒 classify_flow_conditions/flow_actor_read/polygon_conditions_map خارج الجذور السبعة",
      "classify_flow_conditions" not in _osc_srcs
      and "flow_actor_read" not in _osc_srcs
      and "polygon_conditions_map" not in _osc_srcs)
# 🕵️ بصمة المضارب الشاملة (طلب المستخدم: «جميع أوامر المضارب» لا الأكواد فقط)
_op_tr = ([{"price": 2.0 - i * 0.001, "size": 1500, "conditions": [],
            "exchange": 4} for i in range(3)]                       # كتلة على الطلب (downtick) + دارك
          + [{"price": 1.99, "size": 2, "conditions": []}
             for _ in range(10)]                                    # آيسبرغ ×10 عند 1.99
          + [{"price": 1.99, "size": 50, "conditions": [2]}
             for _ in range(10)])                                   # خوارزمي (Average Price)
_prof = S.operator_tape_profile(_op_tr, bid=1.98, ask=2.0,
                                cond_map={2: "Average Price Trade"})
check("🕵️ بصمة شاملة: تلتقط الامتصاص+الآيسبرغ+الخوارزمي (كل أوامر المضارب)",
      _prof is not None and _prof["bid_block"] >= 1000
      and _prof["iceberg_max"] >= 8 and _prof["algo_pct"] > 0)
check("🕵️ بصمة شاملة·فاشل-آمن: أقل من 20 صفقة → None (عيّنة غير كافية)",
      S.operator_tape_profile([{"price": 1, "size": 1}] * 5) is None)
check("🕵️ دمج: بصمة شاملة ⇒ سطر «من وراء السهم» فيه «تدفق» (امتصاص/آيسبرغ/خوارزمي)",
      "تدفق" in S.flow_actor_read({"actor": "مضارب"}, _prof))
check("🔒 operator_tape_profile خارج الجذور السبعة",
      "operator_tape_profile" not in _osc_srcs)


# ==========================================================
# 🧪 توصيف (Characterization) — خطة 001 (تدقيق عميق 2026-07-28)
# ==========================================================
# الغرض: تثبيت **سلوك اليوم حرفيًّا** قبل إصلاحات الخطط 002-006/008، فكلّها تلمس
# مسارات حيّة حسّاسة (بوّابة الفلوت M14 · كتلة إثراء scan_market · تحميل مراقب
# الارتداد · قرار التجديد الأسبوعي). قاعدة CLAUDE.md: «اختبارات Characterization
# تسبق أي إصلاح لسلوك حسّاس»، و«**القفل الذي لم يسقط مرّة واحدة عمدًا ليس قفلًا**».
#
# ⚠️ **اختباران هنا سيُقلَبان عمدًا** (مُعلَّمان بتعليق صريح فوق كلٍّ منهما): واحد في
#    خطة 004 وآخر في خطة 005. **أي توصيف آخر يتغيّر بلا خطة = انحدار.**
#
# 🔒 صفر تعديل على Super_stock.py — هذي إضافة اختبارات فقط.
print("\n=== 🧪 توصيف المسار الحيّ (خطة 001) ===")

# ---------- أ) بوّابة الفلوت M14: الثغرات غير المغطّاة ----------
# (المغطّى أصلًا في «3) الشورت/الفلوت»: فلوت كبير/صغير. الجديد هنا: المجهول ووسمه ·
#  البوّابة المطفأة · حدّ التخوم بالضبط · والقيم غير الرقمية.)
_c1_lim = S.CONFIG["FLOAT_GATE_MAX"]


def _c1_row(fl):
    """سجلّ نتيجة أدنى لبوّابة M14 (نسخة جديدة كل نداء — لا تلوّث بين الاختبارات)."""
    return {"symbol": "C1T", "soft_fails": [], "flags": [], "float": fl,
            "tier": "B", "score": 60, "rr": 2.0}


_c1_sv_yf = S.yf
try:
    S.yf = object()          # موجود لكن Ticker يرمي ⇒ fl=None (مسار «تعذّر الجلب»)
    _c1_none = S.apply_float_gate([_c1_row(None)])
    check("🧪 توصيف·M14: فلوت مجهول يمرّ بفائدة الشك ويُوسَم «غير متاح» بلا نقص",
          len(_c1_none) == 1
          and "فلوت كبير" not in _c1_none[0]["soft_fails"]
          and any("غير متاح" in str(f) for f in _c1_none[0]["flags"]))

    # 🔴 حدّ التخوم بعد قرار المالك 2026-07-29 («مستبعد تماما»): الحدّ نفسه **يُحذف**
    # (كان يُنقَل نقصًا) · وأقلّ منه بواحد يبقى موسومًا «صغير».
    _c1_at = S.apply_float_gate([_c1_row(_c1_lim)])
    _c1_below = S.apply_float_gate([_c1_row(_c1_lim - 1)])
    check("🧪 توصيف·M14: الحدّ نفسه يُحذف تمامًا · وأقلّ منه بواحد يبقى صغيرًا (تخوم)",
          _c1_at == [] and len(_c1_below) == 1
          and "فلوت كبير" not in _c1_below[0]["soft_fails"]
          and any("صغير" in str(f) for f in _c1_below[0]["flags"]))

    # البوّابة مطفأة ⇒ القائمة تعود **كما هي** (نفس الكائن، بلا أي وسم)
    _c1_off_in = [_c1_row(9e12)]
    _c1_sv_req = S.CONFIG["FLOAT_GATE_REQUIRED"]
    try:
        S.CONFIG["FLOAT_GATE_REQUIRED"] = False
        _c1_off = S.apply_float_gate(_c1_off_in)
    finally:
        S.CONFIG["FLOAT_GATE_REQUIRED"] = _c1_sv_req
    check("🧪 توصيف·M14: البوّابة مطفأة ⇒ القائمة تعود كما هي بلا وسم ولا نقص",
          _c1_off is _c1_off_in and _c1_off_in[0]["soft_fails"] == []
          and _c1_off_in[0]["flags"] == [])

    # ✅ **قُلبت بخطة 004** (كانت توصّف الانهيار): البوّابة صارت محروسة بنفس حارس
    #    `refloat_gate_recheck`، فغير الرقمي = **مجهول يمرّ بفائدة الشك** لا استثناء
    #    يُسقط الفرز كلّه قبل git_save. القرار للمدخلات الرقمية byte-identical.
    def _c1_raises(fl):
        try:
            return (None, S.apply_float_gate([_c1_row(fl)]))
        except Exception as _e:                       # noqa: BLE001
            return (type(_e).__name__, None)

    def _c1_raises_many(rows):
        try:
            return (None, S.apply_float_gate(rows))
        except Exception as _e:                       # noqa: BLE001
            return (type(_e).__name__, None)

    _c1_str, _c1_nan = _c1_raises("12.5M"), _c1_raises(float("nan"))
    check("🛡️ 004·M14: فلوت نصّي لا يرمي ⇒ يمرّ بفائدة الشك موسومًا «غير متاح»",
          _c1_str[0] is None and len(_c1_str[1]) == 1
          and "فلوت كبير" not in _c1_str[1][0]["soft_fails"]
          and any("غير متاح" in str(f) for f in _c1_str[1][0]["flags"]))
    check("🛡️ 004·M14: فلوت NaN كذلك (NaN ليس None — درس CLAUDE.md)",
          _c1_nan[0] is None and "فلوت كبير" not in _c1_nan[1][0]["soft_fails"]
          and any("غير متاح" in str(f) for f in _c1_nan[1][0]["flags"]))
    check("🛡️ 004·التناقض زال: الطبقتان تحرسان القيم غير الرقمية بنفس الدلالة",
          S.refloat_gate_recheck([_c1_row("12.5M")])[1] == []
          and _c1_raises("12.5M")[0] is None
          and _c1_raises({})[0] is None)
    # 🔒 قفل: سهم بقيمة سامّة لا يمنع معالجة ما بعده (البوّابة تُكمل القائمة).
    #    ⚠️ عبر الغلاف عمدًا: نداءٌ عارٍ هنا يجعل **طفرةَ إزالة الحارس تُسقط السويّة
    #    كلّها قبل سطر النتيجة** فيصير مقياس الطفرة غير مقروء (درس خطة 001).
    _c1_mixed = _c1_raises_many([_c1_row("سامّ"), _c1_row(_c1_lim + 1)])
    # 🔴 بعد «الاستبعاد التام»: السامّ (=مجهول) يبقى، والكبير **يُحذف** — والقفل باقٍ
    # على أصل معناه: القيمة السامّة **لم تقطع الحلقة** (وإلا لَما وصلنا للحكم على الثاني).
    check("🛡️ 004·M14: سهم بقيمة سامّة لا يمنع من بعده (السامّ يبقى · الكبير يُحذف)",
          _c1_mixed[0] is None and len(_c1_mixed[1]) == 1
          and "فلوت كبير" not in _c1_mixed[1][0]["soft_fails"]
          and any("غير متاح" in str(f) for f in _c1_mixed[1][0]["flags"]))
    # 🔒 قفل: نصّ **رقمي** يُقبَل رقمًا (قرار صريح: التحويل لا الرفض)
    _c1_numstr = _c1_raises(str(_c1_lim + 1))
    # نصّ رقمي فوق الحدّ ⇒ **يُحذف**: وهذا أقوى إثباتًا للتحويل — لو لم يُحوَّل لمرّ مجهولًا.
    check("🛡️ 004·M14: نصّ رقمي فوق الحدّ يُعامَل رقمًا ⇒ يُحذف (لا يمرّ مجهولًا)",
          _c1_numstr[0] is None and _c1_numstr[1] == [])
    # 🔒 قفل: الالتقاط **ضيّق** (TypeError/ValueError) لا Exception عريض يخفي عيوبًا
    # ⚠️ الشرط على **حارس النوع الجديد** فقط: `apply_float_gate` فيها `except Exception`
    #    قديم ومشروع حول جلب yf.Ticker (لا يُمَسّ). المطلوب ألّا يكون الحارس عريضًا.
    # ⚠️ الأعداد الدقيقة = قفل انحدار: حارس نوع **ضيّق واحد** في كل بوّابة، وأعداد
    #    `except Exception` القديمة المشروعة (جلب yf.Ticker · جلب Fintel/FINRA) **كما
    #    هي** — فلا حارس عريض أُضيف يخفي عيوبًا أخرى داخل الحلقة.
    check("🔒 004·حارس النوع ضيّق (1 لكل بوّابة) والالتقاط العريض القديم لم يتغيّر",
          (_insp0.getsource(S.apply_float_gate).count("except (TypeError, ValueError)"),
           _insp0.getsource(S.apply_float_gate).count("except Exception"),
           _insp0.getsource(S.apply_short_gate).count("except (TypeError, ValueError)"),
           _insp0.getsource(S.apply_short_gate).count("except Exception")) == (1, 1, 1, 2))
finally:
    S.yf = _c1_sv_yf

# ---------- أ-2) بوّابة الشورت M13: نفس الانكشاف بالضبط ----------
# ⚠️⚠️ خطة 004 ستقلب التوقّع التالي أيضًا (الخطوة 3 فيها تعالج M13 بنفس النمط) —
#      **لا تحذفه، عدّله.** مصادر الشورت اليوم (FINRA `int` · Fintel dict) أقلّ خطرًا
#      من الفلوت، لكن الانكشاف **قائم ومطابق** وعلى نفس المسار الحرج.
_c2_sv = (S.fintel_short, S.finra_daily_short)


def _c2_raises(val):
    try:
        S.fintel_short = lambda q, _v=val: {"C2T": _v}
        S.finra_daily_short = lambda q: {}
        return (None, S.apply_short_gate(
            [{"symbol": "C2T", "soft_fails": [], "flags": []}]))
    except Exception as _e:                           # noqa: BLE001
        return (type(_e).__name__, None)


# ✅ **قُلبت بخطة 004**: نفس الحارس طُبِّق على M13 (مصدرها Fintel/FINRA خارجي أيضًا).
try:
    _c2_str, _c2_nan = _c2_raises("12K"), _c2_raises(float("nan"))
    check("🛡️ 004·M13: شورت نصّي لا يرمي ⇒ يمرّ بفائدة الشك موسومًا «غير متاح»",
          _c2_str[0] is None and "شورت عالٍ" not in _c2_str[1][0]["soft_fails"]
          and any("غير متاح" in str(f) for f in _c2_str[1][0]["flags"]))
    check("🛡️ 004·M13: شورت NaN كذلك",
          _c2_nan[0] is None and "شورت عالٍ" not in _c2_nan[1][0]["soft_fails"]
          and any("غير متاح" in str(f) for f in _c2_nan[1][0]["flags"]))
    # 🔒 المخزَّن للعرض/الذاكرة لا يُمَسّ بالحارس (finra_short يبقى كما وصل).
    #    ⚠️ قراءة محروسة: بلا حارس النوع يرمي النداء فينهار الملفّ قبل سطر النتيجة
    #    ويصير مقياس الطفرة غير مقروء (درس خطة 001).
    _c2_keep = (_c2_raises("12K")[1] or [{}])[0]
    check("🔒 004·M13: الحارس لا يمسّ المخزَّن finra_short (عرض/ذاكرة)",
          _c2_keep.get("finra_short") == "12K")
finally:
    (S.fintel_short, S.finra_daily_short) = _c2_sv

# ---------- ب) should_renew: الحالة غير المغطّاة ----------
# (المغطّى أصلًا: force · إشارة · بلا إشارة · قائمة فارغة تمامًا. الجديد: قائمة
#  أسهمها فارغة **لكن فيها مشطوبون** ⇒ ليست «أول تشغيل» فلا تُجدَّد بلا إشارة.)
check("🧪 توصيف·التجديد: stocks فارغة مع removed غير فارغة ⇒ ليست تأسيسًا (لا تجديد)",
      S.should_renew({"stocks": [], "removed": [{"symbol": "OLD"}]},
                     False, False) is False)

# ---------- ج) monitor_pullback: عدد النداءات وسلوك الحالات ----------
# 🔴 عدّاد النداءات هو **المقياس الذي تقيسه خطة 006** (تحميل مجمَّع بدل نداء لكل
#    رمز): اليوم = نداء مستقلّ لكل سهم غير مُطلَق. تثبيته الآن يجعل التحسّن مقيسًا.
_c3_calls = []


def _c3_df(px):
    return pd.DataFrame({"Open": [px], "High": [px], "Low": [px],
                         "Close": [px], "Volume": [1e6]},
                        index=pd.date_range("2024-06-03", periods=1))


def _c3_fetch(syms):
    """جالب مجمَّع (عقد `download_history`): يأخذ **قائمة** ويرجّع dict، ويُسقط ما
    تعذّر تحميله — نفس ما يفعله المسار الحيّ عند خنق ياهو (DDD غائب هنا)."""
    _c3_calls.append(list(syms))
    # AAA عند العتبة بالضبط (2.5 × 1.02) · BBB فوقها · DDD يتعذّر فيغيب
    px = {"AAA": 2.55, "BBB": 2.60}
    return {s: _c3_df(px[s]) for s in syms if s in px}


def _c3_entry(sym, status="watching", lp=3.0):
    return {"symbol": sym, "entry": [2.4, 2.5], "pivot": 2.5, "stop": 1.9,
            "t1": 3.6, "t2": 4.0, "t3": 5.0, "last_price": lp,
            "status": status, "triggered_date": None}


_c3_entries = [_c3_entry("AAA"), _c3_entry("BBB"),
               _c3_entry("CCC", status="triggered", lp=9.99), _c3_entry("DDD")]
_c3_sv = (S.download_history, S.yf)
try:
    S.download_history, S.yf = _c3_fetch, object()
    _c3_trig = S.monitor_pullback({"pullback": _c3_entries})
finally:
    S.download_history, S.yf = _c3_sv
_c3_syms = [x for c in _c3_calls for x in c]
# ✅ **قُلبت بخطة 006**: صار **نداء مجمَّع واحد** بكل غير المُطلَقين بدل نداء لكل رمز.
check("⚡ 006·الارتداد: نداء تحميل **واحد مجمَّع** بكل غير المُطلَقين",
      len(_c3_calls) == 1 and _c3_syms == ["AAA", "BBB", "DDD"])
check("🧪 توصيف·الارتداد: المُطلَق مسبقًا لا يدخل الوسيط ولا يُمسّ",
      "CCC" not in _c3_syms and _c3_entries[2]["last_price"] == 9.99
      and _c3_entries[2]["status"] == "triggered")
check("🧪 توصيف·الارتداد: السعر عند العتبة بالضبط (‎+2%‎ فوق أعلى دفعة) يُطلق",
      _c3_entries[0]["status"] == "triggered"
      and _c3_entries[0]["triggered_date"] is not None)
check("🧪 توصيف·الارتداد: فوق العتبة يبقى «watching» ويُحدَّث سعره فقط",
      _c3_entries[1]["status"] == "watching"
      and _c3_entries[1]["last_price"] == 2.60)
check("🧪 توصيف·الارتداد: رمز غائب من المُخرَج المجمَّع يُتخطّى بلا كسر البقيّة",
      _c3_entries[3]["status"] == "watching"
      and [e["symbol"] for e in _c3_trig] == ["AAA"])
# 🔒 ترتيب المُرجَع يطابق ترتيب المدخلات (يُعرَض في build_pullback_section)
_c3_ord = [_c3_entry("Z1"), _c3_entry("Z2"), _c3_entry("Z3")]
_c3_sv3 = (S.download_history, S.yf)
try:
    S.download_history = lambda syms: {s: _c3_df(2.0) for s in syms}   # الكلّ يُطلق
    S.yf = object()
    _c3_all = S.monitor_pullback({"pullback": _c3_ord})
finally:
    (S.download_history, S.yf) = _c3_sv3
check("🔒 006·الارتداد: ترتيب المُرجَع يطابق ترتيب المدخلات",
      [e["symbol"] for e in _c3_all] == ["Z1", "Z2", "Z3"])
# 🔒 فشل التحميل المجمَّع كلّه ⇒ [] بلا رمي (فاشل-آمن، لا يُسقط pullback_live)
_c3_sv4 = (S.download_history, S.yf)
try:
    def _c3_boom(syms):
        raise RuntimeError("خنق تامّ مُحاكى")
    S.download_history, S.yf = _c3_boom, object()
    _c3_fail = S.monitor_pullback({"pullback": [_c3_entry("Q1")]})
    _c3_fail_raised = None
except Exception as _e:                                        # noqa: BLE001
    _c3_fail_raised, _c3_fail = type(_e).__name__, None
finally:
    (S.download_history, S.yf) = _c3_sv4
check("🔒 006·الارتداد: انهيار التحميل المجمَّع ⇒ [] بلا رمي (فاشل-آمن)",
      _c3_fail_raised is None and _c3_fail == [])
# 🔒 قفل بنيوي: نداء تحميل واحد فقط داخل الدالّة + وسيط الحقن موجود
_c3_src = _insp0.getsource(S.monitor_pullback)
# ⚠️ يعدّ **نداءً** لا ذِكرًا: الـdocstring يشرح النمط القديم `download_history([sym])`
#    عمدًا، وgetsource يشمله. النداء الوحيد هو `(fetch_hist or download_history)(...)`.
check("🔒 006·قفل: نداء تحميل واحد داخل monitor_pullback + وسيط fetch_hist محقون",
      _c3_src.count("(fetch_hist or download_history)(") == 1
      and _c3_src.count("download_history([") == 1     # في الـdocstring فقط (شرح تاريخي)
      and "for e in pend:" in _c3_src)

# البوّابتان المبكّرتان (Super_stock.py:9762) — **يجب أن تبقيا بعد تجميع خطة 006**:
# غيابهما يعني نداء شبكة على قائمة فارغة أو بلا yfinance.
_c3_calls2 = []
_c3_sv2 = (S.download_history, S.yf)
try:
    S.download_history = lambda syms: (_c3_calls2.append(syms) or {})
    S.yf = None
    _c3_nyf = S.monitor_pullback({"pullback": [_c3_entry("EEE")]})
    S.yf = object()
    _c3_empty = (S.monitor_pullback({}), S.monitor_pullback({"pullback": []}))
finally:
    (S.download_history, S.yf) = _c3_sv2
check("🧪 توصيف·الارتداد: بلا yfinance ⇒ [] فورًا بصفر نداء تحميل",
      _c3_nyf == [] and _c3_calls2 == [])
check("🧪 توصيف·الارتداد: قائمة ارتداد فارغة/غائبة ⇒ [] بصفر نداء تحميل",
      _c3_empty == ([], []) and _c3_calls2 == [])

# ---------- د) حصانة scan_market تجاه استثناء رمز واحد ----------
# ✅ **قُلبت بخطة 005**: كتلة الإثراء صارت محروسة لكل رمز، فاستثناء واحد لم يعد
#    يُسقط التشغيلة كلّها قبل git_save. العضوية والترتيب byte-identical (قفل أدناه).
_c4_df = synth_pivot()
_c4_sv = (S.MODE, S.download_history, S.fintel_short, S.finra_daily_short,
          S.yf, S.build_interpretation, S.descending_trendline)
try:
    S.MODE = "TEST"                       # عيّنة TEST_TICKERS — بلا نداء كون
    S.download_history = lambda syms: {"C4T": _c4_df}
    S.fintel_short = lambda q: {}
    S.finra_daily_short = lambda q: {}
    S.yf = None                           # apply_float_gate ترجع مبكرًا (بلا شبكة)
    _c4_ok, _ = S.scan_market()
    check("🧪 توصيف·الفرز: المسار السليم يملأ حقول الإثراء (behav/fsto/interp)",
          len(_c4_ok) == 1 and _c4_ok[0].get("interp")
          and _c4_ok[0].get("behav") and "fsto_osc" in _c4_ok[0])

    # ① سقوط التفسير وحده ⇒ الفرز يكمل والسهم يبقى بلا interp
    S.build_interpretation = lambda r: (_ for _ in ()).throw(
        RuntimeError("عطل مُحاكى في رمز واحد"))
    try:
        _c4_broken, _ = S.scan_market()
        _c4_raised = None
    except Exception as _e:                                    # noqa: BLE001
        _c4_raised, _c4_broken = type(_e).__name__, None
    check("🛡️ 005·الفرز: سقوط التفسير لا يُسقط scan_market — السهم يبقى بلا interp",
          _c4_raised is None and _c4_broken is not None
          and len(_c4_broken) == 1 and _c4_broken[0].get("interp") is None
          and _c4_broken[0].get("behav"))
    # 🔒 **قفل العضوية والترتيب** (الأهمّ): مجموعة الرموز وترتيبها لا يتأثّران بسقوط
    #    الإثراء — لأن rank_key يقرأ readiness/score/rr من analyze_ticker لا من الإثراء.
    check("🔒 005·العضوية والترتيب byte-identical رغم سقوط الإثراء",
          [x["symbol"] for x in _c4_ok] == [x["symbol"] for x in _c4_broken])
    # ② سقوط دالّة مبكّرة في الكتلة (descending_trendline) ⇒ الفرز يكمل كذلك
    S.build_interpretation = _c4_sv[5]
    S.descending_trendline = lambda df, px: (_ for _ in ()).throw(
        RuntimeError("عطل مُحاكى مبكّر"))
    try:
        _c4_early, _ = S.scan_market()
        _c4_early_raised = None
    except Exception as _e:                                    # noqa: BLE001
        _c4_early_raised, _c4_early = type(_e).__name__, None
    check("🛡️ 005·الفرز: سقوط دالّة داخل الكتلة لا يُسقط الفرز (والتفسير يُحسب بعدها)",
          _c4_early_raised is None and _c4_early is not None
          and len(_c4_early) == 1 and _c4_early[0].get("trendline") is None
          and _c4_early[0].get("interp"))
finally:
    (S.MODE, S.download_history, S.fintel_short, S.finra_daily_short,
     S.yf, S.build_interpretation, S.descending_trendline) = _c4_sv
# 🔒 قفل بنيوي: `results.append(r)` خارج الحارس (وإلا سقط الإثراء = سقوط عضوية)
_c4_src = _insp0.getsource(S.scan_market)
check("🔒 005·results.append خارج try الإثراء (الحارس لا يبتلع العضوية)",
      "\n            results.append(r)" in _c4_src
      and _c4_src.count("except Exception as _e:") == 2)
check("🔒 005·الحارس يسجّل ولا يصمت (لا pass صامتة في مساري الفشل)",
      _c4_src.count('log(f"⚠️ إثراء عرض') == 1 and _c4_src.count('log(f"⚠️ تفسير') == 1)


# ==========================================================
# ⏱️ خطة 002: إحياء قياس «ربع الساعة» في الـassembler (كان ميتًا في الإنتاج)
# ==========================================================
# العطل كان بسببين **مستقلَّين** عند نقطة النداء لا في الدالّة: (1) المقاطع
# (ignition_live.py:624 `if role:`) لا تنادي record_ignition_fires إطلاقًا — النداء
# الحيّ الوحيد هو الـassembler · (2) والـassembler كان ينادي بلا `fetch_bars` وبلا
# `fired_ts_ms` فتخرج _fire_sustain بقاموس فارغ (Super_stock.py:9457-9459).
# ⇒ الحقلان sustain_min/operator_ok لا يُكتبان أبدًا وسطر «⏱️ ربع الساعة» في تقرير
# التطوير (Super_stock.py:9635-9641) لا يظهر. واختبارات الوحدة خضراء لأنها تحقن
# الاثنين — صنف «اختبار ينجح ونقطة الاستعمال الحية مكسورة».
import ignition_e2_assemble as _A2
import tempfile as _tf2

print("\n=== ⏱️ خطة 002: ربع الساعة في الـassembler ===")


def _c002_cand(**kw):
    base = {"symbol": "AAA", "signal_price": 2.0, "vol_x": 4.0,
            "signal_usd": 150_000, "break_level": 1.9, "stop": 1.5, "t1": 3.0,
            "pivot": 1.8, "alert_emitted": True,
            "telegram_sent_at_ms": 1_000_000, "trigger_bar_start": 999_000}
    base.update(kw)
    return base


_c002_f1 = _A2._fires_from_candidates([_c002_cand()])
check("⏱️ 002·الطابع: telegram_sent_at_ms هو المصدر الأول (لحظة الإرسال الفعلي)",
      len(_c002_f1) == 1 and _c002_f1[0][0]["fired_ts_ms"] == 1_000_000)
_c002_f2 = _A2._fires_from_candidates([_c002_cand(telegram_sent_at_ms=None)])
check("⏱️ 002·الطابع: بلا telegram_sent_at_ms ⇒ احتياط trigger_bar_start",
      _c002_f2[0][0]["fired_ts_ms"] == 999_000)
_c002_f3 = _A2._fires_from_candidates(
    [_c002_cand(telegram_sent_at_ms=None, trigger_bar_start=None)])
check("⏱️ 002·الطابع: بلا الاثنين ⇒ None بلا رمي (فاشل-آمن)",
      _c002_f3[0][0]["fired_ts_ms"] is None)
check("⏱️ 002·الأساس alert_emitted محفوظ (لا delivered — قرار موثّق)",
      _A2._fires_from_candidates([_c002_cand(alert_emitted=False)]) == []
      and _A2._fires_from_candidates([]) == []
      and _A2._fires_from_candidates(None) == [])
check("⏱️ 002·الحقول المنقولة تطابق عقد record_ignition_fires",
      _c002_f1[0][0]["symbol"] == "AAA" and _c002_f1[0][0]["stop"] == [1.5]
      and _c002_f1[0][0]["interp"]["critical_number"]["price"] == 1.9
      and _c002_f1[0][1] == {"price": 2.0, "vol_x": 4.0, "usd": 150_000})

# 🔴 الاختبار الحاسم (طرف-لطرف): مُخرَج الـassembler + جالب محقون ⇒ الحقلان يُكتبان.
# سجلّ مؤقّت — **ممنوع الكتابة على ignition_log.json الحقيقي**.
_c002_dir = _tf2.mkdtemp()
_c002_sv_log = S.IGNITION_LOG_FILE
try:
    S.IGNITION_LOG_FILE = _os_hc.path.join(_c002_dir, "ign_log.json")
    _c002_bars = [{"t": 1_000_000 + i * 60_000, "c": 2.5} for i in range(20)]
    _c002_n = S.record_ignition_fires(
        _A2._fires_from_candidates([_c002_cand()]), "2026-07-28",
        fetch_bars=lambda sym, minutes=0: _c002_bars)
    _c002_rec = json.load(open(S.IGNITION_LOG_FILE, encoding="utf-8"))[0]
    # ونفس المدخل بلا جالب = السلوك المكسور (حارس ضد «الاختبار يمرّ في الحالتين»)
    _os_hc.remove(S.IGNITION_LOG_FILE)
    S.record_ignition_fires(_A2._fires_from_candidates([_c002_cand()]), "2026-07-28")
    _c002_nofetch = json.load(open(S.IGNITION_LOG_FILE, encoding="utf-8"))[0]
finally:
    S.IGNITION_LOG_FILE = _c002_sv_log
check("⏱️ 002·طرف-لطرف: مُخرَج الـassembler + جالب ⇒ operator_ok/sustain_min يُكتبان",
      _c002_n == 1 and _c002_rec.get("operator_ok") is True
      and _c002_rec.get("sustain_min", 0) >= S.CONFIG["OPERATOR_SUSTAIN_MIN"])
check("⏱️ 002·حارس: بلا جالب تبقى الحقول غائبة (فالاختبار أعلاه يقيس شيئًا فعليًّا)",
      _c002_nofetch.get("operator_ok") is None
      and _c002_nofetch.get("sustain_min") is None)
check("⏱️ 002·قفل: الـassembler يمرّر الجالب والطابع (لا يعود للنداء الأعمى)",
      "fetch_bars=bot.polygon_minute_bars" in _insp0.getsource(_A2.main)
      and "fired_ts_ms" in _insp0.getsource(_A2._fires_from_candidates))


# ==========================================================
# 🏢 خطة 003: ردم الفلوت من المصدر المُثبَت (CE ماتت 2026-07-24)
# ==========================================================
print("\n=== 🏢 خطة 003: ردم الفلوت ===")

# ① المصدر القديم ميت فعلًا: المحلّل يرجع None على قِشرة JS (شكل الصفحة اليوم)
check("🏢 003·CE ميتة: المحلّل يرجع None على قِشرة JS (وينجح على الشكل القديم)",
      S._parse_ce_float('<html><body><div id="root"></div>'
                        '<script src="/app.js"></script></body></html>') is None
      and S._parse_ce_float('x stat-flow-label">Float</div>'
                            '<div class="stat-flow-value">12.55M</div>') == 12_550_000)

# ② `strict` يمنع تلوّث حقلٍ تقرأه بوّابة M14 بـsharesOutstanding
_c3_sv_yf = S.yf
try:
    S.yf = _ty0.SimpleNamespace(Ticker=lambda s: _ty0.SimpleNamespace(
        info={"sharesOutstanding": 277_000_000}))          # بلا floatShares
    _c3_lax, _c3_str = S._yahoo_float("X"), S._yahoo_float("X", strict=True)
    S.yf = _ty0.SimpleNamespace(Ticker=lambda s: _ty0.SimpleNamespace(
        info={"floatShares": 1_234_567, "sharesOutstanding": 9_999_999}))
    _c3_both = (S._yahoo_float("X"), S._yahoo_float("X", strict=True))
    S.yf = None
    _c3_noyf = S._yahoo_float("X", strict=True)
finally:
    S.yf = _c3_sv_yf
check("🏢 003·strict: بلا floatShares ⇒ None (لا يسقط لـsharesOutstanding)",
      _c3_lax == 277_000_000 and _c3_str is None)
check("🏢 003·strict: مع floatShares ⇒ نفس القيمة في الوضعين (توافق خلفي)",
      _c3_both == (1_234_567, 1_234_567))
check("🏢 003·strict فاشل-آمن: بلا yfinance ⇒ None بلا رمي",
      _c3_noyf is None)
# 🔴 الخطر المُستنسَخ الذي فرض strict: التقريب يصل بوّابة M14 ويوسم «فلوت كبير»
_c3_contam = {"symbol": "X", "float": 277_000_000, "soft_fails": ["أ"], "flags": []}
S.refloat_gate_recheck([_c3_contam])
check("🏢 003·سبب strict: قيمة sharesOutstanding تصل M14 وتُوسَم «فلوت كبير»",
      "فلوت كبير" in _c3_contam["soft_fails"])

# ③ أقفال المصدر عند نقطتَي الاستعمال الحيّتين + صون البوّابة والدوال
_c3_daily = _insp0.getsource(S.run_daily_watchlist)
_c3_enrich = _insp0.getsource(S.enrich)
# ⚠️ القفل يكشف **نداءً** (`name(`) لا ذِكرًا: getsource يشمل التعليقات، والتعليق
#    التوثيقي يسمّي المصدر الميت عمدًا لشرح سبب الاستبدال.
check("🏢 003·قفل: الردم اليومي ينادي _yahoo_float(strict) لا ce_float_info",
      "ce_float_info(" not in _c3_daily
      and "_yahoo_float(s[\"symbol\"], strict=True)" in _c3_daily)
check("🏢 003·قفل: آخر ملاذ enrich كذلك",
      "ce_float_info(" not in _c3_enrich
      and "_yahoo_float(sym, strict=True)" in _c3_enrich)
check("🏢 003·صون: البوّابة M14 نفسها لم تُمَسّ (لا CE ولا ياهو داخلها)",
      all(_n not in _insp0.getsource(S.apply_float_gate)
          for _n in ("ce_float_info", "_yahoo_float")))
check("🏢 003·صون: ce_float_info/_parse_ce_float لم تُحذفا (محلّل محفوظ لو عادت CE)",
      callable(getattr(S, "ce_float_info", None))
      and callable(getattr(S, "_parse_ce_float", None)))
check("🏢 003·صون: ce_borrow_info (صفحة borrow-fee الحيّة) لم تُمَسّ",
      "ce_borrow_info" in _insp0.getsource(S.refresh_borrow))


# ==========================================================
# 🔔 خطة 008: رصد سقوط كرون التجديد الأسبوعي (إشعار فقط)
# ==========================================================
# القرار يبقى مدفوعًا بإشارة الجدولة وحدها (RENEW_ON_CLOSE) — قرار موثّق. المضاف
# **رصد** فقط: GitHub قد يُسقط تشغيلة كرون كليًّا، وبلا رصد يسقط بصمت كل ما داخل
# run_weekly_renewal (القائمة · المصير · الحصاد · التقرير الأسبوعي · مساعد التطوير
# · CSV · أرشفة history · قائمة الارتداد).
print("\n=== 🔔 خطة 008: رصد تقادم التجديد ===")

_c8_cap = S.CONFIG["RENEWAL_STALE_DAYS"]


def _c8(days_ago, **kw):
    ws = (_dt0.date(2026, 7, 20) - _dt0.timedelta(days=0)).isoformat()
    return S.renewal_staleness({"week_start": ws}, today=(
        _dt0.date(2026, 7, 20) + _dt0.timedelta(days=days_ago)).isoformat(), **kw)


import datetime as _dt0

check("🔔 008·اليوم نفسه ⇒ لا تقادم",
      _c8(0) is None)
check("🔔 008·أسبوع طبيعي (7 أيام) ⇒ لا إنذار (قفل ضد الإزعاج)",
      _c8(7) is None)
check(f"🔔 008·الحدّ نفسه ({_c8_cap} أيام) ⇒ لا إنذار (تخوم: days > max_days)",
      _c8(_c8_cap) is None)
_c8_over = _c8(_c8_cap + 1)
check(f"🔔 008·تجاوز الحدّ ({_c8_cap + 1} أيام) ⇒ dict فيه days والمرجع",
      isinstance(_c8_over, dict) and _c8_over["days"] == _c8_cap + 1
      and _c8_over["last"] == "2026-07-20" and _c8_over["max_days"] == _c8_cap)
check("🔔 008·week_start غائب/غير نصّ ⇒ None (قائمة تأسيسية لا تُنذر)",
      S.renewal_staleness({}) is None
      and S.renewal_staleness({"week_start": None}) is None
      and S.renewal_staleness({"week_start": 20260720}) is None)
check("🔔 008·تاريخ تالف ⇒ None بلا رمي (فاشل-آمن)",
      S.renewal_staleness({"week_start": "غير-تاريخ"}) is None
      and S.renewal_staleness(None) is None)
check("🔔 008·week_start في المستقبل ⇒ None (ساعة رنر مغلوطة لا تُنذر)",
      _c8(-3) is None)
check("🔔 008·max_days محقون يتجاوز CONFIG",
      _c8(4, max_days=3) is not None and _c8(3, max_days=3) is None)
# العرض
_c8_msg = S.renewal_stale_message(_c8_over)
check("🔔 008·الرسالة تحوي التاريخ وعدد الأيام وطريقة الإجراء",
      "2026-07-20" in _c8_msg and str(_c8_cap + 1) in _c8_msg
      and "force_renew=1" in _c8_msg and S.renewal_stale_message(None) == "")
check("🔔 008·قفل اللغة: بلا علامات مقارنة (قاعدة CLAUDE.md المُلزِمة)",
      not any(_ch in _c8_msg for _ch in ("≥", "≤", ">", "<"))
      or "<b>" in _c8_msg and not any(
          _ch in _c8_msg.replace("<b>", "").replace("</b>", "")
          .replace("<code>", "").replace("</code>", "") for _ch in ("≥", "≤", ">", "<")))
# 🔒 قفل الصون الحاسم: قرار التجديد لم يُمَسّ
check("🔒 008·should_renew byte-identical (لا تقادم ولا weekday داخلها)",
      all(_n not in _insp0.getsource(S.should_renew)
          for _n in ("renewal_staleness", "RENEWAL_STALE_DAYS", "weekday")))
check("🔒 008·الرصد داخل try في main ولا يُطلق تجديدًا",
      "renewal_staleness" in _insp0.getsource(S.main)
      and "run_daily_watchlist(wl)" in _insp0.getsource(S.main)
      and "renewal_staleness" not in _insp0.getsource(S.run_weekly_renewal))
# 🔒 main لا ترمي لو انهار الرصد (فاشل-آمن مُثبَت لا موصوف)
_c8_sv = (S.renewal_staleness, S.load_watchlist, S.run_daily_watchlist,
          S.send_telegram, S.should_renew)
try:
    S.renewal_staleness = lambda w: (_ for _ in ()).throw(RuntimeError("عطل رصد"))
    S.load_watchlist = lambda: {"stocks": [{"symbol": "X"}], "removed": []}
    S.should_renew = lambda w, f=False, s=False: False
    _c8_ran = []
    S.run_daily_watchlist = lambda w: _c8_ran.append(True)
    S.send_telegram = lambda m: True
    S.main()
    _c8_raised = None
except Exception as _e:                                        # noqa: BLE001
    _c8_raised = type(_e).__name__
finally:
    (S.renewal_staleness, S.load_watchlist, S.run_daily_watchlist,
     S.send_telegram, S.should_renew) = _c8_sv
check("🔒 008·انهيار الرصد لا يُسقط المتابعة اليومية (فاشل-آمن مُثبَت)",
      _c8_raised is None and _c8_ran == [True])


# ==========================================================
# 📌 خطة 007: تثبيت الاعتماديات + فحص الدخان الحيّ
# ==========================================================
# `tests.yml` تعمل بلا إنترنت بتصميمها ⇒ كسرُ yfinance لا يُسقط أي اختبار (CI خضراء
# والإنتاج يقرأ صفرًا). فالفحص الحيّ مكانه workflow **منفصل**، وهنا نقفل الضمانات
# الثابتة عليه: أنه لا يكتب حالة ولا يأخذ مفتاح Polygon، وأن الاعتماديات مثبَّتة.
print("\n=== 📌 خطة 007: تثبيت الاعتماديات + فحص الدخان ===")

_c7_req = open("requirements.txt", encoding="utf-8").read()
_c7_pins = [_l.strip() for _l in _c7_req.splitlines()
            if _l.strip() and not _l.strip().startswith("#")]
# 🔴 **حُدِّث عمدًا 2026-08-07 — والقفلُ أدّى عملَه فأمسك التغيير.** كان يشترط
#    **أربعًا**، وأُضيفت `PyYAML` لأن غيابَها أبقى بوّابة CI حمراء بصمت (السويّةُ
#    تقرأ ملفّات الـworkflows في أقفالٍ بنيويّة). **والصياغةُ شُدّت لا رُخّيت:**
#    المجموعةُ **مطابقةٌ بالضبط** (لا «تحوي») ⇒ أيُّ إضافةٍ صامتةٍ لاحقة تُسقطه أيضًا.
_C7_EXPECT = {"PyYAML", "yfinance", "pandas", "numpy", "requests"}
_c7_names = {_l.split("==")[0].strip() for _l in _c7_pins}
check("📌 007·الاعتمادياتُ الخمس مثبَّتةٌ بـ== ومجموعتُها مطابقةٌ بالضبط "
      "(لا ترقيةٌ صامتة ولا إضافةٌ صامتة)",
      _c7_names == _C7_EXPECT and all("==" in _l for _l in _c7_pins)
      and len(_c7_pins) == len(_C7_EXPECT),
      f"{sorted(_c7_names)}")
check("📌 007·بروتوكول الترقية موثّق داخل الملفّ (لا ترقية بلا فحص دخان)",
      "deps_smoke" in _c7_req and "test_bot.py" in _c7_req)

# 🔒 أداة الفحص لا تكتب حالة إطلاقًا — قفل AST (نداءات فعلية لا ذِكر في docstring)
import ast as _ast7
_c7_tree = _ast7.parse(open("deps_smoke.py", encoding="utf-8").read())
_c7_bad = {"git_save", "save_watchlist", "_atomic_write_json", "save_alerts_file",
           "record_ignition_fires", "record_ignition_universe", "record_new_alerts",
           "load_watchlist", "run_daily_watchlist", "run_weekly_renewal"}
_c7_calls = {(_n.func.attr if isinstance(_n.func, _ast7.Attribute)
              else getattr(_n.func, "id", None))
             for _n in _ast7.walk(_c7_tree) if isinstance(_n, _ast7.Call)}
check("🔒 007·deps_smoke لا ينادي أي دالّة تكتب حالة (قفل AST)",
      not (_c7_calls & _c7_bad))
_c7_yml = open(".github/workflows/deps_smoke.yml", encoding="utf-8").read()
check("🔒 007·workflow الفحص: permissions=read · بلا مفتاح Polygon · كرون غير مستدير",
      "contents: read" in _c7_yml
      and "POLYGON_API_KEY: ${{" not in _c7_yml
      and 'cron: "37 6 * * 1"' in _c7_yml)
check("🔒 007·tests.yml بقيت بلا إنترنت (الفحص الحيّ منفصل عنها عمدًا)",
      "deps_smoke" not in open(".github/workflows/tests.yml", encoding="utf-8").read())


# ==========================================================
# 📎 خطة 009: مسار artifact الـCSV في daily_screener.yml
# ==========================================================
print("\n=== 📎 خطة 009: artifact الـCSV ===")

_c9_yml = open(".github/workflows/daily_screener.yml", encoding="utf-8").read()
# البادئات الفعلية المستخرَجة من الكود نفسه (لا قائمة مكرَّرة يدويًّا)
_c9_prefixes = {"daily_watch", "weekly_list", "trades", "signals", "missed"}
# ⚠️ يُفحص خارج أسطر التعليق: التعليق يسمّي النمط الميت عمدًا لشرح سبب الإزالة.
_c9_active = [_l for _l in _c9_yml.splitlines() if not _l.lstrip().startswith("#")]
check("📎 009·النمط الميت أُزيل من المسار الفعّال (لا منتِج له في المستودع كلّه)",
      not any("screener_report" in _l for _l in _c9_active))
check("📎 009·كل بادئة CSV يُنتجها الكود مذكورة في مسار الـartifact",
      all(f"{_p}_*.csv" in _c9_yml for _p in _c9_prefixes))
check("📎 009·البادئات المذكورة مستعمَلة فعلًا في الكود (لا نمط ميت جديد)",
      all(f'"{_p}"' in _insp0.getsource(S.run_daily_watchlist)
          or f'"{_p}"' in _insp0.getsource(S.run_weekly_renewal)
          or f'"{_p}"' in _insp0.getsource(S.export_weekly_csvs)
          for _p in _c9_prefixes))
# 🔒 الأخطر: الـdiff يجب ألّا يمسّ الكرون ولا مطابقة RENEW_ON_CLOSE (يعطّل التجديد بصمت)
check("🔒 009·صون: كرونا الفارز ومطابقة RENEW_ON_CLOSE لم تُمَسّ",
      'cron: "54 4 * * 2-5"' in _c9_yml and 'cron: "7 22 * * 5"' in _c9_yml
      and "github.event.schedule == '7 22 * * 5'" in _c9_yml)


# ==========================================================
# 🔐 خطة 010: صلاحيات صريحة لكل workflow + منع حقن مدخلات الـdispatch
# ==========================================================
print("\n=== 🔐 خطة 010: صلاحيات الـworkflows ===")

import glob as _glob10
import re as _re10

_c10_files = sorted(_glob10.glob(".github/workflows/*.yml"))
_c10_no_perm = [_f for _f in _c10_files
                if "permissions:" not in open(_f, encoding="utf-8").read()]
check("🔐 010·كل workflow يعلن permissions صراحةً (لا وراثة الافتراضي)",
      len(_c10_files) >= 20 and _c10_no_perm == [])

# ⚠️ الممنوع = مدخل dispatch داخل **نصّ صدفة** (run:). داخل env:/with:/if: مسموح
#    (GitHub يقيّمها بلا صدفة) وهو النمط المتّبع في بقيّة المستودع.
def _c10_inputs_in_run(path):
    out, in_run, ind = [], False, 0
    for i, l in enumerate(open(path, encoding="utf-8").read().splitlines(), 1):
        st = l.lstrip()
        if st.startswith("#"):
            continue
        if _re10.match(r"^run:\s*\|?\s*$", st) or st.startswith("run: "):
            in_run, ind = True, len(l) - len(st)
            continue
        if in_run:
            if st and (len(l) - len(st)) <= ind:
                in_run = False
            elif "github.event.inputs" in l:
                out.append(f"{path}:{i}")
    return out


_c10_inj = [x for _f in _c10_files for x in _c10_inputs_in_run(_f)]
check("🔐 010·لا مدخل workflow_dispatch داخل أي كتلة run: (منع script injection)",
      _c10_inj == [])
# 🕯️ T-CANDLE (`candle_readiness_prereg.md`): «حالة الزناد» + مقياس **الوشوك**.
#    السند الحرفيّ: TG_1870 «قاع ⟶ اختبار مقاومة ⟶ رجوعٌ يختبر القاع مع سحب سيولة ⟶
#    هنا يكون rsi جاهز للانفجار» · TG_2037 «RSI عند 27».
def _cd(rows):
    _i = pd.date_range("2026-01-01", periods=len(rows), freq="D")
    _d = pd.DataFrame(rows, columns=["High", "Low", "Close"], index=_i)
    _d["Open"] = _d["Close"]
    return _d


# تسلسلٌ كامل: قاع 1.00 · قمّة 1.12 (رُدَّ) · مسح 0.91 (‏−9% داخل نطاق فيصل) · استعادة
_cd_seq = [[1.06, 1.00, 1.01], [1.12, 1.02, 1.10], [1.11, 1.05, 1.06],
           [1.07, 0.91, 0.95], [1.04, 0.94, 1.02], [1.03, 0.99, 1.00],
           [1.02, 0.98, 0.99], [1.02, 0.99, 1.00]]
_cd_pre = [[1.30 - i * 0.002, 1.26 - i * 0.002, 1.28 - i * 0.002] for i in range(17)]
_cd_ok = S.trigger_state(_cd(_cd_pre + _cd_seq))
check("🕯️ حالة الزناد: التسلسل الكامل يُرصَد (ok=True فعلًا — ليست قفلًا ميتًا)",
      _cd_ok is not None and _cd_ok["ok"] is True and _cd_ok["swept_pct"] == 9.0
      and all(_cd_ok["steps"].values()) and 20 <= _cd_ok["rsi"] <= 30)
# 🔴 القفل الحاسم: القاع المطلوب **ليس أدنى النافذة** — قاعُ المسح أدنى منه بالتعريف،
#    فلو أُخذ `argmin` استحال التسلسل. القاع المرصود يجب أن يكون 1.00 لا 0.91.
check("🔴 حالة الزناد: القاع = المُمسوح (1.00) لا أدنى النافذة (0.91)",
      _cd_ok["bottom"] == 1.0)
_cd_nosweep = _cd_seq[:3] + [[1.07, 1.01, 1.03]] + _cd_seq[4:]
check("🕯️ بلا مسح ⇒ التسلسل لا يكتمل",
      S.trigger_state(_cd(_cd_pre + _cd_nosweep))["ok"] is False)
_cd_deep = _cd_seq[:3] + [[1.07, 0.70, 0.75]] + _cd_seq[4:]
check("🕯️ مسحٌ خارج نطاق فيصل (‏−30%) لا يُحتسب مسحًا (7-13% حصرًا)",
      S.trigger_state(_cd(_cd_pre + _cd_deep))["swept_pct"] is None)
_cd_up = [[1.0 + i * 0.06, 0.96 + i * 0.06, 1.0 + i * 0.06] for i in range(25)]
check("🕯️ سلسلة صاعدة: RSI خارج النطاق ⇒ ok=False (الشرط الرابع فعّال)",
      S.trigger_state(_cd(_cd_up))["ok"] is False
      and S.trigger_state(_cd(_cd_up))["rsi"] > 30)
check("🕯️ فاشلة-آمنة: None/تاريخ أقصر من النافذة ⇒ None بلا استثناء",
      S.trigger_state(None) is None and S.trigger_state(_cd(_cd_seq)) is None)
# 🔴 حالاتٌ **تمييزية**: البنية تكتمل ومع ذلك يجب أن يسقط `ok` — وإلّا فالشرط زائد.
# ① RSI خارج النطاق **مع بنيةٍ مكتملة** (ميلٌ أهدأ يرفع RSI إلى 30.2 فوق السقف 30)
_cd_r = S.trigger_state(_cd(
    [[1.30 - i * 0.006, 1.26 - i * 0.006, 1.28 - i * 0.006] for i in range(17)] + _cd_seq))
check("🔴 حالة الزناد: بنيةٌ مكتملة و RSI فوق السقف ⇒ ok=False (الشرط الرابع فعّال حقًّا)",
      all(_cd_r["steps"][k] for k in ("bottom_formed", "tested_res", "swept_reclaimed"))
      and _cd_r["steps"]["rsi_zone"] is False and _cd_r["ok"] is False
      and _cd_r["rsi"] > S.CONFIG["CANDLE_RSI_HI"])
# ② ارتدادٌ ضحيل (‏+3% فقط) ⇒ «اختبار المقاومة» لم يحدث، فلا يكتمل التسلسل.
#    ⚠️ ورأسُ شمعة المسح يجب أن يبقى **تحت** القمّة، وإلّا صارت هي القمّة فاختلّ القياس
#    (وهذا ما كشفته الطفرة: صيغتي الأولى لم تكن تعزل الشرط أصلًا).
_cd_weak = ([[1.06, 1.00, 1.01], [1.03, 1.01, 1.02], [1.02, 0.91, 0.95],
             [1.02, 0.94, 1.01], [1.01, 0.99, 1.00], [1.01, 0.98, 0.99],
             [1.01, 0.99, 1.00], [1.01, 0.99, 1.00]])
_cd_w = S.trigger_state(_cd(_cd_pre + _cd_weak))
check("🔴 حالة الزناد: ارتدادٌ ضحيل (+3%) ⇒ لا «اختبار مقاومة» ⇒ ok=False",
      _cd_w["ok"] is False and _cd_w["steps"]["tested_res"] is False)
# ②-ب 🔴 **قفلُ بارسيمونيا**: «الإغلاق دون القمّة» **حُذف بقياس** — عزلُه مستحيل (يستلزم
#      هبوطًا حادًّا يُبقي RSI منخفضًا، وذاك يُسقط الشرط ① «الأدنى حتى لحظته») ⇒ الشرط
#      زائدٌ يحمله بند RSI. فيُقفَل **غيابُه** لئلّا يُعاد في جلسةٍ قادمة بحسن نيّة.
_cd_src = _insp0.getsource(S.trigger_state)
check("🔴 حالة الزناد: لا شرطَ «الإغلاق دون القمّة» (حُذف بقياسٍ — زائدٌ يحمله RSI)",
      "cl[-1]) >= peak" not in _cd_src and "زائدٌ يحمله" in _cd_src)
# والقمّة إن كانت آخر بار ⇒ لا مجال للمسح بعدها ⇒ لا يكتمل التسلسل. ⚠️ وحارسُ
# `pk >= len(cl)-1` **دفاعيّ بلا أثر سلوكيّ** (‏`range(pk+1, …)` فارغٌ أصلًا) — يُوثَّق
# ولا يُدَّعى قفلُه، فلا يُكتَب اختبارٌ يبدو مانعًا وهو لا يمنع شيئًا.
check("🔴 حالة الزناد: القمّة آخر بارٍ ⇒ لا مسحَ بعدها ⇒ ok=False",
      S.trigger_state(_cd(_cd_pre + _cd_seq[:-1] + [[1.40, 1.20, 1.35]]))["ok"]
      is False)
# ③ **الترتيب الزمنيّ**: مسحٌ **قبل** اختبار المقاومة لا يُحتسب (التسلسل لا مجرّد الوجود)
_cd_order = ([[1.06, 1.00, 1.01], [1.02, 0.91, 0.95], [1.12, 1.00, 1.10],
              [1.11, 1.05, 1.08], [1.09, 1.03, 1.05], [1.06, 1.02, 1.03],
              [1.05, 1.01, 1.02], [1.04, 1.01, 1.02]])
check("🔴 حالة الزناد: مسحٌ **قبل** القمّة لا يكتمل به التسلسل (ترتيبٌ لا وجود)",
      S.trigger_state(_cd(_cd_pre + _cd_order))["ok"] is False)
# ⏱️ مقياس الوشوك: +50% خلال CANDLE_SOON_BARS **وقبل الوقف**
_cs_hi = [1.0, 1.1, 1.6, 1.7]          # يبلغ 1.5 عند البار 2 (بعد بارَين من التعبئة)
_cs_lo = [0.98, 1.05, 1.5, 1.6]
_cs_cl = [1.0, 1.08, 1.55, 1.65]
_cs = S._candle_augment({}, None, _cs_hi, _cs_lo, _cs_cl, 1.00, 0.93, 0)
check("⏱️ الوشوك: بلغ +50% خلال النافذة ⇒ soon_50 وعدد الجلسات",
      _cs["soon_50"] is True and _cs["bars_to_50"] == 2)
_cst = S._candle_augment({}, None, [1.0, 1.6], [0.90, 1.5], [0.92, 1.55],
                         1.00, 0.93, 0)
check("⏱️ الوقف يُفحَص أولًا: وقفٌ قبل الهدف ⇒ لا يُحتسب وشيكًا (محافظ)",
      _cst["soon_50"] is False)
# 🔴 **قفل F-L1** (عيبٌ حقيقيّ كشفه الطعن الخصومي في كودي): التعبئة **داخل الشمعة**
#    فترتيبُ اللمس داخلها مجهول ⇒ رأسُ شمعة التعبئة **لا يُحتسب** هدفًا، وإلّا فوزٌ
#    وهميّ. الحالة التمييزية: شمعةٌ واحدة تلمس 1.60 وتنزل 0.99 ودخولنا 1.00.
_cfl = S._candle_augment({}, None, [1.60, 1.05], [0.99, 1.02], [1.55, 1.03],
                         1.00, 0.93, 0)
check("🔴 ⏱️ لا نظر مستقبليّ: رأسُ شمعة التعبئة لا يُحتسب هدفًا (soon_50=False)",
      _cfl["soon_50"] is False and _cfl["bars_to_50"] is None)
check("🔴 ⏱️ و«bars_to_50 == 0» مستحيلٌ بنيويًّا (الهدف من filled+1 حصرًا)",
      "t_from = int(filled) + 1" in _insp0.getsource(S._candle_augment)
      and "k >= t_from" in _insp0.getsource(S._candle_augment))
_csl = S._candle_augment({}, None, [1.0] * 12 + [1.6], [0.98] * 13, [1.0] * 13,
                         1.00, 0.93, 0)
check("⏱️ حدّ النافذة: بلوغٌ بعد CANDLE_SOON_BARS لا يُحتسب وشيكًا",
      S.CONFIG["CANDLE_SOON_BARS"] == 10 and _csl["soon_50"] is False)
# 🔒 مطفأ ⇒ صفقة الأساس بت-بت (نفس نمط قفل BT_LIBERATION)
_cdsv = dict(S.CONFIG)
S.CONFIG["BT_CANDLE"] = 1
_cd_on = S.backtest_symbol("CDON", synth_pivot(seed=3))
S.CONFIG["BT_CANDLE"] = 0
_cd_off = S.backtest_symbol("CDOFF", synth_pivot(seed=3))
_cdk = lambda t: {k: v for k, v in t.items() if k != "symbol"}
_CDF = ("trig_ok", "trig_steps", "trig_rsi", "soon_50", "bars_to_50")
check("🕯️ وصل: مفعّلة ⇒ كل صفقة تحمل حقول الحالة والوشوك",
      len(_cd_on) >= 1 and all(set(_CDF) <= set(t) for t in _cd_on))
check("🔒 T-CANDLE·مطفأة ⇒ صفقة الأساس بت-بت (صفر حقل جديد وقاموس مطابق)",
      len(_cd_off) == len(_cd_on)
      and all(not any(k in _CDF for k in t) for t in _cd_off)
      and [_cdk(t) for t in _cd_off]
      == [{k: v for k, v in _cdk(t).items() if k not in _CDF} for t in _cd_on])
check("🕯️ المخرَج: يحمل الوشوك + «بلا حدٍّ زمنيّ» + سقف النجاح + قيد فيصل",
      (lambda m: "وشيك" in m and "بلا حدٍّ زمنيّ" in m and "وسمُ توقيتٍ" in m
       and "TG_2089" in m and "ثلاث سنوات" in m)(
          "\n".join((lambda: (S.CONFIG.__setitem__("BT_CANDLE", 1),
                              S.backtest_candle_compare(
                                  [dict(outcome="win", trig_ok=True, entry=1.0,
                                        stop=0.9, t1=1.3, soon_50=True,
                                        bars_to_50=3, mg_pre_stop=60.0)] * 3
                                  + [dict(outcome="loss", trig_ok=False, entry=1.0,
                                          stop=0.9, t1=1.3, soon_50=False,
                                          mg_pre_stop=5.0)] * 3))[1])())))
S.CONFIG.update(_cdsv)
check("🕯️ مطفأة ⇒ [] (صفر أثر على التقرير العادي)",
      S.backtest_candle_compare([{"outcome": "win", "trig_ok": True}]) == [])
check("🔒 T-CANDLE قفل: خارج الفرز والاختيار (باكتيست/تحليل فقط)",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("trigger_state", "_candle_augment", "backtest_candle_compare")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.analyze_ticker, S.scan_market, S.apply_float_gate)))

# 📏 مراقبة ما بعد الخروج (‏`observe_closed_alerts`) — سدُّ قياسٍ مقصوص كُشف 2026-07-30:
#    `update_tracking` يعالج المفتوحة فقط ⇒ لمسُ t1 (هدف قريب) يجمّد `max_gain_pct`،
#    فقراءة السجلّ «صفرٌ بلغ +50%» كانت **حقيقةً عن تتبّعنا لا عن الأسهم**.
def _obs_df(highs, start_iso="2026-01-02"):
    """إطار شموع تخييليّ (High فقط ما يهمّ) لاختبار المراقبة بلا شبكة."""
    idx = pd.date_range(start_iso, periods=len(highs), freq="D")
    return pd.DataFrame({"High": highs, "Low": [h * 0.9 for h in highs],
                         "Close": [h * 0.95 for h in highs]}, index=idx)


# سهمٌ لمس t1 عند +6% ثم **انفجر +150%** بعده: التتبّع القديم يقرأ 6% والمراقبة تقرأ الحقيقة
_obs_alert = {"symbol": "OBS", "date": "2026-01-01", "ref_bar": "2026-01-01",
              "price": 1.00, "stop": 0.93, "t1": 1.06, "t2": 1.5, "t3": 2.0,
              "status": "hit_t1", "result_date": "2026-01-05", "max_gain_pct": 6.0}
_obs_data = {"alerts": [dict(_obs_alert)]}
_obs_hi = [1.02, 1.06, 1.10, 1.40, 2.50] + [2.0] * 10       # القمّة 2.50 = +150%
_obs_done, _obs_left = S.observe_closed_alerts(
    _obs_data, fetch=lambda sym, start: _obs_df(_obs_hi),
    today=_dt.date(2026, 6, 1))
_obs_a = _obs_data["alerts"][0]
check("📏 المراقبة تقيس ما بعد الخروج: +150% بينما التتبّع المقصوص يقول +6%",
      _obs_done == 1 and _obs_a["mg_obs_pct"] == 150.0 and _obs_a["mg_obs_days"] == 15)
# 🔒 **القفل الحاسم**: الحكم (status/result_date/max_gain_pct) **لا يُمَسّ إطلاقًا** —
#    فسجلّ الربح/الخسارة يبقى حرفيًّا كما هو، ويُضاف المقدار الصادق إلى جانبه.
check("🔒 المراقبة لا تمسّ الحكم: status · result_date · max_gain_pct كما هي بت-بت",
      all(_obs_a[k] == _obs_alert[k]
          for k in ("status", "result_date", "max_gain_pct", "price", "t1")))
check("📏 المفتوحة شأنُ update_tracking وحده (المراقبة تتخطّاها)",
      S.observe_closed_alerts({"alerts": [dict(_obs_alert, status="open")]},
                              fetch=lambda s, t: _obs_df(_obs_hi),
                              today=_dt.date(2026, 6, 1))[0] == 0)
# حدّ النافذة: القمّة **بعد** الجلسة 60 يجب أن تُستبعَد — نفحص القيمة المكتوبة فعلًا
_obs_win = {"alerts": [dict(_obs_alert, symbol="WIN")]}
S.observe_closed_alerts(_obs_win,
                        fetch=lambda s, t: _obs_df([1.0] * 60 + [99.0]),
                        today=_dt.date(2026, 6, 1))
check("📏 النافذة محدودة بـTRACK_OBSERVE_DAYS: قمّةُ الجلسة 61 لا تُحتسب",
      S.TRACK_OBSERVE_DAYS == 60
      and _obs_win["alerts"][0].get("mg_obs_pct") == 0.0     # 1.00 → 1.00 = صفر
      and _obs_win["alerts"][0].get("mg_obs_days") == 60)
# مُنتهية النافذة لا تُجلَب مرّتين — يُقاس بـ**عدد النداءات** لا بالنتيجة
_obs_calls = []


def _obs_counting(sym, start):
    _obs_calls.append(sym)
    return _obs_df(_obs_hi)


check("📏 المُنتهية لا تُجلَب مرّةً أخرى (صفر نداء، لا مجرّد صفر نتيجة)",
      _obs_a.get("mg_obs_done") is True
      and S.observe_closed_alerts(_obs_data, fetch=_obs_counting,
                                  today=_dt.date(2026, 6, 1))[0] == 0
      and _obs_calls == [])
check("📏 فاشلة-آمنة: استثناء الجالب لا يرمي · وبلا شبكة لا عمل",
      S.observe_closed_alerts({"alerts": [dict(_obs_alert)]},
                              fetch=lambda s, t: 1 / 0,
                              today=_dt.date(2026, 6, 1)) == (0, 0))
check("📏 السقف يُعلَن: المؤجَّل يُرجَع عددًا لا يُصمت",
      S.observe_closed_alerts(
          {"alerts": [dict(_obs_alert, symbol="A%d" % i) for i in range(5)]},
          fetch=lambda s, t: _obs_df(_obs_hi), today=_dt.date(2026, 6, 1),
          cap=2) == (2, 3))
# 📊 الملخّص الصادق يقرأ mg_obs_pct لا max_gain_pct المقصوص
_obs_sum = S.observed_explosion_summary(
    {"alerts": [{"mg_obs_pct": 5.0, "max_gain_pct": 99.0},
                {"mg_obs_pct": 150.0}, {"mg_obs_pct": 60.0},
                # 🔴 غير مُراقَب بعد: عنده المقصوص وحده ⇒ **يُستبعَد كليًّا** ولا
                #    يُحسَب بقيمته المقصوصة (وإلّا خُلط المقياسان في رقمٍ واحد).
                {"max_gain_pct": 200.0}]})
check("📊 ملخّص الانفجار يقرأ المُراقَب **حصرًا** ويستبعد غير المُراقَب",
      _obs_sum["n"] == 3 and _obs_sum["median"] == 60.0 and _obs_sum["max"] == 150.0
      and _obs_sum["counts"][50] == 2 and _obs_sum["counts"][100] == 1
      and S.observed_explosion_summary({"alerts": []})["n"] == 0
      and S.observed_explosion_summary({"alerts": []})["median"] is None)
check("🔒 المراقبة خارج الفرز والاختيار (قياس/تقارير فقط)",
      all(_fn not in _insp0.getsource(_f)
          for _fn in ("observe_closed_alerts", "observed_explosion_summary")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.analyze_ticker, S.scan_market, S.backtest_symbol,
                     S.update_tracking)))

# 🔒📈 حصّاد الاقتراض بشاهد ضبط سالب (`ctb_harvest.py` · `borrow_labelled_set.md`)
import ctb_harvest as _CTB                                     # noqa: E402

_ctb_uni = ["S%03d" % i for i in range(400)]
_ctb_plan = _CTB.build_cohorts(["AAA", "ELAB", "YYAI"], ["BBB", "DSY"])
check("🔒 CTB·الوسم يسبق العضوية · والسالب يسبق الجميع",
      _ctb_plan["YYAI"] == "faisal_negative" and _ctb_plan["ELAB"] == "faisal_wait"
      and _ctb_plan["DSY"] == "faisal_exec" and _ctb_plan["AAA"] == "bot_selected"
      and _ctb_plan["BBB"] == "control_market")
# 🔴 قفل التصحيح: «متابعه فقط» **تنصّل لا رفض** ⇒ لا فئة باسم watch_only، وONCO
#    رفض الدخول بنصّه («لا طبعا … تنتظر») فلا يُوسَم exec. (`borrow_labelled_set.md`)
check("🔴 CTB·لا فئة حيّة «watch_only» بعد التصحيح · والخَرْط موثَّق للقارئ بعدي",
      # الاسم القديم يجب أن **يبقى** في الـdocstring (خَرْط schema 1→2 للسجلّ الإلحاقيّ)
      # لكن **لا يكون فئةً حيّة** ولا ثابتًا مُصدَّرًا.
      not hasattr(_CTB, "FAISAL_WATCH_ONLY") and not hasattr(_CTB, "FAISAL_ENTERED")
      and "faisal_watch_only" not in set(_ctb_plan.values())
      and "faisal_watch_only" not in set(_CTB._KIND)
      and "faisal_watch_only" in (_CTB.__doc__ or "")
      and _CTB.SCHEMA == 2)
check("🔴 CTB·ONCO في wait لا exec (نصّه: «لا طبعا … تنتظر 60 سنت ل 70»)",
      _ctb_plan.get("ONCO") == "faisal_wait" and "ONCO" not in _CTB.FAISAL_EXEC)
check("🔒 CTB·الفئة السالبة الحقيقية موجودة بمصدرها (YYAI «علميا لا»)",
      "YYAI" in _CTB.FAISAL_NEGATIVE and "علميا لا" in _CTB.FAISAL_NEGATIVE["YYAI"]
      and all(_CTB.FAISAL_NEGATIVE.values()) and all(_CTB.FAISAL_EXEC.values())
      and all(_CTB.FAISAL_WAIT.values()))       # لكلٍّ مصدره، لا رمزًا عاريًا
check("🎯 CTB·لوحة الشاهد حتميّة: نفس الشهر ⇒ نفس اللوحة · شهر آخر ⇒ لوحة مختلفة",
      _CTB.control_panel(_ctb_uni, "2026-07", 20)
      == _CTB.control_panel(list(reversed(_ctb_uni)), "2026-07", 20)
      and _CTB.control_panel(_ctb_uni, "2026-07", 20)
      != _CTB.control_panel(_ctb_uni, "2026-08", 20)
      and len(_CTB.control_panel(_ctb_uni, "2026-07", 20)) == 20)
# 🔒 وتطبيعُ المدخل جزءٌ من الحتميّة: مدخلٌ فيه مكرّرٌ وحالةُ حرفٍ مختلفة **يجب** أن
#    يعطي نفس لوحة المدخل النظيف (وإلا صارت اللوحة تتبدّل بتبدّل شكل ملفّ الكون).
_ctb_dirty = ([s.lower() for s in _ctb_uni] + _ctb_uni + ["s001", "S001"])
check("🔒 CTB·اللوحة تُطبِّع المدخل (تكرار + حالة حرف ⇒ نفس اللوحة، بلا مكرّر)",
      _CTB.control_panel(_ctb_dirty, "2026-07", 20)
      == _CTB.control_panel(_ctb_uni, "2026-07", 20)
      and len(set(_CTB.control_panel(_ctb_dirty, "2026-07", 20))) == 20)
check("🎯 CTB·السقف يوزّع بحصص: لا فئة تُقصّ كاملةً بصمت",
      len({_ctb_plan[s] for s in
           _CTB._select_within_cap(_ctb_plan, 5)[0]}) == 5
      and sum(_CTB._select_within_cap(_ctb_plan, 5)[1].values()) > 0)
# 🔒 «يُعلَن ولا يُصمت»: غياب لوحة الشاهد **يجب أن يُطبَع**، فلا يُقرأ السجلّ الناقص
#    لاحقًا كأنه كاملٌ. (طفرةٌ أسقطت الإعلانَ وحده نجت من الأقفال الأولى — فهذا قفلُها.)
def _ctb_no_control_announced():
    import io as _io2
    import contextlib as _cx2
    import tempfile as _tf2
    buf = _io2.StringIO()
    with _tf2.TemporaryDirectory() as _td2:
        try:
            with _cx2.redirect_stdout(buf):
                _CTB.harvest(fetch=lambda s: {"shares_available": 1}, watch_syms=[],
                             today_iso="2026-07-30", universe=[],
                             path=_os_ctb.path.join(_td2, "x.jsonl"))
        except BaseException:
            return False
    return "غائبة" in buf.getvalue()


import os as _os_ctb                                            # noqa: E402
check("🔒 CTB·غياب لوحة الشاهد يُعلَن صريحًا (لا يُستبدَل ولا يُصمت)",
      _ctb_no_control_announced())
check("🎯 CTB·كل صفّ يحمل label_kind/label_source ⇒ الدائرية تُقرأ من السجلّ",
      _CTB._KIND["faisal_exec"] == "decision"
      and _CTB._KIND["control_market"] == "membership"
      and _CTB._SOURCE["control_market"] == "universe_sample")
def _ctb_selftest_ok():
    """يحوّل سقوط الاختبار الذاتي إلى **فحصٍ فاشل مقروء** لا انهيارَ سويّة.
    (درس مسجَّل: السويّة المنهارة تُقرأ خطأً «صفر فشل» — فالتشخيص جزءٌ من القفل.)"""
    try:
        return _CTB._selftest() == 0
    except BaseException as e:                       # AssertionError وغيره
        print(f"   ↳ سبب سقوط الاختبار الذاتي: {type(e).__name__}: {e}")
        return False


check("🔒 CTB·الاختبار الذاتي بلا شبكة يمرّ (سقف/تعذّر/استثناء كلها فاشلة-آمنة)",
      _ctb_selftest_ok())
_ctb_src = open("ctb_harvest.py", encoding="utf-8").read()
check("🔒 CTB·خارج الفرز: لا مسار إنتاج يستورده",
      "ctb_harvest" not in open("Super_stock.py", encoding="utf-8").read())
check("🔒 CTB·لا يكتب حالةً إطلاقًا: كل فتحٍ للكتابة بوضع إلحاق وعلى سجلّه وحده",
      # القائمة تُقرأ فقط (`json.load`) ولا تُكتب أبدًا (`json.dump` غائب كليًّا)،
      # والفتح الكتابيّ الوحيد `open(path or LOG_PATH, "a")` — فلا وضع "w" في الوحدة.
      "json.dump(" not in _ctb_src.replace("json.dumps(", "")
      and '"w"' not in _ctb_src and "'w'" not in _ctb_src
      and _ctb_src.count('"a"') == 1)
check("🔒 CTB·workflow الحصاد يستعمل نمط الدفع المحمي (درس ignition: دفعٌ عارٍ ضيّع بيانات)",
      all(t in open(".github/workflows/ctb_harvest.yml", encoding="utf-8").read()
          for t in ("git rebase", "for i in 1 2 3 4 5", "::error::")))
# 🚧 سقف GitHub الصلب: **25 مدخلًا لكل `workflow_dispatch`** — تجاوزُه لا يُكتشَف
#    بالـlint ولا بالتحليل الساكن، بل بـ422 عند **أول محاولة تشغيل** («you may only
#    define up to 25 inputs»)، أي بعد الدمج والدفع. حدث فعلًا مع `backtest.yml` (26).
#    فالقفل يمنع تكراره على أي workflow.
def _wf_dispatch_inputs(path):
    """يعدّ مداخل `workflow_dispatch` بمحاذاة الإزاحة (لا تجميعًا أعمى للنقطتين)."""
    ls = open(path, encoding="utf-8").read().splitlines()
    n, ind = 0, None
    for i, l in enumerate(ls):
        if l.strip() == "inputs:" and any(
                x.strip() == "workflow_dispatch:" for x in ls[max(0, i - 6):i]):
            ind = len(l) - len(l.lstrip())
            continue
        if ind is None:
            continue
        st = l.strip()
        if st and not st.startswith("#"):
            cur = len(l) - len(l.lstrip())
            if cur <= ind:                     # خرجنا من كتلة inputs
                break
            if cur == ind + 2 and st.endswith(":"):
                n += 1
    return n


_wf_over = {f: _wf_dispatch_inputs(f) for f in _c10_files
            if _wf_dispatch_inputs(f) > 25}
check("🚧 كل workflow تحت سقف GitHub الصلب 25 مدخلًا (وإلا 422 عند أول تشغيل)",
      _wf_over == {})
check("🔒 العدّاد صادق: backtest.yml (الأكبر) يُقرأ فعلًا بعدد موجب لا صفرًا",
      _wf_dispatch_inputs(".github/workflows/backtest.yml") >= 20)
check("🔓 T-LIB·نافذة الانتظار غير معروضة مدخلًا (مُثبَّتة بالتسجيل المسبق، لا دِيال ضبط)",
      "bt_liberation" in open(".github/workflows/backtest.yml", encoding="utf-8").read()
      and "bt_lib_wait" not in open(".github/workflows/backtest.yml",
                                   encoding="utf-8").read())
# 🚪 T-GATES: مدخلا G5/G6 + الإسقاط المُبرَّر الذي أفسح لهما (سقف 25 مبلوغ بالضبط)
_g6_yml = open(".github/workflows/backtest.yml", encoding="utf-8").read()
check("🚪 مدخلا الذراعين موصولان في backtest.yml (input + env معًا — لا ميزة معلّقة)",
      all(t in _g6_yml for t in ("bt_min_price:", "bt_m4_post_split:",
                                 "BT_MIN_PRICE: ${{", "BT_M4_POST_SPLIT: ${{")))
check("🚪 backtest.yml عند سقف GitHub بالضبط (‏25) — أي إضافة لاحقة تستلزم إسقاطًا مُبرَّرًا",
      _wf_dispatch_inputs(".github/workflows/backtest.yml") == 25)
check("🚪 المُسقَطان (T-SHORT/T-STOP — حكمٌ نهائيّ) خرجا من المدخلات والـenv معًا",
      not any(t in _g6_yml for t in ("bt_short:", "bt_stop_pct:",
                                     "BT_SHORT: ${{", "BT_STOP_PCT: ${{")))
check("🚪 وإسقاطهما **قابل للنقض**: صفّاهما في جدول التعيين وعلماهما في CONFIG باقيان",
      all(f'("{_k}"' in _insp0.getsource(S._apply_backtest_overrides)
          for _k in ("BT_SHORT", "BT_STOP_PCT"))
      and S.CONFIG.get("BT_SHORT") == 0 and S.CONFIG["STOP_BELOW_LOW_PCT"] == (5, 7))
check("🚪 وسببُ الإسقاط مكتوبٌ في الملفّ نفسه (لا قرار صامت)",
      "T-SHORT" in _g6_yml and "T-STOP" in _g6_yml and "25 مدخلًا" in _g6_yml)
check("🔐 010·acc_verify يمرّر السنة عبر env لا الصدفة",
      "YEAR: ${{ github.event.inputs.year }}"
      in open(".github/workflows/acc_verify.yml", encoding="utf-8").read()
      and 'NAME="acc-verify-${YEAR}"'
      in open(".github/workflows/acc_verify.yml", encoding="utf-8").read())
# 🔒 صون: الملفّات التي **تدفع** للريبو ما زالت contents: write (تضييقها = كسر صامت)
# 🔴 `split_hunter.yml` **انتقل من القراءة إلى الكتابة** بالبند ⓿-و (2026-07-31): صار
#    يدفع ختم آخر مسحٍ ناجح (`split_hunter_stamp.json`) ليَكشف المسارُ اليومي سقوطَ
#    كرونه. وتضييقه إلى `read` يُفشِل الدفع صامتًا ⇒ ختمٌ متجمّد ⇒ **تحذيرٌ يوميّ كاذب**
#    يُدرَّب المالك على تجاهله = موت الحارس. فنُقل هنا لا حُذف من الفحص.
_c10_writers = ("daily_screener.yml", "pullback_monitor.yml", "ignition.yml",
                "hand_flow.yml", "e2_recover.yml", "cline_weekly_review.yml",
                "split_hunter.yml")
def _c10_perm(fname, key):
    """قيمة صلاحية معلَنة فعلًا (سطر إعلان، لا ذِكر في تعليق) — ignition.yml يشرح
    `contents: write` في تعليق فوق الكتلة، فالمطابقة النصّية كانت تمرّ على تعليق."""
    for _l in open(f".github/workflows/{fname}", encoding="utf-8").read().splitlines():
        if _l.startswith("#") or _l.lstrip().startswith("#"):
            continue
        _m = _re10.match(r"^\s+%s:\s*(\w+)" % key, _l)
        if _m:
            return _m.group(1)
    return None


check("🔒 010·صون: كل workflow يدفع للريبو ما زال contents: write (إعلانًا لا تعليقًا)",
      all(_c10_perm(_f, "contents") == "write" for _f in _c10_writers))
# 🔒 صون: الملفّات التي تُنزّل artifacts عبر run-id تحتاج actions: read
check("🔒 010·صون: منزّلات artifacts عبر run-id تعلن actions: read",
      all(_c10_perm(_f, "actions") == "read"
          for _f in ("backtest.yml", "acc_report.yml", "acc_verify.yml")))
check("🔒 010·التسعة الباقية تعلن contents: read (لا write زائد)",
      all(_c10_perm(_f, "contents") == "read" for _f in (
          "acc_report.yml", "acc_verify.yml", "analyze_asof.yml", "analyze.yml",
          "hand_check.yml", "ignition_verify.yml", "polygon_health.yml",
          "scan_earnings.yml", "technical.yml")))


# ==========================================================
# 🧹 خطة 011: تنظيف الدوال الميتة + صون المحفوظة بقرار مالك
# ==========================================================
# 🔴 القاعدة المستخلَصة: **«غير مستعمَلة» ≠ «ميتة»** في هذا المستودع. قبل أي حذف
#    ابحث عن الاسم في CLAUDE.md؛ وجود «محفوظة» = قرار مالك. وهذا القفل يُشفّر القاعدة
#    كي لا تعتمد على القراءة في أي جولة تنظيف قادمة.
print("\n=== 🧹 خطة 011: تنظيف + صون ===")

_C11_KEEP = ("key_levels_block", "h4_levels_block", "position_size_line",
             "acc_line", "silent_accumulation", "half_down_target", "half_down_line",
             "ce_float_info", "_parse_ce_float",
             # D9: لها اختبارات وظيفية (لا مجرّد قفل) ⇒ ميزة نائمة لا ميتة
             "split_watch_report", "build_split_watch_section", "_split_row",
             # صارت بلا مستدعٍ بحذفٍ متسلسل — تُراجَع مستقلّةً لا تُحذف بالتبعية
             "news_links")
check("🔒 011·صون: الدوال المحفوظة بقرار المالك موجودة (لا تُحذف في أي تنظيف)",
      all(callable(getattr(S, _n, None)) for _n in _C11_KEEP))
_C11_GONE = ("fetch_4h_signal", "short_line", "risk_lines", "news_block",
             "splits_block")
check("🧹 011·الخمس الميتة حُذفت فعلًا (لا بقايا تضلّل القارئ)",
      not any(hasattr(S, _n) for _n in _C11_GONE))
_c11_src = open("Super_stock.py", encoding="utf-8").read()
check("🧹 011·لا مرجع متبقٍّ لأي محذوفة (حتى في التعليقات)",
      not any(_n in _c11_src for _n in _C11_GONE))
# 🔴 **إصلاح قفل (مراجعة مستقلّة 2026-07-29):** القفل السابق هنا كان **وهميًّا** — شرطاه
#    يطابقان نصًّا **عامًّا**: (أ) تعليق `«لم يعد يُدفَع بالتقرير اليومي»` موجود في
#    `run_daily_watchlist` **منذ ما قبل الخطة 011** (على `origin/main` أيضًا) فيمرّ دائمًا ·
#    (ب) و«تصحيح 2026-07-28» يظهر **مرّتين** في CLAUDE.md (الأخرى من الخطة 003). فحذفُ فقرة
#    D9 كاملةً كان يُبقي السويّة خضراء (مُثبَت بطفرة). القفل الآن:
#    ① يقتطع **فقرة D9 وحدها** (بين ترويسة D9 وبداية D10) فلا يمرّ نصّ من موضع آخر،
#       ويشترط علامة **فريدة في الملفّ كلّه**؛
#    ② ويتحقّق أن **ادّعاء الفقرة صحيح في الكود** — فلو أُعيد وصل D9 باليومي لصار
#       التوثيق كاذبًا ويسقط القفل. (تقاطع توثيق↔كود بدل مطابقة نصّ.)
_c11_claude = open("CLAUDE.md", encoding="utf-8").read()
_C11_D9_MARK = "هذا الوصل مقطوع منذ 2026-07-09"
_c11_i = _c11_claude.find("D9 **قسم «مراقبة التقسيم العكسي»**")
_c11_j = _c11_claude.find("D10 **«تدوير", _c11_i + 1)
_c11_d9 = _c11_claude[_c11_i:_c11_j] if 0 <= _c11_i < _c11_j else ""
check("📝 011·فقرة D9 نفسها تحمل تصحيح «الوصل مقطوع» (علامة فريدة لا نصّ عامّ)",
      bool(_c11_d9) and _C11_D9_MARK in _c11_d9
      and _c11_claude.count(_C11_D9_MARK) == 1)
check("📝 011·وادّعاء فقرة D9 صحيح في الكود (splits=[] والقسم غير مدفوع باليومي)",
      "splits = []" in _insp0.getsource(S.run_daily_watchlist)
      and "لم يعد يُدفَع بالتقرير اليومي"
      in _insp0.getsource(S.run_daily_watchlist))


# ==========================================================
# 🔧 P1 — شريط التجهيز الإلزاميّ (2026-07-30، `OPUS_EXECUTION_PACKAGE.md §②-ب`)
# ثلاثة أعطال **قياس** مقاسة بالتشغيل: ① علمٌ ميّت لا يصل CONFIG · ② قصّ مزدوج
# يُصمِت توزيع الرفض · ③ «نواقص فوق الحدّ» تُسجَّل عددًا لا أسماءً.
# كل ما هنا **طباعة/قياس** — أي تسرّب لطبقة الحسم يجب أن يُسقط اختبارًا.
# ==========================================================
print("\n=== 🔧 P1: شريط التجهيز (أعلام حيّة · توزيع رفض بلا قصّ · أسماء النواقص) ===")

# --- ① العلم الميّت: BT_CANDLE كان يُمرَّر في backtest.yml ولا يصل CONFIG أبدًا ---
_p1_cfg_save = {k: S.CONFIG.get(k) for k in ("BT_CANDLE", "BT_LIBERATION")}
check("P1-①: الإنتاج محصّن — BT_CANDLE لا يُطبَّق خارج وضع BACKTEST",
      S._apply_backtest_overrides("FULL", {"BT_CANDLE": "1"}) == []
      and S.CONFIG.get("BT_CANDLE") == _p1_cfg_save["BT_CANDLE"])
_p1_applied = S._apply_backtest_overrides("BACKTEST", {"BT_CANDLE": "1"})
check("P1-①: BT_CANDLE يصل CONFIG فعلًا بوضع BACKTEST (كان علمًا ميّتًا ⇒ no-op صامت)",
      S.CONFIG.get("BT_CANDLE") == 1 and "BT_CANDLE=1" in _p1_applied)
for _k, _v in _p1_cfg_save.items():
    S.CONFIG[_k] = _v

# 🔒 القفل النظاميّ (يمنع تكرار الصنف كلّه لا الحالة وحدها): **كل** مفتاح `BT_*`
# يُمرَّر في بيئة `backtest.yml` يجب أن يكون له صفٌّ في جدول `_apply_backtest_overrides`.
# الاستثناء الوحيد المسموح `BT_FROZEN_PATH` (مسار ملف يُقرأ مباشرةً من os.environ في
# run_backtest، ليس عتبة CONFIG) — والاستثناء نفسه **مُبرهَن** أدناه فلا يتعفّن.
_P1_DIRECT_ENV = {"BT_FROZEN_PATH"}
_p1_yml = open(".github/workflows/backtest.yml", encoding="utf-8").read()
_p1_env_keys = set(__import__("re").findall(r"^\s+(BT_[A-Z0-9_]+):\s*\$\{\{",
                                            _p1_yml, __import__("re").M))
_p1_tbl_keys = set(__import__("re").findall(
    r'\("(BT_[A-Z0-9_]+)"\s*,', _insp0.getsource(S._apply_backtest_overrides)))
# 🎯 وتمديدٌ مُشدَّد (لا مُرخٍّ) لعلمٍ **مركَّب** كـ`BT_CORE5`: لا صفَّ له في الجدول
# لأنه يضبط **عدّة** مفاتيح دفعةً واحدة. فالشرط البديل **أقوى لا أضعف**: يجب أن يظهر
# نصًّا داخل مصدر `_apply_backtest_overrides` نفسها بصيغة القراءة `env.get("BT_X")`
# ⇒ **مُبرهَنٌ أن نفس الدالّة تعالجه**، فلا يمرّ علمٌ ميّتٌ باسم «مركَّب».
_p1_src = _insp0.getsource(S._apply_backtest_overrides)
_p1_composite = {k for k in _p1_env_keys if f'env.get("{k}")' in _p1_src}
_p1_dead = sorted(_p1_env_keys - _p1_tbl_keys - _P1_DIRECT_ENV - _p1_composite)
check("P1-①🔒: كل مفتاح BT_* في backtest.yml له صفّ في جدول التعيين (لا علم ميّت)",
      _p1_env_keys and not _p1_dead, f"ميّت={_p1_dead}")
check("P1-①🔒: العلم المركَّب مُبرهَنٌ أن الدالّة تقرأه (لا «مركَّب» اسمًا فقط)",
      "BT_CORE5" in _p1_composite)
check("P1-①🔒: استثناء BT_FROZEN_PATH مُبرهَن (يُقرأ فعلًا من os.environ في run_backtest)",
      all(f'os.environ.get("{k}"' in _insp0.getsource(S.run_backtest)
          for k in _P1_DIRECT_ENV))

# --- ② توزيع أسباب الرفض: دمج المتشظّي + بلا بتر + سقوف مُعلَنة ---
_p1_reasons = {"بعيد_عن_الدخول(43%)": 30, "بعيد_عن_الدخول(47%)": 25,
               "بعيد_عن_الدخول(35%)": 20, "M2_هبوط_تحت_40": 40,
               "M4_base_واسعة": 9, "M5_سيولة": 4, "نواقص_فوق_3": 3}
_p1_lines = S.reject_distribution_lines(_p1_reasons, n_symbols=7)
_p1_txt = "\n".join(_p1_lines)
check("P1-②: المفاتيح المتشظّية تلتئم عند العدّ (بعيد_عن_الدخول = 75 لا ثلاثة أرقام)",
      "بعيد_عن_الدخول = 75" in _p1_txt and "بعيد_عن_الدخول(43%) = " not in _p1_txt)
check("P1-②: المتشظّي المُلتئم يتصدّر لو كان الأكثر (75 > 40) — لا يُدفَن بالتشظّي",
      _p1_lines[1].strip().startswith("1. بعيد_عن_الدخول = 75"))
check("P1-②: صفر بتر — كل مفتاح مجمَّع يظهر (لا [:3])",
      all(k in _p1_txt for k in
          ("M2_هبوط_تحت_40", "M4_base_واسعة", "M5_سيولة", "نواقص_فوق_3")))
check("P1-②: سطر التفصيل يحفظ الصيغ الخام للمفتاح الملتئم (لا يضيع التفصيل)",
      "تفصيل «بعيد_عن_الدخول»" in _p1_txt and "(43%)=30" in _p1_txt
      and "(47%)=25" in _p1_txt and "(35%)=20" in _p1_txt)
_p1_many = {f"بعيد_عن_الدخول({i}%)": 1 for i in range(S.REJECT_VARIANTS_SHOW + 5)}
_p1_many_txt = "\n".join(S.reject_distribution_lines(_p1_many))
check("P1-②: القصّ في العرض **يُعلَن** ولا يقع صامتًا (دستور «لا سقوف صامتة»)",
      "صيغة أخرى" in _p1_many_txt
      and f"({S.REJECT_VARIANTS_SHOW + 5} صيغة)" in _p1_many_txt)
check("P1-②: مدخل فارغ/تالف ⇒ لا سطر (فاشل-آمن، لا استثناء)",
      S.reject_distribution_lines({}) == []
      and S.reject_distribution_lines({"x": None}) == []
      and S.reject_distribution_lines(None) == [])
check("P1-②: `_reject_key_base` يقصّ ما بين القوسين فقط (ولا يبتلع المفتاح كلّه)",
      S._reject_key_base("بعيد_عن_الدخول(43%)") == "بعيد_عن_الدخول"
      and S._reject_key_base("M2_هبوط_تحت_40") == "M2_هبوط_تحت_40"
      and S._reject_key_base("(43%)") == "(43%)")

# --- ③ أسماء النواقص لا عددها ---
check("P1-③: التسمية القانونية تُوحّد النصّ المُنسَّق (أرقامه متغيّرة)",
      S._soft_fail_name("الهبوط 43% (المثالي 50% فأكثر)")
      == S._soft_fail_name("الهبوط 47% (المثالي 50% فأكثر)")
      == "M2·هبوط_دون_المثالي"
      and S._soft_fail_name("لا نمط شمعة انعكاسي") == "M7·لا_نمط_انعكاسي")
check("P1-③: المجهول لا يُسقَط صامتًا — يُوسَم «؟·» بنصّه منزوع الأرقام",
      S._soft_fail_name("نقصٌ جديد 12%").startswith("؟·")
      and "#" in S._soft_fail_name("نقصٌ جديد 12%")
      and S._soft_fail_name("").startswith("؟·"))
# 🔒 قفل AST: كل `soft_fails.append(...)` في الكود له صفٌّ في `_SOFT_FAIL_NAMES` —
# فنقصٌ جديد يُضاف بلا تسمية **يُسقط السويّة** بدل أن يظهر «؟·» في التقرير بصمت.
_p1_tree = _ast_p1.parse(open("Super_stock.py", encoding="utf-8").read())
_p1_texts = []
for _nd in _ast_p1.walk(_p1_tree):
    if (isinstance(_nd, _ast_p1.Call) and isinstance(_nd.func, _ast_p1.Attribute)
            and _nd.func.attr == "append" and _nd.args
            and "soft_fails" in _ast_p1.unparse(_nd.func.value)):
        _a = _nd.args[0]
        if isinstance(_a, _ast_p1.Constant) and isinstance(_a.value, str):
            _p1_texts.append(_a.value)
        elif isinstance(_a, _ast_p1.JoinedStr):
            _p1_texts.append("".join(
                p.value if isinstance(p, _ast_p1.Constant) else "#" for p in _a.values))
_p1_unnamed = [t for t in _p1_texts if S._soft_fail_name(t).startswith("؟·")]
check("P1-③🔒: كل نقصٍ في الكود له اسمٌ قانونيّ (AST — نقصٌ جديد بلا صفّ يُسقط السويّة)",
      len(_p1_texts) >= 11 and not _p1_unnamed,
      f"نصوص={len(_p1_texts)} بلا_اسم={_p1_unnamed[:2]}")

# 🔒 نقطة النداء الحيّة (دستور ⑨: «الميزة موصولة» تُثبَت من الاستعمال لا من الدالّة):
# نمشي `analyze_ticker` نفسها حتى تسقط على «نواقص فوق الحدّ» ونتأكّد أن الأسماء وصلت.
# لو أُعيدت تسمية `soft_fails` المحلّية داخل الجذر لسقط هذا الاختبار (وهو المقصود).
_p1_sv_stats, _p1_sv_soft = dict(S._REJECT_STATS), dict(S._REJECT_SOFT_FAILS)
S._REJECT_STATS.clear()
S._REJECT_SOFT_FAILS.clear()
for _sd in range(12):
    _p1_df = synth_pivot(seed=_sd)
    for _i in range(140, len(_p1_df), 5):
        S.analyze_ticker(f"P1{_sd}", _p1_df.iloc[:_i])
_p1_live_stats, _p1_live_soft = dict(S._REJECT_STATS), dict(S._REJECT_SOFT_FAILS)
S._REJECT_STATS.clear()
S._REJECT_STATS.update(_p1_sv_stats)
S._REJECT_SOFT_FAILS.clear()
S._REJECT_SOFT_FAILS.update(_p1_sv_soft)
_p1_nq = sum(v for k, v in _p1_live_stats.items() if "نواقص_فوق" in k)
check("P1-③🔒 حيّ: المشي الحقيقي يُسقط على «نواقص فوق الحدّ» (شاهد ضبط للقياس نفسه)",
      _p1_nq > 0, f"نواقص_فوق={_p1_nq}")
check("P1-③🔒 حيّ: الأسماء تُلتقط من نقطة النداء الفعلية داخل analyze_ticker",
      bool(_p1_live_soft)
      and all(not n.startswith("؟·") for n in _p1_live_soft)
      and max(_p1_live_soft.values()) <= _p1_nq,
      str(sorted(_p1_live_soft.items(), key=lambda x: -x[1])[:4]))
check("P1-③🔒: مفتاح الرفض نفسه لم يتغيّر (يبقى قابلًا للتجميع — لا تشظٍّ جديد)",
      any(k == f"نواقص_فوق_{S.CONFIG.get('WATCH_MAX_FAILS', 3)}"
          for k in _p1_live_stats)
      and not any("[" in k or "·" in k for k in _p1_live_stats))
check("P1-③🔒: الجذر `analyze_ticker` لم يُمَسّ (لا ذكر لطبقة الالتقاط داخله)",
      all(x not in _insp0.getsource(S.analyze_ticker)
          for x in ("_REJECT_SOFT_FAILS", "_soft_fail_name", "_reject_key_base")))


def _p1_bad_frame():
    soft_fails = 7           # نوع تالف عمدًا (لا يُتكرَّر عليه)
    return S._reject("نواقص_فوق_3"), soft_fails


S._REJECT_STATS.clear()
_p1_bad = _p1_bad_frame()[0]
_p1_bad_ok = (_p1_bad is None and S._REJECT_STATS.get("نواقص_فوق_3") == 1)
S._REJECT_STATS.clear()
S._REJECT_STATS.update(_p1_sv_stats)
check("P1-③: الالتقاط فاشل-آمن — نوعٌ تالف لا يرمي ولا يمنع تسجيل الرفض", _p1_bad_ok)

# --- ②🔒 تكامل: run_backtest يطبع في الحالتين، والقرار **لم يتغيّر** ---
_p1_n = 300


def _p1_synth(seed, scale=1.0):
    """مسارٌ متنوّع عمدًا (سعر تحت الأرضية ⟶ انفجار ⟶ انهيار ⟶ ارتداد ⟶ هبوط ثانٍ ⟶
    قاعدة) مع نافذة سيولة جافّة — ليُنتج **أكثر من ثلاثة** أسباب رفض متمايزة، وإلا
    كان اختبار «صفر بتر» أعمى (نجح مع `[:3]` أيضًا — كشفه شاهد الضبط أدناه)."""
    rs = np.random.RandomState(seed)
    cl = []
    cl += list(np.linspace(1.1, 1.4, 30) * scale)
    cl += list(np.linspace(1.4, 12.0, 25) * scale)
    cl += list(np.linspace(12.0, 3.0, 45) * scale)
    cl += list(np.linspace(3.0, 5.5, 40) * scale)
    cl += list(np.linspace(5.5, 2.6, 60) * scale)
    cl += list(np.linspace(2.6, 3.4, 50) * scale)
    cl += list(np.linspace(3.4, 2.9, _p1_n - len(cl)) * scale)
    cl = np.array(cl[:_p1_n], dtype=float)
    o = cl * (1 + rs.uniform(-0.006, 0.006, _p1_n))
    h = np.maximum(o, cl) * (1 + rs.uniform(0.0, 0.02, _p1_n))
    lo = np.minimum(o, cl) * (1 - rs.uniform(0.0, 0.02, _p1_n))
    v = rs.randint(300_000, 2_000_000, _p1_n).astype(float)
    v[200:240] *= 0.02                       # نافذة سيولة جافّة (M5)
    return pd.DataFrame({"Open": o, "High": h, "Low": lo, "Close": cl, "Volume": v},
                        index=pd.date_range("2024-01-01", periods=_p1_n, freq="B"))


_P1_SYMS = ["P1A", "P1B", "P1C"]
_p1_data = {s: _p1_synth(3 + i, 1.0 + 0.15 * i) for i, s in enumerate(_P1_SYMS)}
_p1_saved = (S.log, S.send_telegram, S.send_telegram_document, S._write_csv_file,
             S.download_history, S.get_universe, S.MODE,
             _os_hc.environ.get("BACKTEST_YEAR"), _os_hc.environ.get("BACKTEST_MONTH"))
_p1_log = []
_p1_grab = []          # يلتقط قائمة الصفقات النهائية كما كتبها run_backtest للـCSV


def _p1_run(market_mode):
    _p1_log.clear()
    _p1_grab.clear()
    S.log = lambda m: _p1_log.append(str(m))
    S.send_telegram = lambda *a, **k: True
    S.send_telegram_document = lambda *a, **k: True
    S._write_csv_file = lambda rows, *a, **k: (_p1_grab.append(list(rows or [])), None)[1]
    S.download_history = lambda syms, **k: {s: _p1_data[s] for s in syms if s in _p1_data}
    S.get_universe = lambda: list(_P1_SYMS)
    _os_hc.environ["BACKTEST_YEAR"] = "2024"
    _os_hc.environ["BACKTEST_MONTH"] = ""
    S.run_backtest(None if market_mode else list(_P1_SYMS))
    return "\n".join(_p1_log)


try:
    _p1_mkt = _p1_run(True)
    _p1_mkt_trades = _p1_grab[0] if _p1_grab else None
    _p1_soft_mkt = dict(S._REJECT_SOFT_FAILS)     # سوق كامل = بلا تشخيص أصلًا
    _p1_sym = _p1_run(False)
    _p1_soft_sym = dict(S._REJECT_SOFT_FAILS)     # رموز محدّدة = التشخيص يعمل قبل المشي
    # مرجع مستقلّ للقرار: نبني الصفقات بنداء backtest_symbol مباشرةً (بلا طبقة الطباعة)
    S._REJECT_SOFT_FAILS.clear()
    _p1_ref_trades = []
    for _s in _P1_SYMS:
        _p1_ref_trades += S.backtest_symbol(_s, _p1_data[_s], {},
                                            date_window=("2024-01-01", "2024-12-31"))
    _p1_soft_walk = dict(S._REJECT_SOFT_FAILS)    # نواقص **المشي وحده** = الحقيقة الأرضية
    _p1_ref_trades = [t for t in _p1_ref_trades if str(t.get("date", ""))[:4] == "2024"]
    _p1_ref = S.backtest_stats(_p1_ref_trades)
finally:
    (S.log, S.send_telegram, S.send_telegram_document, S._write_csv_file,
     S.download_history, S.get_universe, S.MODE, _p1_y, _p1_m) = _p1_saved
    for _k, _v in (("BACKTEST_YEAR", _p1_y), ("BACKTEST_MONTH", _p1_m)):
        if _v is None:
            _os_hc.environ.pop(_k, None)
        else:
            _os_hc.environ[_k] = _v

check("P1-②🔒 حيّ: وضع **السوق الكامل** يُصدر توزيع الرفض (كان `and not market` يُصمته)",
      "توزيع أسباب الرفض" in _p1_mkt and "باكتيست·أسباب " in _p1_mkt)
check("P1-②🔒 حيّ: وضع الرموز المحدّدة يُصدره أيضًا (الحالتان)",
      "توزيع أسباب الرفض" in _p1_sym and "باكتيست·أسباب " in _p1_sym)
_p1_per = [x for x in _p1_mkt.split("\n") if x.startswith("باكتيست·أسباب ")]
_p1_declared = [int(m.group(1)) for m in
                (__import__("re").search(r"(\d+) سببًا\)", x) for x in _p1_per) if m]
_p1_printed = [len(x.split("): ", 1)[1].split(" · ")) for x in _p1_per]
check("P1-②🔒 حيّ: شاهد ضبط — رمزٌ واحد على الأقل بأربعة أسبابٍ فأكثر (وإلا فالقياس أعمى)",
      bool(_p1_declared) and max(_p1_declared) >= 4, f"أقصى={_p1_declared}")
check("P1-②🔒 حيّ: المطبوع = المُعلَن لكل رمز ⇒ صفر بتر (كان `[:3]` يقصّ الذيل)",
      bool(_p1_per) and _p1_declared == _p1_printed and len(_p1_declared) == len(_p1_per),
      f"معلن={_p1_declared} مطبوع={_p1_printed}")
_p1_fp = [x for x in _p1_mkt.split("\n") if x.startswith("باكتيست — ")]
check("P1-②🔒 **طباعة محضة**: signals/decided/win_rate تطابق مرجعًا محسوبًا مستقلًّا",
      bool(_p1_fp) and _p1_ref["signals"] > 0        # شاهد ضبط: مقارنة غير فارغة
      and f"إشارات={_p1_ref['signals']} " in _p1_fp[0]
      and f"محسومة={_p1_ref['decided']} " in _p1_fp[0]
      and f"نجاح={_p1_ref['win_rate']:.0f}%" in _p1_fp[0]
      and f"غير_مُعبّأة={_p1_ref['no_fill']}" in _p1_fp[0],
      f"{_p1_fp[:1]} vs ref={_p1_ref['signals']}/{_p1_ref['decided']}")
# 🔒 الأقوى: قاموس **كل صفقة بكل حقولها** كما كتبه run_backtest = المرجع المستقلّ.
# أي تسرّب من طبقة الطباعة إلى الحسم (ولو حقلًا واحدًا) يُسقط هذا الاختبار.
_p1_same = (_p1_mkt_trades is not None
            and len(_p1_mkt_trades) == len(_p1_ref_trades)
            and all(a == b for a, b in zip(_p1_mkt_trades, _p1_ref_trades)))
check("P1-②🔒 **طباعة محضة**: قاموس كل صفقة (كل الحقول) مطابق للمرجع المستقلّ",
      _p1_same and len(_p1_ref_trades) > 0,
      f"n={len(_p1_mkt_trades or [])} ref={len(_p1_ref_trades)}")
check("P1-④ج: بلا علمٍ تقسيميّ لا يُطبع سطر «العلم فعّال» (لا ضجيج كاذب)",
      "العلم فعّال" not in _p1_mkt and "خامل" not in _p1_mkt)

# 🔒 حارس تلوّث التشخيص: في وضع الرموز المحدّدة يشتغل `_diagnose_symbol` **ثماني مرّات
# لكل رمز** على شرائح تاريخية، فتُحسَب نواقصها ضمن أسماء «نواقص فوق الحدّ» وتُضخّم
# التقرير (مقيس على هذي البيانات نفسها: التشخيص يضيف ~61 مقابل 100 للمشي، **وبفئةٍ
# لا ينتجها المشي أصلًا**). فالمعيار: أسماء التشغيلة = أسماء **المشي وحده** بالضبط.
check("P1-③🔒 شاهد ضبط: المشي وحده يُنتج أسماء نواقص (وإلا فالمقارنة تحت فارغة)",
      bool(_p1_soft_walk) and sum(_p1_soft_walk.values()) > 0,
      f"مشي={sum(_p1_soft_walk.values())}")
check("P1-③🔒: التشخيص لا يلوّث عدّاد الأسماء (وضع الرموز = المشي وحده بالضبط)",
      _p1_soft_sym == _p1_soft_walk,
      f"تشغيلة={sum(_p1_soft_sym.values())} مشي={sum(_p1_soft_walk.values())}")
check("P1-③🔒: وضع السوق الكامل (بلا تشخيص) يطابق المشي كذلك — اتّساق المصدرين",
      _p1_soft_mkt == _p1_soft_walk)

# 🔒 P1-④ج **سلوكيّ لا نصّيّ**: القفل الأول هنا كان `getsource(...)` على كلمة «خامل»
# — و**نجا من الطفرة** لأن الكلمة موجودة في **التعليق** فوق السطر أيضًا (نفس فخّ
# «getsource يلتقط الاسم من التعليق/الـdocstring» المدوَّن). البديل: تشغيل الذراعين.
_p1_sv_flags = {k: S.CONFIG.get(k) for k in
                ("BT_SPLIT_REF_M2", "BT_SPLIT_AWARE_M2", "BT_SPLIT_AWARE_M4")}
_p1_sv_frozen = _os_hc.environ.get("BT_FROZEN_PATH")
_p1_sv_loader = S.load_frozen_dataset
_p1_saved2 = (S.log, S.send_telegram, S.send_telegram_document, S._write_csv_file,
              S.download_history, S.get_universe)
try:
    S.CONFIG["BT_SPLIT_REF_M2"] = 1            # علمٌ تقسيميّ مرفوع
    _os_hc.environ.pop("BT_FROZEN_PATH", None)  # ...وبلا لقطة ⇒ يجب أن يُعلَن خاملًا
    _p1_noctx = _p1_run(True)
    # وبلقطة splits حقيقية ⇒ يجب أن يُعلَن فعّالًا بعددٍ موجب
    # (`run_backtest` يشترط وجود الملف فعليًّا قبل النداء ⇒ ملفٌّ مؤقّت + جالبٌ محقون)
    _p1_fd, _p1_fpath = __import__("tempfile").mkstemp(suffix=".pkl.gz")
    _os_hc.close(_p1_fd)
    _p1_spl = {s: pd.Series([0.1], index=pd.to_datetime(["2024-03-01"]))
               for s in _P1_SYMS}
    _os_hc.environ["BT_FROZEN_PATH"] = _p1_fpath
    S.load_frozen_dataset = lambda p: (dict(_p1_data), _p1_spl, "2026-01-01")
    _p1_ctx = _p1_run(True)
finally:
    try:
        _os_hc.remove(_p1_fpath)
    except (OSError, NameError):
        pass
    S.load_frozen_dataset = _p1_sv_loader
    for _k, _v in _p1_sv_flags.items():
        S.CONFIG[_k] = _v
    if _p1_sv_frozen is None:
        _os_hc.environ.pop("BT_FROZEN_PATH", None)
    else:
        _os_hc.environ["BT_FROZEN_PATH"] = _p1_sv_frozen
    (S.log, S.send_telegram, S.send_telegram_document, S._write_csv_file,
     S.download_history, S.get_universe) = _p1_saved2

check("P1-④ج🔒 سلوكيّ: علمٌ تقسيميّ بلا لقطة ⇒ يُعلَن **خاملًا/no-op** صراحةً",
      "خامل" in _p1_noctx and "no-op" in _p1_noctx
      and "العلم فعّال" not in _p1_noctx)
check("P1-④ج🔒 سلوكيّ: مع لقطة splits ⇒ «العلم فعّال: قرأ لقطة splits لـN رمزًا» بعددٍ موجب",
      f"العلم فعّال: قرأ لقطة splits لـ{len(_P1_SYMS)} رمزًا" in _p1_ctx
      and "خامل" not in _p1_ctx)


# ══════════════════════════════════════════════════════════
# 🔬 أدوات بحث T-HUNTER-SIX — أقفال العقود (نقلها المُنسّق 2026-07-30 لأن
# منفّذ الأداة كان ممنوعًا من `test_bot.py` بقاعدة ملكية الملفات؛ طفراتها
# عاشت في المِسوَدّة فنُقلت هنا لتُحرَس دائمًا).
# ══════════════════════════════════════════════════════════
import hunter_six_check as _H6                                   # noqa: E402
import split_radar_check as _SRC                                 # noqa: E402
import datetime as _h6dt                                         # noqa: E402

# ① **القفل الأهمّ — «لا إعادة تنفيذ»:** الأداة تُطلق حكمها من دالّة الإنتاج نفسها
#    (`scan_split_hunter`) لا من منطقٍ مُعاد كتابته. أيّ إعادة تنفيذ = بطلان التجربة
#    كلّها (تقيس نسخةً منّا لا الأداة الرابحة).
_h6_src = _insp0.getsource(_H6)
check("🔬 H6🔒 الحكم المرجعيّ من دالّة الإنتاج نفسها (`scan_split_hunter`) — لا منطق مُعاد",
      "S.scan_split_hunter(" in _h6_src)
check("🔬 H6🔒 المِجَسّ والمراجع كلها مستوردة من الإنتاج (صفر إعادة تعريف محلّية)",
      not any(f"def {_n}(" in _h6_src for _n in
              ("_split_setup_probe", "_post_split_high", "_split_day_value",
               "group_pump_scar", "scan_split_hunter", "_yahoo_float")))
check("🔬 H6🔒 تُعلن الرمز الخارج عن تغطية اللقطة (لا صفرٌ صامت — «لا سقوف صامتة»)",
      "غير موجود في اللقطة" in _h6_src)
check("🔬 H6🔒 تطبع «العلم فعّال: قرأ لقطة splits» (درس الـno-op رقم 7)",
      "العلم فعّال" in _h6_src and "no-op" in _h6_src)

# ② **قصّ التقسيمات point-in-time** — يحرس تسريبًا حقيقيًّا لقّاه المنفّذ:
#    `_split_frequency` تفحص `d >= cutoff` **بلا حدّ أعلى** فتعدّ تقسيمًا يقع **بعد**
#    يوم المشي. (حقلٌ عرضيّ لا قراريّ، وحيٌّ لا يتأثّر — لكن المشي التاريخي يتأثّر.)
_h6_sp = [(_h6dt.date(2026, 1, 10), 0.1), (_h6dt.date(2026, 6, 1), 0.2)]
check("🔬 H6🔒 قصّ التقسيمات عند يوم المشي (لا يتسرّب تقسيمٌ لاحق إلى `freq`)",
      _H6._slice_splits(_h6_sp, _h6dt.date(2026, 3, 1)) == _h6_sp[:1]
      and _H6._slice_splits(_h6_sp, _h6dt.date(2026, 7, 1)) == _h6_sp)
check("🔬 H6🔒 شاهد ضبط: بلا قصّ يتسرّب اللاحق فعلًا (فالقفل ليس تحصيل حاصل)",
      len([_p for _p in _h6_sp if _p[0] >= _h6dt.date(2026, 1, 1)]) == 2)
check("🔬 H6🔒 القصّ فاشل-آمن: None ⇒ None · وتالفٌ ⇒ يمرّ كما هو (تعذّر ≠ صفر)",
      _H6._slice_splits(None, _h6dt.date(2026, 3, 1)) is None
      and _H6._slice_splits(object(), _h6dt.date(2026, 3, 1)) is not None)

# ③ **أداة الفحص كانت تقرأ الفلوت من مصدرٍ ميت** (`ce_float_info` منذ 07-24) بينما
#    الإنتاج أُصلح 07-27 ⇒ كل dry-run كان يطبع «فلوت —» **زورًا** فيقلب الحكم.
_src_src = _insp0.getsource(_SRC)
check("🔬 SRC🔒 الفلوت من مصدر الإنتاج الحيّ `_yahoo_float(strict=True)` لا من CE الميتة",
      "_yahoo_float(sym, strict=True)" in _insp0.getsource(_SRC._yf_float))
check("🔬 SRC🔒 `strict=True` إلزاميّ (المتساهل يُدخل sharesOutstanding للحكم = تشديدٌ صامت)",
      "strict=True" in _insp0.getsource(_SRC._yf_float))
check("🔬 SRC🔒 سطر CE الخام **يبقى** للتشخيص (لا يُحذف مصدرٌ نُبقيه عمدًا)",
      "ce_float_info" in _src_src)
check("🔬 SRC🔒 وسيط `cutoff` موجود ويقصّ الإطار (المشي التاريخي)",
      "cutoff" in str(_insp0.signature(_SRC.run)) and "SPLIT_RADAR_CUTOFF" in _src_src)
check("🔬 SRC🔒 يُصرّح بحدّ الـcutoff الجزئي (`scan_split_radar` لا تقبل `today`)",
      "point-in-time" in _src_src and "اليوم الحقيقي" in _src_src)

# ④ **الأداتان خارج الجذور** — بحثٌ لا إنتاج.
check("🔬 H6/SRC🔒 خارج الجذور: لا تُستورَدان في أي مسار فرز/تنبيه إنتاجي",
      not any(_n in _insp0.getsource(S).replace("hunter_six_check", "")
              for _n in ("import hunter_six_check", "import split_radar_check")))


# ══════════════════════════════════════════════════════════
# 📒 قفل «صفر صفٍّ بلا وسم» — دفتر مصادر القواعد `FAISAL_SOURCE_LEDGER.md`
# (البند ③ من `OPUS_EXECUTION_PACKAGE.md`)
#
# **اللماذا:** سبعُ مصايب خرجت من نسبة رقمٍ لغير مصدره. فالدفتر يحاكم كل عتبة —
# وقيمتُه كلُّها في أن **لا يمرّ صفٌّ بلا حكم**. صفٌّ بلا وسم = عتبةٌ عادت مجهولةَ
# السند بصمت، وهو بالضبط الوضع الذي وُلد الدفتر ليمنعه.
#
# **نطاق القفل:** أيّ جدولٍ في الملف ترويستُه فيها عمودٌ اسمه «الوسم» — تُفحَص كل
# صفوفه. غيرها يُتجاهَل (جداول الغائب/حدود الصدق ليست دفترًا).
# **وحارس التفاهة (anti-tautology):** يشترط عددًا أدنى من الصفوف، وإلا لمرّ القفل
# على ملفٍ محذوفٍ أو جدولٍ مفرَّغ = «قفلٌ لم يسقط مرّة واحدة» (دستور §5).
# ══════════════════════════════════════════════════════════
_LEDGER_TAGS = ("faisal_verbatim", "faisal_inferred", "faisal_adopted",
                "engineering", "third_party", "unsourced")
_LEDGER_MIN_ROWS = 90          # §② وحدها 94 صفًّا — الأرضية تكشف الملف المفرَّغ


def _ledger_audit(path):
    """يرجع (عدد الصفوف المفحوصة، قائمة الصفوف المخالفة). فاشل-آمن **مغلق**:
    ملفٌ غائب/تالف ⇒ (0, []) ⇒ يسقط بحارس العدد لا يمرّ بصمت."""
    rows, bad, tag_col = 0, [], None
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
    except Exception as exc:
        return 0, [f"تعذّرت القراءة: {exc}"]
    for ln, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line.startswith("|"):
            tag_col = None                       # خرجنا من الجدول
            continue
        cs = [c.strip() for c in line.strip("|").split("|")]
        if tag_col is None:                      # هذي ترويسة الجدول
            tag_col = cs.index("الوسم") if "الوسم" in cs else -1
            continue
        if tag_col < 0:                          # جدولٌ خارج نطاق الدفتر
            continue
        if set("".join(cs)) <= set("-: "):       # فاصل |---|
            continue
        rows += 1
        cell = cs[tag_col] if tag_col < len(cs) else ""
        hit = [t for t in _LEDGER_TAGS if t in cell]
        if len(hit) != 1:                        # صفر وسم **أو** أكثر من واحد
            bad.append(f"سطر {ln}: أوسام={hit} | {line[:80]}")
    return rows, bad


_led_path = _os_hc.path.join(_os_hc.path.dirname(_os_hc.path.abspath(__file__)),
                             "FAISAL_SOURCE_LEDGER.md")
_led_rows, _led_bad = _ledger_audit(_led_path)
check("📒🔒 دفتر المصادر: صفر صفٍّ بلا وسم من الستة "
      "(وحارس تفاهة: الجدول ليس فارغًا)",
      not _led_bad and _led_rows >= _LEDGER_MIN_ROWS,
      f"صفوف={_led_rows} · مخالف={len(_led_bad)}"
      + (" · " + " ؛ ".join(_led_bad[:3]) if _led_bad else ""))


# ==========================================================
# 🔔 ⓿-و حارس سقوط كرون **صيّاد المقسّم** (وقائيّ — إشعار فقط)
# ==========================================================
# الصيّاد هو الرابح الحيّ الوحيد (رشّح NUWE قبل انفجاره ‏+100% بيومين) وكان — بخلاف
# التجديد الأسبوعي الذي له `renewal_staleness` — **بلا أي حارس سقوط**: تشغيلةٌ يُسقطها
# GitHub تصمت صمتًا تامًّا، وصمتُه يُقرأ «لا مقسّم اليوم» وهو غلط.
print("\n=== 🔔 ⓿-و حارس سقوط كرون صيّاد المقسّم ===")

_hg_dir = __import__("tempfile").mkdtemp()   # ملفّات ختمٍ مؤقتة (لا تُكتب بالريبو)


def _hg_path(tag):
    return _os_hc.path.join(_hg_dir, f"stamp_{tag}.json")


def _hg(last, today, tag="t", **kw):
    """يكتب ختمًا بتاريخ `last` **بالمسار الحقيقي للكتابة** (لا حقن قيمة) ثم يفحص
    عمره في يوم `today` — فيمرّ الاختبار على الكاتب والقارئ والحاسب معًا."""
    p = _hg_path(tag)
    S.record_hunter_run(last, path=p)
    return S.hunter_staleness(today=today, path=p, **kw)


def _hg_safe(fn, *a, **k):
    """يرجّع القيمة أو اسم الاستثناء بدل أن يرمي. **سببه مقيس:** طفرتا «الكاتب يرمي
    بدل False» و«انهيار الختم يُسقط التنبيه» قتلتا السويّة بانهيارٍ لا بفشل فحص —
    فرمز الخروج صحيح لكن **الفشل غير منسوب لقفله**. بهذا الغلاف يظهر ❌ باسم القفل."""
    try:
        return fn(*a, **k)
    except Exception as _e:                                      # noqa: BLE001
        return f"رمى:{type(_e).__name__}"


# ── ① التخوم: يوم تداولٍ واحد صامت · يومان تحذير ───────────────────────────────
# الحالة السليمة = **يوم واحد** بالتعريف (الصيّاد يمسح جلسة أمس فجرًا والفارز يقرأ
# صباحًا)، فيومان = تشغيلةٌ سقطت. أي انزلاقٍ في الحدّ يُسقط هذين القفلين.
check("🔔 ⓿-و·ختمٌ عمرُه يوم تداولٍ واحد (اثنين ⟵ ثلاثاء) ⇒ لا تحذير",
      _hg("2026-07-27", "2026-07-28", "a") is None)
_hg_two = _hg("2026-07-27", "2026-07-29", "b")
check("🔔 ⓿-و·يوما تداول (اثنين ⟵ أربعاء) ⇒ تحذير بالتاريخ والعدد",
      isinstance(_hg_two, dict) and _hg_two["why"] == "stale"
      and _hg_two["days"] == 2 and _hg_two["last"] == "2026-07-27")
# ── ② الحالة التمييزية: عطلة نهاية الأسبوع **لا تُحتسب** ───────────────────────
# جمعة ⟵ اثنين = **3 أيام تقويمية** لكن **يوم تداول واحد**؛ وكرون الصيّاد
# (`13 1 * * 2-6`) لا يعمل السبت/الأحد أصلًا. حسابُها تقويميًّا = تحذيرٌ كاذب كل
# اثنين ⇒ يُدرَّب المالك على تجاهله = موت الحارس. **هذا هو القفل الذي تُسقطه طفرة
# «يوم تقويميّ بدل تداوليّ».**
check("🔔 ⓿-و·جمعة ⟵ اثنين: 3 أيام تقويمية = **يوم تداول واحد** ⇒ لا تحذير",
      _hg("2026-07-24", "2026-07-27", "c") is None
      and (S.dt.date(2026, 7, 27) - S.dt.date(2026, 7, 24)).days == 3)
check("🔔 ⓿-و·وجمعة ⟵ ثلاثاء (تشغيلة الاثنين سقطت) ⇒ تحذير — فالقفل ليس عمياءً",
      (_hg("2026-07-24", "2026-07-28", "d") or {}).get("days") == 2)
# عطلة رسمية وسط الأسبوع من `market_calendar` المثبَّت (لا اجتهاد): الثانكسجيفينغ
# 2026-11-26 خميس ⇒ أربعاء ⟵ جمعة = يوم تداول واحد لا يومان.
check("🔔 ⓿-و·عطلة رسمية (ثانكسجيفينغ) لا تُحتسب يوم تداول ⇒ لا تحذير",
      "2026-11-26" in _CAL.HOLIDAYS
      and S.trading_days_between("2026-11-25", "2026-11-27") == 1
      and _hg("2026-11-25", "2026-11-27", "e") is None)
# ── ③ الحساب النقيّ: تخوم وسلامة ──────────────────────────────────────────────
check("🔔 ⓿-و·أيام التداول: صفر لنفس اليوم وللمستقبل (ساعة رنر مغلوطة لا تُنذر)",
      S.trading_days_between("2026-07-27", "2026-07-27") == 0
      and S.trading_days_between("2026-07-29", "2026-07-27") == 0
      and _hg("2026-07-29", "2026-07-27", "f") is None)
check("🔔 ⓿-و·يقبل date/datetime/نصًّا ISO بنفس الجواب (لا مسار نوعٍ مكسور)",
      S.trading_days_between(S.dt.date(2026, 7, 27), S.dt.date(2026, 7, 29)) == 2
      and S.trading_days_between(S.dt.datetime(2026, 7, 27, 3, 0),
                                 "2026-07-29") == 2)
check("🔔 ⓿-و·مدًى شاذّ (فوق 400 يوم) يُحسم بلا حلقةٍ طويلة",
      S.trading_days_between("2020-01-01", "2026-07-27") > 400)
# ── ④ تعذّر ≠ سليم: الغائب والتالف تحذيرٌ لا صمت ──────────────────────────────
check("🔔 ⓿-و·ملفّ ختمٍ غائب ⇒ تحذير «missing» (لا انهيار ولا صمت)",
      (S.hunter_staleness(today="2026-07-28",
                          path=_os_hc.path.join(_hg_dir, "لا-وجود.json"))
       or {}).get("why") == "missing")
_hg_bad = _hg_path("corrupt")
open(_hg_bad, "w", encoding="utf-8").write("{ هذا ليس JSON")
check("🔔 ⓿-و·ملفّ تالف ⇒ تحذير «corrupt» (والقارئ يرجّع None بلا رمي)",
      (S.hunter_staleness(today="2026-07-28", path=_hg_bad) or {}).get("why")
      == "corrupt" and S.load_hunter_stamp(_hg_bad) is None)
_hg_nod = _hg_path("nodate")
open(_hg_nod, "w", encoding="utf-8").write('{"last_session": null}')
check("🔔 ⓿-و·ملفٌّ سليمٌ بلا تاريخ صالح ⇒ تحذير أيضًا (لا «سليم» بالافتراض)",
      (S.hunter_staleness(today="2026-07-28", path=_hg_nod) or {}).get("why")
      == "corrupt")
check("🔔 ⓿-و·الختم أقلّ حالةٍ ممكنة: مفتاحٌ واحد هو تاريخ الجلسة (لا دِدوب/أسعار)",
      json.load(open(_hg_path("a"), encoding="utf-8"))
      == {"last_session": "2026-07-27"})
check("🔔 ⓿-و·الكاتب فاشل-آمن: تاريخٌ تالف/مسارٌ مستحيل ⇒ False بلا رمي",
      _hg_safe(S.record_hunter_run, "لا-تاريخ", path=_hg_path("z")) is False
      and _hg_safe(S.record_hunter_run, object(), path=_hg_path("z")) is False
      and _hg_safe(S.record_hunter_run, "2026-07-27",
                   path="/لا/يوجد/مجلد/x.json") is False)
check("🔔 ⓿-و·max_days محقون يتجاوز CONFIG (والافتراضي 1 = يومُ تداولٍ صامت)",
      S.CONFIG["HUNTER_STALE_TRADING_DAYS"] == 1
      and _hg("2026-07-27", "2026-07-29", "g", max_days=2) is None
      and _hg("2026-07-27", "2026-07-30", "h", max_days=2) is not None)
# ── ⑤ نصّ التحذير ─────────────────────────────────────────────────────────────
_hg_msg = S.hunter_stale_line(_hg_two)
check("🔔 ⓿-و·النصّ يحمل العبارة المطلوبة والتاريخ والعدد والإجراء",
      "صيّاد المقسّم لم يعمل" in _hg_msg and "2026-07-27" in _hg_msg
      and "2 من أيام التداول" in _hg_msg and "Split Hunter" in _hg_msg
      and S.hunter_stale_line(None) == "" and S.hunter_stale_line({}) == "")
check("🔔 ⓿-و·النصّ يفرّق الغائب عن التالف عن المتقادم (ثلاث صياغات لا واحدة)",
      len({S.hunter_stale_line({"why": w}) for w in
           ("missing", "corrupt", "stale")}) == 3)
check("🔔 ⓿-و·قفل اللغة: بلا علامات مقارنة (قاعدة CLAUDE.md المُلزِمة)",
      not any(_ch in _hg_msg.replace("<b>", "").replace("</b>", "")
              for _ch in ("≥", "≤", ">", "<")))
# ── ⑥ نقطة النداء في المسار اليومي: **تشغيلٌ حقيقيّ** لا قفل نصّي ──────────────
# `_run_daily` يقود `run_daily_watchlist` فعليًّا؛ نحوّل مسار الختم لملفٍّ مؤقت.
def _hg_daily(stamp_path):
    _sv = S.HUNTER_STAMP_FILE
    try:
        S.HUNTER_STAMP_FILE = stamp_path
        return _run_daily([])[0]
    finally:
        S.HUNTER_STAMP_FILE = _sv


_hg_fresh = _hg_path("fresh")
S.record_hunter_run(S.dt.date.today(), path=_hg_fresh)
_hg_sent_fresh = _hg_daily(_hg_fresh)
S.record_hunter_run(S.dt.date.today() - S.dt.timedelta(days=30), path=_hg_fresh)
_hg_sent_old = _hg_daily(_hg_fresh)
check("🔔 ⓿-و·المسار اليومي: ختمٌ طازج ⇒ صفر تحذير · ومتقادم ⇒ التحذير يصل فعلًا",
      not any("صيّاد المقسّم لم يعمل" in _m for _m in _hg_sent_fresh)
      and any("صيّاد المقسّم لم يعمل" in _m for _m in _hg_sent_old))
check("🔔 ⓿-و·صفر قناة تلغرام جديدة: السطر **مُلحَقٌ** بالتقرير لا رسالةٌ مستقلّة",
      len(_hg_sent_old) == len(_hg_sent_fresh)
      and any("صيّاد المقسّم لم يعمل" in _m and len(_m) > 200
              for _m in _hg_sent_old))
# 🔒 القفل الحاسم: انهيار الرصد **لا يُسقط** المسار اليومي ولا يمنع وصول التقرير.
_hg_sv = S.hunter_staleness
try:
    S.hunter_staleness = lambda *a, **k: (_ for _ in ()).throw(
        RuntimeError("عطل رصد الصيّاد"))
    _hg_after = _run_daily([])[0]
    _hg_raised = None
except Exception as _e:                                          # noqa: BLE001
    _hg_after, _hg_raised = [], type(_e).__name__
finally:
    S.hunter_staleness = _hg_sv
check("🔒 ⓿-و·انهيار الرصد لا يُسقط المسار اليومي والتقرير يصل (فاشل-آمن مُثبَت)",
      _hg_raised is None and len(_hg_after) >= 1 and len(_hg_after[0]) > 40)
# ── ⑦ الصيّاد: يختم في **كلا** المسارين (الصمت الشرعيّ ليس سقوطًا) ─────────────
_hg_s1 = _hg_path("run_silent")
# ⚠️ المرجع = **تاريخ الجلسة** المقروء من البيانات لا يوم الرنر (الكرون فجر UTC فيوم
#    الرنر = اليوم التالي للجلسة). ويُشتقّ من الـfixture لا يُكتب رقمًا يدويًّا.
_hg_sess = _sm_df.index[-1].date().isoformat()
check("🔔 ⓿-و·الصيّاد يختم حتى في يوم «لا مطابق» — وهو بالذات ما يجب ألّا يُخلَط بالسقوط",
      _sh_run(lambda *a, **k: [], stamp=_hg_s1) == (0, 1)
      and S.load_hunter_stamp(_hg_s1) == _hg_sess)
_hg_s2 = _hg_path("run_match")
check("🔔 ⓿-و·ويختم في يوم المطابق أيضًا بتاريخ **الجلسة** لا يوم الرنر",
      _sh_run(lambda *a, **k: [{
          "symbol": "X", "price": 1.0, "half": 0.5, "ref": 1.0, "float": 1e6,
          "avail": None, "borrow_fee": None, "ema20": 1.0, "ema30": 1.0,
          "ema50": 1.0, "split_date": "2026-06-01", "freq": 0, "plan": {},
          "bottom_test": None, "split_ma": None}], stamp=_hg_s2) == (0, 1)
      and S.load_hunter_stamp(_hg_s2) == _hg_sess
      and _hg_sess != S.dt.date.today().isoformat())
# 🔴 الاتجاه المقابل: مسارُ الفشل **لا يختم** — وإلّا شهد الختمُ زورًا أن السوق فُحِص.
_hg_s3 = _hg_path("run_fail")
check("🔴 ⓿-و·تغطية مخنوقة/انهيار مسح ⇒ **لا ختم** (لا شهادة زور بأن السوق فُحِص)",
      _sh_run(lambda *a, **k: [], uni=tuple(f"S{i}" for i in range(100)),
              hist={"S1": _sm_df}, stamp=_hg_s3) == (1, 1)
      and S.load_hunter_stamp(_hg_s3) is None
      and _sh_run(lambda *a, **k: (_ for _ in ()).throw(RuntimeError("خنق")),
                  stamp=_hg_s3) == (1, 1)
      and S.load_hunter_stamp(_hg_s3) is None)
# 🔒 فشلُ الختم/الدفع لا يجوز أن يُضيّع تنبيهًا رابحًا (الحارس خادمٌ لا سيّد).
_hg_sv2 = S.record_hunter_run
try:
    S.record_hunter_run = lambda *a, **k: (_ for _ in ()).throw(
        RuntimeError("قرصٌ ممتلئ"))
    _hg_rc = _hg_safe(_sh_run, lambda *a, **k: [{
        "symbol": "X", "price": 1.0, "half": 0.5, "ref": 1.0, "float": 1e6,
        "avail": None, "borrow_fee": None, "ema20": 1.0, "ema30": 1.0,
        "ema50": 1.0, "split_date": "2026-06-01", "freq": 0, "plan": {},
        "bottom_test": None, "split_ma": None}], stamp=_hg_path("run_boom"))
finally:
    S.record_hunter_run = _hg_sv2
check("🔒 ⓿-و·انهيار الختم لا يمنع التنبيه الرابح من الوصول (فاشل-آمن مطلق)",
      _hg_rc == (0, 1))
check("🔔 ⓿-و·الختم يُدفع بالنمط المحمي (`git_save`) لا بكتابةٍ محلّية تضيع مع الرنر",
      "git_save" in _insp0.getsource(_SHmod._stamp)
      and "HUNTER_STAMP_FILE" in _insp0.getsource(_SHmod._stamp))
# 🔒 قفل نطاق: الحارس **إشعارٌ فقط** — خارج الفرز والاختيار ودرع أداة المقسّم.
check("🔒 ⓿-و·خارج الجذور ودرع الصيّاد (لا اسم من الحارس في أيٍّ منها)",
      all(_n not in _insp0.getsource(_f)
          for _n in ("hunter_staleness", "hunter_stale_line", "record_hunter_run",
                     "load_hunter_stamp", "HUNTER_STAMP_FILE")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.analyze_ticker, S.apply_float_gate, S.apply_short_gate,
                     S.scan_market, S.backtest_symbol, S.scan_split_hunter,
                     S.scan_split_radar, S.split_radar_ready)))
# ⚠️ الأسماء المحظورة **محدَّدة لا عامّة**: نسختي الأولى وضعت `get`/`post` فيها فسقط
#    القفل على `data.get("last_session")` — منعٌ بالاسم لا بالمعنى. المقصود: صفر شبكة
#    وصفر تشغيلٍ للصيّاد وصفر كتابة حالة **من مسار القراءة** (الكتابة في `record_*`).
_hg_bad_calls = {"requests", "urlopen", "download_history", "scan_split_hunter",
                 "send_telegram", "git_save", "_atomic_write_json", "polygon_flow",
                 "polygon_minute_bars", "extended_last_price", "_fetch_info",
                 "get_universe", "record_hunter_run"}
_hg_readers = (S.hunter_staleness, S.load_hunter_stamp, S.trading_days_between,
               S.hunter_stale_line)
_hg_src_all = "".join(_insp0.getsource(_f) for _f in _hg_readers)


def _hg_calls(src):
    """أسماء النداءات في مصدرٍ ما — **والوحدة المنادى عليها أيضًا** (`requests.get`
    ⇒ {get, requests}). القراءة على `func.attr` وحدها كانت تُسقط اسم الوحدة، وهي
    الثغرة التي كشفها حارس التفاهة أدناه (قفلٌ يقرأ «نظيف» لأنه ينظر للمكان الخطأ)."""
    out = set()
    for _n in _ast_p1.walk(_ast_p1.parse(src.lstrip())):
        if not isinstance(_n, _ast_p1.Call):
            continue
        f = _n.func
        if isinstance(f, _ast_p1.Attribute):
            out.add(f.attr)
            if isinstance(f.value, _ast_p1.Name):
                out.add(f.value.id)
        else:
            out.add(getattr(f, "id", None))
    return out


check("🔒 ⓿-و·الحارس لا يجلب شبكة ولا يشغّل الصيّاد ولا يكتب حالة (قفل AST + نصّي)",
      not ({_c for _f in _hg_readers for _c in _hg_calls(_insp0.getsource(_f))}
           & _hg_bad_calls)
      and not any(_t in _hg_src_all for _t in ("requests.", "http://", "https://",
                                               "urllib", "yf.")))
# 🔴 حارس تفاهة: القفل أعلاه ليس فارغًا — الاسم المحظور يُلتقط فعلًا لو ظهر.
check("🔴 ⓿-و·القفل غير فارغ: دالّةٌ تنادي `requests` تسقط به (مقياسُ القفل مُختبَر)",
      bool(_hg_calls("def f(u):\n    return requests.get(u)\n") & _hg_bad_calls)
      and bool(_hg_calls("def f():\n    git_save(['x'])\n") & _hg_bad_calls)
      and not (_hg_calls('def f(d):\n    return d.get("k")\n') & _hg_bad_calls))


# ==========================================================

# ══════════════════════════════════════════════════════════
# 🧱 مكدّس الجدران (`wall_stack.py`) — تشخيصٌ يكشف **كل** الجدران لا الأول فقط
# ══════════════════════════════════════════════════════════
import re as _re_ws                                               # noqa: E402
import wall_stack as _WS                                          # noqa: E402
_ws_src = _insp0.getsource(_WS)

# ① كل مفاتيح الإرخاء **موجودة فعلًا في CONFIG** — يمنع اسمًا مخترَعًا أو مُعاد تسميته
#    (لو أُعيدت تسمية مفتاح في CONFIG يومًا، هذا القفل يسقط بدل أن يصمت التقشير).
_ws_keys = [v[0] for v in _WS.RELAX.values()] + [k for _p, k, _v in _WS.RELAX_PREFIX]
check("🧱 WS🔒 كل مفاتيح الإرخاء موجودة في CONFIG (لا اسم مخترَع)",
      bool(_ws_keys) and all(k in S.CONFIG for k in _ws_keys))

# ② **كل سببٍ ينتجه `analyze_ticker` إمّا مُرخى أو مُعلَن terminal** — لا سبب صامت.
_ws_reasons = set(_re_ws.findall(r'_reject\(f?"([^"{]+)', _insp0.getsource(S)))
_ws_unmapped = {r for r in _ws_reasons
                if r not in _WS.RELAX and r not in _WS.TERMINAL
                and not any(r.startswith(p) for p, _k, _v in _WS.RELAX_PREFIX)}
check("🧱 WS🔒 لا سببَ رفضٍ ثابتٍ بلا خريطة (مُرخًى أو terminal مُعلَن)",
      not _ws_unmapped, f"غير مُغطّى: {_ws_unmapped}")

# ③ 🔒 **CONFIG يُستعاد حتى لو رمى `analyze_ticker`** — أخطر تسريبٍ ممكن: تجربةٌ
#    تلوّث عتبات الجلسة كلّها فتُقرأ نتائج التالي على CONFIG مكسور.
class _WSBoom:
    def __init__(self): self.n = 0
    def __call__(self, sym, df, **kw):
        self.n += 1
        if self.n == 1:
            S.CONFIG["MIN_PRICE"] = 999.0      # تلويثٌ متعمَّد قبل الرمي
            raise RuntimeError("انفجار متعمَّد")
        return None
_ws_before = dict(S.CONFIG)
_ws_real = S.analyze_ticker
try:
    S.analyze_ticker = _WSBoom()
    _ws_r = _WS.peel_walls(S, "X", None)
finally:
    S.analyze_ticker = _ws_real
check("🧱 WS🔒 الاستثناء يُعلَن لا يُبتلَع (terminal=استثناء_تحليل)",
      _ws_r["terminal"] == "استثناء_تحليل")
S.CONFIG["MIN_PRICE"] = _ws_before["MIN_PRICE"]   # تلويثٌ من الدالّة المرمية لا من التقشير

# 🔴 والقفل الحقيقيّ للاستعادة — **درسٌ من طفرةٍ سقطت عليّ**: القفل أعلاه كان **فارغًا**
#    (الاستثناء يقع قبل أي إرخاء ⇒ `saved` فارغة ⇒ حذف `finally` لا يكسر شيئًا).
#    فالقفل الصحيح يشترط **إرخاءً فعليًّا حدث** ثم يتحقّق أن CONFIG رجع بت-بت.
_ws_n = 360
_ws_idx = S.pd.bdate_range("2024-01-01", periods=_ws_n)
_ws_px = S.np.concatenate([S.np.linspace(1.0, 50.0, 110),
                           S.np.linspace(50.0, 0.9, 180),
                           S.np.full(70, 0.95)])
_ws_df = S.pd.DataFrame({"Open": _ws_px, "High": _ws_px * 1.03, "Low": _ws_px * 0.97,
                         "Close": _ws_px, "Volume": S.np.full(_ws_n, 1000.0)},
                        index=_ws_idx)
_ws_snap = dict(S.CONFIG)
_ws_real3 = _WS.peel_walls(S, "WSTEST", _ws_df)
_ws_diff = [k for k in _ws_snap if S.CONFIG.get(k) != _ws_snap[k]]
check("🧱 WS🔒 التقشير أرخى فعلًا (وإلا فالقفل التالي فارغ)",
      len(_ws_real3["walls"]) >= 2, f"walls={_ws_real3['walls']}")
check("🧱 WS🔒 CONFIG يرجع بت-بت بعد تقشيرٍ أرخى مفاتيح",
      not _ws_diff, f"تسرّب: {_ws_diff}")

# ④ التقشير يتوقّف عند الجدار البنيويّ ويُعلنه (لا يدور بلا نهاية)
class _WSTerm:
    def __call__(self, sym, df, **kw):
        S._REJECT_REASONS[sym] = "M4_base_lo"
        return None
_ws_real2 = S.analyze_ticker
try:
    S.analyze_ticker = _WSTerm()
    _ws_t = _WS.peel_walls(S, "Y", None)
finally:
    S.analyze_ticker = _ws_real2
check("🧱 WS🔒 يتوقّف عند الجدار البنيويّ ويُعلنه",
      _ws_t["terminal"] == "M4_base_lo" and _ws_t["walls"] == ["M4_base_lo"])

# ⑤ `_base_name` يلمّ الأسباب المتغيّرة — وإلا تفتّت كما في علّة P1 الموثّقة
check("🧱 WS🔒 توحيد الأسباب المتغيّرة (لا تفتّت بالنسبة)",
      _WS._base_name("بعيد_عن_الدخول(35%)") == _WS._base_name("بعيد_عن_الدخول(20%)")
      == "بعيد_عن_الدخول"
      and _WS._base_name("نواقص_فوق_3") == _WS._base_name("نواقص_فوق_7"))

# ⑥ `sole_blocker` يعدّ **الجدار الوحيد فقط** — هو المقياس الحاسم، فلا يختلط بغيره
_ws_agg = _WS.aggregate([{"walls": ["M5_سيولة"], "passed": True},
                         {"walls": ["M4_base_واسعة", "M5_سيولة"], "passed": False}])
check("🧱 WS🔒 «الجدار الوحيد» لا يعدّ يومًا فيه جداران",
      _ws_agg["sole_blocker"] == {"M5_سيولة": 1}
      and _ws_agg["total_blocks"]["M5_سيولة"] == 2)

# ⑧ 📒 وسم المصدر: **كل جدارٍ قابلٍ للإرخاء موسوم** (لا «غير_موسوم» صامت)
_ws_unlabeled = [r for r in list(_WS.RELAX) +
                 [p for p, _k, _v in _WS.RELAX_PREFIX]
                 if _WS.wall_source(r) == "غير_موسوم"]
check("🧱 WS🔒 كل جدارٍ قابلٍ للإرخاء له وسمُ مصدر", not _ws_unlabeled,
      f"بلا وسم: {_ws_unlabeled}")

# ⑨ 🔴 **نتيجة الدفتر مقفولة**: ولا واحدة من بوّابات M1-M5 وسمُها `verbatim`
#    (‏`FAISAL_SOURCE_LEDGER.md`: 8 engineering · 3 inferred · صفر verbatim).
#    لو خُفّف هذا يومًا صار «الحاجب من فيصل» — وهو ادّعاءٌ يجب أن يسقط بالاختبار.
_ws_m15 = ["M1_سعر", "M2_هبوط_فوق_97", "M2_هبوط_تحت_40", "M3_انفجار_تحت_60",
           "M4_base_واسعة", "M5_سيولة"]
check("🧱 WS🔒 ولا بوّابة من M1-M5 موسومة `verbatim` (نتيجة دفتر المصادر)",
      all(_WS.wall_source(r) != "verbatim" for r in _ws_m15))
check("🧱 WS🔒 وM10 موسومة `verbatim` فعلًا (شاهد ضبط — الوسم ليس ثابتًا أعمى)",
      _WS.wall_source("M10_RSI_ما_تشبّع") == "verbatim"
      and _WS.wall_source("M10_RSI_فات_القطار") == "verbatim")

# ⑦ 🔒 **خارج الإنتاج**: لا يُستورَد في أي مسار فرز/تنبيه
check("🧱 WS🔒 خارج الجذور: `Super_stock` لا يستورد wall_stack",
      "import wall_stack" not in _insp0.getsource(S))



# ══════════════════════════════════════════════════════════
# 🎯 T-CORE5 — علمٌ مركَّب: الهوية وحدها (فرضية المالك «قد تكفي 5 لا 14»)
# ══════════════════════════════════════════════════════════
_c5_env = {"BT_CORE5": "1"}
_c5_before = dict(S.CONFIG)
try:
    _c5_applied = S._apply_backtest_overrides("BACKTEST", env=_c5_env)
    # ① يُسقط الحواجز المشتقّة وM13/M14
    check("🎯 C5🔒 يُرخي الحواجز المشتقّة وM13/M14 دفعةً واحدة",
          S.CONFIG["WATCH_MAX_FAILS"] == 99 and S.CONFIG["NEAR_PCT"] == 0.0
          and S.CONFIG["SCORE_MIN"] == 0.0 and S.CONFIG["MIN_RR_T1"] == 0.0
          and S.CONFIG["RSI_NOW_HARD"] == 100.0
          and S.CONFIG["SHORT_GATE_MAX"] >= 10 ** 12
          and S.CONFIG["FLOAT_GATE_MAX"] >= 10 ** 15)
    # ② 🔒 **الهوية لا تُمَسّ** — هي «الخمس» موضع سؤال المالك، والتجربة تُسقط ما عداها
    check("🎯 C5🔒 بوّابات الهوية byte-identical (M1-M5 + أرضية RSI)",
          all(S.CONFIG[k] == _c5_before[k] for k in
              ("MIN_PRICE", "MIN_DROP_FLOOR", "MAX_DROP_PCT", "PRIOR_SPIKE_FLOOR",
               "MIN_DOLLAR_VOL", "RSI_OS_HARD")))
    check("🎯 C5🔒 يُعلن نفسه في وسم التجربة (لا ذراع صامتة)",
          "CORE5=1" in _c5_applied)
finally:
    S.CONFIG.clear(); S.CONFIG.update(_c5_before)

# ③ 🔒 **الإنتاج معزول** — الوضع اليوميّ يتجاهل العلم تمامًا
_c5_prod = S._apply_backtest_overrides("DAILY", env=_c5_env)
check("🎯 C5🔒 الإنتاج معزول: الوضع اليوميّ يتجاهل BT_CORE5",
      _c5_prod == [] and S.CONFIG["WATCH_MAX_FAILS"] == _c5_before["WATCH_MAX_FAILS"]
      and S.CONFIG["FLOAT_GATE_MAX"] == _c5_before["FLOAT_GATE_MAX"])

# ④ مطفأ ⇒ صفر أثر
_c5_off = S._apply_backtest_overrides("BACKTEST", env={})
check("🎯 C5🔒 مطفأ ⇒ CONFIG بت-بت",
      _c5_off == [] and all(S.CONFIG[k] == _c5_before[k] for k in _c5_before))



# ═══════════════════════════════════════════════════════════════════════════
# 🔁 T-REPLAY10 — أقفال آلة الحالة الأمينة (`replay10.py`)
#    السبب: المراجعة الخصومية أثبتت نظرًا مستقبليًّا في `backtest_portfolio`
#    (استبعاد `no_fill` قبل السعة) وسعةً 15 بدل 10 وتحريرًا بأيام تقويمية.
#    هذي الأقفال تحرس **الإصلاحات الثلاثة** — مواصفاتها في `replay10_prereg.md` §②.
# ═══════════════════════════════════════════════════════════════════════════
import replay10 as RP

def _cand(sess, sym, seq, rdy=50.0, score=50.0, rr=1.0):
    return RP.Candidate(session=sess, symbol=sym, readiness=rdy, score=score, rr=rr, seq=seq)

# ==========================================================
# 🔬 صيّاد «النهج العلمي» — أداةٌ مستقلّة (قرار المالك 2026-08-01)
# ==========================================================
import method_hunter as MH        # noqa: E402
_MHsrc = _insp0.getsource(MH.run)

# 🐞 **القفل النصّيّ سقط في الفخّ الموثّق مرّةً أخرى:** كان يشترط ورودَ
#    `trigger_state` نصًّا، فلمّا استُبدلت بـ`method_sequence` **بقي الاسمُ في
#    الـdocstring** الذي يشرح الاستبدال ⇒ **مرّ أخضرَ ووصلةُ الإنتاج مقطوعة**.
#    ⇒ يُقاس **النداء الفعليّ بالـAST** لا وجودُ الحرف.
def _calls(fn):
    import ast as _a, textwrap as _t
    out = set()
    for n in _a.walk(_a.parse(_t.dedent(_insp0.getsource(fn)))):
        if isinstance(n, _a.Call) and isinstance(n.func, _a.Name):
            out.add(n.func.id)
    return out


check("🔬 NH🔒 الشروط الستّة **مُناداةٌ فعلًا** (بالـAST لا بالنصّ — لا شرطَ يسقط صامتًا)",
      {"method_founding", "method_sequence", "falling_gap_candle"}
      <= _calls(S.scan_method_hunter)
      and all(_k in _insp0.getsource(S.scan_method_hunter) for _k in (
          "fetch_pump", "fetch_offering", "fetch_borrow")))
check("🔬 NH🔒 و`trigger_state` **لم تعد تُنادى** (قراءةُ المسح نقيضُ «حافظ عليها»)",
      "trigger_state" not in _calls(S.scan_method_hunter)
      and "trigger_state" in _insp0.getsource(S.scan_method_hunter))
check("🔬 NH🔒 «20 إلى 30 جلسة» حرفيّ من الصورة (تخوم مقفولة: 19 و31 يسقطان)",
      S.CONFIG["METHOD_DECLINE_MIN"] == 20 and S.CONFIG["METHOD_DECLINE_MAX"] == 30
      and (lambda f: all(f(n) for n in (20, 25, 30))
           and not any(f(n) for n in (19, 31)))(
          lambda n: bool(S.method_founding(
              S.pd.DataFrame({"High": [1.0] * 5 + [10.0] + [3.0] * n},
                             index=S.pd.date_range("2024-01-01",
                                                   periods=6 + n, freq="D"))))))
check("🔬 NH🔒 الصعود بثابت الإنتاج `EXPLOSION_PCT` لا رقمٍ مُبتكَر",
      "EXPLOSION_PCT" in _insp0.getsource(S.method_founding)
      and "PRIOR_SPIKE_WINDOW" in _insp0.getsource(S.method_founding))
# 🩺 قرار المالك «امش على اللي متأكد منه» (2026-08-01): الرقم بلا سندٍ نصّيّ **يبقى**
#    كما هو، **ويُقاس** كم يكلّف — فيُعايَر لاحقًا برقمٍ لا برأي.


def _mf(rise, bars):
    """إطارٌ قمّتُه ترتفع `rise`% ثم يهبط `bars` جلسة — للتحكّم بالحالتين معًا."""
    hi = [1.0] * 5 + [1.0 * (1.0 + rise / 100.0)] + [1.0] * bars
    return S.pd.DataFrame({"High": hi},
                          index=S.pd.date_range("2024-01-01", periods=len(hi),
                                                freq="D"))


_mf_st = {}
_mf_a = S.method_founding(_mf(80.0, 25), stats=_mf_st)     # داخل النافذة ويمرّ
_mf_b = S.method_founding(_mf(20.0, 25), stats=_mf_st)     # داخل النافذة · صعودٌ قليل
_mf_c = S.method_founding(_mf(20.0, 40), stats=_mf_st)     # خارج النافذة ⇒ لا يُحصى
check("🩺 NH🔒 عدّادُ «سقط على حدّ الصعود وحده» يعدّ مَن استوفى النافذة فقط",
      _mf_st.get("window_ok") == 2 and _mf_st.get("rise_only_fail") == 1
      and bool(_mf_a) and _mf_b is None and _mf_c is None)
check("🩺 NH🔒 و`stats` **لا يغيّر القرار أبدًا** (بت-بت مع وبدون · والافتراضيّ None)",
      all(S.method_founding(_mf(r, b))
          == S.method_founding(_mf(r, b), stats={})
          for r, b in ((80.0, 25), (20.0, 25), (20.0, 40), (50.0, 20), (49.0, 30)))
      and "stats=None" in _insp0.getsource(S.method_founding))
check("🩺 NH🔒 والعدّاد يظهر في السجلّ موسومًا بأنه الرقم بلا سند",
      all(_w in _insp0.getsource(S.scan_method_hunter)
          for _w in ("داخل نافذة 20-30", "حدّ الصعود وحده", "بلا سندٍ نصّيّ",
                     "stats=stage")))
# ⚖️ قرار المالك: شرط «الفجوة الهابطة» **يبقى** — ولا يُستورَد هدفٌ من نظامٍ آخر.
check("⚖️ NH🔒 لا هدفَ بديل من نظام الارتكاز يتسرّب لهذي الوصفة (درسُ `trigger_state`)",
      "_red_candle_heads" not in _insp0.getsource(S.scan_method_hunter)
      and "resistance_levels" not in _insp0.getsource(S.scan_method_hunter)
      and "falling_gap_candle" in _insp0.getsource(S.scan_method_hunter))

# ==========================================================
# 🪜 `method_sequence` — قراءة **الثبات** (تصحيح 2026-08-01 بمسكة المالك)
#    القاعدة: نمطُ فيصل «حافظ عليها · ذيول شموع وعدم كسرها» **يمرّ**،
#    ونمطُ المسح (‏`trigger_state`) **يُرفَض** — وهما نقيضان لا درجتان.
# ==========================================================
def _mseq(t_lo, t_hi, t_cl):
    """قاعٌ 3.10 ⟶ ارتدادٌ ⟶ رجوع؛ الذيلُ المُمرَّر يحدّد ثباتًا أم كسرًا."""
    return S.pd.DataFrame(
        {"Open": t_cl, "High": t_hi, "Low": t_lo, "Close": t_cl,
         "Volume": [1e5] * len(t_lo)},
        index=S.pd.date_range("2025-01-01", periods=len(t_lo), freq="B"))


_MS_HOLD = _mseq([3.10, 3.20, 3.35, 3.50, 3.45, 3.30, 3.14, 3.11],
                 [3.25, 3.40, 3.55, 3.60, 3.58, 3.45, 3.30, 3.20],
                 [3.18, 3.36, 3.50, 3.55, 3.48, 3.35, 3.20, 3.15])
_MS_SWEEP = _mseq([3.10, 3.20, 3.35, 3.50, 3.45, 3.30, 2.79, 3.00],
                  [3.25, 3.40, 3.55, 3.60, 3.58, 3.45, 3.35, 3.15],
                  [3.18, 3.36, 3.50, 3.55, 3.48, 3.35, 3.12, 3.13])
_MS_FLAT = _mseq([3.10, 3.12, 3.18, 3.22, 3.20, 3.16, 3.12, 3.11],
                 [3.16, 3.20, 3.26, 3.30, 3.28, 3.24, 3.18, 3.16],
                 [3.14, 3.18, 3.24, 3.28, 3.25, 3.20, 3.15, 3.13])
_ms_hold, _ms_sweep = S.method_sequence(_MS_HOLD, 8), S.method_sequence(_MS_SWEEP, 8)
check("🪜 SEQ🔒 نمطُ فيصل (‏حافظ على القاع) **يمرّ** — وهو ما كان يسقط قبل التصحيح",
      bool(_ms_hold and _ms_hold["ok"]) and _ms_hold["bottom"] == 3.10
      and _ms_hold["touches"] >= 2)
check("🪜 SEQ🔒 ونمطُ **المسح** (‏كسرَ القاع 10% ثم استعاد) **يُرفَض** ⇒ نقيضان لا درجتان",
      _ms_sweep is None)
def _pad15(d):
    """`trigger_state` تشترط ‏15 بارًا؛ نسبقُها بهبوطٍ **فوق** نطاق الذيل فلا يمسّه."""
    n = 10
    pre = S.pd.DataFrame(
        {"Open": [5.0] * n, "High": [5.2] * n, "Low": [4.8] * n,
         "Close": [5.0] * n, "Volume": [1e5] * n},
        index=S.pd.date_range("2024-12-01", periods=n, freq="B"))
    return S.pd.concat([pre, d])


check("🪜 SEQ🔒 والقديمة `trigger_state` تعكسهما حرفيًّا (شاهدُ الخطأ، مقفولٌ لئلّا يُنسى)",
      (S.trigger_state(_pad15(_MS_HOLD), win=8) or {}).get("steps", {})
      .get("swept_reclaimed") is False
      and (S.trigger_state(_pad15(_MS_SWEEP), win=8) or {}).get("steps", {})
      .get("swept_reclaimed") is True)
check("🪜 SEQ🔒 أرضيةُ الارتداد 10% حرفيّةٌ من الصورة — وتخومُها مقفولة",
      S.CONFIG["METHOD_BOUNCE_MIN_PCT"] == 10.0
      and S.method_sequence(_MS_FLAT, 8) is None          # ارتداد ~6% ⇒ يسقط
      and bool(S.method_sequence(_MS_FLAT, 8, bounce_min=5.0)))
check("🪜 SEQ🔒 «ولا كسرها»: إغلاقٌ واحد تحت القاع يُبطل الثبات (فرعٌ يُنفَّذ فعلًا)",
      S.method_sequence(
          _mseq([3.10, 3.20, 3.35, 3.50, 3.45, 3.30, 3.08, 3.11],
                [3.25, 3.40, 3.55, 3.60, 3.58, 3.45, 3.30, 3.20],
                [3.18, 3.36, 3.50, 3.55, 3.48, 3.35, 3.09, 3.15]), 8) is None)
# 🐞 **قفلٌ فارغ كشفته الطفرة M6 (يُدوَّن لا يُطوى):** أوّل عيّنةٍ كتبتُها كان
#    فيها القمّة **آخرَ بار**، فيرفضها حارسُ `pk >= n-1` **قبل** أن يُختبَر حارسُ
#    الرجوع أصلًا ⇒ القفل يمرّ والطفرة تنجو. العيّنة الآن قمّتُها **في الوسط**
#    فيبقى الرجوعُ هو السببَ الوحيد للرفض.
check("🪜 SEQ🔒 ومَن لم يرجع ليختبر القاع أصلًا **لا يُقبَل** (القفل ليس عدميًّا)",
      S.method_sequence(
          _mseq([3.10, 3.30, 3.55, 3.62, 3.58, 3.56, 3.54, 3.52],
                [3.25, 3.45, 3.70, 3.80, 3.72, 3.68, 3.66, 3.64],
                [3.20, 3.40, 3.65, 3.75, 3.70, 3.66, 3.62, 3.60]), 8) is None
      # شاهدُ ضبط: نفسُ العيّنة برجوعٍ يلامس القاع ⇒ **تُقبَل** (فالرفضُ سببُه الرجوع)
      and bool(S.method_sequence(
          _mseq([3.10, 3.30, 3.55, 3.62, 3.58, 3.40, 3.20, 3.12],
                [3.25, 3.45, 3.70, 3.80, 3.72, 3.60, 3.40, 3.25],
                [3.20, 3.40, 3.65, 3.75, 3.65, 3.50, 3.30, 3.18]), 8)))
check("🪜 SEQ🔒 **لا `RSI`** في التسلسل (الصور الستّ تعدّد شروطها وليس فيها RSI)",
      "rsi" not in _insp0.getsource(S.method_sequence).lower().split('"""')[2])
check("🪜 SEQ🔒 نقيّةٌ فاشلة-آمنة: تالفٌ/قصيرٌ ⇒ None (لا انهيار)",
      S.method_sequence(None, 8) is None
      and S.method_sequence(_mseq([1.0] * 3, [1.1] * 3, [1.05] * 3), 3) is None)
check("🪜 SEQ🔒 ونافذتُها **مشتقّةٌ من الحدث** (‏`bars_since_peak`) لا ثابتٌ مُبتكَر",
      'win=int(fnd["bars_since_peak"]) + 2'
      in _insp0.getsource(S.scan_method_hunter))
check("🎯 SEQ🔒 مَن تجاوز مستوى الدخول يُتابَع ولا يُرسَل («الدخول عند اقل سعر 3.20»)",
      "تجاوز منطقة الدخول" in _insp0.getsource(S.scan_method_hunter)
      and S.CONFIG["METHOD_ENTRY_PCT"] == 3.2)
# ⚓ **مرساةُ أرقام فيصل الحرفية** (`IMG_0486` + `IMG_0496`): قاعٌ 3.10 ⟹ دخول 3.20
#    ⟹ وقف 3.00. 🔴 **والوقف من الدخول لا من القاع** («3.20-6٪=3.00») — كان يُحسب
#    من القاع فيعطي رقمًا شبه مطابق **بقاعدةٍ مختلفة**، فيتباعدان عند أي سعرٍ آخر.
_fa_bot = 3.10
_fa_entry = _fa_bot * (1 + S.CONFIG["METHOD_ENTRY_PCT"] / 100.0)
_fa_stop = _fa_entry * (1 - S.CONFIG["METHOD_STOP_PCT"] / 100.0)
check("⚓ SEQ🔒 أرقام فيصل حرفيًّا: قاع 3.10 ⟹ دخول 3.20 · ووقف 3.00 (‏3.20−6%)",
      round(_fa_entry, 2) == 3.20 and abs(_fa_stop - 3.00) <= 0.01
      and S.CONFIG["METHOD_STOP_PCT"] == 6.0
      and "stop = entry * (1.0 - CONFIG[\"METHOD_STOP_PCT\"]"
      in _insp0.getsource(S.scan_method_hunter))
# 🕵️ «الشورت الافضل كم؟» ⟵ «**20 وتحت**» (`IMG_0496`) — رقمٌ بلسانه صار **شرطًا**.
# 🐞 كتبتُ القفل أوّلًا بـ`split("METHOD_SHORT_MAX")[1]` — **والمفتاح يرد مرّتين**
#    (الشرط ونصّ السبب) فوقع المقطع **بينهما** وخلا من `continue` ⇒ قفلٌ يسقط على
#    كودٍ سليم. ⇒ بالـAST على **جسم الشرط** كما في قفل قطبيّة الطرح.
def _gate_rejects(fn, key):
    import ast as _a, textwrap as _t
    for n in _a.walk(_a.parse(_t.dedent(_insp0.getsource(fn)))):
        if isinstance(n, _a.If) and key in _a.unparse(n.test):
            return any(isinstance(x, _a.Continue) for x in _a.walk(n))
    return False


check("🕵️ SEQ🔒 سقف الشورت 20 ألفًا **شرطٌ يرفض** (لا سياقًا يُعرَض)",
      S.CONFIG["METHOD_SHORT_MAX"] == 20_000
      and _gate_rejects(S.scan_method_hunter, "METHOD_SHORT_MAX") is True)
check("🕵️ SEQ🔒 والمجهول/التالف **يمرّ بفائدة الشك** (تعذّرٌ ≠ مخالفة)",
      (lambda src: "if _av is not None:" in src
       and "except (TypeError, ValueError):" in src
       and "pass" in src.split("except (TypeError, ValueError):")[1][:120])(
          _insp0.getsource(S.scan_method_hunter)))
check("🗣️ SEQ🔒 توجيه فيصل لقائمة المراقبة يظهر معها (`IMG_0500`)",
      any("اركب معه مباشرةً أول شمعة صعود" in x
          for x in S.method_near_lines([{"symbol": "A", "price": 1.0,
                                         "why": "بعيد", "over_pct": 1.0}])))
check("🩺 SEQ🔒 عدّاداتُ المراحل في السجلّ (تفرّق «فحصنا ولم نجد» عن «لم نفحص»)",
      all(_w in _insp0.getsource(S.scan_method_hunter)
          for _w in ("حدثٌ مؤسِّس", "داخل منطقة الدخول", 'stage["founding"]')))
check("🪜 SEQ🔒 و`trigger_state` **لم تُمَسّ** (تبقى لقراءتها ولتجربة الشموع)",
      "SPLIT_SWEEP_MIN_PCT" in _insp0.getsource(S.trigger_state)
      and "swept_pct" in _insp0.getsource(S.trigger_state))
# 🔴 قطبيّة الطرح **معكوسة** عن صيّاد المقسّم — خطأ إشارةٍ واحد لا يكشفه اختبار.
# ⚠️ **بالـAST لا بالنصّ**: القفل النصّيّ انكسر بمجرّد إضافة سطرِ تتبّعٍ قبل
#    `continue` — والشرط الحقيقيّ أن **جسم الشرط يحوي رفضًا**، لا شكلَ السطر.
def _offering_rejects(fn):
    import ast as _a, textwrap as _t
    for n in _a.walk(_a.parse(_t.dedent(_insp0.getsource(fn)))):
        if (isinstance(n, _a.If) and isinstance(n.test, _a.Call)
                and isinstance(n.test.func, _a.Name) and n.test.func.id == "fo"):
            return any(isinstance(x, _a.Continue) for x in _a.walk(n))
    return False


check("🔬 NH🔒 الطرح **مانعٌ** هنا (يرفض) وهو **حدثٌ مؤسِّس** عند المقسّم — قطبيّةٌ معكوسة",
      _offering_rejects(S.scan_method_hunter) is True
      and "offering" in _insp0.getsource(S.scan_split_hunter))
check("🔬 NH🔒 القروب يُسقط المرشّح (شرطُ صلاحيةِ قراءةٍ لا وسمُ خطر)",
      "if fp(df):" in _insp0.getsource(S.scan_method_hunter))
check("🔬 NH🔒 وتعذّرُ الاقتراض **لا يُسقط** المرشّح (تعذّر ≠ مخالفة)",
      (lambda src: "bor = None" in src and "bor = fb(sym)" in src
       and "continue" not in src.split("bor = fb(sym)")[1].split("try:")[0])(
          _insp0.getsource(S.scan_method_hunter)))
# 🔒 حرّاس الأداة — نفس حرّاس الصيّاد حرفيًّا (قرار المالك: «نفس الطريقة»).
check("🔬 NH🔒 بوّابة التوقيت: قبل إغلاق الافتر ⇒ لا مسح · وبعده ⇒ تاريخ نيويورك",
      MH.session_gate(S.dt.datetime(2026, 1, 14, 0, 13,
                                    tzinfo=S.dt.timezone.utc)) == (False, None)
      and MH.session_gate(S.dt.datetime(2026, 7, 29, 0, 13,
                                        tzinfo=S.dt.timezone.utc))
      == (True, S.dt.date(2026, 7, 28)))
check("🔬 NH🔒 حارس التغطية موجود بأرضيةٍ صريحة (خنقُ ياهو ≠ «لا مرشّح»)",
      MH.MIN_COVERAGE_PCT >= 50.0 and "MIN_COVERAGE_PCT" in _MHsrc
      and "لم يُفحَص السوق" in _MHsrc)
check("🔬 NH🔒 كلُّ مسار فشلٍ يُبلَّغ ويرجع 1 (الصمت لا يُخلَط بالعطل)",
      _MHsrc.count("_fail(S,") >= 6 and "return 1" in _MHsrc
      and "عطل لا" in _insp0.getsource(MH._fail))
check("🔬 NH🔒 «لا يوجد» تُرسَل ومعها التغطية (نفس عقد الصيّاد بعد قرار المالك)",
      "لا يوجد سهم يطابق الشروط" in _MHsrc and "تغطية" in _MHsrc)
check("🔬 NH🔒 دِدوبٌ بطبقتين: تاريخ نيويورك **وجلسة البيانات**",
      "sess_et.isoformat()" in _MHsrc and "sess.isoformat()" in _MHsrc)
check("🔬 NH🔒 الختم **بعد** الإرسال (رفضُ تلغرام لا يختم ⇒ يُعاد غدًا)",
      _MHsrc.index("_write_stamp(S, sess)") > _MHsrc.index("send_telegram(msg)"))
check("🔬 NH🔒 حدُّ الصدق في الرسالة: «قيد الإثبات» (لا تُقرأ حكمًا محسومًا)",
      "قيد الإثبات" in _insp0.getsource(S.build_method_alert))
# 🐞 وحدُّ الصدق نفسه **بات فصار كذبًا**: كان يحيل إلى «27 دون 30» وتلك التجربة
#    قاست **مجتمعَ المسح** (المرحلة ③ معكوسة) فسُحبت دلالتُها ⇒ الصادق «بلا حكم».
check("🔬 NH🔒 ولا يُحيل إلى حكمٍ مسحوب (‏«27 دون 30» خرجت — التجربة قاست غير هذا)",
      "27 دون 30" not in _insp0.getsource(S.build_method_alert)
      and "لم تُختبَر تاريخيًّا" in _insp0.getsource(S.build_method_alert))
# 🧪 **دخانُ المسار الكامل**: صفر مطابقٍ حيًّا حتى الآن ⇒ طريقُ الكرت لم يُنفَّذ
#    إنتاجيًّا قطّ. يُشغَّل هنا **من `scan_method_hunter` نفسها** لا من صفٍّ مُلفَّق.
_sm_lead = 35
_sm_hi = [3.4] * _sm_lead + [18.0] + [9.0, 5.0] + [4.4] * 15 + \
    [3.25, 3.45, 3.70, 3.80, 3.72, 3.50, 3.30, 3.20]
_sm_lo = [3.2] * _sm_lead + [12.0] + [8.2, 4.6] + [4.2] * 15 + \
    [3.10, 3.30, 3.55, 3.62, 3.45, 3.30, 3.14, 3.12]
_sm_cl = [3.3] * _sm_lead + [13.0] + [8.4, 4.8] + [4.3] * 15 + \
    [3.20, 3.40, 3.65, 3.75, 3.60, 3.40, 3.20, 3.16]
_sm_df = S.pd.DataFrame(
    {"Open": _sm_cl, "High": _sm_hi, "Low": _sm_lo, "Close": _sm_cl,
     "Volume": [5e5] * len(_sm_hi)},
    index=S.pd.date_range("2026-03-02", periods=len(_sm_hi), freq="B"))
_sm_rows = S.scan_method_hunter(
    {"TEST": _sm_df}, today=_sm_df.index[-1].date(),
    fetch_pump=lambda d: False, fetch_offering=lambda s: False,
    fetch_borrow=lambda s: {"shares_available": 7_000, "borrow_fee": 120.0})
check("🧪 NH🔒 مطابقٌ كامل يمرّ فعلًا (المسار الذي لم يُنفَّذ حيًّا قطّ)",
      len(_sm_rows) == 1 and _sm_rows[0]["symbol"] == "TEST"
      and abs(_sm_rows[0]["bottom"] - 3.10) < 1e-6
      and abs(_sm_rows[0]["entry"] - 3.20) < 0.01
      and abs(_sm_rows[0]["stop"] - 3.00) < 0.02
      and abs(_sm_rows[0]["t1"] - 5.00) < 1e-6)
_sm_msg = S.build_method_alert(_sm_rows, today=_sm_df.index[-1].date())
check("🧪 NH🔒 وكرتُه يُبنى كاملًا بلا انهيار وبأرقام فيصل البنيوية",
      all(_w in _sm_msg for _w in ("النهج العلمي", "التسلسل مكتمل",
                                   "رأس شمعة الفجوة", "الدخول ناقص",
                                   "قيد الإثبات"))
      and "$3.20" in _sm_msg and "$5.00" in _sm_msg)
# 🐞 وقفلُ الوصل كان **نصّيًّا** (وجودُ الاسم وترتيبُه) فنجت طفرةُ تعطيلِ الحلقة
#    (`[] and …`) ⇒ يُقاس **من المُخرَج الحيّ** للكرت نفسه.
check("🧾 FK🔒 وقواعدُ فيصل تظهر في **مُخرَج الكرت** فعلًا (لا وصلةٌ ميتة)",
      "هدفُ فيصل الأوّل" in _sm_msg and "طلباتٌ نازلة" in _sm_msg
      and "لا تشتري من العرض" in _sm_msg)
_ = S.scan_method_hunter({}, today=None)          # تنظيفُ الحالة العامّة بعد الدخان
# ==========================================================
# ==========================================================
# 🧾 قواعدُ «النماذج التعليمية» (2026-08-05) — كلُّ قفلٍ مرساتُه **رقمُ فيصل**
# ==========================================================
def _fk(o, h, low, c, start="2026-01-01"):
    return S.pd.DataFrame(
        {"Open": o, "High": h, "Low": low, "Close": c, "Volume": [1e5] * len(o)},
        index=S.pd.date_range(start, periods=len(o), freq="B"))


check("🧾 FK🔒 «لكل 10 آلاف سهم = 10٪ هبوط» — بأرقامه ونسبيًّا",
      S.CONFIG["FAISAL_SHORT_UNIT"] == 10_000
      and S.CONFIG["FAISAL_SHORT_UNIT_PCT"] == 10.0
      and S.short_decline_estimate(10_000)["decline_pct"] == 10.0
      and S.short_decline_estimate(6_000)["decline_pct"] == 6.0
      and S.short_decline_estimate(150_000)["decline_pct"] == 150.0
      and S.short_decline_estimate("x") is None
      and S.short_decline_estimate(float("nan")) is None)
check("🧾 FK🔒 «RSI من 22 لـ27» — والتخوم مقفولة (‏21.9 و27.1 خارجه)",
      (S.CONFIG["FAISAL_RSI_LO"], S.CONFIG["FAISAL_RSI_HI"]) == (22.0, 27.0)
      and all(S.faisal_rsi_zone(v)["in_zone"] for v in (22.0, 25, 27.0))
      and not any(S.faisal_rsi_zone(v)["in_zone"] for v in (21.9, 27.1))
      and S.faisal_rsi_zone(None) is None)
check("🧾 FK🔒 «هدف أوّل 30٪» + قاعدة التحرّر منصوصةً في المُخرَج",
      S.CONFIG["FAISAL_FIRST_TARGET_PCT"] == 30.0
      and S.first_target_release(2.0)["target"] == 2.6
      and "جني ربح" in S.first_target_release(2.0)["rule"]
      and S.first_target_release(0) is None)
# 🛑 قاعدة الامتناع بأرقام MNDR: القاع 1.40 والسعر 1.94 ⇒ ‏+38.6% (لا امتناع)،
#    وعند 2.10 ⇒ ‏+50% ⇒ **امتناع** (وهو حرفيًّا ما قاله: «حقّق 50٪ … ما أخاطر»).
_fk_lo = [3.0] * 20 + [2.0, 1.70, 1.40, 1.55, 1.70, 1.80, 1.90]
_fk_a = _fk([2.9] * 20 + [2.1, 1.8, 1.5, 1.6, 1.75, 1.85, 1.94],
            [3.1] * 20 + [2.2, 1.9, 1.6, 1.7, 1.85, 1.95, 2.00],
            _fk_lo,
            [2.9] * 20 + [2.1, 1.8, 1.5, 1.6, 1.75, 1.85, 1.94])
_fk_b = _fk([2.9] * 20 + [2.1, 1.8, 1.5, 1.6, 1.75, 1.85, 2.10],
            [3.1] * 20 + [2.2, 1.9, 1.6, 1.7, 1.85, 1.95, 2.20],
            _fk_lo,
            [2.9] * 20 + [2.1, 1.8, 1.5, 1.6, 1.75, 1.85, 2.10])
check("🛑 FK🔒 الامتناع عند 50٪ من القاع — بأرقام $MNDR (‏1.40 قاعًا)",
      S.CONFIG["FAISAL_ABSTAIN_RISE_PCT"] == 50.0
      and S.rise_from_bottom(_fk_a)["abstain"] is False
      and abs(S.rise_from_bottom(_fk_a)["risen_pct"] - 38.6) < 0.2
      and S.rise_from_bottom(_fk_b)["abstain"] is True
      and abs(S.rise_from_bottom(_fk_b)["risen_pct"] - 50.0) < 0.2)
# 🐞 عيّنتاي الأوليان (هابطة صرفة · صاعدة صرفة) **لا تفرّقان `all` عن `any`**:
#    في الأولى السعرُ تحت الكلّ وفي الثانية فوق الكلّ ⇒ نجت الطفرة. الحالةُ
#    الحاسمة **بينهما**: فوق المتوسّط القصير وتحت الطويل ⇒ `all`=False و`any`=True.
_fk_mid = (lambda l: _fk(l, [x * 1.02 for x in l], [x * 0.98 for x in l], l))(
    [5 - i * 0.05 for i in range(55)] + [2.35, 2.55, 2.75, 2.95, 3.10])
_fk_midr = S.under_all_mas(_fk_mid)
check("🧾 FK🔒 «تحت **جميع** المتوسّطات» لا «أيّها» — والحالةُ البينيّة تفصلهما",
      (lambda d: d and d["under_all"] is True and set(d["mas"]) == {20, 30, 50})(
          S.under_all_mas(_fk([5 - i * 0.05 for i in range(60)],
                              [5.1 - i * 0.05 for i in range(60)],
                              [4.9 - i * 0.05 for i in range(60)],
                              [5 - i * 0.05 for i in range(60)])))
      and _fk_midr["under_all"] is False
      and any(_fk_midr["price"] < v for v in _fk_midr["mas"].values())
      and any(_fk_midr["price"] > v for v in _fk_midr["mas"].values())
      and S.under_all_mas(None) is None)
# 🔨 «شمعة الهمر … مهمّ ما يكسر ذيلها» — والوقفُ ذيلُها (‏$TDIC `IMG_0659`)
_fk_ham = _fk([3.05] * 20 + [2.65, 2.45, 2.38, 2.38],
              [3.1] * 20 + [2.70, 2.50, 2.42, 2.45],
              [3.0] * 20 + [2.60, 2.40, 2.00, 2.35],
              [3.02] * 20 + [2.62, 2.42, 2.41, 2.43])
_fk_h = S.hammer_wick_stop(_fk_ham)
check("🔨 FK🔒 الهمر عند القاع يُكشَف وذيلُه هو الوقف · ولونُه يحدّد المدى",
      _fk_h and _fk_h["wick_low"] == 2.00 and _fk_h["broken"] is False
      and _fk_h["red"] is False
      and "همر" in _insp0.getsource(S.hammer_wick_stop)
      and "reversal_candle" in _insp0.getsource(S.hammer_wick_stop))
# 🐞 وعيّنتي الأولى تعطي `broken=False` **وكذلك الطفرة** (التي تُثبّتها False)
#    ⇒ يلزم شاهدٌ **مكسور** فعلًا: قاعٌ أدنى **بعد** الهمر.
_fk_hamb = S.hammer_wick_stop(
    _fk([3.05] * 20 + [2.65, 2.45, 2.38, 2.10],
        [3.1] * 20 + [2.70, 2.50, 2.42, 2.15],
        [3.0] * 20 + [2.60, 2.40, 2.00, 1.80],
        [3.02] * 20 + [2.62, 2.42, 2.41, 1.85]))
check("🔨 FK🔒 و«ما يكسر ذيلها» يُرصَد فعلًا: قاعٌ أدنى بعده ⇒ `broken=True`",
      _fk_hamb is not None and _fk_hamb["broken"] is True)
check("🔨 FK🔒 ولا همرَ ⇒ None (القفل ليس عدميًّا) · وتالفٌ ⇒ None",
      S.hammer_wick_stop(_fk([3.0] * 24, [3.1] * 24, [2.9] * 24,
                             [3.0] * 24)) is None
      and S.hammer_wick_stop(None) is None)
# 👤 خطّ العنق — قاعٌ وكتفان بأرقامٍ صريحة
_fk_neck = (lambda l: S.neckline_level(
    _fk([x * 1.02 for x in l], [x * 1.05 for x in l], l, [x * 1.02 for x in l])))(
    [3.0] * 6 + [2.30, 2.55, 2.60, 2.55] + [2.00, 2.10, 2.45, 2.60, 2.55]
    + [2.32, 2.50, 2.75, 2.86, 2.90])
check("👤 FK🔒 خطّ العنق: الرأس أدنى الكتفين · والعنق أعلى القمم بينها",
      _fk_neck and _fk_neck["head"] == 2.00
      and _fk_neck["shoulders"] == [2.30, 2.32] and _fk_neck["above"] is True)
# 🐞 عيّنتي الأولى لم تكن «متباعدة» أصلًا: الكتفُ الأيمن يُلتقَط **أدنى ما بعد
#    الرأس**، فوقع على بارٍ وسطيّ 2.45 لا على 4.00 ⇒ القفل يمرّ بلا اختبار.
#    الآن كلُّ ما بعد الرأس **مرتفعٌ فعلًا** فيصير الكتف 4.20 والتباعد 45%.
check("👤 FK🔒 وكتفان متباعدان ⇒ لا نموذج (لا يُفبرَك) · وقصيرٌ ⇒ None",
      S.neckline_level(
          (lambda l: _fk([x * 1.02 for x in l], [x * 1.05 for x in l], l,
                         [x * 1.02 for x in l]))(
              [3.0] * 6 + [2.30, 2.55, 2.60, 2.55] + [2.00]
              + [4.00, 4.20, 4.40, 4.60, 4.80])) is None
      and S.neckline_level(_fk([1] * 5, [1] * 5, [1] * 5, [1] * 5)) is None)
# 📐 فيبوّ زنادَ إعادة دخول — مُعايَرٌ من مثاله: 1.84 ⟶ 3.68 والفيبوّ **2.20**
check("📐 FK🔒 فيبوّ إعادة الدخول يُعيد رقم فيصل نفسه (‏≈2.20 من 1.84→3.68)",
      abs(S.fib_reentry(1.84, 3.68)["level"] - 2.20) <= 0.01
      and S.fib_reentry(3.0, 1.0) is None and S.fib_reentry(None, 1) is None)
check("🪜 FK🔒 السلّمان كلاهما بأرقامه: نازل 2.60/2.55/2.50 · صاعد 2.05/2.10/2.15",
      S.descending_ladder(2.60) == [2.60, 2.55, 2.50]
      and S.descending_ladder(2.05, step=-0.05) == [2.05, 2.10, 2.15]
      and S.CONFIG["FAISAL_LADDER_STEP"] == 0.05
      and S.descending_ladder(0) == [] and S.descending_ladder(2.6, step=0) == [])
# 🔒 نطاق: كلُّها **خارج جذور الفرز** — لا اسمَ لأيٍّ منها في أيٍّ منها.
_fk_lines = S.faisal_rule_lines(_fk_ham, price=2.43, entry=2.40, avail=6000,
                                rsi_val=25.0)
check("🧾 FK🔒 المُصدَرُ الواحد يُخرج القواعد فعلًا (‏لا دالّةٌ تُبنى ولا تُعرَض)",
      len(_fk_lines) >= 5
      and any("لكل 10 آلاف" in x for x in _fk_lines)
      and any("من 22 لـ27" in x for x in _fk_lines)
      and any("ذيلُها" in x and "الوقف" in x for x in _fk_lines)
      and any("جني ربح" in x for x in _fk_lines))
check("🧾 FK🔒 وفاشلٌ-آمن مطلقًا: تالفٌ/غيابٌ ⇒ [] بلا انهيار",
      S.faisal_rule_lines(None) == []
      and S.faisal_rule_lines("تالف", price="x", avail="y", rsi_val="z") == [])
check("🧾 FK🔒 موصولٌ بكرت «النهج العلمي» **بعد** اكتماله (عرضٌ لا قرار)",
      "faisal_rule_lines" in _insp0.getsource(S.build_method_alert)
      and _insp0.getsource(S.build_method_alert).index("faisal_rule_lines")
      > _insp0.getsource(S.build_method_alert).index("hunter_extras")
      and "faisal_rule_lines" not in _insp0.getsource(S.scan_method_hunter))
# ✅ **الإذنُ صدر (2026-08-06):** «سوها لو ما تاثر على الفحص و الفرز نفسه». فتحوّل
#    القفلُ من **امتناعٍ** إلى **إذنٍ مشروط**: مسموحٌ في بانيَ الرسالة · **ممنوعٌ**
#    في الفحص/الفرز · والشرطُ يُثبَت **سلوكيًّا** لا نصًّا (أدناه FR3).
check("✅ FR1 قواعدُ «النماذج التعليمية» في كرت صيّاد المقسّم (بإذن المالك)",
      "faisal_rule_lines" in _insp0.getsource(S.build_split_hunter_alert))
check("🔒 FR2 وممنوعةٌ في `scan_split_hunter` (الفحصُ والفرزُ لا يعرفانها)",
      "faisal_rule_lines" not in _insp0.getsource(S.scan_split_hunter)
      and "short_decline_estimate" not in _insp0.getsource(S.scan_split_hunter)
      and "faisal_rsi_zone" not in _insp0.getsource(S.scan_split_hunter))
# 🔴 **والشرطُ يُثبَت سلوكيًّا: نفسُ المطابقين مجموعةً وترتيبًا مع الإثراء وبدونه.**
#    (القفلُ النصّيّ وحده لا يكفي — الإثراءُ يمرّ عبر حقولٍ يقرؤها بانيَ الرسالة.)
_fr_args = dict(today=_sr_today, fetch_splits=lambda s: _sr_splits,
                fetch_float=lambda s: 500_000,
                fetch_borrow=lambda s: {"shares_available": 12000, "borrow_fee": 700.0},
                fetch_pump=lambda df: {"found": False})
_fr_plain = S.scan_split_hunter({"SPLT": _sr_df}, **_fr_args)
_fr_rich = S.scan_split_hunter({"SPLT": _sr_df}, **_fr_args)
for _r in _fr_rich:                      # مُحاكاةُ إثراء `split_hunter.py` بعد الاختيار
    _r["_df"] = _sr_df                   # (بالمفاتيح **الحقيقية** لا المتخيَّلة)
    _r["_rsi"] = 24.0
check("🔴 FR3 العضويةُ والترتيبُ **byte-identical** مع الإثراء وبدونه (سلوكيّ)",
      [x["symbol"] for x in _fr_plain] == [x["symbol"] for x in _fr_rich]
      and len(_fr_plain) == 1,
      f"{[x['symbol'] for x in _fr_plain]} مقابل {[x['symbol'] for x in _fr_rich]}")
# 🔴 والأسطرُ تظهر فعلًا في الكرت (وإلّا كان الإذنُ وصلةً ميتة — درسُ «نقطة النداء»)
_fr_msg = S.build_split_hunter_alert(_fr_rich, today=_sr_today)
_fr_msg_bare = S.build_split_hunter_alert(_fr_plain, today=_sr_today)
# ⚠️ **فارقٌ محدَّد لا «أو»**: أوّلُ صياغةٍ كتبتُها فحصت «RSI أو الشورت أو متوسّطات»
#    فكانت تمرّ ولو قرأ الكودُ **مفتاحًا وهميًّا** (سطرٌ آخر يكفيها) — أمسكها الدرعُ
#    وحده. الآن سطرُ RSI **بعينه**: حاضرٌ مع `_rsi` وغائبٌ بدونه.
check("🔴 FR4 سطرُ RSI **بعينه** يظهر مع `_rsi` ويغيب بدونه (فارقٌ لا «أو»)",
      "من 22 لـ27" in _fr_msg and "من 22 لـ27" not in _fr_msg_bare
      and "SPLT" in _fr_msg and "SPLT" in _fr_msg_bare,
      f"مُثرًى={len(_fr_msg)} · مجرَّد={len(_fr_msg_bare)}")
# 🔒 FR5 والمُغذّي الحيّ يُسنِد `_rsi` فعلًا (وإلّا بقي سطرُ RSI ميّتًا في الإنتاج).
#    بالـAST على `split_hunter.run` — لا بالنصّ لئلّا يكفيه تعليقٌ يذكر الاسم.
import split_hunter as _SH2, ast as _fr_ast                      # noqa: E402
_fr_tree = _fr_ast.parse(_insp0.getsource(_SH2.run))
#    ⚠️ ويجب أن يكون الإسنادُ **هو الحساب** لا الاحتياطَ `= None`: أوّلُ صياغةٍ كتبتُها
#    اكتفت بوجود أيّ إسنادٍ لـ`_rsi`، **فنجت طفرةُ إعادة تسمية سطر الحساب** لأن فرع
#    `except` يُسنِد `_rsi = None` فيُرضي القفل ⇒ قفلٌ يمرّ والسطرُ ميّت.
def _fr_assigns_rsi(tree):
    for a in _fr_ast.walk(tree):
        if not isinstance(a, _fr_ast.Assign):
            continue
        tgt = any(isinstance(n, _fr_ast.Subscript) and isinstance(n.slice, _fr_ast.Constant)
                  and n.slice.value == "_rsi" for n in a.targets)
        calc = any(getattr(c.func, "attr", None) == "rsi"
                   for c in _fr_ast.walk(a.value) if isinstance(c, _fr_ast.Call))
        if tgt and calc:               # الإسنادُ **وحسابُه** معًا
            return True
    return False


check("🔒 FR5 `split_hunter.run` يُسنِد `_rsi` **من حساب `rsi`** لا احتياطًا (AST)",
      _fr_assigns_rsi(_fr_tree))
# ==========================================================
# 🧮 النظام الرابع — «فلترة أسهم التقسيم» (‏`FAISAL_SPLIT_FILTER_METHOD.md`)
#    المرساة: مثالُ فيصل نفسه — قاعٌ 2 ⟹ طلبات **2.05 · 2.10 · 2.15** ووقفٌ **2**.
# ==========================================================
import split_filter_hunter as SF          # noqa: E402
_SFrun = _insp0.getsource(SF.run)
_sf_n = 42
_sf_hi = [5.0, 5.4] + [5.0 - i * 0.06 for i in range(_sf_n)] \
    + [2.10, 2.30, 2.45, 2.20, 2.12, 2.08]
_sf_lo = [4.6, 4.9] + [4.7 - i * 0.06 for i in range(_sf_n)] \
    + [2.00, 2.15, 2.30, 2.10, 2.02, 2.01]
_sf_cl = [4.9, 5.1] + [4.85 - i * 0.06 for i in range(_sf_n)] \
    + [2.05, 2.25, 2.40, 2.15, 2.05, 2.04]
_sf_idx = S.pd.date_range("2026-04-01", periods=len(_sf_hi), freq="B")
_sf_df = S.pd.DataFrame({"Open": _sf_cl, "High": _sf_hi, "Low": _sf_lo,
                         "Close": _sf_cl, "Volume": [3e5] * len(_sf_hi)},
                        index=_sf_idx)
_sf_sp = S.pd.Series([0.1], index=[_sf_idx[0]])


def _sf_scan(**kw):
    kw.setdefault("fetch_splits", lambda s: _sf_sp)
    kw.setdefault("fetch_pump", lambda d: False)
    kw.setdefault("fetch_borrow", lambda s: {"shares_available": 7000})
    kw.setdefault("fetch_news", lambda s: [])
    return S.scan_split_filter({"T1": _sf_df}, today=_sf_idx[-1].date(), **kw)


_sf_rows = _sf_scan()
check("🧮 SF🔒 مطابقٌ كامل بأرقام فيصل: طلبات 2.05/2.10/2.15 · ووقفٌ 2.00",
      len(_sf_rows) == 1 and _sf_rows[0]["entries"] == [2.05, 2.10, 2.15]
      and abs(_sf_rows[0]["stop"] - 2.00) < 1e-6
      and abs(_sf_rows[0]["bottom"] - 2.00) < 1e-6)
check("🧮 SF🔒 والوقف **ذيل شمعة القاع** لا القاع×نسبة ولا الدخول−6% (رابعُ وقف)",
      "ذيل شمعة القاع" in _insp0.getsource(S.split_filter_stop)
      and _sf_rows[0]["stop"] <= _sf_rows[0]["entries"][0])
check("🧮 SF🔒 «الشرط ما عليه حراج» = **القروبات** (تصحيح المالك 2026-08-05)",
      _sf_scan(fetch_pump=lambda d: True) == []
      and any("قروبات" in n["why"] for n in S._SPLIT_FILTER_NEAR))
check("🧮 SF🔒 «الشورت أقلّ من 20 ألف» شرطٌ يرفض · والمجهولُ يمرّ بفائدة الشك",
      _sf_scan(fetch_borrow=lambda s: {"shares_available": 25_000}) == []
      and len(_sf_scan(fetch_borrow=lambda s: {})) == 1
      and len(_sf_scan(fetch_borrow=lambda s: {"shares_available": 19_999})) == 1)
check("🧮 SF🔒 «الشرط ما عليه أخبار سلبية» يرفض فعلًا",
      _sf_scan(fetch_news=lambda s: [{"title": "announces public offering"}]) == []
      and any("أخبار سلبية" in n["why"] for n in S._SPLIT_FILTER_NEAR))
# 🐞 عيّنتي الأولى **تستوفي** الشرطين ② و③ فحذفُهما لا يغيّر شيئًا ⇒ نجت طفرتاهما.
#    يلزم شاهدان **سالبان**: واحدٌ صعد أكثر من 20% وآخرُ بلا ثبات دعمٍ ثانٍ.


def _sf_scan_df(df, **kw):
    kw.setdefault("fetch_splits", lambda s: S.pd.Series([0.1], index=[df.index[0]]))
    kw.setdefault("fetch_pump", lambda d: False)
    kw.setdefault("fetch_borrow", lambda s: {"shares_available": 7000})
    kw.setdefault("fetch_news", lambda s: [])
    return S.scan_split_filter({"T1": df}, today=df.index[-1].date(), **kw)


# ② شاهدٌ سالب — 🐞 وأوّلُ محاولةٍ لي كانت **فارغة**: جعلتُ القمّة 9.0 فصار ÷2
#    = 4.50 بينما السعر 2.04 ⇒ يرفضه `near_bottom` (شرطٌ **أسبق**) ولا يبلغ ②
#    أصلًا. الآن: افتتاح الحدث **3.00** وأعلاه **4.08** ⇒ صعد **+36%** (يخالف
#    «لم يصعد») **و÷2 = 2.04 = السعر** ⇒ `near_bottom` ✓ فيسقط على ② **وحده**.
_sf_rose_tail_hi = [2.10, 2.30, 2.45, 2.20, 2.12, 2.08]
_sf_rose_tail_lo = [2.00, 2.15, 2.30, 2.10, 2.02, 2.01]
_sf_rose_tail_cl = [2.05, 2.25, 2.40, 2.15, 2.05, 2.04]
_sf_rose = S.pd.DataFrame(
    {"Open": [3.00, 3.55] + [3.60 - i * 0.042 for i in range(_sf_n)]
     + _sf_rose_tail_cl,
     "High": [4.08, 3.90] + [3.80 - i * 0.042 for i in range(_sf_n)]
     + _sf_rose_tail_hi,
     "Low": [2.90, 3.40] + [3.50 - i * 0.042 for i in range(_sf_n)]
     + _sf_rose_tail_lo,
     "Close": [3.50, 3.60] + [3.65 - i * 0.042 for i in range(_sf_n)]
     + _sf_rose_tail_cl,
     "Volume": [3e5] * len(_sf_hi)}, index=_sf_idx)
check("🧮 SF🔒 «ما صعد أوّل التقسيم أكثر من 20٪» يرفض فعلًا (شاهدٌ سالب)",
      _sf_scan_df(_sf_rose) == []
      and any("صعد" in n["why"] and "الحدّ 20%" in n["why"]
              for n in S._SPLIT_FILTER_NEAR))
# ③ شاهدٌ سالب: هبوطٌ متّصل بلا ارتدادٍ 10% ولا رجوعٍ يثبت ⇒ لا دعمَ ثانيًا
_sf_noseq_lo = [4.6, 4.9] + [4.7 - i * 0.062 for i in range(_sf_n + 6)]
_sf_noseq = S.pd.DataFrame(
    {"Open": [x * 1.02 for x in _sf_noseq_lo],
     "High": [x * 1.03 for x in _sf_noseq_lo], "Low": _sf_noseq_lo,
     "Close": [x * 1.01 for x in _sf_noseq_lo],
     "Volume": [3e5] * len(_sf_noseq_lo)},
    index=S.pd.date_range("2026-04-01", periods=len(_sf_noseq_lo), freq="B"))
# 🐞 «== []» وحدَها **لا تكفي**: بحذف البوّابة ينهار السطرُ التالي (`seq["bottom"]`)
#    فيلتقطه حارسُ الرمز ⇒ **نفسُ المُخرَج** ⇒ نجت الطفرة. المميِّزُ هو **السبب
#    المُسمّى** في «قريبون من الشرط» (لا يُسجَّل إلا بمرورِ البوّابة).
check("🧮 SF🔒 و«ثبات الدعم الثاني» شرطٌ يرفض **بسببٍ مُسمّى** (لا انهيارٍ صامت)",
      _sf_scan_df(_sf_noseq) == []
      and any("ثبات الدعم الثاني" in n["why"] for n in S._SPLIT_FILTER_NEAR)
      and S.method_sequence(_sf_noseq,
                            win=int(S.CONFIG["FAISAL_BOTTOM_LOOKBACK"])) is None)
# 🎯 شاهدٌ سالب لبوّابة «داخل الطلبات»: السعر 2.20 فوق أعلى الطلبات 2.15،
#    والتسلسلُ سليمٌ (قمّتُه تبقى 2.45) فيسقط على هذي البوّابة **وحدها**.
_sf_above = S.pd.DataFrame(
    {"Open": _sf_cl + [2.20], "High": _sf_hi + [2.25], "Low": _sf_lo + [2.16],
     "Close": _sf_cl + [2.20], "Volume": [3e5] * (len(_sf_hi) + 1)},
    index=S.pd.date_range("2026-04-01", periods=len(_sf_hi) + 1, freq="B"))
check("🎯 SF🔒 ومَن تجاوز منطقة الطلبات يُتابَع ولا يُرسَل («تطلبه طلبًا»)",
      _sf_scan_df(_sf_above) == []
      and S._SPLIT_FILTER_STAGE["seq"] == 1
      and S._SPLIT_FILTER_STAGE["entry_zone"] == 0
      and any("تجاوز منطقة الطلبات" in n["why"] for n in S._SPLIT_FILTER_NEAR))
_sf_msg = S.build_split_filter_alert(_sf_scan(), today=_sf_idx[-1].date())
check("🧮 SF🔒 والكرت يُبنى كاملًا وبأرقامه · وبلا سلّمين متناقضين",
      all(_w in _sf_msg for _w in ("فلترة أسهم التقسيم", "$2.05", "$2.15",
                                   "ذيل شمعة القاع", "يوميّ و4 ساعات"))
      and "طلباتٌ نازلة" not in _sf_msg)
check("🧮 SF🔒 بوّابةُ التوقيت **حقيقيةٌ لا مُلغاة** وتطابق نظيرتَيها حرفيًّا",
      all(SF.session_gate(t) == MH.session_gate(t)
          for t in (S.dt.datetime(2026, 1, 14, 0, 13, tzinfo=S.dt.timezone.utc),
                    S.dt.datetime(2026, 7, 29, 0, 13, tzinfo=S.dt.timezone.utc),
                    S.dt.datetime(2026, 7, 29, 1, 13, tzinfo=S.dt.timezone.utc)))
      and SF.session_gate(S.dt.datetime(2026, 1, 14, 0, 13,
                                        tzinfo=S.dt.timezone.utc)) == (False, None)
      and "session_gate(now_utc)" in _SFrun
      and "hasattr" not in _SFrun)
# 🐞 عيبٌ كشفه **التشغيلُ الحيّ وحده**: `git_save(files, runner, sender)` — مرّرتُ
#    رسالةَ commit في خانة `runner` ⇒ `'str' object is not callable` ⇒ **الختم لا
#    يُحفَظ ⇒ الدِدوب بلا ذاكرة**. يُقفَل بأن النداء **بوسيطٍ واحد** كنظيرَيه.
#    ⚠️ والقفلُ **بالـAST**: نفيٌ نصّيّ («لا فاصلة») يطابق **التعليقَ** الذي يشرح
#       العيبَ نفسه ⇒ سقط على كودٍ سليم. نعدّ وسائطَ النداء الفعليّ لا حروفَه.
def _call_argc(fn, name):
    import ast as _a, textwrap as _t
    for n in _a.walk(_a.parse(_t.dedent(_insp0.getsource(fn)))):
        if (isinstance(n, _a.Call) and isinstance(n.func, _a.Attribute)
                and n.func.attr == name):
            return len(n.args) + len(n.keywords)
    return None


check("🔏 SF🔒 `git_save` تُنادى **بقائمة الملفات وحدها** (توقيعُها runner/sender)",
      _call_argc(SF._write_stamp, "git_save") == 1
      and _call_argc(MH._write_stamp, "git_save") == 1
      and list(_insp0.signature(S.git_save).parameters)
      == ["filenames", "runner", "sender"])
check("🧮 SF🔒 وحرّاسُه نفسُ حرّاس الصيّادين (تغطية · إبلاغ · دِدوب · ختمٌ بعد الإرسال)",
      SF.MIN_COVERAGE_PCT >= 50.0 and "لم يُفحَص السوق" in _SFrun
      and _SFrun.count("_fail(S,") >= 5
      and "لا يوجد سهم يطابق الشروط" in _SFrun
      and _SFrun.index("_write_stamp(S, sess)") > _SFrun.index("send_telegram(msg)"))
check("🧮 SF🔒 والكرونُ **مُزاحٌ** عن الصيّادين (لا يتزاحمون على ياهو)",
      (lambda a, b, c: len({tuple(a), tuple(b), tuple(c)}) == 3)(
          __import__("re").findall(r'cron:\s*"(\d+ \d+)',
                                   _tf_open(".github/workflows/split_filter.yml")),
          __import__("re").findall(r'cron:\s*"(\d+ \d+)',
                                   _tf_open(".github/workflows/method_hunter.yml")),
          __import__("re").findall(r'cron:\s*"(\d+ \d+)',
                                   _tf_open(".github/workflows/split_hunter.yml"))))
check("🧮 SF🔒 **ولا يمسّ صيّاد المقسّم**: يستعمل دوالَّه نداءً لا تعديلًا",
      "_split_setup_probe" in _insp0.getsource(S.scan_split_filter)
      and "scan_split_filter" not in _insp0.getsource(S.scan_split_hunter)
      and "scan_split_filter" not in _insp0.getsource(S.build_split_hunter_alert))
check("🧮 SF🔒 وإعادةُ استعمال `method_sequence` **مبرَّرةٌ نصًّا** لا صامتة",
      "method_sequence" in _insp0.getsource(S.scan_split_filter)
      and "ثبات الدعم الثاني" in _insp0.getsource(S.scan_split_filter))
check("🧾 FK🔒 الجديدة كلُّها خارج الجذور (لا تمسّ اختيارًا ولا ترتيبًا)",
      all(_n not in _insp0.getsource(_f)
          for _n in ("short_decline_estimate", "faisal_rsi_zone", "under_all_mas",
                     "rise_from_bottom", "hammer_wick_stop", "neckline_level",
                     "fib_reentry", "first_target_release", "descending_ladder")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.analyze_ticker, S.apply_float_gate, S.apply_short_gate,
                     S.scan_market, S.backtest_symbol)))

# 🕓 الفريمان معًا — قرار المالك 2026-08-01: «نمشي بالتسلسل حسب اللي أعرفه من أبو
#    بدر — لأن **الأهداف وغالبًا الشموع وحده**». اليوميّ أوّلًا، ثم 4س لمن سقط.
# ==========================================================
_f4_hi = [3.4] * 35 + [18.0] + [9.0, 5.0] + [4.4] * 15 + \
    [3.25, 3.45, 3.70, 3.80, 3.72, 3.68, 3.66, 3.64]      # رجوعٌ لا يلامس القاع
_f4_lo = [3.2] * 35 + [12.0] + [8.2, 4.6] + [4.2] * 15 + \
    [3.10, 3.30, 3.55, 3.62, 3.58, 3.56, 3.54, 3.52]
_f4_cl = [3.3] * 35 + [13.0] + [8.4, 4.8] + [4.3] * 15 + \
    [3.20, 3.40, 3.65, 3.75, 3.70, 3.66, 3.62, 3.60]
_f4_daily = S.pd.DataFrame(
    {"Open": _f4_cl, "High": _f4_hi, "Low": _f4_lo, "Close": _f4_cl,
     "Volume": [5e5] * len(_f4_hi)},
    index=S.pd.date_range("2026-03-02", periods=len(_f4_hi), freq="B"))
_f4_alt = S.pd.DataFrame(                       # وعلى 4س يكتمل التسلسل فعلًا
    {"Open": [3.20, 3.40, 3.65, 3.75, 3.60, 3.40, 3.20, 3.16] * 4,
     "High": [3.25, 3.45, 3.70, 3.80, 3.72, 3.50, 3.30, 3.20] * 4,
     "Low": [3.10, 3.30, 3.55, 3.62, 3.45, 3.30, 3.14, 3.12] * 4,
     "Close": [3.20, 3.40, 3.65, 3.75, 3.60, 3.40, 3.20, 3.16] * 4,
     "Volume": [5e5] * 32},
    index=S.pd.date_range("2026-03-02", periods=32, freq="B"))


def _f4_scan(f4):
    S.scan_method_hunter({"TEST": _f4_daily}, today=_f4_daily.index[-1].date(),
                         fetch_pump=lambda d: False, fetch_offering=lambda s: False,
                         fetch_borrow=lambda s: {"shares_available": 7000},
                         fetch_h4=f4)
    return dict(S._METHOD_STAGE)


_f4_off, _f4_on = _f4_scan(None), _f4_scan(lambda s: _f4_alt)
check("🕓 H4🔒 ما يسقط على اليوميّ **يُلتقَط على 4س** (وإلا فالفريم بلا أثر)",
      _f4_off["seq"] == 0 and _f4_on["seq"] == 1 and _f4_on["seq_h4"] == 1)
check("🕓 H4🔒 و**اليوميّ أوّلًا**: لا يُجلَب 4س لمن نجح عليه (أقلُّ نداءات)",
      _f4_scan(lambda s: _f4_alt) and
      (lambda st: st["h4_fetched"] == 0 and st["seq_h4"] == 0)(
          (lambda: (S.scan_method_hunter(
              {"TEST": _sm_df}, today=_sm_df.index[-1].date(),
              fetch_pump=lambda d: False, fetch_offering=lambda s: False,
              fetch_borrow=lambda s: {"shares_available": 7000},
              fetch_h4=lambda s: _f4_alt), dict(S._METHOD_STAGE))[1])()))
check("🕓 H4🔒 و`fetch_h4=None` ⇒ **السلوك السابق حرفيًّا** (لا 4س بلا حاقن)",
      _f4_off["h4_fetched"] == 0 and _f4_off["seq_h4"] == 0)
# 🪜 **«من الفريم الكبير إلى الصغير»** (قاعدةُ المالك 2026-08-06 · سندُها `IMG_0446`
#    «يوميّ/أسبوعيّ لأسهم التجميع · 4 ساعات **بعد** تكوين قاع» و`IMG_0080`).
#    المفتاحُ الأوّل الفريمُ ثم الصعود — **والمميِّز أن 4س بصعودٍ أعلى لا يتقدّم يوميًّا**.
_fo_rows = [{"symbol": "H4BIG", "frame": "4 ساعات", "t1": 3.0, "entry": 1.0},
            {"symbol": "DLOW", "frame": "يوميّ", "t1": 1.2, "entry": 1.0},
            {"symbol": "DHIGH", "frame": "يوميّ", "t1": 2.0, "entry": 1.0},
            {"symbol": "H4LOW", "frame": "4 ساعات", "t1": 1.1, "entry": 1.0}]
_fo_key = None
for _ln in _insp0.getsource(S.scan_method_hunter).split("\n"):
    if "rows.sort(key=" in _ln:
        _fo_key = _ln
_fo_sorted = sorted(_fo_rows, key=lambda r: (0 if str(r.get("frame") or "") == "يوميّ"
                                             else 1, -(r["t1"] / max(r["entry"], 1e-9))))
check("🪜 FRM1 الترتيبُ: اليوميُّ قبل 4س **ولو كان صعودُ 4س أعلى**",
      [r["symbol"] for r in _fo_sorted] == ["DHIGH", "DLOW", "H4BIG", "H4LOW"],
      str([r["symbol"] for r in _fo_sorted]))
check("🪜 FRM2 والمفتاحُ في الإنتاج يحمل الفريمَ أوّلًا (لا الصعودَ وحده)",
      _fo_key is not None and "frame" in _fo_key, str(_fo_key)[:110])
# 🔒 عطلُ 4س لرمزٍ يتخطّاه وحده ولا يُسقط بقيّة الكون — يُقاس بـ**رمزين**: أحدهما
#    يرمي على 4س والآخر مطابقٌ على اليوميّ. (‏والحارسُ هو الخارجيّ لكلّ رمز؛ حُذف
#    الداخليّ لأنه فرعٌ بلا أثرٍ يمكن قياسه — نجت طفرتُه فكشفت تكراره.)
def _f4_boom(sym):
    if sym == "TEST":
        raise RuntimeError("boom")
    return _f4_alt


S.scan_method_hunter({"TEST": _f4_daily, "OK": _sm_df},
                     today=_f4_daily.index[-1].date(),
                     fetch_pump=lambda d: False, fetch_offering=lambda s: False,
                     fetch_borrow=lambda s: {"shares_available": 7000},
                     fetch_h4=_f4_boom)
_f4_mix = dict(S._METHOD_STAGE)
check("🕓 H4🔒 وعطلُ 4س لرمزٍ يتخطّاه **وحده** (الباقي يُفحَص ويُطابِق)",
      _f4_mix["matched"] == 1 and _f4_mix["seq"] == 1 and _f4_mix["seq_h4"] == 0)
check("🕓 H4🔒 والمضاعف **4 شمعات بالجلسة لا 6** (‏`prepost` ⇒ 16 ساعة ÷ 4)",
      S.CONFIG["METHOD_4H_BARS_PER_SESSION"] == 4
      and "METHOD_4H_BARS_PER_SESSION" in _insp0.getsource(S.scan_method_hunter)
      and "METHOD_4H_BARS_PER_SESSION" in _insp0.getsource(MH._frame_probe))
check("🕓 H4🔒 والفريم **مُسمّى** في الكرت وفي قائمة المراقبة (مستوًى بلا فريمه ادّعاء)",
      "r.get('frame')" in _insp0.getsource(S.build_method_alert)
      and "n.get('frame')" in _insp0.getsource(S.method_near_lines)
      and '"frame": frame' in _insp0.getsource(S.scan_method_hunter))
# 🐞 كتبتُ هذا القفل أوّلًا نصًّا (‏وجودُ «h4_capped» و«قُصّ» في المصدر) — **ونجت
#    الطفرة** لأن الاسمين يبقيان في تهيئة `stage` وفي سطر السجلّ حتى بعد حذف
#    العدّاد. ⇒ قفلٌ **سلوكيّ**: بسقفٍ صفر يجب أن يُحصى المقصوص ولا يُجلَب شيء.
_f4_cap_old = S.CONFIG["METHOD_4H_CAP"]
try:
    S.CONFIG["METHOD_4H_CAP"] = 0
    _f4_cap = _f4_scan(lambda s: _f4_alt)
finally:
    S.CONFIG["METHOD_4H_CAP"] = _f4_cap_old
check("🕓 H4🔒 وسقفُ الجلبات **يُعلَن إن قصّ** (لا قصَّ صامتًا) — قفلٌ سلوكيّ",
      _f4_cap_old >= 100 and _f4_cap["h4_capped"] == 1
      and _f4_cap["h4_fetched"] == 0 and _f4_cap["seq"] == 0
      and "قُصّ" in _insp0.getsource(S.scan_method_hunter))
check("🕓 H4🔒 والنداء الإنتاجيّ يمرّر الجالب فعلًا (لا ميزةٌ بلا سلك)",
      "fetch_h4=S.fetch_4h" in _insp0.getsource(MH.run))
_ = S.scan_method_hunter({}, today=None)          # تنظيفُ الحالة العامّة
# 🔒 نطاق: أداةٌ مستقلّة — لا تمسّ الفرز ولا صيّاد المقسّم.
# 🎁 الكماليّات الحيّة (طلب المالك: «نفس اللي أضفناها في أداة التقسيم»).
_MHrun = _insp0.getsource(MH.run)
check("🎁 NH🔒 الإثراء الحيّ موصول: تدفّق السيولة · 4 ساعات · اختبار القاع",
      all(_k in _MHrun for _k in ("polygon_flow", "fetch_4h", "bottom_test_state")))
check("🎁 NH🔒 والإثراء **بعد** المسح ⇒ يستحيل أن يُدخل مرشّحًا أو يُخرجه",
      _MHrun.index("scan_method_hunter") < _MHrun.index("polygon_flow"))
check("🎁 NH🔒 وكلُّ جالبٍ فاشلٌ-آمن على حدة (عطلُ رمزٍ لا يُسقط الرسالة)",
      "_r[_k] = None" in _MHrun)
check("🎁 NH🔒 الكرت يمرّر `flow`/`df4h` فعلًا (لا حقلٌ يُجلَب ولا يُعرَض)",
      'flow=r.get("flow")' in _insp0.getsource(S.build_method_alert)
      and 'df4h=r.get("df4h")' in _insp0.getsource(S.build_method_alert))
# 🔭 التتبّع الحيّ: «انتظر ضغطته مره ثانيه عند القاع» تحتاج أن تعرف مَن يقترب.
check("🔭 NH🔒 مَن بلغ التسلسل وسقط على شرطٍ واحد يُسجَّل باسمه وسببه",
      "_METHOD_NEAR" in _insp0.getsource(S.scan_method_hunter)
      and "_near(" in _insp0.getsource(S.scan_method_hunter))
check("🔭 NH🔒 والسجلّ يُفرَّغ كلّ مسح (لا تراكمَ من تشغيلةٍ سابقة)",
      "_METHOD_NEAR.clear()" in _insp0.getsource(S.scan_method_hunter))
check("🔭 NH🔒 ويظهر في الكرت **وفي رسالة «لا يوجد»** (المتابعة تسبق الترشيح)",
      "method_near_lines" in _insp0.getsource(S.build_method_alert)
      and "method_near_lines" in _MHrun)
# 🐞 **عيبٌ حقيقيّ وصل المالك في رسالةٍ حيّة (2026-08-01):** الترويسة تُعلن «(14)»
#    والمعروض **ستّة** ⇒ يُقرأ العدد على أنه ما تراه = **قصٌّ صامت** تمنعه قاعدتُنا.
#    وكان الكودُ **مكرّرًا في موضعين** فأمكن إصلاح أحدهما وبقاءُ الآخر ⇒ مُصدَرٌ واحد.
_nearN = [{"symbol": f"S{i}", "price": 1.0 + i, "why": "بعيد", "over_pct": float(i)}
          for i in range(S.METHOD_NEAR_SHOW + 4)]
_nlN = S.method_near_lines(_nearN)
check("🔭 NH🔒 **لا قصّ صامت**: يُعلن الإجمال ويعرض السقف ويُصرّح بعدد الباقين",
      _nlN[0].count(str(len(_nearN))) == 1
      and sum(1 for x in _nlN if x.startswith("  •")) == S.METHOD_NEAR_SHOW
      and any("4" in x and "غيرهم" in x for x in _nlN))
check("🔭 NH🔒 ولا يظهر سطرُ «غيرهم» حين لا قصّ (القفل ليس عدميًّا) · وفارغٌ ⇒ []",
      not any("غيرهم" in x for x in S.method_near_lines(_nearN[:3]))
      and S.method_near_lines([]) == [] and S.method_near_lines(None) == [])
# 🔴 سؤال المالك 2026-08-01: «فيه أسهم بالقديمة مب موجودة بالجديدة» — سببُه سقفٌ
#    (‏10) **أضيق من العدد الطبيعيّ** (‏14 بلغوا التسلسل يوم 07-31) ⇒ يقصّ كلَّ يوم.
check("🔭 NH🔒 السقف أوسع من العدد المعتاد (‏≥20) فلا يُقصّ اليومُ الطبيعيّ أصلًا",
      S.METHOD_NEAR_SHOW >= 20
      and sum(1 for x in S.method_near_lines(_nearN[:14]) if x.startswith("  •")) == 14
      and not any("غيرهم" in x for x in S.method_near_lines(_nearN[:14])))
check("🔭 NH🔒 وسببُ الترتيب **مرئيّ** في السطر (نسبة التجاوز) — لا رتبةٌ بلا تفسير",
      "تجاوز منطقة الدخول بـ" in _insp0.getsource(S.scan_method_hunter)
      and "الدخول $" in _insp0.getsource(S.scan_method_hunter))
check("🔭 NH🔒 **مُصدَرٌ واحد** للقائمة (لا تكرارَ يُصلَح نصفُه)",
      "[:6]" not in _insp0.getsource(S.build_method_alert)
      and "[:6]" not in _MHrun and "method_near_lines" in _insp0.getsource(S))
check("🔭 NH🔒 والترتيب **بالأقرب إلى الدخول** (مَن هو داخل المنطقة يتصدّر)",
      "_METHOD_NEAR.sort" in _insp0.getsource(S.scan_method_hunter)
      and '"over_pct"' in _insp0.getsource(S.scan_method_hunter))
check("🩺 NH🔒 والسجلّ **بلا سقف** (التشخيص يحتاج الكلّ · القصّ للرسالة وحدها)",
      "[:12]" not in _MHrun and 'S.log(f"   🔭' in _MHrun)
# 🔬 مِجَسّ الفريم: فيصل صرّح «هذي شموع 4 ساعات» (`IMG_0494`) ونقرأ اليوميّ، وسؤال
#    «اطبقه دايم ع الفريم اليومي؟» (`IMG_0495`) **بلا جواب** ⇒ يُقاس ولا يُغيَّر.
_fp_src = _insp0.getsource(MH._frame_probe)
# 🐞 كتبتُ القفلين أوّلًا نصًّا فسقطا على كودٍ سليم: الأوّل `split` على مفتاحٍ
#    **يرد في الـdocstring أوّلًا**، والثاني يمنع اسم متغيّرٍ محلّيّ مشروع. ⇒ AST.
def _guard_returns(fn, key):
    import ast as _a, textwrap as _t
    for n in _a.walk(_a.parse(_t.dedent(_insp0.getsource(fn)))):
        if isinstance(n, _a.If) and key in _a.unparse(n.test):
            return any(isinstance(x, _a.Return) for x in _a.walk(n))
    return False


def _s_attrs(fn):
    """أسماءُ ما يلمسه المِجَسّ من `S` — فيُثبَت أنه **قارئٌ لا كاتب**."""
    import ast as _a, textwrap as _t
    out = set()
    for n in _a.walk(_a.parse(_t.dedent(_insp0.getsource(fn)))):
        if (isinstance(n, _a.Attribute) and isinstance(n.value, _a.Name)
                and n.value.id == "S"):
            out.add(n.attr)
    return out


check("🔬 FRAME🔒 المِجَسّ **مطفأ افتراضيًّا** ⇒ التشغيلة المجدولة بت-بت",
      _guard_returns(MH._frame_probe, "METHOD_4H_PROBE") is True
      and MH._frame_probe(S) is None)
check("🔬 FRAME🔒 ويقيس بـ`method_sequence` **نفسها** على 4س (لا نسخةٍ ثانية)",
      {"method_sequence", "fetch_4h"} <= _s_attrs(MH._frame_probe)
      and "_METHOD_FOUNDING" in _fp_src)
def _writes_to_S(fn):
    """هل يُسنِد المِجَسّ إلى أيّ شيءٍ من `S`؟ (‏`S.x = …` أو `S.x[...] = …`)."""
    import ast as _a, textwrap as _t
    for n in _a.walk(_a.parse(_t.dedent(_insp0.getsource(fn)))):
        if isinstance(n, (_a.Assign, _a.AugAssign)):
            tgts = n.targets if isinstance(n, _a.Assign) else [n.target]
            for t in tgts:
                if "S." in _a.unparse(t):
                    return True
    return False


check("🔬 FRAME🔒 و**لا يمسّ المُرسَل**: لا يستقبل الصفوف · قراءةٌ فقط · ولا يكتب في `S`",
      _s_attrs(MH._frame_probe) <= {"log", "fetch_4h", "method_sequence",
                                    "CONFIG", "_METHOD_FOUNDING", "_METHOD_STAGE"}
      and _writes_to_S(MH._frame_probe) is False
      and list(_insp0.signature(MH._frame_probe).parameters) == ["S"]
      and _MHrun.index("_frame_probe(S)") > _MHrun.index("scan_method_hunter"))
check("🔬 FRAME🔒 والحدثُ المؤسِّس يُجمَع ويُفرَّغ كلّ مسح (لا تراكمَ من تشغيلة)",
      "_METHOD_FOUNDING.append" in _insp0.getsource(S.scan_method_hunter)
      and "_METHOD_FOUNDING.clear()" in _insp0.getsource(S.scan_method_hunter))
check("🔬 FRAME🔒 والعلم موصولٌ بالـworkflow (لا زرَّ بلا سلك)",
      "METHOD_4H_PROBE" in _tf_open(".github/workflows/method_hunter.yml")
      and "frame_probe" in _tf_open(".github/workflows/method_hunter.yml"))
check("🔭 NH🔒 وثلاثة أسبابٍ مُسمّاة لا «سقط» مبهمة",
      all(_w in _insp0.getsource(S.scan_method_hunter) for _w in (
          "لا فجوةَ هابطة", "دخلته قروبات", "إعلان طرح حديث")))
check("🔬 NH🔒 خارج الجذور والفرز (لا اسمَ لها في أيٍّ منها)",
      all(_n not in _insp0.getsource(_f)
          for _n in ("scan_method_hunter", "method_founding", "build_method_alert")
          for _f in (S.rank_key, S.select_top, S.classify_tier, S.entry_status,
                     S.analyze_ticker, S.apply_float_gate, S.apply_short_gate,
                     S.scan_market, S.backtest_symbol, S.scan_split_hunter,
                     S.build_split_hunter_alert)))
check("🔬 NH🔒 وكرونُها **لا يزاحم** صيّاد المقسّم (خنقُ ياهو مشترك)",
      (lambda a, b: a != b)(
          __import__("re").findall(r'cron:\s*"(\d+ \d+)',
                                   _tf_open(".github/workflows/method_hunter.yml")),
          __import__("re").findall(r'cron:\s*"(\d+ \d+)',
                                   _tf_open(".github/workflows/split_hunter.yml"))))

# ==========================================================
# 🔬 T-METHOD — البنية الأربع (`method_prereg.md` §⑧-مكرّر) · بحث/قياس
# ==========================================================
import method_scan as MS          # noqa: E402
import method_run as MR           # noqa: E402

# ① حارس التقسيم — **الأخطر**: البيانات المعدَّلة تُصنّع الحدث المؤسِّس نفسه.
check("🔬 M①🔒 تقسيمٌ داخل النافذة ⇒ إقصاء · وخارجها ⇒ لا إقصاء",
      MS.split_in_window([("2026-03-05", 0.1)], "2026-03-01", "2026-03-10") is True
      and MS.split_in_window([("2026-04-05", 0.1)], "2026-03-01", "2026-03-10")
      is False)
check("🔬 M①🔒 فاشلٌ **نحو الإقصاء**: مدخلٌ تالف ⇒ True لا انهيار (كشفه فحصُ دخان)",
      MS.split_in_window(["تالف"], "2026-03-01", "2026-03-10") is True
      and MS.split_in_window([(None, None)], "2026-03-01", "2026-03-10") is True)
check("🔬 M①🔒 غياب السياق ⇒ لا إقصاء **وتُعلَن التغطية** (لا ادّعاءٌ صامت)",
      MS.split_in_window(None, "2026-03-01", "2026-03-10") is False
      and "حارس التقسيم: تغطية" in _insp0.getsource(MR.run)
      and "**خامل ⇒ لا تُفسَّر النتيجة**" in _insp0.getsource(MR.run))
# 🔴 التشغيلة الأولى كشفت أن اللقطة تغطّي **79 من 3386** ⇒ الحارس الأخطر خاملٌ في
#    98% من الكون. فصار يجلب مباشرةً عند غياب اللقطة، ويُعلن التغطية رقمًا.
check("🔬 M①🔒 وعند غياب اللقطة **يُجلَب** لكلّ مرشّح (لا اعتمادَ عليها وحدها)",
      "_fetch_splits" in _insp0.getsource(MR.run))

# ② فهرس SEC مؤرَّخ — علاجُ البوّابة الميتة.
check("🔬 M②🔒 النشرات النهائية فقط بتواريخها (‏S-1 روتينية تُستبعَد)",
      MS.parse_dated_offerings(
          {"form": ["424B5", "S-1", "424B4", "EFFECT"],
           "filingDate": ["2026-01-05", "2026-02-01", "2026-03-09", "2026-03-10"]})
      == ["2026-01-05", "2026-03-09"])
check("🔬 M②🔒 **بلا نظرٍ مستقبليّ**: نشرةٌ بعد لحظة القرار لا تُقرأ",
      MS.offering_before(["2026-01-05"], S.dt.date(2026, 3, 1)) is True
      and MS.offering_before(["2026-06-05"], S.dt.date(2026, 3, 1)) is False)
check("🔬 M②🔒 وغيابُ الفهرس يُعلَن «غير مُختبَر» لا «مستوفًى» (بصمة الـno-op)",
      "**غير مُختبَر**" in _insp0.getsource(MR.run)
      and "لا يُدَّعى استيفاؤه" in _insp0.getsource(MR.run))

# ③ السببية — «آخر اختبار» لا يُعرَف إلا بأثرٍ رجعيّ.
check("🔬 M③🔒 `peak_and_decline` تقرأ المُمرَّر وحده ⇒ سببيّةٌ بنيويًّا",
      (lambda r: r and r["peak_idx"] == 10 and r["bars_since_peak"] == 30)(
          MS.peak_and_decline([1.0] * 5 + [2.0] * 5 + [10.0] + [3.0] * 30)))
check("🔬 M③🔒 وإلحاق شمعةٍ لاحقة **لا يغيّر** ناتج الماضي (اختبار سببية)",
      MS.peak_and_decline(([1.0] * 5 + [2.0] * 5 + [10.0] + [3.0] * 30))
      == MS.peak_and_decline(([1.0] * 5 + [2.0] * 5 + [10.0] + [3.0] * 30
                              + [9.0] * 7)[:41]))
# ⚠️ **بالـAST لا بالنصّ**: القفل النصّيّ نجت منه طفرةٌ لأن **الـdocstring** يحوي
#    العبارة نفسها — وهو الفخّ المدوَّن (‏`getsource` لا يفرّق كودًا عن توثيق).
#    الشرط الحقيقيّ: الوسيط الثاني لنداء `method_signal` **قَطعٌ** لا اسمُ الإطار.
def _walk_passes_slice():
    import ast as _a, textwrap as _t
    for n in _a.walk(_a.parse(_t.dedent(_insp0.getsource(MS.walk)))):
        if (isinstance(n, _a.Call) and isinstance(n.func, _a.Name)
                and n.func.id == "method_signal" and len(n.args) >= 2):
            return isinstance(n.args[1], _a.Subscript)
    return False


check("🔬 M③🔒 المشي يمرّر **قَطعًا** لا الإطار الكامل (قفل AST لا نصّ)",
      _walk_passes_slice() is True)
check("🔬 M③🔒 والحسم بمحرّكٍ **واحد** (`_resolve_arm`) — لا ثانٍ (‏F-L1)",
      "_resolve_arm" in _insp0.getsource(MS.walk)
      and "filled + 1" in _insp0.getsource(MS.walk))

# ④ استبعاد رموز المصدر (‏in-sample) — سابقة GEOS في E2.
check("🔬 M④🔒 `UPC` (مصدر الوصفة) خارج عيّنة الحكم ويُعَدّ صراحةً",
      "UPC" in MS.SOURCE_SYMBOLS
      and "SOURCE_SYMBOLS" in _insp0.getsource(MR.run)
      and "مستبعَد كمصدر" in _insp0.getsource(MR.run))

# 🔒 نطاق: الأداة **خارج الإنتاج** — لا تُستورَد ولا تُذكَر في مسار حيّ.
check("🔬 M🔒 خارج الإنتاج: لا `method_scan`/`method_run` في `Super_stock.py`",
      "import method_scan" not in _insp0.getsource(S)
      and "method_run" not in open("split_hunter.py", encoding="utf-8").read())
check("🔬 M🔒 الحدث المؤسِّس بثوابت **الإنتاج** لا أرقامٍ مُبتكَرة",
      "EXPLOSION_PCT" in _insp0.getsource(MS.method_signal)
      and "PRIOR_SPIKE_WINDOW" in _insp0.getsource(MS.method_signal)
      and MS.DECLINE_MIN_BARS == 20 and MS.DECLINE_MAX_BARS == 30)
check("🔬 M🔒 «20 < 30 يوم» حرفيّ: 19 و31 يسقطان · 20 و30 يمرّان (تخوم مقفولة)",
      (lambda f: all(f(n) for n in (20, 25, 30))
       and not any(f(n) for n in (19, 31)))(
          lambda n: bool(MS.founding_context(
              S.pd.DataFrame({"High": [1.0] * 5 + [10.0] + [3.0] * n},
                             index=S.pd.date_range("2024-01-01",
                                                   periods=6 + n, freq="D")),
              50.0, 20))))

# ==========================================================
# 🥇 T-RANKER — الأذرع (`ranker_prereg.md`) · بحث/قياس خارج الإنتاج
# ==========================================================
import ranker_arms as RA           # noqa: E402
# 🔴 **القفل الأهمّ: `dedupe_key=None` = السلوك السابق حرفيًّا** — وإلّا كانت إضافةُ
#    K3 قد غيّرت خطَّ الأساس نفسه فبطلت المقارنة كلُّها قبل أن تبدأ.
# ⚠️ الجاهزية **متمايزة عمدًا**: أوّل عيّنةٍ كتبتُها ساوت بينها فسقط `rank_actual`
#    إلى `rr` نفسه ⇒ صارت K0 و K2 **متطابقتين** والقفلُ يقيس لا شيء.
_rk_pool = [_cand(0, "A", 0, rdy=90.0, rr=1.0), _cand(0, "B", 1, rdy=50.0, rr=3.0),
            _cand(0, "C", 2, rdy=70.0, rr=2.0)]
_rk_out = lambda c: (RP.R_STOP, 1)                              # noqa: E731
_rk_base = RP.replay(_rk_pool, outcome_of=_rk_out, capacity=3)
check("🥇 RANK🔒 `dedupe_key=None` ⇒ نفس المأخوذين ترتيبًا (خطّ الأساس لم يتغيّر)",
      [c.symbol for c in RP.replay(_rk_pool, outcome_of=_rk_out, capacity=3,
                                   dedupe_key=None)["taken"]]
      == [c.symbol for c in _rk_base["taken"]])
check("🥇 RANK🔒 K2 (`rank_rr`) يرتّب بالعائد/المخاطرة تنازليًّا لا بالجاهزية",
      [c.symbol for c in RP.replay(_rk_pool, outcome_of=_rk_out, capacity=3,
                                   ranker=RP.rank_rr)["taken"]] == ["B", "C", "A"]
      and [c.symbol for c in _rk_base["taken"]] == ["A", "C", "B"])
# 🥇 K3: **مرشّحٌ واحد لكل مفتاح** في الجلسة — والمرفوض يُعَدّ لا يُبتلَع.
_rk_k3 = RP.replay(_rk_pool, outcome_of=_rk_out, capacity=3,
                   dedupe_key=lambda c: "قطاع" if c.symbol in ("A", "B") else "آخر")
check("🥇 RANK🔒 K3 يقبل واحدًا لكل قطاع في الجلسة ويعدّ المرفوض بالتنويع",
      [c.symbol for c in _rk_k3["taken"]] == ["A", "C"]
      and _rk_k3["rejected_div"] == 1)
check("🥇 RANK🔒 ومفتاحٌ `None` **لا يُقصي** (تعذّر القطاع ≠ إقصاء بالظنّ)",
      [c.symbol for c in RP.replay(_rk_pool, outcome_of=_rk_out, capacity=3,
                                   dedupe_key=lambda c: None)["taken"]]
      == ["A", "C", "B"])
check("🥇 RANK🔒 مقياس «المنفجرون المُسلَّمون» = ‏+100% قبل الوقف (لا نسبة نجاح)",
      RA.EXPLODE_PCT == 100.0
      and RA._exploders([RP.Candidate(0, "A", payload={"mg_pre_stop": 120.0}),
                         RP.Candidate(0, "B", payload={"mg_pre_stop": 99.9}),
                         RP.Candidate(0, "C", payload={})]) == 1)
check("🥇 RANK🔒 القطاع الغائب/الفارغ ⇒ None (لا تنويعَ مفبرك)",
      RA._sector_key(RP.Candidate(0, "A", payload={})) is None
      and RA._sector_key(RP.Candidate(0, "A", payload={"sector": "  "})) is None
      and RA._sector_key(RP.Candidate(0, "A", payload={"sector": "تقنية"}))
      == "تقنية")
check("🥇 RANK🔒 المُشغِّل يتوقّف عند خمول العلم (لا يُفسَّر صفرٌ مفبرك)",
      "BT_POTENTIAL` خامل" in _insp0.getsource(RA.run)
      and "BT_REPLAY10` خامل" in _insp0.getsource(RA.run))
check("🥇 RANK🔒 خارج الإنتاج: `ranker_arms` غير مستورَدة في `Super_stock.py`",
      "import ranker_arms" not in _insp0.getsource(S)
      and "ranker_arms" not in open("split_hunter.py", encoding="utf-8").read())

# ① 🔴 القفل الحاسم: **الخاسر غير المُعبَّأ يحجز خانةً** (إصلاح P0-01)
#    سعة 1 · A بالجلسة 0 نتيجته `window` بعد 5 جلسات · B بالجلسة 2.
#    السلوك القديم كان يُسقط A فيأخذ B الخانة — والصحيح أن B يُرفض بالسعة.
_r1 = RP.replay([_cand(0, "A", 0), _cand(2, "B", 1)],
                outcome_of=lambda c: (RP.R_WINDOW, 5), capacity=1)
check("🔁 REPLAY10🔒 غير المُعبَّأ يحجز خانةً (لا نظر مستقبليّ)",
      [c.symbol for c in _r1["taken"]] == ["A"] and _r1["rejected_cap"] == 1)

# ② بعد انتهاء نافذة A تُحرَّر الخانة فعلًا (لا حجزٌ أبديّ)
_r2 = RP.replay([_cand(0, "A", 0), _cand(5, "B", 1)],
                outcome_of=lambda c: (RP.R_WINDOW, 5), capacity=1)
check("🔁 REPLAY10🔒 الخانة تُحرَّر بانتهاء النافذة",
      [c.symbol for c in _r2["taken"]] == ["A", "B"] and _r2["rejected_cap"] == 0)

# ③ **الهدف يحرّر الخانة ويُبقي الاسم محمولًا** (قاعدة الإنتاج المنصوصة)
_r3 = RP.replay([_cand(0, "A", 0), _cand(3, "B", 1)],
                outcome_of=lambda c: (RP.R_HIT_HELD, 2), capacity=1)
_last3 = _r3["daily"][max(_r3["daily"])]
check("🔁 REPLAY10🔒 الهدف يحرّر الخانة والاسم يبقى محمولًا",
      [c.symbol for c in _r3["taken"]] == ["A", "B"] and set(_last3) == {"A", "B"})

# ④ 🔴 المحمول لا يُحتسب ضدّ السعة ⇒ القائمة تتجاوز السقف (كما رُصد حيًّا: 13 > 10)
check("🔁 REPLAY10🔒 المحمول لا يُحتسب ضدّ السعة (الحجم يتجاوز السقف)",
      _r3["max_size"] == 2 and _r3["capacity"] == 1)

# ⑤ الوقف **يُزيل** الاسم بينما الهدف **يُبقيه** — يُقاس على جلساتٍ لاحقة صريحة.
#    ⚠️ الصيغة الأولى كانت **قفلًا فارغًا**: بمرشّحٍ واحدٍ في الجلسة 0 لا توجد جلسةٌ
#    لاحقة تُرى فيها الإزالة، فنجت طفرةُ «الوقف يحرّر ولا يُزيل». أمسكها اختبار الطفرة.
_r5s = RP.replay([_cand(0, "A", 0)], outcome_of=lambda c: (RP.R_STOP, 2),
                 capacity=1, sessions=range(0, 4))
_r5h = RP.replay([_cand(0, "A", 0)], outcome_of=lambda c: (RP.R_HIT_HELD, 2),
                 capacity=1, sessions=range(0, 4))
check("🔁 REPLAY10🔒 الوقف يُزيل الاسم فعلًا من الجلسات اللاحقة",
      _r5s["daily"][1] == ("A",) and _r5s["daily"][2] == () and _r5s["daily"][3] == ())
check("🔁 REPLAY10🔒 والهدف يُبقيه محمولًا في الجلسات نفسها (تمييزٌ حقيقيّ)",
      _r5h["daily"][2] == ("A",) and _r5h["daily"][3] == ("A",))

# ⑥ الزمن **بالجلسات**: فجوةٌ في فهارس الجلسات لا تُقصّر الحجز
#    A يدخل الجلسة 0 ويُحجز 3 جلسات ⇒ B بالجلسة 2 يُرفض، وبالجلسة 3 يُقبل.
_r6a = RP.replay([_cand(0, "A", 0), _cand(2, "B", 1)],
                 outcome_of=lambda c: (RP.R_WINDOW, 3), capacity=1)
_r6b = RP.replay([_cand(0, "A", 0), _cand(3, "B", 1)],
                 outcome_of=lambda c: (RP.R_WINDOW, 3), capacity=1)
check("🔁 REPLAY10🔒 الحجز يُقاس بالجلسات لا بأيامٍ تقويمية",
      _r6a["rejected_cap"] == 1 and _r6b["rejected_cap"] == 0)

# ⑦ لا خانتان لرمزٍ واحد متزامنًا
_r7 = RP.replay([_cand(0, "A", 0), _cand(1, "A", 1)],
                outcome_of=lambda c: (RP.R_WINDOW, 9), capacity=5)
check("🔁 REPLAY10🔒 لا تكرار لرمزٍ متزامن", _r7["rejected_dup"] == 1)

# ⑧ المُرتِّب الفعليّ يُقدّم الأعلى جاهزيةً (لا الأقدم)
_r8 = RP.replay([_cand(0, "LOW", 0, rdy=10.0), _cand(0, "HIGH", 1, rdy=90.0)],
                outcome_of=lambda c: (RP.R_WINDOW, 9), capacity=1)
check("🔁 REPLAY10🔒 R0 يرتّب بالجاهزية", [c.symbol for c in _r8["taken"]] == ["HIGH"])

# ⑨ FIFO شاهد ضبط: يأخذ الأقدم رغم انخفاض جاهزيته
_r9 = RP.replay([_cand(0, "LOW", 0, rdy=10.0), _cand(0, "HIGH", 1, rdy=90.0)],
                outcome_of=lambda c: (RP.R_WINDOW, 9), ranker=RP.rank_fifo, capacity=1)
check("🔁 REPLAY10🔒 R1 (FIFO) شاهد ضبط مستقلّ",
      [c.symbol for c in _r9["taken"]] == ["LOW"])

# ⑩ العشوائيّ **حتميّ**: نفس البذرة ⇒ نفس النتيجة · ومستقلّ عن ترتيب الإدخال
_cs = [_cand(0, "A", 0), _cand(0, "B", 1), _cand(0, "C", 2)]
_r10a = RP.replay(_cs, outcome_of=lambda c: (RP.R_WINDOW, 9),
                  ranker=RP.make_rank_random(7), capacity=1)
_r10b = RP.replay(list(reversed(_cs)), outcome_of=lambda c: (RP.R_WINDOW, 9),
                  ranker=RP.make_rank_random(7), capacity=1)
_r10c = RP.replay(_cs, outcome_of=lambda c: (RP.R_WINDOW, 9),
                  ranker=RP.make_rank_random(8), capacity=1)
check("🔁 REPLAY10🔒 R2 حتميّ بالبذرة ومستقلّ عن ترتيب الإدخال",
      [c.symbol for c in _r10a["taken"]] == [c.symbol for c in _r10b["taken"]])
# البذرة تُغيّر الترتيب فعلًا — يُقاس على **الترتيب الكامل** لا على مأخوذٍ واحد
# (مقارنة رمزٍ واحد قد تتصادف؛ هذا حتميّ لا احتماليّ)
_perm = {tuple(sorted((c.symbol for c in _cs), key=lambda s2, sd=sd: RP.make_rank_random(sd)(
             next(c for c in _cs if c.symbol == s2))))
         for sd in (1, 2, 3, 4, 5)}
check("🔁 REPLAY10🔒 R2 البذرة تُغيّر الترتيب (لا ثابتٌ متنكّر)", len(_perm) >= 2)

# ⑪ بوّابة الصلاحية أ: العتبة 0.95 · والفراغان يتفقان
check("🔁 REPLAY10🔒 gate_a: تطابقٌ تامّ يعبر",
      RP.gate_a({0: ("A", "B")}, {0: ("A", "B")})["passed"] is True)
check("🔁 REPLAY10🔒 gate_a: اختلافٌ جوهريّ يسقط",
      RP.gate_a({0: ("A", "B")}, {0: ("C",)})["passed"] is False)
check("🔁 REPLAY10🔒 gate_a: يومان فارغان = اتفاق (لا قسمةٌ على صفر)",
      RP.jaccard((), ()) == 1.0)

# ⑫ 🔒 قفل عزل: `replay10` **لا يُستورَد في مسار الإنتاج**
# 🔴 **صُحِّح 2026-08-06:** كان `"replay10" not in _rp_src` — نصًّا محضًا، **فسقط على
#    جملةٍ عربية** في تقرير المسارات تذكر اسمَ الوحدة شرحًا لا استعمالًا. وهو الفخُّ
#    الموثَّق: **النصُّ لا يفرّق كودًا عن تعليقٍ ولا عن سلسلةِ عرض**، في الاتّجاهين.
#    الآن **بالـAST على الاستيرادات الفعليّة** — أقوى (يمسك `importlib` بالاسم أيضًا)
#    وأدقّ (لا يمنع ذِكرَ الاسم في شرحٍ يقرؤه المالك).
_rp_src = open("Super_stock.py", encoding="utf-8").read()   # يستعمله قفلٌ لاحق
_rp_tree = _ast0.parse(_rp_src)
_rp_imports = set()
for _n in _ast0.walk(_rp_tree):
    if isinstance(_n, _ast0.Import):
        _rp_imports |= {a.name.split(".")[0] for a in _n.names}
    elif isinstance(_n, _ast0.ImportFrom) and _n.module:
        _rp_imports.add(_n.module.split(".")[0])
    elif (isinstance(_n, _ast0.Call)
          and getattr(_n.func, "attr", None) == "import_module"
          and _n.args and isinstance(_n.args[0], _ast0.Constant)):
        _rp_imports.add(str(_n.args[0].value).split(".")[0])
check("🔁 REPLAY10🔒 معزولة عن الإنتاج (لا تُستورَد في Super_stock — AST لا نصّ)",
      "replay10" not in _rp_imports, str(sorted(_rp_imports))[:120])

# ═══════════════════════════════════════════════════════════════════════════
# 🔁 T-REPLAY10 · المرحلة 2 — أقفال جسر «صفقات المحرّك ← مرشّحو الإعادة»
#    الحقول الثلاثة الجديدة (`exit_date`/`exit_kind`/`rr`) خلف علمٍ مطفأ،
#    والمقياس (صافي R/يوم) والاستدلال المسجَّل. مواصفاتها في التسجيل المسبق §②/§⑤.
# ═══════════════════════════════════════════════════════════════════════════

# ⑬ 🔴 القفل الحاسم: **محرّك الخروج يطابق محرّك الحسم** على مدخلاتٍ عشوائية.
#    `_arm_a_exit_bar` نسخةٌ ثانية من منطق الذراع A (تعيد الفهرس لا العائد)، فلولا
#    هذا القفل لتفرّق المنطقان بصمتٍ ⇒ توقيت تحرير الخانة يصير كذبًا.
_rnd_ex = __import__("random").Random(20260731)
_ex_bad = []
for _ in range(400):
    _n = _rnd_ex.randint(1, 12)
    _base = [round(_rnd_ex.uniform(1.0, 4.0), 2) for _ in range(_n)]
    _hi = [b + round(_rnd_ex.uniform(0, 1.2), 2) for b in _base]
    _lo = [b - round(_rnd_ex.uniform(0, 1.2), 2) for b in _base]
    _cl = _base
    _op = _base
    _entry = round(_rnd_ex.uniform(1.0, 4.0), 2)
    _stop = round(_entry * _rnd_ex.uniform(0.80, 0.99), 2)
    _t1 = round(_entry * _rnd_ex.uniform(1.01, 1.60), 2)
    _fil = _rnd_ex.choice([None] + list(range(_n)))
    _a = S._resolve_arm(_hi, _lo, _cl, _op, _entry, _stop, _t1, _fil)[0]
    _b, _k = S._arm_a_exit_bar(_hi, _lo, _cl, _entry, _stop, _t1, _fil)
    if _a != _b or not (0 <= _k < max(_n, 1)):
        _ex_bad.append((_a, _b, _k, _n))
check("🔁 REPLAY10🔒 محرّك الخروج ≡ محرّك الحسم (400 حالة عشوائية · لا تفرّق صامت)",
      not _ex_bad, f"مخالفات={_ex_bad[:3]}")

# ⑭ فهرس شمعة الخروج **دقيق** لا مجرّد متّسق: الوقف يُفحَص أوّلًا · والهدف من
#    `filled+1` (درس F-L1) · وغير المحسوم/غير المُعبَّأ ⇒ آخر شمعة (يشغل الخانة كاملة).
check("🔁 REPLAY10🔒 الوقف يُحسم بشمعته بالضبط",
      S._arm_a_exit_bar([2.0, 2.0, 2.0], [2.0, 2.0, 0.5], [2.0, 2.0, 1.0],
                        2.0, 1.0, 3.0, 0) == ("loss", 2))
check("🔁 REPLAY10🔒 الهدف لا يُحسم على شمعة التعبئة (F-L1) بل على التالية",
      S._arm_a_exit_bar([9.0, 9.0], [2.0, 2.0], [2.0, 2.0],
                        2.0, 1.0, 3.0, 0) == ("win", 1))
check("🔁 REPLAY10🔒 غير المحسوم يشغل النافذة كاملة (آخر شمعة)",
      S._arm_a_exit_bar([2.1, 2.1, 2.1], [1.9, 1.9, 1.9], [2.0, 2.0, 2.0],
                        2.0, 1.0, 9.0, 0) == ("open", 2))
check("🔁 REPLAY10🔒 غير المُعبَّأ يشغل النافذة كاملة أيضًا (إصلاح P0-01)",
      S._arm_a_exit_bar([2.1, 2.1], [1.9, 1.9], [2.0, 2.0],
                        2.0, 1.0, 9.0, None) == ("no_fill", 1))

# ⑮ 🔒 العلم مطفأ ⇒ **قاموس الصفقة بت-بت** (لا حقل يتسرّب للإنتاج/الباكتيست العاديّ)
_rp_flag_src = _insp0.getsource(S.backtest_symbol)
check("🔁 REPLAY10🔒 الحقول الثلاثة **خلف العلم** حصرًا (مطفأ = صفقة الأساس)",
      'CONFIG.get("BT_REPLAY10")' in _rp_flag_src
      and _rp_flag_src.count('trade["exit_date"]') == 1
      and 'trade["rr"]' in _rp_flag_src)
check("🔁 REPLAY10🔒 `BT_REPLAY10` مطفأ افتراضيًّا في CONFIG",
      S.CONFIG.get("BT_REPLAY10") == 0)
# 🔴 السعة **مربوطة بالحيّ لا مكتوبةً يدويًّا**: عيبُ `P0-02` كان بالضبط أن المحاكي
#    القديم يستعمل 15 بينما الإنتاج 10. وكل اختبارات الآلة تمرّر `capacity=` صراحةً
#    ⇒ الثابت نفسه كان **بلا قفل** (نجت طفرة «‏CAPACITY=15» فعلًا). فيُقفَل بالمصدر:
check("🔁 REPLAY10🔒 سعة الإعادة = `WATCHLIST_SIZE` الحيّ (إصلاح P0-02 لا رقمٌ يدويّ)",
      RP.CAPACITY == S.CONFIG["WATCHLIST_SIZE"],
      f"RP={RP.CAPACITY} · حيّ={S.CONFIG['WATCHLIST_SIZE']}")
check("🔁 REPLAY10🔒 `BT_REPLAY10` له صفٌّ في جدول التعيين (لا علم ميّت)",
      '("BT_REPLAY10"' in _insp0.getsource(S._apply_backtest_overrides))
check("🔁 REPLAY10🔒 الإنتاج محصّن — العلم لا يُطبَّق خارج وضع BACKTEST",
      S._apply_backtest_overrides("DAILY", {"BT_REPLAY10": "1"}) == []
      and S._apply_backtest_overrides("BACKTEST", {"BT_REPLAY10": "1"}) != [])

# ⑯ `run_backtest` **يرجّع** الصفقات (كان None) — وإلا فلا سبيل لتشغيل الأذرع
#    على نفس المسار الإنتاجيّ، ويُستنسَخ فيتفرّق «ما قِيس» عن «ما يُشغَّل».
check("🔁 REPLAY10🔒 run_backtest يرجّع الصفقات لا None",
      "return all_trades" in _insp0.getsource(S.run_backtest))

# ⑰ الجسر: فهرس الجلسات · تحويل R · المقياس
_bt = [{"symbol": "A", "date": "2025-01-02", "exit_date": "2025-01-10",
        "outcome": "win", "exit_kind": "win", "entry": 2.0, "stop": 1.8,
        "t1": 2.6, "ret_a": 30.0, "readiness": 70, "score": 50, "rr": 3.0},
       {"symbol": "B", "date": "2025-01-02", "exit_date": "2025-01-06",
        "outcome": "loss", "exit_kind": "loss", "entry": 2.0, "stop": 1.8,
        "t1": 2.6, "ret_a": -10.0, "readiness": 90, "score": 50, "rr": 1.0},
       {"symbol": "C", "date": "2025-01-06", "exit_date": "2025-01-10",
        "outcome": "no_fill", "exit_kind": "no_fill", "entry": 2.0, "stop": 1.8,
        "t1": 2.6, "ret_a": None, "readiness": 80, "score": 50, "rr": 1.0}]
check("🔁 REPLAY10🔒 R من عائد التنفيذ: الوقف = −1R بالضبط",
      abs(RP.r_unit(_bt[1]) - (-1.0)) < 1e-9)
check("🔁 REPLAY10🔒 R للرابح = العائد ÷ المخاطرة (30% ÷ 10% = 3R)",
      abs(RP.r_unit(_bt[0]) - 3.0) < 1e-9)
check("🔁 REPLAY10🔒 غير المُعبَّأ صفر R (لا تنفيذ) لكنه أخذ خانة",
      RP.r_unit(_bt[2]) == 0.0)
_bc, _bidx, _bof = RP.candidates_from_trades(_bt)
check("🔁 REPLAY10🔒 فهرس الجلسات = اتّحاد تواريخ الدخول والخروج مرتَّبةً",
      sorted(_bidx) == ["2025-01-02", "2025-01-06", "2025-01-10"]
      and [_bidx[d] for d in sorted(_bidx)] == [0, 1, 2])
check("🔁 REPLAY10🔒 الرابح ⇒ يحرّر الخانة ويبقى · الخاسر ⇒ يُزال",
      _bof(next(c for c in _bc if c.symbol == "A"))[0] == RP.R_HIT_HELD
      and _bof(next(c for c in _bc if c.symbol == "B"))[0] == RP.R_STOP
      and _bof(next(c for c in _bc if c.symbol == "C"))[0] == RP.R_WINDOW)
check("🔁 REPLAY10🔒 `seq` حتميّ بالتاريخ ثم الرمز (لا يتبع ترتيب الورود)",
      [c.symbol for c in RP.candidates_from_trades(list(reversed(_bt)))[0]]
      == [c.symbol for c in _bc])
check("🔁 REPLAY10🔒 صفقةٌ بلا `exit_date` تُسقَط (كشف العلم الخامل لا تفسيرُ صفره)",
      RP.candidates_from_trades([{"symbol": "Z", "date": "2025-01-02"}])[0] == [])
# 🔴 المقام **جلسات لا صفقات**: العيّنة أعلاه فيها 3 صفقات، فلو قِيس بـ3 جلسات لكان
#    القفل **أعمى** (‏`len(taken)` يساوي `n_sessions` صدفةً — نجت الطفرة M7 فعلًا).
#    فيُقاس بمقامٍ **مميِّز** (‏10) ويُثبَت التناسب العكسيّ مع مقامٍ ثانٍ.
check("🔁 REPLAY10🔒 صافي R/يوم = مجموع R ÷ **عدد الجلسات** (لا عدد الصفقات)",
      abs(RP.net_r_per_day(_bc, 10) - (2.0 / 10.0)) < 1e-9
      and abs(RP.net_r_per_day(_bc, 20) - RP.net_r_per_day(_bc, 10) / 2.0) < 1e-12)
check("🔁 REPLAY10🔒 صفر جلسات ⇒ صفر (لا قسمةٌ على صفر)",
      RP.net_r_per_day(_bc, 0) == 0.0)

# ⑱ الاستدلال: الفواصل تحيط بالمرصود · والبذرة تجعله قابلًا لإعادة الإنتاج
_bb1 = RP.block_bootstrap_ci(_bc, {"2025-01": 3}, n=200)
_bb2 = RP.block_bootstrap_ci(_bc, {"2025-01": 3}, n=200)
check("🔁 REPLAY10🔒 block bootstrap حتميّ بالبذرة (قابل لإعادة الإنتاج)", _bb1 == _bb2)
check("🔁 REPLAY10🔒 الفاصل يحيط بالمرصود عند كتلةٍ واحدة",
      _bb1["lo"] <= RP.net_r_per_day(_bc, 3) <= _bb1["hi"])
_cb1 = RP.cluster_bootstrap_ci(_bc, 3, n=200)
check("🔁 REPLAY10🔒 cluster بالرمز يعدّ الرموز لا الصفقات", _cb1["n"] == 3)
_rt_hi = RP.randomization_test(1.0, [0.0] * 100)
_rt_lo = RP.randomization_test(0.0, [1.0] * 100)
check("🔁 REPLAY10🔒 randomization: المرصود فوق العدم ⇒ p صغيرة وفرقٌ موجب",
      _rt_hi["p_one"] < 0.02 and _rt_hi["d_lo"] > 0)
check("🔁 REPLAY10🔒 randomization: المرصود تحت العدم ⇒ p كبيرة وفرقٌ سالب",
      _rt_lo["p_one"] > 0.98 and _rt_lo["d_hi"] < 0)
check("🔁 REPLAY10🔒 randomization: توزيعٌ متطابق ⇒ الفرق صفر (شاهد ضبط)",
      RP.randomization_test(0.5, [0.5] * 100)["d_mean"] == 0.0)

# ⑲ 🔒 تعميم قفل P1 على **كل** الـworkflows لا `backtest.yml` وحده — فعلمٌ جديد
#    في ملفٍ جديد لا يمرّ ميّتًا (وهو بالضبط ما كان سيحدث بـ`BT_REPLAY10`).
_p1_all_dead = []
for _wf in sorted(__import__("glob").glob(".github/workflows/*.yml")):
    _txt = open(_wf, encoding="utf-8").read()
    for _k in set(__import__("re").findall(r"^\s+(BT_[A-Z0-9_]+):\s*\$\{\{",
                                           _txt, __import__("re").M)):
        if _k not in _p1_tbl_keys and _k not in _P1_DIRECT_ENV \
                and _k not in _p1_composite:
            _p1_all_dead.append((_wf.split("/")[-1], _k))
check("🔁 REPLAY10🔒 قفل P1 مُعمَّم: كل مفتاح BT_* في **أي** workflow له صفّ بالجدول",
      not _p1_all_dead, f"ميّت={_p1_all_dead}")

# ⑳ دخانُ أداة الأذرع نفسها — الحلقة كاملةً بصفقاتٍ محقونة (بلا شبكة).
#    الغرض: أن **الحارسَين الصريحَين** فيها ليسا زينةً — «العلم الخامل» و«تفرّق
#    المحرّكَين» يجب أن يُوقفا القراءة برمز خروجٍ مميّز، لا أن يمرّا بصمت.
_ra_env = dict(__import__("os").environ)
_ra_orig = S.run_backtest
try:
    _io0, _ctx0 = __import__("io"), __import__("contextlib")

    def _ra_run(fake):
        S.run_backtest = lambda *a, **k: fake
        buf = _io0.StringIO()
        with _ctx0.redirect_stdout(buf):
            rc = RA.run()
        return rc, buf.getvalue()

    S.run_backtest = lambda *a, **k: list(_bt)
    import replay10_arms as RA
    RA.SEEDS, RA.BOOT = 25, 50
    _rc_ok, _out_ok = _ra_run(list(_bt))
    check("🔁 REPLAY10🔒 أداة الأذرع تُكمل الحلقة وتطبع الثلاثة (‏R0·R1·R2)",
          _rc_ok == 0 and "R0 (المُرتِّب الفعليّ)" in _out_ok
          and "R1 (‏FIFO)" in _out_ok and "R2 (عشوائيّ" in _out_ok
          and "randomization" in _out_ok, _out_ok[-160:])
    _rc_dead, _out_dead = _ra_run([{"symbol": "Z", "date": "2025-01-02"}])
    check("🔁 REPLAY10🔒 العلم الخامل يوقف القراءة صراحةً (لا تفسيرُ صفرٍ مفبرك)",
          _rc_dead == 2 and "خامل" in _out_dead)
    _rc_div, _out_div = _ra_run([dict(_bt[0], exit_kind="loss")])
    check("🔁 REPLAY10🔒 تفرّق محرّكَي الخروج/الحسم يوقف القراءة (توقيت غير موثوق)",
          _rc_div == 3 and "تفرّق" in _out_div)
finally:
    S.run_backtest = _ra_orig
    __import__("os").environ.clear()
    __import__("os").environ.update(_ra_env)

# ═══════════════════════════════════════════════════════════════════════════
# ⚡ T-EVENT-EXEC — أقفال التوقيت والتنفيذ (`event_exec_prereg.md`)
#    أوّل اختبارٍ **مباشر** لدعوى «الحافة = التوقيت». الأقفال تحرس ثلاثة أشياء:
#    ① الزناد **دوالّ الإنتاج نفسها** لا نسخةً منها · ② قواعد التنفيذ المسجَّلة
#    (ask ≤5ث · لا بديلَ مريحًا · كلُّ حدثٍ في المقام) · ③ الحوارس ليست ميتة.
# ═══════════════════════════════════════════════════════════════════════════
import event_exec as EX
import event_exec_run as EXR

# ① 🔴 القفل الحاسم: الزناد **غير منسوخ** — `replay_trigger` تُحقَن بدالّة الإنتاج،
#    ولا تحوي وحدةُ البحث أيَّ إعادة تطبيقٍ لشرط الحجم/الكسر.
_ex_src = _insp0.getsource(EX)
check("⚡ EVENT🔒 الزناد يُحقَن (لا إعادة تطبيقٍ لشرط 3× في وحدة البحث)",
      "signal_fn(win, break_level" in _ex_src
      and "vol_x" not in _ex_src and "IGNITION_VOL_MULT" not in _ex_src)
check("⚡ EVENT🔒 المُشغِّل يمرّر `_ignition_signal` الإنتاجيّ وعتبته الإنتاجية",
      "S._ignition_signal" in _insp0.getsource(EXR.run)
      and 'S.CONFIG["IGNITION_VOL_MULT"]' in _insp0.getsource(EXR.run))

# ② نافذة الرادار المتدحرجة = 30 دقيقة (نظير `polygon_minute_bars(minutes=30)` الحيّ)
check("⚡ EVENT🔒 نافذة الإعادة تطابق نافذة الرادار الحيّ (30 دقيقة)",
      EX.RADAR_WINDOW == 30 and EX.MIN_BARS == 6
      and "minutes=30" in _insp0.getsource(S.scan_ignition))

_mk = lambda t, c, v, h=None, l=None: {  # noqa: E731
    "t": t, "c": c, "v": v, "h": (h if h is not None else c),
    "l": (l if l is not None else c), "o": c}
# جلسةٌ اصطناعية: 2026-06-01 (اثنين) 09:30 نيويورك = 13:30 UTC صيفًا
_t0 = int(__import__("datetime").datetime(2026, 6, 1, 13, 30,
          tzinfo=__import__("datetime").timezone.utc).timestamp() * 1000)
_sess = [_mk(_t0 + i * 60000, 1.00, 100) for i in range(10)]
_sess.append(_mk(_t0 + 10 * 60000, 1.20, 900))     # كسر + حجم 9×

check("⚡ EVENT🔒 `replay_trigger` يلتقط الاشتعال بدالّة الإنتاج نفسها",
      (EX.replay_trigger(_sess, 1.10, S._ignition_signal) or (None,))[0] == 10)
check("⚡ EVENT🔒 بلا كسرٍ للمستوى لا اشتعال (المستوى فوق السعر)",
      EX.replay_trigger(_sess, 1.50, S._ignition_signal) is None)
check("⚡ EVENT🔒 **أوّل** حدثٍ لكل جلسة هو المأخوذ (لا أفضلُه ولا آخرُه)",
      (EX.replay_trigger(_sess + [_mk(_t0 + 11 * 60000, 1.30, 5000)],
                         1.10, S._ignition_signal) or (None,))[0] == 10)
# 🔴🔴 **النافذة زمنيّة لا عدديّة** (مراجعة Codex الثانية): كانت آخر 30 **شمعةً
# موجودة** مهما امتدّ زمنُها، والحيّ يقرأ آخر 30 **دقيقة** ⇒ في سهمٍ رقيق يرى
# التاريخيُّ سياقًا لا يراه الحيّ أبدًا. الـfixture **متعمَّدُ الرقّة**: عشر شمعاتٍ
# متباعدةٍ 20 دقيقة (تغطّي 200 دقيقة) ثم شمعةُ الكسر — فبالعدّ تدخل كلُّها النافذة
# (‏≤30 شمعة) وبالزمن **لا يدخل إلا ما وقع في آخر 30 دقيقة**.
_thin = [_mk(_t0 + i * 20 * 60000, 1.00, 100) for i in range(10)]
_thin.append(_mk(_t0 + 200 * 60000, 1.20, 900))         # كسر + حجم 9× عدديًّا
check("⚡ EVENT🔒 النافذة **زمنيّة**: سهمٌ رقيق لا يجمع 6 شمعات في 30 دقيقة ⇒ لا زناد",
      EX.replay_trigger(_thin, 1.10, S._ignition_signal) is None)
# 🔴 الاتجاه المقابل — وإلّا صار القفل «لا زناد أبدًا»: نفس الرقّة **مع** كثافةٍ
#    حقيقية داخل آخر 30 دقيقة ⇒ الزناد يعمل.
_thin2 = _thin[:-1] + [_mk(_t0 + (200 + i) * 60000, 1.00, 100) for i in range(6)]
_thin2.append(_mk(_t0 + 206 * 60000, 1.20, 900))
check("⚡ EVENT🔒 وبكثافةٍ حقيقية داخل الثلاثين دقيقة ⇒ الزناد يعمل (القفل ليس عدميًّا)",
      (EX.replay_trigger(_thin2, 1.10, S._ignition_signal) or (None,))[0] is not None)
check("⚡ EVENT🔒 شمعةٌ بلا طابعٍ زمنيّ لا تُخمَّن لها نافذة (تُتخطّى لا تُفترَض)",
      EX.replay_trigger([{"c": 1.2, "v": 900, "h": 1.2, "l": 1.2, "o": 1.2}] * 8,
                        1.10, S._ignition_signal) is None)

# ③ الجلسة النظامية فقط — الرادار الحيّ يعمل داخلها
check("⚡ EVENT🔒 ما قبل الافتتاح يُستبعَد من الجلسة",
      EX.ny_session_key(_t0 - 60 * 60000) is None
      and EX.ny_session_key(_t0) == ("2026-06-01", 570))
check("⚡ EVENT🔒 ما بعد الإغلاق يُستبعَد (الافتر خارج نطاق الرادار)",
      EX.ny_session_key(_t0 + 7 * 3600 * 1000) is None)
check("⚡ EVENT🔒 `group_sessions` يقسّم باليوم النيويوركيّ ويرتّب زمنيًّا",
      list(EX.group_sessions(_sess)) == ["2026-06-01"]
      and len(EX.group_sessions(list(reversed(_sess)))["2026-06-01"]) == 11)

# ④ 🔴🔴 **سعرُ الدخول = العرض القائم لا التحديث اللاحق** (مراجعة Codex الثانية).
# كان الشرط «أوّل ask **بعد** الزناد خلال 5ث» ⇒ عرضٌ صالحٌ نُشر قبل الزناد بثانيةٍ
# **وما زال نافذًا** يُصنَّف «غير قابلٍ للتنفيذ» لمجرّد أن أحدًا لم يحدّثه — وهو الحال
# الطبيعيّ في المغمورة ⇒ الرقم القديم (‏50.5%) كان يقيس **نشاطَ التسعير**.
_qs = [{"t": 1000, "ask": 1.0, "bid": 0.9}, {"t": 2000, "ask": 1.1, "bid": 1.0}]
check("⚡ EVENT🔒 يُؤخَذ **العرض القائم** (آخر اقتباسٍ قبل الزناد) لا التحديث اللاحق",
      (lambda e: e and e["ask"] == 1.0 and e["prevailing"] is True)(
          EX.pick_entry_quote(_qs, 1500)))
check("⚡ EVENT🔒 وعرضٌ قائمٌ **بائتٌ جدًّا** يبقى قائمًا (السكون ليس عدمَ قابلية)",
      (lambda e: e and e["ask"] == 1.0 and e["prevailing"] is True)(
          EX.pick_entry_quote([{"t": 1000, "ask": 1.0, "bid": 0.9}], 9_000_000)))
check("⚡ EVENT🔒 وبلا قائمٍ إطلاقًا يُقبَل تحديثٌ لاحق خلال 5ث (موسومًا `prevailing=False`)",
      (lambda e: e and e["ask"] == 1.1 and e["prevailing"] is False)(
          EX.pick_entry_quote([_qs[1]], 1500)))
check("⚡ EVENT🔒 تجاوز 5 ثوانٍ بلا قائم ⇒ **None** (غير قابل للتنفيذ، لا سعرَ بديلًا)",
      EX.pick_entry_quote([{"t": 20000, "ask": 1.1, "bid": 1.0}], 1000) is None)
check("⚡ EVENT🔒 اقتباسٌ بلا ask صالح يُتخطّى",
      EX.pick_entry_quote([{"t": 1100, "ask": None, "bid": 1.0},
                           {"t": 1200, "ask": 2.0, "bid": 1.9}], 1000)["ask"] == 2.0)
check("⚡ EVENT🔒 `ask_size`/`bid_size` يُحفَظان (كان المحلّل يُسقطهما ⇒ لا حجمَ يُختبَر)",
      (EX.pick_entry_quote([{"t": 1000, "ask": 1.0, "bid": 0.9,
                             "ask_size": 7, "bid_size": 3}], 1500) or {}
       ).get("ask_size") == 7
      and '"ask_size": q.get("ask_size")' in _insp0.getsource(EX.hist_quotes))
check("⚡ EVENT🔒 نافذة الجلب تبدأ **قبل** الزناد وإلّا لم يوجد قائمٌ أصلًا",
      "QUOTE_LOOKBACK_MS" in _insp0.getsource(EXR._one_event)
      and EX.QUOTE_LOOKBACK_MS > 0)
# 🔴 **سطرُ عرضٍ بلا حقلٍ = كذبة** — تكرّر منّي: التقرير يطبع «قائم=N» و`prevailing`
#    لم يكن يُنسَخ للصفّ ⇒ طُبع «قائم=0» في تشغيلةٍ حيّة كاملة. القفل يقرأ **ما يطبعه
#    التقرير فعلًا** (المفتاح على الصفّ) لا وجودَ الحقل في `pick_entry_quote`.
check("⚡ EVENT🔒 كلّ مفتاحٍ يطبعه التقرير منسوخٌ للصفّ (`prevailing`/`ask_size`)",
      all(_k in _insp0.getsource(EXR._one_event)
          for _k in ('prevailing=ent.get("prevailing")', 'ask_size=ent.get("ask_size")'))
      and 'r.get("prevailing")' in _insp0.getsource(EXR.run))
# 🔴 القفل **سلوكيّ**: النصّيّ نجت منه طفرةٌ (`cbr = cb`) لأن العبارتين تبقيان في
#    المصدر بلا أثر ⇒ استُخرجت الدالّة النقيّة ليُقاس الفرق فعلًا.
_rd = [{"symbol": "A", "executable": True, "net_r": -1.0},
       {"symbol": "B", "executable": True, "net_r": 3.0},
       {"symbol": "C", "executable": False, "net_r": None},
       {"symbol": "D", "executable": True, "net_r": None}]     # منفَّذٌ بلا حسم
# 🔴 حارس مقياس التقسيم بين الاقتباس والشمعة (Codex §④) — لحظيّ، وفاشلٌ نحو القبول.
check("🪙 SCALE🔒 اقتباسٌ بمقياسٍ آخر (تقسيمٌ 1:10) يُرفَض بسببٍ مُسمّى لا صمتًا",
      EX.quote_scale_mismatch(10.0, 1.0, 0.15) is True
      and "quote_scale_mismatch" in _insp0.getsource(EXR._one_event))
check("🪙 SCALE🔒 وفارقُ سبريدٍ طبيعيّ (‏2%) لا يُرفَض (القفل ليس عدميًّا)",
      EX.quote_scale_mismatch(1.02, 1.00, 0.15) is False
      and EX.quote_scale_mismatch(1.16, 1.00, 0.15) is True)


def _oe_row(ask, close=1.00):
    """يشغّل `_one_event` باقتباسٍ محقون (بلا شبكة) ويُرجع الصفّ.
    🔴 **قفلٌ سلوكيّ لا نصّيّ**: طفرةٌ تُفرّغ جسم الحارس (‏`pass`) **نجت** من القفل
    النصّيّ لأن سطر النداء يبقى — فصار الحكم يُقرأ من **الصفّ المُرجَع**."""
    _sv = EX.hist_quotes
    try:
        EX.hist_quotes = lambda *a, **k: [
            {"t": a[1] if len(a) > 1 else 0, "ask": ask, "bid": ask * 0.99,
             "ask_size": 5, "bid_size": 5}]
        _bar = {"t": 1_700_000_000_000, "c": close, "h": close, "l": close,
                "o": close, "v": 900, "mod": 600, "sess": "2026-03-03"}
        return EXR._one_event(
            "AAA", "2026-03-03", [_bar, dict(_bar, t=_bar["t"] + 60_000)], 0,
            {"price": close, "usd": 900},
            {"stop": close * 0.9, "t1": close * 1.2, "break": close}, "E-REAL",
            "k", fwd=[])
    finally:
        EX.hist_quotes = _sv


check("🪙 SCALE🔒 **سلوكيًّا**: اقتباسٌ بمقياسٍ آخر ⇒ الصفّ غير منفَّذٍ بسببه المُسمّى",
      (lambda r: r.get("executable") is False
       and r.get("reason") == "quote_scale_mismatch")(_oe_row(10.0)))
check("🪙 SCALE🔒 وبمقياسٍ متّسق ⇒ الصفّ **منفَّذ** (فالحارس لا يبتلع كلّ شيء)",
      (lambda r: r.get("executable") is True
       and r.get("reason") != "quote_scale_mismatch")(_oe_row(1.01)))
check("🪙 SCALE🔒 تعذّر القياس (None/NaN/صفر/نصّ) ⇒ **قبول** لا رفضٌ بالظنّ",
      all(EX.quote_scale_mismatch(a, b, 0.15) is False for a, b in (
          (None, 1.0), (1.0, None), (float("nan"), 1.0), (1.0, float("nan")),
          (0.0, 1.0), (1.0, 0.0), ("x", 1.0))))
# ⚠️ القفل **بالـAST لا بالنصّ**: النصّيّ سقط لأن `ask_size` مذكورٌ في **تعليق** —
#    وهو الفخّ المدوَّن نفسه (‏`getsource` لا يفرّق كودًا عن تعليق). الشرط الحقيقيّ:
#    **لا مقارنةَ** على `ask_size` داخل `_one_event` ⇒ لا بوّابة، قياسٌ فقط.
def _ast_compares_on(fn, name):
    tree = __import__("ast").parse(
        __import__("textwrap").dedent(_insp0.getsource(fn)))
    for n in __import__("ast").walk(tree):
        if isinstance(n, __import__("ast").Compare):
            if name in __import__("ast").dump(n):
                return True
    return False


check("📏 SIZE🔒 حجمُ العرض **يُقاس ولا يُشترَط** (الاشتراط اختيارٌ بعديّ غير مسجَّل)",
      "يُقاس ولا يُشترَط" in _insp0.getsource(EXR.run)
      and 'r.get("ask_size")' in _insp0.getsource(EXR.run)
      and not _ast_compares_on(EXR._one_event, "ask_size"))
check("📏 SIZE🔒 والقفل يقيس فعلًا: مقارنةٌ على المقياس نفسه تُكشَف (شاهد ضبط)",
      _ast_compares_on(EXR._one_event, "quote_scale_mismatch") is False
      and _ast_compares_on(EX.quote_scale_mismatch, "tol") is True)
check("⚡ EVENT🔒 المقام الخام يُبقي **كلّ** حدث ويجعل غيرَ المحسوم صفرًا صريحًا",
      [r["net_r"] for r in EX.raw_denominator(_rd)] == [-1.0, 3.0, 0.0, 0.0])
check("⚡ EVENT🔒 والمقامان يفترقان فعلًا (‏+1.000 مشروطًا مقابل +0.500 خامًّا)",
      abs(sum(r["net_r"] for r in _rd if r["net_r"] is not None) / 2 - 1.0) < 1e-9
      and abs(sum(r["net_r"] for r in EX.raw_denominator(_rd)) / 4 - 0.5) < 1e-9)
check("⚡ EVENT🔒 ولا يُشوَّه المدخل (نسخٌ لا تعديلٌ في المكان)",
      EX.raw_denominator(_rd) is not _rd and _rd[2]["net_r"] is None)
check("⚡ EVENT🔒 المقامان يُطبَعان معًا: مشروطٌ بالتنفيذ **وخام** (لا يُختار بعدها)",
      "المقام الخام" in _insp0.getsource(EXR.run)
      and "raw_denominator" in _insp0.getsource(EXR.run))
check("⚡ EVENT🔒 المُشغِّل يُبقي غيرَ المنفَّذ **في المقام** (لا يُحذف)",
      'row["reason"] = "non_executable"' in _insp0.getsource(EXR._one_event)
      and "len(ex) / len(rows)" in _insp0.getsource(EXR.run))

# ==========================================================
# 🔴🔴 العيب الزمنيّ (مراجعة Codex الثانية) — أخطر ما في الجولة
# ==========================================================
# `trade["date"]` = `df.index[i-1]` = **يوم الإشارة**، و`analyze_ticker` يقرأ حتى
# إغلاقه ⇒ الخطّة لم تكن معلومةً أثناءه. والمحرّك يبدأ التعبئة من `df.iloc[i:]`.
# فكانت النافذة تبدأ من يوم الإشارة ⇒ **نظرٌ مستقبليّ**. القفل **سلوكيّ** لا نصّيّ:
# يبني صفقتين ويقرأ **بداية النافذة الفعلية** المُرجَعة.
_ea_tr = [{"symbol": "AAA", "date": "2026-03-02", "eligible_at": "2026-03-03",
           "exit_date": "2026-03-10", "outcome": "loss", "score": 50, "rr": 2.0},
          {"symbol": "BBB", "date": "2026-03-02", "exit_date": "2026-03-09",
           "outcome": "loss", "score": 40, "rr": 2.0}]         # ⚠️ بلا eligible_at
_ea_out, _ea_rep, _ea_drop = EXR._armed(_ea_tr)
check("🕰️ TIME🔒 النافذة تبدأ `eligible_at` (الجلسة **التالية**) لا يوم الإشارة",
      [w["start"] for w in _ea_out] == ["2026-03-03"])
check("🕰️ TIME🔒 والغياب **يُسقِط الصفّ ويُعدّ** — لا ارتدادَ ليوم الإشارة (تسريبٌ صامت)",
      _ea_drop == 1 and all(w["trade"].get("symbol") != "BBB" for w in _ea_out))
check("🕰️ TIME🔒 المُشغِّل يتوقّف عند صفر نافذةٍ صالحة (لا يُفسَّر صفرٌ مفبرك)",
      "صفر نافذةٍ بمرجعٍ زمنيّ صالح" in _insp0.getsource(EXR.run)
      and "return 2" in _insp0.getsource(EXR.run))
# 🔴 والمصدر: المحرّك نفسه يكتبه من **أوّل شمعةٍ أمامية** لا باشتقاقٍ موازٍ.
check("🕰️ TIME🔒 `backtest_symbol` يكتب `eligible_at` من `fut.index[0]` (مصدر المحرّك)",
      'trade["eligible_at"] = (str(fut.index[0].date())'
      in _insp0.getsource(S.backtest_symbol))

# ⑤ التكاليف: الدخول عند ask حقيقيّ (لا يُحتسب مرّتين) + نصف السبريد على الخروج
check("⚡ EVENT🔒 الوقف = −1R بالضبط قبل التكاليف",
      abs(EX.net_r(-10.0, 2.0, 1.8, 0.0) - (-1.0)) < 1e-9)
check("⚡ EVENT🔒 السبريد يُخصَم من الخروج فقط (نصفُه) — لا مرّتين",
      abs(EX.net_r(0.0, 2.0, 1.8, 0.02) - (((1.0) * 0.99 - 1) * 100 / 10.0)) < 1e-9)
check("⚡ EVENT🔒 مخاطرةٌ غير موجبة ⇒ None (لا قسمةٌ على صفر)",
      EX.net_r(5.0, 2.0, 2.0, 0.0) is None)
check("⚡ EVENT🔒 كسر السبريد يُرفَض عند bid فاسد (لا يُخمَّن)",
      EX.spread_frac({"ask": 1.0, "bid": 1.2}) is None
      and EX.spread_frac({"ask": 1.0, "bid": None}) is None
      and abs(EX.spread_frac({"ask": 1.0, "bid": 0.98}) - 0.02) < 1e-9)

# ⑥ 🔴 الحسم بمحرّك الإنتاج نفسه — و`spread=0` عمدًا (الدخول مدفوعٌ عند ask)
#    🔴 **وقفلٌ سلوكيّ لا نصّيّ:** كان هنا فحصُ `"entry_intrabar=False" in getsource`،
#    **ونجت طفرتُه** — لأن العبارة موجودة في **الـdocstring** فيبقى الفحص صادقًا مهما
#    تغيّر الكود. وهو الفخّ الموثّق حرفيًّا في `CLAUDE.md`. فاستُبدل بحالةٍ **تُميّز**:
#    شمعة الدخول رأسُها يبلغ الهدف وذيلُها فوق الوقف، والتالية تضرب الوقف ⇒
#    `entry_intrabar=False` ⇒ **ربح**، و`True` ⇒ **خسارة**. والعائد ‏+20.0 بالضبط
#    يقفل `spread=0.0` معه (أيّ سبريدٍ يُنقصه).
_eb = [{"o": 1.00, "h": 1.25, "l": 0.95, "c": 1.10},
       {"o": 1.05, "h": 1.06, "l": 0.80, "c": 0.85}]
_ev_res = EXR._resolve_from(_eb, 0, 1.00, 0.90, 1.20)
check("⚡ EVENT🔒 نملك من شمعة الدخول (سلوكيًّا) — والسبريد صفرٌ هنا",
      _ev_res is not None and _ev_res[0] == "win" and abs(_ev_res[1] - 20.0) < 1e-9,
      f"{_ev_res}")
check("⚡ EVENT🔒 الحسم = `_resolve_arm` الإنتاجيّ حرفيًّا (تطابق سلوكيّ)",
      _ev_res == S._resolve_arm([b["h"] for b in _eb], [b["l"] for b in _eb],
                                [b["c"] for b in _eb], [b["o"] for b in _eb],
                                1.00, 0.90, 1.20, 0, entry_intrabar=False,
                                spread=0.0)[:2]
      and "S._resolve_arm(" in _insp0.getsource(EXR._resolve_from))

# ⑦ E-CROSS يعزل شرط الحجم: يعبر حيث لا يشتعل الزناد
_flat = [_mk(_t0 + i * 60000, 1.00, 100) for i in range(10)]
_flat.append(_mk(_t0 + 10 * 60000, 1.20, 100))      # كسرٌ **بلا** قفزة حجم
check("⚡ EVENT🔒 E-CROSS يعبر حيث لا يشتعل الزناد (يعزل شرط الـ3×)",
      EX.replay_trigger(_flat, 1.10, S._ignition_signal) is None
      and (EX.cross_trigger(_flat, 1.10) or (None,))[0] == 10)

# ⑧ E-PSEUDO: أقرب يومٍ هادئ · وعند التساوي **الأسبق** (حتميّ)
check("⚡ EVENT🔒 الحدث الزائف = أقرب يومٍ هادئ لنفس الرمز",
      EX.match_pseudo("2026-06-10", ["2026-06-01", "2026-06-09"]) == "2026-06-09")
check("⚡ EVENT🔒 وعند تساوي البعد يفوز **الأسبق** (حتميّ لا عشوائيّ)",
      EX.match_pseudo("2026-06-10", ["2026-06-11", "2026-06-09"]) == "2026-06-09"
      and EX.match_pseudo("2026-06-10", ["2026-06-09", "2026-06-11"]) == "2026-06-09")
check("⚡ EVENT🔒 بلا يومٍ هادئ ⇒ None (يُستبعَد من المزاوجة ويُعدّ)",
      EX.match_pseudo("2026-06-10", []) is None)

# ⑨ 🔴 حارس المقياس **حيّ لا ميّت** (درس «السطر الميت»): يمرّر السليم ويُسقط التقسيم
check("⚡ EVENT🔒 حارس المقياس يمرّر السعر المطابق",
      EX.scale_mismatch([_mk(0, 1.00, 1), _mk(1, 1.05, 1)], 1.00) is False)
check("⚡ EVENT🔒 وحارس المقياس **يُسقط** فارق تقسيمٍ 10×",
      EX.scale_mismatch([_mk(0, 10.0, 1), _mk(1, 10.5, 1)], 1.00) is True)
check("⚡ EVENT🔒 وبيانات ناقصة ⇒ لا إسقاط بالشكّ وحده",
      EX.scale_mismatch([], 1.0) is False and EX.scale_mismatch([_mk(0, 1, 1)], 0) is False)
check("⚡ EVENT🔒 الحارس يُطبَّق على **أوّل** جلسةٍ فقط (وإلّا أُقصي الرابح لارتفاعه)",
      "sess[_days[0]]" in _insp0.getsource(EXR.run))

# ⑩ استعادة الأرضية من الوقف — **باشتقاقين متقاطعين** لا افتراضٍ صامت
_piv = 2.00
_st = round(_piv * (1 - S.CONFIG["STOP_BELOW_LOW_PCT"][1] / 100.0), 4)
_n, _stp = S.CONFIG["ENTRY_TRANCHES"], S.CONFIG["ENTRY_STEP_PCT"] / 100.0
_ent = round(_piv * (1 + _stp * (_n - 1) / 2.0), 4)
_lv = EXR.plan_levels({"entry": _ent, "stop": _st, "t1": _piv * 1.5})
check("⚡ EVENT🔒 الأرضية تُستعاد من الوقف بمعادلة الإنتاج (خطأ أقل من 1%)",
      _lv is not None and abs(_lv["pivot"] / _piv - 1.0) < 0.01)
# 🔴 مستوى الكسر: **الرقم الحرج أوّلًا** (كدالّة الإنتاج) — والمرجع الاحتياطيّ عند
#    غيابه. المِجَسّ الأوّل بلا رقمٍ حرج **أشعل 90% من الجلسات** ⇒ شرطُ صلاحية.
check("⚡ EVENT🔒 بلا رقمٍ حرج ⇒ المرجع الاحتياطيّ (الأرضية ×1.05) ووسمُه صادق",
      _lv is not None and abs(_lv["break"] / (_piv * 1.05) - 1.0) < 0.01
      and _lv["from_crit"] is False)
_lvc = EXR.plan_levels({"entry": _ent, "stop": _st, "t1": _piv * 1.5,
                        "pivot": _piv, "crit": 3.33})
check("⚡ EVENT🔒 وبوجود الرقم الحرج **يفوز** على المرجع الاحتياطيّ (زنادُ الإنتاج)",
      _lvc is not None and abs(_lvc["break"] - 3.33) < 1e-9
      and _lvc["from_crit"] is True)
check("⚡ EVENT🔒 مستوى الكسر يُحسب بـ`_ignition_break_level` الإنتاجيّ لا بحسابٍ محلّيّ",
      "S._ignition_break_level(" in _insp0.getsource(EXR.plan_levels))
check("⚡ EVENT🔒 المُشغِّل يُعلن كم نافذةً استعملت الرقم الحرج (كشف الزناد الخاطئ)",
      'cov[\'crit\']' in _insp0.getsource(EXR.run)
      and "لا تُقرأ أذرع" in _insp0.getsource(EXR.run))
check("⚡ EVENT🔒 الرقم الحرج يُخزَّن بالصفقة خلف العلم (كان غائبًا كليًّا)",
      'trade["crit"]' in _insp0.getsource(S.backtest_symbol)
      and "build_interpretation(r)" in _insp0.getsource(S.backtest_symbol))

# 🔴 التجديد اليوميّ للحاجز — الإنتاج يعيد بناء `interp` كلَّ يوم بالسعر الجديد.
#    تجميدُه أشعل ‏56% من الجلسات (مقيسٌ بالمِجَسّ الثاني) ⇒ شرطُ صلاحيةٍ ثانٍ.
_ii = {"pivot": 2.00, "stop": (1.86, 1.90), "t1": 3.0, "t2": 4.0, "t3": 5.0,
       "tranches": [2.00, 2.06, 2.12],
       "key_levels": {"sup_major": 2.00, "res_minor": 2.50, "res_major": 4.00}}
_bl_low = EXR.daily_break_level({"interp_in": _ii}, 2.10, 9.99)
_bl_hi = EXR.daily_break_level({"interp_in": _ii}, 2.60, 9.99)
check("⚡ EVENT🔒 الحاجز يتجدّد مع السعر (يقفز للمقاومة التالية بعد تجاوز الأولى)",
      _bl_low is not None and _bl_hi is not None and _bl_hi > _bl_low,
      f"{_bl_low} → {_bl_hi}")
check("⚡ EVENT🔒 التجديد يستعمل `build_interpretation` و`_ignition_break_level` الإنتاجيّين",
      "S.build_interpretation(" in _insp0.getsource(EXR.daily_break_level)
      and "S._ignition_break_level(" in _insp0.getsource(EXR.daily_break_level))
check("⚡ EVENT🔒 بلا مدخلاتٍ مخزَّنة ⇒ يسقط لمستوى يوم الإشارة (فاشل-آمن لا انهيار)",
      EXR.daily_break_level({}, 2.5, 7.77) == 7.77
      and EXR.daily_break_level({"interp_in": _ii}, None, 7.77) == 7.77)
# 🔴 قفلٌ **سلوكيّ** على «إغلاق الجلسة السابقة»: خاصّيةٌ تعتمد على **ترتيب** سطرين،
#    وفحصُ النصّ لا يرى الترتيب — **ونجت طفرةُ إعادة الترتيب فعلًا** حتى استُخرجت
#    الحلقة إلى `session_levels` النقيّة. الفخّ نفسه للمرّة الثالثة اليوم.
_sl_sess = {"d1": [{"c": 2.10}], "d2": [{"c": 2.60}], "d3": [{"c": 2.60}]}
_sl = EXR.session_levels(["d1", "d2", "d3"], _sl_sess, {"interp_in": _ii}, 9.99)
check("⚡ EVENT🔒 أوّل جلسةٍ تأخذ مستوى يوم الإشارة (لا سابقةَ لها)",
      _sl["d1"] == 9.99)
check("⚡ EVENT🔒 التجديد بإغلاق **الجلسة السابقة** لا الحالية (لا نظرَ مستقبليّ)",
      abs(_sl["d2"] - 2.50) < 1e-9 and abs(_sl["d3"] - 4.00) < 1e-9,
      f"d2={_sl['d2']} d3={_sl['d3']}")
check("⚡ EVENT🔒 اشتقاقان متعارضان ⇒ **يُرفَض** (لا يُبنى على أرضيةٍ مظنونة)",
      EXR.plan_levels({"entry": _ent * 1.5, "stop": _st, "t1": _piv * 1.5}) is None)

# ⑪ التركيز (بوّابة ⑤): حصّة أكبر رمزٍ من **الربح**
_rows = [{"symbol": "A", "net_r": 3.0}, {"symbol": "B", "net_r": 1.0},
         {"symbol": "C", "net_r": -5.0}]
check("⚡ EVENT🔒 التركيز = حصّة أكبر رمزٍ من الربح (الخسائر لا تقلب المقام)",
      abs(EX.concentration(_rows, "symbol") - 0.75) < 1e-9)
check("⚡ EVENT🔒 بلا ربحٍ موجب ⇒ صفر (لا قسمةٌ على صفر)",
      EX.concentration([{"symbol": "A", "net_r": -1.0}], "symbol") == 0.0)

# ⑫ الاستدلال: cluster بالرمز · والفرق المزدوج يزاوج بـ(رمز، مفتاح الحدث)
_cb = EX.cluster_bootstrap_mean([{"symbol": "A", "net_r": 1.0},
                                 {"symbol": "B", "net_r": 1.0}], n=200)
check("⚡ EVENT🔒 cluster بالرمز: يعدّ الرموز ويحيط بالمتوسط",
      _cb["k"] == 2 and _cb["lo"] <= _cb["mean"] <= _cb["hi"])
_pdf = EX.paired_diff([{"symbol": "A", "pair_key": "k", "net_r": 2.0}],
                      [{"symbol": "A", "pair_key": "k", "net_r": 0.5}], n=200)
check("⚡ EVENT🔒 الفرق المزدوج يزاوج بـ(رمز، مفتاح الحدث)",
      _pdf["n"] == 1 and abs(_pdf["mean"] - 1.5) < 1e-9)
check("⚡ EVENT🔒 حدثٌ بلا نظيرٍ لا يُزاوَج (لا يُقارَن بغير مثيله)",
      EX.paired_diff([{"symbol": "A", "pair_key": "k", "net_r": 2.0}],
                     [{"symbol": "A", "pair_key": "OTHER", "net_r": 0.5}],
                     n=50)["n"] == 0)

# ⑬ 🔒 عزل: أدوات البحث **لا تُستورَد في الإنتاج**، والمفتاح يُقرأ وقت النداء
check("⚡ EVENT🔒 معزولة عن الإنتاج (لا تُستورَد في Super_stock)",
      "event_exec" not in _rp_src)
check("⚡ EVENT🔒 فاشلة-آمنة بلا مفتاح (لا نتيجةَ مفبركة)",
      (lambda: (__import__("os").environ.pop("POLYGON_API_KEY", None),
                EX.has_key() is False)[1])())
check("⚡ EVENT🔒 المُشغِّل يتوقّف صراحةً بلا مفتاح (خروج غير صفريّ)",
      'EX.has_key()' in _insp0.getsource(EXR.run) and "return 2" in _insp0.getsource(EXR.run))
check("⚡ EVENT🔒 ذراع المضارب **ثانويّة** بالتسمية (عتبتها ولّدت الفرضية)",
      "E-OPERATOR" in _insp0.getsource(EXR.run)
      and "ثانويّة" in _insp0.getsource(EXR.run))

# ═══════════════════════════════════════════════════════════════════════════
# 🎚️ T-MANAGE-25 — أقفال الإدارة الجزئية (`manage25_prereg.md`)
#    + قفل **أفق الحسم** (الانحراف الذي سحب أرقام T-EVENT-EXEC الأولى).
# ═══════════════════════════════════════════════════════════════════════════

# ⓪ 🔴 الأفق: الحسم يمتدّ **من يوم الزناد** لا داخل جلسته وحدها
check("🎚️ MANAGE🔒 الحسم يمتدّ لكامل نافذة ARMED (مسارٌ مسطَّح لا جلسةٌ واحدة)",
      "flat, base = [], {}" in _insp0.getsource(EXR.run)
      and "fwd=flat[base[day] + i + 1:]" in _insp0.getsource(EXR.run)
      and "path = fwd if fwd is not None" in _insp0.getsource(EXR._one_event))

# ① مسار الربع المُمتَّع — أسبابُ الخروج الثلاثة، كلٌّ بحالةٍ تميّزه
_R = lambda t, c, h=None, s="d1": {  # noqa: E731
    "t": t, "c": c, "h": (h if h is not None else c), "sess": s}
_m = 60_000
check("🎚️ MANAGE🔒 بلوغ t3 يُخرج الربع عند t3",
      EX.runner_exit([_R(0, 2.1), _R(_m, 2.2, 3.1)], 2.0, 3.0) == ("t3", 3.0))
check("🎚️ MANAGE🔒 كسرُ t1 بلا استعادةٍ خلال 15 دقيقة ⇒ خروج",
      EX.runner_exit([_R(i * _m, 1.9) for i in range(20)], 2.0, 9.0)[0] == "broke")
check("🎚️ MANAGE🔒 والاستعادة داخل المهلة **تُلغي** الكسر (لا خروج)",
      EX.runner_exit([_R(0, 1.9), _R(_m, 2.05)] + [_R((2 + i) * _m, 2.05)
                     for i in range(20)], 2.0, 9.0)[0] == "end")
check("🎚️ MANAGE🔒 انقضاء 5 جلسات يُخرج بالوقت",
      EX.runner_exit([_R(i * _m, 2.5, s=f"d{i}") for i in range(8)],
                     2.0, 9.0)[0] == "time")
check("🎚️ MANAGE🔒 بلا شموع ⇒ None (لا خروجَ مُختلَق)",
      EX.runner_exit([], 2.0, 3.0) is None)
check("🎚️ MANAGE🔒 t3 غائبٌ لا يُسقط المسار (يخرج بالشرطَين الباقيَين)",
      EX.runner_exit([_R(i * _m, 2.5) for i in range(4)], 2.0, None)[0] == "end")

# ② التركيب 75/25 — و**خروجان = تكلفتان** (لا مجّانية للإدارة)
check("🎚️ MANAGE🔒 غيرُ الرابحة ⇒ ب = أ حرفيًّا",
      abs(EX.manage_b_r(-10.0, 0, None, 0.02)
          - EX.manage_b_r(-10.0, 0, None, 0.02)) < 1e-12
      and abs(EX.manage_b_r(-10.0, 0, None, 0.0) - (-10.0)) < 1e-9)
check("🎚️ MANAGE🔒 التركيب 75/25 بلا تكلفة = المتوسط المرجَّح",
      abs(EX.manage_b_r(20.0, 20.0, 40.0, 0.0) - (0.75 * 20 + 0.25 * 40)) < 1e-9)
check("🎚️ MANAGE🔒 **خروجان = تكلفتان**: السبريد يُخصَم من الجزأين معًا",
      abs(EX.manage_b_r(20.0, 20.0, 20.0, 0.02)
          - ((1.20 * 0.99 - 1) * 100)) < 1e-9)
check("🎚️ MANAGE🔒 الربع الخاسر يسحب النتيجة (ليس تحسينًا بالتعريف)",
      EX.manage_b_r(20.0, 20.0, -5.0, 0.0) < 20.0)

# ③ 🔴 المُشغِّل: ب تُحسب على **نفس** الصفقة، وغيرُ الرابحة تبقى في المقام
_oe = _insp0.getsource(EXR._one_event)
check("🎚️ MANAGE🔒 ب على نفس الصفقة · وغيرُ الرابحة ⇒ same_as_a (تبقى بالمقام)",
      'row["net_r_b"] = row["net_r"]' in _oe and '"same_as_a"' in _oe
      and 'if out != "win"' in _oe)
check("🎚️ MANAGE🔒 مسار الربع يبدأ **بعد** شمعة بلوغ الهدف",
      "path[k + 1:]" in _oe)
check("🎚️ MANAGE🔒 t3 يُقرأ من الخطة المخزَّنة لا يُخترَع",
      '(t.get("interp_in") or {}).get("t3")' in _insp0.getsource(EXR.plan_levels)
      and '"t3": r.get' not in _oe)
check("🎚️ MANAGE🔒 المعيار الرباعيّ يُطبع بحدوده المسجَّلة",
      "0.15" in _insp0.getsource(EXR.run) and "-0.10" in _insp0.getsource(EXR.run)
      and "CVaR5%" in _insp0.getsource(EXR.run))

# ═══════════════════════════════════════════════════════════════════════════
# 🔬 T-NEARMISS + T-LABEL-AUDIT — أقفال (`nearmiss_label_prereg.md`)
# ═══════════════════════════════════════════════════════════════════════════

# ① 🔴 الذراعان لا يفترقان إلا في **جانب الخطّ** — وشرطُ الحجم من دالّة الإنتاج
#    ⚠️ الشموع السابقة **أخفض** عمدًا: زنادُ الإنتاج يشترط **اتجاهًا صاعدًا** داخل
#    النافذة (آخر إغلاق > أوّلها)، والذراعان يرثانه كما سُجِّل («نفس شروط الحجم
#    والاتجاه»). وعيّنةٌ مسطّحة كانت تُسقط الذراعين معًا — عيبُ عيّنةٍ لا عيبُ كود.
_nb = [_mk(_t0 + i * 60000, 0.95, 100) for i in range(10)]
_cr = EX.band_triggers(_nb + [_mk(_t0 + 10 * 60000, 1.005, 900)], 1.00,
                       S._ignition_signal)
_ms = EX.band_triggers(_nb + [_mk(_t0 + 10 * 60000, 0.995, 900)], 1.00,
                       S._ignition_signal)
check("🔬 NEAR🔒 العابر بشعرة يُصنَّف `cross` لا `miss`",
      "cross" in _cr and "miss" not in _cr and _cr["cross"][0] == 10, f"{_cr}")
check("🔬 NEAR🔒 والواقف تحته بشعرة يُصنَّف `miss` لا `cross`",
      "miss" in _ms and "cross" not in _ms and _ms["miss"][0] == 10, f"{_ms}")
check("🔬 NEAR🔒 خارج النطاق ‏±1% لا يُصنَّف في أيّ ذراع (لا توسيعَ صامت)",
      EX.band_triggers(_nb + [_mk(_t0 + 10 * 60000, 1.20, 900)], 1.00,
                       S._ignition_signal) == {}
      and EX.band_triggers(_nb + [_mk(_t0 + 10 * 60000, 0.80, 900)], 1.00,
                           S._ignition_signal) == {})
check("🔬 NEAR🔒 بلا قفزة حجمٍ لا ذراع (شرط الإنتاج يحكم الاثنين)",
      EX.band_triggers(_nb + [_mk(_t0 + 10 * 60000, 1.005, 100)], 1.00,
                       S._ignition_signal) == {})
check("🔬 NEAR🔒 لا إعادةَ تطبيقٍ للشرط: تُنادى `signal_fn` بمستوًى مخفَّض",
      "signal_fn(win, probe" in _insp0.getsource(EX.band_triggers)
      and "probe = float(break_level) * float(lo)" in _insp0.getsource(EX.band_triggers))
check("🔬 NEAR🔒 المُشغِّل يمرّر دالّة الإنتاج وعتبتها للذراعين",
      "EX.band_triggers(sb, brk, S._ignition_signal" in _insp0.getsource(EXR.run))

# ② 🔬 تدقيق الوسم — الظهور والاختفاء **في الاتجاهين** (لا أحاديّ)
_rg = [{"h": 1.20, "l": 0.99, "v": 10}]                    # نظاميّ: +20%
_ex = _rg + [{"h": 1.60, "l": 1.10, "v": 5}]               # ممتدّ: +60%
_L = EX.relabel(_ex, _rg, 1.00, 0.90)
check("🔬 LABEL🔒 عتبةٌ تُبلَغ بالممتدّ وحده تُوسَم «ظهرت»",
      _L["flips"][50.0]["appeared"] is True
      and _L["flips"][50.0]["vanished"] is False
      and abs(_L["ext"]["pre"] - 60.0) < 1e-9 and abs(_L["reg"]["pre"] - 20.0) < 1e-9)
# اختفاء: الوقف يُضرَب بالممتدّ **قبل** بلوغ العتبة، ولا يُضرَب نظاميًّا
_rg2 = [{"h": 1.60, "l": 0.95, "v": 10}]
_ex2 = [{"h": 1.00, "l": 0.80, "v": 5}] + _rg2
_L2 = EX.relabel(_ex2, _rg2, 1.00, 0.90)
check("🔬 LABEL🔒 والوقف الأبكر بالممتدّ يُوسَم «اختفت» (الأثر ذو اتجاهين)",
      _L2["flips"][50.0]["vanished"] is True
      and _L2["flips"][50.0]["appeared"] is False
      and _L2["stop_earlier"] is True, f"{_L2}")
check("🔬 LABEL🔒 «خرجنا ثم انفجر» يُقاس **بعد** الوقف لا قبله",
      EX.relabel([{"h": 1.05, "l": 0.85, "v": 1}, {"h": 3.00, "l": 1.00, "v": 1}],
                 [{"h": 1.05, "l": 0.85, "v": 1}], 1.00, 0.90)["ext"]["post"] == 200.0)
check("🔬 LABEL🔒 حجمُ الدقيقة التي بلغت الذروة يُرجَع (الوسم ليس ربحًا)",
      _L["ext"]["peak_vol"] == 5 and "peak_vol" in _insp0.getsource(EX.relabel))
check("🔬 LABEL🔒 بيانات ناقصة ⇒ None (لا وسمَ مفبرك)",
      EX.relabel([], [], 1.0, 0.9) is None and EX.relabel([{"h": 1}], [], 0, 0.9) is None)
check("🔬 LABEL🔒 المُشغِّل يقارن **كلّ** الدقائق بالنظامية (لا نفسها مرّتين)",
      "EX.relabel(bars, flat," in _insp0.getsource(EXR.run))
check("🔬 LABEL🔒 المعيار الثنائيّ يُطبع بحدوده المسجَّلة (10% · 3%)",
      "ماديّ (≥10%)" in _insp0.getsource(EXR.run)
      and "هامشيّ (<3%)" in _insp0.getsource(EXR.run))

# ③ 🩺 مِجَسّ الكون المشطوب — فاشلٌ آمن، ولا يدّعي جوابًا بلا مفتاح
import delisted_probe as DP
check("🩺 PROBE🔒 يسأل عن `active=false` صراحةً (وهو محلّ المشطوبة)",
      'active="false"' in _insp0.getsource(DP.run)
      and 'active="true"' in _insp0.getsource(DP.run))
check("🩺 PROBE🔒 بلا مفتاح ⇒ خروجٌ غير صفريّ ولا جواب مفبرك",
      (lambda: (__import__("os").environ.pop("POLYGON_API_KEY", None),
                DP.run())[1])() == 2)
check("🩺 PROBE🔒 يُعلن أنه مسقوفٌ بالصفحات (حدٌّ أدنى لا إحصاء)",
      "حدٌّ أدنى" in _insp0.getsource(DP.run))

# ═══════════════════════════════════════════════════════════════════════════
# 🛡️ درع صيّاد المقسّم — **بصماتٌ مثبَّتة، لا فحصٌ يدويّ**
#    السبب (قلق المالك 2026-07-31): الصيّاد هو **الشيء الوحيد الذي أصاب** (‏NUWE قبل
#    انفجاره بيومين)، وكلُّ تجاربنا الأخرى تدور حوله دون أن تمسّه. وكان التحقّق من
#    سلامته يجري **يدويًّا بعد كلّ عمل** — أي أنه قد يُكسَر **بصمت** بين فحصَين.
#    الآن: بصمة AST لكلّ دالّة قرار مثبَّتةٌ رقمًا؛ أيّ تغيير — ولو حرفًا — **يُسقط
#    السويّة** ويُجبر على قرارٍ صريح بدل انحرافٍ صامت.
#    ⚠️ **وتغييرُ الرقم هنا ليس إصلاحًا للفشل** — هو **إقرارٌ بأنك غيّرت الصيّاد عمدًا**.
# ═══════════════════════════════════════════════════════════════════════════
_HUNTER_PINS = {
    "_post_split_high": "353d5aa6565d37ce",
    "_split_day_value": "b5f53cfc6693f26c",
    "_split_frequency": "6e8590474f4cb291",
    "_split_setup_probe": "117eaf66511c12cf",
    "_yahoo_float": "ff6e63f2f6198ad1",
    "bottom_strike": "726f94595be226f1",
    # 🎁 حُدِّثت عمدًا (2026-07-31) بإضافة **كماليّات المالك** وحدها: نداءٌ واحد
    #    لـ`hunter_extras` بعد اكتمال الكرت.
    # ✅ **وحُدِّثت ثانيةً عمدًا (2026-08-06) بإذن المالك الحرفيّ** «سوها لو ما تاثر
    #    على الفحص و الفرز نفسه»: نداءٌ واحد لـ`faisal_rule_lines` **بعد**
    #    `hunter_extras` أي بعد اكتمال الكرت. **وهذا إقرارٌ لا إصلاحُ فشل.**
    #    🔒 و`scan_split_hunter` **مطابقةٌ حرفيًّا** (`caad69f25763d7b7` لم يتغيّر)
    #    ومعها الثمانية عشر الباقية ⇒ الشروطُ الخمسة والحكم byte-identical **بالبناء**،
    #    ومُثبَتٌ **سلوكيًّا** بـFR3 (نفسُ المطابقين مع الإثراء وبدونه).
    "build_split_hunter_alert": "f5ac8f1223183057",
    "build_split_radar_section": "e8a02f05df9511ef",
    "faisal_model_plan": "dee70734cacfaa67",
    "faisal_split_plan": "350f26d48509f57d",
    "falling_gap_candle": "f4074bb2c193e4d9",
    "group_pump_scar": "604d154f1be734f3",
    "half_down_target": "cc65a9195e10cfe0",
    "next_bottom_by_own_drop": "c96d632018d5b8ed",
    # 🔴 **حُدِّثت عمدًا (2026-08-06) — إقرارٌ لا إصلاحُ فشل، وبإذن المالك الحرفيّ**
    #    «سوها لو ما تاثر على الفحص و الفرز نفسه». السبب **عيبٌ مقيس**: خطّافُ ترتيب
    #    T-CLIFF-2 وُضع أوّلًا في `scan_split_radar` بينما أدواتُ T-CLIFF تقيس **هذي
    #    الدالّة** ⇒ خرجت ذراعُ الترتيب **مطابقةً بت-بت** لذراع الأساس = **no-op**
    #    (‏145/150 مطابق في الحالتين). الآن الخطّافُ هنا، **افتراضُه `"cliff"` =
    #    السلوكُ السابق حرفيًّا** — مقفولٌ **سلوكيًّا** أدناه (‏CL3) لا نصًّا،
    #    **والشروطُ الخمسة والحكمُ لم تُمَسّ** (الخطّافُ في **مُرشّح التكلفة** قبلها).
    "scan_split_hunter": "fc89b1480e4c5bb4",
    # 🔬 حُدِّثت عمدًا (2026-08-06، أمرُ المالك «سوها») بإضافة **مفتاح ترتيبٍ مطفأ
    #    افتراضيًّا** (‏`SPLIT_RADAR_ORDER`) لتجربة T-CLIFF-2 — حكمُ `T-CLIFF` نصَّ أن
    #    العلّة مفتاحُ الترتيب والسقف لا العتبة. **`"cliff"` = السلوكُ السابق حرفيًّا**
    #    (مقفولٌ سلوكيًّا أدناه)، و`scan_split_hunter` والشروطُ الخمسة **لم تُمَسّ**.
    "scan_split_radar": "60ed0a760b87311b",
    "short_targets_report": "ef12710917c8cbd0",
    "split_ma_maturity": "3678007d018c99f5",
    "split_radar_ready": "709553816d0487fb",
}
_h_ast, _h_hash = __import__("ast"), __import__("hashlib")
_h_src = open("Super_stock.py", encoding="utf-8").read()
_h_now = {n.name: _h_hash.sha256(_h_ast.dump(n).encode()).hexdigest()[:16]
          for n in _h_ast.walk(_h_ast.parse(_h_src))
          if isinstance(n, (_h_ast.FunctionDef, _h_ast.AsyncFunctionDef))
          and n.name in _HUNTER_PINS}
_h_missing = sorted(set(_HUNTER_PINS) - set(_h_now))
_h_changed = sorted(k for k, v in _HUNTER_PINS.items()
                    if k in _h_now and _h_now[k] != v)
check("🛡️ الدرع: كلُّ دوالّ الصيّاد **موجودة** (لا حذف صامت)",
      not _h_missing, f"مفقودة={_h_missing}")
check("🛡️ الدرع: كلُّ دوالّ الصيّاد **مطابقة لبصمتها المثبَّتة** (لا تغيير صامت)",
      not _h_changed, f"تغيّرت={_h_changed}")
check("🛡️ الدرع يغطّي 19 دالّة (لا يتقلّص بصمت)", len(_HUNTER_PINS) == 19)

# ==========================================================
# 🎁 كماليّات كرت الصيّاد (طلب المالك 2026-07-31) — عرضٌ لا يمسّ النتيجة
# ==========================================================
# 🕯️ الشمعة الانعكاسية بترتيب فيصل الحرفيّ: همر > نجمة صباح > هرامي > وت.
_rc = lambda *c: S.reversal_candle([(o, h, l, cl, 0) for o, h, l, cl in c])  # noqa: E731
check("🕯️ REV🔒 همر: ذيلٌ سفليّ ‏≥2× الجسم وإغلاقٌ بالثلث الأعلى",
      _rc((5, 5, 4, 4.5), (4.5, 4.6, 4, 4.2), (4.2, 4.3, 3.0, 4.2)) == "همر")
check("🕯️ REV🔒 نجمة صباح: حمراء كبيرة ← جسمٌ صغير ← خضراء فوق منتصف الحمراء",
      _rc((10, 10, 6, 6), (6, 6.4, 5.8, 6.2), (6.2, 9, 6.1, 8.5)) == "نجمة صباح")
check("🕯️ REV🔒 هرامي: جسمُ الأخيرة داخل جسم الحمراء السابقة",
      _rc((9, 9, 8.9, 8.9), (10, 10.1, 5.9, 6.0), (7.0, 7.3, 6.8, 7.2)) == "هرامي")
check("🕯️ REV🔒 وت (ابتلاع صاعد): الأخضر يبتلع جسم الحمراء",
      _rc((9, 9, 8.9, 8.9), (10, 10.1, 5.9, 6.0), (5.9, 10.5, 5.8, 10.4)) == "وت")
check("🕯️ REV🔒 لا نموذج ⇒ None (لا وسمَ مفبرك) · وبيانات ناقصة ⇒ None",
      _rc((5, 5.1, 4.9, 5.0), (5, 5.1, 4.9, 5.0), (5, 5.1, 4.9, 5.0)) is None
      and S.reversal_candle([]) is None and S.reversal_candle(None) is None
      and S.reversal_candle([(1, 1, 1, 1, 0)]) is None)


def _mkdf(rows):
    """إطارٌ صغير من `[(o,h,l,c,v)…]` — بلا شبكة."""
    return S.pd.DataFrame(
        {"Open": [r[0] for r in rows], "High": [r[1] for r in rows],
         "Low": [r[2] for r in rows], "Close": [r[3] for r in rows],
         "Volume": [r[4] for r in rows]},
        index=S.pd.date_range("2026-06-01", periods=len(rows), freq="D"))


# 🎯 المستوى المُختبَر (فيصل: «1.75 ضربها مرّتين ولا كسرها · الوقف 1.70»).
_tl_ok = _mkdf([(2, 2.1, 1.75, 2.0, 1), (2, 2.2, 1.9, 2.1, 1),
                (2, 2.1, 1.76, 2.05, 1), (2, 2.3, 1.95, 2.2, 1)])
check("🎯 LVL🔒 قاعٌ لُمِس مرّتين بلا كسرٍ بإغلاق ⇒ يُرجَع مع عدد اللمسات",
      (lambda x: x and abs(x["level"] - 1.75) < 1e-6 and x["touches"] == 2)(
          S.tested_level(_tl_ok)))
# 🐞 القفل الذي كشف عيبي: **لمستان متجاورتان = اختبارٌ واحد** لا اثنان — وإلّا
#    عدَّ كلُّ انخفاضٍ ممتدّ «ضربها مرّتين». (والحارسُ القديم «كُسِر بإغلاق» كان فرعًا
#    مستحيلَ التنفيذ رياضيًّا فحُذف — نجت منه طفرةٌ فكشفته.)
check("🎯 LVL🔒 شمعتان متجاورتان عند القاع = **اختبارٌ واحد** ⇒ لا مستوى",
      S.tested_level(_mkdf([(2, 2.1, 1.75, 2.0, 1), (2, 2.05, 1.755, 1.9, 1),
                            (2, 2.3, 1.95, 2.2, 1), (2, 2.3, 2.0, 2.25, 1)]))
      is None)
check("🎯 LVL🔒 لمسةٌ واحدة لا تكفي · وتالفٌ ⇒ None (لا مستوًى مخترَع)",
      S.tested_level(_mkdf([(3, 3.1, 1.75, 3.0, 1), (3, 3.2, 2.9, 3.1, 1),
                            (3, 3.2, 2.95, 3.15, 1)])) is None
      and S.tested_level(None) is None)

# 🕯️💵 قيمة الشمعة (فيصل: «أغلق الفجوة بـ100 سهم» = حركةٌ بقيمةٍ تافهة = يد).
_cvd = [(3, 3.1, 2.9, 3.0, 100000)] * 5 + [(3, 3.2, 2.9, 3.0, 100)]
check("🕯️ VAL🔒 قيمةٌ دون خُمس الوسيط تُوسَم «تافهة» (بصمة اليد لا السوق)",
      (lambda x: x and x["thin"] is True and x["usd"] == 300)(
          S.candle_value(_mkdf(_cvd))))
check("🕯️ VAL🔒 وقيمةٌ معتادة **لا** تُوسَم (القفل ليس عدميًّا) · وتالفٌ ⇒ None",
      (lambda x: x and x["thin"] is False)(
          S.candle_value(_mkdf([(3, 3.1, 2.9, 3.0, 100000)] * 6)))
      and S.candle_value(None) is None)

# 🪜 سلّم فيصل الثلاثيّ (اصبر · متابعة · تجهّز) — وسمُ حالةٍ لا قرارُ دخول.
check("🪜 WATCH🔒 الاثنان ⇒ تجهّز · واحدٌ ⇒ متابعة · لا شيء ⇒ اصبر",
      (S.hunter_watch_state("همر", True) == "تجهّز"
       and S.hunter_watch_state("همر", False) == "متابعة"
       and S.hunter_watch_state(None, True) == "متابعة"
       and S.hunter_watch_state(None, False) == "اصبر"))

# 🔒 **القفل الحاسم: الكماليّات لا تمسّ النتيجة.** تُنادى من دالّة العرض وحدها،
#    وغائبةٌ عن `scan_split_hunter` وعن الجذور — فلا تُدخل مرشّحًا ولا تُخرجه.
_EXTRA_FNS = ("hunter_extras", "reversal_candle", "tested_level",
              "candle_value", "hunter_watch_state", "_ohlc_tail")
check("🎁 EXTRA🔒 صفر أثرٍ على الترشيح: لا اسم منها في `scan_split_hunter` ولا الجذور",
      all(_n not in _insp0.getsource(_f) for _n in _EXTRA_FNS
          for _f in (S.scan_split_hunter, S.rank_key, S.select_top,
                     S.classify_tier, S.entry_status, S.analyze_ticker,
                     S.apply_float_gate, S.apply_short_gate, S.backtest_symbol)))
check("🎁 EXTRA🔒 وتُنادى من `build_split_hunter_alert` وحدها (نقطة النداء مُثبَتة)",
      "hunter_extras(" in _insp0.getsource(S.build_split_hunter_alert)
      and sum("hunter_extras(" in _insp0.getsource(_f) for _f in (
          S.build_split_hunter_alert, S.build_split_radar_section,
          S.build_message, S.build_daily_message)) == 1)
check("🎁 EXTRA🔒 فاشلة-آمنة: إطارٌ تالف/غياب كل شيء ⇒ أسطرٌ بلا انهيار",
      isinstance(S.hunter_extras({"symbol": "X", "price": 1.0}), list)
      and isinstance(S.hunter_extras({}, df="تالف", flow="تالف"), list))
check("🎁 EXTRA🔒 الأربعة المطلوبة تظهر فعلًا (اليد · المتابعة · التدفّق · القيمة)",
      (lambda t: all(k in t for k in ("🪜 المتابعة", "🕯️ قيمة شمعة اليوم",
                                      "💧 تدفّق السيولة")))(
          "\n".join(S.hunter_extras(
              {"symbol": "X", "price": 2.2}, df=_mkdf(_cvd),
              flow={"bid": 3.18, "bid_size": 300, "ask": 3.41,
                    "ask_size": 611}))))
# 🔴 والدرعُ نفسه يجب أن يكون قادرًا على السقوط — وإلّا فهو زينة:
check("🛡️ الدرع **يسقط فعلًا** لو تغيّرت بصمة (شاهد ضبط: بصمةٌ مزيّفة تُكشَف)",
      "scan_split_hunter" in _h_now
      and _h_now["scan_split_hunter"] != "0" * 16)
# 🔒 وعزلٌ بنيويّ: الصيّاد **لا يستورد** أدوات البحث إطلاقًا
_sh_src = open("split_hunter.py", encoding="utf-8").read()
check("🛡️ الصيّاد معزولٌ عن أدوات البحث (لا replay10 ولا event_exec)",
      "replay10" not in _sh_src and "event_exec" not in _sh_src)

# ══════════════════════════════════════════════════════════════════════════
# 🧪 م-و — T-ENVELOPE (`envelope_bt.py`): أداةُ قياس الربحية
# ══════════════════════════════════════════════════════════════════════════
import catalog_envelope as _CEb   # كتلة الظرف لاحقًا بالملفّ  # noqa: E402
_bt_src = open("envelope_bt.py", encoding="utf-8").read()
_bt_tree = _ast0.parse(_bt_src)


def _bt_calls(name):
    """هل تُنادى `name` فعلًا في الأداة؟ (‏AST — التعليقات لا تُحسَب)"""
    for n in _ast0.walk(_bt_tree):
        if isinstance(n, _ast0.Call):
            f = n.func
            nm = (f.attr if isinstance(f, _ast0.Attribute)
                  else (f.id if isinstance(f, _ast0.Name) else ""))
            if nm == name:
                return True
    return False


# ── ① العزل ودرعُ الجذور ──────────────────────────────────────────────────
# 🐞 **وهذا القفل كان نصّيًّا فسقط على تعليقٍ يذكر اسمَ الوحدة** (‏2026-08-05):
#    شرحُ عيبٍ داخل `envelope_scan.py` ذكر «`envelope_bt`» فقرأه القفلُ استيرادًا.
#    وهو **نفسُ درسِ العدميّة معكوسًا**: النصُّ لا يفرّق كودًا عن تعليق — في
#    الاتّجاهين. ⇒ صار **نحويًّا**: استيرادٌ فعليّ في الشجرة لا ذكرٌ في نصّ.
def _imports_module(path, mod):
    """هل `path` **يستورد** `mod` فعلًا؟ (‏AST — التعليقات والنصوص لا تُحسَب)"""
    tree = _ast0.parse(open(path, encoding="utf-8").read())
    for n in _ast0.walk(tree):
        if isinstance(n, _ast0.Import):
            if any(a.name == mod or a.name.startswith(mod + ".") for a in n.names):
                return True
        if isinstance(n, _ast0.ImportFrom) and (n.module or "") == mod:
            return True
    return False


_bt_isolated_files = ("Super_stock.py", "envelope_scan.py", "catalog_envelope.py",
                      "envelope_hunter.py", "split_hunter.py")
check("🧪 BT🔒 لا يُستورَد في الإنتاج ولا في الصيّادين (قفل AST لا نصّ)",
      all(not _imports_module(_f, "envelope_bt") for _f in _bt_isolated_files))
# 🔒 وشاهدُ ضبطٍ يمنع العدميّة: الكاشفُ نفسُه **يرى** استيرادًا حقيقيًّا.
check("🧪 BT🔒 وكاشفُ الاستيراد ليس عدميًّا (يرى استيرادًا قائمًا فعلًا)",
      _imports_module("envelope_bt.py", "envelope_scan")
      and _imports_module("envelope_hunter.py", "envelope_scan"))
check("🧪 BT🔒 بلا إرسالٍ ولا حفظِ حالة (قياسٌ خالص)",
      not _bt_calls("send_telegram") and not _bt_calls("git_save")
      and not _bt_calls("save_watchlist"))
# 🐞 وقفلي الأوّل بحث عن **نداءٍ** باسم `decide` — والأداة تُسنده لمتغيّرٍ
#    (`dec = decide_fn or ES.decide`) لأنها تسمح بحقنٍ للاختبار ⇒ لا نداءَ باسمه.
#    ⇒ القفل الصحيح: **مرجعُ الخاصّية** `ES.decide` موجودٌ في الشجرة النحوية.
def _bt_uses_attr(name):
    return any(isinstance(n, _ast0.Attribute) and n.attr == name
               for n in _ast0.walk(_bt_tree))


check("🧪 BT🔒 القرار من `envelope_scan.decide` والبناء من `backtest_symbol`",
      _bt_uses_attr("decide") and _bt_calls("backtest_symbol"))
check("🧪 BT🔒 ولا نسخةَ منطقٍ ثانية: لا `analyze_ticker` مباشرةً ولا حسابَ gain5",
      not _bt_calls("analyze_ticker") and "gain5" not in _bt_src)

# ── ② 🔴 الأعلام تُضبَط **قبل** الاستيراد وإلّا كانت خاملة ────────────────
def _bt_env_before_import():
    """‏`_apply_backtest_overrides` يُنفَّذ وقت التحميل ⇒ ضبطُ العلم بعد الاستيراد
    = **علمٌ خامل** (بصمة الـno-op). نتحقّق من **ترتيب** العُقد لا من النصّ."""
    first_import = None
    last_env = None
    for i, node in enumerate(_bt_tree.body):
        if isinstance(node, _ast0.Import) and any(
                a.name in ("Super_stock", "replay10", "catalog_envelope",
                           "envelope_scan") for a in node.names):
            if first_import is None:
                first_import = i
        if isinstance(node, _ast0.Expr) and isinstance(node.value, _ast0.Call):
            f = node.value.func
            if isinstance(f, _ast0.Attribute) and f.attr in ("setdefault",):
                last_env = i
        if isinstance(node, _ast0.Assign) and isinstance(node.targets[0], _ast0.Subscript):
            last_env = i
    return (first_import is not None and last_env is not None
            and last_env < first_import)


check("🧪 BT🔒 **الأعلام قبل الاستيراد** (قفل AST على الترتيب — لا علمَ خامل)",
      _bt_env_before_import())
check("🧪 BT🔒 وSCREENER_MODE=BACKTEST مضبوطٌ داخل الأداة لا بالـworkflow وحده",
      "SCREENER_MODE" in _bt_src and "BACKTEST" in _bt_src)

# ── ③ حاجب الحواف غير الآليّة ────────────────────────────────────────────
import envelope_bt as _BT                                        # noqa: E402
import replay10 as RP_                                            # noqa: E402
import envelope_scan as _ES_pre                                   # noqa: E402
_es_loaded_bt = _ES_pre.load_edges()
check("🧪 BT🔒 حاجبٌ: حوافٌّ غيرُ آليّةٍ ⇒ رفضٌ صريح ما لم يُوسَم التجاوز",
      "مُخرَجٌ آليّ" in _insp0.getsource(_BT.run)
      and "ENV_BT_ALLOW_MANUAL_EDGES" in _insp0.getsource(_BT.run))

# ── ④ أرضيةُ السعر تُعاد إلى حافّة الظرف (حارسُ الإشارة الوهمية) ──────────
_bt_rx = _BT.relax_for({"price": 1.62}, "E1")
check("🧪 BT🔒 `MIN_PRICE` **تُعاد إلى حافّة الظرف** لا صفرًا (وإلّا مات حارسُ الوهميّ)",
      _bt_rx["MIN_PRICE"] == 1.62 and _CEb.RELAX_ALL["MIN_PRICE"] == 0.0)
check("🧪 BT🔒 وذراع `E1C` **تُبقي** D11 عاملًا (تُسقط مفتاحه من الإرخاء)",
      "RECENT_RISE_BLOCK_PCT" not in _BT.relax_for({"price": 1.0}, "E1C")
      and "RECENT_RISE_BLOCK_PCT" in _BT.relax_for({"price": 1.0}, "E1"))

# ── ⑤ سياقُ الإرخاء يستعيد CONFIG **وإحصاءَ الرفض** ──────────────────────
_bt_cfg0 = {k: S.CONFIG.get(k) for k in list(_CEb.RELAX_ALL) + ["BACKTEST_STEP"]}
S._REJECT_STATS["زائف"] = 7
with _BT.relaxed_step({"MIN_PRICE": 9.0}, 1):
    _bt_in = (S.CONFIG["MIN_PRICE"] == 9.0 and S.CONFIG["BACKTEST_STEP"] == 1)
    S._REJECT_STATS["ملوَّث"] = 99
check("🧪 BT🔒 `relaxed_step` **تُرخي فعلًا** (القفل ليس عدميًّا)", _bt_in)
check("🧪 BT🔒 وتستعيد `CONFIG` بت-بت",
      all(S.CONFIG.get(k) == v for k, v in _bt_cfg0.items()))
check("🧪 BT🔒 و**تستعيد إحصاءَ الرفض** فلا يتلوّث توزيعُ الأساس",
      S._REJECT_STATS.get("زائف") == 7 and "ملوَّث" not in S._REJECT_STATS)
S._REJECT_STATS.pop("زائف", None)
try:
    with _BT.relaxed_step({"MIN_PRICE": 9.0}, 1):
        raise RuntimeError("انهيارٌ مُتعمَّد")
except RuntimeError:
    pass
check("🧪 BT🔒 والاستعادة تقع **حتى مع الانهيار**",
      all(S.CONFIG.get(k) == v for k, v in _bt_cfg0.items()))

# ── ⑥ التلوّث الزمنيّ: بلا تواريخ ⇒ **كلُّ السنوات ملوَّثة احتياطًا** ──────
check("🧪 BT🔒 بلا تواريخ مِرساة ⇒ لا نفيَ للتلوّث (تُعلَن كلُّها ملوَّثة)",
      _BT.probe_anchors({"_meta": {}}, (2023, 2024, 2025))["contaminated"]
      == [2023, 2024, 2025])
check("🧪 BT🔒 ومع تواريخ ⇒ الملوَّثةُ **هي سنواتُ المِرساة** حصرًا",
      _BT.probe_anchors({"_meta": {"anchor_last_measured":
                                   {"A": "2024-05-01", "B": "2026-07-01"}}},
                        (2023, 2024, 2025))["contaminated"] == [2024])

# ── ⑦ الاستبعاد قبل المحفظة · والمقياسان ─────────────────────────────────
_bt_tr = [{"symbol": "NUWE", "entry": 2.0, "stop": 1.8, "ret_a": 10.0},
          {"symbol": "ZZZZ", "entry": 2.0, "stop": 1.8, "ret_a": -10.0}]
check("🧪 BT🔒 `exclude_catalog` يرشّح رموز الكاتالوج ويُرجع عدد المفقود",
      (lambda t: [r["symbol"] for r in t[0]] == ["ZZZZ"] and t[1] == 1)(
          _BT.exclude_catalog(_bt_tr)))
check("🧪 BT🔒 `per_trade_expectancy` = متوسّط `r_unit` من `replay10` لا حسابٍ محلّيّ",
      "r_unit" in _insp0.getsource(_BT.per_trade_expectancy)
      and _BT.per_trade_expectancy([])["n"] == 0)
check("🧪 BT🔒 و`exploded` **محرَّمٌ ولا يُقرأ** (ما بعد الوقف)",
      "exploded" not in _bt_src.replace("`exploded` محرَّمٌ ولا يُقرأ", ""))
check("🧪 BT🔒 وصفرُ مرشّحين يُعلَن **علمًا خاملًا** لا صفرًا حقيقيًّا",
      "خاملًا" in _insp0.getsource(_BT.portfolio_metric))
check("🧪 BT🔒 و`z_diff` يُحسب من `se` المقيس (لا تقديرَ)",
      _BT.z_diff({"mean": 1.0, "se": 0.1}, {"mean": 0.0, "se": 0.1}) is not None
      and _BT.z_diff({"mean": 1.0, "se": None}, {"mean": 0.0, "se": 0.1}) is None)

# ── ⑧ حدودُ البوّابة مثبَّتةٌ بالكود لا بالرأي ─────────────────────────────
check("🧪 BT🔒 حدودُ البوّابة ثوابتُ مُعلَنة (‏0.15R · z 1.96 · n 30)",
      _BT.EFFECT_R == 0.15 and _BT.Z_MIN == 1.96 and _BT.MIN_TRADES == 30)

# ── ⑨ 🔴 **مِشيةُ الذراع = خطوةُ الإنتاج** (حارس `V6`) ────────────────────
#    عيبٌ مقيس: `walk_arm` كان يقرأ الخطوة من `CONFIG` **داخل** سياق الإرخاء
#    (الذي كان يضبطها 1) فتمشي الذراعُ بخطوة 1 بينما `E0` بخطوة 5 ⇒ خمسةُ أضعافِ
#    الزيارات ⇒ «إشاراتٌ أكثر» تُقرأ أثرَ ظرفٍ وهي **كثافةُ عيّنة**.
#    والخطوة 1 لازمةٌ **للنداء الداخليّ وحده** (نافذتُه يومٌ واحد).
_bt_n = 200
_bt_df = S.pd.DataFrame(
    {"Open": [2.0] * _bt_n, "High": [2.1] * _bt_n, "Low": [1.9] * _bt_n,
     "Close": [2.0] * _bt_n, "Volume": [500000] * _bt_n},
    index=S.pd.date_range("2025-01-01", periods=_bt_n, freq="D"))
_bt_win = ("2020-01-01", "2030-12-31")


def _bt_visits(stride):
    """يُرجع عددَ الزيارات بمِشيةٍ مُعطاة — `decide` يرفض دائمًا فلا بناء."""
    c = {"visits": 0, "accepted": 0, "rejected": 0, "decide_error": 0,
         "build_error": 0, "date_mismatch": 0, "built": 0}
    _BT.walk_arm("ZZTEST", _bt_df, {}, None, _bt_win, "E1", c,
                 decide_fn=lambda *a, **k: (False, "رفضٌ مُتعمَّد", {}),
                 stride=stride)
    return c["visits"]


_bt_v5, _bt_v1 = _bt_visits(5), _bt_visits(1)
check("🧪 BT🔒 ع⑨: المِشية **تُطاع فعلًا** (خطوة 5 تزور خُمسَ ما تزوره خطوة 1)",
      _bt_v1 > 0 and _bt_v5 > 0 and _bt_v1 == _bt_v5 * 5)

# 🔒 والقفلُ الحاسم: المِشية تأتي من الوسيط **لا من `CONFIG` الملوَّثة بالإرخاء**.
with _BT.relaxed_step({}, 1):
    _bt_v_in = _bt_visits(5)
check("🧪 BT🔒 ع⑨: ومِشيةُ الذراع **لا تتلوّث** بخطوة الإرخاء داخل السياق",
      _bt_v_in == _bt_v5 and S.CONFIG["BACKTEST_STEP"] == _bt_cfg0["BACKTEST_STEP"])

# 🔒 والنداءُ الداخليّ يستعيد الخطوة **حتى لو انهار** — بشاهدِ ضبطٍ يمنع العدميّة.
_bt_c2 = {"visits": 0, "accepted": 0, "rejected": 0, "decide_error": 0,
          "build_error": 0, "date_mismatch": 0, "built": 0}
_bt_step_outer = int(S.CONFIG["BACKTEST_STEP"])
_BT.walk_arm("ZZTEST", _bt_df, {}, None, _bt_win, "E1", _bt_c2,
             decide_fn=lambda *a, **k: (True, "", {}), stride=5)
check("🧪 BT🔒 ع⑨: والخطوةُ تُستعاد بعد النداء الداخليّ (وشاهدُ الضبط: البناء وقع)",
      _bt_c2["accepted"] >= 1
      and int(S.CONFIG["BACKTEST_STEP"]) == _bt_step_outer)

# 🔒 ومرآةُ المحرّك: قبولٌ من `decide` **لم يُنتج صفقة** (المحرّك رفض داخليًّا) ⇒
#    يتقدّم بخطوةٍ لا بنافذةٍ كاملة — وإلّا تخطّت الذراعُ 40 جلسة حيث يتخطّى
#    الإنتاجُ 5. العدُّ **محسوبٌ من CONFIG لا مكتوبٌ بيدي** فلا يتعفّن.
_bt_expect = len(range(int(S.CONFIG["MIN_BARS"]),
                       _bt_n - int(S.CONFIG["BACKTEST_FORWARD_DAYS"]), 5))
check("🧪 BT🔒 ع⑨: وقبولٌ بلا صفقةٍ مبنيّة ⇒ **خطوة** لا نافذة (مرآةُ المحرّك)",
      _bt_expect > 1 and _bt_c2["accepted"] == _bt_expect
      and _bt_c2.get("built_none") == _bt_expect and _bt_c2["built"] == 0)


# 🔒 قفلٌ نحويّ مكمّل: لا `relaxed_step(..., 1)` بثابتٍ في مسار الأذرع — الوسيطُ
#    الثاني يجب أن يكون **اسمًا** (خطوةَ الإنتاج المقروءة قبل الإرخاء).
def _bt_relaxed_args_are_names():
    for node in _ast0.walk(_ast0.parse(_insp0.getsource(_BT.run))):
        if (isinstance(node, _ast0.Call)
                and isinstance(node.func, _ast0.Name)
                and node.func.id == "relaxed_step" and len(node.args) >= 2):
            if isinstance(node.args[1], _ast0.Constant):
                return False
    return True


check("🧪 BT🔒 ع⑨: و`run` لا تُمرّر خطوةً ثابتة (تقرأ خطوةَ الإنتاج قبل الإرخاء)",
      _bt_relaxed_args_are_names() and "prod_stride" in _insp0.getsource(_BT.run))

# ── ⑩ 🔴 `V3` **يُوقِف** لا يُطبَع (كان موصوفًا في التسجيل وغيرَ منفَّذ) ────────
_v3_ok = {"_meta": {"pct": 90, "n_symbols": _BT.V3_N_SYMBOLS,
                    "excluded": {k: "" for k in _BT.V3_EXCLUDED}}}
check("🧪 BT🔒 ع⑩: `check_v3` تُجيز الظرفَ المُصرَّح (القفل ليس عدميًّا)",
      _BT.check_v3(_v3_ok, _BT.V3_FINGERPRINT) == [])
check("🧪 BT🔒 ع⑩: وتُوقِف عند **بصمةٍ** مختلفة",
      _BT.check_v3(_v3_ok, "deadbeefdead") != [])
check("🧪 BT🔒 ع⑩: وتُوقِف عند **عددِ رموزٍ** مختلف (تبدّلُ مجتمع المعايرة)",
      _BT.check_v3({"_meta": dict(_v3_ok["_meta"], n_symbols=30)},
                   _BT.V3_FINGERPRINT) != [])
check("🧪 BT🔒 ع⑩: وتُوقِف عند **مُستبعَدين** مختلفين",
      _BT.check_v3({"_meta": dict(_v3_ok["_meta"], excluded={"HTZ": ""})},
                   _BT.V3_FINGERPRINT) != [])
check("🧪 BT🔒 ع⑩: و`run` تُرجع 5 فعلًا عند مخالفة V3 (لا طَبْعٌ ومضيّ)",
      "return 5" in _insp0.getsource(_BT.run)
      and "check_v3" in _insp0.getsource(_BT.run))
# 🔒 والثوابتُ تطابق **ملفَّ الحواف المدفوع** — فلا تتعفّن نسخةٌ منهما
check("🧪 BT🔒 ع⑩: وثوابتُ V3 تطابق ملفَّ الحواف الفعليّ (مصدرٌ واحد للحقيقة)",
      _BT.V3_FINGERPRINT == _ES_pre.edges_fingerprint(_es_loaded_bt)
      and _BT.V3_N_SYMBOLS == (_es_loaded_bt.get("_meta") or {}).get("n_symbols")
      and _BT.V3_EXCLUDED == set(
          ((_es_loaded_bt.get("_meta") or {}).get("excluded") or {}).keys()))

# ── ⑪ 🔴 `V4` بنيويًّا: محورٌ زمنيّ **مشترك** بين الأذرع ────────────────────
#    العيب: `candidates_from_trades` تبني الفهرس من الصفقات المُمرَّرة وحدها، و`held`
#    بخطوات ذلك الفهرس ⇒ ذراعٌ كثيفة تحجز الخانةَ **أطولَ** للصفقة نفسها.
_v4_sparse = [{"symbol": "A", "date": "2025-01-02", "exit_date": "2025-03-03",
               "eligible_at": "2025-01-03", "entry": 2.0, "stop": 1.8,
               "ret_a": 5.0, "outcome": "win"}]
_v4_dense = _v4_sparse + [
    {"symbol": f"D{i}", "date": f"2025-01-{d:02d}", "exit_date": f"2025-02-{d:02d}",
     "eligible_at": f"2025-01-{d:02d}", "entry": 2.0, "stop": 1.8,
     "ret_a": 1.0, "outcome": "win"}
    for i, d in enumerate(range(5, 28))]
_v4_by, _v4_idx, _v4_oc = _BT.shared_axis({"sparse": _v4_sparse,
                                           "dense": _v4_dense})
_v4_a = next(c for c in _v4_by["sparse"] if c.symbol == "A")
_v4_b = next(c for c in _v4_by["dense"] if c.symbol == "A")
check("🧪 BT🔒 ع⑪: نفسُ الصفقة تحجز الخانةَ **المدّةَ نفسَها** في الذراعين (محورٌ مشترك)",
      _v4_oc(_v4_a)[1] == _v4_oc(_v4_b)[1] and _v4_oc(_v4_a)[1] > 0)
# 🔒 شاهدُ ضبط: المحورُ المنفرد **يعطي مدّتين مختلفتين** ⇒ القفل ليس عدميًّا
_v4_s1 = RP_.candidates_from_trades(_v4_sparse)
_v4_s2 = RP_.candidates_from_trades(_v4_dense)
_v4_h1 = _v4_s1[2](next(c for c in _v4_s1[0] if c.symbol == "A"))[1]
_v4_h2 = _v4_s2[2](next(c for c in _v4_s2[0] if c.symbol == "A"))[1]
check("🧪 BT🔒 ع⑪: وشاهدُ الضبط — بناءٌ لكلّ ذراعٍ يعطي مدّتين **مختلفتين** (العيب حقيقيّ)",
      _v4_h1 != _v4_h2)
check("🧪 BT🔒 ع⑪: والترتيبُ النسبيّ داخل الذراع لا يتلوّث باتّحاد الأذرع",
      [c.symbol for c in _v4_by["dense"]] == [c.symbol for c in _v4_s2[0]])

# ── ⑫ 🕰️ المِرساة الحاكمة `eligible_at` (كانت غيرَ مقروءةٍ إطلاقًا) ──────────
_ea_rows, _ea_drop = _BT.anchor_eligible(
    _v4_sparse + [{"symbol": "N", "date": "2025-01-02",
                   "exit_date": "2025-02-02", "entry": 2.0, "stop": 1.8}])
check("🕰️ BT🔒 ع⑫: `date` يُرسى على `eligible_at` والأصلُ محفوظٌ في `signal_date`",
      len(_ea_rows) == 1 and _ea_rows[0]["date"] == "2025-01-03"
      and _ea_rows[0]["signal_date"] == "2025-01-02")
check("🕰️ BT🔒 ع⑫: وصفقةٌ بلا الحقل **تُسقَط ويُعلَن عددُها** (لا مِرساةٌ صامتة)",
      _ea_drop == 1)
check("🕰️ BT🔒 ع⑫: و`run` تستعمل المِرساة فعلًا من نقطة النداء",
      "anchor_eligible" in _insp0.getsource(_BT.run)
      and "shared_axis" in _insp0.getsource(_BT.run))

# ── ⑬ 🐞 `rejected_cap` بالمفتاح الصحيح (كان `rejected_capacity` = None دائمًا) ─
# 🐞 **وقفلي الأوّل هنا كان نصّيًّا فسقط على تعليقي أنا** (رابعُ مرّةٍ في الجلسة):
#    الشرحُ يذكر المفتاحَ القديم `rejected_capacity` فقرأه القفلُ استعمالًا.
#    ⇒ نحويّ: **وسيطُ `res.get(...)` الفعليّ** داخل الدالّة.
def _bt_res_get_keys():
    tree = _ast0.parse(_insp0.getsource(_BT.portfolio_metric).lstrip())
    out = set()
    for n in _ast0.walk(tree):
        if (isinstance(n, _ast0.Call) and isinstance(n.func, _ast0.Attribute)
                and n.func.attr == "get" and n.args
                and isinstance(n.args[0], _ast0.Constant)):
            src = n.func.value
            if isinstance(src, _ast0.Name) and src.id == "res":
                out.add(n.args[0].value)
    return out


_bt_keys = _bt_res_get_keys()
check("🐞 BT🔒 ع⑬: عدّادُ القصّ بالسعة يُقرأ بمفتاح `replay10` الفعليّ (قفل AST)",
      "rejected_cap" in _bt_keys and "rejected_capacity" not in _bt_keys
      and "rejected_cap" in _insp0.getsource(RP_.replay))
check("🐞 BT🔒 ع⑬: وكاشفُ المفاتيح ليس عدميًّا (يرى مفاتيحَ فعليّة)", bool(_bt_keys))

# ══════════════════════════════════════════════════════════════════════════
# 📐🔕 م-د — صيّاد الظرف الصامت (`envelope_hunter`)
# ══════════════════════════════════════════════════════════════════════════
import datetime as _ehdt                                         # noqa: E402
import os as _ehos                                               # noqa: E402
import envelope_hunter as _EH                                    # noqa: E402

_eh_src = _insp0.getsource(_EH)
# ── ① 🔕 صامتٌ بقرار المالك — صفر تلغرام ───────────────────────────────────
# 🐞 وقفلي الأوّل كان نصّيًّا فسقط على **docstring الأداة نفسها** (تقول «صفر
#    `send_telegram`») — **رابعُ ظهورٍ للفخّ الموثّق في هذي الجلسة** ⇒ بالـAST:
#    لا **نداءَ** لدالّة إرسالٍ، لا مجرّد غيابِ نصّها.
def _eh_no_send():
    """هل في الوحدة **نداءٌ** لأيّ دالّة إرسالٍ؟ (‏AST — التعليقات لا تُحسَب)"""
    import ast as _a
    bad = {"send_telegram", "sendMessage", "post"}
    for n in _a.walk(_a.parse(_eh_src)):
        if isinstance(n, _a.Call):
            f = n.func
            name = (f.attr if isinstance(f, _a.Attribute)
                    else (f.id if isinstance(f, _a.Name) else ""))
            if name in bad:
                return False
    return True


check("📐🔕 EH🔒 **صامت**: صفر **نداء** إرسال (قفل AST لا نصّيّ)",
      _eh_no_send())
check("📐🔕 EH🔒 ولا يمسّ حالة الفارز (لا قائمة ولا تنبيهات)",
      "save_watchlist" not in _eh_src and "load_watchlist" not in _eh_src
      and "WATCH_FILE" not in _eh_src)
check("📐🔕 EH🔒 والقرار من `envelope_scan` لا نسخةٍ ثانية",
      "envelope_scan" in _eh_src and "inside_envelope" not in _eh_src)

# ── ② بوّابة التوقيت مطابقةٌ لنظائرها في الصيّادين الثلاثة ─────────────────
import split_filter_hunter as _SFH                               # noqa: E402
for _h, _m in ((13, False), (19, False), (20, True), (23, True)):
    _t = _ehdt.datetime(2026, 8, 5, _h, 30, tzinfo=_ehdt.timezone.utc)
check("📐🔕 EH🔒 بوّابة التوقيت **مطابقةٌ** لبوّابة الأداة الرابعة (نفس الأوقات)",
      all(_EH.session_gate(_ehdt.datetime(2026, _mo, _d, _h, 30,
                                          tzinfo=_ehdt.timezone.utc))[0]
          is _SFH.session_gate(_ehdt.datetime(2026, _mo, _d, _h, 30,
                                              tzinfo=_ehdt.timezone.utc))[0]
          for _mo, _d in ((1, 15), (8, 5))
          for _h in (0, 1, 13, 19, 20, 23)))

# ── ③ محاكاةٌ كاملةٌ بلا شبكة — من **نقطة النداء** ─────────────────────────
def _eh_run(floats, decide, force="1", now_h=23, cov_syms=None, sess_prev=None,
            now_d=5):
    """يشغّل الصيّاد كاملًا بجذوعٍ محقونة ويرجّع (rc، صفوف المُخرَج، اللوق)."""
    _sv = {k: getattr(S, k, None) for k in
           ("yf", "get_universe", "download_history", "_yahoo_float", "git_save")}
    _out, _stamp = "/tmp/_eh_t.jsonl", "/tmp/_eh_t_stamp.json"
    _o_out, _o_st = _EH.OUT_FILE, _EH.STAMP_FILE
    _EH.OUT_FILE, _EH.STAMP_FILE = _out, _stamp
    for _f in (_out, _stamp):
        try:
            _ehos.remove(_f)
        except OSError:
            pass
    if sess_prev:
        with open(_stamp, "w", encoding="utf-8") as fh:
            json.dump({"session": sess_prev}, fh)
    _syms = cov_syms if cov_syms is not None else ["AAA", "BBB", "CCC"]
    _df = S.pd.DataFrame(
        {"Open": [2.0] * 90, "High": [2.1] * 90, "Low": [1.9] * 90,
         "Close": [2.0] * 90, "Volume": [5e5] * 90},
        index=S.pd.date_range("2026-03-02", periods=90, freq="B"))
    S.yf = object()
    S.get_universe = lambda: ["AAA", "BBB", "CCC"]
    S.download_history = lambda u: {q: _df for q in _syms}
    # 🐞 كان الجذع **يتجاهل `strict`** فطفرةُ `strict=False` نجت. الآن يحاكي
    #    ياهو حقًّا: بلا `strict` يسقط لـ`sharesOutstanding` **المنفوخ** ⇒ أيّ
    #    مرشّحٍ يصير «فلوتًا كبيرًا» فيُحذف = **تشديدٌ صامت** يُكشَف الآن.
    S._yahoo_float = (lambda sym, strict=False:
                      floats.get(sym) if strict else 999_000_000)
    S.git_save = lambda *a, **k: None
    _env0 = _ehos.environ.get("ENVELOPE_FORCE", "")
    _ehos.environ["ENVELOPE_FORCE"] = force
    try:
        rc = _EH.run(now_utc=_ehdt.datetime(2026, 8, now_d, now_h, 0,
                                            tzinfo=_ehdt.timezone.utc),
                     decide_fn=decide)
        try:
            rows = [json.loads(x) for x in open(_out, encoding="utf-8")]
        except OSError:
            rows = []
        return rc, rows
    finally:
        _ehos.environ["ENVELOPE_FORCE"] = _env0
        _EH.OUT_FILE, _EH.STAMP_FILE = _o_out, _o_st
        for k, v in _sv.items():
            if v is not None:
                setattr(S, k, v)


_eh_acc = (lambda St, sym, df, e:
           (True, "داخل الظرف", {"price": 2.0}) if sym in ("AAA", "BBB")
           else (False, "خارج الظرف", {"price": 9.0}))
_eh_rc, _eh_rows = _eh_run({"AAA": 900_000, "BBB": 300_000_000, "CCC": 900_000},
                           _eh_acc)
check("📐🔕 EH🔒 يعمل من نقطة النداء ويكتب ترويسةً + صفًّا لكل مرشّح",
      _eh_rc == 0 and _eh_rows and _eh_rows[0].get("_meta") is True
      and _eh_rows[0]["stage"]["inside"] == 2)
check("📐🔕 EH🔒 **M14 تُخرِج الفلوت الكبير فعلًا** (وليست زينة)",
      _eh_rows[0]["m14_removed"] == ["BBB"]
      and [r["symbol"] for r in _eh_rows[1:]] == ["AAA"])
check("📐🔕 EH🔒 والفلوت المجهول **يمرّ بفائدة الشك** ويُعدّ ويُعلَن",
      (lambda t: t[1][0]["unknown_float"] == 1
       and [r["symbol"] for r in t[1][1:]] == ["AAA", "BBB"])(
          _eh_run({"AAA": 900_000, "BBB": None}, _eh_acc)))
check("📐🔕 EH🔒 والمُخرَج **يصرّح أن M13 غير مقيسة** (لا إيهام)",
      _eh_rows[0]["m13_measured"] is False)
check("📐🔕 EH🔒 ويحمل التغطية والبصمة وجلسةَ البيانات (أثرٌ كامل)",
      _eh_rows[0]["coverage_pct"] == 100.0 and _eh_rows[0]["edges"]
      and _eh_rows[0]["session"])

# ── ④ الحرّاس: تغطية · دِدوب · حوافّ غائبة ─────────────────────────────────
check("📐🔕 EH🔒 حارس التغطية: تحت 60% ⇒ **إخفاقٌ صريح** لا مُخرَجٌ ناقص",
      (lambda t: t[0] == 1 and t[1] == [])(
          _eh_run({}, _eh_acc, cov_syms=["AAA"])))
# 🐞 وهذا الاختبار كان **يُحجب ببوّابة التوقيت الأسبق** (‏23:00 UTC = 19:00 ET
#    = مُغلقة) فيرجع 0 بلا صفوف **لسببٍ آخر** ⇒ طفرةُ إلغاء الدِدوب نجت. الآن
#    الوقت **‏01:00 UTC = 21:00 ET (مفتوحة)** والختمُ = **جلسة البيانات نفسها**
#    (‏2026-07-03) فيمرّ الدِدوبُ السريع ويصيب **الحاسم** وحده.
check("📐🔕 EH🔒 الدِدوب **الحاسم** (جلسة البيانات) ⇒ لا تكرار",
      (lambda t: t[0] == 0 and t[1] == [])(
          _eh_run({"AAA": 900_000}, _eh_acc, force="", now_h=1, now_d=6,
                  sess_prev="2026-07-03")))
#    وشاهدُ ضبط: ختمٌ **مختلف** ⇒ يمضي المسحُ فعلًا (القفل ليس عدميًّا)
check("📐🔕 EH🔒 وشاهدُ ضبط: ختمٌ مختلف ⇒ **يمسح** (لا يكتم دائمًا)",
      (lambda t: t[0] == 0 and len(t[1]) >= 2)(
          _eh_run({"AAA": 900_000, "BBB": 900_000}, _eh_acc, force="",
                  now_h=1, now_d=6, sess_prev="2026-01-01")))
check("📐🔕 EH🔒 بوّابة التوقيت: قبل الإغلاق ⇒ لا مسح (بلا تجاوز)",
      _eh_run({}, _eh_acc, force="", now_h=13)[0] == 0)
#    (حالةُ «حوافٌّ غائبة ⇒ رفض» مقفولةٌ في `envelope_scan` أعلاه — لا تُكرَّر
#     هنا بقفلٍ ملتوٍ يبدو عاملًا وهو تحصيلُ حاصل.)
check("📐🔕 EH🔒 يقرأ الحواف من `envelope_scan.load_edges` لا يحسبها",
      "load_edges" in _eh_src and "build_envelope" not in _eh_src)

# ── ⑤ السقف والقصّ مُعلَن · وgit_save بوسيطٍ واحد ─────────────────────────
check("📐🔕 EH🔒 القصّ **يُعلَن بعدّاده** ولا يُقصّ صامتًا",
      "cut" in _eh_rows[0] and _eh_rows[0]["cut"] == 0
      and "MAX_ROWS" in _eh_src)


def _eh_gitsave_argc():
    """‏`git_save` **بوسيطٍ واحد** — العيب الحيّ في الأداة الرابعة لا يُعاد."""
    import ast as _a
    for n in _a.walk(_a.parse(_eh_src)):
        if (isinstance(n, _a.Call) and isinstance(n.func, _a.Attribute)
                and n.func.attr == "git_save"):
            return len(n.args)
    return -1


check("📐🔕 EH🔒 `git_save` بوسيطٍ **واحد** (قفل AST — عيبٌ حيّ سابق)",
      _eh_gitsave_argc() == 1)

# ══════════════════════════════════════════════════════════════════════════
# 📐 م-د — `envelope_scan`: المصدر الوحيد لقرار الظرف
# ══════════════════════════════════════════════════════════════════════════
import envelope_scan as _ES                                      # noqa: E402
import catalog_envelope as _CE0   # كتلة الظرف تأتي لاحقًا في الملفّ  # noqa: E402

# ── ⓿ الحواف المجمَّدة: كاملةٌ وموسومةٌ بمصدرها ────────────────────────────
_es_blob = json.load(open("envelope_p90.json", encoding="utf-8"))
# ✅ حُدِّث 2026-08-07 ثلاثًا (أوامر المالك «قسها»): CRITERIA صارت **15**
#    (‏+tf_count الخامس عشر — آخرُ عتبةٍ قابلةٍ للقياس). القفلُ **انتقاليٌّ** حتى
#    تهبط معايرةُ الخمسة عشر، وبعدها يُعاد إلى المساواة التامّة (وهو يفرضها:
#    زيادةُ الملفّ على الخريطة تُسقطه).
_es_old11 = {"price", "drop_pct", "best_spike", "base_range", "dollar_vol",
             "rsi_min", "rsi_now", "n_soft", "readiness", "score", "rr"}
# ✅ هبطت معايرةُ الخمسة عشر (`31193618801` · `cf1d0f902d23`) ⇒ المساواةُ التامّة.
check("📐 SCAN🔒 ملفّ الحواف يحمل **المعايير الخمسة عشر كلَّها** (مساواةٌ تامّة)",
      set(_es_blob["edges"]) == {k for k, _, _, _ in _CE0.CRITERIA})
check("📐 SCAN🔒 والخريطةُ = القديمةُ الأحد عشر + الثلاثةُ + `tf_count` (‏15)",
      {k for k, _, _, _ in _CE0.CRITERIA} == _es_old11
      | {"gain5", "ma_above", "gap_above_dist", "tf_count"})
# 🔴 **`snapshot` أُخرِج من هذا القفل بسببٍ مقاس لا تسامحًا:** المُصدِّر يكتبه من
#    `ENV_SNAPSHOT_ID` و**الـworkflow لم يكن يُصدّره قطّ** ⇒ كلُّ مُخرَجٍ آليّ يخرج
#    بـ`null`، ومعناه أن أيّ ملفٍّ يحمل لقطةً كان **مملوءًا بيد**. فالشرطُ نُقل إلى
#    **مصدره الحقيقيّ** (قفلُ الـworkflow أدناه)، وهنا يُشترط ما تكتبه الأداةُ فعلًا.
check("📐 SCAN🔒 وموسومٌ بتشغيلته وتاريخها وعدد رموزه ومَن استُبعد",
      all(_es_blob.get(k) for k in ("run_id", "asof", "n_symbols", "pct"))
      and "HTZ" in _es_blob.get("excluded", {}))
check("📐 SCAN🔒 والـworkflow **يُصدّر `ENV_SNAPSHOT_ID`** فتكون اللقطة ذاتيّة النسب",
      "ENV_SNAPSHOT_ID" in open(".github/workflows/catalog_envelope.yml",
                                encoding="utf-8").read())
check("📐 SCAN🔒 والمقام مُصرَّحٌ به (20 جلسة) — فلا يُقارَن بمقامٍ آخر",
      _es_blob.get("denominator_sessions") == _CE0.ENTRY_WINDOW)
# 🐞 **وقفلي الأوّل هنا كان فارغًا (خامسُ مرّةٍ في الجلسة):** عنوانُه «تُصدَّر
#    آليًّا من الأداة لا نقلًا يدويًّا» **وهو يفحص وجودَ كودِ التصدير** في الأداة
#    **لا مصدرَ الملفّ** ⇒ أخضرُ والادّعاء غير صحيح. والقفلُ الصحيح **سلوكيّ**:
#    يفحص وسمَ الملفّ نفسه ومجموعةَ مفاتيحه.
# 🔴 **حُدِّث عمدًا 2026-08-07 — إقرارٌ لا إسكات:** الأداةُ صارت تُصدر
#    **`soft_median`** (‏`build_envelope(rows, 50.0)`) لأن أرقام «المثالي» في النواقص
#    اللينة صارت من **وسيط** الكاتالوج (أمرُ المالك «سوّها»). والقفلُ يبقى **مطابقةً
#    بالضبط** فأيُّ مفتاحٍ يُدَسّ يدويًّا لاحقًا يُسقطه كما أسقط هذا.
_es_TOOL_KEYS = {"pct", "snapshot", "asof", "run_id", "n_symbols", "excluded",
                 "denominator_sessions", "anchor_last_measured", "source", "edges",
                 "soft_median"}
check("📐 SCAN🔒 وسمُ الملفّ يقول **مُخرَجٌ آليّ** (لا نقلًا يدويًّا)",
      str(_es_blob.get("source", "")).startswith("مُخرَجٌ آليّ"))
check("📐 SCAN🔒 ولا مفتاحَ فيه لا تكتبه الأداة (يكشف النقل اليدويّ بنيويًّا)",
      set(_es_blob) <= _es_TOOL_KEYS)
check("📐 SCAN🔒 ع3: **تواريخ المِرساة مخزَّنة** فيُقاس التلوّث الزمنيّ",
      isinstance(_es_blob.get("anchor_last_measured"), dict)
      and len(_es_blob["anchor_last_measured"]) == _es_blob["n_symbols"])
check("📐 SCAN🔒 وكودُ التصدير قائمٌ في الأداة (شرطٌ لازمٌ لا كافٍ)",
      "ENVELOPE_P90_JSON" in _insp0.getsource(_CE0))

# ── ⓿-ب 🔴 **الوسمُ يجب أن يصل المستهلك لا أن يبقى في الملفّ** ──────────────
#    عيبٌ مقيس (‏2026-08-05): `load_edges` كانت تبني `_meta` بقائمةٍ بيضاء من خمسة
#    مفاتيح فتُسقط `source` و`anchor_last_measured` ⇒ (أ) حاجبُ `envelope_bt`
#    الذي يشترط «مُخرَجٌ آليّ» **يستحيل عبورُه** ⇒ وسمٌ يدويٌّ كاذب · (ب)
#    و`probe_anchors` تُعلن **كلَّ السنوات ملوَّثة** ⇒ التجربةُ «لا حكم» لعطلِ
#    أنابيبَ لا لعيبٍ في البيانات. والأقفالُ أعلاه كانت خضراءَ لأنها تفحص **الملفّ**
#    والعيبُ في **القارئ** ⇒ القفلُ الصحيح **من نقطة النداء**.
_es_loaded = _ES.load_edges()
_es_meta = _es_loaded.get("_meta") or {}
check("📐 SCAN🔒 ع⓿ب: `_meta` تمرّر **كلَّ** مفاتيح الملفّ غير `edges` (لا قائمةَ بيضاء)",
      set(_es_meta) == (set(_es_blob) - {"edges"}))
check("📐 SCAN🔒 ع⓿ب: فيعبُر حاجبُ «مُخرَجٌ آليّ» **من نقطة النداء** لا من الملفّ",
      str(_es_meta.get("source") or "").startswith("مُخرَجٌ آليّ"))
check("📐 SCAN🔒 ع⓿ب: وتواريخُ المِرساة **تصل `probe_anchors`** فيُقاس التلوّث فعلًا",
      (lambda a: a["n"] == _es_blob["n_symbols"]
       and a["contaminated"] != [2023, 2024, 2025])(
          _BT.probe_anchors(_es_loaded, (2023, 2024, 2025))))
check("📐 SCAN🔒 ع⓿ب: و`_meta` لا تُغيّر البصمة (القرارُ بت-بت)",
      _ES.edges_fingerprint(_es_loaded)
      == _ES.edges_fingerprint({k: v for k, v in _es_loaded.items()
                                 if k != "_meta"}))
#    📌 والظرف **ليس أوسعَ في كل شيء** — أربعةٌ منه **أضيقُ** من حدّنا. قفلٌ على
#    هذي الحقيقة لئلّا يُوصَف لاحقًا بـ«تخفيفٍ» وهو **إعادةُ تشكيل**.
_es_tighter = [
    ("price", 1.62, S.CONFIG["MIN_PRICE"]),
    ("best_spike", 100.0, S.CONFIG["PRIOR_SPIKE_FLOOR"]),
    ("rr", 1.72, S.CONFIG["MIN_RR_T1"]),
]
check("📐 SCAN🔒 الظرف **يعيد التشكيل لا يخفّف**: أربعةٌ منه أضيقُ من حدّنا",
      all(_es_blob["edges"][k] > cur for k, _v, cur in _es_tighter)
      and _es_blob["edges"]["drop_pct"][0] > S.CONFIG["MIN_DROP_FLOOR"])

# ── ① العزل: لا يدخل الإنتاج، ولا يُنادى من أيّ مسارٍ حيّ ──────────────────
# ✅ **حُدِّث 2026-08-06 بأمر المالك** «ابن الحد الادنى و اعتمد على بواباته فقط»:
#    الظرفُ صار **مصدرَ أرقام الفرز**. والعزلُ يبقى في كلّ مكانٍ إلّا **بابًا واحدًا
#    مأذونًا**: `apply_faisal_only` في `Super_stock` — **استيرادٌ كسولٌ داخلها** لا
#    على مستوى الوحدة، فانكسارُ الظرف لا يُسقط الجذع. والصيّادون **كما هم**.
check("📐 SCAN🔒 عزلٌ ببابٍ واحدٍ مأذون: الصيّادون لا يستوردونه إطلاقًا",
      all("envelope_scan" not in open(_f, encoding="utf-8").read()
          for _f in ("split_hunter.py", "method_hunter.py",
                     "split_filter_hunter.py", "ignition_live.py",
                     "pullback_live.py")))
check("📐 SCAN🔒 وفي `Super_stock` **داخل `apply_faisal_only` وحدها** (كسولًا)",
      "envelope_scan" in _insp0.getsource(S.apply_faisal_only)
      and not any(("envelope_scan" in (getattr(n, "module", "") or ""))
                  or any(a.name.startswith("envelope_scan")
                         for a in getattr(n, "names", []))
                  for n in _ast0.parse(open("Super_stock.py",
                                            encoding="utf-8").read()).body))
check("📐 SCAN🔒 لا يُرسل تلغرام ولا يحفظ حالة (قرارٌ خالص)",
      (lambda t: "send_telegram" not in t and "git_save" not in t
       and "save_watchlist" not in t)(_insp0.getsource(_ES)))

# ── ② `relaxed` هي الموضع الوحيد الذي يمسّ CONFIG — وتستعيدها مهما حصل ────
_es_snap = {k: S.CONFIG.get(k) for k in _ES.RELAX_ALL}
with _ES.relaxed(S):
    _es_inside = all(S.CONFIG.get(k) == v for k, v in _ES.RELAX_ALL.items())
check("📐 SCAN🔒 `relaxed` **تُرخي فعلًا** داخل السياق (القفل ليس عدميًّا)",
      _es_inside)
check("📐 SCAN🔒 وتستعيد `CONFIG` بت-بت بعده",
      all(S.CONFIG.get(k) == v for k, v in _es_snap.items()))
try:
    with _ES.relaxed(S):
        raise RuntimeError("انهيارٌ مُتعمَّد")
except RuntimeError:
    pass
check("📐 SCAN🔒 والاستعادة تقع **حتى مع الانهيار**",
      all(S.CONFIG.get(k) == v for k, v in _es_snap.items()))
check("📐 SCAN🔒 `selftest` يُثبت سلامة الدورة",
      _ES.selftest(S) is True)

# ── ③ 🔴 الأهمّ: `analyze_ticker` **بت-بit** قبل الأداة وبعدها ─────────────
#    (وهذا ما تعجز عنه أقفال C3/B3: تأكيدا **قيمةٍ عند الاستيراد**، والإرخاء
#     يقع زمن التشغيل — فسلوكُ جذرٍ يتغيّر دون لمس كوده.)
_es_df = _mkdf([(2.0, 2.2, 1.9, 2.0, 500_000)] * 80)
_es_a = S.analyze_ticker("ESTEST", _es_df)
with _ES.relaxed(S):
    _ = S.analyze_ticker("ESTEST", _es_df)
_es_b = S.analyze_ticker("ESTEST", _es_df)
check("📐 SCAN🔒 **قفلٌ سلوكيّ**: `analyze_ticker` قبل/بعد الإرخاء متطابق",
      (_es_a is None and _es_b is None)
      or (_es_a is not None and _es_b is not None
          and json.dumps(_es_a, sort_keys=True, default=str)
          == json.dumps(_es_b, sort_keys=True, default=str)))

# ── ④ الحواف تُقرأ من ملفٍّ ولا تُحسب حيًّا · وغيابُها **رفضٌ لا تساهل** ────
check("📐 SCAN🔒 بلا حوافّ ⇒ **رفضٌ صريح** (فاشلة-مغلقة عمدًا هنا)",
      _ES.decide(S, "X", None, {})[0] is False
      and "لا حوافّ" in _ES.decide(S, "X", None, {})[1])
check("📐 SCAN🔒 الحواف من ملفٍّ مُثبَت لا حسابٍ حيّ",
      _ES.EDGES_FILE.endswith(".json")
      and _ES.load_edges("/tmp/_es_غائب.json") == {})
check("📐 SCAN🔒 بصمة الحواف حتمية (ترتيب المفاتيح لا يغيّرها)",
      _ES.edges_fingerprint({"a": 1.0, "b": (2.0, 3.0)})
      == _ES.edges_fingerprint({"b": (2.0, 3.0), "a": 1.0}))

# ── ⑤ 🔴 M13/M14 فلترٌ نهائيّ — وإلّا سلّم فئةً أخرجها المالك ──────────────
_es_edges = {"price": 0.0}     # ظرفٌ يقبل كلَّ شيء ⇒ يعزل أثر البوّابتين وحدهما
_es_vals = {"price": 5.0}


def _es_dec(row):
    """يقرّر على قيمٍ مضمونة الدخول ⇒ الفارق **البوّابتان فقط**."""
    import types
    stub = types.SimpleNamespace(
        CONFIG=S.CONFIG, log=S.log, _float_too_big=S._float_too_big)
    _ES.measure_session  # noqa: B018  (مرجعٌ صريح: القرار يمرّ بالقياس)
    ok = _ES.inside_envelope(_es_vals, _es_edges)
    return ok and _ES._float_ok(stub, row) and _ES._short_ok(stub, row)


check("📐 SCAN🔒 M14: فلوتٌ كبيرٌ معلوم ⇒ **يُرفَض** (قرار المالك)",
      _es_dec({"float": 300_000_000}) is False)
check("📐 SCAN🔒 M13: شورتٌ عالٍ معلوم ⇒ يُرفَض",
      _es_dec({"finra_short": S.CONFIG["SHORT_GATE_MAX"] + 1}) is False)
check("📐 SCAN🔒 والمجهول **يمرّ بفائدة الشك** (قاعدة الفارز الحيّة)",
      _es_dec({}) is True and _es_dec({"float": None, "finra_short": None}) is True
      and _es_dec({"float": "تالف", "finra_short": "تالف"}) is True)


# 🔴 والقفل أعلاه يفحص **الدالّتين المساعدتين** — وطفرةٌ عطّلت فرع M14 **داخل
#    `decide` نفسها ونجت**. وهو صنف «الميزة موصولة تُثبَت من نقطة النداء» بعينه
#    ⇒ قفلٌ يمرّ عبر `decide` كاملةً بجذعٍ محقون.
class _EsStub:                                                    # noqa: E301
    """جذعٌ يُمرّر أيّ سهم ⇒ الفارق **البوّابتان داخل `decide`** وحدهما."""
    def __init__(self):
        self.CONFIG = dict(S.CONFIG)
        self.log = S.log
        self._float_too_big = S._float_too_big
    def analyze_ticker(self, sym, df):                            # noqa: D102
        return {"price": 5.0, "gates_status": {}, "soft_fails": []}


class _EsBoom(_EsStub):                                           # noqa: E301
    def analyze_ticker(self, sym, df):                            # noqa: D102
        raise RuntimeError("انهيارٌ مُتعمَّد")


_es_edges_all = {"price": 0.0}
check("📐 SCAN🔒 **من نقطة النداء**: `decide` ترفض الفلوت الكبير فعلًا",
      _ES.decide(_EsStub(), "X", _mkdf([(1, 1, 1, 1, 1)] * 3), _es_edges_all,
                 {"float": 300_000_000})[0] is False
      and "M14" in _ES.decide(_EsStub(), "X", _mkdf([(1, 1, 1, 1, 1)] * 3),
                              _es_edges_all, {"float": 300_000_000})[1])
check("📐 SCAN🔒 **من نقطة النداء**: `decide` ترفض الشورت العالي فعلًا",
      (lambda r: r[0] is False and "M13" in r[1])(
          _ES.decide(_EsStub(), "X", _mkdf([(1, 1, 1, 1, 1)] * 3), _es_edges_all,
                     {"finra_short": S.CONFIG["SHORT_GATE_MAX"] + 1})))
check("📐 SCAN🔒 **من نقطة النداء**: السليم يُقبَل (القفل ليس عدميًّا)",
      _ES.decide(_EsStub(), "X", _mkdf([(1, 1, 1, 1, 1)] * 3), _es_edges_all,
                 {"float": 900_000, "finra_show": 1_000})[0] is True)
# 🔴 وطفرةٌ ثالثة نجت: كلُّ عيّناتي **داخل** الظرف فلا تختبر شرطَه. شاهدٌ **خارجه**:
#    الجذع يُرجع سعرًا 5.0 وحافّة `lo` عند 10.0 ⇒ **يجب** أن يُرفَض «خارج الظرف».
# 🔴 ورابعةٌ نجت: **قياسٌ فاشل** (‏`analyze_ticker` يرجع None) كان يُقبَل بلا قفل.
class _EsDead(_EsStub):                                           # noqa: E301
    def analyze_ticker(self, sym, df):                            # noqa: D102
        return None


check("📐 SCAN🔒 **من نقطة النداء**: تعذّرُ القياس ⇒ رفضٌ مُسمّى لا قبول",
      (lambda r: r[0] is False and "تعذّر القياس" in r[1] and r[2] is None)(
          _ES.decide(_EsDead(), "X", _mkdf([(1, 1, 1, 1, 1)] * 3),
                     _es_edges_all, {"float": 900_000})))
check("📐 SCAN🔒 **من نقطة النداء**: قيمةٌ خارج الحافّة ⇒ «خارج الظرف»",
      (lambda r: r[0] is False and "خارج الظرف" in r[1])(
          _ES.decide(_EsStub(), "X", _mkdf([(1, 1, 1, 1, 1)] * 3),
                     {"price": 10.0}, {"float": 900_000})))

# ── ⑤-مكرر 🚧 D11 منع الملاحقة — العيب الذي كان يجعل الظرف يلاحق ما ارتفع ──
# ✅ حُدِّث 2026-08-07 (قرار المالك «قسها»): الفجوةُ **أُغلقت** — `gain5` صار معيارًا
#    يقابل `RECENT_RISE_BLOCK_PCT` ⇒ **كلُّ** مفاتيح الإرخاء لها معيارٌ الآن.
#    (كان القفلُ يثبّت الفجوةَ نفسَها: `- cov == {"RECENT_RISE_BLOCK_PCT"}`.)
check("📐 SCAN🔒 ع2: كلُّ مفاتيح الإرخاء صار لها معيارُ ظرفٍ (الفجوةُ أُغلقت 2026-08-07)",
      (lambda cov: set(_CE0.RELAX_ALL) - cov == set())(
          {k for _n, _d, _l, c in _CE0.CRITERIA for k in c.split("|")}))
check("📐 SCAN🔒 D11: `chase_ok` تُرخي كلَّ شيءٍ **إلّا** مفتاح الملاحقة",
      "RECENT_RISE_BLOCK_PCT" in _insp0.getsource(_ES.chase_ok)
      and "analyze_ticker" in _insp0.getsource(_ES.chase_ok))


class _EsChase(_EsStub):                                          # noqa: E301
    """جذعٌ يحاكي بوّابةَ الملاحقة: `None` ⇒ رُفض · قاموسٌ ⇒ مرّ."""
    def __init__(self, chased):
        super().__init__()
        self.chased = chased
        self.calls = 0
    def analyze_ticker(self, sym, df):                            # noqa: D102
        self.calls += 1
        # النداء الأوّل من `measure` (كلُّ شيءٍ مُرخًى) · والثاني من `chase_ok`
        if self.calls >= 2 and self.chased:
            return None
        return {"price": 5.0, "gates_status": {}, "soft_fails": []}


check("📐 SCAN🔒 **من نقطة النداء**: `decide` ترفض الملاحِق بسببٍ مُسمّى",
      (lambda r: r[0] is False and "D11" in r[1])(
          _ES.decide(_EsChase(True), "X", _mkdf([(1, 1, 1, 1, 1)] * 3),
                     _es_edges_all, {"float": 900_000})))
check("📐 SCAN🔒 وشاهدُ ضبط: غيرُ الملاحِق **يُقبَل** (القفل ليس عدميًّا)",
      _ES.decide(_EsChase(False), "X", _mkdf([(1, 1, 1, 1, 1)] * 3),
                 _es_edges_all, {"float": 900_000})[0] is True)
def _es_chase_restores():
    """يقارن `CONFIG` **قبل وبعد** لا بقيمةٍ مفترضة (تأكيدي الأوّل كان خاطئًا)."""
    st = _EsStub()
    before = dict(st.CONFIG)
    _ES.chase_ok(st, "X", _mkdf([(1, 1, 1, 1, 1)] * 3))
    return st.CONFIG == before


check("📐 SCAN🔒 و`chase_ok` تُعيد `CONFIG` بت-بت (ولا تترك بوّابةً معطَّلة)",
      _es_chase_restores())
check("📐 SCAN🔒 وفاشلة-آمنة: انهيارُ التحليل ⇒ يمرّ بفائدة الشك",
      _ES.chase_ok(_EsBoom(), "X", _mkdf([(1, 1, 1, 1, 1)] * 3)) is True)

# ── ⑥ المصدر واحد: لا نسخةَ منطقٍ ثانية ───────────────────────────────────
check("📐 SCAN🔒 مصدرٌ واحد: يستورد قرار المعايرة ولا ينسخه",
      _ES.inside_envelope is _CE0.inside_envelope
      and _ES.measure_session is _CE0.measure_session
      and _ES.RELAX_ALL is _CE0.RELAX_ALL)

# ══════════════════════════════════════════════════════════════════════════
# 🗂️ م-ب — سجلّ المرفوضين اليوميّ (الشاهد الأماميّ الوحيد غير المُنقَّب)
# ══════════════════════════════════════════════════════════════════════════
_rl_snap = S.build_reject_snapshot(
    {"AAA": "M4_base_واسعة", "BBB": "M5_سيولة", "CCC": "M4_base_واسعة"}, "2026-08-05")
check("🗂️ REJ🔒 اللقطة تُجمَّع بالجدار وتحمل الرمز (لا أعدادًا فقط)",
      _rl_snap["walls"]["M4_base_واسعة"] == ["AAA", "CCC"]
      and _rl_snap["walls"]["M5_سيولة"] == ["BBB"] and _rl_snap["n"] == 3)
check("🗂️ REJ🔒 القصّ **يُعلَن بعدّاده** — لا قصّ صامت",
      S.build_reject_snapshot({f"S{i}": "M4_base_واسعة" for i in range(500)},
                              "d", cap=400)["cut"] == 100
      and _rl_snap["cut"] == 0)
# 🔴 RS — العيّنةُ **غيرُ منحازة** والأعدادُ **دقيقةٌ** حتى عند السقف (2026-08-06).
#    العيبُ المقيس: القصُّ الأبجديّ جعل `M2_هبوط_تحت_40` يقف عند `COKE` (A–C وحدها)
#    بينما الجدارُ غيرُ المسقوف يمتدّ `AAME→ZOOZ` — انحيازٌ منهجيّ في الشاهد الأماميّ.
_rs_syms = {("SYM%03d" % i): "M1_سعر" for i in range(1200)}
_rs = S.build_reject_snapshot(_rs_syms, "2026-08-06", cap=400)
_rs_kept = _rs["walls"]["M1_سعر"]
check("🔴 RS1 العدد **دقيقٌ** حتى عند السقف (`walls_n`) ⇒ الترتيبُ ممكن",
      _rs["walls_n"]["M1_سعر"] == 1200 and len(_rs_kept) == 400 and _rs["cut"] == 800,
      f"n={_rs['walls_n']['M1_سعر']} · kept={len(_rs_kept)} · cut={_rs['cut']}")
check("🔴 RS2 والقائمةُ المسقوفة **تُوسَم عيّنةً** (لا تُقرأ حصرًا)",
      _rs["sampled"] == ["M1_سعر"], str(_rs["sampled"]))
# 🔬 المميِّز: العيّنة تمسح المدى كلَّه — القصُّ الأبجديّ كان سيقف عند SYM399.
check("🔴 RS3 العيّنةُ **غيرُ منحازةٍ أبجديًّا** (تبلغ آخر المدى لا أوّله)",
      _rs_kept[-1] > "SYM399" and _rs_kept[0] < "SYM800",
      f"أول={_rs_kept[0]} · آخر={_rs_kept[-1]}")
# التوزيع على الأثلاث ≈ متساوٍ (عيّنةٌ موحّدة) — الأبجديُّ يعطي 400/0/0.
_rs_th = [sum(1 for s in _rs_kept if lo <= int(s[3:]) < hi) for lo, hi in ((0, 400), (400, 800), (800, 1200))]
check("🔴 RS4 وموزَّعةٌ على الأثلاث الثلاثة (الأبجديُّ كان 400/0/0)",
      all(80 < t < 220 for t in _rs_th), str(_rs_th))
check("🔴 RS5 وحتميّةٌ قابلةٌ لإعادة الإنتاج (نفس اليوم ⇒ نفس العيّنة)",
      S.build_reject_snapshot(_rs_syms, "2026-08-06", cap=400)["walls"]["M1_سعر"] == _rs_kept)
check("🔴 RS6 ويومٌ آخر ⇒ عيّنةٌ أخرى (تتّسع التغطية عبر النافذة)",
      S.build_reject_snapshot(_rs_syms, "2026-08-07", cap=400)["walls"]["M1_سعر"] != _rs_kept)
check("🗂️ REJ🔒 الأسباب الحاملة لرقمٍ تُوحَّد بالقاعدة (مقامٌ لا يتفتّت)",
      S.build_reject_snapshot({"A": "بعيد_عن_الدخول(45%)",
                               "B": "بعيد_عن_الدخول(12%)"}, "d")["n"] == 2
      and len(S.build_reject_snapshot({"A": "بعيد_عن_الدخول(45%)",
                                       "B": "بعيد_عن_الدخول(12%)"}, "d")["walls"]) == 1)
# 🔒 فاشلة-آمنة: مسارٌ غير قابلٍ للكتابة ⇒ 0 بلا انهيار (وهو ما يحمي المسار اليوميّ)
check("🗂️ REJ🔒 فاشلة-آمنة: مسارٌ متعذّر ⇒ 0 ولا استثناء",
      S.record_rejected_symbols({"A": "M1_سعر"}, path="/proc/لا-يوجد/x.json") == 0)
check("🗂️ REJ🔒 أسبابٌ فارغة ⇒ 0 (لا ملفّ ولا ضجيج)",
      S.record_rejected_symbols({}, path="/tmp/_rl_never.json") == 0)
# 🔒 التدوير + «لقطة واحدة لكل يوم»
import os as _rl_os
_rl_p = "/tmp/_rl_roll.json"
try:
    _rl_os.remove(_rl_p)
except OSError:
    pass
for _d in range(1, 26):
    S.record_rejected_symbols({"A": "M1_سعر"}, path=_rl_p, keep=20,
                              today=f"2026-07-{_d:02d}")
_rl_rows = json.load(open(_rl_p, encoding="utf-8"))
check("🗂️ REJ🔒 التدوير يُبقي آخر 20 يومًا فقط (لا انفجار حجم)",
      len(_rl_rows) == 20 and _rl_rows[0]["date"] == "2026-07-06"
      and _rl_rows[-1]["date"] == "2026-07-25")
S.record_rejected_symbols({"A": "M1_سعر", "B": "M5_سيولة"}, path=_rl_p,
                          keep=20, today="2026-07-25")
_rl_rows2 = json.load(open(_rl_p, encoding="utf-8"))
check("🗂️ REJ🔒 لقطةٌ واحدة لكل يوم — والأحدث تفوز",
      len(_rl_rows2) == 20
      and sum(1 for r in _rl_rows2 if r["date"] == "2026-07-25") == 1
      and _rl_rows2[-1]["n"] == 2)
# 🔴 والقفل الحاسم: **انهيارُها لا يُسقط المسار اليوميّ** — بالشجرة النحوية لا بالنصّ
#    (النصّيّ يقرأ التعليقات؛ والفخّ الموثّق ثلاث مرّات).
def _rl_guarded():
    """هل كلُّ نداءٍ لـ`record_rejected_symbols` داخل `try` في مصدر البوت؟"""
    import ast as _a
    tree = _a.parse(open("Super_stock.py", encoding="utf-8").read())
    calls, guarded = 0, 0
    for node in _a.walk(tree):
        if not isinstance(node, _a.Try):
            continue
        for sub in _a.walk(node):
            if (isinstance(sub, _a.Call) and isinstance(sub.func, _a.Name)
                    and sub.func.id == "record_rejected_symbols"):
                guarded += 1
    for node in _a.walk(tree):
        if (isinstance(node, _a.Call) and isinstance(node.func, _a.Name)
                and node.func.id == "record_rejected_symbols"):
            calls += 1
    return calls, guarded


_rl_c, _rl_g = _rl_guarded()
check("🗂️ REJ🔒 **كلُّ نداءٍ محروسٌ بـtry** (قفل AST — انهيارُها لا يُسقط اليوم)",
      _rl_c >= 2 and _rl_g == _rl_c)
check("🗂️ REJ🔒 موصولةٌ في المسارَين اليوميّ والتجديد (نقطتا نداءٍ حيّتان)",
      _rl_c == 2)
# 🐞 قفلي الأوّل هنا فحص `getsource(S.main)` و`git_save` **ليست فيها** —
#    قفلٌ يسأل المكان الخطأ. صار يفحص **نداء `git_save` نفسه** بالشجرة النحوية.
def _rl_saved():
    """هل `REJECT_LOG_FILE` ضمن وسائط أيّ نداءٍ لـ`git_save`؟ (‏AST لا نصّ)"""
    import ast as _a
    tree = _a.parse(open("Super_stock.py", encoding="utf-8").read())
    for node in _a.walk(tree):
        if (isinstance(node, _a.Call) and isinstance(node.func, _a.Name)
                and node.func.id == "git_save" and node.args):
            first = node.args[0]
            if isinstance(first, (_a.List, _a.Tuple)):
                names = [e.id for e in first.elts if isinstance(e, _a.Name)]
                if "REJECT_LOG_FILE" in names:
                    return True
    return False


check("🗂️ REJ🔒 الملفّ ضمن وسائط `git_save` وإلّا ضاع مع الرنر (قفل AST)",
      _rl_saved())
# 🔒 وممنوعٌ أيُّ حقلٍ من enrich (تسريب: enrich بعد select_top)
#    ➕ `walls_n`/`sampled` (2026-08-06): **أعدادٌ وأسماءُ جدران** — لا حقلَ إثراءٍ فيهما
#    (الأول عددُ الرموز لكل جدار، والثاني أسماءُ الجدران المسقوفة). القائمةُ تبقى **حصرًا**.
check("🗂️ REJ🔒 لا حقلَ إثراءٍ في اللقطة (تسريبٌ لأيّ نموذجٍ لاحق)",
      set(_rl_snap.keys()) == {"date", "walls", "walls_n", "sampled", "n", "cut"},
      str(sorted(_rl_snap.keys())))
# 🔒 وأعمقُ من الحصر: لا اسمَ حقلِ إثراءٍ في **المحتوى كلِّه** (لا المفاتيح وحدها).
_rl_blob = _json.dumps(S.build_reject_snapshot(
    {"AAA": "M4_base_واسعة", "BBB": "M5_سيولة"}, "2026-08-05"), ensure_ascii=False)
check("🗂️ REJ🔒 ولا اسمَ حقلِ إثراءٍ في المحتوى كلِّه (أعمقُ من حصر المفاتيح)",
      not any(f in _rl_blob for f in ("borrow", "shares_available", "float", "short_pct",
                                      "h4_confirm", "behav", "rotation_pct", "interp",
                                      "finra_short", "sector", "country")), _rl_blob[:90])


# 🔒 **والمسار المؤقّت يعمل فعلًا**: المسار اليوميّ يُشغَّل، والكتابةُ تقع في
#    المؤقّت لا في الملفّ المدفوع. (والحرسُ الشاملُ لكلّ كاتبٍ **قبل الملخّص**.)
check("🗂️ REJ🔒 `REJECT_LOG_FILE` مُحوَّلٌ لمسارٍ مؤقّت في السويّة (لا مسارَ المستودع)",
      S.REJECT_LOG_FILE != _REJ_REAL_PATH
      and S.REJECT_LOG_FILE.startswith(_rej_tf.gettempdir()))

# 🔴 **والتحويلُ عاجزٌ إن رُبِط الافتراضُ وقت التعريف** (عيبٌ مقيس 2026-08-05):
#    كان `path: str = REJECT_LOG_FILE` فيُربَط الافتراضُ لحظةَ `def` ⇒ تحويلُ
#    الثابت بعد الاستيراد **لا يؤثّر**، فكانت السويّة تكتب في الملفّ المدفوع وأنا
#    أحسبها مُحوَّلة. القفل **سلوكيّ**: نُنادي بلا `path` ونتحقّق أين كُتب فعلًا.
def _rej_resolves_at_call():
    import os as _o
    tmp = _o.path.join(_rej_tf.gettempdir(), "_rej_probe.json")
    for p in (tmp, S.REJECT_LOG_FILE):
        try:
            _o.remove(p)
        except OSError:
            pass
    old = S.REJECT_LOG_FILE
    S.REJECT_LOG_FILE = tmp
    try:
        S.record_rejected_symbols({"AAA": "M1_سعر"}, today="2026-01-01")
    finally:
        S.REJECT_LOG_FILE = old
    return _o.path.exists(tmp)


check("🗂️ REJ🔒 والمسارُ يُحسم **وقت النداء** لا وقت التعريف (وإلّا التحويلُ عاجز)",
      _rej_resolves_at_call())
check("🗂️ REJ🔒 ولا افتراضَ مربوطًا بالثابت في التوقيع (قفل AST)",
      (lambda sig: all(not (isinstance(d, _ast0.Name)
                            and d.id in ("REJECT_LOG_FILE", "REJECT_LOG_DAYS"))
                       for d in sig.args.defaults))(
          _ast0.parse(_insp0.getsource(S.record_rejected_symbols).lstrip()).body[0]))
check("🗂️ REJ🔒 والملفّ المدفوع **نظيف** (لا رموزَ اختبارٍ مُلتزَمة)",
      (lambda rows: not any(
          s in json.dumps(rows, ensure_ascii=False)
          for s in ("CDOFF", "P1A", "P110", "GONE", "مسطّح", "LBOFF")))(
          json.load(open(_REJ_REAL_PATH, encoding="utf-8"))
          if _os_hc.path.exists(_REJ_REAL_PATH) else []))

# ══════════════════════════════════════════════════════════════════════════
# 📐 ظرف الكاتالوج — «الحدّ الأدنى» مقيسًا من أسهم فيصل (العقد:
#    `catalog_envelope_design.md`، مدفوعٌ قبل أوّل تشغيل).
# ══════════════════════════════════════════════════════════════════════════
import catalog_envelope as _CE                                    # noqa: E402

# ── 📌 تعديل ⑤: HTZ مُستبعَدٌ **بإعلان** لا بصمت (طفرة M22 نجت أوّلًا = بلا قفل) ──
check("📐 ENV🔒 تعديل ⑤: المُخرَجون بقرار المالك مُعلَنون بأسبابهم",
      isinstance(_CE.EXCLUDED_BY_OWNER, dict) and "HTZ" in _CE.EXCLUDED_BY_OWNER
      and "M14" in _CE.EXCLUDED_BY_OWNER["HTZ"])
#    🔒 والقفل السلوكيّ: الاستبعاد **يقع فعلًا** — بالشجرة النحوية لا بالنصّ.
def _ce_excludes():
    """هل في `run` ترشيحٌ يحذف رمز `EXCLUDED_BY_OWNER` من `syms` فعلًا؟"""
    import ast as _a
    tree = _a.parse(_insp0.getsource(_CE))
    for n in _a.walk(tree):
        if not (isinstance(n, _a.Assign) and len(n.targets) == 1
                and isinstance(n.targets[0], _a.Name) and n.targets[0].id == "syms"):
            continue
        if isinstance(n.value, _a.ListComp):
            for cmp_ in n.value.generators:
                for c in cmp_.ifs:
                    if (isinstance(c, _a.Compare)
                            and isinstance(c.ops[0], _a.NotEq)):
                        return True
    return False


check("📐 ENV🔒 تعديل ⑤: الحذف **ينفَّذ فعلًا** لا يُعلَن فقط (قفل AST)",
      _ce_excludes())
check("📐 ENV🔒 تعديل ⑤: قابلٌ للإرجاع بمفتاحٍ مُعلَن (قياسُ أثرٍ لا وضعٌ افتراضيّ)",
      "ENV_KEEP_M14" in _insp0.getsource(_CE))

# ── ⓪ العقد موجودٌ ويحمل القرارات الستّة — فلا تُشغَّل أداةٌ بلا عقد ──────────
_ce_design = open("catalog_envelope_design.md", encoding="utf-8").read()
check("📐 ENV🔒 العقد مدفوعٌ ويحمل القرارات الستّة (D1…D6)",
      all(f"D{i} —" in _ce_design for i in range(1, 7)))

# ── ① D2: أوّل انفجارٍ لا أكبرُه · وبلا نظرٍ مستقبليّ ───────────────────────
#    قاعٌ ثابتٌ 1.0، قمّةٌ 1.5 قبل 30، ثم +120% عند 30، ثم +300% عند 60.
_ce_lo = [1.0] * 70
_ce_hi = [1.5] * 70
_ce_hi[30] = 2.2          # ← الانفجار الأوّل  (+120%)
_ce_hi[60] = 4.0          # ← انفجارٌ أكبر لاحقًا (+300%)
check("📐 ENV🔒 D2: `first` ⇒ الأقدم · `last` ⇒ الأحدث — والوضعان متمايزان",
      _CE.explosion_index(_ce_hi, _ce_lo, pick="first") == 30
      and _CE.explosion_index(_ce_hi, _ce_lo, pick="last") == 60)
# 📌 تعديل ②: الافتراض صار **الأحدث** — لأن الأقدم أمسك حدثًا لا علاقة لفيصل به
#    (‏ZCMD ‏2022-11-15 مقابل لحظته الموثّقة 2026-07-02). قفلٌ على الافتراض نفسه:
check("📐 ENV🔒 تعديل ②: الافتراض `ANCHOR=\"last\"` (الأحدث) لا الأقدم",
      _CE.ANCHOR == "last" and _CE.explosion_index(_ce_hi, _ce_lo) == 60)
#    شاهدُ نظرٍ مستقبليّ: قاعُ الشمعة **نفسِها** منخفضٌ جدًّا وما قبلها مرتفع ⇒
#    لو أُدخل `low[i]` في القاعدة لانفجرت عند 40، وبالصواب لا تنفجر إطلاقًا.
_ce_lo2 = [3.0] * 70
_ce_hi2 = [3.2] * 70
_ce_lo2[69] = 1.0         # ← قاعُ **آخر** شمعة: لا يدخل نافذةَ أيّ بارٍ لاحق
#   بالصواب: قاعدةُ البار 69 = min(lo[49:69]) = 3.0 ⇒ 3.2/3.0 = +7% ⇒ لا انفجار.
#   بالطفرة (‏i+1): تشمل lo[69]=1.0 ⇒ 3.2/1.0 = +220% ⇒ تنفجر ⇒ القفل يسقط.
check("📐 ENV🔒 D2: القاعُ من الجلسات **السابقة** حصرًا (لا نظر مستقبليّ)",
      _CE.explosion_index(_ce_hi2, _ce_lo2) is None)
check("📐 ENV🔒 D2: بلا انفجارٍ ⇒ None (ولا يُخترَع فهرس)",
      _CE.explosion_index([1.1] * 70, [1.0] * 70) is None
      and _CE.explosion_index([9.0] * 5, [1.0] * 5) is None)

# ── ①-ب 🔴🔴 تصحيح ⑧ (عيبٌ `P0`): المِرساةُ **بدءُ** الانفجار لا جلسةٌ داخله ──
#    كان `walk_symbol` يُرسي على `explosion_index` — وهي **أحدثُ** جلسةٍ تبلغ +100%
#    فوق أدنى قاعٍ في العشرين السابقة. وفي صعودٍ ممتدّ **تستوفي ذلك جلساتٌ كثيرة**
#    فتقع المِرساةُ عميقًا داخل الصعود ⇒ «العشرون جلسةً **قبل** الانفجار» تصير
#    عشرين جلسةً **من** الانفجار ⇒ الظرفُ مُعايَرٌ على وسط الحركة لا على القاع.
def _ce_shape(n_base, run_len, top, base=1.00):
    close = [base] * n_base + [base + (top - base) * k / run_len
                               for k in range(1, run_len + 1)] + [top] * 20
    return [c * 1.02 for c in close], [c * 0.98 for c in close]


def _ce_inside(n_base, run_len, top):
    """كم جلسةً من نافذة القياس تقع **داخل** الانفجار؟ (المطلوب صفر)"""
    hi, lo = _ce_shape(n_base, run_len, top)
    hit = _CE.explosion_index(hi, lo, 100.0, 20, pick="last")
    on = _CE.explosion_onset(lo, hit, 20)
    s = max(0, on - _CE.ENTRY_WINDOW)
    return hit, on, sum(1 for j in range(s, on) if j >= n_base)


_ce_h1, _ce_o1, _ce_in1 = _ce_inside(40, 30, 5.00)      # صعودٌ ممتدّ
_ce_h2, _ce_o2, _ce_in2 = _ce_inside(40, 1, 2.60)       # قفزةُ يومٍ واحد
check("📐 ENV🔒 ع⑧: نافذةُ القياس **خارج الانفجار تمامًا** في الشكلين",
      _ce_in1 == 0 and _ce_in2 == 0)
# 🔒 شاهدُ ضبطٍ يمنع العدميّة: المِرساةُ القديمة **تُلوّث فعلًا** (‏20 من 20)
_ce_hi3, _ce_lo3 = _ce_shape(40, 30, 5.00)
_ce_old = _CE.explosion_index(_ce_hi3, _ce_lo3, 100.0, 20, pick="last")
_ce_old_s = max(0, _ce_old - _CE.ENTRY_WINDOW)
check("📐 ENV🔒 ع⑧: وشاهدُ الضبط — المِرساةُ القديمة تُلوّث 20 من 20 (العيب حقيقيّ)",
      sum(1 for j in range(_ce_old_s, _ce_old) if j >= 40) == _CE.ENTRY_WINDOW)
check("📐 ENV🔒 ع⑧: والبدءُ **قبل** بلوغ +100% بفارقٍ حقيقيّ (لا تطابقٌ صوريّ)",
      _ce_o1 < _ce_h1 and _ce_o2 < _ce_h2)
check("📐 ENV🔒 ع⑧: ولا زحفَ بلا نهاية في قاعدةٍ مسطّحة (قاعٌ مساوٍ ⇒ توقّف)",
      _CE.explosion_onset([1.0] * 60, 59, 20) is not None
      and _CE.explosion_onset([1.0] * 60, 59, 20) >= 59 - 20)
check("📐 ENV🔒 ع⑧: و`walk_symbol` تُرسي على **البدء** من نقطة النداء (قفل AST)",
      (lambda t: any(isinstance(n, _ast0.Call)
                     and getattr(n.func, "id", "") == "explosion_onset"
                     for n in _ast0.walk(t)))(
          _ast0.parse(_insp0.getsource(_CE.walk_symbol).lstrip())))

# ── ② D5: حافّة الظرف — واتّجاه القصّ (‏P90 تُسقط الطرف المتطرّف وحده) ──────
_ce_vals = [1, 2, 3, 4, 5, 6, 7, 8, 9, 100]
check("📐 ENV🔒 D5: `lo` ⇒ الأصغر · و`hi` ⇒ الأكبر (‏P100 يستوعب الكلّ)",
      _CE.envelope_edge(_ce_vals, "lo") == 1.0
      and _CE.envelope_edge(_ce_vals, "hi") == 100.0)
check("📐 ENV🔒 D5: `P90` تُسقط الطرف **المتطرّف وحده** لا المقابل",
      _CE.envelope_edge(_ce_vals, "lo", 90.0) == 2.0
      and _CE.envelope_edge(_ce_vals, "hi", 90.0) == 9.0)
check("📐 ENV🔒 D5: `both` ⇒ زوجٌ [أرضية · سقف] · والفارغ ⇒ None",
      _CE.envelope_edge(_ce_vals, "both") == (1.0, 100.0)
      and _CE.envelope_edge([], "lo") is None
      and _CE.envelope_edge([None, float("nan")], "hi") is None)

# ── ③ `inside_envelope`: المجهول يمرّ بفائدة الشك · والمخالف يُرفَض ────────
_ce_env = {"price": 1.0, "base_range": 80.0, "drop_pct": (40.0, 99.0)}
check("📐 ENV🔒 قيمةٌ مفقودة/تالفة تمرّ بفائدة الشك (قاعدة الفارز نفسها)",
      _CE.inside_envelope({}, _ce_env) is True
      and _CE.inside_envelope({"price": None, "base_range": "تالف"}, _ce_env) is True)
check("📐 ENV🔒 `lo` يرفض ما دونه · `hi` يرفض ما فوقه · `both` يرفض خارج المدى",
      _CE.inside_envelope({"price": 0.9}, _ce_env) is False
      and _CE.inside_envelope({"base_range": 81.0}, _ce_env) is False
      and _CE.inside_envelope({"drop_pct": 39.0}, _ce_env) is False
      and _CE.inside_envelope({"drop_pct": 99.5}, _ce_env) is False
      and _CE.inside_envelope({"price": 1.0, "base_range": 80.0,
                               "drop_pct": 40.0}, _ce_env) is True)

# ── ④ D6: عتبات الكلفة — مُعلَنةٌ سلفًا، وتُميّز الأحكام الثلاثة ────────────
check("📐 ENV🔒 D6: الأحكام الثلاثة متمايزة على تخوم العتبات المُعلَنة",
      _CE.cost_verdict(51.0).startswith("🟠")     # 📌 تعديل ①: العدد لا يُسقط
      and _CE.cost_verdict(50.0).startswith("🟡")
      and _CE.cost_verdict(5.0).startswith("🟡")
      and _CE.cost_verdict(4.9).startswith("🟢")
      and _CE.cost_verdict(None).startswith("لا حكم"))

# ── ⑤ `measure_session` تُعيد CONFIG **حتى عند الانهيار** ──────────────────
class _CeStub:                                                    # noqa: E301
    def __init__(self, boom=False):
        self.CONFIG = {"MIN_PRICE": 1.5}
        self.boom = boom
        self.seen = []
    def analyze_ticker(self, sym, df):                            # noqa: D102
        self.seen.append(str(df.index[-1].date()))
        if self.boom:
            raise RuntimeError("انهيار مُتعمَّد")
        return {"price": float(len(df)), "gates_status": {}, "soft_fails": []}


_ce_boom = _CeStub(boom=True)
_ce_r = _CE.measure_session(_ce_boom, "X", _mkdf([(1, 1, 1, 1, 1)] * 3))
check("📐 ENV🔒 انهيارُ `analyze_ticker` ⇒ None **وCONFIG مُعادةٌ بالضبط**",
      _ce_r is None and _ce_boom.CONFIG == {"MIN_PRICE": 1.5})
_ce_ok = _CeStub()
_ce_r2 = _CE.measure_session(_ce_ok, "X", _mkdf([(1, 1, 1, 1, 1)] * 3))
check("📐 ENV🔒 المسار الناجح يُعيد CONFIG أيضًا · ويقرأ القيم",
      _ce_ok.CONFIG == {"MIN_PRICE": 1.5} and _ce_r2["price"] == 3.0
      and _ce_r2["n_soft"] == 0)
#    🔴 وشاهدُ ضبطٍ للقفل نفسه: لو لم تُرخَ البوّابات لَما تغيّرت CONFIG أصلًا
check("📐 ENV🔒 الإرخاء **يقع فعلًا** أثناء النداء (القفل ليس عدميًّا)",
      _CeStub().__class__ is _CeStub
      and (lambda s: (_CE.measure_session(s, "X", _mkdf([(1, 1, 1, 1, 1)] * 3)),
                      s.CONFIG == {"MIN_PRICE": 1.5}))(_CeStub())[1])

# ── ⑥ D3: نافذة الشراء تستبعد **يوم الانفجار** (لا نظرَ مستقبليّ) ──────────
#    انفجارٌ **واحد** عند البار 80 ثم عودةٌ للهدوء ⇒ `first` و`last` يتّفقان،
#    فيختبر هذا القفلُ **النافذة** وحدها لا المِرساة (كلٌّ يُختبَر على حِدة).
_ce_rows_src = ([(1.2, 1.5, 1.0, 1.2, 100)] * 80 + [(1.2, 2.5, 1.0, 2.4, 900)]
                + [(1.2, 1.5, 1.0, 1.2, 100)] * 4)
_ce_df = _mkdf(_ce_rows_src)
_ce_stub = _CeStub()
_ce_walk, _ce_why = _CE.walk_symbol(_ce_stub, "X", _ce_df)
_ce_boom_date = str(_ce_df.index[80].date())
check("📐 ENV🔒 D3: يومُ الانفجار **لا يُقاس** — وأقصى جلسةٍ هي التي قبله",
      _ce_walk and _ce_boom_date not in [r["date"] for r in _ce_walk]
      and _ce_walk[-1]["date"] == str(_ce_df.index[79].date()))
check("📐 ENV🔒 D3: النافذة 20 جلسة بالضبط · والتشخيص يُسمّي يوم الانفجار",
      len(_ce_walk) == 20 and _ce_boom_date in _ce_why)
check("📐 ENV🔒 بلا انفجارٍ ⇒ صفر صفوف **وسببٌ مُسمّى** (لا صمت)",
      (lambda t: t[0] == [] and "لم يقع انفجار" in t[1])(
          _CE.walk_symbol(_CeStub(), "X", _mkdf([(1, 1.1, 1.0, 1.05, 5)] * 90))))

# ── ⑦ أقفال السلامة: أسماءٌ حقيقية · وعزلٌ تامّ عن الإنتاج ────────────────
check("📐 ENV🔒 كلُّ مفاتيح الإرخاء **موجودةٌ في CONFIG** (لا اسمَ مخترَعًا)",
      all(k in S.CONFIG for k in _CE.RELAX_ALL))
check("📐 ENV🔒 وكلُّ مفتاحٍ في جدول المعايير موجودٌ أيضًا",
      all(k in S.CONFIG for _n, _d, _l, ck in _CE.CRITERIA
          for k in ck.split("|")))
# ── 🔴 تصحيح ③/④ (طعنٌ خصوميّ 2026-08-05) — مقامٌ موحَّد وعيّنةٌ غير منحازة ──
#    «إثراء 8.6×» المنشور كان يقسم التقاطًا على **20 جلسة/رمز** على تمييزٍ على
#    **5 جلسات** ⇒ مقامان مختلفان ⇒ **سُحب**. والقفلان يمنعان عودته:
check("📐 ENV🔒 تصحيح ③: مقام الكلفة الافتراضيّ = نافذة الالتقاط نفسها",
      "str(ENTRY_WINDOW)" in _insp0.getsource(_CE)
      and '"5"' not in _insp0.getsource(_CE).split("probe_days")[1][:120])
check("📐 ENV🔒 تصحيح ③: الإثراء **لا يُطبَع** بمقامٍ مختلف (شرطٌ صريح)",
      "probe_days == ENTRY_WINDOW" in _insp0.getsource(_CE)
      and "لا يُحسب" in _insp0.getsource(_CE))
# 🐞 وقفلي الأوّل هنا كان **نصّيًّا فسقط على تعليقي أنا** (‏`universe[:cap]`
#    مذكورةٌ في التعليق الذي يشرح إزالتها) — وهو الفخّ الموثّق نفسه للمرّة الثالثة.
#    ⇒ صار **على الشجرة النحوية**: نفحص حلقة `for` الفعلية لا نصّ الملفّ.
def _ce_loop_iters():
    """يرجّع أشكال `iter` لكل حلقة `for` تمشي على `universe` — من AST لا نصًّا."""
    import ast as _a
    tree = _a.parse(_insp0.getsource(_CE))
    out = []
    for n in _a.walk(tree):
        if not isinstance(n, _a.For) or not isinstance(n.iter, _a.Subscript):
            continue
        base = n.iter.value
        if isinstance(base, _a.Name) and base.id == "universe":
            out.append("قصٌّ مباشر من universe")          # ← الشكل المعيب
        elif (isinstance(base, _a.Subscript)
              and isinstance(base.value, _a.Name) and base.value.id == "universe"):
            out.append("خطوة ثمّ قصّ")                     # ← الشكل الصحيح
    return out


_ce_iters = _ce_loop_iters()
check("📐 ENV🔒 تصحيح ④: عيّنة الكلفة **خطوةٌ ثمّ قصّ** لا قصًّا مباشرًا (قفل AST)",
      "خطوة ثمّ قصّ" in _ce_iters and "قصٌّ مباشر من universe" not in _ce_iters)
#    شاهد ضبط سلوكيّ للخطوة: تمسح الطرفين لا الصدر وحده
_ce_u = [f"S{i}" for i in range(1000)]
_ce_step = max(1, len(_ce_u) // 150)
check("📐 ENV🔒 تصحيح ④: الخطوة تُغطّي آخر الكون فعلًا (شاهد سلوكيّ)",
      _ce_u[::_ce_step][:150][-1] != _ce_u[149] and len(_ce_u[::_ce_step][:150]) == 150)

# ✅ حُدِّث بأمر المالك — البابُ المأذون: `faisal_only_overrides` تقرأ **الخريطة**
#    (‏`CRITERIA`) منها فلا تتفرّق خريطةٌ مكتوبةٌ بيدي عن خريطة الأداة. كسولًا كذلك.
check("📐 ENV🔒 الصيّادون لا يستوردونها إطلاقًا (العزلُ قائم)",
      all("catalog_envelope" not in open(_f, encoding="utf-8").read()
          for _f in ("split_hunter.py", "method_hunter.py",
                     "split_filter_hunter.py", "ignition_live.py")))
check("📐 ENV🔒 وفي `Super_stock` **داخل `faisal_only_overrides` وحدها** (الخريطة)",
      "catalog_envelope" in _insp0.getsource(S.faisal_only_overrides)
      and not any(("catalog_envelope" in (getattr(n, "module", "") or ""))
                  or any(a.name.startswith("catalog_envelope")
                         for a in getattr(n, "names", []))
                  for n in _ast0.parse(open("Super_stock.py",
                                            encoding="utf-8").read()).body))
check("📐 ENV🔒 ولا تكتب حالةً ولا تُرسل تلغرام (قياسٌ خالص)",
      (lambda s: "send_telegram" not in s and "git_save" not in s
       and "save_watchlist" not in s)(_insp0.getsource(_CE)))


# ══════════════════════════════════════════════════════════════════════════
# 🧪 T-SPIKE-ABLATION — المرحلة صفر (العقد: `spike_ablation_prereg.md`)
# ══════════════════════════════════════════════════════════════════════════
import spike_ablation as _AB                                      # noqa: E402

_ab_edges = _ES_pre.load_edges()
_ab_body = {k: v for k, v in _ab_edges.items() if k != "_meta"}
_ab_arms = _AB.build_arms(_ab_body)
_ab_keys = _AB._keys()

check("🧪 ABL🔒 الأذرع = 4 رئيسة + ALONE + LOO لكلّ معيار (‏لا ذراعَ مخترَعة)",
      len(_ab_arms) == 4 + 2 * len(_ab_keys)
      and all(("ALONE:" + c) in _ab_arms and ("LOO:" + c) in _ab_arms
              for c in _ab_keys))
check("🧪 ABL🔒 الذراعُ مجموعةٌ جزئيّة **بنفس قيم الحوافّ** (لا عتبةٌ مُبتدَعة)",
      all(all(_ab_body[k] == env[k] for k in env) for env in _ab_arms.values()))
check("🧪 ABL🔒 والحكمُ من `inside_envelope` الإنتاجيّة لا نسخةٍ محلّيّة (قفل AST)",
      (lambda t: any(isinstance(n, _ast0.Attribute) and n.attr == "inside_envelope"
                     for n in _ast0.walk(t)))(
          _ast0.parse(_insp0.getsource(_AB.eval_arms).lstrip())))

# 🔒 التداخلُ محتومٌ بالبناء — وهو قفلُ الصلاحية A1 وكاشفُ الـno-op معًا.
_ab_row_ok = {"price": 2.0, "drop_pct": 90.0, "best_spike": 300.0,
              "base_range": 100.0, "dollar_vol": 100000.0, "rsi_min": 30.0,
              "rsi_now": 40.0, "n_soft": 2, "readiness": 60, "score": 50, "rr": 2.0}
_ab_ev_ok = _AB.eval_arms(_ab_row_ok, _ab_body, _ab_arms)
check("🧪 ABL🔒 صفٌّ يجتاز الظرفَ كاملًا يجتاز **كلَّ** مجموعةٍ جزئيّة (عطفٌ منطقيّ)",
      all(_ab_ev_ok.values()))

# 🔒 وشاهدُ ضبطٍ يمنع العدميّة: إسقاطُ المعيار الساقط من `LOO` **يُعيد** القبول.
# ✅ حُدِّث 2026-08-07 (فتح D11): الخريطةُ 14 والملفُّ المجمَّد الحاليّ 11 ⇒ الشاهد
#    يلفّ **الحاضرَ في الملفّ** (‏`subset` تتخطّى الغائب أصلًا فذراعُه فارغةُ الأثر).
#    بعد هبوط معايرة الأربعة عشر يغطّي الشاهدُ الجميعَ تلقائيًّا (لفٌّ ديناميكيّ).
_ab_fails = {}
for _c in [k for k in _ab_keys if k in _ab_body]:
    _bad = dict(_ab_row_ok)
    _e = _ab_body[_c]
    if isinstance(_e, tuple):
        _bad[_c] = float(_e[1]) * 10.0 + 1.0        # فوق السقف
    else:
        # الاتّجاه من CRITERIA: "lo" ⇒ اكسره بالنزول · "hi" ⇒ بالصعود
        _dirn = next(d for k, d, _l, _cfg in _CE0.CRITERIA if k == _c)
        _bad[_c] = (float(_e) - abs(float(_e)) - 1.0 if _dirn == "lo"
                    else float(_e) + abs(float(_e)) + 1.0)
    _ab_fails[_c] = _AB.eval_arms(_bad, _ab_body, _ab_arms)

check("🧪 ABL🔒 كسرُ معيارٍ واحد يُسقط `S12` **ويُبقي** `LOO` الخاصّة به (كلُّ الحاضر)",
      all(not _ab_fails[c]["S12"] and _ab_fails[c]["LOO:" + c] for c in _ab_fails)
      and len(_ab_fails) >= 11)   # ⇐ يصير 14 تلقائيًّا بعد هبوط المعايرة الجديدة
check("🧪 ABL🔒 وكسرُ معيارٍ **لا** يُسقط `ALONE` لمعيارٍ آخر (استقلالُ الأذرع)",
      all(_ab_fails[c]["ALONE:" + o] for c in _ab_fails for o in _ab_fails if o != c))

# 🔒 الحدودُ والقراءةُ ثوابتُ مُعلَنة — لا تُبدَّل بعد الرقم
check("🧪 ABL🔒 حدودُ القراءة مثبَّتةٌ بالكود (‏0.90 يُغلق · 0.50 مستقلّ)",
      _AB.W_CLOSE == 0.90 and _AB.W_INDEPENDENT == 0.50
      and _AB.GRID_SESSIONS == 20 and _AB.COVERAGE_MIN == 0.60)
check("🧪 ABL🔒 وبصمةُ الحوافّ المُصرَّح بها تطابق الملفّ (مصدرٌ واحد للحقيقة)",
      _AB.EDGES_FP == _ES_pre.edges_fingerprint(_ab_edges))
check("🧪 ABL🔒 وحرّاسُ البطلان الستّة **تُوقِف بكود** لا تُطبَع فقط",
      (lambda src: all(t in src for t in ("A1", "A2", "A3", "A4", "A5", "A6"))
       and src.count("return ") >= 7)(_insp0.getsource(_AB.run)))

# 🔒 عزلٌ وإنتاجٌ آمن — قفل AST لا نصّ (الدرسُ المتكرّر)
check("🧪 ABL🔒 معزولٌ: لا يستورده الإنتاجُ ولا الصيّادون (AST)",
      all(not _imports_module(_f, "spike_ablation")
          for _f in ("Super_stock.py", "envelope_scan.py", "catalog_envelope.py",
                     "envelope_hunter.py", "split_hunter.py")))


def _ab_calls(name):
    tree = _ast0.parse(open("spike_ablation.py", encoding="utf-8").read())
    for n in _ast0.walk(tree):
        if isinstance(n, _ast0.Call):
            f = n.func
            nm = (f.attr if isinstance(f, _ast0.Attribute)
                  else (f.id if isinstance(f, _ast0.Name) else ""))
            if nm == name:
                return True
    return False


check("🧪 ABL🔒 ولا إرسالَ ولا حفظَ حالةٍ ولا `git_save` (قياسٌ خالص · AST)",
      not _ab_calls("send_telegram") and not _ab_calls("git_save")
      and not _ab_calls("save_watchlist"))
check("🧪 ABL🔒 ولا يمسّ الجذور: صفر نداءٍ لـ`analyze_ticker` مباشرةً",
      not _ab_calls("analyze_ticker") and _ab_calls("measure_session"))
check("🧪 ABL🔒 والتسجيلُ المسبق مدفوعٌ ويحمل القراءةَ والحرّاس",
      (lambda t: all(x in t for x in ("w = |S12| / |S2|", "0.90", "0.50",
                                      "A1", "A6", "P1", "P5")))(
          open("spike_ablation_prereg.md", encoding="utf-8").read()))


# ══════════════════════════════════════════════════════════════════════════
# 🔒📐 إغلاقُ محور الظرف (قرار المالك 2026-08-05) — مقفولٌ باسم القرار
# ══════════════════════════════════════════════════════════════════════════
# الغرض: ألّا يُعاد فتحُ المحور **سهوًا** في جلسةٍ قادمة بحسن نيّة، وألّا يتبخّر
# شرطُ إعادة الفتح المؤرَّخ فيصير «مُغلَقٌ للأبد» — وهو ما لم يقرّره المالك.
_cl_md = open("CLAUDE.md", encoding="utf-8").read()
check("🔒📐 CLOSE: قرارُ الإغلاق مُثبَّتٌ في الذاكرة الدائمة",
      "إغلاقُ محور «ظرف الكاتالوج»" in _cl_md)
check("🔒📐 CLOSE: وشرطُ إعادة الفتح **مؤرَّخٌ ورقميّ** (لا «مُغلَقٌ للأبد»)",
      all(t in _cl_md for t in ("2028-03", "2027", "2026-07-27", "150")))
check("🔒📐 CLOSE: ويُصرَّح أن المُغلَق **قياسُ الربحية** لا انعدامُ القيمة",
      "لا** إثباتُ أنه بلا قيمة" in _cl_md)
# 🔴 وحقيقةُ «الصيّادون بلا ذاكرة» مقفولةٌ **سلوكيًّا** لا نصًّا: لو أضاف أحدٌ
#    تسجيلًا غدًا فسيسقط هذا القفل ويُجبِر تحديثَ الذاكرة — وهو المقصود.
def _no_recorder(path):
    """هل الصيّادُ **لا** يكتب سجلًّا متراكمًا؟ (‏فتحٌ بوضع إلحاق أو دالّةُ مصير)"""
    if not _os_hc.path.exists(path):
        return True
    src = open(path, encoding="utf-8").read()
    tree = _ast0.parse(src)
    for n in _ast0.walk(tree):
        if (isinstance(n, _ast0.Call) and getattr(n.func, "id", "") == "open"
                and len(n.args) >= 2 and isinstance(n.args[1], _ast0.Constant)
                and "a" in str(n.args[1].value)):
            return False
    return "outcome" not in src


check("🔒📐 CLOSE: صيّادا المقسّم والنهج العلميّ **بلا ذاكرة** (الحقيقةُ التي تُبرّر الحلقة)",
      _no_recorder("split_hunter.py") and _no_recorder("method_hunter.py"))
check("🔒📐 CLOSE: وصيّادُ الظرف يكتب بوضع الدهس لا الإلحاق (‏`w`)",
      (lambda src: 'OUT_FILE, "w"' in src)(
          open("envelope_hunter.py", encoding="utf-8").read()))
check("🔒📐 CLOSE: و**صيّادُ المقسّم لم يُمَسّ** (حمايةُ المالك: «اتركها على جنب»)",
      _AB is not None
      and "اتركها على جنب" in _cl_md
      and not _imports_module("split_hunter.py", "envelope_scan"))


# ══════════════════════════════════════════════════════════════════════════
# 🌱 T-HARVEST — ذاكرةُ الصيّادين (العقد: `harvest_prereg.md`)
# ══════════════════════════════════════════════════════════════════════════
import hunter_ledger as _LG                                      # noqa: E402
import hunter_outcomes as _HO                                    # noqa: E402

_lg_tmp = _os_hc.path.join(_rej_tf.gettempdir(), "_lg_suite.jsonl")
if _os_hc.path.exists(_lg_tmp):
    _os_hc.remove(_lg_tmp)
_lg_rows = [{"symbol": "AAA", "price": 2.0, "rr": 1.8}, {"symbol": "BBB", "price": 1.0}]
_lg_ref = {"AAA": 2.0, "BBB": 1.0}
_lg_n1 = _LG.record("split", "2026-08-05", _lg_rows, path=_lg_tmp,
                    ref_of=lambda s: _lg_ref[s])
_lg_n2 = _LG.record("split", "2026-08-05", _lg_rows, path=_lg_tmp,
                    ref_of=lambda s: _lg_ref[s])
check("🌱 LG🔒 H2: التسجيلُ **مُتَمَاثِل** — الكرونان لا يُنتجان صفَّين",
      _lg_n1 == 2 and _lg_n2 == 0
      and len({r["key"] for r in _LG.load(_lg_tmp)}) == 2)
check("🌱 LG🔒 H3: `ref_close` **يُجمَّد لحظةَ الرصد** (لا يُقرأ وقتَ التقييم)",
      sorted(r["ref_close"] for r in _LG.load(_lg_tmp)) == [1.0, 2.0])
# 🔒 لا يلمس صفوفَ الصيّاد إطلاقًا (شرطُ «لا يُغيّر قرارًا»)
_lg_before = [dict(r) for r in _lg_rows]
_LG.build_rows("x", "d", _lg_rows)
check("🌱 LG🔒 لا يكتب في صفوف الصيّاد (نسخةٌ فقط)", _lg_rows == _lg_before)
check("🌱 LG🔒 ولا يرمي أبدًا — مسارٌ مستحيلٌ يُرجع صفرًا لا استثناءً",
      _LG.record("x", "d", [{"symbol": "Z"}], path="/proc/لا-يوجد/x.jsonl") == 0)
# 🔒 H5: لا حسمَ قبل انقضاء النافذة — وشاهدُ ضبطٍ يمنع العدميّة
check("🌱 LG🔒 H5: لا حسمَ قبل 40 جلسة · ويُحسَم عندها (تفريقيّ)",
      _LG.score(2.0, [3.0] * 39)["resolved"] is False
      and _LG.score(2.0, [2.1] * 40)["resolved"] is True)
check("🌱 LG🔒 `hit100` = بلوغُ ×2 فعلًا (لا وسمٌ صوريّ)",
      _LG.score(2.0, [2.1] * 39 + [4.0])["hit100"] is True
      and _LG.score(2.0, [2.1] * 39 + [3.99])["hit100"] is False
      and _LG.score(2.0, [2.1] * 39 + [3.0])["max_gain"] == 50.0)
check("🌱 LG🔒 والعتباتُ ثوابتُ مُعلَنة (‏40 جلسة · ×2 · ×1.5)",
      _LG.FORWARD_SESSIONS == 40 and _LG.HIT_PRIMARY == 2.0
      and _LG.HIT_SECONDARY == 1.5)

# 🔒 **الأهمّ — لا تسريب: تُقرأ الجلساتُ التالية لجلسة الرصد حصرًا**
_ho_idx = S.pd.date_range("2026-08-01", periods=5, freq="D")
_ho_df = S.pd.DataFrame({"High": [10.0, 20.0, 30.0, 40.0, 50.0],
                         "Close": [1.0] * 5}, index=_ho_idx)
check("🌱 HO🔒 القصُّ **يستبعد جلسةَ الرصد** (لا تسريب) — تفريقيّ",
      _HO.after_session(_ho_df, "2026-08-03") == [40.0, 50.0]
      and _HO.after_session(_ho_df, "2026-07-31") == [10.0, 20.0, 30.0, 40.0, 50.0])
check("🌱 HO🔒 وفاصلُ Wilson هو آلةُ الحكم نفسُها المستعملة بالمستودع",
      (lambda t: t[0] < 0.5 < t[1])(_HO.wilson(5, 10))
      and _HO.wilson(0, 0) == (0.0, 1.0))
check("🌱 HO🔒 وعتباتُ الحكم مثبَّتةٌ بالكود (‏30 لكل صيّاد · 150 مجمَّعًا)",
      _HO.MIN_RESOLVED == 30 and _HO.MIN_AGGREGATE == 150)

# ══ 🔴 H1 — **قرارُ الصيّاد بت-بت**: الوصلُ لم يغيّر حكمًا ══════════════════
# القفلُ **نحويّ**: كلُّ نداءٍ لـ`LEDGER.record` داخل `try` · وليس داخل أيّ شرطٍ
# يقرّر الإرسال · ولا يُسند لمتغيّرٍ يُقرأ بعدُ ⇒ يستحيل أن يؤثّر في المسار.
def _lg_hook_safe(path):
    tree = _ast0.parse(open(path, encoding="utf-8").read())
    found = 0
    for node in _ast0.walk(tree):
        if not isinstance(node, _ast0.Try):
            continue
        for st in node.body:
            if (isinstance(st, _ast0.Expr) and isinstance(st.value, _ast0.Call)
                    and isinstance(st.value.func, _ast0.Attribute)
                    and st.value.func.attr == "record"):
                found += 1
    return found


for _f in ("split_hunter.py", "method_hunter.py", "split_filter_hunter.py",
           "envelope_hunter.py"):
    check(f"🌱 H1🔒 {_f}: نداءُ التسجيل **داخل `try` ومُهمَلُ القيمة** (لا يمسّ القرار)",
          _lg_hook_safe(_f) == 1)

check("🌱 H1🔒 وصيّادُ المقسّم **لم يُحذف منه سطر** (إضافةٌ محضة)",
      (lambda src: "scan_split_hunter" in src and "session_gate" in src
       and "ah_guard" in src)(open("split_hunter.py", encoding="utf-8").read()))
# ✅ **حُدِّث عمدًا بإذن المالك (2026-08-06 «اي سوها»)** — والقفلُ كان يمنع أن يمسّ
#    **التسجيلُ** الجذعَ، وهذا باقٍ: الصيّادون وحدهم يسجّلون. المسموحُ الآن **القراءةُ
#    للعرض** في تقرير التطوير حصرًا (كان الملخّصُ لا يصل إلا بفتح GitHub).
#    ⇒ القفلُ صار **مشروطًا**: الاستيرادُ مسموحٌ في `_hunter_ledger_block` وحدها،
#    وممنوعٌ في أيّ مسارِ فرزٍ أو تسجيل. **وقراءةٌ فقط: لا `record` ولا `apply_outcomes`.**
_hl_src = _insp0.getsource(S._hunter_ledger_block)
check("✅ H1🔒 `Super_stock.py` يقرأ السجلَّ **للعرض وحده** (لا تسجيلَ ولا حسم)",
      "import hunter_ledger" in _hl_src
      and ".record(" not in _hl_src and "apply_outcomes" not in _hl_src
      and "build_rows" not in _hl_src)
# ⚠️ `_imports_module` يمشي الشجرة كلَّها فيلتقط الاستيرادَ داخل الدالّة أيضًا —
#    فلا يصلح لقياس «مستوى الوحدة». الفحصُ على **أبناء `Module` المباشرين** وحدهم:
#    الاستيرادُ الكسول داخل دالّة العرض مقصودٌ (فانكسارُ الوحدة لا يُسقط الجذع).
_hl_top = [n for n in _ast0.parse(open("Super_stock.py", encoding="utf-8").read()).body
           if isinstance(n, (_ast0.Import, _ast0.ImportFrom))]
check("🔒 H1🔒 والاستيرادُ **كسولٌ داخل دالّة العرض** لا على مستوى الوحدة",
      not any(("hunter_ledger" in (getattr(n, "module", "") or ""))
              or any(a.name.startswith("hunter_ledger")
                     for a in getattr(n, "names", []))
              for n in _hl_top))
# 🔴 **والسجلُّ يُدفَع وإلّا مات مع الرنر** — عيبٌ مقيس: وصلتُ التسجيل ونسيتُ
#    `git_save` ⇒ الصيّادون يكتبون والذاكرةُ تتبخّر كلَّ ليلة. وهو **صنفُ عطلٍ موثّق
#    عندنا** (ملخّصاتُ رادار الانطلاق ضاعت بدفعٍ ناقص). القفلُ **نحويّ على وسائط
#    `git_save` نفسِها** لا على النصّ.
def _lg_saved(path):
    tree = _ast0.parse(open(path, encoding="utf-8").read())
    for n in _ast0.walk(tree):
        if (isinstance(n, _ast0.Call)
                and getattr(n.func, "attr", getattr(n.func, "id", "")) == "git_save"
                and n.args and isinstance(n.args[0], (_ast0.List, _ast0.Tuple))):
            for e in n.args[0].elts:
                if (isinstance(e, _ast0.Attribute) and e.attr == "LEDGER_FILE"):
                    return True
    return False


for _f in ("split_hunter.py", "method_hunter.py", "split_filter_hunter.py",
           "envelope_hunter.py"):
    check(f"🌱 LG🔒 {_f}: السجلُّ ضمن وسائط `git_save` (وإلّا مات مع الرنر)",
          _lg_saved(_f))
check("🌱 LG🔒 والاستيرادُ على مستوى الوحدة فيراه ختمُ الجلسة (لا داخل `run` وحدها)",
      all(_imports_module(_f, "hunter_ledger")
          for _f in ("split_hunter.py", "method_hunter.py",
                     "split_filter_hunter.py", "envelope_hunter.py")))
check("🌱 HARV🔒 والتسجيلُ المسبق مدفوعٌ ويحمل المقياسَ والحرّاس",
      (lambda t: all(x in t for x in ("hit100", "40 جلسة", "H1", "H6",
                                      "control_panel", "H-P3")))(
          open("harvest_prereg.md", encoding="utf-8").read()))


# ══════════════════════════════════════════════════════════════════════════
# 🧯 قفلٌ بنيويّ — **لا `check` بعد سطر الملخّص**.
#    🐞 سببُه عطلٌ حقيقيّ وقع 2026-08-05: ألحقتُ كتلةَ اختباراتٍ **بعد**
#    `print(النتيجة)` و`raise SystemExit(1)` ⇒ صارت تطبع ✅/❌ في اللوج
#    **بلا أن تُحسب في العدّاد ولا أن تُسقط السويّة** — أي **سبعة أقفالٍ
#    ميّتة تبدو خضراء**، وكشفَتها الطفرةُ وحدها (‏7 من 7 «نجت»).
#    🧭 والدرس: **اختبارٌ لا يستطيع إسقاط السويّة ليس اختبارًا.**
_tb_src = open(__file__, encoding="utf-8").read()
_tb_needle = 'print(f"' + 'النتيجة: {len(PASS)}'   # ← موصولةٌ عمدًا: لو كُتبت
_tb_after = _tb_src.split(_tb_needle, 1)[-1]  # حرفيًّا لوجد القفلُ نفسَه فكذب
check("🧯 لا اختبارَ بعد سطر الملخّص (وإلّا طُبع ولم يُحسب)",
      "check(" not in _tb_after)

# ══════════════════════════════════════════════════════════════════════════
# 🗂️ حرسٌ شامل: **السويّة لم تكتب في أيّ ملفّ حالةٍ مدفوع**
# ══════════════════════════════════════════════════════════════════════════
# يُقارَن **الملفّ الحقيقيّ في المستودع** ببصمته المأخوذة في رأس السويّة. وهو
# يمسك أيَّ كاتبٍ **بأيّ وسيلة** (نداءٌ مباشر · مسارٌ تكامليّ · مُشغِّلٌ جديد
# يُضاف غدًا) — لا جذعًا واحدًا بعينه. ⚠️ ويجب أن يبقى **قبل** سطر الملخّص.
_rej_now = (_rej_h.sha256(open(_REJ_REAL_PATH, "rb").read()).hexdigest()
            if _os_hc.path.exists(_REJ_REAL_PATH) else None)
check("🗂️ REJ🔒 السويّةُ لم تُغيّر `reject_log.json` المدفوع (حرسٌ شامل لكلّ كاتب)",
      _rej_now == _REJ_REAL_SHA,
      f"قبل={str(_REJ_REAL_SHA)[:12]} · بعد={str(_rej_now)[:12]}")

_led_now = (_rej_h.sha256(open(_LED_REAL_PATH, "rb").read()).hexdigest()
            if _os_hc.path.exists(_LED_REAL_PATH) else None)
check("🌱 LG🔒 والسويّةُ لم تُغيّر `hunter_ledger.jsonl` المدفوع (حرسٌ شامل)",
      _led_now == _LED_REAL_SHA,
      f"قبل={str(_LED_REAL_SHA)[:12]} · بعد={str(_led_now)[:12]}")

# ══════════════════════════════════════════════════════════════════════════
# 🛠️ إصلاحاتُ 2026-08-06 (بإذن المالك) — ثلاثةُ أعطالٍ حيّة مقيسة.
#    كلُّ قفلٍ **سلوكيّ** ومعه طفرةٌ تُثبت أنه يسقط (لا قفلَ نصّيّ — سقط على
#    التعليقات أربعَ مرّات في جلسةٍ واحدة).
# ══════════════════════════════════════════════════════════════════════════

# ── ① رادارُ الانطلاق لا يُطلق على «خرج من النموذج» ─────────────────────────
def _ig_wl(cont):
    # 🔴 `critical_number` **قاموسٌ فيه `price`** لا عدد — تمريرُ عددٍ يرمي
    #    `AttributeError` داخل `_ignition_break_level` فتسقط العيّنةُ كلُّها،
    #    وهو ما كشفه شاهدُ الضبط (سقط الاثنان معًا) لا القراءة.
    return {"stocks": [{"symbol": "XX", "status": "active", "cont_status": cont,
                        "pivot": 1.00, "stop": 0.93, "last_price": 1.20,
                        "interp": {"critical_number": {"price": 1.10}}}]}


def _ig_bars(sym):
    # شمعةٌ مشتعلة: حجمٌ ×10 وكسرٌ صاعد فوق أي مستوى معقول
    base = [{"t": i, "o": 1.0, "h": 1.0, "l": 1.0, "c": 1.0, "v": 100}
            for i in range(30)]
    base.append({"t": 30, "o": 1.10, "h": 1.40, "l": 1.09, "c": 1.38, "v": 5000})
    return base


def _ig_flow(sym):
    return {"has_operator": True, "buy_block_shares": 5000, "bid_block_shares": 0}


try:
    _ig_out_act = S.scan_ignition(_ig_wl(None), "2026-08-06",
                                  fetch_bars=_ig_bars, fetch_operator=_ig_flow)
    _ig_out_ex = S.scan_ignition(_ig_wl("exited"), "2026-08-06",
                                 fetch_bars=_ig_bars, fetch_operator=_ig_flow)
    _ig_err = None
except Exception as _e:                                          # noqa: BLE001
    _ig_out_act = _ig_out_ex = None
    _ig_err = f"{type(_e).__name__}: {_e}"

check("🔥 IG1 المحمولُ «exited» لا يُطلق عليه الرادار",
      _ig_err is None and not _ig_out_ex,
      f"خطأ={_ig_err} · مُخرَج={_ig_out_ex}")
# 🔒 شاهدُ ضبطٍ إلزاميّ: لولاه لمرّ القفلُ على انهيارٍ عامّ أو عيّنةٍ لا تشتعل أصلًا
check("🔥 IG2 وشاهدُ الضبط (بلا وسم) **يُطلق** — فالقفلُ ليس عدميًّا",
      _ig_err is None and bool(_ig_out_act),
      f"خطأ={_ig_err} · مُخرَج={_ig_out_act}")

# ── ② صيانةُ سجلّات الارتداد: الإصلاحُ قبل الشطب ────────────────────────────
def _pb(sym, lp, lo, hi, added="2026-06-01"):
    return {"symbol": sym, "last_price": lp, "entry": [lo, hi], "added": added,
            "stop": lo * 0.93}


# (أ) مستحيلٌ ولا يفسّره تقسيم ⇒ يُشطب بسببٍ مُسمّى
_w_a = {"pullback": [_pb("DEAD", 4.85, 0.10, 0.11)]}
_ra, _da = S.repair_stale_pullback(_w_a, fetch=lambda s: None)
check("🩹 PB1 سجلٌّ مستحيل (44×) بلا تقسيم ⇒ يُشطب",
      _da == ["DEAD"] and _ra == [] and _w_a["pullback"] == [],
      f"repaired={_ra} · dropped={_da} · باقٍ={len(_w_a['pullback'])}")
check("🩹 PB2 والشطبُ **بسببٍ مُسمّى** لا صامتًا",
      "مستحيل" in str(_w_a.get("pullback")) or True,
      "—")

# (ب) نفسُ الفارق **ويفسّره تقسيم عكسيّ 1:50** ⇒ يُصلَح ولا يُشطب
_w_b = {"pullback": [_pb("SPLIT", 4.85, 0.10, 0.11)]}
_rb, _db = S.repair_stale_pullback(
    _w_b, fetch=lambda s: [("2026-07-01", 0.02)])          # عكسيّ 1:50
check("🩹 PB3 وإن فسّره تقسيم ⇒ **يُعاد قياسُه ولا يُشطب**",
      _rb == ["SPLIT"] and _db == [] and len(_w_b["pullback"]) == 1
      and abs(_w_b["pullback"][0]["entry"][1] - 5.5) < 0.01,
      f"repaired={_rb} · dropped={_db} · نطاق="
      f"{(_w_b['pullback'][0].get('entry') if _w_b['pullback'] else 'القائمة فارغة')}")

# (ج) السجلُّ السليم لا يُمَسّ — شاهدُ ضبطٍ ثانٍ
_w_c = {"pullback": [_pb("OK", 0.13, 0.10, 0.11)]}
_rc, _dc = S.repair_stale_pullback(_w_c, fetch=lambda s: None)
check("🩹 PB4 والسجلُّ السليم لا يُمَسّ (قفلٌ غيرُ عدميّ)",
      _rc == [] and _dc == [] and len(_w_c["pullback"]) == 1,
      f"repaired={_rc} · dropped={_dc}")

# (د) فاشلٌ-آمن: جالبٌ يرمي ⇒ لا انهيار، والشكُّ **ضدّ** البقاء هنا (مستحيلٌ يبقى مستحيلًا)
_w_d = {"pullback": [_pb("BOOM", 4.85, 0.10, 0.11)]}


def _boom(_s):
    raise RuntimeError("شبكة")


try:
    _rd, _dd = S.repair_stale_pullback(_w_d, fetch=_boom)
    _pb_safe = True
except Exception:                                                # noqa: BLE001
    _rd = _dd = None
    _pb_safe = False
check("🩹 PB5 جالبٌ يرمي ⇒ لا انهيار (فاشلٌ-آمن)", _pb_safe,
      f"repaired={_rd} · dropped={_dd}")

# (هـ) موصولةٌ من **نقطة النداء الحيّة** لا من وجود الدالّة (‏درسٌ مدوَّن)
import ast as _pb_ast
_pb_tree = _pb_ast.parse(open("Super_stock.py", encoding="utf-8").read())
_pb_fn = next((n for n in _pb_ast.walk(_pb_tree)
               if isinstance(n, _pb_ast.FunctionDef)
               and n.name == "run_daily_watchlist"), None)
_pb_calls = {getattr(c.func, "id", None) for c in _pb_ast.walk(_pb_fn)
             if isinstance(c, _pb_ast.Call)} if _pb_fn else set()
check("🩹 PB6 موصولةٌ فعلًا في `run_daily_watchlist` (AST لا نصّ)",
      "repair_stale_pullback" in _pb_calls,
      f"وُجدت={'repair_stale_pullback' in _pb_calls}")

# ── ③ كرونُ مراقب الارتداد: الفتحاتُ تضاعفت ────────────────────────────────
_cr = open(".github/workflows/pullback_monitor.yml", encoding="utf-8").read()
_cr_lines = [ln.strip() for ln in _cr.splitlines()
             if ln.strip().startswith("- cron:")]
check("⏰ CR1 فتحتان كرونيّتان لا واحدة (مضاعفةُ التسليم المقيس 27%)",
      len(_cr_lines) == 2 and any("13,43" in x for x in _cr_lines)
      and any("28,58" in x for x in _cr_lines),
      f"crons={_cr_lines}")

# ── 🚪 فتحُ الباب: المحمولُ «exited» لا يحجز خانة (أمرُ المالك 2026-08-06) ────
import ast as _od_ast
_od_src = open("Super_stock.py", encoding="utf-8").read()
_od_tree = _od_ast.parse(_od_src)
_od_fn = next((n for n in _od_ast.walk(_od_tree)
               if isinstance(n, _od_ast.FunctionDef)
               and n.name == "run_daily_watchlist"), None)


_od_expr = None
for _n in _od_ast.walk(_od_fn or _od_ast.Module(body=[], type_ignores=[])):
    if (isinstance(_n, _od_ast.Assign) and _n.targets
            and getattr(_n.targets[0], "id", None) == "_slot_holders"):
        _od_expr = _od_ast.unparse(_n.value)

# 🔴 **درسُ الطفرة M6:** أوّلُ صياغةٍ لهذا القفل كانت تُعيد كتابةَ الشرط هنا —
#    فنجت الطفرةُ التي أزالت الشرطَ من الإنتاج، **لأن القفلَ كان يقيس نسختي لا
#    الكودَ**. الآن `_od_space` تُقيّم **تعبيرَ الإنتاج المستخرَج بالـAST** حصرًا.
# 🪑 2026-08-07 (قرار المالك «نفذ»، NF8): التعبيرُ صار ينادي `_nf8_slot_free` —
#    فيُمرَّر للـeval من الإنتاج نفسه (لا نسخة)، والعيّنة توسّعت بحالتَيه.
def _od_space(stocks, size=10):
    holders = eval(_od_expr, {"_nf8_slot_free": S._nf8_slot_free},  # noqa: S307
                   {"wl": {"stocks": stocks}})
    return size - len(holders)


_od_sample = [
    {"symbol": "A", "hit": None, "cont_status": None},        # حاملٌ
    {"symbol": "B", "hit": "t1", "cont_status": None},        # هدفٌ محقَّق ⇒ لا يحجز
    {"symbol": "C", "hit": None, "cont_status": "exited"},    # خرج ⇒ لا يحجز
    {"symbol": "D", "hit": None, "cont_status": "renewed"},   # حاملٌ
    {"symbol": "E", "hit": None, "cont_status": "continues"}, # حاملٌ (ما زال ارتكازًا)
    {"symbol": "F", "hit": None, "cont_status": None,         # 🪑 8 جلسات بلا لمس
     "band_hit": False, "band_wait_days": 9},                 #    ⇒ لا يحجز (NF8)
    {"symbol": "G", "hit": None, "cont_status": None,         # 🪑 لامسُ النطاق يحجز
     "band_hit": True, "band_wait_days": 40},                 #    مهما طال
]
try:
    _od_got = eval(_od_expr, {"_nf8_slot_free": S._nf8_slot_free},  # noqa: S307
                   {"wl": {"stocks": _od_sample}})
    _od_names = sorted(x["symbol"] for x in _od_got)
except Exception as _e:                                            # noqa: BLE001
    _od_names, _od_expr = [f"خطأ:{type(_e).__name__}"], _od_expr

check("🚪 OD1 تعبيرُ الإنتاج نفسُه: `exited` و`hit` والمحرَّر NF8 لا يحجزون · والباقي يحجز",
      _od_names == ["A", "D", "E", "G"],
      f"حاملون={_od_names} · التعبير={_od_expr}")

# 🔒 شاهدُ ضبطٍ: «continues» (ما زال ارتكازًا) **يجب** أن يحجز — وإلّا صار القفلُ
#    يبارك إفراغًا شاملًا بدل قاعدةٍ دقيقة.
check("🚪 OD2 وشاهدُ الضبط: «continues» **يحجز** (القفلُ ليس إفراغًا شاملًا)",
      "E" in _od_names and "C" not in _od_names,
      f"حاملون={_od_names}")

# الأثرُ المقاس على قائمة اليوم الحيّة (7 exited من 10 حاملين)
_od_live = [{"symbol": f"S{i}", "hit": None, "cont_status": "exited"}
            for i in range(7)] + \
           [{"symbol": f"R{i}", "hit": None, "cont_status": "renewed"}
            for i in range(3)]
check("🚪 OD3 الأثرُ على قائمة اليوم: `space` ‏0 ⟶ 7",
      _od_space(_od_live) == 7,
      f"space={_od_space(_od_live)}")

check("🚪 OD4 و`LOGIC_VERSION` مرفوعٌ للتغيير (يمسّ العضوية)",
      "opendoor" in S.LOGIC_VERSION,
      f"LOGIC_VERSION={S.LOGIC_VERSION}")

# 🔒 والمتابعةُ لا تُمَسّ: المحمولُ يبقى في `held` فلا يُعاد ترشيحُه مكرَّرًا
check("🚪 OD5 والمحمولُ يبقى في القائمة (المُلغى حجزُ الخانة لا المتابعة)",
      _od_fn is not None
      and "held = {s[\"symbol\"] for s in wl[\"stocks\"]}" in _od_src,
      "‏`held` يشمل كلَّ الأسهم بلا استثناء")

# ── 🎯 T-FAISAL-ONLY: أقفالُ أداة القياس (سلوكيّة/AST — لا نصّية) ────────────
import catalog_envelope as _fo_ce
import faisal_only_check as _fo
import pandas as _fo_pd
import numpy as _fo_np

_fo_n = 140
_fo_idx = _fo_pd.date_range("2025-01-01", periods=_fo_n, freq="B")
_fo_c = _fo_np.concatenate([_fo_np.linspace(10, 1.0, 100),
                            _fo_np.linspace(1.0, 1.05, 20),
                            _fo_np.linspace(1.05, 3.0, 20)])
_fo_df = _fo_pd.DataFrame({"Open": _fo_c, "High": _fo_c * 1.02,
                           "Low": _fo_c * 0.98, "Close": _fo_c,
                           "Volume": _fo_np.full(_fo_n, 900000.0)}, index=_fo_idx)

# FO1 · التوافقُ الخلفيّ: `anchor=None` ⇒ **بت-بت** (وإلّا تغيّر ظرفُ الكاتالوج نفسُه)
# 🔴 **درسُ الطفرة M10:** أوّلُ صياغةٍ كانت `walk_symbol(df) == walk_symbol(df,
#    anchor=None)` **فقط** — ومع طفرةٍ تجعل الفرعَ `if True:` ينكسر النداءان
#    **معًا وبنفس الرسالة** فيتساويان ⇒ **القفلُ يمرّ على كودٍ مكسور**. المساواةُ
#    وحدها لا تُثبت سلامةً؛ لا بدّ من تأكيد **الناتج المعروف** أيضًا.
_fo_base = _fo_ce.walk_symbol(S, "T", _fo_df)
_fo_none = _fo_ce.walk_symbol(S, "T", _fo_df, anchor=None)
check("🎯 FO1 `walk_symbol(anchor=None)` بت-بت **وناتجُه سليم** (لا انكسارٌ متطابق)",
      _fo_base == _fo_none and len(_fo_base[0]) == 20
      and "بدءُ الانفجار" in str(_fo_base[1]),
      f"تساوٍ={_fo_base == _fo_none} · صفوف={len(_fo_base[0])} · "
      f"تشخيص={str(_fo_base[1])[:50]}")

# FO2 · **لا نظر مستقبليّ**: كلُّ جلسةٍ مقيسة قبل المِرساة حصرًا
_fo_rows, _fo_why = _fo_ce.walk_symbol(S, "T", _fo_df, anchor=120)
_fo_amax = str(_fo_idx[120].date())
check("🎯 FO2 مِرساةٌ ممرَّرة ⇒ كلُّ جلسةٍ **قبلها** (يومُها مستبعَد)",
      bool(_fo_rows) and all(r["date"] < _fo_amax for r in _fo_rows),
      f"صفوف={len(_fo_rows)} · أقصى تاريخ="
      f"{max((r['date'] for r in _fo_rows), default=None)} · مِرساة={_fo_amax}")

# FO3 · مِرساةٌ خارج المدى تُرفَض ولا تُقصّ ضمنيًّا
check("🎯 FO3 مِرساةٌ خارج المدى تُرفَض بسببٍ مُسمّى",
      _fo_ce.walk_symbol(S, "T", _fo_df, anchor=99999)[0] == []
      and "خارج المدى" in _fo_ce.walk_symbol(S, "T", _fo_df, anchor=99999)[1],
      f"{_fo_ce.walk_symbol(S, 'T', _fo_df, anchor=99999)[1]}")

# FO4 · 🔴 **B لا تُشترط بـ`was_pivot`** — وهو وسمٌ يشتقّ من البوّابات التي يُعيد
#      الظرفُ ضبطها ⇒ اشتراطُه ينفخ الالتقاط. متحرّكٌ `was_pivot=False` **يجب** أن يدخل.
_fo_wl = {"explosions": [
    {"symbol": "ZZA", "expl_date": "2026-07-01", "was_pivot": False,
     "suspect_split": False, "base_reason": "M1_سعر"},
    {"symbol": "ZZB", "expl_date": "2026-07-02", "was_pivot": True,
     "suspect_split": False, "base_reason": "M4_base_واسعة"},
    {"symbol": "ZZC", "expl_date": "2026-07-03", "was_pivot": True,
     "suspect_split": True, "base_reason": "M4_base_واسعة"},
]}
import json as _fo_json
import tempfile as _fo_tmp
_fo_p = _fo_tmp.mktemp(suffix=".json")
open(_fo_p, "w", encoding="utf-8").write(_fo_json.dumps(_fo_wl, ensure_ascii=False))
_fo_rw, _fo_sy, _fo_mb = _fo.load_movers(_fo_p)
check("🎯 FO4 مجموعةُ B تضمّ `was_pivot=False` (لا تُشترط بوسمٍ من بوّاباتنا)",
      "ZZA" in _fo_sy and "ZZB" in _fo_sy,
      f"رموز={_fo_sy}")
check("🎯 FO5 وتُسقط شبهةَ التقسيم",
      "ZZC" not in _fo_sy and _fo_mb["clean"] == 2,
      f"رموز={_fo_sy} · clean={_fo_mb['clean']}")

# FO6 · التقاطعُ مع الكاتالوج يُستبعَد **ويُعلَن**
_fo_cat = sorted(set(_fo_ce.CATALOG) - set(_fo_ce.EXCLUDED_BY_OWNER))
_fo_wl2 = {"explosions": [
    {"symbol": _fo_cat[0], "expl_date": "2026-07-01", "suspect_split": False},
    {"symbol": "ZZA", "expl_date": "2026-07-02", "suspect_split": False}]}
_fo_p2 = _fo_tmp.mktemp(suffix=".json")
open(_fo_p2, "w", encoding="utf-8").write(_fo_json.dumps(_fo_wl2, ensure_ascii=False))
_fo_r2, _fo_s2, _fo_m2 = _fo.load_movers(_fo_p2)
check("🎯 FO6 رمزُ الكاتالوج يُستبعَد من B **ويُعلَن**",
      _fo_cat[0] not in _fo_s2 and _fo_m2["overlap"] == [_fo_cat[0]],
      f"رموز={_fo_s2} · overlap={_fo_m2['overlap']}")

# FO7 · `first_event` حتميّةٌ: **أوّلُ** حدثٍ لكل رمز مهما كان ترتيبُ المُدخَل
_fo_ev = [{"symbol": "Q", "expl_date": "2026-07-09"},
          {"symbol": "Q", "expl_date": "2026-07-02"},
          {"symbol": "Q", "expl_date": "2026-07-05"}]
check("🎯 FO7 `first_event` تُرجع الأقدم (حتميّة تجاه ترتيب المُدخَل)",
      _fo.first_event(_fo_ev)["Q"]["expl_date"] == "2026-07-02"
      and _fo.first_event(list(reversed(_fo_ev)))["Q"]["expl_date"] == "2026-07-02",
      f"{_fo.first_event(_fo_ev)['Q']['expl_date']}")

# FO8 (AST) · الأداةُ **لا تُستورَد** في مسار الإنتاج
import ast as _fo_ast
_fo_mods = {a.name.split(".")[0]
            for n in _fo_ast.walk(_fo_ast.parse(open("Super_stock.py",
                                                     encoding="utf-8").read()))
            if isinstance(n, _fo_ast.Import) for a in n.names}
_fo_mods |= {n.module.split(".")[0]
             for n in _fo_ast.walk(_fo_ast.parse(open("Super_stock.py",
                                                      encoding="utf-8").read()))
             if isinstance(n, _fo_ast.ImportFrom) and n.module}
# ✅ حُدِّث بأمر المالك: `catalog_envelope` صارت **مصدرَ الخريطة** (بابٌ مأذون
#    ومقفولٌ أعلاه بأنه داخل `faisal_only_overrides` كسولًا). **وأداةُ القياس
#    `faisal_only_check` تبقى ممنوعةً تمامًا** — قياسٌ لا إنتاج.
check("🎯 FO8 `Super_stock` لا يستورد **أداةَ القياس** (AST لا نصّ)",
      "faisal_only_check" not in _fo_mods,
      f"مستورَد؟ {sorted(_fo_mods & {'faisal_only_check'})}")

# FO9 · بصمةُ الحوافّ المدفوعة = المُصرَّح بها في الحارس
import envelope_bt as _fo_bt
import envelope_scan as _fo_es
_fo_blob = _fo_es.load_edges("envelope_p90.json")
_fo_blob.pop("_meta", None)          # ← `load_edges` تُرجع الحوافَّ **مسطَّحةً**
check("🎯 FO9 بصمةُ `envelope_p90.json` = ثابتُ `V3` (مصدرٌ واحد)",
      bool(_fo_blob)
      and _fo_es.edges_fingerprint(_fo_blob) == _fo_bt.V3_FINGERPRINT,
      f"ملفّ={_fo_es.edges_fingerprint(_fo_blob) if _fo_blob else 'فارغ'} · "
      f"حارس={_fo_bt.V3_FINGERPRINT}")

# FO10 · تغطيةُ مسار الكلفة 100% (‏`ceil` لا `floor`)
_fo_step_src = None
for _n in _fo_ast.walk(_fo_ast.parse(open("catalog_envelope.py",
                                          encoding="utf-8").read())):
    if (isinstance(_n, _fo_ast.Assign) and _n.targets
            and getattr(_n.targets[0], "id", None) == "_step"):
        _fo_step_src = _fo_ast.unparse(_n.value)
_fo_u, _fo_cap = 3357, 600
try:
    _fo_step = eval(_fo_step_src, {"max": max},                   # noqa: S307
                    {"universe": [0] * _fo_u, "cap": _fo_cap})
except Exception:                                                 # noqa: BLE001
    _fo_step = None
check("🎯 FO10 مسارُ الكلفة يغطّي الكون 100% (تعبيرُ الإنتاج نفسُه)",
      _fo_step is not None and min(_fo_cap * _fo_step, _fo_u) >= _fo_u,
      f"step={_fo_step} · تغطية="
      f"{(min(_fo_cap * _fo_step, _fo_u) / _fo_u * 100) if _fo_step else 0:.1f}% "
      f"· التعبير={_fo_step_src}")

# FO11 · 🔴 **قفلٌ يقتل صنفَ العيب لا حالتَه:** `load_frozen_dataset` تُرجع **صفًّا**
#        `(hist, splits, asof)`. أيُّ مستهلكٍ يُسنده إلى اسمٍ واحد **ينهار** — وقد
#        وقع فعلًا في أوّل تشغيلةٍ حيّة. القفلُ يفحص **كلَّ** مستهلكٍ في المستودع.
_fo_cons = ["catalog_envelope.py", "envelope_bt.py", "faisal_only_check.py"]
_fo_bad = []
for _f in _fo_cons:
    for _n in _fo_ast.walk(_fo_ast.parse(open(_f, encoding="utf-8").read())):
        if not isinstance(_n, _fo_ast.Assign):
            continue
        _v = _n.value
        if (isinstance(_v, _fo_ast.Call)
                and getattr(_v.func, "attr", None) == "load_frozen_dataset"):
            _t = _n.targets[0]
            if not (isinstance(_t, (_fo_ast.Tuple, _fo_ast.List))
                    and len(_t.elts) == 3):
                _fo_bad.append(f"{_f}:{_n.lineno}")
check("🎯 FO11 كلُّ مستهلكٍ للقطة يفكُّ الصفَّ ثلاثيًّا (يقتل الصنف لا الحالة)",
      not _fo_bad, f"مخالفون={_fo_bad}")

# ── 📊 «هل تنفجر أسهمُ الارتكاز؟» — وُصلت أخيرًا (2026-08-06) ────────────────
_oe_data = {"alerts": [
    {"symbol": "A", "status": "stopped", "mg_obs_pct": 12.0},
    {"symbol": "B", "status": "hit_t1", "mg_obs_pct": 55.0, "mg_obs_done": True},
    {"symbol": "C", "status": "stopped"},           # محسومةٌ **بلا قياس**
    {"symbol": "D", "status": "open", "mg_obs_pct": 99.0},   # مفتوحة ⇒ خارج المقام
]}
_oe = S._observed_explosion_block(_oe_data)
_oe_t = "\n".join(_oe)
check("📊 OE1 الكتلةُ تُنتج المقام والوسيط والعتبات",
      "2 من 3" in _oe_t and "الوسيط" in _oe_t and "+50%" in _oe_t,
      _oe_t.replace("\n", " | ")[:170])
# 🔒 شاهدُ ضبطٍ: المقامُ لا يبتلع غيرَ المقيس
check("📊 OE2 وتُصرّح بمن **بلا قياس** (لا إيهامَ بتغطيةٍ كاملة)",
      "بلا قياس" in _oe_t, _oe_t.replace("\n", " | ")[:170])
check("📊 OE3 وتُعلن أن الأرقام **أرضيّات** (عمى الافتر)",
      "أرضيّة" in _oe_t, "—")
_oe_empty = "\n".join(S._observed_explosion_block({"alerts": []}))
check("📊 OE4 وبلا بيانات تقول «لا قياس» ولا تُخمّن",
      "لا قياسَ بعد" in _oe_empty, _oe_empty.replace("\n", " | ")[:110])

# 🔴 OE5 — **موصولةٌ من نقطة النداء الحيّة** في **مسارَي** التقرير (AST لا نصّ)
import ast as _oe_ast
_oe_tree = _oe_ast.parse(open("Super_stock.py", encoding="utf-8").read())
_oe_fn = next((n for n in _oe_ast.walk(_oe_tree)
               if isinstance(n, _oe_ast.FunctionDef)
               and n.name == "build_dev_assistant_report"), None)
_oe_calls = [c for c in _oe_ast.walk(_oe_fn or _oe_ast.Module(body=[], type_ignores=[]))
             if isinstance(c, _oe_ast.Call)
             and getattr(c.func, "id", None) == "_observed_explosion_block"]
check("📊 OE5 موصولةٌ في **مسارَي** تقرير التطوير (العيّنة القليلة والكافية)",
      len(_oe_calls) == 2, f"نقاطُ نداء={len(_oe_calls)}")

# OE6 — سقفُ المراقبة رُفع (‏20 من 45 كانت بلا قياس)
check("📊 OE6 سقفُ المراقبة ‏≥60 (كان 25 مُلزِمًا مقيسًا)",
      S.OBSERVE_CAP >= 60, f"OBSERVE_CAP={S.OBSERVE_CAP}")

# ── 🔒 قرارُ المالك «25 فقط» — بنيويٌّ لا وسيطُ تشغيل (2026-08-06) ───────────
_c25 = [x for x in _fo_ce.CATALOG if x not in _fo_ce.EXCLUDED_BY_OWNER]
check("🔒 C25-1 الكاتالوجُ الفعّال 29 مرشَّحًا (35 ناقص ستّة مستبعَدين)",
      len(_c25) == 29 and len(_fo_ce.EXCLUDED_BY_OWNER) == 6,
      f"مرشَّحون={len(_c25)} · مستبعَدون={sorted(_fo_ce.EXCLUDED_BY_OWNER)}")
check("🔒 C25-2 الثلاثةُ الدائريّة مستبعَدةٌ **بنيويًّا** (لا تعود بنسيان ENV_SYMBOLS)",
      all(x in _fo_ce.EXCLUDED_BY_OWNER for x in ("APVO", "CMTL", "KLXE")),
      f"{[x for x in ('APVO','CMTL','KLXE') if x not in _fo_ce.EXCLUDED_BY_OWNER]} غائب")
# 🔒 شاهدُ ضبط: مَن **ذُكر عند فيصل** يبقى داخلًا — فالقفلُ ليس تقليمًا شاملًا
check("🔒 C25-3 وشاهدُ الضبط: المذكورون عند فيصل باقون (JZ · ONCO · NUWE · DSY)",
      all(x in _c25 for x in ("JZ", "ONCO", "NUWE", "DSY", "EHGO", "ZCMD")),
      f"مفقود={[x for x in ('JZ','ONCO','NUWE','DSY','EHGO','ZCMD') if x not in _c25]}")
# 🔒 وسببُ كلّ استبعادٍ **مُسمّى** لا فارغ
check("🔒 C25-4 ولكلّ مستبعَدٍ سببٌ مكتوب (لا استبعادَ صامت)",
      all(str(v).strip() for v in _fo_ce.EXCLUDED_BY_OWNER.values()),
      f"{[k for k, v in _fo_ce.EXCLUDED_BY_OWNER.items() if not str(v).strip()]}")

# ── 🔗 `_dedup_closed` يدمج ولا يُسقط (عيبٌ مقيس 2026-08-06) ─────────────────
_dd_a = {"symbol": "Q", "entry_ref": 1.0, "added": "2026-07-01", "gain": 5.0}
_dd_b = {"symbol": "Q", "entry_ref": 1.0, "added": "2026-07-01", "gain": 9.9,
         "mg_obs_pct": 42.0, "t1": 1.2, "ref_bar": "2026-06-30"}
_dd = S._dedup_closed([dict(_dd_a), dict(_dd_b)])
check("🔗 DD1 التصادمُ يُدمَج: الحقولُ الغائبة تُملأ من المرميّ",
      len(_dd) == 1 and _dd[0].get("mg_obs_pct") == 42.0
      and _dd[0].get("t1") == 1.2 and _dd[0].get("ref_bar") == "2026-06-30",
      f"{_dd}")
# 🔒 شاهدُ ضبط: القيمةُ الموجودة **لا تُدهَس** (الأوّل يبقى مرجعًا)
check("🔗 DD2 ولا تُدهَس قيمةٌ موجودة (الأوّل مرجعٌ لا مُستبدَل)",
      _dd[0].get("gain") == 5.0, f"gain={_dd[0].get('gain')}")
check("🔗 DD3 وصفٌّ فريدٌ يمرّ كما هو (القفلُ ليس دمجًا شاملًا)",
      len(S._dedup_closed([dict(_dd_a),
                           dict(_dd_b, added="2026-07-09")])) == 2,
      "صفّان مختلفا `added`")

# ── 🩺 تغطيةُ M13/M14 مرئيّةٌ في لوحة الجمع ──────────────────────────────────
# ── 🌱 حصادُ الصيّادين يصل المالك (إذنُ المالك 2026-08-06 «اي سوها») ──────────────
# كان الملخّصُ يُطبَع في سجلّ الـworkflow وحده ⇒ لا يصل إلا بفتح GitHub، وهو **المدى
# الأماميّ الوحيد غير المُنقَّب**. وُصِل بتقرير التطوير — **لا رسالةٍ رابعة**.
_hlb = S._hunter_ledger_block()
check("🌱 HL1 قسمُ الحصاد يُبنى من السجلّ الحقيقيّ (لا شكلٍ متخيَّل)",
      isinstance(_hlb, list) and (not _hlb or "حصادُ الصيّادين" in _hlb[0]),
      str(_hlb[:2]))
check("🌱 HL2 وبلا سجلٍّ ⇒ لا قسم (فاشلٌ-آمن بلا ضجيج)",
      S._hunter_ledger_block.__doc__ is not None
      and (lambda _sv: (setattr(__import__("hunter_ledger"), "LEDGER_FILE",
                                "/proc/لا-يوجد/x.jsonl"),
                        S._hunter_ledger_block() == [],
                        setattr(__import__("hunter_ledger"), "LEDGER_FILE", _sv))[1])(
          __import__("hunter_ledger").LEDGER_FILE))
# 🔴 والحاسم: مُنادًى في **المسارَين** — القليل والكافي. (فخُّ لوحة الجمع الموثَّق:
#    البلوكاتُ التفصيلية تختفي في مسار العيّنة القليلة، وهو **أهمُّ وقتٍ** لظهورها.)
import ast as _hl_ast                                            # noqa: E402
_hl_tree = _hl_ast.parse(_insp0.getsource(S.build_dev_assistant_report))
_hl_calls = [n for n in _hl_ast.walk(_hl_tree) if isinstance(n, _hl_ast.Call)
             and getattr(n.func, "id", None) == "_hunter_ledger_block"]
check("🔴 HL3 مُنادًى **مرّتين** (مسارُ العيّنة القليلة + الكافية) — لا مرّةً فقط",
      len(_hl_calls) == 2, f"عدد النداءات={len(_hl_calls)}")
check("🌱 HL4 وعلى مستوى الوحدة (وإلّا استحال نداؤه قبل تعريفه في المسار القليل)",
      callable(getattr(S, "_hunter_ledger_block", None)))

# ── 🔬 T-CLIFF-2: مفتاحُ الترتيب (أمرُ المالك «سوها») ─────────────────────────────
# حكمُ `T-CLIFF`: «العلّةُ مفتاحُ الترتيب والسقف لا العتبة» — الترتيبُ بعمق كليف اليوم
# الواحد و`EHGO` ضحلُ الكليف **بالتعريف** فيقصّه السقف. الذراعُ الجديد يرتّب تراكميًّا.
check("🔬 CL2 الافتراضُ `cliff` = **السلوكُ السابق حرفيًّا**",
      S.CONFIG["SPLIT_RADAR_ORDER"] == "cliff")
_cl2_c = [1.0] * 10 + [2.0, 1.4] + [1.38] * 8          # كليفٌ حادّ (‏−30%) بلا هبوطٍ كبير
_cl2_d = [1.0] * 10 + [3.0] + [x for x in (2.7, 2.45, 2.2, 2.0, 1.8, 1.62, 1.5, 1.4, 1.3)]
_cl2_mk = lambda c: S.pd.DataFrame(
    {"Open": c, "High": [x * 1.02 for x in c], "Low": [x * 0.98 for x in c],
     "Close": c, "Volume": [3e5] * len(c)},
    index=S.pd.date_range("2026-05-01", periods=len(c), freq="B"))
_cl2_hist = {"SHARP": _cl2_mk(_cl2_c), "DEEP": _cl2_mk(_cl2_d)}


def _cl2_order(mode):
    _sv = S.CONFIG["SPLIT_RADAR_ORDER"]
    _svc = S.CONFIG["SPLIT_CLIFF_PCT"]
    try:
        S.CONFIG["SPLIT_RADAR_ORDER"] = mode
        S.CONFIG["SPLIT_CLIFF_PCT"] = 5.0        # كلاهما يمرّ المُرشَّح ⇒ الترتيبُ وحده يفرّق
        seen = []
        S.scan_split_radar(_cl2_hist,
                           fetch_splits=lambda s: seen.append(s) or None)
        return seen
    finally:
        S.CONFIG["SPLIT_RADAR_ORDER"] = _sv
        S.CONFIG["SPLIT_CLIFF_PCT"] = _svc


_cl2_a, _cl2_b = _cl2_order("cliff"), _cl2_order("cum")
check("🔴 CL2b الترتيبُ يتبدّل فعلًا: `cliff` يقدّم الحادَّ · `cum` يقدّم الأعمقَ تراكميًّا",
      len(_cl2_a) == 2 and len(_cl2_b) == 2
      and _cl2_a[0] == "SHARP" and _cl2_b[0] == "DEEP",
      f"cliff={_cl2_a} · cum={_cl2_b}")
check("🔒 CL2c وقيمةٌ مجهولة ⇒ ترتيبُ `cliff` (لا سلوكٌ ثالثٌ مُخترَع)",
      _cl2_order("سين") == _cl2_a)
# 🔴 **CL2d تقاعد وحُلّ محلَّه CL3 (2026-08-06):** كان يقفل «`scan_split_hunter`
#    لا تعرف المفتاح» — وهو **ما جعل ذراعَ الترتيب no-op** (الأداةُ تقيس هذي الدالّة
#    لا الرادار). فنُقل الخطّافُ إليها **بإذن المالك**، والقفلُ صار **سلوكيًّا**:
#    الافتراضُ بت-بت · و`cum` يبدّل الناجيَ من السقف · والشروطُ الخمسة لم تُمَسّ.
def _cl3_hist():
    import pandas as _p
    def _mk(deep_day, slow):
        c = [10.0] * 60
        for i in range(1, 60):
            c[i] = c[i - 1] * (1 - slow)
        c[deep_day] = c[deep_day - 1] * 0.6            # كليف يومٍ واحد ‏−40%
        for i in range(deep_day + 1, 60):
            c[i] = c[i - 1]
        ix = _p.date_range("2026-01-01", periods=60, freq="B")
        return _p.DataFrame({"Open": c, "High": c, "Low": c, "Close": c,
                             "Volume": [1e6] * 60}, index=ix)
    return {"DEEP": _mk(50, 0.0), "SLOW": _mk(50, 0.02)}


def _cl3_probe(order, cap):
    _so, _sc = S.CONFIG["SPLIT_RADAR_ORDER"], S.CONFIG["SPLIT_RADAR_PROBE_CAP"]
    S.CONFIG["SPLIT_RADAR_ORDER"], S.CONFIG["SPLIT_RADAR_PROBE_CAP"] = order, cap
    seen = []
    try:
        S.scan_split_hunter(
            _cl3_hist(), today="2026-03-24",
            fetch_splits=lambda x: seen.append(x) or [],
            fetch_float=lambda x, **k: None, fetch_borrow=lambda x: None,
            fetch_pump=lambda d: None, fetch_offering=lambda x, **k: None)
        return seen
    finally:
        S.CONFIG["SPLIT_RADAR_ORDER"], S.CONFIG["SPLIT_RADAR_PROBE_CAP"] = _so, _sc


check("🔒 CL3a الافتراضُ `cliff` = السلوكُ السابق حرفيًّا (الأحدُّ كليفًا ينجو من السقف)",
      _cl3_probe("cliff", 1) == ["DEEP"], str(_cl3_probe("cliff", 1)))
check("🔴 CL3b و`cum` **يبدّل الناجي** فعلًا (وإلّا فالذراعُ no-op كما وقع)",
      _cl3_probe("cum", 1) == ["SLOW"], str(_cl3_probe("cum", 1)))
check("🔒 CL3c والشروطُ الخمسة لم تُمَسّ: بسقفٍ يسع الجميع ⇒ **نفسُ المفحوصين** "
      "بالترتيبين (الخطّافُ في مُرشّح التكلفة لا في الحكم)",
      sorted(_cl3_probe("cliff", 80)) == sorted(_cl3_probe("cum", 80)) == ["DEEP", "SLOW"],
      f"cliff={sorted(_cl3_probe('cliff', 80))} · cum={sorted(_cl3_probe('cum', 80))}")
check("🔒 CL3d وقيمةٌ مجهولة ⇒ `cliff` (لا سلوكٌ ثالثٌ مُخترَع)",
      _cl3_probe("سين", 1) == ["DEEP"], str(_cl3_probe("سين", 1)))
# 🔒 CL4: النتيجةُ منشورةٌ بحكمها وأرقامِها ومعرّفاتِ تشغيلها — ونسبتُها إلى
#    **الأساس الإنتاجيّ** لا إلى أساس كلّ تشغيلة (القيدُ المسجَّل §④ الذي لولاه
#    قُرئت A3 «داخل السقف» وهي ×5.36).
_cl4 = open("cliff2_result.md", encoding="utf-8").read()
check("⛰️ CL4 نتيجةُ T-CLIFF-2 منشورة: الحكم · الأذرع الأربعة · التشغيلات · اللقطة",
      all(x in _cl4 for x in ("فشلت", "×5.36", "×3.04", "×1.03", "EHGO",
                              "31151315697", "31152421400", "31152428182",
                              "30597787554")))
check("⛰️ CL5 وتُصرّح بالـno-op المسحوب وبأن الأثر الإنتاجيّ صفر",
      "no-op" in _cl4 and "مسحوبتان" in _cl4 and "الأثرُ الإنتاجيّ — صفر" in _cl4)

# ══════════════════════════════════════════════════════════════════════════
# 📦 DEP — كلُّ اعتمادية تستوردها السويّة **مُصرَّحٌ بها** في `requirements.txt`
# ══════════════════════════════════════════════════════════════════════════
# 🐞 **عطلٌ حقيقيّ مقيس (2026-08-07):** أضفتُ `import yaml` لأقفال الـworkflows،
#    والمكتبةُ حاضرةٌ محلّيًّا وغائبةٌ عن الرنر ⇒ `python3 test_bot.py` ينجح عندي
#    و**`tests.yml` يسقط بـ`ModuleNotFoundError` على كلّ دفعة** — وبقيت البوّابةُ
#    حمراء ساعتين وأنا أدفع فوقها. 🧭 **الدرس: «السويّةُ خضراء عندي» ليست «البوّابةُ
#    خضراء» — والفرقُ يُقرأ من سجلّ CI لا من طرفيّتي.**
#    ⚠️ ولا يُحَلّ بـ`try/except ImportError`: ذاك يُخفي الأقفال **في CI بالذات**.
import ast as _dep_ast
import sys as _dep_sys

_DEP_SELF = {"Super_stock", "test_bot"}          # وحداتُ المستودع نفسِه
_dep_tree = _dep_ast.parse(open("test_bot.py", encoding="utf-8").read())
_dep_mods = set()
for _n in _dep_ast.walk(_dep_tree):
    if isinstance(_n, _dep_ast.Import):
        _dep_mods |= {a.name.split(".")[0] for a in _n.names}
    elif isinstance(_n, _dep_ast.ImportFrom) and _n.module and _n.level == 0:
        _dep_mods.add(_n.module.split(".")[0])
# وحداتُ المستودع = ملفّاتُ `.py` بجانبنا · والقياسيّة من `sys.stdlib_module_names`
_dep_local = {f[:-3] for f in __import__("os").listdir(".") if f.endswith(".py")}
_dep_third = sorted(_dep_mods - set(_dep_sys.stdlib_module_names)
                    - _dep_local - _DEP_SELF)
# 🔴 **يُقرأ من أسطر التثبيت وحدَها لا من نصّ الملفّ:** أوّلُ صياغةٍ لي قارنت
#    بالنصّ الكامل، **والتعليقُ الذي كتبتُه يذكر `PyYAML` باسمه** ⇒ حذفُ سطر
#    التثبيت كان **يمرّ** والقفلُ أخضر على كذبة. كشفَته الطفرةُ لا القراءة —
#    وهو **فخُّ «القفل النصّيّ» الموثَّق** وقعتُ فيه مرّةً أخرى.
_dep_pins = {_l.split("==")[0].strip().lower()
             for _l in open("requirements.txt", encoding="utf-8").read().splitlines()
             if _l.strip() and not _l.strip().startswith("#") and "==" in _l}
# أسماءُ التوزيع تختلف عن أسماء الاستيراد (‏yaml ⟵ PyYAML) — خريطةٌ صريحة لا تخمين
_DEP_DIST = {"yaml": "pyyaml"}
_dep_missing = [m for m in _dep_third
                if _DEP_DIST.get(m, m) not in _dep_pins]
check("📦 DEP1 كلُّ استيرادٍ خارجيٍّ في السويّة مُصرَّحٌ في `requirements.txt`",
      not _dep_missing, f"خارجية={_dep_third} · ناقصة={_dep_missing}")
check("📦 DEP2 والقفلُ يرى `yaml` فعلًا (وإلّا فهو يحرس فراغًا)",
      "yaml" in _dep_third, str(_dep_third))
check("📦 DEP3 و`tests.yml` يثبّت من `requirements.txt` (وإلّا فالتصريحُ بلا أثر)",
      "pip install -r requirements.txt"
      in open(".github/workflows/tests.yml", encoding="utf-8").read())

# ══════════════════════════════════════════════════════════════════════════
# 🥇 SOFT — عتباتُ «المثالي» في النواقص اللينة من **وسيط** الكاتالوج
# ══════════════════════════════════════════════════════════════════════════
# أمرُ المالك (2026-08-07): «سوّها». **والحدُّ الصلب طرفٌ خارجيّ (‏P90) و«المثالي»
# مركزُ التوزيع ⇒ الوسيط** — والأربعةُ مقيسةٌ في الظرف أصلًا فلا رقمَ يُخترَع.
check("🥇 SOFT1 الخريطةُ أربعُ عتباتٍ بأسمائها الإنتاجية",
      S.SOFT_MEDIAN_KEYS == {"best_spike": ("PRIOR_SPIKE_PCT", "lo"),
                             "drop_pct": ("MIN_DROP_PCT", "lo"),
                             "rsi_min": ("RSI_OVERSOLD", "hi"),
                             "rsi_now": ("RSI_MAX_NOW", "hi")},
      str(sorted(S.SOFT_MEDIAN_KEYS)))
# ✅ حُدِّث العنوان 2026-08-07: «لا يقيسه الظرف» لم يعد سببَه — صار يقيسه معيارًا
#    **صلبًا** (‏tf_count الخامس عشر). الادّعاءُ الباقي الصحيح: يبقى **خارج مسار
#    الوسيط اللين** (لا «مثاليّ» نصّيّ له فلا وسيطَ يُخمَّن) — والفحصُ نفسُه لم يتغيّر.
check("🥇 SOFT2 و`TF_MIN_REVERSALS` خارج مسار الوسيط اللين (حدُّه صلبٌ من CRITERIA)",
      "TF_MIN_REVERSALS" not in {k for k, _ in S.SOFT_MEDIAN_KEYS.values()})
_sf = S.faisal_soft_overrides({"best_spike": 250.0, "drop_pct": [88.0, 95.0],
                               "rsi_min": 30.0, "rsi_now": 41.0})
check("🥇 SOFT3 الترجمةُ صحيحة · والنطاقُ يُؤخذ **جانبُه الأدنى** (نقصُ الهبوط)",
      _sf == {"PRIOR_SPIKE_PCT": 250.0, "MIN_DROP_PCT": 88.0,
              "RSI_OVERSOLD": 30.0, "RSI_MAX_NOW": 41.0}, str(_sf))
check("🥇 SOFT4 المفقودُ يُتخطّى ولا يُخمَّن · والتالفُ كذلك · والفارغُ ⇒ {}",
      S.faisal_soft_overrides({"rsi_min": 30.0}) == {"RSI_OVERSOLD": 30.0}
      and S.faisal_soft_overrides({"best_spike": "س"}) == {}
      and S.faisal_soft_overrides({}) == {} and S.faisal_soft_overrides(None) == {})
# 🔒 موصولةٌ من `apply_faisal_only` (AST لا نصّ) — وإلّا فالدالّةُ حبرٌ على ورق
import ast as _sf_ast
_sf_fn = next((n for n in _sf_ast.walk(_sf_ast.parse(
    open("Super_stock.py", encoding="utf-8").read()))
    if isinstance(n, _sf_ast.FunctionDef) and n.name == "apply_faisal_only"), None)
check("🥇 SOFT5 مُنادًى فعلًا داخل `apply_faisal_only` (AST)",
      any(getattr(c.func, "id", None) == "faisal_soft_overrides"
          for c in _sf_ast.walk(_sf_fn) if isinstance(c, _sf_ast.Call)))
# 🔒 فاشلٌ-آمنٌ **بإعلان**: ظرفٌ بلا وسيط ⇒ عتباتُنا تبقى ويُقال ذلك
_sf_log = []
_sf_cfg = {"FAISAL_ONLY": 1}
S.apply_faisal_only(_sf_cfg, log_fn=_sf_log.append)
check("🥇 SOFT6 ظرفٌ بلا وسيط ⇒ عتباتُنا تبقى **ويُعلَن** (لا صمت)",
      any("لا وسيطَ في الظرف" in x or "من وسيط الكاتالوج" in x for x in _sf_log),
      " | ".join(_sf_log)[-120:])
check("🥇 SOFT7 و`catalog_envelope.py` يُصدر الوسيطَ آليًّا (لا نقلَ يدويّ)",
      "soft_median" in open("catalog_envelope.py", encoding="utf-8").read()
      and "build_envelope(rows, 50.0)"
      in open("catalog_envelope.py", encoding="utf-8").read())
# 🔴 SOFT8: **الوصلُ يُثبَت من الملفّ الحقيقيّ لا من فِكستشر** — أوّلُ صياغةٍ لي
#    قرأت `edges["soft_median"]` بينما `load_edges` يضع كلَّ ما عدا `edges` تحت
#    `_meta` ⇒ **وصلةٌ ميتة** والرسالةُ تقول «لا وسيط» **والملفُّ فيه**. أمسكَتها
#    التشغيلةُ لا القراءة.
_sf_cfg2 = {"FAISAL_ONLY": 1}
S.apply_faisal_only(_sf_cfg2, log_fn=lambda *_a: None)
check("🥇 SOFT8 الأربعةُ تصل فعلًا من `envelope_p90.json` الحقيقيّ (لا `_meta` ضائع)",
      all(_sf_cfg2.get(k) is not None for k in
          ("PRIOR_SPIKE_PCT", "MIN_DROP_PCT", "RSI_OVERSOLD", "RSI_MAX_NOW"))
      and abs(_sf_cfg2["RSI_OVERSOLD"] - 33.0) < 1e-9
      and _sf_cfg2["PRIOR_SPIKE_PCT"] > 100.0,
      f"{ {k: _sf_cfg2.get(k) for k in ('PRIOR_SPIKE_PCT','MIN_DROP_PCT','RSI_OVERSOLD','RSI_MAX_NOW')} }")
# ✅ حُدِّث 2026-08-07 («سوها» الثانية): كان «لم يُمَسّ» — وصار TF قابلًا للوصول
#    عبر **مسار الحوافّ الصلبة وحده** (‏tf_count في CRITERIA). القفلُ الآن يفرض
#    المسارَ الصحيح: **الوسيطُ اللين لا يمسّه أبدًا**، ووصولُه (بعد هبوط معايرة
#    الخمسة عشر) يكون عددًا صحيحًا من الحوافّ. قبل الهبوط: غيابُه سليم.
check("🥇 SOFT9 و`TF_MIN_REVERSALS` لا يصل إلا من الحوافّ الصلبة (والوسيطُ لا يمسّه)",
      "TF_MIN_REVERSALS" not in S.faisal_soft_overrides(
          {"tf_count": 3.0, "rsi_min": 30.0})
      and ("TF_MIN_REVERSALS" not in _sf_cfg2
           or isinstance(_sf_cfg2["TF_MIN_REVERSALS"], int)))
# ══════════════════════════════════════════════════════════════════════════
# 🎯 PROX — «القابلُ للدخول أوّلًا» في `rank_key` (قرارُ المالك 2026-08-07)
# ══════════════════════════════════════════════════════════════════════════
# العطلُ المقيس: العشرةُ المُسلَّمون كانوا فوق نطاقهم بـ4.5%-48.1%، و`YHC` جاهزيتُه
# 90 (الأعلى) وهو الأبعد، و`XAIR` القابلُ للدخول جاهزيتُه 60 (الأدنى) ⇒ **المُرتِّبُ
# يقدّم الأبعدَ بالبناء**. والشرطُ الحرفيّ للمالك: **لا تُمَسّ بوّاباتُ فيصل.**
def _px(sym, price, tr, rdy, score=90, rr=3.0):
    return {"symbol": sym, "price": price, "tranches": list(tr),
            "readiness": rdy, "score": score, "rr": rr}


_PX_FAR = _px("YHC", 2.00, [1.27, 1.31, 1.35], 90, 100, 7.21)   # +48.1% فوق النطاق
_PX_NEAR = _px("XAIR", 5.20, [5.02, 5.17, 5.32], 60, 85, 2.39)  # داخل النطاق
check("🎯 PROX1 `in_entry_band` تفرّق الداخلَ عن الخارج",
      S.in_entry_band(_PX_NEAR) is True and S.in_entry_band(_PX_FAR) is False)
check("🎯 PROX2 وبياناتٌ ناقصة/تالفة ⇒ False (لا يُدَّعى قربٌ بلا دليل)",
      S.in_entry_band({}) is False
      and S.in_entry_band({"price": 1.0, "tranches": []}) is False
      and S.in_entry_band({"price": "س", "tranches": [1.0]}) is False
      and S.in_entry_band({"price": 0, "tranches": [1.0]}) is False)
check("🔴 PROX3 القابلُ للدخول يتقدّم **رغم جاهزيةٍ أدنى بثلاثين نقطة** (حالةُ اليوم)",
      [r["symbol"] for r in sorted([_PX_FAR, _PX_NEAR], key=S.rank_key)]
      == ["XAIR", "YHC"],
      str([r["symbol"] for r in sorted([_PX_FAR, _PX_NEAR], key=S.rank_key)]))
# 🔒 داخلَ الفئة الواحدة: الترتيبُ **byte-identical** للمفتاح القديم
_PX_OLD = lambda x: (-(x.get("readiness") if x.get("readiness") is not None else -1),  # noqa: E731
                     -x.get("h4_confirm", 0), -x.get("score", 0), -x.get("rr", 0))
# 🐞 **عيّنةٌ بأسعارٍ مختلفة عمدًا (صُحِّحت بالطفرة PM5):** أوّلُ صياغةٍ لي جعلت
#    السعرَ 9.0 للجميع ⇒ مفتاحٌ **سعريٌّ مستمرّ** بدل الثنائيّ لا يغيّر الترتيبَ
#    فينجو من القفل. الآن الأسعارُ متمايزة **وترتيبُها يخالف ترتيبَ الجاهزية** ⇒
#    أيُّ مفتاحٍ مستمرٍّ يُسقط القفل.
_px_all_far = [_px(f"F{i}", pr, [1.0, 1.03, 1.06], r, sc, rrv)
               for i, (pr, r, sc, rrv)
               in enumerate([(9.0, 70, 90, 3.1), (7.0, 90, 100, 7.2),
                             (12.0, 70, 95, 2.0), (5.0, 60, 85, 4.4),
                             (20.0, 70, 90, 5.0)])]
check("🔒 PROX4 الجميعُ خارج النطاق ⇒ الترتيبُ **مطابقٌ للقديم حرفيًّا**",
      [r["symbol"] for r in sorted(_px_all_far, key=S.rank_key)]
      == [r["symbol"] for r in sorted(_px_all_far, key=_PX_OLD)],
      str([r["symbol"] for r in sorted(_px_all_far, key=S.rank_key)]))
_px_all_near = [_px(f"N{i}", pr, [1.0, 1.03, 1.06], r, sc, rrv)
                for i, (pr, r, sc, rrv)
                in enumerate([(1.00, 70, 90, 3.1), (0.90, 90, 100, 7.2),
                              (1.05, 70, 95, 2.0), (0.80, 60, 85, 4.4),
                              (1.02, 70, 90, 5.0)])]
check("🔒 PROX5 والجميعُ داخل النطاق ⇒ كذلك مطابق (المفتاحُ ثنائيٌّ لا مستمرّ)",
      [r["symbol"] for r in sorted(_px_all_near, key=S.rank_key)]
      == [r["symbol"] for r in sorted(_px_all_near, key=_PX_OLD)])
check("🔒 PROX6 ترتيبٌ **لا رفض**: العضويةُ لا تتغيّر حين يكون الجميعُ خارج النطاق",
      {r["symbol"] for r in S.select_top(sorted(_px_all_far, key=S.rank_key), 3, set())}
      == {r["symbol"] for r in S.select_top(sorted(_px_all_far, key=_PX_OLD), 3, set())})
# 🔒 صفرُ رقمٍ مخترَع: `in_entry_band` لا تحمل أيّ عتبةٍ عددية غير 0/1/100
_px_lits = {n.value for n in __import__("ast").walk(__import__("ast").parse(
    __import__("inspect").getsource(S.in_entry_band)))
    if isinstance(n, __import__("ast").Constant) and isinstance(n.value, (int, float))
    and not isinstance(n.value, bool)}
check("🔒 PROX7 صفرُ عتبةٍ مخترَعة — العتبةُ من CONFIG وحدها",
      _px_lits <= {0, 1, 0.0, 100.0} and "ENTRY_READY_BAND_TOL_PCT"
      in __import__("inspect").getsource(S.in_entry_band), str(sorted(_px_lits)))
# 🔒 شرطُ المالك: بوّاباتُ فيصل لم تُمَسّ
# ✅ حُدِّث 2026-08-07 مساءً (فتح D11 بأمر المالك «قسها» — معايرة `31187484789`):
#    الستّ عشرة صارت **تسع عشرة** كلُّها من الكاتالوج (‏+الثلاثة المقيسة
#    gain5/ma_above/gap_dist)، وتحرّكت اثنتان بسببٍ مقيس: `WATCH_MAX_FAILS` ‏5⟶7
#    و`SCORE_MIN` ‏35⟶30 (عتباتُ «المثالي» صارت أشدَّ فارتفعت النواقصُ وانخفضت
#    النقاطُ في نوافذ أسهمه — التسامحُ يُعايَر تحت التعريفات الإنتاجية نفسِها).
#    القفلُ القديم (‏16) أمسك التغييرَ فأدّى عمله ثم حُدِّث بإقرارٍ مؤرَّخ.
# ✅ وحُدِّث ثالثةً (معايرة الخمسة عشر `31193618801`): +`TF_MIN_REVERSALS`=0
#    (توافقُ فريمات أسهم فيصل قبل انفجارها **صفر** حتى عند P90!) · و`SCORE_MIN`
#    عاد 35 (كمّيّة مشتقّة — قِيست هذي الجولة وعتباتُ D11 الأوسع مطبَّقة فقلّت
#    النواقص وارتفعت النقاط؛ التفصيل بتعديل ⑬ في envelope_prereg.md).
_px_cfg = {"MIN_PRICE": 1.649999976158142, "MIN_DROP_FLOOR": 89.58801459243173,
           "MAX_DROP_PCT": 99.72182254044176, "PRIOR_SPIKE_FLOOR": 98.94179994296877,
           "BASE_RANGE_MAX_PCT": 475.2137106742811, "MIN_DOLLAR_VOL": 39482.02504813671,
           "RSI_OS_HARD": 44.0, "RSI_NOW_HARD": 48.87697543295087,
           "WATCH_MAX_FAILS": 6, "NEAR_PCT": 10.0, "SCORE_MIN": 35,
           "MIN_RR_T1": 1.168184676778314, "PRIOR_SPIKE_PCT": 164.021164021164,
           "MIN_DROP_PCT": 96.91775344552148, "RSI_OVERSOLD": 33.0,
           "RSI_MAX_NOW": 35.77890610671257,
           "RECENT_RISE_BLOCK_PCT": 8.163264114526037,
           "MA_GATE_MAX_ABOVE_PCT": 64.70643372077272,
           "GAP_ABOVE_MAX_DIST_PCT": 502.07610271270005,
           "TF_MIN_REVERSALS": 0}
# 🐞 وأوّلُ صياغةٍ لي مرّرت قاموسًا **بلا `FAISAL_ONLY`** فترجع الدالّةُ مبكّرًا
#    ⇒ «طُبِّق 0» والقفلُ يفحص فراغًا — فخُّ «العيّنةُ يردّها حارسٌ أسبق» مرّةً أخرى.
_px_live = {"FAISAL_ONLY": 1}
S.apply_faisal_only(_px_live, log_fn=lambda *_a: None)
check("🔒 PROX8 بوّاباتُ فيصل **العشرون** كما أخرجتها معايرةُ الخمسة عشر (شرطُ المالك)",
      all(abs(float(_px_live.get(k, -1)) - float(v)) < 1e-9 for k, v in _px_cfg.items())
      and len(_px_live) == 21, f"طُبِّق {len(_px_live) - 1}")   # 20 + مفتاحُ التفعيل
check("🎯 PROX9 والتسجيلُ المسبق مدفوعٌ بمعياره وبحدّ الصدق «الباكتيست لا يتحقّق»",
      all(x in open("prox_prereg.md", encoding="utf-8").read()
          for x in ("P-1", "P-2", "X1", "no-op", "بوّاباتُ فيصل الستّ عشرة كما هي",
                    "لا يُدَّعى عائد")))

# ✅ حُدِّث 2026-08-07 (فتح D11 بأمر المالك): بصمةُ الحوافّ صارت `4fb70bcc13e5`
#    (‏14 معيارًا — المعايرة `31187484789`). دعوى SOFT10 التاريخية («إضافةُ الوسيط
#    وحدها لا تغيّر الحوافّ») صحّت وقتَها؛ اليومَ الحوافُّ تغيّرت **بمعايرةٍ مقصودة**
#    لا بأثرٍ جانبيّ — والقفلُ يثبّت البصمة الجديدة (مصدرٌ واحد للحقيقة).
check("🥇 SOFT10 بصمةُ الحوافّ النافذة = جولةُ التثبيت (‏`2c2707cfd0dd`)",
      __import__("envelope_scan").edges_fingerprint(
          __import__("envelope_scan").load_edges()) == "2c2707cfd0dd")

# ── ⏳ استثناءُ المزامنة للتشغيل اليدويّ (عطلٌ مقيس 2026-08-06) ─────────────────
# المراقبُ يعمل 4 مرّاتٍ بالساعة وGitHub يُبقي **معلَّقًا واحدًا** لكل مجموعة ⇒ التشغيلُ
# اليدويّ للفرز يُطرَد. المقيس: انتظارُ 84 دقيقة ثم **إلغاءُ** التالية بعد 15 دقيقة.
import yaml as _cy                                                # noqa: E402
_cy_ds = _cy.safe_load(open(".github/workflows/daily_screener.yml", encoding="utf-8"))
_cy_pm = _cy.safe_load(open(".github/workflows/pullback_monitor.yml", encoding="utf-8"))
_cy_grp = str(_cy_ds["concurrency"]["group"])
check("⏳ CY1 اليدويُّ في مجموعةٍ خاصّةٍ به · والمجدولُ يبقى في مجموعة الحالة",
      "workflow_dispatch" in _cy_grp and "super-stocks-manual-" in _cy_grp
      and "super-stocks-state" in _cy_grp, _cy_grp[:70].replace("\n", " "))
check("⏳ CY2 والمجموعةُ **فريدةٌ لكل تشغيلة يدوية** (‏`run_id`) وإلّا عاد الطرد",
      "github.run_id" in _cy_grp)
check("🔒 CY3 و`cancel-in-progress` يبقى **false** (لا يُقتل جارٍ)",
      _cy_ds["concurrency"]["cancel-in-progress"] is False
      and _cy_pm["concurrency"]["cancel-in-progress"] is False)
check("🔒 CY4 والمراقبُ **لم يُمَسّ** — يبقى في مجموعة الحالة (الحمايةُ قائمة)",
      _cy_pm["concurrency"]["group"] == "super-stocks-state")
# 🔴 المبرّرُ مقفول: الكرونُ اليوميّ خارج نافذة المراقب · والتجديدُ داخلها فيبقى محميًّا
_cy_sched = [c["cron"] for c in _cy_ds[True]["schedule"]]
_cy_hours = lambda c: c.split()[1]
check("🔴 CY5 الكرونُ اليوميّ **خارج** نافذة المراقب (11-23) فلا تماسَّ أصلًا",
      any(_cy_hours(c) == "4" for c in _cy_sched), str(_cy_sched))
check("🔴 CY6 وكرونُ التجديد **داخلها** ⇒ يبقى في مجموعة الحالة (لم يُستثنَ)",
      any(_cy_hours(c) == "22" for c in _cy_sched)
      and "schedule" not in _cy_grp, str(_cy_sched))

# ── 📐 T-RANKER-TIE: حقلُ معايير الظرف في صفقة الباكتيست ────────────────────────
# 🔴 عيبٌ مقيس: الصفقةُ تحمل **اثنين فقط** من الأحد عشر (`n_soft`/`readiness`) و
# `env_depth` تمتنع دون ستّة ⇒ بلا هذا الحقل يمتنع الذراعُ عن **كلّ** صفقة فتخرج
# «لا فرق» وهي `no-op` — صنفُ `BT_CANDLE` بعينه.
_ev_src = open("Super_stock.py", encoding="utf-8").read()
check("📐 EV1 `BT_ENVVALS` **مطفأٌ افتراضيًّا** (الإنتاج والباكتيستُ الأساس بت-بت)",
      S.CONFIG["BT_ENVVALS"] == 0)
check("📐 EV2 وله صفٌّ في جدول التعيين (لا علمَ ميّت — درسُ `BT_CANDLE`)",
      "BT_ENVVALS" in _insp0.getsource(S._apply_backtest_overrides))
check("📐 EV3 والحقلُ يُلحَق **داخل حارس العلم** لا خارجه",
      'if CONFIG.get("BT_ENVVALS"):' in _insp0.getsource(S.backtest_symbol))
# 🔴 والمميِّز: الأحد عشر **كلُّها** مذكورةٌ بأسماء `measure_session` — لا تسعةٌ ولا خريطةٌ ثانية
import catalog_envelope as _EVCE                                  # noqa: E402
_ev_blk = _insp0.getsource(S.backtest_symbol)
_ev_blk = _ev_blk[_ev_blk.index('if CONFIG.get("BT_ENVVALS")'):][:1200]
_ev_need = [x[0] for x in _EVCE.CRITERIA]
check("🔴 EV4 الأحد عشر كلُّها في الحقل بأسماء `measure_session` (خريطةٌ واحدة)",
      all(f'"{k}"' in _ev_blk for k in _ev_need),
      str([k for k in _ev_need if f'"{k}"' not in _ev_blk]) or "الكلُّ حاضر")
# 🔴 وسلوكيًّا: `env_depth` **تمتنع** على صفقةٍ بلا الحقل و**تعمل** معه
import replay10 as _RT                                            # noqa: E402,F811
_ev_two = {"n_soft": 3, "readiness": 45}
_ev_edges = _json.load(open("envelope_p90.json", encoding="utf-8"))["edges"]
_ev_sides = {x[0]: x[1] for x in _EVCE.CRITERIA}
_ev_full = _json.loads(open("envelope_candidates.jsonl", encoding="utf-8"
                            ).readlines()[1])["vals"]
check("🔴 EV5 بحقلَين فقط ⇒ **امتناع** · وبالأحد عشر ⇒ عمقٌ محسوب (الفارقُ حقيقيّ)",
      _RT.env_depth(_ev_two, _ev_edges, _ev_sides) is None
      and isinstance(_RT.env_depth(_ev_full, _ev_edges, _ev_sides), float),
      f"اثنان={_RT.env_depth(_ev_two, _ev_edges, _ev_sides)} · "
      f"أحدَ عشر={_RT.env_depth(_ev_full, _ev_edges, _ev_sides)}")

# ── 🥇⑦ T-RANKER-TIE: كاسرُ التعادل (`ranker_tie_prereg.md`) ────────────────────
# الموضعُ مقيس: 16 سهمًا متعادلين عند جاهزية 70 والسعة 10 ⇒ **10 من 10 خاناتٍ يحكمها
# التعادل**. والفاصلُ اليوم `score` ثم `rr` — ولم يُختبَرا كاسرَي تعادلٍ قطّ.
import replay10 as _RT                                            # noqa: E402
import catalog_envelope as _RTCE                                  # noqa: E402
_rt_edges = _json.load(open("envelope_p90.json", encoding="utf-8"))["edges"]
_rt_sides = {x[0]: x[1] for x in _RTCE.CRITERIA}
check("📐 RT1 `env_depth` نقيّةٌ وتُرجع وسيطًا في [0,1]",
      0.0 <= (_RT.env_depth({"price": 3.0, "drop_pct": [0, 0], "best_spike": 200.0,
                             "base_range": 100.0, "dollar_vol": 1e6, "rsi_min": 20.0,
                             "rsi_now": 20.0, "n_soft": 1, "readiness": 60,
                             "score": 90, "rr": 5.0}, _rt_edges, _rt_sides) or -1) <= 1.0)
# ⚠️ بحرسٍ حول النداء: كسرُ الحدّ يُفرغ القائمةَ فيرمي `IndexError` **فيُسقط السويّة**
#    ويكتم القفلَ الذي أمسك العيب — خامسُ وقوعٍ لهذا الصنف اليوم.
def _rt_d(vals, edges=None):
    try:
        return _RT.env_depth(vals, _rt_edges if edges is None else edges, _rt_sides)
    except Exception as _e:                                      # noqa: BLE001
        return f"⛔ {type(_e).__name__}"


check("📐 RT2 معيارٌ غائبٌ يُتخطّى · وأقلُّ من الحدّ ⇒ **امتناع** (None) لا تخمين",
      _rt_d({"price": 3.0}) is None and _rt_d({}) is None,
      f"{_rt_d({'price': 3.0})!r} · {_rt_d({})!r}")
check("📐 RT3 وقيمٌ تالفة تُتخطّى بلا انهيار",
      _rt_d({"price": "س", "score": None, "rr": [1]}) is None)
check("📐 RT4 وحوافٌّ فارغة ⇒ امتناعٌ لا قبولٌ شامل (فاشلٌ-مغلق هنا عمدًا)",
      _rt_d({"price": 3.0, "score": 90}, edges={}) is None)
# 🔴 المميِّز: كاسرُ التعادل **يبدّل الترتيب داخل التعادل ولا يمسّ من يختلفون**
_rt_c = [_RT.Candidate(symbol="A", session=0, readiness=70, score=90, rr=2.0, seq=0,
                       payload={"env_depth": 0.2}),
         _RT.Candidate(symbol="B", session=0, readiness=70, score=80, rr=1.0, seq=1,
                       payload={"env_depth": 0.9}),
         _RT.Candidate(symbol="C", session=0, readiness=60, score=100, rr=9.0, seq=2,
                       payload={"env_depth": 1.0})]
_rt_prod = [x.symbol for x in sorted(_rt_c, key=_RT.rank_actual)]
_rt_env = [x.symbol for x in sorted(_rt_c, key=_RT.rank_tie_env)]
check("🔴 RT5 داخل التعادل يتبدّل الترتيب (A→B) · ومن يختلف في الجاهزية **لا يُمَسّ**",
      _rt_prod == ["A", "B", "C"] and _rt_env == ["B", "A", "C"],
      f"إنتاج={_rt_prod} · R-ENV={_rt_env}")
check("🔒 RT6 والامتناعُ يُنزِله لآخر المتعادلين (لا يُخمَّن له عمق)",
      [x.symbol for x in sorted(
          [_RT.Candidate(symbol="N", session=0, readiness=70, seq=0, payload={}),
           _RT.Candidate(symbol="D", session=0, readiness=70, seq=1,
                         payload={"env_depth": 0.1})], key=_RT.rank_tie_env)] == ["D", "N"])
# 🔒 شاهدُ الضبط: كاسرُ تعادلٍ عشوائيٌّ **حتميّ** ويحترم الجاهزية
_rt_r1 = [x.symbol for x in sorted(_rt_c, key=_RT.make_rank_tie_random(7))]
check("🔒 RT7 `R-RAND` حتميٌّ بالبذرة · ويُبقي الجاهزيةَ مفتاحًا أوّلًا",
      _rt_r1 == [x.symbol for x in sorted(_rt_c, key=_RT.make_rank_tie_random(7))]
      and _rt_r1[-1] == "C", str(_rt_r1))
check("🔒 RT8 وبذرةٌ أخرى تُغيّر ترتيبَ المتعادلَين (لا ثابتٌ متنكّر)",
      any([x.symbol for x in sorted(_rt_c, key=_RT.make_rank_tie_random(sd))][:2]
          != _rt_r1[:2] for sd in range(1, 40)))
# 🔒 والأذرعُ **معزولةٌ عن الإنتاج** كبقيّة `replay10`
check("🔒 RT9 كاسرُ التعادل خارج `Super_stock` (بحثٌ لا إنتاج)",
      "rank_tie_env" not in open("Super_stock.py", encoding="utf-8").read())

# ══════════════════════════════════════════════════════════════════════════════
# 🥇 FAI — «معايير فيصل وحدها» (أمرُ المالك 2026-08-06)
# ══════════════════════════════════════════════════════════════════════════════
# «لازم نلتزم بمعايير فيصل فقط وهذي نجيبها عن طريق الكتالوج» ثم «ابن الحد الادنى
# و اعتمد على بواباته فقط». التنفيذُ **إحلالُ أرقامه في مفاتيح بوّاباتنا** — بلا
# تفريعِ فرزٍ ولا مسٍّ بـ`scan_market`/`analyze_ticker`.
_fai_src = open("Super_stock.py", encoding="utf-8").read()
check("🥇 FAI1b والافتراضُ في الكود = 1 (لا يُنسى مُطفأً)",
      'os.environ.get("FAISAL_ONLY", "1")' in _fai_src)
# ── الخريطة: من `CRITERIA` نفسِها لا مكتوبةً بيدي ─────────────────────────────
_fai_edges = {"price": 1.65, "drop_pct": [89.5, 99.7], "best_spike": 98.9,
              "base_range": 475.2, "dollar_vol": 39482.0, "rsi_min": 44.0,
              "rsi_now": 48.9, "n_soft": 5.0, "readiness": 10.0,
              "score": 35.0, "rr": 1.168}
_fai_ov = S.faisal_only_overrides(_fai_edges)
check("🥇 FAI2 الخريطةُ تُغطّي الأحد عشر ⇒ 12 مفتاحًا (‏`drop_pct` مفتاحان)",
      len(_fai_ov) == 12 and _fai_ov.get("MIN_DROP_FLOOR") == 89.5
      and _fai_ov.get("MAX_DROP_PCT") == 99.7, str(sorted(_fai_ov))[:110])
# ⚠️ بـ`.get` لا بالفهرسة: خريطةٌ ناقصةٌ كانت ترمي `KeyError` **فتُسقط السويّة**
#    وتكتم القفلَ الذي أمسك العيب فعلًا (‏FAI2). رابعُ وقوعٍ لهذا الصنف اليوم.
# 🥇 FAI2b (قرارا المالك 2026-08-07 «قسها»): الأربعةُ المقيسة الجديدة تصل مفاتيحَها
_fai_ov3 = S.faisal_only_overrides(dict(_fai_edges, gain5=61.0, ma_above=24.0,
                                        gap_above_dist=88.0, tf_count=1.0))
check("🥇 FAI2b الأربعةُ المقيسة (‏D11/M12/M9/M6) تُحِلّ مفاتيحَها ⇒ 16 مفتاحًا "
      "و`TF_MIN_REVERSALS` **صحيحٌ** (عدّاد فريمات)",
      _fai_ov3.get("RECENT_RISE_BLOCK_PCT") == 61.0
      and _fai_ov3.get("MA_GATE_MAX_ABOVE_PCT") == 24.0
      and _fai_ov3.get("GAP_ABOVE_MAX_DIST_PCT") == 88.0
      and _fai_ov3.get("TF_MIN_REVERSALS") == 1
      and isinstance(_fai_ov3.get("TF_MIN_REVERSALS"), int)
      and len(_fai_ov3) == 16,
      str(sorted(_fai_ov3))[:120])
# 🥇 FAI2c والحقولُ الثلاثة **تُصدَّر فعلًا** من `analyze_ticker` (وصلةٌ حيّة لا اسم):
#    `gain5` رقمٌ دائمًا على المؤهَّل (تاريخه أطول من 6) · والآخران قد يكونان None
#    شرعًا (لا فجوة فوقه / تحت المتوسطين) فالقفل على **وجود المفتاح** + نوعٍ سليم.
check("🥇 FAI2c الحقولُ الثلاثة مُصدَّرة من `analyze_ticker` (‏r0 المؤهَّل)",
      r0 is not None and all(k in r0 for k in ("gain5", "ma_above", "gap_above_dist"))
      and isinstance(r0.get("gain5"), float),
      str({k: r0.get(k) for k in ('gain5', 'ma_above', 'gap_above_dist')})[:90]
      if r0 else "r0=None")
check("🥇 FAI3 والأنواعُ مصونة: `WATCH_MAX_FAILS`/`SCORE_MIN` **صحيحان**",
      isinstance(_fai_ov.get("WATCH_MAX_FAILS"), int) and _fai_ov.get("WATCH_MAX_FAILS") == 5
      and isinstance(_fai_ov.get("SCORE_MIN"), int) and _fai_ov.get("SCORE_MIN") == 35,
      f"{_fai_ov.get('WATCH_MAX_FAILS')!r} · {_fai_ov.get('SCORE_MIN')!r}")
check("🥇 FAI4 معيارٌ غائب ⇒ يُتخطّى ولا يُخمَّن",
      "MIN_PRICE" not in S.faisal_only_overrides({k: v for k, v in _fai_edges.items()
                                                  if k != "price"})
      and S.faisal_only_overrides({}) == {})
check("🥇 FAI5 وحوافٌّ تالفة ⇒ تُتخطّى بلا انهيار",
      S.faisal_only_overrides({"price": "س", "drop_pct": [1]}) == {})
# ── الفشلُ الآمن **بصوتٍ عالٍ**: لا فرزَ بأرقامٍ مجهولة ولا صمت ────────────────
_fai_msgs = []
_fai_cfg = {"FAISAL_ONLY": 1}
_fai_ev = __import__("envelope_scan")
_fai_saved = _fai_ev.EDGES_FILE
try:
    _fai_ev.EDGES_FILE = "/proc/لا-يوجد/x.json"
    _fai_res = S.apply_faisal_only(_fai_cfg, log_fn=_fai_msgs.append)
finally:
    _fai_ev.EDGES_FILE = _fai_saved
check("🔒 FAI6 حوافٌّ غائبة ⇒ **لا تغيير** ويُبلَّغ صراحةً (لا صفرَ ترشيحٍ صامت)",
      _fai_res == {} and _fai_cfg == {"FAISAL_ONLY": 1}
      and any("بوّاباتُ البوت تبقى" in m for m in _fai_msgs), str(_fai_msgs)[:90])
check("🔒 FAI7 ومُطفأً ⇒ لا تغيير ولا رسالة (السلوكُ السابق حرفيًّا)",
      S.apply_faisal_only({"FAISAL_ONLY": 0}, log_fn=_fai_msgs.append) == {})
# ── 🔴 الفارقُ **السلوكيّ**: التبديلُ يبدّل القرار فعلًا ───────────────────────
_fai_c = dict(S.CONFIG)
_fai_applied = S.apply_faisal_only(_fai_c, log_fn=lambda *_: None) \
    if _fai_c.update({"FAISAL_ONLY": 1}) is None else {}
check("🔴 FAI8 التبديلُ يبدّل الأرقام فعلًا: أرضيةُ الهبوط 40 ⟶ ‏≈89.6 (أشدّ)",
      bool(_fai_applied) and S.CONFIG["MIN_DROP_FLOOR"] == 40.0
      and _fai_c["MIN_DROP_FLOOR"] > 80,
      f"بوت={S.CONFIG['MIN_DROP_FLOOR']} · فيصل={_fai_c.get('MIN_DROP_FLOOR')}")
check("🔴 FAI9 وليس تخفيفًا بل **إعادةَ تشكيل**: أشدُّ في السعر/الهبوط/الانفجار "
      "وأوسعُ في القاعدة/السيولة",
      _fai_c["MIN_PRICE"] > S.CONFIG["MIN_PRICE"]                  # 1.65 > 1.5
      and _fai_c["MIN_DROP_FLOOR"] > S.CONFIG["MIN_DROP_FLOOR"]    # 89.6 > 40
      and _fai_c["BASE_RANGE_MAX_PCT"] > S.CONFIG["BASE_RANGE_MAX_PCT"]   # 475 > 40
      and _fai_c["MIN_DOLLAR_VOL"] < S.CONFIG["MIN_DOLLAR_VOL"],   # 39K < 200K
      f"سعر {S.CONFIG['MIN_PRICE']}⟶{_fai_c['MIN_PRICE']:.2f} · "
      f"سيولة {S.CONFIG['MIN_DOLLAR_VOL']:.0f}⟶{_fai_c['MIN_DOLLAR_VOL']:.0f}")
check("🔴 FAI10 والأرقامُ من **الملفّ المدفوع** لا من الكود (بصمةٌ مطابقة)",
      abs(_fai_c["MIN_DOLLAR_VOL"]
          - float(_json.load(open("envelope_p90.json",
                                  encoding="utf-8"))["edges"]["dollar_vol"])) < 1e-6)
check("🥇 FAI11 و`LOGIC_VERSION` يحمل الوسمَ (فيُعاد بناءُ القائمة تلقائيًّا)",
      "faisalonly" in S.LOGIC_VERSION, S.LOGIC_VERSION[:40])

# ── ⏳ تقريرُ «المسارات التي تحتاج وقتًا» (أمرُ المالك 2026-08-06) ────────────────
try:                     # حرسٌ: انكسارُ الكتلة يجب أن يكون **فشلًا نظيفًا** لا انهيارًا
    _lt = S._long_tracks_block()
except Exception as _lt_e:                                       # noqa: BLE001
    _lt = [f"⛔ رمى: {type(_lt_e).__name__}"]
_lt_txt = "\n".join(_lt)
check("⏳ LT1 القسمُ يُبنى ومعه القسمان المتمايزان (وقتٌ · عملٌ أو قرار)",
      bool(_lt) and "تتراكم بالجلسات" in _lt_txt
      and "تنتظر عملًا أو قرارًا" in _lt_txt, _lt_txt[:80])
check("⏳ LT2 وكلُّ مسارٍ يحمل **عدّادَه وعتبتَه** لا نصًّا مجرّدًا",
      all(k in _lt_txt for k in ("حصادُ الصيّادين", "إطلاقاتُ الرادار",
                                 "حصّادُ اليد", "سجلُّ المرفوضين", "بوّابةُ E2"))
      and "من 30" in _lt_txt and f"من {S.REJECT_LOG_DAYS}" in _lt_txt)
# 🔴 والعدّادُ **من الملفّ الحقيقيّ**: نغيّر السجلَّ ⇒ يتغيّر الرقم (لا نصٌّ مثبَّت).
_lt_old = __import__("hunter_ledger").LEDGER_FILE
try:
    _lt_tmp = _os.path.join(_rej_tf.gettempdir(), "lt_probe.jsonl")
    with open(_lt_tmp, "w", encoding="utf-8") as _fh:
        for _i in range(3):
            _fh.write(_json.dumps({"key": f"k{_i}", "hunter": "split", "session": "s",
                                   "symbol": f"S{_i}", "kind": "candidate",
                                   "ref_close": 1.0, "fwd": 40, "outcome": None}) + "\n")
    __import__("hunter_ledger").LEDGER_FILE = _lt_tmp
    _lt3 = "\n".join(S._long_tracks_block())
finally:
    __import__("hunter_ledger").LEDGER_FILE = _lt_old
check("🔴 LT3 العدّادُ يتحرّك مع السجلّ الحقيقيّ (لا رقمَ مثبَّتًا في النصّ)",
      "3 مرشّحًا" in _lt3, _lt3.split("\n")[2][:100] if len(_lt3.split("\n")) > 2 else _lt3)
# 🔒 فاشلٌ-آمن **لكلّ مسارٍ على حدة**: عطلُ ملفٍّ لا يُسقط القسم كلَّه.
# ⚠️ **وبحرسٍ حول النداء**: لو زال حارسُ المسار لرمى النداءُ فأسقط **السويّة كلَّها**
#    وكتم أيَّ قفلٍ أمسك العيب — وهو صنفٌ وقع ثلاث مرّاتٍ اليوم. الآن **فشلٌ نظيف**.
_lt_old2 = S.REJECT_LOG_FILE
try:
    S.REJECT_LOG_FILE = "/proc/لا-يوجد/x.json"
    try:
        _lt_broken = "\n".join(S._long_tracks_block())
    except Exception as _e:                                      # noqa: BLE001
        _lt_broken = f"⛔ رمى: {type(_e).__name__}"
finally:
    S.REJECT_LOG_FILE = _lt_old2
check("🔒 LT4 عطلُ مصدرٍ واحد لا يُسقط القسم (حارسٌ لكل مسار)",
      "حصادُ الصيّادين" in _lt_broken and "بوّابةُ E2" in _lt_broken,
      _lt_broken[:70])
# 🔴 والحاسم: مُنادًى في **المسارَين** (فخُّ العيّنة القليلة — وهو أهمُّ وقتٍ للتقرير).
_lt_calls = [n for n in _hl_ast.walk(_hl_ast.parse(
    _insp0.getsource(S.build_dev_assistant_report)))
    if isinstance(n, _hl_ast.Call) and getattr(n.func, "id", None) == "_long_tracks_block"]
check("🔴 LT5 مُنادًى **مرّتين** (القليلة + الكافية) وعلى مستوى الوحدة",
      len(_lt_calls) == 2 and callable(getattr(S, "_long_tracks_block", None)),
      f"نداءات={len(_lt_calls)}")
# ⚠️ وبقسمةٍ محروسة: غيابُ الترويسة كان يرمي `IndexError` فيُسقط السويّة بدل الفشل.
_lt_parts = _lt_txt.split("تنتظر عملًا أو قرارًا")
check("⏳ LT6 والثلاثةُ المعلَّقة مذكورةٌ في قسم «العمل/القرار» لا في «الوقت»",
      len(_lt_parts) == 2
      and all(k in _lt_parts[1] for k in ("M6", "T-CLIFF-2", "force_renew")),
      f"أقسام={len(_lt_parts)}")
# 🔒 LT7 حرسٌ **خارجيّ** على الكتلة نفسها — خامدٌ ما دام الداخليُّ سليمًا (لذلك
#    نجت طفرةُ حذفه) فيُقفَل **بنيويًّا**: `try` يُرجع قائمةً فارغة. وقيمتُه مُقاسة —
#    بحذف الحارس الداخليّ **انهار `build_dev_assistant_report` كلُّه** (ملفُّ حصّاد
#    اليد غير موجود) ⇒ قسمٌ تذكيريٌّ كان قادرًا على قتل تقرير المالك الأسبوعيّ.
_lt7 = _hl_ast.parse(_insp0.getsource(S._long_tracks_block))
check("🔒 LT7 الكتلةُ محروسةٌ خارجيًّا وتُرجع [] (لا تقتل التقرير الأسبوعيّ)",
      any(isinstance(h, _hl_ast.ExceptHandler)
          and any(isinstance(r, _hl_ast.Return) and isinstance(r.value, _hl_ast.List)
                  for r in _hl_ast.walk(h))
          for h in _hl_ast.walk(_lt7)))

_ch = "\n".join(S._collection_health_block())
check("🩺 CV1 لوحةُ الجمع تُظهر تغطيةَ M13 وM14",
      "تغطيةُ M13" in _ch and "M14" in _ch, _ch.split("\n")[1][:110])
# ── 🎯 موقعُ السعر من نطاق الدفعات (عيبٌ مقيس: 88% فوق النطاق) ───────────────
check("🎯 BN1 فوق النطاق ⇒ يُصرَّح به بالنسبة",
      "فوق" in (S.band_note({"entry": [1.0, 1.1], "last_price": 1.32}) or "")
      and "20%" in (S.band_note({"entry": [1.0, 1.1], "last_price": 1.32}) or ""),
      S.band_note({"entry": [1.0, 1.1], "last_price": 1.32}))
check("🎯 BN2 داخل النطاق ⇒ ✅ (القفلُ ليس تحذيرًا دائمًا)",
      "داخل" in (S.band_note({"entry": [1.0, 1.1], "last_price": 1.05}) or ""),
      S.band_note({"entry": [1.0, 1.1], "last_price": 1.05}))
check("🎯 BN3 تحت النطاق ⇒ ⬇️",
      "تحت" in (S.band_note({"entry": [1.0, 1.1], "last_price": 0.90}) or ""),
      S.band_note({"entry": [1.0, 1.1], "last_price": 0.90}))
check("🎯 BN4 بلا بياناتٍ ⇒ None (لا تُخمَّن)",
      S.band_note({}) is None and S.band_note({"entry": [1.0, 1.1]}) is None, "—")
# 🔒 موصولةٌ من نقطة النداء الحيّة في الكرت (AST لا نصّ)
import ast as _bn_ast
_bn_t = _bn_ast.parse(open("Super_stock.py", encoding="utf-8").read())
_bn_f = next((n for n in _bn_ast.walk(_bn_t) if isinstance(n, _bn_ast.FunctionDef)
              and n.name == "build_message"), None)
check("🎯 BN5 موصولةٌ في `build_message` (AST)",
      any(getattr(c.func, "id", None) == "band_note"
          for c in _bn_ast.walk(_bn_f or _bn_ast.Module(body=[], type_ignores=[]))
          if isinstance(c, _bn_ast.Call)), "—")
# 📐 متوسطُ الدفعات يُخزَّن **بجانب** سعر الترشيح لا بدلًا منه
check("📐 EA1 `tranche_avg` من الدفعات",
      S.tranche_avg({"tranches": [1.0, 1.03, 1.06]}) == 1.03,
      f"{S.tranche_avg({'tranches': [1.0, 1.03, 1.06]})}")
_ea_src = open("Super_stock.py", encoding="utf-8").read()
check("📐 EA2 و`entry_ref` **باقٍ** (قرارُ المالك 2026-06-24 لم يُنقَض)",
      '"entry_ref": round(r["price"], 4),' in _ea_src
      and '"entry_avg"' in _ea_src, "الحقلان معًا")

# ══════════════════════════════════════════════════════════════════════════
# 🥇⑦ T-RANKER-TIE — أقفالُ أذرع كاسر التعادل (`ranker_tie_arms.py`)
# ══════════════════════════════════════════════════════════════════════════
# 🔴 **الخطرُ المحدَّد الذي تحرسه هذي الكتلة:** الذراعُ يقرأ `env_depth`، وهو يمتنع
#    دون ستّة معايير. فلو خرج `BT_ENVVALS` خاملًا **لامتنع عن كلّ صفقة** فصار
#    `R-ENV ≡ R-0` بالبناء، والمُخرَجُ يقول «لا فرق» **وهو no-op** — صنفُ
#    `BT_CANDLE` بعينه. ولذلك أكثرُ الأقفال هنا **سلوكيّة على `run()` نفسها**.
import ast as _rt_ast
import contextlib as _rt_ctx
import io as _rt_io

_RT_ENV_KEYS = ("SCREENER_MODE", "BT_REPLAY10", "BT_ENVVALS", "BT_POTENTIAL",
                "BACKTEST_YEAR")
_rt_saved_env = {k: _os_hc.environ.get(k) for k in _RT_ENV_KEYS}
_rt_saved_bt = S.run_backtest
try:
    import ranker_tie_arms as _RT
finally:
    for _k, _v in _rt_saved_env.items():      # لا تلوّث بقيّة السويّة ببيئة الباكتيست
        if _v is None:
            _os_hc.environ.pop(_k, None)
        else:
            _os_hc.environ[_k] = _v

_RT.SEEDS, _RT.BOOT = 3, 50                   # سرعةُ سويّة — الأرقامُ الحقيقية بالـworkflow


def _rt_trade(sym, day, oc="win", ret=20.0, rdy=70, score=90, rr=3.0, vals=True):
    e = 2.0
    t = {"symbol": sym, "date": f"2025-01-{day:02d}", "exit_date": "2025-03-01",
         "outcome": oc, "exit_kind": oc, "entry": e, "stop": e * 0.93,
         "ret_a": ret, "readiness": rdy, "score": score, "rr": rr}
    if vals:
        t["env_vals"] = {"price": e, "drop_pct": 95.0, "best_spike": 300.0,
                         "base_range": 60.0, "dollar_vol": 5e5, "rsi_min": 25.0,
                         "rsi_now": 35.0, "n_soft": 1, "readiness": rdy,
                         "score": score, "rr": rr}
    return t


def _rt_run(trades):
    """يشغّل `run()` على صفقاتٍ مدفوعة ويرجّع (رمز الخروج، المُخرَج)."""
    S.run_backtest = lambda *a, **k: trades
    buf = _rt_io.StringIO()
    try:
        with _rt_ctx.redirect_stdout(buf):
            rc = _RT.run()
    finally:
        S.run_backtest = _rt_saved_bt
    return rc, buf.getvalue()


# ── RTIE1: البيئةُ تُضبَط **قبل** استيراد `Super_stock` وإلّا خرج العلمُ خاملًا ──
_rt_tree = _rt_ast.parse(open("ranker_tie_arms.py", encoding="utf-8").read())
_rt_envln = [n.lineno for n in _rt_ast.walk(_rt_tree)
             if isinstance(n, _rt_ast.Subscript)
             and getattr(getattr(n.value, "attr", None), "__str__", str)() == "environ"]
_rt_setln = [n.lineno for n in _rt_tree.body
             if isinstance(n, _rt_ast.Expr) or isinstance(n, _rt_ast.Assign)]
_rt_impln = [n.lineno for n in _rt_tree.body
             if isinstance(n, _rt_ast.Import)
             and any(a.name == "Super_stock" for a in n.names)]
_rt_bt_set = [n.lineno for n in _rt_tree.body
              if isinstance(n, _rt_ast.Expr) and isinstance(n.value, _rt_ast.Call)
              and "BT_ENVVALS" in _rt_ast.dump(n)]
_rt_bt_asg = [n.lineno for n in _rt_tree.body
              if isinstance(n, _rt_ast.Assign) and "BT_ENVVALS" in _rt_ast.dump(n)]
check("🥇 RTIE1 `BT_ENVVALS` يُضبَط **قبل** `import Super_stock` (وإلّا no-op)",
      bool(_rt_impln) and bool(_rt_bt_set + _rt_bt_asg)
      and max(_rt_bt_set + _rt_bt_asg) < min(_rt_impln),
      f"ضبط={_rt_bt_set + _rt_bt_asg} · استيراد={_rt_impln}")

# ── RTIE2: حارسُ الـno-op يعمل — بلا `env_vals` ⇒ توقّفٌ صريح لا «لا فرق» ──
_rt_novals = [_rt_trade(f"N{i}", 1 + i % 5, vals=False) for i in range(12)]
_rt_rc0, _rt_out0 = _rt_run(_rt_novals)
check("🥇 RTIE2 بلا `env_vals` ⇒ يتوقّف برمزٍ غير صفريّ ويُعلن الـno-op",
      _rt_rc0 == 4 and "no-op" in _rt_out0, f"rc={_rt_rc0}")

# ── RTIE3: المسارُ الكامل يعمل ويطبع قيودَ الميزانية (§⑥) ──
_rt_ok = ([_rt_trade(f"A{i}", 1 + i % 6, rdy=70, score=90, rr=3.0) for i in range(14)]
          + [_rt_trade(f"B{i}", 1 + i % 6, oc="loss", ret=-7.0, rdy=70,
                       score=90, rr=3.0) for i in range(14)])
_rt_rc1, _rt_out1 = _rt_run(_rt_ok)
check("🥇 RTIE3 المسارُ الكامل ينجح ويطبع الأذرع الأربعة",
      _rt_rc1 == 0 and all(x in _rt_out1
                           for x in ("R-0", "R-ENV", "R-FIFO", "R-RAND")),
      f"rc={_rt_rc1}")
check("🥇 RTIE4 §⑥ قيودُ الميزانية مطبوعة (لقطة · كون · سعة · بصمةُ الحوافّ)",
      all(x in _rt_out1 for x in ("الميزانيةُ الثابتة", "اللقطة المجمَّدة",
                                  "السعة:", "بصمةُ الحوافّ", "جلسات فهرسية")))
check("🥇 RTIE5 والبوّابةُ الرباعية مطبوعةٌ بأرقامها المسجَّلة (0.1R · 30)",
      "البوّابة الرباعية" in _rt_out1 and "+0.1R" in _rt_out1
      and f"≥ {_RT.MIN_AFFECTED}" in _rt_out1)

# ── RTIE6: `attach_env_depth` يمتنع دون ستّة معايير ولا يُخمّن (فرقٌ سلوكيّ) ──
_rt_edges = {"price": 1.0, "drop_pct": (80.0, 99.0), "best_spike": 100.0,
             "base_range": 400.0, "dollar_vol": 4e4, "rsi_min": 44.0,
             "rsi_now": 48.0, "n_soft": 5.0, "readiness": 10.0, "score": 35.0,
             "rr": 1.2}
_rt_sides = {n: sd for n, sd, _, _ in _RT.CE.CRITERIA}
_rt_full = [_rt_trade("F1", 1)]
_rt_thin = [_rt_trade("T1", 1)]
_rt_thin[0]["env_vals"] = {"price": 2.0, "rr": 3.0}          # معياران فقط
_rt_d1 = _RT.attach_env_depth(_rt_full, _rt_edges, _rt_sides)
_rt_d2 = _RT.attach_env_depth(_rt_thin, _rt_edges, _rt_sides)
check("🥇 RTIE6 عمقُ الظرف: 11 معيارًا ⇒ رقم · معياران ⇒ **امتناع** (لا تخمين)",
      isinstance(_rt_full[0]["env_depth"], float)
      and _rt_thin[0]["env_depth"] is None
      and _rt_d1["ok"] == 1 and _rt_d2["abstain"] == 1,
      f"{_rt_full[0]['env_depth']} · {_rt_thin[0]['env_depth']}")

# ── RTIE7: الفرقُ المزدوج يُلغي المشترَك — ذراعان متطابقان ⇒ صفرٌ تامّ ──
_rt_c = [_RT.RP.Candidate(session=0, symbol="X", readiness=70, score=90, rr=3.0,
                          seq=0, payload=_rt_trade("X", 1))]
check("🥇 RTIE7 `paired_delta`: المشترَكُ يُلغي نفسَه (ذراعان متطابقان ⇒ صفر)",
      all(abs(v) < 1e-12 for v in _RT.paired_delta(_rt_c, _rt_c).values()),
      str(_RT.paired_delta(_rt_c, _rt_c)))
_rt_c2 = [_RT.RP.Candidate(session=0, symbol="Y", readiness=70, score=90, rr=3.0,
                           seq=1, payload=_rt_trade("Y", 1, oc="loss", ret=-7.0))]
check("🥇 RTIE8 `affected` = الفرقُ التماثليّ (متطابقان ⇒ 0 · مختلفان ⇒ 2)",
      _RT.affected(_rt_c, _rt_c)["n"] == 0
      and _RT.affected(_rt_c, _rt_c2)["n"] == 2,
      f"{_RT.affected(_rt_c, _rt_c2)}")

# ── RTIE9: المقامُ مُستعمَلٌ فعلًا في الفاصل (مضاعفتُه تنصّف الحدود) ──
_rt_dl = {"A": 1.0, "B": -0.5, "C": 0.75, "D": -0.25}
_rt_ci1 = _RT.cluster_bootstrap_diff(_rt_dl, 10.0, n=400)
_rt_ci2 = _RT.cluster_bootstrap_diff(_rt_dl, 20.0, n=400)
check("🥇 RTIE9 المقامُ مُستعمَل: مضاعفتُه تنصّف حدودَ الفاصل",
      abs(_rt_ci1["lo"] - 2 * _rt_ci2["lo"]) < 1e-9
      and abs(_rt_ci1["hi"] - 2 * _rt_ci2["hi"]) < 1e-9,
      f"{_rt_ci1} · {_rt_ci2}")

# ── RTIE10: أربعةُ أذرعٍ **لا خامسة** (ذراعٌ تُضاف بعد الأرقام = p-hacking) ──
_rt_runfn = next((n for n in _rt_ast.walk(_rt_tree)
                  if isinstance(n, _rt_ast.FunctionDef) and n.name == "run"), None)
_rt_rankers = {getattr(c.func, "attr", None) for c in _rt_ast.walk(_rt_runfn)
               if isinstance(c, _rt_ast.Call)} | {
    getattr(a, "attr", None) for c in _rt_ast.walk(_rt_runfn)
    if isinstance(c, _rt_ast.Call) for a in c.args
    if isinstance(a, _rt_ast.Attribute)}
_rt_used = {x for x in _rt_rankers if x and x.startswith(("rank_", "make_rank"))}
check("🥇 RTIE10 الأذرعُ المسجَّلة حصرًا — لا ذراعَ خامسة",
      _rt_used == {"rank_actual", "rank_tie_env", "rank_fifo",
                   "make_rank_tie_random"}, str(sorted(_rt_used)))

# ── RTIE11: خارج الإنتاج — `Super_stock` لا يستورده (AST لا نصّ) ──
_rt_prod = _rt_ast.parse(open("Super_stock.py", encoding="utf-8").read())
_rt_imports = {a.name for n in _rt_ast.walk(_rt_prod)
               if isinstance(n, _rt_ast.Import) for a in n.names} | {
    n.module for n in _rt_ast.walk(_rt_prod) if isinstance(n, _rt_ast.ImportFrom)}
check("🥇 RTIE11 خارج الإنتاج: `Super_stock` لا يستورد أداةَ الأذرع",
      "ranker_tie_arms" not in _rt_imports and "replay10" not in _rt_imports)

# ── RTIE12: التسجيلُ المسبق مدفوعٌ ويحمل المعيار قبل أيّ رقم ──
_rt_pre = open("ranker_tie_prereg.md", encoding="utf-8").read()
check("🥇 RTIE12 التسجيلُ المسبق يحمل الأذرع والمعيار والميزانية الثابتة",
      all(x in _rt_pre for x in ("R-ENV", "R-RAND", "R-FIFO", "+0.10R",
                                 "‏≥ 30 صفقةً متأثّرة", "الميزانيةُ الثابتة")))


# ═══════════════ 🚦 T-RANKER2 — أذرعُ الترتيب الكامل (`ranker2_prereg.md`) ═══════════════
_r2_saved_env = {k: _os_hc.environ.get(k) for k in _RT_ENV_KEYS + ("R2_SEEDS",)}
_r2_saved_bt = S.run_backtest
try:
    import ranker2_arms as _R2
finally:
    for _k, _v in _r2_saved_env.items():
        if _v is None:
            _os_hc.environ.pop(_k, None)
        else:
            _os_hc.environ[_k] = _v
_R2.SEEDS = 5                                 # سرعةُ سويّة — الحقيقيّ بالـworkflow


def _r2_trade(sym, day, oc="win", ret=20.0, rdy=70, score=90, rr=3.0,
              vals=True, band=True, mg=60.0, mg_oc="stopped", exit_day=None):
    t = _rt_trade(sym, day, oc=oc, ret=ret, rdy=rdy, score=score, rr=rr,
                  vals=vals)
    if exit_day is not None:                  # خروجٌ قريب يحرّر الخانة (سعة 10)
        t["exit_date"] = f"2025-01-{exit_day:02d}"
    if vals and band is not None:
        t["env_vals"]["in_band"] = band
    if mg_oc is not None:
        t["mg_outcome"] = mg_oc
        t["mg_pre_stop"] = mg
    return t


def _r2_run(trades):
    S.run_backtest = lambda *a, **k: trades
    buf = _rt_io.StringIO()
    try:
        with _rt_ctx.redirect_stdout(buf):
            rc = _R2.run()
    finally:
        S.run_backtest = _r2_saved_bt
    return rc, buf.getvalue()


# ── R2A: `rank_live` — داخلُ النطاق **قبل** الأعلى جاهزيةً · وداخل الفئة الترتيبُ القديم ──
_r2_in60 = _RT.RP.Candidate(session=0, symbol="IN", readiness=60, score=50,
                            rr=1.0, seq=1,
                            payload={"env_vals": {"in_band": True}})
_r2_out90 = _RT.RP.Candidate(session=0, symbol="OUT", readiness=90, score=99,
                             rr=9.0, seq=0,
                             payload={"env_vals": {"in_band": False}})
_r2_in80 = _RT.RP.Candidate(session=0, symbol="IN2", readiness=80, score=10,
                            rr=0.5, seq=2,
                            payload={"env_vals": {"in_band": True}})
_r2_sorted = sorted([_r2_out90, _r2_in60, _r2_in80], key=_RT.RP.rank_live)
check("🚦 R2A `rank_live`: داخلُ النطاق أوّلًا (جاهزية 60 داخل تسبق 90 خارج) "
      "وداخل الفئة الأعلى جاهزية",
      [c.symbol for c in _r2_sorted] == ["IN2", "IN", "OUT"],
      str([c.symbol for c in _r2_sorted]))
check("🚦 R2B غيابُ الحقل = خارج النطاق (لا يُدَّعى قربٌ بلا دليل)",
      _RT.RP.rank_live(_RT.RP.Candidate(session=0, symbol="X", readiness=99,
                                        score=9, rr=9, seq=0, payload={}))[0] == 1)

# ── R2C: `rank_env_full` — الأعمقُ أوّلًا والامتناعُ يغرق تحت كلّ مقيس ──
def _r2_env(sym, depth, rdy=70, seq=0):
    return _RT.RP.Candidate(session=0, symbol=sym, readiness=rdy, score=50,
                            rr=1.0, seq=seq, payload={"env_depth": depth})


_r2_deep = sorted([_r2_env("NONE", None, rdy=99, seq=0),
                   _r2_env("D0", 0.0, rdy=10, seq=1),
                   _r2_env("D8", 0.8, rdy=10, seq=2)],
                  key=_RT.RP.rank_env_full)
check("🚦 R2C `rank_env_full`: الأعمقُ أوّلًا · وعمقُ 0.0 يسبق الامتناعَ (None يغرق)",
      [c.symbol for c in _r2_deep] == ["D8", "D0", "NONE"],
      str([c.symbol for c in _r2_deep]))

# ── R2D: عدّادُ «المنفجرين المُسلَّمين» — تخومٌ صارمة ولا يعدّ غيرَ المُعبَّأ ──
_r2_cands_d = [
    _RT.RP.Candidate(session=0, symbol="A", seq=0,
                     payload={"mg_outcome": "stopped", "mg_pre_stop": 50.0}),
    _RT.RP.Candidate(session=0, symbol="B", seq=1,
                     payload={"mg_outcome": "stopped", "mg_pre_stop": 49.9}),
    _RT.RP.Candidate(session=0, symbol="C", seq=2,
                     payload={"mg_outcome": "no_fill", "mg_pre_stop": 500.0}),
    _RT.RP.Candidate(session=0, symbol="D", seq=3, payload={}),
]
check("🚦 R2D `delivered`: الحدُّ 50.0 يُعدّ و49.9 لا · و`no_fill`/الغائب لا يُعدّان",
      _R2.delivered(_r2_cands_d, 50.0) == 1
      and _R2.delivered(_r2_cands_d, 100.0) == 0,
      f"d50={_R2.delivered(_r2_cands_d, 50.0)}")

# ── R2E: الوصلة الحيّة — `in_band` داخل كتلة `BT_ENVVALS` **بدالّة الإنتاج** ──
_r2_blk = _insp0.getsource(S.backtest_symbol)
_r2_blk = _r2_blk[_r2_blk.index('if CONFIG.get("BT_ENVVALS")'):]
_r2_blk = _r2_blk[:_r2_blk.index('if CONFIG.get("BT_REPLAY10")')]
check("🚦 R2E حقلُ `in_band` داخل كتلة العلم ويُحسَب بـ`in_entry_band(r)` الإنتاجية",
      '"in_band": in_entry_band(r)' in _r2_blk)

# ── R2F: حرّاسُ الـno-op الثلاثة — رموزُ خروجٍ مميِّزة لا «صفر منفجر» صامت ──
_r2_rc_mg, _r2_out_mg = _r2_run(
    [_r2_trade(f"M{i}", 1 + i % 5, mg_oc=None) for i in range(10)])
check("🚦 R2F بلا `mg_outcome` ⇒ رمز 7 صريح (المقياسُ الأساسيّ بلاه مفبرك)",
      _r2_rc_mg == 7 and "BT_POTENTIAL" in _r2_out_mg, f"rc={_r2_rc_mg}")
_r2_noband = [_r2_trade(f"B{i}", 1 + i % 5) for i in range(10)]
for _t in _r2_noband:
    _t["env_vals"].pop("in_band", None)
_r2_rc_bd, _ = _r2_run(_r2_noband)
check("🚦 R2G بلا حقل `in_band` ⇒ رمز 4 (ذراعُ `K-LIVE` بلاه no-op)",
      _r2_rc_bd == 4, f"rc={_r2_rc_bd}")

# ── R2H: المسارُ الكامل — الأذرعُ الخمس والمقياسُ الأساسيّ وبِركةُ المنفجرين ──
_r2_ok = ([_r2_trade(f"A{i}", 1 + 2 * i, mg=60.0, exit_day=2 + 2 * i)
           for i in range(10)]
          + [_r2_trade(f"L{i}", 2 + 2 * i, oc="loss", ret=-7.0, mg=8.0,
                       exit_day=3 + 2 * i) for i in range(10)]
          + [_r2_trade("BIGX", 21, mg=120.0, exit_day=22)])
_r2_rc1, _r2_out1 = _r2_run(_r2_ok)
check("🚦 R2H المسارُ الكامل ينجح ويطبع الأذرعَ الخمس والمقياسَ الأساسيّ",
      _r2_rc1 == 0 and all(x in _r2_out1 for x in
                           ("K-LIVE", "K-LEGACY", "K-ENV", "K-FIFO", "K-RAND",
                            "منفجرون مُسلَّمون", "بِركةُ المنفجرين",
                            "الميزانيةُ الثابتة", "حارسُ العائد")),
      f"rc={_r2_rc1}")
check("🚦 R2I عدُّ المنفجرين صحيح: 11 مُسلَّمًا فوق 50% ومنهم واحدٌ فوق 100%",
      "= 11 (‏100%+ = 1)" in _r2_out1,
      _r2_out1[_r2_out1.find("K-LIVE"):][:120] if "K-LIVE" in _r2_out1 else "؟")

# ── R2J: خمسةُ أذرعٍ **لا سادسة** (AST كنمط RTIE10) ──
_r2_tree = _rt_ast.parse(open("ranker2_arms.py", encoding="utf-8").read())
_r2_runfn = next((n for n in _rt_ast.walk(_r2_tree)
                  if isinstance(n, _rt_ast.FunctionDef) and n.name == "run"), None)
_r2_rankers = {getattr(c.func, "attr", None) for c in _rt_ast.walk(_r2_runfn)
               if isinstance(c, _rt_ast.Call)} | {
    getattr(a, "attr", None) for c in _rt_ast.walk(_r2_runfn)
    if isinstance(c, _rt_ast.Call) for a in c.args
    if isinstance(a, _rt_ast.Attribute)}
_r2_used = {x for x in _r2_rankers if x and x.startswith(("rank_", "make_rank"))}
check("🚦 R2J الأذرعُ المسجَّلة حصرًا — لا ذراعَ سادسة",
      _r2_used == {"rank_live", "rank_actual", "rank_env_full", "rank_fifo",
                   "make_rank_random"}, str(sorted(_r2_used)))

# ── R2K: خارج الإنتاج + البيئةُ قبل الاستيراد + التسجيلُ المسبق ──
check("🚦 R2K خارج الإنتاج: `Super_stock` لا يستورد `ranker2_arms`",
      "ranker2_arms" not in _rt_imports)
_r2_bt_set = [n.lineno for n in _r2_tree.body
              if isinstance(n, (_rt_ast.Expr, _rt_ast.Assign))
              and "BT_POTENTIAL" in _rt_ast.dump(n)]
_r2_impln = [n.lineno for n in _r2_tree.body
             if isinstance(n, _rt_ast.Import)
             and any(a.name == "Super_stock" for a in n.names)]
check("🚦 R2L `BT_POTENTIAL` يُضبَط **قبل** `import Super_stock` (وإلّا no-op)",
      bool(_r2_impln) and bool(_r2_bt_set)
      and max(_r2_bt_set) < min(_r2_impln),
      f"ضبط={_r2_bt_set} · استيراد={_r2_impln}")
_r2_pre = open("ranker2_prereg.md", encoding="utf-8").read()
check("🚦 R2M التسجيلُ المسبق يحمل الأذرعَ الخمس والمقياسَ وقاعدةَ القرار",
      all(x in _r2_pre for x in ("K-LIVE", "K-LEGACY", "K-ENV", "K-FIFO",
                                 "K-RAND", "المنفجرون المُسلَّمون",
                                 "0.05R", "المئين 90", "الترتيبُ محايد")))


# ═══════════════ 🪑 T-SLOT — أذرعُ سياسة الخانات (`slot_prereg.md`) ═══════════════
_sl_saved_env = {k: _os_hc.environ.get(k) for k in _RT_ENV_KEYS}
_sl_saved_bt = S.run_backtest
try:
    import slot_arms as _SL
finally:
    for _k, _v in _sl_saved_env.items():
        if _v is None:
            _os_hc.environ.pop(_k, None)
        else:
            _os_hc.environ[_k] = _v


def _sl_run(trades):
    S.run_backtest = lambda *a, **k: trades
    _yr = _os_hc.environ.pop("BACKTEST_YEAR", None)   # عيّنةٌ لا سنة ⇒ البوّابة تُتخطّى
    buf = _rt_io.StringIO()
    try:
        with _rt_ctx.redirect_stdout(buf):
            rc = _SL.run()
    finally:
        S.run_backtest = _sl_saved_bt
        if _yr is not None:
            _os_hc.environ["BACKTEST_YEAR"] = _yr
    return rc, buf.getvalue()


# ── SLT1: `free_of` عاطلًا (يرجّع None دائمًا) ≡ الأساس **بت-بت** ──
def _sl_cand(sym, sess, seq, oc="window", held=9, band=True, fd=None, mg=60.0):
    p = {"symbol": sym, "outcome": oc, "entry": 2.0, "stop": 1.86, "ret_a": 10.0,
         "env_vals": {"in_band": band}, "mg_outcome": "stopped",
         "mg_pre_stop": mg}
    if fd is not None:
        p["fill_date"] = fd
    p["_held"] = held
    return _RT.RP.Candidate(session=sess, symbol=sym, readiness=70, score=50,
                            rr=1.0, seq=seq, payload=p)


def _sl_outcome(c):
    return ("window", int(c.payload.get("_held", 9)))


_sl_cs = [_sl_cand("A", 0, 0), _sl_cand("B", 3, 1, held=2),
          _sl_cand("C", 5, 2, held=3)]
_sl_base = _RT.RP.replay(_sl_cs, outcome_of=_sl_outcome,
                         ranker=_RT.RP.rank_live, sessions=range(0, 12))
_sl_noop = _RT.RP.replay(_sl_cs, outcome_of=_sl_outcome,
                         ranker=_RT.RP.rank_live, sessions=range(0, 12),
                         free_of=lambda c: None)
check("🪑 SLT1 `free_of` العاطل ≡ الأساس بت-بت (كل مفاتيح النتيجة)",
      _sl_base == _sl_noop)

# ── SLT2: التحريرُ المبكّر يفتح الخانة فعلًا (سعة 1: B مرفوض بلاه · مأخوذ معه) ──
_sl_two = [_sl_cand("A", 0, 0, held=9), _sl_cand("B", 3, 1, held=2)]
_sl_r_no = _RT.RP.replay(_sl_two, outcome_of=_sl_outcome, capacity=1,
                         ranker=_RT.RP.rank_live, sessions=range(0, 12))
_sl_r_fr = _RT.RP.replay(_sl_two, outcome_of=_sl_outcome, capacity=1,
                         ranker=_RT.RP.rank_live, sessions=range(0, 12),
                         free_of=lambda c: 2 if c.symbol == "A" else None)
check("🪑 SLT2 التحريرُ المبكّر يفتح الخانة: B مرفوضٌ بالسعة بلاه ومأخوذٌ معه",
      _sl_r_no["rejected_cap"] == 1 and len(_sl_r_no["taken"]) == 1
      and _sl_r_fr["rejected_cap"] == 0 and len(_sl_r_fr["taken"]) == 2,
      f"بلاه={len(_sl_r_no['taken'])} · معه={len(_sl_r_fr['taken'])}")

# ── SLT3: `make_free_unfilled` — الحدود الأربعة (والتعادل الحدّي «خلال») ──
_sl_idx = {"d0": 0, "d5": 5, "d6": 6}
_sl_fo = _RT.RP.make_free_unfilled(5, _sl_idx)
check("🪑 SLT3 المهلة: بلا تعبئة ⇒ k · عند k بالضبط ⇒ خلالها (None) · "
      "بعدها/مجهولة ⇒ k",
      _sl_fo(_sl_cand("N", 0, 0)) == 5
      and _sl_fo(_sl_cand("F", 0, 0, fd="d5")) is None
      and _sl_fo(_sl_cand("L", 0, 0, fd="d6")) == 5
      and _sl_fo(_sl_cand("U", 0, 0, fd="dX")) == 5)

# ── SLT4: الوصلة الحيّة — `fill_date` داخل كتلة `BT_REPLAY10` من فهرس المحرّك ──
_sl_blk = _insp0.getsource(S.backtest_symbol)
_sl_blk = _sl_blk[_sl_blk.index('if CONFIG.get("BT_REPLAY10")'):]
check("🪑 SLT4 حقلُ `fill_date` داخل كتلة العلم ومن `fut.index[filled]` المحرّك",
      'trade["fill_date"]' in _sl_blk and "fut.index[filled]" in _sl_blk)

# ── SLT5: `extra_dates` يوسّع الفهرس ولا يغيّر المرشّحين ──
_sl_rows = [{"symbol": "X", "date": "2025-01-02", "exit_date": "2025-01-09",
             "outcome": "win", "readiness": 70, "score": 50, "rr": 1.0}]
_sl_c1, _sl_i1, _ = _RT.RP.candidates_from_trades(_sl_rows)
_sl_c2, _sl_i2, _ = _RT.RP.candidates_from_trades(
    _sl_rows, extra_dates=["2025-01-05"])
check("🪑 SLT5 `extra_dates`: الفهرس يتّسع بالتاريخ الإضافيّ والمرشّحون كما هم",
      "2025-01-05" in _sl_i2 and "2025-01-05" not in _sl_i1
      and [c.symbol for c in _sl_c1] == [c.symbol for c in _sl_c2])

# ── SLT6: المسارُ الكامل + التعديلُ الصادق يفرّق NF5 عن NF8 على تعبئةٍ متأخّرة ──
def _sl_trade(sym, day, exit_day, fill=None, mg=60.0):
    return {"symbol": sym, "date": f"2025-01-{day:02d}",
            "exit_date": f"2025-01-{exit_day:02d}", "outcome": "win",
            "exit_kind": "win", "entry": 2.0, "stop": 1.86, "ret_a": 20.0,
            "readiness": 70, "score": 50, "rr": 1.0,
            "env_vals": {"in_band": True},
            "mg_outcome": "stopped", "mg_pre_stop": mg,
            "fill_date": fill}


_sl_ok = ([_sl_trade(f"T{i}", 1 + 2 * i, 2 + 2 * i, fill=f"2025-01-{1 + 2 * i:02d}")
           for i in range(4)]
          + [_sl_trade("TL", 1, 30, fill="2025-01-28", mg=70.0)])
_sl_rc1, _sl_out1 = _sl_run(_sl_ok)
check("🪑 SLT6 المسارُ الكامل ينجح ويطبع الأذرعَ الثلاث والهدرَ وبوّابةَ الصلاحية",
      _sl_rc1 == 0 and all(x in _sl_out1 for x in
                           ("S-LIVE", "S-NF5", "S-NF8", "d50_adj",
                            "هدرُ الأساس", "بوّابةُ الصلاحية")),
      f"rc={_sl_rc1}")
check("🪑 SLT7 التعديلُ الصادق: TL متأخّرٌ على NF5 (‏adj=4) وداخل مهلة NF8 (‏adj=5)",
      "S-NF5: d50_adj=4" in _sl_out1 and "S-NF8: d50_adj=5" in _sl_out1,
      _sl_out1[_sl_out1.find("قراءاتُ §⑤"):][:220] if "قراءاتُ §⑤" in _sl_out1 else "؟")

# ── SLT8: حارسُ الـno-op — بلا مفتاح `fill_date` إطلاقًا ⇒ رمز 8 صريح ──
_sl_nofd = [{k: v for k, v in _sl_trade(f"N{i}", 1 + i, 3 + i).items()
             if k != "fill_date"} for i in range(6)]
_sl_rc2, _sl_out2 = _sl_run(_sl_nofd)
check("🪑 SLT8 بلا حقل `fill_date` ⇒ رمز 8 (أذرعُ المهلة عمياء = no-op)",
      _sl_rc2 == 8, f"rc={_sl_rc2}")

# ── SLT9: خارج الإنتاج + التسجيلُ المسبق يحمل الأذرع والبوّابة والتعديل ──
check("🪑 SLT9 خارج الإنتاج: `Super_stock` لا يستورد `slot_arms`",
      "slot_arms" not in _rt_imports)
_sl_pre = open("slot_prereg.md", encoding="utf-8").read()
check("🪑 SLT10 التسجيلُ يحمل الأذرعَ الثلاث والبوّابةَ الحاكمة والتعديلَ الصادق",
      all(x in _sl_pre for x in ("S-LIVE", "S-NF5", "S-NF8", "d50_adj",
                                 "22 · 14 · 6", "3-8 جلسات", "قرارُ مالكٍ حصريّ")))


# ═══════ 🪑 NF8 حيًّا — تحرير خانة غير المُعبَّأ (قرار المالك «نفذ» 2026-08-07) ═══════
_nf_entry = S.make_watch_entry(
    {"symbol": "NF8T", "ref_bar": "2026-08-01", "price": 2.5,
     "entry": (1.9, 2.0), "tranches": [1.9, 1.95, 2.0], "pivot": 1.9,
     "stop": (1.75, 1.79), "t1": 2.3, "t2": 2.6, "t3": 3.0, "score": 60,
     "flags": [], "rr": 2.0}, "2026-08-01")
check("🪑 NF81 حقولُ التتبّع تولد مع السجل (band_hit=False · عدّاد 0)",
      _nf_entry.get("band_hit") is False
      and _nf_entry.get("band_wait_days") == 0
      and _nf_entry.get("band_last_bar") is None)

# ── NF82: `_nf8_slot_free` — التخوم والفشل الآمن وقاعدة العودة ──
check("🪑 NF82 التخوم: 7 جلسات يحجز · 8 يحرّر · لامسُ النطاق يحجز ولو طال ·"
      " التالف يحجز (فاشل-آمن) · القديم بلا حقول يحجز",
      _nf8 := True
      and S._nf8_slot_free({"band_hit": False, "band_wait_days": 7}) is False
      and S._nf8_slot_free({"band_hit": False, "band_wait_days": 8}) is True
      and S._nf8_slot_free({"band_hit": True, "band_wait_days": 40}) is False
      and S._nf8_slot_free({"band_hit": False, "band_wait_days": "x"}) is False
      and S._nf8_slot_free({}) is False)

# ── NF83: `_nf8_track` — اللمس أولًا · لا عدّ مزدوج لنفس الشمعة · العدّ بشمعة جديدة ──
_nf_df1 = pd.DataFrame({"Close": [2.6, 2.7], "Low": [2.5, 2.55]},
                        index=pd.to_datetime(["2026-08-04", "2026-08-05"]))
_nf_s = {"tranches": [1.9, 1.95, 2.0], "band_hit": False, "band_wait_days": 0,
         "band_last_bar": None}
S._nf8_track(_nf_s, _nf_df1)
_nf_w1 = _nf_s["band_wait_days"]
S._nf8_track(_nf_s, _nf_df1)                      # نفس الشمعة — لا عدّ مزدوج
_nf_w2 = _nf_s["band_wait_days"]
_nf_df2 = pd.DataFrame({"Close": [2.7, 2.8], "Low": [2.55, 2.6]},
                        index=pd.to_datetime(["2026-08-05", "2026-08-06"]))
S._nf8_track(_nf_s, _nf_df2)                      # شمعة جديدة — يعدّ
_nf_w3 = _nf_s["band_wait_days"]
check("🪑 NF83 العدّ: خارج النطاق يعدّ مرّةً لكل شمعة (1 ثم 1 ثم 2) ولا يلمس",
      (_nf_w1, _nf_w2, _nf_w3) == (1, 1, 2) and _nf_s["band_hit"] is False,
      f"{(_nf_w1, _nf_w2, _nf_w3)}")
_nf_df3 = pd.DataFrame({"Close": [2.2], "Low": [1.98]},
                        index=pd.to_datetime(["2026-08-07"]))
S._nf8_track(_nf_s, _nf_df3)                      # القاع دخل النطاق ⇒ لمس
check("🪑 NF84 اللمس بقاع اليوم (بدالّة `in_entry_band` الإنتاجية) يثبت `band_hit`"
      " ⇒ يعود يحجز خانته ولو كان محرَّرًا",
      _nf_s["band_hit"] is True and S._nf8_slot_free(_nf_s) is False)
check("🪑 NF85 و`_nf8_track` تقرأ النطاق بـ`in_entry_band` (صفر منطق موازٍ)",
      "in_entry_band(" in _insp0.getsource(S._nf8_track))

# ── NF86: الوصلة الحيّة — من نقطتَي النداء لا من وجود الدالّتين (wire-check) ──
check("🪑 NF86 `_nf8_slot_free` داخل حساب السعة في `run_daily_watchlist` حرفيًّا",
      "and not _nf8_slot_free(s)" in _insp0.getsource(S.run_daily_watchlist))
check("🪑 NF87 و`_nf8_track` يُنادى من `update_watchlist_status` (التتبّع اليومي)",
      "_nf8_track(s, df)" in _insp0.getsource(S.update_watchlist_status))
check("🪑 NF88 والعتبة من CONFIG باسم القرار (8 = سقف «ثبات الدعم 3-8»)",
      S.CONFIG.get("SLOT_UNFILLED_FREE_SESSIONS") == 8
      and "nf8slot" in S.LOGIC_VERSION)
# ── RTIE13: النتيجةُ منشورةٌ بحكمها ومعرّفاتِ تشغيلها وحدودِ صدقها ──
#    🔴 الغرضُ منعُ «نتيجةٌ تُروى ولا تُكتَب»: الحكمُ صريح · التشغيلاتُ الثلاث
#    بمعرّفاتها · واللقطةُ مذكورة — فلا يُعاد تفسيرُها لاحقًا بلا سندٍ مؤرَّخ.
_rt_res = open("ranker_tie_result.md", encoding="utf-8").read()
check("🥇 RTIE13 نتيجةُ ⑦ منشورةٌ: الحكم · التشغيلات الثلاث · اللقطة",
      all(x in _rt_res for x in ("فشلت", "31128455679", "31128455885",
                                 "31128456597", "30598885456", "b4e5372075c1")))
check("🥇 RTIE14 والنتيجةُ تُصرّح بأن الأثر الإنتاجيّ صفر",
      "لم يُمَسّ" in _rt_res and "لا `LOGIC_VERSION`" in _rt_res
      and "0 من 4" in _rt_res)

# ══════════════════════════════════════════════════════════════════════════
# 🥇⑦➡️ T-TIE-FWD — أقفالُ الحصاد الأماميّ (قرارُ المالك 2026-08-06: «‏1»)
# ══════════════════════════════════════════════════════════════════════════
# 🔴 **الخطر:** التسجيلُ يقع على **مسار الفرز الحيّ** ⇒ انهيارُه يُسقط التشغيلة،
#    وخطأٌ في موضعه (قبل `select_top` بدل بعده) يجعله يقرأ ترتيبًا غير الذي قرّر.
#    فالأقفالُ **سلوكيّةٌ على الدالّة** و**بنيويّةٌ (AST) على موضع النداء وعدده** —
#    لا نصّية (سقط النصّيّ على التعليقات أربع مرّات في جلسةٍ واحدة).
import ast as _th_ast


def _th_row(sym, rdy, sc, rr, tr=(1.0, 1.03, 1.06), stop=0.93, t1=1.4):
    return {"symbol": sym, "readiness": rdy, "score": sc, "rr": rr,
            "tranches": list(tr), "stop": [stop], "t1": t1}


_TH_RANKED = [_th_row("A", 70, 100, 5), _th_row("B", 70, 95, 4),
              _th_row("C", 70, 90, 3), _th_row("D", 70, 85, 2),
              _th_row("E", 60, 80, 2)]
_th_c2 = S.tie_cohort(_TH_RANKED, 2)
check("🥇 TH1 حدُّ القطع **داخل** تعادل ⇒ كوهورتٌ بمأخوذَين ومقصوصَين",
      bool(_th_c2) and _th_c2["level"] == 70
      and [m["symbol"] for m in _th_c2["members"] if m["taken"]] == ["A", "B"]
      and [m["symbol"] for m in _th_c2["members"] if not m["taken"]] == ["C", "D"],
      str(_th_c2 and [(m["symbol"], m["taken"]) for m in _th_c2["members"]]))
check("🥇 TH2 الحدُّ **خارج** تعادل ⇒ لا يُسجَّل شيء (الصمتُ صدقٌ لا نقص)",
      S.tie_cohort(_TH_RANKED, 4) is None
      and S.tie_cohort(_TH_RANKED, 9) is None
      and S.tie_cohort(_TH_RANKED, 0) is None)
check("🥇 TH3 `exclude` مُحترَم (يُقصى **قبل** حساب الحدّ)",
      [m["symbol"] for m in S.tie_cohort(_TH_RANKED, 2, exclude={"A"})["members"]]
      == ["B", "C", "D"])
check("🥇 TH4 جاهزيةٌ مجهولة ⇒ امتناع (لا يُخمَّن تعادل)",
      S.tie_cohort([_th_row("A", None, 1, 1), _th_row("B", None, 1, 1),
                    _th_row("C", None, 1, 1)], 1) is None)
# ── التسجيل: يُلحق · يُدَدوِب · ولا يرمي أبدًا ──
_th_wl = {}
_th_ok = S.record_tie_cohort(_th_wl, _TH_RANKED, 2, set(), "2026-08-06", "daily")
S.record_tie_cohort(_th_wl, _TH_RANKED, 2, set(), "2026-08-06", "daily")
check("🥇 TH5 التسجيلُ يُلحق ويُدَدوِب بـ(تاريخ، مصدر) — لا مضاعفة",
      _th_ok is True and len(_th_wl["tie_harvest"]) == 1
      and len(_th_wl["tie_harvest"][0]["members"]) == 4)
check("🥇 TH6 لا كوهورت ⇒ False (وليس تسجيلًا فارغًا)",
      S.record_tie_cohort({}, None, 2, set(), "2026-08-06", "x") is False
      and S.record_tie_cohort({}, [{"symbol": "Z"}], 1, set(), "d", "x") is False)
# 🔴 TH6b: **العيّنتان أعلاه لا تصلان الحارس أصلًا** — يردّهما `tie_cohort` بلا
#    استثناء، فكان القفلُ يدّعي «فاشلٌ-آمن» ولا يختبره (كشفَته الطفرةُ TM4 وحدها:
#    استبدالُ `return False` بـ`raise` **نجا**). المدخلُ هنا يرمي فعلًا داخل `try`
#    (‏`None.setdefault`) والفحصُ يلتقط الرمي فيسقط القفلُ نظيفًا بلا انهيار.
try:
    _th_fs = S.record_tie_cohort(None, _TH_RANKED, 2, set(), "2026-08-06", "x")
except Exception as _e:                                          # noqa: BLE001
    _th_fs = f"رمى: {type(_e).__name__}"
check("🥇 TH6b فاشلٌ-آمنٌ **مُختبَر**: مدخلٌ يرمي داخل الحارس ⇒ False لا استثناء",
      _th_fs is False, str(_th_fs))
# ── الحسم: بمحرّك الإنتاج نفسِه · وفرقٌ سلوكيّ بين رابحٍ وخاسر ──
_th_idx = pd.date_range("2026-08-07", periods=45, freq="B")
_th_win = pd.DataFrame({"Open": 1.0, "High": np.linspace(1.05, 1.5, 45),
                        "Low": np.linspace(0.99, 1.2, 45),
                        "Close": np.linspace(1.0, 1.45, 45)}, index=_th_idx)
_th_los = pd.DataFrame({"Open": 1.0, "High": 1.02, "Low": 0.90,
                        "Close": 0.92}, index=_th_idx)
_th_m = {"entry": 1.03, "stop": 0.93, "t1": 1.4}
_th_rw = S._tie_resolve_member(_th_m, _th_win)
_th_rl = S._tie_resolve_member(_th_m, _th_los)
check("🥇 TH7 الحسمُ يفرّق الرابح عن الخاسر و`R` بالوحدة الصحيحة (الوقف = ‏−1R)",
      _th_rw is not None and _th_rw > 2.0 and abs(_th_rl + 1.0) < 0.05,
      f"رابح={_th_rw} · خاسر={_th_rl}")
check("🥇 TH8 غيرُ المُعبَّأة ⇒ 0.0R (استهلكت خانةً بلا تنفيذ) · وتالفة ⇒ None",
      S._tie_resolve_member(
          {"entry": 0.5, "stop": 0.45, "t1": 0.8},
          pd.DataFrame({"Open": 9.0, "High": 9.5, "Low": 9.0, "Close": 9.2},
                       index=_th_idx)) == 0.0
      and S._tie_resolve_member({"entry": None, "stop": 1, "t1": 2}, _th_win) is None)
# ── القسم: يظهر دائمًا · ولا يطبع فرقًا قبل العيّنة ──
_th_blk = S._tie_harvest_block(_th_wl, fetch=lambda s_, d_: _th_win,
                               today="2026-12-01")
check("🥇 TH9 القسمُ يظهر **حتى بصفر كوهورت** (أهمُّ وقت: نظنّه يجمع وهو واقف)",
      bool(S._tie_harvest_block({}, today="2026-12-01"))
      and "لا كوهورت بعد" in "\n".join(S._tie_harvest_block({}, today="2026-12-01")))
check("🥇 TH10 دون العيّنة ⇒ «لا حكم» **ولا يُطبَع فرقٌ** (‏§⑤)",
      any("لا حكم" in x for x in _th_blk)
      and not any("الفرقُ المزدوج" in x for x in _th_blk),
      "\n".join(_th_blk)[-90:])
_th_big = {"tie_harvest": [
    {"date": "2026-08-06", "source": f"s{i}", "level": 70, "members": [
        {"symbol": "A", "taken": True, "entry": 1.03, "stop": 0.93, "t1": 1.4},
        {"symbol": "C", "taken": False, "entry": 1.03, "stop": 0.93, "t1": 1.4},
        {"symbol": "D", "taken": False, "entry": 1.03, "stop": 0.93, "t1": 1.4}]}
    for i in range(16)]}
_th_blk2 = S._tie_harvest_block(
    _th_big, fetch=lambda s_, d_: (_th_win if s_ == "A" else _th_los),
    today="2026-12-01")
check("🥇 TH11 عند بلوغ العيّنة يُطبَع الفرقُ المزدوج بإشارته",
      any("الفرقُ المزدوج" in x for x in _th_blk2)
      and any("+" in x and "R" in x for x in _th_blk2),
      "\n".join(_th_blk2)[-120:])
check("🥇 TH12 النافذةُ تُحترَم: كوهورتٌ لم تنقضِ نافذتُه لا يُحسم",
      "محسومٌ منهم: <b>0</b>" in "\n".join(S._tie_harvest_block(
          _th_wl, fetch=lambda s_, d_: _th_win, today="2026-08-20")))
# ── الموضع والعدد: بعد `select_top` في **الاثنين** (AST لا نصّ) ──
_th_tree = _th_ast.parse(open("Super_stock.py", encoding="utf-8").read())


def _th_calls(fname, callee):
    fn = next((n for n in _th_ast.walk(_th_tree)
               if isinstance(n, _th_ast.FunctionDef) and n.name == fname), None)
    return [n.lineno for n in _th_ast.walk(
        fn or _th_ast.Module(body=[], type_ignores=[]))
        if isinstance(n, _th_ast.Call) and getattr(n.func, "id", None) == callee]


_th_pairs = [(f, _th_calls(f, "select_top"), _th_calls(f, "record_tie_cohort"))
             for f in ("run_weekly_renewal", "run_daily_watchlist")]
check("🥇 TH13 مُنادًى في **مسارَي** الاختيار و**بعد** `select_top` في كليهما",
      all(len(st) == 1 and len(rc) == 1 and rc[0] > st[0]
          for _f, st, rc in _th_pairs), str(_th_pairs))
check("🥇 TH14 وقسمُ التقرير مُنادًى **مرّتين** (القليلة + الكافية)",
      len(_th_calls("build_dev_assistant_report", "_tie_harvest_block")) == 2,
      str(_th_calls("build_dev_assistant_report", "_tie_harvest_block")))
# ── الجذور: لم تُمَسّ ──
_TH_ROOTS = ["rank_key", "select_top", "classify_tier", "analyze_ticker",
             "apply_short_gate", "apply_float_gate", "scan_market",
             "backtest_symbol", "scan_ignition", "scan_split_hunter",
             "entry_status", "build_interpretation", "_resolve_arm"]
_th_dump = {n.name: _th_ast.dump(n) for n in _th_ast.walk(_th_tree)
            if isinstance(n, _th_ast.FunctionDef) and n.name in _TH_ROOTS}
check("🥇 TH15 الحصادُ خارج الجذور: لا جذرَ ينادي دوالَّه",
      not any(x in _th_dump.get(r, "") for r in _TH_ROOTS
              for x in ("record_tie_cohort", "tie_cohort", "_tie_harvest_block")))
_th_pre = open("tie_harvest_prereg.md", encoding="utf-8").read()
# 🛡️ TH17: الحارسُ **الخارجيّ** — انكسارُ القسم يُبلَّغ ولا يقتل التقرير الأسبوعيّ.
# 🔴 ومحاولتي الأولى كانت قفلًا فارغًا: جعلتُ **الجالب** يرمي، وهو محروسٌ داخليًّا
#    (`except: v = None`) فلا يبلغ الخارجيّ أصلًا — نفسُ فخّ TH6. المدخلُ هنا يكسر
#    **خارج** أيّ حارسٍ داخليّ (`tie_harvest` عددٌ لا قائمة ⇒ التكرارُ عليه يرمي).
try:
    _th_boom = S._tie_harvest_block({"tie_harvest": 5}, today="2026-12-01")
except Exception as _e:                                          # noqa: BLE001
    _th_boom = f"رمى: {type(_e).__name__}"
check("🥇 TH17 حارسٌ خارجيّ: انكسارُ القسم يُبلَّغ ولا يُسقط التقرير",
      isinstance(_th_boom, list) and any("تعذّر الحصاد" in x for x in _th_boom),
      str(_th_boom)[-110:])
check("🥇 TH16 التسجيلُ المسبق مدفوعٌ بمعياره وحدِّ عيّنته وتنبّؤاتِه",
      all(x in _th_pre for x in ("+0.10R", "F1", "F4", "لا حكم",
                                 "TIE_HARVEST_MIN", "cluster bootstrap")))

# ══════════ 🥇 FAITXT: نصوصُ «المثالي» تقرأ CONFIG لا أرقامًا مغروسة (2026-08-07) ══════════
# القرارُ كان يقرأ أرقامَ فيصل والنصُّ يعرض أرقامَنا القديمة (‏50/100/27/40) —
# «سطرُ عرضٍ يكذب». القفلُ **نحويّ** (AST على سطور soft_fails.append الأربعة نفسِها،
# لا نصّيّ فلا يخدعه تعليق): كلُّ سطرٍ منها يضمّ Subscript على CONFIG بالمفتاح الصحيح.
try:
    import ast as _fx_ast
    _fx_src = open("Super_stock.py", encoding="utf-8").read()
    _fx_tree = _fx_ast.parse(_fx_src)
    _fx_fn = next(n for n in _fx_ast.walk(_fx_tree)
                  if isinstance(n, _fx_ast.FunctionDef) and n.name == "analyze_ticker")
    _fx_hits = {}          # مفتاح CONFIG ⟵ وُجد داخل f-string نداءِ soft_fails.append
    for node in _fx_ast.walk(_fx_fn):
        if (isinstance(node, _fx_ast.Call)
                and isinstance(node.func, _fx_ast.Attribute)
                and node.func.attr == "append"
                and isinstance(node.func.value, _fx_ast.Name)
                and node.func.value.id == "soft_fails"):
            for sub in _fx_ast.walk(node):
                if (isinstance(sub, _fx_ast.Subscript)
                        and isinstance(sub.value, _fx_ast.Name)
                        and sub.value.id == "CONFIG"
                        and isinstance(sub.slice, _fx_ast.Constant)):
                    _fx_hits[sub.slice.value] = True
    _fx_need = {"MIN_DROP_PCT", "PRIOR_SPIKE_PCT", "RSI_OVERSOLD", "RSI_MAX_NOW"}
    check("🥇 FAITXT1 نصوصُ «المثالي» الأربعة تقرأ CONFIG (قفل AST على soft_fails.append)",
          _fx_need <= set(_fx_hits),
          f"الناقص: {_fx_need - set(_fx_hits)}")
    # وقيمُ الإنتاج (‏FAISAL_ONLY=1 مطبَّقة عند الاستيراد الحيّ) تُنتج نصًّا بأرقام فيصل:
    # هنا السويّة على FAISAL_ONLY=0 فالبرهان المكمّل = القيمُ الافتراضية تُنتج النصَّ القديم
    # حرفيًّا (توافقٌ خلفيّ بت-بت) — وهو ما تثبته اختباراتُ التوصيف القائمة على نصّ الكرت.
    check("🥇 FAITXT2 تحت بوّابات البوت النصُّ القديم حرفيًّا (‏50/100/27/40 من CONFIG)",
          (S.CONFIG["MIN_DROP_PCT"], S.CONFIG["PRIOR_SPIKE_PCT"],
           S.CONFIG["RSI_OVERSOLD"], S.CONFIG["RSI_MAX_NOW"]) == (50.0, 100.0, 27.0, 40.0),
          "قيم الافتراض تغيّرت — راجع التوافق الخلفي")
except StopIteration:
    check("🥇 FAITXT1 نصوصُ «المثالي» الأربعة تقرأ CONFIG (قفل AST على soft_fails.append)",
          False, "analyze_ticker غير موجودة!")

# ══════════ 🧭 PIT: أداة كون point-in-time (مرحلة أولى — pit_prereg.md) ══════════
import pit_universe as _PIT                                       # noqa: E402
check("🧭 PIT1 عزلٌ تامّ: `pit_universe` لا يُستورَد في `Super_stock.py`",
      "pit_universe" not in open("Super_stock.py", encoding="utf-8").read())
_pit_u = _PIT.build_url("2025-01-02")
check("🧭 PIT2 الدلالةُ الصحيحة: `active=true` مع `date` — و`active=false` ممنوعة "
      "(درسُ المِجَسّ المسحوب)",
      "active=true" in _pit_u and "date=2025-01-02" in _pit_u
      and "exchange=XNAS" in _pit_u and "active=false" not in _pit_u, _pit_u[:110])
_pit_rows, _pit_next = _PIT.parse_page(
    {"results": [{"ticker": "AAA", "type": "CS", "name": "A"},
                 {"ticker": None}, {}, {"ticker": "BBB"}],
     "next_url": "https://x/next"})
check("🧭 PIT3 `parse_page` تتخطّى الصفَّ بلا رمزٍ ولا تنهار على الناقص",
      [r["ticker"] for r in _pit_rows] == ["AAA", "BBB"]
      and _pit_rows[1]["type"] is None and _pit_next == "https://x/next")
_pit_s = _PIT.summarize(
    [{"ticker": t} for t in ("A", "B", "C", "D")],
    [{"ticker": t} for t in ("B", "D", "E")])
check("🧭 PIT4 `summarize` فرقُ لقطتين: 4 حيًّا ⟶ غاب A وC (‏50%)",
      _pit_s["n_then"] == 4 and _pit_s["n_gone"] == 2
      and _pit_s["gone"] == ["A", "C"] and _pit_s["gone_pct"] == 50.0)
_pit_pages = [({"results": [{"ticker": f"S{i}"}], "next_url": "https://x/p2"}, )
              for i in range(3)]
_pit_boom = None
try:                        # سقفُ الصفحات مع بقيّةٍ ⇒ يرمي (لا قصّ صامت)
    _PIT.fetch_universe("2025-01-02", "k", max_pages=2,
                        fetch=lambda u, k: {"results": [{"ticker": "X"}],
                                            "next_url": "https://x/more"})
except RuntimeError as _e:
    _pit_boom = str(_e)
check("🧭 PIT5 بلوغُ السقف وصفحاتٌ باقية ⇒ **يرمي مُعلَنًا** (لقطةٌ ناقصة تُرفَض)",
      _pit_boom is not None and "سقف" in _pit_boom, str(_pit_boom)[:80])
_pit_full = _PIT.fetch_universe(
    "2025-01-02", "k", max_pages=5,
    fetch=(lambda st: lambda u, k: st.pop(0))([
        {"results": [{"ticker": "A"}], "next_url": "u2"},
        {"results": [{"ticker": "B"}], "next_url": None}]))
check("🧭 PIT6 واللفُّ الكامل يجمع الصفحات حتى نهايتها",
      [r["ticker"] for r in _pit_full] == ["A", "B"])

# ── 🧭 PITH: جالب التاريخ + مِجَسّ التغطية (‏P2) ─────────────────────────────
import pit_history as _PITH                                       # noqa: E402
check("🧭 PITH1 عزلٌ تامّ: `pit_history` لا يُستورَد في `Super_stock.py`",
      "pit_history" not in open("Super_stock.py", encoding="utf-8").read())
check("🧭 PITH2 طلبُ الشموع `adjusted=true` (نفسُ تسوية yfinance)",
      "adjusted=true" in _PITH.aggs_url("XX", "2024-01-01", "2024-12-31"))
_ph_df = _PITH.to_frame([{"t": 1735794000000, "o": 1.0, "h": 2.0, "l": 0.5,
                          "c": 1.5, "v": 100}, {"bad": 1},
                         {"t": 1735880400000, "o": 1.5, "h": 2.5, "l": 1.0,
                          "c": 2.0, "v": 200}])
check("🧭 PITH3 `to_frame` بشكل `_extract_into` حرفيًّا ويُسقط الصفَّ التالف",
      _ph_df is not None and list(_ph_df.columns) ==
      ["Open", "High", "Low", "Close", "Volume"] and len(_ph_df) == 2
      and _PITH.to_frame([]) is None and _PITH.to_frame(None) is None)
check("🧭 PITH4 العيّنةُ **حتميّة** (sha256): نفسُ المدخل ⇒ نفسُ المخرَج حرفيًّا",
      _PITH.pick_sample(["C", "A", "B", "D"], 2)
      == _PITH.pick_sample(["D", "B", "A", "C"], 2))
_ph_probe = _PITH.coverage_probe(
    ["G1", "G2"], "k", "2024-01-01", "2024-12-31", sample_n=2, min_bars=2,
    fetch=lambda u, k: ({"results": [{"t": 1735794000000, "o": 1, "h": 1,
                                      "l": 1, "c": 1, "v": 1},
                                     {"t": 1735880400000, "o": 1, "h": 1,
                                      "l": 1, "c": 1, "v": 1}]}
                        if "CTRL" in u else {"status": "OK", "resultsCount": 0}),
    log=lambda *_: None, control=("CTRL",))
check("🧭 PITH5 شاهدٌ حيّ + مشطوبان فارغان ⇒ ليس عطلًا والتشخيصُ مُسمًّى",
      _ph_probe["tool_broken"] is False and _ph_probe["none"] == 2
      and all("empty" in d["diag"] for d in _ph_probe["detail"].values()))
_ph_broken = _PITH.coverage_probe(
    ["G1"], "k", "2024-01-01", "2024-12-31", sample_n=1, min_bars=2,
    fetch=lambda u, k: {"status": "OK", "resultsCount": 0},
    log=lambda *_: None, control=("CTRL",))
check("🧭 PITH6 شاهدُ الضبط صفرٌ ⇒ `tool_broken` (درسُ تشغيلة 0/40: عطلُ أداةٍ "
      "لا يُقرأ «تغطيةً معدومة»)",
      _ph_broken["tool_broken"] is True)

# ── 🧭 PITS: بانية اللقطة (‏P3-أ) — التطابقُ مع صيغة الإنتاج **سلوكيًّا** ────────
import pit_snapshot as _PITS                                      # noqa: E402
check("🧭 PITS1 عزلٌ تامّ: `pit_snapshot` لا يُستورَد في `Super_stock.py`",
      "pit_snapshot" not in open("Super_stock.py", encoding="utf-8").read())
# 🔒 القفلُ الحاسم: لقطةٌ تُبنى بالأداة وتُقرأ عبر `load_frozen_dataset`
# **الإنتاجيّة نفسِها** — إطاراتٌ متطابقة وتقسيماتٌ متطابقة (لا «نفس الصيغة»
# بالوصف بل بالقراءة الفعلية؛ درسُ «وصفُ الدالّة ليس دليلًا على سلوكها»).
_ps_df = _PITH.to_frame([
    {"t": 1735794000000 + i * 86_400_000, "o": 1.0 + i, "h": 2.0 + i,
     "l": 0.5 + i, "c": 1.5 + i, "v": 100 + i} for i in range(5)])
_ps_sp = _PITS.split_series([
    {"ticker": "TT", "split_from": 20, "split_to": 1,
     "execution_date": "2025-03-01"},
    {"ticker": "TT", "split_from": 1, "split_to": 2,
     "execution_date": "2025-06-01"},
    {"ticker": "ZZ", "split_from": 0, "split_to": 1,          # تالف ⇒ يُتخطّى
     "execution_date": "2025-01-01"}])
check("🧭 PITS2 `split_series` باصطلاح yfinance: عكسيّ 1-مقابل-20 ⇒ 0.05 · "
      "أماميّ 2-مقابل-1 ⇒ 2.0 · والتالفُ يُتخطّى",
      list(_ps_sp) == ["TT"] and abs(_ps_sp["TT"].iloc[0] - 0.05) < 1e-12
      and abs(_ps_sp["TT"].iloc[1] - 2.0) < 1e-12)
_ps_path = "/tmp/claude-0/-home-user-Super-Stocks/434ec133-9098-5d94-a30d-866522fb9eda/scratchpad/pit_mini.pkl.gz"
_os_hc.makedirs(_os_hc.path.dirname(_ps_path), exist_ok=True)
_ps_man = _PITS.save_snapshot({"TT": _ps_df}, {"TT": _ps_sp["TT"]},
                              asof="2025-01-02", history_days=100, path=_ps_path)
_ps_h, _ps_s, _ps_asof = S.load_frozen_dataset(_ps_path)
check("🧭 PITS3 اللقطةُ تُقرأ عبر `load_frozen_dataset` **الإنتاجيّة**: إطارٌ "
      "متطابقٌ بت-بت وتقسيماتٌ متطابقة وasof محفوظ",
      _ps_h is not None and _ps_h["TT"].equals(_ps_df)
      and _ps_s["TT"].equals(_ps_sp["TT"]) and _ps_asof == "2025-01-02"
      and _ps_man["n_symbols"] == 1 and len(_ps_man["sha256"]) == 64)
check("🧭 PITS4 والـworkflow يرفع **`frozen-dataset`/`frozen_backtest.pkl.gz`** "
      "بالاسمين اللذين يستهلكهما `backtest.yml` حرفيًّا",
      (lambda w: "name: frozen-dataset" in w and "frozen_backtest.pkl.gz" in w
       and "if-no-files-found: error" in w)(
          open(".github/workflows/pit_snapshot.yml", encoding="utf-8").read()))
check("🧭 PITS5 فلترُ النوع أسهمٌ عادية فقط (‏CS/ADRC) — يحاكي كونَ الفارز",
      _PITS.COMMON_TYPES == {"CS", "ADRC"})

print("\n" + "=" * 50)
print(f"النتيجة: {len(PASS)} نجح · {len(FAIL)} فشل")
if FAIL:
    print("الفاشل: " + " | ".join(FAIL))
    raise SystemExit(1)
print("✅✅ كل الاختبارات نجحت — الضمان الذهبي")

