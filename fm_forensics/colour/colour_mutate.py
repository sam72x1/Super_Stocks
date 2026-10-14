"""T-COLOUR mutation round: each mutation must make `colour_build.py --guards` fail cleanly (no crash). Restores the file in
finally. Bytecode is never written and the module's __pycache__ is cleared before each run (stale-bytecode lesson)."""
import glob
import os
import subprocess
import sys

WT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
P = os.path.join(WT, "fm_forensics/colour/colour_build.py")
M = [
    ("m1 tie goes to the lower red", "(round(d(s), 9), -s))[0]", "(round(d(s), 9), s))[0]"),
    ("m2 one shared line merges", 'c["set"] < d["set"] and len(c["set"]) >= 2', 'c["set"] < d["set"] and len(c["set"]) >= 1'),
    ("m3 smallest superset", '(-len(d["set"]), pos[d["key"]]))[0]', '(len(d["set"]), pos[d["key"]]))[0]'),
    ("m4 Faisal member ignored", '    if "FAISAL" in auth:\n        return "FAISAL"', '    if False:\n        return "FAISAL"'),
    ("m5 single non-unsigned kind ignored", 'return kinds.pop() if len(kinds) == 1 else "UNSIGNED"', 'return "UNSIGNED"'),
    ("m6 null symbol joins a superset", 'same = sorted([d for d in known if d["set"] == c["set"]]', 'same = sorted([d for d in known if d["set"] >= c["set"]]'),
    ("m7 transformed role kept both", '    if "تحول" in t and', '    if False and "تحول" in t and'),
    ("m8 red not compatible with entry", 'cls == "support" or (cls == "bid" and word == "دخول")', 'cls == "support"'),
    ("m9 black not compatible with target", 'return cls in ("resistance", "target")', 'return cls in ("resistance",)'),
    ("m10 no Arabic normalisation", '    return _DIAC.sub("", s or "").translate(_AR).lower()', '    return (s or "").lower()'),
    ("m11 red above black allowed", '        if c == "red" and above(v, val["black"]):', '        if False:'),
    ("m12 black below red allowed", '        if c == "black" and below(v, val["red"]):', '        if False:'),
    ("m13 blue below red allowed", '        if c == "blue" and below(v, val["red"]):', '        if False:'),
    ("m14 purple above black allowed", '        if c == "purple" and above(v, val["black"]):', '        if False:'),
    ("m15 above-all sensitivity ignored", 'v > max(others) if above_all else v > min(others)', 'v > min(others)'),
    ("m16 equal Pmin is above", 'cls = "above" if pmin > S else', 'cls = "above" if pmin >= S else'),
    ("m17 width over Pmax", '"width": _r((P[-1] - P[0]) / P[0] * 100)', '"width": _r((P[-1] - P[0]) / P[-1] * 100)'),
    ("m18 six percent excluded", '"le_6": sum(x <= ZONE_PCT for x in w)', '"le_6": sum(x < ZONE_PCT for x in w)'),
    ("m19 highest red above the low", '        rs = min(above)', '        rs = max(above)'),
    ("m20 red at the low counts as above", 'above = [r for r in R if r > u["low"]]', 'above = [r for r in R if r >= u["low"]]'),
    ("m21 13 % leaves the band", '    if d <= 13:\n        return "7-13"', '    if d < 13:\n        return "7-13"'),
    ("m22 axis lows govern", 'def measure_depth(units, srcs=("label",), keep_conflict=False):', 'def measure_depth(units, srcs=("label", "axis"), keep_conflict=False):'),
    ("m23 stop band 2 %", "NEAR_PCT = 1.0", "NEAR_PCT = 2.0"),
    ("m24 blue above the lowest black", 'cls = "all_above" if min(B) > max(K) else', 'cls = "all_above" if min(B) > min(K) else'),
    ("m25 non-canonical tags pass", "                    if t not in TAGS:", "                    if False:"),
    ("m26 text entries pass", "            if e is not None and not (isinstance(e, list)", "            if False and not (isinstance(e, list)"),
    ("m27 missing images pass", "    if sorted(last) != sorted(ids):", "    if False:"),
    ("m28 main never checked", "        if got != PROTO_SHA256:", "        if False:"),
    ("m29 fold ignores the family", "                c = fam\n", '                c = "other"\n'),
    ("m30 conflicts counted as bids", '        b = sum(1 for x in u["roles"] if x["colour"] == "purple" and x["role"] != "conflict")',
     '        b = sum(1 for x in u["roles"] if x["colour"] == "purple")'),
    ("m31 entries against the lowest red", "            S = nearest_red(R, e, e)", "            S = min(R)"),
    ("m32 labels from the chosen chart only", "        for m in members:\n            for lv in m[\"levels\"]:", "        for m in [chosen]:\n            for lv in m[\"levels\"]:"),
    ("m33 stop at support before at low", '        elif low is not None and near(st, low):\n            cat = "at_low"',
     '        elif False:\n            cat = "at_low"'),
    ("m34 a label with no role conflicts", "    if not roles or colour not in KEY_ROLE:\n        return False", "    if colour not in KEY_ROLE:\n        return False"),
]
orig = open(P, encoding="utf-8").read()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")


def clear():
    for f in glob.glob(os.path.join(WT, "fm_forensics/colour/__pycache__/colour_build*")):
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
        r = subprocess.run([sys.executable, "-B", P, "--guards"], cwd=WT, capture_output=True, text=True, timeout=300, env=env)
        fails = [ln[2:].split(" ")[0] for ln in r.stdout.splitlines() if ln.startswith("❌")]
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
