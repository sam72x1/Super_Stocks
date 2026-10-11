"""READY NOW discovery — seed technical matrix (descriptive; seeds never enter a statistic).

For every clean episode of DLXY, RETO, DKI and SXTC since 2025-05-01 (HUBC listed separately, never a success), the
sessions 10, 9, 8 and 7 before the corrected onset (start of the final +70% leg), pivot-day or not, with the values
computed from bars ≤ that session and the state of each existing rule. DKI's 2026-10-07 intraday spike is not an
episode (no daily-close detection) and is reported as such.
Run from the repo root:  python3 faisal_engine/readynow/disc/rn_disc_seeds.py   → disc/data/seed_matrix.json
"""
import bisect
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RN = os.path.dirname(HERE)
sys.path.insert(0, RN)
sys.path.insert(0, HERE)
os.environ["FAISAL_ONLY"] = "1"
import rn_build as B                                                      # noqa: E402
import rn_disc_build as DB                                                # noqa: E402
import rn_disc_dev as D                                                   # noqa: E402
import rn_lib as K                                                        # noqa: E402

R = B.R
SHOW = ("pivot", "rsi", "rsi_low", "dist", "bounce", "hold_n", "boom5", "range20", "r5", "v1x", "pos60", "bot_age",
        "pc_stage", "below3", "macd_pos", "split120", "rsi_div", "hl_count", "rise10_vdry", "v_then_up", "first_up")


def main():
    meta, bars = R.load_bars()
    splits = json.load(open(R.SPLITS_FILE, encoding="utf-8"))["splits"]
    rows = K.rd("rows.csv.gz", D.DATA)
    piv = {(r["sym"], r["t"]): r for r in rows}
    by_t = {}
    for r in rows:
        by_t.setdefault(r["t"], []).append(r)
    ev = [e for e in K.rd("events.csv.gz", D.DATA) if e["sym"] in DB.SEEDS + DB.ACTIVE and e["L"] >= "2025-05-01"]
    alerts = json.load(open(os.path.join(D.DATA, "alerts.json"), encoding="utf-8"))
    out = {"episodes": [], "alerts": alerts,
           "dki_2026_10_07": "intraday-only spike (high +167.6%, close +22.8%); no daily-close detection — "
                             "neither a success nor a failure"}
    for e in ev:
        sym = e["sym"]
        b = bars[sym]
        b["fac"] = R.split_factor_after(splits.get(sym, []), b["d"])
        z = B.series(b)
        sd = sorted(d for d, r_ in (splits.get(sym) or []) if r_ and float(r_) < 1)
        k0 = b["ix"][e["onset"]]
        days = []
        for off in (-10, -9, -8, -7):
            i = k0 + off
            d = b["d"][i]
            r = piv.get((sym, d))
            if r is None:                         # not a pivot-day: compute the same values from bars ≤ d
                r = dict(B.conditions(b, z, i, sd) or {})
                r.update(R.features(b, i))
                r.update(DB.temporal(b, z, i))
                r = {k: (None if v is None else str(v)) for k, v in r.items()}
                r["pivot"] = "0"
                r["lab_on"] = "not a pivot-day"
            else:
                r = dict(r, pivot="1")
                sess = [x for x in by_t[d] if x.get("v1x") not in (None, "")]
                vals = sorted(float(x["v1x"]) for x in sess)
                if r.get("v1x") not in (None, ""):
                    x = float(r["v1x"])
                    r["p_v1x"] = (bisect.bisect_left(vals, x) + 0.5 * (bisect.bisect_right(vals, x)
                                                                       - bisect.bisect_left(vals, x))) / len(vals)
            rules = {n: int(bool(f(r))) for n, f in D.REFS.items()}
            days.append({"off": off, "t": d, "label_corrected": r.get("lab_on"),
                         **{k: r.get(k) for k in SHOW}, "rules": rules})
        out["episodes"].append({"sym": sym, "active_not_success": int(sym in DB.ACTIVE),
                                **{k: e[k] for k in ("trough", "L", "onset", "q", "x70", "d1", "ign", "peak", "kind",
                                                     "gain_d1", "peak_gain", "edge_clipped")},
                                "window": days})
    json.dump(out, open(os.path.join(D.DATA, "seed_matrix.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    r = main()
    for e in r["episodes"]:
        print(f'{"(HUBC) " if e["active_not_success"] else ""}{e["sym"]} L {e["L"]} ONSET {e["onset"]} Q {e["q"]} '
              f'D1 {e["d1"]} {e["kind"]} {e["gain_d1"]}%')
        for d in e["window"]:
            print("  ", d["t"], d["label_corrected"], {k: d[k] for k in ("pivot", "rsi", "dist", "bounce", "hold_n", "range20",
                                                                         "r5", "v1x", "pos60", "pc_stage")},
                  "rules", "".join(n[0] + str(v) for n, v in d["rules"].items()))
