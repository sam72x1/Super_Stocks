"""APP_POS — the sealed evaluation of the app's two reproducible conditions (APP_POS_PREREG.md).

Refuses to read any row (exit 9) unless `APP_POS_PREREG.md` matches the pinned SHA-256. Reuses READYNOW's shared
definitions (`rn_lib`) unchanged: windows, labels, matching, equal-burden rankings, bootstrap.
Run from the repo root:  python3 faisal_engine/readynow/audit/rn_app_eval.py final   → audit/data/app_pos_result.json
"""
import hashlib
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RN = os.path.dirname(HERE)
sys.path.insert(0, RN)
import rn_lib as K                                                       # noqa: E402

PREREG = os.path.join(HERE, "APP_POS_PREREG.md")
PREREG_SHA256 = "90aa624293ec7a45aa0d32ee79544c38eb1a590c8a6faacfce99b511538659bb"
OUT = os.path.join(HERE, "data", "app_pos_result.json")
REPS = 2000
SEED = 20261011
ALPHA_W = 0.025
ALPHA_P = 0.05
FLOORS = {"eligible_events": 20, "c1_pairs": 300, "c3_pairs": 200}
OOS = ("validation", "holdout")


def app_pos(r):
    return K.COND["NEAR15"](r) and K.COND["BOUNCE10_40"](r)


def prereg_ok():
    try:
        return hashlib.sha256(open(PREREG, "rb").read()).hexdigest() == PREREG_SHA256
    except OSError:
        return False


rd = K.rd


def _units(pairs):
    u = defaultdict(lambda: [0, 0, 0, 0])
    for a, c in pairs:
        x = u[a["sym"]]
        x[0] += 1
        x[1] += a["lab"] == "POS710"
        x[2] += 1
        x[3] += c["lab"] == "POS710"
    return u


def relabel(rows, lab):
    return [dict(r, lab=r[lab]) for r in rows]


def window(w, rows_all, events_all, cal, decisive):
    rows = K.window_rows(rows_all, w)
    by = K.annotate(rows)
    six = {d: k for k, d in enumerate(cal)}
    events = K.events_index(rows, events_all, cal, w)
    tc = K.EXISTING["TC_TECH"]
    res = {"window": K.WINDOWS[w], "rows": len(rows), "sessions": len(by),
           "eligible_events": sum(1 for e in events if e["pos_rows"])}
    alpha = ALPHA_W if decisive else ALPHA_P
    res["APP_POS"] = K.evaluate(rows, by, events, six, app_pos, REPS, SEED, alpha, "APP_POS")
    p1, _u1 = K.match(by, app_pos)
    p3, _u3 = K.match(by, K.only_beyond_tool(app_pos), exact=tc)
    res["C1"] = K.matched(by, app_pos, REPS, SEED, alpha)
    res["C3"] = K.matched(by, K.only_beyond_tool(app_pos), REPS, SEED, alpha, exact=tc)
    res["C2"] = {k: [res["APP_POS"][k]["rule_minus_pp"], res["APP_POS"][k]["rule_minus_pp_ci"]]
                 for k in ("VOL_k", "VOLAT_k")}
    res["sufficient"] = (res["eligible_events"] >= FLOORS["eligible_events"] and res["C1"]["pairs"] >= FLOORS["c1_pairs"]
                         and res["C3"]["pairs"] >= FLOORS["c3_pairs"])
    ok = lambda ci, thr: bool(ci) and ci[0] > thr                              # noqa: E731
    res["pass"] = {"C1": ok(res["C1"]["ci"], 1.0),
                   "C2": ok(res["C2"]["VOL_k"][1], 0.0) and ok(res["C2"]["VOLAT_k"][1], 0.0),
                   "C3": ok(res["C3"]["ci"], 1.0)}
    # reported, never decisive
    res["single"] = {}
    for n in ("NEAR15", "BOUNCE10_40"):
        e = K.evaluate(rows, by, events, six, K.COND[n], REPS, SEED, alpha, n)
        res["single"][n] = {k: e[k] for k in ("flags_per_session", "precision", "lift", "lift_ci", "recall")}
        res["single"][n]["C1"] = K.matched(by, K.COND[n], REPS, SEED, alpha)
    sp = [r for r in rows if r.get("split120") == "1"]
    sby = K.annotate([dict(r) for r in sp])
    ev = [r for r in sp if r["lab"] in K.EVAL]
    base = sum(r["lab"] == "POS710" for r in ev) / len(ev) if ev else None
    fl = [r for r in ev if app_pos(r)]
    prec = sum(r["lab"] == "POS710" for r in fl) / len(fl) if fl else None
    res["split_domain"] = {"rows": len(sp), "evaluable": len(ev), "base": round(base, 4) if base else None,
                           "flagged": len(fl), "precision": round(prec, 4) if prec is not None else None,
                           "lift": round(prec / base, 3) if (prec is not None and base) else None,
                           "C1": K.matched(sby, app_pos, REPS, SEED, alpha)}
    res["sensitivity"] = {}
    for lab in ("lab_x70", "lab_l10", "lab_ign"):
        rr = relabel(rows, lab)
        rby = K.annotate(rr)
        ev = [r for r in rr if r["lab"] in K.EVAL]
        base = sum(r["lab"] == "POS710" for r in ev) / len(ev)
        fl = [r for r in ev if app_pos(r)]
        prec = sum(r["lab"] == "POS710" for r in fl) / len(fl) if fl else None
        res["sensitivity"][lab] = {"base": round(base, 4), "precision": round(prec, 4) if prec is not None else None,
                                   "lift": round(prec / base, 3) if prec is not None else None,
                                   "C1": K.matched(rby, app_pos, REPS, SEED, alpha)}
    return res, p1, p3


