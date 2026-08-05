#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧪 `T-ENVELOPE` — هل **التداول** بظرف الكاتالوج يربح؟

**العقد:** `envelope_prereg.md` (مدفوعٌ قبل أيّ رقم) · **المواصفة:** مشتقّةٌ منه.
**القرار** من `envelope_scan.decide` — نفسِ الدالّة التي يقرّر بها الصيّاد الحيّ.
**وبناءُ الصفقة** من `backtest_symbol` الإنتاجيّ — **صفر سطرِ منطقٍ مستنسَخ**.

🔒 **بحث/قياس فقط:** لا يُعدَّل `Super_stock.py` ولا `envelope_scan.py` ولا
`catalog_envelope.py` ولا `replay10.py` ولا `envelope_p90.json` ولا
`backtest.yml` · بلا تلغرام · بلا حفظ حالة · ولا علمَ `BT_*` جديدًا (‏workflow
مستقلّ كـ`catalog_envelope.yml` فلا يُسقط قفل P1 ولا قفل عدد المدخلات).

⚠️ **لقطةٌ مجمَّدة إلزامية**، و**المِجَسّات تُطبَع قبل أيّ رقمِ ذراع** — فبلا
جدول المِرساة لا تُفسَّر نتيجة (‏التلوّث الزمنيّ: نافذةُ معايرة رمزٍ قد تقع
**داخل** سنة الاختبار).
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import statistics
import sys
import time

# ⚠️ **قبل الاستيراد حصرًا:** `_apply_backtest_overrides` يُنفَّذ وقت التحميل
#    ويشترط `SCREENER_MODE=BACKTEST` ⇒ ضبطُه بعد الاستيراد = **علمٌ خامل**
#    (بصمة الـno-op الموثّقة). ولذلك يُضبَط هنا لا في الـworkflow وحده.
os.environ["SCREENER_MODE"] = "BACKTEST"
os.environ["BT_REPLAY10"] = "1"                  # يُلحق date/exit_date/rr
os.environ.setdefault("BT_POTENTIAL", "1")       # mg_pre_stop

import replay10 as RP                                             # noqa: E402
import catalog_envelope as CE                                     # noqa: E402
import envelope_scan as ES                                        # noqa: E402
import Super_stock as S                                           # noqa: E402

EFFECT_R = 0.15        # حدُّ الأثر المسجَّل
Z_MIN = 1.96           # أحاديّ · بونفيروني على مقارنتين (α=0.025)
TOST_D = 0.35          # حدُّ التكافؤ — أصغرُ قابلٍ للاستيفاء بالـSE المقيس
MIN_TRADES = 30        # حدُّ العيّنة/سنة


# ═══════════════════════════════════════════════════════════════════════════
# ① المِجَسّات الإلزامية — تُطبَع **قبل** أيّ رقمِ ذراع
# ═══════════════════════════════════════════════════════════════════════════
def probe_manifest(path: str) -> dict:
    """🔏 بصمةُ اللقطة. **لازم** لأن `load_frozen_dataset` يحذّر **ويمضي** عند
    اختلاف البصمة، وقراءةُ المانفست كلُّها داخل `try/except` ⇒ مانفستٌ غائب =
    **صمتٌ تام**. هنا يُطبَع صراحةً."""
    out = {"manifest": None, "sha256": None, "ok": False}
    try:
        with open(path + ".manifest.json", encoding="utf-8") as fh:
            man = json.load(fh)
        out["manifest"] = man
        with open(path, "rb") as fh:
            out["sha256"] = hashlib.sha256(fh.read()).hexdigest()
        out["ok"] = (not man.get("sha256")) or man["sha256"] == out["sha256"]
    except Exception as e:                                        # noqa: BLE001
        out["error"] = str(e)
    return out


