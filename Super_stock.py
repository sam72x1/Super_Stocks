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
  • الجمعة بعد الإغلاق: فرز السوق كامل → اختيار أفضل 10 أسهم
    → تثبيتها في weekly_watchlist.json كقائمة الأسبوع.
  • الاثنين→الخميس: لا فرز جديد — حساب نسبة جاهزية الدخول
    (0-100%) لكل سهم حسب التحليل الفني اللحظي، وإرسال القائمة
    مرتبة بالنسبة.
  • سهم يضرب الستوب → يُشطب بسببه، ويُستبدل في تشغيل اليوم
    التالي (القائمة دائماً ≤ 10).
  • الجمعة: تقرير حصاد الأسبوع (الأداء + أسباب الشطب للتعلم)
    ثم تجديد القائمة كاملة.
  • أول تشغيل بدون قائمة = تأسيس فوري (لا تنتظر الجمعة).
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
    "BOLL_SQUEEZE_PCTL": 0.25,     # عرض الحزمة ضمن أدنى 25% من آخر 60 جلسة

    # ---- القائمة الأسبوعية (v2.0) ----
    "WATCHLIST_SIZE": 10,        # حجم القائمة الثابتة (حد أقصى)
    # ---- قائمة مراقبة الارتداد المستقلة (v2.8): أسهم ارتكاز حقيقية ارتفعت
    # فوق دخولها؛ نتابعها يوميًا وننبّه أول ما تنزل لسعر الدعم (انهيار البورصة)
    "PULLBACK_WATCH": True,
    "PULLBACK_SIZE": 15,         # حجم قائمة مراقبة الارتداد (حد أقصى)
    "PULLBACK_TRIGGER_PCT": 2.0,  # تنبيه عند الوصول ضمن +2% فوق سعر الدعم
    # v2.6 (فيصل): فرز السوق كاملاً كل يوم بعد الإغلاق بدل الجمعة فقط
    # (أسهم الشروط الصارمة نادرة جداً — نصطادها أي يوم تظهر)
    "DAILY_FULL_SCAN": True,
    "READY_PCT": 75,             # نسبة الجاهزية: 🟢 جاهز من هنا وفوق
    "NEAR_PCT": 50,              # 🟡 يقترب من هنا وفوق، وتحتها 🔴 بعيد
    "EXCLUDE_STOPPED_FROM_RENEWAL": True,  # لا تُعِد سهماً ضرب ستوبه هذا الأسبوع

    # ---- قاعدة الثبات (التوقيت الذهبي: 3-5 جلسات بعد القاع) ----
    "PIVOT_LOOKBACK": 25,        # نبحث عن القاع في آخر 25 جلسة
    "STABILITY_MIN": 3,
    "STABILITY_MAX": 8,          # 5 + سماحية بسيطة
    "STABILITY_TOL_PCT": 2.0,    # القيعان بعد القاع ضمن 2% منه

    # ---- مستويات مقترحة ----
    "STOP_BELOW_LOW_PCT": (5.0, 7.0),    # الوقف 5-7% تحت القاع (فيصل: تحت
                                         # منطقة سحب السيولة، لا 1-2% الضيقة)
    "ENTRY_ABOVE_PIVOT_PCT": 8.0,        # الحد الأعلى للدخول = القاع +8%
                                         # (لا تطارد السهم أعلى من هذا)
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
    "RED_CANDLE_MIN_DROP": 15.0,         # شمعة الهبوط الكبيرة ≥ 15% للهدف الأول

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
    "MIN_TARGET_GAP_PCT": 8.0,   # أقل مسافة بين هدف وآخر
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
}

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
MODE = os.environ.get("SCREENER_MODE", CONFIG["MODE"]).strip().upper()

