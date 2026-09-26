"""🔒📈 حصّاد سياق الاقتراض **مع لوحة شاهدٍ ضبطيّة** (بحث/جمع فقط · خارج الفرز بالكامل).

**السبب:** `refresh_borrow` القائم يحدّث الاقتراض **لأسهم القائمة فقط** — أي ناجين اختارهم
البوت ⇒ أي تحليل لاحق دائريّ. فيجمع هذا الحصّاد **معينات مختلفة** لا معينًا واحدًا.

🔴 **تصحيح جوهريّ (schema 1 → 2، 2026-07-30):** النسخة الأولى بَنَت فئتيها على قراءةٍ
**خاطئة** لكلام فيصل: حسبتُ «متابعه فقط» **رفضًا** فسمّيتُ فئةً `faisal_watch_only`
وعدَدْتُها «شاهد ضبط سالب». وهي **تنصّلٌ من التوصية** بلفظه («متابعه فقط ( ليس توصيه شرا )»
— ELAB) لا حكمًا على السهم. ⇒ الفئتان كانتا **موجبتين معًا**، والاسم مضلِّل مرّتين (يوحي
بالسلبية، ويوحي بأنه ضبط). التفصيل والأدلّة: `borrow_labelled_set.md`.

**والتسمية الآن تفصل نوع الوسم عن مصدره** (وهو ما كان مفقودًا):
· `faisal_exec`     — نزّله وأمَر بالتنفيذ («اخذته الآن» · «شيله من العرض بأي سعر»).
· `faisal_wait`     — نزّله وقرارُه انتظار/شرطٌ غير محقَّق (+ تنصّل). **حالة توقيت لا رفض.**
· `faisal_negative` — نفيٌ منصوص بصوته: YYAI «علميا لا». **الفئة السالبة الحقيقية.**
· `bot_selected`    — ناجو الفرز (وسم **عضوية** عند ناجٍ، لا قرار خبير).
· `control_market`  — **لوحة الشاهد**: سحبٌ حتميّ من كون ناسداك، بلا انتقاء.

`label_kind` (decision/membership) و`label_source` يُكتبان مع كل صفّ **فتُقرأ الدائرية من
السجلّ نفسه** بلا رجوعٍ للتوثيق.

**🔴 خطوط حمراء:** فاشل-آمن مطلق · append-only (سطر JSONL لكل قياس) · **لا يكتب في
`weekly_watchlist.json` ولا يقرأ قرارًا ولا يؤثّر فيه** · **صفر كتابة حالة** (اللوحة
تُعاد حسابيًّا لا تُخزَّن) · لا أسرار · **السقف والحصص تُعلَن ويُسجَّل ما أُسقِط** · بلا
شبكة = لا عمل. **والنتيجة لا تُخزَّن في الصفّ أبدًا** (تُشتقّ وقت التحليل، وإلّا صار
الحصاد ذا نظرٍ مستقبليّ).

**ولا نتيجة تُستخرج منه الآن:** يحتاج تسجيلًا مسبقًا + موافقة المالك + أشهرًا من التراكم.
⚠️ وحدٌّ مقاس يجب أن يُقرأ قبل أي تحليل: **المقياس يتحرّك بمقدار خمس مراتب** (ELAB
«لايوجد اسهم متاحه» بنصّه مقابل 350,000 بحصادنا) ⇒ الفارق اليوميّ ضجيج، والصالح **المستوى
والاتجاه عبر أسابيع**.

التشغيل: `python3 ctb_harvest.py` (اختبار ذاتي: `--selftest`).
"""
import datetime as dt
import hashlib
import json
import os
import sys

