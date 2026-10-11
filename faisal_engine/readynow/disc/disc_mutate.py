"""READY NOW discovery mutation round — every guard of test_disc.py must fall on its own mutation, cleanly.
Run from the repo root:  python3 faisal_engine/readynow/disc/disc_mutate.py [--write]
(DISC_FAST=1 inside the round: the slow regenerations DG7/DG8 are skipped; no mutation targets them.)
"""
import json
import os
import subprocess
import sys

C = "faisal_engine/readynow/disc/"
ENV = dict(os.environ, DISC_FAST="1")
CODE = [
    ("DM1 the +70% leg uses G 1.50 instead of 1.70", C + "rn_disc_build.py",
     "        q, g = e[\"x70\"], 1.70\n", "        q, g = e[\"x70\"], 1.50\n", "DG1"),
    ("DM2 POS710 starts one session earlier (t+6)", C + "rn_disc_build.py",
     "    p = next((e for e in soon if i + H_LO <= e[\"ON\"] <= i + H_HI), None)",
     "    p = next((e for e in soon if i + H_LO - 1 <= e[\"ON\"] <= i + H_HI), None)", "DG2"),
    ("DM3 IN_EVENT ends at the peak (ignores a later detection)", C + "rn_disc_build.py",
     "        if e[\"ON\"] <= i <= max(e[\"P\"], e[\"D1\"], e[\"Q\"]):", "        if e[\"ON\"] <= i <= e[\"P\"]:", "DG2"),
    ("DM4 hl_count reads the next session's close", C + "rn_disc_build.py",
     "    out[\"hl_count\"] = hl\n",
     "    out[\"hl_count\"] = hl + int(b[\"c\"][min(i + 1, len(b[\"c\"]) - 1)] > c[i])\n", "DG3"),
    ("DM5 the v1x baseline shifts by one session", C + "rn_disc_cand.py",
     "    base = s.rolling(BASE[0] - BASE[1] + 1).median().shift(BASE[1])",
     "    base = s.rolling(BASE[0] - BASE[1] + 1).median().shift(BASE[1] - 1)", "DG4"),
    ("DM6 the candidate development run reads the holdout", C + "rn_disc_cand.py",
     '        res = {"mode": "dev", "development": run_window("development")[0]}',
     '        res = {"mode": "dev", "development": run_window("holdout")[0]}', "DG5"),
    ("DM7 the pinned protocol hash drifts", C + "rn_disc_model.py",
     'PROTOCOL_SHA256 = "a7', 'PROTOCOL_SHA256 = "b7', "DG5"),
    ("DM8 the burst threshold is hard-coded at 4", C + "rn_disc_cand.py",
     'SPIKE = float(R.S().CONFIG["VOL_SPIKE_MULT"])', "SPIKE = 4.0", "DG6"),
    ("DM9 the seed exclusion is dropped from the development rows", C + "rn_disc_dev.py",
     'if lo <= r["t"] <= hi and r["sym"] not in K.EXCLUDE and r.get("cond_ok") == "1":',
     'if lo <= r["t"] <= hi and r.get("cond_ok") == "1":', "DG6"),
    ("DM10 the verdict ignores criterion A3", C + "rn_disc_verdict.py",
     '    a3 = _gt(_lo(pooled["DROP_k"]["ci95"]), 0) and _gt(_lo(pooled["VOLAT_k"]["ci95"]), 0)',
     "    a3 = True", "DG9"),
]


def run():
    p = subprocess.run([sys.executable, C + "test_disc.py"], capture_output=True, text=True, env=ENV, timeout=3600)
    fell = [ln.split()[1] for ln in p.stdout.splitlines() if ln.startswith("❌")]
    return p.returncode, fell, ("Traceback" in p.stdout + p.stderr)


def main():
    res = []
    for name, path, old, new, lock in CODE:
        src = open(path, encoding="utf-8").read()
        if src.count(old) != 1:
            res.append([name, f"⛔ anchor count {src.count(old)}", "", "expected " + lock])
            continue
        try:
            open(path, "w", encoding="utf-8").write(src.replace(old, new, 1))
            rc, fell, crash = run()
        finally:
            open(path, "w", encoding="utf-8").write(src)
        ok = rc != 0 and fell == [lock] and not crash
        res.append([name, "fell cleanly" if ok else "⛔", ",".join(fell) + (" (crash)" if crash else ""),
                    "expected " + lock])
    rc, fell, crash = run()
    res.append(["baseline after restore", "clean" if rc == 0 and not fell and not crash else "⛔", ",".join(fell), ""])
    for r in res:
        print(" | ".join(str(x) for x in r))
    if "--write" in sys.argv:
        json.dump(res, open(C + "data/mutations.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return 0 if all(r[1] in ("fell cleanly", "clean") for r in res) else 1


if __name__ == "__main__":
    sys.exit(main())
