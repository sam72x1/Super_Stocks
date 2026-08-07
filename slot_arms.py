#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🪑 T-SLOT — **أذرعُ سياسة الخانات** (`slot_prereg.md`): هل تحريرُ خانة «غير
المُعبَّأ» مبكّرًا (مع بقائه متابَعًا) يُسلّم منفجرين أكثر؟

**الأذرعُ الثلاث مثبَّتةٌ قبل أيّ رقم** (‏§③): `S-LIVE` (الأساس) · `S-NF5`
(‏إيقاع التجديد الأسبوعيّ) · `S-NF8` (سقف «ثبات الدعم 3-8» عند فيصل). **ولا
رابعة.** المُرتِّبُ مثبَّت على `rank_live` في الكلّ ⇒ المتغيّرُ سياسةُ الخانة وحدها.

**بوّابةُ الصلاحية الحاكمة** (‏§②): `S-LIVE` يجب أن يُعيد إنتاج أرقام T-RANKER2
لذراع `K-LIVE` حرفيًّا (‏2024=22 · 2025=14 · 2026=6) وإلّا فالأداة معطوبة.

**التعديلُ الصادق** (‏§④): `d50_adj` = المُسلَّمون ناقصَ منفجري التعبئة المتأخّرة
(تفاؤلُ «عدم إعادة الشحن» يُحاسَب عليه الذراع).

