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
    # (2) 🚨 كشف مسح السيولة اللحظي على أسهم القائمة الرئيسية (لحظة فيصل «مسح
    #     ثم استعادة») — تنبيه فوري بدل انتظار تقرير الصباح/المساء.
    main_syms = [s["symbol"] for s in wl.get("stocks", [])
                 if s.get("status") == "active"]
    if main_syms and bot.yf is not None:
        try:
            hist = bot.download_history(main_syms)
            sweeps = bot.monitor_sweeps(wl, hist, bot.dt.date.today().isoformat())
            if sweeps:
                alerts.append(bot.build_sweep_alert(sweeps))
                bot.log(f"🚨 مسح سيولة لحظي: {len(sweeps)} سهم.")
            else:
                bot.log("مراقبة المسح: لا مسح سيولة جديد.")
        except Exception as e:
            bot.log(f"⚠️ كشف المسح اللحظي: {e}")
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
