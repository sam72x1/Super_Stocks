#!/usr/bin/env python3
"""🧹 إحصاءُ «فلتر الشوائب» — تنفيذُ عقد `impurity_prereg.md` حرفيًّا.

أمرُ المالك 2026-08-22: «سجّل فلتر الشوائب» ثم «شغّل».

🔴🔴 **وإفصاحٌ يسبق كلَّ رقم (العقد §⓪):** هذي **إعادةُ فتحِ ملفٍّ مُغلَق** —
`red_mute` قاس الفكرةَ بعينها وحكم «لا كتم» وأغلقها المالكُ بقراره، وشرطُ
الفتح المدوَّن «أمرٌ صريحٌ منه» وقد صدر. **وما سقط هناك الكلفةُ لا الفصل**
⇒ السؤالُ المشروعُ الوحيد: **هل ثمّةَ تعريفٌ أضيقُ من «الأحمر» تمرّ كلفتُه؟**
ولهذا **الاتّجاهُ تضييقٌ لا توسيع**، و`Z3` (الأوسع) مُدرَجٌ للمنحنى مع
تنبّؤٍ مسجَّلٍ بسقوطه (‏I-P1) لا للاعتماد.

🔒 **مقياسٌ واحدٌ لا اثنان:** التعريفُ والعتباتُ والمعيارُ الثلاثيّ وفواصلُ
ويلسون **تُستورَد بالاسم** من `kasih2_red_stats` (وهي بدورها تستورد
`kasih_scan`) — صفرُ منطقٍ مكرّر وصفرُ رقمٍ مغروس.

🔒 **قراءةٌ فقط:** صفرُ إرسالٍ وصفرُ كتابةِ حالة · بلا كرون · والإنتاجُ لا
يستوردها.

**رموزُ الخروج:** 0 حكمٌ صدر · 2 مدخلاتٌ ناقصة · **3 بوّابةُ التكامل سقطت**
(‏`Z2` لم يُعد أرقامَ `red_mute_result.md` ⇒ عطبُ أداةٍ لا نتيجة).
"""

import sys

from kasih_scan import KASIH_PCT, wilson                 # المقياسُ الواحد
from kasih2_red_stats import (COMPS, RED_MIN_TOTAL, RED_MIN_YEAR,
                              RECENT_MIN_DAYS, SWEEP_SHARE_MAX, TOP, YEARS,
                              _fmt, _rate, is_red, load_all)

# 🔒 **بوّابةُ التكامل (العقد §①)** — أرقامُ `red_mute_result.md` المنشورة.
#    `Z2` هو `is_red` حرفيًّا فيجب أن يُعيدها؛ وإلا فالمدخلاتُ أو الأداةُ
#    تغيّرت ⇒ **تُسحَب التشغيلةُ ولا تُفسَّر** (خروج 3).
PUB_RED_RATE = {"2023": 3.4, "2024": 3.9, "2025": 4.0}
PUB_NRED_RATE = {"2023": 14.2, "2024": 17.1, "2025": 16.1}
PUB_SHARE = 14.1          # حصّةُ الأحمر من كلّ الكاسحين مجمَّعًا
PUB_TOL = 0.15            # تسامحُ التدوير (عُشرٌ ونصف)


def _green(row):
    """عددُ المكوّنات في سلّتها العليا (‏«أخضر») — تعريفُ `liq_tier` نفسُه."""
    return sum(1 for c in COMPS if row.get(c) == TOP[c])


def _j1_combo(row):
    """هل الصفُّ **توليفةُ `J1`**؟

    🔴 **عيبُ نوعٍ أُصلح (2026-08-22):** `j1` في صفوف `kasih2_scan` **سلسلةُ
    سلّةٍ لا بوليان** (‏`j1_bucket` تُرجع «توليفة (قوي/مضارب × فجوة 30%+)» أو
    «الباقي» أو `None`) ⇒ صياغتي الأولى `not r.get("j1")` كانت **صفرًا أبدًا**
    لأن السلسلتين كلتاهما صادقة ⇒ ذراعٌ خاملةٌ حجمُها 0.0% في 44 ألف صفّ.
    **والقراءةُ الصحيحة هي قراءةُ `kasih2_scan` نفسِها** (بادئةُ «توليفة»).
    """
    return str(row.get("j1") or "").startswith("توليفة")


def _j1_known(row):
    """هل `J1` **محسوب**؟ (‏`None` = تعذّرت الفجوة ⇒ غيرُ معلوم).

    ⚖️ وغيرُ المعلوم **خارج الذراع** — نفسُ سابقة `is_red` («ما دون ثلاثٍ
    محسوبةً يمرّ بفائدة الشك»): **الكتمُ إزالة**، فلا يُكتَم ما لم يُقَس.
    """
    return row.get("j1") is not None


