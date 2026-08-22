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

from kasih_scan import KASIH_PCT, wilson
from kasih2_red_stats import COMPS, TOP, YEARS, load_all
from strong2_scan import SISTERS, _green, _j1

DAY = "2026-08-19"          # جلسةُ «رداك وخواتها» — يومُ سؤال المالك
ADOPTED = 3                 # حدُّ «قوي» النافذُ بعد اعتماد `S2`

_AR = {"c3": "التصديق", "c4": "الخضراء", "v2": "التوالي", "v3": "النبض"}


def _computed(r):
    """كم مكوّنًا **حُسب فعلًا** — غيرُ المحسوب ليس سالبًا."""
    return sum(1 for c in COMPS if r.get(c) is not None)


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
    print(f"{'الرمز':<7}{'عدّاد':>6}{'محسوب':>7}  "
          f"{'التصديق':<9}{'الخضراء':<9}{'التوالي':<9}{'النبض':<9}"
          f"{'J1':>4}{'فجوة%':>8}{'كسح30':>7}  الفئة")
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
        gap = r.get("gap_pct")
        tier = "قوي" if g >= ADOPTED else ("ضعيف" if g <= 1 else "متوسط")
        print(f"{s:<7}{g:>6}{cm:>7}  "
              f"{marks[0]:<9}{marks[1]:<9}{marks[2]:<9}{marks[3]:<9}"
              f"{('✅' if _j1(r) else '—'):>4}"
              f"{(f'{float(gap):.0f}' if gap is not None else '—'):>8}"
              f"{('✅' if r.get('kasih30') else '—'):>7}  {tier}")
        out.append((s, g, cm, r))
    return out


def ladder(data):
    """§② منحنى كلفةِ العدّاد — ماذا يُشترى وبأيّ ثمن عند كلّ درجة."""
    years = {y: data[y] for y in YEARS if y in data}
    print(f"\n{'=' * 78}\n② منحنى الكلفة: «قوي = العدّادُ t فأكثر» "
          f"على السنوات الثلاث\n{'=' * 78}")
    print(f"{'الحدّ t':<8}{'تغطية%':>9}{'استرجاع%':>11}"
          f"{'داخلَه%':>10}{'خارجَه%':>10}{'ضِعف':>7}  فصلٌ منفصل")
    rows_all = [r for v in years.values() for r in v]
    n_all = len(rows_all)
    k_all = sum(1 for r in rows_all if r.get("kasih30"))
    print(f"  الأساس: {n_all} صفًّا · {k_all} كاسحًا "
          f"({_rate(k_all, n_all):.1f}%) · كاسح{KASIH_PCT:.0f}")
    for t in (4, 3, 2, 1):
        inn = [r for r in rows_all if _green(r) >= t]
        out = [r for r in rows_all if _green(r) < t]
        ki = sum(1 for r in inn if r.get("kasih30"))
        ko = sum(1 for r in out if r.get("kasih30"))
        ri, ro = _rate(ki, len(inn)), _rate(ko, len(out))
        lo_i, _ = wilson(ki, len(inn))
        _, hi_o = wilson(ko, len(out))
        mark = "◀ النافذ" if t == ADOPTED else ""
        print(f"  {t} فأكثر{'':<2}{_rate(len(inn), n_all):>9.1f}"
              f"{_rate(ki, k_all):>11.1f}{ri:>10.1f}{ro:>10.1f}"
              f"{(ri / ro if ro else 0):>7.2f}  "
              f"{'✅' if lo_i > hi_o else '🔴'} {mark}")


def why_six(sis):
    """§③ لكلّ خارجٍ: ما أقلُّ حدٍّ يلتقطه — وبأيّ ثمنٍ من §②."""
    outs = [(s, g, cm, r) for s, g, cm, r in sis if g < ADOPTED]
    print(f"\n{'=' * 78}\n③ الباقون خارجَ «قوي» ({len(outs)}) — "
          f"ما الذي يلزم لالتقاط كلٍّ منهم\n{'=' * 78}")
    for s, g, cm, r in outs:
        miss = [_AR[c] for c in COMPS if r.get(c) is not None
                and r.get(c) != TOP[c]]
        unk = [_AR[c] for c in COMPS if r.get(c) is None]
        swept = "✅ كسح" if r.get("kasih30") else "لم يكسح"
        if g == 0:
            need = "لا يلتقطه إلّا إلغاءُ الشرط كلِّه (عدّادُه صفر)"
        else:
            need = f"يلتقطه الحدُّ «{g} فأكثر»"
        print(f"  {s}: عدّاد {g} من {cm} محسوب · {swept} ⇒ {need}")
        if miss:
            print(f"      نقضت: {' · '.join(miss)}")
        if unk:
            print(f"      لم تُحسب: {' · '.join(unk)} (ليست سالبة)")


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
    ladder(data)
    why_six(sis)

    print(f"\n{'=' * 78}\n④ حدودُ صدق\n{'=' * 78}")
    print("  1) 🔴 الدائريّةُ قائمة: المكوّناتُ اختيرت على هذي الصفوف "
          "⇒ الأرقامُ **وصفُ عيّنةٍ لا تنبّؤ**.")
    print("  2) «كسح» لمسُ +30% لا صفقةٌ منفَّذة.")
    print("  3) يومٌ واحدٌ مقامُه عشرة ⇒ **لا حكمَ منه**؛ الحكمُ من §②.")
    print("  4) غيرُ المحسوب **ليس سالبًا** — والعدّادُ يخلطهما بالبناء.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
