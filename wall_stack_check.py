"""🧱 مُشغِّل مكدّس الجدران — يمشي لقطةً مجمَّدة ويقشّر جدران كل يومٍ مرفوض.

الاستعمال (‏workflow `wall_stack.yml`):
    WS_FROZEN=<path>   لقطة `load_frozen_dataset` (إلزامية — لا تحميل حيّ)
    WS_SYMBOLS=A,B,C   رموزٌ صريحة (فارغ = عيّنة من الكون)
    WS_MAX_SYMBOLS=60  سقف الرموز عند عدم التحديد
    WS_STEP=5          خطوة المشي بالجلسات (تقليل الكلفة)
    WS_MIN_BARS=260    أقلّ تاريخٍ لازم قبل تقييم يوم

🔒 تشخيص/بحث: **صفر كتابة حالة · صفر تنبيه · صفر مسّ إنتاج.** الحكم في كل خطوة من
`analyze_ticker` الإنتاجيّ نفسه (‏`wall_stack.peel_walls`).

⚠️ **حدُّ صدقٍ يُطبع مع النتيجة:** التقشير يقرأ «ماذا يحجبه **لو** فُتح ما قبله»، لا
تقييمًا متوازيًا للأربع عشرة — وهو المطلوب لسؤال «ماذا يدخل لو فتحتُ M5؟».
"""
from __future__ import annotations

import os
import sys

import Super_stock as S
import wall_stack as W


def _int(name, default):
    try:
        return int(str(os.environ.get(name, "")).strip() or default)
    except (TypeError, ValueError):
        return default


def run():
    path = (os.environ.get("WS_FROZEN") or "").strip()
    if not path or not os.path.exists(path):
        print("⛔ WS_FROZEN غير موجود — اللقطة المجمَّدة **إلزامية** "
              "(لا تحميل حيّ: النتيجة يجب أن تكون قابلة لإعادة الإنتاج).")
        return 2

    hist, splits_map, asof = S.load_frozen_dataset(path)
    if not hist:
        print("⛔ اللقطة فارغة")
        return 2

    want = [x.strip().upper() for x in
            (os.environ.get("WS_SYMBOLS") or "").split(",") if x.strip()]
    cap = _int("WS_MAX_SYMBOLS", 60)
    step = max(1, _int("WS_STEP", 5))
    min_bars = _int("WS_MIN_BARS", 260)

    if want:
        syms = [s for s in want if s in hist]
        missing = [s for s in want if s not in hist]
    else:
        syms = sorted(hist.keys())[:cap]      # حتميّ: مرتَّبٌ لا عشوائيّ
        missing = []

    print(f"🧱 مكدّس الجدران · لقطة as-of {asof} · {len(hist)} رمزًا بالكون")
    print(f"   المفحوص: {len(syms)} رمزًا · خطوة {step} جلسة · أقلّ تاريخ {min_bars}")
    if missing:
        print(f"   ⚠️ غير موجود باللقطة: {', '.join(missing)}")

    rows, n_days, n_pass_direct, n_err = [], 0, 0, 0
    for sym in syms:
        df = hist.get(sym)
        if df is None or len(df) < min_bars:
            continue
        for i in range(min_bars, len(df), step):
            sub = df.iloc[:i]
            n_days += 1
            try:
                if S.analyze_ticker(sym, sub):
                    n_pass_direct += 1        # مقبولٌ أصلًا — لا جدران له
                    continue
            except Exception:
                n_err += 1
                continue
            rows.append(W.peel_walls(S, sym, sub))

    print(f"   أيامٌ قُيِّمت: {n_days} · مقبولة أصلًا: {n_pass_direct} · "
          f"مرفوضة (قُشِّرت): {len(rows)} · أخطاء: {n_err}")
    if not rows:
        print("   ⚠️ لا يومَ مرفوض — لا تقرير (وهذا نتيجةٌ لا عطل)")
        return 0

    agg = W.aggregate(rows)
    print()
    for line in W.format_report(agg):
        print(line)

    # 🔑 السطر الذي بُنيت الأداة لأجله
    sole = agg.get("sole_blocker") or {}
    tot = sum(sole.values())
    print()
    print(f"🔑 الخلاصة: {tot} من {len(rows)} يومًا مرفوضًا ({100*tot/len(rows):.1f}%) "
          f"تحجبه **بوّابةٌ واحدة فقط** ⇒ هذي وحدها هي التي يفتحها فتحُ تلك البوّابة.")
    print("⚠️ حدّ صدق: التقشير تسلسليّ (ماذا يحجب **لو** فُتح ما قبله) لا تقييمٌ متوازٍ · "
          "واللقطة كون ناسداك اليوم (انحياز بقاء) · والعيّنة بخطوة "
          f"{step} جلسات لا كل جلسة.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