def _computed(row):
    """عددُ المكوّنات المحسوبة (قيمتُها ليست `None`)."""
    return sum(1 for c in COMPS if row.get(c) is not None)


# ── الأذرعُ الأربع، مثبَّتةٌ بنصّ العقد §① — ولا خامسة ──
ARMS = (
    ("Z1", "صفرُ خضراء والأربعُ محسوبة (الأضيق — الحاكمة)",
     lambda r: _green(r) == 0 and _computed(r) == 4),
    ("Z2", "تعريفُ «الأحمر» حرفيًّا (شاهدُ التكامل)", is_red),
    ("Z3", "صفرُ خضراء مهما كان المحسوب (الأوسع)", lambda r: _green(r) == 0),
    ("Z4", "صفرُ خضراء وبلا توليفة J1",
     lambda r: _green(r) == 0 and _j1_known(r) and not _j1_combo(r)),
)


def arm_stats(rows, pred):
    """عدّاداتُ ذراعٍ على سلّةٍ واحدة — نظيرُ `stats` معمَّمًا على أيّ تعريف."""
    n = len(rows)
    k = sum(1 for r in rows if r.get("kasih30"))
    inn = [r for r in rows if pred(r)]
    out = [r for r in rows if not pred(r)]
    ki = sum(1 for r in inn if r.get("kasih30"))
    ko = sum(1 for r in out if r.get("kasih30"))
    f5i = [r for r in inn if r.get("kasih30_from5") is not None]
    f5o = [r for r in out if r.get("kasih30_from5") is not None]
    return {"n": n, "k": k, "in_n": len(inn), "in_k": ki,
            "out_n": len(out), "out_k": ko,
            "f5_in": (sum(1 for r in f5i if r["kasih30_from5"]), len(f5i)),
            "f5_out": (sum(1 for r in f5o if r["kasih30_from5"]), len(f5o))}


def judge(name, desc, pred, data, day_labels):
    """المعيارُ الثلاثيُّ حرفيًّا كما في `red_mute_prereg §③` — بلا تحريكِ حدّ."""
    per = {lb: arm_stats(rows, pred) for lb, rows in data.items()}
    print(f"\n{'=' * 78}\n🧹 **{name}** — {desc}\n{'=' * 78}")
    for lb in list(YEARS) + day_labels:
        s = per[lb]
        base = _rate(s["k"], s["n"])
        print(f"  {lb}: أساس {_fmt(s['k'], s['n'])} · "
              f"داخل {_fmt(s['in_k'], s['in_n'])} · "
              f"خارج {_fmt(s['out_k'], s['out_n'])} · "
              f"حجمُ الذراع {_rate(s['in_n'], s['n']):.1f}% · "
              f"نصفُ الأساس {base / 2:.1f}%")
    tot_in = sum(per[lb]["in_n"] for lb in per)
    fl_t = tot_in >= RED_MIN_TOTAL
    fl_y = {y: per[y]["in_n"] >= RED_MIN_YEAR for y in YEARS}
    print(f"\n  📏 الأرضية: مجمَّعًا {tot_in} (الحدّ {RED_MIN_TOTAL}) "
          f"{'✅' if fl_t else '🔴'} · "
          + " · ".join(f"{y}={per[y]['in_n']}{'✅' if fl_y[y] else '🔴'}"
                       for y in YEARS) + f" (الحدّ {RED_MIN_YEAR}/سنة)")
    floors = fl_t and all(fl_y.values())

    c1 = True
    print("  ① الفصلُ التاريخيّ (دون نصف الأساس + ويلسون منفصلان، كلَّ سنة):")
    for y in YEARS:
        s = per[y]
        base, ri = _rate(s["k"], s["n"]), _rate(s["in_k"], s["in_n"])
        half = ri < base / 2
        ilo, ihi = wilson(s["in_k"], s["in_n"])
        olo, ohi = wilson(s["out_k"], s["out_n"])
        dis = ihi < olo
        c1 = c1 and half and dis
        print(f"     {y}: داخل {ri:.1f}% مقابل نصفِ الأساس {base / 2:.1f}% "
              f"{'✅' if half else '🔴'} · [{ilo:.0f}·{ihi:.0f}] مقابل "
              f"[{olo:.0f}·{ohi:.0f}] "
              f"{'منفصلان ✅' if dis else 'متداخلان 🔴'}")
    print(f"     ⇒ ① {'✅ يعبر' if c1 else '🔴 ساقط'}")

    sw_all = sum(per[lb]["k"] for lb in per)
    sw_in = sum(per[lb]["in_k"] for lb in per)
    share = _rate(sw_in, sw_all)
    c2 = share <= SWEEP_SHARE_MAX
    print(f"  ② الكلفة: الذراعُ يحمل {sw_in} من {sw_all} كاسحًا = "
          f"{share:.1f}% (الحدّ {SWEEP_SHARE_MAX:.0f}%) "
          f"⇒ {'✅ يعبر' if c2 else '🔴 ساقط'}")

    rec = arm_stats([r for lb in day_labels for r in data[lb]], pred)
    enough = len(day_labels) >= RECENT_MIN_DAYS
    rb, ri = _rate(rec["k"], rec["n"]), _rate(rec["in_k"], rec["in_n"])
    c3 = enough and ri <= rb
    print(f"  ③ الأيامُ الحديثة ({len(day_labels)} جلسة · الحدّ "
          f"{RECENT_MIN_DAYS}): أساسها {_fmt(rec['k'], rec['n'])} · "
          f"داخل {_fmt(rec['in_k'], rec['in_n'])} ⇒ "
          f"{'✅ لا يناقض' if c3 else '🔴 ساقط/غير كافٍ'}")

    f5i, f5o = rec["f5_in"], rec["f5_out"]
    print(f"  🛡️ الرفيقُ (حارسُ الدائرية — يُطبَع ولا يدخل المعيار): "
          f"كاسح-من-د5 داخل {_fmt(*f5i)} · خارج {_fmt(*f5o)}")

    ok = floors and c1 and c2 and c3
    print(f"  ⚖️ **الحكم: {'✅ يعبر الثلاثةَ' if ok else '🔴 لا يُعتمَد'}**"
          + ("" if floors else " — والأرضيةُ لم تُبلَغ ⇒ «لا حكم»"))
    return {"per": per, "floors": floors, "c1": c1, "c2": c2, "c3": c3,
            "ok": ok, "share": share, "tot_in": tot_in}