LOG_PATH = os.environ.get("CTB_LOG", "ctb_log.jsonl")
SCHEMA = 2
# سقف نداءات ChartExchange لكل تشغيلة (الصفحة تُكشَط، فالإفراط يُخاطر بحظر).
# 🔄 60 ⟶ 110 (2026-09-26): فئةُ الارتداد (‏~23) ‏+ القائمةُ (‏~42) كانت تُقصّ بالسقف
#    (‏09-22: «أسقط bot_selected: 19») — والحمايةُ من الحظر صارت **بالمهلة** أدناه.
HARVEST_CAP = int(os.environ.get("CTB_HARVEST_CAP", "110") or 110)
# ⏱️ **مهلةٌ بين الطلبات وتمريرةُ إعادة** (2026-09-26 · `engineering` بلا ادّعاء سند):
#    السجلُّ يُثبت نمطًا ثابتًا — **أوّلُ 9-19 طلبًا تنجح ثمّ يتعذّر كلُّ ما بعدها**
#    (‏09-22: قِيس 60 · كُتب 9 · تعذّر 51 في ‏≈9 ثوانٍ · والتشغيلةُ خضراء) ⇒ الأرجحُ
#    حظرُ دفعاتٍ متتالية (استنتاجٌ قويّ من الترتيب الثابت · والسببُ يُطبع الآن).
#    والمهلةُ تعمل مع الجالب الحقيقيّ وحدَه — المحقونُ للاختبار بلا نوم.
FETCH_GAP_S = float(os.environ.get("CTB_FETCH_GAP_S", "2.0") or 2.0)
RETRY_PAUSE_S = float(os.environ.get("CTB_RETRY_PAUSE_S", "60") or 60)
# ⚠️ تعذّرُ نصفِ المقيس فأكثر (وعشرةٌ على الأقلّ) ⇒ تنبيهُ `::warning::` في التشغيلة
#    لا سطرٌ يمرّ صامتًا تحت خُضرتها.
WARN_FAIL_FRAC = 0.5
WARN_MIN_MEASURED = 10
# ⏳ سقفُ وقت الجالب الحقيقيّ (ثوانٍ) — ما بعده يُعدّ تعذّرًا بسبب `deadline` فلا تتجاوز
#    التشغيلةُ مهلةَ الجوب (30 دقيقة) لو صار كلُّ طلبٍ ينتظر مهلتَه (8 ثوانٍ).
BUDGET_S = float(os.environ.get("CTB_BUDGET_S", "1200") or 1200)
# حجم لوحة الشاهد الضبطيّ (سحبٌ حتميّ من كون ناسداك).
CONTROL_SIZE = int(os.environ.get("CTB_CONTROL_SIZE", "20") or 20)

