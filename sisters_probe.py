#!/usr/bin/env python3
"""🔎🔟 مِجَسُّ «الستّةُ الباقون» — لماذا لا يصيرون «قوي»؟

سؤالُ المالك 2026-08-22 بعد اعتماد `S2`: «بخصوص 6 الباقين — بلا اشتراط
الفجوة والصنف، 4 من عشرتك يصيرون قوي — ما لقيت لهم حل؟ مب منطقي».

⚖️ **مِجَسُّ تشخيصٍ لا تجربةَ حكم** (سابقةُ `wall_stack` · `flatfiles_probe` ·
`liq_case_probe`) ⇒ **بلا تسجيلٍ مسبق، وسقفُ نجاحه صفر**: لا يُغيّر تعريفًا
ولا عتبةً ولا يقترح اعتمادًا. وإن أظهر درجةً تستحقّ الاختبار فذاك **تسجيلٌ
جديدٌ بأمرِ المالك** — والأرقامُ هنا **وصفيّةٌ على صفوفٍ اختيرت مكوّناتُها
عليها** (الدائريّةُ المدوَّنة في `strong2_result §⑦-1` قائمةٌ كما هي).

🔒 **مقياسٌ واحدٌ لا اثنان:** `_green`/`_j1`/`SISTERS` تُستورَد من
`strong2_scan` بالاسم، والسلالُ من `kasih2_red_stats` — صفرُ منطقٍ مكرّر
وصفرُ رقمٍ مغروس.

🔒 **قراءةٌ فقط:** صفرُ إرسالٍ وصفرُ كتابةِ حالة · بلا كرون · والإنتاجُ لا
يستوردها · و`liq_tier` لا تُمَسّ.

**رموزُ الخروج:** 0 طُبع التشخيص · 2 مدخلاتٌ ناقصة · 4 صفوفُ 08-19 غائبة
(‏السؤالُ نفسُه غيرُ قابلٍ للإجابة ⇒ يُعلَن ولا يُخمَّن).
"""

import sys

from kasih_scan import KASIH_DESC, KASIH_PCT, wilson
from kasih2_red_stats import COMPS, TOP, YEARS, load_all
from strong2_scan import SISTERS, _green, _j1
from Super_stock import LIQ_TIER_STRONG_MIN as _S_STRONG_MIN

DAY = "2026-08-19"          # جلسةُ «رداك وخواتها» — يومُ سؤال المالك
# 🔒 حدُّ «قوي» **من الإنتاج** لا نسخةً — فلا يطبع المِجَسُّ عتبةً بائتة
#    (‏`SIS4` يقفله سلوكيًّا).
ADOPTED = _S_STRONG_MIN

_AR = {"c3": "التصديق", "c4": "الخضراء", "v2": "التوالي", "v3": "النبض"}


def _computed(r):
    """كم مكوّنًا **حُسب فعلًا** — غيرُ المحسوب ليس سالبًا."""
    return sum(1 for c in COMPS if r.get(c) is not None)


def _mg1(r):
    """أقصى ارتفاعٍ من **إغلاق شمعة المِرساة** (كرت `M1`) قبل الخروج البنيويّ."""
    v = r.get("mg_after")
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _mg5(r):
    """أقصى ارتفاعٍ من **سعر كرت `M5`** — الرقمُ الذي يراه المالك.
    متاحٌ في ملفّات اليوم الواحد وحدها (`_ev`)؛ وإلّا `None` **ولا يُخمَّن**."""
    ev = r.get("_ev") or {}
    v = ev.get("mg5")
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _rate(k, n):
    return (k / n * 100.0) if n else 0.0


def sisters_table(rows):
    """§① العشرةُ صفًّا صفًّا — الجوابُ المباشر على سؤال المالك."""
    by = {}
    for r in rows:
        s = r.get("sym")
        if s in SISTERS and s not in by:
            by[s] = r
    print(f"\n{'=' * 78}\n① عشرةُ {DAY} — مكوّناتُها صفًّا صفًّا\n{'=' * 78}")
    print(f"{'الرمز':<7}{'عدّاد':>6}  "
          f"{'التصديق':<9}{'الخضراء':<9}{'التوالي':<9}{'النبض':<9}"
          f"{'J1':>4}{'من M5%':>9}{'من M1%':>9}{'الخروج':>8}  الفئة")
    out = []
    for s in SISTERS:
        r = by.get(s)
        if r is None:
            print(f"{s:<7}{'—':>6}{'—':>7}  غائبٌ عن صفوف اليوم")
            continue
        g, cm = _green(r), _computed(r)
        marks = []
        for c in COMPS:
            v = r.get(c)
            marks.append("✅" if v == TOP[c] else ("⬜" if v is None else "❌"))
        tier = "قوي" if g >= ADOPTED else ("ضعيف" if g <= 1 else "متوسط")
        m5, m1 = _mg5(r), _mg1(r)
        print(f"{s:<7}{g:>6}  "
              f"{marks[0]:<9}{marks[1]:<9}{marks[2]:<9}{marks[3]:<9}"
              f"{('✅' if _j1(r) else '—'):>4}"
              f"{(f'{m5:+.1f}' if m5 is not None else '—'):>9}"
              f"{(f'{m1:+.1f}' if m1 is not None else '—'):>9}"
              f"{str(r.get('exit') or '—'):>8}  {tier}")
        out.append((s, g, cm, r))
    n5 = sum(1 for _s, _g, _c, r in out if _mg5(r) is not None)
    print(f"  ℹ️ «من M5» = أقصى ارتفاعٍ عن سعر كرت M5 قبل الخروج البنيويّ "
          f"(متاحٌ في {n5} من {len(out)}) · «من M1» عن إغلاق شمعة المِرساة.")
    print("  🔴 وكلاهما **لمسٌ لا بيعٌ منفَّذ** — سقفُ الربح لا الربحُ المحقَّق.")
    return out


