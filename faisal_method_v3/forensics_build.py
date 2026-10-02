# -*- coding: utf-8 -*-
"""
🔬 FAISAL METHOD V3 — بناءُ الطبقة الجنائيّة (قراءةٌ فقط · لا يمسّ الإنتاج).

يقرأ: `image_corpus.json` (من corpus_build.py) · `FAISAL_SOURCE_LEDGER.md` (الدفتر القائم).
يكتب: `pattern_catalog.json` · `rule_graph.json` · `evidence_matrix.json` · `target_forensics.json`
       · `data/visual_review.json` (المراجعةُ البصريّة لهذه المهمّة).

⚖️ ثلاثُ طبقاتٍ لا تُخلط (§14): **observation** (ما في الصورة حرفًا) · **interpretation**
(قراءتي) · **rule** (قاعدةٌ قابلةٌ للتنفيذ) — ولكلّ قاعدةٍ وسمُ مصدرٍ من الدفتر (الستّة) ووسمُ
دليلٍ من سلّم المهمّة (§12):
  CONFIRMED  = بلفظ فيصل في وحدتين مستقلّتين فأكثر (بعد إزالة التكرار) أو بلفظه مع مثالٍ مطبَّقٍ منه
  SUPPORTED  = بلفظه في وحدةٍ واحدة
  PROBABLE   = استنتاجٌ متّسقٌ من أمثلته (faisal_inferred) أو تبنٍّ متكرّر (faisal_adopted)
  POSSIBLE   = مادّةُ طرفٍ ثالث نشرها فيصل أو قناةٌ تعليميّة · أو مصدرٌ ثانويّ وحدَه (دليلُ الـPDF)
  CONTRADICTED = يناقضه نصٌّ لفيصل
  UNKNOWN    = بلا دليلٍ فيصليّ (قرارٌ هندسيّ أو بلا سند)
🔴 CONFIRMED تعني «ثابتٌ أنه من منهج فيصل» — **لا** «مربح». الربحيّةُ في `quant_status` من التجارب المسجَّلة.
"""
import json
import os
import re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "faisal_method_v3")
LEDGER = os.path.join(ROOT, "FAISAL_SOURCE_LEDGER.md")
TAGS = ("faisal_verbatim", "faisal_inferred", "faisal_adopted", "engineering", "third_party", "unsourced")
STATUSES = ("CONFIRMED", "SUPPORTED", "PROBABLE", "POSSIBLE", "CONTRADICTED", "UNKNOWN")

# ── أدلّةٌ خارج المدوَّنة (لا ملفَّ لها في faisal_images · تُستشهَد وصفًا) ─────────────
EXTERNAL = {
    "PDF_B_p25": "دليل طريقة فيصل (PDF · لا يُدفَع) ص25 — «قاعدة فيصل في DXST: رسم النموذج عبر فريم 30 دقيقة لتقليل الضجيج · حدد خط العنق عند 2.86 · طلب ثبات فوقه أكثر من ربع ساعة · بعدها توقع اختبار 3.11، وفعلًا وصل تقريبًا 3.10»",
    "PDF_B_p26": "الدليل ص26 — «لا تدخل لأنك رأيت W فقط. انتظر كسر خط العنق والثبات فوقه»",
    "PDF_B_p52": "الدليل ص52 — لقطةُ منشورٍ لفيصل: «ضرب المقاومه الان 3.11 · وصل 3.10 · طاب مساكم كان هذا شرح في مباشر للجميع كان تطبيق عملي للنماذج · حقق نسبة 25٪ · ليته صابر خضير كان ربح» (DXST)",
    "PDF_B_p27": "الدليل ص27 — «كل موجة قد تعطي 20% إلى 40% إذا دخلت من الدعم · ادخل قرب قاع الموجة، لا في منتصفها»",
    "PDF_B_p76": "الدليل (جدول التغريدات · HTCR) — «حقق 50% صعود أول، فالدخول الآن قد يكون مطاردة · إما اختبار 2.50/2.30/2.00 وثبات أو اختراق 3.70/3.90 بثبات» · و«إذا حقق السهم 50% أو أكثر ينتظر Retest أو سحب سيولة»",
    "PDF_B_MWC": "الدليل (MWC) — «وضع مستهدف هبوط 2.35؛ وهو غالباً نصف 4.70 · هنا ليس دعماً تاريخياً لأن السهم لم يصل له سابقاً؛ هو مستهدف غسل/قاع أدنى محتمل إذا فشل القاع الأول»",
    "UPL_933a9f58": "مرفقُ محادثة (لا يُدفَع · من مُعرِّف الشارت) — منشورُ فيصل 2026/9/24 5:47: «هذا سهم سابق الجميع ربح فيه · الدعم والقاع 2.10 اخذنا دفعه بسيط · قبل يصعد بمشعه هبط فيه الى 1.78 · مباشره دخلنا بكل الكمية المقرره للدخول · ثاني يوم دبل»",
}

