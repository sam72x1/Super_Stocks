# -*- coding: utf-8 -*-
"""
🧭 FAISAL ANALYSIS TOOL v3 — أداةُ تحليلٍ بمنهج فيصل، قابلةٌ للتفسير، كلُّ سطرٍ فيها بمصدره.

الطبقات (§25-28): البيانات ⟵ السياق ⟵ البنية ⟵ النموذج (W/M) ⟵ التأكيد ⟵ الاختراق ⟵ إعادة الاختبار ⟵
الدخول ⟵ الإبطال ⟵ الأهداف (50٪/100٪ بمعانيها) ⟵ المخاطرة ⟵ قائمةُ الفحص ⟵ المخرَج (نصٌّ عربيّ ‏+ JSON).

⚖️ مبادئ لا تُكسر:
- **لا نظرَ إلى المستقبل:** القاعُ/القمّةُ المحوريّة عند الفهرس i لا تُعرف إلّا عند i+k ⟵ لا تُستعمل قبله (`confirmed_swings`).
- **كلُّ عتبةٍ بوسم مصدرها** (`PARAMS`): faisal_verbatim · faisal_inferred · production (ثابتٌ إنتاجيّ قائم) · engineering.
- **ثلاثُ عائلاتِ أهدافٍ لا تُخلط** (target_forensics.json): سلّمُ مقاومات فيصل · ‏+100% من الدخول (فيصل) ·
  الحركةُ المقيسة 100%/50% من الارتفاع (طرفٌ ثالث — للمقارنة فقط).
- **الدرجةُ قائمةُ فحصٍ لا وزنٌ مخترَع:** كلُّ بندٍ PASS/FAIL/NA مع رقم القاعدة ووسم دليلها.
- **أداةُ قراءةٍ وعرض:** لا تكتب حالةَ إنتاج · ولا ترسل تلغرام إلّا بمُدخَلٍ صريح من المالك (`--send`).

الاستعمال:
    python3 faisal_method_v3/faisal_tool.py TICKER [--asof YYYY-MM-DD] [--json out.json] [--png out.png] [--send]
    python3 faisal_method_v3/faisal_tool.py --cases     # التحقّق البصريّ على حالات صور فيصل (يلزمه TradingView)
"""
import json
import math
import os
import sys

import numpy as np

TOOL_VERSION = "FAISAL-V3 1.0 (2026-10-02)"

# (القيمة، المصدر، القاعدة/السند)
PARAMS = {
    "SWING_K": (3, "engineering", "عرضُ المحور الفركتاليّ اليوميّ (3 بارات كلَّ جهة) — لا رقمَ عند فيصل"),
    "SWING_K_30M": (2, "engineering", "عرضُ المحور على 30 دقيقة"),
    "NECK_RISE_MIN_PCT": (10.0, "faisal_verbatim", "«الصعود غالبا من 10 > 15٪» — METHOD_BOUNCE_MIN_PCT (IMG_0486/IMG_0497) · ارتدادُ القاع إلى العنق"),
    "LOW2_SWEEP_MAX_PCT": (13.0, "faisal_verbatim", "«سحب السيوله متعارف عليه من 7٪ ل 13٪» (IMG_0297) — القاعُ الثاني تحت الأوّل حتى 13% = سحب · وأبعدُ منه ليس W"),
    "LOW2_SWEEP_MIN_PCT": (7.0, "faisal_verbatim", "الحدُّ الأدنى لسحب السيولة (IMG_0297)"),
    "LOW2_ABOVE_MAX_PCT": (10.0, "engineering", "القاعُ الثاني فوق الأوّل حتى 10% ما زال «قاعًا مزدوجًا» — لا رقمَ عند فيصل"),
    "W_BARS_MIN": (3, "engineering", "أدنى فصلٍ بين القاعين"),
    "W_BARS_MAX": (60, "engineering", "أقصى فصلٍ بين القاعين (≈ ثلاثة أشهر تداول)"),
    "SUPPORT2_ZONE_PCT": (6.0, "production", "منطقةُ الدعم الثاني = القاع + دفعاتُ الدخول (ENTRY_TRANCHES=3 × ENTRY_STEP_PCT=3 ⟵ حتى +6%)"),
    "DECISION_BAND_PCT": (3.0, "production", "نطاقُ القرار «مقرون» (TG_58045: 6.18/6.34 = 2.6%) ≈ خطوةُ دفعةٍ واحدة ENTRY_STEP_PCT=3"),
    "LEVEL_TOL_PCT": (2.0, "faisal_verbatim", "«دقة الخطأ لاتتجاوز 2% للدخول الامن» — FAISAL_LEVEL_TOL_PCT (الدليل ص22 · X_20260918_11)"),
    "STOP_BELOW_PCT": (7.0, "faisal_verbatim", "«الوقف عند المتداولين من 5-7٪» (TG_2062) — STOP_BELOW_LOW_PCT الحدُّ الأعلى"),
    "ANTI_CHASE_PCT": (50.0, "faisal_verbatim", "«50٪ تمت بصعود اول ✅ · انتظار اختبار دعم» (IMG_8242 · TG_2108) — R-50-01"),
    "HOLD_MIN_MINUTES": (15, "faisal_verbatim", "«ثبات وتداول فوق خط العنق > اكثر من ربع ساعه» (IMG_0627) — R-W-05"),
    "LADDER_N": (3, "production", "ثلاثةُ أهداف (t1-t3) كما في الإنتاج"),
}


