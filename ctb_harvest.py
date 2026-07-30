"""🔒📈 حصّاد سياق الاقتراض **بشاهد ضبط سالب** (بحث/جمع فقط · خارج الفرز بالكامل).

**السبب (البند 2 من `COMMON_LINK_REPORT_FOR_OPUS.md` §⑥-مكرر):** `refresh_borrow` القائم
يحدّث الاقتراض **لأسهم القائمة فقط** — أي **ناجين اختارهم البوت** ⇒ أي تحليل لاحق دائريّ
باعتراض القضاة. هذا الحصّاد يضيف **شاهد ضبط سالبًا**: أسهمًا **وسمها فيصل نفسه «متابعه فقط»**
(`borrow_labelled_set.md`) ⇒ فتتراكم لدينا الفئتان معًا لا فئة واحدة.

⚠️ **ونطاقه محدود عن قصد.** `borrow_labelled_set.md` أثبت — من مجموعة فيصل المُوسَمة — أن
الاقتراض **سياقٌ لا قاعدة** (ELAB متاحُه **صفر** وحكمه «متابعة فقط» ⇒ الكفاية تسقط · ONCO
‏150 ألفًا **ودخله** ⇒ اللزوم يسقط · DSY 7,000 «دخل» مقابل EDBL/CCHH 9,000 «متابعة» ⇒ لا
تمييز عند الحدّ). ⇒ **لا يُبنى خطٌّ ضخم لفرضية الاقتراض وحدها.** الباقي غير المُجاب هو
**التركيبة** «متاح × رسوم × حضور مضارب»، فهذا الحصّاد يسجّل **الشقّ الاقتراضيّ** منها
ليُقرَن لاحقًا بحصاد المضارب (`hand_flow_log.jsonl`).

**🔴 خطوط حمراء:** فاشل-آمن مطلق · append-only crash-safe (سطر JSONL لكل قياس) · **لا يكتب
في `weekly_watchlist.json` ولا يقرأ قرارًا ولا يؤثّر فيه** · لا أسرار · **سقف نداءات معلَن
ويُسجَّل ما أُسقِط** (قاعدة «لا سقوف صامتة») · بلا شبكة = لا عمل.

**ولا نتيجة تُستخرج منه الآن:** التحليل يحتاج تسجيلًا مسبقًا + موافقة المالك، وأشهرًا من
التراكم. هذا **جمعُ بيانات** بحت.

التشغيل: `python3 ctb_harvest.py` (اختبار ذاتي: `--selftest`).
"""
import datetime as dt
import json
import os
import sys

LOG_PATH = os.environ.get("CTB_LOG", "ctb_log.jsonl")
SCHEMA = 1
# سقف نداءات ChartExchange لكل تشغيلة (الصفحة تُكشَط، فالإفراط يُخاطر بحظر).
HARVEST_CAP = int(os.environ.get("CTB_HARVEST_CAP", "40") or 40)

# 🔴 **شاهد الضبط السالب — أسهمٌ وسمها فيصل نفسه «متابعه فقط» بذكر أرقام اقتراضها.**
# المصدر لكلٍّ منها موثّق في `borrow_labelled_set.md` §① (صورةً بصورة). هذه **ليست**
# ترشيحات ولا قائمة مراقبة — هي **أمثلة سالبة** يلزم وجودها لئلّا يكون التحليل دائريًّا.
FAISAL_WATCH_ONLY = {
    "ELAB": "IMG_6475 «متاح صفر + تدوير 750% · متابعة فقط»",
    "EZRA": "IMG_0295 «رُفع أكثر من مرة بدون مضارب · شورت 2000→20000 · متابعه فقط»",
    "EDBL": "IMG_0298 «تم التلاعب بالشموع أكثر من مرة · شورت 9000 · متابعه فقط»",
    "CCHH": "IMG_0297 «شورته 9000 · تحت المتابعه»",
}
# وأسهمٌ **دخلها/أيّدها** فيصل بذكر أرقامه — الطرف الموجب من نفس المجموعة المُوسَمة.
FAISAL_ENTERED = {
    "DSY": "IMG_0291 «اخذته الآن 1.85» · IMG_9509/9510 «7000 متاح · رسوم 725% = اجابي»",
    "ONCO": "IMG_0392 «شورت 150 الف · دخول مع مضارب انتظار»",
    "AZI": "IMG_0290 «تحرر من 1.36 شيله من العرض بأي سعر»",
}


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


def build_cohorts(watch_syms=None):
    """يبني خطّة القياس: {symbol: cohort} بأولوية **الوسم على العضوية**.

    الوسم أولًا لأن سهمًا وسمه فيصل «متابعه فقط» ثم رشّحه البوت **يبقى مثالًا سالبًا
    عند فيصل** — ولو وسمناه `watch` لضاع شاهد الضبط بصمت (وهو كل الغرض). نقيّة."""
    plan = {}
    for sym, _why in FAISAL_WATCH_ONLY.items():
        plan[sym] = "faisal_watch_only"
    for sym, _why in FAISAL_ENTERED.items():
        plan.setdefault(sym, "faisal_entered")
    for sym in (watch_syms or []):
        plan.setdefault(str(sym).upper(), "bot_watchlist")
    return plan


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


