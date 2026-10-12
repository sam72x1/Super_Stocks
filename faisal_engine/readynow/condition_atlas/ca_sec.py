"""Faisal condition atlas — the share-count and offering conditions on the only point-in-time source available:
the SEC snapshot of 238 symbols chosen on 2026-10-08 (`fm_forensics/data/sec_2026-10-08.json.gz`). DESCRIPTIVE ONLY:
the subset was selected after the fact by the bot's lists (survivorship and outcome-related selection are likely),
so nothing here is a population estimate. Development window only (2025-05-01 → 12-31).

  SH2M    shares outstanding < 2,000,000 at T («عدد اسهمه تحت 2 مليون», IMG_0151): the latest reported value filed on or
          before T, scaled by every split dated after the value's period end and on or before T
  SH5M    the same < 5,000,000 (the app's float limit)
  OFFER30 a final prospectus (424B1 / 424B4 / 424B5) filed in the 30 calendar days before T («اعلان طرح», IMG_0497)
  REG90   a registration (S-1 / S-3 / F-1 / F-3) filed in the 90 calendar days before T
Run from the repo root:  python3 faisal_engine/readynow/condition_atlas/ca_sec.py   → data/sec_dev.json
"""
import datetime as dt
import gzip
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ca_lib as L                                                        # noqa: E402

K, D = L.K, L.D
ROOT = os.path.dirname(os.path.dirname(L.RN))
SEC = os.path.join(ROOT, "fm_forensics", "data", "sec_2026-10-08.json.gz")
PROSP = ("424B1", "424B4", "424B5")
REGS = ("S-1", "S-3", "F-1", "F-3")


def _d(x):
    return dt.date.fromisoformat(x[:10])


def prepare():
    sec = json.load(gzip.open(SEC, "rt", encoding="utf-8"))["symbols"]
    sp = json.load(open(os.path.join(ROOT, "faisal_engine", "data", "rank", "splits.json"), encoding="utf-8"))["splits"]
    out = {}
    for sym, v in sec.items():
        if v.get("status") != "ok":
            continue
        sh = sorted(((x["filed"], x["end"], float(x["val"])) for x in (v.get("shares_outstanding") or [])
                     if x.get("filed") and x.get("val")), key=lambda t: t[0])
        fl = [(f.get("form"), f.get("filingDate")) for f in (v.get("filings") or []) if f.get("filingDate")]
        out[sym] = {"shares": sh, "prosp": sorted(d for f, d in fl if f in PROSP),
                    "regs": sorted(d for f, d in fl if f in REGS),
                    "splits": sorted((d, float(r)) for d, r in (sp.get(sym) or []) if r)}
    return out


def at(s, t):
    T = _d(t)
    sh = [x for x in s["shares"] if _d(x[0]) <= T]
    shares = None
    if sh:
        filed, end, val = sh[-1]
        f = 1.0
        for d, r in s["splits"]:
            if _d(end) < _d(d) <= T:
                f *= r
        shares = val * f
    off = any(0 <= (T - _d(d)).days <= 30 for d in s["prosp"])
    reg = any(0 <= (T - _d(d)).days <= 90 for d in s["regs"])
    return shares, off, reg


def main():
    rows, _by, _m = L.load("development")
    sec = prepare()
    er = [r for r in rows if r["lab"] in K.EVAL and r["sym"] in sec]
    flags = {"SH2M": lambda x: x[0] is not None and x[0] < 2e6, "SH5M": lambda x: x[0] is not None and x[0] < 5e6,
             "OFFER30": lambda x: x[1], "REG90": lambda x: x[2]}
    vals = {(r["sym"], r["t"]): at(sec[r["sym"]], r["t"]) for r in er}
    out = {"note": "descriptive; 238 symbols selected on 2026-10-08 (biased subset)",
           "rows_covered": len(er), "symbols_covered": len({r["sym"] for r in er}),
           "pos_covered": sum(r["lab"] == "POS710" for r in er),
           "rows_with_share_count": sum(1 for v in vals.values() if v[0] is not None),
           "base": round(sum(r["lab"] == "POS710" for r in er) / len(er), 4) if er else None, "flags": {}}
    for name, f in flags.items():
        u = defaultdict(lambda: [0, 0, 0, 0])
        for r in er:
            x = u[r["sym"]]
            x[2] += 1
            x[3] += r["lab"] == "POS710"
            if f(vals[(r["sym"], r["t"])]):
                x[0] += 1
                x[1] += r["lab"] == "POS710"
        lift, ci = K.cluster_ratio(u, 2000, 20261011, 0.05)
        pos = [r for r in er if r["lab"] == "POS710"]
        neg = [r for r in er if r["lab"] == "NEG"]
        out["flags"][name] = {"flagged": sum(v[0] for v in u.values()), "pos_flagged": sum(v[1] for v in u.values()),
                              "prev_pos": round(sum(1 for r in pos if f(vals[(r["sym"], r["t"])])) / len(pos), 4)
                              if pos else None,
                              "prev_neg": round(sum(1 for r in neg if f(vals[(r["sym"], r["t"])])) / len(neg), 4)
                              if neg else None, "lift": lift, "lift_ci": ci}
    json.dump(out, open(os.path.join(L.DATA, "sec_dev.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=1))
