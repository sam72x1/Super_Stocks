# -*- coding: utf-8 -*-
"""🧭 FAISAL RESEARCH ENGINE — محرّكُ بحثٍ معزول (2026-10-09 · «COMPLETE RECONSTRUCTION & EXECUTION»)

قراءةٌ فقط · لا إنتاج · لا تلغرام · لا V4 يُعدَّل (نواةُ V4 المجمَّدة تُستورَد كما هي وتُستدعى).
المحرّك = طبقةُ مراحلَ فوق نواة V4:
  DATA ⟵ SCREEN (هُويّةُ الارتكاز بلا جدار اللمستين · بإطارين: كاملٌ وما بعد التقسيم) ⟵ TECH (V4)
  ⟵ الحالةُ الزمنيّة FOCUS / WATCH / READY (+ TRIGGER حين يُعرَف الضغط) ⟵ الصلاحيّةُ المؤرَّخة.
كلُّ قراءةٍ عند `asof` تستعمل الشموعَ التي تاريخُها **قبل** `asof` حصرًا (لا نظرَ للأمام) — والسياقُ
(طرح · تقسيم · فلوت · متاح · قروبات · ضغط) يُمرَّر مؤرَّخًا أو يبقى UNKNOWN. لا رقمَ يُخترَع.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (os.path.join(ROOT, "faisal_method_v4"), os.path.join(ROOT, "faisal_method_v3")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import decision_engine as V4          # noqa: E402 — نواةُ V4 المجمَّدة (لا تُعدَّل)

ENGINE_VERSION = "FE 1.0 (2026-10-09)"
LABELS = ("HISTORICAL", "EXPLORATORY", "LIVE")
STAGES = ("INSUFFICIENT_DATA", "REJECTED", "SCREENED", "FOCUS", "WATCH", "READY", "TRIGGER", "HOLD")
ORDER = {s: i for i, s in enumerate(STAGES)}

PARAMS = {
    # (القيمة · الوسم · المصدر) — كلُّ رقمٍ موسوم؛ ولا عتبةَ جديدةً من عندي بلا وسم inferred/engineering
    "MIN_BARS": (40, "engineering", "R4-DATA-01 (V4 PARAMS)"),
    "FRAME_BARS": (120, "production", "نافذةُ قمّة الدورة CYCLE_BARS (V4) — وإطارُ ما بعد التقسيم يُقرأ داخلها"),
    "POST_SPLIT_MIN_BARS": (40, "engineering", "إطارُ ما بعد التقسيم يُقيَّم فقط حين يحمل 40 جلسةً فأكثر (= MIN_BARS)"),
    "OFFERING_DAYS": (90, "faisal_adopted", "نشرةٌ نهائيّة (424B1/4/5) خلال 90 يومًا = طرحٌ معلَّق (Phase 5 H2 · R4-VAL-OFF-01)"),
    "HOLD_MIN": (5, "faisal_verbatim", "R4-HOLD-01 «اذا ماكسر القاع اكثر من 5 جلسات»"),
    "FLOAT_MAX": (5_000_000, "faisal_adopted", "الفلوت 5 ملايين أو أقلّ (H6 A · FWD_FLOAT_MAX)"),
    "SHORT_AVAIL_MAX": (20_000, "faisal_verbatim", "R4-VAL-SHORT-01 «تحت 20 الف»"),
}
OFFERING_FORMS = ("424B1", "424B4", "424B5")    # = الإنتاج `_FOUNDING_OFFERING_FORMS` (S-1/S-3/EFFECT روتينيّة لا حدث)

# الحالةُ الفنيّة في V4 ⟵ المرحلةُ الزمنيّة عند فيصل (FE-STAGE-01 · مستندٌ إلى FAISAL_STATE_MACHINE والمرحلتين 3/4)
TECH_TO_STAGE = {
    "BASE_FORMING": "FOCUS", "BROKEN_NEW_BASE": "FOCUS",                    # قاعٌ غيرُ مُختبَر · اللمسةُ الأولى (Phase 3: الجدارُ الأوّل)
    "SWEEP_ACTIVE": "WATCH", "RETEST_PENDING": "WATCH", "RETEST_IN_PROGRESS": "WATCH",
    "BASE_HELD": "READY", "RETEST_HELD": "READY", "PRESS_RECLAIM": "READY",  # = TECH_READY في V4
}
NEXT_CONDITION = {
    "INSUFFICIENT_DATA": "40 جلسةً يوميّةً فأكثر قبل تاريخ القراءة",
    "REJECTED": "عبورُ بوّابة الهُويّة الساقطة (أو تقسيمٌ عكسيٌّ يفتح إطارًا جديدًا)",
    "FOCUS": "ثباتُ القاع 5 جلساتٍ بلا كسر (R4-HOLD-01)",
    "WATCH": "عودةٌ فوق القاع السابق خلال جلستين بعد السحب أو ثباتٌ في المنطقة 3 جلسات (R4-SWEEP-01 · R4-HOLDZ-01)",
    "READY": "بصمةُ ضغط المضارب لحظيًّا (R4-OP-01) — لا تُقرأ من الشموع اليوميّة",
    "TRIGGER": "تنفيذُ الدخول بالطلبات 5-15% فوق القاع (R4-ENT-01)",
    "HOLD": "زوالُ المانع المؤرَّخ (طرحٌ معلَّق / متاحٌ فوق 20 ألف / قروبات)",
}


def P(name, params=None):
    if params and name in params:
        return params[name]
    return PARAMS[name][0]


# ---------------------------------------------------------------- أدواتٌ نقيّة
def rows_before(rows, asof):
    """الشموعُ التي تاريخُها قبل asof حصرًا (جدارُ النظر للأمام)."""
    out = [r for r in rows if r and str(r[0])[:10] < str(asof)[:10] and all(x is not None for x in r[1:5])]
    return sorted(out, key=lambda r: str(r[0])[:10])


def reverse_splits(splits, asof):
    """[(date, ratio)] ⟵ التقسيماتُ العكسيّة (ratio < 1) بتاريخٍ ≤ asof."""
    return sorted((str(d)[:10], float(r)) for d, r in (splits or []) if float(r) < 1 and str(d)[:10] <= str(asof)[:10])


def offering_state(filings, asof, days=None):
    """(True/False/None, سبب) من إيداعات SEC المؤرَّخة ≤ asof: نشرةٌ نهائيّةٌ خلال `days` ⟵ True · إيداعاتٌ بلا نشرة ⟵ False · لا سجلّ ⟵ None."""
    days = P("OFFERING_DAYS") if days is None else days
    if filings is None:
        return None, "لا سجلَّ SEC"
    dated = [f for f in filings if str(f.get("filingDate", ""))[:10] <= str(asof)[:10]]
    if not dated:
        return None, "لا إيداعَ مؤرَّخًا قبل تاريخ القراءة"
    fin = [f for f in dated if f.get("form") in OFFERING_FORMS]
    if not fin:
        return False, f"إيداعاتٌ {len(dated)} بلا نشرةٍ نهائيّة"
    last = max(str(f["filingDate"])[:10] for f in fin)
    gap = _days(last, asof)
    return (gap <= days), f"آخرُ نشرةٍ نهائيّة {last} (قبل {gap} يومًا)"


def _days(d0, d1):
    import datetime as _dt
    a = _dt.date.fromisoformat(str(d0)[:10]); b = _dt.date.fromisoformat(str(d1)[:10])
    return (b - a).days


def fingerprint(rows):
    h = hashlib.sha256()
    for r in rows:
        h.update(("|".join(str(x) for x in r[:6]) + "\n").encode())
    return h.hexdigest()[:16]


# ---------------------------------------------------------------- SCREEN: هُويّةُ الارتكاز بلا جدار اللمستين
def screen_frozen_bot(symbol, rows, min_bars=None):
    """الفارزُ الإنتاجيّ المجمَّد (analyze_ticker) بتعطيل جدار اللمستين وحدَه = REMOVE_candidate (المرحلة 4).
    ⟵ dict(result, gate, reason). استيرادٌ كسول (البوت ثقيل) — ويُحقَن بديلٌ في الاختبارات.
    `min_bars`: إطارُ ما بعد التقسيم يُقرأ بعمقٍ أقلّ من عمق الإنتاج (120) — يُستعاد بعد النداء."""
    sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "phase3"))
    import p3lib as L            # noqa: E402
    df = L.frame(rows)
    saved = L.S.CONFIG["MIN_BARS"]
    try:
        if min_bars is not None:
            L.S.CONFIG["MIN_BARS"] = int(min_bars)
        res, why, det = L.run_gates(symbol, df, neutral=("ANCHOR",))
    finally:
        L.S.CONFIG["MIN_BARS"] = saved
    gate = "" if res == "PASS" else ("DEPTH" if res == "TOO_FEW_BARS" else (L.reason_gate(why) if res == "REJECT" else "ERROR"))
    return dict(result=res, gate=gate, reason=why, detail=det)


def screen_frames(symbol, rows, splits, asof, screen, params=None):
    """FE-FRAME-01: إطارٌ كامل ثمّ إطارُ ما بعد آخر تقسيمٍ عكسيّ داخل نافذة الدورة (Phase 2: تعريفاتُ البوّابات على النظام
    المسوّى مقابل إطار فيصل بعد التقسيم — مستوى 4). يمرّ إن مرّ أحدُهما؛ ويُسجَّل أيُّ إطارٍ مرّ."""
    out = {"FULL": screen(symbol, rows)}
    rs = reverse_splits(splits, asof)
    post = None
    if rs:
        d0 = rs[-1][0]
        post = [r for r in rows if str(r[0])[:10] >= d0]
        if len(post) >= P("POST_SPLIT_MIN_BARS", params) and len(post) < len(rows):
            out["POST_SPLIT"] = screen(symbol, post, min_bars=P("POST_SPLIT_MIN_BARS", params))
            out["POST_SPLIT"]["since"] = d0
        else:
            out["POST_SPLIT"] = dict(result="NOT_EVALUATED", gate="", reason=f"جلساتُ ما بعد التقسيم {len(post)} دون {P('POST_SPLIT_MIN_BARS', params)}", since=d0)
    passed = [k for k, v in out.items() if v.get("result") == "PASS"]
    return out, (passed[0] if passed else None), (post if (passed and passed[0] == "POST_SPLIT") else rows)


# ---------------------------------------------------------------- القلب
def evaluate(symbol, rows, asof, context=None, label="HISTORICAL", screen=screen_frozen_bot, params=None):
    """صفوفٌ [date,o,h,l,c,v] + تاريخُ القراءة + سياقٌ مؤرَّخ ⟵ سجلُّ قرارٍ قابلٌ للتفسير (§8 من الأمر).
    context: splits=[(date,ratio)] · sec_filings=[{form,filingDate}] · float_shares · short_available · groups · operator_press
    (الغائبُ = None = UNKNOWN · لا يُستنتَج «لا»)."""
    assert label in LABELS, label
    ctx = dict(context or {})
    rows = rows_before(rows, asof)
    rec = {"engine": ENGINE_VERSION, "symbol": symbol, "asof": str(asof)[:10], "label": label,
           "provenance": {"bars": len(rows), "bars_last": (str(rows[-1][0])[:10] if rows else None), "bars_sha": fingerprint(rows),
                          "lookahead": "bars strictly < asof; context dated <= asof", "v4": V4.ENGINE_VERSION,
                          "screen": getattr(screen, "__name__", str(screen)), "context_sources": ctx.get("sources", {})},
           "params": {k: {"value": v[0], "tag": v[1]} for k, v in PARAMS.items()}}
    rules_passed, missing = [], []
    if len(rows) < P("MIN_BARS", params):
        return _finish(rec, "INSUFFICIENT_DATA", first_failed=("FE-DATA-01", f"الجلسات {len(rows)} دون {P('MIN_BARS', params)}"),
                       rules_passed=rules_passed, missing=["شموعٌ يوميّةٌ كافية"])
    rules_passed.append("FE-DATA-01")
    # --- SCREEN (الهُويّة) ---
    frames, frame, frame_rows = screen_frames(symbol, rows, ctx.get("splits"), asof, screen, params)
    rec["screen"] = {"frames": frames, "frame": frame}
    rs = reverse_splits(ctx.get("splits"), asof)
    rec["corporate_actions"] = {"reverse_splits": rs, "last_reverse_split": (rs[-1][0] if rs else None),
                                "splits_source": ("dated" if ctx.get("splits") is not None else "UNKNOWN")}
    if ctx.get("splits") is None:
        missing.append("التقسيمات (إطارُ ما بعد التقسيم غيرُ مقروء)")
    if frame is None:
        f = frames["FULL"]
        return _finish(rec, "REJECTED", first_failed=("FE-SCREEN-01/" + (f.get("gate") or f.get("result")), f.get("reason") or f.get("result")),
                       rules_passed=rules_passed, missing=missing)
    rules_passed += ["FE-SCREEN-01", "FE-FRAME-01:" + frame]
    # --- TECH (نواةُ V4 كما هي) ---
    v4ctx = {"groups": ctx.get("groups"), "offering_pending": None, "short_available": ctx.get("short_available"),
             "operator_press": ctx.get("operator_press")}
    off, off_why = offering_state(ctx.get("sec_filings"), asof, P("OFFERING_DAYS", params))
    v4ctx["offering_pending"] = off
    d = V4.analyze_rows([list(r) + ([None] if len(r) < 6 else []) for r in frame_rows], asof_date=None, context=v4ctx, symbol=symbol)
    ts = d.get("tech_state")
    rec["v4"] = {"state": d.get("state"), "tech_state": ts, "tech_state_ar": d.get("tech_state_ar"), "decisive_level": d.get("decisive_level"),
                 "blocking": d.get("blocking_reasons"), "missing": d.get("missing_information"), "rule_ids": d.get("rule_ids")}
    rec["setup"] = {"structure": d.get("structure"), "patterns": d.get("patterns"), "price_location": d.get("price_location"),
                    "market_context": d.get("market_context")}
    rec["levels"] = {"zone": (d.get("support_resistance") or {}).get("zone"), "levels": (d.get("support_resistance") or {}).get("levels"),
                     "ladder": (d.get("support_resistance") or {}).get("ladder"), "entry": d.get("entry"),
                     "invalidation": d.get("invalidation"), "target": d.get("target")}
    if ts == "DATA_INSUFFICIENT":
        return _finish(rec, "INSUFFICIENT_DATA", first_failed=("R4-DATA-01", "نواةُ V4: بياناتٌ غيرُ كافية في الإطار المختار"),
                       rules_passed=rules_passed, missing=missing + ["شموعٌ كافيةٌ في الإطار"])
    stage = TECH_TO_STAGE[ts]
    rules_passed.append(V4.STATE_RULE[ts])
    # --- الصلاحيّةُ المؤرَّخة ---
    val = {"offering_pending": off, "offering_why": off_why, "float_shares": ctx.get("float_shares"),
           "short_available": ctx.get("short_available"), "groups": ctx.get("groups"), "operator_press": ctx.get("operator_press")}
    rec["validity"] = val
    blocks = []
    if off is True:
        blocks.append(("R4-VAL-OFF-01", off_why))
    elif off is None:
        missing.append("الطرح/التخفيف (R4-VAL-OFF-01)")
    else:
        rules_passed.append("R4-VAL-OFF-01")
    fl = ctx.get("float_shares")
    if isinstance(fl, (int, float)):
        (rules_passed if fl <= P("FLOAT_MAX", params) else blocks).append("FE-VAL-FLOAT-01" if fl <= P("FLOAT_MAX", params) else ("FE-VAL-FLOAT-01", f"الفلوت {int(fl):,} فوق {P('FLOAT_MAX', params):,}"))
    else:
        missing.append("الفلوت (FE-VAL-FLOAT-01)")
    sh = ctx.get("short_available")
    if isinstance(sh, (int, float)):
        (rules_passed if sh <= P("SHORT_AVAIL_MAX", params) else blocks).append("R4-VAL-SHORT-01" if sh <= P("SHORT_AVAIL_MAX", params) else ("R4-VAL-SHORT-01", f"المتاح {int(sh):,} فوق 20,000"))
    else:
        missing.append("المتاح للشورت (R4-VAL-SHORT-01)")
    g = ctx.get("groups")
    if g is True:
        blocks.append(("R4-VAL-GRP-01", "قروباتٌ داخلة"))
    elif g is None:
        missing.append("القروبات (R4-VAL-GRP-01)")
    else:
        rules_passed.append("R4-VAL-GRP-01")
    op = ctx.get("operator_press")
    if op is None:
        missing.append("بصمة الضغط (R4-OP-01)")
    first_failed = None
    if stage == "READY" and blocks:
        stage, first_failed = "HOLD", blocks[0]
    elif stage == "READY" and op is True:
        stage = "TRIGGER"; rules_passed.append("R4-OP-01")
    return _finish(rec, stage, first_failed=first_failed, rules_passed=rules_passed, missing=missing, blocks=blocks)


def _finish(rec, stage, first_failed=None, rules_passed=(), missing=(), blocks=()):
    rec["stage"] = stage
    rec["stage_rank"] = ORDER[stage]
    rec["rules_passed"] = list(rules_passed)
    rec["first_failed"] = ({"rule": first_failed[0], "why": first_failed[1]} if first_failed else None)
    rec["blocks"] = [{"rule": b[0], "why": b[1]} for b in blocks]
    rec["missing_data"] = list(missing)
    rec["validity_verified"] = (stage in ("READY", "TRIGGER") and not missing)
    rec["next_condition"] = NEXT_CONDITION.get(stage, "")
    rec["explain"] = _explain(rec)
    return rec


def _explain(rec):
    s = rec["stage"]
    out = [f"{rec['symbol']} @ {rec['asof']} ⟵ {s} ({rec['label']})"]
    if rec.get("first_failed"):
        out.append(f"أوّلُ شرطٍ ساقط: {rec['first_failed']['rule']} — {rec['first_failed']['why']}")
    if rec.get("v4"):
        out.append(f"الحالةُ الفنيّة (V4): {rec['v4']['tech_state']} — {rec['v4']['tech_state_ar']} · قرارُ V4: {rec['v4']['state']}")
    if rec.get("screen", {}).get("frame"):
        out.append(f"إطارُ الهُويّة: {rec['screen']['frame']}")
    if rec.get("missing_data"):
        out.append("ناقص (UNKNOWN لا «لا»): " + " · ".join(rec["missing_data"]))
    out.append("الشرطُ التالي: " + rec["next_condition"])
    return out


def to_json(rec):
    return json.dumps(rec, ensure_ascii=False, indent=1, default=str)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="FAISAL RESEARCH ENGINE — قراءةُ رمزٍ عند تاريخٍ من الشموع المجمَّدة")
    ap.add_argument("symbol"); ap.add_argument("--asof", required=True); ap.add_argument("--label", default="HISTORICAL")
    a = ap.parse_args()
    import data as D                      # noqa: E402
    rows = D.bars(a.symbol)
    print(to_json(evaluate(a.symbol, rows, a.asof, D.context(a.symbol, a.asof), label=a.label)))
