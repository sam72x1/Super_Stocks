#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⏳ `T-WAIT-23W` — اختبارٌ **تأكيديّ** لذراعَي فيصل `R23` و`R27w` بضبطٍ **مطابَقِ
التعبئة** وحصادٍ **لم يُرَ** (العقد `wait_rsi23w_prereg.md` مدفوعٌ **قبل هذا الملفّ**
وقبل أيّ رقم).

**السؤال:** هل تصمد الذراعان (أ) أمام ضبطٍ يجرّدهما من محتوى RSI **ويُطابقهما في عدد
التعبئة**، و(ب) على 2021/2022 (خلفيًّا) وما بعد 2026-07-10 (أماميًّا)؟

🔴 **الالتباسُ الذي بُنيت الأداةُ لإبطاله:** `no_fill` يُحتسَب صفرًا والتوقّعُ سالب ⇒
**أيُّ ذراعٍ تتاجر أقلَّ تتحسّن آليًّا** (‏`R27abs` أعطت +0.2027R بتخطّي 90%). ولأن
الضبطَ المطابقَ **للعمق** وحده يترك فرقَ تعبئةٍ يميل **لصالح** الذراع، فالضبطُ الحاكم
هنا **مطابَقُ التعبئة** `M` (عمقٌ ثابتٌ يُحَلّ عدديًّا حتى تتساوى التعبئة)، والضبطُ
الدوريُّ `C` مساندٌ يُطبَع ولا يحكم.

**إعادةُ استعمالٍ بالاسم — لا نسخ:** `wait_rsi27_arms.arms_for` تُنتج `R0`/`R23`/`R27w`
**بت-بت** كما نُشرت، ومعها `agg`/`decomp`/`r0_of`/`bootstrap_ci`/`stop_for`،
و`_resolve_arm`/`rsi_target_price`/`analyze_ticker` الإنتاجيّة عبرها.

