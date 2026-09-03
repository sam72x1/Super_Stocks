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

try:
    import presession_radar as _PRE                              # 🌙⏱️ قائمةُ ما قبل الجلسة
except Exception:                                                # noqa: BLE001
    _PRE = None            # فاشلٌ-آمن: انكسارُ الاستيراد لا يمسّ العاملَ الحيّ

INTERVAL_DEFAULT = 60          # ثانيةً بين الدورات
MAX_RUNTIME_MIN = 330          # سقفُ أمانٍ تحت حدّ GitHub (‏6 ساعات)
REFRESH_EVERY = 10             # كلَّ ~10 دقائق: تحديثُ القوائم من origin/main
EXT_CLOSE_NY = 20 * 60         # نهايةُ الجلسة الممتدّة (‏20:00 نيويورك)
EXT_OPEN_NY = 4 * 60           # بدءُ الجلسة الممتدّة (‏04:00 نيويورك)
CHAIN_MIN_LEFT = 6             # 🔗 دقائقُ قبل نهاية الميزانية يُطلَق فيها الخلَف (تداخلٌ لا فجوة)
CHAIN_LAST_NY = 19 * 60 + 30   # 🔗 لا خلَفَ بعد 19:30 نيويورك (الجلسةُ الممتدّة تنتهي 20:00)
CHAIN_WORKFLOW = "operator_entry.yml"


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


def _restarts(env=None) -> int:
    """🔢 كم مرّةً أُعيد تشغيلُ هذي العملية بـ`_self_update`؟ **نقيّةٌ لتُقفَل
    سلوكيًّا** (قفلٌ بنيويٌّ يُثبت الوصلَ ولا يرى دلالةَ العدّ) · وتُقرأ البيئةَ
    **وقتَ النداء** لا وقتَ التعريف (سابقةُ `load_edges` المقيسة) · والتالفُ
    والسالبُ ⇒ **صفر** (فاشلٌ-آمن: لا نُلحق سطرَ تحذيرٍ على قيمةٍ لا نفهمها)."""
    src = os.environ if env is None else env
    try:
        n = int(str(src.get("OE_RESTARTS") or 0).strip())
    except (TypeError, ValueError):
        return 0
    return n if n > 0 else 0


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


def _gh_api(method, path, body=None, timeout=25):
    """🔗 نداءُ GitHub API بمفتاح الرنر `GITHUB_TOKEN` — `None` بلا مفتاحٍ أو
    مستودع (بيئةٌ محلّية) · ويرمي عند فشل HTTP (المُنادي يقرّر الفاشل-الآمن)."""
    tok = (os.environ.get("GITHUB_TOKEN") or "").strip()
    repo = (os.environ.get("GITHUB_REPOSITORY") or "").strip()
    if not tok or not repo:
        return None
    import requests                          # في `requirements.txt` (يستعمله البوت)
    r = requests.request(method, f"https://api.github.com/repos/{repo}{path}",
                         json=body, timeout=timeout,
                         headers={"Authorization": f"Bearer {tok}",
                                  "Accept": "application/vnd.github+json",
                                  "X-GitHub-Api-Version": "2022-11-28"})
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:120]}")
    return r.json() if (r.text or "").strip() else {}


def alive_runs(runs, my_id, now) -> list:
    """🔗 **نقيّة**: مَن من تشغيلات هذا الـworkflow **حيٌّ فعلًا غيري**؟
    حيٌّ = `in_progress` **وبدأ قبل أقلَّ من `MAX_RUNTIME_MIN − CHAIN_MIN_LEFT`
    دقيقة** — فمَن تجاوزها **ينتهي هو الآخر الآن** ولا يُعوَّل عليه للتغطية
    (وإلّا رأى عاملان متزامنان بعضَهما فامتنعا معًا وفُتحت فجوة). التالفُ يُتخطّى."""
    out = []
    for r in runs or []:
        try:
            rid = int(r.get("id"))
            if str(rid) == str(my_id or ""):
                continue
            if str(r.get("status") or "") != "in_progress":
                continue
            st = str(r.get("run_started_at") or r.get("created_at") or "")[:19]
            t = bot.dt.datetime.strptime(st, "%Y-%m-%dT%H:%M:%S").replace(
                tzinfo=bot.dt.timezone.utc)
            age_min = (now - t).total_seconds() / 60.0
            if age_min < (MAX_RUNTIME_MIN - CHAIN_MIN_LEFT):
                out.append(rid)
        except Exception:                                        # noqa: BLE001
            continue
    return out


