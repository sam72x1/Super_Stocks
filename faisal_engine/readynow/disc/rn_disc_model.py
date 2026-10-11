"""READY NOW discovery — how much can ANY combination of point-in-time daily features say? (ceiling test)

Two L2-regularised logistic models on a fixed, pre-declared feature list (`FEATS`, bars ≤ t only; the outcome-defined
`in_drift` is excluded):
  M_MAIN  main effects (numeric features winsorised at the training 1st/99th percentiles, standardised; missing →
          training median + a missing indicator; binary flags; cycle stage one-hot), ridge λ = 1
  M_INT   M_MAIN + every pairwise product of the standardised numeric features (the interaction ceiling), ridge λ = 10
Fitted by Newton's method (numpy only; no network, no new package). Compared on held-out rows by ROC AUC with a
ticker-cluster bootstrap, against single generic rankings (20-session range = volatility, 5-session drop, volume
ratio, low price, low RSI) and the existing tool's technical part.
Populations scored: all evaluable pivot-days, and the «free» rows the existing reference rules do not flag (where the
missed winners live).
Modes:
  dev    train 2025-05-01 → 09-30, test 2025-10-01 → 12-31 (both inside READYNOW's development window)
  final  train on the whole development window, score validation (2026-01-16 → 05-15) and holdout (06-02 → 08-27)
         once — refused (exit 9) unless DISC_PROTOCOL.md matches the SHA-256 pinned below
Run from the repo root:  python3 faisal_engine/readynow/disc/rn_disc_model.py dev|final   → disc/data/model_<mode>.json
"""
import hashlib
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RN = os.path.dirname(HERE)
sys.path.insert(0, RN)
sys.path.insert(0, HERE)
os.environ["FAISAL_ONLY"] = "1"
import numpy as np                                                        # noqa: E402
import rn_lib as K                                                        # noqa: E402
import rn_disc_dev as D                                                   # noqa: E402

DATA = D.DATA
PROTOCOL = os.path.join(HERE, "DISC_PROTOCOL.md")
PROTOCOL_SHA256 = "a75d21b9bdf15fca0c0bfb2c4be504847f0c822f8dbdafc5c8b1ca765aef20a0"
REPS, SEED = 1000, 20261011
NUM = ("rsi", "rsi_low", "dist", "bounce", "hold_n", "boom5", "dv20", "range20", "tl_dist", "r5", "v1x", "v5x", "tr5x",
       "pos60", "bot_age", "nlow20", "clv5", "pc_bottom_ago", "pc_vs_bottom", "rise_low10", "ret1", "rsi_div_gap",
       "hl_count", "first_up", "px")
LOG = ("dv20", "range20", "v1x", "v5x", "tr5x", "px")
BIN = ("held", "below3", "macd_pos", "ema_up", "ema_x5", "split120", "rsi_div", "rise10_vdry", "v_then_up",
       "pc_first_rise", "loc")
STAGES = ("0", "1", "2", "3", "4")
BASELINES = {"VOLAT_range20": lambda r: K.num(r.get("range20")), "DROP_r5": lambda r: _neg(K.num(r.get("r5"))),
             "VOL_v1x": lambda r: K.num(r.get("v1x")), "LOWPX": lambda r: _neg(K.num(r.get("px"))),
             "LOWRSI": lambda r: _neg(K.num(r.get("rsi"))),
             "TC_TECH": lambda r: 1.0 if K.EXISTING["TC_TECH"](r) else 0.0}


def _neg(x):
    return None if x is None else -x


