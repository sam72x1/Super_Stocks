"""🔬 PHASE 4 — البنى البحثيّة (§11-13 · PHASE4_PREREG.md §④ · §⑥-O5/O6): A الحاليّة · REMOVE · B · C · D على صفوف فيصل المؤرَّخة وأيّام الضوابط المطابَقة.
الاستعمال: python3 arch.py discovery   ⟵ ثمّ تجميدٌ (commit) ⟵ python3 arch.py validation (أعمى · بلا تغييرِ تعريف) · python3 arch.py anchor.
لا عتبةَ تُضبط · الذاكرةُ محدودةٌ بالبنية (E5) لا بعدد."""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p4lib as P                        # noqa: E402

L = P.L
ARCHS = ["A", "REMOVE", "B", "C", "D"]
_SCAN = {}


def scans(sym, level, ft):
    k = (sym, level, ft)
    if k not in _SCAN:
        _SCAN[k] = (P.e2_scan(sym, level, ft), P.cycle_scan(sym, level, ft))
    return _SCAN[k]


def observation(sym, T, lv):
    """كائنُ ملاحظةٍ عند T: جلسةٌ s ∈ (اللمسة الأولى، T] كان فيها الرمزُ أهلًا بلا مرساة والمستوى عندها هو مستوى T."""
    for d in [lv["first_touch"]] + P.sym_sessions_after(sym, lv["first_touch"], P.E2_MAX + 1):   # s ∈ [اللمسة الأولى + 1 جلسة, T]
        s = L.shift(d, 1)
        if s > T:
            break
        l2 = P.level_at(sym, s)
        if not l2 or abs(l2["level"] - lv["level"]) > 1e-4 * max(1.0, lv["level"]):
            continue
        el, _ = P.eligible(sym, s)
        if el:
            return s
    return None


def states_at(sym, T):
    """حالاتُ البنى الخمس عند T (شموعٌ < T · والأحداثُ E2/E3/E4 المحسوبةُ من شموعٍ < تاريخها ≤ T)."""
    g = P.gate_row(sym, T)
    el = (g["result"] == "PASS") or (g["gate"] == "ANCHOR")
    out = dict(A_candidate=int(g["result"] == "PASS"), A_gate=g["gate"], REMOVE_candidate=int(el))
    lv = P.level_at(sym, T)
    if not lv:
        out.update(B_observation=0, B_watch_ready=0, C_focus_watch=0, C_ready=0, D_observation=0, D_retest=0, D_trigger=0, OBS_SINCE="", LEVEL="", FIRST_TOUCH="", E2="", E3="", E4="")
        return out
    e2, cy = scans(sym, lv["level"], lv["first_touch"])
    obs = observation(sym, T, lv)
    e2d = e2["date"] if e2["date"] and e2["date"] <= T else None
    e3d = cy["e3"] if cy["e3"] and cy["e3"] <= T else None
    e4d = cy["e4"] if cy["e4"] and cy["e4"] <= T else None
    o = int(bool(obs))
    out.update(B_observation=o, B_watch_ready=int(o and bool(e2d)), C_focus_watch=o, C_ready=int(o and (bool(e2d) or bool(e3d))), D_observation=o, D_retest=int(o and bool(e3d)),
               D_trigger=int(o and bool(e4d)), OBS_SINCE=obs or "", LEVEL=lv["level"], FIRST_TOUCH=lv["first_touch"], E2=e2d or "", E3=e3d or "", E4=e4d or "")
    return out


ANY = {"A": ["A_candidate"], "REMOVE": ["REMOVE_candidate"], "B": ["B_observation"], "C": ["C_focus_watch"], "D": ["D_observation"]}
MATCHED = {  # المرحلةُ المطابِقة لحالة فيصل في كلّ بنية (PHASE4_PREREG §⑥-O5)
    "FOCUS": {"A": "A_candidate", "REMOVE": "REMOVE_candidate", "B": "B_observation", "C": "C_focus_watch", "D": "D_observation"},
    "WATCH": {"A": "A_candidate", "REMOVE": "REMOVE_candidate", "B": "B_observation", "C": "C_focus_watch", "D": "D_observation"},
    "READY": {"A": "A_candidate", "REMOVE": "REMOVE_candidate", "B": "B_watch_ready", "C": "C_ready", "D": "D_retest"},
    "ENTRY": {"A": "A_candidate", "REMOVE": "REMOVE_candidate", "B": "B_watch_ready", "C": "C_ready", "D": "D_trigger"}}
ALERT = {"A": "A_candidate", "REMOVE": "REMOVE_candidate", "B": "B_watch_ready", "C": "C_ready", "D": "D_trigger"}
OBS = {"A": "A_candidate", "REMOVE": "REMOVE_candidate", "B": "B_observation", "C": "C_focus_watch", "D": "D_observation"}


