"""Mutation round of the historical-4H guards — every guard of test_h4.py must fall on its own mutation, cleanly.
Run from the repo root:  python3 faisal_engine/readynow/condition_atlas/h4_mutate.py [--write]
Most mutations run with H4_FAST=1 (the slow end-to-end H4G1 skipped); the renderer mutation runs the full round.
Every file is restored in a finally block and a clean baseline is run last. Bytecode is neither written nor trusted:
a same-length mutation restored within the same second leaves a .pyc whose mtime and size still match the source, and
the next run would import the mutated code (seen in the first round: the baseline failed on a stale h4_report.pyc).
"""
import glob
import json
import os
import subprocess
import sys

C = "faisal_engine/readynow/condition_atlas/"
A, R = C + "h4_audit.py", C + "h4_report.py"
CODE = [
    ("HM1 in-event decisions are not excluded", A, "        if o <= k <= end:", "        if False:", "H4G4", True),
    ("HM2 an upload bound becomes the decision date", A,
     '    out["basis"] = "UPLOAD_BOUND_ONLY" if upper else ("AXIS_LOWER_BOUND_ONLY" if lower else "UNDATED")',
     '    out["basis"] = "UPLOAD_BOUND_ONLY" if upper else ("AXIS_LOWER_BOUND_ONLY" if lower else "UNDATED")\n'
     '    out["decision"] = upper', "H4G3", True),
    ("HM3 an ambiguous price anchor dates a chart", A, 'return ("unique" if len(hits) == 1 else',
     'return ("unique" if len(hits) >= 1 else', "H4G5", True),
    ("HM4 any bar step builds any grid", A, "            if m < edge < m + step:", "            if False:", "H4G6", True),
    ("HM5 the verdict is hard-coded", A, "    ok = pos_ohlc > 0 and neg_ohlc > 0 and len(ev_ohlc) >= 2",
     "    ok = False", "H4G9", True),
    ("HM6 the verbatim check is disabled", A, "                if norm(ex) not in hay:", "                if False:",
     "H4G2", True),
    ("HM7 the findings report claims the test was performed", R,
     '"**The formal four-hour test could not be performed.** The repository',
     '"**The formal four-hour test was performed.** The repository', "H4G1,H4G12", False),
    ("HM8 a fwd/ path becomes a source", A, '    "fm_bars": "fm_forensics/data/bars_2026-10-08.json.gz",',
     '    "fm_bars": "fm_forensics/data/bars_2026-10-08.json.gz", "fwd": "faisal_engine/readynow/fwd/x.json",',
     "H4G7", True),
    ("HM9 a network library is imported", A, "import bisect\n", "import bisect\nimport urllib.request\n", "H4G11", True),
    ("HM10 a third-party caption is filed as Faisal's rule", A, '("IMG_0151", "الشرط خالي من القروبات"),',
     '("EDU_20260827_dki_group_candle", "شمعة قروب الشكوى لله"),', "H4G10", True),
    ("HM11 the T−10…T−7 window starts at T−6", A, 'st = "T7_10" if 7 <= n <= 10', 'st = "T7_10" if 6 <= n <= 10',
     "H4G4", True),
    ("HM12 the intraday-only threshold drops to +60%", A, ">= 0.70 and not any", ">= 0.60 and not any", "H4G15", True),
    ("HM13 a cited grid number is not in its source", A, '("hubc_result", "0.0269",', '("hubc_result", "0.0296",',
     "H4G13", True),
    ("HM14 the file-date example misstates the capture day", R, "its EXIF capture date is 2026-08-06",
     "its EXIF capture date is 2026-08-05", "H4G14", True),
    ("HM15 a sealed hash drifts", C + "ca_reconcile.py", 'PREFIX_SHA256 = "6a64', 'PREFIX_SHA256 = "7a64', "H4G8", True),
]


def purge(path):
    stem = os.path.splitext(os.path.basename(path))[0]
    for f in glob.glob(os.path.join(os.path.dirname(path), "__pycache__", stem + ".*.pyc")):
        os.remove(f)


def run(fast):
    env = dict(os.environ, H4_FAST="1" if fast else "0", PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run([sys.executable, "-B", C + "test_h4.py"], capture_output=True, text=True, env=env, timeout=3600)
    fell = [ln.split()[1] for ln in p.stdout.splitlines() if ln.startswith("❌")]
    return p.returncode, fell, ("Traceback" in p.stdout + p.stderr)


def main():
    res = []
    for name, path, old, new, lock, fast in CODE:
        src = open(path, encoding="utf-8").read()
        if src.count(old) != 1:
            res.append([name, f"⛔ anchor count {src.count(old)}", "", "expected " + lock])
            continue
        try:
            open(path, "w", encoding="utf-8").write(src.replace(old, new, 1))
            purge(path)
            rc, fell, crash = run(fast)
        finally:
            open(path, "w", encoding="utf-8").write(src)
            purge(path)
        ok = rc != 0 and fell == lock.split(",") and not crash
        res.append([name, "fell cleanly" if ok else "⛔", ",".join(fell) + (" (crash)" if crash else ""),
                    "expected " + lock])
    rc, fell, crash = run(False)
    res.append(["baseline after restore", "clean" if rc == 0 and not fell and not crash else "⛔", ",".join(fell), ""])
    for r in res:
        print(" | ".join(str(x) for x in r))
    if "--write" in sys.argv:
        json.dump(res, open(C + "data/h4_mutations.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if all(r[1] in ("fell cleanly", "clean") for r in res) else 1


if __name__ == "__main__":
    sys.exit(main())
