#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🕓 `T-H4` — هل يتغيّر الحكمُ على فريم الأربع ساعات؟ (العقد: `h4_prereg.md`
مدفوعٌ **قبل** هذا الملفّ وقبل `h4_build.py`).

**ذراعان لا ثالثة (§③):** `D0` القاعدةُ على اليوميّ (إعادةُ إنتاجٍ للمنشور) ·
`H1` القاعدةُ **نفسُها حرفيًّا** على شموع 4س المبنيّة من الدقائق.

**والمحرّكُ واحدٌ بالاسم — صفرُ مِشيةٍ منسوخة:** `fuse_arms.walk` (وهي
`press_wake_arms.walk_symbol_wake` المجمَّدة + `enrich_episode`) تُستدعى على
**الإطار** فقط، فالفرقُ بين الذراعين **إطارٌ لا قاعدة**.

⚠️ **وحدُّ صدقٍ يُقرأ مع الأرقام (يلحق `§⑨`):** نافذةُ `press_read(w=40)`
**أربعون شمعةً لا أربعون يومًا** ⇒ على 4س تصير عشرةَ أيام، و`READY_HOLD=3`
تصير ثلاثَ شمعاتِ 4س. **وهذا عينُ ما ينصّ عليه `§③`** («القاعدةُ نفسُها
حرفيًّا») — لا تُعايَر نافذةٌ لتناسب الفريم، فمعايرتُها بعد رؤية الأرقام
تحريكُ هدف.