def main(which):
    P.load_extra()
    rows = [r for r in P.faisal_timeline() if r["has_bars"] and r["set"] == which]
    fs = P.first_states([r for r in P.faisal_timeline() if r["has_bars"]])
    tickers = sorted({r["ticker"] for r in rows})
    per_row = []
    for r in rows:
        st = states_at(r["ticker"], r["session"])
        per_row.append(dict(TICKER=r["ticker"], SET=which, DECISION_DATE=r["session"], FAISAL_STATE=r["state"], EVIDENCE_ID=r["evidence_id"], EVIDENCE_CLASS=r["evidence_class"],
                            DATA_CUTOFF=f"bars < {r['session']}", EVIDENCE_CUTOFF=f"units <= {r['date']}", FUTURE_REVEAL_DATE="none (states use events <= decision date only)", **st))
    L.write_csv(os.path.join(P.OUT, f"arch_rows_{which}.csv"), per_row)
    # controls for this set
    ctrl = [c for c in csv.DictReader(open(os.path.join(HERE, "NEGATIVE_VALIDATION_CASES.csv"), encoding="utf-8")) if c["SET"] == which]
    per_ctrl = []
    for c in ctrl:
        st = states_at(c["CONTROL"], c["DATE"])
        lv = P.level_at(c["CONTROL"], c["DATE"])
        seq = dict(FWD_E3=0, FWD_E4=0, FWD_E2=0)
        if lv:
            e2, cy = scans(c["CONTROL"], lv["level"], lv["first_touch"])
            seq = dict(FWD_E2=int(bool(e2["date"])), FWD_E3=int(bool(cy["e3"])), FWD_E4=int(bool(cy["e4"])), FWD_E3_BRANCH=cy["e3_branch"] or "", FWD_REVEAL="today")
        per_ctrl.append(dict(CONTROL=c["CONTROL"], MATCHED_POSITIVE=c["MATCHED_POSITIVE"], SET=which, DECISION_DATE=c["DATE"], **st, **seq))
    L.write_csv(os.path.join(P.OUT, f"arch_controls_{which}.csv"), per_ctrl)
    # positives' forward sequence (for §⑪-D comparison) on the first-state level
    pos_seq = []
    for t in tickers:
        D = fs[t]["first_state"]; lv = P.level_at(t, D)
        if not lv:
            continue
        e2, cy = scans(t, lv["level"], lv["first_touch"])
        pos_seq.append(dict(TICKER=t, SET=which, DECISION_DATE=D, FWD_E2=int(bool(e2["date"])), FWD_E3=int(bool(cy["e3"])), FWD_E4=int(bool(cy["e4"])), FWD_E3_BRANCH=cy["e3_branch"] or ""))
    L.write_csv(os.path.join(P.OUT, f"pos_sequence_{which}.csv"), pos_seq)

    # ---- STATE_ALIGNMENT_MATRIX (components separately) + ARCHITECTURE_COMPARISON + MOVE_VS_REMOVE
    align, comp, mvr = [], [], []
    n_ctrl = len(per_ctrl)
    for a in ARCHS:
        rec_any = sum(1 for r in per_row if any(r[k] for k in ANY[a]))
        rec_matched = sum(1 for r in per_row if r[MATCHED[r["FAISAL_STATE"]][a]])
        by_state = {}
        for s in ("FOCUS", "WATCH", "READY", "ENTRY"):
            rs = [r for r in per_row if r["FAISAL_STATE"] == s]
            by_state[s] = (sum(1 for r in rs if r[MATCHED[s][a]]), len(rs))
        # first divergence per ticker: first dated row (chronological) with no object at any stage
        fd = 0; fd_dates = []
        for t in tickers:
            rs = sorted((r for r in per_row if r["TICKER"] == t), key=lambda r: r["DECISION_DATE"])
            miss = next((r for r in rs if not any(r[k] for k in ANY[a])), None)
            if miss:
                fd += 1; fd_dates.append(f"{t}:{miss['DECISION_DATE']}")
        fp_obs = sum(1 for c in per_ctrl if c[OBS[a]]); fp_alert = sum(1 for c in per_ctrl if c[ALERT[a]])
        # transition timing: arch stage-change date vs Faisal READY/ENTRY (where both exist)
        gaps = []
        for t in tickers:
            d = fs[t]
            for s, key in (("first_ready", "READY"), ("first_entry", "ENTRY")):
                if not d.get(s):
                    continue
                r = next((x for x in per_row if x["TICKER"] == t and x["DECISION_DATE"] == d[s]), None)
                if not r:
                    continue
                ev = {"A": None, "REMOVE": None, "B": r["E2"], "C": (min(x for x in (r["E2"], r["E3"]) if x) if (r["E2"] or r["E3"]) else ""), "D": (r["E3"] if key == "READY" else r["E4"])}[a]
                if ev:
                    gaps.append(L.cal_index(d[s]) - L.cal_index(ev))
        qq = P.q(gaps)
        for s in ("FOCUS", "WATCH", "READY", "ENTRY"):
            k, n = by_state[s]
            align.append(dict(SET=which, ARCHITECTURE=a, FAISAL_STATE=s, STAGE_USED=MATCHED[s][a], ALIGNED=k, N=n, SHARE=round(k / n, 3) if n else None, WILSON95=P.wilson(k, n) if n >= 5 else ""))
        comp.append(dict(SET=which, ARCHITECTURE=a, FAISAL_ROWS=len(per_row), TICKERS=len(tickers), RECALL_ANY_STAGE=rec_any, RECALL_MATCHED_STAGE=rec_matched,
                         FIRST_DIVERGENCE_TICKERS=fd, FIRST_DIVERGENCE_SHARE=round(fd / len(tickers), 3) if tickers else None, FIRST_DIVERGENCE_DATES=";".join(fd_dates),
                         CONTROL_DAYS=n_ctrl, FP_OBSERVATION_STAGE=fp_obs, FP_OBSERVATION_RATE=round(fp_obs / n_ctrl, 3) if n_ctrl else None,
                         FP_ALERT_STAGE=fp_alert, FP_ALERT_RATE=round(fp_alert / n_ctrl, 3) if n_ctrl else None,
                         TRANSITION_TIMING_SESSIONS_STAGE_TO_FAISAL_READY_ENTRY=f"median {qq['median']} IQR {qq['q1']}-{qq['q3']} n {qq['n']}" if qq["n"] else "n/a"))
    rem = next(c for c in comp if c["ARCHITECTURE"] == "REMOVE"); cur = next(c for c in comp if c["ARCHITECTURE"] == "A")
    for a in ("B", "C", "D"):
        m = next(c for c in comp if c["ARCHITECTURE"] == a)
        keep = (m["RECALL_ANY_STAGE"] >= 0.8 * rem["RECALL_ANY_STAGE"]) if rem["RECALL_ANY_STAGE"] else False
        clean = (m["FP_ALERT_RATE"] is not None and cur["FP_ALERT_RATE"] is not None and m["FP_ALERT_RATE"] <= 1.5 * cur["FP_ALERT_RATE"] + 1e-9)
        mvr.append(dict(SET=which, MOVE_ARCH=a, REMOVE_RECALL_ANY=rem["RECALL_ANY_STAGE"], MOVE_RECALL_ANY=m["RECALL_ANY_STAGE"], REMOVE_RECALL_MATCHED=rem["RECALL_MATCHED_STAGE"], MOVE_RECALL_MATCHED=m["RECALL_MATCHED_STAGE"],
                        A_FP_ALERT_RATE=cur["FP_ALERT_RATE"], REMOVE_FP_ALERT_RATE=rem["FP_ALERT_RATE"], MOVE_FP_ALERT_RATE=m["FP_ALERT_RATE"], MOVE_FP_OBSERVATION_RATE=m["FP_OBSERVATION_RATE"],
                        REMOVE_FP_OBSERVATION_RATE=rem["FP_OBSERVATION_RATE"], RULE_RECALL_KEPT_80PCT=int(keep), RULE_ALERT_NOISE_LE_1_5x_A=int(clean), MOVE_BETTER_THAN_REMOVE_PER_PREREG=int(keep and clean)))
    # positives vs controls forward sequence (observation→retest→trigger)
    def rate(rows_, k):
        return (sum(int(r[k]) for r in rows_), len(rows_))
    seqcmp = []
    for k in ("FWD_E2", "FWD_E3", "FWD_E4"):
        a_, n_ = rate(pos_seq, k); b_, m_ = rate(per_ctrl, k)
        seqcmp.append(dict(SET=which, EVENT=k, POSITIVES=f"{a_}/{n_}", CONTROLS=f"{b_}/{m_}", RATIO=round(((a_ / n_) / (b_ / m_)), 2) if n_ and m_ and b_ else ("inf" if a_ and n_ and m_ else "")))
    L.write_csv(os.path.join(P.OUT, f"state_alignment_{which}.csv"), align)
    L.write_csv(os.path.join(P.OUT, f"architecture_comparison_{which}.csv"), comp)
    L.write_csv(os.path.join(P.OUT, f"move_vs_remove_{which}.csv"), mvr)
    L.write_csv(os.path.join(P.OUT, f"sequence_pos_vs_ctrl_{which}.csv"), seqcmp)
    P.save_extra()
    for c in comp:
        print({k: c[k] for k in ("ARCHITECTURE", "RECALL_ANY_STAGE", "RECALL_MATCHED_STAGE", "FIRST_DIVERGENCE_TICKERS", "FP_OBSERVATION_RATE", "FP_ALERT_RATE")})
    for m in mvr:
        print(m)
    for s in seqcmp:
        print(s)


def merge():
    """يجمع ملفّاتِ الأقسام في المخرجات المطلوبة (بعد تشغيل discovery ثمّ validation ثمّ anchor)."""
    for name, out in (("state_alignment", "STATE_ALIGNMENT_MATRIX.csv"), ("architecture_comparison", "ARCHITECTURE_COMPARISON.csv"), ("move_vs_remove", "MOVE_VS_REMOVE_RESULTS.csv")):
        rows = []
        for which in ("discovery", "validation", "anchor"):
            p = os.path.join(P.OUT, f"{name}_{which}.csv")
            if os.path.exists(p):
                rows += list(csv.DictReader(open(p, encoding="utf-8")))
        L.write_csv(os.path.join(HERE, out), rows)
        print(out, len(rows))


if __name__ == "__main__":
    if sys.argv[1] == "merge":
        merge()
    else:
        main(sys.argv[1])
