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
**الخلاصة:** الرادار صار تجربة prospective كاملة القياس **دون أن يتغيّر تنبيه واحد**. الخطوة التالية =
تراكم ≥5 جلسات كاملة (E2-A) ثم E2-B الوصفي — بموافقة المالك، لا تطبيق تلقائي.
