# -*- coding: utf-8 -*-
"""🎯 **«هنا الدخول» — عاملُ جلسةٍ حيّ** (أمرُ المالك 2026-08-16 «سرعة»).

يمسح **كونَ المتابعة الحيّة** (قوائمنا الخمس) كلَّ ‏≈60 ثانية عن **ثلاثية
فيصل على فريم الدقيقة** — صعودٌ أوّل ⟵ رجعَ لنفس الدعم وثبت ⟵ عبرَ الفيواب
صاعدًا — ويرسل «‏🎯 هنا الدخول» أوّلَ ما تكتمل، **قبل الافتتاح وبعده**.

⚖️ **ولماذا عاملُ جلسةٍ لا كرون:** المراقبُ الدوريّ حبيبتُه 15 دقيقة، ونافذةُ
`WETO` في صورة المالك (لمسةُ الدعم ⟶ عبورُ الفيواب) كانت **‏≈10 دقائق** ⇒
الحبيبةُ الخشنة قد تُدخله بعد بدء الحركة بدقائق. وهذا **يكمّله لا يستبدله**:
المراقبُ يبقى شبكةَ أمانٍ للأفتر ولِما يُسقطه GitHub من تشغيلات.

🔒 **إشعارٌ/توقيتٌ فقط:** لا يمسّ فرزًا ولا عضويةَ قائمة ولا عتبة — يقرأ
القوائمَ ويرسل. وبلا `POLYGON_API_KEY` = **صفرُ عمل** (فاشلٌ-آمن).

المقاطع (`OE_SEGMENT`): `pre` قبل الافتتاح · `open` الجلسة · `post` الإغلاق
والأفتر. وكلٌّ يقف عند سقف زمنه أو عند نهاية الجلسة الممتدّة — أيُّهما أبكر.
"""
import json
import os
import subprocess
import time

try:
    import Super_stock as bot
except ImportError:                                              # pragma: no cover
    import super_stock as bot

INTERVAL_DEFAULT = 60          # ثانيةً بين الدورات
MAX_RUNTIME_MIN = 330          # سقفُ أمانٍ تحت حدّ GitHub (‏6 ساعات)
REFRESH_EVERY = 10             # كلَّ ~10 دقائق: تحديثُ القوائم من origin/main
EXT_CLOSE_NY = 20 * 60         # نهايةُ الجلسة الممتدّة (‏20:00 نيويورك)
EXT_OPEN_NY = 4 * 60           # بدءُ الجلسة الممتدّة (‏04:00 نيويورك)


def _log(msg):
    bot.log(msg)


def _ny_minutes(now=None):
    """دقائقُ اليوم بتوقيت نيويورك — **يتصيّف/يتشتّى ذاتيًّا** (لا ثوابت UTC)."""
    try:
        from zoneinfo import ZoneInfo
        n = now or bot.dt.datetime.now(bot.dt.timezone.utc)
        ny = n.astimezone(ZoneInfo("America/New_York"))
        return ny.hour * 60 + ny.minute, ny.date().isoformat()
    except Exception:                                            # noqa: BLE001
        n = now or bot.dt.datetime.now(bot.dt.timezone.utc)
        return (n.hour * 60 + n.minute - 240) % 1440, n.date().isoformat()


def _budget(left_min, raw=None):
    """سقفُ العمل بالدقائق — و`OE_BUDGET_MIN` **يُقصّر ولا يُطيل** (بنيويًّا).

    الحاصلُ = أصغرُ الثلاثة: سقفُ السكربت (‏330) · قيمةُ المفتاح · وما تبقّى من
    الجلسة الممتدّة ⇒ فمهما كبرت القيمةُ لا تتجاوز الجلسةَ ولا سقفَ الجوب.
    وُلد لأن عاملَ جلسةٍ يعمل ‏5.5 ساعة **لا يُمكن فحصُ دخانه**: سجلُّ GitHub
    لا يُنزَّل قبل انتهاء التشغيلة ⇒ ميزةٌ بلا طريقِ إثباتٍ من نقطة النداء الحيّة.
    وتعذّرُ القراءة ⇒ الافتراضُ (فاشلٌ-آمن) لا صفرٌ صامت.
    """
    try:
        cap = int(str(raw or "").strip() or MAX_RUNTIME_MIN)
    except Exception:                                            # noqa: BLE001
        cap = MAX_RUNTIME_MIN
    cap = max(1, min(MAX_RUNTIME_MIN, cap))
    return max(0, min(cap, int(left_min)))


