"""Guards of the historical 4H audit (research only). Exit 0 = all pass.
H4_FAST=1 skips the slow end-to-end regeneration (H4G1); every other guard is fast and always runs.
Run from the repo root:  python3 faisal_engine/readynow/condition_atlas/test_h4.py
"""
import ast
import copy
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, HERE)
FAST = os.environ.get("H4_FAST") == "1"
FAILS = []


def check(name, ok, detail=""):
    print(("✅ " if ok else "❌ ") + name + ("" if ok else f" — {detail}"))
    if not ok:
        FAILS.append(name)


def guarded(name, fn):
    try:
        ok, detail = fn()
    except Exception as e:                                                # noqa: BLE001
        ok, detail = False, f"⛔ {type(e).__name__}: {e}"
    check(name, ok, detail)


import h4_audit as H                                                      # noqa: E402

RES = json.load(open(H.OUT_JSON, encoding="utf-8"))


class FakeCal(H.Cal):
    def __init__(self, sessions):
        self.s = list(sessions)
        self.i = {d: k for k, d in enumerate(self.s)}


SESS = [f"2026-01-{d:02d}" for d in range(1, 31)] + [f"2026-02-{d:02d}" for d in range(1, 28)]


def ep(sym, onset, end, quality="OK"):
    return {"sym": sym, "onset": onset, "peak": end, "d1": end, "q": end, "x70": end, "kind": "jump",
            "quality": quality}


def h4g1():
    """End to end: the JSON and the four reports are reproduced byte for byte from the sources."""
    p = subprocess.run([sys.executable, os.path.join(HERE, "h4_audit.py"), "--check"], cwd=ROOT, capture_output=True,
                       text=True, timeout=900)
    return p.returncode == 0 and "OK" in p.stdout, (p.stdout + p.stderr)[-300:]


def h4g2():
    """Verbatim: every rule excerpt is in the register, and an altered excerpt is caught."""
    reg = H.load_register()
    clean = H.verify_quotes(reg) == []
    saved = copy.deepcopy(H.RULES)
    try:
        H.RULES[0]["src"][0] = (H.RULES[0]["src"][0][0], H.RULES[0]["src"][0][1] + " متماسك جدا")
        caught = len(H.verify_quotes(reg)) == 1
    finally:
        H.RULES[:] = saved
    return clean and caught and RES["quote_check"] == [], f"clean={clean} caught={caught}"


def h4g3():
    """A capture/upload/send date never becomes a market date."""
    r = {"id": "X1", "dprec": "TIME", "date": "12:00", "seen": "شارت 4 ساعات بلا سعر", "tk": ["AAA"]}
    out = H.date_image(r, {"X1": ("2026-05-01", "exif")}, {}, None, "2026-10-08")
    bad = [i["id"] for i in RES["images"] if (i.get("dating") or {}).get("basis") == "UPLOAD_BOUND_ONLY"
           and (i["dating"]["decision"] or i.get("links"))]
    return out["decision"] is None and out["basis"] == "UPLOAD_BOUND_ONLY" and not bad, f"{out} {bad[:3]}"


def h4g4():
    """In-event decisions are excluded; T−10…T−7 is counted in sessions, with exact edges."""
    cal = FakeCal(SESS)
    e1, e2 = ep("AAA", SESS[10], SESS[12]), ep("AAA", SESS[30], SESS[31])
    inev = H.relation(cal, [e1, e2], SESS[11])
    t8 = H.relation(cal, [e1, e2], SESS[22])
    t6 = H.relation(cal, [e1, e2], SESS[24])
    t10 = H.relation(cal, [e1, e2], SESS[20])
    t11 = H.relation(cal, [e1, e2], SESS[19])
    ok = (inev["status"] == "IN_EVENT" and t8["status"] == "T7_10" and t8["sessions_to_onset"] == 8
          and t6["status"] == "T1_6" and t10["status"] == "T7_10" and t11["status"] == "T11_30")
    return ok, [x["status"] for x in (inev, t8, t6, t10, t11)]


