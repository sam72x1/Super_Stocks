"""T-HEAT mutation round: each mutation must make `heat_test.py --guards` fail (no crash). Restores the file in finally."""
import glob
import os
import subprocess
import sys

WT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
P = os.path.join(WT, "fm_forensics/heat/heat_test.py")
M = [
 ("m1 K_GAP 2→1", "K_GAP = 2 ", "K_GAP = 1 "),
 ("m2 governing leads start at 1", "GOV_LEADS = tuple(range(K_GAP, K_GAP + W_GOV))", "GOV_LEADS = tuple(range(1, 1 + W_GOV))"),
 ("m3 tri_or uses and", "    if a is True or b is True:\n        return True", "    if a is True and b is True:\n        return True"),
 ("m4 onset does not walk back", "        o = j\n    return None, \"UNKNOWN\"", "        return o, \"OK\"\n    return None, \"UNKNOWN\""),
 ("m5 window needs every day", "        out[tr] = True if fired else", "        out[tr] = True if len(fired) == len(vals) else"),
 ("m6 forward reached inverted", "\"reached\": st[\"realized_idx\"] is not None", "\"reached\": st[\"realized_idx\"] is None"),
 ("m7 MDE rule off", "    if mde_rule and (b[\"design_mde80\"] is None", "    if False and (b[\"design_mde80\"] is None"),
 ("m8 identity cap off", "        return \"A0\" if p == \"A\" else p", "        return p"),
 ("m9 RET5 label", "LAB_VX, LAB_R5 = \"≥3\", \">+20%\"", "LAB_VX, LAB_R5 = \"≥3\", \"-20..+20%\""),
 ("m10 split guard off", "    bad = X.split_unadjusted(hist, splits, hist[lo_i][0], hist[hi_i][0]) if hi_i > lo_i else []", "    bad = []"),
 ("m11 run rule uses JUMP", "        if run_min > 0 and top / run_min >= X.RUN:\n            return j, unknown", "        if run_min > 0 and top / run_min >= X.JUMP:\n            return j, unknown"),
 ("m12 window_clean ignores unknown", "    return None if unk else True\n\n\ndef onset", "    return True\n\n\ndef onset"),
 ("m13 MDE_MAX 0.20", "MDE_MAX = 0.25 ", "MDE_MAX = 0.20 "),
 ("m14 final = strongest", "def final_verdict(per_anchor):\n    return min(", "def final_verdict(per_anchor):\n    return max("),
 ("m15 traits read A−1 (gap leak)", "        days[ld] = {\"VOLX3\": None, \"RET5\": None} if bad else day_traits(hist, k_arch - ld)", "        days[ld] = {\"VOLX3\": None, \"RET5\": None} if bad else day_traits(hist, k_arch - ld + 1)"),
 ("m17 merged gate passes anything", "    if got != PREREG_SHA256:\n        print(f\"⛔ the pinned contract is not on origin/main", "    if False:\n        print(f\"⛔ the pinned contract is not on origin/main"),
 ("m18 merged gate accepts absence", "    got = hashlib.sha256(blob).hexdigest() if blob is not None else None", "    got = hashlib.sha256(blob).hexdigest() if blob is not None else PREREG_SHA256"),
 ("m16 intersect = or", "    out[\"INTERSECT\"] = tri_and(out[\"VOLX3\"], out[\"RET5\"])", "    out[\"INTERSECT\"] = tri_or(out[\"VOLX3\"], out[\"RET5\"])"),
]
orig = open(P, encoding="utf-8").read()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
try:
    for name, a, b in M:
        if orig.count(a) != 1:
            print("⛔ anchor count", orig.count(a), name)
            continue
        open(P, "w", encoding="utf-8").write(orig.replace(a, b, 1))
        for f in glob.glob(os.path.join(WT, "fm_forensics/heat/__pycache__/*")):
            os.remove(f)
        r = subprocess.run([sys.executable, "-B", P, "--guards"], cwd=WT, capture_output=True, text=True, timeout=600, env=env)
        fails = [ln[2:].split("  [")[0] for ln in r.stdout.splitlines() if ln.startswith("❌")]
        tb = "Traceback" in r.stdout + r.stderr
        print(("FELL " if (r.returncode != 0 and fails and not tb) else "SURVIVED/CRASH ") + name, "rc", r.returncode, "tb", tb, fails[:4])
finally:
    open(P, "w", encoding="utf-8").write(orig)
r = subprocess.run([sys.executable, "-B", P, "--guards"], cwd=WT, capture_output=True, text=True, env=env)
print("restored rc", r.returncode)
