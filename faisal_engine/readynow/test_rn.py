"""READYNOW guards — run from the repo root:  python3 faisal_engine/readynow/test_rn.py   (exit 0 = all pass).

G1  conditions read bars at or before the decision session only (every later bar altered → same values)
G2  the development reader returns development rows only, without the seeds or HUBC
G3  windows: each start more than 10 sessions after the previous end; the holdout ends at the label-known limit
G4  labels: POS710 exactly for a clean onset at t+7 … t+10 · IN_EVENT · UNKNOWN_SPLIT · CENSORED (t+10+19) · strict
G5  matching: same session and price bucket, within the caliper, unflagged, no reuse, same tool status when asked;
    equal-burden rankings flag exactly as many rows per session as the rule, the highest scores first
G6  a changed specification is refused (exit 9) before any read; the sealed one is accepted
G7  outputs regenerate byte-identically (rn_build --check · seeds_matrix · dev · dev_round2)  [slow; R70_FAST=1 skips]
G8  the candidate and the tool's part are exactly the sealed definitions (boundaries included)
"""
import copy
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
os.environ["FAISAL_ONLY"] = "1"
import numpy as np                                                        # noqa: E402
import rn_build as B                                                      # noqa: E402
import rn_dev as D                                                        # noqa: E402
import rn_eval as V                                                       # noqa: E402
import rn_lib as K                                                        # noqa: E402

FAILS = []


def check(name, ok, info=""):
    print(("✅ " if ok else "❌ ") + name + (f" — {info}" if info else ""))
    if not ok:
        FAILS.append(name)


def g1():
    try:
        meta, bars = B.R.load_bars()
        splits = json.load(open(B.R.SPLITS_FILE, encoding="utf-8"))["splits"]
        rnd = random.Random(7)
        syms = rnd.sample([s for s in sorted(bars) if len(bars[s]["c"]) > 300], 20)
        bad, n = [], 0
        for sym in syms:
            b = bars[sym]
            sd = sorted(d for d, r_ in (splits.get(sym) or []) if r_ and float(r_) < 1)
            z = B.series(b)
            for i in rnd.sample(range(100, len(b["c"]) - 5), 4):
                n += 1
                d0 = B.conditions(b, z, i, sd)
                nb = {k: (v.copy() if isinstance(v, np.ndarray) else copy.copy(v)) for k, v in b.items()}
                for j in range(i + 1, len(b["c"])):
                    f = rnd.uniform(0.3, 3.0)
                    for k in ("o", "h", "l", "c"):
                        nb[k][j] = b[k][j] * f
                    nb["v"][j] = b["v"][j] * rnd.uniform(0.1, 10)
                if B.conditions(nb, B.series(nb), i, sd) != d0:
                    bad.append((sym, i))
        ok, info = not bad and n == 80, f"{n} rows · bad {bad[:3]}"
    except Exception as e:                                                # noqa: BLE001
        ok, info = False, f"⛔ {type(e).__name__}: {e}"
    check("G1 conditions ignore bars after the decision session", ok, info)


def g2():
    fake = [{"t": d, "sym": s, "cond_ok": "1"} for d in ("2025-04-30", "2025-05-01", "2025-12-31", "2026-01-02",
                                                         "2026-02-02", "2026-07-01") for s in ("AAA", "DLXY", "HUBC")]
    orig = K.rd
    try:
        K.rd = lambda name, folder=K.DATA: [dict(r) for r in fake]
        got = D.load_window("development")
        ok = sorted((r["t"], r["sym"]) for r in got) == [("2025-05-01", "AAA"), ("2025-12-31", "AAA")]
        info = str(sorted((r["t"], r["sym"]) for r in got))
    except Exception as e:                                                # noqa: BLE001
        ok, info = False, f"⛔ {type(e).__name__}: {e}"
    finally:
        K.rd = orig
    check("G2 the development reader returns development rows only (seeds and HUBC removed)", ok, info)


