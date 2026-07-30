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
HARVEST_CAP = int(os.environ.get("CTB_HARVEST_CAP", "60") or 60)
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
         "control_market": "membership"}
_SOURCE = {"faisal_exec": "faisal_text", "faisal_wait": "faisal_text",
           "faisal_negative": "faisal_text", "bot_selected": "bot_screen",
           "control_market": "universe_sample"}
# حصّةٌ محفوظة لكل فئة عند السقف — فنموّ القائمة **لا يخنق** لوحة الشاهد بصمت.
_QUOTA_ORDER = ["faisal_negative", "faisal_exec", "faisal_wait",
                "control_market", "bot_selected"]


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


def build_cohorts(watch_syms=None, control_syms=None):
    """يبني خطّة القياس: {symbol: cohort} بأولوية **الوسم على العضوية**.

    الوسم أولًا لأن سهمًا وسمه فيصل ثم رشّحه البوت **يبقى مثالًا موسومًا عنده** — ولو
    وسمناه `bot_selected` لضاع الوسم بصمت. والسالب يسبق الجميع (أندر وأثمن). نقيّة."""
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
    return plan


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
            universe=None):
    """يقيس الاقتراض لكل رمز في الخطّة ويسجّله. `fetch(sym) → {borrow_fee,
    shares_available}` (يُحقَن للاختبار؛ الافتراضي `ce_borrow_info` من البوت).
    يرجّع (مكتوب، مُسقَط، مُتعذّر).

    **الاقتصار على السقف يُعلَن ولا يُصمت**، والتوزيع **بحصص** (‏`_select_within_cap`)
    فلا تُخنَق لوحة الشاهد ولا الفئة السالبة عند ضيق السقف. وفشلُ جلب الكون يُسقط
    **لوحة الشاهد وحدها معلَنًا** — لا الحصاد كلّه، ولا يُستبدَل بصمت."""
    day = today_iso or dt.date.today().isoformat()
    cap = HARVEST_CAP if cap is None else cap
    if fetch is None:                       # استيراد كسول: انكساره لا يُسقط الأداة
        try:
            from Super_stock import ce_borrow_info as fetch      # noqa: PLC0415
        except Exception:
            print("⛔ تعذّر استيراد `ce_borrow_info` — لا حصاد (فاشل-آمن).")
            return (0, 0, 0)
    uni = _fetch_universe() if universe is None else universe
    ctrl = control_panel(uni, day[:7])
    if not ctrl:
        print("⚠️ لوحة الشاهد الضبطيّ **غائبة** هذه التشغيلة (تعذّر جلب الكون) — "
              "تُعلَن ولا تُستبدَل: الحصاد يمضي بفئات الوسم والقائمة فقط.")
    plan = build_cohorts(watch_syms if watch_syms is not None
                         else _watchlist_symbols(), ctrl)
    syms, dropped = _select_within_cap(plan, cap)
    rows, failed = [], 0
    for sym in syms:
        try:
            d = fetch(sym) or {}
        except Exception:
            d = {}
        if not d:
            failed += 1                     # تعذّر ≠ صفر ⇒ لا سطر كاذب
            continue
        c = plan[sym]
        rows.append({"schema": SCHEMA, "date": day, "symbol": sym, "cohort": c,
                     "label_kind": _KIND.get(c), "label_source": _SOURCE.get(c),
                     "shares_available": d.get("shares_available"),
                     "borrow_fee": d.get("borrow_fee"), "source": "chartexchange"})
    wrote = _record(rows, path)
    counts = {}
    for c in plan.values():
        counts[c] = counts.get(c, 0) + 1
    print("🔒 حصّاد الاقتراض " + day + " (schema " + str(SCHEMA) + "): خطّة "
          + str(len(plan)) + " رمزًا " + str(counts)
          + " → قِيس " + str(len(syms)) + " · كُتب " + str(wrote)
          + " · تعذّر " + str(failed))
    if dropped:
        print("⚠️ السقف " + str(cap) + " أسقط: " + str(dropped) + " — يُعلَن ولا يُصمت.")
    if wrote == 0:
        print("⚠️ صفر قياس — تعذّر الجلب لكل الرموز (لا يعني «لا بيانات»؛ عطلٌ محتمل).")
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
                           universe=uni)
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
                             path=p, universe=uni)
        assert w2 == 5 and dr2 > 0, (w2, dr2)
        got = [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()][-5:]
        assert len({r["cohort"] for r in got}) == 5, [r["cohort"] for r in got]
        # ④ غياب الكون ⇒ لوحة الشاهد غائبة معلَنة، والحصاد يمضي
        w3, _, _ = harvest(fetch=lambda s: {"shares_available": 2}, watch_syms=[],
                           today_iso="2026-07-30", path=p, universe=[])
        r3 = [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()][-w3:]
        assert not any(r["cohort"] == "control_market" for r in r3)
        # ⑤ فشل الجلب لا يكتب سطرًا كاذبًا · واستثناء الجالب يُعدّ تعذّرًا لا انهيارًا
        w4, _, f4 = harvest(fetch=lambda s: None, watch_syms=[],
                            today_iso="2026-07-30", path=p, universe=[])
        assert w4 == 0 and f4 == len(build_cohorts([], []))

        def _boom(_s):
            raise RuntimeError("شبكة")
        w5, _, f5 = harvest(fetch=_boom, watch_syms=[], today_iso="2026-07-30",
                            path=p, universe=[])
        assert w5 == 0 and f5 == len(build_cohorts([], []))
    print("✅ ctb_harvest selftest نجح")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(0 if harvest()[0] >= 0 else 1)
