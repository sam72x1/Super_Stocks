# -*- coding: utf-8 -*-
"""🔎 **مُعرِّف الشارت** — صورةُ شارتٍ لأيّ سهمٍ أمريكيّ ⟵ رمزُه **بالدليل**، أو «لا أعرف» بصراحة.

أمرُ المالك (2026-09-24) — البرومبتُ بنصّه في `chart_finder_prereg.md §⓪`.

🔒 **قراءةٌ فقط:** لا حالة · لا تلغرام · خارج الجذور والفرز · لا يستورد البوت.
   أسرارُه: `POLYGON_API_KEY` ومفتاحا الملفّات المجمَّعة (`POLYGON_S3_KEY`/`POLYGON_S3_SECRET`).

**المراحل:**
  أ) **البطاقة** — JSON يكتبه Claude داخل الجلسة من الصورة. **الصورةُ لا تُدفَع** (المستودعُ عامّ)
     ولا تحمل البطاقةُ الرمز. وكلُّ رقمٍ **نصٌّ كما قُرئ** ⇒ التسامح = نصفُ آخر خانةٍ مسجَّلة
     (قاعدةُ `faisal_indicator_anchor.half_ulp` — بُنيت لتأريخ سهمٍ **معروف** من قيمة مؤشّر —
     ومُدّت هنا للاحقتَي K/M وللنسبة) **+ هامشُ مصدر البيانات** `FEED_TOL_PCT` (التطبيقُ غيرُ Polygon).
  ب) **البحث — السوقُ كلُّه:**
     • **مرساةٌ لحظيّةٌ مؤرَّخة** (رأسُ الشارت: O/H/L/C لشمعةٍ بتاريخها ووقتها) ⟵ **ملفُّ دقائق
       ذلك اليوم لكلّ الرموز** ⟵ تُبنى الشمعةُ بكلّ تعريفٍ معقول (المدى × تسميةُ البداية أو
       النهاية × نيويورك ثم توقيتُ الجهاز) ⟵ مطابقةُ الأسعار الأربعة.
     • **قيودُ النافذة** (أعلى/أدنى الشاشة · آخرُ سعر) لكلّ مرشّح من دقائقه الخام، **ثم تسويةُ
       التقسيم حتى آخر شمعةٍ ظاهرة** — الشارتُ يعرض التسوية حتى لحظة التقاطه فقط.
  ج) **التحقّق** — يطبع سلسلةَ أعلى 3 مرشّحين (`SERIES_D`/`SERIES_I`) ⇒ تُرسم في الجلسة
     وتُقارَن بالأصل **بالعين** قبل أيّ جواب.

**والحكم:** `CHART_FINDER card=… verdict=… top1=… top2=… passers=… exit=…` في آخر سطر.
«واثق» آليًّا = **مرشّحٌ وحيدٌ** يعبر كلَّ قيدٍ نصّيّ ضمن تسامحه (قيدان مستقلّان على الأقل)
— والشرطُ الثالث (المقارنةُ بالعين) خارج الأداة بالبناء، فلا تقول الأداةُ «واثق» نهائيًّا.
"""
from __future__ import annotations

import bisect
import datetime as dt
import gzip
import json
import math
import os
import sys
import tempfile
import time as _time
from zoneinfo import ZoneInfo

import requests

import ah_scan                       # day_key · head_size_mb · download (بُنيت لقياس الافتر · خفيفةُ الاستيراد)
import flatfiles_probe as FP         # مفاتيحُ S3 ومنافذُها (بُنيت لمِجَسّ الجدوى)
import market_calendar as MC         # أيامُ التداول وحدودُ الجلسة

NY = ZoneInfo("America/New_York")
API = "https://api.polygon.io"
CARD_VERSION = 1

# ── العتبات (هندسيّة · مُعلنةٌ في العقد قبل أيّ قياسٍ على المجموعة الحقيقيّة) ─────────────
FEED_TOL_PCT = 0.5        # هامشُ اختلاف مصدر البيانات بين التطبيق وPolygon (نسبةٌ من القيمة)
VOL_TOL_PCT = 5.0         # الحجمُ أشدُّ اختلافًا بين المصادر (شروطُ الصفقات) ⇒ ترتيبٌ لا بوّابة
DECISIVE_RATIO = 3.0      # «مرجّح» بين عابرَين: خطأُ الثاني ‏3 أضعاف الأوّل على الأقل
WINDOW_SLACK_DAYS = 3     # النافذةُ المقروءة من المحور تقريبيّة ⇒ الطرفُ الأقصى يُقبل داخل ±3 أيام تداول
SPANS = (1, 2, 3, 5, 10, 15, 30, 45, 60, 90, 120, 180, 240, 390, 960)
DEVICE_TZ = "Asia/Riyadh"  # توقيتُ جهاز المالك — يُجرَّب ثانيًا بعد نيويورك
TOP_SERIES = 3
ANCHOR_MAX = 25            # أقصى عابري المرساة تُفحص نوافذُهم (دقائق REST لكلٍّ) — والمقصوصُ يحجب «واثق»
DAYS_PER_BAR = {"1D": 1.0, "1W": 5.0, "1M": 21.0}      # أيامُ تداولٍ لكلّ شمعة (اليوميّ فما فوقه)
INTRADAY_SPAN = {"1m": 1, "2m": 2, "3m": 3, "5m": 5, "10m": 10, "15m": 15, "30m": 30, "45m": 45,
                 "1H": 60, "2H": 120, "3H": 180, "4H": 240}
EXT_OPEN_MIN, EXT_CLOSE_MIN = 4 * 60, 20 * 60
FORBIDDEN_KEYS = {"ticker", "symbol", "sym", "رمز", "الرمز"}
TIMEFRAMES = {"1m", "2m", "3m", "5m", "10m", "15m", "30m", "45m", "1H", "2H", "3H", "4H",
              "1D", "1W", "1M", "intraday", "unknown"}
_BIDI = ("‎", "‏", "‪", "‫", "‬", "‭", "‮",
         "⁦", "⁧", "⁨", "⁩", "؜")
_SUFFIX = {"K": 1e3, "M": 1e6, "B": 1e9}


def log(m: str = "") -> None:
    print(m, flush=True)


# ══ أ) البطاقة — دوالُّ نقيّة ═══════════════════════════════════════════════════════
def parse_num(txt):
    """الرقمُ كما قُرئ ⟵ `(القيمة، نصفُ آخر خانة)`. تعذّرٌ ⟵ `None` (لا يُخمَّن).

    «2.30» ⟵ (2.30, 0.005) · «6.43K» ⟵ (6430, 5) · «+3.99%» ⟵ (3.99, 0.005) ·
    «‑0.9957» ⟵ (-0.9957, 0.00005) · «1,234» ⟵ (1234, 0.5)."""
    if txt is None or isinstance(txt, bool):
        return None
    if isinstance(txt, (int, float)):
        txt = repr(txt)
    t = str(txt).strip()
    for ch in _BIDI:
        t = t.replace(ch, "")
    t = (t.replace("−", "-").replace("‑", "-").replace("–", "-")
         .replace(",", "").replace("%", "").replace("+", "").replace("$", "").strip())
    mult = 1.0
    if t and t[-1].upper() in _SUFFIX:
        mult, t = _SUFFIX[t[-1].upper()], t[:-1].strip()
    try:
        v = float(t)
    except ValueError:
        return None
    if not math.isfinite(v):
        return None
    n = len(t.split(".")[1]) if "." in t else 0
    return (v * mult, 0.5 * (10.0 ** (-n)) * mult)


def num_spec(x):
    """رقمُ البطاقة ⟵ `(قيمة، تسامحُ القراءة)`:
    • نصٌّ مقروء ⟵ `parse_num` (نصفُ آخر خانة).
    • `{"v": "2.35", "src": "pixel", "tol": "0.02"}` ⟵ قراءةُ بكسل **بتسامحٍ مصرَّح** — وبلا `tol`
      ⟵ `None` (لا يُخمَّن تسامحُ قراءةٍ تقريبيّة).
    • `{"v": "2.35", "src": "text"}` ⟵ كالنصّ."""
    if isinstance(x, dict):
        base = parse_num(x.get("v"))
        if base is None:
            return None
        if str(x.get("src") or "text") == "pixel":
            tol = parse_num(x.get("tol"))
            return None if tol is None or tol[0] <= 0 else (base[0], abs(tol[0]))
        return base
    return parse_num(x)


def _walk_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from _walk_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_keys(v)


def _iso(d) -> bool:
    try:
        dt.date.fromisoformat(str(d))
        return True
    except (TypeError, ValueError):
        return False


def _hhmm(t):
    try:
        hh, mm = str(t).strip().split(":")
        hh, mm = int(hh), int(mm)
    except (ValueError, AttributeError):
        return None
    return hh * 60 + mm if 0 <= hh <= 24 and 0 <= mm < 60 else None


