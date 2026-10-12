"""Faisal condition atlas — development analysis (2025-05-01 → 2025-12-31 only; 2026 is not read here).

Part 1 · condition strength. For every atlas flag (`ca_lib.COND`): prevalence among the rows whose corrected onset
falls 7–10 sessions later (POS710) and among the inactive rows (NEG); lift with a ticker-cluster CI (95% and
Bonferroni over the number of flags); same-session matched ratio (price bucket, volume, volatility and dollar-volume
percentiles within 0.10); events captured and the exclusion cost (eligible events the flag never marks in T−10..T−7,
i.e. lost if the flag were required); precision minus the volume, volatility, low-price and 5-session-drop rankings at
the same per-session burden (pp, cluster CI); stability across the two chronological halves; lift inside two
contexts (at the support · oversold); and the lead profile (prevalence 1..20 sessions before the onset against the
rows with no onset within 20 sessions).
Part 2 · the three-axis classifier. Ridge logistic models on the binary atlas flags (A axis: validity; B axis:
technical state and candles; C: every flag incl. invalidation and timing). Penalty chosen on development
(train 2025-05-01 → 09-30, test 10-01 → 12-31) by the test AUC; then refit on the whole development window and frozen
(`data/model_frozen.json`). Equal-burden comparison on the development test half against the tool's technical part,
CAPIT_TC, DROP_k, VOLAT_k, VOL_k, the condition count and the app's weighted score.
Run from the repo root:  python3 faisal_engine/readynow/condition_atlas/ca_dev.py [--model-only]   → data/strength_dev.json,
data/model_dev.json, data/model_frozen.json
"""
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np                                                        # noqa: E402
import ca_lib as L                                                        # noqa: E402

K, D = L.K, L.D
sys.path.insert(0, os.path.join(L.RN, "disc"))
import rn_disc_cand as DC                                                 # noqa: E402
import rn_disc_model as M                                                 # noqa: E402

DATA = L.DATA
REPS, SEED = 2000, 20261011
WIN = "development"
TRAIN = ("2025-05-01", "2025-09-30")
TEST = ("2025-10-01", "2025-12-31")
LAMS = (1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0, 3000.0, 10000.0, 30000.0, 100000.0)   # widened after the first
#   development run chose the edge (1000); development only, before any 2026 number
num = K.num


def _neg(x):
    return None if x is None else -x


SCORES = {"VOL_k": lambda r: num(r.get("v1x")), "VOLAT_k": lambda r: num(r.get("range20")),
          "LOWPX_k": lambda r: _neg(num(r.get("px"))), "DROP_k": lambda r: _neg(num(r.get("r5")))}


def lead_profile(rows, f, maxk=20):
    """Share of rows flagged k sessions before a clean onset (k = 1..maxk) and among rows with no onset within maxk."""
    out = {}
    for k in range(1, maxk + 1):
        rs = [r for r in rows if num(r.get("to_onset_on")) == k and r["lab"] != "UNKNOWN_SPLIT"]
        out[k] = [len(rs), round(sum(1 for r in rs if f(r)) / len(rs), 4) if rs else None]
    base = [r for r in rows if r["lab"] == "NEG" and (num(r.get("to_onset_on")) is None
                                                      or num(r.get("to_onset_on")) > maxk)]
    out["far"] = [len(base), round(sum(1 for r in base if f(r)) / len(base), 4) if base else None]
    return out


def ctx_lift(rows, f, ctx):
    er = [r for r in rows if r["lab"] in K.EVAL and ctx(r)]
    fl = [r for r in er if f(r)]
    if not er or not fl:
        return None
    base = sum(r["lab"] == "POS710" for r in er) / len(er)
    prec = sum(r["lab"] == "POS710" for r in fl) / len(fl)
    return {"n_ctx": len(er), "flagged": len(fl), "precision": round(prec, 4), "ctx_base": round(base, 4),
            "lift": round(prec / base, 3) if base else None}


