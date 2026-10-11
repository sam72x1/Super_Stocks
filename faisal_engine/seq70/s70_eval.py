"""SEQ70 — the sealed test of one sequence hypothesis (one run). Refuses to read any validation or test row unless
S70_PREREG.md matches its hash.

Hypothesis (from the discovery window only, s70_explore.py E4 → C-A): on a pivot-day whose 5-session return is
still negative, a volume day in the session's top quintile (v1x) marks a higher chance of the +70% condition within
10 sessions than (K-V) the same drop and volatility without that volume, and (K-P) the same volume and volatility
without the drop. Run from the repo root:  python3 faisal_engine/seq70/s70_eval.py test
"""
import bisect
import csv
import gzip
import hashlib
import json
import os
import random
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
PREREG = os.path.join(HERE, "S70_PREREG.md")
PREREG_SHA256 = "1b511ab3ff5c8a0fbdaa959ebf457b6a21e20523e465f6bf142f41140aeecdeb"   # sealed 2026-10-11 before any validation or test outcome was read
WINDOWS = {"validation": ("2026-01-16", "2026-05-15"), "test": ("2026-06-02", "2026-09-24")}
DEV_WINDOW = {"discovery": ("2025-05-01", "2025-12-31")}     # `dev` mode: the same code on discovery rows only
BOOT, SEED, ALPHA = 2000, 20261011, 0.0125      # 98.75% two-sided = Bonferroni over 2 comparisons × 2 windows
FLOOR_ROWS, FLOOR_EVENTS, FLOOR_PAIRS = 300, 20, 250
TOP_Q = 0.8
SIGNAL = "v1x"                # the hypothesis' volume descriptor (C-A); C-B/C-C use v5x/tr5x in s70_explore E5
CALIPER = 0.10                # each matched within-session percentile within 0.10 of the flagged row's


def prereg_ok():
    return bool(PREREG_SHA256) and os.path.exists(PREREG) and \
        hashlib.sha256(open(PREREG, "rb").read()).hexdigest() == PREREG_SHA256