# ── المراجعةُ البصريّة لهذه المهمّة (observation حرفًا · لا تفسير هنا) ───────────────────
VISUAL_REVIEW = {
    "TG_58042": {"source_class": "EDU_THIRD_PARTY", "author": "قناةٌ تعليميّة غيرُ مسمّاة (لقطةُ بحثٍ «نموذج» في تلغرام · 13 من 19)",
                 "same_source_group": "SG-58042", "ticker": None, "timeframe": None, "pattern": "W / double bottom",
                 "observation": "رسمٌ يدويّ «نمط W»: «كسر الدعم» · «المقاومة» (دائرةٌ على تقاطع الترند الهابط والخطّ الأفقيّ) · «المطرقة» بين القاعين · «الدخول» (دائرةٌ على كسر الترند الهابط تحت الخطّ الأفقيّ) · «ستوبلوس» تحته · سهمٌ «100%» من مستوى الدخول إلى «الهدف» · سهمٌ «50%» من تحت الدخول إلى القاع الثاني · ونصٌّ: «نموذج W أو القاع المزدوج من أقوى نماذج انعكاس الاتجاه من هبوط إلى صعود · يتكون بعد نزول قوي عندما يفشل السعر بكسر القاع مرتين · ظهور شمعة المطرقة قرب القاع يعطي إشارة مبكرة لدخول المشترين (الثيران) بدؤ بالسيطرة · خط العنق (Neckline) يمثل المقاومة أو القمة بين القاعين · اختراق خط العنق مع كسر الترند الهابط يعتبر إشارة قوة عالية · الدخول يكون بعد إغلاق شمعة فوق المقاومة والترند الهابط»",
                 "drawn_levels": {"entry": "كسر الترند الهابط", "stop": "تحت الدخول", "target": "أعلى السهم 100%"},
                 "fifty_hundred": "100% = سهمٌ من الدخول إلى الهدف · 50% = سهمٌ من مستوى الوقف/الدخول إلى القاع الثاني · الرسمُ ليس بمقياس (مقيسٌ بالبكسل: 0.91 و0.72 من الارتفاع)"},
    "TG_58043": {"source_class": "EDU_THIRD_PARTY", "same_source_group": "SG-58042", "pattern": "W / double bottom",
                 "observation": "تتمّةُ النصّ نفسِه: «الدخول يكون بعد إغلاق شمعة فوق المقاومة والترند الهابط · وقف الخسارة أسفل آخر قاع أو أسفل منطقة الاختراق · الهدف يقاس بمسافة القاع إلى خط العنق ثم تضاف فوق نقطة الاختراق · أهم نقطة: لا تدخل قبل تأكيد الإغلاق لتجنب الاختراقات الكاذبة · نماذج الشموع»"},
    "TG_58044": {"source_class": "FAISAL_REPOST_THIRD_PARTY", "author": "فيصل @kisar_ · 2026/2/11 10:15 م · 3 آلاف مشاهدة",
                 "pattern": "W / M", "observation": "«نماذج التداول الشهيره W M» ‏+ إنفوغراف «M AND W PATTERNS» (شعارُ خوذة): Simple M · Extended M · Short formed M · Simple W · Short formed W · Extended W — الدخولُ مُعلَّمٌ عند كسر مستوى القمّة/القاع الأوسط (العنق)"},
    "TG_58045": {"source_class": "FAISAL_VERBATIM", "author": "فيصل (منشور X · التاريخُ غيرُ ظاهر)", "ticker": "VEEE", "timeframe": "4h",
                 "pattern": "W vs M decision band", "observation": "«هل يصعد ويكمل نموذج W الاجابي ام يهبط ويكون نموذجً M السلبي - مقرون 6.18> 6.34 > ادناهما سلبي اعلاهما اجابي -» · الشارت: قمّة 9.67 · قاع 5.00 · خطوط 8.76 (أسود) · 8.27 (بنفسجيّ) · 7.27 (أسود) · 6.57 (أسود) · 6.34 (بنفسجيّ) · 6.18 (أحمر) · 5.34 (أحمر) · 3.54 (بنفسجيّ) · مسارٌ بنفسجيّ متعرّج (W) يصعد فوق 10 · ومسارٌ أحمر يهبط إلى 5.34 · بعد الإغلاق 6.89 ‏+1.92% · KST(10,15,20,30,10,10,10,15,9) · MACD(12,26,9)",
                 "drawn_levels": {"band_low": 6.18, "band_high": 6.34, "bear_target": 5.34, "resistances": [6.57, 7.27, 8.27, 8.76]}},
    "TG_58046": {"source_class": "FAISAL_VERBATIM", "author": "فيصل · 2026/6/30 5:34 ص · ألفا مشاهدة", "ticker": "EZRA", "timeframe": "D",
                 "pattern": "butterfly + W", "observation": "«نموذج الفراشه المتوقع اذا صدق التحليل مع نموذج W · 5.40 خطوره السهم اما بالهبوط او الصعود» · الشارت اليوميّ: قمّة 5.450 · قاع 3.030 · خطوط 5.433 · 3.994 · 3.430 (بنفسجيّة) · السعر 3.260 · فراشةٌ مرسومة: 5.45 ⟵ 3.25 ⟵ 3.994 ⟵ 3.03 ⟵ 5.433 · FSTO(14,3) · CCI(14)",
                 "drawn_levels": {"risk_level": 5.40, "x_top": 5.45, "low": 3.03, "mid": 3.994, "projection": 5.433}},
    "TG_58047": {"source_class": "OTHER_USER", "author": "@xzdixz · 2026/6/16", "ticker": "DXST", "timeframe": "4h",
                 "observation": "«ابشر حالياً شورته ٣٠٠٠ · عنده دعمين الي ب الاحمر و المقاومة عند ٣.١٩ ما قدر يثبت فوقها من الهبوط و الأهداف ب الازرق و مقاومه عنده ٤.١٤ سابقه» · خطوط 5.469 (أحمر) · 4.145 (أسود) · 3.905 · 3.352 (أزرق) · 3.195 (أسود) · 2.632 · 2.298 (أحمر) · قمّة 5.480 · قاع 2.280 · EMA(5,10,20) · RSI 46.67",
                 "note": "متابعٌ يطبّق مفتاحَ ألوان فيصل (أحمر دعم · أسود مقاومة · أزرق هدف) — ليس فيصل"},
    "TG_58048": {"source_class": "FAISAL_VERBATIM", "author": "فيصل · اقتباسٌ لمنشور @xzdixz (2026/6/16)", "ticker": "DXST",
                 "pattern": "W", "observation": "«نحتاج رسم مثلث W ع فريم 30 دقيقه مع تحديد خط العنق» — «مثلث» حرفًا (قد تكون «مثل»؛ والدليلُ الثانويّ ص25 يقرؤها «رسم W عبر فريم 30 دقيقة»)"},
    "TG_58049": {"source_class": "FAISAL_VERBATIM", "author": "فيصل ($ATMV)", "ticker": "ATMV",
                 "observation": "«فنيا > عنده ترند هابط 6.70 - اذا ارتد وحافظ عليها ذكرني - ثباته + اقفال يومي على 8.76 مهم - مقاومه 13.47 الزخم يحدد اتجاه السهم - بالنسبه لي حاليا لايوجد اي شمعة تأكد الصعود - خطاي اكثر من صوابي لاتبني عليه» · خطوط 22.20 · 20.49 · 18.48 · 13.47 · 9.92 · 8.76 (سوداء) · 16.03 · 14.36 (زرقاء) · 6.71 · 5.40 (حمراء) · RSI14 50.69"},
    "TG_58050": {"source_class": "FAISAL_REPOST_THIRD_PARTY", "author": "فيصل · 2025/12/7 2:09 ص", "pattern": "W / M",
                 "observation": "«اشهر النماذج بالاسهم حرف M هبوطي حرف W صعودي» ‏+ نتيجةُ بحثٍ في TradingView «Double Top & Double Bottom (EDU) by RocketBomb» ومصغّراتُ Equiti (سهمان متساويان: من القاع إلى العنق ومن العنق إلى الهدف) وFXMaroc"},
    "TG_58051": {"source_class": "EDU_THIRD_PARTY", "pattern": "W / M", "observation": "رسمُ «Double bottom / Double top / Neckline» عامّ — نسخةٌ من EDU_20260918_10_pattern"},
    "TG_58052": {"source_class": "FAISAL_VERBATIM", "author": "فيصل · 2026/2/14 5:17 م · 6 آلاف مشاهدة", "pattern": "Elliott ABC + Wyckoff labels",
                 "observation": "«البعض ارسلي عن موجات اليوت · التحليل عدة مدارس · كلها تتفق في الدعوم والارتداد · دعم 1 · عنق · دعم 2 دخول · منطقة تراكم صعود · منطقة توزيع ( تصريف كميات مضارب ) 3-5 · غالبا السهم اذا صعد له 3 رؤوس 2 ارتداد سبق ذكرتها · الهبوط نفس الشي» ‏+ إنفوغراف «Elliot_wave ABC pattern · Art of chart»: PS · AR · ST · (A) · B · (B) %61 %50 · C · (C) · 1-5 · Resistance · Support"},
    "X_20260918_12_doublebottom": {"source_class": "FAISAL_VERBATIM", "author": "فيصل (منشور X)", "pattern": "W / double bottom",
                 "observation": "«لازال لم يتخبر القاع المزدوج · هذا السهم راح يمشي ع موجات اليوت · الان سلوكه يتبع نماذج فنيه - الضغط لابد منه - خط العنق بعد الضغط = تحرر - بالنسبه لي السهم مازال تحت الاجابيه انتظر فرصه دخول مناسبه - الدخول بين خط العنق والقاع المزدوج غير امن - المحللين ( الفاهمين العارفين الدارسين عن علم ) يبحث عن فرصه دخول عند سحب السيوله او عند اول اختراق صحيح - ضبابيه الدخول بين وبين ليست جيده -»"},
    "EDU_20260918_44_doublebottom": {"source_class": "EDU_THIRD_PARTY", "pattern": "W / double bottom",
                 "observation": "«عائد مرتفع مخاطرة منخفضة · استراتيجية الشراء عند القاع المزدوج» · الإشارات: اتجاه هابط سابق · تكوين قاع مزدوج · اختراق خط العنق · إعادة اختبار خط العنق · استمرار الاتجاه الصاعد · تأكيد الدخول: اختراق صعودي · إعادة اختبار · سلوك صاعد · شمعة صاعدة قوية · زخم شرائي · الخطة: الدخول عند إعادة اختبار خط العنق · وقف الخسارة أسفل أدنى إعادة اختبار · الهدف أقرب مقاومة أو سيولة الشراء"},
    "TG_57862": {"source_class": "FAISAL_VERBATIM", "author": "فيصل (اقتباسٌ لمنشوره 2026/9/11 «اضافة كميات مع الضغط»)", "ticker": "SXTC",
                 "observation": "«عدة اساله عن sxtc · جني الربح عند مقاومه 3 > باكثر من 70٪ من الكميه · ليش · الصفقه ممكن تنعكس عليك ويفشل السهم يروح عليك ربح 50٪ · كل الصور باختلاف النماذج رفض الاختراق = هبوط - بعد الاختراق وتاكيد الدعوم يكون دخول جديد» ‏+ إنفوغرافان لطرفٍ ثالث: «التحليل الفني» (وتدٌ/علمٌ صاعدٌ بعد هبوط · كسرٌ ثمّ إعادة اختبار ثمّ هبوط) و«دخول فيبوناتشي 50%» (‏100% القمّة · 88.6 · 79 · 70.5 · 50% «كتلة الأوامر» · 0% القاع · دخولٌ عند 50% · RR 1:3)"},
    "TG_57858": {"source_class": "FAISAL_REPOST_THIRD_PARTY", "pattern": "rising wedge/channel → short",
                 "observation": "إنفوغراف «مستوى دخول عند المقاومة»: قناةٌ/وتدٌ صاعد تحت مقاومتين · الدخول عند كسر الحدّ السفليّ · وقف الخسارة فوقه · «نسبة العائد إلى المخاطرة 1.3»"},
    "TG_57860": {"source_class": "FAISAL_REPOST_THIRD_PARTY", "pattern": "bear flag / rising wedge",
                 "observation": "إنفوغراف «التحليل الفني · ما اسم النمط؟»: اتجاه هابط · كسر · خطّا اتجاهٍ صاعدان · إعادة الاختبار · كسر المنطقة ⟵ هبوط"},
    "TG_1985": {"source_class": "FAISAL_VERBATIM", "author": "فيصل", "pattern": "Elliott wave size",
                 "observation": "«اختبر الدعم 2.40 · 2.37 بذيل شمعه · صعد الى 2.87 · 2.87=2.40+20٪ · 20٪ الموجه الثانيه · هكذا تدار الاسهم بنظرية اليوت · هذا السهم حقق النظريه · هناك اسهم تصعد مباشره لاتصلح لها هذي النظريه · لكل سهم سلوك تربح منه» · واقتباس: «باقي موجه في حال اختبر الدعم 2.40 ولافشل تابع عشان تتعلم» · خطوط 3.145 · 2.886 (زرقاء) · 2.504 (حمراء)"},
    "X_20260827_raya_notready": {"source_class": "FAISAL_VERBATIM", "ticker": "RAYA", "observation": "«غير. جاهز فنيا · انتظار الهبوط» (4:44) — مطابقٌ لـ X_20260827_raya_notready_2"},
    "X_20260905_11": {"source_class": "FAISAL_VERBATIM", "ticker": "RAYA", "observation": "«$RAYA اعتقد الشركه مصريه يطبق ماذكر ادناه» (12:25) — منشورٌ آخر"},
    "TG_1908": {"source_class": "FAISAL_VERBATIM", "ticker": "SMX", "observation": "«$SMX تحت المراقبه الان انتظار البري»"},
}

