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


def _load_press_state(path: str = "press_radar_state.json") -> dict:
    """ذاكرةُ رادار الضغط (قراءةٌ فقط) — منها نأخذ مَن نُبِّه عليه حديثًا فيدخل
    كونَ المتابعة الحيّة. **فاشلٌ-آمن ⇒ `{}`** (غيابُه يُنقص الكونَ ولا يُسقط شيئًا).
    🔒 ولا يُكتَب فيه هنا إطلاقًا — الرادارُ وحده يملكه."""
    try:
        with open(path, encoding="utf-8") as fh:
            d = bot.json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:                                            # noqa: BLE001
        return {}


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
    # (3) 🎯 «هنا الدخول» — متابعةٌ حيّةٌ لِـ**كلّ** أسهمنا (الترشيح · الارتداد ·
    #     رادار الضغط · تحت المتابعة · متابعة الصيّاد) عن ثلاثية فيصل على فريم
    #     الدقيقة، **قبل الافتتاح وبعده** (حركةُ WETO في صورته كانت بريماركت).
    #     أمرُ المالك 2026-08-16: «يوصلنا تحديث مباشرة حسب دخول المضارب … عشان
    #     اقدر ادخل مع المضارب لو ما تمركزت في السهم من قبل».
    #     🔒 حارسٌ مطلق: قسمٌ إشعاريّ لا يجوز أن يُسقط المراقبة · وبلا مفتاح
    #     Polygon = صفرُ عمل (‏`polygon_minute_bars` ترجع None فلا مطابق).
    _op_seen, _op_rows = None, []
    try:
        _op_today = bot.dt.date.today().isoformat()
        _uni, _cut = bot.live_watch_universe(
            wl, near=bot.load_near_watch(), press=_load_press_state(),
            hunter=bot.load_hunter_watch(), today_iso=_op_today)
        if _cut:
            # ⚠️ **يُعلَن بعدده** (قاعدة «لا قصَّ صامتًا») — والمقصوصُ هو الأبعدُ
            #    عن التنفيذ بترتيب الأولوية المُعلَن، لا اختيارٌ عشوائيّ.
            bot.log(f"ℹ️ كون المتابعة الحيّة: قُصّ {_cut} فوق السقف "
                    f"{bot.LIVE_WATCH_CAP} (مُعلَن لا صامت).")
        if _uni:
            _op_seen = bot.load_op_entry_state()
            _op_rows = bot.scan_operator_entry(_uni, _op_today, seen=_op_seen)
            bot.log(f"🎯 متابعة الدخول: فُحص {len(_uni)} سهمًا · "
                    f"مطابق {len(_op_rows)}.")
            if _op_rows:
                alerts.append(bot.build_operator_entry_alert(_op_rows))
    except Exception as e:                                       # noqa: BLE001
        bot.log(f"⚠️ متابعة «هنا الدخول»: {e}")
    if not alerts:
        return
    # احفظ الحالة (triggered + sweep_alert_date) **قبل** الإرسال — لو فشل الإرسال
    # أو انهارت العملية بعده لا تتكرّر التنبيهات (نفس ضمان المسار الأصلي).
    bot.save_watchlist(wl)
    # 🎯 ودِدوبُ «هنا الدخول» يُحفَظ بنفس المقايضة (حفظٌ قبل الإرسال يمنع التكرار)
    #    — ويُعاد عند الإخفاق أدناه تمامًا كأختام المراقب.
    _op_files = []
    if _op_rows and _op_seen is not None:
        if bot.save_op_entry_state(_op_seen):
            _op_files = [bot.OP_ENTRY_STATE_FILE]
    try:
        bot.git_save([bot.WATCH_FILE] + _op_files)
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
        # 🎯 والدِدوبُ الجديد يُنزَع فتُعاد محاولةُ «هنا الدخول» أيضًا — وإلّا
        #    استُهلك ختمُ السهم على رسالةٍ لم تصل (عينُ عيب 2026-07-27).
        if _op_rows and _op_seen is not None:
            for _r, _v, _o in _op_rows:
                _op_seen.pop(_r.get("symbol"), None)
            bot.save_op_entry_state(_op_seen)
        bot.save_watchlist(wl)
        try:
            bot.git_save([bot.WATCH_FILE] + _op_files)
        except Exception as e:                                   # noqa: BLE001
            bot.log(f"⚠️ استرجاع الأختام: {e}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
