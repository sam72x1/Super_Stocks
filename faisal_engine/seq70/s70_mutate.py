"""SEQ70 mutation round — every guard of test_s70.py must fall on its own mutation, cleanly (no crash).
Code mutations edit one line and restore it; M7 corrupts one committed output for the full run and restores it.
Run from the repo root:  GIT_ALLOW_PROTOCOL=file python3 faisal_engine/seq70/s70_mutate.py [--write]
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

D = "faisal_engine/seq70/"
ENV = dict(os.environ, GIT_ALLOW_PROTOCOL="file", GIT_TERMINAL_PROMPT="0")
CODE = [
    ("M1 today's volume replaced by the next session's (truncation removed)", D + "s70_build.py",
     [('c, h, lw, v = b["c"][: i + 1], b["h"][: i + 1], b["l"][: i + 1], b["v"][: i + 1]',
       'c, h, lw, v = b["c"], b["h"], b["l"], b["v"]'),
      ('"v1x": _r(v[i] / vb)', '"v1x": _r(v[i + 1] / vb)')], None, "G1"),
    ("M2 reconstruction reads past the discovery end", D + "s70_explore.py",
     'traj = [r for r in rd("traj.csv.gz") if DISC_FROM <= r["t"] <= DISC_TO]',
     'traj = [r for r in rd("traj.csv.gz") if DISC_FROM <= r["t"]]', "G2"),
    ("M3 test window starts inside the embargo", D + "s70_eval.py",
     '"test": ("2026-06-02", "2026-09-24")', '"test": ("2026-05-20", "2026-09-24")', "G3"),
    ("M4 flag accepts a small positive 5-session return", D + "s70_eval.py",
     'and num(r["r5"]) is not None and num(r["r5"]) < 0)', 'and num(r["r5"]) is not None and num(r["r5"]) < 5)', "G4"),
    ("M4b matching ignores the caliper", D + "s70_eval.py",
     "                    and all(abs(c[k] - a[k]) <= CALIPER for k in keys)]", "                    ]", "G4"),
    ("M5 spell gap off by one", D + "s70_build.py",
     "if prev is None or k - prev > SPELL_GAP + 1:", "if prev is None or k - prev > SPELL_GAP:", "G5"),
    ("M6 seal check skipped", D + "s70_eval.py", "    if not prereg_ok():", "    if False:", "G6"),
]


def run(fast=True):
    env = dict(ENV)
    if fast:
        env["R70_FAST"] = "1"
    else:
        env.pop("R70_FAST", None)
    p = subprocess.run([sys.executable, D + "test_s70.py"], capture_output=True, text=True, env=env, timeout=3600)
    fell = [ln.split()[1] for ln in p.stdout.splitlines() if ln.startswith("❌")]
    return p.returncode, fell, ("Traceback" in p.stdout + p.stderr)


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    res = []
    dd = os.path.join(D, "data")
    keep = {f: _sha(os.path.join(dd, f)) for f in sorted(os.listdir(dd))}
    for name, path, old, new, lock in CODE:
        src = open(path, encoding="utf-8").read()
        edits = old if isinstance(old, list) else [(old, new)]
        bad = [o for o, _n in edits if src.count(o) != 1]
        if bad:
            res.append([name, f"⛔ anchor count {[src.count(o) for o in bad]}", "", "expected " + lock])
            continue
        mut = src
        for o, n in edits:
            mut = mut.replace(o, n)
        try:
            open(path, "w", encoding="utf-8").write(mut)
            shutil.rmtree(D + "__pycache__", ignore_errors=True)
            rc, fell, crash = run()
            res.append([name, "fell: " + ",".join(fell), "crash" if crash else "clean", "expected " + lock])
        finally:
            open(path, "w", encoding="utf-8").write(src)
    out = os.path.join(dd, "events.csv.gz")
    raw = open(out, "rb").read()
    try:
        open(out, "wb").write(raw + b"\0")
        rc, fell, crash = run(fast=False)
        res.append(["M7 corrupted output (full run)", "fell: " + ",".join(fell), "crash" if crash else "clean",
                    "expected G7"])
    finally:
        open(out, "wb").write(raw)
    shutil.rmtree(D + "__pycache__", ignore_errors=True)
    after = {f: _sha(os.path.join(dd, f)) for f in sorted(os.listdir(dd))}
    res.append(["data/ unchanged after the round", str(after == keep), "", ""])
    for r in res:
        print(r)
    return res


if __name__ == "__main__":
    out = main()
    if "--write" in sys.argv:
        json.dump({"run": "2026-10-11", "harness": D + "s70_mutate.py", "result": out},
                  open(os.path.join(D, "data", "mutations.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
