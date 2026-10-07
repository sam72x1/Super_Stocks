# 🧊🔒 FAISAL V4 — FINAL PROSPECTIVE VALIDATION PROTOCOL — التسجيلُ المسبق (العقد)

> **أمرُ المالك 2026-10-07:** «FAISAL V4 — FINAL PROSPECTIVE VALIDATION PROTOCOL / FROZEN-MODEL / BLIND-FIRST / ANTI-CONTAMINATION /
> ANTI-LEAKAGE / OBJECTIVE: DETERMINE WHETHER V4 ACTUALLY REPRODUCES FAISAL'S DECISIONS / DO NOT MODIFY V4 / DO NOT REBUILD THE CORPUS /
> DO NOT OPTIMIZE FOR THE VALIDATION SET».
> **هذا العقدُ يُدمَج قبل أيّ رقمٍ جديد** — قبل الأداة وقبل أيّ تصنيفٍ أو عدٍّ بتعريفاته. يُبنى فوق `V41_prereg.md` (§⑥-⑨) ولا ينسخه:
> حيث يختلفان **يغلب الأشدّ**. مصطلحاتُ المالك (الحقولُ والأصنافُ والحالاتُ والمراحل) تُكتب بنصّها الإنجليزيّ · وكلُّ ما أضفتُه لسدّ فجوةٍ
> في نصّ البروتوكول موسومٌ **🧩 سدُّ فجوة** صراحةً · وكلُّ عتبةٍ بمصدرها.

## ⓪ السؤال · والحالاتُ النهائيّة الخمس
- **السؤال:** هل يُعيد V4 **المجمَّد** قراراتِ فيصل **الجديدة** (READY / WAIT / REJECT) **أماميًّا وأعمى**، على حالاتٍ لم تُستعمل في بنائه؟
  المطلوب **جوابٌ تجريبيّ لا حجّةٌ نظريّة**.
