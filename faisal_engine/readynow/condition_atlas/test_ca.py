"""Guards of the Faisal condition atlas study (research only). Exit 0 = all pass.
CA_FAST=1 skips the slow regenerations (CA2 build, CA13 reconciliation; CA9, CA12 and CA14 are fast and always run).
Run from the repo root:  python3 faisal_engine/readynow/condition_atlas/test_ca.py
"""
import gzip
import csv
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
FAST = os.environ.get("CA_FAST") == "1"
FAILS = []


def check(name, ok, detail=""):
    print(("✅ " if ok else "❌ ") + name + ("" if ok else f" — {detail}"))
    if not ok:
        FAILS.append(name)


def guarded(name, fn):
    try:
        ok, detail = fn()
    except Exception as e:                                                # noqa: BLE001
        ok, detail = False, f"⛔ {type(e).__name__}: {e}"
    check(name, ok, detail)


def ca1():
    """Look-ahead: the stored columns equal a recomputation on bars truncated at the decision day."""
    import ca_build as CB
    _m, bars = CB.R.load_bars()
    sp = json.load(open(CB.R.SPLITS_FILE, encoding="utf-8"))["splits"]
    rows = list(csv.DictReader(gzip.open(os.path.join(CB.DATA, "ca_rows.csv.gz"), "rt", encoding="utf-8")))
    random.seed(20261011)
    bad = []
    for r in random.sample(rows, 25):
        b = bars[r["sym"]]
        i = b["ix"][r["t"]]
        p = CB.point_features(b, CB.reverse_splits(sp.get(r["sym"]), b["d"]), i)
        for k in CB.COLS:
            a = None if r[k] == "" else float(r[k])
            x = CB._val(p[k])
            if (a is None) != (x is None) or (a is not None and abs(a - x) > 1e-3 * max(1.0, abs(a))):
                bad.append((r["sym"], r["t"], k, a, x))
    return not bad, str(bad[:3])


def ca2():
    p = subprocess.run([sys.executable, os.path.join(HERE, "ca_build.py"), "--check"], capture_output=True, text=True,
                       cwd=ROOT, timeout=3000)
    return p.returncode == 0, p.stdout[-200:] + p.stderr[-200:]


def ca3():
    """Atlas integrity: every flag named in the atlas exists; every condition has a quote and a source; every named
    image (TG_/IMG_/X_/APP_ ids) is on disk unless recorded as a text record."""
    import ca_atlas as A
    import ca_lib as L
    disk = {os.path.splitext(f)[0] for f in os.listdir(os.path.join(ROOT, "faisal_images"))}
    bad = []
    for a in A.ATLAS:
        if a["flag"] is not None and a["flag"] not in L.COND and a["flag"] != "K11_STANDARD":
            bad.append(("flag", a["id"], a["flag"]))
        if not a["quote"].strip() or not a["src"]:
            bad.append(("quote", a["id"]))
        for s in a["src"]:
            sid = s.split(" ")[0]
            if sid[:3] in ("TG_", "IMG", "X_2", "APP") and "text record" not in s and sid not in disk:
                bad.append(("image", a["id"], sid))
        for k in ("kind", "strict", "conf", "data"):
            allowed = {"kind": {"pivot", "strength", "timing", "confirmation", "invalidation"},
                       "strict": {"mandatory", "likely optional", "undecided"},
                       "conf": {"documented", "reconstructed from example", "hypothetical"},
                       "data": {"testable", "partial", "not available"}}[k]
            if a[k] not in allowed:
                bad.append((k, a["id"], a[k]))
    ids = [a["id"] for a in A.ATLAS]
    if len(ids) != len(set(ids)):
        bad.append(("duplicate ids",))
    return not bad, str(bad[:4])


def ca4():
    """Candle definitions on synthetic bars."""
    import numpy as np
    import ca_build as CB
    o = np.array([10.0, 9.8, 9.5, 9.6, 9.0])
    h = np.array([10.1, 9.9, 9.6, 9.65, 9.05])
    lo = np.array([9.7, 9.4, 9.2, 9.3, 8.0])
    c = np.array([9.8, 9.5, 9.3, 9.4, 9.02])          # last bar: tiny body at the top, long lower wick = hammer
    k = CB.candles_at(o, h, lo, c, 4)
    o2, h2, l2, c2 = (np.array([10.0, 10.0, 9.0]), np.array([10.2, 10.1, 9.6]), np.array([9.8, 8.9, 9.1]),
                      np.array([10.1, 9.0, 9.4]))   # bar 1 big red, bar 2 small green inside its body = harami
    k2 = CB.candles_at(o2, h2, l2, c2, 2)
    ok = (k["k_hammer"] == 1 and k["k_longwick"] == 1 and k["k_hammer_red"] == 0 and k["k_invhammer"] == 0
          and k2["k_harami"] == 1 and k2["k_inside"] == 1 and k2["k_engulf"] == 0)
    return ok, f"{k} {k2}"


