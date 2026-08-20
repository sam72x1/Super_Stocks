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
import sys
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


def _git_out(args, timeout=15):
    """مُخرَجُ git نصًّا — فاشلٌ-آمن ⇒ سلسلةٌ فارغة."""
    try:
        r = subprocess.run(["git"] + list(args), capture_output=True,
                           timeout=timeout)
        return r.stdout.decode("utf-8", "replace").strip() if r.returncode == 0 \
            else ""
    except Exception:                                            # noqa: BLE001
        return ""


# 🧭 sha الإقلاع — كودُ العملية **في الذاكرة** لا رأسُ الشجرة: `git_save` يدفع
#    حالةَ البوت كلَّ دقائق بـrebase فيبتلع HEAD المحلّيُّ كوميتاتِ الكود الجديدة
#    **في الشجرة** بينما بايثون يشغّل ما استورده عند الإقلاع ⇒ مقارنةُ HEAD
#    بالريموت تقرأ «لا جديد» أبدًا (مقيسٌ 2026-08-18: مقطعٌ عاش 5.5 ساعةً على
#    `fbf21f1` عبر ستّ دفعاتِ كودٍ وصفرِ سطرِ 🔄 في سجلّه).
_BOOT_SHA = _git_out(["rev-parse", "HEAD"]) or None


def _code_changed():
    """📜 ملفّاتُ **الكود** المتغيّرة بين sha الإقلاع وFETCH_HEAD — حالةُ البوت لا تُحصى.

    العاملُ نفسُه يدفع `op_entry_state.json` كلَّ دقائق فلو حُسبت الحالةُ تغييرًا
    لأعاد التشغيلَ بلا نهاية؛ ولو حُسب التاريخُ (`rev-list`) بدل المحتوى لكذب
    (‏`git_save` يعيد كتابةَ main). ⇒ **المحتوى وحدَه**: `git diff --name-only`
    مقصورًا على `.py` والـworkflow و`alert_filter.json` و`requirements.txt`.
    تعذّرُ الفرق (sha الإقلاع أُزيل بإعادة كتابةٍ عنيفة) ⇒ **يُعَدّ تغييرًا**
    (إعادةُ التشغيل تعيد الرسوَ على الرأس الجديد فلا حلقةَ: بعدها الإقلاع = الرأس)."""
    if not _BOOT_SHA:
        return []
    try:
        r = subprocess.run(["git", "diff", "--name-only", _BOOT_SHA,
                            "FETCH_HEAD"], capture_output=True, timeout=30)
        if r.returncode != 0:
            return ["(تعذّر قياسُ الفرق — يُعاد الرسوّ احتياطًا)"]
        names = [n.strip() for n in r.stdout.decode("utf-8", "replace")
                 .splitlines() if n.strip()]
    except Exception:                                            # noqa: BLE001
        return ["(تعذّر قياسُ الفرق — يُعاد الرسوّ احتياطًا)"]
    keep = (".py", ".yml", "alert_filter.json", "requirements.txt")
    return [n for n in names if n.endswith(keep)]


def _stamps_covered():
    """🧷 هل أختامُ الدِدوب المحلّيّة كلُّها حاضرةٌ في نسخة origin؟

    مقارنةُ **محتوًى لا نسبِ تاريخ** — فالنسبُ تكذب حين يُعيد `git_save` كتابةَ
    main (مقيس 2026-08-18: جلبٌ عاديّ رُفض non-fast-forward). الثابتُ المطلوبُ
    حمايتُه واحد: **ألّا يضيع ختمُ إرسالٍ فيتكرّر إشعار** — يُفحَص من الملفّ
    نفسِه: كلُّ مفتاحٍ محلّيٍّ موجودٌ في نسخة origin و`sent` لا تنقص."""
    try:
        loc = bot.load_op_entry_state()
    except Exception:                                            # noqa: BLE001
        return False
    if not loc:
        return True                       # لا أختامَ محلّيّة ⇒ لا شيءَ يُحمى
    rem_txt = _git_out(["show", f"FETCH_HEAD:{bot.OP_ENTRY_STATE_FILE}"])
    try:
        rem = json.loads(rem_txt or "")
    except Exception:                                            # noqa: BLE001
        return False
    if not isinstance(rem, dict):
        return False
    for k, lv in loc.items():
        rv = rem.get(k)
        if rv is None:
            return False
        # 🗓️ ختمُ **يومٍ أقدم** محلّيًّا لاغٍ — نسخةُ origin ليومٍ أحدث تبدأ
        #    `sent` من جديدٍ فلا يُقرأ نقصُها «ختمًا ضائعًا» فيُحجَب التحديثُ
        #    صباحَ كلِّ يومٍ حتى أوّل إرسال.
        if isinstance(lv, dict) and isinstance(rv, dict) \
                and str(rv.get("date") or "") > str(lv.get("date") or ""):
            continue
        if isinstance(lv, dict) and lv.get("sent"):
            rs = set((rv.get("sent") or [])) if isinstance(rv, dict) else set()
            if not set(lv.get("sent") or []) <= rs:
                return False
    return True


