# -*- coding: utf-8 -*-
"""
==========================================================
🔥 رادار الانطلاق اللحظي (Ignition Radar) — عامل جلسة حي
==========================================================
النقلة النوعية من اشتراك Polygon (بعد أن أثبت T-ACC أن **الاختيار** عند القاع
مستحيل): لا نتنبّأ بأيّ زنبرك ينفجر — بل نراقب القائمة المؤهّلة **كلها لحظيًّا**
ونمسك **لحظة الاشتعال** (رد فعل لا تنبّؤ: الحجم والسعر حقيقيان، والتدفق يؤكّد).
يسبق أي بوت على Yahoo بـ15-25 دقيقة. أسرع تنفيذ لحافة **التوقيت** المثبتة.

عامل **جلسة واحدة**: يلفّ كل ~45ث من الافتتاح حتى الإغلاق (جوب واحد طويل، لا كرون
كل دقيقة). **إشعار فقط — لا يحفظ القائمة** (دِدوب بالذاكرة، صفر سباق حالة).
**فاشل-آمن مطلق:** بلا مفتاح Polygon = لا عمل (يخرج فورًا). `IGNITION_PLAN.md`.

التشغيل: python ignition_live.py   (workflow: ignition.yml، من الافتتاح)
متغيّرات اختيارية: IGNITION_INTERVAL (ثوانٍ، افتراضي 45) · IGNITION_END_UTC (HH:MM،
افتراضي 20:00 = إغلاق ناسداك).
"""
import os
import time

try:
    import Super_stock as bot
except ImportError:
    import super_stock as bot


def _deadline():
    """نهاية الجلسة (UTC): IGNITION_END_UTC إن ضُبط، وإلا **إغلاق ناسداك الفعلي**
    المشتق من توقيت نيويورك (⑤ إصلاح تدقيق 2026-07-12: كان 20:00 UTC مثبّتًا =
    صيفي فقط؛ شتاءً الإغلاق 21:00 فكان الرادار يتوقف ساعة قبل الإغلاق)."""
    end = os.environ.get("IGNITION_END_UTC", "").strip()
    now = bot.dt.datetime.utcnow()
    if end:
        try:
            hh, mm = (int(x) for x in end.split(":"))
            return now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        except Exception:
            pass
    _close = bot.market_session_now()["close"]           # دقائق-UTC (يتشتّى آليًا)
    return now.replace(hour=_close // 60, minute=_close % 60,
                       second=0, microsecond=0)


def main():
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        bot.log("⚠️ رادار الانطلاق: لا مفتاح Polygon — لا عمل (فاشل-آمن).")
        return
    wl = bot.load_watchlist()
    active = [s for s in wl.get("stocks", []) if s.get("status") == "active"]
    if not active:
        bot.log("رادار الانطلاق: القائمة فارغة — لا شيء نراقبه.")
        return
    interval = max(15, int(os.environ.get("IGNITION_INTERVAL", "45") or 45))
    # ⑤ انتظر الافتتاح الفعلي (شتاءً كرون 13:35 يسبق الافتتاح 14:30 بساعة — كان
    # يلفّ أعمى على سوق مغلق ويحرق ميزانية الجوب). نوم واحد مقيَّد بساعة.
    try:
        _open_m = bot.market_session_now()["open"]
        _now = bot.dt.datetime.utcnow()
        _gap = _open_m - (_now.hour * 60 + _now.minute)
        if 0 < _gap <= 70:
            bot.log(f"⏳ قبل الافتتاح — انتظار {_gap} دقيقة حتى الجرس.")
            time.sleep(_gap * 60)
    except Exception:
        pass
    deadline = _deadline()
    bot.log(f"🔥 رادار الانطلاق: {len(active)} زنبرك · كل {interval}ث حتى "
            f"{deadline.strftime('%H:%M')} UTC.")
    loops = 0
    max_loops = 2000                       # حارس ضد اللف اللانهائي (≈25س عند 45ث)
    session_fires, seen = [], set()        # 📏 جمع إطلاقات الجلسة لتسجيلها بالنهاية
    session_day = bot.dt.date.today().isoformat()
    while bot.dt.datetime.utcnow() < deadline and loops < max_loops:
        loops += 1
        today = bot.dt.date.today().isoformat()
        try:
            rows = bot.scan_ignition(wl, today)
        except Exception as e:
            rows = []
            bot.log(f"⚠️ رادار الانطلاق (دورة {loops}): {e}")
        if rows:
            try:
                bot.send_telegram(bot.build_ignition_alert(rows) + "\n\n" + bot.FOOTER)
                bot.log(f"🔥 {len(rows)} انطلاق: "
                        + ", ".join(r[0]["symbol"] for r in rows))
            except Exception as e:
                bot.log(f"⚠️ إرسال تنبيه الانطلاق: {e}")
            for r in rows:                 # جمع فريد (دِدوب مرة/سهم/جلسة)
                if r[0]["symbol"] not in seen:
                    seen.add(r[0]["symbol"])
                    session_fires.append(r)
        time.sleep(interval)
    # 📏 حلقة القياس: سجّل إطلاقات الجلسة بسجلّ دائم + احفظه بالريبو (فاشل-آمن — لا
    # يعيق إنهاء الرادار). أداة التطوير تقرأه الجمعة وتحكم على الالتقاط/الإنذار الكاذب.
    if session_fires:
        try:
            n_rec = bot.record_ignition_fires(session_fires, session_day)
            if n_rec:
                bot.git_save([bot.IGNITION_LOG_FILE])
                bot.log(f"📝 سُجِّل {n_rec} إطلاق في سجلّ القياس.")
        except Exception as e:
            bot.log(f"⚠️ حفظ سجلّ الانطلاق: {e}")
    bot.log(f"رادار الانطلاق: انتهت الجلسة ({loops} دورة).")


if __name__ == "__main__":
    main()
