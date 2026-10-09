# 🧭 FAISAL RESEARCH ENGINE (`faisal_engine/`) — محرّكُ بحثٍ معزول (2026-10-09)

**قراءةٌ فقط · لا إنتاج · لا تلغرام · لا V4 يُعدَّل · لا H6 يُمَسّ.** يُعيد بناءَ عمليّة فيصل (SCREEN ⟵ FOCUS ⟵ WATCH ⟵ READY ⟵ TRIGGER) فوق
نواة V4 المجمَّدة والفارز الإنتاجيّ المجمَّد بلا جدار اللمستين، بقراءةٍ آمنةٍ من النظر للأمام وصلاحيّةٍ مؤرَّخة، وUNKNOWN لكلّ ما لا مصدرَ له.

| الملفّ | الدور |
|---|---|
| `engine.py` | القلب: `evaluate(symbol, rows, asof, context, label, screen)` ⟵ سجلٌّ قابلٌ للتفسير (§8) · CLI: `engine.py SYM --asof DATE` |
| `data.py` | مِقبسُ الشموع/التقسيمات/SEC المجمَّدة (2026-10-08) · السياقُ المؤرَّخ |
| `replay.py` | الإعادةُ التاريخيّة وفق `REPLAY_PROTOCOL.md` ⟵ `out/` (units · controls · lead_time · summary.json) |
| `ledger.py` | `FAISAL_RULE_LEDGER.json/.csv` — القواعدُ بأصناف الدليل الخمسة ومعرّفاتِ الصور |
| `source_audit.py` | `out/source_audit.json` — مصالحةُ المدوّنة والمصادر |
| `docs.py` | يبني الوثائق السبع من JSON/CSV (لا رقمَ باليد) |
| `SOURCE_RECOVERY_AUDIT.md` · `FAISAL_METHOD_SPEC.md` · `HISTORICAL_REPLAY_REPORT.md` · `BASELINE_COMPARISON.md` · `KNOWN_FAILURES.md` · `VALIDATION_REPORT.md` · `OWNER_HANDOFF.md` | المخرجاتُ المطلوبة |

## التشغيل
```bash
FAISAL_ONLY=1 python3 faisal_engine/engine.py DKI --asof 2026-09-14
FAISAL_ONLY=1 python3 faisal_engine/replay.py          # ≈2 دقيقة · يكتب faisal_engine/out/ وحدَه
python3 faisal_engine/ledger.py && python3 faisal_engine/source_audit.py && python3 faisal_engine/docs.py
python3 test_bot.py                                     # أقفال FE0-FE9 (قبل LEAK0)
```
المراحل: `INSUFFICIENT_DATA` · `REJECTED` (أوّلُ بوّابةٍ ساقطة مسمّاة) · `FOCUS` · `WATCH` · `READY` · `TRIGGER` · `HOLD` (مانعُ صلاحيّةٍ مؤرَّخ).
الوسوم: `HISTORICAL` · `EXPLORATORY` · `LIVE`. الحكمُ الحاليّ: **IMPLEMENTED, BUT PERFORMANCE NOT ESTABLISHED** (`VALIDATION_REPORT.md`).

## 🏁 المرتِّب تحت ميزانيةٍ ثابتة (2026-10-09 · `RANKING_PROTOCOL.md` مدموجٌ قبل أيّ ترتيب #592 · EXPLORATORY)

| الملفّ | الدور |
|---|---|
| `RANKING_PROTOCOL.md` | العقد (مجمَّدٌ ببصمته في RNK7) · `RANKING_PROTOCOL_ADDENDA.md` الإضافاتُ المؤرَّخة (D1 لاحقٌ موسوم) |
| `rank_universe.py` | إعادةُ بناء الكون كلِّه لكلّ جلسة على رنر (شموع TradingView · التقسيمات · SEC · البوتُ المجمَّد · المحرّك) ⟵ `data/rank/` (‏`rows.csv.gz` ‏229,449 صفًّا · `manifest.json` بالبصمات · تشغيلة `37942829821`) |
| `ranker.py` | المتغيّرات A/B/C المسجَّلة و D1 اللاحق — مفاتيحُ معجميّةٌ حتميّة بلا أوزان · سجلُّ الميزات (8 حقول لكلّ ميزة) · تفسيرٌ لكلّ صفّ |
| `rank_eval.py` · `rank_report.py` | التقييمُ كلُّه (الحلقات · K = 25/50/108 · الدقيق والمبكر منفصلان · خطّا الأساس · العشوائيّ · البوتستراب العنقوديّ · LOO · الطيّان · التشخيص · DKI/SXTC/HUBC) ⟵ `out/rank_*` و`RANKING_RESULT.md` |
| `RANKING_REPORT.md` | التقريرُ النهائيّ (A–J ‏+ تدقيقُ النزاهة العشريّ) |
| `data/rank/reject_stats.json` | لقطةُ `reject_stats` المجمَّدة (الإنتاجُ يحفظ 56 يومًا متدحرجة ⟵ لا تُقرأ حيّةً · RNK16) |

