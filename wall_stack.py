"""🧱 مكدّس الجدران — يكشف **كل** البوّابات التي تحجب اليوم، لا الأولى فقط.

المشكلة التي يحلّها (‏`gates_result.md` §⑨-8 و`OPUS_EXECUTION_PACKAGE.md` ④-أ-5):
`analyze_ticker` سلسلة **AND** تقطع عند **أوّل** بوّابة ساقطة (`return _reject`)، فتوزيع
أسباب الرفض يعدّ **الجدار الأول حصرًا**. ⇒ لا نعرف — ولا مرّة في تاريخ المشروع — كم يومًا
**بوّابةٌ واحدة فقط** تحجبه. وهذا بالضبط ما يجعل «افتحْ M5 فيدخل السهم» **شرطًا لازمًا لا
كافيًا**: قد يسقط خلفها على جدارٍ لم يُقَس قطّ.

🔑 **الطريقة — «تقشير البصلة» بدل إعادة كتابة البوّابات:**
لا نُعيد تنفيذ منطق البوّابات (وهو ذنبٌ موثّق: منطقان يتفرّقان فيكذب التشخيص). بل:

    ننادي `analyze_ticker` **الإنتاجيّ نفسه** → يرجع سبب الرفض الأول
    → نُرخي **ذلك السبب وحده** في CONFIG → نُعيد النداء → السبب التالي … حتى يمرّ.

فالحكم في كل خطوة من **دالّة الإنتاج حرفيًّا**، وصفر منطقٍ مكرّر ⇒ صفر خطر تفرّق.

**المُخرَج لكل يوم:** قائمةٌ **مرتَّبة** بكل الجدران (`["M4_base_واسعة", "M5_سيولة", …]`)
‏+ هل مرّ في النهاية. **والمقياس الحاسم:** `sole_blocker` = أيام حجبتها **بوّابة واحدة**.

🔒 **التصنيف:** تشخيص/بحث — **لا يُستورَد في أي مسار إنتاج**، ولا يعدّل `analyze_ticker`،
ويعيد CONFIG لحالته في `finally` مهما حصل.

⚠️ **حدّ صدقٍ بنيويّ يُعلَن مع كل نتيجة:** الإرخاء يجعل الدالّة تمضي أبعد، **وقد تتولّد
بذلك نواقصُ أو حساباتٌ لم تكن تُحسب أصلًا** — فالجدران التالية تُقرأ «ما كان سيحجبه **لو**
فُتح السابق»، لا «ما كان يحجبه فعلًا بالتوازي». وهذا **هو المطلوب بالضبط** لسؤالنا
(«ماذا يدخل لو فتحتُ M5؟») لكنه ليس «تقييمًا متوازيًا للأربع عشرة».
"""
from __future__ import annotations

import re

# ── خريطة: سبب الرفض ⟶ (مفتاح CONFIG، القيمة المتساهلة) ──────────────────────
# كل مفتاحٍ هنا **موجودٌ في CONFIG** ومُتحقَّقٌ منه باختبار (لا أسماء مخترَعة).
RELAX = {
    "M1_سعر":              ("MIN_PRICE",           0.0),
    "M2_هبوط_فوق_97":      ("MAX_DROP_PCT",        100.0),
    "M2_هبوط_تحت_40":      ("MIN_DROP_FLOOR",      0.0),
    "M3_انفجار_تحت_60":    ("PRIOR_SPIKE_FLOOR",   0.0),
    "M4_base_واسعة":       ("BASE_RANGE_MAX_PCT",  1e9),
    "M5_سيولة":            ("MIN_DOLLAR_VOL",      0.0),
    "M10_RSI_ما_تشبّع":     ("RSI_OS_HARD",         100.0),
    "M10_RSI_فات_القطار":  ("RSI_NOW_HARD",        100.0),
}
# أسبابٌ نصُّها متغيّر (يحمل رقمًا) ⇒ تُطابَق ببادئة:
RELAX_PREFIX = [
    ("نواقص_فوق_",      "WATCH_MAX_FAILS", 99),
    ("بعيد_عن_الدخول",  "NEAR_PCT",        0.0),
    ("نقاط_تحت_",       "SCORE_MIN",       0.0),
]

# جدرانٌ **بنيوية بلا مفتاح CONFIG** — لا تُرخى، فيتوقّف التقشير عندها ويُعلَن ذلك
# صراحةً بدل ابتلاعه (‏`M2_hi52` بيانات ناقصة · `M4_base_lo` قاعدة منعدمة ·
# `M4_انفجر_فعلاً` فات القطار · `RR+نواقص_فوق_الحد` مركّب).
TERMINAL = {"M2_hi52", "M4_base_lo", "M4_انفجر_فعلاً", "RR+نواقص_فوق_الحد"}

MAX_PEEL = 16          # سقف أمان: أكثر من عدد البوّابات، فلا حلقة لا نهائية


