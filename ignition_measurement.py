# -*- coding: utf-8 -*-
"""
==========================================================
🔬 E2-A — قياس ظلّي لرادار الانطلاق (Ignition Measurement)
==========================================================
طبقة **قياس مستقلة تمامًا** عن منطق الرادار (E2 SPEC §3/§5). لا تكرّر `scan_ignition`،
بل تتلقّى أحداث funnel عبر `recorder.trace` (المُمرَّر لـ`scan_ignition(trace=...)`) وتجمّع:
- **exposure حقيقي** لكل symbol-session (أول/آخر مشاهدة · polls · تغطية) — لا قائمة نهائية فقط.
- **candidate-events** لكل raw candidate فريد (سعر/حجم/NBBO/توقيت/بوّابة) — حتى المكبوت.
- **funnel** كامل يفصل raw عن operator gate عن fallback عن emitted عن delivered.
- **مسار الدقيقة** (اختياري) بدِدوب (symbol, t).

**فاشل-آمن مطلق:** أي خطأ داخل أي دالّة يُبتلَع — القياس **لا يُسقط الرادار أبدًا**.
**crash-safe:** candidates/deliveries/minute تُلحَق فورًا مع flush · الحالة تُحفَظ دوريًّا ·
`finalize` يُستدعى في `finally` (يكتب session/summary/index حتى عند الانقطاع).
**لا أسرار** تُخزَّن (§8): لا مفاتيح/توكنات/headers/URLs فيها apiKey.

🔒 قياس/توثيق فقط — لا يمسّ الفرز/الاختيار/الدخول/الوقف/الأهداف/العتبات · لا LOGIC_VERSION.
"""
import datetime as _dt
import gzip
import json
import os
import queue as _queue
import threading as _threading

SCHEMA_VERSION = 3                 # 🔬 مراجعة Codex 4: NBBO لا-تزامني + latency مفكّكة + manifest
_TERMINATION = ("normal", "exception", "timeout", "cancelled", "unknown")

BAR_INTERVAL_MS = 60_000           # §2c: شمعة الدقيقة الواحدة
MAX_QUOTE_AGE_MS = 5_000           # §2d: أقصى عمر NBBO تنفيذي (5 ثوانٍ، مطابق التسجيل المسبق)
# §2e: حدود جودة بيانات أهلية recall (SPEC §7) — **ليست عتبات تداول**.
RECALL_MIN_POLLS, RECALL_MIN_COVERAGE, RECALL_MIN_EXPOSURE_MIN = 20, 0.80, 60
EARLY_CLOSE_MARGIN_MIN = 10        # §2a: هامش «انتهت قبل الإغلاق المتوقّع» المعقول


def _utcnow_iso():
    """طابع UTC ISO 8601 بلاحقة Z (فاشل-آمن)."""
    try:
        return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    except Exception:
        return None


def _utcnow_ms():
    """الآن بالملّي ثانية epoch-UTC (فاشل-آمن → None). مرجع «وقت القرار» لعمر NBBO."""
    try:
        return int(_dt.datetime.now(_dt.timezone.utc).timestamp() * 1000)
    except Exception:
        return None


def _iso_epoch_s(iso):
    """ISO «YYYY-MM-DDTHH:MM:SSZ» → epoch ثوانٍ (فاشل-آمن → None). نقيّة/قابلة للاختبار."""
    if not iso:
        return None
    try:
        return _dt.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=_dt.timezone.utc).timestamp()
    except Exception:
        return None


def _normalize_ts_ms(t):
    """🔬 §2d: أيّ طابع Unix (ثوانٍ/ملّي/مايكرو/نانو) → **ملّي ثانية UTC** بالمقدار.
    Polygon يرجّع NBBO بالنانو والـaggregates بالملّي — نوحّدهما. `None` لغير الصالح/الصغير
    (تحت 2001 تقريبًا). نقيّة/قابلة للاختبار (بلا شبكة/ساعة)."""
    try:
        t = float(t)
    except (TypeError, ValueError):
        return None
    if t <= 0:
        return None
    # نُرجع **عدد صحيح** ملّي (floor) ليطابق `_utcnow_ms` فلا يظهر فارق كسر-ملّي كطابع مستقبلي.
    if t >= 1e18:          # نانو ثانية (2026 ≈ 1.75e18)
        return int(t / 1e6)
    if t >= 1e15:          # مايكرو ثانية (2026 ≈ 1.75e15)
        return int(t / 1e3)
    if t >= 1e12:          # ملّي ثانية (2026 ≈ 1.75e12)
        return int(t)
    if t >= 1e9:           # ثوانٍ (2026 ≈ 1.75e9)
        return int(t * 1e3)
    return None            # أصغر من ذلك = غير صالح/مجهول


def _quote_freshness(quote_ms, now_ms, max_age_ms=MAX_QUOTE_AGE_MS):
    """🔬 §2d: (quote_age_ms, is_fresh). العمر = now − quote (ملّي). طازج **فقط** لو
    `0 ≤ العمر ≤ max`. مفقود(None) → (None, False) · سالب(طابع مستقبلي، غير منطقي) →
    (age, False) · قديم → (age, False). نقيّة/قابلة للاختبار."""
    if quote_ms is None or now_ms is None:
        return (None, False)
    try:
        age = now_ms - quote_ms
    except (TypeError, ValueError):
        return (None, False)
    if age < 0:                       # طابع مستقبلي = غير منطقي (انحراف ساعة)
        return (age, False)
    return (age, age <= max_age_ms)


def _nbbo_metrics(bid, ask, quote_raw, now_ms):
    """🔬 §2d/P1.3: مقاييس NBBO لمصدرٍ واحد (نقيّة): mid · spread_pct_mid · quote_ts_ms ·
    quote_age_ms · executable. **executable = NBBO صالح (ask>0 · ask≥bid · سبريد متاح) ‏و‏
    طازج (0≤العمر≤5000ملّي).** قابلة للاختبار (بلا شبكة)."""
    q_ms = _normalize_ts_ms(quote_raw)
    age, fresh = _quote_freshness(q_ms, now_ms)
    mid = spread = None
    valid = False
    try:
        if bid is not None and ask is not None and float(ask) > 0:
            mid = round((float(bid) + float(ask)) / 2.0, 6)
            if mid > 0:
                spread = round((float(ask) - float(bid)) / mid * 100.0, 4)
            valid = bool(float(ask) >= float(bid) and spread is not None)
    except Exception:
        valid = False
    return {"mid": mid, "spread_pct_mid": spread, "quote_ts_ms": q_ms,
            "quote_age_ms": (int(age) if age is not None else None),
            "executable": bool(valid and fresh)}


