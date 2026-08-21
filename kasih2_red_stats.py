#!/usr/bin/env python3
"""🔴🔇 إحصاءُ «الأحمر» — تنفيذُ عقد `red_mute_prereg.md` حرفيًّا (2026-08-20).

أمرُ المالك: «زد الأيام. إذا كانت النتيجة سلبية فاكتم الأحمر. نفّذ الآن.»

- **قراءةٌ فقط**: يقرأ صفوف `kasih2_rows_*.jsonl` كما كتبتها أداةُ القياس
  (`kasih2_scan.py`) — **صفرُ إعادةِ قياس** (الحقول `c3/c4/v2/v3/kasih30`
  تُقرأ ولا تُحسب من جديد؛ مقياسٌ واحد).
- **«الأحمر»** (العقد §①): حدثُ `M5` عددُ مؤشّراته المحسوبة من الأربعة
  (شمعةُ التصديق · خضراءُ الخمس · تركُّزُ السيولة · صافي النبض) **ثلاثةٌ
  فأكثر** وصفرٌ منها في سلّته العليا. ما دون ثلاثٍ محسوبةً يمرّ بفائدة الشك.
- **المعيار الثلاثيّ** (§③) وأرضياتُ العيّنة تُقرأ كما نُصَّت — لا تُحرَّك.
- ولا كرون ولا إرسال ولا كتابةَ حالة — المُخرَجُ سطورُ سجلٍّ فقط.
"""

import glob
import json
import re
import sys

from kasih_scan import wilson, KASIH_PCT  # المقياسُ الواحد — بالاسم (K2L1)

# السلالُ العليا حرفيًّا كما تكتبها kasih2_scan (تُقفَل بمطابقةٍ سلوكية RED4)
TOP = {
    "c3": "صادقت (إغلاقٌ فوق المرساة)",
    "c4": "خضراء 3-4",
    "v2": "المرساة دون 30% (سيولة تتوالى)",
    "v3": "سيولةٌ داخلة (نبضٌ صافٍ موجب)",
}
COMPS = ("c3", "c4", "v2", "v3")

# أرضياتُ العقد §③ — أرقامُ العقد المدفوع قبل أيّ رقم، لا تُحرَّك
RED_MIN_TOTAL = 200      # «الأحمر ≥200 صفًّا مجمَّعًا»
RED_MIN_YEAR = 40        # «و≥40/سنة»
SWEEP_SHARE_MAX = 10.0   # «حصّة الأحمر من كلّ الكاسحين 10% أو أقلّ»
RECENT_MIN_DAYS = 5      # «5 جلساتٍ فأكثر مجمَّعةً»
YEARS = ("2023", "2024", "2025")


def is_red(row):
    """«الأحمر» بنصّ العقد §① — ثلاثةٌ محسوبةٌ فأكثر وصفرٌ في السلّة العليا."""
    computed = [c for c in COMPS if row.get(c) is not None]
    if len(computed) < 3:
        return False                    # يمرّ بفائدة الشك (الكتمُ إزالة)
    return not any(row.get(c) == TOP[c] for c in computed)


def _rate(k, n):
    return (k / n * 100.0) if n else 0.0


def _fmt(k, n):
    lo, hi = wilson(k, n)
    return f"{_rate(k, n):.1f}% ({k}/{n}) [{lo:.0f}·{hi:.0f}]"


