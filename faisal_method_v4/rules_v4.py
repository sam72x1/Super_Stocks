# -*- coding: utf-8 -*-
"""
🧭 FAISAL V4 — سجلُّ القواعد (§27): لكلّ قاعدةٍ مصدرُها ومستوى مصدرها وأمثلتُها المؤيّدة والمناقضة وحالةُ دليلها
وقراريّتُها — بياناتٌ لا كود قرار (المحرّك يقرأ `decisionality` و`active` منها).

مستوى المصدر (§3): 1 فيصل مباشرةً · 2 تكرارٌ عبر أمثلةٍ لفيصل · 3 شرحٌ أو مصطلحٌ صريحٌ منه · 4 سلوكٌ بصريٌّ متّسق ·
5 طرفٌ ثالث · 6 استنتاجُ النموذج · 7 عُرفُ التحليل الفنّيّ العامّ.
حالةُ الدليل: CONFIRMED · SUPPORTED · PROBABLE · POSSIBLE · CONTRADICTED · UNKNOWN (لا ترقيةَ صامتة).
القراريّة (§11): DECISIONAL (تغيّر READY/WAIT/REJECT) · SUPPORTING (تشرح) · INFORMATIONAL (تُعرض ولا تغيّر) · UNKNOWN (لا أثر).
وكلُّ قاعدةٍ هنا **ليست مشتقّةً من باكتيست** (§24) — `backtest_derived` = False بقفل.
"""

VERSION = "V4-RULES 1.0 (2026-10-02)"

