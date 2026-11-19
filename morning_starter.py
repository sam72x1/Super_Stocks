#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌅 مُطلِقُ الصباح — حارسٌ ينوب عن جدولة GitHub في إطلاق المراقب ورسالة الظلّ (أمرُ المالك 2026-11-06 «ابنِ مُطلِق الصباح»).

**العطلُ المُثبَت (2026-11-06):** `shadow_telegram.yml` صفرُ تشغيلةٍ مجدولة طوالَ اليوم (رسالةُ 14:25 خرجت بإطلاقٍ يدويّ) · و`pullback_monitor.yml`
تشغيلتان مجدولتان (02:38 · 02:49 UTC) · وسلسلةُ جوب الجلسة (`pullback_session`) تنقطع ليلًا بعد آخر فتحة (`CHAIN_HORIZON_MIN`) فيعتمد
**بدءُ الصباح** على كرونٍ لا يصل.

**الحارس:** جوبٌ واحدٌ ينام ويستيقظ عند نقاطٍ محسوبة · ويُطلق خلَفه قبل نهاية ميزانيّته (`workflow_dispatch` · مجموعةُ تزامنٍ ثابتة ⟵ واحدٌ يعمل
وواحدٌ ينتظر على الأكثر) — فيعيش بلا كرون:
- **المراقب:** قبل كلّ فتحةٍ داخل نافذة المراقب بـ`LEAD_MIN` دقائق (`pullback_session.in_window`/`next_slot` **بالاسم** · النافذةُ اتّحادُ الكرونات
  القديمة) ⟵ إن لم يكن جوبُ جلسةٍ حيًّا (`operator_entry_live.alive_runs` بالاسم) ولا منتظرًا ⟵ يُطلَق `pullback_monitor.yml` بـ`mode=session` ·
  وإلّا لا شيء (السلسلةُ تكفي).
- **رسالةُ الظلّ:** يومَ الجلسة (`operator_entry_live._no_session` بالاسم) عند `SHADOW_CHECKS_NY` (05:30 · 06:30 · 07:30 · 08:30 · 09:05 نيويورك ·
  كلُّها داخل انتظار `shadow_telegram.WAIT_MAX_S`) ⟵ إن لم يُختم اليومُ على main ولا تشغيلةٌ حيّةٌ أو منتظرة ⟵ يُطلَق `shadow_telegram.yml` ·
  والرسالةُ نفسُها وختمُها ودِدوبُها كما هي (الإطلاقُ المكرّر لا يُرسل مرّتين).
- **قناةُ المشتركين (2026-11-19):** قبل موعدها (`subs_channel.SEND_AT` الرياض) بـ`SUBS_LEAD_MIN` ثمّ كلَّ ساعةٍ حتى المساء ⟵ إن كان في صندوق main
  رسالةٌ لم تُرسَل حلّ موعدُها ⟵ يُطلَق `subs_sender.yml` · والقناةُ مطفأة (`subs_channel.ON = False`) ⟵ لا نقطةَ أصلًا (بت-بت · `SUB8`).
