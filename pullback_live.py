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


def main():
    wl = bot.load_watchlist()
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
            # قبل الافتتاح (13:30 UTC): الشمعة اليومية = أمس (بايتة) → premarket_only
            # يتخطّى أحداث الجلسة ويكتفي برادار البريماركت الحي (POLYGON_EDGE_PLAN §ج).
            _now = bot.dt.datetime.utcnow()
            _pm_only = (_now.hour * 60 + _now.minute) < 13 * 60 + 30
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
    for msg in alerts:
        bot.send_telegram(msg + "\n\n" + bot.FOOTER)


if __name__ == "__main__":
    main()