def status(win, pooled):
    suff = [win[w]["sufficient"] for w in OOS]
    if not any(suff):
        return "BLOCKED_BY_SPECIFIC_DATA_GAP"
    if all(suff) and all(all(win[w]["pass"].values()) for w in OOS):
        return "VALIDATED_READY_SIGNAL"
    if pooled["C1"]["ci"] and pooled["C1"]["ci"][0] > 1.0 and pooled["C3"]["ci"] and pooled["C3"]["ci"][0] > 1.0:
        return "PROMISING_UNVALIDATED"
    return "NO_INCREMENTAL_EDGE_FOUND"


def final():
    if not prereg_ok():
        print("⛔ APP_POS_PREREG.md differs from the sealed version — nothing read")
        sys.exit(9)
    cal = json.load(open(os.path.join(K.DATA, "calendar.json"), encoding="utf-8"))["sessions"]
    rows_all = rd("rows.csv.gz")
    events_all = rd("events.csv.gz")
    win, pairs1, pairs3 = {}, [], []
    dev, _p, _q = window("development", rows_all, events_all, cal, decisive=False)
    for w in OOS:
        res, p1, p3 = window(w, rows_all, events_all, cal, decisive=True)
        win[w] = res
        pairs1 += p1
        pairs3 += p3
    pooled = {}
    for name, pr in (("C1", pairs1), ("C3", pairs3)):
        est, ci = K.cluster_ratio(_units(pr), REPS, SEED, ALPHA_P)
        pooled[name] = {"pairs": len(pr), "ratio": est, "ci": ci}
    out = {"spec_sha256": PREREG_SHA256, "rule": "APP_POS = NEAR15 and BOUNCE10_40 (rn_lib.COND)",
           "development_descriptive": dev, "windows": win, "pooled_95": pooled, "status": status(win, pooled)}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    if (sys.argv[1] if len(sys.argv) > 1 else "") != "final":
        sys.exit("usage: rn_app_eval.py final")
    r = final()
    d = r["development_descriptive"]
    print("development", d["APP_POS"]["flags_per_session"], d["APP_POS"]["precision"], d["APP_POS"]["lift"],
          d["APP_POS"]["lift_ci"], "C1", d["C1"]["ratio"], d["C1"]["ci"])
    for w in OOS:
        x = r["windows"][w]
        print(w, "sufficient", x["sufficient"], "pass", x["pass"], "flags/session", x["APP_POS"]["flags_per_session"],
              "precision", x["APP_POS"]["precision"], "lift", x["APP_POS"]["lift"], x["APP_POS"]["lift_ci"],
              "C1", x["C1"]["ratio"], x["C1"]["ci"], "C2", x["C2"], "C3", x["C3"]["ratio"], x["C3"]["ci"])
    print("pooled", r["pooled_95"], "→", r["status"])