def P(name):
    return PARAMS[name][0]


# ── البنية ───────────────────────────────────────────────────────────────────────────
def confirmed_swings(high, low, asof: int, k: int):
    """محاورُ فركتاليّة **مؤكَّدةٌ عند asof**: قمّةٌ/قاعٌ عند i تُعرف عند i+k ⟵ i+k ≤ asof. [(i, 'H'|'L', سعر)] مرتّبة."""
    out = []
    n = min(len(high), asof + 1)
    for i in range(k, n - k):
        if i + k > asof:
            break
        hw = high[i - k:i + k + 1]
        lw = low[i - k:i + k + 1]
        if high[i] == np.max(hw) and np.argmax(hw) == k:
            out.append((i, "H", float(high[i])))
        if low[i] == np.min(lw) and np.argmin(lw) == k:
            out.append((i, "L", float(low[i])))
    out.sort(key=lambda x: (x[0], x[1]))
    return out


def label_structure(sw):
    """HH/LH للقمم · HL/LL للقيعان مقارنةً بالسابقة من نوعها (R-ST-01: «قمة اعلى» · «قاع ادنى»)."""
    last = {"H": None, "L": None}
    out = []
    for i, t, p in sw:
        prev = last[t]
        if prev is None:
            lab = t + "?"
        elif t == "H":
            lab = "HH" if p > prev else "LH"
        else:
            lab = "HL" if p > prev else "LL"
        out.append({"i": i, "type": t, "price": p, "label": lab})
        last[t] = p
    return out


def heads_since_low(sw, low_i):
    """عددُ القمم الصاعدة (رؤوس) منذ قاع الدورة — R-EL-03 «غالبا 3 رؤوس 2 ارتداد»."""
    hs = [p for i, t, p in sw if t == "H" and i > low_i]
    n, best = 0, None
    for p in hs:
        if best is None or p > best:
            n += 1
            best = p
    return n


