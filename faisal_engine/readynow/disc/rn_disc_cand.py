"""READY NOW discovery — the candidate readiness conditions and paths (declared here before any candidate rate was
computed; the only numbers seen beforehand were the seed windows and the quartile map of `rn_disc_dev.py`).

Observation behind them (`rn_disc_seeds.py`): in several seed episodes the pivot printed an extreme single-day volume
burst with a flat-to-rising close 7–10 sessions before the start of the final +70% leg — DLXY 2026-09-01 (v1x 59.8,
r5 +13.2), RETO 2026-02-13 (v1x 114.3, r5 +13.3), and in the April DLXY window (v1x 15.7 with r5 −13.1, already
SEQ70's H-S70 path). None of the reference rules flags the rising-close bursts. The nearest prior measurements were on
other populations or leads (T-PRELINK `vol_x0 ≥ 10` on alert anchors · T-LINK100 `vol_x ≥ 3` the day before ·
T-RANKER3 `A1` as a ranker · READY70 VOL-k · SEQ70 H-S70 for r5 < 0) — see READY_DISCOVERY.md §1.

Definitions (bars ≤ T only; v1x = volume / median volume of sessions j−60 .. j−11, SEQ70's definition; the burst
threshold is the production constant `VOL_SPIKE_MULT` = 5, «شمعة الفوليوم الضخمة ≥ 5x», not a fitted value):
  BURST_UP     v1x(T) ≥ 5 ∧ r5(T) ≥ 0                       a burst today, close not lower than 5 sessions ago
  BURST_UP_3   max v1x(T−2 .. T) ≥ 5 ∧ r5(T) ≥ 0           the same with the burst on any of the last 3 sessions
  BURST_ANY_3  max v1x(T−2 .. T) ≥ 5                        the burst alone (any direction) — separates «burst» from
                                                           «burst with a rising close»
  PATH2        REF_UNION ∨ BURST_UP_3                       two readiness paths: the existing capitulation rules + the
                                                           burst path
  CAPIT_TC     on each session, the k pivot-days with the highest p_range20 + (1 − p_r5), k = the number the tool's
               technical part (TC_TECH) flags that session — the profile of the captured group A in development
               (RSI ≈ 34, r5 ≈ −11%, range20 ≈ 88%, close at the 60-session low; `dev_map.json`) as one explainable
               ranking (p_ = within-session mid-rank percentile among pivot-days); asks whether «falling» adds to
               «volatile» at the tool's own burden
  TC_OR_CAPIT  TC_TECH ∨ CAPIT_TC — two paths (oversold-and-held · volatile-and-falling); added after the development
               paired table showed the two capture almost disjoint event sets (CAPIT 59, TC_TECH 44, both 3)
Controls: the reference rules (`rn_disc_dev.REFS`), equal-burden rankings by volume (VOL_k), volatility (VOLAT_k),
low price (LOWPX_k), 5-session momentum (MOM_k), 5-session drop (DROP_k) and low RSI (LOWRSI_k), and same-session
controls matched on volume, volatility and dollar volume percentiles and price bucket (`rn_lib.matched`).
Modes:
  dev    the development window only (2025-05-01 → 12-31), with chronological halves   → disc/data/cand_dev.json
  final  validation (2026-01-16 → 05-15) and holdout (06-02 → 08-27) once — refused (exit 9) unless DISC_PROTOCOL.md
         matches the SHA-256 pinned below                                                → disc/data/cand_final.json
Run from the repo root:  python3 faisal_engine/readynow/disc/rn_disc_cand.py dev|final
"""
import bisect
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
import pandas as pd                                                       # noqa: E402
import rn_build as B                                                      # noqa: E402
import rn_disc_dev as D                                                   # noqa: E402
import rn_lib as K                                                        # noqa: E402

