#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📦 T-CAP — **ذراعا السعة** (`cap_prereg.md`): ماذا يتغيّر لو صارت خانات
القائمة 15 بدل 10 — **بسياسة NF8 الحيّة مفعَّلةً في الذراعين**؟

**ذراعان لا ثالثة** (‏§①): `C10` (الحيّة) · `C15` (سعةُ أداة المحفظة المنشورة).
**بوّابةُ الصلاحية:** `C10` يعيد أرقام T-SLOT لذراع `S-NF8` حرفيًّا.
🔒 بحث/قياس — صفر مسّ إنتاج. النتائج تُطبَع للسجلّ.
"""
from __future__ import annotations

import os
import sys

os.environ["SCREENER_MODE"] = "BACKTEST"
os.environ["BT_REPLAY10"] = "1"
os.environ["BT_ENVVALS"] = "1"
os.environ["BT_POTENTIAL"] = "1"

import replay10 as RP                                          # noqa: E402
import slot_arms as SL                                         # noqa: E402
import Super_stock as S                                        # noqa: E402

CAPS = (10, 15)                      # §①: ذراعان — ولا ثالثة
R_GUARD = 0.05
# §① بوّابة الصلاحية: (d50 خام، d50_adj) لذراع S-NF8 من T-SLOT حرفيًّا
EXPECT_NF8 = {"2024": (35, 26), "2025": (30, 19), "2026": (15, 11)}


def _arm(cands, outcome_of, n_sessions, expl, idx, cap):
    k = int(S.CONFIG["SLOT_UNFILLED_FREE_SESSIONS"])   # مصدرٌ واحد (الإنتاج)
    res = RP.replay(cands, outcome_of=outcome_of, ranker=RP.rank_live,
                    sessions=range(0, n_sessions), capacity=cap,
                    free_of=RP.make_free_unfilled(k, idx))
    taken = res["taken"]
    rs = [v for v in (RP.r_unit(c.payload) for c in taken) if v is not None]
    late = [c for c in taken if SL.is_late(c, idx, k)]
    return {"res": res, "taken": taken, "n": len(taken),
            "d50": SL.delivered(taken, expl),
            "d100": SL.delivered(taken, 100.0),
            "late_n": len(late), "d50_late": SL.delivered(late, expl),
            "d100_late": SL.delivered(late, 100.0),
            "per_trade": (sum(rs) / len(taken)) if taken else 0.0}


def run() -> int:
    trades = S.run_backtest() or []
    year = (os.environ.get("BACKTEST_YEAR", "") or "?").strip()
    print(f"\n{'=' * 72}\n📦 T-CAP — ذراعا السعة (بسياسة NF8) · السنة {year}\n"
          f"{'=' * 72}")
    with_fields = [t for t in trades if t.get("exit_date")]
    with_band = [t for t in with_fields
                 if isinstance(t.get("env_vals"), dict)
                 and "in_band" in t["env_vals"]]
    with_mg = [t for t in with_fields if t.get("mg_outcome") is not None]
    with_fd = [t for t in with_fields if "fill_date" in t]
    print(f"صفقات: {len(trades)} · إعادة: {len(with_fields)} · نطاق: "
          f"{len(with_band)} · حركة: {len(with_mg)} · تعبئة: {len(with_fd)}")
    if not with_fields:
        print("⛔ `BT_REPLAY10` خامل ⇒ no-op.")
        return 2
    if not with_band or not with_mg or not with_fd:
        print("⛔ حقلٌ لازم غائب (نطاق/حركة/تعبئة) ⇒ no-op.")
        return 4

    cands, idx, outcome_of = RP.candidates_from_trades(
        with_fields, extra_dates=[t.get("fill_date") for t in with_fields])
    n_sessions = len(idx)
    expl = float(S.CONFIG["EXPLOSION_PCT"])
    print(f"⚖️ الميزانية: جلسات = {n_sessions} · NF8 k = "
          f"{S.CONFIG['SLOT_UNFILLED_FREE_SESSIONS']} · المُرتِّب rank_live "
          f"· الأذرع = سعة {CAPS[0]} وسعة {CAPS[1]}")

    arms = {c: _arm(cands, outcome_of, n_sessions, expl, idx, c) for c in CAPS}

    exp = EXPECT_NF8.get(year)
    a10 = arms[10]
    if exp is not None:
        got = (a10["d50"], a10["d50"] - a10["d50_late"])
        if got != exp:
            print(f"⛔ بوّابةُ الصلاحية سقطت: C10 (خام، معدَّل) = {got} "
                  f"والمتوقَّع من T-SLOT = {exp} ⇒ الأداة معطوبة — توقّف.")
            return 9
        print(f"🧪 بوّابةُ الصلاحية ✅: C10 يعيد أرقام S-NF8 حرفيًّا {exp}.")
    else:
        print("🧪 بوّابةُ الصلاحية: سنةٌ خارج الخريطة — تُتخطّى بإعلان.")

    print(f"\n📊 الذراعان (المقياسُ الأساسيّ أوّلًا):")
    for c, a in arms.items():
        adj50 = a["d50"] - a["d50_late"]
        adj100 = a["d100"] - a["d100_late"]
        print(f"  C{c}: منفجرون {expl:g}%+ = {a['d50']} ⟶ معدَّل = {adj50} "
              f"(‏100%+ = {a['d100']} ⟶ {adj100}) · مأخوذة = {a['n']} · "
              f"مرفوض بالسعة = {a['res']['rejected_cap']} · "
              f"R/صفقة = {a['per_trade']:+.4f}")

    a15 = arms[15]
    adj10 = a10["d50"] - a10["d50_late"]
    adj15 = a15["d50"] - a15["d50_late"]
    print("\n🧭 قراءاتُ §② لهذي السنة (الحكمُ عبر الثلاث):")
    print(f"  d50_adj: C15 = {adj15} مقابل C10 = {adj10} "
          f"{'✅ أكثر' if adj15 > adj10 else ('= مساوٍ' if adj15 == adj10 else '🔴 أقلّ')}")
    print(f"  حارسُ العائد (C15 − C10): "
          f"{a15['per_trade'] - a10['per_trade']:+.4f}R (الحدّ −{R_GUARD:g})")
    print("\n⚠️ حدودُ الصدق (‏§④): كما في T-SLOT · و15 مركزًا حيًّا عبءُ متابعةٍ "
          "ومخاطرةٍ لا يقيسهما الباكتيست — القرارُ للمالك حصريًّا.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