def g3():
    try:
        cal = json.load(open(os.path.join(K.DATA, "calendar.json"), encoding="utf-8"))["sessions"]
        inv = json.load(open(os.path.join(K.DATA, "inventory.json"), encoding="utf-8"))
        ix = {d: k for k, d in enumerate(cal)}
        (d0, d1), (v0, v1), (h0, h1) = (K.WINDOWS[w] for w in ("development", "validation", "holdout"))
        last_dev = max(d for d in cal if d <= d1)
        ok = (ix[v0] - ix[last_dev] > 10 and ix[h0] - ix[v1] > 10 and ix[h1] + B.H_HI + B.MAXGAP <= len(cal) - 1
              and h1 == inv["label_known_last_decision"] and inv["max_launch_to_detection"] <= B.MAXGAP)
        info = (f"dev→val {ix[v0] - ix[last_dev]} · val→hold {ix[h0] - ix[v1]} · hold end {h1} vs label-known "
                f"{inv['label_known_last_decision']} · maxgap {inv['max_launch_to_detection']}")
    except Exception as e:                                                # noqa: BLE001
        ok, info = False, f"⛔ {type(e).__name__}: {e}"
    check("G3 windows separated by the horizon · holdout ends at the label-known limit", ok, info)


def g4():
    try:
        def ep(L, q="OK", x70=True, P=None, D1=None):
            return {"L": L, "L10": L, "IGN": L, "P": P if P is not None else L + 2, "D1": D1 if D1 is not None else L + 3,
                    "quality": q, "x70": (L + 2) if x70 else None}
        last = 200
        res = []
        for off in range(1, 13):
            res.append(B.label([ep(100 + off)], 100, last)[0])
        want = ["NEG"] * 6 + ["POS710"] * 4 + ["NEG"] * 2
        ok = res == want
        ok &= B.label([ep(95)], 96, last)[0] == "IN_EVENT"
        ok &= B.label([ep(105, q="SPLIT_NEAR")], 100, last)[0] == "UNKNOWN_SPLIT"
        ok &= B.label([ep(105)], last - B.H_HI - B.MAXGAP, last)[0] == "NEG"
        ok &= B.label([ep(105)], last - B.H_HI - B.MAXGAP + 1, last)[0] == "CENSORED"
        ok &= B.label([ep(108, x70=False)], 100, last, strict=True)[0] == "NEG"
        ok &= B.label([ep(108, x70=False)], 100, last)[0] == "POS710"
        info = f"{res}"
    except Exception as e:                                                # noqa: BLE001
        ok, info = False, f"⛔ {type(e).__name__}: {e}"
    check("G4 labels: POS710 at t+7…t+10 only · IN_EVENT · UNKNOWN_SPLIT · CENSORED at t+10+19 · strict", ok, info)


def g5():
    try:
        rnd = random.Random(11)
        rows = []
        for t in ("2026-02-02", "2026-02-03"):
            for k in range(400):
                rows.append({"t": t, "sym": f"S{k:03d}", "v1x": str(round(rnd.uniform(0.1, 9), 3)),
                             "range20": str(round(rnd.uniform(10, 300), 1)), "dv20": str(round(rnd.uniform(1e3, 1e6))),
                             "px": str(round(rnd.choice([0.5, 2.0]) * rnd.uniform(0.9, 1.1), 3)),
                             "lab": rnd.choice(["NEG", "NEG", "POS710"]), "rsi": str(round(rnd.uniform(15, 50), 2)),
                             "hold_n": str(rnd.randint(0, 9)), "held": "1", "boom5": "5", "bounce": "20",
                             "f": rnd.choice("01")})
        by = K.annotate(rows)
        flag = lambda r: r["f"] == "1"                                    # noqa: E731
        tc = K.EXISTING["TC_TECH"]
        ok = True
        for exact in (None, tc):
            pairs, un = K.match(by, flag, exact)
            ok &= bool(pairs)
            ok &= all(a["t"] == c["t"] and not flag(c) and K.bucket(a["px"]) == K.bucket(c["px"])
                      and all(abs(a[k] - c[k]) <= K.CALIPER for k in K.MATCH_KEYS)
                      and (exact is None or exact(a) == exact(c)) for a, c in pairs)
            per = {}
            for a, c in pairs:
                per.setdefault(c["t"], []).append(c["sym"])
            ok &= all(len(v) == len(set(v)) for v in per.values())
            ok &= len(pairs) + un == sum(1 for r in rows if flag(r) and r["lab"] in K.EVAL)
        vb = K.burden_match(by, flag, K.BURDEN_SCORES["VOL_k"])
        for t, rs in by.items():
            k = sum(1 for r in rs if flag(r))
            got = [r for r in rs if (r["sym"], t) in vb]
            top = sorted(rs, key=lambda r: -float(r["v1x"]))[:k]
            ok &= len(got) == k and {r["sym"] for r in got} == {r["sym"] for r in top}
        info = f"pairs {len(pairs)} (same tool status) · burden {len(vb)}"
    except Exception as e:                                                # noqa: BLE001
        ok, info = False, f"⛔ {type(e).__name__}: {e}"
    check("G5 matched controls and equal-burden rankings obey the specification", ok, info)