def harvest(fetch=None, watch_syms=None, today_iso=None, cap=None, path=None):
    """يقيس الاقتراض لكل رمز في الخطّة ويسجّله. `fetch(sym) → {borrow_fee, shares_available}`
    (يُحقَن للاختبار؛ الافتراضي `ce_borrow_info` من البوت). يرجّع (مكتوب، مُسقَط، مُتعذّر).

    **الاقتصار على السقف يُعلَن ولا يُصمت** — والترتيب **حتميّ** (الشاهد السالب أولًا) فلا
    يقع القصّ على شاهد الضبط عند ضيق السقف."""
    day = today_iso or dt.date.today().isoformat()
    cap = HARVEST_CAP if cap is None else cap
    if fetch is None:                       # استيراد كسول: انكساره لا يُسقط الأداة
        try:
            from Super_stock import ce_borrow_info as fetch      # noqa: PLC0415
        except Exception:
            print("⛔ تعذّر استيراد `ce_borrow_info` — لا حصاد (فاشل-آمن).")
            return (0, 0, 0)
    plan = build_cohorts(watch_syms if watch_syms is not None
                         else _watchlist_symbols())
    order = ["faisal_watch_only", "faisal_entered", "bot_watchlist"]
    syms = sorted(plan, key=lambda s: (order.index(plan[s]), s))
    dropped = max(0, len(syms) - cap)
    rows, failed = [], 0
    for sym in syms[:cap]:
        try:
            d = fetch(sym) or {}
        except Exception:
            d = {}
        if not d:
            failed += 1
            continue
        rows.append({"schema": SCHEMA, "date": day, "symbol": sym,
                     "cohort": plan[sym],
                     "shares_available": d.get("shares_available"),
                     "borrow_fee": d.get("borrow_fee"), "source": "chartexchange"})
    wrote = _record(rows, path)
    print(f"🔒 حصّاد الاقتراض {day}: خطّة {len(syms)} رمزًا "
          f"(سالب {sum(1 for s in plan.values() if s == 'faisal_watch_only')} · "
          f"موجب {sum(1 for s in plan.values() if s == 'faisal_entered')} · "
          f"قائمة {sum(1 for s in plan.values() if s == 'bot_watchlist')}) "
          f"→ كُتب {wrote} · تعذّر {failed} · أُسقِط بالسقف {dropped}")
    if dropped:
        print(f"⚠️ السقف {cap} أسقط {dropped} رمزًا — يُعلَن ولا يُصمت.")
    if wrote == 0:
        print("⚠️ صفر قياس — تعذّر الجلب لكل الرموز (لا يعني «لا بيانات»؛ عطلٌ محتمل).")
    return (wrote, dropped, failed)


def _selftest():
    """اختبار ذاتي بلا شبكة (يُشغَّل أيضًا من `test_bot.py`)."""
    plan = build_cohorts(["AAA", "ELAB"])
    assert plan["ELAB"] == "faisal_watch_only", "الوسم يجب أن يسبق العضوية"
    assert plan["AAA"] == "bot_watchlist"
    assert plan["DSY"] == "faisal_entered"
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "t.jsonl")
        w, dr, f = harvest(fetch=lambda s: {"shares_available": 5, "borrow_fee": 1.5},
                           watch_syms=["AAA"], today_iso="2026-07-30", path=p)
        assert w == len(plan) and dr == 0 and f == 0, (w, dr, f)
        recs = [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]
        assert {r["symbol"] for r in recs} == set(plan)
        # السقف: الشاهد السالب لا يُقصّ (الترتيب حتميّ)
        w2, dr2, _ = harvest(fetch=lambda s: {"shares_available": 1},
                             watch_syms=["AAA"], today_iso="2026-07-30",
                             cap=2, path=p)
        assert w2 == 2 and dr2 == len(plan) - 2
        recs2 = [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()][-2:]
        assert all(r["cohort"] == "faisal_watch_only" for r in recs2), recs2
        # فشل الجلب لا يرمي ولا يكتب سطرًا كاذبًا
        w3, _, f3 = harvest(fetch=lambda s: None, watch_syms=[],
                            today_iso="2026-07-30", path=p)
        assert w3 == 0 and f3 == len(build_cohorts([]))
        # استثناء داخل الجالب يُعدّ تعذّرًا لا انهيارًا
        def _boom(_s):
            raise RuntimeError("شبكة")
        w4, _, f4 = harvest(fetch=_boom, watch_syms=[], today_iso="2026-07-30", path=p)
        assert w4 == 0 and f4 == len(build_cohorts([]))
    print("✅ ctb_harvest selftest نجح")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    sys.exit(0 if harvest()[0] >= 0 else 1)
