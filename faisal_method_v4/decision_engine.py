# -*- coding: utf-8 -*-
"""
🧭 FAISAL V4 — محرّكُ القرار (READY · WAIT · REJECT · UNKNOWN) بكائنٍ قابلٍ للتفسير (§31-32).

البنية (§30) — كلُّ طبقةٍ دالّةٌ مستقلّة بلا عرضٍ ولا تلغرام:
  البيانات ⟵ جودةُ البيانات ⟵ البنية (القاع · الثبات · صعودُ الاختبار) ⟵ النموذج (W من V3.1 معلومةً)
  ⟵ الدعم/المقاومة ⟵ موقعُ السعر ⟵ التأكيد (ثباتٌ في المنطقة · سحبٌ ثمّ عودة) ⟵ الدخول ⟵ الإبطال ⟵ الأهداف
  ⟵ الصلاحيّة (قروبات · طرح · شورت — سياقٌ اختياريّ) ⟵ القرار ⟵ التفسير.

⚖️ مبادئ لا تُكسر:
  • **لا نظرَ للأمام:** المحرّكُ يقصّ المصفوفاتِ عند asof قبل أيّ حساب (`_slice`) — وقفلُ «إلحاقُ المستقبل لا يغيّر المخرَج» في السويّة.
  • **كلُّ عتبةٍ بوسم مصدرها** (`PARAMS`) · وكلُّ قاعدةٍ في `rules_v4.RULES_V4` بمصدرها وقراريّتها.
  • **ما لا يُرى يُقال إنّه لا يُرى:** بصمةُ المضارب والقروباتُ والطرحُ والشورتُ لا تظهر في الشموع ⟵ الجاهزيّةُ الفنيّةُ بلا
    هذه المعلومات تُخرج UNKNOWN (ومعها «ما الناقص») لا READY مختلَقًا (§32 · «UNKNOWN > FABRICATED CERTAINTY»).
  • **الصلاحيّةُ لا ترقّي أبدًا:** قروبات ⟵ REJECT · طرحٌ/شورتٌ عالٍ ⟵ WAIT · ولا شيءَ منها يحوّل WAIT إلى READY.
  • أداةُ بحثٍ وعرضٍ عند الطلب: لا تكتب حالةَ إنتاج ولا ترسل تلغرام (§37).
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "faisal_method_v3"))

import faisal_tool as V31          # noqa: E402 — V3.1 محفوظةٌ كما هي ويُعاد استعمالُ دوالّها النقيّة
import rules_v4 as RV              # noqa: E402

ENGINE_VERSION = "FAISAL-V4 1.0 (2026-10-02)"

# (القيمة · المصدر · السند) — §27: لا رقمَ بلا وسم
PARAMS = {
    "MIN_BARS": (40, "engineering", "R4-DATA-01: أقلُّ من 40 جلسة ⟵ UNKNOWN"),
    "CYCLE_BARS": (120, "production", "R-SUP-MAIN (V3.1 · V31_prereg §②): نافذةُ قمّة الدورة 2 × W_BARS_MAX"),
    "HOLD_MIN": (5, "faisal_verbatim", "R4-HOLD-01: «اذا ماكسر القاع اكثر من 5 جلسات» (X_20260918_85_YMT)"),
    "RISE_TEST_PCT": (15.0, "faisal_inferred", "R4-CYC-01: المدى 10-50 · الغالب 20 · المقبول 17 (IMG_0488)"),
    "ZONE_PCT": (15.0, "faisal_verbatim", "R4-ZONE-01: «طلبات 5-15٪ فوق القاع» (IMG_0531)"),
    "BID_LO_PCT": (5.0, "faisal_verbatim", "R4-ZONE-01: الحدُّ الأدنى للطلبات فوق القاع (IMG_0531)"),
    "HOLD_ZONE": (3, "faisal_inferred", "R4-HOLDZ-01: المدى 2-5 (CLIR «جلستين او 3» · STKH «5»)"),
    "SWEEP_MAX_PCT": (13.0, "faisal_tier2b", "R4-SWEEP-01: IMG_0297 (EDU) «7٪ ل 13٪» · ومدى الطبقة 1 حتى 15"),
    "SWEEP_PROJ_PCT": ((5.0, 10.0), "faisal_verbatim", "R4-SWEEP-01: «5٪ تحت أدنى شمعة القاع» (TG_50584) · «10٪» (IMG_0177)"),
    "RECLAIM_BARS": (2, "engineering", "R4-SWEEP-01: العودةُ فوق القاع السابق خلال جلستين («الضغط قبل الصعود بيوم» IMG_0531)"),
    "AT_BAND_PCT": (3.0, "production", "DECISION_BAND_PCT (V3.1): «عند» = ضمن 3%"),
    "LEVEL_TOL_PCT": (2.0, "faisal_verbatim", "«دقة الخطأ لاتتجاوز 2٪» — حدُّ القاع المزدوج ومطابقةُ المستويات"),
    "SHORT_AVAIL_MAX": (20000, "faisal_verbatim", "R4-VAL-SHORT-01: «تابعه لين يبقى الشورت تحت 20 الف» (IMG_0150)"),
    "SWING_K": (3, "engineering", "عرضُ المحور اليوميّ (V3.1)"),
}


def P(name, params=None):
    if params and name in params:
        return params[name]
    return PARAMS[name][0]


STATE_DECISION = {          # الحالةُ الفنيّة ⟵ القرارُ قبل الصلاحيّة
    "DATA_INSUFFICIENT": "UNKNOWN", "BASE_FORMING": "WAIT", "BROKEN_NEW_BASE": "WAIT", "SWEEP_ACTIVE": "WAIT",
    "RETEST_PENDING": "WAIT", "RETEST_IN_PROGRESS": "WAIT",
    "PRESS_RECLAIM": "TECH_READY", "RETEST_HELD": "TECH_READY", "BASE_HELD": "TECH_READY",
}
STATE_RULE = {"DATA_INSUFFICIENT": "R4-DATA-01", "BASE_FORMING": "R4-HOLD-01", "BROKEN_NEW_BASE": "R4-INV-01",
              "SWEEP_ACTIVE": "R4-SWEEP-01", "RETEST_PENDING": "R4-LOC-01", "RETEST_IN_PROGRESS": "R4-HOLDZ-01",
              "PRESS_RECLAIM": "R4-SWEEP-01", "RETEST_HELD": "R4-HOLDZ-01", "BASE_HELD": "R4-HOLD-01"}
STATE_AR = {
    "DATA_INSUFFICIENT": "بياناتٌ غيرُ كافية", "BASE_FORMING": "القاعُ لم يثبت 5 جلسات بعد",
    "BROKEN_NEW_BASE": "كُسر القاعُ السابق بأبعد من مدى السحب — تحليلٌ جديدٌ من القاع الجديد",
    "SWEEP_ACTIVE": "سحبُ سيولةٍ تحت القاع السابق ولم يعد فوقه بعد",
    "RETEST_PENDING": "صعد للاختبار والسعرُ فوق المنطقة — انتظارُ الرجوع لاختبار الدعم",
    "RETEST_IN_PROGRESS": "رجع إلى المنطقة ولم يثبت فيها جلساتٍ كافية",
    "PRESS_RECLAIM": "سحبُ سيولةٍ ثمّ عودةٌ فوق القاع السابق (ضغطٌ مكتمل)",
    "RETEST_HELD": "اختبر الدعم وثبت في المنطقة", "BASE_HELD": "قاعٌ ثابتٌ والسعرُ في المنطقة بلا صعود اختبارٍ بعد",
}


def _slice(arrs, asof):
    return [np.asarray(a[:asof + 1], float) for a in arrs]


def _cls(level, close, params=None):
    """موقعُ مستوًى من السعر: AT (ضمن AT_BAND) · BELOW · ABOVE."""
    if level is None or close is None or level <= 0 or close <= 0:
        return None
    b = math.log(1 + P("AT_BAND_PCT", params) / 100)
    d = math.log(level / close)
    return "AT" if abs(d) <= b else ("BELOW" if d < 0 else "ABOVE")


def structure(o, h, l, c, params=None):
    """البنية على مصفوفاتٍ مقصوصة عند asof (آخرُ عنصر = asof) — بلا نظرٍ للأمام بالبناء."""
    n = len(c)
    asof = n - 1
    k = P("SWING_K", params)
    sw = V31.confirmed_swings(h, l, asof, k)
    bars = P("CYCLE_BARS", params)
    j0 = max(0, asof - bars)
    i_c = j0 + int(np.argmax(h[j0:asof + 1]))                       # قمّةُ الدورة
    i_b = i_c + int(np.argmin(l[i_c:asof + 1]))                     # القاع = أدنى ذيلٍ منذها (R4-BOT-01)
    B = float(l[i_b])
    tol = P("LEVEL_TOL_PCT", params) / 100
    prev = None                                                     # قاعٌ سابقٌ «راسخ»: قاعٌ محوريٌّ ثبت HOLD_MIN جلساتٍ قبل أن يُكسر
    hm = P("HOLD_MIN", params)
    for jp, tp, pp in reversed(sw):
        if tp != "L" or not (i_c <= jp <= i_b - hm):
            continue
        seg = l[jp + 1:jp + 1 + hm]
        if len(seg) == hm and float(np.min(seg)) >= pp * (1 - tol):
            prev = {"i": int(jp), "price": float(pp)}
            break
    out = {"asof_i": asof, "cycle_high": {"i": int(i_c), "price": float(h[i_c])},
           "bottom": {"i": int(i_b), "price": B, "body_low": float(min(o[i_b], c[i_b]))},
           "prior_base": prev, "swings": sw, "close": float(c[asof])}
    # قاعٌ مزدوج: القاعُ الجديد ضمن 2% من السابق ⟵ الثباتُ يُحسب من الأوّل
    hold_from = i_b
    depth = None
    if prev and prev["price"] > 0:
        depth = 1 - B / prev["price"]
        if depth <= tol:
            hold_from = prev["i"]
    out["undercut_pct"] = None if depth is None else round(depth * 100, 3)
    out["hold_sessions"] = int(asof - hold_from)
    hi_after = float(np.max(h[i_b + 1:asof + 1])) if i_b < asof else B
    i_h = (i_b + 1 + int(np.argmax(h[i_b + 1:asof + 1]))) if i_b < asof else i_b
    out["test_high"] = {"i": int(i_h), "price": hi_after, "rise_pct": round((hi_after / B - 1) * 100, 3) if B > 0 else None}
    s2 = [p for i, t, p in sw if t == "L" and i > i_b and p > B * (1 + tol)]
    out["support2"] = float(s2[-1]) if s2 else None
    ladder = V31.resistance_ladder(h, sw, float(c[asof]), asof)
    out["ladder"] = [float(x) for x in ladder]
    out["labels"] = V31.label_structure(sw)[-6:]
    return out


def tech_state(o, h, l, c, st, params=None):
    """الحالةُ الفنيّة ومستواها الحاسم — الترتيبُ نفسُه في V4_prereg §④."""
    asof = st["asof_i"]
    B = st["bottom"]["price"]
    i_b = st["bottom"]["i"]
    close = st["close"]
    zone_hi = B * (1 + P("ZONE_PCT", params) / 100)
    tol = P("LEVEL_TOL_PCT", params) / 100
    prev = st["prior_base"]
    depth = (st["undercut_pct"] or 0) / 100
    since_b = asof - i_b
    if prev and depth > tol and since_b < P("HOLD_MIN", params):
        if depth > P("SWEEP_MAX_PCT", params) / 100:
            return "BROKEN_NEW_BASE", B, {"depth_pct": round(depth * 100, 2)}
        pv = prev["price"]
        rec = [i for i in range(i_b, min(asof, i_b + P("RECLAIM_BARS", params)) + 1) if c[i] >= pv * (1 - tol)]
        if rec:
            return "PRESS_RECLAIM", pv, {"depth_pct": round(depth * 100, 2), "reclaim_i": int(rec[0])}
        if since_b <= P("RECLAIM_BARS", params):
            return "SWEEP_ACTIVE", pv, {"depth_pct": round(depth * 100, 2)}
    if st["hold_sessions"] < P("HOLD_MIN", params):
        return "BASE_FORMING", B, {}
    rise = st["test_high"]["rise_pct"] or 0
    if rise < P("RISE_TEST_PCT", params):
        return "BASE_HELD", B * (1 + P("BID_LO_PCT", params) / 100), {"zone": [B, zone_hi]}
    if close > zone_hi:
        sup = [x for x in (st["support2"], st["bottom"]["body_low"], B) if x is not None and x < close]
        return "RETEST_PENDING", (max(sup) if sup else B), {"zone": [B, zone_hi]}
    n_in = 0
    for i in range(asof, st["test_high"]["i"], -1):
        if c[i] <= zone_hi and l[i] >= B * (1 - tol):
            n_in += 1
        else:
            break
    if n_in >= P("HOLD_ZONE", params):
        return "RETEST_HELD", close, {"zone": [B, zone_hi], "sessions_in_zone": n_in}
    return "RETEST_IN_PROGRESS", close, {"zone": [B, zone_hi], "sessions_in_zone": n_in}


def validity(context, params=None):
    """الصلاحيّة من سياقٍ اختياريّ: groups · offering_pending · short_available. ⟵ (حكم · أسباب · ناقص)."""
    ctx = context or {}
    blocks, missing = [], []
    g = ctx.get("groups")
    if g is True:
        blocks.append(("REJECT", "R4-VAL-GRP-01", "قروباتٌ داخلة — قراءةُ الشموع باطلة"))
    elif g is None:
        missing.append("القروبات (R4-VAL-GRP-01)")
    off = ctx.get("offering_pending")
    if off is True:
        blocks.append(("WAIT", "R4-VAL-OFF-01", "طرحٌ/تخفيفٌ معلَّق"))
    elif off is None:
        missing.append("الطرح/التخفيف (R4-VAL-OFF-01)")
    sh = ctx.get("short_available")
    if isinstance(sh, (int, float)) and sh > P("SHORT_AVAIL_MAX", params):
        blocks.append(("WAIT", "R4-VAL-SHORT-01", f"المتاحُ للشورت {int(sh):,} فوق 20,000"))
    elif sh is None:
        missing.append("المتاح للشورت (R4-VAL-SHORT-01)")
    op = ctx.get("operator_press")
    if op is None:
        missing.append("بصمة المضارب/الضغط (R4-OP-01)")
    return blocks, missing


def level_set(st, params=None):
    """مستوياتُ المحرّك القابلة للمقارنة بمستويات فيصل النصّيّة (V4_prereg §⑤ H-LEVEL) — مرتّبةٌ بأسمائها."""
    B = st["bottom"]["price"]
    out = {"bottom": B, "bottom_body": st["bottom"]["body_low"], "test_high": st["test_high"]["price"]}
    if st["support2"]:
        out["support2"] = st["support2"]
    if st["ladder"]:
        out["resistance1"] = st["ladder"][0]
    if st["prior_base"]:
        out["prior_base"] = st["prior_base"]["price"]
    for p in P("SWEEP_PROJ_PCT", params):
        out[f"sweep_{int(p)}"] = B * (1 - p / 100)
    out["bid_lo"] = B * (1 + P("BID_LO_PCT", params) / 100)
    out["zone_hi"] = B * (1 + P("ZONE_PCT", params) / 100)
    return {k: round(float(v), 6) for k, v in out.items() if v and v > 0}


def analyze(o, h, l, c, dates, asof=None, context=None, symbol="", params=None, v=None):
    """القلبُ النقيّ: مصفوفاتٌ يوميّة ⟵ كائنُ القرار (§31). `asof` فهرسٌ أو None (آخر جلسة)."""
    n = len(c)
    asof = n - 1 if asof is None else int(asof)
    o, h, l, c = _slice((o, h, l, c), asof)
    vol = None if v is None else np.asarray(v[:asof + 1], float)
    dobj = {"engine": ENGINE_VERSION, "rules_version": RV.VERSION, "symbol": symbol, "timeframe": "1D",
            "asof": str(dates[asof])[:10] if dates is not None and len(dates) > asof else None,
            "params": {k: {"value": (list(x[0]) if isinstance(x[0], tuple) else x[0]), "source": x[1]} for k, x in PARAMS.items()},
            "context_input": context or {}}
    bad = int(np.sum(~np.isfinite(np.concatenate([o, h, l, c])))) if len(c) else 0
    dq = {"bars": int(len(c)), "nan": bad, "min_bars": P("MIN_BARS", params)}
    dobj["data_quality"] = dq
    if len(c) < P("MIN_BARS", params) or bad:
        return _unknown(dobj, f"بياناتٌ {len(c)} جلسة · قيمٌ ناقصة {bad}")
    st = structure(o, h, l, c, params)
    ts, dec_level, extra = tech_state(o, h, l, c, st, params)
    base_dec = STATE_DECISION[ts]
    blocks, missing = validity(context, params)
    reasons = [{"rule": STATE_RULE[ts], "why": STATE_AR[ts]}]
    blocking, info = [], []
    if any(b[0] == "REJECT" for b in blocks):
        state = "REJECT"
        blocking += [{"rule": b[1], "why": b[2]} for b in blocks]
    elif base_dec == "WAIT":
        state = "WAIT"
        blocking.append({"rule": STATE_RULE[ts], "why": STATE_AR[ts]})
        blocking += [{"rule": b[1], "why": b[2]} for b in blocks]
    elif blocks:
        state = "WAIT"
        blocking += [{"rule": b[1], "why": b[2]} for b in blocks]
    elif missing:
        state = "UNKNOWN"
    else:
        state = "READY"
    close = st["close"]
    B = st["bottom"]["price"]
    zone = [round(B, 6), round(B * (1 + P("ZONE_PCT", params) / 100), 6)]
    w = V31.find_w(o, h, l, c, len(c) - 1, P("SWING_K", params), sw=st["swings"])
    info.append({"rule": "R4-TF-01", "why": "المحرّكُ يوميٌّ وحدَه — سياقُ 4 ساعات و30 دقيقة غيرُ مقروء هنا"})
    if w:
        info.append({"rule": "R-W-SPAN", "why": f"W (V3.1 معلومة): قاعان {w['low1']:.4g}/{w['low2']:.4g} · عنق {w['neckline']:.4g}"})
    lib = st["ladder"][0] if st["ladder"] else None
    if lib:
        info.append({"rule": "R4-ENT-02", "why": f"البديلُ (متنازَعٌ عليه C-BREAKOUT): التحرّرُ فوق {lib:.4g} بإقفالين"})
    rsi = None
    try:
        if len(c) >= 15:
            d = np.diff(c[-15:])
            up, dn = d[d > 0].sum() / 14, -d[d < 0].sum() / 14
            rsi = 100.0 if dn == 0 else round(100 - 100 / (1 + up / dn), 2)
    except Exception:                                               # noqa: BLE001
        rsi = None
    vol_ratio = None
    if vol is not None and len(vol) >= 21 and np.nanmean(vol[-21:-1]) > 0:
        vol_ratio = round(float(vol[-1] / np.nanmean(vol[-21:-1])), 3)
    stops = [{"name": "القاع (الأساسيّ)", "price": round(B, 6), "rule": "R4-STOP-01"},
             {"name": "‏−5% تحت القاع", "price": round(B * 0.95, 6), "rule": "R4-STOP-01 (TG_1978)"},
             {"name": "‏−7% تحت القاع", "price": round(B * 0.93, 6), "rule": "R4-STOP-01 (الإنتاج 5-7)"}]
    entry_ref = B * (1 + (P("BID_LO_PCT", params) + P("ZONE_PCT", params)) / 200)
    tg = V31.targets(None, entry_ref, st["ladder"])
    dobj.update({
        "state": state, "tech_state": ts, "tech_state_ar": STATE_AR[ts],
        "decisive_level": round(float(dec_level), 6) if dec_level else None,
        "decisive_class": _cls(dec_level, close, params) if ts not in ("PRESS_RECLAIM", "RETEST_HELD", "BASE_HELD",
                                                                      "RETEST_IN_PROGRESS") else "AT",
        "market_context": {"cycle_high": round(st["cycle_high"]["price"], 6), "cycle_high_date": str(dates[st["cycle_high"]["i"]])[:10],
                           "rsi14": rsi, "volume_vs_20d": vol_ratio},
        "structure": {"bottom": round(B, 6), "bottom_date": str(dates[st["bottom"]["i"]])[:10],
                      "bottom_body_low": round(st["bottom"]["body_low"], 6),
                      "prior_base": (round(st["prior_base"]["price"], 6) if st["prior_base"] else None),
                      "undercut_pct": st["undercut_pct"], "hold_sessions": st["hold_sessions"],
                      "test_high": round(st["test_high"]["price"], 6), "rise_pct": st["test_high"]["rise_pct"],
                      "support2": (round(st["support2"], 6) if st["support2"] else None), "labels": st["labels"], **extra},
        "patterns": ([{"pattern": "W (V3.1)", "low1": w["low1"], "low2": w["low2"], "neckline": w["neckline"],
                       "decisionality": "INFORMATIONAL"}] if w else []),
        "support_resistance": {"zone": zone, "levels": level_set(st, params), "ladder": [round(x, 6) for x in st["ladder"]]},
        "price_location": {"close": round(close, 6), "vs_bottom_pct": round((close / B - 1) * 100, 3),
                           "in_zone": bool(zone[0] <= close <= zone[1])},
        "confirmation": {k: v for k, v in extra.items() if k in ("sessions_in_zone", "reclaim_i", "depth_pct")},
        "entry": {"type1_bids": [round(B * (1 + P("BID_LO_PCT", params) / 100), 6), zone[1]], "type1_rule": "R4-ENT-01 (SUPPORTING)",
                  "type2_liberation": (round(lib, 6) if lib else None), "type2_rule": "R4-ENT-02 (INFORMATIONAL · C-BREAKOUT)"},
        "invalidation": stops,
        "target": tg,
        "decision_reasons": reasons if state in ("READY", "UNKNOWN") else [],
        "blocking_reasons": blocking,
        "informational_factors": info,
        "missing_information": (missing if state == "UNKNOWN" else []),
        "rule_ids": sorted({r["rule"] for r in reasons + blocking + info} | {"R4-BOT-01", "R4-STOP-01", "R4-TGT-01"}),
        "explain": explain_lines(state, ts, dec_level, close, missing, blocking),
    })
    dobj["evidence"] = {rid: RV.RULES_V4[rid]["image_ids"][:6] for rid in dobj["rule_ids"] if rid in RV.RULES_V4}
    dobj["confidence"] = {"tech_state": "rule-based (§34)", "decision": ("UNVERIFIED_VALIDITY" if state == "UNKNOWN" else "rule-based"),
                          "note": "الصلاحيّةُ وبصمةُ المضارب لا تُرى في الشموع"}
    return dobj


_EMPTY_KEYS = ("decisive_level", "decisive_class", "market_context", "structure", "support_resistance", "price_location",
               "confirmation", "entry", "target")


def _unknown(dobj, why):
    """R4-DATA-01: كائنٌ كاملُ المفاتيح بحالة UNKNOWN (لا مفتاحَ يغيب فيكسر قارئًا)."""
    dobj.update(state="UNKNOWN", tech_state="DATA_INSUFFICIENT", tech_state_ar=STATE_AR["DATA_INSUFFICIENT"],
                decision_reasons=[], blocking_reasons=[{"rule": "R4-DATA-01", "why": why}], informational_factors=[],
                missing_information=["شموعٌ يوميّةٌ كافية قبل تاريخ القراءة"], rule_ids=["R4-DATA-01"], patterns=[],
                invalidation=[], evidence={}, explain=[f"لماذا UNKNOWN؟ {why}"],
                confidence={"decision": "DATA_INSUFFICIENT"})
    for k in _EMPTY_KEYS:
        dobj.setdefault(k, None)
    return dobj


def explain_lines(state, ts, lvl, close, missing, blocking):
    """§32: لماذا READY/WAIT/REJECT — أو ما الناقص لـUNKNOWN."""
    if state == "READY":
        return [f"لماذا READY؟ {STATE_AR[ts]} · والصلاحيّةُ مُتحقَّقة"]
    if state == "WAIT":
        return [f"لماذا WAIT؟ {b['why']} ({b['rule']})" for b in blocking] + (
            [f"المستوى الحاسم {lvl:.4g} (السعر {close:.4g})"] if lvl else [])
    if state == "REJECT":
        return [f"لماذا REJECT؟ {b['why']} ({b['rule']})" for b in blocking]
    return [f"لماذا UNKNOWN؟ {STATE_AR[ts]} — والناقص: " + " · ".join(missing or ["بيانات"])]


def analyze_rows(rows, asof_date=None, context=None, symbol="", params=None):
    """صفوفٌ [date, o, h, l, c, v] ⟵ analyze عند آخر جلسةٍ تاريخُها **قبل** asof_date حصرًا (V4_prereg §③)."""
    rows = [r for r in rows if r and all(x is not None for x in r[1:5])]
    if asof_date is not None:
        rows = [r for r in rows if str(r[0])[:10] < str(asof_date)[:10]]
    if not rows:
        return _unknown({"engine": ENGINE_VERSION, "rules_version": RV.VERSION, "symbol": symbol, "timeframe": "1D",
                         "asof": None, "data_quality": {"bars": 0}}, "لا جلسةَ قبل تاريخ العبارة")
    d = [r[0] for r in rows]
    col = lambda j: np.array([float(r[j]) for r in rows])          # noqa: E731
    vol = np.array([float(r[5]) if len(r) > 5 and r[5] is not None else np.nan for r in rows])
    return analyze(col(1), col(2), col(3), col(4), d, None, context, symbol, params, v=vol)
