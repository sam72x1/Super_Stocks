"""T-ANCHOR-AGE mutation round: each mutation must make `anchor_age.py --guards` fail cleanly (no crash, the named guard
falls). Restores the file in finally. Bytecode is never written and the module's __pycache__ is cleared before each run
(stale-bytecode lesson).

  python3 fm_forensics/anchor_age/anchor_mutate.py [worktree]     exit 0 only if every mutation falls cleanly
"""
import glob
import os
import subprocess
import sys

WT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
P = os.path.join(WT, "fm_forensics/anchor_age/anchor_age.py")
M = [
    ("m1 bin 3-8 widened to 3-9", '(3, 8, "3-8"), (9, 15, "9-15")', '(3, 9, "3-8"), (10, 15, "9-15")', "AG1"),
    ("m2 far multiplier 1.10", "STEP, N_TR, FAR_MULT, RECLAIM = 0.03, 3, 1.05, 0.995", "STEP, N_TR, FAR_MULT, RECLAIM = 0.03, 3, 1.10, 0.995", "AG2"),
    ("m3 reclaim 0.99", "STEP, N_TR, FAR_MULT, RECLAIM = 0.03, 3, 1.05, 0.995", "STEP, N_TR, FAR_MULT, RECLAIM = 0.03, 3, 1.05, 0.99", "AG2"),
    ("m4 step 2.5 %", "STEP, N_TR, FAR_MULT, RECLAIM = 0.03, 3, 1.05, 0.995", "STEP, N_TR, FAR_MULT, RECLAIM = 0.025, 3, 1.05, 0.995", "AG2"),
    ("m5 stop at the anchor is open", "    if stop and price <= stop:\n        return \"stop\"", "    if stop and price < stop:\n        return \"stop\"", "AG2"),
    ("m6 far before reclaim", "    if price < pivot * RECLAIM:\n        return \"reclaim\"\n    if price > hi * FAR_MULT:\n        return \"far\"",
     "    if price > hi * FAR_MULT:\n        return \"far\"\n    if False:\n        return \"reclaim\"", "AG2"),
    ("m7 k tolerance open at 3 %", "    if abs(k - 1.0) <= K_OK + 1e-12:", "    if abs(k - 1.0) <= K_OK:", "AG3"),
    ("m8 split threshold open", "    if abs(math.log(k)) >= K_SPLIT:", "    if abs(math.log(k)) > K_SPLIT:", "AG3"),
    ("m9 stop reason read as far", '    if "كسر الوقف" in r:\n        return "stop"', '    if False:\n        return "stop"', "AG4"),
    ("m10 oldest touch instead of latest", "    for j in range(n - 1, max(-1, n - 1 - TOUCH_LOOK), -1):",
     "    for j in range(max(0, n - TOUCH_LOOK), n):", "AG5"),
    ("m11 median by mean", 'round(statistics.median(xs), 2)', 'round(statistics.mean(xs), 2)', "AG6"),
    ("m12 decision session reads the open session", "    k = bisect.bisect_right(closes_utc, t) - 1", "    k = bisect.bisect_right(closes_utc, t)", "AG7"),
    ("m13 dropped below 20 not 25", "    elif a < 25:", "    elif a < 20:", "AG9"),
    ("m14 defect from 40 %", "    elif a >= 50 and (b_med or 0) >= 5 and (c_share or 0) >= 25:",
     "    elif a >= 40 and (b_med or 0) >= 5 and (c_share or 0) >= 25:", "AG9"),
    ("m15 flips from 20 %", "    elif a >= 50 and (b_med or 0) >= 5 and (c_share or 0) >= 25:",
     "    elif a >= 50 and (b_med or 0) >= 5 and (c_share or 0) >= 20:", "AG9"),
    ("m16 (b) by the largest bin median", '    b_med = pooled["median"] if pooled else None',
     '    b_med = max((v or {}).get("median") or 0 for v in r2.get("gaps_build_anchor", {}).values())', "AG10"),
    ("m17 share over the known only", '"pct": round(100 * sum(x == what for x in xs) / len(xs), 1) if xs else None}',
     '"pct": round(100 * sum(x == what for x in xs) / max(1, sum(x != "x" for x in xs)), 1) if xs else None}', "AG11"),
    ("m18 head anywhere in the document", '    head = t.split("## ⓪")[0] if "## ⓪" in t else ""', "    head = t", "AG13"),
    ("m19 verdict words not checked", '"{v[\'c_flip_share_pct\']}%", VERDICT_AR[v["verdict"]]]', '"{v[\'c_flip_share_pct\']}%"]', "AG13"),
    ("m20 m5 over six bars", '"m5": float(lows[-5:].min())', '"m5": float(lows[-6:].min())', "AG14"),
    ("m21 bars after s read", "    x = df[df.index <= s]", "    x = df", "AG14"),
    ("m22 thirty-bar floor dropped", "    if len(x) < MIN_BARS:\n        return None", "    if len(x) < 2:\n        return None", "AG14"),
    ("m23 axis open", "AXIS_CLOSED = True", "AXIS_CLOSED = False", "AG15"),
    ("m24 any value reopens", 'return AXIS_CLOSED and (os.environ.get(REOPEN_ENV) or "").strip() != "1"',
     'return AXIS_CLOSED and not (os.environ.get(REOPEN_ENV) or "").strip()', "AG15"),
    ("m25 closed exit code 0", "CLOSED_RC = 8 ", "CLOSED_RC = 0 ", "AG15"),
]


def run():
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    for f in glob.glob(os.path.join(os.path.dirname(P), "__pycache__", "anchor_age*.pyc")):
        os.remove(f)
    p = subprocess.run([sys.executable, "-B", P, "--guards"], cwd=WT, capture_output=True, text=True, timeout=600, env=env)
    out = p.stdout + p.stderr
    return p.returncode, out, ("Traceback" in out)


def main():
    src = open(P, encoding="utf-8").read()
    rc0, out0, tb0 = run()
    if rc0 != 0 or tb0:
        print(f"⛔ الأصلُ لا يعبر: rc={rc0}\n{out0[-800:]}")
        return 2
    bad = []
    try:
        for name, old, new, guard in M:
            if src.count(old) != 1:
                print(f"⛔ {name}: المرساةُ موجودة {src.count(old)} مرّة")
                bad.append(name)
                continue
            open(P, "w", encoding="utf-8").write(src.replace(old, new, 1))
            rc, out, tb = run()
            fell = [ln[2:].split(" ")[0] for ln in out.splitlines() if ln.startswith("❌ AG")]
            ok = rc != 0 and not tb and guard in fell
            print(("✅ " if ok else "❌ ") + f"{name} ⟵ سقط {fell or '—'}" + (" · انهار" if tb else ""))
            if not ok:
                bad.append(name)
    finally:
        open(P, "w", encoding="utf-8").write(src)
    rc1, _, tb1 = run()
    print(f"{len(M) - len(bad)}/{len(M)} سقطت بقفلها · الأصلُ بعد الاستعادة rc={rc1}")
    return 0 if not bad and rc1 == 0 and not tb1 else 1


if __name__ == "__main__":
    sys.exit(main())
