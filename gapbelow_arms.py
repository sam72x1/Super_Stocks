#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🕳️ `T-GAPBELOW` — «سجّل الفجوة تحت السعر»: هل تُغطّى الفجوةُ الصاعدةُ تحت السعر («لازم»)،
وهل أمرُ حدٍّ عند قاعها دخولٌ أفضل («كويس»)؟ (العقد `gapbelow_prereg.md` مدموجٌ **قبل هذا الملفّ**
وقبل أيّ رقم).

**المصدر:** `TG_57869` (CRE «لازم ينزل يغطي الفراغ») · `TG_57871` (DSY «اذا نزل … وغطاها كويس») ·
`TG_20260905_08` (STKH «غطا فجوته الان المفروض يطلع») — فيصل بتأكيد المالك. **والمختبَرُ نقلُنا**
(الأفقُ والهدفُ والوقفُ من الإنتاج) لا نصُّه: سقوطُه لا يُكذّب فيصل ونجاحُه لا يصادق عليه.

🔴 **الالتباسُ الحاكم (درسُ `T-WAIT-23W`):** التوقّعُ سالبٌ و`no_fill` صفر ⇒ ذراعٌ تتاجر أقلَّ تتحسّن
آليًّا ⇒ **الضبطُ الحاكم لـ`E2` مطابَقُ التعبئة `M`** · و`C` (عمقُ صفِّ فجوةٍ آخر) ضبطُ المسافة لـ`D2`.
**`M` و`C` نماذجُ عدمٍ إحصائيّة لا استراتيجيّات ⇒ لا تُشحَن أبدًا.**

**إعادةُ استعمالٍ بالاسم — لا نسخ:** `wait_rsi27_arms.arms_for` تُنتج `R0` **بت-بت** كما نُشر (`V-G0`)
ومعها `agg`/`decomp`/`r0_of`/`stop_for` · و`wait_rsi23w_arms.REF23`/`rotate`/`cluster_ci`/`per_fill_mean`
· و`tranche_arms.FLOOR_DECIDED` · و`_resolve_arm`/`analyze_ticker`/`backtest_symbol` الإنتاجيّة عبرها.
**والحدّان `GAP_MIN_PCT`/`GAP_ABOVE_LOOKBACK_D` يُقرآن من `CONFIG` بالاسم وقتَ النداء.**

