#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔬 صيّاد «النهج العلمي» (فيصل) — **أداة مستقلّة** عن فارز الارتكاز وعن صيّاد المقسّم.

قرار المالك 2026-08-01: «خلّها أداة مستقلّة … نفس الطريقة اللي قدرت تبني فيها أداة
الصيّاد». فبُنيت على **نمط `split_hunter.py` حرفيًّا** بكلّ حرّاسه: بوّابة توقيت ·
دِدوب بطبقتين · حارس تغطية · إبلاغٌ صريح لا صمت · ختمُ حياة.

**المصدر:** `FAISAL_SCIENTIFIC_METHOD.md` (ستّ صور UPC، انفجر ‏+99.76% بالافتر).

🔴 **تصحيحٌ جوهريّ 2026-08-01 (بمسكة المالك على `IMG_0488`):** بُنيت المرحلة ③
أوّلًا على `trigger_state` وسندُها `TG_1870` «رجوعٌ يختبر القاع **مع سحب سيولة**»
= **كسرُ** القاع 7-13% ثم استعادته — **وهو نقيضُ** ما تنصّ عليه هذي الصور: «حافظ
عليها» · «**ذيول شموع وعدم كسرها**». فكان مَن يفعل ما يصفه فيصل **يسقط بنيويًّا**
(‏1 من 3386 حيًّا). العلاجُ دالّةٌ مستقلّة **`method_sequence`** بقراءة **الثبات**،
و`trigger_state` **لم تُمَسّ**. التفصيل: `FAISAL_SCIENTIFIC_METHOD.md §③`.

**الشروط الستّة** (‏`scan_method_hunter`): حدثٌ مؤسِّس (صعودٌ عالٍ ثم هبوط 20-30
جلسة) · التسلسل الرباعيّ · هدفٌ بنيويّ (رأس شمعة الفجوة) · خالٍ من قروب · لا
إعلان طرح · وسياق الاقتراض.

⚖️ **وميزتُها على القياس التاريخيّ:** الشرطان اللذان **استحال باكتيستُهما** —
«لا إعلان طرح» و«شورت قليل ورسوم عالية» — **يعملان حيًّا** ⇒ تُطبَّق الوصفة كاملة.
⚠️ **وحدُّ صدقٍ في كلّ رسالة:** الوصفة **قيد الإثبات الأماميّ** (‏`method_result.md`:
العيّنة 27 دون 30 ⇒ «لا حكم») — ولها سابقةٌ عندنا: **صيّاد المقسّم لم يُثبَت
بباكتيست قطّ وأثبت نفسه حيًّا** (‏NUWE قبل انفجاره بيومين).

