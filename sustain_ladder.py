#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⏱️🪜 **T-SUSTAIN-LADDER** — هل **سلّمُ** الصمود يفصل أفضلَ من البولياني؟

عقدُه `sustain_ladder_prereg.md` **مدفوعٌ قبل أيّ رقم**. أداةٌ **مستقلّة** عن
`radar_quarter.py` و`radar_read.py` عمدًا فتبقى أرقامُهما بت-بت.

🔒 **صفرُ منطقٍ جديد:** النتيجةُ من `_ignition_outcome` **الإنتاجيّة** والصمودُ من
`sustain_min` **المخزَّن** — لا إعادةَ حسابٍ ولا مقياسٌ ثانٍ.
🔒 **قراءةٌ فقط:** لا كتابةَ حالةٍ ولا إرسالَ رسالةٍ ولا مسَّ فرزٍ ولا عتبة.

🔴 **والحكمُ مستحيلٌ اليوم بنيويًّا وأُعلن ذلك في العقد قبل التشغيل:** أربعُ درجاتٍ
× أرضية 8 = **‏32** محسومة، والمحسومُ **‏18** ⇒ المُخرَجُ الأوّلُ «لا حكم» **وهو
ليس نتيجة**. ويُطبَع **كم من العيّنة سبق التسجيل** فيُقرأ الحكمُ لاحقًا على ما
لم يُرَ.

رموزُ الخروج: `0` حكمٌ صدر · `2` تعذّرت القراءة · `3` سجلٌّ فارغ ·
`5` **الأرضيةُ لم تُبلَغ ⇒ «لا حكم»** (بنصّ §④).
"""
import json
import math
import os

import Super_stock as bot

# 🔒 الأذرعُ الأربعُ **مثبَّتةٌ في العقد ولا خامسة** — حدُّ 15 من نصّ فيصل
#    وقطوعُ الخمسِ من عندي (`engineering`)، ولا تُعاد تقطيعًا بعد الأرقام.
RUNGS = ((0, 5, "0-4د"), (5, 10, "5-9د"), (10, 15, "10-14د"),
         (15, None, "15د فأكثر"))
PREREG_DECIDED = 18       # ما سبق التسجيل — يُطبَع كي يُقرأ الحكمُ على ما بعده


def wilson(k, n, z=1.96):
    """فاصلُ ثقةٍ 95% لنسبة — نفسُ آلة الدلالة في كلّ تجاربنا."""
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, 100 * (c - h)), min(100.0, 100 * (c + h)))


def rung_of(mins):
    """الدرجةُ التي يقع فيها الصمود — أو `None` لغير الرقميّ (‏تعذّرٌ لا صفر)."""
    try:
        v = float(mins)
        if v != v:                                   # NaN ليس None
            return None
    except (TypeError, ValueError):
        return None
    for lo, hi, name in RUNGS:
        if v >= lo and (hi is None or v < hi):
            return name
    return None


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
    pop = [r for r in log if rung_of(r.get("sustain_min")) is not None]
    print("⏱️🪜 T-SUSTAIN-LADDER · العقد: sustain_ladder_prereg.md")
    print(f"   السجلّ {len(log)} إطلاقًا · فيه `sustain_min` رقميًّا: {len(pop)} "
          f"· بلا الحقل: {len(log) - len(pop)}")
    print(f"   العتبات: أرضيةُ الدرجة {floor} · تأكيدٌ "
          f"+{bot.CONFIG['IGNITION_CONFIRM_PCT']}% · حدُّ فيصل "
          f"{bot.CONFIG['OPERATOR_SUSTAIN_MIN']}د")
    arms = {name: [0, 0] for _lo, _hi, name in RUNGS}     # name → [real, fake]
    pend = nodata = 0
    for f in pop:
        try:
            df = bot._ignition_outcome_fetch(f.get("symbol"), f.get("date"))
        except Exception:                                        # noqa: BLE001
            df = None
        oc = bot._ignition_outcome(f, df)
        if oc == "pending":
            # 🔴 «pending» تُرجَع أيضًا عند `df is None` ⇒ يُفصَل «تعذّر الجلب»
            #    عن «لم يُحسَم» عدًّا (نفسُ إصلاح `radar_quarter.py`).
            try:
                blank = df is None or len(df) == 0
            except Exception:                                    # noqa: BLE001
                blank = True
            if blank:
                nodata += 1
            else:
                pend += 1
            continue
        arms[rung_of(f.get("sustain_min"))][0 if oc == "real" else 1] += 1
    dec = sum(sum(v) for v in arms.values())
    print(f"\n📊 المقام: محسوم {dec} · معلّق {pend} · تعذّر الجلب {nodata} "
          f"(الاثنان مُستبعَدان بنصّ §②)")
    print(f"   ⚖️ ومنها **ما سبق التسجيل ‏≈{PREREG_DECIDED}** ⇒ "
          f"تراكم بعده {max(0, dec - PREREG_DECIDED)} (‏§أعلى العقد).")
    rows = []
    for _lo, _hi, name in RUNGS:
        r, f_ = arms[name]
        n = r + f_
        rate = 100 * r / n if n else 0.0
        lo_, hi_ = wilson(r, n)
        rows.append((name, r, f_, n, rate, lo_, hi_))
        print(f"   {name:12s} n={n:3d} · حقيقيّ {r} · كاذب {f_} "
              f"· نسبةُ الحقيقيّ {rate:5.1f}% · Wilson [{lo_:.0f} · {hi_:.0f}]")
    thin = [x[0] for x in rows if x[3] < floor]
    if thin:
        print(f"\n⏳ **لا حكم** — درجاتٌ دون الأرضية {floor}: "
              + " · ".join(thin))
        print("   بنصّ §④ لا تُطبَع رتابةٌ ولا فصلٌ ولا يُعتمَد شيء.")
        print("   ⇒ يتراكم تلقائيًّا مع كلّ جلسةٍ يعمل فيها الرادار.")
        return 5
    mono = all(rows[i][4] <= rows[i + 1][4] + 1e-9 for i in range(len(rows) - 1))
    sep = rows[-1][5] > rows[0][6] or rows[0][5] > rows[-1][6]
    print(f"\n   ② الرتابةُ غيرُ المتناقصة: {'✅' if mono else '🔴'} · "
          f"③ العليا لا تتقاطع مع السفلى: {'✅' if sep else '🔴'}")
    if mono and sep:
        print("\n✅ **الثلاثةُ استُوفيت** ⇒ يُقترَح **سطرُ عرضٍ في تنبيه الرادار "
              "وحده** (سقفُ النجاح §⑤) — والقرارُ للمالك.")
    else:
        print("\n🔴 **لا يفصل** — العيّنةُ كافيةٌ والمعيارُ ساقط (بنصّ §④، وهو "
              "**غيرُ** «لا حكم»).")
    print("\n⚠️ حدودُ صدق (§⑦): **الفرضيةُ بعديّة** (اختيرت بعد رؤية البولياني) · "
          "و«حقيقيّ» لمسُ التأكيد لا تنفيذًا · وانحيازُ تاريخٍ مقيس · "
          "**ودائريّةٌ جزئية**: الصمودُ والنتيجةُ كلاهما من حركة السعر بعد "
          "الاشتعال ⇒ أيُّ رتابةٍ صاعدةٍ تُقرأ معها، ولا قرارَ كتمٍ عليها.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
