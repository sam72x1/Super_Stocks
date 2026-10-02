# -*- coding: utf-8 -*-
"""
🧪 FAISAL V3.1 — الحالاتُ الذهبيّة مقابل العقد `V31_prereg.md` (قراءةٌ فقط · بلا شبكة · لا تلغرام · لا حالةَ إنتاج).

    python3 faisal_method_v3/v31_cases.py DATA.json     ⟵ faisal_method_v3/v31/golden_cases_v31.json

DATA.json = حمولةُ وضع `dump` بعد فكّها (`case_dump.unpack`) — شموعُ TradingView كما طُبعت في سجلّ التشغيلة.
كلُّ ما هنا مكتوبٌ **بعد** دمج العقد (#545) و**كما نصّ**: تواريخُ §③ · القاعدتان المرشّحتان C1/C2 وسؤالُ البيانات C3 (§②) ·
معاييرُ القبول A1-A4 (§④) · التنبّؤاتُ P1-P5 (§⑤). **لا بارامتر يُضبط هنا** — قيمُ V3 في `faisal_tool.PARAMS` كما هي.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))          # hs_forensic (render_bars) في جذر المستودع
sys.path.insert(0, HERE)
import faisal_tool as T                                                    # noqa: E402

READY = {"AT_SUPPORT2", "BREAKOUT", "RETEST_HOLD"}
WAIT = {"NO_W", "UNSAFE_MIDDLE", "SUB_SUPPORT_WAIT", "INVALIDATED", "FAILED_BREAKOUT"}
CYCLE_BARS = 2 * T.P("W_BARS_MAX")                     # 120 · `engineering` — ضعفُ أقصى امتداد W في V3 (§② C1 · مُعلَن قبل الرقم)
FAISAL = {"RAYA": "WAIT", "LABT": "WAIT", "ZNB": "WAIT", "RUBI": "WAIT", "AMIX": "READY", "HCWB": "READY",
          "DXST": "WAIT", "VEEE": "WAIT", "ATMV": "WAIT"}


# ── §③ التواريخ ─────────────────────────────────────────────────────────────────────
def _arr(rows):
    return ([r[0] for r in rows], np.array([r[1] for r in rows], float), np.array([r[2] for r in rows], float),
            np.array([r[3] for r in rows], float), np.array([r[4] for r in rows], float))


def resolve_dates(D):
    """تواريخُ §③ حرفًا. ⟵ {الحالة: {"asof": تاريخ أو None, "how": ..., "candidates": [...]}}"""
    out = {}

    def near_close(sym, upto, close, tol=0.01):
        d, o, h, l, c = _arr(D[sym]["daily"])
        cand = [d[i] for i in range(len(d)) if d[i] <= upto and abs(c[i] / close - 1) <= tol]
        return cand
    for sym, upto, cl in (("RAYA", "2026-08-27", 2.35),):
        cand = near_close(sym, upto, cl)
        out[sym] = {"asof": cand[-1] if cand else None, "how": f"أقربُ جلسةٍ ≤ {upto} إغلاقُها {cl} ±1%", "candidates": cand[-5:]}
    for sym, day, cl in (("LABT", "2026-08-21", 2.24), ("ZNB", "2026-07-31", 2.38)):
        d, o, h, l, c = _arr(D[sym]["daily"])
        ok = day in d and abs(c[d.index(day)] / cl - 1) <= 0.01
        out[sym] = {"asof": day if ok else None, "how": f"{day} وإغلاقُها {cl} ±1%",
                    "close": float(c[d.index(day)]) if day in d else None}
    d, o, h, l, c = _arr(D["RUBI"]["daily"])
    cand = [d[i] for i in range(len(d)) if all(abs(x / y - 1) <= 0.005 for x, y in ((o[i], 1.870), (h[i], 1.877), (l[i], 1.740), (c[i], 1.760)))]
    out["RUBI"] = {"asof": cand[0] if len(cand) == 1 else None, "how": "الشمعة O 1.870 · H 1.877 · L 1.740 · C 1.760 ±0.5%", "candidates": cand}
    d, o, h, l, c = _arr(D["AMIX"]["daily"])
    cand = [d[i] for i in range(len(d)) if d[i] <= "2026-08-27" and abs(c[i] / 5.27 - 1) <= 0.01
            and abs(np.max(h[max(0, i - 60):i + 1]) / 24.68 - 1) <= 0.02]
    out["AMIX"] = {"asof": cand[-1] if cand else None, "how": "آخرُ جلسةٍ ≤ 2026-08-27 إغلاقُها 5.27 ±1% وقمّةُ الستّين 24.68 ±2%", "candidates": cand}
    out["HCWB"] = {"asof": out["AMIX"]["asof"], "how": "تاريخُ AMIX نفسُه (الرسالةُ نفسُها)"}
    out["DXST"] = {"asof": "2026-06-15", "asof_30m_end": "2026-06-16 12:30", "how": "منشور 2026/6/16 · 30 دقيقة حتى 12:30 نيويورك"}
    d, o, h, l, c = _arr(D["VEEE"]["daily"])
    cand = [d[i] for i in range(len(d)) if abs(c[i] / 6.76 - 1) <= 0.01
            and abs(np.max(h[max(0, i - 60):i + 1]) / 9.67 - 1) <= 0.02 and abs(np.min(l[max(0, i - 60):i + 1]) / 5.00 - 1) <= 0.02]
    out["VEEE"] = {"asof": cand[0] if len(cand) == 1 else None,
                   "how": "جلسةٌ إغلاقُها 6.76 ±1% وفي الستّين قبلها قمّةٌ 9.67 ±2% وقاعٌ 5.00 ±2% · وإن تعدّدت فلا تاريخ",
                   "candidates": cand, "status": "UNKNOWN" if len(cand) != 1 else "OK"}
    if D.get("ATMV", {}).get("daily"):
        d, o, h, l, c = _arr(D["ATMV"]["daily"])
        cand = [d[i] for i in range(len(d)) if abs(c[i] / 8.29 - 1) <= 0.01 and abs(np.max(h[max(0, i - 120):i + 1]) / 22.20 - 1) <= 0.02]
        out["ATMV"] = {"asof": cand[-1] if cand else None, "how": "آخرُ جلسةٍ إغلاقُها 8.29 ±1% وقمّةُ 120 قبلها 22.20 ±2%", "candidates": cand}
    else:
        out["ATMV"] = {"asof": None, "how": "لا شموع", "status": "DATA_UNAVAILABLE", "tries": D.get("ATMV", {}).get("tries")}
    return out


# ── §② القاعدتان المرشّحتان ──────────────────────────────────────────────────────────
def find_w_span(o, h, l, c, asof, k=None, sw=None):
    """C2 (R-W-SPAN) — منفَّذةٌ في الأداة V3.1 (`find_w(span_rule=True)`) · وهذا اسمٌ لها هنا."""
    return T.find_w(o, h, l, c, asof, k, sw=sw, span_rule=True)


def main_support(h, l, asof, bars=CYCLE_BARS):
    """C1: MS من الأداة V3.1 (`T.main_support`) ⟵ (MS · فهرسُ القمّة)."""
    ms, ip, _ = T.main_support(h, l, asof, bars)
    return ms, ip


def state_v31(o, h, l, c, asof, use_c1=True, use_c2=True):
    """حالةُ V3.1 المرشَّحة: W بـC2 (إن فُعّل) ثمّ w_state V3 حرفًا ثمّ C1 على AT_SUPPORT2 وحدَها."""
    w = find_w_span(o, h, l, c, asof) if use_c2 else T.find_w(o, h, l, c, asof, span_rule=False)
    if w is None:
        return {"state": "NO_W", "w": None}
    st = T.w_state(o, h, l, c, w, asof)
    out = {"state": st["state"], "w": w, "v3_state": st["state"]}
    if use_c1 and st["state"] == "AT_SUPPORT2":
        ms, ip = main_support(h, l, asof)
        out["main_support"] = round(ms, 4)
        out["low2_over_ms_pct"] = round((w["low2"] / ms - 1) * 100, 2)
        if w["low2"] > ms * (1 + T.P("LOW2_SWEEP_MIN_PCT") / 100):
            out["state"] = "SUB_SUPPORT_WAIT"
    return out


def label(state):
    return "READY" if state in READY else ("WAIT" if state in WAIT else None)


# ── §② C3 · DXST على 30 دقيقة ───────────────────────────────────────────────────────
FAISAL_DXST = {"low1": 2.40, "neck": 2.864, "low2": 2.55}       # مقروءةٌ من IMG_0627 (approx للقاعين · العنقُ مكتوب)


def dxst_30m(rows, end="2026-06-16 12:30", k=None, span_rule=False):
    """C3 بكاشف V3 (`span_rule=False` · السؤالُ المسجَّل) أو V3.1 (`True`) — كلاهما يُطبع."""
    rr = [r for r in rows if r[0] <= end]
    if len(rr) < 40:
        return {"bars": len(rr), "w": None}
    d, o, h, l, c = _arr(rr)
    k = T.P("SWING_K_30M") if k is None else k
    w = T.find_w(o, h, l, c, len(c) - 1, k, span_rule=span_rule)
    res = {"bars": len(rr), "first": d[0], "last": d[-1], "w": None}
    if w:
        res["w"] = {"t1": d[w["i1"]], "low1": w["low1"], "tneck": d[w["ineck"]], "neckline": w["neckline"],
                    "t2": d[w["i2"]], "low2": w["low2"]}
        res["state"] = T.w_state(o, h, l, c, w, len(c) - 1)["state"]
        res["match"] = {k2: round((res["w"][k1] / FAISAL_DXST[k2] - 1) * 100, 2)
                        for k1, k2 in (("low1", "low1"), ("neckline", "neck"), ("low2", "low2"))}
        res["within_2pct"] = all(abs(v) <= 2.0 for v in res["match"].values())
    # هل يوجد في الشموع قاعٌ ‏≈2.40 ثمّ قمّةٌ ‏≈2.864 ثمّ قاعٌ ‏≈2.55 (بلا شرط المحور)؟ — وصفٌ لا قاعدة
    lo1 = [(d[i], l[i]) for i in range(len(l)) if abs(l[i] / 2.40 - 1) <= 0.02]
    nk = [(d[i], h[i]) for i in range(len(h)) if abs(h[i] / 2.864 - 1) <= 0.005]
    res["raw_presence"] = {"lows_near_2.40": lo1[-3:], "highs_near_2.864": nk[-5:]}
    return res


def evaluate(D):
    dates = resolve_dates(D)
    rows = []
    for case, fz in FAISAL.items():
        info = dates.get(case) or {}
        asof = info.get("asof")
        rec = {"case": case, "faisal": fz, "asof": asof, "date_rule": info.get("how"), "date_status": info.get("status", "OK" if asof else "NO_DATE")}
        if not asof or not D.get(case, {}).get("daily"):
            rows.append(rec)
            continue
        d, o, h, l, c = _arr(D[case]["daily"])
        a = max(i for i in range(len(d)) if d[i] <= asof)
        rec["close"] = float(c[a])
        w3 = T.find_w(o, h, l, c, a, span_rule=False)                    # V3 حرفًا (القاعدةُ قبل V3.1)
        v3s = T.w_state(o, h, l, c, w3, a)["state"] if w3 else "NO_W"
        rec["v3"] = {"state": v3s, "label": label(v3s), "w": {k: w3[k] for k in ("low1", "low2", "neckline")} if w3 else None}
        rep = T.analyze_arrays(o, h, l, c, d, a, symbol=case)                # الأداة V3.1 كما تُشحن (C2 نشطة · C1 معلومة)
        t31 = (rep.get("state") or {}).get("state")
        rec["tool_v31"] = {"state": t31, "label": label(t31), "main_support": rep.get("main_support"),
                           "w": {k: rep["w"][k] for k in ("low1", "low2", "neckline")} if rep.get("w") else None}
        for name, c1, c2 in (("C1", True, False), ("C2", False, True), ("C1+C2", True, True)):
            s = state_v31(o, h, l, c, a, use_c1=c1, use_c2=c2)
            rec[name] = {"state": s["state"], "label": label(s["state"]),
                         "w": {k: s["w"][k] for k in ("low1", "low2", "neckline")} if s.get("w") else None,
                         **{k: s[k] for k in ("main_support", "low2_over_ms_pct") if k in s}}
        # C2/P1: أدنى ما بين قاعَي W V3
        if w3:
            rec["v3_w_span_min_low"] = float(np.min(l[w3["i1"]:w3["i2"] + 1]))
            rec["v3_w_dates"] = [d[w3["i1"]], d[w3["ineck"]], d[w3["i2"]]]
        rows.append(rec)
    agree = {}
    for arm in ("v3", "C1", "C2", "C1+C2", "tool_v31"):
        m = [r for r in rows if r.get(arm)]
        agree[arm] = {"matched": sum(1 for r in m if r[arm]["label"] == r["faisal"]), "of": len(m),
                      "ready_flipped": [r["case"] for r in m if r["faisal"] == "READY" and r[arm]["label"] != "READY"]}
    return {"dates": dates, "rows": rows, "agreement": agree}


FIXTURE_DAILY_BEFORE = 300          # شموعٌ قبل asof في ملفّ الحالات الذهبيّة (تكفي المحاورَ ونافذةَ 120 · مُتحقَّقٌ بالتطابق أدناه)
FIXTURE_DAILY_AFTER = 10            # وبعده — لقفل «لا نظرَ للأمام» (النتيجةُ عند asof لا تتغيّر بوجودها)
FIXTURE_M30 = 400                   # شموعُ 30 دقيقة قبل نهاية DXST (النظاميّة والممتدّة)
FIXTURE_EXTRA = {"RAYA": ["2026-08-26"]}   # تاريخُ V3 لـRAYA (تناقضُ V3 المنشور) — يُقفَل أيضًا


def build_fixtures(D, dates):
    """ملفُّ الحالات الذهبيّة (V3.1 §21): نوافذُ الشموع التي تكفي لإعادة كلّ حكمٍ هنا بلا شبكة."""
    fx = {"meta": {"source": "TradingView عبر وضع dump (case_dump.py) — تشغيلة 37036590477 على main 760996255",
                   "daily_before": FIXTURE_DAILY_BEFORE, "daily_after": FIXTURE_DAILY_AFTER, "m30": FIXTURE_M30},
          "daily": {}, "m30": {}, "m30x": {}, "dates": {}}
    for case, info in dates.items():
        fx["dates"][case] = {k: info.get(k) for k in ("asof", "status", "how")}
        rows = (D.get(case) or {}).get("daily") or []
        if case == "VEEE":                                   # «لا تاريخ» يلزمه التاريخُ كلُّه
            fx["daily"][case] = rows
            continue
        if not info.get("asof") or not rows:
            continue
        ends = [info["asof"]] + FIXTURE_EXTRA.get(case, [])
        a0 = min(max(i for i, r in enumerate(rows) if r[0] <= e) for e in ends)
        a1 = max(max(i for i, r in enumerate(rows) if r[0] <= e) for e in ends)
        lo = 0 if case in ("RAYA", "AMIX") else max(0, a0 - FIXTURE_DAILY_BEFORE)   # قاعدتا تاريخَيهما تمسحان ما قبلهما
        fx["daily"][case] = rows[lo:a1 + FIXTURE_DAILY_AFTER + 1]
    for key in ("m30", "m30x"):
        rr = [r for r in (D["DXST"].get(key) or []) if r[0] <= "2026-06-16 12:30"]
        fx[key]["DXST"] = rr[-FIXTURE_M30:]
    return fx


def render_overlays(fx, outdir=None):
    """§20: طبقاتٌ بصريّة للحالات الذهبيّة من الملفّ نفسِه (بلا شبكة) — الأداة V3.1 كما تُشحن: W (L1 · L2 · العنق) ·
    الدخولان · الوقف · الأهداف · الدعمُ الأساسيّ (MS · معلومة) · ولـDXST طبقتا 30 دقيقة النظاميّة والممتدّة. ⟵ قائمةُ الملفّات."""
    import hs_forensic as FX
    outdir = outdir or os.path.join(HERE, "v31", "overlays")
    os.makedirs(outdir, exist_ok=True)
    made = []
    for case, info in sorted(fx["dates"].items()):
        rows = fx["daily"].get(case)
        ends = ([info["asof"]] if info.get("asof") else []) + (FIXTURE_EXTRA.get(case, []) if info.get("asof") else [])
        for end in ends:
            d, o, h, l, c = _arr([r for r in rows if r[0] <= end])
            rep = T.analyze_arrays(o, h, l, c, d, len(c) - 1, symbol=case)
            pth = os.path.join(outdir, f"{case}_{end}_daily.png")
            T.render_png(rep, o, h, l, c, pth)
            made.append(os.path.relpath(pth, HERE))
    for key in ("m30", "m30x"):
        rr = fx[key].get("DXST") or []
        d, o, h, l, c = _arr(rr)
        w = T.find_w(o, h, l, c, len(c) - 1, T.P("SWING_K_30M"))
        marks, lines = {}, {"faisal_neck_2.864": (2.864, 0)}
        s0 = max(0, len(c) - 150)
        if w:
            marks = {"L1": (w["i1"] - s0, w["low1"]), "L2": (w["i2"] - s0, w["low2"]), "NECK": (w["ineck"] - s0, w["neckline"])}
            lines["tool_neck"] = (w["neckline"], max(0, w["i1"] - s0))
        pth = os.path.join(outdir, f"DXST_2026-06-16_{'regular' if key == 'm30' else 'extended'}_30m.png")
        FX.render_bars([[o[i], h[i], l[i], c[i]] for i in range(s0, len(c))], pth, marks=marks, lines=lines,
                       title=f"DXST 30m {'regular' if key == 'm30' else 'extended'} to 2026-06-16 12:30 · V3.1")
        made.append(os.path.relpath(pth, HERE))
    return made


def main(path):
    D = json.load(open(path, encoding="utf-8"))
    res = evaluate(D)
    res["dxst_30m"] = {"regular": dxst_30m(D["DXST"].get("m30") or []), "extended": dxst_30m(D["DXST"].get("m30x") or []),
                       "regular_v31": dxst_30m(D["DXST"].get("m30") or [], span_rule=True),
                       "extended_v31": dxst_30m(D["DXST"].get("m30x") or [], span_rule=True)}
    res["c3_accepted"] = bool(res["dxst_30m"]["extended"].get("within_2pct")) and not res["dxst_30m"]["regular"].get("within_2pct")
    r26 = {}
    d, o, h, l, c = _arr(D["RAYA"]["daily"])
    a = max(i for i in range(len(d)) if d[i] <= "2026-08-26")
    w3 = T.find_w(o, h, l, c, a, span_rule=False)
    r26["v3"] = {"state": T.w_state(o, h, l, c, w3, a)["state"], "w": [d[w3["i1"]], w3["low1"], d[w3["i2"]], w3["low2"], w3["neckline"]],
                 "span_min_low": float(np.min(l[w3["i1"]:w3["i2"] + 1]))}
    rep = T.analyze_arrays(o, h, l, c, d, a, symbol="RAYA")
    r26["tool_v31"] = {"state": rep["state"]["state"], "main_support": rep["main_support"]}
    res["raya_v3_date"] = r26
    out = os.path.join(HERE, "v31", "golden_cases_v31.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    fx = build_fixtures(D, res["dates"])
    json.dump(fx, open(os.path.join(HERE, "v31", "golden_fixtures.json"), "w", encoding="utf-8"), ensure_ascii=False,
              separators=(",", ":"))
    # الملفُّ يكفي: إعادةُ الحساب من نوافذه = الحسابُ من التفريغ الكامل (وإلّا فالقفلُ يحرس شيئًا غيرَ المنشور)
    D2 = {k: {"daily": fx["daily"].get(k) or [], "m30": fx["m30"].get(k) or [], "m30x": fx["m30x"].get(k) or []} for k in D}
    D2["ATMV"] = {"daily": [], "tries": D.get("ATMV", {}).get("tries")}
    re2 = evaluate(D2)
    same = all(json.dumps(x, sort_keys=True, default=str) == json.dumps(y, sort_keys=True, default=str)
               for x, y in zip(res["rows"], re2["rows"]))
    print("🧪 الملفُّ يعيد الحكمَ نفسَه:", same, "· الحجم", os.path.getsize(os.path.join(HERE, "v31", "golden_fixtures.json")))
    print("🖼️ الطبقات:", render_overlays(fx))
    for r in res["rows"]:
        print(r["case"], r["faisal"], r["asof"], r.get("date_status"), "| V3", (r.get("v3") or {}).get("state"),
              "| C1", (r.get("C1") or {}).get("state"), "| C2", (r.get("C2") or {}).get("state"),
              "| C1+C2", (r.get("C1+C2") or {}).get("state"))
    print(json.dumps(res["agreement"], ensure_ascii=False))
    print(json.dumps(res["dxst_30m"], ensure_ascii=False)[:1500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
