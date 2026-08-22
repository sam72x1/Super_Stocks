#!/usr/bin/env python3
"""🥇🔁 إعادةُ تعريف «قوي» — تنفيذُ عقد `strong2_prereg.md` حرفيًّا.

أمرُ المالك 2026-08-22: «أعِد تعريف قوي و اتركه يجمع».

🔒 **مقياسٌ واحدٌ لا اثنان:** الحسمُ يُقرأ من حقل `kasih30` **المكتوب في
صفوف `kasih2_scan`** (صفرُ إعادةِ حساب)، وسلالُ المكوّنات و`wilson` و
`f5_bucket` **تُستورَد بالاسم** — صفرُ رقمٍ مغروسٍ وصفرُ منطقٍ مكرّر.

🔒 **قراءةٌ فقط:** صفرُ إرسالٍ وصفرُ كتابةِ حالة · بلا كرون · والإنتاجُ لا
يستوردها. **و`liq_tier` لا تُمَسّ** — شقُّ «اتركه يجمع» ينفَّذ بعدم الفعل.

**رموزُ الخروج:** 0 حكمٌ صدر · 2 مدخلاتٌ ناقصة · **3 بوّابةُ التكامل سقطت**
(‏`S0` لم يُعد تعريفَ الإنتاج ⇒ عطبُ أداةٍ لا نتيجة).
"""

import sys

from kasih_scan import KASIH_PCT, f5_bucket, wilson       # المقياسُ الواحد
from kasih2_red_stats import COMPS, TOP, YEARS, load_all
from kasih2_scan import j1_bucket

MIN_COVER = 10.0          # العقد §③-2 — رقمٌ مشتقٌّ لا مخترَع
MIN_RECALL = 25.0         # العقد §③-4
SEP_MULT = 2.0            # العقد §③-1
TRAIN = ("2023", "2024")  # العقد §③-3 — والهولد-آوت 2025
HOLDOUT = "2025"

# 🔑 عشرةُ 08-19 التي سأل عنها المالك (‏`S-P5`)
SISTERS = ("YJ", "WXM", "INLF", "ZYBT", "LGHL", "PSIG", "AZI", "ELPW",
           "RDAC", "MSS")


def _green(r):
    """عددُ المكوّنات في سلّتها العليا — تعريفُ `liq_tier` نفسُه."""
    return sum(1 for c in COMPS if r.get(c) == TOP[c])


def _j1(r):
    """هل الصفُّ **توليفةُ `J1`**؟ — `j1` **سلسلةُ سلّةٍ لا بوليان**."""
    return str(r.get("j1") or "").startswith("توليفة")


def _gap75(r):
    """الفجوةُ «فوق 75%» — **بدالّة الإنتاج** `f5_bucket` لا بعتبةٍ مغروسة."""
    g = r.get("gap_pct")
    if g is None:
        return False
    try:
        return f5_bucket(float(g)) == f5_bucket(100.0)
    except (TypeError, ValueError):
        return False


# ── الأذرعُ الخمس، مثبَّتةٌ بنصّ العقد §① — ولا سادسة ──
ARMS = (
    ("S0", "الأساس: `J1` **و** أخضر 3 فأكثر (النافذُ اليوم)",
     lambda r: _j1(r) and _green(r) >= 3),
    ("S1", "`C4` وحدَها (خضراء 3-4)",
     lambda r: r.get("c4") == TOP["c4"]),
    ("S2", "أخضر 3 فأكثر — **بلا اشتراط `J1`**",
     lambda r: _green(r) >= 3),
    ("S3", "صنفُ الخمس قوي/مضارب **و** فجوةٌ فوق 75%",
     lambda r: r.get("f2") in ("strong", "operator") and _gap75(r)),
    ("S4", "`J1` **و** أخضر 2 فأكثر",
     lambda r: _j1(r) and _green(r) >= 2),
)


def _rate(k, n):
    return (k / n * 100.0) if n else 0.0


def _fmt(k, n):
    lo, hi = wilson(k, n)
    return f"{_rate(k, n):.1f}% ({k}/{n}) [{lo:.0f}·{hi:.0f}]"


