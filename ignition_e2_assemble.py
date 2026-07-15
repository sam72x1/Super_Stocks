#!/usr/bin/env python3
"""🔬 E2 (ب+) — دامج الجلسة المجزّأة (job3: assemble_e2_session).

يدمج مقطعَي الجلسة (`segment_open` + `segment_close`) → جلسة واحدة نهائية:
- **البارات** دِدوب على `(symbol, t)` · **candidates** دِدوب على `candidate_id` · **deliveries** تُجمَّع.
- **symbol-session counters** تُجمَّع مع `min(first_seen)` و`max(last_seen)` (+ recompute coverage/exposure/recall).
- **backfill نهائي بعد الإغلاق** (P0-2): يجلب مسار الدقيقة الكامل لكل رمز مُنبَّه حتى الإغلاق.
- **وحده** يكتب `summary/index` النهائيين (المقاطع لا تكتبهما).

يُعيد استخدام `IgnitionMeasurementRecorder` (لا تكرار منطق): يُعبّئ حالته من المقاطع ثم
`backfill_emitted` + `finalize`. **قياس/تجميع فقط — لا يمسّ الفرز/التنبيه/الاختيار · لا LOGIC_VERSION.**

تشغيل:  python3 ignition_e2_assemble.py [session_date] [e2_measurement_root]
"""
import gzip
import json
import os
import sys

import ignition_measurement as M

MAX_TRANSITION_GAP_MIN = 10        # 🔬 P0-3: أقصى فجوة انتقال مقبولة (مقفول قبل confirmatory)
# عدّادات symbol-session التي تُجمَّع عبر المقاطع (بقيّة الحقول min/max أو أوّل غير-None).
_SUM_KEYS = ["active_polls", "level_available_polls", "bars_attempted", "bars_ok", "bars_failed",
             "raw_candidate_count", "operator_pass_count", "operator_fail_count",
             "operator_unavailable_count", "fallback_pass_count", "fallback_fail_count",
             "emitted_count", "delivered_count"]


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


_IMMUTABLE = ("break_level", "trigger_bar_start", "trigger_bar_end", "symbol", "session_date")


def _merge_candidate(a, b):
    """🔬 P1-1: دمج candidate **field-wise** (لا «أول ظهور يفوز») عند تكرار candidate_id على حدود
    المقاطع: `alert_emitted`/`telegram_delivered` = OR (لا يُسقَطان) · `gate_decision` emit يفوز
    suppress · غير-None يفوز None · تعارض حقل ثابت يُسجَّل في `merge_conflicts`. نقيّة."""
    out = dict(a)
    for k, v in (b or {}).items():
        if k == "alert_emitted":
            out[k] = bool(a.get(k)) or bool(v)
        elif k == "telegram_delivered":
            out[k] = True if (a.get(k) is True or v is True) else (a.get(k) if a.get(k) is not None else v)
        elif k == "gate_decision":
            out[k] = "emit" if "emit" in (a.get(k), v) else (a.get(k) or v)
        elif k in _IMMUTABLE:
            if a.get(k) is not None and v is not None and a.get(k) != v:
                out["merge_conflicts"] = sorted(set(out.get("merge_conflicts", []) + [k]))
            out[k] = a.get(k) if a.get(k) is not None else v
        else:
            out[k] = a.get(k) if a.get(k) is not None else v
    return out


def _merge_symbol_sessions(session_date, rows):
    """يدمج صفوف symbol-session عبر المقاطع: يجمع العدّادات، `min(first_seen)`/`max(last_seen)`،
    وأوّل/آخر بار. يرجّع dict {symbol: ss}. النوافذ **متقطّعة زمنيًّا** فالجمع دقيق (لا ازدواج)."""
    out = {}
    for r in rows:
        sym = r.get("symbol")
        if not sym:
            continue
        m = out.get(sym)
        if m is None:
            m = M._new_symbol_session(session_date, sym)
            out[sym] = m
        for k in _SUM_KEYS:
            m[k] = (m.get(k) or 0) + (r.get(k) or 0)
        # 🔬 P0-3: exposure = **مجموع** فترات المراقبة (لا max−min الذي يخفي فجوة الانتقال).
        m["exposure_minutes"] = round((m.get("exposure_minutes") or 0.0)
                                      + (r.get("exposure_minutes") or 0.0), 2)
        fs = r.get("first_seen_at")
        if fs and (m["first_seen_at"] is None or fs < m["first_seen_at"]):
            m["first_seen_at"] = fs
        ls = r.get("last_seen_at")
        if ls and (m["last_seen_at"] is None or ls > m["last_seen_at"]):
            m["last_seen_at"] = ls
        fb = r.get("first_bar_ts")
        if fb is not None and (m["first_bar_ts"] is None or fb < m["first_bar_ts"]):
            m["first_bar_ts"] = fb
        lb = r.get("last_bar_ts")
        if lb is not None and (m["last_bar_ts"] is None or lb > m["last_bar_ts"]):
            m["last_bar_ts"] = lb
        if m["break_level_first"] is None and r.get("break_level_first") is not None:
            m["break_level_first"] = r.get("break_level_first")
            m["break_level_source_first"] = r.get("break_level_source_first")
        if r.get("break_level_last") is not None:
            m["break_level_last"] = r.get("break_level_last")
    return out