def h4g5():
    """Price anchors date a chart only when exactly one session matches within 0.75% (raw = adjusted × later ratios)."""
    a = H.Anchor.__new__(H.Anchor)
    a.bars = {"AAA": [["2026-01-02", 1, 1, 1, 2.00, 1], ["2026-01-05", 1, 1, 1, 2.01, 1], ["2026-01-06", 1, 1, 1, 3.00, 1]]}
    a.spl = {"AAA": []}
    amb = a.match("AAA", "ah", 2.00, 0.0, "2026-01-01", "2026-01-31")[0]
    uni = a.match("AAA", "ah", 3.00, 0.0, "2026-01-01", "2026-01-31")
    edge_in = a.match("AAA", "ah", 3.0 * 1.0074, 0.0, "2026-01-01", "2026-01-31")[0]
    edge_out = a.match("AAA", "ah", 3.0 * 1.0080, 0.0, "2026-01-01", "2026-01-31")[0]
    a.spl = {"AAA": [["2026-01-10", 0.1]]}        # a later 1:10 reverse split: raw = adjusted × 0.1
    spl = a.match("AAA", "ah", 0.30, 0.0, "2026-01-01", "2026-01-31")
    ok = (amb == "ambiguous" and uni[0] == "unique" and uni[1][0][0] == "2026-01-06" and edge_in == "unique"
          and edge_out == "none" and spl[0] == "unique" and spl[1][0][0] == "2026-01-06")
    return ok, (amb, uni[0], edge_in, edge_out, spl[0])


def h4g6():
    """Grid constructibility: hourly :00 bars cannot form the 09:30-anchored grid; 30-minute bars form both."""
    hourly = [h * 60 for h in range(4, 20)]
    m30 = [m for m in range(240, 1200, 30)]
    ok = (not H.grid_ok(hourly, 60, "G_APP") and H.grid_ok(hourly, 60, "G_NY")
          and H.grid_ok(m30, 30, "G_APP") and H.grid_ok(m30, 30, "G_NY"))
    stores_ok = all(s["grids_constructible"]["G_APP"] == s["ohlc"] for s in RES["stores"])
    return ok and stores_ok, f"stores_ok={stores_ok}"


def h4g7():
    """fwd/ is never a source and no path literal in the code reaches it."""
    srcs = [v for v in H.SOURCES.values() if "readynow/fwd" in v]
    lits = []
    for f in ("h4_audit.py", "h4_report.py"):
        tree = ast.parse(open(os.path.join(HERE, f), encoding="utf-8").read())
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                for a in list(n.args) + [k.value for k in n.keywords]:
                    if isinstance(a, ast.Constant) and isinstance(a.value, str) and "fwd" in a.value:
                        lits.append((f, a.value))
    return not srcs and not lits, f"{srcs} {lits}"


def h4g8():
    """Sealed atlas artifacts and the reconciliation §0 are byte-identical to their recorded hashes."""
    import ca_reconcile as R
    bad = [p for p, h in R.SEALED_DATA.items()
           if hashlib.sha256(open(os.path.join(HERE, p), "rb").read()).hexdigest() != h]
    pre = open(os.path.join(HERE, "RECONCILIATION_ADDENDUM.md"), "rb").read()[:R.PREFIX_BYTES]
    return not bad and hashlib.sha256(pre).hexdigest() == R.PREFIX_SHA256, f"{bad}"


def h4g9():
    """The verdict follows its rule (not hard-coded): enough OHLC positives, controls and events flip it."""
    fake = copy.deepcopy(RES)
    p = fake["population"]["holdout"]
    p["pos710_rows_with_intraday_ohlc"], p["neg_rows_with_intraday_ohlc"] = 40, 400
    p["eligible_events_with_intraday_ohlc"] = ["AAA|2026-06-10", "BBB|2026-07-01"]
    flips = H.verdict(fake)["status"] == "DATA_SUFFICIENT_FOR_A_TEST"
    now = H.verdict(RES)["status"] == RES["verdict"]["status"] == "TEST_NOT_PERFORMED — EVIDENCE GAP"
    return flips and now, f"flips={flips} now={now}"


