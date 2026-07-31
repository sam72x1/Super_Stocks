#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔁 T-REPLAY10 — **المرحلة 2: تشغيل الأذرع** (`replay10_prereg.md` §④-⑦).

**السؤال:** هل ترتيبُنا (`rank_key`) يساوي شيئًا أصلًا؟ ‏10 خانات فقط، فأيُّ يومٍ
مزدحمٍ يعني أن **الترتيب** — لا البوّابات — هو مَن يقرّر ما يصل المالك.

**الأذرع المثبَّتة قبل أي رقم:** `R0` المُرتِّب الفعليّ · `R1` FIFO (شاهد ضبط) ·
`R2` عشوائيّ بآلاف البذور (توزيعُ العدم).
**المقياس المثبَّت:** صافي R لليوم عند إجمالي مخاطرةٍ ثابت، من **عوائد التنفيذ
الفعلية** (`ret_a`) — لا `win_rate` ولا `mg_pre_stop`.

🔒 **بحث/قياس — صفر مسّ إنتاج.** يشغّل **مسار الباكتيست الإنتاجيّ نفسه**
(`run_backtest`) بدل استنساخه، فلا يتفرّق «ما قِيس» عن «ما يُشغَّل». والنتائج
**تُطبَع للسجلّ** لأن تنزيل الـartifacts محجوبٌ بسياسة الشبكة.
"""
from __future__ import annotations

import os
import sys

# ⚠️ **قبل الاستيراد**: `_apply_backtest_overrides` يُنفَّذ وقت تحميل الوحدة ويشترط
# `SCREENER_MODE=BACKTEST` — فالضبط بعد الاستيراد يصل متأخّرًا والعلم يخرج **خاملًا**
# (بصمة الـno-op الموثّقة). لذلك يُضبط هنا حصرًا.
os.environ["SCREENER_MODE"] = "BACKTEST"
os.environ["BT_REPLAY10"] = "1"
# `BT_POTENTIAL` يملأ «الحركة المتاحة قبل الوقف» — مقياسٌ **ثانويّ مسجَّل** (§⑤)
# يُنشَر ولا يحكم. إلحاق حقولٍ فقط، فلا يمسّ اختيارًا ولا حسمًا.
os.environ.setdefault("BT_POTENTIAL", "1")

import replay10 as RP                                          # noqa: E402
import Super_stock as S                                        # noqa: E402

SEEDS = int(os.environ.get("REPLAY10_SEEDS", "10000"))
BOOT = int(os.environ.get("REPLAY10_BOOT", "10000"))
EQUIV = 0.05          # هامش التكافؤ المسجَّل ‏±0.05R/يوم (§⑦-2)


def _sessions_per_month(idx: dict) -> dict:
    """عدد الجلسات الفهرسية في كل شهر — مقام الـ`block bootstrap` الشهريّ."""
    out: dict[str, int] = {}
    for d in idx:
        out[str(d)[:7]] = out.get(str(d)[:7], 0) + 1
    return out


def _arm(cands, outcome_of, ranker, n_sessions):
    # ⚠️ `sessions` **كثيف** (كل جلسات الفهرس لا جلسات المرشّحين وحدها): قرار السعة
    # لا يتغيّر بالكثافة (الخروجات تُصرَّف بشرط `≤ s`)، **لكن `slot_days` مقياسٌ
    # مسجَّل ثانويّ** ويُبخَس بالمسح المتفرّق ⇒ يُقاس على الفهرس كاملًا.
    res = RP.replay(cands, outcome_of=outcome_of, ranker=ranker,
                    sessions=range(0, n_sessions))
    return res, RP.net_r_per_day(res["taken"], n_sessions)


def _secondary(taken, n_sessions):
    """المقاييس الثانوية المسجَّلة (§⑤ — **تُنشَر ولا تحكم**): أقصى تراجع بمنحنى R ·
    ‏CVaR‏5% · عدد المنفجرين المُسلَّمين · وسيط «الحركة المتاحة قبل الوقف»."""
    rs = [(c.payload, RP.r_unit(c.payload)) for c in taken]
    seq = [v for _, v in rs if v is not None]
    eq, peak, dd = 0.0, 0.0, 0.0
    for v in seq:
        eq += v
        peak = max(peak, eq)
        dd = min(dd, eq - peak)
    tail = sorted(seq)[:max(1, len(seq) // 20)] if seq else [0.0]
    mg = sorted(float(t.get("mg_pre_stop")) for t, _ in rs
                if t.get("mg_pre_stop") is not None)
    return {"total_r": sum(seq), "max_dd_r": dd,
            "cvar5": sum(tail) / len(tail),
            "exploded": sum(1 for t, _ in rs if t.get("exploded")),
            "mg_median": (mg[len(mg) // 2] if mg else None)}


def run() -> int:
    trades = S.run_backtest() or []
    year = (os.environ.get("BACKTEST_YEAR", "") or "?").strip()
    print(f"\n{'=' * 72}\n🔁 T-REPLAY10 — الأذرع · السنة {year}\n{'=' * 72}")

    # ✅ «أثبت أن التجربة اشتغلت» قبل تفسير أيّ رقم — علمٌ خاملٌ يُعلَن لا يُفسَّر.
    with_fields = [t for t in trades if t.get("exit_date")]
    print(f"صفقات المحرّك: {len(trades)} · بحقول الإعادة: {len(with_fields)}")
    if not with_fields:
        print("⛔ `BT_REPLAY10` **خامل**: لا صفقة تحمل `exit_date` ⇒ التجربة no-op — "
              "لا تُفسَّر نتيجتها.")
        return 2
    # كاشف تفرّقٍ حيّ: `exit_kind` (من `_arm_a_exit_bar`) يجب أن يطابق `outcome`
    # (من `_resolve_arm`) في **كل** صفقة — القفل في السويّة، وهذا شاهدُه على بياناتٍ حقيقية.
    mism = [t for t in with_fields if t.get("exit_kind") != t.get("outcome")]
    print(f"تطابق محرّك الخروج مع محرّك الحسم: {len(with_fields) - len(mism)}"
          f"/{len(with_fields)}" + (f" · ⛔ تفرّق={len(mism)}" if mism else " ✅"))
    if mism:
        print("⛔ تفرّق المحرّكان ⇒ توقيت تحرير الخانة غير موثوق — لا تُقرأ الأذرع.")
        return 3

    cands, idx, outcome_of = RP.candidates_from_trades(with_fields)
    n_sessions = len(idx)
    spm = _sessions_per_month(idx)
    print(f"مرشّحون: {len(cands)} · جلسات فهرسية: {n_sessions} · أشهر: {len(spm)} "
          f"· السعة: {RP.CAPACITY}")

    # ── R0 · R1 ──
    r0, v0 = _arm(cands, outcome_of, RP.rank_actual, n_sessions)
    r1, v1 = _arm(cands, outcome_of, RP.rank_fifo, n_sessions)
    # ── R2: توزيع العدم ──
    v2 = []
    for sd in range(1, SEEDS + 1):
        res = RP.replay(cands, outcome_of=outcome_of, ranker=RP.make_rank_random(sd))
        v2.append(RP.net_r_per_day(res["taken"], n_sessions))
    v2m = sum(v2) / len(v2)

    def _line(tag, res, val):
        sec = _secondary(res["taken"], n_sessions)
        print(f"  {tag}: صافي R/يوم = {val:+.4f} · مأخوذة={len(res['taken'])} "
              f"· مرفوض بالسعة={res['rejected_cap']} · مكرّر={res['rejected_dup']} "
              f"· أقصى حجم قائمة={res['max_size']} · أيام إشغال={res['slot_days']}")
        print(f"      ثانويّ (يُنشَر ولا يحكم): إجمالي R={sec['total_r']:+.1f} "
              f"· أقصى تراجع={sec['max_dd_r']:+.1f}R · CVaR5%={sec['cvar5']:+.2f}R "
              f"· منفجرون مُسلَّمون={sec['exploded']}"
              + (f" · وسيط الحركة قبل الوقف={sec['mg_median']:g}%"
                 if sec["mg_median"] is not None else ""))

    print("\n📊 الأذرع:")
    _line("R0 (المُرتِّب الفعليّ)", r0, v0)
    _line("R1 (‏FIFO)          ", r1, v1)
    print(f"  R2 (عشوائيّ ×{len(v2)}): متوسط = {v2m:+.4f} "
          f"· ‏[5%,95%] = [{RP._pct(v2, .05):+.4f}, {RP._pct(v2, .95):+.4f}]")

    print("\n📐 الاستدلال المسجَّل:")
    for tag, res in (("R0", r0), ("R1", r1)):
        bb = RP.block_bootstrap_ci(res["taken"], spm, n=BOOT)
        cb = RP.cluster_bootstrap_ci(res["taken"], n_sessions, n=BOOT)
        print(f"  {tag} · block bootstrap شهريّ 95%: [{bb['lo']:+.4f}, {bb['hi']:+.4f}]"
              f" (‏{bb['n']} شهرًا) · cluster بالرمز 95%: [{cb['lo']:+.4f}, "
              f"{cb['hi']:+.4f}] (‏{cb['n']} رمزًا)")
    rt = RP.randomization_test(v0, v2)
    print(f"  randomization (R0 مقابل R2): فرق المتوسط = {rt['d_mean']:+.4f} "
          f"· فاصل 90% = [{rt['d_lo']:+.4f}, {rt['d_hi']:+.4f}] "
          f"· p أحادية = {rt['p_one']:.4f} · p ثنائية = {rt['p_two']:.4f}")

    print("\n🧭 المعيار الثلاثيّ (‏§⑦ — يُقرأ عبر السنوات الثلاث مجتمعةً لا سنةً وحدها):")
    if rt["d_lo"] > 0:
        print("  ① هذي السنة: الحدّ السفليّ للفرق موجب ⇒ **مرشّح تفوّق** "
              "(يلزم موجبًا في الثلاث).")
    elif rt["d_lo"] >= -EQUIV and rt["d_hi"] <= EQUIV:
        print(f"  ② هذي السنة: الفاصل داخل ±{EQUIV}R ⇒ **مرشّح تكافؤ** "
              "(الترتيب لا يضيف).")
    else:
        print(f"  ③ هذي السنة: خارج التفوّق وخارج ±{EQUIV}R ⇒ **غير حاسم** — "
              "لا ادّعاء في أيّ اتجاه.")
    print(f"  🔑 شاهد FIFO: R1−R0 = {v1 - v0:+.4f} "
          + ("⚠️ **‏FIFO يتفوّق ⇒ إشارةُ عطبٍ في المُرتِّب** لا مجرّد غياب حافة."
             if v1 > v0 else "(‏FIFO لا يتفوّق)"))
    print("\n⚠️ حدود الصدق كما سُجِّلت: انحياز بقاء · تشويه تقسيمات · بلا افتر · "
          "`h4_confirm`=0 · `M13`/`M14` غير ممثَّلتين · `ret_a` يفترض تعبئةً كاملة "
          "عند متوسط الدفعات (مشترَك بين الأذرع فلا يحيز المقارنة).")
    return 0


if __name__ == "__main__":
    sys.exit(run())