```bash
python3 faisal_engine/ranker.py --date 2026-09-14 --variant C --symbol DKI   # رتبةُ رمزٍ في يوم (مع التفسير)
python3 faisal_engine/ranker.py --date 2026-09-14 --variant C --k 108        # قائمةُ اليوم (25 · 50 · 108 بـ--k)
python3 faisal_engine/rank_eval.py            # الإعادةُ الكاملة (≈10 ث) ⟵ out/rank_* + RANKING_RESULT.md
python3 faisal_engine/rank_eval.py --check    # إعادةُ التوليد في مجلّدٍ مؤقّت ومقارنةُ البايتات بالملتزَم (خروج 0)
python3 test_bot.py                           # أقفال RNK0-RNK16 (قبل LEAK0)
```
الحكم: **2 — IMPROVEMENT NOT DEMONSTRATED** (C ‏6/22 مقابل البوت 2/22 عند 108 · الحدُّ الأدنى 98.33% = 0.000 لا أكبر منه).

## 🔀 دلالاتُ المراحل: «قائمتي» و«جاهز» عند فيصل مقابل مراحل المحرّك (2026-10-09 · العقد `STAGE_SEMANTICS_PROTOCOL.md` مدموجٌ قبل أيّ قراءة محرّك #595 · EXPLORATORY · بحثٌ فقط)

| الملفّ | الدور |
|---|---|
| `stage_ledger.py` · `data/stage/eye_reads.json` | سجلُّ أحداثٍ من المصدر (عبارةٌ × رمز): `RAW_LABEL`/`RAW_ACTION` حرفيّان · جودةُ الطابع من وقتٍ مطبوعٍ أو مشتقّ لا من ترتيب الملفّات · المفاهيمُ منفصلة (A عضويّةُ القائمة · B مرحلةُ الاختيار · C الفعل · E الزناد) · المُسترجَع لا يُنسَب ليوم المنشور ⟵ `out/stage_events.csv` · `stage_episodes.csv` · `stage_transitions.csv` · `stage_phase3_reconciliation.csv` · `stage_ledger_summary.json` · بلا استيرادٍ للمحرّك |
| `stage_crosswalk.py` | قراءاتُ المحرّك (`engine`) ⟵ `out/stage_engine_reads.csv` · ثمّ H1-H3 والمقارنات A-E منفصلة (صارمٌ/عريض · المجهولُ ليس خطأ) ⟵ `stage_crosswalk.csv` · `stage_overlay.csv` (SOURCE_LIST_STATE · SOURCE_SELECTION_STAGE · TECHNICAL_ENGINE_STAGE · OBSERVED_ACTION · TRIGGER_STATE · EVIDENCE_STATUS · والفجوةُ UNKNOWN) · `stage_case_timelines.csv` · `STAGE_SEMANTICS_RESULT.md` |
| `STAGE_SEMANTICS_REPORT.md` | التقريرُ النهائيّ (A–J) |

```bash
python3 faisal_engine/stage_ledger.py --check            # إعادةُ توليد السجلّ ومقارنتُه بالملتزَم (خروج 0)
python3 faisal_engine/stage_crosswalk.py engine          # قراءاتُ المحرّك (FAISAL_ONLY=1 داخليًّا · ≈دقيقة)
python3 faisal_engine/stage_crosswalk.py --check         # إعادةُ توليد المقارنة ومقارنتُها (خروج 0)
python3 test_bot.py                                      # أقفال STG1-STG14 · STX1-STX12 (قبل LEAK0)
```
الحكم: **3 — INSUFFICIENT EVIDENCE TO ESTABLISH THE MAPPING** (H1 «جاهز» = READY: حلقةٌ صارمةٌ واحدة دون حدّ 3 · H2 عضويّةُ القائمة مستقلّةٌ عن الحالة الفنّيّة: **مسنودة** · H3 الانتباهُ المحمول لا يُقرأ من الشموع: مسنودةٌ على المجموعة المقبولة بالعقد (2 من 3 خارج المسار) وصارمًا وحدَه لا كفاية) · وFOCUS في المرحلة 3 = عضويّةُ قائمةٍ وحدَها (10/10) و«جاهز» صريحٌ في 0 من 6 صفوف READY.

