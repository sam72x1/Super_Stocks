"""READY NOW discovery guards — run from the repo root:
    python3 faisal_engine/readynow/disc/test_disc.py        (exit 0 = pass · DISC_FAST=1 skips the slow regenerations)

DG1  onset_leg: a clean run starts at L; a drift that ends in a jump starts at the jump; ONSET lies in [L, Q];
     close[Q] >= G x close[ONSET-1] and close[ONSET-1] is the lowest close of [ONSET-1, Q-1]; G = 1.70 with x70,
     1.50 without (Q = D1)
DG2  label: IN_EVENT from ONSET to max(P, D1, Q) · POS710 only when ONSET is in [t+7, t+10] · CENSORED at t+29 ·
     UNKNOWN_SPLIT for a split-near onset in [t+1, t+10]
DG3  temporal() at session i depends on bars <= i only (volume, closes and lows after i perturbed on a real symbol)
DG4  v1x_series at i depends on bars <= i only, and equals the pivot-day v1x stored by SEQ70 (relative difference
     below 1e-4 on every development row)
DG5  the discovery scripts read the development window only; both «final» modes refuse unless DISC_PROTOCOL.md
     matches its pinned SHA-256, and the pinned value is the file's hash
DG6  the burst threshold is the production constant VOL_SPIKE_MULT (5) read at call time, and the seeds and HUBC
     are absent from every scored row
DG7  rn_disc_build.py --check regenerates the dataset byte-identically (skipped with DISC_FAST=1)
DG8  cand_dev.json, cand_final.json and model_final.json regenerate identically (skipped with DISC_FAST=1)
DG9  verdict.json is what rn_disc_verdict.py derives from the stored results, and the sealed run's output
     (cand_final_asrun.json) differs from the event-de-duplicated rerun only in event counts and lead times
"""
import hashlib
import inspect
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
import numpy as np                                                        # noqa: E402
import rn_disc_build as DB                                                # noqa: E402
import rn_disc_cand as CA                                                 # noqa: E402
import rn_disc_dev as D                                                   # noqa: E402
import rn_disc_model as M                                                 # noqa: E402
import rn_lib as K                                                        # noqa: E402

FAILS = []
FAST = os.environ.get("DISC_FAST") == "1"


def check(name, ok, info=""):
    print(("✅ " if ok else "❌ ") + name + (f" — {info}" if info else ""))
    if not ok:
        FAILS.append(name)


def dg1():
    try:
        # clean run: trough 1.00 at L-1, slow climb, first close >= 1.70 at Q
        c = np.array([2.0] * 5 + [1.0, 1.10, 1.20, 1.25, 1.71, 1.9])
        on, q, g = DB.onset_leg(c, {"L": 6, "x70": 9, "D1": 9})
        a = (on, q, g) == (6, 9, 1.70)
        # drift then jump: from the trough the close drifts to 1.30 then jumps to 2.40 (Q)
        c2 = np.array([2.0] * 5 + [1.0, 1.10, 1.20, 1.30, 1.25, 2.40])
        on2, q2, _g = DB.onset_leg(c2, {"L": 6, "x70": 10, "D1": 10})
        b = (on2, q2) == (10, 10)
        # jump episode without a +70% close: Q = D1, G = 1.50
        c3 = np.array([2.0] * 5 + [1.0, 1.05, 1.60, 1.40])
        on3, q3, g3 = DB.onset_leg(c3, {"L": 6, "x70": None, "D1": 7})
        cc = (on3, q3, g3) == (7, 7, 1.50)
        # properties on random paths
        rng = random.Random(7)
        prop = True
        for _ in range(300):
            n = 40
            p = [1.0]
            for _k in range(n):
                p.append(max(0.05, p[-1] * (1 + rng.uniform(-0.12, 0.25))))
            cr = np.array(p)
            L = rng.randint(2, 15)
            tc = cr[L - 1]
            x = next((k for k in range(L, n) if cr[k] >= 1.70 * tc), None)
            if x is None:
                continue
            o, qq, gg = DB.onset_leg(cr, {"L": L, "x70": x, "D1": x})
            prop &= L <= o <= qq and cr[qq] >= gg * cr[o - 1] - 1e-12 and cr[o - 1] <= cr[o - 1: qq].min() + 1e-12
        info = ""
        ok = a and b and cc and prop
    except Exception as ex:                                               # noqa: BLE001
        ok, info = False, f"⛔ {type(ex).__name__}: {ex}"
    check("DG1 onset_leg (clean run at L · drift-then-jump at the jump · no-x70 G 1.50 · properties on 300 paths)",
          ok, info)


