"""🚪🧭 Gate provenance inventory — research only (no Telegram, no state writes, no production change).

What it builds (owner mission «GATE PROVENANCE, CANDIDATE GENERATION, AND EVIDENCE-BASED REPAIR», 2026-10-09):
  · one row per gate of the candidate chain (universe → data → `analyze_ticker` → post-scan → quality → capacity →
    post-enrich → readiness → manual display), from the curated provenance file `data/gate_provenance.json`;
  · derived columns read from the code itself: the line of each gate's anchor inside its function (AST), the live
    threshold values under the production configuration (`FAISAL_ONLY=1`), production reject counts from a frozen
    snapshot of `reject_log.json`, and completeness checks (every `_reject(...)` code and every post-scan gate
    function must be inventoried — an uninventoried gate fails the build);
  · the first exclusion of each Faisal episode at its as-of date, recomputed with the production `analyze_ticker`
    on the frozen ranking bars (`data/rank/bars.json.gz`, bars dated < T), checked against the frozen ranking rows
    (`data/rank/rows.csv.gz`), with the peel chain (the next wall when the previous one is neutralised — research
    only, the cause is always the FIRST wall) and the metrics needed to tell an adjustment artefact from a rule;
  · `GATE_PROVENANCE_REPORT.md` — the decision table, generated from the data (no hand-typed numbers).

`python3 faisal_engine/gate_inventory.py` builds · `--check` rebuilds in memory and compares (line numbers are
normalised: they move with any edit above the gate; the anchor must still be found inside its function).
`--snapshot` refreshes the frozen reject-count snapshot from the working `reject_log.json` (explicit only).
"""
import ast
import contextlib
import csv
import gzip
import hashlib
import io
import json
import os
import re
import sys

os.environ["FAISAL_ONLY"] = "1"                 # the subject is the production configuration
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
DATA = os.path.join(HERE, "data")
PROV = os.environ.get("GATE_PROV_FILE") or os.path.join(DATA, "gate_provenance.json")
SNAP = os.path.join(DATA, "gate_reject_snapshot.json")
F_JSON = os.path.join(OUT, "GATE_INVENTORY.json")
F_CSV = os.path.join(OUT, "GATE_INVENTORY.csv")
F_FX = os.path.join(OUT, "gate_first_exclusion.csv")
F_MD = os.path.join(HERE, "GATE_PROVENANCE_REPORT.md")
CATS = ["DIRECT_FAISAL_EVIDENCE", "INFERRED_FROM_FAISAL_EVIDENCE", "OWNER_POLICY", "ENGINEERING_GUARD",
        "DATA_OR_ADJUSTMENT_ARTIFACT", "UNKNOWN_OR_UNSUPPORTED"]
# post-scan gate functions that must each be inventoried (completeness)
REQUIRED_FUNCS = ["get_universe", "_extract_into", "analyze_ticker", "apply_short_gate", "apply_float_gate", "classify_tier",
                  "rank_key", "dq_filter", "fill_picks", "refloat_gate_recheck", "borrow_second_chance",
                  "borrow_gate_recheck", "entry_status", "append_short_float_gates", "post_enrich_verdict"]
# production reject code → peel-chain gate name (p3lib.reason_gate names) → inventory id
GATE_ID = {"M1": "M1_PRICE", "M2_CEIL": "M2_CEIL", "M2_FLOOR": "M2_FLOOR", "M3": "M3_FLOOR", "M4_RANGE": "M4_RANGE",
           "M4_RISE": "M4_RISE", "M5": "M5_DOLLAR_VOL", "RSI_OS": "M10_RSI_OS", "RSI_NOW": "M10_RSI_NOW",
           "SOFT": "SOFT_COUNT", "SCORE": "SCORE_MIN", "NEAR": "NEAR_READINESS", "ANCHOR": "ANCHOR_TWO_TOUCH",
           "DEPTH": "D_DEPTH", "UNIVERSE": "U_NASDAQ"}
NEUTRAL = {"M1": {"MIN_PRICE": 0.0}, "M2_CEIL": {"MAX_DROP_PCT": 1e9}, "M2_FLOOR": {"MIN_DROP_FLOOR": -1e9},
           "M3": {"PRIOR_SPIKE_FLOOR": -1e9}, "M4_RANGE": {"BASE_RANGE_MAX_PCT": 1e9},
           "M4_RISE": {"RECENT_RISE_BLOCK_PCT": 1e9}, "M5": {"MIN_DOLLAR_VOL": 0.0}, "RSI_OS": {"RSI_OS_HARD": 1e9},
           "RSI_NOW": {"RSI_NOW_HARD": 1e9}, "SOFT": {"WATCH_MAX_FAILS": 10 ** 6}, "SCORE": {"SCORE_MIN": -1e9},
           "NEAR": {"NEAR_PCT": -1e9}, "DEPTH": {"MIN_BARS": 0}, "ANCHOR": {}}
EXTRA_CASES = [("HUBC", "2026-04-24", "TG_2098", "anchor case (Faisal state UNKNOWN)")]


def _S():
    sys.path.insert(0, ROOT)
    os.chdir(ROOT)
    with contextlib.redirect_stdout(io.StringIO()):
        import Super_stock as S                          # noqa: E402
    return S