UA = {"User-Agent": "Mozilla/5.0 (pivot-screener; personal research)"}
# SEC تتطلب User-Agent فيه وسيلة تواصل — يمكن ضبطه بمتغير بيئة SEC_CONTACT
SEC_UA = {"User-Agent": os.environ.get(
    "SEC_CONTACT", "PivotScreener/2.0 (personal research; contact@example.com)")}
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
#   Bollinger 20/2 · StochRSI 14/14/3/3 · DMI 14 · ATR 14 ·
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
            data = yf.download(chunk, start=start, interval="1d",
                               auto_adjust=True, group_by="ticker",
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


def resistance_levels(df: pd.DataFrame, price: float, max_levels: int = 8):
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
    try:
        wk = resample_ohlc(df, "W")
        if wk is not None and len(wk) >= 7:
            real += _swing_highs(wk["High"].values.astype(float), price, 2)
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
    return {"supports": supports, "resistances": resistances,
            "flip": flip, "sweep_low": round(float(np.min(lo)), 2)}


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


def _reject(code):
    """يسجّل سبب رفض السهم (للتشخيص في سجل الفرز) ويرجع None."""
    _REJECT_STATS[code] = _REJECT_STATS.get(code, 0) + 1
    return None


def analyze_ticker(sym: str, df: pd.DataFrame, pullback: bool = False):
    """يرجع dict بالنتيجة إذا اجتاز الشروط الإلزامية، وإلا None.
    pullback=True: وضع «مراقبة الارتداد» — سهم ارتكاز حقيقي (بنية مكتملة)
    لكنه ارتفع فوق دخوله؛ نرصده ليُتابَع يوميًا وندخله لو رجع للدعم (انهيار
    البورصة). الوضع العادي (pullback=False) يبقى مطابقًا تمامًا بلا أي تغيير."""
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
            return _reject("M2_هبوط>97")  # محتضر/فخ تقسيم
        if drop_pct < CONFIG["MIN_DROP_FLOOR"]:
            return _reject("M2_هبوط<40")   # تحت الأرضية = ليس ارتكازًا
        if drop_pct < CONFIG["MIN_DROP_PCT"]:
            soft_fails.append(f"هبوط حدّي {drop_pct:.0f}%")

        # ---- M3: الانفجار السابق (تدرّج v2.7) ----
        # أرضية (<60%) = رفض. حدّي (60-100%) = نقص (B). مثالي (≥100%) = بلا عقوبة.
        best_spike, n_spikes = spike_info(c, exclude_last=CONFIG["BASE_WINDOW"])
        if best_spike < CONFIG["PRIOR_SPIKE_FLOOR"]:
            return _reject("M3_انفجار<60")  # ما انفجر كفاية
        if best_spike < CONFIG["PRIOR_SPIKE_PCT"]:
            soft_fails.append(f"انفجار حدّي {best_spike:.0f}%")

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
            soft_fails.append(f"توافق فريمات {mtf['count']}/3")

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
            soft_fails.append("فجوة-هدف فوق")

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
                soft_fails.append(f"RSI تشبع حدّي ({r_min_os:.0f})")  # 27-32 → B
            if r_now > CONFIG["RSI_NOW_HARD"]:
                if not pullback:
                    return _reject("M10_RSI_فات_القطار")  # >50 = فات الارتكاز
                risen = True
                watch_reasons.append(f"RSI ارتفع للـ{r_now:.0f}")
            elif r_now > CONFIG["RSI_MAX_NOW"]:
                soft_fails.append(f"RSI الآن {r_now:.0f}>40")        # 40-50 طار → B

        # ---- M11: تقاطع MACD إيجابي — بوابة لينة ----
        m_line, m_sig = macd(close)
        macd_ok = (float(m_line.iloc[-1]) >= float(m_sig.iloc[-1])
                   or (m_line.iloc[-5:] > m_sig.iloc[-5:]).any())
        if CONFIG.get("MACD_GATE_REQUIRED", False) and not macd_ok:
            soft_fails.append("MACD")

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
            soft_fails.append("المتوسط الأسي")

        # حد أقصى للنواقص هنا (M13/M14 شورت/فلوت تُضاف لاحقًا في الفرز)
        if not pullback and len(soft_fails) > CONFIG.get("WATCH_MAX_FAILS", 2):
            return _reject(f"نواقص>{CONFIG.get('WATCH_MAX_FAILS',2)}")

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
            return _reject(f"نقاط<{CONFIG['SCORE_MIN']}")

        # ======== المستويات المقترحة ========
        pivot = ps["pivot"] if ps else float(low.tail(20).min())
        # الوقف تحت القاع بنسبة فيصل (~7%، تحت منطقة "سحب السيولة")
        # فيصل (SMX): القاع 6.11، سحب السيولة قد يصل 5.80 ثم يرتد.
        # الوقف الفعلي تحت منطقة السحب — لا 1-2% الضيقة التي تُضرب بالتذبذب.
        s_lo, s_hi = CONFIG["STOP_BELOW_LOW_PCT"]
        stop_hi = pivot * (1 - s_lo / 100.0)    # أعلى الوقف (أقرب للقاع)
        stop_lo = pivot * (1 - s_hi / 100.0)    # أدنى الوقف (تحت السحب)
        # ستوب ATR ديناميكي (v2.7): يحترم تذبذب السهم الفعلي — نأخذ الأبعد
        # (الأكثر أمانًا) بين نسبة 5-7% و(القاع - 1.5×ATR) حتى لا يُكنس.
        if CONFIG.get("USE_ATR_STOP", False) and ind.get("atr", 0) > 0:
            atr_stop = pivot - CONFIG["ATR_STOP_MULT"] * ind["atr"]
            stop_lo = min(stop_lo, atr_stop)
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
                    target_cands += list(resistance_levels(wk, price))
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
        entry_ref = entry_hi
        risk = max(entry_ref - stop_lo, 1e-9)
        rr = (t1 - entry_ref) / risk
        rr2 = (t2 - entry_ref) / risk
        # v2.7: ضعف RR = نقص (ينقل لقائمة B المراقبة) بدل الرفض النهائي —
        # متوافق مع قرار «ما نطلع صفر». لو تجاوز مجموع النواقص الحد → يُرفض.
        if rr < CONFIG["MIN_RR_T1"]:
            soft_fails.append("عائد/مخاطرة منخفض")
            if not pullback and len(soft_fails) > CONFIG.get("WATCH_MAX_FAILS", 2):
                return _reject("RR+نواقص>الحد")

        # ملخص حالة بوابات فيصل (للرسالة المختصرة) — كلها ✅ لأن السهم
        # اجتازها، لكن نعرضها للتأكيد البصري ولمعرفة قيمة كل شرط فعلياً
        ema30_v = ema(close, 30)
        macd_now_ok = (float(m_line.iloc[-1]) >= float(m_sig.iloc[-1])
                       or (m_line.iloc[-5:] > m_sig.iloc[-5:]).any())
        ma_dist = ((price / ema30_v - 1.0) * 100.0) if ema30_v > 0 else 0.0
        gates_status = {
            "السعر≥2": (True, f"${price:.2f}"),
            "هبوط 50-97%": (True, f"{drop_pct:.0f}%"),
            "انفجار≥100%": (True, f"{best_spike:.0f}%"),
            "قاعدة ضيقة": (True, f"{base_range:.0f}%"),
            "سيولة كافية": (True, fmt_money(dvol)),
            "توافق فريمات": (mtf["count"] >= CONFIG["TF_MIN_REVERSALS"],
                            f"{mtf['count']}/3"),
            "شمعة انعكاس": (bool(patterns),
                           "، ".join(patterns) if patterns else "لا"),
            "RSI تشبع (≤27)": (r_min_recent <= CONFIG["RSI_OVERSOLD"],
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
        tier = "W" if pullback else ("A" if not soft_fails else "B")

        return {
            "symbol": sym, "price": price, "score": int(min(score, 100)),
            "drop_pct": drop_pct, "best_spike": best_spike,
            "n_spikes": n_spikes, "base_range": base_range,
            "rsi": r_now, "dollar_vol": dvol,
            "pivot": pivot, "stop": (stop_lo, stop_hi),
            "entry": (entry_lo, entry_hi), "tranches": tranches,
            "sweep": (sweep_lo, sweep_hi),
            "t1": t1, "t2": t2, "t3": t3, "rr": rr, "rr2": rr2,
            "ready": ready, "readiness": readiness_pct,
            "flags": flags, "warnings": warnings,
            "tf_count": mtf["count"], "tf_display": mtf["display"],
            "patterns": patterns,
            "gaps": gaps,
            "gaps_above": gaps_above,
            "gates_status": gates_status,
            "soft_fails": soft_fails,                 # بوابات تأكيد ناقصة
            "tier": tier,                             # A/B عادي · W مراقبة ارتداد
            "watch_reasons": watch_reasons,           # أسباب وضع الارتداد
            "indicators": ind,                        # مؤشرات فيصل الإضافية
            "liberation": liberation,                 # بوابة "تحرر السهم"
            "lib_near": lib_near,                      # قريب من التحرر؟
            "qab": qab,                               # أقرب فجوة (قاب) فوق السعر
        }
    except Exception:
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
}

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
        for i in range(len(forms)):
            fdate = dates[i] if i < len(dates) else ""
            if fdate < cutoff:
                break  # القائمة مرتبة من الأحدث للأقدم
            form = (forms[i] or "").strip()
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
                break
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
    for i in range(attempts):
        try:
            info = t.info or {}
            # نعتبرها ناجحة لو رجّعت حقولًا مفيدة (وإلا غالبًا خُنقت)
            if info.get("sector") or info.get("country") or \
                    info.get("floatShares") or info.get("longBusinessSummary"):
                return info
        except Exception:
            pass
        if i < attempts - 1:
            time.sleep(base * (2 ** i))
    return {}


def enrich(results: list) -> None:
    """إثراء المرشحين: شورت (Fintel→FINRA→Yahoo) + SEC + تقسيمات + أخبار"""
    syms = {r["symbol"] for r in results}
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
        r["short_pct"] = None
        r["float"] = None
        r["recent_split"] = None
        r["news"] = []
        r["tf4h"] = "غير متوفر"
        # إعلانات SEC الرسمية (هوية مضمونة بالـCIK)
        r["sec_filings"], r["sec_status"] = sec_recent_filings(r["symbol"])
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
                                  else cached.get("short_pct"))
                # القيمة المجلوبة إن وُجدت، وإلا آخر قيمة معروفة (لا يختفي 🏢)
                r["float"] = _or_cache(info.get("floatShares"), cached, "float")
                r["sector"] = _or_cache(info.get("sector") or
                                        info.get("industry"), cached, "sector")
                r["industry"] = _or_cache(info.get("industry"),
                                          cached, "industry")
                summ = info.get("longBusinessSummary") or ""
                r["business"] = ((summ[:160].strip() + "…") if summ
                                 else cached.get("business"))
                r["country"] = _or_cache(info.get("country"), cached, "country")
                r["cash"] = _or_cache(info.get("totalCash"), cached, "cash")
                r["revenue"] = _or_cache(info.get("totalRevenue"),
                                         cached, "revenue")
                r["shares_out"] = _or_cache(info.get("sharesOutstanding"),
                                            cached, "shares_out")
                # حدّث الذاكرة بالقيم المعروفة الآن (للتشغيلات القادمة)
                COMPANY_CACHE[sym] = {k: r.get(k) for k in
                                      ("sector", "industry", "business",
                                       "country", "cash", "revenue",
                                       "shares_out", "short_pct", "float")
                                      if r.get(k) is not None}
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
                else:
                    r["tf4h"] = "غير متوفر"
            except Exception:
                r["tf4h"] = "غير متوفر"
        except Exception:
            continue
        time.sleep(0.5)
    _save_company_cache(COMPANY_CACHE)   # حفظ آخر القطاعات/الدول المعروفة


# ==========================================================
# 7) استراتيجية التقسيم العكسي
# ==========================================================
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
            target = round(day_open / 2.0, 2) if day_open else None
            srt = shorts.get(sym)
            ok = (srt is not None and srt < CONFIG["SHORT_DAILY_MAX"])
            rows.append({
                "symbol": sym, "split_date": str(split_date),
                "open": day_open, "half": target, "price": price,
                "short": srt, "short_ok": ok,
            })
        except Exception:
            continue
    return rows


# ==========================================================
# 8) أدوات الرسائل المشتركة
# ==========================================================
def esc(s):
    """تعقيم النصوص الخارجية حتى لا تكسر HTML تيليجرام"""
    return (str(s).replace("&", "&amp;")
            .replace("<", "&lt;").replace(">", "&gt;"))


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
}


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
            head = esc(it.get("title", ""))[:140]
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
                         + " · ".join(f"{k}={v}" for k, v in top))
    for r in results:
        # ===== بطاقة مرتّبة ومختصرة (v2.7) — أساسيات فقط =====
        tier = r.get("tier", "A")
        badge = "🅰️" if tier == "A" else "🅱️"
        # رقمان واضحان: «نسبة الدخول/الجاهزية» (قرب الدخول) بصيغة /100،
        # و«النسبة العامة» (قوة المطابقة) بصيغة %. حالة الجاهزية (🟢🟡🔴) بسطرها.
        lines.append("━━━━━━━━━━━━━━━")
        lines.append(f"{badge} <b>{r['symbol']}</b> · ${r['price']:.2f}")
        lines.append(f"   {readiness_ratio(r.get('readiness'), tier)} · "
                     f"النسبة العامة <b>{r['score']}%</b>")
        if tier == "B":
            sf = r.get("soft_fails", [])
            if sf:
                lines.append("   🅱️ مراقبة — ينقصها:")
                for f in sf:
                    lines.append(f"      • {f}")
            else:
                lines.append("   🅱️ مراقبة")
        # سطر الشركة (مختصر)
        sec = r.get("sector") or r.get("industry")
        cbits = []
        if sec:
            cbits.append(esc(ar_sector(sec)))
        if r.get("country"):
            cbits.append(esc(ar_country(r["country"])))
        if r.get("cash"):
            cbits.append(f"نقد {fmt_money(r['cash'])}")
        if cbits:
            lines.append("🏢 " + " · ".join(cbits))
        # سطر النمط (لماذا ارتكاز): هبوط/انفجار/RSI/شورت/فلوت
        pat = [f"هبوط {r['drop_pct']:.0f}%", f"انفجار {r['best_spike']:.0f}%",
               f"RSI {r['rsi']:.0f}"]
        sv = (r.get("fintel") or {}).get("short_volume") or r.get("finra_short")
        if sv is not None:
            pat.append(f"شورت {fmt_money(sv)}")
        if r.get("float"):
            pat.append(f"فلوت {fmt_money(r['float'])}")
        lines.append("📊 " + " · ".join(pat))
        # سطر التأكيد الفني (نمط الشمعة + الفريمات + إشارات مفتاحية)
        conf = []
        if r.get("patterns"):
            conf.append("، ".join(r["patterns"]))
        _fr = f"فريمات {r.get('tf_count', 0)}/3"
        _tf4 = r.get("tf4h")
        if _tf4 and _tf4 not in ("غير متوفر", "غير مفعّل"):
            _fr += f" + 4س {_tf4}"
        conf.append(_fr)
        if any("مسح سيولة" in f for f in r.get("flags", [])):
            conf.append("مسح سيولة ✓")
        if any("MFI" in f for f in r.get("flags", [])):
            conf.append("تباعد MFI ✓")
        lines.append("🕯️ " + " · ".join(conf))
        # ===== الخطة (الأسعار الأساسية فقط) =====
        lines.append("🎯 <b>الخطة:</b>")
        _trs = r.get("tranches") or [r['entry'][0], r['entry'][1]]
        lines.append("   دخول دفعات: "
                     + " · ".join(f"${p:.2f}" for p in _trs)
                     + f"  ·  وقف ${r['stop'][0]:.2f}")
        lines.append(f"   أهداف ${r['t1']:.2f} → ${r['t2']:.2f} → ${r['t3']:.2f}"
                     f"  (ربح/مخاطرة {r['rr']:.1f}×)")
        if r.get("qab"):
            q = r["qab"]
            lines.append(f"   🟡 قاب (فجوة-هدف) من ${q['bottom']:.2f} "
                         f"إلى ${q['top']:.2f}  (يبعد +{q['dist_pct']:.0f}%)")
        if r.get("liberation"):
            tag = " 🔓 قريب!" if r.get("lib_near") else ""
            lines.append(f"   🚀 تحرر فوق ${r['liberation']:.2f}{tag}")
        lines += h4_levels_block(r.get("h4_levels"))
        # مؤشرات مختصرة (سطر واحد)
        ic = r.get("indicators") or {}
        mp = []
        if "mfi" in ic:
            mp.append(f"MFI {ic['mfi']:.0f}")
        if "adx" in ic:
            mp.append(f"ADX {ic['adx']:.0f}")
        if ic.get("boll_pctb") is not None:
            mp.append(f"كلنجر%B {ic['boll_pctb']:.2f}")
        if mp:
            lines.append("📐 " + " · ".join(mp))
        # تنبيهات حرجة فقط (تقسيم + SEC أحمر + تحذيرات)
        if r.get("recent_split"):
            lines.append(f"✂️ تقسيم عكسي {r['recent_split'][0]}")
        red = [x for x in (r.get("sec_filings") or []) if "🔴" in x]
        if red:
            lines.append("📋 " + esc(red[0]))
        if r.get("warnings"):
            lines.append("⚠️ " + "؛ ".join(esc(w) for w in r["warnings"]))
        lines.append(news_links(r["symbol"]))
    lines += ["", FOOTER]
    return "\n".join(lines)


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
    chunks, cur = [], ""
    for ln in text.split("\n"):
        if len(cur) + len(ln) + 1 > 3800:
            chunks.append(cur)
            cur = ln
        else:
            cur = cur + "\n" + ln if cur else ln
    if cur:
        chunks.append(cur)
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