def dg2():
    try:
        e = {"ON": 20, "P": 24, "D1": 26, "Q": 22, "quality": "OK"}
        sp = {"ON": 60, "P": 62, "D1": 62, "Q": 61, "quality": "SPLIT_NEAR"}
        f = DB.label
        ok = (f([e], 10, 200)[0] == "POS710" and f([e], 13, 200)[0] == "POS710" and f([e], 9, 200)[0] == "NEG"
              and f([e], 14, 200)[0] == "NEG" and f([e], 20, 200)[0] == "IN_EVENT" and f([e], 25, 200)[0] == "IN_EVENT"
              and f([e], 26, 200)[0] == "IN_EVENT" and f([e], 27, 200)[0] == "NEG" and f([e], 19, 200)[0] == "NEG"
              and f([e], 172, 200)[0] == "CENSORED" and f([e], 171, 200)[0] == "NEG"
              and f([sp], 55, 200)[0] == "UNKNOWN_SPLIT" and f([e], 14, 200)[2] == 1 and f([e], 9, 200)[2] == 0)
        info = ""
    except Exception as ex:                                               # noqa: BLE001
        ok, info = False, f"⛔ {type(ex).__name__}: {ex}"
    check("DG2 label (IN_EVENT to max(P, D1, Q) · POS710 at t+7..t+10 only · CENSORED at t+29 · split)", ok, info)


def _bars():
    _meta, bars = DB.R.load_bars()
    return bars


def dg3(bars):
    try:
        sym = "DLXY" if "DLXY" in bars else sorted(bars)[0]
        b = bars[sym]
        n = len(b["c"])
        rng = random.Random(11)
        bad = []
        for i in rng.sample(range(80, n - 5), 25):
            z = DB.B.series(b)
            want = DB.temporal(b, z, i)
            p = {k: (np.array(b[k], dtype=float).copy() if k in ("c", "h", "l", "v", "o") else b[k]) for k in b}
            for k in ("c", "h", "l", "v"):
                p[k][i + 1:] = p[k][i + 1:] * 3.0
            got = DB.temporal(p, DB.B.series(p), i)
            if json.dumps(want, sort_keys=True, default=str) != json.dumps(got, sort_keys=True, default=str):
                bad.append(i)
        ok, info = not bad, f"{sym} · 25 sessions · differing {bad[:5]}"
    except Exception as ex:                                               # noqa: BLE001
        ok, info = False, f"⛔ {type(ex).__name__}: {ex}"
    check("DG3 temporal() reads bars <= i only (future bars ×3)", ok, info)


