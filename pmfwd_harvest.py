#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌅📡 `T-PMFWD` — الحصّادُ الأماميّ (العقد `pmfwd_prereg.md` مدموجٌ قبل هذا الملفّ).

يمشي **بعد إغلاق الافتر** فيسجّل لكلّ رمزٍ في قائمتنا الحيّة صفًّا واحدًا لهذا
اليوم: سيولةُ بريماركته · حركتُه في الجلسة النظاميّة · وهل أطلقت له طبقةُ
السيولة. **حصادٌ فقط — لا حكمَ هنا ولا رسالةَ تُرسَل** (الحكمُ في `pmfwd_report.py`).

🔑 **الشمعةُ الدقيقيّةُ لليوم تحمل البريماركتَ والجلسةَ معًا** ⇒ جوبٌ واحدٌ بعد
الإغلاق يكفي، والقياسُ **حتميٌّ يُعاد بالأمر نفسِه** بلا سباقِ توقيتٍ حيّ.

🔒 **الكتابةُ الوحيدةُ في هذا الملفّ سطرُ إلحاقٍ إلى `LOG`** — بنصّ §⑨ —
والدِدوبُ بمفتاح `(يوم، رمز)` فإعادةُ التشغيل لا تُضاعف صفًّا. وصفرُ إسنادٍ إلى
`CONFIG` (‏`no_config_assign` بالاسم).
⚖️ **و`selfcheck_readonly` لا تنطبق هنا وتُرجع `False` عن قصد** — فالملفُّ يكتب
السجلَّ بتصميم العقد؛ تنطبق على `pmfwd_report.py` الذي **يحكم ولا يكتب**.
وحارسُ هذا الملفّ `append_only` (`V-W3`).
🔴 **وثغرةٌ حقيقيّةٌ كُشفت أثناء بنائه:** تمريرُ وضع الفتح **متغيّرًا** كان
يُمرِّر ملفًّا كاتبًا على `selfcheck_readonly` لأنها تقرأ الثابتَ النصّيَّ وحدَه
⇒ **شُدَّ الحارسُ في `optrade_arms` ولم يُرخَ**، وصار ما لا يُثبَت أنه قراءةٌ
يُعَدّ كتابةً. **يُقال ولا يُطوى.**
"""
import ast as _ast
import datetime as _dt
import json
import os
import sys

from link100_probe import pm_feats, ticker_daily                 # بالاسم
from market_calendar import is_trading_day                       # بالاسم
from opcurve_probe import NY, ny_hour                            # بالاسم
from optrade_arms import no_config_assign                        # بالاسم
from tier_fwd_report import fetch_day                            # بالاسم

# ═══════════════ ⓪ الحدود — مثبَّتةٌ بالعقد §③ و§⑨ ════════════════════════════
LOG = "pmfwd_log.jsonl"
WL = "weekly_watchlist.json"
OP_STATE = "op_entry_state.json"
DRY = os.environ.get("PMFWD_DRY", "").strip() == "1"
DAY_OVERRIDE = os.environ.get("PMFWD_DAY", "").strip()

REG_OPEN, REG_CLOSE = 9.5, 16.0        # الجلسةُ النظاميّة بتوقيت نيويورك
MIN_COVER = 0.95                       # `V-W2`
RC_OK, RC_NOKEY, RC_COVER, RC_NOROW, RC_GUARD = 0, 2, 3, 4, 6

_CALLS = {"write": 0}


def _log(msg: str = "") -> None:
    print(msg, flush=True)


# ═══════════════ ① المجتمع (§②) ═══════════════════════════════════════════════
def watch_symbols(path: str = WL):
    """رموزُ القائمة الحيّة — النشطُ من `stocks` ‏+ كلُّ `pullback` (§②).

    و`None` عند تعذّر التحميل ⇒ اليومُ **يُسجَّل غيابًا صريحًا** (`V-W1`) ولا يُطوى."""
    try:
        wl = json.load(open(path, encoding="utf-8"))
    except Exception:                                            # noqa: BLE001
        return None
    out = set()
    for s in wl.get("stocks") or []:
        if s.get("status") == "active" and s.get("symbol"):
            out.add(str(s["symbol"]).upper())
    for r in wl.get("pullback") or []:
        if r.get("symbol"):
            out.add(str(r["symbol"]).upper())
    return sorted(out)


def fired_of(day: str, path: str = OP_STATE):
    """`(رموزُ الإطلاق في اليوم، هل القراءةُ موثوقة؟)` — §③ · §⑦-4.

    🔴 الحالةُ **تُكتَب فوق نفسها** فلا تحمل إلّا أحدثَ يوم ⇒ الموثوقيّةُ أن
    أحدثَ تاريخٍ فيها **ليس أقدمَ من اليوم المقيس**؛ وإلّا فالعاملُ لم يعمل
    ذلك اليوم ⇒ `ok=False` واليومُ **يُقصى من `C-LIQ` ويُعَدّ** لا يُطوى."""
    try:
        st = json.load(open(path, encoding="utf-8"))
    except Exception:                                            # noqa: BLE001
        return set(), False
    rows = [(k[4:], v) for k, v in st.items()
            if k.startswith("LIQ:") and isinstance(v, dict) and v.get("date")]
    if not rows:
        return set(), False
    newest = max(v["date"] for _s, v in rows)
    return ({s for s, v in rows if v.get("date") == day}, newest >= day)


def target_day(now=None) -> str:
    """آخرُ يومِ تداولٍ **أُغلقت جلستُه النظاميّة** بتوقيت نيويورك.

    فلو تأخّر الكرون (والتأخّرُ عندنا مقيسٌ بمئات الدقائق) بقي اليومُ المقيسُ
    هو هو، ولا ينزلق الحصادُ إلى يومٍ لم يُغلَق بعد."""
    t = now or _dt.datetime.now(_dt.timezone.utc)
    ny = t.astimezone(NY)
    d = ny.date()
    if ny.hour + ny.minute / 60.0 < REG_CLOSE:
        d -= _dt.timedelta(days=1)
    for _ in range(12):
        if d.weekday() < 5 and is_trading_day(d.isoformat()):
            return d.isoformat()
        d -= _dt.timedelta(days=1)
    return d.isoformat()


# ═══════════════ ② الصفّ (§③) ═════════════════════════════════════════════════
def day_row(bars, prev_close):
    """`pm_usd` قبل الجرس و`mv` من الجلسة النظاميّة — أو `None` بلا جلسة.

    `mv` = (أعلى الجلسة النظاميّة ÷ **أوّلِ إغلاقِ دقيقةٍ عند 09:30 أو بعدها**) − 1
    بنصّ §③ — والسلّةُ من `pm_feats` بالاسم فهي سلّةُ `T-PMUSD` نفسُها."""
    if not bars:
        return None
    pre = [b for b in bars if ny_hour(b[0]) < REG_OPEN]
    reg = [b for b in bars if REG_OPEN <= ny_hour(b[0]) < REG_CLOSE]
    if not reg:
        return None
    o930 = reg[0][4]
    hi = max(b[2] for b in reg)
    f = pm_feats(bars, prev_close)                               # بالاسم
    return {"pm_usd": f["pm_usd"],
            "pm_raw": round(sum(b[4] * b[5] for b in pre), 2),
            "open930": o930, "reg_hi": hi,
            "mv": (round((hi / o930 - 1.0) * 100.0, 4) if o930 else None),
            "n_pre": len(pre), "n_reg": len(reg)}


def seen_keys(path: str = LOG):
    """مفاتيحُ `(يوم، رمز)` المسجَّلةُ سلفًا — الدِدوبُ بنصّ §⑨."""
    out = set()
    try:
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    r = json.loads(ln)
                except Exception:                                # noqa: BLE001
                    continue
                if r.get("day") and r.get("sym"):
                    out.add((r["day"], r["sym"]))
    except FileNotFoundError:
        return out
    except Exception:                                            # noqa: BLE001
        return out
    return out


def append_rows(rows, path: str = LOG):
    """🔒 **الكتابةُ الوحيدةُ في هذا الملفّ** — إلحاقٌ سطرًا سطرًا، ولا `w` أبدًا.

    🔴 والوضعُ **ثابتٌ حرفيٌّ `"a"`** عمدًا: تمريرُه متغيّرًا كان يُمرِّر الملفَّ
    على `selfcheck_readonly` **وهو يكتب** — ثغرةٌ حقيقيّةٌ كشفها هذا الملفُّ
    بنفسه فشُدّ الحارسُ (‏`optrade_arms`) ولم يُرخَ."""
    _CALLS["write"] += 1
    with open(path, "a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")
    return len(rows)


def append_only(src: str = None) -> bool:
    """`V-W3` — **حارسُ الحصّاد**: كتابةٌ واحدةٌ إلى مسارٍ واحدٍ بوضعِ إلحاق.

    `selfcheck_readonly` لا تنطبق هنا (الملفُّ يكتب السجلَّ **بتصميم العقد §⑨**)
    ⇒ الحارسُ البديلُ يُثبت بالـAST: **كلُّ** `open` بوضعِ كتابةٍ وضعُه `"a"`
    حرفيًّا · وعددُها **واحد** · ومسارُها الوسيطُ `path` لا مسارٌ آخر · وصفرُ
    نداءِ إرسالٍ أو حفظِ حالةٍ إنتاجيّة."""
    banned = {"send_telegram", "send_telegram_document", "git_save",
              "save_watchlist", "save_op_entry_state", "record_new_alerts"}
    try:
        tree = _ast.parse(src if src is not None
                          else open(__file__, encoding="utf-8").read())
    except Exception:                                            # noqa: BLE001
        return False
    writes = 0
    for n in _ast.walk(tree):
        if not isinstance(n, _ast.Call):
            continue
        fn = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
        if fn in banned:
            return False
        if fn != "open":
            continue
        mode = None
        if len(n.args) > 1:
            mode = n.args[1]
        for kw in n.keywords or []:
            if kw.arg == "mode":
                mode = kw.value
        if mode is None:
            continue                                   # قراءةٌ صريحة
        if not (isinstance(mode, _ast.Constant) and mode.value == "a"):
            return False
        if not (n.args and getattr(n.args[0], "id", None) == "path"):
            return False
        writes += 1
    return writes == 1


# ═══════════════ ③ التشغيل ════════════════════════════════════════════════════
def main() -> int:                                               # noqa: PLR0911
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        _log("⛔ لا POLYGON_API_KEY — خروج 2")
        return RC_NOKEY
    src = open(__file__, encoding="utf-8").read()
    if not (no_config_assign(src) and append_only(src)):          # بالاسم ‏+ `V-W3`
        _log("⛔ حارسُ «إلحاقٌ واحدٌ / صفرُ إسنادٍ إلى CONFIG» ساقط — خروج 6")
        return RC_GUARD
    day = DAY_OVERRIDE or target_day()
    _log("🌅📡 T-PMFWD — الحصّادُ الأماميّ (العقد `pmfwd_prereg.md`)")
    _log(f"⚙️ اليومُ المقيس: {day} · العتبةُ `>1M` من `pm_feats` · "
         f"السجلُّ {LOG} (إلحاقٌ · دِدوبٌ بمفتاح يوم/رمز)")
    if DRY:
        _log("🧪 وضعُ جدوى `PMFWD_DRY=1` — ثلاثةُ أعدادٍ ثمّ عودةٌ **قبل أيّ "
             "كتابةٍ للسجلّ وقبل أيّ نسبة**")

    syms = watch_symbols()
    if syms is None:
        row = {"day": day, "sym": "—", "absent": "watchlist_unreadable"}
        _log("🔴 `V-W1` — تعذّر تحميلُ القائمة ⇒ يُسجَّل غيابًا صريحًا")
        if not DRY:
            append_rows([row])
        return RC_NOROW
    fired, fired_ok = fired_of(day)
    seen = seen_keys()
    _log(f"👥 رموزُ القائمة {len(syms)} · أطلقت لها الطبقةُ {len(fired)} "
         f"(موثوقيّةُ القراءة: {'✅' if fired_ok else '🔴 العاملُ لم يعمل'}) · "
         f"مسجَّلٌ سلفًا لهذا اليوم "
         f"{sum(1 for s in syms if (day, s) in seen)}")

    rows, got, miss = [], 0, 0
    for s in syms:
        if (day, s) in seen:
            continue
        bars = fetch_day(s, day, key)                            # بالاسم
        pc = None
        h = ticker_daily(s, (_dt.date.fromisoformat(day)
                             - _dt.timedelta(days=12)).isoformat(), day, key)
        if h:
            i = next((k for k, b in enumerate(h) if b[0] == day), None)
            if i is not None and i >= 1:
                pc = h[i - 1][4]
        r = day_row(bars, pc) if bars else None
        if r is None:
            miss += 1
            rows.append({"day": day, "sym": s, "absent": "no_bars",
                         "fired": (s in fired), "fired_ok": fired_ok})
            continue
        got += 1
        r.update({"day": day, "sym": s, "prev_close": pc,
                  "fired": (s in fired), "fired_ok": fired_ok})
        rows.append(r)

    total = got + miss
    cover = (got / total) if total else 0.0
    over = sum(1 for r in rows if r.get("pm_usd") == ">1M")
    _log(f"📊 صفوفٌ جديدة {len(rows)} · تغطيةُ الجلب {got}/{total} "
         f"(‏{cover * 100:.1f}%) · العابرون `>1M` {over}")
    if DRY:
        _log(f"🧪 نداءاتُ الكتابة = {_CALLS['write']} (يجب أن تكون صفرًا) — "
             "وضعُ الجدوى يعود الآن بلا كتابةٍ وبلا نسبة")
        return RC_OK
    if not rows:
        _log("ℹ️ لا صفَّ جديدًا (كلُّه مسجَّلٌ سلفًا) — لا كتابة")
        return RC_OK
    if total and cover < MIN_COVER:
        for r in rows:
            r["short_cover"] = True
        _log(f"🔴 `V-W2` — التغطيةُ دون {MIN_COVER * 100:.0f}% ⇒ "
             "اليومُ **يُوسَم ناقصًا** ويُقصى من الحكم ويُعَدّ")
    n = append_rows(rows)
    _log(f"💾 أُلحق {n} صفًّا بـ{LOG}")
    return RC_OK if (not total or cover >= MIN_COVER) else RC_COVER


if __name__ == "__main__":
    sys.exit(main())
