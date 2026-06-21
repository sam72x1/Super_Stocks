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
    entries = [e for e in (wl.get("pullback") or [])
               if e.get("status") != "triggered"]
    if not entries:
        bot.log("مراقبة الارتداد: لا أسهم نشطة للمتابعة.")
        return
    bot.log(f"مراقبة الارتداد اللحظية: فحص {len(entries)} سهم...")
    triggered = bot.monitor_pullback(wl)
    if triggered:
        msg = ("🚨 <b>تنبيه ارتداد فوري</b>\n\n"
               + bot.build_pullback_section([], triggered)
               + "\n\n" + bot.FOOTER)
        bot.send_telegram(msg)
        bot.save_watchlist(wl)
        try:
            bot.git_save([bot.WATCH_FILE])   # تثبيت حالة «وصل الدعم»
        except Exception as e:
            bot.log(f"⚠️ حفظ الحالة: {e}")
        bot.log(f"🚨 تنبيه: {len(triggered)} سهم وصل الدعم.")
    else:
        bot.log("مراقبة الارتداد: لا سهم وصل الدعم بعد.")


if __name__ == "__main__":
    main()
