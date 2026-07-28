# -*- coding: utf-8 -*-
"""
==========================================================
مراقبة الارتداد اللحظية (Intraday Pullback Monitor)
==========================================================
سكربت خفيف يُشغّل كل ~30 دقيقة أثناء ساعات السوق. يفحص فقط أسهم
«قائمة مراقبة الارتداد» (لا فرز كامل للسوق) — فهو سريع جداً. أول ما
ينزل سهم لسعر الدعم يرسل تنبيهاً فورياً (بدل انتظار تشغيل الصباح).

ملف منفصل — لا يلمس الفرز التلقائي ولا منطق البوت الأساسي.
التشغيل: python pullback_live.py
"""
try:
    import Super_stock as bot
except ImportError:
    import super_stock as bot


def _stamp_snapshot(wl):
    """لقطة أختام الدِدوب (`live_alert` + حالة الارتداد) قبل الرصد — للاسترجاع لو
    أخفق الإرسال. نقيّة (نسخ سطحي كافٍ: القيم قواميس تواريخ بسيطة)."""
    return ({s.get("symbol"): dict(s.get("live_alert") or {})
             for s in (wl.get("stocks") or [])},
            {e.get("symbol"): e.get("status") for e in (wl.get("pullback") or [])})


def _stamp_restore(wl, snap):
    """يُعيد الأختام كما كانت ⇒ الدورة التالية تُعيد المحاولة بدل ضياع التنبيه."""
    st, pb = snap
    for s in (wl.get("stocks") or []):
        prev = st.get(s.get("symbol"))
        if prev:
            s["live_alert"] = prev
        else:
            s.pop("live_alert", None)
    for e in (wl.get("pullback") or []):
        if e.get("symbol") in pb:
            e["status"] = pb[e["symbol"]]


def main():
    wl = bot.load_watchlist()
    snap = _stamp_snapshot(wl)     # 🛡️ للاسترجاع عند إخفاق الإرسال
    alerts = []           # (نص الرسالة) — تُرسَل بعد حفظ الحالة (دِدوب آمن)
    # (1) مراقبة الارتداد: تنبيه أول ما ينزل سهم لسعر الدعم
    entries = [e for e in (wl.get("pullback") or [])
               if e.get("status") != "triggered"]
    if entries:
        bot.log(f"مراقبة الارتداد اللحظية: فحص {len(entries)} سهم...")
        triggered = bot.monitor_pullback(wl)
        if triggered:
            alerts.append("🚨 <b>تنبيه ارتداد فوري</b>\n\n"
                          + bot.build_pullback_section([], triggered))
            bot.log(f"🚨 تنبيه ارتداد: {len(triggered)} سهم وصل الدعم.")
        else:
            bot.log("مراقبة الارتداد: لا سهم وصل الدعم بعد.")
    # (2) 🚨 الأحداث اللحظية على أسهم القائمة الرئيسية (مسح سيولة · دخول منطقة
    #     الشراء · كسر دعم/وقف · تجاوز الرقم الحرج) + لقطة أوامر السهم المتحرّك.
    main_syms = [s["symbol"] for s in wl.get("stocks", [])
                 if s.get("status") == "active"]
    if main_syms and bot.yf is not None:
        try:
            hist = bot.download_history(main_syms)
            # قبل الافتتاح: الشمعة اليومية = أمس (بايتة) → premarket_only يتخطّى
            # أحداث الجلسة ويكتفي برادار البريماركت الحي (POLYGON_EDGE_PLAN §ج).
            # ⑤ (إصلاح تدقيق 2026-07-12): الافتتاح مشتق من توقيت نيويورك — كان
            # مثبّتًا 13:30 UTC (صيفي) فتشغيلات 13:30-14:30 شتاءً تقرأ شمعة أمس
            # كأنها حيّة وتحرق الدِدوب فيُكتَم التنبيه الحقيقي.
            _now = bot.dt.datetime.utcnow()
            _pm_only = ((_now.hour * 60 + _now.minute)
                        < bot.market_session_now()["open"])
            events = bot.monitor_live_events(
                wl, hist, bot.dt.date.today().isoformat(),
                premarket_only=_pm_only)
            if events:
                # سطر المضارب المختصر داخل وصف الحدث يكفي (طلب المستخدم 2026-07-09)
                # — «لقطة الأوامر» لم تعد تُعرض فلا تُجلب (توفير نداءات).
                alerts.append(bot.build_live_alert(events))
                bot.log(f"🚨 أحداث لحظية: {len(events)}.")
            else:
                bot.log("المراقبة اللحظية: لا أحداث جديدة.")
        except Exception as e:
            bot.log(f"⚠️ الأحداث اللحظية: {e}")
    if not alerts:
        return
    # احفظ الحالة (triggered + sweep_alert_date) **قبل** الإرسال — لو فشل الإرسال
    # أو انهارت العملية بعده لا تتكرّر التنبيهات (نفس ضمان المسار الأصلي).
    bot.save_watchlist(wl)
    try:
        bot.git_save([bot.WATCH_FILE])
    except Exception as e:
        bot.log(f"⚠️ حفظ الحالة: {e}")
    # ⚠️ **إصلاح 2026-07-27 (تدقيق «أعلى مستوى»):** كانت نتيجة الإرسال **مُهمَلة**،
    # والختم محفوظًا ومدفوعًا **قبله** — فرفضُ تلغرام (400 على HTML، حالة موثّقة) كان
    # يعني أن تنبيه **كسر الوقف** يُستهلَك ولا يصل **أبدًا**، والوظيفة خضراء.
    # الحلّ لا يقلب المقايضة (الحفظ-قبل-الإرسال يمنع التكرار): عند الإخفاق **تُعاد
    # الأختام كما كانت** فتُعيد الدورة التالية (30د) المحاولة، ويخرج بغير صفر ليُرى.
    failed = 0
    for msg in alerts:
        try:
            if not bot.send_telegram(msg + "\n\n" + bot.FOOTER):
                failed += 1
        except Exception as e:                                   # noqa: BLE001
            bot.log(f"⚠️ إرسال التنبيه: {e}")
            failed += 1
    if failed:
        bot.log(f"⛔ لم يصل {failed} من {len(alerts)} تنبيهًا — أُعيدت أختام الدِدوب "
                "لتُعاد المحاولة بالدورة التالية (تنبيه الخطر لا يُفقَد).")
        _stamp_restore(wl, snap)
        bot.save_watchlist(wl)
        try:
            bot.git_save([bot.WATCH_FILE])
        except Exception as e:                                   # noqa: BLE001
            bot.log(f"⚠️ استرجاع الأختام: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
