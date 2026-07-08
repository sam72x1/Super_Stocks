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
    """نهاية الجلسة (UTC): IGNITION_END_UTC أو 20:00 (إغلاق ناسداك). كود بوت عادي —
    utcnow متاح (ليس سكربت workflow)."""
    end = os.environ.get("IGNITION_END_UTC", "20:00").strip()
    try:
        hh, mm = (int(x) for x in end.split(":"))
    except Exception:
        hh, mm = 20, 0
    now = bot.dt.datetime.utcnow()
    return now.replace(hour=hh, minute=mm, second=0, microsecond=0)


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
    deadline = _deadline()
    bot.log(f"🔥 رادار الانطلاق: {len(active)} زنبرك · كل {interval}ث حتى "
            f"{deadline.strftime('%H:%M')} UTC.")
    loops = 0
    max_loops = 2000                       # حارس ضد اللف اللانهائي (≈25س عند 45ث)
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
        time.sleep(interval)
    bot.log(f"رادار الانطلاق: انتهت الجلسة ({loops} دورة).")


if __name__ == "__main__":
    main()
