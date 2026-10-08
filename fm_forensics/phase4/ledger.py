"""🔬 PHASE 4 — سجلُّ الأحداث (§5) ومصفوفةُ الترتيب (§8) وتحليلا اللمستين (§9-10 · §20):
لكلّ وحدةِ فيصل مؤرَّخةٍ ذاتِ شموع: المستوى واللمسةُ الأولى عند يوم القرار (شموعٌ < اليوم) · ثمّ **بعد تجميد الحقول التاريخيّة** تُكشف الأحداثُ الأماميّة
(E2/E3/E4/E5) في أعمدة FWD_ مع FUTURE_REVEAL_DATE. لا حالةَ تُستنتج من النتيجة."""
import collections
import datetime as dt
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p4lib as P                        # noqa: E402

L = P.L
TODAY = dt.date.today().isoformat()


def cmp(a, b):
    if not a or not b:
        return "UNKNOWN"
    return "BEFORE" if a < b else ("SAME" if a == b else "AFTER")


def class_reading(state, st, e3d):
    if state in ("FOCUS", "WATCH"):
        pos = "before" if (e3d and st < e3d) else ("at" if e3d == st else ("after" if e3d else "with no"))
        return f"WATCH/FOCUS declared {pos} retest(E3)"
    pos = "after/at" if (e3d and e3d <= st) else ("before" if e3d else "with no")
    return f"READY/ENTRY declared {pos} retest(E3)"