# ── W / القاعُ المزدوج ────────────────────────────────────────────────────────────────
def find_w(o, h, l, c, asof: int, k: int = None, sw=None):
    """آخرُ W صالحٍ مؤكَّدٍ عند asof (بلا نظرٍ للأمام) أو None.

    الشروط (كلُّها بمصدرها في PARAMS):
      ① قاعان محوريّان مؤكَّدان L1 ثمّ L2 · فصلُهما W_BARS_MIN..W_BARS_MAX
      ② العنق = أعلى قمّةٍ بينهما · وارتفاعُه فوق أدنى القاعين ≥ NECK_RISE_MIN_PCT
      ③ L2 بين L1×(1−LOW2_SWEEP_MAX) وL1×(1+LOW2_ABOVE_MAX)  (تحت الأوّل حتى 13% = سحب سيولة)
      ④ «جاء من فوق»: أعلى قمّةٍ قبل L1 في نافذةٍ بطول الـW ≥ العنق (اتّجاهٌ هابطٌ سابق · «الضغط لابد منه»)
    """
    k = P("SWING_K") if k is None else k
    # المحورُ عند i يعتمد على [i−k · i+k] وحدَها ⟵ قائمةٌ محسوبةٌ مرّةً تُرشَّح بـ i+k ≤ asof بلا نظرٍ للأمام (تسريعٌ للتحقّق الكمّيّ)
    sw = confirmed_swings(h, l, asof, k) if sw is None else [x for x in sw if x[0] + k <= asof]
    lows = [(i, p) for i, t, p in sw if t == "L"]
    for j in range(len(lows) - 1, 0, -1):
        i2, p2 = lows[j]
        for m in range(j - 1, -1, -1):
            i1, p1 = lows[m]
            gap = i2 - i1
            if gap < P("W_BARS_MIN"):
                continue
            if gap > P("W_BARS_MAX"):
                break
            if not (p1 * (1 - P("LOW2_SWEEP_MAX_PCT") / 100) <= p2 <= p1 * (1 + P("LOW2_ABOVE_MAX_PCT") / 100)):
                continue
            seg = h[i1:i2 + 1]
            ineck = i1 + int(np.argmax(seg))
            neck = float(np.max(seg))
            base = min(p1, p2)
            if neck < base * (1 + P("NECK_RISE_MIN_PCT") / 100):
                continue
            pre0 = max(0, i1 - gap)
            if i1 - pre0 < 1 or float(np.max(h[pre0:i1])) < neck:
                continue
            swept = p2 < p1 * (1 - P("LOW2_SWEEP_MIN_PCT") / 100)
            return {"i1": int(i1), "low1": float(p1), "i2": int(i2), "low2": float(p2), "ineck": int(ineck),
                    "neckline": neck, "height": neck - base, "base": base,
                    "low2_vs_low1_pct": round((p2 / p1 - 1) * 100, 2), "low2_is_sweep": bool(swept),
                    "confirmed_at": int(i2 + k)}
    return None


def w_state(o, h, l, c, w, asof: int):
    """حالةُ الـW عند asof بقواعد فيصل:
       INVALIDATED (إغلاقٌ تحت القاعدة بأكثر من 13%) · AT_SUPPORT2 (منطقةُ دخولٍ A · R-W-03) · UNSAFE_MIDDLE (R-W-02) ·
       BREAKOUT (أوّلُ إغلاقٍ فوق العنق · R-W-03) · RETEST_HOLD · FAILED_BREAKOUT (رفضُ الاختراق = هبوط · R-CL-03)."""
    neck, base, i2 = w["neckline"], w["base"], w["i2"]
    tol = P("LEVEL_TOL_PCT") / 100
    after = range(i2 + 1, asof + 1)
    inval = next((i for i in after if c[i] < base * (1 - P("LOW2_SWEEP_MAX_PCT") / 100)), None)
    brk = next((i for i in after if c[i] > neck), None)
    if inval is not None and (brk is None or inval < brk):
        return {"state": "INVALIDATED", "at": int(inval), "rule": "R-W-03 (حدُّ السحب 13%)"}
    px = float(c[asof])
    if brk is None:
        if px <= w["low2"] * (1 + P("SUPPORT2_ZONE_PCT") / 100):
            return {"state": "AT_SUPPORT2", "at": None, "rule": "R-W-03 «دعم 2 دخول» (TG_58052)"}
        return {"state": "UNSAFE_MIDDLE", "at": None, "rule": "R-W-02 «الدخول بين خط العنق والقاع المزدوج غير امن»"}
    post = range(brk + 1, asof + 1)
    fail = next((i for i in post if c[i] < neck * (1 - tol)), None)
    if fail is not None:
        return {"state": "FAILED_BREAKOUT", "at": int(brk), "failed_at": int(fail), "rule": "R-CL-03 «رفض الاختراق = هبوط»"}
    rt = next((i for i in post if l[i] <= neck * (1 + tol)), None)
    if rt is not None:
        return {"state": "RETEST_HOLD", "at": int(brk), "retest_at": int(rt), "rule": "R-CL-03 «بعد الاختراق وتاكيد الدعوم يكون دخول جديد»"}
    return {"state": "BREAKOUT", "at": int(brk), "rule": "R-W-03 «اول اختراق صحيح»"}


