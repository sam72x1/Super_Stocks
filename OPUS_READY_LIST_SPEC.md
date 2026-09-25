# OPUS EXECUTION SPECIFICATION — `OPUS_READY_LIST_SPEC` (حزمةُ T-OPLINK · 2026-09-25)

> **مصدرُ الحزمة:** `opentry_link_result.md` (الحاكمة `36125202136`) على العقد `opentry_link_prereg.md`.
> **الأمرُ الذي يُشغّلها:** «نفذ OPUS_READY_LIST_SPEC.md» من المالك — **وقبله صفرُ كود.**
> ⚖️ **الحكمُ الذي تُبنى عليه: الفرعُ 2 «لا رابط» للأساسيّات** ⇒ هذه الحزمةُ **لا تُعيد برمجة قائمة «الجاهز» على RSI/الفلوت/المتاح** — لأن ذلك يكون شحنَ ميزاتٍ سقطت بقياسها (خطُّ المالك: «لا يُرخى معيارٌ بعد رؤية رقم»). ما تُشحنه: **قائمةٌ ظلّيّة تُقاس أماميًّا خلف مفتاحٍ مطفأ** وسطرُ عرضٍ اختياريّ.

## 1. OBJECTIVE
بناءُ **قائمة «جاهز» ظلّيّة** (`shadow ready`) من الميزات **العابرة وحدَها** في `T-OPLINK` (مرساةُ سيولةٍ في **البريماركت** · `J1` · `gap≥30%`)، تُقارَن **يوميًّا وصامتًا** بقائمة «الجاهز» الحيّة على المراسي (كم انفجارًا تلتقط · وكم ضجيجًا تضيف)، **خلف مفتاحٍ مطفأ يُرجع الإنتاجَ بت-بت** — بلا بوّابةٍ ولا عتبةٍ جديدة ولا مسٍّ بالجذور.

## 2. SOURCE MATERIAL
- `opentry_link_result.md` §②-§⑧ (‏711 مرساة · الأساس 13.2% · الشاهد 0.0% · فرضيّاتُ المالك لا تفصل · البريماركت 24.4% · `J1` 27.3% · `gap≥30%` 29.8% · `J1∧pre` 37.3% · عضويّةُ «الجاهز» 5.3% · SXTC مرفوضٌ بـ`M2_هبوط_فوق_97`).
- `tierlink_result.md` (الرابطُ نفسُه على 321 مرساة · 2026-09-02) · `tier_v3`/`strong2` (تعريفُ «قوي» الحيّ).
- برومبتُ المالك `OPENTRY_LINK_PROMPT.md §①` ⑥-4.

## 3. MASTER KNOWLEDGE BASE
| ID | SOURCE | TYPE | CONTENT | INTERPRETATION | IMPORTANCE | EVIDENCE | RELATED_ITEMS | IMPLEMENTATION_IMPACT | CONFIDENCE |
|---|---|---|---|---|---|---|---|---|---|
| KB-01 | result §③ | Data | RSI<30 · فلوت<4م · متاح<20k لا تفصل (‏1.3× · 1.2× · لا قياس) | فرضيّةُ المالك للأساسيّات ساقطة على المراسي | عالية | `36125202136` §③ | KB-04 | **لا تُشحَن عتبةٌ منها** | CONFIRMED |
| KB-02 | result §④ | Data | البريماركت 24.4% مقابل 8.0% · `J1` 27.3% · `gap≥30%` 29.8% · `J1∧pre` 37.3% | ما يفصل = توقيتُ المرساة وشكلُها | عالية | §④ · وT-TIERLINK بت-بت | KB-05 | أساسُ القائمة الظلّيّة | CONFIRMED |
| KB-03 | result §② | Data | الشاهدُ العشوائيّ 0.0% مقابل 24.1% للمراسي (`expl50_daily`) | المرساةُ نفسُها إشارة | عالية | §② | KB-02 | القائمةُ الظلّيّة = مراسٍ لا مرشّحو فرز | CONFIRMED |
| KB-04 | result §⑤ | Data | عضويّةُ «الجاهز» 5.3% من المراسي · 2.1% من المنفجرين · الرفضُ M4 249 · المستوى المُختبَر 215 | الفارزُ والمرساةُ منتجان مختلفان بالتصميم | عالية | §⑤ | KB-01 | لا دمجَ بالاختيار (سابقةُ `T-RANKER3`/`C3`) | STRONGLY_SUPPORTED |
| KB-05 | result §④ ملاحظة 1 | Pattern | القاعدةُ الضيّقة (<40%) تنفجر 4.1% مقابل 16.4% للواسعة | اتّجاهٌ معاكس لبوّابة M4 — على المراسي | متوسّطة | §④ | KB-04 | **وصفيّ** — لا يُشحَن (سلّةٌ دنيا خارج المعيار) | LIKELY |
| KB-06 | result §⑥ | Example | SXTC: RSI 23 · هبوط >99.95% · قاعدة 147-169% ⇒ M2 ثمّ M4 | فيصل دخل على حركةِ سيولة لا من قاعٍ ضيّق | متوسّطة | §⑥ | KB-04 | مثالٌ لا قاعدة | CONFIRMED |
| KB-07 | result §⑨ | Constraint | المتاحُ المؤرَّخ 39 من 711 | فرضيّةُ المتاح لم تُقَس فعلًا | عالية | §② | KB-01 | حصّادٌ أماميّ يخزّن المتاحَ يومَ المرساة (اختياريّ · R-03) | CONFIRMED |