def ca5():
    """Development outputs read development rows only (windows recorded in the JSON) and exclude seeds/HUBC."""
    import ca_dev as CD
    import ca_lib as L
    s = json.load(open(os.path.join(L.DATA, "strength_dev.json"), encoding="utf-8"))
    m = json.load(open(os.path.join(L.DATA, "model_dev.json"), encoding="utf-8"))
    rows, _by, _m = L.load("development")
    lo, hi = L.K.WINDOWS["development"]
    ok = (s["window"] == [lo, hi] and m["train"][0] >= lo and m["test"][1] <= hi
          and CD.WIN == "development" and lo <= CD.TRAIN[0] and CD.TEST[1] <= hi and CD.TRAIN[1] < CD.TEST[0]
          and all(lo <= r["t"] <= hi for r in rows) and not any(r["sym"] in L.K.EXCLUDE for r in rows))
    return ok, f"{s['window']} {m['train']} {m['test']} {CD.TRAIN} {CD.TEST}"


def ca6():
    """The 2026 scorer refuses to run when the protocol or the frozen model differs from the pinned hashes."""
    import ca_final as CF
    ok_now = CF.protocol_ok()
    saved = CF.PROTOCOL_SHA256
    try:
        CF.PROTOCOL_SHA256 = "0" * 64
        refused = not CF.protocol_ok()
    finally:
        CF.PROTOCOL_SHA256 = saved
    return ok_now and refused, f"ok_now={ok_now} refused={refused}"


def ca7():
    """Classes: invalidated rows never reach READY; READY_1 has exactly the tool's per-session count when enough
    valid rows exist."""
    import ca_dev as CD
    rows = []
    for j in range(10):
        rows.append({"sym": f"S{j}", "t": "2025-06-02", "lab": "NEG", "rsi": "20" if j < 2 else "50", "hold_n": "6",
                     "held": "1", "boom5": "0", "dist": "45" if j == 9 else "5", "ret5": "0", "a_grp10": "0",
                     "s_C": float(10 - j) if j != 9 else 99.0, "s_B": float(j)})
    by = {"2025-06-02": rows}
    tc = lambda r: r["rsi"] == "20"                                     # noqa: E731 — two flags
    cls = CD.classes(by, tc, lambda r: r["s_C"], lambda r: r["s_B"])
    r1 = [k for k, v in cls.items() if v == "READY_1"]
    ok = cls[("S9", "2025-06-02")] == "INVALIDATED" and len(r1) == 2 and ("S0", "2025-06-02") in r1
    return ok, str(cls)


def ca8():
    """The app's weighted score sums its visible weights (70) when every condition holds."""
    import ca_lib as L
    total = sum(w for _n, w, _f in L.APP_WEIGHTS if w) + 8.0
    return abs(total - 70.0) < 1e-9, str(total)


def ca9():
    p = subprocess.run([sys.executable, os.path.join(HERE, "ca_docs.py"), "--check"], capture_output=True, text=True,
                       cwd=ROOT, timeout=600)
    return p.returncode == 0, p.stdout[-200:]


def ca10():
    """The verdict file is reproduced by the verdict script from final.json (when the sealed run exists)."""
    import ca_lib as L
    path = os.path.join(L.DATA, "verdict.json")
    if not os.path.exists(os.path.join(L.DATA, "final.json")):
        return True, "no sealed run yet"
    import ca_verdict as V
    stored = json.load(open(path, encoding="utf-8"))
    return V.verdict() == stored, "verdict differs from final.json"


def ca11():
    p = subprocess.run([sys.executable, os.path.join(HERE, "ca_report.py"), "--check"], capture_output=True, text=True,
                       cwd=ROOT, timeout=600)
    return p.returncode == 0, p.stdout[-200:]


def ca12():
    """The reconciliation addendum: §0 unchanged since it was written before the run, §1–§6 equal their rendering, the
    sealed data files unchanged, and the reconciliation reproduces the sealed numbers it re-reads."""
    import ca_reconcile as RC
    return RC.doc_check()


