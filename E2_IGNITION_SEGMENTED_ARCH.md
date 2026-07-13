# 🔬 E2 — معمارية الجلسة المجزّأة (ب+): جوبان متسلسلان + handoff + assembler

> **قرار §2a (اختاره Codex في مراجعة PR #167، 2026-07-13):** الجلسة الكاملة (open→close)
> لا تُغطّى بجوب واحد (سقف رنر GitHub 6س < جلسة 6.5س). الحلّ **(ب+)**: جوبان متسلسلان
> يغطّيان النافذة كاملةً + assembler نهائي يدمج ويحكم. **قياس/بحث فقط — لا LOGIC_VERSION ·
> لا تغيير عتبة/تنبيه/اختيار.**
>
> رُفِض **(أ)** [كرون أمتّ يضحّي بالافتتاح — أهم نافذة للأبكرية] و**(ج) كتعريف للجلسة
> confirmatory** [التسجيل المسبق يقفل `regular_hours` حتى الإغلاق · `remaining_gain_to_session_peak`
> · بوّابات 5/20 جلسة]. يجوز تسمية النافذة الجزئية `segment_complete` لكن **لا** تُحتسب
> `session_complete` ولا تدخل بوّابات العيّنة.

## المعمارية — 3 jobs في `ignition.yml`

### `job1: open_segment`
- يبدأ قبل/عند الافتتاح الفعلي (كرون 13:35، ينتظر الجرس).
- **حدود المقطع من الافتتاح الفعلي** (لا من بدء الرنر): `[open, open + IGNITION_SEGMENT_SPLIT_MIN]`.
- يرفع **handoff artifact** + الملفّات الخام للمقطع عند النهاية.

### `job2: close_segment`  (`needs: open_segment`)
- ينزّل handoff الخاص بـjob1.
- **يستعيد:** candidates · alerted_symbols · symbol counters · آخر timestamps · **أختام
  الدِدوب في الذاكرة** (`ignition_alert`) لمنع **إعادة إرسال التنبيهات** (صون إنتاجي — لا تنبيه
  مكرّر للمستخدم عبر المقطعين).
- يكمل حتى **إغلاق نيويورك الفعلي** (`[handoff_start, close]`).
- يرفع handoff الخاص به + الخام.

### `job3: assemble_e2_session`  (`needs: close_segment`)
- يدمج الجزأين · يدِدوب البارات على `(symbol,t)` · candidates على `candidate_id` · deliveries.
- يجمع symbol-session counters مع `min(first_seen)` و`max(last_seen)`.
- ينفّذ **backfill النهائي بعد الإغلاق** (المسار حتى الإغلاق — P0-2).
- يشغّل المدقّق · **وحده** يكتب `summary/index` النهائيين.

## Handoff (يُحفَظ عند نهاية كل مقطع)
`schema_version · session_date · segment_id · segment_started_at · segment_ended_at ·
expected_segment_start/end · source_commit · watchlist_commit_start/end · workflow_run_id ·
alerted_symbols · candidate_ids · last_bar_by_symbol · symbols_union · loops_started/completed ·
raw_files_sha256 · previous_segment_sha256`.

## تعريف الاكتمال (يُطبِّقه المدقّق)

### `segment_complete`
- إنهاء طبيعي · loops متوازنة (started == completed) · **غطّى نافذته المقصودة** · schema سليم.

### `session_complete`  (وحده يدخل بوّابات 5/20)
- **الجزآن مكتملان** · union يمتد **من الافتتاح إلى الإغلاق** · handoff سليم · **لا duplicate
  Telegram** · **المسارات تصل للإغلاق** (`path_last_bar ≥ expected_close_last_bar − locked_tolerance`)
  · **فجوة الانتقال مقاسة ومقفولة مسبقًا** · أي فرصة وقعت داخل فجوة غير مراقبة **لا تدخل recall
  denominator**.

## 🔒 ضوابط
- كل ما سبق **قياس/instrumentation فقط**: لا `LOGIC_VERSION` · لا تغيير نص تنبيه/عتبة/اختيار ·
  لا معايرة. طبقة القياس خارج `rank_key`/`select_top`/`classify_tier`/`entry_status`.
- **الاستثناء الإنتاجي الوحيد المقصود:** استعادة أختام الدِدوب عبر المقطعين لمنع تنبيه مكرّر
  (صون سلوك «مرة/سهم/يوم» عبر البنية الجديدة — ضمن طبقة توقيت الرادار، لا الاختيار).
- **لا Pilot على رأسٍ لا يستطيع إنتاج جلسة مكتملة** (قرار Codex): يُشغَّل Pilot واحد موسوم
  `excluded_from_confirmatory=true` **فقط بعد** اكتمال البناء + مراجعة Codex النظيفة + موافقة المالك.