🔒 **بحث/قياس — صفر مسّ إنتاج.** النتائج تُطبَع للسجلّ.
"""
from __future__ import annotations

import os
import sys

# ⚠️ قبل الاستيراد — وإلّا خرجت الأعلام خاملة (بصمة الـno-op الموثّقة).
os.environ["SCREENER_MODE"] = "BACKTEST"
os.environ["BT_REPLAY10"] = "1"      # تاريخا الخروج والتعبئة
os.environ["BT_ENVVALS"] = "1"       # `in_band` — بلاه `rank_live` no-op
os.environ["BT_POTENTIAL"] = "1"     # 🔴 إلزاميّ: المقياس يقرأ mg_pre_stop

import replay10 as RP                                          # noqa: E402
import Super_stock as S                                        # noqa: E402

NF_ARMS = (5, 8)                     # §③: المهلتان المسجَّلتان — ولا ثالثة
R_GUARD = 0.05                       # §④-4: حارسُ العائد
EXPECT_LIVE = {"2024": 22, "2025": 14, "2026": 6}   # §②: بوّابة الصلاحية


def delivered(taken, thr: float) -> int:
    """عددُ المأخوذين البالغين `thr`% قبل وقفهم (نفس عدّاد T-RANKER2)."""
    n = 0
    for c in taken:
        t = c.payload
        if t.get("mg_outcome") in (None, "no_fill"):
            continue
        try:
            if float(t.get("mg_pre_stop") or 0.0) >= thr:
                n += 1
        except (TypeError, ValueError):
            continue
    return n


def is_late(c, idx, k: int) -> bool:
    """هل تعبئةُ هذا المأخوذ **متأخّرة** عن مهلة `k`؟ (تعبّأ فعلًا لكن بعد أن
    حُرِّرت خانتُه — موضعُ تفاؤل «عدم إعادة الشحن» الذي يحاسبه `d50_adj`).
    نفسُ حدود `make_free_unfilled` حرفيًّا لكن مشروطًا بوقوع تعبئةٍ فعلية."""
    t = c.payload
    if t.get("outcome") == "no_fill" or t.get("fill_date") is None:
        return False
    fs = idx.get(str(t["fill_date"]))
    return fs is None or fs - c.session > int(k)


def _arm(cands, outcome_of, n_sessions, expl, idx, k=None):
    fo = RP.make_free_unfilled(k, idx) if k is not None else None
    res = RP.replay(cands, outcome_of=outcome_of, ranker=RP.rank_live,
                    sessions=range(0, n_sessions), free_of=fo)
    taken = res["taken"]
    rs = [v for v in (RP.r_unit(c.payload) for c in taken) if v is not None]
    late = [c for c in taken if k is not None and is_late(c, idx, k)]
    return {"res": res, "taken": taken, "n": len(taken),
            "d50": delivered(taken, expl), "d100": delivered(taken, 100.0),
            "late_n": len(late), "d50_late": delivered(late, expl),
            "d100_late": delivered(late, 100.0),
            "total_r": sum(rs),
            "per_trade": (sum(rs) / len(taken)) if taken else 0.0}


def run() -> int:
    trades = S.run_backtest() or []
    year = (os.environ.get("BACKTEST_YEAR", "") or "?").strip()
    print(f"\n{'=' * 72}\n🪑 T-SLOT — أذرعُ سياسة الخانات · السنة {year}\n"
          f"{'=' * 72}")

    # ── ✅ «أثبت أن التجربة اشتغلت» ──
    with_fields = [t for t in trades if t.get("exit_date")]
    with_band = [t for t in with_fields
                 if isinstance(t.get("env_vals"), dict)
                 and "in_band" in t["env_vals"]]
    with_mg = [t for t in with_fields if t.get("mg_outcome") is not None]
    with_fd = [t for t in with_fields if "fill_date" in t]
    print(f"صفقات المحرّك: {len(trades)} · بحقول الإعادة: {len(with_fields)} · "
          f"بحقل النطاق: {len(with_band)} · بحقول الحركة: {len(with_mg)} · "
          f"بحقل التعبئة: {len(with_fd)}")
    if not with_fields:
        print("⛔ `BT_REPLAY10` **خامل** ⇒ no-op — لا تُفسَّر النتيجة.")
        return 2
    if not with_band:
        print("⛔ `in_band` غائب ⇒ `rank_live` no-op — لا تُفسَّر النتيجة.")
        return 4
    if not with_mg:
        print("⛔ `BT_POTENTIAL` خامل ⇒ المقياسُ الأساسيّ مفبرك — توقّف.")
        return 7
    if not with_fd:
        print("⛔ حقلُ `fill_date` غائب ⇒ أذرعُ المهلة عمياء عن التعبئة "
              "المتأخّرة = no-op — لا تُفسَّر النتيجة.")
        return 8

    cands, idx, outcome_of = RP.candidates_from_trades(
        with_fields, extra_dates=[t.get("fill_date") for t in with_fields])
    n_sessions = len(idx)
    expl = float(S.CONFIG["EXPLOSION_PCT"])
    print(f"\n⚖️ الميزانية: صفقات = {len(with_fields)} · جلسات فهرسية (مع تواريخ "
          f"التعبئة) = {n_sessions} · السعة = {RP.CAPACITY} · المُرتِّب مثبَّت = "
          f"rank_live · نافذة الحسم = {S.CONFIG['BACKTEST_FORWARD_DAYS']} جلسة")

    live = _arm(cands, outcome_of, n_sessions, expl, idx, k=None)

    # ── 🧪 بوّابةُ الصلاحية الحاكمة (‏§②) قبل قراءة أيّ ذراع ──
    exp = EXPECT_LIVE.get(year)
    if exp is not None:
        if live["d50"] != exp:
            print(f"⛔ بوّابةُ الصلاحية سقطت: S-LIVE d50={live['d50']} والمتوقَّع "
                  f"من T-RANKER2 = {exp} ⇒ الأداةُ معطوبة — لا تُقرأ الأذرع.")
            return 9
        print(f"🧪 بوّابةُ الصلاحية ✅: S-LIVE يعيد رقم T-RANKER2 حرفيًّا "
              f"(‏d50={exp}).")
    else:
        print("🧪 بوّابةُ الصلاحية: سنةٌ خارج خريطة T-RANKER2 — تُتخطّى بإعلان.")

    arms = {"S-LIVE": live}
    for k in NF_ARMS:
        arms[f"S-NF{k}"] = _arm(cands, outcome_of, n_sessions, expl, idx, k=k)

    # ── تشخيصُ الهدر (‏§④-3): حصّة غير المُعبَّأ من أيام الخانات في الأساس ──
    dead = tot = 0
    for c in live["taken"]:
        _, held = outcome_of(c)
        tot += max(int(held), 0)
        if c.payload.get("outcome") == "no_fill":
            dead += max(int(held), 0)
    print(f"\n🪦 هدرُ الأساس: غيرُ المُعبَّأ يستهلك {dead} من {tot} يوم-خانة "
          f"({dead / tot * 100.0 if tot else 0.0:.0f}%) — تقديرًا بمدد الحسم.")

    print(f"\n📊 الأذرع (سعة {RP.CAPACITY} · المقياسُ الأساسيّ أوّلًا):")
    for tag, a in arms.items():
        adj50 = a["d50"] - a["d50_late"]
        adj100 = a["d100"] - a["d100_late"]
        extra = (f" · متأخّرة = {a['late_n']} · d50_adj = {adj50} "
                 f"(‏100%+ معدَّل = {adj100})" if tag != "S-LIVE" else "")
        print(f"  {tag}: منفجرون مُسلَّمون {expl:g}%+ = {a['d50']} "
              f"(‏100%+ = {a['d100']}) · مأخوذة = {a['n']} · "
              f"R/صفقة = {a['per_trade']:+.4f} · مرفوض بالسعة = "
              f"{a['res']['rejected_cap']} · أيام-خانات = {a['res']['slot_days']}"
              + extra)

    print("\n🧭 قراءاتُ §⑤ لهذي السنة (الحكمُ عبر السنوات الثلاث):")
    for k in NF_ARMS:
        a = arms[f"S-NF{k}"]
        adj = a["d50"] - a["d50_late"]
        print(f"  S-NF{k}: d50_adj={adj} مقابل الأساس {live['d50']} "
              f"{'✅ أكثر' if adj > live['d50'] else ('= مساوٍ' if adj == live['d50'] else '🔴 أقلّ')}"
              f" · حارسُ العائد = {a['per_trade'] - live['per_trade']:+.4f}R "
              f"(الحدّ −{R_GUARD:g})")

    print("\n⚠️ حدودُ الصدق (‏§⑦): عيّناتٌ صغيرة · مِشيةٌ متفرّقة · 2026 جزئية · "
          "«عدمُ إعادة شحن» المتأخّر تفاؤلٌ يقيَّد بـd50_adj ولا يُمحى · والحجزُ "
          "الحيّ غيرُ محدود بينما النافذة هنا 40 جلسة ⇒ المقيسُ أرضيةُ الهدر.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