# 🎯 بارات النجاح — أمرُ المالك 2026-08-22: «المهمّ انه يكون ربحان»
#    ⚖️ **تُطبَع كلُّها معًا** ولا يُنتقى منها الأنسب (ذاك «قِسْ حتى تعجبك»)،
#    **ومعها نسبةُ الأساس عند كلِّ بار** — فبارٌ أدنى يرفع الجميعَ لا الفئةَ
#    وحدَها، والمعنى في **المضاعف** لا في النسبة الخام.
OWNER_BAR = 10.0     # رقمُ المالك نفسِه: «و واحد حقق لو 10٪ عادي»
BARS = ((0.0, "أيّ ربح"), (OWNER_BAR, f"‏+{OWNER_BAR:.0f}% فأكثر"),
        (20.0, "‏+20% فأكثر"), (KASIH_PCT, f"‏+{KASIH_PCT:.0f}% فأكثر"),
        (KASIH_DESC[0], f"‏+{KASIH_DESC[0]:.0f}% فأكثر"))


def _tier_of(r):
    g = _green(r)
    return "قوي" if g >= ADOPTED else ("ضعيف" if g <= 1 else "متوسط")


def bars_by_tier(data):
    """§② هل تفصل الفئةُ على بارِ المالك أيضًا — ومعها الأساسُ عند كلّ بار."""
    rows = [r for y in YEARS if y in data for r in data[y]]
    have = [r for r in rows if _mg1(r) is not None]
    print(f"\n{'=' * 78}\n② الفئةُ عند بارات النجاح المختلفة "
          f"(السنواتُ الثلاث)\n{'=' * 78}")
    print(f"  المقام: {len(have)} صفًّا من {len(rows)} فيها ربحٌ مقيس · "
          "القياسُ **من إغلاق شمعة المِرساة** (`mg_after`)")
    print(f"{'البار':<14}{'الأساس%':>9}{'🥇 قوي%':>10}{'🥈 وسط%':>10}"
          f"{'🥉 ضعيف%':>11}{'قوي÷أساس':>11}{'ضعيف÷أساس':>12}")
    for thr, lab in BARS:
        hit = {"قوي": [0, 0], "متوسط": [0, 0], "ضعيف": [0, 0]}
        nb = 0
        for r in have:
            t = _tier_of(r)
            hit[t][1] += 1
            if _mg1(r) > thr:
                hit[t][0] += 1
                nb += 1
        base = _rate(nb, len(have))
        rs = {t: _rate(hit[t][0], hit[t][1]) for t in hit}
        print(f"{lab:<14}{base:>9.1f}{rs['قوي']:>10.1f}{rs['متوسط']:>10.1f}"
              f"{rs['ضعيف']:>11.1f}"
              f"{(rs['قوي'] / base if base else 0):>11.2f}"
              f"{(rs['ضعيف'] / base if base else 0):>12.2f}")
    print("  🔑 المضاعفُ هو المعنى: بارٌ أدنى يرفع الأساسَ والفئةَ معًا.")


def ladder(data, thr, lab):
    """§②-ب منحنى كلفةِ العدّاد **عند بارِ المالك** لا عند بارِ الثلاثين."""
    rows = [r for y in YEARS if y in data for r in data[y]
            if _mg1(r) is not None]
    n_all = len(rows)
    k_all = sum(1 for r in rows if _mg1(r) > thr)
    print(f"\n{'=' * 78}\n②-ب منحنى الكلفة عند بار «{lab}» — "
          f"«قوي = العدّادُ t فأكثر»\n{'=' * 78}")
    print(f"  الأساس: {n_all} صفًّا · {k_all} رابحًا "
          f"({_rate(k_all, n_all):.1f}%)")
    print(f"{'الحدّ t':<10}{'تغطية%':>9}{'استرجاع%':>11}"
          f"{'داخلَه%':>10}{'خارجَه%':>10}{'مقابل الأساس':>14}  فصلٌ منفصل")
    for t in (4, 3, 2, 1):
        inn = [r for r in rows if _green(r) >= t]
        out = [r for r in rows if _green(r) < t]
        ki = sum(1 for r in inn if _mg1(r) > thr)
        ko = sum(1 for r in out if _mg1(r) > thr)
        ri, ro = _rate(ki, len(inn)), _rate(ko, len(out))
        lo_i, _ = wilson(ki, len(inn))
        _, hi_o = wilson(ko, len(out))
        base = _rate(k_all, n_all)
        mark = "◀ النافذ" if t == ADOPTED else ""
        print(f"  {t} فأكثر{'':<3}{_rate(len(inn), n_all):>9.1f}"
              f"{_rate(ki, k_all):>11.1f}{ri:>10.1f}{ro:>10.1f}"
              f"{(ri / base if base else 0):>14.2f}  "
              f"{'✅' if lo_i > hi_o else '🔴'} {mark}")