# ==========================================================
# 9) نظام القائمة الأسبوعية الثابتة (v2.0)
# ==========================================================
WATCH_FILE = "weekly_watchlist.json"   # ملف ذاكرة القائمة في الـ repo
COMPANY_FILE = "company_cache.json"    # ذاكرة آخر قطاع/دولة معروفة لكل سهم
WEEKLY_RENEW_DAY = 4                   # 4 = الجمعة (الاثنين = 0)


def _load_company_cache() -> dict:
    if os.path.exists(COMPANY_FILE):
        try:
            with open(COMPANY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_company_cache(cache: dict) -> None:
    try:
        with open(COMPANY_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=1)
    except Exception as e:
        log(f"⚠️ حفظ ذاكرة الشركات: {e}")


def _or_cache(val, cached, key):
    """يرجّع القيمة المجلوبة إن وُجدت، وإلا آخر قيمة معروفة من الذاكرة."""
    return val if val not in (None, "") else cached.get(key)


COMPANY_CACHE = _load_company_cache()


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
    try:
        with open(WATCH_FILE, "w", encoding="utf-8") as f:
            json.dump(wl, f, ensure_ascii=False, indent=1)
    except Exception as e:
        log(f"⚠️ حفظ ملف القائمة: {e}")


def should_renew(wl: dict, today: dt.date, force: bool = False) -> bool:
    """تحديد متى نفرز السوق كاملاً ونبني قائمة جديدة.
    - DAILY_FULL_SCAN=True (فيصل، v2.6): فرز كامل كل يوم بعد الإغلاق
      (لأن أسهم الشروط الصارمة نادرة، نصطادها أي يوم تظهر).
    - غير ذلك: جمعة = تجديد | لا قائمة = تأسيس | FORCE_RENEW=1 = إجبار."""
    if force:
        return True
    if not wl.get("stocks") and not wl.get("removed"):
        return True  # أول تشغيل — تأسيس فوري
    # القائمة ثابتة دائمة: لا نعيد بناءها كل تشغيل (يسبب رفرفة الأسهم).
    # التجديد الكامل = الجمعة فقط؛ باقي الأيام = متابعة + إضافة الجديد فقط.
    return today.weekday() == WEEKLY_RENEW_DAY


def make_watch_entry(r: dict, today_iso: str) -> dict:
    """تحويل نتيجة تحليل إلى سجل سهم في القائمة الأسبوعية"""
    return {
        "symbol": r["symbol"], "added": today_iso,
        "entry_ref": round(r["price"], 4),
        "entry": [round(r["entry"][0], 4), round(r["entry"][1], 4)],
        "tranches": [round(p, 4) for p in (r.get("tranches") or r["entry"])],
        "pivot": round(r["pivot"], 4),
        "stop": round(r["stop"][0], 4),        # الوقف الأبعد (2% تحت القاع)
        "stop_hi": round(r["stop"][1], 4),
        "t1": round(r["t1"], 4), "t2": round(r["t2"], 4),
        "t3": round(r["t3"], 4),
        "score": r["score"], "flags": list(r["flags"]),
        "tier": r.get("tier", "A"),                       # A صارمة / B مراقبة
        "soft_fails": list(r.get("soft_fails", [])),
        "warnings": list(r.get("warnings", [])),          # تحذيرات (تخفيف/جغرافي)
        "news_risk": bool([w for w in r.get("warnings", [])
                           if "تخفيف" in w or "طرح" in w]),  # خبر تخفيف؟
        "h4_levels": r.get("h4_levels"),                  # مستويات 4س (فيصل)
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
    """تصنيف السهم حسب عدد بوابات التأكيد الناقصة:
    0 → 'A' (صارمة) | 1..maxf → 'B' (مراقبة) | أكثر → None (يُرفض).
    دالة نقية لتسهيل الاختبار (تستخدمها scan_market)."""
    two_tier = CONFIG.get("WATCHLIST_TWO_TIER", True) if two_tier is None else two_tier
    maxf = CONFIG.get("WATCH_MAX_FAILS", 2) if maxf is None else maxf
    n = len(soft_fails or [])
    if n == 0:
        return "A"
    if two_tier and n <= maxf:
        return "B"
    return None


def rank_key(x):
    """مفتاح ترتيب القائمة التأسيسية (موحّد مع التقرير اليومي والرقم المعروض):
    A قبل B → الأعلى جاهزيةً → الأعلى نقاطًا → الأعلى عائدًا/مخاطرة."""
    rdy = x.get("readiness")
    return (0 if x.get("tier") == "A" else 1,
            -(rdy if rdy is not None else -1),
            -x.get("score", 0), -x.get("rr", 0))


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
    """فرز السوق (تجديد الجمعة أو جلب بدائل) — يرجع (نتائج مرتبة، بيانات)"""
    if MODE == "FULL":
        universe = get_universe()
        if not universe:
            log("⚠️ فشل جلب الكون — التحويل لوضع TEST")
            universe = CONFIG["TEST_TICKERS"]
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
    for sym, df in history.items():
        r = analyze_ticker(sym, df)
        if r:
            results.append(r)
    # تشخيص: أين تُرفض الأسهم؟ (يظهر بسجل الأكشن لمعرفة البوابة الخانقة)
    if _REJECT_STATS:
        top = sorted(_REJECT_STATS.items(), key=lambda x: -x[1])
        log("أسباب الرفض: " + " · ".join(f"{k}={v}" for k, v in top))
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
    # ترتيب موحّد: A قبل B → الأعلى جاهزيةً (الرقم المعروض) → النقاط → العائد.
    # (يطابق التقرير اليومي + ترويسة «الجاهز أولاً» = لا تناقض مع الرقم المعروض)
    results.sort(key=rank_key)
    na = sum(1 for r in results if r.get("tier") == "A")
    log(f"الفرز: {na} (A صارمة) + {len(results) - na} (B مراقبة) "
        f"= {len(results)} مرشح")
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
        s["last_price"] = round(float(df["Close"].iloc[-1]), 4)
        # شموع ما بعد يوم الإضافة فقط (التنبيه صدر بعد إغلاق يومه)
        rows = []
        for i in range(len(df)):
            try:
                day = df.index[i].date()
            except Exception:
                continue
            if day > added:
                rows.append((day, float(df["High"].iloc[i]),
                             float(df["Low"].iloc[i])))
        if rows:
            mx = max(h for _, h, _ in rows)
            s["max_gain_pct"] = round((mx / s["entry_ref"] - 1.0) * 100.0, 1)
        for day, hi, lo in rows:
            # الستوب أولاً (محافظ) إذا لم يتحقق أي هدف قبله
            if lo <= s["stop"] and not s["hit"]:
                s["status"] = "stopped"
                s["removed_date"] = today_iso
                loss = (s["stop"] / s["entry_ref"] - 1.0) * 100.0
                s["removal_reason"] = (f"ضرب الستوب ${s['stop']:.2f} "
                                       f"يوم {day} ({loss:+.1f}%)")
                break
            # الأهداف (تصاعدياً)
            if hi >= s["t3"] and s["hit"] != "t3":
                s["hit"], s["hit_date"] = "t3", str(day)
            elif hi >= s["t2"] and s["hit"] not in ("t2", "t3"):
                s["hit"], s["hit_date"] = "t2", str(day)
            elif hi >= s["t1"] and not s["hit"]:
                s["hit"], s["hit_date"] = "t1", str(day)
            # ستوب بعد تحقيق هدف = خروج رابح مفترض، لكن النموذج انتهى
            if lo <= s["stop"]:
                s["status"] = "stopped"
                s["removed_date"] = today_iso
                s["removal_reason"] = (f"لمس الستوب يوم {day} بعد تحقيق "
                                       f"هدف{s['hit'][-1]} (خروج رابح مفترض)")
                break
        # ملاحظات تعلّم (لا تُشطب بسببها — تُعرض الجمعة)
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
            if s["stop"] < lp < s["pivot"]:
                _note(wl, s["symbol"],
                      f"يتداول تحت القاع ${s['pivot']:.2f} بدون لمس الستوب",
                      family="تحت القاع")
    # نقل المشطوبين من النشطين إلى سجل المشطوبين
    newly = [s for s in wl["stocks"] if s["status"] != "active"]
    wl["stocks"] = [s for s in wl["stocks"] if s["status"] == "active"]
    wl["removed"].extend(newly)
    return newly


def fill_replacements(wl: dict):
    """جلب بدائل لمن شُطب في يوم *سابق* (قاعدة: الاستبدال اليوم التالي).
    يرجع (نتائج البدائل، بياناتهم التاريخية)"""
    today_iso = dt.date.today().isoformat()
    pending = [rm for rm in wl["removed"]
               if not rm.get("replaced")
               and rm.get("removed_date")
               and rm["removed_date"] < today_iso]
    space = CONFIG["WATCHLIST_SIZE"] - len(wl["stocks"])
    n = min(len(pending), max(space, 0))
    if n <= 0:
        if space > 0 and any(not rm.get("replaced") for rm in wl["removed"]):
            log("شُطب اليوم → الاستبدال غداً (حسب القاعدة)")
        return [], {}
    exclude = ({s["symbol"] for s in wl["stocks"]}
               | {rm["symbol"] for rm in wl["removed"]})
    log(f"البحث عن {n} بديل من السوق...")
    results, hist = scan_market()
    picks = select_top(results, n, exclude)
    added = []
    for r, rm in zip(picks, pending):
        rm["replaced"] = True
        wl["stocks"].append(make_watch_entry(r, today_iso))
        wl["replacements_log"].append({
            "date": today_iso, "out": rm["symbol"],
            "in": r["symbol"], "score": r["score"]})
        added.append(r)
    if added:
        log("أُضيف بديل: " + "، ".join(p["symbol"] for p in added))
    elif n > 0:
        log("لم يُعثر على بدائل تطابق الشروط اليوم — سيُعاد غداً")
    sub_hist = {r["symbol"]: hist[r["symbol"]]
                for r in added if r["symbol"] in hist}
    return added, sub_hist


def check_promotions(wl: dict, history: dict) -> list:
    """ترقية B→A (v2.7): يعيد تحليل كل سهم نشط بالبيانات الحالية. السهم
    الذي اكتمل نموذجه (0 نواقص تأكيد) يُرقّى من قائمة المراقبة B إلى A مع
    تنبيه «🚀 جاهز». يحدّث أيضًا النواقص الحالية لكل سهم B (عرض حيّ).
    هذا قلب فكرة الارتكاز: نمسك السهم مبكرًا (B) ثم ننبّه لحظة جاهزيته."""
    promoted = []
    today = dt.date.today().isoformat()
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
        # نزول A→B لخبر التخفيف فقط لو ظهر «تأثير سلبي فعلي» (قرار المستخدم):
        # كسر الدعم أو قاع أدنى جديد. يرجع A تلقائياً لمّا يستقر فوق الدعم.
        if s.get("news_risk"):
            piv = s.get("pivot")
            last = float(fresh.get("price") or df["Close"].iloc[-1])
            recent_low = float(df["Low"].tail(5).min())
            broke = bool(piv) and (last < piv or recent_low < piv * 0.99)
            tag = "تخفيف: كسر الدعم"
            if broke and tag not in combined:
                combined.append(tag)
        was = s.get("tier", "A")
        s["soft_fails"] = combined
        s["tier"] = "A" if not combined else "B"
        s["liberation"] = fresh.get("liberation")
        if was == "B" and s["tier"] == "A":
            s["promoted_date"] = today
            promoted.append(s)
            _note(wl, s["symbol"], "🚀 ترقية B→A: اكتمل النموذج", family="ترقية")
    if promoted:
        log("ترقيات B→A: " + "، ".join(p["symbol"] for p in promoted))
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


def readiness_badge(p, tier="A"):
    if p is None:
        return "⚠️ لا بيانات"
    if p >= CONFIG["READY_PCT"]:
        # "جاهز" للقائمة A فقط (النموذج مكتمل). B = "قرب الدخول" (السعر بالنطاق)
        label = "جاهز" if tier == "A" else "قرب الدخول"
        return f"<b>{p}%</b> 🟢 {label}"
    if p >= CONFIG["NEAR_PCT"]:
        return f"<b>{p}%</b> 🟡 يقترب"
    return f"<b>{p}%</b> 🔴 بعيد عن الدخول"


def readiness_ratio(p, tier="A"):
    """«نسبة الدخول/الجاهزية» بصيغة X/100 + حالتها (🟢🟡🔴) — تنسيق موحّد
    للبطاقة والتقرير اليومي (مصدر واحد، لا اختلاف)."""
    if p is None:
        return "نسبة الدخول/الجاهزية غير متاحة"
    status = readiness_badge(p, tier).split("</b>")[-1].strip()
    return f"نسبة الدخول/الجاهزية <b>{p}/100</b> {status}"


def build_pullback_section(entries: list, triggered: list = None) -> str:
    """قسم «مراقبة الارتداد»: أسهم ارتكاز ارتفعت ننتظر رجوعها للدعم +
    تنبيهات الأسهم التي وصلت سعر الدعم اليوم (جاهزة للدخول)."""
    triggered = triggered or []
    if not entries and not triggered:
        return ""
    lines = []
    if triggered:
        lines.append("🎯 <b>وصلت الدعم — جاهزة للدخول!</b>")
        for e in triggered:
            lines.append(f"• <b>{e['symbol']}</b> نزل ${e['last_price']:.2f} "
                         f"≈ دخول ${e['entry'][1]:.2f} · وقف ${e['stop']:.2f} "
                         f"· هدف١ ${e['t1']:.2f}")
        lines.append("")
    if entries:
        lines.append("👁️ <b>مراقبة للارتداد</b> "
                     "(ارتكاز ارتفع — ننتظر رجوعه لسعر الدعم):")
        for e in entries:
            tgt = e["entry"][1]
            dist = (e["last_price"] / tgt - 1.0) * 100.0 if tgt else 0.0
            sec = f" · {esc(ar_sector(e['sector']))}" if e.get("sector") else ""
            lines.append(f"• <b>{e['symbol']}</b> ${e['last_price']:.2f} "
                         f"→ دخول الدعم ${tgt:.2f} (يبعد {dist:+.0f}%){sec}")
        lines.append("<i>يُنبَّه تلقائيًا أول ما ينزل لسعر الدعم.</i>")
    return "\n".join(lines)


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
                        promoted: list = None) -> str:
    """التقرير اليومي (الاثنين→الخميس): القائمة الثابتة مرتبة بالجاهزية"""
    today = dt.date.today().isoformat()
    n = len(wl["stocks"])
    lines = [f"📋 <b>قائمة الأسبوع</b> — {today}",
             f"{n}/{CONFIG['WATCHLIST_SIZE']} سهم | مرتبة حسب جاهزية الدخول "
             f"(تجديد القائمة: الجمعة)", ""]
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
    for i, s in enumerate(wl["stocks"], 1):
        lp = s["last_price"]
        tb = "🅰️" if s.get("tier", "A") == "A" else "🅱️"
        promo = " 🚀" if s.get("promoted_date") == today else ""
        lines.append(f"{i}) {tb}{promo} 📌 <b>{s['symbol']}</b> — "
                     f"{readiness_ratio(s['readiness'], s.get('tier', 'A'))} · "
                     f"النسبة العامة <b>{s.get('score', '?')}%</b>")
        if s.get("tier") == "B" and s.get("soft_fails"):
            lines.append("   🅱️ مراقبة — ينقصها:")
            for f in s["soft_fails"]:
                lines.append(f"      • {f}")
        # القطاع/الدولة (بالعربي) إن توفّرا
        cbits = []
        if s.get("sector"):
            cbits.append(esc(ar_sector(s["sector"])))
        if s.get("country"):
            cbits.append(esc(ar_country(s["country"])))
        if cbits:
            lines.append("   🏢 " + " · ".join(cbits))
        # نطاق الدخول؛ السجلّات القديمة بلا المفتاح → من الدعم لفوقه بقليل
        trs = s.get("tranches") or [
            round(s["pivot"] * (1 + CONFIG["ENTRY_STEP_PCT"] / 100.0 * i), 2)
            for i in range(int(CONFIG["ENTRY_TRANCHES"]))]
        lines.append(f"   💵 ${lp:.2f} | دفعات "
                     + " · ".join(f"${p:.2f}" for p in trs)
                     + f" | الدعم ${s['pivot']:.2f} | ستوب ${s['stop']:.2f}")
        if s.get("liberation"):
            lines.append(f"   🚀 تحرر فوق ${s['liberation']:.2f}")
        lines += h4_levels_block(s.get("h4_levels"))
        for w in (s.get("warnings") or []):
            lines.append(f"   ⚠️ {esc(w)}")
        # العائد/المخاطرة من أعلى دفعة دخول (أسوأ تعبئة) لا من السعر الحالي —
        # لأنك تنتظر السهم ينزل للدفعات قبل ما تشتري (تحفّظ في الحساب).
        entry_px = (s.get("entry") or [None, s["pivot"]])[1] or s["pivot"]
        e_risk = entry_px - s["stop"]
        if entry_px < s["t1"] and e_risk > 0:
            g1 = s["t1"] - entry_px
            mult = g1 / e_risk
            lines.append(f"   🛡️ عند الدخول ${entry_px:.2f}: تخاطر ${e_risk:.2f} "
                         f"← ربح هدف1 ${g1:.2f} ({mult:.1f}× المخاطرة)")
        elif lp >= s["t1"]:
            lines.append(f"   🎯 تجاوز هدف1 (${s['t1']:.2f}) — "
                         f"التالي ${s['t2']:.2f}")
        if s.get("hit"):
            lines.append(f"   🏆 حقق هدف{s['hit'][-1]} يوم {s['hit_date']} | "
                         f"أقصى ارتفاع {s['max_gain_pct']:+.0f}%")
        if s.get("have"):
            lines.append("   ✅ متوفر: " + "، ".join(s["have"]))
        if s.get("partial"):
            lines.append("   🔸 جزئي: " + "، ".join(s["partial"]))
        if s.get("missing"):
            lines.append("   ⏳ ناقص: " + "، ".join(s["missing"]))
    if replaced:
        lines += ["", "🔄 <b>بدلاء اليوم (انضموا للقائمة):</b>"]
        for r in replaced:
            lines.append(f"• <b>{r['symbol']}</b> | ${r['price']:.2f} | "
                         f"نقاط {r['score']} | قاع ${r['pivot']:.2f} | "
                         f"ستوب ${r['stop'][0]:.2f} | هدف1 ${r['t1']:.2f}")
        lines.append("(بطاقاتهم الكاملة مع SEC والشورت في تقرير الجمعة)")
    if stopped_today:
        lines += ["", "🛑 <b>شُطب اليوم (يُستبدل غداً):</b>"]
        for s in stopped_today:
            lines.append(f"• {s['symbol']}: {s['removal_reason']}")
    lines += ["", FOOTER]
    return "\n".join(lines)


def build_wrapup_message(wl: dict) -> str:
    """حصاد الأسبوع (الجمعة قبل التجديد): الأداء + أسباب الشطب للتعلم"""
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
            lines.append(f"• {s['symbol']}: {s['removal_reason']}")
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
    """الجمعة (أو التأسيس الأول): حصاد الأسبوع المنتهي + قائمة جديدة"""
    today_iso = dt.date.today().isoformat()
    is_friday = dt.date.today().weekday() == WEEKLY_RENEW_DAY
    # 1) إغلاق الأسبوع المنتهي (إن وُجد) بتحديث أخير + رسالة حصاد
    old_syms = sorted({s["symbol"] for s in wl["stocks"]})
    if old_syms and yf is not None:
        try:
            hist_old = download_history(old_syms)
            update_watchlist_status(wl, hist_old)
        except Exception as e:
            log(f"⚠️ تحديث الأسبوع المنتهي: {e}")
    # رسالة الحصاد تُرسل دائماً (حتى لو تعذر التحديث الأخير)
    wrap = build_wrapup_message(wl)
    if wrap:
        send_telegram(wrap)
    # 2) أرشفة مختصرة (آخر 8 أسابيع للتعلم التراكمي)
    if wl.get("week_start"):
        summary = {"week_start": wl["week_start"], "ended": today_iso,
                   "stocks": [{k: s.get(k) for k in
                               ("symbol", "entry_ref", "last_price",
                                "max_gain_pct", "status", "hit",
                                "removal_reason")}
                              for s in wl["stocks"] + wl["removed"]]}
        wl.setdefault("history", []).append(summary)
        wl["history"] = wl["history"][-8:]
    # 3) فرز جديد واختيار القائمة
    exclude = set()
    if CONFIG["EXCLUDE_STOPPED_FROM_RENEWAL"]:
        exclude = {s["symbol"] for s in wl["removed"]
                   if s["status"] == "stopped"}
    results, hist = scan_market()
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
    # 4) حفظ القائمة الجديدة
    new_wl = {"week_start": today_iso, "created": today_iso,
              "stocks": [make_watch_entry(r, today_iso) for r in picks],
              "removed": [], "replacements_log": [], "notes": [],
              "pullback": pull_entries,
              "history": wl.get("history", [])}
    save_watchlist(new_wl)
    # 5) رسالة القائمة الجديدة (بطاقات كاملة)
    title = ("🔄 <b>القائمة الأسبوعية الجديدة</b>" if is_friday
             else "🚀 <b>القائمة التأسيسية (تُجدَّد الجمعة)</b>")
    subnote = None
    if len(picks) < CONFIG["WATCHLIST_SIZE"]:
        subnote = (f"(وُجد {len(picks)} فقط يطابق الشروط — "
                   f"الحد الأقصى {CONFIG['WATCHLIST_SIZE']})")
    msg = build_message(picks, splits, title=title, subnote=subnote)
    msg += "\n" + build_pullback_section(pull_entries)
    send_telegram(msg)
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
        run_performance_system(picks)
    except Exception as e:
        log(f"⚠️ نظام التتبع: {e}")


def merge_pullback(wl: dict, hist: dict, exclude: set, today_iso: str) -> None:
    """يدمج مرشّحي الارتداد الجدد في القائمة المستقلة (يُضيف فقط، لا يحذف).
    لا يُكرّر سهماً موجوداً، ويحترم الحد الأقصى."""
    if not CONFIG.get("PULLBACK_WATCH", False):
        return
    existing = {e["symbol"] for e in wl.get("pullback", [])}
    active = [e for e in wl.get("pullback", []) if e.get("status") != "triggered"]
    space = CONFIG.get("PULLBACK_SIZE", 10) - len(active)
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


def run_daily_watchlist(wl: dict) -> None:
    """يومي (غير الجمعة): قائمة ثابتة دائمة — تُتابَع وتُضاف لها الجديد فقط،
    ولا يُحذف منها سهم إلا بستوب/هدف. سوق مقفل = نفس القائمة (تنمو، ما ترفرف)."""
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
    # 3) متابعة القائمة الحالية (تُحذف فقط بستوب/هدف؛ نقص البيانات = تُبقى)
    stopped_today = update_watchlist_status(wl, hist)
    # 4) إضافة الجديد دون حذف القديم (حتى حد القائمة)
    held = {s["symbol"] for s in wl["stocks"]}
    stopped = {rm["symbol"] for rm in wl["removed"]
               if rm.get("status") == "stopped"}
    space = CONFIG["WATCHLIST_SIZE"] - len(wl["stocks"])
    added = []
    if space > 0:
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
    # 6) دمج قائمة الارتداد الجديدة (تُضاف فقط) + التنبيه عند وصول الدعم
    try:
        merge_pullback(wl, hist, held | stopped, today_iso)
    except Exception as e:
        log(f"⚠️ دمج الارتداد: {e}")
    pull_triggered = []
    try:
        pull_triggered = monitor_pullback(wl)
    except Exception as e:
        log(f"⚠️ متابعة الارتداد: {e}")
    # 7) الرسالة
    splits = []
    msg = build_daily_message(wl, splits, stopped_today, added, promoted)
    watching = [e for e in wl.get("pullback", [])
                if e.get("status") != "triggered"]
    pull_sec = build_pullback_section(watching, pull_triggered)
    if pull_sec:
        msg += "\n\n" + pull_sec
    send_telegram(msg)
    save_watchlist(wl)
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


# ==========================================================
# 10) التشغيل الرئيسي
# ==========================================================
def main():
    log(f"بدء الفحص — الوضع: {MODE}")
    today = dt.date.today()
    force = os.environ.get("FORCE_RENEW", "").strip() == "1"
    wl = load_watchlist()
    if should_renew(wl, today, force):
        why = ("إجبار يدوي" if force else
               ("تجديد الجمعة" if today.weekday() == WEEKLY_RENEW_DAY
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
WEEKLY_REPORT_DAY = 4                # 4 = الجمعة (الاثنين = 0) — غيّره إن أردت

STATUS_AR = {
    "hit_t1": "✅ حقق الهدف 1",
    "hit_t2": "✅✅ حقق الهدف 2",
    "hit_t3": "🏆 حقق الهدف 3",
    "stopped": "🛑 ضرب الستوب",
    "expired": "⌛ انتهى التتبع (30 يوم)",
}


def git_save(filenames):
    """يرفع ملفات البيانات إلى الـ repo حتى لا تضيع بين تشغيلات GitHub Actions"""
    try:
        os.system('git config user.email "bot@screener.local"')
        os.system('git config user.name "Screener Bot"')
        added = False
        for fn in filenames:
            if os.path.exists(fn):
                os.system(f'git add "{fn}"')
                added = True
        if not added:
            return
        if os.system("git diff --cached --quiet") == 0:
            log("ℹ️ لا تغييرات جديدة للحفظ")
            return
        os.system(f'git commit -m "bot data {dt.date.today().isoformat()}"')
        # HEAD:main يضمن الدفع حتى لو كان checkout بوضع detached
        if os.system("git push origin HEAD:main") == 0:
            log("✅ حُفظت بيانات التتبع في الـ repo")
        else:
            log("⚠️ git push فشل — تأكد من permissions: contents: write في YML")
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
        with open(TRACK_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
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
            "price": round(r["price"], 4),
            "stop": round(r["stop"][0], 4),   # الوقف الأبعد (2% تحت القاع)
            "t1": round(r["t1"], 4),
            "t2": round(r["t2"], 4),
            "t3": round(r["t3"], 4),
            "score": r["score"],
            "flags": r["flags"],
            "ready": r["ready"],
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
            age = (dt.date.today() - dt.date.fromisoformat(a["date"])).days
            # التنبيه صدر اليوم (أو تاريخه بالمستقبل) — ما في جلسة جديدة بعده
            # لمتابعتها؛ نتخطّاه (وإلا نطلب start=بكرة > end=اليوم = خطأ Yahoo).
            if age < 1:
                continue
            # نبدأ من اليوم التالي للتنبيه (التنبيه صدر بعد إغلاق يومه)
            start = (dt.date.fromisoformat(a["date"])
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
            entry = float(a["price"])
            if len(highs):
                a["max_gain_pct"] = round(
                    (float(np.max(highs)) / entry - 1.0) * 100.0, 1)

            best, status, when = 0, None, None
            for i in range(len(df)):
                day = str(df.index[i].date())
                # الستوب أولاً = افتراض محافظ
                # (إلا إذا حقق هدفاً قبله، فالصفقة رابحة أصلاً)
                if lows[i] <= a["stop"] and best == 0:
                    status, when = "stopped", day
                    break
                if highs[i] >= a["t3"]:
                    best, when = 3, day
                    break
                if highs[i] >= a["t2"] and best < 2:
                    best, when = 2, day
                elif highs[i] >= a["t1"] and best < 1:
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


def run_performance_system(results):
    data = load_alerts()
    updates = update_tracking(data)      # 1) تابع التنبيهات القديمة
    record_new_alerts(data, results)     # 2) سجّل تنبيهات اليوم
    save_alerts_file(data)               # 3) احفظ السجل محلياً
    if updates:
        send_telegram(tracking_message(updates))
    if dt.date.today().weekday() == WEEKLY_REPORT_DAY:
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
