# 🔬 E2 — مخطّط قياس رادار الانطلاق (Ignition Measurement Schema)
> يوثّق ما يسجّله `ignition_measurement.py` (القياس الظلّي). **E2-A = instrumentation فقط**
> (لا تحليل عتبات). طبقة قياس/بحث — لا يمسّ الفرز/التنبيه/العتبات · لا LOGIC_VERSION.
> المرجع التنفيذي: `E2_IGNITION_IMPLEMENTATION_SPEC` (Codex) · التسجيل المسبق:
> `E2_IGNITION_PREREGISTRATION_2026-07-13.yaml`.

## المبدأ: صفر تكرار لمنطق الرادار
لا نسخة ثانية من `scan_ignition`. القياس يتلقّى **أحداث funnel وصفية** عبر
`scan_ignition(trace=recorder.trace)` — `trace=None` (الافتراضي) = سلوك الرادار حرفيًّا بت-بت.
أي استثناء في القياس يُبتلَع (لا يُسقط الرادار). لا أسرار تُخزَّن.

## الـfunnel (13 حالة)
```
01_SEEN_ACTIVE        سهم نشط وغير مُنبَّه اليوم (poll)
02_LEVEL_AVAILABLE    له break_level (الرقم الحرج أو أرضية×1.05)
03_BARS_FETCH         محاولة جلب شموع الدقيقة (bars_ok/failed + مسار الدقيقة)
04_RAW_IGNITION       اشتعال خام (_ignition_signal: حجم+كسر+صعود) — **يُسجَّل حتى لو كُتم لاحقًا**
05_OPERATOR_MEASURED  قِيس تدفق المضارب (operator_flow) + NBBO
06_OPERATOR_PASS      دخل المضارب → يمرّ
07_OPERATOR_FAIL      لا مضارب → **يُكتَم** (suppress_operator)
08_OPERATOR_UNAVAILABLE  تعذّر قياس المضارب → احتياط تصنيف الشمعة
09_FALLBACK_PASS      شمعة غير-قروب → يمرّ
10_FALLBACK_FAIL      شمعة قروب → **يُكتَم** (suppress_group)
11_ALERT_EMITTED      أُضيف لصفوف التنبيه (scan_ignition)
12/13 (Telegram)      يُسجَّلان من ignition_live: attempt/success/failure
```
**تعريفات دقيقة (لا تُخلَط):**
- **raw ignition** = ناتج `_ignition_signal` دون أي تغيير (04).
- **gated ignition** = اجتاز بوّابة المضارب/الاحتياط (06 أو 09).
- **emitted alert** = أُضيف إلى `rows` (11 · `candidate.alert_emitted=true`).
- **delivered alert** = `send_telegram` بلا استثناء (`deliveries.jsonl` · `telegram_delivered=true`).
  **emitted ≠ delivered.**

## الملفّات (لكل جلسة)
```
e2_measurement/session_YYYY-MM-DD/
  session.json           ← بيانات الجلسة (إنهاء/دورات/union/provenance)
  symbol_sessions.jsonl  ← صف لكل symbol-session (exposure + funnel + coverage)
  candidates.jsonl       ← صف لكل raw candidate فريد (كامل مع التسليم عند finalize)
  deliveries.jsonl       ← سجلّ تسليم Telegram (emitted ≠ delivered)
  minute_paths.jsonl.gz  ← مسار الدقيقة (دِدوب symbol+t) — لتحليل النتيجة لاحقًا
```
**الخام** (`e2_measurement/`) يُرفَع **artifact** (retention 90) — **لا يُدفَع للريبو** (`.gitignore`).
الصغيران القابلان للدفع (العامل الحيّ فقط): `ignition_e2_summary.json` · `ignition_e2_session_index.json`.
**crash-safe:** candidates/deliveries/minute تُلحَق فورًا مع flush · session كل 7 دورات ·
`finalize` في `finally` (يكتب حتى عند exception/timeout).

## schema — session.json  (`schema_version=2`)
`schema_version · session_date · started_at · ended_at · termination(normal|exception|timeout|
cancelled|unknown) · loops_started/completed · symbols_union · n_symbols · n_candidates ·
measurement_enabled · alert_logic_version="unchanged" · source_commit · workflow_run_id · …`
- **🔬 §2a إغلاق الجلسة:** `expected_open_iso · expected_close_iso · deadline_iso · deadline_reason
  (market_close|max_runtime_cap|env_override) · ended_before_expected_close(bool|null) ·
  minutes_short_of_close`. الموعد النهائي للّف = الأبكر من (الإغلاق الفعلي المشتقّ من نيويورك ·
  بدء الجوب + IGNITION_MAX_RUNTIME_MIN · IGNITION_END_UTC الصريح). **قيد سقف رنر GitHub (6س)
  مقابل جلسة 6.5س ⇒ التغطية قد تكون جزئية — تُسجَّل صراحةً بعلم «انتهت قبل الإغلاق» لا تُخفى.**

## schema — symbol_sessions.jsonl (صف لكل symbol-day)  (`schema_version=2`)
`symbol · first_seen_at · last_seen_at · active_polls · level_available_polls · bars_attempted/ok/
failed · raw_candidate_count · operator_pass/fail/unavailable_count · fallback_pass/fail_count ·
emitted_count · delivered_count · first_bar_ts · last_bar_ts · break_level_first/last ·
break_level_source_first · coverage_ratio · exposure_minutes · recall_eligible · backfilled ·
backfill_bars_added`
- `coverage_ratio = bars_ok / max(1, bars_attempted)`.
- **🔬 §2e exposure_minutes** = دقائق (first_seen_at→last_seen_at). **أهلية recall (`recall_eligible`)
  = الشروط الثلاثة معًا** (جودة بيانات لا عتبات تداول): `active_polls≥20 · coverage_ratio≥0.80 ·
  exposure_minutes≥60`.