## 4. VERIFIED FACTS
- V1 لا ميزةَ أساسيّاتٍ تفصل بالمعيار الرباعيّ (‏§③-§④).
- V2 `tod=pre` · `J1` · `gap≥30%` تعبر 1-4؛ و`tod=pre` تضيف خارج `J1∧pre` (‏§④).
- V3 الشاهد 0/682 (‏§②) · V4 شاهدُ الهُويّة 33/321 بت-بت (‏§①).
- V5 «قُبل» 10 من 673 غيرِ عضو — أي 10 مراسٍ اجتازت الهويّة ولم تُدرَج (سعة/ترتيب) (‏§⑤).

## 5. DERIVED RULES — بوسمها
- DR-1 (GENERAL RULE · CONFIRMED): **لا تُبنى «الجاهز» على RSI/الفلوت/المتاح.**
- DR-2 (POSSIBLE RULE · STRONGLY_SUPPORTED): مرساةُ سيولةٍ في البريماركت (‏+ `J1` أو `gap≥30%`) هي أقوى مرشِّحٍ للانفجار في يومها — **قيدُ الإثبات الأماميّ**.
- DR-3 (EXAMPLE): SXTC — لا يُعمَّم.
- DR-4 (UNKNOWN): أثرُ المتاح للاقتراض — بلا قياس.

## 6. PATTERNS
- P-1 المنفجرُ في مجتمع المراسي يأتي من القاعدة الواسعة وسعرٍ دون 1$ وتقسيمٍ عمرُه 31-120 يومًا — **اتّجاهاتٌ لا روابط** (كلُّها دون 2×).
- P-2 الأعضاءُ ينفجرون أقلّ (‏5.3%) — n=38.

## 7. CONSTRAINTS
- C-1 الجذورُ الاثنا عشر بت-بت (بصمةُ `ast.dump` كما في `faisal-gates §④`) · لا `LOGIC_VERSION`.
- C-2 المفتاحُ `SHADOW_READY` افتراضُه `""` (مطفأ) ⇒ الإنتاجُ بت-بت · و`"1"` يُفعّل **القياسَ الصامت وسطرَ العرض فقط** — لا إرسالَ تلغرام جديدًا (خطٌّ أحمر).
- C-3 لا عتبةَ جديدة: `IGNITION_USD_OPERATOR` و`tier_of`/`liq_tier` و`gap` **بأسمائها** كما هي.
- C-4 لا محورَ مُغلَقٌ يُفتح (`T-RSI40` · `T-RANKER3`).

## 8. EDGE CASES
- E-1 يومٌ بلا مراسي بريماركت ⇒ القائمةُ الظلّيّة فارغة **وتُسجَّل فارغة** (لا تخمين).
- E-2 مرساةٌ لرمزٍ هو عضوٌ في «الجاهز» ⇒ تُحسب في الطرفين (تقاطعٌ يُطبَع).
- E-3 إعادةُ رسوٍّ بعد الكتم ⇒ مرساةٌ واحدة بمفتاح (يوم · رمز) — كما في `liq_trig_read`.
- E-4 غيابُ `op_entry_state.json` أو المفتاح ⇒ لا عمل، لا انهيار.

