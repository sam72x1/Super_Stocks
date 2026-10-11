"""READYNOW reconciliation guards — run from the repo root:
    python3 faisal_engine/readynow/recon/test_recon.py        (exit 0 = pass · R70_FAST=1 skips the 10-minute ROOM rerun)

RC1  the detection-anchored label (rn_recon.label_d1): IN_EVENT · CENSORED without MAXGAP · UNKNOWN_SPLIT · POS710 ·
     NEG · run_started, on a synthetic episode
RC2  rn_recon.py regenerates recon.json and seed_dates.csv.gz byte-identically
RC3  the fresh build reproduces READYNOW's sealed numbers: eligible events 513 · 333 · 208 under L (RN_REPORT §4),
     last label-known decision 2026-08-27 under L and 2026-09-24 under D1
RC4  the fresh build: every date of the five seed events is outside READYNOW's evaluated sample with the symbol
     exclusion named; DKI has two daily-close episodes and no detection on 2026-10-06 … 10-08
RC5  the three discovery scripts read the development window only
RC6  ROOM and GAPS at session i depend on bars ≤ i only (bars after i perturbed ×3 on a real symbol)
RC7  gap_dev.json and anchor_dev.json (and room_dev.json unless R70_FAST=1) regenerate identically
"""
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RN = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(RN))
sys.path.insert(0, HERE)
sys.path.insert(0, RN)
os.environ["FAISAL_ONLY"] = "1"
import rn_lib as K                                                        # noqa: E402
import rn_recon as RC                                                     # noqa: E402

FAILS = []
FRESH = {}


def check(name, ok, info=""):
    print(("✅ " if ok else "❌ ") + name + (f" — {info}" if info else ""))
    if not ok:
        FAILS.append(name)


def rc1():
    try:
        e = {"L": 20, "D1": 25, "P": 27, "quality": "OK"}
        early = {"L": 12, "D1": 25, "P": 27, "quality": "OK"}
        sp = {"L": 60, "D1": 62, "P": 63, "quality": "SPLIT_NEAR"}
        f = RC.label_d1
        ok = (f([e], 15, 100)[0] == "POS710" and f([e], 15, 100)[2] == 0 and f([e], 18, 100)[0] == "POS710"
              and f([e], 14, 100)[0] == "NEG" and f([e], 19, 100)[0] == "NEG" and f([e], 21, 100)[0] == "NEG"
              and f([early], 15, 100)[2] == 1 and f([e], 25, 100)[0] == "IN_EVENT" and f([e], 27, 100)[0] == "IN_EVENT"
              and f([e], 91, 100)[0] == "CENSORED" and f([e], 90, 100)[0] == "NEG" and f([e], 85, 100)[0] == "NEG"
              and f([sp], 55, 100)[0] == "UNKNOWN_SPLIT"
              and f([{"L": 40, "x70": 42, "D1": 50, "P": 43, "quality": "OK"}], 43, 100)[0] == "IN_EVENT"
              and f([{"L": 40, "x70": None, "D1": 50, "P": 52, "quality": "OK"}], 43, 100)[0] == "POS710")
        info = ""
    except Exception as ex:                                               # noqa: BLE001
        ok, info = False, f"⛔ {type(ex).__name__}: {ex}"
    check("RC1 detection-anchored label (IN_EVENT from min(x70, D1) · CENSORED at t+10 only · split · POS710 · NEG · "
          "run_started)", ok, info)


def rc2():
    tmp = tempfile.mkdtemp()
    try:
        RC.build(tmp)
        FRESH["recon"] = json.load(open(os.path.join(tmp, "recon.json"), encoding="utf-8"))
        FRESH["dates"] = K.rd("seed_dates.csv.gz", tmp)
        same = all(open(os.path.join(tmp, f), "rb").read() == open(os.path.join(RC.OUT, f), "rb").read()
                   for f in ("recon.json", "seed_dates.csv.gz"))
        ok, info = same, ""
    except Exception as ex:                                               # noqa: BLE001
        ok, info = False, f"⛔ {type(ex).__name__}: {ex}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check("RC2 rn_recon.py regenerates its outputs identically", ok, info)


def rc3():
    try:
        r = FRESH["recon"]
        a = r["all_clean_episodes"]
        el = [a[f"L:{w}"]["eligible_under_L_label"] for w in ("development", "validation", "holdout")]
        lim = r["label_limits"]
        inv = json.load(open(os.path.join(K.DATA, "inventory.json"), encoding="utf-8"))
        d1k = next(v for k, v in lim.items() if k.startswith("detection_anchored"))
        ok = (el == [513, 333, 208] and lim["readynow_L_anchored_last_known"] == "2026-08-27"
              == inv["label_known_last_decision"] and d1k == "2026-09-24" and lim["max_L_to_D1_clean"] == lim["MAXGAP"])
        info = f"eligible {el} · L {lim['readynow_L_anchored_last_known']} · D1 {d1k}"
    except Exception as ex:                                               # noqa: BLE001
        ok, info = False, f"⛔ {type(ex).__name__}: {ex}"
    check("RC3 reproduces READYNOW's sealed eligible counts and both label limits", ok, info)


