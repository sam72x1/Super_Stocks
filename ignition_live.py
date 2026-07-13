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

import ignition_measurement as measure   # 🔬 E2-A: قياس ظلّي (مطفأ افتراضيًّا)


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


def _iso(d):
    """datetime (naive UTC) → «YYYY-MM-DDTHH:MM:SSZ» (يطابق مُحلّل المسجّل). فاشل-آمن → None."""
    try:
        return d.replace(second=0, microsecond=0).isoformat() + "Z"
    except Exception:
        return None


def _session_window(t0=None):
    """🔬 §2a: نافذة الجلسة (UTC) + **الموعد النهائي الفعلي للّف**. يرجّع dict:
    `open`/`close` (من `market_session_now`، يتصيّف/يتشتّى آليًا) · `deadline` (الأبكر من:
    الإغلاق الفعلي · بدء الجوب + `IGNITION_MAX_RUNTIME_MIN` · `IGNITION_END_UTC` الصريح) ·
    `reason`. **قيد سقف رنر GitHub (6 ساعات):** جلسة 6.5س لا تُغطّى بجوب واحد فالحدّ
    الأدنى يضمن `finalize` رشيقًا **قبل** قتل الجوب (وإلّا لا session.json نظيف). الإغلاق
    الحقيقي يُسجَّل في `session.json` (expected_close) + علم «انتهت قبل الإغلاق»
    (`_compute_close_gap`) فالتغطية الجزئية صريحة لا صامتة. `t0` = بدء الجوب (يُحقَن للاختبار)."""
    now = t0 or bot.dt.datetime.utcnow()
    # مرّر نفس اللحظة (aware) لـmarket_session_now فالافتتاح/الإغلاق يطابقان تاريخ الموعد
    # (يتصيّف/يتشتّى بنفس اليوم) — وقابل للاختبار بحقن t0.
    now_aware = now if now.tzinfo else now.replace(tzinfo=bot.dt.timezone.utc)
    sess = bot.market_session_now(now_aware)

    def _at(mins):
        return now.replace(hour=(mins // 60) % 24, minute=mins % 60, second=0, microsecond=0)
    open_dt, close_dt = _at(sess["open"]), _at(sess["close"])
    deadline, reason = close_dt, "market_close"
    mr = os.environ.get("IGNITION_MAX_RUNTIME_MIN", "").strip()
    if mr:
        try:
            cap = now + bot.dt.timedelta(minutes=int(mr))   # نسبةً لبدء الجوب (لا بعد النوم)
            if cap < deadline:
                deadline, reason = cap, "max_runtime_cap"
        except Exception:
            pass
    end = os.environ.get("IGNITION_END_UTC", "").strip()     # تجاوز يدوي صريح (يحكم)
    if end:
        try:
            hh, mm = (int(x) for x in end.split(":"))
            deadline, reason = now.replace(hour=hh, minute=mm, second=0, microsecond=0), "env_override"
        except Exception:
            pass
    return {"open": open_dt, "close": close_dt, "deadline": deadline, "reason": reason}


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
    t0 = bot.dt.datetime.utcnow()          # 🔬 §2a: بدء الجوب (مرجع سقف زمن التشغيل)
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
    # 🔬 §2a: الموعد النهائي = الأبكر من (الإغلاق الفعلي · بدء الجوب + سقف التشغيل ·
    # IGNITION_END_UTC الصريح). الإغلاق المتوقّع يُسجَّل بالقياس فالتغطية الجزئية صريحة.
    window = _session_window(t0)
    deadline = window["deadline"]
    bot.log(f"🔥 رادار الانطلاق: {len(active)} زنبرك · كل {interval}ث حتى "
            f"{deadline.strftime('%H:%M')} UTC (إغلاق متوقّع {window['close'].strftime('%H:%M')} · "
            f"سبب={window['reason']}).")
    loops = 0
    max_loops = 2000                       # حارس ضد اللف اللانهائي (≈25س عند 45ث)
    session_fires, seen = [], set()        # 📏 جمع إطلاقات الجلسة لتسجيلها بالنهاية
    session_day = bot.dt.date.today().isoformat()
    # 🔬 E2-A: مسجّل القياس الظلّي (اختياري · `E2_MEASUREMENT=1`). **مطفأ = trace=None = سلوك
    # الرادار حرفيًّا بت-بت.** فاشل-آمن: أي خطأ تهيئة = نواصل بلا قياس. لا يغيّر تنبيهًا/عتبة.
    recorder = None
    if os.environ.get("E2_MEASUREMENT", "").strip() == "1":
        try:
            recorder = measure.IgnitionMeasurementRecorder(
                session_day, write_repo_index=True,
                meta={"source_commit": os.environ.get("GITHUB_SHA", "").strip() or None,
                      "workflow_run_id": os.environ.get("GITHUB_RUN_ID", "").strip() or None,
                      "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "").strip() or None,
                      "interval_seconds": interval,
                      # 🔬 §2a: الافتتاح/الإغلاق المتوقّعان + الموعد الفعلي وسببه (لعلم «انتهت
                      # قبل الإغلاق» + تدقيق المدقّق). الإغلاق الحقيقي مرجعُ التغطية الصريحة.
                      "expected_open_iso": _iso(window["open"]),
                      "expected_close_iso": _iso(window["close"]),
                      "deadline_iso": _iso(window["deadline"]),
                      "deadline_reason": window["reason"]})
            bot.log("🔬 E2: القياس الظلّي مُفعَّل (لا يغيّر أي تنبيه/عتبة/اختيار).")
        except Exception as e:
            bot.log(f"⚠️ E2: تعذّر تهيئة القياس ({e}) — نواصل بلا قياس.")
            recorder = None
    _trace = recorder.trace if recorder is not None else None
    termination = "normal"
    try:
        while bot.dt.datetime.utcnow() < deadline and loops < max_loops:
            loops += 1
            if recorder is not None:
                recorder.loop_start()
            today = bot.dt.date.today().isoformat()
            # ⑧ تحديث القائمة من origin/main كل ~5 دقائق (7 دورات × 45ث): سهم شُطب
            # بدفعة المراقب يختفي من الرادار بدل «ادخل الآن» على مشطوب. فاشل-آمن.
            if loops % 7 == 0:
                _new = _fresh_watchlist(wl)
                if _new:
                    wl = _new
            try:
                rows = bot.scan_ignition(wl, today, trace=_trace)
            except Exception as e:
                rows = []
                bot.log(f"⚠️ رادار الانطلاق (دورة {loops}): {e}")
            if rows:
                if recorder is not None:
                    recorder.telegram_attempt(rows)
                try:
                    bot.send_telegram(bot.build_ignition_alert(rows) + "\n\n" + bot.FOOTER)
                    bot.log(f"🔥 {len(rows)} انطلاق: "
                            + ", ".join(r[0]["symbol"] for r in rows))
                    if recorder is not None:
                        recorder.telegram_success(rows)
                except Exception as e:
                    bot.log(f"⚠️ إرسال تنبيه الانطلاق: {e}")
                    if recorder is not None:
                        recorder.telegram_failure(rows, error_type=type(e).__name__)
                for r in rows:                 # جمع فريد (دِدوب مرة/سهم/جلسة)
                    if r[0]["symbol"] not in seen:
                        seen.add(r[0]["symbol"])
                        session_fires.append(r)
            if recorder is not None:
                recorder.loop_end()
            time.sleep(interval)
        # 🔬 §2b: بعد اللف الطبيعي، أكمِل مسار الدقيقة لكل رمز مُنبَّه من لحظة الاشتعال حتى
        # نهاية الجلسة (الرادار يتوقّف عن جلبه بعد التنبيه — دِدوب — فتُفقَد الحركة اللاحقة
        # اللازمة لتحليل النتيجة). نافذة يوم كامل · فاشل-آمن · لا يمسّ التنبيه/الاختيار.
        if recorder is not None:
            try:
                n_bf = recorder.backfill_emitted(
                    lambda sym: bot.polygon_minute_bars(sym, minutes=480))
                if n_bf:
                    bot.log(f"🔬 E2: رُدم مسار الدقيقة لـ{n_bf} رمز مُنبَّه حتى نهاية الجلسة.")
            except Exception as e:
                bot.log(f"⚠️ E2: ردم المسار البعدي ({e})")
    except Exception as e:                 # 🔬 E2 §21.5: لا نفقد الجلسة عند انقطاع غير متوقّع
        termination = "exception"
        bot.log(f"⚠️ رادار الانطلاق: انقطاع غير متوقّع ({type(e).__name__}: {e})")
    finally:
        if recorder is not None:           # finalize في finally = crash-safe (يكتب حتى عند الانقطاع)
            try:
                recorder.finalize(termination=termination)
            except Exception as e:
                bot.log(f"⚠️ E2: finalize ({e})")
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
        # 🔬 E2: الملفّان الصغيران القابلان للدفع فقط (الخام e2_measurement/ يبقى artifact).
        if recorder is not None:
            for _f in ("ignition_e2_summary.json", "ignition_e2_session_index.json"):
                if os.path.exists(_f):
                    _save_files.append(_f)
        if _save_files:
            bot.git_save(_save_files)
    except Exception as e:
        bot.log(f"⚠️ حفظ سجلّ الانطلاق: {e}")
    bot.log(f"رادار الانطلاق: انتهت الجلسة ({loops} دورة).")


if __name__ == "__main__":
    main()