# 🎯 **فئات فيصل — بأفعاله المنصوصة لا بتأويلنا.** المصدر لكلٍّ موثّق في
#    `borrow_labelled_set.md` §① (صورةً بصورة).
FAISAL_EXEC = {
    "DSY": "IMG_0291 «اخذته الآن من العرض الليلي 1.85 · دفعه اخرى 1.70 غدا»",
    "AZI": "TG_2198 «تحرر من 1.36 شيله من العرض بأي سعر»",
    "SPRC": "«محفظتي فلللل منه ابي اربح»",
    "PPCB": "«شورت صفر - فلوت 1.94مليون … ماركت ناخذه · تم»",
    "LABT": "TG_1807/TG_1816 «الأمان دخول من 2» · «الدخول بالملي 1.70←1.80»",
}
FAISAL_WAIT = {
    # ⚠️ ONCO كان مُوسَمًا خطأً `faisal_entered` في schema 1 — ونصّه رفضُ دخولٍ صريح.
    "ONCO": "TG_2171/IMG_0320 «لا طبعا · تبي تدخل مع مضارب تنتظر 60 سنت ل 70 · هل يثبت اولا»",
    "ELAB": "IMG_6475 «لايوجد اسهم متاحه للشورت · متابعه فقط ( ليس توصيه شرا )»",
    "EZRA": "IMG_0295 «الشورت متذبذب من 2000 ل 20000 · متابعه فقط»",
    "EDBL": "IMG_0298 «القاع 2 = ثبات او سحب سيوله · متابعه فقط · شورت 9000»",
    "CCHH": "IMG_0297 «شورته 9000 · تحت المتابعه · صعود قادم كسّر المقاومه الاولى»",
    "WORX": "TG_2076 «الشورت 550 الف · تابعه لين يبقى الشورت تحت 20 الف · ثباته فوق 1 نقرر»",
    "EHGO": "«شورت 15 الف - فلوت 1.62 مليون … ننتظر فقط مضارب يصعد بالسهم»",
    "CANF": "«الشورت صفر · اقتراض 200%» + «تحرر السهم 3.50 يتحول للإيجابية»",
    "MBRX": "«خبره عدم قبوله = هبوط · شورت 0»",
    "HTCR": "«انتظار سحب سيولة 2 ← 2.30 · شورت 20 ألف · فلوت 541 ألف»",
}
# 🔴 **الفئة السالبة الحقيقية** — نفيٌ منصوص بصوت فيصل، بلا لفظ «متابعة» فلا يمسّه
#    تصحيح المالك. وYYAI أثمنُها: يستوفي **كل** معيار عدديّ موثّق (مقسّم لم يصعد ·
#    متاح 1,000 تحت عتبته «تحت 20 ألف» · فلوت 800 ألفًا · تشبّع بيعي) وحكمُه «علميا لا»
#    — **ونتيجتُه سالبة محقَّقة** (‏$11 → 85 سنتًا). فهو ينقض **كفاية** البصمة بالنتيجة
#    لا بالوسم وحده.
FAISAL_NEGATIVE = {
    "YYAI": "TG_1876 «هل يصعد الان من المناطق الحاليه علميا لا» · شورت 1000 · فلوت 800 ألف",
    "GWAV": "«تم تهييض السهم 4 مرات ويهبط فيه المضارب · شورت 20 ألف · فلوت 778 ألف»",
}
_KIND = {"faisal_exec": "decision", "faisal_wait": "decision",
         "faisal_negative": "decision", "bot_selected": "membership",
         "control_market": "membership", "bot_pullback": "membership"}
_SOURCE = {"faisal_exec": "faisal_text", "faisal_wait": "faisal_text",
           "faisal_negative": "faisal_text", "bot_selected": "bot_screen",
           "control_market": "universe_sample", "bot_pullback": "bot_pullback_list"}
# حصّةٌ محفوظة لكل فئة عند السقف — فنموّ القائمة **لا يخنق** لوحة الشاهد بصمت.
# 🆕 `bot_pullback` (2026-09-26): **قائمةُ الارتداد** يراقبها البوت ولا يُخزَّن لها
#    «المتاح» ⇒ سؤالُ المالك «GRML وVBIO يطابقون؟» بقي شرطُه الرابع **مجهولًا**
#    (`watch_week_result.md` ⑥) — فصارت تُحصَد من هنا.
_QUOTA_ORDER = ["faisal_negative", "faisal_exec", "faisal_wait",
                "control_market", "bot_selected", "bot_pullback"]


def _watchlist_symbols(path="weekly_watchlist.json"):
    """رموز القائمة الحالية — **قراءة فقط** (لا كتابة ولا قرار). فاشلة-آمنة → []."""
    try:
        with open(path, encoding="utf-8") as fh:
            wl = json.load(fh) or {}
        out = []
        for s in (wl.get("stocks") or []):
            sym = (s or {}).get("symbol")
            if sym and (s or {}).get("status") == "active":
                out.append(str(sym).upper())
        return sorted(set(out))
    except Exception:
        return []


def _pullback_symbols(path="weekly_watchlist.json"):
    """رموز **قائمة الارتداد** بكلّ حالاتها — **قراءة فقط** (لا كتابة ولا قرار).
    فاشلة-آمنة → []."""
    try:
        with open(path, encoding="utf-8") as fh:
            wl = json.load(fh) or {}
        out = []
        for p in (wl.get("pullback") or []):
            sym = (p or {}).get("symbol")
            if sym:
                out.append(str(sym).upper())
        return sorted(set(out))
    except Exception:
        return []