def arm_year(rows, pred):
    """عدّاداتُ ذراعٍ على سلّةٍ واحدة."""
    inn = [r for r in rows if pred(r)]
    out = [r for r in rows if not pred(r)]
    ki = sum(1 for r in inn if r.get("kasih30"))
    ko = sum(1 for r in out if r.get("kasih30"))
    f5i = [r for r in inn if r.get("kasih30_from5") is not None]
    return {"n": len(rows), "in_n": len(inn), "in_k": ki,
            "out_n": len(out), "out_k": ko, "k_all": ki + ko,
            "f5": (sum(1 for r in f5i if r["kasih30_from5"]), len(f5i))}


def sep_ok(d):
    """المعيار ①: ضِعفٌ فأكثر **و**فاصلا ويلسون منفصلان."""
    ri, ro = _rate(d["in_k"], d["in_n"]), _rate(d["out_k"], d["out_n"])
    lo_i, _ = wilson(d["in_k"], d["in_n"])
    _, hi_o = wilson(d["out_k"], d["out_n"])
    return (ri >= SEP_MULT * ro) and (lo_i > hi_o), ri, ro


def judge(name, desc, pred, data):
    per = {lb: arm_year(rows, pred) for lb, rows in data.items()}
    agg = {k: sum(v[k] for v in per.values())
           for k in ("n", "in_n", "in_k", "out_n", "out_k", "k_all")}
    print(f"\n{'=' * 78}\n🥇 **{name}** — {desc}\n{'=' * 78}")
    for lb in sorted(per):
        d = per[lb]
        ok, ri, ro = sep_ok(d)
        print(f"  {lb}: داخل {_fmt(d['in_k'], d['in_n'])} · "
              f"خارج {_fmt(d['out_k'], d['out_n'])} · "
              f"تغطية {_rate(d['in_n'], d['n']):.1f}% · "
              f"استرجاع {_rate(d['in_k'], d['k_all']):.1f}% · "
              f"{'✅' if ok else '🔴'} ({ri:.1f} مقابل {ro:.1f})")
    c1 = all(sep_ok(per[y])[0] for y in YEARS if y in per)
    cover = _rate(agg["in_n"], agg["n"])
    recall = _rate(agg["in_k"], agg["k_all"])
    c2 = cover >= MIN_COVER
    c3 = sep_ok(per[HOLDOUT])[0] if HOLDOUT in per else False
    c4 = recall >= MIN_RECALL
    print(f"  ① الفصلُ في السنوات الثلاث ⇒ {'✅' if c1 else '🔴'}")
    print(f"  ② التغطية {cover:.1f}% (الحدّ {MIN_COVER:.0f}) ⇒ "
          f"{'✅' if c2 else '🔴'}")
    print(f"  ③ خارج العيّنة ({HOLDOUT}) ⇒ {'✅' if c3 else '🔴'}")
    print(f"  ④ الاسترجاع {recall:.1f}% (الحدّ {MIN_RECALL:.0f}) ⇒ "
          f"{'✅' if c4 else '🔴'}")
    ok = c1 and c2 and c3 and c4
    print(f"  ⚖️ **{'✅ يعبر' if ok else '🔴 لا يعبر'}**")
    return {"name": name, "ok": ok, "cover": cover, "recall": recall,
            "c": (c1, c2, c3, c4), "per": per, "agg": agg}