def intraday_hold(ts_list, closes, neckline, minutes_per_bar: int = 30):
    """R-W-05: «ثبات وتداول فوق خط العنق > اكثر من ربع ساعه» — أوّلُ شمعة 30 دقيقة تُغلق فوق العنق كاملةً
    (= ثباتٌ ≥ 30 د ≥ 15) ⟵ ts أو None. على فريم 30 دقيقة كما يرسم فيصل (R-W-06)."""
    if minutes_per_bar < P("HOLD_MIN_MINUTES"):
        raise ValueError("فريمٌ أقصر من ربع ساعة يلزمه عدُّ شموعٍ متتالية")
    for t, x in zip(ts_list, closes):
        if x > neckline:
            return t
    return None


# ── الأهداف والوقف ───────────────────────────────────────────────────────────────────
def resistance_ladder(h, sw, above: float, asof: int, n: int = None):
    """سلّمُ المقاومات فوق مستوى (R-W-08 · R-100 · «الأهداف = سلّم المقاومات»): قممٌ محوريّةٌ مؤكَّدة فوق `above` ·
    مدموجةٌ ضمن LEVEL_TOL_PCT · تصاعديّة · أوّلُ n — وإن نقصت تُكمَّل بأعلى قمّةٍ قبل asof (قمّةُ الدورة)."""
    n = P("LADDER_N") if n is None else n
    tol = P("LEVEL_TOL_PCT") / 100
    lv = sorted({p for i, t, p in sw if t == "H" and p > above * (1 + tol) and i <= asof})
    out = []
    for p in lv:
        if not out or p > out[-1] * (1 + tol):
            out.append(p)
    top = float(np.max(h[:asof + 1]))
    if top > above * (1 + tol) and (not out or top > out[-1] * (1 + tol)):
        out.append(top)
    return out[:n] if len(out) > n else out


def targets(w, entry: float, ladder):
    """ثلاثُ عائلاتٍ بوسومها — لا تُخلط (target_forensics.json)."""
    out = []
    for j, p in enumerate(ladder, 1):
        out.append({"name": f"T{j}", "price": round(p, 4), "family": "faisal_ladder",
                    "source": "faisal_verbatim", "rule": "R-W-08", "status": "CONFIRMED"})
    out.append({"name": "+100%", "price": round(entry * 2, 4), "family": "faisal_gain100",
                "source": "faisal_verbatim", "rule": "R-100-01 · F100-1", "status": "CONFIRMED"})
    if w:
        out.append({"name": "MM100", "price": round(w["neckline"] + w["height"], 4), "family": "third_party_measured_move",
                    "source": "third_party", "rule": "R-W-09 · F100-6", "status": "POSSIBLE",
                    "note": "ارتفاعُ النموذج فوق العنق — لفظُ القناة التعليميّة لا فيصل"})
        out.append({"name": "MM50", "price": round(w["neckline"] + 0.5 * w["height"], 4), "family": "third_party_measured_move",
                    "source": "third_party", "rule": "F50-7", "status": "UNKNOWN",
                    "note": "نصفُ الارتفاع — معنى «50%» في الرسم غيرُ قابلٍ للحسم · للمقارنة فقط"})
    return out


def stops(w):
    s = [{"name": "وقفُ فيصل (الارتكاز)", "price": round(w["low2"] * (1 - P("STOP_BELOW_PCT") / 100), 4),
          "source": "faisal_verbatim", "rule": "STOP_BELOW_LOW_PCT 5-7% (TG_2062)"},
         {"name": "حدُّ السحب (إبطالُ الـW)", "price": round(w["base"] * (1 - P("LOW2_SWEEP_MAX_PCT") / 100), 4),
          "source": "faisal_verbatim", "rule": "IMG_0297 7-13%"},
         {"name": "أسفلُ آخر قاع (طرفٌ ثالث)", "price": round(w["low2"], 4), "source": "third_party", "rule": "R-W-12"}]
    return s


def rr(entry, stop, target):
    risk = entry - stop
    if risk <= 0 or target is None:
        return None
    return round((target - entry) / risk, 2)