def probe_anchors(edges: dict, years: tuple) -> dict:
    """🕰️ **جدولُ المِرساة والتلوّث الزمنيّ.**

    الحوافُّ مُعايرةٌ على نافذةِ ما قبل انفجارِ كلّ رمز. فلو وقعت نافذةُ رمزٍ
    **داخل** سنةٍ نختبرها ⇒ تسرّبٌ. تواريخُ المِرساة مخزَّنةٌ الآن في
    `envelope_p90.json:anchor_last_measured` (‏كانت تُطبَع سجلًّا فقط فتتبخّر).

    🔴 يرجّع `contaminated` = السنواتُ الملوَّثة. ⚠️ **والأداةُ ترصد ولا تُقصي:**
    كلُّ تشغيلةٍ سنةٌ واحدة، فالإقصاءُ يقع في **خطوة التجميع** (‏عند كتابة الحكم)
    لا هنا — يُقال صريحًا لئلّا يُقرأ السطرُ ضمانةً لا يملكها الكود."""
    anchors = ((edges.get("_meta") or {}).get("anchor_last_measured")
               or {})
    if not anchors:
        # ⚠️ يُعلَن ولا يُخمَّن: بلا تواريخ **لا يمكن** نفيُ التلوّث.
        return {"n": 0, "by_year": {}, "contaminated": sorted(years),
                "note": "تواريخُ المِرساة غائبة ⇒ **كلُّ السنوات تُعلَن ملوَّثة "
                        "احتياطًا** (لا نفيَ بلا قياس)"}
    by_year = {}
    for sym, d in anchors.items():
        y = int(str(d)[:4])
        by_year.setdefault(y, []).append(sym)
    return {"n": len(anchors), "by_year": {k: sorted(v) for k, v in
                                           sorted(by_year.items())},
            "contaminated": sorted(y for y in years if y in by_year)}


def probe_power(r_units: list) -> dict:
    """📏 القوّة الإحصائية **من الأرقام المقيسة لا المُقدَّرة**.

    🔴 سببُه طعنٌ خصوميّ أصاب: بسعة 10 والـSE المقيس، أصغرُ أثرٍ يَبين على مقياس
    المحفظة **‏0.23-0.27R/جلسة** — أي أضعافُ حدّ الأثر المسجَّل (‏0.15R) ⇒
    **التجربةُ بذلك المقياس غير قابلةٍ للعبور ولو نجح الظرف.** فالمقياس الأساسيّ
    صار **التوقّع لكل إشارة** (‏`M-P`) والمحفظة **ثانويًّا** (‏`M-D`)."""
    xs = [v for v in r_units if v is not None]
    n = len(xs)
    if n < 2:
        return {"n": n, "sd": None, "mde": None, "note": "عيّنةٌ لا تكفي"}
    sd = statistics.stdev(xs)
    se = sd / (n ** 0.5)
    return {"n": n, "mean": sum(xs) / n, "sd": sd, "se": se,
            "mde_1side": Z_MIN * se * (2 ** 0.5),
            "detectable_at_effect": (EFFECT_R / (se * (2 ** 0.5)))
            if se > 0 else None}


# ═══════════════════════════════════════════════════════════════════════════
# ② سياقُ الإرخاء — الموضع الوحيد الذي يمسّ CONFIG وإحصاءَ الرفض
# ═══════════════════════════════════════════════════════════════════════════
@contextlib.contextmanager
def relaxed_step(relax: dict, step: int):
    """🔓 يُرخي `relax` ويضبط `BACKTEST_STEP`، **ويستعيد كذلك إحصاءَ الرفض**
    (`_REJECT_STATS`/`_REJECT_REASONS`) لئلّا يتلوّث توزيعُ الأساس بملايين
    نداءات المشي المُرخى. ببصمةٍ قبل/بعد تكشف أيّ تسرّب."""
    keys = sorted(set(relax) | {"BACKTEST_STEP"})
    snap = {k: S.CONFIG.get(k) for k in keys}
    before = hashlib.sha256(json.dumps(snap, sort_keys=True,
                                       default=str).encode()).hexdigest()
    rs = dict(S._REJECT_STATS)
    rr = dict(S._REJECT_REASONS)
    try:
        S.CONFIG.update(relax)
        S.CONFIG["BACKTEST_STEP"] = int(step)
        yield
    finally:
        for k in keys:
            if snap[k] is None:
                S.CONFIG.pop(k, None)
            else:
                S.CONFIG[k] = snap[k]
        S._REJECT_STATS.clear(); S._REJECT_STATS.update(rs)
        S._REJECT_REASONS.clear(); S._REJECT_REASONS.update(rr)
        after = hashlib.sha256(json.dumps(
            {k: S.CONFIG.get(k) for k in keys}, sort_keys=True,
            default=str).encode()).hexdigest()
        if after != before:
            S.log("⛔ envelope_bt: **تسرّبُ إرخاء** — CONFIG لم تعد كما كانت!")