def _segment_dirs(session_dir):
    """مجلّدات المقاطع الموجودة تحت الجلسة (بالترتيب: open ثم close ثم أيّ آخر)."""
    order = {"open": 0, "close": 1}
    segs = []
    try:
        for d in sorted(os.listdir(session_dir)):
            full = os.path.join(session_dir, d)
            if d.startswith("segment_") and os.path.isdir(full):
                segs.append((order.get(d[len("segment_"):], 9), d[len("segment_"):], full))
    except Exception:
        pass
    return [(role, path) for _, role, path in sorted(segs)]


def assemble(session_date, root="e2_measurement", fetch_bars=None, write_repo_index=True):
    """يدمج مقاطع `session_<date>` ويكتب الجلسة النهائية في جذرها. `fetch_bars(symbol)->bars`
    محقون (حيّ = bot.polygon_minute_bars). يرجّع dict الملخّص أو None لو لا مقاطع. فاشل-آمن."""
    session_dir = os.path.join(root, "session_%s" % session_date)
    seg_dirs = _segment_dirs(session_dir)
    if not seg_dirs:
        return None
    # اجمع الخام من المقاطع
    ss_rows, cand_rows, deliv_rows, minute_rows = [], [], [], []
    seg_meta = []
    for role, sdir in seg_dirs:
        ss_rows += _read_jsonl(os.path.join(sdir, "symbol_sessions.jsonl"))
        cand_rows += _read_jsonl(os.path.join(sdir, "candidates.jsonl"))
        deliv_rows += _read_jsonl(os.path.join(sdir, "deliveries.jsonl"))
        minute_rows += _read_jsonl_gz(os.path.join(sdir, "minute_paths.jsonl.gz"))
        sj = _read_json(os.path.join(sdir, "session.json"))
        seg_meta.append({"role": role, "termination": sj.get("termination"),
                         "loops_started": sj.get("loops_started"),
                         "loops_completed": sj.get("loops_completed"),
                         "segment_started_at": sj.get("segment_started_at"),
                         "segment_ended_at": sj.get("segment_ended_at"),
                         "expected_segment_start_iso": sj.get("expected_segment_start_iso"),
                         "expected_segment_end_iso": sj.get("expected_segment_end_iso"),
                         "ended_before_expected_close": sj.get("ended_before_expected_close"),
                         # 🔬 P0-2/P0-3: توقيت المراقبة الفعلي (لتغطية البداية + فجوة الانتقال).
                         "monitoring_started_at": sj.get("monitoring_started_at"),
                         "monitoring_ended_at": sj.get("monitoring_ended_at"),
                         "first_successful_poll_at": sj.get("first_successful_poll_at"),
                         "expected_open_iso": sj.get("expected_open_iso"),
                         "start_tolerance_min": sj.get("start_tolerance_min"),
                         "session_type": sj.get("session_type")})
    # 🔬 P0-4: تحقّق سلسلة manifest (كل مقطع + السلسلة open→close). الفشل يُسجَّل ويرفضه المدقّق.
    import ignition_e2_manifest as _man
    seg_manifests, manifest_reasons = {}, []
    for role, sdir in seg_dirs:
        mman = _man.read_manifest(sdir)
        seg_manifests[role] = mman
        ok, r = _man.verify_manifest(mman, sdir, expect_session_date=session_date, expect_segment=role)
        if not ok:
            manifest_reasons += ["%s:%s" % (role, x) for x in r]
    if "open" in seg_manifests and "close" in seg_manifests:
        ok, r = _man.verify_chain(seg_manifests["open"], seg_manifests["close"])
        if not ok:
            manifest_reasons += r
    manifest_chain_ok = not manifest_reasons
    # 🔬 P0-3: فجوة الانتقال بين الجوبين (open.monitoring_ended → close.monitoring_started) — غير
    # مراقبة حيًّا (رفع/تنزيل artifact + تجهيز runner). تُقاس وتُقفَل؛ تجاوزها يرفض الجلسة.
    _by_role = {s["role"]: s for s in seg_meta}
    transition_gap_ms = None
    if "open" in _by_role and "close" in _by_role:
        _a = M._iso_epoch_s(_by_role["open"].get("monitoring_ended_at"))
        _b = M._iso_epoch_s(_by_role["close"].get("monitoring_started_at"))
        if _a is not None and _b is not None:
            transition_gap_ms = int(max(0.0, _b - _a) * 1000)
    # مصدر meta من مقطع الإغلاق (يحمل الإغلاق المتوقّع) وإلّا أوّل مقطع
    base_sj = _read_json(os.path.join(seg_dirs[-1][1], "session.json")) or \
        _read_json(os.path.join(seg_dirs[0][1], "session.json"))
    expected_close_iso = base_sj.get("expected_close_iso")
    # بنِ recorder للجلسة المدموجة (segment=None → يكتب في جذر session_<date>/)
    # 🔬 P1-8: provenance صادق — نافذة المراقبة (من المقاطع) ≠ وقت التجميع.
    _mon_start = min((s.get("segment_started_at") for s in seg_meta if s.get("segment_started_at")),
                     default=None)
    _mon_end = max((s.get("segment_ended_at") for s in seg_meta if s.get("segment_ended_at")),
                   default=None)
    rec = M.IgnitionMeasurementRecorder(
        session_date, out_root=root, segment=None, write_repo_index=write_repo_index,
        meta={"assembled": True, "segments": seg_meta,
              "expected_open_iso": base_sj.get("expected_open_iso"),
              "expected_close_iso": expected_close_iso,
              "source_commit": base_sj.get("source_commit"),
              "workflow_run_id": base_sj.get("workflow_run_id"),
              "interval_seconds": base_sj.get("interval_seconds"),
              # 🔬 P0-4: نتيجة سلسلة التحقّق (يرفضها المدقّق لو فشلت).
              "manifest_chain_ok": manifest_chain_ok, "manifest_chain_reasons": manifest_reasons,
              # 🔬 P0-3: فجوة الانتقال + حدّها المقفول (يرفضها المدقّق لو تجاوزت).
              "transition_gap_ms": transition_gap_ms,
              "max_transition_gap_min": MAX_TRANSITION_GAP_MIN,
              # 🔬 P1-8: نافذة المراقبة الحقيقية vs وقت التجميع (assembled_at يُملأ في finalize).
              "monitoring_started_at": _mon_start, "monitoring_ended_at": _mon_end})
    rec.meta["assembled_at"] = rec.started_at    # 🔬 P1-8: وقت التجميع (≠ نافذة المراقبة)
    # عبّئ الحالة المدموجة
    rec.symbols = _merge_symbol_sessions(session_date, ss_rows)
    for c in cand_rows:                      # 🔬 P1-1: دمج field-wise (لا يُسقط emitted/delivered)
        cid = c.get("candidate_id")
        if not cid:
            continue
        rec.candidates[cid] = _merge_candidate(rec.candidates[cid], c) if cid in rec.candidates else c
    for d in deliv_rows:                     # deliveries تُجمَّع كما هي
        rec._append(rec._deliv_fh, d)
    # اكتب البارات المدموجة (دِدوب symbol+t) عبر record_minute_path
    by_sym = {}
    for m in minute_rows:
        by_sym.setdefault(m.get("symbol"), []).append(m)
    for sym, bars in by_sym.items():
        rec.record_minute_path(sym, sorted(bars, key=lambda b: (b.get("t") or 0)))
    rec.loops_started = sum((s.get("loops_started") or 0) for s in seg_meta)
    rec.loops_completed = sum((s.get("loops_completed") or 0) for s in seg_meta)
    # 🔬 P0-2: **backfill نهائي بعد الإغلاق** — المسار الكامل لكل رمز مُنبَّه حتى الإغلاق.
    exp_last = None
    _cs = M._iso_epoch_s(expected_close_iso)
    if _cs is not None:
        exp_last = int(_cs * 1000) - M.BAR_INTERVAL_MS   # بداية آخر شمعة دقيقة قبل الإغلاق
    if fetch_bars is not None:
        rec.backfill_emitted(fetch_bars, expected_last_bar_ts=exp_last)
    # الإنهاء المدموج = normal فقط لو كل المقاطع انتهت طبيعيًّا (وإلّا exception) — الاكتمال
    # التفصيلي (وصول المسار للإغلاق · الجزآن) يحكمه المدقّق (session_complete).
    seg_terms = [s.get("termination") for s in seg_meta]
    merged_term = "normal" if seg_terms and all(t == "normal" for t in seg_terms) else "exception"
    rec.finalize(termination=merged_term)
    summ = _read_json(os.path.join(session_dir, "summary.json"))
    return summ or {"session_date": session_date, "assembled": True}


