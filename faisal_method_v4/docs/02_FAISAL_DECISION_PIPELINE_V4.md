# 02 — خطّ قرار فيصل V4 (مُعادٌ بناؤه ومُعدَّلٌ بالدليل)

> الترتيبُ المفترض في المهمّة **لم يُقبل كما هو**: الصلاحيّةُ حاجبٌ يأتي بعد البنية ولا يرقّي · والنموذجُ معلومةٌ لا قرار · والتأكيدُ = ثباتٌ في المنطقة أو سحبٌ ثمّ عودة ·
> والدخولُ آليّةٌ لا قرار. ترتيبُ المهمّة مُعدَّلٌ بالدليل: الصلاحيّةُ (أخبار · طرح · قروبات · شورت) **حاجبٌ** يأتي بعد البنية ولا يرقّي (ADIL TG_2064 · KWM) · والنموذجُ (W) معلومةٌ لا قرار · والتأكيدُ = ثباتٌ في المنطقة أو سحبٌ ثمّ عودة · والدخولُ آليّةٌ لا قرار

## ① المراحل
DATA ⟵ DATA_QUALITY ⟵ MARKET_CONTEXT ⟵ STRUCTURE ⟵ PATTERN ⟵ SUPPORT_RESISTANCE ⟵ PRICE_LOCATION ⟵ CONFIRMATION ⟵ VALIDITY ⟵ ENTRY ⟵ INVALIDATION ⟵ TARGET ⟵ DECISION ⟵ EXPLANATION

## ② ترتيبُ آلة الحالات (أوّلُ ما يصدق يحكم)
| القاعدة | الحالة | القرار الفنيّ | المعنى |
|---|---|---|---|
| R4-DATA-01 | DATA_INSUFFICIENT | UNKNOWN | بياناتٌ غيرُ كافية |
| R4-INV-01 | BROKEN_NEW_BASE | WAIT | كُسر القاعُ السابق بأبعد من مدى السحب — تحليلٌ جديدٌ من القاع الجديد |
| R4-SWEEP-01 | PRESS_RECLAIM | TECH_READY | سحبُ سيولةٍ ثمّ عودةٌ فوق القاع السابق (ضغطٌ مكتمل) |
| R4-SWEEP-01 | SWEEP_ACTIVE | WAIT | سحبُ سيولةٍ تحت القاع السابق ولم يعد فوقه بعد |
| R4-HOLD-01 | BASE_FORMING | WAIT | القاعُ لم يثبت 5 جلسات بعد |
| R4-CYC-01 | BASE_HELD | TECH_READY | قاعٌ ثابتٌ والسعرُ في المنطقة بلا صعود اختبارٍ بعد |
| R4-LOC-01 | RETEST_PENDING | WAIT | صعد للاختبار والسعرُ فوق المنطقة — انتظارُ الرجوع لاختبار الدعم |
| R4-HOLDZ-01 | RETEST_HELD | TECH_READY | اختبر الدعم وثبت في المنطقة |
| R4-HOLDZ-01 | RETEST_IN_PROGRESS | WAIT | رجع إلى المنطقة ولم يثبت فيها جلساتٍ كافية |

## ③ الصلاحيّة (حاجبٌ · لا ترقية)
| من | إلى | القاعدة | متى |
|---|---|---|---|
| TECH_READY | REJECT | R4-VAL-GRP-01 | groups = True (وفي أيّ حالة) |
| TECH_READY | WAIT | R4-VAL-OFF-01 · R4-VAL-SHORT-01 | طرحٌ معلَّق أو متاحٌ فوق 20,000 |
| TECH_READY | UNKNOWN | R4-OP-01 | معلومةٌ ناقصة (قروبات · طرح · شورت · بصمةُ المضارب) |
| TECH_READY | READY | — | الصلاحيّةُ كاملةٌ نظيفة |

## ④ العتبات بمصادرها
| المفتاح | القيمة | المصدر | التعليل |
|---|---|---|---|
| MIN_BARS | 40 | engineering | R4-DATA-01: أقلُّ من 40 جلسة ⟵ UNKNOWN |
| CYCLE_BARS | 120 | production | R-SUP-MAIN (V3.1 · V31_prereg §②): نافذةُ قمّة الدورة 2 × W_BARS_MAX |
| HOLD_MIN | 5 | faisal_verbatim | R4-HOLD-01: «اذا ماكسر القاع اكثر من 5 جلسات» (X_20260918_85_YMT) |
| RISE_TEST_PCT | 15.0 | faisal_inferred | R4-CYC-01: المدى 10-50 · الغالب 20 · المقبول 17 (IMG_0488) |
| ZONE_PCT | 15.0 | faisal_verbatim | R4-ZONE-01: «طلبات 5-15٪ فوق القاع» (IMG_0531) |
| BID_LO_PCT | 5.0 | faisal_verbatim | R4-ZONE-01: الحدُّ الأدنى للطلبات فوق القاع (IMG_0531) |
| HOLD_ZONE | 3 | faisal_inferred | R4-HOLDZ-01: المدى 2-5 (CLIR «جلستين او 3» · STKH «5») |
| SWEEP_MAX_PCT | 13.0 | faisal_tier2b | R4-SWEEP-01: IMG_0297 (EDU) «7٪ ل 13٪» · ومدى الطبقة 1 حتى 15 |
| SWEEP_PROJ_PCT | (5.0, 10.0) | faisal_verbatim | R4-SWEEP-01: «5٪ تحت أدنى شمعة القاع» (TG_50584) · «10٪» (IMG_0177) |
| RECLAIM_BARS | 2 | engineering | R4-SWEEP-01: العودةُ فوق القاع السابق خلال جلستين («الضغط قبل الصعود بيوم» IMG_0531) |
| AT_BAND_PCT | 3.0 | production | DECISION_BAND_PCT (V3.1): «عند» = ضمن 3% |
| LEVEL_TOL_PCT | 2.0 | faisal_verbatim | «دقة الخطأ لاتتجاوز 2٪» — حدُّ القاع المزدوج ومطابقةُ المستويات |
| SHORT_AVAIL_MAX | 20000 | faisal_verbatim | R4-VAL-SHORT-01: «تابعه لين يبقى الشورت تحت 20 الف» (IMG_0150) |
| SWING_K | 3 | engineering | عرضُ المحور اليوميّ (V3.1) |

