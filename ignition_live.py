# -*- coding: utf-8 -*-
"""
==========================================================
🔥 رادار الانطلاق اللحظي (Ignition Radar) — عامل جلسة حي
==========================================================
النقلة النوعية من اشتراك Polygon (بعد أن أثبت T-ACC أن **الاختيار** عند القاع
مستحيل): لا نتنبّأ بأيّ زنبرك ينفجر — بل نراقب القائمة المؤهّلة **كلها لحظيًّا**
ونمسك **لحظة الاشتعال** (رد فعل لا تنبّؤ: الحجم والسعر حقيقيان، والتدفق يؤكّد).
يسبق أي بوت على Yahoo بـ15-25 دقيقة. أسرع تنفيذ لفرضية **التوقيت اللحظي** (فرضية بحثية
ذات أولوية — **غير مثبتة حتى الآن**؛ E2 يقيسها).

عامل **جلسة واحدة**: يلفّ كل ~45ث من الافتتاح حتى الإغلاق (جوب واحد طويل، لا كرون
كل دقيقة). **إشعار فقط — لا يحفظ القائمة** (دِدوب بالذاكرة، صفر سباق حالة).
**فاشل-آمن مطلق:** بلا مفتاح Polygon = لا عمل (يخرج فورًا). `IGNITION_PLAN.md`.

التشغيل: python ignition_live.py   (workflow: ignition.yml، من الافتتاح)
متغيّرات اختيارية: IGNITION_INTERVAL (ثوانٍ، افتراضي 45) · IGNITION_END_UTC (HH:MM،
افتراضي 20:00 = إغلاق ناسداك).
"""
import json
import os
import subprocess
import time

try:
    import Super_stock as bot
except ImportError:
    import super_stock as bot


def _fresh_watchlist(cur_wl, runner=None):
    """⑧ (إصلاح تدقيق 2026-07-12): يجلب أحدث قائمة من `origin/main` — الرادار يعمل
    على **رنر منفصل** عن مراقب الارتداد، فدفعات المراقب (شطب ستوب مثلًا) لا تصل
    ملفه المحلي أبدًا؛ كان يلفّ ~6 ساعات على لقطة مجمَّدة وقد يصرخ «ادخل الآن»
    على سهم شُطب قبل ساعات. (إعادة قراءة الملف المحلي — إصلاح تقرير التدقيق
    المقترح — لا تكفي لنفس السبب.) ينقل أختام دِدوب الجلسة (`ignition_alert`)
    من النسخة الحالية للجديدة (الرادار لا يحفظ — الأختام بالذاكرة فقط، وبدون
    النقل يُعاد إطلاق تنبيه منفَّذ). `runner` محقون للاختبار بلا شبكة/git.
    **فاشل-آمن → None** (نواصل على آخر نسخة = سلوك اليوم)."""
    run = runner or subprocess.run
    try:
        run(["git", "fetch", "origin", "main", "-q"],
            capture_output=True, timeout=60)
        r2 = run(["git", "show", "FETCH_HEAD:weekly_watchlist.json"],
                 capture_output=True, timeout=30)
        if getattr(r2, "returncode", 1) != 0 or not getattr(r2, "stdout", None):
            return None
        new_wl = json.loads(r2.stdout.decode("utf-8"))
        if not isinstance(new_wl, dict) or not new_wl.get("stocks"):
            return None
        stamps = {s.get("symbol"): s.get("ignition_alert")
                  for s in (cur_wl or {}).get("stocks", [])
                  if s.get("ignition_alert")}
        for s in new_wl["stocks"]:
            if s.get("symbol") in stamps:
                s["ignition_alert"] = stamps[s["symbol"]]
        return new_wl
    except Exception:
        return None


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
        # ⑧ تحديث القائمة من origin/main كل ~5 دقائق (7 دورات × 45ث): سهم شُطب
        # بدفعة المراقب يختفي من الرادار بدل «ادخل الآن» على مشطوب. فاشل-آمن.
        if loops % 7 == 0:
            _new = _fresh_watchlist(wl)
            if _new:
                wl = _new
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
    # 📏 حلقة القياس: سجّل إطلاقات الجلسة + ⑩ **مقام الالتقاط** (كل أسهم الجلسة
    # ولو صفر إطلاق — بدونه «الالتقاط» غير قابل للحساب) بسجلّ دائم + احفظه بالريبو
    # (فاشل-آمن — لا يعيق إنهاء الرادار). أداة التطوير تقرأهما الجمعة.
    try:
        _save_files = []
        _uni_syms = [s.get("symbol") for s in wl.get("stocks", [])
                     if s.get("status") == "active"]
        if bot.record_ignition_universe(_uni_syms, session_day):
            _save_files.append(bot.IGNITION_UNI_FILE)
        if session_fires:
            n_rec = bot.record_ignition_fires(session_fires, session_day)
            if n_rec:
                _save_files.append(bot.IGNITION_LOG_FILE)
                bot.log(f"📝 سُجِّل {n_rec} إطلاق في سجلّ القياس.")
        if _save_files:
            bot.git_save(_save_files)
    except Exception as e:
        bot.log(f"⚠️ حفظ سجلّ الانطلاق: {e}")
    bot.log(f"رادار الانطلاق: انتهت الجلسة ({loops} دورة).")


if __name__ == "__main__":
    main()