def main():
    session_date = sys.argv[1] if len(sys.argv) > 1 else None
    root = sys.argv[2] if len(sys.argv) > 2 else "e2_measurement"
    # جالب البارات الحيّ (بعد الإغلاق) — فاشل-آمن؛ بلا bot/مفتاح = بلا backfill (المسار من المقاطع).
    fetch, bot = None, None
    try:
        try:
            import Super_stock as bot
        except ImportError:
            import super_stock as bot
        fetch = lambda sym: bot.polygon_minute_bars(sym, minutes=480)
    except Exception:
        bot = None
        fetch = None
    if not session_date:
        try:
            cands = sorted(d for d in os.listdir(root) if d.startswith("session_"))
            session_date = cands[-1][len("session_"):] if cands else None
        except Exception:
            session_date = None
    if not session_date:
        print("📋 لا جلسة للدمج.")
        return
    summ = assemble(session_date, root=root, fetch_bars=fetch)
    if summ is None:
        print(f"📋 لا مقاطع segment_* تحت session_{session_date} — لا شيء للدمج.")
        return
    print("=" * 70)
    print(f"🔬 E2 assembler: دُمجت جلسة {session_date}")
    print(f"    رموز={summ.get('n_symbols')} · candidates={summ.get('n_raw_candidates')} "
          f"· emitted={summ.get('n_emitted')} · delivered={summ.get('n_delivered')}")
    print(f"    recall-eligible={summ.get('n_recall_eligible_symbol_sessions')} "
          f"· الإنهاء={summ.get('termination')}")
    print("=" * 70)
    # 🔬 P1-7: الـassembler **وحده** يولّد السجلّ القديم (ignition_log/universe) من البيانات
    # المدموجة (الإطلاقات = candidates المُصدَرة) — الـworkflow يدفعه مرة واحدة. فاشل-آمن.
    try:
        if bot is None:
            raise RuntimeError("bot غير متاح")
        session_dir = os.path.join(root, "session_%s" % session_date)
        cands = _read_jsonl(os.path.join(session_dir, "candidates.jsonl"))
        ss = _read_jsonl(os.path.join(session_dir, "symbol_sessions.jsonl"))
        fires = [({"symbol": c.get("symbol"), "stop": [c.get("stop")], "t1": c.get("t1"),
                   "pivot": c.get("pivot"), "last_price": c.get("signal_price"),
                   "interp": {"critical_number": {"price": c.get("break_level")}}},
                  {"price": c.get("signal_price"), "vol_x": c.get("vol_x"), "usd": c.get("signal_usd")},
                  None) for c in cands if c.get("alert_emitted")]
        if fires:
            bot.record_ignition_fires(fires, session_date)
        bot.record_ignition_universe(sorted({r.get("symbol") for r in ss if r.get("symbol")}), session_date)
    except Exception as e:
        print(f"⚠️ توليد السجلّ القديم: {e}")
    # شغّل المدقّق على الجذر المدموج (session_complete)
    try:
        import ignition_e2_analyze as A
        r = A.analyze_session(os.path.join(root, "session_%s" % session_date))
        print("مدقّق: complete=%s%s" % (
            r.get("complete"), ("" if r.get("complete") else " · " + " · ".join(r.get("incomplete_reasons", [])))))
    except Exception as e:
        print(f"⚠️ المدقّق: {e}")


if __name__ == "__main__":
    main()
