# PROSPECTIVE_BATCH_48_CONTAMINATION — فحصُ التلوّث (B48_20261007)

> مولَّدٌ من `faisal_method_v41/batch_intake.py` (لا رقمَ باليد) · V4 مجمَّد · الصورُ **تقيس V4 ولا تدرّبه**.

## ① القاعدة (مكتوبةٌ في الكود قبل أيّ نتيجة · `batch_intake.classify`)
- **DUPLICATE** = البايتاتُ نفسُها (SHA-256) لصورةٍ في المدوّنة (722 صورة · 609 وحدة) أو أسبقَ في الدفعة · أو `file_id` سبق تنزيلُه (الجامع «seen»).
- **DERIVATIVE** = بصمةٌ إدراكيّةٌ قريبة (dHash256 ≤ 24 **و** pHash64 ≤ 10 — قاعدةُ V3 `corpus_build.dedup` و`ledger.near_duplicates` · و«أو» القديمة كانت ستَسِم 17 صورةً — BB4) · أو نصُّ OCR بجاكارد ≥ 0.85 على 15 كلمةً فأكثر · أو مراجعةٌ بصريّةٌ تقول مقصوصٌ/معلَّم.
- **CONTAMINATED** = الحالةُ نفسُها (الرمزُ وتاريخُ القرار ±3 أيّام) في حالات V4 (157) أو الذهبيّة · أو مثالٌ رآه V3/V4 · أو تاريخُ القرار (أو حدُّه الأعلى الظاهر) قبل نافذة الأهليّة **2026-10-03** (مادّةٌ تاريخيّة).
- **UNKNOWN** = غيرُ مقروء · أو لم يُراجَع بصريًّا · أو الكاتبُ لا يُثبَت (صورةٌ بلا رأس منشورٍ ولا اسم — ولا يُفترض أنه فيصل) · أو تاريخُ القرار لا يُثبَت (لا مصدرَ توجيهٍ ولا طابعٌ ظاهر).
- **CLEAN_PROSPECTIVE** = ما سوى ذلك — **وحدَه يدخل النتيجةَ الأساسيّة**.

## ② الأعداد
- **TOTAL_RECEIVED 48** (صورٌ وصلت البوت في تشغيلات الجامع `37616553357`) · ما قاله المالك 48 ⟵ **يطابق** · رسائلُ بلا صورة 0.
- **CLEAN_PROSPECTIVE 2** · **CONTAMINATED 9** · **DUPLICATE 2** · **DERIVATIVE 9** · **UNKNOWN 26**
- **VALIDATION CASES 1** (نظيفٌ ‏+ فيصل ‏+ رمزٌ واحد ‏+ عبارةُ قرار — `V41_prereg §⑥`).

