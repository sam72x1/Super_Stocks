"""Mutation round of the condition-atlas guards — every guard of test_ca.py must fall on its own mutation, cleanly.
Run from the repo root:  python3 faisal_engine/readynow/condition_atlas/ca_mutate.py [--write]
(CA_FAST=1 inside the round: the slow regeneration CA2 is skipped; no mutation targets it.)
A change to a feature definition in ca_build.py is caught twice by design: by its synthetic check (CA4) and by CA1,
which recomputes stored features on truncated bars and so sees any drift between the code and the stored data.
"""
import json
import os
import subprocess
import sys

C = "faisal_engine/readynow/condition_atlas/"
ENV = dict(os.environ, CA_FAST="1")
CODE = [
    ("CM1 the 3-session volume maximum reads the next session", C + "ca_build.py",
     '    out["b_vmax3"] = pd.Series(v1x).rolling(3, min_periods=1).max().to_numpy()',
     '    out["b_vmax3"] = pd.Series(v1x).rolling(3, min_periods=1).max().shift(-1).to_numpy()', "CA1"),
    ("CM2 the red hammer is read on a green candle", C + "ca_build.py",
     '    out["k_hammer_red"] = int(out["k_hammer"] and c[i] < o[i])',
     '    out["k_hammer_red"] = int(out["k_hammer"] and c[i] > o[i])', "CA1,CA4"),
    ("CM3 the harami body ratio is tightened to 0.3", C + "ca_build.py",
     "and c[i] <= o[i - 1] and body <= 0.6 * pb)", "and c[i] <= o[i - 1] and body <= 0.3 * pb)", "CA1,CA4"),
    ("CM4 the development test half runs into 2026", C + "ca_dev.py",
     'TEST = ("2025-10-01", "2025-12-31")', 'TEST = ("2025-10-01", "2026-01-31")', "CA5"),
    ("CM5 the pinned protocol hash drifts", C + "ca_final.py", 'PROTOCOL_SHA256 = "4', 'PROTOCOL_SHA256 = "5', "CA6"),
    ("CM6 the classes ignore invalidation", C + "ca_dev.py",
     "        ok = [r for r in rs if not L.invalidated(r)]", "        ok = list(rs)", "CA7"),
    ("CM7 the app's support weight is changed to 15", C + "ca_lib.py",
     '    ("support clear, break failed (12)", 12.0,', '    ("support clear, break failed (12)", 15.0,', "CA8"),
    ("CM8 an atlas entry names a flag that does not exist", C + "ca_atlas.py",
     'flag="B08_SWEEP"', 'flag="B08_SWEEPX"', "CA3"),
    ("CM9 the inventory document drifts from its generator", C + "ca_docs.py",
     '"- The Phase 6 ledger and every log from 2026-10-08 on are prospective and excluded by instruction."',
     '"- The Phase 6 ledger is prospective."', "CA9"),
    ("CM10 the verdict ignores criterion V2", C + "ca_verdict.py",
     '    v2 = _pos(_lo(P["W_k"]["DROP_k"])) and _pos(_lo(P["W_k"]["VOLAT_k"]))', "    v2 = True", "CA10"),
    ("CM11 a result report drifts from its generator", C + "ca_report.py",
     "- **Composite:** the third-party rule", "- **Composite (edited):** the third-party rule", "CA11"),
    ("CM12 the reconciliation addendum drifts from its generator", C + "ca_reconcile.py",
     "f'- **Fine order not supported:** READY_1", "f'- **Fine order (edited):** READY_1", "CA12"),
    ("CM13 §0 of the addendum is edited after the run", C + "RECONCILIATION_ADDENDUM.md",
     "(written 2026-10-11 23:50 UTC, before `ca_reconcile.py` was run)",
     "(written 2026-10-11 23:50 UTC, after `ca_reconcile.py` was run)", "CA12"),
]


def run():
    p = subprocess.run([sys.executable, C + "test_ca.py"], capture_output=True, text=True, env=ENV, timeout=3600)
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
        ok = rc != 0 and fell == lock.split(",") and not crash
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