# الأمثلةُ معرّفاتُ صورٍ من `data/visual_pass_v4.jsonl` · والذهبيّةُ لا تُعدّ مصدرَ اكتشاف (تُذكر في `golden_witness` وحدَها).
RULES_V4 = {
    "R4-DATA-01": dict(
        description="جودةُ البيانات: 40 جلسةً يوميّةً فأكثر حتى تاريخ القراءة · بلا قيمٍ ناقصة · والقراءةُ لا ترى ما بعد asof",
        source="engineering (§26 · §35)", author="—", source_level=7, image_ids=[], supporting=[], contradicting=[],
        status="CONFIRMED", decisionality="DECISIONAL", effect="نقصُ البيانات ⟵ UNKNOWN", active=True),
    "R4-BOT-01": dict(
        description="القاعُ = أدنى ذيلٍ منذ قمّة الدورة (نافذة 120 جلسة) · وكسرُه بأبعد من مدى السحب يعيد التحليل من القاع الجديد "
                    "(يعمّم R-W-SPAN: القاعُ الحقيقيُّ هو الأدنى)",
        source="faisal", author="F", source_level=2,
        image_ids=["TG_50584", "X_20260827_checklist_7points", "X_20260905_10", "X_20260905_07", "IMG_0689"],
        supporting=["TG_50584 «أدنى شمعة القاع»", "X_20260827_checklist_7points «ادنى شمعه … الوقف القاع»",
                    "X_20260905_10 «كسر 1.81 تصنع تحليل اخر بنفس النهج» (طبقة 2)", "X_20260905_07 «إن كسر قاع 2.08 يذهب إلى 1.70»",
                    "IMG_0689 «كسره = ذهاب الى دعوم اخرى»"],
        contradicting=["C1 (V3.1): دعومُ فيصل فوق الذيل أحيانًا (ZNB 1.963 · LABT 2/1.80) — حُلّ بفصل القاع (ذيل) عن الدعم (جسم · دعمٌ ثانٍ · منطقة)"],
        golden_witness=["RAYA: دعمُ فيصل 1.999 = القاعُ الداخليّ 2.0 (تحقّقٌ لا مصدر)"],
        status="SUPPORTED", decisionality="DECISIONAL", effect="مرساةُ البنية (القاع والمنطقة والوقف)", active=True),
    "R4-HOLD-01": dict(
        description="القاعُ لا يُكسر 5 جلساتٍ فأكثر قبل أيّ حكمٍ بالإيجابيّة",
        source="faisal", author="F", source_level=3,
        image_ids=["X_20260918_85_YMT", "X_20260827_checklist_7points", "TG_20260905_09", "TG_2066", "TG_2044"],
        supporting=["X_20260918_85_YMT «اذا ماكسر القاع اكثر من 5 جلسات»", "X_20260827_checklist_7points «5 جلسات»",
                    "TG_20260905_09 «ثبات ٥ جلسات دخول ذا نهج علمي» (المالك يشهد)", "TG_2066 «3-5 جلسات» (طبقة 2)",
                    "TG_2044 «ثبات السعر 5 جلسات» (للمبتدئ)"],
        contradicting=["WA_20260918_31_SXTC: READY يومَ الضغط (طبقة 2)", "TG_2059 PPCB: «ماركت ناخذه» بعد الضغط والارتداد"],
        status="SUPPORTED", decisionality="DECISIONAL", effect="أقلّ من 5 ⟵ WAIT (BASE_FORMING)", active=True),
    "R4-CYC-01": dict(
        description="الدورة: قاع ⟵ صعودُ اختبارٍ (15% فأكثر · غالبًا 20%) ⟵ رجوعٌ يختبر الدعم ⟵ الحكمُ عند الاختبار «هذا اصل التحليل»",
        source="faisal", author="F", source_level=3,
        image_ids=["X_20260918_85_YMT", "TG_50584", "X_20260918_13_NUWE", "TG_50585", "TG_57872", "TG_57884", "TG_57867",
                   "TG_50579", "IMG_0566", "IMG_0488", "X_20260918_24_SXTC", "TG_20260905_07", "TG_20260905_09"],
        supporting=["X_20260918_85_YMT «يصعد 20٪ بعد القاع · يرجع يختبر الدعم · هذا اصل التحليل»",
                    "TG_50584 «ارتداد لاختبار المقاومة 20% غالبًا»", "X_20260918_13_NUWE «قاع ⟵ صعود ⟵ اختبار مقاومة ⟵ هبوط ⟵ اختبار دعم»",
                    "TG_50585 LIMN «اختبار مقاومه ✅ · تبقى اختبار القاع»", "TG_57872 OMH «اعادة الاختبار شرط اساسي»",
                    "TG_57884 CIIT «موجه هابطه … بعد اختبار المقاومه»", "TG_57867 NRSN «ضغط متوقع 20> 30٪»",
                    "TG_50579 EDBL «لازم يرجع يحقق المقاومه · بعده يرجع للدعم»", "IMG_0566 MNDR «حقق 50٪ … او يرجع يختبر 1.60»",
                    "IMG_0488 «قاع صعد 17٪ · هبط اختبار شمعه الصعود»", "X_20260918_24_SXTC «حقق المقاومة الأولى ثمّ هبط لاختبار الدعم»",
                    "TG_20260905_07 MSGY «يختبر المقاومة ثمّ يرجع يختبر الدعم»"],
        contradicting=["X_20260918_85_YMT نفسُه: «يصعد مباشره بعد القاع … نادر» (استثناءٌ معترَف به)",
                       "TG_1985 «اسهم تصعد مباشره لاتصلح لها هذي النظريه»",
                       "X_20260827_checklist_7points: دخولٌ عند القاع بلا صعود اختبار (C-CYCLE-VS-CHECKLIST)"],
        status="CONFIRMED", decisionality="DECISIONAL", effect="بعد صعود الاختبار والسعرُ فوق المنطقة ⟵ WAIT (RETEST_PENDING)",
        params={"RISE_TEST_PCT": "15 (المدى 10-50 · الغالب 20 · المقبول 17 في IMG_0488)"}, active=True),
    "R4-ZONE-01": dict(
        description="منطقةُ الدخول/الاختبار: من القاع حتى 15% فوقه · والطلباتُ 5-15% فوق القاع",
        source="faisal", author="F", source_level=1,
        image_ids=["IMG_0531", "IMG_0569", "X_20260827_checklist_7points", "TG_50585", "X_20260918_85_YMT"],
        supporting=["IMG_0531 «طلبات جاهزه 5-15٪ فوق القاع» · «تذبذب 10-20٪ فوق القاع»", "IMG_0569 MNDR 1.50-1.60 فوق قاع 1.40",
                    "X_20260827_checklist_7points «1.50 ⟵ 1.60-1.70»", "TG_50585 LIMN 3.40 فوق 3.29",
                    "X_20260918_85_YMT الدعم الثاني 1.84 فوق 1.81"],
        contradicting=["TG_1963 ERNA: طلباتٌ 5.00-5.40 فوق قاعٍ قديم 3.70 بـ35%+ (القاعُ المرجعيُّ مختلف)"],
        status="SUPPORTED", decisionality="DECISIONAL", effect="السعرُ داخل المنطقة شرطُ الجاهزيّة الفنيّة", active=True),
    "R4-HOLDZ-01": dict(
        description="ثباتٌ داخل المنطقة بعد الاختبار (2-5 جلسات · الأساسيّ 3) = جاهزيّةٌ فنيّة",
        source="faisal", author="F", source_level=2, image_ids=["TG_2108", "TG_20260905_09", "IMG_0566", "IMG_0697"],
        supporting=["TG_2108 CLIR «الدخول بعد ثبات الدعوم بجلستين او 3»", "TG_20260905_09 STKH «ثبات ٥ جلسات دخول»",
                    "IMG_0566 MNDR «في حال اختبر 1.60 ولاكسرها وحافظ ع قاعه يعتبر اجابي»", "TG_2066 «3-5 جلسات» (طبقة 2)"],
        contradicting=["IMG_0395 SPRC: «حقق الدعوم بالامس» ثمّ شراء (جلسةٌ واحدة)", "WA_20260918_31_SXTC: READY يومَ الضغط",
                       "IMG_0659 TDIC (EDU): الدخولُ على شمعة الهمر"],
        golden_witness=["ZNB «مافيه دخول لين يختبر 2 > 1.96»"],
        status="PROBABLE", decisionality="DECISIONAL", effect="أقلّ من HOLD_ZONE ⟵ WAIT (RETEST_IN_PROGRESS)",
        params={"HOLD_ZONE": "3 (المدى 2-5)"}, active=True),
    "R4-SWEEP-01": dict(
        description="سحبُ سيولةٍ تحت القاع السابق (حتى 13% · مدى الطبقة 1: 5-15%) ثمّ عودةٌ فوقه = ضغطُ المضارب (إيجابيّ)",
        source="faisal + EDU", author="F (المدى) · EDU (7-13 حرفيًّا)", source_level=2,
        image_ids=["TG_50584", "IMG_0177", "TG_57874", "TG_57870", "TG_57879", "TG_1822", "IMG_0297"],
        supporting=["TG_50584 «سحب سيولة 5% تحت أدنى شمعة القاع»", "IMG_0177 «مسح سيوله 10٪ تحت القاع»", "TG_57874 «10-15٪»",
                    "TG_57870 «15٪ تحت متوسط التجميع»", "TG_57879 CIIT «الاجابيه ثبات اسفل الدعم … بعدها العوده فوق الدعم»",
                    "TG_1822 EHGO «سحب السيوله اسفل الشمعه 10٪ تقريبا ورجع صعد فوق الدعم»", "IMG_0297 (EDU) «7٪ ل 13٪»"],
        contradicting=["IMG_0153 وصفةُ المقسّم: هبوطٌ إلى 2 من ÷2≈2.75 (‏−27%)", "C-STOP-VS-SWEEP: وقفُ 5-7% يُضرب بسحب 8%"],
        status="SUPPORTED", decisionality="DECISIONAL", effect="سحبٌ ثمّ عودةٌ خلال جلستين ⟵ جاهزيّةٌ فنيّة (PRESS_RECLAIM)",
        params={"SWEEP_MAX_PCT": "13 (حدُّ EDU · ومدى الطبقة 1 حتى 15)", "SWEEP_PROJ": "5 و10 (الطبقة 1)"}, active=True),
    "R4-INV-01": dict(
        description="كسرُ القاع بأبعد من مدى السحب يُفشل التحليل الحاليّ ⟵ انتظارُ قاعٍ جديد",
        source="faisal", author="F", source_level=2, image_ids=["IMG_0512", "IMG_0513", "IMG_0569", "X_20260905_10", "X_20260905_07"],
        supporting=["IMG_0512 CANF «السهم اذا ماكسر 2.80 بيصعد»", "IMG_0569 MNDR «1.40 اخطر مرحله للوقف»",
                    "X_20260905_10 YMT «كسر 1.81 تصنع تحليل اخر بنفس النهج»", "X_20260905_07 BTOG «إن كسر قاع 2.08 يذهب إلى 1.70»"],
        contradicting=["C-SUPPORT10: ENPH ‏−11..−13% وELAB ‏−39% ثمّ صعودٌ كبير (TG_2017 · TG_2127)"],
        golden_witness=["SPRC «كسر 4 يفشل التحليل»", "ZNB «كسرها = مافيه دخول»"],
        status="SUPPORTED", decisionality="DECISIONAL", effect="كسرٌ أعمق من SWEEP_MAX ⟵ WAIT (BROKEN_NEW_BASE)", active=True),
    "R4-LOC-01": dict(
        description="السعرُ فوق المنطقة بعد الصعود («الوسط غير الآمن») ⟵ لا دخول · انتظارُ الاختبار",
        source="faisal", author="F", source_level=2, image_ids=["X_20260918_12_doublebottom", "TG_2097", "TG_50580", "X_20260827_target10_entry_below"],
        supporting=["X_20260918_12_doublebottom «الدخول بين خط العنق والقاع المزدوج غير امن · ضبابيه الدخول بين وبين ليست جيده»",
                    "TG_2097 «هل تعتقد يرتفع من سعره الحالي … لايمكن … ABC لابد تتحقق»", "TG_50580 DCOY «العقل بالأسهم تشري تحت»",
                    "X_20260827_target10_entry_below «السعر الحالي غير صالح للدخول» (طبقة 2)"],
        contradicting=["T-W (V3): «الوسط غير آمن» عُكس يوميًّا بقياسٍ تداوليّ (A − M ‏−0.98) — مقياسُ ربحٍ لا وفاء (§24)"],
        status="CONFIRMED", decisionality="DECISIONAL", effect="فوق المنطقة ⟵ WAIT (RETEST_PENDING)", active=True),
    "R4-OP-01": dict(
        description="بصمةُ المضارب (الضغط) هي التأكيدُ الافتراضيّ قبل READY · والجاهزيّةُ الفنيّة بلا بصمةٍ ⟵ انتظار",
        source="faisal", author="F", source_level=2, image_ids=["TG_1822", "TG_2218", "X_20260827_amix_hcwb_ready", "X_20260905_01", "TG_50575", "TG_50584"],
        supporting=["TG_1822 EHGO «ننتظر فقط مضارب»", "TG_2218 CDIO «جاهز … بانتظار فقط دخول المضارب»",
                    "X_20260827_amix_hcwb_ready HCWB «ننتظر ضغط المضارب»", "X_20260905_01 PPBT «انتظار ضغط البري»",
                    "TG_50575 DCOY «ننتظر ضغط الماركت»", "TG_50584 «تبقى الضغط ✅»"],
        contradicting=["X_20260827_checklist_7points_cont «ماتم ضغطه … تدخل مباشره ع خط متوسط 50 > 200»", "AMIX READY قبل الضغط (طلبات)"],
        status="SUPPORTED", decisionality="UNKNOWN",
        effect="غيرُ مرئيٍّ تاريخيًّا إلّا بالسحب والعودة (R4-SWEEP-01) ⟵ الجاهزيّةُ الفنيّةُ بلا معلومة ⟵ UNKNOWN لا READY", active=True),
    "R4-VAL-GRP-01": dict(
        description="دخولُ القروبات يُبطل قراءةَ الشموع ⟵ رفض",
        source="faisal", author="F", source_level=2, image_ids=["IMG_0488", "TG_1835", "X_20260827_checklist_7points", "TG_2090", "IMG_0316", "IMG_0508"],
        supporting=["IMG_0488 «دخول سيوله قروبات … لا انا ولا اكبر محلل يستطيع قراءة الشموع»", "TG_1835 LABT «سيولة قروبات داخلة»",
                    "X_20260827_checklist_7points ⑥ «خالٍ من القروبات»", "TG_2090 CDIO «مالم تدخل قروبات»",
                    "IMG_0316 JZ «دخل قروب غبي … المضارب الغى جميع الاهداف»", "IMG_0508 SLXN «رفعه سريعه من اللي وصى عليه»"],
        contradicting=["X_20260905_10 YMT «لايهم حتى لو دخل قروب ورفعه 20٪ · المضارب اذا بيحقق اهدافه راح يهبط فيه»"],
        status="SUPPORTED", decisionality="DECISIONAL", effect="context.groups = True ⟵ REJECT", active=True),
    "R4-VAL-OFF-01": dict(
        description="طرحٌ أو تخفيفٌ معلَّق ⟵ انتظار",
        source="faisal", author="F", source_level=2, image_ids=["X_20260827_kwm_offering_notready", "TG_50828", "TG_2064", "X_20260918_85_YMT"],
        supporting=["X_20260827_kwm_offering_notready «غير جاهز فنيا» بعد طرح 500 ألف", "TG_50828 CETX «إغلاق طرح معلّق ⟵ انتظار»",
                    "TG_2064 ADIL «هل عنده تقسيم قادم او طرح او تخفيف»", "X_20260918_85_YMT «يهمك قراءة الاخبار هل هناك طرح اسهم»"],
        contradicting=[], status="SUPPORTED", decisionality="DECISIONAL", effect="context.offering_pending = True ⟵ WAIT", active=True),
    "R4-VAL-SHORT-01": dict(
        description="المتاحُ للشورت فوق 20 ألفًا ⟵ انتظار",
        source="faisal", author="F", source_level=2, image_ids=["IMG_0150", "TG_50578", "X_20260827_rubi_read_short150k"],
        supporting=["IMG_0150 WORX «تابعه لين يبقى الشورت تحت 20 الف»", "TG_50578 DCOY «باقي 80 الف شورت ننتظر»",
                    "X_20260827_rubi_read_short150k RUBI «المشكله بالشورت» (150 ألفًا)"],
        contradicting=["TG_2196 ONCO: شورت 150 ألفًا وخطّةٌ كاملة", "TG_1831 LABT: «الشورت 55 ألف متاح ولم يمنع التحليل» (طبقة 2)"],
        status="PROBABLE", decisionality="DECISIONAL", effect="context.short_available > 20,000 ⟵ WAIT (لا يرقّي أبدًا)", active=True),
    "R4-ENT-01": dict(
        description="الدخولُ الأوّل: طلباتٌ عند الدعم بدفعاتٍ (فوارق 5 سنتات) — آليّةُ دخولٍ مفضّلة لا شرطُ قرار",
        source="faisal", author="F", source_level=2, image_ids=["IMG_0569", "X_20260918_85_YMT", "X_20260827_checklist_7points", "IMG_0510", "TG_1963", "IMG_0505"],
        supporting=["IMG_0569 MNDR «طلبات عند الدعوم · شرا من العرض خساره»", "X_20260918_85_YMT «طلبات فوارق 5 سنت عند الدعم»",
                    "IMG_0510 CANF «نشري مع المضارب طلبات صغيره»", "IMG_0505 ADIL «شرحنا طريقة الدخول والتجميع»"],
        contradicting=["TG_1963 ERNA «اللي ماتفرق معاه ومتعود يشري من العرض قدامك السهم»", "IMG_0291 DSY «اخذته الان من العرض الليلي»",
                       "IMG_0290 AZI «شيله من العرض باي سعر» (عند التحرّر)", "TG_2059 PPCB «ماركت ناخذه»"],
        status="CONFIRMED", decisionality="SUPPORTING", effect="يشرح طريقة الدخول · لا يغيّر الحالة (جوابُ §15)", active=True),
    "R4-ENT-02": dict(
        description="الدخولُ الثاني: بعد التحرّر/الاختراق مع التأكيد (ثباتٌ فوقه · إقفالٌ يوميٌّ ثانٍ)",
        source="faisal", author="F", source_level=2, image_ids=["TG_2197", "X_20260827_checklist_7points_cont", "TG_57862", "IMG_0602", "X_20260918_61_VEEE"],
        supporting=["TG_2197 «دخول المضاربين > بعد الاختراق ربح سريع قليل امن»", "TG_57862 «دخول جديد بعد الاختراق وتأكيد الدعوم»",
                    "IMG_0602 CANF «اذا تجاوز 3.67 ممتاز»", "X_20260918_61_VEEE «انتظر تكوين الشمعه الثانيه باقفال يومي»"],
        contradicting=["TG_1840 «تشري ع الاختراق اعرف انك خسران … الاختراق فاشل الدخول فيه» (C-BREAKOUT)"],
        status="SUPPORTED", decisionality="INFORMATIONAL", effect="يُعرض بديلًا (مستوى التحرّر) ولا يقلب الحالة — متنازَعٌ عليه",
        active=True),
    "R4-STOP-01": dict(
        description="الوقف: القاعُ نفسُه (الأساسيّ) · وبدائلُ موسومة: ‏−5% · ‏−7% تحت الدعم · 7% من الدخول",
        source="faisal", author="F", source_level=2, image_ids=["X_20260827_checklist_7points", "TG_2106", "TG_1978", "TG_2098", "X_20260918_61_VEEE"],
        supporting=["X_20260827_checklist_7points «الوقف القاع»", "TG_2106 «وقفك صارم الدعم الاول»", "AMIX 4.60 تحت أدنى دفعة"],
        contradicting=["TG_1978 «الوقف −5٪»", "TG_2098 HUBC «وقف 7٪»", "X_20260918_61_VEEE «7٪ من دخولنا» (C-STOP-REF)"],
        status="SUPPORTED", decisionality="SUPPORTING", effect="ثلاثُ عائلاتِ وقفٍ موسومة لا تُخلط", active=True),
    "R4-TGT-01": dict(
        description="الأهداف: سلّمُ المقاومات (الأسود) · رأسُ/ذيلُ الشمعة الساقطة · الفجوات · و«100٪ هدف» = مسافةُ ربح ‏+100% · والحركةُ المقيسة طرفٌ ثالث",
        source="faisal", author="F", source_level=2, image_ids=["X_20260827_amix_hcwb_ready", "IMG_0508", "TG_2097", "IMG_0587", "X_20260827_pfsa_500pct"],
        supporting=["AMIX «هدفنا 100٪ 9.45» = ضعفُ الدخول", "IMG_0508 SLXN «يصعد ل 3 = 100٪»", "TG_2097 «الهدف 4 = 100٪» من الدعم 2"],
        contradicting=["IMG_0587 «100٪ مضمونه» = يقين لا مسافة (فئةٌ ثالثة)"],
        status="CONFIRMED", decisionality="INFORMATIONAL", effect="الأهدافُ لا تغيّر الحالة", active=True),
    "R4-TF-01": dict(
        description="الفريمات: يوميّ ‏+ 4 ساعات · و30/5 دقائق للّحظيّ · والمستوياتُ تختلف بالفريم — المحرّكُ يوميٌّ وحدَه",
        source="faisal", author="F", source_level=2, image_ids=["X_20260905_10", "IMG_0361", "TG_58048", "TG_2031"],
        supporting=["X_20260905_10 «فريم 4 ساعات كذلك 30 دقيقه»", "IMG_0361 «5 دقائق ادق واوضح»", "TG_58048 «W يُرسم على 30 دقيقة»"],
        contradicting=[], status="SUPPORTED", decisionality="INFORMATIONAL", effect="سياقُ الفريم الأدنى UNKNOWN تاريخيًّا", active=True),
    # ── قواعد V3.1 ومصيرُها في V4 ──
    "R-W-SPAN": dict(
        description="(V3.1) لا قاعَ بين قاعَي W أدنى منهما بأكثر من 2%", source="inferred (V3.1)", author="طرفٌ ثالث + رسمُ فيصل",
        source_level=4, image_ids=["IMG_0627", "TG_58042", "TG_58043"], supporting=[], contradicting=[],
        status="SUPPORTED", decisionality="UNKNOWN", effect="في V4: مُدمَجةٌ في R4-BOT-01 (القاعُ = الأدنى) — لا تُستعمل منفصلة",
        superseded_by="R4-BOT-01", active=False),
    "R-SUP-MAIN": dict(
        description="(V3.1 · معلومة) أدنى ذيلٍ منذ قمّة الدورة", source="engineering (V3.1)", author="—", source_level=6,
        image_ids=[], supporting=[], contradicting=["ZNB · LABT (V3.1 C1)"], status="SUPPORTED", decisionality="DECISIONAL",
        effect="في V4: هو تعريفُ القاع (R4-BOT-01) · والدعمُ فوقه يُقرأ بالجسم والدعم الثاني والمنطقة", superseded_by="R4-BOT-01",
        active=False),
    "H-D2": dict(
        description="(V3.1 · مرفوضة) جلسةٌ ممتدّة لـW على 30 دقيقة", source="faisal_adopted", author="—", source_level=5,
        image_ids=[], supporting=[], contradicting=["DXST: لا النظاميّ ولا الممتدّ أعاد W فيصل"], status="CONTRADICTED",
        decisionality="UNKNOWN", effect="لا أثر", active=False),
}

for _k, _r in RULES_V4.items():
    _r.setdefault("golden_witness", [])
    _r.setdefault("params", {})
    _r.setdefault("superseded_by", None)
    _r["backtest_derived"] = False
    _r["rule_id"] = _k
    _r["current_version"] = VERSION
    _r["change_history"] = (["V3.1 ⟵ V4: " + _r["effect"]] if _k in ("R-W-SPAN", "R-SUP-MAIN", "H-D2") else ["أُنشئت في V4 (2026-10-02)"])


def independent_sources(rule):
    """عددُ الصور المستقلّة المؤيّدة (المعرّفات الفريدة في image_ids) — §29 «قاعدةٌ من صورةٍ واحدة» تُوسَم."""
    return len(set(rule.get("image_ids") or []))


def single_image_rules():
    return sorted(k for k, r in RULES_V4.items() if r.get("active") and independent_sources(r) <= 1 and r["source_level"] <= 4)