# ── القواعدُ الجديدة من هذه المهمّة (ما لا يغطّيه الدفتر) ─────────────────────────────
NEW_RULES = [
    # W / القاع المزدوج
    {"id": "R-W-01", "category": "pattern", "scope": "W",
     "statement": "القاعُ المزدوج (W) نموذجٌ صاعد والقمّةُ المزدوجة (M) نموذجٌ هابط — وكلاهما من «اشهر النماذج بالاسهم»",
     "source_type": "faisal_verbatim", "supporting": ["TG_58050", "TG_58044", "TG_58045"], "contradicting": []},
    {"id": "R-W-02", "category": "entry", "scope": "W",
     "statement": "الدخولُ بين خط العنق والقاع المزدوج غيرُ آمن («ضبابيه الدخول بين وبين ليست جيده»)",
     "source_type": "faisal_verbatim", "supporting": ["X_20260918_12_doublebottom"], "contradicting": []},
    {"id": "R-W-03", "category": "entry", "scope": "W",
     "statement": "نقطتا الدخول الصحيحتان: عند سحب السيولة (تحت القاع/الدعم) أو عند أوّل اختراقٍ صحيحٍ لخط العنق",
     "source_type": "faisal_verbatim", "supporting": ["X_20260918_12_doublebottom", "UPL_933a9f58", "TG_58052"], "contradicting": [],
     "note": "TG_58052: «دعم 1 · عنق · دعم 2 دخول» = الدخولُ عند الدعم الثاني (القاع الثاني) · UPL_933a9f58 تطبيقٌ: سحبٌ من 2.10 إلى 1.78 ثمّ «دخلنا بكل الكمية» ⟵ «دبل»"},
    {"id": "R-W-04", "category": "breakout", "scope": "W",
     "statement": "خطُّ العنق بعد الضغط = تحرّر («الضغط لابد منه»)",
     "source_type": "faisal_verbatim", "supporting": ["X_20260918_12_doublebottom"], "contradicting": []},
    {"id": "R-W-05", "category": "confirmation", "scope": "W",
     "statement": "تأكيدُ الاختراق: ثباتٌ وتداولٌ فوق خط العنق أكثرَ من ربع ساعة (DXST · العنق 2.86) ثمّ التحرّرُ من المقاومة الثانية (3.11) يعطي 3.30",
     "source_type": "faisal_verbatim", "supporting": ["IMG_0627", "IMG_0628", "PDF_B_p25"], "contradicting": []},
    {"id": "R-W-06", "category": "timeframe", "scope": "W",
     "statement": "يُرسَم الـW على فريم 30 دقيقة مع تحديد خط العنق",
     "source_type": "faisal_verbatim", "supporting": ["TG_58048", "PDF_B_p25"], "contradicting": []},
    {"id": "R-W-07", "category": "invalidation", "scope": "W",
     "statement": "نطاقُ القرار «مقرون»: مستويان متقاربان — الإغلاقُ فوق أعلاهما يكمل W الإيجابيّ وتحت أدناهما يصنع M السلبيّ (VEEE 6.18/6.34)",
     "source_type": "faisal_verbatim", "supporting": ["TG_58045"], "contradicting": []},
    {"id": "R-W-08", "category": "target", "scope": "W",
     "statement": "هدفُ فيصل بعد اختراق العنق مستوياتٌ أفقيّة من سلّم المقاومات (DXST: 3.11 ثمّ 3.30) — لا «ارتفاعُ النموذج»",
     "source_type": "faisal_verbatim", "supporting": ["IMG_0627", "IMG_0628", "PDF_B_p52"], "contradicting": [],
     "note": "النتيجةُ عنده «حقق نسبة 25٪» (PDF_B_p52) · وT-TGT حسب الأهدافَ المرسومة 1.07h و1.82h و3.92h من العنق"},
    {"id": "R-W-09", "category": "target", "scope": "W",
     "statement": "هدفُ W = مسافةُ القاع إلى خط العنق تُضاف فوق نقطة الاختراق (الحركةُ المقيسة 100%)",
     "source_type": "third_party", "supporting": ["TG_58043", "TG_58050"], "contradicting": ["IMG_0627"],
     "note": "طرفٌ ثالث (القناةُ التعليميّة · مصغّرةُ Equiti التي أعاد فيصل نشرَها بلا تعليقٍ على القياس) · وهدفا فيصل في DXST لا يطابقانها (1.07h · 1.82h)"},
    {"id": "R-W-10", "category": "entry", "scope": "W",
     "statement": "الدخولُ بعد إغلاق شمعةٍ فوق المقاومة والترند الهابط · ولا دخولَ قبل تأكيد الإغلاق",
     "source_type": "third_party", "supporting": ["TG_58042", "TG_58043"], "contradicting": [],
     "note": "يطابق نصفَ R-W-03 (الاختراق) ويغفل نصفَه الآخر (سحب السيولة) · ورسمُ الصورة نفسِها يضع «الدخول» على كسر الترند تحت الخطّ الأفقيّ — تناقضٌ داخليّ في المصدر"},
    {"id": "R-W-11", "category": "entry", "scope": "W",
     "statement": "الدخولُ عند إعادة اختبار خط العنق · الوقفُ أسفل أدنى إعادة اختبار · الهدفُ أقرب مقاومة أو سيولة الشراء",
     "source_type": "third_party", "supporting": ["EDU_20260918_44_doublebottom"], "contradicting": []},
    {"id": "R-W-12", "category": "invalidation", "scope": "W",
     "statement": "وقفُ W: أسفل آخر قاع أو أسفل منطقة الاختراق",
     "source_type": "third_party", "supporting": ["TG_58043"], "contradicting": []},
    {"id": "R-W-13", "category": "confirmation", "scope": "W",
     "statement": "شمعةُ المطرقة قرب القاع إشارةٌ مبكرةٌ لدخول المشترين",
     "source_type": "third_party", "supporting": ["TG_58042"], "contradicting": [],
     "quant_status": "T-CANDLE (أيُّ شمعةٍ انعكاسيّة تفصل؟) — فشلت صفرًا من ستّة"},
    {"id": "R-W-14", "category": "pattern", "scope": "W",
     "statement": "الفراشةُ المتوقّعة مع W — ومستوى «خطورة السهم» (5.40) يحسم الاتّجاه صعودًا أو هبوطًا",
     "source_type": "faisal_verbatim", "supporting": ["TG_58046"], "contradicting": [],
     "note": "بلا نِسَبٍ هارمونيّة — هندسةُ الفراشة عنده غيرُ مكتوبة ⟵ UNKNOWN كبنية"},
    # الرقمُ الحرج / الاتّجاه
    {"id": "R-CL-01", "category": "confirmation", "scope": "general",
     "statement": "مستوًى واحدٌ حاسم يُذكر قبل الحركة: الثباتُ والإقفالُ اليوميّ فوقه شرطُ الإيجابيّة («ثباته + اقفال يومي على 8.76 مهم») · وكسرُه سلبيّ",
     "source_type": "faisal_verbatim", "supporting": ["TG_58049", "TG_58046", "TG_58045"], "contradicting": []},
    {"id": "R-CL-02", "category": "confirmation", "scope": "general",
     "statement": "لا دخولَ بلا شمعةٍ تؤكّد الصعود («لايوجد اي شمعة تأكد الصعود»)",
     "source_type": "faisal_verbatim", "supporting": ["TG_58049"], "contradicting": []},
    {"id": "R-CL-03", "category": "structure", "scope": "general",
     "statement": "عبر النماذج كلّها: رفضُ الاختراق = هبوط · وبعد الاختراق وتأكيد الدعوم يكون دخولٌ جديد",
     "source_type": "faisal_verbatim", "supporting": ["TG_57862"], "contradicting": []},
    {"id": "R-TP-01", "category": "risk", "scope": "general",
     "statement": "جنيُ الربح عند المقاومة الثالثة بأكثرَ من 70% من الكمّيّة — لأن الصفقة قد تنعكس فيضيع ربح 50%",
     "source_type": "faisal_verbatim", "supporting": ["TG_57862"], "contradicting": [],
     "quant_status": "محورُ إدارة الخروج مُغلَقٌ مُنفَّذًا (TRAIL_REOPEN) — T-EXIT/T-EXITMGMT/T-TRAIL"},
    # إليوت · المدارس الثلاث
    {"id": "R-EL-01", "category": "structure", "scope": "elliott",
     "statement": "التحليلُ يدمج ثلاثَ مدارس: موجات إليوت ‏+ وايكوف ‏+ الكلاسيكيّ (دعم/مقاومة) — «كلها تتفق في الدعوم والارتداد»",
     "source_type": "faisal_verbatim", "supporting": ["TG_50584", "TG_58052"], "contradicting": []},
    {"id": "R-EL-02", "category": "structure", "scope": "elliott",
     "statement": "خريطةُ الدورة: دعم 1 ⟵ عنق ⟵ دعم 2 (دخول) ⟵ منطقةُ تراكمٍ صعودًا ⟵ منطقةُ توزيعٍ 3-5 (تصريفُ كمّيّات المضارب)",
     "source_type": "faisal_verbatim", "supporting": ["TG_58052"], "contradicting": []},
    {"id": "R-EL-03", "category": "structure", "scope": "elliott",
     "statement": "غالبًا السهمُ إذا صعد له 3 رؤوس وارتدادان · والهبوطُ مثلُه",
     "source_type": "faisal_verbatim", "supporting": ["TG_58052"], "contradicting": []},
    {"id": "R-EL-04", "category": "target", "scope": "elliott",
     "statement": "الموجةُ نحو 20% من الدعم المُختبَر (2.40 ⟵ 2.87 = ‏+20% «الموجة الثانية»)",
     "source_type": "faisal_verbatim", "supporting": ["TG_1985", "PDF_B_p27"], "contradicting": [],
     "note": "والدليلُ الثانويّ: «كل موجة قد تعطي 20% إلى 40% إذا دخلت من الدعم» · وفيصل نفسُه: «هناك اسهم تصعد مباشره لاتصلح لها هذي النظريه»"},
    {"id": "R-EL-05", "category": "entry", "scope": "elliott",
     "statement": "ادخل قرب قاع الموجة لا في منتصفها",
     "source_type": "faisal_adopted", "supporting": ["PDF_B_p27", "X_20260918_12_doublebottom"], "contradicting": [],
     "note": "النصُّ من الدليل الثانويّ · ويوافقه لفظُ فيصل «الدخول بين خط العنق والقاع المزدوج غير امن»"},
    # 50٪ و100٪ (مختصرٌ من target_forensics)
    {"id": "R-50-01", "category": "entry", "scope": "general",
     "statement": "إذا حقّق السهمُ صعودًا أوّلَ ‏+50% فلا مطاردة — انتظار اختبار دعمٍ أو سحب سيولة",
     "source_type": "faisal_verbatim", "supporting": ["IMG_8242", "TG_2108", "PDF_B_p76"], "contradicting": [],
     "note": "IMG_8242 «50٪ تمت بصعود اول ✅ · انتظار اختبار دعم او سحب سيولة 2 > 2.30» · TG_2108 «حقق 5 تقريبا > 50٪ · الرجل المشنوق · انتظر تكوين دعوم»"},
    {"id": "R-100-01", "category": "target", "scope": "general",
     "statement": "«100٪» مقرونةً بـ«هدف» عند فيصل = ربحٌ ‏+100% (ضعفُ سعر الدخول/القاع) — لا 100% من ارتفاع النموذج",
     "source_type": "faisal_verbatim", "supporting": ["IMG_0151", "IMG_0153", "TG_2173"], "contradicting": [],
     "note": "حكمُ T-TGT (hs_forensic/TARGET_FORENSICS.md §②)"},
    # البنية
    {"id": "R-ST-01", "category": "structure", "scope": "general",
     "statement": "مفرداتُ البنية عند فيصل: «قاع جديد» · «قاع ادنى» · «قمة اعلى» · و«كسر القاع ⇒ تحليلٌ جديد بنفس النهج»",
     "source_type": "faisal_verbatim", "supporting": ["IMG_8127", "X_20260905_10"], "contradicting": [],
     "note": "مصطلحا BOS/CHoCH: صفرُ استعمال في المدوَّنة ⟵ لا يُنسبان إليه"},
]

