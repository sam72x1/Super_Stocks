# -*- coding: utf-8 -*-
"""🔬 مِجَسّ OTC — **الخطوة الحاسمة** (مؤقّت، يُحذف بعد القراءة).

المِجَسّ الأول أثبت أن `8-A12*` يُقرأ (61/220، صفر خطأ)، وأن **ثلثيه اكتتابات لا
نقلًا** (39/61 تاريخهم يبدأ عند الإدراج)، وأن **11** من المرجّحين نقلًا **غير
مغطّى** بتقسيم أو طرح قريب.

لكن ذلك كلّه **بلا معنى** ما لم نُجب السؤال الوحيد الذي يهمّ:

> **هل هذي الأسهم تمرّ من بوّابات هوية الارتكاز أصلًا (M1-M5)؟**

سهم الارتكاز يحتاج **انفجارًا ≥100% ثم انهيارًا ≥50%**. فلو سقط كلّ هؤلاء على
الهوية، فالوسم الثالث **يفتح بابًا على جدار** ⇒ يُغلق الملف بدليل.

يشغّل `analyze_ticker` (الجذر نفسه، بلا أي تعديل) ويطبع سبب الرفض الأول لكل رمز.
قراءة/تشخيص فقط · لا يمسّ الفرز ولا الحالة.
"""

import Super_stock as S

# الـ61 المُسجَّلين من المِجَسّ الأول — و«uncov» هم الـ11 غير المغطَّين بتقسيم/طرح قريب
UNCOV = ["ABLV", "AIFA", "AIIR", "ANNA", "ANTX", "ARQ", "AVAT", "AXG",
         "BDMD", "BEEP", "BHST"]
PRE = ["ABAT", "ACDC", "ACON", "ADAM", "AGNC", "AMPG", "ASPS", "ASST",
       "ATPC", "BCTX", "BGDE"]          # مرجّحون نقلًا لكن **مغطَّون** أصلًا


def run(tag, syms, hist):
    ok, rej = [], {}
    print(f"\n### {tag} ({len(syms)} رمزًا)\n")
    print("| الرمز | يجتاز الهوية؟ | سبب الرفض الأول |")
    print("|---|---|---|")
    for s in syms:
        df = (hist or {}).get(s)
        if df is None or len(df) < 60:
            print(f"| {s} | — | بلا بيانات كافية |")
            continue
        try:
            S._REJECT_STATS.clear()
        except Exception:                                    # noqa: BLE001
            pass
        try:
            r = S.analyze_ticker(s, df)
        except Exception as e:                               # noqa: BLE001
            print(f"| {s} | ⚠️ | انهيار: {str(e)[:60]} |")
            continue
        if r:
            ok.append(s)
            print(f"| {s} | ✅ **يجتاز** | — |")
        else:
            why = " · ".join(f"{k}={v}" for k, v in
                             (getattr(S, "_REJECT_STATS", {}) or {}).items())
            first = why.split(" · ")[0] if why else "غير معروف"
            rej[first] = rej.get(first, 0) + 1
            print(f"| {s} | ❌ | {why[:90] or '—'} |")
    print(f"\n**{tag}: يجتاز {len(ok)}/{len(syms)}**"
          + (f" ⇒ {', '.join(ok)}" if ok else ""))
    if rej:
        top = sorted(rej.items(), key=lambda x: -x[1])[:4]
        print("أكثر بوّابة رفضت: " + " · ".join(f"{k} ({v})" for k, v in top))
    return ok


def main():
    print("🔬 مِجَسّ OTC — الخطوة الحاسمة: هل يمرّون من بوّابات الهوية؟\n")
    syms = sorted(set(UNCOV + PRE))
    hist = S.download_history(syms)
    print(f"حُمِّل {len(hist or {})} من {len(syms)}")
    a = run("① غير المغطَّين بتقسيم/طرح (الشريحة التي قد يضيفها الوسم)", UNCOV, hist)
    b = run("② مرجّحون نقلًا لكن مُغطَّون أصلًا (شاهد ضبط)", PRE, hist)
    print("\n## ⚖️ الحكم\n")
    if not a:
        print("**صفر من الشريحة الجديدة يجتاز هوية الارتكاز** ⇒ الوسم الثالث يفتح بابًا")
        print("على جدار: الأسهم التي سيكشفها **مرفوضة أصلًا** على M1-M5 ⇒ **لا يُضاف**،")
        print("ويُغلق الملف بدليل بدل بقائه «مفتوحًا» إلى الأبد.")
    else:
        print(f"**{len(a)} يجتاز الهوية** ({', '.join(a)}) ⇒ الوسم **يفتح فرصة حقيقية**")
        print("لا نلتقطها اليوم ⇒ يستحقّ التنفيذ (بعد تسجيل مسبق لمعيار القبول).")
    print(f"\n(شاهد الضبط: {len(b)}/{len(PRE)} من المغطَّين يجتاز — للمقارنة فقط.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
