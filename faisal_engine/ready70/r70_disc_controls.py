"""Discovery-only: stage 1 vs burden-matched generic controls (counted as examined combinations 45-48)."""
import sys, statistics as st
sys.path.insert(0, "faisal_engine/ready70")
import r70_eval as E
rows = E.load(E.PI_FILE, E.DISC_FROM, E.DISC_TO); assert max(r["t"] for r in rows) <= E.DISC_TO
E.set_label("f")
s1 = lambda r: r["pc_stage"] == "1"
def matched(field, sign):
    from collections import defaultdict
    by = defaultdict(list)
    for r in rows: by[r["t"]].append(r)
    keep = set()
    for t, rs in by.items():
        k = sum(1 for r in rs if s1(r))
        ranked = sorted((r for r in rs if E.num(r[field]) is not None), key=lambda r: (sign * E.num(r[field]), r["sym"]))
        keep |= {(r["t"], r["sym"]) for r in ranked[:k]}
    return lambda r: (r["t"], r["sym"]) in keep
vol = matched("range20", -1)      # most volatile first
drop = matched("ret5", +1)        # most dropped first
loc = lambda r: r["loc"] == "1"
ev = E.evaluable(rows); base = sum(r[E.LAB] == "POS" for r in ev) / len(ev)
for name, f in (("ALL", lambda r: True), ("STAGE1", s1), ("VOL-k", vol), ("DROP-k", drop), ("LOC", loc)):
    c = E.cell_stats(rows, f, base, name)
    g = [E.num(r["g10_max"]) for r in ev if f(r) and E.num(r["g10_max"]) is not None]
    d = [E.num(r["g10_dd"]) for r in ev if f(r) and E.num(r["g10_dd"]) is not None]
    r70 = sum(1 for x in g if x >= 70) / len(g)
    print(name, c["rows"], c["rate"], c["lift"], "flags/day", c["flags_per_day"], "| +70% from decision", round(r70, 4),
          "med max gain", st.median(g), "med dd", st.median(d))
for nm, f in (("VOL-k", vol), ("DROP-k", drop)):
    print("STAGE1 vs", nm, E.cluster_boot_ratio(rows, s1, f, reps=400))
price = matched("px", +1)          # cheapest traded price first
c = E.cell_stats(rows, price, base, "PRICE-k"); print("PRICE-k", c["rows"], c["rate"], c["lift"], "flags/day", c["flags_per_day"])
print("STAGE1 vs PRICE-k", E.cluster_boot_ratio(rows, s1, price, reps=400))
print("STAGE1 vs LOC", E.cluster_boot_ratio(rows, s1, loc, reps=400))
print("STAGE1 vs ALL", E.cluster_boot_ratio(rows, s1, lambda r: True, reps=400))