def chain_decision(ny_min, session_ok, others, already):
    """🔗 **نقيّة** — هل يُطلَق خلَفٌ الآن؟ ⟶ `(نعم/لا, رمزٌ, نصّ)`.

    الرموز: `already` (أُطلق سلفًا) · `no_session` · `late` (بعد 19:30 نيويورك)
    · `api_fail` (تعذّر فحصُ الأحياء ⇒ **يُطلَق احتياطًا** — فاشلٌ-آمنٌ نحو
    التغطية: الخلَفُ المكرَّر تُسكته الدِدوبُ المشتركة، والفجوةُ لا يُسكتها شيء)
    · `others` (عاملٌ آخر حيّ ⇒ لا حاجة) · `go`."""
    if already:
        return (False, "already", "أُطلق خلَفٌ من هذي العملية سلفًا")
    if not session_ok:
        return (False, "no_session", "لا جلسةَ سوقٍ اليوم")
    if int(ny_min) >= CHAIN_LAST_NY:
        return (False, "late",
                f"بعد {CHAIN_LAST_NY // 60:02d}:{CHAIN_LAST_NY % 60:02d} نيويورك")
    if others is None:
        return (True, "api_fail", "تعذّر فحصُ العمّال الأحياء ⇒ يُطلَق احتياطًا")
    if others:
        return (False, "others",
                "عاملٌ آخر حيّ: " + ", ".join(str(x) for x in others))
    return (True, "go", "لا عاملَ حيًّا غيري")


def _chain_next(extra_inputs=None, api=None) -> bool:
    """🔗 يطلب من GitHub تشغيلةً جديدة (`workflow_dispatch`) لهذا الـworkflow
    بوسم `segment=chain`. `True` إن أُرسل الطلب (‏204) · `False` بلا مفتاح."""
    api = api or _gh_api
    body = {"ref": (os.environ.get("GITHUB_REF_NAME") or "main"),
            "inputs": dict({"segment": "chain"}, **(extra_inputs or {}))}
    res = api("POST", f"/actions/workflows/{CHAIN_WORKFLOW}/dispatches", body)
    return res is not None