def relax_for(edges: dict, arm: str) -> dict:
    """قاموسُ الإرخاء لكل ذراع.

    🔴 **وأرضيةُ السعر تُعاد إلى حافّة الظرف** لا `0.0`: `RELAX_ALL` تضع
    `MIN_PRICE=0` فيموت **حارسُ الإشارة الوهمية** في المحرّك (يرفض عند سعرٍ خامٍ
    تحت الأرضية = تشويهُ تقسيم). وبإعادتها إلى حافّة الظرف يطبّق **المحرّكُ نفسه**
    الحارسَ بأرضيةٍ صحيحة — بلا دالّةٍ جديدة ولا تشويه (‏`decide` يشترط السعر
    المعدَّل ≥ الحافّة سلفًا، فالرفضُ الجديد هو الوهميّ وحده)."""
    rx = dict(CE.RELAX_ALL)
    try:
        p = edges.get("price")
        if p is not None:
            rx["MIN_PRICE"] = float(p)
    except (TypeError, ValueError):
        pass
    if arm == "E1C":
        rx.pop("RECENT_RISE_BLOCK_PCT", None)      # D11 يعمل
    return rx


# ═══════════════════════════════════════════════════════════════════════════
# ③ المشي — بنفس سياسة المحرّك حرفيًّا
# ═══════════════════════════════════════════════════════════════════════════
def walk_arm(sym, df, edges, splits, window, arm, counters, decide_fn=None,
             stride=None):
    """🚶 مشيٌ بسياسة المحرّك: `i = MIN_BARS` · `while i < n - fwd` · القرارُ على
    `df.iloc[:i]` · المرفوض `i += stride` · المقبولُ يُبنى بـ`backtest_symbol`
    **الإنتاجيّ** على شريحةٍ `iloc[:i+fwd+1]` بنافذة `(d, d)` وخطوة 1 ⇒ صفقةٌ
    واحدة بلا تسريب (النافذةُ الأمامية `fut = df.iloc[i:i+fwd]` لا تقرأ الزائدة).

    🔴 **و`stride` ≠ خطوةُ النداء الداخليّ — والخلطُ بينهما عيبٌ مقيس:**
    الخطوةُ **1** لازمةٌ للنداء الداخليّ وحده (نافذتُه يومٌ واحد `(d,d)`، فبخطوة 5
    قد يتخطّى المحرّكُ ذلك البار عينَه فلا تُبنى صفقة). أمّا **مِشيةُ الذراع** فيجب
    أن تكون **خطوةَ الإنتاج (5)** كما في `E0` — وإلّا زارت الذراعُ خمسةَ أضعافِ
    البارات فصار «إشاراتٌ أكثر» **كثافةَ عيّنةٍ لا أثرَ ظرف**، وهو بعينه ما يرفضه
    حارسُ الصلاحية `V6` في التسجيل («الخطوة 5 لا تتغيّر بين الأذرع»).

    🔒 `d = str(df.index[i-1].date())` مثبَّتٌ هنا، ويُتحقَّق أن `trade["date"] == d`."""
    dec = decide_fn or ES.decide
    fwd = int(S.CONFIG["BACKTEST_FORWARD_DAYS"])
    step = int(S.CONFIG["BACKTEST_STEP"] if stride is None else stride)
    n = len(df)
    out = []
    i = int(S.CONFIG["MIN_BARS"])
    lo, hi = window
    while i < n - fwd:
        d = str(df.index[i - 1].date())
        if d < lo or d > hi:
            i += step
            continue
        counters["visits"] += 1
        try:
            good, why, vals = dec(S, sym, df.iloc[:i], edges)
        except Exception:                                        # noqa: BLE001
            counters["decide_error"] += 1
            i += step
            continue
        if not good:
            counters["rejected"] += 1
            i += step
            continue
        counters["accepted"] += 1
        # 🔒 الخطوة **1 للنداء الداخليّ وحده** ثم تُستعاد فورًا — فمِشيةُ الذراع
        #    تبقى خطوةَ الإنتاج (‏`step`) كما في `E0`.
        _prev_step = S.CONFIG.get("BACKTEST_STEP")
        S.CONFIG["BACKTEST_STEP"] = 1
        try:
            tr = S.backtest_symbol(sym, df.iloc[:i + fwd + 1], None,
                                   date_window=(d, d), splits=splits)
        except Exception:                                        # noqa: BLE001
            counters["build_error"] += 1
            i += fwd
            continue
        finally:
            if _prev_step is None:                # لم يكن موجودًا ⇒ يُرفَع لا يُصفَّر
                S.CONFIG.pop("BACKTEST_STEP", None)
            else:
                S.CONFIG["BACKTEST_STEP"] = _prev_step
        for t in (tr or []):
            if str(t.get("date")) != d:
                counters["date_mismatch"] += 1
                continue
            t["arm"] = arm
            out.append(t)
        counters["built"] += len(tr or [])
        # 🔒 مرآةُ المحرّك حرفيًّا: **نافذةٌ كاملة بعد صفقةٍ مبنيّة** (`:14321`)،
        #    و**خطوةٌ واحدة إن لم تُبنَ** — والمحرّكُ قد يرفض داخليًّا بعد قبول
        #    `decide` (حارسُ الإشارة الوهمية `M1_phantom_split`)، وهناك يتقدّم
        #    الإنتاجُ بخطوةٍ لا بنافذة. فلولا هذا التمييز لتخطّت الذراعُ 40 جلسة
        #    حيث يتخطّى الإنتاجُ 5 = فرقُ كثافةٍ ثانٍ بين الأذرع.
        if tr:
            i += fwd
        else:
            counters["built_none"] = counters.get("built_none", 0) + 1
            i += step
    return out


