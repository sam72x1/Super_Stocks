# 🧊 V4 FREEZE REPORT — المرشَّحُ المجمَّد للتحقّق الأماميّ

> مولَّدٌ من `faisal_method_v41/freeze.py` (V4.1-FREEZE 1.0 (2026-10-07)) · **لا يُحرَّر باليد** · والعقد `faisal_method_v41/V41_prereg.md` §②.

## ① الهويّة

- **freeze_id:** `5f291a3b301be047d8c9d2a42e17c82cc75b6a37077d4c3cf17bba6c420f392f` (‏SHA-256 لخريطة بصمات 81 ملفًّا مجمَّدًا)
- **المراجعة:** 1 (INITIAL) · الحالة **FROZEN**
- **المحرّك:** `FAISAL-V4 1.0 (2026-10-02)` · **السجلّ:** `V4-RULES 1.0 (2026-10-02)` · **بصمةُ الإعداد:** `3829aa5ed84827c68d04daa14cd3bd4e8cf1b1040fe3c04724a81d784879397e`
- **آخرُ تغييرٍ في نواة المحرّك:** `d8b493727af7` (2026-10-02T21:36:57+00:00) — المنهجُ لم يتغيّر منذه (بصماتُ النواة في البيان)
- **رأسُ البناء:** `49f30f95c7c7` · وcommit الدمج على main يُسجَّل في وثائق V4.1 بعد الدمج

## ② ما يُجمَّد وما يُسجَّل

- **مجمَّد (منهجٌ ودليل):** كلُّ ملفٍّ تحت `faisal_method_v4/` (المحرّك · سجلُّ القواعد · بنّاءُ الحالات · الوسوم · المرورُ البصريّ · التقييم · الفِكستشر · النتائج · الوثائق · الصور المركّبة) ‏+ `.github/workflows/faisal_v4.yml` ‏+ ما يقرؤه V4 من V3.1: `faisal_method_v3/faisal_tool.py` · `faisal_method_v3/image_corpus.json` · `faisal_method_v3/dedup_clusters.json` · `faisal_method_v3/source_access.json` · `faisal_method_v3/v31/golden_fixtures.json` · `faisal_method_v3/v31/golden_cases_v31.json` · `faisal_method_v3/v31/reconcile_v31.json` · `faisal_method_v3/v31/rule_audit_v31.json`
- **مسجَّلٌ لا مجمَّد (اكتسابُ بيانات):** `Super_stock.py` (`40d5f89884a8`) · `market_calendar.py` (`01909d482472`) · `tv_data.py` (`2523e156ccda`) — تُختم بصمتُها في كلّ تشغيلةٍ أماميّة.
- **صورُ فيصل (722):** مثبَّتةٌ عبر `image_corpus.json` المجمَّد (بصمةُ كلّ صورة · ويعيد V4L16 حسابها).

## ③ الإعداد المجمَّد (PARAMS)

| المفتاح | القيمة | وسمُ المصدر |
|---|---|---|
| `AT_BAND_PCT` | 3.0 | production |
| `BID_LO_PCT` | 5.0 | faisal_verbatim |
| `CYCLE_BARS` | 120 | production |
| `HOLD_MIN` | 5 | faisal_verbatim |
| `HOLD_ZONE` | 3 | faisal_inferred |
| `LEVEL_TOL_PCT` | 2.0 | faisal_verbatim |
| `MIN_BARS` | 40 | engineering |
| `RECLAIM_BARS` | 2 | engineering |
| `RISE_TEST_PCT` | 15.0 | faisal_inferred |
| `SHORT_AVAIL_MAX` | 20000 | faisal_verbatim |
| `SWEEP_MAX_PCT` | 13.0 | faisal_tier2b |
| `SWEEP_PROJ_PCT` | [5.0, 10.0] | faisal_verbatim |
| `SWING_K` | 3 | engineering |
| `ZONE_PCT` | 15.0 | faisal_verbatim |

## ④ جردُ القواعد