def h4g10():
    """Faisal's rules carry no app or third-party source; «شمعة قروب» stays in the non-Faisal list."""
    reg = H.load_register()
    allowed_u = {"TG_50587", "TG_50832", "TG_20260918_38_NUWE"}
    bad = [(x["id"], i) for x in H.RULES for i, _e in x["src"]
           if reg[i]["au"] not in ("F", "U") or (reg[i]["au"] == "U" and i not in allowed_u)]
    edu = any(i == "EDU_20260827_dki_group_candle" for x in H.NON_FAISAL for i, _e in x["src"])
    return not bad and edu, f"{bad} edu={edu}"


def h4g11():
    """No production module, network library or download path is imported."""
    banned = {"Super_stock", "requests", "urllib", "yfinance", "websocket", "tv_data", "http", "socket"}
    hits = []
    for f in ("h4_audit.py", "h4_report.py"):
        for n in ast.walk(ast.parse(open(os.path.join(HERE, f), encoding="utf-8").read())):
            names = [a.name for a in n.names] if isinstance(n, ast.Import) else (
                [n.module or ""] if isinstance(n, ast.ImportFrom) else [])
            hits += [(f, x) for x in names if x.split(".")[0] in banned]
    return not hits, f"{hits}"


def h4g12():
    """The findings report, rendered from the JSON, states the verdict and the counts."""
    import h4_report as HR
    txt = HR.findings_doc(RES)
    v = RES["verdict"]
    need = [v["status"], f"= {v['eligible_events_all_windows']}:", "The formal four-hour test could not be performed"]
    miss = [n for n in need if n not in txt]
    return not miss, f"{miss}"


def h4g13():
    """Every cited number about the 4H grid is present in its source file."""
    ge = H.grid_evidence()
    return all(g["found"] for g in ge) and len(ge) == len(H.GRID_EVIDENCE), [g["claim"] for g in ge if not g["found"]]


def h4g14():
    """The file-date example in the source audit holds in the register and the date table, and the report says so."""
    import h4_report as HR
    reg = H.load_register()
    r = reg["IMG_0698"]
    ub = H.upper_bounds(reg)
    txt = HR.source_audit(RES)
    said = all(x in txt for x in ("07/31/2026", "2026-08-01", "2026-08-06"))
    return ("07/31/2026" in r["seen"] and r["date"].startswith("2026-08-01") and ub.get("IMG_0698") == ("2026-08-06", "exif")
            and said, f"{r['date']} {ub.get('IMG_0698')} said={said}")


def h4g15():
    """An intraday-only threshold needs a daily high ≥ 70% over the prior close outside every episode."""
    cal = FakeCal(SESS)
    bars = [[d, 1, 1.0, 1.0, 1.0, 1] for d in SESS]
    bars[5] = [SESS[5], 1, 1.65, 1.0, 1.0, 1]      # +65%: not a threshold
    bars[8] = [SESS[8], 1, 1.75, 1.0, 1.1, 1]      # +75%: a threshold
    bars[12] = [SESS[12], 1, 1.9, 1.0, 1.0, 1]     # +90% but inside an episode
    out = H.intraday_only(cal, bars, [ep("AAA", SESS[11], SESS[13])], 1, 20)
    return [z["session"] for z in out] == [SESS[8]], f"{out}"


for name, fn in (("H4G1 end-to-end reproduction (--check)", h4g1), ("H4G2 verbatim quotes", h4g2),
                 ("H4G3 file dates are never market dates", h4g3), ("H4G4 in-event exclusion and T−10…T−7 edges", h4g4),
                 ("H4G5 unique price anchor at 0.75%", h4g5), ("H4G6 grid constructibility", h4g6),
                 ("H4G7 fwd/ never read", h4g7), ("H4G8 sealed atlas untouched", h4g8),
                 ("H4G9 verdict follows its rule", h4g9), ("H4G10 Faisal vs app/third party", h4g10),
                 ("H4G11 no production or network import", h4g11), ("H4G12 findings state the JSON", h4g12),
                 ("H4G13 grid evidence in sources", h4g13), ("H4G14 file-date example", h4g14),
                 ("H4G15 intraday-only threshold", h4g15)):
    if FAST and name.startswith("H4G1 "):
        print("⏭️  " + name + " (H4_FAST)")
        continue
    guarded(name, fn)

print(f"\nالفاشل: {len(FAILS)}" + (f" — {', '.join(FAILS)}" if FAILS else ""))
sys.exit(1 if FAILS else 0)