def _no_session(date_iso) -> bool:
    """لا جلسةَ اليوم؟ (عطلةُ سوقٍ **أو** نهايةُ أسبوع) — **فاشل-آمن ⇒ False**.

    🐞 **وسابقتُه عيبٌ حقيقيّ مقيس (2026-08-16):** كان يقرأ `.get("type")`
    و**المفتاحُ الفعليّ `session_type`** ⇒ يُرجع `None` أبدًا ⇒ **الحارسُ ميّتٌ
    منذ ولادته** = «المفتاحُ المتخيَّل» للمرّة الرابعة في هذا المستودع.
    🔴 **وأُضيفت نهايةُ الأسبوع** لأن `market_calendar.is_trading_day` تنصّ
    صراحةً أنها **لا تفحصها** وتتّكل على أن الكرون أيامُ عمل — وهو صحيحٌ
    للكرون **لا للتشغيل اليدويّ**، وهذا عاملٌ يعمل ساعاتٍ لا دقائق.
    """
    try:
        y, m, d = (int(x) for x in str(date_iso).split("-")[:3])
        if bot.dt.date(y, m, d).weekday() >= 5:                   # سبتٌ أو أحد
            return True
        import market_calendar as mc
        return (mc.session_info(date_iso) or {}).get("session_type") == "holiday"
    except Exception:                                            # noqa: BLE001
        return False


def _fetch_state(paths):
    """يجلب أحدثَ نسخةٍ من ملفّات الحالة من `origin/main` — العاملُ على رنرٍ
    منفصل، فدفعاتُ المراقب/الفرز لا تصل نسختَه المحلّية أبدًا.
    **فاشل-آمن:** أيُّ إخفاق ⇒ نُبقي المحلّيّ (سلوكُ اليوم)."""
    out = {}
    try:
        subprocess.run(["git", "fetch", "origin", "main", "-q"],
                       capture_output=True, timeout=60)
    except Exception:                                            # noqa: BLE001
        return out
    for p in paths:
        try:
            r = subprocess.run(["git", "show", f"FETCH_HEAD:{p}"],
                               capture_output=True, timeout=30)
            if r.returncode == 0 and r.stdout:
                out[p] = json.loads(r.stdout.decode("utf-8"))
        except Exception:                                        # noqa: BLE001
            continue
    return out


# 🔗 **قائمةُ الترشيح محفوظةٌ هنا لضمّ سياقِ الفلتر بلا نداءٍ إضافيّ.**
#    ⚖️ ولماذا خاصّيّةُ وحدةٍ لا عنصرٌ خامسٌ في المُرجَع: ثلاثةُ مِجَسّاتٍ تُفكّك
#    مُخرَجَ `_load_universe` **رباعيًّا** (`m0_probe` · `liq_move_probe` ·
#    `gate_probe`) ⇒ تغييرُ عددِ العناصر يكسرها صامتًا. **والقراءةُ هنا فقط.**
_WL = {}


def _load_universe():
    """يبني كونَ المتابعة من **أحدث** نسخةٍ للقوائم الخمس (أو المحلّية عند التعذّر).

    ويحفظ قائمةَ الترشيح في `_WL` ليضمّ الفلترُ سياقَه بلا نداءٍ شبكيٍّ جديد."""
    fresh = _fetch_state(["weekly_watchlist.json", "near_watch.json",
                          "press_radar_state.json", "hunter_watchlist.json",
                          bot.OP_ENTRY_STATE_FILE])
    wl = fresh.get("weekly_watchlist.json") or bot.load_watchlist()
    near = fresh.get("near_watch.json")
    if near is None:
        near = bot.load_near_watch()
    press = fresh.get("press_radar_state.json") or {}
    hunter = fresh.get("hunter_watchlist.json") or bot.load_hunter_watch()
    seen = fresh.get(bot.OP_ENTRY_STATE_FILE)
    if not isinstance(seen, dict):
        seen = bot.load_op_entry_state()
    _WL.clear()
    if isinstance(wl, dict):
        _WL.update(wl)
    uni, cut = bot.live_watch_universe(wl, near, press, hunter)
    # 💰 كونُ السيولة **بلا سقف** — أمرُ المالك «لكل الأسهم اللي تحت متابعة البوت
    #    بلا اي استثناء». والقصُّ في الكون المُسقَّف يبقى لِـ«هنا الدخول» وحده.
    uni_all, _ = bot.live_watch_universe(wl, near, press, hunter, cap=10 ** 9)
    return uni, cut, seen, uni_all


