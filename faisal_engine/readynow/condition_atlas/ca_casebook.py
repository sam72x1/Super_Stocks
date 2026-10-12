"""Faisal condition atlas — chart casebook (descriptive; cases never enter a statistic they inspired).

Cases
  seeds         every clean episode of DLXY, RETO, DKI, SXTC (excluded from all statistics)
  HUBC          every episode, reported separately: active, never a completed success
  development   (2025-05-01 → 12-31) the largest eligible events the frozen classifier's READY classes captured and
                the largest it missed; pivot-days with most of Faisal's counted conditions that did not explode;
                one same-session matched inactive pivot-day for each captured or missed case (on the case's first POS710 day)
  2026          the same for validation and holdout, written only after the sealed run (`ca_final.py`)
For every event the dates are kept apart: trough · ONSET (start of the final +70% leg) · first intraday high ≥ +70%
above the trough close · Q (first close ≥ +70%, or the jump's detection) · D1 (first detection) · peak close and peak
intraday gain. For T−10 … T−7 before the onset: the atlas flags that hold, key values, and the frozen axis scores and
class (each from bars ≤ that day).
Run from the repo root:  python3 faisal_engine/readynow/condition_atlas/ca_casebook.py [dev|all]  → data/casebook.json
"""
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np                                                        # noqa: E402
import ca_build as CB                                                     # noqa: E402
import ca_lib as L                                                        # noqa: E402

K, D, B, R = L.K, L.D, CB.B, CB.R
DATA = L.DATA
SEEDS, ACTIVE = ("DLXY", "RETO", "DKI", "SXTC"), ("HUBC",)
LAST_BAR = "2026-10-08"            # the last complete bar of the archive
num = K.num
_BARS = None


def bars():
    global _BARS
    if _BARS is None:
        _meta, b = R.load_bars()
        sp = json.load(open(R.SPLITS_FILE, encoding="utf-8"))["splits"]
        _BARS = (b, sp)
    return _BARS


_ARR = {}


def arrays(sym):
    """Per-symbol arrays: the atlas columns, READY NOW's condition inputs and the bars."""
    if sym in _ARR:
        return _ARR[sym]
    b, sp = bars()
    bb = b[sym]
    bb["fac"] = R.split_factor_after(sp.get(sym, []), bb["d"])
    rs = CB.reverse_splits(sp.get(sym), bb["d"])
    a = CB.symbol_arrays(bb, rs)
    z = B.series(bb)
    sdates = [d for d, r in (sp.get(sym) or []) if r and float(r) < 1.0]
    x = CB.pd.Series(bb["v"])
    base = x.rolling(50).median().shift(11)
    v1x = (x / base.where(base > 0)).to_numpy()
    _ARR[sym] = (bb, a, z, sdates, v1x)
    return _ARR[sym]


def row_at(sym, i):
    """A row with every input the flags read, computed from bars ≤ i (same definitions as the population rows)."""
    bb, a, z, sdates, v1x = arrays(sym)
    r = {"sym": sym, "t": bb["d"][i]}
    cnd = B.conditions(bb, z, i, sdates) or {}
    r.update({k: ("" if v is None else str(v)) for k, v in cnd.items()})
    f = R.features(bb, i)
    r.update({k: ("" if v is None else str(v)) for k, v in f.items()})
    c = bb["c"]
    r["r5"] = str(round((c[i] / c[i - 5] - 1.0) * 100.0, 2)) if i >= 5 and c[i - 5] > 0 else ""
    r["v1x"] = "" if not np.isfinite(v1x[i]) else str(round(float(v1x[i]), 4))
    for k in CB.COLS:
        r[k] = "" if CB._val(a[k][i]) is None else str(CB._val(a[k][i]))
    return r


def frozen():
    return json.load(open(os.path.join(DATA, "model_frozen.json"), encoding="utf-8"))


def axis_scores(r, fz):
    out = {}
    for ax, v in fz.items():
        x = L.design([r], v["features"])[0]
        s = float(v["w"][0] + np.dot(np.asarray(v["w"][1:]), x))
        out[ax] = round(1.0 / (1.0 + np.exp(-s)), 4)
        contrib = sorted(((v["w"][1 + j] * x[j], f) for j, f in enumerate(v["features"]) if x[j]), reverse=True)
        out[ax + "_top"] = [f for c, f in contrib[:3] if c > 0]
        out[ax + "_blockers"] = [f for c, f in sorted(contrib)[:3] if c < 0]
    return out


