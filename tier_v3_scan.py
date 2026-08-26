#!/usr/bin/env python3
"""🥇③ `T-TIER-V3` — «سجل تصنيف v3»: تنفيذُ عقد `tier_v3_prereg.md` حرفيًّا.

أمرُ المالك 2026-08-26: «سجل تصنيف v3» — الاقتراحُ الثاني من سقف نجاح
`T-TARGET10`: هل يوجد تعريفٌ ثلاثيٌّ يضمّ `J1` يفصل ويسترجع أكثر من `S2`؟

🔒 **مقياسٌ واحدٌ لا اثنان:** الحاكمُ حقل `kasih30_from5` والرفيقُ `kasih30`
**المكتوبان في صفوف `kasih2_scan`** (صفرُ إعادةِ حساب) · و`_green`/`_j1`
وثوابتُ المعايير **تُستورَد من `strong2_scan` بالاسم** · والحدُّ `SMIN` من
`Super_stock.LIQ_TIER_STRONG_MIN` **بالاسم** (رقمُ المالك «ارفع الحد 3» —
لا يُمَسّ) · و`j1_top` بقاعدة `kasih_j1` الإنتاجية (بوّابةُ تكافؤ `G2`).

🔒 **قراءةٌ فقط:** صفرُ إرسالٍ وصفرُ كتابةِ حالة · بلا كرون · والإنتاجُ لا
يستوردها · **و`liq_tier` لا تُمَسّ بحرف**.

**رموزُ الخروج:** 0 حكمٌ صدر · 2 مدخلاتٌ ناقصة · **3 بوّابةُ صلاحيةٍ سقطت**
(‏`G1` التكامل · `G2` تكافؤ `j1_top` · `G4` تفرّقُ الأذرع ⇒ عطبُ أداةٍ لا
نتيجة).
"""

import sys

import Super_stock as S
from kasih_scan import KASIH_PCT, wilson
from kasih2_red_stats import YEARS, load_all
from kasih2_scan import j1_bucket
from strong2_scan import (HOLDOUT, MIN_COVER, MIN_RECALL, SEP_MULT, SISTERS,
                          _green, _j1)

SMIN = int(S.LIQ_TIER_STRONG_MIN)      # رقمُ المالك — بالاسم لا نسخةً
MIN_TIER_ROWS = 30                     # العقد §③-5 — سلّمٌ لا يُقرأ لا يُعتمَد
TIERS = ("قوي", "متوسط", "ضعيف")

# 🔒 `G1` — أرقامُ `S2` المنشورة (`strong2_result.md`) التي يجب أن يعيدها
#    `V0` على الرفيق `kasih30` **بت-بت** (خانةٌ عشرية واحدة كما نُشرت).
S2_PUB = {"cover": 10.2, "recall": 35.7,
          "yr": {"2023": 34.0, "2024": 41.5, "2025": 38.5}}


def _j1top(r) -> bool:
    """أقوى خليّة — بقاعدة `kasih_j1` الإنتاجية: `J1` وصنفُ الخمس `strong`
    وفجوةٌ 75 فأكثر. ⚠️ `gap_pct` في الصفوف مدوَّرٌ لخانةٍ (تفاوتٌ ممكن في
    [74.95،75.0) فقط — يُعلَن ولا يُخفى)."""
    if not _j1(r) or r.get("f2") != "strong":
        return False
    try:
        return float(r.get("gap_pct")) >= 75.0
    except (TypeError, ValueError):
        return False


def tier_of(arm: str, g: int, j1: bool, j1top: bool) -> str:
    """منطقُ التعريفات الأربعة — **مصدرٌ واحد** لقارئ الصفوف ولقسم `DAIC`
    (سجلُّ `tier_fwd_ledger` يخزّن الخامَ بأسماءَ أخرى فيتشاركان المنطق)."""
    if arm == "V0":
        return ("قوي" if g >= SMIN
                else ("متوسط" if g == SMIN - 1 else "ضعيف"))
    if arm == "V1":
        if g >= SMIN or j1:
            return "قوي"
        return "متوسط" if g == SMIN - 1 else "ضعيف"
    if arm == "V2":
        if j1:
            return "قوي"
        return "متوسط" if g >= SMIN else "ضعيف"
    if arm == "V3":
        if g >= SMIN or j1top:
            return "قوي"
        return "متوسط" if (g == SMIN - 1 or j1) else "ضعيف"
    raise ValueError(arm)