def why_six(sis):
    """§③ الباقون خارجَ «قوي» — بربحِهم الفعليّ لا ببوليانِ الكسح."""
    outs = [(s, g, cm, r) for s, g, cm, r in sis if g < ADOPTED]
    print(f"\n{'=' * 78}\n③ الباقون خارجَ «قوي» ({len(outs)}) — "
          f"كم ربح كلٌّ منهم فعلًا\n{'=' * 78}")
    for s, g, cm, r in outs:
        m5, m1 = _mg5(r), _mg1(r)
        best = m5 if m5 is not None else m1
        if best is None:
            verdict = "لا ربحَ مقيسًا"
        elif best > 0:
            verdict = f"**ربح** حتى {best:+.1f}% (لمسًا)"
        else:
            verdict = f"لم يربح ({best:+.1f}%)"
        need = ("لا يلتقطه إلّا إلغاءُ الشرط كلِّه (عدّادُه صفر)"
                if g == 0 else f"يلتقطه الحدُّ «{g} فأكثر»")
        print(f"  {s}: عدّاد {g} من {cm} · {verdict} · الخروج "
              f"{r.get('exit') or '—'} ⇒ {need}")
        miss = [_AR[c] for c in COMPS if r.get(c) is not None
                and r.get(c) != TOP[c]]
        if miss:
            print(f"      نقضت: {' · '.join(miss)}")
    vals = [(_mg5(r) if _mg5(r) is not None else _mg1(r))
            for _s, _g, _c, r in outs]
    ok = [v for v in vals if v is not None and v > 0]
    print(f"  🎯 بمعيار المالك «المهمّ يكون ربحان»: **{len(ok)} من "
          f"{len(outs)}** ربحوا (لمسًا) — والقيمُ: "
          + " · ".join(f"{v:+.1f}%" for v in vals if v is not None))


def main() -> int:
    data = load_all()
    if not data:
        print("⛔ لا ملفات kasih2_rows_*.jsonl — لا شيء يُقاس")
        return 2
    missing = [y for y in YEARS if y not in data]
    if missing:
        print(f"⛔ سنواتٌ ناقصة: {missing} — منحنى §② يشترط الثلاث")
        return 2
    day = data.get(DAY)
    if not day:
        print(f"⛔ صفوفُ {DAY} غائبة ⇒ سؤالُ المالك غيرُ قابلٍ للإجابة هنا "
              "— يُعلَن ولا يُخمَّن")
        return 4
    tot = sum(len(v) for v in data.values())
    print(f"📦 الملفات {len(data)} · **{tot} صفًّا** · "
          f"وحدُّ «قوي» النافذ = العدّاد {ADOPTED} فأكثر (اعتمادُ `S2`)")
    print("⚖️ مِجَسُّ تشخيصٍ — **سقفُ نجاحه صفر**: لا يُغيّر تعريفًا ولا عتبة.")

    sis = sisters_table(day)
    bars_by_tier(data)
    ladder(data, 0.0, "أيّ ربح")
    ladder(data, OWNER_BAR, f"‏+{OWNER_BAR:.0f}% فأكثر")
    ladder(data, KASIH_PCT, f"‏+{KASIH_PCT:.0f}% فأكثر")
    why_six(sis)

    print(f"\n{'=' * 78}\n④ حدودُ صدق\n{'=' * 78}")
    print("  1) 🔴 الدائريّةُ قائمة: المكوّناتُ اختيرت على هذي الصفوف "
          "⇒ الأرقامُ **وصفُ عيّنةٍ لا تنبّؤ**.")
    print("  2) 🔴 **الربحُ هنا «لمسٌ» لا بيعٌ منفَّذ** (أقصى ارتفاعٍ قبل "
          "الخروج البنيويّ) ⇒ **سقفُ الربح لا الربحُ المحقَّق** · والعائدُ "
          "المحقَّق **غيرُ مخزَّنٍ في الصفوف** فلا يُخمَّن.")
    print("  2-ب) وقياسُ السنوات الثلاث **من إغلاق شمعة المِرساة** لأن "
          "`mg5` لا يوجد إلّا في ملفّات اليوم الواحد — والأساسُ والفئةُ "
          "بالمقياس نفسِه فالمقارنةُ سليمة.")
    print("  3) يومٌ واحدٌ مقامُه عشرة ⇒ **لا حكمَ منه**؛ الحكمُ من §②.")
    print("  4) غيرُ المحسوب **ليس سالبًا** — والعدّادُ يخلطهما بالبناء.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
