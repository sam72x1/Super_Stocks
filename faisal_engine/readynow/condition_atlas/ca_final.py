"""Faisal condition atlas — the sealed 2026 check (validation 2026-01-16 → 05-15 · holdout 2026-06-02 → 08-27).

Scores the frozen three-axis classifier (`data/model_frozen.json`, fitted on development only) and every comparison
ranking at the tool's per-session burden, once, and only if CA_PROTOCOL.md matches the SHA-256 pinned below.
Also exposes `classify_window` (used by the casebook) and the condition strength on 2026 for the conditions the
protocol names. Outputs data/final.json.
Run from the repo root:  python3 faisal_engine/readynow/condition_atlas/ca_final.py
"""
import hashlib
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np                                                        # noqa: E402
import ca_dev as CD                                                       # noqa: E402
import ca_lib as L                                                        # noqa: E402

K, D, M = L.K, L.D, CD.M
DATA = L.DATA
PROTOCOL = os.path.join(HERE, "CA_PROTOCOL.md")
PROTOCOL_SHA256 = "457d9703963a988be2806aad0cdfb80788ad8bf7ac025280c309ad78a5941d34"
FROZEN_SHA256 = "482b9d580c3cccaf5aace7c06deab312356f4b10baa73f46054ada94e4d2d849"
WINDOWS = ("validation", "holdout")
REFS = ("TC_TECH", "CAPIT_TC", "DROP_k", "VOLAT_k", "VOL_k", "COUNT_k", "APPW_k")


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def protocol_ok():
    try:
        return (_sha(PROTOCOL) == PROTOCOL_SHA256
                and _sha(os.path.join(DATA, "model_frozen.json")) == FROZEN_SHA256)
    except OSError:
        return False


def models(fz):
    return {ax: (v["features"], np.asarray(v["w"])) for ax, v in fz.items()}


def classify_window(window, fz):
    rows, by, _m = L.load(window)
    for r in rows:
        for ax, (feats, w) in models(fz).items():
            r["s_" + ax] = float(M.score(w, L.design([r], feats))[0])
    return CD.classes(by, D.REFS["TC_TECH"], lambda r: r["s_C"], lambda r: r["s_B"])


def run_window(window, fz):
    rows, by, miss = L.load(window)
    events, six = D.events(rows, window)
    rk = CD.rankers_for(rows, by, models(fz))
    cmp_ = CD.compare(rows, by, events, six, rk, ref_names=REFS)
    cls = CD.classes(by, D.REFS["TC_TECH"], lambda r: r["s_C"], lambda r: r["s_B"])
    er = [r for r in rows if r["lab"] in K.EVAL]
    s = np.array([r["s_C"] for r in er])
    y = np.array([1.0 if r["lab"] == "POS710" else 0.0 for r in er])
    units = {}
    for name in ("W_k", "COUNT_k", "APPW_k"):
        units[name] = {}
        for ref in REFS:
            if ref == name:
                continue
            u = defaultdict(lambda: [0, 0, 0, 0])
            for r in er:
                key = (r["sym"], r["t"])
                x = u[r["sym"]]
                if key in rk[name]:
                    x[0] += 1
                    x[1] += r["lab"] == "POS710"
                if key in rk[ref]:
                    x[2] += 1
                    x[3] += r["lab"] == "POS710"
            units[name][ref] = dict(u)
    out = {"window": K.WINDOWS[window], "rows": len(rows), "rows_without_atlas_columns": miss,
           "evaluable": len(er), "base_rate": round(float(y.mean()), 4) if len(y) else None,
           "eligible_events": sum(1 for e in events if e["pos_rows"]), "auc_C": round(M.auc(s, y), 4),
           "auc_volatility": round(M.auc(np.array([K.num(r.get("range20")) or 0.0 for r in er]), y), 4),
           "auc_drop": round(M.auc(np.array([-(K.num(r.get("r5")) or 0.0) for r in er]), y), 4),
           "compare": cmp_, "classes": CD.class_table(rows, cls, events), "conditions": cond_lifts(rows)}
    return out, units


def cond_lifts(rows):
    """Every atlas flag on the window: flagged rows, precision, lift vs the window base with a ticker-cluster CI,
    and the prevalence among POS710 and NEG rows."""
    er = [r for r in rows if r["lab"] in K.EVAL]
    pos = [r for r in er if r["lab"] == "POS710"]
    neg = [r for r in er if r["lab"] == "NEG"]
    out = {}
    for name, f in L.COND.items():
        u = defaultdict(lambda: [0, 0, 0, 0])
        for r in er:
            x = u[r["sym"]]
            x[2] += 1
            x[3] += r["lab"] == "POS710"
            if f(r):
                x[0] += 1
                x[1] += r["lab"] == "POS710"
        lift, ci = K.cluster_ratio(u, CD.REPS, CD.SEED, 0.05)
        fl = sum(v[0] for v in u.values())
        out[name] = {"flagged": fl, "precision": round(sum(v[1] for v in u.values()) / fl, 4) if fl else None,
                     "lift": lift, "lift_ci": ci,
                     "prev_pos": round(sum(1 for r in pos if f(r)) / len(pos), 4) if pos else None,
                     "prev_neg": round(sum(1 for r in neg if f(r)) / len(neg), 4) if neg else None}
    return out


def pooled(uv, uh):
    out = {}
    for name in uv:
        out[name] = {}
        for ref in uv[name]:
            u = {f"V|{k}": v for k, v in uv[name][ref].items()}
            u.update({f"H|{k}": v for k, v in uh[name][ref].items()})
            d, ci = K.cluster_diff(u, CD.REPS, CD.SEED, 0.05)
            out[name][ref] = {"pp": d, "ci95": ci}
    return out


def main():
    if not protocol_ok():
        print("⛔ CA_PROTOCOL.md or model_frozen.json differs from the sealed version — nothing scored")
        sys.exit(9)
    fz = json.load(open(os.path.join(DATA, "model_frozen.json"), encoding="utf-8"))
    (va, uva), (ho, uho) = run_window("validation", fz), run_window("holdout", fz)
    res = {"protocol_sha256": PROTOCOL_SHA256, "frozen_sha256": FROZEN_SHA256, "validation": va, "holdout": ho,
           "pooled": pooled(uva, uho)}
    json.dump(res, open(os.path.join(DATA, "final.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return res


if __name__ == "__main__":
    r = main()
    for w in WINDOWS:
        v = r[w]
        print(w, "rows", v["rows"], "base", v["base_rate"], "events", v["eligible_events"], "AUC C", v["auc_C"],
              "vol", v["auc_volatility"], "drop", v["auc_drop"])
        for n, x in v["compare"].items():
            print(f'  {n:12s} f/s {x["flags_per_session"]} prec {x["precision"]} lift {x["lift"]} {x["lift_ci"]} '
                  f'ev {x["events_captured"]}/{x["events_eligible"]} fpr {x["fpr"]}')
        for c, x in v["classes"].items():
            print("  ", c, x)
    for n, x in r["pooled"].items():
        print("pooled", n, x)
