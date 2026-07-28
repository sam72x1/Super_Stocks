#!/usr/bin/env python3
"""🌏📏 مُجمِّع T-CMAG عبر السنوات الثلاث — يطبّق `country_magnitude_prereg.md` حرفيًّا.

يُكتب **قبل رؤية أي نتيجة** (نفس انضباط التسجيل المسبق): المعيار الخماسي مكتوب هنا
كشيفرة لا كحُكم بشري بعديّ، فلا مجال لتحريكه بعد ظهور الأرقام.

الاستعمال: `python3 cmag_assemble.py backtest_2023.csv backtest_2024.csv backtest_2025.csv`
(اسم الملفّ يجب أن يحوي السنة). **تحليل/طباعة فقط** — لا يستورد البوت ولا يمسّ أي حالة.
"""
import csv
import sys

MOVE_PCT = 30.0        # المقياس المساند («حركة فيصل 30-50%»)
MIN_SLICE = 20         # ④ العيّنة
MIN_GAP = 5.0          # ② حجم الفرق (نقاط مئوية)
MIN_RATIO = 1.5        # ② نسبة الوسيطين
CN = ("China", "Hong Kong")


def median(v):
    s = sorted(v)
    n = len(s)
    if not n:
        return None
    m = n // 2
    return s[m] if n % 2 else (s[m - 1] + s[m]) / 2.0


def wilson(k, n):
    if n <= 0:
        return (0.0, 0.0)
    z, p = 1.96, k / n
    d = 1.0 + z * z / n
    c = p + z * z / (2 * n)
    m = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return (max(0.0, (c - m) / d) * 100, min(1.0, (c + m) / d) * 100)