class Design:
    """Feature matrix with training-set statistics frozen at fit time."""

    def __init__(self, rows, interactions):
        self.inter = interactions
        cols = {}
        for k in NUM:
            v = np.array([np.nan if K.num(r.get(k)) is None else K.num(r.get(k)) for r in rows], dtype=float)
            if k in LOG:
                v = np.log1p(np.clip(v, 0, None))
            cols[k] = v
        self.lo = {k: np.nanpercentile(v, 1) for k, v in cols.items()}
        self.hi = {k: np.nanpercentile(v, 99) for k, v in cols.items()}
        self.med = {}
        self.mu, self.sd = {}, {}
        for k, v in cols.items():
            w = np.clip(v, self.lo[k], self.hi[k])
            self.med[k] = float(np.nanmedian(w))
            w = np.where(np.isnan(w), self.med[k], w)
            self.mu[k], self.sd[k] = float(w.mean()), float(w.std() or 1.0)

    def matrix(self, rows):
        parts, names, z = [], [], []
        for k in NUM:
            v = np.array([np.nan if K.num(r.get(k)) is None else K.num(r.get(k)) for r in rows], dtype=float)
            if k in LOG:
                v = np.log1p(np.clip(v, 0, None))
            miss = np.isnan(v)
            w = np.clip(np.where(miss, self.med[k], v), self.lo[k], self.hi[k])
            w = (w - self.mu[k]) / self.sd[k]
            parts.append(w)
            names.append(k)
            z.append(w)
            if miss.any():
                parts.append(miss.astype(float))
                names.append(k + "_missing")
        for k in BIN:
            parts.append(np.array([1.0 if r.get(k) == "1" else 0.0 for r in rows]))
            names.append(k)
        for s in STAGES:
            parts.append(np.array([1.0 if r.get("pc_stage") == s else 0.0 for r in rows]))
            names.append("stage" + s)
        if self.inter:
            for a in range(len(z)):
                for b in range(a + 1, len(z)):
                    parts.append(z[a] * z[b])
                    names.append(f"{NUM[a]}*{NUM[b]}")
        return np.column_stack(parts), names


def fit(X, y, lam, iters=25):
    """Ridge logistic regression by Newton's method (intercept unpenalised)."""
    Xa = np.column_stack([np.ones(len(X)), X])
    w = np.zeros(Xa.shape[1])
    pen = np.full(Xa.shape[1], lam)
    pen[0] = 0.0
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(Xa @ w, -30, 30)))
        g = Xa.T @ (p - y) + pen * w
        Hm = (Xa * (p * (1 - p))[:, None]).T @ Xa + np.diag(pen)
        step = np.linalg.solve(Hm, g)
        w -= step
        if np.max(np.abs(step)) < 1e-6:
            break
    return w


def score(w, X):
    return np.column_stack([np.ones(len(X)), X]) @ w


def auc(s, y):
    """ROC AUC by mid-ranks (ties count half), vectorised."""
    npos = float(y.sum())
    nneg = len(y) - npos
    if not npos or not nneg:
        return None
    _u, inv, cnt = np.unique(s, return_inverse=True, return_counts=True)
    start = np.concatenate([[0], np.cumsum(cnt)[:-1]])
    ranks = (start + (cnt + 1) / 2.0)[inv]
    return float((ranks[y == 1].sum() - npos * (npos + 1) / 2) / (npos * nneg))


def cluster_auc(scores, y, syms, reps=REPS, seed=SEED, alpha=0.05, base=None):
    """AUC (and AUC − baseline AUC) with a ticker-cluster bootstrap."""
    groups = defaultdict(list)
    for k, s in enumerate(syms):
        groups[s].append(k)
    keys = sorted(groups)
    idx = [np.array(groups[k]) for k in keys]
    rng = np.random.default_rng(seed)
    est = auc(scores, y)
    d_est = (est - auc(base, y)) if base is not None and est is not None else None
    vals, dvals = [], []
    for _ in range(reps):
        pick = np.concatenate([idx[j] for j in rng.integers(0, len(keys), len(keys))])
        a = auc(scores[pick], y[pick])
        if a is None:
            continue
        vals.append(a)
        if base is not None:
            b = auc(base[pick], y[pick])
            if b is not None:
                dvals.append(a - b)
    q = lambda v: [round(float(np.quantile(v, alpha / 2)), 4), round(float(np.quantile(v, 1 - alpha / 2)), 4)] if v else None  # noqa: E731,E501
    return {"auc": round(est, 4) if est is not None else None, "ci": q(vals),
            "minus_base": round(d_est, 4) if d_est is not None else None, "minus_base_ci": q(dvals)}