def _exposure_minutes(first_iso, last_iso):
    """🔬 §2e: دقائق التعرّض بين أول/آخر مشاهدة (ISO). نقيّة/فاشلة-آمنة → 0.0."""
    a, b = _iso_epoch_s(first_iso), _iso_epoch_s(last_iso)
    if a is None or b is None or b < a:
        return 0.0
    return round((b - a) / 60.0, 2)


def _recall_eligible(polls, coverage, exposure_min):
    """🔬 §2e: أهلية recall = **الشروط الثلاثة معًا** (polls≥20 · coverage≥0.80 · exposure≥60د).
    جودة بيانات لا عتبات تداول (SPEC §7). نقيّة/قابلة للاختبار."""
    try:
        return bool(polls >= RECALL_MIN_POLLS and coverage >= RECALL_MIN_COVERAGE
                    and exposure_min >= RECALL_MIN_EXPOSURE_MIN)
    except (TypeError, ValueError):
        return False


def _atomic_write(path, text):
    """كتابة ذرّية (tmp ثم rename) — فاشلة-آمنة (لا ترفع)."""
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        return True
    except Exception:
        return False


def _new_symbol_session(session_date, symbol):
    """قالب صف symbol-session (SPEC §7)."""
    return {
        "schema_version": SCHEMA_VERSION, "session_date": session_date, "symbol": symbol,
        "first_seen_at": None, "last_seen_at": None,
        "active_polls": 0, "level_available_polls": 0,
        "bars_attempted": 0, "bars_ok": 0, "bars_failed": 0,
        "raw_candidate_count": 0, "operator_pass_count": 0, "operator_fail_count": 0,
        "operator_unavailable_count": 0, "fallback_pass_count": 0, "fallback_fail_count": 0,
        "emitted_count": 0, "delivered_count": 0,
        "first_bar_ts": None, "last_bar_ts": None,
        "break_level_first": None, "break_level_last": None, "break_level_source_first": None,
        "coverage_ratio": 0.0,
        # §2e: exposure حقيقي + أهلية recall (تُحسب في finalize).
        "exposure_minutes": 0.0, "recall_eligible": False,
        # 🔬 P1.2 §2b: حالة الردم البعدي (success فقط عند وصول المسار للحدّ المتوقّع).
        "backfill_status": "not_attempted", "backfill_bars_added": 0, "backfill_last_bar_ts": None,
    }


