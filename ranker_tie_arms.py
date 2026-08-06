#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🥇⑦ T-RANKER-TIE — **تشغيل أذرع كاسر التعادل** (`ranker_tie_prereg.md`).

**السؤال المحدَّد** (‏§① من التسجيل): على جلسةٍ حيّة كان **‏16 سهمًا متعادلين عند
جاهزية 70** والسعة 10 ⇒ **‏10 من 10 خاناتٍ يحكمها كاسرُ التعادل**، والفاصلُ اليوم
`score` ثم `rr` — **ولم يُختبَرا قطّ**. فهل «الأعمقُ داخل ظرف فيصل» أفضل؟

**الأذرعُ الأربعة مثبَّتةٌ قبل أيّ رقم** (‏§②/§⑤): `R-0` المُرتِّب الفعليّ ·
`R-ENV` كاسرُ تعادلٍ بعمق الظرف · `R-RAND` كاسرُ تعادلٍ عشوائيٌّ حتميّ (شاهدُ الضبط
الحاسم) · `R-FIFO` الأقدمُ أوّلًا. **ولا ذراعَ خامسة** — أيُّ ذراعٍ تُضاف بعد رؤية
الأرقام هي `p-hacking`.

**المقياس** (‏§④): `R` المحقَّق بأداة `replay10` الأمينة، والفرقُ **مزدوجٌ داخل
الجلسة** (نفسُ البِركة · نفسُ اليوم · نفسُ السعة) ⇒ لا يحمل ضجيجَ السوق.

⚖️ **الميزانيةُ الثابتة (‏§⑥ — شرطُ صلاحيةٍ لا تفصيل):** الأذرعُ الأربعة تعمل على
**نفس قائمة الصفقات** المُخرَجة من تشغيلةِ باكتيستٍ **واحدة** ⇒ نفسُ اللقطة والكون
والسعة والنافذة وسقوفِ الجلب **بالبناء لا بالوعد**. وتُطبَع القيودُ في المُخرَج.

