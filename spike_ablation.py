#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧪 `T-SPIKE-ABLATION` — المرحلة صفر: هل الظرفُ أحدَ عشر معيارًا أم واحدٌ بأحدَ عشر اسمًا؟

**العقد:** `spike_ablation_prereg.md` (مدفوعٌ قبل أيّ رقم).

**الطريقة:** لكل (رمز، جلسة) في شبكة القياس ⟶ نداءُ `measure` **مرّةً واحدة** (وهو
الغالي: `analyze_ticker` مُرخى) ⟶ ثم تُختبَر **كلُّ** الأذرع على **الصفّ نفسه**
بـ`inside_envelope` الإنتاجيّة ⇒ **صفرُ نداءٍ إضافيّ لأيّ ذراع.**

🔒 **بحث/قياس فقط:** لا يُستورَد في أيّ مسار إنتاج · لا يمسّ الجذور · لا يكتب حالة ·
لا تلغرام · ولقطةٌ مجمَّدة إلزامية.

⚠️ **`chase_ok` (‏D11) و`M13`/`M14` مُستبعَدةٌ ويُصرَّح بذلك** (‏§③ بالتسجيل): تُطبَّق
بالتساوي على كل الأذرع فتُختصر من النسبة `w` رياضيًّا، وإدخالُها = نداءُ شبكةٍ لكل
رمزٍ على الكون الكامل. ⇒ **`w` دقيقٌ بلا نقصان.**
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time

# ⚠️ قبل الاستيراد حصرًا (`_apply_backtest_overrides` يُنفَّذ وقت التحميل).
os.environ["SCREENER_MODE"] = "BACKTEST"

import catalog_envelope as CE                                     # noqa: E402
import envelope_scan as ES                                        # noqa: E402
import Super_stock as S                                           # noqa: E402

# ── ثوابتُ التسجيل (‏§⑥) — مجمَّدة ────────────────────────────────────────────
EDGES_FP = "2dc8c7afb0db"
GRID_SESSIONS = 20            # نفسُ `denominator_sessions`
COVERAGE_MIN = 0.60           # حارس A5
W_CLOSE = 0.90                # ‏≥ ⇒ يُغلَق المحور
W_INDEPENDENT = 0.50          # ‏≤ ⇒ مضمونٌ مستقلّ

# الأذرع الرئيسة (‏§③) — مثبَّتةٌ قبل أيّ رقم
ARM_S1 = ("best_spike",)
ARM_S2 = ("price", "best_spike")
ARM_S5 = ("price", "best_spike", "drop_pct", "base_range")


def _keys():
    return [k for k, _, _, _ in CE.CRITERIA]


def subset(edges: dict, keys) -> dict:
    """ظرفٌ جزئيّ: **نفسُ قيم الحوافّ**، مفاتيحُ أقلّ. و`inside_envelope` تتخطّى الغائب."""
    return {k: edges[k] for k in keys if k in edges}


def eval_arms(row: dict, edges: dict, arms: dict) -> dict:
    """يختبر كلَّ ذراعٍ على **الصفّ نفسه** — صفرُ نداءٍ إضافيّ."""
    return {name: bool(CE.inside_envelope(row, env)) for name, env in arms.items()}


def build_arms(edges: dict) -> dict:
    """الرئيسةُ الأربع + `ALONE[c]` + `LOO[c]` للأحد عشر (‏§③)."""
    ks = _keys()
    arms = {
        "S1": subset(edges, ARM_S1),
        "S2": subset(edges, ARM_S2),
        "S5": subset(edges, ARM_S5),
        "S12": subset(edges, ks),
    }
    for c in ks:
        arms["ALONE:" + c] = subset(edges, (c,))
        arms["LOO:" + c] = subset(edges, [k for k in ks if k != c])
    return arms


def grid_sessions(df, n=GRID_SESSIONS):
    """آخرُ `n` جلسة — فهارسُها في الإطار (لا تواريخ، فالقصّ بالفهرس)."""
    total = len(df)
    if total < int(S.CONFIG["MIN_BARS"]) + 1:
        return []
    start = max(int(S.CONFIG["MIN_BARS"]), total - n)
    return list(range(start, total))


