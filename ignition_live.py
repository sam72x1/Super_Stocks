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

🔬 **الجلسة المجزّأة (ب+ · قرار Codex §2a، `E2_IGNITION_SEGMENTED_ARCH.md`):** سقف رنر
GitHub (6س) < الجلسة (6.5س) فلا يغطّيها جوب واحد. `IGNITION_SEGMENT=open|close` يشغّل
**مقطعًا** بحدوده من **الافتتاح الفعلي** (لا بدء الرنر). المقطع `close` يستعيد أختام الدِدوب
من handoff المقطع السابق (لا تنبيه مكرّر) ويكمل حتى الإغلاق. الـassembler (job3) يدمج.
بلا `IGNITION_SEGMENT` = المسار القديم (جلسة واحدة) — توافق خلفي كامل.

**فاشل-آمن مطلق:** بلا مفتاح Polygon = لا عمل. التشغيل: `python ignition_live.py`.
متغيّرات: IGNITION_INTERVAL(45) · IGNITION_SEGMENT(open|close) · IGNITION_SEGMENT_SPLIT_MIN(195) ·
IGNITION_MAX_RUNTIME_MIN · IGNITION_HANDOFF_IN/OUT · E2_MEASUREMENT.
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

SEGMENT_SPLIT_MIN_DEFAULT = 195           # حدّ المقطعين من الافتتاح (~3س15د) — الجزآن < 6س رنر
MAX_RUNTIME_SAFETY_DEFAULT = 340          # سقف أمان (نادرًا يبلغ) لضمان finalize قبل قتل الجوب


