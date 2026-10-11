"""READYNOW mutation round — every guard of test_rn.py must fall on its own mutation, cleanly (no crash).
Code mutations edit one line and restore it; M7 corrupts one committed output for the full run and restores it.
Run from the repo root:  GIT_ALLOW_PROTOCOL=file python3 faisal_engine/readynow/rn_mutate.py [--write]
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

D = "faisal_engine/readynow/"
ENV = dict(os.environ, GIT_ALLOW_PROTOCOL="file", GIT_TERMINAL_PROMPT="0")
CODE = [
    ("M1 RSI read from the next session", D + "rn_build.py",
     '"rsi": _r(z["rsi"][i], 2)', '"rsi": _r(z["rsi"][min(i + 1, len(b["c"]) - 1)], 2)', "G1"),
    ("M2 the window reader ignores its end date", D + "rn_lib.py",
     'return [r for r in rows if lo <= r["t"] <= hi and r["sym"] not in EXCLUDE',
     'return [r for r in rows if lo <= r["t"] and r["sym"] not in EXCLUDE', "G2"),
    ("M3 holdout runs past the label-known limit", D + "rn_lib.py",
     '"holdout": ("2026-06-02", "2026-08-27")', '"holdout": ("2026-06-02", "2026-09-10")', "G3"),
    ("M4 the positive window starts at t+6", D + "rn_build.py",
     "p710 = next((e for e in soon if i + H_LO <= e[key] <= i + H_HI), None)",
     "p710 = next((e for e in soon if i + H_LO - 1 <= e[key] <= i + H_HI), None)", "G4"),
    ("M4b censoring forgets the detection gap", D + "rn_build.py",
     "if i + H_HI + MAXGAP > last:", "if i + H_HI > last:", "G4"),
    ("M5 matching ignores the caliper", D + "rn_lib.py",
     "and (exact is None or exact(c) == ex) and all(abs(c[k] - a[k]) <= CALIPER for k in MATCH_KEYS)]",
     "and (exact is None or exact(c) == ex)]", "G5"),
    ("M5b matching ignores the tool status", D + "rn_lib.py",
     "and (exact is None or exact(c) == ex) and all(", "and (exact is None or True) and all(", "G5"),
    ("M6 seal check skipped", D + "rn_eval.py", "    if not prereg_ok():", "    if False:", "G6"),
    ("M8 the candidate's RSI limit drifts to 31", D + "rn_lib.py",
     '"RSI30": lambda r: _lt(r.get("rsi"), 30),', '"RSI30": lambda r: _lt(r.get("rsi"), 31),', "G8"),
]


def run(fast=True):
    env = dict(ENV)
    if fast:
        env["R70_FAST"] = "1"
    else:
        env.pop("R70_FAST", None)
    p = subprocess.run([sys.executable, D + "test_rn.py"], capture_output=True, text=True, env=env, timeout=3600)
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
        if src.count(old) != 1:
            res.append([name, f"⛔ anchor count {src.count(old)}", "", "expected " + lock])
            continue
        try:
            open(path, "w", encoding="utf-8").write(src.replace(old, new))
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
        json.dump({"run": "2026-10-11", "harness": D + "rn_mutate.py", "result": out},
                  open(os.path.join(D, "data", "mutations.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