def g6():
    tmp = tempfile.mkdtemp()
    try:
        fake = os.path.join(tmp, "RN_SPEC.md")
        open(fake, "wb").write(open(V.PREREG, "rb").read() + b"\n")
        sealed = V.prereg_ok()
        code = ("import sys; sys.path.insert(0, %r); import rn_eval as V; V.PREREG = %r; V.DATA = %r; "
                "V.rd = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('read before the seal check')); "
                "V.K.rd = V.rd; V.final()" % (HERE, fake, tmp))
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT)
        ok = sealed and r.returncode == 9 and "read before the seal check" not in (r.stdout + r.stderr)
        info = f"sealed {sealed} · rc={r.returncode}"
    except Exception as e:                                                # noqa: BLE001
        ok, info = False, f"⛔ {type(e).__name__}: {e}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    check("G6 changed specification refused (exit 9) before any read · sealed one accepted", ok, info)


def g7():
    if os.environ.get("R70_FAST") == "1":
        print("⏭️ G7 skipped (R70_FAST=1)")
        return
    env = dict(os.environ, GIT_ALLOW_PROTOCOL="file")
    r1 = subprocess.run([sys.executable, os.path.join(HERE, "rn_build.py"), "--check"], capture_output=True,
                        text=True, cwd=ROOT, env=env)
    same = []
    for mode, out in (("seeds", "seeds_matrix.json"), ("dev", "dev.json"), ("dev2", "dev_round2.json")):
        p = os.path.join(K.DATA, out)
        before = open(p, "rb").read()
        r = subprocess.run([sys.executable, os.path.join(HERE, "rn_dev.py"), mode], capture_output=True, text=True,
                           cwd=ROOT, env=env)
        after = open(p, "rb").read()
        if after != before:
            open(p, "wb").write(before)
        same.append(r.returncode == 0 and after == before)
    check("G7 build, seeds and development outputs regenerate identically", r1.returncode == 0 and all(same),
          f"build {r1.returncode} · seeds/dev/dev2 {same}")


def g8():
    try:
        def row(rsi, bounce, hold="6", held="1", boom="10"):
            return {"rsi": str(rsi), "bounce": str(bounce), "hold_n": hold, "held": held, "boom5": boom}
        A, T = K.ROUND2[K.CANDIDATE], K.EXISTING["TC_TECH"]
        ok = (A(row(29.99, 10)) and A(row(29.99, 40)) and not A(row(30.0, 20)) and not A(row(25, 9.99))
              and not A(row(25, 40.01)) and not A(row("", 20)))
        ok &= (T(row(32.99, 0)) and not T(row(33.0, 0)) and not T(row(20, 0, hold="4")) and not T(row(20, 0, held="0"))
               and not T(row(20, 0, boom="50")) and T(row(20, 0, boom="49.9")))
        spec = open(V.PREREG, encoding="utf-8").read()
        ok &= bool(re.search(r"Candidate RN_A: RSI14 below 30 at the close, and the close's bounce from the 25-session "
                             r"low \(max high since the low\s+day\) between 10% and 40%", spec))
        ok &= K.CANDIDATE == "RN_A" and K.ABLATION == "RSI30"
        info = ""
    except Exception as e:                                                # noqa: BLE001
        ok, info = False, f"⛔ {type(e).__name__}: {e}"
    check("G8 the candidate and the tool's part are exactly the sealed definitions", ok, info)


if __name__ == "__main__":
    g1()
    g2()
    g3()
    g4()
    g5()
    g6()
    g7()
    g8()
    print(f"\nالفاشل: {len(FAILS)}" + (" — " + ", ".join(FAILS) if FAILS else ""))
    sys.exit(1 if FAILS else 0)