def row_tier(arm: str, r: dict) -> str:
    return tier_of(arm, _green(r), _j1(r), _j1top(r))


# ── الأذرعُ الأربع بنصّ العقد §① — ولا خامسة (`V0` أساسٌ لا مرشَّحة) ──
ARMS = (
    ("V0", f"الأساس = الإنتاج `S2` (أخضر {SMIN} فأكثر)"),
    ("V1", f"🎯 الاتحاد: أخضر {SMIN} فأكثر **أو** `J1` — الحاكمة"),
    ("V2", "الإحلال: `J1` وحدَها «قوي»"),
    ("V3", f"القنّاص: أخضر {SMIN} فأكثر **أو** `j1_top`"),
)
CANDIDATES = ("V1", "V2", "V3")


def _gov_hit(r):
    """الحاكم: كاسح30 **من سعر كرت الخمس** — `None` = خارج المقام."""
    v = r.get("kasih30_from5")
    return None if v is None else bool(v)


def _comp_hit(r) -> bool:
    """الرفيق: كاسح30 من دخول المِرساة — على كلّ الصفوف."""
    return bool(r.get("kasih30"))


def _rate(k, n):
    return (k / n * 100.0) if n else 0.0


def _fmt(k, n):
    lo, hi = wilson(k, n)
    return f"{_rate(k, n):.1f}% ({k}/{n}) [{lo:.0f}·{hi:.0f}]"


def sep_ok(ik, inn, ok_, on):
    """المعيار ①/⑥: ضِعفٌ فأكثر **و**فاصلا ويلسون منفصلان."""
    ri, ro = _rate(ik, inn), _rate(ok_, on)
    lo_i, _ = wilson(ik, inn)
    _, hi_o = wilson(ok_, on)
    return (ri >= SEP_MULT * ro) and (lo_i > hi_o), ri, ro


def arm_label(arm: str, rows: list) -> dict:
    """عدّاداتُ ذراعٍ على سلّةٍ واحدة — الحاكمُ والرفيقُ معًا والسلّم."""
    d = {"n_all": len(rows)}
    gov = [(row_tier(arm, r), _gov_hit(r)) for r in rows]
    gov = [(t, h) for t, h in gov if h is not None]
    d["n_gov"] = len(gov)
    for t in TIERS:
        seg = [h for tt, h in gov if tt == t]
        d[f"g_{t}"] = (sum(1 for h in seg if h), len(seg))
    d["gk_all"] = sum(1 for _t, h in gov if h)
    comp = [(row_tier(arm, r), _comp_hit(r)) for r in rows]
    d["c_in"] = (sum(1 for t, h in comp if t == "قوي" and h),
                 sum(1 for t, _h in comp if t == "قوي"))
    d["c_out"] = (sum(1 for t, h in comp if t != "قوي" and h),
                  sum(1 for t, _h in comp if t != "قوي"))
    d["ck_all"] = sum(1 for _t, h in comp if h)
    return d


def ladder_ok(per_year: dict) -> bool:
    """المعيار ⑤: قوي فوق متوسط فوق ضعيف **نِقاطًا** في كلّ سنة — وأيُّ
    فئةٍ دون `MIN_TIER_ROWS` في سنةٍ تُسقط الذراع (سلّمٌ لا يُقرأ)."""
    for y in YEARS:
        d = per_year.get(y)
        if not d:
            return False
        rates = []
        for t in TIERS:
            k, n = d[f"g_{t}"]
            if n < MIN_TIER_ROWS:
                return False
            rates.append(_rate(k, n))
        if not (rates[0] > rates[1] > rates[2]):
            return False
    return True


