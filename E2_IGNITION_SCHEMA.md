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

## schema — session.json
`schema_version · session_date · started_at · ended_at · termination(normal|exception|timeout|
cancelled|unknown) · loops_started/completed · symbols_union · n_symbols · n_candidates ·
measurement_enabled · alert_logic_version="unchanged" · source_commit · workflow_run_id · …`

## schema — symbol_sessions.jsonl (صف لكل symbol-day)
`symbol · first_seen_at · last_seen_at · active_polls · level_available_polls · bars_attempted/ok/
failed · raw_candidate_count · operator_pass/fail/unavailable_count · fallback_pass/fail_count ·
emitted_count · delivered_count · first_bar_ts · last_bar_ts · break_level_first/last ·
break_level_source_first · coverage_ratio`
- `coverage_ratio = bars_ok / max(1, bars_attempted)`.
- **أهلية recall** (جودة بيانات لا عتبات تداول): `active_polls≥20 · coverage_ratio≥0.80 ·
  exposure≥60 دقيقة`.

## schema — candidates.jsonl (أول raw candidate فريد)
مفتاح الدِدوب: `session_date + symbol + trigger_bar_end + break_level`.
`candidate_id · symbol · source_commit · watchlist_commit · break_level · break_level_source ·
pivot · stop · t1/t2/t3 · trigger_bar_end · bar_is_closed · detected_at · telegram_attempted_at ·
telegram_sent_at · signal_price · vol_x · signal_usd · candle_class · operator_status(pass|fail|
unavailable|error) · operator_has_operator · operator_bid/buy_block_shares · nbbo_bid/ask/mid ·
spread_pct_mid · quote_timestamp · quote_age_ms · primary_executable · fallback_status ·
gate_decision(emit|suppress_operator|suppress_group) · alert_emitted · telegram_delivered ·
decision_latency_ms · delivery_latency_ms`
- **primary_executable** (§13.1): `ask>0 · ask≥bid · spread متاح` (وإلا الحدث يبقى في التغطية/funnel
  لكن يخرج من تحليل العائد الأولي؛ الثانوي يجوز أن يستعمل signal_price بوسم صريح).
- **لا أسرار:** لا مفاتيح/توكن/Authorization/URLs فيها apiKey.

## schema — minute_paths.jsonl.gz
`session_date · symbol · t · o · h · l · c · v` (دِدوب `(symbol, t)`).

## حدود E2-A (SPEC §18)
الحكم على: **اكتمال schema · التغطية · عدم فقد البيانات · timestamps · تكافؤ التنبيهات · artifact
recovery** فقط. **ممنوع** تحليل جودة عتبة/نتيجة/expectancy هنا (E2-B عند 20 · E2-C عند 50 + موافقة المالك).
