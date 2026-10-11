"""SEQ70 guards — run from the repo root:  python3 faisal_engine/seq70/test_s70.py   (exit 0 = all pass).

G1  path descriptors read bars at or before the decision session only (every later bar altered → same values)
G2  the reconstruction reads discovery rows and discovery launches only
G3  windows: validation starts more than 10 sessions after discovery ends, test starts 10 sessions after validation
    ends, the last test decision has its 10 sessions inside the archive
G4  the flag needs the top volume quintile AND a negative 5-session return; K-V controls are never flagged, K-P
    controls have r5 ≥ 0; same session, same price bucket, within the caliper, never reused within a session
G5  spells: a gap of more than SPELL_GAP sessions opens a new spell; age counts sessions from the spell start
G6  a changed preregistration is refused (exit 9) before any read; the sealed one is accepted
G7  outputs regenerate byte-identically (s70_build --check · explore.json · dev_discovery.json)  [slow; R70_FAST=1 skips]
"""
import copy
import os
import random
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
os.environ["FAISAL_ONLY"] = "1"
import numpy as np                                                        # noqa: E402
import s70_build as B                                                     # noqa: E402
import s70_eval as V                                                      # noqa: E402
import s70_explore as X                                                   # noqa: E402

FAILS = []


def check(name, ok, info=""):
    print(("✅ " if ok else "❌ ") + name + (f" — {info}" if info else ""))
    if not ok:
        FAILS.append(name)


def g1():
    meta, bars = B.R.load_bars()
    rnd = random.Random(7)
    syms = rnd.sample([s for s in sorted(bars) if len(bars[s]["c"]) > 300], 30)
    bad, n = [], 0
    for sym in syms:
        b = bars[sym]
        for i in rnd.sample(range(100, len(b["c"]) - 5), 4):
            n += 1
            d0 = B.descriptors(b, i)
            nb = {k: (v.copy() if isinstance(v, np.ndarray) else copy.copy(v)) for k, v in b.items()}
            for j in range(i + 1, len(b["c"])):
                f = rnd.uniform(0.3, 3.0)
                for k in ("o", "h", "l", "c"):
                    nb[k][j] = b[k][j] * f
                nb["v"][j] = b["v"][j] * rnd.uniform(0.1, 10)
            if B.descriptors(nb, i) != d0:
                bad.append((sym, i))
    check("G1 path descriptors ignore bars after the decision session", not bad and n == 120, f"{n} rows · bad {bad[:3]}")


def g2():
    fake = [{"t": d, "sym": "S", "split60": "0", "desc_ok": "1"} for d in ("2025-04-30", "2025-07-01", "2026-01-02",
                                                                              "2026-03-01")]
    fev = [{"quality": "OK", "launch": d, "sym": "S"} for d in ("2025-07-01", "2026-02-01")]
    orig = X.rd
    try:
        X.rd = lambda name: [dict(r) for r in (fake if name == "traj.csv.gz" else fev)]
        traj, events = X.load_discovery()
        ok = [r["t"] for r in traj] == ["2025-07-01"] and [e["launch"] for e in events] == ["2025-07-01"]
    except Exception as e:                                                # noqa: BLE001
        ok = False
        traj, events = [f"⛔ {type(e).__name__}"], []
    finally:
        X.rd = orig
    check("G2 the reconstruction reads discovery rows and launches only", ok, f"{[r['t'] for r in traj if isinstance(r, dict)]}")


def g3():
    try:
        import csv
        import gzip
        with gzip.open(os.path.join(B.DATA, "traj.csv.gz"), "rt", encoding="utf-8") as f:
            cal = sorted({r["t"] for r in csv.DictReader(f)})
        meta, bars = B.R.load_bars()
        full = B.R.sessions_calendar(bars)
        ix = {d: i for i, d in enumerate(full)}
        (v0, v1), (t0, t1) = V.WINDOWS["validation"], V.WINDOWS["test"]
        d1 = X.DISC_TO
        last_d = max(d for d in full if d <= d1)
        ok = (ix[v0] - ix[last_d] > 10 and ix[t0] - ix[v1] > 10 and ix[t1] + 10 <= len(full) - 1
              and V.DEV_WINDOW["discovery"][1] == X.DISC_TO and v0 in cal and t1 in cal)
        info = f"disc→val {ix[v0] - ix[last_d]} · val→test {ix[t0] - ix[v1]} · test end+10 ≤ last {ix[t1] + 10 <= len(full) - 1}"
    except Exception as e:                                                # noqa: BLE001
        ok, info = False, f"⛔ {type(e).__name__}: {e}"
    check("G3 windows are separated by the 10-session horizon and inside the archive", ok, info)


