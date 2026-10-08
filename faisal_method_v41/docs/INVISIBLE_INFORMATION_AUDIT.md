# INVISIBLE_INFORMATION_AUDIT — فرضيّةُ «المعلومة الخفيّة» (§11 · §13-15)

> مولَّدٌ من `faisal_method_v41/docs_v41.py` — كلُّ رقمٍ من JSON (لا رقمَ باليد · FVD1) · العقدُ `V41_prereg.md` مدموجٌ قبل أيّ رقم (#550) · V4 مجمَّد: `FREEZE_ID 5f291a3b301be047…` · commit التجميد الرسميّ `7c8826c`.

## ① الحكم
- **الأماميّ (الرسميّ): UNKNOWN** — N = 3 (دون حدّ الحكم بالنسبة 10) · خلافاتٌ أماميّة 0.
- **التاريخيّ الملوَّث (وصفيّ): SUPPORTED** — k (D بعد البدائل) = 6 من N (الخلافاتُ عدا E/G) = 11 ⟵ 0.545.
  ❌ **تنبّؤي Q8 «الحكمُ PARTIAL» خاب** (الأكثرُ D صدق) — يُنشر ولا يُحذف.
- **ما يعنيه بالضبط:** كلُّ D هنا من نوعٍ واحد — **V4 جاهزٌ فنيًّا ويمتنع (UNKNOWN) لأنّ الصلاحيّةَ غائبة وفيصل قال WAIT** ⟵ فيصل يقرّر بمعلومةٍ
  ليست في الشموع (المضارب · القروبات · الطرح · الشورت) — **ولا حالةَ واحدةً قال فيها V4 WAIT/REJECT وناقضته معلومةٌ خفيّة**. والمقامُ 11 (حدُّ الحكم بالنسبة 10).

## ② المنهج (العقد §⑫ — البدائلُ قبل «المعلومة الخارجيّة»)
لكلّ خلافٍ يُسجَّل **أوّلُ** ما يفسّره بالدليل المسجَّل: ① بياناتٌ ناقصة ⟵ **E** · ② توقيت (`SCALE_MISMATCH` أو سعرُ الصورة يخالف إغلاقَ القراءة
بأكثرَ من 15%) ⟵ **G** · ③ V4 جاهزٌ فنيًّا ويمتنع لغياب معلومةٍ بنفسه ⟵ **D** · ④ فريمُ فيصل لا يضمّ اليوميّ ⟵ **B** · ⑤ فئةُ خطّة فيصل ≠ فئةُ المستوى
الحاسم في V4 ⟵ **B** · ⑥ العبارةُ مذكورةٌ مناقِضةً في القاعدة الحاجبة ⟵ **C** · ⑦ اعتمادُ الحالة UNAVAILABLE/EXTERNAL ⟵ **D** · ⑧ وإلّا **H** ·
و**A** إن ناقض مخرجُ V4 مواصفتَه · و**F** لعباراتٍ متعارضة. أسئلةُ المهمّة العشرة (§15) مرسومةٌ عليها: الهندسةُ والبنيةُ والدعمُ والموقع ⟵ ⑤ ·
الفريم ⟵ ④ · التوقيت ⟵ ② · المعلومةُ الخارجيّة ⟵ ③/⑦ · التعليقُ اليدويّ/الالتباس ⟵ F · البياناتُ الناقصة ⟵ ① · الحكمُ التقديريّ ⟵ ⑥.

## ③ كلُّ خلاف (S1+S2 · 16) — الحقولُ الأحد عشر (§11)
الفئات: D 6 · B 5 · G 4 · E 1 · A 0 · C 0 · F 0 · H 0 · **H (غيرُ مفسَّر) = 0**.

| الحالة | المجموعة | فيصل | V4 | الفرق | الحاجبة | الناقص | السببُ المحتمل | دليلُ القواعد | الفئة |
|---|---|---|---|---|---|---|---|---|---|
| `EHGO_2026-05-22` | S1 | WAIT | UNKNOWN (PRESS_RECLAIM) | V4 يمتنع (UNKNOWN) وفيصل يقرّر WAIT | — | القروبات (R4-VAL-GRP-01) · الطرح/التخفيف (R4-VAL-OFF-01) · المتاح للشورت (R4-VAL-SHORT-01) · بصمة المضارب/الضغط (R4-OP-01) | V4 جاهزٌ فنيًّا وينقصه بنفسه: القروبات (R4-VAL-GRP-01) · الطرح/التخفيف (R4-VAL-OFF-01) · المتاح للشورت (R4-VAL-SHORT-01) · بصمة المضارب/الضغط (R4-OP-01) | R4-OP-01 SUPPORTED · R4-VAL-GRP-01 CONFIRMED · R4-VAL-OFF-01 CONFIRMED · R4-VAL-SHORT-01 SUPPORTED | **D** |
| `PIII_2026-05-16` | S2 | READY | WAIT (BASE_FORMING) | V4 أشدّ: WAIT وفيصل READY | R4-HOLD-01 | — | فئةُ خطّة فيصل AT ≠ فئةُ مستوى V4 BELOW | R4-HOLD-01 SUPPORTED | **B** |
| `ERNA_2026-05-0x` | S2 | READY | WAIT (BROKEN_NEW_BASE) | V4 أشدّ: WAIT وفيصل READY | R4-INV-01 | — | سعرُ الصورة يخالف إغلاقَ القراءة ×0.635 (توقيت/أفتر) | R4-INV-01 CONFIRMED | **G** |
| `BETA_2026-04-05` | S1 | WAIT | UNKNOWN (PRESS_RECLAIM) | V4 يمتنع (UNKNOWN) وفيصل يقرّر WAIT | — | القروبات (R4-VAL-GRP-01) · الطرح/التخفيف (R4-VAL-OFF-01) · المتاح للشورت (R4-VAL-SHORT-01) · بصمة المضارب/الضغط (R4-OP-01) | V4 جاهزٌ فنيًّا وينقصه بنفسه: القروبات (R4-VAL-GRP-01) · الطرح/التخفيف (R4-VAL-OFF-01) · المتاح للشورت (R4-VAL-SHORT-01) · بصمة المضارب/الضغط (R4-OP-01) | R4-OP-01 SUPPORTED · R4-VAL-GRP-01 CONFIRMED · R4-VAL-OFF-01 CONFIRMED · R4-VAL-SHORT-01 SUPPORTED | **D** |
| `MSGY_2026-09-0x` | S2 | WAIT | UNKNOWN (BASE_HELD) | V4 يمتنع (UNKNOWN) وفيصل يقرّر WAIT | — | القروبات (R4-VAL-GRP-01) · الطرح/التخفيف (R4-VAL-OFF-01) · المتاح للشورت (R4-VAL-SHORT-01) · بصمة المضارب/الضغط (R4-OP-01) | V4 جاهزٌ فنيًّا وينقصه بنفسه: القروبات (R4-VAL-GRP-01) · الطرح/التخفيف (R4-VAL-OFF-01) · المتاح للشورت (R4-VAL-SHORT-01) · بصمة المضارب/الضغط (R4-OP-01) | R4-OP-01 SUPPORTED · R4-VAL-GRP-01 CONFIRMED · R4-VAL-OFF-01 CONFIRMED · R4-VAL-SHORT-01 SUPPORTED | **D** |
| `DCOY_2026-09-2x` | S2 | REJECT | UNKNOWN (PRESS_RECLAIM) | V4 يمتنع (UNKNOWN) وفيصل يقرّر REJECT | — | القروبات (R4-VAL-GRP-01) · الطرح/التخفيف (R4-VAL-OFF-01) · المتاح للشورت (R4-VAL-SHORT-01) · بصمة المضارب/الضغط (R4-OP-01) | سعرُ الصورة يخالف إغلاقَ القراءة ×0.506 (توقيت/أفتر) | — | **G** |
| `LIMN_2026-09-22` | S1 | WAIT | UNKNOWN (BASE_HELD) | V4 يمتنع (UNKNOWN) وفيصل يقرّر WAIT | — | القروبات (R4-VAL-GRP-01) · الطرح/التخفيف (R4-VAL-OFF-01) · المتاح للشورت (R4-VAL-SHORT-01) · بصمة المضارب/الضغط (R4-OP-01) | V4 جاهزٌ فنيًّا وينقصه بنفسه: القروبات (R4-VAL-GRP-01) · الطرح/التخفيف (R4-VAL-OFF-01) · المتاح للشورت (R4-VAL-SHORT-01) · بصمة المضارب/الضغط (R4-OP-01) | R4-OP-01 SUPPORTED · R4-VAL-GRP-01 CONFIRMED · R4-VAL-OFF-01 CONFIRMED · R4-VAL-SHORT-01 SUPPORTED | **D** |
| `CRE_2026-09-2x` | S2 | WAIT | UNKNOWN (PRESS_RECLAIM) | V4 يمتنع (UNKNOWN) وفيصل يقرّر WAIT | — | القروبات (R4-VAL-GRP-01) · الطرح/التخفيف (R4-VAL-OFF-01) · المتاح للشورت (R4-VAL-SHORT-01) · بصمة المضارب/الضغط (R4-OP-01) | V4 جاهزٌ فنيًّا وينقصه بنفسه: القروبات (R4-VAL-GRP-01) · الطرح/التخفيف (R4-VAL-OFF-01) · المتاح للشورت (R4-VAL-SHORT-01) · بصمة المضارب/الضغط (R4-OP-01) | R4-OP-01 SUPPORTED · R4-VAL-GRP-01 CONFIRMED · R4-VAL-OFF-01 CONFIRMED · R4-VAL-SHORT-01 SUPPORTED | **D** |
| `BTOG_2026-09-04` | S2 | REJECT | WAIT (BROKEN_NEW_BASE) | V4 WAIT وفيصل REJECT | R4-INV-01 | — | فريمُ فيصل ['W'] لا يضمّ اليوميّ (المحرّكُ يوميٌّ وحدَه · R4-TF-01) | R4-INV-01 CONFIRMED · R4-TF-01 SUPPORTED | **B** |
| `ELPW_2026-01` | S2 | READY | WAIT (BROKEN_NEW_BASE) | V4 أشدّ: WAIT وفيصل READY | R4-INV-01 | — | فئةُ خطّة فيصل None ≠ فئةُ مستوى V4 BELOW | R4-INV-01 CONFIRMED | **B** |
| `DSY_2026-04` | S2 | READY | WAIT (BROKEN_NEW_BASE) | V4 أشدّ: WAIT وفيصل READY | R4-INV-01 | — | سعرُ الصورة يخالف إغلاقَ القراءة ×1.31 (توقيت/أفتر) | R4-INV-01 CONFIRMED | **G** |
| `EHGO_2026-06` | S2 | READY | WAIT (RETEST_IN_PROGRESS) | V4 أشدّ: WAIT وفيصل READY | R4-HOLDZ-01 | — | سعرُ الصورة يخالف إغلاقَ القراءة ×1.21 (توقيت/أفتر) | R4-HOLDZ-01 SUPPORTED | **G** |
| `JZ_2026-07` | S2 | WAIT | UNKNOWN (BASE_HELD) | V4 يمتنع (UNKNOWN) وفيصل يقرّر WAIT | — | القروبات (R4-VAL-GRP-01) · الطرح/التخفيف (R4-VAL-OFF-01) · المتاح للشورت (R4-VAL-SHORT-01) · بصمة المضارب/الضغط (R4-OP-01) | V4 جاهزٌ فنيًّا وينقصه بنفسه: القروبات (R4-VAL-GRP-01) · الطرح/التخفيف (R4-VAL-OFF-01) · المتاح للشورت (R4-VAL-SHORT-01) · بصمة المضارب/الضغط (R4-OP-01) | R4-OP-01 SUPPORTED · R4-VAL-GRP-01 CONFIRMED · R4-VAL-OFF-01 CONFIRMED · R4-VAL-SHORT-01 SUPPORTED | **D** |
| `MWC_2026-06` | S2 | WAIT | UNKNOWN (DATA_INSUFFICIENT) | V4 يمتنع (UNKNOWN) وفيصل يقرّر WAIT | R4-DATA-01 | شموعٌ يوميّةٌ كافية قبل تاريخ القراءة | شموعٌ ناقصة قبل تاريخ القراءة | R4-DATA-01 UNKNOWN | **E** |
| `UPC_2026-07` | S1 | READY | WAIT (BROKEN_NEW_BASE) | V4 أشدّ: WAIT وفيصل READY | R4-INV-01 | — | فئةُ خطّة فيصل NONE ≠ فئةُ مستوى V4 BELOW | R4-INV-01 CONFIRMED | **B** |
| `SXTC_2026-09-1x_a` | S2 | READY | WAIT (BROKEN_NEW_BASE) | V4 أشدّ: WAIT وفيصل READY | R4-INV-01 | — | فئةُ خطّة فيصل AT ≠ فئةُ مستوى V4 BELOW | R4-INV-01 CONFIRMED | **B** |

> `RULES_TRIGGERED` و`DATA_AVAILABLE` (شموعُ القراءة · الإغلاق · سعرُ الصورة · والسياقُ «لا شيء» في تشغيل V4 التاريخيّ) لكلّ خلافٍ في
> `results/analysis_v41.json` · و`EVIDENCE_STATUS` للحالة كلِّها: **HISTORICAL-CONTAMINATED** بطبقتها.

## ④ الاعتمادُ على المعلومة الخارجيّة (§14 · S1+S2)
| الاعتماد | N | كلمةُ فيصل | قرارُ V4 |
|---|---|---|---|
| CHART-DERIVABLE | 35 | WAIT 20 · UNKNOWN 12 · READY 2 · REJECT 1 | WAIT 28 · UNKNOWN 7 |
| EXTERNAL-DATA-DERIVABLE | 33 | WAIT 20 · UNKNOWN 10 · READY 2 · REJECT 1 | WAIT 29 · UNKNOWN 4 |
| MANUAL/DISCRETIONARY | 3 | WAIT 3 | WAIT 2 · UNKNOWN 1 |
| UNAVAILABLE | 13 | WAIT 9 · READY 3 · UNKNOWN 1 | WAIT 11 · UNKNOWN 2 |

**هل UNKNOWN في V4 يتصرّف صحيحًا؟** مخرجاتُ V4 الجاهزة فنيًّا 16 ⟵ UNKNOWN 16 · READY 0 ⟵
**يمتنع ولا يختلق READY** (§36: «UNKNOWN أفضلُ من READY مصطنَع») — بنيويّ: operator_press = None دائمًا ⟵ الجاهزيّةُ الفنيّة بلا WAIT/REJECT صريحٍ تصير UNKNOWN.

## ⑤ «الطلباتُ عند الدعم» (§13 — لا يُفترض أنّها شرط)
| الدعم/الطلبات | READY | WAIT | REJECT | UNKNOWN |
|---|---|---|---|---|
| no_support+no_orders | 2 | 7 | 0 | 10 |
| no_support+orders | 0 | 6 | 1 | 7 |
| support+no_orders | 2 | 23 | 0 | 5 |
| support+orders | 3 | 16 | 1 | 1 |

**H-ORD («كلُّ READY بدعمٍ يذكر الطلبات»): CONTRADICTED** (READY بدعم = 5) — تاريخيٌّ ملوَّثٌ وصفيّ ⟵ يوافق قرارَ V4
أنّها `SUPPORTING` (آليّةُ دخولٍ لا شرطُ قرار) · **ولا يُغيَّر V4** · والحكمُ الرسميّ أماميّ.