# ── التحليل الكامل ───────────────────────────────────────────────────────────────────
def analyze_arrays(o, h, l, c, dates, asof: int = None, m30=None, context=None, symbol: str = ""):
    """قلبُ الأداة (نقيّ): مصفوفاتٌ يوميّة ⟵ تقرير. `m30` = (ts_list, closes) لفريم 30 دقيقة اختياريًّا."""
    o, h, l, c = (np.asarray(x, float) for x in (o, h, l, c))
    n = len(c)
    asof = n - 1 if asof is None else int(asof)
    if asof < 20:
        return {"symbol": symbol, "error": "بياناتٌ أقلّ من 20 جلسة", "tool": TOOL_VERSION}
    k = P("SWING_K")
    sw = confirmed_swings(h, l, asof, k)
    struct = label_structure(sw)
    w = find_w(o, h, l, c, asof, k)
    px = float(c[asof])
    rep = {"tool": TOOL_VERSION, "symbol": symbol, "asof": str(dates[asof])[:10], "price": round(px, 4),
           "structure": struct[-8:], "w": w, "params": {k2: {"value": v[0], "source": v[1], "why": v[2]} for k2, v in PARAMS.items()},
           "context": context or {}}
    checks = []
    if w is None:
        rep["state"] = {"state": "NO_W", "rule": "لا قاعَ مزدوجًا مؤكَّدًا بالشروط"}
        cyc_low = min(range(max(0, asof - 120), asof + 1), key=lambda i: l[i])
        ladder = resistance_ladder(h, sw, px, asof)
        rep["targets"] = targets(None, px, ladder)
        rep["stops"] = []
        rep["heads_since_low"] = heads_since_low(sw, cyc_low)
        rep["checks"] = [{"rule": "R-W-01", "check": "نموذجُ W قائم", "result": "FAIL", "status": "CONFIRMED"}]
        rep["entries"] = []
        return rep
    st = w_state(o, h, l, c, w, asof)
    rep["state"] = st
    # الدخول: منطقتان صالحتان (R-W-03) · والوسطُ غيرُ آمن (R-W-02)
    eA = round(w["low2"] * (1 + P("SUPPORT2_ZONE_PCT") / 200), 4)
    eB = round(w["neckline"], 4)
    entries = [{"mode": "A · الدعم الثاني/سحب السيولة", "price": eA,
                "zone": [round(w["low2"], 4), round(w["low2"] * (1 + P("SUPPORT2_ZONE_PCT") / 100), 4)],
                "rule": "R-W-03 · TG_58052 «دعم 2 دخول» · X_20260918_12 «عند سحب السيوله»", "status": "CONFIRMED"},
               {"mode": "B · أوّلُ اختراقٍ صحيحٍ للعنق", "price": eB, "rule": "R-W-03 «اول اختراق صحيح» · R-W-05",
                "status": "CONFIRMED"}]
    rep["entries"] = entries
    rep["decision_band"] = {"low": round(w["low2"], 4), "high": round(w["low2"] * (1 + P("DECISION_BAND_PCT") / 100), 4),
                            "rule": "R-W-07 «مقرون … ادناهما سلبي اعلاهما اجابي» (TG_58045)",
                            "reading": ("فوق النطاق — W قائم" if px >= w["low2"] * (1 + P("DECISION_BAND_PCT") / 100)
                                        else ("داخل النطاق — قرار" if px >= w["low2"] else "تحت النطاق — سيناريو M السلبيّ"))}
    ladder = resistance_ladder(h, sw, w["neckline"], asof)
    rep["targets"] = targets(w, eB, ladder)
    rep["targets_from_A"] = targets(w, eA, ladder)
    rep["stops"] = stops(w)
    stop0 = rep["stops"][0]["price"]
    t1 = ladder[0] if ladder else None
    rep["rr"] = {"A_to_T1": rr(eA, stop0, t1), "B_to_T1": rr(eB, stop0, t1),
                 "A_to_+100%": rr(eA, stop0, eA * 2), "B_to_+100%": rr(eB, stop0, eB * 2)}
    rep["heads_since_low"] = heads_since_low(sw, w["i2"])
    if m30 is not None:
        ts, cl = m30
        rep["intraday_hold_ts"] = intraday_hold(ts, cl, w["neckline"])
    # قائمةُ الفحص — بنودٌ صريحة لا وزن
    def add(rule, text, ok, status):
        checks.append({"rule": rule, "check": text, "result": ("NA" if ok is None else ("PASS" if ok else "FAIL")), "status": status})
    add("R-W-01", "نموذجُ W قائم (قاعان · عنق · جاء من فوق)", True, "CONFIRMED")
    add("R-W-04", "ضغطٌ قبل العنق (هبوطٌ سابقٌ من فوق العنق)", True, "SUPPORTED")
    add("R-W-02", "السعرُ ليس في الوسط غيرِ الآمن", st["state"] != "UNSAFE_MIDDLE", "SUPPORTED")
    add("R-W-03", "في منطقة دخولٍ صالحة (الدعم الثاني أو بعد الاختراق)",
        st["state"] in ("AT_SUPPORT2", "BREAKOUT", "RETEST_HOLD"), "CONFIRMED")
    add("R-W-05", "ثباتٌ فوق العنق على 30 دقيقة (ربع ساعة فأكثر)",
        None if m30 is None or st["state"] not in ("BREAKOUT", "RETEST_HOLD") else rep.get("intraday_hold_ts") is not None, "CONFIRMED")
    add("R-CL-03", "لا رفضَ للاختراق", st["state"] != "FAILED_BREAKOUT", "SUPPORTED")
    add("R-50-01", "لم يحقّق صعودًا أوّلَ ‏+50% (لا مطاردة)", px < w["base"] * (1 + P("ANTI_CHASE_PCT") / 100), "CONFIRMED")
    add("R-EL-03", "رؤوسٌ منذ القاع الثاني أقلُّ من 3 (قبل منطقة التوزيع)", rep["heads_since_low"] < 3, "SUPPORTED")
    rep["checks"] = checks
    rep["checklist_summary"] = {r: sum(1 for x in checks if x["result"] == r) for r in ("PASS", "FAIL", "NA")}
    return rep