def strength(rows, by, events, six, names):
    m = len(names)
    saved = dict(K.BURDEN_SCORES)
    K.BURDEN_SCORES.clear()
    K.BURDEN_SCORES.update(SCORES)
    out = {}
    halves = [(lo, hi) for lo, hi in DC.HALVES[WIN]]
    try:
        for name in names:
            f = L.COND[name]
            e = K.evaluate(rows, by, events, six, f, REPS, SEED, 0.05, name)
            mt = K.matched(by, f, REPS, SEED, 0.05)
            er = [r for r in rows if r["lab"] in K.EVAL]
            pos = [r for r in er if r["lab"] == "POS710"]
            neg = [r for r in er if r["lab"] == "NEG"]
            u = defaultdict(lambda: [0, 0, 0, 0])
            for r in er:
                x = u[r["sym"]]
                x[2] += 1
                x[3] += r["lab"] == "POS710"
                if f(r):
                    x[0] += 1
                    x[1] += r["lab"] == "POS710"
            _l, bci = K.cluster_ratio(u, REPS, SEED, 0.05 / m)
            res = {k: e[k] for k in ("flags_per_session", "triggers_per_session", "evaluable_flagged", "pos710_flagged",
                                     "precision", "precision_ci95", "fpr", "lift", "lift_ci", "events_captured",
                                     "events_eligible", "recall", "recall_ci95", "trigger_precision",
                                     "lead_to_onset_q25_med_q75", "flagged_tickers")}
            res["lift_ci_bonferroni"] = bci
            res["prev_pos"] = round(sum(1 for r in pos if f(r)) / len(pos), 4) if pos else None
            res["prev_neg"] = round(sum(1 for r in neg if f(r)) / len(neg), 4) if neg else None
            res["exclusion_cost_events"] = e["events_eligible"] - e["events_captured"]
            for bn in SCORES:
                res[bn] = e[bn]
            res["matched"] = {k: mt[k] for k in ("pairs", "unmatched", "flag_rate", "ctrl_rate", "ratio", "ci")}
            res["halves"] = [DC._period(rows, events, six, lo, hi, f, name) for lo, hi in halves]
            res["context"] = {c: ctx_lift(rows, f, g) for c, g in L.CONTEXTS.items() if c != "all"}
            res["lead_profile"] = lead_profile(rows, f)
            out[name] = res
    finally:
        K.BURDEN_SCORES.clear()
        K.BURDEN_SCORES.update(saved)
    return out


# ───────────────────────── part 2: the classifier ─────────────────────────
def _xy(rows, feats):
    er = [r for r in rows if r["lab"] in K.EVAL]
    X = L.design(er, feats)
    y = np.array([1.0 if r["lab"] == "POS710" else 0.0 for r in er])
    return er, X, y


def choose(rows, feats):
    tr = [r for r in rows if TRAIN[0] <= r["t"] <= TRAIN[1]]
    te = [r for r in rows if TEST[0] <= r["t"] <= TEST[1]]
    _a, Xtr, ytr = _xy(tr, feats)
    _b, Xte, yte = _xy(te, feats)
    grid = []
    for lam in LAMS:
        w = M.fit(Xtr, ytr, lam)
        grid.append({"lam": lam, "train_auc": round(M.auc(M.score(w, Xtr), ytr), 4),
                     "test_auc": round(M.auc(M.score(w, Xte), yte), 4)})
    best = max(grid, key=lambda g: (g["test_auc"], g["lam"]))
    return best["lam"], grid


