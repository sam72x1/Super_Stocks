"""ALERTS70 guards — run from the repo root:  python3 faisal_engine/alerts70/test_a70.py   (exit 0 = all pass).

G1  daily fields (ret1 · volx · px) ignore every bar after the decision session
G2  forward label at the decision session: R70 label_fwd ignores bars before t, and every alert row carries exactly
    the label of its observed symbol-day (same session index in both loops of the builder)
G3  decision-session rule: in the builder code (AST) an alert at/after 16:00 ET moves to the next session; in the
    outputs every alert row obeys it and the observed table's alerted flag is exactly the set of decision sessions
G4  classify(): synthetic episodes give BEFORE_START · START_DAY · UNDERWAY_PRE70 · AT_OR_AFTER_70 · AFTER_70 ·
    NO_EVENT_WITHIN_H · CENSORED exactly where defined
G5  matched control: same session, same price bucket, never an alerted row, never reused within a session
G6  offline: GIT_ENV sets GIT_ALLOW_PROTOCOL=file in the code itself (AST), every git call of the extractor uses it,
    and only blobs already in the local object store are streamed
G7  a changed preregistration is refused (exit 9) before any data is read; the sealed one is accepted
G8  outputs regenerate byte-identically (a70_extract.py --check · a70_build.py --check)  [slow; R70_FAST=1 skips]
A70_DATA=<dir> points G2/G3 at another copy of data/ (used by a70_mutate.py for data mutations).
"""
import ast
import copy
import csv
import gzip
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
import a70_build as B                                                     # noqa: E402
import a70_eval as V                                                      # noqa: E402

DATA_DIR = os.environ.get("A70_DATA") or B.DATA
FAILS = []


def check(name, ok, info=""):
    print(("✅ " if ok else "❌ ") + name + (f" — {info}" if info else ""))
    if not ok:
        FAILS.append(name)


def _rd(name):
    with gzip.open(os.path.join(DATA_DIR, name), "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _src_tree(name):
    return ast.parse(open(os.path.join(HERE, name), encoding="utf-8").read())


def _fn(tree, name):
    return next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name), None)


def _stmts(node):
    """Normalised source of every simple statement inside a function (comments and docstrings never count)."""
    return {ast.unparse(n) for n in ast.walk(node) if isinstance(n, (ast.Assign, ast.Expr))} if node else set()


def _perturb(b, lo, hi, rnd):
    nb = {k: (v.copy() if isinstance(v, np.ndarray) else copy.copy(v)) for k, v in b.items()}
    for j in range(lo, hi):
        f = rnd.uniform(0.3, 3.0)
        for k in ("o", "h", "l", "c"):
            nb[k][j] = b[k][j] * f
        nb["v"][j] = b["v"][j] * rnd.uniform(0.1, 10)
    return nb


def g1_g2():
    meta, bars = B.R.load_bars()
    rnd = random.Random(5)
    syms = rnd.sample([s for s in sorted(bars) if len(bars[s]["c"]) > 300], 30)
    bad1, bad2, n = [], [], 0
    for sym in syms:
        b = bars[sym]
        b["fac"] = np.ones(len(b["c"]))
        eps = B.episodes_with_trough(sym, b, {})
        for i in rnd.sample(range(200, len(b["c"]) - 25), 4):
            n += 1
            f0 = B.daily_fields(b, i)
            if B.daily_fields(_perturb(b, i + 1, len(b["c"]), rnd), i) != f0:
                bad1.append((sym, i))
            l0 = B.R.label_fwd(b, eps, [], i, B.H)
            if B.R.label_fwd(_perturb(b, 0, i, rnd), eps, [], i, B.H) != l0:
                bad2.append((sym, i))
    check("G1 daily fields ignore bars after the decision session", not bad1, f"{n} rows · bad {bad1[:3]}")
    # the builder labels alerts (index = alert date + shift) and observed days (index = t) in two separate loops:
    # both must give the identical forward label for the same symbol-day
    try:
        al_rows, ob_rows = _rd("alerts.csv.gz"), _rd("obs.csv.gz")
        ob = {(o["sym"], o["t"]): o for o in ob_rows}
        rows = [(a, ob.get((a["symbol"], a["decision_t"]))) for a in al_rows if a["decision_t"]]
        rows = [(a, o) for a, o in rows if o and o["bars"] == "OK"]
        mism = [a["symbol"] + "|" + a["decision_t"] for a, o in rows
                if (a["f10"], a["f10_k"], a["f10_gain"]) != (o["f10"], o["f10_k"], o["f10_gain"])]
        info = f"{n} rows look-back · {len(rows)} alert rows · mismatch {mism[:3]}"
        ok = not bad2 and len(rows) > 1000 and not mism
    except Exception as e:                                                # noqa: BLE001
        ok, info = False, f"⛔ {type(e).__name__}: {e}"
    check("G2 forward label at the decision session (no look-back · alerts = observed day)", ok, info)


