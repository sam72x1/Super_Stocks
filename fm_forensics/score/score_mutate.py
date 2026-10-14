"""T-SCORE mutation round: each mutation must make `score_test.py --guards` fail (no crash). Restores the file in finally."""
import glob
import os
import subprocess
import sys

WT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
P = os.path.join(WT, "fm_forensics/score/score_test.py")
M = [
    ("m1 RSI full at 33", "RSI_FULL, RSI_ZERO = 27.0, 40.0", "RSI_FULL, RSI_ZERO = 33.0, 40.0"),
    ("m2 RSI zero at 50", "RSI_FULL, RSI_ZERO = 27.0, 40.0", "RSI_FULL, RSI_ZERO = 27.0, 50.0"),
    ("m3 hold full at 3", "HOLD_FULL = 5 ", "HOLD_FULL = 3 "),
    ("m4 test full at 10", "TEST_FULL = 15.0 ", "TEST_FULL = 10.0 "),
    ("m5 no give-back credit in stage 2", "            back = _clip(1.0 - vs / bounce)", "            back = 0.0"),
    ("m6 zone without decay", "c[\"ZONE\"] = 1.0 if vs <= ZONE_TOP else _clip(1.0 - (vs - ZONE_TOP) / ZONE_DECAY)",
     "c[\"ZONE\"] = 1.0 if vs <= ZONE_TOP else 0.0"),
    ("m7 hold-in-zone before the retest", "_clip(int(pc[\"held\"]) / HOLDZ_FULL) if st >= 3 else 0.0",
     "_clip(int(pc[\"held\"]) / HOLDZ_FULL) if st >= 2 else 0.0"),
    ("m8 unreclaimed sweep gets full credit", "            c[\"SWEEP\"] = 0.5", "            c[\"SWEEP\"] = 1.0"),
    ("m9 unknown counted as zero", "    den = sum(w[k] for k, v in c.items() if v is not None)", "    den = sum(w.values())"),
    ("m10 direction reversed", "    return {\"S\": a + (a - b), \"S_L\": a, \"D\": a - b}", "    return {\"S\": a - (a - b), \"S_L\": a, \"D\": a - b}"),
    ("m11 scan RSI ≤ 33", "(raw[\"rsi\"] < SCAN_RSI and", "(raw[\"rsi\"] <= SCAN_RSI and"),
    ("m12 ties count as wins", "1.0 if e > x else (0.5 if e == x else 0.0)", "1.0 if e >= x else 0.0"),
    ("m13 bootstrap by unit", "        by.setdefault(u[\"sym\"], []).append(u)\n    syms = sorted(by)\n    rng = random.Random(seed)\n    vals = []",
     "        by.setdefault(id(u), []).append(u)\n    syms = sorted(by)\n    rng = random.Random(seed)\n    vals = []"),
    ("m14 MDE factor 2.0", "    return round(2.8 * math.sqrt((n_e + n_c + 1) / (12.0 * n_e * n_c)), 4)",
     "    return round(2.0 * math.sqrt((n_e + n_c + 1) / (12.0 * n_e * n_c)), 4)"),
    ("m15 AUC at ½ counts as separation", "    if lo is None or lo <= 0.5:", "    if lo is None or lo < 0.5:"),
    ("m16 identity cap off", "        return \"A0\" if p == \"A\" else p", "        return p"),
    ("m17 layer 3 dropped", "def weights(ledger=LEDGER, matrix=MATRIX, tags=TAGS, layers=(1, 2, 3)):",
     "def weights(ledger=LEDGER, matrix=MATRIX, tags=TAGS, layers=(1, 2)):"),
    ("m18 merged gate accepts absence", "    got = hashlib.sha256(blob).hexdigest() if blob is not None else None\n    if got != PREREG_SHA256:\n        print(f\"⛔ the pinned contract is not on origin/main",
     "    got = hashlib.sha256(blob).hexdigest() if blob is not None else PREREG_SHA256\n    if got != PREREG_SHA256:\n        print(f\"⛔ the pinned contract is not on origin/main"),
    ("m19 split guard off", "    bad = X.split_unadjusted(rows, splits, lo, rows[i][0])", "    bad = []"),
    ("m20 look-ahead in the readings", "    d = df.iloc[: i + 1]\n    out = {\"t\"", "    d = df\n    out = {\"t\""),
    ("m21 history floor off", "    if i - DIR_LAG < MIN_BARS:", "    if False:"),
    ("m22 «باقي» measured to 40", "باقي {rsi - RSI_FULL:.1f} نقطة", "باقي {RSI_ZERO - rsi:.1f} نقطة"),
]
orig = open(P, encoding="utf-8").read()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
res = []
try:
    for name, a, b in M:
        if orig.count(a) != 1:
            print("⛔ anchor count", orig.count(a), name)
            res.append(False)
            continue
        open(P, "w", encoding="utf-8").write(orig.replace(a, b, 1))
        for f in glob.glob(os.path.join(WT, "fm_forensics/score/__pycache__/*")):
            os.remove(f)
        r = subprocess.run([sys.executable, "-B", P, "--guards"], cwd=WT, capture_output=True, text=True, timeout=900, env=env)
        fails = [ln[2:].split("  [")[0][:60] for ln in r.stdout.splitlines() if ln.startswith("❌")]
        tb = "Traceback" in r.stdout + r.stderr
        ok = r.returncode != 0 and bool(fails) and not tb
        res.append(ok)
        print(("FELL " if ok else "SURVIVED/CRASH ") + name, "rc", r.returncode, "tb", tb, fails[:3])
finally:
    open(P, "w", encoding="utf-8").write(orig)
r = subprocess.run([sys.executable, "-B", P, "--guards"], cwd=WT, capture_output=True, text=True, env=env)
print(f"fell {sum(res)}/{len(M)} · restored rc", r.returncode)