def analyze_w_30m(m30_df, asof=None):
    """R-W-06: W على فريم 30 دقيقة (كما يرسمه فيصل) — نفسُ find_w/w_state بعرض محورٍ SWING_K_30M. ⟵ dict أو None."""
    if m30_df is None or len(m30_df) < 40:
        return None
    m = m30_df
    if asof is not None:
        m = m[[str(x)[:10] <= str(asof)[:10] for x in m.index]]
    if len(m) < 40:
        return None
    o, h, l, c = (m[x].astype(float).values for x in ("Open", "High", "Low", "Close"))
    a = len(c) - 1
    w = find_w(o, h, l, c, a, P("SWING_K_30M"))
    if not w:
        return {"w": None}
    st = w_state(o, h, l, c, w, a)
    ts = [str(x) for x in m.index]
    w = dict(w, t1=ts[w["i1"]], t2=ts[w["i2"]], tneck=ts[w["ineck"]])
    return {"w": w, "state": dict(st, at_ts=(ts[st["at"]] if st.get("at") is not None else None))}


def analyze_df(df, asof=None, m30_df=None, context=None, symbol=""):
    """إطارُ pandas بأعمدة Open/High/Low/Close (فهرسٌ زمنيّ) ⟵ analyze_arrays. `asof` تاريخٌ ⟵ آخرُ جلسةٍ ≤ التاريخ."""
    import pandas as pd
    d = df.dropna(subset=["Open", "High", "Low", "Close"])
    dates = [str(x)[:10] for x in d.index]
    a = None
    if asof is not None:
        cand = [i for i, x in enumerate(dates) if x <= str(asof)[:10]]
        if not cand:
            return {"symbol": symbol, "error": "لا جلسةَ قبل asof", "tool": TOOL_VERSION}
        a = cand[-1]
    m30 = None
    if m30_df is not None and len(m30_df):
        m = m30_df
        if asof is not None:
            m = m[[str(x)[:10] <= str(asof)[:10] for x in m.index]]
        m30 = ([str(x) for x in m.index], m["Close"].astype(float).tolist())
    _ = pd
    rep = analyze_arrays(d["Open"].values, d["High"].values, d["Low"].values, d["Close"].values, dates, a,
                         m30=m30, context=context, symbol=symbol)
    if m30_df is not None:
        rep["w_30m"] = analyze_w_30m(m30_df, asof)
    return rep