def load(path):
    """يقرأ صفقات سنة: المُعبَّأة فقط (mg_pre_stop موجود) ومعلومة الدولة."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            mg, cty = (r.get("mg_pre_stop") or "").strip(), (r.get("country") or "").strip()
            if r.get("outcome") == "no_fill" or not mg or mg.lower() in ("none", "nan"):
                continue
            try:
                g = float(mg)
            except ValueError:
                continue
            rows.append({"g": g, "cty": cty, "known": bool(cty) and cty != "—"})
    return rows


def slices(rows):
    kn = [r for r in rows if r["known"]]
    return ([r["g"] for r in kn if r["cty"] in CN],
            [r["g"] for r in kn if r["cty"] not in CN],
            len(rows) - len(kn))


def describe(tag, a, b, unk):
    ma, mb = median(a), median(b)
    ka = sum(1 for g in a if g >= MOVE_PCT)
    kb = sum(1 for g in b if g >= MOVE_PCT)
    print(f"\n=== {tag} ===  (مجهولة الدولة: {unk} — تُعرَض ولا تُقارَن)")
    for lbl, v, m, k in (("الصين/هونغ كونغ", a, ma, ka), ("بقية الدول", b, mb, kb)):
        if not v:
            print(f"  {lbl}: صفر صفقة")
            continue
        lo, hi = wilson(k, len(v))
        print(f"  {lbl}: n={len(v)} · وسيط {m:.1f}% · متوسط {sum(v)/len(v):.1f}% · "
              f"بلغ {MOVE_PCT:.0f}%+ = {k} ({k/len(v)*100:.1f}%، Wilson {lo:.1f}-{hi:.1f}%)")
    if not (a and b):
        return None
    gap = ma - mb
    ratio = (max(ma, mb) / min(ma, mb)) if min(ma, mb) > 0 else float("inf")
    lo_a, hi_a = wilson(ka, len(a))
    lo_b, hi_b = wilson(kb, len(b))
    sep = lo_a > hi_b or lo_b > hi_a
    print(f"  فرق الوسيطين (الصين − البقية): {gap:+.1f} نقطة · النسبة {ratio:.2f}× · "
          f"فاصلا Wilson {'منفصلان' if sep else 'متداخلان'}")
    return {"gap": gap, "ratio": ratio, "sep": sep, "na": len(a), "nb": len(b),
            "ma": ma, "mb": mb}


def main(paths):
    years, pooled_a, pooled_b, pooled_u = {}, [], [], 0
    for p in paths:
        y = next((t for t in ("2023", "2024", "2025", "2022", "2026") if t in p), p)
        a, b, unk = slices(load(p))
        pooled_a += a
        pooled_b += b
        pooled_u += unk
        years[y] = describe(f"سنة {y}", a, b, unk)
    pool = describe("المجمَّع (ثلاث سنوات)", pooled_a, pooled_b, pooled_u)

    print("\n" + "=" * 62)
    print("📋 المعيار المسجَّل مسبقًا (country_magnitude_prereg.md §④) — تطبيق حرفي")
    ok = {}
    valid = [y for y, v in years.items() if v]
    # ① ثبات الاتجاه في السنوات الثلاث كلها
    signs = {y: (1 if years[y]["gap"] > 0 else -1 if years[y]["gap"] < 0 else 0)
             for y in valid}
    ok["① ثبات الاتجاه (نفس الشريحة أعلى في الثلاث)"] = (
        len(valid) == len(paths) and len(set(signs.values())) == 1
        and 0 not in signs.values())
    # ② حجم الفرق في كلّ سنة
    ok[f"② الفرق ≥{MIN_GAP:.0f} نقاط و≥{MIN_RATIO}× في كلّ سنة"] = (
        len(valid) == len(paths)
        and all(abs(years[y]["gap"]) >= MIN_GAP and years[y]["ratio"] >= MIN_RATIO
                for y in valid))
    # ③ الدلالة على المقياس المساند مجمَّعًا
    ok["③ فاصلا Wilson منفصلان مجمَّعًا"] = bool(pool and pool["sep"])
    # ④ العيّنة في كلّ شريحة وكلّ سنة
    ok[f"④ ≥{MIN_SLICE} صفقة/شريحة/سنة"] = (
        len(valid) == len(paths)
        and all(years[y]["na"] >= MIN_SLICE and years[y]["nb"] >= MIN_SLICE
                for y in valid))
    # ⑤ لا انقلاب: اتجاه المجمَّع = اتجاه السنوات
    ok["⑤ اتجاه المجمَّع = اتجاه السنوات"] = bool(
        pool and signs and len(set(signs.values())) == 1
        and (1 if pool["gap"] > 0 else -1) == next(iter(signs.values())))
    for k, v in ok.items():
        print(f"  {'✅' if v else '❌'} {k}")
    print("=" * 62)
    # ⚠️ تمييز صدق (يُكتب قبل النتائج): «الفرضية سقطت» ≠ «العيّنة لا تكفي».
    # الأولى نتيجة سلبية حقيقية، والثانية **لا حكم**. الخلط بينهما ادّعاء زائد.
    sample_key = f"④ ≥{MIN_SLICE} صفقة/شريحة/سنة"
    others = [v for k, v in ok.items() if k != sample_key]
    if all(ok.values()):
        v = ("**استوفت المعيار كاملًا** — تُعرَض على المالك بالأرقام "
             "(وسقفها المسجَّل: سطر عرض فقط)")
    elif not ok[sample_key] and all(others):
        v = ("**لا حكم — العيّنة لا تكفي**: الشروط الأخرى تحقّقت لكن شريحةً واحدة على "
             "الأقل دون الحدّ. هذه ليست نتيجة سلبية؛ لا تُعتمد ولا تُنفى، وتُعاد "
             "بعيّنة أوسع (أو تُترَك) بقرار المالك.")
    else:
        v = ("**فشلت** — تبقى الدولة عمود تحليل بلا أي دور قرار "
             "(كما أُغلقت T-ACC · T-SHORT · T-EXIT · T-STOP)")
    print("🏁 الحكم: " + v)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("الاستعمال: cmag_assemble.py <csv سنة> [<csv> …]")
    main(sys.argv[1:])
