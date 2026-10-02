# -*- coding: utf-8 -*-
"""
🖼️ التحقّقُ البصريّ للأداة على حالات صور فيصل (§29) — يُشغَّل على Actions (TradingView).

المستوياتُ المتوقَّعة أدناه **مكتوبةٌ من الصور قبل أيّ تشغيلٍ للأداة على السوق** (2026-10-02):
كلُّ رقمٍ قرأتُه بعيني من الصورة المذكورة · والأداةُ لا ترى هذه الأرقام (تُقارَن بعد خروجها).

معاييرُ «الأداةُ تعيد قراءةَ فيصل» — مكتوبةٌ قبل الرقم ولا تُرخى بعده:
  M1 · تطابقُ المستويات: نسبةُ مستويات فيصل المرسومة التي يقع ضمن 2% منها (LEVEL_TOL_PCT · faisal_verbatim)
       مستوًى من مستويات الأداة (القاعان · العنق · نطاقُ القرار · الدخولان · الوقوف · الأهداف · قممُ وقيعانُ البنية).
       «يعيد القراءة» = 50% فأكثر في الحالة.
  M2 · حضورُ W: في الحالات التي سمّى فيها فيصل W (EZRA · VEEE · DXST) تكتشف الأداةُ W على اليوميّ **أو** 30 دقيقة.
  M3 · نطاقُ القرار (VEEE وحدَها): حدّا نطاق الأداة ضمن 2% من 6.18 و6.34.
  والحكمُ الإجماليّ: «يعيد القراءة» إن تحقّق M2 في الحالات الثلاث **و** M1 في نصف الحالات فأكثر.
  وإلّا يُكتب «لا يعيد القراءة» بأرقامه ولا يُضبط شيءٌ في الأداة بعده على هذه الحالات نفسِها (لا تفصيلَ على المثال).
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

CASES = [
    {"case": "EZRA", "img": "TG_58046", "asof": "2026-06-29", "faisal_says_w": True,
     "faisal_levels": [5.45, 5.433, 3.994, 3.430, 3.03, 5.40],
     "faisal_reading": "فراشةٌ متوقَّعة مع W · 5.40 خطورةُ السهم صعودًا أو هبوطًا"},
    {"case": "DXST", "img": "IMG_0627/IMG_0628 · TG_58048", "asof": "2026-06-15", "asof_30m_end": "2026-06-16 12:30",
     "faisal_says_w": True, "faisal_levels": [2.864, 3.114, 3.302, 3.61, 4.467, 2.539, 2.306, 2.28, 3.30, 2.455],
     "faisal_reading": "W على 30 دقيقة · العنق 2.86 وثباتٌ فوقه ربعَ ساعة · التحرّر من 3.11 يعطي 3.30"},
    {"case": "VEEE", "img": "TG_58045", "search": {"from": "2026-03-01", "to": "2026-07-31", "close": 6.76, "tol": 0.015,
                                                  "hi": 9.67, "lo": 5.00, "look": 60},
     "faisal_says_w": True, "faisal_levels": [6.18, 6.34, 5.34, 6.57, 7.27, 8.27, 8.76, 9.67, 5.00, 3.54],
     "band": [6.18, 6.34], "faisal_reading": "مقرون 6.18/6.34: أدناهما سلبيّ (M) وأعلاهما إيجابيّ (W)"},
    {"case": "ATMV", "img": "TG_58049", "search": {"from": "2025-06-01", "to": "2026-09-30", "close": 8.29, "tol": 0.015,
                                                  "hi": 22.20, "lo": None, "look": 120},
     "faisal_says_w": False, "faisal_levels": [22.20, 20.49, 18.48, 16.03, 14.36, 13.47, 9.92, 8.76, 6.71, 5.40, 6.70],
     "faisal_reading": "ترندٌ هابط 6.70 · الثباتُ والإقفالُ اليوميّ فوق 8.76 مهمّ · مقاومة 13.47 · لا شمعةَ تؤكّد الصعود"},
    {"case": "RAYA", "img": "X_20260827_raya_notready", "asof": "2026-08-26", "faisal_says_w": False,
     "faisal_levels": [4.908, 4.569, 3.998, 3.233, 2.617, 4.570],
     "faisal_reading": "غيرُ جاهزٍ فنيًّا · انتظار الهبوط"},
]


def tool_levels(rep):
    lv = []
    w = rep.get("w") or {}
    for k in ("low1", "low2", "neckline"):
        if w.get(k):
            lv.append(w[k])
    for e in rep.get("entries", []):
        lv.append(e["price"])
    for s in rep.get("stops", []):
        lv.append(s["price"])
    for t in rep.get("targets", []):
        lv.append(t["price"])
    db = rep.get("decision_band") or {}
    lv += [x for x in (db.get("low"), db.get("high")) if x]
    for s in rep.get("structure", []):
        lv.append(s["price"])
    w3 = (rep.get("w_30m") or {}).get("w") or {}
    for k in ("low1", "low2", "neckline"):
        if w3.get(k):
            lv.append(w3[k])
    return [float(x) for x in lv if x]


def agreement(faisal, tool, tol=0.02):
    hit = []
    for f in faisal:
        best = min(tool, key=lambda t: abs(t / f - 1)) if tool else None
        hit.append({"faisal": f, "nearest_tool": None if best is None else round(best, 4),
                    "diff_pct": None if best is None else round((best / f - 1) * 100, 2),
                    "within": bool(best is not None and abs(best / f - 1) <= tol)})
    n = sum(1 for x in hit if x["within"])
    return {"matched": n, "of": len(faisal), "share": round(n / len(faisal), 3) if faisal else None, "rows": hit}


def resolve_asof(df, spec):
    s = spec["search"]
    dates = [str(x)[:10] for x in df.index]
    c, h, lo = df["Close"].values, df["High"].values, df["Low"].values
    best = None
    for i, d in enumerate(dates):
        if not (s["from"] <= d <= s["to"]):
            continue
        if abs(c[i] / s["close"] - 1) > s["tol"]:
            continue
        j0 = max(0, i - s["look"])
        sc = abs(np.max(h[j0:i + 1]) / s["hi"] - 1)
        if s.get("lo"):
            sc += abs(np.min(lo[j0:i + 1]) / s["lo"] - 1)
        if best is None or sc < best[0]:
            best = (sc, d)
    return None if best is None else {"asof": best[1], "fit": round(best[0], 4)}


def main():
    sys.path.insert(0, os.path.dirname(HERE))
    sys.path.insert(0, HERE)
    import faisal_tool as T
    os.makedirs(OUT, exist_ok=True)
    res = []
    for spec in CASES:
        sym = spec["case"]
        try:
            df, full = T.fetch_daily(sym, n=900)
        except Exception as e:                                           # noqa: BLE001
            res.append({"case": sym, "error": f"جلب: {type(e).__name__}"})
            continue
        if df is None or len(df) < 40:
            res.append({"case": sym, "error": "لا شموع"})
            continue
        asof, fit = spec.get("asof"), None
        if "search" in spec:
            r = resolve_asof(df, spec)
            asof, fit = (r or {}).get("asof"), r
        if not asof:
            res.append({"case": sym, "error": "تعذّر تحديد تاريخ المنشور من الشموع", "search": spec.get("search")})
            continue
        try:
            m30 = T.fetch_30m(full, n=5000)
        except Exception:                                                # noqa: BLE001
            m30 = None
        if m30 is not None and spec.get("asof_30m_end"):
            m30 = m30[[str(x)[:16] <= spec["asof_30m_end"] for x in m30.index]]
        d = df[[str(x)[:10] <= asof for x in df.index]]
        ctx = T.production_context(sym, d)
        rep = T.analyze_df(df, asof=asof, m30_df=m30, context=ctx, symbol=sym)
        if spec.get("asof_30m_end") and m30 is not None:
            rep["w_30m"] = T.analyze_w_30m(m30, None)
        tl = tool_levels(rep)
        ag = agreement(spec["faisal_levels"], tl)
        w_any = bool(rep.get("w")) or bool((rep.get("w_30m") or {}).get("w"))
        out = {"case": sym, "img": spec["img"], "asof": asof, "asof_fit": fit, "faisal_reading": spec["faisal_reading"],
               "faisal_says_w": spec["faisal_says_w"], "tool_w_daily": bool(rep.get("w")),
               "tool_w_30m": bool((rep.get("w_30m") or {}).get("w")), "M1": ag, "M2": (w_any if spec["faisal_says_w"] else None),
               "tool_state": rep.get("state"), "tool_text": T.render_text(rep)}
        if spec.get("band"):
            db = rep.get("decision_band") or {}
            out["M3"] = {"tool_band": [db.get("low"), db.get("high")], "faisal_band": spec["band"],
                         "within": bool(db and abs(db["low"] / spec["band"][0] - 1) <= 0.02 and abs(db["high"] / spec["band"][1] - 1) <= 0.02)}
        png = os.path.join(OUT, f"case_{sym}.png")
        try:
            T.render_png(rep, d["Open"].values, d["High"].values, d["Low"].values, d["Close"].values, png)
            out["png"] = os.path.relpath(png, os.path.dirname(HERE))
        except Exception as e:                                           # noqa: BLE001
            out["png_error"] = type(e).__name__
        json.dump(rep, open(os.path.join(OUT, f"case_{sym}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
        res.append(out)
        print(f"── {sym} asof {asof} · W يوميّ {out['tool_w_daily']} · W 30د {out['tool_w_30m']} · "
              f"M1 {ag['matched']}/{ag['of']} · الحالة {(rep.get('state') or {}).get('state')}")
    for r in res:
        if r.get("error"):                                               # الحالةُ المتعذّرة تُعلَن لا تُسقَط صامتةً
            print(f"── {r['case']} ⛔ لم تُقَس: {r['error']} {json.dumps(r.get('search') or {}, ensure_ascii=False)}")
    w_cases = [r for r in res if r.get("faisal_says_w")]
    m2_ok = bool(w_cases) and all(r.get("M2") for r in w_cases) and len(w_cases) == 3
    m1_ok_n = sum(1 for r in res if r.get("M1") and r["M1"]["share"] is not None and r["M1"]["share"] >= 0.5)
    m1_ok = m1_ok_n * 2 >= len([r for r in res if r.get("M1")]) and m1_ok_n > 0
    verdict = "يعيد القراءة" if (m2_ok and m1_ok) else "لا يعيد القراءة"
    summ = {"verdict": verdict, "M2_all_w_cases": m2_ok, "M1_cases_ok": m1_ok_n,
            "M1_cases_measured": len([r for r in res if r.get("M1")]), "cases": res}
    json.dump(summ, open(os.path.join(OUT, "cases_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print(f"🏁 الحكم: {verdict} · M2 {m2_ok} · M1 {m1_ok_n}/{summ['M1_cases_measured']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
