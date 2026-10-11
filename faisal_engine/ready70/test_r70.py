"""READY70 guards — run from the repo root:  python3 faisal_engine/ready70/test_r70.py   (exit 0 = all pass).

L1  features(b, i) are unchanged when every bar after i is altered (no look-ahead in any feature)
L2  the forward label is unchanged when bars before the decision are altered (labels read the future only)
L3  FastFrame gives the same pivot_cycle_state / tested_level as the pandas frame over the full history
L4  identity_vec equals Super_stock._had_pivot_identity bar for bar (adjusted prices, 300 sampled bars)
L5  detect_asof equals the live tool Super_stock.scan_explosions on synthetic histories (kind, day, gain)
L6  windows: discovery ends before the embargo, the embargo is at least H sessions, test starts after it,
    and explore() never holds a row past DISC_TO
L7  the test mode refuses to run (exit 9) when the preregistration bytes differ from the sealed hash
L8  outputs on disk regenerate identically (r70_build.py --check)  [slow; skipped with R70_FAST=1]
"""
import copy
import io
import json
import os
import random
import subprocess
import sys
import contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ["FAISAL_ONLY"] = "1"
import numpy as np                                                        # noqa: E402
import pandas as pd                                                       # noqa: E402
import r70_build as R                                                     # noqa: E402
import r70_eval as E                                                      # noqa: E402

FAILS = []


def check(name, ok, info=""):
    print(("✅ " if ok else "❌ ") + name + (f" — {info}" if info else ""))
    if not ok:
        FAILS.append(name)


def _bars_sample(n_sym=40, seed=3):
    meta, bars = R.load_bars()
    rnd = random.Random(seed)
    syms = [s for s in sorted(bars) if len(bars[s]["c"]) > 300]
    return bars, rnd.sample(syms, n_sym), rnd


def _perturb(b, lo, hi, rnd):
    """Copy of b with bars [lo, hi) scaled by random factors (OHLC consistent)."""
    nb = {k: (v.copy() if isinstance(v, np.ndarray) else copy.copy(v)) for k, v in b.items()}
    for j in range(lo, hi):
        f = rnd.uniform(0.3, 3.0)
        for k in ("o", "h", "l", "c"):
            nb[k][j] = b[k][j] * f
        nb["v"][j] = b["v"][j] * rnd.uniform(0.1, 10)
    return nb


def l1_l2_l3(bars, syms, rnd):
    bad_f, bad_l, bad_ff, n = [], [], [], 0
    for sym in syms:
        b = bars[sym]
        b["fac"] = np.ones(len(b["c"]))
        eps = R.episodes_for(sym, b)
        for i in rnd.sample(range(200, len(b["c"]) - 25), 4):
            n += 1
            f0 = R.features(b, i)
            fut = _perturb(b, i + 1, len(b["c"]), rnd)
            if R.features(fut, i) != f0:
                bad_f.append((sym, i))
            l0 = R.label_fwd(b, eps, [], i, 10)
            past = _perturb(b, 0, i, rnd)                  # bars strictly before the decision bar
            if R.label_fwd(past, eps, [], i, 10) != l0:
                bad_l.append((sym, i))
            full = R.frame_upto(b, i, tail=10 ** 6)
            ff = R.fast_frame(b, i)
            if R.S().pivot_cycle_state(full) != R.S().pivot_cycle_state(ff) or \
                    R.S().tested_level(full) != R.S().tested_level(ff):
                bad_ff.append((sym, i))
    check("L1 features ignore every bar after the decision", not bad_f, f"{n} rows · bad {bad_f[:3]}")
    check("L2 forward label ignores every bar before the decision", not bad_l, f"{n} rows · bad {bad_l[:3]}")
    check("L3 FastFrame == pandas frame (cycle + tested level)", not bad_ff, f"{n} rows · bad {bad_ff[:3]}")


def l4(bars, syms, rnd):
    bad, n = [], 0
    for sym in syms:
        b = bars[sym]
        v = R.identity_vec(b, None)
        for i in rnd.sample(range(130, len(b["c"])), 8):
            n += 1
            if bool(R.S()._had_pivot_identity(R.frame_upto(b, i, tail=10 ** 6))) != bool(v[i]):
                bad.append((sym, i))
    check("L4 identity_vec == _had_pivot_identity", not bad and n >= 300, f"{n} bars · bad {bad[:3]}")