def _rel(p):
    return os.path.relpath(p, ROOT)


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- code locations (AST)
def _functions(path):
    src = open(os.path.join(ROOT, path), encoding="utf-8").read()
    lines = src.splitlines()
    out = {}
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name not in out:
            out[n.name] = (n.lineno, n.end_lineno, n)
    return src, lines, out


def locate(gates):
    """(file, function, anchor) ⟶ line of the anchor inside the function; missing ⟶ build error."""
    cache, errors = {}, []
    for g in gates:
        f = g["file"]
        if f not in cache:
            cache[f] = _functions(f)
        src, lines, fn = cache[f]
        if g["function"] not in fn:
            errors.append(f"{g['id']}: function {g['function']} not in {f}")
            g["line"] = None
            continue
        a, b, _ = fn[g["function"]]
        hit = [i for i in range(a - 1, b) if g["anchor"] in lines[i]]
        if not hit:
            errors.append(f"{g['id']}: anchor not found in {f}::{g['function']}")
            g["line"] = None
            continue
        g["line"] = hit[0] + 1
        g["function_lines"] = [a, b]
    return errors, cache


def completeness(gates, cache):
    """Every reject code / bare `return None` of `analyze_ticker` and every required function must be inventoried."""
    errors = []
    _, _, fn = cache["Super_stock.py"]
    node = fn["analyze_ticker"][2]
    codes, bare = [], 0
    for n in ast.walk(node):
        if isinstance(n, ast.Return):
            v = n.value
            if isinstance(v, ast.Call) and getattr(v.func, "id", "") == "_reject":
                a = v.args[0]
                if isinstance(a, ast.Constant):
                    codes.append(str(a.value))
                elif isinstance(a, ast.JoinedStr):
                    codes.append("".join(str(x.value) for x in a.values if isinstance(x, ast.Constant)))
            elif v is None or (isinstance(v, ast.Constant) and v.value is None):
                bare += 1
    inv = [c for g in gates for c in g.get("reject_codes") or []]
    for c in codes:
        if not any(c == x or c.startswith(x) for x in inv):
            errors.append(f"reject code not inventoried: {c}")
    silent = [g["id"] for g in gates if g["function"] == "analyze_ticker" and "return None" in g.get("on_fail", "")]
    if bare != len(silent):
        errors.append(f"bare `return None` paths in analyze_ticker: {bare} vs inventoried {len(silent)} ({silent})")
    funcs = {g["function"] for g in gates}
    for f in REQUIRED_FUNCS:
        if f not in funcs:
            errors.append(f"required gate function not inventoried: {f}")
    return errors, codes, bare


# ---------------------------------------------------------------- live values and production counts
def _fmt(v):
    if isinstance(v, bool) or v is None or isinstance(v, str):
        return v
    try:
        fv = float(v)
    except (TypeError, ValueError):
        return str(v)
    return int(fv) if fv == int(fv) and abs(fv) < 1e15 else round(fv, 4)