## 🧾 الحقيقةُ التاريخيّة لحلقات الترتيب (2026-10-09 · «HISTORICAL GROUND-TRUTH RECOVERY» · EXPLORATORY · بحثٌ فقط)

| الملفّ | الدور |
|---|---|
| `data/gt/gt_eye_reads.json` | قراءةُ عينٍ لـ33 صورةً أصليّةً لم تُقرأ في سجلّ المراحل (النصُّ حرفيًّا · بلا أسماءٍ خاصّة ولا معرّفات متابعين) |
| `data/gt/episode_evidence.json` | سجلُّ أدلّة الحلقات الـ23: كلُّ عبارةٍ بكاتبها وهُويّة رمزها وطابعها (VERIFIED/STRONGLY_SUPPORTED/INFERRED/AMBIGUOUS/UNKNOWN) وأساسِ كلٍّ منها · وفعلُ فيصل بفئاته التسع · والتصحيحاتُ والعناصرُ الناقصة |
| `gt_audit.py` | المُدقِّق: المقتطفُ حرفيٌّ من القراءة · الطابعُ VERIFIED يُعيد يومَ القرار من الوقت المطبوع · وحداتُ الترتيب الـ41 كلُّها محسوبة · العلاقةُ بالحركة بتعريف المرحلة 3 (MOVE_50_20) على الشموع المجمَّدة حتى 2026-10-08 · المتعلّقاتُ وحدةٌ واحدة ⟵ `out/gt_episodes.csv` · `gt_units.csv` · `gt_summary.json` · `GROUND_TRUTH_RESULT.md` · بلا استيرادٍ للمحرّك ولا للإنتاج |
| `GROUND_TRUTH_AUDIT.md` | التقريرُ النهائيّ (1–10) |

```bash
python3 faisal_engine/gt_audit.py            # إعادةُ البناء
python3 faisal_engine/gt_audit.py --check    # إعادةُ التوليد في مجلّدٍ مؤقّت ومقارنةُ البايتات بالملتزَم (خروج 0)
python3 test_bot.py                          # أقفال GTA1-GTA12 (قبل LEAK0)
```
القرار: **C — INSUFFICIENT HISTORICAL GROUND TRUTH** (وحداتٌ مستقلّةٌ لاختيار فيصل نفسِه قبل الحركة بطابعٍ موثوق: 4 — AMIX · DCOY · MI · MSGY — و3 منها بين الـ22 · والحدُّ 15 · وحتى لو حُسم كلُّ مجهولٍ لصالحها فالسقفُ 13).

## 🚪 جردُ البوّابات ومصدرُها والاستبعادُ الأوّل (2026-10-09 · «GATE PROVENANCE, CANDIDATE GENERATION, AND EVIDENCE-BASED REPAIR» · بحثٌ فقط)

| الملفّ | الدور |
|---|---|
| `data/gate_provenance.json` | المصدرُ المنسَّق: لكلّ بوّابةٍ في السلسلة (الكون ⟵ البيانات ⟵ `analyze_ticker` ⟵ ما بعد الفرز ⟵ السلامة ⟵ السعة ⟵ ما بعد الإثراء ⟵ الجاهزيّة ⟵ أدوات الطلب) موضعُها ودورُها ونوعُها وصنفُ مصدرها **الواحد من ستّة** وأدلّتُها (الوحدة · النصّ حرفيًّا · الكاتب · الطابع · المعنى · الاستقلال · ما الذي بُني عليه) وحالتُها وما يُسمح بعدها |
| `gate_audit.py` | (‏2026-10-09 · المراجعةُ الخصوميّة) دوالُّ نقيّة: أربعةُ أبعادٍ لكلّ بوّابة (المنشأ · المسوِّغ · الدور · الأمانة) و**المسوِّغُ مشتقٌّ من الأدلّة** (`derive_justification`: المفهومُ وكلُّ عتبةٍ والصلابة · الغيابُ والتعليقُ والموروثُ والعيّنةُ لا تُسوِّغ · وقولُ فيصل لنظامٍ آخر منقولٌ لا مباشر) · `check_origin` · `check_fidelity` · `pass_rate` (المجهولُ لا يجتاز ولا يسقط) |
| `data/gate_v23_extract.json` | مقتطفٌ مجمَّد من رفع المالك الأوّل v2.3 (`4510eb3ce` · 2026-06-20 · بصمتُه) — لأن استنساخ CI ضحل · مصدرُ منشأ «موروث» |
| `data/gate_pool_evidence.json` | صفوفُ حصاد المتاح المجمَّدة (997 حتى 2026-10-09 · بصمتُها) وتشغيلةُ 10-09 (`37902530011`) — مصدرُ §4c |
| `data/gate_reject_snapshot.json` | لقطةٌ مجمَّدة من `reject_log.json` (‏20 يومًا · العدُّ الكامل `walls_n` لا القائمةُ المقصوصة) |
| `gate_inventory.py` | البنّاء: سطرُ كلّ بوّابةٍ داخل دالّتها بالـAST · القيمُ الحيّة على `FAISAL_ONLY=1` · **الاكتمال** (كلُّ رمزِ رفضٍ وكلُّ `return None` صامتٍ في `analyze_ticker` وكلُّ دالّةِ بوّابةٍ بعد الفرز مجرودة وإلّا يسقط البناء) · الاستبعادُ الأوّل لكلّ حلقةٍ على الشموع المجمَّدة (< T) بـ`analyze_ticker` الإنتاجيّ مع سلسلة القشر واختبارِ التقسيم غيرِ المسوّى ⟵ `out/GATE_INVENTORY.json` · `out/GATE_INVENTORY.csv` · `out/gate_first_exclusion.csv` · `GATE_PROVENANCE_REPORT.md` |

