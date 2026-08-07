#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🚦 T-RANKER2 — **أذرعُ الترتيب الكامل** بعد ثبوت عنق الزجاجة (`ranker2_prereg.md`).

**السؤال المسجَّل** (‏§①): من 71 بالغَ +100% في بِركة العشرين وصل **‏21% فقط**
لخانات المحفظة (ملحق ⑨) — فأيُّ ترتيبٍ يُسلّم أكثرَ منفجري البِركة إلى خانات
السعة الحيّة (‏10)؟

**الأذرعُ الخمس مثبَّتةٌ قبل أيّ رقم** (‏§③): `K-LIVE` مُرتِّبُ الإنتاج الحاليّ
(داخل النطاق أوّلًا) · `K-LEGACY` ما قبل T-PROX · `K-ENV` عمقُ الظرف مفتاحًا
أوّلًا · `K-FIFO` · `K-RAND` ×200 (**شاهدُ الضبط الحاسم**). **ولا ذراعَ سادسة.**

**المقياسُ الأساسيّ** (‏§④): «المنفجرون المُسلَّمون» = مأخوذون بلغوا
`EXPLOSION_PCT` قبل وقفهم (‏`mg_pre_stop`) — وحارسُ العائد `r_unit`.

⚖️ **الميزانيةُ الثابتة:** الأذرعُ كلُّها تقرأ **نفس قائمة الصفقات** من تشغيلةِ
باكتيستٍ واحدة ⇒ نفسُ اللقطة والكون والسعة والنافذة **بالبناء**، وتُطبَع القيود.