def rd(name):
    with gzip.open(os.path.join(DATA, name), "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def q(v, p):
    v = sorted(v)
    return v[int(p * (len(v) - 1))] if v else None


def bucket(px):
    px = num(px)
    return None if px is None else (0 if px < 1 else 1 if px < 3 else 2 if px < 10 else 3)


def day_pct(rows, key):
    vals = sorted(num(r[key]) for r in rows if num(r[key]) is not None)
    n = len(vals)
    out = {}
    for r in rows:
        x = num(r[key])
        if x is None or not n:
            continue
        lo, hi = bisect.bisect_left(vals, x), bisect.bisect_right(vals, x)
        out[r["sym"]] = (lo + 0.5 * (hi - lo)) / n
    return out


def annotate(rows):
    """Within-session percentiles of v1x, v5x, tr5x, r5, range20 among the rows of each session (clean pivot-days)."""
    by = defaultdict(list)
    for r in rows:
        by[r["t"]].append(r)
    for t, rs in by.items():
        p = {k: day_pct(rs, k) for k in ("v1x", "v5x", "tr5x", "r5", "range20")}
        for r in rs:
            for k in p:
                r["p_" + k] = p[k].get(r["sym"])
    return by


def flagged(r, sk=None):
    sk = sk or SIGNAL
    return (r.get("p_" + sk) is not None and r["p_" + sk] >= TOP_Q and num(r["r5"]) is not None and num(r["r5"]) < 0)


def match(by, ev_keys, mode, sk=None):
    """mode 'V': controls not flagged, nearest on p_r5 + p_range20 · mode 'P': controls with r5 ≥ 0, nearest on
    p_v1x + p_range20. Same session, same traded-price bucket, each matched percentile within CALIPER, without
    replacement, ties by symbol; no candidate ⇒ unmatched (counted, dropped)."""
    sk = sk or SIGNAL
    pairs, unmatched = [], 0
    for t in sorted(by):
        rs = [r for r in by[t] if (r["sym"], t) in ev_keys]
        fl = sorted((r for r in rs if flagged(r, sk)), key=lambda r: r["sym"])
        if mode == "V":
            pool = [r for r in rs if not flagged(r, sk) and r.get("p_r5") is not None and r.get("p_range20") is not None]
            keys = ("p_r5", "p_range20")
        else:
            pool = [r for r in rs if num(r["r5"]) is not None and num(r["r5"]) >= 0 and r.get("p_" + sk) is not None
                    and r.get("p_range20") is not None]
            keys = ("p_" + sk, "p_range20")
        used = set()
        for a in fl:
            if any(a.get(k) is None for k in keys):
                unmatched += 1
                continue
            bk = bucket(a["px"])
            cand = [c for c in pool if c["sym"] not in used and bucket(c["px"]) == bk
                    and all(abs(c[k] - a[k]) <= CALIPER for k in keys)]
            if not cand:
                unmatched += 1
                continue
            c = min(cand, key=lambda c: (sum(abs(c[k] - a[k]) for k in keys), c["sym"]))
            used.add(c["sym"])
            pairs.append((a, c))
    return pairs, unmatched


def cluster_ratio(pairs, label="f10", reps=BOOT, seed=SEED, alpha=ALPHA):
    units = defaultdict(lambda: [0, 0, 0, 0])
    for a, c in pairs:
        u = units[a["sym"]]
        u[0] += 1
        u[1] += a[label] == "POS"
        u[2] += 1
        u[3] += c[label] == "POS"
    keys = sorted(units)
    tot = [sum(units[k][j] for k in keys) for j in range(4)]

    def ratio(t):
        return (t[1] / t[0]) / (t[3] / t[2]) if t[0] and t[2] and t[3] else None
    rnd = random.Random(seed)
    vals = []
    for _ in range(reps):
        t = [0, 0, 0, 0]
        for _k in keys:
            v = units[keys[rnd.randrange(len(keys))]]
            for j in range(4):
                t[j] += v[j]
        x = ratio(t)
        if x is not None:
            vals.append(x)
    vals.sort()
    pt = ratio(tot)
    lo = vals[int(alpha / 2 * len(vals))] if vals else None
    hi = vals[min(len(vals) - 1, int((1 - alpha / 2) * len(vals)))] if vals else None
    return {"point": round(pt, 3) if pt else None, "lo": round(lo, 3) if lo else None, "hi": round(hi, 3) if hi else None,
            "flag_pos": tot[1], "flag_rows": tot[0], "ctrl_pos": tot[3], "ctrl_rows": tot[2],
            "flag_rate": round(tot[1] / tot[0], 4) if tot[0] else None,
            "ctrl_rate": round(tot[3] / tot[2], 4) if tot[2] else None, "clusters": len(keys), "reps_ok": len(vals)}


def window_eval(all_rows, events, cal, w):
    lo_d, hi_d = dict(WINDOWS, **DEV_WINDOW)[w]
    cix = {d: i for i, d in enumerate(cal)}
    rows = [r for r in all_rows if lo_d <= r["t"] <= hi_d]
    clean = [r for r in rows if r["split60"] == "0" and r["desc_ok"] == "1"]
    by = annotate(clean)
    ev = [r for r in clean if r["f10"] in ("POS", "NEG")]
    ev_keys = {(r["sym"], r["t"]) for r in ev}
    out = {"window": [lo_d, hi_d], "pivot_days": len(rows), "clean": len(clean), "evaluable": len(ev),
           "sessions": len(by), "labels": dict(Counter(r["f10"] for r in clean))}
    fl = [r for r in ev if flagged(r)]
    out["flagged_evaluable"] = len(fl)
    out["base_rate"] = round(sum(r["f10"] == "POS" for r in ev) / len(ev), 4) if ev else None
    out["flag_rate"] = round(sum(r["f10"] == "POS" for r in fl) / len(fl), 4) if fl else None
    pos_ev = {(r["sym"], cix[r["t"]] + int(float(r["f10_k"]))) for r in fl if r["f10"] == "POS" and r["f10_k"]}
    out["distinct_positive_events_flagged"] = len(pos_ev)
    pv, uv = match(by, ev_keys, "V")
    pp, up = match(by, ev_keys, "P")
    out["K_V"] = dict(cluster_ratio(pv), pairs=len(pv), unmatched=uv)
    out["K_P"] = dict(cluster_ratio(pp), pairs=len(pp), unmatched=up)
    out["_pairs"] = {"K_V": pv, "K_P": pp}
    for nm, pr in (("K_V", pv), ("K_P", pp)):
        out[nm]["median_v1x_pct"] = [q([a["p_v1x"] for a, _ in pr], .5), q([c["p_v1x"] for _, c in pr], .5)]
        out[nm]["median_r5"] = [q([num(a["r5"]) for a, _ in pr], .5), q([num(c["r5"]) for _, c in pr], .5)]
        out[nm]["median_range20_pct"] = [q([a["p_range20"] for a, _ in pr], .5), q([c["p_range20"] for _, c in pr], .5)]
    out["floor_ok"] = (len(fl) >= FLOOR_ROWS and len(pos_ev) >= FLOOR_EVENTS and len(pv) >= FLOOR_PAIRS
                       and len(pp) >= FLOOR_PAIRS)
    # ── descriptive ──
    d = {}
    d["flags_per_session"] = round(sum(1 for r in clean if flagged(r)) / max(1, len(by)), 2)
    d["flagged_f10_neg_share"] = round(sum(r["f10"] == "NEG" for r in fl) / len(fl), 4) if fl else None
    ks = [int(float(r["f10_k"])) for r in fl if r["f10"] == "POS" and r["f10_k"]]
    d["flag_to_70_sessions_q25_med_q75"] = [q(ks, .25), q(ks, .5), q(ks, .75)]
    # trigger episodes: first flag of a symbol after at least 5 sessions without one
    last, trig = {}, []
    for r in sorted((r for r in clean if flagged(r)), key=lambda r: (r["sym"], r["t"])):
        k = cix[r["t"]]
        if r["sym"] not in last or k - last[r["sym"]] > 5:
            trig.append(r)
        last[r["sym"]] = k
    tl = [r for r in trig if r["f10"] in ("POS", "NEG")]
    d["trigger_episodes"] = len(trig)
    d["trigger_episodes_evaluable"] = len(tl)
    d["trigger_precision_f10"] = round(sum(r["f10"] == "POS" for r in tl) / len(tl), 4) if tl else None
    d["false_triggers_per_session"] = round(sum(r["f10"] == "NEG" for r in tl) / max(1, len(by)), 2)
    # recall and lead on eligible events: OK episodes with D1 in the window, a clean pivot-day in [L-10, D1-1]
    days_of = defaultdict(dict)
    for r in clean:
        days_of[r["sym"]][r["t"]] = r
    el, cap70, capL, lead_L, lead_D1, lead_L10, cap_vk, cap_dk = 0, 0, 0, [], [], [], 0, 0
    # burden-matched generic flags each session: k = number of flagged rows that session
    topv, lowr = set(), set()
    for t, rs in by.items():
        k = sum(1 for r in rs if flagged(r))
        if not k:
            continue
        rv = sorted((r for r in rs if r.get("p_v1x") is not None), key=lambda r: (-r["p_v1x"], r["sym"]))[:k]
        rr = sorted((r for r in rs if num(r["r5"]) is not None), key=lambda r: (num(r["r5"]), r["sym"]))[:k]
        topv |= {(r["sym"], t) for r in rv}
        lowr |= {(r["sym"], t) for r in rr}
    for e in events:
        if not (lo_d <= e["d1"] <= hi_d) or e["quality"] != "OK" or e["launch"] not in cix or e["d1"] not in cix:
            continue
        L, D1, L10 = cix[e["launch"]], cix[e["d1"]], cix.get(e["l10"])
        span = [cal[k] for k in range(max(0, L - 10), D1)]
        seen = [d_ for d_ in span if d_ in days_of[e["sym"]]]
        if not seen:
            continue
        el += 1
        fdays = [d_ for d_ in seen if flagged(days_of[e["sym"]][d_])]
        if fdays:
            cap70 += 1
            f0 = cix[fdays[0]]
            lead_L.append(L - f0)
            lead_D1.append(D1 - f0)
            if L10 is not None:
                lead_L10.append(L10 - f0)
            if f0 < L:
                capL += 1
        cap_vk += any((e["sym"], d_) in topv for d_ in seen)
        cap_dk += any((e["sym"], d_) in lowr for d_ in seen)
    d["eligible_events"] = el
    d["recall_before_70"] = [cap70, round(cap70 / el, 4) if el else None]
    d["recall_before_start"] = [capL, round(capL / el, 4) if el else None]
    d["lead_first_flag_to_start_q25_med_q75"] = [q(lead_L, .25), q(lead_L, .5), q(lead_L, .75)]
    d["lead_first_flag_to_start_L10_q25_med_q75"] = [q(lead_L10, .25), q(lead_L10, .5), q(lead_L10, .75)]
    d["lead_first_flag_to_70_q25_med_q75"] = [q(lead_D1, .25), q(lead_D1, .5), q(lead_D1, .75)]
    d["burden_matched_recall_before_70"] = {"VOL-k (top v1x, any price)": [cap_vk, round(cap_vk / el, 4) if el else None],
                                            "DROP-k (lowest r5)": [cap_dk, round(cap_dk / el, 4) if el else None]}
    rv_rows = [r for r in ev if (r["sym"], r["t"]) in topv]
    rd_rows = [r for r in ev if (r["sym"], r["t"]) in lowr]
    d["burden_matched_rate"] = {"VOL-k": round(sum(r["f10"] == "POS" for r in rv_rows) / len(rv_rows), 4) if rv_rows else None,
                                "DROP-k": round(sum(r["f10"] == "POS" for r in rd_rows) / len(rd_rows), 4) if rd_rows else None,
                                "rows": [len(rv_rows), len(rd_rows)]}
    # sensitivity: horizon 20 and the strict label on the same pairs; split rows included
    d["sens_f20"] = {nm: cluster_ratio([(a, c) for a, c in pr if a["f20"] in ("POS", "NEG") and c["f20"] in ("POS", "NEG")],
                                       label="f20", reps=500, alpha=0.05) for nm, pr in (("K_V", pv), ("K_P", pp))}
    d["sens_y10"] = {nm: cluster_ratio([(a, c) for a, c in pr if a["y10"] in ("POS", "NEG") and c["y10"] in ("POS", "NEG")],
                                       label="y10", reps=500, alpha=0.05) for nm, pr in (("K_V", pv), ("K_P", pp))}
    allr = [r for r in rows if r["desc_ok"] == "1"]
    by2 = annotate([dict(r) for r in allr])
    ev2 = {(r["sym"], t) for t, rs in by2.items() for r in rs if r["f10"] in ("POS", "NEG")}
    pv2, _u = match(by2, ev2, "V")
    pp2, _u = match(by2, ev2, "P")
    d["sens_split_rows_included"] = {"K_V": cluster_ratio(pv2, reps=500, alpha=0.05),
                                     "K_P": cluster_ratio(pp2, reps=500, alpha=0.05)}
    bt = [r for r in fl if r.get("bt_src")]
    d["bot_tracked_flagged"] = {"rows": len(bt), "pos": sum(r["f10"] == "POS" for r in bt),
                                "by_src": dict(Counter(r["bt_src"] for r in bt)),
                                "bot_ready": sum(1 for r in bt if r.get("bot_ready") == "1")}
    out["descriptive"] = d
    return out


def test():
    if not prereg_ok():
        print("⛔ S70_PREREG.md missing or changed — no validation or test row is read.")
        sys.exit(9)
    traj = rd("traj.csv.gz")
    events = rd("events.csv.gz")
    cal = sorted({r["t"] for r in traj})
    res = {"prereg_sha256": PREREG_SHA256, "windows": WINDOWS, "alpha": ALPHA, "boot": BOOT, "seed": SEED}
    for w in WINDOWS:
        res[w] = window_eval(traj, events, cal, w)
    v, t = res["validation"], res["test"]
    pooled = {k: cluster_ratio(v["_pairs"][k] + t["_pairs"][k], alpha=0.05) for k in ("K_V", "K_P")}
    for x in (v, t):
        x.pop("_pairs")
    res["pooled_out_of_sample_95"] = pooled
    floors = v["floor_ok"] and t["floor_ok"]
    los = [x[k]["lo"] or 0 for x in (v, t) for k in ("K_V", "K_P")]
    if not (v["floor_ok"] or t["floor_ok"]):
        dec = "INSUFFICIENT_OR_UNLINKABLE_DATA"
    elif floors and all(x > 1.0 for x in los):
        dec = "VALIDATED_INCREMENTAL_SIGNAL"
    elif all((pooled[k]["lo"] or 0) > 1.0 for k in ("K_V", "K_P")):
        dec = "PROMISING_UNVALIDATED"
    else:
        dec = "NO_INCREMENTAL_EDGE_FOUND"
    res["floors_ok_both"] = floors
    res["decision"] = dec
    json.dump(res, open(os.path.join(DATA, "result.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({w: {k: res[w][k] for k in ("base_rate", "flag_rate", "flagged_evaluable",
                                                  "distinct_positive_events_flagged", "K_V", "K_P", "floor_ok")}
                      for w in WINDOWS}, ensure_ascii=False, indent=1))
    print("DECISION:", dec)


def dev():
    """The sealed code path on the discovery window only (no seal needed, no validation/test row read)."""
    traj = [r for r in rd("traj.csv.gz") if r["t"] <= DEV_WINDOW["discovery"][1]]
    events = [e for e in rd("events.csv.gz") if e["d1"] <= DEV_WINDOW["discovery"][1]]
    cal = sorted({r["t"] for r in traj})
    out = window_eval(traj, events, cal, "discovery")
    out.pop("_pairs")
    json.dump(out, open(os.path.join(DATA, "dev_discovery.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: out[k] for k in ("base_rate", "flag_rate", "flagged_evaluable", "distinct_positive_events_flagged",
                                          "K_V", "K_P", "floor_ok")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if (sys.argv[1:] or [""])[0] == "test":
        test()
    elif (sys.argv[1:] or [""])[0] == "dev":
        dev()
    else:
        print("usage: s70_eval.py test | dev")
        sys.exit(2)