def judge(arm: str, desc: str, data: dict) -> dict:
    per = {lb: arm_label(arm, rows) for lb, rows in data.items()}
    agg = {}
    for k in ("n_all", "n_gov", "gk_all", "ck_all"):
        agg[k] = sum(v[k] for v in per.values())
    for t in TIERS:
        agg[f"g_{t}"] = tuple(sum(v[f"g_{t}"][i] for v in per.values())
                              for i in (0, 1))
    agg["c_in"] = tuple(sum(v["c_in"][i] for v in per.values()) for i in (0, 1))
    agg["c_out"] = tuple(sum(v["c_out"][i] for v in per.values())
                         for i in (0, 1))
    print(f"\n{'=' * 78}\n🥇 **{arm}** — {desc}\n{'=' * 78}")
    for lb in sorted(per):
        d = per[lb]
        ik, inn = d["g_قوي"]
        ok_, on = (d["gk_all"] - ik), (d["n_gov"] - inn)
        s_ok, ri, ro = sep_ok(ik, inn, ok_, on)
        lad = " · ".join(
            f"{t} {_rate(d[f'g_{t}'][0], d[f'g_{t}'][1]):.1f}%"
            for t in TIERS)
        print(f"  {lb}: قوي(حاكم) {_fmt(ik, inn)} مقابل {_fmt(ok_, on)} "
              f"{'✅' if s_ok else '🔴'} · سلّم: {lad}")
    # المعايير الستّة (العقد §③)
    c1 = all(sep_ok(per[y]["g_قوي"][0], per[y]["g_قوي"][1],
                    per[y]["gk_all"] - per[y]["g_قوي"][0],
                    per[y]["n_gov"] - per[y]["g_قوي"][1])[0]
             for y in YEARS if y in per)
    cover = _rate(agg["g_قوي"][1], agg["n_gov"])
    c2 = cover >= MIN_COVER
    c3 = (sep_ok(per[HOLDOUT]["g_قوي"][0], per[HOLDOUT]["g_قوي"][1],
                 per[HOLDOUT]["gk_all"] - per[HOLDOUT]["g_قوي"][0],
                 per[HOLDOUT]["n_gov"] - per[HOLDOUT]["g_قوي"][1])[0]
          if HOLDOUT in per else False)
    recall = _rate(agg["g_قوي"][0], agg["gk_all"])
    c4 = recall >= MIN_RECALL
    c5 = ladder_ok(per)
    c6 = all(sep_ok(per[y]["c_in"][0], per[y]["c_in"][1],
                    per[y]["c_out"][0], per[y]["c_out"][1])[0]
             for y in YEARS if y in per)
    marks = [c1, c2, c3, c4, c5, c6]
    labels = ("① فصل الحاكم (3 سنوات)", f"② تغطية {cover:.1f}%",
              f"③ هولد-آوت {HOLDOUT}", f"④ استرجاع {recall:.1f}%",
              "⑤ رتابة السلّم", "⑥ فصل الرفيق (3 سنوات)")
    for lab, ok_ in zip(labels, marks):
        print(f"  {lab} ⇒ {'✅' if ok_ else '🔴'}")
    ok = all(marks)
    print(f"  ⚖️ **{'✅ يعبر الستّة' if ok else '🔴 لا يعبر'}**")
    return {"arm": arm, "ok": ok, "cover": cover, "recall": recall,
            "c": marks, "per": per, "agg": agg}


# ── بوّاباتُ الصلاحية (العقد §④) — دوالُّ نقيّةٌ قابلةٌ للاختبار ──
def g1_ok(res_v0: dict) -> bool:
    """`G1`: `V0` على الرفيق يعيد أرقامَ `S2` المنشورة بخانةٍ عشرية."""
    agg, per = res_v0["agg"], res_v0["per"]
    cov = round(_rate(agg["c_in"][1], agg["n_all"]), 1)
    rec = round(_rate(agg["c_in"][0], agg["ck_all"]), 1)
    if cov != S2_PUB["cover"] or rec != S2_PUB["recall"]:
        return False
    for y, want in S2_PUB["yr"].items():
        if y not in per:
            return False
        if round(_rate(per[y]["c_in"][0], per[y]["c_in"][1]), 1) != want:
            return False
    return True


def g2_ok() -> bool:
    """`G2`: تكافؤُ `j1_top` مع `Super_stock.kasih_j1` على أربع حالاتٍ حدّية."""
    for f2, gap, want in (("strong", 75.0, True), ("strong", 74.9, False),
                          ("operator", 80.0, False), ("group", 80.0, False)):
        ev = {"class": (f2, ""), "anchor_price": 1.0 + gap / 100.0,
              "prev_close": 1.0}
        r = {"j1": j1_bucket(f2, gap), "f2": f2, "gap_pct": gap}
        if bool(S.kasih_j1(ev)[1]) != want or _j1top(r) != want:
            return False
    return True