def _synthetic(kind):
    rnd = random.Random(11 if kind == "jump" else 12)
    n = 160
    c = [5.0 * (1 + rnd.uniform(-0.02, 0.02)) for _ in range(n)]
    if kind == "jump":
        c[-3] = c[-4] * 1.8                                  # +80% one-day jump three sessions ago
        c[-2], c[-1] = c[-3] * 0.97, c[-3] * 0.95
    else:
        base = c[-15]
        for k in range(14, 0, -1):
            c[-k] = base * (1 + 0.06 * (15 - k))            # steady climb, no single day >= 50%
    d = pd.bdate_range("2025-01-02", periods=n)
    a = np.array(c)
    df = pd.DataFrame({"Open": a, "High": a * 1.01, "Low": a * 0.99, "Close": a, "Volume": np.full(n, 1e6)}, index=d)
    b = {"d": [x.date().isoformat() for x in d], "o": a, "h": a * 1.01, "l": a * 0.99, "c": a, "v": np.full(n, 1e6)}
    return df, b


def l5():
    S = R.S()
    ok, info = True, []
    for kind in ("jump", "run"):
        df, b = _synthetic(kind)
        with contextlib.redirect_stdout(io.StringIO()):
            live = S.scan_explosions({"SYN": df})
        mine = R.detect_asof(b["c"], len(b["c"]) - 1)
        if not live or mine is None:
            ok = False
            info.append((kind, bool(live), mine))
            continue
        e = live[0]
        same = (({"jump": "قفزة", "run": "تجمّع"}[mine[0]] == e["kind"]) and b["d"][mine[1]] == e["expl_date"]
                and round(mine[2], 0) == e["gain"])
        ok &= same
        info.append((kind, e["kind"], e["expl_date"], e["gain"], b["d"][mine[1]], round(mine[2], 0)))
    check("L5 detect_asof == live scan_explosions (kind · day · gain)", ok, str(info))


def l6():
    rows = E.load(E.PI_FILE, E.DISC_FROM, E.DISC_TO)
    cal = sorted({r["t"] for r in E.load(E.PI_FILE, "0000", "9999")})
    gap = sum(1 for d in cal if E.DISC_TO < d < E.TEST_FROM)
    check("L6 windows ordered · embargo at least H sessions · discovery rows end by DISC_TO",
          E.DISC_TO < E.TEST_FROM and gap >= E.H and max(r["t"] for r in rows) <= E.DISC_TO,
          f"embargo sessions {gap} · H {E.H}")


def l7():
    import tempfile
    tmp = tempfile.mkdtemp()
    fake = os.path.join(tmp, "R70_PREREG.md")
    open(fake, "wb").write(open(E.PREREG, "rb").read() + b"\n")
    orig = E.PREREG
    try:
        E.PREREG = fake
        refused = not E.prereg_ok()
        E.PREREG = orig
        sealed = E.prereg_ok()
    finally:
        E.PREREG = orig
    r = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0, %r); import r70_eval as E; "
                        "E.PREREG = %r; E.test()" % (HERE, fake)], capture_output=True, text=True, cwd=ROOT)
    check("L7 a changed preregistration is refused (exit 9) · the sealed one is accepted",
          refused and sealed and r.returncode == 9, f"rc={r.returncode}")


def l8():
    if os.environ.get("R70_FAST") == "1":
        print("⏭️ L8 skipped (R70_FAST=1)")
        return
    r = subprocess.run([sys.executable, os.path.join(HERE, "r70_build.py"), "--check"], capture_output=True, text=True,
                       cwd=ROOT)
    check("L8 r70_build.py --check regenerates every output identically", r.returncode == 0,
          (r.stdout.strip().splitlines() or [""])[-1])


if __name__ == "__main__":
    bars, syms, rnd = _bars_sample()
    l1_l2_l3(bars, syms, rnd)
    l4(bars, syms, rnd)
    l5()
    l6()
    l7()
    l8()
    print(f"\nالفاشل: {len(FAILS)}" + (" — " + ", ".join(FAILS) if FAILS else ""))
    sys.exit(1 if FAILS else 0)