🔒 `Super_stock.py` و`wait_rsi27_arms.py` و`wait_rsi23w_arms.py` لا تُمَسّ بحرف · قراءةٌ فقط ·
الإنتاجُ لا يستوردها · لا `LOGIC_VERSION` · بلا تلغرام ولا مفتاحِ مزوّد."""
from __future__ import annotations

import ast
import gc
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np

from tranche_arms import FLOOR_DECIDED                                   # بالاسم
from wait_rsi23w_arms import REF23, cluster_ci, per_fill_mean, rotate     # بالاسم
from wait_rsi27_arms import agg, arms_for, decomp, stop_for               # بالاسم (`r0_of` عبر `agg`/`decomp`/`cluster_ci`)

OUT_ROWS = "gapbelow_rows.jsonl"

# §③ — أربعُ أذرعٍ ولا خامسة (إضافةُ ذراعٍ بعد الأرقام ممنوعة)
ARMS = ("R0", "G", "M", "C")
GOV = "G"                               # §③ — الحاكمة: أمرُ حدٍّ عند قاع الفجوة
CONTRACT_YEARS = ("2023", "2024", "2025")   # §② — السنواتُ الثلاث يُحكَم بها
ROT_DEN = 3                             # §③ — إزاحةُ `C` ⌊n/3⌋ داخل السنة
MATCH_ITERS = 60                        # §③ — تنصيفاتُ حلّ عمق `M`
BOOT_N = 2000                           # §④
BOOT_SEED = 57869                       # §④ — حتميّ
CI_PCT = 97.5                           # §④ — ثنائيُّ الجانب
E1_MIN_R = 0.05                         # §④ `E1` (engineering — من `T-WAIT-LOWER`)
E2_MIN_R = 0.025                        # §④ `E2` (engineering — من `T-WAIT-23W`)
E3_MIN_FILL_RATIO = 0.30                # §④ `E3` (engineering — من `T-WAIT-LOWER`)
D1_MIN_WILSON = 0.80                    # §④ `D1` — «لازم» حرفيًّا: حدُّ ويلسون الأدنى 95%
D2_MIN_PP = 5.0                         # §④ `D2` — المغناطيس بالنقاط المئويّة
V_G3_FILL_TOL = 0.02                    # §④ `V-G3` — مطابقةُ تعبئة `M` لـ`G`
V_G4_MIN_CHANGED = 0.80                 # §④ `V-G4` — الإزاحةُ تُغيّر العمق
WILSON_Z = 1.959963984540054            # 95% ثنائيّ


def _log(m):
    print(m, flush=True)


# ─────────────────────────── §③ تعريفُ الفجوة (نقيّة) ───────────────────────────
def _ts(x):
    """**يومٌ** بلا منطقةٍ زمنيّة ولا ساعة: التقسيماتُ في اللقطة قد تحمل منطقةً أو ساعةً (منتصفُ
    ليل نيويورك = 04:00/05:00 UTC) ⇒ المقارنةُ بالتاريخ وحدَه وإلّا انزاح التقسيمُ إلى الشمعة التالية."""
    import pandas as pd                                          # noqa: PLC0415
    t = pd.Timestamp(x)
    t = t.tz_localize(None) if getattr(t, "tz", None) is not None else t
    return t.normalize()


def split_dates(splits):
    """تواريخُ التقسيمات المُدرَجة للرمز (أيُّ نسبةٍ موجبة — أماميٌّ وعكسيّ) بلا منطقة.
    تقبل `Series` أو قائمةَ أزواج · وفاشلةٌ-آمنة ⇒ قائمةٌ فارغة."""
    out = []
    if splits is None:
        return out
    try:
        it = splits.items() if hasattr(splits, "items") else splits
        for d, r in it:
            try:
                if r is not None and float(r) > 0 and float(r) != 1.0:
                    out.append(_ts(d))
            except (TypeError, ValueError):
                continue
    except Exception:                                            # noqa: BLE001
        return []
    return sorted(out)


def gaps_below(high, low, close, dates=None, sdates=None, lookback=None, min_pct=None):
    """§③ — كلُّ فجوةٍ صاعدةٍ **لم تُغطَّ** تحت سعر التحليل على شموعٍ تنتهي بشمعة الإشارة `s`.

    1. `k` في `[max(1, s − L + 1), s]` · 2. فراغٌ كامل `low[k] > high[k−1]` بحجم ‏≥ `GAP_MIN_PCT` ·
    3. لم تُغطَّ: `min(low[k+1 … s]) > high[k−1]` (المدى الفارغ ⟵ لم تُغطَّ) · 4. `b < ref` ·
    5. حارسُ التقسيم: تقسيمٌ في `(date[k−1], date[k]]` ⟵ تُستبعَد وتُعَدّ.
    **والحدّان من `CONFIG` بالاسم وقتَ النداء** إن لم يُمرَّرا. يرجّع (قائمة، عددُ المستبعَد بالتقسيم)."""
    if lookback is None or min_pct is None:
        import Super_stock as S                                  # noqa: PLC0415
        if lookback is None:
            lookback = int(S.CONFIG["GAP_ABOVE_LOOKBACK_D"])
        if min_pct is None:
            min_pct = float(S.CONFIG["GAP_MIN_PCT"])
    h = np.asarray(high, dtype=float)
    lo = np.asarray(low, dtype=float)
    n = len(h)
    if n < 2 or len(lo) != n:
        return [], 0
    try:
        ref = float(np.asarray(close, dtype=float)[-1])
    except (TypeError, ValueError, IndexError):
        return [], 0
    if not (math.isfinite(ref) and ref > 0):
        return [], 0
    s = n - 1
    start = max(1, s - int(lookback) + 1)
    lo_c = np.where(np.isfinite(lo), lo, np.inf)                 # قاعٌ مجهول لا يُغطّي شيئًا
    suf = np.full(n, np.inf)                                     # suf[k] = min(low[k+1 … s])
    for k in range(s - 1, start - 1, -1):
        suf[k] = min(suf[k + 1], lo_c[k + 1])
    sd = list(sdates or [])
    out, n_split = [], 0
    for k in range(start, n):
        b, top = h[k - 1], lo[k]
        if not (math.isfinite(b) and math.isfinite(top) and b > 0 and top > 0):
            continue
        if not top > b:
            continue
        size = (top / b - 1.0) * 100.0
        if size < float(min_pct):
            continue
        if not suf[k] > b:                                       # غُطّيت قبل الإشارة
            continue
        if not b < ref:                                          # §③-4 يُفحَص صراحةً
            continue
        if sd and dates is not None:
            d0, d1 = _ts(dates[k - 1]), _ts(dates[k])
            if any(d0 < x <= d1 for x in sd):
                n_split += 1
                continue
        out.append({"k": int(k), "ago": int(s - k), "b": float(b), "top": float(top),
                    "size": float(size), "cov_min": (float(suf[k]) if math.isfinite(suf[k])
                                                     else None)})
    return out, n_split


def governing_gap(gaps):
    """§③-6 — **أعلى قاعٍ** (الأقربُ تحت السعر) · والتعادلُ ⟵ الأحدث (أكبرُ `k`). نقيّة."""
    if not gaps:
        return None
    return max(gaps, key=lambda g: (g["b"], g["k"]))


def gap_ok(g, ref, min_pct):
    """§④ `V-G1` — الصفُّ يحقّق التعريفَ مُعادًا من حقوله المخزَّنة. نقيّة."""
    try:
        b, top, size = float(g["b"]), float(g["top"]), float(g["size"])
        cov = g.get("cov_min")
        return (top > b > 0 and b < float(ref)
                and abs((top / b - 1.0) * 100.0 - size) < 1e-6
                and size >= float(min_pct)
                and (cov is None or float(cov) > b))
    except (TypeError, ValueError, KeyError):
        return False


# ─────────────────────────── §③ الأذرع ───────────────────────────
def entry_depth(ref, d):
    """§③ `M`/`C` — دخولٌ بعمقٍ ثابتٍ تحت سعر التحليل **بلا قصٍّ بـ`entry0`** (توأمُ `G`)."""
    return float(ref) * (1.0 - float(d))


def ref_of(r):
    """سعرُ التحليل بدقّته الكاملة (`ref_raw`) · و`ref` المدوَّر من `arms_for` احتياطًا."""
    v = r.get("ref_raw")
    return float(v if v is not None else r["ref"])


def fill_count(rows, d):
    """عددُ صفوف الفجوة التي تتعبّأ عند عمقٍ ثابت `d` (بأدنى قاعٍ أماميٍّ محسوبٍ مرّةً)."""
    return sum(1 for r in rows if r.get("minlow") is not None
               and float(r["minlow"]) <= entry_depth(ref_of(r), d))


def solve_match_depth(rows, target, iters=MATCH_ITERS):
    """§③ `M` — بحثٌ ثنائيٌّ على `[0, 0.99]` يُصغّر `|تعبئة − target|` (التعبئةُ متناقصةٌ رتيبًا
    في العمق). حتميٌّ ونقيّ."""
    lo_d, hi_d = 0.0, 0.99
    best, best_err = 0.0, abs(fill_count(rows, 0.0) - target)
    for _ in range(int(iters)):
        mid = (lo_d + hi_d) / 2.0
        c = fill_count(rows, mid)
        err = abs(c - target)
        if err < best_err:
            best, best_err = mid, err
        if c > target:
            lo_d = mid
        else:
            hi_d = mid
    return best, best_err


def resolve_into(S, r, name, entry, bars, spread):
    """يحسم ذراعًا على الصفّ نفسِه بـ`_resolve_arm` الإنتاجيّ: الوقفُ **بنسبة الإنتاج**
    (`stop_for`) والهدفُ `t1` · والتعبئةُ أوّلُ شمعةٍ قاعُها ‏≤ الدخول. يكتب حقولَ `agg`."""
    hi, lo, cl, op = bars
    e0, s0, t1 = r["e_R0"], r["stop0"], r["t1"]
    stop = stop_for(entry, e0, s0)
    r[f"e_{name}"] = round(float(entry), 4)
    r[f"bite_{name}"] = bool(float(entry) < float(e0) - 1e-12)
    if stop is None or float(entry) - float(stop) <= 0:
        r[f"s_{name}"], r[f"o_{name}"], r[f"ret_{name}"], r[f"k_{name}"] = None, "skip", None, None
        return
    filled = next((k for k in range(len(lo)) if lo[k] <= entry), None)
    o, rt, _, _ = S._resolve_arm(hi, lo, cl, op, float(entry), float(stop), float(t1),
                                 filled, spread=spread)
    r[f"s_{name}"] = round(float(stop), 4)
    r[f"o_{name}"] = o
    r[f"ret_{name}"] = (round(rt, 1) if rt is not None else None)
    r[f"k_{name}"] = filled


def is_filled(r, name):
    return r.get(f"o_{name}") not in (None, "no_fill", "skip")


def build_arms(S, rows, bars, spread):
    """§③ — الأذرع `G`/`M`/`C` على صفوف الفجوة (مرتّبةً حتميًّا بـ`(symbol, date)`) ·
    ويرجّع (الصفوف، إحصاءاتٌ لبوّابات الصلاحية). `R0` يبقى كما حسمه `arms_for` حرفيًّا."""
    rows.sort(key=lambda r: (r["symbol"], r["date"]))
    for r in rows:
        resolve_into(S, r, "G", r["gap_b"], bars[(r["symbol"], r["date"])], spread)
    target = sum(1 for r in rows if is_filled(r, "G"))
    md, merr = solve_match_depth(rows, target)
    depth = [max(0.0, 1.0 - float(r["gap_b"]) / ref_of(r)) for r in rows]
    rot = rotate(depth, ROT_DEN)
    changed = sum(1 for a, b in zip(depth, rot) if abs(a - b) > 1e-12)
    for i, r in enumerate(rows):
        bb = bars[(r["symbol"], r["date"])]
        resolve_into(S, r, "M", entry_depth(ref_of(r), md), bb, spread)
        resolve_into(S, r, "C", entry_depth(ref_of(r), rot[i]), bb, spread)
        r["depth"] = round(depth[i], 6)
        r["depth_C"] = round(rot[i], 6)
    stats = {"match_depth": md, "match_err": merr, "target": target,
             "rot_changed": (changed / len(rows)) if rows else 0.0}
    return rows, stats


# ─────────────────────────── §④ الإحصاء ───────────────────────────
def wilson_lower(k, n, z=WILSON_Z):
    """حدُّ ويلسون الأدنى لنسبةٍ `k/n` (95% افتراضًا) · `n = 0` ⟵ 0. نقيّة."""
    if not n:
        return 0.0
    p = float(k) / float(n)
    den = 1.0 + z * z / n
    ctr = p + z * z / (2.0 * n)
    rad = z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n))
    return max(0.0, (ctr - rad) / den)


def cluster_ci_vals(rows, fn, pct=CI_PCT, n_boot=BOOT_N, seed=BOOT_SEED):
    """§④ — **المقدِّرُ نفسُه** في `wait_rsi23w_arms.cluster_ci` (بوتستراب عنقوديٌّ بالرمز ·
    نسبةُ المجاميع · البذرةُ والمعايَنةُ بالترتيب نفسِه) على قيمةٍ لكلّ صفٍّ من `fn` (و`None` ⟵
    يُتخطّى الصفّ). **مطابقتُه لـ`cluster_ci` على فروق `R₀` مقفولةٌ في السويّة** — يُستعمَل لـ`D2`."""
    g = defaultdict(list)
    for r in rows:
        v = fn(r)
        if v is None:
            continue
        g[r["symbol"]].append(float(v))
    syms = sorted(g)
    if not syms:
        return None
    sums = np.array([sum(g[s]) for s in syms], dtype=float)
    cnts = np.array([len(g[s]) for s in syms], dtype=float)
    m = len(syms)
    rng = np.random.default_rng(int(seed))
    means = np.empty(int(n_boot), dtype=float)
    for j in range(int(n_boot)):
        idx = rng.integers(0, m, m)
        den = cnts[idx].sum()
        means[j] = (sums[idx].sum() / den) if den > 0 else 0.0
    lo = (100.0 - float(pct)) / 2.0
    return {"lo": float(np.percentile(means, lo)),
            "mean": float(sums.sum() / max(cnts.sum(), 1.0)),
            "hi": float(np.percentile(means, 100.0 - lo)),
            "n_sym": m, "n_rows": int(cnts.sum())}


def fill_ind(r, name):
    """مؤشّرُ التعبئة (1/0) · وذراعٌ غيرُ محسومة ⟵ None."""
    if r.get(f"o_{name}") is None:
        return None
    return 1.0 if is_filled(r, name) else 0.0


def d_metrics(rows):
    """§④ D — «لازم» (`D1` حرفيًّا · ويلسون) والمغناطيس (`D2` · `G − C` بالنقاط مع فاصلٍ عنقوديّ)."""
    n = sum(1 for r in rows if r.get("o_G") is not None)
    k = sum(1 for r in rows if is_filled(r, "G"))
    kc = sum(1 for r in rows if is_filled(r, "C"))
    wl = wilson_lower(k, n)
    diff = cluster_ci_vals(rows, lambda r: (None if fill_ind(r, "G") is None
                                            or fill_ind(r, "C") is None
                                            else fill_ind(r, "G") - fill_ind(r, "C")))
    pp = ((k - kc) / n * 100.0) if n else 0.0
    return {"n": n, "fill_G": k, "fill_C": kc,
            "cover_pct": (k / n * 100.0) if n else 0.0, "wilson_lo": wl,
            "D1": wl >= D1_MIN_WILSON,
            "magnet_pp": pp, "magnet_ci": diff,
            "D2": bool(diff is not None and pp >= D2_MIN_PP and diff["lo"] > 0)}


def verdict(per_year, pooled_ci_r0, pooled_ci_m, pooled_pf, floors_ok, vg3_ok):
    """§④ — الفرع: (1) «تُوصى» `E1∧E2∧E3∧E4` · (2) «لا تُوصى» أيُّ ساقطٍ مع الأرضية ·
    (3) «لا قياس» أرضيةٌ ساقطةٌ في سنةٍ أو `V-G3` ساقط. نقيّة (المدخلاتُ أرقامٌ محسوبة).

    `per_year`: {سنة: {"d_r0": G−R0 بالسنة, "fill_ratio": تعبئة(G)÷تعبئة(R0)}} ·
    `pooled_ci_r0`/`pooled_ci_m`: فاصلا `G−R0`/`G−M` العنقوديّان المجمَّعان ·
    `pooled_pf`: (لكلّ مُعبَّأة G، لكلّ مُعبَّأة R0) مجمَّعًا."""
    e1 = (all(v["d_r0"] > 0 for v in per_year.values())
          and pooled_ci_r0 is not None and pooled_ci_r0["mean"] >= E1_MIN_R
          and pooled_ci_r0["lo"] > 0)
    e2 = bool(pooled_ci_m is not None and pooled_ci_m["mean"] >= E2_MIN_R
              and pooled_ci_m["lo"] > 0)
    e3 = all(v["fill_ratio"] >= E3_MIN_FILL_RATIO for v in per_year.values())
    e4 = bool(pooled_pf is not None and pooled_pf[0] >= pooled_pf[1])
    gates = {"E1": e1, "E2": e2, "E3": e3, "E4": e4}
    if not floors_ok or not vg3_ok or set(per_year) != set(CONTRACT_YEARS):
        return 3, "لا قياس", gates
    if e1 and e2 and e3 and e4:
        return 1, "تُوصى", gates
    return 2, "لا تُوصى", gates


# ─────────────────────────── قراءةٌ فقط ───────────────────────────
def _selfcheck_readonly() -> bool:
    """قراءةٌ فقط (نمطُ `TV6`): صفرُ إرسالٍ وصفرُ كتابةِ حالة (بالـAST على مصدرها هي) ·
    والملفُّ الوحيد المسموحُ فتحُه للكتابة `OUT_ROWS`."""
    try:
        src = open(__file__, encoding="utf-8").read()
    except Exception:                                            # noqa: BLE001
        return False
    banned = {"send_telegram", "git_save", "save_watchlist", "save_op_entry_state",
              "record_new_alerts", "save_near_watch", "save_hunter_watch"}
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call):
            fn = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            if fn in banned:
                return False
            if fn == "open":
                mode = ""
                if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                    mode = str(n.args[1].value)
                for kw in n.keywords or []:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = str(kw.value.value)
                if any(c in mode for c in ("w", "a", "x", "+")):
                    ok = (n.args and isinstance(n.args[0], ast.Name)
                          and n.args[0].id == "OUT_ROWS")
                    if not ok:
                        return False
    return True


# ─────────────────────────── التقرير ───────────────────────────
def _arm_line(rows, nm):
    x = agg(rows, nm)
    return (f"{nm}: R₀ {x['r_fixed']:+.4f} · تعبئة {x['fill_pct']:.1f}% ({x['n_fill']}) · "
            f"ربح {x['win_pct']:.2f}% · لكلّ مُعبَّأة {per_fill_mean(rows, nm):+.4f}R")


def year_report(S, year, all_rows, gap_rows, issues, stats, counts):
    """سنةٌ واحدة ⟵ (رمزُ خروج، ملخّص). 0 سليم · 3 عطبُ أداة (بوّابةُ صلاحية) · 4 بلا صفوف."""
    _log(f"\n🕳️ T-GAPBELOW · سنة {year} · صفوفُ الإشارة {len(all_rows)} · صفوفُ الفجوة {len(gap_rows)}")
    if issues:
        _log("   ℹ️ أسبابُ عدم القياس: " + " · ".join(f"{k} {v}" for k, v in sorted(issues.items())))
    if not all_rows:
        _log("   ⛔ صفرُ صفقات ⇒ `no-op`")
        return 4, None
    ref = REF23.get(str(year))
    a0 = agg(all_rows, "R0")
    same0 = sum(1 for r in all_rows if r.get("o_R0") == r.get("prod_o"))
    _log(f"   ℹ️ حسمُ `R0` = حسمُ الإنتاج: {same0}/{len(all_rows)}")
    if ref:                                                       # `V-G0`
        got = (round(a0["r_fixed"], 4), len(all_rows), a0["n_fill"])
        exp = (ref["r0"], ref["n"], ref["f0"])
        ok0 = (abs(got[0] - exp[0]) < 5e-5 and got[1] == exp[1] and got[2] == exp[2])
        _log(f"   🔒 `V-G0` {got} مقابل `REF23` {exp} ⇒ {'✅ بت-بت' if ok0 else '⛔ تفرّق'}")
        if not ok0:
            return 3, None
    else:
        _log("   ⛔ `V-G0` سنةٌ بلا مرجعٍ منشور ⇒ خارج العقد")
        return 3, None
    if not gap_rows:
        _log("   ⚪ صفرُ صفوف فجوة")
        return 0, {"year": str(year), "n_all": len(all_rows), "n_gap": 0}

    min_pct = float(S.CONFIG["GAP_MIN_PCT"])
    bad1 = sum(1 for r in gap_rows if not gap_ok(
        {"b": r["gap_b"], "top": r["gap_top"], "size": r["gap_size"], "cov_min": r["gap_cov_min"]},
        ref_of(r), min_pct))
    _log(f"   🔒 `V-G1` صفوفٌ تخالف التعريف: {bad1}")
    if bad1:
        return 3, None
    bad2 = sum(1 for r in gap_rows
               if is_filled(r, "G") != (r["minlow"] is not None and float(r["minlow"]) <= float(r["gap_b"])))
    _log(f"   🔒 `V-G2` تعبئةُ G ⟺ أدنى قاعٍ أماميّ ‏≤ القاع: مخالِف {bad2}")
    if bad2:
        return 3, None
    a = {nm: agg(gap_rows, nm) for nm in ARMS}
    ns = {nm: a[nm]["n"] for nm in ARMS}
    _log(f"   🔒 `V-G5` مقامٌ واحد: {ns}")
    if len(set(ns.values())) != 1:
        return 3, None
    _log(f"   🔒 `V-G4` الإزاحةُ غيّرت العمقَ في {stats['rot_changed'] * 100:.1f}% (الحدّ {V_G4_MIN_CHANGED * 100:.0f}%)")
    if stats["rot_changed"] < V_G4_MIN_CHANGED:
        return 3, None
    dc = decomp(gap_rows, GOV)
    _log(f"   🔒 `V-G6` هويّةُ التفكيك {'✅' if dc['identity_ok'] else '⛔'}")
    if not dc["identity_ok"]:
        return 3, None
    tol = V_G3_FILL_TOL * a["G"]["n_fill"]
    vg3 = abs(a["M"]["n_fill"] - a["G"]["n_fill"]) <= tol
    _log(f"   🎯 `M`: عمقٌ محلول {stats['match_depth'] * 100:.2f}% ⇒ تعبئة {a['M']['n_fill']} مقابل "
         f"`G` {a['G']['n_fill']} (التسامح {tol:.2f}) · `V-G3` {'✅' if vg3 else '🔴 غيرُ قابلٍ للمقارنة'}")

    hi_rows = [r for r in gap_rows if not r.get("bite_G")]
    lo_rows = [r for r in gap_rows if r.get("bite_G")]
    _log(f"   📊 الانتشار: {len(gap_rows)} من {len(all_rows)} = {len(gap_rows) / len(all_rows) * 100:.1f}% · "
         f"مستبعَدٌ بالتقسيم {counts['split_rows']} صفًّا ({counts['split_gaps']} فجوة) · "
         f"«أعلى» {len(hi_rows)} ({len(hi_rows) / len(gap_rows) * 100:.1f}%) · «أعمق» {len(lo_rows)} · "
         f"الدخولُ فوق الهدف {sum(1 for r in gap_rows if float(r['gap_b']) >= float(r['t1']))}")
    _log("   ┌─ الأذرع على صفوف الفجوة (‏`R₀` الثابتة · `no_fill`/`skip` = 0R) ─")
    for nm in ARMS:
        mk = " 🥇" if nm == GOV else (" ⚖️" if nm in ("M", "C") else "")
        _log(f"   │ {_arm_line(gap_rows, nm)}{mk}")
    _log("   ├─ وصفٌ لا يحكم: «أعلى» (قاعُ الفجوة ‏≥ `entry0`) · «أعمق» ─")
    for lab, sub in (("أعلى", hi_rows), ("أعمق", lo_rows)):
        if sub:
            _log(f"   │ {lab} ({len(sub)}): " + " ‖ ".join(_arm_line(sub, nm) for nm in ("R0", "G")))
    _log("   └─────────────────────────────────────────────────────────")
    b = dc["buckets"]
    _log("   🔬 تفكيك `G−R0`: " + " · ".join(f"{k} n={b[k]['n']} {b[k]['mean_per_row']:+.4f}R"
                                         for k in ("B0", "B1", "B2", "B3"))
         + f" · الانتقالات {dc['transitions']}")
    dm = d_metrics(gap_rows)
    _log(f"   🧲 «لازم»: التغطية {dm['cover_pct']:.1f}% ({dm['fill_G']}/{dm['n']}) · ويلسون الأدنى "
         f"{dm['wilson_lo'] * 100:.1f}% · المغناطيس G−C {dm['magnet_pp']:+.1f} نقطة")
    c0 = cluster_ci(gap_rows, "R0", GOV, seed=BOOT_SEED)
    cm = cluster_ci(gap_rows, "M", GOV, seed=BOOT_SEED)
    _log(f"   📏 G−R0 [{c0['lo']:+.4f}, {c0['hi']:+.4f}] وسط {c0['mean']:+.4f} · "
         f"G−M [{cm['lo']:+.4f}, {cm['hi']:+.4f}] وسط {cm['mean']:+.4f} (رموز {c0['n_sym']})")
    out = {"year": str(year), "n_all": len(all_rows), "n_gap": len(gap_rows),
           "prevalence": len(gap_rows) / len(all_rows), "split_rows": counts["split_rows"],
           "split_gaps": counts["split_gaps"], "hi_share": len(hi_rows) / len(gap_rows),
           "arms": a, "per_fill": {nm: per_fill_mean(gap_rows, nm) for nm in ARMS},
           "match_depth": stats["match_depth"], "v_g3": vg3, "d": dm,
           "d_r0": a["G"]["r_fixed"] - a["R0"]["r_fixed"],
           "fill_ratio": a["G"]["n_fill"] / max(a["R0"]["n_fill"], 1),
           "floor_ok": (a["R0"]["n_fill"] >= FLOOR_DECIDED and a["G"]["n_fill"] >= FLOOR_DECIDED),
           "ci_r0": c0, "ci_m": cm, "decomp": {k: {"n": b[k]["n"], "mean": b[k]["mean_per_row"]}
                                               for k in b}}
    return 0, out


def predictions(summaries, rows, dm, gates, c0):
    """§⑤ — التنبّؤاتُ السبع **بنصّ العقد** (تُنشَر كما تقع). نقيّة.

    🔴 `GB-P5` نصُّها «`E1` تسقط (`G − R0` المجمَّع دون +0.05R)» ⇒ السقوطُ **و**آليّتُه المكتوبة معًا.
    كانت تفحص `not E1` وحدَه فطبعت «✅ صدق» على مجمَّعٍ +0.1071 **فوق** الحدّ (الحاكمة `36812671247`) —
    أُصلحت بعد التشغيلة **تشديدًا يطابق العقد** (`gapbelow_result.md` §⑥ · قفل `GBA14`)."""
    return {
        "GB-P1": all(0.05 <= s["prevalence"] <= 0.30 for s in summaries),
        "GB-P2": bool(rows) and (sum(1 for r in rows if not r.get("bite_G")) / len(rows)) > 0.5,
        "GB-P3": bool(dm and not dm["D1"] and 45.0 <= dm["cover_pct"] <= 75.0),
        "GB-P4": bool(dm and abs(dm["magnet_pp"]) < D2_MIN_PP),
        "GB-P5": bool(not gates["E1"] and c0 is not None and c0["mean"] < E1_MIN_R),
        "GB-P6": not gates["E2"],
        "GB-P7": all(s["arms"][nm]["r_fixed"] < 0 for s in summaries for nm in ARMS),
    }


def pooled(judged, summaries):
    """§④ — الحكمُ المجمَّع: عنقدةٌ بالرمز عبر السنوات معًا (محافِظ) · والفرعُ من `verdict`."""
    rows = [r for _, rs in judged for r in rs]
    if not rows:
        _log("\n══════ صفرُ صفوف فجوة في السنوات كلّها ⇒ **الفرع 3: «لا قياس»** ══════")
        return 3
    _log(f"\n══════ الحكمُ المجمَّع على {len(judged)} سنة: "
         f"{' · '.join(y for y, _ in judged)} ({len(rows)} صفّ فجوة) ══════")
    per_year = {s["year"]: {"d_r0": s["d_r0"], "fill_ratio": s["fill_ratio"]} for s in summaries}
    floors_ok = all(s.get("floor_ok") for s in summaries) and len(summaries) == len(CONTRACT_YEARS)
    vg3_ok = all(s.get("v_g3") for s in summaries) and len(summaries) == len(CONTRACT_YEARS)
    c0 = cluster_ci(rows, "R0", GOV, seed=BOOT_SEED) if rows else None
    cm = cluster_ci(rows, "M", GOV, seed=BOOT_SEED) if rows else None
    pf = (per_fill_mean(rows, GOV), per_fill_mean(rows, "R0")) if rows else None
    br, label, gates = verdict(per_year, c0, cm, pf, floors_ok, vg3_ok)
    dm = d_metrics(rows) if rows else None
    for y, v in per_year.items():
        _log(f"   {y}: G−R0 {v['d_r0']:+.4f}R · تعبئة G÷R0 {v['fill_ratio']:.3f}")
    if c0:
        _log(f"   E1 {'✅' if gates['E1'] else '🔴'} (G−R0 وسط {c0['mean']:+.4f}R · فاصل "
             f"[{c0['lo']:+.4f}, {c0['hi']:+.4f}] · الحدّ {E1_MIN_R})")
    if cm:
        _log(f"   E2 {'✅' if gates['E2'] else '🔴'} (G−M وسط {cm['mean']:+.4f}R · فاصل "
             f"[{cm['lo']:+.4f}, {cm['hi']:+.4f}] · الحدّ {E2_MIN_R})")
    _log(f"   E3 {'✅' if gates['E3'] else '🔴'} (الحدّ {E3_MIN_FILL_RATIO}) · "
         f"E4 {'✅' if gates['E4'] else '🔴'} (لكلّ مُعبَّأة G {pf[0] if pf else 0:+.4f}R مقابل "
         f"R0 {pf[1] if pf else 0:+.4f}R)")
    _log(f"   الأرضية ({FLOOR_DECIDED} مُعبَّأة في R0 وG بكلّ سنة) {'✅' if floors_ok else '🔴'} · "
         f"`V-G3` {'✅' if vg3_ok else '🔴'}")
    if dm:
        _log(f"   D1 «لازم» حرفيًّا {'✅ تصدق' if dm['D1'] else '🔴 لا تصدق'} (التغطية {dm['cover_pct']:.1f}% · "
             f"ويلسون الأدنى {dm['wilson_lo'] * 100:.1f}% · الحدّ {D1_MIN_WILSON * 100:.0f}%) · "
             f"D2 المغناطيس {'✅' if dm['D2'] else '🔴'} ({dm['magnet_pp']:+.1f} نقطة · فاصل "
             + (f"[{dm['magnet_ci']['lo'] * 100:+.1f}, {dm['magnet_ci']['hi'] * 100:+.1f}]"
                if dm.get("magnet_ci") else "—") + f" · الحدّ +{D2_MIN_PP:.0f})")
    _log(f"   ⇒ **الفرع {br}: «{label}»**")
    pred = predictions(summaries, rows, dm, gates, c0)
    _log("   🔮 التنبّؤات (تُنشر كما وقعت): " + " · ".join(
        f"{k} {'✅ صدق' if v else '❌ خاب'}" for k, v in pred.items()))
    _log("POOLED " + json.dumps({"branch": br, "label": label, "gates": gates,
                                 "floors_ok": floors_ok, "vg3_ok": vg3_ok, "d": dm,
                                 "ci_r0": c0, "ci_m": cm, "per_fill": pf, "pred": pred},
                                ensure_ascii=False, default=float))
    return br


def main() -> int:
    if not _selfcheck_readonly():
        _log("⛔ الأداةُ ليست قراءةً فقط")
        return 3
    years = [y.strip() for y in (os.environ.get("BT_YEARS") or "").split(",") if y.strip()]
    paths = [p.strip() for p in (os.environ.get("BT_FROZEN_PATHS") or "").split(",") if p.strip()]
    if not years or len(years) != len(paths):
        _log("⛔ BT_YEARS و BT_FROZEN_PATHS مطلوبان وبالطول نفسه")
        return 2
    if tuple(years) != CONTRACT_YEARS:
        _log(f"⛔ السنواتُ {years} ليست سنواتِ العقد {list(CONTRACT_YEARS)}")
        return 2
    os.environ["SCREENER_MODE"] = "BACKTEST"
    import pandas as pd                                          # noqa: PLC0415
    import Super_stock as S                                      # noqa: PLC0415
    judged, summaries = [], []
    fh = open(OUT_ROWS, "w", encoding="utf-8")
    for year, path in zip(years, paths):
        if not os.path.exists(path):
            _log(f"⛔ لقطةٌ غيرُ موجودة: {path}")
            return 2
        hist, splits_map, asof = S.load_frozen_dataset(path)
        if not hist:
            _log(f"⛔ تعذّر تحميل {path}")
            return 2
        if str(asof or "")[:4] != str(year):
            _log(f"⛔ اللقطة as-of {asof} لا تطابق سنةَ القياس {year}")
            return 2
        S.CONFIG["BT_REPLAY10"] = 1
        S.CONFIG["BT_ENVVALS"] = 1
        fwd = int(S.CONFIG["BACKTEST_FORWARD_DAYS"])
        spread = S.CONFIG.get("BT_SPREAD_PCT", 0.0) or 0.0
        lookback = int(S.CONFIG["GAP_ABOVE_LOOKBACK_D"])
        min_pct = float(S.CONFIG["GAP_MIN_PCT"])
        syms = sorted(hist)
        _log(f"\n📦 {year}: as-of {asof} · رموز {len(syms)} · نافذة {fwd}ج · سبريد {spread} · وقفُ القاع "
             f"{'مشحون' if S.CONFIG.get('PIVOT_STOP_AT_LOW') else 'مُطفأ'} · FAISAL_ONLY "
             f"{S.CONFIG.get('FAISAL_ONLY')} · الفجوة: ‏≥{min_pct}% في {lookback}ج · الأذرع " + " · ".join(ARMS))
        all_rows, gap_rows, issues, bars = [], [], {}, {}
        counts = {"split_rows": 0, "split_gaps": 0}
        lo_d, hi_d = f"{year}-01-01", f"{year}-12-31"
        for k, sym in enumerate(syms):
            df = hist.get(sym)
            if df is None or len(df) < int(S.CONFIG["MIN_BARS"]) + 60:
                continue
            try:
                trs = S.backtest_symbol(sym, df, date_window=(lo_d, hi_d),
                                        splits=(splits_map or {}).get(sym))
            except Exception as e:                               # noqa: BLE001
                issues[type(e).__name__] = issues.get(type(e).__name__, 0) + 1
                continue
            if not trs:
                continue
            sd = split_dates((splits_map or {}).get(sym))
            H = df["High"].values.astype(float)
            L = df["Low"].values.astype(float)
            C = df["Close"].values.astype(float)
            for tr in trs:
                row, why = arms_for(S, sym, df, tr, fwd, spread)  # `R0` بت-بت مع المنشور
                if row is None:
                    issues[why] = issues.get(why, 0) + 1
                    continue
                for drop in ("R27", "R23", "R27w", "R27abs"):     # ناتجٌ عرَضيٌّ لا يعني هذا العقد
                    for f in ("e_", "s_", "o_", "ret_", "bite_", "k_"):
                        row.pop(f + drop, None)
                all_rows.append(row)
                pos = int(df.index.get_loc(pd.Timestamp(tr["date"])))
                gs, nsp = gaps_below(H[:pos + 1], L[:pos + 1], C[:pos + 1], df.index[:pos + 1],
                                     sd, lookback, min_pct)
                if nsp:
                    counts["split_gaps"] += nsp
                    if not gs:
                        counts["split_rows"] += 1
                g = governing_gap(gs)
                if g is None:
                    continue
                fut = df.iloc[pos + 1:pos + 1 + fwd]
                hi = fut["High"].values.astype(float)
                lo = fut["Low"].values.astype(float)
                cl = fut["Close"].values.astype(float)
                op = fut["Open"].values.astype(float)
                r = dict(row)
                r.update({"ref_raw": float(C[pos]), "gap_b": g["b"], "gap_top": g["top"],
                          "gap_size": g["size"], "gap_ago": g["ago"], "gap_n": len(gs),
                          "gap_cov_min": g["cov_min"], "minlow": float(lo.min())})
                bars[(sym, r["date"])] = (hi, lo, cl, op)
                gap_rows.append(r)
            if (k + 1) % 500 == 0:
                _log(f"   … {k + 1}/{len(syms)} · إشارات {len(all_rows)} · فجوات {len(gap_rows)}")
        gap_rows, stats = build_arms(S, gap_rows, bars, spread)
        del hist, splits_map, bars
        gc.collect()
        rc, summ = year_report(S, year, all_rows, gap_rows, issues, stats, counts)
        if rc:
            fh.close()
            return rc
        _log("SUMMARY " + json.dumps(summ, ensure_ascii=False, default=float))
        for r in gap_rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        if summ and summ.get("n_gap"):
            judged.append((str(year), gap_rows))
            summaries.append(summ)
    fh.close()
    pooled(judged, summaries)
    return 0


if __name__ == "__main__":
    sys.exit(main())