def control_panel(universe, month, size=None):
    """🎯 **لوحة الشاهد الضبطيّ** — نقيّة وحتميّة: ترتيبٌ بـsha256(f"{month}:{sym}").

    نفس الشهر ⇒ **نفس اللوحة كل يوم** (فتنشأ سلسلة زمنية حقيقية للشاهد لا لقطات مبعثرة)،
    وتتجدّد شهريًّا **بلا انتقاء** (لا سعر ولا حجم ولا بوّابة ⇒ صفر انحياز اختيار وصفر
    نداء ياهو). ولا تُخزَّن (تُعاد حسابيًّا) ⇒ **صفر كتابة حالة**.

    ⚠️ **وما تجيبه محدود بصراحة:** «هل المتاح بالآلاف نادرٌ أصلًا أم شائعٌ في ناسداك؟»
    — وهو **خطُّ أساس سوقيّ** لا شاهدَ «قريبٍ من المرشّح»، ولا يجيب «هل يميّز المنفجر
    بين المرشّحين». وانحياز البقاء قائم (كون اليوم بلا المشطوبة)."""
    size = CONTROL_SIZE if size is None else size
    try:
        syms = sorted({str(s).upper() for s in (universe or []) if s})
    except Exception:
        return []
    if not syms or size <= 0:
        return []
    keyed = sorted(syms, key=lambda s: hashlib.sha256(
        (str(month) + ":" + s).encode("utf-8")).hexdigest())
    return keyed[:size]


def _fetch_universe():
    """كون ناسداك — نداء واحد، استيراد كسول، فاشل-آمن → []."""
    try:
        from Super_stock import get_universe                      # noqa: PLC0415
        return get_universe() or []
    except Exception:
        return []


def build_cohorts(watch_syms=None, control_syms=None, pullback_syms=None):
    """يبني خطّة القياس: {symbol: cohort} بأولوية **الوسم على العضوية**.

    الوسم أولًا لأن سهمًا وسمه فيصل ثم رشّحه البوت **يبقى مثالًا موسومًا عنده** — ولو
    وسمناه `bot_selected` لضاع الوسم بصمت. والسالب يسبق الجميع (أندر وأثمن). نقيّة.
    و`bot_pullback` (قائمةُ الارتداد) **آخرُ الأولويّات**: سهمٌ موسومٌ أو في القائمة
    أو في لوحة الشاهد يبقى بوسمه (فلا يتغيّر مقامُ فئةٍ قائمة بإضافتها)."""
    plan = {}
    for src, cohort in ((FAISAL_NEGATIVE, "faisal_negative"),
                        (FAISAL_EXEC, "faisal_exec"),
                        (FAISAL_WAIT, "faisal_wait")):
        for sym in src:
            plan.setdefault(sym, cohort)
    for sym in (control_syms or []):
        plan.setdefault(str(sym).upper(), "control_market")
    for sym in (watch_syms or []):
        plan.setdefault(str(sym).upper(), "bot_selected")
    for sym in (pullback_syms or []):
        plan.setdefault(str(sym).upper(), "bot_pullback")
    return plan


def fetch_order(syms, plan):
    """ترتيبُ الجلب **دوّارٌ بين الفئات** (واحدٌ من كلّ فئةٍ في كلّ لفّة) — نقيّة وحتميّة.

    🐞 **لماذا (2026-09-26):** الترتيبُ كان **فئةً بعد فئة** و`bot_selected` آخرُها،
    والحظرُ يقع بعد أوّل 9-19 طلبًا ⇒ **القائمةُ لم تُحصَد إلّا 12 يومًا من 37** منذ
    08-07 — فالحصصُ التي يوزّعها `_select_within_cap` بعدل **كان يهدمها ترتيبُ الجلب**.
    والدوّارُ يوزّع أيَّ خسارةٍ متبقّية على الفئات كلِّها بدل أن تبتلع فئةً كاملة."""
    by = {}
    for s in (syms or []):
        by.setdefault(plan.get(s), []).append(s)
    order = ([c for c in _QUOTA_ORDER if by.get(c)]
             + [c for c in by if c not in _QUOTA_ORDER])
    out, i, n = [], 0, sum(len(v) for v in by.values())
    while len(out) < n:
        for c in order:
            if i < len(by[c]):
                out.append(by[c][i])
        i += 1
    return out


