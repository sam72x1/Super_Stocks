#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔁 جوبُ جلسةٍ طويلٌ للمراقب (أمرُ المالك 2026-11-06 «حوّل المراقب لجوب جلسة طويل» — على نمط `ignition.yml`/`operator_entry.yml`).

**العلّةُ مقيسة:** يومَ 11-05 وصل من `pullback_monitor` **4 تشغيلاتٍ** بين 12:00 و02:00 UTC من ‏≈56 فتحةً (GitHub يُسقط الكرون تحت الحمل)
وصفرٌ من فتحات الأفتر الشتويّ ليلتين ⟵ جوبٌ واحدٌ يعيش طوالَ النافذة ويُشغّل **الدورةَ نفسَها** على الفتحات نفسِها.

**الدورةُ = ما كانت تفعله تشغيلةُ الكرون حرفيًّا:** نسخةٌ طازجةٌ من main (`git fetch` ⟵ `git reset --hard FETCH_HEAD`) ثمّ عمليّةٌ جديدة
`python pullback_live.py` بمهلة 15 دقيقة (مهلةُ الجوب القديمة) ⟵ **صفرُ تغييرٍ في أيّ قاعدةٍ أو تنبيه** (الكودُ والحالةُ يُقرآن طازجين كلَّ دورة).
- **الإيقاع:** الدقائقُ 13 · 28 · 43 · 58 (‏`13,43` و`28,58` القديمة) · والنافذةُ اتّحادُ نوافذ الكرونات القديمة بحرفها (`in_window` · `PBJ1`):
  ‏08:00-23:59 UTC الاثنين-الجمعة · و00:xx UTC (الثلاثاء-السبت) حين نيويورك 16:00-19:59 الاثنين-الجمعة (الأفترُ الشتويّ · `AHW1`).
- **مجموعةُ الحالة:** المراقبُ القديم كان في `super-stocks-state` مع الفرز المجدول (`CY4`) فلا يتزاحمان · وجوبٌ بطول 5.5 ساعة فيها كان سيحجز
  تجديدَ الجمعة خلفه ⟵ الجوبُ خارجها **والحمايةُ داخل الحلقة:** لا دورةَ ما دام `daily_screener.yml` المجدولُ يعمل (‏`state_busy`) — كالانتظار
  في المجموعة · وتعذّرُ الـAPI ⟵ تمضي الدورة (الفجوةُ أغلى · و`git_save` وحدُّ الجيل يحلّان التعارض).
- **الخلَف وعاملٌ واحد:** دوالُّ `operator_entry_live` بالاسم (`alive_runs` · `older_alive` · `chain_decision` · `_gh_api` · `_no_session`) ·
  قبل `CHAIN_MIN_LEFT` دقائقَ من نهاية الميزانيّة يُطلَق خلَفٌ (`workflow_dispatch` · `mode=session`) ما دامت النافذةُ قائمة ولا عاملَ حيٌّ غيره ·
  والعاملُ الأحدث ينتظر احتياطًا ما دام أقدمُ حيًّا.
