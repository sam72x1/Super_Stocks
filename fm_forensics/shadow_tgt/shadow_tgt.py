#!/usr/bin/env python3
"""🌘🎯 `T-SHADOW-TGT` — «عقدُ هدفٍ للظلّ أماميًّا» (العقد `fm_forensics/shadow_tgt/T_SHADOW_TGT_prereg.md` · مدموجٌ قبل أيّ رقم).

**التقاطُ مستويات الذراع ② عند 09:25 (§④):** يُنادى من `shadow_telegram.main` **بعد** إرسال الرسالة وختمها ⟵ لكلّ مرساةِ بريٍّ قبل وقت البناء: الرمزُ
النشطُ في قائمة البوت ⟵ `stop`/`t1`/`t2` منها (`list`) · وإلّا `analyze_one.analyze_on_demand` بالاسم على الشموع اليوميّة **قبل يوم الصفّ وحدَها**
(`stop[0]` = حقلُ القائمة نفسُه · `on_demand`) · والتعذّرُ ⟵ صفٌّ بسببه لا رقم. ⚠️ وشموعُ الأربع ساعات داخل التحليل حتى لحظة الالتقاط (09:25) — بلا نظرٍ لما بعدها.
🔒 الملفُّ `shadow_tgt_levels.jsonl` إلحاقيٌّ (لا يُعدَّل صفٌّ مكتوب · ولا يُكرَّر (يوم، رمز)) · فاشلٌ-آمنٌ مطلقًا: أيُّ عطلٍ ⟵ سطرُ سجلٍّ ولا يمسّ الرسالة ولا الختم ·
ولا تلغرام · ولا قاعدةَ S · وأداةُ الحكم (`run`) تُبنى في PR لاحق قبل أوانه.
"""
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

LEVELS_FILE = "shadow_tgt_levels.jsonl"          # نسبةً إلى جذر المستودع (cwd الـworkflow)
WATCHLIST = "weekly_watchlist.json"
TGT_FROM = "2026-11-09"                          # §① أماميٌّ خالص


def list_levels(sym, wl):
    """مستوياتُ الرمز **النشط** في قائمة البوت ⟵ dict أو None."""
    for s in (wl or {}).get("stocks") or []:
        if str(s.get("symbol") or "").upper() == sym and s.get("status") == "active":
            try:
                return {"stop": float(s["stop"]), "t1": float(s["t1"]), "t2": float(s["t2"])}
            except (KeyError, TypeError, ValueError):
                return None
    return None


def before_day(day, dl):
    """غلافٌ لـ`download_history` يقصّ كلَّ إطارٍ إلى الجلسات **قبل** `day` (لا شمعةَ ليوم الصفّ)."""
    def _dl(syms, *a, **k):
        data = dl(syms, *a, **k) or {}
        out = {}
        for s, df in data.items():
            out[s] = None if df is None else df[[str(x)[:10] < day for x in df.index]]
        return out
    return _dl


def on_demand_levels(sym, day, ao=None):
    """`analyze_one.analyze_on_demand` بالاسم على الشموع قبل `day` ⟵ (dict | None، السبب)."""
    if ao is None:
        import analyze_one as ao
    keep = ao.bot.download_history
    try:
        ao.bot.download_history = before_day(day, keep)
        res = ao.analyze_on_demand(sym)
    except Exception as e:                                          # noqa: BLE001
        return None, f"تعذّر: {type(e).__name__}"
    finally:
        ao.bot.download_history = keep
    r = res[0] if res else None
    if not r:
        return None, str(res[1] if res and len(res) > 1 else "تعذّر")[:80]
    try:
        return {"stop": float(r["stop"][0]), "t1": float(r["t1"]), "t2": float(r["t2"])}, "ok"
    except (KeyError, TypeError, ValueError, IndexError):
        return None, "بلا مستويات"


def _done(path):
    seen = set()
    try:
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                if ln.strip():
                    x = json.loads(ln)
                    seen.add((x.get("date"), x.get("symbol")))
    except OSError:
        pass
    return seen


def capture(day, syms, wl=None, levels_of=None, path=None, now=None, log=print):
    """§④ ⟵ عددُ الصفوف المكتوبة. `syms` رموزُ مراسي البري قبل وقت البناء · `levels_of(sym, day)` محقونٌ للاختبار."""
    if str(day) < TGT_FROM:
        log(f"🎯 T-SHADOW-TGT: {day} قبل {TGT_FROM} — لا التقاط")
        return 0
    path = path or LEVELS_FILE
    levels_of = levels_of or on_demand_levels
    if wl is None:
        try:
            with open(WATCHLIST, encoding="utf-8") as fh:
                wl = json.load(fh)
        except (OSError, ValueError):
            wl = {}
    seen = _done(path)
    rows = []
    stamp = (now or dt.datetime.now(dt.timezone.utc)).isoformat(timespec="seconds")
    for sym in syms:
        sym = str(sym).upper()
        if (day, sym) in seen:
            continue
        lv, src, why = list_levels(sym, wl), "list", "ok"
        if lv is None:
            try:
                lv, why = levels_of(sym, day)
            except Exception as e:                                  # noqa: BLE001
                lv, why = None, f"تعذّر: {type(e).__name__}"
            src = "on_demand" if lv else "none"
        row = {"schema": 1, "date": day, "symbol": sym, "src": src, "why": why, "captured_at": stamp}
        if lv:
            row.update({k: round(lv[k], 6) for k in ("stop", "t1", "t2")})
        rows.append(row)
        seen.add((day, sym))
    if rows:
        with open(path, "a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    log(f"🎯 T-SHADOW-TGT التقاطُ 09:25: {len(rows)} رمزًا · من القائمة {sum(r['src'] == 'list' for r in rows)} · "
        f"بالتحليل {sum(r['src'] == 'on_demand' for r in rows)} · بلا مستويات {sum(r['src'] == 'none' for r in rows)}")
    return len(rows)