def event_dates(sym, e):
    bb = arrays(sym)[0]
    ix = bb["ix"]
    tr = ix[e["trough"]]
    c0 = bb["c"][tr]
    pk = ix[e["peak"]]
    first_hi = next((k for k in range(tr + 1, pk + 1) if bb["h"][k] >= 1.70 * c0), None)   # within the episode
    return {"trough": e["trough"], "onset": e["onset"], "first_intraday_+70": bb["d"][first_hi] if first_hi else None,
            "q_+70_close_or_jump": e["q"], "d1": e["d1"], "peak": e["peak"],
            "peak_close_gain_pct": round((bb["c"][pk] / c0 - 1.0) * 100.0, 1),
            "peak_intraday_gain_pct": round((float(np.max(bb["h"][tr + 1: pk + 1])) / c0 - 1.0) * 100.0, 1)
            if pk > tr else None, "kind": e["kind"]}


def timeline(sym, onset, fz, offsets=(10, 9, 8, 7)):
    bb = arrays(sym)[0]
    on = bb["ix"].get(onset)
    out = []
    for k in offsets:
        i = on - k if on is not None else None
        if i is None or i < 60:
            continue
        r = row_at(sym, i)
        flags = [n for n, f in L.COND.items() if f(r)]
        rec = {"T": f"T-{k}", "date": r["t"], "flags": flags, "invalidated": L.invalidated(r),
               "count_score": L.count_score(r), "app_score": L.app_score(r),
               "rsi": r.get("rsi"), "dist": r.get("dist"), "bounce": r.get("bounce"), "hold_n": r.get("hold_n"),
               "r5": r.get("r5"), "range20": r.get("range20"), "v1x": r.get("v1x"), "px": r.get("px")}
        if fz:
            rec.update(axis_scores(r, fz))
        out.append(rec)
    return out


def session_index(fz):
    """Per session of every window: the C and B scores of the valid (non-invalidated) pivot-days and k (the tool's
    technical-part flags), to place an excluded seed day where it would have ranked."""
    import ca_final as CF
    out = {}
    for w in ("development", "validation", "holdout"):
        rows, by, _m = L.load(w)
        for t, rs in by.items():
            for r in rs:
                for ax, (feats, wv) in CF.models(fz).items():
                    r["s_" + ax] = float(CF.M.score(wv, L.design([r], feats))[0])
            ok = [r for r in rs if not L.invalidated(r)]
            out[t] = {"k": sum(1 for r in rs if D.REFS["TC_TECH"](r)), "C": sorted((r["s_C"] for r in ok), reverse=True),
                      "B": sorted(r["s_B"] for r in ok)}
    return out