| القاعدة | فعّالة | الحالة (السجلّ) | القراريّة | مستوى المصدر | صور |
|---|---|---|---|---|---|
| `H-D2` | لا | CONTRADICTED | UNKNOWN | 5 | 0 |
| `R-SUP-MAIN` | لا | SUPPORTED | DECISIONAL | 6 | 0 |
| `R-W-SPAN` | لا | SUPPORTED | UNKNOWN | 4 | 3 |
| `R4-BOT-01` | نعم | SUPPORTED | DECISIONAL | 2 | 5 |
| `R4-CYC-01` | نعم | CONFIRMED | DECISIONAL | 3 | 13 |
| `R4-DATA-01` | نعم | CONFIRMED | DECISIONAL | 7 | 0 |
| `R4-ENT-01` | نعم | CONFIRMED | SUPPORTING | 2 | 6 |
| `R4-ENT-02` | نعم | SUPPORTED | INFORMATIONAL | 2 | 5 |
| `R4-HOLD-01` | نعم | SUPPORTED | DECISIONAL | 3 | 5 |
| `R4-HOLDZ-01` | نعم | PROBABLE | DECISIONAL | 2 | 4 |
| `R4-INV-01` | نعم | SUPPORTED | DECISIONAL | 2 | 5 |
| `R4-LOC-01` | نعم | CONFIRMED | DECISIONAL | 2 | 4 |
| `R4-OP-01` | نعم | SUPPORTED | UNKNOWN | 2 | 6 |
| `R4-STOP-01` | نعم | SUPPORTED | SUPPORTING | 2 | 5 |
| `R4-SWEEP-01` | نعم | SUPPORTED | DECISIONAL | 2 | 7 |
| `R4-TF-01` | نعم | SUPPORTED | INFORMATIONAL | 2 | 4 |
| `R4-TGT-01` | نعم | CONFIRMED | INFORMATIONAL | 2 | 5 |
| `R4-VAL-GRP-01` | نعم | SUPPORTED | DECISIONAL | 2 | 6 |
| `R4-VAL-OFF-01` | نعم | SUPPORTED | DECISIONAL | 2 | 4 |
| `R4-VAL-SHORT-01` | نعم | PROBABLE | DECISIONAL | 2 | 3 |
| `R4-ZONE-01` | نعم | SUPPORTED | DECISIONAL | 1 | 5 |

## ⑤ النتائج المنشورة عند التجميد (قائمةٌ لا جديدة)

- **السويّة:** 5177 نجح · 0 فشل · خروج 0 (‏`0e909a7`) · **الطفرات:** 36/36
- **الذهبيّة:** V3.1 3/7 · V4 4/7 · «دائمًا WAIT» 5/7 (من 9 · المؤرَّخة 7) · DXST D · VEEE UNKNOWN
- **H-STATE S1 (وصفيّ):** n 19 · تطابقٌ 15 · «دائمًا WAIT» 18 · READY من المحرّك 0 · UNKNOWN 3 · READY عند فيصل 1
- **H-LEVEL الاحتجاز:** FAIL (‏+0.2466 [-0.0094 · +0.5873] · مستويات 22 · حالات 7)
- **الحالات:** 157 من 217 عبارة · S1 22 (اكتشاف 12 · احتجاز 10) · S2 63 · S3 19 · S4 13 · مستبعد 40
- **المدوّنة:** 722 صورة · بصمةٌ مطابقة 722 · وحداتٌ 609 · عناقيد 102 · أوّليّة 265
- **القواعد:** 21 (18 فعّالة)

## ⑥ السياسة

- **لا تغييرَ منهجيّ** أثناء التحقّق الأماميّ (إضافةُ قاعدة · حذفُها · عتبة · تسامح · ترتيبُ القرار · منطقُ READY/WAIT/REJECT · النماذج · الدعم · الأهداف · الصلاحيّة) ⟵ `V4_CHANGE_REQUESTS.md` و`V4_2_RESEARCH_QUEUE.md`.
- **خطأُ التنفيذ** (والمواصفةُ المجمَّدة تحدّد السلوكَ صراحةً) ⟵ مراجعةٌ جديدة `IMPLEMENTATION_BUG` بقفلِ ارتداد وطفرة وقائمةِ تشغيلاتٍ مُبطَلةٍ تُعاد.
- **FV41** يُسقط السويّة عند أيّ بايتٍ تغيّر أو ملفٍّ أُضيف/حُذف أو إعدادٍ حيٍّ اختلف أو مراجعةٍ خارج السياسة.