- **🔬 §2b `backfilled`/`backfill_bars_added`:** بعد التنبيه يتوقّف الرادار عن جلب شموع السهم
  (دِدوب) فيُردَم مسار الدقيقة بعد الجلسة (نافذة يوم كامل) — فلا تُفقَد الحركة اللاحقة لتحليل النتيجة.

## schema — candidates.jsonl (أول raw candidate فريد)  (`schema_version=2`)
مفتاح الدِدوب: `session_date + symbol + trigger_bar_end + break_level`.
`candidate_id · symbol · source_commit · watchlist_commit · break_level · break_level_source ·
pivot · stop · t1/t2/t3 · trigger_bar_start · trigger_bar_end · bar_is_closed · detected_at ·
detected_at_ms · telegram_attempted_at · telegram_sent_at · signal_price · vol_x · signal_usd ·
candle_class · operator_status(pass|fail|unavailable|error) · operator_has_operator ·
operator_bid/buy_block_shares · nbbo_bid/ask/mid · spread_pct_mid · quote_timestamp_raw ·
quote_timestamp · quote_age_ms · primary_executable · fallback_status ·
gate_decision(emit|suppress_operator|suppress_group) · alert_emitted · telegram_delivered ·
decision_latency_ms · delivery_latency_ms`
- **🔬 §2c توقيت الشمعة:** Polygon `t` = **بداية** شمعة الدقيقة. `trigger_bar_start` مسجَّل صراحةً ·
  `trigger_bar_end = trigger_bar_start + 60000` · `bar_is_closed` يُحسم حتميًّا وقت القرار
  (`detected_at_ms ≥ trigger_bar_end`).
- **🔬 §2d عمر NBBO:** `quote_timestamp_raw` كما ورد (نانو/مايكرو/ملّي) · `quote_timestamp` موحّد
  **ملّي-UTC** · `quote_age_ms` = وقت القرار − الطابع. **primary_executable = NBBO صالح
  (ask>0 · ask≥bid · سبريد متاح) ‏و‏ طازج (0 ≤ العمر ≤ 5000ملّي).** مجهول/بائت/مستقبلي = غير تنفيذي
  (يبقى في التغطية/funnel لكن يخرج من تحليل العائد الأولي؛ الثانوي قد يستعمل signal_price بوسم صريح).
- **لا أسرار:** لا مفاتيح/توكن/Authorization/URLs فيها apiKey.

## schema — minute_paths.jsonl.gz
`session_date · symbol · t · o · h · l · c · v` (دِدوب `(symbol, t)`).

## 🔬 إضافات المعمارية المجزّأة (ب+) — مراجعة Codex الثالثة
> `E2_IGNITION_SEGMENTED_ARCH.md`. **قياس فقط · لا LOGIC_VERSION · بت-بت في الإنتاج.**

**المقاطع + الدمج:** كل جوب مقطع (`open`/`close`) يكتب في `session_<date>/segment_<role>/`. الـassembler
(`ignition_e2_assemble.py`) يدمجهما في `session_<date>/` (الجذر) + **backfill بعد الإغلاق** (P0-2).
`session.json` يكتسب: `segment · segment_id · segment_started_at/ended_at · assembled(bool) · segments[]
(provenance المقطعين) · instrumentation_timing (P1.6)`.

**candidate — حقول (ب+) الجديدة:**
- **P1.3 NBBO مزدوج:** `measurement_nbbo_bid/ask/mid · measurement_spread_pct_mid · measurement_quote_ts_raw/
  ms · measurement_quote_age_ms · measurement_executable` (مصدر مستقلّ `polygon_nbbo`) · نظير `operator_*`
  (من operator_flow) · `nbbo_source` (measurement مفضَّل). **primary_executable = مصدر الأساسي** (المرآة).
  **قفل: measurement لا يمسّ قرار التنبيه** (مُحقَن كـ`fetch_measure_nbbo`، بت-بت مؤكَّد باختبار).
- **P1.4 provenance القائمة:** `watchlist_commit_start · watchlist_commit_at_candidate` (يتغيّر مع التحديث).
- **P1.5 latency:** `emitted_at_ms · telegram_attempted_at_ms · telegram_sent_at_ms · decision_latency_ms ·
  delivery_latency_ms`.

**symbol-session — P1.2:** `backfill_status (success|partial|empty|error|not_attempted) · backfill_bars_added
· backfill_last_bar_ts`. **success فقط** عند بلوغ المسار الحدّ المتوقّع قبل الإغلاق.

**تعريف الاكتمال (المدقّق):** `kind = segment|assembled|single`. **`segment_complete`** (إنهاء طبيعي · loops
متوازنة · غطّى نافذته · schema) — لا يدخل البوّابة. **`session_complete`** (الجزآن · union افتتاح→إغلاق ·
**المسارات تصل الإغلاق** `path_last_bar ≥ close_last_bar − 3د` · لا duplicate) — **وحده** يعدّ نحو 5/20.

## حدود E2-A (SPEC §18)
الحكم على: **اكتمال schema · التغطية · عدم فقد البيانات · timestamps · تكافؤ التنبيهات · artifact
recovery** فقط. **ممنوع** تحليل جودة عتبة/نتيجة/expectancy هنا (E2-B عند 20 · E2-C عند 50 + موافقة المالك).