- **الحالاتُ النهائيّة (واحدةٌ فقط):** `VALIDATED` · `PARTIALLY_VALIDATED` · `NOT_VALIDATED` · `INSUFFICIENT_SAMPLE` · `VALIDATION_BLOCKED` (قواعدُها §⑱).
- **IMPORTANT DISTINCTION:** تدقيقُ المدوّنة (EX · #562 · «YES — محدودةٌ بالمتاح») **ليس** صحّةَ V4 — يُطبع `CORPUS_AUDIT = COMPLETE` ولا يُستشهد به على V4.

## ① إفصاحاتٌ قبل الرقم (ما أعرفه الآن · لا يُبنى عليه بعد الرقم)
1. **فضاءُ مخرَج V4 الأماميّ (قفلُ FVO1 القائم):** السياقُ الآليّ يترك القروباتِ والطرحَ والمضاربَ `None` دائمًا ⟵ `validity` تُرجع ناقصًا
   بلا حاجبِ REJECT ⟵ **مخرجُ V4 الأماميّ ∈ {WAIT · UNKNOWN} بالبناء.** ويترتّب عليه قبل أيّ حالة:
   (أ) V4 لا يقول READY ولا REJECT في هذه الحقبة · (ب) **كلُّ تطابقٍ لـV4 تطابقٌ لـ«دائمًا WAIT» أيضًا** ⟵ V4 لا يتقدّم على خطّ الأساس في
   حالةٍ واحدة · (ج) `VALIDATED` غيرُ بالغٍ في الحقبة 1 بالبناء (§⑳-P4). **ولا يُغيَّر شيءٌ لتجاوز هذا** (تغييرُ مصدر البيانات ممنوع — §②).
2. **معدّلُ READY التاريخيّ عند فيصل 4.55%** (S1 · `results/analysis_v41.json`) ⟵ 43 حالةَ READY تحتاج ≈946 حالة (≈28.6 سنةً بمعدّل S1
   2.757 حالةً/شهر) ⟵ تحقّقُ صنف READY ليس في الأفق القريب — **مُعلَنٌ لا مُغطّى**.
3. **الحالةُ الأماميّةُ الكاملةُ الوحيدة CASE_0001 (BRTX):** V4 قال WAIT (`BROKEN_NEW_BASE`) وفيصل «مراقبه مبكره» ⟵ WATCH ⟵ WAIT ⟵ تطابق
   (`batches/B48_20261007/PROSPECTIVE_BATCH_48_RESULTS.json`). **ومصدريّتُها معروفةٌ الآن:** جُمعت قبل #558 فلا مصدرَ توجيه · ولقطةُ منشور X
   بلا طابعٍ مطلق · وتاريخُ القرار 2026-10-03 **مستنتَجٌ من محتوى الصورة** («منذ التقسيم 25 يوم» ‏+ تقسيم 8-9-2026) ⟵ بتعريف §⑤:
   `PROVENANCE_CONFIDENCE = LOW` ⟵ **SECONDARY لا PRIMARY**. والقاعدةُ تُقصي **تطابقًا** (لا تخدم V4) وكُتبت لكلّ حالةٍ لا لهذه.
4. **دفعةُ B48 بالأصناف الخمسة منشورة** (CLEAN 2 · CONTAMINATED 9 · DUPLICATE 2 · DERIVATIVE 9 · UNKNOWN 26 · بأسبابها الفرعيّة) ⟵
   إعادةُ رسمها بالأصناف السبعة (§⑦) **آليّةٌ** — والأعدادُ الناتجة متنبَّأٌ بها في §⑳-P2 قبل أن تحسبها الأداة.
5. **تحقّقان كوديّان أُجريا قبل هذا العقد (هويّةُ كود لا نتيجةُ تحقّق):** ملفّاتُ V4 الواحد والثمانون عند `7c8826c` **تطابق** بصماتِ
   `docs/V4_FREEZE_MANIFEST.json` (81/81) · وإغلاقُ خطّ البيانات (§② · 93 مكوّنًا: 22 من tv_data · 10 من Super_stock · 2 من market_calendar · 5 من v4_run · 28 من runner · 26 من ctb_harvest) عند commit تشغيلة CASE_0001 (`ea9e266`) **= الرأس الآن**
   (صفرُ اختلاف).
6. **الجامع:** كود #558 قائمٌ وأقفالُه TCM1-TCM7 خضراء · **والمسارُ الحيّ بعده لم يُختبَر** (التشغيلة `37652483700` جمعت صفرًا) · وتلغرام
   يحفظ التحديثَ غيرَ المسحوب ≈24 ساعة · وتأخّرُ كرونات GitHub المقيس عندنا 257-361 دقيقة (وبلغ 666-731 مرّةً).
7. **لا صورةَ جديدةً تنتظر الالتقاط الآن** ⟵ أوّلُ حالةٍ أماميّةٍ بهذا العقد تأتي من الجمع المجدول بعده (§⑥).

## ② التجميد — ABSOLUTE RULE #1 (V4 IS FROZEN)
- **الحقبة 1 (`EPOCH 1`)** تُسجَّل مرّةً واحدة في `faisal_method_v41/final_protocol/EPOCH_FREEZE.json` **قبل أيّ حالةٍ جديدة** — إلحاقيّ:
  حقبةٌ جديدة تُضاف بإذن المالك ولا تُعدَّل القائمة (قفلٌ يثبّت بصمتها). المعرّفاتُ الخمسة:
  - **`V4_COMMIT`** = `7c8826c25e745668d33facabb2efbc488e997fb7` (commit التجميد الرسميّ #550) ‏+ `freeze_id` من البيان ‏+ **شهادةٌ لمرّةٍ واحدة**
    أنّ كلَّ ملفٍّ مجمَّدٍ عنده = بصمةَ البيان (تتطلّب تاريخ git · تُكتب في السجلّ ولا تُعاد في السويّة).
  - **`V4_CONFIG_HASH`** = SHA-256 لـJSON قانونيّ **من الاستيراد الحيّ**: نسخةُ المحرّك ونسخةُ السجلّ · `PARAMS` · `STATE_DECISION` · `STATE_RULE`
    (`freeze.config_snapshot` بلا القواعد).
  - **`V4_RULE_REGISTRY_HASH`** = SHA-256 لسجلّ القواعد (`config_snapshot()["rules"]`).
  - **`V4_TOOL_VERSION`** = {المحرّك · السجلّ · `runner.RUNNER_VERSION` · `freeze.FREEZE_VERSION`} — **وأداةُ هذا البروتوكول ليست منه** (تقريرٌ لا منهج).
  - **`DATA_PIPELINE_VERSION`** = SHA-256 لخريطة {مكوّن: بصمة} ‏+ تثبيتات `requirements.txt` لـ`yfinance` · `websocket-client` · `requests` · `pandas`
    · `numpy`. **والمكوّناتُ = الإغلاقُ الساكن (AST)** من مداخل الجلب: `runner.{fetch_rows · fetch_splits · live_borrow · validity_context ·
    load_ctb · snapshot · firewall · decide · run_case · is_session · prev_trading_days · next_trading_day}` و`ctb_harvest.harvest` — متبوعًا
    عبر الوحدات (`tv_data` · `Super_stock` · `market_calendar` · `v4_run`) بأسمائها المستوردة · وبصمةُ كلّ مكوّنٍ من شجرته **بلا docstring
    ولا تعليقات** وبمسلسِلٍ لا يتأثّر بنسخة بايثون ⟵ تعديلُ دالّةٍ خارج الإغلاق لا يكسرها · وتعديلُ أيّ دالّةٍ أو ثابتٍ فيه يكسرها.
- **السلامة (PHASE 18) قبل كلّ تشغيلٍ ودفعة — I1-I12:** I1 `V4_FROZEN` (FV41 كاملًا) · I2 `freeze_id` = الحقبة · I3 `V4_CONFIG_HASH` حيًّا =
  الحقبة · I4 `V4_RULE_REGISTRY_HASH` · I5 `V4_TOOL_VERSION` · I6 `DATA_PIPELINE_VERSION` · I7 لا مراجعةَ تجميدٍ بعد الحقبة · I8 السجلُّ
  الإلحاقيّ سليم (`ledger.verify`) · I9 بادئةُ `telegram_collect_meta.jsonl` عند الحقبة لم تتغيّر (إلحاقٌ فقط) · I10 كلُّ صورةٍ لحالةٍ مختومة
  بصمتُها = المسجَّلة · I11 كلُّ قرار V4 جديد يحمل `pipeline_version` الحقبة (والقديمُ بشهادةٍ §①-5) · I12 لا تسرّبَ من صنف العيب (§⑯).
  **أيُّ فشلٍ ⟵ `VALIDATION_BLOCKED`** · والمشغّلُ يرفض تشغيلَ V4 برمز خروجٍ مميَّز ولا تُختم حالةٌ جديدة **حتى يُعلن المالكُ حقبةً جديدة**.
- **ما لا يكسر الحقبة:** كودُ التنسيق والتقارير (أداةُ البروتوكول · الوثائق · مسارُ `mode_run` خارج الإغلاق) — ما دامت المعرّفاتُ الخمسة ثابتة.
- **ما يكسرها بالبناء:** أيُّ تغييرٍ في القواعد · العتبات · مخطّط القرار · المؤشّرات · الأهداف · الصلاحيّة · المعالجة المسبقة · الميزات · مصدرِ
  البيانات · وأيُّ رقعةٍ لرمزٍ أو تاريخٍ أو صورة — **ولو إصلاحًا لعطلٍ غيرِ منهجيّ:** يُصلَح على فرعٍ مستقلّ ثمّ حقبةٌ جديدة بإذن المالك
  **ولا تُخلط حالاتُ حقبتين أبدًا**. ⚠️ **مُعلَنٌ لا مُغطّى:** إصلاحٌ إنتاجيّ في `tv_data.py` أو `ce_borrow_info` أو `ctb_harvest.py` أو عطلاتِ
  `market_calendar` **يُوقف التحقّق** (يظهر BLOCKED ويُسمّى المكوّنُ المتغيّر) — مقصودٌ بأمر المالك «Do NOT silently continue».

## ③ العمى — ABSOLUTE RULE #2
- **الترتيب:** `INPUT ⟵ V4 ⟵ V4 RESULT SEALED ⟵ ONLY THEN ⟵ FAISAL DECISION REVEALED` — مضمونٌ بالسجلّ الإلحاقيّ (`seal_case` ⟵ `record_v4` ⟵
  `record_faisal` يرفض بلا قرار V4 مختوم · FV48) ويُفحص في كلّ حالة (LA3 · §⑯).
- **مُدخَلُ V4** = الرمز · تاريخُ القرار · السياقُ الآليّ — وحدَها: شموعُ TradingView **قبل يوم القرار حصرًا** ‏+ المتاحُ من حصّاد الاقتراض
  (أو جلبٌ حيٌّ داخل جلسةٍ من القرار) ‏+ الباقي `None` بسببه. **لا** صورة · تعليق · شرحٌ لاحق · تعليقاتٌ على الشارت · نتيجةُ هدف · شموعٌ مستقبليّة.
- **الحدُّ المُعلَن (من V41):** الملتقِطُ يرى الصورةَ وفيها الكلمة — فالضمُّ والتاريخُ والفريمُ **آليّةٌ بقواعد هذا العقد** ولا قناةَ منها إلى مُدخَل V4.

## ④ «جديد يعني جديد» — ABSOLUTE RULE #3 (ثمانيةُ فحوصٍ لكلّ مرشَّح)
- **C1 exact hash:** SHA-256 مقابل المدوّنة المجمَّدة (722 · `image_corpus.json`) وكلِّ ملفٍّ في `faisal_images/` وكلِّ مرشَّحٍ سابق.
- **C2 perceptual hash:** dHash256 ≤ 24 **و** pHash64 ≤ 10 (قاعدةُ V3 `corpus_build.dedup` · BB4) مقابل المدوّنة والمرشَّحين السابقين.
- **C3 visual similarity:** نصُّ OCR بجاكارد ≥ 0.85 على 15 كلمةً فأكثر حين يتوفّر OCR (وإلّا `NOT_RUN` مكتوبًا) **و**مراجعةٌ بالعين **إلزاميّة**
  مقابل أقرب خمس صورٍ إدراكيًّا (تسردها الأداة) تكتب `NONE` أو المعرّفات.
- **C4 ticker/date:** الرمزُ ‏+ تاريخُ القرار ±3 أيّام في حالات V4 (157) أو الذهبيّة (`batch_intake.case_overlap`).
- **C5 chart-window 🧩:** الرمزُ نفسُه في **مجموعة التطوير** بتاريخٍ داخل نافذة **الـ120 جلسةً** قبل تاريخ القرار حتى يومه (= `CYCLE_BARS`
  المجمَّد) ⟵ CONTAMINATED. **مجموعةُ التطوير** = صفوفُ جرد EX غيرُ B48 (‏`MASTER_CORPUS_INVENTORY.json` · والتاريخُ الجزئيّ «2026-09-1x» يُمدّ
  لمداه) ‏+ حالاتُ V4 (`cases_v4.json`) ‏+ الذهبيّة — **ثلاثةُ مصادر مجمَّدة لا يغيّرها الأماميّ** · وB48 ليس منها (مادّةٌ بعد التجميد).
- **C6 known derivative:** مشتقٌّ معروف (قصّ · تعليم · إعادةُ نشر) لصورةٍ في المدوّنة أو لمرشَّحٍ أسبقَ في الدفعة نفسِها (C2/C3 ‏+ وسمُ العين).
- **C7 corpus cross-reference:** الملفُّ أو معرّفُه في سجلّ المدوّنة المجمَّد أو المرور البصريّ لـV4 أو جرد EX كوحدةٍ تطويريّة.
- **C8 prior V4 exposure 🧩:** الرمزُ ‏+ تاريخٌ داخل نافذة الـ120 في قرارات V4 التطويريّة (حالاتُ V4 المحسوبة · تواريخُ الذهبيّة) ⟵ CONTAMINATED ·
  وتشغيلاتُ smoke بعد التجميد على الرمز نفسِه تُسجَّل **إفصاحًا** لا تلوّثًا (V4 مجمَّد والضمُّ آليّ).
- **حالتان أماميّتان** على الرمز نفسِه بتاريخين = قراران مستقلّان (الثاني يُوسَم `follow_up_of` للتنوّع) · وبالرمز والتاريخ نفسِهما = DUPLICATE
  (حالةٌ واحدة · أسبقُها برقم الرسالة) — **ولا يُعَدّ المشتقُّ والمكرَّر**.

## ⑤ المصدريّة — ABSOLUTE RULE #4
- **الحقولُ الثلاثة عشر بنصّها لكلّ مرشَّح:** `CASE_ID` · `SOURCE` · `SOURCE_MESSAGE_ID` · `CAPTURE_TIMESTAMP` · `ORIGINAL_POST_TIMESTAMP` ·
  `FORWARD_TYPE` · `PUBLIC_CHANNEL_METADATA` · `IMAGE_HASH` · `PERCEPTUAL_HASH` · `TICKER` · `TIMEFRAME` · `DATE_VISIBLE` · `PROVENANCE_CONFIDENCE` —
  والمجهولُ **`UNKNOWN` مكتوبًا لا مخمَّنًا**.
- **🧩 الحرجة (لم يسمّها البروتوكول):** `SOURCE` · `SOURCE_MESSAGE_ID` · `CAPTURE_TIMESTAMP` · `ORIGINAL_POST_TIMESTAMP` · `FORWARD_TYPE` ·
  `IMAGE_HASH` · `PERCEPTUAL_HASH` · `TICKER` · `TIMEFRAME`. (`PUBLIC_CHANNEL_METADATA` = `N/A` لغير القناة العامّة · و`DATE_VISIBLE` وصف.)
- **`ORIGINAL_POST_TIMESTAMP` «معلوم» في حالتين فقط:** (أ) من بيانات توجيه تلغرام (`forward.date`) · (ب) طابعٌ زمنيٌّ **مطلق ظاهر** في الصورة
  لمنشور فيصل نفسِه يُنقل حرفًا مع موضعه. **تواريخُ الشارت لا تكون طابعَ منشور** (حدٌّ أدنى لا أكثر) · وشهادةُ المالك بلا سندٍ آليّ لا ترفعه.
- **`FORWARD_TYPE` «معلوم»** = نوعُ التوجيه أو `none` صريحًا (صفوفُ الجامع `meta_v 2`) — وغيابُ الحقل في صفٍّ أقدم = `UNKNOWN`.
- **`PROVENANCE_CONFIDENCE`:** `HIGH` (الحرجةُ كلُّها معلومة والطابعُ من التوجيه) · `MEDIUM` (الحرجةُ معلومة والطابعُ ظاهرٌ في الصورة) ·
  `LOW` (حرجٌ مجهول لكنّ التاريخ محصورٌ بمحتوى الصورة ووقتِ الالتقاط) · `UNKNOWN` (ما سواه).
- **PRIMARY = HIGH أو MEDIUM** — وحدَه يدخل مقاييسَ التحقّق · **SECONDARY = LOW أو UNKNOWN** — يُتتبَّع ويُطبع منفصلًا **ولا يُدمج مع الأساسيّ أبدًا**.
- **تاريخُ القرار للأساسيّ** = تاريخُ نيويورك لطابع المنشور الأصليّ — ولو نُشر بعد الإغلاق (محافظ: V4 يرى ما رآه فيصل أو أقلّ لا أكثر · مُعلَن).
  وطابعُ تلغرام UTC مطلق · **والطابعُ الظاهر يُقرأ بتوقيت الرياض** (جهازُ المالك) ما لم تُظهر الصورةُ منطقةً أخرى — وإن لم يُعرف جهازُ اللقطة ⟵ `LOW`.

## ⑥ الجامع — PHASE 1-2
- **القفلُ يتحقّق من حفظ:** تاريخ المنشور الأصليّ · نوع التوجيه · بيانات القناة العامّة · رقم الرسالة · وقت الجمع · SHA-256 · البصمة الإدراكيّة ·
  المصدريّة بلا هويّة · وسمُ «من مستلمي التقرير» — **سلوكيًّا بتلغرامٍ وهميّ** ‏+ طفراتٌ تُسقطه.
- **التعديلات:** `meta_v: 2` · `forward_type` صريح (`none` حين لا توجيه) · `dhash256`/`phash64` للصورة المحفوظة **عند الجمع** (دوالّ V3 نفسُها ·
  فاشلةٌ-آمنة ⟵ `null` مكتوب لا حذف) · **صفُّ فجوة** (`kind: gap`) حين يمضي على آخر جمعٍ ناجحٍ أكثرُ من 24 ساعة (`RETENTION_WINDOW_EXCEEDED`
  بمداه) أو تقفز أرقامُ التحديث (`UPDATE_ID_GAP` — «محتمل» لا «فقدٌ مؤكَّد»: أنواعُ تحديثٍ غيرُ مطلوبة تستهلك أرقامًا) — **ولا يُخترع ما فُقد**.
- الإلحاقُ فقط · لا كتابةَ فوق صورة · لا هويّةَ شخصيّة (قواعدُ TCM1-TCM7 كما هي).
- **الجدولة: كلَّ 4 ساعات** (‏الدقيقة 17) — الحفظُ 24 ساعة وتأخّرُ GitHub ≈6 ساعات (وأكثرَ نادرًا) ⟵ اليوميُّ قد يفوّت · والأربعُ تُبقي أسوأَ فجوةٍ
  مقيسة ≈10-16 ساعة. ⚠️ **أثرٌ جانبيّ مُعلَن:** كلُّ ما يُرسَل للبوت يُنشر في المستودع العامّ آليًّا خلال ساعات — **فلا تُرسَل له صورٌ خاصّة**.
- **قبولُ المسار الحيّ (يحسمه أوّلُ دفعةٍ `meta_v 2` تدخل الاستلام):** كلُّ صفّ صورةٍ محفوظةٍ فيها يحمل `message_id` · `date` · `collected_utc` ·
  `run_id` · `sha256` · `dhash256` · `phash64` · `forward_type` ⟵ `COLLECTOR = PASS` · وإلّا `FAIL` ⟵ `VALIDATION_BLOCKED`. وقبلها:
  `PASS_SIMULATED` (الأقفال) · `LIVE_PENDING`.

## ⑦ التصنيف — PHASE 3 (صنفٌ واحد لكلّ مرشَّح · بالأسبقيّة)
1. **DUPLICATE** ⟵ C1 · أو `file_id` سبق تنزيلُه.
2. **DERIVATIVE** ⟵ C2 · C3 · C6.
3. **CONTAMINATED** ⟵ C4 · C5 · C7 · C8 · أو «مثالٌ رآه V3/V4» من العين.
4. **PRE_EXISTING** ⟵ تاريخُ القرار (أو حدُّه الأعلى الظاهر) قبل **2026-10-03**.
5. **UNKNOWN** ⟵ غيرُ مقروء · لم يُراجَع بالعين · الكاتبُ لا يُثبَت.
6. **INSUFFICIENT_CONTEXT** ⟵ الكاتبُ معلوم لكن: ليس فيصل · أو بلا رمز · أو بلا عبارةِ قرار · أو تاريخُ القرار لا يُثبَت.
7. **NEW_PROSPECTIVE** ⟵ ما سوى ذلك — **وحدَه يدخل التجربة**.
- **الرسمُ من رموز B48 القائمة:** EXACT ⟵ DUPLICATE · NEAR/VISUAL ⟵ DERIVATIVE · SAME_CASE/SEEN_EXAMPLE ⟵ CONTAMINATED · HISTORICAL_BEFORE_WINDOW ⟵
  PRE_EXISTING · UNREADABLE/NOT_REVIEWED/AUTHOR_NOT_ESTABLISHED ⟵ UNKNOWN · DATE_NOT_ESTABLISHED و(CLEAN مع NOT_FAISAL/NO_TICKER/NO_DECISION) ⟵
  INSUFFICIENT_CONTEXT · CLEAN المؤهَّل ⟵ NEW_PROSPECTIVE ثمّ C5/C8 عليه.

## ⑧ الختم — PHASE 4 (CASE SEAL)
- لكلّ NEW_PROSPECTIVE قيدُ `case` في السجلّ الإلحاقيّ يحمل فوق حقوله القائمة كتلةَ **`protocol`**: `provenance` (الحقولُ الثلاثة عشر والثقة) ·
  `blind_input` {symbol · decision_date · timeframe `1D`} · `input_hash` = SHA-256 لـ`blind_input` القانونيّ · `v4_freeze` (المعرّفاتُ الخمسة
  للحقبة) · `intake` (الصنف · السبب · الفحوصُ الثمانية) — **قبل** تشغيل V4 (السلسلةُ تثبت الترتيب). والصورةُ تبقى في `faisal_images/` محالةً
  ببصمتها (لا نسخة).
- **CASE_0001 قيدُه سابقٌ للعقد (`LEGACY`):** تُشتقّ كتلتُه من قيوده وصفّ الجامع **ولا يُعاد ختمُه** (الإلحاقُ فقط).

## ⑨ كائنُ قرار V4 — PHASE 5-6
| حقلُ البروتوكول | المصدر (قيدُ V4 المختوم) |
|---|---|
| `CASE_ID` · `V4_VERSION` · `V4_COMMIT` · `CONFIG_HASH` · `INPUT_HASH` | الحالة · `decision.engine`/`rules_version` · الحقبة ‏+ `meta.commit` · الحقبة · `protocol.input_hash` (والقديم: `case_sha256` ‏+ `snapshot_sha256`) |
| `DATA_AVAILABLE` | `firewall` (الحكم · الشموع · آخرُ شمعة) ‏+ `context_provenance` لكلّ حقل |
| `TIMEFRAME` · `STRUCTURE` · `PATTERN` · `BOTTOM/CYCLE` | `decision.timeframe` · `structure` · `patterns` · `structure.bottom/bottom_date` ‏+ `market_context.cycle_high` |
| `5_SESSION_HOLD` · `TEST_RISE` · `15_PERCENT_ZONE` · `HOLD/SWEEP_RETURN` | `hold_sessions` مقابل `HOLD_MIN` · `rise_pct` مقابل `RISE_TEST_PCT` · `zone` ‏+ `in_zone` · `undercut_pct`/`depth_pct` مقابل `SWEEP_MAX_PCT` ‏+ `HOLD_ZONE` |
| `VALIDITY` · `ENTRY_MECHANISM` · `INVALIDATION` · `TARGET` | `blocking_reasons` ‏+ `missing_information` ‏+ `context_input` · `entry` · `invalidation` · `target` |
| `FINAL_DECISION` · `DECISION_REASON` · `DECISION_GRAPH` · `FINAL_STATE` | `state` · `explain` ‏+ `decision_reasons` · المسارُ أدناه · `state` **حرفًا** |
- **`DECISION_GRAPH`** = `tech_state` ⟵ `STATE_DECISION` ⟵ `validity(context_input)` ⟵ النهائيّ — يُعاد حسابُه بدوالّ المحرّك المجمَّد ويجب أن يساوي
  المسجَّل (وإلّا `IMPLEMENTATION_BUG` مُعلَن). **`NEVER silently convert UNKNOWN to WAIT`** — قفل.
- **الختم (PHASE 6):** `decision_sha256` ‏+ بصمةُ القيد في السلسلة — قائمان (FV44/FV46/FV47).

## ⑩ قرارُ فيصل — PHASE 7
- `label` ∈ READY · WAIT · WATCH · REJECT · UNKNOWN · MIXED ⟵ `label4` بجدول L4 (WATCH ⟵ WAIT) · و**`evidence_class`:**
  **DIRECT** (كلمةُ القرار نفسُها في نصّ فيصل) · **STRONG_INFERENCE** (لا كلمة لكنّ نصَّه يفرض الوسم: شرطٌ/خطّة) · **WEAK_INFERENCE** (من علامات
  الشارت أو السياق بلا نصّ). و`evidence_quote` **جزءٌ حرفيٌّ من الاقتباس المسجَّل** (يُفحص آليًّا — لا إعادةَ صياغة).
- **WEAK ⟵ «ambiguous» ⟵ UNKNOWN فعّال** (والوسمُ الضعيف يُحفظ للإفصاح) · والقديم CASE_0001: **DIRECT** («مراقبه مبكره» ⟵ WATCH ⟵ WAIT).
- تُكتب مع الكلمة أسعارُ المكوّنات الأربعة بنصّها (§⑮) أو «غيرُ مذكور» — بعد ختم V4 وحدَه.

## ⑪ المطابقة — PHASE 8
- **MATCH** · **FALSE_READY** (V4 READY وفيصل WAIT/REJECT) · **FALSE_WAIT** (V4 WAIT وفيصل READY) · **FALSE_REJECT** (V4 REJECT وفيصل READY) ·
  **FALSE_UNKNOWN** (V4 UNKNOWN وفيصل معلوم) · **FAISAL_UNKNOWN** (فيصل UNKNOWN فعّالًا) · **UNRESOLVED** (فيصل MIXED).
- **🧩 سدُّ فجوة:** V4 WAIT وفيصل REJECT ⟵ `MISMATCH_WAIT_REJECT` · V4 REJECT وفيصل WAIT ⟵ `MISMATCH_REJECT_WAIT` — يُعدّان في MISMATCHES ولا يُحشران
  في `FALSE_*` المعرَّفة بنصّ المالك.
- **FALSE_READY أوّلًا** في كلّ تقرير.

## ⑫ طابورُ V4.2 وتحقيقُ FALSE_READY — PHASE 9-10
- لكلّ عدمِ تطابق: `V4_2_CANDIDATE` بالحقول السبعة (`CASE_ID` · `OBSERVATION` · `EVIDENCE` · `WHY_V4_FAILED` · `POSSIBLE_MISSING_RULE` ·
  `GENERALIZATION_STATUS` · `CONTRADICTING_CASES`) يُلحق بـ`V4_2_RESEARCH_QUEUE.md` (من JSON الحالة · `docs_v41`) — **لا تنفيذ ولا إعادةَ تشغيل**.
- لكلّ FALSE_READY: تقريرٌ بأحد الأسباب العشرة (`IMPLEMENTATION_BUG` · `DATA_BUG` · `MISSING_CONTEXT` · `EXTERNAL_INFORMATION` · `TIMEFRAME` ·
  `LOCATION` · `ENTRY_TIMING` · `VALIDITY` · `DISCRETION` · `UNKNOWN`) — و`EXTERNAL_INFORMATION` يلزمه دليلٌ مقتبس. **وفي الحقبة 1 FALSE_READY = 0 بالبناء** (§①-1).

## ⑬ التنوّع — PHASE 11
- الأبعادُ التسعة ⟵ مصادرها: النموذج (`pattern_f` · `patterns`) · الفريم · الرمز · **نظامُ السوق** (QQQ فوق/تحت متوسّط 50 عند آخر جلسةٍ قبل القرار —
  يُسجَّل في التشغيل · والقديم `UNKNOWN`) · **جودةُ الإعداد** (`tech_state`) · READY/WAIT/REJECT · **شريحةُ السعر** (أقلّ من 1 · 1-5 · 5-20 · 20 فأكثر ·
  من إغلاق V4) · **القطاع** (ياهو في التشغيل · وإلّا `UNKNOWN`) · **فئةُ السياق الخارجيّ** (من `external_codes` بكلماتٍ ثابتة).
- **LOW_DIVERSITY** عند **20** حالةً أساسيّةً متتالية بالمفتاح نفسِه (`tech_state` · `label4` فيصل) — **وسمٌ لا استبعاد ولا انتقاء**.

## ⑭ السجلّ · خطّ الأساس · المقاييس · UNKNOWN — PHASE 12-15
- **CASE_LEDGER:** صفٌّ لكلّ مرشَّحٍ وحالة · وملخّصٌ دوريّ N/MATCH/MISMATCH/FALSE_* — **بلا تعديلٍ مرحليّ**.
- **BASELINE_A = ALWAYS_WAIT** · **BASELINE_B = NONE** (لا خطَّ أساسٍ فنّيًّا مسجَّلًا مسبقًا في V41 · والفارزُ الإنتاجيّ غيرُ معرَّفٍ as-of لرمزٍ
  اعتباطيّ) — **ولا يُخترع بعد الرقم**.
- **المقاييس على PRIMARY القابلة للمقارنة** (فيصل ∈ READY/WAIT/REJECT بدليل DIRECT/STRONG): دقّةُ واستدعاءُ READY · WAIT · REJECT (`UNDEFINED` عند
  مقامٍ صفر) · `FALSE_READY_RATE` = FALSE_READY ÷ N (تعريفُ V41 §⑧) ومعه FALSE_READY ÷ (فيصل غيرُ READY) · ويلسون 95% حين المقامُ 10 فأكثر ·
  **ولا دقّةٌ إجماليّة تُطبع بلا سطر READY بجوارها**.
- **UNKNOWN منفصل:** `V4_UNKNOWN` و`FAISAL_UNKNOWN` عدّادان · **UNKNOWN ليس MATCH ولا WAIT أبدًا**.
- **`V4_BEATS_BASELINE`:** b = حالاتٌ طابق فيها V4 وأخطأ الأساس · c = العكس ⟵ N = 0 ⟵ `UNKNOWN` · b = 0 ⟵ `NO` · b+c أقلّ من 10 ⟵ `UNKNOWN` ·
  وإلّا `YES` إن كان حدُّ ويلسون الأدنى لـb÷(b+c) فوق 0.5 وإلّا `NO` (فاصلٌ لا قيمة p — §⑧ V41).
- **`READY_CLASS_VALIDATED`:** `NO (STRUCTURAL)` ما دام فضاءُ المخرَج لا يحوي READY (فحصُ FVO1 حيًّا) · وإلّا `YES` بشرط: READY عند فيصل 43 فأكثر
  (V41 §⑨) **و**READY عند V4 10 فأكثر **و**حدّا ويلسون الأدنى للاستدعاء والدقّة 0.5 فأكثر · `NO` إن كان READY عند فيصل 10 فأكثر وحدُّ ويلسون
  الأعلى للاستدعاء دون 0.5 · وإلّا `UNKNOWN`.

## ⑮ المكوّنات — PHASE 16
- **ENTRY** (`type1_bids` ‏+ `type2_liberation`) · **STOP** (`invalidation` بقاعدة R4-STOP-01) · **INVALIDATION** (`invalidation` كلُّها ‏+ القاع) ·
  **TARGET** (الأهدافُ بعائلاتها) — مقابل أسعار فيصل لكلّ مكوّن:
  `MATCH` إن وقع أيُّ سعرٍ لفيصل داخل ±2% (`LEVEL_TOL_PCT` المجمَّد · «دقة الخطأ لاتتجاوز 2٪») من أيّ سعرٍ لـV4 في المكوّن — **و`type1_bids`
  منطقةٌ لا طرفان:** سعرُ دخولٍ لفيصل داخل [أدناها × 0.98 · أعلاها × 1.02] تطابق · `MISMATCH` ·
  `FAISAL_NOT_STATED` · `FAISAL_NONE` (نفيٌ صريح: «لا دخول») · `V4_NOT_AVAILABLE` · `SCALE_MISMATCH` (سعرُ فيصل الظاهر يبعد عن إغلاق V4 أكثرَ من
  15% — `PX_TOL` في `v4_eval`).
- **عدمُ تطابق مكوّنٍ ليس عدمَ تطابق قرار** — يُطبعان منفصلين.

## ⑯ النظرُ المستقبليّ — PHASE 17 (لكلّ حالة)
- **LA1 الشموعُ المستقبليّة:** كلُّ تاريخٍ في اللقطة قبل تاريخ القرار ∧ `asof` المحرّك قبله ∧ لا `F7`.
- **LA2 المُدخَلُ الأعمى:** مفاتيحُ السياق الأربعة وحدَها · وكلُّ مصدرٍ آليّ (`ctb_log:` · `live:` · `UNAVAILABLE`) · والقروبات/الطرح/المضارب `None`.
- **LA3 الترتيب:** حالة ⟵ V4 ⟵ فيصل في السلسلة · و`after_v4_seq` = قيدُ V4.
- **LA4 لا صورةَ ولا تعليقَ لـV4:** `run_case` لا يقرأ من الحالة إلّا الرمزَ والتاريخ (AST · FV48) ⟵ التعليقاتُ والأهدافُ وتعديلاتُ الشارت وتعليقاتُ
  فيصل لا تصل بالبناء.
- **LA5 إجراءاتُ الشركات:** ثباتُ `state` و`tech_state` حين تُضرب أسعارُ اللقطة ×10 و×0.1 (والحجمُ بعكسها) ⟵ تسويةُ تقسيمٍ لاحقٍ لا تغيّر القرار ·
  وإن تغيّر: تقسيمٌ مسجَّلٌ بين تاريخ القرار والتشغيل أو تقسيماتٌ مجهولة ⟵ **INVALIDATE**.
- **LA6 قيمُ المؤشّرات:** إعادةُ الحساب من اللقطة المحفوظة = بصمةُ القرار (FV50) ⟵ لا مؤشّرَ من خارج اللقطة.
- **فشلُ LA5 ⟵ إبطالُ الحالة وحدَها** (حدثٌ خارجيّ) · **وفشلُ LA1-LA4/LA6 ⟵ إبطالُها و`LOOKAHEAD = FAIL` ⟵ `VALIDATION_BLOCKED`** (يدلّ على عيبٍ في الخطّ).

## ⑰ السلامةُ لكلّ دفعة — PHASE 18
I1-I12 (§②) قبل كلّ تشغيلٍ لـV4 وكلّ ختمٍ وكلّ تقرير · و`NO_RULE_MUTATIONS` = I3-I4 ‏+ ملفُّ القواعد المجمَّد (I1) · `NO_LOOKAHEAD` = I12 ·
`NO_PROVENANCE_CORRUPTION` = I8-I10 · **وأيُّ تغيّرٍ ⟵ STOP**.

## ⑱ أشرطةُ العيّنة والحالةُ النهائيّة — PHASE 19-20 · FINAL STATES
- **`CURRENT_STATUS`** (من PRIMARY): أقلّ من 10 ⟵ `VERY_PRELIMINARY` · 10-24 ⟵ `PRELIMINARY` · 25-42 ⟵ `MEANINGFUL` (BUT INCOMPLETE) ·
  43 فأكثر ⟵ `MINIMUM_TARGET_REACHED` (**لا نجاحَ تلقائيّ**).
- **`FINAL_VALIDATION_STATE` بالترتيب:**
  1. **VALIDATION_BLOCKED** ⟵ أيُّ فشلٍ في I1-I12 · أو `LOOKAHEAD = FAIL` · أو `PROVENANCE = FAIL` · أو `COLLECTOR = FAIL`.
  2. **INSUFFICIENT_SAMPLE** ⟵ PRIMARY أقلّ من 43 · **أو** READY عند فيصل في PRIMARY أقلّ من **5** (🧩 تغطيةُ الصنف · `engineering`).
  3. **VALIDATED** ⟵ كلُّ ما يلي: READY · WAIT · REJECT عند فيصل 5 فأكثر لكلٍّ · صفرُ تلوّثٍ وتسرّب · `V4_BEATS_BASELINE = YES` ·
     `READY_CLASS_VALIDATED = YES` · لا فشلَ منهجيّ غيرُ مفسَّر (لا FALSE_READY سببُه UNKNOWN/IMPLEMENTATION_BUG/DATA_BUG · ولا صنفُ عدمِ تطابقٍ
     بخمس حالاتٍ فأكثر سببُه الغالب UNKNOWN) · المنهجُ لم يتغيّر.
  4. **PARTIALLY_VALIDATED** ⟵ FALSE_READY = 0 **و** (P1: READY عند فيصل 5 فأكثر وWAIT∪REJECT 5 فأكثر وحدُّ نيوكومب الأدنى 95% لفرق «TECH_READY
     عند V4» بين READY فيصل وWAIT∪REJECT فيصل فوق الصفر — الطبقةُ الفنيّة تحمل إشارةَ READY فيصل · **أو** P2: `V4_BEATS_BASELINE = YES`).
  5. **NOT_VALIDATED** ⟵ ما سوى ذلك.
- **`FINAL_PROSPECTIVE_VALIDATION_REPORT.md`** يُولَّد عند PRIMARY 43 فأكثر **وحدَه** بمحتوياته: الإجماليّ · المستبعدُ وأسبابه · التطابقُ وعدمُه ·
  كلُّ `FALSE_*` · الدقّةُ والاستدعاءُ لكلّ صنف · V4_UNKNOWN · FAISAL_UNKNOWN · خطُّ ALWAYS_WAIT وV4 مقابله · المكوّنات · عدمُ التطابق المتكرّر ·
  أدلّةُ المعلومة الخارجيّة · أدلّةُ فجوة المنهج.

## ⑲ كتلةُ الإخراج (FINAL OUTPUT) — بنصّها في كلّ تشغيل
`V4_FROZEN` · `V4_COMMIT` · `CORPUS_AUDIT` · `VALID_PROSPECTIVE_CASES` · `EXCLUDED_CASES` · `MATCHES` · `MISMATCHES` · `FALSE_READY` · `FALSE_WAIT` ·
`FALSE_REJECT` · `FALSE_UNKNOWN` · `V4_UNKNOWN` · `FAISAL_UNKNOWN` · `ALWAYS_WAIT_MATCH` · `V4_BEATS_BASELINE` · `READY_CLASS_VALIDATED` ·
`METHODOLOGY_CHANGED` · `LOOKAHEAD` · `PROVENANCE` · `CURRENT_STATUS` · `FINAL_VALIDATION_STATE` — **بترتيب المالك** ‏+ أسطرٌ مكمّلة تحتها
(SECONDARY · COLLECTOR · INTEGRITY · الاستبعادُ بالصنف).
- `CORPUS_AUDIT = COMPLETE` يُشتقّ من جرد EX (ملفّاتٌ غيرُ محلّلة 0 · OCR وحدَه 0 · عينٌ معلّقة 0 · عاليةُ المعلومة كلُّها كاملة) وإلّا `INCOMPLETE`.
- `METHODOLOGY_CHANGED = NO` ⟺ I1-I7 ناجحة · و`EXCLUDED_CASES` = كلُّ مرشَّحٍ لم يدخل PRIMARY (بأسبابه: الصنف · المصدريّة · الجودة · الإبطال).
- `VALID_PROSPECTIVE_CASES` = حالاتُ PRIMARY **المكتملة** (قرارُ V4 ‏+ كلمةُ فيصل) بلا إبطال (جدارُ الجودة · النظرُ المستقبليّ) = MATCHES ‏+ MISMATCHES ‏+
  FAISAL_UNKNOWN ‏+ UNRESOLVED · والمختومةُ التي تنتظر V4 أو فيصل تُطبع `PENDING` ولا تُعَدّ.

## ⑳ التنبّؤات (قبل الرقم · تُنشر إن خابت)
- **P1 أوّلُ تشغيلٍ للأداة:** `V4_FROZEN = YES` · `VALID_PROSPECTIVE_CASES = 0` · SECONDARY 1 (CASE_0001 · MATCH) · `CURRENT_STATUS = VERY_PRELIMINARY` ·
  `FINAL_VALIDATION_STATE = INSUFFICIENT_SAMPLE` · `V4_BEATS_BASELINE = UNKNOWN` · `READY_CLASS_VALIDATED = NO` · `LOOKAHEAD = PASS` ·
  `PROVENANCE = PASS` · `COLLECTOR = LIVE_PENDING`.
- **P2 B48 بالأصناف السبعة:** NEW_PROSPECTIVE 1 · INSUFFICIENT_CONTEXT 14 · UNKNOWN 13 · DERIVATIVE 9 · PRE_EXISTING 7 · CONTAMINATED 2 · DUPLICATE 2
  (= 48) — **وBRTX يعبر C5 وC8**.
- **P3 CASE_0001:** LA1-LA6 كلُّها PASS (ومنها ثباتُ القرار تحت ×10/×0.1) · ومكوّناتُه الأربعة FAISAL_NOT_STATED أو FAISAL_NONE.
- **P4 الحقبة 1 كلُّها:** FALSE_READY 0 · FALSE_REJECT 0 · `V4_BEATS_BASELINE` لا يكون YES · `READY_CLASS_VALIDATED = NO` ·
  `FINAL_VALIDATION_STATE` لا يكون `VALIDATED` (أقصاه `PARTIALLY_VALIDATED`).
- **P5 نسبةُ PRIMARY من NEW_PROSPECTIVE مجهولة:** تعتمد على أن يُعيد المالكُ **توجيهَ** منشورات فيصل من قناته (التوجيهُ يحمل الطابع ⟵ HIGH)
  بدل لقطات الشاشة — **توصيةٌ عمليّةٌ للمالك لا قاعدة**.

## ㉑ ممنوعات — ABSOLUTE FINAL RULE · والأقفال
- **لا** تحسين · **لا** تعلّم · **لا** رقعة · **لا** انتقاء · **لا** تعديلَ لـV4 بسبب نتيجةٍ أماميّة · **لا** نجاحَ من حالةٍ واحدة · **لا** نجاحَ من دقّةٍ
  إجماليّةٍ عالية إن ندر READY · **لا** يُعَدّ UNKNOWN تطابقًا · **لا** دليلَ من المدوّنة القديمة يُستعمل أماميًّا · **لا** يُستعمل الرمزُ الذي حدّده
  المالك (HUBC) سببًا لتعديل المنهج · **لا** خطَّ أساسٍ يُخترع بعد الرقم · **لا** إعادةَ تشغيلٍ بعد عدمِ تطابق.
- **الحلقة:** `FREEZE V4 ⟶ CAPTURE NEW CASE ⟶ RUN V4 BLIND ⟶ SEAL RESULT ⟶ REVEAL FAISAL ⟶ COMPARE ⟶ RECORD ⟶ REPEAT`.
- **الأقفالُ المزمعة (`FPA*`) — كلٌّ تُسقطه طفرة:** بصمةُ الحقبة مثبَّتة · المعرّفاتُ الخمسة حيّةً = الحقبة · الإغلاقُ يتجاهل التعليقَ والـdocstring ويلتقط
  تعديلَ أيّ مكوّن ولا يلتقط دالّةً خارجه · السلامةُ تمسك كلَّ عطب (I1-I12) بشاهد ضبط · المشغّلُ يرفض عند الانكسار · الأصنافُ السبعة وأسبقيّتُها ·
  الفحوصُ الثمانية بشواهد · المصدريّةُ والثقةُ والأساسيّ/الثانويّ · كائنُ V4 لا يحوّل UNKNOWN · `evidence_quote` حرفيّ · أصنافُ المطابقة كلُّها ·
  المكوّناتُ بالتسامح · LA1-LA6 بشواهد · الحالةُ النهائيّة بقواعدها · كتلةُ الإخراج بترتيبها · إعادةُ التوليد بايتًا بايتًا · الجامعُ (meta_v 2 ·
  forward_type · البصمةُ الإدراكيّة · صفُّ الفجوة) سلوكيًّا · والـworkflows (الجدولة · كتلةُ الحالة · FVW1 قائم).
