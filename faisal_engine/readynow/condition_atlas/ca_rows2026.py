"""Faisal condition atlas — per-stock rows for the 2026 READY classes (after the sealed run only).
One row per (symbol, session) in READY_1, READY_2 or READY_3 of validation and holdout: class, label (known
afterwards), the three axis probabilities, the flags that hold, the top contributors and blockers of axis C, and the
confidence note. Output: data/ready_rows_2026.csv.gz
Run from the repo root:  python3 faisal_engine/readynow/condition_atlas/ca_rows2026.py
"""
import csv
import gzip
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ca_casebook as CB                                                  # noqa: E402
import ca_final as CF                                                     # noqa: E402
import ca_lib as L                                                        # noqa: E402

CONF = "partial: daily bars only; float, borrow, offering, groups and operator UNKNOWN"
FIELDS = ["window", "sym", "t", "class", "label", "A", "B", "C", "flags", "C_top", "C_blockers", "confidence"]


def main():
    if not CF.protocol_ok():
        print("⛔ not sealed — nothing written")
        sys.exit(9)
    fz = json.load(open(os.path.join(L.DATA, "model_frozen.json"), encoding="utf-8"))
    out = []
    for w in CF.WINDOWS:
        cls = CF.classify_window(w, fz)
        rows, _by, _m = L.load(w)
        for r in sorted(rows, key=lambda r: (r["t"], r["sym"])):
            c = cls.get((r["sym"], r["t"]))
            if c not in ("READY_1", "READY_2", "READY_3"):
                continue
            s = CB.axis_scores(r, fz)
            out.append({"window": w, "sym": r["sym"], "t": r["t"], "class": c, "label": r["lab"], "A": s["A"],
                        "B": s["B"], "C": s["C"], "flags": ";".join(n for n, f in L.COND.items() if f(r)),
                        "C_top": ";".join(s["C_top"]), "C_blockers": ";".join(s["C_blockers"]), "confidence": CONF})
    buf = io.StringIO()
    wr = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator="\n")
    wr.writeheader()
    wr.writerows(out)
    with gzip.GzipFile(os.path.join(L.DATA, "ready_rows_2026.csv.gz"), "wb", mtime=0) as f:
        f.write(buf.getvalue().encode("utf-8"))
    return len(out)


if __name__ == "__main__":
    print("rows", main())