def rc4():
    try:
        foc = [d for d in FRESH["dates"] if d.get("t") and (d["sym"], d["episode"].split("|")[1]) in RC.FOCUS]
        dki = FRESH["recon"]["dki_2026_10_07"]
        ok = (len(foc) == 5 * 4 * 4 and all(d["rn_evaluated"] == "0" and "EXCLUDED_SYMBOL" in d["rn_not_evaluated_because"]
                                            for d in foc)
              and len(dki["episodes"]) == 2 and all(v is None for v in dki["detector_asof"].values())
              and dki["close_to_close_10_07_pct"] < 50)
        info = f"focus dates {len(foc)} · DKI episodes {len(dki['episodes'])}"
    except Exception as ex:                                               # noqa: BLE001
        ok, info = False, f"⛔ {type(ex).__name__}: {ex}"
    check("RC4 seed dates excluded by symbol (named) · DKI: two episodes, no detection 10-06 … 10-08", ok, info)


def rc5():
    try:
        import rn_anchor_dev as AD
        import rn_gap_dev as GD
        import rn_room_dev as RM
        dev = K.WINDOWS["development"]
        srcs = [open(os.path.join(HERE, f), encoding="utf-8").read() for f in
                ("rn_room_dev.py", "rn_gap_dev.py", "rn_anchor_dev.py")]
        ok = (RM.DEV == GD.DEV == AD.DEV == dev and all("assert all(r[\"t\"] <= DEV[1]" in s for s in srcs)
              and not any('"validation"' in s or '"holdout"' in s for s in srcs))
        info = f"DEV {RM.DEV}"
    except Exception as ex:                                               # noqa: BLE001
        ok, info = False, f"⛔ {type(ex).__name__}: {ex}"
    check("RC5 the discovery scripts read the development window only", ok, info)


def _cut(b, i):
    return {k: (v[: i + 1] if k in ("o", "h", "l", "c", "v", "d") else v) for k, v in b.items()}


def rc6():
    try:
        import numpy as np
        import pandas as pd
        import rn_gap_dev as GD
        import rn_room_dev as RM
        S = RM.R.S()
        # synthetic: flat bars with one high 2 sessions before t — not yet a confirmed swing high at t (needs 3 bars
        # after it); bars after t are flat, so any look-ahead turns it into a level 20% above
        n, i = 300, 280
        d = [x.strftime("%Y-%m-%d") for x in pd.bdate_range("2024-01-01", periods=n)]
        h = np.ones(n)
        h[i - 2] = 1.2
        syn = {"d": d, "o": np.ones(n), "h": h, "l": np.ones(n) * 0.99, "c": np.ones(n), "v": np.ones(n) * 1e5}
        ok = RM.room(S, syn, i) is None and RM.room(S, _cut(syn, i), i) is None
        meta, bars = RM.R.load_bars()
        rng = random.Random(20261011)
        n_real = 0
        for sym in ("DLXY", "SXTC", "RETO", "DKI", "HUBC"):
            b = bars[sym]
            for j in rng.sample(range(260, len(b["c"]) - 5), 8):
                r0, g0 = RM.room(S, b, j), GD.gaps(S, b, j)
                bb = dict(b)
                for k in ("o", "h", "l", "c"):
                    a = b[k].copy()
                    a[j + 1:] = a[j + 1:] * 3.0
                    bb[k] = a
                ok &= (RM.room(S, bb, j) == r0 == RM.room(S, _cut(b, j), j)
                       and GD.gaps(S, bb, j) == g0 == GD.gaps(S, _cut(b, j), j))
                n_real += 1
        info = f"synthetic + {n_real} real sessions"
    except Exception as ex:                                               # noqa: BLE001
        ok, info = False, f"⛔ {type(ex).__name__}: {ex}"
    check("RC6 ROOM and GAPS use bars ≤ t only (synthetic look-ahead case · real sessions cut and perturbed)", ok, info)


def regen(script, out):
    p = os.path.join(HERE, "data", out)
    before = open(p, "rb").read()
    r = subprocess.run([sys.executable, os.path.join(HERE, script)], capture_output=True, text=True, cwd=ROOT,
                       env=dict(os.environ, GIT_ALLOW_PROTOCOL="file"))
    after = open(p, "rb").read()
    if after != before:
        open(p, "wb").write(before)
    return r.returncode == 0 and after == before, r.returncode


def rc7():
    res = [regen("rn_gap_dev.py", "gap_dev.json"), regen("rn_anchor_dev.py", "anchor_dev.json")]
    if os.environ.get("R70_FAST") != "1":
        res.append(regen("rn_room_dev.py", "room_dev.json"))
    check("RC7 development outputs regenerate identically" + (" (ROOM skipped: R70_FAST=1)"
                                                              if os.environ.get("R70_FAST") == "1" else ""),
          all(ok for ok, _ in res), f"rc={[rc for _, rc in res]}")


if __name__ == "__main__":
    rc1()
    rc2()
    rc3()
    rc4()
    rc5()
    rc6()
    rc7()
    print(f"\nالفاشل: {len(FAILS)}" + (" — " + ", ".join(FAILS) if FAILS else ""))
    sys.exit(1 if FAILS else 0)
