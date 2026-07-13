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

SCHEMA_VERSION = 2                 # 🔬 §2c/2d/2e: توقيت الشمعة + عمر NBBO + exposure
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
        # §2e: exposure حقيقي + أهلية recall (تُحسب في finalize) · §2b: أعلام الردم البعدي.
        "exposure_minutes": 0.0, "recall_eligible": False,
        "backfilled": False, "backfill_bars_added": 0,
    }


class IgnitionMeasurementRecorder:
    """مسجّل القياس الظلّي. الاستعمال:
        rec = IgnitionMeasurementRecorder(session_date, meta={...})
        rows = scan_ignition(wl, today, trace=rec.trace)
        rec.telegram_attempt(rows); rec.telegram_success(rows) / rec.telegram_failure(rows, err)
        ... (في finally) rec.finalize(termination="normal")
    كل دالّة فاشلة-آمنة (لا ترفع) فلا تُسقط الرادار."""

    def __init__(self, session_date, out_root="e2_measurement", meta=None,
                 write_repo_index=False):
        self.session_date = session_date
        self.dir = os.path.join(out_root, "session_%s" % session_date)
        self.meta = dict(meta or {})
        # الملفّان الصغيران القابلان للدفع للريبو (SPEC §5) يُكتبان في جذر العمل **فقط** حين
        # يطلبها العامل الحيّ صراحةً (write_repo_index=True) — الاختبارات لا تلوّث الريبو.
        self.write_repo_index = bool(write_repo_index)
        self.symbols = {}          # symbol -> symbol-session dict
        self.candidates = {}       # candidate_id -> candidate dict (دِدوب بالذاكرة)
        self._minute_seen = set()  # (symbol, t) لدِدوب مسار الدقيقة
        self.loops_started = 0
        self.loops_completed = 0
        self.started_at = _utcnow_iso()
        self.ended_at = None
        self.termination = "unknown"
        # §2a: هل انتهت الجلسة قبل الإغلاق المتوقّع (يُحسب في finalize من meta.expected_close_iso).
        self.ended_before_expected_close = None
        self.minutes_short_of_close = None
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
                "operator_bid_block_shares": p.get("bid_block_shares"),
                "nbbo_bid": p.get("nbbo_bid"), "nbbo_ask": p.get("nbbo_ask"),
                "quote_timestamp_raw": p.get("quote_ts")})   # §2d: الخام كما ورد (provenance)
            self._compute_nbbo(symbol)
        elif event == "08_OPERATOR_UNAVAILABLE":
            ss["operator_unavailable_count"] += 1
            self._patch_candidate(symbol, {"operator_status": "unavailable"})
        elif event == "06_OPERATOR_PASS":
            ss["operator_pass_count"] += 1
            self._patch_candidate(symbol, {"operator_status": "pass", "fallback_status": "not_used"})
        elif event == "07_OPERATOR_FAIL":
            ss["operator_fail_count"] += 1
            self._patch_candidate(symbol, {"operator_status": "fail", "fallback_status": "not_used",
                                           "gate_decision": "suppress_operator", "alert_emitted": False})
            self._flush_candidate(symbol)
        elif event == "09_FALLBACK_PASS":
            ss["fallback_pass_count"] += 1
            self._patch_candidate(symbol, {"fallback_status": "pass"})
        elif event == "10_FALLBACK_FAIL":
            ss["fallback_fail_count"] += 1
            self._patch_candidate(symbol, {"fallback_status": "fail",
                                           "gate_decision": "suppress_group", "alert_emitted": False})
            self._flush_candidate(symbol)
        elif event == "11_ALERT_EMITTED":
            ss["emitted_count"] += 1
            self._patch_candidate(symbol, {"gate_decision": "emit", "alert_emitted": True})
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
            "candidate_id": cid, "source_commit": self.meta.get("source_commit"),
            "watchlist_commit": self.meta.get("watchlist_source_commit_start"),
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
            "nbbo_bid": None, "nbbo_ask": None, "nbbo_mid": None, "spread_pct_mid": None,
            "quote_timestamp_raw": None, "quote_timestamp": None, "quote_age_ms": None,
            "primary_executable": None,
            "fallback_status": "not_used", "gate_decision": None,
            "alert_emitted": False, "telegram_delivered": None,
            "decision_latency_ms": None, "delivery_latency_ms": None,
        }
        self.candidates[cid] = cand
        self.symbols[symbol]["_cur_cand"] = cid

    def _patch_candidate(self, symbol, fields):
        cand = self._cur_candidate(symbol)
        if cand is not None:
            for k, v in fields.items():
                if v is not None or cand.get(k) is None:
                    cand[k] = v

    def _compute_nbbo(self, symbol):
        """🔬 §2d: يوحّد طابع NBBO لملّي-UTC، يحسب عمره وقت القرار، ويحسم الصلاحية
        التنفيذية = (NBBO صالح) **و** (طازج ≤5ث). مجهول/قديم/مستقبلي = غير تنفيذي."""
        cand = self._cur_candidate(symbol)
        if cand is None:
            return
        # توحيد الطابع (نانو/مايكرو/ملّي/ثوانٍ → ملّي) + العمر مقابل «الآن» (وقت القياس ≈ القرار).
        q_ms = _normalize_ts_ms(cand.get("quote_timestamp_raw"))
        cand["quote_timestamp"] = q_ms
        age, fresh = _quote_freshness(q_ms, _utcnow_ms())
        cand["quote_age_ms"] = (int(age) if age is not None else None)
        bid, ask = cand.get("nbbo_bid"), cand.get("nbbo_ask")
        valid = False
        try:
            if bid is not None and ask is not None and float(ask) > 0:
                mid = (float(bid) + float(ask)) / 2.0
                cand["nbbo_mid"] = round(mid, 6)
                if mid > 0:
                    cand["spread_pct_mid"] = round((float(ask) - float(bid)) / mid * 100.0, 4)
                # NBBO صالح (SPEC §13.1): ask>0, ask>=bid, سبريد متاح.
                valid = bool(float(ask) >= float(bid) and cand.get("spread_pct_mid") is not None)
        except Exception:
            valid = False
        # تنفيذي أوّلي **فقط** لو NBBO صالح وطازج (§2d): يخرج البائت من تحليل العائد لاحقًا.
        cand["primary_executable"] = bool(valid and fresh)

    def _flush_candidate(self, symbol):
        """crash-safe: يُلحق الـcandidate عند وصوله قرار البوّابة النهائي (مع flush)."""
        cand = self._cur_candidate(symbol)
        if cand is not None and self._cand_fh is not None and not cand.get("_flushed"):
            cand["_flushed"] = True
            self._append(self._cand_fh, {k: v for k, v in cand.items() if not k.startswith("_")})

    # ── تسليم Telegram (emitted ≠ delivered، SPEC §4) ──────────────────────
    def telegram_attempt(self, rows):
        try:
            now = _utcnow_iso()
            for sym in self._row_symbols(rows):
                cand = self._latest_emitted(sym)
                if cand is not None and cand.get("telegram_attempted_at") is None:
                    cand["telegram_attempted_at"] = now
        except Exception:
            pass

    def telegram_success(self, rows):
        self._telegram_result(rows, delivered=True, error_type=None)

    def telegram_failure(self, rows, error_type=None):
        self._telegram_result(rows, delivered=False, error_type=error_type)

    def _telegram_result(self, rows, delivered, error_type):
        try:
            now = _utcnow_iso()
            for sym in self._row_symbols(rows):
                if delivered:
                    self._sym(sym)["delivered_count"] += 1
                cand = self._latest_emitted(sym)
                if cand is not None:
                    cand["telegram_delivered"] = bool(delivered)
                    if delivered:
                        cand["telegram_sent_at"] = now
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

    def backfill_emitted(self, fetch_bars):
        """🔬 §2b: يكمّل **مسار الدقيقة لكل رمز مُنبَّه** من لحظة الاشتعال حتى نهاية الجلسة.
        الرادار يتوقّف عن جلب شموع السهم بعد التنبيه (دِدوب `ignition_alert`) فتُفقَد الحركة
        اللاحقة اللازمة لتحليل النتيجة (T1/ذروة الجلسة). `fetch_bars(symbol)->bars` **محقون**
        (حيّ = polygon_minute_bars بنافذة يوم كامل) فيبقى المسجّل بلا شبكة. يُستدعى **مرة**
        بعد اللف. **فاشل-آمن مطلق · لا يمسّ التنبيه/الدِدوب/الاختيار** (دِدوب symbol+t يمنع
        الازدواج مع ما سُجِّل أثناء اللف). يرجّع عدد الرموز المردومة."""
        n = 0
        try:
            emitted = sorted({c.get("symbol") for c in self.candidates.values()
                              if c.get("alert_emitted") and c.get("symbol")})
            for sym in emitted:
                try:
                    bars = fetch_bars(sym)
                except Exception:
                    bars = None
                before = len(self._minute_seen)
                if bars:
                    self.record_minute_path(sym, bars)
                ss = self._sym(sym)
                ss["backfilled"] = True
                ss["backfill_bars_added"] = len(self._minute_seen) - before
                n += 1
        except Exception:
            pass
        return n

    def loop_start(self):
        self.loops_started += 1

    def loop_end(self, checkpoint_every=7):
        self.loops_completed += 1
        if checkpoint_every and self.loops_completed % checkpoint_every == 0:
            self._write_session("running")

    # ── الإنهاء (يُستدعى في finally) ───────────────────────────────────────
    def _coverage(self, ss):
        return round(ss["bars_ok"] / max(1, ss["bars_attempted"]), 4)

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
            self.termination = termination if termination in _TERMINATION else "unknown"
            self.ended_at = _utcnow_iso()
            self._compute_close_gap()          # §2a: هل انتهت قبل الإغلاق المتوقّع؟
            # symbol-sessions: coverage + §2e exposure حقيقي + أهلية recall (الشروط الثلاثة).
            lines = []
            for sym in sorted(self.symbols):
                ss = self.symbols[sym]
                ss["coverage_ratio"] = self._coverage(ss)
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
        except Exception:
            pass

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
