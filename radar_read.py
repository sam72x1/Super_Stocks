#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔥📏 **اقرأ الرادار** — قياسُ نسبة الإنذار الكاذب من السجلّ الحيّ.

أمرُ المالك 2026-08-17 «اقرا الرادار». والمقياسُ **مسجَّلٌ سلفًا في تصميم
الرادار** لا مخترَعٌ الآن: `IGNITION_CONFIRM_PCT`=12 (حقيقيّ = بلغ ‏+12% من سعر
الاشتعال) · `IGNITION_OUTCOME_MIN`=8 (أرضيةُ العيّنة) — ثابتان منذ 2026-07-08
قبل أوّل إطلاق. ⇒ هذا **تنفيذُ قياسٍ مسجَّل** لا تجربةٌ جديدة.

🔒 **صفرُ منطقٍ جديد:** يُنادي `_ignition_log_block` **الإنتاجيّة** التي تُنادي
`_ignition_outcome` — مقياسٌ واحد لا اثنان. ولا يكتب حالةً ولا يُرسل رسالة ولا
يمسّ فرزًا؛ يقرأ `ignition_log.json` ويطبع.

⚠️ **وما لا يُدَّعى:** «حقيقيّ» = بلغ السعرُ ‏+12% **لمسًا** لا تنفيذًا · و«معلّق»
ليس نجاحًا ولا فشلًا · والعيّنةُ صغيرة فالفاصلُ عريض.
"""
import json
import math
import os
import sys

import Super_stock as bot


def wilson(k, n, z=1.96):
    """فاصلُ ثقةٍ 95% لنسبةٍ (نفسُ آلة الدلالة في كلّ تجاربنا)."""
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, 100 * (c - h)), min(100.0, 100 * (c + h)))


def main():
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
        print("⛔ السجلُّ فارغ — لا حكم (وليس «صفر إنذارٍ كاذب»).")
        return 3
    ds = sorted(r.get("date") or "" for r in log)
    print(f"🔥 السجلّ: {len(log)} إطلاقًا · المدى {ds[0]} ⟶ {ds[-1]}")
    print(f"   العتبات المسجَّلة: تأكيدٌ +{bot.CONFIG['IGNITION_CONFIRM_PCT']}% · "
          f"أرضيةُ العيّنة {bot.CONFIG['IGNITION_OUTCOME_MIN']} محسومة")
    # 🔒 المقياسُ الإنتاجيُّ نفسُه — لا نسخةَ ثانية.
    for ln in bot._ignition_log_block(log):
        print("  " + str(ln).replace("<b>", "").replace("</b>", ""))
    # تفصيلٌ صريحٌ بالمقام + فاصلُ Wilson (المُخرَجُ الإنتاجيّ لا يطبعه)
    real = fake = pend = 0
    by = {}
    for f in log:
        try:
            df = bot._ignition_outcome_fetch(f.get("symbol"), f.get("date"))
        except Exception:                                        # noqa: BLE001
            df = None
        oc = bot._ignition_outcome(f, df)
        if oc == "pending":
            pend += 1
            continue
        real += oc == "real"
        fake += oc == "fakeout"
        b = by.setdefault(f.get("candle_class") or "—", [0, 0])
        b[0 if oc == "real" else 1] += 1
    dec = real + fake
    print(f"\n📊 المقام: محسوم {dec} · معلّق {pend} من {len(log)}")
    if dec < int(bot.CONFIG["IGNITION_OUTCOME_MIN"]):
        print(f"⏳ **لا حكم** — المحسومُ {dec} دون الأرضية "
              f"{bot.CONFIG['IGNITION_OUTCOME_MIN']} (يتراكم).")
        return 5
    lo, hi = wilson(fake, dec)
    print(f"🔴 نسبةُ الإنذار الكاذب: {100 * fake / dec:.1f}% "
          f"({fake} من {dec}) · Wilson 95% [{lo:.0f}% · {hi:.0f}%]")
    print(f"✅ حقيقيّ: {real} · 🔴 كاذب: {fake}")
    print("\n🕯️ حسب تصنيف الشمعة (مضارب مقابل قروب):")
    for k, (r, f_) in sorted(by.items(), key=lambda x: -(x[1][0] + x[1][1])):
        n = r + f_
        l2, h2 = wilson(f_, n)
        print(f"   {k:10s} كاذب {100 * f_ / n:5.1f}% ({f_}/{n}) "
              f"· Wilson [{l2:.0f},{h2:.0f}]")
    print("\n⚠️ حدودُ صدق: «حقيقيّ» لمسُ ‏+12% لا تنفيذًا · و«معلّق» ليس حكمًا · "
          "والعيّنةُ صغيرةٌ فالفاصلُ عريض · ولا يُقارَن برقم الباكتيست إلّا بتحفّظ "
          "(مجتمعان مختلفان: هذا إطلاقاتٌ حيّةٌ وذاك كونُ باكتيست).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