# ── معاني «50٪» و«100٪» — §10 ──────────────────────────────────────────────────────
TARGET_MEANINGS = {
    "50": [
        {"id": "F50-1", "meaning": "صعودٌ أوّلُ ‏+50% تحقّق ⟵ لا مطاردة · انتظار اختبار دعم أو سحب سيولة", "kind": "anti_chase_trigger",
         "source_type": "faisal_verbatim", "evidence": ["IMG_8242", "TG_2108", "PDF_B_p76"], "status": "CONFIRMED"},
        {"id": "F50-2", "meaning": "ربحٌ 50% قد يضيع إذا انعكست الصفقة ⟵ جنيٌ مبكّر عند المقاومة الثالثة (أكثر من 70%)", "kind": "profit_at_risk",
         "source_type": "faisal_verbatim", "evidence": ["TG_57862"], "status": "SUPPORTED"},
        {"id": "F50-3", "meaning": "متوسّطُ حركةٍ 50 يدلّ على صعودٍ «أقلها من 30 لـ50٪»", "kind": "expected_move_range",
         "source_type": "faisal_verbatim", "evidence": ["TG_1809"], "status": "SUPPORTED",
         "note": "IMG_0097 (doc_only) تكرّرها · والإنتاج: faisal_move 30-50%"},
        {"id": "F50-4", "meaning": "÷2 في وصفة المقسّم: مستهدفُ الهبوط نصفُ قمّة ما بعد التقسيم", "kind": "halving_downside_target",
         "source_type": "faisal_verbatim", "evidence": ["IMG_0150", "IMG_0151", "IMG_0153"], "status": "CONFIRMED"},
        {"id": "F50-5", "meaning": "MWC: مستهدفُ هبوطٍ 2.35 = نصفُ القاع الأوّل 4.70 لسهمٍ بلا تاريخ (طرحٌ جديد)", "kind": "halving_downside_target",
         "source_type": "faisal_inferred", "evidence": ["IMG_8127", "PDF_B_MWC"], "status": "PROBABLE",
         "note": "فيصل كتب الرقمَ 2.35 · وعلاقةُ «النصف» حسابُنا (والدليلُ الثانويّ يقولها)"},
        {"id": "F50-6", "meaning": "تصحيحُ فيبوناتشي 50% منطقةُ دخول (كتلةُ أوامر)", "kind": "fib_retracement",
         "source_type": "third_party", "evidence": ["TG_57862", "TG_58052"], "status": "POSSIBLE",
         "note": "إنفوغرافان لطرفٍ ثالث أرفقهما فيصل (وأحدُهما بيعٌ على المكشوف) · بلا قاعدةٍ بلفظه"},
        {"id": "F50-7", "meaning": "سهمُ «50%» في رسم W للقناة التعليميّة (من الوقف/الدخول إلى القاع الثاني)", "kind": "drawing_label",
         "source_type": "third_party", "evidence": ["TG_58042"], "status": "UNKNOWN",
         "note": "الرسمُ يدويّ وليس بمقياس (0.72 من الارتفاع بالبكسل) والنصُّ لا يذكر 50% ⟵ المعنى الهندسيّ غيرُ قابلٍ للحسم"},
        {"id": "F50-8", "meaning": "إغلاقٌ فوق مستوى 50% من الشمعة الأولى (Three Inside Up)", "kind": "candle_midpoint",
         "source_type": "third_party", "evidence": ["EDU_20260918_56_three_inside_up"], "status": "POSSIBLE"},
        {"id": "F50-9", "meaning": "مقاديرُ وصفيّة: «خساره 50٪» لمن دخل مع القروب · «10 الاف دولار ترفعه 50٪» · «متعدي 50٪» في ثواني", "kind": "descriptive_magnitude",
         "source_type": "faisal_verbatim", "evidence": ["TG_50817", "IMG_0506"], "status": "CONFIRMED",
         "note": "وصفٌ لا قاعدة"},
        {"id": "F50-10", "meaning": "هويّةُ سهم الارتكاز: انهيارٌ 50% فأكثر بعد الانفجار (بوّابةُ الفارز M2)", "kind": "identity_threshold",
         "source_type": "engineering", "evidence": [], "status": "UNKNOWN",
         "note": "الدفتر: بوّابات الهويّة صفرُ faisal_verbatim · والنافذُ اليوم ظرفُ الكاتالوج ≈71.7"},
    ],
    "100": [
        {"id": "F100-1", "meaning": "هدفٌ = ربحٌ ‏+100% (ضعفُ السعر)", "kind": "gain_distance",
         "source_type": "faisal_verbatim", "evidence": ["IMG_0151", "IMG_0153", "TG_2173"], "status": "CONFIRMED", "note": "T-TGT L1-L3"},
        {"id": "F100-2", "meaning": "ربحٌ متحقّق أو كامن («دبل الان فوق 100٪» · «$sphl 100%» · «حقق 100%» · «في بطنه فوق 100٪»)", "kind": "realized_gain",
         "source_type": "faisal_verbatim", "evidence": ["TG_2199", "TG_57892", "IMG_0647"], "status": "CONFIRMED"},
        {"id": "F100-3", "meaning": "صفقاتُه الارتكازيّة «تعتمد ع ربح يتجاوز 100٪»", "kind": "strategy_goal",
         "source_type": "faisal_verbatim", "evidence": ["X_20260827_indicators_canf"], "status": "SUPPORTED"},
        {"id": "F100-4", "meaning": "فيبوناتشي النطاق الكامل: 100% = قمّةُ الدورة السابقة (SPRC 4.30 ⟵ 11.84)", "kind": "fib_full_range",
         "source_type": "faisal_verbatim", "evidence": ["IMG_9933"], "status": "SUPPORTED", "note": "IMG_9933 doc_only (الصورةُ غائبة · وصفُها في الكاتالوج)"},
        {"id": "F100-5", "meaning": "«اضمن لك 100٪ بكل صفقه» — صيغةُ ضمانٍ بلا «هدف»", "kind": "rhetoric",
         "source_type": "faisal_verbatim", "evidence": ["TG_50589"], "status": "UNKNOWN", "note": "T-TGT L12: المعنى غيرُ قابلٍ للحسم"},
        {"id": "F100-6", "meaning": "100% من ارتفاع النموذج يُسقَط فوق نقطة الاختراق (الحركةُ المقيسة)", "kind": "measured_move",
         "source_type": "third_party", "evidence": ["TG_58043", "TG_58050", "TG_58042"], "status": "POSSIBLE",
         "note": "لفظُ القناة التعليميّة ومصغّرةٌ أعاد فيصل نشرَها · وصفرُ استعمالٍ بلفظه · وهدفا DXST عنده 1.07h و1.82h"},
        {"id": "F100-7", "meaning": "«100٪ مضمونه عند 5» — يقينٌ لا مسافة (5 من 3.16 = ‏+58%)", "kind": "certainty",
         "source_type": "faisal_verbatim", "evidence": ["IMG_0587"], "status": "SUPPORTED", "note": "T-TGT L8"},
    ],
}

