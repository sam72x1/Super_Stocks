# V4_HOLDOUT_INTEGRITY — الاحتجاز وسلامتُه (§4-6)

> مولَّدٌ من `faisal_method_v41/docs_v41.py` — كلُّ رقمٍ من JSON (لا رقمَ باليد · FVD1) · العقدُ `V41_prereg.md` مدموجٌ قبل أيّ رقم (#550) · V4 مجمَّد: `FREEZE_ID 5f291a3b301be047…` · commit التجميد الرسميّ `7c8826c`.

## ① الحكم
**TRUE HOLDOUT: INSUFFICIENT SAMPLE — 0 حالةً نظيفة** من 157 (POST-HOC · التشغيلةُ الأولى قالت 2 بعيبٍ مُثبَت — §⑤ أدناه).
السبب **قاعدةُ العقد لا الصدفة**: كلُّ وحدةٍ تاريخيّة قُرئت في مرور V4 البصريّ قبل كتابة القواعد ⟵ `EXPOSED` ⟵ ملوَّثة (§4: «إن شككتَ فاكتشاف») ·
**ولا يُصنَع احتجازٌ بإرخاء العَلَم** ⟵ **الطريقُ الوحيد إلى احتجازٍ نظيف أماميّ** (`V4_PROSPECTIVE_PROTOCOL.md`).

## ② البيانُ المختوم
- **البصمة (الختم):** `601b800da2caf76ee580494ff0e43f040965a1b6efebf915175c99574e5c6ce8` — والكشفُ يتحقّق منها ويرفض بيانًا تغيّر بعد ختمه (FV42 · FV44).
- **المُدخَلات:** cases_v4 `422a28f2fe28e3a2…` · المدوّنة `8bde6fe4766ad55a…` · المرورُ البصريّ
  `d431061c6a841b5b…` · وحداتٌ مستشهَدٌ بها 81 · وحداتٌ مكشوفة 609.
- **الأعلام:** EXPOSED 157 · CITED 57 · EXCLUDED 40 · GOLDEN 20 · EDU 16 · THIRD_PARTY 14 · DISCOVERY 12 · SHARED_UNIT 2.
- **الطبقات:** T1_CITED 57 · OTHER_CONTAMINATED 56 · T2_EXPOSED_UNCITED 44 · CLEAN 0 — T1 = `CITED` · T2 = مكشوفةٌ بلا علمٍ آخر (طبقتان **وصفيّتان** لا احتجاز).

## ③ العمى عن الكلمة (§6)
البنّاءُ يرى `case · sids · third_party_sids · tickers · dates · statement_date · date_precision · set · split · golden · tiers · best_tier` وحدَها · **ولا يقرأ** `label · label4 · plan_F · levels_F · targets_F · dec` (قفل FV42 بالـAST) ·
ثمّ يُختم البيانُ ⟵ وبعدها فقط `reveal` تضمّ كلمةَ فيصل وتحمل بصمةَ البيان. ⚠️ **حدّ:** العمى بنيويٌّ في الكود لا معرفيّ — المنفّذُ قرأ الوحداتِ كلَّها في V4 ·
والمسطرةُ آليّةٌ مسجَّلةٌ قبل الرقم فلا يملك توجيهَها.

## ④ «احتجازُ V4» ليس احتجازًا هنا
من 10 حالاتِ احتجاز V4 **9 مستشهَدٌ بعباراتها في سجلّ القواعد نفسِه** (Q2 · صدق) — أي أنّ قواعدَ V4 كُتبت
وهي ترى «احتجازَه» ⟵ رقمُ V4 على احتجازه (‏H-STATE 8/9) **وصفٌ ملوَّث** لا تحقّق.

| الحالة | الرمز | الطبقة | الأعلام |
|---|---|---|---|
| `STKH_2026-09-04` | STKH | T1_CITED | CITED · EXPOSED |
| `EDBL_2026-09-22` | EDBL | T1_CITED | CITED · EXPOSED |
| `LIMN_2026-09-22` | LIMN | T1_CITED | CITED · EXPOSED |
| `IPDN_2026-09-2x` | IPDN | T2_EXPOSED_UNCITED | EXPOSED |
| `NRSN_2026-09-27` | NRSN | T1_CITED | CITED · EXPOSED |
| `OMH_2026-09-26` | OMH | T1_CITED | CITED · EXPOSED |
| `CIIT_2026-09-26` | CIIT | T1_CITED | CITED · EXPOSED |
| `PPBT_2026-09-04` | PPBT | T1_CITED | CITED · EXPOSED |
| `YMT_2026-09-04` | YMT | T1_CITED | CITED · EXPOSED |
| `SLXN_2026-08-06` | SLXN | T1_CITED | CITED · EXPOSED |

## ⑤ إفصاحُ POST-HOC (العقد §⑲ — التشغيلةُ الأولى تُنشر ولا تُدهَس)
- **التشغيلةُ الأولى:** مؤهَّلة 2 · CITED 53 · SHARED_UNIT 0 · EXPOSED 146 ·
  الطبقات OTHER_CONTAMINATED 59 · T1_CITED 53 · T2_EXPOSED_UNCITED 43 · CLEAN 2 · ختمُها `8f98d47b0d234be8…`.
- **العيب (BB2):** معرّفُ العبارة «#k» لم يُطبَّع إلى وحدة صورته ⟵ لا يطابق المرورَ البصريّ ولا الاستشهاد (العددُ في analysis_v41.json · posthoc_disclosure) · **الإصلاح:** `holdout.base_id` · **القفل:** FV43 (حالة panel) ‏+ M43e.
- **الإعادة (POST-HOC):** مؤهَّلة 0 · CITED 57 · SHARED_UNIT
  2 · EXPOSED 157 · ختمُها `601b800da2caf76e…`.
- **الأثرُ على الخلاصات:** T1 22/35 ⟵ 23/36 ·
  T2 24/42 ⟵ 24/43 ·
  المعلومةُ الخفيّة SUPPORTED (6/11) في الاثنتين ⟵ **لا خلاصةَ انقلبت** ·
  والذي تغيّر: «النظيفة» في الأولى (`FTFT_2026-07-2x` · `ELPW_2026-01`) صارت مكشوفة ⟵ Q1 صدق **بعد الإصلاح وحدَه**.

| الحالة | الطبقة (الأولى) | الطبقة (POST-HOC) | الأعلام (الأولى) | الأعلام (POST-HOC) |
|---|---|---|---|---|
| `INLF_2026-07-19` | OTHER_CONTAMINATED | OTHER_CONTAMINATED | THIRD_PARTY · EXCLUDED | THIRD_PARTY · EXCLUDED · EXPOSED |
| `HODO_2026-07-19` | OTHER_CONTAMINATED | OTHER_CONTAMINATED | THIRD_PARTY · EXCLUDED | THIRD_PARTY · EXCLUDED · EXPOSED |
| `XAIR_2026-07-19` | OTHER_CONTAMINATED | OTHER_CONTAMINATED | THIRD_PARTY · EXCLUDED | THIRD_PARTY · EXCLUDED · EXPOSED |
| `WLDS_2026-07-19` | OTHER_CONTAMINATED | OTHER_CONTAMINATED | THIRD_PARTY · EXCLUDED | THIRD_PARTY · EXCLUDED · EXPOSED |
| `RBNE_2026-07-19` | OTHER_CONTAMINATED | OTHER_CONTAMINATED | THIRD_PARTY · EXCLUDED | THIRD_PARTY · EXCLUDED · EXPOSED |
| `ELPW_2026-05-0x` | T2_EXPOSED_UNCITED | T1_CITED | EXPOSED | CITED · EXPOSED |
| `CDIO_2026-01-28/02` | OTHER_CONTAMINATED | T1_CITED | EXCLUDED | CITED · EXCLUDED · EXPOSED |
| `UNK_TG_2099` | OTHER_CONTAMINATED | OTHER_CONTAMINATED | EXCLUDED | EXCLUDED · EXPOSED |
| `FTFT_2026-07-2x` | CLEAN | T2_EXPOSED_UNCITED | — | EXPOSED |
| `DCOY_2026-09-22` | T1_CITED | T1_CITED | CITED · EXPOSED | CITED · EXPOSED |
| `AMIX_2026-08-24` | OTHER_CONTAMINATED | T1_CITED | GOLDEN | CITED · GOLDEN · SHARED_UNIT · EXPOSED |
| `HCWB_2026-08-24` | OTHER_CONTAMINATED | T1_CITED | GOLDEN | CITED · GOLDEN · SHARED_UNIT · EXPOSED |
| `ELPW_2026-09-1x` | T2_EXPOSED_UNCITED | T2_EXPOSED_UNCITED | EXPOSED | EXPOSED |
| `ELPW_2026-01` | CLEAN | T2_EXPOSED_UNCITED | — | EXPOSED |

## ⑥ اختباراتُ التسرّب (FV42 · FV43 · FV44)
- **FV42:** الأعلامُ السبعة كلٌّ على حالته · النظيفةُ وحدَها مؤهَّلة · العمى بالـAST · والكشفُ يرفض بيانًا عُبث به.
- **FV43:** عضوُ العنقود يرث الاستشهاد · ومعرّفُ العبارة «#k» يرث وحدةَ صورته · والوحدةُ المشتركة مع الاكتشاف تُلوِّث · والنسخةُ المطابقة والمصغّرة
  تُكشف بالبصمة الإدراكيّة (dHash ≤ 24 · pHash ≤ 10 من V3) والضجيجُ لا · والختمُ يرفض حالةً لها نسخةٌ في المدوّنة.
- **الطفرات:** 53/53 لأقفال FV42-FV50 وFVT1 وFVO1 وFVD1 سقطت كلٌّ بقفلها (صفرُ انهيار).