def run() -> int:
    path = os.environ.get("BT_FROZEN_PATH", "").strip()
    if not path:
        S.log("⛔ `BT_FROZEN_PATH` إلزاميّ (لقطةٌ مجمَّدة).")
        return 2

    edges = ES.load_edges()
    if not edges:
        S.log("⛔ حوافُّ الظرف غائبة — لا قرار.")
        return 2
    meta = edges.get("_meta") or {}
    fp = ES.edges_fingerprint(edges)
    src = str(meta.get("source") or "")
    S.log(f"🧪 T-SPIKE-ABLATION · حوافّ {fp} · لقطة {meta.get('snapshot')} · "
          f"{meta.get('n_symbols')} رمزًا · مُستبعَدون "
          f"{sorted((meta.get('excluded') or {}).keys())}")
    # حارس A3
    if not src.startswith("مُخرَجٌ آليّ") or fp != EDGES_FP:
        S.log(f"⛔ A3: الحوافُّ غيرُ مُصرَّحٍ بها (وسم «{src}» · بصمة {fp} ≠ {EDGES_FP}).")
        return 5

    body = {k: v for k, v in edges.items() if k != "_meta"}
    cfg_keys = sorted(CE.RELAX_ALL)
    before = hashlib.sha256(json.dumps(
        {k: S.CONFIG.get(k) for k in cfg_keys}, sort_keys=True,
        default=str).encode()).hexdigest()

    hist, splits_map, asof = S.load_frozen_dataset(path)
    if not hist:
        S.log("⛔ تعذّر تحميل اللقطة.")
        return 2
    S.log(f"📦 اللقطة as-of {asof} · {len(hist)} رمزًا · شبكة آخر {GRID_SESSIONS} جلسة")

    arms = build_arms(body)
    S.log(f"🎯 الأذرع: {len(arms)} — الرئيسة 4 · ALONE {len(_keys())} · "
          f"LOO {len(_keys())}")

    catalog = set(CE.CATALOG)
    counts = {name: 0 for name in arms}
    rows_measured = 0
    seen_syms, skipped = 0, {"short": 0, "catalog": 0, "no_row": 0, "error": 0}
    t0 = time.time()

    for sym, df in hist.items():
        if sym in catalog:
            skipped["catalog"] += 1
            continue
        if df is None or len(df) < int(S.CONFIG["MIN_BARS"]) + 1:
            skipped["short"] += 1
            continue
        idxs = grid_sessions(df)
        if not idxs:
            skipped["short"] += 1
            continue
        seen_syms += 1
        for j in idxs:
            try:
                row = CE.measure_session(S, sym, df.iloc[:j + 1])
            except Exception:                                    # noqa: BLE001
                skipped["error"] += 1
                continue
            if not row:
                skipped["no_row"] += 1
                continue
            rows_measured += 1
            for name, hit in eval_arms(row, body, arms).items():
                if hit:
                    counts[name] += 1
        if seen_syms % 250 == 0:
            S.log(f"   … {seen_syms} رمزًا · {rows_measured} صفًّا · "
                  f"{round(time.time() - t0)}ث")

    secs = round(time.time() - t0, 1)
    after = hashlib.sha256(json.dumps(
        {k: S.CONFIG.get(k) for k in cfg_keys}, sort_keys=True,
        default=str).encode()).hexdigest()
    if after != before:
        S.log("⛔ A4: **تسرّبُ إرخاء** — CONFIG لم تعد كما كانت.")
        return 7

    universe = len(hist) - skipped["catalog"]
    cov = (seen_syms / universe) if universe else 0.0
    S.log("")
    S.log(f"🩺 التغطية: {seen_syms} من {universe} رمزًا ({cov*100:.1f}%) · "
          f"{rows_measured} صفًّا مقيسًا · {secs}ث · متخطّى {skipped}")
    if cov < COVERAGE_MIN:
        S.log(f"⛔ A5: التغطية دون {COVERAGE_MIN*100:.0f}% ⇒ لا حكم.")
        return 6

    # ── حارس A1: التداخلُ محتومٌ بالبناء ⇒ نقضُه عطلُ أداة ──────────────────
    c1, c2, c5, c12 = counts["S1"], counts["S2"], counts["S5"], counts["S12"]
    S.log("")
    S.log("═══ 📊 السلسلة المتداخلة ═══")
    S.log(f"   S1  {{best_spike}}                 : {c1}")
    S.log(f"   S2  {{+ price}}                    : {c2}")
    S.log(f"   S5  {{+ drop_pct, base_range}}     : {c5}")
    S.log(f"   S12 (الظرف الكامل)                : {c12}")
    if not (c12 <= c5 <= c2 <= c1):
        S.log("⛔ A1: **التداخلُ منقوض** — عطلُ أداة لا نتيجة.")
        return 4
    if c2 == 0:
        S.log("⛔ A6: مقامٌ صفريّ.")
        return 3

    # ── حارس A2: علمٌ خامل ────────────────────────────────────────────────
    alone = {c: counts["ALONE:" + c] for c in _keys()}
    if c1 == c12 and len(set(alone.values())) == 1:
        S.log("⛔ A2: الأذرعُ لا تُطبَّق فعلًا (‏علمٌ خامل).")
        return 2

    w = c12 / c2
    w1 = (c12 / c1) if c1 else None
    S.log("")
    S.log("═══ ⚖️ الحكم (القراءةُ مثبَّتةٌ قبل الرقم) ═══")
    S.log(f"   w  = |S12|/|S2| = {c12}/{c2} = **{w:.4f}**")
    S.log(f"   w1 = |S12|/|S1| = {c12}/{c1} = "
          + (f"{w1:.4f}" if w1 is not None else "—"))
    if w >= W_CLOSE:
        S.log(f"   🔴 **‏w ≥ {W_CLOSE}** ⇒ العشرةُ **زينة**: الظرفُ معيارٌ واحد يلبس "
              "أحدَ عشر اسمًا ⇒ **يُغلَق محورُ الظرف**، والقرارُ هو موقفُنا من "
              "«المضاعِف المتسلسل».")
    elif w <= W_INDEPENDENT:
        S.log(f"   ✅ **‏w ≤ {W_INDEPENDENT}** ⇒ العشرةُ تُقصي نصفَ ما يقبله المحورُ "
              "الواحد ⇒ للظرف **مضمونٌ مستقلّ** ⇒ تُقترَح المرحلةُ الأولى.")
    else:
        S.log("   ⚖️ **بين الحدّين ⇒ «لا حكم»** — يُنشَر وصفيًّا ولا يُبنى عليه قرار.")

    # ── الشاملة: قوّةُ الإقصاء المنفردة والإسهامُ الحدّيّ ───────────────────
    S.log("")
    S.log("═══ 🔬 لكلّ معيار: منفردًا (ALONE) · وحدّيًّا (LOO) ═══")
    S.log(f"   {'المعيار':<14}{'ALONE':>10}{'ALONE%':>9}{'LOO':>10}"
          f"{'الإسهام الحدّيّ':>16}")
    marg = {}
    for c in sorted(_keys(), key=lambda k: counts["LOO:" + k], reverse=True):
        a = counts["ALONE:" + c]
        lo = counts["LOO:" + c]
        # الإسهامُ الحدّيّ: كم يُقصي هذا المحور **فوق** العشرة الباقية
        m = (lo - c12) / lo if lo else 0.0
        marg[c] = m
        S.log(f"   {c:<14}{a:>10}{a/rows_measured*100:>8.1f}%{lo:>10}"
              f"{m*100:>15.1f}%")
    S.log("")
    top = max(marg, key=marg.get) if marg else None
    zero = [c for c, v in marg.items() if v < 0.01]
    S.log(f"   🥇 أكبرُ إسهامٍ حدّيّ: **{top}** ({marg.get(top, 0)*100:.1f}%)")
    S.log("   🪦 إسهامُها دون 1% (مكرّرةٌ بنيويًّا): "
          + (" · ".join(zero) if zero else "لا شيء"))

    S.log("")
    S.log("⚠️ حدودُ صدقٍ: هذا **بنيةُ القاعدة لا دليلُ ربحية** · انحيازُ بقاء · تشويهُ "
          "تقسيمات · بلا افتر · و`chase_ok`/`M13`/`M14` مُستبعَدةٌ (تُختصر من النسبة).")

    out = os.environ.get("ABL_OUT", "")
    if out:
        try:
            with open(out, "w", encoding="utf-8") as fh:
                json.dump({"edges_fp": fp, "asof": str(asof), "w": w, "w1": w1,
                           "counts": counts, "rows": rows_measured,
                           "symbols": seen_syms, "coverage": cov,
                           "skipped": skipped, "marginal": marg,
                           "seconds": secs}, fh, ensure_ascii=False, indent=1)
            S.log(f"📝 كُتب {out}")
        except Exception as e:                                    # noqa: BLE001
            S.log(f"⚠️ تعذّرت الكتابة: {e}")
    return 0


if __name__ == "__main__":                                       # pragma: no cover
    sys.exit(run())