# ── المخرَج ──────────────────────────────────────────────────────────────────────────
_STATE_AR = {"NO_W": "لا W مؤكَّد", "AT_SUPPORT2": "🟢 عند الدعم الثاني (منطقة دخول A)",
             "UNSAFE_MIDDLE": "🟡 في الوسط بين القاع والعنق — دخولٌ غيرُ آمن",
             "BREAKOUT": "🟢 اختراقٌ للعنق (منطقة دخول B)", "RETEST_HOLD": "🟢 اختراقٌ ثمّ إعادةُ اختبارٍ صامدة",
             "FAILED_BREAKOUT": "🔴 رفضُ الاختراق (= هبوط)", "INVALIDATED": "🔴 أُبطل (كسرٌ أعمق من سحب السيولة)"}


def fmt(x):
    return "—" if x is None else (f"{x:.4f}".rstrip("0").rstrip(".") if x < 1 else f"{x:.2f}")


def render_text(rep):
    """رسالةٌ عربيّة مختصرة — بلا علامات مقارنة (قاعدة المشروع) · كلُّ رقمٍ بوسمه."""
    if rep.get("error"):
        return f"🧭 ${rep.get('symbol', '')} — {rep['error']}"
    L = [f"🧭 ${rep['symbol']} · منهج فيصل v3 · بيانات جلسة {rep['asof']}", f"💰 السعر {fmt(rep['price'])}"]
    st = rep["state"]["state"]
    L.append(f"📍 الحالة: {_STATE_AR.get(st, st)} — {rep['state'].get('rule', '')}")
    w = rep.get("w")
    if w:
        L.append(f"〰️ W: القاع الأول {fmt(w['low1'])} · القاع الثاني {fmt(w['low2'])}"
                 + (" (سحب سيولة)" if w["low2_is_sweep"] else "") + f" · خط العنق {fmt(w['neckline'])}")
        db = rep["decision_band"]
        L.append(f"⚖️ نطاق القرار {fmt(db['low'])} – {fmt(db['high'])}: {db['reading']}")
        for e in rep["entries"]:
            L.append(f"📥 دخول {e['mode']}: {fmt(e['price'])}")
        L.append("🚫 الدخول في الوسط بين القاع والعنق غير آمن (فيصل) — وكمّيًّا على اليوميّ لم يُثبَت (T-W)")
        s = rep["stops"][0]
        L.append(f"⛔ وقف الخسارة {fmt(s['price'])} ({s['name']})")
    fam = {"faisal_ladder": "🎯", "faisal_gain100": "🎯", "third_party_measured_move": "📐"}
    for t in rep.get("targets", []):
        tag = "فيصل" if t["source"] == "faisal_verbatim" else "طرف ثالث — للمقارنة"
        L.append(f"{fam.get(t['family'], '🎯')} {t['name']}: {fmt(t['price'])} ({tag})")
    if rep.get("rr"):
        L.append(f"⚖️ العائد إلى المخاطرة حتى الهدف الأول: من A {fmt(rep['rr']['A_to_T1'])} · من B {fmt(rep['rr']['B_to_T1'])}")
    w3 = (rep.get("w_30m") or {}).get("w")
    if w3:
        L.append(f"🕧 W على 30 دقيقة: {fmt(w3['low1'])} / {fmt(w3['low2'])} · العنق {fmt(w3['neckline'])} · "
                 f"{_STATE_AR.get(rep['w_30m']['state']['state'], rep['w_30m']['state']['state'])}")
    cs = rep.get("checklist_summary") or {}
    if cs:
        L.append(f"✅ قائمة الفحص: نجح {cs.get('PASS', 0)} · لم ينجح {cs.get('FAIL', 0)} · غير متاح {cs.get('NA', 0)}")
        for x in rep["checks"]:
            if x["result"] == "FAIL":
                L.append(f"   ✖️ {x['check']} ({x['rule']})")
    L.append("ℹ️ أداة قراءة لا توصية · الأهداف بالمصدر: فيصل (سلّم المقاومات و+100%) · الطرف الثالث للمقارنة فقط")
    return "\n".join("‏" + x for x in L)