R = B.R
DATA = D.DATA
PROTOCOL = os.path.join(HERE, "DISC_PROTOCOL.md")
PROTOCOL_SHA256 = "a75d21b9bdf15fca0c0bfb2c4be504847f0c822f8dbdafc5c8b1ca765aef20a0"
REPS, SEED = 2000, 20261011
SPIKE = float(R.S().CONFIG["VOL_SPIKE_MULT"])          # 5.0 — production constant, read at call time
BASE = (60, 11)                                        # SEQ70's v1x baseline (sessions j−60 .. j−11)
num = K.num
HALVES = {"development": (("2025-05-01", "2025-08-31"), ("2025-09-01", "2025-12-31")),
          "validation": (("2026-01-16", "2026-03-15"), ("2026-03-16", "2026-05-15")),
          "holdout": (("2026-06-02", "2026-07-15"), ("2026-07-16", "2026-08-27"))}


def v1x_series(v):
    """v1x at every session: v[j] / median(v[j−60 .. j−11]) (NaN when the baseline is missing or zero)."""
    s = pd.Series(np.asarray(v, dtype=float))
    base = s.rolling(BASE[0] - BASE[1] + 1).median().shift(BASE[1])
    out = (s / base.where(base > 0)).to_numpy()
    return out


def add_burst(rows):
    """Adds `vmax3` (max v1x over T−2 .. T, from bars ≤ T) and `v1x_bars` (today's, for the identity check)."""
    _meta, bars = R.load_bars()
    by = defaultdict(list)
    for r in rows:
        by[r["sym"]].append(r)
    for sym, rs in by.items():
        b = bars.get(sym)
        if b is None:
            continue
        x = v1x_series(b["v"])
        for r in rs:
            i = b["ix"].get(r["t"])
            if i is None:
                continue
            w = x[max(0, i - 2): i + 1]
            w = w[np.isfinite(w)]
            r["vmax3"] = float(w.max()) if len(w) else None
            r["v1x_bars"] = float(x[i]) if np.isfinite(x[i]) else None
    return rows


def _r5_ok(r):
    v = num(r.get("r5"))
    return v is not None and v >= 0


def burst_up(r):
    v = num(r.get("v1x"))
    return v is not None and v >= SPIKE and _r5_ok(r)


def burst_up_3(r):
    v = r.get("vmax3")
    return v is not None and v >= SPIKE and _r5_ok(r)


def burst_any_3(r):
    v = r.get("vmax3")
    return v is not None and v >= SPIKE


def path2(r):
    return D.union(r) or burst_up_3(r)


CANDS = {"BURST_UP": burst_up, "BURST_UP_3": burst_up_3, "BURST_ANY_3": burst_any_3, "PATH2": path2}
REFS = {"TC_TECH": D.REFS["TC_TECH"], "H_S70": D.REFS["H_S70"], "REF_UNION": D.union}


def _mom(r):
    return num(r.get("r5"))


def load(window):
    """The window's rows on the corrected target, annotated, with the burst columns and p_r5."""
    rows, _by = D.load(window)
    add_burst(rows)
    by = K.annotate(rows)
    for rs in by.values():
        vals = sorted(v for v in (num(r.get("r5")) for r in rs) if v is not None)
        for r in rs:
            x = num(r.get("r5"))
            if x is None or not vals:
                r["p_r5"] = None
                continue
            lo, hi = bisect.bisect_left(vals, x), bisect.bisect_right(vals, x)
            r["p_r5"] = (lo + 0.5 * (hi - lo)) / len(vals)
    return rows, by


def capit_score(r):
    a, b = r.get("p_range20"), r.get("p_r5")
    return None if a is None or b is None else a + (1.0 - b)


def _period(rows, events, six, lo, hi, f, name):
    rs = [r for r in rows if lo <= r["t"] <= hi]
    by = defaultdict(list)
    for r in rs:
        by[r["t"]].append(r)
    ev = [e for e in events if e["pos_rows"] and lo <= min(r["t"] for r in e["pos_rows"]) <= hi]
    er = [r for r in rs if r["lab"] in K.EVAL]
    fl = [r for r in er if f(r)]
    pos = sum(r["lab"] == "POS710" for r in fl)
    bp = sum(r["lab"] == "POS710" for r in er)
    u = defaultdict(lambda: [0, 0, 0, 0])
    for r in er:
        x = u[r["sym"]]
        x[2] += 1
        x[3] += r["lab"] == "POS710"
        if f(r):
            x[0] += 1
            x[1] += r["lab"] == "POS710"
    lift, ci = K.cluster_ratio(u, REPS, SEED, 0.05)
    cap = sum(1 for e in ev if any(f(r) for r in e["pos_rows"]))
    return {"period": [lo, hi], "flagged": len(fl), "pos": pos, "precision": round(pos / len(fl), 4) if fl else None,
            "precision_ci95": K.wilson(pos, len(fl)), "base": round(bp / len(er), 4) if er else None,
            "lift": lift, "lift_ci": ci, "events_eligible": len(ev), "events_captured": cap,
            "flags_per_session": round(sum(1 for r in rs if f(r)) / max(len(by), 1), 2), "rule": name}


