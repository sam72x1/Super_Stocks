#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🪝 صيّاد أسهم التقسيم (منهج فيصل) — أداة **مستقلة تمامًا** عن فارز الارتكاز (14 بوابة).

الفكرة (طلب المستخدم 2026-07-24): فكرة/نمط مختلف عن البوت الأساسي — تمسح ناسداك
**يوميًّا بعد الإغلاق** عن مقسّم عكسي يطابق setup فيصل **الصارم**، وإذا لقت سهمًا يطابق
كل الشروط الأساسية ترسله لتلغرام مباشرة. **صامتة لو لا مطابق.**

الشروط الصارمة (كلها): مقسّم عكسي حديث + وصل قمة-ما-بعد-التقسيم÷2 + حافظ القاع 3
جلسات + فلوت<2مليون (ياهو) + خالٍ من رفعة قروب. السياق (عرض): المتاح<20ألف + الرسوم
(ChartExchange) + متوسطات 20/30/50 + تكرار التقسيم.

🔒 عرض/تنبيه فقط — لا تمسّ حالة البوت ولا الفرز ولا LOGIC_VERSION. لا تحفظ شيئًا.
التشغيل: python split_hunter.py (يلزم TELEGRAM_BOT_TOKEN/CHAT_ID · ياهو للفلوت)."""


MIN_COVERAGE_PCT = 60.0        # 🩺 أرضية تغطية المسح (أقلّ منها = لم نفحص السوق)
# 🌙 وسم الفاشل-الآمن المفتوح: يُرسَل التنبيه **ولا يُكتَم**، لكن بلا ثقةٍ كاذبة.
AH_UNVERIFIED_TAG = "⚠️ لم يُتحقّق من سعر الافتر"


def ah_guard(S, rows, session_date, fetch=None):
    """🌙⛔ **حارس الافتر (AH-GUARD)** — يمنع التنبيه **البائت**.

    العيب المُثبَت (2026-07-30): الصيّاد يعمل بعد إغلاق الافتر بالتصميم، لكن بياناته
    شمعة ياهو اليومية و**هي لا تشمل الافتر** ⇒ رشّح NUWE بعد أن انفجر ‏+100% في الافتر.

    القاعدة — **صفر عتبة مخترعة**: نعيد تطبيق شرط فيصل ② «لم يصعد»
    (`SPLIT_ROSE_MAX_PCT` كما هو) على **السعر الممتد** مقابل مرجعَي الصفّ نفسه:
    `price` (إغلاق الجلسة الذي بُني عليه الكرت كلّه: القاع÷2 · الهدف · الوقف) و`ref`
    (قمة ما بعد الحدث = الهدف +100%). كسرُ أيّهما ⇒ **يُكتَم** مع سطر سجلّ صريح.

    ⚠️ **لماذا المرجعان لا `ref` وحده** (تصريحٌ لا اجتهادٌ صامت): في NUWE نفسه
    ‏`ref ≈ 2×price`، والانفجار بلغ ‏~`ref` ⇒ ‏`ext/ref − 1 ≈ 0%` فلا يكتم شيئًا؛
    الذي يلتقط «+100% في الافتر» فعلًا هو ‏`ext/price − 1`. فأُبقي شرط `ref` كما نُصّ
    عليه **وأُضيف** مرجع `price` — والعتبة واحدة لم تُمسّ.

    🔒 **فاشل-آمن مفتوح (fail-open):** بلا مفتاح/تعذّر الجلب/صفر شموع/مرجع تالف ⇒
    الصفّ **يبقى** ويُوسَم في `unverified` (تعذّر ≠ صفر · لا كتم صامت ولا ثقة كاذبة).
    يرجع `(kept, unverified)`. `fetch(sym, date)` محقون للاختبار بلا شبكة."""
    kept, unverified = [], []
    try:
        th = float(S.CONFIG["SPLIT_ROSE_MAX_PCT"])
    except Exception:                                            # noqa: BLE001
        return list(rows or []), [str(r.get("symbol") or "") for r in (rows or [])]
    f = fetch if fetch is not None else S.extended_last_price
    for r in rows or []:
        sym = str(r.get("symbol") or "")
        try:
            ext = f(sym, session_date)
            ext = float(ext) if ext is not None else None
        except Exception:                                        # noqa: BLE001
            ext = None
        if ext is None or ext != ext or ext <= 0:                # ⚠️ NaN ليس None
            unverified.append(sym)
            kept.append(r)
            continue
        bases, broke = [], None
        for name, raw in (("إغلاق الجلسة", r.get("price")),
                          ("قمة ما بعد الحدث", r.get("ref"))):
            try:
                b = float(raw)
            except (TypeError, ValueError):
                continue
            if b != b or b <= 0:
                continue
            bases.append(name)
            rise = (ext / b - 1.0) * 100.0
            # نفس صيغة المِجَسّ حرفيًّا: القرار على الخام و«أكبر من» لا «أكبر أو يساوي»
            if broke is None and rise > th:
                broke = (name, b, rise)
        if not bases:                     # لا مرجع صالح ⇒ لم نتحقّق (لا نكتم بالظنّ)
            unverified.append(sym)
            kept.append(r)
            continue
        if broke:
            S.log(f"⛔ {sym}: شرط «لم يصعد» مكسور بالافتر (+{broke[2]:.0f}% عن "
                  f"{broke[0]} ${broke[1]:.2f} ← ${ext:.2f}) — تنبيه بائت أُلغي")
            continue
        kept.append(r)
    return kept, unverified


def _fail(S, why: str) -> int:
    """🚨 **عطل صريح لا صمت.** عقد الأداة أن الصمت محجوز لـ«لا مرشّح كامل اليوم»؛
    فأي مسار فشل يجب أن **يُبلَّغ** وإلا قرأه المالك «لا سهم مقسّم اليوم» وهو غلط.
    (هذا بعينه الناقل الموثّق في CLAUDE.md: «أخطر ناقل — تفويت بصمت».)
    يرجع 1 ⇒ الوظيفة **حمراء** في Actions أيضًا فلا يضيع العطل لو تعذّر تلغرام."""
    S.log(f"🪝 صيّاد المقسّم: {why}")
    try:
        S.send_telegram("🪝 <b>صيّاد أسهم التقسيم</b>\n\n"
                        f"⚠️ تعذّر المسح اليوم: {S.esc(why[:200])}\n"
                        "<i>الصمت اليوم عطل لا «لا مرشّح» — يُعاد غدًا آليًّا.</i>"
                        f"\n\n{S.FOOTER}")
    except Exception:                                            # noqa: BLE001
        pass
    return 1


def run(fetch_ext=None):
    import Super_stock as S
    # ⚠️ **كل مسارات الفشل كانت ترجع 0 بصمت** (تدقيق 2026-07-27): وظيفة خضراء بلا
    # رسالة = مطابقٌ تمامًا ليوم «لا مرشّح» ⇒ العطل غير مرئي. صارت كلها تمرّ بـ`_fail`.
    if S.yf is None:
        return _fail(S, "yfinance غير متاح على الرنر.")
    try:
        uni = S.get_universe()
    except Exception as e:                                       # noqa: BLE001
        return _fail(S, f"تعذّر جلب كون ناسداك ({e}).")
    if not uni:
        return _fail(S, "كون ناسداك رجع فارغًا (تعذّر تحميل قائمة الرموز).")
    try:
        hist = S.download_history(uni)
    except Exception as e:                                       # noqa: BLE001
        return _fail(S, f"تحميل البيانات فشل ({e}).")
    if not hist:
        return _fail(S, "لا بيانات مُحمَّلة إطلاقًا.")
    # 🩺 **حارس التغطية** — الناقل الأخطر: خنق ياهو يُنزل التغطية من ~3400 رمز إلى
    # بضع مئات، فيمشي المسح ويطبع «0 مطابق» ويصمت، والمالك يقرأ الصمت «لا سهم مقسّم».
    # الحقيقة أننا **لم نفحص السوق**. (نفس حارس المسار اليومي الموثّق بـCLAUDE.md.)
    cov = 100.0 * len(hist) / max(1, len(uni))
    if cov < MIN_COVERAGE_PCT:
        return _fail(S, f"تغطية ناقصة: {len(hist)} من {len(uni)} رمزًا ({cov:.0f}%) — "
                        f"أقل من الأرضية {MIN_COVERAGE_PCT:.0f}%، فلم يُفحَص السوق.")
    try:
        rows = S.scan_split_hunter(hist)
    except Exception as e:                                       # noqa: BLE001
        return _fail(S, f"انهار المسح ({e}).")
    # 🔎 **الرموز تُطبَع دائمًا** (إصلاح رصد 2026-07-30): كان السجلّ يقول «1 مطابق
    # كامل» بلا اسم، فيوم NUWE لم يكن في السجلّ ما يُقرأ لاحقًا لمعرفة مَن رُشِّح.
    _syms = " · ".join(str(r.get("symbol") or "?") for r in rows) or "—"
    S.log(f"🪝 صيّاد المقسّم: فحص {len(hist)} من {len(uni)} رمزًا ({cov:.0f}%) "
          f"→ {len(rows)} مطابق كامل: {_syms}")
    if not rows:
        S.log("🪝 صيّاد المقسّم: لا مطابق كامل اليوم — صمت (لا إرسال).")
        return 0
    # 📅 تاريخ **الجلسة** من البيانات لا `date.today()` على الرنر: الكرون صار فجر UTC
    # فتاريخ اليوم هناك = **اليوم التالي** للجلسة (جلسة الجمعة تُوسَم سبتًا).
    try:
        sess = max(df.index[-1] for df in hist.values() if len(df)).date()
    except Exception:                                            # noqa: BLE001
        sess = None
    # 🌙⛔ حارس الافتر: شمعة ياهو لا تشمل الافتر، والصيّاد يُسلّم **بعده** ⇒ نتحقّق
    # من السعر الممتد لـ**يوم الجلسة نفسه** ونكتم البائت. بلا يوم جلسة = لا تحقّق
    # (فاشل-آمن مفتوح: يُرسَل موسومًا، لا كتم بالظنّ).
    if sess is None:
        unverified = [str(r.get("symbol") or "") for r in rows]
    else:
        rows, unverified = ah_guard(S, rows, sess, fetch=fetch_ext)
    if not rows:
        S.log("🪝 صيّاد المقسّم: كل المطابقين بائتون بعد فحص الافتر — لا إرسال.")
        return 0
    try:
        msg = S.build_split_hunter_alert(rows, today=sess) + (
            "\n" + S._rtl_join([
                f"{AH_UNVERIFIED_TAG} لـ: {S.esc(' · '.join(unverified))} — "
                "قد يكون تحرّك بعد الإغلاق ولم نتمكّن من قراءته."])
            if unverified else "") + "\n\n" + S.FOOTER
    except Exception as e:                                       # noqa: BLE001
        return _fail(S, f"تعذّر بناء التنبيه رغم وجود {len(rows)} مطابق ({e}).")
    # ⚠️ **نتيجة الإرسال كانت مُهمَلة** والسجلّ يطبع «✅ أُرسل» بلا شرط: رفضُ تلغرام
    # (400 على HTML) كان يُضيّع **المطابق** والوظيفة خضراء والسجلّ يكذب.
    if not S.send_telegram(msg):
        S.log("⛔ صيّاد المقسّم: تلغرام رفض التنبيه — المطابق لم يصل.")
        return 1
    S.log("✅ أُرسل تنبيه صيّاد المقسّم لتلغرام.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
