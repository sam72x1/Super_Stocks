"""READY NOW audit mutation round — every guard of test_audit.py must fall on its own mutation, cleanly.
Run from the repo root:  GIT_ALLOW_PROTOCOL=file python3 faisal_engine/readynow/audit/audit_mutate.py [--write]
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

D = "faisal_engine/readynow/"
A = D + "audit/"
ENV = dict(os.environ, GIT_ALLOW_PROTOCOL="file", GIT_TERMINAL_PROMPT="0")
ENV.pop("R70_FAST", None)
CODE = [
    ("AM1 the distance limit drifts to 14.9%", D + "rn_lib.py",
     '"NEAR15": lambda r: _between(r.get("dist"), -1e9, 15),', '"NEAR15": lambda r: _between(r.get("dist"), -1e9, 14.9),',
     "A1"),
    ("AM2 seal check skipped", A + "rn_app_eval.py", "    if not prereg_ok():", "    if False:", "A2"),
    ("AM3 one transcribed app state altered (MSGY stability)", A + "rn_chip_parity.py",
     '"app": {"STAB2": True, "NEAR15": False, "BOUNCE": True, "BELOW": True, "RETEST": True, "MOMENTUM": True}},',
     '"app": {"STAB2": False, "NEAR15": False, "BOUNCE": True, "BELOW": True, "RETEST": True, "MOMENTUM": True}},', "A3"),
    ("AM4 the seed window shifts one session earlier", A + "rn_seed_audit.py",
     "for off in range(-10, -6):", "for off in range(-11, -7):", "A4"),
    ("AM5 the evaluator uses fewer resamples", A + "rn_app_eval.py", "REPS = 2000", "REPS = 1000", "A5"),
]


def run():
    p = subprocess.run([sys.executable, A + "test_audit.py"], capture_output=True, text=True, env=ENV, timeout=3600)
    fell = [ln.split()[1] for ln in p.stdout.splitlines() if ln.startswith("❌")]
    return p.returncode, fell, ("Traceback" in p.stdout + p.stderr)


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    res = []
    dd = A + "data"
    keep = {f: _sha(os.path.join(dd, f)) for f in sorted(os.listdir(dd))}
    for name, path, old, new, lock in CODE:
        src = open(path, encoding="utf-8").read()
        if src.count(old) != 1:
            res.append([name, f"⛔ anchor count {src.count(old)}", "", "expected " + lock])
            continue
        try:
            open(path, "w", encoding="utf-8").write(src.replace(old, new))
            for c in (D + "__pycache__", A + "__pycache__"):
                shutil.rmtree(c, ignore_errors=True)
            rc, fell, crash = run()
            res.append([name, "fell: " + ",".join(fell), "crash" if crash else "clean", "expected " + lock])
        finally:
            open(path, "w", encoding="utf-8").write(src)
    for c in (D + "__pycache__", A + "__pycache__"):
        shutil.rmtree(c, ignore_errors=True)
    after = {f: _sha(os.path.join(dd, f)) for f in sorted(os.listdir(dd))}
    res.append(["audit/data unchanged after the round", str(after == keep), "", ""])
    for r in res:
        print(r)
    return res


if __name__ == "__main__":
    out = main()
    if "--write" in sys.argv:
        json.dump({"run": "2026-10-11", "harness": A + "audit_mutate.py", "result": out},
                  open(os.path.join(A, "data", "mutations.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
