"""ALERTS70 mutation round — every guard of test_a70.py must fall on its own mutation, cleanly (no crash).
Code mutations edit one line and restore it; data mutations edit a temporary copy of data/ (A70_DATA), never the
committed files. M8 corrupts one committed output for the full run and restores it. Run from the repo root:
    GIT_ALLOW_PROTOCOL=file python3 faisal_engine/alerts70/a70_mutate.py
"""
import csv
import gzip
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

D = "faisal_engine/alerts70/"
ENV = dict(os.environ, GIT_ALLOW_PROTOCOL="file", GIT_TERMINAL_PROMPT="0")
CODE = [
    ("M1 volume median reads the next bar", D + "a70_build.py",
     "med = float(np.median(v[max(0, i - 20):i])) if i >= 5 else None",
     "med = float(np.median(v[max(0, i - 20):i + 2])) if i >= 5 else None", "G1"),
    ("M3 after-hours cut at 17:00", D + "a70_build.py",
     'row["shift"] = int(_et.hour >= 16)', 'row["shift"] = int(_et.hour >= 17)', "G3"),
    ("M4 launch day counted as before the start", D + "a70_build.py",
     '    if a < e["L_i"]:', '    if a <= e["L_i"]:', "G4"),
    ("M5 control drawn from any price bucket", D + "a70_eval.py",
     'cand = [c for c in pool if c["sym"] not in used and bucket(num(c["px"])) == bk]',
     'cand = [c for c in pool if c["sym"] not in used]', "G5"),
    ("M6 GIT_ENV without the offline protocol", D + "a70_extract.py",
     'GIT_ENV = dict(os.environ, GIT_ALLOW_PROTOCOL="file", GIT_TERMINAL_PROMPT="0")',
     'GIT_ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0")', "G6"),
    ("M6b every history blob streamed (no local filter)", D + "a70_extract.py",
     "cs = [c for c in allc if c[2] in have]", "cs = list(allc)", "G6"),
    ("M7 seal check skipped", D + "a70_eval.py", "    if not prereg_ok():", "    if False:", "G7"),
]


def _first(rows, pred):
    return next(i for i, r in enumerate(rows) if pred(r))


def flip_label(rows):
    i = _first(rows, lambda r: r["decision_t"] and r["f10"] in ("POS", "NEG"))
    rows[i]["f10"] = "NEG" if rows[i]["f10"] == "POS" else "POS"


def unshift(rows):
    i = _first(rows, lambda r: r["decision_t"] and r["shift"] == "1")
    rows[i]["shift"] = "0"


DATA_MUT = [("M2 one alert row carries another session's label", flip_label, "G2"),
            ("M3b one after-hours alert stamped with its own date", unshift, "G3")]


def run(extra_env=None, fast=True):
    env = dict(ENV, **(extra_env or {}))
    if fast:
        env["R70_FAST"] = "1"
    else:
        env.pop("R70_FAST", None)
    p = subprocess.run([sys.executable, D + "test_a70.py"], capture_output=True, text=True, env=env, timeout=3600)
    fell = [ln.split()[1] for ln in p.stdout.splitlines() if ln.startswith("❌")]
    return p.returncode, fell, ("Traceback" in p.stdout + p.stderr)


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    res = []
    keep = {f: _sha(os.path.join(D, "data", f)) for f in sorted(os.listdir(os.path.join(D, "data")))}
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
    for name, fn, lock in DATA_MUT:
        tmp = tempfile.mkdtemp()
        try:
            for f in os.listdir(os.path.join(D, "data")):
                shutil.copy(os.path.join(D, "data", f), tmp)
            p = os.path.join(tmp, "alerts.csv.gz")
            with gzip.open(p, "rt", encoding="utf-8") as fh:
                rd = csv.DictReader(fh)
                fields, rows = rd.fieldnames, list(rd)
            fn(rows)
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
            with gzip.GzipFile(p, "wb", mtime=0) as fh:
                fh.write(buf.getvalue().encode("utf-8"))
            rc, fell, crash = run({"A70_DATA": tmp})
            res.append([name, "fell: " + ",".join(fell), "crash" if crash else "clean", "expected " + lock])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    # M8: a committed output corrupted → the full run's regeneration check (G8) must fall
    out = os.path.join(D, "data", "side.csv.gz")
    raw = open(out, "rb").read()
    try:
        open(out, "wb").write(raw + b"\0")
        rc, fell, crash = run(fast=False)
        res.append(["M8 corrupted output (full run)", "fell: " + ",".join(fell), "crash" if crash else "clean",
                    "expected G8"])
    finally:
        open(out, "wb").write(raw)
    shutil.rmtree(D + "__pycache__", ignore_errors=True)
    after = {f: _sha(os.path.join(D, "data", f)) for f in sorted(os.listdir(os.path.join(D, "data")))}
    res.append(["data/ unchanged after the round", str(after == keep), "", ""])
    for r in res:
        print(r)
    return res


if __name__ == "__main__":
    out = main()
    if "--write" in sys.argv:
        json.dump({"run": "2026-10-11", "harness": D + "a70_mutate.py", "result": out},
                  open(os.path.join(D, "data", "mutations.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
