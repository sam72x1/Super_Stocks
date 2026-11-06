#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌘 قائمةُ الظلّ على تلغرام قبل الافتتاح (أمرُ المالك 2026-11-06 «أرسل قائمة الظل على تلغرام» · سببُه `T-RRGATE` ④:
S تلتقط 41.1% من راكضي ‏+100% مقابل 0.1% من غيرهم).

رسالةٌ واحدة يومَ الجلسة عند **09:25 نيويورك** بعنوان المالك حرفيًّا · أسماءُ S لليوم وسببُ كلِّ اسم (J1 أو فجوة) ·
**بلا أيّ تغييرٍ في قاعدة S**: صفُّ كلِّ مرساةٍ من `shadow_ready.anchor_row` **بالاسم** (ميزاتُ `features` · فجوةُ `gap_pct_of` ·
صفُّ سجلّ التصنيف `tier_fwd_report.load_ledger` لمن فيه · شموعُ الدقيقة `fetch_day` · والإغلاقاتُ `daily_range`) ثمّ `shadow_flag`
— **السطورُ نفسُها التي يبني بها السجلُّ الليليّ صفَّه** (`shadow_ready.main`) · والمصدرُ مراسي «هنا الدخول» في **بريماركت اليوم
نفسِه** من `op_entry_state.json` على main لحظةَ البناء (العاملُ الحيّ يكتبها) · وما تعذّرت شموعُه أو لا أساسَ له بعد يُعَدّ ويُعلَن.
🔁 `SHADOW_TG_REPLAY=YYYY-MM-DD` ⟵ يُعيد بناءَ قائمة يومٍ ماضٍ من الحالة ويطبعها **ولا يُرسل ولا يختم أبدًا** (للمطابقة بالسجلّ الليليّ).
🔒 قراءةٌ فقط عدا ختمِ الإرسال (`shadow_tg_stamp.json`) · لا يمسّ الإنتاجَ ولا `shadow_ready.py` (`V-S7` يخصّه) ولا سجلَّ T-SHADOW ·
و`SHADOW_TG_SEND≠1` ⟵ تُبنى وتُطبع ولا تُرسَل (الرجوع: حذفُ الإرسال).
"""
import datetime as dt
import json
import os
import subprocess
import sys
import time
from zoneinfo import ZoneInfo

from shadow_ready import shadow_flag, anchor_row                  # بالاسم — صفُّ المرساة وقاعدةُ S كما في السجلّ الليليّ
from tierlink_probe import daily_range                            # بالاسم — الإغلاقاتُ اليوميّة
from shadow_ready import split_fn                                 # ✂️ بالاسم — تسويةُ الفجوة بالتقسيم (`SSG1`-`SSG3`)
from tier_fwd_report import fetch_day, load_ledger                # بالاسم — شموعُ الدقيقة وسجلُّ التصنيف

NY = ZoneInfo("America/New_York")
TITLE = "🌘 قائمة الظل — قيد الإثبات، لا حكم قبل 12-31"           # نصُّ المالك حرفيًّا
SEND_AT_NY = 9 * 60 + 25                                          # 09:25 نيويورك (أمرُ المالك: «حتى 09:25»)
OPEN_NY = 9 * 60 + 30                                             # بعده لا إرسال («قبل الافتتاح»)
WAIT_MAX_S = 5 * 3600                                             # أبعدُ انتظارٍ مقبول (المجدولُ يبدأ قبلها بساعاتٍ احتياطًا)
STAMP = "shadow_tg_stamp.json"
STATE = "op_entry_state.json"
_sleep = time.sleep


def log(msg):
    print(f"[{dt.datetime.now(dt.timezone.utc).strftime('%H:%M:%S')}] {msg}", flush=True)


def _hm(ms):
    t = dt.datetime.fromtimestamp(int(ms) / 1000, tz=NY)
    return t.strftime("%H:%M")


def premarket_anchors(state, day):
    """🔒 **نقيّة**: مراسي `LIQ:*` ليوم نيويورك `day` التي وقعت قبل 09:30 ⟵ [(رمز، صفّ)] مرتَّبةً بوقت المرساة."""
    out = []
    for k, v in (state or {}).items():
        if not str(k).startswith("LIQ:") or not isinstance(v, dict) or not v.get("anchor_ms"):
            continue
        if str(v.get("date") or "") != day:
            continue
        t = dt.datetime.fromtimestamp(int(v["anchor_ms"]) / 1000, tz=NY)
        if t.date().isoformat() != day or t.hour * 60 + t.minute >= OPEN_NY:
            continue
        out.append((str(k)[4:], v))
    return sorted(out, key=lambda kv: int(kv[1]["anchor_ms"]))


def shadow_rows(anchors, dailies_of, day, bars_of, ledger=None, split_of=None):
    """🔒 **نقيّة على المُدخلات**: صفُّ كلِّ مرساةٍ بـ`anchor_row` بالاسم (بصفّ سجلّ التصنيف إن وُجد) ثمّ `shadow_flag` — كما في
    `shadow_ready.main` حرفيًّا ⟵ (صفوفُ S، كلُّ المراسي المقيسة، المستبعَدُ {bars · base}) · الصفّ = {sym · ms · px · gap · j1 · why}."""
    rows, allr, skipped = [], [], {"bars": 0, "base": 0}
    for sym, a in anchors:
        bars = bars_of(sym)
        if not bars:
            skipped["bars"] += 1
            continue
        got = anchor_row(a, (ledger or {}).get((day, sym)), bars, dailies_of(sym), day,
                         split=(split_of(sym) if split_of else None))
        if got is None:
            skipped["base"] += 1
            continue
        f, _o, g = got
        j1 = f.get("j1") == "J1"
        r = {"sym": sym, "ms": int(a["anchor_ms"]), "px": a.get("anchor_price"), "gap": g, "j1": j1, "tod": f.get("tod"),
             "S": bool(shadow_flag(f))}
        why = []
        if j1:
            why.append("J1")
        if f.get("gap") == "≥30%":
            why.append(f"فجوة {g:+.0f}%" if g is not None else "فجوة 30% فأكثر")
        r["why"] = " · ".join(why)
        allr.append(r)
        if r["S"]:
            rows.append(r)
    return rows, allr, skipped


def last_state_ms(state, day):
    """آخرُ ما كتبه عاملُ «هنا الدخول» لليوم (أكبرُ `last_eval_ms`/`last_ms`/`pulse_ms`) ⟵ ms أو None — تغطيةُ البريماركت تُقرأ منه."""
    best = None
    for k, v in (state or {}).items():
        if str(k).startswith("LIQ:") and isinstance(v, dict) and str(v.get("date") or "") == day:
            for f in ("last_eval_ms", "last_ms", "pulse_ms"):
                try:
                    x = int(v.get(f) or 0)
                except (TypeError, ValueError):
                    continue
                if x and (best is None or x > best):
                    best = x
    return best


def build_message(day, built_ny, rows, allr, last_ms, first, skipped=None):
    """🔒 **نقيّة**: نصُّ الرسالة — العنوانُ حرفيًّا · وقتُ البناء · مصدرُه (بريُ اليوم نفسِه) · الأسماءُ وسببُها · وفي الأولى شرحُ التغطية."""
    L = [f"<b>{TITLE}</b>",
         f"📅 {day} · بُنيت {built_ny} نيويورك من مراسي «هنا الدخول» في <b>بريماركت اليوم نفسِه</b> حتى وقت البناء "
         f"(آخرُ لقطةٍ لعامل «هنا الدخول»: {_hm(last_ms) if last_ms else 'لا لقطة اليوم'})",
         "S = مرساةٌ قبل 09:30 ∧ (J1 أو فجوةُ المرساة عن إغلاق الأمس 30% فأكثر)",
         f"مراسي البريماركت اليوم {len(allr)} · منها في S <b>{len(rows)}</b>"
         + ("" if not skipped or not (skipped.get("bars") or skipped.get("base")) else
            f" (ولم يُقَس بعد {skipped.get('bars', 0) + skipped.get('base', 0)}: تعذّرت شموعُه {skipped.get('bars', 0)} · "
            f"بلا أساسٍ بعد {skipped.get('base', 0)} — يُقاسان في السجلّ الليليّ)"), ""]
    if rows:
        for i, r in enumerate(rows, 1):
            px = "" if r["px"] is None else f" ${float(r['px']):g}"
            gp = "" if r["gap"] is None or "فجوة" in r["why"] else f" · فجوة {r['gap']:+.0f}%"
            L.append(f"{i}. <b>${r['sym']}</b> — {r['why']}{gp} · مرساة {_hm(r['ms'])}{px}")
    else:
        L.append(f"لا اسمَ في S حتى {built_ny} نيويورك.")
    if first:
        L += ["", "ℹ️ <b>عن هذه القائمة (الرسالة الأولى):</b> تشمل بريَ اليوم نفسِه حتى لحظة بنائها — لا شموعَ الأمس — من مراسي عامل "
                  "«هنا الدخول» الحيّ · فإن سقط كرونُ العامل في البريماركت فالقائمةُ <b>ناقصةٌ لا فارغة</b> (آخرُ لقطته أعلاه يكشف ذلك) · "
                  "والسجلُّ الليليّ لـT-SHADOW يُبنى من الحالة نفسِها بعد الإغلاق فقد يختلف إن أُعيدت مرساةٌ بعد 09:25."]
    L += ["", "⚠️ قيد الإثبات: الحكمُ على T-SHADOW بعد 2026-12-31 · عرضٌ لا توصية."]
    return "\n".join(L)


def send_window(now_ny):
    """🔒 **نقيّة**: (انتظارٌ بالثواني، يُرسَل الآن؟) — قبل 09:25 انتظار · 09:25-09:29 إرسال · بعده لا."""
    m = now_ny.hour * 60 + now_ny.minute
    if m < SEND_AT_NY:
        target = now_ny.replace(hour=SEND_AT_NY // 60, minute=SEND_AT_NY % 60, second=0, microsecond=0)
        return (target - now_ny).total_seconds(), False
    return 0.0, m < OPEN_NY


def _load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _refresh(runner=subprocess.run):
    """main طازجٌ قبل البناء (`op_entry_state.json` يكتبه العاملُ الحيّ كلَّ دقائق)."""
    for cmd in (["git", "fetch", "--quiet", "origin", "main"], ["git", "reset", "--hard", "--quiet", "FETCH_HEAD"]):
        r = runner(cmd, capture_output=True, text=True, timeout=120)
        if getattr(r, "returncode", 1) != 0:
            log(f"⚠️ المزامنة ({' '.join(cmd[:2])}) rc={getattr(r, 'returncode', '?')} — يُبنى على النسخة الحاليّة")
            return False
    return True


def _inputs(day, dailies_fn=None, bars_fn=None):
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    dailies_fn = dailies_fn or (lambda s: daily_range(s, day, key) if key else None)
    bars_fn = bars_fn or (lambda s: fetch_day(s, day, key) if key else None)
    ledger = {(r["date"], r["symbol"]): r for r in load_ledger()}
    return dailies_fn, bars_fn, ledger, (lambda s: split_fn(s, day, key))


def replay_day(day, dailies_fn=None, bars_fn=None):
    """🔁 إعادةُ بناء قائمة يومٍ ماضٍ من الحالة الحاليّة — **تطبع ولا تُرسل ولا تختم** (لا نداءَ لتلغرام ولا كتابة) ⟵ 0."""
    state = _load(STATE) or {}
    dailies_fn, bars_fn, ledger, split_of = _inputs(day, dailies_fn, bars_fn)
    rows, allr, skipped = shadow_rows(premarket_anchors(state, day), dailies_fn, day, bars_fn, ledger, split_of)
    log(build_message(day, "إعادة", rows, allr, last_state_ms(state, day), first=False, skipped=skipped))
    log(f"🔁 REPLAY {day} · S=" + ",".join(r["sym"] for r in rows) + f" · مراسٍ={len(allr)} · مستبعَد={skipped}")
    return 0


def main(now_fn=None, runner=subprocess.run, dailies_fn=None, send_fn=None, save_fn=None, bars_fn=None):
    import market_calendar as MC
    now_fn = now_fn or (lambda: dt.datetime.now(NY))
    now = now_fn()
    replay = (os.environ.get("SHADOW_TG_REPLAY") or "").strip()
    if replay:
        return replay_day(replay, dailies_fn, bars_fn)
    day = now.date().isoformat()
    if now.isoweekday() > 5 or MC.session_info(day).get("open_ny_min") is None:
        log(f"📭 {day} ليس جلسة — لا رسالة")
        return 0
    stamp = _load(STAMP) or {}
    if stamp.get("last_sent") == day:
        log(f"📭 أُرسلت قائمةُ {day} سلفًا — لا تكرار")
        return 0
    wait, ok = send_window(now)
    if wait > WAIT_MAX_S:
        log(f"⏳ الانتظار {wait / 60:.0f} د فوق السقف — خروج بلا إرسال")
        return 0
    if wait > 0:
        log(f"⏳ أنتظر {wait / 60:.0f} دقيقة حتى 09:25 نيويورك")
        _sleep(wait)
        now = now_fn()
        wait, ok = send_window(now)
    if not ok:
        log(f"⛔ {now.strftime('%H:%M')} نيويورك بعد الافتتاح أو عنده — لا إرسال (الأمرُ «قبل الافتتاح»)")
        return 0
    if runner is not None:
        _refresh(runner)
    stamp = _load(STAMP) or {}
    if stamp.get("last_sent") == day:
        log(f"📭 أُرسلت قائمةُ {day} سلفًا (بعد المزامنة) — لا تكرار")
        return 0
    state = _load(STATE) or {}
    dailies_fn, bars_fn, ledger, split_of = _inputs(day, dailies_fn, bars_fn)
    anchors = premarket_anchors(state, day)
    rows, allr, skipped = shadow_rows(anchors, dailies_fn, day, bars_fn, ledger, split_of)
    built = now_fn().strftime("%H:%M")
    msg = build_message(day, built, rows, allr, last_state_ms(state, day), first=not stamp.get("first_sent"), skipped=skipped)
    log(msg)
    if (os.environ.get("SHADOW_TG_SEND") or "").strip() != "1":
        log("🔒 SHADOW_TG_SEND≠1 — بُنيت ولم تُرسَل")
        return 0
    if send_fn is None:
        import Super_stock as S
        send_fn = lambda t: S.send_telegram(t + "\n\n" + S.FOOTER)                    # noqa: E731
    if not send_fn(msg):
        log("⛔ لم تصل الرسالة — لا ختم (يُعاد في التشغيلة الاحتياطيّة التالية قبل الافتتاح)")
        return 1
    stamp = {"last_sent": day, "first_sent": stamp.get("first_sent") or day, "built_ny": built, "n_s": len(rows),
             "n_anchors": len(allr), "skipped": skipped, "symbols": [r["sym"] for r in rows]}
    with open(STAMP, "w", encoding="utf-8") as fh:
        json.dump(stamp, fh, ensure_ascii=False, indent=1)
    if save_fn is None:
        import Super_stock as S
        save_fn = lambda: S.git_save([STAMP])                                         # noqa: E731
    save_fn()
    log(f"✅ أُرسلت قائمةُ الظلّ ({len(rows)} اسمًا من {len(allr)} مرساة) وخُتمت")
    return 0


if __name__ == "__main__":
    sys.exit(main())