def g4_ok(tier_fn=tier_of) -> bool:
    """`G4`: الأذرعُ الأربع تتفرّق — لكلّ زوجٍ حالةٌ خامّة تفصله."""
    cases = ((SMIN, False, False), (0, True, False), (0, True, True),
             (SMIN - 1, False, False))
    arms = [a for a, _d in ARMS]
    for i, a in enumerate(arms):
        for b in arms[i + 1:]:
            if not any(tier_fn(a, *c) != tier_fn(b, *c) for c in cases):
                return False
    return True


def main() -> int:
    data = load_all()
    if not data:
        print("⛔ لا ملفات kasih2_rows_*.jsonl — لا شيء يُقاس")
        return 2
    missing = [y for y in YEARS if y not in data]
    if missing:
        print(f"⛔ سنواتٌ ناقصة: {missing} — المعيار ① يشترط الثلاث")
        return 2
    tot = sum(len(v) for v in data.values())
    n_gov = sum(1 for rows in data.values() for r in rows
                if _gov_hit(r) is not None)
    print(f"📦 الملفات {len(data)} · **{tot} صفًّا** · مقامُ الحاكم "
          f"(بلغ الخمس) **{n_gov}** — والفرقُ يُطبَع لا يُخفى (العقد §⑦-3)")
    print(f"🔎 الحاكم: كاسح{KASIH_PCT:.0f} **من سعر كرت الخمس** "
          f"(`kasih30_from5`) · الرفيق `kasih30` شرطُ فصلٍ سادس · "
          f"`SMIN`={SMIN} من الإنتاج بالاسم")
    print("🔒 `liq_tier` **لم تُمَسّ** — قياسٌ خارج الإنتاج.")

    if not g2_ok():
        print("⛔ `G2`: `_j1top` لا يكافئ `kasih_j1` ⇒ عطبُ أداةٍ لا نتيجة")
        return 3
    print("✅ `G2` تكافؤُ `j1_top` مع الإنتاج على أربع حالاتٍ حدّية")
    if not g4_ok():
        print("⛔ `G4`: ذراعان لا تفترقان ⇒ بوّابةٌ عمياء — عطبُ أداة")
        return 3
    print("✅ `G4` الأذرعُ الأربع تتفرّق (كلُّ زوجٍ له حالةٌ فاصلة)")

    res = {a: judge(a, d, data) for a, d in ARMS}

    if not g1_ok(res["V0"]):
        agg = res["V0"]["agg"]
        print(f"⛔ `G1`: `V0` لا يعيد أرقامَ `S2` المنشورة "
              f"(تغطية {_rate(agg['c_in'][1], agg['n_all']):.1f} مقابل "
              f"{S2_PUB['cover']} · استرجاع "
              f"{_rate(agg['c_in'][0], agg['ck_all']):.1f} مقابل "
              f"{S2_PUB['recall']}) ⇒ عطبُ أداةٍ لا نتيجة")
        return 3
    print("\n✅ `G1` التكامل: `V0` على الرفيق يعيد أرقامَ `S2` المنشورة "
          f"بت-بت (تغطية {S2_PUB['cover']}% · استرجاع {S2_PUB['recall']}% · "
          f"{S2_PUB['yr']})")

    print(f"\n{'=' * 78}\n📈 الجدولُ الجامع (الحاكم `kasih30_from5`)\n{'=' * 78}")
    print(f"{'الذراع':<7}{'تغطية%':>9}{'استرجاع%':>11}"
          f"{'①':>4}{'②':>4}{'③':>4}{'④':>4}{'⑤':>4}{'⑥':>4}{'الحكم':>12}")
    for a, _d in ARMS:
        r = res[a]
        m = ["✅" if x else "🔴" for x in r["c"]]
        tag = ("أساس" if a == "V0"
               else ("✅ يعبر" if r["ok"] else "🔴 لا"))
        print(f"{a:<7}{r['cover']:>9.1f}{r['recall']:>11.1f}"
              f"{m[0]:>4}{m[1]:>4}{m[2]:>4}{m[3]:>4}{m[4]:>4}{m[5]:>4}"
              f"{tag:>12}")
    winners = [res[a] for a in CANDIDATES if res[a]["ok"]]
    if winners:
        w = max(winners, key=lambda r: r["recall"])
        moved = (w["agg"]["g_قوي"][1] - res["V0"]["agg"]["g_قوي"][1])
        print(f"\n🥇 **الفائزة `{w['arm']}`** (الأعلى استرجاعًا بين العابرات "
              "— قاعدةُ §③ المثبَّتة) ⇒ **اقتراحٌ للمالك، ولا تنفيذَ بلا "
              "أمره**.")
        print(f"⚠️ **أثرُ التسليم يُسمّى** (العقد §⑤): «قوي» تتّسع بنحو "
              f"{moved:+,} صفًّا على هذي الصفوف — و`update_tier=[\"قوي\"]` "
              "مشحونٌ فتغييرُ التعريف يغيّر مَن يستلم التحديثات.")
    else:
        print("\n🔴 **لا ذراعَ مرشَّحة تعبر الستّة ⇒ يبقى `S2` كما هو** "
              "(‏`TV-P4` تحقّق) — ولا اقتراح.")

    # 🔑 `TV-P5` — عشرةُ 08-19 (سؤال المالك الأصليّ)
    day19 = data.get("2026-08-19") or []
    if day19:
        print(f"\n{'=' * 78}\n🔑 عشرةُ 08-19 تحت كلّ ذراع (`TV-P5`)\n{'=' * 78}")
        for a, _d in ARMS:
            hit = sorted({r["sym"] for r in day19
                          if r.get("sym") in SISTERS
                          and row_tier(a, r) == "قوي"})
            print(f"  {a}: {len(hit)} من 10 ⇒ {hit or '—'}")
    else:
        print("\n⚠️ `TV-P5` غيرُ مقيس: صفوفُ 2026-08-19 غيرُ محمَّلة.")

    # 📌 مطابقةُ `DAIC` الوصفيّة — من السجلّ الأماميّ (العقد §⑥)
    try:
        import json
        daic = {}
        with open("tier_fwd_ledger.jsonl", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if row.get("symbol") == "DAIC":
                    daic[row.get("date")] = row
        if daic:
            print(f"\n{'=' * 78}\n📌 `DAIC` من `tier_fwd_ledger` "
                  f"(مطابقةٌ وصفيّةٌ محسوبةٌ سلفًا)\n{'=' * 78}")
            for dt_ in sorted(daic):
                row = daic[dt_]
                g = int(row.get("green") or 0)
                j1 = bool(row.get("j1"))
                jt = bool(row.get("j1_top"))
                tiers = " · ".join(f"{a}={tier_of(a, g, j1, jt)}"
                                   for a, _d in ARMS)
                print(f"  {dt_}: أخضر {g} · J1={'✅' if j1 else '—'} · "
                      f"top={'✅' if jt else '—'} · الإنتاج={row.get('tier')}"
                      f" ⟶ {tiers}")
    except OSError:
        print("\n⚠️ `tier_fwd_ledger.jsonl` غيرُ متاح — قسمُ `DAIC` يُتخطّى "
              "معلَنًا.")

    print(f"\n{'=' * 78}\n⚠️ حدودُ صدقٍ (العقد §⑦)\n{'=' * 78}")
    print("  1) 🔴 دائريّةٌ مضاعفة: المكوّناتُ اختيرت على هذي الصفوف، "
          "واختيارُ الحاكم مُطَّلعٌ على §B — والمعيار ⑥ يخفّف الثانيةَ "
          "ولا يُلغي الأولى. النظيفُ الوحيد السجلُّ الأماميّ.")
    print("  2) «كاسح» لمسُ +30% لا صفقةٌ منفَّذة (بالتساوي لكلّ ذراع).")
    print(f"  3) مقامُ الحاكم «مَن بلغ الخمس» ({n_gov} من {tot}) أصغرُ من "
          "مقام الرفيق — مطبوعٌ أعلاه.")
    print("  4) والعبورُ لا يُثبت ربحية.")
    print("  5) وصفوفُ الجلسات العشر لا تدخل المعيار ① (سنويٌّ حصرًا).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