def g4():
    rnd = random.Random(11)
    rows = []
    for t in ("2026-02-02", "2026-02-03"):
        for k in range(80):
            rows.append({"t": t, "sym": f"S{k:02d}", "v1x": str(round(rnd.uniform(0.1, 9), 3)),
                         "v5x": str(round(rnd.uniform(0.1, 5), 3)), "tr5x": str(round(rnd.uniform(0.3, 3), 3)),
                         "r5": str(round(rnd.uniform(-40, 40), 2)), "range20": str(round(rnd.uniform(10, 300), 1)),
                         "px": str(round(rnd.choice([0.5, 2.0, 5.0, 20.0]) * rnd.uniform(0.9, 1.1), 3)), "f10": "NEG"})
    by = V.annotate(rows)
    keys = {(r["sym"], r["t"]) for r in rows}
    fl = [r for r in rows if V.flagged(r)]
    ok = bool(fl) and all(r["p_v1x"] >= V.TOP_Q and float(r["r5"]) < 0 for r in fl)
    ok &= not any(V.flagged(r) for r in rows if r["p_v1x"] < V.TOP_Q or float(r["r5"]) >= 0)
    pv, uv = V.match(by, keys, "V")
    pp, up = V.match(by, keys, "P")
    ok &= all(a["t"] == c["t"] and not V.flagged(c) and V.bucket(a["px"]) == V.bucket(c["px"])
              and abs(a["p_r5"] - c["p_r5"]) <= V.CALIPER and abs(a["p_range20"] - c["p_range20"]) <= V.CALIPER
              for a, c in pv)
    ok &= all(a["t"] == c["t"] and float(c["r5"]) >= 0 and V.bucket(a["px"]) == V.bucket(c["px"])
              and abs(a["p_v1x"] - c["p_v1x"]) <= V.CALIPER and abs(a["p_range20"] - c["p_range20"]) <= V.CALIPER
              for a, c in pp)
    for pr in (pv, pp):
        per = {}
        for a, c in pr:
            per.setdefault(c["t"], []).append(c["sym"])
        ok &= all(len(v) == len(set(v)) for v in per.values())
    ok &= len(pv) + uv == len(fl) and len(pp) + up == len(fl)
    check("G4 flag = top volume quintile ∧ r5 < 0 · K-V/K-P controls obey session, bucket, caliper, no reuse", ok,
          f"flagged {len(fl)} · K-V {len(pv)}+{uv} · K-P {len(pp)}+{up}")


def g5():
    got = B.spells([0, 1, 2, 8, 9, 20])
    want = [(0, 0), (0, 1), (0, 2), (0, 8), (0, 9), (1, 0)]       # 2→8 gap of 5 non-pivot sessions continues
    got2 = B.spells([0, 7])                                        # 6 non-pivot sessions → new spell
    check("G5 spells: a gap above SPELL_GAP opens a new spell · age counts from the spell start",
          got == want and got2 == [(0, 0), (1, 0)], f"{got} · {got2}")


def g6():
    tmp = tempfile.mkdtemp()
    try:
        fake = os.path.join(tmp, "S70_PREREG.md")
        open(fake, "wb").write(open(V.PREREG, "rb").read() + b"\n")
        sealed = V.prereg_ok()
        code = ("import sys; sys.path.insert(0, %r); import s70_eval as V; V.PREREG = %r; V.DATA = %r; "
                "V.rd = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('read before the seal check')); V.test()"
                % (HERE, fake, tmp))
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT)
        ok = sealed and r.returncode == 9 and "read before the seal check" not in (r.stdout + r.stderr)
        check("G6 changed preregistration refused (exit 9) before any read · sealed one accepted", ok,
              f"sealed {sealed} · rc={r.returncode}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def g7():
    if os.environ.get("R70_FAST") == "1":
        print("⏭️ G7 skipped (R70_FAST=1)")
        return
    env = dict(os.environ, GIT_ALLOW_PROTOCOL="file")
    r1 = subprocess.run([sys.executable, os.path.join(HERE, "s70_build.py"), "--check"], capture_output=True,
                        text=True, cwd=ROOT, env=env)
    same = []
    for script, mode, out in (("s70_explore.py", None, "explore.json"), ("s70_eval.py", "dev", "dev_discovery.json")):
        p = os.path.join(B.DATA, out)
        before = open(p, "rb").read()
        r = subprocess.run([sys.executable, os.path.join(HERE, script)] + ([mode] if mode else []), capture_output=True,
                           text=True, cwd=ROOT, env=env)
        after = open(p, "rb").read()
        if after != before:
            open(p, "wb").write(before)
        same.append(r.returncode == 0 and after == before)
    check("G7 build, reconstruction and discovery dry run regenerate identically", r1.returncode == 0 and all(same),
          f"build {r1.returncode} · explore {same[0]} · dev {same[1]}")


if __name__ == "__main__":
    g1()
    g2()
    g3()
    g4()
    g5()
    g6()
    g7()
    print(f"\nالفاشل: {len(FAILS)}" + (" — " + ", ".join(FAILS) if FAILS else ""))
    sys.exit(1 if FAILS else 0)