def baseline_scores(rows, f):
    v = np.array([np.nan if f(r) is None else f(r) for r in rows], dtype=float)
    return np.where(np.isnan(v), np.nanmin(v) - 1 if np.isfinite(np.nanmin(v)) else 0.0, v)


def evaluate(train, test, label="all"):
    ytr = np.array([1.0 if r["lab"] == "POS710" else 0.0 for r in train])
    yte = np.array([1.0 if r["lab"] == "POS710" else 0.0 for r in test])
    syms = [r["sym"] for r in test]
    out = {"population": label, "train_rows": len(train), "train_pos": int(ytr.sum()), "test_rows": len(test),
           "test_pos": int(yte.sum())}
    vol = baseline_scores(test, BASELINES["VOLAT_range20"])
    for name, inter, lam in (("M_MAIN", False, 1.0), ("M_INT", True, 10.0)):
        dz = Design(train, inter)
        Xtr, names = dz.matrix(train)
        w = fit(Xtr, ytr, lam)
        Xte, _n = dz.matrix(test)
        s = score(w, Xte)
        out[name] = cluster_auc(s, yte, syms, base=vol)
        out[name]["train_auc"] = round(auc(score(w, Xtr), ytr), 4)
        top = np.argsort(-np.abs(w[1:]))[:12]
        out[name]["largest_weights"] = [[names[k], round(float(w[1 + k]), 3)] for k in top]
        # precision at the burden of the existing tool on each test session (top-k per session by model score)
        out[name]["_scores"] = s
    for bn, f in BASELINES.items():
        out[bn] = cluster_auc(baseline_scores(test, f), yte, syms)
    for name in ("M_MAIN", "M_INT"):
        out[name].pop("_scores")
    return out


def rows_between(lo, hi):
    rows = K.rd("rows.csv.gz", DATA)
    out = []
    for r in rows:
        if lo <= r["t"] <= hi and r["sym"] not in K.EXCLUDE and r.get("cond_ok") == "1" and r["lab_on"] in K.EVAL:
            out.append(dict(r, lab=r["lab_on"], ep=r["ep_on"]))
    return out


def protocol_ok():
    try:
        return hashlib.sha256(open(PROTOCOL, "rb").read()).hexdigest() == PROTOCOL_SHA256
    except OSError:
        return False


def main(mode):
    if mode == "dev":
        train, test = rows_between("2025-05-01", "2025-09-30"), rows_between("2025-10-01", "2025-12-31")
        res = {"mode": "dev", "train": ["2025-05-01", "2025-09-30"], "test": ["2025-10-01", "2025-12-31"],
               "all": evaluate(train, test, "all"),
               "free": evaluate([r for r in train if not D.union(r)], [r for r in test if not D.union(r)], "free")}
    else:
        if not protocol_ok():
            print("⛔ DISC_PROTOCOL.md differs from the sealed version — nothing scored")
            sys.exit(9)
        train = rows_between(*K.WINDOWS["development"])
        res = {"mode": "final", "train": list(K.WINDOWS["development"])}
        for w in ("validation", "holdout"):
            test = rows_between(*K.WINDOWS[w])
            res[w] = {"all": evaluate(train, test, "all"),
                      "free": evaluate([r for r in train if not D.union(r)], [r for r in test if not D.union(r)], "free")}
    json.dump(res, open(os.path.join(DATA, f"model_{mode}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return res


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else ""
    if m not in ("dev", "final"):
        sys.exit("usage: rn_disc_model.py dev|final")
    r = main(m)
    print(json.dumps(r, ensure_ascii=False, indent=1, default=lambda x: None)[:6000])