- **الرجوع:** إعادةُ الكرونات القديمة في `pullback_monitor.yml` (وظيفةُ `monitor` القديمة باقيةٌ بحرفها) وحذفُ كرونات الجلسة.
"""
import datetime as dt
import os
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

import operator_entry_live as OE                                  # الخلَف وعاملٌ واحد — بالاسم

NY = ZoneInfo("America/New_York")
SLOTS = (13, 28, 43, 58)                 # دقائقُ الكرونات القديمة `13,43 8-23` و`28,58 8-23` (والأفترُ الشتويّ بالدقائق نفسِها)
CYCLE_TIMEOUT_S = 15 * 60                # مهلةُ الجوب القديمة (`timeout-minutes: 15`)
WORKFLOW = "pullback_monitor.yml"
STATE_WORKFLOWS = ("daily_screener.yml",)   # شريكُ المراقب في `super-stocks-state` (المجدولُ وحدَه · اليدويُّ في مجموعته)
STATE_POLL_S = 60
_sleep = time.sleep                       # يُجذَّع في السويّة


def log(msg):
    print(f"[{dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S')}] {msg}", flush=True)


def in_window(now):
    """🔒 **نقيّة**: هل كانت فتحةُ كرونٍ قديمةٌ ستُشغّل الدورةَ في هذه الدقيقة؟ (اتّحادُ `13,43 8-23 * * 1-5` و`28,58 8-23 * * 1-5` ·
    والأفترُ الشتويّ `13,43 0 * * 2-6`/`28,58 0 * * 2-6` ببوّابته: نيويورك 16-19 الاثنين-الجمعة) — الدقيقةُ نفسُها في `SLOTS` تُفحص منفصلة."""
    u = now.astimezone(dt.timezone.utc)
    wd, h = u.isoweekday(), u.hour
    if wd <= 5 and 8 <= h <= 23:
        return True
    if h == 0 and 2 <= wd <= 6:
        n = u.astimezone(NY)
        return 16 <= n.hour <= 19 and n.isoweekday() <= 5
    return False


def next_slot(now):
    """🔒 **نقيّة**: أقربُ دقيقةٍ من `SLOTS` في `now` أو بعده (ثوانيها صفر) — لا شرطَ نافذة."""
    base = now.astimezone(dt.timezone.utc).replace(second=0, microsecond=0)
    if base < now.astimezone(dt.timezone.utc):
        base += dt.timedelta(minutes=1)
    for k in range(0, 61):
        t = base + dt.timedelta(minutes=k)
        if t.minute in SLOTS:
            return t
    return base + dt.timedelta(minutes=15)


def window_left(now, horizon_min=24 * 60):
    """🔒 **نقيّة**: هل بقيت فتحةٌ داخل النافذة **اليوم** (خلال الساعات الستّ القادمة)؟ — لقرار الخلَف ونهاية العامل."""
    t = next_slot(now)
    end = now + dt.timedelta(minutes=min(horizon_min, 6 * 60))
    while t <= end:
        if in_window(t):
            return True
        t = next_slot(t + dt.timedelta(minutes=1))
    return False


def state_busy(runs) -> bool:
    """🔒 **نقيّة**: تشغيلةُ فرزٍ مجدولةٌ تعمل الآن؟ (`event == schedule` ∧ `in_progress`) — مجموعةُ الحالة القديمة."""
    return any(str(r.get("status") or "") == "in_progress" and str(r.get("event") or "") == "schedule" for r in (runs or ()))


def _state_busy_now(api=None):
    api = api or OE._gh_api
    try:
        for wf in STATE_WORKFLOWS:
            res = api("GET", f"/actions/workflows/{wf}/runs?status=in_progress&per_page=20")
            if res is None:
                return None
            if state_busy(res.get("workflow_runs") or []):
                return True
        return False
    except Exception as e:                                       # noqa: BLE001
        log(f"⚠️ فحصُ مجموعة الحالة: {e} — تمضي الدورة (الفجوةُ أغلى · و`git_save` يحلّ التعارض)")
        return None


def _older_alive_now(api=None, now=None):
    api = api or OE._gh_api
    now = now or dt.datetime.now(dt.timezone.utc)
    try:
        res = api("GET", f"/actions/workflows/{WORKFLOW}/runs?status=in_progress&per_page=50")
    except Exception as e:                                       # noqa: BLE001
        log(f"⚠️ فحصُ العامل الأقدم: {e} — يمضي")
        return None
    if res is None:
        return None
    return OE.older_alive(res.get("workflow_runs") or [], os.environ.get("GITHUB_RUN_ID"), now)


def _alive_others(api=None, now=None):
    api = api or OE._gh_api
    now = now or dt.datetime.now(dt.timezone.utc)
    try:
        res = api("GET", f"/actions/workflows/{WORKFLOW}/runs?status=in_progress&per_page=50")
    except Exception as e:                                       # noqa: BLE001
        log(f"⚠️ فحصُ العمّال الأحياء: {e}")
        return None
    if res is None:
        return None
    return OE.alive_runs(res.get("workflow_runs") or [], os.environ.get("GITHUB_RUN_ID"), now)


def maybe_chain(now, api=None, already=False):
    """🔗 الخلَف بقرار `OE.chain_decision` بالاسم ⟵ True إن أُرسل الطلب. والنافذةُ المتبقّية شرطٌ إضافيّ (لا خلَفَ بلا فتحةٍ قادمة)."""
    api = api or OE._gh_api
    n = now.astimezone(NY)
    if not window_left(now):
        log("🔗 لا خلَف — لا فتحةَ قادمةً في النافذة")
        return False
    do, code, why = OE.chain_decision(n.hour * 60 + n.minute, not OE._no_session(n.date().isoformat()),
                                      _alive_others(api, now), already)
    if not do:
        log(f"🔗 لا خلَف — {why}")
        return False
    try:
        res = api("POST", f"/actions/workflows/{WORKFLOW}/dispatches",
                  {"ref": os.environ.get("GITHUB_REF_NAME") or "main", "inputs": {"mode": "session"}})
    except Exception as e:                                       # noqa: BLE001
        log(f"⚠️ إطلاقُ الخلَف فشل: {e} — الكروناتُ الاحتياطيّة شبكةُ أمان")
        return False
    if res is None:
        log("🔗 لا مفتاحَ GitHub — لا خلَف (بيئةٌ محلّية)")
        return False
    log(f"🔗 أُطلق الخلَف (mode=session) — {why}")
    return True


def run_cycle(runner=None):
    """الدورةُ = تشغيلةُ الكرون القديمة: main طازجٌ ثمّ `python pullback_live.py` في عمليّةٍ جديدة بمهلة 15 دقيقة ⟵ رمزُ خروجه."""
    runner = runner or subprocess.run
    for cmd in (["git", "fetch", "--quiet", "origin", "main"], ["git", "reset", "--hard", "--quiet", "FETCH_HEAD"]):
        r = runner(cmd, capture_output=True, text=True, timeout=120)
        if getattr(r, "returncode", 1) != 0:
            log(f"⚠️ المزامنة ({' '.join(cmd[:2])}): rc={getattr(r, 'returncode', '?')} — تمضي على النسخة الحاليّة")
            break
    try:
        p = runner([sys.executable, "pullback_live.py"], timeout=CYCLE_TIMEOUT_S)
        return int(getattr(p, "returncode", 1) or 0)
    except subprocess.TimeoutExpired:
        log(f"⛔ تجاوزت الدورةُ {CYCLE_TIMEOUT_S // 60} دقيقة — قُتلت (كمهلة الجوب القديمة)")
        return 124


def budget_min(raw=None):
    """دقائقُ العمل — `PB_BUDGET_MIN` **يُقصّر ولا يُطيل** (سقفُ `OE.MAX_RUNTIME_MIN`)."""
    try:
        v = int(str(raw or "").strip() or OE.MAX_RUNTIME_MIN)
    except ValueError:
        v = OE.MAX_RUNTIME_MIN
    return max(1, min(OE.MAX_RUNTIME_MIN, v))


def main(now_fn=None, api=None, runner=None):
    now_fn = now_fn or (lambda: dt.datetime.now(dt.timezone.utc))
    t0 = now_fn()
    budget = budget_min(os.environ.get("PB_BUDGET_MIN"))
    end = t0 + dt.timedelta(minutes=budget)
    log(f"🔁 جوبُ جلسة المراقب: ميزانيّة {budget} دقيقة حتى {end.strftime('%H:%M')} UTC · الفتحات {SLOTS} · النافذةُ اتّحادُ الكرونات القديمة")
    older = _older_alive_now(api, t0)
    said = False
    while older:
        if not said:
            log("🔗🚦 عاملٌ أقدمُ حيّ (" + ", ".join(str(x) for x in older) + ") — أنتظر احتياطًا حتى يدخل دقائقَه الأخيرة")
            said = True
        if (end - now_fn()).total_seconds() <= OE.STANDBY_POLL_S:
            log("🔗🚦 انقضت الميزانيّة منتظرًا — خروج")
            return 0
        _sleep(OE.STANDBY_POLL_S)
        older = _older_alive_now(api, now_fn())
    cycles = fails = 0
    chained, last = False, None
    chain_at = end - dt.timedelta(minutes=OE.CHAIN_MIN_LEFT)
    while True:
        now = now_fn()
        if not chained and now >= chain_at:
            chained = True
            maybe_chain(now, api)
        t = next_slot(now)
        if t == last:
            t = next_slot(t + dt.timedelta(minutes=1))
        if t >= end or not window_left(now):
            if not chained and now < chain_at and window_left(now):
                _sleep(max(1.0, (chain_at - now).total_seconds()))
                continue
            log("🌙 لا فتحةَ قادمةً داخل الميزانيّة والنافذة — خروج")
            break
        target = t if chained else min(t, chain_at)
        wait = (target - now).total_seconds()
        if wait > 0:
            _sleep(wait)
            continue
        last = t
        if not in_window(t):
            continue
        busy = _state_busy_now(api)
        while busy and now_fn() < end:
            log("⏳ الفرزُ المجدول يعمل (مجموعةُ الحالة) — الدورةُ تنتظر كما كانت تنتظر في المجموعة")
            _sleep(STATE_POLL_S)
            busy = _state_busy_now(api)
        if now_fn() >= end:
            break
        rc = run_cycle(runner)
        cycles += 1
        fails += int(rc != 0)
        log(f"🔁 دورة {cycles} عند فتحة {t.strftime('%H:%M')} UTC ⟵ rc={rc}")
    log(f"🔁 انتهى: دورات {cycles} · غيرُ صفريّة {fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