def g3():
    try:
        st = _stmts(_fn(_src_tree("a70_build.py"), "build"))
        code_ok = ("row['shift'] = int(_et.hour >= 16)" in st and "i = b['ix'][d] + row['shift']" in st
                   and "row['decision_t'] = b['d'][i]" in st)
        al_rows, ob_rows = _rd("alerts.csv.gz"), _rd("obs.csv.gz")
        dec = [a for a in al_rows if a["decision_t"]]
        bad_shift = [a["symbol"] for a in dec if int(a["shift"]) != int(int(a["anchor_et"][:2]) >= 16)]
        bad_date = [a["symbol"] for a in dec if (a["shift"] == "0" and a["decision_t"] != a["date"])
                    or (a["shift"] == "1" and not a["decision_t"] > a["date"])]
        alerted = {(o["sym"], o["t"]) for o in ob_rows if o["alerted"] == "1"}
        same = alerted == {(a["symbol"], a["decision_t"]) for a in dec}
        n_after = sum(1 for a in dec if a["shift"] == "1")
        ok = code_ok and not bad_shift and not bad_date and same and n_after > 0
        info = f"code {code_ok} · after-hours {n_after} · bad shift {bad_shift[:3]} · bad date {bad_date[:3]} · alerted set {same}"
    except Exception as e:                                                # noqa: BLE001
        ok, info = False, f"⛔ {type(e).__name__}: {e}"
    check("G3 after-hours alerts move to the next session (code + outputs)", ok, info)


def g4():
    # one episode: launch at index 10, crossing at 13, peak at 15, trough close (index 9) = 1.0
    eps = [{"L_i": 10, "D1_i": 13, "P_i": 15, "trough_close": 1.0, "quality": "OK", "launch": "L", "d1": "D"}]
    n = 40
    got = {
        "before": B.classify(eps, 8, 1.05, n)[0], "start": B.classify(eps, 10, 1.2, n)[0],
        "start_hi": B.classify(eps, 10, 1.75, n)[0], "under": B.classify(eps, 12, 1.5, n)[0],
        "under_hi": B.classify(eps, 12, 1.71, n)[0], "after": B.classify(eps, 14, 2.0, n)[0],
        "none": B.classify(eps, 20, 1.0, n)[0], "cens": B.classify([], 35, 1.0, n)[0],
        "far": B.classify(eps, -1, 1.0, n)[0]}
    want = {"before": "BEFORE_START", "start": "START_DAY", "start_hi": "AT_OR_AFTER_70", "under": "UNDERWAY_PRE70",
            "under_hi": "AT_OR_AFTER_70", "after": "AFTER_70", "none": "NO_EVENT_WITHIN_H", "cens": "CENSORED",
            "far": "NO_EVENT_WITHIN_H"}
    check("G4 classify() puts each synthetic alert in its defined class", got == want,
          str({k: v for k, v in got.items() if want[k] != v}))