# ── كتالوج النماذج ──────────────────────────────────────────────────────────────────
PATTERNS = [
    {"id": "P01", "name": "دورةُ الارتكاز (انفجار ⟵ انهيار ⟵ قاعٌ متشبّع ⟵ اشتعال)", "status": "CONFIRMED",
     "faisal": ["IMG_0151", "IMG_0153", "TG_2043", "TG_2062"], "third_party": [], "rules": ["ledger: M1-M14 · الوقف · الدفعات"],
     "quant": "الفارزُ الإنتاجيّ نفسُه — والأحكامُ في DECISIONS_ARCHIVE (لا رابطَ قبل الانفجار داخل المؤهَّلين · نسبة 2025 الحيّة 25.9%)",
     "note": "المفهومُ لفيصل · والعتباتُ الرقميّة للهويّة هندسيّة/مستنتجة (الدفتر)"},
    {"id": "P02", "name": "W / القاعُ المزدوج", "status": "CONFIRMED",
     "faisal": ["X_20260918_12_doublebottom", "TG_58045", "TG_58048", "IMG_0627", "IMG_0628", "TG_58052", "UPL_933a9f58"],
     "faisal_repost": ["TG_58044", "TG_58050", "TG_50589"],
     "third_party": ["TG_58042", "TG_58043", "EDU_20260918_44_doublebottom", "EDU_20260918_10_pattern", "TG_58051"],
     "other_user": ["TG_58047"],
     "rules": ["R-W-01", "R-W-02", "R-W-03", "R-W-04", "R-W-05", "R-W-06", "R-W-07", "R-W-08", "R-W-09", "R-W-10", "R-W-11", "R-W-12", "R-W-13"],
     "quant": "لم يُقَس قطّ في المشروع ⟵ T-W مسجَّلٌ في هذه المهمّة (faisal_method_v3/T_W_prereg.md)",
     "note": "التعارضُ الحقيقيّ: الطرفُ الثالث يقيس الهدفَ بارتفاع النموذج (R-W-09) وفيصل بسلّم المقاومات (R-W-08)"},
    {"id": "P03", "name": "M / القمّةُ المزدوجة", "status": "SUPPORTED",
     "faisal": ["TG_58045"], "faisal_repost": ["TG_58044", "TG_58050"], "third_party": ["EDU_20260918_10_pattern"],
     "rules": ["R-W-01", "R-W-07"], "quant": "لا قياس",
     "note": "عند فيصل سيناريو سلبيّ يُتجنَّب (لا يبيع على المكشوف) — كسرُ أدنى نطاق القرار"},
    {"id": "P04", "name": "الرأسُ والكتفان (المقلوب الصاعد · والقمّة)", "status": "SUPPORTED",
     "faisal": ["TG_2197", "X_20261001_HS_03_LS", "CH_20261001_HS_01_DRMA", "CH_20261001_HS_02_DCOY"], "faisal_repost": ["TG_50589"], "third_party": [],
     "rules": ["hs_forensic/RULE_AUDIT.md"],
     "quant": "مُغلَقٌ مُنفَّذًا (HSFX_REOPEN) — T-HS «لا ميزة على الضبط» · T-HS-FX «لا ميزةَ تداوليّة» · T-HS-RX «لا ميزةَ حتى بالبناء الأمين» · وT-TGT للهدف",
     "note": "محفوظٌ كما هو — لا يُعاد فتحُه هنا (§22)"},
    {"id": "P05", "name": "موجاتُ إليوت (تسميةٌ تشغيليّة)", "status": "CONFIRMED",
     "faisal": ["TG_1985", "TG_58052", "TG_50577", "TG_50584", "X_20260918_12_doublebottom"], "third_party": ["TG_50821", "TG_50822", "TG_50823"],
     "rules": ["R-EL-01", "R-EL-02", "R-EL-03", "R-EL-04", "R-EL-05"],
     "quant": "T-WAVES (موجاتُ التوقيت داخل الجلسة) الفرعُ 2 ومُغلَق — دعوى أخرى غيرُ حجم الموجة",
     "note": "دليلُ إليوت (PDF · 57 ص) ملخّصُه FAISAL_ELLIOTT_NOTES.md"},
    {"id": "P06", "name": "وايكوف (تجميع · ربيع · توزيع)", "status": "SUPPORTED",
     "faisal": ["TG_50584", "TG_58052"], "faisal_repost": ["TG_50599"], "third_party": ["TG_50595"],
     "rules": ["R-EL-01", "R-EL-02"], "quant": "لا قياس مباشر · و«الربيع» يقابله سحبُ السيولة (P07)",
     "note": "خريطةُ TG_58052 تحمل رموزَ وايكوف (PS · AR · ST) مع ABC إليوت"},
    {"id": "P07", "name": "سحبُ السيولة (كنسٌ تحت الدعم ثمّ استرداد)", "status": "CONFIRMED",
     "faisal": ["IMG_0297", "X_20260918_12_doublebottom", "UPL_933a9f58", "TG_50603"], "third_party": [],
     "rules": ["ledger: SPLIT_SWEEP 7/10/13", "R-W-03"],
     "quant": "T-SWEEP-RECLAIM فشلت (إعادةُ الدخول الآليّة ‏−0.041R) · T-FUSE فشلت · T-RECLAIM-INTRADAY فشلت",
     "note": "المفهومُ ثابت · والدخولُ الآليُّ على الاسترداد سالبُ التوقّع في القياس"},
    {"id": "P08", "name": "نطاقُ القرار / الرقمُ الحرج", "status": "CONFIRMED",
     "faisal": ["TG_58045", "TG_58046", "TG_58049"], "third_party": [], "rules": ["R-W-07", "R-W-14", "R-CL-01"],
     "quant": "الإنتاج: «الرقم الحرج» عرضٌ (build_interpretation) بلا قياسٍ تداوليّ مستقلّ"},
    {"id": "P09", "name": "الفراشة (هارمونيّ)", "status": "SUPPORTED",
     "faisal": ["TG_58046"], "third_party": [], "rules": ["R-W-14"], "quant": "لا قياس",
     "note": "ذِكرٌ واحد بلا نِسَب ⟵ البنيةُ الهندسيّة UNKNOWN"},
    {"id": "P10", "name": "المثلّث · الوتد · العلم · القناة", "status": "POSSIBLE",
     "faisal": [], "faisal_repost": ["TG_57858", "TG_57860"], "third_party": [], "doc_only": ["IMG_6989"],
     "rules": ["R-CL-03"], "quant": "لا قياس",
     "note": "إنفوغرافاتُ طرفٍ ثالث أرفقها فيصل بتعليقٍ عامّ («رفض الاختراق = هبوط») · و«مثلث تجميع» CNMD وصفٌ في الكاتالوج بلا صورة · والقناةُ صفرُ دليل"},
    {"id": "P11", "name": "بنيةُ السوق HH/HL/LH/LL · BOS · CHoCH", "status": "SUPPORTED",
     "faisal": ["IMG_8127", "X_20260905_10"], "third_party": [], "rules": ["R-ST-01"], "quant": "لا قياس",
     "note": "المفرداتُ العربيّة (قاع ادنى · قمة اعلى) بلفظه · وBOS/CHoCH صفرُ استعمال ⟵ UNKNOWN · وصورةُ «HIGHER HIGH…» المذكورة 10-01 لم تصل"},
    {"id": "P12", "name": "نماذجُ الشموع (مطرقة · ابتلاع · الرجل المشنوق · Piercing · Three Inside Up)", "status": "SUPPORTED",
     "faisal": ["TG_2108", "TG_2176"], "third_party": ["TG_58042", "EDU_20260918_56_three_inside_up", "TG_2274"], "rules": ["R-W-13"],
     "quant": "T-CANDLE فشلت (صفرٌ من ستّة · والهمرُ أسوأ)"},
    {"id": "P13", "name": "الفجوات أهدافًا («الازرق فجوة لازم يغطيها»)", "status": "CONFIRMED",
     "faisal": ["TG_20260905_06", "TG_20260905_08"], "third_party": [], "rules": ["ledger: الأزرق فجوة · تغطية الفجوة = تفعيل"],
     "quant": "T-GAPBELOW (الفجوةُ تحت السعر) الفرعُ 3 «لا قياس» — والفجوةُ فوق السعر هدفٌ عرضًا في الإنتاج"},
    {"id": "P14", "name": "وصفةُ المقسّم (÷2 · ثبات 3 جلسات · شورت تحت 20 ألف · فلوت تحت 2 مليون · الهدف الشمعة الساقطة = 100٪)", "status": "CONFIRMED",
     "faisal": ["IMG_0150", "IMG_0151", "IMG_0153"], "third_party": [], "rules": ["ledger: بوّابات الصيّاد الخمس 5/5 faisal_verbatim"],
     "quant": "صيّادُ المقسّم حيّ (تحت حماية المالك) — لم يُثبَت بباكتيست وأثبت نفسه حيًّا (الذاكرة)"},
    {"id": "P15", "name": "فيبوناتشي", "status": "SUPPORTED",
     "faisal": ["TG_1995"], "faisal_repost": ["TG_57862"], "third_party": ["TG_58052"], "doc_only": ["IMG_9933"],
     "rules": ["F100-4", "F50-6"], "quant": "لا قياس",
     "note": "النطاقُ الكامل (قاع ⟵ قمّة الدورة) سلّمُ أهداف · و50% دخولٌ عند الطرف الثالث وحدَه"},
    {"id": "P16", "name": "خطُّ الترند الهابط", "status": "SUPPORTED",
     "faisal": ["TG_58049"], "third_party": ["TG_58042", "TG_58043"], "rules": ["R-W-10"],
     "quant": "الإنتاج: descending_trendline عرضٌ ويغذّي الرقمَ الحرج"},
    {"id": "P17", "name": "المتوسّطاتُ 20/30/50", "status": "CONFIRMED",
     "faisal": ["IMG_0151", "IMG_0153"], "third_party": [], "rules": ["ledger: SPLIT_MA_PERIODS · MA_GATE"],
     "quant": "T-MA-LADDER الفرعُ 2 «لا تُوصى»"},
]