def _fresh_watchlist(cur_wl, runner=None):
    """⑧ (إصلاح تدقيق 2026-07-12): يجلب أحدث قائمة من `origin/main` — الرادار يعمل
    على **رنر منفصل** عن مراقب الارتداد، فدفعات المراقب (شطب ستوب مثلًا) لا تصل
    ملفه المحلي أبدًا؛ كان يلفّ ~6 ساعات على لقطة مجمَّدة وقد يصرخ «ادخل الآن»
    على سهم شُطب قبل ساعات. ينقل أختام دِدوب الجلسة (`ignition_alert`) من النسخة
    الحالية للجديدة (الرادار لا يحفظ — الأختام بالذاكرة). `runner` محقون للاختبار.
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


def _fetch_head_sha(runner=None):
    """🔬 P1.4: commit `weekly_watchlist.json` على origin/main (بعد fetch) — للـprovenance.
    فاشل-آمن → None."""
    run = runner or subprocess.run
    try:
        r = run(["git", "rev-parse", "FETCH_HEAD"], capture_output=True, timeout=15)
        if getattr(r, "returncode", 1) == 0 and getattr(r, "stdout", None):
            return r.stdout.decode("utf-8").strip() or None
    except Exception:
        pass
    return None


def _iso(d):
    """datetime (naive UTC) → «YYYY-MM-DDTHH:MM:SSZ» (يطابق مُحلّل المسجّل). فاشل-آمن → None."""
    try:
        return d.replace(second=0, microsecond=0).isoformat() + "Z"
    except Exception:
        return None


def _segment_window(role, t0=None):
    """🔬 (ب+/P0-1/P1.1): نافذة المقطع (UTC) **بحدود من الافتتاح الفعلي** (لا بدء الرنر).
    يرجّع dict: open/close/split (توقيت السوق) · segment_start/end (نافذة المقطع المقصودة) ·
    deadline (الأبكر من segment_end · t0+max_runtime · IGNITION_END_UTC) · reason · role · split_min.
    role: `open`=[open, open+split] · `close`=[open+split, close] · غيره=جلسة واحدة [open, close].
    max_runtime = سقف أمان نسبةً لبدء الجوب (نادرًا يبلغ) يضمن finalize رشيقًا. `t0` يُحقَن للاختبار."""
    now = t0 or bot.dt.datetime.utcnow()
    now_aware = now if now.tzinfo else now.replace(tzinfo=bot.dt.timezone.utc)
    sess = bot.market_session_now(now_aware)
    split_min = SEGMENT_SPLIT_MIN_DEFAULT
    try:
        split_min = int(os.environ.get("IGNITION_SEGMENT_SPLIT_MIN", "").strip()
                        or SEGMENT_SPLIT_MIN_DEFAULT)
    except Exception:
        pass

    def _at(mins):
        return now.replace(hour=(mins // 60) % 24, minute=mins % 60, second=0, microsecond=0)
    open_dt, close_dt = _at(sess["open"]), _at(sess["close"])
    split_dt = _at(sess["open"] + split_min)
    if role == "open":
        seg_start, seg_end = open_dt, split_dt
    elif role == "close":
        seg_start, seg_end = split_dt, close_dt
    else:
        seg_start, seg_end = open_dt, close_dt
    deadline, reason = seg_end, ("segment_end" if role else "market_close")
    mr = os.environ.get("IGNITION_MAX_RUNTIME_MIN", "").strip()
    try:
        if mr:
            cap = now + bot.dt.timedelta(minutes=int(mr))   # نسبةً لبدء الجوب
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
    return {"open": open_dt, "close": close_dt, "split": split_dt,
            "segment_start": seg_start, "segment_end": seg_end,
            "deadline": deadline, "reason": reason, "role": role or "single", "split_min": split_min}


def _load_handoff(path):
    """🔬 (ب+): يحمّل handoff المقطع السابق (فاشل-آمن → None)."""
    try:
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                ho = json.load(fh)
            return ho if isinstance(ho, dict) else None
    except Exception:
        pass
    return None


def _apply_handoff_dedup(wl, handoff, today_iso):
    """🔬 (ب+): يستعيد أختام الدِدوب من handoff المقطع السابق → **لا تنبيه مكرّر** عبر
    المقطعين (صون إنتاجي · طبقة توقيت الرادار لا الاختيار). فاشل-آمن → 0. يرجّع العدد."""
    n = 0
    try:
        alerted = set((handoff or {}).get("alerted_symbols") or [])
        for s in wl.get("stocks", []):
            if s.get("symbol") in alerted:
                s["ignition_alert"] = today_iso
                n += 1
    except Exception:
        pass
    return n


def _write_handoff(path, ho):
    """🔬 (ب+): يكتب handoff هذا المقطع (JSON) للـjob التالي. فاشل-آمن."""
    try:
        if not path:
            return False
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(ho, fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        return True
    except Exception:
        return False


def main():
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        bot.log("⚠️ رادار الانطلاق: لا مفتاح Polygon — لا عمل (فاشل-آمن).")
        return
    role = os.environ.get("IGNITION_SEGMENT", "").strip().lower()
    if role not in ("open", "close"):
        role = ""                          # جلسة واحدة (توافق خلفي)
    wl = bot.load_watchlist()
    active = [s for s in wl.get("stocks", []) if s.get("status") == "active"]
    if not active:
        bot.log("رادار الانطلاق: القائمة فارغة — لا شيء نراقبه.")
        return
    interval = max(15, int(os.environ.get("IGNITION_INTERVAL", "45") or 45))
    t0 = bot.dt.datetime.utcnow()          # بدء الجوب (مرجع سقف زمن التشغيل)
    session_day = bot.dt.date.today().isoformat()
    # المقطع `close` يبدأ فورًا (السوق مفتوح مسبقًا)؛ open/single ينتظران الجرس.
    if role != "close":
        try:
            _open_m = bot.market_session_now()["open"]
            _now = bot.dt.datetime.utcnow()
            _gap = _open_m - (_now.hour * 60 + _now.minute)
            if 0 < _gap <= 70:
                bot.log(f"⏳ قبل الافتتاح — انتظار {_gap} دقيقة حتى الجرس.")
                time.sleep(_gap * 60)
        except Exception:
            pass
    window = _segment_window(role, t0)
    deadline = window["deadline"]
    # 🔬 (ب+): استعادة أختام الدِدوب من handoff المقطع السابق (المقطع close فقط) — لا تنبيه مكرّر.
    handoff_in = None
    seen = set()
    if role == "close":
        handoff_in = _load_handoff(os.environ.get("IGNITION_HANDOFF_IN", "").strip())
        if handoff_in:
            _nd = _apply_handoff_dedup(wl, handoff_in, session_day)
            seen |= set(handoff_in.get("alerted_symbols") or [])
            bot.log(f"🔁 استعادة {_nd} ختم دِدوب من المقطع السابق (لا تنبيه مكرّر).")
    bot.log(f"🔥 رادار الانطلاق [{window['role']}]: {len(active)} زنبرك · كل {interval}ث حتى "
            f"{deadline.strftime('%H:%M')} UTC (نافذة {window['segment_start'].strftime('%H:%M')}–"
            f"{window['segment_end'].strftime('%H:%M')} · إغلاق {window['close'].strftime('%H:%M')} · "
            f"سبب={window['reason']}).")
    loops = 0
    max_loops = 2000                       # حارس ضد اللف اللانهائي
    session_fires = []
    # 🔬 E2-A: مسجّل القياس الظلّي (اختياري · `E2_MEASUREMENT=1`). **مطفأ = trace=None = بت-بت.**
    recorder = None
    if os.environ.get("E2_MEASUREMENT", "").strip() == "1":
        try:
            _prev_sha = None                # سلسلة sha للمقطع السابق (تحقّق التسلسل)
            if handoff_in:
                try:
                    _prev_sha = json.dumps(handoff_in.get("raw_files_sha256") or {}, sort_keys=True)
                except Exception:
                    _prev_sha = None
            recorder = measure.IgnitionMeasurementRecorder(
                session_day, segment=(role or None), write_repo_index=(role == ""),
                meta={"source_commit": os.environ.get("GITHUB_SHA", "").strip() or None,
                      "workflow_run_id": os.environ.get("GITHUB_RUN_ID", "").strip() or None,
                      "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "").strip() or None,
                      "interval_seconds": interval,
                      "expected_open_iso": _iso(window["open"]),
                      "expected_close_iso": _iso(window["close"]),
                      "expected_segment_start_iso": _iso(window["segment_start"]),
                      "expected_segment_end_iso": _iso(window["segment_end"]),
                      "deadline_iso": _iso(window["deadline"]),
                      "deadline_reason": window["reason"],
                      "watchlist_commit_start": os.environ.get("GITHUB_SHA", "").strip() or None,
                      "previous_segment_sha256": _prev_sha})
            bot.log("🔬 E2: القياس الظلّي مُفعَّل (لا يغيّر أي تنبيه/عتبة/اختيار).")
        except Exception as e:
            bot.log(f"⚠️ E2: تعذّر تهيئة القياس ({e}) — نواصل بلا قياس.")
            recorder = None
    _trace = recorder.trace if recorder is not None else None
    _fm = bot.polygon_nbbo if recorder is not None else None    # 🔬 P1.3: NBBO قياسي مستقلّ
    termination = "normal"
    _last_start = None
    try:
        while bot.dt.datetime.utcnow() < deadline and loops < max_loops:
            loops += 1
            _loop_start = time.time()
            if recorder is not None:
                recorder.loop_start()
            today = bot.dt.date.today().isoformat()
            if loops % 7 == 0:                 # تحديث القائمة من origin/main كل ~5 دقائق
                _new = _fresh_watchlist(wl)
                if _new:
                    wl = _new
                    if recorder is not None:
                        recorder.set_watchlist_commit(_fetch_head_sha())
            try:
                rows = bot.scan_ignition(wl, today, trace=_trace, fetch_measure_nbbo=_fm)
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
            if recorder is not None:           # 🔬 P1.6: قياس أثر الأداة نفسها
                _now_s = time.time()
                _lag = (int((_loop_start - _last_start) * 1000 - interval * 1000)
                        if _last_start is not None else None)
                recorder.loop_end(schedule_lag_ms=_lag,
                                  loop_duration_ms=int((_now_s - _loop_start) * 1000))
            _last_start = _loop_start
            time.sleep(interval)
        # 🔬 §2b/P0-2: **الجلسة الواحدة (القديمة) فقط** تردم هنا. الجلسة المجزّأة تؤجّل الردم
        # النهائي للـassembler **بعد الإغلاق** (بارات ما بعد المقطع لم توجد بعد وقت اللف).
        if recorder is not None and role == "":
            try:
                recorder.backfill_emitted(lambda sym: bot.polygon_minute_bars(sym, minutes=480))
            except Exception as e:
                bot.log(f"⚠️ E2: ردم المسار البعدي ({e})")
    except Exception as e:                 # 🔬 E2 §21.5: لا نفقد الجلسة عند انقطاع غير متوقّع
        termination = "exception"
        bot.log(f"⚠️ رادار الانطلاق: انقطاع غير متوقّع ({type(e).__name__}: {e})")
    finally:
        if recorder is not None:           # finalize في finally = crash-safe
            try:
                recorder.finalize(termination=termination)
            except Exception as e:
                bot.log(f"⚠️ E2: finalize ({e})")
    # 🔬 (ب+): اكتب handoff هذا المقطع (أختام الدِدوب دائمًا + إثراء E2 لو مُفعَّل).
    if role or os.environ.get("IGNITION_HANDOFF_OUT", "").strip():
        ho = dict((recorder.export_handoff() if recorder is not None else {}) or {})
        ho.setdefault("session_date", session_day)
        ho["segment"] = window["role"]
        ho["alerted_symbols"] = sorted(set(ho.get("alerted_symbols") or []) | seen)
        _out = os.environ.get("IGNITION_HANDOFF_OUT", "").strip() or ("handoff_%s.json" % window["role"])
        if _write_handoff(_out, ho):
            bot.log(f"🔁 handoff [{window['role']}] → {_out} ({len(ho['alerted_symbols'])} مُنبَّه).")
    # 📏 سجلّ الإطلاقات + مقام الالتقاط + الملفّان القابلان للدفع (الجلسة الواحدة فقط —
    # المجزّأة يدفعها الـassembler بعد الدمج). فاشل-آمن.
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
        if recorder is not None and role == "":
            for _f in ("ignition_e2_summary.json", "ignition_e2_session_index.json"):
                if os.path.exists(_f):
                    _save_files.append(_f)
        if _save_files:
            bot.git_save(_save_files)
    except Exception as e:
        bot.log(f"⚠️ حفظ سجلّ الانطلاق: {e}")
    bot.log(f"رادار الانطلاق [{window['role']}]: انتهت الجلسة ({loops} دورة).")


if __name__ == "__main__":
    main()
