#!/usr/bin/env python3
"""🔬 E2-A — مدقّق تغطية/اكتمال القياس الظلّي (لا معايرة · لا حكم عتبات).

**E2-A حصريًّا (SPEC §18):** يقرأ مخرجات `ignition_measurement` ويتحقّق من: اكتمال الـschema ·
التغطية · عدم فقد البيانات · التوقيت · funnel متّسق · تكافؤ التنبيهات · استرداد artifact. **ممنوع**
هنا أي تحليل جودة عتبة/نتيجة/expectancy (ذلك E2-B/E2-C بعد اكتمال العيّنة + تسجيل مسبق + موافقة
المالك). قياس/تدقيق فقط · لا يمسّ الفرز.

🔬 **تشديد مراجعة Codex (§2e):** الجلسة **لا تُعدّ مكتملة** إن: انتهت قبل الإغلاق المتوقّع ·
loops_started ≠ loops_completed · فُقِد مسار ما بعد التنبيه لرمز مُنبَّه · NBBO غير محسوم لمرشّح
مطلوب · تناقض emitted/delivered · نقص حقل توقيت مقفول.

تشغيل:  python3 ignition_e2_analyze.py [e2_measurement]
"""
import gzip
import json
import os
import sys

# 🔬 P1-9: حقول candidate المقفولة (توقيت §2c/§2d + مراجعة Codex 4) — نقصها = schema-gap.
CAND_REQUIRED = ["candidate_id", "symbol", "session_date", "break_level",
                 "trigger_bar_start", "trigger_bar_end", "bar_is_closed",
                 "detected_at", "detected_at_ms", "raw_signal_computed_at_ms",
                 "signal_price", "gate_decision", "alert_emitted",
                 "measurement_nbbo_status", "watchlist_commit_at_candidate"]
# حقول إضافية مطلوبة **للمرشّح المُصدَر** فقط (latency + توقيت التسليم).
EMITTED_REQUIRED = ["emitted_at_ms", "telegram_attempted_at_ms", "bar_end_to_raw_signal_ms"]
# 🔬 P0-3/P1.7: سماحية «وصول المسار للإغلاق» + هامش «تغطية النافذة».
CLOSE_PATH_TOLERANCE_MS = 3 * 60_000
WINDOW_MARGIN_MIN = 10
SS_REQUIRED = ["symbol", "active_polls", "bars_attempted", "bars_ok", "coverage_ratio",
               "first_seen_at", "last_seen_at", "raw_candidate_count", "emitted_count",
               "exposure_minutes", "recall_eligible", "backfill_status"]