🔒 `Super_stock.py` **و**`wait_rsi27_arms.py` لا يُمَسّان بحرف · قراءةٌ فقط · الإنتاجُ
لا يستوردها · لا `LOGIC_VERSION`."""
from __future__ import annotations

import ast
import gc
import json
import os
import sys
from collections import defaultdict

import numpy as np

from tranche_arms import FLOOR_DECIDED
from wait_rsi27_arms import (agg, arms_for, bootstrap_ci, decomp, r0_of,  # بالاسم
                             stop_for)

OUT_ROWS = "wait_rsi23w_rows.jsonl"

# §③ — سبعُ أذرعٍ مُعلَنة (‏`R27`/`R27abs` ناتجان عرَضيّان من `arms_for` يُطبَعان ولا يحكمان)
ARMS = ("R0", "R23", "R27w", "M23", "M27w", "C23", "C27w")
BYPRODUCT = ("R27", "R27abs")
GOV = ("R23", "R27w")                  # §③ — الحاكمتان (أمرُ المالك «سجّل 23 والأسبوعيّ»)
MATCH = {"R23": "M23", "R27w": "M27w"}  # §③ — الضبطُ الحاكم (مطابَقُ التعبئة)
ROTC = {"R23": "C23", "R27w": "C27w"}   # §③ — الضبطُ المساند (مطابَقُ العمق)
ROT_DEN = 3                            # §③ — الإزاحة ⌊n/3⌋ داخل السنة (حتميّة)
MATCH_ITERS = 60                       # §③ — تنصيفاتُ حلّ العمق الثابت
BOOT_N = 2000                          # §④
BOOT_SEED = 23                         # §④ — حتميّ
CI_PCT = 97.5                          # §④ — ثنائيُّ الجانب ⇒ أحاديٌّ فعليّ عند 1.25%
G1_MIN_R = 0.05                        # §④ `G1` (engineering — من `T-WAIT-LOWER`)
G2_MIN_R = 0.025                       # §④ `G2` (engineering — نصفُ بار `G1`)
G3_MIN_FILL_RATIO = 0.30               # §④ `G3` (engineering — من `T-WAIT-LOWER`)
V_S1_MIN_DIFF = 0.20                   # §④ `V-S1` — الضبطُ يختلف عن ذراعه
V_S2_MIN_CHANGED = 0.80                # §④ `V-S2` — الإزاحةُ تُغيّر المُبنَّد
V_S8_FILL_TOL = 0.02                   # §④ `V-S8` — تحقُّقُ المطابقة
SEEN_YEARS = ("2023", "2024", "2025")  # §② — بوّابةُ صلاحيةٍ فقط
DESC_YEARS = ("2026",)                 # §② — وصفيّة

# §④ `V-S0` — المنشورُ في `wait_rsi27_result.md` (‏+ ملحقُه المؤرَّخ 2026-09-09 للتعبئات)
REF23 = {
    "2023": {"r0": -0.2602, "r23": -0.1753, "r27w": -0.1444,
             "n": 1620, "f0": 1399, "f23": 554, "f27w": 824},
    "2024": {"r0": -0.1807, "r23": -0.0653, "r27w": -0.1260,
             "n": 1591, "f0": 1386, "f23": 491, "f27w": 812},
    "2025": {"r0": -0.2172, "r23": -0.0719, "r27w": -0.1526,
             "n": 1606, "f0": 1370, "f23": 469, "f27w": 856},
}


def _log(m):
    print(m, flush=True)


def raw_depth(row, arm):
    """§③ — العمقُ الخام: `d = max(0, 1 − سعرُ RSI / ref)` · و`None` ⇒ `d = 0`
    (الذراعُ ‏≡ `R0` في ذلك الصفّ). يُحسَب من **قيم الصفّ** فيبقى متّسقًا مع الضبط. نقيّة."""
    px = row.get({"R23": "rsi23", "R27w": "rsi27w"}[arm])
    ref = row.get("ref")
    try:
        if px is None or not ref or float(ref) <= 0:
            return 0.0
        return max(0.0, 1.0 - float(px) / float(ref))
    except (TypeError, ValueError):
        return 0.0


def rotate(vals, den=ROT_DEN):
    """§③ — إزاحةٌ حتميّة `π(i) = (i + ⌊n/den⌋) mod n` · **تبديلٌ** فتوزيعُ الأعماق محفوظ."""
    n = len(vals)
    if n == 0:
        return []
    sh = (max(1, n // int(den)) % n) if n > 1 else 0
    return [vals[(i + sh) % n] for i in range(n)]


def entry_at(ref, e0, d):
    """§③ — دخولُ ذراعِ ضبطٍ بعمق `d`. **عمقٌ صفر ⇒ `entry0` حرفيًّا** (تناظرٌ مع
    الذراع عند `None`) — فـ`ref` قد يقع **تحت** متوسّط الدفعات فلا يصحّ `min(ref, e0)`."""
    e0 = float(e0)
    return e0 if float(d) <= 0.0 else min(float(ref) * (1.0 - float(d)), e0)


def fill_count(rows, d):
    """عددُ الصفوف التي تتعبّأ عند عمقٍ **ثابت** `d` — بأدنى قاعٍ محسوبٍ مرّةً واحدة."""
    n = 0
    for r in rows:
        if r.get("minlow") is None:
            continue
        if float(r["minlow"]) <= entry_at(r["ref"], r["e_R0"], d):
            n += 1
    return n


def solve_match_depth(rows, target, iters=MATCH_ITERS):
    """§③ — بحثٌ ثنائيٌّ على عمقٍ ثابتٍ يُصغّر `|تعبئة(M) − target|`. التعبئةُ **متناقصةٌ
    رتيبًا** في العمق فالتنصيفُ صالح. حتميٌّ ونقيّ (لا عشوائيّة)."""
    lo, hi = 0.0, 0.99
    best, best_err = 0.0, abs(fill_count(rows, 0.0) - target)
    for _ in range(int(iters)):
        mid = (lo + hi) / 2.0
        c = fill_count(rows, mid)
        err = abs(c - target)
        if err < best_err:
            best, best_err = mid, err
        if c > target:
            lo = mid
        else:
            hi = mid
    return best, best_err


def build_controls(S, hist, rows, fwd, spread):
    """§③ — التمريرةُ الثانية: تُضيف مفاتيحَ أذرع الضبط إلى **الصفوف نفسِها** (فتعمل
    `agg`/`decomp` المستورَدتان عليها بلا تعديل)، ولا تُعيد تشغيل `analyze_ticker`.
    الصفُّ الذي يتعذّر بناءُ ضبطه **يُسقَط من المجتمع كلِّه** (مقامٌ واحد · `V-S7`).

    🔴 **أذرعُ الضبط نماذجُ عدمٍ إحصائيّة لا استراتيجيّاتٌ قابلةٌ للتنفيذ** — `C` تأخذ
    عمقَ صفٍّ آخر (قد يكون لاحقًا) و`M` يُحَلّ على المجتمع كلِّه ⇒ **لا تُشحَن أبدًا.**"""
    import pandas as pd                                          # noqa: PLC0415
    rows.sort(key=lambda r: (r["symbol"], r["date"]))            # ترتيبٌ حتميّ قبل الإزاحة
    keep, dropped = [], 0
    bars = {}
    for r in rows:
        try:
            df = hist.get(r["symbol"])
            pos = df.index.get_loc(pd.Timestamp(r["date"]))
            k0 = int(pos) + 1
            fut = df.iloc[k0:k0 + fwd]
            if not len(fut):
                raise ValueError("نافذةٌ فارغة")
            hi = fut["High"].values.astype(float)
            lo = fut["Low"].values.astype(float)
            cl = fut["Close"].values.astype(float)
            op = fut["Open"].values.astype(float)
        except Exception:                                        # noqa: BLE001
            dropped += 1
            continue
        r["minlow"] = float(lo.min())
        bars[(r["symbol"], r["date"])] = (hi, lo, cl, op)
        keep.append(r)
    rows = keep

    depth = {g: [raw_depth(r, g) for r in rows] for g in GOV}
    rot = {g: rotate(depth[g]) for g in GOV}
    md, merr = {}, {}
    for g in GOV:
        target = sum(1 for r in rows if r.get(f"o_{g}") not in (None, "no_fill", "skip"))
        md[g], merr[g] = solve_match_depth(rows, target)

    stats = {"dropped": dropped, "same": {g: 0 for g in GOV},
             "live": {g: 0 for g in GOV}, "match_depth": md, "match_err": merr,
             "diff": {}, "n": len(rows)}
    for i, r in enumerate(rows):
        hi, lo, cl, op = bars[(r["symbol"], r["date"])]
        e0, s0, t1 = r["e_R0"], r["stop0"], r["t1"]
        plan = [(ROTC[g], rot[g][i]) for g in GOV] + [(MATCH[g], md[g]) for g in GOV]
        for name, d in plan:
            entry = entry_at(r["ref"], e0, d)
            stop = stop_for(entry, e0, s0)
            if stop is None or entry - stop <= 0:
                r[f"e_{name}"], r[f"s_{name}"] = round(entry, 4), None
                r[f"o_{name}"], r[f"ret_{name}"] = "skip", None
                r[f"bite_{name}"] = bool(entry < float(e0) - 1e-12)
                r[f"k_{name}"] = None
                continue
            filled = next((k for k in range(len(lo)) if lo[k] <= entry), None)
            o, rt, _, _ = S._resolve_arm(hi, lo, cl, op, entry, stop, t1, filled,
                                         spread=spread)
            r[f"e_{name}"], r[f"s_{name}"] = round(entry, 4), round(stop, 4)
            r[f"o_{name}"] = o
            r[f"ret_{name}"] = (round(rt, 1) if rt is not None else None)
            r[f"bite_{name}"] = bool(entry < float(e0) - 1e-12)
            r[f"k_{name}"] = filled
        for g in GOV:
            if depth[g][i] > 0.0:
                stats["live"][g] += 1
                if abs(rot[g][i] - depth[g][i]) < 1e-12:
                    stats["same"][g] += 1
    for g in GOV:
        for c in (ROTC[g], MATCH[g]):
            stats["diff"][c] = sum(
                1 for r in rows
                if (r.get(f"o_{c}"), r.get(f"ret_{c}")) != (r.get(f"o_{g}"), r.get(f"ret_{g}"))
            ) / max(len(rows), 1)
    return rows, stats


def boot_rows(vals, pct=CI_PCT, n_boot=BOOT_N, seed=BOOT_SEED):
    """فاصلٌ على مستوى الصفّ عند نسبةٍ حرّة (يُطبَع · لا يحكم)."""
    d = np.asarray([float(x) for x in vals], dtype=float)
    if not len(d):
        return None
    rng = np.random.default_rng(int(seed))
    means = np.array([d[rng.integers(0, len(d), len(d))].mean()
                      for _ in range(int(n_boot))])
    lo = (100.0 - float(pct)) / 2.0
    return (float(np.percentile(means, lo)), float(d.mean()),
            float(np.percentile(means, 100.0 - lo)))


def cluster_ci(rows, base, arm, pct=CI_PCT, n_boot=BOOT_N, seed=BOOT_SEED):
    """§④ **المقدِّرُ الحاكم** — بوتستراب **عنقوديٌّ بالرمز** بمُقدِّرِ نسبةِ المجاميع:
    الصفوفُ ليست مستقلّة (الرمزُ يتكرّر وأخطاؤه مرتبطة) فمعايَنةُ الصفوف تُضيّق الفاصلَ كذبًا."""
    g = defaultdict(list)
    for r in rows:
        if r.get(f"o_{base}") is None or r.get(f"o_{arm}") is None:
            continue
        g[r["symbol"]].append(r0_of(r, arm) - r0_of(r, base))
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


def per_fill_mean(rows, name):
    """§④ `G4` — توقّعُ **الصفقة المُعبَّأة** وحدَها (لا المقام الكامل): يمنع الفوزَ
    بقلّة التداول. نقيّة."""
    v = [r0_of(r, name) for r in rows
         if r.get(f"o_{name}") not in (None, "no_fill", "skip")]
    return (sum(v) / len(v)) if v else 0.0


def _selfcheck_readonly() -> bool:
    """قراءةٌ فقط (نمطُ `TV6`): صفرُ إرسالٍ وصفرُ كتابةِ حالة (بالـAST على مصدرها هي)."""
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


def role_of(year, holdout):
    """§② — الدور: `H-FWD` (حصادٌ أماميٌّ لسنةٍ غيرِ مرئيّة) · `seen` · `desc` ·
    وإلّا `H-BACK`. 🔒 سنةٌ مرئيّةٌ **لا تصير** حصادًا بمجرّد تمرير حدٍّ زمنيّ."""
    y = str(year)
    if holdout and y not in SEEN_YEARS:
        return "H-FWD"
    if y in SEEN_YEARS:
        return "seen"
    if y in DESC_YEARS:
        return "desc"
    return "H-BACK"


def year_report(rows, year, issues, role, stats):
    """يطبع سنةً واحدة ويرجّع (رمزُ خروجٍ، ملخّص). 0 سليم · 3 عطبُ أداة · 4 لا حكم."""
    ref = REF23.get(str(year))
    tag = {"seen": " (مرئيّة — بوّابةُ صلاحيةٍ ووصفٌ لا حكم)",
           "desc": " (وصفيّةٌ خارج الحكم)",
           "H-BACK": " (غيرُ مرئيّة خلفيًّا — يُحكَم بها)",
           "H-FWD": " (غيرُ مرئيّة أماميًّا — يُحكَم بها)"}[role]
    _log(f"\n⏳ T-WAIT-23W · سنة {year}{tag} · صفقات {len(rows)}")
    if issues:
        _log("   ℹ️ أسبابُ عدم القياس: " + " · ".join(
            f"{k} {v}" for k, v in sorted(issues.items())))
    if not rows:
        _log("   ⛔ صفرُ صفقات ⇒ `no-op`")
        return 4, None
    dates = sorted(r["date"] for r in rows if r.get("date"))
    _log(f"   📅 المدى {dates[0]} ⟶ {dates[-1]} · رموزٌ فريدة "
         f"{len({r['symbol'] for r in rows})} · صفوفٌ أُسقطت لتعذّر الضبط "
         f"{stats['dropped']} (مقامٌ واحد)")

    same0 = sum(1 for r in rows if r.get("o_R0") == r.get("prod_o"))
    pct0 = same0 / len(rows) * 100.0
    _log(f"   🔒 `V-S6` حسمُ `R0` = حسمُ الإنتاج: {same0}/{len(rows)} ({pct0:.2f}%)")
    if pct0 < 99.0:
        _log("   ⛔ `V-S6` سقطت ⇒ الآلةُ ليست نفسَها")
        return 3, None

    a = {nm: agg(rows, nm) for nm in ARMS + BYPRODUCT}
    counts = {nm: a[nm]["n"] for nm in ARMS}
    if len(set(counts.values())) != 1:                            # `V-S7`
        _log(f"   ⛔ `V-S7` مقاماتٌ مختلفة: {counts}")
        return 3, None
    for g in GOV:
        if a[g]["n_fill"] > a["R0"]["n_fill"]:                    # `V-S4`
            _log(f"   ⛔ `V-S4` تعبئةُ `{g}` تتجاوز `R0`")
            return 3, None
        if all(r.get(f"o_{g}") == r.get("o_R0")
               and r.get(f"ret_{g}") == r.get("ret_R0") for r in rows):   # `V-S5`
            _log(f"   ⛔ `V-S5` `{g}` لم تتفرّق عن `R0` ⇒ `no-op`")
            return 4, None
        frac = stats["same"][g] / max(stats["live"][g], 1)         # `V-S2`
        if (1.0 - frac) < V_S2_MIN_CHANGED:
            _log(f"   ⛔ `V-S2` الإزاحةُ غيّرت {(1 - frac) * 100:.1f}% من مُبنَّد `{g}` "
                 f"(الحدّ {V_S2_MIN_CHANGED * 100:.0f}%)")
            return 3, None
        for c in (ROTC[g], MATCH[g]):                              # `V-S1`
            if stats["diff"][c] < V_S1_MIN_DIFF:
                _log(f"   ⛔ `V-S1` الضبطُ `{c}` يختلف عن `{g}` في "
                     f"{stats['diff'][c] * 100:.1f}% فقط ⇒ ضبطٌ عديمُ الأثر")
                return 3, None
    if ref:                                                        # `V-S0`
        got = (round(a["R0"]["r_fixed"], 4), round(a["R23"]["r_fixed"], 4),
               round(a["R27w"]["r_fixed"], 4), len(rows),
               a["R0"]["n_fill"], a["R23"]["n_fill"], a["R27w"]["n_fill"])
        exp = (ref["r0"], ref["r23"], ref["r27w"], ref["n"],
               ref["f0"], ref["f23"], ref["f27w"])
        ok0 = all(abs(float(x) - float(y)) < 5e-5 for x, y in zip(got, exp))
        _log(f"   🔒 `V-S0` {got} مقابل المنشور {exp} ⇒ {'✅ بت-بت' if ok0 else '⛔ تفرّق'}")
        if not ok0:
            return 3, None

    _log("   ┌─ الأذرع (‏`R₀` الثابتة · `no_fill`/`skip` = 0R في المقام) ─")
    for nm in ARMS + BYPRODUCT:
        x = a[nm]
        mk = " 🥇" if nm in GOV else (" ⚖️" if nm in stats["diff"] else
                                     (" ℹ️" if nm in BYPRODUCT else ""))
        _log(f"   │ {nm}{mk}: R₀ {x['r_fixed']:+.4f} · تعبئة {x['fill_pct']:.1f}% "
             f"({x['n_fill']}) · ربح {x['win_pct']:.2f}% · لكلّ مُعبَّأة "
             f"{per_fill_mean(rows, nm):+.4f}R")
    _log("   └───────────────────────────────────────────────────────────")

    out = {"year": str(year), "role": role, "n_rows": len(rows),
           "dates": [dates[0], dates[-1]], "dropped": stats["dropped"],
           "n_sym": len({r["symbol"] for r in rows}),
           "match_depth": stats["match_depth"], "match_err": stats["match_err"],
           "arms": a, "per_fill": {nm: per_fill_mean(rows, nm)
                                   for nm in ARMS + BYPRODUCT},
           "gates": {}, "decomp": {}}
    for g in GOV:
        m = MATCH[g]
        tol = V_S8_FILL_TOL * max(a[g]["n_fill"], 1)
        ok8 = abs(a[m]["n_fill"] - a[g]["n_fill"]) <= max(tol, 1.0)
        _log(f"   🎯 `{g}`: عمقُ الضبط المحلول {stats['match_depth'][g] * 100:.1f}% ⇒ "
             f"تعبئة {a[m]['n_fill']} مقابل {a[g]['n_fill']} · `V-S8` "
             f"{'✅ مطابقة' if ok8 else '🔴 غيرُ قابلٍ للمقارنة'}")
        c0 = cluster_ci(rows, "R0", g)
        cm = cluster_ci(rows, m, g)
        cr = cluster_ci(rows, ROTC[g], g)
        _log(f"   📏 `{g}`−R0 عنقوديٌّ {CI_PCT}% [{c0['lo']:+.4f}, {c0['hi']:+.4f}] "
             f"وسط {c0['mean']:+.4f} (رموز {c0['n_sym']}) · صفّيٌّ 95% "
             f"{tuple(round(v, 4) for v in (bootstrap_ci([r0_of(r, g) - r0_of(r, 'R0') for r in rows]) or (0, 0, 0)))}")
        _log(f"   ⚖️ `{g}`−`{m}` (الضبطُ الحاكم) [{cm['lo']:+.4f}, {cm['hi']:+.4f}] "
             f"وسط {cm['mean']:+.4f} · `{g}`−`{ROTC[g]}` (مساند) وسط {cr['mean']:+.4f}")
        d = decomp(rows, g)
        b = d["buckets"]
        _log(f"   🔬 تفكيك `{g}` (هويّة {'✅' if d['identity_ok'] else '⛔'}): "
             + " · ".join(f"{k} n={b[k]['n']} {b[k]['mean_per_row']:+.4f}R"
                          for k in ("B0", "B1", "B2", "B3")))
        out["decomp"][g] = d
        out["gates"][g] = {"vs_r0": c0, "vs_match": cm, "vs_rot": cr, "v_s8": ok8,
                           "fill_ratio": a[g]["n_fill"] / max(a["R0"]["n_fill"], 1)}
    return 0, out


def pooled(judged):
    """§④ — الحكمُ المجمَّع على السنوات المحكومة: عنقدةٌ بالرمز **عبر السنوات معًا**
    (الرمزُ الواحد عنقودٌ واحد — محافِظ)، وأرجلُ `G1`-`G4` كما ثُبِّتت في العقد."""
    rows = [r for _, rs in judged for r in rs]
    years = [y for y, _ in judged]
    _log(f"\n══════ الحكمُ المجمَّع على {len(years)} سنةً محكومة: {' · '.join(years)} "
         f"({len(rows)} صفًّا) ══════")
    if len(years) < 2:
        _log("   ⛔ سنةٌ واحدةٌ فقط ⇒ **لا قياس** (العقد §④)")
        return 4
    verdict = {}
    for g in GOV:
        m = MATCH[g]
        c0, cm = cluster_ci(rows, "R0", g), cluster_ci(rows, m, g)
        per_year = {y: (agg(rs, g)["r_fixed"] - agg(rs, "R0")["r_fixed"])
                    for y, rs in judged}
        fills = {y: agg(rs, g)["n_fill"] / max(agg(rs, "R0")["n_fill"], 1)
                 for y, rs in judged}
        g1 = (all(v > 0 for v in per_year.values()) and c0["mean"] >= G1_MIN_R
              and c0["lo"] > 0)
        g2 = cm["mean"] >= G2_MIN_R and cm["lo"] > 0
        g3 = all(v >= G3_MIN_FILL_RATIO for v in fills.values())
        g4 = per_fill_mean(rows, g) >= per_fill_mean(rows, "R0")
        _log(f"   🥇 `{g}`: G1 {'✅' if g1 else '🔴'} (وسط {c0['mean']:+.4f}R · "
             f"فاصل [{c0['lo']:+.4f}, {c0['hi']:+.4f}] · بالسنة "
             + " · ".join(f"{y} {v:+.4f}" for y, v in per_year.items()) + ")")
        _log(f"      G2 {'✅' if g2 else '🔴'} (‏−`{m}` وسط {cm['mean']:+.4f}R · "
             f"فاصل [{cm['lo']:+.4f}, {cm['hi']:+.4f}] · الحدّ {G2_MIN_R})")
        _log(f"      G3 {'✅' if g3 else '🔴'} (" + " · ".join(
            f"{y} {v:.3f}" for y, v in fills.items()) + f" · الحدّ {G3_MIN_FILL_RATIO})")
        _log(f"      G4 {'✅' if g4 else '🔴'} (لكلّ مُعبَّأة {per_fill_mean(rows, g):+.4f}R "
             f"مقابل `R0` {per_fill_mean(rows, 'R0'):+.4f}R)")
        _log(f"      ⇒ **{'مرشَّحٌ مستمرّ (ينتظر الحصادَ الأماميّ)' if (g1 and g2 and g3 and g4) else 'لا تُوصى'}**")
        verdict[g] = {"G1": g1, "G2": g2, "G3": g3, "G4": g4,
                      "vs_r0": c0, "vs_match": cm, "per_year": per_year,
                      "fills": fills}
    _log("POOLED " + json.dumps({"years": years, "n_rows": len(rows),
                                 "verdict": verdict}, ensure_ascii=False, default=float))
    return 0


def main() -> int:
    if not _selfcheck_readonly():
        _log("⛔ الأداةُ ليست قراءةً فقط")
        return 3
    years = [y.strip() for y in (os.environ.get("BT_YEARS") or "").split(",") if y.strip()]
    paths = [p.strip() for p in (os.environ.get("BT_FROZEN_PATHS") or "").split(",")
             if p.strip()]
    if not years or len(years) != len(paths):
        _log("⛔ BT_YEARS و BT_FROZEN_PATHS مطلوبان وبالطول نفسه")
        return 2
    holdout = (os.environ.get("HOLDOUT_AFTER") or "").strip()
    os.environ["SCREENER_MODE"] = "BACKTEST"
    import Super_stock as S                                      # noqa: PLC0415
    judged, rc_all = [], 0
    fh = open(OUT_ROWS, "w", encoding="utf-8")
    for year, path in zip(years, paths):
        if not os.path.exists(path):
            _log(f"⛔ لقطةٌ غيرُ موجودة: {path}")
            return 2
        hist, splits_map, asof = S.load_frozen_dataset(path)
        if not hist:
            _log(f"⛔ تعذّر تحميل {path}")
            return 2
        S.CONFIG["BT_REPLAY10"] = 1
        S.CONFIG["BT_ENVVALS"] = 1
        fwd = int(S.CONFIG["BACKTEST_FORWARD_DAYS"])
        spread = S.CONFIG.get("BT_SPREAD_PCT", 0.0) or 0.0
        role = role_of(year, holdout)
        # 🔒 `V-S3` تغطيةُ اللقطة: بلا حصادٍ ⇒ سنةُ اللقطة = سنةُ القياس · ومعه ⇒ as-of بعده
        if holdout and role == "H-FWD":
            if not (str(asof or "") > holdout):
                _log(f"⛔ `V-S3` as-of {asof} ليست بعد حدّ الحصاد {holdout}")
                return 4
        elif str(asof or "")[:4] != str(year):
            _log(f"⛔ `V-S3` اللقطة as-of {asof} لا تطابق سنةَ القياس {year}")
            return 4
        syms = sorted(hist)
        _log(f"\n📦 {year}: as-of {asof} · رموز {len(syms)} · نافذة {fwd}ج · سبريد "
             f"{spread} · وقفُ القاع "
             f"{'مشحون' if S.CONFIG.get('PIVOT_STOP_AT_LOW') else 'مُطفأ'} · الأذرع "
             + " · ".join(ARMS) + f" · الدور {role}"
             + (f" · حصادٌ بعد {holdout}" if holdout else ""))
        rows, issues = [], {}
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
            for tr in trs:
                if holdout and str(tr.get("date") or "") <= holdout:
                    issues["خارج نافذة الحصاد"] = issues.get("خارج نافذة الحصاد", 0) + 1
                    continue
                row, why = arms_for(S, sym, df, tr, fwd, spread)  # بت-بت مع المنشور
                if row is None:
                    issues[why] = issues.get(why, 0) + 1
                    continue
                rows.append(row)
            if (k + 1) % 500 == 0:
                _log(f"   … {k + 1}/{len(syms)} · صفوف {len(rows)}")
        rows, stats = build_controls(S, hist, rows, fwd, spread)
        del hist, splits_map
        gc.collect()
        rc, summ = year_report(rows, year, issues, role, stats)
        if rc:
            fh.close()
            return rc
        _log("SUMMARY " + json.dumps(summ, ensure_ascii=False, default=float))
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        if role in ("H-BACK", "H-FWD"):
            if (agg(rows, "R0")["n_fill"] < FLOOR_DECIDED
                    or min(agg(rows, g)["n_fill"] for g in GOV) < FLOOR_DECIDED):
                _log(f"   ⛔ الأرضية: دون {FLOOR_DECIDED} مُعبَّأة ⇒ السنةُ تخرج من الحكم")
            else:
                judged.append((str(year), rows))
    fh.close()
    if judged:
        rc_all = pooled(judged) or rc_all
    else:
        _log("\nℹ️ لا سنةَ محكومة في هذي التشغيلة (صلاحيةٌ/وصفٌ فقط)")
    return rc_all


if __name__ == "__main__":
    sys.exit(main())
