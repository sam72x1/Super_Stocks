# تقرير تنفيذ E2-A — القياس الظلّي لرادار الانطلاق
## Super_Stocks · استجابة لـ`E2_IGNITION_MEASUREMENT_IMPLEMENTATION_SPEC_20260713` (Codex)
**التاريخ:** 2026-07-13 · **الطبقة:** قياس/instrumentation فقط · **لا LOGIC_VERSION · لا مسّ جذور · لا معايرة/تحليل عتبات.**

---

### 1. Base commit
`49f3f0d259834e711de710ac9b673c2bbdb42227` (فرع `claude/sharp-bohr-vz31gl`).

### 2. Final commit / branch
فرع مستقل **`claude/e2a-ignition-measurement`** (مشتقّ من 49f3f0d). 4 كوميتات: `539821c` (instrumentation) ·
`1b4d861` (recorder) · `41a831f` (live+workflow+analyze) · `97360ec` (prereg+schema) + كوميت التقرير/التوثيق.

### 3. الملفّات المعدَّلة/الجديدة
| ملف | نوع | السبب |
|---|---|---|
| `Super_stock.py` | معدَّل (+91) | `scan_ignition(trace=None)` + `_emit_trace` (lazy) + `_ignition_break_source` + funnel emit · `polygon_minute_bars` يحفظ `t` (additive) · `operator_flow` يحفظ `quote_ts` (additive) · تصحيح 4 تعليقات overclaim (E2-F09) |
| `ignition_measurement.py` | جديد (439) | `IgnitionMeasurementRecorder`: exposure/funnel/candidate/minute · crash-safe · فاشل-آمن · لا أسرار |
| `ignition_live.py` | معدَّل (+91/−32) | recorder خلف `E2_MEASUREMENT=1` · `trace=_trace` · telegram attempt/success/failure · **try/finally** (finalize) · دفع الصغيرين فقط |
| `.github/workflows/ignition.yml` | معدَّل (+20) | `E2_MEASUREMENT=1` · خطوة بيئة (python -VV + pip freeze) · رفع artifact `if:always` (retention 90) |
| `ignition_e2_analyze.py` | جديد (108) | مدقّق تغطية/اكتمال schema فقط (E2-A §18) — **لا معايرة** |
| `E2_IGNITION_PREREGISTRATION_2026-07-13.yaml` | جديد | تسجيل مسبق prospective (يستبعد GEOS) |
| `E2_IGNITION_SCHEMA.md` | جديد | توثيق funnel/schemas/emitted≠delivered |
| `test_bot.py` | معدَّل (+126) | 22 اختبار E2-A (تكافؤ/funnel/exposure/crash/أقفال) |
| `.gitignore` | معدَّل | `e2_measurement/` (الخام artifact لا للريبو) |

### 4. سبب كل تعديل
كلها لتحويل الرادار من «يرسل تنبيهًا ويسجّل الناجح» إلى «تجربة prospective تسجّل كل مراحل القرار +
التغطية + التنفيذ + التوقيت» **دون تغيير تنبيه واحد** (SPEC §27). التفاصيل بالجدول أعلاه.

### 5. Proof — منطق التنبيه لم يتغيّر (بت-بت)
- `scan_ignition` بلا trace = **مطابق حرفيًّا**: `_emit_trace(None,…)` يرجع فورًا قبل بناء الحمولة (اختبار
  `_emit_trace(None, "X", lambda: 1/0) is None`). التحكّم غير مُمَسّ.
- اختبار تكافؤ: `trace=None` ≡ `trace=collector` (نفس الرموز ونفس الإشارات بت-بت) · استثناء داخل trace
  لا يغيّر المخرجات · **نص Telegram متطابق مع/بدون trace**.
- `ignition_live` مطفأ افتراضيًّا (`E2_MEASUREMENT≠1` ⇒ `trace=None`).
- ثوابت العتبات مقفولة باختبار: `IGNITION_VOL_MULT=3.0 · OPERATOR_MIN_SHARES=1000 · USD 100k/300k` بلا تغيير.

### 6. Proof — LOGIC_VERSION لم يتغيّر
`LOGIC_VERSION = "2026.06.22-redheads.dw+noskip+tranches+4h+keylevels+avgRR"` (بلا تغيير · مقفول باختبار).