def main() -> int:                                               # noqa: C901
    data = load_all()
    if not data:
        print("⛔ لا ملفات kasih2_rows_*.jsonl — لا شيء يُحصى")
        return 2
    miss = [y for y in YEARS if y not in data]
    if miss:
        print(f"⛔ سنواتٌ ناقصة: {miss} — المعيار ① يشترط الثلاث")
        return 2
    day_labels = sorted(lb for lb in data if lb not in YEARS)
    total = sum(len(v) for v in data.values())
    print(f"📦 الملفات {len(data)} · سنوات {list(YEARS)} · "
          f"أيام ({len(day_labels)}): {day_labels} · **{total} صفًّا**")
    print(f"🔎 الحاكمُ كاسح{KASIH_PCT:.0f} · المكوّنات {list(COMPS)}")
    print("🔴 العقد §⓪: إعادةُ فتحِ `red_mute` بأمرِ المالك الصريح — "
          "والسؤالُ «هل ثمّةَ تعريفٌ أضيقُ تمرّ كلفتُه؟» لا «هل يفصل».")

    zero_comp = sum(1 for v in data.values() for r in v if _computed(r) == 0)
    print(f"🩺 تشخيصٌ يُطبَع ولا يغيّر تعريفًا: صفوفٌ **بلا مكوّنٍ محسوبٍ "
          f"واحد** = {zero_comp} ({_rate(zero_comp, total):.2f}%) — "
          "وهي داخلةٌ في `Z3` بنصّ تعريفه (‏«مهما كان المحسوب»).")
    j1_na = sum(1 for v in data.values() for r in v if not _j1_known(r))
    print(f"🩺 وصفوفٌ **بلا `j1` محسوب** = {j1_na} "
          f"({_rate(j1_na, total):.2f}%) — **خارج `Z4`** بفائدة الشك "
          "(سابقةُ `is_red`: ما لم يُقَس لا يُكتَم).")

    res = {n: judge(n, d, p, data, day_labels) for n, d, p in ARMS}

    # ── 🔒 بوّابةُ التكامل: `Z2` يجب أن يُعيد المنشور ──
    print(f"\n{'=' * 78}\n🔒 بوّابةُ التكامل — هل يُعيد `Z2` أرقامَ "
          f"`red_mute_result.md`؟\n{'=' * 78}")
    bad = []
    z2 = res["Z2"]["per"]
    for y in YEARS:
        s = z2[y]
        ri, ro = _rate(s["in_k"], s["in_n"]), _rate(s["out_k"], s["out_n"])
        for got, want, lbl in ((ri, PUB_RED_RATE[y], "أحمر"),
                               (ro, PUB_NRED_RATE[y], "غيره")):
            mark = "✅" if abs(got - want) <= PUB_TOL else "🔴"
            if mark == "🔴":
                bad.append(f"{y}/{lbl}: {got:.1f} مقابل المنشور {want}")
            print(f"  {y} {lbl}: {got:.1f}% مقابل المنشور {want}% {mark}")
    sh = res["Z2"]["share"]
    mark = "✅" if abs(sh - PUB_SHARE) <= PUB_TOL else "🔴"
    if mark == "🔴":
        bad.append(f"الحصّة: {sh:.1f} مقابل المنشور {PUB_SHARE}")
    print(f"  حصّةُ الكاسحين: {sh:.1f}% مقابل المنشور {PUB_SHARE}% {mark}")
    if bad:
        print("\n⛔⛔ **بوّابةُ التكامل ساقطة** — `Z2` لا يُعيد المنشور: "
              + " · ".join(bad))
        print("⇒ **عطبُ أداةٍ أو مدخلاتٍ لا نتيجة** — التشغيلةُ تُسحَب "
              "ولا تُفسَّر (العقد §①).")
        return 3
    print("✅ `Z2` يُعيد المنشورَ ⇒ المدخلاتُ والمقياسُ سليمان.")

    # ── منحنى الكلفة + بطاقةُ التنبّؤات ──
    print(f"\n{'=' * 78}\n📈 منحنى الكلفة (الحاكمةُ `Z1`)\n{'=' * 78}")
    print(f"{'الذراع':<6}{'الحجم%':>9}{'حصّةُ الكاسحين%':>18}"
          f"{'①':>4}{'②':>4}{'③':>4}{'الحكم':>10}")
    for n, _d, _p in ARMS:
        r = res[n]
        size = _rate(r["tot_in"], total)
        print(f"{n:<6}{size:>9.1f}{r['share']:>18.1f}"
              f"{'✅' if r['c1'] else '🔴':>4}{'✅' if r['c2'] else '🔴':>4}"
              f"{'✅' if r['c3'] else '🔴':>4}"
              f"{'✅ يعبر' if r['ok'] else '🔴 لا':>10}")

    s1 = _rate(res["Z1"]["tot_in"], total)
    s2 = _rate(res["Z2"]["tot_in"], total)
    rel = abs(s1 - s2) / s2 * 100 if s2 else 0.0
    print(f"\n🎯 بطاقةُ التنبّؤات (‏العقد §⑤) — تُنشَر ولو كُذّبت:")
    print(f"   I-P1 (‏`Z3` يسقط بالكلفة): "
          f"{'✅ تحقّق' if not res['Z3']['c2'] else '🔴 مكذَّب'} "
          f"(حصّتُه {res['Z3']['share']:.1f}%)")
    print(f"   I-P2 (‏`Z1` حصّتُه تحت 10%): "
          f"{'✅ تحقّق' if res['Z1']['c2'] else '🔴 مكذَّب'} "
          f"({res['Z1']['share']:.1f}%)")
    print(f"   I-P4 (‏حجمُ `Z1` بين 15 و30%): "
          f"{'✅ تحقّق' if 15 <= s1 <= 30 else '🔴 مكذَّب'} ({s1:.1f}%)")
    print(f"   I-P5 (‏خطرُ التكرار — فرقُ الحجم دون 10% نسبيًّا): "
          f"{'🔴 وقع ⇒ تكرارٌ لا جديد' if rel < 10 else '✅ لم يقع'} "
          f"(‏`Z1` {s1:.1f}% مقابل `Z2` {s2:.1f}% ⇒ فرقٌ نسبيٌّ {rel:.0f}%)")
    print(f"   I-P6 (‏`Z4` لا يعبر ②): "
          f"{'✅ تحقّق' if not res['Z4']['c2'] else '🔴 مكذَّب'} "
          f"({res['Z4']['share']:.1f}%)")

    print(f"\n{'=' * 78}\n⚠️ حدودُ صدقٍ (العقد §⑥) — تُقرأ **مع** الأرقام:")
    print("   1) 🔴 دائريّةٌ مُعلَنة: المكوّناتُ اختيرت في `T-KASIH-2` على "
          "المقياس نفسِه وعلى الصفوف نفسِها ⇒ وصفُ عيّنةٍ لا تنبّؤ.")
    print("   2) إعادةُ فتحٍ لا اكتشاف — و`Z2` أعاد المنشورَ (بوّابةٌ أعلاه).")
    print("   3) «كاسح» لمسُ +30% لا صفقةٌ منفَّذة ⇒ سقفٌ متفائل.")
    print("   4) الكتمُ **إزالة**: إشعارٌ لم يُرسَل لا يُسترجَع.")
    print("   5) التعريفُ من نافذة الخمس حصرًا — والأثرُ يُقاس بحصّة ② لا بالرأي.")
    print("   6) الشريحةُ الحديثة صغيرة ⇒ ③ شرطُ عدمِ تناقضٍ لا شرطُ إثبات.")
    print("   7) العبورُ لا يُثبت ربحيّة — يُثبت أن الشريحةَ أفقرُ كاسحين.")
    print("\n🔒 سقفُ النجاح (§④): **اقتراحٌ للمالك لا تنفيذٌ آليّ** — "
          "وقرارُ التسليم قرارُه وحده.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