## 9. IMPLEMENTATION REQUIREMENTS
- **R-00 (إلزاميّ):** لا تغييرَ على `analyze_ticker`/`rank_key`/`select_top`/البوّابات. يُكتب سطرٌ مؤرَّخ في `CLAUDE.md` أن «إعادة بناء الجاهز على الأساسيّات» **مقيسةٌ وساقطة** (`T-OPLINK`).
  - 🔄 **سندٌ ثانٍ (‏2026-09-25 · `T-PRELINK` ‏+ §⑩ «فوق الدولار»):** الشروطُ نفسُها على الانفجار **المتأخّر** (1-10 جلسات) وعلى الأسهم فوق الدولار وحدَها ⟵ الفرعُ 2 مرّتين (`prelink_result.md` §③ و§⑧): RSI أقلّ من 30 ‏1.4-2.1× ويسقط على ⑤ · والفلوتُ أقلّ من 4م في ‏80% من المراسي فلا يفرّق · والمتاحُ بلا تاريخ ⇒ **R-00 قائمٌ** ولا يُقترح بلا محورٍ جديدٍ وعقد.
- **R-01 قائمةٌ ظلّيّة مقيسة:** `shadow_ready.py` (قراءةٌ فقط · بالاسم من `tierlink_probe.anchor_history` و`measure` و`tier_fwd_report.tier_of`) يُخرج يوميًّا (بعد الإغلاق) صفوفَ «الظلّيّة» = مراسي اليوم التي `tod=pre` ∧ (`J1` ∨ `gap≥30%`)، ونتيجتَها `exploded50`، ويقارنها بأعضاء «الجاهز» يومَها (لقطةُ git) — **يُلحق سطرًا في `shadow_ready_ledger.jsonl`** (حصادٌ لا حالةُ إنتاج) خلف `SHADOW_READY == "1"`. **بُنيت لـ…:** `anchor_history` بُنيت لقراءة المراسي من تاريخ git (T-TIERLINK) — الاستعمالُ هنا مطابق؛ `measure` بُنيت لأساس سعر كرت `M5` — مطابق؛ `tier_of` بُنيت لإعادة اشتقاق الفئة من المكوّنات المخزَّنة — مطابق.
- **R-02 سطرُ عرضٍ اختياريّ:** في `build_live_alert` (`Super_stock.py:17149` (`build_live_alert`)) سطرٌ واحد «🌅 مرساةٌ في البريماركت — الأعلى انفجارًا في `T-OPLINK` (‏24% مقابل 8%)» عند `tod=pre`، خلف `SHADOW_READY` — **عرضٌ فقط**، ولا يغيّر شرطَ الإرسال ولا الدِدوب.
- **R-03 (اختياريّ · يفتح فرضيّةَ المتاح):** حصّادُ المتاح يومَ المرساة: عند كلّ مرساةٍ جديدة يُخزَّن `shares_available` من `ce_borrow_info` بالاسم في `shadow_ready_ledger.jsonl` (قناةٌ قائمة · بلا نداءٍ جديد على الفرز) — فتصير فرضيّةُ «متاح<20k» قابلةً للقياس بعد ‏≥100 مرساة.

## 10. SYSTEM ARCHITECTURE
`shadow_ready.py` (وحدةٌ مستقلّة · لا يستوردها الإنتاج) ⟵ `shadow_ready.yml` (كرونٌ **لا** — يدويٌّ أوّلًا؛ الكرونُ بعد أوّل تشغيلتين ناجحتين وبأمرٍ منفصل) ⟵ `shadow_ready_ledger.jsonl` (يُدفَع بـ`git_save` القائم كما `tier_fwd_ledger`). سطرُ العرض في `build_live_alert` وحدَه.

## 11. ALGORITHMS / LOGIC
1. مراسي اليوم من `anchor_history(since=اليوم)` ⟵ 2. لكلٍّ: `tod` من `anchor_ms` بساعة نيويورك · `J1` من `k2` · `gap` من `anchor_price/prev_close` (كما في `tierlink_probe.features`) ⟵ 3. `shadow = tod=="pre" and (j1 or gap>=30)` ⟵ 4. `exploded50` من `measure` ⟵ 5. `member` من لقطة `weekly_watchlist.json` يومَها ⟵ 6. صفٌّ للسجلّ + عدّاداتٌ يوميّة (ظلّيّة/جاهز/تقاطع/منفجر في كلٍّ).

## 12. INPUTS
`op_entry_state.json` (تاريخ git) · `tier_fwd_ledger.jsonl` · `weekly_watchlist.json` · شموعُ Polygon (`fetch_day` · `daily_range`) · `POLYGON_API_KEY` · مفتاح `SHADOW_READY`.

## 13. OUTPUTS
`shadow_ready_ledger.jsonl` (صفٌّ لكلّ مرساة: يوم · رمز · shadow · member · exploded50 · tod · j1 · gap · avail_today) · سطرُ ملخّصٍ يوميّ في سجلّ التشغيلة · (اختياريًّا) سطرُ عرضٍ في تنبيه السيولة.