def walk_production(sym, df, splits, window):
    """‏E0: يفوّض لـ`backtest_symbol` بلا حرفٍ إضافيّ — **ولا يُنفَّذ داخل أيّ
    سياق إرخاء** (وإلّا لم يعد أساسًا)."""
    try:
        return S.backtest_symbol(sym, df, None, date_window=window,
                                 splits=splits) or []
    except Exception:                                            # noqa: BLE001
        return []


def arm_trades(hist, splits_map, window, arm, edges, stride=None):
    """يلفّ الكون لذراعٍ واحدة. حارسٌ لكل رمز **يُسجَّل ولا يُصمَت**.

    `stride` = مِشيةُ الذراع، وتُمرَّر **خطوةَ الإنتاج المقروءةَ قبل أيّ إرخاء**
    فتتساوى كثافةُ العيّنة مع `E0` (حارس `V6`)."""
    fwd = int(S.CONFIG["BACKTEST_FORWARD_DAYS"])
    need = int(S.CONFIG["MIN_BARS"]) + fwd
    counters = {"symbols": 0, "skipped_short": 0, "visits": 0, "accepted": 0,
                "rejected": 0, "decide_error": 0, "build_error": 0,
                "date_mismatch": 0, "built": 0, "stride": stride}
    trades = []
    t0 = time.time()
    for sym, df in hist.items():
        if df is None or len(df) < need:
            counters["skipped_short"] += 1
            continue
        counters["symbols"] += 1
        if arm == "E0":
            trades += [dict(t, arm="E0") for t in
                       walk_production(sym, df, (splits_map or {}).get(sym), window)]
        else:
            trades += walk_arm(sym, df, edges, (splits_map or {}).get(sym),
                               window, arm, counters, stride=stride)
    counters["seconds"] = round(time.time() - t0, 1)
    return trades, counters


def exclude_catalog(trades):
    """‏X: يرشّح صفقات الكاتالوج **قبل** إعادة المحفظة لا بعدها — لأن الاستبعاد
    يغيّر مَن يزاحم على الخانات."""
    cat = set(CE.CATALOG)
    kept = [t for t in trades if str(t.get("symbol")) not in cat]
    return kept, len(trades) - len(kept)


# ═══════════════════════════════════════════════════════════════════════════
# ④ الجسر والمقياسان
# ═══════════════════════════════════════════════════════════════════════════
def per_trade_expectancy(trades):
    """`M-P` **الأساسيّ**: متوسّط `r_unit` لكل إشارة (غيرُ المُعبَّأة = 0.0R)."""
    xs = [v for v in (RP.r_unit(t) for t in trades) if v is not None]
    if not xs:
        return {"n": 0, "mean": None, "sd": None, "se": None}
    sd = statistics.stdev(xs) if len(xs) > 1 else 0.0
    return {"n": len(xs), "mean": sum(xs) / len(xs), "sd": sd,
            "se": (sd / (len(xs) ** 0.5)) if len(xs) > 1 else None,
            "r_units": xs}