def render_png(rep, o, h, l, c, path, start: int = None):
    """تراكبٌ بصريّ للتحقّق (§29) — يعيد استعمال hs_forensic.render_bars."""
    import hs_forensic as FX
    a = len(c) - 1
    s = max(0, (start if start is not None else a - 120))
    bars = [[o[i], h[i], l[i], c[i]] for i in range(s, a + 1)]
    lines, marks = {}, {}
    w = rep.get("w")
    if w:
        lines["neck"] = (w["neckline"], max(0, w["i1"] - s))
        marks["L1"] = (w["i1"] - s, w["low1"])
        marks["L2"] = (w["i2"] - s, w["low2"])
        for e in rep["entries"]:
            lines[e["mode"][:1]] = (e["price"], max(0, w["i2"] - s))
        lines["stop"] = (rep["stops"][0]["price"], max(0, w["i2"] - s))
    for t in rep.get("targets", []):
        lines[t["name"]] = (t["price"], 0)
    return FX.render_bars(bars, path, marks=marks, lines=lines, title=f"{rep['symbol']} {rep['asof']} {rep['state']['state']}")


# ── التشغيل الحيّ ────────────────────────────────────────────────────────────────────
def fetch_daily(symbol, n=900):
    import Super_stock as S
    import tv_data as TV
    tmap = S._tv_ticker_map()
    full = tmap.get(symbol) or f"NASDAQ:{symbol}"
    bars = TV.Chart().bars(full, "1D", n=n)
    return S.tv_daily_frame(bars, "2000-01-01"), full


def fetch_30m(full, n=1500):
    import pandas as pd
    import tv_data as TV
    bars = TV.Chart().bars(full, "30", n=n)
    if not bars:
        return None
    df = pd.DataFrame([(TV.ny_time(b[0]), b[1], b[2], b[3], b[4], b[5]) for b in bars],
                      columns=["ts", "Open", "High", "Low", "Close", "Volume"]).set_index("ts")
    return df


def production_context(symbol, df):
    """سياقُ الإنتاج (للعرض): حكمُ analyze_ticker ومستوياته — فاشلٌ-آمن."""
    try:
        import Super_stock as S
        r = S.analyze_ticker(symbol, df)
    except Exception as e:                                             # noqa: BLE001
        return {"production": f"تعذّر ({type(e).__name__})"}
    if not r:
        return {"production": "ليس سهمَ ارتكازٍ بمعايير الفارز اليوم (analyze_ticker ⟵ None)"}
    def rnd(v):
        if isinstance(v, (int, float)):
            return round(float(v), 4)
        if isinstance(v, (list, tuple)):
            return [rnd(x) for x in v]
        return v
    keep = ("tier", "pivot", "entry", "tranches", "stop", "t1", "t2", "t3", "rr")
    return {"production": {k: rnd(r.get(k)) for k in keep}}


def run_ticker(symbol, asof=None, json_out=None, png_out=None, send=False):
    df, full = fetch_daily(symbol)
    if df is None or len(df) < 30:
        print(f"⛔ لا شموع لـ{symbol}")
        return 2
    m30 = fetch_30m(full)
    ctx = production_context(symbol, df if asof is None else df[[str(x)[:10] <= asof for x in df.index]])
    rep = analyze_df(df, asof=asof, m30_df=m30, context=ctx, symbol=symbol)
    txt = render_text(rep)
    print(txt)
    if json_out:
        json.dump(rep, open(json_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    if png_out:
        d = df if asof is None else df[[str(x)[:10] <= asof for x in df.index]]
        render_png(rep, d["Open"].values, d["High"].values, d["Low"].values, d["Close"].values, png_out)
    if send:
        import Super_stock as S
        S.send_telegram(txt)
        print("📤 أُرسلت (بمُدخَل send صريح)")
    return 0


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    if not a:
        print(__doc__)
        return 2
    if a[0] == "--cases":
        import faisal_cases
        return faisal_cases.main()

    def opt(name):
        if name in a:
            i = a.index(name)
            return a[i + 1] if i + 1 < len(a) else None
        return None
    return run_ticker(a[0].upper().lstrip("$"), asof=opt("--asof"), json_out=opt("--json"),
                      png_out=opt("--png"), send=("--send" in a))


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    _ = math
    raise SystemExit(main())
