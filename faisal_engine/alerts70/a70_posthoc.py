"""ALERTS70 — post-hoc descriptives (NOT preregistered, never decisive). Written after the sealed run, from the same
outputs, to disclose two things the sealed design leaves implicit:

  1. after-hours controls — a symbol-day whose only alert came at/after 16:00 ET is "not alerted" at its own close
     (the sealed decision-session rule moves the alert to the next session), so it can sit in the K1 pool and be
     drawn as a K2 control. Count them, and the K1/K2 point and interval with those rows left out.
  2. alert price vs the same session's close (two recorded prices, no intraday path claimed), for alerts that
     belong to their own session (shift 0): how far the close ended from the price at which the card was sent.

Run from the repo root:  python3 faisal_engine/alerts70/a70_posthoc.py   (--check verifies data/post_hoc.json)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import a70_eval as V                                                      # noqa: E402

OUT = os.path.join(V.DATA, "post_hoc.json")


def build():
    obs = [r for r in V.rd("obs.csv.gz") if V.T_FROM <= r["t"] <= V.T_TO]
    alerts = V.rd("alerts.csv.gz")
    ah = {(a["symbol"], a["date"]) for a in alerts if a["shift"] == "1"}
    ev, _k1, _k2, _p = V.k_tests(obs)
    pairs, _un = V.match_controls(ev)
    ctl = [c for _a, c in pairs if (c["sym"], c["t"]) in ah]
    pool = [r for r in ev if r["alerted"] == "0" and (r["sym"], r["t"]) in ah]
    keep = [r for r in ev if not (r["alerted"] == "0" and (r["sym"], r["t"]) in ah)]
    _e, k1x, k2x, _q = V.k_tests(keep)
    ob = {(o["sym"], o["t"]): o for o in obs}
    mv, cl = [], []
    for a in alerts:
        if a["shift"] != "0" or not a["decision_t"] or not a["move_at_alert"]:
            continue
        o = ob.get((a["symbol"], a["decision_t"]))
        if not o or o.get("bars") != "OK" or not o.get("ret1"):
            continue
        m, r = float(a["move_at_alert"]), float(o["ret1"])
        mv.append(m)
        cl.append(((1 + r / 100.0) / (1 + m / 100.0) - 1.0) * 100.0)
    return {
        "label": "post-hoc · descriptive · not preregistered · never decisive",
        "after_hours_controls": {
            "k2_controls_alerted_after_16_same_day": len(ctl),
            "k2_controls_alerted_after_16_same_day_pos": sum(c["f10"] == "POS" for c in ctl),
            "k1_pool_rows_alerted_after_16_same_day": len(pool),
            "k1_pool_rows_alerted_after_16_same_day_pos": sum(r["f10"] == "POS" for r in pool),
            "K1_without_them": k1x, "K2_without_them": k2x},
        "alert_price_vs_session_close": {
            "alerts": len(cl),
            "move_at_alert_q25_med_q75": [V.q(mv, .25), V.q(mv, .5), V.q(mv, .75)],
            "close_vs_alert_pct_q25_med_q75": [round(V.q(cl, .25), 1), round(V.q(cl, .5), 1), round(V.q(cl, .75), 1)],
            "closed_below_alert_price": sum(1 for v in cl if v < 0)}}


def _dump(res, path):
    json.dump(res, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    res = build()
    if "--check" in sys.argv:
        import tempfile
        tmp = os.path.join(tempfile.mkdtemp(), "post_hoc.json")
        _dump(res, tmp)
        same = open(tmp, "rb").read() == open(OUT, "rb").read()
        print("✅ regenerated identically" if same else "❌ differs: post_hoc.json")
        sys.exit(0 if same else 1)
    _dump(res, OUT)
    print(json.dumps(res, ensure_ascii=False, indent=1))