def snapshot():
    log = json.load(open(os.path.join(ROOT, "reject_log.json"), encoding="utf-8"))
    days = []
    for e in log:
        walls = e.get("walls") or {}
        full = e.get("walls_n") or {}            # the stored name lists are sampled (400); walls_n holds the full counts
        days.append({"date": e.get("date"),
                     "walls": {k: int(full.get(k, len(v) if isinstance(v, list) else v)) for k, v in walls.items()},
                     "sampled": list(e.get("sampled") or [])})
    snap = {"source": "reject_log.json (working tree)", "source_sha256": _sha(os.path.join(ROOT, "reject_log.json")),
            "days": days}
    json.dump(snap, open(SNAP, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"snapshot: {len(days)} days")


def counts_for(g, snap):
    codes = g.get("reject_codes") or []
    if not codes or not snap:
        return None
    per = []
    for d in snap["days"]:
        n = sum(v for k, v in d["walls"].items() if any(k == c or k.startswith(c) for c in codes))
        per.append((d["date"], n))
    vals = sorted(n for _, n in per)
    med = vals[len(vals) // 2] if vals else 0
    return {"days": len(per), "median_per_day": med, "max_per_day": max(vals) if vals else 0,
            "last_day": per[-1][0] if per else "", "last_day_count": per[-1][1] if per else 0}


# ---------------------------------------------------------------- first exclusion (frozen bars, production code)
def _load_rank():
    bars = json.load(gzip.open(os.path.join(DATA, "rank", "bars.json.gz"), "rt", encoding="utf-8"))["daily"]
    rows = {}
    with gzip.open(os.path.join(DATA, "rank", "rows.csv.gz"), "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows[(r["date"], r["symbol"])] = r
    splits = json.load(open(os.path.join(DATA, "rank", "splits.json"), encoding="utf-8"))["splits"]
    ub = json.load(gzip.open(os.path.join(DATA, "universe_bars.json.gz"), "rt", encoding="utf-8"))
    ubars = ub.get("daily") or ub.get("bars") or {}
    uni = json.load(open(os.path.join(DATA, "rank", "universe.json"), encoding="utf-8"))
    return bars, rows, splits, ubars, uni


def _frame(rows):
    import pandas as pd
    df = pd.DataFrame(rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    df["Date"] = pd.to_datetime(df["Date"])
    return df.set_index("Date")


def _reason_gate(why):
    m = {"M1_سعر": "M1", "M2_هبوط_فوق_97": "M2_CEIL", "M2_هبوط_تحت_40": "M2_FLOOR", "M2_hi52": "M2_FLOOR",
         "M3_انفجار_تحت_60": "M3", "M4_base_واسعة": "M4_RANGE", "M4_base_lo": "M4_RANGE", "M4_انفجر_فعلاً": "M4_RISE",
         "M5_سيولة": "M5", "M10_RSI_ما_تشبّع": "RSI_OS", "M10_RSI_فات_القطار": "RSI_NOW", "M_لا_مستوى_مختبر": "ANCHOR",
         "MIN_BARS": "DEPTH"}
    if why in m:
        return m[why]
    for p, n in (("نواقص_فوق", "SOFT"), ("RR+نواقص", "SOFT"), ("نقاط_تحت", "SCORE"), ("بعيد_عن_الدخول", "NEAR")):
        if str(why).startswith(p):
            return n
    return str(why)


def run_once(S, sym, df, neutral):
    """production `analyze_ticker`; neutralised gates use relaxed CONFIG values restored in `finally`."""
    saved, tl = {}, S.tested_level
    for gname in neutral:
        for k, v in NEUTRAL[gname].items():
            saved[k] = S.CONFIG[k]
            S.CONFIG[k] = v
    if "ANCHOR" in neutral:
        def _tl(d, lookback=30, tol=0.015, min_touches=2):
            r = tl(d, lookback, tol, min_touches)
            if r:
                return r
            return {"level": round(float(d.tail(int(lookback))["Low"].min()), 4), "touches": 1}
        S.tested_level = _tl
    for k in ("BT_SPLIT_REF_M2", "BT_SPLIT_AWARE_M4", "BT_M4_POST_SPLIT", "BT_STABILITY_GATE"):
        saved.setdefault(k, S.CONFIG.get(k))
        S.CONFIG[k] = 0 if k != "BT_STABILITY_GATE" else ""
    S._BT_SPLITS_CTX = None
    S._REJECT_REASONS.pop(sym, None)
    try:
        if len(df) < S.CONFIG["MIN_BARS"]:
            return "REJECT", "MIN_BARS"
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                r = S.analyze_ticker(sym, df)
            except Exception as e:                                # noqa: BLE001
                return "ERROR", type(e).__name__
        return ("PASS", "") if r else ("REJECT", S._REJECT_REASONS.get(sym, "?"))
    finally:
        for k, v in saved.items():
            S.CONFIG[k] = v
        S.tested_level = tl


def metrics(S, df, rsplits, T):
    """the quantities each gate reads, with the production formulas; plus the post-split reference (artefact test)."""
    import math
    c = df["Close"].values
    high, low, vol, close = df["High"], df["Low"], df["Volume"], df["Close"]
    price = float(c[-1])
    hi52 = float(high.tail(252).max())
    drop = (1.0 - price / hi52) * 100.0 if hi52 > 0 else None
    sp = [(d, r) for d, r in rsplits if d < T]
    psh = None
    if sp:
        import pandas as pd
        try:
            psh = S._post_split_high(high.tail(252), pd.Series([r for _, r in sp], index=pd.to_datetime([d for d, _ in sp])),
                                     df.index[-1])
        except Exception:                                         # noqa: BLE001
            psh = None
    drop_ps = ((1.0 - price / psh) * 100.0) if psh else None
    bw = int(S.CONFIG["BASE_WINDOW"])
    base_hi, base_lo = float(high.tail(bw).max()), float(low.tail(bw).min())
    base_range = (base_hi / base_lo - 1.0) * 100.0 if base_lo > 0 else None
    first_base = str(df.index[-bw].date()) if len(df) >= bw else ""
    split_in_base = bool([d for d, _ in sp if d >= first_base])
    best_spike, n_spikes = S.spike_info(c, exclude_last=bw)
    gain5 = (c[-1] / c[-6] - 1.0) * 100.0 if len(c) > 6 else None
    dvol = float((close * vol).tail(20).mean())
    rs = S.rsi(close)
    tl = S.tested_level(df)
    last_split = sp[-1][0] if sp else ""
    # a reverse split left UNADJUSTED in the series shows as a jump ≈ 1/ratio between the close before and the open on the
    # split date; an adjusted series is continuous. Only an unadjusted split is a data artefact (frame choice is not).
    unadj = []
    idx = [str(x.date()) for x in df.index]
    for d, r in sp:
        k = next((i for i, x in enumerate(idx) if x >= d), None)
        if k is None or k == 0 or not (r > 0):
            continue
        c0, o1 = float(df["Close"].iloc[k - 1]), float(df["Open"].iloc[k])
        if c0 > 0 and o1 / c0 > 0.65 / r:
            unadj.append(d)
    return {"nbars": len(df), "last_bar": str(df.index[-1].date()), "price": round(price, 4), "drop_adj_pct": _fmt(drop),
            "drop_post_split_pct": _fmt(drop_ps), "base_range_pct": _fmt(base_range), "reverse_split_in_base": split_in_base,
            "best_spike_pct": _fmt(best_spike), "gain5_pct": _fmt(gain5), "dollar_vol_20": _fmt(dvol if math.isfinite(dvol) else None),
            "rsi_min_25": _fmt(float(rs.tail(int(S.CONFIG["RSI_OS_LOOKBACK"])).min())), "rsi_now": _fmt(float(rs.iloc[-1])),
            "tested_touches": (int(tl["touches"]) if tl else 1), "last_reverse_split": last_split,
            "unadjusted_splits": " ".join(unadj)}


def _value_of(gname, m, S):
    C = S.CONFIG
    v = {"M1": (m["price"], f"MIN_PRICE {_fmt(C['MIN_PRICE'])}"),
         "M2_CEIL": (m["drop_adj_pct"], f"MAX_DROP_PCT {_fmt(C['MAX_DROP_PCT'])}"),
         "M2_FLOOR": (m["drop_adj_pct"], f"MIN_DROP_FLOOR {_fmt(C['MIN_DROP_FLOOR'])}"),
         "M3": (m["best_spike_pct"], f"PRIOR_SPIKE_FLOOR {_fmt(C['PRIOR_SPIKE_FLOOR'])}"),
         "M4_RANGE": (m["base_range_pct"], f"BASE_RANGE_MAX_PCT {_fmt(C['BASE_RANGE_MAX_PCT'])}"),
         "M4_RISE": (m["gain5_pct"], f"RECENT_RISE_BLOCK_PCT {_fmt(C['RECENT_RISE_BLOCK_PCT'])}"),
         "M5": (m["dollar_vol_20"], f"MIN_DOLLAR_VOL {_fmt(C['MIN_DOLLAR_VOL'])}"),
         "RSI_OS": (m["rsi_min_25"], f"RSI_OS_HARD {_fmt(C['RSI_OS_HARD'])}"),
         "RSI_NOW": (m["rsi_now"], f"RSI_NOW_HARD {_fmt(C['RSI_NOW_HARD'])}"),
         "ANCHOR": (m["tested_touches"], "≥2 independent touches of the 30-bar low (±1.5%)"),
         "DEPTH": (m["nbars"], f"MIN_BARS {_fmt(C['MIN_BARS'])}")}
    return v.get(gname, ("", ""))


def classify(first, m, S):
    """provenance class of the first wall for THIS case (an adjustment artefact overrides the gate's own class)."""
    C = S.CONFIG
    if first == "M2_CEIL" and m["drop_post_split_pct"] is not None and \
            C["MIN_DROP_FLOOR"] <= m["drop_post_split_pct"] <= C["MAX_DROP_PCT"]:
        return "DATA_OR_ADJUSTMENT_ARTIFACT", "post-split drop is inside the M2 band; the adjusted drop exceeds the ceiling only because of reverse-split adjustment"
    if first == "M2_CEIL" and m["drop_post_split_pct"] is not None and m["drop_post_split_pct"] < C["MIN_DROP_FLOOR"]:
        return None, (f"post-split drop {m['drop_post_split_pct']}% is below the floor {_fmt(C['MIN_DROP_FLOOR'])}: excluded in "
                      "either frame — the ceiling name is an adjustment misnomer, not the decisive reason")
    if m.get("unadjusted_splits") and first in ("M2_CEIL", "M2_FLOOR", "M3", "M4_RANGE", "M4_RISE", "ANCHOR"):
        return "DATA_OR_ADJUSTMENT_ARTIFACT", f"reverse split(s) {m['unadjusted_splits']} left unadjusted in the series"
    if first == "M4_RANGE" and m["reverse_split_in_base"]:
        return None, ("a reverse split falls inside the 15-bar window but the series is adjusted at that date (no jump): "
                      "the range is genuine price action, not an adjustment artefact")
    return None, ""


EVIDENCE_NEEDED = {
    "UNIVERSE": "listing venue of the symbol at T and an owner decision on the universe scope",
    "DEPTH": "Faisal's frame for short post-split histories (TG_1807/TG_1811 describe it); a prereg for a post-split depth rule",
    "M2_CEIL": "closed axis (owner «خلّ السقف»); only the owner can reopen — evidence would be Faisal's own drop reference at T",
    "M4_RANGE": "a Faisal statement of a base-width limit (none found); for artefacts, a split-aware window already exists as a research arm",
    "M3": "a Faisal statement on the size/window of the prior explosion (the «100٪» text is about the target)",
    "RSI_NOW": "his RSI reading at T (closed RSI axis)",
    "ANCHOR": "frozen by the H6 control-pool dependency and the perf verdict; prospective H6 evidence is the admissible route",
    "PASS": "point-in-time float / borrow / short at T (not archived for history) to replay the post-scan gates",
}


def first_exclusion(S):
    bars, rows, splits, ubars, uni = _load_rank()
    eps = list(csv.DictReader(open(os.path.join(OUT, "gt_episodes.csv"), encoding="utf-8")))
    cases = [(e["episode_id"], e["ticker"], e["rank_T_e"], e["defensible_ref"], e["eligibility"], e["rank_evaluable"])
             for e in eps]
    cases += [(f"{t}_{d}", t, d, ref, "ANCHOR_CASE", "1") for t, d, ref, _ in EXTRA_CASES]
    rc = {}
    p = os.path.join(OUT, "rank_cases.csv")
    if os.path.exists(p):
        for r in csv.DictReader(open(p, encoding="utf-8")):
            rc[r["episode_id"]] = r
    out = []
    nas = set(uni.get("symbols") or [])
    for eid, sym, T, ref, elig, rkev in cases:
        src_rows = bars.get(sym)
        in_uni = sym in nas
        src = "rank" if src_rows is not None else ("universe_test" if sym in ubars else "")
        rr = src_rows if src_rows is not None else ubars.get(sym)
        hist = [r for r in (rr or []) if r[0] < T]
        rsp = sorted((d, float(x)) for d, x in (splits.get(sym) or []) if float(x) < 1.0)
        rec = {"case": eid, "ticker": sym, "T": T, "source_ref": ref, "eligibility": elig, "in_universe": int(in_uni),
               "bars_source": src}
        if not hist:
            rec.update(first_gate="NO_BARS", chain="", classification="UNKNOWN_OR_UNSUPPORTED")
            out.append(rec)
            continue
        df = _frame(hist)
        m = metrics(S, df, rsp, T)
        chain, neutral = [], []
        if not in_uni:
            chain.append(("UNIVERSE", "not in nasdaqlisted snapshot"))
        res, why = run_once(S, sym, df, ())
        first_g = _reason_gate(why) if res == "REJECT" else res
        chain_g = first_g
        steps = 0
        while res == "REJECT" and steps < 10:
            gname = _reason_gate(why)
            chain.append((gname, why))
            if gname not in NEUTRAL or gname in neutral:
                break
            neutral.append(gname)
            res, why = run_once(S, sym, df, tuple(neutral))
            steps += 1
        tail = "PASS" if res == "PASS" else (res if res != "REJECT" else "")
        fr = rows.get((T, sym)) or {}
        g0 = chain[0][0] if chain else "PASS"
        val, thr = _value_of(g0, m, S) if g0 not in ("PASS", "UNIVERSE") else ("", "")
        cls, why_cls = classify(g0, m, S)
        rec.update(first_gate=g0, first_gate_id=GATE_ID.get(g0, g0), first_reason=(chain[0][1] if chain else ""),
                   value=val, threshold=thr, frozen_bot_gate=fr.get("bot_gate", ""), frozen_bot_res=fr.get("bot_res", ""),
                   replay_matches_frozen=(("" if not fr else int((fr.get("bot_res") == "PASS" and chain_g == "PASS")
                                                               or (fr.get("bot_gate") == chain_g)))),
                   chain=" → ".join(gname for gname, _ in chain) + (f" → {tail}" if tail else ""),
                   never_ran=_never_ran(g0), case_artifact=cls or "", case_artifact_reason=why_cls,
                   bot_operational_list=(rc.get(eid, {}).get("bot_op_exact", "") if eid in rc else ""),
                   post_scan_gates=("M13/M14/borrow/DQ/capacity: point-in-time UNKNOWN (inputs not archived)" if g0 == "PASS" else ""),
                   evidence_needed=EVIDENCE_NEEDED.get(g0, ""))
        rec.update({k: m[k] for k in ("nbars", "last_bar", "price", "drop_adj_pct", "drop_post_split_pct", "base_range_pct",
                                      "reverse_split_in_base", "best_spike_pct", "rsi_now", "tested_touches", "last_reverse_split",
                                      "unadjusted_splits")})
        out.append(rec)
    return out


ORDER = ["UNIVERSE", "DEPTH", "M1", "M2_CEIL", "M2_FLOOR", "M3", "M4_RANGE", "M4_RISE", "M5", "RSI_OS", "RSI_NOW", "SOFT",
         "NEAR", "SCORE", "ANCHOR", "RR", "M13/M14/TIER", "DQ", "CAPACITY/FILL", "BORROW", "ENTRY_STATUS"]


def _never_ran(g0):
    if g0 == "PASS":
        return ""
    i = ORDER.index(g0) if g0 in ORDER else -1
    return " · ".join(ORDER[i + 1:]) if i >= 0 else ""


# ---------------------------------------------------------------- build
FX_COLS = ["case", "ticker", "T", "source_ref", "eligibility", "in_universe", "bars_source", "first_gate", "first_gate_id",
           "first_reason", "value", "threshold", "frozen_bot_res", "frozen_bot_gate", "replay_matches_frozen", "chain",
           "never_ran", "case_artifact", "case_artifact_reason", "bot_operational_list", "post_scan_gates", "evidence_needed",
           "nbars", "last_bar", "price", "drop_adj_pct", "drop_post_split_pct", "base_range_pct", "reverse_split_in_base",
           "best_spike_pct", "rsi_now", "tested_touches", "last_reverse_split", "unadjusted_splits", "classification"]
INV_COLS = ["order", "id", "system", "stage", "file", "function", "line", "role", "kind", "blocks_downstream", "provenance",
            "confidence", "artifact_risk", "status", "status_ref", "condition", "config", "on_pass", "on_fail",
            "on_unavailable", "on_malformed", "inputs", "provider", "timestamp_rule", "prod_median_per_day",
            "prod_last_day_count", "affected_cases", "chain_cases", "evidence_units", "next_action", "repro"]


def build():
    S = _S()
    prov = json.load(open(PROV, encoding="utf-8"))
    gates = prov["gates"]
    errors = []
    ids = [g["id"] for g in gates]
    if len(ids) != len(set(ids)):
        errors.append("duplicate gate ids")
    for g in gates:
        if g["provenance"] not in CATS:
            errors.append(f"{g['id']}: provenance {g['provenance']} not one of the six categories")
    e1, cache = locate(gates)
    e2, codes, bare = completeness(gates, cache)
    errors += e1 + e2
    snap = json.load(open(SNAP, encoding="utf-8")) if os.path.exists(SNAP) else None
    fx = first_exclusion(S)
    for g in gates:
        g["config"] = {k: _fmt(S.CONFIG.get(k)) for k in g.get("config_keys") or []}
        g["production_counts"] = counts_for(g, snap)
        g["affected_cases"] = [r["case"] for r in fx if r.get("first_gate_id") == g["id"]]
        g["chain_cases"] = [r["case"] for r in fx if g["id"] in {GATE_ID.get(x.strip(), x.strip()) for x in (r.get("chain") or "").split("→")}
                            and r.get("first_gate_id") != g["id"]]
    for r in fx:
        gid = r.get("first_gate_id")
        gg = next((g for g in gates if g["id"] == gid), None)
        r["classification"] = r.get("case_artifact") or (gg["provenance"] if gg else ("PASS" if r.get("first_gate") == "PASS" else "UNKNOWN_OR_UNSUPPORTED"))
    summary = {"gates": len(gates), "by_provenance": {c: sum(1 for g in gates if g["provenance"] == c) for c in CATS},
               "reject_codes_in_analyze_ticker": len(codes), "bare_none_returns": bare,
               "cases": len(fx), "first_gate_counts": _count(r["first_gate"] for r in fx),
               "replay_mismatches": [r["case"] for r in fx if r.get("replay_matches_frozen") == 0],
               "chain_presence": _count(x.strip() for r in fx for x in (r.get("chain") or "").split("→")
                                        if x.strip() and x.strip() != "PASS"),
               "errors": errors,
               "inputs": {"provenance_sha256": _sha(PROV), "snapshot_sha256": (_sha(SNAP) if snap else ""),
                          "rank_bars_sha256": _sha(os.path.join(DATA, "rank", "bars.json.gz")),
                          "rank_rows_sha256": _sha(os.path.join(DATA, "rank", "rows.csv.gz"))}}
    inv = {"schema": 1, "summary": summary, "categories": CATS, "gates": gates}
    return inv, fx


def _count(it):
    d = {}
    for x in it:
        d[x] = d.get(x, 0) + 1
    return dict(sorted(d.items(), key=lambda kv: (-kv[1], kv[0])))


def render(inv, fx):
    j = json.dumps(inv, ensure_ascii=False, indent=1, default=str) + "\n"
    s = io.StringIO()
    w = csv.writer(s, lineterminator="\n")
    w.writerow(INV_COLS)
    for g in sorted(inv["gates"], key=lambda g: (g["order"], g["id"])):
        pc = g.get("production_counts") or {}
        w.writerow([g["order"], g["id"], g["system"], g["stage"], g["file"], g["function"], g.get("line"), g["role"], g["kind"],
                    int(bool(g["blocks_downstream"])), g["provenance"], g["confidence"], g["artifact_risk"], g["status"],
                    g["status_ref"], g["condition"], json.dumps(g["config"], ensure_ascii=False), g["on_pass"], g["on_fail"],
                    g["on_unavailable"], g["on_malformed"], g["inputs"], g["provider"], g["timestamp_rule"],
                    pc.get("median_per_day", ""), pc.get("last_day_count", ""), " ".join(g["affected_cases"]),
                    " ".join(g["chain_cases"]), " | ".join(e["source_unit"] for e in g["evidence"]), g["next_action"], g["repro"]])
    c = s.getvalue()
    s2 = io.StringIO()
    w2 = csv.writer(s2, lineterminator="\n")
    w2.writerow(FX_COLS)
    for r in fx:
        w2.writerow([r.get(k, "") for k in FX_COLS])
    return j, c, s2.getvalue(), report(inv, fx)


# the owner's «13 gates» shown by hand_check/analyze_one (main f6afbb81) — display kind before and after 2026-10-09;
# the current kinds are enforced by the suite locks GPV4/GPV5 (behavioural), not by this table.
HC13 = [("السعر", "M1_PRICE", "hard", "hard"), ("الهبوط ضمن الأرضية–السقف", "M2_FLOOR / M2_CEIL", "hard", "hard"),
        ("انفجار سابق", "M3_FLOOR", "hard", "hard"), ("قاعدة ضيقة ولم ينفجر", "M4_RANGE / M4_RISE", "hard", "hard"),
        ("سيولة", "M5_DOLLAR_VOL", "hard", "hard"), ("توافق الفريمات", "SOFT_M6_TF", "info", "info"),
        ("نمط شمعة انعكاسي", "SOFT_M7_PATTERN", "soft", "soft"), ("فجوة-هدف فوق السعر", "SOFT_M9_GAP_ABOVE", "soft", "soft"),
        ("RSI تشبّع والآن", "M10_RSI_OS / M10_RSI_NOW", "hard", "hard"), ("تقاطع MACD", "SOFT_M11_MACD", "soft", "soft"),
        ("السعر قرب متوسطه 30/50", "SOFT_M12_EMA", "soft", "soft"), ("الشورت تحت 40K", "M13_SHORT", "hard", "soft"),
        ("الفلوت تحت 50M", "M14_FLOAT", "hard", "hard"), ("مِرساة: قاعٌ مُختبَر", "ANCHOR_TWO_TOUCH", "absent", "hard"),
        ("المتاح للاقتراض 20K أو أقل", "BORROW_AVAIL", "absent", "hard")]


def _q(gates, pred):
    return [g["id"] for g in gates if pred(g)]


def report(inv, fx):
    G = sorted(inv["gates"], key=lambda g: (g["order"], g["id"]))
    sm = inv["summary"]
    hard = [g for g in G if g["role"] == "reject" and g["status"] not in ("INACTIVE",) and g["blocks_downstream"]
            and g["kind"] in ("hard", "owner_policy", "coverage_guard", "ops_safety")]
    L = ["# 🚪🧭 Gate provenance report — generated (`python3 faisal_engine/gate_inventory.py`)", "",
         "Research only. Generated from `faisal_engine/data/gate_provenance.json` (curated evidence), the code (AST anchors, live",
         "production configuration `FAISAL_ONLY=1`), a frozen snapshot of `reject_log.json`, and the frozen ranking bars. "
         "Every number below is produced by the builder; `--check` regenerates and compares. Line numbers are as of the build "
         "and move with edits (the check verifies each anchor still sits inside its function).", "",
         f"**{sm['gates']} gates inventoried** · reject codes in `analyze_ticker`: {sm['reject_codes_in_analyze_ticker']} (all inventoried) · "
         f"silent `return None` paths: {sm['bare_none_returns']} (all inventoried) · build errors: {len(sm['errors'])}", "",
         "## 1. The seven decision questions", ""]
    def ids(pred):
        x = _q(G, pred)
        return ", ".join(f"`{i}`" for i in x) or "none"
    hard_ids = {g["id"] for g in hard}
    L += [f"1. **Hard exclusions with direct Faisal evidence:** {ids(lambda g: g['id'] in hard_ids and g['provenance'] == 'DIRECT_FAISAL_EVIDENCE')} "
          "(the only DIRECT row, `STABILITY_BT`, is a backtest arm and inactive in production).",
          f"2. **Hard exclusions inferred from Faisal evidence (catalog envelope / concept):** {ids(lambda g: g['id'] in hard_ids and g['provenance'] == 'INFERRED_FROM_FAISAL_EVIDENCE')}.",
          f"3. **Engineering guards:** {ids(lambda g: g['id'] in hard_ids and g['provenance'] == 'ENGINEERING_GUARD')} · "
          f"**owner policy:** {ids(lambda g: g['id'] in hard_ids and g['provenance'] == 'OWNER_POLICY')}.",
          f"4. **Possible data/adjustment/order artefacts or frame differences:** {ids(lambda g: str(g['artifact_risk']).startswith(('HIGH', 'MEDIUM', 'FRAME')))}; "
          f"cases whose first wall is an artefact: {', '.join(r['case'] for r in fx if r.get('case_artifact')) or 'none'}.",
          f"5. **Without supporting evidence (UNKNOWN_OR_UNSUPPORTED):** {ids(lambda g: g['provenance'] == 'UNKNOWN_OR_UNSUPPORTED')}; "
          "rows whose evidence list is only «no Faisal source» are engineering by construction (question 3).",
          f"6. **Change the candidate set** (hard, active): {', '.join(f'`{g}`' for g in sorted(hard_ids, key=lambda i: next(x['order'] for x in G if x['id'] == i)))} · "
          f"**ranking only:** {ids(lambda g: g['role'] == 'rank')} · **display/readiness only:** {ids(lambda g: g['role'] == 'display')} · "
          f"**soft (count toward `SOFT_COUNT`):** {ids(lambda g: g['kind'] == 'soft')}.",
          "7. **Highest-value permitted next action:** see §5.", "",
          "## 2. Gate table (pipeline order)", "",
          "| # | gate | where (as of build) | role · kind | provenance | confidence | status | live value | prod/day (median · 10-09) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for g in G:
        pc = g.get("production_counts") or {}
        cfg = " · ".join(f"{k}={v}" for k, v in g["config"].items()) or "—"
        L.append(f"| {g['order']} | `{g['id']}` | `{g['file']}::{g['function']}` L{g.get('line')} | {g['role']} · {g['kind']} | "
                 f"{g['provenance']} | {g['confidence']} | {g['status']} | {cfg} | "
                 f"{(str(pc.get('median_per_day')) + ' · ' + str(pc.get('last_day_count'))) if pc else '—'} |")
    L += ["", "## 3. First exclusion per Faisal episode (frozen bars < T, production `analyze_ticker`)", "",
          "The cause is the **first** wall; the chain lists what would block next if each wall were neutralised (research only).",
          "", "| case | T | first wall | value · threshold | case class | chain | frozen replay | operational list |", "|---|---|---|---|---|---|---|---|"]
    for r in fx:
        L.append(f"| {r['case']} | {r['T']} | {r.get('first_gate', '')} | {r.get('value', '')} · {r.get('threshold', '')} | "
                 f"{r.get('classification', '')} | {r.get('chain', '')} | "
                 f"{({1: 'match', 0: 'MISMATCH'}.get(r.get('replay_matches_frozen'), '—'))} | {r.get('bot_operational_list', '') or '—'} |")
    L += ["", f"First-wall counts: {', '.join(f'{k} {v}' for k, v in sm['first_gate_counts'].items())} · replay mismatches against the frozen "
          f"ranking rows: {len(sm['replay_mismatches'])} · walls present anywhere in a chain: "
          f"{', '.join(f'{k} {v}' for k, v in sm['chain_presence'].items())} (of {sm['cases']} cases).", ""]
    notes = [r for r in fx if r.get("case_artifact_reason")]
    if notes:
        L += ["Case notes:"] + [f"- **{r['case']}** ({r['first_gate']}): {r['case_artifact_reason']}." for r in notes] + [""]
    prov = {g["id"]: g["provenance"] for g in G}
    L += ["## 4. The manual tools (`hand_check.py` · `analyze_one.py`) — the owner's «13 gates»", "",
          "| displayed gate | inventory id | shown before | shown now | scanner provenance |", "|---|---|---|---|---|"]
    for lab, gid, k0, k1 in HC13:
        L.append(f"| {lab} | `{gid}` | {k0} | {k1} | {' / '.join(prov.get(x.strip(), '?') for x in gid.split('/'))} |")
    L += ["",
          "Displayed gates now mirror the scanner: M1–M5 + RSI hard (catalog numbers), M6 info at 0, M7/M9/M11/M12 soft, "
          "**M13 soft** (was shown hard), **M14 hard**, **borrow hard** (was absent), **anchor hard** (was absent). "
          "The verdict line now equals the scanner's post-enrich decision (`post_enrich_verdict`): a stock removed by M14 or the "
          "borrow gate is no longer called «مؤهّل — كان سيدخل قائمة المراقبة». Attention (technical identity) and owner eligibility "
          "remain one verdict in production; separating them is proposed research-only (no production change).", "",
          "## 5. Next permitted action", "",
          "- The dominant first wall on Faisal's episodes is `ANCHOR_TWO_TOUCH` (owner policy, FROZEN by the H6 control-pool "
          "dependency and the perf verdict): no production change is permitted; the admissible evidence is the prospective H6 "
          "collection already running.",
          "- `FILL_ROUNDS` (engineering cap) left 8 of 12 slots empty in production run 37902530011 (2026-10-09 log, not recomputed "
          "here) with eligible names unexamined; the new log line (`fill_shortfall_note`) measures how often the cap binds. A change "
          "is a live-threshold change ⇒ prereg + owner.",
          "- `M2_CEIL` / `M4_RANGE` artefacts on reverse-split names: closed / owner-decided axes; reopening needs the owner.", ""]
    return "\n".join(L) + "\n"


def _norm(text):
    text = re.sub(r'"line": (\d+|null)', '"line": #', text)
    text = re.sub(r'"function_lines": \[\s*\d+,\s*\d+\s*\]', '"function_lines": #', text)
    return re.sub(r"\bL(\d+|None)\b", "L#", text)


def _norm_csv(text):
    rows = list(csv.reader(io.StringIO(text)))
    if rows and "line" in rows[0]:
        i = rows[0].index("line")
        for r in rows[1:]:
            if len(r) > i:
                r[i] = "#"
    return rows


def main(argv):
    if "--snapshot" in argv:
        snapshot()
        return 0
    if "--completeness" in argv:                     # fast: anchors + coverage of reject codes / silent returns / functions
        gates = json.load(open(PROV, encoding="utf-8"))["gates"]
        e1, cache = locate(gates)
        e2, codes, bare = completeness(gates, cache)
        bad = [f"{g['id']}: provenance {g['provenance']}" for g in gates if g["provenance"] not in CATS]
        errs = e1 + e2 + bad
        print(f"🚪 completeness: codes {len(codes)} · silent returns {bare} · errors {len(errs)}")
        for e in errs:
            print("  ⛔", e)
        return 0 if not errs else 1
    inv, fx = build()
    j, c, x, md = render(inv, fx)
    errs = inv["summary"]["errors"]
    if "--check" in argv:
        bad = []
        for path, new, norm in ((F_JSON, j, _norm), (F_MD, md, _norm)):
            old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            if norm(old) != norm(new):
                bad.append(_rel(path))
        for path, new in ((F_CSV, c), (F_FX, x)):
            old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            if _norm_csv(old) != _norm_csv(new):
                bad.append(_rel(path))
        if errs:
            bad.append("build errors: " + "; ".join(errs))
        print("🚪 gate inventory --check:", "OK" if not bad else "⛔ " + " · ".join(bad))
        return 0 if not bad else 1
    os.makedirs(OUT, exist_ok=True)
    for path, text in ((F_JSON, j), (F_CSV, c), (F_FX, x), (F_MD, md)):
        open(path, "w", encoding="utf-8").write(text)
    print(f"🚪 gates {inv['summary']['gates']} · cases {inv['summary']['cases']} · first walls {inv['summary']['first_gate_counts']} · "
          f"errors {len(errs)}")
    for e in errs:
        print("  ⛔", e)
    return 0 if not errs else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