def beyond(rows, events, f, ref):
    """What `f` adds over `ref`: events captured by f and not by ref, and the flags it adds that ref does not raise."""
    elig = [e for e in events if e["pos_rows"]]
    add_ev = [e for e in elig if any(f(r) for r in e["pos_rows"]) and not any(ref(r) for r in e["pos_rows"])]
    er = [r for r in rows if r["lab"] in K.EVAL]
    extra = [r for r in er if f(r) and not ref(r)]
    ep = sum(r["lab"] == "POS710" for r in extra)
    sess = len({r["t"] for r in rows})
    free = [r for r in er if not ref(r)]
    fb = sum(r["lab"] == "POS710" for r in free)
    return {"events_added": len(add_ev), "events_added_list": sorted(f'{e["sym"]}|{e["launch"]}' for e in add_ev),
            "extra_flags_evaluable": len(extra), "extra_true": ep, "extra_false": len(extra) - ep,
            "extra_precision": round(ep / len(extra), 4) if extra else None, "extra_precision_ci95": K.wilson(ep, len(extra)),
            "extra_flags_per_session": round(sum(1 for r in rows if f(r) and not ref(r)) / max(sess, 1), 2),
            "free_base": round(fb / len(free), 4) if free else None}


def independence(rows, f):
    """Share flagged and precision by traded-price bucket and by quartiles of volatility (range20) and liquidity (dv20)."""
    er = [r for r in rows if r["lab"] in K.EVAL]
    out = {}
    for key in ("range20", "dv20"):
        vals = sorted(x for x in (num(r.get(key)) for r in er) if x is not None)
        cuts = [vals[int(len(vals) * q)] for q in (.25, .5, .75)]
        cells = defaultdict(list)
        for r in er:
            x = num(r.get(key))
            cells["missing" if x is None else f"Q{sum(x > c for c in cuts) + 1}"].append(r)
        out[key] = {k: _cell(v, f) for k, v in sorted(cells.items())}
    cells = defaultdict(list)
    for r in er:
        cells[str(K.bucket(r.get("px")))].append(r)
    out["px_bucket"] = {k: _cell(v, f) for k, v in sorted(cells.items())}
    return out


def _cell(rs, f):
    fl = [r for r in rs if f(r)]
    p = sum(r["lab"] == "POS710" for r in fl)
    bp = sum(r["lab"] == "POS710" for r in rs)
    return {"n": len(rs), "flag_share": round(len(fl) / len(rs), 4) if rs else None,
            "precision": round(p / len(fl), 4) if fl else None, "cell_base": round(bp / len(rs), 4) if rs else None,
            "flagged": len(fl)}