def portfolio_metric(trades, n_sessions):
    """`M-D` **ثانويّ**: صافي R/جلسة بسعة `replay10` (‏10 = الحيّ).

    🔴 `exploded` محرَّمٌ ولا يُقرأ (ما بعد الوقف). والمساند: المرفوض بالسعة ·
    وسيط `mg_pre_stop`."""
    cands, idx, outcome_of = RP.candidates_from_trades(trades)
    if not cands:
        return {"net_r_per_day": None, "taken": 0,
                "note": "صفر مرشّح ⇒ **العلم كان خاملًا** (لا يُفسَّر كصفرٍ حقيقيّ)"}
    res = RP.replay(cands, outcome_of=outcome_of,
                    sessions=range(0, max(1, n_sessions)))
    taken = res.get("taken") or []
    mg = [float(t.payload.get("mg_pre_stop")) for t in taken
          if t.payload.get("mg_pre_stop") is not None]
    return {"net_r_per_day": RP.net_r_per_day(taken, max(1, n_sessions)),
            "taken": len(taken), "n_candidates": len(cands),
            "n_sessions": n_sessions,
            "rejected_cap": res.get("rejected_capacity"),
            "mg_median": (statistics.median(mg) if mg else None),
            "mg_ge_100": sum(1 for v in mg if v >= 100.0)}


def z_diff(a, b):
    """‏z لفرق متوسّطَين مستقلَّين — والحكمُ يستعمله لا التقديرَ."""
    try:
        if not a.get("se") or not b.get("se"):
            return None
        se = (a["se"] ** 2 + b["se"] ** 2) ** 0.5
        return (a["mean"] - b["mean"]) / se if se > 0 else None
    except Exception:                                            # noqa: BLE001
        return None