def dg4(bars):
    try:
        sym = "DLXY" if "DLXY" in bars else sorted(bars)[0]
        v = np.array(bars[sym]["v"], dtype=float)
        full = CA.v1x_series(v)
        bad = []
        for i in range(70, len(v) - 3, 37):
            w = v.copy()
            w[i + 1:] *= 3.0
            a, b_ = full[i], CA.v1x_series(w)[i]
            if not ((np.isnan(a) and np.isnan(b_)) or abs(a - b_) < 1e-12):
                bad.append(i)
        dev = json.load(open(os.path.join(D.DATA, "cand_dev.json"), encoding="utf-8"))["development"]
        rel = dev["v1x_identity_max_rel_diff"]
        # live identity on 40 symbols (recomputed now, not read from the stored result)
        by_sym = {}
        for r in K.rd("rows.csv.gz", D.DATA):
            by_sym.setdefault(r["sym"], []).append(r)
        syms = sorted(s_ for s_ in by_sym if s_ in bars)
        syms = syms[::max(1, len(syms) // 40)][:40]
        live, n = 0.0, 0
        for sym in syms:
            x = CA.v1x_series(bars[sym]["v"])
            for r in by_sym[sym]:
                if K.num(r.get("v1x")) is not None:
                    i = bars[sym]["ix"].get(r["t"])
                    if i is not None and np.isfinite(x[i]):
                        live = max(live, abs(K.num(r["v1x"]) - x[i]) / max(1.0, abs(x[i])))
                        n += 1
        ok = not bad and rel is not None and rel < 1e-4 and dev["v1x_identity_rows"] > 50000 and n > 1000 and live < 1e-4
        info = (f"future-dependent {bad[:3]} · stored identity {dev['v1x_identity_rows']} rows max {rel} · "
                f"live {n} rows max {live:.2e}")
    except Exception as ex:                                               # noqa: BLE001
        ok, info = False, f"⛔ {type(ex).__name__}: {ex}"
    check("DG4 v1x_series is causal and equals SEQ70's v1x", ok, info)


def dg5():
    try:
        src_c = inspect.getsource(CA.main)
        src_m = inspect.getsource(M.main)
        dev_only = (D.WIN == "development" and '"development": run_window("development")' in src_c
                    and 'rows_between("2025-05-01", "2025-09-30"), rows_between("2025-10-01", "2025-12-31")' in src_m
                    and K.WINDOWS["development"] == ("2025-05-01", "2025-12-31"))
        real = hashlib.sha256(open(CA.PROTOCOL, "rb").read()).hexdigest() if os.path.exists(CA.PROTOCOL) else None
        pinned = CA.PROTOCOL_SHA256 == real and M.PROTOCOL_SHA256 == real
        tmp = tempfile.mkdtemp()
        try:
            fake = os.path.join(tmp, "DISC_PROTOCOL.md")
            shutil.copy(CA.PROTOCOL, fake)
            with open(fake, "a", encoding="utf-8") as f:
                f.write("\nedit\n")
            saved = (CA.PROTOCOL, M.PROTOCOL)
            CA.PROTOCOL = M.PROTOCOL = fake
            refuse = not CA.protocol_ok() and not M.protocol_ok()
            CA.PROTOCOL, M.PROTOCOL = saved
            accept = CA.protocol_ok() and M.protocol_ok()
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        ok, info = dev_only and pinned and refuse and accept, f"dev {dev_only} pinned {pinned} refuse {refuse} accept {accept}"
    except Exception as ex:                                               # noqa: BLE001
        ok, info = False, f"⛔ {type(ex).__name__}: {ex}"
    check("DG5 development-only discovery · final modes gated by the pinned protocol hash", ok, info)


def dg6():
    try:
        spike = CA.SPIKE == float(CA.R.S().CONFIG["VOL_SPIKE_MULT"]) == 5.0
        rows, _by = D.load("development")
        ex = sum(1 for r in rows if r["sym"] in K.EXCLUDE)
        dev = json.load(open(os.path.join(D.DATA, "cand_dev.json"), encoding="utf-8"))["development"]
        same = dev["rows"] == len(rows) and dev["spike_mult"] == 5.0
        ok, info = spike and ex == 0 and same, f"spike {CA.SPIKE} · excluded rows present {ex} · rows {len(rows)}"
    except Exception as ex_:                                              # noqa: BLE001
        ok, info = False, f"⛔ {type(ex_).__name__}: {ex_}"
    check("DG6 burst threshold = VOL_SPIKE_MULT · seeds and HUBC absent", ok, info)


def dg7():
    if FAST:
        print("⏭️ DG7 skipped (DISC_FAST=1)")
        return
    p = subprocess.run([sys.executable, os.path.join(HERE, "rn_disc_build.py"), "--check"], cwd=ROOT,
                       capture_output=True, text=True, timeout=3600)
    check("DG7 rn_disc_build.py --check", p.returncode == 0, (p.stdout + p.stderr).strip()[-160:])


def dg8():
    if FAST:
        print("⏭️ DG8 skipped (DISC_FAST=1)")
        return
    ok, info = True, []
    jobs = [("rn_disc_cand.py", "dev", "cand_dev.json"), ("rn_disc_cand.py", "final", "cand_final.json"),
            ("rn_disc_model.py", "final", "model_final.json")]
    for script, mode, name in jobs:
        path = os.path.join(D.DATA, name)
        if not os.path.exists(path):
            ok = False
            info.append(f"{name}: missing")
            continue
        before = open(path, "rb").read()
        try:
            p = subprocess.run([sys.executable, os.path.join(HERE, script), mode], cwd=ROOT,
                               capture_output=True, text=True, timeout=7200)
            after = open(path, "rb").read()
            same = p.returncode == 0 and after == before
        finally:
            open(path, "wb").write(before)
        ok &= same
        info.append(f"{name}: {'same' if same else 'DIFFERS'}")
    check("DG8 cand_dev.json · cand_final.json · model_final.json regenerate identically", ok, " · ".join(info))


EVENT_KEYS = {"events_captured", "events_eligible", "recall", "recall_ci95", "lead_to_onset_q25_med_q75",
              "lead_to_x70_q25_med_q75", "events_added", "events_added_list", "events_capit", "events_ctrl",
              "events_capit_only", "events_ctrl_only", "eligible_events"}


def _row_level_diffs(x, y, path=""):
    if isinstance(x, dict) and isinstance(y, dict):
        out = []
        for k in sorted(set(x) | set(y)):
            if k not in EVENT_KEYS:
                out += _row_level_diffs(x.get(k), y.get(k), path + "/" + k)
        return out
    if isinstance(x, list) and isinstance(y, list) and x and isinstance(x[0], dict):
        return [d for i, (p, q) in enumerate(zip(x, y)) for d in _row_level_diffs(p, q, f"{path}/{i}")]
    return [] if x == y else [path]


def dg9():
    try:
        import rn_disc_verdict as V
        stored = json.load(open(os.path.join(D.DATA, "verdict.json"), encoding="utf-8"))
        saved = V.DATA
        tmp = tempfile.mkdtemp()
        try:
            for f in ("cand_final.json", "model_final.json"):
                shutil.copy(os.path.join(D.DATA, f), tmp)
            V.DATA = tmp
            fresh = V.main()
        finally:
            V.DATA = saved
            shutil.rmtree(tmp, ignore_errors=True)
        same = json.dumps(fresh, sort_keys=True) == json.dumps(stored, sort_keys=True)
        a = json.load(open(os.path.join(D.DATA, "cand_final_asrun.json"), encoding="utf-8"))
        b = json.load(open(os.path.join(D.DATA, "cand_final.json"), encoding="utf-8"))
        diffs = _row_level_diffs(a, b)
        ev_moved = a["holdout"]["eligible_events"] != b["holdout"]["eligible_events"]
        ok = same and not diffs and ev_moved and stored["CAPIT_TC"]["verdict"] == "IMPROVES_ON_TOOL_EQUAL_TO_GENERIC"
        info = f"verdict reproduced {same} · row-level differences {len(diffs)} {diffs[:2]} · event counts moved {ev_moved}"
    except Exception as ex:                                               # noqa: BLE001
        ok, info = False, f"⛔ {type(ex).__name__}: {ex}"
    check("DG9 verdict derived from the stored results · as-run and corrected agree row-level", ok, info)


if __name__ == "__main__":
    dg1()
    dg2()
    bars = _bars()
    dg3(bars)
    dg4(bars)
    dg5()
    dg6()
    dg7()
    dg8()
    dg9()
    print(f"\nالفاشل: {len(FAILS)}" + (" — " + ", ".join(FAILS) if FAILS else ""))
    sys.exit(1 if FAILS else 0)