def _self_update(t0, budget):
    """🔄 يُحدّث الكودَ حيًّا حين تتغيّر **ملفّاتُ الكود** على origin ثم يُعيد تشغيل نفسه.

    🔴🔴 **إصلاحان مقيسان (2026-08-18):** ① النسخةُ الأولى قارنت HEAD بالريموت —
    و`git_save` يجعلهما متساويين دائمًا (يدفع الحالةَ بـrebase فيتقدّم HEAD فوق
    كوميتات الكود الجديدة) ⇒ **مقطعٌ عاش 5.5 ساعةً على كودٍ بائتٍ بصفرِ سطرِ 🔄
    في سجلّه** والمالكُ يستلم كروتًا بختم `fbf21f1` بعد ستّ دفعاتِ إصلاح.
    الآن المقارنةُ **كودُ الذاكرة (sha الإقلاع) مقابل الريموت، محتوًى لا تاريخًا**
    (`_code_changed`) ② وحارسُ «كوميتاتٌ غيرُ مدفوعة» كان `rev-list` — نسبُ
    تاريخٍ تكذب مع إعادة الكتابة ⇒ صار **فحصَ محتوى الأختام** (`_stamps_covered`).

    🔒 **فاشلٌ-آمنٌ ومحافظ:** شجرةٌ متّسخة أو أختامٌ ناقصةٌ على origin ⇒ لا تحديث
    (لئلّا يضيع ختمُ ددوبٍ فيتكرّر إشعار — الضجيجُ الذي يكرهه المالك). وأيُّ
    إخفاق ⇒ **يمضي بالكود القديم ولا يتوقّف**. ⚖️ **ولا يُطيل الجوب أبدًا:**
    المتبقّي يُمرَّر عبر `OE_BUDGET_MIN` وهو **يُقصّر ولا يُطيل** بنيويًّا
    (`_budget`). يُرجع `False` إن لم يُعِد التشغيل (وإلّا لا يعود أصلًا)."""
    remote = _git_out(["rev-parse", "FETCH_HEAD"])
    if not remote or not _BOOT_SHA:
        return False
    changed = _code_changed()
    if not changed:
        return False                       # حالةُ بوتٍ فقط ⇒ لا إعادةَ تشغيل
    _log(f"🔄 كودٌ أحدثُ على origin ({_BOOT_SHA[:7]} ⟶ {remote[:7]}: "
         f"{'، '.join(changed[:3])}) — يُفحَص الأمان.")
    if _git_out(["status", "--porcelain"]):
        _log("⏸️ الشجرةُ غيرُ نظيفة ⇒ **لا تحديث** (يمضي بالقديم).")
        return False
    if not _stamps_covered():
        _log("⏸️ أختامُ ددوبٍ محلّيّةٌ ليست كلُّها على origin ⇒ **لا تحديث** "
             "(لئلّا يتكرّر إشعار).")
        return False
    rem = int(budget - (time.time() - t0) / 60.0)
    if rem < 2:
        _log("⏸️ المتبقّي أقلُّ من دقيقتين ⇒ لا فائدةَ من إعادة التشغيل.")
        return False
    if _git_out(["reset", "--hard", "FETCH_HEAD"], timeout=60) == "":
        _log("⚠️ تعذّر تحديثُ الشجرة ⇒ يمضي بالقديم (فاشلٌ-آمن).")
        return False
    _log(f"♻️ حُدِّث الكودُ إلى {remote[:7]} — يُعاد التشغيل بميزانية {rem} دقيقة.")
    try:
        os.execve(sys.executable, [sys.executable] + sys.argv,
                  dict(os.environ, OE_BUDGET_MIN=str(rem)))
    except Exception as e:                                       # noqa: BLE001
        _log(f"⚠️ تعذّرت إعادةُ التشغيل ({e}) — يمضي بالكود المحدَّث في الذاكرة.")
    return False


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
         + " و".join(str(m) for m in bot.LIQ_STAGE_MINUTES) + " دقيقة"
         # 💓 **والنبضُ يُعلَن بأرضيته وبوّابته** (أُضيف 2026-08-20): الترويسةُ
         #    كانت تذكر أرضيةَ السيولة والمراحلَ **ولا تذكر النبضَ إطلاقًا**
         #    بعد أن صار له أرضيةٌ وبوّابةُ تصنيفٍ في اليوم نفسِه ⇒ **شرطٌ بلا
         #    سطرٍ = دعوًى غيرُ قابلةٍ للفحص** (نظيرُ «سطرُ عرضٍ بلا حقلٍ =
         #    كذبة»). عرضٌ بحت: صفرُ أثرٍ على أيّ قرار.
         + f" · 💓 نبضٌ {bot.LIQ_PULSE_PCT:g}% بأرضيةِ "
           f"${bot.LIQ_PULSE_MIN_USD:,.0f} **وللمصنَّف بعد M5 وحدَه**")
    loops, fired, errs = 0, 0, 0
    liq_at, liq_cov, liq_hit = 0, 0, 0
    def _liq_sweep():
        """⏫💰 مسحُ السيولة كاملًا (فحص ⟵ فلتر ⟵ إرسال ⟵ ختم) — يُنادى
        **مرّتين في الدورة** (إصلاح 2026-08-19، بلاغُ المالك على `$WXM` «برضو
        فيه تاخير»): مرّةً **قبل** مسح الدخول التسلسليّ البطيء ومرّةً بعده —
        الفاصلُ بين مسحَي سيولةٍ متتاليين مقيسٌ من السجلّ الحيّ **‏86-757 ثانية**
        (مسحُ الدخول يستهلك الدورة) بينما مسحُ السيولة نفسُه ‏10-13ث ⇒ النداءُ
        المزدوج يقصّ فاصلَ الانتظار إلى النصف تقريبًا بلا خيوطٍ جديدة ولا
        تغييرِ عتبة. والدِدوبُ و`last_eval_ms` يجعلان الثاني بلا حدثٍ ما لم
        تُغلَق دقيقةٌ جديدة (لا تكرار)."""
        nonlocal liq_cov, liq_hit, errs
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
                # 🔴 **بلا `FOOTER` (أمرُ الاختصار 2026-08-20):** الكرتُ يحمل
                #    ذيلَه المضغوط («توقيتٌ لا توصية · «سيولة» ليست «مضارب»»)
                #    ⇒ إلحاقُ الذيل العامّ تكرارُ تنويهٍ بمئة محرفٍ يدفع القرار
                #    إلى أسفل الشاشة. **والتنويهُ باقٍ**، وختمُ الإصدار يُلحقه
                #    `send_telegram` كما هو لكلّ رسالة.
                lok = bot.send_telegram(bot.build_liq_stage_alert(lrows))
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
    while (time.time() - t0) < budget * 60:
        loops += 1
        _cyc = time.time()
        if loops % REFRESH_EVERY == 0:
            try:
                uni, _c, _s, uni_all = _load_universe()
                for _k, _v in (_s or {}).items():
                    seen.setdefault(_k, _v)
            except Exception as e:                               # noqa: BLE001
                _log(f"⚠️ تحديثُ الكون (دورة {loops}): {e}")
            # 🔄 **وبعد الجلب مباشرةً**: `_load_universe` نفّذ `git fetch` سلفًا
            #    فالمقارنةُ بلا نداءٍ شبكيٍّ إضافيّ. (يُنادى **بعد** ضمّ الددوب
            #    كي لا يُعاد التشغيل قبل أن تُقرأ أختامُ المقاطع الأخرى.)
            try:
                _self_update(t0, budget)
            except Exception as e:                               # noqa: BLE001
                _log(f"⚠️ فحصُ تحديث الكود: {e}")
            _log(f"💰 تغطيةُ السيولة: {liq_cov} قراءةً تراكميًّا من "
                 f"{len(uni_all)} · الموضعُ الآن {liq_at} · {liq_hit} رفعة.")
        # ⏫ السيولة أوّلًا (النداء الأوّل من اثنين — انظر docstring المسح):
        #    الدقيقةُ الحرِجة لا تنتظر المسحَ التسلسليَّ البطيء.
        _liq_sweep()
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
        _liq_sweep()
        # ⏱️ **إيقاعٌ لا إضافة** (مع رفع السقف 2026-08-18): كان يُضاف `interval`
        #    **فوق** زمن العمل ⇒ دورةٌ = عملٌ ‏+ 60ث. ومع كونٍ أكبرَ يصير المسحُ
        #    التسلسليُّ أطولَ فتتضخّم الدورةُ **فتتأخّر إشعاراتُ السيولة** — وهي
        #    شكوى المالك بعينها. الآن الدورةُ `max(عمل، interval)`:
        #    🔒 **رتيبٌ لا يُؤخّر أبدًا** — يساوي القديمَ حين يطول العمل، وأسرعُ
        #    منه حين يقصُر؛ ويستحيل عليه بنيويًّا أن يجعل دورةً أطولَ ممّا كانت.
        time.sleep(max(0.0, interval - (time.time() - _cyc)))
    _log(f"✅ انتهى [{role}]: {loops} دورة · {fired} دخولًا · {liq_hit} رفعةَ "
         f"سيولة · تغطيةُ السيولة {liq_cov} قراءةً · {errs} خطأ.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