def _maybe_chain(left_min, api=None, now=None, force_test=False) -> bool:
    """🔗🔗 **الخلَف — العاملُ يُعيد إطلاقَ نفسه ولا ينتظر الكرون** (بلاغُ المالك
    2026-09-02 بصور 08-28: «التأخير … نسبة الارتفاع خلال هذا الوقت مب منطقية»).

    🔴 **والعطبُ مقيسٌ من سجلّ التشغيلات لا مُفترَض:** يوم 08-28 لم يُنتج هذا
    الـworkflow أيَّ تشغيلةٍ بين 01:12 و**18:32 UTC** — كرونا `pre` و`open`
    **سقطا كلاهما** ⇒ أوّلُ رؤيةٍ لـ`$CHAI` و`$FTFT` كانت **14:27-14:31 نيويورك**
    و`CHAI` صاعدٌ 70% قبلها. وتكرّر يوم 08-31 (‏3 كرونات صباحيّة لم تُنتج شيئًا).
    GitHub يُسقط الكرونَ تحت الحمل (موثَّقٌ منذ 07-28) — **ولا كرونَ احتياطيٍّ
    يضمن**؛ أمّا `workflow_dispatch` فليس في طابور الكرون ويبدأ خلال ثوانٍ.
    ⚙️ **العقد:** قبل `CHAIN_MIN_LEFT` دقائقَ من نهاية الميزانية يُفحَص: جلسةٌ
    قائمة · قبل 19:30 نيويورك · **ولا عاملَ آخر حيًّا** (من API — فلا تتوالد
    السلاسلُ: كلُّ عمليةٍ تُطلق مرّةً واحدةً على الأكثر) ⇒ يُطلَق خلَفٌ يبدأ
    **قبل** أن ينتهي السلف (تداخلٌ ‏≈6 دقائق = صفرُ فجوة، والدِدوبُ المشتركة
    تمنع التكرار). تعذّرُ الـAPI ⇒ **يُطلَق** (الفجوةُ أغلى من التكرار)، وفشلُ
    الإطلاق **يُسجَّل ولا يُوقف** — الكرونُ يبقى شبكةَ أمان. والعلمُ `OE_CHAINED`
    في البيئة فينجو من `os.execve` في `_self_update`.
    🧪 `force_test` (مدخلُ `chain_test`): إطلاقٌ فوريٌّ لخلَفٍ بميزانيةِ دقيقةٍ
    واحدة — فحصُ دخانٍ لمسار الإذن والطلب من نقطة النداء الحيّة."""
    if os.environ.get("OE_CHAINED") == "1":
        return False
    if not force_test and float(left_min) > CHAIN_MIN_LEFT:
        return False
    api = api or _gh_api
    now = now or bot.dt.datetime.now(bot.dt.timezone.utc)
    mins, day = _ny_minutes(now)
    if force_test:
        do, code, why = True, "test", "فحصُ دخانٍ يدويّ (chain_test)"
    else:
        others = None
        try:
            res = api("GET", f"/actions/workflows/{CHAIN_WORKFLOW}/runs"
                             "?status=in_progress&per_page=50")
            if res is not None:
                others = alive_runs(res.get("workflow_runs") or [],
                                    os.environ.get("GITHUB_RUN_ID"), now)
        except Exception as e:                                   # noqa: BLE001
            _log(f"⚠️ فحصُ العمّال الأحياء: {e}")
            others = None
        do, code, why = chain_decision(mins, not _no_session(day), others, False)
    if not do:
        if code in ("no_session", "late"):        # قرارٌ لا يتغيّر اليوم
            os.environ["OE_CHAINED"] = "1"
        _log(f"🔗 لا خلَف — {why}")
        return False
    try:
        sent = _chain_next({"budget": "1"} if force_test else None, api=api)
    except Exception as e:                                       # noqa: BLE001
        _log(f"⚠️ إطلاقُ الخلَف فشل: {e} — يبقى الكرونُ شبكةَ أمان.")
        return False
    if not sent:
        _log("🔗 لا مفتاحَ GitHub في البيئة — لا خلَف (بيئةٌ محلّية).")
        os.environ["OE_CHAINED"] = "1"
        return False
    os.environ["OE_CHAINED"] = "1"
    _log(f"🔗 أُطلق الخلَف (segment=chain) — {why}")
    return True


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