🔒 **لا يُرسل تلغرامَ ولا يكتب حالةً ولا يمسّ قاعدةً** — إطلاقاتُ `workflow_dispatch` وقراءاتٌ من GitHub API وحدَها · وبلا مفتاح ⟵ صفرُ عمل ·
وتعذّرُ الـAPI ⟵ سطرُ سجلٍّ ويمضي (الكروناتُ القديمةُ باقيةٌ احتياطًا).
↩️ **الرجوع: احذف سطرَ `MORNING_STARTER: "1"` من `morning_starter.yml`** ⟵ التشغيلةُ القائمة تقرأ الملفَّ من main عند كلّ استيقاظ فتتوقّف بلا
إطلاقٍ ولا خلَف · والجديدةُ تخرج فورًا (`MST1`-`MST3`).
"""
import base64
import datetime as dt
import json
import os
import sys
import time
from zoneinfo import ZoneInfo

import operator_entry_live as OE                       # alive_runs · _gh_api · _no_session — بالاسم
import subs_channel as SC                              # 📣 موعدُ قناة المشتركين وصندوقُها — بالاسم
from pullback_session import in_window, next_slot      # نافذةُ المراقب وفتحاتُه — بالاسم

NY = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
ENV = "MORNING_STARTER"
SELF_WF = "morning_starter.yml"
MONITOR_WF = "pullback_monitor.yml"
SHADOW_WF = "shadow_telegram.yml"
SHADOW_STAMP = "shadow_tg_stamp.json"
BUDGET_MIN = 330          # تحت حدّ GitHub (6 ساعات) · ومهلةُ الجوب 345
HOP_LEFT_MIN = 4          # الخلَفُ قبل نهاية الميزانيّة بهذي الدقائق
LEAD_MIN = 6              # إطلاقُ المراقب قبل الفتحة (بدءُ الرنر ‏≈دقيقة · والجوبُ ينام حتى الفتحة)
LATE_MIN = 10             # نقطةٌ فات موعدُها بأكثر من هذا ⟵ تُترك (والتالية تغطّي)
SHADOW_CHECKS_NY = (5 * 60 + 30, 6 * 60 + 30, 7 * 60 + 30, 8 * 60 + 30, 9 * 60 + 5)
SHADOW_SEND_NY = 9 * 60 + 25                         # = `shadow_telegram.SEND_AT_NY`
SHADOW_GUARD_MIN = 50     # لا إطلاقَ ثانٍ للرسالة قبل هذا من الأوّل (حتى تظهر تشغيلتُه)
ACTIVE = ("queued", "in_progress", "waiting", "pending", "requested")
SEARCH_DAYS = 4           # أبعدُ بحثٍ عن الفتحة/النقطة التالية (نهايةُ أسبوعٍ طويلة)
SUBS_WF = "subs_sender.yml"
SUBS_LEAD_MIN = 6         # إطلاقُ مُرسِل القناة قبل موعدها (ينتظره بـ`flush --wait`)
_sleep = time.sleep


def log(msg):
    print(f"[{dt.datetime.now(UTC).strftime('%H:%M:%S')}] {msg}", flush=True)


def window_slots(start, end):
    """🔒 **نقيّة**: فتحاتُ نافذة المراقب في [start, end] بالترتيب."""
    out, t = [], next_slot(start)
    while t <= end:
        if in_window(t):
            out.append(t)
        t = next_slot(t + dt.timedelta(minutes=1))
    return out


def next_monitor_point(now, done):
    """🔒 **نقيّة**: (الفتحة، لحظةُ إطلاقها) لأقرب فتحةٍ لم تُعالَج ولم يفُت موعدُها بأكثر من `LATE_MIN` ⟵ أو (None, None)."""
    lo = now - dt.timedelta(minutes=LATE_MIN)
    t = next_slot(lo + dt.timedelta(minutes=LEAD_MIN))
    hi = now + dt.timedelta(days=SEARCH_DAYS)
    while t <= hi:
        if in_window(t) and t not in done:
            return t, t - dt.timedelta(minutes=LEAD_MIN)
        t = next_slot(t + dt.timedelta(minutes=1))
    return None, None


def next_shadow_point(now, done, no_session=None):
    """🔒 **نقيّة** (بحقن `no_session`): (مفتاحُ النقطة، لحظتُها UTC) لأقرب نقطة فحصٍ للرسالة يومَ جلسةٍ لم تُعالَج ولم يفُت موعدُها
    بأكثر من `LATE_MIN` ⟵ أو (None, None)."""
    no_session = no_session or OE._no_session
    d0 = now.astimezone(NY).date()
    for k in range(SEARCH_DAYS + 1):
        d = d0 + dt.timedelta(days=k)
        if no_session(d.isoformat()):
            continue
        for m in SHADOW_CHECKS_NY:
            at = dt.datetime(d.year, d.month, d.day, m // 60, m % 60, tzinfo=NY).astimezone(UTC)
            key = (d.isoformat(), m)
            if key in done or at < now - dt.timedelta(minutes=LATE_MIN):
                continue
            return key, at
    return None, None


def next_subs_point(now, done, on=None, env=None):
    """🔒 **نقيّة** (بحقن `on`): (مفتاحُ النقطة، لحظتُها UTC) لقناة المشتركين — موعدُها (`subs_channel.SEND_AT` الرياض) ناقصَ `SUBS_LEAD_MIN` ثمّ
    كلَّ ساعةٍ بعده حتى `EVENING_HOUR` (إعادةُ ما تعذّر) — لم تُعالَج ولم يفُت موعدُها بأكثر من `LATE_MIN` · والقناةُ مطفأة ⟵ (None, None)
    فالحارسُ بت-بت (`SUB8`)."""
    if not (SC.on() if on is None else on):
        return None, None
    h, m = SC._at(env)
    d0 = now.astimezone(SC.RIYADH).date()
    for k in range(2):
        d = d0 + dt.timedelta(days=k)
        base = dt.datetime(d.year, d.month, d.day, h, m, tzinfo=SC.RIYADH)
        pts = [base - dt.timedelta(minutes=SUBS_LEAD_MIN)]
        pts += [base + dt.timedelta(hours=i) for i in range(1, 24 - h) if (base + dt.timedelta(hours=i)).hour < SC.EVENING_HOUR]
        for at in pts:
            at = at.astimezone(UTC)
            key = at.isoformat()
            if key in done or at < now - dt.timedelta(minutes=LATE_MIN):
                continue
            return key, at
    return None, None


def _main_names(api, path):
    """أسماءُ ملفّات مجلّدٍ على main ⟵ [] إن لم يوجد (404) · وNone عند تعذّر القراءة."""
    try:
        res = api("GET", f"/contents/{path}?ref=main")
    except Exception as e:                                       # noqa: BLE001
        if "HTTP 404" in str(e):
            return []
        log(f"⚠️ قراءةُ {path}: {e}")
        return None
    return [str((x or {}).get("name") or "") for x in res] if isinstance(res, list) else []


def ensure_subs(api, now, key):
    """نقطةُ القناة: في صندوق main رسالةٌ لم تُرسَل حلّ موعدُها أو يحلّ خلال انتظار المُرسِل ⟵ إطلاقُ `subs_sender.yml` (ما لم تكن تشغيلتُه قائمة) ·
    وإلّا لا شيء. الموعدُ من بادئة اسم الملفّ (`subs_channel.unsent_names`) بلا فكّ تشفير."""
    names = []
    for d in SC.month_dirs(now):
        got = _main_names(api, d)
        if got is None:
            names = None
            break
        names += got
    if names is None:
        log("📣 تعذّرت قراءةُ صندوق القناة — يُطلَق المُرسِل احتياطًا")
        due = [now]
    else:
        due = [d for _n, d in SC.unsent_names(names) if d <= now + dt.timedelta(minutes=SC.WAIT_MAX_MIN)]
    if not due:
        log(f"📣 {key}: لا رسالةَ في صندوق القناة حلّ موعدُها — لا إطلاق")
        return False
    try:
        active = [r.get("id") for r in (_runs(api, SUBS_WF) or []) if str(r.get("status") or "") in ACTIVE]
    except Exception as e:                                       # noqa: BLE001
        log(f"⚠️ فحصُ تشغيلات المُرسِل: {e}")
        active = []
    if active:
        log(f"📣 {key}: تشغيلةٌ قائمة {active} — لا إطلاق")
        return False
    ok = _dispatch(api, SUBS_WF)
    log(f"📣 {key}: {len(due)} رسالةً حلّ موعدُها ⟵ {'أُطلق مُرسِلُ القناة' if ok else '⛔ تعذّر الإطلاق'}")
    return ok


def _runs(api, wf, status=None):
    q = f"/actions/workflows/{wf}/runs?per_page=50" + (f"&status={status}" if status else "")
    res = api("GET", q)
    return None if res is None else (res.get("workflow_runs") or [])


def _main_text(api, path):
    res = api("GET", f"/contents/{path}?ref=main")
    if not res or not res.get("content"):
        return None
    return base64.b64decode(res["content"]).decode("utf-8")


def _dispatch(api, wf, inputs=None, tries=3):
    body = {"ref": os.environ.get("GITHUB_REF_NAME") or "main"}
    if inputs:
        body["inputs"] = inputs
    for k in range(tries):
        try:
            if api("POST", f"/actions/workflows/{wf}/dispatches", body) is not None:
                return True
            return False
        except Exception as e:                                   # noqa: BLE001
            log(f"⚠️ إطلاقُ {wf} (محاولة {k + 1}): {e}")
            if k + 1 < tries:
                _sleep(2 ** (k + 1))
    return False


def switch_on(api):
    """↩️ مفتاحُ الرجوع من main (لا من نسخة الإقلاع): السطرُ موجود ⟵ True · محذوف ⟵ False · وتعذّرُ القراءة ⟵ True (يمضي)."""
    try:
        import yaml
        txt = _main_text(api, f".github/workflows/{SELF_WF}")
        if txt is None:
            return True
        y = yaml.safe_load(txt) or {}
        for j in (y.get("jobs") or {}).values():
            for s in (j or {}).get("steps") or []:
                if str(((s or {}).get("env") or {}).get(ENV, "")) == "1":
                    return True
        return False
    except Exception as e:                                       # noqa: BLE001
        log(f"⚠️ قراءةُ مفتاح الرجوع: {e} — يمضي")
        return True


def ensure_monitor(api, now, slot):
    """قبل الفتحة: جوبُ جلسةٍ حيٌّ أو منتظر؟ ⟵ لا شيء · وإلّا إطلاقُه بـ`mode=session`."""
    try:
        alive = OE.alive_runs(_runs(api, MONITOR_WF, "in_progress") or [], None, now)
        queued = _runs(api, MONITOR_WF, "queued") or []
    except Exception as e:                                       # noqa: BLE001
        log(f"⚠️ فحصُ جوب المراقب: {e} — يمضي إلى الإطلاق")
        alive, queued = [], []
    if alive or queued:
        log(f"🌅 فتحة {slot.strftime('%a %H:%M')} UTC: جوبُ جلسةٍ قائم ({alive or 'منتظر'}) — لا إطلاق")
        return False
    ok = _dispatch(api, MONITOR_WF, {"mode": "session"})
    log(f"🌅 فتحة {slot.strftime('%a %H:%M')} UTC: لا جوبَ جلسة ⟵ {'أُطلق المراقب (mode=session)' if ok else '⛔ تعذّر الإطلاق'}")
    return ok


def ensure_shadow(api, now, key):
    """نقطةُ الرسالة: مختومةٌ اليوم على main أو تشغيلتُها حيّةٌ/منتظرة ⟵ لا شيء · وإلّا إطلاقُ `shadow_telegram.yml`."""
    day = key[0]
    try:
        st = json.loads(_main_text(api, SHADOW_STAMP) or "{}")
    except Exception as e:                                       # noqa: BLE001
        log(f"⚠️ قراءةُ ختم الرسالة: {e}")
        st = {}
    if str(st.get("last_sent") or "") == day:
        log(f"🌘 {day} {key[1] // 60:02d}:{key[1] % 60:02d} نيويورك: الرسالةُ مختومة — لا إطلاق")
        return False
    try:
        active = [r.get("id") for r in (_runs(api, SHADOW_WF) or []) if str(r.get("status") or "") in ACTIVE]
    except Exception as e:                                       # noqa: BLE001
        log(f"⚠️ فحصُ تشغيلات الرسالة: {e}")
        active = []
    if active:
        log(f"🌘 {day} {key[1] // 60:02d}:{key[1] % 60:02d} نيويورك: تشغيلةٌ قائمة {active} — لا إطلاق")
        return False
    ok = _dispatch(api, SHADOW_WF)
    log(f"🌘 {day} {key[1] // 60:02d}:{key[1] % 60:02d} نيويورك: لا ختمَ ولا تشغيلة ⟵ {'أُطلقت رسالةُ الظلّ' if ok else '⛔ تعذّر الإطلاق'}")
    return ok


def main(now_fn=None, api=None, no_session=None):
    if os.environ.get(ENV) != "1":
        log(f"↩️ `{ENV}` غائب — الحارسُ مُطفأ (لا إطلاقَ ولا خلَف)")
        return 0
    now_fn = now_fn or (lambda: dt.datetime.now(UTC))
    if api is None and not ((os.environ.get("GITHUB_TOKEN") or "").strip() and (os.environ.get("GITHUB_REPOSITORY") or "").strip()):
        log("🔑 لا مفتاحَ GitHub — صفرُ عمل")
        return 0
    api = api or OE._gh_api
    t0 = now_fn()
    hop_at = t0 + dt.timedelta(minutes=BUDGET_MIN - HOP_LEFT_MIN)
    log(f"🌅 مُطلِقُ الصباح: ميزانيّة {BUDGET_MIN} دقيقة · الخلَفُ عند {hop_at.strftime('%a %H:%M')} UTC")
    done_m, done_s, done_c, shadow_last = set(), set(), set(), None
    while True:
        now = now_fn()
        slot, at_m = next_monitor_point(now, done_m)
        key, at_s = next_shadow_point(now, done_s, no_session)
        ckey, at_c = next_subs_point(now, done_c)
        wake = min(x for x in (at_m, at_s, at_c, hop_at) if x is not None)
        if wake > now:
            _sleep((wake - now).total_seconds())
            now = now_fn()
        if not switch_on(api):
            log(f"↩️ سطرُ `{ENV}` حُذف من main — توقّفٌ بلا إطلاقٍ ولا خلَف")
            return 0
        if slot is not None and at_m <= now:
            done_m.add(slot)
            ensure_monitor(api, now, slot)
        if key is not None and at_s <= now:
            done_s.add(key)
            if shadow_last is None or (now - shadow_last) >= dt.timedelta(minutes=SHADOW_GUARD_MIN):
                if ensure_shadow(api, now, key):
                    shadow_last = now
        if ckey is not None and at_c <= now:
            done_c.add(ckey)
            ensure_subs(api, now, ckey)
        if now >= hop_at:
            ok = _dispatch(api, SELF_WF)
            log(f"🔗 {'أُطلق الخلَف' if ok else '⛔ تعذّر إطلاقُ الخلَف — الكروناتُ الاحتياطيّة شبكةُ أمان'} — خروج")
            return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
