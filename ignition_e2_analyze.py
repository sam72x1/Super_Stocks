#!/usr/bin/env python3
"""🔬 E2-A — مدقّق تغطية/اكتمال القياس الظلّي (لا معايرة · لا حكم عتبات).

**E2-A حصريًّا (SPEC §18):** يقرأ مخرجات `ignition_measurement` ويتحقّق من: اكتمال الـschema ·
التغطية · عدم فقد البيانات · التوقيت · funnel متّسق. **ممنوع** هنا أي تحليل جودة عتبة/نتيجة/expectancy
(ذلك E2-B/E2-C بعد اكتمال العيّنة + تسجيل مسبق + موافقة المالك). قياس/تدقيق فقط · لا يمسّ الفرز.

تشغيل:  python3 ignition_e2_analyze.py [e2_measurement]
"""
import json
import os
import sys

CAND_REQUIRED = ["candidate_id", "symbol", "session_date", "break_level", "trigger_bar_end",
                 "detected_at", "signal_price", "gate_decision", "alert_emitted"]
SS_REQUIRED = ["symbol", "active_polls", "bars_attempted", "bars_ok", "coverage_ratio",
               "first_seen_at", "last_seen_at", "raw_candidate_count", "emitted_count"]
# حدود جودة البيانات لأهلية recall (SPEC §7) — **ليست عتبات تداول**.
RECALL_MIN_POLLS, RECALL_MIN_COVERAGE = 20, 0.80


def _read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(x) for x in fh if x.strip()]


def _read_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def analyze_session(sdir):
    sess = _read_json(os.path.join(sdir, "session.json"))
    ss = _read_jsonl(os.path.join(sdir, "symbol_sessions.jsonl"))
    cands = _read_jsonl(os.path.join(sdir, "candidates.jsonl"))
    delivs = _read_jsonl(os.path.join(sdir, "deliveries.jsonl"))
    # اكتمال الـschema
    ss_missing = sum(1 for r in ss for k in SS_REQUIRED if k not in r)
    cand_missing = sum(1 for c in cands for k in CAND_REQUIRED if k not in c)
    # التغطية
    eligible = [r for r in ss if r.get("active_polls", 0) >= RECALL_MIN_POLLS
                and r.get("coverage_ratio", 0) >= RECALL_MIN_COVERAGE]
    cov_vals = sorted(r.get("coverage_ratio", 0) for r in ss)
    med_cov = cov_vals[len(cov_vals) // 2] if cov_vals else 0.0
    # funnel
    emitted = sum(1 for c in cands if c.get("alert_emitted"))
    delivered = sum(1 for d in delivs if d.get("delivered"))
    executable = sum(1 for c in cands if c.get("primary_executable"))
    # اتساق: كل candidate له trigger_bar_end + detected_at + gate_decision
    with_ts = sum(1 for c in cands if c.get("trigger_bar_end") is not None
                  and c.get("detected_at") is not None)
    with_gate = sum(1 for c in cands if c.get("gate_decision"))
    return {
        "session_date": sess.get("session_date"), "termination": sess.get("termination"),
        "loops_completed": sess.get("loops_completed"),
        "n_symbols": len(ss), "n_candidates": len(cands),
        "n_emitted": emitted, "n_delivered": delivered, "n_executable": executable,
        "recall_eligible_symbol_sessions": len(eligible), "median_coverage": round(med_cov, 3),
        "schema_gaps_symbol_sessions": ss_missing, "schema_gaps_candidates": cand_missing,
        "candidates_with_timestamps": with_ts, "candidates_with_gate_decision": with_gate,
        "alert_logic_version": sess.get("alert_logic_version"),
    }


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "e2_measurement"
    if not os.path.isdir(root):
        print(f"📋 لا مجلّد قياس بعد: {root} (يُنشأ عند أول جلسة رادار بـE2_MEASUREMENT=1).")
        return
    sessions = sorted(d for d in os.listdir(root) if d.startswith("session_"))
    if not sessions:
        print(f"📋 لا جلسات مُسجَّلة بعد في {root}.")
        return
    print("=" * 78)
    print("🔬 E2-A — تدقيق تغطية/اكتمال القياس الظلّي (لا معايرة عتبات — SPEC §18)")
    print("=" * 78)
    total_complete = 0
    for s in sessions:
        r = analyze_session(os.path.join(root, s))
        clean = (r["schema_gaps_symbol_sessions"] == 0 and r["schema_gaps_candidates"] == 0
                 and r["candidates_with_timestamps"] == r["n_candidates"]
                 and r["candidates_with_gate_decision"] == r["n_candidates"]
                 and r["alert_logic_version"] == "unchanged")
        if r["termination"] == "normal" and clean:
            total_complete += 1
        print(f"\n▸ {r['session_date']} · إنهاء={r['termination']} · دورات={r['loops_completed']}")
        print(f"    رموز={r['n_symbols']} · candidates={r['n_candidates']} "
              f"(نُفِّذ NBBO={r['n_executable']}) · emitted={r['n_emitted']} · delivered={r['n_delivered']}")
        print(f"    recall-eligible symbol-sessions={r['recall_eligible_symbol_sessions']} "
              f"· وسيط التغطية={r['median_coverage']}")
        print(f"    اكتمال schema: ثغرات symbol-session={r['schema_gaps_symbol_sessions']} "
              f"· ثغرات candidate={r['schema_gaps_candidates']} "
              f"· بالطوابع={r['candidates_with_timestamps']}/{r['n_candidates']} "
              f"· ببوّابة={r['candidates_with_gate_decision']}/{r['n_candidates']}")
        print(f"    منطق التنبيه: {r['alert_logic_version']} · اكتمال الجلسة: {'✅' if clean else '⚠️'}")
    print("\n" + "=" * 78)
    print(f"📋 جلسات مُسجَّلة={len(sessions)} · مكتملة نظيفة={total_complete}. "
          f"بوّابة E2-A (SPEC §18): {'✅ عيّنة قابلة للتقييم' if total_complete >= 5 else 'تتراكم (المطلوب 5 جلسات كاملة)'}.")
    print("⚠️ E2-A: قياس فقط — لا معايرة/حكم عتبات (E2-B/C بعد العيّنة + تسجيل مسبق + موافقة المالك).")
    print("=" * 78)


if __name__ == "__main__":
    main()