🔒 **بحث/قياس — صفر مسّ إنتاج.** يشغّل `run_backtest` الإنتاجيّ نفسَه، والنتائجُ
**تُطبَع للسجلّ** لأن تنزيل الـartifacts محجوبٌ بسياسة الشبكة.
"""
from __future__ import annotations

import os
import random
import sys

# ⚠️ **قبل الاستيراد**: `_apply_backtest_overrides` يُنفَّذ وقت تحميل الوحدة ويشترط
# `SCREENER_MODE=BACKTEST` — فالضبط بعد الاستيراد يصل متأخّرًا والعلمُ يخرج **خاملًا**
# (بصمة الـno-op الموثّقة: `BT_CANDLE`).
os.environ["SCREENER_MODE"] = "BACKTEST"
os.environ["BT_REPLAY10"] = "1"      # تاريخُ الخروج + `rr` (تحرير الخانة بجلسات)
os.environ["BT_ENVVALS"] = "1"       # 📐 معايير الظرف الأحد عشر — بلاها الذراعُ no-op
os.environ.setdefault("BT_POTENTIAL", "1")   # مقياسٌ ثانويّ يُنشَر ولا يحكم

import catalog_envelope as CE                                  # noqa: E402
import envelope_scan as EV                                     # noqa: E402
import replay10 as RP                                          # noqa: E402
import Super_stock as S                                        # noqa: E402

SEEDS = int(os.environ.get("TIE_SEEDS", "200"))       # §⑤: 200 خلطة كما سُجِّل
BOOT = int(os.environ.get("TIE_BOOT", "10000"))
MIN_CRITERIA = int(os.environ.get("TIE_MIN_CRITERIA", "6"))   # §②: أقلُّ من 6 ⇒ امتناع
DIFF_MIN_R = 0.10        # §④-2: الفرقُ المجمَّع لكلّ صفقة
MIN_AFFECTED = 30        # §④-4


# ───────────────────────── تجهيزُ عمق الظرف ─────────────────────────
def attach_env_depth(trades, edges, sides, min_criteria=MIN_CRITERIA) -> dict:
    """يحسب `env_depth` لكلّ صفقة ويضعه في **نفس قاموس الصفقة** (وهو `payload`
    المرشّح). يرجّع عدّاداتٍ تشخيصية — **بلا حكم**: الامتناعُ يُعلَن لا يُخمَّن."""
    n_ok = n_abstain = n_novals = 0
    ncrit = []
    for t in trades:
        vals = t.get("env_vals")
        if not isinstance(vals, dict):
            n_novals += 1
            t["env_depth"] = None
            continue
        ncrit.append(sum(1 for k in sides
                         if vals.get(k) is not None and edges.get(k) is not None))
        d = RP.env_depth(vals, edges, sides, min_criteria=min_criteria)
        t["env_depth"] = d
        if d is None:
            n_abstain += 1
        else:
            n_ok += 1
    ncrit.sort()
    med = ncrit[len(ncrit) // 2] if ncrit else 0
    return {"ok": n_ok, "abstain": n_abstain, "no_vals": n_novals,
            "median_criteria": med}


# ───────────────────────── الفرقُ المزدوج ─────────────────────────
def _key(c) -> tuple:
    return (c.session, c.symbol)


def paired_delta(taken_a, taken_b) -> dict:
    """الفرقُ المزدوج `A − B` **مفكَّكًا بالرمز** (وحدةُ العنقود في §④-3).

    مساهمةُ الرمز = مجموعُ `R` لما أخذه `A` منه ناقصَ ما أخذه `B` — فالمشترَكُ
    يُلغي نفسَه بالبناء ويبقى **أثرُ التبديل وحده**."""
    out: dict[str, float] = {}
    for arm, sign in ((taken_a, 1.0), (taken_b, -1.0)):
        for c in arm:
            v = RP.r_unit(c.payload)
            if v is None:
                continue
            out[c.symbol] = out.get(c.symbol, 0.0) + sign * v
    return out


def affected(taken_a, taken_b) -> dict:
    """الصفقاتُ المتأثّرة = **الفرقُ التماثليّ** بين مأخوذَي الذراعين.

    ⚖️ **وهذي القراءةُ العملية الأضيق** لعبارة التسجيل «صفقةٌ وقع فيها تعادلٌ
    فعليّ»: تعادلٌ وقع **وغيَّر النتيجة**. واخترتُها لأنها **تُصعّب** استيفاء الشرط 4
    فتميل إلى «لا حكم» لا إلى الاعتماد — والانحيازُ الآمن هو هذا."""
    sa = {_key(c) for c in taken_a}
    sb = {_key(c) for c in taken_b}
    return {"only_a": len(sa - sb), "only_b": len(sb - sa),
            "n": len(sa ^ sb), "shared": len(sa & sb)}


def cluster_bootstrap_diff(delta_by_symbol: dict, denom: float,
                           n: int = BOOT, seed: int = 24680,
                           level: float = 0.95) -> dict:
    """فاصلُ ثقةٍ للفرق بإعادة معاينة **الرموز** بالإحلال (‏§④-3). المقامُ ثابت
    (عددُ الصفقات أو الجلسات) فلا ينحاز بتغيّر حجم العيّنة المعادة."""
    syms = sorted(delta_by_symbol)
    if not syms or denom <= 0:
        return {"lo": 0.0, "hi": 0.0, "n": 0}
    rng = random.Random(seed)
    draws = []
    for _ in range(n):
        tot = sum(delta_by_symbol[syms[rng.randrange(len(syms))]] for _ in syms)
        draws.append(tot / denom)
    a = (1.0 - level) / 2.0
    return {"lo": RP._pct(draws, a), "hi": RP._pct(draws, 1.0 - a), "n": len(syms)}


# ───────────────────────── تشغيلُ ذراع ─────────────────────────
def _arm(cands, outcome_of, ranker, n_sessions):
    res = RP.replay(cands, outcome_of=outcome_of, ranker=ranker,
                    sessions=range(0, n_sessions))
    taken = res["taken"]
    tot = sum(v for v in (RP.r_unit(c.payload) for c in taken) if v is not None)
    return {"res": res, "taken": taken, "n": len(taken), "total_r": tot,
            "per_day": tot / n_sessions if n_sessions else 0.0,
            "per_trade": tot / len(taken) if taken else 0.0}


def _budget_lines(trades, cands, n_sessions) -> list:
    """§⑥: تُطبَع قيودُ الميزانية في مُخرَج كلّ تشغيلة — وإلّا لا تُفسَّر النتيجة."""
    frozen = os.environ.get("BT_FROZEN_PATH") or "—"
    return [
        f"  اللقطة المجمَّدة: {frozen} · السنة: "
        f"{os.environ.get('BACKTEST_YEAR', '?')}",
        f"  الكون: صفقاتُ تشغيلةٍ **واحدة** = {len(trades)} · مرشّحون = {len(cands)}"
        f" · جلسات فهرسية = {n_sessions}",
        f"  السعة: {RP.CAPACITY} (‏= `WATCHLIST_SIZE` الحيّ "
        f"{S.CONFIG.get('WATCHLIST_SIZE')})",
        f"  معايير فيصل: FAISAL_ONLY={S.CONFIG.get('FAISAL_ONLY')} · بصمةُ الحوافّ "
        f"{EV.edges_fingerprint(EV.load_edges() or {})[:12] or '—'}",
        f"  سقوفُ الجلب: HISTORY_DAYS={S.CONFIG.get('HISTORY_DAYS')} · "
        f"CHUNK={S.CONFIG.get('CHUNK')} · MAX_SYMBOLS={S.CONFIG.get('MAX_SYMBOLS')}",
        "  🔒 الأذرعُ الأربعة تقرأ **نفس** القائمة أعلاه — لا إعادةَ جلبٍ ولا "
        "إعادةَ فرز ⇒ الفرقُ منسوبٌ إلى الترتيب وحده.",
    ]


def run() -> int:
    trades = S.run_backtest() or []
    year = (os.environ.get("BACKTEST_YEAR", "") or "?").strip()
    print(f"\n{'=' * 72}\n🥇⑦ T-RANKER-TIE — أذرعُ كاسر التعادل · السنة {year}\n"
          f"{'=' * 72}")

    # ── ✅ «أثبت أن التجربة اشتغلت» قبل تفسير أيّ رقم ──
    with_fields = [t for t in trades if t.get("exit_date")]
    with_vals = [t for t in with_fields if isinstance(t.get("env_vals"), dict)]
    print(f"صفقات المحرّك: {len(trades)} · بحقول الإعادة: {len(with_fields)} "
          f"· بقيم الظرف: {len(with_vals)}")
    if not with_fields:
        print("⛔ `BT_REPLAY10` **خامل** ⇒ التجربة no-op — لا تُفسَّر نتيجتُها.")
        return 2
    if not with_vals:
        print("⛔ `BT_ENVVALS` **خامل** ⇒ `env_depth` يمتنع عن كلّ صفقة، فتخرج "
              "«لا فرق» وهي **no-op** — لا تُفسَّر نتيجتُها.")
        return 4
    mism = [t for t in with_fields if t.get("exit_kind") != t.get("outcome")]
    print(f"تطابق محرّك الخروج مع محرّك الحسم: {len(with_fields) - len(mism)}"
          f"/{len(with_fields)}" + (f" · ⛔ تفرّق={len(mism)}" if mism else " ✅"))
    if mism:
        print("⛔ تفرّق المحرّكان ⇒ توقيت تحرير الخانة غير موثوق — لا تُقرأ الأذرع.")
        return 3

    edges = EV.load_edges()
    if not edges:
        print("⛔ حوافُّ الظرف غير محمَّلة ⇒ `R-ENV` بلا مرجع — لا تُشغَّل الأذرع.")
        return 5
    sides = {n: sd for n, sd, _, _ in CE.CRITERIA}
    diag = attach_env_depth(with_fields, edges, sides)
    print(f"عمقُ الظرف: محسوبٌ لـ{diag['ok']} · امتناعٌ (دون {MIN_CRITERIA} معايير) "
          f"{diag['abstain']} · بلا قيم {diag['no_vals']} "
          f"· وسيطُ المعايير المتاحة {diag['median_criteria']}/11")
    if diag["ok"] == 0:
        print("⛔ امتنع الذراعُ عن **كلّ** صفقة ⇒ `R-ENV` ≡ `R-0` بالبناء = no-op.")
        return 6

    cands, idx, outcome_of = RP.candidates_from_trades(with_fields)
    n_sessions = len(idx)
    print("\n⚖️ الميزانيةُ الثابتة (‏§⑥):")
    for ln in _budget_lines(trades, cands, n_sessions):
        print(ln)

    # ── الأذرعُ الأربعة على نفس البِركة ──
    a0 = _arm(cands, outcome_of, RP.rank_actual, n_sessions)
    aenv = _arm(cands, outcome_of, RP.rank_tie_env, n_sessions)
    afifo = _arm(cands, outcome_of, RP.rank_fifo, n_sessions)
    rand = [_arm(cands, outcome_of, RP.make_rank_tie_random(sd), n_sessions)
            for sd in range(1, SEEDS + 1)]

    print("\n📊 الأذرع (‏R المحقَّق):")

    def _line(tag, a):
        print(f"  {tag}: R/يوم = {a['per_day']:+.4f} · R/صفقة = "
              f"{a['per_trade']:+.4f} · مأخوذة = {a['n']} · إجمالي R = "
              f"{a['total_r']:+.1f} · مرفوض بالسعة = {a['res']['rejected_cap']}")

    _line("R-0    (المُرتِّب الفعليّ)", a0)
    _line("R-ENV  (عمقُ ظرف فيصل)  ", aenv)
    _line("R-FIFO (الأقدم أوّلًا)   ", afifo)
    rd = [x["per_day"] for x in rand]
    rt = [x["per_trade"] for x in rand]
    print(f"  R-RAND (عشوائيّ ×{len(rand)}): R/يوم متوسط = {sum(rd) / len(rd):+.4f} "
          f"‏[{RP._pct(rd, .05):+.4f}, {RP._pct(rd, .95):+.4f}] · R/صفقة متوسط = "
          f"{sum(rt) / len(rt):+.4f} ‏[{RP._pct(rt, .05):+.4f}, "
          f"{RP._pct(rt, .95):+.4f}]")

    # ── الفرقُ المزدوج والاستدلال ──
    print("\n📐 الفرقُ المزدوج داخل الجلسة (‏§④):")
    for tag, arm in (("R-ENV − R-0   ", aenv), ("R-FIFO − R-0  ", afifo)):
        dsym = paired_delta(arm["taken"], a0["taken"])
        tot = sum(dsym.values())
        aff = affected(arm["taken"], a0["taken"])
        # المقامُ **عددُ مأخوذي الذراع** لا المتأثّرين — فالمعيار §④-2 «لكلّ صفقة»
        # على الصفقات كلِّها، والقسمةُ على المتأثّرين وحدهم تضخّم الفرق بلا وجه.
        den = max(arm["n"], 1)
        ci_t = cluster_bootstrap_diff(dsym, den, n=BOOT)
        ci_d = cluster_bootstrap_diff(dsym, max(n_sessions, 1), n=BOOT)
        print(f"  {tag}: مجموع = {tot:+.2f}R · لكلّ صفقة = {tot / den:+.4f}R "
              f"· لليوم = {tot / max(n_sessions, 1):+.4f}R")
        print(f"      متأثّرة (فرقٌ تماثليّ) = {aff['n']} "
              f"(دخل {aff['only_a']} · خرج {aff['only_b']} · مشترَك {aff['shared']}) "
              f"· رموزٌ متأثّرة = {ci_t['n']}")
        print(f"      cluster bootstrap 95% (لكلّ صفقة) = "
              f"[{ci_t['lo']:+.4f}, {ci_t['hi']:+.4f}] · (لليوم) = "
              f"[{ci_d['lo']:+.4f}, {ci_d['hi']:+.4f}]")

    # ── شاهدُ الضبط الحاسم: R-ENV مقابل R-RAND ──
    d_rand = [aenv["per_trade"] - x for x in rt]
    p_one = sum(1 for x in rt if x >= aenv["per_trade"]) / len(rt)
    print(f"\n🎲 شاهدُ الضبط (‏§⑤): R-ENV − R-RAND لكلّ صفقة = "
          f"{sum(d_rand) / len(d_rand):+.4f}R "
          f"· فاصل 90% = [{RP._pct(d_rand, .05):+.4f}, {RP._pct(d_rand, .95):+.4f}] "
          f"· p أحادية = {p_one:.4f}")

    # ── البوّابة الرباعية ──
    dsym = paired_delta(aenv["taken"], a0["taken"])
    tot = sum(dsym.values())
    per_trade = tot / max(aenv["n"], 1)
    aff = affected(aenv["taken"], a0["taken"])
    ci = cluster_bootstrap_diff(dsym, max(aenv["n"], 1), n=BOOT)
    print("\n🧭 البوّابة الرباعية (‏§④ — الشرط ① يُقرأ عبر السنوات الثلاث):")
    print(f"  ① إشارةُ الفرق هذي السنة: {'موجب ✅' if tot > 0 else 'سالب 🔴'} "
          f"({tot:+.2f}R) — الحكمُ يشترط موجبًا في الثلاث بلا انقلاب.")
    print(f"  ② الفرقُ لكلّ صفقة ≥ +{DIFF_MIN_R:g}R: {per_trade:+.4f} "
          f"{'✅' if per_trade >= DIFF_MIN_R else '🔴'}")
    print(f"  ③ الفاصل 95% لا يلمس الصفر: [{ci['lo']:+.4f}, {ci['hi']:+.4f}] "
          f"{'✅' if (ci['lo'] > 0 or ci['hi'] < 0) else '🔴'}")
    print(f"  ④ متأثّرة ≥ {MIN_AFFECTED}: {aff['n']} "
          f"{'✅' if aff['n'] >= MIN_AFFECTED else '🔴 (سقوطُه وحده ⇒ «لا حكم»)'}")
    print(f"  🔑 شاهد FIFO: R-FIFO − R-0 لكلّ صفقة = "
          f"{afifo['per_trade'] - a0['per_trade']:+.4f}R"
          + ("  ⚠️ **‏FIFO يتفوّق ⇒ إشارةُ عطبٍ في المُرتِّب**"
             if afifo["per_trade"] > a0["per_trade"] else ""))

    print("\n⚠️ حدودُ الصدق كما سُجِّلت (‏§⑨): انحيازُ بقاء · تشويهُ تقسيمات · بلا "
          "افتر · `h4_confirm`=0 حيًّا فالمفتاحُ الثاني خاملٌ فعليًّا · والظرفُ "
          "**مُعايَرٌ على 25 رمزًا** ومراسيهم داخل مدى الباكتيست ⇒ قربُ سهمٍ من وسطه "
          "ليس دليلَ جودةٍ مستقلًّا، **والبوّاباتُ نفسُها في الأذرع الأربعة** فالفرقُ "
          "بينها لا يتأثّر بذلك.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
