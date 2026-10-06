# 01 — FAISAL METHOD V4 · التقرير النهائيّ

> **الحالة: PARTIALLY COMPLETE** — المنهجُ أُعيد بناؤه من النصّ وسُجّل قبل أيّ رقم (#547) ثمّ شُغِّل مرّةً واحدة (التشغيلةُ الأولى هي النتيجة) ·
> **والحكمُ الحاكم: H-LEVEL على الاحتجاز FAIL** (+0.2466 [-0.0094 · +0.5873] · مستويات 22 · حالات 7) ⟵ المحرّكُ لا يُدّعى أنّه يعيد مستويات فيصل على شارتٍ لم يُرَ.
> كلُّ رقمٍ هنا من `results/*.json` (‏`v4_docs.py`) · وكلُّ دعوى موسومةٌ بأحد الأربعة (§41): **مشاهَد · مستنتَج · مُنفَّذ · مُتحقَّق**.

## ① ما شوهد (OBSERVED)
- 609 وحدةً بصريّة قُرئت كلُّها بالعين ⟵ 217 عبارةَ قرار ⟵ 157 حالة · S1 = 22 (READY 1 · WAIT 21).
- فيصل يقول «جاهز فنيًّا … انتظر المضارب» مرارًا: الكلمةُ تتبع معلوماتٍ خارج الشموع (المضارب · القروبات · الطرح · الشورت).
- تركيباتُ «مكوّن ‏+ قرار» في نصّ فيصل الحرفيّ: 47 تركيبة · 25 منها بمثالٍ واحد (لا قاعدةَ منها).

## ② ما استُنتج (INFERRED)
- الترتيبُ الفعليّ: البنيةُ (القاع والدورة) ⟵ الموقعُ من المنطقة ⟵ التأكيدُ (ثباتٌ أو سحبٌ ثمّ عودة) ⟵ الصلاحيّةُ حاجبٌ لا يرقّي — والنموذجُ معلومة.
- «الطلباتُ عند الدعم» آليّةُ دخولٍ مفضّلةٌ لا شرطُ قرار (§15) · وR-W-SPAN مُدمَجةٌ في «القاعُ = الأدنى» (§12).

## ③ ما نُفِّذ (IMPLEMENTED)
- `decision_engine.py` (FAISAL-V4 1.0 (2026-10-02)): 9 حالاتٍ فنيّة · كائنُ قرارٍ بأسباب القرار والحجب والناقص · 21 قاعدة بمصادرها.
- `v4_run.py` ‏+ `faisal_v4.yml` (يدويٌّ للقراءة) · `v4_offline.py` يعيد الحساب من الشموع المحفوظة · وطبقاتٌ بصريّة في `overlays/`.

## ④ ما تُحقِّق منه (VALIDATED) — بالعقد المدموج قبل الرقم
| المجموعة | حالات | سليمة | الحالات | H-LEVEL | الفرق [95%] (كلّ المستويات) | النصّيّة الصرفة | H-CLASS |
|---|---|---|---|---|---|---|---|
| S1 الاكتشاف | 12 | 10 | OK 10 · SCALE_MISMATCH 2 | PASS | +0.3978 [+0.1961 · +0.5977] · مستويات 23 · حالات 7 | +0.3978 [+0.1961 · +0.5977] · مستويات 23 · حالات 7 | FAIL · اتّفاق 4/10 · ويلسون [0.1682, 0.6873] · الأغلبيّة NONE 0.3 |
| **S1 الاحتجاز (الحاكم)** | 10 | 9 | OK 9 · SCALE_MISMATCH 1 | FAIL | +0.2466 [-0.0094 · +0.5873] · مستويات 22 · حالات 7 | +0.2031 [-0.0499 · +0.5766] · مستويات 20 · حالات 7 | FAIL · اتّفاق 4/9 · ويلسون [0.1888, 0.7333] · الأغلبيّة BELOW 0.6667 |
| S1 كلُّها | 22 | 19 | OK 19 · SCALE_MISMATCH 3 | PASS | +0.3239 [+0.1364 · +0.5246] · مستويات 45 · حالات 14 | +0.3073 [+0.1186 · +0.5117] · مستويات 43 · حالات 14 | FAIL · اتّفاق 8/19 · ويلسون [0.2314, 0.6372] · الأغلبيّة BELOW 0.4737 |
| S2 الثانويّة | 63 | 51 | DATA_INSUFFICIENT 1 · NO_BARS 1 · OK 51 · SCALE_MISMATCH 10 | FAIL | +0.1814 [-0.0042 · +0.3765] · مستويات 36 · حالات 18 | +0.1814 [-0.0042 · +0.3765] · مستويات 36 · حالات 18 | FAIL · اتّفاق 14/27 · ويلسون [0.3399, 0.6926] · الأغلبيّة BELOW 0.4815 |
| S3 الذهبيّة | 19 | 16 | NO_BARS 1 · OK 16 · SCALE_MISMATCH 2 | FAIL | +0.1272 [-0.0316 · +0.2939] · مستويات 29 · حالات 11 | +0.1272 [-0.0316 · +0.2939] · مستويات 29 · حالات 11 | FAIL · اتّفاق 5/15 · ويلسون [0.1518, 0.5829] · الأغلبيّة BELOW 0.4 |
| S4 القناة التعليميّة | 13 | 12 | OK 12 · SCALE_MISMATCH 1 | FAIL | -0.1089 [-0.2405 · +0.0696] · مستويات 11 · حالات 6 | -0.1089 [-0.2405 · +0.0696] · مستويات 11 · حالات 6 | FAIL · اتّفاق 5/10 · ويلسون [0.2366, 0.7634] · الأغلبيّة BELOW 0.7 |

- **H-STATE (وصفيّ):** على الاحتجاز تطابقُ الكلمة 8/9 مقابل «دائمًا WAIT» 9/9 ⟵ **لا قدرةَ مُثبَتةً على الكلمة فوق الخطّ التافه** · والمحرّكُ لم يقل READY قطّ (UNKNOWN 3 مرّةً على S1 بقائمة الناقص).
- **الإعادة:** الشموعُ محفوظة (`data/v4_bars_fixture.json` · SHA-256 `6b107ceaca682d0c…`) والحسابُ المحلّيّ يطابق Actions: **True**.
- **🔁 إعادةُ بناءٍ 2026-10-06:** حاويةُ الجلسة أُعيدت أثناء التوقّف بحدّ الاستخدام الأسبوعيّ (2026-10-02 22:13Z ⟵ 2026-10-06 21:03Z) فضاع كلُّ عملٍ غيرِ مدفوعٍ بعد #547. استُعيد حرفيًّا من سجلّ الجلسة: `v4_offline.py` · `v4_docs.py` · `data/corrections_v4.json` · `results/run_registry_v4.json (الأصل)` · `../FAISAL_SOURCE_LEDGER.md (خلايا ‏+ ملاحظات)` · `../FAISAL_IMAGES_CATALOG.md (§أربعة وثلاثون)` · `../SOURCE_ANALYSIS.md` · `../FAISAL_SCIENTIFIC_METHOD.md` · `../test_bot.py (PC6)` · وأُعيد جلبُ سجلّات التشغيلات الأربع (111046023777 · 111046051795 · 111046061360 · 111046070399) فطابقت بصمةُ المثبّت المسجَّلة: **True**.
- **أُعيدت كتابتُه (لا حرفيّ):** `v4_forensics.py` — الدوالُّ والثوابتُ من نصّها المحفوظ في سجلّ الجلسة حرفًا · وأُكملت ثلاثُ جملٍ مقصوصة في GENERIC_NOT_IMPLEMENTED · وأُعيدت نصوصُ خمسةَ عشرَ تعارضًا من شواهدها (المعرّفاتُ والحالاتُ كما طُبعت يوم 10-02 حرفًا) · `v4_corpus.py` — أُعيدت كتابتُه كلُّه بتعريفاتٍ مكتوبةٍ في رأسه تعيد الأرقامَ المطبوعة يوم 10-02 حرفًا.
- **قِيس على المطبوع يوم 10-02:** forensics_v4.json — أوّلُ 700 حرفٍ لكلّ قسم: 9 من 9 متطابقة · rule_generalization: 21 من 21 قاعدةً متطابقة · decision_combos: 47 · 25 بمثالٍ واحد · وأعلى 12 تركيبةً متطابقة · corpus_counts: 722 · 722 · 722 · 609 · 102 · 602 · 609 · 265 · 369 · واستعمالُ الدليل 220/190/277/35 · telegram: 11/11 · مكرّر 1 · أوّليّ 6 · محتوى أوّليّ 3 · طرفٌ ثالث 7 · v4_eval_results: مطابقةُ Actions True · H-STATE والذهبيّة 3/4/7/5 · VEEE البعديّ 2026-05-15 · 26 طبقة — المقارنةُ مع مخرجاتٍ طُبعت في سجلّ الجلسة يوم 10-02 (لا تُعاد في CI) · وما يُعاد في CI أقفالُ V4L11-V4L16 على الملفّات نفسِها.

## ⑤ التنبّؤات المكتوبة قبل الرقم (تُنشر إن خابت)
| # | التنبّؤ | النتيجة | صدق؟ |
|---|---|---|---|
| P1 | H-LEVEL على الاحتجاز PASS (ثقة ‏≈55%) | FAIL | ❌ |
| P2 | H-CLASS على الاحتجاز FAIL | FAIL | ✅ |
| P3 | لا READY من المحرّك على S1 | READY = 0 | ✅ |
| P4 | DXST ⟵ B أو D | D | ✅ |
| P5 | VEEE ⟵ AMBIGUOUS | UNKNOWN | ❌ |
| P6 | ATMV ⟵ DATA_UNAVAILABLE | DATA_UNAVAILABLE | ✅ |
| P7 | poolcap2 لا يطابق V3.1 بت-بت · والحكمُ UNKNOWN | مطابق=True · UNKNOWN | ❌ |
⟵ صدق 4 من 7.

## ⑥ §40 — هل يعيد المحرّكُ قرارَ فيصل على شارتٍ جديد؟
**جزئيًّا · ولا دليلَ احتجازٍ على المستويات:** الاكتشاف PASS والاحتجاز FAIL (الفرقُ موجبٌ +0.2466 والفاصلُ يلامس الصفر -0.0094) · والفئةُ FAIL في كلّ المجموعات · والكلمةُ لا تتجاوز «دائمًا WAIT». الباقي بالضبط: معلوماتُ الصلاحيّة الحيّة · وعيّنةُ احتجازٍ أكبر · وفصلُ الاختيار التقديريّ (DXST) عن القاعدة.

## ⑦ بوّابةُ الإكمال (§39)
| البند | الحالة | الدليل |
|---|---|---|
| Full corpus reconciled | ✅ | 722/722 SHA · 14_TELEGRAM_…json |
| Telegram batch reconciled | ✅ | 11/11 |
| Provenance verified | ✅ | طبقات 1/2/2b/X لكلّ وحدة · تصحيحاتُ C01-C15 |
| Third-party evidence separated | ✅ | الطبقة X لا تصنع وسمًا (V4L3) |
| All major pattern families audited | ✅ | 36 مكوّنًا بحالةٍ (12_RULE_AUDIT) |
| All major structural rules audited | ✅ | R4-BOT/HOLD/CYC/ZONE/HOLDZ/SWEEP/INV/LOC |
| Target methodology audited | ✅ | 08_TARGET_FORENSICS |
| READY/WAIT/REJECT reconstructed | ⚠️ جزئيّ | البنيةُ والموقعُ نعم · والكلمةُ تتبع صلاحيّةً غيرَ مرئيّة (UNKNOWN) |
| Decision hierarchy reconstructed | ✅ | 02 · 03 |
| Contradiction search completed | ✅ | 19 تعارضًا (07) |
| Single-image rules identified | ✅ | 0 قاعدةً نشطة بصورةٍ واحدة |
| Backtest-derived rules isolated | ✅ | backtest_derived = False لكلّ قاعدة (V4L7) |
| Golden Cases explained | ✅ | 09 |
| Golden Case overfitting ruled out | ✅ | لا رمزَ ذهبيٌّ في المحرّك (V4L7) · الذهبيّةُ تحقّقٌ لا مصدر |
| DXST classified | ✅ | D |
| VEEE classified | ✅ | UNKNOWN (بعديّ: DATED_POSTHOC) |
| ATMV classified | ✅ | DATA_UNAVAILABLE |
| 30m data limitation documented | ✅ | v4_cov30.json |
| Pressure Pool downstream effect measured or explicitly UNKNOWN | ✅ | UNKNOWN |
| V4 implementation complete where justified | ⚠️ جزئيّ | H-LEVEL الاحتجاز FAIL ⟵ «عرضُ بنية» لا أداةُ قرار |
| V3.1 preserved | ✅ | لا ملفَّ في faisal_method_v3/ عُدِّل في V4 (يُتحقَّق بـgit diff قبل كلّ دمج) |
| Mutation tests pass | ✅ | 36/36 |
| Unit/Integration/Regression/Mutation/Look-ahead/Data-quality/Determinism tests pass | ❌ | — |
| Visual validation complete where data exists | ✅ | 26 طبقة |
| CI green | ✅ (#547) · ⏳ PR النتائج | 37068980702 · 37068947244 · 37068980761 · ومعرّفاتُ PR النتائج تُسجَّل في الذاكرة بعد الدمج |
| Main CI green | ✅ (#547) · ⏳ بعد دمج النتائج | 37069716913 |
| Production unchanged | ✅ | §37 |
| Every READY/WAIT/REJECT/UNKNOWN explainable | ✅ | explain في كلّ كائن (05) |

## ⑧ الحالةُ النهائيّة (§43)
```
================================================
FAISAL METHOD V4 — FINAL STATUS
================================================

STATUS:
PARTIALLY COMPLETE

CORPUS:
722 صورة في السجلّ · موجودة 722 · مطابقةُ SHA-256 722 · وحداتٌ مستقلّة 609 (‏102 عنقودًا متعدّد الأعضاء) · 602 بعد دمج V3.1 البصريّ · مرورُ V4 609 سجلًّا · صورٌ أوّليّة (فيصل · طبقة 1) 265 · قواعدُ V3.1 369 · تلغرام 11/11 (مكرّر 1 · محتوى أوّليّ 3)

METHODOLOGY:
خطّ القرار المُعاد بناؤه (مُعدَّلٌ بالدليل): البيانات ⟵ القاع/الدورة (البنية) ⟵ الثبات 5 جلسات ⟵ صعودُ الاختبار ⟵ منطقةُ 15% فوق القاع (الموقع) ⟵ الثبات فيها أو سحبٌ ثمّ عودة (التأكيد) ⟵ الصلاحيّة حاجبٌ لا يرقّي ⟵ الدخولُ آليّةٌ (طلباتٌ عند الدعم) ⟵ الإبطال ⟵ الأهداف (معلومةٌ لا قرار) · والنموذجُ (W) معلومة · و«المضارب» عاملٌ حاسمٌ غيرُ مرئيٍّ في الشموع

DECISION ENGINE:
READY = جاهزيّةٌ فنيّة (BASE_HELD · RETEST_HELD · PRESS_RECLAIM) ‏+ صلاحيّةٌ معلومةٌ نظيفة · WAIT = قاعٌ يتكوّن/مكسور/سحبٌ جارٍ/فوق المنطقة/في المنطقة بلا ثبات · أو طرحٌ/شورتٌ فوق 20,000 · REJECT = قروبات · UNKNOWN = بياناتٌ ناقصة أو جاهزيّةٌ فنيّةٌ بلا معلومة الصلاحيّة (بقائمة الناقص) — والتحقّق: H-LEVEL الاحتجاز FAIL (+0.2466 [-0.0094 · +0.5873] · مستويات 22 · حالات 7) ⟵ المحرّكُ «عرضُ بنيةٍ» لا مُعيدٌ لمستويات فيصل (§⑭)

NEW GENERAL RULES:
R4-DATA-01 (CONFIRMED · DECISIONAL · هندسيّة) · R4-BOT-01 (SUPPORTED · DECISIONAL · مستوى 2 · صور 5) · R4-HOLD-01 (SUPPORTED · DECISIONAL · مستوى 3 · صور 5) · R4-CYC-01 (CONFIRMED · DECISIONAL · مستوى 3 · صور 13) · R4-ZONE-01 (SUPPORTED · DECISIONAL · مستوى 1 · صور 5) · R4-HOLDZ-01 (PROBABLE · DECISIONAL · مستوى 2 · صور 4) · R4-SWEEP-01 (SUPPORTED · DECISIONAL · مستوى 2 · صور 7) · R4-INV-01 (SUPPORTED · DECISIONAL · مستوى 2 · صور 5) · R4-LOC-01 (CONFIRMED · DECISIONAL · مستوى 2 · صور 4) · R4-OP-01 (SUPPORTED · UNKNOWN · مستوى 2 · صور 6) · R4-VAL-GRP-01 (SUPPORTED · DECISIONAL · مستوى 2 · صور 6) · R4-VAL-OFF-01 (SUPPORTED · DECISIONAL · مستوى 2 · صور 4) · R4-VAL-SHORT-01 (PROBABLE · DECISIONAL · مستوى 2 · صور 3) · R4-ENT-01 (CONFIRMED · SUPPORTING · مستوى 2 · صور 6) · R4-ENT-02 (SUPPORTED · INFORMATIONAL · مستوى 2 · صور 5) · R4-STOP-01 (SUPPORTED · SUPPORTING · مستوى 2 · صور 5) · R4-TGT-01 (CONFIRMED · INFORMATIONAL · مستوى 2 · صور 5) · R4-TF-01 (SUPPORTED · INFORMATIONAL · مستوى 2 · صور 4)

RULES REJECTED:
R-W-SPAN ⟵ في V4: مُدمَجةٌ في R4-BOT-01 (القاعُ = الأدنى) — لا تُستعمل منفصلة · R-SUP-MAIN ⟵ في V4: هو تعريفُ القاع (R4-BOT-01) · والدعمُ فوقه يُقرأ بالجسم والدعم الثاني والمنطقة · H-D2 ⟵ لا أثر · وتصحيحاتُ الدفتر: نطاقُ السحب 7-13 و`PIVOT_SWEEP_PCT` ⟵ تبنّيًا (لا لفظَ فيصل) · `TG_38_NUWE` ⟵ طرفٌ ثالث · ومكوّناتُ «UNKNOWN» في التدقيق: BOS_CHOCH · CHANNEL · FLAG · PENNANT · TRIANGLE

TARGET:
«100٪» مقرونةً بـ«هدف» عند فيصل = مسافةُ ربحٍ ‏+100% · «50٪/70٪» ليست إسقاطَ نموذج (70٪ = كمّيّةُ جني الربح الأوّل) · والأهدافُ سلّمُ مقاوماتٍ أفقيّ — معلومةٌ لا تغيّر الحالة (R4-TGT-01)

GOLDEN CASES:
قبل (V3.1) 3/7 · بعد (V4) 4/7 · وخطُّ «دائمًا WAIT» 5/7 ⟵ لا تحسّنَ مُثبَت · DXST D (MANUAL_JUDGMENT_UNREPRODUCIBLE) · VEEE UNKNOWN (والبعديّ DATED_POSTHOC ['2026-05-15']) · ATMV DATA_UNAVAILABLE · والعامُّ: S3 H-LEVEL FAIL

CONTRADICTIONS:
C-BREAKOUT (UNRESOLVED) · C-CYCLE-VS-CHECKLIST (PARTIALLY_RESOLVED) · C-OPTIMING (UNRESOLVED) · C-SHORT-THRESHOLD (UNRESOLVED) · C-SUPPORT10 (UNRESOLVED) · C-SWEEP-DEPTH (RANGE_NOT_NUMBER) · C-STOP-REF (UNRESOLVED) · C-STOP-VS-SWEEP (UNRESOLVED) · C-HOLD-SESSIONS (RANGE_NOT_NUMBER) · C-GROUPS (PARTIALLY_RESOLVED) · C-AUTO-LEVELS (RESOLVED_FOR_V4) · C-SUCCESS-DEF (UNRESOLVED) · C-AUTHOR-DARKCHANNEL (UNRESOLVED_OWNER_QUESTION) · C-AUTHOR-PALMTREE (RESOLVED (النخيلُ جهازُ فيصل)) · C-TRIG-ABOVE-HOLDER (RESOLVED_BY_CONVENTION) · C-T7 (RESOLVED ($7 سعر · STRONGLY_SUPPORTED)) · C-FOGGY (DISSOLVED (خطأُ قراءة)) · C-MA-TARGET (UNRESOLVED) · C-PURPLE (PRIMARY=DEMAND · NOT EXCLUSIVE)

PRESSURE POOL:
UNKNOWN — إعادةُ poolcap2 طابقت V3.1 بت-بت (‏272 · 177 · 0.5061) · والمحاكي لا يعيد سجلَّ الإنتاج (اتّفاق 0.5061 دون 0.60) ⟵ «إشاراتُ تلغرام الصالحة المفقودة بسبب السقف وحدَه» UNKNOWN

DATA LIMITATIONS:
ATMV بلا شموع من أيّ مصدر · 30 دقيقة: 31 رمزًا بشموع · 22 منها عند سقف الطلب 5000 · أقدمُ شمعة 2021-03-26 11:30 (لا عشر سنوات) · VEEE: مرساةُ العقد سقطت (قمّةُ الستّين 23.05 لا 8.80) · الصلاحيّة (القروبات · الطرح · الشورت · المضارب) غيرُ مؤرَّخةٍ تاريخيًّا ⟵ UNKNOWN · Polygon منتهٍ · X والمحادثاتُ الأخرى غيرُ متاحة · الـartifact وروابطُ السجلّ الموقَّعة محجوبةٌ من الجلسة

TOOL:
محرّكُ V4 (`FAISAL-V4 1.0 (2026-10-02)`) فوق دوالّ V3.1 المحفوظة · سجلُّ 21 قاعدة · كائنُ قرارٍ قابلٌ للتفسير · faisal_v4.yml يدويٌّ للقراءة · ولا تغييرَ في V3/V3.1

TESTS:
لم تُشغَّل بعد

MUTATIONS:
36/36 سقطت كلٌّ بقفلها

CI:
Tests 37068980702 success · Tests 37068947244 success · Lint 37068980761 success · Tests 37069716913 success (العقد #547) · وCI لـPR النتائج يُسجَّل في الذاكرة بعد الدمج

PRODUCTION:
UNCHANGED — لا كرون · لا ماسح · لا تلغرام · لا عتبة · لا سقف بِركة · لا كون · لا منطقَ دخول · والوسومُ المصحَّحة توثيقٌ (الأرقامُ في الكود بت-بت)

REMAINING BLOCKERS:
① لا مصدرَ تاريخيٌّ لمعلومات الصلاحيّة (قروبات · طرح · شورت · بصمةُ المضارب) ⟵ كلمةُ READY/WAIT غيرُ قابلةٍ للإعادة آليًّا · ② عيّنةُ الاحتجاز صغيرة (10 حالات · 7 بمستويات) · ③ DXST حكمٌ تقديريّ · ④ ATMV بلا بيانات · ⑤ بِركةُ الضغط: المحاكي لا يعيد الإنتاج

NEXT HIGHEST-VALUE ACTION:
حصادٌ أماميٌّ مسجَّلٌ مسبقًا: كلُّ قرار READY/WAIT جديدٍ لفيصل يُلتقط يومَ صدوره مع معلومات الصلاحيّة الحيّة (قروبات · طرح · متاح الشورت) ويُقارَن بمحرّك V4 المجمَّد — اختبارُ احتجازٍ نظيفٌ لم يُرَ ولا يتعفّن
```