def load_all():
    """يقرأ كلَّ ملفات الصفوف في المجلد الحاليّ ويصنّفها سنة/يوم من اسمها."""
    files = sorted(glob.glob("kasih2_rows_*.jsonl"))
    data = {}
    for fp in files:
        m = re.match(r"kasih2_rows_(.+)\.jsonl$", fp)
        label = m.group(1) if m else fp
        rows = []
        with open(fp, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        data[label] = rows
    return data


def stats(rows):
    """عدّاداتُ سلّةٍ واحدة: أساس · أحمر · غير أحمر · كاسحو كلٍّ · الرفيق."""
    n = len(rows)
    k = sum(1 for r in rows if r.get("kasih30"))
    red = [r for r in rows if is_red(r)]
    nred = [r for r in rows if not is_red(r)]
    kr = sum(1 for r in red if r.get("kasih30"))
    kn = sum(1 for r in nred if r.get("kasih30"))
    # الرفيق (حارسُ الدائرية — يُطبَع ولا يدخل المعيار)
    f5r = [r for r in red if r.get("kasih30_from5") is not None]
    f5n = [r for r in nred if r.get("kasih30_from5") is not None]
    return {"n": n, "k": k,
            "red_n": len(red), "red_k": kr,
            "nred_n": len(nred), "nred_k": kn,
            "f5_red": (sum(1 for r in f5r if r["kasih30_from5"]), len(f5r)),
            "f5_nred": (sum(1 for r in f5n if r["kasih30_from5"]), len(f5n))}


def main():
    data = load_all()
    if not data:
        print("⛔ لا ملفات kasih2_rows_*.jsonl — لا شيء يُحصى")
        return 2
    missing_years = [y for y in YEARS if y not in data]
    if missing_years:
        print(f"⛔ سنواتٌ ناقصة: {missing_years} — المعيار ① يشترط الثلاث")
        return 2

    day_labels = sorted(lb for lb in data if lb not in YEARS)
    print(f"📦 الملفات: {len(data)} — سنوات {list(YEARS)} · "
          f"أيام ({len(day_labels)}): {day_labels}")
    print(f"🔎 تعريف الأحمر (العقد §①): ثلاثةٌ محسوبةٌ فأكثر من "
          f"{list(COMPS)} وصفرٌ في السلّة العليا · الحاكم كاسح{KASIH_PCT:.0f}")

    per = {lb: stats(rows) for lb, rows in data.items()}

    # ── الجدول ──
    print("\n📊 الجدول (السلّة: كاسح30 [ويلسون]):")
    for lb in list(YEARS) + day_labels:
        s = per[lb]
        base = _rate(s["k"], s["n"])
        print(f"  {lb}: أساس {_fmt(s['k'], s['n'])} · "
              f"🔴 أحمر {_fmt(s['red_k'], s['red_n'])} · "
              f"غير الأحمر {_fmt(s['nred_k'], s['nred_n'])} · "
              f"نصيب الأحمر من الصفوف {_rate(s['red_n'], s['n']):.1f}% · "
              f"نصف الأساس {base / 2:.1f}%")
        f5r, f5n = s["f5_red"], s["f5_nred"]
        print(f"      الرفيق كاسح-من-د5: أحمر {_fmt(*f5r)} · "
              f"غيره {_fmt(*f5n)}")

    # ── أرضياتُ العيّنة (قبل أيّ حكم) ──
    red_total = sum(per[lb]["red_n"] for lb in per)
    floor_total = red_total >= RED_MIN_TOTAL
    floor_years = {y: per[y]["red_n"] >= RED_MIN_YEAR for y in YEARS}
    print(f"\n📏 أرضياتُ العيّنة: الأحمر مجمَّعًا {red_total} "
          f"(الحدّ {RED_MIN_TOTAL}) {'✅' if floor_total else '🔴'} · "
          + " · ".join(f"{y}={per[y]['red_n']}"
                       f"{'✅' if floor_years[y] else '🔴'}" for y in YEARS)
          + f" (الحدّ {RED_MIN_YEAR}/سنة)")
    floors_ok = floor_total and all(floor_years.values())

    # ── المعيار ① — الفصلُ التاريخيّ في كلّ سنة ──
    c1_details = []
    c1_ok = True
    for y in YEARS:
        s = per[y]
        base = _rate(s["k"], s["n"])
        red_rate = _rate(s["red_k"], s["red_n"])
        below_half = red_rate < base / 2
        r_lo, r_hi = wilson(s["red_k"], s["red_n"])
        n_lo, n_hi = wilson(s["nred_k"], s["nred_n"])
        disjoint = r_hi < n_lo
        ok = below_half and disjoint
        c1_ok = c1_ok and ok
        c1_details.append(
            f"{y}: أحمر {red_rate:.1f}% مقابل نصف الأساس {base / 2:.1f}% "
            f"{'✅' if below_half else '🔴'} · فاصلاه [{r_lo:.0f}·{r_hi:.0f}] "
            f"وغيره [{n_lo:.0f}·{n_hi:.0f}] "
            f"{'منفصلان ✅' if disjoint else 'متداخلان 🔴'}")
    print("\n① الفصلُ التاريخيّ (أدنى من نصف الأساس + ويلسون منفصلان، "
          "في كلّ سنة):")
    for d in c1_details:
        print(f"   {d}")
    print(f"   ⇒ المعيار ① {'✅ يعبر' if c1_ok else '🔴 ساقط'}")

    # ── المعيار ② — حصّةُ الأحمر من كلّ الكاسحين مجمَّعًا ──
    sweep_all = sum(per[lb]["k"] for lb in per)
    sweep_red = sum(per[lb]["red_k"] for lb in per)
    share = _rate(sweep_red, sweep_all)
    c2_ok = share <= SWEEP_SHARE_MAX
    print(f"\n② كلفةُ الكتم: الأحمرُ يحمل {sweep_red} من {sweep_all} كاسحًا "
          f"= {share:.1f}% (الحدّ {SWEEP_SHARE_MAX:.0f}%) "
          f"⇒ {'✅ يعبر' if c2_ok else '🔴 ساقط'}")

    # ── المعيار ③ — الأيامُ الحديثة لا تناقض ──
    rec_rows = [r for lb in day_labels for r in data[lb]]
    rec = stats(rec_rows)
    enough_days = len(day_labels) >= RECENT_MIN_DAYS
    rec_base = _rate(rec["k"], rec["n"])
    rec_red = _rate(rec["red_k"], rec["red_n"])
    c3_ok = enough_days and rec_red <= rec_base
    print(f"\n③ الأيامُ الحديثة ({len(day_labels)} جلسة — الحدّ "
          f"{RECENT_MIN_DAYS}): أساسها {_fmt(rec['k'], rec['n'])} · "
          f"أحمرها {_fmt(rec['red_k'], rec['red_n'])} ⇒ "
          f"{'✅ لا يناقض' if c3_ok else '🔴 ساقط/غير كافٍ'}")

    # ── كلفةٌ حيّة تقديرية (R-P3) — للعرض لا للمعيار ──
    if day_labels:
        per_day = [(_rate(per[lb]["red_n"], per[lb]["n"]), per[lb]["red_n"])
                   for lb in day_labels]
        print("\n💰 نصيبُ الأحمر من صفوف الأيام (تقدير الكلفة الحيّة): "
              + " · ".join(f"{lb}={per[lb]['red_n']}/{per[lb]['n']}"
                           for lb in day_labels)
              + f" (متوسط النسبة {sum(p for p, _ in per_day) / len(per_day):.1f}%)")

    # ── الحكم ──
    print("\n" + "═" * 60)
    if not floors_ok:
        print("⚖️ الحكم: **لا حكم — ولا كتم** (أرضيةُ العيّنة لم تُبلَغ، "
              "بنصّ العقد §③)")
        # 🛡️ خطة 035 — أرضيةُ العيّنة لم تُبلَغ ⇒ رمزُ خروجٍ مميَّز (نظيرُ
        #    exit_stop_arms: floor-not-met ⇒ 5) لا `return 0` العامّ في نهاية
        #    الدالّة — فلا يُقرأ «فُحص ولا كتم» بل «الأرضيةُ لم تُبلَغ».
        return 5
    elif c1_ok and c2_ok and c3_ok:
        print("⚖️ الحكم: 🔴 **النتيجة سلبية — الشروطُ الثلاثة معًا ⇒ "
              "يُكتَم الأحمر** (التنفيذ بنصّ العقد §④: محورُ تسليمٍ "
              "فاشلٌ-آمنٌ مفتوح · M5 فقط)")
    else:
        why = []
        if not c1_ok:
            why.append("① الفصل")
        if not c2_ok:
            why.append("② الكلفة")
        if not c3_ok:
            why.append("③ الأيام الحديثة")
        print(f"⚖️ الحكم: **لا كتم** — ساقطٌ في: {'، '.join(why)} "
              "(الشروطُ الثلاثة تلزم معًا)")
    print("⚠️ حدود الصدق (§⑥): «كاسح» لمسٌ لا تنفيذ · المؤشّراتُ ارتباطٌ "
          "لا سببية · والكتمُ يقرأ لقطةَ الخمس فقط")
    return 0


if __name__ == "__main__":
    sys.exit(main())