### 7. مخرجات الاختبار
`python3 test_bot.py` → **812 نجح · 0 فشل · خروج 0** (منها 22 اختبار E2-A). ⚠️ العدد لا يُقتبس كرقم دائم (§21.7.37).

### 8. مخرجات P0 self-check
`python3 phase_p0_audit.py` → `"status":"PASS" · "fails":[] · OR 8.222…` (لم يتأثّر — E2-A لا يمسّ P0).

### 9. شجرة artifact التجريبية (من الاختبارات + المتوقّع حيًّا)
```
e2_measurement/session_YYYY-MM-DD/
  session.json · symbol_sessions.jsonl · candidates.jsonl · deliveries.jsonl · minute_paths.jsonl.gz
  env_<run_id>.txt (من الworkflow)
```
+ الصغيران (يُدفعان): `ignition_e2_summary.json` · `ignition_e2_session_index.json`.

### 10. أمثلة schema
candidate (مضارب موجود): `signal_price=2.05 · nbbo_mid=2.05 · spread_pct_mid=0.98 · primary_executable=true ·
gate_decision="emit" · alert_emitted=true · telegram_delivered=true · trigger_bar_end=<t>`. symbol-session:
`active_polls · bars_ok/attempted · coverage_ratio · raw/emitted/delivered_count`. (كامل في `E2_IGNITION_SCHEMA.md`.)

### 11. فحص أمني — لا أسرار
اختبار: لا `POLYGON`/`Bearer`/`apiKey`/`TELEGRAM_` في candidates/sessions. المسجّل لا يخزّن مفاتيح/توكن/headers/URLs.

### 12. حدود معروفة (صدق)
- **لم أشغّله حيًّا** (Polygon/Yahoo محجوبان ببيئة التطوير) — التكافؤ مُثبَت بحقن جالبات بلا شبكة؛ أول
  تشغيل Actions يؤكّد التغطية الحيّة.
- **§21.6 (اختبارات النتائج target/stop/opportunity) مؤجَّلة لـE2-B**: E2-A لا يبني مصنّف النتيجة (ممنوع
  تحليل العتبات/النتائج §18) — لا كود لاختباره بعد. مسار الدقيقة يُسجَّل الآن ليُغذّيها لاحقًا.
- **hard-kill (SIGKILL/OOM):** `finally` قد لا يعمل — لكن candidates/deliveries/minute مُلحَقة مع flush
  أثناء الجلسة + artifact `if:always` يلتقط الجزئي.
- **quote_age_ms/decision_latency_ms/bar_is_closed** حقول محجوزة تُملأ عند توفّر توقيت المصدر الحيّ.

### 13. أمر تشغيل الـworkflow (بعد الدمج)
Actions → **Ignition Radar** → Run workflow على `claude/e2a-ignition-measurement` (أو بعد الدمج على main).
يشتغل تلقائيًّا cron 13:35 UTC أيام التداول. القياس مُفعَّل (`E2_MEASUREMENT=1`). يلزم سرّ `POLYGON_API_KEY`.

### 14. ملخّص الـdiff
9 ملفّات · **+1013 / −32** · لا LOGIC_VERSION · لا تغيير عتبة/تنبيه/اختيار · طبقة قياس + توثيق حصريًّا.

### 15. نقاط لم تُنفَّذ (مع السبب)
- تحليل النتائج/الالتقاط/الأبكرية (§14/§15/§16) وحساب expectancy (§19): **مقصود — E2-B/E2-C**، ممنوع في
  E2-A (§18). البنية (candidates + minute_paths + preregistration) جاهزة لتغذيتها.
- معايرة العتبات: **ممنوعة** حتى بوّابة القرار (50 + موافقة المالك).

---

### 16. إصلاحات فجوات مراجعة Codex (§2a–§2e) — بعد المراجعة الثانية على `5708fdeb`
**كلها قياس/instrumentation فقط · لا LOGIC_VERSION · لا تغيير تنبيه/عتبة/اختيار · لا معايرة.** `schema_version`
رُفِع 1→2 (حقول provenance إضافية). 793 اختبار (خروج 0). خُلاصة كل فجوة:

| § | الفجوة | الحل |
|---|---|---|
| **2a** | إنهاء الجلسة كان مثبّتًا `IGNITION_END_UTC=19:20` | أُزيل المثبّت · `_session_window` = الأبكر من (الإغلاق الفعلي المشتقّ من نيويورك · بدء الجوب + `IGNITION_MAX_RUNTIME_MIN`=335 · تجاوز صريح) فيخرج رشيقًا (finalize/ردم) **قبل** حدّ الجوب · `timeout-minutes` 350→355 · session.json يسجّل expected_open/close + deadline_reason + **علم «انتهت قبل الإغلاق المتوقّع»** (`_compute_close_gap`). ⚠️ **قيد بنيوي: سقف رنر GitHub 6س < جلسة 6.5س** فالتغطية جزئية — تُسجَّل صراحةً لا صامتة (قرار المعمارية للمالك/Codex أدناه). |
| **2b** | مسار الدقيقة يتوقّف بعد التنبيه (دِدوب) فتُفقَد الحركة اللاحقة | `backfill_emitted(fetch_bars)` يُكمِّل مسار كل رمز مُنبَّه من الاشتعال حتى نهاية الجلسة (نافذة يوم كامل، fetch محقون فالمسجّل بلا شبكة) بعد اللف · دِدوب (symbol,t) يمنع الازدواج · علم `backfilled`. اختبار: بارات **بعد** لحظة الاشتعال موجودة للرمز المُنبَّه. |
| **2c** | Polygon `t` = **بداية** الشمعة عومل كنهاية | `trigger_bar_start` مسجَّل صراحةً · `trigger_bar_end = start+60000` · `bar_is_closed` حتمي (`detected_at_ms ≥ end`). |
| **2d** | NBBO بلا توحيد طابع/عمر؛ executable بلا طزاجة | `_normalize_ts_ms` (نانو/مايكرو/ملّي/ثوانٍ → ملّي) · `quote_age_ms` وقت القرار · **`primary_executable` = NBBO صالح ‏و‏ طازج (≤5000ملّي)**؛ مجهول/بائت/مستقبلي = غير تنفيذي. اختبارات fresh/stale/missing/future. |
| **2e** | recall بشرطين فقط؛ المدقّق متساهل | `exposure_minutes` حقيقي + **أهلية recall بالشروط الثلاثة** (polls≥20 · cov≥0.80 · exposure≥60د، `_recall_eligible` نقيّة) · **المدقّق يرفض «مكتملة»** عند: إنهاء غير طبيعي · loops_started≠completed · انتهت قبل الإغلاق · فقد مسار ما بعد التنبيه · NBBO غير محسوم لمرشّح مطلوب · تناقض emitted/delivered · نقص حقل توقيت مقفول. |

**🔴 قرار معماري مطروح على المالك/Codex (§2a):** جوب واحد على رنر GitHub مسقوف بـ6 ساعات (360د)، والجلسة النظامية
6.5 ساعة (13:30–20:00 صيفًا / 14:30–21:00 شتاءً). من كرون 13:35 **لا يمكن لجوب واحد بلوغ الإغلاق** (355د من 13:35 =
19:30 < 20:00). الحلّ الحالي يغطّي الافتتاح حتى ~19:10 **ويسجّل النقص صراحةً** (`ended_before_expected_close`) فالمدقّق
يرفض الجلسة كمكتملة. **إن أردنا جلسات «مكتملة» تبلغ الإغلاق فالخيارات: (أ) كرون أبكر/أمتّ للإغلاق يضحّي بالافتتاح · (ب)
جوبان متسلسلان (افتتاح→منتصف، منتصف→إغلاق) · (ج) تعريف «مكتملة» = «شغّلت نافذتها المقصودة بلا انقطاع» لا «بلغت الإغلاق».**
لم أختر صامتًا — سجّلت الحقيقة وطرحت القرار.

---

### 17. المعمارية المجزّأة (ب+) — استجابة مراجعة Codex الثالثة (REQUEST CHANGES على `7e98422`)
Codex قبِل جوهر القياس لكن حجب Pilot الرأس السابق بـ**3 موانع P0** واختار **(ب+): جوبان متسلسلان +
handoff + assembler**. نُفِّذ بالكامل (قياس فقط · لا LOGIC_VERSION · بت-بت في الإنتاج · 801 اختبار).
التفاصيل: `E2_IGNITION_SEGMENTED_ARCH.md`.

