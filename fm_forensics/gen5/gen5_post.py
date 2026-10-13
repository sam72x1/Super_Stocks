"""GEN5 · post-run readings declared in the sealed contract (no new test, no criterion changed).

Reads data/gen5_result.json written by the sealed run and prints/writes only what GEN5_PREREG.md already declared:
  §⑤  likelihood ratio p_E ÷ p_C per component (declared "تُطبع");
  §⑥  the strict reading: Bonferroni over 11 component comparisons ⟶ 99.5% interval, same bootstrap and seed;
  §⑨  P5 — float / available-to-borrow known on the event decision days (E−20 … E−1), as the bot stored them before
       the next open (gen5_pit), unknown stays unknown;
  bars coverage by count (owner's prompt: «وأعلن التغطية»).
Output: data/gen5_post.json
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen5_features as G   # noqa: E402
import gen5_pit as PIT      # noqa: E402
import gen5_test as T       # noqa: E402

RES = os.path.join(HERE, "data", "gen5_result.json")
OUT = os.path.join(HERE, "data", "gen5_post.json")
STRICT = 0.995                       # contract §⑥: Bonferroni, 11 comparisons


def boot_ci(units, comp, level, reps=T.BOOT, seed=T.SEED):
    """Same resampling as gen5_test.boot_delta (symbol clusters, same seed), two-sided `level` interval."""
    def d(us):
        e = [u["ev"][comp] for u in us if u["ev"].get(comp) is not None]
        k = [sum(x[comp] for x in u["ctrl"] if x.get(comp) is not None)
             / max(1, sum(1 for x in u["ctrl"] if x.get(comp) is not None))
             for u in us if any(x.get(comp) is not None for x in u["ctrl"])]
        return (sum(e) / len(e) - sum(k) / len(k)) if e and k else None
    by = {}
    for u in units:
        by.setdefault(u["sym"], []).append(u)
    syms = sorted(by)
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        v = d([u for t in (rng.choice(syms) for _ in syms) for u in by[t]])
        if v is not None:
            vals.append(v)
    vals.sort()
    a = (1.0 - level) / 2.0
    return [round(vals[int(a * len(vals))], 4), round(vals[int((1.0 - a) * len(vals)) - 1], 4)]


def main():
    res = json.load(open(RES, encoding="utf-8"))
    if res.get("prereg_sha256") != T.PREREG_SHA256:
        print("⛔ result was not produced under the sealed contract")
        sys.exit(9)
    units = res["units"]
    out = {"prereg_sha256": T.PREREG_SHA256, "readings": {}}
    for name, us in (("primary", units), ("sensitivity_identity", [u for u in units if u["identity"]]),
                     ("descriptive_follow10", [u for u in units if u["follow"] >= 10])):
        blk = res[name]["components"]
        rows = {}
        for comp in T.COMPONENTS:
            c = blk[comp]
            lr = round(c["p_events"] / c["p_controls"], 3) if c["p_events"] is not None and c["p_controls"] else None
            rows[comp] = {"delta": c["delta"]["point"], "ci95": c["delta"]["ci95"],
                          "ci995_strict": boot_ci(us, comp, STRICT), "lr": lr}
        out["readings"][name] = rows
    # bars coverage (events and the controls actually used)
    bars = G.load_bars()
    ev_syms = sorted({u["sym"] for u in units})
    ctrl_syms = sorted({c for u in units for c in u["ctrl_syms"]})
    out["bars_coverage"] = {"archive_symbols": len(bars), "event_rows_with_bars": res["accounting"]["rows"]
                            - res["accounting"]["no_bars"], "event_rows": res["accounting"]["rows"],
                            "event_symbols_used": len(ev_syms), "control_symbols_used": len(ctrl_syms),
                            "control_draws": sum(len(u["ctrl_syms"]) for u in units)}
    # P5: float / available known on event decision days
    cnt = {}
    for df in bars.values():
        for dd in df.index.strftime("%Y-%m-%d"):
            cnt[dd] = cnt.get(dd, 0) + 1
    cal = sorted(dd for dd, n in cnt.items() if n >= 0.5 * len(bars))
    cix = {dd: i for i, dd in enumerate(cal)}
    pairs = []
    for u in units:
        k = cix[u["E"]]
        pairs += [(u["sym"], cal[j]) for j in range(k - T.WIN, k)]
    dates = sorted({t for _, t in pairs})
    pit = PIT.PIT(dates, {t: cal[cix[t] + 1] for t in dates})
    fk = sum(1 for s, t in pairs if pit.float_at(s, t)[0] is not None)
    ak = sum(1 for s, t in pairs if pit.avail_at(s, t)[0] is not None)
    out["p5"] = {"decision_days": len(pairs), "float_known": fk, "avail_known": ak,
                 "float_share": round(fk / len(pairs), 4), "avail_share": round(ak / len(pairs), 4),
                 "prediction": "float under 40% and available under 10%",
                 "held": fk / len(pairs) < 0.40 and ak / len(pairs) < 0.10}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for name, rows in out["readings"].items():
        print(f"\n== {name}")
        for comp, r in rows.items():
            print(f"  {comp:10s} Δ {r['delta']:+.3f}  95% {r['ci95']}  99.5% {r['ci995_strict']}  LR {r['lr']}")
    print("\nbars:", out["bars_coverage"])
    print("P5:", out["p5"])


if __name__ == "__main__":
    main()
