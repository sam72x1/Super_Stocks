# -*- coding: utf-8 -*-
"""
🧭 FAISAL V4 — التقييم (دوالٌّ نقيّة · حتميّة · بلا شبكة) — هذا الملفُّ هو نصُّ المقاييس المسجَّلة في `V4_prereg.md` §⑤-§⑩.

المدخل: حالاتُ `results/cases_v4.json` ‏+ شموعٌ يوميّة {الرمز: [[تاريخ، o، h، l، c، v] …]} (من وضع fetch على Actions).
المخرج: مصفوفةُ القرار (§9) ‏+ H-LEVEL (وفاءُ المستويات مقابل خطّ أساسٍ عشوائيٍّ مطابق العدد) ‏+ H-CLASS (فئةُ الخطّة مقابل
الأغلبيّة) ‏+ H-STATE (وصفيّ) ‏+ تصنيفُ DXST (§19) ‏+ تأريخُ VEEE (§20).

⚖️ لا اختيارَ لتشغيلةٍ مواتية (§25): التشغيلةُ الكاملةُ الأولى هي النتيجة · وأيُّ إعادةٍ تُنشر بجانبها.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decision_engine as E      # noqa: E402

SEED = 20261002
B_BOOT = 2000
BAND_LO, BAND_HI = 0.60, 1.40     # نطاقُ خطّ الأساس العشوائيّ حول سعر القراءة (‏−40% · ‏+40%)
TOL = 0.02                        # «دقة الخطأ لاتتجاوز 2٪»
PX_TOL = 0.15                     # فحصُ المقياس: |إغلاق القراءة ÷ سعر الصورة − 1| فوق 15% ⟵ SCALE_MISMATCH (يُستبعد من H-LEVEL)
LEVEL_KINDS = ("support", "bottom", "zone_lo", "zone_hi", "sweep", "trigger", "resistance", "stop")
DELTA = math.log(1 + TOL)


# ── الحالة الواحدة ─────────────────────────────────────────────────────────────────────────
def run_case(case, rows, context=None):
    """يشغّل المحرّك عند آخر جلسةٍ قبل تاريخ العبارة حصرًا ⟵ ملخّصٌ مضغوط ‏+ فحصُ المقياس."""
    sd = case.get("statement_date")
    if not rows:
        return {"case": case["case"], "status": "NO_BARS"}
    d = E.analyze_rows(rows, asof_date=sd, context=context, symbol=(case.get("tickers") or ["?"])[0])
    close = (d.get("price_location") or {}).get("close")
    px = case.get("px_F")
    scale = None
    if close and px:
        scale = round(close / px, 4)
    status = "OK"
    if d.get("tech_state") == "DATA_INSUFFICIENT":
        status = "DATA_INSUFFICIENT"
    elif scale is not None and abs(scale - 1) > PX_TOL:
        status = "SCALE_MISMATCH"
    return {"case": case["case"], "status": status, "asof": d.get("asof"), "close": close, "px_F": px, "scale": scale,
            "state": d.get("state"), "tech_state": d.get("tech_state"), "decisive_level": d.get("decisive_level"),
            "decisive_class": d.get("decisive_class"), "levels": (d.get("support_resistance") or {}).get("levels") or {},
            "structure": d.get("structure"), "entry": d.get("entry"), "target": d.get("target"),
            "blocking": d.get("blocking_reasons"), "missing": d.get("missing_information"), "rule_ids": d.get("rule_ids"),
            "explain": d.get("explain"), "market_context": d.get("market_context"), "patterns": d.get("patterns")}


# ── H-LEVEL ───────────────────────────────────────────────────────────────────────────────
def _merge(levels):
    """مستوياتُ المحرّك الفريدة: ما بينها أقلُّ من 2% يُدمَج (فلا يتضخّم K بالتكرار)."""
    out = []
    for x in sorted(v for v in levels if v and v > 0):
        if not out or math.log(x / out[-1]) > DELTA:
            out.append(x)
    return out


def _q_cover(f, close):
    """نسبةُ نطاق خطّ الأساس (لوغاريتميًّا) التي يصيب فيها مستوًى عشوائيٌّ واحدٌ المستوى f ضمن 2%."""
    lo, hi = math.log(close * BAND_LO), math.log(close * BAND_HI)
    a, b = max(lo, math.log(f) - DELTA), min(hi, math.log(f) + DELTA)
    return max(0.0, b - a) / (hi - lo)


def in_band(x, close):
    return close * BAND_LO <= x <= close * BAND_HI


def level_rows(case, res):
    """صفٌّ لكلّ مستوًى نصّيٍّ لفيصل داخل النطاق: إصابةُ المحرّك (0/1) · احتمالُ الإصابة العشوائيّة المطابقة K · أقربُ مستوى."""
    if res.get("status") != "OK":
        return []
    close = res["close"]
    eng = _merge(res["levels"].values())
    eng_in = [x for x in eng if in_band(x, close)]
    k = len(eng_in)
    out = []
    for lv in case.get("levels_F") or []:
        f = lv.get("price")
        if not f or lv.get("kind") not in LEVEL_KINDS or not in_band(f, close):
            continue
        near = min(eng, key=lambda x: abs(math.log(x / f))) if eng else None
        hit = bool(near and abs(math.log(near / f)) <= DELTA)
        q = _q_cover(f, close)
        p = 1 - (1 - q) ** k
        names = [n for n, v in res["levels"].items() if v and abs(math.log(v / f)) <= DELTA]
        out.append({"case": case["case"], "kind": lv["kind"], "f": f, "src": lv.get("src"), "derived": bool(lv.get("derived")),
                    "hit": int(hit), "p_random": round(p, 6), "k": k, "nearest": near,
                    "dist_pct": (round((near / f - 1) * 100, 3) if near else None), "matched_names": names})
    return out


def boot_ci(rows, seed=SEED, n=B_BOOT):
    """فرقُ (إصابة − عشوائيّ) بمتوسّطٍ على المستويات · وفاصلٌ 95% ببوتستراب عنقوديّ على الحالات (بذرةٌ ثابتة)."""
    if not rows:
        return None
    by = {}
    for r in rows:
        by.setdefault(r["case"], []).append(r["hit"] - r["p_random"])
    keys = sorted(by)
    point = float(np.mean([x for k_ in keys for x in by[k_]]))
    rng = np.random.RandomState(seed)
    stats = []
    for _ in range(n):
        pick = rng.randint(0, len(keys), len(keys))
        vals = [x for i in pick for x in by[keys[i]]]
        stats.append(np.mean(vals))
    lo, hi = np.percentile(stats, [2.5, 97.5])
    return {"diff": round(point, 4), "ci95": [round(float(lo), 4), round(float(hi), 4)], "cases": len(keys), "levels": len(rows),
            "hit_rate": round(float(np.mean([r["hit"] for r in rows])), 4),
            "random_rate": round(float(np.mean([r["p_random"] for r in rows])), 4)}


def h_level_verdict(stat):
    """§⑤: PASS إن (الفرق ≥ 0.15 والحدُّ الأدنى للفاصل > 0) · وإلّا FAIL · وبلا مستويات ⟵ NO_DATA."""
    if not stat:
        return "NO_DATA"
    return "PASS" if (stat["diff"] >= 0.15 and stat["ci95"][0] > 0) else "FAIL"


# ── H-CLASS ───────────────────────────────────────────────────────────────────────────────
def class_agree(plan, eng):
    if plan == "NONE" or eng is None:
        return False
    if plan == "BOTH":
        return eng in ("BELOW", "ABOVE")
    return plan == eng


def wilson(k, n, z=1.959964):
    if n == 0:
        return None
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(c - h, 4), round(c + h, 4)]


def h_class(pairs):
    """pairs = [(plan_F, decisive_class)] ⟵ الاتّفاق · ويلسون · خطُّ الأغلبيّة · الحكم (§⑥)."""
    pairs = [(p, e) for p, e in pairs if p]
    n = len(pairs)
    if not n:
        return {"n": 0, "verdict": "NO_DATA"}
    k = sum(class_agree(p, e) for p, e in pairs)
    counts = {}
    for p, _ in pairs:
        counts[p] = counts.get(p, 0) + 1
    maj = max(counts.values()) / n
    w = wilson(k, n)
    return {"n": n, "agree": k, "rate": round(k / n, 4), "wilson95": w, "majority_class": max(counts, key=counts.get),
            "majority_rate": round(maj, 4), "plan_counts": counts,
            "verdict": "PASS" if w and w[0] > maj else "FAIL"}


# ── H-STATE (وصفيّ) ───────────────────────────────────────────────────────────────────────
def h_state(pairs):
    m = {}
    for f, e in pairs:
        m.setdefault(f, {}).setdefault(e, 0)
        m[f][e] += 1
    return m


# ── §19 DXST ──────────────────────────────────────────────────────────────────────────────
DXST_ANCHORS = {"L1": 2.40, "NECK": 2.864, "L2": 2.55}       # رسمُ فيصل IMG_0627/0628 (V31_prereg :26)


def _near(x, a):
    return abs(math.log(x / a)) <= DELTA


def dxst_classify(m30_by_session, cutoff="2026-06-16 12:30", lookback=120):
    """شجرةُ القرار المسجَّلة (§⑧): A مكتشفٌ افتراضيٌّ يعيدها · B نقاطٌ في البيانات لا محاور · D محاورُ موجودة والمكتشفُ لا يختارها ·
    C النقاطُ غائبةٌ عن البيانات · E بياناتٌ ناقصة. ⟵ لكلّ جلسةٍ (regular · extended) ثمّ حكمٌ واحد."""
    import faisal_tool as V31
    out = {}
    for name, rows in m30_by_session.items():
        rows = [r for r in rows or [] if str(r[0]) <= cutoff][-lookback:]
        if len(rows) < 40:
            out[name] = {"bars": len(rows), "step1": None, "step2": None, "step3": None}
            continue
        h = np.array([float(r[2]) for r in rows])
        lo = np.array([float(r[3]) for r in rows])
        o = np.array([float(r[1]) for r in rows])
        c = np.array([float(r[4]) for r in rows])
        n = len(rows)
        s1 = None
        for i in range(n):
            if not _near(lo[i], DXST_ANCHORS["L1"]):
                continue
            for j in range(i + 1, n):
                if not _near(h[j], DXST_ANCHORS["NECK"]):
                    continue
                m = next((m for m in range(j + 1, n) if _near(lo[m], DXST_ANCHORS["L2"])), None)
                if m is not None:
                    s1 = [rows[i][0], rows[j][0], rows[m][0]]
                    break
            if s1:
                break
        s2 = {}
        for k in (1, 2, 3):
            sw = V31.confirmed_swings(h, lo, n - 1, k)
            ls = [(i, p) for i, t, p in sw if t == "L"]
            hs = [(i, p) for i, t, p in sw if t == "H"]
            hit = None
            for i1, p1 in ls:
                if not _near(p1, DXST_ANCHORS["L1"]):
                    continue
                for ih, ph in hs:
                    if ih <= i1 or not _near(ph, DXST_ANCHORS["NECK"]):
                        continue
                    for i2, p2 in ls:
                        if i2 > ih and _near(p2, DXST_ANCHORS["L2"]):
                            hit = [rows[i1][0], rows[ih][0], rows[i2][0]]
                            break
                    if hit:
                        break
                if hit:
                    break
            s2[k] = hit
        w = V31.find_w(o, h, lo, c, n - 1, 2)
        s3 = bool(w and _near(w["low1"], DXST_ANCHORS["L1"]) and _near(w["neckline"], DXST_ANCHORS["NECK"])
                  and _near(w["low2"], DXST_ANCHORS["L2"]))
        out[name] = {"bars": n, "first": rows[0][0], "last": rows[-1][0], "step1": s1, "step2": s2, "step3": s3,
                     "w_found": ({x: w[x] for x in ("low1", "neckline", "low2")} if w else None)}
    reg = out.get("regular") or {}
    anyp = [v for v in out.values() if v.get("bars", 0) >= 40]
    if not anyp:
        verdict = "E"
    elif reg.get("step3"):
        verdict = "A"
    elif any(v.get("step1") for v in anyp):
        verdict = "D" if any(any(x for x in (v.get("step2") or {}).values()) for v in anyp) else "B"
    else:
        verdict = "C"
    label = {"A": "REPRODUCIBLE_RULE", "B": "MANUAL_JUDGMENT_UNREPRODUCIBLE (رسمٌ يدويّ — النقاطُ ليست محاور)",
             "D": "MANUAL_JUDGMENT_UNREPRODUCIBLE (اختيارٌ تقديريّ بين بُنًى صالحة)",
             "C": "DATA_UNAVAILABLE (نقاطُه غائبةٌ عن بياناتنا)", "E": "UNRESOLVED (بياناتٌ ناقصة)"}[verdict]
    return {"sessions": out, "verdict": verdict, "label": label, "anchors": DXST_ANCHORS}


# ── §20 VEEE ──────────────────────────────────────────────────────────────────────────────
VEEE_ANCHORS = {"A8": {"close": 6.76, "low60": 5.00, "high60": 8.80, "src": "TG_1972 (يوميّ: قاع 5.00 · قمّة 8.80) ‏+ 6.89 ÷ 1.0192"},
                "A9": {"close": 6.76, "low60": 5.00, "high60": 9.67, "src": "V3.1 (قمّةُ ذيل 4 ساعات TG_1865)"}}


def veee_date(rows, anchors, close_tol=0.01, ext_tol=0.02, window=60):
    """الجلساتُ التي إغلاقُها ضمن 1% من المرساة وفي الستّين قبلها (شاملةً) قاعٌ وقمّةٌ ضمن 2% ⟵ DATED · AMBIGUOUS · UNKNOWN."""
    hits = []
    for i in range(len(rows)):
        c = float(rows[i][4])
        if abs(c / anchors["close"] - 1) > close_tol:
            continue
        seg = rows[max(0, i - window + 1):i + 1]
        lo = min(float(r[3]) for r in seg)
        hi = max(float(r[2]) for r in seg)
        if abs(lo / anchors["low60"] - 1) <= ext_tol and abs(hi / anchors["high60"] - 1) <= ext_tol:
            hits.append(str(rows[i][0])[:10])
    return {"candidates": hits, "verdict": ("DATED" if len(hits) == 1 else ("AMBIGUOUS" if hits else "UNKNOWN"))}


# ── التجميع ───────────────────────────────────────────────────────────────────────────────
def evaluate(cases, bars, sets=("S1", "S2", "S3", "S4")):
    """كلُّ حالةٍ في المجموعات المطلوبة ⟵ صفٌّ في المصفوفة · ثمّ المقاييس لكلّ مجموعةٍ/قسم."""
    rows = []
    lv_rows = {}
    for cs in cases:
        if cs.get("set") not in sets:
            continue
        tk = (cs.get("tickers") or [None])[0]
        res = run_case(cs, bars.get(tk) if tk else None)
        res.update(set=cs["set"], split=cs.get("split"), ticker=tk, faisal=cs.get("label4"), plan_F=cs.get("plan_F"),
                   statement_date=cs.get("statement_date"), basis=cs.get("basis"), best_tier=cs.get("best_tier"))
        rows.append(res)
        lv_rows[cs["case"]] = level_rows(cs, res)
    groups = {"S1_discovery": lambda r: r["set"] == "S1" and r["split"] == "discovery",
              "S1_holdout": lambda r: r["set"] == "S1" and r["split"] == "holdout",
              "S1_all": lambda r: r["set"] == "S1", "S2": lambda r: r["set"] == "S2",
              "S3_golden": lambda r: r["set"] == "S3", "S4_edu": lambda r: r["set"] == "S4"}
    metrics = {}
    for g, fn in groups.items():
        sel = [r for r in rows if fn(r)]
        ok = [r for r in sel if r["status"] == "OK"]
        lvl = [x for r in ok for x in lv_rows.get(r["case"], [])]
        lvl_text = [x for x in lvl if not x["derived"]]
        stat = boot_ci(lvl)
        metrics[g] = {
            "cases": len(sel), "ok": len(ok), "status_counts": _count(r["status"] for r in sel),
            "h_level": stat, "h_level_verdict": h_level_verdict(stat),
            "h_level_text_only": boot_ci(lvl_text),
            "h_class": h_class([(r["plan_F"], r["decisive_class"]) for r in ok]),
            "h_class_excl_none": h_class([(r["plan_F"], r["decisive_class"]) for r in ok if r["plan_F"] != "NONE"]),
            "h_state": h_state([(r["faisal"], r["state"]) for r in ok]),
            "h_tech": h_state([(r["faisal"], E.STATE_DECISION.get(r["tech_state"])) for r in ok]),
            "by_level_name": _by_name(lvl),
        }
    return {"rows": rows, "level_rows": lv_rows, "metrics": metrics}


def _count(it):
    d = {}
    for x in it:
        d[x] = d.get(x, 0) + 1
    return d


def _by_name(lvl):
    d = {}
    for r in lvl:
        for nm in r["matched_names"]:
            d[nm] = d.get(nm, 0) + 1
    return dict(sorted(d.items()))
