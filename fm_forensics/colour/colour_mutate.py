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
    ("m14 purple gets a key role", 'KEY_ROLE = {"red": "support", "black": "resistance", "blue": "target_clean"}',
     'KEY_ROLE = {"red": "support", "black": "resistance", "blue": "target_clean", "purple": "bid"}'),
    ("m15 above-all sensitivity ignored", 'v > max(others) if above_all else v > min(others)', 'v > min(others)'),
    ("m16 equal Pmin is above", 'cls = "above" if pmin > S else', 'cls = "above" if pmin >= S else'),
    ("m17 width over Pmax", '"width": _r((P[-1] - P[0]) / P[0] * 100)', '"width": _r((P[-1] - P[0]) / P[-1] * 100)'),
    ("m18 six percent excluded (purple width)", '            "le_6": sum(x <= ZONE_PCT for x in w), "gt_6": sum(x > ZONE_PCT for x in w), "rows": rows}',
     '            "le_6": sum(x < ZONE_PCT for x in w), "gt_6": sum(x > ZONE_PCT for x in w), "rows": rows}'),
    ("m18b six percent excluded (written width)", '"written_width": {"n": len(wrows), "le_6": sum(x <= ZONE_PCT for x in w)',
     '"written_width": {"n": len(wrows), "le_6": sum(x < ZONE_PCT for x in w)'),
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
    ("m30 gate opens on G1 alone", 'for g in ("G1_FAISAL", "G2_FAISAL_UNSIGNED"))', 'for g in ("G1_FAISAL",))'),
    ("m31 entries against the lowest red", "            S = nearest_red(R, e, e)", "            S = min(R)"),
    ("m32 labels from the chosen chart only", "        for m in members:\n            for lv in m[\"levels\"]:", "        for m in [chosen]:\n            for lv in m[\"levels\"]:"),
    ("m33 stop at support before at low", '        elif low is not None and near(st, low):\n            cat = "at_low"',
     '        elif False:\n            cat = "at_low"'),
    ("m34 a label with no role conflicts", "    if not roles or colour not in KEY_ROLE:\n        return False", "    if colour not in KEY_ROLE:\n        return False"),
    ("m35 the ±1 % band is open", 'return "above" if r > NEAR_PCT else', 'return "above" if r >= NEAR_PCT else'),
    ("m36 float noise at the band edge", "    r = round(rel, 9)", "    r = rel"),
    ("m37 exact half is a majority", "        if kl * 2 > n and ku * 2 > m:", "        if kl * 2 >= n and ku * 2 >= m:"),
    ("m38 unit votes ignored", "        if kl * 2 > n and ku * 2 > m:", "        if kl * 2 > n:"),
    ("m39 decisive on levels alone", "wilson_lo(kl, n) > 0.5 and wilson_lo(ku, m) > 0.5", "wilson_lo(kl, n) > 0.5"),
    ("m40 unit floor dropped", "    if n < MIN_LEVELS or m < MIN_UNITS:", "    if n < MIN_LEVELS:"),
    ("m41 at leaves the denominator", "    n, m = len(lv_sides), len(unit_sides)", '    n, m = sum(x != "at" for x in lv_sides), len(unit_sides)'),
    ("m42 shade rows dropped", '                keys.append("other:" + sh)', "                pass"),
    ("m43 unit vote by the mean", "uv = [_side(statistics.median(v)) for v", "uv = [_side(statistics.mean(v)) for v"),
    ("m44 other below the highest purple", 'cls = f"{other}_all_below_purple" if max(O) < min(P) else', 'cls = f"{other}_all_below_purple" if max(O) < max(P) else'),
    ("m45 depth2 over the low", '        d1, d2 = (r1 - u["low"]) / r1 * 100, (r2 - u["low"]) / r2 * 100',
     '        d1, d2 = (r1 - u["low"]) / u["low"] * 100, (r2 - u["low"]) / u["low"] * 100'),
    ("m46 depth2 half is not support", '"supported_descriptive" if both * 2 >= n else', '"supported_descriptive" if both * 2 > n else'),
    ("m47 depth2 floor lowered", 'verdict = "no_measure" if n < 10 else', 'verdict = "no_measure" if n < 5 else'),
    ("m48 stop against the lowest red", '(nearest_red(R, st, st) if s_rule == "nearest" else min(R))', '(min(R) if s_rule == "nearest" else min(R))'),
    ("m49 unit price from the chosen chart only", '            "price_last": fields["price_last"], "price_last_src"', '            "price_last": chosen.get("price_last"), "price_last_src"'),
    ("m50 price_last not required", '            if "price_last" not in c:', "            if False:"),
    ("m51 price_now governs", 'def assign_roles(u, above_all=False, price_key="price_last"):', 'def assign_roles(u, above_all=False, price_key="price_now"):'),
    ("m52 ANPA side to the tag", '            r1, s1 = side_of(value, c["price_last"])', '            r1, s1 = side_of(value, c["price_now"])'),
    ("m53 nearest before purple", "cand.append((0 if purple_family(lv[0], fam) else 1, abs(lv[1] - v), n_i, k, i, lv, c))",
     "cand.append((abs(lv[1] - v), 0 if purple_family(lv[0], fam) else 1, n_i, k, i, lv, c))"),
    ("m54 match tolerance 2 %", "                    if abs(lv[1] - v) <= 0.01 * v:", "                    if abs(lv[1] - v) <= 0.02 * v:"),
    ("m55 written width over the max", '"width": _r((max(E) - min(E)) / min(E) * 100)', '"width": _r((max(E) - min(E)) / max(E) * 100)'),
    ("m56 entries against the tag", '            rel, side = side_of(e, u.get("price_last"))', '            rel, side = side_of(e, u.get("price_now"))'),
    ("m57 dark purple outside the family", '    return colour == "purple" or (colour == "other" and fam == "purple")', '    return colour == "purple"'),
    ("m58 precedence: wick before body", 'HEAD_PRECEDENCE = ("RED_BODY_TOP", "RED_WICK_TOP",', 'HEAD_PRECEDENCE = ("RED_WICK_TOP", "RED_BODY_TOP",'),
    ("m59 class not checked against contacts", "            elif not con or cls != min(con, key=HEAD_PRECEDENCE.index):", "            elif False:"),
    ("m60 unreadable with contacts allowed", "                if con:\n                    probs.append", "                if False:\n                    probs.append"),
    ("m61 first reading from the latest rev", '            if r.get("rev") == 1:\n                first[k] = cls', '            if True:\n                first[k] = cls'),
    ("m62 sample seed moved", "HEAD_SEED, HEAD_N, HEAD_MIN = 20261015, 40, 10", "HEAD_SEED, HEAD_N, HEAD_MIN = 20261016, 40, 10"),
    ("m63 purple values descending", '        v = rng.choice(sorted(x["value"] for x in u["levels"] if x["colour"] == "purple"))',
     '        v = rng.choice(sorted((x["value"] for x in u["levels"] if x["colour"] == "purple"), reverse=True))'),
    ("m64 unreadable in the denominator", '        readable = sum(v for k, v in cnt.items() if k != "UNREADABLE")', "        readable = sum(cnt.values())"),
    ("m65 sensitivity without wicks", '        loose = top + cnt.get("RED_WICK_TOP", 0)', "        loose = top"),
    ("m66 exact half not supported", '("supported_descriptive" if k * 2 >= readable else "dropped_descriptive")',
     '("supported_descriptive" if k * 2 > readable else "dropped_descriptive")'),
    ("m67 unknown contacts pass", "any(c not in HEAD_PRECEDENCE for c in con)", "False"),
    ("m68 floor lowered", "HEAD_SEED, HEAD_N, HEAD_MIN = 20261015, 40, 10", "HEAD_SEED, HEAD_N, HEAD_MIN = 20261015, 40, 5"),
    ("m69 revised counts the unchanged", 'sum(r["class"] != r["first_class"] for r in rows)', 'sum(r["class"] == r["first_class"] for r in rows)'),
    ("m70 sample from G1 only", 'if u["author"] in ("FAISAL", "UNSIGNED")', 'if u["author"] in ("FAISAL",)'),
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