def main() -> int:
    data = load_all()
    if not data:
        print("⛔ لا ملفات kasih2_rows_*.jsonl — لا شيء يُقاس")
        return 2
    missing = [y for y in YEARS if y not in data]
    if missing:
        print(f"⛔ سنواتٌ ناقصة: {missing} — المعيار ① يشترط الثلاث")
        return 2
    days = sorted(lb for lb in data if lb not in YEARS)
    tot = sum(len(v) for v in data.values())
    print(f"📦 الملفات {len(data)} · سنوات {list(YEARS)} · أيام "
          f"({len(days)}) · **{tot} صفًّا**")
    print(f"🔎 الحاكم: كاسح{KASIH_PCT:.0f} من حقل `kasih30` المكتوب "
          "(صفرُ إعادةِ حساب) · والتدريبُ "
          f"{list(TRAIN)} والهولد-آوت {HOLDOUT}")
    print("🔒 `liq_tier` **لم تُمَسّ** — شقُّ «اتركه يجمع» ينفَّذ بعدم الفعل.")

    # 🔒 بوّابةُ التكامل: `S0` يجب أن يُعيد تعريفَ الإنتاج على أربع حالاتٍ
    #    حدّية — وإلّا فالصفوفُ أو القراءةُ تغيّرت ⇒ عطبُ أداةٍ لا نتيجة.
    _hi = dict({c: TOP[c] for c in COMPS}, j1=j1_bucket("strong", 40.0))
    _lo = dict({c: "x" for c in COMPS}, j1=j1_bucket("group", 5.0))
    _n1 = dict(_hi, c4="x")                       # أخضر 3 · J1 ⇒ داخل
    _n2 = dict(_hi, c3="x", c4="x")               # أخضر 2 · J1 ⇒ خارج
    _s0 = ARMS[0][2]
    if not (_s0(_hi) and _s0(_n1) and not _s0(_n2) and not _s0(_lo)):
        print("⛔ بوّابةُ التكامل: `S0` لا يُعيد تعريفَ الإنتاج ⇒ عطبُ أداة")
        return 3
    print("✅ بوّابةُ التكامل: `S0` يُعيد تعريفَ الإنتاج على أربع حالاتٍ حدّية")

    res = [judge(n, d, p, data) for n, d, p in ARMS]

    print(f"\n{'=' * 78}\n📈 الجدولُ الجامع\n{'=' * 78}")
    print(f"{'الذراع':<8}{'تغطية%':>9}{'استرجاع%':>11}"
          f"{'①':>4}{'②':>4}{'③':>4}{'④':>4}{'الحكم':>10}")
    for r in res:
        m = ["✅" if x else "🔴" for x in r["c"]]
        print(f"{r['name']:<8}{r['cover']:>9.1f}{r['recall']:>11.1f}"
              f"{m[0]:>4}{m[1]:>4}{m[2]:>4}{m[3]:>4}"
              f"{('✅ يعبر' if r['ok'] else '🔴 لا'):>10}")
    winners = [r for r in res if r["ok"]]
    if winners:
        w = max(winners, key=lambda r: r["recall"])   # قاعدةُ §③ المثبَّتة
        print(f"\n🥇 **الفائز `{w['name']}`** (الأعلى استرجاعًا بين العابرين "
              f"— قاعدةٌ مثبَّتةٌ قبل الأرقام) ⇒ **اقتراحٌ للمالك**.")
    else:
        print("\n🔴 **لا ذراعَ تعبر الأربعة ⇒ يبقى التعريفُ كما هو** "
              "(‏`S-P4` تحقّق) — ولا اقتراح.")

    # 🔑 `S-P5` — الرابطُ بسؤال المالك نفسِه
    day19 = data.get("2026-08-19") or []
    if day19:
        print(f"\n{'=' * 78}\n🔑 عشرةُ 08-19 تحت كلّ ذراع (`S-P5`)\n{'=' * 78}")
        for n, _d, p in ARMS:
            hit = sorted({r["sym"] for r in day19
                          if r.get("sym") in SISTERS and p(r)})
            print(f"  {n}: {len(hit)} من 10 ⇒ {hit or '—'}")
        print("  ⚠️ وإن كان الفائزُ صفرًا فالتعريفُ الجديد **لا يجيب سؤالَ "
              "المالك** ولو عبر إحصائيًّا.")
    else:
        print("\n⚠️ `S-P5` غيرُ مقيس: صفوفُ 2026-08-19 غيرُ محمَّلة.")

    print(f"\n{'=' * 78}\n⚠️ حدودُ صدقٍ (العقد §⑥)\n{'=' * 78}")
    print("  1) 🔴 دائريّةٌ باقيةٌ لا يزيلها الهولد-آوت: المكوّناتُ نفسُها "
          "اختيرت على هذي الصفوف ⇒ المُختبَرُ **تركيبُها** لا صلاحيتُها.")
    print("  2) واختيارُ الأذرع مُطَّلعٌ على `T-KASIH-2` — ليست عشوائية.")
    print("  3) «كاسح» لمسُ +30% لا صفقةٌ منفَّذة (بالتساوي لكلّ ذراع).")
    print("  4) المجتمعُ مراسي بوّابةِ السيولة لا كونُ السوق.")
    print("  5) والعبورُ لا يُثبت ربحية.")
    print("\n🔒 والاختبارُ النظيفُ الوحيد **السجلُّ الأماميّ** — وهو يجمع.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