## 14. VALIDATION
- بصماتُ الجذور الاثني عشر مطابقةٌ لـ`origin/main` قبل وبعد.
- `SHADOW_READY=""` ⇒ `build_live_alert` بت-بت على 20 صفًّا مصنوعًا · و`shadow_ready.py` بلا مفتاح ⇒ خروج 2 · بلا مراسي ⇒ سجلٌّ فارغ لا انهيار.
- شاهدُ الهُويّة: على 08-18⟶09-01 يُعيد `exploded50` 33/321.

## 15. TEST PLAN
أقفال `SHR1`-`SHR6` قبل فاصل `LEAK0`: قراءةٌ فقط (AST) · المفتاحُ المطفأ بت-بت · `shadow` نقيّة على صفوفٍ مصنوعة (pre∧J1 ✅ · pre بلا J1 وgap 29% ❌ · reg∧J1 ❌) · لا لقطةَ لاحقة · workflow بلا كرون · سطرُ العرض يظهر مع المفتاح ويغيب بدونه (قفلٌ فارق لا «أو»). **كلُّ قفلٍ تُسقطه طفرة** (`lock-and-mutate`).

## 16. FAILURE CONDITIONS
أيُّ جذرٍ تغيّرت بصمتُه · أيُّ رسالةِ تلغرام جديدة · عتبةٌ رقميّة جديدة بلا سطر «مِجَسّ:» ووسمٍ في الدفتر · السويّةُ غيرُ صفر · CI أحمر على الـPR أو main.

## 17. UNCERTAINTIES
- U-1 هل «الظلّيّة» تُسلِّم شيئًا **فوق** ما يُرسله المراقبُ الحيّ اليوم (`PRESESSION_SEND: PM,AH` + `tier` قوي)؟ — **غالبًا لا** (نفسُ الميزات) ⇒ قيمتُها **قياسٌ مقارِن** لا تنبيهٌ جديد.
- U-2 الربحيّةُ الفعليّة للمراسي سالبة في `T-OPTRADE` (‏−0.70R) ⇒ «ينفجر» ≠ «يربح».
- U-3 المتاحُ بلا تاريخ (R-03 يعالجه أماميًّا).

## 18. IMPLEMENTATION ORDER
### PHASE 0 — Repository Inspection
- OBJECTIVE: تثبيتُ `origin/main` وبصمات الجذور. FILES: `Super_stock.py` · `tierlink_probe.py` · `tier_fwd_report.py`. CHANGES: لا شيء. DEPENDENCIES: —. TESTS: بصمةُ `ast.dump`. EXPECTED RESULT: 12 بصمة مسجَّلة. FAILURE CONDITIONS: شجرةٌ غيرُ نظيفة.
### PHASE 1 — Understand Existing Architecture
- OBJECTIVE: قراءةُ `anchor_history`/`measure`/`tier_of`/`build_live_alert`. FILES: كما أعلاه. CHANGES: لا شيء. DEPENDENCIES: PHASE 0. TESTS: —. EXPECTED RESULT: «بُنيت لـ…» لكلّ دالّةٍ تُعاد. FAILURE CONDITIONS: دالّةٌ نظامُها مختلف (سابقةُ `trigger_state`).
### PHASE 2 — Map Requirements to Existing System
- OBJECTIVE: R-01/R-02/R-03 ⟵ مواضعُها. FILES: `Super_stock.py:17149` (`build_live_alert`). CHANGES: لا شيء. DEPENDENCIES: PHASE 1. TESTS: —. EXPECTED RESULT: جدولُ SOURCE→REQUIREMENT→IMPLEMENTATION→TEST. FAILURE CONDITIONS: متطلَّبٌ يمسّ جذرًا.
### PHASE 3 — Identify Gaps
- OBJECTIVE: ما ليس موجودًا: السجلُّ الظلّيّ · حصّادُ المتاح. FILES: —. CHANGES: لا شيء. DEPENDENCIES: PHASE 2. TESTS: —. EXPECTED RESULT: قائمةُ الجديد الصافي. FAILURE CONDITIONS: إعادةُ بناء موجود.
### PHASE 4 — Implement
- OBJECTIVE: `shadow_ready.py` + `shadow_ready.yml` + مفتاح `SHADOW_READY` + سطرُ العرض. FILES: جديدان + `Super_stock.py` (سطرٌ واحد في `build_live_alert`). CHANGES: كما R-01/R-02/R-03. DEPENDENCIES: PHASE 3. TESTS: `SHR1`-`SHR6`. EXPECTED RESULT: السويّة 0 · الجذورُ بت-بت. FAILURE CONDITIONS: أيُّ بصمةٍ تتغيّر.
### PHASE 5 — Test
- OBJECTIVE: جولةُ طفرات. FILES: `test_bot.py`. CHANGES: أقفالٌ فقط. DEPENDENCIES: PHASE 4. TESTS: طفرةٌ لكلّ قفل. EXPECTED RESULT: كلُّ طفرةٍ تسقط بقفلها. FAILURE CONDITIONS: طفرةٌ تنجو أو تنهار.
### PHASE 6 — Validate Against Source Requirements
- OBJECTIVE: شاهدُ الهُويّة 33/321 · المفتاحُ المطفأ بت-بت. FILES: —. CHANGES: لا شيء. DEPENDENCIES: PHASE 5. TESTS: §14. EXPECTED RESULT: كلُّها ✅. FAILURE CONDITIONS: انحرافٌ عن المنشور.
### PHASE 7 — Review for Regression
- OBJECTIVE: `grep` مستهلكي الدوالّ المُعادة. FILES: كلُّ `*.py`. CHANGES: لا شيء. DEPENDENCIES: PHASE 6. TESTS: السويّة الكاملة. EXPECTED RESULT: 0 فشل. FAILURE CONDITIONS: أيُّ فشل.
### PHASE 8 — Final Report
- OBJECTIVE: تقريرٌ بصيغة ⑤ + ذاكرة. FILES: `CLAUDE.md` · `HANDOFF.md` · الأرشيفان. CHANGES: سطورٌ مؤرَّخة. DEPENDENCIES: PHASE 7. TESTS: `MEM5`/`HND5`. EXPECTED RESULT: PR مدموج وCI أخضر على main. FAILURE CONDITIONS: CI أحمر.