def _maybe_presession(seen, mod, day) -> bool:
    """🌙⏱️ **قائمةُ ما قبل الافتر/البري بعشر دقائق** (أمرُ المالك 2026-09-03).

    مرّةً واحدةً لكلّ قرارٍ في اليوم (ختمٌ `PRE:<يوم>:<AH|PM>` داخل ددوب «هنا
    الدخول» — لا ملفَّ حالةٍ جديد). **والافتراضُ صامت**: يُكتَب السجلُّ الأماميّ
    ولا تُرسَل رسالة.
    🔴 **والإرسالُ لجلسةٍ بعينها بأمر المالك «شغّل البريماركت» (2026-09-03):**
    `PRESESSION_SEND` تقبل اسمَ الجلسة (`PM`) أو أكثرَ (`PM,AH`) أو `1` للجميع —
    والبوّابةُ **دالّةٌ نقيّةٌ واحدة** في `presession_radar.send_enabled` فلا تُكتَب
    مقارنةُ البيئة هنا وهناك فتتفرّق. المشحونُ اليوم **`PM`** (والافترُ صامتٌ لأن
    رافعتَه المقيسة ‏4.2× مقابل 29.8× للبريماركت).

    🔒 **الختمُ بعد التسليم حصرًا** (عقدُ «فُحِص وسُلِّم»): رفضُ تلغرام ⇒ لا ختمَ
    ولا سجلّ ⇒ تُعاد المحاولةُ في الدورة التالية داخل نافذة القرار.
    🔒 **وفاشلٌ-آمنٌ مطلق:** أيُّ عطلٍ ⇒ يُسجَّل ويمضي العاملُ كما هو.
    """
    if _PRE is None:
        return False
    slot = _PRE.slot_now(mod)
    if not slot:
        return False
    key = _PRE.stamp_key(day, slot)
    if key in seen:
        return False
    rows, msg, diag = _PRE.run_presession(
        slot, day, int(time.time() * 1000), log=_log,
        price_lo=float(bot.CONFIG["MIN_PRICE"]),
        price_hi=float(bot.CONFIG["SPLIT_RADAR_PRICE_MAX"]),
        liq_fn=bot.liq_stage_events, win=int(bot.LIQ_WINDOW_MIN))
    _log(f"🌙 قرارُ {slot} {day}: {diag}")
    if not rows:
        return False
    send = _PRE.send_enabled(slot, os.environ.get("PRESESSION_SEND"))
    ok = True
    if send and msg:
        try:
            ok = bool(bot.send_telegram(msg + "\n\n" + bot.FOOTER))
        except Exception as e:                                   # noqa: BLE001
            ok = False
            _log(f"⚠️ إرسالُ قائمة ما قبل الجلسة: {e}")
        if not ok:
            _log("⚠️ تيليجرام رفض القائمة — لا ختمَ ولا سجلّ، تُعاد المحاولة.")
            return False
    n = _PRE.append_ledger(rows, slot, day, sent=bool(send and ok))
    seen[key] = bot.dt.datetime.now(bot.dt.timezone.utc).isoformat()
    try:
        bot.save_op_entry_state(seen)
        bot.git_save([bot.OP_ENTRY_STATE_FILE, _PRE.LEDGER_FILE])
    except Exception as e:                                       # noqa: BLE001
        _log(f"⚠️ دفعُ ختم ما قبل الجلسة: {e}")
    _log(f"🌙⏱️ قائمةُ {slot}: {len(rows)} اسمًا · سُجِّل {n} · "
         + ("أُرسلت" if (send and ok)
            else f"صامتة (‏PRESESSION_SEND لا تشمل {slot})"))
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
        # 🔢 **عدّادُ إعادات التشغيل يُمرَّر عبر البيئة** (أُضيف 2026-08-20):
        #    `os.execve` يبدأ عمليةً جديدةً فتُصفَّر عدّاداتُ الدورات والرفعات،
        #    **وسطرُ «انتهى» كان يطبعها كأنها عدّادُ المقطع كلِّه** — مقيسٌ
        #    اليومَ: مقطعٌ عاش 5.5 ساعةٍ وطبع «2 دورة · 3 رفعة» لأنه أُعيد
        #    تشغيلُه قبل نهايته بدقائق. ⇒ **عدّادٌ يُعلَن لا يُصمَت عنه.**
        os.execve(sys.executable, [sys.executable] + sys.argv,
                  dict(os.environ, OE_BUDGET_MIN=str(rem),
                       OE_RESTARTS=str(_restarts() + 1)))
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
                # 📏➡️ **حصادُ التصنيف الأماميّ** (العقد `tier_fwd_prereg.md`
                #    مدفوعٌ قبل أوّل صفّ · أمرُ المالك «قِس التصنيف أماميًّا»):
                #    يُسجَّل **هنا حصرًا** — بعد الفلتر وبعد نجاح الإرسال ⇒
                #    المقامُ «ما وصله موسومًا» لا كونُ المسح. فاشلٌ-آمنٌ مطلق.
                _tfwd = 0
                try:
                    _tfwd = bot.record_tier_fwd(lrows, _today2)
                    if _tfwd:
                        _log(f"📏 حصادُ التصنيف: +{_tfwd} صفًّا")
                except Exception as e:                           # noqa: BLE001
                    _log(f"⚠️ حصادُ التصنيف: {e}")
                try:
                    # 🔴 **والسجلُّ يُدفَع مع الحالة** — درسُ `near_watch.json`:
                    #    ملفٌّ لا يُدفَع **يموت مع الرنر كلَّ يوم** فيستحيل أيُّ
                    #    حصادٍ أماميّ. و`git_save` يوحّد `.jsonl` عند التعارض.
                    _files = [bot.OP_ENTRY_STATE_FILE]
                    if _tfwd:
                        _files.append(bot.TIER_FWD_LEDGER_FILE)
                    bot.git_save(_files)
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
    if str(os.environ.get("OE_CHAIN_TEST") or "").strip() in ("1", "true"):
        try:
            _maybe_chain(0, force_test=True)
        except Exception as e:                                   # noqa: BLE001
            _log(f"⚠️ فحصُ دخان الخلَف: {e}")
    while (time.time() - t0) < budget * 60:
        loops += 1
        _cyc = time.time()
        # 🔗 الخلَفُ قبل نهاية الميزانية (تداخلٌ لا فجوة) — انظر `_maybe_chain`.
        try:
            _maybe_chain(budget - (time.time() - t0) / 60.0)
        except Exception as e:                                   # noqa: BLE001
            _log(f"⚠️ الخلَف (دورة {loops}): {e}")
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
        # 🌙⏱️ قائمةُ ما قبل الافتر/البري (نافذةٌ ستُّ دقائقَ مرّتين في اليوم).
        try:
            _maybe_presession(seen, *_ny_minutes())
        except Exception as e:                                   # noqa: BLE001
            _log(f"⚠️ قائمةُ ما قبل الجلسة (دورة {loops}): {e}")
        # ⏱️ **إيقاعٌ لا إضافة** (مع رفع السقف 2026-08-18): كان يُضاف `interval`
        #    **فوق** زمن العمل ⇒ دورةٌ = عملٌ ‏+ 60ث. ومع كونٍ أكبرَ يصير المسحُ
        #    التسلسليُّ أطولَ فتتضخّم الدورةُ **فتتأخّر إشعاراتُ السيولة** — وهي
        #    شكوى المالك بعينها. الآن الدورةُ `max(عمل، interval)`:
        #    🔒 **رتيبٌ لا يُؤخّر أبدًا** — يساوي القديمَ حين يطول العمل، وأسرعُ
        #    منه حين يقصُر؛ ويستحيل عليه بنيويًّا أن يجعل دورةً أطولَ ممّا كانت.
        time.sleep(max(0.0, interval - (time.time() - _cyc)))
    _rs = _restarts()
    _log(f"✅ انتهى [{role}]: {loops} دورة · {fired} دخولًا · {liq_hit} رفعةَ "
         f"سيولة · تغطيةُ السيولة {liq_cov} قراءةً · {errs} خطأ."
         # ⚠️ **والعدّاداتُ من آخر إعادةِ تشغيل لا من بدء المقطع** — تُقال
         #    صراحةً وإلّا قُرئ «2 دورة» عن مقطعٍ عاش خمسَ ساعات.
         + (f" ⚠️ العدّاداتُ **من آخر إعادةِ تشغيل** (أُعيد {_rs} مرّة)."
            if _rs else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