## ③ لكلّ صورة
| الصورة | الرسالة | أُرسلت | المصدر | الأبعاد | التكرار | الاشتقاق | أقربُ صورةٍ في المدوّنة (dHash/pHash) | الفئة | السبب | حالة؟ |
|---|---|---|---|---|---|---|---|---|---|---|
| `TG_58382` | 58382 | 2026-10-07T10:16:32Z | telegram_bot | 590×1280 | NONE | NONE | `TG_50600` 81/14 | **UNKNOWN** | DATE_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58383` | 58383 | 2026-10-07T10:16:32Z | telegram_bot | 590×1280 | NONE | NONE | `IMG_0149` 62/20 | **UNKNOWN** | AUTHOR_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58384` | 58384 | 2026-10-07T10:16:32Z | telegram_bot | 590×1280 | NONE | NONE | `TG_2012` 44/18 | **UNKNOWN** | AUTHOR_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58385` | 58385 | 2026-10-07T10:16:32Z | telegram_bot | 590×1280 | NONE | NONE | `TG_1885` 45/10 | **UNKNOWN** | AUTHOR_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58386` | 58386 | 2026-10-07T10:16:32Z | telegram_bot | 590×1280 | NONE | NONE | `TG_2033` 47/6 | **UNKNOWN** | AUTHOR_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58387` | 58387 | 2026-10-07T10:16:32Z | telegram_bot | 994×1280 | NONE | NONE | `IMG_0414` 73/26 | **CONTAMINATED** | HISTORICAL_BEFORE_WINDOW:2026-09-28 | BEFORE_WINDOW |
| `TG_58388` | 58388 | 2026-10-07T10:16:32Z | telegram_bot | 590×1280 | NONE | NEAR:TG_58385 | `TG_1885` 46/6 | **DERIVATIVE** | NEAR:TG_58385 | DUPLICATE_OF:TG_58385 |
| `TG_58389` | 58389 | 2026-10-07T10:16:32Z | telegram_bot | 590×1280 | NONE | NONE | `IMG_0690` 84/20 | **UNKNOWN** | DATE_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58390` | 58390 | 2026-10-07T10:16:32Z | telegram_bot | 798×1280 | NONE | NONE | `TG_2177` 56/36 | **UNKNOWN** | DATE_NOT_ESTABLISHED | DATE_IMPRECISE |
| `TG_58391` | 58391 | 2026-10-07T10:16:32Z | telegram_bot | 590×1280 | NONE | NONE | `TG_1868` 80/28 | **UNKNOWN** | DATE_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58392` | 58392 | 2026-10-07T10:16:38Z | telegram_bot | 590×1280 | NONE | NONE | `TG_50576` 72/24 | **UNKNOWN** | DATE_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58393` | 58393 | 2026-10-07T10:16:38Z | telegram_bot | 590×1280 | NONE | NONE | `X_20260918_66_ELPW` 83/20 | **UNKNOWN** | DATE_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58394` | 58394 | 2026-10-07T10:16:38Z | telegram_bot | 590×1280 | NONE | NONE | `TG_20260918_67_BRNX` 71/34 | **UNKNOWN** | DATE_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58395` | 58395 | 2026-10-07T10:16:38Z | telegram_bot | 1050×1280 | NONE | NONE | `TG_20260905_06` 25/14 | **UNKNOWN** | AUTHOR_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58396` | 58396 | 2026-10-07T10:16:38Z | telegram_bot | 1081×1280 | NONE | NONE | `TG_20260905_06` 33/26 | **UNKNOWN** | DATE_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58397` | 58397 | 2026-10-07T10:16:38Z | telegram_bot | 1196×1280 | NONE | NONE | `TG_20260905_06` 28/24 | **DERIVATIVE** | VISUAL:TG_58396 | DUPLICATE_OF:TG_58396 |
| `TG_58398` | 58398 | 2026-10-07T10:16:38Z | telegram_bot | 590×1280 | NONE | NONE | `TG_50578` 78/24 | **UNKNOWN** | AUTHOR_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58399` | 58399 | 2026-10-07T10:16:38Z | telegram_bot | 590×1280 | NONE | NONE | `TG_2121` 79/30 | **UNKNOWN** | AUTHOR_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58400` | 58400 | 2026-10-07T10:16:38Z | telegram_bot | 584×1266 | NONE | NONE | `TG_2192` 46/10 | **UNKNOWN** | AUTHOR_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58401` | 58401 | 2026-10-07T10:16:38Z | telegram_bot | 650×800 | NONE | NONE | `TG_1942` 93/30 | **UNKNOWN** | DATE_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58402` | 58402 | 2026-10-07T10:16:44Z | telegram_bot | 590×1280 | NONE | NONE | `IMG_0602` 75/24 | **CLEAN_PROSPECTIVE** | — | ✅ |
| `TG_58403` | 58403 | 2026-10-07T10:16:44Z | telegram_bot | 642×800 | NONE | NONE | `APP_20260918_19_NTCL` 86/32 | **UNKNOWN** | DATE_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58404` | 58404 | 2026-10-07T10:16:44Z | telegram_bot | 369×800 | NONE | NONE | `CH_20260918_60_VEEE` 50/20 | **UNKNOWN** | AUTHOR_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58405` | 58405 | 2026-10-07T10:16:44Z | telegram_bot | 590×1280 | NONE | NONE | `X_20260827_target10_entry_below` 90/26 | **DERIVATIVE** | VISUAL:TG_58402 | DUPLICATE_OF:TG_58402 |
| `TG_58406` | 58406 | 2026-10-07T10:16:44Z | telegram_bot | 804×1280 | NONE | NONE | `TG_57878` 39/4 | **DERIVATIVE** | VISUAL:TG_58402 | DUPLICATE_OF:TG_58402 |
| `TG_58407` | 58407 | 2026-10-07T10:16:44Z | telegram_bot | 590×1280 | NONE | NONE | `TG_2024` 59/18 | **DERIVATIVE** | VISUAL:TG_58402 | DUPLICATE_OF:TG_58402 |
| `TG_58408` | 58408 | 2026-10-07T10:16:44Z | telegram_bot | 590×1280 | NONE | NONE | `TG_50585` 74/22 | **CLEAN_PROSPECTIVE** | — | NO_TICKER |
| `TG_58409` | 58409 | 2026-10-07T10:16:44Z | telegram_bot | 590×1280 | NONE | NONE | `IMG_0697` 37/6 | **CONTAMINATED** | HISTORICAL_BEFORE_WINDOW:2026-10-02 | BEFORE_WINDOW |
| `TG_58410` | 58410 | 2026-10-07T10:16:44Z | telegram_bot | 590×1280 | NONE | NONE | `TG_2192` 46/14 | **UNKNOWN** | AUTHOR_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58411` | 58411 | 2026-10-07T10:16:44Z | telegram_bot | 1280×895 | NONE | NONE | `TG_2087` 84/30 | **UNKNOWN** | AUTHOR_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58412` | 58412 | 2026-10-07T10:16:50Z | telegram_bot | 588×1280 | NONE | NONE | `TG_20260905_05` 69/30 | **UNKNOWN** | AUTHOR_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58413` | 58413 | 2026-10-07T10:16:50Z | telegram_bot | 590×1280 | NONE | NONE | `IMG_0602` 99/26 | **UNKNOWN** | DATE_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58414` | 58414 | 2026-10-07T10:16:50Z | telegram_bot | 590×1280 | NONE | NONE | `X_20260918_24_SXTC` 68/22 | **UNKNOWN** | AUTHOR_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58415` | 58415 | 2026-10-07T10:16:50Z | telegram_bot | 1006×1280 | NONE | NONE | `TG_20260918_42_NUWE` 85/32 | **CONTAMINATED** | HISTORICAL_BEFORE_WINDOW:≤2026-10-02 | BEFORE_WINDOW |
| `TG_58416` | 58416 | 2026-10-07T10:16:50Z | telegram_bot | 590×1280 | NONE | NONE | `TG_1894` 71/10 | **CONTAMINATED** | HISTORICAL_BEFORE_WINDOW:2026-10-02 | BEFORE_WINDOW |
| `TG_58417` | 58417 | 2026-10-07T10:16:50Z | telegram_bot | 590×1280 | NONE | NONE | `TG_2093` 72/20 | **CONTAMINATED** | SAME_CASE:V4:SXTC_2026-09-1x_a | DUPLICATE_OF:V4:SXTC_2026-09-1x_a |
| `TG_58418` | 58418 | 2026-10-07T10:16:50Z | telegram_bot | 680×1280 | NONE | NONE | `TG_2179` 87/16 | **DERIVATIVE** | VISUAL:WA_20260918_31_SXTC | DUPLICATE_OF:WA_20260918_31_SXTC |
| `TG_58419` | 58419 | 2026-10-07T10:16:50Z | telegram_bot | 590×1280 | NONE | NONE | `TG_50588` 58/26 | **UNKNOWN** | DATE_NOT_ESTABLISHED | DATE_IMPRECISE |
| `TG_58420` | 58420 | 2026-10-07T10:16:50Z | telegram_bot | 590×1280 | NONE | NONE | `X_20260827_rubi_daily_ma_rsi` 91/28 | **UNKNOWN** | DATE_NOT_ESTABLISHED | NOT_FAISAL |
| `TG_58421` | 58421 | 2026-10-07T10:16:50Z | telegram_bot | 590×1280 | NONE | NONE | `IMG_9925` 59/32 | **CONTAMINATED** | HISTORICAL_BEFORE_WINDOW:2026-09-30 | BEFORE_WINDOW |
| `TG_58422` | 58422 | 2026-10-07T10:16:57Z | telegram_bot | 590×1280 | NONE | NONE | `TG_1918` 71/6 | **CONTAMINATED** | HISTORICAL_BEFORE_WINDOW:2026-10-02 | BEFORE_WINDOW |
| `TG_58423` | 58423 | 2026-10-07T10:16:57Z | telegram_bot | 590×1280 | NONE | NONE | `X_20260918_23_watchlist` 51/4 | **CONTAMINATED** | HISTORICAL_BEFORE_WINDOW:2026-10-02 | BEFORE_WINDOW |
| `MSG_58424` | 58424 | 2026-10-07T10:16:57Z | telegram_bot | 590×1280 | EXACT:TG_58052 | NONE | — | **DUPLICATE** | EXACT:TG_58052 | DUPLICATE_OF:TG_58052 |
| `MSG_58425` | 58425 | 2026-10-07T10:16:57Z | telegram_bot | 800×372 | EXACT:TG_58051 | NONE | — | **DUPLICATE** | EXACT:TG_58051 | DUPLICATE_OF:TG_58051 |
| `TG_58426` | 58426 | 2026-10-07T10:16:57Z | telegram_bot | 590×1280 | NONE | NEAR:CH_20260918_14_NUWE | `CH_20260918_14_NUWE` 11/4 | **DERIVATIVE** | NEAR:CH_20260918_14_NUWE | DUPLICATE_OF:CH_20260918_14_NUWE |
| `TG_58427` | 58427 | 2026-10-07T10:16:57Z | telegram_bot | 1246×1280 | NONE | NONE | `EDU_20260827_wnw_precall_chinese` 91/26 | **DERIVATIVE** | VISUAL:X_20260918_13_NUWE | DUPLICATE_OF:X_20260918_13_NUWE |
| `TG_58428` | 58428 | 2026-10-07T10:16:57Z | telegram_bot | 590×1280 | NONE | NEAR:TG_58052 | `TG_58052` 0/0 | **DERIVATIVE** | NEAR:TG_58052 | DUPLICATE_OF:TG_58052 |
| `TG_58429` | 58429 | 2026-10-07T10:16:57Z | telegram_bot | 590×1280 | NONE | NONE | `IMG_8126` 51/2 | **CONTAMINATED** | SAME_CASE:GOLDEN:DXST,V4:DXST_2026-06-16 | DUPLICATE_OF:GOLDEN:DXST |

## ④ ما لم يُفحص آليًّا (حدودٌ معلنة)
- القصُّ الشديد (مقطعٌ صغيرٌ من شارتٍ أكبر) قد يفلت من البصمة الإدراكيّة ⟵ تغطّيه المقارنةُ بالحالة (الرمز ‏+ التاريخ) والمراجعةُ البصريّة.
- «نفسُ الحالة» تُقرأ من الرمز وتاريخ القرار في `input_annotations.json` — وما لا رمزَ له يبقى UNKNOWN لا CLEAN.