## ⑤ قراريّةُ القواعد (§11)
| القاعدة | القراريّة | الحالة | مستوى المصدر | نشطة؟ | الأثر |
|---|---|---|---|---|---|
| R4-DATA-01 | DECISIONAL | CONFIRMED | 7 | ✅ | نقصُ البيانات ⟵ UNKNOWN |
| R4-BOT-01 | DECISIONAL | SUPPORTED | 2 | ✅ | مرساةُ البنية (القاع والمنطقة والوقف) |
| R4-HOLD-01 | DECISIONAL | SUPPORTED | 3 | ✅ | أقلّ من 5 ⟵ WAIT (BASE_FORMING) |
| R4-CYC-01 | DECISIONAL | CONFIRMED | 3 | ✅ | بعد صعود الاختبار والسعرُ فوق المنطقة ⟵ WAIT (RETEST_PENDING) |
| R4-ZONE-01 | DECISIONAL | SUPPORTED | 1 | ✅ | السعرُ داخل المنطقة شرطُ الجاهزيّة الفنيّة |
| R4-HOLDZ-01 | DECISIONAL | PROBABLE | 2 | ✅ | أقلّ من HOLD_ZONE ⟵ WAIT (RETEST_IN_PROGRESS) |
| R4-SWEEP-01 | DECISIONAL | SUPPORTED | 2 | ✅ | سحبٌ ثمّ عودةٌ خلال جلستين ⟵ جاهزيّةٌ فنيّة (PRESS_RECLAIM) |
| R4-INV-01 | DECISIONAL | SUPPORTED | 2 | ✅ | كسرٌ أعمق من SWEEP_MAX ⟵ WAIT (BROKEN_NEW_BASE) |
| R4-LOC-01 | DECISIONAL | CONFIRMED | 2 | ✅ | فوق المنطقة ⟵ WAIT (RETEST_PENDING) |
| R4-OP-01 | UNKNOWN | SUPPORTED | 2 | ✅ | غيرُ مرئيٍّ تاريخيًّا إلّا بالسحب والعودة (R4-SWEEP-01) ⟵ الجاهزيّةُ الفنيّةُ بلا معلومة ⟵ UNKNOWN لا READY |
| R4-VAL-GRP-01 | DECISIONAL | SUPPORTED | 2 | ✅ | context.groups = True ⟵ REJECT |
| R4-VAL-OFF-01 | DECISIONAL | SUPPORTED | 2 | ✅ | context.offering_pending = True ⟵ WAIT |
| R4-VAL-SHORT-01 | DECISIONAL | PROBABLE | 2 | ✅ | context.short_available > 20,000 ⟵ WAIT (لا يرقّي أبدًا) |
| R4-ENT-01 | SUPPORTING | CONFIRMED | 2 | ✅ | يشرح طريقة الدخول · لا يغيّر الحالة (جوابُ §15) |
| R4-ENT-02 | INFORMATIONAL | SUPPORTED | 2 | ✅ | يُعرض بديلًا (مستوى التحرّر) ولا يقلب الحالة — متنازَعٌ عليه |
| R4-STOP-01 | SUPPORTING | SUPPORTED | 2 | ✅ | ثلاثُ عائلاتِ وقفٍ موسومة لا تُخلط |
| R4-TGT-01 | INFORMATIONAL | CONFIRMED | 2 | ✅ | الأهدافُ لا تغيّر الحالة |
| R4-TF-01 | INFORMATIONAL | SUPPORTED | 2 | ✅ | سياقُ الفريم الأدنى UNKNOWN تاريخيًّا |
| R-W-SPAN | UNKNOWN | SUPPORTED | 4 | ❌ | في V4: مُدمَجةٌ في R4-BOT-01 (القاعُ = الأدنى) — لا تُستعمل منفصلة |
| R-SUP-MAIN | DECISIONAL | SUPPORTED | 6 | ❌ | في V4: هو تعريفُ القاع (R4-BOT-01) · والدعمُ فوقه يُقرأ بالجسم والدعم الثاني والمنطقة |
| H-D2 | UNKNOWN | CONTRADICTED | 5 | ❌ | لا أثر |

## ⑥ ما لا يراه المحرّك (ولذلك UNKNOWN)
القروبات · الطرحُ المعلَّق · المتاحُ للشورت · بصمةُ المضارب/الضغط — كلُّها **شرطُ READY عند فيصل** ولا مصدرَ تاريخيٌّ لها ⟵ الجاهزيّةُ الفنيّةُ بلا هذه المعلومة **UNKNOWN بقائمة الناقص** لا READY.
