"""READYNOW audit — do the READYNOW condition proxies reproduce the app's own condition states?

Definition audit only (no outcome is read): for every app snapshot whose condition chips are visible in the owner's
screenshots, compute the READYNOW proxies (`rn_build.conditions` + READY70 cycle stage) on the local daily bars of that
session and compare each with the state the app displays. The app states are transcribed from the images listed in
SNAPSHOTS (read by eye 2026-10-11; `faisal_batches/2026-10-01/EVIDENCE_REPORT.md` §② / §⑤ for the same readings).
OMH and CIIT carry no date on screen: among sessions 2026-09-18 … 2026-10-02 whose 25-session low and bounce equal the
app's support and bounce (display tolerance), the one whose close-based distance also equals the app's (±0.1 point) is
evaluated; the other candidates are listed.
Run from the repo root:  python3 faisal_engine/readynow/audit/rn_chip_parity.py   → audit/data/chip_parity.json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RN = os.path.dirname(HERE)
sys.path.insert(0, RN)
os.environ["FAISAL_ONLY"] = "1"
import rn_build as B                                                      # noqa: E402

# app state per chip: True = satisfied, False = shown missing, None = not visible on the screenshots
# chips: STAB2 «ثبات يومي جلستين على الأقل» · NEAR15 «ضمن 15% من الدعم» · BOUNCE «الارتداد ضمن 10–40%» ·
#        BELOW «أسفل EMA20/30/50» · RETEST «إعادة اختبار يومي ناجح» · MOMENTUM «الزخم اليومي و4H تحسّن»
SNAPSHOTS = [
    {"tag": "NTCL-25", "sym": "NTCL", "dates": ["2026-09-25"], "img": "TG_57913 · TG_57914",
     "support": 1.735, "bounce": 26.8, "price": 2.12, "score": "76 · 6/8 · short 1/1",
     "app": {"STAB2": False, "NEAR15": False, "BOUNCE": True, "BELOW": True, "RETEST": True, "MOMENTUM": True}},
    {"tag": "NTCL-15", "sym": "NTCL", "dates": ["2026-09-15"], "img": "TG_57921-23 = APP_20260918_18/19/20",
     "support": 1.735, "bounce": 26.8, "price": 2.04, "score": "71 · 6/8 · short 0/1",
     "app": {"STAB2": False, "NEAR15": False, "BOUNCE": True, "BELOW": True, "RETEST": True, "MOMENTUM": True}},
    {"tag": "MSGY", "sym": "MSGY", "dates": ["2026-09-18"], "img": "TG_50592 (= TG_57920)",
     "support": 1.73, "bounce": 30.6, "price": 2.08, "score": "83 · 7/8 · short 0/1",
     "app": {"STAB2": True, "NEAR15": False, "BOUNCE": True, "BELOW": True, "RETEST": True, "MOMENTUM": True}},
    {"tag": "ELPW-05", "sym": "ELPW", "dates": ["2026-09-04"], "img": "TG_57924 = APP_20260918_52",
     "support": 3.01, "bounce": 8.6, "price": 3.085, "score": "59 · 5/8 · short 0/1",
     "app": {"STAB2": False, "NEAR15": True, "BOUNCE": False, "BELOW": True, "RETEST": False, "MOMENTUM": True}},
    {"tag": "ZNB-04", "sym": "ZNB", "dates": ["2026-09-04"], "img": "TG_57925 = APP_20260918_50",
     "support": 1.55, "bounce": 12.9, "price": 1.60, "score": "83 · 7/8 · short 0/1",
     "app": {"STAB2": False, "NEAR15": True, "BOUNCE": True, "BELOW": True, "RETEST": True, "MOMENTUM": True}},
    {"tag": "OMH", "sym": "OMH", "dates": None, "img": "TG_57876",
     "support": 2.05, "bounce": 27.8, "price": 2.35, "score": "64 · 5/8 · short 1/1",
     "app": {"STAB2": False, "NEAR15": True, "BOUNCE": True, "BELOW": False, "RETEST": True, "MOMENTUM": False}},
    {"tag": "CIIT", "sym": "CIIT", "dates": None, "img": "TG_57880 · TG_57882",
     "support": 2.26, "bounce": 32.3, "price": 2.75, "score": "64 · 5/8 · short 1/1",
     "app": {"STAB2": False, "NEAR15": False, "BOUNCE": True, "BELOW": False, "RETEST": True, "MOMENTUM": True}},
    {"tag": "GCTK-25", "sym": "GCTK", "dates": ["2026-09-25"], "img": "TG_57914 (list card only)",
     "support": 1.77, "bounce": None, "price": 1.82, "score": "not visible",
     "app": {"STAB2": None, "NEAR15": True, "BOUNCE": None, "BELOW": True, "RETEST": False, "MOMENTUM": None}},
    {"tag": "LIMN-21", "sym": "LIMN", "dates": ["2026-09-21"], "img": "TG_50585 (Faisal's post 2026-09-22)",
     "support": 3.32, "bounce": 10.7, "price": 3.64, "score": "64 · 3 missing (only the first is named)",
     "app": {"STAB2": None, "NEAR15": True, "BOUNCE": True, "BELOW": False, "RETEST": False, "MOMENTUM": None}},
]
PROXY = {"STAB2": "HOLD2", "NEAR15": "NEAR15", "BOUNCE": "BOUNCE10_40", "BELOW": "BELOW3", "RETEST": "CYCLE3",
         "MOMENTUM": "MACD_POS"}


def proxies(c):
    return {"HOLD2": bool(c["hold_n"] >= 2 and c["held"]), "NEAR15": c["dist"] is not None and c["dist"] <= 15,
            "BOUNCE10_40": c["bounce"] is not None and 10 <= c["bounce"] <= 40, "BELOW3": bool(c["below3"]),
            "CYCLE3": (c.get("pc_stage") or 0) >= 3, "MACD_POS": bool(c["macd_pos"])}


def main():
    meta, bars = B.R.load_bars()
    splits = json.load(open(B.R.SPLITS_FILE, encoding="utf-8"))["splits"]
    out = []
    agree = {k: [0, 0] for k in PROXY}
    for s in SNAPSHOTS:
        b = bars[s["sym"]]
        b["fac"] = B.R.split_factor_after(splits.get(s["sym"], []), b["d"])
        sd = sorted(d for d, r_ in (splits.get(s["sym"]) or []) if r_ and float(r_) < 1)
        z = B.series(b)
        dates, cands = s["dates"], None
        if dates is None:      # undated screenshot: the session whose support, bounce and distance equal the app's
            cands, dates = [], []
            app_dist = (s["price"] / s["support"] - 1) * 100
            for d in b["d"]:
                if not "2026-09-18" <= d <= "2026-10-02":
                    continue
                c = B.conditions(b, z, b["ix"][d], sd)
                if c and abs(c["low25"] - s["support"]) <= 0.005 and abs(c["bounce"] - s["bounce"]) <= 0.05:
                    cands.append(d)
                    if abs(c["dist"] - app_dist) <= 0.1:
                        dates.append(d)
        for d in dates:
            i = b["ix"][d]
            c = B.conditions(b, z, i, sd)
            c.update(B._pi(b, i))
            p = proxies(c)
            cmp = {}
            for chip, proxy in PROXY.items():
                a = s["app"][chip]
                if a is None:
                    continue
                cmp[chip] = {"app": a, "proxy": p[proxy], "agree": a == p[proxy]}
                agree[chip][0] += a == p[proxy]
                agree[chip][1] += 1
            out.append({"tag": s["tag"], "session": d, "img": s["img"], "score": s["score"],
                        "undated_support_bounce_candidates": cands,
                        "app_support": s["support"], "rn_low25": c["low25"], "app_bounce": s["bounce"],
                        "rn_bounce": c["bounce"], "app_dist_from_app_price": round((s["price"] / s["support"] - 1) * 100, 1),
                        "rn_dist_close": c["dist"], "rn_hold_n": c["hold_n"], "rn_pc_stage": c.get("pc_stage"),
                        "compare": cmp})
    res = {"note": "definition audit; the app states are read from the screenshots; undated OMH/CIIT evaluated on "
                   "every session whose support and bounce match",
           "snapshots": out, "agreement_by_chip": {k: f"{v[0]}/{v[1]}" for k, v in agree.items()},
           "proxy_of_chip": PROXY}
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    json.dump(res, open(os.path.join(HERE, "data", "chip_parity.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return res


if __name__ == "__main__":
    r = main()
    for x in r["snapshots"]:
        print(x["tag"], x["session"], "low25", x["rn_low25"], "vs", x["app_support"], "· bounce", x["rn_bounce"], "vs",
              x["app_bounce"], "· dist", x["rn_dist_close"], "(app", x["app_dist_from_app_price"], ") · hold", x["rn_hold_n"],
              "· stage", x["rn_pc_stage"], "·", {k: ("✓" if v["agree"] else f"✗ app={v['app']} rn={v['proxy']}")
                                                 for k, v in x["compare"].items()})
    print(r["agreement_by_chip"])