def g5():
    rnd = random.Random(9)
    rows = []
    for t in ("2026-09-01", "2026-09-02"):
        for k in range(60):
            rows.append({"t": t, "sym": f"S{k:02d}", "alerted": "1" if k < 8 else "0",
                         "ret1": str(round(rnd.uniform(-10, 40), 2)), "volx": str(round(rnd.uniform(0.2, 30), 2)),
                         "px": str(round(rnd.choice([0.5, 2.0, 5.0, 20.0]) * rnd.uniform(0.9, 1.1), 3)),
                         "f10": "NEG", "bars": "OK"})
    pairs, un = V.match_controls(rows)
    ok = all(a["t"] == c["t"] and c["alerted"] == "0" and V.bucket(float(a["px"])) == V.bucket(float(c["px"]))
             for a, c in pairs)
    per = {}
    for a, c in pairs:
        per.setdefault(c["t"], []).append(c["sym"])
    ok &= all(len(v) == len(set(v)) for v in per.values())
    check("G5 matched control: same session · same price bucket · never alerted · no reuse",
          ok and len(pairs) + un == 16, f"pairs {len(pairs)} unmatched {un}")


def g6():
    try:
        tree = _src_tree("a70_extract.py")
        env_def = next((n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                        and any(getattr(t, "id", "") == "GIT_ENV" for t in n.targets)), None)
        def_ok = isinstance(env_def, ast.Call) and any(
            k.arg == "GIT_ALLOW_PROTOCOL" and isinstance(k.value, ast.Constant) and k.value.value == "file"
            for k in env_def.keywords)
        calls = [c for c in ast.walk(tree) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                 and c.func.attr in ("run", "Popen", "call", "check_output") and getattr(c.func.value, "id", "") == "subprocess"]
        env_ok = all(any(k.arg == "env" and getattr(k.value, "id", "") == "GIT_ENV" for k in c.keywords) for c in calls)
        st = _stmts(_fn(tree, "extract"))
        filt = "cs = [c for c in allc if c[2] in have]" in st
        fed = any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "stream_blobs"
                  and n.args and ast.unparse(n.args[0]) == "[c[2] for c in cs]" for n in ast.walk(_fn(tree, "extract")))
        ok, info = bool(calls) and def_ok and env_ok and filt and fed, \
            f"calls {len(calls)} · GIT_ENV {def_ok} · env {env_ok} · local filter {filt} · streamed {fed}"
    except Exception as e:                                                # noqa: BLE001
        ok, info = False, f"⛔ {type(e).__name__}: {e}"
    check("G6 extractor git calls run offline (GIT_ALLOW_PROTOCOL=file) and read local blobs only", ok, info)


def g7():
    tmp = tempfile.mkdtemp()
    try:
        fake = os.path.join(tmp, "A70_PREREG.md")
        open(fake, "wb").write(open(V.PREREG, "rb").read() + b"\n")
        sealed = V.prereg_ok()
        # the changed seal must stop the run before any read: V.DATA points at an empty directory and V.rd raises
        code = ("import sys; sys.path.insert(0, %r); import a70_eval as V; V.PREREG = %r; V.DATA = %r; "
                "V.rd = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('read before the seal check')); V.test()"
                % (HERE, fake, tmp))
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=ROOT)
        ok = sealed and r.returncode == 9 and "read before the seal check" not in (r.stdout + r.stderr)
        check("G7 changed preregistration refused (exit 9) before any read · sealed one accepted", ok,
              f"sealed {sealed} · rc={r.returncode}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def g8():
    if os.environ.get("R70_FAST") == "1":
        print("⏭️ G8 skipped (R70_FAST=1)")
        return
    env = dict(os.environ, GIT_ALLOW_PROTOCOL="file")
    r1 = subprocess.run([sys.executable, os.path.join(HERE, "a70_extract.py"), "--check"], capture_output=True,
                        text=True, cwd=ROOT, env=env)
    r2 = subprocess.run([sys.executable, os.path.join(HERE, "a70_build.py"), "--check"], capture_output=True,
                        text=True, cwd=ROOT, env=env)
    check("G8 extractor and builder regenerate every output identically", r1.returncode == 0 and r2.returncode == 0,
          f"extract {r1.returncode} {r1.stdout.strip()[-60:]} · build {r2.returncode} {r2.stdout.strip()[-60:]}")


if __name__ == "__main__":
    g1_g2()
    g3()
    g4()
    g5()
    g6()
    g7()
    g8()
    print(f"\nالفاشل: {len(FAILS)}" + (" — " + ", ".join(FAILS) if FAILS else ""))
    sys.exit(1 if FAILS else 0)