def classes(by, flag_tc, score, b_score):
    """Per session: k = the tool's technical-part flags. Non-invalidated rows ranked by `score`: READY_1 the top k,
    READY_2 the next k, READY_3 the next 2k; the rest WATCH when the B-axis score is at or above the session median of
    the non-invalidated rows, else NOT_READY; invalidated rows INVALIDATED. Sessions where the tool flags nothing get
    k = 0 (every valid row is WATCH or NOT_READY)."""
    cls = {}
    for t, rs in by.items():
        k = sum(1 for r in rs if flag_tc(r))
        ok = [r for r in rs if not L.invalidated(r)]
        for r in rs:
            if L.invalidated(r):
                cls[(r["sym"], t)] = "INVALIDATED"
        ranked = sorted(ok, key=lambda r: (-score(r), r["sym"]))
        bs = sorted(b_score(r) for r in ok)
        med = bs[len(bs) // 2] if bs else 0.0
        for j, r in enumerate(ranked):
            if j < k:
                c = "READY_1"
            elif j < 2 * k:
                c = "READY_2"
            elif j < 4 * k:
                c = "READY_3"
            else:
                c = "WATCH" if b_score(r) >= med else "NOT_READY"
            cls[(r["sym"], t)] = c
    return cls


def class_table(rows, cls, events):
    out = {}
    er = [r for r in rows if r["lab"] in K.EVAL]
    for c in ("READY_1", "READY_2", "READY_3", "WATCH", "NOT_READY", "INVALIDATED"):
        rs = [r for r in er if cls.get((r["sym"], r["t"])) == c]
        p = sum(r["lab"] == "POS710" for r in rs)
        elig = [e for e in events if e["pos_rows"]]
        cap = sum(1 for e in elig if any(cls.get((r["sym"], r["t"])) == c for r in e["pos_rows"]))
        out[c] = {"rows": len(rs), "pos": p, "precision": round(p / len(rs), 4) if rs else None,
                  "precision_ci95": K.wilson(p, len(rs)), "events_touched": cap,
                  "per_session": round(sum(1 for r in rows if cls.get((r["sym"], r["t"])) == c)
                                       / max(len({r["t"] for r in rows}), 1), 2)}
    return out


def rank_flag(by, k_flag, score, exclude=None):
    """Equal burden: per session flag as many rows as `k_flag`, the highest `score` (rows failing `exclude` skipped)."""
    out = set()
    for t, rs in by.items():
        k = sum(1 for r in rs if k_flag(r))
        if not k:
            continue
        pool = [r for r in rs if not (exclude and exclude(r))]
        ranked = sorted(pool, key=lambda r: (0 if score(r) is not None else 1, -(score(r) or 0.0), r["sym"]))
        out.update((r["sym"], t) for r in ranked[:k])
    return out


def compare(rows, by, events, six, rankers, ref_names=("TC_TECH", "CAPIT_TC", "DROP_k", "VOLAT_k")):
    """Every ranker against every reference: precision difference (pp, cluster CI) and events captured."""
    er = [r for r in rows if r["lab"] in K.EVAL]
    elig = [e for e in events if e["pos_rows"]]
    sess = max(len(by), 1)
    out = {}
    for name, sel in rankers.items():
        fl = [r for r in er if (r["sym"], r["t"]) in sel]
        p = sum(r["lab"] == "POS710" for r in fl)
        neg_all = sum(r["lab"] == "NEG" for r in er)
        cap = sum(1 for e in elig if any((r["sym"], r["t"]) in sel for r in e["pos_rows"]))
        res = {"flags_per_session": round(sum(1 for r in rows if (r["sym"], r["t"]) in sel) / sess, 2),
               "flagged": len(fl), "pos": p, "precision": round(p / len(fl), 4) if fl else None,
               "precision_ci95": K.wilson(p, len(fl)), "fpr": round((len(fl) - p) / neg_all, 4) if neg_all else None,
               "events_captured": cap, "events_eligible": len(elig),
               "recall": round(cap / len(elig), 4) if elig else None}
        u_all = defaultdict(lambda: [0, 0, 0, 0])
        for r in er:
            x = u_all[r["sym"]]
            x[2] += 1
            x[3] += r["lab"] == "POS710"
            if (r["sym"], r["t"]) in sel:
                x[0] += 1
                x[1] += r["lab"] == "POS710"
        res["lift"], res["lift_ci"] = K.cluster_ratio(u_all, REPS, SEED, 0.05)
        for ref in ref_names:
            if ref == name or ref not in rankers:
                continue
            o = rankers[ref]
            u = defaultdict(lambda: [0, 0, 0, 0])
            for r in er:
                key = (r["sym"], r["t"])
                x = u[r["sym"]]
                if key in sel:
                    x[0] += 1
                    x[1] += r["lab"] == "POS710"
                if key in o:
                    x[2] += 1
                    x[3] += r["lab"] == "POS710"
            d, ci = K.cluster_diff(u, REPS, SEED, 0.05)
            ocap = sum(1 for e in elig if any((r["sym"], r["t"]) in o for r in e["pos_rows"]))
            res["minus_" + ref] = {"pp": d, "ci95": ci, "events_self_minus_ref": cap - ocap}
        out[name] = res
    return out


def rankers_for(rows, by, models):
    """The equal-burden selections (k per session = the tool's technical-part flags)."""
    tc = D.REFS["TC_TECH"]
    for r in rows:
        for ax, (feats, w) in models.items():
            r["s_" + ax] = float(M.score(np.asarray(w), L.design([r], feats))[0])
    _p_r5(by)
    capit = K.burden_match(by, tc, DC.capit_score)
    out = {"TC_TECH": {(r["sym"], r["t"]) for r in rows if tc(r)}, "CAPIT_TC": capit,
           "DROP_k": K.burden_match(by, tc, SCORES["DROP_k"]), "VOLAT_k": K.burden_match(by, tc, SCORES["VOLAT_k"]),
           "VOL_k": K.burden_match(by, tc, SCORES["VOL_k"]),
           "COUNT_k": rank_flag(by, tc, L.count_score), "APPW_k": rank_flag(by, tc, L.app_score),
           "W_k": rank_flag(by, tc, lambda r: r["s_C"], exclude=L.invalidated),
           "W_k_noinval": rank_flag(by, tc, lambda r: r["s_C"]),
           "B_k": rank_flag(by, tc, lambda r: r["s_B"], exclude=L.invalidated),
           "A_k": rank_flag(by, tc, lambda r: r["s_A"], exclude=L.invalidated)}
    return out


def _p_r5(by):
    import bisect
    for rs in by.values():
        vals = sorted(v for v in (num(r.get("r5")) for r in rs) if v is not None)
        for r in rs:
            x = num(r.get("r5"))
            if x is None or not vals:
                r["p_r5"] = None
                continue
            lo, hi = bisect.bisect_left(vals, x), bisect.bisect_right(vals, x)
            r["p_r5"] = (lo + 0.5 * (hi - lo)) / len(vals)


def main():
    rows, by, miss = L.load(WIN)
    events, six = D.events(rows, WIN)
    names = list(L.COND)
    res = {"window": K.WINDOWS[WIN], "rows": len(rows), "rows_without_atlas_columns": miss,
           "evaluable": sum(1 for r in rows if r["lab"] in K.EVAL),
           "base_rate": round(sum(r["lab"] == "POS710" for r in rows if r["lab"] in K.EVAL)
                              / max(1, sum(1 for r in rows if r["lab"] in K.EVAL)), 4),
           "eligible_events": sum(1 for e in events if e["pos_rows"]), "flags_tested": len(names),
           "strength": None}
    if "--model-only" in sys.argv:
        res = json.load(open(os.path.join(DATA, "strength_dev.json"), encoding="utf-8"))
    else:
        res["strength"] = strength(rows, by, events, six, names)
        json.dump(res, open(os.path.join(DATA, "strength_dev.json"), "w", encoding="utf-8"), ensure_ascii=False,
                  indent=1)
    # part 2
    axes = {"A": L.AXIS_A, "B": L.AXIS_B, "C": L.AXIS_C}
    chosen, grids, frozen = {}, {}, {}
    for ax, feats in axes.items():
        lam, grid = choose(rows, feats)
        chosen[ax], grids[ax] = lam, grid
        _er, X, y = _xy(rows, feats)
        w = M.fit(X, y, lam)
        frozen[ax] = {"features": list(feats), "lam": lam, "w": [round(float(x), 6) for x in w]}
    # development test-half comparison with models fitted on the training half only (honest within development)
    tr = [r for r in rows if TRAIN[0] <= r["t"] <= TRAIN[1]]
    half_models = {}
    for ax, feats in axes.items():
        _er, X, y = _xy(tr, feats)
        half_models[ax] = (feats, M.fit(X, y, chosen[ax]))
    te = [r for r in rows if TEST[0] <= r["t"] <= TEST[1]]
    by_te = defaultdict(list)
    for r in te:
        by_te[r["t"]].append(r)
    ev_te = [e for e in events if e["pos_rows"] and TEST[0] <= min(r["t"] for r in e["pos_rows"]) <= TEST[1]]
    rk = rankers_for(te, by_te, half_models)
    cmp_ = compare(te, by_te, ev_te, six, rk)
    cls = classes(by_te, D.REFS["TC_TECH"], lambda r: r["s_C"], lambda r: r["s_B"])
    model = {"train": TRAIN, "test": TEST, "lams": LAMS, "chosen": chosen, "grids": grids,
             "test_half_compare": cmp_, "test_half_classes": class_table(te, cls, ev_te),
             "coef_half": {ax: dict(zip(["intercept"] + list(f), [round(float(x), 4) for x in w]))
                           for ax, (f, w) in half_models.items()},
             "coef_frozen": {ax: dict(zip(["intercept"] + v["features"], v["w"])) for ax, v in frozen.items()}}
    json.dump(model, open(os.path.join(DATA, "model_dev.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(frozen, open(os.path.join(DATA, "model_frozen.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1, sort_keys=True)
    return res, model


if __name__ == "__main__":
    res, model = main()
    print("rows", res["rows"], "eval", res["evaluable"], "base", res["base_rate"], "events", res["eligible_events"],
          "no atlas cols", res["rows_without_atlas_columns"])
    for n, v in res["strength"].items():
        print(f'{n:24s} f/s {v["flags_per_session"]:6} pp {v["prev_pos"]} pn {v["prev_neg"]} lift {v["lift"]} '
              f'{v["lift_ci"]} bonf {v["lift_ci_bonferroni"]} matched {v["matched"]["ratio"]} {v["matched"]["ci"]} '
              f'ev {v["events_captured"]}/{v["events_eligible"]} VOLAT {v["VOLAT_k"]["rule_minus_pp"]} '
              f'{v["VOLAT_k"]["rule_minus_pp_ci"]} DROP {v["DROP_k"]["rule_minus_pp"]} {v["DROP_k"]["rule_minus_pp_ci"]}'
              f' halves {[h["lift"] for h in v["halves"]]}')
    print("chosen", model["chosen"])
    for n, v in model["test_half_compare"].items():
        print(n, v["flags_per_session"], v["precision"], v["lift"], v["lift_ci"], v["events_captured"],
              {k: (x["pp"], x["ci95"]) for k, x in v.items() if k.startswith("minus_")})
    for c, v in model["test_half_classes"].items():
        print(c, v)