_ID_RE = re.compile(r"\b((?:TG|IMG|X|CH|EDU|APP|WA)_[0-9A-Za-z][0-9A-Za-z_]*)")


def load_corpus():
    d = json.load(open(os.path.join(OUT, "image_corpus.json"), encoding="utf-8"))
    by_id = {r["id"]: r for r in d["images"]}
    return by_id


def doc_only_ids():
    sa = json.load(open(os.path.join(OUT, "source_access.json"), encoding="utf-8"))
    for s in sa["sources"]:
        if s["id"] == "SRC-DOC-ONLY-IMAGES":
            return set(s["ids"])
    return set()


def resolve(token, by_id):
    """معرّفٌ كاملٌ أو مختصر (X_21 · TG_40 · CH_05_CPOP) ⟵ (الحالة، المعرّفات)."""
    t = token.rstrip("_")
    if t in by_id:
        return "resolved", [t]
    m = re.match(r"^(TG|IMG|X|CH|EDU|APP|WA)_(\d{1,3})(?:_(.+))?$", t)
    if m:
        fam, num, suf = m.group(1), int(m.group(2)), m.group(3)
        pat = re.compile(rf"^{fam}_\d{{8}}_0*{num}(?:_|$)")
        cands = [k for k in by_id if pat.match(k)]
        if suf:
            c2 = [k for k in cands if k.endswith(suf) or ("_" + suf) in k]
            cands = c2 or cands
        if len(cands) == 1:
            return "resolved", cands
        if len(cands) > 1:
            return "ambiguous", sorted(cands)
    for k in by_id:
        if k.startswith(t + "_") and re.match(r"^(X|CH|EDU|APP|WA|TG)_\d{8}", k):
            return "resolved", [k]
    return "unresolved", []