```bash
python3 faisal_engine/gate_inventory.py                 # إعادةُ البناء
python3 faisal_engine/gate_inventory.py --check         # إعادةُ التوليد والمقارنة (الأسطرُ مُطبَّعة) — خروج 0
python3 faisal_engine/gate_inventory.py --completeness  # سريع: المراسي والاكتمال وحدَهما
python3 test_bot.py                                     # أقفال GPV1-GPV12 · GPA1-GPA8 · GPS0-GPS10 (قبل LEAK0)
```
النتيجة (EXPLORATORY · `GATE_PROVENANCE_REPORT.md`): 49 بوّابة — مباشرٌ من فيصل 1 (ذراعُ باكتيستٍ مطفأة) · مستنتَجٌ 17 · سياسةُ المالك 12 · هندسيّ 19 · صفرُ بوّابةِ رفضٍ نشطة بدليلٍ مباشر · **الجدارُ الأوّل على الحلقات الـ22: المِرساة 13 · مدى القاعدة 3 · يمرّ 2 · العمق 1 · السقف 1 · الانفجار 1 · RSI الآن 1** · والمِرساةُ في سلسلة 21 من 24 حالة · ومطابقةُ صفوف الترتيب المجمَّدة 22/22 · والتقسيماتُ في الشموع مسوّاةٌ عند تواريخها (لا حالةَ جدارُها الأوّل خطأُ بيانات) · و23/23 طفرةً سقطت (`out/gate_mutations.json`).
🔄 **تصحيحٌ مؤرَّخ 2026-10-09 (المراجعةُ الخصوميّة):** «صنفُ المصدر الواحد» أعلاه خلط المنشأَ بالمسوِّغ (غيابُ مصدرِ فيصل قُرئ «حارسًا هندسيًّا») ⟵ الأبعادُ الأربعة: المنشأ — مستنتَجٌ 17 · مالكٌ 11 · هندسيّ 6 · موروثٌ 15 · مباشرٌ 0 · المسوِّغ — مباشرٌ 0 · مالكٌ 8 · ثابتٌ تشغيليّ 5 · مختبَرٌ 1 · جزئيٌّ 32 · **بلا مسوِّغ 3** (`M13_SHORT` · `STOPPED_EXCLUSION` · `M8_GAP_REQUIRED` المطفأ) · مناقَضٌ بمصدرٍ لفيصل 8 · وسؤالُ البِركة (§4c) «غيرُ قابلٍ للتحديد» · و30/30 طفرة (`out/gate_audit_mutations.json`).

## 🎯🗂️ قمعُ بِركة التعبئة — رصدٌ أماميّ (2026-10-09 · متابعةُ #599 · «PROSPECTIVE CANDIDATE-POOL CAPTURE»)