# حدود جودة البيانات لأهلية recall (SPEC §7) — **ليست عتبات تداول** (الثلاثة تُطبَّق في المسجّل).
RECALL_MIN_POLLS, RECALL_MIN_COVERAGE, RECALL_MIN_EXPOSURE_MIN = 20, 0.80, 60
# 🔬 (2026-09-24) «لماذا لا يُنفَّذ NBBO؟» وعدّادُ بوّابة E2-B — **قراءةٌ فقط**: لا يمسّ الاكتمالَ ولا
#    تعريفَ «قابل للتنفيذ» (يصف ما سجّله القياسُ وقتَها). الرقمان **مرآةُ التسجيل المسبق** بحرفهما
#    (`entry.max_quote_age_seconds` = 5 · `sample_gates.preliminary.decided_alerts` = 20) — قفل E2N3.
MAX_QUOTE_AGE_MS = 5_000
E2B_MIN_DECIDED_ALERTS = 20
# 🔬 (2026-09-25) عدّا E2-B **يُحفظان في الفهرس** مع الحكم (`verdict_entry`) — كانا يُحسبان ويُطبعان
#    ولا يُحفظان، فلا يُعاد العدّادُ التراكميّ إلّا من artifacts احتفاظُها 90 يومًا.
E2B_INDEX_KEYS = ("n_executable", "n_executable_emitted")


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def nbbo_age_breakdown(cands):
    """🔬 نقيّة: تصنيفُ NBBO الأساسيّ لكلّ candidate — `executable` (كما سُجِّل) · `stale` (العمرُ فوق
    5ث) · `future` (عمرٌ سالب = طابعُ الاقتباس أحدثُ من ساعة الرنر) · `invalid` (العمرُ داخل النافذة
    والـNBBO غيرُ صالح) · `missing` (بلا عمر) — مع وسيطِ عمرِ البائت وأدنى عمرٍ سالب (ملّي).
    **يصف ولا يُعيد تعريف «قابل للتنفيذ»** — المرجعُ `primary_executable` المسجَّل."""
    out = {"executable": 0, "stale": 0, "future": 0, "invalid": 0, "missing": 0}
    stale_ages, neg_ages = [], []
    for c in cands or []:
        age = _num(c.get("quote_age_ms"))
        if c.get("primary_executable") is True:
            out["executable"] += 1
        elif age is None:
            out["missing"] += 1
        elif age < 0:
            out["future"] += 1
            neg_ages.append(age)
        elif age > MAX_QUOTE_AGE_MS:
            out["stale"] += 1
            stale_ages.append(age)
        else:
            out["invalid"] += 1
    stale_ages.sort()
    out["stale_median_ms"] = int(stale_ages[len(stale_ages) // 2]) if stale_ages else None
    out["future_min_ms"] = int(min(neg_ages)) if neg_ages else None
    return out


def e2b_gate_count(results):
    """🔬 نقيّة: تنبيهاتٌ **مُصدَرةٌ بـNBBO قابلٍ للتنفيذ في جلساتٍ مكتملة** — حدٌّ أعلى لـ«المحسوم»
    في بوّابة E2-B (المحسومُ يلزمه فوق هذا مصيرُ خمس جلسات). الجلسةُ غيرُ المكتملة لا تُعَدّ."""
    return sum(int(r.get("n_executable_emitted") or 0) for r in results or []
               if isinstance(r, dict) and r.get("session_complete") is True)


def e2b_count_from_index(idx):
    """🔬 نقيّة (2026-09-25): عدّادُ بوّابة E2-B **التراكميّ من الفهرس** — كلُّ الجلسات المكتملة، لا
    ما في مجلّد التشغيلة وحدَه (الـassembler يرى جلسةً واحدة والاسترجاعُ الليليّ آخرَ ~15 تشغيلة ⇒
    طُبع ‏11/20 على 47 جلسة ثمّ ‏2/20 على 4). ترجّع `(العدد، المكتملة، منها بعدٍّ محفوظ)` — والمكتملةُ
    بلا عدٍّ **تُعلَن ولا تُعَدّ صفرًا** (فالرقمُ حدٌّ أدنى حتى تُستكمَل). والعدُّ `e2b_gate_count` نفسُه."""
    rows = [v for v in (idx.values() if isinstance(idx, dict) else ())
            if isinstance(v, dict) and v.get("session_complete") is True]
    have = [v for v in rows if isinstance(v.get("n_executable_emitted"), int)
            and not isinstance(v.get("n_executable_emitted"), bool)]
    return e2b_gate_count(have), len(rows), len(have)

# 🔴 **أسبابٌ مؤجَّلةٌ بالتصميم إلى الـassembler** (إصلاح 2026-08-06 — عطلٌ مقيس):
#
# `lost_post_alert_path` يشترط بارَ دقيقةٍ **بعد** شمعة الزناد داخل ملفّات المقطع نفسه.
# وهذا **مستحيلٌ بنيويًّا** في الإنتاج: دِدوب الرادار (`Super_stock.py:11554` —
# `if s.get("ignition_alert") == today_iso: continue`) يقع **قبل** `fb(s["symbol"])`،
# فبعد أوّل تنبيهٍ لرمزٍ لا يُجلَب له بارٌ آخر ذلك اليوم ⇒ لا بارَ بعد الزناد في المقطع.
# وهذا **سببُ وجود `backfill_emitted`** حرفيًّا بنصّ docstring‌ها: «الرادار يتوقّف عن جلب
# شموع السهم بعد التنبيه (دِدوب) فتُفقَد الحركة اللاحقة» — و`P0-2` يفرض أن يُنادى
# **بعد الإغلاق من الـassembler حصريًّا**، والـassembler يكتب في **جذر الجلسة** لا في
# مجلّدات المقاطع ⇒ **لا سبيلَ لأيّ ردمٍ أن يُرضي هذا الشرط على مستوى المقطع.**
#
# ⇒ الأثر المقيس: **كلُّ جلسةٍ أطلقت تنبيهًا كانت تُرفَض** — والارتباط في السجلّ المدفوع
# قاطع: `n_emitted > 0` ⟺ أحمر · `n_emitted == 0` ⟺ أخضر (16 جلسة، 07-15→08-05) ⇒
# `session_complete=0` ليس ندرةَ بياناتٍ بل **بوّابةً غيرَ قابلةٍ للاستيفاء عند وجود
# البيانات التي بُنيت لقياسها**.
#
# 🔒 **ولا يُفقَد تدقيقٌ واحد:** الجوهر يحرسه على مستوى الجلسة `path_not_reaching_close`
# الذي يقرأ **البيانات المدموجة بعد الردم** — فلو فشل الردم (بلا مفتاح · خطأ شبكة ·
# `backfill_status=empty/error`) لم يبلغ المسارُ الإغلاقَ فتُرفَض الجلسة. أي أن الشرط
# **انتقل إلى موضعه الصحيح** ولم يُلغَ. وباقي أسباب المقطع (تغطية النافذة · بدء
# الافتتاح · الدورات · الـschema · الطوابع) تبقى **رافضة** كما هي.
#
# ⚠️ ولا تُوسَّع هذي القائمة إلا لسببٍ **مستحيل الاستيفاء بنيويًّا** ويحرسه بديلٌ أقوى
# على مستوى الجلسة — وإلّا صارت بابًا لتخفيفٍ صامت.
#
# 🔴 **وإضافةٌ ثانيةٌ بالقاعدة نفسِها (2026-09-24 — عطلٌ مقيسٌ من سجلّ الـworkflow):**
# `segment_window_capped` — مقطعُ الافتتاح **قصّه سقفُ زمن التشغيل** قبل نهاية نافذته الاسميّة.
# كرونُ الاحتياط (2026-08-29) يُقلع الجوبَ مبكّرًا فينتظر الجرسَ من ميزانيّته: تشغيلةُ
# `35845795981` أقلعت 09:56 UTC وانتظرت 214 دقيقة ⇒ المهلةُ 09:56 ‏+ 330 = 15:26 قبل نهاية
# النافذة 16:45 ⇒ مسح 116 من 195 دقيقة **ثمّ أقلع `close` بعد خمس ثوانٍ وملأ الباقي**
# (`_start_plan`: المِرساةُ الجرسُ لا بدايةُ المقطع). فالرادارُ لم يَعمَ دقيقة، **والمدقّقُ
# وحدَه لم يعرف هذا الوضع** ⇒ رُفضت **كلُّ جلسةٍ منذ 2026-08-31** (‏17 جلسةً في 18 تشغيلةٍ فاشلة
# حتى 09-23 — لـ08-31 تشغيلتان؛ عدٌّ من واجهة Actions 2026-09-24)
# وكان سببَها الوحيد في 09-21 · 09-22 · 09-23.
# ⚖️ **والشرطان محقَّقان:** ① مستحيلُ الاستيفاء بنيويًّا في الوضع المشروع (الانتظارُ قبل
# الجرس يأكل ميزانيّةَ الجوب المحدودة بـ345 دقيقة) ② ويحرسه بديلٌ أقوى على مستوى الجلسة:
# `transition_gap_ms` **من مسحٍ فعليٍّ إلى مسحٍ فعليّ** (آخرُ لفّةٍ في `open` ⟶ أوّلُ لفّةٍ في
# `close`) **وحدُّه 10 دقائق** · و`close` يبلغ الإغلاق · و`ended_before_expected_close`.
# 🔒 **والتأجيلُ ضيّقٌ عمدًا:** مقطعُ الافتتاح وحدَه · وسببُ مهلته `max_runtime_cap` حرفيًّا ·
# **وبلغ مهلتَه فعلًا** (انتهاءٌ قبلها = عطلٌ لا قصّ ⇒ يبقى `segment_window_not_covered`
# رافضًا) · ولو غابت الفجوةُ المقيسة على مستوى الجلسة ⇒ `transition_gap_unmeasured` رافض.
DEFERRED_TO_ASSEMBLER = ("lost_post_alert_path", "segment_window_capped")
# حارسُ كلِّ مؤجَّلٍ على مستوى الجلسة — يُطبَع معه فلا يكون التأجيلُ تخفيفًا صامتًا.
DEFERRED_GUARD = {"lost_post_alert_path": "path_not_reaching_close",
                  "segment_window_capped": "transition_gap ≤ 10د من مسحٍ فعليّ"}
# 🧾 الحكمُ يُحفظ في الفهرس المدفوع (كان يُطبَع فقط فلا يعرفه التقريرُ الأسبوعيّ) — وسمُ
# القاعدة التي صدر بها، فالأحكامُ قبل هذا التاريخ غيرُ محفوظةٍ لا «غيرُ مكتملة».
# 🔎 (2026-09-26) صار «ذيلُ المسار المتحقَّقُ خاليًا عند المزوّد» يُحتسب بلوغًا للإغلاق (أدناه) ⇒ تاريخٌ جديد.
# 🔴 (2026-09-26b) ومعه `delivered_unrecorded` (تسليمٌ وصل ولم يُسجَّل) — لا يغيّر حكمَ جلسةٍ سابقة
#    (الحقلُ لا يُكتب إلّا بعد الإصلاح) ⇒ وسمٌ جديدٌ لا حكمٌ جديدٌ على الماضي.
VERDICT_RULE = "2026-09-26b"

# 🔎 (2026-09-26) **ذيلٌ بلا شموع ليس مسارًا ناقصًا — عطلٌ مقيسٌ في تعريف `path_not_reaching_close`**:
#    مِجَسُّ الفرع `36223025879` على أرشيف الخام (49 جلسة · 110 تنبيهًا مُصدَرًا): سبعُ رفضاتٍ بهذا السبب،
#    **خمسٌ منها جُمِّعت بعد الإغلاق** (CELU 08-18 · MIMI 08-24 · CCTG 09-03 · SMX 09-18 · CURX 09-25) وفي
#    الخمس **آخرُ شمعةٍ في المسار = آخرُ شمعةٍ نظاميّةٍ عند Polygon اليوم** (الردمُ التقط كلَّ ما عند المزوّد)
#    وصفقاتُ الدقائق الأخيرة **odd lot وحدَها** (شرط 37) فلا تصنع شمعةَ دقيقة ⇒ «شمعةٌ في آخر 4 دقائق»
#    **مستحيلُ الاستيفاء** لسهمٍ رقيقٍ لم يُتداوَل فيه لوتٌ كامل — فيُسقط جلستَه **ويحيّز عيّنةَ E2 ضدّ
#    الرقيقة**. والرفضان الباقيان (PSTV 07-24 · VHUB 08-31) جُمِّعا **قبل** الإغلاق وعند المزوّد شموعٌ بعد
#    مسارهما ⇒ صحيحان ويبقيان.
#    ⇒ **البديلُ الأقوى دليلٌ من المزوّد لا افتراض:** فحصٌ **بعد الإغلاق** لنافذةٍ مؤرَّخة من الدقيقة التالية
#    لآخر شمعةٍ حتى بداية آخر دقيقة، بجوابٍ صريحٍ فارغ (`n == 0`) — يكتبه الـassembler حيًّا أو `e2_recover`
#    للماضي في `TAIL_CHECKS_FILE`. **ولا يُقبل غيرُه:** تعذّرُ الجلب لا يُكتب أصلًا، وشموعٌ في الذيل تُدمَج في
#    المسار (ثغرةٌ حقيقيّة سُدّت) أو يبقى الرفض، وفحصٌ قبل الإغلاق أو نافذةٌ لا تلاصق المسار أو لا تبلغ آخرَ
#    دقيقة ⇒ رافض. والمقبولُ **يُطبَع** (`tail_verified`) ويُحفظ في الفهرس — لا تخفيفَ صامت.
TAIL_CHECKS_FILE = "close_tail_checks.json"


def tail_check_valid(ck, last_t, close_ms):
    """🔎 نقيّة: هل يُثبت فحصُ الذيل `ck` أن مسارَ رمزٍ آخرُ شمعته `last_t` مكتملٌ حتى الإغلاق `close_ms`؟
    ‏`n` صفرٌ صحيح (لا منطقيّ) · جرى **بعد** الإغلاق · يبدأ عند الدقيقة التالية لآخر شمعةٍ أو قبلها ·
    ويبلغ بدايةَ آخر دقيقة. أيُّ شكلٍ آخر ⇒ False (فاشلٌ-مغلق: لا دليلَ = لا قبول)."""
    try:
        if not isinstance(ck, dict) or last_t is None or close_ms is None:
            return False
        n = ck.get("n")
        if isinstance(n, bool) or not isinstance(n, int) or n != 0:
            return False
        vals = [ck.get("at_ms"), ck.get("from_ms"), ck.get("to_ms")]
        if any(isinstance(v, bool) or not isinstance(v, int) for v in vals):
            return False
        at, frm, to = vals
        return at >= int(close_ms) and frm <= int(last_t) + 60_000 and to >= int(close_ms) - 60_000
    except Exception:
        return False


def _read_jsonl(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            return [json.loads(x) for x in fh if x.strip()]
    except Exception:
        return []


def _read_jsonl_gz(path):
    if not os.path.exists(path):
        return []
    try:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            return [json.loads(x) for x in fh if x.strip()]
    except Exception:
        return []


def _read_json(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def _iso_epoch_s(iso):
    if not iso:
        return None
    try:
        import datetime as _dt
        return _dt.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=_dt.timezone.utc).timestamp()
    except Exception:
        return None


def _ended_before(end_iso, expected_iso, margin_min):
    """True لو `end_iso` أبكر من `expected_iso` بأكثر من `margin_min` دقيقة. None-آمن → False."""
    a, b = _iso_epoch_s(end_iso), _iso_epoch_s(expected_iso)
    if a is None or b is None:
        return False
    return a < b - margin_min * 60


def _start_coverage_reason(sess):
    """🔬 P0-2: أول poll ناجح يجب أن يكون ≤ الافتتاح المتوقّع + start_tolerance (مقفول). يرجّع
    سبب التأخّر أو None. بلا بيانات = None (يُلتقَط بنقص الحقول لا هنا)."""
    a = _iso_epoch_s(sess.get("first_successful_poll_at"))
    b = _iso_epoch_s(sess.get("expected_open_iso"))
    tol = sess.get("start_tolerance_min") or 2
    if a is None or b is None:
        return None
    return ("start_coverage_late(%.1fد)" % ((a - b) / 60.0)) if a > b + tol * 60 else None


def analyze_session(sdir, close_checks=None):
    """`close_checks` = {رمز: فحصُ ذيل} يُضاف فوق `TAIL_CHECKS_FILE` في المجلّد (لـ`e2_recover`) — انظر
    `tail_check_valid`. بلا الاثنين = الحكمُ السابق حرفيًّا."""
    sess = _read_json(os.path.join(sdir, "session.json"))
    ss = _read_jsonl(os.path.join(sdir, "symbol_sessions.jsonl"))
    cands = _read_jsonl(os.path.join(sdir, "candidates.jsonl"))
    delivs = _read_jsonl(os.path.join(sdir, "deliveries.jsonl"))
    minute = _read_jsonl_gz(os.path.join(sdir, "minute_paths.jsonl.gz"))
    # نوع الوحدة: segment (جزء) · assembled (مدموجة) · single (جلسة واحدة قديمة).
    kind = "assembled" if sess.get("assembled") else ("segment" if sess.get("segment") else "single")
    is_session = (kind != "segment")        # فقط الجلسة الكاملة تخضع لـsession_complete
    # اكتمال الـschema (P1-9: candidate + المُصدَر + symbol-session)
    ss_missing = sum(1 for r in ss for k in SS_REQUIRED if k not in r)
    cand_missing = sum(1 for c in cands for k in CAND_REQUIRED if k not in c)
    emitted_missing = sum(1 for c in cands if c.get("alert_emitted")
                          for k in EMITTED_REQUIRED if k not in c)
    eligible = [r for r in ss if r.get("recall_eligible")]
    cov_vals = sorted(r.get("coverage_ratio", 0) for r in ss)
    med_cov = cov_vals[len(cov_vals) // 2] if cov_vals else 0.0
    # funnel
    emitted_cands = [c for c in cands if c.get("alert_emitted")]
    emitted = len(emitted_cands)
    delivered = sum(1 for d in delivs if d.get("delivered"))
    executable = sum(1 for c in cands if c.get("primary_executable"))
    executable_emitted = sum(1 for c in emitted_cands if c.get("primary_executable"))
    with_ts = sum(1 for c in cands if c.get("trigger_bar_start") is not None
                  and c.get("trigger_bar_end") is not None and c.get("detected_at") is not None)
    with_gate = sum(1 for c in cands if c.get("gate_decision"))
    max_t = {}
    for m in minute:
        sym, t = m.get("symbol"), m.get("t")
        if sym is not None and t is not None:
            max_t[sym] = max(max_t.get(sym, t), t)

    # ── أسباب عدم الاكتمال (data-integrity فقط، لا حكم عتبات) ──────────────────
    reasons = []
    close_ms = None
    tail_ok, tail_open = set(), {}     # 🔎 (2026-09-26) ذيلٌ متحقَّق · وما لم يُتحقَّق منه {رمز: آخرُ شمعة}
    deferred = []      # أسبابُ مقاطعَ مؤجَّلةٌ للـassembler — تُعلَن ولا تَرفض (لا صمت)
    term = sess.get("termination")
    if term != "normal":
        reasons.append(f"termination={term}")
    ls, lc = sess.get("loops_started"), sess.get("loops_completed")
    if ls is not None and lc is not None and ls != lc:
        reasons.append(f"loops_mismatch({ls}≠{lc})")
    if ss_missing or cand_missing or emitted_missing:
        reasons.append("schema_gaps(ss=%d,cand=%d,emit=%d)" % (ss_missing, cand_missing, emitted_missing))
    if with_ts != len(cands):
        reasons.append("missing_locked_timestamps")
    emitted_syms = {c.get("symbol") for c in emitted_cands}
    deliv_syms = {d.get("symbol") for d in delivs if d.get("delivered")}
    if delivered > emitted or not deliv_syms.issubset(emitted_syms):
        reasons.append("emitted_delivered_contradiction")
    # 🔬 P0-5: لا تسليم مكرّر — كل رمز يُسلَّم مرة واحدة (دِدوب مرة/سهم/يوم).
    _dpsym = {}
    for d in delivs:
        if d.get("delivered"):
            _dpsym[d.get("symbol")] = _dpsym.get(d.get("symbol"), 0) + 1
    _dups = sorted(str(s) for s, n in _dpsym.items() if n > 1)
    if _dups:
        reasons.append("duplicate_delivery(%s)" % ",".join(_dups))
    # 🔴 2026-09-26 (جلسة 09-18): تسليمٌ **وصل** في الإنتاج (`delivered_symbols_segment` يكتبه العاملُ
    #    من `seen`) ولم يُسجَّل في القياس = ثغرةٌ تُعلَن لا غيابٌ صامت (ONMD صدر قبل التحاق المسجّل).
    #    غيابُ الحقل (مقاطعُ ما قبل الإصلاح · والمدموجةُ نفسُها) ⇒ لا حكمَ هنا.
    _dss = sess.get("delivered_symbols_segment")
    if isinstance(_dss, list):
        _unrec = sorted({s for s in _dss if isinstance(s, str) and s} - deliv_syms)
        if _unrec:
            reasons.append("delivered_unrecorded(%s)" % ",".join(_unrec))
    unresolved_nbbo = [c.get("symbol") for c in emitted_cands
                       if c.get("operator_status") == "pass" and c.get("primary_executable") is None]
    if unresolved_nbbo:
        reasons.append("unresolved_nbbo(%s)" % ",".join(sorted(set(unresolved_nbbo))))
    if sess.get("alert_logic_version") != "unchanged":
        reasons.append("alert_logic_version_changed")

    if kind == "segment":
        # segment_complete: غطّى نافذته المقصودة (وصل ~ نهاية المقطع) + كل رمز مُنبَّه له بار لاحق.
        _seg_end = sess.get("segment_ended_at") or sess.get("ended_at")
        if _ended_before(_seg_end, sess.get("expected_segment_end_iso"), WINDOW_MARGIN_MIN):
            # 🔴 2026-09-24: قصُّ سقفِ التشغيل لمقطع الافتتاح **مؤجَّلٌ** (انظر
            #    `DEFERRED_TO_ASSEMBLER`) — بشرط أنه بلغ مهلتَه فعلًا؛ وإلّا فالقديمُ الرافض.
            if (sess.get("segment") == "open"
                    and sess.get("deadline_reason") == "max_runtime_cap"
                    and sess.get("deadline_iso")
                    and not _ended_before(_seg_end, sess.get("deadline_iso"), WINDOW_MARGIN_MIN)):
                reasons.append("segment_window_capped(max_runtime_cap)")
            else:
                reasons.append("segment_window_not_covered")
        if sess.get("segment") == "open":          # 🔬 P0-2: تغطية بداية الافتتاح (open فقط)
            _sc = _start_coverage_reason(sess)
            if _sc:
                reasons.append(_sc)
        lost = [c.get("symbol") for c in emitted_cands
                if c.get("trigger_bar_start") is not None
                and max_t.get(c.get("symbol"), c["trigger_bar_start"]) <= c["trigger_bar_start"]]
        if lost:
            reasons.append("lost_post_alert_path(%s)" % ",".join(sorted(set(lost))))
    else:
        # session_complete: انتهت للإغلاق + المسارات تصل للإغلاق + بدء التغطية + الجزآن + الفجوة + السلسلة.
        if sess.get("ended_before_expected_close"):
            reasons.append("ended_before_expected_close(%s د)" % sess.get("minutes_short_of_close"))
        close_ms = _iso_epoch_s(sess.get("expected_close_iso"))
        close_ms = int(close_ms * 1000) if close_ms is not None else None
        if close_ms is not None:
            target = close_ms - 60_000 - CLOSE_PATH_TOLERANCE_MS
            # 🔎 (2026-09-26): ذيلٌ متحقَّقٌ خالٍ عند المزوّد بعد الإغلاق = مسارٌ مكتمل (انظر
            #    `TAIL_CHECKS_FILE`) — يُعلَن في `tail_verified` ولا يَرفض؛ وما سواه يبقى رافضًا.
            _tail = _read_json(os.path.join(sdir, TAIL_CHECKS_FILE))
            _tail = dict(_tail) if isinstance(_tail, dict) else {}
            if isinstance(close_checks, dict):
                _tail.update(close_checks)
            not_reaching = []
            for c in emitted_cands:
                _s = c.get("symbol")
                if _s is None or max_t.get(_s, -1) >= target:
                    continue
                if tail_check_valid(_tail.get(_s), max_t.get(_s), close_ms):
                    tail_ok.add(_s)
                else:
                    not_reaching.append(_s)
                    tail_open[_s] = max_t.get(_s)
            if not_reaching:
                reasons.append("path_not_reaching_close(%s)" % ",".join(sorted(set(not_reaching))))
        elif emitted_cands:
            reasons.append("expected_close_unknown")   # لا يمكن إثبات وصول المسار
        if kind == "single":                       # 🔬 P0-2: الجلسة الواحدة تغطّي الافتتاح بنفسها
            _sc = _start_coverage_reason(sess)
            if _sc:
                reasons.append(_sc)
        if kind == "assembled":
            segs = sess.get("segments") or []
            roles = {s.get("role") for s in segs}
            if not ({"open", "close"} <= roles):
                reasons.append("missing_segment(%s)" % (",".join(sorted(str(x) for x in roles)) or "none"))
            # 🔬 P0-5: **اكتمال كل مقطع فعليًّا** (يحلّل المجلّدات الفرعية — يشمل تغطية بداية open).
            for _role in ("open", "close"):
                _segdir = os.path.join(sdir, "segment_%s" % _role)
                if os.path.isdir(_segdir):
                    _sr = analyze_session(_segdir)
                    # 🔴 2026-08-06: يُفصَل الرافضُ عن **المؤجَّل بالتصميم** (انظر
                    #    `DEFERRED_TO_ASSEMBLER` أعلاه). المؤجَّل يُعلَن ولا يَرفض.
                    _block, _defer = [], []
                    for _x in (_sr.get("incomplete_reasons") or []):
                        (_defer if _x.startswith(DEFERRED_TO_ASSEMBLER) else _block).append(_x)
                    if _defer:
                        deferred.append("%s:%s" % (_role, "|".join(_defer)))
                    if _block:
                        reasons.append("segment_incomplete(%s:%s)" % (_role, "|".join(_block)[:80]))
            # 🔬 P0-3: فجوة الانتقال ضمن الحدّ المقفول.
            _gap, _gmax = sess.get("transition_gap_ms"), sess.get("max_transition_gap_min")
            if _gap is not None and _gmax and _gap > _gmax * 60_000:
                reasons.append("transition_gap_exceeded(%.1fد>%sد)" % (_gap / 60000.0, _gmax))
            # 🔴 2026-09-24: قصُّ `open` المؤجَّل **لا يمرّ إلّا بفجوةٍ مقيسة** — غيابُها يعني أن
            #    استمرارَ المسح غيرُ مُثبَت ⇒ رافض (لا يُفترَض الأفضل).
            if any(d.startswith("open:") and "segment_window_capped" in d for d in deferred) \
                    and (_gap is None or not _gmax):
                reasons.append("transition_gap_unmeasured(open:capped)")
            # 🔬 P0-4: سلسلة manifest سليمة.
            if sess.get("manifest_chain_ok") is False:
                reasons.append("manifest_chain_failed(%s)"
                               % "|".join(sess.get("manifest_chain_reasons") or [])[:80])

    complete = (not reasons)
    return {
        "session_date": sess.get("session_date"), "kind": kind, "termination": term,
        "loops_started": ls, "loops_completed": lc,
        "deadline_reason": sess.get("deadline_reason"),
        "ended_before_expected_close": sess.get("ended_before_expected_close"),
        "minutes_short_of_close": sess.get("minutes_short_of_close"),
        "n_symbols": len(ss), "n_candidates": len(cands),
        "n_emitted": emitted, "n_delivered": delivered, "n_executable": executable,
        "n_executable_emitted": executable_emitted, "nbbo_breakdown": nbbo_age_breakdown(cands),
        "recall_eligible_symbol_sessions": len(eligible), "median_coverage": round(med_cov, 3),
        "schema_gaps_symbol_sessions": ss_missing, "schema_gaps_candidates": cand_missing,
        "candidates_with_timestamps": with_ts, "candidates_with_gate_decision": with_gate,
        "alert_logic_version": sess.get("alert_logic_version"),
        "incomplete_reasons": reasons,
        # 🔴 أسبابُ مقاطعَ **مؤجَّلةٌ للـassembler** (لا تَرفض) — تُطبَع صراحةً فلا يكون
        #    التأجيلُ تخفيفًا صامتًا، ويبقى مرئيًّا أن الشرط قِيس ومَن يحرسه.
        "deferred_reasons": deferred,
        # 🔎 (2026-09-26): ذيلٌ قُبل بدليل المزوّد (يُطبَع ويُحفظ) · وما بقي بلا دليل {رمز: آخرُ شمعة}
        #    ليفحصه `e2_recover` · والإغلاقُ المتوقّع بالملّي.
        "tail_verified": sorted(tail_ok),
        "path_tail_unverified": dict(sorted(tail_open.items())),
        "expected_close_ms": close_ms,
        # segment → segment_complete · session → session_complete
        "segment_complete": (complete if kind == "segment" else None),
        "session_complete": (complete if is_session else None),
        "complete": complete,
    }


def verdict_entry(r):
    """🧾 مفاتيحُ حكم المدقّق التي تُحفظ في الفهرس — **نقيّة**. ترجّع `{}` لغير الجلسة
    (المقطعُ وحدَه لا يُحكَم عليه بـsession_complete) أو لنتيجةٍ فارغة: لا حكمَ يُخترَع.

    🔬 (2026-09-25) **ومعها عدّا E2-B** (`E2B_INDEX_KEYS`) ليبقى العدّادُ التراكميّ بعد انتهاء
    artifacts (‏`ign-assembled` جلسة 08-11 ينتهي 2026-11-09 يومَ تذكير E2-B). **ولا عددَ يُخترَع:**
    غيرُ الصحيح غيرِ السالب (غائب · منطقيّ · نصّ) لا يُكتب."""
    if not isinstance(r, dict) or not isinstance(r.get("session_complete"), bool):
        return {}
    out = {"session_complete": r["session_complete"],
           "incomplete_reasons": [str(x)[:120] for x in (r.get("incomplete_reasons") or [])][:8],
           "deferred_reasons": [str(x)[:120] for x in (r.get("deferred_reasons") or [])][:8],
           "verdict_rule": VERDICT_RULE}
    for _k in E2B_INDEX_KEYS:
        _v = r.get(_k)
        if isinstance(_v, int) and not isinstance(_v, bool) and _v >= 0:
            out[_k] = _v
    # 🔎 (2026-09-26): ذيلٌ قُبل بدليل المزوّد **يُحفظ اسمُه** مع الحكم (غيابُه = لم يُقبل ذيلٌ) — فلا
    #    تُقرأ الجلسةُ المكتملةُ به مكتملةً بالتعريف القديم.
    _tv = [str(x)[:12] for x in (r.get("tail_verified") or []) if x][:8]
    if _tv:
        out["tail_verified"] = _tv
    return out


def record_verdict(index_path, session_date, r):
    """🧾 يدمج حكمَ المدقّق في مدخل الفهرس **ولا يمسّ العدّادات** — فاشلٌ-آمن (خطأٌ ⇒ False).
    لا يُنشئ مدخلًا لتاريخٍ غائب: الفهرسُ يكتبه المسجّلُ/الاسترجاعُ، والحكمُ يُلحَق به فقط."""
    try:
        v = verdict_entry(r)
        if not v or not session_date or not os.path.exists(index_path):
            return False
        with open(index_path, encoding="utf-8") as fh:
            idx = json.load(fh) or {}
        if not isinstance(idx, dict) or not isinstance(idx.get(session_date), dict):
            return False
        idx[session_date] = {**idx[session_date], **v}
        tmp = index_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(idx, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        os.replace(tmp, index_path)
        return True
    except Exception:
        return False


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    strict = "--strict" in sys.argv        # 🔬 P0-6: يفشل بخروج غير صفر عند جلسة غير مكتملة
    root = args[0] if args else "e2_measurement"
    if not os.path.isdir(root):
        print(f"📋 لا مجلّد قياس بعد: {root} (يُنشأ عند أول جلسة رادار بـE2_MEASUREMENT=1).")
        return
    sessions = sorted(d for d in os.listdir(root) if d.startswith("session_"))
    if not sessions:
        print(f"📋 لا جلسات مُسجَّلة بعد في {root}.")
        if strict:
            sys.exit(3)                    # لا جلسة = فشل في الوضع الصارم (بوّابة Pilot)
        return
    print("=" * 78)
    print("🔬 E2-A — تدقيق تغطية/اكتمال القياس الظلّي (لا معايرة عتبات — SPEC §18)")
    print("=" * 78)
    total_complete = 0                       # 🔬 (ب+): البوّابة تعدّ session_complete فقط (لا المقاطع)
    results = []
    for s in sessions:
        r = analyze_session(os.path.join(root, s))
        results.append(r)
        if r.get("session_complete"):        # المقاطع/الجلسات القديمة ذات session_complete=None لا تُعدّ
            total_complete += 1
        print(f"\n▸ {r['session_date']} [{r['kind']}] · إنهاء={r['termination']} · "
              f"دورات {r['loops_started']}→{r['loops_completed']} · موعد={r['deadline_reason']}")
        print(f"    رموز={r['n_symbols']} · candidates={r['n_candidates']} "
              f"(نُفِّذ NBBO={r['n_executable']}) · emitted={r['n_emitted']} · delivered={r['n_delivered']}")
        print(f"    recall-eligible symbol-sessions={r['recall_eligible_symbol_sessions']} "
              f"(polls≥{RECALL_MIN_POLLS}·cov≥{RECALL_MIN_COVERAGE}·exp≥{RECALL_MIN_EXPOSURE_MIN}د) "
              f"· وسيط التغطية={r['median_coverage']}")
        print(f"    اكتمال schema: ثغرات symbol-session={r['schema_gaps_symbol_sessions']} "
              f"· ثغرات candidate={r['schema_gaps_candidates']} "
              f"· بالطوابع={r['candidates_with_timestamps']}/{r['n_candidates']} "
              f"· ببوّابة={r['candidates_with_gate_decision']}/{r['n_candidates']}")
        if r["ended_before_expected_close"]:
            print(f"    ⚠️ انتهت قبل الإغلاق المتوقّع بـ{r['minutes_short_of_close']} د "
                  f"(قيد سقف رنر GitHub — تغطية جزئية صريحة).")
        if r.get("tail_verified"):
            print("    ℹ️ ذيلٌ بلا شموعٍ عند المزوّد (متحقَّقٌ بعد الإغلاق · لا يَرفض · %s): %s"
                  % (TAIL_CHECKS_FILE, " · ".join(r["tail_verified"])))
        if r.get("deferred_reasons"):
            _guards = sorted({g for d in r["deferred_reasons"]
                              for k, g in DEFERRED_GUARD.items() if k in d})
            print("    ℹ️ مؤجَّلٌ للـassembler (لا يَرفض · يحرسه " + " · ".join(_guards) + "): "
                  + " · ".join(r["deferred_reasons"]))
        _nb = r.get("nbbo_breakdown") or {}
        if r.get("n_candidates"):
            print("    NBBO الأساسيّ: قابلٌ للتنفيذ %s (منها مُصدَر %s) · بائت %s%s · مستقبليّ %s%s · غيرُ صالح %s · مفقود %s"
                  % (_nb.get("executable"), r.get("n_executable_emitted"), _nb.get("stale"),
                     (" (وسيطُ العمر %.1fث)" % (_nb["stale_median_ms"] / 1000.0)
                      if _nb.get("stale_median_ms") is not None else ""),
                     _nb.get("future"),
                     (" (أدنى %dملّي)" % _nb["future_min_ms"] if _nb.get("future_min_ms") is not None else ""),
                     _nb.get("invalid"), _nb.get("missing")))
        _label = "segment_complete" if r["kind"] == "segment" else "session_complete"
        verdict = ("✅ %s" % _label) if r["complete"] else ("⚠️ غير مكتملة: " + " · ".join(r["incomplete_reasons"]))
        print(f"    منطق التنبيه: {r['alert_logic_version']} · الحكم: {verdict}")
    print("\n" + "=" * 78)
    # 🔴 (2026-09-25): العدّان **لهذا المجلّد وحدَه** — وهو في الـassembler جلسةٌ واحدة وفي الاسترجاع
    #    الليليّ آخرُ ~15 تشغيلة ⇒ «تتراكم» و«‏2/20» كانا يُقرآن حالَ البوّابتين وليسا هي (‏`36002049868`
    #    على 47 جلسة ‏11/20 ثمّ `36082836057` على 4 ‏2/20 · والمكتملُ في الفهرس 31). **التراكميُّ من
    #    الفهرس** (`e2b_count_from_index` · يطبعه `e2_recover`).
    print(f"📋 وحدات هذا المجلّد وحدَه={len(sessions)} · session_complete={total_complete} — "
          "ليس عدَّ بوّابة E2-A (التراكميُّ من الفهرس: e2_recover).")
    _e2b = e2b_gate_count(results)
    print("🔬 E2-B في هذا المجلّد وحدَه: %d تنبيهًا بـNBBO قابلٍ للتنفيذ في جلساتٍ مكتملة — "
          "والبوّابةُ %d تراكميًّا (من الفهرس: e2_recover)." % (_e2b, E2B_MIN_DECIDED_ALERTS))
    print("⚠️ E2-A: قياس فقط — لا معايرة/حكم عتبات (E2-B/C بعد العيّنة + تسجيل مسبق + موافقة المالك).")
    print("=" * 78)
    # 🔬 P0-6: بوّابة صارمة — أي جلسة (assembled/single) غير مكتملة تُفشل الأمر (بوّابة Pilot).
    if strict:
        incomplete = [r for r in results if r.get("session_complete") is False]
        if incomplete:
            print("❌ --strict: %d جلسة غير مكتملة → فشل." % len(incomplete))
            sys.exit(1)
        print("✅ --strict: كل الجلسات (assembled/single) مكتملة.")


if __name__ == "__main__":
    main()