🔒 عرض/تنبيه فقط — خارج الفرز والحالة، ولا `LOGIC_VERSION`.
"""

MIN_COVERAGE_PCT = 60.0        # 🩺 أرضية تغطية المسح (أقلّ منها = لم نفحص السوق)
STAMP_FILE = "method_hunter_stamp.json"


def session_gate(now_utc=None, close_hour=20):
    """⏰ نفس بوّابة الصيّاد: لا مسحَ قبل إغلاق الافتر (20:00 نيويورك) — تُصيب
    الفصلين ذاتيًّا. يرجّع `(مفتوحة، تاريخ الجلسة النيويوركيّ)`. نقيّة."""
    import datetime as _dt
    from zoneinfo import ZoneInfo as _Z
    now = now_utc or _dt.datetime.now(_dt.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=_dt.timezone.utc)
    et = now.astimezone(_Z("America/New_York"))
    if et.hour < int(close_hour):
        return (False, None)
    return (True, et.date())


def _fail(S, why: str) -> int:
    """🚨 عطلٌ صريح لا صمت (درس الصيّاد): وظيفةٌ خضراء بلا رسالة = مطابقةٌ ليوم
    «لا مرشّح» ⇒ العطل غير مرئي. يرجّع 1 فتصير الوظيفة حمراء أيضًا."""
    S.log(f"🔬 النهج العلمي: {why}")
    try:
        S.send_telegram("🔬 <b>النهج العلمي</b>\n\n"
                        f"⚠️ تعذّر المسح اليوم: {S.esc(why[:200])}\n"
                        "<i>الصمت اليوم عطل لا «لا مرشّح» — يُعاد غدًا آليًّا.</i>"
                        f"\n\n{S.FOOTER}")
    except Exception:                                            # noqa: BLE001
        pass
    return 1


def _read_stamp(S):
    try:
        import json
        with open(STAMP_FILE, encoding="utf-8") as f:
            return str((json.load(f) or {}).get("last_session") or "")
    except Exception:                                            # noqa: BLE001
        return ""


def _write_stamp(S, session_date) -> None:
    """🔔 ختمُ حياة — يُكتب **بعد الإرسال** (درس الصيّاد: لو خُتم قبل إرسالٍ فاشل
    لقرأه الكرون الثاني «سُلِّم» فضاعت رسالة الليلة). فاشل-آمن مطلق."""
    try:
        S._atomic_write_json(STAMP_FILE, {"last_session": str(session_date)})
        S.git_save([STAMP_FILE])
    except Exception as e:                                       # noqa: BLE001
        S.log(f"⚠️ ختم النهج العلمي: {e}")


def _frame_probe(S):
    """🔬 **مِجَسّ الفريم** — يقيس ولا يقرّر (‏`METHOD_4H_PROBE=1`، مطفأ افتراضيًّا
    ⇒ التشغيلة الليلية **بت-بت**).

    **سببُه سؤالٌ لم يُجَب:** `IMG_0494` «**هذي شموع 4 ساعات**» ⇒ الشارت الذي رسم
    عليه فيصل «ذيول شموع وعدم كسرها» فريمُه **4 ساعات**، وأداتُنا تقرأ **اليوميّ**.
    وفي `IMG_0495` يسأل متابعٌ «هذا النهج اطبقه دايم ع الفريم اليومي؟» **والجواب
    غير متاح**. ⇒ **لا يُغيَّر الفريم بالظنّ** (‏درسُ `trigger_state`) — يُقاس الفرق.

    **الحدثُ المؤسِّس تقويميّ فمستقلٌّ عن الفريم**، فنأخذ مَن استوفاه
    (`_METHOD_FOUNDING`) ونعيد قراءة **التسلسل وحده** على 4س بنفس `method_sequence`
    وبنافذةٍ مكافئة (‏جلسةٌ ⟹ **‏×6** شمعات 4س). فاشلٌ-آمن لكلّ رمز على حدة.
    🔒 **لا يمسّ المُرسَل ولا القائمة** — يطبع أرقامًا في السجلّ فقط.

    🔴 **وصُحِّح المضاعف (2026-08-01):** كان ‏×6 افتراضًا أن الجلسة ستّ شمعات 4س،
    و`fetch_4h` يجلب بـ`prepost=True` فالجلسة الممتدّة **16 ساعة ⟹ أربع شمعات**
    ⇒ كانت النافذة على 4س **أوسع من مكافئها اليوميّ** فالمِجَسّ متساهلٌ مع 4س.
    ⇒ صار المضاعف `METHOD_4H_BARS_PER_SESSION`=4 ومعه الإنتاج بالثابت نفسه.
    ⚠️ ولهذا **رقمُ 4س المنشور سابقًا (‏16) سقفٌ لا أرضية**."""
    import os
    if os.environ.get("METHOD_4H_PROBE", "") != "1":
        return
    rows = list(getattr(S, "_METHOD_FOUNDING", []) or [])
    if not rows:
        S.log("🔬 مِجَسّ الفريم: لا حدثَ مؤسِّس اليوم — لا شيء يُقاس.")
        return
    hit4h, checked, failed = [], 0, 0
    for r in rows:
        sym = str(r.get("symbol") or "")
        try:
            d4 = S.fetch_4h(sym)
            if d4 is None or len(d4) < 8:
                failed += 1
                continue
            checked += 1
            win = max(8, int(r.get("bars_since_peak") or 20)
                      * int(S.CONFIG["METHOD_4H_BARS_PER_SESSION"]) + 2)
            if S.method_sequence(d4, win=win):
                hit4h.append(sym)
        except Exception:                                        # noqa: BLE001
            failed += 1
    S.log(f"🔬 مِجَسّ الفريم (قياس فقط · لا يمسّ المُرسَل): حدثٌ مؤسِّس "
          f"{len(rows)} · فُحِص على 4س {checked} (تعذّر {failed}) · "
          f"**بلغ التسلسلَ على 4س {len(hit4h)}** مقابل "
          f"{(getattr(S, '_METHOD_STAGE', {}) or {}).get('seq', '؟')} على اليوميّ")
    if hit4h:
        S.log("   🕓 على 4س: " + " · ".join(hit4h[:40]))


def run(now_utc=None) -> int:
    import Super_stock as S
    import hunter_ledger as LEDGER
    import os
    manual = os.environ.get("METHOD_FORCE", "").strip() == "1"
    open_ok, sess_et = session_gate(now_utc)
    if not open_ok and not manual:
        S.log("⏰ النهج العلمي: الافتر لم يُغلق بعد — لا مسح.")
        return 0
    prev = _read_stamp(S)
    if sess_et is not None and not manual and prev == sess_et.isoformat():
        S.log(f"🔁 النهج العلمي: مساء {sess_et} سُلِّم سلفًا — لا تكرار.")
        return 0
    if S.yf is None:
        return _fail(S, "yfinance غير متاح على الرنر.")
    try:
        uni = S.get_universe()
    except Exception as e:                                       # noqa: BLE001
        return _fail(S, f"تعذّر جلب كون ناسداك ({e}).")
    if not uni:
        return _fail(S, "كون ناسداك رجع فارغًا.")
    try:
        hist = S.download_history(uni)
    except Exception as e:                                       # noqa: BLE001
        return _fail(S, f"تحميل البيانات فشل ({e}).")
    if not hist:
        return _fail(S, "لا بيانات مُحمَّلة إطلاقًا.")
    cov = 100.0 * len(hist) / max(1, len(uni))
    if cov < MIN_COVERAGE_PCT:
        return _fail(S, f"تغطية ناقصة: {len(hist)} من {len(uni)} رمزًا "
                        f"({cov:.0f}%) — لم يُفحَص السوق.")
    try:
        sess = max(df.index[-1] for df in hist.values() if len(df)).date()
    except Exception:                                            # noqa: BLE001
        sess = None
    if sess is not None and not manual and prev == sess.isoformat():
        S.log(f"🔁 النهج العلمي: جلسة {sess} سُلِّمت سلفًا — لا تكرار.")
        return 0
    try:
        # 🕓 **الفريمان معًا** (قرار المالك 2026-08-01: «الأهداف وغالبًا الشموع
        #    وحده»): اليوميّ أوّلًا بلا كلفة، ولا يُجلَب 4س إلا لمن سقط عليه.
        rows = S.scan_method_hunter(hist, today=sess, fetch_h4=S.fetch_4h)
    except Exception as e:                                       # noqa: BLE001
        return _fail(S, f"انهار المسح ({e}).")
    # 🌱 **ذاكرةُ الصيّاد** (`harvest_prereg.md`، بإذن المالك «نعم ابنها»):
    #    تُنادى **بعد اكتمال الاختيار وقبل أيّ إثراء** ⇒ لا تُدخل مرشّحًا ولا تُخرجه،
    #    ولا ترمي أبدًا، ومُتَمَاثِلة فالكرونان لا يُنتجان صفَّين.
    #    🔒 `ref_close` **يُجمَّد لحظةَ الرصد** (‏H3) — إغلاقُ جلسة المسح نفسها.
    try:
        LEDGER.record("method", sess, rows, log=S.log,
                      ref_of=lambda _s: float(hist[_s]["Close"].iloc[-1]))
    except Exception:                                            # noqa: BLE001
        pass
    # 🎁 **إثراء الكماليّات الحيّة** (طلب المالك 2026-08-01: «نفس اللي أضفناها في
    #    أداة التقسيم»): تدفّق السيولة · شمعة 4س · اختبار القاع.
    #    🔒 **بعد `scan_method_hunter`** ⇒ يستحيل بنيويًّا أن يُدخل مرشّحًا أو يُخرجه
    #    (الصفوف مُختارةٌ سلفًا)، وكلُّ جالبٍ **فاشلٌ-آمن على حدة**.
    for _r in rows:
        _sym = str(_r.get("symbol") or "")
        for _k, _fn in (("flow", lambda: S.polygon_flow(_sym)),
                        ("df4h", lambda: S.fetch_4h(_sym)),
                        ("bottom_test", lambda: S.bottom_test_state(_r.get("df")))):
            try:
                _r[_k] = _fn()
            except Exception:                                    # noqa: BLE001
                _r[_k] = None
    syms = " · ".join(str(r.get("symbol") or "?") for r in rows) or "—"
    S.log(f"🔬 النهج العلمي: فحص {len(hist)} من {len(uni)} رمزًا ({cov:.0f}%) "
          f"→ {len(rows)} مطابق كامل: {syms}")
    # 🩺 وأسبابُ «القريبين» في **السجلّ** أيضًا لا في تلغرام وحده — فيُشخَّص القمع
    #    من التشغيلة نفسها بلا انتظار رسالة (نظير عدّادات المراحل بالمسح).
    # ⚠️ **السجلّ بلا سقف عمدًا** — التشخيص يحتاج الكلّ، والقصّ للرسالة وحدها.
    for _n in (getattr(S, "_METHOD_NEAR", []) or []):
        S.log(f"   🔭 {_n.get('symbol')} ${float(_n.get('price') or 0):.2f} — "
              f"{_n.get('why')}")
    _frame_probe(S)
    if not rows:
        # 🔭 وحتى في يوم «لا يوجد» يصلك **مَن يقترب** — وهو جوهر «انتظر ضغطته
        #    مره ثانيه عند القاع»: المتابعة تسبق الترشيح.
        _near = getattr(S, "_METHOD_NEAR", []) or []
        msg = S._rtl_join([
            "🔬 <b>النهج العلمي</b>", "",
            "لا يوجد سهم يطابق الشروط اليوم.",
            f"🩺 فُحِص {len(hist)} من {len(uni)} رمزًا ({cov:.0f}% تغطية)"
            + (f" · جلسة {S.esc(str(sess))}" if sess else ""),
        ] + ([""] + S.method_near_lines(_near) if _near else [])) + "\n\n" + S.FOOTER
    else:
        try:
            msg = S.build_method_alert(rows, today=sess) + "\n\n" + S.FOOTER
        except Exception as e:                                   # noqa: BLE001
            return _fail(S, f"تعذّر بناء التنبيه رغم {len(rows)} مطابق ({e}).")
    if not S.send_telegram(msg):
        S.log("⛔ النهج العلمي: تلغرام رفض الرسالة.")
        return 1
    S.log("✅ أُرسلت رسالة النهج العلمي.")
    _write_stamp(S, sess)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