**الموانع P0 (حُلّت):**
- **P0-1** `IGNITION_MAX_RUNTIME_MIN` كان من t0 قبل انتظار الافتتاح → لا جلسة تكتمل. الحلّ: `_segment_window`
  يحسب حدود المقطع **من الافتتاح الفعلي** (لا بدء الرنر)، ومقطعان يغطّيان النافذة كاملةً.
- **P0-2** backfill كان يُشغَّل عند نهاية اللف المبكر (بارات ما بعده لم توجد بعد). الحلّ: **الردم النهائي
  في الـassembler بعد الإغلاق** (`ignition_e2_assemble.py`).
- **P0-3** المدقّق كان يقبل بارًا واحدًا بعد الاشتعال. الحلّ: **`path_last_bar ≥ expected_close_last_bar −
  locked_tolerance`** (3د) في `session_complete`.

**المعمارية:** `open_segment` [افتتاح→+195د] → `close_segment` [→إغلاق] (يستعيد أختام الدِدوب من handoff
open → **لا تنبيه Telegram مكرّر**) → `assemble_e2_session` (يدمج · دِدوب bars/candidates/deliveries ·
`min(first_seen)`/`max(last_seen)` · **backfill نهائي بعد الإغلاق** · المدقّق · وحده يكتب summary/index).
`handoff` يحمل: segment_id/timestamps/expected · alerted_symbols · candidate_ids · last_bar_by_symbol ·
symbols_union · loops · **raw_files_sha256** + previous_segment_sha256 (تسلسل).

**تعريف الاكتمال:** `segment_complete` (إنهاء طبيعي · loops متوازنة · غطّى نافذته · schema) — **لا** يدخل
البوّابة. `session_complete` (الجزآن · union افتتاح→إغلاق · handoff · لا duplicate · المسارات تصل الإغلاق ·
فجوة الانتقال مقاسة) — **وحده** يعدّ نحو 5/20. المدقّق يميّز `kind = segment|assembled|single`.

**P1 (كلها نُفِّذت):** **P1.1** حدود من الافتتاح (=P0-1) · **P1.2** `backfill_status` (success **فقط** عند
بلوغ الحدّ · partial/empty/error/not_attempted) + `backfill_last_bar_ts` · **P1.3** **NBBO قياسي مستقلّ**
(`polygon_nbbo`، مُحقَن كـ`fetch_measure_nbbo` — **قفل: لا يمسّ قرار التنبيه**، بت-بت مؤكَّد باختبار) مع
`measurement_nbbo_*`/`operator_nbbo_*`/`nbbo_source` (measurement مفضَّل) · **P1.4** `watchlist_commit_start/
at_candidate/end` (يُحدَّث مع `_fresh_watchlist`) · **P1.5** latency (`emitted_at_ms`/`telegram_*_at_ms`/
`decision_latency_ms`/`delivery_latency_ms`) · **P1.6** أثر الأداة (`instrumentation_timing`: median/p95 لزمن
الدورة + تأخّر الجدولة + نسبة تجاوز interval) · **P1.7** المدقّق يفحص نهاية المسار قرب الإغلاق (=P0-3).

`schema_version` يبقى 2. **الاستثناء الإنتاجي الوحيد المقصود:** استعادة أختام الدِدوب عبر المقطعين (صون
«مرة/سهم/يوم» عبر البنية الجديدة — طبقة توقيت الرادار لا الاختيار؛ مقفول باختبار «لا تكرار»).

**⏳ متبقٍّ:** دفع الفرع + تحديث PR #167 · مراجعة Codex الرابعة على الرأس الجديد · ثم **Pilot واحد** موسوم
`excluded_from_confirmatory=true` (بموافقة Codex + المالك — **لا** على رأسٍ لم يُراجَع).

---

### 18. مراجعة Codex الرابعة (REQUEST CHANGES على `ae0b325`) — 6 موانع P0 + 9 P1 (كلها نُفِّذت)
`schema_version` 2→3 · قياس فقط · **scan_ignition بت-بت في الإنتاج (أُزيل جلب NBBO منه كليًّا)** ·
LOGIC_VERSION بلا تغيير · 815 اختبار · خروج 0. ملفّان جديدان: `ignition_e2_manifest.py` · `market_calendar.py`.