def classify_id(i, by_id, doc_only):
    if i in EXTERNAL:
        return "external"
    if i in by_id:
        return "corpus"
    if i in doc_only:
        return "doc_only"
    return "missing"


def status_of(source_type, supp_units, has_contra_verbatim=False, visual_neg=False, ledger_checked=False):
    if visual_neg or has_contra_verbatim:
        return "CONTRADICTED"
    if source_type == "faisal_verbatim":
        if supp_units >= 2:
            return "CONFIRMED"
        if supp_units >= 1 or ledger_checked:      # صفٌّ تحقّق منه الدفترُ بصريًّا وصورتُه خارج المدوَّنة
            return "SUPPORTED"
        return "PROBABLE"
    if source_type in ("faisal_inferred", "faisal_adopted"):
        return "PROBABLE"
    if source_type == "third_party":
        return "POSSIBLE"
    return "UNKNOWN"


def ledger_rules(by_id):
    L = open(LEDGER, encoding="utf-8").read().split("\n")
    sec, rules, n = "", [], 0
    for line in L:
        if line.startswith("#"):
            sec = line.strip("# ").strip()
            continue
        if not line.startswith("|") or set(line) <= set("|-: "):
            continue
        tags = [x for x in TAGS if f"`{x}`" in line]
        if not tags or line.startswith("| `faisal") or line.startswith("| الوسم") or line.startswith("| `engineering`") \
                or line.startswith("| `third_party`") or line.startswith("| `unsourced`"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        n += 1
        toks = sorted(set(_ID_RE.findall(line)))
        res, unres, amb = [], [], []
        for tk in toks:
            st, ids = resolve(tk, by_id)
            if st == "resolved":
                res += ids
            elif st == "ambiguous":
                amb.append({"token": tk, "candidates": ids})
            else:
                unres.append(tk)
        neg = "✗" in line and "✓" not in line
        # ✗ عند الدفتر = «فحصتُ ونفيت» — يصير تناقضًا فقط إن ذكر الصفُّ نصًّا مخالفًا لفيصل أو نفيًا صريحًا للنسبة إليه ·
        # و«✗ لا نظير له في نصوصه» = لا دليل (UNKNOWN) لا تناقض
        contra = neg and bool(re.search(r"يناقض|المنصوص|نُفي|نفيت|خلاف نصّه|تصحيح فيصل", line))
        rules.append({"id": f"L-{n:03d}", "origin": "FAISAL_SOURCE_LEDGER.md", "section": sec[:120],
                      "name": re.sub(r"\*\*|`", "", cells[0])[:200],
                      "row": re.sub(r"\s+", " ", line)[:900], "source_type": tags[0], "all_tags": tags,
                      "supporting": sorted(set(res)), "unresolved_refs": unres, "ambiguous_refs": amb,
                      "visual_check": "✗" if neg else ("✓" if "✓" in line or "✅" in line else ""),
                      "contradicted_by_text": contra, "contradicting": []})
    return rules


def main():
    by_id = load_corpus()
    doc_only = doc_only_ids()
    cl = {k: r["dup_cluster"] for k, r in by_id.items()}

    def units(ids):
        u = set()
        for i in ids:
            if i in cl:
                u.add(cl[i])
            elif i in EXTERNAL:
                u.add("EXT:" + i)
            elif i in doc_only:
                u.add("DOC:" + i)          # صورةٌ موصوفةٌ في الوثائق وغائبةٌ عن المدوَّنة — وحدةٌ معلَّمة
        return u

    # المراجعةُ البصريّة ⟵ ملفُّ البيانات (يقرؤه corpus_build في التشغيلة التالية)
    vr = {k: dict(v, reviewed="2026-10-02 · بعيني في هذه المهمّة (Read + تكبيرٌ عند الحاجة)") for k, v in VISUAL_REVIEW.items()}
    json.dump(vr, open(os.path.join(OUT, "data", "visual_review.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # القواعد
    rules = []
    for r in NEW_RULES:
        r = dict(r)
        r["origin"] = "FAISAL_METHOD_V3 (هذه المهمّة)"
        sup_f = [i for i in r["supporting"] if i in EXTERNAL or i in by_id or i in doc_only]
        r["supporting_units"] = len(units(sup_f))
        r["evidence_status"] = status_of(r["source_type"], r["supporting_units"])
        r["id_classes"] = {i: classify_id(i, by_id, doc_only) for i in r["supporting"] + r["contradicting"]}
        rules.append(r)
    for r in ledger_rules(by_id):
        docs = [t for t in r["unresolved_refs"] if t in doc_only]
        r["supporting_doc_only"] = docs
        r["supporting_units"] = len(units(r["supporting"] + docs))
        r["evidence_status"] = status_of(r["source_type"], r["supporting_units"],
                                         visual_neg=r["contradicted_by_text"], ledger_checked=(r["visual_check"] == "✓"))
        r["evidence_not_in_corpus"] = r["supporting_units"] == 0 or bool(docs)
        r["id_classes"] = {i: classify_id(i, by_id, doc_only) for i in r["supporting"] + docs}
        rules.append(r)

    # تحقّق: كلُّ معرّفٍ مستشهَدٍ به في القواعد الجديدة والنماذج والمعاني معروفُ الصنف
    bad = []
    for r in NEW_RULES:
        for i in r["supporting"] + r["contradicting"]:
            if classify_id(i, by_id, doc_only) == "missing":
                bad.append((r["id"], i))
    for p in PATTERNS:
        for k in ("faisal", "faisal_repost", "third_party", "other_user", "doc_only"):
            for i in p.get(k, []):
                if classify_id(i, by_id, doc_only) == "missing":
                    bad.append((p["id"], i))
    for grp in TARGET_MEANINGS.values():
        for m in grp:
            for i in m["evidence"]:
                if classify_id(i, by_id, doc_only) == "missing":
                    bad.append((m["id"], i))
    if bad:
        raise SystemExit(f"⛔ معرّفاتٌ غيرُ معروفة: {bad}")

    by_status = defaultdict(int)
    for r in rules:
        by_status[r["evidence_status"]] += 1
    json.dump({"meta": {"rules": len(rules), "new_rules": len(NEW_RULES), "ledger_rules": len(rules) - len(NEW_RULES),
                        "by_status": dict(by_status), "status_definitions": __doc__.split("⚖️")[1].split("🔴")[0].strip(),
                        "external_evidence": EXTERNAL},
               "rules": rules},
              open(os.path.join(OUT, "rule_graph.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    # مصفوفةُ الأدلّة: قاعدة ⟵ وحدات · ووحدة ⟵ قواعد
    inv = defaultdict(set)
    rows = []
    for r in rules:
        u = sorted(units(r["supporting"]))
        cu = sorted(units(r.get("contradicting", [])))
        rows.append({"rule": r["id"], "status": r["evidence_status"], "source_type": r["source_type"],
                     "supporting_units": u, "contradicting_units": cu})
        for x in u:
            inv[x].add(r["id"])
    all_units = {r["dup_cluster"] for r in by_id.values()}
    json.dump({"meta": {"rules": len(rows), "units_total": len(all_units), "units_cited": len([x for x in inv if not x.startswith("EXT:")]),
                        "units_uncited": len(all_units - set(inv))},
               "by_rule": rows, "by_unit": {k: sorted(v) for k, v in sorted(inv.items())}},
              open(os.path.join(OUT, "evidence_matrix.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    for p in PATTERNS:
        ids = [i for k in ("faisal", "faisal_repost", "third_party", "other_user") for i in p.get(k, [])]
        p["independent_units"] = len(units(ids))
        p["faisal_units"] = len(units(p.get("faisal", [])))
    json.dump({"meta": {"patterns": len(PATTERNS)}, "patterns": PATTERNS},
              open(os.path.join(OUT, "pattern_catalog.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    for grp in TARGET_MEANINGS.values():
        for m in grp:
            m["independent_units"] = len(units(m["evidence"]))
    summary = {
        "verdict_50": "في لفظ فيصل لا تعني «50٪» إسقاطًا من ارتفاع النموذج قطّ: هي (1) صعودٌ أوّلُ تحقّق يُطفئ المطاردة · (2) ربحٌ معرَّضٌ للضياع · (3) مدى حركةٍ متوقَّع 30-50% · (4) تنصيفٌ في وصفة المقسّم مستهدفَ هبوط · والمعنى الهندسيّ (فيبو 50% · سهمُ 50% في رسم W) عند الطرف الثالث وحدَه",
        "verdict_100": "«100٪» مقرونةً بـ«هدف» = ربحٌ ‏+100% (T-TGT) · و«100% من ارتفاع النموذج فوق الاختراق» لفظُ القناة التعليميّة ومصغّرةٌ أعاد فيصل نشرَها بلا تعليق — صفرُ استعمالٍ بلفظه · وهدفُه في W الوحيد المقيس (DXST) مستوياتٌ أفقيّة (1.07h · 1.82h) ونتيجتُه «حقق نسبة 25٪»",
        "tool_policy": "الأداةُ تعرض الأهدافَ الثلاثة بوسومها: سلّمُ المقاومات (فيصل) · ‏+100% من الدخول (فيصل) · الحركةُ المقيسة 100%/50% من الارتفاع (طرفٌ ثالث · للمقارنة) — ولا تخلطها",
    }
    json.dump({"meta": summary, "meanings": TARGET_MEANINGS},
              open(os.path.join(OUT, "target_forensics.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"rules": len(rules), "by_status": dict(by_status), "patterns": len(PATTERNS),
                      "units_cited": len(inv), "visual_review": len(vr)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