def run_window(window, halves=True):
    rows, by = load(window)
    cal = json.load(open(os.path.join(K.DATA, "calendar.json"), encoding="utf-8"))["sessions"]
    ev = [dict(e, launch=e["onset"], x70=e["q"]) for e in K.rd("events.csv.gz", DATA)]
    events = K.events_index(rows, ev, cal, window)
    six = {d: k for k, d in enumerate(cal)}
    chk = [r for r in rows if num(r.get("v1x")) is not None and r.get("v1x_bars") is not None]
    ident = max((abs(num(r["v1x"]) - r["v1x_bars"]) / max(1.0, abs(r["v1x_bars"])) for r in chk), default=None)
    er = [r for r in rows if r["lab"] in K.EVAL]
    out = {"window": K.WINDOWS[window], "rows": len(rows), "evaluable": len(er),
           "base_rate": round(sum(r["lab"] == "POS710" for r in er) / len(er), 4),
           "eligible_events": sum(1 for e in events if e["pos_rows"]), "spike_mult": SPIKE,
           "v1x_identity_rows": len(chk), "v1x_identity_max_rel_diff": ident,
           "vmax3_missing": sum(1 for r in rows if r.get("vmax3") is None), "rules": {}}
    capit = K.burden_match(by, D.REFS["TC_TECH"], capit_score)
    cands = dict(CANDS, CAPIT_TC=lambda r: (r["sym"], r["t"]) in capit,
                 TC_OR_CAPIT=lambda r: D.REFS["TC_TECH"](r) or (r["sym"], r["t"]) in capit)
    saved = dict(K.BURDEN_SCORES)
    K.BURDEN_SCORES["MOM_k"] = _mom
    K.BURDEN_SCORES["DROP_k"] = PAIRED_CONTROLS["DROP_k"]
    K.BURDEN_SCORES["LOWRSI_k"] = PAIRED_CONTROLS["LOWRSI_k"]
    try:
        for name, f in list(REFS.items()) + list(cands.items()):
            e = K.evaluate(rows, by, events, six, f, REPS, SEED, 0.05, name)
            m = K.matched(by, f, REPS, SEED, 0.05)
            res = {k: e[k] for k in ("flags_per_session", "triggers_per_session", "evaluable_flagged", "pos710_flagged",
                                     "precision", "precision_ci95", "fpr", "lift", "lift_ci", "events_captured",
                                     "events_eligible", "recall", "recall_ci95", "trigger_precision",
                                     "trigger_precision_ci95", "lead_to_onset_q25_med_q75", "lead_to_x70_q25_med_q75",
                                     "flagged_tickers")}
            for bn in ("VOL_k", "VOLAT_k", "LOWPX_k", "MOM_k", "DROP_k", "LOWRSI_k"):
                res[bn] = e[bn]
            res["matched"] = {k: m[k] for k in ("pairs", "unmatched", "flag_rate", "ctrl_rate", "ratio", "ci")}
            if name in cands:
                res["beyond_REF_UNION"] = beyond(rows, events, f, D.union)
                res["beyond_TC_TECH"] = beyond(rows, events, f, D.REFS["TC_TECH"])
                res["independence"] = independence(rows, f)
                if halves:
                    res["halves"] = [_period(rows, events, six, lo, hi, f, name) for lo, hi in HALVES[window]]
            out["rules"][name] = res
    finally:
        K.BURDEN_SCORES.clear()
        K.BURDEN_SCORES.update(saved)
    out["capit_paired"], units = paired(rows, by, events, capit)
    return out, units


PAIRED_CONTROLS = {"TC_TECH": None,
                   "VOLAT_k": lambda r: num(r.get("range20")),
                   "DROP_k": lambda r: _neg(num(r.get("r5"))),
                   "LOWRSI_k": lambda r: _neg(num(r.get("rsi")))}


def _neg(x):
    return None if x is None else -x


def paired(rows, by, events, capit):
    """CAPIT_TC against the tool's technical part and three single generic rankings at the same per-session burden:
    precision difference (percentage points, ticker-cluster CI) and events captured. Returns (summary, units)."""
    tc = D.REFS["TC_TECH"]
    er = [r for r in rows if r["lab"] in K.EVAL]
    elig = [e for e in events if e["pos_rows"]]
    a_cap = {f'{e["sym"]}|{e["launch"]}' for e in elig if any((r["sym"], r["t"]) in capit for r in e["pos_rows"])}
    out, units = {}, {}
    for name, score in PAIRED_CONTROLS.items():
        ctl = {(r["sym"], r["t"]) for r in rows if tc(r)} if score is None else K.burden_match(by, tc, score)
        u = defaultdict(lambda: [0, 0, 0, 0])
        for r in er:
            key = (r["sym"], r["t"])
            x = u[r["sym"]]
            if key in capit:
                x[0] += 1
                x[1] += r["lab"] == "POS710"
            if key in ctl:
                x[2] += 1
                x[3] += r["lab"] == "POS710"
        d, ci = K.cluster_diff(u, REPS, SEED, 0.05)
        b_cap = {f'{e["sym"]}|{e["launch"]}' for e in elig if any((r["sym"], r["t"]) in ctl for r in e["pos_rows"])}
        tot = [sum(v[k] for v in u.values()) for k in range(4)]
        out[name] = {"capit_flags": tot[0], "capit_pos": tot[1], "ctrl_flags": tot[2], "ctrl_pos": tot[3],
                     "capit_minus_ctrl_pp": d, "ci95": ci, "events_capit": len(a_cap), "events_ctrl": len(b_cap),
                     "events_capit_only": len(a_cap - b_cap), "events_ctrl_only": len(b_cap - a_cap)}
        units[name] = dict(u)
    return out, units