## 19. DO NOT
- لا تُغيّر `RSI_MAX_NOW`/`FLOAT_GATE_MAX`/`BORROW_AVAIL_MAX` ولا أيَّ عتبةٍ على أساس هذي النتيجة.
- لا تُدخل المراسي في `select_top` (سابقةُ `T-RANKER3`/`C3`).
- لا رسالةَ تلغرام جديدة ولا كرون قبل أمرٍ منفصل.
- لا تفتح `T-RSI40` (‏`CLOSED_RC`).

## 20. FINAL ACCEPTANCE CRITERIA
- الجذورُ بت-بت · السويّة 0 · طفراتٌ تسقط كلُّها · CI أخضر على الـPR وmain من السجلّ · المفتاحُ مطفأٌ افتراضًا · وأوّلُ تشغيلةٍ يدويّة لـ`shadow_ready.yml` تُخرج صفوفًا بصفر انهيار — **ولا يُستنتَج من الحزمة أن «الجاهز» أُعيد بناؤه: لم يُعَد، بالدليل.**

---
## ملحقٌ تنفيذيّ — 2026-09-25 (أمرُ المالك: اسمُ الحزمة بعد التحويل = «نفذ»)
- **نُفِّذ:** R-00 (سطرٌ مؤرَّخ في `CLAUDE.md`) · R-01 (`shadow_ready.py` ‏+ `shadow_ready.yml` يدويّ) · R-03 (حارسُ جلسة المتاح) · وعقدٌ أماميّ `shadow_ready_prereg.md` قبل أيّ رقم (الحزمةُ بلا معيار حكم — قاعدةُ المشروع ② أعلى).
- **لم يُنفَّذ R-02 — تناقضٌ بين الحزمة والكود:** `Super_stock.py:17149` (`build_live_alert`) تنبيهُ أحداث المراقب («🚨 أحداث لحظية»، `pullback_live.py`) لا كرتَ «هنا الدخول»؛ الكرتُ `Super_stock.py:15879` (`build_liq_stage_alert`، `operator_entry_live.py`) وفيه سلفًا «🌅 J1 في البريماركت» (`Super_stock.py:15775` (`j1_premarket_flag`)). والحلُّ الأقلُّ خطرًا: لا سطرَ في تنبيهٍ حيّ (خطٌّ أحمر) ⇒ الشارةُ العامّة صارت اقتراحَ الفرع 1 من العقد بأمر المالك.
- **الانحرافاتُ الستّة** (`D-1`…`D-6`) مفصّلةٌ في `shadow_ready_prereg.md §⓪`. والجذورُ الاثنا عشر بت-بت (لا مسَّ لـ`Super_stock.py`).
