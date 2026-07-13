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

# حقول candidate المقفولة (منها توقيت §2c/§2d) — نقصها = schema-gap.
CAND_REQUIRED = ["candidate_id", "symbol", "session_date", "break_level",
                 "trigger_bar_start", "trigger_bar_end", "bar_is_closed",
                 "detected_at", "detected_at_ms", "signal_price", "gate_decision", "alert_emitted"]
# 🔬 P0-3/P1.7: سماحية «وصول المسار للإغلاق» + هامش «تغطية النافذة».
CLOSE_PATH_TOLERANCE_MS = 3 * 60_000
WINDOW_MARGIN_MIN = 10
SS_REQUIRED = ["symbol", "active_polls", "bars_attempted", "bars_ok", "coverage_ratio",
               "first_seen_at", "last_seen_at", "raw_candidate_count", "emitted_count",
               "exposure_minutes", "recall_eligible"]
# حدود جودة البيانات لأهلية recall (SPEC §7) — **ليست عتبات تداول** (الثلاثة تُطبَّق في المسجّل).
RECALL_MIN_POLLS, RECALL_MIN_COVERAGE, RECALL_MIN_EXPOSURE_MIN = 20, 0.80, 60


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


def analyze_session(sdir):
    sess = _read_json(os.path.join(sdir, "session.json"))
    ss = _read_jsonl(os.path.join(sdir, "symbol_sessions.jsonl"))
    cands = _read_jsonl(os.path.join(sdir, "candidates.jsonl"))
    delivs = _read_jsonl(os.path.join(sdir, "deliveries.jsonl"))
    minute = _read_jsonl_gz(os.path.join(sdir, "minute_paths.jsonl.gz"))
    # نوع الوحدة: segment (جزء) · assembled (مدموجة) · single (جلسة واحدة قديمة).
    kind = "assembled" if sess.get("assembled") else ("segment" if sess.get("segment") else "single")
    is_session = (kind != "segment")        # فقط الجلسة الكاملة تخضع لـsession_complete
    # اكتمال الـschema
    ss_missing = sum(1 for r in ss for k in SS_REQUIRED if k not in r)
    cand_missing = sum(1 for c in cands for k in CAND_REQUIRED if k not in c)
    eligible = [r for r in ss if r.get("recall_eligible")]
    cov_vals = sorted(r.get("coverage_ratio", 0) for r in ss)
    med_cov = cov_vals[len(cov_vals) // 2] if cov_vals else 0.0
    # funnel
    emitted_cands = [c for c in cands if c.get("alert_emitted")]
    emitted = len(emitted_cands)
    delivered = sum(1 for d in delivs if d.get("delivered"))
    executable = sum(1 for c in cands if c.get("primary_executable"))
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
    term = sess.get("termination")
    if term != "normal":
        reasons.append(f"termination={term}")
    ls, lc = sess.get("loops_started"), sess.get("loops_completed")
    if ls is not None and lc is not None and ls != lc:
        reasons.append(f"loops_mismatch({ls}≠{lc})")
    if ss_missing or cand_missing:
        reasons.append("schema_gaps")
    if with_ts != len(cands):
        reasons.append("missing_locked_timestamps")
    emitted_syms = {c.get("symbol") for c in emitted_cands}
    deliv_syms = {d.get("symbol") for d in delivs if d.get("delivered")}
    if delivered > emitted or not deliv_syms.issubset(emitted_syms):
        reasons.append("emitted_delivered_contradiction")
    unresolved_nbbo = [c.get("symbol") for c in emitted_cands
                       if c.get("operator_status") == "pass" and c.get("primary_executable") is None]
    if unresolved_nbbo:
        reasons.append("unresolved_nbbo(%s)" % ",".join(sorted(set(unresolved_nbbo))))
    if sess.get("alert_logic_version") != "unchanged":
        reasons.append("alert_logic_version_changed")

    if kind == "segment":
        # segment_complete: غطّى نافذته المقصودة (وصل ~ نهاية المقطع) + كل رمز مُنبَّه له بار لاحق.
        if _ended_before(sess.get("segment_ended_at") or sess.get("ended_at"),
                         sess.get("expected_segment_end_iso"), WINDOW_MARGIN_MIN):
            reasons.append("segment_window_not_covered")
        lost = [c.get("symbol") for c in emitted_cands
                if c.get("trigger_bar_start") is not None
                and max_t.get(c.get("symbol"), c["trigger_bar_start"]) <= c["trigger_bar_start"]]
        if lost:
            reasons.append("lost_post_alert_path(%s)" % ",".join(sorted(set(lost))))
    else:
        # session_complete: انتهت للإغلاق + المسارات تصل للإغلاق (P0-3/P1.7) + (المدموجة) الجزآن.
        if sess.get("ended_before_expected_close"):
            reasons.append("ended_before_expected_close(%s د)" % sess.get("minutes_short_of_close"))
        close_ms = _iso_epoch_s(sess.get("expected_close_iso"))
        close_ms = int(close_ms * 1000) if close_ms is not None else None
        if close_ms is not None:
            target = close_ms - 60_000 - CLOSE_PATH_TOLERANCE_MS
            not_reaching = [c.get("symbol") for c in emitted_cands
                            if c.get("symbol") is not None
                            and max_t.get(c.get("symbol"), -1) < target]
            if not_reaching:
                reasons.append("path_not_reaching_close(%s)" % ",".join(sorted(set(not_reaching))))
        elif emitted_cands:
            reasons.append("expected_close_unknown")   # لا يمكن إثبات وصول المسار
        if kind == "assembled":
            segs = sess.get("segments") or []
            roles = {s.get("role") for s in segs}
            if not ({"open", "close"} <= roles):
                reasons.append("missing_segment(%s)" % ",".join(sorted(roles)) or "none")
            bad = [s.get("role") for s in segs if s.get("termination") != "normal"]
            if bad:
                reasons.append("segment_not_normal(%s)" % ",".join(str(x) for x in bad))

    complete = (not reasons)
    return {
        "session_date": sess.get("session_date"), "kind": kind, "termination": term,
        "loops_started": ls, "loops_completed": lc,
        "deadline_reason": sess.get("deadline_reason"),
        "ended_before_expected_close": sess.get("ended_before_expected_close"),
        "minutes_short_of_close": sess.get("minutes_short_of_close"),
        "n_symbols": len(ss), "n_candidates": len(cands),
        "n_emitted": emitted, "n_delivered": delivered, "n_executable": executable,
        "recall_eligible_symbol_sessions": len(eligible), "median_coverage": round(med_cov, 3),
        "schema_gaps_symbol_sessions": ss_missing, "schema_gaps_candidates": cand_missing,
        "candidates_with_timestamps": with_ts, "candidates_with_gate_decision": with_gate,
        "alert_logic_version": sess.get("alert_logic_version"),
        "incomplete_reasons": reasons,
        # segment → segment_complete · session → session_complete
        "segment_complete": (complete if kind == "segment" else None),
        "session_complete": (complete if is_session else None),
        "complete": complete,
    }


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
        _label = "segment_complete" if r["kind"] == "segment" else "session_complete"
        verdict = ("✅ %s" % _label) if r["complete"] else ("⚠️ غير مكتملة: " + " · ".join(r["incomplete_reasons"]))
        print(f"    منطق التنبيه: {r['alert_logic_version']} · الحكم: {verdict}")
    print("\n" + "=" * 78)
    print(f"📋 وحدات مُسجَّلة={len(sessions)} · session_complete={total_complete}. "
          f"بوّابة E2-A (SPEC §18): {'✅ عيّنة قابلة للتقييم' if total_complete >= 5 else 'تتراكم (المطلوب 5 جلسات session_complete)'}.")
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