def validate_card(card) -> list:
    """أخطاءُ البطاقة بالعربيّة — فارغةٌ = سليمة. **والبطاقةُ لا تحمل الرمز** (حقلٌ باسمه يُرفض)."""
    if not isinstance(card, dict):
        return ["البطاقةُ ليست كائنًا"]
    err = []
    if card.get("v") != CARD_VERSION:
        err.append(f"الإصدار {card.get('v')!r} ليس {CARD_VERSION}")
    if not str(card.get("id") or "").strip():
        err.append("بلا معرّف id")
    if card.get("timeframe", "unknown") not in TIMEFRAMES:
        err.append(f"فريمٌ مجهول {card.get('timeframe')!r}")
    bad = sorted({k for k in _walk_keys(card) if k.strip().lower() in FORBIDDEN_KEYS})
    if bad:
        err.append(f"البطاقةُ تحمل الرمز ({bad}) — ممنوع")
    a = card.get("anchor")
    if a is not None:
        if not isinstance(a, dict) or not _iso(a.get("date")):
            err.append("المرساةُ بلا تاريخٍ صالح")
        else:
            if a.get("time") is not None and _hhmm(a.get("time")) is None:
                err.append(f"وقتُ المرساة غيرُ صالح {a.get('time')!r}")
            for f in ("o", "h", "l", "c", "v", "chg_pct"):
                if a.get(f) is not None and num_spec(a.get(f)) is None:
                    err.append(f"المرساة.{f} لا يُقرأ رقمًا")
            h, l_ = num_spec(a.get("h")), num_spec(a.get("l"))
            if h and l_ and h[0] < l_[0]:
                err.append("المرساة: الأعلى دون الأدنى")
    ex = card.get("extremes")
    if ex is not None:
        hi, lo = num_spec((ex or {}).get("high")), num_spec((ex or {}).get("low"))
        if (ex or {}).get("high") is not None and hi is None:
            err.append("أعلى الشاشة لا يُقرأ")
        if (ex or {}).get("low") is not None and lo is None:
            err.append("أدنى الشاشة لا يُقرأ")
        if hi and lo and hi[0] < lo[0]:
            err.append("أعلى الشاشة دون أدناها")
    w = card.get("window")
    if w is not None:
        if not (isinstance(w, dict) and _iso(w.get("from")) and _iso(w.get("to"))):
            err.append("النافذةُ بلا تاريخين صالحين")
        elif w["from"] > w["to"]:
            err.append("بدايةُ النافذة بعد نهايتها")
    if card.get("last") is not None and num_spec(card.get("last")) is None:
        err.append("آخرُ سعرٍ لا يُقرأ")
    searchable = ((isinstance(a, dict) and _iso(a.get("date"))
                   and any(a.get(f) is not None for f in ("o", "h", "l", "c")))
                  or (ex and (ex.get("high") is not None or ex.get("low") is not None))
                  or card.get("last") is not None)
    if not searchable:
        err.append("لا قيدَ قابلًا للبحث (مرساةٌ مؤرَّخة أو أعلى/أدنى الشاشة أو آخرُ سعر)")
    return err


def tol_near(spec, pct: float = FEED_TOL_PCT) -> float:
    """تسامحُ «ضمن تسامحه» = نصفُ آخر خانة + هامشُ المصدر."""
    v, hu = spec
    return hu + pct / 100.0 * abs(v)


def field_check(val, spec, pct: float = FEED_TOL_PCT) -> dict:
    """قيمةٌ مقيسة مقابل رقمٍ مقروء ⟵ `{strict, near, err}` · و`err` = الفرقُ ÷ التسامح."""
    if val is None or spec is None:
        return {"strict": False, "near": False, "err": math.inf, "val": val}
    d = abs(float(val) - spec[0])
    tn = tol_near(spec, pct)
    return {"strict": d <= spec[1] + 1e-12, "near": d <= tn + 1e-12,
            "err": d / tn if tn > 0 else (0.0 if d == 0 else math.inf), "val": val}


def anchor_specs(anchor) -> dict:
    """حقولُ المرساة المقروءة ⟵ `{o,h,l,c,v: (قيمة، نصف خانة)}` (الغائبُ لا يُدرج)."""
    out = {}
    for f in ("o", "h", "l", "c", "v"):
        s = num_spec((anchor or {}).get(f))
        if s is not None:
            out[f] = s
    return out


# ══ ب) الوقت وتعريفاتُ الشمعة ══════════════════════════════════════════════════════
def ny_offset_min(day: str, tzname: str) -> int:
    """كم دقيقةً تُضاف لوقتٍ محلّيّ في `tzname` ليصير وقتَ نيويورك في يومٍ بعينه (ظهرًا)."""
    d = dt.date.fromisoformat(day)
    noon_ny = dt.datetime(d.year, d.month, d.day, 12, 0, tzinfo=NY)
    other = noon_ny.astimezone(ZoneInfo(tzname))
    local_naive = other.replace(tzinfo=None)
    ny_naive = noon_ny.replace(tzinfo=None)
    return int(round((ny_naive - local_naive).total_seconds() / 60.0))


def anchor_defs(day: str, t_hhmm, tz_names, spans=SPANS) -> list:
    """كلُّ تعريفٍ معقولٍ لشمعة المرساة بدقائق نيويورك: `[{a, b, span, label, tz}]`.

    التسميةُ **بالنهاية** ([T−المدى، T)) أو **بالبداية** ([T، T+المدى)) · والمنطقةُ نيويورك ثم
    الجهاز. والوقتُ الغائب ⇒ الشمعةُ اليوميّة (نظاميّة وممتدّة) وحدَها."""
    out, seen = [], set()
    if t_hhmm is None:
        info = MC.session_info(day)
        op, cl = info.get("open_ny_min"), info.get("close_ny_min")
        cand = [(EXT_OPEN_MIN, EXT_CLOSE_MIN, 960, "day_ext", "America/New_York")]
        if op is not None and cl is not None:
            cand.append((op, cl, cl - op, "day_reg", "America/New_York"))
        return [{"a": a, "b": b, "span": s, "label": lb, "tz": tz} for a, b, s, lb, tz in cand]
    T = _hhmm(t_hhmm)
    for tz in tz_names:
        try:
            T_ny = T + ny_offset_min(day, tz)
        except Exception:                                           # noqa: BLE001
            continue
        for s in spans:
            for a, b, lb in ((T_ny - s, T_ny, "end"), (T_ny, T_ny + s, "start")):
                a2, b2 = max(a, 0), min(b, 24 * 60)
                if b2 - a2 < 1 or (a2, b2) in seen:
                    continue
                seen.add((a2, b2))
                out.append({"a": a2, "b": b2, "span": s, "label": lb, "tz": tz})
    return out


