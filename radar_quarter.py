#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⏱️📏 **T-QUARTER** — هل «صمد ‏≥15 دقيقة» يفصل الحقيقيَّ عن الكاذب؟

عقدُه `quarter_prereg.md` **مدفوعٌ قبل أيّ رقم**. أداةٌ **مستقلّة** عن
`radar_read.py` عمدًا: ذاك نشر رقمًا (‏74.2%) فيبقى بت-بت قابلًا لإعادة الإنتاج.

🔒 **صفرُ منطقٍ جديد:** النتيجةُ من `_ignition_outcome` **الإنتاجيّة** والصمودُ من
`operator_ok` **المخزَّن** — لا إعادةَ حسابٍ ولا مقياسٌ ثانٍ.
🔒 **قراءةٌ فقط:** لا كتابةَ حالةٍ ولا إرسالَ رسالةٍ ولا مسَّ فرزٍ.

رموزُ الخروج: `0` حكمٌ صدر · `2` تعذّرت القراءة · `3` سجلٌّ فارغ ·
`5` **الأرضيةُ لم تُبلَغ ⇒ «لا حكم»** (بنصّ §④).
"""
import json
import math
import os

import Super_stock as bot

ARM_MIN = None          # يُقرأ من CONFIG (رقمٌ مُعادٌ لا مخترَع — §③)


def wilson(k, n, z=1.96):
    """فاصلُ ثقةٍ 95% لنسبة — نفسُ آلة الدلالة في كلّ تجاربنا."""
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, 100 * (c - h)), min(100.0, 100 * (c + h)))


def main():
    floor = int(bot.CONFIG["IGNITION_OUTCOME_MIN"])
    path = os.environ.get("RADAR_LOG", "ignition_log.json")
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception as exc:                                     # noqa: BLE001
        print(f"⛔ تعذّر قراءة {path}: {type(exc).__name__} — لا حكم.")
        return 2
    log = raw if isinstance(raw, list) else (raw.get("fires")
                                            or raw.get("log") or [])
    log = [r for r in log if isinstance(r, dict)]
    if not log:
        print("⛔ السجلُّ فارغ — لا حكم.")
        return 3
    # ① المجتمع: `operator_ok` حاضرٌ (‏§②) — والغائبُ يُعلَن لا يُخمَّن
    pop = [r for r in log if r.get("operator_ok") is not None]
    print(f"⏱️ T-QUARTER · العقد: quarter_prereg.md")
    print(f"   السجلّ {len(log)} إطلاقًا · فيه `operator_ok`: {len(pop)} "
          f"· بلا الحقل (أقدمُ من وصله): {len(log) - len(pop)}")
    print(f"   العتبات: صمودٌ ‏≥{bot.CONFIG['OPERATOR_SUSTAIN_MIN']}د · تأكيدٌ "
          f"+{bot.CONFIG['IGNITION_CONFIRM_PCT']}% · أرضيةُ الذراع {floor}")
    arms = {True: [0, 0], False: [0, 0]}          # ok → [real, fake]
    pend = 0
    for f in pop:
        try:
            df = bot._ignition_outcome_fetch(f.get("symbol"), f.get("date"))
        except Exception:                                        # noqa: BLE001
            df = None
        oc = bot._ignition_outcome(f, df)
        if oc == "pending":
            pend += 1
            continue
        a = arms[bool(f.get("operator_ok"))]
        a[0 if oc == "real" else 1] += 1
    dec = sum(sum(v) for v in arms.values())
    print(f"\n📊 المقام: محسوم {dec} · معلّق {pend} (مُستبعَدٌ بنصّ §②)")
    rows = []
    for ok in (True, False):
        r, f_ = arms[ok]
        n = r + f_
        rate = 100 * r / n if n else 0.0
        lo, hi = wilson(r, n)
        rows.append((ok, r, f_, n, rate, lo, hi))
        nm = "صمد ‏≥15د" if ok else "سُحق فورًا"
        print(f"   {nm:12s} n={n:3d} · حقيقيّ {r} · كاذب {f_} "
              f"· نسبةُ الحقيقيّ {rate:5.1f}% · Wilson [{lo:.0f} · {hi:.0f}]")
    okr = next(x for x in rows if x[0] is True)
    nor = next(x for x in rows if x[0] is False)
    # ② البوّابةُ الثلاثية — بترتيب §④ حرفيًّا
    if okr[3] < floor or nor[3] < floor:
        print(f"\n⏳ **لا حكم** — ذراعٌ دون الأرضية {floor} "
              f"(صمد={okr[3]} · سُحق={nor[3]}). بنصّ §④ لا يُطبَع فرقٌ ولا يُعتمَد.")
        print("   ⇒ يتراكم تلقائيًّا مع كلّ جلسةٍ يعمل فيها الرادار.")
        return 5
    sep = okr[5] > nor[6] or nor[5] > okr[6]
    direction = okr[4] > nor[4]
    print(f"\n   فرقُ نسبةِ الحقيقيّ: {okr[4] - nor[4]:+.1f} نقطة")
    print(f"   ① العيّنة: ✅ · ② الفاصلان لا يتقاطعان: "
          f"{'✅' if sep else '🔴'} · ③ الاتّجاه للصمود: "
          f"{'✅' if direction else '🔴'}")
    if sep and direction:
        print("\n✅ **الثلاثةُ استُوفيت** ⇒ يُقترَح **سطرُ عرضٍ في تنبيه الرادار "
              "وحده** (سقفُ النجاح §⑤) — والقرارُ للمالك.")
    else:
        print("\n🔴 **لا يفصل** — العيّنةُ كافيةٌ والمعيارُ ساقط (بنصّ §④، وهو "
              "**غيرُ** «لا حكم»).")
    print("\n⚠️ حدودُ صدق (§⑦): «حقيقيّ» لمسُ ‏+12% لا تنفيذًا · والحقلُ مخزَّنٌ "
          "في جزءٍ من السجلّ ⇒ انحيازُ تاريخ · **ودائريّةٌ جزئية**: كلا المقياسَين "
          "من حركة السعر بعد الاشتعال ⇒ لا قرارَ كتمٍ عليه مهما كانت الأرقام.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