def main():
    rows = [r for r in P.faisal_timeline() if r["has_bars"]]
    fs = P.first_states(rows)
    ledger, ordering = [], []
    per_ticker = {}
    for r in rows:
        T = r["session"]
        lv = P.level_at(r["ticker"], T)
        safe = P.lookahead_check(r["ticker"], T)
        base = dict(TICKER=r["ticker"], SET=r["set"], DECISION_DATE=T, FAISAL_DATE_RAW=r["date"], DATE_AMBIGUOUS=r["date_ambiguous"], FAISAL_STATE=r["state"],
                    EVIDENCE_ID=r["evidence_id"], EVIDENCE_CLASS=r["evidence_class"], REPEATED_ATTENTION=r["repeated_attention"],
                    DATA_CUTOFF=f"bars < {T}", EVIDENCE_CUTOFF=f"Faisal units dated <= {r['date']}", LOOKAHEAD_SAFE=int(safe))
        if not lv:
            ledger.append(dict(base, EVENT="NO_LEVEL", LEVEL="", PRICE="", TOLERANCE=P.TOL, TOUCH_INDEX="", PREVIOUS_TOUCH_DATE="", DAYS_SINCE_PREVIOUS_TOUCH="",
                               DATA_AVAILABLE_AT_EVENT="insufficient bars", EVIDENCE_SOURCE="bars", FUTURE_REVEAL_DATE=""))
            continue
        ledger.append(dict(base, EVENT="FIRST_TOUCH(E1) of LEVEL(T)", LEVEL=lv["level"], PRICE=lv["level"], TOLERANCE=P.TOL, TOUCH_INDEX=1, PREVIOUS_TOUCH_DATE="",
                           DAYS_SINCE_PREVIOUS_TOUCH="", EVENT_DATE=lv["first_touch"], SESSIONS_FIRST_TOUCH_TO_DECISION=lv["sessions_since"],
                           TOUCHES_AT_DECISION=lv["touches"], DATA_AVAILABLE_AT_EVENT="daily bar closed (observable next session)", EVIDENCE_SOURCE="bars", FUTURE_REVEAL_DATE=""))
        key = (r["ticker"], lv["level"], lv["first_touch"])
        if key not in per_ticker:
            e2 = P.e2_scan(r["ticker"], lv["level"], lv["first_touch"])
            cy = P.cycle_scan(r["ticker"], lv["level"], lv["first_touch"])
            per_ticker[key] = (e2, cy)
        e2, cy = per_ticker[key]
        ledger.append(dict(base, EVENT="SECOND_TOUCH(E2 production tested_level)", LEVEL=lv["level"], PRICE=lv["level"], TOLERANCE=P.TOL, TOUCH_INDEX=2,
                           PREVIOUS_TOUCH_DATE=lv["first_touch"], DAYS_SINCE_PREVIOUS_TOUCH=(L.cal_index(e2["date"]) - L.cal_index(lv["first_touch"])) if e2["date"] else "",
                           EVENT_DATE=e2["date"] or "", FWD_STATUS=e2["status"], FWD_POSITION_VS_DECISION=cmp(e2["date"], T) if e2["date"] else "NEVER",
                           DATA_AVAILABLE_AT_EVENT="bars < event date", EVIDENCE_SOURCE="bars", FUTURE_REVEAL_DATE=TODAY))
        ledger.append(dict(base, EVENT="RETEST(E3 pivot_cycle_state stage>=3)", LEVEL=lv["level"], PRICE=cy.get("sweep_low") or lv["level"], TOLERANCE=P.cfg()["tol"], TOUCH_INDEX="",
                           PREVIOUS_TOUCH_DATE=lv["first_touch"], DAYS_SINCE_PREVIOUS_TOUCH=(L.cal_index(cy["e3"]) - L.cal_index(lv["first_touch"])) if cy["e3"] else "",
                           EVENT_DATE=cy["e3"] or "", FWD_STATUS=(f"E3:{cy['e3_branch']}" if cy["e3"] else (cy["e5_kind"] or "NONE")), FWD_POSITION_VS_DECISION=cmp(cy["e3"], T) if cy["e3"] else "NEVER",
                           FWD_SWEEP_PCT=cy.get("sweep_pct"), LEVEL_MISMATCH=cy["level_mismatch"], DATA_AVAILABLE_AT_EVENT="bars < event date", EVIDENCE_SOURCE="bars", FUTURE_REVEAL_DATE=TODAY))
        ledger.append(dict(base, EVENT="TRIGGER(E4 sweep-reclaim | stability)", LEVEL=lv["level"], PRICE="", TOLERANCE="", TOUCH_INDEX="", PREVIOUS_TOUCH_DATE=cy["e3"] or "",
                           DAYS_SINCE_PREVIOUS_TOUCH=(L.cal_index(cy["e4"]) - L.cal_index(cy["e3"])) if cy["e4"] and cy["e3"] else "", EVENT_DATE=cy["e4"] or "",
                           FWD_STATUS=(f"E4:{cy['e4_branch']}" if cy["e4"] else "NONE"), FWD_POSITION_VS_DECISION=cmp(cy["e4"], T) if cy["e4"] else "NEVER",
                           DATA_AVAILABLE_AT_EVENT="bars < event date", EVIDENCE_SOURCE="bars", FUTURE_REVEAL_DATE=TODAY))
        ledger.append(dict(base, EVENT="BREAK/INVALIDATION(E5)", LEVEL=lv["level"], PRICE="", TOLERANCE=P.cfg()["sweep"], TOUCH_INDEX="", PREVIOUS_TOUCH_DATE="", DAYS_SINCE_PREVIOUS_TOUCH="",
                           EVENT_DATE=cy["e5"] or "", FWD_STATUS=cy["e5_kind"] or "NONE", FWD_POSITION_VS_DECISION=cmp(cy["e5"], T) if cy["e5"] else "NEVER",
                           DATA_AVAILABLE_AT_EVENT="bars < event date", EVIDENCE_SOURCE="bars", FUTURE_REVEAL_DATE=TODAY))
    keys = []
    for r in ledger:
        for k in r:
            if k not in keys:
                keys.append(k)
    ledger = [{k: r.get(k, "") for k in keys} for r in ledger]
    L.write_csv(os.path.join(HERE, "EVENT_LEDGER.csv"), ledger, keys)

    # ---- ordering per ticker (first-state level)
    first_rows = {}
    for r in rows:
        if r["session"] == fs[r["ticker"]]["first_state"] and r["ticker"] not in first_rows:
            first_rows[r["ticker"]] = r
    for t, r in sorted(first_rows.items()):
        T = r["session"]; lv = P.level_at(t, T)
        d = fs[t]
        if not lv:
            ordering.append(dict(TICKER=t, SET=r["set"], FIRST_TOUCH_DATE="", FIRST_STATE_DATE=T, FIRST_STATE_CLASS=r["state"], SECOND_TOUCH_DATE="", RETEST_DATE="",
                                 TRIGGER_DATE="", ENTRY_DATE=d.get("first_entry") or "", READY_DATE=d.get("first_ready") or "", ORDER_RESULT="INSUFFICIENT",
                                 EVIDENCE_QUALITY=r["evidence_class"], LOOKAHEAD_SAFE=int(P.lookahead_check(t, T)), NOTE="no level (insufficient bars)"))
            continue
        e2, cy = per_ticker[(t, lv["level"], lv["first_touch"])]
        ft, st, e2d, e3d, e4d, en, rd = lv["first_touch"], T, e2["date"], cy["e3"], cy["e4"], d.get("first_entry"), d.get("first_ready")
        checks = []
        checks.append(("FT<=STATE", ft <= st))
        if e2d:
            checks.append(("STATE<E2", st < e2d))
        if e3d:
            checks.append(("STATE<E3", st < e3d))
        if e4d and en:
            checks.append(("TRIGGER<=ENTRY", e4d <= en))
        if all(v for _, v in checks) and len(checks) >= 2:
            res = "EXPECTED"
        elif any(not v for _, v in checks):
            res = "CONTRADICTED"
        else:
            res = "INSUFFICIENT"
        ordering.append(dict(TICKER=t, SET=r["set"], FIRST_TOUCH_DATE=ft, FIRST_STATE_DATE=st, FIRST_STATE_CLASS=r["state"], SESSIONS_FT_TO_STATE=lv["sessions_since"],
                             SECOND_TOUCH_DATE=e2d or "", SECOND_TOUCH_STATUS=e2["status"], RETEST_DATE=e3d or "", RETEST_BRANCH=cy["e3_branch"] or "", TRIGGER_DATE=e4d or "",
                             TRIGGER_BRANCH=cy["e4_branch"] or "", BREAK_DATE=cy["e5"] or "", BREAK_KIND=cy["e5_kind"] or "", READY_DATE=rd or "", ENTRY_DATE=en or "",
                             E2_VS_STATE=cmp(e2d, st) if e2d else "NEVER", E3_VS_STATE=cmp(e3d, st) if e3d else "NEVER", E2_VS_READY=cmp(e2d, rd) if (e2d and rd) else ("NEVER" if rd and not e2d else "UNKNOWN"),
                             E3_VS_READY=cmp(e3d, rd) if (e3d and rd) else ("NEVER" if rd and not e3d else "UNKNOWN"), E2_VS_ENTRY=cmp(e2d, en) if (e2d and en) else ("NEVER" if en and not e2d else "UNKNOWN"),
                             E3_VS_ENTRY=cmp(e3d, en) if (e3d and en) else ("NEVER" if en and not e3d else "UNKNOWN"), E4_VS_ENTRY=cmp(e4d, en) if (e4d and en) else ("NEVER" if en and not e4d else "UNKNOWN"),
                             CHECKS=";".join(f"{k}={'ok' if v else 'FAIL'}" for k, v in checks), ORDER_RESULT=res,
                             CLASS_READING=class_reading(r["state"], st, e3d), EVIDENCE_QUALITY=r["evidence_class"] + ("+REPEATED_ATTENTION" if r["repeated_attention"] else ""),
                             DATE_AMBIGUOUS=r["date_ambiguous"], LOOKAHEAD_SAFE=int(P.lookahead_check(t, T)), FUTURE_REVEAL_DATE=TODAY))
    okeys = []
    for r in ordering:
        for k in r:
            if k not in okeys:
                okeys.append(k)
    ordering = [{k: r.get(k, "") for k in okeys} for r in ordering]
    L.write_csv(os.path.join(HERE, "PHASE_ORDERING_MATRIX.csv"), ordering, okeys)

    # ---- §9 first touch → attention (documented states only)
    fta = []
    for grp in ("discovery", "validation", "anchor", "discovery+validation"):
        sel = [o for o in ordering if o["ORDER_RESULT"] != "INSUFFICIENT" or o["FIRST_TOUCH_DATE"]]
        sel = [o for o in sel if (o["SET"] in ("discovery", "validation") if grp == "discovery+validation" else o["SET"] == grp)]
        for target, key in (("FIRST_STATE", "FIRST_STATE_DATE"), ("FOCUS", None), ("WATCH", None), ("READY", "READY_DATE"), ("ENTRY", "ENTRY_DATE")):
            gaps, unknown = [], 0
            for o in sel:
                if not o["FIRST_TOUCH_DATE"]:
                    unknown += 1; continue
                if target in ("FOCUS", "WATCH"):
                    dd = fs[o["TICKER"]].get(f"first_{target.lower()}")
                else:
                    dd = o[key]
                if not dd:
                    unknown += 1; continue
                gaps.append(L.cal_index(dd) - L.cal_index(o["FIRST_TOUCH_DATE"]))
            qq = P.q(gaps)
            fta.append(dict(SET=grp, TARGET=target, N=len(sel), N_EVALUABLE=qq["n"], N_UNKNOWN=unknown, MEDIAN=qq["median"], Q1=qq["q1"], Q3=qq["q3"], MIN=qq["min"], MAX=qq["max"],
                            PROP_POSITIVE=round(sum(1 for g in gaps if g > 0) / len(gaps), 3) if gaps else None, PROP_ZERO=round(sum(1 for g in gaps if g == 0) / len(gaps), 3) if gaps else None,
                            PROP_NEGATIVE=round(sum(1 for g in gaps if g < 0) / len(gaps), 3) if gaps else None,
                            NOTE="sessions from FIRST_TOUCH (of the level in force at the first state date) to the documented state; negative impossible by construction for FIRST_STATE (level measured at that date) — see report"))
    L.write_csv(os.path.join(HERE, "FIRST_TOUCH_ANALYSIS.csv"), fta)

    # ---- §10/§20 second touch role
    sta, role = [], []
    for ev, dkey in (("E2_production", "SECOND_TOUCH_DATE"), ("E3_retest", "RETEST_DATE"), ("E4_trigger", "TRIGGER_DATE")):
        for grp in ("discovery", "validation", "anchor", "discovery+validation"):
            sel = [o for o in ordering if o["FIRST_TOUCH_DATE"] and (o["SET"] in ("discovery", "validation") if grp == "discovery+validation" else o["SET"] == grp)]
            for target in ("FOCUS", "WATCH", "READY", "ENTRY"):
                c = collections.Counter(); gaps = []
                for o in sel:
                    dd = fs[o["TICKER"]].get(f"first_{target.lower()}")
                    if not dd:
                        c["UNKNOWN(no such state)"] += 1; continue
                    e = o[dkey]
                    if not e:
                        c["NEVER"] += 1; continue
                    c[cmp(e, dd)] += 1; gaps.append(L.cal_index(dd) - L.cal_index(e))
                qq = P.q(gaps)
                sta.append(dict(EVENT=ev, SET=grp, TARGET_STATE=target, N=len(sel), BEFORE=c["BEFORE"], SAME=c["SAME"], AFTER=c["AFTER"], NEVER=c["NEVER"], UNKNOWN=c["UNKNOWN(no such state)"],
                                SESSIONS_EVENT_TO_STATE_MEDIAN=qq["median"], Q1=qq["q1"], Q3=qq["q3"], MIN=qq["min"], MAX=qq["max"], N_GAPS=qq["n"], SOURCE="bot-computed event vs documented state"))
    L.write_csv(os.path.join(HERE, "SECOND_TOUCH_ANALYSIS.csv"), sta)
    # role summary: for E2/E3, which state does the event sit between most consistently (discovery+validation)
    for ev in ("E2_production", "E3_retest", "E4_trigger"):
        rr = [s for s in sta if s["EVENT"] == ev and s["SET"] == "discovery+validation"]
        for s in rr:
            tot = s["BEFORE"] + s["SAME"] + s["AFTER"]
            role.append(dict(EVENT=ev, TARGET_STATE=s["TARGET_STATE"], N_EVALUABLE=tot, SHARE_BEFORE=round(s["BEFORE"] / tot, 3) if tot else None, SHARE_AFTER=round(s["AFTER"] / tot, 3) if tot else None,
                             NEVER=s["NEVER"], ROLE_READING=("precedes" if tot and s["BEFORE"] / tot >= 0.7 else "follows" if tot and s["AFTER"] / tot >= 0.7 else "mixed/insufficient")))
    L.write_csv(os.path.join(HERE, "TEMPORAL_ROLE_ANALYSIS.csv"), role)
    print("ledger", len(ledger), "ordering", len(ordering), collections.Counter(o["ORDER_RESULT"] for o in ordering), collections.Counter((o["SET"], o["E2_VS_STATE"]) for o in ordering))
    print("E3 vs state", collections.Counter((o["SET"], o["E3_VS_STATE"]) for o in ordering))
    print("E2 status", collections.Counter(o.get("SECOND_TOUCH_STATUS") for o in ordering))


if __name__ == "__main__":
    main()