def ca13():
    p = subprocess.run([sys.executable, os.path.join(HERE, "ca_reconcile.py"), "--check"], capture_output=True,
                       text=True, cwd=ROOT, timeout=1800)
    return p.returncode == 0, p.stdout[-200:]


def ca14():
    """The mutation round can neither run nor leave stale bytecode: every run is `python -B` with
    PYTHONDONTWRITEBYTECODE=1, the mutated module's .pyc (and only that module's) is purged after the mutated write and
    after the restore — checked by calling ca_mutate's own run/purge/main with the subprocess stubbed."""
    import contextlib
    import importlib
    import io
    import tempfile
    import ca_mutate as MU

    class _P:
        returncode, stdout, stderr = 1, "❌ CA0 stub\n", ""
    # the round itself runs this guard with PYTHONDONTWRITEBYTECODE=1 in its environment: drop the inherited value and
    # rebuild the harness's ENV, so the check sees what ca_mutate sets, not what its parent passed down (CM15)
    inherited = os.environ.pop("PYTHONDONTWRITEBYTECODE", None)
    calls = []
    try:
        MU = importlib.reload(MU)
        orig = MU.subprocess.run
        try:
            MU.subprocess.run = lambda args, **kw: (calls.append((list(args), dict(kw.get("env") or {}))), _P())[1]
            MU.run()
        finally:
            MU.subprocess.run = orig
    finally:
        if inherited is not None:
            os.environ["PYTHONDONTWRITEBYTECODE"] = inherited
    flags_ok = bool(calls) and "-B" in calls[-1][0] and calls[-1][1].get("PYTHONDONTWRITEBYTECODE") == "1"
    with tempfile.TemporaryDirectory() as d:
        mod = os.path.join(d, "x_mod.py")
        open(mod, "w", encoding="utf-8").write("X = 1\n")
        os.makedirs(os.path.join(d, "__pycache__"))
        mine, other = (os.path.join(d, "__pycache__", n) for n in ("x_mod.cpython-311.pyc", "y_mod.cpython-311.pyc"))
        for f in (mine, other):
            open(f, "wb").write(b"0")
        MU.purge(mod)
        purge_ok = not os.path.exists(mine) and os.path.exists(other)
        events, saved = [], (MU.CODE, MU.run, MU.purge, sys.argv)
        try:
            MU.CODE = [("CMX", mod, "X = 1", "X = 2", "CA0")]
            MU.run = lambda: (events.append(("run", open(mod, encoding="utf-8").read())), (1, ["CA0"], False))[1]
            MU.purge = lambda q: events.append(("purge", open(q, encoding="utf-8").read()))
            sys.argv = [sys.argv[0]]
            with contextlib.redirect_stdout(io.StringIO()):
                MU.main()
        finally:
            MU.CODE, MU.run, MU.purge, sys.argv = saved
    order_ok = events == [("purge", "X = 2\n"), ("run", "X = 2\n"), ("purge", "X = 1\n"), ("run", "X = 1\n")]
    return flags_ok and purge_ok and order_ok, f"flags={flags_ok} purge={purge_ok} order={events}"


def main():
    guarded("CA1 look-ahead: stored atlas columns equal recomputation on truncated bars", ca1)
    if not FAST:
        guarded("CA2 the feature build regenerates identically", ca2)
    guarded("CA3 atlas integrity (flags, quotes, sources on disk, classification values)", ca3)
    guarded("CA4 candle definitions on synthetic bars", ca4)
    guarded("CA5 development reads development rows only, seeds and HUBC excluded", ca5)
    guarded("CA6 the 2026 scorer is sealed to the protocol and the frozen model", ca6)
    guarded("CA7 invalidated rows never reach READY; READY_1 keeps the tool's burden", ca7)
    guarded("CA8 the app score sums its visible weights", ca8)
    guarded("CA9 the generated documents match their sources", ca9)
    guarded("CA10 the verdict is reproduced from the sealed results", ca10)
    guarded("CA11 the result reports match their JSON sources", ca11)
    guarded("CA12 the reconciliation addendum matches its sources and the sealed files are unchanged", ca12)
    if not FAST:
        guarded("CA13 the reconciliation regenerates identically", ca13)
    guarded("CA14 the mutation round neither runs nor leaves stale bytecode", ca14)
    print("FAILED: " + ", ".join(FAILS) if FAILS else "ALL PASS")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