🔒 **بحث/قياس — صفر مسّ إنتاج.** يشغّل `run_backtest` الإنتاجيّ نفسَه، والنتائج
**تُطبَع للسجلّ** (تنزيل الـartifacts محجوب بسياسة الشبكة).
"""
from __future__ import annotations

import os
import sys

# ⚠️ **قبل الاستيراد**: `_apply_backtest_overrides` يُنفَّذ وقت تحميل الوحدة —
# الضبطُ بعده يصل متأخّرًا والعلمُ يخرج خاملًا (بصمة الـno-op الموثّقة: `BT_CANDLE`).
os.environ["SCREENER_MODE"] = "BACKTEST"
os.environ["BT_REPLAY10"] = "1"      # تاريخُ الخروج (تحرير الخانة بجلسات)
os.environ["BT_ENVVALS"] = "1"       # قيمُ الظرف + `in_band` — بلاها ذراعان no-op
os.environ["BT_POTENTIAL"] = "1"     # 🔴 إلزاميّ: المقياسُ الأساسيّ يقرأ mg_pre_stop

import catalog_envelope as CE                                  # noqa: E402
import envelope_scan as EV                                     # noqa: E402
import ranker_tie_arms as RT                                   # noqa: E402
import replay10 as RP                                          # noqa: E402
import Super_stock as S                                        # noqa: E402

SEEDS = int(os.environ.get("R2_SEEDS", "200"))       # §③: 200 خلطة كما سُجِّل
R_GUARD = 0.05                                       # §④-2: حارسُ العائد لكلّ صفقة


def delivered(taken, thr: float) -> int:
    """عددُ المأخوذين الذين بلغوا `thr`% من دخولهم **قبل وقفهم** (‏`mg_pre_stop`).
    غيرُ المُعبَّأ (`no_fill`/غائب) لا يُعدّ — لكنه **استهلك خانةً** وأثرُه في
    إزاحة غيره (وهذا بعينه ما تقيسه آلةُ `replay10`)."""
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


def _arm(cands, outcome_of, ranker, n_sessions, expl, ):
    res = RP.replay(cands, outcome_of=outcome_of, ranker=ranker,
                    sessions=range(0, n_sessions))
    taken = res["taken"]
    rs = [v for v in (RP.r_unit(c.payload) for c in taken) if v is not None]
    return {"res": res, "taken": taken, "n": len(taken),
            "d50": delivered(taken, expl), "d100": delivered(taken, 100.0),
            "total_r": sum(rs),
            "per_trade": (sum(rs) / len(taken)) if taken else 0.0}


def run() -> int:
    trades = S.run_backtest() or []
    year = (os.environ.get("BACKTEST_YEAR", "") or "?").strip()
    print(f"\n{'=' * 72}\n🚦 T-RANKER2 — أذرعُ الترتيب الكامل · السنة {year}\n"
          f"{'=' * 72}")

    # ── ✅ «أثبت أن التجربة اشتغلت» قبل تفسير أيّ رقم ──
    with_fields = [t for t in trades if t.get("exit_date")]
    with_vals = [t for t in with_fields if isinstance(t.get("env_vals"), dict)]
    with_band = [t for t in with_vals if "in_band" in t["env_vals"]]
    with_mg = [t for t in with_fields if t.get("mg_outcome") is not None]
    print(f"صفقات المحرّك: {len(trades)} · بحقول الإعادة: {len(with_fields)} · "
          f"بقيم الظرف: {len(with_vals)} · بحقل النطاق: {len(with_band)} · "
          f"بحقول الحركة: {len(with_mg)}")
    if not with_fields:
        print("⛔ `BT_REPLAY10` **خامل** ⇒ no-op — لا تُفسَّر النتيجة.")
        return 2
    if not with_vals or not with_band:
        print("⛔ `BT_ENVVALS`/`in_band` **غائب** ⇒ ذراعا `K-LIVE`/`K-ENV` "
              "no-op — لا تُفسَّر النتيجة.")
        return 4
    if not with_mg:
        print("⛔ `BT_POTENTIAL` **خامل** ⇒ «المنفجرون المُسلَّمون» صفرٌ مفبرك "
              "— لا تُفسَّر النتيجة.")
        return 7
    mism = [t for t in with_fields if t.get("exit_kind") != t.get("outcome")]
    print(f"تطابق محرّك الخروج مع محرّك الحسم: {len(with_fields) - len(mism)}"
          f"/{len(with_fields)}" + (f" · ⛔ تفرّق={len(mism)}" if mism else " ✅"))
    if mism:
        return 3

    edges = EV.load_edges()
    if not edges:
        print("⛔ حوافُّ الظرف غير محمَّلة ⇒ `K-ENV` بلا مرجع — لا تُشغَّل.")
        return 5
    sides = {n: sd for n, sd, _, _ in CE.CRITERIA}
    diag = RT.attach_env_depth(with_fields, edges, sides)
    print(f"عمقُ الظرف: محسوبٌ لـ{diag['ok']} · امتناع {diag['abstain']} · "
          f"بلا قيم {diag['no_vals']} · وسيطُ المعايير {diag['median_criteria']}")
    if diag["ok"] == 0:
        print("⛔ امتنع العمقُ عن الكلّ ⇒ `K-ENV` ≡ `K-LEGACY` بالبناء = no-op.")
        return 6

    cands, idx, outcome_of = RP.candidates_from_trades(with_fields)
    n_sessions = len(idx)
    expl = float(S.CONFIG["EXPLOSION_PCT"])
    pool50 = sum(1 for t in with_fields
                 if t.get("mg_outcome") not in (None, "no_fill")
                 and float(t.get("mg_pre_stop") or 0) >= expl)
    pool100 = sum(1 for t in with_fields
                  if t.get("mg_outcome") not in (None, "no_fill")
                  and float(t.get("mg_pre_stop") or 0) >= 100.0)
    print("\n⚖️ الميزانيةُ الثابتة (‏§②):")
    for ln in RT._budget_lines(trades, cands, n_sessions):
        print(ln)
    print(f"  بِركةُ المنفجرين (كلُّ المُعبَّئين): {expl:g}%+ = {pool50} · "
          f"‏100%+ = {pool100}")

    # ── الأذرعُ الخمس على نفس البِركة (‏§③ — ولا سادسة) ──
    arms = {
        "K-LIVE  ": _arm(cands, outcome_of, RP.rank_live, n_sessions, expl),
        "K-LEGACY": _arm(cands, outcome_of, RP.rank_actual, n_sessions, expl),
        "K-ENV   ": _arm(cands, outcome_of, RP.rank_env_full, n_sessions, expl),
        "K-FIFO  ": _arm(cands, outcome_of, RP.rank_fifo, n_sessions, expl),
    }
    rand = [_arm(cands, outcome_of, RP.make_rank_random(sd), n_sessions, expl)
            for sd in range(1, SEEDS + 1)]

    print(f"\n📊 الأذرع (سعة {RP.CAPACITY} · المقياسُ الأساسيّ أوّلًا):")
    for tag, a in arms.items():
        print(f"  {tag}: منفجرون مُسلَّمون {expl:g}%+ = {a['d50']} "
              f"(‏100%+ = {a['d100']}) · مأخوذة = {a['n']} · "
              f"R/صفقة = {a['per_trade']:+.4f} · إجمالي R = {a['total_r']:+.1f} "
              f"· مرفوض بالسعة = {a['res']['rejected_cap']}")
    r50 = sorted(x["d50"] for x in rand)
    r100 = sorted(x["d100"] for x in rand)
    rpt = [x["per_trade"] for x in rand]
    print(f"  K-RAND ×{len(rand)}: منفجرون {expl:g}%+ متوسط = "
          f"{sum(r50) / len(r50):.2f} ‏[p05={RP._pct(r50, .05):g}, "
          f"وسيط={RP._pct(r50, .50):g}, p90={RP._pct(r50, .90):g}, "
          f"p95={RP._pct(r50, .95):g}] · ‏100%+ متوسط = {sum(r100) / len(r100):.2f}"
          f" · R/صفقة متوسط = {sum(rpt) / len(rpt):+.4f}")

    # ── موقعُ كلّ ذراعٍ من حزام العشوائيّ (‏§④-3) ──
    print("\n🎲 المئينُ داخل حزام العشوائيّ (على المنفجرين المُسلَّمين):")
    for tag, a in arms.items():
        pct = sum(1 for v in r50 if v < a["d50"]) / len(r50) * 100.0
        med = RP._pct(r50, .50)
        p90 = RP._pct(r50, .90)
        pos = ("فوق p90 ✅" if a["d50"] > p90 else
               ("دون الوسيط 🔴" if a["d50"] < med else "داخل الحزام"))
        print(f"  {tag}: d50={a['d50']} · مئين ≈ {pct:.0f}% · {pos}")

    # ── بوّابةُ القرار لهذي السنة (‏§⑤ — الحكمُ النهائيّ يلزمه الثلاث) ──
    live, leg, env = arms["K-LIVE  "], arms["K-LEGACY"], arms["K-ENV   "]
    print("\n🧭 قراءاتُ §⑤ لهذي السنة (الحكمُ عبر السنوات الثلاث):")
    print(f"  K-ENV مقابل K-LIVE (المنفجرون): {env['d50']} مقابل {live['d50']} "
          f"{'✅ أكثر' if env['d50'] > live['d50'] else ('= مساوٍ' if env['d50'] == live['d50'] else '🔴 أقلّ')}")
    print(f"  K-LIVE مقابل K-LEGACY (تحقيق T-PROX): {live['d50']} مقابل "
          f"{leg['d50']} "
          f"{'✅' if live['d50'] >= leg['d50'] else '🔴 أقلّ — قراءة التراجع تُفحَص'}")
    print(f"  حارسُ العائد (K-ENV − K-LIVE): "
          f"{env['per_trade'] - live['per_trade']:+.4f}R/صفقة "
          f"(الحدّ −{R_GUARD:g})")

    print("\n⚠️ حدودُ الصدق كما سُجِّلت (‏§⑦): عيّناتٌ صغيرة فحزامُ العشوائيّ هو "
          "الحكم · مِشيةٌ متفرّقة (سؤالُ الإشغال عبر الأيام لا التعادل اليوميّ) · "
          "2026 جزئية · 2025/2026 داخل-العيّنة للبوّابات (مشتركةٌ بين الأذرع) · "
          "سعة 10 هنا مقابل 15 في ملحق ⑨ فلا تُقارَن الأعداد عبرهما.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
