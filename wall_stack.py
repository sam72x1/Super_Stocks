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
    # 🧱🕯️ `T-STABILITY` (‏`stability_prereg.md`) — بوّابتا الثبات: **علمٌ نصّيّ
    #    مطفأٌ في الإنتاج** (`""`) ⇒ لا تظهران في توزيع الرفض الحيّ أصلًا، لكنهما
    #    تظهران في أذرع الباكتيست ⇒ تُرخيان بإطفاء العلم نفسِه (لا بتحريك الأرضية
    #    3 — فهي **نصُّ فيصل** ولا تُرخى). مقفولٌ `ST4`.
    "M_ثبات_تحت_الأرضية":   ("BT_STABILITY_GATE",   ""),
    "M_ثبات_لم_يكتمل":      ("BT_STABILITY_GATE",   ""),
    # 🎯📌 `T-ANCHOR` (2026-08-13، `anchor_prereg.md`): ذراعُ `tested_strict`
    #    ترفض حين لا مستوًى مُختبَر — **علمٌ مطفأٌ في الإنتاج** (`""`) فلا يظهر
    #    السببُ في توزيع الرفض الحيّ أصلًا، ويُرخى بإطفاء العلم نفسِه (لا بتحريك
    #    أرقام `tested_level` — تلك نصُّ فيصل ولا تُعاير هنا). مقفولٌ `AN6`.
    "M_لا_مستوى_مختبر":     ("BT_ANCHOR",           ""),
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
TERMINAL = {"M2_hi52", "M4_base_lo", "M4_انفجر_فعلاً", "RR+نواقص_فوق_الحد",
            # 🚪 «اقفل الباب» (2026-08-11): شرطُ **اتجاه** بلا عتبةٍ في CONFIG فلا
            # يُرخى — وهو **حصريُّ مسار الارتداد** (`pullback=True`) فلا يظهر أصلًا
            # في تقشير هذي الأداة (تمشي بمسار الفرز العاديّ).
            "M4_base_واسعة_هبوطًا"}

MAX_PEEL = 16          # سقف أمان: أكثر من عدد البوّابات، فلا حلقة لا نهائية

# ── 📒 وسم مصدر كل جدار — من `FAISAL_SOURCE_LEDGER.md` (سؤال المالك 2026-07-31:
#     «هل المشكلة في إضافاتنا والفلسفة الزائدة؟») ──────────────────────────────
# 🔴 **الأوسمة منقولةٌ من الدفتر لا مخترَعة هنا**، ومقفولةٌ باختبارٍ يقارنها به.
#     `engineering` = رقمٌ من عندنا · `inferred` = استنتاجنا من كلامه ·
#     `verbatim` = قاله فيصل بلفظه (‏ولا واحدة منها في M1-M5 — نتيجة الدفتر).
#
# 🔴🔴 **تصحيحٌ مؤرَّخ 2026-08-12 — هذي الخريطةُ تصف «مَن صاغ البوّابة» لا «مَن
#     صاغ رقمَها»، والأرقامُ في التعليقات أدناه كانت **بائتةً** (ما قبل الظرف):**
#     بعد «معايير فيصل وحدها» صارت العتباتُ النافذة **من كاتالوج فيصل** (‏`MIN_PRICE`
#     0.40 · `MIN_DROP_FLOOR` 71.72 · `PRIOR_SPIKE_FLOOR` 78.27 · `MIN_DOLLAR_VOL`
#     14,314 · `SCORE_MIN` 5 · `NEAR_PCT` 0 · `WATCH_MAX_FAILS` 8 · `RSI` 69/71.1 …)
#     ⇒ **سطرُ «‏100% engineering» كان يُقرأ «الجدرانُ كلُّها من عندنا» وهو مُضلِّل.**
#     ولذلك أُضيف بُعدٌ ثانٍ **يُحسَب من القيمة النافذة** (`threshold_source`) ويُطبَع
#     معه، فيُقرأ البُعدان معًا: **البوّابةُ من عندنا · ورقمُها من كاتالوجه.**
WALL_SOURCE = {
    "M1_سعر":              "engineering",   # MIN_PRICE=1.5
    "M2_هبوط_فوق_97":      "engineering",   # MAX_DROP_PCT=97
    "M2_هبوط_تحت_40":      "engineering",   # MIN_DROP_FLOOR=40
    "M3_انفجار_تحت_60":    "engineering",   # PRIOR_SPIKE_FLOOR=60
    "M4_base_واسعة":       "engineering",   # BASE_RANGE_MAX_PCT=40  ← حاجب SPRC
    "M5_سيولة":            "engineering",   # MIN_DOLLAR_VOL=200K (له شاهد حماية C3)
    "M4_انفجر_فعلاً":       "inferred",      # RECENT_RISE_BLOCK_PCT=35
    "M10_RSI_ما_تشبّع":     "verbatim",      # RSI 23-27 (TG_2043)
    "M10_RSI_فات_القطار":  "verbatim",      # RSI≤40 (TG_2043)
    "نواقص_فوق":           "engineering",   # WATCH_MAX_FAILS=3
    "بعيد_عن_الدخول":      "engineering",   # NEAR_PCT=50
    "نقاط_تحت":            "engineering",   # SCORE_MIN=45
    "RR+نواقص_فوق_الحد":   "engineering",   # MIN_RR_T1
    "M2_hi52":             "بنيويّ",         # بيانات ناقصة لا عتبة
    "M4_base_lo":          "بنيويّ",
    "M4_base_واسعة_هبوطًا": "بنيويّ",         # اتجاهٌ لا عتبة (مسارُ الارتداد وحده)
    # 🧱🕯️ `T-STABILITY`: الأرضيةُ 3 جلسات **نصُّ فيصل** (`IMG_0151` «حافظ ع قاعه
    #    لمدة 3 جلسات» — وسمُ الدفتر `faisal_verbatim`) ⇒ الوسمُ `verbatim`.
    #    والسقفُ 8 `engineering` **ولا يُنفَّذ إطلاقًا** (ST5) فلا جدارَ له.
    "M_ثبات_تحت_الأرضية":   "verbatim",      # STABILITY_MIN=3 (IMG_0151)
    "M_ثبات_لم_يكتمل":      "verbatim",      # held + STABILITY_MIN (نصُّه كاملًا)
    # المستوى المُختبَر «‏1.75 ضربها مرّتين ولا كسرها» (‏IMG_0451) ⇒ `verbatim`.
    "M_لا_مستوى_مختبر":     "verbatim",
}