def _select_within_cap(plan, cap):
    """يوزّع السقف **بحصص** لا بأولوية مسطّحة، فلا تُقصّ فئةٌ كاملةً بصمت.
    يرجّع (المختار مرتَّبًا حتميًّا، المُسقَط لكل فئة). نقيّة."""
    by = {}
    for sym, c in plan.items():
        by.setdefault(c, []).append(sym)
    for c in by:
        by[c].sort()
    if cap is None or cap >= len(plan):
        return ([s for c in _QUOTA_ORDER for s in by.get(c, [])], {})
    order = [c for c in _QUOTA_ORDER if by.get(c)]
    take = {c: 0 for c in order}
    left = max(0, int(cap))
    while left > 0 and any(take[c] < len(by[c]) for c in order):
        for c in order:                       # دورة عادلة: صفٌّ واحد لكل فئة كل لفّة
            if left <= 0:
                break
            if take[c] < len(by[c]):
                take[c] += 1
                left -= 1
    chosen = [s for c in order for s in by[c][:take[c]]]
    dropped = {c: len(by[c]) - take[c] for c in order if len(by[c]) > take[c]}
    return (chosen, dropped)


def _record(rows, path=None):
    """يكتب القياسات append-only. يرجّع عدد المكتوب. فاشل-آمن → 0."""
    n = 0
    try:
        with open(path or LOG_PATH, "a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                n += 1
    except Exception:
        return n
    return n


def harvest(fetch=None, watch_syms=None, today_iso=None, cap=None, path=None,
            universe=None, pullback_syms=None, sleep=None, gap=None,
            retry_pause=None):
    """يقيس الاقتراض لكل رمز في الخطّة ويسجّله. `fetch(sym) → {borrow_fee,
    shares_available}` (يُحقَن للاختبار؛ الافتراضي `ce_borrow_info` من البوت).
    يرجّع (مكتوب، مُسقَط، مُتعذّر).

    **الاقتصار على السقف يُعلَن ولا يُصمت**، والتوزيع **بحصص** (‏`_select_within_cap`)
    فلا تُخنَق لوحة الشاهد ولا الفئة السالبة عند ضيق السقف. وفشلُ جلب الكون يُسقط
    **لوحة الشاهد وحدها معلَنًا** — لا الحصاد كلّه، ولا يُستبدَل بصمت.

    ⏱️ **(2026-09-26)** الجلبُ **دوّارٌ بين الفئات** (`fetch_order`) · ومهلةُ `gap` بين
    الطلبات · وتمريرةُ إعادةٍ واحدة للمتعذّر بعد `retry_pause` — والنومُ **مع الجالب
    الحقيقيّ وحدَه** (المحقونُ للاختبار لا ينام) · وسقفُ وقتٍ `BUDGET_S` للجالب الحقيقيّ
    فلا تتجاوز التشغيلةُ مهلتَها · **وسببُ كلّ تعذّرٍ نهائيٍّ يُعدّ ويُطبع** · وتعذّرُ
    النصف فأكثر ⇒ `::warning::` (كانت التشغيلةُ خضراءَ وقد تعذّر 51 من 60)."""
    day = today_iso or dt.date.today().isoformat()
    cap = HARVEST_CAP if cap is None else cap
    real = fetch is None
    if real:                                # استيراد كسول: انكساره لا يُسقط الأداة
        try:
            from Super_stock import ce_borrow_info as fetch      # noqa: PLC0415
        except Exception:
            print("⛔ تعذّر استيراد `ce_borrow_info` — لا حصاد (فاشل-آمن).")
            return (0, 0, 0)
    if sleep is None:
        if real:
            import time as _time                                  # noqa: PLC0415
            sleep = _time.sleep
        else:
            def sleep(_s):
                return None
    gap = FETCH_GAP_S if gap is None else gap
    retry_pause = RETRY_PAUSE_S if retry_pause is None else retry_pause
    if real:
        import time as _time                                      # noqa: PLC0415
        deadline = _time.monotonic() + BUDGET_S
        clock = _time.monotonic
    else:
        deadline, clock = None, None
    uni = _fetch_universe() if universe is None else universe
    ctrl = control_panel(uni, day[:7])
    if not ctrl:
        print("⚠️ لوحة الشاهد الضبطيّ **غائبة** هذه التشغيلة (تعذّر جلب الكون) — "
              "تُعلَن ولا تُستبدَل: الحصاد يمضي بفئات الوسم والقائمة فقط.")
    plan = build_cohorts(watch_syms if watch_syms is not None
                         else _watchlist_symbols(), ctrl,
                         pullback_syms if pullback_syms is not None
                         else _pullback_symbols())
    syms, dropped = _select_within_cap(plan, cap)
    order = fetch_order(syms, plan)

    def _one(sym):
        dg = {}
        try:
            d = (fetch(sym, diag=dg) if real else fetch(sym)) or {}
        except Exception as e:              # الجالبُ المحقون قد يرمي — تعذّرٌ لا انهيار
            return {}, "exc:" + type(e).__name__, dg
        return d, ("" if d else (dg.get("reason") or "empty")), dg

    got, why, pending, first_bad = {}, {}, list(order), 0
    seq, samples, canary = [], [], ""
    for rnd in (1, 2):
        if rnd == 2:
            if not pending:
                break
            sleep(retry_pause)
        bad = []
        for k, sym in enumerate(pending):
            if deadline is not None and clock() > deadline:
                for rest in pending[k:]:
                    why[rest] = "deadline"
                bad.extend(pending[k:])
                break
            if k and gap > 0:
                sleep(gap)
            d, reason, dg = _one(sym)
            if rnd == 1:
                seq.append("✓" if d else "✗")
            if d:
                got[sym] = d
            else:                           # تعذّر ≠ صفر ⇒ لا سطر كاذب
                why[sym] = reason
                bad.append(sym)
                if rnd == 1 and len(samples) < 6:
                    samples.append(sym + ":" + reason + ":len=" + str(dg.get("len"))
                                   + ":" + repr(dg.get("snip", ""))[:120])
        if rnd == 1:
            first_bad = len(bad)
            # 🐤 **شاهدٌ داخليّ** (الجالبُ الحقيقيّ وحدَه · لا يُكتب): أوّلُ رمزٍ يُعاد جلبُه بعد
            #    التمريرة — نجح أوّلًا وتعذّر آخرًا ⇒ الموقعُ يتغيّر تحت الدفعة (لا عيبَ رمز).
            if real and order:
                sleep(gap)
                d0, r0, _dg0 = _one(order[0])
                canary = (order[0] + ": أوّلًا " + seq[0] + " · آخرًا "
                          + ("✓" if d0 else "✗ " + r0))
        pending = bad
    failed = len(pending)
    rows = []
    for sym in order:
        d = got.get(sym)
        if not d:
            continue
        c = plan[sym]
        rows.append({"schema": SCHEMA, "date": day, "symbol": sym, "cohort": c,
                     "label_kind": _KIND.get(c), "label_source": _SOURCE.get(c),
                     "shares_available": d.get("shares_available"),
                     "borrow_fee": d.get("borrow_fee"), "source": "chartexchange"})
    wrote = _record(rows, path)
    counts, wrote_by, reasons = {}, {}, {}
    for c in plan.values():
        counts[c] = counts.get(c, 0) + 1
    for r in rows:
        wrote_by[r["cohort"]] = wrote_by.get(r["cohort"], 0) + 1
    for sym in pending:
        reasons[why.get(sym, "?")] = reasons.get(why.get(sym, "?"), 0) + 1
    print("🔒 حصّاد الاقتراض " + day + " (schema " + str(SCHEMA) + "): خطّة "
          + str(len(plan)) + " رمزًا " + str(counts)
          + " → قِيس " + str(len(syms)) + " · كُتب " + str(wrote)
          + " · تعذّر " + str(failed))
    print("   ↳ كُتب لكلّ فئة: " + str(wrote_by)
          + " · أُنقذ بالإعادة: " + str(first_bad - failed)
          + " · أسبابُ التعذّر: " + str(reasons))
    print("   ↳ تسلسلُ التمريرة الأولى بترتيب الجلب: " + "".join(seq))
    if samples:
        print("   ↳ أمثلةُ التعذّر: " + " | ".join(samples))
    if canary:
        print("   ↳ 🐤 الشاهد " + canary)
    if dropped:
        print("⚠️ السقف " + str(cap) + " أسقط: " + str(dropped) + " — يُعلَن ولا يُصمت.")
    if wrote == 0:
        print("⚠️ صفر قياس — تعذّر الجلب لكل الرموز (لا يعني «لا بيانات»؛ عطلٌ محتمل).")
    if len(syms) >= WARN_MIN_MEASURED and failed >= WARN_FAIL_FRAC * len(syms):
        print("::warning::⚠️ حصّاد الاقتراض " + day + ": تعذّر " + str(failed)
              + " من " + str(len(syms)) + " — أسباب " + str(reasons)
              + " (التشغيلةُ خضراء والحصادُ ناقص)")
    return (wrote, sum(dropped.values()), failed)


def _selftest():
    """اختبار ذاتي بلا شبكة (يُشغَّل أيضًا من `test_bot.py`)."""
    import tempfile
    # ① حتميّة اللوحة: نفس الشهر ⇒ نفس اللوحة · شهر آخر ⇒ لوحة مختلفة · بلا انتقاء
    uni = ["S%03d" % i for i in range(400)]
    a1 = control_panel(uni, "2026-07", 20)
    a2 = control_panel(list(reversed(uni)), "2026-07", 20)   # الترتيب لا يؤثّر
    b1 = control_panel(uni, "2026-08", 20)
    assert a1 == a2 and len(a1) == 20, (a1[:3], a2[:3])
    assert a1 != b1, "الشهر يجب أن يبدّل اللوحة"
    assert control_panel([], "2026-07") == [] and control_panel(None, "x") == []
    # ② الوسم يسبق العضوية · والسالب يسبق الجميع
    plan = build_cohorts(["AAA", "ELAB", "YYAI"], ["BBB", "DSY"])
    assert plan["YYAI"] == "faisal_negative", plan.get("YYAI")
    assert plan["ELAB"] == "faisal_wait" and plan["DSY"] == "faisal_exec"
    assert plan["ONCO"] == "faisal_wait", "ONCO رفض الدخول — ليس exec"
    assert plan["AAA"] == "bot_selected" and plan["BBB"] == "control_market"
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "t.jsonl")
        w, dr, f = harvest(fetch=lambda s: {"shares_available": 5, "borrow_fee": 1.5},
                           watch_syms=["AAA"], today_iso="2026-07-30", path=p,
                           universe=uni, pullback_syms=[])
        assert dr == 0 and f == 0 and w == len(build_cohorts(["AAA"], a1)), (w, dr, f)
        recs = [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]
        assert all(r["schema"] == 2 and r["label_kind"] and r["label_source"]
                   for r in recs)
        assert {r["cohort"] for r in recs} >= {"faisal_negative", "faisal_exec",
                                               "faisal_wait", "bot_selected",
                                               "control_market"}
        # ③ السقف يوزّع بحصص: لا فئة تُقصّ كاملةً
        w2, dr2, _ = harvest(fetch=lambda s: {"shares_available": 1},
                             watch_syms=["AAA"], today_iso="2026-07-30", cap=5,
                             path=p, universe=uni, pullback_syms=[])
        assert w2 == 5 and dr2 > 0, (w2, dr2)
        got = [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()][-5:]
        assert len({r["cohort"] for r in got}) == 5, [r["cohort"] for r in got]
        # ④ غياب الكون ⇒ لوحة الشاهد غائبة معلَنة، والحصاد يمضي
        w3, _, _ = harvest(fetch=lambda s: {"shares_available": 2}, watch_syms=[],
                           today_iso="2026-07-30", path=p, universe=[],
                           pullback_syms=[])
        r3 = [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()][-w3:]
        assert not any(r["cohort"] == "control_market" for r in r3)
        # ⑤ فشل الجلب لا يكتب سطرًا كاذبًا · واستثناء الجالب يُعدّ تعذّرًا لا انهيارًا
        w4, _, f4 = harvest(fetch=lambda s: None, watch_syms=[],
                            today_iso="2026-07-30", path=p, universe=[],
                            pullback_syms=[])
        assert w4 == 0 and f4 == len(build_cohorts([], []))

        def _boom(_s):
            raise RuntimeError("شبكة")
        w5, _, f5 = harvest(fetch=_boom, watch_syms=[], today_iso="2026-07-30",
                            path=p, universe=[], pullback_syms=[])
        assert w5 == 0 and f5 == len(build_cohorts([], []))
        # ⑥ قائمةُ الارتداد فئةٌ مستقلّة وآخرُ الأولويّات (الموسومُ والقائمةُ يبقيان بوسمهما)
        pl6 = build_cohorts(["AAA"], ["BBB"], ["PBK", "AAA", "BBB", "DSY"])
        assert pl6["PBK"] == "bot_pullback" and pl6["AAA"] == "bot_selected"
        assert pl6["BBB"] == "control_market" and pl6["DSY"] == "faisal_exec"
        assert _KIND["bot_pullback"] == "membership" and _SOURCE["bot_pullback"]
        # ⑦ الجلبُ دوّار: أوّلُ لفّةٍ تمسّ كلَّ فئة قبل أن تتكرّر أيٌّ منها
        pl7 = build_cohorts(["W%02d" % i for i in range(8)], a1, ["P%02d" % i for i in range(8)])
        s7, _ = _select_within_cap(pl7, None)
        o7 = fetch_order(s7, pl7)
        k7 = len({pl7[x] for x in s7})
        assert sorted(o7) == sorted(s7) and len(o7) == len(s7)
        assert len({pl7[x] for x in o7[:k7]}) == k7, [pl7[x] for x in o7[:k7]]
        # ⑧ المهلةُ بين الطلبات وتمريرةُ الإعادة: يُنقَذ ما تعذّر أوّلًا · والنومُ يُحقَن
        seen, naps = {}, []

        def _flaky(sym):
            seen[sym] = seen.get(sym, 0) + 1
            return {"shares_available": 7} if seen[sym] >= 2 else {}
        w8, _, f8 = harvest(fetch=_flaky, watch_syms=[], today_iso="2026-07-31",
                            path=p, universe=[], pullback_syms=[],
                            sleep=naps.append, gap=0.5, retry_pause=9.0)
        n8 = len(build_cohorts([], []))
        assert w8 == n8 and f8 == 0, (w8, f8)
        assert naps.count(9.0) == 1 and naps.count(0.5) == 2 * (n8 - 1), naps
        # ⑨ تعذّرُ النصف فأكثر ⇒ `::warning::` (لا خُضرةٌ صامتة)
        import io as _io
        import contextlib as _cx
        buf = _io.StringIO()
        with _cx.redirect_stdout(buf):
            harvest(fetch=lambda s: None, watch_syms=[], today_iso="2026-07-31",
                    path=p, universe=[], pullback_syms=[])
        assert "::warning::" in buf.getvalue() and "empty" in buf.getvalue()
        buf2 = _io.StringIO()
        with _cx.redirect_stdout(buf2):
            harvest(fetch=lambda s: {"shares_available": 3}, watch_syms=[],
                    today_iso="2026-07-31", path=p, universe=[], pullback_syms=[])
        assert "::warning::" not in buf2.getvalue()
    print("✅ ctb_harvest selftest نجح")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(0 if harvest()[0] >= 0 else 1)