**ماذا يُسجَّل الآن:** كلُّ فرزٍ يوميٍّ وكلُّ تجديدٍ أسبوعيّ يُلحق سطرًا واحدًا بـ`fill_pool_log.jsonl` (جذرُ المستودع · يُدفَع مع حالة البوت بـ`git_save` في `run_performance_system` · إلحاقٌ فقط · اتّحادٌ عند تعارض الدفع · حتى 400 صفٍّ للتشغيلة والقصُّ مُعلَنٌ في `rows_cut` · وسطرٌ أيضًا حين لا تعبئة بسببها). لكلّ مؤهَّلٍ مرتَّبٍ صفّ: رتبتُه · `rank_key` · حكمُ السلامة · سببُ الاستثناء (HELD · STOPPED) · جولتُه · نتيجتُه · المتاحُ وحالتُه (KNOWN · UNKNOWN · MALFORMED · NOT_COLLECTED) ومرحلةُ مصدره (الإثراء · الفرصة الثانية) · و«أُضيف» من القائمة المضافة فعلًا. وأثرُ كلّ جولة (`trace`: المختارون · المتاحُ بعد الإثراء وعند البوّابة · المُخرَجون · عدّاداتُ الفرصة الثانية). **صفرُ طلبٍ إضافيّ:** ما لم يُسأل عنه في التشغيلة يبقى NOT_COLLECTED · و`borrow_asof` NOT_COLLECTED (المزوّدُ لا يُعطي طابعًا نحفظه). 🔒 **رصدٌ لا قرار:** `trace=None` ⟵ `fill_picks` بت-بت · و300 عالَمٍ عشوائيّ بالأثر وبدونه متطابقة (المختارون · المُخرَجون · الجولات · نداءاتُ الإثراء والفرصة الثانية) · و`FILL_POOL_LOG=False` يطفئه كلَّه · وانكسارُ أيّ جزءٍ يُبتلَع.

| الملفّ | الدور |
|---|---|
| `Super_stock.py` — `fill_pool_begin` · `_fill_trace_note` · `fill_pool_record` · `record_fill_pool` · `append_fill_pool` · `fill_pool_sha` | اللقطةُ قبل `fill_picks` · الأثر · بناءُ السطر (نقيّة) · الإلحاق · البصمة |
| `pool_funnel.py` | المُقيِّم (قراءةٌ فقط · بلا شبكةٍ ولا استيرادٍ للبوت): يعيد اشتقاقَ نتيجة كلّ صفٍّ من الأثر · ويعيد اختيارَ `select_top` جولةً جولة · ويعيد العدّاداتِ والسبب (NONE · POOL_EXHAUSTED · ROUNDS_CAP · LOOP_ENDED · NO_FILL) · والبصمة · وحالاتُ المهمّة A-F لكلّ صفّ |
| `data/pool_funnel_frozen.jsonl` | نسخٌ مجمَّدةٌ من سطور السجلّ الحيّ (إلحاقٌ بالمفتاح · المحرَّفُ يُرفض) — فارغٌ حتى أوّل تشغيلةٍ مجدولة |
| `data/pool_funnel_legacy.json` | للتشغيلات الثلاث قبل السجلّ: حدٌّ أعلى للمستثنى (held ∪ stopped) من القائمة المدفوعة عند commit الرأس وcommit الحفظ (تاريخ git · بلا طلبٍ خارجيّ) |
| `data/pool_capture_mutations.json` | 26/26 طفرةً سقطت (والجولةُ الأولى نجت منها 3 فأُضيفت PFC20-PFC22) |
| `out/POOL_FUNNEL.json` · `POOL_FUNNEL_REPORT.md` | المخرجان (من المدخلات المجمَّدة وحدَها) |

```bash
python3 faisal_engine/pool_funnel.py --check                         # إعادةُ التوليد والمقارنة — خروج 0
python3 faisal_engine/pool_funnel.py --live fill_pool_log.jsonl      # يقيّم السجلَّ الحيّ ويطبع · لا يكتب
python3 faisal_engine/pool_funnel.py --freeze fill_pool_log.jsonl    # يُلحق غيرَ المجمَّد (بالمفتاح والبصمة) ثمّ أعِد البناء
python3 test_bot.py                                                  # PFC1-PFC22 · PFE1-PFE11 (قبل LEAK0)
```
النتيجة (VERIFIED على السجلّات · EXPLORATORY على المعنى): **السجلّاتُ الأماميّة 0** (يبدأ بأوّل تشغيلةٍ مجدولة بعد الدمج) · والأيّامُ السابقة: 10-07 **غيرُ قابلٍ للتحديد** (حجمُ البِركة لم يُسجَّل) · 10-08 و10-09 **سقفُ الجولات** بحدٍّ أدنى لغير المفحوصين المؤهَّلين 33 و10 · وأسماءُ غير المفحوصين ومتاحُهم NOT_COLLECTED فسؤالُ «هل كانوا يجتازون؟» **باقٍ مفتوحًا** لهم — والسجلُّ الجديد يسمّيهم ولا يجلب متاحَهم (جلبُه طلباتٌ إضافيّة ⟵ قرارُ المالك). 🔒 لا يغيّر الاختيار · وليس دليلًا على أنّ عتبةً ما لفيصل ولا على تعبئةٍ أكثر.