def main():
    if not os.environ.get("POLYGON_API_KEY", "").strip():
        _log("⚠️ «هنا الدخول»: لا مفتاح Polygon — لا عمل (فاشل-آمن).")
        return 0
    role = (os.environ.get("OE_SEGMENT", "").strip().lower() or "full")
    try:
        interval = max(20, int(os.environ.get("OE_INTERVAL", "")
                               or INTERVAL_DEFAULT))
    except Exception:                                            # noqa: BLE001
        interval = INTERVAL_DEFAULT
    t0 = time.time()
    mins, day = _ny_minutes()
    if _no_session(day):
        _log(f"📅 {day} لا جلسةَ سوقٍ اليوم (عطلةٌ أو نهايةُ أسبوع) — لا متابعة.")
        return 0
    # نهايةُ العمل: إغلاقُ الجلسة الممتدّة (‏20:00 نيويورك) أو سقفُ الزمن.
    left_min = max(0, EXT_CLOSE_NY - mins)
    budget = _budget(left_min, os.environ.get("OE_BUDGET_MIN"))
    if budget <= 0:
        _log(f"⏹️ الجلسةُ الممتدّة انتهت (‏{mins // 60:02d}:{mins % 60:02d} "
             "نيويورك) — لا عمل.")
        return 0
    _log(f"🎯 «هنا الدخول» [{role}]: يبدأ عند {mins // 60:02d}:{mins % 60:02d} "
         f"نيويورك · كلَّ {interval}ث · لمدّة {budget} دقيقة.")
    uni, cut, seen, uni_all = _load_universe()
    if cut:
        _log(f"ℹ️ كون المتابعة: قُصّ {cut} فوق السقف {bot.LIVE_WATCH_CAP} "
             "(مُعلَن لا صامت).")
    _log(f"👁️ كون المتابعة: {len(uni)} سهمًا — "
         + " · ".join(f"{k}={sum(1 for r in uni if r['src'] == k)}"
                      for k in bot.LIVE_WATCH_SOURCES))
    _log(f"💰 كونُ السيولة (**بلا استثناء**): {len(uni_all)} سهمًا · خيوط "
         f"{bot.LIQ_WORKERS} · زنادٌ قفزةُ حجمٍ "
         f"{bot.CONFIG['IGNITION_VOL_MULT']}× **وأرضيةُ ${bot.LIQ_MIN_USD:,} "
         f"داخلةً** · تحديثٌ عند تجاوز القمّة · مراحل 1 و"
         + " و".join(str(m) for m in bot.LIQ_STAGE_MINUTES) + " دقيقة")
    loops, fired, errs = 0, 0, 0
    liq_at, liq_cov, liq_hit = 0, 0, 0
    while (time.time() - t0) < budget * 60:
        loops += 1
        if loops % REFRESH_EVERY == 0:
            try:
                uni, _c, _s, uni_all = _load_universe()
                for _k, _v in (_s or {}).items():
                    seen.setdefault(_k, _v)
            except Exception as e:                               # noqa: BLE001
                _log(f"⚠️ تحديثُ الكون (دورة {loops}): {e}")
            _log(f"💰 تغطيةُ السيولة: {liq_cov} قراءةً تراكميًّا من "
                 f"{len(uni_all)} · الموضعُ الآن {liq_at} · {liq_hit} رفعة.")
        try:
            _today = _ny_minutes()[1]
            rows = bot.scan_operator_entry(uni, _today, seen=seen)
        except Exception as e:                                   # noqa: BLE001
            errs += 1
            rows = []
            _log(f"⚠️ المسح (دورة {loops}): {e}")
        if rows:
            _syms = [r[0]["symbol"] for r in rows]
            try:
                ok = bot.send_telegram(
                    bot.build_operator_entry_alert(rows) + "\n\n" + bot.FOOTER)
            except Exception as e:                               # noqa: BLE001
                ok, _ = False, _log(f"⚠️ إرسال «هنا الدخول»: {e}")
            if ok:
                fired += len(rows)
                _log(f"🎯 {len(rows)} دخول: {', '.join(_syms)}")
                # ⚠️ الختمُ **بعد** الإرسال حصرًا (عقدُ «فُحِص وسُلِّم») — والدفعُ
                #    فورًا كي ينجو الدِدوب من موت الرنر وتقرأه المقاطعُ التالية.
                bot.save_op_entry_state(seen)
                try:
                    bot.git_save([bot.OP_ENTRY_STATE_FILE])
                except Exception as e:                           # noqa: BLE001
                    _log(f"⚠️ دفعُ الدِدوب: {e}")
            else:
                for _s in _syms:                 # لم يصل ⇒ يُعاد في الدورة التالية
                    seen.pop(_s, None)
                _log(f"⚠️ تيليجرام رفض «هنا الدخول» ({len(rows)}) — "
                     "نُزع الختمُ لتُعاد المحاولة.")
        # ⏫💰 **التدرّجُ بنصّ المالك**: أوّلُ دقيقةٍ تدخل فيها سيولةٌ ⇒ إشعارٌ فوريّ ·
        #    ثم تحديثٌ بكلّ دقيقة · ثم مجموعُ 5 و30 دقيقة **من لحظة الدخول**.
        #    والمسحُ **متزامنٌ** فيغطّي الكونَ كلَّه في دورةٍ واحدة (‏319 نداءً
        #    تسلسليًّا ‏≈96ث ⇒ يستحيل وعدُ الدقيقة).
        _snap = dict(seen)          # لقطةٌ للرجوع عند رفض تيليجرام (لا كتمَ صامت)
        try:
            _today2 = _ny_minutes()[1]
            lrows, lcov, lsec = bot.scan_liq_stages(
                uni_all, _today2, seen=seen,
                fetch_operator=bot.operator_flow)
            liq_cov += lcov
        except Exception as e:                                   # noqa: BLE001
            errs += 1
            lrows, lcov, lsec = [], 0, 0.0
            _log(f"⚠️ مسحُ السيولة (دورة {loops}): {e}")
        if lcov and (loops % REFRESH_EVERY == 0 or lrows):
            _log(f"💰 التغطية: {lcov} من {len(uni_all)} في {lsec}ث "
                 f"(خيوط {bot.LIQ_WORKERS})")
        # 🎛️ **فلترُ المالك — يقصّ ما يُرسَل ولا يمسّ ما يُفحَص** (قرارُه
        #    2026-08-18 «ابن الفلتر»). ملفٌّ غائبٌ/فارغ ⇒ **بت-بت كما كان**.
        #    🔴 **وحارسٌ حاسم:** الحالةُ تُختَم **بعد الإرسال** في هذا المسار، فلو
        #    كتم الفلترُ كلَّ شيءٍ لَما خُتم شيءٌ ⇒ يُعاد الإشعارُ نفسُه كلَّ دورة.
        #    ⇒ **يُختَم المكتومُ أيضًا** (فُحص وقُرِّر كتمُه عمدًا)، والرجوعُ عند
        #    رفض تيليجرام يقتصر على **المُرسَل** لا على المكتوم.
        _lmuted = []
        if lrows:
            try:
                _cfg = bot.load_alert_filter()
                # 🩺 **عِلَلُ الإعداد تُطبَع ولا تُصلَّح**: مفتاحٌ مطبعيٌّ يمرّ كلَّ
                #    شيءٍ صامتًا فيظنّ المالكُ أنه يُفلتر — فيُرى بالعين في السجلّ.
                for _iss in (bot.alert_filter_issues(_cfg) or []):
                    _log(f"🩺 فلترُ الإشعارات: {_iss}")
                lrows, _lmuted = bot.apply_alert_filter(lrows, _cfg, _WL)
            except Exception as e:                               # noqa: BLE001
                _lmuted = []
                _log(f"⚠️ فلترُ الإشعارات (يمرّ الكلّ): {e}")
            if _lmuted:
                _log(f"🎛️ كُتم {len(_lmuted)} بالفلتر: "
                     + " · ".join(f"{s}/{st} ({w})" for s, st, w in _lmuted[:8])
                     + (f" … و{len(_lmuted) - 8}" if len(_lmuted) > 8 else ""))
            if not lrows:            # كُتم الكلّ ⇒ **يُختَم ولا يُرسَل**
                bot.save_op_entry_state(seen)
                try:
                    bot.git_save([bot.OP_ENTRY_STATE_FILE])
                except Exception as e:                           # noqa: BLE001
                    _log(f"⚠️ دفعُ ددوب السيولة (مكتوم): {e}")
        if lrows:
            _lsyms = [r[0]["symbol"] for r in lrows]
            _lstg = [e["stage"] for _r, _evs in lrows for e in _evs]
            try:
                lok = bot.send_telegram(
                    bot.build_liq_stage_alert(lrows) + "\n\n" + bot.FOOTER)
            except Exception as e:                               # noqa: BLE001
                lok, _ = False, _log(f"⚠️ إرسال «سيولة الشمعة»: {e}")
            if lok:
                liq_hit += len(_lstg)
                _log(f"💰 {len(_lstg)} حدثًا: {', '.join(_lsyms)} "
                     f"[{', '.join(_lstg)}]")
                bot.save_op_entry_state(seen)     # الختمُ **بعد** الإرسال حصرًا
                try:
                    bot.git_save([bot.OP_ENTRY_STATE_FILE])
                except Exception as e:                           # noqa: BLE001
                    _log(f"⚠️ دفعُ ددوب السيولة: {e}")
            else:
                for _s in _lsyms:                # لم يصل ⇒ يُعاد في دورةٍ تالية
                    _k = bot.LIQ_STATE_PREFIX + _s
                    if _k in _snap:
                        seen[_k] = _snap[_k]
                    else:
                        seen.pop(_k, None)
                _log(f"⚠️ تيليجرام رفض «سيولة الشمعة» ({len(lrows)}) — "
                     "أُرجعت الحالةُ لتُعاد المحاولة.")
        time.sleep(interval)
    _log(f"✅ انتهى [{role}]: {loops} دورة · {fired} دخولًا · {liq_hit} رفعةَ "
         f"سيولة · تغطيةُ السيولة {liq_cov} قراءةً · {errs} خطأ.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