def wall_source(reason):
    """وسمُ مصدر **البوّابة** (من الدفتر)، أو «غير موسوم» — ولا يُخمَّن."""
    return WALL_SOURCE.get(_base_name(reason), "غير_موسوم")


def _config_key(reason):
    """مفتاحُ `CONFIG` الذي يحكم هذا الجدار — من `RELAX`/`RELAX_PREFIX` **نفسِهما**
    (مصدرٌ واحد: خريطةُ الإرخاء هي خريطةُ العتبات) أو `None` للبنيويّ."""
    base = _base_name(reason)
    if base in RELAX:
        return RELAX[base][0]
    for pref, key, _ in RELAX_PREFIX:
        if str(reason).startswith(pref) or base.startswith(pref.rstrip("_")):
            return key
    return None


def threshold_source(reason, cfg=None, applied=None, owner=None):
    """📒 مصدرُ **رقمِ** الجدار من **القيمة النافذة** لا من جدولٍ مكتوب:
    `faisal_envelope` (‏من ظرف الكاتالوج) · `owner` (قرارُ مالكٍ يعلو الظرف) ·
    `engineering` (رقمُنا) · `بنيويّ` (بلا مفتاح عتبة).

    🔴 **ولماذا يُحسَب لا يُكتَب:** جدولٌ مكتوبٌ **يتعفّن** — وهو بعينه ما وقع في
    تعليقات `WALL_SOURCE` أعلاه (أرقامُ ما قبل الظرف). فيُقرأ من الإحلال الفعليّ."""
    import Super_stock as _S                                     # noqa: PLC0415
    cfg = _S.CONFIG if cfg is None else cfg
    key = _config_key(reason)
    if key is None:
        return "بنيويّ"
    if owner is None:
        owner = getattr(_S, "OWNER_GATE_OVERRIDES", {}) or {}
    if key in owner:
        return "owner"
    if not int(cfg.get("FAISAL_ONLY", 0)):
        return "engineering"          # وضعُ بوّابات البوت ⇒ الرقمُ رقمُنا
    if applied is None:
        try:
            import envelope_scan as _E                           # noqa: PLC0415
            applied = _S.faisal_only_overrides(_E.load_edges(_E.EDGES_FILE))
        except Exception:                                          # noqa: BLE001
            return "غير_محسوم"       # يُعلَن ولا يُخمَّن
    return "faisal_envelope" if key in applied else "engineering"


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
    # 📒 التجميع بالمصدر: كم يومًا **جدارُه الأول** من هندستنا مقابل كلام فيصل؟
    by_src, sole_src = {}, {}
    # 📒 بُعدٌ ثانٍ **محسوبٌ من القيمة النافذة**: مَن صاغ **رقمَ** الجدار؟
    #    (‏تصحيح 2026-08-12 — البُعدُ الأوّل يصف البوّابة وكان يُقرأ خطأً عن الرقم.)
    by_th, sole_th = {}, {}
    for r in rows:
        w = r.get("walls") or []
        if not w:
            continue
        s = wall_source(w[0])
        by_src[s] = by_src.get(s, 0) + 1
        t = threshold_source(w[0])
        by_th[t] = by_th.get(t, 0) + 1
        if len(w) == 1:
            sole_src[s] = sole_src.get(s, 0) + 1
            sole_th[t] = sole_th.get(t, 0) + 1
    return {"n": len(rows), "passed_after_relax": passed, "walls_hist": hist,
            "total_blocks": total, "sole_blocker": sole, "first_blocks": first,
            "first_by_source": by_src, "sole_by_source": sole_src,
            "first_by_thresh": by_th, "sole_by_thresh": sole_th}


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
    for title, key in (("📒 صياغةُ البوّابة — الجدار الأول", "first_by_source"),
                       ("📒 صياغةُ البوّابة — الجدار الوحيد", "sole_by_source"),
                       ("📒 مصدرُ **رقمِ** الجدار الأول (محسوبٌ من النافذ)",
                        "first_by_thresh"),
                       ("📒 مصدرُ **رقمِ** الجدار الوحيد (محسوبٌ من النافذ)",
                        "sole_by_thresh")):
        d = agg.get(key) or {}
        if d:
            tot = sum(d.values()) or 1
            body = " · ".join(f"{k}={v} ({100*v/tot:.0f}%)"
                              for k, v in sorted(d.items(), key=lambda kv: -kv[1]))
            out.append(f"   {title}: {body}")
    return out