# ═══════════════════════════════════════════════════════════════════════════
def run() -> int:
    path = os.environ.get("BT_FROZEN_PATH", "").strip()
    if not path:
        S.log("⛔ T-ENVELOPE: `BT_FROZEN_PATH` إلزاميّ.")
        return 2
    edges = ES.load_edges()
    if not edges:
        S.log("⛔ T-ENVELOPE: حوافُّ الظرف غائبة — لا قرار.")
        return 2
    meta = edges.get("_meta") or {}
    src = str((meta or {}).get("source") or "")
    fp = ES.edges_fingerprint(edges)
    S.log(f"🧪 T-ENVELOPE · حوافّ {fp} · لقطة {meta.get('snapshot')} · "
          f"{meta.get('n_symbols')} رمزًا · مُستبعَدون "
          f"{list((meta.get('excluded') or {}).keys())}")
    # 🔴 حاجب: حوافٌّ غيرُ آليّةٍ ⇒ التجربة تختبر قرارًا غير مُبرهَنٍ أنه مُخرَجُ الأداة
    if os.environ.get("ENV_BT_ALLOW_MANUAL_EDGES", "") != "1" \
            and not src.startswith("مُخرَجٌ آليّ"):
        S.log(f"⛔ حاجب: وسمُ الحواف «{src}» — ليس مُخرَجًا آليًّا. "
              "أعِد المعايرة، أو مرّر ENV_BT_ALLOW_MANUAL_EDGES=1 بوسمٍ صريح.")
        return 3

    man = probe_manifest(path)
    S.log(f"🔏 المانفست: ok={man['ok']} · sha={str(man.get('sha256'))[:12]} "
          f"· {man.get('manifest')}")
    hist, splits_map, asof = S.load_frozen_dataset(path)
    if not hist:
        S.log("⛔ تعذّر تحميل اللقطة.")
        return 2

    year = int(os.environ.get("ENV_BT_YEAR", "2025"))
    window = (f"{year}-01-01", f"{year}-12-31")
    S.log(f"📅 النافذة {window} · اللقطة as-of {asof} · {len(hist)} رمزًا")

    anch = probe_anchors(edges, (year,))
    S.log(f"🕰️ المِرساة: {anch['n']} تاريخًا · بالسنوات {anch.get('by_year')}")
    if anch["contaminated"]:
        S.log(f"🔴 **تلوّثٌ زمنيّ**: {anch['contaminated']} — **رصدٌ لا إقصاء**: "
              "هذي التشغيلة سنةٌ واحدة، والإقصاءُ يقع عند تجميع الحكم"
              + (f" · {anch['note']}" if anch.get("note") else ""))

    sess_dates = sorted({str(d.date()) for df in hist.values()
                         for d in df.index if window[0] <= str(d.date()) <= window[1]})
    n_sessions = len(sess_dates)
    S.log(f"🗓️ جلسات النافذة: {n_sessions}")

    # 🔒 خطوةُ الإنتاج تُقرأ **قبل أيّ إرخاء** وتُمرَّر مِشيةً لكل ذراع، فلا تُقاس
    #    كثافةُ عيّنةٍ أكبر على أنها أثرُ ظرف (حارس `V6`: الخطوة 5 لا تتغيّر).
    prod_stride = int(S.CONFIG["BACKTEST_STEP"])
    S.log(f"🚶 مِشيةُ كلّ الأذرع = خطوةُ الإنتاج {prod_stride} جلسة "
          f"(النداء الداخليّ وحده بخطوة 1، ويُستعاد فورًا)")
    if prod_stride != 5:
        S.log("⛔ V6: `BACKTEST_STEP` ليس 5 — ثابتٌ متبدّل.")
        return 8

    arms = {}
    for arm in [a.strip() for a in
                os.environ.get("ENV_BT_ARMS", "E0,E1,E1C").split(",") if a.strip()]:
        if arm == "E0":
            tr, cnt = arm_trades(hist, splits_map, window, "E0", edges,
                                 stride=prod_stride)
        else:
            rx = relax_for(edges, arm)
            with relaxed_step(rx, prod_stride):
                tr, cnt = arm_trades(hist, splits_map, window, arm, edges,
                                     stride=prod_stride)
        arms[arm] = tr
        S.log(f"── {arm}: {len(tr)} صفقة · {cnt}")

    S.log("")
    S.log("═══ 📊 النتائج ═══")
    report = {}
    for arm, tr in arms.items():
        for tag, rows in (("", tr), ("-X", exclude_catalog(tr)[0])):
            key = arm + tag
            mp = per_trade_expectancy(rows)
            md = portfolio_metric(rows, n_sessions)
            report[key] = {"MP": {k: v for k, v in mp.items() if k != "r_units"},
                           "MD": md}
            S.log(f"   {key:<8} M-P: n={mp['n']:<5} "
                  f"متوسط={('%.4f' % mp['mean']) if mp['mean'] is not None else '—'}R "
                  f"se={('%.4f' % mp['se']) if mp.get('se') else '—'} │ "
                  f"M-D: net={('%.4f' % md['net_r_per_day']) if md.get('net_r_per_day') is not None else '—'} "
                  f"مأخوذة={md.get('taken')} قُصَّ={md.get('rejected_cap')}")
    S.log("")
    S.log("═══ 📏 القوّة (من المقيس لا المُقدَّر) ═══")
    # 🔒 تُقاس على **نفس المجتمع الذي يحكم به الفرق النافذ** (‏`-X`) — وإلّا كان
    #    الـ`MDE` المطبوع عن عيّنةٍ أوسع من التي يُقارَن بها الأثر، فيُقرأ متفائلًا.
    for key in ("E0", "E1C"):
        if key in arms:
            mp = per_trade_expectancy(exclude_catalog(arms[key])[0])
            pw = probe_power(mp.get("r_units") or [])
            S.log(f"   {key}-X: sd={pw.get('sd')} se={pw.get('se')} "
                  f"MDE={pw.get('mde_1side')}")
    S.log("")
    S.log("═══ ⚖️ الفرق النافذ: E1C-X مقابل E0-X ═══")
    a, b = report.get("E1C-X", {}).get("MP"), report.get("E0-X", {}).get("MP")
    if a and b and a.get("mean") is not None and b.get("mean") is not None:
        z = z_diff(a, b)
        S.log(f"   Δ = {a['mean'] - b['mean']:+.4f}R · z = "
              f"{('%.2f' % z) if z is not None else '—'} "
              f"(الحدّ {Z_MIN}) · n = {a['n']} مقابل {b['n']} (الحدّ {MIN_TRADES})")
    else:
        S.log("   ⛔ لا حكم — عيّنةٌ ناقصة بأحد الطرفين")
    S.log("")
    S.log("⚠️ حدود صدق: انحياز بقاء · تشويه تقسيمات · بلا افتر · والكاتالوج "
          "اختيارٌ لاحقٌ للحدث ⇒ الحكم **وصفيٌّ داخل العيّنة** لا معدَّل ربحية.")
    out = os.environ.get("ENV_BT_OUT", "")
    if out:
        try:
            with open(out, "w", encoding="utf-8") as fh:
                json.dump({"year": year, "edges_fp": fp, "n_sessions": n_sessions,
                           "anchors": anch, "manifest_ok": man["ok"],
                           "report": report}, fh, ensure_ascii=False, indent=1)
            S.log(f"📝 كُتب {out}")
        except Exception as e:                                    # noqa: BLE001
            S.log(f"⚠️ تعذّرت الكتابة: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
