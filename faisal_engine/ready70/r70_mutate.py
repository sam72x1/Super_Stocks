import subprocess, sys, os, shutil
D = "faisal_engine/ready70/"
MUT = [
 ("M1 look-ahead in features", D+"r70_build.py", 'c, h, l = b["c"][: i + 1], b["h"][: i + 1], b["l"][: i + 1]', 'c, h, l = b["c"][: i + 2], b["h"][: i + 2], b["l"][: i + 2]', "L1"),
 ("M2 label reads the bar before", D+"r70_build.py", "    run_min = c[i]\n", "    run_min = min(c[i], c[i - 1])\n", "L2"),
 ("M3 frame shorter than the window", D+"r70_build.py", "def fast_frame(b, i, tail=80):", "def fast_frame(b, i, tail=40):", "L3"),
 ("M4 identity 52w window", D+"r70_build.py", "hi = h[max(0, t - 251): t + 1].max()", "hi = h[max(0, t - 199): t + 1].max()", "L4"),
 ("M5 jump day off by one", D+"r70_build.py", 'return ("jump", i - k_max + 1, float(g1))', 'return ("jump", i - k_max, float(g1))', "L5"),
 ("M6 embargo shorter than H", D+"r70_eval.py", 'TEST_FROM, TEST_TO = "2026-01-16", "2026-09-24"', 'TEST_FROM, TEST_TO = "2026-01-08", "2026-09-24"', "L6"),
 ("M7 seal always accepted", D+"r70_eval.py", "    return hashlib.sha256(open(PREREG, \"rb\").read()).hexdigest() == PREREG_SHA256", "    return True", "L7"),
]
res = []
for name, path, old, new, lock in MUT:
    src = open(path, encoding="utf-8").read()
    if src.count(old) != 1:
        res.append((name, "⛔ anchor count %d" % src.count(old))); continue
    try:
        open(path, "w", encoding="utf-8").write(src.replace(old, new))
        for pc in ("faisal_engine/ready70/__pycache__",):
            shutil.rmtree(pc, ignore_errors=True)
        p = subprocess.run([sys.executable, D+"test_r70.py"], capture_output=True, text=True, env=dict(os.environ, R70_FAST="1"), timeout=1200)
        failed = [l for l in p.stdout.splitlines() if l.startswith("❌")]
        crashed = "Traceback" in p.stdout + p.stderr
        res.append((name, "rc=%d" % p.returncode, "fell:" + ",".join(l.split()[1] for l in failed), "crash" if crashed else "clean", "expected " + lock))
    finally:
        open(path, "w", encoding="utf-8").write(src)
# M8: corrupt an output → L8
inv = D + "data/inventory.json"; src = open(inv, "rb").read()
try:
    open(inv, "wb").write(src + b" ")
    p = subprocess.run([sys.executable, D+"test_r70.py"], capture_output=True, text=True, timeout=1800)
    failed = [l for l in p.stdout.splitlines() if l.startswith("❌")]
    res.append(("M8 corrupted output", "rc=%d" % p.returncode, "fell:" + ",".join(l.split()[1] for l in failed), "expected L8"))
finally:
    open(inv, "wb").write(src)
shutil.rmtree("faisal_engine/ready70/__pycache__", ignore_errors=True)
for r in res: print(r)