class IgnitionMeasurementRecorder:
    """مسجّل القياس الظلّي. الاستعمال:
        rec = IgnitionMeasurementRecorder(session_date, meta={...})
        rows = scan_ignition(wl, today, trace=rec.trace)
        rec.telegram_attempt(rows); rec.telegram_success(rows) / rec.telegram_failure(rows, err)
        ... (في finally) rec.finalize(termination="normal")
    كل دالّة فاشلة-آمنة (لا ترفع) فلا تُسقط الرادار."""

    def __init__(self, session_date, out_root="e2_measurement", meta=None,
                 write_repo_index=False, segment=None, nbbo_fetcher=None):
        self.session_date = session_date
        # 🔬 (ب+): مقطع مستقلّ لكل جوب (open/close) فلا يتصادمان؛ assembler يدمجهما لاحقًا.
        # بلا segment = المسار القديم (جلسة واحدة session_<date>/) — توافق خلفي كامل.
        self.segment = (str(segment).strip() or None) if segment else None
        base = os.path.join(out_root, "session_%s" % session_date)
        self.dir = os.path.join(base, "segment_%s" % self.segment) if self.segment else base
        self.meta = dict(meta or {})
        self.segment_id = self.meta.get("segment_id") or (
            "%s|%s" % (session_date, self.segment) if self.segment else session_date)
        # الملفّان الصغيران القابلان للدفع للريبو (SPEC §5) يُكتبان في جذر العمل **فقط** حين
        # يطلبها العامل الحيّ صراحةً (write_repo_index=True) — الاختبارات لا تلوّث الريبو.
        self.write_repo_index = bool(write_repo_index)
        self.symbols = {}          # symbol -> symbol-session dict
        self.candidates = {}       # candidate_id -> candidate dict (دِدوب بالذاكرة)
        self._minute_seen = set()  # (symbol, t) لدِدوب مسار الدقيقة
        self.loops_started = 0
        self.loops_completed = 0
        self._loop_timings = []    # 🔬 P1.6: (schedule_lag_ms, loop_duration_ms) لكل دورة
        # 🔬 P0-2/P0-3: توقيت المراقبة (لبوّابة تغطية البداية + فجوة الانتقال).
        self.monitoring_started_at = None
        self.monitoring_ended_at = None
        self.first_successful_poll_at = None
        self.started_at = _utcnow_iso()
        self.ended_at = None
        self.termination = "unknown"
        # §2a: هل انتهت الجلسة قبل الإغلاق المتوقّع (يُحسب في finalize من meta.expected_close_iso).
        self.ended_before_expected_close = None
        self.minutes_short_of_close = None
        # 🔬 P1.4/P1-4: تتبّع commit + **SHA محتوى** القائمة (يتغيّر مع _fresh_watchlist كل ~5د)
        # — لا يكفي non-null؛ SHA يثبت أن نفس bytes استُخدمت وقت الترشيح.
        self.watchlist_commit_current = self.meta.get("watchlist_commit_start")
        self.watchlist_file_sha256_current = self.meta.get("watchlist_file_sha256_start")
        self.manifest_sha256 = None        # 🔬 P0-4: hash المقطع (يُحسب في finalize)
        self.enabled = False
        self._cand_fh = None
        self._deliv_fh = None
        self._minute_fh = None
        try:
            os.makedirs(self.dir, exist_ok=True)
            self._cand_fh = open(os.path.join(self.dir, "candidates.jsonl"), "a", encoding="utf-8")
            self._deliv_fh = open(os.path.join(self.dir, "deliveries.jsonl"), "a", encoding="utf-8")
            self.enabled = True
        except Exception:
            self.enabled = False
        # 🔬 P0-1: worker NBBO **لا-تزامني** — يجلب NBBO القياسي خارج مسار التنبيه الحرج فلا
        # ينتظر send_telegram أي شبكة. القفل يحمي تعديل candidate بين الخيط الرئيسي والـworker.
        self._lock = _threading.Lock()
        self.nbbo_fetcher = nbbo_fetcher
        self._nbbo_q = None
        self._nbbo_worker = None
        self._nbbo_stop = None
        if nbbo_fetcher is not None:
            try:
                self._nbbo_q = _queue.Queue()
                self._nbbo_stop = _threading.Event()
                self._nbbo_worker = _threading.Thread(target=self._nbbo_loop, daemon=True)
                self._nbbo_worker.start()
            except Exception:
                self._nbbo_q = None

    # ── worker NBBO لا-تزامني (P0-1) ────────────────────────────────────────
    def _enqueue_nbbo(self, cid, symbol):
        """يضع طلب NBBO في الطابور (لا-حاجز). فاشل-آمن."""
        try:
            if self._nbbo_q is not None and cid and symbol:
                self._nbbo_q.put_nowait((cid, symbol))
        except Exception:
            pass

    def _nbbo_loop(self):
        while True:
            try:
                item = self._nbbo_q.get(timeout=0.5)
            except Exception:
                if self._nbbo_stop is not None and self._nbbo_stop.is_set() \
                        and (self._nbbo_q is None or self._nbbo_q.empty()):
                    return
                continue
            try:
                if item is None:
                    return
                self._do_measure_nbbo(item[0], item[1])
            except Exception:
                pass
            finally:
                try:
                    self._nbbo_q.task_done()
                except Exception:
                    pass

    def _do_measure_nbbo(self, cid, symbol):
        """يجلب NBBO القياسي (المُحقَن) ويربطه بالمرشّح بـcandidate_id. يسجّل التوقيت والحالة.
        **الصلاحية من طابع المصدر لا من انتهاء HTTP** (§P0-1). قياس فقط."""
        started = _utcnow_ms()
        nb, status = None, "error"
        try:
            nb = self.nbbo_fetcher(symbol)
            status = "success" if nb else "empty"
        except Exception as e:
            nb = None
            status = "timeout" if "timeout" in type(e).__name__.lower() else "error"
        received = _utcnow_ms()
        with self._lock:
            cand = self.candidates.get(cid)
            if cand is None:
                return
            cand["measurement_nbbo_status"] = status
            cand["quote_request_started_at_ms"] = started
            cand["quote_received_at_ms"] = received
            if cand.get("detected_at_ms") is not None and received is not None:
                cand["quote_capture_lag_ms"] = int(received - cand["detected_at_ms"])
            if nb:
                self._apply_nbbo_source(cand, "measurement", nb.get("bid"), nb.get("ask"),
                                        nb.get("quote_ts"), _locked=True)

    def _drain_nbbo(self, timeout=10.0):
        """يوقف الـworker بعد تفريغ الطابور (يُستدعى في finalize قبل الكتابة). فاشل-آمن."""
        try:
            if self._nbbo_worker is None:
                return
            if self._nbbo_stop is not None:
                self._nbbo_stop.set()
            self._nbbo_worker.join(timeout=timeout)
        except Exception:
            pass

    def set_watchlist_commit(self, commit, file_sha256=None):
        """🔬 P1.4/P1-4: يُحدَّث عند كل تحديث قائمة (_fresh_watchlist). المرشّح اللاحق يختم
        commit **و**SHA المحتوى (إثبات أن نفس bytes استُخدمت)."""
        try:
            if commit:
                self.watchlist_commit_current = str(commit)
            if file_sha256:
                self.watchlist_file_sha256_current = str(file_sha256)
        except Exception:
            pass

    # ── مساعِدات داخلية ────────────────────────────────────────────────────
    def _sym(self, symbol):
        ss = self.symbols.get(symbol)
        if ss is None:
            ss = _new_symbol_session(self.session_date, symbol)
            self.symbols[symbol] = ss
        return ss

    def _append(self, fh, obj):
        try:
            fh.write(json.dumps(obj, ensure_ascii=False) + "\n")
            fh.flush()
        except Exception:
            pass

    def _cur_candidate(self, symbol):
        """آخر candidate لهذا الرمز في نفس الدورة (الأحداث 05..11 تلي 04 لنفس الرمز)."""
        cid = self.symbols.get(symbol, {}).get("_cur_cand")
        return self.candidates.get(cid) if cid else None

    # ── مقبض الأحداث (يُمرَّر لـscan_ignition) ─────────────────────────────
    def trace(self, event, payload):
        """مقبض trace — فاشل-آمن مطلق (لا يرفع أبدًا)."""
        try:
            self._handle(event, payload or {})
        except Exception:
            pass

    def _handle(self, event, p):
        symbol = p.get("symbol")
        if not symbol:
            return
        now = _utcnow_iso()
        ss = self._sym(symbol)
        if ss["first_seen_at"] is None:
            ss["first_seen_at"] = now
        ss["last_seen_at"] = now

        if event == "01_SEEN_ACTIVE":
            ss["active_polls"] += 1
        elif event == "02_LEVEL_AVAILABLE":
            ss["level_available_polls"] += 1
            ss["break_level_last"] = p.get("break_level")
            if ss["break_level_first"] is None:
                ss["break_level_first"] = p.get("break_level")
                ss["break_level_source_first"] = p.get("break_level_source")
        elif event == "03_BARS_FETCH":
            ss["bars_attempted"] += 1
            if p.get("bars_ok"):
                ss["bars_ok"] += 1
            else:
                ss["bars_failed"] += 1
            if p.get("first_bar_t") is not None and ss["first_bar_ts"] is None:
                ss["first_bar_ts"] = p.get("first_bar_t")
            if p.get("last_bar_t") is not None:
                ss["last_bar_ts"] = p.get("last_bar_t")
            if p.get("bars"):                     # 🔬 §10: مسار الدقيقة (دِدوب symbol+t)
                self.record_minute_path(symbol, p.get("bars"))
        elif event == "04_RAW_IGNITION":
            ss["raw_candidate_count"] += 1
            self._start_candidate(symbol, now, p)
        elif event == "05_OPERATOR_MEASURED":
            self._patch_candidate(symbol, {
                "operator_status": ("measured" if p.get("operator_status") == "measured"
                                    else p.get("operator_status") or "unavailable"),
                "operator_has_operator": p.get("has_operator"),
                "operator_buy_block_shares": p.get("buy_block_shares"),
                "operator_bid_block_shares": p.get("bid_block_shares")})
            # 🔬 P1.3: NBBO من operator_flow يُخزَّن كمصدر operator (يصبح الأساسي فقط لو
            # measurement غائب). measurement (لو جُلب) ضُبط أصلًا في _start_candidate.
            self._apply_nbbo_source(self._cur_candidate(symbol), "operator",
                                    p.get("nbbo_bid"), p.get("nbbo_ask"), p.get("quote_ts"))
        elif event == "08_OPERATOR_UNAVAILABLE":
            ss["operator_unavailable_count"] += 1
            self._patch_candidate(symbol, {"operator_status": "unavailable"})
        elif event == "06_OPERATOR_PASS":
            ss["operator_pass_count"] += 1
            self._patch_candidate(symbol, {"operator_status": "pass", "fallback_status": "not_used"})
        elif event == "07_OPERATOR_FAIL":
            ss["operator_fail_count"] += 1
            self._patch_candidate(symbol, {"operator_status": "fail", "fallback_status": "not_used",
                                           "gate_decision": "suppress_operator", "alert_emitted": False,
                                           "gate_decision_at_ms": _utcnow_ms()})
            self._flush_candidate(symbol)
        elif event == "09_FALLBACK_PASS":
            ss["fallback_pass_count"] += 1
            self._patch_candidate(symbol, {"fallback_status": "pass"})
        elif event == "10_FALLBACK_FAIL":
            ss["fallback_fail_count"] += 1
            self._patch_candidate(symbol, {"fallback_status": "fail",
                                           "gate_decision": "suppress_group", "alert_emitted": False,
                                           "gate_decision_at_ms": _utcnow_ms()})
            self._flush_candidate(symbol)
        elif event == "11_ALERT_EMITTED":
            ss["emitted_count"] += 1
            self._patch_candidate(symbol, {"gate_decision": "emit", "alert_emitted": True})
            # 🔬 P1.5: زمن الإصدار = لحظة قرار البوّابة (emit) + latency القرار.
            cand = self._cur_candidate(symbol)
            if cand is not None:
                em = _utcnow_ms()
                cand["emitted_at_ms"] = em
                cand["gate_decision_at_ms"] = em
                if cand.get("detected_at_ms") is not None and em is not None:
                    cand["decision_latency_ms"] = int(em - cand["detected_at_ms"])
            self._flush_candidate(symbol)

    def _start_candidate(self, symbol, now, p):
        # 🔬 §2c: Polygon `t` = **بداية** شمعة الدقيقة (لا نهايتها). نسجّل البداية صراحةً
        # ونشتقّ النهاية = البداية + 60000، ونحسب bar_is_closed حتميًّا وقت القرار.
        start = p.get("trigger_bar_start")
        try:
            start = float(start) if start is not None else None
        except (TypeError, ValueError):
            start = None
        end = (start + BAR_INTERVAL_MS) if start is not None else None
        now_ms = _utcnow_ms()
        bar_is_closed = bool(now_ms is not None and end is not None and now_ms >= end)
        bl = p.get("break_level")
        cid = "%s|%s|%s|%s" % (self.session_date, symbol, end, bl)   # end = معرّف الشمعة الثابت
        if cid in self.candidates:
            self.symbols[symbol]["_cur_cand"] = cid
            return                                   # دِدوب: نفس شمعة الاشتعال ونفس الحاجز
        cand = {
            "schema_version": SCHEMA_VERSION, "session_date": self.session_date, "symbol": symbol,
            "segment": self.segment,
            "candidate_id": cid, "source_commit": self.meta.get("source_commit"),
            # 🔬 P1.4/P1-4: commit + SHA محتوى القائمة وقت الترشيح (إثبات نفس bytes).
            "watchlist_commit_start": self.meta.get("watchlist_commit_start"),
            "watchlist_commit_at_candidate": self.watchlist_commit_current,
            "watchlist_file_sha256_at_candidate": self.watchlist_file_sha256_current,
            "break_level": bl, "break_level_source": p.get("break_level_source"),
            "pivot": p.get("pivot"), "stop": p.get("stop"),
            "t1": p.get("t1"), "t2": p.get("t2"), "t3": p.get("t3"),
            "trigger_bar_start": start, "trigger_bar_end": end,
            "bar_is_closed": bar_is_closed, "detected_at": now, "detected_at_ms": now_ms,
            "telegram_attempted_at": None, "telegram_sent_at": None,
            "signal_price": p.get("signal_price"), "vol_x": p.get("vol_x"),
            "signal_usd": p.get("signal_usd"), "candle_class": p.get("candle_class"),
            "operator_status": None, "operator_has_operator": None,
            "operator_bid_block_shares": None, "operator_buy_block_shares": None,
            # 🔬 P1.3: NBBO قياسي مستقلّ (measurement) + NBBO operator (من operator_flow) — منفصلان.
            "measurement_nbbo_bid": None, "measurement_nbbo_ask": None, "measurement_nbbo_mid": None,
            "measurement_spread_pct_mid": None, "measurement_quote_ts_raw": None,
            "measurement_quote_ts_ms": None, "measurement_quote_age_ms": None,
            "measurement_executable": None,
            # 🔬 P0-1/P1.5: حالة NBBO القياسي (لا-تزامني) + توقيت الجلب (الصلاحية من طابع المصدر
            # لا انتهاء HTTP). not_requested = بلا جالب · pending = طُلب ولم يعُد بعد.
            "measurement_nbbo_status": ("pending" if self.nbbo_fetcher is not None else "not_requested"),
            "quote_request_started_at_ms": None, "quote_received_at_ms": None, "quote_capture_lag_ms": None,
            "operator_nbbo_bid": None, "operator_nbbo_ask": None, "operator_nbbo_mid": None,
            "operator_spread_pct_mid": None, "operator_quote_ts_raw": None,
            "operator_quote_ts_ms": None, "operator_quote_age_ms": None, "operator_executable": None,
            # مرآة «الأساسي» (يفضّل measurement) + مصدره — توافق خلفي مع المدقّق/الاختبارات.
            "nbbo_source": None, "nbbo_bid": None, "nbbo_ask": None, "nbbo_mid": None,
            "spread_pct_mid": None, "quote_timestamp_raw": None, "quote_timestamp": None,
            "quote_age_ms": None, "primary_executable": None,
            "fallback_status": "not_used", "gate_decision": None, "gate_decision_at_ms": None,
            "alert_emitted": False, "telegram_delivered": None,
            # 🔬 P1.5/P1-3: زمنيات + **تفكيك latency** (bar→raw→gate→attempt→success).
            "raw_signal_computed_at_ms": now_ms, "emitted_at_ms": None,
            "telegram_attempted_at_ms": None, "telegram_sent_at_ms": None,
            "decision_latency_ms": None, "delivery_latency_ms": None,
            "bar_end_to_raw_signal_ms": None, "raw_signal_to_gate_decision_ms": None,
            "gate_decision_to_telegram_attempt_ms": None, "telegram_attempt_to_success_ms": None,
            "bar_end_to_telegram_success_ms": None,
        }
        self.candidates[cid] = cand
        self.symbols[symbol]["_cur_cand"] = cid
        # 🔬 P0-1: طلب NBBO القياسي **لا-تزامنيًّا** (لا ينتظره التنبيه). يُربط لاحقًا بـcandidate_id.
        self._enqueue_nbbo(cid, symbol)

    def _patch_candidate(self, symbol, fields):
        cand = self._cur_candidate(symbol)
        if cand is not None:
            for k, v in fields.items():
                if v is not None or cand.get(k) is None:
                    cand[k] = v

    def _apply_nbbo_source(self, cand, src, bid, ask, quote_raw, _locked=False):
        """🔬 P1.3: يخزّن مقاييس NBBO لمصدرٍ (measurement|operator) في حقول `{src}_*`، ويضبط
        «الأساسي» (primary_executable + nbbo_source + المرآة). **measurement مفضَّل**: يضبط الأساسي
        دائمًا لو له NBBO؛ operator يضبطه **فقط** لو الأساسي فارغ. **آمن-خيوط** (القفل يمنع سباق
        الـworker اللا-تزامني مع الخيط الرئيسي على المرآة). قياس فقط."""
        if cand is None:
            return
        if not _locked:                       # الخيط الرئيسي (operator) — اقفل ثم أعد الدخول
            with self._lock:
                self._apply_nbbo_source(cand, src, bid, ask, quote_raw, _locked=True)
            return
        m = _nbbo_metrics(bid, ask, quote_raw, _utcnow_ms())
        cand["%s_nbbo_bid" % src] = bid
        cand["%s_nbbo_ask" % src] = ask
        cand["%s_nbbo_mid" % src] = m["mid"]
        cand["%s_spread_pct_mid" % src] = m["spread_pct_mid"]
        cand["%s_quote_ts_raw" % src] = quote_raw
        cand["%s_quote_ts_ms" % src] = m["quote_ts_ms"]
        cand["%s_quote_age_ms" % src] = m["quote_age_ms"]
        cand["%s_executable" % src] = m["executable"]
        has_nbbo = (bid is not None or ask is not None)
        if has_nbbo and (src == "measurement" or cand.get("nbbo_source") is None):
            cand["nbbo_source"] = src
            cand["nbbo_bid"], cand["nbbo_ask"], cand["nbbo_mid"] = bid, ask, m["mid"]
            cand["spread_pct_mid"] = m["spread_pct_mid"]
            cand["quote_timestamp_raw"] = quote_raw
            cand["quote_timestamp"] = m["quote_ts_ms"]
            cand["quote_age_ms"] = m["quote_age_ms"]
            cand["primary_executable"] = m["executable"]

    def _flush_candidate(self, symbol):
        """crash-safe: يُلحق الـcandidate عند وصوله قرار البوّابة النهائي (مع flush). القفل يمنع
        قراءة الـdict أثناء تعديل الـworker اللا-تزامني له (النسخة النهائية تُكتب في finalize)."""
        cand = self._cur_candidate(symbol)
        if cand is not None and self._cand_fh is not None and not cand.get("_flushed"):
            cand["_flushed"] = True
            with self._lock:
                snap = {k: v for k, v in cand.items() if not k.startswith("_")}
            self._append(self._cand_fh, snap)

    @staticmethod
    def _decompose_latencies(cand):
        """🔬 P1-3: يفكّك التأخير: bar→raw · raw→gate · gate→attempt · attempt→success · bar→success.
        لا يخلط latency الشمعة بـlatency القرار. فاشل-آمن (None عند نقص أي طرف)."""
        def _d(a, b):
            try:
                return int(a - b) if (a is not None and b is not None) else None
            except (TypeError, ValueError):
                return None
        be, raw = cand.get("trigger_bar_end"), cand.get("raw_signal_computed_at_ms")
        gate = cand.get("gate_decision_at_ms")
        att, sent = cand.get("telegram_attempted_at_ms"), cand.get("telegram_sent_at_ms")
        cand["bar_end_to_raw_signal_ms"] = _d(raw, be)
        cand["raw_signal_to_gate_decision_ms"] = _d(gate, raw)
        cand["gate_decision_to_telegram_attempt_ms"] = _d(att, gate)
        cand["telegram_attempt_to_success_ms"] = _d(sent, att)
        cand["bar_end_to_telegram_success_ms"] = _d(sent, be)

    # ── تسليم Telegram (emitted ≠ delivered، SPEC §4) ──────────────────────
    def telegram_attempt(self, rows):
        try:
            now = _utcnow_iso()
            now_ms = _utcnow_ms()
            for sym in self._row_symbols(rows):
                cand = self._latest_emitted(sym)
                if cand is not None and cand.get("telegram_attempted_at") is None:
                    cand["telegram_attempted_at"] = now
                    cand["telegram_attempted_at_ms"] = now_ms      # 🔬 P1.5
        except Exception:
            pass

    def telegram_success(self, rows):
        self._telegram_result(rows, delivered=True, error_type=None)

    def telegram_failure(self, rows, error_type=None):
        self._telegram_result(rows, delivered=False, error_type=error_type)

    def _telegram_result(self, rows, delivered, error_type):
        try:
            now = _utcnow_iso()
            now_ms = _utcnow_ms()
            for sym in self._row_symbols(rows):
                if delivered:
                    self._sym(sym)["delivered_count"] += 1
                cand = self._latest_emitted(sym)
                if cand is not None:
                    cand["telegram_delivered"] = bool(delivered)
                    if delivered:
                        cand["telegram_sent_at"] = now
                        cand["telegram_sent_at_ms"] = now_ms       # 🔬 P1.5
                        if cand.get("emitted_at_ms") is not None and now_ms is not None:
                            cand["delivery_latency_ms"] = int(now_ms - cand["emitted_at_ms"])
                self._append(self._deliv_fh, {
                    "session_date": self.session_date, "symbol": sym, "delivered": bool(delivered),
                    "error_type": error_type, "at": now})
        except Exception:
            pass

    @staticmethod
    def _row_symbols(rows):
        out = []
        for r in (rows or []):
            try:
                out.append(r[0]["symbol"])
            except Exception:
                pass
        return out

    def _latest_emitted(self, symbol):
        cid = self.symbols.get(symbol, {}).get("_cur_cand")
        cand = self.candidates.get(cid) if cid else None
        return cand if (cand and cand.get("alert_emitted")) else None

    # ── مسار الدقيقة (اختياري) + دورات ─────────────────────────────────────
    def record_minute_path(self, symbol, bars):
        """يُلحق شموع دقيقة جديدة (دِدوب symbol+t) لملف مضغوط. فاشل-آمن."""
        try:
            if not bars:
                return
            path = os.path.join(self.dir, "minute_paths.jsonl.gz")
            new = []
            for b in bars:
                t = b.get("t")
                key = (symbol, t)
                if t is None or key in self._minute_seen:
                    continue
                self._minute_seen.add(key)
                new.append({"session_date": self.session_date, "symbol": symbol, "t": t,
                            "o": b.get("o"), "h": b.get("h"), "l": b.get("l"),
                            "c": b.get("c"), "v": b.get("v")})
            if new:
                with gzip.open(path, "at", encoding="utf-8") as fh:
                    for row in new:
                        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def backfill_emitted(self, fetch_bars, expected_last_bar_ts=None,
                         tolerance_ms=BAR_INTERVAL_MS * 3):
        """🔬 §2b/P1.2: يكمّل **مسار الدقيقة لكل رمز مُنبَّه** من الاشتعال حتى نهاية الجلسة.
        الرادار يتوقّف عن جلب شموع السهم بعد التنبيه (دِدوب) فتُفقَد الحركة اللاحقة اللازمة لتحليل
        النتيجة (T1/ذروة الجلسة). `fetch_bars(symbol)->bars` **محقون** (حيّ = polygon_minute_bars
        نافذة يوم كامل) فيبقى المسجّل بلا شبكة. **يُستدعى بعد الإغلاق (P0-2)** — في الجلسة المجزّأة
        من الـassembler حصريًّا. `expected_last_bar_ts` (بداية آخر شمعة دقيقة قبل الإغلاق) → الحالة
        `success` **فقط** لو وصل المسار إليه (ضمن `tolerance_ms`) وإلّا `partial`. بلا حدّ متوقّع =
        `done_unverified`. **فاشل-آمن · لا يمسّ التنبيه/الدِدوب/الاختيار** (دِدوب symbol+t). يرجّع العدد."""
        n = 0
        try:
            emitted = sorted({c.get("symbol") for c in self.candidates.values()
                              if c.get("alert_emitted") and c.get("symbol")})
            for sym in emitted:
                err = False
                try:
                    bars = fetch_bars(sym)
                except Exception:
                    bars, err = None, True
                before = len(self._minute_seen)
                last_t = None
                if bars:
                    self.record_minute_path(sym, bars)
                    try:
                        last_t = max(b.get("t") for b in bars if b.get("t") is not None)
                    except (ValueError, TypeError):
                        last_t = None
                ss = self._sym(sym)
                ss["backfill_bars_added"] = len(self._minute_seen) - before
                ss["backfill_last_bar_ts"] = last_t if last_t is not None else ss.get("last_bar_ts")
                if err:
                    ss["backfill_status"] = "error"
                elif not bars:
                    ss["backfill_status"] = "empty"
                elif expected_last_bar_ts is not None:
                    reached = (ss["backfill_last_bar_ts"] is not None
                               and ss["backfill_last_bar_ts"] >= expected_last_bar_ts - tolerance_ms)
                    ss["backfill_status"] = "success" if reached else "partial"
                else:
                    ss["backfill_status"] = "done_unverified"
                n += 1
        except Exception:
            pass
        return n

    # ── handoff بين المقاطع (ب+) ───────────────────────────────────────────
    @staticmethod
    def _file_sha256(path):
        try:
            import hashlib
            h = hashlib.sha256()
            with open(path, "rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return None

    def _raw_files_sha256(self):
        out = {}
        for name in ("candidates.jsonl", "deliveries.jsonl", "symbol_sessions.jsonl",
                     "minute_paths.jsonl.gz", "session.json"):
            p = os.path.join(self.dir, name)
            if os.path.exists(p):
                out[name] = self._file_sha256(p)
        return out

    def _emitted_symbols(self):
        return sorted({c.get("symbol") for c in self.candidates.values()
                       if c.get("alert_emitted") and c.get("symbol")})

    def export_handoff(self):
        """🔬 (ب+): يبني handoff المقطع (يُستدعى بعد finalize فالملفّات الخام مكتوبة).
        يُمرَّر لـjob التالي لاستعادة أختام الدِدوب + التسلسل + تحقّق السلامة. فاشل-آمن → {}."""
        try:
            return {
                "schema_version": SCHEMA_VERSION, "session_date": self.session_date,
                "segment": self.segment, "segment_id": self.segment_id,
                "segment_started_at": self.started_at, "segment_ended_at": self.ended_at,
                "expected_segment_start": self.meta.get("expected_segment_start_iso"),
                "expected_segment_end": self.meta.get("expected_segment_end_iso"),
                "source_commit": self.meta.get("source_commit"),
                "watchlist_commit_start": self.meta.get("watchlist_commit_start"),
                "watchlist_commit_end": self.watchlist_commit_current,
                "workflow_run_id": self.meta.get("workflow_run_id"),
                "alerted_symbols": self._emitted_symbols(),
                "candidate_ids": sorted(self.candidates.keys()),
                "last_bar_by_symbol": {s: ss.get("last_bar_ts") for s, ss in self.symbols.items()
                                       if ss.get("last_bar_ts") is not None},
                "symbols_union": sorted(self.symbols.keys()),
                "loops_started": self.loops_started, "loops_completed": self.loops_completed,
                "raw_files_sha256": self._raw_files_sha256(),
                # 🔬 P0-4: hashes حقيقية (سلسلة تحقّق) — لا نص JSON.
                "manifest_sha256": self.manifest_sha256,
                "previous_segment_manifest_sha256": self.meta.get("previous_segment_manifest_sha256"),
            }
        except Exception:
            return {}

    def loop_start(self):
        self.loops_started += 1
        if self.monitoring_started_at is None:     # 🔬 P0-2: أول لفّة = بدء المراقبة الفعلي
            self.monitoring_started_at = _utcnow_iso()

    def mark_first_poll(self):
        """🔬 P0-2: أول poll ناجح (scan فعلي) — لبوّابة تغطية بداية المقطع."""
        if self.first_successful_poll_at is None:
            self.first_successful_poll_at = _utcnow_iso()

    def loop_end(self, checkpoint_every=7, schedule_lag_ms=None, loop_duration_ms=None):
        self.loops_completed += 1
        self.monitoring_ended_at = _utcnow_iso()   # 🔬 P0-3: آخر لفّة = نهاية المراقبة
        # 🔬 P1.6: قياس أثر الأداة نفسها (تأخّر الجدولة + زمن الدورة) — يُلخَّص median/p95.
        if schedule_lag_ms is not None or loop_duration_ms is not None:
            self._loop_timings.append((schedule_lag_ms, loop_duration_ms))
        if checkpoint_every and self.loops_completed % checkpoint_every == 0:
            self._write_session("running")

    # ── الإنهاء (يُستدعى في finally) ───────────────────────────────────────
    def _coverage(self, ss):
        return round(ss["bars_ok"] / max(1, ss["bars_attempted"]), 4)

    def _timing_stats(self):
        """🔬 P1.6: إحصاء أثر الأداة (median/p95 لزمن الدورة + تأخّر الجدولة + نسبة الدورات
        التي تجاوزت interval). فاشل-آمن → dict فارغ القيم."""
        try:
            interval_ms = float(self.meta.get("interval_seconds") or 0) * 1000.0
            durs = sorted(d for _, d in self._loop_timings if d is not None)
            lags = sorted(l for l, _ in self._loop_timings if l is not None)

            def _pct(vals, q):
                if not vals:
                    return None
                i = min(len(vals) - 1, int(round(q * (len(vals) - 1))))
                return round(vals[i], 1)
            over = (sum(1 for d in durs if interval_ms and d > interval_ms) / len(durs)
                    if durs else None)
            return {
                "loop_duration_ms_median": _pct(durs, 0.5), "loop_duration_ms_p95": _pct(durs, 0.95),
                "schedule_lag_ms_median": _pct(lags, 0.5), "schedule_lag_ms_p95": _pct(lags, 0.95),
                "loops_over_interval_ratio": (round(over, 4) if over is not None else None),
                "n_timed_loops": len(durs),
            }
        except Exception:
            return {}

    def _compute_close_gap(self):
        """🔬 §2a: يحسب هل انتهت الجلسة **قبل الإغلاق المتوقّع** (من meta.expected_close_iso)
        بهامش معقول. `ended_before_expected_close`=True لو انتهت أبكر من الإغلاق بأكثر من
        EARLY_CLOSE_MARGIN_MIN دقيقة. **يقيس فقط — لا يمسّ الرادار.**"""
        exp = self.meta.get("expected_close_iso")
        a, b = _iso_epoch_s(self.ended_at), _iso_epoch_s(exp)
        if a is None or b is None:
            return
        self.minutes_short_of_close = round(max(0.0, (b - a) / 60.0), 1)
        self.ended_before_expected_close = bool(a < b - EARLY_CLOSE_MARGIN_MIN * 60)

    def _write_session(self, termination):
        try:
            sess = {
                "schema_version": SCHEMA_VERSION, "session_date": self.session_date,
                "started_at": self.started_at, "ended_at": self.ended_at,
                "termination": termination, "loops_started": self.loops_started,
                "loops_completed": self.loops_completed,
                "symbols_union": sorted(self.symbols.keys()),
                "n_symbols": len(self.symbols),
                "n_candidates": len(self.candidates),
                "measurement_enabled": self.enabled, "alert_logic_version": "unchanged",
                # §2a: أعلام إغلاق الجلسة (تُحسب في finalize؛ None أثناء اللف/بلا expected_close).
                "ended_before_expected_close": self.ended_before_expected_close,
                "minutes_short_of_close": self.minutes_short_of_close,
                # 🔬 (ب+): هوية المقطع · P1.6: أثر الأداة.
                "segment": self.segment, "segment_id": self.segment_id,
                "segment_started_at": self.started_at, "segment_ended_at": self.ended_at,
                "instrumentation_timing": self._timing_stats(),
                # 🔬 P0-2/P0-3: توقيت المراقبة (بدء/نهاية/أول poll ناجح) — لبوّابات التغطية/الفجوة.
                "monitoring_started_at": self.monitoring_started_at,
                "monitoring_ended_at": self.monitoring_ended_at,
                "first_successful_poll_at": self.first_successful_poll_at,
            }
            sess.update(self.meta)
            _atomic_write(os.path.join(self.dir, "session.json"),
                          json.dumps(sess, ensure_ascii=False, indent=2))
        except Exception:
            pass

    def finalize(self, termination="unknown"):
        """يُستدعى في finally: يكتب session/symbol_sessions/candidates(النهائي)/summary/index.
        فاشل-آمن مطلق (لا يرفع)."""
        try:
            self._drain_nbbo()                 # 🔬 P0-1: أنهِ worker NBBO قبل الكتابة (لا سباق)
            # أي طلب NBBO لم يعُد بعد التفريغ = «pending» → «not_received» (يُوسَم لا يُخفى).
            for c in self.candidates.values():
                if c.get("measurement_nbbo_status") == "pending":
                    c["measurement_nbbo_status"] = "not_received"
                self._decompose_latencies(c)   # 🔬 P1-3: تفكيك التأخير قبل الكتابة النهائية
            self.termination = termination if termination in _TERMINATION else "unknown"
            self.ended_at = _utcnow_iso()
            self._compute_close_gap()          # §2a: هل انتهت قبل الإغلاق المتوقّع؟
            # symbol-sessions: coverage + §2e exposure حقيقي + أهلية recall (الشروط الثلاثة).
            lines = []
            _assembled = bool(self.meta.get("assembled"))
            for sym in sorted(self.symbols):
                ss = self.symbols[sym]
                ss["coverage_ratio"] = self._coverage(ss)
                # 🔬 P0-3: الجلسة المدموجة = مجموع فترات المقاطع (محسوب في الدمج، يستبعد الفجوة)؛
                # الجلسة الواحدة = من أول/آخر مشاهدة. لا نعيد الحساب للمدموجة (يخفي الفجوة).
                if not _assembled:
                    ss["exposure_minutes"] = _exposure_minutes(ss.get("first_seen_at"),
                                                               ss.get("last_seen_at"))
                ss["recall_eligible"] = _recall_eligible(
                    ss["active_polls"], ss["coverage_ratio"], ss["exposure_minutes"])
                lines.append(json.dumps({k: v for k, v in ss.items() if not k.startswith("_")},
                                        ensure_ascii=False))
            _atomic_write(os.path.join(self.dir, "symbol_sessions.jsonl"), "\n".join(lines))
            # candidates النهائية (الكاملة مع التسليم) — تحلّ محلّ سجلّ الإلحاق crash-safe
            try:
                if self._cand_fh is not None:
                    self._cand_fh.flush()
                    self._cand_fh.close()
                    self._cand_fh = None
            except Exception:
                pass
            clines = [json.dumps({k: v for k, v in c.items() if not k.startswith("_")},
                                 ensure_ascii=False) for c in self.candidates.values()]
            _atomic_write(os.path.join(self.dir, "candidates.jsonl"), "\n".join(clines))
            try:
                if self._deliv_fh is not None:
                    self._deliv_fh.flush(); self._deliv_fh.close(); self._deliv_fh = None
            except Exception:
                pass
            self._write_session(self.termination)
            self._write_summary()
            self._write_manifest()             # 🔬 P0-4: manifest + hash (بعد كل الملفّات الخام)
        except Exception:
            pass

    def _write_manifest(self):
        """🔬 P0-4: يبني manifest المقطع (canonical JSON + SHA-256 فوق ملفّاته الخام) ويكتبه.
        يُخزَّن `self.manifest_sha256` لحمله في handoff (سلسلة تحقّق). فاشل-آمن."""
        try:
            import ignition_e2_manifest as _man
            mf = _man.build_manifest(
                session_date=self.session_date, segment=self.segment, segment_id=self.segment_id,
                source_commit=self.meta.get("source_commit"),
                workflow_run_id=self.meta.get("workflow_run_id"),
                expected_segment_start=self.meta.get("expected_segment_start_iso"),
                expected_segment_end=self.meta.get("expected_segment_end_iso"),
                alerted_symbols=self._emitted_symbols(), candidate_ids=list(self.candidates.keys()),
                symbols_union=list(self.symbols.keys()),
                loops_started=self.loops_started, loops_completed=self.loops_completed,
                segment_dir=self.dir,
                previous_segment_manifest_sha256=self.meta.get("previous_segment_manifest_sha256"))
            self.manifest_sha256 = _man.write_manifest(self.dir, mf)
        except Exception:
            self.manifest_sha256 = None

    def _write_summary(self):
        """summary صغير قابل للدفع (SPEC §5 ignition_e2_summary.json) + index — لا خام."""
        try:
            emitted = sum(1 for c in self.candidates.values() if c.get("alert_emitted"))
            delivered = sum(ss["delivered_count"] for ss in self.symbols.values())
            # §2e: أهلية recall بالشروط الثلاثة (polls≥20 · coverage≥0.80 · exposure≥60د)
            # المحسوبة في finalize — لا إعادة حساب هنا (exposure غير متاح إلا بعدها).
            eligible = sum(1 for ss in self.symbols.values() if ss.get("recall_eligible"))
            summ = {
                "schema_version": SCHEMA_VERSION, "session_date": self.session_date,
                "termination": self.termination, "loops_completed": self.loops_completed,
                "loops_started": self.loops_started,
                "n_symbols": len(self.symbols), "n_raw_candidates": len(self.candidates),
                "n_emitted": emitted, "n_delivered": delivered,
                "n_recall_eligible_symbol_sessions": eligible,
                "ended_before_expected_close": self.ended_before_expected_close,
                "minutes_short_of_close": self.minutes_short_of_close,
                "operator_pass": sum(ss["operator_pass_count"] for ss in self.symbols.values()),
                "operator_fail": sum(ss["operator_fail_count"] for ss in self.symbols.values()),
                "operator_unavailable": sum(ss["operator_unavailable_count"] for ss in self.symbols.values()),
                "fallback_pass": sum(ss["fallback_pass_count"] for ss in self.symbols.values()),
                "fallback_fail": sum(ss["fallback_fail_count"] for ss in self.symbols.values()),
                "measurement_enabled": self.enabled, "alert_logic_version": "unchanged",
            }
            summ.update({k: v for k, v in self.meta.items()
                         if k in ("source_commit", "workflow_run_id", "run_id",
                                  "expected_open_iso", "expected_close_iso", "deadline_reason")})
            _atomic_write(os.path.join(self.dir, "summary.json"),
                          json.dumps(summ, ensure_ascii=False, indent=2))
            # ملفّان صغيران يجوز دفعهما للريبو (SPEC §5) — فقط للعامل الحيّ (لا الاختبارات).
            if not self.write_repo_index:
                return
            _atomic_write("ignition_e2_summary.json",
                          json.dumps(summ, ensure_ascii=False, indent=2))
            idx = {}
            if os.path.exists("ignition_e2_session_index.json"):
                try:
                    with open("ignition_e2_session_index.json", encoding="utf-8") as fh:
                        idx = json.load(fh) or {}
                except Exception:
                    idx = {}
            idx[self.session_date] = {"n_symbols": summ["n_symbols"],
                                      "n_raw_candidates": summ["n_raw_candidates"],
                                      "n_emitted": emitted, "n_delivered": delivered,
                                      "termination": self.termination}
            _atomic_write("ignition_e2_session_index.json",
                          json.dumps(idx, ensure_ascii=False, indent=2, sort_keys=True))
        except Exception:
            pass
