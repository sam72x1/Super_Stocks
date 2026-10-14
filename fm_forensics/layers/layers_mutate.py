"""T-LAYERS mutation round: each mutation must make `layers_test.py --guards` fail cleanly (no crash). Restores the file in finally.
Bytecode is never written and the module's __pycache__ is cleared before each run (stale-bytecode lesson, same-length mutations)."""
import glob
import os
import subprocess
import sys

WT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
P = os.path.join(WT, "fm_forensics/layers/layers_test.py")
M = [
    ("m1 band floor 5 %", "SW_LO, SW_HI = 7.0, 13.0 ", "SW_LO, SW_HI = 5.0, 13.0 "),
    ("m2 band floor exclusive", "    if pc.get(\"branch\") != \"sweep\" or sp < SW_LO:", "    if pc.get(\"branch\") != \"sweep\" or sp <= SW_LO:"),
    ("m3 no upper bound", "    if sp > SW_HI:\n        return False, \"deep\"", "    if False:\n        return False, \"deep\""),
    ("m4 reclaim at the base counts", "    if not float(close) > float(pc[\"bottom\"]):", "    if not float(close) >= float(pc[\"bottom\"]):"),
    ("m5 every reclaim is a trigger", "        if cy.c23(y)[0]:\n            return {**out, \"status\": \"NOT_FIRST\"",
     "        if False:\n            return {**out, \"status\": \"NOT_FIRST\""),
    ("m6 no test rise needed", "    if int(pc.get(\"stage\") or 0) < 3:", "    if int(pc.get(\"stage\") or 0) < 0:"),
    ("m7 history floor off", "    if x + 1 < MIN_BARS:\n        return {\"status\": \"UNKNOWN\"", "    if False:\n        return {\"status\": \"UNKNOWN\""),
    ("m8 look-ahead in the cycle", "self.pc_fn(self.df.iloc[: x + 1], sweep=self.sweep)", "self.pc_fn(self.df, sweep=self.sweep)"),
    ("m9 cancellation inverted", "    return any(float(close[y]) < float(sweep_low)", "    return any(float(close[y]) > float(sweep_low)"),
    ("m10 VOL at 1× counts", "    return bool(f) and f.get(\"vol_x\") == \"≥3\"", "    return bool(f) and f.get(\"vol_x\") != \"<1\""),
    ("m11 VOL reads the day before", "    f = L.daily_feats(rows, x + 1, False)", "    f = L.daily_feats(rows, x, False)"),
    ("m12 NODE any sweep under the base", "    return float(sweep_low) <= floor + (k + 1) * width", "    return float(sweep_low) <= base"),
    ("m13 NODE no history floor", "    if s0 - a < NODE_MIN:\n        return False", "    if False:\n        return False"),
    ("m14 CANDLE wick 70 %", "WICK_MIN = 0.5 ", "WICK_MIN = 0.7 "),
    ("m15 CANDLE without the wick", "    return rng > 0 and (min(o, c) - l) >= WICK_MIN * rng and c >= l + 0.5 * rng",
     "    return rng > 0 and c >= l + 0.5 * rng"),
    ("m16 F1 strict", "    m[\"F1\"] = m[\"median\"] <= F1_MED_MAX", "    m[\"F1\"] = m[\"median\"] < F1_MED_MAX"),
    ("m17 F3 strict", "    m[\"F3\"] = m[\"longest_silence\"] <= F3_SILENCE_MAX", "    m[\"F3\"] = m[\"longest_silence\"] < F3_SILENCE_MAX"),
    ("m18 F4 strict", "    m[\"F4\"] = m[\"max\"] <= F4_DAY_MAX", "    m[\"F4\"] = m[\"max\"] < F4_DAY_MAX"),
    ("m19 rolling window of 5", "    roll = [sum(counts[i:i + 3]) for i in range(len(counts) - 2)]",
     "    roll = [sum(counts[i:i + 5]) for i in range(len(counts) - 4)]"),
    ("m20 dry core does not stop", "    if not (core[\"F2\"] and core[\"F3\"]):\n        return None, \"DRY\"",
     "    if False:\n        return None, \"DRY\""),
    ("m21 combo order reversed", "    for combo in ORDER[1:]:", "    for combo in ORDER[:0:-1]:"),
    ("m22 C1 against the ready's lower bound", "    hi_r = wilson(k_ready, n)[1]", "    hi_r = wilson(k_ready, n)[0]"),
    ("m23 C1 floor off", "    if n < FLOOR_SYMS:\n        return None", "    if False:\n        return None"),
    ("m24 unknown membership read as known", "    out[\"known\"] = out[\"nw_known\"] and out[\"wl_known\"]", "    out[\"known\"] = True"),
    ("m24b one snapshot is enough for «not a member»", "    out[\"known\"] = out[\"nw_known\"] and out[\"wl_known\"]",
     "    out[\"known\"] = out[\"nw_known\"] or out[\"wl_known\"]"),
    ("m25 Q = near_watch only", "    out[\"Q\"] = out[\"NW\"] | out[\"WL\"]", "    out[\"Q\"] = out[\"NW\"]"),
    ("m26 missed attribution takes the nearest step", "        if best is None or rank[why] > rank[best[\"fail\"]]:",
     "        if best is None or rank[why] < rank[best[\"fail\"]]:"),
    ("m27 free depth resets the base", "self.pc_fn(self.df.iloc[: x + 1], sweep=self.sweep)", "self.pc_fn(self.df.iloc[: x + 1])"),
    ("m28 merged gate accepts absence",
     "    got = hashlib.sha256(blob).hexdigest() if blob is not None else None\n    if got != PREREG_SHA256:",
     "    got = hashlib.sha256(blob).hexdigest() if blob is not None else PREREG_SHA256\n    if got != PREREG_SHA256:"),
]
orig = open(P, encoding="utf-8").read()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", FAISAL_ONLY="1")


def clear():
    for f in glob.glob(os.path.join(WT, "fm_forensics/layers/__pycache__/layers_test*")):
        os.remove(f)


res = []
try:
    for name, a, b in M:
        if orig.count(a) != 1:
            print("⛔ anchor count", orig.count(a), name)
            res.append(False)
            continue
        open(P, "w", encoding="utf-8").write(orig.replace(a, b, 1))
        clear()
        r = subprocess.run([sys.executable, "-B", P, "--guards"], cwd=WT, capture_output=True, text=True, timeout=900, env=env)
        fails = [ln[2:].split(":")[0][:40] for ln in r.stdout.splitlines() if ln.startswith("❌")]
        tb = "Traceback" in r.stdout + r.stderr
        ok = r.returncode != 0 and bool(fails) and not tb
        res.append(ok)
        print(("FELL " if ok else "SURVIVED/CRASH ") + name, "rc", r.returncode, "tb", tb, fails[:3], flush=True)
finally:
    open(P, "w", encoding="utf-8").write(orig)
    clear()
r = subprocess.run([sys.executable, "-B", P, "--guards"], cwd=WT, capture_output=True, text=True, env=env)
print(f"fell {sum(res)}/{len(M)} · restored rc", r.returncode)
sys.exit(0 if all(res) and r.returncode == 0 else 1)