def would_be(r, fz, sess):
    """The class the day would have received inside its session (descriptive; seeds never entered a statistic)."""
    s = sess.get(r["t"])
    if s is None:
        return "outside the evaluation windows"
    if L.invalidated(r):
        return "INVALIDATED"
    sc = {ax: float(fz[ax]["w"][0] + np.dot(np.asarray(fz[ax]["w"][1:]), L.design([r], fz[ax]["features"])[0]))
          for ax in ("B", "C")}
    j = sum(1 for x in s["C"] if x > sc["C"])
    k = s["k"]
    if j < k:
        return "READY_1"
    if j < 2 * k:
        return "READY_2"
    if j < 4 * k:
        return "READY_3"
    med = s["B"][len(s["B"]) // 2] if s["B"] else 0.0
    return "WATCH" if sc["B"] >= med else "NOT_READY"


def seeds_and_hubc(fz, upto):
    ev = D.unique_events(K.rd("events.csv.gz", D.DATA))
    sess = session_index(fz)
    out = defaultdict(list)
    for e in ev:
        if e["sym"] in SEEDS + ACTIVE and e["quality"] == "OK" and e["onset"] <= upto:
            tl = timeline(e["sym"], e["onset"], fz)
            bb = arrays(e["sym"])[0]
            for t in tl:
                t["would_be_class"] = would_be(row_at(e["sym"], bb["ix"][t["date"]]), fz, sess)
            out[e["sym"]].append({"dates": event_dates(e["sym"], e), "timeline": tl})
    return dict(out)


def window_cases(window, cls, fz, n=6):
    """Largest captured / missed eligible events of a window, partial-condition non-exploders, matched controls."""
    rows, by, _m = L.load(window)
    events, _six = D.events(rows, window)
    ev_all = {(e["sym"], e["onset"]): e for e in D.unique_events(K.rd("events.csv.gz", D.DATA))}
    elig = [e for e in events if e["pos_rows"]]
    gain = {}
    for e in elig:
        x = ev_all.get((e["sym"], e["launch"]))
        gain[(e["sym"], e["launch"])] = num(x["peak_gain"]) if x else None
    ready = ("READY_1", "READY_2", "READY_3")
    cap = [e for e in elig if any(cls.get((r["sym"], r["t"])) in ready for r in e["pos_rows"])]
    mis = [e for e in elig if e not in cap]
    key = lambda e: -(gain[(e["sym"], e["launch"])] or 0.0)          # noqa: E731
    out = {"captured": [], "missed": [], "partial_no_explosion": [], "controls": []}
    for name, lst in (("captured", sorted(cap, key=key)[:n]), ("missed", sorted(mis, key=key)[:n])):
        for e in lst:
            x = ev_all[(e["sym"], e["launch"])]
            case = {"sym": e["sym"], "dates": event_dates(e["sym"], x), "timeline": timeline(e["sym"], e["launch"], fz)}
            for t in case["timeline"]:
                t["would_be_class"] = cls.get((e["sym"], t["date"]), "not a pivot-day")
            out[name].append(case)
            # matched inactive control on the case's first POS710 pivot-day (T−10 … T−7)
            a = min(e["pos_rows"], key=lambda r: r["t"])
            t8 = a["t"]
            if a is not None and all(a.get(k) is not None for k in K.MATCH_KEYS):
                pool = [r for r in by[t8] if r["lab"] == "NEG" and r["sym"] != e["sym"]
                        and K.bucket(r.get("px")) == K.bucket(a.get("px"))
                        and all(r.get(k) is not None and abs(r[k] - a[k]) <= K.CALIPER for k in K.MATCH_KEYS)]
                if pool:
                    c = min(pool, key=lambda r: (sum(abs(r[k] - a[k]) for k in K.MATCH_KEYS), r["sym"]))
                    i = arrays(c["sym"])[0]["ix"][t8]
                    rr = row_at(c["sym"], i)
                    out["controls"].append({"for": f'{e["sym"]}|{e["launch"]}', "sym": c["sym"], "date": t8,
                                            "flags": [nm for nm, f in L.COND.items() if f(rr)],
                                            "count_score": L.count_score(rr), "class": cls.get((c["sym"], t8)),
                                            **(axis_scores(rr, fz) if fz else {})})
    allinv = [e for e in elig if all(L.invalidated(r) for r in e["pos_rows"])]
    anyinv = [e for e in elig if any(L.invalidated(r) for r in e["pos_rows"])]
    top = sorted(elig, key=key)[:20]
    out["invalidation_events"] = {
        "eligible": len(elig), "all_pos_rows_invalidated": len(allinv), "any_pos_row_invalidated": len(anyinv),
        "top20_by_peak_all_invalidated": sum(1 for e in top if e in allinv),
        "captured_by_ready_and_all_invalidated": sum(1 for e in cap if e in allinv)}
    neg = sorted((r for r in rows if r["lab"] == "NEG" and r["sym"] not in SEEDS + ACTIVE),
                 key=lambda r: (-L.count_score(r), r["t"], r["sym"]))
    seen = set()
    for r in neg:
        if r["sym"] in seen:
            continue
        seen.add(r["sym"])
        out["partial_no_explosion"].append({"sym": r["sym"], "date": r["t"], "count_score": L.count_score(r),
                                            "flags": [nm for nm in L.COUNT_SET if L.COND[nm](r)],
                                            "missing": [nm for nm in L.COUNT_SET if not L.COND[nm](r)],
                                            "class": cls.get((r["sym"], r["t"]))})
        if len(out["partial_no_explosion"]) >= n:
            break
    return out


def main(mode):
    import ca_final as CF
    fz = frozen()
    res = {"generated_for": mode}
    cls_dev = CF.classify_window("development", fz)
    res["development"] = window_cases("development", cls_dev, fz)
    if mode == "all":
        if not CF.protocol_ok():
            print("⛔ CA_PROTOCOL.md differs from the sealed version — 2026 cases not written")
            sys.exit(9)
        for w in ("validation", "holdout"):
            res[w] = window_cases(w, CF.classify_window(w, fz), fz)
        res["seeds_and_hubc"] = seeds_and_hubc(fz, upto=LAST_BAR)
    json.dump(res, open(os.path.join(DATA, "casebook.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return res


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else "dev"
    if m not in ("dev", "all"):
        sys.exit("usage: ca_casebook.py dev|all")
    main(m)
    print("written data/casebook.json")
