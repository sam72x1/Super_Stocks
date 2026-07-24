#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🪝 صيّاد أسهم التقسيم (منهج فيصل) — أداة **مستقلة تمامًا** عن فارز الارتكاز (14 بوابة).

الفكرة (طلب المستخدم 2026-07-24): فكرة/نمط مختلف عن البوت الأساسي — تمسح ناسداك
**يوميًّا بعد الإغلاق** عن مقسّم عكسي يطابق setup فيصل **الصارم**، وإذا لقت سهمًا يطابق
كل الشروط الأساسية ترسله لتلغرام مباشرة. **صامتة لو لا مطابق.**

الشروط الصارمة (كلها): مقسّم عكسي حديث + وصل قمة-ما-بعد-التقسيم÷2 + حافظ القاع 3
جلسات + فلوت<2مليون (ياهو) + خالٍ من رفعة قروب. السياق (عرض): المتاح<20ألف + الرسوم
(ChartExchange) + متوسطات 20/30/50 + تكرار التقسيم.

🔒 عرض/تنبيه فقط — لا تمسّ حالة البوت ولا الفرز ولا LOGIC_VERSION. لا تحفظ شيئًا.
التشغيل: python split_hunter.py (يلزم TELEGRAM_BOT_TOKEN/CHAT_ID · ياهو للفلوت)."""


def run():
    import Super_stock as S
    if S.yf is None:
        S.log("🪝 صيّاد المقسّم: yfinance غير متاح — تخطّي.")
        return 0
    try:
        uni = S.get_universe()
    except Exception as e:
        S.log(f"🪝 صيّاد المقسّم: تعذّر جلب كون ناسداك ({e}) — تخطّي (لا إرسال).")
        return 0
    if not uni:
        S.log("🪝 صيّاد المقسّم: كون ناسداك فارغ — تخطّي (لا إرسال).")
        return 0
    try:
        hist = S.download_history(uni)
    except Exception as e:
        S.log(f"🪝 صيّاد المقسّم: تحميل البيانات فشل ({e}) — تخطّي.")
        return 0
    if not hist:
        S.log("🪝 صيّاد المقسّم: لا بيانات — تخطّي.")
        return 0
    rows = S.scan_split_hunter(hist)
    S.log(f"🪝 صيّاد المقسّم: فحص {len(hist)} رمز → {len(rows)} مطابق كامل.")
    if rows:
        S.send_telegram(S.build_split_hunter_alert(rows) + "\n\n" + S.FOOTER)
        S.log("✅ أُرسل تنبيه صيّاد المقسّم لتلغرام.")
    else:
        S.log("🪝 صيّاد المقسّم: لا مطابق كامل اليوم — صمت (لا إرسال).")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