def protocol_ok():
    try:
        return hashlib.sha256(open(PROTOCOL, "rb").read()).hexdigest() == PROTOCOL_SHA256
    except OSError:
        return False


def main(mode):
    if mode == "dev":
        res = {"mode": "dev", "development": run_window("development")[0]}
    else:
        if not protocol_ok():
            print("⛔ DISC_PROTOCOL.md differs from the sealed version — nothing scored")
            sys.exit(9)
        (va, uva), (ho, uho) = run_window("validation"), run_window("holdout")
        pooled = {}
        for name in PAIRED_CONTROLS:
            u = {f"V|{k}": v for k, v in uva[name].items()}
            u.update({f"H|{k}": v for k, v in uho[name].items()})
            d, ci = K.cluster_diff(u, REPS, SEED, 0.05)
            pooled[name] = {"capit_minus_ctrl_pp": d, "ci95": ci}
        res = {"mode": "final", "protocol_sha256": PROTOCOL_SHA256, "validation": va, "holdout": ho,
               "capit_pooled": pooled}
    json.dump(res, open(os.path.join(DATA, f"cand_{mode}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return res


def _show(w):
    print(w["window"], "rows", w["rows"], "eval", w["evaluable"], "base", w["base_rate"], "events", w["eligible_events"],
          "v1x identity", w["v1x_identity_rows"], w["v1x_identity_max_rel_diff"], "vmax3 missing", w["vmax3_missing"])
    for n, v in w["rules"].items():
        print(f'{n:12s} f/s {v["flags_per_session"]:7} prec {v["precision"]} lift {v["lift"]} {v["lift_ci"]} '
              f'rec {v["events_captured"]}/{v["events_eligible"]} matched {v["matched"]["ratio"]} {v["matched"]["ci"]} '
              f'VOL {v["VOL_k"]["rule_minus_pp"]} {v["VOL_k"]["rule_minus_pp_ci"]} '
              f'VOLAT {v["VOLAT_k"]["rule_minus_pp"]} {v["VOLAT_k"]["rule_minus_pp_ci"]} '
              f'MOM {v["MOM_k"]["rule_minus_pp"]} {v["MOM_k"]["rule_minus_pp_ci"]} '
              f'DROP {v["DROP_k"]["rule_minus_pp"]} {v["DROP_k"]["rule_minus_pp_ci"]} '
              f'LOWRSI {v["LOWRSI_k"]["rule_minus_pp"]} {v["LOWRSI_k"]["rule_minus_pp_ci"]}')
        if "beyond_REF_UNION" in v:
            bu = v["beyond_REF_UNION"]
            print("     +union events", bu["events_added"], "extra prec", bu["extra_precision"], bu["extra_precision_ci95"],
                  "free base", bu["free_base"], "extra f/s", bu["extra_flags_per_session"])
            for h in v.get("halves", []):
                print("     half", h["period"], "prec", h["precision"], "lift", h["lift"], h["lift_ci"],
                      "rec", h["events_captured"], "/", h["events_eligible"])
    for n, v in w["capit_paired"].items():
        print("  CAPIT_TC vs", n, v)


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else ""
    if m not in ("dev", "final"):
        sys.exit("usage: rn_disc_cand.py dev|final")
    r = main(m)
    for w in ("development", "validation", "holdout"):
        if w in r:
            _show(r[w])
    if "capit_pooled" in r:
        print("pooled", r["capit_pooled"])