def _relax_for(reason):
    """يرجّع (مفتاح CONFIG، القيمة المتساهلة) للسبب، أو None لو غير قابل للإرخاء."""
    if reason in RELAX:
        return RELAX[reason]
    for pref, key, val in RELAX_PREFIX:
        if reason.startswith(pref):
            return (key, val)
    return None


def peel_walls(S, sym, df, max_peel=MAX_PEEL):
    """🧱 يقشّر جدران يومٍ واحد بنداء `analyze_ticker` الإنتاجيّ مرارًا.

    يرجّع dict:
      walls    : قائمة مرتَّبة بأسماء الجدران (الأول أولًا)
      passed   : هل مرّ بعد إرخاء كل ما أُرخي
      terminal : اسم الجدار البنيويّ الذي أوقف التقشير (أو None)
      n_walls  : len(walls)

    🔒 CONFIG يُستعاد كاملًا في `finally` — حتى لو رمى `analyze_ticker`.
    """
    saved = {}
    walls, terminal, passed = [], None, False
    try:
        for _ in range(max_peel):
            try:
                r = S.analyze_ticker(sym, df)
            except Exception:
                # فشل تحليلٍ لسببٍ آخر (بيانات) — يُعلَن ولا يُخمَّن
                terminal = "استثناء_تحليل"
                break
            if r:
                passed = True
                break
            reason = S._REJECT_REASONS.get(sym)
            if not reason:
                terminal = "بلا_سبب_مسجَّل"
                break
            walls.append(reason)
            if reason in TERMINAL:
                terminal = reason
                break
            relax = _relax_for(reason)
            if relax is None:
                terminal = reason          # سببٌ جديد لا خريطة له — يُعلَن لا يُبتلَع
                break
            key, val = relax
            if key not in saved:
                saved[key] = S.CONFIG.get(key)
            S.CONFIG[key] = val
        else:
            terminal = "تجاوز_سقف_التقشير"
    finally:
        for k, v in saved.items():
            S.CONFIG[k] = v
    return {"walls": walls, "passed": passed, "terminal": terminal,
            "n_walls": len(walls)}


def _base_name(reason):
    """يوحّد الأسباب المتغيّرة نصًّا («بعيد_عن_الدخول(35%)» ⟶ «بعيد_عن_الدخول»)
    حتى لا تتفتّت بالتجميع — نفس علّة P1 الموثّقة."""
    r = re.sub(r"\(.*?\)", "", reason)
    for pref, _k, _v in RELAX_PREFIX:
        if r.startswith(pref):
            return pref.rstrip("_")
    return r


def aggregate(rows):
    """🧮 يجمّع نتائج `peel_walls` لعدّة أيام ⟶ الأرقام الثلاثة التي تهمّ.

    - `total_blocks`  : كم يومًا تظهر فيه البوّابة **في أي موضع** (الكُلفة الحقيقية،
                        لا «الأول فقط» الذي يطبعه الفارز).
    - `sole_blocker`  : كم يومًا تكون فيه **الجدار الوحيد** ⇒ **الأثر الحديّ لفتحها**.
    - `first_blocks`  : الجدار الأول (لمقارنة مباشرة بتوزيع الفارز — فحصُ اتّساق).
    """
    total, sole, first, hist = {}, {}, {}, {}
    passed = 0
    for r in rows:
        w = r.get("walls") or []
        if r.get("passed"):
            passed += 1
        hist[len(w)] = hist.get(len(w), 0) + 1
        if w:
            first[_base_name(w[0])] = first.get(_base_name(w[0]), 0) + 1
        for name in {_base_name(x) for x in w}:
            total[name] = total.get(name, 0) + 1
        if len(w) == 1:
            n = _base_name(w[0])
            sole[n] = sole.get(n, 0) + 1
    return {"n": len(rows), "passed_after_relax": passed, "walls_hist": hist,
            "total_blocks": total, "sole_blocker": sole, "first_blocks": first}


def format_report(agg):
    """تقريرٌ نصّيّ عربيّ — أسطر جاهزة للسجلّ."""
    out = []
    n = agg["n"]
    out.append(f"🧱 مكدّس الجدران: {n} يومًا مرفوضًا · مرّ بعد الإرخاء الكامل "
               f"{agg['passed_after_relax']}")
    hist = agg["walls_hist"]
    if hist:
        parts = " · ".join(f"{k} جدار={v}" for k, v in sorted(hist.items()))
        out.append(f"   توزيع عدد الجدران: {parts}")
    for title, key in (("الكُلفة الحقيقية (بأي موضع)", "total_blocks"),
                       ("الجدار الأول (كما يطبعه الفارز)", "first_blocks"),
                       ("🔑 الجدار الوحيد (الأثر الحديّ للفتح)", "sole_blocker")):
        d = agg.get(key) or {}
        if not d:
            out.append(f"   {title}: — لا شيء")
            continue
        items = sorted(d.items(), key=lambda kv: -kv[1])
        body = " · ".join(f"{k}={v}" for k, v in items)
        out.append(f"   {title}: {body}")
    return out
