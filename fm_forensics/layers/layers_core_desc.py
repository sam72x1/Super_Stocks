"""T-LAYERS descriptive, non-governing (contract §④ «والبقيّةُ وصفًا»): stage B and false alarms for the CORE ALONE, run after the
governing run 2. The governing verdict is the selected definition's (layers_test.py); this only answers «what would the core alone
have caught and how often would it have been wrong». Writes data/core_descriptive.json.

    python3 fm_forensics/layers/layers_core_desc.py
"""
import contextlib
import io
import json
import os
import sys

WT = sys.argv[1] if len(sys.argv) > 1 else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(WT, "fm_forensics", "layers"))
os.chdir(WT)


def main():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        import layers_test as LT
        S, T, F, H, L = LT._mods()
        nwh = T.nearwatch_history()
        wlh = LT.watchlist_history()
        D, events, acc, evs = LT.stage_b(S, T, F, H, L, nwh, wlh, ())
        fa = LT.false_alarms(S, T, L, D, nwh, wlh, ())
    cap = LT.by_symbol(evs, lambda e: e["captured"] is not None)
    res = {"combo": "core", "symbols": len(cap), "captured": sum(cap.values()), "wilson": LT.wilson(sum(cap.values()), len(cap)),
           "captured_rows": [{k: e["captured"][k] for k in ("day", "lead", "depth", "VOL", "NODE", "CANDLE")} | {"sym": e["sym"], "O": e["A"]}
                             for e in evs if e["captured"]],
           "missed": {},
           "fa": {"fired": len(fa), "resolved": sum(1 for r in fa if r["outcome"] != "UNKNOWN"),
                  "false": sum(1 for r in fa if r["outcome"] == "FALSE"),
                  "reached": sorted(f'{r["sym"]} {r["day"]}' for r in fa if r["outcome"] == "REACHED_2X")}}
    for e in evs:
        if not e["captured"]:
            w = (e["best_fail"] or {}).get("fail") or "no_readable_day"
            res["missed"][w] = res["missed"].get(w, 0) + 1
    json.dump(res, open(os.path.join(WT, "fm_forensics/layers/data/core_descriptive.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
