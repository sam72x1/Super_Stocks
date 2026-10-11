"""ALERTS70 — link the historical live alerts to the bot's +70% events (research · offline · read-only).

Reuses, by import and without modification, the sealed R70 code (faisal_engine/ready70/r70_build.py):
the archived bars, the recomputed explosion detector (episodes), and the forward/strict labels.

Inputs (all local): data/liq_alerts.csv.gz + data/entry_alerts.csv.gz + data/oe_days.json (a70_extract.py),
tier_fwd_ledger.jsonl (delivered M5 cards), ignition_log.json (delivered ignition fires).
Outputs (data/):
  alerts.csv.gz   one row per liquidity anchor (first alert of the liquidity card flow) with its link to the
                  nearest tool episode and the alert-time fields it carried
  obs.csv.gz      one row per (symbol, session) the live scanner actually observed (a LIQ: state key that day),
                  with alerted flag, daily-visible momentum (ret1, volx, px) and the R70 labels
  events.csv.gz   eligible +70% episodes (tool definition) on observed symbols, with the earliest alert class
  side.csv.gz     «هنا الدخول» stamps and ignition fires linked the same way (descriptive)
Run from the repo root:  python3 faisal_engine/alerts70/a70_build.py   (--check verifies the outputs)
"""
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(HERE, "data")
sys.path.insert(0, os.path.join(ROOT, "faisal_engine", "ready70"))
os.environ["FAISAL_ONLY"] = "1"
import numpy as np                                                        # noqa: E402
import r70_build as R                                                     # noqa: E402  (sealed R70 code, read-only)

H = 10
WIN_FROM, WIN_TO = "2026-08-17", "2026-09-29"     # live liquidity alerts existed (Polygon refused from 09-29 15:15 UTC)
ET = dt.timezone(dt.timedelta(hours=-4))           # EDT for the whole window


def _rd(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load_alerts():
    """Union of liquidity anchors: local state snapshots (M1 stamped after a successful send) and the delivered M5
    cards of tier_fwd_ledger.jsonl (an M5 card implies its M1). Key = (symbol, NY date, anchor_ms)."""
    out = {}
    for a in _rd(os.path.join(DATA, "liq_alerts.csv.gz")):
        k = (a["symbol"], a["date"], int(a["anchor_ms"]))
        out[k] = {"symbol": a["symbol"], "date": a["date"], "anchor_ms": int(a["anchor_ms"]), "src": "state",
                  "anchor_price": _f(a.get("anchor_price")), "vol_x": _f(a.get("vol_x")),
                  "usd": _f(a.get("peak_usd")), "trig": a.get("trig") or "", "rearm_n": a.get("rearm_n") or "",
                  "t_M1": a.get("t_M1") or "", "pre_hi": _f(a.get("pre_hi")), "anchor_open": _f(a.get("anchor_open"))}
    for ln in open(os.path.join(ROOT, "tier_fwd_ledger.jsonl"), encoding="utf-8"):
        if not ln.strip():
            continue
        t = json.loads(ln)
        k = (t["symbol"], t["date"], int(t["anchor_ms"]))
        row = out.get(k)
        if row is None:
            row = {"symbol": t["symbol"], "date": t["date"], "anchor_ms": int(t["anchor_ms"]), "src": "tier",
                   "anchor_price": _f(t.get("anchor_price")), "vol_x": _f(t.get("vol_x")), "usd": _f(t.get("usd")),
                   "trig": "", "rearm_n": "", "t_M1": "", "pre_hi": None, "anchor_open": None}
            out[k] = row
        else:
            row["src"] = "both"
        row["tier"] = t.get("tier")
        row["prev_close_ledger"] = _f(t.get("prev_close"))
        if row.get("anchor_price") is None:
            row["anchor_price"] = _f(t.get("anchor_price"))
    return [out[k] for k in sorted(out, key=lambda k: (k[2], k[0]))]


def classify(eps, a, p_adj, n_bars):
    """Where an alert on session index `a` (alert price p_adj, split-adjusted) sits relative to the symbol's episodes.
    The nearest episode still unfinished at the alert (peak >= a) whose launch is within H sessions after it."""
    cand = [e for e in eps if e["P_i"] >= a and e["L_i"] <= a + H]
    if not cand:
        return ("CENSORED" if a + H > n_bars - 1 else "NO_EVENT_WITHIN_H"), None, {}
    e = min(cand, key=lambda x: x["L_i"])
    if e.get("quality", "OK") != "OK":
        return "UNKNOWN_SPLIT", e, {}
    trough = e["trough_close"]
    lvl70 = trough * 1.70
    info = {"to_launch": e["L_i"] - a, "to_d1": e["D1_i"] - a,
            "gain_at_alert": round((p_adj / trough - 1.0) * 100.0, 1) if (p_adj and trough > 0) else None}
    if a < e["L_i"]:
        cls = "BEFORE_START"
    elif a == e["L_i"]:
        cls = "START_DAY" if (p_adj is None or p_adj < lvl70) else "AT_OR_AFTER_70"
    elif a <= e["D1_i"]:
        cls = "UNDERWAY_PRE70" if (p_adj is None or p_adj < lvl70) else "AT_OR_AFTER_70"
    else:
        cls = "AFTER_70"
    return cls, e, info


def episodes_with_trough(sym, b, splits):
    eps = R.split_flags(R.episodes_for(sym, b), splits)
    for e in eps:
        e["trough_close"] = float(b["c"][max(e["L_i"] - 1, 0)])
    return eps


def daily_fields(b, i):
    c, v = b["c"], b["v"]
    ret1 = round((c[i] / c[i - 1] - 1.0) * 100.0, 2) if i >= 1 and c[i - 1] > 0 else None
    med = float(np.median(v[max(0, i - 20):i])) if i >= 5 else None
    volx = round(float(v[i]) / med, 2) if med and med > 0 else None
    px = round(float(c[i] * b["fac"][i]), 4)
    return ret1, volx, px


def _wcsv(path, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k) for k in fields})
    with gzip.GzipFile(path, "wb", mtime=0) as f:
        f.write(buf.getvalue().encode("utf-8"))