🔒 بحث/قياس حصرًا: قراءةٌ فقط · الإنتاجُ لا يستوردها · لا `LOGIC_VERSION`."""
from __future__ import annotations

import gzip
import json
import math
import os
import pickle
import sys

Z95 = 1.959964
OUT_ROWS = "h4_rows.jsonl"
GATE_MIN_R = 0.15          # §⑤-1 — عتبةٌ **مُعادة** لا مخترَعة
FLOOR_YEAR = 30            # §⑤-4
FLOOR_TOTAL = 150          # §⑤-4

# 🚪 `HV4` — مِرساةُ إعادة الإنتاج: (محسومة، فائزة) لكلّ سنة،
#    منشورةٌ في `candle_result.md §①` (‏`CV0`-ب) ومجموعُها 5371/1025
#    المنشورُ في `press_prereg §⑬`. ⛔ لا تُحرَّك ولا تُقرَّب.
HV4_PUBLISHED = {"2023": (1660, 351), "2024": (1857, 333),
                 "2025": (1854, 341)}


def _log(m=""):
    print(m, flush=True)


def frame_4h(rows):
    """يبني إطارَ 4س لرمزٍ من صفوف `h4_build`: ‏(يوم، دلو، o,h,l,c,v).
    الفهرسُ **طابعٌ زمنيّ** عند بداية الدلو بتوقيت نيويورك (تسلسلٌ صاعد)."""
    import pandas as pd                                          # noqa: PLC0415
    if not rows:
        return None
    rows = sorted(rows, key=lambda r: (r[0], r[1]))
    idx = [pd.Timestamp(f"{d} {4 + 4 * b:02d}:00:00") for d, b, *_ in rows]
    return pd.DataFrame(
        {"Open": [r[2] for r in rows], "High": [r[3] for r in rows],
         "Low": [r[4] for r in rows], "Close": [r[5] for r in rows],
         "Volume": [r[6] for r in rows]}, index=pd.DatetimeIndex(idx))


def ev_r(sub, r_win):
    """توقّعُ `R` لمجموعةِ حلقاتٍ + العدد + فاصلُ 95%. `no_fill` ⇒ ‏0.0R."""
    vals = []
    for e in sub:
        oc = e.get("oc")
        if oc == "win":
            vals.append(float(r_win))
        elif oc == "loss":
            vals.append(-1.0)
        elif oc == "no_fill":
            vals.append(0.0)
    n = len(vals)
    if not n:
        return (None, 0, None, None)
    m = sum(vals) / n
    if n < 2:
        return (m, n, None, None)
    var = sum((v - m) ** 2 for v in vals) / (n - 1)
    se = (var ** 0.5) / (n ** 0.5)
    return (m, n, m - Z95 * se, m + Z95 * se)


def fmt(st):
    m, n, lo, hi = st
    if m is None:
        return f"— (‏{n})"
    ci = (f" [‏{lo:+.3f} · {hi:+.3f}]" if lo is not None else "")
    return f"{m:+.3f}R{ci} · {n} حلقة"


def main() -> int:
    year = (os.environ.get("BACKTEST_YEAR") or "").strip()
    frozen = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    h4p = os.environ.get("H4_PATH") or f"h4_{year}.pkl.gz"
    _log(f"\n{'=' * 78}\n🕓 T-H4 — سنة {year} · لقطة={frozen} · 4س={h4p}\n{'=' * 78}")
    if not year:
        _log("⛔ `BACKTEST_YEAR` غائب ⇒ خروج 2.")
        return 2
    for p in (frozen, h4p):
        if not os.path.exists(p):
            _log(f"⛔ ملفٌّ مفقود ({p!r}) ⇒ خروج 2.")
            return 2

    os.environ.setdefault("SCREENER_MODE", "BACKTEST")
    import Super_stock as S                                      # noqa: PLC0415
    import fuse_arms as FU                                       # noqa: PLC0415
    import press_backtest as PB                                  # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415

    hist, _sp, asof = S.load_frozen_dataset(frozen)
    if not hist:
        _log("⛔ لقطةٌ فارغة ⇒ خروج 2.")
        return 2
    with gzip.open(h4p, "rb") as fh:
        blob = pickle.load(fh)
    bars = blob.get("bars") or {}
    _log(f"📦 لقطة as-of {asof} · رموز {len(hist)} · 4س لـ{len(bars)} رمزًا")

    d0, h1, n_syms, issues = [], [], 0, {}
    seen_d0, seen_h1 = set(), set()
    for sym, df in hist.items():
        if df is None or len(df) < RB.MIN_BARS + 5:
            continue
        n_syms += 1
        rows, iss = FU.walk(sym, df, year)
        for k, v in iss.items():
            issues[f"d0_{k}"] = issues.get(f"d0_{k}", 0) + v
        d0.extend(rows)
        seen_d0.update(r["sym"] for r in rows)
        f4 = frame_4h(bars.get(sym))
        if f4 is not None and len(f4) >= RB.MIN_BARS + 5:
            r4, iss4 = FU.walk(sym, f4, year)
            for k, v in iss4.items():
                issues[f"h1_{k}"] = issues.get(f"h1_{k}", 0) + v
            h1.extend(r4)
            seen_h1.update(r["sym"] for r in r4)
        if n_syms % 400 == 0:
            _log(f"  … مشى {n_syms} رمزًا · D0={len(d0)} · H1={len(h1)}")

    # ── 🚪 `HV4` — `D0` يُعيد رقمًا **منشورًا** بت-بت ────────────────────
    # 🔴 **ودرسُ `LV0` مطبَّقٌ لا مقتبَس:** المِرساةُ من `candle_result.md`
    #    (‏`CV0`-ب) وهي **نفسُ المسار ونفسُ اللقطات ونفسُ المرشِّح**
    #    (`FU.walk` · و`len(df) < RB.MIN_BARS + 5` حرفيًّا) ⇒ **قابلةٌ
    #    للاستيفاء بالبناء**، بخلاف `LV0` التي طالبت برقمٍ قِيس قبل ثلاثةِ
    #    قراراتٍ للمالك فاستحالت.
    _res = sum(1 for e in d0 if e.get("oc") in ("win", "loss"))
    _win = sum(1 for e in d0 if e.get("oc") == "win")
    _exp = HV4_PUBLISHED.get(str(year))
    if _exp is None:
        _log(f"   🚪 `HV4`: لا رقمَ منشورٌ لسنة {year} ⇒ خروج 3 "
             "(‏لا تُقاس سنةٌ بلا مِرساة).")
        return 3
    if (_res, _win) != _exp:
        _log(f"   🚪 `HV4` **ساقطة**: `D0` أعطى محسومة={_res} فائزة={_win} "
             f"والمنشورُ {_exp[0]}/{_exp[1]} ⇒ خروج 3 — "
             "**عطبُ أداةٍ لا نتيجة**، ولا يُقرأ رقمٌ من تشغيلةٍ سقطت هنا.")
        return 3
    _log(f"   🚪 `HV4` ✅ `D0` يُعيد `candle_result` بت-بت: {_res}/{_win}")

    # ── 🚪 `HV5` — الذراعان تفترقان (وإلّا `no-op`) ─────────────────────────
    inter = seen_d0 & seen_h1
    uni = seen_d0 | seen_h1
    ov = (len(inter) / len(uni) * 100.0) if uni else 0.0
    if not h1 or not d0 or len(h1) == len(d0) and ov >= 99.9:
        _log(f"⛔ `HV5`: الذراعان لا تفترقان (D0={len(d0)} · H1={len(h1)} · "
             f"تقاطع {ov:.1f}%) ⇒ خروج 4 (‏`no-op`).")
        return 4

    r_win = PB.r_win_value()
    s0, s1 = ev_r(d0, r_win), ev_r(h1, r_win)
    gap = ((s1[0] - s0[0]) if (s0[0] is not None and s1[0] is not None) else None)
    _log(f"\n🕓 <b>T-H4 سنة {year}</b> — رموز {n_syms} · `R_win`={r_win:.2f}")
    _log(f"   `D0` اليوميّ: {fmt(s0)}")
    _log(f"   `H1` أربعُ ساعات: {fmt(s1)}")
    _log(f"   ▸ الفارقُ `H1 − D0`: "
         f"{(f'{gap:+.3f}R' if gap is not None else '—')} · "
         f"الحدُّ المسجَّل +{GATE_MIN_R:.2f}R "
         f"{'✅' if (gap is not None and gap >= GATE_MIN_R) else '❌'}")
    _log(f"   📊 `H-P2` تقاطعُ العضويّة: {ov:.1f}% "
         f"(‏`_frame_probe` قاس 20% على مجتمعٍ آخر)")
    _log(f"   📊 `H-P3` كثافةُ الحلقات: H1/D0 = "
         f"{(len(h1) / len(d0)) if d0 else 0:.2f}×")
    _log(f"   📊 `H-P5` بلوغُ الهدف: اليوميّ "
         f"{100.0 * sum(1 for e in d0 if e['oc'] == 'win') / max(1, len(d0)):.1f}% · "
         f"‏4س {100.0 * sum(1 for e in h1 if e['oc'] == 'win') / max(1, len(h1)):.1f}%")
    _log(f"   🚪 الأرضية (‏{FLOOR_YEAR}/سنة): D0 "
         f"{'✅' if s0[1] >= FLOOR_YEAR else '❌'} · H1 "
         f"{'✅' if s1[1] >= FLOOR_YEAR else '❌'} "
         f"(‏والمجمَّع {FLOOR_TOTAL} يُقرأ عبر الثلاث)")
    if issues:
        _log(f"   ⚠️ ملاحظاتُ الإثراء: {issues}")
    _log("   ⏳ <b>سنةٌ واحدة</b>: المعيارُ أربعةٌ معًا في ثلاث سنوات.")
    _log("   🔒 سقفُ النجاح: <b>اقتراحٌ + سطرُ عرض</b> — لا مسَّ بـM1-M14 ولا "
         "بالوقف ولا بالأهداف.")

    try:
        with open(OUT_ROWS, "w", encoding="utf-8") as f:
            for tag, rows in (("D0", d0), ("H1", h1)):
                for r in rows:
                    f.write(json.dumps({**r, "arm": tag, "year": year},
                                       ensure_ascii=False, default=str) + "\n")
        _log(f"💾 {OUT_ROWS}: {len(d0) + len(h1)} صفًّا")
    except Exception as _e:                                      # noqa: BLE001
        _log(f"⚠️ تعذّر الحفظ: {type(_e).__name__}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
