"""READYNOW reconciliation mutation round — every guard of test_recon.py must fall on its own mutation, cleanly.
Run from the repo root:  GIT_ALLOW_PROTOCOL=file python3 faisal_engine/readynow/recon/recon_mutate.py [--write]
(R70_FAST=1 inside the round: the 10-minute ROOM rerun of RC7 is skipped; no mutation targets it.)
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

C = "faisal_engine/readynow/recon/"
ENV = dict(os.environ, GIT_ALLOW_PROTOCOL="file", GIT_TERMINAL_PROMPT="0", R70_FAST="1")
CODE = [
    ("RM1 the detection label censors with MAXGAP", C + "rn_recon.py",
     "    if i + B.H_HI > last:\n", "    if i + B.H_HI + B.MAXGAP > last:\n", "RC1"),
    ("RM2 the anchor window shifts one session earlier", C + "rn_recon.py",
     "days = [cal[g] for g in range(g0 - 10, g0 - 6)]", "days = [cal[g] for g in range(g0 - 11, g0 - 7)]", "RC3"),
    ("RM3 the symbol exclusion is not recorded", C + "rn_recon.py",
     "        if sym in K.EXCLUDE:\n            reasons.append", "        if False:\n            reasons.append", "RC4"),
    ("RM4 ROOM discovery reads the holdout", C + "rn_room_dev.py",
     'DEV = K.WINDOWS["development"]', 'DEV = K.WINDOWS["holdout"]', "RC5"),
    ("RM5 ROOM swing highs see two future sessions", C + "rn_room_dev.py",
     '    h = df["High"].values.astype(float)\n', '    h = b["h"][lo:i + 3].astype(float)\n', "RC6"),
    ("RM6 GAP_BIG threshold drifts to 25%", C + "rn_gap_dev.py",
     'r["g_big"] >= 30}', 'r["g_big"] >= 25}', "RC7"),
    ("RM7 the event period starts at D1 again (ignores an earlier +70% close)", C + "rn_recon.py",
     'start = min(e["D1"], e["x70"]) if e.get("x70") is not None else e["D1"]', 'start = e["D1"]', "RC1"),
]


def run():
    p = subprocess.run([sys.executable, C + "test_recon.py"], capture_output=True, text=True, env=ENV, timeout=3600)
    fell = [ln.split()[1] for ln in p.stdout.splitlines() if ln.startswith("❌")]
    return p.returncode, fell, ("Traceback" in p.stdout + p.stderr)


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    res = []
    dd = C + "data"
    keep = {f: _sha(os.path.join(dd, f)) for f in sorted(os.listdir(dd))}
    for name, path, old, new, lock in CODE:
        src = open(path, encoding="utf-8").read()
        if src.count(old) != 1:
            res.append([name, f"⛔ anchor count {src.count(old)}", "", "expected " + lock])
            continue
        try:
            open(path, "w", encoding="utf-8").write(src.replace(old, new))
            shutil.rmtree(C + "__pycache__", ignore_errors=True)
            rc, fell, crash = run()
            res.append([name, "fell: " + ",".join(fell), "crash" if crash else "clean", "expected " + lock])
        finally:
            open(path, "w", encoding="utf-8").write(src)
    shutil.rmtree(C + "__pycache__", ignore_errors=True)
    after = {f: _sha(os.path.join(dd, f)) for f in sorted(os.listdir(dd))}
    res.append(["recon/data unchanged after the round", str(after == keep), "", ""])
    for r in res:
        print(r)
    return res


if __name__ == "__main__":
    out = main()
    if "--write" in sys.argv:
        json.dump({"run": "2026-10-11", "harness": C + "recon_mutate.py", "result": out},
                  open(os.path.join(C, "data", "mutations.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