def build(out_dir=DATA):
    meta, bars = R.load_bars()
    splits = json.load(open(R.SPLITS_FILE, encoding="utf-8"))["splits"]
    days = json.load(open(os.path.join(DATA, "oe_days.json"), encoding="utf-8"))["days"]
    alerts = load_alerts()
    need = {a["symbol"] for a in alerts}
    for d, v in days.items():
        if WIN_FROM <= d <= WIN_TO:
            need |= set(v.get("evaluated_symbols") or [])
    eps, ready = {}, set()
    for sym in sorted(need):
        b = bars.get(sym)
        if b is None:
            continue
        b["fac"] = R.split_factor_after(splits.get(sym, []), b["d"])
        eps[sym] = episodes_with_trough(sym, b, splits)
        ready.add(sym)
    # ── alerts ──
    arows = []
    for a in alerts:
        sym, d = a["symbol"], a["date"]
        b = bars.get(sym)
        row = dict(a)
        _et = dt.datetime.fromtimestamp(a["anchor_ms"] / 1000, ET)
        row["anchor_et"] = _et.strftime("%H:%M")
        # decision session = the first regular close after the alert: after 16:00 ET it is the next session
        row["shift"] = int(_et.hour >= 16)
        if b is None or d not in b["ix"] or b["ix"][d] + row["shift"] > len(b["c"]) - 1:
            row["link"] = "NO_BARS"
            arows.append(row)
            continue
        i = b["ix"][d] + row["shift"]
        row["decision_t"] = b["d"][i]
        i0 = b["ix"][d]                       # the alert's own NY date (the price was traded then)
        fac = float(b["fac"][i0])
        p_adj = (a["anchor_price"] / fac) if a.get("anchor_price") else None
        pc_adj = float(b["c"][i0 - 1] if not row["shift"] else b["c"][i0]) if i0 >= 1 else None
        row["move_at_alert"] = round((p_adj / pc_adj - 1.0) * 100.0, 1) if (p_adj and pc_adj) else None
        cls, e, info = classify(eps[sym], i, p_adj, len(b["c"]))
        row["link"] = cls
        row.update(info)
        if e is not None:
            row["event"] = f'{sym}|{e["launch"]}'
            row["event_d1"] = e["d1"]
            row["event_peak_gain"] = e["peak_gain"]
        fl, fk, fg = R.label_fwd(b, eps[sym], splits.get(sym, []), i, H)
        row["f10"], row["f10_k"], row["f10_gain"] = fl, fk, fg
        mx = [float(b["c"][j]) for j in range(i, min(len(b["c"]), i + H + 1))]
        row["alert70_close"] = int(bool(p_adj and mx and max(mx) >= 1.70 * p_adj)) if i + H <= len(b["c"]) - 1 else ""
        arows.append(row)
    # ── observed symbol-days ──
    alerted = {}
    for a in arows:
        if a.get("decision_t"):
            alerted.setdefault((a["symbol"], a["decision_t"]), []).append(a)
    observed = {}
    for d, v in sorted(days.items()):
        if WIN_FROM <= d <= WIN_TO:
            for sym in v.get("evaluated_symbols") or []:
                observed[(sym, d)] = {"final": int(bool(v.get("final_local"))), "src": "liq_key"}
    for (sym, d), al in alerted.items():          # an alert proves observation even when its session shifted
        if (sym, d) not in observed:
            fin = int(bool((days.get(d) or {}).get("final_local")))
            observed[(sym, d)] = {"final": fin, "src": "alert"}
    orows = []
    for (sym, d), ov in sorted(observed.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        row = {"t": d, "sym": sym, "final_snapshot_local": ov["final"], "obs_src": ov["src"]}
        al = alerted.get((sym, d), [])
        row["alerted"] = int(bool(al))
        row["n_anchors"] = len(al)
        b = bars.get(sym)
        if b is None or d not in b["ix"]:
            row["bars"] = "MISSING"
            orows.append(row)
            continue
        i = b["ix"][d]
        row["bars"] = "OK"
        row["ret1"], row["volx"], row["px"] = daily_fields(b, i)
        fl, fk, fg = R.label_fwd(b, eps[sym], splits.get(sym, []), i, H)
        row["f10"], row["f10_k"], row["f10_gain"] = fl, fk, fg
        ys, ye = R.label(eps[sym], i, len(b["c"]), H)
        if ys == "POS" and ye.get("quality") != "OK":
            ys = "UNKNOWN_SPLIT"
        row["y10"] = ys
        if al:
            first = min(al, key=lambda x: x["anchor_ms"])
            row["first_alert_et"] = first.get("anchor_et")
            row["first_link"] = first.get("link")
            row["move_at_alert"] = first.get("move_at_alert")
        orows.append(row)
    # ── eligible events: tool episodes with D1 in the window, on symbols the scanner observed in [L-10, D1] ──
    obs_days = {}
    for d, v in days.items():
        for s in v.get("evaluated_symbols") or []:
            obs_days.setdefault(s, set()).add(d)
    erows = []
    for sym in sorted(ready):
        b = bars[sym]
        for e in eps[sym]:
            if not (WIN_FROM < e["d1"] <= WIN_TO):
                continue
            lo = b["d"][max(0, e["L_i"] - H)]
            seen_days = sorted(x for x in obs_days.get(sym, ()) if lo <= x <= e["d1"])
            row = {"sym": sym, "launch": e["launch"], "d1": e["d1"], "kind_d1": e["kind_d1"], "gain_d1": e["gain_d1"],
                   "peak_gain": e["peak_gain"], "quality": e.get("quality"), "observed_days": len(seen_days),
                   "first_observed": seen_days[0] if seen_days else ""}
            al = [a for a in arows if a["symbol"] == sym and a.get("event") == f'{sym}|{e["launch"]}']
            row["alerts_linked"] = len(al)
            if al:
                first = min(al, key=lambda x: x["anchor_ms"])
                row["first_alert_date"] = first["date"]
                row["first_alert_et"] = first.get("anchor_et")
                row["first_alert_class"] = first.get("link")
                row["first_alert_to_launch"] = first.get("to_launch")
                row["first_alert_to_d1"] = first.get("to_d1")
                row["first_alert_gain_at_alert"] = first.get("gain_at_alert")
            erows.append(row)
    # ── side streams (descriptive): «هنا الدخول» stamps and ignition fires ──
    srows = []
    for e_ in _rd(os.path.join(DATA, "entry_alerts.csv.gz")):
        srows.append({"stream": "operator_entry", "symbol": e_["symbol"], "date": e_["date"], "time": e_["first_commit"],
                      "price": None})
    for g in json.load(open(os.path.join(ROOT, "ignition_log.json"), encoding="utf-8")):
        srows.append({"stream": "ignition", "symbol": g["symbol"], "date": g["date"],
                      "time": g.get("fired_at") or "", "price": g.get("price")})
    for r in srows:
        b = bars.get(r["symbol"])
        if b is None or r["date"] not in b["ix"]:
            r["link"] = "NO_BARS"
            continue
        if r["symbol"] not in eps:
            b["fac"] = R.split_factor_after(splits.get(r["symbol"], []), b["d"])
            eps[r["symbol"]] = episodes_with_trough(r["symbol"], b, splits)
        i0 = b["ix"][r["date"]]
        sh = 0
        if r.get("time"):
            try:
                sh = int(dt.datetime.fromisoformat(r["time"].replace("Z", "+00:00")).astimezone(ET).hour >= 16)
            except ValueError:
                sh = 0
        i = min(i0 + sh, len(b["c"]) - 1)
        p_adj = (float(r["price"]) / float(b["fac"][i0])) if r.get("price") else None
        cls, e, info = classify(eps[r["symbol"]], i, p_adj, len(b["c"]))
        r["link"] = cls
        r.update(info)
        r["event"] = f'{r["symbol"]}|{e["launch"]}' if e is not None else ""
    os.makedirs(out_dir, exist_ok=True)
    _wcsv(os.path.join(out_dir, "alerts.csv.gz"), arows,
          ["symbol", "date", "anchor_ms", "anchor_et", "src", "anchor_price", "move_at_alert", "vol_x", "usd", "tier",
           "trig", "rearm_n", "pre_hi", "anchor_open", "prev_close_ledger", "t_M1", "shift", "decision_t", "link",
           "to_launch", "to_d1",
           "gain_at_alert", "event", "event_d1", "event_peak_gain", "f10", "f10_k", "f10_gain", "alert70_close"])
    _wcsv(os.path.join(out_dir, "obs.csv.gz"), orows,
          ["t", "sym", "final_snapshot_local", "obs_src", "alerted", "n_anchors", "bars", "ret1", "volx", "px", "f10",
           "f10_k",
           "f10_gain", "y10", "first_alert_et", "first_link", "move_at_alert"])
    _wcsv(os.path.join(out_dir, "events.csv.gz"), erows,
          ["sym", "launch", "d1", "kind_d1", "gain_d1", "peak_gain", "quality", "observed_days", "first_observed",
           "alerts_linked", "first_alert_date", "first_alert_et", "first_alert_class", "first_alert_to_launch",
           "first_alert_to_d1", "first_alert_gain_at_alert"])
    _wcsv(os.path.join(out_dir, "side.csv.gz"), srows,
          ["stream", "symbol", "date", "time", "price", "link", "to_launch", "to_d1", "gain_at_alert", "event"])
    return len(arows), len(orows), len(erows), len(srows)


def _digest(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


if __name__ == "__main__":
    if "--check" in sys.argv:
        import tempfile
        tmp = tempfile.mkdtemp()
        build(tmp)
        bad = [f for f in ("alerts.csv.gz", "obs.csv.gz", "events.csv.gz", "side.csv.gz")
               if _digest(os.path.join(tmp, f)) != _digest(os.path.join(DATA, f))]
        print("❌ differs: " + ", ".join(bad) if bad else "✅ regenerated identically")
        sys.exit(1 if bad else 0)
    print(build())