| # | المانع/التحسين | الحلّ |
|---|---|---|
| **P0-1** | جلب NBBO القياسي كان تزامنيًّا في scan_ignition قبل التنبيه (حتى 8ث تأخير) | أُزيل كليًّا من المسار الحرج؛ المسجّل يجلبه **لا-تزامنيًّا** (worker+queue، آمن-خيوط بقفل) ويربطه بـcandidate_id. **اختبار: جالب 1.2ث لا يؤخّر التنبيه (« 400ms).** الصلاحية من طابع المصدر لا انتهاء HTTP. + raw_signal_computed_at_ms/quote_request_started/received/capture_lag_ms |
| **P0-2** | كرون 13:35 يفوّت أول دقائق الصيف (افتتاح 13:30 + تجهيز) | كرون **13:18** (قبل الافتتاح) · انتظار حتى 90د (الشتاء) · `first_successful_poll_at`/`monitoring_started_at` · **بوّابة: أول poll ≤ الافتتاح + start_tolerance(2د)** |
| **P0-3** | فجوة الانتقال بين الجوبين غير مقاسة/مستبعدة | `transition_gap_ms` (open.monitoring_ended→close.monitoring_started) · حدّ مقفول `MAX_TRANSITION_GAP_MIN`=10 · تجاوزه ⇒ session غير مكتملة · **exposure = مجموع فترات المقاطع لا max−min** (لا يخفي الفجوة) |
| **P0-4** | handoff غير متحقّق منه · previous_sha نص لا hash · assembler لا يقرأ handoff | `ignition_e2_manifest.py`: manifest مقفول (canonical JSON + **SHA-256 حقيقي**) + سلسلة تحقّق. **close fail-closed** (يرفض المسح قبله عند فساد) · الassembler يتحقّق من السلسلة. اختبارات عبث (byte/chain/mismatch) |
| **P0-5** | session_complete لا يطبّق التعريف الموثّق | المدقّق (assembled) يحلّل **كل مقطع فعليًّا** (segment_complete) + بدء open + فجوة الانتقال + سلسلة manifest + **تسليم مكرّر** (delivered/symbol ≤1) |
| **P0-6** | فشل المدقّق لا يفشل الـworkflow (`|| true`) | `--strict` (خروج غير صفر عند incomplete) · أُزيل `|| true` من البوّابة · artifact upload يبقى `if:always` |
| **P1-1** | دمج candidate «أول ظهور يفوز» | دمج **field-wise** (`_merge_candidate`): emitted/delivered=OR · emit يفوز suppress · تعارض ثابت→`merge_conflicts` (لا يُسقط emitted) |
| **P1-2** | cadence = interval + scan | جدولة **مطلقة** (`_next_tick += interval`) |
| **P1-3** | latency لا تقيس كامل التأخير | تفكيك bar→raw→gate→attempt→success |
| **P1-4** | provenance القائمة non-null فقط | + **SHA-256 لمحتوى القائمة الفعلي** (`watchlist_file_sha256_at_candidate` — إثبات نفس bytes) |
| **P1-5** | NBBO status لبعض cohorts فقط | resolved **لكل** raw candidate (success/empty/error/timeout/not_requested/not_received) |
| **P1-6** | لا عطلات/إغلاق مبكر | `market_calendar.py` (مثبَّت الإصدار `2026.1`): عطلة⇒لا جلسة · إغلاق مبكر⇒close حقيقي |
| **P1-7** | كل job يدفع legacy log (non-ff) | **المقاطع لا تدفع**؛ الassembler وحده يولّد + يدفع **مرة واحدة بلا `|| true`** على الدفع |
| **P1-8** | provenance المجمَّع مضلِّل | `monitoring_started/ended_at` (النافذة) ≠ `assembled_at` (وقت التجميع) |
| **P1-9** | الحقول الجديدة خارج schema gate | `CAND_REQUIRED`+`EMITTED_REQUIRED`+`SS_REQUIRED` تشمل الجديد |

**⚠️ حدود صدق:** تقويم 2026 مثبَّت الإصدار **يُتحقَّق قبل الـconfirmatory** · لم يُشغَّل حيًّا (Polygon محجوب) ·
**لا Pilot على هذا الرأس قبل مراجعة Codex الخامسة** (قرار Codex).

---
**الخلاصة:** الرادار صار تجربة prospective كاملة القياس **دون أن يتغيّر تنبيه واحد**. الخطوة التالية =
تراكم ≥5 جلسات كاملة (E2-A) ثم E2-B الوصفي — بموافقة المالك، لا تطبيق تلقائي.
