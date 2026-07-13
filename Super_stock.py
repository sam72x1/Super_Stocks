# -*- coding: utf-8 -*-
"""
==========================================================
بوت فرز أسهم الارتكاز (Pivot Low Screener) — النسخة 2.3

==========================================================

جديد v2.3 — التحليل متعدد الفريمات + أنماط الشموع الانعكاسية:
  • شرطان إلزاميان جديدان يرفعان الدقة (ويستبعدان الأسهم التي
    تبدو حلوة على اليومي فقط):
    - M6: انعكاس مؤكَّد على ≥ 2 من 3 فريمات (شهري/أسبوعي/يومي).
      (تُحسب الفريمات بإعادة تجميع اليومي — بلا أي تحميل إضافي.)
    - M7: ظهور نمط شمعة انعكاسي واحد على الأقل (يومي أو أسبوعي).
  • 8 أنماط انعكاس عند القاع تُكتشف رياضياً: مطرقة، مطرقة مقلوبة،
    ابتلاع صاعد، اختراق صاعد، نجمة الصباح، ثلاثة جنود بيض،
    دوجي عند الدعم، ماروبوزو أخضر.
  • تأكيد فريم 4 ساعات للمرشحين النهائيين فقط (معلومة/نقاط — لأن
    بيانات الإنتراداي محدودة، فهو غير إلزامي عمداً).
  • نقاط إضافية: +10 لتوافق الفريمات الثلاثة، +5 لنمط شمعة قوي.
  • زيادة التاريخ إلى ~2.2 سنة ليصبح الفريم الشهري سليماً.

جديد v2.2 — إضافة الأخبار لكل مرشح:
  • أخبار ياهو التلقائية (مجانية عبر yfinance): عناوين آخر 14 يوم
    تظهر داخل بطاقة السهم مع رابط كل خبر وتاريخه ومصدره.
  • روابط متابعة بضغطة واحدة: TipRanks + Yahoo + Finviz لكل سهم.
    (TipRanks/thefly مدفوع ومحمي ضد السحب الآلي، فنعطي رابطه
     المباشر بدل محاولة سحب غير موثوقة.)
  • فحص آلي لعناوين ياهو (scan_news_risk): يمسك الطرح/التخفيف/التقسيم
    العكسي/الشطب من نص الخبر → تحذير صريح في البطاقة (يخدم البوت تلقائياً).
  • ملاحظة: أخطار التخفيف المهمة (طرح أسهم/وحدات مثل خبر EHGO)
    يلتقطها مرصد SEC أيضاً كـ"🔴 نشرة طرح (تخفيف)" — أسرع وأوثق رسمياً.

جديد v2.1 — معايرة الفلاتر بعد مراجعة المنهجية (سبب "السهم الواحد"):
  خُفّفت الفلاتر التي كانت مشددة زيادة عن كلام فيصل، دون المساس
  بجوهر منهجيته. الإلزامي ما زال يفرض: فوق دولارين + هبوط عميق +
  انفجار سابق ≥100% + تجميع + عدم ملاحقة + سيولة + تأكيد فني.
  التغييرات (كلها في CONFIG، قابلة للرجوع برقم واحد):
    • وضع الفرز الافتراضي صار FULL بدل TEST (أمان: لا يفرز العينة
      الصغيرة بالغلط لو سقط متغير البيئة).
    • الهبوط المقبول: 50%-97% (كان 60%-92%) — يشمل أسهم فيصل
      شديدة الهبوط مثل "معيد الإجرام" (ELPW).
    • نافذة الانفجار السابق: <=20 جلسة (كانت <=10) — أكبر فلتر كان
      يخنق النتائج؛ يبقى شرط 100% كما حدده فيصل.
    • مدى التجميع: <=40% (كان 30%) — يناسب تذبذب الأسهم الصغيرة.
    • منع الملاحقة: <=35% خلال 5 جلسات (كان 25%).
    • حد السيولة: >=200 ألف$ (كان 300 ألف) — مع بقاء تحذير السيولة.
    • العائد/المخاطرة: >=1.0 (كان 1.5) — بوابة كانت من اجتهادي.
    • حد النقاط: >=40 (كان 50) — VOR كان يعدّي بالكاد عند 50.
  ملاحظة: البورصة بقيت ناسداك فقط (بطلب صريح). وأُضيف BCAB
  لقائمة مراقبة التقسيم العكسي (يطابق ملفه: تقسيم حديث + شورت<20ألف).

جديد v2.0 — نظام القائمة الأسبوعية الثابتة:
  • الجمعة 22:00 UTC (بعد إغلاق السوق = شمعة أسبوعية مكتملة اثنين→جمعة):
    فرز السوق كامل → أفضل 10 أسهم → تثبيتها في weekly_watchlist.json.
  • الثلاثاء→الجمعة صباحًا: لا تجديد — متابعة يومية + حساب جاهزية
    الدخول لكل سهم حسب التحليل الفني، وإرسال القائمة مرتبة بالجاهزية.
  • سهم يضرب الستوب → يُشطب بسببه، ويُستبدل في تشغيل اليوم
    التالي (القائمة دائماً ≤ 10).
  • الجمعة بعد الإغلاق: تقرير حصاد الأسبوع (الأداء + أسباب الشطب)
    ثم تجديد القائمة كاملة.
  • أول تشغيل بدون قائمة = تأسيس فوري (لا ينتظر يوم التجديد).
  • البورصة المعتمدة: ناسداك فقط.
  • عرض المخاطرة بالدولار الفعلي بدل نسبة 1:X الغامضة.
  • الشورت: Fintel محاولة أولى صامتة → FINRA أساسي → Yahoo
    احتياطي، مع التفريق بين "تعذّر الجلب" والرقم الفعلي.

يتضمن كل إصلاحات v1.1 (الـ14 مشكلة) كما هي:
  فلتر العائد/المخاطرة، إعلانات SEC الرسمية بالـCIK، منطق RSI
  المصحح، سقف الهبوط 97%، الجاهز أولاً، لا ثبات بصفر جلسات،
  تحذير الانفجارات الضخمة، تباعد الأهداف، سقف 2x، مسح السيولة
  الحقيقي، تحذير السيولة المنخفضة، تتبع الأداء والذاكرة الدائمة.

ملاحظات تشغيل:
  • لا حاجة لأي تعديل على ملف YML — البوت يعرف اليوم بنفسه.
  • لإجبار تجديد القائمة في أي يوم: أضف متغير بيئة FORCE_RENEW=1
    (اختياري، للطوارئ فقط).

هذا البوت *فارز فقط* — لا ينفّذ صفقات. القرار النهائي لك.
(معلومات ليست توصية)
"""

import os
import re
import sys
import json
import time
import math
import datetime as dt
import traceback

import numpy as np
import pandas as pd
import requests

# yfinance قد لا تكون مثبتة في بيئة الاختبار — نتعامل مع غيابها بلطف
try:
    import yfinance as yf
except Exception:
    yf = None

# ==========================================================
# 1) الإعدادات — كل أرقام المعايرة هنا (عدّل بحرية)
# ==========================================================
CONFIG = {
    # وضع التشغيل: TEST = عينة صغيرة سريعة | FULL = السوق كامل
    # (يمكن تجاوزه بمتغير بيئة SCREENER_MODE)
    # v2.1: الافتراضي FULL حتى لا يفرز العينة (28 سهم) بالغلط لو
    #       سقط متغير البيئة. للاختبار السريع: مرّر SCREENER_MODE=TEST
    "MODE": "FULL",

    # عينة الاختبار: الأسهم الموثقة من تحليلات فيصل
    "TEST_TICKERS": [
        "NXTT", "ADIL", "BIRD", "ELAB", "CDIO", "LFS", "VEEE", "AUUD",
        "EHGO", "FRGT", "PCLA", "EZRA", "CNMD", "RENX", "PRFX", "CLIK",
        "SMX", "NCT", "ELPW", "EDHL", "FRSX", "VMAR", "WORX", "WCT",
        "INHD", "ICU", "BNAI", "ENPH",
    ],

    # ---- الشروط الإلزامية (M) ----
    "MIN_PRICE": 1.5,            # M1: الحد الأدنى للسعر (v2.7: نُزّل من 2.0
                                 # إلى 1.5 — أسهم فيصل تنزل تحت دولارين بعد
                                 # التقسيم العكسي: ADIL/AUUD/EHGO/BNKK. الأفترهارز
                                 # ينزل لحظيًا تحت، والإغلاق اليومي غالبًا فوق 1.5)
    "MIN_DROP_PCT": 50.0,        # M2: هبوط مثالي ≥ 50% (تحته حتى الأرضية = نقص B)
    "MIN_DROP_FLOOR": 40.0,      # M2 أرضية صلبة: تحتها = ليس ارتكازًا (رفض) v2.7
    "MAX_DROP_PCT": 97.0,        # M2+: فوقه = سهم محتضر/فخ تقسيم (v2.1: كان 92)
    "PRIOR_SPIKE_PCT": 100.0,    # M3: انفجار مثالي ≥ 100% (تحته حتى الأرضية = نقص B)
    "PRIOR_SPIKE_FLOOR": 60.0,   # M3 أرضية صلبة: تحتها = ما انفجر كفاية (رفض) v2.7
    "PRIOR_SPIKE_WINDOW": 20,    # ...خلال ≤ 20 جلسة (v2.1: كان 10 — أكبر فلتر خانق)
    "BASE_WINDOW": 15,           # M4: نافذة التجميع (جلسات)
    "BASE_RANGE_MAX_PCT": 40.0,  # M4: مدى التجميع ≤ 40% (v2.1: كان 30)
    "RECENT_RISE_BLOCK_PCT": 35.0,  # M4: استبعاد من انفجر فعلاً (آخر 5 جلسات) (v2.1: كان 25)
    "MIN_DOLLAR_VOL": 200_000,   # M5: متوسط سيولة دولارية 20 يوم (v2.1: كان 300K)

    # ---- فلتر العائد/المخاطرة الإلزامي ----
    "MIN_RR_T1": 1.0,            # أقل عائد/مخاطرة مقبول للهدف الأول (v2.1: كان 1.5)
    "MIN_T1_GAIN_PCT": 8.0,      # الهدف الأول يبعد ≥ 8% عن السعر الحالي

    # ---- إشارات النقاط (S) ----
    "RSI_OVERSOLD": 27.0,        # فيصل: التشبع البيعي 23-27 (مستحيل ينفجر فوق هذا)
    "RSI_RECENT_WINDOW": 5,      # نافذة قاع RSI (للنقاط/الجاهزية)
    "RSI_OS_LOOKBACK": 25,       # نافذة فحص «وصل التشبع» (تطابق PIVOT_LOOKBACK)
    "RSI_OS_HARD": 32.0,         # أرضية صلبة: قاع RSI لازم ≤32 (تشبّع فعلاً) —
                                 # فوقها = ما حقّق نموذج الارتكاز → رفض. 27-32 = نقص.
    "RSI_MAX_NOW": 40.0,         # فيصل: "مستحيل يصعد إذا RSI بمناطق 40"
    "RSI_NOW_HARD": 50.0,        # سقف صلب: RSI الحالي >50 = فات الارتكاز (تحرّك
                                 # أصلاً) → رفض. 40-50 = طار قليلًا → نقص ناعم (B).
    # ---- بوابات فيصل الإلزامية (v2.6: مطابقة الشروط الستة بصرامة) ----
    "RSI_GATE_REQUIRED": True,   # M10: RSI لازم في التشبع (27) وتحت السقف (40)
    "MACD_GATE_REQUIRED": True,  # M11: تقاطع MACD إيجابي إلزامي
    "MA_GATE_REQUIRED": True,    # M12: السعر على المتوسط الأسي 30/50
    "MA_GATE_MAX_ABOVE_PCT": 15.0,  # أقصى ارتفاع فوق المتوسط الأسي (مرتكز لا طائر)
    "SHORT_GATE_REQUIRED": True, # M13: رفض الشورت العالي (ذكي: يعدّي لو مفقود)
    "SHORT_GATE_MAX": 40_000,    # حد "الشورت العالي" (≤20ألف مثالي · حتى 40ألف
                                 # مقبول: فيصل اختار SPPL بـ35ألف · فوقها = نقص B)
    "FLOAT_GATE_REQUIRED": True,  # M14: رفض الفلوت الكبير (أقوى رابط في أسهم فيصل)
    "FLOAT_GATE_MAX": 50_000_000, # حد الفلوت: كل أسهم فيصل تحته (HCAI 163ألف ←
                                  # MWC 26.68م). الفلوت الصغير = ينفجر بسهولة.
                                  # ذكي: يعدّي لو الفلوت مفقود (فائدة الشك).
    "VOL_SPIKE_MULT": 5.0,       # شمعة الفوليوم الضخمة ≥ 5x متوسط 20
    "VOL_DRY_RATIO": 0.6,        # جفاف: متوسط 5 < 60% من متوسط 20
    "PM_MOVE_PCT": 10,           # 🌙 عتبة تنبيه تحرّك البريماركت (POLYGON_EDGE_PLAN §ج،
                                 # عرضية موثّقة): تحرّك ≥10% بحجم بريماركت = «راقب الافتتاح»
    "PRESS_DROP_PCT": 15,        # 📉 عتبة «ضغط/تصريف المضارب» (طلب المستخدم — نمط LABT):
                                 # هبوط ≥15% (يومي عن الأمس · أو أفتر عن الإغلاق) = تصريف
    "IGNITION_VOL_MULT": 3.0,    # 🔥 رادار الانطلاق: قفزة حجم الدقيقة ≥3× متوسط الدقائق
                                 # السابقة = لحظة الاشتعال (رد فعل حي، `IGNITION_PLAN.md`)
    # 💰 عتبات «شمعة مضارب/قروب» بالدولار (FAISAL_OPERATOR_PACK_PLAN §P1، عرضية موثّقة
    # من كلام فيصل حرفيًّا): شمعة المضارب سيولتها ≥100 ألف (قوية ≥300 ألف) · القروب ≤50 ألف.
    "IGNITION_USD_OPERATOR": 100_000,
    "IGNITION_USD_STRONG": 300_000,
    "IGNITION_USD_GROUP": 50_000,
    # 📏 قياس حافة الرادار من السجلّ الحي (أداة التطوير — حلقة القياس، عرض/قياس فقط):
    "IGNITION_CONFIRM_PCT": 12.0,   # صعود ≥12% من سعر الاشتعال لاحقًا = اشتعال حقيقي
    "IGNITION_LOG_CAP": 500,        # حدّ سجلّ الإطلاقات (لا ينمو بلا حدّ)
    "IGNITION_OUTCOME_MIN": 8,      # أقل نتائج محسومة قبل عرض نسبة الإنذار الكاذب (صدق)
    # 🕵️ بوّابة المضارب على التنبيهات (طلب المستخدم: «لا إشعار إلا لو دخل المضارب» —
    # قاعدة فيصل: صفقة المضارب ≥1000 سهم؛ يشتري على الطلب، يفرّغ العروض لحظة الرفع):
    "OPERATOR_MIN_SHARES": 1000,    # أقل حجم طبعة تُعدّ «مضاربًا» (فيصل — عرضية موثّقة)
    # 🔒 معدّل الاقتراض (طلب المستخدم 2026-07-09 — فيصل يركّز عليه للارتكاز: فلوت صغير +
    # شورت منخفض + **اقتراض صعب** = وقود سكويز). عرض/سياق فقط — عتبة عرضية تُعاير لاحقًا:
    "BORROW_HIGH_PCT": 20.0,        # رسوم اقتراض ≥20% سنويًّا = صعب الاقتراض (وقود سكويز)
    "BORROW_MID_PCT": 5.0,          # 5-20% = متوسط (وقود جزئي) · أقل = سهل (لا وقود) —
                                    # حدود عرضية للتفسير فقط (لا بوابة/ترتيب)
    # 📅 الأحداث المعلنة القادمة (طلب المستخدم 2026-07-09 — «يوم الانفجار الذي ينتظره
    # المضارب»، فيصل 9428): أرباح + اكتمال تجارب سريرية. أبعد من هذا الأفق لا يُعرض
    "EVENTS_SHOW_DAYS": 45,
    "PROXY_LOOKBACK_DAYS": 75,      # 📅 نافذة التقاط دعوة اجتماع المساهمين (الاجتماع
                                    # يُعقد عادة بعد شهر-شهرين من الدعوة)
    "LOCKUP_DAYS": 180,             # 📅 حظر بيع المؤسسين الشائع بعد الإدراج (تقدير —
                                    # العقد قد يختلف؛ يُوسم «تقديري» بالعرض)
    # دول مشهورة بتجاهل التحليل الفني (تلاعب/pump&dump): تحذير فقط (تظل تظهر)
    "HIGH_RISK_COUNTRIES": ["China", "Hong Kong"],
    "SCORE_MIN": 45,             # الحد الأدنى لدخول الترشيح (v2.7: رُفع لـ45
                                 # لجودة أعلى — السهم لازم يجمع إشارات حقيقية)

    # ---- نظام القائمتين (v2.7): صارمة A + مراقبة B ----
    # قرار المستخدم: ما نطلع صفر أبدًا. القائمة A تجتاز كل البوابات،
    # والقائمة B "قريبة" تجتاز البنية الأساسية (سهم ارتكاز فعلي) لكن
    # ينقصها 1-2 من بوابات التأكيد (RSI/MACD/MA/شورت/فلوت/فجوة-فوق).
    "WATCHLIST_TWO_TIER": True,
    "WATCH_SOFT_GATES": ["M6", "M7", "M9", "M10", "M11", "M12", "M13", "M14"],
    # ملاحظة (تدقيق 2026-07-03): توثيقي فقط — غير مقروء في أي منطق؛ سلوك «النواقص
    # اللينة» مطبّق ضمنيًا بإلحاق soft_fails في كل بوابة، والنواقص الفعلية أوسع
    # (تشمل M2/M3 الحدّية وRR). تغييره هنا لا يغيّر الفرز. (نمط ATR_STOP_MULT.)
    "WATCH_MAX_FAILS": 3,        # الوسط: السهم باقي له 2-3 بوابات بالكثير
                                 # (مع SCORE_MIN=35 للجودة). أنزله لـ2 لأصرم
    # بوابات البنية الأساسية (إلزامية دائمًا — فشلها = ليس سهم ارتكاز):
    # M1 سعر · M2 هبوط · M3 انفجار · M4 قاعدة/طزاجة · M5 سيولة ·
    # M6 توافق فريمات · M7 نمط شمعة · M8 فجوة طازجة (لو مفعّلة).

    # ---- ستوب ATR ديناميكي (v2.7، قرار المستخدم) ----
    "USE_ATR_STOP": False,       # قاعدة فيصل: الوقف ~7% تحت القاع (ثابت)، لا ATR
                                 # (ATR كان يعمّق الوقف للأسهم المتذبذبة = خطأ)
    "ATR_STOP_MULT": 1.5,        # (غير مستخدم — USE_ATR_STOP=False)
    "ATR_PERIOD": 14,

    # ---- Fibonacci كأهداف (v2.7، قرار المستخدم) ----
    "USE_FIB_TARGETS": True,     # أضف مستويات فيب فوق السعر لمرشحي الأهداف

    # ---- MFI: كشف خلق السيولة الوهمية (v2.7، تغريدة فيصل 7379) ----
    "MFI_PERIOD": 14,
    "MFI_OVERSOLD": 25.0,        # تشبع بيعي بالـMFI (تأكيد مع RSI)
    "MFI_DIVERGENCE_SCORE": 10,  # نقاط: السعر يكسر قاعًا والـMFI لا يتبع (تباعد)

    # ---- نقاط المؤشرات الإضافية (v2.7) ----
    "SCORE_BOLLINGER_SQUEEZE": 5,  # انكماش حزمة كلنجر (تجميع قبل الانفجار)
    "SCORE_STOCHRSI": 5,           # StochRSI من التشبع وانعطاف صاعد
    "SCORE_DMI": 5,                # +DI يتجاوز -DI (بداية اتجاه صاعد)
    "SCORE_MA_SHORT": 5,           # السعر استعاد MA5/MA20 (إشارة تجميع)
    "SCORE_WILLIAMS": 5,           # Williams %R انعطاف من التشبع (فيصل + كلنجر، 7377)
    "WILLIAMS_OVERSOLD": -80.0,    # %R ≤ -80 = تشبع بيعي («بانتظار دخول المضارب»)
    "BOLL_SQUEEZE_PCTL": 0.25,     # عرض الحزمة ضمن أدنى 25% من آخر 60 جلسة

    # ---- القائمة الأسبوعية (v2.0) ----
    "WATCHLIST_SIZE": 10,        # حجم القائمة الثابتة (حد أقصى)
    # ---- قائمة مراقبة الارتداد المستقلة (v2.8): أسهم ارتكاز حقيقية ارتفعت
    # فوق دخولها؛ نتابعها يوميًا وننبّه أول ما تنزل لسعر الدعم (انهيار البورصة)
    "PULLBACK_WATCH": True,
    "PULLBACK_SIZE": 15,         # حجم قائمة مراقبة الارتداد (حد أقصى)
    "PULLBACK_TRIGGER_PCT": 2.0,  # تنبيه عند الوصول ضمن +2% فوق أعلى دفعة (بداية
                                  # منطقة الدفعات) — أبكر وأأمن من انتظار الدعم نفسه (D3)
    # v2.6 (فيصل): فرز السوق كاملاً كل يوم بعد الإغلاق بدل الجمعة فقط
    # (أسهم الشروط الصارمة نادرة جداً — نصطادها أي يوم تظهر)
    "DAILY_FULL_SCAN": True,
    "READY_PCT": 75,             # نسبة الجاهزية: 🟢 جاهز من هنا وفوق
    "NEAR_PCT": 50,              # 🟡 يقترب من هنا وفوق، وتحتها 🔴 إعداد فني ضعيف
    "EXCLUDE_STOPPED_FROM_RENEWAL": True,  # لا تُعِد سهماً ضرب ستوبه هذا الأسبوع

    # ---- قاعدة الثبات (التوقيت الذهبي: 3-5 جلسات بعد القاع) ----
    "PIVOT_LOOKBACK": 25,        # نبحث عن القاع في آخر 25 جلسة
    "STABILITY_MIN": 3,
    "STABILITY_MAX": 8,          # 5 + سماحية بسيطة
    "STABILITY_TOL_PCT": 2.0,    # القيعان بعد القاع ضمن 2% منه

    # ---- مستويات مقترحة ----
    "STOP_BELOW_LOW_PCT": (5.0, 7.0),    # الوقف 5-7% تحت القاع (فيصل: تحت
                                         # منطقة سحب السيولة، لا 1-2% الضيقة)
    # (D1، تدقيق 2026-07-03: حُذف ENTRY_ABOVE_PIVOT_PCT — كان ثابتًا ميتًا غير
    #  مقروء في أي منطق. «عدم الملاحقة» منفّذ فعليًا عبر: M4 يرفض صعود 5 جلسات
    #  أكثر من 35% (RECENT_RISE_BLOCK_PCT) + الدفعات مرساة على القاع + رفض الجاهزية<50%.)
    "ENTRY_ZONE_PCT": 4.0,               # (للتوافق القديم فقط — استُبدل بالدفعات)
    # ---- دفعات الدخول (أسلوب فيصل الموثّق @kisar_) ----
    # فيصل: "الدخول دفعات 1.80 · 1.75 · 1.70 · الوقف 1.50". أي 3 أوامر عند
    # الدعم وصعوداً بخطوة ثابتة؛ تتعبّى كلما نزل السعر للدعم. أدنى دفعة =
    # الدعم = أفضل تعبئة. (راجع FAISAL_METHODOLOGY_NOTES.md)
    "ENTRY_TRANCHES": 3,                  # عدد دفعات الدخول (فيصل: 3)
    "ENTRY_STEP_PCT": 3.0,               # الخطوة بين الدفعات (~5سنت على $1.8 ≈ 3%)
    "SWEEP_SMALL_PCT": (8.0, 10.0),      # عمق المسح: أسهم صغيرة
    "SWEEP_LARGE_PCT": (5.0, 7.0),       # عمق المسح: أسهم كبيرة (سعر ≥ 15)
    "LARGE_PRICE_CUT": 15.0,
    # 🔬 تجربة «الدخول المؤكَّد بالمسح» (T1، باكتيست حصريًا — كلها تتصفّر افتراضيًا =
    # صفر أثر على الإنتاج، لا LOGIC_VERSION). فيصل: «قبل يصعد لازم مسح سيولة تحت القاع
    # ثم استعادة · لا تدخل الدعم الأول». تُحقن عبر BT_SWEEP_* في وضع BACKTEST فقط.
    # ⚠️ الدخول والوقف **منفصلان** (مراجعة خصومية: خلطهما يعيد استيراد «الوقف الأعمق»
    # الفاشل حيًّا تحت لافتة الدخول) — BT_SWEEP_ENTRY يعزل أثر الدخول ووقفه = الأساس.
    "BT_SWEEP_ENTRY": 0,                  # 1 = دخول بعد مسح+استعادة (بدل التعبئة الفورية)
    "BT_SWEEP_STOP": 0,                   # 1 = وقف تحت ذيل المسح (0 = وقف الأساس، لعزل الدخول)
    "BT_SWEEP_PCT": 0.10,                # عمق المسح المطلوب تحت الدعم (مفتاح، لا قاعدة فيصل)
    "BT_SWEEP_STOP_MARGIN": 0.03,        # هامش الوقف تحت أدنى ذيل المسح (عند BT_SWEEP_STOP=1)
    "BT_SWEEP_MIN_RR": 1.0,              # أرضية العائد/المخاطرة لقبول تعبئة المسح
    "BT_SPREAD_PCT": 0.0,                # 🔬 F-COST: تكلفة تنفيذ (سبريد+انزلاق) — 0=سلوك
                                         # اليوم؛ نصفها يرفع الدخول ويخفض الخروج (حساسية 1/3/5%)
    "BT_POTENTIAL": 0,                   # 🏦 قوة البوت: قِس أقصى صعود من الدخول قبل الوقف
    "BT_PORTFOLIO": 0,                   # 🏦 محاكاة الانتقائية (أفضل N بالترتيب)
    "BT_PORT_SIZE": 15,                  # سعة المحفظة المحاكاة (= WATCHLIST_SIZE)
    "BT_RAW_PRICE": 0,                   # 🕰️ point-in-time: 1 = تحميل خام (auto_adjust=False)
                                         #   لتفادي إشارات وهمية من تعديل تقسيم مستقبلي (تدقيق
                                         #   خارجي). باكتيست حصريًا؛ الإنتاج يتجاهله (قفل B1).
    "BT_DUMP_DATASET": 0,                # 🔬 Phase C: 1 = اطبع صفوف المتغيّرات (raw_pit_entry/
                                         #   behav/score/readiness/mg…) للـstdout بمعلَم ثابت
                                         #   لسحبها من سجل Actions (المنافذ الخارجية محجوبة).
                                         #   باكتيست حصريًا · تشخيص/تصدير فقط · الإنتاج يتجاهله.
    "BT_DUMP_4H": 0,                     # 🔬 Phase E1: 1 = احسب سمات 4س نقطة-زمنية لكل إشارة
                                         #   (تغطية/انعكاس/RSI) وأضفها للتفريغ — لاختبار «هل 4س
                                         #   أدقّ من اليومية؟». يجلب 1h حيًّا (بطيء). باكتيست فقط.
    "RED_CANDLE_MIN_DROP": 15.0,         # شمعة الهبوط الكبيرة ≥ 15% للهدف الأول
    "RES_RED_HEAD_MIN_DROP": 3.0,        # رأس شمعة حمرا (هبوط ≥3%) = مقاومة/هدف
                                         #   (قاعدة فيصل: «رأس الحمرا مقاومة» — يومي)

    # ---- الفجوات السعرية (شرط فيصل السادس: "مع فجوات عالية") ----
    # v2.4 (نسخة B التجريبية): الفجوة بوابة إلزامية — فيصل: "أسهم الارتكاز
    # عدوها السيولة بسبب الفجوات الكبيرة". اختبار A/B: لو حسّنت النتائج نعتمدها.
    "GAP_REQUIRED": False,       # M8 (فجوة طازجة): نقاط فقط — المفهوم الصحيح
                                 # لفيصل هو الفجوة-فوق (M9)، فنطفّي هذي كبوابة
    "GAP_LOOKBACK": 20,          # نبحث عن الفجوات في آخر 20 جلسة
    "GAP_LOOKBACK_W": 26,        # نافذة فجوات الفريم الأسبوعي (~6 شهور)
    "GAP_LOOKBACK_M": 18,        # نافذة فجوات الفريم الشهري (~18 شهر)
    "GAP_MIN_PCT": 3.0,          # فجوة صاعدة معتبرة = افتتاح اليوم > إغلاق أمس بـ ≥3%
    "GAP_REQ_WINDOW": 20,        # البوابة: الفجوة المعتبرة لازم تكون خلال آخر N جلسة
    "GAP_BIG_PCT": 8.0,          # فجوة "عالية" حسب وصف فيصل (نقاط أعلى)
    "GAP_SCORE_NORMAL": 5,       # نقاط لوجود فجوة صاعدة معتبرة حديثة
    "GAP_SCORE_BIG": 10,         # نقاط لفجوة عالية ≥8% (بدل الـ5، لا تُجمع)
    "GAP_SCORE_MULTIFRAME": 5,   # نقاط إضافية لو الفجوات على أكثر من فريم
    # ---- الفجوة غير المملوءة فوق السعر (مفهوم فيصل: منطقة-هدف) v2.5 ----
    "GAP_ABOVE_REQUIRED": True,   # ★ بوابة: لازم فجوة غير مملوءة فوق السعر
    "GAP_ABOVE_LOOKBACK_D": 120,  # نافذة بحث الفجوات-فوق على اليومي (~6 شهور)
    "GAP_ABOVE_LOOKBACK_W": 52,   # على الأسبوعي (~سنة)
    "GAP_ABOVE_LOOKBACK_M": 24,   # على الشهري (~سنتين)
    "GAP_ABOVE_MAX_DIST_PCT": 60.0,  # تجاهل الفجوات الأبعد من 60% فوق (غير واقعية كهدف قريب)
    "GAP_ABOVE_SCORE": 10,        # نقاط لوجود فجوة-هدف فوق السعر
    "GAP_ABOVE_USE_AS_TARGET": True,  # استخدم الفجوة كهدف في T1/T2/T3

    # ---- الأهداف ----
    "TARGET_CAP_MULT": 2.0,      # سقف الأهداف: 2x السعر
    "MIN_TARGET_GAP_PCT": 3.0,   # أقل مسافة بين هدف وآخر = تسامح التجميع (3%)
                                 #   حتى لا يُتخطّى مستوى حقيقي قريب (قاعدة فيصل:
                                 #   الأهداف = سلّم المقاومات بالترتيب، بلا تجاوز)
    "USE_MULTIFRAME_TARGETS": True,  # فيصل: «الأهداف ع يومي + أسبوعي» — أضف
                                 # قمم ومنشأ الشمعة الحمرا الأسبوعية لمرشّحي الأهداف

    # ---- تحذيرات الجودة ----
    "SPIKE_VERIFY_PCT": 800.0,   # انفجار فوقه = تحذير "تحقق من تقسيم عكسي"
    "LOW_LIQ_WARN": 1_000_000,   # تحذير سيولة منخفضة تحت هذا الرقم

    # ---- إعلانات SEC ----
    "SEC_FILING_DAYS": 30,       # عرض إعلانات آخر 30 يوم فقط
    "SEC_MAX_SHOW": 4,           # أقصى عدد إعلانات في الرسالة لكل سهم

    # ---- الأخبار (v2.2) ----
    "NEWS_DAYS": 14,             # عرض عناوين أخبار آخر 14 يوم فقط
    "NEWS_MAX_SHOW": 3,          # أقصى عدد عناوين في الرسالة لكل سهم

    # ---- التحليل متعدد الفريمات + أنماط الشموع (v2.3) ----
    "TF_MIN_REVERSALS": 2,       # إلزامي: انعكاس على ≥ 2 من 3 فريمات
    "TF_BOTTOM_POS": 0.40,       # "عند القاع" = ضمن أدنى 40% من مدى الفريم
    "TF_RSI_OVERSOLD": 45.0,     # تشبع الفريم (أعلى قليلاً لأن الفريمات أبطأ)
    "TF_MONTHLY_LOOKBACK": 18,   # نافذة مدى الفريم الشهري
    "TF_WEEKLY_LOOKBACK": 52,    # نافذة مدى الفريم الأسبوعي
    "TF_DAILY_LOOKBACK": 60,     # نافذة مدى الفريم اليومي
    "CANDLE_SCAN_DAILY": 5,      # البحث عن نمط في آخر N شمعة يومية
    "CANDLE_SCAN_WEEKLY": 3,     # البحث عن نمط في آخر N شمعة أسبوعية
    "DOJI_BODY_MAX": 0.10,       # الدوجي: الجسم ≤ 10% من المدى
    "ENABLE_4H": True,           # تأكيد 4 ساعات للمرشحين النهائيين (نقاط/معلومة)

    # ---- استراتيجية التقسيم العكسي ----
    "SPLIT_LOOKBACK_DAYS": 120,
    "SHORT_DAILY_MAX": 20_000,   # "تابعه لين يبقى الشورت تحت 20 ألف"
    # قائمة يدوية إضافية (مثلاً من رسائل الغامدي): رموز تتابعها دائماً
    "SPLIT_WATCHLIST": ["WCT", "WORX", "EHGO", "FRSX", "BCAB"],

    # ---- تقنية ----
    "HISTORY_DAYS": 800,         # ~2.2 سنة (يكفي لفريم شهري سليم ~27 شمعة)
    "CHUNK_SIZE": 250,           # حجم دفعة التحميل
    "CHUNK_SLEEP": 2.0,          # ثوانٍ بين الدفعات (احترام Yahoo)
    "DOWNLOAD_RETRIES": 3,       # محاولات إعادة تحميل الدفعة عند الخنق/الفشل
    "RETRY_BACKOFF": 3.0,        # ثوانٍ أساس التراجع الأسّي (3,6,12...)
    "DATA_HEALTH_MIN_PCT": 85,   # تغطية بيانات أقل من هذا = تحذير صحة في الرسالة
    "MIN_BARS": 120,             # أقل عدد شموع مقبول للتحليل
    "REPORT_CSV": True,
    "MISSED_RISE_PCT": 30.0,     # مرفوض صعد ≥ هذا (آخر ~10 جلسات) = فرصة فائتة
    "SPLIT_SUSPECT_GAIN_PCT": 300.0,  # A2: كسب فوق هذا يُرجَّح أثر تقسيم عكسي غير
                                      # معدَّل بالبيانات (GDC «+11424%») — يُوسَم
                                      # ويُفصل من إحصاء الفائتة، لا يُحذف (شفافية)
    # ---- كاشف الانفجارات اليومية (للتعلّم) ----
    "EXPLOSION_PCT": 50.0,       # قفزة يوم واحد ≥ هذا = انفجار نحلّله (قرار المستخدم)
    "EXPLOSION_LOOKBACK": 5,     # نبحث عن يوم القفزة في آخر N جلسة
    # طلب المستخدم 2026-07-04: «لا سهم يرتفع >70% إلا وحنا عارفين بوابة رفضه» —
    # نضيف شبكة **تجمّع متعدّد الأيام** (قاع→قمة) تلتقط الصاعد التدريجي بلا يوم قفزة.
    "EXPLOSION_RUN_PCT": 70.0,   # ارتفاع تراكمي قاع→قمة ≥ هذا داخل النافذة = متحرّك
    "EXPLOSION_RUN_LOOKBACK": 20,  # نافذة البحث عن الركض التراكمي (جلسات)
    "EXPLOSION_KEEP_DAYS": 30,   # نحتفظ بسجل الانفجارات آخر N يوم للتقرير
    "EXPLOSION_KEEP_MAX": 600,   # سقف السجل (شبكة التجمّع تزيد الحجم — الارتكازات أولًا)
    # ---- حجم المركز + الباكتيست ----
    "ACCOUNT_SIZE": 10000.0,     # رأس المال لحساب حجم المركز (env: ACCOUNT_SIZE)
    "RISK_PER_TRADE_PCT": 1.0,   # نسبة المخاطرة من رأس المال لكل صفقة
    "BACKTEST_FORWARD_DAYS": 40, # أفق الباكتيست للأمام (جلسات) لقياس الهدف/الوقف
    "BACKTEST_STEP": 5,          # خطوة المشي للأمام (جلسات) لتقليل التداخل
    "ALERTS_KEEP_DAYS": 180,     # نقلّم سجل التنبيهات المغلقة الأقدم من هذا (نمو محدود)
}

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
MODE = os.environ.get("SCREENER_MODE", CONFIG["MODE"]).strip().upper()
try:                                  # رأس المال من البيئة (اختياري)
    if os.environ.get("ACCOUNT_SIZE"):
        CONFIG["ACCOUNT_SIZE"] = float(os.environ["ACCOUNT_SIZE"])
except Exception:
    pass


def _apply_backtest_overrides(mode: str, env=None) -> list:
    """B1 (خطة الضبط 2026-07-03): تجاوز عتبات محدّدة عبر env — **في وضع BACKTEST
    حصريًا** (تجربة A/B لبوابتي M4/M2). الإنتاج محصّن تمامًا: أي وضع آخر يتجاهل
    المفاتيح (مقفول باختبار). يرجع قائمة ما طُبِّق للتوثيق برسالة الباكتيست."""
    applied = []
    if str(mode).strip().upper() != "BACKTEST":
        return applied
    env = env if env is not None else os.environ
    # (توسعة 2026-07-03 بعد تشخيص أسهم فيصل: السقف 97 والنافذة 20 والسيولة 200K
    #  أرقام هندسية غير موثّقة من فيصل وتخنق أسهمه — صارت قابلة للتجربة أيضًا.)
    for bt_env, cfg_key, cast in (
            ("BT_BASE_RANGE_MAX", "BASE_RANGE_MAX_PCT", float),
            ("BT_MIN_DROP_FLOOR", "MIN_DROP_FLOOR", float),
            ("BT_MAX_DROP_PCT", "MAX_DROP_PCT", float),
            ("BT_SPIKE_WINDOW", "PRIOR_SPIKE_WINDOW", int),
            ("BT_MIN_DOLLAR_VOL", "MIN_DOLLAR_VOL", float),
            # 🔬 تجربة الدخول المؤكَّد بالمسح (T1) — باكتيست حصريًا، منفصلة الدخول/الوقف
            ("BT_SWEEP_ENTRY", "BT_SWEEP_ENTRY", int),
            ("BT_SWEEP_STOP", "BT_SWEEP_STOP", int),
            ("BT_SWEEP_PCT", "BT_SWEEP_PCT", float),
            ("BT_SWEEP_STOP_MARGIN", "BT_SWEEP_STOP_MARGIN", float),
            ("BT_SWEEP_MIN_RR", "BT_SWEEP_MIN_RR", float),
            ("BT_SPREAD_PCT", "BT_SPREAD_PCT", float),    # 🔬 F-COST
            ("BT_POTENTIAL", "BT_POTENTIAL", int),        # 🏦 قوة البوت
            ("BT_PORTFOLIO", "BT_PORTFOLIO", int),
            ("BT_PORT_SIZE", "BT_PORT_SIZE", int),
            ("BT_RAW_PRICE", "BT_RAW_PRICE", int),         # 🕰️ point-in-time
            ("BT_DUMP_DATASET", "BT_DUMP_DATASET", int),    # 🔬 Phase C dump
            ("BT_DUMP_4H", "BT_DUMP_4H", int)):             # 🔬 Phase E1 4h features
        v = (env.get(bt_env) or "").strip()
        if not v:
            continue
        try:
            CONFIG[cfg_key] = cast(float(v))
            applied.append(f"{cfg_key}={CONFIG[cfg_key]:g}")
        except ValueError:
            pass
    return applied


_BT_OVERRIDES = _apply_backtest_overrides(MODE)

# نسخة منطق التحليل — تُختم في ملف القائمة. أي تعديل يمسّ الدخول/الوقف/الأهداف/
# المستويات → ارفع الرقم، فالبوت يعيد حساب القائمة كاملة تلقائياً في أول تشغيل
# (ضمان: القائمة دائمًا على آخر منطق، بلا انتظار يوم التجديد ولا تدخّل يدوي).
LOGIC_VERSION = "2026.06.22-redheads.dw+noskip+tranches+4h+keylevels+avgRR"

UA = {"User-Agent": "Mozilla/5.0 (pivot-screener; personal research)"}
# SEC تتطلب User-Agent فيه وسيلة تواصل حقيقية — يُضبط بسرّ SEC_CONTACT في الـ
# workflows (14ج: الوهمي contact@example.com قد يُبطأ/يُحجب بسياسة الوصول العادل).
# `or` لا الوسيط الثاني: السرّ غير المضبوط يصل بيئةً فارغةً "" ويجب ألا يُعتمد.
SEC_UA = {"User-Agent": (os.environ.get("SEC_CONTACT") or
                         "PivotScreener/2.0 (personal research; contact@example.com)")}
# متصفح عادي لـ fintel (محاولة أولى صامتة — قد يحجب الطلبات الآلية)
BROWSER_UA = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
}


def log(msg):
    print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ==========================================================
# 2) المؤشرات الفنية (مكتوبة يدوياً = صفر اعتماد على مكتبات هشة)
# ==========================================================
def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out = 100.0 - (100.0 / (1.0 + rs))
    return out.fillna(50.0)


def ema(close: pd.Series, span: int) -> float:
    """المتوسط المتحرك الأسي (EMA) — فيصل يستخدم "المتوسط الأسي" 30/50،
    لا المتوسط البسيط. يعطي وزناً أكبر للشموع الأحدث."""
    if close is None or len(close) < 1:
        return 0.0
    return float(close.ewm(span=span, adjust=False).mean().iloc[-1])


def macd(close: pd.Series, fast=12, slow=26, signal=9):
    ema_f = close.ewm(span=fast, adjust=False).mean()
    ema_s = close.ewm(span=slow, adjust=False).mean()
    line = ema_f - ema_s
    sig = line.ewm(span=signal, adjust=False).mean()
    return line, sig


def kst(close: pd.Series):
    """KST بإعدادات فيصل (10,15,20,30,10,10,10,15,9)"""
    def roc(n):
        return close.pct_change(n) * 100.0
    k = (roc(10).rolling(10).mean() * 1
         + roc(15).rolling(10).mean() * 2
         + roc(20).rolling(10).mean() * 3
         + roc(30).rolling(15).mean() * 4)
    return k, k.rolling(9).mean()


def momentum_kst_state(close: pd.Series):
    """🎬 حالة KST بإعدادات فيصل — أربع حالات كما يفرّقها بفيديو DSY (KST −309 فوق
    KSTMA −320 وكلاهما سالب = «تحسّن مبكر تحت الصفر»). فيصل يقرأه على 4س. عرض/سياق
    فقط — لا بوابة ولا نقاط (المؤشر مساند لا أساس؛ درس §0-ز). None لو البيانات قصيرة."""
    try:
        k, s = kst(close)
        kv, sv = float(k.iloc[-1]), float(s.iloc[-1])
        if kv != kv or sv != sv:                  # NaN (بيانات غير كافية)
            return None
        above, neg = kv > sv, (kv < 0 and sv < 0)
        if above and neg:
            return "فوق إشارته وكلاهما تحت الصفر — تحسّن مبكر (لا انعكاس مؤكَّد)"
        if above:
            return "فوق إشارته فوق الصفر — زخم صاعد"
        if neg:
            return "تحت إشارته تحت الصفر — زخم هابط"
        return "تحت إشارته فوق الصفر — تراجع زخم"
    except Exception:
        return None


def mfi(high, low, close, volume, period: int = 14) -> pd.Series:
    tp = (high + low + close) / 3.0
    raw = tp * volume
    pos = raw.where(tp > tp.shift(1), 0.0)
    neg = raw.where(tp < tp.shift(1), 0.0)
    pr = pos.rolling(period).sum()
    nr = neg.rolling(period).sum().replace(0, np.nan)
    out = 100.0 - 100.0 / (1.0 + pr / nr)
    return out.fillna(50.0)


def williams_r(high, low, close, period: int = 14) -> pd.Series:
    hh = high.rolling(period).max()
    ll = low.rolling(period).min()
    rng = (hh - ll).replace(0, np.nan)
    return (-100.0 * (hh - close) / rng).fillna(-50.0)


# ==========================================================
# 2أ) مؤشرات فيصل الإضافية (v2.7): صفحة إعداداته الكاملة
#   Bollinger 20/2 · StochRSI 14/14/3/3 · DMI 14 · ATR 14 · Williams %R 14 ·
#   Fibonacci 0.236-0.786 · VWAP · DMA(10,50,10).
#   كلها مكتوبة يدوياً = صفر اعتماد على مكتبات هشة (نفس نهج الملف).
# ==========================================================
def atr(high, low, close, period: int = 14) -> pd.Series:
    """المدى الحقيقي المتوسط (ATR 14) — لقياس التذبذب وحساب ستوب ديناميكي."""
    pc = close.shift(1)
    tr = pd.concat([(high - low),
                    (high - pc).abs(),
                    (low - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()


def bollinger(close: pd.Series, period: int = 20, mult: float = 2.0):
    """مؤشر كلنجر (Bollinger 20/2) — يرجع (وسط، علوي، سفلي، %B، عرض الحزمة).
    فيصل: ينتظر انكماش الحزمة (تجميع) قبل الانفجار."""
    mid = close.rolling(period).mean()
    sd = close.rolling(period).std(ddof=0)
    upper = mid + mult * sd
    lower = mid - mult * sd
    width = (upper - lower) / mid.replace(0, np.nan)         # عرض نسبي
    pctb = (close - lower) / (upper - lower).replace(0, np.nan)
    return mid, upper, lower, pctb, width


def stoch_rsi(close: pd.Series, period: int = 14, k: int = 3, d: int = 3):
    """Stochastic RSI (14/14/3/3) — يرجع (%K، %D) بين 0-100."""
    r = rsi(close, period)
    lo = r.rolling(period).min()
    hi = r.rolling(period).max()
    st = (r - lo) / (hi - lo).replace(0, np.nan) * 100.0
    kline = st.rolling(k).mean()
    dline = kline.rolling(d).mean()
    return kline.fillna(50.0), dline.fillna(50.0)


def dmi_adx(high, low, close, period: int = 14):
    """DMI/ADX (14) — يرجع (+DI، -DI، ADX). +DI>-DI = اتجاه صاعد."""
    up = high.diff()
    dn = -low.diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    pc = close.shift(1)
    tr = pd.concat([(high - low), (high - pc).abs(),
                    (low - pc).abs()], axis=1).max(axis=1)
    atr_ = tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    pdi = 100.0 * pd.Series(plus_dm, index=high.index).ewm(
        alpha=1.0 / period, min_periods=period, adjust=False).mean() \
        / atr_.replace(0, np.nan)
    mdi = 100.0 * pd.Series(minus_dm, index=high.index).ewm(
        alpha=1.0 / period, min_periods=period, adjust=False).mean() \
        / atr_.replace(0, np.nan)
    dx = 100.0 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    adx = dx.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    return pdi.fillna(0.0), mdi.fillna(0.0), adx.fillna(0.0)


def rolling_vwap(df: pd.DataFrame, period: int = 20) -> float:
    """VWAP تقريبي على آخر period جلسة (السعر المرجّح بالحجم).
    فيصل يستخدمه كخط مرجعي (CDIO VWAP 1.246)."""
    tail = df.tail(period)
    tp = (tail["High"] + tail["Low"] + tail["Close"]) / 3.0
    vol = tail["Volume"]
    denom = float(vol.sum())
    if denom <= 0:
        return float(tail["Close"].iloc[-1])
    return float((tp * vol).sum() / denom)


def dma_oscillator(close: pd.Series, short: int = 10, long: int = 50,
                   disp: int = 10):
    """DMA(10,50,10) المزاحة كما في شارتات فيصل (RAYA/CDIO): الفرق بين
    متوسطين بسيطين مزاحين للأمام. يرجع (DDD، AMA) ≈ القيمتين المعروضتين."""
    ma_s = close.rolling(short).mean().shift(disp)
    ma_l = close.rolling(long).mean().shift(disp)
    ddd = ma_s - ma_l                     # الفرق (الخط الأزرق DDD)
    ama = ddd.rolling(short).mean()       # تنعيمه (البرتقالي AMA)
    return ddd, ama


def fibonacci_levels(swing_low: float, swing_high: float) -> dict:
    """مستويات فيبوناتشي الارتدادية/الامتدادية (فيصل IMG_6473): تُستخدم
    كأهداف/مناطق. من القاع للقمة: 0.236/0.382/0.5/0.618/0.786 ارتداد،
    و1.272/1.618 امتداد فوق القمة."""
    if swing_high <= swing_low or swing_low <= 0:
        return {}
    rng = swing_high - swing_low
    out = {}
    for r in (0.236, 0.382, 0.5, 0.618, 0.786):
        out[f"{r:.3f}"] = round(swing_low + rng * r, 3)
    out["1.000"] = round(swing_high, 3)
    out["1.272"] = round(swing_high + rng * 0.272, 3)
    out["1.618"] = round(swing_high + rng * 0.618, 3)
    return out


# ==========================================================
# 2ب) أنماط الشموع الانعكاسية + التحليل متعدد الفريمات (v2.3)
# ==========================================================
# الأنماط القوية (تعطي نقاطاً إضافية مقارنة بالمطرقة/الدوجي)
STRONG_PATTERNS = {"ابتلاع صاعد", "نجمة الصباح", "ثلاثة جنود بيض",
                   "ماروبوزو أخضر", "اختراق صاعد"}


def resample_ohlc(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    """تجميع الشموع إلى فريم أكبر (أسبوعي/شهري/4س) — بلا تحميل إضافي.
    يدعم اختلاف رموز pandas بين الإصدارات (W / ME-M / 4h-4H)."""
    agg = {"Open": "first", "High": "max", "Low": "min",
           "Close": "last", "Volume": "sum"}
    candidates = [rule]
    if rule == "ME":
        candidates.append("M")
    elif rule == "M":
        candidates.append("ME")
    elif rule and rule[-1] in "hH":          # 4h / 4H
        candidates = [rule[:-1] + "h", rule[:-1] + "H"]
    for r in candidates:
        try:
            out = df.resample(r).agg(agg)
            return out.dropna(subset=["Close"])
        except (ValueError, KeyError):
            continue
    raise ValueError(f"تعذّر إعادة التجميع بالقاعدة: {rule}")


def _candle(o, h, l, c, i):
    """خصائص الشمعة i: (الجسم، المدى، الظل العلوي، الظل السفلي، أخضر؟)"""
    body = abs(c[i] - o[i])
    rng = h[i] - l[i]
    up = h[i] - max(o[i], c[i])
    dn = min(o[i], c[i]) - l[i]
    return body, rng, up, dn, (c[i] > o[i])


def _patterns_at(o, h, l, c, i, support):
    """أنماط الانعكاس الصاعد المكتشفة عند الشمعة i (قائمة أسماء عربية)."""
    found = []
    body, rng, up, dn, green = _candle(o, h, l, c, i)
    if rng <= 0:
        return found
    small_up = up <= max(body * 0.5, 0.10 * rng)
    small_dn = dn <= max(body * 0.5, 0.10 * rng)
    # مطرقة: جسم صغير أعلى المدى + ظل سفلي طويل (≥2× الجسم)
    if body <= 0.40 * rng and dn >= 2.0 * body and small_up:
        found.append("مطرقة")
    # مطرقة مقلوبة: جسم صغير أسفل المدى + ظل علوي طويل
    if body <= 0.40 * rng and up >= 2.0 * body and small_dn:
        found.append("مطرقة مقلوبة")
    # دوجي عند الدعم: جسم ضئيل جداً + قاعها قرب الدعم الحديث
    if body <= CONFIG["DOJI_BODY_MAX"] * rng and support > 0 \
            and l[i] <= support * 1.03:
        found.append("دوجي عند الدعم")
    # ماروبوزو أخضر: جسم ≥90% من المدى، أخضر، شمعة حقيقية
    if green and body >= 0.90 * rng and rng >= 0.02 * max(c[i], 1e-9):
        found.append("ماروبوزو أخضر")
    # أنماط شمعتين
    if i >= 1:
        pb = abs(c[i - 1] - o[i - 1])
        prev_red = c[i - 1] < o[i - 1]
        if prev_red and green and o[i] <= c[i - 1] and c[i] >= o[i - 1] \
                and body > pb:
            found.append("ابتلاع صاعد")
        if prev_red and green and o[i] < c[i - 1] \
                and c[i] > (o[i - 1] + c[i - 1]) / 2.0 and c[i] < o[i - 1]:
            found.append("اختراق صاعد")
    # أنماط ثلاث شمعات
    if i >= 2:
        b0 = abs(c[i - 2] - o[i - 2]); r0 = h[i - 2] - l[i - 2]
        g0 = c[i - 2] > o[i - 2]
        b1 = abs(c[i - 1] - o[i - 1]); g1 = c[i - 1] > o[i - 1]
        # نجمة الصباح: أحمر كبير + جسم صغير + أخضر يغلق فوق منتصف الأول
        if (not g0) and r0 > 0 and b0 >= 0.40 * r0 and b1 <= 0.50 * b0 \
                and green and c[i] > (o[i - 2] + c[i - 2]) / 2.0 \
                and max(o[i - 1], c[i - 1]) <= c[i - 2] * 1.01:
            found.append("نجمة الصباح")
        # ثلاثة جنود بيض: ثلاث خضر صاعدة، كل واحدة تفتح داخل جسم سابقتها
        if g0 and g1 and green and c[i] > c[i - 1] > c[i - 2] \
                and o[i - 2] <= o[i - 1] <= c[i - 2] \
                and o[i - 1] <= o[i] <= c[i - 1] \
                and body >= 0.50 * rng and up <= body:
            found.append("ثلاثة جنود بيض")
    return found


def detect_candle_patterns(df: pd.DataFrame, scan_last: int) -> list:
    """يبحث عن أنماط الانعكاس في آخر scan_last شمعة — يرجع قائمة فريدة."""
    o = df["Open"].values.astype(float)
    h = df["High"].values.astype(float)
    l = df["Low"].values.astype(float)
    c = df["Close"].values.astype(float)
    n = len(c)
    if n < 3:
        return []
    support = float(np.min(l[-min(30, n):]))   # أدنى قاع حديث = الدعم
    found = []
    for i in range(max(2, n - scan_last), n):
        for p in _patterns_at(o, h, l, c, i, support):
            if p not in found:
                found.append(p)
    return found


def timeframe_reversal(tf_df: pd.DataFrame, lookback: int,
                       min_bars: int) -> bool:
    """هل يُظهر الفريم انعكاساً صاعداً عند القاع؟
    شرط: السعر ضمن أدنى TF_BOTTOM_POS من مداه + ≥2 إشارات صعود
    (RSI ينحني من تشبع / MACD إيجابي / آخر إغلاق صاعد)."""
    if tf_df is None or len(tf_df) < min_bars:
        return False
    close = tf_df["Close"]
    price = float(close.iloc[-1])
    seg = close.tail(lookback)
    lo, hi = float(seg.min()), float(seg.max())
    if hi <= lo:
        return False
    if (price - lo) / (hi - lo) > CONFIG["TF_BOTTOM_POS"]:
        return False                       # ليس عند القاع → ليس انعكاس قاع
    rs = rsi(close)
    rsi_up = (float(rs.iloc[-1]) > float(rs.iloc[-2])
              and float(rs.tail(4).min()) <= CONFIG["TF_RSI_OVERSOLD"])
    ml, msig = macd(close)
    macd_up = float(ml.iloc[-1]) >= float(msig.iloc[-1])
    last_up = float(close.iloc[-1]) > float(close.iloc[-3])  # صعود فعلي
    return (int(rsi_up) + int(macd_up) + int(last_up)) >= 2


def multi_timeframe(df: pd.DataFrame) -> dict:
    """تحليل شهري/أسبوعي/يومي من البيانات اليومية (إعادة تجميع، بلا تحميل).
    يرجع: عدد الفريمات المنعكسة + حالة كل فريم + أنماط الشموع + نص العرض."""
    weekly = resample_ohlc(df, "W")
    monthly = resample_ohlc(df, "ME")
    d = timeframe_reversal(df, CONFIG["TF_DAILY_LOOKBACK"], 30)
    w = timeframe_reversal(weekly, CONFIG["TF_WEEKLY_LOOKBACK"], 20)
    m = timeframe_reversal(monthly, CONFIG["TF_MONTHLY_LOOKBACK"], 12)
    pats = detect_candle_patterns(df, CONFIG["CANDLE_SCAN_DAILY"])
    for p in detect_candle_patterns(weekly, CONFIG["CANDLE_SCAN_WEEKLY"]):
        if p not in pats:
            pats.append(p)

    def mark(x):
        return "✅" if x else "⏳"
    disp = f"شهري {mark(m)} · أسبوعي {mark(w)} · يومي {mark(d)}"
    return {"count": int(d) + int(w) + int(m), "daily": d, "weekly": w,
            "monthly": m, "patterns": pats, "display": disp}


def fetch_4h(sym: str):
    """يحمّل فريم 4 ساعات (يشمل التداول خارج السوق prepost — لرصد ذيل المسح
    الحقيقي مثل ما يوضّح فيصل). يرجع DataFrame مجمّعة 4س أو None."""
    if yf is None or not CONFIG.get("ENABLE_4H", True):
        return None
    try:
        h1 = yf.download(sym, period="60d", interval="1h", auto_adjust=True,
                         prepost=True, progress=False)
        if h1 is None or h1.empty:
            return None
        if isinstance(h1.columns, pd.MultiIndex):
            h1.columns = h1.columns.get_level_values(0)
        h1 = h1.dropna(subset=["Close"])
        h4 = resample_ohlc(h1, "4h")
        return h4 if len(h4) >= 20 else None
    except Exception:
        return None


def fetch_4h_signal(sym: str):
    """تأكيد انعكاس فريم 4 ساعات. يرجع (إشارة bool/None، وصف)."""
    if yf is None or not CONFIG.get("ENABLE_4H", True):
        return None, "غير مفعّل"
    h4 = fetch_4h(sym)
    if h4 is None:
        return None, "غير متوفر"
    ok = timeframe_reversal(h4, 60, 20)
    return ok, ("✅ مؤكِّد" if ok else "⏳ غير مؤكِّد بعد")


def _fetch_1h_window(sym: str, asof, days: int = 120):
    """🔬 Phase E1 (بحث/باكتيست فقط): يحمّل شموع الساعة في نافذة [asof-days, asof] لبناء 4س
    نقطة-زمنية (point-in-time) عند إشارة تاريخية — end=asof فلا تسريب مستقبلي. yfinance يتيح 1h
    حتى ~730 يومًا للخلف فقط، فالتغطية التاريخية للمايكروكاب مجهولة (نقيسها). فاشل-آمن → None."""
    if yf is None:
        return None
    try:
        a = pd.Timestamp(asof)
        end = (a + pd.Timedelta(days=1)).date().isoformat()
        start = (a - pd.Timedelta(days=days)).date().isoformat()
        h1 = yf.download(sym, start=start, end=end, interval="1h", auto_adjust=True,
                         prepost=True, progress=False)
        if h1 is None or h1.empty:
            return None
        if isinstance(h1.columns, pd.MultiIndex):
            h1.columns = h1.columns.get_level_values(0)
        return h1.dropna(subset=["Close"])
    except Exception:
        return None


def h4_features_at(sym: str, asof, fetch=None):
    """🔬 Phase E1: يستخرج سمات 4س نقطة-زمنية عند إشارة تاريخية (بلا تسريب) لاختبار
    «هل شمعة 4س أدقّ من اليومية في تمييز المنفجر؟». يعيد dict أو None (تعذّر جلب). المفتاح
    الأول = التغطية (h4_bars): كم شمعة 4س توفّرت تاريخيًّا. بحث/باكتيست فقط · فاشل-آمن.
    `fetch` قابل للحقن للاختبار (يعيد إطار شموع ساعة أو None)."""
    fetch = fetch if fetch is not None else _fetch_1h_window
    h1 = fetch(sym, asof)
    if h1 is None or len(h1) < 8:
        return None
    try:
        h4 = resample_ohlc(h1, "4h")
    except Exception:
        return None
    # 🔬 P0-5 (تدقيق Codex): provenance يكفي لإعادة إنتاج السمة بت-بت — نافذة/tz/حدود البارات/
    # قاعدة إعادة التجميع/المصدر (كله مشتقّ من البيانات الفعلية المجلوبة، لا وقت جدار). كان
    # الموجود (h4_status/bars/reversal/rsi) يكفي للتغطية لا لإعادة الإنتاج (الثغرة التي رصدها Codex).
    prov = {
        "h4_asof": str(pd.Timestamp(asof).date()),
        "h4_source": "yfinance 1h->4h (interval=1h, prepost=True, auto_adjust=True)",
        "h4_resample": "4h",
        "h4_timezone": str(getattr(h1.index, "tz", None)),
        "h4_1h_bars": int(len(h1)),
        "h4_1h_first": str(h1.index[0]),
        "h4_1h_last": str(h1.index[-1]),
    }
    if h4 is not None and len(h4):
        prov["h4_first_bar"] = str(h4.index[0])
        prov["h4_last_bar"] = str(h4.index[-1])
    if h4 is None or len(h4) < 10:
        return {"h4_bars": (0 if h4 is None else int(len(h4))),
                "h4_reversal": None, "h4_rsi": None, **prov}
    try:
        rev = bool(timeframe_reversal(h4, 60, 20))
    except Exception:
        rev = None
    try:
        _r = rsi(h4["Close"])
        h4r = round(float(_r.iloc[-1]), 1)
    except Exception:
        h4r = None
    return {"h4_bars": int(len(h4)), "h4_reversal": rev, "h4_rsi": h4r, **prov}


# ==========================================================
# 3) كون الأسهم (Universe) — ناسداك فقط (v2.0)
# ==========================================================
def get_universe() -> list:
    """البورصة المعتمدة: ناسداك فقط (nasdaqlisted.txt)"""
    urls = [
        "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
    ]
    symbols = []
    for url in urls:
        try:
            r = requests.get(url, headers=UA, timeout=40)
            r.raise_for_status()
            lines = r.text.splitlines()
            header = lines[0].split("|")
            idx = {name: i for i, name in enumerate(header)}
            sym_col = "Symbol" if "Symbol" in idx else "ACT Symbol"
            for ln in lines[1:]:
                if ln.startswith("File Creation Time"):
                    continue
                parts = ln.split("|")
                if len(parts) < len(header):
                    continue
                sym = parts[idx[sym_col]].strip()
                name = parts[idx.get("Security Name", 1)].strip()
                etf = parts[idx["ETF"]].strip() if "ETF" in idx else "N"
                test = parts[idx["Test Issue"]].strip() if "Test Issue" in idx else "N"
                if etf == "Y" or test == "Y":
                    continue
                if not sym.isalpha():           # يستبعد .W $ = إلخ
                    continue
                if len(sym) == 5 and sym[-1] in "WRU":  # وارنت/حقوق/وحدات
                    continue
                bad = ("WARRANT", "RIGHT", " UNIT", "UNITS")
                if any(b in name.upper() for b in bad):
                    continue
                symbols.append(sym)
        except Exception as e:
            log(f"⚠️ فشل تحميل {url}: {e}")
    symbols = sorted(set(symbols))
    log(f"حجم كون ناسداك بعد الفلترة: {len(symbols)} سهم")
    return symbols


# ==========================================================
# 4) تحميل البيانات التاريخية على دفعات
# ==========================================================
def _download_chunk(chunk: list, start: str):
    """تحميل دفعة مع إعادة محاولة وتراجع أسّي عند الخنق/الفشل (rate-limit)."""
    attempts = CONFIG.get("DOWNLOAD_RETRIES", 3)
    base = CONFIG.get("RETRY_BACKOFF", 3.0)
    for i in range(attempts):
        try:
            # 🕰️ point-in-time (BT_RAW_PRICE، باكتيست حصريًا): auto_adjust=False يُبقي
            # الأسعار الخام (لا تعديل تقسيم مستقبلي) فتُرفَض الإشارات الوهمية ببوابة M1.
            # الإنتاج =0 دائمًا (قفل B1) → auto_adjust=True كما كان.
            data = yf.download(chunk, start=start, interval="1d",
                               auto_adjust=not CONFIG.get("BT_RAW_PRICE"),
                               group_by="ticker",
                               threads=True, progress=False)
            if data is not None and len(data):
                return data
        except Exception as e:
            if i == attempts - 1:
                log(f"⚠️ فشل التحميل بعد {attempts} محاولات: {e}")
        if i < attempts - 1:
            time.sleep(base * (2 ** i))      # 3 ثم 6 ثم 12 ...
    return None


def _extract_into(out: dict, data, chunk: list):
    """استخراج إطارات الأسهم من نتيجة yfinance إلى out (يتجاهل الناقص)."""
    for sym in chunk:
        if sym in out:
            continue
        try:
            if len(chunk) == 1:
                df = data.copy()
                if isinstance(df.columns, pd.MultiIndex):
                    df = df[sym]
            else:
                if sym not in data.columns.get_level_values(0):
                    continue
                df = data[sym].copy()
            df = df.dropna(subset=["Close"])
            if len(df) >= CONFIG["MIN_BARS"]:
                out[sym] = df[["Open", "High", "Low", "Close", "Volume"]]
        except Exception:
            continue


def download_history(tickers: list) -> dict:
    if yf is None:
        raise RuntimeError("yfinance غير مثبتة — ثبّتها أو استخدم GitHub Actions")
    start = (dt.date.today() - dt.timedelta(days=CONFIG["HISTORY_DAYS"])).isoformat()
    out = {}
    size = CONFIG["CHUNK_SIZE"]
    chunks = [tickers[i:i + size] for i in range(0, len(tickers), size)]
    for n, chunk in enumerate(chunks, 1):
        log(f"تحميل دفعة {n}/{len(chunks)} ({len(chunk)} سهم)...")
        data = _download_chunk(chunk, start)
        if data is not None:
            _extract_into(out, data, chunk)
        time.sleep(CONFIG["CHUNK_SLEEP"])
    # تمريرة ثانية: إعادة محاولة الرموز التي لم تُحمّل (غالبًا خُنقت ضمن دفعتها)
    missing = [t for t in tickers if t not in out]
    if missing:
        log(f"إعادة محاولة {len(missing)} رمز لم يُحمّل...")
        for i in range(0, len(missing), size):
            sub = missing[i:i + size]
            data = _download_chunk(sub, start)
            if data is not None:
                _extract_into(out, data, sub)
            time.sleep(CONFIG["CHUNK_SLEEP"])
    log(f"بيانات صالحة لـ {len(out)} سهم")
    return out


# ==========================================================
# 4ب) تجميد باكتيست point-in-time (قابلية إعادة الإنتاج + رفض الوهميات)
# ==========================================================
# سبب (تدقيق خارجي 2026-07-12): الباكتيست يعيد التحميل حيًّا كل تشغيلة → غير قابل
# لإعادة الإنتاج (نجاح 26↔44% لمجرد إعادة التشغيل، تواريخ الإشارات تنزاح). وyfinance
# يعدّل التقسيمات دائمًا → أسعار وهمية (INLF المخزَّن $1779 وحقيقته $0.56 تحت أرضية M1).
# الحل: تحميل مرة → حفظ ببصمة → إلغاء تعديل التقسيم يدويًّا لبوابة M1. باكتيست/بنية فقط.
def _pit_split_factor(splits, asof) -> float:
    """عامل إلغاء تعديل التقسيم لسعر point-in-time: **raw = adjusted × factor**.
    `factor` = حاصل ضرب نسب التقسيم (بصيغة yfinance) للتقسيمات **بعد** تاريخ الشمعة `asof`
    فقط (لا تسريب: تقسيم لاحق لم يكن معروفًا وقتها). مثال INLF (شمعة 2025-12-09): تقسيمان
    لاحقان 1:16 (0.0625) و1:200 (0.005) → factor=0.0003125 → 1779.84×factor=$0.556 الحقيقي.
    نقيّة، فاشلة-آمنة → 1.0 (لا تقسيم/تعذّر = لا تغيير = سلوك اليوم)."""
    if splits is None:
        return 1.0
    try:
        items = splits.items() if hasattr(splits, "items") else splits
        a = pd.Timestamp(asof)
        a = a.tz_localize(None) if getattr(a, "tz", None) is not None else a
        f = 1.0
        for d, ratio in items:
            dd = pd.Timestamp(d)
            dd = dd.tz_localize(None) if getattr(dd, "tz", None) is not None else dd
            if dd > a and ratio and float(ratio) > 0:
                f *= float(ratio)
        return f if f > 0 else 1.0
    except Exception:
        return 1.0


def _pit_raw_price(adjusted_price, splits, asof) -> float:
    """السعر الحقيقي المعاصر (point-in-time) = المعدَّل × عامل إلغاء التقسيم اللاحق.
    يُستعمل لرفض «الإشارات الوهمية» ببوابة M1 (سعرها الحقيقي تحت الأرضية، لكن تعديل
    تقسيم لاحق رفعه فوقها). باكتيست فقط."""
    try:
        return float(adjusted_price) * _pit_split_factor(splits, asof)
    except Exception:
        return float(adjusted_price)


def _package_versions() -> dict:
    """إصدارات المكتبات الفعلية (provenance) — للمانفست v2. فاشل-آمن."""
    import importlib
    out = {}
    for _p in ("numpy", "pandas", "yfinance", "scipy", "sklearn", "statsmodels"):
        try:
            out[_p] = getattr(importlib.import_module(_p), "__version__", "?")
        except Exception:
            out[_p] = None
    return out


def save_frozen_dataset(hist: dict, splits: dict, asof: str, path: str,
                        extra_meta: dict = None) -> dict:
    """يحفظ لقطة باكتيست مجمَّدة (gzip-pickle) + ملف بصمة (manifest JSON) للاسترجاع
    القابل لإعادة الإنتاج 100%. المخزَّن: {hist, splits, asof, split_status, meta}.
    المانفست v2 (P0): SHA-256 + as-of + عدد الرموز + source_commit + إصدارات المكتبات +
    معاملات التحميل + بصمة الكون + الرموز الفاشلة + عدّ حالات التقسيم. بنية/باكتيست فقط."""
    import gzip
    import pickle
    import hashlib
    import json as _json
    import sys
    extra_meta = dict(extra_meta or {})
    payload = {"schema_version": 2, "hist": hist, "splits": splits, "asof": asof,
               "history_days": CONFIG["HISTORY_DAYS"],
               "split_status": extra_meta.get("split_status", {})}
    blob = pickle.dumps(payload, protocol=4)
    with gzip.open(path, "wb") as fh:
        fh.write(blob)
    sha = hashlib.sha256(blob).hexdigest()
    manifest = {
        "schema_version": 2,
        "asof": asof,
        "n_symbols": len(hist),
        "sha256": sha,                       # = payload_sha256 (توافق خلفي: المفتاح نفسه)
        "payload_sha256": sha,
        "history_days": CONFIG["HISTORY_DAYS"],
        "path": path,
        "source_commit": os.environ.get("GITHUB_SHA", "").strip() or None,
        "python_version": sys.version.split()[0],
        "package_versions": _package_versions(),
        "download_params": {"interval": "1d", "auto_adjust": True, "actions": True,
                            "group_by": "ticker", "history_days": CONFIG["HISTORY_DAYS"]},
        "universe_n": extra_meta.get("universe_n"),
        "universe_sha256": extra_meta.get("universe_sha256"),
        "failed_symbols": extra_meta.get("failed_symbols", []),
        "split_status_counts": extra_meta.get("split_status_counts", {}),
    }
    with open(path + ".manifest.json", "w", encoding="utf-8") as fh:
        _json.dump(manifest, fh, ensure_ascii=False, indent=2)
    return manifest


def load_frozen_dataset(path: str, strict: bool = False):
    """يحمّل لقطة مجمَّدة ويتحقّق من بصمتها (SHA-256) مقابل المانفست.
    **strict=True** (يُطلب حين BT_FROZEN_PATH): أي فشل تحقّق (ملف/مانفست مفقود · SHA لا يطابق ·
    schema غير مدعوم) → يرفع استثناء = fail-closed **بلا** أي تحميل حيّ بديل (P0). strict=False:
    فاشل-آمن (يرجّع None) كالسابق. يرجّع (hist, splits, asof, meta). meta فيه payload_sha256."""
    import gzip
    import pickle
    import hashlib
    import json as _json

    def _fail(msg):
        if strict:
            raise ValueError(f"Frozen dataset validation failed: {msg}")
        log(f"⚠️ تجميد: {msg}")
        return None, None, None, None

    try:
        with gzip.open(path, "rb") as fh:
            blob = fh.read()
    except Exception as e:
        return _fail(f"تعذّر فتح اللقطة {path}: {e}")
    try:
        with open(path + ".manifest.json", encoding="utf-8") as fh:
            man = _json.load(fh)
    except Exception as e:
        return _fail(f"تعذّر قراءة المانفست: {e}")
    got_sha = hashlib.sha256(blob).hexdigest()
    if man.get("sha256") and man["sha256"] != got_sha:
        return _fail(f"بصمة SHA-256 لا تطابق المانفست (البيانات تغيّرت): "
                     f"{got_sha[:12]} != {str(man['sha256'])[:12]}")
    try:
        payload = pickle.loads(blob)
    except Exception as e:
        return _fail(f"تعذّر فكّ payload: {e}")
    if not isinstance(payload, dict) or "hist" not in payload:
        return _fail("payload schema غير مدعوم (لا مفتاح hist)")
    meta = dict(man)
    meta["payload_sha256"] = got_sha
    meta["split_status"] = payload.get("split_status", {})
    return payload.get("hist"), payload.get("splits"), payload.get("asof"), meta


# ==========================================================
# 5) أدوات تحليل النموذج
# ==========================================================
def spike_info(close: np.ndarray, exclude_last: int):
    """أكبر مكسب خلال ≤ نافذة جلسات + عدد الانفجارات المنفصلة (معيد إجرام)"""
    c = close[:-exclude_last] if exclude_last > 0 else close
    n = len(c)
    if n < 15:
        return 0.0, 0
    w_max = CONFIG["PRIOR_SPIKE_WINDOW"]
    spike_end = np.zeros(n, dtype=bool)
    best = 0.0
    for w in range(1, w_max + 1):
        if n <= w:
            break
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = c[w:] / np.where(c[:-w] > 0, c[:-w], np.nan) - 1.0
        ratio = np.nan_to_num(ratio, nan=0.0)
        if ratio.size:
            best = max(best, float(np.max(ratio)))
            hits = np.where(ratio >= CONFIG["PRIOR_SPIKE_PCT"] / 100.0)[0] + w
            spike_end[hits] = True
    # عدّ العناقيد المنفصلة (فجوة ≥ 20 جلسة = انفجار مستقل)
    idxs = np.where(spike_end)[0]
    clusters = 0
    last = -10_000
    for i in idxs:
        if i - last >= 20:
            clusters += 1
        last = i
    return best * 100.0, clusters


def behavior_rise_profile(df):
    """🧬 بصمة «طريقة ارتفاع اليد» (سلوك المضارب — طلب المستخدم 2026-07-05، أولويته
    القصوى: «كيف يرفعها»). **عرض/تشخيص فقط — لا تمسّ الفرز ولا اختيار select_top إطلاقًا**
    (مقفول باختبار الثبات؛ درس C3: بصمة تدخل الاختيار = بوابة خفية تخنق ارتكازات فيصل).
    تقرأ من OHLCV **الخلفي فقط** (بلا نظر مستقبلي · بلا today · المسافات بالجلسات لا
    بالتقويم) كيف رفع المضاربُ السهمَ تاريخيًا — لأن بصمة اليد **تتكرّر**. المكوّنات
    ومتانة سندها عند فيصل (لا نلوّن الضعيف بلونه):
      • عدد الرفعات + الأكبر [جزئي: GWAV «تهييض 4 مرات» · «ارتفع سابقًا 100%+»].
      • حداثة آخر رفعة (جلسات) + إعادة الرفع بعده [استنتاج مسنود بـ«النموذج يتكرر» 7403
        · «ننتظر صعوده ثانية»].
      • بصمة المسح: كنس دعم بذيل ثم استعادة [مسنود قوي: 7379/7366/7402].
    يرجّع dict: score(0-100 أو None) · n_pumps · best_pump · recency_bars · repumps ·
    sweeps · label(عربي مبسّط). فاشل-آمن → score=None. **الوقود (فلوت/شورت) ليس هنا**
    (مكرّر لبوابتَي M13/M14 ومُعاير على ناجين — يبقى وسمًا حيًّا منفصلًا لا وزنًا)."""
    try:
        c = df["Close"].values.astype(float)
        lo = df["Low"].values.astype(float)
        n = len(c)
        if n < CONFIG["MIN_BARS"]:
            return {"score": None, "label": "—", "n_pumps": 0, "best_pump": 0.0,
                    "recency_bars": None, "repumps": 0, "sweeps": 0}
        bw = int(CONFIG["BASE_WINDOW"])
        best, _ = spike_info(c, exclude_last=bw)      # الأكبر (نفس ثوابت البوت)
        # مواقع عناقيد الانفجار (خلفي، لاستخراج الحداثة/الإعادة) — نفس منطق spike_info
        seg = c[:n - bw] if bw > 0 else c
        m = len(seg)
        w_max = int(CONFIG["PRIOR_SPIKE_WINDOW"])
        thr = CONFIG["PRIOR_SPIKE_PCT"] / 100.0
        ends = set()
        for w in range(1, w_max + 1):
            if m <= w:
                break
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = seg[w:] / np.where(seg[:-w] > 0, seg[:-w], np.nan) - 1.0
            ratio = np.nan_to_num(ratio, nan=0.0)
            ends.update((np.where(ratio >= thr)[0] + w).tolist())
        clusters = []
        last = -10_000
        for i in sorted(ends):
            if i - last >= 20:                        # فجوة 20ج = انفجار مستقل
                clusters.append(int(i))
            last = i
        n_pumps = len(clusters)
        recency_bars = (m - 1 - clusters[-1]) if clusters else None
        repumps = max(0, n_pumps - 1)                 # كم مرّة أعاد الرفع بعد الأولى
        # بصمة المسح التاريخية: كنس أدنى نافذة W بذيل ≥8% ثم إغلاق يستعيدها
        sweeps = 0
        W = 20
        for i in range(W, m):
            sup = float(np.min(lo[i - W:i]))
            if sup > 0 and lo[i] <= sup * 0.92 and c[i] >= sup:
                sweeps += 1
        # الدرجة المركّبة (سقف 100): العدد 35 · المقدار 15 · الحداثة 15 · الإعادة 10 · المسح 25
        pump_ct = min(n_pumps, 4)                      # سقف 4 = «تهييض 4 مرات»
        count_pts = pump_ct / 4.0 * 35.0
        mag_pts = min(best / 200.0, 1.0) * 15.0        # 200%+ = يد قوية
        rec_pts = (max(0.0, 1.0 - recency_bars / 250.0) * 15.0
                   if recency_bars is not None else 0.0)
        repump_pts = min(repumps, 3) / 3.0 * 10.0
        sweep_pts = min(sweeps, 3) / 3.0 * 25.0
        score = int(round(count_pts + mag_pts + rec_pts + repump_pts + sweep_pts))
        if n_pumps == 0:
            label = "رفعة يتيمة / يد خاملة"
        elif score >= 70:
            label = "🔥 يد نشطة تعيد الضخّ بقوة"
        elif score >= 45:
            label = "يد فعّالة (تعيد الرفع)"
        else:
            label = "نشاط محدود"
        return {"score": score, "label": label, "n_pumps": n_pumps,
                "best_pump": round(best, 0), "recency_bars": recency_bars,
                "repumps": repumps, "sweeps": sweeps}
    except Exception:
        return {"score": None, "label": "—", "n_pumps": 0, "best_pump": 0.0,
                "recency_bars": None, "repumps": 0, "sweeps": 0}


def group_pump_scar(df, scan_bars=90, rise_window=5, break_window=15):
    """N1 (لوحة علامات اليد — طلب المستخدم 2026-07-08): «رفعة قروب ثم كسر دعوم» —
    قفزة مفاجئة بسيولة عالية (نمط الضخّ الجماعي/القروب) يعقبها كسر متعمّد للدعم
    لهزّ المتعلّقين قبل الانطلاق. **عرض/تشخيص فقط · خلفي بلا نظر مستقبلي** (النمط
    اكتمل تاريخيًا حتى آخر شمعة). العتبات من الموجود: الصعود ≥`EXPLOSION_PCT`
    خلال ≤5ج + حجم يوم القفزة ≥`VOL_SPIKE_MULT`× متوسط 20ج (سيولة القروب). يعيد
    آخر نمط مطابق في آخر `scan_bars`: {found, jump_pct, bars_ago, broke_support,
    pre_support} أو None."""
    try:
        c = df["Close"].values.astype(float)
        lo = df["Low"].values.astype(float)
        v = df["Volume"].values.astype(float)
        n = len(c)
        if n < 40:
            return None
        rise_thr = CONFIG["EXPLOSION_PCT"] / 100.0
        vmult = CONFIG["VOL_SPIKE_MULT"]
        start = max(21, n - scan_bars)
        found = None
        for i in range(start, n):
            base = float(np.min(c[max(0, i - rise_window):i]))
            vavg = float(np.mean(v[i - 20:i]))
            if base <= 0 or vavg <= 0:
                continue
            rise = c[i] / base - 1.0
            if rise < rise_thr or v[i] < vmult * vavg:     # قروب: قفزة + سيولة
                continue
            j = max(0, i - rise_window)                     # دعم ما قبل الرفعة
            pre_sup = float(np.min(lo[max(0, j - 5):j + 1]))
            end = min(n, i + 1 + break_window)
            broke = bool(pre_sup > 0 and end > i + 1
                         and float(np.min(c[i + 1:end])) < pre_sup)
            found = {"found": True, "jump_pct": round(rise * 100, 0),
                     "bars_ago": int(n - 1 - i), "broke_support": broke,
                     "pre_support": round(pre_sup, 2)}
        return found
    except Exception:
        return None


def pivot_stability(lows: np.ndarray, closes: np.ndarray):
    """كشف Pivot Low + ثبات 3-5 جلسات (قاعدة التوقيت الذهبية)"""
    look = min(CONFIG["PIVOT_LOOKBACK"], len(lows))
    seg = lows[-look:]
    k_rel = int(np.argmin(seg))
    k = len(lows) - look + k_rel
    pivot = float(lows[k])
    bars_after = len(lows) - 1 - k
    if pivot <= 0:
        return None
    tol = pivot * (1.0 - CONFIG["STABILITY_TOL_PCT"] / 100.0)
    after = lows[k + 1:]
    # صفر جلسات بعد القاع = لا يوجد ثبات أصلاً
    if bars_after < 1:
        held = False
    else:
        held = bool(np.min(after) >= tol) and bool(closes[-1] > pivot)
    ready = held and CONFIG["STABILITY_MIN"] <= bars_after <= CONFIG["STABILITY_MAX"]
    return {"pivot": pivot, "bars_after": int(bars_after),
            "held": held, "ready": ready}


def _swing_highs(h: np.ndarray, price: float, win: int):
    """قمم سوينغ فوق السعر (قمة أعلى من المجاور ضمن نافذة win كل جهة)."""
    out = []
    n = len(h)
    for i in range(win, n - win):
        seg = h[i - win:i + win + 1]
        if h[i] == seg.max() and h[i] > price:
            out.append(float(h[i]))
    return out


def descending_trendline(df: pd.DataFrame, price: float,
                         win: int = 3, tol_pct: float = 2.0, span: int = 130):
    """§10 خط الترند الهابط (خطة طبقة التفسير — **عرض/تفسير فقط، حيّ فقط**، لا يمسّ
    الفرز/الأهداف/الوقف ولا يُستدعى بالباكتيست). المواصفة الملزمة (+ تشديدات
    المراجعة الخصومية 2026-07-08):
      • قمم سوينغ **فريدة** هابطة (هضبة مسطّحة ليست قمة) · **لمستان على الأقل** ·
        ميل سالب · تسامح ~2%. **كل قمة مرشّحة مرساةً** (ليس أعلى قمة حصريًا —
        قفلها على الأعلى كان يُسقط الخط الحقيقي عند ازدواج القمة/الريتيست).
      • **حد أدنى للانحدار:** هبوط الخط من المرساة إلى اليوم لا يقل عن التسامح
        نفسه — ازدواج قمة شبه أفقي = مقاومة أفقية، لا «خط ترند هابط».
      • **حارس ضد فبركة الخطوط:** الخط لا يُرسم لو اخترقته قمة فوق التسامح
        (يُسمح بالاختراق في آخر 5 شموع فقط = الكسر الحديث نفسه).
      • `line_price_now` بإسقاط خطي **عند آخر شمعة فقط** (لا نظر مستقبلي).
      • state **لكل مرشّح** (الكسر = إغلاق أخير فوق الخط بأكثر من التسامح ·
        testing = قربه · below = تحته)، والتفضيل: **قائم (غير مكسور) أولًا** ثم
        الأكثر لمساتٍ ثم الأدنى الآن (أقرب حاجز = الأكثر تحفّظًا) — خط مكسور
        كثير اللمسات لا يحجب خطًا قائمًا يسقف السعر فعلًا.
      • الحالة لقطة يومية والخط قد يُستبدل بتطوّر البنية (رأس كسرٍ فاشل يصير
        مرساة جديدة) — سلوك مقصود، يُعاد الحساب يوميًا من بيانات اليوم.
    يرجع dict {touches, slope_per_bar, anchor, line_price_now, state}
    أو None لو لا خط صادق."""
    try:
        h = df["High"].values.astype(float)[-span:]
        c = df["Close"].values.astype(float)[-span:]
        n = len(h)
        if n < 30 or price <= 0:
            return None
        tol = tol_pct / 100.0
        # قمة سوينغ **فريدة** ضمن نافذتها (تعادل = هضبة مسطّحة، ليست قمة —
        # حارس ضد فبركة خط من ضجيج قاعدة مسطّحة)
        piv = [(i, float(h[i])) for i in range(win, n - win)
               if h[i] == h[i - win:i + win + 1].max()
               and (h[i - win:i + win + 1] == h[i]).sum() == 1]
        if len(piv) < 2:
            return None
        break_allow = 5                              # آخر 5 شموع = كسر حديث مسموح
        last_close = float(c[-1])
        best = None
        for k, (ia, pa) in enumerate(piv):           # كل قمة مرشّحة مرساةً
            for ib, pb in piv[k + 1:]:
                if pb >= pa:                          # لمسة أدنى من مرساتها حتمًا
                    continue
                slope = (pb - pa) / (ib - ia)         # سالب حتمًا (pb < pa)
                # صدق الخط: لا قمة تخترقه فوق التسامح (عدا آخر 5 شموع)
                ok = True
                for i in range(ia, max(ia, n - break_allow)):
                    if h[i] > (pa + slope * (i - ia)) * (1.0 + tol):
                        ok = False
                        break
                if not ok:
                    continue
                line_now = pa + slope * (n - 1 - ia)
                if line_now <= 0:
                    continue
                # حد أدنى للانحدار: نزول الخط من المرساة لليوم ≥ التسامح
                if pa - line_now < pa * tol:
                    continue
                touches = sum(1 for j, pj in piv if j >= ia
                              and abs(pj / (pa + slope * (j - ia)) - 1.0) <= tol)
                if touches < 2:
                    continue
                if last_close > line_now * (1.0 + tol):
                    state = "broken"
                elif last_close >= line_now * (1.0 - tol):
                    state = "testing"
                else:
                    state = "below"
                cand = {"touches": touches, "slope_per_bar": round(slope, 6),
                        "anchor": round(pa, 4),
                        "line_price_now": round(line_now, 4), "state": state}
                if best is None or (
                        (state != "broken", touches, -line_now)
                        > (best["state"] != "broken", best["touches"],
                           -best["line_price_now"])):
                    best = cand
        return best
    except Exception:
        return None


def psychological_levels(price: float, top: float):
    """المستويات النفسية الدائرية بين السعر والسقف (أرقام صحيحة وأنصاف:
    1.0, 1.5, 2.0...). المضاربون يضعون أوامر عندها فتعمل كمقاومات."""
    if price <= 0 or top <= price:
        return []
    # خطوة مناسبة لحجم السعر
    if price < 5:
        step = 0.5
    elif price < 20:
        step = 1.0
    elif price < 100:
        step = 5.0
    else:
        step = 10.0
    lvls = []
    x = (int(price / step) + 1) * step
    while x <= top and len(lvls) < 12:
        lvls.append(round(x, 2))
        x += step
    return lvls


def _red_candle_heads(df: pd.DataFrame, price: float, span: int = 130):
    """رؤوس (High) الشموع الحمرا ذات الجسم المعتبر فوق السعر = مقاومات/أهداف.
    قاعدة فيصل الموثّقة: «رأس الشمعة الحمرا = مقاومة/هدف» (مطبّقة في 4س،
    نضيفها لليومي حتى لا نتخطّى مناطق العرض المتوسطة مثل EZRA 4.00/4.38 التي
    ليست قمم سوينغ بل منشأ هبوط). إضافة فقط — لا تحذف أي مستوى."""
    o = df["Open"].values.astype(float)
    c = df["Close"].values.astype(float)
    h = df["High"].values.astype(float)
    n = len(c)
    thr = CONFIG.get("RES_RED_HEAD_MIN_DROP", 3.0) / 100.0
    s = min(span, n)
    out = []
    for i in range(n - s, n):
        if o[i] > 0 and c[i] < o[i] and (o[i] - c[i]) / o[i] >= thr \
                and h[i] > price:
            out.append(float(h[i]))
    return out


def resistance_levels(df: pd.DataFrame, price: float, max_levels: int = 8,
                      include_red_heads: bool = True):
    """كشف مستويات المقاومة الأفقية فوق السعر — كخطوط فيصل الأفقية
    (SMX: 9.53/11.84/14/16.51/23 · LNAI: 2.80/3.25/3.49/3.83/4.35).

    الأولوية للقمم الحقيقية من الشارت، والمستويات النفسية تملأ الفراغات
    فقط (لا تزاحم القمم الفعلية):
    1) قمم سوينغ يومية (نافذتان: قصيرة 3 + أطول 6 لقمم أبعد)
    2) قمم سوينغ من الفريم الأسبوعي (فيصل يرسم من الأسبوعي أيضاً)
    3) مستويات نفسية دائرية — تُضاف فقط في الفجوات الكبيرة بين القمم
    ثم يجمّع المتقاربة (ضمن 3%) في مستوى واحد."""
    h = df["High"].values.astype(float)
    n = len(h)
    if n < 11 or price <= 0:
        return []
    # ---- 1+2) القمم الحقيقية (يومي + أسبوعي) لها الأولوية ----
    real = []
    real += _swing_highs(h, price, 3)
    real += _swing_highs(h, price, 6)
    if include_red_heads:                  # رؤوس الشموع الحمرا (قاعدة فيصل، يومي)
        real += _red_candle_heads(df, price)
    try:
        wk = resample_ohlc(df, "W")
        if wk is not None and len(wk) >= 7:
            real += _swing_highs(wk["High"].values.astype(float), price, 2)
            if include_red_heads:          # رؤوس حمرا أسبوعي (للشارتات الأسبوعية)
                real += _red_candle_heads(wk, price)
    except Exception:
        pass
    real = sorted(set(round(s, 2) for s in real if s > price))
    # تجميع القمم الحقيقية المتقاربة (ضمن 3%)
    real_clusters = []
    for s in real:
        if real_clusters and s <= real_clusters[-1] * 1.03:
            real_clusters[-1] = max(real_clusters[-1], s)
        else:
            real_clusters.append(s)
    # ---- 3) المستويات النفسية تملأ الفراغات الكبيرة فقط ----
    top = max(real_clusters) if real_clusters else price * 2.0
    psych = psychological_levels(price, top)
    # نضيف مستوى نفسي فقط إذا بعيد ≥4% عن كل قمة حقيقية (فجوة فعلية)
    psych_fill = [pv for pv in psych
                  if all(abs(pv / rc - 1.0) > 0.04 for rc in real_clusters)]
    # القمم الحقيقية لها الأولوية المطلقة (تُحجز أولاً ولا تُطرد).
    # النفسية تملأ المتبقي من الحد الأقصى فقط.
    slots_for_psych = max(0, max_levels - len(real_clusters))
    # النفسية القريبة أهم (الأهداف الأولى)، لكن نضمن بقاء أعلى قمة حقيقية
    if slots_for_psych and psych_fill:
        psych_fill = psych_fill[:slots_for_psych]   # الأقرب أولاً
    else:
        psych_fill = []
    merged = sorted(set(real_clusters + psych_fill))
    # تجميع نهائي للمتقاربة + ضمان فوق السعر
    final = []
    for s in merged:
        if final and s <= final[-1] * 1.03:
            final[-1] = max(final[-1], s)
        else:
            final.append(s)
    levels = [round(c, 2) for c in final if c > price]
    # ضمان: أعلى قمة حقيقية تبقى ضمن النتيجة (هدف التحرر الأبعد)
    if real_clusters:
        top_real = round(max(real_clusters), 2)
        if top_real not in levels:
            if len(levels) >= max_levels:
                levels = levels[:max_levels - 1]
            levels.append(top_real)
            levels = sorted(set(levels))
    # لو ما فيه قمم حقيقية إطلاقاً، رجّع النفسية كبديل
    if not real_clusters and not levels:
        tail = h[-120:] if n > 120 else h
        levels = sorted({round(float(x), 2) for x in tail if x > price})[:max_levels]
    return levels[:max_levels]


def first_target(df: pd.DataFrame):
    """الهدف 1: منشأ أكبر شمعة هابطة (≥15%) في الهبوط = منطقة المقاومة"""
    o = df["Open"].values
    c = df["Close"].values
    n = len(c)
    span = min(130, n - 1)
    seg_o, seg_c = o[-span:], c[-span:]
    with np.errstate(divide="ignore", invalid="ignore"):
        drop = (seg_o - seg_c) / np.where(seg_o > 0, seg_o, np.nan)
    drop = np.nan_to_num(drop, nan=0.0)
    i = int(np.argmax(drop))
    if drop[i] >= CONFIG["RED_CANDLE_MIN_DROP"] / 100.0:
        return float(seg_o[i])
    # بديل: أعلى قمة قبل منطقة التجميع
    hi = df["High"].values
    if n > 70:
        return float(np.max(hi[-70:-15]))
    return float(np.max(hi))


def _cluster_levels(levels, tol=0.02):
    """يدمج المستويات المتقاربة (ضمن نسبة tol) في مستوى واحد = متوسطها.
    يرجع قائمة مرتّبة تصاعدياً (بلا تكرار قريب)."""
    out = []
    for lv in sorted(float(x) for x in levels):
        if out and abs(lv / out[-1][0] - 1.0) <= tol:
            g = out[-1]
            g[1].append(lv)
            g[0] = sum(g[1]) / len(g[1])
        else:
            out.append([lv, [lv]])
    return [round(g[0], 2) for g in out]


def four_hour_levels(h4: pd.DataFrame, price: float):
    """منظومة فيصل على فريم 4 ساعات (موثّقة بصور @kisar_ — الـ6 صور):
      • resistances/أهداف = رؤوس (High) الشموع الحمرا الهابطة فوق السعر.
      • supports/دعوم   = ذيول (Low) الشمعة الحمرا اللي بعدها صعود مباشر، تحت السعر.
      • flip            = أعلى رأس حمرا تحت السعر (مقاومة استرجعها السهم = دعم/دخول).
      • sweep_low       = أدنى قاع 4س (يشمل خارج السوق) = ذيل المسح الحقيقي.
    يرجع dict أو None لو البيانات غير كافية. (طبقة إضافية — لا تمسّ الدعم/الوقف
    اليومي المقفول؛ معلومة مساندة لفيصل.)"""
    if h4 is None or len(h4) < 10 or not price:
        return None
    o = h4["Open"].values.astype(float)
    c = h4["Close"].values.astype(float)
    hi = h4["High"].values.astype(float)
    lo = h4["Low"].values.astype(float)
    n = len(c)
    red = c < o
    res, sup, heads_below = [], [], []
    for i in range(n):
        if not red[i]:
            continue
        if hi[i] > price * 1.005:                     # رأس حمرا فوق السعر = هدف
            res.append(hi[i])
        else:
            heads_below.append(hi[i])                  # رأس حمرا تحت السعر
        if i + 1 < n and c[i + 1] > c[i] and lo[i] < price * 0.995:
            sup.append(lo[i])                         # ذيل حمرا بعده صعود = دعم
    resistances = _cluster_levels(res)[:5]            # تصاعدي (أقرب هدف أولاً)
    supports = sorted(_cluster_levels(sup), reverse=True)[:5]  # أقرب دعم أولاً
    flip = round(max(heads_below), 2) if heads_below else None
    # N2 (لوحة علامات اليد): «سقف مُدار» = رأس مقاومة 4س تجمّعت عنده 3 لمسات فأكثر
    # (يد تبيع عند نفس السعر بانتظام). يُختار الأكثر لمسًا (الأكثر دفاعًا).
    managed = None
    grp = []
    for lv in sorted(res):
        if grp and abs(lv / (sum(grp) / len(grp)) - 1.0) <= 0.02:
            grp.append(lv)
        else:
            if len(grp) >= 3 and (managed is None or len(grp) > managed["touches"]):
                managed = {"price": round(sum(grp) / len(grp), 2),
                           "touches": len(grp)}
            grp = [lv]
    if len(grp) >= 3 and (managed is None or len(grp) > managed["touches"]):
        managed = {"price": round(sum(grp) / len(grp), 2), "touches": len(grp)}
    # تغطية الخضرا (المقطع: «تغطية الشمعة الحمراء بشمعة خضراء تعطي تأكيد»):
    # آخر شمعة حمرا — هل جاءت بعدها خضرا أغلقت عند/فوق جسمها (open الحمرا)؟
    # True=تأكيد · False=حمرا بلا تغطية (ننتظر) · None=لا شموع حمرا (غير منطبق).
    green_cover = None
    red_idx = [i for i in range(n) if red[i]]
    if red_idx:
        li = red_idx[-1]
        green_cover = bool(any(c[j] > o[j] and c[j] >= o[li]
                               for j in range(li + 1, n)))
    return {"supports": supports, "resistances": resistances,
            "flip": flip, "sweep_low": round(float(np.min(lo)), 2),
            "green_cover": green_cover, "managed_ceiling": managed}


def refine_targets_4h(t1, t2, t3, price, h4l):
    """دمج فيصل #1: يضيف رؤوس الشموع الحمرا على 4س لأهداف **t2/t3 فقط**
    (فيصل: «الأهداف ع يومي + 4 ساعات»). **t1 وRR مقفولان — لا يتغيّران.**
    يرجع (t2, t3) المنقّحة، أو الأصلية لو لا جديد من الـ4س."""
    if not h4l or not price:
        return t2, t3
    cap = price * CONFIG["TARGET_CAP_MULT"]
    gap = 1.0 + CONFIG["MIN_TARGET_GAP_PCT"] / 100.0
    extra = [round(float(x), 2) for x in (h4l.get("resistances") or [])
             if t1 * gap < x <= cap]
    if not extra:
        return t2, t3                       # لا مستوى 4س جديد → لا تغيير
    pool = sorted({round(t2, 2), round(t3, 2), *extra})
    out = [round(t1, 2)]
    for x in pool:
        if x >= out[-1] * gap:
            out.append(x)
        if len(out) >= 3:
            break
    while len(out) < 3:                      # إكمال احتياطي (نادر)
        out.append(round(out[-1] * 1.25, 2))
    return out[1], out[2]


def _swing_lows(low: np.ndarray, lo_bound: float, hi_bound: float, win: int):
    """قيعان سوينغ ضمن نطاق (قاع أدنى من المجاور ضمن نافذة win كل جهة)."""
    out = []
    n = len(low)
    for i in range(win, n - win):
        seg = low[i - win:i + win + 1]
        if low[i] == seg.min() and lo_bound < low[i] < hi_bound:
            out.append(float(low[i]))
    return out


def key_levels(df: pd.DataFrame, price: float, pivot: float, h4l=None):
    """الدعوم والمقاومات **الأساسية والفرعية** (مفهوم فيصل NAMM: «$2 دعم أساسي ·
    2.20 دعم فرعي»). أساسي = المستوى الأقوى/الهيكلي · فرعي = الأقرب للسعر (أول
    لمسة). يُثرى بمستويات 4س إن توفّرت. **معلومة/عرض فقط — لا يمسّ الدعم/الوقف
    المقفول.** يرجع dict أو None."""
    if df is None or not price or price <= 0:
        return None
    # ----- المقاومات فوق السعر (يومي + 4س) -----
    res = list(resistance_levels(df, price))
    if h4l:
        res += [x for x in (h4l.get("resistances") or []) if x > price]
    res = _cluster_levels([x for x in res if x > price * 1.01])
    res_minor = res[0] if res else None                  # الأقرب = مقاومة فرعية
    try:
        ft = first_target(df)                            # منشأ أكبر شمعة حمرا
    except Exception:
        ft = None
    if ft and ft > price * 1.02 and (res_minor is None or ft > res_minor * 1.02):
        res_major = round(float(ft), 2)                  # المقاومة الأساسية (الكبرى)
    else:
        res_major = res[1] if len(res) > 1 else res_minor
    # ----- الدعوم تحت السعر (يومي + 4س) -----
    sup_major = round(float(pivot), 2)                    # الأرضية = الدعم الأساسي
    cands = _swing_lows(df["Low"].values.astype(float),
                        pivot * 1.005, price * 0.99, 3)
    if h4l:
        cands += [x for x in (h4l.get("supports") or [])
                  if pivot * 1.005 < x < price * 0.99]
    cands = _cluster_levels(cands)
    sup_minor = cands[-1] if cands else None              # الأقرب للسعر = دعم فرعي
    return {"sup_major": sup_major, "sup_minor": sup_minor,
            "res_major": res_major, "res_minor": res_minor}


def key_levels_block(kl) -> list:
    """سطر الدعوم/المقاومات الأساسية والفرعية (مصطلحات فيصل). المستوى الناقص
    يظهر شرطة (-) ليبقى الشكل ثابتًا (قرار المستخدم)."""
    if not kl:
        return []

    def _f(v):
        return f"${v:.2f}" if v else "-"

    rmaj = kl.get("res_major")
    rmin = kl.get("res_minor")
    if rmaj == rmin:                       # مقاومة واحدة فقط = نعتبرها أساسية
        rmin = None
    sup = (f"🟢 دعم: أساسي {_f(kl.get('sup_major'))} · "
           f"فرعي {_f(kl.get('sup_minor'))}")
    res = f"🔴 مقاومة: فرعية {_f(rmin)} · أساسية {_f(rmaj)}"
    return ["   🧱 " + sup + " | " + res]


def h4_confirm_score(r) -> int:
    """دمج فيصل #3: قوة تأكيد الـ4س للترتيب فقط (0-3). **لا يمسّ أي بوابة
    ولا اختيار** — يرفع الإعدادات المحاذية لكل الفريمات لأعلى القائمة.
    +2 انعكاس 4س مؤكَّد · +1 مقاومة↗دعم قريبة (السعر استرجعها)."""
    s = 0
    if r.get("tf4h") == "✅ مؤكِّد":
        s += 2
    h4l = r.get("h4_levels") or {}
    price = r.get("price")
    if h4l.get("flip") and price and h4l["flip"] >= price * 0.92:
        s += 1
    return s


def _gaps_on_frame(df: pd.DataFrame, lookback: int):
    """كشف الفجوات الصاعدة على فريم واحد (يومي/أسبوعي/شهري).
    فجوة صاعدة = افتتاح الشمعة > إغلاق الشمعة السابقة بنسبة ≥ GAP_MIN_PCT.
    الفجوة "تُغلق" لو نزل Low لأي شمعة لاحقة تحت إغلاق ما قبل الفجوة.
    يرجع dict: count, max_gap, last_gap, last_gap_ago, unfilled."""
    empty = {"count": 0, "max_gap": 0.0, "last_gap": 0.0,
             "last_gap_ago": None, "unfilled": False}
    if df is None or len(df) < 2:
        return empty
    o = df["Open"].values.astype(float)
    c = df["Close"].values.astype(float)
    lw = df["Low"].values.astype(float)
    n = len(c)
    min_gap = CONFIG["GAP_MIN_PCT"]
    start = max(1, n - lookback)
    gaps = []
    for i in range(start, n):
        pc = c[i - 1]
        if pc <= 0:
            continue
        gp = (o[i] / pc - 1.0) * 100.0
        if gp >= min_gap:
            filled = bool(np.any(lw[i:] <= pc))   # أُغلقت لاحقاً؟
            gaps.append((gp, i, filled))
    if not gaps:
        return empty
    last = gaps[-1]
    return {
        "count": len(gaps),
        "max_gap": round(max(g[0] for g in gaps), 1),
        "last_gap": round(last[0], 1),
        "last_gap_ago": int(n - 1 - last[1]),
        "unfilled": (not last[2]),
    }


def gap_analysis(df: pd.DataFrame):
    """كشف الفجوات السعرية الصاعدة على الفريمات الثلاثة (يومي/أسبوعي/شهري).
    (شرط فيصل السادس + طلب فحص الفريمات). الفريم اليومي هو الأساس؛
    الأسبوعي/الشهري معلومة إضافية (نادرة بطبيعتها). يعيد التجميع من
    اليومي بلا أي تحميل إضافي — يستخدم resample_ohlc الموجودة.

    يرجع: نتيجة اليومي مدموجة (للتوافق مع الكود القديم) + مفاتيح:
      daily / weekly / monthly: نتيجة كل فريم،
      frames_with_gaps: كم فريم فيه فجوة (0-3)."""
    daily = _gaps_on_frame(df, CONFIG["GAP_LOOKBACK"])
    # الأسبوعي والشهري بإعادة تجميع (نوافذ أقصر لأن الشموع أكبر)
    weekly = {"count": 0, "max_gap": 0.0, "last_gap": 0.0,
              "last_gap_ago": None, "unfilled": False}
    monthly = dict(weekly)
    try:
        wdf = resample_ohlc(df, "W")
        weekly = _gaps_on_frame(wdf, CONFIG["GAP_LOOKBACK_W"])
    except Exception:
        pass
    try:
        mdf = resample_ohlc(df, "ME")
        monthly = _gaps_on_frame(mdf, CONFIG["GAP_LOOKBACK_M"])
    except Exception:
        pass
    frames = int(daily["count"] > 0) + int(weekly["count"] > 0) \
        + int(monthly["count"] > 0)
    # المخرج الأساسي = اليومي (توافق مع الاستدعاءات القديمة) + إضافات
    out = dict(daily)
    out["daily"] = daily
    out["weekly"] = weekly
    out["monthly"] = monthly
    out["frames_with_gaps"] = frames
    return out


def unfilled_gaps_above(df: pd.DataFrame, lookback: int):
    """كشف الفجوات السعرية غير المملوءة *فوق* السعر الحالي (مفهوم فيصل
    الحقيقي من صور MTVA/TRUG/ONCO: السهم طار من فوق ونزل بعنف تاركاً
    فراغاً هابطاً، استقر تحته، فصار الفراغ مقاومة/هدف فوق السعر).

    فجوة هابطة (down gap) = High لشمعة < Low للشمعة السابقة (فراغ كامل
    بينهما لم يتداول فيه السهم). الفراغ = [High الحالية ... Low السابقة].
    "غير مملوء وفوق السعر" = قاع الفراغ (High الحالية) أعلى من السعر
    الحالي، ولم يُغلق (لم يصعد أي High لاحق إلى داخل الفراغ بعد تكوّنه).
    يرجع: list مناطق [{bottom, top, size_pct, ago}] + ملخص (nearest)."""
    out = {"zones": [], "count": 0, "nearest": None, "nearest_dist_pct": None}
    if df is None or len(df) < 2:
        return out
    h = df["High"].values.astype(float)
    lw = df["Low"].values.astype(float)
    c = df["Close"].values.astype(float)
    n = len(c)
    price = float(c[-1])
    if price <= 0:
        return out
    min_gap = CONFIG["GAP_MIN_PCT"]
    start = max(1, n - lookback)
    zones = []
    for i in range(start, n):
        prev_low = lw[i - 1]
        cur_high = h[i]
        if prev_low <= 0 or cur_high <= 0:
            continue
        # فجوة هابطة: قمة الشمعة الحالية تحت قاع السابقة (فراغ كامل)
        if cur_high >= prev_low:
            continue
        gap_size = (prev_low / cur_high - 1.0) * 100.0
        if gap_size < min_gap:
            continue
        bottom = cur_high      # قاع الفراغ (أقرب حافة للسعر)
        top = prev_low         # قمة الفراغ
        # لازم الفراغ فوق السعر الحالي (هدف/مقاومة)
        if bottom <= price:
            continue
        # غير مملوء: لم يدخل أي High لاحق إلى الفراغ (لم يصعد فوق bottom)
        filled = bool(np.any(h[i + 1:] >= bottom)) if i + 1 < n else False
        if filled:
            continue
        zones.append({
            "bottom": round(bottom, 3),
            "top": round(top, 3),
            "size_pct": round(gap_size, 1),
            "ago": int(n - 1 - i),
        })
    if not zones:
        return out
    zones_sorted = sorted(zones, key=lambda z: z["bottom"])
    nearest = zones_sorted[0]
    out["zones"] = zones_sorted
    out["count"] = len(zones_sorted)
    out["nearest"] = nearest
    out["nearest_dist_pct"] = round((nearest["bottom"] / price - 1.0) * 100.0, 1)
    return out


def all_unfilled_gaps_above(df: pd.DataFrame):
    """يجمع الفجوات غير المملوءة فوق السعر من الفريمات الثلاثة (يومي/
    أسبوعي/شهري) — لاستخدامها كأهداف ومقاومات (مفهوم فيصل)."""
    daily = unfilled_gaps_above(df, CONFIG["GAP_ABOVE_LOOKBACK_D"])
    weekly = {"zones": [], "count": 0, "nearest": None, "nearest_dist_pct": None}
    monthly = dict(weekly)
    try:
        weekly = unfilled_gaps_above(resample_ohlc(df, "W"),
                                     CONFIG["GAP_ABOVE_LOOKBACK_W"])
    except Exception:
        pass
    try:
        monthly = unfilled_gaps_above(resample_ohlc(df, "ME"),
                                      CONFIG["GAP_ABOVE_LOOKBACK_M"])
    except Exception:
        pass
    # كل المناطق مجمّعة ومرتبة من الأقرب فوق السعر
    allz = (daily["zones"] + weekly["zones"] + monthly["zones"])
    allz = sorted(allz, key=lambda z: z["bottom"])
    nearest = allz[0] if allz else None
    return {
        "daily": daily, "weekly": weekly, "monthly": monthly,
        "all_zones": allz, "count": len(allz), "nearest": nearest,
    }


_REJECT_STATS = {}
_SCAN_STATS = {}        # صحة الفرز: حجم الكون مقابل البيانات الصالحة المحمّلة
_REJECT_REASONS = {}    # سبب رفض كل سهم (رمز→سبب) — لتتبّع الفرص الفائتة
_MISSED = []            # فرص فائتة: مرفوض صعد فعلاً (symbol/reason/gain)
_CUR_SYM = None         # السهم قيد التحليل (لربط سبب الرفض به)


def _reject(code):
    """يسجّل سبب رفض السهم (عدّاد + لكل سهم لتتبّع الفرص الفائتة) ويرجع None."""
    _REJECT_STATS[code] = _REJECT_STATS.get(code, 0) + 1
    if _CUR_SYM:
        _REJECT_REASONS[_CUR_SYM] = code
    return None


def _hanging_man(df: pd.DataFrame) -> bool:
    """كشف «الرجل المشنوق» (D8، فيصل CUR IMG_6334): الشمعة الأخيرة بشكل مطرقة
    (جسم صغير · ظل سفلي طويل ≥2× الجسم · ظل علوي صغير) لكن **عند قمة قريبة بعد
    صعود** = تحذير انعكاس هابط. عرض/تحذير فقط — لا نقاط ولا بوابة (لا يمسّ الفرز).
    يطابق منطق technical_report.py:482-484."""
    try:
        if df is None or len(df) < 20:
            return False
        o = float(df["Open"].iloc[-1])
        h = float(df["High"].iloc[-1])
        lo = float(df["Low"].iloc[-1])
        c = float(df["Close"].iloc[-1])
        rng = h - lo
        if rng <= 0:
            return False
        body = abs(c - o)
        up = h - max(o, c)               # الظل العلوي
        dn = min(o, c) - lo              # الظل السفلي
        small_up = up <= max(body * 0.5, 0.10 * rng)
        recent_high = float(df["High"].tail(20).max())
        near_top = recent_high > 0 and c >= recent_high * 0.97
        return (body <= 0.40 * rng and dn >= 2.0 * body
                and small_up and near_top)
    except Exception:
        return False


def analyze_ticker(sym: str, df: pd.DataFrame, pullback: bool = False):
    """يرجع dict بالنتيجة إذا اجتاز الشروط الإلزامية، وإلا None.
    pullback=True: وضع «مراقبة الارتداد» — سهم ارتكاز حقيقي (بنية مكتملة)
    لكنه ارتفع فوق دخوله؛ نرصده ليُتابَع يوميًا وندخله لو رجع للدعم (انهيار
    البورصة). الوضع العادي (pullback=False) يبقى مطابقًا تمامًا بلا أي تغيير."""
    global _CUR_SYM
    _CUR_SYM = sym                 # لربط سبب الرفض بالسهم (تتبّع الفرص الفائتة)
    try:
        close = df["Close"]
        high, low, vol = df["High"], df["Low"], df["Volume"]
        c = close.values
        price = float(c[-1])
        watch_reasons = []        # أسباب وضعه في مراقبة الارتداد
        risen = False             # هل ارتفع فعلاً فوق دخوله؟ (شرط الارتداد)

        # ---- M1: السعر ----
        if price < CONFIG["MIN_PRICE"]:
            return _reject("M1_سعر")

        # نواقص التأكيد (v2.7): تُجمع من M2/M3 الحدّية + M9-M14 + RR.
        # 0 = قائمة A · 1-2 = قائمة B · أكثر = يُرفض.
        soft_fails = []

        # ---- M2: الهبوط من قمة 52 أسبوع (تدرّج v2.7) ----
        # أرضية صلبة (<40%) = ليس ارتكازًا → رفض. حدّي (40-50%) = نقص (B).
        # مثالي (≥50%) = بلا عقوبة. (>97% = محتضر → رفض).
        hi52 = float(high.tail(252).max())
        if hi52 <= 0:
            return _reject("M2_hi52")
        drop_pct = (1.0 - price / hi52) * 100.0
        if drop_pct > CONFIG["MAX_DROP_PCT"]:
            return _reject("M2_هبوط_فوق_97")  # محتضر/فخ تقسيم
        if drop_pct < CONFIG["MIN_DROP_FLOOR"]:
            return _reject("M2_هبوط_تحت_40")   # تحت الأرضية = ليس ارتكازًا
        if drop_pct < CONFIG["MIN_DROP_PCT"]:
            soft_fails.append(f"الهبوط {drop_pct:.0f}% (المثالي 50% فأكثر)")

        # ---- M3: الانفجار السابق (تدرّج v2.7) ----
        # أرضية (<60%) = رفض. حدّي (60-100%) = نقص (B). مثالي (≥100%) = بلا عقوبة.
        best_spike, n_spikes = spike_info(c, exclude_last=CONFIG["BASE_WINDOW"])
        if best_spike < CONFIG["PRIOR_SPIKE_FLOOR"]:
            return _reject("M3_انفجار_تحت_60")  # ما انفجر كفاية
        if best_spike < CONFIG["PRIOR_SPIKE_PCT"]:
            soft_fails.append(f"الانفجار السابق {best_spike:.0f}% (المثالي 100% فأكثر)")

        # ---- M4: تجميع حالي (مدى ضيق + ما انفجر بعد) ----
        bw = CONFIG["BASE_WINDOW"]
        base_hi = float(high.tail(bw).max())
        base_lo = float(low.tail(bw).min())
        if base_lo <= 0:
            return _reject("M4_base_lo")
        base_range = (base_hi / base_lo - 1.0) * 100.0
        if base_range > CONFIG["BASE_RANGE_MAX_PCT"]:
            if not pullback:
                return _reject("M4_base_واسعة")
            risen = True       # القاعدة اتسعت لأنه ارتفع = مرشّح ارتداد
            watch_reasons.append("ارتفع عن قاعدته")
        if len(c) > 6:
            gain5 = (c[-1] / c[-6] - 1.0) * 100.0
            # «انفجر فعلاً» (قفزة 5 جلسات) = فاتنا القطار — يُرفض حتى للارتداد
            if gain5 > CONFIG["RECENT_RISE_BLOCK_PCT"]:
                return _reject("M4_انفجر_فعلاً")

        # ---- M5: سيولة دولارية ----
        dvol = float((close * vol).tail(20).mean())
        if not math.isfinite(dvol) or dvol < CONFIG["MIN_DOLLAR_VOL"]:
            return _reject("M5_سيولة")

        # ---- M6: توافق الفريمات (شهري/أسبوعي/يومي) — بوابة لينة (v2.7) ----
        # (كانت رفضًا صلبًا؛ صارت نقصًا حتى تظهر أسهم الارتكاز قبل تأكيد الفريمات)
        mtf = multi_timeframe(df)
        if mtf["count"] < CONFIG["TF_MIN_REVERSALS"]:
            soft_fails.append(f"توافق الفريمات {mtf['count']} من 3 (نحتاج 2 على الأقل)")

        # ---- M7: نمط شمعة انعكاسي — بوابة لينة (v2.7) ----
        patterns = mtf["patterns"]
        if not patterns:
            soft_fails.append("لا نمط شمعة انعكاسي")

        # ---- M8: فجوة سعرية معتبرة حديثة — إلزامي (v2.4 نسخة B) ----
        # فيصل: "أسهم الارتكاز عدوها السيولة بسبب الفجوات الكبيرة"
        # (نحسب الفجوات مرة واحدة هنا ونعيد استخدامها في النقاط — بلا تكرار)
        gaps = gap_analysis(df)
        if CONFIG.get("GAP_REQUIRED", False):
            recent_gap = (gaps["count"] > 0
                          and gaps["last_gap_ago"] is not None
                          and gaps["last_gap_ago"] <= CONFIG["GAP_REQ_WINDOW"])
            if not recent_gap:
                return None  # لا فجوة معتبرة حديثة → يُرفض (بوابة فيصل السادسة)

        # (soft_fails مُهيّأة بعد M1؛ تتجمّع من M2/M3 الحدّية + M9-M14 + RR)
        # ---- M9: فجوة غير مملوءة فوق السعر (مفهوم فيصل) — بوابة لينة ----
        # من صور MTVA/TRUG/ONCO: الفجوة منطقة-هدف فوق السعر الراكد.
        gaps_above = all_unfilled_gaps_above(df)
        maxd = CONFIG["GAP_ABOVE_MAX_DIST_PCT"]
        near_zones = [z for z in gaps_above["all_zones"]
                      if (z["bottom"] / price - 1.0) * 100.0 <= maxd]
        if CONFIG.get("GAP_ABOVE_REQUIRED", False) and not near_zones:
            soft_fails.append("ما فيه فجوة سعرية فوقه (هدف)")

        # ---- M10: RSI — قاعدة فيصل الذهبية «مستحيل يتحرك قبل يوصل 23-27» ----
        # جزء صلب (إلزامي): لازم يكون لمس التشبع البيعي (≤27) خلال نافذة قريبة.
        #   سهم ما وصل التشبع أصلاً = ما اكتمل قاعه → لا يتحرك → يُرفض.
        # جزء لين (نقص→B): RSI الحالي ما طار فوق 40 (لسّه ما انطلق).
        rsi_s = rsi(close)
        r_now = float(rsi_s.iloc[-1])
        r_prev = float(rsi_s.iloc[-2])
        r_min_recent = float(rsi_s.tail(CONFIG["RSI_RECENT_WINDOW"]).min())
        r_min_os = float(rsi_s.tail(CONFIG["RSI_OS_LOOKBACK"]).min())
        if CONFIG.get("RSI_GATE_REQUIRED", False):
            if r_min_os > CONFIG["RSI_OS_HARD"]:
                if not pullback:
                    return _reject("M10_RSI_ما_تشبّع")  # قاعه >32 = ليس ارتكازًا
                watch_reasons.append("لم يصل التشبّع بعد")  # سيتشبّع عند الارتداد
            elif r_min_os > CONFIG["RSI_OVERSOLD"]:
                soft_fails.append(f"قاع RSI {r_min_os:.0f} (المثالي 27 أو أقل)")  # 27-32 → B
            if r_now > CONFIG["RSI_NOW_HARD"]:
                if not pullback:
                    return _reject("M10_RSI_فات_القطار")  # >50 = فات الارتكاز
                risen = True
                watch_reasons.append(f"RSI ارتفع للـ{r_now:.0f}")
            elif r_now > CONFIG["RSI_MAX_NOW"]:
                soft_fails.append(f"RSI الآن {r_now:.0f} أعلى من 40")  # 40-50 طار → B

        # ---- M11: تقاطع MACD إيجابي — بوابة لينة ----
        m_line, m_sig = macd(close)
        macd_ok = (float(m_line.iloc[-1]) >= float(m_sig.iloc[-1])
                   or (m_line.iloc[-5:] > m_sig.iloc[-5:]).any())
        if CONFIG.get("MACD_GATE_REQUIRED", False) and not macd_ok:
            soft_fails.append("MACD لسّا ما أعطى إشارة إيجابية")

        # ---- M12: السعر على المتوسط الأسي 30/50 — بوابة لينة ----
        ema30 = ema(close, 30)
        ema50 = ema(close, 50)
        band = CONFIG["MA_GATE_MAX_ABOVE_PCT"] / 100.0
        ma_ok = any(
            m > 0 and (price >= m * (1.0 - 0.02))
            and (price / m - 1.0) <= band
            for m in (ema30, ema50)
        )
        if CONFIG.get("MA_GATE_REQUIRED", False) and not ma_ok:
            _md = ((price / ema30 - 1.0) * 100.0) if ema30 else 0.0
            if _md < 0:
                _rise = ((ema30 * 0.98 / price - 1.0) * 100.0) if price else 0.0
                soft_fails.append(
                    f"السعر أقل بـ{abs(_md):.0f}% من متوسطه المتحرك "
                    f"(يفتح بصعود ~{_rise:.0f}% أو بثبات أسابيع)")
            else:
                soft_fails.append(
                    f"السعر أعلى بـ{_md:.0f}% من متوسطه المتحرك "
                    "(يفتح برجوعه قرب متوسطه)")

        # حد أقصى للنواقص هنا (M13/M14 شورت/فلوت تُضاف لاحقًا في الفرز)
        if not pullback and len(soft_fails) > CONFIG.get("WATCH_MAX_FAILS", 3):
            return _reject(f"نواقص_فوق_{CONFIG.get('WATCH_MAX_FAILS',3)}")

        # ---- M13: الشورت العالي — يُطبّق كمرحلة ثانية بعد الفرز ----
        # (الشورت يُجلب فقط للأسهم الناجحة لأن جلبه بطيء — لا يمكن لكل
        # السوق. لذا بوابة الشورت تُطبّق في screen_market بعد هذا الفرز،
        # على القائمة القصيرة الناجحة. انظر apply_short_gate أدناه.)

        # ======== اجتاز الإلزامي → حساب النقاط ========
        score = 0
        flags = []
        warnings = []

        # انفجار ضخم جداً قد يكون أثر تقسيم عكسي في البيانات
        # (وقد يكون حقيقياً مثل SBET) — لا نخفيه، بل ننبّه للتحقق اليدوي
        if best_spike >= CONFIG["SPIKE_VERIFY_PCT"]:
            warnings.append(f"انفجار سابق ضخم ({best_spike:.0f}%) — "
                            "تحقق يدوياً من تقسيم عكسي")
        # تحذير سيولة منخفضة (يصعب الدخول/الخروج بأمان)
        if dvol < CONFIG["LOW_LIQ_WARN"]:
            warnings.append(f"سيولة منخفضة ({fmt_money(dvol)}/يوم)")
        # D8: شمعة «الرجل المشنوق» عند قمة = تحذير انعكاس (فيصل CUR: انتظر الدعم)
        if _hanging_man(df):
            warnings.append("شمعة الرجل المشنوق (انعكاس هابط محتمل) — "
                            "انتظر تكوين دعم قبل الدخول")

        # RSI: قاع تشبع حديث (≤5 جلسات) + انحناء + لم يرتد فوق 50
        rsi_s = rsi(close)
        r_now, r_prev = float(rsi_s.iloc[-1]), float(rsi_s.iloc[-2])
        r_min_recent = float(rsi_s.tail(CONFIG["RSI_RECENT_WINDOW"]).min())
        if (r_min_recent <= CONFIG["RSI_OVERSOLD"] and r_now > r_prev
                and r_now <= CONFIG["RSI_MAX_NOW"]):
            score += 15
            flags.append(f"RSI تشبع وانحناء (قاع {r_min_recent:.0f}→{r_now:.0f})")

        m_line, m_sig = macd(close)
        if (m_line.iloc[-5:] > m_sig.iloc[-5:]).any() and \
           float(m_line.iloc[-1]) >= float(m_sig.iloc[-1]):
            score += 10
            flags.append("تقاطع MACD")

        k_line, k_sig = kst(close)
        try:
            if float(k_line.iloc[-1]) > float(k_sig.iloc[-1]) and \
               float(k_line.iloc[-1]) > float(k_line.iloc[-3]):
                score += 10
                flags.append("KST صاعد")
        except Exception:
            pass

        # بصمة الفوليوم: جفاف + شمعة خضراء ضخمة منفردة
        v = vol.values.astype(float)
        v20 = float(vol.tail(20).mean())
        v5 = float(vol.tail(5).mean())
        big_green = False
        if v20 > 0 and len(c) > 21:
            for i in range(len(c) - 20, len(c)):
                if v[i] >= CONFIG["VOL_SPIKE_MULT"] * v20 and c[i] > df["Open"].values[i]:
                    big_green = True
                    break
        if big_green:
            score += 10
            flags.append("شمعة فوليوم ضخمة")
        if v20 > 0 and v5 <= CONFIG["VOL_DRY_RATIO"] * v20:
            score += 5
            flags.append("جفاف بيع")

        sma30 = ema(close, 30)
        sma50 = ema(close, 50)
        near_ma = any(ma > 0 and abs(price / ma - 1.0) <= 0.05
                      for ma in (sma30, sma50))
        if near_ma:
            score += 10
            flags.append("يرتكز على متوسط 30/50")

        if n_spikes >= 2:
            score += 15
            flags.append(f"معيد إجرام ({n_spikes} انفجارات)")

        ps = pivot_stability(low.values.astype(float), c)
        if ps and ps["held"]:
            score += 15           # الثبات يرفع النقاط (مكوّن، لا قرار جاهزية)
            flags.append(f"ثبات {ps['bars_after']} جلسات فوق القاع")
        # §11 (طبقة التفسير): جلسات منذ القاع الرئيسي — حقل عرض/تفسير فقط
        bars_after_low = int(ps["bars_after"]) if ps else None

        # نسبة جاهزية الدخول 0-100% — المصدر الوحيد للجاهزية في كل البوت
        # (العرض + الترتيب + الحالة المنطقية تشتقّ كلها من هذا الرقم → لا تناقض)
        try:
            readiness_pct, _ = entry_readiness(df)
        except Exception:
            readiness_pct = None
        # قرار المستخدم: السهم "بعيد عن الدخول" (نسبة < NEAR_PCT) لا يدخل القائمة
        # حتى المراقبة B — لأنه لسّه ما تهيّأ. (None = بيانات ناقصة → فائدة الشك)
        if readiness_pct is not None and readiness_pct < CONFIG["NEAR_PCT"]:
            if not pullback:
                return _reject(f"بعيد_عن_الدخول({readiness_pct:.0f}%)")
            risen = True       # بعيد عن الدخول = مرشّح ارتداد (ننتظر رجوعه)
            watch_reasons.append(f"بعيد عن الدخول ({readiness_pct:.0f}%)")
        # «جاهز» (البوليان) = مشتقّة حصريًا من النسبة (≥ READY_PCT). مصدر واحد:
        # مستحيل يطلع سهم «🟢 جاهز» ونسبته أقل من «🟡 يقترب». انتهى التناقض.
        ready = (readiness_pct is not None
                 and readiness_pct >= CONFIG["READY_PCT"])

        # مسح سيولة حقيقي: كسر قاع *سابق* ثم استعادة فوقه
        # (القاع السابق = أدنى قاع في الجلسات 35→10 قبل الأخيرة)
        mfi_s = mfi(high, low, close, vol)
        sweep = False
        lows_arr = low.values.astype(float)
        if len(lows_arr) > 35:
            prior_low = float(np.min(lows_arr[-35:-10]))
            recent_min = float(np.min(lows_arr[-10:]))
            if (prior_low > 0 and recent_min < prior_low * 0.995
                    and price > prior_low
                    and float(mfi_s.iloc[-1]) >= float(mfi_s.tail(10).min())):
                sweep = True
        if sweep:
            score += 10
            flags.append("مسح سيولة (كسر قاع سابق واستعادة)")

        # نقاط إضافية: تماسك الفريمات الكامل (3/3) + نمط شمعة قوي
        if mtf["count"] >= 3:
            score += 10
            flags.append("توافق 3 فريمات")
        if any(p in STRONG_PATTERNS for p in patterns):
            score += 5
            flags.append("نمط شمعة قوي")

        # ======== مؤشرات فيصل الإضافية (v2.7): نقاط فقط، لا ترفض ========
        ind = {}   # قيم تُعرض بالبطاقة (مطابقة لصفحة إعدادات فيصل)
        try:
            atr_s = atr(high, low, close, CONFIG["ATR_PERIOD"])
            ind["atr"] = float(atr_s.iloc[-1])
        except Exception:
            ind["atr"] = 0.0
        # MFI: كشف "خلق السيولة الوهمية" — تباعد صعودي عند مسح القاع
        try:
            mfi_now = float(mfi_s.iloc[-1])
            mfi_min = float(mfi_s.tail(10).min())
            ind["mfi"] = mfi_now
            if sweep and mfi_now > mfi_min and mfi_min <= CONFIG["MFI_OVERSOLD"]:
                score += CONFIG["MFI_DIVERGENCE_SCORE"]
                flags.append(f"تباعد MFI صعودي ({mfi_min:.0f}→{mfi_now:.0f}) — سيولة مخفية")
        except Exception:
            ind["mfi"] = 50.0
        # Bollinger: انكماش الحزمة = تجميع قبل الانفجار
        try:
            _bm, _bu, _bl, _pctb, _bw = bollinger(close)
            ind["boll_pctb"] = float(_pctb.iloc[-1])
            bw_tail = _bw.dropna().tail(60)
            if len(bw_tail) >= 20:
                thr = float(bw_tail.quantile(CONFIG["BOLL_SQUEEZE_PCTL"]))
                if float(_bw.iloc[-1]) <= thr:
                    score += CONFIG["SCORE_BOLLINGER_SQUEEZE"]
                    flags.append("انكماش حزمة كلنجر (تجميع)")
        except Exception:
            pass
        # StochRSI: من التشبع وانعطاف صاعد
        try:
            _sk, _sd = stoch_rsi(close)
            ind["stochrsi_k"] = float(_sk.iloc[-1])
            if float(_sk.iloc[-2]) <= 20 and float(_sk.iloc[-1]) > float(_sk.iloc[-2]):
                score += CONFIG["SCORE_STOCHRSI"]
                flags.append("StochRSI انعطاف من التشبع")
        except Exception:
            pass
        # Williams %R: من التشبع البيعي وانعطاف صاعد (فيصل يقرنه بكلنجر —
        # «بانتظار دخول المضارب»، تغريدة 7377)
        try:
            _wlr = williams_r(high, low, close)
            ind["williams_r"] = float(_wlr.iloc[-1])
            if (float(_wlr.iloc[-2]) <= CONFIG["WILLIAMS_OVERSOLD"]
                    and float(_wlr.iloc[-1]) > float(_wlr.iloc[-2])):
                score += CONFIG["SCORE_WILLIAMS"]
                flags.append("Williams %R انعطاف من التشبع")
        except Exception:
            pass
        # DMI: +DI يتجاوز -DI (بداية اتجاه صاعد)
        try:
            _pdi, _mdi, _adx = dmi_adx(high, low, close)
            ind["plus_di"] = float(_pdi.iloc[-1])
            ind["minus_di"] = float(_mdi.iloc[-1])
            ind["adx"] = float(_adx.iloc[-1])
            if float(_pdi.iloc[-1]) > float(_mdi.iloc[-1]):
                score += CONFIG["SCORE_DMI"]
                flags.append("DMI: ‎+DI فوق ‎-DI")
        except Exception:
            pass
        # MA5/MA20 القصيرة: استعادتها = تجميع مبكر (فيصل يستخدمها مع 30/50)
        try:
            ma5 = float(close.rolling(5).mean().iloc[-1])
            ma20 = float(close.rolling(20).mean().iloc[-1])
            ind["ma5"], ind["ma20"] = ma5, ma20
            if ma5 > 0 and price >= ma5 and ma5 >= ma20 * 0.99:
                score += CONFIG["SCORE_MA_SHORT"]
                flags.append("استعاد MA5/MA20 (تجميع)")
        except Exception:
            pass
        # VWAP + DMA(10,50,10) — خطوط فيصل المرجعية (عرض فقط)
        try:
            ind["vwap"] = rolling_vwap(df)
            _ddd, _ama = dma_oscillator(close)
            ind["dma_ddd"] = float(_ddd.iloc[-1])
            ind["dma_ama"] = float(_ama.iloc[-1])
        except Exception:
            pass

        # الفجوات السعرية (شرط فيصل السادس) — نقاط (gaps محسوبة فوق في M8)
        if gaps["count"] > 0:
            if gaps["max_gap"] >= CONFIG["GAP_BIG_PCT"]:
                score += CONFIG["GAP_SCORE_BIG"]
                flags.append(f"فجوة عالية يومي {gaps['max_gap']:.0f}%")
            else:
                score += CONFIG["GAP_SCORE_NORMAL"]
                flags.append(f"فجوة صاعدة يومي {gaps['max_gap']:.0f}%")
            if gaps["unfilled"]:
                flags.append("فجوة يومية مفتوحة (لم تُغلق)")
            # نقاط إضافية لو الفجوات على أكثر من فريم (يومي+أسبوعي/شهري)
            if gaps.get("frames_with_gaps", 1) >= 2:
                score += CONFIG["GAP_SCORE_MULTIFRAME"]
                wk = gaps.get("weekly", {}).get("count", 0)
                mo = gaps.get("monthly", {}).get("count", 0)
                extra_fr = []
                if wk > 0:
                    extra_fr.append("أسبوعي")
                if mo > 0:
                    extra_fr.append("شهري")
                if extra_fr:
                    flags.append("فجوات متعددة الفريمات (" +
                                 "، ".join(extra_fr) + ")")

        # فجوة-هدف غير مملوءة فوق السعر (مفهوم فيصل) — نقاط + هدف
        if near_zones:
            score += CONFIG["GAP_ABOVE_SCORE"]
            nz = near_zones[0]
            dist = round((nz["bottom"] / price - 1.0) * 100.0, 1)
            flags.append(f"فجوة-هدف فوق السعر عند ${nz['bottom']:.2f} "
                         f"(+{dist:.0f}%)")

        if not pullback and score < CONFIG["SCORE_MIN"]:
            return _reject(f"نقاط_تحت_{CONFIG['SCORE_MIN']}")

        # ======== المستويات المقترحة ========
        pivot = ps["pivot"] if ps else float(low.tail(20).min())
        # الوقف تحت القاع بنسبة فيصل (~7%، تحت منطقة "سحب السيولة")
        # فيصل (SMX): القاع 6.11، سحب السيولة قد يصل 5.80 ثم يرتد.
        # الوقف الفعلي تحت منطقة السحب — لا 1-2% الضيقة التي تُضرب بالتذبذب.
        s_lo, s_hi = CONFIG["STOP_BELOW_LOW_PCT"]
        stop_hi = pivot * (1 - s_lo / 100.0)    # أعلى الوقف (أقرب للقاع)
        stop_lo = pivot * (1 - s_hi / 100.0)    # أدنى الوقف (تحت السحب)
        # وقف ATR أُلغي عمدًا (USE_ATR_STOP=False): كان يعمّق الوقف ويُكنَس.
        # منهجية فيصل: 5-7% تحت القاع فقط (قرار مقفول — لا تُعِد فرع ATR هنا).
        big = price >= CONFIG["LARGE_PRICE_CUT"]
        d_lo, d_hi = (CONFIG["SWEEP_LARGE_PCT"] if big
                      else CONFIG["SWEEP_SMALL_PCT"])
        sweep_lo = pivot * (1 - d_hi / 100.0)
        sweep_hi = pivot * (1 - d_lo / 100.0)

        # ---- دفعات الدخول (أسلوب فيصل): أوامر عند الدعم وصعوداً بخطوة ثابتة.
        #      تتعبّى كلما نزل السعر للدعم؛ أدنى دفعة = الدعم = أفضل تعبئة.
        #      (فيصل @kisar_: 1.70/1.75/1.80 · الوقف 1.50). ----
        n_tr = max(1, int(CONFIG["ENTRY_TRANCHES"]))
        step = CONFIG["ENTRY_STEP_PCT"] / 100.0
        tranches = [round(pivot * (1 + step * i), 2) for i in range(n_tr)]
        entry_lo = tranches[0]                           # عند الدعم (أفضل تعبئة)
        entry_hi = tranches[-1]                          # أعلى دفعة (أسوأ تعبئة)

        # ضمان ذهبي: الوقف لازم يكون دائمًا تحت أدنى منطقة الدخول.
        # (السحب 8-10% قد يكون أعمق من الوقف 5-7%، فيصير الوقف فوق الدخول
        #  = يُضرب فورًا. هنا نُجبر الوقف تحت الدخول بهامش فيصل 5-7%.)
        entry_floor = min(entry_lo, entry_hi)
        if stop_hi >= entry_floor:
            stop_hi = round(entry_floor * (1 - s_lo / 100.0), 2)
        if stop_lo >= stop_hi:
            stop_lo = round(entry_floor * (1 - s_hi / 100.0), 2)

        # ---- الأهداف الثلاثة (من مستويات الشارت الحقيقية، لا عشوائية) ----
        # مصادر الأهداف كلها من الشارت (كخطوط فيصل الأفقية):
        #   1) مقاومات سوينغ أفقية فوق السعر (قمم ارتد منها)
        #   2) قيعان الفجوات غير المملوءة فوق السعر
        #   3) منشأ الشمعة الهابطة الكبيرة + قمة الموجة
        resist = resistance_levels(df, price)        # مقاومات حقيقية
        raw_t1 = first_target(df)
        raw_t3 = float(high.tail(60).max())
        cap = price * CONFIG["TARGET_CAP_MULT"]            # سقف واقعي
        min_first = price * (1.0 + CONFIG["MIN_T1_GAIN_PCT"] / 100.0)
        gap = 1.0 + CONFIG["MIN_TARGET_GAP_PCT"] / 100.0
        # نجمع كل المرشحين من الشارت
        target_cands = list(resist) + [raw_t1, raw_t3]
        # أهداف الفريم الأسبوعي (فيصل: «الأهداف ع يومي + أسبوعي»). إضافة فقط —
        # المنطق أدناه (min_first/cap/gap) يرتّبها ويمنع الأهداف غير الواقعية.
        if CONFIG.get("USE_MULTIFRAME_TARGETS", True):
            try:
                wk = resample_ohlc(df, "W")
                if wk is not None and len(wk) >= 10:
                    # الأسبوعي إضافي فقط (لا يغيّر t1) → بلا رؤوس حمرا قريبة
                    target_cands += list(resistance_levels(
                        wk, price, include_red_heads=False))
                    target_cands.append(first_target(wk))
            except Exception:
                pass
        if CONFIG.get("GAP_ABOVE_USE_AS_TARGET", False):
            for z in near_zones:
                target_cands.append(z["bottom"])   # قاع الفجوة = مقاومة
        # Fibonacci كأهداف (فيصل IMG_6473): مستويات ارتداد من القاع للقمة
        if CONFIG.get("USE_FIB_TARGETS", False):
            try:
                fib = fibonacci_levels(pivot, raw_t3)
                for key in ("0.382", "0.500", "0.618", "0.786", "1.000"):
                    if fib.get(key):
                        target_cands.append(fib[key])
            except Exception:
                pass
        cands = sorted(t for t in target_cands
                       if min_first <= t <= cap)
        targets = []
        for t in cands:                         # دمج الأهداف الملتصقة
            if not targets or t >= targets[-1] * gap:
                targets.append(round(float(t), 2))
        if not targets:                         # لا مقاومة فوق ضمن السقف
            # نأخذ أقرب مقاومة حتى لو فوق السقف (هدف حقيقي أفضل من عشوائي)
            above = sorted(t for t in (list(resist) + [raw_t3]) if t > price)
            targets = [round(above[0], 2)] if above else [round(price * 1.25, 2)]
        while len(targets) < 3:                 # إكمال بأقرب مقاومة أعلى
            nxt = next((t for t in cands if t > targets[-1] * gap), None)
            targets.append(round(nxt, 2) if nxt else round(targets[-1] * 1.25, 2))
        t1, t2, t3 = targets[0], targets[1], targets[2]

        # ===== "تحرر السهم" + "قاب/الفجوة" (مفهوم فيصل الذهبي، v2.7) =====
        # تحرر = أعلى مقاومة حقيقية فوق السعر؛ تجاوزها بثبات = انطلاق لمساحة
        # بلا مقاومة (فيصل: LNAI تحرر 3.38 · CLIK 2.21 · FRSX فوق 3 · SMX 23).
        liberation = None
        lib_near = False
        try:
            res_above = sorted(x for x in resist if x > price)
            if res_above:
                liberation = round(float(res_above[-1]), 2)  # أعلى مقاومة = بوابة التحرر
            elif raw_t3 > price:
                liberation = round(float(raw_t3), 2)
            if liberation:
                # "قريب من التحرر" = ضمن 12% تحت بوابة التحرر (قابل للانطلاق)
                lib_near = price >= liberation * 0.88
        except Exception:
            liberation = None
        # قاب/الفجوة: أقرب فجوة غير مملوءة فوق السعر = منطقة-هدف ذهبية
        qab = None
        if near_zones:
            z0 = near_zones[0]
            qab = {"bottom": z0["bottom"], "top": z0["top"],
                   "size_pct": z0["size_pct"],
                   "dist_pct": round((z0["bottom"] / price - 1.0) * 100.0, 1)}
            flags.append(f"قاب (فجوة) فوق السعر عند ${z0['bottom']:.2f} "
                         f"(فراغ {z0['size_pct']:.0f}% = هدف ذهبي)")
        if lib_near and liberation:
            flags.append(f"🔓 قرب التحرر فوق ${liberation:.2f} "
                         f"(تجاوزه بثبات = انطلاق)")

        # عائد/مخاطرة من سعر الدخول المخطّط (أعلى نطاق الدخول = أسوأ تعبئة)،
        # لا من السعر الحالي — لأن المضارب يدخل عند الدعم وينتظر التنفيذ، فالعائد
        # الحقيقي يُقاس من نقطة الشراء الفعلية (يصحّح ظلم الأسهم المرتدّة فوق دخولها).
        # مرجع RR موحّد = متوسط الدفعات (فيصل يمتّع → تعبئته الفعلية ≈ المتوسط).
        entry_ref = round(sum(tranches) / len(tranches), 4)
        risk = max(entry_ref - stop_lo, 1e-9)
        rr = (t1 - entry_ref) / risk
        rr2 = (t2 - entry_ref) / risk
        # v2.7: ضعف RR = نقص (ينقل لقائمة B المراقبة) بدل الرفض النهائي —
        # متوافق مع قرار «ما نطلع صفر». لو تجاوز مجموع النواقص الحد → يُرفض.
        if rr < CONFIG["MIN_RR_T1"]:
            soft_fails.append("العائد مقابل المخاطرة منخفض")
            if not pullback and len(soft_fails) > CONFIG.get("WATCH_MAX_FAILS", 3):
                return _reject("RR+نواقص_فوق_الحد")

        # ملخص حالة بوابات فيصل (للرسالة المختصرة) — كلها ✅ لأن السهم
        # اجتازها، لكن نعرضها للتأكيد البصري ولمعرفة قيمة كل شرط فعلياً
        ema30_v = ema(close, 30)
        macd_now_ok = (float(m_line.iloc[-1]) >= float(m_sig.iloc[-1])
                       or (m_line.iloc[-5:] > m_sig.iloc[-5:]).any())
        ma_dist = ((price / ema30_v - 1.0) * 100.0) if ema30_v > 0 else 0.0
        gates_status = {
            "السعر فوق 2": (True, f"${price:.2f}"),
            "هبوط 50-97%": (True, f"{drop_pct:.0f}%"),
            "انفجار 100% فأكثر": (True, f"{best_spike:.0f}%"),
            "قاعدة ضيقة": (True, f"{base_range:.0f}%"),
            "سيولة كافية": (True, fmt_money(dvol)),
            "توافق فريمات": (mtf["count"] >= CONFIG["TF_MIN_REVERSALS"],
                            f"{mtf['count']}/3"),
            "شمعة انعكاس": (bool(patterns),
                           "، ".join(patterns) if patterns else "لا"),
            "RSI تشبع (27 أو أقل)": (r_min_recent <= CONFIG["RSI_OVERSOLD"],
                                    f"قاع {r_min_recent:.0f}"),
            "RSI تحت 40": (r_now <= CONFIG["RSI_MAX_NOW"], f"{r_now:.0f}"),
            "تقاطع MACD": (macd_now_ok, "إيجابي" if macd_now_ok else "لا"),
            "على المتوسط الأسي": (
                any(m > 0 and price >= m * 0.98
                    and (price / m - 1.0) <= CONFIG["MA_GATE_MAX_ABOVE_PCT"] / 100.0
                    for m in (ema30_v, ema(close, 50))),
                f"{ma_dist:+.0f}% من EMA30"),
            "فجوة-هدف فوق": (bool(near_zones),
                            f"{len(near_zones)} منطقة" if near_zones else "لا"),
        }

        # وضع الارتداد: لازم يكون مرتفعًا فعلاً فوق دخوله (وإلا فهو مرشّح
        # دخول عادي يلتقطه المسار العادي). لو مرتفع → tier="W" مراقبة ارتداد.
        if pullback and not risen:
            return None
        tier = "W" if pullback else "B"    # 🪦 A/B متقاعد → فئة واحدة "B" (مؤهّل) · W للارتداد

        return {
            "symbol": sym, "price": price, "score": int(min(score, 100)),
            "drop_pct": drop_pct, "best_spike": best_spike,
            "n_spikes": n_spikes, "base_range": base_range,
            "rsi": r_now, "dollar_vol": dvol,
            "vol_today": float(vol.iloc[-1]),   # D10: لحساب تدوير الفلوت في enrich
            "pivot": pivot, "stop": (stop_lo, stop_hi),
            "entry": (entry_lo, entry_hi), "tranches": tranches,
            "key_levels": key_levels(df, price, pivot),
            "sweep": (sweep_lo, sweep_hi),  # محفوظ للمستقبل — غير معروض؛ حماية الوقف
                                            # الفعلية = الحارس الذهبي أعلاه (D2)
            "t1": t1, "t2": t2, "t3": t3, "rr": rr, "rr2": rr2,
            "ready": ready, "readiness": readiness_pct,
            "flags": flags, "warnings": warnings,
            "tf_count": mtf["count"], "tf_display": mtf["display"],
            "patterns": patterns,
            "gaps": gaps,
            "gaps_above": gaps_above,
            "gates_status": gates_status,
            "soft_fails": soft_fails,                 # بوابات تأكيد ناقصة
            "tier": tier,                             # B مؤهّل · W مراقبة ارتداد (A متقاعد)
            "watch_reasons": watch_reasons,           # أسباب وضع الارتداد
            "indicators": ind,                        # مؤشرات فيصل الإضافية
            "liberation": liberation,                 # بوابة "تحرر السهم"
            "lib_near": lib_near,                      # قريب من التحرر؟
            "qab": qab,                               # أقرب فجوة (قاب) فوق السعر
            "bars_after": bars_after_low,             # §11: جلسات منذ القاع (تفسير/عرض)
        }
    except Exception as exc:
        # C4 (خطة الضبط، موافقة المستخدم 2026-07-03): تسجيل تشخيصي فقط —
        # كان استثناءً صامتًا يخفي أخطاء بيانات/حسابات وقد يفوّت سهمًا بلا أثر.
        # **لا يغيّر نتيجة الفرز إطلاقًا** (يبقى return None كما هو).
        try:
            log(f"⚠️ استثناء تحليل {sym}: {type(exc).__name__}: {exc}")
        except Exception:
            pass
        return None


# ==========================================================
# 6) الإثراء: شورت (Fintel→FINRA→Yahoo) / إعلانات SEC / تقسيمات
# ==========================================================
def finra_daily_short(symbols: set) -> dict:
    """الشورت اليومي من ملفات FINRA المجانية (المصدر الأساسي الموثوق).
    يقرأ حتى يومين متاحين لسد النواقص لكل رمز."""
    out = {}
    today = dt.date.today()
    days_used = 0
    for back in range(0, 10):
        if days_used >= 2 or len(out) >= len(symbols):
            break
        d = today - dt.timedelta(days=back)
        if d.weekday() >= 5:
            continue
        url = ("https://cdn.finra.org/equity/regsho/daily/"
               f"CNMSshvol{d.strftime('%Y%m%d')}.txt")
        try:
            r = requests.get(url, headers=UA, timeout=40)
            if r.status_code != 200 or "|" not in r.text[:200]:
                continue
            days_used += 1
            for ln in r.text.splitlines()[1:]:
                p = ln.split("|")
                if len(p) >= 5 and p[1] in symbols and p[1] not in out:
                    try:
                        out[p[1]] = int(p[2])
                    except ValueError:
                        pass
            log(f"شورت FINRA ليوم {d.isoformat()} "
                f"(مغطّى: {len(out)}/{len(symbols)})")
        except Exception:
            continue
    return out


# ==========================================================
# 🔒 معدّل الاقتراض (Cost to Borrow) — طلب المستخدم 2026-07-09: فيصل يركّز عليه
# للارتكاز (رابط chartexchange بصورة 9431). فلوت صغير + شورت منخفض + **اقتراض صعب**
# = وقود سكويز. **عرض/سياق + تحذير إيجابي فقط — خارج الفرز/الاختيار** (لا عتبة قرار
# موثّقة من فيصل؛ لا بوابة رفض). فاشل-آمن مطلق → «—». مصدران فاشلان-آمنان: Fintel
# (نفس طلب الشورت، بلا نداء إضافي) ثم iBorrowDesk (بيانات IBKR، احتياط للتغطية).
# ==========================================================
def _parse_fintel_borrow(html: str) -> dict:
    """نقيّة: يستخرج رسوم الاقتراض (Cost to Borrow %) + الأسهم المتاحة من صفحة Fintel
    (نفس HTML المجلوب للشورت — بلا نداء إضافي). يرجّع {} لو غاب أيّهما. فاشل-آمن."""
    d = {}
    try:
        mb = re.search(r"(?:Cost\s*to\s*Borrow|Borrow\s*Fee(?:\s*Rate)?)"
                       r"[^0-9%]{0,80}?([\d.]+)\s*%", html, re.I | re.S)
        if mb:
            d["borrow_fee"] = float(mb.group(1))
        ma = re.search(r"(?:Shares\s*Available|Available\s*(?:Shares|to\s*Borrow))"
                       r"[^0-9]{0,80}?([\d,]{2,})", html, re.I | re.S)
        if ma:
            d["shares_available"] = int(ma.group(1).replace(",", ""))
    except Exception:
        pass
    return d


def _parse_iborrow(data) -> dict:
    """نقيّة: يستخرج (رسوم%, أسهم متاحة) من رد iBorrowDesk (بيانات IBKR). يأخذ أحدث
    لقطة `real_time` (وإلا `daily`). يرجّع {} لو غير صالح/فارغ. فاشل-آمن."""
    try:
        rt = data.get("real_time") or data.get("daily") or []
        if isinstance(rt, dict):
            rt = [rt]
        if not rt:
            return {}
        last = rt[-1]
        out = {}
        if last.get("fee") is not None:
            out["borrow_fee"] = float(last["fee"])
        if last.get("available") is not None:
            out["shares_available"] = int(last["available"])
        return out
    except Exception:
        return {}


def iborrow_info(sym: str) -> dict:
    """غلاف شبكي فاشل-آمن لـ iBorrowDesk (احتياط لمعدّل الاقتراض حين يُحجب Fintel).
    يرجّع {} عند أي فشل (بلا شبكة/حجب/شكل غير متوقّع) — لا يعيق الإثراء إطلاقًا.
    ⚠️ خدمة مجتمعية (بيانات IBKR) قد تنقطع؛ العرض «—» عندها. عرض/سياق فقط."""
    try:
        r = requests.get(f"https://iborrowdesk.com/api/ticker/{sym.upper()}",
                         headers=BROWSER_UA, timeout=8)
        if r.status_code != 200:
            return {}
        return _parse_iborrow(r.json() or {})
    except Exception:
        return {}


def _parse_ce_borrow(html: str) -> dict:
    """محلّل ChartExchange النقي (اقتراح المستخدم 2026-07-10 — **مصدر فيصل نفسه**،
    رابطه في صورة 9431). مكتوب من الشكل الحقيقي (مجسّ Actions، لا تخمين): مقطع
    `name="ctbtoday"` يحوي جملة ثابتة الشكل عبر الرموز (GEOS/PTN مطابقان):
      «As of <b>2026-07-10 03:54 AM EDT</b>, there were <b>550,000</b> shares
       available with a fee of <b>0.40%</b>.»
    (بيانات Interactive Brokers، تُحدَّث كل 15 دقيقة.) نقتصّ نافذة بعد المرساة،
    نجرّد الوسوم، ثم regex بسيط. {} عند أي شكل غير متوقّع (فاشل-آمن)."""
    try:
        i = html.find('name="ctbtoday"')
        if i < 0:
            return {}
        window = re.sub(r"<[^>]+>", " ", html[i:i + 1200])
        m = re.search(r"there were\s*([\d,]+)\s*shares available with a fee of"
                      r"\s*([\d,]+(?:\.\d+)?)\s*%", window)
        if not m:
            return {}
        return {"shares_available": int(m.group(1).replace(",", "")),
                "borrow_fee": float(m.group(2).replace(",", ""))}
    except Exception:
        return {}


def ce_borrow_info(sym: str) -> dict:
    """غلاف شبكي فاشل-آمن لصفحة اقتراض ChartExchange (ناسداك فقط — بورصة البوت
    المعتمدة). أثبت مجسّ Actions (2026-07-10) أن بيئة البوت تصل 200/سريعة رغم
    حجب بيئات التطوير. {} عند أي فشل — لا يعيق الإثراء. عرض/سياق فقط."""
    try:
        r = requests.get("https://chartexchange.com/symbol/"
                         f"nasdaq-{sym.lower()}/borrow-fee/",
                         headers=BROWSER_UA, timeout=8)
        if r.status_code != 200:
            return {}
        return _parse_ce_borrow(r.text or "")
    except Exception:
        return {}


def _ce_num(s):
    """يحوّل رقم ChartExchange المختصر (12.55M · 778K · 1.2B · 550,000) إلى int.
    None عند التعذّر (فاشل-آمن)."""
    try:
        s = s.strip().replace(",", "")
        mult = {"K": 1e3, "M": 1e6, "B": 1e9}.get(s[-1:].upper(), 1)
        if mult != 1:
            s = s[:-1]
        return int(float(s) * mult)
    except Exception:
        return None


def _parse_ce_float(html: str):
    """محلّل الفلوت النقي من صفحة ChartExchange (اقتراح المستخدم 2026-07-10 لحلّ
    «الفلوت مجهول» من ياهو المخنوق). مكتوب من الشكل الحقيقي (مجسّ Actions،
    مؤكَّد على GEOS/PTN/FEMY):
      `stat-flow-label">Float</div><div class="stat-flow-value">12.55M</div>`
    مطابقة تسمية «Float» **بالضبط** (لا «Free Float»/«Free Float %»). يرجّع
    الفلوت int أو None (فاشل-آمن). عرض/سياق فقط — خارج الفرز."""
    try:
        m = re.search(r'stat-flow-label">Float</div>\s*<div[^>]*'
                      r'stat-flow-value[^>]*>\s*([\d.,]+)\s*([KMB]?)', html)
        if not m:
            return None
        return _ce_num(m.group(1) + m.group(2))
    except Exception:
        return None


def ce_float_info(sym: str):
    """غلاف شبكي فاشل-آمن لفلوت ChartExchange (صفحة النظرة العامة، ناسداك فقط).
    None عند أي فشل — لا يعيق الإثراء. عرض/سياق فقط — خارج الفرز (M14 لا تُمسّ)."""
    try:
        r = requests.get("https://chartexchange.com/symbol/"
                         f"nasdaq-{sym.lower()}/", headers=BROWSER_UA, timeout=8)
        if r.status_code != 200:
            return None
        return _parse_ce_float(r.text or "")
    except Exception:
        return None


def refresh_borrow(s: dict, today_iso: str, fetch=None) -> None:
    """تحديث يومي لاقتراض سهم قائمة من ChartExchange + **مسار «المتاح»** في
    `borrow_hist` [[تاريخ، متاح]…] (سقف 14). فيصل يتابع «المتاح» يوميًّا (IMG_9505:
    جدول Changes — المتاح تضخّم 30 ألف→600 ألف في 3 أيام قبيل حكم «طاخ طيخ»)،
    فمسار التضخّم نفسه معلومة. فاشل-آمن: فشل الجلب = القيم القديمة تبقى (تعذّر ≠
    اختفاء). عرض/سياق فقط — خارج الفرز."""
    try:
        d = (fetch or ce_borrow_info)(s.get("symbol", "")) or {}
        if not d:
            return
        s["borrow_fee"] = d.get("borrow_fee")
        s["shares_available"] = d.get("shares_available")
        av = d.get("shares_available")
        if av is not None:
            h = s.setdefault("borrow_hist", [])
            if h and h[-1] and h[-1][0] == today_iso:
                h[-1][1] = int(av)               # نفس اليوم → حدّث القيمة
            else:
                h.append([today_iso, int(av)])
            del h[:-14]                          # سقف أسبوعان (لا نموّ بلا حد)
    except Exception:
        pass


def spread_line(bid, ask, session=None, brief=False) -> str:
    """💧 سطر السبريد وتحذير السيولة (🎬 فيصل يبدأ فيديو DSY بدفتر الأوامر — الحالة
    المرئية Bid 2.52 / Ask 3.12 = سبريد ~21%). السبريد نسبةً لمنتصف السعر (صيغة
    الفيديو: 0.60/2.82 = 21.28%، لا نسبةً للعرض). **عرض/تحذير فقط — لا بوابة**
    (اقتراح التقرير بالحظر ليس قول فيصل). العتبة 5% هندسية (نفس N5، لا رقم فيصل
    منطوق). session للوسم بصدق (سبريد خارج الجلسة واسع طبيعيًّا — لقطة الفيديو 21%
    كانت مغلقة). brief=True نسخة مختصرة للتنبيهات اللحظية. '' عند غياب bid/ask أو
    سبريد طبيعي (فاشل-آمن)."""
    try:
        bid, ask = float(bid or 0), float(ask or 0)
        if bid <= 0 or ask <= 0 or ask < bid:
            return ""
        pct = (ask - bid) / ((ask + bid) / 2.0) * 100.0
        if pct < 5.0:
            return ""
        if brief:
            return f"💧 سبريد واسع {pct:.0f}% — سيولة ضعيفة، ادخل بأمر محدّد"
        sess = f" [{session}]" if session else ""
        return (f"💧 سبريد واسع: {pct:.0f}% (طلب ${bid:.2f} / عرض ${ask:.2f}){sess} "
                "— السعر الأخير قد لا يكون قابلًا للتنفيذ؛ ادخل بأوامر محدّدة")
    except Exception:
        return ""


def _sanitize_name(name, max_len: int = 64):
    """⑦ (إصلاح تدقيق 2026-07-12): تعقيم اسم الشركة عند حدّ الدخول — نص حرّ من
    مصدر خارجي (ياهو) يُخزَّن في JSON يقرأه وكيل Cline المستقل (contents: write)؛
    لنموذج لغوي لا يتمايز النص عن التعليمات. محارف محافظة فقط (حروف/أرقام/مسافة/
    `.,&'()-`) + سقف طول. None تمرّ كما هي. نقيّة، فاشلة-آمنة → None."""
    try:
        if not name:
            return None
        clean = "".join(ch if (ch.isalnum() or ch in " .,&'()-") else " "
                        for ch in str(name))
        clean = " ".join(clean.split())[:max_len].strip()
        return clean or None
    except Exception:
        return None


def _short_headline(r: dict) -> str:
    """نص «شورت» في السطر الرئيسي للكرت/اليومي (2026-07-11، طلب المستخدم — عرض فقط).
    يعتمد **عمود Available من ChartExchange** (`shares_available`) = قراءة فيصل للشورت
    الموثّقة (XHLD «شورته 600 ألف طاخ طيخ» · DSY IMG_9509-9510 «7000 سهم متوفر») بدل
    الحجم اليومي المربِك. السلسلة الصادقة: المتاح (CE) → الحجم اليومي (Fintel/FINRA) →
    نسبة من الفلوت → «—». **عرض فقط — لا يمسّ M13** (تبقى على الحجم اليومي: قيد معماري،
    CE يُجلب بعد الاختيار). فاشل-آمن. `shares_available=0` (ELAB) قيمة صحيحة تُعرض."""
    av = r.get("shares_available")
    if av is not None:
        return f"شورت {fmt_money(av)}"
    # احتياط الحجم اليومي: الكرت الحي (fintel/finra_short) أو المخزَّن باليومي (short).
    sv = ((r.get("fintel") or {}).get("short_volume")
          or r.get("finra_short") or r.get("short"))
    if sv is not None:
        return f"شورت {fmt_money(sv)}"
    if r.get("short_pct") is not None:
        return f"شورت {r['short_pct']}% من الفلوت"
    return "شورت —"


def short_interest_line(r: dict) -> str:
    """📊 الشورت الرسمي (SI) + أيام التغطية — من ياهو `.info` (🎬 نفس رقمَي Fintel
    اللذين قرأهما فيصل بفيديو DSY: SI 37,993 · Days to Cover 0.30). **حقلان
    مستقلان — لا يُخلطان بـ`finra_short`** (مقياس مختلف؛ درس التلوّث 2026-06-24:
    sharesShort بالملايين ≠ الحجم اليومي بالآلاف). '' عند غيابهما. عرض/سياق فقط."""
    si = r.get("short_interest")
    dtc = r.get("days_to_cover")
    parts = []
    if si:
        parts.append(f"شورت رسمي {int(si):,} سهم")
    if dtc:
        parts.append(f"تغطية {float(dtc):.2f} يوم")
    return "📊 " + " · ".join(parts) if parts else ""


def borrow_line(r: dict) -> str:
    """سطر «🔒 اقتراض» **مفسَّر ذاتيًّا** بلغة مبتدئ — **على إطار فيصل الموثّق فقط**
    (⚖️ تصحيح 2026-07-10 بعد تشكيك المستخدم «متأكد من معلومة الوقود؟»: سردية
    «الرسوم العالية تجبر الشورت يغطّي فيتسارع الصعود» كانت سردية سوق عامة غير
    موثّقة من فيصل — **أُزيلت**). إطار فيصل الموثّق يدور حول **المتاح للاقتراض**:
      • متاح ضخم (فوق حد الشورت 40 ألف) = «حرب وتصريف» — الشورت الضخم يحارب أي
        صعود ويصرّف فيه، مستحيل يرتفع بسببه (XHLD IMG_9504: «طاخ طيخ الى الهاويه»).
      • متاح صفر = شرط حالة السكويز الوحيدة الموثّقة (ELAB IMG_6475: «**لا يوجد
        أسهم متاحة للشورت** · تدوير 750% · التدوير من الشورت»).
      • صفر/قليل شورت مطلبه للارتكاز أصلًا (TRUG «صفر شورت» · LNAI · MBRX).
      • **الرسوم العالية = إيجابي عند فيصل حرفيًّا** (DSY IMG_9510: «نسبة الاقتراض
        725% عاليه جدا للشورت = اجابي» — مع 7 آلاف متاح فقط؛ تأكيد المستخدم
        «معلوماتك صحيحة وهذا تاكيد من فيصل») — تصعّب دخول شورت جديد للحرب،
        والرخيصة تفتح بابها. **الحكم مركّب دائمًا مع المتاح** (XHLD عكسها بمتاح
        ضخم). (درجات صعب/متوسط/سهل وصف واقعي للرسوم؛ العتبتان 20/5 هندسيتان.)
    «—» عند التعذّر (تعذّر ≠ صفر). عرض/سياق فقط — لا بوابة ولا ترتيب."""
    fee = r.get("borrow_fee")
    avail = r.get("shares_available")
    if fee is None and avail is None:
        return "🔒 اقتراض: —"
    if avail == 0:
        # فيصل ELAB (IMG_6475): «لا يوجد أسهم متاحة للشورت» = شرط حالة السكويز
        av_txt = "لا أسهم متاحة للشورت أصلًا (فيصل ELAB: شرط حالة السكويز)"
    elif avail is not None and avail <= CONFIG["SHORT_GATE_MAX"]:
        av_txt = (f"متاح للشورت {fmt_money(avail)} سهم "
                  "(قليل — تحت حد فيصل 40 ألف)")
    elif avail is not None:
        av_txt = f"متاح للشورت {fmt_money(avail)} سهم"
    else:
        av_txt = ""
    # ⚠️ قراءة فيصل المركّبة (IMG_9504، XHLD: «سهم شورته 600 الف يصعد؟ طاخ طيخ الى
    # الهاويه» — رقمه = «المتاح» من نفس صفحة CE، وكان 600 ألف برسوم 23%): متاح ضخم
    # = ذخيرة شورت تهبط السهم حتى مع رسوم عالية — الرسوم وقود سكويز فقط لو المتاح
    # قليل. العتبة = حد فيصل الموثّق (SHORT_GATE_MAX=40 ألف · 600 ألف = مثال الهاوية).
    # ⚠️ دقة (تصحيح المستخدم 2026-07-10): XHLD **سهم خبر انضخّ، ليس ارتكازًا** —
    # فيصل علّم القاعدة عليه، فهي قاعدة عامة على المتاح الضخم لا حكمًا على مرشّح ارتكاز.
    if avail is not None and avail > CONFIG["SHORT_GATE_MAX"]:
        fee_txt = f" مع رسوم {fee:.0f}%" if fee is not None else ""
        # مسار التضخّم من borrow_hist (IMG_9505: 30 ألف→600 ألف في 3 أيام) —
        # يُعرض فقط لو التاريخ يثبت نموًّا حقيقيًّا عبر أيام.
        traj = ""
        try:
            h = r.get("borrow_hist") or []
            if len(h) >= 2 and h[0][1] and avail > h[0][1]:
                days = (dt.date.fromisoformat(h[-1][0])
                        - dt.date.fromisoformat(h[0][0])).days
                if days >= 1:
                    traj = (f" — كان {fmt_money(h[0][1])} قبل {days} "
                            "يوم (يتضخّم)")
        except Exception:
            traj = ""
        # «طاخ طيخ» بمعناه الصحيح (توضيح المستخدم 2026-07-10): حرب وتصريف —
        # الشورت الضخم يحارب أي صعود ويصرّف فيه فيستحيل الارتفاع بسببه.
        return ("🔒 اقتراض: ⚠️ متاح للشورت ضخم "
                f"({fmt_money(avail)} سهم — فوق حد فيصل "
                f"{CONFIG['SHORT_GATE_MAX'] // 1000} ألف){fee_txt}{traj} — "
                "حرب وتصريف: الشورت الضخم يحارب أي صعود ويصرّف فيه، "
                "مستحيل يرتفع بسببه (فيصل: طاخ طيخ إلى الهاوية)")
    if fee is None:
        return f"🔒 اقتراض: {av_txt} (الرسوم غير معروفة)"
    # الرسوم العالية = **إيجابي عند فيصل حرفيًّا** (DSY IMG_9510: «نسبة الاقتراض
    # 725% عاليه جدا للشورت = اجابي» مع 7 آلاف متاح فقط) — تصعّب دخول شورت جديد
    # للحرب. الحكم مركّب مع المتاح: الفرع الضخم أعلاه يعترض قبل الوصول هنا،
    # فالوصول هنا = المتاح قليل (إيجابي مؤكَّد) أو غير معروف (حكم ناقص، يُصرَّح).
    if fee >= CONFIG["BORROW_HIGH_PCT"]:
        if avail is not None:
            body = (f"صعب 🔥 (رسوم {fee:.0f}% سنويًّا على من يشورته) = إيجابي "
                    "— يصعّب دخول شورت جديد للحرب (فيصل: «عاليه جدا للشورت "
                    "= اجابي» — DSY رسوم 725% ومتاح 7 آلاف فقط)")
        else:
            body = (f"صعب 🔥 (رسوم {fee:.0f}% سنويًّا على من يشورته) — يصعّب "
                    "دخول شورت جديد؛ الحكم الكامل يحتاج «المتاح» (غير معروف)")
    elif fee >= CONFIG["BORROW_MID_PCT"]:
        body = f"متوسط (رسوم {fee:.0f}% سنويًّا على من يشورته)"
    else:
        body = (f"سهل ورخيص (رسوم {fee:.0f}%) — "
                "باب دخول شورت جديد للحرب عليه مفتوح ورخيص")
    return "🔒 اقتراض: " + body + (f" · {av_txt}" if av_txt else "")


# ==========================================================
# 📅 الأحداث المعلنة القادمة (طلب المستخدم 2026-07-09: «تواريخ الإعلانات المعلنة
# مسبقًا — غالبًا يوم الانفجار اللي ينتظره المضارب»؛ فيصل صورة 9428: «المضارب قبل
# صدور اعلان للشركه يهيئ السهم فنيا للصعود»). أرباح (كل الأسهم) + اكتمال التجارب
# السريرية (الرعاية الصحية، من السجل الرسمي ClinicalTrials.gov). **عرض/سياق فقط —
# خارج الفرز/الترتيب.** فاشل-آمن مطلق. ⚠️ حدود صدق: مواعيد قرارات FDA (PDUFA)
# والمؤتمرات لا API مجاني موثوق لها — غير مشمولة؛ وتاريخ اكتمال التجربة تقدير
# معلن بالسجل (الإعلان الرسمي للنتيجة عادة بعده).
# ==========================================================
def next_earnings(sym: str):
    """📅 أقرب تاريخ أرباح معلن (ISO أو None) — يعيد استخدام مصادر أداة الأرباح
    (`technical_report`: Alpha Vantage→FMP→Finnhub→yfinance؛ المفاتيح اختيارية
    وكلها فاشلة-آمنة). استيراد كسول لتفادي الاستيراد الدائري. عرض فقط."""
    try:
        import technical_report as _tr
        d = _tr._next_earnings_date(sym)
        return d.isoformat() if d else None
    except Exception:
        return None


def _parse_ct_studies(data, company, today, horizon_days):
    """نقيّة (بلا شبكة): من ردّ ClinicalTrials.gov v2 تستخرج التجارب التي راعيها
    الرئيسي يطابق اسم الشركة وتاريخ اكتمالها (الأولي أو الكلي) قادم ضمن الأفق.
    صيغة «سنة-شهر» فقط → أول الشهر (تقدير). ترجع [{'kind','date','note'}...]
    مرتّبة بالأقرب (بحدّ 2). فاشلة-آمنة → []."""
    out = []
    try:
        base = (company or "").strip().lower().split()
        base = base[0] if base else ""
        for st in (data.get("studies") or []):
            try:
                proto = st.get("protocolSection") or {}
                spons = (((proto.get("sponsorCollaboratorsModule") or {})
                          .get("leadSponsor") or {}).get("name") or "")
                if not base or base not in spons.lower():
                    continue                    # حارس المطابقة (لا ننسب تجربة لغير شركتها)
                stat = proto.get("statusModule") or {}
                d = ((stat.get("primaryCompletionDateStruct") or {}).get("date")
                     or (stat.get("completionDateStruct") or {}).get("date"))
                if not d:
                    continue
                iso = d if len(str(d)) >= 10 else f"{d}-01"
                dd = dt.date.fromisoformat(str(iso)[:10])
                days = (dd - today).days
                if days < 0 or days > horizon_days:
                    continue
                phases = (proto.get("designModule") or {}).get("phases") or []
                ph = str(phases[0]).replace("PHASE", "المرحلة ").strip() \
                    if phases else ""
                nct = ((proto.get("identificationModule") or {})
                       .get("nctId") or "")
                note = " · ".join(x for x in (ph, nct) if x)
                out.append({"kind": "تجربة", "date": dd.isoformat(),
                            "note": note})
            except Exception:
                continue
        out.sort(key=lambda e: e["date"])
    except Exception:
        return []
    return out[:2]


def clinical_events(company: str) -> list:
    """📅 تجارب سريرية تكتمل قريبًا لشركة (ClinicalTrials.gov v2 — رسمي مجاني بلا
    مفتاح). فاشل-آمن مطلق → [] (شبكة/شكل/حجب). عرض فقط — خارج الفرز."""
    try:
        if not company:
            return []
        r = requests.get(
            "https://clinicaltrials.gov/api/v2/studies",
            params={"query.spons": company, "pageSize": 30,
                    "filter.overallStatus":
                        "RECRUITING,ACTIVE_NOT_RECRUITING,"
                        "ENROLLING_BY_INVITATION,NOT_YET_RECRUITING"},
            timeout=10)
        if r.status_code != 200:
            return []
        return _parse_ct_studies(r.json() or {}, company, dt.date.today(),
                                 CONFIG["EVENTS_SHOW_DAYS"])
    except Exception:
        return []


def upcoming_events(sym: str, company: str = None, sector: str = None,
                    proxy: dict = None, first_trade: str = None):
    """📅 يجمع الأحداث المعلنة القادمة للسهم: أرباح (دائمًا) + اكتمال تجارب سريرية
    (قطاع الرعاية الصحية فقط — يوفّر النداءات) + دعوة اجتماع مساهمين (`proxy` من
    قناة SEC — غالبًا تصويت تقسيم/زيادة أسهم) + انتهاء حظر بيع المؤسسين التقديري
    (`first_trade` + LOCKUP_DAYS للإدراجات الحديثة). يرجع قائمة مرتّبة بالأقرب أو
    None. فاشل-آمن. عرض/سياق فقط — لا يدخل أي فرز/ترتيب/بوابة."""
    ev = []
    try:
        ne = next_earnings(sym)
        if ne:
            ev.append({"kind": "أرباح", "date": ne, "note": ""})
    except Exception:
        pass
    try:
        if company and (sector or "") == "Healthcare":
            ev += clinical_events(company)
    except Exception:
        pass
    try:
        if proxy and proxy.get("date"):
            ev.append({"kind": "اجتماع", "date": str(proxy["date"])[:10],
                       "note": proxy.get("form") or ""})
    except Exception:
        pass
    try:
        if first_trade:
            _est = (dt.date.fromisoformat(str(first_trade)[:10])
                    + dt.timedelta(days=int(CONFIG["LOCKUP_DAYS"])))
            _d = (_est - dt.date.today()).days
            if 0 <= _d <= CONFIG["EVENTS_SHOW_DAYS"]:
                ev.append({"kind": "حظر", "date": _est.isoformat(),
                           "note": "تقدير من تاريخ الإدراج"})
    except Exception:
        pass
    ev = [e for e in ev if e.get("date")]
    ev.sort(key=lambda e: e["date"])
    return ev or None


def events_lines(events, today=None) -> list:
    """📅 أسطر «الأحداث المعلنة» للكرت/اليومي (نقيّة): تُخفي الماضي والأبعد من
    الأفق · «اليوم!»/«غدًا» للقريب · بحدّ 3 أسطر (لا حشو). أنواعها: أرباح · تجربة
    سريرية · اجتماع مساهمين (تاريخه = تاريخ الدعوة الماضي، يظهر ما دامت الدعوة
    ضمن PROXY_LOOKBACK_DAYS لأن الاجتماع بعدها بشهر-شهرين) · حظر مؤسسين (تقديري).
    لغة مبتدئ بلا رموز مقارنة. ترجع [] عند لا شيء. عرض فقط."""
    out = []
    try:
        t = today or dt.date.today()
        for e in (events or []):
            d = dt.date.fromisoformat(str(e.get("date"))[:10])
            if e.get("kind") == "اجتماع":
                _behind = (t - d).days           # كم مضى على تقديم الدعوة
                if _behind < 0 or _behind > CONFIG["PROXY_LOOKBACK_DAYS"]:
                    continue
                _frm = f" (دعوة {esc(e['note'])})" if e.get("note") else ""  # 14أ
                out.append(f"📅 اجتماع مساهمين قادم{_frm}: الدعوة قُدّمت "
                           f"{d.isoformat()} — يُعقد عادة خلال شهر إلى شهرين؛ "
                           "راقب بنود التقسيم العكسي/زيادة الأسهم")
                continue
            days = (d - t).days
            if days < 0 or days > CONFIG["EVENTS_SHOW_DAYS"]:
                continue
            when = ("اليوم!" if days == 0 else
                    ("غدًا" if days == 1 else f"بعد {days} يوم"))
            if e.get("kind") == "أرباح":
                out.append(f"📅 أرباح معلنة: {d.isoformat()} ({when}) — "
                           "يوم انفجار محتمل (المضارب يجهّز قبل الإعلان)")
            elif e.get("kind") == "حظر":
                out.append(f"📅 انتهاء حظر بيع المؤسسين (تقديري): {d.isoformat()} "
                           f"({when}) — نحو {int(CONFIG['LOCKUP_DAYS'])} يومًا من "
                           "الإدراج؛ قد يفكّ أسهمًا للبيع (العقد قد يختلف)")
            else:
                note = f" ({esc(e['note'])})" if e.get("note") else ""  # 14أ
                out.append(f"📅 اكتمال تجربة سريرية{note}: {d.isoformat()} "
                           f"({when}) — موعد تقديري معلن قد يتغيّر")
    except Exception:
        return []
    return out[:3]


def fintel_short(symbols: list) -> dict:
    """محاولة أولى صامتة من fintel.io (الأدق عند نجاحها).
    Cloudflare غالباً يحجب الطلبات الآلية — عند الفشل نرجع {}
    بصمت ويتولى FINRA ثم Yahoo المهمة."""
    out = {}
    for sym in symbols:
        try:
            r = requests.get(f"https://fintel.io/ss/us/{sym.lower()}",
                             headers=BROWSER_UA, timeout=25)
            if r.status_code != 200:
                continue
            html = r.text
            d = {}
            m = re.search(r"Short\s*Interest\s*%?\s*(?:of\s*)?Float"
                          r"[^0-9%]{0,80}?([\d.]+)\s*%", html, re.I | re.S)
            if m:
                d["si_pct_float"] = float(m.group(1))
            m2 = re.search(r"Short\s*Volume[^0-9]{0,80}?([\d,]{3,})",
                           html, re.I | re.S)
            if m2:
                d["short_volume"] = int(m2.group(1).replace(",", ""))
            d.update(_parse_fintel_borrow(html))   # 🔒 اقتراض (نفس الطلب — بلا نداء إضافي)
            if d:
                out[sym] = d
        except Exception:
            pass
        time.sleep(1.5)  # احترام الموقع
    if out:
        log(f"fintel: بيانات لـ {len(out)}/{len(symbols)} رمز")
    else:
        log("fintel: محجوب/لا بيانات — FINRA وYahoo يتوليان المهمة")
    return out


# ---- إعلانات SEC EDGAR الرسمية ----
_SEC_CIK_CACHE = None


def sec_cik_map() -> dict:
    """خريطة رمز→CIK الرسمية من SEC (هوية مضمونة 100% للشركة الأمريكية)"""
    global _SEC_CIK_CACHE
    if _SEC_CIK_CACHE is not None:
        return _SEC_CIK_CACHE
    try:
        r = requests.get("https://www.sec.gov/files/company_tickers.json",
                         headers=SEC_UA, timeout=40)
        r.raise_for_status()
        data = r.json()
        _SEC_CIK_CACHE = {v["ticker"].upper(): int(v["cik_str"])
                          for v in data.values()}
        log(f"خريطة SEC: {len(_SEC_CIK_CACHE)} رمز")
    except Exception as e:
        log(f"⚠️ خريطة SEC: {e}")
        _SEC_CIK_CACHE = {}
    return _SEC_CIK_CACHE


# تصنيف بنود 8-K: (إيموجي، وصف عربي)
SEC_8K_ITEMS = {
    "1.01": ("🟢", "اتفاقية جوهرية"),
    "1.02": ("🔴", "إنهاء اتفاقية"),
    "1.03": ("🔴", "إفلاس/إعسار"),
    "2.01": ("🟢", "إتمام استحواذ/بيع أصول"),
    "2.02": ("🟡", "نتائج مالية"),
    "2.03": ("🟡", "التزام مالي مباشر"),
    "2.05": ("🔴", "تكاليف خروج/إعادة هيكلة"),
    "2.06": ("🔴", "انخفاض قيمة أصول"),
    "3.01": ("🔴", "إشعار شطب/مخالفة شروط الإدراج"),
    "3.02": ("🔴", "بيع أسهم غير مسجلة (تخفيف)"),
    "3.03": ("🟡", "تعديل حقوق حملة الأسهم"),
    "4.01": ("🔴", "تغيير مدقق الحسابات"),
    "4.02": ("🔴", "عدم الاعتماد على قوائم مالية سابقة"),
    "5.01": ("🟡", "تغيير في السيطرة"),
    "5.02": ("🟡", "تغييرات إدارية/مجلس الإدارة"),
    "5.03": ("🟡", "تعديل النظام الأساسي (تقسيم عكسي محتمل)"),
    "5.07": ("⚪", "نتائج تصويت المساهمين"),
    "7.01": ("⚪", "إفصاح تنظيمي FD"),
    "8.01": ("🟡", "أحداث أخرى مهمة"),
    "9.01": ("⚪", "قوائم ومرفقات"),
}

# تصنيف نماذج أخرى مهمة (غير 8-K)
SEC_FORM_CLASS = {
    "424B5": ("🔴", "نشرة طرح أسهم (تخفيف)"),
    "424B4": ("🔴", "نشرة طرح (تخفيف)"),
    "424B3": ("🟡", "نشرة/تحديث طرح"),
    "S-1": ("🔴", "تسجيل طرح جديد"),
    "S-1/A": ("🔴", "تعديل تسجيل طرح"),
    "S-3": ("🔴", "تسجيل طرح رفّي"),
    "S-3/A": ("🔴", "تعديل تسجيل رفّي"),
    "EFFECT": ("🔴", "تفعيل تسجيل طرح"),
    "25": ("🔴", "شطب من الإدراج"),
    "25-NSE": ("🔴", "بدء إجراءات شطب"),
    "NT 10-K": ("🔴", "تأخر التقرير السنوي"),
    "NT 10-Q": ("🔴", "تأخر التقرير الربعي"),
    # 📅 دعوات اجتماع المساهمين (وكالة): غالبًا تصويت تقسيم عكسي/زيادة أسهم لأسهم
    # الارتكاز — تُلتقط أيضًا كحدث قادم (قناة _SEC_PROXY → upcoming_events)
    "DEF 14A": ("🟡", "دعوة اجتماع مساهمين (راقب بنود تقسيم/طرح)"),
    "PRE 14A": ("🟡", "دعوة اجتماع مساهمين مبدئية"),
    "DEF 14C": ("🟡", "إشعار قرار مساهمين (بلا تصويت)"),
}

# 📅 قناة جانبية: آخر دعوة اجتماع مساهمين لكل رمز (نمط _REJECT_STATS) — تُلتقط في
# sec_recent_filings بنافذة أطول من نافذة العرض وتُستهلك في enrich → upcoming_events
_SEC_PROXY = {}
_PROXY_FORMS = ("DEF 14A", "DEFA14A", "DEFR14A", "PRE 14A", "PRER14A",
                "DEF 14C", "PRE 14C")

_RANK = {"🔴": 0, "🟢": 1, "🟡": 2, "⚪": 3}


def classify_8k_items(items_str: str):
    """يحوّل سلسلة بنود 8-K إلى أهم بند مصنّف (أحمر ثم أخضر ثم أصفر)"""
    codes = [x.strip() for x in (items_str or "").split(",") if x.strip()]
    parsed = []
    for cd in codes:
        emoji, label = SEC_8K_ITEMS.get(cd, ("⚪", f"بند {cd}"))
        parsed.append((emoji, label, cd))
    meaningful = [p for p in parsed if p[0] != "⚪"]
    if not meaningful:
        return None
    meaningful.sort(key=lambda x: _RANK.get(x[0], 9))
    emoji, label, cd = meaningful[0]
    extra = f" (+{len(meaningful) - 1} بنود)" if len(meaningful) > 1 else ""
    return f"{emoji} 8-K بند {cd}: {label}{extra}"


def sec_recent_filings(sym: str):
    """إعلانات SEC الرسمية لآخر N يوم، مصنّفة 🟢/🔴/🟡.
    يرجع (قائمة سطور، حالة: ok / no_cik / error)"""
    out = []
    cik = sec_cik_map().get(sym.upper())
    if not cik:
        return out, "no_cik"
    try:
        url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
        r = requests.get(url, headers=SEC_UA, timeout=40)
        r.raise_for_status()
        recent = ((r.json().get("filings") or {}).get("recent")) or {}
        forms = recent.get("form", []) or []
        dates = recent.get("filingDate", []) or []
        items_l = recent.get("items", []) or []
        cutoff = (dt.date.today()
                  - dt.timedelta(days=CONFIG["SEC_FILING_DAYS"])).isoformat()
        # 📅 نافذة أطول لالتقاط دعوة اجتماع المساهمين (الاجتماع يُعقد عادة بعد
        # شهر-شهرين من الدعوة، فنافذة العرض القصيرة تفوّته) — التقاط فقط، لا عرض.
        pcut = (dt.date.today()
                - dt.timedelta(days=CONFIG["PROXY_LOOKBACK_DAYS"])).isoformat()
        full = False
        for i in range(len(forms)):
            fdate = dates[i] if i < len(dates) else ""
            if fdate < pcut:
                break  # القائمة مرتبة من الأحدث للأقدم
            form = (forms[i] or "").strip()
            if form in _PROXY_FORMS and sym.upper() not in _SEC_PROXY:
                _SEC_PROXY[sym.upper()] = {"form": form, "date": fdate}
            if fdate < cutoff or full:
                continue           # خارج نافذة العرض — نكمل لالتقاط الوكالة فقط
            line = None
            if form.startswith("8-K"):
                cls = classify_8k_items(items_l[i] if i < len(items_l) else "")
                if cls:
                    line = f"{cls} — {fdate}"
            else:
                fc = SEC_FORM_CLASS.get(form)
                if fc:
                    line = f"{fc[0]} {form}: {fc[1]} — {fdate}"
            if line:
                out.append(line)
            if len(out) >= CONFIG["SEC_MAX_SHOW"]:
                full = True
        return out, "ok"
    except Exception as e:
        log(f"⚠️ SEC {sym}: {e}")
        return out, "error"


def parse_yahoo_news(items, max_items: int, days: int) -> list:
    """يحوّل قائمة أخبار yfinance إلى عناوين نظيفة (آخر N يوم).
    يدعم البنيتين القديمة والجديدة لـ yfinance، ويرجع [] بلا أخطاء
    لو تغيّرت البنية أو لا توجد أخبار (Yahoo مصدر مجاني عبر yfinance)."""
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    out = []
    for it in (items or []):
        try:
            if not isinstance(it, dict):
                continue
            title = pub = link = None
            when = None
            # البنية الجديدة: كل الحقول داخل "content"
            if isinstance(it.get("content"), dict):
                c = it["content"]
                title = c.get("title")
                pub = (c.get("provider") or {}).get("displayName")
                cu = c.get("canonicalUrl") or c.get("clickThroughUrl") or {}
                link = cu.get("url") if isinstance(cu, dict) else None
                raw = c.get("pubDate") or c.get("displayTime")
                if raw:
                    try:
                        when = dt.datetime.fromisoformat(
                            str(raw).replace("Z", "+00:00"))
                    except Exception:
                        when = None
            # البنية القديمة: الحقول في الجذر مباشرة
            else:
                title = it.get("title")
                pub = it.get("publisher")
                link = it.get("link")
                ts = it.get("providerPublishTime")
                if ts:
                    try:
                        when = dt.datetime.fromtimestamp(
                            int(ts), dt.timezone.utc)
                    except Exception:
                        when = None
            if not title:
                continue
            if when is not None and when < cutoff:
                continue
            out.append({
                "title": str(title).strip(),
                "publisher": (pub or "").strip(),
                "link": (link or "").strip(),
                "date": when.date().isoformat() if when else "",
            })
            if len(out) >= max_items:
                break
        except Exception:
            continue
    return out


# ---- كشف أخبار الخطر تلقائياً (للبوت، لا يعتمد على المستخدم): يمسح عناوين
#      ياهو عن الطرح/التخفيف/التقسيم العكسي/الشطب → تحذير صريح في البطاقة.
#      الأنماط من الأخص للأعم (نأخذ أول تطابق لكل عنوان لتفادي التكرار). ----
NEWS_RISK_PATTERNS = [
    ("registered direct",    "طرح مباشر مسجّل (تخفيف)"),
    ("private placement",    "اكتتاب خاص (تخفيف)"),
    ("at-the-market",        "طرح ATM (تخفيف)"),
    ("at the market",        "طرح ATM (تخفيف)"),
    ("shelf offering",       "طرح رفّي (تخفيف)"),
    ("public offering",      "طرح عام (تخفيف)"),
    ("underwritten",         "طرح مكتتب (تخفيف)"),
    ("proposed offering",    "طرح مقترح (تخفيف)"),
    ("common stock offering", "طرح أسهم (تخفيف)"),
    ("convertible note",     "سند قابل للتحويل (تخفيف)"),
    ("convertible debenture", "سند قابل للتحويل (تخفيف)"),
    ("offering",             "طرح/تخفيف"),
    ("dilut",                "تخفيف (dilution)"),
    ("reverse stock split",  "تقسيم عكسي"),
    ("reverse split",        "تقسيم عكسي"),
    ("going concern",        "شك في الاستمرارية"),
    ("chapter 11",           "إفلاس (Chapter 11)"),
    ("bankrupt",             "إفلاس"),
    ("delist",               "خطر الشطب"),
]


def scan_news_risk(news) -> list:
    """يمسح عناوين الأخبار (Yahoo) عن إشارات الطرح/التخفيف/الخطر ويرجع
    تحذيراً عربياً واحداً مجمّعاً (أو [] لو لا خطر). يخدم البوت تلقائياً
    حتى قبل أن يصل الملف الرسمي لمرصد SEC."""
    labels = []
    for it in (news or []):
        low = (it.get("title") or "").lower()
        if not low:
            continue
        hit = None
        for kw, lbl in NEWS_RISK_PATTERNS:
            if kw in low:
                hit = lbl
                break
        # نمط "files to sell N units/shares" (مثل خبر EHGO) بلا كلمة offering
        if hit is None and "to sell" in low and (
                "unit" in low or "share" in low):
            hit = "طرح/تخفيف"
        if hit and hit not in labels:
            labels.append(hit)
    if labels:
        return [f"📰 خبر محتمل بالتخفيف/الخطر (Yahoo): "
                f"{' · '.join(labels)} — تحقّق"]
    return []


def _fetch_info(t):
    """جلب معلومات الشركة من Yahoo مع إعادة محاولة (info يُخنق كثيرًا)."""
    attempts = CONFIG.get("DOWNLOAD_RETRIES", 3)
    base = CONFIG.get("RETRY_BACKOFF", 3.0)
    last = {}
    for i in range(attempts):
        try:
            info = t.info or {}
            # نعتبرها ناجحة لو رجّعت حقولًا مفيدة (وإلا غالبًا خُنقت)
            if info.get("sector") or info.get("country") or \
                    info.get("floatShares") or info.get("longBusinessSummary"):
                return info
            if info and not last:
                last = info        # رد جزئي — نحتفظ به ونعيد المحاولة
        except Exception:
            pass
        if i < attempts - 1:
            time.sleep(base * (2 ** i))
    return last                    # أفضل رد جزئي توفّر بدل {} (كان يرمي الجزئي فتختفي البيانات)


def enrich(results: list) -> None:
    """إثراء المرشحين: شورت (Fintel→FINRA→Yahoo) + SEC + تقسيمات + أخبار"""
    syms = {r["symbol"] for r in results}
    # 🔬 التجميع الصامت أُزيل من الإثراء (2026-07-09): تجربة T-ACC فشلت بالسنتين
    # (غير مميِّز للمنفجر) فتقاعد عرضه من الكرت/اليومي/فحص اليد — لا نستهلك نداءات
    # Polygon لإشارة غير مُجدية. الدوال النقيّة + acc_verify.py محفوظة لإعادة الاختبار.
    _bor_budget = [0]        # 🔒 سقف طلبات احتياط الاقتراض/الفلوت من CE+iBorrow (فاشل-آمن)
    _ce_fails = [0]          # قاطع دائرة اقتراض ChartExchange: يتوقف بعد 3 إخفاقات
    _bor_fails = [0]         # قاطع دائرة iBorrowDesk: يتوقف بعد 3 إخفاقات متتالية
    _flt_fails = [0]         # 🏢 قاطع دائرة فلوت ChartExchange: يتوقف بعد 3 إخفاقات
    fintel = {}
    try:
        fintel = fintel_short(sorted(syms))
    except Exception as e:
        log(f"⚠️ fintel: {e}")
    shorts = {}
    try:
        shorts = finra_daily_short(syms)
    except Exception as e:
        log(f"⚠️ FINRA: {e}")
    sec_cik_map()  # تحميل الخريطة مرة واحدة
    for r in results:
        r["fintel"] = fintel.get(r["symbol"]) or {}
        r["finra_short"] = shorts.get(r["symbol"])
        # سلسلة fintel→FINRA الموثّقة للقيمة المخزّنة (Yahoo يُضاف داخل كتلة .info)
        if r["finra_short"] is None:
            r["finra_short"] = r["fintel"].get("short_volume")
        # 🔒 معدّل الاقتراض (طلب المستخدم — فيصل: أساس الارتكاز):
        # ⚖️ **ChartExchange = المرجع الأول صراحةً** (قرار المستخدم 2026-07-10 «نعتمد
        # الموقع مرجعنا الأول» — مصدر فيصل نفسه، IBKR مباشر كل 15د). السلسلة:
        # **ChartExchange ← Fintel (احتياط، من طلب الشورت بلا نداء) ← iBorrowDesk**.
        # نبدأ بـNone ونملؤها بالأولوية. سقف نداءات مشترك + قاطع دائرة مستقل لكل مصدر.
        r["borrow_fee"] = None
        r["shares_available"] = None
        if _bor_budget[0] < 25 and _ce_fails[0] < 3:      # 1) CE أولًا (المرجع الأول)
            _bor_budget[0] += 1
            try:
                _ce = ce_borrow_info(r["symbol"])
            except Exception:
                _ce = {}
            if _ce:
                _ce_fails[0] = 0                           # نجاح → صفّر القاطع
                r["borrow_fee"] = _ce.get("borrow_fee")
                r["shares_available"] = _ce.get("shares_available")
            else:
                _ce_fails[0] += 1                          # إخفاق متتالٍ → قاطع بعد 3
        if r["borrow_fee"] is None and r["shares_available"] is None:
            # 2) Fintel احتياطًا (مُلتقط مجّانًا من طلب الشورت أعلاه)
            r["borrow_fee"] = r["fintel"].get("borrow_fee")
            r["shares_available"] = r["fintel"].get("shares_available")
        if (r["borrow_fee"] is None and r["shares_available"] is None
                and _bor_budget[0] < 25 and _bor_fails[0] < 3):
            _bor_budget[0] += 1
            try:
                _ib = iborrow_info(r["symbol"])
            except Exception:
                _ib = {}
            if _ib:
                _bor_fails[0] = 0                          # نجاح → صفّر القاطع
                r["borrow_fee"] = _ib.get("borrow_fee")
                r["shares_available"] = _ib.get("shares_available")
            else:
                _bor_fails[0] += 1                         # إخفاق متتالٍ (قد تكون الخدمة منقطعة)
        # نلتقط قيمة بوابة الفلوت/الشورت المجلوبة في scan_market كاحتياط أخير قبل
        # التصفير وإعادة الجلب (لا تضيع لو خُنق .info — إصلاح فحص 2026-06-24).
        _prev_float = r.get("float")
        _prev_short_pct = r.get("short_pct")
        r["short_pct"] = None
        r["float"] = None
        r["recent_split"] = None
        r["news"] = []
        r["tf4h"] = "غير متوفر"
        # إعلانات SEC الرسمية (هوية مضمونة بالـCIK)
        r["sec_filings"], r["sec_status"] = sec_recent_filings(r["symbol"])
        # 📅 دعوة اجتماع مساهمين (قناة _SEC_PROXY من النداء أعلاه — حدث قادم)
        r["proxy_filing"] = _SEC_PROXY.pop(r["symbol"].upper(), None)
        time.sleep(0.15)  # احترام حد SEC (10 طلبات/ثانية)
        if yf is None:
            continue
        try:
            t = yf.Ticker(r["symbol"])
            try:
                info = _fetch_info(t)                 # مع إعادة محاولة
                sym = r["symbol"]
                cached = COMPANY_CACHE.get(sym, {})    # آخر قيم معروفة
                sp = info.get("shortPercentOfFloat")
                r["short_pct"] = (round(sp * 100, 1) if sp
                                  else cached.get("short_pct") or _prev_short_pct)
                # عدد الشورت (حجم يومي): لو غاب عن FINRA/Fintel استرجع آخر قيمة
                # معروفة من الذاكرة — نفس المقياس بالضبط (لا نخلط بفائدة شورت
                # Yahoo «sharesShort» بالملايين؛ بديل Yahoo يُعرَض كنسبة من الفلوت
                # عبر short_pct). تغطية ثابتة بلا تلوّث مقياس.
                if r.get("finra_short") is None:
                    r["finra_short"] = cached.get("finra_short")
                # 📊 الشورت الرسمي (SI) + أيام التغطية (🎬 فيصل قرأهما بفيديو DSY من
                # Fintel: 37,993 · 0.30). حقلان مستقلان بمقياسهما — **لا يُخلطان
                # بfinra_short** (الحجم اليومي). عرض/سياق فقط — خارج M13/الفرز.
                r["short_interest"] = _or_cache(info.get("sharesShort"),
                                                cached, "short_interest")
                r["days_to_cover"] = _or_cache(info.get("shortRatio"),
                                               cached, "days_to_cover")
                # القيمة المجلوبة إن وُجدت، وإلا آخر قيمة معروفة (لا يختفي 🏢)
                r["float"] = (_or_cache(info.get("floatShares"), cached, "float")
                              or _prev_float)
                # 🏢 احتياط ChartExchange للفلوت (اقتراح المستخدم 2026-07-10: «كثير
                # أسهم يجيني الفلوت مجهول» — ياهو مخنوق). آخر ملاذ لو غاب من ياهو
                # والذاكرة. **عرض فقط: بعد select_top، وM14 مرّت أثناء الفرز فلا
                # تتأثر إطلاقًا.** بودجت + قاطع دائرة مستقل، فاشل-آمن.
                if (r["float"] is None
                        and _bor_budget[0] < 25 and _flt_fails[0] < 3):
                    _bor_budget[0] += 1
                    try:
                        _cf = ce_float_info(sym)
                    except Exception:
                        _cf = None
                    if _cf:
                        _flt_fails[0] = 0
                        r["float"] = _cf
                    else:
                        _flt_fails[0] += 1
                # D10: تدوير الفلوت (حجم اليوم ÷ الفلوت) — إشارة سكويز عند تجاوز
                # 100% (فيصل ELAB: تدوير 750%). عرض فقط — لا نقاط ولا بوابة.
                _flt, _vt = r.get("float"), r.get("vol_today")
                if _flt and _vt:
                    r["rotation_pct"] = round(_vt / _flt * 100.0)
                r["sector"] = _or_cache(info.get("sector") or
                                        info.get("industry"), cached, "sector")
                r["industry"] = _or_cache(info.get("industry"),
                                          cached, "industry")
                # 📅 اسم الشركة (لمطابقة راعي التجارب السريرية — الأحداث المعلنة)
                # ⑦ (إصلاح تدقيق 2026-07-12): تعقيم عند الحد — نص حرّ من مصدر
                # خارجي يُكوَّت في weekly_watchlist.json الذي يقرأه وكيل Cline
                # (contents: write). محارف محافظة + سقف طول، فلا يحمل الحقلُ
                # تعليماتٍ لنموذج لغوي ولا وسومًا.
                r["company_name"] = _sanitize_name(info.get("shortName")
                                                   or info.get("longName")
                                                   or cached.get("company_name"))
                # 📅 تاريخ أول تداول (لتقدير انتهاء حظر المؤسسين للإدراجات الحديثة)
                try:
                    _ftd = info.get("firstTradeDateEpochUtc")
                    if _ftd:
                        r["first_trade"] = dt.datetime.fromtimestamp(
                            int(_ftd), dt.timezone.utc).date().isoformat()
                except Exception:
                    pass
                if not r.get("first_trade"):
                    r["first_trade"] = cached.get("first_trade")
                summ = info.get("longBusinessSummary") or ""
                r["business"] = ((summ[:160].strip() + "…") if summ
                                 else cached.get("business"))
                r["country"] = _or_cache(info.get("country"), cached, "country")
                r["cash"] = _or_cache(info.get("totalCash"), cached, "cash")
                r["revenue"] = _or_cache(info.get("totalRevenue"),
                                         cached, "revenue")
                r["shares_out"] = _or_cache(info.get("sharesOutstanding"),
                                            cached, "shares_out")
                # §12 session_context (نسخة دنيا صادقة): snapshot جلسة اليوم من
                # المتاح فعلًا فقط — ما قبل/بعد السوق غير متاح بمسار البوت →
                # سبب صريح بدل التخمين (خطة طبقة التفسير). عرض/تخزين فقط.
                r["session_ctx"] = {
                    "open": info.get("regularMarketOpen") or info.get("open"),
                    "high": (info.get("regularMarketDayHigh")
                             or info.get("dayHigh")),
                    "low": (info.get("regularMarketDayLow")
                            or info.get("dayLow")),
                    "prev_close": (info.get("regularMarketPreviousClose")
                                   or info.get("previousClose")),
                    "volume": (info.get("regularMarketVolume")
                               or info.get("volume")),
                    "market_cap": info.get("marketCap"),
                    "pre_after": None,
                    "unavailable_reason": ("بيانات ما قبل/بعد السوق غير متاحة "
                                           "بمسار البوت — لا تخمين"),
                }
                # N3 (لوحة علامات اليد): لقطة الطلبات الصادقة — bid/ask وحيدة وقت
                # الفرز. تدفق الطلبات الحي (Level 2) غير متاح بمسارنا → يُقال صراحة،
                # لا يُخمَّن. السبريد الواسع = علامة ضعف سيولة/يد تتحكّم بالعرض.
                _bid, _ask = info.get("bid"), info.get("ask")
                _spread = None
                if _bid and _ask and _ask > 0 and _ask >= _bid:
                    _spread = round((_ask - _bid) / _ask * 100.0, 1)
                r["session_ctx"]["quote"] = {
                    "bid": _bid, "ask": _ask,
                    "bid_size": info.get("bidSize"),
                    "ask_size": info.get("askSize"), "spread_pct": _spread,
                    "note": ("لقطة وحيدة وقت الفرز — تدفق الطلبات الحي غير متاح "
                             "بمسار البوت"),
                }
                # 🌙 إكمال pre_after بصدق (POLYGON_EDGE_PLAN §ج): **لو** المفتاح موجود
                # وداخل نافذة البريماركت، املأ ببيانات Polygon الفعلية وبدّل السبب —
                # وإلا يبقى None بسببه الصريح (لا تخمين). فاشل-آمن (يكمل P1-1 بشرف).
                if os.environ.get("POLYGON_API_KEY", "").strip():
                    try:
                        _pm = polygon_premarket(
                            r["symbol"], prev_close=r["session_ctx"].get("prev_close"))
                        if _pm:
                            r["session_ctx"]["pre_after"] = _pm
                            r["session_ctx"]["unavailable_reason"] = \
                                "من Polygon (اشتراك المستخدم)"
                    except Exception:
                        pass
                # حدّث الذاكرة بالقيم المعروفة الآن (للتشغيلات القادمة)
                _cc_entry = {k: r.get(k) for k in
                             ("sector", "industry", "business",
                              "country", "cash", "revenue",
                              "shares_out", "short_pct", "float",
                              "finra_short", "company_name", "first_trade",
                              "short_interest", "days_to_cover")
                             if r.get(k) is not None}
                COMPANY_CACHE.pop(sym, None)      # LRU: ينقله لأحدث موضع
                COMPANY_CACHE[sym] = _cc_entry
                # تحذير جغرافي (تحذير فقط — السهم يظل يظهر حتى في A)
                if r.get("country") in CONFIG.get("HIGH_RISK_COUNTRIES", []):
                    r.setdefault("warnings", []).append(
                        f"بلد عالي التلاعب ({ar_country(r['country'])}) — "
                        "غالباً يتجاهل التحليل الفني؛ تحقق يدوياً")
            except Exception:
                pass
            try:
                cutoff = pd.Timestamp.today(tz="UTC") - pd.Timedelta(
                    days=CONFIG["SPLIT_LOOKBACK_DAYS"])
                sp = t.splits
                if sp is not None and len(sp):
                    idx = sp.index.tz_localize("UTC") if sp.index.tz is None \
                        else sp.index.tz_convert("UTC")
                    recent = sp[idx >= cutoff]
                    rev = recent[recent < 1.0]
                    if len(rev):
                        r["recent_split"] = (str(rev.index[-1].date()),
                                             float(rev.iloc[-1]))
            except Exception:
                pass
            # أخبار ياهو (مجانية عبر yfinance) — عناوين آخر N يوم
            try:
                r["news"] = parse_yahoo_news(
                    t.news, CONFIG["NEWS_MAX_SHOW"], CONFIG["NEWS_DAYS"])
            except Exception:
                r["news"] = []
            # فحص آلي لعناوين الأخبار عن الطرح/التخفيف/الخطر → تحذير بالبطاقة
            for _w in scan_news_risk(r["news"]):
                r.setdefault("warnings", []).append(_w)
            # فريم 4 ساعات: تأكيد الانعكاس + مستويات فيصل (دعوم/أهداف/انقلاب)
            try:
                h4 = fetch_4h(r["symbol"])
                if h4 is not None:
                    _ok4 = timeframe_reversal(h4, 60, 20)
                    r["tf4h"] = "✅ مؤكِّد" if _ok4 else "⏳ غير مؤكِّد بعد"
                    r["h4_levels"] = four_hour_levels(h4, r["price"])
                    # دمج فيصل (#1+#3): أهداف 4س في t2/t3 (t1/RR مقفولان) +
                    # تأكيد 4س للترتيب — بنفس بيانات الـ4س المجلوبة (بلا تحميل زائد).
                    r["t2"], r["t3"] = refine_targets_4h(
                        r["t1"], r["t2"], r["t3"], r["price"], r["h4_levels"])
                    # حدّث rr2 بعد تنقيح t2 (يُكتب في CSV الأسبوعي) — من متوسط
                    # الدفعات نفسه، فلا يتعارض مع t2 الجديد (t1/rr مقفولان).
                    try:
                        _er = sum(r["tranches"]) / len(r["tranches"])
                        r["rr2"] = (r["t2"] - _er) / max(_er - r["stop"][0], 1e-9)
                    except Exception:
                        pass
                    r["h4_confirm"] = h4_confirm_score(r)
                    # 🎬 KST على 4س بإعدادات فيصل (فيديو DSY) — حالة زخم مساندة.
                    # عرض/سياق فقط — لا نقاط ولا بوابة (المؤشر مساند لا أساس).
                    try:
                        r["kst4"] = momentum_kst_state(h4["Close"])
                    except Exception:
                        r["kst4"] = None
                else:
                    r["tf4h"] = "غير متوفر"
            except Exception:
                r["tf4h"] = "غير متوفر"
        except Exception:
            continue
        # 📅 الأحداث المعلنة القادمة (أرباح + تجارب سريرية للرعاية الصحية) —
        # فاشل-آمن → None (عرض/سياق فقط، «يوم الانفجار الذي ينتظره المضارب»)
        try:
            r["upcoming_events"] = upcoming_events(
                r["symbol"], r.get("company_name"), r.get("sector"),
                r.get("proxy_filing"), r.get("first_trade"))
        except Exception:
            r["upcoming_events"] = None
        time.sleep(0.5)
    _save_company_cache(COMPANY_CACHE)   # حفظ آخر القطاعات/الدول المعروفة
    # 🧭 تجديد طبقة التفسير **بعد** الإثراء (إصلاح 2026-07-07): h4_levels والأخبار
    # وSEC والتقسيم وتنقيح t2/t3 كلها تُضاف هنا — التفسير المحسوب قبلها كان يفوته
    # سياق 4س وأعلام الخطر. عرض/تفسير فقط؛ حارس «لا يمسح الموجود»: لو رجع فارغًا
    # (سجل بلا سعر/قاع) يبقى التفسير المخزّن كما هو.
    for r in results:
        try:
            _ip = build_interpretation(r)
            if _ip:
                r["interp"] = _ip
        except Exception:
            pass


# ==========================================================
# 7) استراتيجية التقسيم العكسي
# ==========================================================
def _split_frequency(splits, today, days: int = 365) -> int:
    """🔁 عدد التقسيمات العكسية (نسبة أقل من 1) في آخر `days` يومًا (سنة افتراضيًا).
    قاعدة فيصل (FAISAL_OPERATOR_PACK §P4، من الصور): «اذا تقسيم كثير خلال فتره زمنيه
    قصيره غالبا مايطول، سبوع بالكثير» (مثل ZCMD حقّق 600% ثم ارتدّ). دالة نقيّة ·
    فاشلة-آمنة (بيانات مفقودة/غير صالحة → 0). تقبل pandas Series (فهرسها تواريخ ·
    قيمتها نسبة التقسيم) أو قائمة أزواج (تاريخ, نسبة). `today` = dt.date. **عرض/تحذير
    فقط — خارج الفرز نهائيًا** (لا يمسّ الدخول/الوقف/الأهداف/العضوية)."""
    try:
        cutoff = today - dt.timedelta(days=days)
        if hasattr(splits, "index") and hasattr(splits, "values"):
            pairs = list(zip(splits.index, splits.values))
        else:
            pairs = list(splits or [])
        n = 0
        for ts, ratio in pairs:
            try:
                d = ts.date() if hasattr(ts, "date") else ts
                if isinstance(d, str):
                    d = dt.date.fromisoformat(d[:10])
                if float(ratio) < 1.0 and d >= cutoff:
                    n += 1
            except Exception:
                continue
        return n
    except Exception:
        return 0


def _split_freq_line(freq) -> str:
    """سطر تحذير «تقسيمات متكررة = نَفَس قصير» (عند تقسيمين فأكثر في سنة). عرض فقط —
    يرجع "" لو أقل من تقسيمين (لا حشو). موحَّد بين قسم D9 وفحص اليد."""
    if (freq or 0) >= 2:
        return (f"🔁 تقسيمات متكررة ({int(freq)} في سنة) — قاعدة فيصل: الصعود "
                "غالبًا لا يتجاوز أسبوعًا (ZCMD صعد 600% ثم ارتدّ)")
    return ""


def _split_row(sym, split_date, day_open, price, short, freq=None):
    """صفّ تقرير التقسيم العكسي (D9): هدف الهبوط = افتتاح التقسيم ÷ 2 (فيصل
    EHGO 2.80÷2=1.40)؛ والشورت «مقبول» لو أقل من SHORT_DAILY_MAX («تابعه لين
    الشورت تحت 20 ألف»). `freq` = عدد التقسيمات العكسية في آخر سنة (قرينة فيصل §P4،
    عرض فقط). دالة نقية قابلة للاختبار بلا شبكة."""
    target = round(day_open / 2.0, 2) if day_open else None
    ok = (short is not None and short < CONFIG["SHORT_DAILY_MAX"])
    return {"symbol": sym, "split_date": str(split_date), "open": day_open,
            "half": target, "price": price, "short": short, "short_ok": ok,
            "freq": freq}


def split_watch_report(history: dict) -> list:
    """مراقبة قائمة التقسيمات اليدوية: قاع متوقع = شمعة التقسيم ÷ 2"""
    rows = []
    if yf is None:
        return rows
    watch = [s for s in CONFIG["SPLIT_WATCHLIST"] if s in history]
    if not watch:
        return rows
    shorts = {}
    try:
        shorts = finra_daily_short(set(watch))
    except Exception:
        pass
    for sym in watch:
        try:
            t = yf.Ticker(sym)
            sp = t.splits
            if sp is None or not len(sp):
                continue
            idx = sp.index.tz_localize("UTC") if sp.index.tz is None \
                else sp.index.tz_convert("UTC")
            cutoff = pd.Timestamp.today(tz="UTC") - pd.Timedelta(
                days=CONFIG["SPLIT_LOOKBACK_DAYS"])
            recent = sp[idx >= cutoff]
            rev = recent[recent < 1.0]
            if not len(rev):
                continue
            split_date = rev.index[-1].date()
            df = history[sym]
            day_open = None
            try:
                after = df[df.index.tz_localize(None) >= pd.Timestamp(split_date)] \
                    if df.index.tz is not None else \
                    df[df.index >= pd.Timestamp(split_date)]
                if len(after):
                    day_open = float(after["Open"].iloc[0])
            except Exception:
                pass
            price = float(df["Close"].iloc[-1])
            freq = _split_frequency(sp, dt.date.today())   # §P4 (نفس بيانات sp)
            rows.append(_split_row(sym, split_date, day_open, price,
                                   shorts.get(sym), freq))
        except Exception:
            continue
    return rows


def build_split_watch_section(rows: list) -> str:
    """قسم «مراقبة التقسيم العكسي» (D9): يفعّل قاعدة فيصل ÷2 النائمة — عرض فقط."""
    if not rows:
        return ""
    lines = ["✂️ <b>مراقبة التقسيم العكسي</b> (هدف الهبوط = افتتاح التقسيم ÷2):"]
    for r in rows:
        half = f"${r['half']:.2f}" if r.get("half") else "—"
        if r.get("short") is not None:
            stag = (f"شورت {fmt_money(r['short'])} "
                    + ("✓" if r.get("short_ok") else "⚠️ عالٍ"))
        else:
            stag = "شورت —"
        lines.append(f"• <b>{esc(r['symbol'])}</b> ${r['price']:.2f} · "
                     f"هدف هبوط {half} · {stag}")
        _fl = _split_freq_line(r.get("freq"))              # §P4 (عرض/تحذير فقط)
        if _fl:
            lines.append("  " + _fl)
    lines.append("<i>القاع المتوقع بعد التقسيم ≈ نصف افتتاح التقسيم (فيصل).</i>")
    return _rtl_join(lines)


# ==========================================================
# 8) أدوات الرسائل المشتركة
# ==========================================================
def esc(s):
    """تعقيم النصوص الخارجية حتى لا تكسر HTML تيليجرام.
    14أ (إصلاح تدقيق 2026-07-12): إضافة تهريب `\"` — الدالة تُستعمل داخل خاصية
    href=\"...\" واقتباس في رابط خارجي كان يكسر الخاصية → تلغرام يرفض الرسالة
    كلها بـ400 وsend_telegram يسجّل ويمضي = تنبيه تداول لا يصل."""
    return (str(s).replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def fmt_money(x):
    if x is None:
        return "غير متوفر"
    if x >= 1_000_000:
        return f"{x/1_000_000:.1f}M"
    if x >= 1_000:
        return f"{x/1_000:.0f}K"
    return str(int(x))


# ترجمة القطاع/الدولة للعربي (تعريب البطاقة)
SECTOR_AR = {
    "Technology": "تقنية",
    "Communication Services": "اتصالات وإعلام",
    "Healthcare": "رعاية صحية",
    "Financial Services": "خدمات مالية",
    "Financials": "خدمات مالية",
    "Consumer Cyclical": "استهلاكي تدويري",
    "Consumer Defensive": "استهلاكي دفاعي",
    "Energy": "طاقة",
    "Industrials": "صناعات",
    "Basic Materials": "مواد أساسية",
    "Real Estate": "عقارات",
    "Utilities": "مرافق",
    "Biotechnology": "تقنية حيوية",
}
COUNTRY_AR = {
    "United States": "أمريكا",
    "China": "الصين",
    "Hong Kong": "هونغ كونغ",
    "Singapore": "سنغافورة",
    "Canada": "كندا",
    "Israel": "إسرائيل",
    "United Kingdom": "بريطانيا",
    "Ireland": "أيرلندا",
    "Germany": "ألمانيا",
    "France": "فرنسا",
    "Switzerland": "سويسرا",
    "Netherlands": "هولندا",
    "Australia": "أستراليا",
    "Japan": "اليابان",
    "South Korea": "كوريا الجنوبية",
    "Taiwan": "تايوان",
    "India": "الهند",
    "Brazil": "البرازيل",
    "Cayman Islands": "جزر كايمان",
    "Bermuda": "برمودا",
    "Vietnam": "فيتنام",
    "Greece": "اليونان",
    "Marshall Islands": "جزر مارشال",
    "Cyprus": "قبرص",
    "Monaco": "موناكو",
    "Mexico": "المكسيك",
    "Argentina": "الأرجنتين",
    "Chile": "تشيلي",
    "Indonesia": "إندونيسيا",
    "Malaysia": "ماليزيا",
    "Philippines": "الفلبين",
    "Thailand": "تايلاند",
    "Sweden": "السويد",
    "Norway": "النرويج",
    "Denmark": "الدنمارك",
    "Finland": "فنلندا",
    "Italy": "إيطاليا",
    "Spain": "إسبانيا",
    "Belgium": "بلجيكا",
    "Austria": "النمسا",
    "Luxembourg": "لوكسمبورغ",
    "United Arab Emirates": "الإمارات",
    "South Africa": "جنوب أفريقيا",
    "New Zealand": "نيوزيلندا",
    "Turkey": "تركيا",
}
# علم الدولة (إيموجي) — يُعرض بجانب اسمها بالكرت واليومي (طلب المستخدم)
COUNTRY_FLAG = {
    "United States": "🇺🇸", "China": "🇨🇳", "Hong Kong": "🇭🇰",
    "Singapore": "🇸🇬", "Canada": "🇨🇦", "Israel": "🇮🇱",
    "United Kingdom": "🇬🇧", "Ireland": "🇮🇪", "Germany": "🇩🇪",
    "France": "🇫🇷", "Switzerland": "🇨🇭", "Netherlands": "🇳🇱",
    "Australia": "🇦🇺", "Japan": "🇯🇵", "South Korea": "🇰🇷",
    "Taiwan": "🇹🇼", "India": "🇮🇳", "Brazil": "🇧🇷",
    "Cayman Islands": "🇰🇾", "Bermuda": "🇧🇲",
    "Vietnam": "🇻🇳", "Greece": "🇬🇷", "Marshall Islands": "🇲🇭",
    "Cyprus": "🇨🇾", "Monaco": "🇲🇨", "Mexico": "🇲🇽",
    "Argentina": "🇦🇷", "Chile": "🇨🇱", "Indonesia": "🇮🇩",
    "Malaysia": "🇲🇾", "Philippines": "🇵🇭", "Thailand": "🇹🇭",
    "Sweden": "🇸🇪", "Norway": "🇳🇴", "Denmark": "🇩🇰",
    "Finland": "🇫🇮", "Italy": "🇮🇹", "Spain": "🇪🇸",
    "Belgium": "🇧🇪", "Austria": "🇦🇹", "Luxembourg": "🇱🇺",
    "United Arab Emirates": "🇦🇪", "South Africa": "🇿🇦",
    "New Zealand": "🇳🇿", "Turkey": "🇹🇷",
}


def position_size(avg_entry, stop_lo):
    """حجم المركز من إدارة المخاطر: كم سهم تشتري بحيث خسارتك لو ضُرب الوقف =
    RISK_PER_TRADE_PCT% من رأس المال. يرجع dict أو None."""
    try:
        risk_share = float(avg_entry) - float(stop_lo)
    except Exception:
        return None
    if risk_share <= 0 or not CONFIG.get("ACCOUNT_SIZE"):
        return None
    budget = CONFIG["ACCOUNT_SIZE"] * CONFIG["RISK_PER_TRADE_PCT"] / 100.0
    shares = int(budget / risk_share)
    if shares <= 0:
        return None
    return {"shares": shares, "cost": round(shares * float(avg_entry), 0),
            "risk": round(budget, 0)}


def position_size_line(tranches, stop_lo) -> list:
    """سطر حجم المركز (يُحسب من متوسط الدفعات = تعبئة فيصل الفعلية)."""
    if not tranches:
        return []
    avg = sum(tranches) / len(tranches)
    ps = position_size(avg, stop_lo)
    if not ps:
        return []
    return [f"   📐 حجم المركز (مخاطرة {CONFIG['RISK_PER_TRADE_PCT']:.0f}% من "
            f"${CONFIG['ACCOUNT_SIZE']:,.0f}): ~{ps['shares']:,} سهم "
            f"(~${ps['cost']:,.0f} · مخاطرة ${ps['risk']:,.0f})"]


def h4_levels_block(h4l) -> list:
    """سطر مستويات الـ4 ساعات (منظومة فيصل): انقلاب/دعوم/أهداف/قاع المسح.
    طبقة مساندة — لا تغيّر الخطة اليومية. يرجع [] لو لا مستويات."""
    if not h4l:
        return []
    bits = []
    if h4l.get("flip"):
        bits.append(f"مقاومة↗دعم ${h4l['flip']:.2f}")
    if h4l.get("supports"):
        bits.append("دعوم " + "/".join(f"${x:.2f}" for x in h4l["supports"][:3]))
    if h4l.get("resistances"):
        bits.append("أهداف " + "/".join(f"${x:.2f}"
                                          for x in h4l["resistances"][:3]))
    if h4l.get("sweep_low"):
        bits.append(f"ذيل المسح ${h4l['sweep_low']:.2f}")
    return ["   🕓 4س: " + " · ".join(bits)] if bits else []


def ar_sector(s):
    """يرجّع القطاع بالعربي إن وُجد، وإلا الأصل كما هو"""
    return SECTOR_AR.get(s, s) if s else s


def ar_country(c):
    """يرجّع الدولة بالعربي إن وُجد، وإلا الأصل كما هو"""
    return COUNTRY_AR.get(c, c) if c else c


def country_label(c):
    """علم الدولة + اسمها بالعربي (مثل «🇺🇸 أمريكا») — أو الاسم فقط لو لا علم،
    أو "" لو لا دولة. يُعرض في الكرت واليومي."""
    if not c:
        return ""
    flag = COUNTRY_FLAG.get(c, "")
    return f"{flag} {esc(ar_country(c))}".strip()


def short_line(r) -> str:
    """سطر الشورت (v2.0): بلا إيموجي، مع اسم المصدر،
    والتفريق الصريح بين الرقم الفعلي وتعذّر الجلب."""
    fd = r.get("fintel") or {}
    vol_part = None
    if fd.get("short_volume") is not None:
        vol_part = f"{fmt_money(fd['short_volume'])} (Fintel)"
    elif r.get("finra_short") is not None:
        vol_part = f"{fmt_money(r['finra_short'])} (FINRA)"
    pct_part = None
    if fd.get("si_pct_float") is not None:
        pct_part = f"{fd['si_pct_float']}% من الفلوت (Fintel)"
    elif r.get("short_pct") is not None:
        pct_part = f"{r['short_pct']}% من الفلوت (Yahoo)"
    if vol_part and pct_part:
        return f"شورت يومي: {vol_part} | فائدة الشورت: {pct_part}"
    if vol_part:
        return f"شورت يومي: {vol_part}"
    if pct_part:
        return f"فائدة الشورت: {pct_part}"
    return "شورت: تعذّر الجلب من كل المصادر (ليس صفراً)"


def risk_lines(price, stop_lo, t1, t2, rr):
    """عرض المخاطرة بالدولار الفعلي (v2.0) بدل نسبة 1:X الغامضة"""
    risk = price - stop_lo
    g1 = t1 - price
    g2 = t2 - price
    if rr >= 3:
        q = "ممتازة جداً"
    elif rr >= 2:
        q = "ممتازة"
    else:
        q = "جيدة"
    return [
        f"🛡️ تخاطر بـ${risk:.2f} للسهم ← ربح هدف1: ${g1:.2f} | "
        f"هدف2: ${g2:.2f}",
        f"⚖️ جودة الصفقة: {q} (الربح {rr:.1f}× المخاطرة)",
    ]


def news_links(sym: str) -> str:
    """روابط أخبار قابلة للضغط لكل سهم (موثوقة 100% — لا سحب آلي).
    ضغطة واحدة → تفتح صفحة أخبار السهم في الموقع. TipRanks هو المصدر
    الأفضل حسب فيصل (قسم The Fly يرصد الطرح/التخفيف بسرعة)، لكنه مدفوع
    ومحمي ضد السحب الآلي، فنعطيك رابطه المباشر بدل محاولة سحب فاشلة."""
    s = sym.upper()
    tr = f"https://www.tipranks.com/stocks/{s.lower()}/stock-news"
    yh = f"https://finance.yahoo.com/quote/{s}/news"
    fv = f"https://finviz.com/quote.ashx?t={s}"
    return (f'🔗 تابع أخباره — <a href="{tr}">⭐ TipRanks</a> (الأفضل) | '
            f'<a href="{yh}">Yahoo</a> | <a href="{fv}">Finviz</a>')


def news_block(r) -> list:
    """قسم الأخبار في البطاقة: عناوين ياهو التلقائية + روابط المتابعة"""
    lines = []
    news = r.get("news") or []
    if news:
        lines.append("📰 <b>آخر الأخبار (Yahoo):</b>")
        for it in news:
            # 14أ: القصّ **قبل** التهريب — القصّ بعده كان قد يشطر كيان HTML
            # (مثل &amp; → &am) فيكسر رسالة تلغرام كاملة.
            head = esc(it.get("title", "")[:140])
            src = esc(it.get("publisher", ""))
            day = it.get("date", "")
            meta = " — ".join(x for x in (src, day) if x)
            link = it.get("link", "")
            if link:
                lines.append(f'  • <a href="{esc(link)}">{head}</a>'
                             + (f" ({meta})" if meta else ""))
            else:
                lines.append(f"  • {head}" + (f" ({meta})" if meta else ""))
    lines.append(news_links(r["symbol"]))
    return lines


def splits_block(splits) -> list:
    """قسم مراقبة التقسيم العكسي (مشترك بين الرسائل)"""
    if not splits:
        return []
    lines = ["", "✂️ <b>مراقبة أسهم التقسيم العكسي</b>"]
    for s in splits:
        half = f"${s['half']:.2f}" if s["half"] else "غير محسوب"
        if s["short"] is None:
            srt = "تعذّر الجلب"
        elif s["short_ok"]:
            srt = f"{fmt_money(s['short'])} ✅ تحت 20 ألف"
        else:
            srt = f"{fmt_money(s['short'])} ⏳ فوق 20 ألف"
        lines.append(
            f"• {s['symbol']} | قسم {s['split_date']} | "
            f"القاع المتوقع (الافتتاح÷2): {half} | "
            f"السعر: ${s['price']:.2f} | شورت: {srt}")
    return lines


FOOTER = ("⚠️ <i>فارز آلي حسب منهجية موثقة — ليست توصية. "
          "القرار النهائي وإدارة المخاطر عليك.</i>")


def _rtl_join(lines):
    """يربط الأسطر مع **إجبار اتجاه RTL** لكل سطر (علامة RLM غير مرئية ‏ في
    بدايته) — فيبدأ كل سطر من **اليمين** ويتّسق الترتيب في تيليجرام العربي، فلا
    تتفاوت الأسطر (بعضها يبدأ برقم/$ من اليسار وبعضها بعربي من اليمين). عرض بحت."""
    return "\n".join(("‏" + ln) if ln.strip() else ln for ln in lines)


def strength_bar(score):
    """شريط القوة العامة (10 خانات) + وصف — للبطاقة المختصرة (عرض فقط)."""
    s = max(0, min(int(score or 0), 100))
    filled = int(round(s / 10.0))
    bar = "█" * filled + "░" * (10 - filled)
    if s >= 85:
        label = "🔥 قوي جدًا"
    elif s >= 70:
        label = "💪 قوي"
    elif s >= 55:
        label = "⚖️ متوسط"
    else:
        label = "🔻 ضعيف"
    return bar, label


def readiness_tag(p):
    """وسم حالة الجاهزية (🟢/🟡/🔴 + الكلمة) بلا النسبة — لرأس البطاقة المختصرة.
    يعيد استخدام `readiness_badge` (مصدر العتبات/المسمّيات الوحيد، لا تكرار)."""
    if p is None:
        return "⚠️ لا بيانات"
    return readiness_badge(p).split("</b>")[-1].strip()


def news_links_compact(sym: str) -> str:
    """روابط أخبار مختصرة (سطر واحد نظيف) — نفس مصادر `news_links` بمسمّيات أقصر."""
    s = sym.upper()
    tr = f"https://www.tipranks.com/stocks/{s.lower()}/stock-news"
    yh = f"https://finance.yahoo.com/quote/{s}/news"
    fv = f"https://finviz.com/quote.ashx?t={s}"
    return (f'🔗 <a href="{tr}">TipRanks</a> · '
            f'<a href="{yh}">Yahoo</a> · <a href="{fv}">Finviz</a>')


def timeframes_info(tf_count, tf_display=None):
    """سطر معلومة عن توافق الفريمات لمّا تُجتاز البوابة (2 فأكثر) — يسمّي كل فريم
    (شهري/أسبوعي/يومي) بعلامته فيبان الفريم الناقص (⏳). يرجع None لو لم تُجتَز
    (تظهر وقتها ضمن النواقص) أو العدد غير متوفر."""
    if tf_count is None or tf_count < CONFIG["TF_MIN_REVERSALS"]:
        return None
    if tf_display:
        tag = "مكتمل" if tf_count >= 3 else f"{tf_count}/3 · ⏳ = الباقي للكمال"
        return f"🕯️ الفريمات ({tag}): {tf_display}"
    # احتياطي (سجلّات قديمة بلا تفصيل الفريمات)
    return ("🕯️ الفريمات 3/3 ✓ (مكتمل)" if tf_count >= 3
            else "🕯️ الفريمات 2/3 ✓ (باقي فريم للكمال)")


_SETUP_AR = {"pivot_reversal": "ارتكاز انعكاسي", "liquidity_sweep": "مسح سيولة",
             "support_reclaim": "استعادة دعم", "h4_reclaim": "استعادة 4س",
             "extended_risk": "ممتد/بعيد عن الدعم", "unclassified": "غير مصنّف"}
_ENTRY_AR = {"near_support": "قرب الدعم", "sweep_confirmed": "بعد مسح مؤكَّد",
             "reclaim_wait": "انتظار استعادة الدعم", "no_entry_far": "لا دخول (بعيد)"}


def behavior_tags(bh: dict) -> list:
    """§13 توسعة 🧬: وسوم وصفية إضافية على بصمة «طريقة الارتفاع» عند توفّر الدليل —
    **عرض فقط، لا تغيير بالدرجة/المكوّنات المقفولة** (خطة INTERPRETATION_LAYER_PLAN):
      • «صيد وقفات متكرّر» (stop hunt): اليد كنست الدعم بذيل ثم استعادت مرّتين فأكثر.
      • «رفعة قديمة وخمول طويل» (نمط BJDX): رفعة سابقة ثم سكون طويل (120 جلسة فأكثر).
      • «يد نشطة — حذارِ مسح الوقف قبل الانطلاق» (درجة 60 فأكثر): **حكم باكتيست
        السنتين 2025+2026** (تجربة مسجّلة مسبقًا بلا تسريب): البصمة العالية نجاحها
        بالوقف الثابت أقل بثبات (~30%→~10-14% بالسنتين) لأن اليد النشطة تمسح
        الستوبات — فهي تحذير توقيت (انتظر المسح والاستعادة)، **ليست أولوية اختيار**
        (فرق الانفجار متداخل الفواصل بالسنتين → «تبقى عرضًا فقط»)."""
    tags = []
    if not bh:
        return tags
    if (bh.get("sweeps") or 0) >= 2:
        tags.append("صيد وقفات متكرّر")
    rec = bh.get("recency_bars")
    if (bh.get("n_pumps") or 0) >= 1 and rec is not None and rec >= 120:
        tags.append("رفعة قديمة وخمول طويل")
    if (bh.get("score") or 0) >= 60:
        tags.append("يد نشطة — حذارِ مسح الوقف قبل الانطلاق")
    return tags


def hand_evidence(r: dict) -> list:
    """🕵️ لوحة «علامات اليد» (خطة HAND_EVIDENCE_PANEL_PLAN، طلب المستخدم 2026-07-08:
    «أي سهم فيه شك أن وراه مضارب»). تجمع قرائن يدٍ تشتغل على السهم من المصادر
    الأربعة (شموع يومية · 4س · طلبات · رفعة قروب ثم كسر دعوم) في **قائمة أدلة
    نوعية موحّدة — بلا درجة مبتدعة ولا أولوية اختيار** (حكم السنتين §0-ح: اليد
    النشطة تمسح الوقف الثابت، فالقيمة أن يعرف المتداول ويتوقّع الكنسة لا أن يُرجَّح
    السهم بالفرز). عرض/تحذير فقط · تُقرأ من حقول مخزّنة (behav/h4_levels/pump_scar/
    rotation/session_ctx/interp). كل دليل: {frame, sign, detail}. فاشل-آمن → []."""
    ev = []
    try:
        bh = r.get("behav") or {}
        if (bh.get("sweeps") or 0) >= 2:
            ev.append({"frame": "يومي", "sign": "مسح دعم متكرر",
                       "detail": f"{bh['sweeps']} مرّات"})
        # (لا نكرّر درجة البصمة هنا — هي على سطر 🧬 بالفعل؛ اللوحة تجمع الأدلة
        # النوعية المتمايزة لا الدرجة — مراجعة خصومية عدسة العرض 2026-07-08)
        ps = r.get("pump_scar") or {}
        if ps.get("found"):
            sign = ("رفعة قروب ثم كسر دعوم" if ps.get("broke_support")
                    else "رفعة قروب بسيولة")
            det = f"قفزة {ps.get('jump_pct', 0):.0f}% قبل {ps.get('bars_ago', 0)}ج"
            ev.append({"frame": "يومي", "sign": sign, "detail": det})
        h4 = r.get("h4_levels") or {}
        mc = h4.get("managed_ceiling")
        if mc and mc.get("price"):
            ev.append({"frame": "4س",
                       "sign": f"سقف مُدار عند ${mc['price']:.2f}",
                       "detail": f"{mc['touches']} لمسات"})
        if (r.get("interp") or {}).get("entry_mode", {}).get(
                "mode") == "sweep_confirmed":
            ev.append({"frame": "4س", "sign": "مسح واستعادة الآن",
                       "detail": "تأكيد لحظي"})
        rot = r.get("rotation_pct")
        if rot and rot >= 100:
            ev.append({"frame": "حجم", "sign": "تدوير فلوت مرتفع",
                       "detail": f"{rot:.0f}% (سكويز)"})
        q = (r.get("session_ctx") or {}).get("quote") or {}
        if q.get("spread_pct") is not None and q["spread_pct"] >= 3.0:
            ev.append({"frame": "طلبات", "sign": "سبريد واسع",
                       "detail": f"{q['spread_pct']:.0f}% (لقطة)"})
        # N5 (FAISAL_OPERATOR_PACK §P2): «عروض شبه مُفرَّغة» — بصمة تجهيز المضارب
        # (فيصل باللقطة الحقيقية: «يفرّغ العروض كامله · اقرب عرض 30٪ فوق · يشري بالف
        # دولار ارتفع 30% · لايريد ضخ سيوله عاليه»). وكيل صادق من لقطة NBBO الخام
        # (flow_raw، تُخزَّن بفحص اليد فقط): دولارات أفضل عرض تافهة + سبريد واسع.
        # حدّ الصدق مكتوب داخل الدليل (أفضل عرض فقط — عمق L2 غير متاح). فاشل-آمن.
        fr = r.get("flow_raw") or {}
        _ask, _asz, _spr = fr.get("ask"), fr.get("ask_size"), fr.get("spread_pct")
        if (_ask and _asz and _spr is not None
                and _spr >= 5.0 and float(_ask) * float(_asz) <= 1000):
            ev.append({"frame": "طلبات", "sign": "عروض شبه مُفرَّغة",
                       "detail": f"${float(_ask) * float(_asz):.0f} فقط عند أفضل "
                                 f"عرض · سبريد {_spr:.0f}% (تجهيز مضارب — أفضل عرض "
                                 "فقط، عمق الدفتر غير متاح)"})
    except Exception:
        pass
    return ev


def hand_evidence_line(r: dict) -> str:
    """سطر «🕵️ علامات اليد» المكثّف (يظهر عند دليلين فأكثر — لا حشو لكل سهم).
    أول 3 أدلة نصًّا و«+N» للباقي. يرجع "" لو أقل من دليلين. عرض فقط."""
    ev = hand_evidence(r)
    if len(ev) < 2:
        return ""
    shown = [f"{e['sign']} ({e['frame']})" for e in ev[:3]]
    extra = f" +{len(ev) - 3}" if len(ev) > 3 else ""
    return f"🕵️ علامات اليد ({len(ev)}): " + " · ".join(shown) + extra


def hand_activity_today(s: dict, df) -> list:
    """🕵️ «ماذا فعلت اليد اليوم؟» (تحديث نهاية اليوم — طلب المستخدم 2026-07-08:
    «يوصلني تحديث نهاية اليوم بخصوص الأسهم اللي وراها مضارب وأعرف وش سوّى»).
    يقرأ شمعة اليوم (آخر شمعة) مقابل السياق القريب ويصف تحرّك اليد الفعلي:
    كنس دعم · كسر دعم · دفاع عن سقف · شمعة بحجم ضخم. **عرض/تشخيص فقط · خلفي بلا
    نظر مستقبلي** (يصف ما حدث في آخر شمعة مكتملة). العتبات من الموجود
    (VOL_SPIKE_MULT + الدعم القريب). يرجّع قائمة أفعال عربية — فارغة عند الهدوء."""
    acts = []
    try:
        c = df["Close"].values.astype(float)
        h = df["High"].values.astype(float)
        lo = df["Low"].values.astype(float)
        o = df["Open"].values.astype(float)
        v = df["Volume"].values.astype(float)
        n = len(c)
        if n < 25:
            return acts
        t_c, t_h, t_lo, t_o, t_v = c[-1], h[-1], lo[-1], o[-1], v[-1]
        prev_c = c[-2]
        sup = float(np.min(lo[-21:-1]))            # دعم قريب (20ج قبل اليوم)
        vavg = float(np.mean(v[-21:-1]))
        gain = (t_c / prev_c - 1.0) * 100.0 if prev_c > 0 else 0.0
        # 1) كنس دعم اليوم (ذيل خرق الدعم ثم إغلاق فوقه) · أو 2) كسر دعم (إغلاق تحته)
        if sup > 0 and t_lo < sup * 0.98 and t_c >= sup:
            acts.append(f"كنس الدعم ${sup:.2f} بذيل ثم استعاده (مسح سيولة)")
        elif sup > 0 and t_c < sup:
            acts.append(f"كسر الدعم ${sup:.2f} وأغلق تحته")
        # 3) دفاع عن السقف المُدار (ضربه ثم أغلق أحمر تحته = بيع اليد عنده)
        ceil = ((s.get("h4_levels") or {}).get("managed_ceiling") or {}).get("price")
        if ceil and t_h >= ceil * 0.99 and t_c < t_o and t_c < ceil:
            acts.append(f"دافع عن السقف ${ceil:.2f} (ضربه ثم ارتد بيعًا)")
        # 4) شمعة بحجم ضخم (سيولة قروب) — أخضر=رفع · أحمر=توزيع/هزّ
        if vavg > 0 and t_v >= CONFIG["VOL_SPIKE_MULT"] * vavg:
            mult = t_v / vavg
            if t_c > t_o:
                acts.append(f"شمعة صعود بحجم ضخم (+{gain:.0f}% · {mult:.0f}× الحجم)")
            else:
                acts.append(f"شمعة هبوط بحجم ضخم ({gain:.0f}% · {mult:.0f}× — توزيع/هزّ)")
            # ⚠️ قاعدة فيصل LABT (FAISAL_OPERATOR_PACK §P3): سيولة كبيرة تدخل **قبل**
            # كسر الرقم الحرج = سيولة قطيع قبل رفعة المضارب → غالبًا يُهبِطه عمدًا
            # (LABT هبط −40% بالأفتر). عرض/تحذير فقط — فاشل-آمن (لا رقم حرج = لا سطر).
            _crit = ((s.get("interp") or {}).get("critical_number") or {}).get("price")
            if _crit and t_c < float(_crit):
                acts.append(f"⚠️ سيولة كبيرة بلا كسر الرقم الحرج ${float(_crit):.2f} — "
                            "قاعدة فيصل: سيولة قبل رفعة المضارب تُهبِط (مثال LABT −40%)")
    except Exception:
        pass
    return acts


def build_hand_digest(wl: dict, history: dict) -> str:
    """🕵️ تحديث نهاية اليوم: الأسهم التي وراءها بصمة يد + ماذا فعلت اليوم.
    عرض/تحذير فقط — يجمع `hand_evidence` (بصمة اليد الثابتة) + `hand_activity_today`
    (تحرّك اليوم) لكل سهم نشط. يُدرَج السهم لو له دليلان فأكثر **أو** فعل اليد شيئًا
    اليوم. النشط اليوم أولًا. لا يمسّ أي حساب."""
    today = dt.date.today().isoformat()
    lines = [f"🕵️ <b>تحديث اليد — نهاية اليوم</b> · {today}",
             "أسهم القائمة التي وراءها بصمة يد + ماذا فعلت اليوم", ""]
    rows = []
    for s in wl.get("stocks", []):
        if s.get("status") != "active":
            continue
        df = history.get(s["symbol"])
        ev = hand_evidence(s)
        acts = hand_activity_today(s, df) if df is not None else []
        if len(ev) < 2 and not acts:
            continue
        rows.append((s, ev, acts))
    if not rows:
        lines.append("🟢 لا نشاط مضارب ملحوظ اليوم على القائمة.")
    else:
        rows.sort(key=lambda x: (-len(x[2]), -len(x[1])))   # النشط اليوم أولًا
        for s, ev, acts in rows:
            lp = s.get("last_price")
            es = entry_status(s)             # الأهم: جاهز للدخول أم متابعة؟
            tag = "🟢 جاهز للدخول" if es["status"] == "ready_now" else "👀 متابعة"
            head = f"{tag} · <b>${s['symbol']}</b>"
            if lp:
                head += f" · ${lp:.2f}"
            lines.append(head)
            if acts:
                for a in acts:
                    lines.append(f"   📌 اليوم: {a}")
            else:
                lines.append("   💤 اليوم: هدوء (لا تحرّك يد واضح)")
            hl = hand_evidence_line(s)
            if hl:
                lines.append("   " + hl)
            lines.append("")
    lines.append("ℹ️ كشف/تحذير — علامات اشتباه بيد نشطة، ليست توصية ولا تُرجّح "
                 "السهم بالفرز. تدفق الطلبات الحي غير متاح (لقطة فقط).")
    lines.append(FOOTER)
    return _rtl_join(lines)


def build_interpretation(r: dict) -> dict:
    """🧭 طبقة التفسير والقرار (خطة INTERPRETATION_LAYER_PLAN.md، 2026-07-05 — **عرض/تفسير
    فقط**: لا تمسّ الفرز/الدخول/الوقف/الأهداف/العضوية · لا LOGIC_VERSION). تقرأ حقول r
    المحسوبة أصلًا (key_levels/h4_levels/t1..t3/tranches/pivot/warnings/behav/sec/split)
    وتُنتج تفسيرًا: setup_type · critical_number (الرقم الحرج، فيصل NAMM) · activation_state
    (**وسم** على الأهداف الحالية لا يعيد حسابها) · entry_mode (وصفي) · four_hour_context ·
    risk_profile (تجميع، بلا تجريم الفلوت/الرسملة) · level_roles · targets_src. فاشل-آمن:
    أي جزء ينكسر يُهمَل بلا إسقاط البقية. حيّ فقط (لا يُستدعى بالباكتيست)."""
    out = {}
    try:
        # سقوط للسعر اليومي المحدَّث (سجلّات القائمة المخزّنة تحمل last_price لا price)
        # — يسمح بتجديد التفسير يوميًا فلا يتجمّد الرقم الحرج/وضع الدخول يوم الترشيح.
        price = float(r.get("price") or r.get("last_price") or 0)
        pivot = float(r.get("pivot") or 0)
        if price <= 0 or pivot <= 0:
            return out
        trs = [float(x) for x in (r.get("tranches") or []) if x]
        kl = r.get("key_levels") or {}
        h4l = r.get("h4_levels") or {}
        behav = r.get("behav") or {}
        _st = r.get("stop")
        stop0 = (float(_st[0]) if isinstance(_st, (list, tuple)) and _st
                 else (float(_st) if isinstance(_st, (int, float)) else None))
        res_minor, res_major = kl.get("res_minor"), kl.get("res_major")
        sup_major = kl.get("sup_major") or round(pivot, 2)
        sup_minor = kl.get("sup_minor")
        targets = [float(t) for t in (r.get("t1"), r.get("t2"), r.get("t3")) if t]
        top_tr = max(trs) if trs else price

        # ---- setup_type
        if price < pivot * 0.995:
            setup = "support_reclaim"
        elif price > top_tr * 1.05:
            setup = "extended_risk"
        elif behav.get("sweeps", 0) >= 1 and h4l.get("sweep_low"):
            setup = "liquidity_sweep"
        elif h4l.get("flip") and abs(h4l["flip"] / price - 1.0) <= 0.05:
            setup = "h4_reclaim"
        else:
            setup = "pivot_reversal"
        out["setup_type"] = setup

        # ---- §10 خط الترند الهابط (حاجز إضافي — عرض/تفسير، لا يمسّ الأهداف نفسها)
        tl = r.get("trendline") or {}
        tl_px = (float(tl["line_price_now"])
                 if tl.get("line_price_now")
                 and tl.get("state") in ("below", "testing") else None)
        if tl:
            out["trendline_pressure"] = tl

        # ---- الرقم الحرج (رقم حسم واحد = **أقرب** حاجز فوق السعر، مواصفة §3)
        crit = None
        if price < pivot * 0.995:
            crit = {"price": round(float(sup_major), 2), "type": "reclaim_level",
                    "why": "استعادته تعيد فكرة الارتكاز"}
        else:
            cands = [float(b) for b in (
                res_minor, res_major, (h4l.get("resistances") or [None])[0],
                tl_px) if b and float(b) > price * 1.01]
            barrier = min(cands) if cands else None
            if barrier is None:
                up = [t for t in targets if t > price * 1.01]
                barrier = min(up) if up else None
            if barrier:
                why = ("إغلاق فوقه يكسر خط الترند الهابط ويفعّل الهدف التالي"
                       if tl_px is not None and barrier == tl_px
                       else "تجاوزه يفعّل الهدف التالي")
                crit = {"price": round(barrier, 2), "type": "breakout_activation",
                        "why": why}
        out["critical_number"] = crit

        # ---- activation_state (وسم على الأهداف الحالية فقط — لا يعيد حسابها)
        gate = crit["price"] if crit and crit["type"] == "breakout_activation" else None
        active = [t for t in targets if not (gate and t > gate * 1.02)]
        pending = [t for t in targets if gate and t > gate * 1.02]
        if stop0 and price <= stop0:
            a_state = "high_risk"
        elif setup == "support_reclaim":
            a_state = "waiting_reclaim"
        else:
            a_state = "active"
        out["activation_state"] = {"setup": a_state, "active_targets": active,
                                   "inactive_targets": pending,
                                   "blocked_by": (gate if pending else None)}

        # ---- entry_mode (وصفي — sweep وصفًا لا شرطًا)
        lo_z = round(min(trs), 2) if trs else round(pivot, 2)
        hi_z = round(max(trs), 2) if trs else round(price, 2)
        if stop0 and price <= stop0:
            mode, ereason = "no_entry_far", "كسر الوقف — الفكرة ملغاة/خطرة"
        elif price < pivot * 0.995:
            mode, ereason = "reclaim_wait", "تحت الدعم — ننتظر استعادته"
        elif price > hi_z * 1.05:
            mode, ereason = "no_entry_far", "بعيد فوق منطقة الدفعات"
        elif setup == "liquidity_sweep":
            mode, ereason = "sweep_confirmed", "مسح تحت الدعم ثم استعادة"
        else:
            mode, ereason = "near_support", "داخل/قرب منطقة الدفعات"
        out["entry_mode"] = {"mode": mode, "entry_zone": [lo_z, hi_z],
                             "stop": (round(stop0, 2) if stop0 else None),
                             "reason": ereason}

        # ---- four_hour_context (من h4_levels — بلا وقف تكتيكي)
        if h4l:
            red_head = (h4l.get("resistances") or [None])[0]
            flip = h4l.get("flip")
            gcov = h4l.get("green_cover")     # المقطع: تغطية الخضرا = تأكيد
            if red_head and red_head > price:
                h4state = "blocked_by_red_head"
            elif flip and flip <= price * 1.01:
                h4state = "support_flipped"
            elif gcov is False:
                h4state = "waiting_green_cover"   # حمرا أخيرة بلا تغطية = ننتظر
            elif h4l.get("sweep_low"):
                h4state = "confirming"
            else:
                h4state = "weak"
            out["four_hour_context"] = {
                "state": h4state, "red_candle_head": red_head, "flip": flip,
                "sweep_low": h4l.get("sweep_low"), "green_cover": gcov}

        # ---- risk_profile (تجميع التحذيرات الموجودة — بلا تجريم الفلوت/الرسملة)
        flags = []
        wtext = " ".join(str(w) for w in (r.get("warnings") or []))
        if "تخفيف" in wtext or "طرح" in wtext:
            flags.append("خبر تخفيف/طرح")
        if r.get("recent_split"):
            flags.append("تقسيم حديث")
        if r.get("sec_filings"):
            flags.append("ملفات SEC")
        if "الصين" in wtext or "هونغ" in wtext:
            flags.append("صيني/هونغ كونغ")
        if "مشنوق" in wtext:
            flags.append("شمعة انعكاس (المشنوق)")
        if price > sup_major * 1.15:
            flags.append("بعيد عن الدعم")
        out["risk_profile"] = {
            "risk_level": ("منخفض", "متوسط", "مرتفع", "شديد")[min(len(flags), 3)],
            "flags": flags}

        # ---- §11 cycle_context (عرض/تخزين فقط — لا يدخل أي ترتيب أو اختيار)
        rec = behav.get("recency_bars")
        cyc = {"days_since_last_impulse": rec,
               "days_since_major_low": r.get("bars_after")}
        if rec is not None:
            if rec <= 29:
                cyc["window_state"] = "رفعة حديثة (أقل من 30 جلسة)"
            elif rec <= 50:
                cyc["window_state"] = ("داخل النافذة الشائعة لإعادة الرفع "
                                       "(30-50 جلسة)")
            else:
                cyc["window_state"] = "خمول أطول من النافذة الشائعة"
        out["cycle_context"] = cyc

        # ---- §12 session_context (نسخة دنيا صادقة — snapshot المتاح فعلًا من enrich؛
        #      ما قبل/بعد السوق غير متاح بمسارنا → سبب صريح، لا تخمين)
        if r.get("session_ctx"):
            out["session_context"] = r["session_ctx"]

        # ---- §13 وسوم 🧬 الإضافية (وصفية، عند توفّر الدليل فقط)
        btags = behavior_tags(behav)
        if btags:
            out["behavior_tags"] = btags

        # ---- level_roles (بنية داخلية/تقرير — لا الكرت المختصر)
        roles = [{"price": round(float(sup_major), 2), "role": "support",
                  "note": "دعم أساسي (الأرضية)"}]
        if sup_minor:
            roles.append({"price": sup_minor, "role": "support", "note": "دعم فرعي"})
        if stop0:
            roles.append({"price": round(stop0, 2), "role": "stop_source",
                          "note": "الوقف"})
        if res_minor:
            roles.append({"price": res_minor, "role": "resistance",
                          "note": "مقاومة فرعية"})
        if res_major and res_major != res_minor:
            roles.append({"price": res_major, "role": "resistance",
                          "note": "مقاومة أساسية"})
        # مصدر كل هدف (P1-4 — **استدلال بالمطابقة** على المستويات المعروفة وقت
        # التفسير، عرض فقط: لا يغيّر الأهداف ولا يدّعي دقة أعلى من الواقع؛
        # ما لا يطابق مصدرًا معروفًا = «سلّم المقاومات اليومي» الافتراضي الصادق)
        def _target_source(tv):
            t2 = round(float(tv), 2)
            if res_minor is not None and abs(t2 - round(res_minor, 2)) < 0.005:
                return "المقاومة الفرعية (قمة يومية)"
            if res_major is not None and abs(t2 - round(res_major, 2)) < 0.005:
                return "المقاومة الأساسية (منشأ الهبوط)"
            for x in (h4l.get("resistances") or []):
                if abs(t2 - round(float(x), 2)) < 0.005:
                    return "رأس شمعة حمرا 4س"
            _lib = r.get("liberation")
            if _lib and abs(t2 - round(float(_lib), 2)) < 0.005:
                return "مستوى التحرر"
            for z in ((r.get("gaps_above") or {}).get("zones") or []):
                if (isinstance(z, dict) and z.get("bottom")
                        and abs(t2 - round(float(z["bottom"]), 2)) < 0.005):
                    return "حافة فجوة فوقية"
            return "سلّم المقاومات اليومي"

        tsrc = []
        for i, t in enumerate(targets, 1):
            src = _target_source(t)
            st_t = "active" if t in active else "pending"
            roles.append({"price": t, "role": "target", "state": st_t,
                          "note": f"الهدف {i}", "src": src})
            tsrc.append({"price": round(float(t), 2), "source": src,
                         "activation": st_t,
                         "blocked_by": (gate if st_t == "pending" else None)})
        out["targets_src"] = tsrc
        if crit:
            roles.append({"price": crit["price"], "role": "critical_number",
                          "note": crit["why"]})
        out["level_roles"] = roles
    except Exception:
        pass
    return out


def interp_card_lines(interp: dict) -> list:
    """أسطر التفسير المدمجة بالكرت (≤4، عربي مبسّط بلا علامات مقارنة). عرض فقط.
    السطر الرابع = قصة شموع الـ4س من المقطع (رأس الحمرا مقاومة/الدعم المنقلب/
    ذيل المسح) — يظهر عند وجود حالة ذات معنى فقط (weak لا يُعرض)."""
    if not interp:
        return []
    lines = []
    st = interp.get("setup_type")
    em = interp.get("entry_mode") or {}
    if st:
        seg = f"🧭 الإعداد: {_SETUP_AR.get(st, st)}"
        if em.get("mode"):
            seg += f" · الدخول: {_ENTRY_AR.get(em['mode'], em['mode'])}"
        lines.append(seg)
    cr = interp.get("critical_number")
    if cr and cr.get("price"):
        lines.append(f"🎯 الرقم الحرج: ${cr['price']:.2f} ({cr.get('why', '')})")
    # 🕓 سياق الـ4 ساعات (قصة الشموع — فيصل: «رأس الحمرا مقاومة، تجاوزه يؤكّد»
    # و«تغطية الحمرا بخضرا تعطي تأكيد»)
    h4c = interp.get("four_hour_context") or {}
    h4s = h4c.get("state")
    if h4s == "blocked_by_red_head" and h4c.get("red_candle_head"):
        _gc = " · الحمرا الأخيرة مغطّاة بخضرا" if h4c.get("green_cover") else ""
        lines.append(f"🕓 4س: رأس الشمعة الحمرا ${h4c['red_candle_head']:.2f} "
                     f"مقاومة — تجاوزه يؤكّد{_gc}")
    elif h4s == "support_flipped" and h4c.get("flip"):
        lines.append(f"🕓 4س: مقاومة انقلبت دعمًا قرب ${h4c['flip']:.2f}")
    elif h4s == "waiting_green_cover":
        lines.append("🕓 4س: الشمعة الحمرا الأخيرة بلا تغطية خضرا — ننتظر التأكيد")
    elif h4s == "confirming" and h4c.get("sweep_low"):
        lines.append(f"🕓 4س: ذيل مسح عند ${h4c['sweep_low']:.2f} ثم استعادة "
                     "(تأكيد)")
    rp = interp.get("risk_profile") or {}
    if rp.get("flags") and rp.get("risk_level") != "منخفض":
        lines.append(f"⚠️ الخطر: {rp['risk_level']} ({' · '.join(rp['flags'][:3])})")
    return lines


def build_message(results: list, splits: list,
                  title="🎯 <b>فارز أسهم الارتكاز</b>", subnote=None) -> str:
    """بطاقات الترشيح الكاملة (تُستخدم يوم تجديد القائمة)"""
    today = dt.date.today().isoformat()
    lines = [f"{title} — {today}",
             f"العدد: {len(results)} (الجاهز أولاً)"]
    # مؤشر صحة البيانات (يكشف خنق Yahoo بدل ما تنقص الأسهم بصمت)
    uni, val = _SCAN_STATS.get("universe"), _SCAN_STATS.get("valid")
    if uni and val is not None:
        cov = val / uni * 100.0
        if cov < CONFIG["DATA_HEALTH_MIN_PCT"]:
            lines.append(f"⚠️ تغطية بيانات {cov:.0f}% ({val}/{uni}) — "
                         "Yahoo خنق الطلبات، قد تنقص أسهم")
        else:
            lines.append(f"⚙️ تغطية بيانات {cov:.0f}% ({val}/{uni}) ✓")
    if subnote:
        lines.append(subnote)
    lines.append("")
    if not results:
        lines.append("لا توجد أسهم تطابق الشروط اليوم. ✋")
        if _REJECT_STATS:   # تشخيص مباشر: أكثر البوابات رفضًا
            top = sorted(_REJECT_STATS.items(), key=lambda x: -x[1])[:6]
            lines.append("🔎 أكثر بوابة رفضت اليوم: "
                         + " · ".join(f"{esc(k)}={v}" for k, v in top))
    for r in results:
        # ===== بطاقة مختصرة ومرتّبة (v2.9): كل معلومة مهمّة بسطرها،
        #   والصغيرة (فلوت/شورت/قطاع) تتجمّع بسطر واحد. عرض فقط — لا يمسّ الحساب. =====
        tier = r.get("tier", "B")
        badge = "🎯"        # 🪦 A/B متقاعد → شارة موحّدة «ارتكاز مؤهّل»؛ الجاهزية بالوسم التالي
        price = r["price"]
        lines.append("━━━━━━━━━━━━━━━")
        # الرأس: الرمز + حالة الجاهزية (🟢🟡🔴 + الكلمة) + النسبة /100
        rdy = r.get("readiness")
        if rdy is not None:
            lines.append(f"{badge} <b>${r['symbol']}</b>  ·  "
                         f"{readiness_tag(rdy)} {rdy}/100")
        else:
            lines.append(f"{badge} <b>${r['symbol']}</b>")
        # القوة العامة + شريط بصري
        bar, slabel = strength_bar(r.get("score", 0))
        lines.append(f"💪 القوة العامة: {r.get('score', 0)}/100  {bar}  {slabel}")
        # 🟢👀 حالة الدخول العملية (جاهز للدخول الآن / متابعة + السبب) — من موقع السعر
        _es = entry_status(r)
        lines.append(_es["label"] + (f" — {_es['reason']}" if _es["reason"] else ""))
        # 🧬 طريقة ارتفاع اليد (سلوك المضارب — **عرض/تشخيص فقط، لا يمسّ الفرز ولا الاختيار**):
        # كيف رفع المضاربُ السهمَ تاريخيًا (كم مرّة · أكبر رفعة · بصمة المسح). فيصل: البصمة تتكرّر.
        bh = r.get("behav") or {}
        if bh.get("score") is not None:
            det = []
            if bh.get("n_pumps"):
                det.append(f"رفع {bh['n_pumps']} مرّة")
            if bh.get("best_pump"):
                det.append(f"أكبر {bh['best_pump']:.0f}%")
            if bh.get("sweeps"):
                det.append(f"مسح {bh['sweeps']} مرّة")
            det += behavior_tags(bh)      # §13: وسوم وصفية (صيد وقفات/خمول طويل)
            tail = (" (" + " · ".join(det) + ")") if det else ""
            lines.append(f"🧬 طريقة الارتفاع: {bh['score']}/100 · {bh['label']}{tail}")
        # (🔬 التجميع الصامت أُزيل من العرض — تجربة T-ACC فشلت بالسنتين، غير مميِّز)
        # 🕵️ لوحة علامات اليد (تجميع قرائن مضارب — يظهر عند دليلين فأكثر)
        _he = hand_evidence_line(r)
        if _he:
            lines.append(_he)
        # المعلومات الصغيرة بسطر واحد (سعر · فلوت · شورت · قطاع · دولة)
        small = [f"${price:.2f}"]
        # فلوت/شورت: لو تعذّر الجلب من كل المصادر نعرض شرطة «—» (وضوح: تعذّر
        # الجلب ≠ صفر) بدل إخفاء الحقل بصمت (طلب المستخدم 2026-06-24).
        small.append(f"فلوت {fmt_money(r['float'])}" if r.get("float") else "فلوت —")
        # «شورت» = المتاح من ChartExchange (قراءة فيصل) ← الحجم اليومي ← نسبة ← «—».
        small.append(_short_headline(r))
        sec = r.get("sector") or r.get("industry")
        if sec:
            small.append(esc(ar_sector(sec)))
        if r.get("country"):
            small.append(country_label(r["country"]))
        lines.append("💰 " + " · ".join(small))
        # 🔒 معدّل الاقتراض (فيصل: أساس الارتكاز · اقتراض صعب = وقود سكويز) — يظهر عند
        # توفّره فقط (غالبًا يُحجب Fintel؛ لا نحشو «—» بسطر مستقل لكل كرت). عرض/سياق فقط.
        if r.get("borrow_fee") is not None or r.get("shares_available") is not None:
            lines.append(borrow_line(r))
        # 📊 الشورت الرسمي (SI) + أيام التغطية (🎬 فيديو DSY — فيصل قرأهما من Fintel)
        _sil = short_interest_line(r)
        if _sil:
            lines.append(_sil)
        # 🎬 KST 4س (حالة زخم مساندة من فيديو فيصل) — يظهر عند توفّره فقط
        if r.get("kst4"):
            lines.append(f"📈 KST (4س): {r['kst4']}")
        # 💧 سبريد/سيولة (🎬 فيصل يبدأ بدفتر الأوامر) — يظهر فقط لو NBBO حاضر (نادر بالكرت)
        _spl = spread_line(r.get("bid"), r.get("ask"), r.get("session"))
        if _spl:
            lines.append(_spl)
        # 📅 الأحداث المعلنة القادمة (أرباح/تجارب — يوم الانفجار المحتمل، فيصل 9428)
        lines += events_lines(r.get("upcoming_events"))
        lines += interp_card_lines(r.get("interp"))   # 🧭 التفسير/القرار (عرض فقط)
        # D10: تدوير الفلوت (سكويز) — يظهر عند تجاوز 100% فقط
        rot = r.get("rotation_pct")
        if rot and rot >= 100:
            lines.append(f"🔄 تدوير اليوم ≈ {rot:.0f}% من الفلوت (إشارة سكويز)")

        # ===== مجموعة الدخول / الدعم / الوقف =====
        lines.append("")
        _trs = r.get("tranches") or [r["entry"][0], r["entry"][1]]
        lines.append("📥 الشراء (دفعات): "
                     + " · ".join(f"${p:.2f}" for p in _trs))
        kl = r.get("key_levels") or {}
        pivot = r.get("pivot")
        sup_major = kl.get("sup_major") or pivot
        if sup_major:
            lines.append(f"🟢 الدعم الأساسي: ${sup_major:.2f}")
        if kl.get("sup_minor"):
            lines.append(f"🟢 الدعم الفرعي: ${kl['sup_minor']:.2f}")
        stop_lo = r["stop"][0]
        lines.append(f"⛔ وقف خسارة: ${stop_lo:.2f}")

        # ===== مجموعة الأهداف / المقاومات / التحرر =====
        lines.append("")
        res_minor = kl.get("res_minor")
        res_major = kl.get("res_major")
        targets = (r["t1"], r["t2"], r["t3"])
        # وسم «(معلّق حتى $X)» للهدف خلف حاجز غير مكسور (طبقة التفسير §9 —
        # وسم عرض فقط: الأهداف نفسها لا تتغيّر ولا تُحذف، قفل D5)
        _as = (r.get("interp") or {}).get("activation_state") or {}
        _blk = _as.get("blocked_by")
        _pend = {round(float(t), 2) for t in (_as.get("inactive_targets") or [])}
        for i, tv in enumerate(targets, 1):
            is_minor = (res_minor is not None
                        and abs(round(tv, 2) - round(res_minor, 2)) < 0.005)
            suffix = " (مقاومة فرعية)" if is_minor else ""
            if _blk and round(tv, 2) in _pend:
                suffix += f" (معلّق حتى ${_blk:.2f})"
            lines.append(f"🎯 الهدف {i}{suffix}: ${tv:.2f}")
        # المقاومة الفرعية لو ما طابقت أي هدف معروض (لا تكرار)
        minor_shown = res_minor is not None and any(
            abs(round(tv, 2) - round(res_minor, 2)) < 0.005 for tv in targets)
        if res_minor is not None and not minor_shown:
            lines.append(f"🔴 المقاومة الفرعية: ${res_minor:.2f}")
        # المقاومة الأساسية: مستوى أعلى متميّز فوق الهدف الثالث (إلا لو = التحرر)
        lib = r.get("liberation")
        dup_lib = (lib is not None and res_major is not None
                   and abs(round(res_major, 2) - round(lib, 2)) < 0.005)
        if res_major is not None and res_major > targets[-1] * 1.005 and not dup_lib:
            lines.append(f"🔴 المقاومة الأساسية: ${res_major:.2f}")
        if lib:
            ctag = " 🔓 قريب!" if r.get("lib_near") else ""
            lines.append(f"🚀 تحرر فوق ${lib:.2f}{ctag}")
        if any("Williams" in f for f in (r.get("flags") or [])):
            lines.append("⚡ دخول المضارب ✓ (إشارة زخم للدخول)")

        # ===== مجموعة العائد / البوابات / التنبيهات =====
        lines.append("")
        lines.append(f"⚖️ ربح/مخاطرة: {r['rr']:.1f}×")
        if tier == "B":
            sf = r.get("soft_fails", [])
            if sf:
                lines.append(f"🅱️ البوابات الناقصة ({len(sf)} من 14):")
                for i, f in enumerate(sf, 1):
                    lines.append(f"   {i}- {f}")
            else:
                lines.append("🅱️ مراقبة")
        else:
            lines.append("✅ اجتاز 14/14 بوابة")
        _tfi = timeframes_info(r.get("tf_count"), r.get("tf_display"))
        if _tfi:
            lines.append(_tfi)
        # تنبيهات حرجة تبقى (تقسيم عكسي / SEC أحمر / تحذيرات تخفيف-جغرافي)
        if r.get("recent_split"):
            lines.append(f"✂️ تقسيم عكسي {r['recent_split'][0]}")
        red = [x for x in (r.get("sec_filings") or []) if "🔴" in x]
        if red:
            lines.append("📋 " + esc(red[0]))
        if r.get("warnings"):
            lines.append("⚠️ " + "؛ ".join(esc(w) for w in r["warnings"]))
        lines.append(news_links_compact(r["symbol"]))
    lines += ["", FOOTER]
    return _rtl_join(lines)


def code_version() -> str:
    """رقم إصدار الكود (SHA قصير) — يُختم في كل رسالة حتى تُعرف النسخة فورًا
    ولا تختلط برسائل تشغيلات قديمة. GitHub Actions يضبط GITHUB_SHA."""
    return (os.environ.get("GITHUB_SHA") or "").strip()[:7] or "local"


def _chunk_message(text: str, limit: int = 3800) -> list:
    """تقسيم الرسالة على الأسطر ضمن حدّ تيليجرام. السطر الطويل جدًا **وبلا وسوم
    HTML** يُقسَّم على أقرب مسافة (آمن — لا نقسم سطرًا فيه «<...>» حتى لا ينكسر
    الوسم). احتياط نادر يمنع رفض الرسالة لو طال سطر بشكل غير متوقّع."""
    chunks, cur = [], ""
    for ln in text.split("\n"):
        while len(ln) > limit and "<" not in ln:
            cut = ln.rfind(" ", 0, limit)
            if cut <= 0:
                cut = limit
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(ln[:cut])
            ln = ln[cut:].lstrip(" ")
        if len(cur) + len(ln) + 1 > limit:
            if cur:
                chunks.append(cur)
            cur = ln
        else:
            cur = cur + "\n" + ln if cur else ln
    if cur:
        chunks.append(cur)
    return chunks


def send_telegram(text: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        log("ℹ️ لا يوجد توكن تيليجرام — الطباعة على الشاشة فقط:")
        print("\n" + text.replace("<b>", "").replace("</b>", "")
              .replace("<i>", "").replace("</i>", "") + "\n")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    # دعم أكثر من مستلم: TELEGRAM_CHAT_ID يقبل عدة أرقام مفصولة بفاصلة
    # (لإضافة أصدقاء يستقبلون نفس الرسائل). رقم واحد يشتغل عادي.
    recipients = [c.strip() for c in TELEGRAM_CHAT.replace(";", ",").split(",")
                  if c.strip()]
    chunks = _chunk_message(text)
    # ختم الإصدار في كل رسالة (تعريف النسخة فورًا — ضمان ضد لبس الرسائل القديمة)
    stamp = f"\n🧾 إصدار {code_version()} · {dt.date.today().isoformat()}"
    chunks = [c + stamp for c in chunks]
    ok = True
    for ch in chunks:
        for cid in recipients:
            try:
                resp = requests.post(url, json={
                    "chat_id": cid, "text": ch,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True}, timeout=30)
                if resp.status_code != 200:
                    log(f"⚠️ تيليجرام رفض ({cid}): {resp.text[:200]}")
                    ok = False
            except Exception as e:
                log(f"⚠️ خطأ تيليجرام ({cid}): {e}")
                ok = False
        time.sleep(1)
    return ok


def _admin_chat() -> list:
    """المستلم المشرف (أول رقم) فقط — لا يُرسل الملفات للأصدقاء."""
    recips = [c.strip() for c in TELEGRAM_CHAT.replace(";", ",").split(",")
              if c.strip()]
    return recips[:1]


def send_telegram_document(path: str, caption: str = "") -> bool:
    """يرسل ملفًا (CSV) للمشرف فقط (يبقى بمحادثته للأبد حتى لو ضاع القرص)."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        log(f"ℹ️ (بلا تيليجرام) ملف جاهز: {path}")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
    ok = True
    for cid in _admin_chat():
        try:
            with open(path, "rb") as fh:
                resp = requests.post(url, data={"chat_id": cid,
                                                "caption": caption[:1000]},
                                     files={"document": fh}, timeout=60)
            if resp.status_code != 200:
                log(f"⚠️ sendDocument رفض ({resp.status_code}): {resp.text[:160]}")
                ok = False
        except Exception as e:
            log(f"⚠️ خطأ sendDocument: {e}")
            ok = False
    return ok


def _write_csv_file(rows: list, prefix: str):
    """يكتب صفوفًا إلى CSV ويرجع المسار (أو None لو فاضي/فشل)."""
    if not rows:
        return None
    try:
        fn = f"{prefix}_{dt.date.today().isoformat()}.csv"
        pd.DataFrame(rows).to_csv(fn, index=False, encoding="utf-8-sig")
        return fn
    except Exception as e:
        log(f"⚠️ كتابة CSV {prefix}: {e}")
        return None


def export_weekly_csvs(wl: dict, picks: list, alert_data: dict = None) -> None:
    """يصدّر 3 ملفات CSV للمشرف يوم التجديد (الجمعة بعد الإغلاق): الصفقات المحسومة · الإشارات الحالية ·
    الفرص الفائتة. (البيانات محفوظة أصلًا في git؛ هذا للراحة وسهولة التحليل.)"""
    d = dt.date.today().isoformat()
    cols_t = ("symbol", "tier", "sector", "rsi", "float", "short", "drop_pct",
              "best_spike", "rr", "score", "max_gain_pct", "status", "hit",
              "hit_date", "added", "removal_reason")
    trades = [{k: r.get(k) for k in cols_t}
              for r in _dedup_closed(_collect_closed(wl)
                                     + _collect_closed_alerts(alert_data))]
    def _stop0(r):
        st = r.get("stop")
        try:
            return round(st[0], 2)
        except Exception:
            return round(st, 2) if isinstance(st, (int, float)) else st


    signals = [{"symbol": r["symbol"], "tier": r.get("tier"),
                "sector": r.get("sector"), "rsi": r.get("rsi"),
                "float": r.get("float"),
                # تدرّج الشورت مثل short_line: حجم Fintel ← FINRA ← (نسبة Yahoo
                # بعمود منفصل). كان يكتب finra_short فقط فيظهر فارغًا رغم توفّر
                # short_pct (مثل UPB). إصلاح فحص 2026-06-26 — تصدير فقط.
                "short": ((r.get("fintel") or {}).get("short_volume")
                          or r.get("finra_short")),
                "short_pct": r.get("short_pct"),
                "drop_pct": round(r.get("drop_pct", 0), 1),
                "best_spike": round(r.get("best_spike", 0), 0),
                "rr": r.get("rr"), "score": r.get("score"),
                "pivot": round(r["pivot"], 2), "stop": _stop0(r),
                "t1": round(r["t1"], 2), "t2": round(r["t2"], 2),
                "t3": round(r["t3"], 2)} for r in picks]
    for rows, prefix, cap in [
            (trades, "trades", "📎 الصفقات المحسومة ونتائجها"),
            (signals, "signals", "📎 كل الإشارات (القائمة الحالية)"),
            (list(_MISSED), "missed", "📎 الفرص الفائتة (مرفوض صعد)")]:
        fn = _write_csv_file(rows, prefix)
        if fn:
            send_telegram_document(fn, f"{cap} — {d}")


# ==========================================================
# 9) نظام القائمة الأسبوعية الثابتة (v2.0)
# ==========================================================
WATCH_FILE = "weekly_watchlist.json"   # ملف ذاكرة القائمة في الـ repo
COMPANY_FILE = "company_cache.json"    # ذاكرة آخر قطاع/دولة معروفة لكل سهم
IGNITION_LOG_FILE = "ignition_log.json"  # 📏 سجلّ إطلاقات رادار الانطلاق (قياس الحافة)
IGNITION_UNI_FILE = "ignition_universe.json"  # ⑩ مقام الالتقاط: أسهم كل جلسة رادار
COMPANY_CACHE_MAX = 5000               # حدّ علوي سخيّ لذاكرة الشركات (LRU)
# 🔄 التجديد الأسبوعي مدفوع بإشارة الجدولة (RENEW_ON_CLOSE) لا بيوم الأسبوع:
# الـworkflow يشغّل جوب تجديد **الجمعة 22:00 UTC = بعد إغلاق السوق الأمريكي**
# (الإغلاق 20:00 صيفًا/21:00 شتاءً UTC) → الشمعة الأسبوعية مكتملة (اثنين→جمعة)
# لبوابة M6/الفجوات/الأهداف الأسبوعية. قرار المستخدم 2026-07-09: «ابيه يبدأ بعد
# إغلاق الجمعة». صباح الجمعة كان يقرأ إغلاق الخميس فقط = أسبوعي ناقص يوم.


def _load_company_cache() -> dict:
    if os.path.exists(COMPANY_FILE):
        try:
            with open(COMPANY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _json_default(o):
    """🛡️ شبكة أمان تسلسل «قاعدة البيانات» (إصلاح حادثة 2026-07-09 — فقدان صامت):
    قيم numpy تتسرّب أحيانًا لحقول مخزَّنة فتفجّر json.dump ويضيع **حفظ القائمة
    كاملًا** بصمت (سجلّ الأكشن: «Object of type bool is not JSON serializable» →
    ضاعت إضافات اليوم GEOS/FEMY/DTI/PTN — انفجار «قفزة» حمل suspect_split كـnp.bool).
    نحوّل عائلة numpy لأنواع بايثون + التواريخ isoformat، وأي نوع مجهول آخر → str
    (حقل غريب مقروء أهون بكثير من ضياع القائمة كلها — درس الحادثة)."""
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (dt.date, dt.datetime)):
        return o.isoformat()
    return str(o)


def _atomic_write_json(path: str, data) -> None:
    """كتابة ذرّية: نكتب لملف مؤقت ثم نستبدله دفعة واحدة (os.replace).
    لا يبقى أبدًا ملف نصف-مكتوب/تالف لو انقطع التشغيل أو تزامن تشغيلان —
    حماية «قاعدة البيانات» من الفقدان الصامت. `default=_json_default` = شبكة
    أمان ضد أنواع numpy المتسرّبة (حادثة 2026-07-09)."""
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, default=_json_default)
    os.replace(tmp, path)


def _save_company_cache(cache: dict) -> None:
    try:
        # حدّ علوي سخيّ (LRU): نُبقي آخر COMPANY_CACHE_MAX رمزًا تم إثراؤه
        # (الأحدث في النهاية). الأسهم النشطة تُثرى في كل تجديد فتبقى ضمن الأحدث
        # ولا تُطرد بياناتها (تغطية ثابتة محفوظة) — يمنع النمو غير المحدود فقط.
        if len(cache) > COMPANY_CACHE_MAX:
            items = list(cache.items())[-COMPANY_CACHE_MAX:]
            cache.clear()
            cache.update(items)
        _atomic_write_json(COMPANY_FILE, cache)
    except Exception as e:
        log(f"⚠️ حفظ ذاكرة الشركات: {e}")


def _or_cache(val, cached, key):
    """يرجّع القيمة المجلوبة إن وُجدت، وإلا آخر قيمة معروفة من الذاكرة."""
    return val if val not in (None, "") else cached.get(key)


COMPANY_CACHE = _load_company_cache()


def _dedup_history(history: list) -> list:
    """N2 (2026-07-04): يبقي **أحدث** إدخال أرشيف لكل `week_start` (الأحدث = آخر
    إضافة) مع الحفاظ على ترتيب أول ظهور — يمنع تكرار الأسبوع نفسه عبر تشغيلات
    متعددة (كان `2026-06-21` مكرَّرًا ×9). الإدخالات بلا `week_start` تبقى مستقلة.
    طبقة ذاكرة/أرشيف فقط — لا تمسّ الفرز/الدخول/الوقف/الأهداف."""
    if not isinstance(history, list) or len(history) < 2:
        return history if isinstance(history, list) else []
    latest, order = {}, []
    for i, h in enumerate(history):
        wk = h.get("week_start") if isinstance(h, dict) else None
        key = wk if wk else ("__none__", i)   # بلا week_start = يبقى مستقلًا
        if key not in latest:
            order.append(key)
        latest[key] = h                        # الأحدث بنفس الأسبوع يفوز
    return [latest[k] for k in order]


def load_watchlist() -> dict:
    if os.path.exists(WATCH_FILE):
        try:
            with open(WATCH_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log(f"⚠️ قراءة ملف القائمة: {e}")
    return {"week_start": None, "created": None, "stocks": [],
            "removed": [], "replacements_log": [], "notes": [],
            "history": []}


def save_watchlist(wl: dict) -> None:
    # حدود نمو: تُقصّ السجلّات التراكمية عند كل حفظ (لا تنتظر يوم التجديد)
    # حتى لا تنمو بلا حدّ لو تأخّر/تخطّى التجديد. لا تمسّ الأسهم النشطة.
    for _k, _cap in (("notes", 250), ("removed", 120), ("replacements_log", 120)):
        _lst = wl.get(_k)
        if isinstance(_lst, list) and len(_lst) > _cap:
            wl[_k] = _lst[-_cap:]
    # N2: أرشيف history — إزالة تكرار الأسبوع (أحدث إدخال يفوز) + قصّ لـ26.
    # ينظّف التلوّث القديم على أول حفظ ويمنع تكراره مستقبلًا (ذاتي الشفاء).
    _h = wl.get("history")
    if isinstance(_h, list) and _h:
        wl["history"] = _dedup_history(_h)[-26:]
    try:
        _atomic_write_json(WATCH_FILE, wl)
    except Exception as e:
        log(f"⚠️ حفظ ملف القائمة: {e}")


def should_renew(wl: dict, force: bool = False,
                 renew_signal: bool = False) -> bool:
    """متى نفرز السوق كاملاً ونبني قائمة جديدة:
    - renew_signal=True: جوب التجديد الأسبوعي (الجمعة 22:00 UTC بعد إغلاق
      السوق) — يمرّره الـworkflow عبر RENEW_ON_CLOSE. الشمعة الأسبوعية مكتملة
      (اثنين→جمعة) فتُبنى القائمة على أسبوع كامل.
    - قائمة فارغة = تأسيس فوري (أي يوم). | FORCE_RENEW=1 = إجبار يدوي.
    القائمة ثابتة دائمة: باقي التشغيلات = متابعة + إضافة الجديد فقط (لا رفرفة)."""
    if force:
        return True
    if not wl.get("stocks") and not wl.get("removed"):
        return True  # أول تشغيل — تأسيس فوري
    return renew_signal


def make_watch_entry(r: dict, today_iso: str) -> dict:
    """تحويل نتيجة تحليل إلى سجل سهم في القائمة الأسبوعية"""
    return {
        "symbol": r["symbol"], "added": today_iso,
        # ① تاريخ شمعة الترشيح الفعلية (لا تاريخ التشغيل) — مرجع نافذة التقييم.
        "ref_bar": r.get("ref_bar"),
        "entry_ref": round(r["price"], 4),
        "entry": [round(r["entry"][0], 4), round(r["entry"][1], 4)],
        "tranches": [round(p, 4) for p in (r.get("tranches") or r["entry"])],
        "pivot": round(r["pivot"], 4),
        "stop": round(r["stop"][0], 4),        # الوقف الأبعد (~7% تحت القاع)
        "stop_hi": round(r["stop"][1], 4),
        "t1": round(r["t1"], 4), "t2": round(r["t2"], 4),
        "t3": round(r["t3"], 4),
        "score": r["score"], "flags": list(r["flags"]),
        "rsi": r.get("rsi"), "float": r.get("float"),      # سمات للتعلم
        "short": r.get("finra_short"), "short_pct": r.get("short_pct"),
        "short_interest": r.get("short_interest"),         # 📊 SI الرسمي (🎬 فيديو DSY)
        "days_to_cover": r.get("days_to_cover"),           # 📊 أيام التغطية (🎬 فيديو DSY)
        "kst4": r.get("kst4"),                             # 🎬 حالة KST 4س (عرض/سياق)
        "borrow_fee": r.get("borrow_fee"),                 # 🔒 رسوم الاقتراض (فيصل: سكويز)
        "shares_available": r.get("shares_available"),     # 🔒 الأسهم المتاحة للاقتراض
        "company_name": r.get("company_name"),             # 📅 لمطابقة راعي التجارب
        "upcoming_events": r.get("upcoming_events"),       # 📅 أحداث معلنة (أرباح/تجارب)
        "proxy_filing": r.get("proxy_filing"),             # 📅 دعوة اجتماع مساهمين (SEC)
        "first_trade": r.get("first_trade"),               # 📅 أول تداول (تقدير الحظر)
        "rotation_pct": r.get("rotation_pct"),             # D10: تدوير الفلوت (سكويز)
        "drop_pct": r.get("drop_pct"), "best_spike": r.get("best_spike"),
        "rr": r.get("rr"),
        "tier": r.get("tier", "B"),                       # 🪦 A متقاعد: B مؤهّل · W ارتداد
        "soft_fails": list(r.get("soft_fails", [])),
        "warnings": list(r.get("warnings", [])),          # تحذيرات (تخفيف/جغرافي)
        "news_risk": bool([w for w in r.get("warnings", [])
                           if "تخفيف" in w or "طرح" in w]),  # خبر تخفيف؟
        "h4_levels": r.get("h4_levels"),                  # مستويات 4س (فيصل)
        "key_levels": r.get("key_levels"),                # دعوم/مقاومات أساسي/فرعي
        "h4_confirm": r.get("h4_confirm", 0),             # قوة تأكيد 4س (ترتيب)
        "behav": r.get("behav"),                          # 🧬 بصمة طريقة الارتفاع (عرض فقط)
        "pump_scar": r.get("pump_scar"),                  # 🕵️ N1 رفعة قروب/كسر دعوم (عرض فقط)
        "interp": r.get("interp"),                         # 🧭 طبقة التفسير/القرار (عرض فقط)
        "bars_after": r.get("bars_after"),                # §11: جلسات منذ القاع (تفسير)
        "trendline": r.get("trendline"),                  # §10: خط الترند الهابط (تفسير)
        "sec_filings": bool(r.get("sec_filings")),        # لعلم SEC عند تجديد التفسير
        "recent_split": r.get("recent_split"),            # لعلم التقسيم عند التجديد
        "session_ctx": r.get("session_ctx"),              # §12: snapshot الجلسة (صادق)
        "tf_count": r.get("tf_count"),                    # عدد الفريمات المتوافقة (0-3)
        "tf_display": r.get("tf_display"),                # تفصيل الفريمات (شهري/أسبوعي/يومي)
        "liberation": r.get("liberation"),               # بوابة التحرر
        "sector": r.get("sector"), "country": r.get("country"),
        "status": "active", "removed_date": None, "removal_reason": None,
        "replaced": False,
        "readiness": None, "have": [], "partial": [], "missing": [],
        "hit": None, "hit_date": None,
        "max_gain_pct": 0.0,
        "last_price": round(r["price"], 4),
    }


def make_pullback_entry(r: dict, today_iso: str) -> dict:
    """سجل سهم في قائمة مراقبة الارتداد (نتابعه يوميًا حتى ينزل للدعم)."""
    return {
        "symbol": r["symbol"], "added": today_iso,
        "entry": [round(r["entry"][0], 4), round(r["entry"][1], 4)],
        "tranches": [round(p, 4) for p in (r.get("tranches") or r["entry"])],
        "pivot": round(r["pivot"], 4),
        "stop": round(r["stop"][0], 4),
        "t1": round(r["t1"], 4), "t2": round(r["t2"], 4),
        "t3": round(r["t3"], 4),
        "score": r["score"],
        "liberation": r.get("liberation"),
        "watch_reasons": list(r.get("watch_reasons", [])),
        "sector": r.get("sector"), "country": r.get("country"),
        "float": r.get("float"),
        "last_price": round(r["price"], 4),
        "status": "watching",          # watching → triggered (وصل الدعم)
        "triggered_date": None,
    }


def apply_short_gate(results: list) -> list:
    """M13 — بوابة الشورت العالي، تُطبّق بعد الفرز (مرحلة ثانية).
    الشورت يُجلب فقط للأسهم الناجحة (جلبه بطيء، يستحيل لكل السوق).
    يرفض السهم لو شورته معروف وعالي (≥ الحد). لو البيانة مفقودة من
    المصادر الثلاثة (Fintel→FINRA→Yahoo) → يعدّي (فائدة الشك)."""
    if not CONFIG.get("SHORT_GATE_REQUIRED", False) or not results:
        return results
    syms = [r["symbol"] for r in results]
    # نجلب الشورت من المصادر (نفس منطق الإثراء: Fintel ثم FINRA)
    short_map = {}
    try:
        short_map = fintel_short(sorted(syms)) or {}
    except Exception:
        short_map = {}
    try:
        finra = finra_daily_short(set(syms)) or {}
        for k, v in finra.items():
            short_map.setdefault(k, v)   # FINRA يكمّل ما نقص
    except Exception:
        pass
    kept, rejected = [], []
    limit = CONFIG["SHORT_GATE_MAX"]
    for r in results:
        srt = short_map.get(r["symbol"])
        # Fintel يرجّع dict {short_volume, si_pct_float} — نستخرج الحجم اليومي
        # (مثل enrich) فلا تنكسر المقارنة/التخزين بقيمة dict.
        if isinstance(srt, dict):
            srt = srt.get("short_volume")
        # نعيد استعمال القيمة المجلوبة هنا للتخزين/العرض بدل رميها (لا يمسّ
        # قرار البوابة: القرار أدناه يعتمد srt المحلي لا finra_short).
        if srt is not None and r.get("finra_short") is None:
            r["finra_short"] = srt
        if srt is not None and srt >= limit:
            # v2.7: لا يُحذف — يُسجّل نقصًا وينزل لقائمة المراقبة B
            r.setdefault("soft_fails", []).append("شورت عالٍ")
            r.setdefault("flags", []).append(
                f"⚠️ شورت عالٍ {int(srt):,} (فوق {limit:,})")
            rejected.append((r["symbol"], srt))
            kept.append(r)
        else:
            if srt is not None:
                r.setdefault("flags", []).append(f"شورت {int(srt):,} (مقبول)")
            else:
                r.setdefault("flags", []).append("شورت غير متاح — مُرِّر بفائدة الشك")
            kept.append(r)
    if rejected:
        names = "، ".join(f"{s}({int(v):,})" for s, v in rejected)
        log(f"بوابة الشورت (M13) نقلت لقائمة B: {len(rejected)}: {names}")
    return kept


def apply_float_gate(results: list) -> list:
    """M14 — بوابة الفلوت الكبير، تُطبّق بعد الفرز (مرحلة ثانية، آخر فلتر).
    أقوى رابط مشترك في كل أسهم فيصل = الفلوت الصغير (HCAI 163ألف،
    GWAV 778ألف، BJDX 918ألف، EHGO 1.62م... كلها صغيرة). الفلوت الصغير
    ينفجر بسهولة (أسهم قليلة، الطلب يرفعه بقوة). الفلوت يُجلب من
    yf.Ticker().info['floatShares'] — بطيء، فيُجلب للناجحين فقط.
    يرفض السهم لو فلوته معروف وكبير (≥ الحد). لو البيانة مفقودة →
    يعدّي (فائدة الشك، نفس منطق الشورت)."""
    if not CONFIG.get("FLOAT_GATE_REQUIRED", False) or not results:
        return results
    if yf is None:
        return results
    limit = CONFIG["FLOAT_GATE_MAX"]
    kept, rejected = [], []
    for r in results:
        fl = r.get("float")          # قد يكون مجلوباً مسبقاً من enrich
        if fl is None:               # غير مجلوب بعد → نجلبه الآن
            try:
                info = yf.Ticker(r["symbol"]).info or {}
                fl = info.get("floatShares")
                r["float"] = fl
                sp = info.get("shortPercentOfFloat")
                if r.get("short_pct") is None and sp:
                    r["short_pct"] = round(sp * 100, 1)
            except Exception:
                fl = None
            time.sleep(0.10)         # احترام حدود الطلبات
        if fl is not None and fl >= limit:
            # v2.7: لا يُحذف — يُسجّل نقصًا وينزل لقائمة المراقبة B
            r.setdefault("soft_fails", []).append("فلوت كبير")
            r.setdefault("flags", []).append(
                f"⚠️ فلوت كبير {int(fl):,} (فوق {limit:,})")
            rejected.append((r["symbol"], fl))
            kept.append(r)
        else:
            if fl is not None:
                r.setdefault("flags", []).append(
                    f"فلوت {int(fl):,} (صغير ✅)")
            else:
                r.setdefault("flags", []).append(
                    "فلوت غير متاح — مُرِّر بفائدة الشك")
            kept.append(r)
    if rejected:
        names = "، ".join(f"{s}({int(v):,})" for s, v in rejected)
        log(f"بوابة الفلوت (M14) نقلت لقائمة B: {len(rejected)}: {names}")
    return kept


def classify_tier(soft_fails, two_tier=None, maxf=None):
    """قبول/رفض السهم حسب عدد بوابات التأكيد الناقصة: 0..maxf → 'B' (مؤهّل) | أكثر → None
    (يُرفض). دالة نقية (تستخدمها scan_market).
    🪦 **تقاعد A/B** (2026-07-05، بالدليل — سنتان باكتيست + الحي): فئة A («صفر نواقص»)
    **ميتة** (0 سهم بلغها) و**ضجيج** (نسبة النجاح موزّعة بالتساوي على شرائح النواقص،
    والاتجاه ينقلب بين السنتين). فألغينا التمييز النوعي A/B: القبول **فئة واحدة "B"
    (مؤهّل)**، والترتيب بالجاهزية. **بوابة الرفض (n>maxf) محفوظة حرفيًا** (لا تمسّ العضوية)."""
    two_tier = CONFIG.get("WATCHLIST_TWO_TIER", True) if two_tier is None else two_tier
    maxf = CONFIG.get("WATCH_MAX_FAILS", 3) if maxf is None else maxf
    n = len(soft_fails or [])
    # n==0 يبقى مقبولًا حتى مع two_tier=False (وضع الفئة الواحدة الصارمة) — نفس مجموعة
    # القبول السابقة تمامًا (كانت 0→A · 1..maxf→B)، لكن بمسمّى موحّد = ثبات العضوية.
    if n == 0 or (two_tier and n <= maxf):
        return "B"
    return None


def rank_key(x):
    """مفتاح ترتيب القائمة التأسيسية (موحّد مع التقرير اليومي والرقم المعروض):
    **الأعلى جاهزيةً** → الأقوى تأكيدًا على 4س (دمج فيصل #3) → الأعلى نقاطًا → الأعلى
    عائدًا/مخاطرة. (الترتيب فقط — لا يمسّ الاختيار.)
    🪦 أُزيل مفتاح «A قبل B» بعد تقاعد A/B (كان ثابتًا=B للجميع فبلا أثر؛ إزالته تُبقي
    الترتيب/العضوية مطابقَين حرفيًا، والجاهزية هي المحور)."""
    rdy = x.get("readiness")
    return (-(rdy if rdy is not None else -1),
            -x.get("h4_confirm", 0),
            -x.get("score", 0), -x.get("rr", 0))


def _had_pivot_identity(df) -> bool:
    """هل توفّرت **هوية الارتكاز** (بوابات البنية M1-M3) في هذه البيانات؟
    سعر مقبول + هبوط ضمن المدى (فوق الأرضية وتحت السقف) + انفجار سابق فوق الأرضية.
    لا تفحص جاهزية الدخول (RSI الآن/القرب/النواقص) — فقط البنية، وهو ما يقصده كاشف
    الانفجارات بـ«كان ارتكازًا». تستعمل نفس spike_info والثوابت (بلا ازدواج منطق).
    فاشل-آمن → False. (إصلاح فحص 2026-06-26: كان was_pivot يعيد تشغيل مصنّف الدخول
    الكامل على شمعة ما قبل الانفجار، وهي تفشل بنيويًا دائمًا (RSI/قرب/نواقص) →
    was_pivot=False لكل الانفجارات؛ الآن يقيس الهوية فقط فيصير ذا معنى.)"""
    try:
        c = df["Close"].values.astype(float)
        price = float(c[-1])
        if price < CONFIG["MIN_PRICE"]:                                # M1
            return False
        hi52 = float(df["High"].tail(252).max())
        if hi52 <= 0:
            return False
        drop_pct = (1.0 - price / hi52) * 100.0                        # M2
        if not (CONFIG["MIN_DROP_FLOOR"] <= drop_pct <= CONFIG["MAX_DROP_PCT"]):
            return False
        best_spike, _ = spike_info(c, exclude_last=CONFIG["BASE_WINDOW"])  # M3
        return best_spike >= CONFIG["PRIOR_SPIKE_FLOOR"]
    except Exception:
        return False


def _run_explosion(c):
    """شبكة «التجمّع» (طلب المستخدم 2026-07-04): أكبر ارتفاع تراكمي **قاع→قمة**
    داخل آخر EXPLOSION_RUN_LOOKBACK جلسة — يلتقط الصاعد التدريجي >70% الذي لا يملك
    يوم قفزة واحد ≥50% (فلا يفلت متحرّك كبير من التصنيف). يعيد (نسبة الارتفاع %،
    موقع «يوم الانطلاق» المطلق = أول يوم بعد القاع) أو (None, None) إن لم يبلغ العتبة."""
    try:
        n = len(c)
        look = min(int(CONFIG["EXPLOSION_RUN_LOOKBACK"]), n - 1)
        if look < 2:
            return None, None
        seg = c[n - look - 1:]                 # آخر look+1 إغلاق
        best_rise, best_trough_j = 0.0, 0
        run_min, run_min_j = float(seg[0]), 0
        for j in range(1, len(seg)):
            if run_min > 0:
                rise = (float(seg[j]) / run_min - 1.0) * 100.0
                if rise > best_rise:
                    best_rise, best_trough_j = rise, run_min_j
            if float(seg[j]) < run_min:
                run_min, run_min_j = float(seg[j]), j
        if best_rise < CONFIG["EXPLOSION_RUN_PCT"]:
            return None, None
        # يوم الانطلاق = أول يوم بعد القاع → القاعدة = البيانات حتى القاع (شامل)
        launch_abs = (n - look - 1) + best_trough_j + 1
        return best_rise, min(launch_abs, n - 1)
    except Exception:
        return None, None


def scan_explosions(history: dict) -> list:
    """كاشف المتحرّكين (للتعلّم): يلتقط الأسهم اللي **قفزت ≥ EXPLOSION_PCT في يوم**
    (آخر EXPLOSION_LOOKBACK جلسة) **أو تجمّعت ≥ EXPLOSION_RUN_PCT قاع→قمة** (نافذة
    أطول) ويصنّفها:
      • was_pivot=True  → كان **ارتكازًا قبل الانفجار** (نحلّل بياناته حتى قبل يوم
        الانفجار) = فرصة فاتتنا → نراجع سبب عدم الترشيح.
      • was_pivot=False → انفجار عشوائي/خرابيط (لا بنية ارتكاز) = صح تجاهلناه.
    **`base_reason`** (طلب المستخدم 2026-07-04) = **البوابة الدقيقة التي رفضته عند
    قاعه قبل الركض** (لا الرفض الحالي بعد الانفجار) — فلا متحرّك >العتبة بلا بوابة
    معروفة. يعيد استخدام البيانات المحمّلة (لا تحميل إضافي)."""
    global _CUR_SYM
    today = dt.date.today().isoformat()
    # تحليل الشرائح التاريخية أدناه يستدعي analyze_ticker الذي يلوّث خرائط الرفض
    # الحيّة عبر _reject — نلتقط نسخة ونستعيدها في النهاية (لا يفسد الإحصاء الحي).
    _snap_reasons = dict(_REJECT_REASONS)
    _snap_stats = dict(_REJECT_STATS)
    out = []
    for sym, df in history.items():
        try:
            c = df["Close"].values.astype(float)
        except Exception:
            continue
        if len(c) < CONFIG["MIN_BARS"] + 1:
            continue
        look = min(int(CONFIG["EXPLOSION_LOOKBACK"]), len(c) - 1)
        # نتتبّع إزاحة اليوم k مع كل قفزة (لا نعتمد .index على قائمة مُرشَّحة قد
        # تُسقط أيامًا بإغلاق ≤0 فينحرف موقع يوم الانفجار).
        gains = [(k, (c[-k] / c[-k - 1] - 1.0) * 100.0)
                 for k in range(1, look + 1) if c[-k - 1] > 0]
        # (1) قفزة يوم واحد (المسار الأصلي — بلا تغيير سلوك). (2) وإلا: تجمّع تراكمي.
        kind, g, idx = None, None, None
        if gains:
            k_max, g1 = max(gains, key=lambda p: p[1])
            if g1 >= CONFIG["EXPLOSION_PCT"]:
                kind, g = "قفزة", g1
                idx = len(c) - k_max              # موقع يوم القفزة (مطلق، صحيح)
        if kind is None:                          # لا قفزة → جرّب التجمّع التدريجي
            grun, launch = _run_explosion(c)
            if grun is None:
                continue
            kind, g, idx = "تجمّع", grun, launch
        # تاريخ يوم الانفجار الفعلي (لا تاريخ المسح) — حتى لا يُحسَب نفس الانفجار
        # عدّة مرّات عبر أيام النافذة (dedup = symbol + تاريخ الانفجار).
        try:
            expl_date = df.index[idx].date().isoformat()
        except Exception:
            expl_date = today
        live_reason = _REJECT_REASONS.get(sym, "—")   # الرفض الحالي (بعد الانفجار)
        was_pivot = False
        base_reason = "—"
        slice_df = df.iloc[:idx]                   # بياناته قبل الانفجار/الركض
        if len(slice_df) >= CONFIG["MIN_BARS"]:
            # هوية الارتكاز فقط (M1-M3)، لا جاهزية الدخول — انظر _had_pivot_identity.
            was_pivot = _had_pivot_identity(slice_df)
            # **البوابة الدقيقة عند القاع قبل الركض** (لا الرفض الحالي): نشغّل الفارز
            # الكامل على شريحة ما قبل الانفجار فيُسجّل _reject البوابة الأولى الفاشلة.
            _REJECT_REASONS.pop(sym, None)
            base_reason = ("مرشّح" if analyze_ticker(sym, slice_df)
                           else _REJECT_REASONS.get(sym, "—"))
        out.append({"symbol": sym, "date": today, "expl_date": expl_date,
                    "gain": round(g, 0), "kind": kind,
                    "reason": live_reason,        # توافق خلفي (الرفض الحالي)
                    "base_reason": base_reason,   # البوابة عند القاع (الأهم)
                    "was_pivot": bool(was_pivot),
                    # A2: قفزة خارقة قد تكون تقسيمًا غير معدَّل — وسم للتحقق اليدوي.
                    # 🛡️ bool() إلزامي: مسار «قفزة» يمرّ من numpy → np.bool كان يفجّر
                    # حفظ القائمة كلها (حادثة 2026-07-09 — لهذا كان المخزَّن كله «تجمّع»
                    # وصفر «قفزة»: كل يوم فيه قفزة كان الحفظ يفشل بصمت!).
                    "suspect_split": bool(g >= CONFIG["SPLIT_SUSPECT_GAIN_PCT"])})
    _CUR_SYM = None
    # استعادة خرائط الرفض كما كانت قبل تحليل الشرائح التاريخية (لا تلوّث الحيّة)
    _REJECT_REASONS.clear()
    _REJECT_REASONS.update(_snap_reasons)
    _REJECT_STATS.clear()
    _REJECT_STATS.update(_snap_stats)
    out.sort(key=lambda x: -x["gain"])
    return out


def accumulate_explosions(wl: dict, history: dict) -> int:
    """يضيف انفجارات اليوم لسجل تراكمي في القائمة (dedup symbol+date، يحتفظ
    بآخر EXPLOSION_KEEP_DAYS يوم) — يُعرض في تقرير مساعد التطوير (الجمعة بعد الإغلاق)."""
    found = scan_explosions(history)
    log_ex = wl.setdefault("explosions", [])
    # dedup على **تاريخ الانفجار الفعلي** (expl_date) لا تاريخ المسح — فلا يُحسب
    # نفس الانفجار عدّة مرّات عبر أيام نافذة المسح. التاريخ المعروض/الانقضاء يبقى
    # تاريخ المسح (date) للحفاظ على نافذة الاحتفاظ. إصلاح فحص 2026-06-24.
    def _ek(e):
        return (e["symbol"], e.get("expl_date", e.get("date")))
    seen = {_ek(e) for e in log_ex}
    for e in found:
        if _ek(e) not in seen:
            log_ex.append(e)
            seen.add(_ek(e))
    cutoff = (dt.date.today()
              - dt.timedelta(days=int(CONFIG["EXPLOSION_KEEP_DAYS"]))).isoformat()
    kept = [e for e in log_ex if e.get("date", "") >= cutoff]
    cap = int(CONFIG["EXPLOSION_KEEP_MAX"])
    if len(kept) > cap:                    # شفافية: لا قصّ صامت (طلب المستخدم)
        # نُبقي الارتكازات الفائتة أولًا ثم الأحدث — فلا يُطرد «ارتكاز فاتنا» بضجيج
        # عشوائي عند الامتلاء (الوعد: لا متحرّك ارتكازي يُفقَد بلا بوابة معروفة).
        piv = [e for e in kept if e.get("was_pivot")]
        rest = [e for e in kept if not e.get("was_pivot")]
        kept = (piv + rest)[-cap:] if len(piv) >= cap else piv + rest[-(cap - len(piv)):]
        log(f"⚠️ كاشف الانفجارات: تجاوز السعة ({cap}) — أُبقيت الارتكازات + الأحدث.")
    wl["explosions"] = kept
    return len(found)


def record_reject_stats(wl: dict) -> None:
    """A1 (خطة الضبط 2026-07-03): لقطة يومية لمقام أسباب الرفض — كان `_REJECT_STATS`
    يُطبع باللوق ويُصفَّر كل تشغيل فيضيع المقام، ولا يمكن حسم «هل بوابة M4/M2
    متشدّدة؟» بلا نسبة (الفائتة ÷ المقام). تُحفظ آخر 56 يومًا في القائمة ويستهلكها
    مساعد التطوير. **طبقة قياس/تقارير فقط — لا تمسّ الفرز.**"""
    if not _REJECT_STATS:
        return
    today = dt.date.today().isoformat()
    snap = {"date": today, "stats": dict(_REJECT_STATS),
            "universe": _SCAN_STATS.get("universe"),
            "valid": _SCAN_STATS.get("valid")}
    log_rs = [e for e in wl.get("reject_stats", [])
              if e.get("date") != today]          # لقطة واحدة لكل يوم (الأحدث تفوز)
    log_rs.append(snap)
    cutoff = (dt.date.today() - dt.timedelta(days=56)).isoformat()
    wl["reject_stats"] = [e for e in log_rs if e.get("date", "") >= cutoff][-60:]


def scan_pullback(history: dict, exclude: set = None) -> list:
    """قائمة مراقبة الارتداد: أسهم ارتكاز حقيقية ارتفعت فوق دخولها.
    تعيد استخدام البيانات المحمّلة (لا تحميل إضافي). مرتّبة بالأقرب للدعم."""
    if not CONFIG.get("PULLBACK_WATCH", False):
        return []
    exclude = exclude or set()
    out = []
    for sym, df in history.items():
        if sym in exclude:
            continue
        try:
            w = analyze_ticker(sym, df, pullback=True)
        except Exception:
            w = None
        if w:
            out.append(w)
    # ترتيب بالجودة (قوة الارتكاز) أولاً ثم القرب للدعم — كل أسهم الارتداد
    # بعيدة بطبيعتها، فالأهم نراقب الأقوى (مثل HTCR) لا الأقرب فقط.
    out.sort(key=lambda x: (-x.get("score", 0), -(x.get("readiness") or 0)))
    return out[:CONFIG.get("PULLBACK_SIZE", 10)]


def scan_market():
    """فرز السوق (التجديد الأسبوعي أو جلب بدائل) — يرجع (نتائج مرتبة، بيانات)"""
    _SCAN_STATS["universe_fallback"] = False
    if MODE == "FULL":
        universe = get_universe()
        if not universe:
            log("⚠️ فشل جلب الكون — التحويل لوضع TEST")
            universe = CONFIG["TEST_TICKERS"]
            _SCAN_STATS["universe_fallback"] = True   # عيّنة اختبار صغيرة ≠ السوق
    else:
        universe = CONFIG["TEST_TICKERS"]
        log(f"وضع تجربة: {len(universe)} سهم من العينة الموثقة")
    history = download_history(universe)
    # صحة البيانات: كم سهم من الكون وصلت بياناته فعلاً (يكشف خنق Yahoo)
    _SCAN_STATS["universe"] = len(universe)
    _SCAN_STATS["valid"] = len(history)
    cov = (len(history) / len(universe) * 100.0) if universe else 0.0
    if MODE == "FULL" and cov < CONFIG["DATA_HEALTH_MIN_PCT"]:
        log(f"⚠️ تغطية بيانات منخفضة: {cov:.0f}% ({len(history)}/{len(universe)})"
            " — Yahoo خنق الطلبات؛ قد تنقص أسهم")
    results = []
    _REJECT_STATS.clear()                 # تصفير عدّاد أسباب الرفض
    _REJECT_REASONS.clear()
    for sym, df in history.items():
        r = analyze_ticker(sym, df)
        if r:
            # ① (إصلاح تدقيق 2026-07-12): تاريخ **شمعة الترشيح الفعلية** (آخر شمعة
            # في البيانات) — المسار اليومي يعمل 07:23 UTC قبل الافتتاح فتاريخ التشغيل
            # (added) أحدثُ من آخر شمعة بيوم، وكانت مقارنة `day > added` تُسقط شمعة
            # يوم الترشيح من التقييم للأبد (ستوب اليوم الأول غير مرئي). التتبع صار
            # يقارن بـ ref_bar. فاشل-آمن: تعذّر القراءة → None → ارتداد لـ added.
            try:
                r["ref_bar"] = df.index[-1].date().isoformat()
            except Exception:
                r["ref_bar"] = None
            r["behav"] = behavior_rise_profile(df)   # 🧬 بصمة طريقة الارتفاع (حيّ، عرض فقط)
            r["pump_scar"] = group_pump_scar(df)     # 🕵️ N1 رفعة قروب/كسر دعوم (حيّ، عرض فقط)
            r["trendline"] = descending_trendline(df, r["price"])  # §10 (حيّ، عرض فقط)
            r["interp"] = build_interpretation(r)    # 🧭 طبقة التفسير/القرار (حيّ، عرض فقط)
            results.append(r)
    # تشخيص: أين تُرفض الأسهم؟ (يظهر بسجل الأكشن لمعرفة البوابة الخانقة)
    if _REJECT_STATS:
        top = sorted(_REJECT_STATS.items(), key=lambda x: -x[1])
        log("أسباب الرفض: " + " · ".join(f"{k}={v}" for k, v in top))
    # 👻 الفرص الفائتة: مرفوض صعد فعلاً (آخر ~10 جلسات) → يكشف تشدّد البوت
    _MISSED.clear()
    passed = {r["symbol"] for r in results}
    for sym, reason in _REJECT_REASONS.items():
        df = history.get(sym)
        if sym in passed or df is None or len(df) < 12:
            continue
        try:
            c = df["Close"].values.astype(float)
            g = (c[-1] / c[-11] - 1.0) * 100.0
        except Exception:
            continue
        if g >= CONFIG["MISSED_RISE_PCT"]:
            # §6: تاريخ بداية نافذة الكسب (c[-11]) لتسوية تقسيم دقيقة بالتقرير.
            try:
                _ws = df.index[-11].date().isoformat()
            except Exception:
                _ws = None
            _MISSED.append({"symbol": sym, "reason": reason,
                            "gain_10d": round(float(g), 1),
                            "price": round(float(c[-1]), 2),
                            "window_start": _ws,
                            # A2: كسب خارق = يُرجَّح أثر تقسيم عكسي غير معدَّل.
                            # 🛡️ bool() ضد np.bool (نفس صنف حادثة 2026-07-09)
                            "suspect_split":
                                bool(g >= CONFIG["SPLIT_SUSPECT_GAIN_PCT"])})
    _MISSED.sort(key=lambda x: -x["gain_10d"])
    if _MISSED:
        log(f"فرص فائتة (مرفوض صعد فوق {CONFIG['MISSED_RISE_PCT']:.0f}%): "
            f"{len(_MISSED)}")
    # M13: بوابة الشورت العالي (مرحلة ثانية على الناجحين فقط)
    results = apply_short_gate(results)
    # M14: بوابة الفلوت الكبير (آخر فلتر — الفلوت بطيء، والناجحون هنا قلائل)
    results = apply_float_gate(results)
    # ===== التصنيف النهائي لقائمتين (v2.7) =====
    # A = صفر نواقص (صارمة) | B = 1-2 نواقص (مراقبة) | أكثر = يُحذف.
    final = []
    for r in results:
        tier = classify_tier(r.get("soft_fails", []))
        if tier is None:
            continue
        r["tier"] = tier
        final.append(r)
    results = final
    # ترتيب موحّد: الأعلى جاهزيةً (الرقم المعروض) → تأكيد 4س → النقاط → العائد.
    # (🪦 A/B متقاعد — الجاهزية هي المحور؛ يطابق اليومي وترويسة «الجاهز أولاً»)
    results.sort(key=rank_key)
    log(f"الفرز: {len(results)} مرشح مؤهّل (مرتّب بالجاهزية)")
    return results, history


def select_top(results: list, n: int, exclude: set) -> list:
    """أفضل n نتيجة مع استبعاد رموز محددة"""
    out = []
    for r in results:
        if r["symbol"] in exclude:
            continue
        out.append(r)
        if len(out) >= n:
            break
    return out


def entry_readiness(df: pd.DataFrame):
    """نسبة جاهزية الدخول 0-100% (تتغير يومياً، الأسهم ثابتة).
    الأوزان: ثبات بعد القاع 30 (الأهم) + RSI 20 + MACD 10 + KST 10
    + قرب متوسط 30/50 10 + جفاف بيع 10 + مسح سيولة 10 = 100"""
    close = df["Close"]
    high, low, vol = df["High"], df["Low"], df["Volume"]
    c = close.values
    price = float(c[-1])
    comp = {}

    # 1) الثبات بعد القاع — 30 (كامل في النافذة الذهبية 3-8، نصفها خارجها)
    ps = pivot_stability(low.values.astype(float), c)
    pts = 0
    if ps and ps["held"]:
        pts = 30 if ps["ready"] else 15
    comp["ثبات بعد القاع"] = (pts, 30)

    # 2) RSI — 20 (كامل: قاع ≤35 + انحناء + الحالي ≤50 | نصف: ارتد فوق 50)
    rsi_s = rsi(close)
    r_now, r_prev = float(rsi_s.iloc[-1]), float(rsi_s.iloc[-2])
    r_min = float(rsi_s.tail(CONFIG["RSI_RECENT_WINDOW"]).min())
    pts = 0
    if r_min <= CONFIG["RSI_OVERSOLD"] and r_now > r_prev:
        pts = 20 if r_now <= CONFIG["RSI_MAX_NOW"] else 10
    comp["RSI تشبع وانحناء"] = (pts, 20)

    # 3) MACD — 10
    m_line, m_sig = macd(close)
    pts = 10 if ((m_line.iloc[-5:] > m_sig.iloc[-5:]).any()
                 and float(m_line.iloc[-1]) >= float(m_sig.iloc[-1])) else 0
    comp["تقاطع MACD"] = (pts, 10)

    # 4) KST — 10
    k_line, k_sig = kst(close)
    pts = 0
    try:
        if (float(k_line.iloc[-1]) > float(k_sig.iloc[-1])
                and float(k_line.iloc[-1]) > float(k_line.iloc[-3])):
            pts = 10
    except Exception:
        pass
    comp["KST صاعد"] = (pts, 10)

    # 5) قرب متوسط 30/50 — 10
    sma30 = ema(close, 30)
    sma50 = ema(close, 50)
    near = any(ma > 0 and abs(price / ma - 1.0) <= 0.05
               for ma in (sma30, sma50))
    comp["قرب متوسط 30/50"] = (10 if near else 0, 10)

    # 6) جفاف بيع — 10
    v20 = float(vol.tail(20).mean())
    v5 = float(vol.tail(5).mean())
    dry = bool(v20 > 0 and v5 <= CONFIG["VOL_DRY_RATIO"] * v20)
    comp["جفاف بيع"] = (10 if dry else 0, 10)

    # 7) مسح سيولة — 10 (كسر قاع سابق ثم استعادة)
    sweep = False
    lows_arr = low.values.astype(float)
    if len(lows_arr) > 35:
        prior_low = float(np.min(lows_arr[-35:-10]))
        recent_min = float(np.min(lows_arr[-10:]))
        mfi_s = mfi(high, low, close, vol)
        if (prior_low > 0 and recent_min < prior_low * 0.995
                and price > prior_low
                and float(mfi_s.iloc[-1]) >= float(mfi_s.tail(10).min())):
            sweep = True
    comp["مسح سيولة"] = (10 if sweep else 0, 10)

    total = int(sum(p for p, _ in comp.values()))
    return total, comp


def _note(wl: dict, sym: str, text: str, family: str = None) -> None:
    """تسجيل ملاحظة تعلّم (مرة واحدة لكل عائلة ملاحظة لكل سهم بالأسبوع)"""
    fam = family or text
    for n in wl.get("notes", []):
        if n.get("symbol") == sym and n.get("family") == fam:
            return
    wl.setdefault("notes", []).append({
        "date": dt.date.today().isoformat(),
        "symbol": sym, "text": text, "family": fam})


def _split_scale_factor(splits, since_iso: str) -> float:
    """⚖️ عامل تحويل المقياس من أحداث التقسيم **بعد** تاريخ مرجعي (إصلاح تدقيق
    2026-07-10 — F-02): المستويات المخزّنة (وقف/أهداف) بمقياس يوم الترشيح، بينما
    بيانات yfinance المعاد تحميلها معدَّلة بالتقسيم — تقسيم عكسي أثناء التتبع كان
    يجعل «هدفًا محققًا» زائفًا يدخل سجل النجاح. دالة نقيّة (بلا شبكة، قابلة للاختبار):
    تقبل pandas Series (فهرس تواريخ، القيمة = جديد/قديم: 0.1 لعكسي 1:10) أو قائمة
    أزواج (تاريخ، نسبة). ترجع حاصل ضرب النسب بعد `since_iso` حصريًا — والقسمة عليه
    تحوّل المستوى المخزّن لمقياس البيانات الحالية. فاشلة-آمنة → 1.0 (سلوك اليوم)."""
    try:
        if splits is None:
            return 1.0
        pairs = []
        if hasattr(splits, "items"):                     # pandas Series
            for idx, val in splits.items():
                try:
                    d = idx.date().isoformat() if hasattr(idx, "date") else str(idx)[:10]
                    pairs.append((d, float(val)))
                except Exception:
                    continue
        else:                                            # قائمة أزواج
            for d, val in splits:
                pairs.append((str(d)[:10], float(val)))
        factor = 1.0
        for d, val in pairs:
            if d > str(since_iso)[:10] and val > 0:
                factor *= val
        return factor if factor > 0 else 1.0
    except Exception:
        return 1.0


def _fetch_splits(sym: str):
    """جلب أحداث التقسيم من ياهو — **فاشل-آمن مطلق** → None (فيصير العامل 1.0 =
    سلوك اليوم حرفيًا، لا تعطيل للحسم بعطل شبكي). تُستدعى فقط في مسارَي تسوية
    النتائج (update_tracking/update_watchlist_status) — خارج الفرز كليًّا."""
    try:
        if yf is None:
            return None
        return yf.Ticker(sym).splits
    except Exception:
        return None


def _scale_divisor(last_price, ref_level, factor: float) -> float:
    """⚖️ مُختار تماسك المقياس (حارس ضد التصحيح المزدوج): بعد ترحيل LOGIC_VERSION
    قد تكون المستويات أعيد حسابها من بيانات معدَّلة أصلًا (مقياس جديد) رغم أن تاريخ
    الإضافة قديم — القسمة على العامل حينها تُفسدها. نقارن المستوى كما هو مقابل
    المستوى÷العامل ونختار **الأقرب لوغاريتميًا لسعر اليوم** (فرق المقياس بالتقسيم
    العكسي ×5+ أكبر بكثير من أي حركة سعرية). نقيّة، ترجع 1.0 أو `factor`."""
    try:
        lp = float(last_price)
        ref = float(ref_level)
        if factor == 1.0 or lp <= 0 or ref <= 0 or factor <= 0:
            return 1.0
        raw_gap = abs(math.log(lp / ref))                 # المستوى بمقياسه المخزّن
        scaled_gap = abs(math.log(lp / (ref / factor)))   # المستوى محوَّلًا
        return factor if scaled_gap < raw_gap else 1.0
    except Exception:
        return 1.0


def _split_corrected_gain(gain_pct, factor):
    """§6 (2026-07-11): يزيل تضخّم تقسيم عكسي من كسب مُبلَّغ في تقرير التطوير.
    `factor` = حاصل ضرب قيم التقسيم بعد بداية النافذة (عكسي 1:10 = 0.1). ذو معنى
    فقط عند `factor < 1.0` — التقسيم العكسي على بيانات غير معدَّلة يضخّم الكسب
    (c[-1] بمقياس جديد ×10 مقابل c[-11] بمقياس قديم). الصيغة تعيد الكسب لمقياس
    البداية: ((1+g/100)×factor − 1)×100. عامل ≥1 (لا تقسيم/تقسيم أمامي) → الأصل
    بلا مساس. نقيّة، فاشلة-آمنة → الأصل عند أي خطأ. طبقة تقارير فقط."""
    try:
        f = float(factor)
        if f <= 0 or f >= 1.0:
            return gain_pct
        return ((1.0 + float(gain_pct) / 100.0) * f - 1.0) * 100.0
    except Exception:
        return gain_pct


def _resolve_split_suspects(missed, fetch=None):
    """§6: يسوّي مشتبهات التقسيم في الفرص الفائتة (طبقة تقارير فقط) بدل استبعادها
    الأعمى. لكل عنصر موسوم `suspect_split`: يجلب أحداث التقسيم ويحسب العامل بعد
    `window_start`؛ لو حدث **تقسيم عكسي فعلي** (عامل < 1.0) بالنافذة يصحّح الكسب
    ويُعيد التصنيف:
      • مصحَّح في [MISSED_RISE_PCT, SPLIT_SUSPECT_GAIN_PCT) → نظيف (`split_corrected`).
      • مصحَّح أقل من MISSED_RISE_PCT → ضجيج تقسيم صرف، يُسقَط.
      • لا تقسيم عكسي / بقي ≥ SPLIT_SUSPECT_GAIN_PCT → يبقى موسومًا (سلوك اليوم).
    غير المشتبه يمرّ بلا مساس. **أسوأ حالة = سلوك اليوم حرفيًا** (تعذّر الجلب/لا
    window_start → يبقى suspect). `fetch` محقون للاختبار بلا شبكة. يرجع قائمة جديدة
    (لا يمسّ _MISSED). مقفول خارج الفرز/الاختيار."""
    _f = fetch or _fetch_splits              # بحث وقت النداء (يُتيح المونكي-باتش)
    lo = float(CONFIG["MISSED_RISE_PCT"])
    hi = float(CONFIG["SPLIT_SUSPECT_GAIN_PCT"])
    out = []
    for m in missed:
        if not m.get("suspect_split"):
            out.append(m)
            continue
        ws = m.get("window_start")
        if not ws:
            out.append(m)
            continue
        try:
            factor = _split_scale_factor(_f(m["symbol"]), ws)
        except Exception:
            factor = 1.0
        if factor >= 1.0:                       # لا تقسيم عكسي بالنافذة
            out.append(m)
            continue
        cg = _split_corrected_gain(m["gain_10d"], factor)
        if cg >= hi:                            # التصحيح لم يحسم الشذوذ
            out.append(m)
            continue
        if cg < lo:                             # ضجيج تقسيم صرف
            log(f"👻 {m['symbol']}: +{m['gain_10d']:.0f}% كان تقسيمًا عكسيًا "
                f"(عامل {factor:g}) → +{cg:.0f}% فعلي، أقل من عتبة الفائتة — يُسقَط")
            continue
        mm = dict(m)
        mm["gain_10d"] = round(float(cg), 1)
        mm["suspect_split"] = False
        mm["split_corrected"] = True
        log(f"👻 {m['symbol']}: +{m['gain_10d']:.0f}% بعد تسوية تقسيم "
            f"(عامل {factor:g}) → +{cg:.0f}% فعلي (يدخل الإحصاء)")
        out.append(mm)
    return out


def _resolve_explosion_suspects(explosions, fetch=None):
    """§6: نظير `_resolve_split_suspects` لسجل الانفجارات المتراكم. المرجع =
    `expl_date` **ناقص يوم** (لالتقاط تقسيم يوم الانفجار نفسه — `_split_scale_factor`
    تستخدم `d > since` الصارمة). يصحّح كسب الانفجار المشتبه عند تقسيم عكسي مؤكَّد،
    ويُعيد التصنيف بنفس المنطق (نظيف/يُسقَط/يبقى). `gain` رقم لا نسبة (round(g,0)).
    أسوأ حالة = سلوك اليوم. يرجع قائمة جديدة. مقفول خارج الفرز/الاختيار."""
    _f = fetch or _fetch_splits              # بحث وقت النداء (يُتيح المونكي-باتش)
    hi = float(CONFIG["SPLIT_SUSPECT_GAIN_PCT"])
    ex_lo = float(CONFIG["EXPLOSION_PCT"])      # دون عتبة الانفجار = لم يعد انفجارًا
    out = []
    for e in explosions:
        if not e.get("suspect_split"):
            out.append(e)
            continue
        ed = e.get("expl_date") or e.get("date")
        if not ed:
            out.append(e)
            continue
        try:
            since = (dt.date.fromisoformat(str(ed)[:10])
                     - dt.timedelta(days=1)).isoformat()
        except Exception:
            out.append(e)
            continue
        try:
            factor = _split_scale_factor(_f(e["symbol"]), since)
        except Exception:
            factor = 1.0
        if factor >= 1.0:
            out.append(e)
            continue
        cg = _split_corrected_gain(e.get("gain", 0), factor)
        if cg >= hi:
            out.append(e)
            continue
        if cg < ex_lo:                          # ضجيج تقسيم صرف
            log(f"💥 {e['symbol']}: +{e.get('gain', 0):.0f}% كان تقسيمًا عكسيًا "
                f"(عامل {factor:g}) → +{cg:.0f}% فعلي، دون عتبة الانفجار — يُسقَط")
            continue
        ee = dict(e)
        ee["gain"] = round(float(cg), 0)
        ee["suspect_split"] = False
        ee["split_corrected"] = True
        log(f"💥 {e['symbol']}: +{e.get('gain', 0):.0f}% بعد تسوية تقسيم "
            f"(عامل {factor:g}) → +{cg:.0f}% فعلي")
        out.append(ee)
    return out


def update_watchlist_status(wl: dict, history: dict) -> list:
    """فحص الستوب/الأهداف/الملاحظات لكل سهم نشط منذ إضافته.
    الستوب أولاً = افتراض محافظ (إلا إذا تحقق هدف قبله).
    يرجع قائمة المشطوبين في هذا التشغيل."""
    today_iso = dt.date.today().isoformat()
    for s in [x for x in wl["stocks"] if x["status"] == "active"]:
        df = history.get(s["symbol"])
        if df is None or len(df) == 0:
            _note(wl, s["symbol"], "تعذر جلب بياناته (تداول موقوف؟)",
                  family="لا بيانات")
            continue
        added = dt.date.fromisoformat(s["added"])
        # ① (إصلاح تدقيق 2026-07-12): مرجع نافذة التقييم = شمعة الترشيح الفعلية
        # (ref_bar) لا تاريخ التشغيل — المسار اليومي يعمل قبل الافتتاح فشمعة يوم
        # الترشيح تتكوّن **بعد** الختم وكان `day > added` يُسقطها للأبد (ستوب اليوم
        # الأول غير مرئي). ارتداد للسجلات القديمة بلا ref_bar → added = سلوك اليوم
        # حرفيًا (توافق خلفي، لا موجة تصحيح رجعية).
        try:
            ref_bar = dt.date.fromisoformat(str(s.get("ref_bar") or s["added"])[:10])
        except Exception:
            ref_bar = added
        s["last_price"] = round(float(df["Close"].iloc[-1]), 4)
        # §10: خط الترند يُعاد حسابه من بيانات اليوم (الخط الهابط ينزل يوميًا).
        # ⚠️ الإسناد **بلا شرط عمدًا**: None اليوم = الخط مات → يجب أن يختفي من
        # العرض اليوم نفسه (إبقاء المخزّن = حاجز بالٍ لم يعد موجودًا — لا «تصلحها»).
        try:
            s["trendline"] = descending_trendline(df, s["last_price"])
        except Exception:
            pass
        # 🧬 بصمة طريقة الارتفاع + جلسات القاع تتجدّدان يوميًا (إصلاح 2026-07-08،
        # ملاحظة المستخدم من التقرير الحي: سطر 🧬 كان يغيب عن الأسهم المضافة قبل
        # الميزة لأن البصمة تُخزَّن وقت الإضافة فقط). حارس لا-يمسح: بيانات اليوم
        # القاصرة (score=None) لا تمحو بصمة مخزّنة صالحة. عرض فقط.
        try:
            _bh_new = behavior_rise_profile(df)
            if _bh_new.get("score") is not None:
                s["behav"] = _bh_new
            _psn = pivot_stability(df["Low"].values.astype(float),
                                   df["Close"].values.astype(float))
            if _psn:
                s["bars_after"] = int(_psn["bars_after"])
            s["pump_scar"] = group_pump_scar(df)   # 🕵️ N1 يتجدّد يوميًا (عرض فقط)
        except Exception:
            pass
        # 🧭 تجديد التفسير يوميًا بالسعر الجديد (عرض فقط — الرقم الحرج/وضع الدخول
        # يتحرّكان مع السعر؛ بلا تجديد يتجمّدان يوم الترشيح). الحارس هنا يخصّ
        # interp وحده: لو رجع فارغًا (سجل قديم ناقص الحقول) يبقى التفسير المخزّن.
        try:
            _ip = build_interpretation(s)
            if _ip:
                s["interp"] = _ip
        except Exception:
            pass
        # ⚖️ F-02 (إصلاح تدقيق 2026-07-10): تسوية مقياس التقسيم قبل الحسم —
        # المستويات مخزّنة بمقياس يوم الترشيح والبيانات معدَّلة بالتقسيم؛ تقسيم
        # عكسي أثناء التتبع كان يُنتج «أهدافًا محققة» زائفة. العامل من أحداث
        # التقسيم بعد الإضافة، ومُختار التماسك يحمي من التصحيح المزدوج لو كانت
        # المستويات أعيد حسابها بعد الترحيل. فاشل-آمن: تعذُّر الجلب → عامل 1.0
        # = السلوك السابق حرفيًا. **تسوية مقارنات فقط — المخزّن لا يُمسّ.**
        _spf = _split_scale_factor(_fetch_splits(s["symbol"]), s["added"])
        _div = _scale_divisor(s["last_price"],
                              s.get("pivot") or s["stop"], _spf)
        if _div != 1.0:
            log(f"⚖️ {s['symbol']}: تقسيم بعد الإضافة (عامل {_spf:g}) — "
                "تُسوَّى مستويات الحسم لمقياس اليوم")
        _stop_c = float(s["stop"]) / _div
        _t1_c = float(s["t1"]) / _div
        _t2_c = float(s["t2"]) / _div
        _t3_c = float(s["t3"]) / _div
        _eref_c = float(s["entry_ref"]) / _div
        _split_tag = " (بعد تسوية تقسيم)" if _div != 1.0 else ""
        # ① شموع ما بعد **شمعة الترشيح** (ref_bar) — لا بعد تاريخ التشغيل: المسار
        # اليومي يختم قبل الافتتاح فشمعة يوم الختم نفسها تدخل التقييم (كانت تضيع).
        rows = []
        for i in range(len(df)):
            try:
                day = df.index[i].date()
            except Exception:
                continue
            if day > ref_bar:
                rows.append((day, float(df["High"].iloc[i]),
                             float(df["Low"].iloc[i])))
        if rows:
            mx = max(h for _, h, _ in rows)
            s["max_gain_pct"] = round((mx / _eref_c - 1.0) * 100.0, 1)
        for day, hi, lo in rows:
            # الستوب أولاً (محافظ) إذا لم يتحقق أي هدف قبله
            if lo <= _stop_c and not s["hit"]:
                s["status"] = "stopped"
                s["removed_date"] = today_iso
                loss = (_stop_c / _eref_c - 1.0) * 100.0
                s["removal_reason"] = (f"ضرب الستوب ${_stop_c:.2f} "
                                       f"يوم {day} ({loss:+.1f}%){_split_tag}")
                break
            # الأهداف (تصاعدياً)
            if hi >= _t3_c and s["hit"] != "t3":
                s["hit"], s["hit_date"] = "t3", str(day)
            elif hi >= _t2_c and s["hit"] not in ("t2", "t3"):
                s["hit"], s["hit_date"] = "t2", str(day)
            elif hi >= _t1_c and not s["hit"]:
                s["hit"], s["hit_date"] = "t1", str(day)
            # ستوب بعد تحقيق هدف = خروج رابح مفترض، لكن النموذج انتهى
            if lo <= _stop_c:
                s["status"] = "stopped"
                s["removed_date"] = today_iso
                s["removal_reason"] = (f"لمس الستوب يوم {day} بعد تحقيق "
                                       f"هدف{s['hit'][-1]} (خروج رابح مفترض)"
                                       f"{_split_tag}")
                break
        # ملاحظات تعلّم (لا تُشطب بسببها — تُعرض يوم التجديد)
        if s["status"] == "active":
            lp = s["last_price"]
            if lp < CONFIG["MIN_PRICE"]:
                _note(wl, s["symbol"],
                      f"نزل تحت ${CONFIG['MIN_PRICE']:.0f} (${lp:.2f})",
                      family="تحت الحد")
            cvals = df["Close"].values
            if len(cvals) > 6:
                g5 = (float(cvals[-1]) / float(cvals[-6]) - 1.0) * 100.0
                if g5 > CONFIG["RECENT_RISE_BLOCK_PCT"]:
                    _note(wl, s["symbol"],
                          f"انفجر {g5:+.0f}% خلال أسبوع — النموذج اشتغل "
                          "(الدخول الجديد فات)", family="انفجر")
            _piv_c = float(s["pivot"]) / _div     # ⚖️ نفس تسوية المقياس
            if _stop_c < lp < _piv_c:
                _note(wl, s["symbol"],
                      f"يتداول تحت القاع ${_piv_c:.2f} بدون لمس الستوب",
                      family="تحت القاع")
    # نقل المشطوبين من النشطين إلى سجل المشطوبين
    newly = [s for s in wl["stocks"] if s["status"] != "active"]
    wl["stocks"] = [s for s in wl["stocks"] if s["status"] == "active"]
    wl["removed"].extend(newly)
    return newly


def migrate_watchlist(wl: dict, history: dict) -> int:
    """ضمان آلي ضد تكرار مشكلة البيانات القديمة: لو تغيّرت نسخة منطق الكود
    (LOGIC_VERSION) عن المختومة في القائمة، يعيد حساب الدخول/الوقف/الأهداف/
    الدفعات/المستويات لكل سهم نشط **فورًا** (لا ينتظر يوم التجديد). يحافظ على
    تاريخ الإضافة/المرجع/التصنيف. يرجع عدد الأسهم المُحدّثة."""
    if wl.get("logic_version") == LOGIC_VERSION:
        return 0
    active = [s for s in wl.get("stocks", []) if s.get("status") == "active"]
    migrated = 0
    for s in active:
        df = history.get(s["symbol"])
        if df is None or len(df) < CONFIG["MIN_BARS"]:
            continue
        try:
            fresh = analyze_ticker(s["symbol"], df)
        except Exception:
            fresh = None
        if fresh is None:
            continue
        # تحديث القيم المحسوبة بالمنطق الجديد (entry_ref/added/tier تبقى)
        s["entry"] = [round(fresh["entry"][0], 4), round(fresh["entry"][1], 4)]
        s["tranches"] = [round(p, 4) for p in fresh["tranches"]]
        s["pivot"] = round(fresh["pivot"], 4)
        s["stop"] = round(fresh["stop"][0], 4)
        s["stop_hi"] = round(fresh["stop"][1], 4)
        s["t1"] = round(fresh["t1"], 4)
        s["t2"] = round(fresh["t2"], 4)
        s["t3"] = round(fresh["t3"], 4)
        s["key_levels"] = fresh.get("key_levels")
        s["liberation"] = fresh.get("liberation")
        # حقول مشتقّة من السعر تتغيّر مع الوقف/الأهداف → نحدّثها معها حتى لا
        # يظهر RR قديم بجانب وقف/أهداف جديدة (تناقض). أمّا score/flags/h4/
        # float/short فمشتقّة من الإثراء (شبكة) ويعاد بناؤها كاملةً جمعةَ التجديد.
        s["rr"] = fresh.get("rr")
        s["drop_pct"] = fresh.get("drop_pct")
        s["best_spike"] = fresh.get("best_spike")
        migrated += 1
    # لا نختم نسخة المنطق إلا لو رُحّل كل سهم نشط فعلًا — لو خُنقت البيانات
    # وتُخطّي بعضها نُبقي النسخة القديمة فيُعاد الترحيل لاحقًا (لا عَلَم زائف
    # يترك قيمًا قديمة بلا تحديث). إصلاح فحص 2026-06-24.
    if migrated == len(active):
        wl["logic_version"] = LOGIC_VERSION
    if migrated:
        log(f"ترحيل القائمة لنسخة المنطق {LOGIC_VERSION}: "
            f"حُدّث {migrated} سهم تلقائيًا")
    return migrated


def check_promotions(wl: dict, history: dict) -> list:
    """التحديث اليومي الحيّ لكل سهم نشط (إعادة تحليل بالبيانات الحالية):
    النواقص الحالية + المستويات + وسم «تخفيف: كسر الدعم» + تجديد التفسير.
    🪦 الترقية B→A تقاعدت مع التصنيف (2026-07-05: A وهمية — 0 سهم بلغها،
    والنجاح لا يميّزها) — الدالة تُبقي اسمها للتوافق وترجع [] دائمًا
    (run_daily_watchlist يمرّرها لبانر الترقيات الذي لن يظهر)."""
    promoted = []
    for s in wl.get("stocks", []):
        if s.get("status") != "active":
            continue
        df = history.get(s["symbol"])
        if df is None or len(df) < CONFIG["MIN_BARS"]:
            continue
        fresh = analyze_ticker(s["symbol"], df)
        if fresh is None:
            continue  # تعذّر إعادة التحليل (لا نغيّر حالته)
        # الشورت/الفلوت (M13/M14) يُحسبان في الفرز لا في analyze — نحتفظ بهما
        prev_extra = [x for x in s.get("soft_fails", [])
                      if "شورت" in x or "فلوت" in x]
        combined = list(fresh.get("soft_fails", []))
        combined += [x for x in prev_extra if x not in combined]
        # وسم خبر التخفيف لو ظهر «تأثير سلبي فعلي» (قرار المستخدم): كسر الدعم
        # أو قاع أدنى جديد → يُضاف للنواقص المعروضة، ويزول لمّا يستقر فوق الدعم.
        if s.get("news_risk"):
            piv = s.get("pivot")
            last = float(fresh.get("price") or df["Close"].iloc[-1])
            recent_low = float(df["Low"].tail(5).min())
            broke = bool(piv) and (last < piv or recent_low < piv * 0.99)
            tag = "تخفيف: كسر الدعم"
            if broke and tag not in combined:
                combined.append(tag)
        was = s.get("tier", "B")
        s["soft_fails"] = combined            # نحفظ النواقص (تُعرض) — تأثير خبر التخفيف باقٍ
        s["tier"] = "W" if was == "W" else "B"  # 🪦 A متقاعد → يبقى "B" (لا إحياء لـA)
        s["liberation"] = fresh.get("liberation")
        s["tf_count"] = fresh.get("tf_count")
        s["tf_display"] = fresh.get("tf_display")
        # تحديث يومي رخيص (بلا تحميل زائد): المستويات من إعادة التحليل +
        # القطاع/الدولة من الذاكرة لو ناقصة بالسجل (تظهر بدل ما تبقى فاضية).
        if fresh.get("key_levels"):
            s["key_levels"] = fresh["key_levels"]
        _cc = COMPANY_CACHE.get(s["symbol"], {})
        if not s.get("sector") and _cc.get("sector"):
            s["sector"] = _cc["sector"]
        if not s.get("country") and _cc.get("country"):
            s["country"] = _cc["country"]
        # استرجاع فلوت/شورت من الذاكرة لو ناقصة (تغطية ثابتة — لا تختفي)
        if not s.get("float") and _cc.get("float"):
            s["float"] = _cc["float"]
        if s.get("short") is None and _cc.get("finra_short") is not None:
            s["short"] = _cc["finra_short"]
        if not s.get("short_pct") and _cc.get("short_pct"):
            s["short_pct"] = _cc["short_pct"]
        # 🧭 تجديد التفسير بعد تحديث المستويات (مراجعة 2026-07-08: توحيد أعمار
        # الحواجز — بدونه min() بالرقم الحرج يقارن ترند اليوم بمقاومات الأمس،
        # لأن check_promotions يجدّد key_levels **بعد** تجديد update_watchlist_status
        # للتفسير). عرض فقط، بحارس لا-يمسح.
        try:
            _ipn = build_interpretation(s)
            if _ipn:
                s["interp"] = _ipn
        except Exception:
            pass
    return promoted


def compute_readiness(wl: dict, history: dict) -> None:
    """حساب نسبة الجاهزية اليومية لكل سهم نشط + الترتيب بها"""
    for s in wl["stocks"]:
        df = history.get(s["symbol"])
        if df is None or len(df) < 60:
            s["readiness"] = None
            s["have"], s["partial"], s["missing"] = [], [], []
            continue
        pct, comp = entry_readiness(df)
        s["readiness"] = pct
        s["have"] = [k for k, (p, m) in comp.items() if p >= m]
        s["partial"] = [k for k, (p, m) in comp.items() if 0 < p < m]
        s["missing"] = [k for k, (p, m) in comp.items() if p == 0]
    wl["stocks"].sort(
        key=lambda s: -(s["readiness"] if s["readiness"] is not None else -1))


def readiness_badge(p):
    """شارة الجاهزية (🪦 وسيط tier أُزيل مع تقاعد A/B — الجاهزية وحدها المحور)."""
    if p is None:
        return "⚠️ لا بيانات"
    if p >= CONFIG["READY_PCT"]:
        # 🪦 A/B متقاعد: الجاهزية هي المحور — تجاوز عتبة الجاهزية = «جاهز» للجميع.
        return f"<b>{p}%</b> 🟢 جاهز"
    if p >= CONFIG["NEAR_PCT"]:
        return f"<b>{p}%</b> 🟡 يقترب"
    return f"<b>{p}%</b> 🔴 إعداد فني ضعيف"


def readiness_ratio(p):
    """«نسبة الدخول/الجاهزية» بصيغة X/100 + حالتها (🟢🟡🔴) — تنسيق موحّد
    للبطاقة والتقرير اليومي (مصدر واحد، لا اختلاف)."""
    if p is None:
        return "نسبة الدخول/الجاهزية غير متاحة"
    status = readiness_badge(p).split("</b>")[-1].strip()
    return f"نسبة الدخول/الجاهزية <b>{p}/100</b> {status}"


def entry_status(s: dict) -> dict:
    """🟢👀 حالة الدخول العملية (خطة ENTRY_READY_SPLIT_PLAN.md — طلب المستخدم
    2026-07-08: «فرّق بين سهم جاهز للدخول وسهم متابعة»). **عرض/تصنيف-عرضي فقط**:
    لا يمسّ الفرز/الاختيار/الترتيب/الأهداف/الوقف · لا LOGIC_VERSION.

    القرار من **موقع السعر** (منهجية المقطع P0-5: قرار فيصل = قرب الدعم/بعد مسح، لا
    اكتمال بوابات ولا عتبة جاهزية) — مصدره الوحيد `entry_mode` المحسوب أصلًا في
    `build_interpretation` (يتجدّد يوميًا). **الجاهزية لا تدخل القرار إطلاقًا** (قفل
    ضد تكرار عتبة 75 الفاضية). فاشل-آمن → «متابعة» بسبب صريح. يرجّع:
      {"status": "ready_now"|"watch", "label": "🟢 جاهز للدخول الآن"|"👀 متابعة",
       "reason": نص عربي مبسّط (فارغ للجاهز)}"""
    try:
        em = (s.get("interp") or {}).get("entry_mode") or {}
        mode = em.get("mode")
        reason = em.get("reason") or ""
        if mode is None:
            # احتياط السجلّات القديمة بلا interp: نفس صيغ build_interpretation حرفيًا
            lp = float(s.get("last_price") or s.get("price") or 0)
            trs = [float(x) for x in (s.get("tranches") or []) if x]
            _st = s.get("stop")
            stop0 = (float(_st[0]) if isinstance(_st, (list, tuple)) and _st
                     else (float(_st) if isinstance(_st, (int, float)) else None))
            piv = float(s.get("pivot") or 0)
            if lp <= 0 or not trs or piv <= 0:
                return {"status": "watch", "label": "👀 متابعة",
                        "reason": "بيانات ناقصة لتقييم وضع الدخول"}
            hi_z = max(trs)
            if stop0 and lp <= stop0:
                mode, reason = "no_entry_far", "كسر الوقف — الفكرة ملغاة/خطرة"
            elif lp < piv * 0.995:
                mode, reason = "reclaim_wait", "تحت الدعم — ننتظر استعادته"
            elif lp > hi_z * 1.05:
                mode, reason = "no_entry_far", "بعيد فوق منطقة الدفعات"
            else:
                mode, reason = "near_support", ""
        if mode in ("near_support", "sweep_confirmed"):
            return {"status": "ready_now", "label": "🟢 جاهز للدخول الآن",
                    "reason": ""}
        if mode == "reclaim_wait":
            return {"status": "watch", "label": "👀 متابعة",
                    "reason": "تحت الدعم — يتحوّل جاهزًا باستعادته"}
        # no_entry_far: كسر الوقف يبقى بلا لاحقة (خطر لا انتظار) · البُعد يوضّح كيف يعود
        if "كسر الوقف" in reason:
            return {"status": "watch", "label": "👀 متابعة", "reason": reason}
        return {"status": "watch", "label": "👀 متابعة",
                "reason": (reason or "بعيد عن منطقة الدفعات")
                + " — يتحوّل جاهزًا برجوعه لمنطقة الدفعات"}
    except Exception:
        return {"status": "watch", "label": "👀 متابعة",
                "reason": "تعذّر تقييم وضع الدخول"}


def build_hand_section(wl: dict) -> str:
    """🕵️ قسم مستقل مختصر (طلب المستخدم 2026-07-08: «أبي أسهم علامة المضارب في
    قائمة لحالها عشان ما أضيع من كثر بيانات الأسهم»): أسهم القائمة التي وراءها
    علامات يد (دليلان فأكثر) — قائمة نظيفة لحالها، سطر لكل سهم. عرض/تحذير فقط،
    لا يمسّ الفرز/الحالة/الترتيب المخزّن (partition عرضي فقط)."""
    rows = []
    for s in wl.get("stocks", []):
        if s.get("status") != "active":
            continue
        ev = hand_evidence(s)
        if len(ev) >= 2:
            rows.append((s, ev))
    if not rows:
        return ""
    # الجاهز للدخول أولًا (الأهم للمستخدم) ثم الأكثر أدلةً
    rows.sort(key=lambda x: (entry_status(x[0])["status"] != "ready_now",
                             -len(x[1])))
    lines = [f"🕵️ <b>أسهم فيها علامات يد ({len(rows)})</b>",
             "أسهم مُدارة — توقّع كسر دعوم مفتعل قبل الانطلاق، لا تتعجّل:"]
    for s, ev in rows:
        signs = " · ".join(e["sign"] for e in ev[:3])
        extra = f" +{len(ev) - 3}" if len(ev) > 3 else ""
        lp = s.get("last_price")
        px = f" ${lp:.2f}" if lp else ""
        es = entry_status(s)                  # الأهم: جاهز للدخول أم متابعة؟
        tag = "🟢 جاهز للدخول" if es["status"] == "ready_now" else "👀 متابعة"
        lines.append(f"• {tag} · <b>${s['symbol']}</b>{px} — {signs}{extra}")
    return _rtl_join(lines)


# ==========================================================
# ⚡ كنسة الدقيقة الحية (POLYGON_EDGE_PLAN §ب) — تأكيد مسح أدق بشموع الدقيقة
# ==========================================================
def polygon_minute_bars(sym: str, minutes: int = 90):
    """شموع الدقيقة الحية (آخر ~`minutes` دقيقة) من Polygon:
    `GET /v2/aggs/ticker/{sym}/range/1/minute/{from}/{to}`. **فاشل-آمن مطلق** →
    None عند غياب المفتاح/401/403/429/شبكة (يسقط للمسار اليومي، لا يعيق التنبيه).
    يرجّع [{'o','h','l','c','v'}...] بترتيب زمني تصاعدي، أو None."""
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        return None
    try:
        h = {"Authorization": f"Bearer {key}"}
        now_ms = int(time.time() * 1000)
        frm = now_ms - int(minutes) * 60_000
        url = (f"https://api.polygon.io/v2/aggs/ticker/{sym.upper()}"
               f"/range/1/minute/{frm}/{now_ms}?adjusted=true&sort=asc&limit=500")
        r = requests.get(url, headers=h, timeout=10)
        if r.status_code != 200:
            return None
        res = (r.json() or {}).get("results") or []
        # 🔬 E2 (§9): نحفظ الطابع الزمني `t` (بداية شمعة الدقيقة، ms) — مطلوب لقياس الأبكرية/
        # الـlatency في القياس الظلّي. **حقل إضافي فقط** (المستهلكون يقرؤون c/v/l/h فلا يتأثّرون).
        bars = [{"o": b.get("o"), "h": b.get("h"), "l": b.get("l"),
                 "c": b.get("c"), "v": b.get("v"), "t": b.get("t")} for b in res
                if b.get("l") is not None and b.get("c") is not None]
        return bars or None
    except Exception:
        return None


def _minute_sweep(bars: list, support: float) -> bool:
    """كشف نقي (بلا شبكة) لكنسة السيولة بشموع الدقيقة (قاعدة فيصل «مسح ثم استعادة»):
    أدنى دقيقة خرقت الدعم بأكثر من 2% (`< support*0.98`) **ثم آخر إغلاق دقيقة استعاد
    فوقه** (`>= support`). خرق بلا استعادة = False · بلا خرق = False. قابل للاختبار."""
    try:
        if not bars or support <= 0:
            return False
        low_min = min(float(b["l"]) for b in bars if b.get("l") is not None)
        last_close = float(bars[-1]["c"])
        return low_min < support * 0.98 and last_close >= support
    except Exception:
        return False


# ==========================================================
# 🌙 رادار البريماركت (POLYGON_EDGE_PLAN §ج) — تحرّك ما قبل الافتتاح + session_ctx صادق
# ==========================================================
def _premarket_summary(bars: list, prev_close=None):
    """ملخّص البريماركت من شموع الدقيقة (دالّة نقيّة، بلا شبكة): أعلى/أدنى/آخر سعر +
    حجم تراكمي + التغيّر% عن إغلاق الأمس (لو مُرّر `prev_close`). None لو لا بارات.
    قابلة للاختبار — قلب رادار البريماركت وإكمال session_ctx الصادق."""
    try:
        if not bars:
            return None
        highs = [float(b["h"]) for b in bars if b.get("h") is not None]
        lows = [float(b["l"]) for b in bars if b.get("l") is not None]
        if not highs or not lows:
            return None
        last = float(bars[-1]["c"])
        cum_vol = sum(float(b["v"]) for b in bars if b.get("v") is not None)
        chg = (round((last / prev_close - 1.0) * 100.0, 1)
               if prev_close and prev_close > 0 else None)
        return {"kind": "premarket", "high": round(max(highs), 4),
                "low": round(min(lows), 4), "last": round(last, 4),
                "cum_vol": cum_vol, "change_pct": chg}
    except Exception:
        return None


def market_session_now(now=None):
    """⑤ (إصلاح تدقيق 2026-07-12) نوافذ جلسة ناسداك **بالدقائق-UTC لليوم الجاري**،
    مشتقة من توقيت نيويورك فتتصيّف/تتشتّى آليًا. الثوابت الصيفية المثبّتة (13:30
    افتتاحًا · 20:00 إغلاقًا) كانت تجعل المراقبة شتاءً (الافتتاح الفعلي 14:30 UTC)
    تقرأ شمعة **أمس** كأنها حيّة وتستهلك خانة الدِدوب فيُكتَم التنبيه الحقيقي.
    يرجع: pre_start (بريماركت 04:00 نيويورك) · open (09:30) · close (16:00).
    الثلاثة داخل نفس يوم UTC فلا التفاف منتصف الليل. **فاشل-آمن: أي خطأ →
    ثوابت الصيف = سلوك اليوم حرفيًا.** `now` قابل للحقن للاختبار (aware UTC)."""
    try:
        from zoneinfo import ZoneInfo
        ny = ZoneInfo("America/New_York")
        now_utc = now or dt.datetime.now(dt.timezone.utc)
        d = now_utc.astimezone(ny).date()

        def _mins(h, m=0):
            t = dt.datetime(d.year, d.month, d.day, h, m,
                            tzinfo=ny).astimezone(dt.timezone.utc)
            return t.hour * 60 + t.minute
        return {"pre_start": _mins(4, 0), "open": _mins(9, 30),
                "close": _mins(16, 0)}
    except Exception:
        return {"pre_start": 8 * 60, "open": 13 * 60 + 30, "close": 20 * 60}


def polygon_premarket(sym: str, prev_close=None):
    """🌙 ملخّص بريماركت اليوم من دقائق Polygon (شموع اليوم قبل افتتاح السوق).
    **فاشل-آمن مطلق** → None عند: غياب المفتاح · خارج نافذة البريماركت (قبل 08:00 أو
    بعد 13:30 UTC — فحص زمني **قبل** الشبكة، فصفر نداء مهدور بالفرز الباكر 07:00) ·
    401/403/429/شبكة. يرجّع dict `_premarket_summary` أو None. عرض/تنبيه فقط."""
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        return None
    try:
        now = dt.datetime.utcnow()
        _m = now.hour * 60 + now.minute
        # ⑤ نافذة البريماركت مشتقة من توقيت نيويورك (شتاءً تنزاح ساعة تلقائيًا)
        _w = market_session_now()
        if _m < _w["pre_start"] or _m >= _w["open"]:  # خارج النافذة → None فورًا
            return None
        h = {"Authorization": f"Bearer {key}"}
        today = dt.date.today().isoformat()
        url = (f"https://api.polygon.io/v2/aggs/ticker/{sym.upper()}"
               f"/range/1/minute/{today}/{today}?adjusted=true&sort=asc&limit=1000")
        r = requests.get(url, headers=h, timeout=10)
        if r.status_code != 200:
            return None
        res = (r.json() or {}).get("results") or []
        bars = [{"o": b.get("o"), "h": b.get("h"), "l": b.get("l"),
                 "c": b.get("c"), "v": b.get("v")} for b in res
                if b.get("c") is not None]
        return _premarket_summary(bars, prev_close)
    except Exception:
        return None


def polygon_after_hours(sym: str, regular_close=None):
    """🌆 ملخّص ما بعد الإغلاق (ضغط/تصريف المضارب — نمط LABT الحيّ). دقائق اليوم من
    Polygon، آخر سعر (أفتر) مقابل إغلاق الجلسة النظامية `regular_close`. **فحص زمني
    قبل الشبكة: None قبل 20:00 UTC (الجلسة لم تُغلق) = صفر نداء مهدور** · فاشل-آمن →
    None (بلا مفتاح/401/403/429/شبكة). يعيد استخدام `_premarket_summary` (آخر بار مقابل
    المرجع) بـ`kind='afterhours'`. عرض/تنبيه فقط — خارج الفرز."""
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        return None
    try:
        now = dt.datetime.utcnow()
        # ⑤ عتبة الأفتر = إغلاق الجلسة النظامية بتوقيت نيويورك (20:00 صيفًا/21:00 شتاءً UTC)
        if now.hour * 60 + now.minute < market_session_now()["close"]:
            return None
        h = {"Authorization": f"Bearer {key}"}
        today = dt.date.today().isoformat()
        url = (f"https://api.polygon.io/v2/aggs/ticker/{sym.upper()}"
               f"/range/1/minute/{today}/{today}?adjusted=true&sort=asc&limit=1000")
        r = requests.get(url, headers=h, timeout=10)
        if r.status_code != 200:
            return None
        res = (r.json() or {}).get("results") or []
        bars = [{"o": b.get("o"), "h": b.get("h"), "l": b.get("l"),
                 "c": b.get("c"), "v": b.get("v")} for b in res
                if b.get("c") is not None]
        s = _premarket_summary(bars, regular_close)   # آخر بار (أفتر) مقابل الإغلاق
        if s:
            s["kind"] = "afterhours"
        return s
    except Exception:
        return None


def monitor_live_events(wl: dict, history: dict, today_iso: str,
                        premarket_only: bool = False,
                        fetch_operator=None, fetch_afterhours=None) -> list:
    """🚨 كشف الأحداث اللحظية على أسهم القائمة (كل 30د بالسوق — طلب المستخدم
    2026-07-08) للتنبيه الفوري بلحظات التنفيذ/الخطر:
      • `sweep`    : كنس دعم بذيل ثم استعادة (لحظة فيصل «مسح ثم استعادة»).
      • `buyzone`  : دخل منطقة الشراء (لحظة تنفيذ الدفعات نفسها).
      • `break`    : كسر الوقف/الدعم وأغلق تحته (خطر — الفكرة مهدّدة).
      • `breakout` : تجاوز الرقم الحرج (يفعّل الهدف التالي).
      • `premarket`: 🌙 تحرّك ما قبل الافتتاح (Polygon حي — POLYGON_EDGE_PLAN §ج).
    **دِدوب مرة/سهم/حدث/يوم** (`s['live_alert'][kind]`) فلا تتكرّر كل 30د. يحدّث
    last_price. عرض/تنبيه فقط — خارج الفرز/الاختيار. يرجع [(s, kind, desc)].
    `premarket_only` (قبل الافتتاح 13:30 UTC — يمرّره pullback_live حسب الساعة):
    يتخطّى أحداث الجلسة (مسح/كسر/منطقة/تجاوز) لأن الشمعة اليومية وقتها = أمس (بايتة،
    فتُعيد إطلاق حالة الأمس صباحًا)، ويكتفي برادار البريماركت الحي من Polygon."""
    out = []
    for s in wl.get("stocks", []):
        if s.get("status") != "active":
            continue
        df = history.get(s["symbol"])
        if df is None or len(df) < 25:
            continue
        try:
            lp = round(float(df["Close"].iloc[-1]), 4)
            s["last_price"] = lp
        except Exception:
            continue
        # ⑤ حارس الشمعة البائتة (إصلاح تدقيق 2026-07-12): أحداث الجلسة تُقيَّم فقط
        # إذا كانت آخر شمعة بتاريخ **اليوم** — شتاءً كانت تشغيلات ما قبل الافتتاح
        # (بالثوابت الصيفية) تقرأ شمعة أمس كأنها حيّة، والأدهى أن الحدث الكاذب
        # يستهلك خانة الدِدوب الوحيدة فيُكتَم الحدث الحقيقي بقية اليوم. فاشل-آمن:
        # تعذّر قراءة تاريخ الشمعة → السلوك السابق (لا كتم زائد).
        try:
            _stale = df.index[-1].date().isoformat() != str(today_iso)[:10]
        except Exception:
            _stale = False
        trs = [float(x) for x in (s.get("tranches") or []) if x]
        _st = s.get("stop")
        stop0 = (float(_st[0]) if isinstance(_st, (list, tuple)) and _st
                 else (float(_st) if isinstance(_st, (int, float)) else None))
        piv = float(s.get("pivot") or 0)
        events = []
        # أحداث الجلسة (تحتاج سعر الجلسة الحي) — تُتخطّى قبل الافتتاح (premarket_only)
        # و⑤ عند شمعة بائتة (تاريخها ≠ اليوم = السوق لم يفتح/البيانات متأخرة).
        if not premarket_only and not _stale:
            try:
                sw = next((a for a in hand_activity_today(s, df)
                           if "كنس الدعم" in a), None)
            except Exception:
                sw = None
            # ⚡ تأكيد أدق بشموع الدقيقة (POLYGON_EDGE_PLAN §ب): **لو** المفتاح موجود
            # والمسار اليومي لم يرصد المسح، افحص دقائق Polygon على نفس الدعم (أدنى 20ج).
            # نفس نوع الحدث (sweep) ونفس الدِدوب — لا نوع جديد. بلا مفتاح = المسار
            # اليومي حرفيًا (polygon_minute_bars ترجع None → _minute_sweep=False).
            if not sw and os.environ.get("POLYGON_API_KEY", "").strip():
                try:
                    _lo = df["Low"].values.astype(float)
                    _sup20 = float(np.min(_lo[-21:-1]))
                    # سقف الطلبات (يحمي ميزانية المراقب 15د): نفحص الدقائق فقط
                    # للأسهم **قرب دعمها** (ضمن 8% فوقه) حيث المسح ممكن. البعيد لا
                    # يُمسح، والمسح-ثم-الركض البعيد يلتقطه المسار اليومي (كسر+ارتفاع).
                    if _sup20 > 0 and lp <= _sup20 * 1.08:
                        _mb = polygon_minute_bars(s["symbol"])
                        if _mb and _minute_sweep(_mb, _sup20):
                            sw = (f"كنس الدعم ${_sup20:.2f} بذيل ثم استعاده "
                                  "(تأكيد دقائق Polygon)")
                except Exception:
                    pass
            if sw:
                events.append(("sweep", sw))
            if stop0 is not None and lp <= stop0:
                events.append(("break",
                               f"كسر الوقف ${stop0:.2f} — الفكرة ملغاة/خطرة"))
            elif piv and lp < piv * 0.995:
                events.append(("break", f"كسر الدعم ${piv:.2f} وأغلق تحته — خطر"))
            elif trs and min(trs) <= lp <= max(trs) * 1.005:
                events.append(("buyzone", f"دخل منطقة الشراء "
                               f"(${min(trs):.2f}–${max(trs):.2f}) — لحظة التنفيذ"))
            crit = (s.get("interp") or {}).get("critical_number") or {}
            cp = crit.get("price")
            if cp and crit.get("type") == "breakout_activation" \
                    and lp > float(cp) * 1.005:
                events.append(("breakout", f"تجاوز الرقم الحرج ${float(cp):.2f} "
                               "— يفعّل الهدف التالي"))
            # 📉 ضغط/تصريف المضارب (طلب المستخدم 2026-07-09، نمط LABT): هبوط اليوم
            # الحادّ عن إغلاق الأمس = المضارب يضغط السهم للهاوية. مستقل عن break (قد
            # يتزامنان بمعلومة مختلفة: dump=هبوط حادّ · break=كسر مستوى). تنبيه خطر.
            try:
                _pc = float(df["Close"].iloc[-2])
                if _pc > 0 and lp <= _pc * (1 - CONFIG["PRESS_DROP_PCT"] / 100.0):
                    events.append(("dump", f"ضغط المضارب: هبوط "
                                   f"{(lp / _pc - 1) * 100:.0f}% عن إغلاق الأمس "
                                   f"${_pc:.2f} — تصريف (نمط LABT)"))
            except Exception:
                pass
        # 🌙 تحرّك بريماركت (POLYGON_EDGE_PLAN §ج): فقط بوجود المفتاح وداخل نافذة
        # البريماركت (polygon_premarket تُرجع None خارجها/بلا مفتاح فورًا). تحرّك
        # ≥PM_MOVE_PCT بحجم بريماركت >0 → «راقب الافتتاح». إغلاق الأمس = آخر إغلاق
        # يومي (البريماركت لم يفتح بعد فآخر بار = أمس). فاشل-آمن → لا حدث.
        if os.environ.get("POLYGON_API_KEY", "").strip():
            try:
                _prev = float(df["Close"].iloc[-1])
                _pm = polygon_premarket(s["symbol"], prev_close=_prev)
                if (_pm and _pm.get("change_pct") is not None
                        and abs(_pm["change_pct"]) >= CONFIG["PM_MOVE_PCT"]
                        and (_pm.get("cum_vol") or 0) > 0):
                    _sg = "+" if _pm["change_pct"] >= 0 else ""
                    events.append(("premarket",
                                   f"تحرّك بريماركت {_sg}{_pm['change_pct']:.0f}% "
                                   f"بحجم {_pm['cum_vol']:,.0f} — راقب الافتتاح"))
            except Exception:
                pass
        # 📉 ضغط المضارب بعد الإغلاق (الأفتر — نمط LABT الحيّ، طلب المستخدم): هبوط حادّ
        # بالأفتر عن إغلاق الجلسة = تصريف المضارب (LABT هبط 3.10→1.97 بالأفتر). فحص زمني
        # داخل polygon_after_hours (None قبل 20:00 UTC) · بلا مفتاح = لا حدث · فاشل-آمن.
        _fah = fetch_afterhours or (polygon_after_hours
                                    if os.environ.get("POLYGON_API_KEY", "").strip()
                                    else None)
        if _fah:
            try:
                _rc = float(df["Close"].iloc[-1])     # إغلاق الجلسة النظامية (آخر شمعة)
                _ah = _fah(s["symbol"], _rc)
                if (_ah and _ah.get("change_pct") is not None
                        and _ah["change_pct"] <= -CONFIG["PRESS_DROP_PCT"]):
                    events.append(("afterdump",
                                   f"ضغط المضارب بالأفتر: هبوط {_ah['change_pct']:.0f}% "
                                   f"عن الإغلاق ${_rc:.2f} — تصريف (نمط LABT)"))
            except Exception:
                pass
        # 🕵️ بوّابة المضارب على الأحداث الإيجابية (طلب المستخدم 2026-07-09 — كلا
        # النظامين): لا تنبيه مسح/دخول/تجاوز إلا لو دخل المضارب (طبعات ≥
        # OPERATOR_MIN_SHARES). الخطر (break) والبريماركت لا يُبوَّبان (تنبيه واجب/مغطّى).
        # فاشل-آمن: تعذّر القياس (None) → لا نكتم (لا نفوّت حدثًا حقيقيًا بعطل شبكي)؛
        # وُجد المضارب → نُلحق كمياته بوصف الحدث المبوَّب.
        _gated = {"sweep", "buyzone", "breakout"}
        _fo = fetch_operator or (operator_flow
                                 if os.environ.get("POLYGON_API_KEY", "").strip()
                                 else None)
        if _fo and events and any(k in _gated for k, _ in events):
            try:
                _of = _fo(s["symbol"])
            except Exception:
                _of = None
            if _of is not None and not _of.get("has_operator"):
                events = [(k, d) for k, d in events if k not in _gated]
            elif _of is not None:
                _ol = operator_line(_of, s)
                # 💧 سبريد لحظي (اشتراك المستخدم Polygon Advanced لحظي — الجلسة مفتوحة
                # وقت المراقب فالسبريد حقيقي، خلاف تقرير السبت بعد الإغلاق). فيصل يبدأ
                # بدفتر الأوامر — تحذير سيولة عند الدخول. مختصر · فاشل-آمن ('' لو طبيعي).
                _spl = spread_line(_of.get("bid"), _of.get("ask"), brief=True)
                _tail = _ol + ((" · " + _spl) if _spl else "")
                events = [(k, (d + " · " + _tail) if k in _gated else d)
                          for k, d in events]
        seen = s.setdefault("live_alert", {})
        for kind, desc in events:
            if seen.get(kind) != today_iso:
                seen[kind] = today_iso               # دِدوب: مرة/حدث/يوم
                out.append((s, kind, desc))
    return out


_LIVE_ICON = {"sweep": "🚨", "buyzone": "🎯", "break": "⛔", "breakout": "🚀",
              "premarket": "🌙", "dump": "📉", "afterdump": "📉"}

# فاصل شرطات بين أسهم التقرير اليومي (طلب المستخدم 2026-07-09: «ارفع شرطات» بين كل سهم)
DAILY_CARD_SEP = "━━━━━━━━━━━━━━━"


def polygon_flow(sym: str):
    """📊 تدفق الأوامر الحقيقي من Polygon (اشتراك المستخدم — **طبقة اختيارية بالكامل**):
    NBBO حي (أفضل عرض/طلب + أحجام) + نسبة الشراء/البيع من آخر ~100 صفقة (صفقة عند/فوق
    منتصف السعر = شراء عدواني · تحته = بيع — قاعدة Lee-Ready المبسّطة). **فاشل-آمن
    تمامًا** → None عند: غياب المفتاح · انتهاء الاشتراك (401/403) · حد الطلبات (429) ·
    أي خطأ شبكي/رد. **لا يعيق الفحص إطلاقًا** (طلب المستخدم: «شرطة، لا تعطيل»). المفتاح
    يُقرأ وقت النداء (غيابه = None فورًا). عرض فقط — خارج الفرز نهائيًا."""
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        return None
    try:
        base, h = "https://api.polygon.io", {"Authorization": f"Bearer {key}"}
        s = sym.upper()
        q = requests.get(f"{base}/v2/last/nbbo/{s}", headers=h, timeout=12)
        if q.status_code != 200:
            return None
        res = (q.json() or {}).get("results") or {}
        bid, ask = res.get("p"), res.get("P")       # p=أفضل طلب · P=أفضل عرض
        bsz, asz = res.get("s"), res.get("S")
        if not (bid and ask and ask > 0):
            return None
        out = {"bid": float(bid), "ask": float(ask),
               "bid_size": bsz, "ask_size": asz,
               "spread_pct": round((ask - bid) / ask * 100.0, 1),
               "buy_pct": None, "sell_pct": None, "n_trades": 0}
        try:
            mid = (float(bid) + float(ask)) / 2.0
            tr = requests.get(f"{base}/v3/trades/{s}",
                              headers=h, params={"limit": 100, "order": "desc"},
                              timeout=12)
            if tr.status_code == 200:
                trades = (tr.json() or {}).get("results") or []
                prices = [t.get("price") for t in trades if t.get("price")]
                if prices:
                    buys = sum(1 for p in prices if p >= mid)
                    out["n_trades"] = len(prices)
                    out["buy_pct"] = round(buys / len(prices) * 100.0)
                    out["sell_pct"] = 100 - out["buy_pct"]
        except Exception:
            pass
        return out
    except Exception:
        return None


def order_snapshot(sym: str):
    """📊 تدفق/لقطة الأوامر — **طبقة اختيارية فاشلة-آمنة** (طلب المستخدم: لا تعيق
    الفحص أبدًا؛ تعذّرها = «—»): تُفضّل تدفق Polygon الحي (اشتراك المستخدم)، وإلا
    لقطة Yahoo الوحيدة، وإلا None (فيُعرض «—»). Level 2 غير مستعمل. عرض فقط."""
    pf = polygon_flow(sym)              # 1) تدفق حي من Polygon (إن توفّر الاشتراك)
    if pf:
        parts = []
        if pf.get("buy_pct") is not None:
            parts.append(f"{pf['buy_pct']:.0f}% شراء · {pf['sell_pct']:.0f}% بيع "
                         f"(آخر {pf['n_trades']} صفقة)")
        parts.append(f"طلب ${pf['bid']:.2f}"
                     + (f"×{pf['bid_size']}" if pf.get('bid_size') else "")
                     + f" · عرض ${pf['ask']:.2f}"
                     + (f"×{pf['ask_size']}" if pf.get('ask_size') else ""))
        return "🟢 تدفق حي (Polygon): " + " · ".join(parts)
    if yf is None:                     # 2) احتياط: لقطة Yahoo الوحيدة
        return None
    try:
        info = _fetch_info(yf.Ticker(sym))
        bid, ask = info.get("bid"), info.get("ask")
        if not (bid and ask and ask > 0):
            return None
        bs, ask_sz = info.get("bidSize"), info.get("askSize")
        spread = round((ask - bid) / ask * 100.0, 1)
        return (f"لقطة Yahoo: شراء ${bid:.2f}" + (f"×{bs}" if bs else "")
                + f" · بيع ${ask:.2f}" + (f"×{ask_sz}" if ask_sz else "")
                + f" · سبريد {spread:.0f}%")
    except Exception:
        return None


# ==========================================================
# 🔬 رادار التجميع الصامت (POLYGON_EDGE_PLAN §أ) — من الصفقات الخام عند القاع
# ==========================================================
def _tick_classify(prices: list) -> list:
    """قاعدة التيك (tick rule — نقية، قابلة للاختبار): صفقة أعلى من سابقتها =
    شراء عدواني (+1) · أدنى = بيع (-1) · مساوية = اتجاه آخر صفقة مصنّفة (0 لو لم
    يسبقها اتجاه). الأولى دائمًا 0 (لا سابق). يرجع قائمة بطول prices."""
    out = []
    last_dir = 0
    prev = None
    for p in prices:
        if prev is None:
            out.append(0)
        elif p > prev:
            last_dir = 1
            out.append(1)
        elif p < prev:
            last_dir = -1
            out.append(-1)
        else:
            out.append(last_dir)
        prev = p
    return out


def acc_components(trades: list):
    """🔬 مكوّنات التجميع الصامت من صفقات خام [{'price','size','exchange'}...]
    (نقية، بلا شبكة — قلب رادار التجميع). **عرض/تشخيص فقط — لا تدخل أي فرز/ترتيب
    قبل نجاح تجربة T-ACC** (POLYGON_EDGE_PLAN §أ-4). يرجع dict أو None لو أقل من
    30 صفقة (عيّنة غير كافية — صدق):
      • aggressive_buy_pct: حجم الشراء العدواني (تيك رول +1) ÷ الحجم المصنَّف ×100.
      • block_share_pct: حجم الطبعات الكبيرة (≥10× **وسيط** أحجام هذه العيّنة —
        نسبي ذاتي المعايرة، لا رقم مطلق) ÷ الحجم الكلي ×100.
      • dark_share_pct: حجم صفقات الدارك/خارج البورصة ÷ الكلي ×100. Polygon يرمز
        الطبعات المُبلَّغة عبر FINRA TRF (خارج البورصة = دارك) بـ exchange==4 (موثّق).
      • block_buy_pct (🔬 T-ACC-2، `T_ACC2_PREREGISTRATION.md`): عدوانية الشراء **داخل
        الطبعات الكبيرة فقط** (اتجاه×حجم) = حجم الطبعات الكبيرة المصنَّفة شراءً ÷ المصنَّفة
        (شراء+بيع) ×100. None لو أقل من 5 طبعات مصنَّفة (نسبة على <5 = بلا معنى). محور
        مستقل عن الاتجاه العام والحجم العام — «هل المال الكبير هو المُبادِر بالشراء؟».
      • n_trades."""
    try:
        rows = [(float(t["price"]), float(t["size"]), t.get("exchange"))
                for t in trades if t.get("price") and t.get("size")]
        if len(rows) < 30:
            return None
        prices = [r[0] for r in rows]
        sizes = [r[1] for r in rows]
        total = sum(sizes)
        if total <= 0:
            return None
        dirs = _tick_classify(prices)
        buy_vol = sum(sz for d, sz in zip(dirs, sizes) if d > 0)
        sell_vol = sum(sz for d, sz in zip(dirs, sizes) if d < 0)
        classified = buy_vol + sell_vol
        agg_buy = round(buy_vol / classified * 100.0) if classified > 0 else None
        med = sorted(sizes)[len(sizes) // 2]              # وسيط أحجام العيّنة
        is_block = [sz >= 10 * med for sz in sizes] if med > 0 else [False] * len(sizes)
        block_vol = sum(sz for sz, b in zip(sizes, is_block) if b)
        # 🔬 T-ACC-2: عدوانية الشراء داخل الطبعات الكبيرة فقط (اتجاه×حجم، تسجيل مسبق)
        blk_buy = sum(sz for d, sz, b in zip(dirs, sizes, is_block) if b and d > 0)
        blk_sell = sum(sz for d, sz, b in zip(dirs, sizes, is_block) if b and d < 0)
        blk_n = sum(1 for d, b in zip(dirs, is_block) if b and d != 0)
        blk_cls = blk_buy + blk_sell
        block_buy = (round(blk_buy / blk_cls * 100.0)
                     if blk_n >= 5 and blk_cls > 0 else None)
        dark_vol = sum(sz for _p, sz, ex in rows if ex == 4)
        return {"aggressive_buy_pct": agg_buy,
                "block_share_pct": round(block_vol / total * 100.0),
                "block_buy_pct": block_buy,               # 🔬 T-ACC-2 (مسجَّل مسبقًا)
                "dark_share_pct": round(dark_vol / total * 100.0),
                "n_trades": len(rows)}
    except Exception:
        return None


def polygon_base_trades(sym: str, days: int = None, end_date=None,
                        cap: int = 150_000):
    """غلاف جلب صفقات نافذة القاع (BASE_WINDOW يوم تداول) من Polygon مع ترقيم صفحات
    حتى `cap`. `end_date` (ISO/date) = نهاية النافذة **حصريًا** (`timestamp.lt`) —
    للتجربة التاريخية بلا تسريب؛ None = حتى اليوم. **فاشل-آمن مطلق** → None عند
    غياب المفتاح/401/403/429/شبكة. يرجع [{'price','size','exchange'}...]."""
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        return None
    days = days or int(CONFIG["BASE_WINDOW"])
    try:
        h = {"Authorization": f"Bearer {key}"}
        end = end_date if end_date else dt.date.today()
        if isinstance(end, str):
            end = dt.date.fromisoformat(end[:10])
        start = (end - dt.timedelta(days=days * 2)).isoformat()
        url = (f"https://api.polygon.io/v3/trades/{sym.upper()}"
               f"?timestamp.gte={start}&limit=50000&order=asc")
        if end_date:                          # نهاية حصرية (بلا تسريب)
            url += f"&timestamp.lt={end.isoformat()}"
        out = []
        for _ in range(6):                                # حتى ~300k سقف صلب
            r = requests.get(url, headers=h, timeout=12)
            if r.status_code != 200:
                return out or None
            j = r.json() or {}
            for t in (j.get("results") or []):
                out.append({"price": t.get("price"), "size": t.get("size"),
                            "exchange": t.get("exchange")})
            nxt = j.get("next_url")
            if not nxt or len(out) >= cap:
                break
            url = nxt + f"&apiKey={key}" if "apiKey" not in nxt else nxt
        return out or None
    except Exception:
        return None


def silent_accumulation(sym: str):
    """🔬 درجة التجميع الصامت الحية لسهم (غلاف: polygon_base_trades ← acc_components).
    فاشل-آمن → None (يُعرض «—»). **عرض/تسجيل فقط، خارج الفرز نهائيًا** حتى تثبت T-ACC."""
    trades = polygon_base_trades(sym)
    return acc_components(trades) if trades else None


def acc_line(acc: dict) -> str:
    """سطر عرض التجميع الصامت (يظهر فقط لو acc موجود). عربي مبسّط."""
    if not acc:
        return ""
    parts = []
    if acc.get("aggressive_buy_pct") is not None:
        parts.append(f"شراء عدواني {acc['aggressive_buy_pct']}%")
    parts.append(f"طبعات كبيرة {acc.get('block_share_pct', 0)}%")
    parts.append(f"دارك {acc.get('dark_share_pct', 0)}%")
    return (f"🔬 تجميع صامت: {' · '.join(parts)} "
            f"(آخر {CONFIG['BASE_WINDOW']}ج)")


def build_live_alert(rows: list, quotes: dict = None) -> str:
    """رسالة تنبيه الأحداث اللحظية (مسح/دخول/كسر/تجاوز) — مختصرة (طلب المستخدم
    2026-07-09 «فيها فلسفة كثيرة»): سطر الحدث فقط، ومعلومات الأوامر تأتي داخل
    وصف الحدث المبوَّب بسطر المضارب المختصر (operator_line بلغة المتداول).
    أُسقطت «📊 لقطة الأوامر» وتذييلا ℹ️ (Lee-Ready/L2/Yahoo) — التفصيل وحدود
    الصدق بقيا في أداة فحص اليد فقط. `quotes` تُقبل وتُتجاهَل (توافق خلفي)."""
    if not rows:
        return ""
    lines = ["🚨 <b>أحداث لحظية على القائمة</b>",
             "لحظات تنفيذ/خطر — راقبها الآن:"]
    for s, kind, desc in rows:
        icon = _LIVE_ICON.get(kind, "•")
        es = entry_status(s)
        tag = "🟢 جاهز" if es["status"] == "ready_now" else "👀 متابعة"
        lp = s.get("last_price")
        px = f" ${lp:.2f}" if lp else ""
        lines.append(f"{icon} <b>${s['symbol']}</b>{px} · {tag} — {desc}")
    return _rtl_join(lines)


# ==========================================================
# 🕵️ كشف دخول المضارب من الطبعات الكبيرة (طلب المستخدم 2026-07-09: «علّمني لو دخل
# المضارب + كميات شرائه على الطلب — ولا يجيني إشعار إلا على شي يستاهل»). قاعدة فيصل:
# صفقة المضارب ≥1000 سهم · يشتري على الطلب (امتصاص) · يفرّغ العروض لحظة الرفع.
# **بوّابة تنبيه + عرض فقط — خارج الفرز/الاختيار.** حدّ الصدق: تصنيف تيك تقريبي + قمة
# الدفتر فقط (لا L2 كامل) — يُذكر صراحةً بالعرض.
# ==========================================================
def _operator_blocks(trades, min_shares):
    """نقيّة (بلا شبكة): من صفقات [(price, size)...] **بترتيب زمني تصاعدي**، تصنّف
    الطبعات الكبيرة (≥min_shares سهم) بقاعدة التيك:
      • buy_block_shares: طبعات صعودية (رفع/شراء عدواني من العرض — لحظة الإشعال).
      • bid_block_shares: طبعات هبوطية (بائع ضرب الطلب = امتصاص المضارب على الطلب —
        «الأوامر في الطلب» التي تهمّ المستخدم؛ تُوسم امتصاصًا محتملًا لا يقينًا).
      • n_blocks: عدد الطبعات ≥min_shares.
      • has_operator: وُجدت طبعة شراء (عدوانية أو على الطلب) ≥min_shares = المضارب دخل.
    يرجع dict أو None لو أقل من 20 صفقة (عيّنة غير كافية — صدق). **قياس/عرض فقط.**"""
    try:
        rows = [(float(p), float(s)) for p, s in trades if p and s]
        if len(rows) < 20:
            return None
        dirs = _tick_classify([p for p, _ in rows])
        buy = sum(sz for (p, sz), d in zip(rows, dirs) if sz >= min_shares and d > 0)
        bid = sum(sz for (p, sz), d in zip(rows, dirs) if sz >= min_shares and d < 0)
        n = sum(1 for (p, sz) in rows if sz >= min_shares)
        return {"n_blocks": n, "buy_block_shares": int(buy),
                "bid_block_shares": int(bid),
                "has_operator": (buy >= min_shares or bid >= min_shares)}
    except Exception:
        return None


def operator_flow(sym: str):
    """🕵️ كشف دخول المضارب من صفقات Polygon الخام (غلاف شبكي فاشل-آمن حول
    `_operator_blocks`). يجلب آخر ~250 صفقة + NBBO (جدار الطلب) → طبعات ≥
    `OPERATOR_MIN_SHARES` مصنَّفة (شراء عدواني/على الطلب). **فاشل-آمن مطلق → None**
    (بلا مفتاح/401/403/429/شبكة — لا يعيق شيئًا). المفتاح يُقرأ وقت النداء. عرض/تنبيه
    فقط — خارج الفرز. حدّ الصدق: تصنيف تيك تقريبي + قمة الدفتر فقط (لا L2)."""
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        return None
    try:
        base, h = "https://api.polygon.io", {"Authorization": f"Bearer {key}"}
        s = sym.upper()
        tr = requests.get(f"{base}/v3/trades/{s}", headers=h,
                          params={"limit": 250, "order": "desc"}, timeout=12)
        if tr.status_code != 200:
            return None
        trades = (tr.json() or {}).get("results") or []
        rows = [(t.get("price"), t.get("size")) for t in trades
                if t.get("price") and t.get("size")]
        rows.reverse()                       # Polygon يرجع desc → تصاعدي للتيك
        ob = _operator_blocks(rows, CONFIG["OPERATOR_MIN_SHARES"])
        if ob is None:
            return None
        try:     # جدارا الطلب والعرض (NBBO — نفس النداء، أفضل طلب/عرض + حجمهما)
            q = requests.get(f"{base}/v2/last/nbbo/{s}", headers=h, timeout=12)
            if q.status_code == 200:
                res = (q.json() or {}).get("results") or {}
                ob["bid"] = float(res["p"]) if res.get("p") else None
                ob["bid_size"] = res.get("s")
                ob["ask"] = float(res["P"]) if res.get("P") else None
                ob["ask_size"] = res.get("S")
                ob["quote_ts"] = res.get("t")   # 🔬 E2 (§13.1): طابع NBBO الزمني (quote_age)
        except Exception:
            pass
        return ob
    except Exception:
        return None


def _price_level_tag(price, s) -> str:
    """وسم موقع سعرٍ من مستويات السهم المخزّنة بلغة المتداول (طلب المستخدم
    2026-07-09: «المضارب طلب 1000 سهم فوق الدعم»): يختار أقرب مستوى معروف
    (وقف/دعم أساسي/فرعي/الرقم الحرج/مقاومة فرعية/أساسية) ويصف الموقع —
    «عند» ضمن 1.5%، وإلا «فوق/تحت». '' لو لا مستويات (فاشل-آمن). عرض فقط."""
    try:
        if not price or not s:
            return ""
        kl = s.get("key_levels") or {}
        crit = ((s.get("interp") or {}).get("critical_number") or {}).get("price")
        _st = s.get("stop")
        stop0 = (_st[0] if isinstance(_st, (list, tuple)) and _st else _st)
        levels = [("الوقف", stop0),
                  ("الدعم", kl.get("sup_major") or s.get("pivot")),
                  ("الدعم الفرعي", kl.get("sup_minor")),
                  ("الرقم الحرج", crit),
                  ("المقاومة الفرعية", kl.get("res_minor")),
                  ("المقاومة", kl.get("res_major"))]
        levels = [(n, float(v)) for n, v in levels if v]
        if not levels:
            return ""
        name, lvl = min(levels, key=lambda x: abs(price - x[1]) / x[1])
        rel = (price - lvl) / lvl
        if abs(rel) <= 0.015:
            return f" (عند {name} ${lvl:.2f})"
        return f" ({'فوق' if rel > 0 else 'تحت'} {name} ${lvl:.2f})"
    except Exception:
        return ""


def operator_line(of, s=None) -> str:
    """سطر «🕵️ المضارب» المختصر بلغة أوامر المتداول (طلب المستخدم 2026-07-09:
    «ابي شي مختصر جدا — المضارب طلب 1000 سهم فوق الدعم · عرض 5 آلاف عند
    المقاومة» — بلا فلسفة/نسب/حدود صدق؛ التفصيل والحدود بفحص اليد فقط):
    ما نفّذه (شرى على الطلب/رفع بشراء) + جدارا الطلب والعرض موسومَين بأقرب
    مستوى (`_price_level_tag` لو مُرّر السهم). «—» لو None. عرض فقط."""
    if not of:
        return "🕵️ المضارب: —"
    parts = []
    if of.get("bid_block_shares"):       # الأهم عند المستخدم: الشراء على الطلب
        parts.append(f"شرى على الطلب ~{of['bid_block_shares']:,} سهم")
    if of.get("buy_block_shares"):
        parts.append(f"رفع بشراء ~{of['buy_block_shares']:,} سهم")
    if not parts:
        parts.append(f"لا صفقات مضارب ({CONFIG['OPERATOR_MIN_SHARES']} سهم فأكثر)")
    def _wall(label, size, price):
        tag = _price_level_tag(price, s)
        if tag.startswith(" (عند "):     # الجدار عند مستوى ⇒ المستوى هو الموقع
            return f"{label} {size:,} سهم {tag[2:-1]} (${price:.2f})"
        return f"{label} {size:,} سهم عند ${price:.2f}{tag}"
    if of.get("bid") and of.get("bid_size"):
        parts.append(_wall("طلب", of["bid_size"], of["bid"]))
    if of.get("ask") and of.get("ask_size"):
        parts.append(_wall("عرض", of["ask_size"], of["ask"]))
    return "🕵️ المضارب: " + " · ".join(parts)


# ==========================================================
# 🔥 رادار الانطلاق اللحظي (IGNITION_PLAN.md) — عامل جلسة حي على القائمة المؤهّلة
# ==========================================================
# الفكرة (بعد أن أثبت T-ACC أن الاختيار عند القاع مستحيل): لا نتنبّأ بأيّ زنبرك ينفجر
# — بل نراقب القائمة المؤهّلة **كلها لحظيًّا** ونمسك **لحظة الاشتعال** (رد فعل لا تنبّؤ:
# الحجم والسعر حقيقيان، والتدفق يؤكّد). يسبق البوت على Yahoo بـ15-25د. أسرع تنفيذ لفرضية
# التوقيت اللحظي (فرضية بحثية ذات أولوية — **غير مثبتة حتى الآن**؛ E2 يقيسها).
# 🔒 خارج الفرز/الاختيار (القائمة مختارة مسبقًا) — تنبيه/توقيت فقط.
def _emit_trace(trace, event, payload_fn):
    """🔬 E2-A (قياس ظلّي · IGNITION MEASUREMENT §3): يبعث حدث funnel وصفيًّا فقط.
    **فاشل-آمن مطلق:** `trace=None` (الافتراضي) = صفر عمل = سلوك الرادار حرفيًّا · الحمولة
    دالّة (lazy) فلا تُبنى إلا عند وجود trace (زمن-صفر عند None) · أي استثناء (حتى في بناء
    الحمولة) يُبتلع فلا يمسّ التنبيه · لا يقرأ trace قرارًا ولا يعدّل سهمًا/إشارة/عتبة.
    🔒 قياس/توثيق فقط — خارج أي قرار فرز/اختيار/تنبيه."""
    if trace is None:
        return
    try:
        trace(event, payload_fn())
    except Exception:
        pass


def _ignition_break_source(s: dict) -> str:
    """🔬 E2: مصدر break_level (مواز لـ_ignition_break_level بلا تغييره): «critical_number»
    (الرقم الحرج) · «pivot_plus_5pct» (5% فوق الأرضية) · «none». قياس فقط."""
    crit = ((s.get("interp") or {}).get("critical_number") or {}).get("price")
    if crit:
        try:
            float(crit)
            return "critical_number"
        except (TypeError, ValueError):
            pass
    piv = s.get("pivot")
    try:
        return "pivot_plus_5pct" if piv and float(piv) else "none"
    except (TypeError, ValueError):
        return "none"


def _ignition_break_level(s: dict):
    """السعر الذي يعني «خرج من القاع صاعدًا» لسهم القائمة: الرقم الحرج (تفعيل فيصل
    NAMM) إن وُجد، وإلا 5% فوق الأرضية (pivot). None لو لا مرجع."""
    crit = ((s.get("interp") or {}).get("critical_number") or {}).get("price")
    if crit:
        try:
            return float(crit)
        except (TypeError, ValueError):
            pass
    piv = s.get("pivot")
    try:
        return round(float(piv) * 1.05, 4) if piv else None
    except (TypeError, ValueError):
        return None


def _ignition_signal(bars: list, break_level: float, vol_mult: float = 3.0,
                     min_bars: int = 6):
    """كشف نقي «لحظة الانطلاق» من شموع الدقيقة (رد فعل لا تنبّؤ، بلا شبكة، قابل
    للاختبار): (1) قفزة حجم الدقيقة الأخيرة ≥ `vol_mult`× متوسط الدقائق السابقة ·
    (2) آخر سعر كسر `break_level` صاعدًا · (3) الاتجاه صاعد داخل النافذة (آخر > أول).
    يرجّع {price, vol_x, usd} أو None (لا اشتعال / بيانات غير كافية). `usd` = سيولة
    شمعة الاشتعال بالدولار (السعر×الحجم) — لوسم «مضارب/قروب» (FAISAL_OPERATOR_PACK §P1)."""
    try:
        if (not bars or len(bars) < min_bars
                or not break_level or break_level <= 0):
            return None
        vols = [float(b["v"]) for b in bars if b.get("v") is not None]
        if len(vols) < min_bars:
            return None
        lc = float(bars[-1]["c"])
        lvol = float(bars[-1]["v"])
        prior = vols[:-1]
        avg = sum(prior) / len(prior) if prior else 0.0
        vol_x = (lvol / avg) if avg > 0 else 0.0
        rising = lc > float(bars[0]["c"])
        if vol_x >= vol_mult and lc > float(break_level) and rising:
            return {"price": round(lc, 4), "vol_x": round(vol_x, 1),
                    "usd": round(lc * lvol)}
        return None
    except Exception:
        return None


def _ignition_candle_class(usd):
    """💰 تصنيف شمعة الاشتعال بسيولتها الدولارية (FAISAL_OPERATOR_PACK §P1 — قاعدة
    فيصل: شمعة المضارب ≥100 ألف/قوية ≥300 ألف · القروب ≤50 ألف ويهبط). نقيّة، تُرجّع
    (مفتاح، وصف عربي) — والوصف يذكر رقم فيصل. `None`/غير رقم → ("", "")."""
    try:
        if usd is None:
            return ("", "")
        usd = float(usd)
    except (TypeError, ValueError):
        return ("", "")
    if usd >= CONFIG["IGNITION_USD_STRONG"]:
        return ("strong", "شمعة مضارب قوية (فيصل: 300 ألف فأكثر)")
    if usd >= CONFIG["IGNITION_USD_OPERATOR"]:
        return ("operator", "شمعة مضارب (فيصل: 100 ألف فأصعد)")
    if usd <= CONFIG["IGNITION_USD_GROUP"]:
        return ("group", "حجم قروب — حذارِ تصريفًا سريعًا (فيصل: حدّها 50 ألف ويهبط)")
    return ("mid", "بين حدّي المضارب والقروب")


def scan_ignition(wl: dict, today_iso: str, fetch_bars=None, fetch_flow=None,
                  vol_mult: float = None, fetch_operator=None, trace=None) -> list:
    """🔥 يفحص القائمة المؤهّلة ويكشف **لحظة اشتعال** كل زنبرك (قفزة حجم + كسر الرقم
    الحرج صاعدًا) ثم يرفق تدفق الأوامر الحي للتأكيد. `fetch_bars`/`fetch_flow`/
    `fetch_operator` قابلة للحقن (اختبار بلا شبكة). **دِدوب مرة/سهم/يوم**
    (`s['ignition_alert']`). **فاشل-آمن** → يتخطّى أي سهم يفشل جلبه. **رد فعل لا تنبّؤ ·
    خارج الفرز/الاختيار** (القائمة مختارة مسبقًا). يرجّع [(s, metrics, flow)].
    🕵️ **بوّابة المضارب (طلب المستخدم 2026-07-09): لا إشعار إلا لو دخل المضارب** — لو
    قِيس التدفق ولا طبعات مضارب (≥OPERATOR_MIN_SHARES) = ضجيج يُكتَم؛ لو تعذّر القياس
    (None) = احتياط لتصنيف شمعة الدولار (يُكتَم القروب فقط) فلا نفوّت بعطل شبكي.
    🔬 **E2-A:** `trace` (اختياري، افتراضي None) دالّة قياس ظلّي تتلقّى أحداث funnel وصفية
    عبر `_emit_trace` — **لا تغيّر أي قرار/عتبة/تنبيه**؛ None = سلوك الرادار حرفيًّا بت-بت."""
    fb = fetch_bars or (lambda sym: polygon_minute_bars(sym, minutes=30))
    ff = fetch_flow or order_snapshot
    fo = fetch_operator or operator_flow
    vm = vol_mult if vol_mult is not None else CONFIG["IGNITION_VOL_MULT"]
    out = []
    for s in wl.get("stocks", []):
        if s.get("status") != "active" or s.get("ignition_alert") == today_iso:
            continue
        _sym = s.get("symbol")
        # 🔬 E2-A: كل _emit_trace no-op تام عند trace=None (الافتراضي) → التحكّم أدناه حرفيّ.
        _emit_trace(trace, "01_SEEN_ACTIVE", lambda: {"symbol": _sym})
        lvl = _ignition_break_level(s)
        if not lvl:
            continue
        _emit_trace(trace, "02_LEVEL_AVAILABLE", lambda: {
            "symbol": _sym, "break_level": lvl,
            "break_level_source": _ignition_break_source(s)})
        try:
            bars = fb(s["symbol"])
        except Exception:
            bars = None
        _emit_trace(trace, "03_BARS_FETCH", lambda: {
            "symbol": _sym, "bars_ok": bool(bars), "n_bars": (len(bars) if bars else 0),
            "first_bar_t": (bars[0].get("t") if bars else None),
            "last_bar_t": (bars[-1].get("t") if bars else None)})
        sig = _ignition_signal(bars, lvl, vol_mult=vm) if bars else None
        if not sig:
            continue
        _emit_trace(trace, "04_RAW_IGNITION", lambda: {
            "symbol": _sym, "signal_price": sig.get("price"), "vol_x": sig.get("vol_x"),
            "signal_usd": sig.get("usd"), "candle_class": _ignition_candle_class(sig.get("usd"))[0],
            "break_level": lvl, "break_level_source": _ignition_break_source(s),
            "pivot": s.get("pivot"),
            "stop": (s.get("stop")[0] if isinstance(s.get("stop"), (list, tuple)) and s.get("stop") else s.get("stop")),
            "t1": s.get("t1"), "t2": s.get("t2"), "t3": s.get("t3"),
            "trigger_bar_end": (bars[-1].get("t") if bars else None)})
        # 🕵️ بوّابة المضارب: يُكتَم الاشتعال بلا مضارب (لا نضع ignition_alert = يُعاد
        # الفحص لو دخل المضارب لاحقًا نفس اليوم). فاشل-آمن: تعذّر القياس → شمعة الدولار.
        try:
            of = fo(s["symbol"])
        except Exception:
            of = None
        _emit_trace(trace, "05_OPERATOR_MEASURED" if of is not None else "08_OPERATOR_UNAVAILABLE",
                    lambda: {"symbol": _sym,
                             "operator_status": ("measured" if of is not None else "unavailable"),
                             "has_operator": (of.get("has_operator") if of else None),
                             "buy_block_shares": (of.get("buy_block_shares") if of else None),
                             "bid_block_shares": (of.get("bid_block_shares") if of else None),
                             "nbbo_bid": (of.get("bid") if of else None),
                             "nbbo_ask": (of.get("ask") if of else None),
                             "quote_ts": (of.get("quote_ts") if of else None)})
        if of is not None:
            if not of.get("has_operator"):
                _emit_trace(trace, "07_OPERATOR_FAIL", lambda: {"symbol": _sym})
                continue
            _emit_trace(trace, "06_OPERATOR_PASS", lambda: {"symbol": _sym})
        elif _ignition_candle_class(sig.get("usd"))[0] == "group":
            _emit_trace(trace, "10_FALLBACK_FAIL", lambda: {"symbol": _sym, "candle_class": "group"})
            continue
        else:
            _emit_trace(trace, "09_FALLBACK_PASS", lambda: {
                "symbol": _sym, "candle_class": _ignition_candle_class(sig.get("usd"))[0]})
        sig["operator"] = of
        flow = None
        try:
            flow = ff(s["symbol"])
        except Exception:
            flow = None
        s["ignition_alert"] = today_iso          # دِدوب مرة/سهم/يوم (بالذاكرة)
        s["last_price"] = sig["price"]
        _emit_trace(trace, "11_ALERT_EMITTED", lambda: {"symbol": _sym, "signal_price": sig.get("price")})
        out.append((s, sig, flow))
    return out


def build_ignition_alert(rows: list) -> str:
    """رسالة رادار الانطلاق: «🔥 انطلاق الآن» لكل زنبرك اشتعل + الحجم/الكسر + تدفق
    الأوامر + هدف/وقف للتنفيذ الفوري."""
    if not rows:
        return ""
    lines = ["🔥 <b>انطلاق لحظي — القائمة المؤهّلة</b>",
             "زنبرك اشتعل الآن (حجم + كسر صاعد) — لحظة الدخول:"]
    for s, sig, flow in rows:
        lvl = _ignition_break_level(s)
        lvl_txt = f" · كسر ${lvl:.2f} صاعدًا" if lvl else ""
        lines.append(f"🔥 <b>${esc(s['symbol'])}</b> ${sig['price']:.2f}{lvl_txt} "
                     f"· حجم الدقيقة {sig['vol_x']:.0f}× المتوسط")
        # 💰 وسم شمعة مضارب/قروب بسيولتها الدولارية (قاعدة فيصل — عرض فقط، لا فلترة)
        _usd = sig.get("usd")
        _cls, _desc = _ignition_candle_class(_usd)
        if _desc:
            _icon = "⚠️" if _cls == "group" else "💰"
            lines.append(f"   {_icon} سيولة الشمعة ${_usd:,.0f} — {_desc}")
        # 🕵️ كميات المضارب (طلب المستخدم: شراء عدواني/على الطلب) — تظهر لو قِيست.
        # مختصرة بلغة الأوامر مع وسم المستوى (طلب المستخدم 2026-07-09)؛ سطر التدفق
        # المفصّل (نِسَب/لقطة) أُسقط من التنبيه — التفصيل بفحص اليد.
        if sig.get("operator"):
            lines.append("   " + operator_line(sig["operator"], s))
        _st = s.get("stop")
        stop0 = (_st[0] if isinstance(_st, (list, tuple)) and _st else _st)
        if s.get("t1") and stop0:
            lines.append(f"   🎯 هدف1 ${float(s['t1']):.2f} · ⛔ وقف ${float(stop0):.2f}")
    lines.append("ℹ️ رد فعل لحظي على حركة بدأت فعلًا (لا تنبّؤ) — أكّد بعينك قبل الدخول.")
    return _rtl_join(lines)


# ==========================================================
# 📏 حلقة قياس رادار الانطلاق (سجلّ حي → أداة التطوير) — قياس فرضية التوقيت اللحظي (ذات
# الأولوية — **غير مثبتة حتى الآن**؛ E2). (الالتقاط ونسبة الإنذار الكاذب لا تُقاسان إلا حيًّا).
# **قياس/عرض فقط — خارج الفرز/
# الاختيار.** الرادار يسجّل إطلاقاته؛ أداة التطوير تجلب النتيجة اليومية اللاحقة وتحكم.
# ==========================================================
def load_ignition_log() -> list:
    """يقرأ سجلّ إطلاقات رادار الانطلاق (قائمة سجلّات) — فاشل-آمن → []."""
    try:
        if os.path.exists(IGNITION_LOG_FILE):
            with open(IGNITION_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except Exception as e:
        log(f"⚠️ قراءة سجلّ الانطلاق: {e}")
    return []


def record_ignition_fires(rows, today_iso) -> int:
    """يسجّل إطلاقات الرادار في سجلّ دائم لقياس الحافة (الالتقاط/الإنذار الكاذب لاحقًا
    بأداة التطوير). كل سجلّ: رمز·تاريخ·مستوى الكسر·سعر الاشتعال·مضاعف الحجم·سيولة الشمعة
    وتصنيفها. **قياس فقط — خارج الفرز/الاختيار.** دِدوب مرة/سهم/يوم. فاشل-آمن → 0.
    يُستدعى من عامل الجلسة (ignition_live) عند نهاية الجلسة، لا من scan_ignition النقيّة."""
    try:
        if not rows:
            return 0
        log_data = load_ignition_log()
        seen = {(r.get("symbol"), r.get("date")) for r in log_data}
        added = 0
        for s, sig, _flow in rows:
            sym = s.get("symbol")
            if not sym or (sym, today_iso) in seen:
                continue
            usd = sig.get("usd")
            log_data.append({"symbol": sym, "date": today_iso,
                             # ⑩ (إصلاح تدقيق 2026-07-12): طابع وقت الإطلاق —
                             # بدونه مقياس «الأبكرية» (كم دقيقة سبقنا المسار
                             # اليومي) مستحيل بنيويًا. إلحاق فقط، توافق خلفي
                             # (السجلات القديمة بلا الحقل تُقرأ بـ.get عادي).
                             "fired_at": dt.datetime.utcnow().isoformat(
                                 timespec="seconds") + "Z",
                             "break_level": _ignition_break_level(s),
                             "price": sig.get("price"), "vol_x": sig.get("vol_x"),
                             "usd": usd, "candle_class": _ignition_candle_class(usd)[0]})
            seen.add((sym, today_iso))
            added += 1
        if added:
            _atomic_write_json(IGNITION_LOG_FILE, log_data[-CONFIG["IGNITION_LOG_CAP"]:])
        return added
    except Exception as e:
        log(f"⚠️ تسجيل إطلاقات الانطلاق: {e}")
        return 0


def record_ignition_universe(symbols, today_iso) -> bool:
    """⑩ (إصلاح تدقيق 2026-07-12): يسجّل **مقام الالتقاط** — أسهم القائمة التي
    راقبها الرادار في الجلسة (سواء أُطلق عليها أم لا). بدون المقام، مقياس
    «الالتقاط» (% المنفجرات التي أطلقنا عليها) مستحيل بنيويًا: السجل كان يحفظ
    الإطلاقات فقط. أداة التطوير تقاطعه لاحقًا مع الشموع اليومية (المنفجر بلا
    إطلاق = تفويت). دِدوب مرة/يوم · سقف 90 جلسة · فاشل-آمن → False.
    **قياس فقط — خارج الفرز/الاختيار.**"""
    try:
        syms = sorted({str(x) for x in (symbols or []) if x})
        if not syms:
            return False
        data = []
        if os.path.exists(IGNITION_UNI_FILE):
            try:
                with open(IGNITION_UNI_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f) or []
            except Exception:
                data = []
        if any(e.get("date") == today_iso for e in data):
            return False                       # جلسة اليوم مسجَّلة أصلًا
        data.append({"date": today_iso, "symbols": syms})
        _atomic_write_json(IGNITION_UNI_FILE, data[-90:])
        return True
    except Exception as e:
        log(f"⚠️ تسجيل مقام الانطلاق: {e}")
        return False


def _ignition_outcome(fire, df, confirm_pct=None) -> str:
    """نتيجة إطلاق مسجَّل من الشموع اليومية اللاحقة (نقيّة، قابلة للاختبار):
      • «real» حقيقي: بلغ أعلى لاحق صعودًا ≥confirm_pct% من سعر الاشتعال (الزنبرك اشتعل).
      • «fakeout» كاذب: أغلق يوم لاحق **تحت مستوى الكسر** قبل بلوغ التأكيد (اشتعال فاشل).
      • «pending» معلّق: لا شموع لاحقة كافية / لم يُحسم بعد.
    يمشي يومًا بيوم بعد يوم الاشتعال حصريًا؛ الأسبق يحكم. داخل اليوم الواحد يُفحَص بلوغ
    التأكيد (الأعلى) قبل الكسر الهابط (الإغلاق) — فرصة صعود ≥12% تُحتسب حقيقية (غاية
    الرادار توقيت الدخول). فاشل-آمن → «pending». **قياس فقط — خارج الفرز.**"""
    try:
        conf = confirm_pct if confirm_pct is not None else CONFIG["IGNITION_CONFIRM_PCT"]
        price = float(fire.get("price") or 0)
        lvl = float(fire.get("break_level") or 0)
        fdate = str(fire.get("date") or "")
        if price <= 0 or df is None or len(df) == 0:
            return "pending"
        highs = df["High"].astype(float).values
        closes = df["Close"].astype(float).values
        dates = [str(t.date()) if hasattr(t, "date") else str(t)[:10]
                 for t in df.index]
        target = price * (1.0 + conf / 100.0)
        for i, d in enumerate(dates):
            if d <= fdate:                       # بعد يوم الاشتعال حصريًا (لا تسريب)
                continue
            if highs[i] >= target:
                return "real"
            if lvl > 0 and closes[i] < lvl:
                return "fakeout"
        return "pending"
    except Exception:
        return "pending"


def _ignition_outcome_fetch(sym, fire_date):
    """يجلب الشموع اليومية بعد يوم الاشتعال (لحساب النتيجة) — فاشل-آمن → None."""
    if yf is None:
        return None
    try:
        start = (dt.date.fromisoformat(str(fire_date)[:10])
                 + dt.timedelta(days=1)).isoformat()
        df = yf.download(sym, start=start, interval="1d",
                         auto_adjust=True, progress=False)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df.dropna(subset=["Close"])
    except Exception:
        return None


def _ignition_log_block(log, fetch=None, today=None) -> list:
    """🔥 قياس رادار الانطلاق من السجلّ الحي (أداة التطوير — فرضية التوقيت اللحظي ذات
    الأولوية، **غير مثبتة حتى الآن**؛ E2 §0-ك): الالتقاط ونسبة الإنذار الكاذب + تفصيل حسب تصنيف الشمعة (مضارب/قروب — يجيب
    «هل القروب يكذب أكثر؟» = دليل معايرة عتبات المضارب). يجلب الشموع اليومية اللاحقة لكل
    إطلاق (`fetch` قابل للحقن للاختبار، فاشل-آمن). عيّنة محسومة أقل من العتبة → يُقال
    «تتراكم» بصدق. **عرض/قياس فقط — لا قرار قبل عيّنة كافية + موافقة المستخدم.**"""
    if not log:
        return []
    fx = fetch or _ignition_outcome_fetch
    measured = log[-120:]                # سقف جلب واقعي (أحدث 120) — لا تكلفة شبكة مفتوحة
    real = fake = pend = 0
    by_class = {}                        # class → [real, fake]
    for fire in measured:
        try:
            df = fx(fire.get("symbol"), fire.get("date"))
        except Exception:
            df = None
        oc = _ignition_outcome(fire, df)
        if oc == "pending":
            pend += 1
            continue
        if oc == "real":
            real += 1
        else:
            fake += 1
        b = by_class.setdefault(fire.get("candle_class") or "—", [0, 0])
        b[0 if oc == "real" else 1] += 1
    decided = real + fake
    _cap = f" · قِيس أحدث {len(measured)}" if len(log) > len(measured) else ""
    out = [f"\n🔥 <b>رادار الانطلاق — قياس حي ({len(log)} إطلاق مسجَّل{_cap})</b>"]
    if decided < CONFIG["IGNITION_OUTCOME_MIN"]:
        out.append(f"   ⏳ محسوم {decided} فقط (أقل من {CONFIG['IGNITION_OUTCOME_MIN']}) "
                   f"· معلّق {pend} — النسبة تتراكم أسبوعيًّا بصدق.")
        return out
    out.append(f"   ✅ حقيقي {real} · 🚫 كاذب {fake} · ⏳ معلّق {pend} → "
               f"إنذار كاذب <b>{fake / decided * 100:.0f}%</b> (من {decided} محسوم)")
    labels = {"strong": "قوية", "operator": "مضارب", "mid": "وسط",
              "group": "قروب", "—": "بلا تصنيف"}
    parts = [f"{labels.get(c, c)}: {f_}/{r_ + f_} كاذب"
             for c, (r_, f_) in by_class.items() if (r_ + f_)]
    if parts:
        out.append("   حسب تصنيف الشمعة: " + " · ".join(parts))
    out.append("   <i>قياس تقريبي (نتيجة الشمعة اليومية) — كلّما تراكم السجلّ زادت الثقة.</i>")
    return out


# دالّتان نقيّتان للتحقّق التاريخي من الرادار (IGNITION_VERIFY_PLAN.md) — قابلتان
# للاختبار، لا تُستعملان في المسار الحي (تحقّق/قياس فقط).
def _find_explosion_day(fwd_highs: list, entry: float, expl_pct: float):
    """يوم الانفجار: أول فهرس في القمم الأمامية اليومية يبلغ فيه الصعود من الدخول
    `expl_pct`%. None لو لم يبلغه (أو مدخلات غير صالحة). نقيّة."""
    try:
        if not fwd_highs or not entry or entry <= 0:
            return None
        for i, h in enumerate(fwd_highs):
            if (float(h) / entry - 1.0) * 100.0 >= expl_pct:
                return i
        return None
    except Exception:
        return None


def _ignition_first_fire(day_bars: list, break_level: float, open_px: float,
                         vol_mult: float = 3.0, win: int = 10):
    """يمشي شموع دقيقة يوم الانفجار ويعيد **أول لحظة** يشتعل فيها الرادار
    (`_ignition_signal` على نافذة زاحفة) + **مكسب اليوم من الافتتاح عند الاشتعال**
    (يقيس: هل يشتعل مبكرًا فيبقى معظم الحركة أمامنا؟). None لو لم يشتعل. نقيّة."""
    try:
        if not day_bars or not open_px or open_px <= 0:
            return None
        for i in range(6, len(day_bars) + 1):
            sig = _ignition_signal(day_bars[max(0, i - win):i], break_level,
                                   vol_mult=vol_mult)
            if sig:
                return {"minute": i - 1, "price": sig["price"],
                        "vol_x": sig["vol_x"],
                        "gain_pct": round((sig["price"] / open_px - 1.0) * 100.0, 1)}
        return None
    except Exception:
        return None


def build_pullback_section(entries: list, triggered: list = None) -> str:
    """قسم «مراقبة الارتداد»: أسهم ارتكاز ارتفعت ننتظر رجوعها للدعم +
    تنبيهات الأسهم التي وصلت سعر الدعم اليوم (جاهزة للدخول)."""
    triggered = triggered or []
    if not entries and not triggered:
        return ""
    lines = []
    if triggered:
        lines.append("🎯 <b>وصلت منطقة الدخول — جاهزة!</b>")
        for e in triggered:
            lines.append(f"• <b>{e['symbol']}</b> نزل ${e['last_price']:.2f} "
                         f"≈ دخول ${e['entry'][1]:.2f} · وقف ${e['stop']:.2f} "
                         f"· هدف١ ${e['t1']:.2f}")
        lines.append("")
    if entries:
        lines.append("👁️ <b>مراقبة للارتداد</b> "
                     "(ارتكاز ارتفع — ننتظر رجوعه لمنطقة الدخول):")
        for e in entries:
            tgt = e["entry"][1]
            dist = (e["last_price"] / tgt - 1.0) * 100.0 if tgt else 0.0
            sec = f" · {esc(ar_sector(e['sector']))}" if e.get("sector") else ""
            lines.append(f"• <b>{e['symbol']}</b> ${e['last_price']:.2f} "
                         f"→ منطقة الدخول ${tgt:.2f} (يبعد {dist:+.0f}%){sec}")
        lines.append("<i>يُنبَّه تلقائيًا أول ما ينزل لسعر الدعم.</i>")
    return _rtl_join(lines)


def monitor_pullback(wl: dict) -> list:
    """متابعة يومية لقائمة الارتداد: يحدّث السعر، ويُطلق تنبيهًا عند نزول
    السهم لسعر الدعم (ضمن PULLBACK_TRIGGER_PCT). يعيد قائمة المُنبَّه عنها."""
    entries = wl.get("pullback") or []
    if not entries or yf is None:
        return []
    triggered = []
    buf = 1.0 + CONFIG.get("PULLBACK_TRIGGER_PCT", 2.0) / 100.0
    for e in entries:
        if e.get("status") == "triggered":
            continue
        try:
            d = download_history([e["symbol"]])
            df = d.get(e["symbol"])
            if df is None or df.empty:
                continue
            lp = float(df["Close"].iloc[-1])
            e["last_price"] = round(lp, 4)
            if lp <= e["entry"][1] * buf:        # نزل لسعر الدعم
                e["status"] = "triggered"
                e["triggered_date"] = dt.date.today().isoformat()
                triggered.append(e)
        except Exception:
            continue
    return triggered


def build_daily_message(wl: dict, splits: list,
                        stopped_today: list, replaced: list,
                        promoted: list = None, ready_only: bool = False) -> str:
    """التقرير اليومي (الاثنين→الخميس): القائمة الثابتة مرتبة بالجاهزية.
    `ready_only` (طلب المستخدم 2026-07-09): يدفع **الجاهزين للدخول فقط** بفواصل شرطات ·
    المتابعة تُحصى بالترويسة لكن لا تُعرض كروتها (البوت يتكفّل بها داخليًّا)."""
    today = dt.date.today().isoformat()
    n = len(wl["stocks"])
    # 🟢👀 فصل «جاهز للدخول الآن» عن «متابعة» (خطة ENTRY_READY_SPLIT_PLAN — عرض فقط،
    # من موقع السعر عبر entry_status؛ الترتيب المخزّن لا يُلمس، فقط partition للعرض).
    _st = [(s, entry_status(s)) for s in wl["stocks"]]
    _ready = [(s, es) for s, es in _st if es["status"] == "ready_now"]
    _watch = [(s, es) for s, es in _st if es["status"] != "ready_now"]
    if ready_only:
        lines = [f"📋 <b>قائمة الأسبوع</b> — {today}",
                 f"🟢 {len(_ready)} جاهز للدخول · 👀 {len(_watch)} تحت متابعة البوت "
                 "(تجديد: الجمعة بعد إغلاق السوق)", ""]
    else:
        lines = [f"📋 <b>قائمة الأسبوع</b> — {today}",
                 f"{n} سهم: {len(_ready)} جاهز للدخول · {len(_watch)} متابعة "
                 f"(تجديد القائمة: الجمعة بعد إغلاق السوق)", ""]
    # 🚀 ترقيات اليوم (B→A): إنذار مبكر — اكتمل النموذج، جاهز للدخول
    if promoted:
        lines.append("🚀 <b>ترقيات اليوم (اكتمل النموذج — جاهز للدخول):</b>")
        for s in promoted:
            lib = (f" · تحرر فوق ${s['liberation']:.2f}"
                   if s.get("liberation") else "")
            lines.append(f"• <b>{s['symbol']}</b> صعد من مراقبة B → A "
                         f"| ${s['last_price']:.2f} | قاع ${s['pivot']:.2f} "
                         f"| ستوب ${s['stop']:.2f}{lib}")
        lines.append("")
    if not wl["stocks"]:
        lines.append("القائمة فارغة مؤقتاً — البدائل تُجلب في التشغيل القادم.")
    # الجاهز أولًا ثم المتابعة (ترقيم مستمر 1..N · عنوان القسم يُطبع مرة عند تغيّره ·
    # القسم الفاضي لا يظهر عنوانه — من _ready/_watch أعلاه).
    # 🟢 وضع الجاهز-فقط: كروت الجاهزين فقط، مفصولة بشرطات (طلب المستخدم). المتابعة لا
    # تُعرض (البوت يتابعها + يُنبّه لحظيًّا عند جاهزيتها). غير الوضع = السلوك القديم (قسمان).
    if ready_only:
        _partition = [(s, es, "ready_now") for s, es in _ready]
        if not _ready:
            lines.append(f"🟢 لا سهم جاهز للدخول الآن — {len(_watch)} تحت متابعة البوت "
                         "(يُنبّهك أول ما يجهز).")
    else:
        _partition = ([(s, es, "ready_now") for s, es in _ready]
                      + [(s, es, "watch") for s, es in _watch])
    _cur_section = None
    for i, (s, _es, _sec) in enumerate(_partition, 1):
        if ready_only:
            if i == 1:
                lines.append(f"🟢 <b>جاهز للدخول الآن</b> ({len(_ready)})")
            else:                          # فاصل شرطات بين كل سهم وسهم (طلب المستخدم)
                lines += ["", DAILY_CARD_SEP, ""]
        elif _sec != _cur_section:
            if _cur_section is not None:   # فراغ بين القسمين فقط (الترويسة توفّره للأول)
                lines.append("")
            _cur_section = _sec
            if _sec == "ready_now":
                lines.append(f"🟢 <b>جاهز للدخول الآن</b> ({len(_ready)})")
            else:
                lines.append("👀 <b>متابعة — ننتظر وصولها لمنطقة الدخول</b> "
                             f"({len(_watch)})")
        lp = s["last_price"]
        tier = s.get("tier", "B")
        tb = "🎯"          # 🪦 A/B متقاعد → شارة موحّدة؛ الجاهزية بالوسم التالي
        promo = " 🚀" if s.get("promoted_date") == today else ""
        # الرأس: الرمز + حالة الجاهزية + النسبة + القوة العامة (سطر واحد)
        rdy = s.get("readiness")
        head = f"{i}) {tb}{promo} <b>${s['symbol']}</b> · "
        if rdy is not None:
            head += (f"{readiness_tag(rdy)} {rdy}/100 · "
                     f"قوة {s.get('score', '?')}")
        else:
            head += f"قوة {s.get('score', '?')}"
        lines.append(head)
        # سطر السبب لأسهم المتابعة فقط (ما الذي يحوّلها جاهزة) — الجاهز يكفيه عنوان القسم
        if _sec == "watch" and _es.get("reason"):
            lines.append(f"   👀 {_es['reason']}")
        # المعلومات الصغيرة بسطر واحد (سعر · فلوت · شورت · قطاع)
        small = [f"${lp:.2f}"]
        # فلوت/شورت: شرطة «—» عند تعذّر الجلب (تعذّر ≠ صفر) بدل الإخفاء الصامت.
        small.append(f"فلوت {fmt_money(s['float'])}" if s.get("float") else "فلوت —")
        # «شورت» = المتاح من ChartExchange (قراءة فيصل) ← الحجم اليومي ← نسبة ← «—».
        small.append(_short_headline(s))
        if s.get("sector"):
            small.append(esc(ar_sector(s["sector"])))
        if s.get("country"):
            small.append(country_label(s["country"]))
        lines.append("   💰 " + " · ".join(small))
        # 🔒 معدّل الاقتراض (فيصل: أساس الارتكاز · اقتراض صعب = سكويز) — عند توفّره فقط
        if s.get("borrow_fee") is not None or s.get("shares_available") is not None:
            lines.append("   " + borrow_line(s))
        # 📅 الأحداث المعلنة القادمة (أرباح/تجارب — يوم الانفجار المحتمل، فيصل 9428)
        for _evl in events_lines(s.get("upcoming_events")):
            lines.append("   " + _evl)
        for _il in interp_card_lines(s.get("interp")):   # 🧭 التفسير/القرار (عرض فقط)
            lines.append("   " + _il)
        # 🧬 طريقة ارتفاع اليد (سلوك المضارب — عرض فقط، لا يمسّ الفرز/الاختيار)
        _bh = s.get("behav") or {}
        if _bh.get("score") is not None:
            _bd = []
            if _bh.get("n_pumps"):
                _bd.append(f"رفع {_bh['n_pumps']} مرّة")
            if _bh.get("sweeps"):
                _bd.append(f"مسح {_bh['sweeps']}")
            _bd += behavior_tags(_bh)     # §13: وسوم وصفية (صيد وقفات/خمول طويل)
            _bt = (" (" + " · ".join(_bd) + ")") if _bd else ""
            lines.append(f"   🧬 طريقة الارتفاع: {_bh['score']}/100 · {_bh['label']}{_bt}")
        # (🔬 التجميع الصامت أُزيل — تجربة T-ACC فشلت بالسنتين، غير مميِّز للمنفجر)
        # 🕵️ علامات اليد لم تعد سطرًا داخل كل كرت (طلب المستخدم: تُجمع في قسم
        # «أسهم فيها علامات يد» المستقل أسفل التقرير — قائمة نظيفة لحالها).
        # D10: تدوير الفلوت (سكويز) — يظهر عند تجاوز 100% فقط
        rot = s.get("rotation_pct")
        if rot and rot >= 100:
            lines.append(f"   🔄 تدوير ≈ {rot:.0f}% من الفلوت")
        # الدخول (دفعات) + الوقف بنسبته. السجلّات القديمة بلا tranches → تُبنى من الدعم
        trs = s.get("tranches") or [
            round(s["pivot"] * (1 + CONFIG["ENTRY_STEP_PCT"] / 100.0 * j), 2)
            for j in range(int(CONFIG["ENTRY_TRANCHES"]))]
        stop = s["stop"]
        lines.append("   📥 دخول: " + " · ".join(f"${p:.2f}" for p in trs)
                     + f"  ·  ⛔ وقف خسارة ${stop:.2f}")
        # الأهداف الثلاثة (أسعار فقط — بلا نسبة، تفاديًا لتشوّش ٪ في العربي RTL)
        # + وسم «معلّق» للهدف خلف حاجز غير مكسور (طبقة التفسير §9 — عرض فقط)
        _das = (s.get("interp") or {}).get("activation_state") or {}
        _dblk = _das.get("blocked_by")
        _dpend = {round(float(t), 2)
                  for t in (_das.get("inactive_targets") or [])}
        _tparts = []
        for _tv in (s["t1"], s["t2"], s["t3"]):
            _seg = f"${_tv:.2f}"
            if _dblk and round(_tv, 2) in _dpend:
                _seg += " (معلّق)"
            _tparts.append(_seg)
        lines.append("   🎯 أهداف: " + " · ".join(_tparts))
        if _dblk and _dpend:
            lines.append(f"   ⏳ المعلّق يتفعّل بتجاوز ${_dblk:.2f}")
        if s.get("liberation"):
            lines.append(f"   🚀 تحرر فوق ${s['liberation']:.2f}")
        if any("Williams" in f for f in (s.get("flags") or [])):
            lines.append("   ⚡ دخول المضارب ✓ (إشارة زخم للدخول)")
        # النواقص (B) مرقّمة بسطر واحد (n من 14)
        if tier == "B" and s.get("soft_fails"):
            sf = s["soft_fails"]
            lines.append(f"   🅱️ ناقص ({len(sf)}/14): "
                         + " · ".join(f"{j}- {x}" for j, x in enumerate(sf, 1)))
        _tfi = timeframes_info(s.get("tf_count"), s.get("tf_display"))
        if _tfi:
            lines.append("   " + _tfi)
        # تنبيهات عملية تبقى: لحظة الدخول · تحقيق هدف · تحذيرات حرجة
        if trs and min(trs) <= lp <= max(trs) * 1.005 and lp > stop:
            lines.append("   🎯 <b>في منطقة الدفعات الآن — نفّذ خطتك</b>")
        if s.get("hit"):
            lines.append(f"   🏆 حقق هدف{s['hit'][-1]} يوم {s['hit_date']} "
                         f"| أقصى {s['max_gain_pct']:+.0f}%")
        for w in (s.get("warnings") or []):
            lines.append(f"   ⚠️ {esc(w)}")
    # بدلاء اليوم: قائمة الإضافات — تُخفى بوضع الجاهز-فقط (الجديد يظهر كرته لو جاهز؛
    # وإلا فهو «تحت المتابعة» يتكفّل بها البوت — طلب المستخدم «ما يوصلني إلا الجاهز»).
    if replaced and not ready_only:
        lines += ["", "🔄 <b>بدلاء اليوم (انضموا للقائمة):</b>"]
        for r in replaced:
            lines.append(f"• <b>{r['symbol']}</b> | ${r['price']:.2f} | "
                         f"نقاط {r['score']} | قاع ${r['pivot']:.2f} | "
                         f"ستوب ${r['stop'][0]:.2f} | هدف1 ${r['t1']:.2f}")
        lines.append("(بطاقاتهم الكاملة مع SEC والشورت في تقرير تجديد الجمعة بعد الإغلاق)")
    if stopped_today:
        lines += ["", "🛑 <b>شُطب اليوم (يُستبدل غداً):</b>"]
        for s in stopped_today:
            lines.append(f"• {s['symbol']}: {s['removal_reason']}")
    lines += ["", FOOTER]
    return _rtl_join(lines)


def build_wrapup_message(wl: dict) -> str:
    """حصاد الأسبوع (الجمعة بعد الإغلاق قبل التجديد): الأداء + أسباب الشطب"""
    entries = wl["stocks"] + wl["removed"]
    if not entries:
        return ""
    today = dt.date.today().isoformat()
    start = wl.get("week_start") or "؟"
    # حماية: لو القائمة تأسست اليوم نفسه (عمرها 0 يوم) لا يوجد أسبوع لحصاده —
    # نتجنّب رسالة "حصاد" فارغة بـ +0% للكل (تظهر عند تكرار التشغيل بنفس اليوم).
    if start == today or wl.get("created") == today:
        return ""
    lines = [f"📊 <b>حصاد أسبوع القائمة</b> ({start} ← {today})", ""]
    for s in sorted(entries, key=lambda x: -(x.get("max_gain_pct") or 0)):
        chg = (s["last_price"] / s["entry_ref"] - 1.0) * 100.0
        if s["status"] == "stopped":
            st = "🛑 شُطب"
        elif s.get("hit"):
            st = f"🏆 هدف{s['hit'][-1]}"
        else:
            st = "⏳ ما زال يتشكل"
        lines.append(f"• <b>{s['symbol']}</b>: ${s['entry_ref']:.2f} ← "
                     f"${s['last_price']:.2f} ({chg:+.0f}%) | "
                     f"أقصى {s['max_gain_pct']:+.0f}% | {st}")
    stopped = [s for s in entries if s["status"] == "stopped"]
    if stopped:
        lines += ["", "🛑 <b>المشطوبون وأسبابهم (للتعلم):</b>"]
        for s in stopped:
            lines.append(f"• {s['symbol']}: {s.get('removal_reason') or '—'}")
            if s.get("flags"):
                lines.append(f"  إشاراته عند الاختيار: "
                             f"{'، '.join(s['flags'])}")
        cnt = {}
        for s in stopped:
            for f in s.get("flags", []):
                name = f.split("(")[0].strip()
                cnt[name] = cnt.get(name, 0) + 1
        common = [f"{k} ({v})" for k, v in
                  sorted(cnt.items(), key=lambda x: -x[1]) if v >= 2]
        if common:
            lines += ["", "💡 إشارات تكررت عند المشطوبين: "
                      + "، ".join(common),
                      "(إذا تكرر النمط أسابيع متتالية، نراجع وزنها)"]
    notes = wl.get("notes") or []
    if notes:
        lines += ["", "📝 <b>ملاحظات الأسبوع:</b>"]
        for nt in notes[-12:]:
            lines.append(f"• {nt['date']} {nt['symbol']}: {nt['text']}")
    wins = len([s for s in entries if s.get("hit")])
    act = len([s for s in entries
               if s["status"] == "active" and not s.get("hit")])
    lines += ["", f"الخلاصة: {wins} حقق هدفاً | {len(stopped)} ضرب الستوب | "
              f"{act} ما زال يتشكل",
              "", "⚠️ <i>إحصاءات آلية للتقييم الذاتي — ليست توصية.</i>"]
    return "\n".join(lines)


# ===== 🔬 مساعد التطوير (المساعد الثالث) — يحلّل نتائج البوت نفسه =====
DEV_MIN_SAMPLE = 10        # أقل عدد صفقات محسومة قبل أن تكون الأرقام ذات معنى



def _alert_hit_from_status(status: str):
    """يرجّع t1/t2/t3 من حالة سجل التنبيهات hit_t*، وإلا None."""
    st = str(status or "")
    return st.replace("hit_", "") if st.startswith("hit_t") else None


def _collect_closed_alerts(alert_data) -> list:
    """يجمع الصفقات المحسومة من alerts_history.json (نظام التتبع القديم/الموازي).
    طبقة تقارير فقط: لا تغيّر الفرز ولا الدخول/الوقف/الأهداف؛ تمنع أن يعرض مساعد
    التطوير 0 صفقات بينما تقرير الأداء الأسبوعي سجّل أهدافًا/ستوبات."""
    if not alert_data:
        return []
    alerts = alert_data.get("alerts", alert_data) if isinstance(alert_data, dict) else alert_data
    rows = []
    for a in alerts or []:
        status = str(a.get("status") or "")
        hit = _alert_hit_from_status(status)
        won = bool(hit)
        lost = status == "stopped"
        if not (won or lost):
            continue
        r = dict(a)
        r["entry_ref"] = r.get("entry_ref", r.get("price"))
        r["hit"] = hit
        r["hit_date"] = r.get("hit_date") or r.get("result_date")
        r["added"] = r.get("added") or r.get("date")
        if lost and not r.get("removal_reason"):
            r["removal_reason"] = "ضرب الستوب"
        r["_win"] = won
        rows.append(r)
    return rows


def _dedup_closed(rows: list) -> list:
    """يزيل تكرار الصفقة المحسومة بين المصدرين (القائمة + alerts) بمفتاح
    (رمز, entry_ref) — الأول يفوز. طبقة تقارير فقط، لا تمسّ الفرز. (تأمين فحص
    2026-06-30: دمج _collect_closed + _collect_closed_alerts كان يحتمل عدّ نفس
    الصفقة مرّتين لو ظهرت في القائمة و alerts معًا — غير مؤذٍ الآن، حارس وقائي.)"""
    seen, out = set(), []
    for r in rows:
        k = (r.get("symbol"), r.get("entry_ref"))
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def _collect_closed(wl: dict) -> list:
    """يجمع كل الصفقات المحسومة (رابحة=حقّقت هدفًا · خاسرة=ضربت الستوب بلا هدف)
    من الأرشيف التراكمي + الأسبوع الحالي. كل صف يحمل سماته عند الدخول."""
    rows = []
    seen = set()
    buckets = list(wl.get("history") or [])
    buckets.append({"stocks": (wl.get("removed") or []) + (wl.get("stocks") or [])})
    for wk in buckets:
        for s in wk.get("stocks", []):
            won = bool(s.get("hit"))
            lost = (s.get("status") == "stopped") and not won
            if not (won or lost):
                continue
            key = (s.get("symbol"), s.get("entry_ref"))
            if key in seen:                 # تفادي التكرار بين الأرشيف والحالي
                continue
            seen.add(key)
            r = dict(s)
            r["_win"] = won
            rows.append(r)
    return rows


def _wr(rows: list):
    """(عدد، نسبة النجاح %، متوسط أقصى ربح%) لمجموعة صفقات."""
    n = len(rows)
    if not n:
        return (0, 0.0, 0.0)
    wins = sum(1 for r in rows if r["_win"])
    avg_mg = sum((r.get("max_gain_pct") or 0) for r in rows) / n
    return (n, wins / n * 100.0, avg_mg)


# ── مساعدات تحليل مقتبَسة ومُكيَّفة من أداتَي التطوير (dev_assistant_standalone +
#    dev_backtest_toolkit) على منهجية فيصل. طبقة تقارير/تحليل بحتة — لا تمسّ الفرز
#    ولا الدخول/الوقف/الأهداف/البوابات (لا LOGIC_VERSION). كلها على بياناتنا المتاحة.
def _close_date(r):
    """تاريخ **إغلاق** الصفقة (لا الدخول): الرابح=hit_date · الخاسر=result_date/
    removed_date. للتبويب الزمني «قبل/بعد» — السؤال عن نتائج تحقّقت لا صفقات فُتحت."""
    return r.get("hit_date") or r.get("result_date") or r.get("removed_date")


def _median(vals):
    """الوسيط (الصفقة النموذجية) — أمتن من المتوسط ضد ذيل صفقة واحدة."""
    s = sorted(float(v) for v in vals)
    n = len(s)
    if not n:
        return 0.0
    m = n // 2
    return s[m] if n % 2 else (s[m - 1] + s[m]) / 2.0


def _wilson_ci(wins, n):
    """فاصل ثقة Wilson 95% (سفلى%، عليا%) لنسبة نجاح ثنائية — أصدق من النسبة الخام
    لعيّنة صغيرة، وعرضُه يميّز الإشارة من الضجيج. دالة صرفة بلا عشوائية (أنسب من
    bootstrap للعنوان الثنائي، وقابل لإعادة الإنتاج)."""
    if n <= 0:
        return (0.0, 0.0)
    z = 1.96
    p = wins / n
    denom = 1.0 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    lo = max(0.0, (centre - margin) / denom)
    hi = min(1.0, (centre + margin) / denom)
    return (lo * 100.0, hi * 100.0)


def _wilson_lower_pct(wins, n):
    """أرضية ثقة Wilson السفلى 95% (%) — للرأس بمساعد التطوير."""
    return _wilson_ci(wins, n)[0]


def _realized_r(r):
    """عائد الصفقة بوحدة المخاطرة (R): الرابح=(هدف مُصاب−دخول)/(دخول−وقف) ·
    الخاسر≈−1. يوحّد الدخول على entry_ref (نفس أساس RR بالكرت). None لو نقص حقل.
    مقياس «هل الحافة موجبة أصلًا؟» — مختلف عن أقصى الربح (ذروة لحظية)."""
    try:
        entry = float(r.get("entry_ref") or r.get("price"))
        stop = float(r.get("stop"))
        risk = entry - stop
        if risk <= 0:
            return None
        if r.get("_win"):
            h = r.get("hit")
            tp = r.get(h) if h in ("t1", "t2", "t3") else None
            return (float(tp) - entry) / risk if tp else None
        return -1.0
    except (TypeError, ValueError):
        return None


def _weekly_compare_block(rows, today=None):
    """📅 «التطوير مقابل الأسبوع الماضي» (مُكيَّف من dev_assistant_standalone.compare):
    يبوّب المحسومة بتاريخ **الإغلاق** إلى نافذتين (آخر 7 أيام · الـ7 السابقة) ويقيس
    فرق نسبة النجاح بالنقاط = «نسبة التطوير» (متين ضد ذيل صفقة واحدة، لا متوسط الربح).
    يجيب سؤال المستخدم المتكرّر تلقائيًا. حارس عيّنة يقود العرض (اتجاه لا حكم)."""
    today = today or dt.date.today()
    cur_lo = (today - dt.timedelta(days=6)).isoformat()
    prev_lo = (today - dt.timedelta(days=13)).isoformat()
    prev_hi = (today - dt.timedelta(days=7)).isoformat()
    cur, prev = [], []
    for r in rows:
        d = _close_date(r)
        if not d:
            continue
        d = str(d)
        if d >= cur_lo:
            cur.append(r)
        elif prev_lo <= d <= prev_hi:
            prev.append(r)
    if not cur and not prev:
        return []

    def _wl(g):
        w = sum(1 for r in g if r["_win"])
        return w, len(g) - w

    cw, cl = _wl(cur)
    pw, pl = _wl(prev)
    out = ["\n📅 <b>التطوير مقابل الأسبوع الماضي</b>"]
    # حارس: أي نافذة أقل من 3 صفقات → عدّ فقط بلا نسب (تقلّب لا إشارة)
    if len(cur) < 3 or len(prev) < 3:
        cs = f"{len(cur)} صفقة ({cw}✅ / {cl}🛑)" if cur else "لا صفقات محسومة"
        ps = f"{len(prev)} صفقة ({pw}✅ / {pl}🛑)" if prev else "لا صفقات محسومة"
        out.append(f"   هذا الأسبوع: {cs} · الأسبوع الماضي: {ps}")
        out.append("   ⚠️ عدد الصفقات أقل من أن تُحسب منه نسبة موثوقة — "
                   "نكتفي بالعدّ حتى تتراكم.")
        return out
    _, cwr, cmg = _wr(cur)
    _, pwr, pmg = _wr(prev)
    out.append(f"   هذا الأسبوع: {len(cur)} صفقات · نجاح {cwr:.0f}% · "
               f"متوسط أقصى ربح {cmg:+.0f}% · لمس الوقف {cl}")
    out.append(f"   الأسبوع الماضي: {len(prev)} صفقات · نجاح {pwr:.0f}% · "
               f"متوسط أقصى ربح {pmg:+.0f}% · لمس الوقف {pl}")
    diff = cwr - pwr
    if diff >= 10:
        d_txt = f"النجاح أعلى (فارق {diff:+.0f} نقطة) 🔼"
    elif diff <= -10:
        d_txt = f"النجاح أقل (فارق {diff:+.0f} نقطة) 🔽"
    else:
        d_txt = f"النجاح ثابت تقريبًا (فارق {diff:+.0f}) ↔️"
    gdiff = cmg - pmg
    out.append(f"   التطوير: {d_txt} · الربح (فارق {gdiff:+.0f})")
    out.append(f"   ⚠️ العيّنة صغيرة ({len(cur) + len(prev)} صفقة على أسبوعين) — "
               "المؤشر اتجاهي لا حاسم.")
    return out


def _honest_metrics_block(rows):
    """📏 مقاييس صادقة (مُكيَّف من dev_backtest_toolkit.honest_summary): الوسيط +
    استبعاد الأعلى/الأدنى + اعتماد الذيل — تكشف إن كانت الحافة يحملها ذيل قِلّة
    (متوسط مرتفع + وسيط منخفض) أم عريضة. كلها على أقصى الربح (نفس مقياس الرأس)."""
    gains = [float(r.get("max_gain_pct") or 0) for r in rows]
    if len(gains) < 3:
        return []
    s = sorted(gains)
    mean = sum(s) / len(s)
    med = _median(s)
    # مشذّب-5% على N~10 يقرّب لصفر → نستبدله باستبعاد أعلى صفقة وأدنى صفقة
    trimmed = sum(s[1:-1]) / len(s[1:-1]) if len(s) > 2 else mean
    out = ["\n📏 <b>مقاييس صادقة (أقصى ربح)</b>",
           f"   المتوسط {mean:+.0f}% · الوسيط {med:+.0f}% · "
           f"بعد استبعاد الأعلى والأدنى {trimmed:+.0f}%"]
    if mean - med >= 5:
        out.append("   ↳ المتوسط أعلى من الوسيط بوضوح — الحافة يحملها قليل من "
                   "الصفقات لا الجسم.")
    # اعتماد الذيل: بركة الرابحين فقط (نسبة الفوز ثنائية بلا ذيل)، مقارنة بخط
    # أساس التساوي k/W (حارس W خمسة فأكثر وإلا صِغَر عيّنة يوهم تركّزًا).
    winners = sorted(((float(r.get("max_gain_pct") or 0), r.get("symbol"))
                      for r in rows if r.get("_win")), reverse=True)
    W = len(winners)
    tot = sum(g for g, _ in winners)
    if W >= 5 and tot > 0:
        share = sum(g for g, _ in winners[:2]) / tot * 100.0
        base = 2.0 / W * 100.0
        out.append("\n🎢 <b>اعتماد الذيل (تركّز الربح بين الرابحين)</b>")
        out.append(f"   أعلى صفقتين تصنعان {share:.0f}% من مجمّع أقصى الأرباح "
                   f"(لو توزّع بالتساوي لكانت {base:.0f}%)")
        if share - base >= 25:
            names = " · ".join(f"{esc(str(sym))} {g:+.0f}%"
                               for g, sym in winners[:2])
            out.append(f"   الحاملتان: {names} — الحافة تعتمد عليهما؛ تأكّد أن "
                       "المنهجية تكرّر أمثالهما لا أنها حظّ صفقتين.")
        else:
            out.append("   الربح موزّع على صفقات كثيرة — حافة عريضة أمتن.")
    return out


def build_dev_assistant_report(wl: dict, alert_data: dict = None) -> str:
    """🔬 المساعد الثالث: يحلّل الصفقات المحسومة ويطلّع تشخيص الأداء بالشرائح
    + أنماط الفشل + اقتراحات ضبط (اقتراح فقط — لا يغيّر إعدادات). يُرسل الجمعة."""
    rows = _dedup_closed(_collect_closed(wl) + _collect_closed_alerts(alert_data))
    n, wr, avg = _wr(rows)
    _ig_log = load_ignition_log()      # 📏 قياس حافة الرادار (مستقل عن الصفقات المحسومة)
    head = ["🔬 <b>مساعد التطوير — تحليل أداء المنهجية</b>",
            f"صفقات محسومة متراكمة: <b>{n}</b>"]
    # 📅 «التطوير مقابل الأسبوع الماضي» — يظهر دائمًا (يجيب سؤال المستخدم المتكرّر
    # مهما صغرت العيّنة). طبقة تقارير فقط.
    head += _weekly_compare_block(rows)

    # §6 (2026-07-11): تسوية مشتبهات التقسيم مرّة واحدة — الكسب الخارق (≥300%)
    # يُصحَّح بعامل التقسيم العكسي المؤكَّد بدل استبعاده الأعمى، فنسترجع عيّنات
    # حقيقية. طبقة تقارير فقط · أسوأ حالة = سلوك اليوم (يبقى suspect). القوائم
    # الجديدة تُستعمل في المُداخل الثلاثة بدل _MISSED / wl["explosions"] الخام.
    _missed_resolved = _resolve_split_suspects(_MISSED)
    _ex_resolved = _resolve_explosion_suspects(wl.get("explosions") or [])

    def _missed_block():
        if not _missed_resolved:
            return []
        # تصنيف: بوابات الهوية/البنية = «ليس ارتكازًا أصلًا» (رفض صحيح، لا تشدّد):
        # M1 سعر · M2 هبوط · M3 انفجار · M4_base (قاعدة واسعة/شاذّة = ليست تجميعًا
        # ضيّقًا — بنيوية مثل M1-M3، وملتقَطة أصلًا بمسار الارتداد إن كانت ارتكازًا
        # حقيقيًا ارتفع). الباقي (M4_انفجر_فعلاً «فات القطار»/حدّي/RSI/نواقص) = ارتكاز
        # فعلي تحرّك → هو الإشارة الحقيقية للمراجعة. (إصلاح فحص 2026-06-26: كان M4_base
        # يُحسب خطأً «ارتكاز فاتنا» فيفبرك فرصًا فائتة وهمية.)
        def _identity(reason):
            r = str(reason)
            return r.startswith(("M1_", "M2_", "M3_")) or r.startswith("M4_base")
        # A2: القفزات الخارقة (يُرجَّح أثر تقسيم غير معدَّل) تُفصل من الإحصاء
        # وتُعرض ببند مستقل للتحقق اليدوي — لا تُحذف (شفافية). §6: المصحَّحة
        # بتقسيم عكسي مؤكَّد دخلت clean بأرقامها الحقيقية (split_corrected).
        suspects = [m for m in _missed_resolved if m.get("suspect_split")]
        clean = [m for m in _missed_resolved if not m.get("suspect_split")]
        corrected = [m for m in clean if m.get("split_corrected")]
        moved = [m for m in clean if not _identity(m["reason"])]
        not_pivot = [m for m in clean if _identity(m["reason"])]
        out = [f"\n👻 <b>فرص فائتة (مرفوض صعد {int(CONFIG['MISSED_RISE_PCT'])}% أو أكثر)</b>",
               f"   📌 ارتكاز تحرّك (راجع الارتداد): <b>{len(moved)}</b> · "
               f"🗑️ ليس ارتكازًا (تجاهل صحيح): {len(not_pivot)}"]
        if corrected:
            top_cor = " · ".join(f"{m['symbol']} +{m['gain_10d']:.0f}%"
                                 for m in sorted(corrected,
                                                 key=lambda x: -x["gain_10d"])[:4])
            out.append(f"   ✅ مصحّح تقسيم ({len(corrected)}) — الكسب الخارق كان "
                       f"تقسيمًا عكسيًا فأُعيد لمقياسه الحقيقي: {top_cor}")
        if suspects:
            top_sus = " · ".join(f"{m['symbol']} +{m['gain_10d']:.0f}%"
                                 for m in suspects[:4])
            out.append(f"   ⚠️ مستبعد من الإحصاء ({len(suspects)}) — يُرجَّح أثر "
                       f"تقسيم عكسي بالبيانات (تحقق يدوي): {top_sus}")
        if moved:
            rc = {}
            for m in moved:
                rc[m["reason"]] = rc.get(m["reason"], 0) + 1
            out.append("   أسباب الارتكاز المتحرّك: "
                       + "، ".join(f"{k} ({v})" for k, v in
                                   sorted(rc.items(), key=lambda x: -x[1])[:3]))
            for m in sorted(moved, key=lambda x: -x["gain_10d"])[:6]:
                out.append(f"   • {m['symbol']}: +{m['gain_10d']:.0f}% — "
                           f"ارتكاز تحرّك ({m['reason']})")
            out.append("   ↳ هذي مرشّحات ارتداد؛ تأكّد قائمة المراقبة تلتقط أقواها.")
        else:
            out.append("   ✅ لا ارتكاز فعلي فاتنا — كل الفائتة ليست أسهم ارتكاز.")
        return out

    def _explosions_block():
        ex = _ex_resolved                      # §6: المشتبهات مُسوّاة تقسيميًّا
        if not ex:
            return []

        def _br(e):    # البوابة الدقيقة عند القاع (توافق خلفي مع السجلات القديمة)
            return e.get("base_reason") or e.get("reason") or "—"

        missed = [e for e in ex if e.get("was_pivot")]
        junk = [e for e in ex if not e.get("was_pivot")]
        corrected = [e for e in ex if e.get("split_corrected")]
        thr = (f"{int(CONFIG['EXPLOSION_PCT'])}% قفزة أو "
               f"{int(CONFIG['EXPLOSION_RUN_PCT'])}% تجمّع")
        out = [f"\n💥 <b>المتحرّكون ({thr}) — {len(ex)} سهم</b>",
               f"   🎯 كان ارتكازًا فاتنا: {len(missed)} · "
               f"🗑️ عشوائي (صح تجاهلناه): {len(junk)}"]
        if corrected:
            out.append(f"   ✅ مصحّح تقسيم ({len(corrected)}) — كسب خارق أُعيد "
                       "لمقياسه الحقيقي بعامل تقسيم عكسي مؤكَّد.")
        # 🚪 توزيع البوابات على **كل** المتحرّكين — طلب المستخدم: لا متحرّك >العتبة
        # بلا بوابة رفض معروفة بالضبط عند قاعه (لا الرفض الحالي بعد الانفجار).
        gc = {}
        for e in ex:
            gc[_br(e)] = gc.get(_br(e), 0) + 1
        out.append("   🚪 بوابة الرفض عند القاع (كل المتحرّكين): "
                   + " · ".join(f"{esc(str(k))}={v}" for k, v in
                                sorted(gc.items(), key=lambda x: -x[1])[:6]))
        if missed:
            for e in sorted(missed, key=lambda x: -x["gain"])[:6]:
                # A2: 🔍 = قفزة خارقة قد تكون تقسيمًا غير معدَّل — تحقق يدويًا
                sus = " 🔍" if e.get("suspect_split") else ""
                knd = e.get("kind", "قفزة")
                out.append(f"   • {e['symbol']}: +{e['gain']:.0f}% ({knd}){sus} — "
                           f"كان ارتكازًا، بوابة القاع: {esc(str(_br(e)))}")
            mc = {}
            for e in missed:                    # بوابات فعلية فقط (لا «مرشّح»/«—»)
                br = _br(e)
                if br not in ("مرشّح", "—"):
                    mc[br] = mc.get(br, 0) + 1
            if mc:
                out.append("   ↳ أكثر بوابة فوّتت ارتكازًا: "
                           + "، ".join(f"{esc(str(k))} ({v})" for k, v in
                                       sorted(mc.items(), key=lambda x: -x[1])[:3])
                           + " — راجعها (قد تكون متشدّدة).")
            if any(e.get("suspect_split") for e in missed):
                out.append("   🔍 = قفزة خارقة، قد تكون أثر تقسيم — تحقق يدويًا.")
        # ⚠️ الأخطر: متحرّك كان **مرشّحًا** عند قاعه (اجتاز الفارز) لكنه لم يدخل
        # القائمة — تأكّد لِمَ (توقيت/تغطية؟)، هذا أقوى إشارة «تفويت حقيقي».
        real = [e for e in ex if _br(e) == "مرشّح"]
        if real:
            out.append(f"   ⚠️ {len(real)} متحرّك كان مرشّحًا عند قاعه — تأكّد لِمَ "
                       "لم يدخل القائمة: "
                       + "، ".join(f"{e['symbol']}(+{e['gain']:.0f}%)" for e in
                                   sorted(real, key=lambda x: -x["gain"])[:5]))
        return out

    def _denominator_block():
        """A1: مقام أسباب الرفض (مجموع آخر 7 أيام) + نسبة الفائتة/المقام —
        يحسم بالأرقام هل بوابة (M4/M2...) متشدّدة فعلًا أم تعمل كما صُممت."""
        snaps = wl.get("reject_stats") or []
        if not snaps:
            return []
        week_ago = (dt.date.today() - dt.timedelta(days=7)).isoformat()
        recent = [s for s in snaps if s.get("date", "") >= week_ago]
        if not recent:
            return []
        totals = {}
        for s in recent:
            for k, v in (s.get("stats") or {}).items():
                totals[k] = totals.get(k, 0) + int(v)
        if not totals:
            return []
        top = sorted(totals.items(), key=lambda x: -x[1])[:6]
        out = [f"\n🧮 <b>مقام الرفض (مجموع {len(recent)} تشغيل، آخر 7 أيام)</b>",
               "   " + " · ".join(f"{esc(k)}={v}" for k, v in top)]
        # نسبة الفائتة الواقعية ÷ المقام لكل بوابة (تُظهر البوابة المتشددة فعلًا)
        # §6: القائمة المُسوّاة تقسيميًّا (المصحَّح دخل، الضجيج سقط).
        clean_missed = [m for m in _missed_resolved if not m.get("suspect_split")]
        ratios = []
        for gate, total in top:
            miss = sum(1 for m in clean_missed if str(m["reason"]) == gate)
            if total and miss:
                ratios.append(f"{esc(gate)}: {miss}/{total} "
                              f"({miss / total * 100:.1f}%)")
        if ratios:
            out.append("   فائتة/مقام: " + " · ".join(ratios[:4]))
        return out

    if n < DEV_MIN_SAMPLE:
        head.append(f"⏳ صفقات محسومة قليلة (أقل من {DEV_MIN_SAMPLE}) — "
                    "تشخيص الأداء يتراكم أسبوعيًا (~10+ صفقة).")
        head += _missed_block()           # الفرص الفائتة تظهر فورًا (مستقلة)
        head += _explosions_block()       # الانفجارات المفقودة (مستقلة)
        head += _denominator_block()      # A1: مقام الرفض (مستقل)
        head += _ignition_log_block(_ig_log)  # 📏 قياس حافة الرادار (مستقل)
        head.append("\n⚠️ <i>أداة تطوير ذاتي — ليست توصية.</i>")
        return "\n".join(head)
    wins = [r for r in rows if r["_win"]]
    losses = [r for r in rows if not r["_win"]]
    head.append(f"النجاح الكلي: <b>{wr:.0f}%</b> ({len(wins)}✅ / {len(losses)}🛑) "
                f"· متوسط أقصى ربح {avg:+.0f}%")
    # أرضية ثقة Wilson: يحوّل «العيّنة صغيرة» من تحذير نصّي إلى رقم صلب
    head.append(f"   الأرضية الموثوقة للنجاح على {n} صفقة: "
                f"{_wilson_lower_pct(len(wins), n):.0f}% (لا تنبؤ — حدّ أدنى إحصائي)")
    # 🎯 توقّع الصفقة بوحدة المخاطرة (R): هل الحافة موجبة أصلًا؟ (مقياس مختلف عن النسبة)
    _rs = [x for x in (_realized_r(r) for r in rows) if x is not None]
    if _rs:
        _er = sum(_rs) / len(_rs)
        head.append(f"🎯 توقّع الصفقة الواحدة: <b>{_er:+.1f}R</b> — النجاح {wr:.0f}% "
                    f"والصفقة الواحدة تكسب متوسطًا {_er:.1f} ضعف ما تخاطر به "
                    "(الهدف المُصاب مقابل الوقف).")
    # A5: حارس العيّنة الصغيرة — يمنع الانجرار خلف نسب على 3-10 صفقات
    if n < 20:
        head.append(f"⚠️ العيّنة صغيرة (N={n}) — النِّسَب أدناه استرشادية؛ "
                    "لا قرارات ضبط قبل 20 صفقة محسومة.")
        _sw = [r.get("score") for r in wins if r.get("score") is not None]
        _sl = [r.get("score") for r in losses if r.get("score") is not None]
        if _sw and _sl and sum(_sl) / len(_sl) > sum(_sw) / len(_sw):
            head.append(f"   ملاحظة: متوسط قوة الخاسرين "
                        f"({sum(_sl) / len(_sl):.0f}) أعلى من الرابحين "
                        f"({sum(_sw) / len(_sw):.0f}) — القوة ليست تنبؤية بعد.")

    def seg(title, keyfn):
        groups = {}
        for r in rows:
            k = keyfn(r)
            if k is None:
                continue
            groups.setdefault(k, []).append(r)
        items = [(k, _wr(v)) for k, v in groups.items() if _wr(v)[0] >= 3]
        if not items:
            return []
        items.sort(key=lambda x: -x[1][1])
        out = [f"\n📊 <b>{title}</b>"]
        for k, (gn, gwr, gmg) in items:
            out.append(f"   • {esc(str(k))}: {gwr:.0f}% نجاح "
                       f"({gn} صفقة · {gmg:+.0f}% متوسط)")
        return out

    def _bucket(v, edges):
        if v is None:
            return None
        for lo, hi, lbl in edges:
            if lo <= v < hi:
                return lbl
        return None

    # (1) تشخيص الأداء بالشرائح
    body = []
    body += _honest_metrics_block(rows)   # 📏 الوسيط + اعتماد الذيل (صدق الحافة)
    # 🪦 A متقاعد: الوسم يبقى للصفوف التاريخية فقط (لو وُجدت) — الجديد كله «مؤهّل»
    body += seg("حسب القائمة", lambda r: {
        "A": "A (تاريخي — تصنيف متقاعد)", "B": "مؤهّل",
        "W": "مراقبة ارتداد"}.get(r.get("tier")) if r.get("tier") else None)
    body += seg("حسب القطاع", lambda r: ar_sector(r.get("sector")) or None)
    body += seg("حسب RSI عند الدخول", lambda r: _bucket(
        r.get("rsi"), [(0, 28, "27 أو أقل (مثالي)"), (28, 33, "28-32"),
                       (33, 41, "33-40"), (41, 200, "أعلى من 40")]))
    body += seg("حسب الفلوت", lambda r: _bucket(
        (r.get("float") or 0) / 1e6 if r.get("float") else None,
        [(0, 10, "أقل من 10م"), (10, 30, "10-30م"), (30, 1e9, "أكثر من 30م")]))
    body += seg("حسب الشورت", lambda r: _bucket(
        r.get("short"),
        [(0, 20000, "20ألف أو أقل"), (20000, 40000, "20-40ألف"), (40000, 1e12, "أعلى من 40ألف")]))
    body += seg("حسب العائد/المخاطرة", lambda r: _bucket(
        r.get("rr"), [(0, 1.5, "أقل من 1.5×"), (1.5, 2.5, "1.5-2.5×"), (2.5, 99, "2.5× أو أكثر")]))

    # إشارات: نسبة النجاح عند وجود كل إشارة
    flag_names = set()
    for r in rows:
        for f in (r.get("flags") or []):
            flag_names.add(f.split("(")[0].strip())
    flag_rows = []
    for fn in flag_names:
        present = [r for r in rows if any(
            (f.split("(")[0].strip() == fn) for f in (r.get("flags") or []))]
        gn, gwr, _ = _wr(present)
        if gn >= 3:
            flag_rows.append((fn, gn, gwr))
    if flag_rows:
        flag_rows.sort(key=lambda x: -x[2])
        body.append("\n🚦 <b>حسب الإشارة (نسبة النجاح عند وجودها)</b>")
        for fn, gn, gwr in flag_rows:
            body.append(f"   • {fn}: {gwr:.0f}% ({gn})")

    # (2) أنماط الفشل
    fails = ["\n🛑 <b>أنماط الخاسرين</b>"]
    if losses:
        sec_cnt, flag_cnt = {}, {}
        for r in losses:
            sc = ar_sector(r.get("sector"))
            if sc:
                sec_cnt[sc] = sec_cnt.get(sc, 0) + 1
            for f in (r.get("flags") or []):
                nm = f.split("(")[0].strip()
                flag_cnt[nm] = flag_cnt.get(nm, 0) + 1
        tier_l = sum(1 for r in losses if r.get("tier") == "B")
        fails.append(f"   • {tier_l}/{len(losses)} من الخاسرين كانوا B مراقبة")
        top_sec = sorted(sec_cnt.items(), key=lambda x: -x[1])[:2]
        if top_sec:
            fails.append("   • أكثر قطاعات الخسارة: "
                         + "، ".join(f"{esc(str(k))} ({v})" for k, v in top_sec))
    body += fails if len(fails) > 1 else []

    # عمق الأهداف: أي هدف نوصله؟ وكم يطول؟ (هل أهدافنا واقعية / نخرج بدري؟)
    if wins:
        depth = {"t1": 0, "t2": 0, "t3": 0}
        for w_ in wins:
            h = w_.get("hit")
            if h in depth:
                depth[h] += 1
        days = []
        for w_ in wins:
            try:
                a = dt.date.fromisoformat(str(w_.get("added")))
                hd = dt.date.fromisoformat(str(w_.get("hit_date")))
                days.append((hd - a).days)
            except Exception:
                pass
        dep = ["\n🎯 <b>عمق الأهداف (الرابحون)</b>",
               f"   t1 فقط: {depth['t1']} · t2: {depth['t2']} · t3: {depth['t3']}"]
        if depth["t2"] + depth["t3"] == 0 and depth["t1"] >= 4:
            dep.append("   ↳ نوصل t1 فقط دائمًا — قد تكون t2/t3 بعيدة، فكّر بتقريبها.")
        if days:
            dep.append(f"   متوسط زمن الوصول للهدف: {sum(days)/len(days):.0f} يوم")
        body += dep

    body += _missed_block()           # 👻 الفرص الفائتة
    body += _explosions_block()       # 💥 الانفجارات المفقودة
    body += _denominator_block()      # 🧮 A1: مقام الرفض (نسبة الفائتة/المقام)
    body += _ignition_log_block(_ig_log)  # 🔥 قياس حافة الرادار الحي (الالتقاط/الكاذب)

    # (3) اقتراحات ضبط (اقتراح فقط — لا يغيّر إعدادات)
    # 🪦 اقتراح «A أفضل من B» أُزيل مع تقاعد التصنيف (A لم تُنتَج قط —
    # الشرط مستحيل التحقّق، وبقاؤه يوحي أن المقارنة ما زالت قائمة).
    sugg = ["\n💡 <b>اقتراحات ضبط (للمراجعة فقط — لا تُطبّق تلقائيًا)</b>"]
    hi_rsi = [r for r in rows if (r.get("rsi") or 0) > 40]
    if len(hi_rsi) >= 5 and _wr(hi_rsi)[1] < wr - 15:
        sugg.append(f"   • صفقات RSI أعلى من 40 نجاحها {_wr(hi_rsi)[1]:.0f}% (أقل من المعدل) "
                    "— فكّر بتشديد سقف RSI.")
    lo_rr = [r for r in rows if (r.get("rr") or 0) < 1.5]
    if len(lo_rr) >= 5 and _wr(lo_rr)[1] < wr - 15:
        sugg.append(f"   • صفقات RR أقل من 1.5× نجاحها {_wr(lo_rr)[1]:.0f}% — "
                    "فكّر برفع حد RR الأدنى.")
    if len(sugg) == 1:
        sugg.append("   • لا نمط واضح بعد — البيانات متّسقة أو غير كافية لاقتراح.")

    tail = ["", "⚠️ <i>أداة تطوير ذاتي تتعلّم من نتائج البوت — ليست توصية. "
            "الاقتراحات للمراجعة البشرية فقط.</i>"]
    return "\n".join(head + body + sugg + tail)


def write_csv(rows: list, prefix: str) -> None:
    if not (CONFIG["REPORT_CSV"] and rows):
        return
    try:
        fn = f"{prefix}_{dt.date.today().isoformat()}.csv"
        pd.DataFrame(rows).to_csv(fn, index=False, encoding="utf-8-sig")
        log(f"حُفظ التقرير: {fn}")
    except Exception as e:
        log(f"⚠️ حفظ CSV: {e}")


def run_weekly_renewal(wl: dict) -> None:
    """التجديد الأسبوعي (الجمعة بعد إغلاق السوق) أو التأسيس الأول:
    حصاد الأسبوع المنتهي + بناء قائمة جديدة. يقرأ إغلاق الجمعة →
    الشمعة الأسبوعية مكتملة (فريمات M6/الفجوات/الأهداف الأسبوعية)."""
    today_iso = dt.date.today().isoformat()
    # عنوان الرسالة: «قائمة جديدة» لو كان في قائمة سابقة تُستبدَل، وإلا «تأسيسية».
    had_prev_list = bool(wl.get("stocks"))
    # 1) إغلاق الأسبوع المنتهي (إن وُجد) بتحديث أخير + رسالة حصاد
    old_syms = sorted({s["symbol"] for s in wl["stocks"]})
    if old_syms and yf is not None:
        # ⑫ (إصلاح تدقيق 2026-07-12): حارس تغطية **الأسبوع المنتهي** — كان حارس
        # الصحة يحرس الفرز الجديد فقط؛ خنق ياهو هنا كان يؤرشف أسبوعًا غير محسوم
        # (ستوبات الأسبوع تفلت بأسعار قديمة وتُعاد ترشيحها بنفس المساء). دون
        # التغطية → تأجيل التجديد كاملًا (نفس دلالة حارس الكون: القائمة النشطة
        # محفوظة ويُعاد التجديد لاحقًا).
        try:
            hist_old = download_history(old_syms)
            _cov_old = (sum(1 for s in old_syms
                            if hist_old.get(s) is not None
                            and len(hist_old[s]) > 0) / len(old_syms) * 100.0)
            if _cov_old < CONFIG["DATA_HEALTH_MIN_PCT"]:
                msg = (f"⚠️ تجديد مؤجَّل: تغطية بيانات الأسبوع المنتهي "
                       f"{_cov_old:.0f}% فقط (خنق مصدر البيانات؟) — لا نؤرشف "
                       "أسبوعًا غير محسوم. القائمة النشطة محفوظة، يُعاد التجديد لاحقًا.")
                log(msg)
                send_telegram(msg + "\n\n" + FOOTER)
                return
            update_watchlist_status(wl, hist_old)
        except Exception as e:
            log(f"⚠️ تحديث الأسبوع المنتهي فشل كليًا: {e} — تأجيل التجديد "
                "(لا أرشفة لأسبوع غير محسوم)")
            return
    # رسالة الحصاد تُرسل دائماً (حتى لو تعذر التحديث الأخير)
    wrap = build_wrapup_message(wl)
    if wrap:
        send_telegram(wrap)
    # 3) فرز جديد واختيار القائمة
    exclude = set()
    if CONFIG["EXCLUDE_STOPPED_FROM_RENEWAL"]:
        exclude = {s["symbol"] for s in wl["removed"]
                   if s["status"] == "stopped"}
    results, hist = scan_market()
    # حارس ضد مسح القائمة: لو خُنق فحص الجمعة (تغطية ضعيفة/صفر نتائج) **أو** فشل
    # جلب كون ناسداك (يتحوّل لعيّنة اختبار صغيرة تغطيتها ~100% فيخدع حساب التغطية)
    # — لا نستبدل القائمة النشطة. نحفظ الستوبات المرصودة ونُبقي القائمة، ويُؤجَّل
    # التجديد للتشغيل القادم (المتابعات الجارية لا تُفقد). إصلاح فحص 2026-06-24.
    _uni = _SCAN_STATS.get("universe") or 0
    _val = _SCAN_STATS.get("valid") or 0
    _cov = (_val / _uni * 100.0) if _uni else 0.0
    _fallback = _SCAN_STATS.get("universe_fallback", False)
    if not results or _cov < CONFIG["DATA_HEALTH_MIN_PCT"] or _fallback:
        _why = ("فشل جلب كون ناسداك (عيّنة اختبار صغيرة)" if _fallback
                else f"تغطية بيانات ضعيفة ({_cov:.0f}%) — غالبًا خنق مؤقت من Yahoo")
        log(f"⚠️ تجديد مُلغى: {_why} — القائمة النشطة محفوظة، يُعاد التجديد لاحقًا.")
        save_watchlist(wl)   # نحفظ الستوبات المرصودة (لا تضيع) — القائمة كما هي
        try:
            send_telegram("⚠️ <b>تأجّل تجديد القائمة الأسبوعية</b>\n"
                          f"السبب: {_why}.\nالقائمة النشطة الحالية محفوظة كما هي، "
                          "ويُعاد التجديد تلقائيًا في التشغيل القادم.")
        except Exception as e:
            log(f"⚠️ إشعار تأجيل التجديد: {e}")
        return
    # 2) أرشفة الأسبوع المنتهي (فقط عند تجديد فعلي — لا على مسار التأجيل) —
    #    نحفظ سمات الدخول مع النتيجة لربط «ليش نجح/فشل» لاحقًا.
    if wl.get("week_start"):
        summary = {"week_start": wl["week_start"], "ended": today_iso,
                   "stocks": [{k: s.get(k) for k in
                               ("symbol", "entry_ref", "last_price",
                                "max_gain_pct", "status", "hit", "hit_date",
                                "added", "removal_reason", "tier", "sector",
                                "score", "flags", "rsi", "float", "short",
                                "drop_pct", "best_spike", "rr")}
                              for s in wl["stocks"] + wl["removed"]]}
        # ⚠️ اسم مستقل (arch) عمدًا — لا تُعِد استخدام `hist` هنا: تظليل الاسم كان
        # يمرّر قائمة الأرشيف بدل قاموس الأسعار إلى accumulate_explosions/
        # scan_pullback أدناه فيفشلان بصمت وتُبنى قائمة الارتداد فارغة كل جمعة
        # (إصلاح تدقيق 2026-07-10 — F-01).
        arch = wl.setdefault("history", [])
        arch.append(summary)
        # N2: حارس تكرار — لو أُرشِف الأسبوع نفسه سابقًا (تشغيل متكرر) يُستبدل
        # بالأحدث بدل ما يتراكم؛ فالتقرير في نفس التشغيل يرى أرشيفًا نظيفًا.
        wl["history"] = _dedup_history(arch)[-26:]
    try:
        accumulate_explosions(wl, hist)   # كاشف الانفجارات (للتعلّم)
    except Exception as e:
        log(f"⚠️ كاشف الانفجارات: {e}")
    try:
        record_reject_stats(wl)           # A1: مقام أسباب الرفض (للتعلّم)
    except Exception as e:
        log(f"⚠️ مقام الرفض: {e}")
    picks = select_top(results, CONFIG["WATCHLIST_SIZE"], exclude)
    try:
        enrich(picks)  # SEC + شورت للقائمة الجديدة
    except Exception as e:
        log(f"⚠️ الإثراء: {e}")
    splits = []   # (أُلغي عرض التقسيم العكسي — يهمّنا A وB فقط)
    # 3ب) قائمة مراقبة الارتداد المستقلة (تعيد استخدام نفس البيانات)
    pull_entries = []
    try:
        excl = {r["symbol"] for r in picks}
        w_list = scan_pullback(hist, exclude=excl)
        if w_list:
            enrich(w_list)
        pull_entries = [make_pullback_entry(w, today_iso) for w in w_list]
    except Exception as e:
        log(f"⚠️ مراقبة الارتداد: {e}")
    # 4) حفظ القائمة الجديدة — ⑥ (إصلاح تدقيق 2026-07-12): نبدأ بنسخة من wl
    # القديم ثم نكتب فوق **مفاتيح التجديد فقط**، فتنجو المفاتيح المتراكمة
    # (reject_stats — كان يُمسح كل جمعة فمقام «الفائتة/المقام» لا يتراكم 56 يومًا
    # أبدًا رغم وعد الدالة) **وأي مفتاح حالة مستقبلي افتراضيًا** (كانت القائمة
    # البيضاء لغمًا بنيويًا: كل مفتاح جديد يختفي بصمت أول جمعة).
    new_wl = dict(wl)
    new_wl.update({"week_start": today_iso, "created": today_iso,
                   "logic_version": LOGIC_VERSION,   # القائمة مبنية على آخر منطق
                   "stocks": [make_watch_entry(r, today_iso) for r in picks],
                   "removed": [], "replacements_log": [], "notes": [],
                   "pullback": pull_entries,
                   "history": wl.get("history", []),
                   "explosions": wl.get("explosions", [])})   # سجل الانفجارات يستمر
    save_watchlist(new_wl)
    # 5) رسالة القائمة الجديدة (بطاقات كاملة)
    title = ("🔄 <b>القائمة الأسبوعية الجديدة</b>" if had_prev_list
             else "🚀 <b>القائمة التأسيسية (تُجدَّد الجمعة بعد إغلاق السوق)</b>")
    subnote = None
    if len(picks) < CONFIG["WATCHLIST_SIZE"]:
        subnote = (f"(وُجد {len(picks)} فقط يطابق الشروط — "
                   f"الحد الأقصى {CONFIG['WATCHLIST_SIZE']})")
    msg = build_message(picks, splits, title=title, subnote=subnote)
    msg += "\n" + build_pullback_section(pull_entries)
    send_telegram(msg)
    # 5.5) 🔬 مساعد التطوير (تقرير مستقل) + تصدير CSV للمشرف — بعد الفرز
    #      (الفرص الفائتة _MISSED جاهزة الآن من scan_market أعلاه).
    alert_data = None

    try:
        alert_data = load_alerts()
        dev = build_dev_assistant_report(wl, alert_data)
        if dev:
            send_telegram(dev)
    except Exception as e:
        log(f"⚠️ مساعد التطوير: {e}")
    try:
        export_weekly_csvs(wl, picks, alert_data)
    except Exception as e:
        log(f"⚠️ تصدير CSV: {e}")
    # 6) CSV + تتبع الأداء (يسجل القائمة كتنبيهات ويتابع القدامى)
    write_csv([{
        "symbol": r["symbol"], "price": r["price"], "score": r["score"],
        "drop%": round(r["drop_pct"], 1), "spike%": round(r["best_spike"], 0),
        "pivot": round(r["pivot"], 2), "stop_lo": round(r["stop"][0], 2),
        "t1": round(r["t1"], 2), "rr1": round(r["rr"], 2),
        "rr2": round(r["rr2"], 2), "ready": r["ready"],
        "flags": " | ".join(r["flags"]),
        "warnings": " | ".join(r.get("warnings", [])),
    } for r in picks], "weekly_list")
    try:
        # التجديد الأسبوعي → أرسل التقرير الأسبوعي معه (أسبوع كامل على إغلاق الجمعة)
        run_performance_system(picks, weekly_report_now=True)
    except Exception as e:
        log(f"⚠️ نظام التتبع: {e}")


def merge_pullback(wl: dict, hist: dict, exclude: set, today_iso: str) -> None:
    """يدمج مرشّحي الارتداد الجدد في القائمة المستقلة (يُضيف فقط، لا يحذف).
    لا يُكرّر سهماً موجوداً، ويحترم الحد الأقصى."""
    if not CONFIG.get("PULLBACK_WATCH", False):
        return
    existing = {e["symbol"] for e in wl.get("pullback", [])}
    # الحد على إجمالي القائمة (يشمل «triggered») حتى لا تتجاوز PULLBACK_SIZE
    # بتراكم المُفعّلة فوق الحد بين تجديدات الجمعة (إصلاح 2026-06-24).
    space = CONFIG.get("PULLBACK_SIZE", 10) - len(wl.get("pullback", []))
    if space <= 0:
        return
    cands = scan_pullback(hist, exclude=exclude | existing)
    new = cands[:space]
    if not new:
        return
    try:
        enrich(new)
    except Exception as e:
        log(f"⚠️ إثراء الارتداد: {e}")
    wl.setdefault("pullback", []).extend(
        make_pullback_entry(w, today_iso) for w in new)


def prune_graduated_pullback(wl: dict) -> list:
    """نظافة بيانات: يشيل من قائمة مراقبة الارتداد أي سهم **تخرّج فعليًا**
    لقائمة A/B الأساسية (دخل `wl["stocks"]`) — فلا يبقى في القائمتين معًا.
    يرجع رموز المُتخرّجة."""
    main = {s["symbol"] for s in wl.get("stocks", [])}
    pb = wl.get("pullback") or []
    graduated = [e["symbol"] for e in pb if e["symbol"] in main]
    if graduated:
        wl["pullback"] = [e for e in pb if e["symbol"] not in main]
    return graduated


def run_daily_watchlist(wl: dict) -> None:
    """يومي (غير الجمعة): قائمة ثابتة دائمة — تُتابَع وتُضاف لها الجديد فقط.
    **الشطب بالستوب فقط**؛ الهدف المُحقَّق **لا يُنهي المتابعة** (يبقى نشطًا
    لتسجيل سلّم الأهداف t1→t2→t3، فيصل يمتّع) لكنه **لا يحجز خانة** فلا يمنع
    مرشّحًا جديدًا (⑨ خيار ب، تدقيق 2026-07-12). التجديد الكامل الجمعة. سوق
    مقفل = نفس القائمة (تنمو، ما ترفرف)."""
    today_iso = dt.date.today().isoformat()
    # 1) فرز كامل للسوق (لالتقاط الجديد) — بياناته تُعاد استخدامها للمتابعة
    results, hist = scan_market()
    # 2) تحميل أي رمز في القائمة لم يأتِ ضمن الفرز (نادر) حتى نتابعه
    wl_syms = {s["symbol"] for s in wl["stocks"]}
    missing = [s for s in wl_syms if s not in hist]
    if missing and yf is not None:
        try:
            hist.update(download_history(missing))
        except Exception as e:
            log(f"⚠️ تحميل رموز القائمة: {e}")
    # 2.5) ترحيل آلي: لو تغيّرت نسخة منطق الكود → أعِد حساب القائمة كاملة فورًا
    #      (ضمان: لا تبقى بيانات قديمة بعد أي تعديل — قبل فحص الستوب).
    try:
        migrate_watchlist(wl, hist)
    except Exception as e:
        log(f"⚠️ ترحيل القائمة: {e}")
    # 2.6) كاشف الانفجارات اليومية (للتعلّم) — يتراكم ويُعرض بتقرير الجمعة
    try:
        accumulate_explosions(wl, hist)
    except Exception as e:
        log(f"⚠️ كاشف الانفجارات: {e}")
    try:
        record_reject_stats(wl)           # A1: مقام أسباب الرفض (للتعلّم)
    except Exception as e:
        log(f"⚠️ مقام الرفض: {e}")
    # 3) متابعة القائمة الحالية (تُحذف فقط بستوب/هدف؛ نقص البيانات = تُبقى)
    try:
        stopped_today = update_watchlist_status(wl, hist)
    except Exception as e:
        log(f"⚠️ تحديث حالة القائمة: {e}")
        stopped_today = []
    # 4) إضافة الجديد دون حذف القديم (حتى حد القائمة)
    # حارس التغطية اليومي (إصلاح فحص 2026-06-26): لو خُنق Yahoo (تغطية ضعيفة) أو
    # فشل جلب كون ناسداك (رجوع لعيّنة 28 رمز تبدو 100%) — لا نضيف أسهمًا من فرز غير
    # موثوق (نتجنّب تفويت ارتكازات حقيقية لم تُفحَص أصلًا). المتابعة مستمرة دائمًا.
    # نفس مقياس حارس الجمعة (run_weekly_renewal) — كان غائبًا عن المسار اليومي (4/5 أيام).
    _uni = _SCAN_STATS.get("universe") or 0
    _val = _SCAN_STATS.get("valid") or 0
    _cov = (_val / _uni * 100.0) if _uni else 0.0
    _fallback = _SCAN_STATS.get("universe_fallback", False)
    coverage_ok = bool(results) and _cov >= CONFIG["DATA_HEALTH_MIN_PCT"] \
        and not _fallback
    held = {s["symbol"] for s in wl["stocks"]}
    stopped = {rm["symbol"] for rm in wl["removed"]
               if rm.get("status") == "stopped"}
    # ⑨ (تدقيق 2026-07-12، خيار ب): أصحاب الهدف المُحقَّق (`hit`) لا يحجزون خانة —
    # النموذج نجح ويبقى نشطًا لتسجيل سلّم الأهداف (t1→t2→t3، فيصل يمتّع)، لكن
    # لا يجب أن يمنع مرشّحًا جديدًا في أفضل الأسابيع. نحسب السعة على «الحاملين
    # للخانة» = النشطون **بلا هدف** فقط. (الأرباح ما زالت في held فلا تُكرَّر.)
    _slot_holders = [s for s in wl["stocks"] if not s.get("hit")]
    space = CONFIG["WATCHLIST_SIZE"] - len(_slot_holders)
    added = []
    low_coverage_note = None
    if space > 0 and not coverage_ok:
        low_coverage_note = ("فشل جلب كون ناسداك (عيّنة اختبار صغيرة)" if _fallback
                             else f"تغطية بيانات ضعيفة ({_cov:.0f}%)")
        log(f"⚠️ تخطّي إضافة الجديد اليوم: {low_coverage_note} — "
            "القائمة الحالية تُتابَع كالمعتاد.")
    elif space > 0:
        picks = select_top(results, space, exclude=held | stopped)
        if picks:
            try:
                enrich(picks)
            except Exception as e:
                log(f"⚠️ الإثراء: {e}")
            for r in picks:
                wl["stocks"].append(make_watch_entry(r, today_iso))
                added.append(r)
            if added:
                log("أُضيف للقائمة: " + "، ".join(p["symbol"] for p in added))
    # 5) ترقية B→A (إنذار مبكر) + نسبة الجاهزية اليومية
    promoted = []
    try:
        promoted = check_promotions(wl, hist)
    except Exception as e:
        log(f"⚠️ فحص الترقيات: {e}")
    compute_readiness(wl, hist)
    # 📅 تحديث الأحداث المعلنة يوميًّا لكل النشطين («يوم الانفجار الذي ينتظره المضارب»
    # — فيصل 9428): فاشل-آمن لكل رمز على حدة، والقيمة القديمة تبقى لو تعذّر الجلب
    # (تاريخ معلوم لا يختفي بعطل شبكي؛ الماضي يُخفيه العرض ذاتيًّا).
    for s in wl["stocks"]:
        if s.get("status") != "active":
            continue
        try:
            _ue = upcoming_events(s["symbol"], s.get("company_name"),
                                  s.get("sector"), s.get("proxy_filing"),
                                  s.get("first_trade"))
            if _ue:
                s["upcoming_events"] = _ue
        except Exception:
            pass
        # 🔒 تحديث الاقتراض يوميًّا + مسار «المتاح» (فيصل يتابعه يوميًّا — IMG_9505:
        # قفز 30 ألف→600 ألف في 3 أيام قبيل «طاخ طيخ»). فاشل-آمن: القديم يبقى.
        refresh_borrow(s, today_iso)
        # 🏢 ردم الفلوت المجهول من ChartExchange (اقتراح المستخدم 2026-07-10):
        # الأسهم القديمة التي غاب فلوتها (ياهو مخنوق) تُملأ مرة واحدة (الفلوت
        # ثابت فيُخزَّن ويبقى). فاشل-آمن، وفقط عند الغياب (نداء واحد/سهم مرّة).
        if s.get("float") is None:
            try:
                _cf = ce_float_info(s["symbol"])
                if _cf:
                    s["float"] = _cf
            except Exception:
                pass
    # 6) دمج قائمة الارتداد الجديدة (تُضاف فقط) + التنبيه عند وصول الدعم.
    #    نمرّر القائمة الأساسية الحالية (تشمل ما أُضيف توًّا) كاستبعاد، ثم
    #    نشيل أي سهم تخرّج للأساسية من المراقبة (لا ازدواج بين القائمتين).
    held_now = {s["symbol"] for s in wl["stocks"]}
    try:
        merge_pullback(wl, hist, held_now | stopped, today_iso)
    except Exception as e:
        log(f"⚠️ دمج الارتداد: {e}")
    graduated = prune_graduated_pullback(wl)
    if graduated:
        log("تخرّج من مراقبة الارتداد → A/B: " + "، ".join(graduated))
    pull_triggered = []
    try:
        pull_triggered = monitor_pullback(wl)
    except Exception as e:
        log(f"⚠️ متابعة الارتداد: {e}")
    # 7) الرسالة — **رسالتان فقط** (طلب المستخدم 2026-07-09): (1) الجاهز للدخول فقط
    # (2) أسهم اليد. المتابعة/الارتداد المنتظِر/التقسيم = «تحت المراقبة» يتكفّل بها البوت
    # داخليًّا (تنبيه لحظي عند الجاهزية) — لا تُدفَع في التقرير حتى لا تغرق المهم.
    splits = []
    msg = build_daily_message(wl, splits, stopped_today, added, promoted,
                              ready_only=True)
    if low_coverage_note:   # تنبيه التغطية للمستخدم (يكشف الخنق الصامت Mon-Thu)
        msg += ("\n\n⚠️ <b>تنبيه تغطية:</b> " + low_coverage_note
                + " — لم تُضف أسهم جديدة اليوم (متابعة القائمة الحالية مستمرة).")
    # 🕵️ أسهم اليد = **رسالة تلغرام مستقلة** (طلب المستخدم: «ما تندفن بالتقرير
    # الطويل») — تُرسَل منفصلة بعد التقرير الرئيسي أدناه، لا تُلحَق به.
    hand_msg = build_hand_section(wl)
    # الارتداد: يُدفَع **فقط ما وصل منطقة الدخول** (جاهز الآن) — المنتظِر يتابعه البوت.
    pull_sec = build_pullback_section([], pull_triggered)
    if pull_sec:
        msg += "\n\n" + pull_sec
    # (قسم مراقبة التقسيم العكسي D9 لم يعد يُدفَع بالتقرير اليومي — «تحت المراقبة»؛
    # قاعدة فيصل ÷2 محفوظة بالكود وتُستدعى عند الحاجة/الجمعة، لا تغرق تقرير الجاهز.)
    # احفظ حالة اليوم (ترقيات/تنبيهات/تحديثات) قبل الإرسال — لو فشل الإرسال
    # (شبكة/تيليجرام) لا تضيع الحالة المحسوبة (إصلاح 2026-06-24).
    save_watchlist(wl)
    send_telegram(msg)
    # 🕵️ رسالة أسهم اليد المستقلة (منفصلة عن التقرير الطويل — لا تُدفن)
    if hand_msg:
        send_telegram(hand_msg + "\n\n" + FOOTER)
    write_csv([{
        "symbol": s["symbol"], "readiness%": s["readiness"],
        "price": s["last_price"], "pivot": s["pivot"], "stop": s["stop"],
        "t1": s["t1"], "hit": s["hit"] or "",
        "max_gain%": s["max_gain_pct"],
    } for s in wl["stocks"]], "daily_watch")
    try:
        run_performance_system(added)
    except Exception as e:
        log(f"⚠️ نظام التتبع: {e}")


def run_hand_digest() -> None:
    """🕵️ تحديث نهاية اليوم (مسار خفيف مستقل — طلب المستخدم 2026-07-08): يحمّل
    القائمة + بيانات رموزها **الطازجة فقط** (لا فرز سوق كامل) → يحدّث بصمة اليد/
    الرفعة من شمعة اليوم → يرسل ملخّص «ماذا فعلت اليد اليوم». **عرض/إشعار فقط —
    لا يحفظ القائمة ولا يمسّ الحالة القانونية** (تجنّب أي سباق مع تشغيل الصباح)."""
    wl = load_watchlist()
    syms = [s["symbol"] for s in wl.get("stocks", [])
            if s.get("status") == "active"]
    if not syms:
        log("تحديث اليد: القائمة فارغة — لا شيء لإرساله.")
        return
    hist = {}
    if yf is not None:
        try:
            hist = download_history(syms)
        except Exception as e:
            log(f"⚠️ تحديث اليد: تحميل البيانات {e}")
    for s in wl.get("stocks", []):     # تحديث البصمة/الرفعة من شمعة اليوم (بالذاكرة)
        df = hist.get(s["symbol"])
        if df is None:
            continue
        try:
            _bh = behavior_rise_profile(df)
            if _bh.get("score") is not None:
                s["behav"] = _bh
            s["pump_scar"] = group_pump_scar(df)
            s["last_price"] = round(float(df["Close"].iloc[-1]), 4)
        except Exception:
            pass
    send_telegram(build_hand_digest(wl, hist))
    log("✅ أُرسل تحديث اليد (نهاية اليوم).")


# ==========================================================
# 10) التشغيل الرئيسي
# ==========================================================
def _resolve_arm(hi, lo, cl, op, entry, stop, t1, filled, entry_intrabar=True,
                 spread=0.0):
    """يحسم صفقة باكتيست من فهرس التعبئة بذراعَي الوقف (نفس منطق A/B، مصدر واحد):
    ذراع الذيل (A): الوقف بلمسة الذيل `low<=stop`، الخروج `min(stop, open)` لواقعية
    الفجوة · ذراع الإغلاق (B): الوقف بإغلاق `close<=stop`. الرابح يخرج t1، العالق آخر
    إغلاق. يرجّع (outcome_wick, ret_wick, outcome_close, ret_close)؛ العائد None إن لم
    تُعبَّأ. مصدر واحد يضمن أن تجربة الدخول تُقاس بنفس محرّك الأساس تمامًا (مقارنة عادلة)."""
    if filled is None or entry <= 0:
        return ("no_fill", None, "no_fill", None)
    # 🔬 F-L1 (تدقيق النظر المستقبلي 2026-07-12): للتعبئة داخل الشمعة (الأساس) لا
    # يُحسم الهدف على شمعة التعبئة نفسها — ترتيب اللمس داخلها مجهول (قد يُضرب t1 قبل
    # نزول السعر لدخولنا = فوز وهمي). الستوب يبقى محميًّا (يُفحص أولًا). ذراع المسح
    # (entry_intrabar=False) يدخل بإغلاق الاستعادة فيملك من الفتح التالي = لا لبس.
    t1_from = (filled + 1) if entry_intrabar else filled
    last_close = float(cl[-1])
    ow, exit_w = "open", last_close
    for k in range(filled, len(cl)):
        if lo[k] <= stop:                       # الوقف أولًا (محافظ، حتى شمعة التعبئة)
            ow, exit_w = "loss", min(stop, float(op[k]))
            break
        if k >= t1_from and hi[k] >= t1:        # F-L1: ليس على شمعة التعبئة الداخلية
            ow, exit_w = "win", t1
            break
    oc, exit_c = "open", last_close
    for k in range(filled, len(cl)):
        if cl[k] <= stop:
            oc, exit_c = "loss", float(cl[k])
            break
        if k >= t1_from and hi[k] >= t1:
            oc, exit_c = "win", t1
            break
    # 🔬 F-COST: تكلفة التنفيذ (سبريد+انزلاق) — نشتري أغلى (ask) ونبيع أرخص (bid):
    # نصف السبريد على كل جهة. spread=0 → buy=entry والعامل 1 = سلوك اليوم حرفيًا.
    buy = entry * (1.0 + spread / 2.0)
    sell_f = 1.0 - spread / 2.0
    return (ow, (exit_w * sell_f / buy - 1.0) * 100.0,
            oc, (exit_c * sell_f / buy - 1.0) * 100.0)


def _max_gain_before_stop(hi, lo, op, entry, stop, filled, entry_intrabar=True):
    """🏦 «قوة البوت» (خطة BT_LADDER_PLAN، تصحيح المستخدم 2026-07-12): الحكم الحقيقي
    ليس أهداف البوت (تمهيدية = سلّم مقاومات) بل **كم انفجر السهم من نقطة الدخول قبل
    أن يضرب وقفه** — والوقف يبقى حاكمًا. دالة نقيّة، مشي يومي محافظ متّسق مع F-L1:
      • الوقف يُفحص أولًا كل شمعة (`low<=stop`): لمسه يقطع القياس → أقصى صعود **قبل**
        شمعة الوقف (رأس شمعة الوقف لا يُحسب — ترتيب اللمس داخلها مجهول).
      • القياس الموجب يبدأ من `filled+1` عند `entry_intrabar` (رأس شمعة التعبئة
        الداخلية لا يُحسب — قد يسبق تعبئتنا؛ نفس درس F-L1).
      • لا وقف بالنافذة → «survived» بأقصى صعود بها.
    يرجّع (outcome, max_gain_pct_before_stop, peak_day): outcome ∈ {stopped,
    survived, no_fill}. **يختلف عمدًا عن `fwd_max_gain`** (يُحسب على كامل النافذة
    حتى بعد الوقف) — الفرق بينهما = «انفجارات قتلها الوقف» (يقيس §0-ب بالأرقام).
    باكتيست حصريًا — لا يمسّ الفرز/الإنتاج."""
    if filled is None or entry <= 0:
        return ("no_fill", None, None)
    g_from = (filled + 1) if entry_intrabar else filled
    peak = 0.0
    peak_day = 0
    for k in range(filled, len(hi)):
        if lo[k] <= stop:                       # الوقف حاكم — يقطع القياس محافظًا
            return ("stopped", round(peak, 1), peak_day)
        if k >= g_from:
            g = (float(hi[k]) / entry - 1.0) * 100.0
            if g > peak:
                peak, peak_day = g, k - filled
    return ("survived", round(peak, 1), peak_day)


def backtest_portfolio(trades, size=None, fwd_days=None):
    """🏦 محاكاة الانتقائية الحية (خطة BT_LADDER_PLAN §3): يوميًا تتزاحم إشاراتٌ كثيرة
    على محفظة سعتها `size` (=BT_PORT_SIZE=WATCHLIST_SIZE) — تُؤخذ **الأعلى ترتيبًا**
    (readiness ثم score، محورا rank_key الحيّان المخزَّنان بكل صفقة) وتحجز كل مأخوذة
    خانةً نافذةً أمامية (`fwd_days` يومًا تقويميًا — نموذج محافظ يقارب «حتى الحسم/نهاية
    النافذة»). **لا خانتان لرمز واحد متزامنًا** · المرفوض بالسعة/التكرار **يُعدّ** (لا
    قصّ صامت). يرجّع dict: taken (الصفقات المأخوذة) · n_rejected_cap · n_rejected_dup.
    يجيب سؤال §0 النسبي: هل الانتقائية (top-N بالترتيب) تتفوّق على «كل المُعبَّئين»؟
    دالة نقيّة، بلا نظر مستقبلي (ترتيب زمني + مخزَّنات لحظة الإشارة) — **باكتيست/تحليل
    فقط، خارج الفرز/الاختيار الحي** (قفل getsource)."""
    size = int(size or CONFIG.get("BT_PORT_SIZE", 15))
    fwd_days = int(fwd_days if fwd_days is not None
                   else CONFIG["BACKTEST_FORWARD_DAYS"])

    def _pri(t):                       # أولوية اليوم = محورا rank_key (readiness→score)
        rdy = t.get("readiness")
        return (-(rdy if rdy is not None else -1), -(t.get("score") or 0))
    rows = []
    for t in trades:
        if t.get("outcome") == "no_fill":          # غير مُعبَّأة لا تحجز خانة
            continue
        try:
            o = dt.date.fromisoformat(str(t.get("date"))).toordinal()
        except Exception:
            continue                               # تاريخ غير صالح يُتخطّى بأمان
        rows.append((o, t))
    rows.sort(key=lambda ot: (ot[0], _pri(ot[1])))  # زمنيًا ثم الأعلى أولوية داخل اليوم
    active = {}                        # symbol → يوم تحرّر الخانة (ordinal)
    taken, n_cap, n_dup = [], 0, 0
    for o, t in rows:
        for s in [s for s, fo in active.items() if fo <= o]:   # حرّر المنتهية
            del active[s]
        sym = t.get("symbol")
        if sym in active:              # الرمز يحجز خانة أصلًا — لا دخول مزدوج
            n_dup += 1
            continue
        if len(active) >= size:        # لا خانة شاغرة — رُفض بالسعة (يُعدّ)
            n_cap += 1
            continue
        active[sym] = o + fwd_days
        taken.append(t)
    return {"taken": taken, "n_rejected_cap": n_cap, "n_rejected_dup": n_dup,
            "size": size, "fwd_days": fwd_days}


def _mg_segment_lines(trades, label):
    """أسطر شرائح «الحركة المتاحة قبل الوقف» لمجموعة صفقات (نقيّة، للتقرير)."""
    filled = [t for t in trades if t.get("mg_outcome") not in (None, "no_fill")]
    n = len(filled)
    if not n:
        return []
    gains = [float(t.get("mg_pre_stop") or 0.0) for t in filled]
    expl = int(CONFIG["EXPLOSION_PCT"])
    b100 = sum(1 for g in gains if g >= 100)
    b50 = sum(1 for g in gains if g >= expl)
    b30 = sum(1 for g in gains if g >= 30)
    b1030 = sum(1 for g in gains if 10 <= g < 30)
    blt = sum(1 for g in gains if g < 10)
    days = [t.get("mg_peak_day") for t in filled if t.get("mg_peak_day") is not None]
    return [f"  <b>{esc(label)}</b> ({n} مُعبَّأة): منفجر {expl}% أو أكثر قبل الوقف "
            f"<b>{b50} ({b50 / n * 100:.0f}%)</b>",
            f"    شرائح: 100%+={b100} · {expl}%+={b50} · 30%+={b30} · "
            f"10-30%={b1030} · أقل من 10%={blt}",
            f"    وسيط الصعود المشروط {_median(gains):.0f}% · متوسط "
            f"{sum(gains) / n:.0f}% · وسيط أيام الذروة {_median(days):.0f}"]


def backtest_potential_report(all_trades):
    """🏦 كتلة تقرير «قوة البوت» (خطة BT_LADDER_PLAN §4، تصحيح المستخدم 2026-07-12):
    الحكم = **كم انفجر كل سهم من نقطة الدخول قبل ضرب وقفه** + كم عددهم من المجمل —
    لا البيع على أهداف البوت (تمهيدية). المقاييس على «كل المُعبَّئين» **و** على محفظة
    top-N (هل الانتقائية تضيف؟ = سؤال §0 النسبي). يطبع المعيار المسجَّل + حدّي الصدق
    حرفيًا. يرجّع [] ما لم يُفعَّل BT_POTENTIAL (لا صفقة تحمل mg_*). تحليل فقط."""
    if not CONFIG.get("BT_POTENTIAL"):
        return []
    base = [t for t in all_trades if t.get("mg_outcome") not in (None, "no_fill")]
    if not base:
        return []
    lines = ["\n🏦 <b>قوة البوت (الحركة المتاحة من الدخول قبل الوقف)</b>"]
    lines += _mg_segment_lines(base, "كل المُعبَّئين")
    top = sorted(base, key=lambda t: -(float(t.get("mg_pre_stop") or 0)))[:8]
    if top:
        lines.append("    أقوى 8: " + " · ".join(
            f"{esc(str(t['symbol']))} +{float(t.get('mg_pre_stop') or 0):.0f}%"
            for t in top))
    # المحفظة (الانتقائية) — العمود المقابل: هل top-N بالترتيب يتفوّق على الكل؟
    if CONFIG.get("BT_PORTFOLIO"):
        pf = backtest_portfolio(all_trades)
        lines += _mg_segment_lines(pf["taken"], f"محفظة top-{pf['size']}")
        lines.append(f"    (المحفظة: مأخوذة {len(pf['taken'])} · مرفوض بالسعة "
                     f"{pf['n_rejected_cap']} · تكرار رمز {pf['n_rejected_dup']})")
    # §0-ب بالأرقام: انفجارات قتلها الوقف (صعدت ≥50% بالنافذة لكن بعد ضرب وقفها)
    expl = int(CONFIG["EXPLOSION_PCT"])
    killed = [t for t in base if t.get("exploded") and t.get("mg_outcome") == "stopped"
              and float(t.get("mg_pre_stop") or 0) < CONFIG["EXPLOSION_PCT"]]
    lines.append(f"  🔪 انفجارات قتلها الوقف: <b>{len(killed)}</b> "
                 f"(صعدت {expl}% أو أكثر بالنافذة لكن بعد ضرب وقفها)")
    # 🔬 ذراع المسح (لو BT_SWEEP_ENTRY+BT_POTENTIAL): هل الدخول-بعد-المسح يلتقط
    # الانفجارات المقتولة **من نقطة الدخول** (لا t1)؟ = سؤال المستخدم المباشر.
    swf = [t for t in base if t.get("mg_sweep_outcome")]   # عبّأ ذراع المسح
    if swf:
        base_e = sum(1 for t in swf if float(t.get("mg_pre_stop") or 0) >= expl)
        sw_e = sum(1 for t in swf if float(t.get("mg_sweep_pre_stop") or 0) >= expl)
        lines.append(f"  🔬 <b>ذراع المسح</b> (عبّأ {len(swf)} من {len(base)}): انفجار "
                     f"{expl}%+ قبل الوقف — الأساس {base_e} ← المسح <b>{sw_e}</b>")
        # الأهم: من الانفجارات المقتولة، كم عبّأها المسح وكم التقط ≥50% منها فعلًا
        sw_on_killed = [t for t in killed if t.get("mg_sweep_outcome")]
        recov = [t for t in sw_on_killed if float(t.get("mg_sweep_pre_stop") or 0) >= expl]
        lines.append(f"  🎯 <b>استرداد المقتولة</b>: من {len(killed)} قتلها الوقف — "
                     f"المسح عبّأ {len(sw_on_killed)} · التقط {expl}%+ منها <b>{len(recov)}</b>"
                     + ("  (" + " · ".join(f"{esc(str(t['symbol']))} +"
                        f"{float(t.get('mg_sweep_pre_stop') or 0):.0f}%" for t in recov)
                        + ")" if recov else ""))
    # المعيار المسجَّل مسبقًا §0 (قرار المستخدم بالأرقام، لا آليًا) + حدّا الصدق حرفيًا
    lines.append("  📋 <b>معيار مسجَّل مسبقًا</b>: قوي = منفجرون 20% أو أكثر (بالمحفظة، "
                 "السنتين) ووسيط صعود مشروط +15% أو أكثر · حدّي 10-20% · ضعيف أقل. "
                 "القرار بالأرقام لا آليًا.")
    lines.append("  ⚠️ أقصى الصعود = <b>الحركة المتاحة لا عائد محقَّق</b> (التحقيق يعتمد "
                 "إدارتك) · <b>أرضية لا سقف</b>: بلا حافة التوقيت اللحظي (الرادار/الكنسة).")
    return lines


def _sweep_confirmed_fill(lo, cl, support, sweep_pct):
    """🔬 تعبئة «الدخول المؤكَّد بالمسح» (فيصل: «قبل يصعد لازم مسح سيولة تحت القاع ثم
    استعادة · لا تدخل الدعم الأول»). مشي أمامي **بلا نظر مستقبلي**: عند كل شمعة نقرأ
    `lo[≤k]`/`cl[k]` فقط. (أ) شمعة مسح `low<=support*(1-sweep_pct)` ثم (ب) أول شمعة
    إغلاق يستعيد الدعم `close>=support` = تعبئة عند **إغلاق** الاستعادة (سعر محقَّق).
    يرجّع (fill_reason, reclaim_idx, entry_px, sweep_low): fill_reason ∈ {filled,
    no_sweep, sweep_no_reclaim}. sweep_low = أعمق ذيل حتى الاستعادة (لوقف تحت-الذيل).
    الحسم اللاحق يبدأ من reclaim_idx+1 حصرًا (لا نستعمل ذيل/رأس شمعة الدخول = لا تسريب).
    باكتيست حصريًا — لا يمسّ الفرز/الإنتاج."""
    sweep_px = support * (1.0 - sweep_pct)
    swept = False
    run_low = float("inf")
    for k in range(len(cl)):
        run_low = min(run_low, float(lo[k]))       # ماضٍ+حاضر فقط
        if not swept and lo[k] <= sweep_px:
            swept = True
        if swept and cl[k] >= support:             # استعادة مؤكَّدة بالإغلاق
            return ("filled", k, float(cl[k]), run_low)
    return (("sweep_no_reclaim" if swept else "no_sweep"), None, None,
            (run_low if run_low != float("inf") else None))


def _sweep_augment(trade, r, hi, lo, cl, op, stop, t1):
    """🔬 يُلحِق حقول تجربة «الدخول المؤكَّد بالمسح» بصفقة الأساس (باكتيست حصريًا،
    مطفأة افتراضيًا). على **نفس الإشارة**: نموذج دخول بديل = مسح تحت الدعم ثم استعادة
    (`_sweep_confirmed_fill`)، مقاسًا بنفس `_resolve_arm` (مقارنة عادلة). **الدخول
    منفصل عن الوقف**: `BT_SWEEP_STOP=0` (الافتراضي) يُبقي وقف الأساس فيعزل أثر الدخول
    عن أثر «تعميق الوقف» الذي فشل حيًّا (مراجعة خصومية)؛ `=1` يضع الوقف تحت ذيل المسح.
    الحقول: fill_reason_sweep · outcome_sweep(+_b) · ret_sweep_a/b · entry_sweep ·
    stop_sweep · swept. الحكم لاحقًا على المُعبَّأة فقط (backtest_sweep_compare)."""
    support = float(r.get("pivot") or min(r["tranches"]))
    fr, ridx, e_sw, sw_low = _sweep_confirmed_fill(
        lo, cl, support, CONFIG["BT_SWEEP_PCT"])
    trade["entry_model"] = "sweep_confirmed"
    trade["swept"] = (fr != "no_sweep")
    filled_sw = stop_sw = None
    if fr == "filled":
        filled_sw = ridx + 1
        if filled_sw >= len(cl):                 # استعادة بآخر شمعة = لا حسم أمامي
            fr, filled_sw = "reclaim_at_end", None
    if filled_sw is not None:
        stop_sw = (sw_low * (1.0 - CONFIG["BT_SWEEP_STOP_MARGIN"])
                   if CONFIG.get("BT_SWEEP_STOP") else stop)   # عزل الدخول عن الوقف
        rr = ((t1 - e_sw) / (e_sw - stop_sw)) if e_sw > stop_sw else 0.0
        if CONFIG["BT_SWEEP_MIN_RR"] and rr < CONFIG["BT_SWEEP_MIN_RR"]:
            fr, filled_sw = "rr_too_low", None
    o_sw = ret_sa = ret_sb = ob_sw = None
    if filled_sw is not None:
        # ذراع المسح يدخل بإغلاق الاستعادة (يملك من الفتح التالي) — لا لبس شمعة
        # التعبئة، فـ entry_intrabar=False (كان سلوكه الصحيح أصلًا؛ F-L1 يوثّقه صراحة).
        o_sw, ret_sa, ob_sw, ret_sb = _resolve_arm(
            hi, lo, cl, op, e_sw, stop_sw, t1, filled_sw, entry_intrabar=False,
            spread=CONFIG.get("BT_SPREAD_PCT", 0.0) or 0.0)   # 🔬 F-COST بالتساوي
    trade["fill_reason_sweep"] = fr
    trade["outcome_sweep"] = o_sw if o_sw is not None else fr
    trade["outcome_sweep_b"] = ob_sw if ob_sw is not None else fr
    trade["entry_sweep"] = (round(e_sw, 2) if e_sw is not None else None)
    trade["stop_sweep"] = (round(stop_sw, 2) if stop_sw is not None else None)
    trade["ret_sweep_a"] = (round(ret_sa, 1) if ret_sa is not None else None)
    trade["ret_sweep_b"] = (round(ret_sb, 1) if ret_sb is not None else None)
    # 🏦 قوة البوت لذراع المسح (لو BT_POTENTIAL): أقصى صعود من **دخول المسح** قبل وقفه —
    # يجيب سؤال المستخدم مباشرة: كم من «الانفجارات المقتولة» (مُسِحت تحت الوقف الثابت ثم
    # انطلقت) يلتقطها الدخول-بعد-المسح من نقطة الدخول (لا t1). نفس entry_intrabar=False
    # (يملك من فتح ridx+1 فرأس تلك الشمعة صالح). إلحاق فقط · مطفأ = لا حقول.
    if filled_sw is not None and CONFIG.get("BT_POTENTIAL"):
        _smo, _smg, _smd = _max_gain_before_stop(
            hi, lo, op, e_sw, stop_sw, filled_sw, entry_intrabar=False)
        trade["mg_sweep_outcome"] = _smo
        trade["mg_sweep_pre_stop"] = _smg
        trade["mg_sweep_peak_day"] = _smd


def backtest_symbol(sym: str, df: pd.DataFrame, reasons: dict = None,
                    date_window: tuple = None, splits=None, frozen: bool = False) -> list:
    """باكتيست سهم واحد — **مشي للأمام بلا نظر للمستقبل**: عند كل نقطة نحلّل
    البيانات حتى تلك النقطة فقط، ولو رشّح البوت ننتظر وصول السعر لمنطقة الدفعات
    (تعبئة واقعية) ثم نقيس: t1 قبل الوقف = ربح، الوقف أولًا = خسارة (محافظ:
    الوقف يفوز بالتعادل داخل الشمعة). يرجع قائمة صفقات بنتائجها.
    reasons (اختياري): dict يُملأ بعدّاد أسباب الرفض عبر أيام المشي — تشخيص
    «أي بوابة خنقت هذا السهم تاريخيًا» (باكتيست فقط، لا يمسّ الفرز).
    date_window (اختياري = (من، إلى) ISO، لوضع السوق الكامل): نقيّم نقاط الدخول
    **داخل هذه النافذة فقط** (النافذة الأمامية تمتدّ بعدها لقياس النتيجة) — يقصر
    الحساب فيصير مسح السوق كامل ضمن الجدوى.
    كل صفقة تحمل **fwd_max_gain** (أقصى صعود أمامي) و**max_draw_pct** (أعمق ذيل) و
    **exploded** (صعد ≥EXPLOSION_PCT = «انفجر فعلًا»).

    🔬 **تجربة الوقف الزوجية** (طلب المستخدم 2026-07-05): كل صفقة تُقيَّم بذراعين على
    **نفس البيانات**: `outcome`/`ret_a` = الوقف الحالي (لمسة ذيل: `low ≤ stop`) ·
    `outcome_b`/`ret_b` = الوقف بـ**إغلاق** تحت الوقف (صمود على مسح السيولة، الخروج
    عند إغلاق الكسر = تكلفة صادقة أعمق). العائد المحقّق يُقاس بسعر الخروج الفعلي لكل
    ذراع (t1 للرابح · الوقف/الإغلاق للخاسر · آخر إغلاق للعالق) — للمقارنة الصادقة."""
    trades = []
    n = len(df)
    fwd = int(CONFIG["BACKTEST_FORWARD_DAYS"])
    step = int(CONFIG["BACKTEST_STEP"])
    expl_thr = CONFIG["EXPLOSION_PCT"]
    lo_d, hi_d = (date_window or (None, None))
    i = int(CONFIG["MIN_BARS"])
    while i < n - fwd:
        if date_window is not None:      # قصر نقاط الدخول على النافذة (وضع السوق)
            try:
                d_iso = df.index[i - 1].date().isoformat()
            except Exception:
                d_iso = None
            if d_iso is None or (lo_d and d_iso < lo_d) or (hi_d and d_iso > hi_d):
                i += step
                continue
        try:
            r = analyze_ticker(sym, df.iloc[:i])
        except Exception:
            r = None
        if not r:
            if reasons is not None:
                _rr = _REJECT_REASONS.get(sym, "؟")
                reasons[_rr] = reasons.get(_rr, 0) + 1
            i += step
            continue
        # 🕰️ بوابة point-in-time (splits من اللقطة المجمَّدة): ارفض «الإشارة الوهمية» —
        # سعرها الحقيقي وقت الإشارة تحت أرضية M1 لكن تعديل تقسيم لاحق (yfinance يعدّله دائمًا)
        # رفعه فوقها. بلا splits = سلوك اليوم حرفيًا (لا بوابة). باكتيست فقط.
        if splits is not None and _pit_raw_price(
                r.get("price") or r["tranches"][-1], splits,
                df.index[i - 1]) < CONFIG["MIN_PRICE"]:
            if reasons is not None:
                reasons["M1_phantom_split"] = reasons.get("M1_phantom_split", 0) + 1
            i += step
            continue
        entry = sum(r["tranches"]) / len(r["tranches"])   # متوسط الدفعات
        stop, t1 = r["stop"][0], r["t1"]
        fut = df.iloc[i:i + fwd]
        hi = fut["High"].values.astype(float)
        lo = fut["Low"].values.astype(float)
        cl = fut["Close"].values.astype(float)
        op = fut["Open"].values.astype(float)
        filled = next((k for k in range(len(fut)) if lo[k] <= entry), None)
        fwd_max = max_draw = 0.0
        if filled is not None and entry > 0:
            fwd_max = (float(max(hi[filled:])) / entry - 1.0) * 100.0
            max_draw = (float(min(lo[filled:])) / entry - 1.0) * 100.0
        # الأساس: ذراعا الوقف (لمسة ذيل A · إغلاق B) بمصدر واحد _resolve_arm — بلا
        # تغيير سلوك (نفس المنطق السابق حرفيًا، DRY فقط لتقيس تجربة المسح بنفس المحرّك).
        _spread = CONFIG.get("BT_SPREAD_PCT", 0.0) or 0.0   # 🔬 F-COST
        outcome, ret_a, outcome_b, ret_b = _resolve_arm(
            hi, lo, cl, op, entry, stop, t1, filled, spread=_spread)
        # 🔬 F-L1: قياس أثر «تفاؤل شمعة التعبئة» — السلوك القديم (t1 من شمعة التعبئة)
        # محفوظ للمقارنة بتشغيل واحد؛ تقرير الباكتيست يطبع «كم فوزًا كان وهميًا».
        # (نفس السبريد ليُعزَل أثر شمعة التعبئة وحده عن تكلفة التنفيذ.)
        _lg_out, _lg_ret, _, _ = _resolve_arm(
            hi, lo, cl, op, entry, stop, t1, filled, entry_intrabar=False,
            spread=_spread)
        trade = {"symbol": sym, "date": str(df.index[i - 1].date()),
                 "outcome_legacy": _lg_out,
                 "ret_legacy": (round(_lg_ret, 1) if _lg_ret is not None else None),
                 "entry": round(entry, 2), "stop": round(stop, 2),
                 "t1": round(t1, 2), "outcome": outcome,
                 "outcome_b": outcome_b,
                 "ret_a": (round(ret_a, 1) if ret_a is not None else None),
                 "ret_b": (round(ret_b, 1) if ret_b is not None else None),
                 "tier": r.get("tier"),
                 # 🔬 تشخيص تصنيف A/B (T2): عدد النواقص + الجاهزية لكل صفقة — لاختبار
                 # «هل قلّة النواقص/عُلوّ الجاهزية تميّز النجاح؟» (كل الصفقات B لأن A=صفر
                 # نواقص مستحيل). تحليل فقط، لا يمسّ الفرز.
                 "n_soft": len(r.get("soft_fails") or []),
                 "readiness": r.get("readiness"),
                 # 🧬 درجة بصمة «طريقة الارتفاع» عند لحظة الإشارة (df حتى i، خلفي = لا
                 # تسريب) — لاختبار: هل البصمة العالية ترتبط بالانفجار الفعلي؟ (تحقّق قبل
                 # منحها وزن ترتيب). تُحسب على الإشارة فقط (~عشرات المرّات) = رخيصة.
                 "behav_score": behavior_rise_profile(df.iloc[:i]).get("score"),
                 "fwd_max_gain": round(fwd_max, 1),
                 "max_draw_pct": round(max_draw, 1),
                 # 🔬 Phase E3 (نظام السوق/خارج الشموع): متغيّرات سياقية متاحة في نتيجة
                 # analyze_ticker (بلا جلب إضافي) لاختبار «هل عمق الانهيار/حجم الانفجار
                 # السابق/العائد-المخاطرة يميّز المنفجر؟». تصدير/باكتيست فقط.
                 "drop_pct": (round(r["drop_pct"], 1) if r.get("drop_pct") is not None else None),
                 "best_spike": (round(r["best_spike"], 0) if r.get("best_spike") is not None else None),
                 "rr": r.get("rr"),
                 "exploded": bool(filled is not None and fwd_max >= expl_thr)}
        # 🔬 Phase E1: سمات 4س نقطة-زمنية عند الإشارة (يجلب 1h حيًّا، بطيء) — للمُعبَّئين فقط
        # (توفيرًا) خلف BT_DUMP_4H. المفتاح الأول h4_bars = التغطية التاريخية (مجهولة للمايكروكاب).
        if CONFIG.get("BT_DUMP_4H") and filled is not None:
            _h4 = h4_features_at(sym, df.index[i - 1])
            if _h4:
                trade.update(_h4)
                trade["h4_status"] = "ok"
            else:
                # 🔬 P0-S5: غياب 4س صريح (لا حذف صامت) — لفحص non-random missingness (تدقيق Codex).
                trade["h4_status"] = "no_1h_data"
        # 🕰️ H_PRICE_2_5 (فرضية مسجَّلة مسبقًا): السعر الحقيقي point-in-time للدخول =
        # المعدَّل × عامل التقسيم اللاحق (yfinance يعدّل دائمًا). لاختبار شريحة $2-5 على
        # اللقطة المجمَّدة بلا تلوّث تقسيم (السعر المخزَّن `entry` معدَّل). بلا splits
        # (تشغيل حيّ/غير مجمَّد) = الحقل غائب = صفقة الأساس بت-بت. تصدير/باكتيست فقط.
        if splits is not None:
            trade["raw_pit_entry"] = round(
                _pit_raw_price(trade["entry"], splits, df.index[i - 1]), 4)
        # 🔬 P0 (تدقيق المصدر): مخطط provenance للصف — خلف BT_DUMP_DATASET فقط (صفر أثر على
        # صفقة الأساس أو CSV القياسي). يمكّن: نافذة النتيجة لتطبيق embargo (forward_window_end) +
        # تتبّع دقيق للسعر الحقيقي/عامل التقسيم + سبب صريح لأي «تصحيح» (split_lookup_status).
        # كله مشتقّ من المحسوب سلفًا (لا جلب · لا نظر مستقبلي · df.index[i-1] = شمعة الإشارة).
        if CONFIG.get("BT_DUMP_DATASET"):
            _sig_date = df.index[i - 1]
            _sig_price = r.get("price") or r["tranches"][-1]
            _spf = _pit_split_factor(splits, _sig_date) if splits is not None else 1.0
            trade["forward_window_start"] = str(fut.index[0].date()) if len(fut) else ""
            trade["forward_window_end"] = str(fut.index[-1].date()) if len(fut) else ""
            trade["outcome_complete"] = bool(len(fut) >= fwd)
            trade["signal_price_raw_pit"] = round(_pit_raw_price(_sig_price, splits, _sig_date), 6)
            trade["entry_adjusted_exact"] = entry
            trade["raw_pit_entry_exact"] = _pit_raw_price(entry, splits, _sig_date)
            trade["post_signal_split_factor"] = _spf
            # 🔬 P0-3 (تدقيق Codex): افصل «رمز مجمَّد بلا أحداث تقسيم» (معروف) عن «لا بيانات
            # تقسيم أصلًا» (تشغيل حيّ). `frozen` يُمرَّر من run_backtest = bool(BT_FROZEN_PATH).
            trade["split_lookup_status"] = (
                ("frozen_no_split_events" if frozen else "no_frozen_splits") if splits is None
                else "no_post_signal_split" if _spf == 1.0 else "corrected")
        # 🔬 تجربة «الدخول المؤكَّد بالمسح» (BT_SWEEP_ENTRY، باكتيست حصريًا): على نفس
        # الإشارة نموذج دخول بديل (مسح+استعادة)، مقاسًا بنفس _resolve_arm. الدخول منفصل
        # عن الوقف (BT_SWEEP_STOP) لعزل أثر الدخول. المقارنة على المُعبَّأة في
        # backtest_sweep_compare. مطفأة افتراضيًا = صفقة الأساس بلا تغيير (صفر أثر).
        if CONFIG.get("BT_SWEEP_ENTRY"):
            _sweep_augment(trade, r, hi, lo, cl, op, stop, t1)
        # 🏦 قوة البوت (BT_POTENTIAL): أقصى صعود من الدخول **قبل الوقف** + يوم الذروة.
        # إلحاق فقط (كنمط المسح) — صفقة الأساس بلا تغيير. مطفأ = صفر حقول.
        if CONFIG.get("BT_POTENTIAL"):
            _mgo, _mgg, _mgd = _max_gain_before_stop(hi, lo, op, entry, stop, filled)
            trade["mg_outcome"] = _mgo
            trade["mg_pre_stop"] = _mgg
            trade["mg_peak_day"] = _mgd
        # 🏦 محاكاة الانتقائية (BT_PORTFOLIO): خزّن `score` (المحور الثاني لترتيب المحفظة
        # بعد readiness المخزَّن أصلًا) — إلحاق فقط، مطفأ = صفقة الأساس بت-بت.
        if CONFIG.get("BT_PORTFOLIO"):
            trade["score"] = r.get("score")
        trades.append(trade)
        i += fwd                                # تخطَّ نافذة كاملة (لا تكرار)
    return trades


def backtest_stats(trades: list) -> dict:
    """يجمّع نتائج الباكتيست: عدد الصفقات المحسومة ونسبة النجاح."""
    decided = [t for t in trades if t["outcome"] in ("win", "loss")]
    wins = [t for t in decided if t["outcome"] == "win"]
    nofill = [t for t in trades if t["outcome"] == "no_fill"]
    open_ = [t for t in trades if t["outcome"] == "open"]
    wr = (len(wins) / len(decided) * 100.0) if decided else 0.0
    return {"signals": len(trades), "decided": len(decided),
            "wins": len(wins), "losses": len(decided) - len(wins),
            "win_rate": round(wr, 1), "no_fill": len(nofill),
            "open": len(open_)}   # عُبّئت لكن لم تُحسم (شفافية: خارج النسبة/العائد)


def _bt_realized(t):
    """العائد المحقَّق% لصفقة باكتيست محسومة: الرابح يخرج عند t1 · الخاسر عند الوقف
    (الباكتيست يقيس t1 قبل الوقف = خروج فعلي لا «لمس=فوز» غامض). None لو نقص حقل."""
    try:
        e = float(t["entry"])
        if e <= 0:
            return None
        px = float(t["t1"]) if t["outcome"] == "win" else float(t["stop"])
        return (px / e - 1.0) * 100.0
    except (TypeError, ValueError, KeyError):
        return None


def _bt_realized_r(t):
    """العائد بوحدة المخاطرة (R): الرابح=(t1−دخول)/(دخول−وقف) · الخاسر=−1."""
    try:
        e, s = float(t["entry"]), float(t["stop"])
        risk = e - s
        if risk <= 0:
            return None
        return (float(t["t1"]) - e) / risk if t["outcome"] == "win" else -1.0
    except (TypeError, ValueError, KeyError):
        return None


def backtest_honest_summary(trades: list) -> list:
    """📊 المقاييس الصادقة للباكتيست (اقتباس مُكيَّف من dev_backtest_toolkit.honest_summary
    على منهجية فيصل): لا تكتفِ بنسبة النجاح (تخدع على عيّنة صغيرة) — أضِف الوسيط +
    توقّع R + اعتماد الذيل + **فاصل ثقة Wilson** (إشارة أم ضجيج؟) + **الأشهر الموجبة**
    (صلابة زمنية). باكتيست فقط — طبقة تحليل، لا تمسّ الفرز. أسطر عربية بلا علامات مقارنة."""
    decided = [t for t in trades if t["outcome"] in ("win", "loss")]
    n = len(decided)
    if n < 3:
        return []
    wins = [t for t in decided if t["outcome"] == "win"]
    w = len(wins)
    rets = sorted(x for x in (_bt_realized(t) for t in decided) if x is not None)
    rs = [x for x in (_bt_realized_r(t) for t in decided) if x is not None]
    out = ["\n📊 <b>مقاييس صادقة للباكتيست</b>"]
    # شفافية (مراجعة خصومية): الصفقات «العالقة» (عُبّئت ولم تلمس هدفًا ولا وقفًا خلال
    # النافذة) خارج النسبة والعائد أدناه — نُفصح عن عددها فلا تُقرأ النسبة كأنها الكل.
    open_n = sum(1 for t in trades if t.get("outcome") == "open")
    if open_n:
        out.append(f"   ℹ️ {open_n} صفقة عُبّئت ولم تُحسم بعد (خارج النسبة والعائد "
                   "أدناه — المقاييس على المحسومة فقط).")
    if rets:
        mean = sum(rets) / len(rets)
        med = _median(rets)
        out.append(f"   العائد المحقّق: المتوسط {mean:+.0f}% · الوسيط {med:+.0f}%")
        if mean - med >= 3:
            out.append("   ↳ المتوسط أعلى من الوسيط — الحافة يحملها قليل من الصفقات.")
    if rs:
        exp_r = sum(rs) / len(rs)
        out.append(f"   توقّع الصفقة الواحدة: {exp_r:+.1f}R (الهدف مقابل الوقف)")
    lo, hi = _wilson_ci(w, n)
    span = "واسع = عيّنة صغيرة/ضجيج" if hi - lo >= 30 else "ضيّق نسبيًا"
    out.append(f"   نسبة النجاح {w / n * 100:.0f}% · فاصل الثقة 95%: من {lo:.0f}% "
               f"إلى {hi:.0f}% ({span})")
    # اعتماد الذيل على الرابحين (العائد المحقّق) مقارنًا بخط أساس التساوي k/W
    wr_rets = sorted((x for x in (_bt_realized(t) for t in wins) if x is not None),
                     reverse=True)
    if len(wr_rets) >= 5 and sum(wr_rets) > 0:
        share = sum(wr_rets[:2]) / sum(wr_rets) * 100.0
        base = 2.0 / len(wr_rets) * 100.0
        tag = " — حافة هشّة" if share - base >= 25 else " — حافة عريضة"
        out.append(f"   اعتماد الذيل: أعلى صفقتين تصنعان {share:.0f}% من الربح "
                   f"(لو توزّع بالتساوي {base:.0f}%){tag}")
    # الأشهر الموجبة (صلابة زمنية) — شهر «موجب» إذا مجموع عائده المحقّق أكبر من صفر
    by_month = {}
    for t in decided:
        m = str(t.get("date", ""))[:7]
        rv = _bt_realized(t)
        if m and rv is not None:
            by_month.setdefault(m, []).append(rv)
    big = {m: v for m, v in by_month.items() if len(v) >= 3}
    if len(big) >= 2:
        pos = sum(1 for v in big.values() if sum(v) > 0)
        out.append(f"   الأشهر الموجبة: {pos} من {len(big)} (صلابة زمنية)")
    return out


def backtest_variant_compare(trades: list) -> list:
    """🔬 التجربة الزوجية الصارمة (طلب المستخدم 2026-07-05، «نقلة نوعية»): الوقف
    الحالي (لمسة ذيل) مقابل الوقف بالإغلاق (صمود على مسح السيولة) على **نفس الصفقات**.
    المقياس الحاسم = **العائد المحقّق الفعلي** لا الربح/الخسارة الثنائي (الصمود يلتقط
    انفجارات لكنه يعمّق بعض الخسائر — الصدق أن نقيس الصافي الزوجي B−A). باكتيست فقط.
    ملاحظة رياضية: B يوقف على مجموعة **جزئية** من شموع A (إغلاق≤وقف يستلزم ذيل≤وقف)،
    فكل خسارة B أعمق-أو-تساوي خسارة A المقابلة، وبعض خسائر A تصير أرباح B (الإنقاذ).
    فالفرق الزوجي يلتقط المقايضة كاملةً بدقّة."""
    fill = [t for t in trades
            if t.get("ret_a") is not None and t.get("ret_b") is not None]
    if len(fill) < 5:
        return []

    n = len(fill)

    def _arm(oc, rk):
        # **مقام موحّد لكلا الذراعين = كل المعبّأة** (مراجعة خصومية): B يوقف أقل فتصير
        # بعض خسائر A «عالق» عند B وتخرج من مقامه، فتبدو نسبة نجاح B أعلى بنيويًا مهما
        # كانت جدارته. نحسب على نفس المقام n ونُظهر العالق صراحةً — والحاسم مع ذلك هو
        # الفرق الزوجي بالعائد المحقّق لا نسبة النجاح.
        rets = [t[rk] for t in fill]
        cap = sum(1 for t in fill if t.get("exploded") and t[oc] == "win")
        return {"win": sum(1 for t in fill if t[oc] == "win"),
                "loss": sum(1 for t in fill if t[oc] == "loss"),
                "open": sum(1 for t in fill if t[oc] == "open"),
                "mean": sum(rets) / n, "med": _median(rets), "cap": cap}

    A = _arm("outcome", "ret_a")
    B = _arm("outcome_b", "ret_b")
    diffs = [t["ret_b"] - t["ret_a"] for t in fill]
    mean_diff = sum(diffs) / n
    med_diff = _median(diffs)
    recovered = [t for t in fill
                 if t["outcome"] == "loss" and t["outcome_b"] == "win"]
    deeper = [t for t in fill
              if t["outcome_b"] == "loss" and t["ret_b"] < t["ret_a"] - 0.5]
    exp_total = sum(1 for t in fill if t.get("exploded"))
    out = ["\n🔬 <b>تجربة الوقف الزوجية: لمسة الذيل (A) مقابل الإغلاق (B)</b>",
           f"   العيّنة: {n} صفقة معبّأة (نفسها ونفس المقام للذراعين)",
           # 🎯 المقياس الحاسم أولًا (صادق، نفس المقام، غير قابل للتحيّز البنيوي):
           f"   🎯 <b>العائد المحقّق (الحاسم): A متوسط {A['mean']:+.1f}% · B متوسط "
           f"{B['mean']:+.1f}% → الفرق الزوجي B−A = {mean_diff:+.1f} نقطة/صفقة "
           f"(وسيط الفرق {med_diff:+.1f})</b>",
           f"   A: ربح {A['win']} · وقف {A['loss']} · عالق {A['open']} · انفجارات "
           f"{A['cap']}/{exp_total}",
           f"   B: ربح {B['win']} · وقف {B['loss']} · عالق {B['open']} · انفجارات "
           f"{B['cap']}/{exp_total}",
           "   ⚠️ لا تُخدع بنسبة نجاح B الأعلى — بعض خسائر A تصير «عالق» عند B فترفعها "
           "بنيويًا؛ الحاسم هو الفرق الزوجي بالعائد المحقّق أعلاه.",
           f"   انفجارات أنقذها الإغلاق (وقف→ربح): {len(recovered)} · "
           f"خسائر عمّقها الإغلاق: {len(deeper)}"]
    if recovered:
        out.append("   الأسهم المُنقَذة: " + " · ".join(
            f"{esc(str(t['symbol']))} +{t.get('fwd_max_gain', 0):.0f}%"
            for t in sorted(recovered, key=lambda x: -x.get("fwd_max_gain", 0))[:8]))
    # 📋 معيار مسجَّل مسبقًا (لا p-hacking): الحكم على الفرق الزوجي بالعائد المحقّق
    verdict = ("مبدئيًا لصالح B (فرق زوجي موجب + إنقاذ يفوق التعميق)"
               if (mean_diff > 0 and len(recovered) >= len(deeper))
               else "مبدئيًا لا يتبنّى (التعميق يأكل المكسب أو الفرق غير موجب)")
    out.append(f"   📋 المعيار المسجَّل: يُعتمد B فقط لو (الفرق الزوجي بالعائد المحقّق "
               f"موجب بوضوح + يصمد عبر السنتين) → الحكم الأولي: <b>{verdict}</b> "
               "(قرارك بالأرقام لا آليًا)")
    return out


def _mean_lo95(xs):
    """المتوسط + الحدّ السفلي لفاصل الثقة 95% (تقريب طبيعي) + العدد. للحكم على الفرق
    الزوجي: نطلب الحدّ السفلي > 0 (لا مجرد المتوسط) فلا نُخدع بضجيج عيّنة صغيرة."""
    n = len(xs)
    if n == 0:
        return (0.0, 0.0, 0)
    m = sum(xs) / n
    if n < 2:
        return (m, m, n)
    var = sum((x - m) ** 2 for x in xs) / (n - 1)
    se = (var ** 0.5) / (n ** 0.5)
    return (m, m - 1.96 * se, n)


def backtest_sweep_compare(trades: list) -> list:
    """🔬 تجربة «الدخول المؤكَّد بالمسح» (T1، طلب المستخدم 2026-07-05 + صور فيصل: «قبل
    يصعد لازم مسح سيولة تحت القاع ثم استعادة · لا تدخل الدعم الأول»). نموذج دخول بديل
    (مسح+استعادة) مقابل التعبئة الفورية على **نفس الإشارة**. مطفأة ما لم يُفعَّل
    BT_SWEEP_ENTRY → ترجّع [] فلا تمسّ التقرير العادي. باكتيست حصريًا.

    🛡️ تحرس فخّين كشفتهما المراجعة الخصومية (7 وكلاء):
    - **فخّ عدم-التعبئة:** تحويل خسائر إلى عدم-تعبئة يزيّف «حافة». فالحكم الحاسم على
      **المُعبَّأة في الطرفين فقط** (بما أننا دخلنا كلانا، أيّهما أفضل؟) + تفكيك كامل
      يفصل «التفادي» (امتناع) عن «التحويل» (رافعة دخول حقيقية) ويشترط التحويل ≥ التفادي.
    - **خلط الدخول بالوقف:** الوقف الأعمق فشل حيًّا؛ فالدخول معزول (BT_SWEEP_STOP=0)
      فأيّ حافة تُنسب للدخول وحده لا لتعميق الوقف."""
    sw = [t for t in trades if t.get("entry_model") == "sweep_confirmed"]
    if not sw:
        return []

    def _bf(t):     # عبّأ الأساس؟
        return t.get("ret_a") is not None

    def _sf(t):     # عبّأ المسح؟
        return t.get("ret_sweep_a") is not None

    n_sig = len(sw)
    n_bf = sum(1 for t in sw if _bf(t))
    n_sf = sum(1 for t in sw if _sf(t))
    # أسباب عدم تعبئة المسح (شفافية — قد يكون «التحسّن» مجرّد امتناع)
    reasons = {}
    for t in sw:
        if not _sf(t):
            reasons[t.get("fill_reason_sweep", "?")] = \
                reasons.get(t.get("fill_reason_sweep", "?"), 0) + 1
    stop_iso = "الوقف=الأساس (عزل الدخول)" if not CONFIG.get("BT_SWEEP_STOP") \
        else "الوقف=تحت الذيل (دخول+وقف معًا)"
    out = ["\n🔬 <b>تجربة الدخول المؤكَّد بالمسح (T1): مسح+استعادة مقابل التعبئة الفورية</b>",
           f"   إعداد: عمق المسح {CONFIG['BT_SWEEP_PCT']*100:.0f}% · {stop_iso}",
           f"   الإشارات: {n_sig} · عبّأ الأساس: {n_bf} · عبّأ المسح: {n_sf}"
           + (f" ({n_sf / n_bf * 100:.0f}% من تعبئات الأساس)" if n_bf else "")]
    if reasons:
        out.append("   لم يعبّئ المسح بسبب: " + " · ".join(
            f"{k}={v}" for k, v in sorted(reasons.items(), key=lambda x: -x[1])))
    # 🎯 الحكم الحاسم: المُعبَّأة في الطرفين (يستبعد رصيد الامتناع تمامًا)
    both = [t for t in sw if _bf(t) and _sf(t)]
    da = [t["ret_sweep_a"] - t["ret_a"] for t in both]
    db = [t["ret_sweep_b"] - t["ret_b"] for t in both
          if t.get("ret_b") is not None and t.get("ret_sweep_b") is not None]
    ma, la, na = _mean_lo95(da)
    mb, lb, nb = _mean_lo95(db)
    if na:
        out.append(f"   🎯 <b>المُعبَّأة في الطرفين ({na}) — الفرق الزوجي (مسح−أساس): "
                   f"ذراع A {ma:+.1f} نقطة (حدّ ثقة سفلي {la:+.1f}) · "
                   f"ذراع B {mb:+.1f} (سفلي {lb:+.1f})</b>")
    else:
        out.append("   ⚠️ لا صفقة عبّأها الطرفان — لا حكم على الدخول (امتناع صافٍ).")
    # 🧩 تفكيك كامل (يفصل التفادي عن التحويل): br/sr = العائد المحقّق (0 = خارج السوق)
    av_sum = cv_sum = deep_sum = cost_sum = 0.0
    av_n = cv_n = deep_n = cost_n = 0
    for t in sw:
        bo, so = t.get("outcome"), t.get("outcome_sweep")
        br = t["ret_a"] if _bf(t) else 0.0
        sr = t["ret_sweep_a"] if _sf(t) else 0.0
        d = sr - br
        if bo == "loss" and not _sf(t):            # تفادٍ (امتناع): خسارة أساس → لا دخول
            av_sum += d; av_n += 1
        elif bo == "loss" and so == "win":         # تحويل: خسارة أساس → ربح مسح (الرافعة)
            cv_sum += d; cv_n += 1
        elif bo == "loss" and _sf(t):              # خسارة أساس بقيت خسارة/عالق بالمسح
            deep_sum += d; deep_n += 1
        elif bo == "win" and so != "win":          # كلفة: ربح أساس ضاع
            cost_sum += d; cost_n += 1
    out.append(f"   🧩 التفكيك: تفادٍ(امتناع) {av_n}={av_sum:+.0f} · "
               f"تحويل(دخول→ربح) {cv_n}={cv_sum:+.0f} · "
               f"خسارة-تبقى {deep_n}={deep_sum:+.0f} · كلفة(ربح ضاع) {cost_n}={cost_sum:+.0f}")
    # 📅 يصمد عبر السنوات؟ (الفرق الزوجي للمُعبَّأة في الطرفين لكل سنة)
    by_year = {}
    for t in both:
        y = str(t.get("date", ""))[:4]
        by_year.setdefault(y, []).append(t["ret_sweep_a"] - t["ret_a"])
    yr_line = " · ".join(f"{y}: {sum(v) / len(v):+.1f}({len(v)})"
                         for y, v in sorted(by_year.items()))
    if yr_line:
        out.append(f"   📅 بالسنة (فرق A): {yr_line}")
    # 📋 معيار مسجَّل مسبقًا (افتراض الرفض + قفل، أسلوب C3) — كل الأرجل معًا:
    yrs_ok = [y for y, v in by_year.items() if len(v) >= 3]
    year_pass = bool(yrs_ok) and all(sum(by_year[y]) > 0 for y in yrs_ok)
    fill_ok = n_bf and (n_sf / n_bf) >= 0.40
    passed = (na >= 5 and la > 0 and mb > 0 and cv_sum >= av_sum
              and cv_sum > 0 and fill_ok and year_pass)
    verdict = ("مبدئيًا يتبنّى الدخول (فرق موجب بحدّ ثقة + تحويل يفوق التفادي + "
               "تعبئة كافية + يصمد بالسنوات)" if passed else
               "مبدئيًا يُرفض ويُقفل (فرق غير حاسم / الحافة من الامتناع لا التحويل / "
               "تعبئة ضعيفة / لا يصمد بالسنوات)")
    out.append("   📋 المعيار المسجَّل (قبل التشغيل): يُعتمد الدخول فقط لو — فرق A "
               "المُعبَّأة حدّه السفلي فوق صفر + ذراع B موجب + التحويل ≥ التفادي + "
               "تعبئة المسح ≥ 40% + موجب كل سنة. أي رِجل تسقط ⇒ رفض. "
               f"→ الحكم الأولي: <b>{verdict}</b> (قرارك بالأرقام لا آليًا).")
    return out


def backtest_tier_analysis(trades: list) -> list:
    """🔬 تشخيص تصنيف A/B (T2 — طلب المستخدم: «التصنيف عشوائي ولا سهم وصل A»). فئة A
    تتطلّب **صفر نواقص** عبر ~8-10 بوابات = مستحيل (0 من كل الصفقات). هذا يختبر **بالدليل**:
    هل عدد النواقص (أو الجاهزية) يميّز النجاح/الانفجار فعلًا؟ لو نعم → «A = ناقص واحد أو
    أقل» يعيد التمييز؛ لو لا → التصنيف بعدد النواقص ضجيج، والتمييز يجي من غيره (سلوك/جاهزية).
    تحليل فقط — لا يمسّ الفرز/التصنيف/الجذور."""
    dec = [t for t in trades if t.get("outcome") in ("win", "loss")
           and t.get("n_soft") is not None]
    if len(dec) < 10:
        return []

    def _bucket(sel):
        d = [t for t in sel if t["outcome"] in ("win", "loss")]
        if not d:
            return None
        w = sum(1 for t in d if t["outcome"] == "win")
        f = [t for t in sel if t.get("outcome") != "no_fill"]
        exp = sum(1 for t in f if t.get("exploded"))
        lo, hi = _wilson_ci(w, len(d))
        return (len(d), w / len(d) * 100.0, exp, len(f), lo, hi)

    zero = sum(1 for t in dec if t["n_soft"] == 0)
    out = ["\n🔬 <b>تشخيص التصنيف A/B (هل عدد النواقص يميّز النجاح؟)</b>",
           f"   محسومة: {len(dec)} · منها «صفر نواقص»(=A): <b>{zero}</b> "
           "(تأكيد: A مستحيل عمليًا)"]
    # شرائح عدد النواقص
    sb = []
    for lbl, a, b in [("0-1 نقص", 0, 1), ("2 نقص", 2, 2),
                      ("3 نقص", 3, 3), ("4 فأكثر", 4, 99)]:
        r = _bucket([t for t in dec if a <= t["n_soft"] <= b])
        if r:
            sb.append((lbl, r))
            out.append(f"   {lbl}: {r[0]} صفقة · نجاح {r[1]:.0f}% "
                       f"(ثقة {r[4]:.0f}-{r[5]:.0f}%) · انفجر {r[2]}/{r[3]}")
    # حكم تمييز النواقص: أقلّها مقابل أكثرها + هل فاصلا الثقة منفصلان
    soft_disc = False
    if len(sb) >= 2:
        best, worst = sb[0][1], sb[-1][1]
        gap = best[1] - worst[1]
        sep = best[4] > worst[5]                       # lo(الأقل) فوق hi(الأكثر)
        soft_disc = gap >= 15 and sep
        out.append(f"   📊 الفرق (أقل نواقص − أكثر): {gap:+.0f} نقطة · فاصلان "
                   f"{'منفصلان' if sep else 'متداخلان'} → عدد النواقص "
                   f"{'<b>يميّز</b>' if soft_disc else '<b>لا يميّز بوضوح</b>'}")
    # شرائح الجاهزية (قد تميّز حتى لو النواقص لا — بديل جذري للتصنيف)
    rb = []
    for lbl, a, b in [("جاهزية أقل من 50", 0, 49), ("50-64", 50, 64),
                      ("65 فأكثر", 65, 200)]:
        r = _bucket([t for t in dec if t.get("readiness") is not None
                     and a <= t["readiness"] <= b])
        if r:
            rb.append((lbl, r))
    if rb:
        out.append("   — بالجاهزية —")
        for lbl, r in rb:
            out.append(f"   {lbl}: {r[0]} · نجاح {r[1]:.0f}% "
                       f"(ثقة {r[4]:.0f}-{r[5]:.0f}%) · انفجر {r[2]}/{r[3]}")
    rdy_disc = False
    if len(rb) >= 2:
        g = rb[-1][1][1] - rb[0][1][1]
        rdy_disc = g >= 15 and rb[-1][1][4] > rb[0][1][5]
    # التوصية المبنية على الدليل (لا اجتهاد)
    if soft_disc:
        rec = "عدّل التصنيف: A = «ناقص واحد أو أقل» (النواقص تميّز فعلًا)"
    elif rdy_disc:
        rec = ("عدّل التصنيف: A بعتبة **جاهزية** لا بعدد النواقص (الجاهزية تميّز، "
               "النواقص لا) — حلّ جذري يعيد A حيّة")
    else:
        rec = ("لا النواقص ولا الجاهزية تميّز بوضوح → التصنيف الثنائي الحالي **ضجيج**؛ "
               "الحلّ الجذري = استبدال A/B بمحور مُثبَت (سلوك المضارب/الترتيب) لا بوابة صفرية")
    out.append(f"   ✅ <b>التوصية بالدليل: {rec}</b>")
    return out


def backtest_behav_correlation(trades: list) -> list:
    """🧬 تحقّق ارتباط بصمة «طريقة الارتفاع» بالانفجار (طلب المستخدم: امنحها وزنًا في
    الترتيب **فقط بعد** إثبات أن الدرجة العالية ترتبط بالانفجار فعلًا، بلا تسريب —
    البصمة تُحسب على df حتى لحظة الإشارة). يبوّب المعبّأة بشرائح البصمة → معدل الانفجار
    + النجاح + فاصل Wilson، ثم يحكم: هل يرتفع الانفجار مع الدرجة (فرق واضح + فاصلان
    منفصلان)؟ **تحليل فقط — لا يمسّ الترتيب؛ البصمة تبقى عرضًا حتى يثبت هذا.**"""
    fb = [t for t in trades if t.get("behav_score") is not None
          and t.get("outcome") != "no_fill"]
    if len(fb) < 12:
        return []
    out = ["\n🧬 <b>تحقّق البصمة: هل «طريقة الارتفاع» ترتبط بالانفجار؟</b>"]
    rows = []
    for lbl, a, b in [("بصمة أقل من 35", 0, 34), ("35-59", 35, 59),
                      ("60 فأكثر", 60, 200)]:
        sel = [t for t in fb if a <= t["behav_score"] <= b]
        if not sel:
            continue
        exp = sum(1 for t in sel if t.get("exploded"))
        dec = [t for t in sel if t["outcome"] in ("win", "loss")]
        w = sum(1 for t in dec if t["outcome"] == "win")
        elo, ehi = _wilson_ci(exp, len(sel))
        wr = (w / len(dec) * 100.0) if dec else 0.0
        rows.append((exp / len(sel) * 100.0, elo, ehi))
        out.append(f"   {lbl}: {len(sel)} معبّأة · انفجر {exp} "
                   f"({exp / len(sel) * 100:.0f}%، ثقة {elo:.0f}-{ehi:.0f}%) · "
                   f"نجاح {wr:.0f}%")
    disc = False
    if len(rows) >= 2:
        gap = rows[-1][0] - rows[0][0]                 # فرق معدل الانفجار أعلى-أدنى
        sep = rows[-1][1] > rows[0][2]                 # فاصلا الانفجار منفصلان
        disc = gap >= 10 and sep
        out.append(f"   📊 فرق الانفجار (أعلى بصمة − أدنى): {gap:+.0f}% · فاصلان "
                   f"{'منفصلان' if sep else 'متداخلان'}")
    rec = ("<b>تُمنح وزن ترتيب</b> (داخل المختارين بعد القصّ فقط): البصمة العالية "
           "ترتبط بالانفجار فعلًا" if disc else
           "<b>تبقى عرضًا فقط</b>: لا ارتباط واضح بعد — لا تُمنح وزنًا (تجنّب الضجيج)")
    out.append(f"   ✅ التوصية بالدليل: {rec}")
    return out


_ACC_COMPS = [("aggressive_buy_pct", "الشراء العدواني"),
              ("block_share_pct", "الطبعات الكبيرة"),
              ("block_buy_pct", "شراء الطبعات الكبيرة (T-ACC-2)"),
              ("dark_share_pct", "الدارك بول")]


def acc_verify_report(signals: list) -> list:
    """🔬 حكم تجربة T-ACC (POLYGON_EDGE_PLAN §أ-4، بلا تسريب — كل مكوّن يُحسب من
    صفقات ما قبل الإشارة حصريًا). لكل مكوّن تجميع: يبوّب الإشارات المعبّأة لثلاثة
    أثلاث (أدنى/أوسط/أعلى) → معدل الانفجار + فاصل Wilson، ثم يحكم بالمعيار **المسجّل
    مسبقًا** (لا يتغيّر بعد النتائج): فرق الانفجار (الأعلى − الأدنى) ≥ 10 نقاط **و**
    فاصلا Wilson منفصلان (لهذه السنة) — ويُعتمد نهائيًا **فقط لو صمد في السنتين**.
    **تحليل/تحقّق فقط — لا يمنح وزن ترتيب تلقائيًا** (قرار المستخدم بالأرقام)."""
    fb = [s for s in signals if s.get("outcome") != "no_fill"]
    out = [f"\n🔬 <b>تحقّق التجميع الصامت (T-ACC) — {len(fb)} إشارة معبّأة</b>"]
    if len(fb) < 12:
        out.append("   عيّنة غير كافية (أقل من 12) — شغّل سنة كاملة.")
        return out
    for key, label in _ACC_COMPS:
        vals = sorted(s[key] for s in fb if s.get(key) is not None)
        if len(vals) < 12:
            out.append(f"   {label}: عيّنة غير كافية.")
            continue
        q1, q2 = vals[len(vals) // 3], vals[2 * len(vals) // 3]
        buckets = [("الأدنى", lambda v: v <= q1),
                   ("الأوسط", lambda v: q1 < v <= q2),
                   ("الأعلى", lambda v: v > q2)]
        rates = []
        out.append(f"   <b>{label}:</b>")
        for blbl, cond in buckets:
            sel = [s for s in fb if s.get(key) is not None and cond(s[key])]
            if not sel:
                continue
            exp = sum(1 for s in sel if s.get("exploded"))
            elo, ehi = _wilson_ci(exp, len(sel))
            rates.append((exp / len(sel) * 100.0, elo, ehi))
            out.append(f"     {blbl}: {len(sel)} · انفجر {exp} "
                       f"({exp / len(sel) * 100:.0f}%، ثقة {elo:.0f}-{ehi:.0f}%)")
        if len(rates) >= 2:
            gap = rates[-1][0] - rates[0][0]
            sep = rates[-1][1] > rates[0][2]
            disc = gap >= 10 and sep
            out.append(f"     📊 فرق الانفجار (الأعلى − الأدنى): {gap:+.0f}% · "
                       f"فاصلان {'منفصلان' if sep else 'متداخلان'} → "
                       + ("<b>مرشّح للاعتماد</b> (لو صمد بالسنة الأخرى)" if disc
                          else "<b>يبقى عرضًا</b>"))
    out.append("   📋 المعيار المسجَّل: يُعتمد المكوّن **فقط** لو (فرق ≥10 نقاط + "
               "فاصلان منفصلان) **وصمد في 2025 و2026** — وقتها يُمنح وزن ترتيب "
               "بموافقتك (لا آليًا).")
    return out


def _normalize_bt_period(month, year):
    """🧭 يصحّح خانتَي «الشهر»/«السنة» للباكتيست قبل بناء النافذة (طلب/التباس متكرّر
    للمستخدم، أُصلح 2026-07-05): كتب «2025» في خانة **الشهر** بدل السنة والسنة فارغة →
    البوت بنى نافذة مشوّهة «2025-2025-01..2025-2025-31» فسقطت كل التواريخ خارجها = **صفر
    إشارة بلا سطر فترة**. القواعد:
      (1) رقم يشبه سنة (4 خانات، 2000 فأكثر) في «الشهر» والسنة فارغة → المقصود **السنة
          كاملة**: يُنقل الرقم لخانة السنة، والشهر يُفرَّغ (فيمرّ على مسار «السنة كاملة»).
      (2) أي شهر يبقى بعدها **غير صالح** (ليس 1-12) → يُفرَّغ (لا نبني نافذة مشوّهة؛
          يسقط على المنتقي التلقائي/كل التاريخ).
    يرجّع (شهر، سنة) نظيفَين كنصوص. باكتيست فقط — طبقة إدخال، لا تمسّ الفرز."""
    month = str(month or "").strip()
    year = str(year or "").strip()
    if (month.isdigit() and len(month) == 4 and int(month) >= 2000 and not year):
        year, month = month, ""             # سنة كُتبت بخانة الشهر → انقلها للسنة
    if month and not (month.isdigit() and 1 <= int(month) <= 12):
        month = ""                          # شهر غير صالح (ليس 1-12 وليس سنة) → أهمِله
    return month, year


def _bt_year_of(m, year=None):
    """السنة المستهدفة للشهر m: صريحة (year) إن مُرّرت، وإلا **أحدث ظهور** (الحالية
    إن مضى/جارٍ الشهر وإلا السابقة). طلب المستخدم 2026-07-05: تحديد سنة (مثلًا 2025)."""
    if year:
        try:
            return int(year)
        except (TypeError, ValueError):
            pass
    today = dt.date.today()
    return today.year if int(m) <= today.month else today.year - 1


def _filter_trades_by_month(trades, month, year=None):
    """يقصر صفقات الباكتيست على **شهر تقويمي** (1-12) من سنة محدّدة (year) أو **أحدث
    سنة متوفّرة** (طلب المستخدم 2026-07-04/07-05: الشهر + السنة). يرجّع (الصفقات، وسم
    الفترة أو None). باكتيست فقط — طبقة تحليل، لا تمسّ الفرز."""
    try:
        m = int(str(month).strip())
    except (TypeError, ValueError):
        return trades, None
    if not 1 <= m <= 12:
        return trades, None
    y_want = None
    if year:
        try:
            y_want = str(int(year))
        except (TypeError, ValueError):
            y_want = None

    def _ym(t):
        d = str(t.get("date", ""))
        return (d[:4], d[5:7]) if len(d) >= 7 else (None, None)

    mm = f"{m:02d}"
    in_month = [t for t in trades if _ym(t)[1] == mm]
    if y_want:
        in_month = [t for t in in_month if _ym(t)[0] == y_want]
    if not in_month:
        tag = f"{y_want}-{mm}" if y_want else f"شهر {mm}"
        return [], f"{tag} (لا صفقات بالبيانات)"
    yr = y_want or max(y for y, _ in map(_ym, in_month) if y)
    return [t for t in in_month if _ym(t)[0] == yr], f"{yr}-{mm}"


def _recent_month_window(m, year=None):
    """نافذة (من، إلى) ISO للشهر m من سنة محدّدة أو أحدث ظهور — لقصر مسح السوق الكامل
    على شهر واحد (الجدوى). الحدّ الأعلى «..-31» يعمل بمقارنة النصوص (يشمل كل الأيام).
    يرفع ValueError لشهر خارج 1-12 (دفاع عميق: يُلتقط بالمستدعي → نافذة None بدل مشوّهة)."""
    m = int(m)
    if not 1 <= m <= 12:
        raise ValueError(f"شهر خارج النطاق 1-12: {m}")
    y = _bt_year_of(m, year)
    return (f"{y}-{m:02d}-01", f"{y}-{m:02d}-31")


def _forward_window_complete(m, year=None):
    """هل للشهر m (من سنة محدّدة أو أحدث ظهور) نافذة أمامية كافية (BACKTEST_FORWARD_DAYS
    جلسة) قبل اليوم؟ (مراجعة خصومية 2026-07-04: شهر حديث نافذته ناقصة فيُستبعَد كل دخوله
    بحارس `i < n-fwd` → تقرير فارغ.) سنة سابقة = مكتملة دومًا. ~1.5 يوم تقويمي لكل جلسة."""
    try:
        m = int(m)
    except (TypeError, ValueError):
        return True
    y = _bt_year_of(m, year)
    nxt = dt.date(y + (m == 12), (m % 12) + 1, 1)     # أول الشهر التالي = نهاية الشهر
    return (dt.date.today() - nxt).days >= int(CONFIG["BACKTEST_FORWARD_DAYS"] * 1.5)


def _diagnose_symbol(sym, df, cutoff=0):
    """تشخيص دقيق (باكتيست فقط، طلب المستخدم 2026-07-04): يطبع الأرقام الخام لكل
    بوابة هوية + الحكم النهائي — للإجابة بدقة على «ليش لم يُرشَّح هذا السهم؟».
    لا يمسّ الفرز (يستدعي نفس analyze_ticker).

    ⏪ **cutoff** (طلب المستخدم 2026-07-04): يقيّم السهم كأنه **قبل `cutoff` يوم تداول**
    (يقصّ آخر `cutoff` شمعة) — أي «كيف رآه البوت وقت القاع قبل الانفجار» لا بعده.
    cutoff=0 = الحالة الحالية. هذا هو التقييم بلا-نظر-للمستقبل عند لحظة تاريخية محددة."""
    try:
        d = df.iloc[:len(df) - cutoff] if cutoff > 0 else df
        if len(d) < CONFIG["MIN_BARS"]:
            log(f"🔬{sym}@-{cutoff}ي: بيانات غير كافية عند هذا القصّ ({len(d)} شمعة)")
            return
        tag = f"{sym}@-{cutoff}ي" if cutoff > 0 else sym
        try:
            asof = str(d.index[-1].date())
        except Exception:
            asof = "?"
        close, high, low, vol = d["Close"], d["High"], d["Low"], d["Volume"]
        c = close.values.astype(float)
        price = float(c[-1])
        hi52 = float(high.tail(252).max())
        drop = (1.0 - price / hi52) * 100.0 if hi52 > 0 else 0.0
        best_spike, n_sp = spike_info(c, exclude_last=CONFIG["BASE_WINDOW"])
        bw = CONFIG["BASE_WINDOW"]
        base_hi, base_lo = float(high.tail(bw).max()), float(low.tail(bw).min())
        base_range = (base_hi / base_lo - 1.0) * 100.0 if base_lo > 0 else -1.0
        dvol = float((close * vol).tail(20).mean())
        rs = rsi(close)
        rsi_min = float(rs.tail(CONFIG["RSI_OS_LOOKBACK"]).min())
        rsi_now = float(rs.iloc[-1])
        gain5 = (c[-1] / c[-6] - 1.0) * 100.0 if len(c) > 6 and c[-6] > 0 else 0.0
        log(f"🔬{tag} خام(بتاريخ {asof}): سعر={price:.2f} هبوط={drop:.0f}%"
            f" انفجار={best_spike:.0f}%(معيد×{n_sp}) قاعدة={base_range:.0f}%"
            f" سيولة=${dvol:,.0f} RSIقاع={rsi_min:.0f}/الآن={rsi_now:.0f}"
            f" صعود5ج={gain5:+.0f}% شموع={len(c)}")
        r = analyze_ticker(sym, d)
        rej = _REJECT_REASONS.get(sym, "—")
        rp = analyze_ticker(sym, d, pullback=True)
        if r:
            log(f"🔬{tag} حكم: ✅ مرشّح درجة={r['score']} فئة={r['tier']}"
                f" جاهزية={r.get('readiness')} نواقص={r.get('soft_fails')}")
        else:
            log(f"🔬{tag} حكم: ❌ مرفوض بـ«{rej}» · مسار الارتداد="
                f"{'✅ يُقبل' if rp else '❌ يُرفض'}")
    except Exception as e:
        log(f"🔬{sym}@-{cutoff} تشخيص: خطأ {type(e).__name__}: {e}")


def _default_backtest_symbols() -> list:
    """كون افتراضي للباكتيست عند عدم تحديد رموز (طلب المستخدم 2026-07-04: «التشغيل
    بالشهر فقط بلا تعبئة الرموز»): اتحاد رموز القائمة الحالية + الأرشيف + سجل
    التنبيهات = **كون البوت المعروف**. باكتيست فقط — طبقة تحليل، لا تمسّ الفرز.
    ⚠️ انحياز اختيار: هذه رموز رشّحها البوت أصلًا، فالنسبة عليها متفائلة (التقرير
    يحذّر). للحُكم الحقيقي مرّر عيّنة واسعة."""
    syms = set()
    try:
        wl = load_watchlist()
        buckets = list(wl.get("history") or [])
        buckets.append({"stocks": (wl.get("stocks") or []) + (wl.get("removed") or [])})
        for wk in buckets:
            for s in wk.get("stocks", []):
                if s.get("symbol"):
                    syms.add(str(s["symbol"]).upper())
    except Exception as e:
        log(f"⚠️ باكتيست·كون القائمة: {e}")
    try:
        ad = load_alerts()
        for a in (ad.get("alerts") if isinstance(ad, dict) else ad) or []:
            if a.get("symbol"):
                syms.add(str(a["symbol"]).upper())
    except Exception as e:
        log(f"⚠️ باكتيست·كون التنبيهات: {e}")
    return sorted(syms)


def run_backtest(symbols=None) -> None:
    """يشغّل الباكتيست على قائمة رموز (env BACKTEST_SYMBOLS أو وسيط) ويرسل
    تقريرًا + CSV. عند عدم تحديد رموز → **كون البوت الافتراضي** (القائمة + التنبيهات)
    فيكفي تحديد الشهر وحده. **تنبيه انحياز الناجين:** لو جرّبت رموز رابحة معروفة فقط
    تطلع النسبة متضخّمة — للحُكم الحقيقي جرّب عيّنة عشوائية واسعة من السوق."""
    if symbols is None:
        env = os.environ.get("BACKTEST_SYMBOLS", "").strip()
        symbols = [s.strip().upper() for s in env.replace(";", ",").split(",")
                   if s.strip()]
    _raw_month = os.environ.get("BACKTEST_MONTH", "").strip()
    _bt_month, _bt_year = _normalize_bt_period(
        _raw_month, os.environ.get("BACKTEST_YEAR", ""))   # سنة محدّدة (2025 مثلًا)
    if _raw_month and _raw_month != _bt_month:   # التُقط خلط الخانتين → أبلغ بالسجل
        if _bt_year == _raw_month:
            log(f"🧭 باكتيست: «{_raw_month}» كُتب بخانة الشهر ويشبه سنة والسنة فارغة "
                f"→ فُسِّر كـ«السنة {_raw_month} كاملة» (أُفرِّغت خانة الشهر).")
        else:
            log(f"⚠️ باكتيست: «{_raw_month}» ليس شهرًا صالحًا (1-12) → أُهمِلت خانة الشهر.")
    date_window = None
    whole_year = False
    _month_valid = _bt_month.isdigit() and 1 <= int(_bt_month) <= 12
    # 🌍 **لا رموز محدّدة → مسح السوق الكامل** (طلب المستخدم: يكفي تحديد الشهر، بلا
    # خانة ثانية). رموز صريحة → تلك فقط. السوق مقصور على شهر/سنة للجدوى + بلا انحياز.
    market = not symbols
    if market:
        uni = get_universe()
        if uni:
            symbols = uni
            log(f"باكتيست·السوق الكامل: {len(symbols)} رمز ناسداك (بلا انحياز اختيار)")
        else:      # تعذّر جلب ناسداك (شبكة) → كون البوت الاحتياطي بدل الفشل الكامل
            symbols = _default_backtest_symbols()
            log(f"⚠️ باكتيست·السوق: تعذّر جلب ناسداك → كون البوت الاحتياطي "
                f"({len(symbols)} رمز)")
        if _bt_year and not _month_valid:
            # 📆 **سنة كاملة بتشغيل واحد** (طلب المستخدم: 2025 كاملة، شهر فارغ = كل الأشهر).
            whole_year = True
            _yv = int(_bt_year)
            date_window = (f"{_yv}-01-01", f"{_yv}-12-31")
            log(f"باكتيست·السوق: السنة {_yv} كاملة (كل الأشهر بتشغيل واحد)")
            if _yv >= dt.date.today().year:   # صدق: أشهر السنة الجارية الأخيرة نافذتها ناقصة
                log(f"⚠️ باكتيست·السوق: {_yv} سنة جارية — آخر ~شهرين نافذتهما الأمامية "
                    "ناقصة فتقلّ صفقاتهما. للسنة الكاملة اختر سنة مكتملة (2025).")
        else:
            if not _bt_month:
                # أحدث شهر **نافذته الأمامية مكتملة** (لا «آخر شهر مكتمل» — بياناته
                # الأمامية ناقصة فيُفرَّغ التقرير، عيب لقّته المراجعة الخصومية).
                _base = dt.date.today().replace(day=1)
                for _ in range(24):
                    _base = (_base - dt.timedelta(days=1)).replace(day=1)
                    if _forward_window_complete(_base.month):
                        break
                _bt_month = str(_base.month)
                log(f"باكتيست·السوق: بلا شهر → أحدث شهر نافذته الأمامية مكتملة "
                    f"({_base.year}-{_base.month:02d}؛ يحتاج ~{CONFIG['BACKTEST_FORWARD_DAYS']}ج بعده)")
            try:
                date_window = _recent_month_window(int(_bt_month), _bt_year)
            except (TypeError, ValueError):
                date_window = None
            if not _forward_window_complete(_bt_month, _bt_year):
                log(f"⚠️ باكتيست·السوق: الفترة حديثة — نافذتها الأمامية "
                    f"(~{CONFIG['BACKTEST_FORWARD_DAYS']}ج) غير مكتملة، فقد تقلّ/تنعدم "
                    "الصفقات المحسومة. اختر شهرًا/سنة أقدم لنتيجة كاملة.")
    if not symbols:
        log("⚠️ باكتيست: تعذّر تحديد رموز (لا ناسداك ولا كون احتياطي)")
        send_telegram("🧪 الباكتيست: تعذّر تحديد رموز (لا ناسداك ولا كون احتياطي).")
        return
    log(f"باكتيست {len(symbols)} رمز…"
        + (f" · نافذة {date_window[0]}..{date_window[1]}" if date_window else ""))
    # 🕰️ تجميد point-in-time (تدقيق خارجي): لو BT_FROZEN_PATH لملف لقطة موجود → حمّل منه
    # (قابل لإعادة الإنتاج 100% + splits لبوابة الوهميات) بدل التحميل الحيّ المتغيّر.
    splits_map = None
    _frozen_meta = None
    _asof = None
    _frozen_path = os.environ.get("BT_FROZEN_PATH", "").strip()
    # 🕰️ P0 (تدقيق المصدر): حارس صريح **يقوّي فقط**. BT_FROZEN_STRICT=1 يعلن «لا تشغّل حيًّا
    # كأنه مجمَّد». لو رُفع بلا مسار لقطة → misconfig يُفشل الـjob بدل تحميل حيّ صامت. لا يُضعف
    # أبدًا: حين BT_FROZEN_PATH مُعطى فالتحميل صارم أصلًا (strict=True أدناه) بصرف النظر عنه.
    _frozen_strict = os.environ.get("BT_FROZEN_STRICT", "").strip() == "1"
    if _frozen_strict and not _frozen_path:
        raise SystemExit("BT_FROZEN_STRICT=1 لكن BT_FROZEN_PATH فارغ — أرفض التشغيل الحيّ كأنه مجمَّد")
    if _frozen_path:
        # 🕰️ P0 (تدقيق المصدر): الوضع الصارم — إن طُلبت لقطة، أي فشل تحقّق يُفشل الـjob
        # (SystemExit) **بلا أي تحميل حيّ بديل**. كان يرجع بصمت لتحميل حيّ = تشغيل «مجمَّد»
        # يتحوّل حيًّا دون علم. بنية/باكتيست فقط.
        if not os.path.exists(_frozen_path):
            raise SystemExit(f"Frozen dataset requested but file missing: {_frozen_path}")
        hist, splits_map, _asof, _frozen_meta = load_frozen_dataset(_frozen_path, strict=True)
        if not hist:
            raise SystemExit("Frozen dataset requested but validation failed")
        symbols = list(hist.keys())
        log(f"🕰️ تجميد: حُمِّلت لقطة point-in-time ({len(hist)} رمز · as-of {_asof}) "
            "— قابلة لإعادة الإنتاج + بوابة الوهميات مفعّلة")
    else:
        hist = download_history(symbols)
    all_trades = []
    for sym in symbols:
        df = hist.get(sym)
        if df is None or df.empty:
            if not market:
                log(f"🔬{sym}: لا بيانات (محذوف/رمز خطأ؟)")
            continue
        if not market:      # التشخيص المفصّل (8 قصّات/رمز) لعيّنة صغيرة فقط — لا للسوق
            _diagnose_symbol(sym, df)     # تشخيص الحالة الحالية (دائمًا)
            # ⏪ تشخيص «قبل الانفجار»: نقيّم السهم كأنه قبل N يوم — وقت القاع قبل الركض.
            for off in (15, 20, 25, 30, 40, 50, 60):
                _diagnose_symbol(sym, df, cutoff=off)
        if len(df) < CONFIG["MIN_BARS"] + CONFIG["BACKTEST_FORWARD_DAYS"]:
            if not market:
                log(f"باكتيست·{sym}: بيانات غير كافية للمشي ({len(df)} شمعة)")
            continue
        sym_reasons = {}
        all_trades += backtest_symbol(sym, df, sym_reasons, date_window=date_window,
                                      splits=(splits_map or {}).get(sym),
                                      frozen=bool(_frozen_path))
        if sym_reasons and not market:   # تشخيص: أكثر بوابة رفضت هذا السهم تاريخيًا
            top = sorted(sym_reasons.items(), key=lambda x: -x[1])[:3]
            log(f"باكتيست·أسباب {sym}: "
                + " · ".join(f"{k}={v}" for k, v in top))
    # 📅 قصر على شهر تقويمي محدّد (طلب المستخدم): BACKTEST_MONTH=1..12 → إشارات ذلك
    # الشهر فقط (آخر سنة متوفّرة). فارغ = كل التاريخ. باكتيست فقط، لا يمسّ الفرز.
    period_tag = None
    if whole_year:
        _yv = str(int(_bt_year))
        all_trades = [t for t in all_trades if str(t.get("date", ""))[:4] == _yv]
        period_tag = f"{_yv} (كل السنة)"
        log(f"باكتيست: قصر على السنة {period_tag} ({len(all_trades)} صفقة)")
    elif _bt_month:
        all_trades, period_tag = _filter_trades_by_month(all_trades, _bt_month, _bt_year)
        log(f"باكتيست: قصر على {period_tag} ({len(all_trades)} صفقة)")
    st = backtest_stats(all_trades)
    # تشخيص للسجل: تفاصيل كل إشارة (سقف 200 سطر في وضع السوق تفاديًا لتضخّم السجل).
    for t in all_trades[:(200 if market else len(all_trades))]:
        log(f"باكتيست·{t['symbol']}: {t['date']} → {t['outcome']} "
            f"(دخول {t['entry']} · هدف {t['t1']} · وقف {t['stop']})")
    # B1: هوية التجربة — تظهر برسالة التلقرام + اللوق (لمقارنة تشغيلات A/B)
    settings = (f"إعدادات: M4 قاعدة {CONFIG['BASE_RANGE_MAX_PCT']:g}% · "
                f"M2 أرضية {CONFIG['MIN_DROP_FLOOR']:g}%"
                + (" (تجربة: " + " · ".join(_BT_OVERRIDES) + ")"
                   if _BT_OVERRIDES else " (القيم الأصلية)"))
    log(f"باكتيست — {settings} | إشارات={st['signals']} "
        f"محسومة={st['decided']} نجاح={st['win_rate']:.0f}% "
        f"({st['wins']}✅/{st['losses']}🛑) غير_مُعبّأة={st['no_fill']}")
    head0 = ("🌍 <b>باكتيست السوق الكامل (بلا انحياز اختيار)</b>" if market
             else "🧪 <b>باكتيست تاريخي (مشي للأمام، بلا نظر للمستقبل)</b>")
    lines = [head0, settings]
    if period_tag:
        lines.append(f"📅 <b>الفترة: {period_tag}</b>"
                     + (" (السوق كامل)" if market else " (شهر محدّد)"))
    lines += [f"رموز: {len(symbols)} · إشارات: {st['signals']} · "
              f"غير مُعبّأة: {st['no_fill']} · عالقة (لم تُحسم): {st['open']}",
             f"صفقات محسومة: <b>{st['decided']}</b> · "
             f"نجاح: <b>{st['win_rate']:.0f}%</b> "
             f"({st['wins']}✅ / {st['losses']}🛑)"]
    # 🔬 F-L1: قياس «تفاؤل شمعة التعبئة» بتشغيل واحد — النجاح القديم (t1 يُحسم على
    # شمعة التعبئة) مقابل المحافظ الآن. الفرق = كم فوزًا كان وهميًا.
    _lg_wins = sum(1 for t in all_trades if t.get("outcome_legacy") == "win")
    _lg_dec = sum(1 for t in all_trades
                  if t.get("outcome_legacy") in ("win", "loss"))
    if _lg_dec:
        _lg_wr = _lg_wins / _lg_dec * 100.0
        lines.append(f"🔬 F-L1: النجاح القديم (تفاؤل شمعة التعبئة) {_lg_wr:.0f}% → "
                     f"المحافظ {st['win_rate']:.0f}% (تضخّم {_lg_wr - st['win_rate']:+.0f} نقطة)")
    _spread_v = CONFIG.get("BT_SPREAD_PCT", 0.0) or 0.0
    if _spread_v:
        lines.append(f"🔬 F-COST: العوائد بعد تكلفة تنفيذ {_spread_v * 100:.0f}% "
                     "(سبريد+انزلاق، نصفها كل جهة)")
    # 🕰️ point-in-time (BT_RAW_PRICE): أسعار خام بلا تعديل تقسيم مستقبلي — تُرفَض الإشارات
    # الوهمية (سعرها الحقيقي تحت أرضية M1). تشخيص: صفقات بصعود شاذّ (>300%) قد تحمل تقسيمًا
    # داخل النافذة (نادر) فتُعرَض للفحص لا تُخفى.
    if CONFIG.get("BT_RAW_PRICE"):
        _raw_susp = [t for t in all_trades if (t.get("fwd_max_gain") or 0) > 300]
        lines.append("🕰️ <b>point-in-time (أسعار خام، بلا تعديل تقسيم مستقبلي)</b>"
                     + (f" · ⚠️ {len(_raw_susp)} صفقة صعودها >300% (افحص تقسيمًا داخل النافذة): "
                        + " · ".join(esc(str(t["symbol"])) for t in _raw_susp[:8])
                        if _raw_susp else " · لا صعود شاذّ (>300%)"))
    # 💥 «اللي انفجر فعلًا واللي لا» (طلب المستخدم): من الارتكازات التي رشّحها البوت
    # وعُبّئت، كم صعد ≥EXPLOSION_PCT بعد الدخول. يجيب السؤال مباشرة (مقياس فيصل ≥50%).
    filled = [t for t in all_trades if t.get("outcome") != "no_fill"]
    exploded = [t for t in all_trades if t.get("exploded")]
    if filled:
        pct = len(exploded) / len(filled) * 100.0
        lines.append(f"\n💥 <b>انفجر فعلًا (صعد {int(CONFIG['EXPLOSION_PCT'])}% أو "
                     f"أكثر بعد الدخول): {len(exploded)} من {len(filled)} "
                     f"({pct:.0f}%)</b>")
        top_expl = sorted(exploded, key=lambda t: -t.get("fwd_max_gain", 0))[:8]
        if top_expl:
            lines.append("   أقوى الانفجارات: " + " · ".join(
                f"{esc(str(t['symbol']))} +{t.get('fwd_max_gain', 0):.0f}%"
                for t in top_expl))
        lines.append("   ↳ الباقي: ربح صغير (لمس t1) أو خسارة أو تحرّك محدود — "
                     "أي الارتكازات فجّرت فعلًا وأيها لا.")
    # 📊 المقاييس الصادقة (اقتباس dev_backtest_toolkit): وسيط + R + فاصل ثقة +
    # أشهر موجبة — تكشف إن كانت النسبة إشارة أم ضجيج/ذيل قِلّة.
    honest = backtest_honest_summary(all_trades)
    lines += honest
    for _hl in honest:
        log("باكتيست·" + _hl.strip().replace("\n", " "))
    # 🔬 التجربة الزوجية الصارمة (طلب المستخدم): الوقف الحالي مقابل وقف الإغلاق —
    # على نفس الصفقات، بالعائد المحقّق الفعلي (هل الصمود على مسح السيولة يحسّن الصافي؟)
    variant = backtest_variant_compare(all_trades)
    lines += variant
    for _vl in variant:
        log("باكتيست·" + _vl.strip().replace("\n", " "))
    # 🔬 تجربة الدخول المؤكَّد بالمسح (T1) — ترجع [] ما لم يُفعَّل BT_SWEEP_ENTRY
    sweep = backtest_sweep_compare(all_trades)
    lines += sweep
    for _sl in sweep:
        log("باكتيست·" + _sl.strip().replace("\n", " "))
    # 🔬 تشخيص التصنيف A/B (T2): هل النواقص/الجاهزية تميّز؟ (تحليل دائم، لا يمسّ الفرز)
    tier_diag = backtest_tier_analysis(all_trades)
    lines += tier_diag
    for _tl in tier_diag:
        log("باكتيست·" + _tl.strip().replace("\n", " "))
    # 🧬 تحقّق ارتباط البصمة بالانفجار (T0-تحقّق): قبل منح البصمة وزن ترتيب
    behav_diag = backtest_behav_correlation(all_trades)
    lines += behav_diag
    for _bl in behav_diag:
        log("باكتيست·" + _bl.strip().replace("\n", " "))
    # 🏦 قوة البوت (BT_POTENTIAL): الحركة المتاحة من الدخول قبل الوقف + الانتقائية
    # (المحفظة) — ترجع [] ما لم يُفعَّل BT_POTENTIAL (المحور الذي طلبه المستخدم).
    potential = backtest_potential_report(all_trades)
    lines += potential
    for _pl in potential:
        log("باكتيست·" + _pl.strip().replace("\n", " "))
    if st["decided"] < 20:
        lines.append("⏳ عيّنة صغيرة — وسّع الرموز لحُكم موثوق.")
    # 📋 معيار القرار المسجَّل مسبقًا (يمنع p-hacking) — التجربة الزوجية لا تناسب
    # تغيير البوابة (يغيّر مجموعة الصفقات)، فقارِن ذراعين مستقلّين بحذر بالفاصل.
    lines.append("📋 <b>معيار القرار المسجَّل مسبقًا</b>: عدّل بوابة فقط لو الفرق "
                 "واضح + فاصل الثقة لا يلمس صفر الفرق + عيّنة واسعة + يصمد عبر "
                 "الأشهر. لا تعصر متغيّرات حتى «يعدّي أحدها». تغيير البوابة يغيّر "
                 "الصفقات فلا يُقارَن زوجيًا — قارن ذراعين مستقلّين.")
    lines.append("⚠️ <i>انحياز الناجين: رموز رابحة معروفة فقط تضخّم النسبة. "
                 "للحقيقة استخدم عيّنة واسعة عشوائية. باكتيست ليس توصية.</i>")
    send_telegram("\n".join(lines))
    fn = _write_csv_file(all_trades, "backtest")
    if fn:
        send_telegram_document(fn, f"🧪 تفاصيل الباكتيست — {dt.date.today()}")
    # 🔬 Phase C: فرّغ صفوف المتغيّرات للـstdout بمعلَم ثابت (⟪DSROW⟫) لسحبها من سجل
    # Actions واختبارها OOS — المنافذ الخارجية (تنزيل الأرتيفاكت) محجوبة بسياسة الحوكمة.
    # تشخيص/باكتيست حصريًا · الإنتاج يتجاهله (قفل B1) · لا يمسّ أي حساب.
    if CONFIG.get("BT_DUMP_DATASET"):
        _dcols = ("symbol", "date", "outcome", "mg_outcome", "readiness",
                  "behav_score", "score", "fwd_max_gain", "mg_pre_stop",
                  "exploded", "entry", "raw_pit_entry",
                  # 🔬 Phase E3 (نظام السوق) + E1 (سمات 4س، فارغة إن لم يُفعَّل BT_DUMP_4H)
                  "drop_pct", "best_spike", "rr",
                  "h4_bars", "h4_reversal", "h4_rsi", "h4_status",
                  # 🔬 P0-5 (تدقيق Codex): provenance 4س لإعادة إنتاج السمة بت-بت.
                  "h4_asof", "h4_timezone", "h4_resample", "h4_1h_bars",
                  "h4_1h_first", "h4_1h_last", "h4_first_bar", "h4_last_bar", "h4_source",
                  # 🔬 P0 (تدقيق المصدر): provenance الصف — نافذة النتيجة (لتطبيق embargo) +
                  # السعر الحقيقي/عامل التقسيم الدقيق + حالة بحث التقسيم (سبب أي «تصحيح»).
                  "forward_window_start", "forward_window_end", "outcome_complete",
                  "signal_price_raw_pit", "entry_adjusted_exact", "raw_pit_entry_exact",
                  "post_signal_split_factor", "split_lookup_status")
        # ملاحظة: raw_pit_entry يُملأ فقط للرموز ذات تقسيمات باللقطة؛ لغيرها السعر
        # الحقيقي = entry المعدَّل نفسه (لا تقسيم لاحق) → التحليل: raw_pit_entry أو entry.
        # وh4_* فارغة ما لم يُفعَّل BT_DUMP_4H (توافق خلفي).
        # 🔬 P0-S6: سطر meta واحد ببصمة اللقطة + الإصدارات + عتبات الفرز + النافذة =
        # provenance كامل لإعادة إنتاج/تدقيق التفريغ من السجل (المنافذ الخارجية محجوبة).
        _snap_commit = (_frozen_meta or {}).get("source_commit")
        _ana_commit = os.environ.get("GITHUB_SHA", "").strip() or None
        _dsmeta = {
            "frozen_sha256": (_frozen_meta or {}).get("payload_sha256"),
            "asof": _asof,
            # 🔬 P0-4 (تدقيق Codex): افصل كوميت بناء اللقطة عن كوميت كود التحليل + أبلِغ التعارض
            # (كانا يُدمجان في قيمة واحدة فيتعذّر معرفة الاثنين معًا).
            "snapshot_source_commit": _snap_commit,
            "analysis_source_commit": _ana_commit,
            "commit_mismatch": bool(_snap_commit and _ana_commit and _snap_commit != _ana_commit),
            "source_commit": _snap_commit or _ana_commit,   # توافق خلفي (المفتاح القديم)
            "python_version": (_frozen_meta or {}).get("python_version"),
            "package_versions": ((_frozen_meta or {}).get("package_versions")
                                 or _package_versions()),
            "date_window": date_window,
            "forward_days": int(CONFIG["BACKTEST_FORWARD_DAYS"]),
            "min_price": CONFIG["MIN_PRICE"],
            "max_drop_pct": CONFIG["MAX_DROP_PCT"],
            "min_drop_floor": CONFIG["MIN_DROP_FLOOR"],
            "prior_spike_window": CONFIG["PRIOR_SPIKE_WINDOW"],
            "min_dollar_vol": CONFIG["MIN_DOLLAR_VOL"],
            "n_trades": len(all_trades),
            "schema_version": 2,
        }
        print("⟪DSMETA⟫" + json.dumps(_dsmeta, ensure_ascii=False, default=str), flush=True)
        print("⟪DSHEAD⟫" + ",".join(_dcols), flush=True)
        for _t in all_trades:
            # 🔬 comma-safe: نستبدل أي فاصلة داخل خليّة بـ«;» فلا تُزيح الأعمدة (h4_source يحوي
            # فواصل — كان يكسر محاذاة الصف عند السحب من السجل). DSMETA منفصل (JSON) فلا يُمَسّ.
            print("⟪DSROW⟫" + ",".join(
                "" if _t.get(_c) is None else str(_t.get(_c)).replace(",", ";") for _c in _dcols),
                flush=True)
        print(f"⟪DSEND⟫{len(all_trades)}", flush=True)
    log(f"باكتيست: {st}")


def run_freeze() -> None:
    """🕰️ يجمّد لقطة باكتيست point-in-time: يحمّل الكون مرة (OHLCV + التقسيمات معًا عبر
    actions=True) ويحفظها ببصمة SHA-256. تشغيل واحد → كل باكتيست لاحق بـ`BT_FROZEN_PATH`
    قابل لإعادة الإنتاج 100% (نفس البيانات نفس النتيجة) + يرفض الإشارات الوهمية. حلّ P0
    من التدقيق الخارجي (الباكتيست الحيّ يقفز 26↔44% لمجرد إعادة التشغيل). بنية/باكتيست فقط."""
    uni = get_universe() or _default_backtest_symbols()
    asof = dt.date.today().isoformat()
    start = (dt.date.today() - dt.timedelta(days=CONFIG["HISTORY_DAYS"])).isoformat()
    log(f"🕰️ تجميد: تحميل {len(uni)} رمز (OHLCV + تقسيمات) as-of {asof}…")
    hist, splits = {}, {}
    split_status = {}          # 🔬 P0-S2: حالة التقسيم لكل رمز (provenance المانفست)
    size = CONFIG["CHUNK_SIZE"]
    for k in range(0, len(uni), size):
        chunk = uni[k:k + size]
        try:
            data = yf.download(chunk, start=start, interval="1d", auto_adjust=True,
                               actions=True, group_by="ticker", threads=True,
                               progress=False)
        except Exception:
            data = None
        if data is not None:
            for sym in chunk:
                try:
                    df = (data[sym].copy() if len(chunk) > 1 else data.copy())
                    df = df.dropna(subset=["Close"])
                    if len(df) < CONFIG["MIN_BARS"]:
                        continue
                    hist[sym] = df[["Open", "High", "Low", "Close", "Volume"]]
                    _st = "none"
                    if "Stock Splits" in df.columns:
                        sp = df["Stock Splits"]
                        sp = sp[sp != 0]
                        if len(sp):
                            splits[sym] = sp
                            _st = ("reverse" if any(float(x) < 1.0 for x in sp.values)
                                   else "forward")
                    split_status[sym] = _st
                except Exception:
                    continue
        if (k // size) % 20 == 0:
            log(f"🕰️ تجميد: {len(hist)} رمز حتى الآن…")
        time.sleep(CONFIG["CHUNK_SLEEP"])
    # 🔬 P0-S2 (تدقيق المصدر): provenance اللقطة للمانفست v2 — حالة التقسيم لكل رمز + عدّها
    # + بصمة الكون + الرموز الفاشلة (طُلبت بالكون لكن لم تدخل hist: لا بيانات/أقل من MIN_BARS).
    import hashlib as _hl
    _counts = {}
    for _v in split_status.values():
        _counts[_v] = _counts.get(_v, 0) + 1
    extra_meta = {
        "split_status": split_status,
        "split_status_counts": _counts,
        "universe_n": len(uni),
        "universe_sha256": _hl.sha256(",".join(sorted(uni)).encode("utf-8")).hexdigest(),
        "failed_symbols": sorted(set(uni) - set(hist.keys())),
    }
    path = os.environ.get("BT_FREEZE_OUT", "frozen_backtest.pkl.gz")
    man = save_frozen_dataset(hist, splits, asof, path, extra_meta=extra_meta)
    log(f"🕰️ تجميد: حُفِظت لقطة {man['n_symbols']} رمز · {len(splits)} بتقسيمات · "
        f"SHA {man['sha256'][:12]} · {path}")
    send_telegram(
        f"🕰️ <b>تُجمّدت لقطة باكتيست point-in-time</b>\n"
        f"رموز: {man['n_symbols']} · بتقسيمات: {len(splits)} · as-of {asof}\n"
        f"SHA-256: <code>{man['sha256'][:16]}</code>\n"
        f"جاهزة لباكتيست قابل لإعادة الإنتاج (BT_FROZEN_PATH) + رفض الوهميات." + FOOTER)


def main():
    log(f"بدء الفحص — الوضع: {MODE}")
    if MODE == "FREEZE":              # 🕰️ تجميد لقطة point-in-time (تدقيق خارجي)
        run_freeze()
        log("انتهى التجميد ✅")
        return
    if MODE == "BACKTEST":
        run_backtest()
        log("انتهى الباكتيست ✅")
        return
    if MODE == "DIGEST":              # 🕵️ تحديث نهاية اليوم (مسار خفيف مستقل)
        run_hand_digest()
        return
    force = os.environ.get("FORCE_RENEW", "").strip() == "1"
    # 🔄 إشارة التجديد من الـworkflow: كرون الجمعة 22:00 UTC (بعد الإغلاق) فقط.
    renew_signal = os.environ.get("RENEW_ON_CLOSE", "").strip() == "1"
    wl = load_watchlist()
    if should_renew(wl, force, renew_signal):
        why = ("إجبار يدوي" if force else
               ("تجديد أسبوعي (الجمعة بعد إغلاق السوق)" if renew_signal
                else "تأسيس أول قائمة"))
        log(f"وضع اليوم: {why}")
        run_weekly_renewal(wl)
    else:
        log("وضع اليوم: متابعة يومية للقائمة الثابتة")
        run_daily_watchlist(wl)
    log("انتهى الفحص ✅")


# ==========================================================
# 11) نظام تتبع الأداء + الذاكرة الدائمة + التقرير الأسبوعي
# ==========================================================
TRACK_FILE = "alerts_history.json"   # ملف الذاكرة الدائمة في الـ repo
TRACK_EXPIRE_DAYS = 30               # نغلق تتبع السهم بعد 30 يوم
# التقرير الأسبوعي يُرسَل مع التجديد (الجمعة بعد الإغلاق) عبر
# run_performance_system(weekly_report_now=True) — لا حسب يوم الأسبوع.

STATUS_AR = {
    "hit_t1": "✅ حقق الهدف 1",
    "hit_t2": "✅✅ حقق الهدف 2",
    "hit_t3": "🏆 حقق الهدف 3",
    "stopped": "🛑 ضرب الستوب",
    "expired": "⌛ انتهى التتبع (30 يوم)",
}


def git_save(filenames, runner=None, sender=None):
    """يرفع ملفات البيانات إلى الـ repo حتى لا تضيع بين تشغيلات GitHub Actions.
    ⑬ (إصلاح تدقيق 2026-07-12): عند تعارض rebase كان `--abort` يعيد الحالة كما
    كانت فتفشل المحاولات الأربع **بمدخلات متطابقة** (حلقة ميتة ~30ث) ثم تضيع
    حالة التشغيلة بصمت مع الرنر المؤقت (جوب أخضر!). الآن التعارض يُحل فعليًا:
    نقرأ ملفاتنا للذاكرة → نعتمد الريموت (`reset --hard FETCH_HEAD`) → نعيد
    كتابة ملفاتنا فوقه ونعيد الكوميت (آخر-كاتب-يفوز **لملفاتنا فقط** = نفس دلالة
    نجاح الـrebase أصلًا؛ untracked لا يمسّها reset). والفشل النهائي يُبلَّغ
    **تلغرام** لا لوقًا فقط. `runner`/`sender` محقونان للاختبار بلا git/شبكة.
    ملاحظة معمارية: لم نُدرج ignition.yml في مجموعة `super-stocks-state` (اقتراح
    التقرير) — جوب الرادار 6 ساعات وسيحجز المراقب خلفه طوال الجلسة؛ هذا
    الاسترجاع يحل تعارضه بلا قتل التوازي المقصود."""
    run = runner or os.system
    try:
        run('git config user.email "bot@screener.local"')
        run('git config user.name "Screener Bot"')
        added = False
        for fn in filenames:
            if os.path.exists(fn):
                run(f'git add "{fn}"')
                added = True
        if not added:
            return
        if run("git diff --cached --quiet") == 0:
            log("ℹ️ لا تغييرات جديدة للحفظ")
            return
        _msg = f"bot data {dt.date.today().isoformat()}"
        run(f'git commit -m "{_msg}"')
        # دفع آمن ضد السباق (HEAD:main يضمن الدفع حتى بوضع detached).
        pushed = False
        for attempt in range(4):
            run("git fetch origin main >/dev/null 2>&1")
            if run("git rebase FETCH_HEAD >/dev/null 2>&1") != 0:
                run("git rebase --abort >/dev/null 2>&1")
                # ⑬ حل التعارض فعليًا: اعتمد الريموت ثم أعد ملفاتنا فوقه.
                try:
                    _blobs = {}
                    for fn in filenames:
                        if os.path.exists(fn):
                            with open(fn, "rb") as f:
                                _blobs[fn] = f.read()
                    run("git reset --hard FETCH_HEAD >/dev/null 2>&1")
                    for fn, _b in _blobs.items():
                        with open(fn, "wb") as f:
                            f.write(_b)
                        run(f'git add "{fn}"')
                    run(f'git commit -m "{_msg}"')
                    log("⚖️ تعارض rebase — اعتُمد الريموت وأُعيدت ملفاتنا فوقه")
                except Exception as e:
                    log(f"⚠️ استرجاع التعارض: {e}")
            if run("git push origin HEAD:main") == 0:
                pushed = True
                break
            wait = 2 ** (attempt + 1)
            log(f"⚠️ git push فشل (محاولة {attempt + 1}/4) — إعادة بعد {wait}ث")
            time.sleep(wait)
        if pushed:
            log("✅ حُفظت بيانات التتبع في الـ repo")
        else:
            log("⛔ git push فشل نهائيًا — البيانات محفوظة محليًا فقط. "
                "تأكّد من permissions: contents: write في الـ YML")
            # ⑬ فشل نهائي = حالة التشغيلة ستضيع مع الرنر — تنبيه واجب لا لوق.
            try:
                _snd = sender or send_telegram
                _snd("⛔ <b>فشل حفظ حالة البوت في GitHub</b> بعد 4 محاولات — "
                     "بيانات هذه التشغيلة (حسم/دِدوب) قد تضيع مع انتهاء الرنر. "
                     "تحقّق من سجلّ Actions." + "\n\n" + FOOTER)
            except Exception:
                pass
    except Exception as e:
        log(f"⚠️ git_save: {e}")


def load_alerts():
    if os.path.exists(TRACK_FILE):
        try:
            with open(TRACK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            log(f"⚠️ قراءة سجل التنبيهات: {e}")
    return {"alerts": []}


def save_alerts_file(data):
    try:
        _atomic_write_json(TRACK_FILE, data)
    except Exception as e:
        log(f"⚠️ حفظ سجل التنبيهات: {e}")


def record_new_alerts(data, results):
    """يضيف تنبيهات اليوم للسجل (يتجاهل سهماً ما زال تتبعه مفتوحاً)"""
    open_syms = {a["symbol"] for a in data["alerts"] if a["status"] == "open"}
    today = dt.date.today().isoformat()
    for r in results:
        if r["symbol"] in open_syms:
            continue
        data["alerts"].append({
            "symbol": r["symbol"], "date": today,
            # ① تاريخ شمعة الترشيح الفعلية — مرجع نافذة المتابعة (لا تاريخ التشغيل).
            "ref_bar": r.get("ref_bar"),
            "price": round(r["price"], 4),
            "stop": round(r["stop"][0], 4),   # الوقف الأبعد (~7% تحت القاع)
            "t1": round(r["t1"], 4),
            "t2": round(r["t2"], 4),
            "t3": round(r["t3"], 4),
            "score": r["score"],
            "flags": r["flags"],
            "ready": r["ready"],
            # A3 (خطة الضبط 2026-07-03): سمات التعلّم — كانت 7/10 من الصفقات
            # المحسومة بلا tier/rsi/float فتُحسب شرائح مساعد التطوير على 3 فقط.
            # كلها متاحة في r وقت الإنشاء (تتبّع فقط — لا يمسّ الفرز).
            "tier": r.get("tier"),
            "sector": r.get("sector"),
            "rsi": r.get("rsi"),
            "float": r.get("float"),
            "short": r.get("finra_short"),
            "short_pct": r.get("short_pct"),
            "drop_pct": r.get("drop_pct"),
            "best_spike": r.get("best_spike"),
            "rr": r.get("rr"),
            "status": "open",
            "result_date": None,
            "max_gain_pct": 0.0,
        })


def update_tracking(data):
    """يرجع قائمة بالتنبيهات التي تغيّرت حالتها اليوم"""
    updates = []
    open_alerts = [a for a in data["alerts"] if a["status"] == "open"]
    if not open_alerts or yf is None:
        return updates
    log(f"متابعة {len(open_alerts)} تنبيه مفتوح...")
    for a in open_alerts:
        try:
            # ① (إصلاح تدقيق 2026-07-12): مرجع النافذة = شمعة الترشيح (ref_bar) لا
            # تاريخ التشغيل — المسار اليومي يختم قبل الافتتاح فشمعة يوم التنبيه
            # تتكوّن بعده وكان `start = date+1` يُسقطها للأبد. ارتداد للسجلات
            # القديمة بلا ref_bar → date = سلوك اليوم حرفيًا.
            try:
                _ref = str(a.get("ref_bar") or a["date"])[:10]
                dt.date.fromisoformat(_ref)
            except Exception:
                _ref = a["date"]
            age = (dt.date.today() - dt.date.fromisoformat(_ref)).days
            # الشمعة المرجعية اليوم (أو بالمستقبل) — ما في جلسة جديدة بعدها
            # لمتابعتها؛ نتخطّاه (وإلا نطلب start=بكرة > end=اليوم = خطأ Yahoo).
            if age < 1:
                continue
            # نبدأ من اليوم التالي لشمعة الترشيح (لا التالي لتاريخ التشغيل)
            start = (dt.date.fromisoformat(_ref)
                     + dt.timedelta(days=1)).isoformat()
            df = yf.download(a["symbol"], start=start, interval="1d",
                             auto_adjust=True, progress=False)
            if df is None or df.empty:
                if age >= TRACK_EXPIRE_DAYS:
                    a["status"] = "expired"
                    a["result_date"] = dt.date.today().isoformat()
                    updates.append(a)
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna(subset=["Close"])
            highs = df["High"].astype(float).values
            lows = df["Low"].astype(float).values
            # ⚖️ F-02 (إصلاح تدقيق 2026-07-10): المستويات المخزّنة بمقياس يوم
            # التنبيه والسلسلة المعاد تحميلها معدَّلة بالتقسيم — تقسيم عكسي أثناء
            # التتبع كان يسجّل «hit_t3» زائفًا. نقسم المستويات على عامل التقسيم
            # منذ التنبيه (فاشل-آمن → 1.0 = السلوك السابق). التنبيهات لا يُعاد
            # حساب مستوياتها أبدًا فالعامل الخام يكفي (بلا مُختار تماسك).
            _spf = _split_scale_factor(_fetch_splits(a["symbol"]), a["date"])
            if _spf != 1.0:
                log(f"⚖️ {a['symbol']}: تقسيم بعد التنبيه (عامل {_spf:g}) — "
                    "تُسوَّى مستويات الحسم لمقياس اليوم")
            entry = float(a["price"]) / _spf
            _stop_c = float(a["stop"]) / _spf
            _t1_c = float(a["t1"]) / _spf
            _t2_c = float(a["t2"]) / _spf
            _t3_c = float(a["t3"]) / _spf
            if len(highs):
                a["max_gain_pct"] = round(
                    (float(np.max(highs)) / entry - 1.0) * 100.0, 1)

            best, status, when = 0, None, None
            for i in range(len(df)):
                day = str(df.index[i].date())
                # الستوب أولاً = افتراض محافظ
                # (إلا إذا حقق هدفاً قبله، فالصفقة رابحة أصلاً)
                if lows[i] <= _stop_c and best == 0:
                    status, when = "stopped", day
                    break
                if highs[i] >= _t3_c:
                    best, when = 3, day
                    break
                if highs[i] >= _t2_c and best < 2:
                    best, when = 2, day
                elif highs[i] >= _t1_c and best < 1:
                    best, when = 1, day
            if status is None and best > 0:
                status = f"hit_t{best}"
            if status is None and age >= TRACK_EXPIRE_DAYS:
                status, when = "expired", dt.date.today().isoformat()

            if status:
                a["status"], a["result_date"] = status, when
                updates.append(a)
        except Exception as e:
            log(f"⚠️ تتبع {a['symbol']}: {e}")
        time.sleep(0.4)
    return updates


def realized_pct(a):
    """نسبة الربح/الخسارة المحققة حسب الحالة النهائية"""
    e = float(a["price"])
    if a["status"] == "stopped":
        return (float(a["stop"]) / e - 1.0) * 100.0
    if a["status"].startswith("hit_t"):
        t = float(a[a["status"].replace("hit_", "")])  # t1 / t2 / t3
        return (t / e - 1.0) * 100.0
    return float(a.get("max_gain_pct") or 0.0)


def tracking_message(updates):
    lines = [f"📡 <b>متابعة التنبيهات السابقة</b> — "
             f"{dt.date.today().isoformat()}", ""]
    for a in updates:
        lines.append(f"• <b>{a['symbol']}</b> | سعر التنبيه "
                     f"${a['price']:.2f} يوم {a['date']}")
        if a["status"] == "expired":
            lines.append(f"  {STATUS_AR['expired']} — أقصى ارتفاع شافه: "
                         f"{a['max_gain_pct']:+.0f}%")
        else:
            pct = realized_pct(a)
            lines.append(f"  {STATUS_AR[a['status']]} يوم {a['result_date']} "
                         f"({pct:+.0f}%) | أقصى ارتفاع: "
                         f"{a['max_gain_pct']:+.0f}%")
    return "\n".join(lines)


def weekly_report(data):
    alerts = data["alerts"]
    if not alerts:
        return ""
    opens = [a for a in alerts if a["status"] == "open"]
    closed = [a for a in alerts if a["status"] != "open"]
    expired = [a for a in closed if a["status"] == "expired"]
    decided = [a for a in closed if a["status"] != "expired"]
    wins = [a for a in decided if a["status"].startswith("hit")]
    losses = [a for a in decided if a["status"] == "stopped"]

    lines = [f"📊 <b>تقرير الأداء الأسبوعي</b> — "
             f"{dt.date.today().isoformat()}", "",
             f"إجمالي التنبيهات: {len(alerts)} | مفتوحة: {len(opens)} | "
             f"منتهية بلا حسم: {len(expired)}"]

    if decided:
        wr = len(wins) / len(decided) * 100.0
        avg_w = (sum(realized_pct(a) for a in wins) / len(wins)) if wins else 0.0
        avg_l = (sum(realized_pct(a) for a in losses) / len(losses)) \
            if losses else 0.0
        lines += [
            f"✅ رابحة: {len(wins)} | 🛑 خاسرة: {len(losses)} | "
            f"نسبة النجاح: <b>{wr:.0f}%</b>",
            f"متوسط ربح الرابحة: {avg_w:+.0f}% | "
            f"متوسط خسارة الخاسرة: {avg_l:+.0f}%",
        ]
        # تحليل دقة كل إشارة (flag)
        stats = {}
        for a in decided:
            won = a["status"].startswith("hit")
            for f in a.get("flags", []):
                name = f.split("(")[0].strip()
                s = stats.setdefault(name, [0, 0])
                s[0] += 1
                if won:
                    s[1] += 1
        ranked = [(n, c[1] / c[0] * 100.0, c[0])
                  for n, c in stats.items() if c[0] >= 3]
        ranked.sort(key=lambda x: x[1], reverse=True)
        if ranked:
            lines += ["", "🧩 <b>دقة الإشارات</b> (3 ظهورات فأكثر):"]
            for n, pct, cnt in ranked:
                lines.append(f"• {n}: {pct:.0f}% نجاح ({cnt} مرة)")
            lines += ["", f"💡 أقوى إشارة: {ranked[0][0]} | "
                          f"أضعف إشارة: {ranked[-1][0]}. "
                          "إذا ثبت النمط أسبوعين، نعدّل أوزان النقاط."]
    else:
        lines += ["", "لا توجد صفقات محسومة كافية بعد — "
                      "التقييم يحتاج أسبوعين إلى شهر من البيانات."]

    lines += ["", "⚠️ <i>إحصاءات آلية للتقييم الذاتي — ليست توصية.</i>"]
    return "\n".join(lines)


def _prune_alerts(data):
    """يقلّم سجل التنبيهات: يبقي المفتوحة + المغلقة خلال ALERTS_KEEP_DAYS فقط
    (يمنع نمو alerts_history.json بلا حد عبر الشهور — البيانات المؤرشفة كافية)."""
    cutoff = (dt.date.today()
              - dt.timedelta(days=int(CONFIG["ALERTS_KEEP_DAYS"]))).isoformat()
    kept = []
    for a in data.get("alerts", []):
        if a.get("status") == "open":
            kept.append(a)
            continue
        when = a.get("result_date") or a.get("date") or ""
        if when >= cutoff:
            kept.append(a)
    data["alerts"] = kept


def run_performance_system(results, weekly_report_now=False):
    data = load_alerts()
    updates = update_tracking(data)      # 1) تابع التنبيهات القديمة
    record_new_alerts(data, results)     # 2) سجّل تنبيهات اليوم
    _prune_alerts(data)                  # 2.5) قلّم القديم (نمو محدود)
    save_alerts_file(data)               # 3) احفظ السجل محلياً
    if updates:
        send_telegram(tracking_message(updates))
    # التقرير الأسبوعي يُرسَل مع التجديد (الجمعة بعد الإغلاق = أسبوع كامل)،
    # لا حسب يوم الأسبوع — فلا يُرسَل مبكرًا على إغلاق ناقص بمسار المتابعة.
    if weekly_report_now:
        rep = weekly_report(data)
        if rep:
            send_telegram(rep)
    # 4) ذاكرة دائمة في الـ repo (سجل التنبيهات + قائمة الأسبوع)
    git_save([TRACK_FILE, WATCH_FILE, COMPANY_FILE])


if __name__ == "__main__":
    try:
        main()
    except Exception:
        err = traceback.format_exc()
        log("❌ خطأ غير متوقع:\n" + err)
        # محاولة إبلاغك بالخطأ على تيليجرام بدل الصمت
        try:
            send_telegram("❌ البوت توقف بخطأ:\n<code>"
                          + esc(err[-1500:]) + "</code>")
        except Exception:
            pass
        sys.exit(1)