def intraday_grid(d: dict, lo: int = EXT_OPEN_MIN, hi: int = EXT_CLOSE_MIN) -> list:
    """شبكةُ الشموع اللحظيّة **كما يرسمها التطبيق**: حدودُها `نهايةُ المرساة + k × المدى` مقصوصةً
    إلى [04:00، 20:00) — لا من 04:00 (سلسلةٌ بمحاذاةٍ غير محاذاة التطبيق لا تُقارَن بالعين)."""
    span = max(1, int(d.get("span") or 1))
    b0 = int(d["b"])
    k_lo = -((b0 - lo) // span) - 1
    out = []
    k = k_lo
    while True:
        a, b = b0 + k * span - span, b0 + k * span
        if a >= hi:
            break
        a2, b2 = max(a, lo), min(b, hi)
        if b2 > a2:
            out.append((a2, b2))
        k += 1
    return out


def agg_bar(rows, a: int, b: int):
    """شمعةٌ من دقائقَ مرتَّبة `[(mod, o, h, l, c, v)]` داخل [a، b) ⟵ `{o,h,l,c,v,n}` أو `None`."""
    if not rows:
        return None
    mods = [r[0] for r in rows]
    i, j = bisect.bisect_left(mods, a), bisect.bisect_left(mods, b)
    sel = rows[i:j]
    if not sel:
        return None
    return {"o": sel[0][1], "h": max(r[2] for r in sel), "l": min(r[3] for r in sel),
            "c": sel[-1][4], "v": sum(r[5] for r in sel), "n": len(sel)}


def score_anchor(bar, specs: dict) -> dict:
    """مطابقةُ شمعةٍ مبنيّة لمرساةٍ مقروءة. **البوّابةُ الأسعارُ الأربعة** (الحاضرُ منها) والحجمُ
    **ترتيبٌ لا بوّابة** (يختلف بين المصادر بشروط الصفقات)."""
    res = {}
    for f in ("o", "h", "l", "c"):
        if f in specs:
            res[f] = field_check(bar.get(f) if bar else None, specs[f])
    if "v" in specs:
        res["v"] = field_check(bar.get("v") if bar else None, specs["v"], VOL_TOL_PCT)
    price = [res[f] for f in ("o", "h", "l", "c") if f in res]
    ok = bool(price) and all(r["near"] for r in price)
    score = sum(r["err"] for r in price) + (0.25 * min(res["v"]["err"], 40.0) if "v" in res else 0.0)
    return {"fields": res, "near": ok, "n_strict": sum(1 for r in price if r["strict"]),
            "n_price": len(price), "score": score}


def best_anchor_match(rows, specs: dict, defs: list):
    """أفضلُ تعريفٍ لشمعة المرساة عند رمزٍ واحد (الأقلُّ خطأً بين العابرة، وإلّا الأقلُّ خطأً)."""
    best = None
    for d in defs:
        bar = agg_bar(rows, d["a"], d["b"])
        if bar is None:
            continue
        sc = score_anchor(bar, specs)
        key = (0 if sc["near"] else 1, sc["score"])
        if best is None or key < best["key"]:
            best = {"key": key, "def": d, "bar": bar, "sc": sc}
    return best


# ══ ب′) قيودُ النافذة والتقسيم ══════════════════════════════════════════════════════
def split_factor(splits, day: str, as_of: str) -> float:
    """معاملُ تسوية سعرٍ خامٍ يومَ `day` كما يعرضه شارتٌ التُقط يومَ `as_of`: جداءُ `from/to`
    لكلّ تقسيمٍ **بعد** `day` و**حتى** `as_of` (شاملًا). عكسيٌّ 1:10 (from=10,to=1) ⟵ ×10."""
    f = 1.0
    for ex, fr, to in splits or ():
        try:
            if day < ex <= as_of and fr > 0 and to > 0:
                f *= float(fr) / float(to)
        except TypeError:
            continue
    return f


def day_extremes(minute_rows_by_day: dict, day: str, session: str = "ext"):
    """أعلى/أدنى/إغلاقُ يومٍ من دقائقه الخام: `ext` = 04:00-20:00 · `reg` = حدودُ التقويم."""
    rows = minute_rows_by_day.get(day) or []
    if session == "reg":
        info = MC.session_info(day)
        a, b = info.get("open_ny_min"), info.get("close_ny_min")
        if a is None:
            return None
    else:
        a, b = EXT_OPEN_MIN, EXT_CLOSE_MIN
    bar = agg_bar(rows, a, b)
    return bar


def window_check(daily: dict, days: list, core: tuple, spec_hi, spec_lo, spec_last=None,
                 factor_of=None) -> dict:
    """قيودُ النافذة على أيامٍ مرتَّبة `days` وشموعٍ يوميّة `daily[day] = {o,h,l,c}`.

    • **أعلى/أدنى الشاشة:** لا يُتجاوزان داخل اللبّ `core`، ويُبلَغان داخل اللبّ ± `WINDOW_SLACK_DAYS`.
    • **آخرُ سعر:** إغلاقُ آخر يومٍ في اللبّ أو داخل مداه (لقطةٌ أثناء الجلسة).
    `factor_of(day)` يُسوّي السعرَ الخامّ كما يعرضه الشارت (تقسيم)."""
    fac = factor_of or (lambda _d: 1.0)
    c0, c1 = core
    idx = [i for i, d in enumerate(days) if c0 <= d <= c1 and d in daily]
    if not idx:
        return {"ok": False, "why": "لا أيامَ في اللبّ", "checks": {}}
    lo_i = max(0, idx[0] - WINDOW_SLACK_DAYS)
    hi_i = min(len(days) - 1, idx[-1] + WINDOW_SLACK_DAYS)
    ext = [d for d in days[lo_i:hi_i + 1] if d in daily]
    core_d = [days[i] for i in idx]
    checks = {}
    if spec_hi is not None:
        tn = tol_near(spec_hi)
        core_max = max(daily[d]["h"] * fac(d) for d in core_d)
        hit = [d for d in ext if abs(daily[d]["h"] * fac(d) - spec_hi[0]) <= tn + 1e-12]
        near_best = min(ext, key=lambda d: abs(daily[d]["h"] * fac(d) - spec_hi[0]))
        checks["high"] = {"ok": core_max <= spec_hi[0] + tn + 1e-12 and bool(hit),
                          "val": daily[near_best]["h"] * fac(near_best), "day": near_best,
                          "core_max": core_max,
                          "err": abs(daily[near_best]["h"] * fac(near_best) - spec_hi[0]) / tn}
    if spec_lo is not None:
        tn = tol_near(spec_lo)
        core_min = min(daily[d]["l"] * fac(d) for d in core_d)
        hit = [d for d in ext if abs(daily[d]["l"] * fac(d) - spec_lo[0]) <= tn + 1e-12]
        near_best = min(ext, key=lambda d: abs(daily[d]["l"] * fac(d) - spec_lo[0]))
        checks["low"] = {"ok": core_min >= spec_lo[0] - tn - 1e-12 and bool(hit),
                         "val": daily[near_best]["l"] * fac(near_best), "day": near_best,
                         "core_min": core_min,
                         "err": abs(daily[near_best]["l"] * fac(near_best) - spec_lo[0]) / tn}
    if spec_last is not None:
        tn = tol_near(spec_last)
        dl = core_d[-1]
        b = daily[dl]
        c_adj, h_adj, l_adj = b["c"] * fac(dl), b["h"] * fac(dl), b["l"] * fac(dl)
        inside = l_adj - tn <= spec_last[0] <= h_adj + tn
        checks["last"] = {"ok": abs(c_adj - spec_last[0]) <= tn + 1e-12 or inside,
                          "val": c_adj, "day": dl, "err": abs(c_adj - spec_last[0]) / tn,
                          "close_exact": abs(c_adj - spec_last[0]) <= tn + 1e-12}
    return {"ok": bool(checks) and all(c["ok"] for c in checks.values()), "checks": checks}


def window_days(card: dict) -> tuple:
    """مدى طول النافذة **بأيام التداول** `(أدنى، أعلى)` من الفريم وعدد الشموع الظاهرة (±20-25%).
    اليوميّ فما فوقه بـ`DAYS_PER_BAR` · واللحظيُّ بين الجلسة الممتدّة (16 ساعة) والنظاميّة (6.5) —
    **تقريبٌ بشموعٍ يوميّةٍ نظاميّة** (محاولةٌ لا تخمين: الحكمُ يُسقط ما لا يطابق) · وبلا عدد ⟵ مدًى افتراضيّ."""
    tf = card.get("timeframe") or "1D"
    nv = int(card.get("bars_visible") or 0)
    if tf in INTRADAY_SPAN:
        span = INTRADAY_SPAN[tf]
        lo_dpb = 1.0 / math.ceil((EXT_CLOSE_MIN - EXT_OPEN_MIN) / span)
        hi_dpb = 1.0 / max(1, math.ceil(390 / span))
    elif tf == "intraday":
        return (1, 30)
    else:
        lo_dpb = hi_dpb = DAYS_PER_BAR.get(tf, 1.0)
    base_lo, base_hi = (nv * 0.8, nv * 1.25) if nv else (20.0, 120.0)
    lo = max(1, int(base_lo * lo_dpb))
    hi = max(lo, int(math.ceil(base_hi * hi_dpb)))
    return (lo, hi)


def undated_scan(bars: list, splits, spec_hi, spec_lo, spec_last, n_range,
                 ends_back: int = 260, ends=None) -> list:
    """شارتٌ يوميٌّ **بلا تاريخ**: لكلّ يومِ نهايةٍ `e` (آخرُ `ends_back` يومًا، أو الأيامُ `ends`
    وحدَها إن أُعطيت) ولكلّ عددِ شموعٍ `N` في `n_range` ⟵ النافذةُ آخرُ `N` شمعةً تنتهي عند `e`
    **مُسوّاةً حتى `e`** ⟵ أعلى/أدنى/آخر. `bars = [(day, o, h, l, c, v)]` مرتَّبة خامًا
    ⟵ `[{e, N, ok, score, checks}]` — **أفضلُ طولٍ لكلّ يوم نهاية** (العابرُ أوّلًا ثمّ أدنى خطأ)
    مرتَّبةٌ بالأفضل. الأطرافُ لكلّ الأطوال دفعةً واحدة (تراكمٌ من النهاية للخلف) · والمعاملُ لأيام النافذة وحدَها."""
    import numpy as np                                              # noqa: PLC0415
    out = []
    days = [b[0] for b in bars]
    n_all = len(bars)
    ns = sorted({int(n) for n in n_range if int(n) >= 1})
    if not ns or not n_all or (spec_hi is None and spec_lo is None and spec_last is None):
        return out
    n_top = ns[-1]
    H = np.array([b[2] for b in bars], dtype=float)
    L = np.array([b[3] for b in bars], dtype=float)
    C = np.array([b[4] for b in bars], dtype=float)
    if ends is not None:
        want = set(ends)
        idx = [i for i, d in enumerate(days) if d in want]
    else:
        idx = list(range(n_all - 1, max(-1, n_all - 1 - ends_back), -1))
    for ei in idx:
        e = days[ei]
        a0 = max(0, ei - n_top + 1)
        fac = np.array([split_factor(splits, days[k], e) for k in range(a0, ei + 1)])
        run_hi = np.maximum.accumulate((H[a0:ei + 1] * fac)[::-1])
        run_lo = np.minimum.accumulate((L[a0:ei + 1] * fac)[::-1])
        valid = [n for n in ns if n <= len(fac)]
        if not valid:
            continue
        ni = np.array(valid) - 1
        score = np.zeros(len(valid))
        ok = np.ones(len(valid), dtype=bool)
        for spec, run in ((spec_hi, run_hi), (spec_lo, run_lo)):
            if spec is None:
                continue
            tn = tol_near(spec)
            dd = np.abs(run[ni] - spec[0])
            score += np.minimum(dd / tn if tn > 0 else np.where(dd == 0, 0.0, np.inf), 40.0)
            ok &= dd <= tn + 1e-12
        last_fc = None
        if spec_last is not None:
            c_e, h_e, l_e = C[ei] * fac[-1], H[ei] * fac[-1], L[ei] * fac[-1]
            last_fc = field_check(float(c_e), spec_last)
            tn = tol_near(spec_last)
            last_fc["near"] = last_fc["near"] or bool(l_e - tn <= spec_last[0] <= h_e + tn)
            score += min(last_fc["err"], 40.0)
            ok &= last_fc["near"]
        pick = np.where(ok, score, np.inf)
        k = int(np.argmin(pick)) if np.isfinite(pick).any() else int(np.argmin(score))
        n_best = valid[k]
        checks = {}
        if spec_hi is not None:
            checks["high"] = field_check(float(run_hi[n_best - 1]), spec_hi)
        if spec_lo is not None:
            checks["low"] = field_check(float(run_lo[n_best - 1]), spec_lo)
        if last_fc is not None:
            checks["last"] = last_fc
        out.append({"e": e, "N": n_best, "ok": bool(ok[k]), "score": float(score[k]),
                    "checks": checks})
    out.sort(key=lambda r: (0 if r["ok"] else 1, r["score"]))
    return out


def window_minutes_check(mins: dict, w: dict, tz: str, spec_hi, spec_lo, spec_last,
                         factor_of=None) -> dict:
    """نافذةٌ **لحظيّة بوقتٍ** (`from`+`from_time` ⟶ `to`+`to_time` بتوقيت `tz`): أعلى/أدنى الشاشة
    وآخرُ سعر **من دقائق المدى نفسِه** — فأطرافُ اليوم الكامل خارج الشاشة لا تُحسب عليها."""
    fac = factor_of or (lambda _d: 1.0)
    rows = []
    for d in sorted(mins):
        if not (w["from"] <= d <= w["to"]):
            continue
        off = ny_offset_min(d, tz) if tz and tz != "America/New_York" else 0
        a = (_hhmm(w.get("from_time")) or 0) + off if d == w["from"] else 0
        b = (_hhmm(w.get("to_time")) or 24 * 60) + off if d == w["to"] else 24 * 60
        f = fac(d)
        rows += [(r[2] * f, r[3] * f, r[4] * f) for r in mins[d] if a <= r[0] <= b]
    if not rows:
        return {"ok": False, "why": "لا دقائق في المدى", "checks": {}}
    checks = {}
    if spec_hi is not None:
        checks["high"] = field_check(max(r[0] for r in rows), spec_hi)
    if spec_lo is not None:
        checks["low"] = field_check(min(r[1] for r in rows), spec_lo)
    if spec_last is not None:
        checks["last"] = field_check(rows[-1][2], spec_last)
    for k, c in checks.items():
        c["day"] = w["to"] if k == "last" else "المدى"
    return {"ok": bool(checks) and all(c["near"] for c in checks.values()), "checks": checks}


def verdict(cands: list) -> tuple:
    """الحكمُ الآليّ (قاعدةُ العقد §③ بشرطيها الآليَّين):
    • **واثق** — مرشّحٌ **وحيد** يعبر كلَّ القيود ضمن تسامحها وعددُ قيوده المستقلّة 2 فأكثر.
    • **مرجّح** — عابرٌ وحيد بقيدٍ واحد · أو عابرون وخطأُ الثاني ≥ `DECISIVE_RATIO`× الأوّل.
    • **غير محسوم** — عابرون لا يفصلهم شيء. • **لا تطابق** — لا عابر.
    والشرطُ الثالث (المقارنةُ بالعين) **خارج الأداة** — فلا تُعلن الأداةُ «واثق» نهائيًّا."""
    passers = sorted([c for c in cands if c.get("pass")], key=lambda c: c.get("score", math.inf))
    if not passers:
        best = sorted(cands, key=lambda c: c.get("score", math.inf))
        return ("لا تطابق", best[0] if best else None, best[1] if len(best) > 1 else None, 0)
    t1 = passers[0]
    t2 = passers[1] if len(passers) > 1 else None
    if t2 is None:
        return ("واثق" if t1.get("n_groups", 0) >= 2 else "مرجّح", t1, None, 1)
    if t2.get("score", math.inf) >= DECISIVE_RATIO * max(t1.get("score", 0.0), 1e-9):
        return ("مرجّح", t1, t2, len(passers))
    return ("غير محسوم", t1, t2, len(passers))


def judge_line(card_id: str, label: str, t1, t2, n_pass: int, rc: int) -> str:
    s1 = (t1 or {}).get("sym") or "-"
    s2 = (t2 or {}).get("sym") or "-"
    return (f"CHART_FINDER card={card_id} verdict={label} top1={s1} top2={s2} "
            f"passers={n_pass} exit={rc}")


# ══ IO — Polygon (REST) والملفّات المجمَّعة (S3) ═════════════════════════════════════
def _key() -> str:
    return (os.environ.get("POLYGON_API_KEY") or "").strip()


def _get_json(url: str, params=None, get=None, tries: int = 4, sleep=None):
    g = get or requests.get
    sl = sleep or _time.sleep
    last = ""
    for i in range(tries):
        try:
            r = g(url, params=params or {}, headers={"Authorization": f"Bearer {_key()}"},
                  timeout=60)
            code = getattr(r, "status_code", 0)
            if code == 200:
                return r.json()
            last = f"HTTP {code}"
            if code in (401, 403, 404):
                break
        except Exception as e:                                      # noqa: BLE001
            last = type(e).__name__
        if i + 1 < tries:
            sl(2 * (2 ** i))
    log(f"   ⛔ تعذّر: {url.split('?')[0][-90:]} · {last}")
    return None


def grouped_day(day: str, get=None) -> dict:
    """السوقُ كلُّه ليومٍ واحد **خامًا** (`adjusted=false`) ⟵ `{رمز: (o,h,l,c,v)}`.
    نسخةٌ محلّيّةٌ مكافئة لـ`link100_probe.grouped_day` (بُنيت لـ`T-LINK100`) — لأن استيرادَها
    يسحب البوتَ كلَّه (`Super_stock` عبر `kasih_scan`)، وسابقتُها `HRA11`."""
    js = _get_json(f"{API}/v2/aggs/grouped/locale/us/market/stocks/{day}",
                   {"adjusted": "false"}, get=get)
    out = {}
    for b in (js or {}).get("results") or []:
        try:
            s = str(b.get("T") or "").strip().upper()
            o, h, lo, c = float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"])
            v = float(b.get("v") or 0.0)
        except (TypeError, ValueError, KeyError):
            continue
        if s and c > 0 and h > 0:
            out[s] = (o, h, lo, c, v)
    return out


def ticker_aggs(sym: str, mult: int, span: str, frm: str, to: str, adjusted: bool = False,
                get=None) -> list:
    """شموعُ رمزٍ بمدًى صريح (مع الصفحات) ⟵ `[{t,o,h,l,c,v,vw,n}]` مرتَّبة."""
    url = f"{API}/v2/aggs/ticker/{sym}/range/{mult}/{span}/{frm}/{to}"
    params = {"adjusted": "true" if adjusted else "false", "sort": "asc", "limit": "50000"}
    out, n = [], 0
    while url and n < 20:
        js = _get_json(url, params, get=get)
        if not js:
            break
        out.extend(js.get("results") or [])
        url, params, n = js.get("next_url"), {}, n + 1
    return out


_LAST_ENDS: dict = {}        # {رمز: أيامُ النهاية العابرة خامًا} من آخر مسحٍ للسوق بلا تاريخ
_SPLITS_ALL: dict = {}
_SPLITS_ALL_SINCE = None     # تاريخُ بداية الجلب الجماعيّ (تغطيتُه) — `None` = لم يُجلب


def _split_rows(results) -> list:
    out = []
    for r in results or []:
        try:
            out.append((str(r["ticker"]).upper(), str(r["execution_date"]),
                        float(r["split_from"]), float(r["split_to"])))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def load_all_splits(since: str, get=None) -> int:
    """كلُّ تقسيمات السوق منذ `since` بصفحاتٍ قليلة (`next_url`) ⟵ ذاكرةٌ لكلّ رمز. يُرجع العدد."""
    global _SPLITS_ALL_SINCE
    url = f"{API}/v3/reference/splits"
    params = {"execution_date.gte": since, "limit": "1000", "order": "asc"}
    rows, n = [], 0
    while url and n < 50:
        js = _get_json(url, params, get=get)
        if not js:
            break
        rows += _split_rows(js.get("results"))
        url, params, n = js.get("next_url"), {}, n + 1
    if not rows and n == 0:
        return 0
    _SPLITS_ALL.clear()
    for t, ex, fr, to in rows:
        _SPLITS_ALL.setdefault(t, []).append((ex, fr, to))
    for t in _SPLITS_ALL:
        _SPLITS_ALL[t].sort()
    _SPLITS_ALL_SINCE = since
    log(f"   ✂️ تقسيماتُ السوق منذ {since}: {len(rows):,} في {len(_SPLITS_ALL):,} رمزًا ({n} صفحة)")
    return len(rows)


def ticker_splits(sym: str, get=None, need_since: str = None) -> list:
    """تقسيماتُ الرمز ⟵ `[(تاريخُ التنفيذ، from، to)]` مرتَّبة — من الذاكرة الجماعيّة إن غطّت
    `need_since` (وإلّا نداءٌ للرمز وحدَه)."""
    if (_SPLITS_ALL_SINCE is not None and need_since is not None
            and _SPLITS_ALL_SINCE <= need_since):
        return list(_SPLITS_ALL.get(sym.upper(), []))
    js = _get_json(f"{API}/v3/reference/splits", {"ticker": sym, "limit": "1000"}, get=get)
    out = [(ex, fr, to) for _t, ex, fr, to in
           _split_rows([dict(r, ticker=r.get("ticker") or sym) for r in (js or {}).get("results") or []])]
    return sorted(out)


def ticker_info(sym: str, day: str = None, get=None) -> dict:
    params = {"date": day} if day else {}
    js = _get_json(f"{API}/v3/reference/tickers/{sym}", params, get=get)
    r = (js or {}).get("results") or {}
    return {"name": r.get("name"), "active": r.get("active"),
            "delisted": r.get("delisted_utc"), "exchange": r.get("primary_exchange")}


def minutes_by_day(aggs: list) -> dict:
    """شموعُ دقيقة REST (`t` بالمللي) ⟵ `{يوم نيويورك: [(mod, o, h, l, c, v, vw)]}` مرتَّبة."""
    out = {}
    for b in aggs or []:
        try:
            d = dt.datetime.fromtimestamp(int(b["t"]) / 1000.0, tz=NY)
            row = (d.hour * 60 + d.minute, float(b["o"]), float(b["h"]), float(b["l"]),
                   float(b["c"]), float(b.get("v") or 0.0), float(b.get("vw") or b["c"]))
        except (KeyError, TypeError, ValueError, OSError, OverflowError):
            continue
        out.setdefault(d.date().isoformat(), []).append(row)
    for k in out:
        out[k].sort()
    return out


def _ny_offset_seconds(day: str) -> int:
    d = dt.date.fromisoformat(day)
    return int(dt.datetime(d.year, d.month, d.day, 12, tzinfo=NY).utcoffset().total_seconds())


def read_minute_file(path: str, day: str, band) -> dict:
    """ملفُّ دقائق يومٍ **لكلّ الرموز** ⟵ `{رمز: [(mod,o,h,l,c,v)]}` للرموز التي يتقاطع مداها
    اليوميّ مع `band=(أدنى، أعلى)` — بمرورين (الأوّلُ مدى كلّ رمز · والثاني صفوفُ المتقاطع وحدَه)
    فلا تُحمَّل ملايينُ الصفوف في الذاكرة. الأعمدةُ **من الترويسة** (درسُ `V2`)."""
    off = _ny_offset_seconds(day)

    def rows():
        with gzip.open(path, "rt", newline="") as fh:
            import csv as _csv                                      # noqa: PLC0415
            rd = _csv.reader(fh)
            header = next(rd)
            ix = {n: ah_scan._pick(header, *al) for n, al in (
                ("t", ("ticker", "symbol")), ("o", ("open",)), ("h", ("high",)),
                ("l", ("low",)), ("c", ("close",)), ("v", ("volume",)),
                ("w", ("window_start", "t", "timestamp")))}
            if min(ix.values()) < 0:
                raise KeyError(f"ترويسةٌ ناقصة: {header}")
            for r in rd:
                yield r, ix

    rng = {}
    for r, ix in rows():
        try:
            s = r[ix["t"]].strip().upper()
            h, lo = float(r[ix["h"]]), float(r[ix["l"]])
        except (IndexError, ValueError):
            continue
        cur = rng.get(s)
        rng[s] = (min(cur[0], lo), max(cur[1], h)) if cur else (lo, h)
    lo_b, hi_b = band
    keep = {s for s, (lo, h) in rng.items() if lo <= hi_b and h >= lo_b}
    out = {s: [] for s in keep}
    for r, ix in rows():
        s = r[ix["t"]].strip().upper()
        if s not in keep:
            continue
        try:
            ts = int(r[ix["w"]]) // 1_000_000_000
            mod = ((ts + off) % 86400) // 60
            out[s].append((mod, float(r[ix["o"]]), float(r[ix["h"]]), float(r[ix["l"]]),
                           float(r[ix["c"]]), float(r[ix["v"]])))
        except (IndexError, ValueError):
            continue
    for s in out:
        out[s].sort()
    log(f"   📦 ملفُّ الدقائق {day}: {len(rng):,} رمزًا · يتقاطع مداه مع النطاق "
        f"[{lo_b:g}، {hi_b:g}]: {len(keep):,}")
    return out


def fetch_minute_file(day: str, tmpdir: str):
    """⬇️ ملفُّ دقائق يومٍ من S3 عبر أدوات `ah_scan` (تراجعٌ أُسّيّ وتسجيلٌ صريح) ⟵ مسارٌ أو `None`."""
    FP.resolve_swapped_creds()
    if not FP.creds_present():
        log("   ⛔ مفتاحا الملفّات المجمَّعة غائبان — لا مرساةَ لحظيّة")
        return None
    key = ah_scan.day_key(day)
    mb, ep = ah_scan.head_size_mb(key)
    if mb is None:
        return None
    dest = os.path.join(tmpdir, f"{day}.csv.gz")
    log(f"   ⬇️ {key} ({mb:.1f} ميغا)")
    return dest if ah_scan.download(key, dest, ep) else None


DAY_PATH = "us_stocks_sip/day_aggs_v1"
UNDATED_YEARS = 3          # بلا تاريخ ⇒ آخرُ 3 سنوات (نصُّ البرومبت)
PANEL_WORKERS = 8
SHORTLIST_MAX = 1000       # أقصى رموزٍ عابرةٍ خامًا تُفحص بالتقسيم الفعليّ — والمقصوصُ يُعلَن **ويحجب «واثق»**
_LAST_CUT = 0              # عددُ العابرين الذين قُصّوا بلا فحصٍ كامل في آخر بطاقة (يُصفَّر في `run_card`)


def day_aggs_key(day: str) -> str:
    y, m, _ = day.split("-")
    return f"{DAY_PATH}/{y}/{m}/{day}.csv.gz"


def read_day_aggs(path: str) -> dict:
    """ملفُّ اليوم المجمَّع ⟵ `{رمز: (o,h,l,c,v)}` — الأعمدةُ من الترويسة."""
    import csv as _csv                                              # noqa: PLC0415
    out = {}
    with gzip.open(path, "rt", newline="") as fh:
        rd = _csv.reader(fh)
        header = next(rd)
        ix = {n: ah_scan._pick(header, *al) for n, al in (
            ("t", ("ticker", "symbol")), ("o", ("open",)), ("h", ("high",)),
            ("l", ("low",)), ("c", ("close",)), ("v", ("volume",)))}
        if min(ix.values()) < 0:
            raise KeyError(f"ترويسةٌ ناقصة: {header}")
        for r in rd:
            try:
                s = r[ix["t"]].strip().upper()
                vals = tuple(float(r[ix[k]]) for k in ("o", "h", "l", "c", "v"))
            except (IndexError, ValueError):
                continue
            if s and vals[3] > 0 and vals[1] > 0:
                out[s] = vals
    return out


def _fetch_day_s3(day: str, tmpdir: str):
    dest = os.path.join(tmpdir, f"day_{day}.csv.gz")
    for ep in FP.ENDPOINTS:
        rc, _, _ = FP.aws("cp", f"s3://{FP.BUCKET}/{day_aggs_key(day)}", dest,
                          endpoint=ep, timeout=300)
        if rc == 0:
            try:
                return read_day_aggs(dest)
            except (OSError, KeyError, EOFError):
                return None
            finally:
                try:
                    os.remove(dest)
                except OSError:
                    pass
    return None


def load_panel(days: list, tmpdir: str, get=None) -> dict:
    """لوحةُ السوق اليوميّة **خامًا** لأيامٍ بعينها ⟵ `{يوم: {رمز: (o,h,l,c,v)}}`.
    المصدرُ الملفّاتُ المجمَّعة (S3) وإلّا REST (`grouped_day`) — **وكلُّ يومٍ مفقودٍ يُعلَن**."""
    from concurrent.futures import ThreadPoolExecutor                # noqa: PLC0415
    FP.resolve_swapped_creds()
    use_s3 = FP.creds_present()
    out, src = {}, {"s3": 0, "rest": 0}

    def one(d):
        if use_s3:
            g = _fetch_day_s3(d, tmpdir)
            if g:
                return d, g, "s3"
        g = grouped_day(d, get=get)
        return d, g, "rest"

    import numpy as np                                              # noqa: PLC0415
    with ThreadPoolExecutor(max_workers=PANEL_WORKERS) as ex:
        for d, g, how in ex.map(one, days):
            if g:
                syms = sorted(g)
                arr = np.array([g[s][1:4] for s in syms], dtype=np.float32)   # h · l · c
                out[d] = (syms, arr)          # مضغوطٌ فورًا: 750 يومًا × 12 ألف رمز لا تُحمَل قواميسَ
                src[how] += 1
    missing = [d for d in days if d not in out]
    log(f"   🗂️ لوحةُ السوق: {len(out)} من {len(days)} يومًا (S3 {src['s3']} · REST {src['rest']})"
        + (f" · ⛔ مفقود {len(missing)}: {missing[:8]}" if missing else ""))
    return out


def panel_arrays(panel: dict):
    """اللوحة `{يوم: (رموز، [h,l,c])}` ⟵ مصفوفاتُ numpy `(أيام × رموز)` للأعمدة H/L/C مع NaN للغائب."""
    import numpy as np                                              # noqa: PLC0415
    days = sorted(panel)
    syms = sorted({s for d in days for s in panel[d][0]})
    ix = {s: i for i, s in enumerate(syms)}
    H = np.full((len(days), len(syms)), np.nan, dtype=np.float32)
    L, C = H.copy(), H.copy()
    for di, d in enumerate(days):
        ds, arr = panel[d]
        cols = np.array([ix[s] for s in ds], dtype=np.int64)
        H[di, cols], L[di, cols], C[di, cols] = arr[:, 0], arr[:, 1], arr[:, 2]
    return days, syms, H, L, C


def _pair_errors(hs, ls, c_e, h_e, l_e, spec_hi, spec_lo, spec_last):
    """أخطاءُ زوجٍ (رمز، يوم نهاية) **خامًا**: `(آخر، أفضلُ طرف)` — والطرفُ يُقاس على كلّ أطوال النافذة
    حتى `n_max` دفعةً واحدة (المتراكمُ من النهاية للخلف)."""
    import numpy as np                                              # noqa: PLC0415
    e_last = 0.0
    if spec_last is not None:
        tn = tol_near(spec_last)
        if abs(c_e - spec_last[0]) <= tn:
            e_last = abs(c_e - spec_last[0]) / tn
        elif l_e - tn <= spec_last[0] <= h_e + tn:
            e_last = 1.0
        else:
            return None
    best = math.inf
    for spec, arr, acc in ((spec_lo, ls, np.fmin), (spec_hi, hs, np.fmax)):
        if spec is None:
            continue
        with np.errstate(invalid="ignore"):
            run = acc.accumulate(arr[::-1])
        fin = run[np.isfinite(run)]
        if fin.size:
            best = min(best, float(np.min(np.abs(fin - spec[0]))) / tol_near(spec))
    if spec_lo is None and spec_hi is None:
        best = 0.0
    return e_last, best


def undated_market_candidates(days, syms, H, L, C, spec_hi, spec_lo, spec_last, n_max: int,
                              end_ok=None):
    """مسحُ السوق كلِّه بلا تاريخ **بقيودٍ لا يكسرها تقسيمٌ داخل النافذة**:
    • آخرُ سعر عند يوم النهاية (إغلاقٌ، أو داخل المدى بخطأ 1) — آخرُ شمعةٍ بعد كلّ تقسيمٍ بالبناء.
    • وأحدُ الطرفين **خامًا** داخل آخر `n_max` شمعة (الطرفُ الواقع بعد التقسيم خامٌ = معروض).
    ⟵ `{رمز: (خطأ، يوم نهاية)}` بأفضل زوجٍ لكلّ رمز · والتحقّقُ الكامل بالتقسيم الفعليّ بعده."""
    import numpy as np                                              # noqa: PLC0415
    if spec_last is None and spec_lo is None and spec_hi is None:
        return {}
    if spec_last is not None:
        tn = tol_near(spec_last)
        with np.errstate(invalid="ignore"):
            m = (np.abs(C - spec_last[0]) <= tn) | ((L - tn <= spec_last[0]) & (spec_last[0] <= H + tn))
        pairs = np.argwhere(m)
    else:
        spec, arr = (spec_lo, L) if spec_lo is not None else (spec_hi, H)
        tn = tol_near(spec)
        with np.errstate(invalid="ignore"):
            hit = np.abs(arr - spec[0]) <= tn
        ends = set()
        for di, j in np.argwhere(hit):
            for e in range(di, min(len(days), di + n_max)):
                ends.add((e, j))
        pairs = np.array(sorted(ends)) if ends else np.zeros((0, 2), dtype=int)
    best = {}
    for e, j in pairs:
        if end_ok is not None and not end_ok(int(e)):
            continue
        a = max(0, e - n_max + 1)
        r = _pair_errors(H[a:e + 1, j], L[a:e + 1, j], C[e, j], H[e, j], L[e, j],
                         spec_hi, spec_lo, spec_last)
        if r is None or r[1] > 1.0:
            continue
        err = r[0] + r[1]
        s = syms[j]
        if s not in best or err < best[s][0]:
            best[s] = (err, days[e], (best.get(s) or (0, 0, []))[2])
        best[s][2].append(days[e])
    return best


def trading_days_back(end_iso: str, years: int) -> list:
    d1 = dt.date.fromisoformat(end_iso)
    d0 = d1 - dt.timedelta(days=int(366 * years))
    out, d = [], d0
    while d <= d1:
        iso = d.isoformat()
        if d.weekday() < 5 and MC.is_trading_day(iso):
            out.append(iso)
        d += dt.timedelta(days=1)
    return out


# ══ المراحل ═════════════════════════════════════════════════════════════════════
def stage_anchor(card: dict, tmpdir: str, file_path: str = None) -> list:
    """المرساةُ اللحظيّة على **كلّ الرموز** من ملفّ دقائق يومها ⟵ مرشّحون مرتَّبون."""
    a = card.get("anchor") or {}
    specs = anchor_specs(a)
    prices = [specs[f][0] for f in ("o", "h", "l", "c") if f in specs]
    if not prices or not _iso(a.get("date")):
        return []
    day = a["date"]
    tzs = [z for z in dict.fromkeys(["America/New_York", card.get("tz") or "", DEVICE_TZ])
           if z and z != "unknown"]
    defs = anchor_defs(day, a.get("time"), tzs)
    band = (min(prices) * 0.999, max(prices) * 1.001)
    path = file_path or fetch_minute_file(day, tmpdir)
    if not path:
        return []
    by_sym = read_minute_file(path, day, band)
    cands = []
    for s, rows in by_sym.items():
        m = best_anchor_match(rows, specs, defs)
        if m is None:
            continue
        cands.append({"sym": s, "anchor": m, "score": m["sc"]["score"], "near": m["sc"]["near"]})
    cands.sort(key=lambda c: (0 if c["near"] else 1, c["score"]))
    n_near = sum(1 for c in cands if c["near"])
    log(f"① المرساة {day} {a.get('time') or 'يوميّة'} · {len(defs)} تعريفًا للشمعة · "
        f"عابرٌ ضمن التسامح: {n_near} من {len(cands):,}")
    for c in cands[:8]:
        log("   " + fmt_anchor(c))
    return cands


def fmt_anchor(c: dict) -> str:
    m = c["anchor"]
    d, b, f = m["def"], m["bar"], m["sc"]["fields"]
    parts = []
    for k in ("o", "h", "l", "c"):
        if k in f:
            parts.append(f"{k.upper()} {b[k]:.4g}{'✅' if f[k]['near'] else '❌'}")
    if "v" in f:
        parts.append(f"V {b['v']:,.0f}{'✅' if f['v']['near'] else '≈'}")
    return (f"{'✅' if c['near'] else '·'} {c['sym']:6} [{d['a'] // 60:02d}:{d['a'] % 60:02d}-"
            f"{d['b'] // 60:02d}:{d['b'] % 60:02d}) ET · مدى {d['span']}د · تسمية {d['label']} · "
            f"{d['tz']} · " + " · ".join(parts) + f" · خطأ {c['score']:.3f}")


def stage_window(card: dict, sym: str, get=None, tz: str = "America/New_York") -> dict:
    """قيودُ النافذة لمرشّحٍ واحد من **دقائقه الخام** (الممتدّة والنظاميّة) ثم التسوية.
    والنافذةُ بوقتٍ (`from_time`/`to_time`) ⟵ `window_minutes_check` على المدى الزمنيّ نفسِه."""
    w = card.get("window") or {}
    ex = card.get("extremes") or {}
    spec_hi, spec_lo = num_spec(ex.get("high")), num_spec(ex.get("low"))
    spec_last = num_spec(card.get("last"))
    if not (w.get("from") and w.get("to")) or not (spec_hi or spec_lo or spec_last):
        return {"ok": None, "why": "لا نافذةَ مؤرَّخة"}
    d0 = (dt.date.fromisoformat(w["from"]) - dt.timedelta(days=10)).isoformat()
    d1 = (dt.date.fromisoformat(w["to"]) + dt.timedelta(days=10)).isoformat()
    mins = minutes_by_day(ticker_aggs(sym, 1, "minute", d0, d1, get=get))
    days = sorted(mins)
    splits = ticker_splits(sym, get=get)
    as_of = w["to"]
    if w.get("from_time") or w.get("to_time"):
        out = window_minutes_check(mins, w, tz, spec_hi, spec_lo, spec_last,
                                   factor_of=lambda d: split_factor(splits, d, as_of))
        out["session"], out["splits"], out["mins"] = "مدًى زمنيّ", splits, mins
        return out
    res = {}
    for sess in ("ext", "reg"):
        daily = {}
        for d in days:
            b = day_extremes(mins, d, sess)
            if b:
                daily[d] = b
        res[sess] = window_check(daily, days, (w["from"], w["to"]), spec_hi, spec_lo, spec_last,
                                 factor_of=lambda d: split_factor(splits, d, as_of))
    best = "ext" if res["ext"]["ok"] or not res["reg"]["ok"] else "reg"
    out = dict(res[best])
    out["session"], out["splits"], out["mins"] = best, splits, mins
    return out


def panel_slice(panel_arr, d0: str, d1: str):
    """شريحةُ أيامٍ من لوحةٍ محقونة `(days, syms, H, L, C)` — للتقييم داخل عمليّةٍ واحدة."""
    days, syms, H, L, C = panel_arr
    idx = [i for i, d in enumerate(days) if d0 <= d <= d1]
    if not idx:
        return [], syms, H[:0], L[:0], C[:0]
    a, b = idx[0], idx[-1] + 1
    return days[a:b], syms, H[a:b], L[a:b], C[a:b]


def stage_market_dated(card: dict, tmpdir: str, get=None, panel_arr=None) -> tuple:
    """شارتٌ يوميٌّ **بتاريخ** بلا مرساة: لوحةُ أيام النافذة ± 10 أيام ⟵ يومُ النهاية داخل
    `to ± WINDOW_SLACK_DAYS` ⟵ القيدان الخامّان ⟵ قائمةٌ قصيرة (والمقصوصُ يُعلَن ويحجب «واثق»)
    ⟵ `(الرموز، شريحةُ اللوحة)` فيُفحص كلُّ مرشّحٍ منها بلا نداءٍ للرمز."""
    w = card["window"]
    ex = card.get("extremes") or {}
    spec_hi, spec_lo = num_spec(ex.get("high")), num_spec(ex.get("low"))
    spec_last = num_spec(card.get("last"))
    d0 = (dt.date.fromisoformat(w["from"]) - dt.timedelta(days=10)).isoformat()
    d1 = (dt.date.fromisoformat(w["to"]) + dt.timedelta(days=10)).isoformat()
    if panel_arr is not None:
        pdays, syms, H, L, C = panel_slice(panel_arr, d0, d1)
    else:
        span_years = max(1, (dt.date.fromisoformat(d1) - dt.date.fromisoformat(d0)).days // 365 + 1)
        days = [d for d in trading_days_back(d1, span_years) if d >= d0]
        panel = load_panel(days, tmpdir, get=get)
        if not panel:
            return [], None
        pdays, syms, H, L, C = panel_arrays(panel)
    core = [i for i, d in enumerate(pdays) if w["from"] <= d <= w["to"]]
    if not core:
        return [], None
    n_max = (core[-1] - core[0] + 1) + 2 * WINDOW_SLACK_DAYS
    lo_e, hi_e = core[-1] - WINDOW_SLACK_DAYS, core[-1] + WINDOW_SLACK_DAYS
    best = undated_market_candidates(pdays, syms, H, L, C, spec_hi, spec_lo, spec_last, n_max,
                                     end_ok=lambda e: lo_e <= e <= hi_e)
    ranked = sorted(best.items(), key=lambda kv: (kv[1][0], kv[0]))
    global _LAST_CUT
    _LAST_CUT = max(0, len(ranked) - SHORTLIST_MAX)
    log(f"① نافذةٌ مؤرَّخة {w['from']} ⟶ {w['to']} ⟵ رموزٌ عبرت القيدَين الخامَّين: {len(ranked):,}"
        + (f" · ✂️ فُحص أوّلُ {SHORTLIST_MAX} وقُصّ {_LAST_CUT:,} (⇒ لا «واثق»)" if _LAST_CUT else ""))
    need = (dt.date.fromisoformat(w["from"]) - dt.timedelta(days=20)).isoformat()
    if ranked and (_SPLITS_ALL_SINCE is None or _SPLITS_ALL_SINCE > need):
        load_all_splits(need, get=get)
    return [s for s, _ in ranked[:SHORTLIST_MAX]], (pdays, syms, H, L, C)


def stage_dated_exact(card: dict, syms: list, get=None, panel_arr=None) -> list:
    """التحقّقُ الكامل للنافذة المؤرَّخة: شموعٌ يوميّةٌ خام لكلّ مرشّح (من اللوحة المحقونة إن وُجدت،
    وإلّا REST) مُسوّاةً بتقسيمه حتى `to`."""
    w = card["window"]
    ex = card.get("extremes") or {}
    spec_hi, spec_lo = num_spec(ex.get("high")), num_spec(ex.get("low"))
    spec_last = num_spec(card.get("last"))
    d0 = (dt.date.fromisoformat(w["from"]) - dt.timedelta(days=20)).isoformat()
    d1 = (dt.date.fromisoformat(w["to"]) + dt.timedelta(days=20)).isoformat()
    out = []
    for s in syms:
        daily = {}
        if panel_arr is not None:
            for d, o, h, lo, c, _v in _panel_bars(panel_arr, s):
                if d0 <= d <= d1:
                    daily[d] = {"o": o, "h": h, "l": lo, "c": c}
        else:
            for b in ticker_aggs(s, 1, "day", d0, d1, get=get):
                try:
                    d = dt.datetime.fromtimestamp(int(b["t"]) / 1000.0, tz=NY).date().isoformat()
                    daily[d] = {"o": float(b["o"]), "h": float(b["h"]), "l": float(b["l"]),
                                "c": float(b["c"])}
                except (KeyError, TypeError, ValueError):
                    continue
        splits = ticker_splits(s, get=get, need_since=d0)
        wr = window_check(daily, sorted(daily), (w["from"], w["to"]), spec_hi, spec_lo, spec_last,
                          factor_of=lambda d, sp=splits: split_factor(sp, d, w["to"]))
        wr["splits"], wr["session"] = splits, "يوميّ"
        log(fmt_window(s, wr))
        n_ok = sum(1 for c in (wr.get("checks") or {}).values() if c.get("ok"))
        out.append({"sym": s, "pass": bool(wr.get("ok")), "n_groups": n_ok,
                    "score": sum(min(c["err"], 40.0) for c in (wr.get("checks") or {}).values()),
                    "window": wr})
    return out


def stage_market_undated(card: dict, tmpdir: str, get=None, panel_arr=None) -> list:
    """بلا تاريخ ⟵ لوحةُ آخر `UNDATED_YEARS` سنوات ⟵ قيودٌ لا يكسرها التقسيم ⟵ قائمةٌ قصيرة
    (أقصاها `SHORTLIST_MAX` رمزًا — **والمقصوصُ يُعلَن بعدده**)."""
    ex = card.get("extremes") or {}
    spec_hi, spec_lo = num_spec(ex.get("high")), num_spec(ex.get("low"))
    spec_last = num_spec(card.get("last"))
    n_max = window_days(card)[1] + 1
    end = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    days = panel_arr[0] if panel_arr is not None else trading_days_back(end, UNDATED_YEARS)
    log(f"① بلا تاريخ ⟵ لوحةُ السوق {days[0] if days else '-'} ⟶ {days[-1] if days else '-'} "
        f"({len(days)} يومًا{' · محقونة' if panel_arr is not None else ''}) · نافذةٌ حتى {n_max} شمعة")
    if panel_arr is not None:
        pdays, syms, H, L, C = panel_arr
    else:
        panel = load_panel(days, tmpdir, get=get)
        if not panel:
            return [], None
        pdays, syms, H, L, C = panel_arrays(panel)
    best = undated_market_candidates(pdays, syms, H, L, C, spec_hi, spec_lo, spec_last, n_max)
    ranked = sorted(best.items(), key=lambda kv: (kv[1][0], kv[0]))
    if ranked and (_SPLITS_ALL_SINCE is None or _SPLITS_ALL_SINCE > pdays[0]):
        load_all_splits(pdays[0], get=get)
    global _LAST_CUT
    _LAST_CUT = max(0, len(ranked) - SHORTLIST_MAX)
    log(f"   🔎 رموزٌ عبرت القيدَين الخامَّين: {len(ranked):,}"
        + (f" · ✂️ فُحص أوّلُ {SHORTLIST_MAX} بالتقسيم الفعليّ وقُصّ {_LAST_CUT:,} (⇒ لا «واثق»)"
           if _LAST_CUT else ""))
    for s, (err, e, _ends) in ranked[:8]:
        log(f"   · {s:6} خطأ {err:.2f} · يوم النهاية {e} · أيامُ نهايةٍ عابرة خامًا {len(_ends)}")
    global _LAST_ENDS
    _LAST_ENDS = {s: sorted(set(v[2])) for s, v in ranked[:SHORTLIST_MAX]}
    return [s for s, _ in ranked[:SHORTLIST_MAX]], (pdays, syms, H, L, C)


def _panel_bars(panel_arr, sym: str) -> list:
    """شموعُ رمزٍ من لوحةٍ محقونة ⟵ `[(day, o, h, l, c, v)]` (o=c و v=0 — اللوحةُ تحمل H/L/C)."""
    import numpy as np                                              # noqa: PLC0415
    days, syms, H, L, C = panel_arr
    try:
        j = syms.index(sym)
    except ValueError:
        return []
    out = []
    for i, d in enumerate(days):
        h, lo, c = H[i, j], L[i, j], C[i, j]
        if np.isfinite(c):
            out.append((d, float(c), float(h), float(lo), float(c), 0.0))
    return out


def stage_undated(card: dict, syms: list, get=None, panel_arr=None, use_ends: bool = False) -> list:
    """شارتٌ يوميٌّ بلا تاريخ على رموزٍ بعينها (قائمةٌ قصيرة أو تحقّقٌ متقاطع) ⟵ مرشّحون بحكمهم."""
    ex = card.get("extremes") or {}
    spec_hi, spec_lo = num_spec(ex.get("high")), num_spec(ex.get("low"))
    spec_last = num_spec(card.get("last"))
    lo_d, hi_d = window_days(card)
    n_range = range(lo_d, hi_d + 1)
    today = dt.date.today()
    out = []
    since = (today - dt.timedelta(days=int(366 * UNDATED_YEARS))).isoformat()
    for s in syms:
        if panel_arr is not None:
            bars = _panel_bars(panel_arr, s)
        else:
            bars = []
            for b in ticker_aggs(s, 1, "day", since, today.isoformat(), get=get):
                try:
                    d = dt.datetime.fromtimestamp(int(b["t"]) / 1000.0, tz=NY).date().isoformat()
                    bars.append((d, float(b["o"]), float(b["h"]), float(b["l"]), float(b["c"]),
                                 float(b.get("v") or 0.0)))
                except (KeyError, TypeError, ValueError):
                    continue
        splits = ticker_splits(s, get=get, need_since=bars[0][0] if bars else since)
        ends = ((_LAST_ENDS.get(s) or None) if use_ends else None)
        res = undated_scan(bars, splits, spec_hi, spec_lo, spec_last, n_range,
                           ends_back=len(bars), ends=ends)
        best = res[0] if res else None
        n_ok = len({r["e"] for r in res if r["ok"]})
        if best:
            parts = []
            for k, lab in (("high", "أعلى"), ("low", "أدنى"), ("last", "آخر")):
                c = best["checks"].get(k)
                if c:
                    parts.append(f"{lab} {c['val']:.4g}{'✅' if c['near'] else '❌'}")
            log(f"   {'✅' if best['ok'] else '❌'} {s:6} أفضلُ نافذة: تنتهي {best['e']} · "
                f"{best['N']} شمعة · " + " · ".join(parts) + f" · أيامُ نهايةٍ عابرة {n_ok}"
                + (f" · تقسيمات {splits[-3:]}" if splits else " · بلا تقسيم"))
        out.append({"sym": s, "pass": bool(best and best["ok"]),
                    "n_groups": sum(1 for c in (best or {}).get("checks", {}).values() if c["near"]),
                    "score": best["score"] if best else math.inf, "undated": best,
                    "window": {"splits": splits}})
    return out


def fmt_window(sym: str, wr: dict) -> str:
    if wr.get("ok") is None:
        return f"   {sym}: {wr.get('why')}"
    parts = []
    for k, lab in (("high", "أعلى"), ("low", "أدنى"), ("last", "آخر")):
        c = (wr.get("checks") or {}).get(k)
        if c:
            parts.append(f"{lab} {c['val']:.4g} يوم {c.get('day')} "
                         f"{'✅' if c.get('ok', c.get('near')) else '❌'}")
    sp = [s for s in wr.get("splits") or []]
    return (f"   {'✅' if wr.get('ok') else '❌'} {sym:6} النافذة ({wr.get('session')}): "
            + " · ".join(parts) + (f" · تقسيمات {sp[-3:]}" if sp else " · بلا تقسيم"))


def print_series(sym: str, card: dict, wr: dict, m: dict = None, get=None) -> None:
    """🖼️ ما يكفي لرسم المقارنة داخل الجلسة: يوميٌّ مُسوًّى حتى آخر النافذة ‏+ لحظيٌّ بتعريف المرساة."""
    w = card.get("window") or {}
    to = w.get("to") or (card.get("anchor") or {}).get("date")
    if not to:
        return
    d0 = (dt.date.fromisoformat(to) - dt.timedelta(days=100)).isoformat()
    d1 = (dt.date.fromisoformat(to) + dt.timedelta(days=20)).isoformat()
    splits = (wr or {}).get("splits") if wr else ticker_splits(sym, get=get)
    for b in ticker_aggs(sym, 1, "day", d0, d1, get=get):
        try:
            day = dt.datetime.fromtimestamp(int(b["t"]) / 1000.0, tz=NY).date().isoformat()
        except (KeyError, TypeError, ValueError):
            continue
        f = split_factor(splits, day, to)
        log(f"SERIES_D {sym} {day} {b['o'] * f:.4f} {b['h'] * f:.4f} {b['l'] * f:.4f} "
            f"{b['c'] * f:.4f} {b.get('v', 0):.0f} x{f:g}")
    mins = (wr or {}).get("mins") or {}
    if m and mins:
        for day in sorted(mins):
            for a, b in intraday_grid(m["def"]):
                bar = agg_bar(mins[day], a, b)
                if bar:
                    log(f"SERIES_I {sym} {day} {a // 60:02d}:{a % 60:02d} {bar['o']:.4f} "
                        f"{bar['h']:.4f} {bar['l']:.4f} {bar['c']:.4f} {bar['v']:.0f}")


def probe_session_days(sym: str, mins: dict, get=None, max_days: int = 12) -> str:
    """⓪ **الحاسم:** أيامٌ يخرج فيها طرفُ الجلسة الممتدّة عن النظاميّة ⟵ هل يتبعه يوميُّ Polygon؟
    ⟵ `ممتدّ` / `نظاميّ` / `مختلط` / `لا يوم يفصل` مع العدّ."""
    days = sorted(mins)
    if not days:
        return "لا دقائق"
    daily = {}
    for b in ticker_aggs(sym, 1, "day", days[0], days[-1], get=get):
        try:
            d = dt.datetime.fromtimestamp(int(b["t"]) / 1000.0, tz=NY).date().isoformat()
            daily[d] = (float(b["h"]), float(b["l"]))
        except (KeyError, TypeError, ValueError):
            continue
    ext_n = reg_n = 0
    shown = 0
    for d in days:
        reg, ext = day_extremes(mins, d, "reg"), day_extremes(mins, d, "ext")
        if not (reg and ext and d in daily):
            continue
        if abs(ext["h"] - reg["h"]) < 1e-9 and abs(ext["l"] - reg["l"]) < 1e-9:
            continue
        h, lo_ = daily[d]
        is_ext = abs(h - ext["h"]) < 1e-9 and abs(lo_ - ext["l"]) < 1e-9
        is_reg = abs(h - reg["h"]) < 1e-9 and abs(lo_ - reg["l"]) < 1e-9
        ext_n += is_ext
        reg_n += is_reg
        if shown < max_days:
            log(f"   ⓪ {sym} {d}: يوميّ H {h:g} L {lo_:g} · نظاميّ H {reg['h']:g} L {reg['l']:g} · "
                f"ممتدّ H {ext['h']:g} L {ext['l']:g} ⇒ {'ممتدّ' if is_ext else 'نظاميّ' if is_reg else 'لا هذا ولا ذاك'}")
            shown += 1
    tag = ("لا يوم يفصل" if ext_n + reg_n == 0 else "ممتدّ" if reg_n == 0 else
           "نظاميّ" if ext_n == 0 else "مختلط")
    log(f"   ⓪ الحكم ({sym}): يوميُّ Polygon = **{tag}** (أيامٌ فاصلة: ممتدّ {ext_n} · نظاميّ {reg_n})")
    return tag


def probe_daily_session(day: str, syms: list, get=None) -> None:
    """⓪ مِجَسُّ البرومبت: **هل الشمعةُ اليوميّة في Polygon تشمل الجلسة الممتدّة؟**
    يقارن grouped daily بالدقائق (نظاميّة · ممتدّة) لرموزٍ بعينها ويطبع الحكمَ لكلٍّ."""
    g = grouped_day(day, get=get)
    for s in syms:
        gb = g.get(s)
        d0 = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
        d1 = (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()
        mins = minutes_by_day(ticker_aggs(s, 1, "minute", d0, d1, get=get))
        reg, ext = day_extremes(mins, day, "reg"), day_extremes(mins, day, "ext")
        if not (gb and reg and ext):
            log(f"   ⓪ {s} {day}: بياناتٌ ناقصة (يوميّ={bool(gb)} نظاميّ={bool(reg)} ممتدّ={bool(ext)})")
            continue
        o, h, lo, c, v = gb
        m_reg = abs(h - reg["h"]) < 1e-9 and abs(lo - reg["l"]) < 1e-9
        m_ext = abs(h - ext["h"]) < 1e-9 and abs(lo - ext["l"]) < 1e-9
        tag = ("ممتدّ" if m_ext and not m_reg else "نظاميّ" if m_reg and not m_ext
               else "متطابقان (لا يفصل)" if m_reg and m_ext else "لا هذا ولا ذاك")
        log(f"   ⓪ {s} {day}: يوميّ H {h:g} L {lo:g} V {v:,.0f} · نظاميّ H {reg['h']:g} "
            f"L {reg['l']:g} V {reg['v']:,.0f} · ممتدّ H {ext['h']:g} L {ext['l']:g} "
            f"V {ext['v']:,.0f} ⇒ {tag}")


def run_card(card: dict, tmpdir: str, get=None, file_path: str = None,
             cross_syms: list = None, results: dict = None, panel_arr=None,
             series: bool = True) -> dict:
    """بطاقةٌ واحدة ⟵ مسارُها ⟵ الحكم. يُرجع `{rc, label, top, n_pass, mode}` ويطبع سطرَ الحكم.

    المسارات: مرساةٌ مؤرَّخة (ملفُّ دقائق اليوم) · نافذةٌ مؤرَّخة بلا مرساة (لوحةُ أيامها) ·
    بلا تاريخ (لوحةُ 3 سنوات) · `cross_with` (تحقّقٌ متقاطع لا بحث). `panel_arr` لوحةٌ محقونة
    للتقييم داخل عمليّةٍ واحدة (المصنوعة) · و`series=False` يُسكت سلاسلَ الرسم."""
    errs = validate_card(card)
    cid = str(card.get("id") or "?") if isinstance(card, dict) else "?"
    if errs:
        for e in errs:
            log(f"⛔ البطاقة {cid}: {e}")
        log(judge_line(cid, "بطاقةٌ غيرُ صالحة", None, None, 0, 2))
        return {"rc": 2, "label": "بطاقةٌ غيرُ صالحة", "top": [], "n_pass": 0, "mode": "invalid"}
    global _LAST_CUT
    _LAST_CUT = 0
    log(f"\n🔎 البطاقة {cid} · فريم {card.get('timeframe')} · ممتدّة {card.get('extended')} · "
        f"منطقة {card.get('tz')}")
    has_anchor = bool((card.get("anchor") or {}).get("date"))
    has_window = bool((card.get("window") or {}).get("to"))
    anchor_ref = None
    if has_anchor:
        mode = "anchor"
        anchor_c = stage_anchor(card, tmpdir, file_path=file_path)
        near = [c for c in anchor_c if c["near"]]
        _LAST_CUT = max(0, len(near) - ANCHOR_MAX)
        if _LAST_CUT:
            log(f"   ✂️ عابرو المرساة {len(near)} ⟵ فُحصت نوافذُ أوّل {ANCHOR_MAX} وقُصّ {_LAST_CUT} (⇒ لا «واثق»)")
        shortlist = near[:ANCHOR_MAX] or anchor_c[:3]
        final = []
        for c in shortlist:
            wr = stage_window(card, c["sym"], get=get, tz=c["anchor"]["def"]["tz"])
            log(fmt_window(c["sym"], wr))
            groups = 1 + (1 if wr.get("ok") is not None else 0)
            ok = c["near"] and (wr.get("ok") is not False)
            wscore = sum(min(ch["err"], 40.0) for ch in (wr.get("checks") or {}).values())
            final.append({"sym": c["sym"], "pass": ok, "n_groups": groups,
                          "score": c["score"] + wscore, "anchor": c["anchor"], "window": wr})
        anchor_ref = card["anchor"]["date"]
    elif has_window:
        mode = "dated"
        syms, dated_arr = stage_market_dated(card, tmpdir, get=get, panel_arr=panel_arr)
        final = stage_dated_exact(card, syms, get=get, panel_arr=dated_arr)
        anchor_ref = card["window"]["to"]
    else:
        cross = [x for x in (cross_syms or []) if x]
        mode = "cross" if cross else "market"
        if cross:
            log(f"🔁 تحقّقٌ متقاطع (لا بحثٌ مستقلّ) على مرشّحي بطاقةٍ أخرى: {cross}")
            syms = cross
        else:
            syms, panel_arr = stage_market_undated(card, tmpdir, get=get, panel_arr=panel_arr)
        final = stage_undated(card, syms, get=get, panel_arr=panel_arr, use_ends=not cross)
    label, t1, t2, n_pass = verdict(final)
    if label == "واثق" and _LAST_CUT:
        label = "مرجّح"
        log(f"   ⚠️ «واثق» حُجب ⟵ «مرجّح»: {_LAST_CUT} عابرًا خامًّا قُصّوا بلا فحصٍ كامل (التفرّدُ غيرُ مُتحقَّق)")
    ranked = sorted(final, key=lambda x: (0 if x["pass"] else 1, x["score"]))
    log(f"⚖️ الحكمُ الآليّ ({mode}): **{label}** · عابرون {n_pass} · "
        f"الأوّل {(t1 or {}).get('sym', '-')} · الثاني {(t2 or {}).get('sym', '-')}"
        + (" — ويبقى الشرطُ الثالث: المقارنةُ بالعين" if label == "واثق" else ""))
    if series:
        for c in ranked[:TOP_SERIES]:
            ref = anchor_ref or (c.get("undated") or {}).get("e")
            info = ticker_info(c["sym"], ref, get=get)
            info_now = ticker_info(c["sym"], None, get=get)
            log(f"🏷️ {c['sym']}: {info.get('name')} · {info.get('exchange')} · "
                f"نشِط اليوم={info_now.get('active')}")
            sc = card if (has_anchor or has_window) else {"window": {"to": ref}}
            print_series(c["sym"], sc, c.get("window"), c.get("anchor"), get=get)
        if has_anchor and final:
            probe_daily_session(card["anchor"]["date"], [final[0]["sym"], "AAPL"], get=get)
            for c in final[:2]:
                mins = (c.get("window") or {}).get("mins") or {}
                if mins:
                    probe_session_days(c["sym"], mins, get=get)
    top = [c["sym"] for c in ranked[:TOP_SERIES]]
    if results is not None:
        results[cid] = top
    log(judge_line(cid, label, t1, t2, n_pass, 0) + f" mode={mode}")
    return {"rc": 0, "label": label, "top": top, "n_pass": n_pass, "mode": mode}


def load_cards() -> list:
    raw = (os.environ.get("CHART_CARD") or "").strip()
    files = [p.strip() for p in (os.environ.get("CHART_CARD_FILES") or "").split(",") if p.strip()]
    cards = []
    if raw:
        js = json.loads(raw)
        cards.extend(js if isinstance(js, list) else [js])
    for p in files:
        with open(p, encoding="utf-8") as fh:
            cards.append(json.load(fh))
    return cards


def main() -> int:
    if not _key():
        log("⛔ POLYGON_API_KEY غائب")
        return 3
    try:
        cards = load_cards()
    except (ValueError, OSError) as e:
        log(f"⛔ تعذّرت قراءةُ البطاقة: {type(e).__name__}: {e}")
        return 2
    if not cards:
        log("⛔ لا بطاقة (CHART_CARD أو CHART_CARD_FILES)")
        return 2
    rc, results = 0, {}
    with tempfile.TemporaryDirectory() as tmp:
        for card in cards:
            link = (card.get("cross_with") if isinstance(card, dict) else None) or ""
            rc = max(rc, run_card(card, tmp, cross_syms=results.get(link),
                                  results=results)["rc"])
    return rc


if __name__ == "__main__":
    sys.exit(main())
